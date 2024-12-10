# -------------------------------
# General LLM Response Generation
# -------------------------------
# This module handles the generation of responses from a language model (LLM) based on user queries. It uses a 
# prompt template designed to work with the system's settings and the user query to produce contextually relevant 
# answers. The module also integrates logging for tracking the LLM's response generation process and output.
#
# Key Components:
# 1. **LLM_Response**: A Pydantic model for structuring the LLM's response.
# 2. **general_llm**: The main function that interacts with the language model to generate responses based on user 
#    queries and the current mode of operation.
# 3. **Prompt Template**: A `ChatPromptTemplate` is used to format the system and user inputs before passing them to 
#    the model, including details like the current mode and an optional image description.
#
# Logging:
# The module includes logging functionality to record each step of the response generation, including the query, 
# mode, and the final output. Logs are sent to a centralized server for monitoring purposes.
#
# Functions:
# - general_llm: Accepts the current state, generates the query, processes the response from the LLM, and logs the 
#   result.
#
# Future Improvements:
# - Refine how the model handles bad or unclear queries, which currently might not be well understood by the model.
# -------------------------------

from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

import state
from llm import llm
from utils import log_message, send_logs
from config import LOGGING_SETTINGS
import uuid
from prompt import prompts

class LLM_Response(BaseModel):
    answer: Optional[str] = Field(default=None, description="Just LLM response")


# TODO: put modes in config
## TODO: the model does not understand very well when i ask bad questions to it.
_general_llm_system_prompt = prompts._general_llm_system_prompt

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _general_llm_system_prompt),
        ("human", "Current Mode:{run_mode} \nUser query: {image_desc} {query}"),
    ]
)

llm_response = prompt | llm.with_structured_output(LLM_Response)


def general_llm(state: state.OverallState):
    log_message("---LLM ANSWERING FROM KNOWLEDGE---")
    query = state["question"]
    mode = f"{state.get('fast_vs_slow','slow')} + {state.get('normal_vs_research','research')}"

    llm_output = llm_response.invoke(
        {"query": query, "run_mode": mode, "image_desc": state["image_desc"]}
    )

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = "general_llm" + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}
    # tree_log(f"send_Log_tree_logs : {state['send_log_tree_logs']}",1)
    if (
        not LOGGING_SETTINGS["general_llm"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part
    output_state = {
        "final_answer": llm_output.answer,
        "answer": llm_output.answer,
        "messages": [AIMessage(role="Chatbot", content=llm_output.answer)],
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

    return {
        "final_answer": llm_output.answer,
        "answer": llm_output.answer,
        "messages": [AIMessage(role="Chatbot", content=llm_output.answer)],
    }
