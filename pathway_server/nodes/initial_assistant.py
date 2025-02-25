# This script contains the `combine_conversation_history` function which processes user queries
# by combining conversation history and relevant retrieved context. It decides whether the query
# should trigger a Retrieval-Augmented Generation (RAG) pipeline or be answered directly.
#
# Key Components:
# 1. **Conversation History Retrieval**: Retrieves recent conversation messages and relevant
#    context from the vector store using a cache retriever.
# 2. **Decision-Making Process**: Forms a prompt for the AI model to refine the query and decide
#    whether the RAG pipeline should be triggered or not.
# 3. **Logging and Output**: Logs all critical steps including refined queries and pipeline decisions
#    to a logging system. Additionally, generates a structured output state that can be used in the
#    broader application pipeline.
#
# The function also integrates error handling, logging, and image URL handling (if provided).
# It uses LangChain's `ChatPromptTemplate` and structured output functionality for smooth
# integration with large language models (LLMs).

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

import state, nodes
import config
from prompt import prompts
from llm import llm
from utils import log_message
import uuid
from utils import send_logs
from config import LOGGING_SETTINGS
from retriever import cache_retriever


class QueryDraftDecision(BaseModel):
    """Draft a refined query and determine routing."""

    refined_question: str = Field(
        description="The refined question incorporating conversation history."
    )
    trigger_rag_pipeline: bool = Field(
        description="Flag indicating if the RAG pipeline should be triggered."
    )


_system_prompt = prompts.initial_assistant_prompt

import os
import jsonlines


