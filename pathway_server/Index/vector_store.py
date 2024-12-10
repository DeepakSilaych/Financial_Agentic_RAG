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
import json
from openai import OpenAI
from FlagEmbedding import BGEM3FlagModel
import torch
import numpy as np
# import fitz  # PyMuPDF
import base64
import io
from PIL import Image
from langchain.chat_models import ChatOpenAI
import voyageai

db = FinancialDatabase()
db.reset_database()

client = OpenAI()
llm = ChatOpenAI(model="gpt-4o")

class VoyageEmbedder(embedders.OpenAIEmbedder):
    """Pathway wrapper for Voyage AI Embedding services."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __wrapped__(self, input, **kwargs) -> np.ndarray:
        """Embed the documents

        Args:
            - input: mandatory, the string to embed.
            - **kwargs: optional parameters, if unset defaults from the constructor
              will be taken.
        """
        kwargs = {**self.kwargs, **kwargs}
        vo = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))   
        ret = vo.embed([input or "."], model="voyage-3", input_type="document")
        return np.array(ret.embeddings[0])

class Bge_m3_embedder(embedders.OpenAIEmbedder):
    """
    Custom Pathway embedder for BGE-M3 model with flexible embedding handling.
    
    Key Considerations:
    - Ensures compatibility with Pathway's vector store
    - Handles various input scenarios
    - Provides flexible embedding output
    """
    
    def __init__(self, 
                 model_name='BAAI/bge-m3', 
                 *args, 
                 **kwargs):
        """
        Initialize the BGE-M3 embedder.
        
        Args:
            model_name (str): Hugging Face model identifier
            *args: Additional positional arguments for OpenAIEmbedder
            **kwargs: Additional keyword arguments for OpenAIEmbedder
        """
        super().__init__(*args, **kwargs)
        
        # Load BGE-M3 model
        self.bgem3_model = BGEM3FlagModel(
            model_name,
            use_fp16=torch.cuda.is_available()  # Use FP16 if CUDA available
        )

    async def __wrapped__(self, input, **kwargs) -> np.ndarray:
        """
        Embed input text with flexible handling.
        
        Args:
            input (str): Text to embed
            **kwargs: Additional embedding parameters
        
        Returns:
            np.ndarray: Embedding vector
        """
        # Handle empty or whitespace inputs
        if not input or input.isspace():
            input = "."
        
        try:
            # Encode input with dense vector return
            embeddings_dict = self.bgem3_model.encode(
                [input], 
                return_dense=True
            )
            
            # Extract dense vector and ensure correct type
            embedding = embeddings_dict['dense_vecs'][0]
            
            # Convert to float32 numpy array
            embedding_array = np.array(embedding, dtype=np.float32)
            
            return embedding_array
        
        except Exception as e:
            print(f"Embedding error: {e}")
            # Return None or raise the exception based on your error handling preference
            raise

def make_succinct_context_for_value(company_name: str, year: str, type: str):
    if type == "10-K" or type == "10-Q":
        if company_name and year:
            return f"This value is from a {type} report of {company_name} for the year {year}."
        elif company_name:
            return f"This value is from a {type} report of {company_name}."
        elif year:
            return f"This value is from a {type} report for the year {year}."
        else:
            return f"This value is from a {type} report."            
    else:
        if company_name and year:
            return f"This value is from a finance-related document of {company_name} for the year {year}."
        elif company_name:
            return f"This value is from a finance-related document of {company_name}."
        elif year:
            return f"This value is from a finance-related document for the year {year}."
        else:
            return "This value is from a finance-related document."

def extract_page_image(doc, node):
    """
    Extract the full page image containing the specified node from the PDF.
    
    Args:
        doc (openparse.Pdf): The PDF document
        node (Node): The node used to identify the page
    
    Returns:
        str: Base64 encoded full page image, or None if extraction fails
    """
    try:
        # Convert to PyMuPDF document if not already done
        pdoc = doc.to_pymupdf_doc()
        
        # Check if node has bbox and elements
        if not node.elements or not node.elements[0].bbox:
            return None
        
        # Get the page number from the first element's bbox
        page_num = node.elements[0].bbox.page
        
        # Extract the full page
        page = pdoc[page_num]
        
        # Render full page as pixmap
        pix = page.get_pixmap()
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    except Exception as e:
        print(f"Error extracting page image: {e}")
        return None
    
def extract_node_image(doc, node):
    """
    Extract the image for a specific node using its bounding box from the PDF.
    
    Args:
        doc (openparse.Pdf): The PDF document
        node (Node): The node to extract the image for
    
    Returns:
        str: Base64 encoded image of the node, or None if extraction fails
    """
    try:
        # Convert to PyMuPDF document if not already done
        pdoc = doc.to_pymupdf_doc()
        
        # Check if node has bbox and elements
        if not node.elements or not node.elements[0].bbox:
            return None
        
        # Get the page number from the first element's bbox
        page_num = node.elements[0].bbox.page
        
        # Extract the full page
        page = pdoc[page_num]
        
        # Get the bounding box coordinates
        bbox = node.elements[0].bbox
        
        # Render full page as pixmap
        pix = page.get_pixmap()
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Crop the image based on bbox
        # Note: PyMuPDF and PIL might have slightly different coordinate systems
        # Adjust coordinates if needed
        cropped_img = img.crop((
            int(bbox.x0), 
            int(bbox.y0), 
            int(bbox.x1), 
            int(bbox.y1)
        ))
        
        # Convert to base64
        buffered = io.BytesIO()
        cropped_img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    except Exception as e:
        print(f"Error extracting node image: {e}")
        return None

Whole_chunk = """You are a values extractor and describer
You are given an image of a page from a 10-K document. You need to find out Table name, row name, column name, and the value of each and every cell in the each table(s)(if present) in the image and describe each and every value in the KeyValueSchema format.

