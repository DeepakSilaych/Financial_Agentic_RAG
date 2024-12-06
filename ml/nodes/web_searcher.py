from langchain.schema import Document
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.errors import NodeInterrupt
import tldextract
import config

from nodes.data_loaders import (
    extract_clean_html_data,
    extract_pdf_content,
    get_responses,
)
from langchain_google_community import GoogleSearchAPIWrapper
from utils import log_message, send_logs
from config import LOGGING_SETTINGS
import config


web_search_tool = TavilySearchResults(max_results=1)


def search_web(state):
    """
    Web search based on the re-phrased question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with appended web results
    """

    log_message("---WEB SEARCH---")
    question = state.get("original_question", state["question"])

    # print("Inside search_web")
    # Perform web search
    docs = web_search_tool.invoke({"query": question})

    # print([doc["url"] for doc in docs])
    # urls = [doc["url"] for doc in docs]
    # urls = [tldextract.extract(url) for url in urls]
    # urls = [".".join([url.subdomain, url.domain, url.suffix]) for url in urls]

    documents = []
    # Process docs based on its actual structure
    if isinstance(docs, list) and all(isinstance(d, Document) for d in docs):
        for d in docs:  # If docs are Document instances
            documents.append(Document(metadata=d.metadata, page_content=d.page_content))
    elif isinstance(docs, list) and all(
        isinstance(d, dict) and "content" in d for d in docs
    ):
        for d in docs:  # If docs are dictionaries
            documents.append(
                Document(metadata={"url": d["url"]}, page_content=d["content"])
            )
    else:
        web_results = "\n".join(
            docs
        )  # Assume docs is a list of strings or has content directly
        web_results = Document(page_content=web_results)
        documents = [web_results]

    # Wrap the final results in a Document
    # web_results = Document(page_content=web_results)

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
        "documents": documents,
        "original_question": question,
        "web_searched": True,
        # "urls": urls ,
        "prev_node": child_node,
        "log_tree": log_tree,
    }

    if (config.WEB_FALL_BACK):
        raise RuntimeError("This is a runtime error (FALLBACK CODE)")

    send_logs(
        parent_node=parent_node,
        curr_node=child_node,
        child_node=None,
        input_state=state,
        output_state=output_state,
        text=child_node.split("//")[0],
    )

    ######

    log_message(f" \n\n Web Results : \n\n {documents} \n\n")



    return output_state


google_search_retriever = GoogleSearchAPIWrapper(
    k=5,
    google_api_key="AIzaSyDoqHaSM22-uuzuZT9K9emeL25xzlb0lLc",
    google_cse_id="92f402682f5a54958",
)


def search_google_snippets(state):
    # Return snnipets from google search ( does not return source urls )
    # All results are returned as 1 combined string ( by the google_search_retriever)
    question = state.get("original_question", state["question"])
    search_results = google_search_retriever.run(question)
    state["documents"] = [search_results]


def google_search_scraper(state):
    # Working fine ( adds the scrapped content along with the source url to the state["documents"] )
    # Scrapping too much content ( can't pass this to llm for answer generation due to very long scrapped content )

    question = state.get("original_question", state["question"])

    search_results = google_search_retriever.results(query=question, num_results=3)
    search_result_links = [res["link"] for res in search_results]

    html_links = [link for link in search_result_links if not link.endswith(".pdf")]
    pdf_links = [res["link"] for res in search_results if res["link"].endswith(".pdf")]

    responses = get_responses(html_links)
    documents = [
        {"metadata": {"url": link}, "page_content": extract_clean_html_data(res)[:5000]}
        for link, res in zip(html_links, responses)
    ]

    for link in pdf_links:
        extracted_result = extract_pdf_content(link)
        documents.append({"metadata": {"url": link}, "page_content": extracted_result})

    return {"documents": documents}
