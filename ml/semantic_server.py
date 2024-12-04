from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.servers import DocumentStoreServer
from pathway.stdlib.indexing import BruteForceKnnFactory
from pathway.udfs import DiskCache
from pathway.xpacks.llm import embedders
import pathway as pw
from dotenv import load_dotenv
import config
from langchain_core.documents import Document

load_dotenv()

# Initialize Embedder and KNN Index
embedder = embedders.OpenAIEmbedder(
    cache_strategy=DiskCache()
)

knn_index = BruteForceKnnFactory(
    reserved_space=1000,
    embedder=embedder,
    metric=pw.engine.BruteForceKnnMetricKind.COS,
    dimensions=1536,
)

# Define schema to match JSON structure
class InputSchema(pw.Schema):
    record_id: str
    query: str
    answer: str
    type: str  # Metadata tag for differentiation


t1 = pw.io.fs.read(
    path="data_cache/",
    format="json",
    schema=InputSchema,
)


t2 = pw.io.fs.read(
    path="data_convo/",
    format="json",
    schema=InputSchema,
)

pw.universes.promise_are_pairwise_disjoint(t1, t2)
t3 = t1.concat(t2)
docs = t3.select(
    data=pw.this.query + "########" + pw.this.answer,
    _metadata={"is_cache":pw.this.type=="cache"},
    **t3,
)

class ParseUtf8(pw.UDF):
    def __wrapped__(self, contents: bytes) -> list[tuple[str, dict]]:
        parts = contents.split('########')
        question = parts[0]
        answer = parts[1]
        type_tag = parts[2] if len(parts) > 2 else None

        docs: list[tuple[str, dict]] = [
            (question, {"answer": answer, "type": type_tag})
        ]
        return docs

    def __call__(self, contents: pw.ColumnExpression, **kwargs) -> pw.ColumnExpression:
        return super().__call__(contents, **kwargs)


parser=ParseUtf8()

# Initialize the DocumentStore
vector_store = DocumentStore(
    docs,
    retriever_factory=knn_index,
    parser=parser,
    splitter=None,
)

# Run the server
server = DocumentStoreServer(
    host=config.CACHE_STORE_HOST,
    port=config.CACHE_STORE_PORT,
    document_store=vector_store,
)
server.run()



