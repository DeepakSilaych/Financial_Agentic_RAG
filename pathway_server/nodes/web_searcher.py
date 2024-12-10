"""
Module for performing web searches using multiple search APIs.

This module queries web search APIs (Tavily, Google, Bing) and processes the results. If Tavily fails, it falls back to Google and Bing search results. The results are then parsed, cleaned, and returned as documents.

Functions:
- search_web: Executes the web search, processes results, and logs them.
"""

from typing import Optional

from langchain.schema import Document
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities import BingSearchAPIWrapper
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()

from nodes.data_loaders import (
    extract_clean_html_data,
    extract_pdf_content,
    get_responses,
)
from utils import log_message, send_logs
import config
from config import LOGGING_SETTINGS


class WebSearchTool(BaseTool):
    """Tool that queries the Tavily Search API and gets back json.
    It will use custom website scraper to retrieve results if Tavily is down
    """

    name: str = "custom_search_results_document"
    description: str = "Custom web searcher"
    max_results: int = 1

    tavily_api_wrapper: TavilySearchResults = TavilySearchResults(max_results=1)
    google_api_wrapper: GoogleSearchAPIWrapper = GoogleSearchAPIWrapper(k=1)
    bing_api_wrapper: BingSearchAPIWrapper = BingSearchAPIWrapper(k=1)  # type: ignore

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> list[Document]:
        try:
            if config.SIMULATE_ERRORS["tavily"]:
                raise RuntimeError("Simulating error in `tavily`")

            docs = self.tavily_api_wrapper.invoke({"query": query})
            documents = []
            log_message(f"{docs} , type : {type(docs)} " , 1)

            # Process docs based on its actual structure
            if isinstance(docs, list) and all(isinstance(d, Document) for d in docs):
                for d in docs:  # If docs are Document instances
                    documents.append(
                        Document(metadata=d.metadata, page_content=d.page_content)
                    )
            elif isinstance(docs, list) and all(
                isinstance(d, dict) and "content" in d for d in docs
            ):
                for d in docs:  # If docs are dictionaries
                    documents.append(
                        Document(metadata={"url": d["url"]}, page_content=d["content"])
                        # Document(metadata=d.metadata, page_content=d.page_content)
                    )
            else:
                web_results = "\n".join(
                    docs
                )  # Assume docs is a list of strings or has content directly
                web_results = Document(page_content=web_results)
                documents = [web_results]

            return documents
        except Exception:
            try:
                try:
                    if config.SIMULATE_ERRORS["google_search"]:
                        raise RuntimeError("Simulating error in `google_search`")
                    search_results = self.google_api_wrapper.results(
                        query, num_results=1
                    )
                except:
                    try:
                        if config.SIMULATE_ERRORS["bing"]:
                            raise RuntimeError("Simulating error in `bing`")
                        search_results = self.bing_api_wrapper.results(
                            query, num_results=1
                        )
                    except:
                        raise RuntimeError("Unable to retrieve web search results")
                search_result_links = [res["link"] for res in search_results]

                html_links = [
                    link for link in search_result_links if not link.endswith(".pdf")
                ]
                pdf_links = [
                    res["link"]
                    for res in search_results
                    if res["link"].endswith(".pdf")
                ]

                responses = get_responses(html_links)
                extracted_texts = [extract_clean_html_data(res) for res in responses]
                extracted_texts = [text for text in extracted_texts if text is not None]
                extracted_texts = [text[:5000] for text in extracted_texts]
                docs = [
                    Document(metadata={"url": link}, page_content=text)
                    for link, text in zip(html_links, extracted_texts)
                ]

                for link in pdf_links:
                    extracted_result = extract_pdf_content(link)
                    if extracted_result:
                        docs.append(
                            Document(
                                metadata={"url": link}, page_content=extracted_result
                            )
                        )

                return docs
            except Exception as e:
                raise RuntimeError("Unable to retrieve web search results")


web_search_tool = WebSearchTool()


def search_web(state):
    log_message("---WEB SEARCH---")
    question = state.get("original_question", state["question"])

    docs = web_search_tool.invoke({"query": question})

    ###### log_tree part
    import uuid, nodes

    id = str(uuid.uuid4())
    child_node = nodes.search_web.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}

    if (
        not LOGGING_SETTINGS["search_web"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "documents": docs,
        "original_question": question,
        "web_searched": True,
        "prev_node": child_node,
        "log_tree": log_tree,
    }

    send_logs(
        parent_node=parent_node,
        curr_node=child_node,
        child_node=None,
        input_state=state,
        output_state=output_state,
        text=child_node.split("//")[0],
    )

    ######

    log_message(f" \n\n Web Results : \n\n {docs} \n\n")

    return output_state