Key Instructions:
1. Identify Table Name, Row Name, Column Name, and Cell Values
2. Capture any hierarchical information
3. At last return the detailed description of each an every value of the table with the table name, corresponding row name and column name with any other information which is necessary to interpret that value in ListofKeyValues format.

Processing Guidelines:
- Extract EVERY value in the table
- Provide contextual description for each value
- Include relevant hierarchical and financial context
- Demonstrate calculation methodology where applicable

Special Focus for Consolidated/Net/Total Values:
- Explain calculation methodology
- Identify contributing components
- Provide financial context and significance  

Here is an example of how to represent the table values:
The table name that we got from the image is "Net Losses for Defined Benefit Pension Plans".
Notice how each description also contains the table name, row name, and column name for clarity.

[
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value 8617 corresponds to the pre-tax net loss for US defined benefit pension plans as of January 1, 2023. This represents the cumulative unrecognized actuarial loss that has been recorded in other comprehensive income at the beginning of the year for the US pension plans.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value 14273 corresponds to the pre-tax net loss for US defined benefit pension plans as of January 1, 2022. This is the starting value of accumulated unrecognized actuarial losses in other comprehensive income at the beginning of the prior year for the US pension plans.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value 11219 corresponds to the pre-tax net loss for non-US defined benefit pension plans as of January 1, 2022. This reflects the accumulated actuarial losses for non-US pension plans at the beginning of the prior year, recognized in other comprehensive income.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value 959 corresponds to the current period pre-tax loss recognized for US defined benefit pension plans in 2023. This represents the actuarial losses incurred during the year, primarily due to changes in assumptions or market conditions affecting the US pension plans.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value 794 corresponds to the current period pre-tax loss recognized for US defined benefit pension plans in 2022. This is the amount of new actuarial losses recorded for the US pension plans during the prior year.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value 2125 corresponds to the current period pre-tax loss recognized for non-US defined benefit pension plans in 2022. This indicates the actuarial losses recognized in other comprehensive income for non-US pension plans during that year.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value negative 1115 corresponds to the current period pre-tax gain recognized for non-US defined benefit pension plans in 2023. This reflects actuarial gains, reducing the total accumulated net loss for non-US pension plans during the year.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value negative 3923 corresponds to curtailments and settlements for US defined benefit pension plans in 2023. This large negative value primarily results from significant non-cash settlement charges related to plan amendments or terminations, which reduced the recognized net loss.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value negative 7 corresponds to curtailments and settlements for US defined benefit pension plans in 2022. This small negative value reflects minor settlements or amendments impacting the US pension plans' accumulated net loss.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value negative 47 corresponds to curtailments and settlements for non-US defined benefit pension plans in 2022. This amount shows the impact of plan amendments or settlements on non-US pension plans' accumulated net loss during that year.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value negative 109 corresponds to the amortization of net loss included in net periodic cost for US defined benefit pension plans in 2023. This represents the portion of unrecognized actuarial loss that was amortized and included as part of the pension expense for the year.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value negative 527 corresponds to the amortization of net loss included in net periodic cost for US defined benefit pension plans in 2022. This shows the prior year's amount of actuarial losses amortized into the net periodic pension cost.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value negative 400 corresponds to the amortization of net loss included in net periodic cost for non-US defined benefit pension plans in 2023. This amount reflects the amortization of actuarial losses for non-US pension plans that were included in the periodic pension cost.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value negative 1031 corresponds to the amortization of net loss included in net periodic cost for non-US defined benefit pension plans in 2022. This is the prior year's amortized actuarial loss for non-US pension plans.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value 9467 corresponds to the net loss at December 31 for US defined benefit pension plans in 2023. This total is calculated by starting with the opening balance of net loss of 8617 at January 1, adding the current period loss of 959, subtracting curtailments and settlements of negative 3923, and subtracting amortization of net loss of negative 109. These components together determine the year-end balance.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value 8617 corresponds to the net loss at December 31 for US defined benefit pension plans in 2022. This total is derived by taking the beginning net loss of 14273, adding the current period loss of 794, subtracting curtailments and settlements of negative 7, and subtracting amortization of net loss of negative 527. These adjustments yield the year-end total.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value 12937 corresponds to the net loss at December 31 for non-US defined benefit pension plans in 2023. This value is calculated by starting with the beginning balance of 11219, subtracting the current period gain of negative 1115, subtracting curtailments and settlements of negative 47, and subtracting amortization of net loss of negative 400. These elements together make up the final total.",
    "In the table 'Net Losses for Defined Benefit Pension Plans', the value 11219 corresponds to the net loss at December 31 for non-US defined benefit pension plans in 2022. This total is derived by taking the beginning balance of 111219, adding the current period loss of 2125, subtracting curtailments and settlements of negative 47, and subtracting amortization of net loss of negative 1031.",      
    . . . <for all the values>
]                     

