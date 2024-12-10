"""
Document Reranking Module with Cohere API

This module is responsible for reranking a set of documents based on their relevance to a user query. 
It uses Cohere's API for document reranking, which provides a numerical relevance score for each document 
and a brief summary explaining why the document is relevant.

### Key Components:

1. **DocumentRerank (BaseModel)**:
   - A data model representing the reranking results for a document.
   - `relevance_score`: A numerical value indicating the relevance of the document to the query.
   - `summary`: A short description explaining why the document is considered relevant to the query.

2. **rerank_documents**:
   - The main function that takes a list of documents and reranks them based on their relevance to the user's question.
   - Uses Cohere's `rerank` API to compute relevance scores and returns the documents sorted by relevance.

### Workflow:
1. The function `rerank_documents` retrieves the question and documents from the state.
2. It sends the documents and the query to the Cohere API for reranking.
3. The documents are reranked based on the relevance scores returned by Cohere, with the highest-scoring documents placed first.
4. Logs the reranking process and sends detailed logs to the server.
5. Returns the reranked documents.

### Dependencies:
- **uuid**: For generating unique identifiers for logging purposes.
- **pydantic**: For structured data validation and creation of the `DocumentRerank` model.
- **cohere**: For interacting with Cohere's API to rerank documents based on their relevance to the query.
- **state, nodes**: To interact with the overall system state and track the node transitions in the process flow.
- **utils.send_logs**: To send logs for tracking and analysis of the reranking process.
- **config.LOGGING_SETTINGS**: For controlling logging behavior based on configuration settings.

### Cohere API:
- The `rerank_documents` function interacts with the `cohere.Client` to use the `rerank` model provided by Cohere. The model computes a relevance score for each document relative to the user query. The function sorts the documents based on these scores to prioritize the most relevant ones.

### Example Workflow:
1. **Rerank Process**:
   - A set of documents is retrieved based on a user query.
   - The documents are sent to Cohere's `rerank` API, where each document is scored based on how relevant it is to the user's query.
   - The documents are sorted in descending order of their relevance score.
   - The sorted documents are returned as the output, and a log is generated with details of the reranking process.

2. **Logging**:
   - Logs the document reranking process and the resulting sorted documents.
   - Logs are sent to the server for tracking, which includes a hierarchical node structure representing the process flow.

### Server Logs:
- Server logs are sent after the reranking is completed, containing details about the documents' new order, reasons for the reranking, and other contextual information.

"""

import uuid
from pydantic import BaseModel, Field
import cohere

import state, nodes
from utils import log_message, send_logs
from config import LOGGING_SETTINGS

cohere_client = cohere.Client()


class DocumentRerank(BaseModel):
    """Structure for document reranking based on query relevance."""

    relevance_score: float = Field(
        description="A numerical score indicating document relevance to the query."
    )
    summary: str = Field(
        description="Short summary highlighting why this document is relevant to the query."
    )


def rerank_documents(state: state.InternalRAGState):
    log_message("---RERANKING DOCUMENTS WITH COHERE---")
    documents = state["documents"]
    if len(documents) == 0:
        reranked_docs = documents
    else:
        query = state["question"]
        document_texts = [doc.page_content for doc in documents]

        # Use Cohere's rerank API to rerank the documents
        response = cohere_client.rerank(
            model="rerank-english-v2.0",  # Specify the model version
            query=query,
            documents=document_texts,
            top_n=len(documents),  # Retrieve all documents in ranked order
        ).results

        # Sort documents by relevance score (highest first)
        reranked_docs = [documents[res.index] for res in response]

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = nodes.rerank_documents.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if (
        not LOGGING_SETTINGS["rerank_documents"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "documents": reranked_docs,
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

    return output_state
