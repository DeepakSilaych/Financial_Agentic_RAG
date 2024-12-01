from dotenv import load_dotenv

load_dotenv()

import logging
import os
from io import BytesIO

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

os.environ["TESSDATA_PREFIX"] = "/home/ganeshr/miniconda3/envs/harshit/share/tessdata/"


class FinancialStatementSchema(BaseModel):
    """
    The schema for the financial statement metadata.
    """

    company_name: str = Field(description="The name of the company.")
    year: str = Field(description="The year of the financial statement.")


_system_prompt = """Extract the company name and fiscal year from the following financial statement text. The fiscal year is often noted as a specific year (e.g., 2023 or 'Fiscal Year 2023'). """
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
TABLE_PARSE_PROMPT = """Explain the following table row by row, covering each detail precisely.
For each row, include all values and their associated units, measurements, or categories with the appropriate column names.
Begin each row explanation by identifying the row title or label if present. For each of the rows, describe each column with its specific information and unit, and ensure no data is skipped.
Make sure each row is in natural language and not just labels and numbers.
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
    server.run()
