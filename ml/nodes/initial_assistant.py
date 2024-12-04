from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

import state , nodes
import config
from llm import llm
from utils import log_message
import uuid
from utils import send_logs
from config import LOGGING_SETTINGS
from retriever import cache_retreiver

class QueryDraftDecision(BaseModel):
    """Draft a refined query and determine routing."""

    refined_question: str = Field(
        description="The refined question incorporating conversation history."
    )
    trigger_rag_pipeline: bool = Field(
        description="A boolean indicating whether the RAG pipeline should be triggered."
    )


_system_prompt = """
You are a conversational system tasked with determining whether the user's input requires a retrieval process. You are only supposed to trigger the RAG pipeline if the user's query requires external information or context-specific knowledge beyond the current conversation and is a financial query. If it is not financial, you should set it to false. You can send it forward to the RAG pipeline if the query requires internet-based information. Your responsibilities are as follows:
Using the provided conversation history and the user's latest query:
0. Rewrite the query to include relevant context from the image and previous conversation into the refined query. Don't add any new question or expand the question but only refine the existing one with some relevant context.
1. Maintain the conversational context while analyzing the user's intent.
2. Decide if the query requires information retrieval, particularly if it seeks factual, external, or context-specific knowledge that extends beyond the current discussion.
3. If retrieval is required, frame a refined version of the query that incorporates relevant conversational context and the user's intent accurately.
4. If retrieval is not required, preserve the user's message as-is without modification.

Respond strictly in the following format:
- `{{"trigger_rag_pipeline": true, "refined_question": "<refined_query>"}}`
  if retrieval is required, replacing `<refined_query>` with the refined version of the query.
- `{{"trigger_rag_pipeline": false, "refined_question": "<user_message>"}}`
  if retrieval is not required, replacing `<user_message>` with the original user message.
"""

#With last k messages in state
def combine_conversation_history(state: state.OverallState):
    num_messages = len(state["messages"])
    if num_messages == 0:
        log_message("No conversation history available.")
        conversation_history = "No prior conversation history available."
    else:
        log_message(
            f"Using the last {min(config.NUM_PREV_MESSAGES, num_messages)} messages for context.",
        )
        conversation_history = "\n".join(
            f"{msg.role}: {msg.content}"
            for msg in state["messages"][-config.NUM_PREV_MESSAGES :]
        )

    new_query = state["question"]
    new_message = HumanMessage(role="User", content=new_query)
    log_message(f"User: {new_query}")
    log_message("-----PROCESSING NEW QUERY BASED ON MESSAGE HISTORY-----")
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
                            "text": f"Conversation History: {conversation_history} \nImage being shared may or may not be relevant to the question.",
                        },
                        {"type": "image_url", "image_url": {"url": f"{image_url}"}},
                        {"type": "text", "text": f"Question: {new_query}"},
                    ]
                ),
            ]
        )
        query_decider = decision_prompt | llm.with_structured_output(QueryDraftDecision)
        # Invoke the LLM for decision-making and query drafting
    else:
        decision_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", _system_prompt),
                (
                    "human",
                    f"Conversation history: {conversation_history}\nQuestion: {new_query}",
                ),
            ]
        )
        query_decider = decision_prompt | llm.with_structured_output(QueryDraftDecision)
        # Invoke the LLM for decision-making and query drafting

    decision_data: QueryDraftDecision = query_decider.invoke({})  # type: ignore
    log_message(f"Refined Question: {decision_data.refined_question}")

    log_message(f"Trigger RAG Pipeline: {decision_data.trigger_rag_pipeline}")

    ###### log_tree part
    id = str(uuid.uuid4())
    child_node = nodes.combine_conversation_history.__name__ + "//" + id
    parent_node = state.get("prev_node" , "START")
    log_tree = {}

    if not LOGGING_SETTINGS['combine_conversation_history']:
        child_node = parent_node  
    
    log_tree[parent_node] = [child_node]

    ######
    
    if decision_data.trigger_rag_pipeline:
        log_message("RAG pipeline will be triggered.")

    ##### Server Logging part

        output_state = {
                "question": decision_data.refined_question,
                "messages": [new_message],
                "final_answer": "none",
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
    
    
    else:
        log_message("RAG pipeline will NOT be triggered. Generating direct answer.")

        new_question = f"""
        Given the conversation history and the refined query, directly answer the user's query.
        Conversation history: \n\n {conversation_history} \n\n User: {new_query}
        """

        ##### Server Logging part

        output_state = {
                "question": decision_data.refined_question,
                "messages": [new_message],
                "final_answer": "none",
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

#With Indexing to the Cache Server
def combine_conversation_history_v2(state: state.OverallState, vector_store):
    # Retrieve relevant context from vector DB
    log_message("Retrieving relevant conversational history from vector DB.")
    query = state["question"]
    retrieved_contexts = cache_retreiver.similarity_search(
        query,
        config.NUM_PREV_MESSAGES,
        metadata_filter= nodes.convert_metadata_to_jmespath(["conversational_awareness"],["type"])
    )

    # Format the retrieved context for use in the decision-making process
    conversation_history = "\n".join(
        f"{context['role']}: {context['content']}" for context in retrieved_contexts
    )

    new_query = state["question"]
    new_message = HumanMessage(role="User", content=new_query)
    log_message(f"User: {new_query}")
    log_message("-----PROCESSING NEW QUERY BASED ON RETRIEVED CONTEXT-----")
    image_url = state.get("image_url", "")
    if image_url != "":
        image_url = f"data:image/jpeg;base64,{image_url}"
        decision_prompt = ChatPromptTemplate.from_messages(
            messages=[
                SystemMessage(content=_system_prompt),
                HumanMessage(
                    content=[{
                            "type": "text",
                            "text": f"Conversation History: {conversation_history} \nImage being shared may or may not be relevant to the question.",
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
                    f"Conversation history: {conversation_history}\nQuestion: {new_query}",
                ),
            ]
        )

    query_decider = decision_prompt | llm.with_structured_output(QueryDraftDecision)
    decision_data: QueryDraftDecision = query_decider.invoke({})  # type: ignore
    log_message(f"Refined Question: {decision_data.refined_question}")
    log_message(f"Trigger RAG Pipeline: {decision_data.trigger_rag_pipeline}")

    ###### log_tree part
    id = str(uuid.uuid4())
    child_node = nodes.combine_conversation_history_v2.__name__ + "//" + id
    parent_node = state.get("prev_node" , "START")
    log_tree = {}

    if not LOGGING_SETTINGS['combine_conversation_history_v2']: # TODO : Add in config ( True )
        child_node = parent_node  
    
    log_tree[parent_node] = [child_node]

    ######

    if decision_data.trigger_rag_pipeline:
        log_message("RAG pipeline will be triggered.")

    ##### Server Logging part

        output_state = {
                "question": decision_data.refined_question,
                "messages": [new_message],
                "final_answer": "none",
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
    
    
    else:
        log_message("RAG pipeline will NOT be triggered. Generating direct answer.")

        new_question = f"""
        Given the conversation history and the refined query, directly answer the user's query.
        Conversation history: \n\n {conversation_history} \n\n User: {new_query}
        """


        output_state = {
                "question": new_question,
                "messages": [new_message],
                "final_answer": "Generate from context",
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
