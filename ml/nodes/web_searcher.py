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
from utils import log_message

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
    question = state["original_question"]

    # print("Inside search_web")
    # Perform web search
    docs = web_search_tool.invoke({"query": question})
    
    
    # print([doc["url"] for doc in docs])
    urls = [doc["url"] for doc in docs]
    urls = [tldextract.extract(url) for url in urls]
    urls = [".".join([url.subdomain, url.domain, url.suffix]) for url in urls]
    
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

    log_message(f" \n\n Web Results : \n\n {documents} \n\n")

    return {"documents": documents, "original_question": question, "web_searched": True, "urls": urls}


google_search_retriever = GoogleSearchAPIWrapper(
    k=5,
    google_api_key="AIzaSyDoqHaSM22-uuzuZT9K9emeL25xzlb0lLc",
    google_cse_id="92f402682f5a54958",
)


def search_google_snnipets(state):

    # Return snnipets from google search ( does not return source urls )
    # All results are returned as 1 combined string ( by the google_search_retriever)
    question = state["original_question"]
    search_results = google_search_retriever.run(question)
    state["documents"] = [search_results]


def google_search_scrapper(state):
    # Working fine ( adds the scrapped content along with the source url to the state["documents"] )
    # Scrapping too much content ( can't pass this to llm for answer generation due to very long scrapped content )

    question = state["original_question"]
    documents = []
    search_results = google_search_retriever.results(query=question, num_results=3)
    search_result_links = [res["link"] for res in search_results]
    html_links = [link for link in search_result_links if not link.endswith(".pdf")]
    pdf_links = [res["link"] for res in search_results if res["link"].endswith(".pdf")]

    for link in html_links:
        res = get_responses(link)
        extracted_result = extract_clean_html_data(res)
        documents.append({"metadata": {"url": link}, "page_content": extracted_result})

    for link in pdf_links:
        extracted_result = extract_pdf_content(link)
        documents.append({"metadata": {"url": link}, "page_content": extracted_result})

    # extracted_search_results = [
    #                 extract_clean_html_data(res)
    #                 for res in get_responses(html_links)
    #             ]
    # extracted_search_results += [
    #                 extract_pdf_content(link) for link in pdf_links
    #             ]

    state["documents"] = documents

    return state