You are give with the image of a whole page of a document, you need to extract all the values from the table(s) present in the image with the detailed description of each and every value in the format mentioned above. 
If no table is present in the given image then return None object only. and if the input is None then also return None object only.
"""

#-------------------------------------------------

class CustomOpenParse(OpenParse):
    """
    Custom OpenParse class with modified _wrapped_ behavior.
    """
    def _init_(self, *args, **kwargs):
        super()._init_(*args, **kwargs)
    def _wrapped_(self, contents: bytes) -> list[tuple[str, dict]]:
        
        reader = PdfReader(stream=BytesIO(contents))
        doc = openparse.Pdf(file=reader)

        # Original document parsing with custom modifications
        parsed_content = self.doc_parser.parse(doc)
        nodes = list(parsed_content.nodes)
        
        # Extract the static metadata from the document
        type, company_name, year, quarter = extract_static_metadata_using_openai(nodes)
        
        # list for storing all the chunks with their metadata
        docs = []

        # set for storing the topics used till now in this document
        set_of_topics = set()

        # list for storing all the key value pairs extracted from the document
        key_val_docs = []

        queried_pages = set()
        
        
        
        # Extract the dynamic metadata from the document
        if type == "10-K" or type == "10-Q" or type == "Finance":

            # TABLE VALUE EXTRACTION
            for node in nodes:
                if "table" in node.variant and node.bbox[0].page not in queried_pages:
                    base64_image = extract_page_image(doc, node)
                    if base64_image is not None:
                        response = client.beta.chat.completions.parse(
                          model="gpt-4o",
                          messages=[
                            {
                              "role": "user",
                              "content": [
                                {
                                  "type": "text",
                                  "text": Whole_chunk,
                                },
                                {
                                  "type": "image_url",
                                  "image_url": {
                                    "url":  f"data:image/png;base64,{base64_image}"
                                  },
                                },
                              ],
                            }
                          ],
                          response_format=ListofKeyValues,
                        )
                        if response.choices[0].message.parsed:
                            keyvals = response.choices[0].message.parsed.listofstr
                            if keyvals:
                                key_val_docs.extend([
                                    (
                                        make_succinct_context_for_value(company_name, year, type) + " " + key_value,
                                        {
                                            "type": type,
                                            "company_name": company_name,
                                            "year": year,
                                            "quarter": quarter,
                                            "topic": "Other",
                                            "item_10K": "Other",
                                            "is_table_value": "True",
                                            "table": "True",
                                            "image": base64_image,
                                            "page_no": node.bbox[0].page if len(node.bbox) > 0 else -1,
                                        },
                                    )
                                    for key_value in keyvals
                                ])
                                queried_pages.add(node.bbox[0].page)


            # NORMAL TEXT EXTRACTION
            for node in nodes:
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
                                "is_table_value": "False",
                                "table": "True" if "table" in node.variant else "False",
                                "image": extract_node_image(doc, node),
                                "page_no": node.bbox[0].page if len(node.bbox) > 0 else -1,
                            },
                        )
                    )
        else:
            # FOR OTHER DOCUMENTS
            for node in nodes:
                docs.append(
                        (
                            node.text,
                            {
                                "type": type,
                                "company_name": company_name,
                                "year": year,
                                "quarter": quarter,
                                "topic": None,
                                "item_10K": None,
                                "is_table_value": "False",
                                "table": "True" if "table" in node.variant else "False",
                                "image": extract_node_image(doc, node),
                                "page_no": node.bbox[0].page if len(node.bbox) > 0 else -1,
                            },
                        )
                    )

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
        # filename = f"{type}{company_name}{year}_data.json"
        # with open(filename, "w") as f:
        #     json.dump(json_data, f, indent=4)

        # filename2 = f"{type}{company_name}{year}_topics.py"
        # with open(filename2, "w") as f:
        #     f.write(f"TOPICS = {set_of_topics}")
            
        return docs

folder = pw.io.fs.read(
    path="./data/",
    format="binary",
    with_metadata=True,
)
# define the inputs (local folders & files, google drive, sharepoint, ...)
sources = [folder]

vision_llm = llms.OpenAIChat(
    model="gpt-4o",
    cache_strategy=DiskCache(),
    retry_strategy=ExponentialBackoffRetryStrategy(max_retries=4),
    verbose=True,
)

TABLE_PARSE_PROMPT = """
*Table Title:* 
Extract the title of the table and list it as the first element of the explanation.

