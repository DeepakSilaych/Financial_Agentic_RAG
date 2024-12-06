from pydantic import BaseModel, Field
import cohere

import state , nodes
from utils import log_message , send_logs 
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
    query = state["question"]
    formatted_documents = [{"text": doc} for doc in documents]

    # Use Cohere's rerank API to rerank the documents
    response = cohere_client.rerank(
        model="rerank-english-v2.0",  # Specify the model version
        query=query,
        documents=formatted_documents,
        top_n=len(documents),  # Retrieve all documents in ranked order
    )

    # Store reranked documents based on relevance score
    reranked_docs = [(doc.text, doc.relevance_score) for doc in response]

    # Sort documents by relevance score (highest first)
    reranked_docs = sorted(reranked_docs, key=lambda x: x[1], reverse=True)
    reranked = [doc for doc, score in reranked_docs]

    ###### log_tree part
    # import uuid , nodes 
    id = str(uuid.uuid4())
    child_node = nodes.rerank_documents.__name__ + "//" + id
    parent_node = state.get("prev_node" , "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not LOGGING_SETTINGS['rerank_documents'] or state.get("send_log_tree_logs" , "") == "False":
        child_node = parent_node  
    
    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "documents": reranked , 
        "prev_node" : child_node,
        "log_tree" : log_tree ,
    }


    send_logs(
        parent_node = parent_node , 
        curr_node= child_node , 
        child_node=None , 
        input_state=state , 
        output_state=output_state , 
        text=child_node.split("//")[0] ,
    )
    
    ######

    return output_state 

    return {"documents": reranked}
