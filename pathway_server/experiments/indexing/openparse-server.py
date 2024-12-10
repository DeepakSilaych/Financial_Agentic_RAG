
import logging
logging.basicConfig(level=logging.DEBUG)
import os
from dotenv import load_dotenv
import pathway as pw
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms, parsers, prompts
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer

load_dotenv()
os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/5/tessdata/"
# os.environ['DISK_CACHE_PATH'] = './Cache'
pw.set_license_key(os.getenv("pathway_key"))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# persistence_backend = pw.persistence.Backend.filesystem("./state/")

import pathway as pw
from typing import List, Tuple, Dict


# ==========================================================
## Custom Parser

from io import BytesIO
from pathway.xpacks.llm.parsers import OpenParse  # Adjust the import path if necessary

class CustomOpenParse(OpenParse):
    """
    Custom OpenParse class with modified __wrapped__ behavior.
    """

    def __wrapped__(self, contents: bytes) -> list[tuple[str, dict]]:
        # Import dependencies locally to handle optional imports gracefully
        try:
            import openparse
            from pypdf import PdfReader
        except ImportError as e:
            raise ImportError("Required library not found. Please ensure openparse and pypdf are installed.") from e

        # Custom behavior: process the contents differently as needed
        reader = PdfReader(stream=BytesIO(contents))
        doc = openparse.Pdf(file=reader)


        # Original document parsing with custom modifications
        parsed_content = self.doc_parser.parse(doc)
        nodes = list(parsed_content.nodes)
        file_name = extract_company_info_from_nodes(list(parsed_content.model_dump()['nodes']))

        # for i in parsed_basic_doc.model_dump()['nodes']


        # Customize metadata or text output as needed
        docs = [(node.model_dump()["text"], {"filename_year" : str(file_name), "custom_meta" : str(node.model_dump())}) for node in nodes]

        # Additional custom processing can be added here
        return docs

# ==========================================================


# #==========================================================
# ## Additional Metadata

import os
import openai

class DocumentProcessor:
    def __init__(self):
        # Get API key from environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("API key not found in environment variables. Please set 'OPENAI_API_KEY'.")
        self.client = openai.OpenAI(api_key=api_key)

    def extract_company_and_year_from_nodes(self, nodes):
        """
        Extracts the 'Company Name' and 'Year of Report' from a list of nodes.
        """
        # Combine text from nodes to form the document content

        nodes_first_three_pages = [node for node in nodes if node.get('bbox', [{}])[0].get('page', 0) < 3]
        document_text = "\n".join(node.get("text", "") for node in nodes_first_three_pages)
        # document_text = "\n".join(node.get("text", "") for node in nodes)
        
        # Define the prompt for extracting company name and year
        prompt = (
            "Extract the following details from this document, and provide them in this format only:\n"
            "1. Company Name\n"
            "2. Year of Report\n"
            "Document content:\n\n" + document_text
        )

        # Call the OpenAI API to process the document text
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0
        )

        # Parse the response to extract company name and year
        response_text = response.choices[0].message.content
        details = {}
        for line in response_text.split("\n"):
            if "Company Name" in line:
                details["Company Name"] = line.split(":")[-1].strip()
            elif "Year of Report" in line:
                details["Year of Report"] = line.split(":")[-1].strip()
        
        return details

# Entry point function for importing
def extract_company_info_from_nodes(nodes):
    processor = DocumentProcessor()
    return processor.extract_company_and_year_from_nodes(nodes)

# #==========================================================


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

folder = pw.io.fs.read(
    path="./data/",
    format="binary",
    with_metadata=True,
    mode = 'static'
)
sources = [
    folder,
]  # define the inputs (local folders & files, google drive, sharepoint, ...)
chat = llms.OpenAIChat(
    model="gpt-4o-mini",
    retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6),
    cache_strategy=DiskCache(),
    temperature=0.0,
)

table_args = {
    "parsing_algorithm": "llm",
    "llm": chat,
    "prompt": prompts.DEFAULT_MD_TABLE_PARSE_PROMPT,
}

image_args = {
    "parsing_algorithm": "llm",
    "llm": chat,
    "prompt": prompts.DEFAULT_IMAGE_PARSE_PROMPT,
}


parser = CustomOpenParse(table_args=table_args, image_args=image_args,parse_images=False,cache_strategy=DiskCache())

# from pathlib import Path
# pdf_path = Path("./data/20230203_alphabet_10K.pdf")
# with pdf_path.open("rb") as f:
#     pdf_content = f.read()
# parsed_content = parser.__wrapped__(pdf_content)
# print(parsed_content)
# pw.run()

# # exit(0)
# persistence_config=persistence_config

embedder = embedders.OpenAIEmbedder(cache_strategy=DiskCache())
app_host = "0.0.0.0"
app_port = 7000
doc_store = VectorStoreServer(
        *sources,
        embedder=embedder,
        splitter=None,  # OpenParse parser handles the chunking
        parser=parser,
    )
# print(doc_store. __repr__())
doc_store.run_server(app_host, app_port, threaded = False, with_cache=True)
# pw.run()
# print(doc_store.docs)


## Testing on vector client of pathways ###

# db = VectorStoreClient(host=app_host, port=app_port)

# q = "what is the totalstockholders equity as of december 31, 2022"
# print(db.query(q,k=3))

# ## Testing on basic rag ###

# app = BaseRAGQuestionAnswerer(
#         llm=chat,
#         indexer=doc_store,
#         search_topk=6,
#         short_prompt_template=prompts.prompt_qa,
#     )
# app.build_server(host=app_host, port=app_port)
# app.run_server(with_cache=True, terminate_on_error=False)

# ## Commands ###

# curl -X 'POST' 'http://0.0.0.0:8000/v1/pw_list_documents' -H 'accept: */*' -H 'Content-Type: application/json'
# curl -X 'POST'   'http://0.0.0.0:8000/v1/pw_ai_answer'   -H 'accept: */*'   -H 'Content-Type: application/json'   -d '{"prompt": "what is the TotalStockholders equity as of December 31, 2022`"}'
