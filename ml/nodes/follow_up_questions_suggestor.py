from typing import List, Optional

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

import state
from llm import llm
from utils import log_message


class FollowUpQuestion(BaseModel):
    """Suggests intelligent follow-up questions based on the original query, previous conversation history, decomposed answers, and final answer."""

    follow_up_questions: Optional[List[str]] = Field(
        default=None,
        description="Follow-up questions the user might want to ask based on the final answer for deeper exploration.",
    )


# System prompt for generating follow-up questions
_system_prompt_for_follow_up = """You are a query refinement assistant. Given an initial query, a set of decomposed answers, and a final answer, identify any areas for deeper clarification or further inquiry.\n
If no follow-up is necessary, respond with no follow-up questions. Otherwise, suggest intelligent follow-up questions to enhance user understanding or to dive deeper into the topic."""
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
    log_message("---GENERATING FOLLOW-UP QUESTIONS BASED ON FINAL ANSWER AND HISTORY---")
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

    return {"follow_up_questions": followup_output.follow_up_questions}
