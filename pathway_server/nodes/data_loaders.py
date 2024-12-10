"""
Web Content Extraction and Processing Module

This module contains utility functions for extracting and processing content from various online sources, such as PDFs and HTML pages. 
It includes functions to fetch the content from URLs, extract and clean text from PDF and HTML documents, 
and store or process this content for further use, such as creating embeddings for document storage.

### Key Functions:

1. **extract_pdf_content(link: str) -> Optional[str]**:
   - Extracts content from a PDF located at the specified URL. 
   - The function loads the PDF using the PyPDFLoader, retrieves all the text content from the document's pages, 
     and returns the content as a string.
   - Returns `None` if the PDF cannot be loaded or processed.

2. **extract_clean_html_data(res: Optional[requests.Response]) -> Optional[str]**:
   - Extracts clean and readable text from an HTML page by parsing the HTML content with BeautifulSoup.
   - The function strips extraneous elements such as navigation, footers, and images.
   - If the response is `None` or the body is empty, it returns `None`.
   - It ensures content is cleaned of excessive whitespace and formatted for better readability.

3. **get_responses(links: list[str]) -> list[requests.Response]**:
   - Fetches content from a list of URLs using multi-threading for concurrent requests.
   - Utilizes Python's `concurrent.futures.ThreadPoolExecutor` to handle multiple HTTP requests in parallel, 
     speeding up the process of gathering HTML content from multiple links.

4. **get_content(node) -> str**:
   - A helper function used by `extract_clean_html_data` to recursively extract text content from an HTML node.
   - It handles different HTML tags like `<a>`, `<nav>`, `<footer>`, `<img>`, and `<svg>`, 
     ensuring that links and unwanted tags are processed or ignored as needed.
   - This function builds a clean string representation of the document's content.

### Data Processing:

- **Text Extraction and Cleaning**:
   - HTML and PDF documents are processed to extract the relevant textual content.
   - The HTML content is parsed and cleaned to remove unnecessary elements and format the content for further processing.
   - The PDF content is extracted page by page and combined into a single text string.

- **Parallel Requests**:
   - For improved efficiency, requests to fetch HTML content from multiple URLs are performed concurrently using Python’s `ThreadPoolExecutor`.
   - This allows for faster data fetching from multiple sources.

- **Commented-out Functions**:
   - The `load_html_data` function (commented-out) outlines an example of how the extracted HTML content can be split into chunks, 
     cleaned, and then embedded for storage in a database. 
   - It also includes an optional check for unrecognized characters in the text.

### Potential Use Cases:

- **Web Scraping**:
   - Extracting content from various web pages, such as news articles, research papers, or any other online content for further processing or analysis.

- **Document Embedding**:
   - The module could be part of a system that collects web-based documents, processes the text, splits them into smaller chunks, and stores them in a vector database for later querying.

- **Data Preprocessing for NLP**:
   - Extracted and cleaned data can be used for training machine learning models or for tasks like information retrieval and document search.

### Dependencies:
- **requests**: For making HTTP requests to fetch web pages and PDF content.
- **concurrent.futures**: For concurrent HTTP requests to handle multiple links at once.
- **BeautifulSoup**: For parsing and extracting clean text from HTML documents.
- **PyPDFLoader**: For loading and extracting text from PDF files.
- **langchain**: For text splitting and processing (e.g., for embeddings or document storage).
"""

from typing import Union, Optional
import re
import concurrent.futures as cf
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

from langchain_core.embeddings import Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from bs4 import BeautifulSoup

# from instigpt import config

# Suppress the warnings from urllib3 regarding SSL verification
urllib3.disable_warnings(category=InsecureRequestWarning)


def extract_pdf_content(link: str) -> Optional[str]:
    try:
        loader = PyPDFLoader("/tmp/live_extract.pdf")
        loader.web_path = link
    except:
        return None

    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])


def extract_clean_html_data(res: Optional[requests.Response]) -> Optional[str]:
    if res is None:
        return None

    html = res.text
    soup = BeautifulSoup(html, "lxml")
    if soup.body is None:
        return None
    content = "\n".join([get_content(child) for child in soup.body.children])  # type: ignore
    content = re.sub(r"\s{2,}", "\n", content)
    return content


def get_responses(links: list[str]) -> list[requests.Response]:
    responses = []
    session = requests.Session()
    with cf.ThreadPoolExecutor() as executor:
        responses = list(
            executor.map(lambda link: session.get(link, verify=False), links)
        )
    return responses


def get_content(node) -> str:
    name = node.name
    if name is None:
        if str(node) == "\n":
            return " "
        return node.text
    elif name == "a":
        # return get_content(node)
        if node.text != "":
            return f"{node.text} ({node.get('href')}) "
        else:
            text = " ".join([get_content(child) for child in node.children]).replace(
                "\n", ""
            )
            return f"{text} ({node.get('href')}) "
    elif name == "nav" or name == "footer" or name == "img" or name == "svg":
        return ""

    content = ""
    for child in node.children:
        content += get_content(child)

    return content


######################

# def has_unrecognized_characters(text):
#     count = sum((not c.isascii() or not c.isprintable()) and c != "\n" for c in text)
#     if (count / len(text)) * 100 > 0.1:
#         return True
#     else:
#         return False


# def load_html_data(
#     client: ClientAPI,
#     embeddings: Embeddings,
#     data_path: Union[str, list[str]],
# ) -> int:
#     """Fetches the html content from the link(s), extracts requried content and
#     then stores it in the database along with its embeddings.

#     returns: int: number of dicuments stored in the database
#     """
#     if type(data_path) == str:
#         data_path = [data_path]

#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=2000,
#         chunk_overlap=200,
#         length_function=len,
#         is_separator_regex=True,
#     )
#     coll = client.get_or_create_collection(config.COLLECTION_NAME)
#     num_docs_added = 0

#     for res in get_responses(data_path):  # type: ignore
#         if res is None:
#             continue
#         try:
#             html = res.text
#             soup = BeautifulSoup(html, "lxml")
#             if soup.body is None:
#                 continue
#             content = "\n".join([get_content(child) for child in soup.body.children])  # type: ignore
#             content = re.sub(r"\s{2,}", "\n", content)
#             docs = text_splitter.split_text(content)
#             docs = [doc for doc in docs if not has_unrecognized_characters(doc)]
#             metadatas = [{"source": res.url} for _ in range(len(docs))]
#             ids = [f"{res.url}-{i}" for i in range(len(docs))]
#         except AssertionError:
#             continue

#         if len(ids) == 0:
#             continue

#         coll.add(
#             documents=docs,
#             embeddings=embeddings.embed_documents(docs),  # type: ignore
#             metadatas=list(metadatas),
#             ids=ids,
#         )
#         num_docs_added += len(docs)

#     return num_docs_added
