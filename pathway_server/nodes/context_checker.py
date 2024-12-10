"""
Context Checker Module for Conversational History Refinement

This module defines the logic for determining if prior conversational context is necessary to answer a user's query.
It integrates with a LangChain-based LLM system to analyze the user's input and decide whether prior conversation history
can provide additional context that would improve the quality or clarity of the response.

### Key Components:

1. **ContextCheckerDecision**:
   - A Pydantic model that holds the decision on whether conversational context is required. 
   - The decision is made based on the user query and previous conversation history.

2. **System Prompt**:
   - The `_system_prompt_context_checker` string provides a system-level prompt that helps the LLM decide if context from prior messages is required for the current query.

3. **Main Functionality - `check_context`**:
   - This function:
     - Analyzes the current state to decide if context from the conversation history should be included in generating a response.
     - Loads prior conversation history from a `.jsonl` file if no messages are available in the current session.
     - Constructs a prompt to check if prior conversation history is needed.
     - Uses the LangChain model to get the decision on whether the context is necessary.
     - Returns a dictionary containing the result (`context_required`) and the available conversation messages.

4. **Conversation History**:
   - The module attempts to load conversation history from a file located at `data_convo/conversation_history.jsonl`.
   - If the file exists, it loads the last recorded conversation for the current user, allowing the system to consider prior interactions.
   - The function also checks if there are no messages in the current session, and in such cases, attempts to load the conversation history for context.

5. **Logging and Decision Making**:
   - The module logs significant steps such as whether prior conversation history was used or not.
   - The decision on whether context is required is logged and returned in a structured format.

6. **Potential Use Cases**:
   - This system is particularly useful for conversational agents that need to remember past interactions or consider the history of a user’s conversation to refine responses.
   - The module can be incorporated into chat-based systems where context can enhance the relevance and accuracy of responses.

### Usage:
- This module is invoked as part of a larger conversational AI pipeline. It helps the system determine if the user's query requires additional context or if it can be answered directly based on the current input.
- The function `check_context` returns a boolean decision about whether context is required, which can then influence subsequent actions or responses in the system.

### Dependencies:
- **LangChain**: Used for interacting with the LLM for decision-making tasks.
- **Pydantic**: Used to define the structure of the context decision.
- **JSONLines**: For reading and storing conversation history.
- **Utils**: For logging and other helper functions.
- **Config**: Contains configuration settings such as the number of messages to consider for context and logging settings.

### Example Workflow:
1. The system receives a user query.
2. It checks if there are any previous messages in the current conversation.
3. If no messages are present, it attempts to load prior conversation history from a `.jsonl` file.
4. The system then constructs a prompt to decide if the current query can be answered directly or if prior context is required.
5. The result (True/False) is returned, indicating whether context is required.

### Logging:
- The module includes logging for key events such as:
  - Whether prior conversation history is loaded.
  - The decision on whether context is required for the current query.
  - Integration with logging and server systems to track decision-making in the pipeline.

"""

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
import state
import jsonlines
import nodes
from llm import llm
from utils import log_message
import uuid
import config
from utils import send_logs
from config import LOGGING_SETTINGS

class ContextCheckerDecision(BaseModel):
    """Decide if query refinement with conversational context is required."""
    context_required: bool = Field(
        description="Boolean indicating if context from the conversation history is required for the query."
    )

_system_prompt_context_checker = """
You are a system tasked with determining if the user's input requires refinement with prior conversational history.
Your responsibilities:
1. Analyze the user's input for ambiguity or missing context.
2. Decide if prior conversational history is necessary for clarifying the user's intent.
3. Return only a boolean value indicating whether context is required (true/false).
Return False if user's query can be answered directly.
"""

def check_context(state: state.OverallState):
    messages = state.get("messages", [])
    user_id=state["user_id"]
    num_messages = len(messages)
    if num_messages==0:
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

    if num_messages == 0:
        log_message("No conversational history available.")
        recent_messages = "No prior conversation history available."
    else:
        log_message(
            f"Using the last {min(config.NUM_PREV_MESSAGES, num_messages)} messages for context."
        )
        recent_messages = "\n".join(
            f"{msg.role}: {msg.content}" for msg in messages[-config.NUM_PREV_MESSAGES :]
        )

    # Construct prompt for the context-checker node
    query = state["question"]
    decision_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=_system_prompt_context_checker),
            HumanMessage(content=f"Recent Messages:\n{recent_messages}\nQuery: {query}"),
        ]
    )

    # Decision making
    decision_pipeline = decision_prompt | llm.with_structured_output(ContextCheckerDecision)
    decision_data: ContextCheckerDecision = decision_pipeline.invoke({})  # type: ignore
    log_message(f"Context Required: {decision_data.context_required}")

    # # Logging the execution tree
    # id = str(uuid.uuid4())
    # child_node = nodes.check_context.__name__ + "//" + id
    # parent_node = state.get("prev_node", "START")
    # log_tree = {}

    # if not LOGGING_SETTINGS["check_context"]:
    #     child_node = parent_node

    # log_tree[parent_node] = [child_node]

    # # Send server logs
    # send_logs(
    #     parent_node=parent_node,
    #     curr_node=child_node,
    #     child_node=None,
    #     input_state=state,
    #     output_state={"context_required": decision_data.context_required},
    #     text=child_node.split("//")[0],
    # )

    return {"context_required": decision_data.context_required, "messages":messages}
