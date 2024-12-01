from dotenv import load_dotenv
load_dotenv()

import logging
from io import BytesIO
import pathway as pw
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms
from pathway.xpacks.llm.parsers import OpenParse
from pathway.xpacks.llm.vector_store import VectorStoreServer
import openparse
from pypdf import PdfReader
from .static_metadata import *
from .dynamic_metadata import *

db = FinancialDatabase()
db.reset_database()

os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/4.00/tessdata"


class CustomOpenParse(OpenParse):
    """
    Custom OpenParse class with modified __wrapped__ behavior.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def __wrapped__(self, contents: bytes) -> list[tuple[str, dict]]:
        
        reader = PdfReader(stream=BytesIO(contents))
        doc = openparse.Pdf(file=reader)

        # Original document parsing with custom modifications
        parsed_content = self.doc_parser.parse(doc)
        nodes = list(parsed_content.nodes)

        # Extract the static metadata from the document
        type, company_name, year, quarter = extract_static_metatdata(nodes)
        
        # list for storing all the chunks with their metadata
        docs = []

        # set for storing the topics used till now in this document
        set_of_topics = set()

        # list for storing all the key value pairs extracted from the document
        key_val_docs = []
        
        # Extract the dynamic metadata from the document
        if type == "10-K" or type == "10-Q" or type == "Finance":
            prev_node = None
            for node in nodes:
                if "table" in node.variant:
                    for retries in range(MAX_RETRIES_ANTHROPIC):
                        try:
                            response = situate_context_finance_table(doc=doc, chunk=node.text, prev_chunk=prev_node, typetext="table", type=type)
                            response = response[0]
                            set_of_topics.add(response.topic)
                            key_vals = [
                                (
                                    make_succinct_context_for_value(company_name, year, type) + " " + key_value,
                                    {
                                        "type": type,
                                        "company_name": company_name,
                                        "year": year,
                                        "quarter": quarter,
                                        "topic": response.topic,
                                        "item_10K": response.item_10K,
                                        "is_table_value": "true",
                                        "page_no": node.bbox[0].page if len(node.bbox) > 0 else -1,
                                    },
                                )
                                for key_value in response.listofstr
                            ]
                            key_val_docs.extend(key_vals)
                            docs.append(
                                (
                                    response.succint_context + " " + node.text,
                                    {
                                        "type": type,
                                        "company_name": company_name,
                                        "year": year,
                                        "quarter": quarter,
                                        "topic": response.topic,
                                        "item_10K": response.item_10K,
                                        "is_table_value": "false",
                                        "page_no": node.bbox[0].page if len(node.bbox) > 0 else -1,
                                    },
                                )
                            )
                            break
                        except Exception as e:
                            print(f"Error in extracting table values: {e}")
                            print(f"Retrying for the {retries+1} time.")
                            if retries == MAX_RETRIES_ANTHROPIC - 1:
                                print("Max retries reached. Skipping this chunk for Succinct context extraction.")
                                docs.append(
                                    (
                                        node.text,
                                        {
                                            "type": type,
                                            "company_name": company_name,
                                            "year": year,
                                            "quarter": quarter,
                                            "topic": "Other",
                                            "item_10K": "Other",
                                            "is_table_value": "false",
                                            "page_no": node.bbox[0].page if len(node.bbox) > 0 else -1,
                                        },
                                    )
                                )
                                break
                            continue
                else:
                    for retries in range(MAX_RETRIES_ANTHROPIC):
                        try:
                            response = situate_context_finance(doc=doc, chunk=node.text, typetext="text", type=type)
                            response = response[0]
                            set_of_topics.add(response.topic)
                            docs.append(
                                (
                                    response.succint_context + " " + node.text,
                                    {
                                        "type": type,
                                        "company_name": company_name,
                                        "year": year,
                                        "quarter": quarter,
                                        "topic": response.topic,
                                        "item_10K": response.item_10K,
                                        "is_table_value": "false",
                                        "page_no": node.bbox[0].page if len(node.bbox) > 0 else -1,
                                    },
                                )
                            )
                            break
                        except Exception as e:
                            print(f"Error in generating succinct context values: {e}")
                            print(f"Retrying for the {retries+1} time.")
                            if retries == MAX_RETRIES_ANTHROPIC - 1:
                                print("Max retries reached. Skipping this chunk for succinct context generation.")
                                docs.append(
                                    (
                                        node.text,
                                        {
                                            "type": type,
                                            "company_name": company_name,
                                            "year": year,
                                            "quarter": quarter,
                                            "topic": "Other",
                                            "item_10K": "Other",
                                            "is_table_value": "false",
                                            "page_no": node.bbox[0].page if len(node.bbox) > 0 else -1,
                                        },
                                    )
                                )
                                break
                            continue
                prev_node = node
        else:
            for node in nodes:
                for retries in range(MAX_RETRIES_ANTHROPIC):
                    try:
                        response = situate_context_others(doc=doc, chunk=node.text, set_of_topics=set_of_topics)
                        response = response[0]
                        set_of_topics.add(response.topic)
                        docs.append(
                            (
                                response.succint_context + " " + node.text,
                                {
                                    "type": type,
                                    "company_name": company_name,
                                    "year": year,
                                    "quarter": quarter,
                                    "topic": response.topic,
                                    "item_10K": None,
                                    "is_table_value": "false",
                                    "page_no": node.bbox[0].page if len(node.bbox) > 0 else -1,
                                },
                            )
                        )
                        break
                    except Exception as e:
                        print(f"Error in generating succinct context values: {e}")
                        print(f"Retrying for the {retries+1} time.")
                        if retries == MAX_RETRIES_ANTHROPIC - 1:
                            print("Max retries reached. Skipping this chunk for succinct context generation.")
                            docs.append(
                                (
                                    node.text,
                                    {
                                        "type": type,
                                        "company_name": company_name,
                                        "year": year,
                                        "quarter": quarter,
                                        "topic": "Other",
                                        "item_10K": None,
                                        "is_table_value": "false",
                                        "page_no": node.bbox[0].page if len(node.bbox) > 0 else -1,
                                    },
                                )
                            )
                            break
                        continue

        # write to database, if error occurs then just move on 
        report = {
            'company_name': company_name, 
            'year': year, 
            'quarter': quarter, 
            'type': type,
            'topics': set_of_topics
        }
        try:
            db.insert_report(report)
        except:
            print("=============================================")
            print("Error in inserting the report in the database.")
            print("=============================================")
            print("Report: ", report)
            pass 

        # concat docs with key_val_docs
        docs.extend(key_val_docs)
        
        # COMMENT OUT TO SEE THE CHUNKS IN A SEPERATE JSON FILE
        
        # json_data = [{"label": item[0], "data": item[1]} for item in docs]
        # filename = f"{type}_{company_name}_data.json"
        # with open(filename, "w") as f:
        #     json.dump(json_data, f, indent=4)

        # filename2 = f"{type}_{company_name}_topics.py"
        # with open(filename2, "w") as f:
        #     f.write(f"TOPICS = {set_of_topics}")
            
        return docs
    
#-------------------------------------------------

folder = pw.io.fs.read(
    path="./data/",
    format="binary",
    with_metadata=True,
)
# define the inputs (local folders & files, google drive, sharepoint, ...)
sources = [folder]

vision_llm = llms.OpenAIChat(
    model="gpt-4o-mini",
    cache_strategy=DiskCache(),
    retry_strategy=ExponentialBackoffRetryStrategy(max_retries=4),
    verbose=True,
)

TABLE_PARSE_PROMPT = """Explain the following table row by row, covering each detail precisely.
The first line should be the title of the table.
Then each row, include all values and their associated units, measurements, or categories with the appropriate column names.
Begin each row explanation by identifying the row title or label if present. For each of the rows, describe each column with its specific information and unit, and ensure no data is skipped or if there is any heirarchy then include that as well.
Make sure each row is in natural language and not just labels and numbers, their context should be explained.
If it is not a table, return 'No table.'."""
parser = CustomOpenParse(
    table_args={
        "parsing_algorithm": "llm",
        "llm": vision_llm,
        "prompt": TABLE_PARSE_PROMPT,   
    },
    parse_images=False,
    cache_strategy=DiskCache(),
)
embedder = embedders.OpenAIEmbedder(
    # model="text-embedding-3-large",
    cache_strategy=DiskCache())

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    doc_store = VectorStoreServer(
        *sources,
        embedder=embedder,
        splitter=None,  # OpenParse parser handles the chunking
        parser=parser,
    )
    doc_store.run_server(
        VECTOR_STORE_HOST,
        5000,
        # threaded=True,
        with_cache=True,
        cache_backend=pw.persistence.Backend.filesystem("./Cache-keyval-str"),
    )