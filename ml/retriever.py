from langchain_community.vectorstores import PathwayVectorClient
from typing import Optional
from pathway.xpacks.llm.vector_store import VectorStoreClient
import config

class PathwayVectorStoreClient(PathwayVectorClient):
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        url: Optional[str] = None,
        timeout: int = config.VECTOR_STORE_TIMEOUT,
    ):
        super().__init__(host, port, url)

        self.client = VectorStoreClient(host, port, url, timeout)

    def similarity_search(self, *args, **kwargs):
        # Check config for RETRIEVER_FALL_BACK
        if config.RETREIVER_FALL_BACK:
            raise ValueError("RETREIVER FALL BACK ERROR")
        else:
            # Call the parent class's similarity_search method
            return super().similarity_search(*args, **kwargs)

retriever = PathwayVectorStoreClient(
    url=f"http://{config.VECTOR_STORE_HOST}:{config.VECTOR_STORE_PORT}",
)

cache_retreiver = PathwayVectorStoreClient(
    url=f"http://{config.CACHE_STORE_HOST}:{config.CACHE_STORE_PORT}"
)
