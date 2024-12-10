from dotenv import load_dotenv

load_dotenv()

import logging
import os
from io import BytesIO
from prompt import prompts
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
import pathway as pw
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy
from pathway.xpacks.llm import embedders, llms
from pathway.xpacks.llm.parsers import OpenParse
from pathway.stdlib.indexing import (
    BruteForceKnnFactory,
    HybridIndexFactory,
    UsearchKnnFactory,
)
from pathway.stdlib.indexing.bm25 import TantivyBM25Factory
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.servers import DocumentStoreServer
import config
from llm import llm
from workflows.repeater import repeater
from workflows.rag_e2e import rag_e2e
from workflows.post_processing import visual_workflow

os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/5/tessdata"


from typing import Callable

import pathway as pw
from pathway.internals.udfs.utils import coerce_async
from pathway.xpacks.llm.servers import BaseRestServer

import config
import uuid


def serve_callable(
        server,
        route: str,
        schema: type[pw.Schema],
        callable_func: Callable,
        **additional_endpoint_kwargs,
    ):
        def func_to_transformer(fn):
            HTTP_CONN_RESPONSE_KEY = "result"

            async_fn = coerce_async(fn)

            class FuncAsyncTransformer(
                pw.AsyncTransformer, output_schema=pw.schema_from_types(result=dict)
            ):
                async def invoke(self, *args, **kwargs) -> dict:
                    args = tuple(
                        (
                            arg.value
                            if isinstance(arg, (pw.Json, pw.PyObjectWrapper))
                            else arg
                        )
                        for arg in args
                    )
                    kwargs = {
                        k: (
                            v.value
                            if isinstance(v, (pw.Json, pw.PyObjectWrapper))
                            else v
                        )
                        for k, v in kwargs.items()
                    }

                    result = await async_fn(*args, **kwargs)

                    return {HTTP_CONN_RESPONSE_KEY: result}

            def table_transformer(table: pw.Table) -> pw.Table:
                return FuncAsyncTransformer(input_table=table).successful

            return table_transformer

        server.serve(
            route,
            schema,
            handler=func_to_transformer(callable_func),
            **additional_endpoint_kwargs,
        )

        return callable_func

   
class InputSchema(pw.Schema):
    question: str = pw.column_definition(
        description="Your question that you want the answer to",
    )


def handler(question):
    question_group_id = str(uuid.uuid4())
    print('INPUT',input)
    res = rag_e2e.invoke(
        {
            "question": question,
            "question_group_id": question_group_id,
        }
    )
    print(f"{res}")

    documents=[doc.model_dump() for doc in res['documents']]
    documents_after_metada=[doc.model_dump() for doc in res['documents_after_metadata_filter']]
    res['documents']=documents
    res['documents_after_metadata_filter']=documents_after_metada
    return res

rest_kwargs = {"methods": ("GET", "POST")}


class FinancialStatementSchema(BaseModel):
    """
    The schema for the financial statement metadata.
    """

    company_name: str = Field(description="The name of the company.")
    year: str = Field(description="The year of the financial statement.")


_system_prompt = prompts.extract_compamy_system_prompt
company_name_and_year_extractor_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        ("human", "Text: \n\n {text}"),
    ]
)
company_name_and_year_extractor = (
    company_name_and_year_extractor_prompt
    | llm.with_structured_output(FinancialStatementSchema)
)


def extract_company_name_and_year_from_nodes(nodes) -> FinancialStatementSchema:
    """
    Extracts the 'Company Name' and 'Year of Report' from a list of nodes.
    """

    # Combine text from nodes to form the document content
    nodes_first_three_pages = []
    for node in nodes:
        if len(node.bbox) > 0 and node.bbox[0].page < 3:
            nodes_first_three_pages.append(node)
    document_text = "\n".join(node.text for node in nodes_first_three_pages)

    res = company_name_and_year_extractor.invoke({"text": document_text})

    return res  # type: ignore


class CustomOpenParse(OpenParse):
    """
    Custom OpenParse class with modified __wrapped__ behavior.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __wrapped__(self, contents: bytes) -> list[tuple[str, dict]]:
        # Import dependencies locally to handle optional imports gracefully
        try:
            import openparse
            from pypdf import PdfReader
        except ImportError as e:
            raise ImportError(
                "Required library not found. Please ensure openparse and pypdf are installed."
            ) from e

        reader = PdfReader(stream=BytesIO(contents))
        doc = openparse.Pdf(file=reader)

        # Original document parsing with custom modifications
        parsed_content = self.doc_parser.parse(doc)
        nodes = list(parsed_content.nodes)
        extracted_statement_schema = extract_company_name_and_year_from_nodes(
            parsed_content.nodes
        )

        company_name = extracted_statement_schema.company_name.lower().strip()
        if company_name.endswith(" inc"):
            company_name = company_name.replace(" inc", "")
        elif company_name.endswith(" inc."):
            company_name = company_name.replace(" inc.", "")

        docs = [
            (
                node.text,
                {
                    "company_name": company_name,
                    "year": extracted_statement_schema.year.strip(),
                    "page_no": node.bbox[0].page if len(node.bbox) > 0 else -1,
                    "variant": str(node.variant),
                },
            )
            for node in nodes
        ]

        return docs


folder = pw.io.fs.read(
    path="./data/",
    format="binary",
    with_metadata=True,
)
sources = [folder]

vision_llm = llms.OpenAIChat(
    model="gpt-4o-mini",
    cache_strategy=DiskCache(),
    retry_strategy=ExponentialBackoffRetryStrategy(max_retries=4),
    verbose=True,
)
TABLE_PARSE_PROMPT = prompts.TABLE_PARSE_PROMPT
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
    cache_strategy=DiskCache()
)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    knn_index = BruteForceKnnFactory(
        reserved_space=1000,
        embedder=embedder,
        metric=pw.engine.BruteForceKnnMetricKind.COS,
        dimensions=1536,
    )
    bm25_index = TantivyBM25Factory(
        ram_budget=5000 * 1024 * 1024, in_memory_index=False
    )
    # usearch_knn_index = UsearchKnnFactory(embedder=embedder)

    hybrid_index_factory = HybridIndexFactory(
        retriever_factories=[bm25_index, knn_index],
    )

    doc_store = DocumentStore(
        *sources,
        retriever_factory=knn_index,
        splitter=None,  # OpenParse parser handles the chunking
        parser=parser,
    )
    server = DocumentStoreServer(
        host=config.VECTOR_STORE_HOST,
        port=config.VECTOR_STORE_PORT,
        document_store=doc_store,
    )

    ##ADDING IN SERVE CALLABLE FOR OTHER END POINTS
    serve_callable(server,"/answer", InputSchema, handler, **rest_kwargs)

    server.run()
