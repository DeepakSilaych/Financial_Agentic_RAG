from concurrent.futures import ThreadPoolExecutor

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils import log_message
from pydantic import BaseModel, Field

import state, nodes
from llm import llm


class Hyde_doc(BaseModel):
    """Generate Hypothetical Answer to the query"""

    Hyde_ans: str = Field(description="Generate a Hypothetical answer.")


# System prompt for the question rewriter
_system_prompt = """You are a question re-writer that converts an input question to a better version that is optimized for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""
re_write_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        (
            "human",
            "Here is the initial question: \n\n {question} \n Formulate an improved question.",
        ),
    ]
)
question_rewriter = re_write_prompt | llm | StrOutputParser()

_system_prompt_answergrader = """You are a question re-writer that converts an input question to a better version that is optimized for vectorstore retrieval.The input contains the intial query by the user and a generated answer.
The generated answer was not able to completely resolve the query. Look at the input and try to reason about the underlying semantic intent / meaning. 
Try to understand why the answer was not able to resolve the query and rewrite the query."""
re_write_prompt_answergrader = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_answergrader),
        (
            "human",
            "Here is the initial question: \n\n {question}. \n\n Here is the generated answer: \n\n{answer}. Here is the reason for insufficiency: \n\n {reason}. \n Formulate an improved question.",
        ),
    ]
)
question_rewriter2 = re_write_prompt_answergrader | llm | StrOutputParser()

_system_prompt_gradedocs = """You are a question re-writer that converts an input question to a better version that is optimized for vectorstore retrieval. The input contains the intial query by the user and the reason why all the retrieved documents were irrelevant to the query and what was missing the documents. 
Look at the input and try to reason about the underlying semantic intent / meaning. 
Try to understand why the documents were irrelevant to the query and rewrite the query emphasing more on the part that was missing in the documents."""
re_write_prompt_gradedocs = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_gradedocs),
        (
            "human",
            "Here is the initial question: \n\n {question}. \n\n Here is the reason for the documents to be graded irrelevant: {reason}. \n\n Formulate an improved question.",
        ),
    ]
)

question_rewriter3 = re_write_prompt_gradedocs | llm | StrOutputParser()


### Not using rewrite_question


def rewrite_question(state: state.InternalRAGState):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """
    question_group_id = state["question_group_id"]

    log_message("---TRANSFORM QUERY---", f"question_group{question_group_id}")
    question = state["original_question"]
    documents = state["documents"]
    loop_step = state.get("loop_step", 0)
    prev_node = state.get("prev_node", "")
    answer = state.get("answer", "")
    insufficiency_reason = state.get("insufficiency_reason", "")

    # Re-write question
    if prev_node == "grade_answer":
        better_question = question_rewriter2.invoke(
            {"question": question, "answer": answer, "reason": insufficiency_reason}
        )
    else:
        better_question = question_rewriter.invoke({"question": question})

    return {
        "documents": documents,
        "question": better_question,
        "loop_step": loop_step + 1,
        "prev_node": "rewrite_question",
    }


# System prompt for the HyDE-based rewriter
_hyde_system_prompt = """You are an assistant that generates a hypothetical answer based on the provided question. This hypothetical answer should not be too long and should help clarify the semantic intent and underlying meaning of the question, allowing for a more optimized query formulation. Generate a concise hypothetical answer and then rephrase the question to better match this document."""
hyde_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _hyde_system_prompt),
        (
            "human",
            "Here is the initial question: \n\n {question} \n Generate a hypothetical answer and then improve the question based on it ( Make sure to not change the semantics of what the question is asking ).",
        ),
    ]
)
hyde_rewriter = hyde_prompt | llm.with_structured_output(Hyde_doc)


def rewrite_with_hyde(state: state.InternalRAGState):
    """
    Rewrites the query using a hypothetical document (HyDE).

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question based on HyDE
    """
    question_group_id = state.get("question_group_id", 1)

    log_message(
        "------TRANSFORMING QUERY USING HyDE AND REWRITING------",
        f"question_group{question_group_id}",
    )
    question = state["original_question"]
    # documents = state["documents"]
    answer = state.get("answer", "")
    insufficiency_reason = state.get("insufficiency_reason", "")
    prev_node = state["prev_node"]
    irrelevancy_reason = state.get("irrelevancy_reason", "")

    metadata_retries = state["metadata_retries"]
    if (
        len(state["documents"]) + len(state.get("documents_with_kv", [])) == 0
        and (prev_node == nodes.retrieve_documents_with_metadata.__name__
             or 
             prev_node == nodes.retrieve_documents_with_quant_qual.__name__
        )
    ):
        metadata_retries += 1

    # Generate hypothetical document and re-write question based on it
    # better_question = hyde_rewriter.invoke({"question": question})
    def get_hyde_question() -> str:
        return hyde_rewriter.invoke({"question": question}).Hyde_ans

    def get_rewritten_question() -> str:
        if prev_node == nodes.grade_answer.__name__:
            return question_rewriter2.invoke(
                {"question": question, "answer": answer, "reason": insufficiency_reason}
            )
        elif prev_node == nodes.grade_documents.__name__:
            return question_rewriter3.invoke(
                {"question": question, "reason": irrelevancy_reason}
            )
        else:
            return question_rewriter.invoke({"question": question})

    with ThreadPoolExecutor() as executor:
        hyde_question_future = executor.submit(get_hyde_question)
        rewritten_question_future = executor.submit(get_rewritten_question)

        hyde_better_question = hyde_question_future.result()
        rewriting_question = rewritten_question_future.result()

    better_question = hyde_better_question + "xxxxxxxxxx" + rewriting_question

    # ##### log_tree part
    # curr_node = nodes.rewrite_with_hyde.__name__
    # prev_node = state.get("prev_node" , "START")
    # state["question"] = better_question
    # state["metadata_retries"] = metadata_retries
    # state["rewritten_question"] = rewriting_question
    # state["log_tree"][prev_node] = [{"node" : curr_node , "state" : state}]
    # state["prev_node"] = curr_node
    # #####

    return {
        "question": better_question,
        "metadata_retries": metadata_retries,
        "prev_node": nodes.rewrite_with_hyde.__name__,
        "rewritten_question": rewriting_question,
    }
