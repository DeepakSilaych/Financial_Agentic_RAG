from pydantic import BaseModel, Field
import cohere

import state
from utils import log_message

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
    return {"documents": reranked}
