# -------------------------------
# Follow-Up Question Generation
# -------------------------------
# This module provides functionality to generate follow-up questions based on:
# 1. The original query provided by the user.
# 2. The previous conversation history.
# 3. Decomposed answers from the conversation.
# 4. The final answer provided by the system.
#
# The follow-up questions are intended to help the user explore the topic further.
# The generation is based on a system prompt template and interaction with a language model (llm).
# The model suggests relevant follow-up questions that can be asked to enhance the depth of the conversation.
#
# Functions:
# - ask_follow_up_questions: This function combines the inputs (query, messages, decomposed answers, final answer)
#   and invokes the language model to generate potential follow-up questions. It logs the process and returns the output.
# -------------------------------


from typing import List, Optional

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from prompt import prompts
import state
from llm import llm
from utils import log_message, send_logs
from config import LOGGING_SETTINGS
import uuid


class FollowUpQuestion(BaseModel):
    """Suggests intelligent follow-up questions based on the original query, previous conversation history, decomposed answers, and final answer."""

    follow_up_questions: Optional[List[str]] = Field(
        default=None,
        description="Follow-up questions the user might want to ask based on the final answer for deeper exploration.",
    )


# System prompt for generating follow-up questions
_system_prompt_for_follow_up = prompts._system_prompt_for_follow_up
follow_up_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_follow_up),
        (
            "human",
            "Original query: {query}\nPrevious messages history: {messages}\nDecomposed answers: {decomposed_answers}\nFinal answer: {final_answer}",
        ),
    ]
)
follow_up_question_generator = follow_up_prompt | llm.with_structured_output(
    FollowUpQuestion
)


def ask_follow_up_questions(state: state.OverallState):
    """
    A Human-in-the-Loop function that:
    1. Combines the original query, previous messages, decomposed answers, and final answer.
    2. Generates follow-up questions based on these inputs.
    3. Interacts with the user by suggesting potential follow-up questions for further exploration.
    """
    log_message(
        "---GENERATING FOLLOW-UP QUESTIONS BASED ON FINAL ANSWER AND HISTORY---"
    )
    query = state.get("question", "")
    messages = state.get("messages", [])
    decomposed_answers = state.get("decomposed_answers", [])
    final_answer = state.get("final_answer", "")

    followup_output = follow_up_question_generator.invoke(
        {
            "query": query,
            "messages": messages,
            "decomposed_answers": decomposed_answers,
            "final_answer": final_answer,
        }
    )

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = "ask_follow_up_questions" + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}
    # tree_log(f"send_Log_tree_logs : {state['send_log_tree_logs']}",1)
    if (
        not LOGGING_SETTINGS["ask_follow_up_questions"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part
    output_state = {
        "follow_up_questions": followup_output.follow_up_questions,
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

    return {"follow_up_questions": followup_output.follow_up_questions}
