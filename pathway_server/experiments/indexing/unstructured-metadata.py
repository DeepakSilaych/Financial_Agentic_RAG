import os 

import logging
logging.basicConfig(level=logging.DEBUG)
import time
from io import BytesIO
import pathway as pw
import json


from unstructured.partition.auto import partition


from call_llm import process_elements_for_company

# from dotenv import load_dotenv
import pathway as pw
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms, parsers, prompts
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.splitters import TokenCountSplitter

os.environ['OPENAI_API_KEY'] = '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'
os.environ['pathway_key']='Ip4kv2J47MFeVeQB7EFYY6kGhhBXAD'

#LOGGING TO DEBUG ISSUES IN BETWEEN

folder_path = "./data2"

# load_dotenv("new.env")
#os.environ["TESSDATA_PREFIX"] = 'C:\\Program Files (x86)\\Tesseract\\tesseract.exe'

pw.set_license_key(os.getenv("pathway_key"))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')



class ParseUnstructured(pw.UDF):
    """
    Parse documents using Unstructured's `partition` function with enhanced metadata.
    
    Args:
        mode: single, elements, or paged.
        post_processors: list of callable functions to process each extracted element.
        **unstructured_kwargs: additional kwargs for the `partition` function
    """

    def __init__(self, mode="single",post_processors=None, **unstructured_kwargs):
        super().__init__()
        self.kwargs = {
            "mode": mode,
            "post_processors": post_processors or [],
            "unstructured_kwargs": unstructured_kwargs,
    
        }

    def __wrapped__(self, contents: bytes, **kwargs) -> list[tuple[str, dict]]:
        # Merge instance kwargs with any additional kwargs provided at call time
        kwargs = {**self.kwargs, **kwargs}

        # Partition the document into elements
        elements = partition(file=BytesIO(contents), **kwargs.pop("unstructured_kwargs"))

        # Extract the mode and post-processors
        mode = kwargs.pop("mode")
        post_processors = kwargs.pop("post_processors")        

        combined_string=""
        for element in elements:
            if element.metadata.page_number<3:
                combined_string+=element.text
        
        details=process_elements_for_company(OPENAI_API_KEY,combined_string)

        print("********************************")
        print(details)
        print("***********************************")

        docs = []
        for element in elements:

            # Apply each post-processor to the element
            for post_processor in post_processors:
                element.apply(post_processor)

            # Extract and customize metadata
            if hasattr(element, "metadata"):
                metadata = element.metadata.to_dict()
            else:
                metadata = {}
            
                 
            # Add custom metadata fields
            metadata['company_name']=details['Company']
            metadata['year']=details['Year']
            
            # Add element's category to metadata if it exists
            if hasattr(element, "category"):
                metadata["category"] = element.category

            # Append element text and updated metadata to docs list based on mode
            if mode == "elements":
                docs.append((str(element), metadata))
            elif mode == "paged":
                # Paged mode groups elements by page number
                page_number = metadata.get("page_number", 1)
                text = docs.get(page_number, "") + str(element) + "\n\n"
                docs[page_number] = (text, metadata)
            elif mode == "single":
                # Single mode combines all text
                docs = [(str(element), metadata)]

        return docs



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

#READING DATA IN (BINARY) AND ALSO DEFINING THE LLM
folder = pw.io.fs.read(
    path="./data2/",
    format="binary",
    with_metadata=True,
)
sources = [
    folder,
]  # define the inputs (local folders & files, google drive, sharepoint, ...)
chat = llms.OpenAIChat(
    model="gpt-4o",
    retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6),
    cache_strategy=DiskCache(),
    temperature=0.0,
)

# SETTING UP HOST FOR SERVER AND ALSO THE PARSER (this is where we can change from Unstructured to OpenParse)
app_host = "0.0.0.0"
app_port = 3000

parser = ParseUnstructured(startegy='hi_res', mode='elements',extract_image_block_types=['Image','Table'],extract_image_block_output_dir='./images-FY-elements2')

#parser=parsers.OpenParse()
#text_splitter = TokenCountSplitter(max_tokens=100)

embedder = embedders.OpenAIEmbedder(cache_strategy=DiskCache())

doc_store = VectorStoreServer(
        *sources,
        embedder=embedder,
        splitter=None,  # OpenParse parser handles the chunking
        parser=parser,
    )


doc_store.run_server(app_host, app_port, threaded=False, with_cache=True)


'''

try:
    logging.info(f"Starting VectorStore server on {app_host}:{app_port}")
    doc_store.run_server(app_host, app_port, threaded=True, with_cache=True)
      # Disable threading temporarily
except RuntimeError as e:
    logging.error("RuntimeError encountered during server execution.", exc_info=True)
except Exception as e:
    logging.error("An unexpected error occurred while running the server.", exc_info=True)
finally:
    logging.info("Shutting down server gracefully.")
'''

#time.sleep()

### Testing on vector client of pathways ###

#db = VectorStoreClient(host=app_host, port=app_port)

#q = "what is the totalstockholders equity as of december 31, 2022"
#print(db.query(q,k=3))

### Testing on basic rag ###

'''
app = BaseRAGQuestionAnswerer(
         llm=chat,
         indexer=doc_store,
         search_topk=6,
         short_prompt_template=prompts.prompt_qa,
     )
app.build_server(host=app_host, port=app_port)
app.run_server(with_cache=True, terminate_on_error=False)
'''

### Commands ###

# curl -X 'POST' 'http://0.0.0.0:8000/v1/pw_list_documents' -H 'accept: */*' -H 'Content-Type: application/json'
# curl -X 'POST'   'http://0.0.0.0:8000/v1/pw_ai_answer'   -H 'accept: */*'   -H 'Content-Type: application/json'   -d '{"prompt": "what is the TotalStockholders equity as of December 31, 2022`"}'
