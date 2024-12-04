from typing import Optional

# in order to allow timoouts, we use a temporary fix
from pathway.xpacks.llm.vector_store import VectorStoreClient
from typing import Any, Optional

import requests
import json
import config
import logging
from langchain_core.documents import Document
from retriever import PathwayVectorStoreClient


class CustomPathwayVectorStoreClient():
    def __init__(
        self,
        server1_url: Optional[str] = None,
        server2_url: Optional[str] = None,
        timeout: int = config.VECTOR_STORE_TIMEOUT,
    ):
        self.client1 = PathwayVectorStoreClient(host=None, port=None, url=server1_url, timeout=timeout)
        self.client2 = PathwayVectorStoreClient(host=None, port=None, url=server2_url, timeout=timeout)
        self.url1 = server1_url
        self.url2 = server2_url
        self.timeout = timeout

    def check_server_status(self, url):
        stat_url = url + "/v1/statistics"
        try:
            response = requests.post(
                stat_url,
                json={},
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            responses = response.json()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def get_active_url(self):
        if self.check_server_status(self.url1):
            print("Server 1 is active")
            return self.url1
        elif self.check_server_status(self.url2):
            print("Server 2 is active")
            return self.url2
        else:
            print("Both servers are inactive")
            print("Using server 1 as default")
            return self.url1


    def query(
        self,
        query: str,
        k: int = 3,
        metadata_filter: str | None = None,
        filepath_globpattern: str | None = None,
    ) -> list[dict]:
        """
        Perform a query to the vector store and fetch results.

        Args:
            query:
            k: number of documents to be returned
            metadata_filter: optional string representing the metadata filtering query
                in the JMESPath format. The search will happen only for documents
                satisfying this filtering.
            filepath_globpattern: optional glob pattern specifying which documents
                will be searched for this query.
        """

        data = {"query": query, "k": k}
        if metadata_filter is not None:
            data["metadata_filter"] = metadata_filter
        if filepath_globpattern is not None:
            data["filepath_globpattern"] = filepath_globpattern
        url = self.get_active_url() + "/v1/retrieve"
        response = requests.post(
            url,
            data=json.dumps(data),
            headers=self._get_request_headers(),
            timeout=self.timeout,
        )

        responses = response.json()
        return sorted(responses, key=lambda x: x["dist"])
    
    def similarity_search(self, query: str, k: int = 4, **kwargs: Any):
        try:
            response = requests.post(
                self.url1 + "/v1/health",
                json={},
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            text = response.text
            print(f"Server 1: {text}")
        except Exception as e:
            print(f"Error: {e}")
            text = "none"

        try:
            if text != "none":
                ret1 = self.client1.similarity_search(query, k, **kwargs)
            else:
                ret1 = []
        except Exception as e:
            print(f"Error: {e}")
            ret1 = []

        try:
            if text != "both":
                ret2 = self.client2.similarity_search(query, k, **kwargs)
            else:
                ret2 = []
        except Exception as e:
            print(f"Error: {e}")
            ret2 = []

        return ret1 + ret2



    # Make an alias
    __call__ = query

    def get_vectorstore_statistics(self):
        """Fetch basic statistics about the vector store."""

        url = self.get_active_url() + "/v1/statistics"
        response = requests.post(
            url,
            json={},
            headers=self._get_request_headers(),
            timeout=self.timeout,
        )
        responses = response.json()
        return responses

    def get_input_files(
        self,
        metadata_filter: str | None = None,
        filepath_globpattern: str | None = None,
    ):
        """
        Fetch information on documents in the the vector store.

        Args:
            metadata_filter: optional string representing the metadata filtering query
                in the JMESPath format. The search will happen only for documents
                satisfying this filtering.
            filepath_globpattern: optional glob pattern specifying which documents
                will be searched for this query.
        """
        url = self.get_active_url() + "/v1/inputs"
        response = requests.post(
            url,
            json={
                "metadata_filter": metadata_filter,
                "filepath_globpattern": filepath_globpattern,
            },
            headers=self._get_request_headers(),
            timeout=self.timeout,
        )
        responses = response.json()
        return responses

    def _get_request_headers(self):
        request_headers = {"Content-Type": "application/json"}
        # request_headers.update(self.additional_headers)
        return request_headers


retriever = CustomPathwayVectorStoreClient(
    server1_url=f"http://{config.MULTI_SERVER_HOST}:{config.MULTI_SERVER_PORT}",
    server2_url=f"http://{config.FAST_VECTOR_STORE_HOST}:{config.FAST_VECTOR_STORE_PORT}",
    timeout=5,
)