def combine_conversation_history(state: state.OverallState, vector_store=None):
    messages = []
    user_id = state["user_id"]
    file_path = os.path.join("data_convo", "conversation_history.jsonl")
    if os.path.exists(file_path):
        log_message(f"Loading conversation history from {file_path}.")
        with jsonlines.open(file_path) as reader:
            for record in reader:
                if record["record_id"] == user_id:
                    messages.append(HumanMessage(role="User", content=record["query"]))
                    messages.append(AIMessage(role="Chatbot", content=record["answer"]))
    else:
        log_message(f"No external conversation history found in {file_path}.")

    num_messages = len(messages)
    if num_messages == 0:
        log_message("No conversational history available.")
        recent_messages = "No prior conversation history available."
    else:
        log_message(
            f"Using the last {min(config.NUM_PREV_MESSAGES, num_messages)} messages for context."
        )
        recent_messages = "\n".join(
            f"{msg.role}: {msg.content}"
            for msg in messages[-config.NUM_PREV_MESSAGES :]
        )

    log_message("Retrieving relevant conversational history from vector DB.")
    query = state["question"]
    retrieved_contexts = cache_retriever.similarity_search(
        query,
        config.NUM_PREV_MESSAGES,
        metadata_filter=nodes.convert_metadata_to_jmespath({"record_id": user_id}),
    )

    retrieved_context = "\n".join(
        f"User:{ctx.page_content}\n Chatbot : {ctx.metadata['answer']}"
        for ctx in retrieved_contexts
    )

    # Combine both sources of context
    combined_context = f"Recent Messages:\n{recent_messages}\n\nRetrieved Context:\n{retrieved_context}"

    # Process query and create decision prompt
    new_query = state["question"]
    new_message = HumanMessage(role="User", content=new_query)
    log_message(f"User: {new_query}")
    log_message("-----PROCESSING NEW QUERY BASED ON COMBINED CONTEXT-----")
    image_url = state.get("image_url", "")
    if image_url != "":
        image_url = f"data:image/jpeg;base64,{image_url}"
        decision_prompt = ChatPromptTemplate.from_messages(
            messages=[
                SystemMessage(content=_system_prompt),
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": f"Conversation History: {combined_context} \nImage being shared may or may not be relevant to the question.",
                        },
                        {"type": "image_url", "image_url": {"url": f"{image_url}"}},
                        {"type": "text", "text": f"Question: {new_query}"},
                    ]
                ),
            ]
        )
    else:
        decision_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", _system_prompt),
                (
                    "human",
                    f"Conversation history: {combined_context}\nQuestion: {new_query}",
                ),
            ]
        )

    # Determine query refinement and pipeline routing
    query_decider = decision_prompt | llm.with_structured_output(QueryDraftDecision)
    decision_data: QueryDraftDecision = query_decider.invoke({})  # type: ignore
    log_message(f"Refined Question: {decision_data.refined_question}")
    log_message(f"Trigger RAG Pipeline: {decision_data.trigger_rag_pipeline}")

    ###### Logging tree setup
    id = str(uuid.uuid4())
    child_node = nodes.combine_conversation_history.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}

    if not LOGGING_SETTINGS["combine_conversation_history"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]

    ##### Server Logging part
    output_state = {
        "question": decision_data.refined_question,
        "messages": [new_message],
        "final_answer": "none",
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

    # Return output state
    return output_state


# # With Indexing to the Cache Server
# def combine_conversation_history_v2(state: state.OverallState, vector_store):
#     # Retrieve relevant context from vector DB
#     log_message("Retrieving relevant conversational history from vector DB.")
#     query = state["question"]
#     retrieved_contexts = cache_retriever.similarity_search(
#         query,
#         config.NUM_PREV_MESSAGES,
#         metadata_filter=nodes.convert_metadata_to_jmespath(
#             ["conversational_awareness"], ["type"]
#         ),
#     )

#     # Format the retrieved context for use in the decision-making process
#     conversation_history = "\n".join(
#         f"{context['role']}: {context['content']}" for context in retrieved_contexts
#     )

#     new_query = state["question"]
#     new_message = HumanMessage(role="User", content=new_query)
#     log_message(f"User: {new_query}")
#     log_message("-----PROCESSING NEW QUERY BASED ON RETRIEVED CONTEXT-----")
#     image_url = state.get("image_url", "")
#     if image_url != "":
#         image_url = f"data:image/jpeg;base64,{image_url}"
#         decision_prompt = ChatPromptTemplate.from_messages(
#             messages=[
#                 SystemMessage(content=_system_prompt),
#                 HumanMessage(
#                     content=[
#                         {
#                             "type": "text",
#                             "text": f"Conversation History: {conversation_history} \nImage being shared may or may not be relevant to the question.",
#                         },
#                         {"type": "image_url", "image_url": {"url": f"{image_url}"}},
#                         {"type": "text", "text": f"Question: {new_query}"},
#                     ]
#                 ),
#             ]
#         )
#     else:
#         decision_prompt = ChatPromptTemplate.from_messages(
#             [
#                 ("system", _system_prompt),
#                 (
#                     "human",
#                     f"Conversation history: {conversation_history}\nQuestion: {new_query}",
#                 ),
#             ]
#         )

#     query_decider = decision_prompt | llm.with_structured_output(QueryDraftDecision)
#     decision_data: QueryDraftDecision = query_decider.invoke({})  # type: ignore
#     log_message(f"Refined Question: {decision_data.refined_question}")
#     log_message(f"Trigger RAG Pipeline: {decision_data.trigger_rag_pipeline}")

#     ###### log_tree part
#     id = str(uuid.uuid4())
#     child_node = nodes.combine_conversation_history_v2.__name__ + "//" + id
#     parent_node = state.get("prev_node", "START")
#     log_tree = {}

#     if not LOGGING_SETTINGS[
#         "combine_conversation_history_v2"
#     ]:  # TODO : Add in config ( True )
#         child_node = parent_node

#     log_tree[parent_node] = [child_node]

#     ######

#     if decision_data.trigger_rag_pipeline:
#         log_message("RAG pipeline will be triggered.")

#         ##### Server Logging part

#         output_state = {
#             "question": decision_data.refined_question,
#             "messages": [new_message],
#             "final_answer": "none",
#             "prev_node": child_node,
#             "log_tree": log_tree,
#         }

#         send_logs(
#             parent_node=parent_node,
#             curr_node=child_node,
#             child_node=None,
#             input_state=state,
#             output_state=output_state,
#             text=child_node.split("//")[0],
#         )

#         ######

#         return output_state

#     else:
#         log_message("RAG pipeline will NOT be triggered. Generating direct answer.")

#         new_question = f"""
#         Given the conversation history and the refined query, directly answer the user's query.
#         Conversation history: \n\n {conversation_history} \n\n User: {new_query}
#         """

#         output_state = {
#             "question": new_question,
#             "messages": [new_message],
#             "final_answer": "Generate from context",
#             "prev_node": child_node,
#             "log_tree": log_tree,
#         }

#         send_logs(
#             parent_node=parent_node,
#             curr_node=child_node,
#             child_node=None,
#             input_state=state,
#             output_state=output_state,
#             text=child_node.split("//")[0],
#         )

#         ######

#         return output_state
