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