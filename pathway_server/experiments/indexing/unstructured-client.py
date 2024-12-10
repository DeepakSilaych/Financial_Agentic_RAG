import os 
import pathway
from dotenv import load_dotenv
load_dotenv()
import logging
logging.basicConfig(level=logging.INFO)


# from dotenv import load_dotenv
import pathway as pw
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms, parsers, prompts
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.splitters import TokenCountSplitter

#LOGGING TO DEBUG ISSUES IN BETWEEN

pw.set_license_key(os.getenv("pathway_key"))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

#READING DATA IN (BINARY) AND ALSO DEFINING THE LLM
folder = pw.io.fs.read(
    path="./data/",
    format="binary",
    with_metadata=True,
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

# SETTING UP HOST FOR SERVER AND ALSO THE PARSER (this is where we can change from Unstructured to OpenParse)
app_host = "0.0.0.0"
app_port = 7000

parser = parsers.ParseUnstructured(startegy='hi_res', mode='elements',extract_image_block_types=['Image','Table'],extract_image_block_output_dir='./images-FY-elements2',
                                   cache_strategy=DiskCache())

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