*Row-by-Row Explanation:* 
For each row, start with a clear label or identifier if available. For every value, mention the corresponding column name, value, and its associated unit, measurement, or category. Explain hierarchical relationships or nested structures within rows if present.

*Example Structure:*
1. *Title of the Table*: Mention the title clearly.
2. *Row 1*: Begin with the row identifier or label (if any). Then explain each column in this format:
   - Column Name: Value (Unit or Category if applicable). Additional context or clarification.
   - Repeat for all columns in the row.
3. *Sub-rows*: If there is a sub-row or hierarchy within a row, introduce it as a sub-element of the main row and follow the same explanation pattern.
4. *Row 2*: Continue similarly for subsequent rows.

*Important Guidelines:*
- Do not skip any data or leave out any context.
- Ensure a natural language format for easy readability.
- If no table is found, return 'No table.'
"""
parser = CustomOpenParse(
    table_args={
        "parsing_algorithm": "llm",
        "llm": vision_llm,
        "prompt": TABLE_PARSE_PROMPT,   
    },
    parse_images=False,
    cache_strategy=DiskCache(),
)
openai_embedder = embedders.OpenAIEmbedder(
    cache_strategy=DiskCache()
    )
voyage_embedder = VoyageEmbedder(
    cache_strategy=DiskCache()
)
bgem3_embedder = Bge_m3_embedder(
    cache_strategy=DiskCache()
)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    doc_store = VectorStoreServer(
        *sources,
        embedder=openai_embedder, # (or voyage_embedder or bgem3_embedder) as per the requirement
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
