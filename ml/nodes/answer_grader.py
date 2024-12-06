from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

import state , nodes
from llm import llm
from utils import log_message
import uuid

from utils import send_logs 
from config import LOGGING_SETTINGS

class AnswerGrader(BaseModel):
    """Grader assesses whether an answer addresses a question with a binary score and reasoning."""

    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )
    reason: str = Field(
        description="Reason why the answer does not address the question (only applicable if binary_score is 'no')"
    )


_system_prompt = """You are a grader assessing whether an answer addresses/resolves a question. 
For each question-answer pair:
1. Give a binary score: 'yes' or 'no'. 
   - 'yes' means the answer resolves the question.
   - 'no' means the answer does not resolve the question.
2. If the binary score is 'no', explain the reason in brief try to infer what parts of the question were not resolved by the generated answer.
3. If the question does not specify numbers of something (like reasons or inferences) then don't say 'no' just because the answer contains less reasons. 

"""

answer_grader_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
    ]
)

answer_grader = answer_grader_prompt | llm.with_structured_output(AnswerGrader)


def grade_answer(state: state.InternalRAGState):
    """
    Determines whether the generated answer satisfies the query or not.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates answer with a hallucination flag if query is unanswered
                      and includes the reason for insufficiency if applicable.
    """
    question_group_id = state.get("question_group_id", 1)
    log_message(
        "------CHECKING IF ANSWER SATISFIES QUERY------",
        f"question_group{question_group_id}",
    )
    question = state["original_question"]
    answer = state["answer"]

    # Score the answer
    score = answer_grader.invoke({"question": question, "generation": answer})
    answer_sufficiency_flag = score.binary_score  # type: ignore
    reason = score.reason if answer_sufficiency_flag == "no" else None

    if answer_sufficiency_flag == "no":
        log_message(
            "------ANSWER IS INSUFFICIENT------", f"question_group{question_group_id}"
        )
        is_answer_sufficient = False
        insufficiency_reason = reason
    else:
        log_message(
            "------ANSWER IS SUFFICIENT------", f"question_group{question_group_id}"
        )
        is_answer_sufficient = True
        insufficiency_reason = None

    answer_generation_retries = state.get("answer_generation_retries", 0)
    # state["answer_generation_retries"] += 1
    # state["prev_node"] = "grade_answer"

    ###### log_tree part
    id = str(uuid.uuid4())
    child_node = nodes.grade_answer.__name__ + "//" + id
    prev_node_rewrite = child_node
    parent_node = state.get("prev_node" , "START")
    log_tree = {}

    if not LOGGING_SETTINGS['grade_answer'] or state.get("send_log_tree_logs" , "") == "False":
        child_node = parent_node  
        
    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "answer_generation_retries": answer_generation_retries + 1 ,
        "insufficiency_reason" : insufficiency_reason,
        "is_answer_sufficient" : is_answer_sufficient,
        "prev_node_rewrite" : prev_node_rewrite ,
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


class WebAnswerGrader(BaseModel):
    """Grader assesses whether an answer addresses a question with a binary score and reasoning."""

    rag_score: str = Field(
        description="Score given to rag answer '1' or '0' "
    )
    web_score: str = Field(
        description="Score given to web answer '1' or '0' "
    )

    reason: str = Field(
        description="Reason for the score given to rag answer and web answer"
    )


web_answer_grader_prompt = ChatPromptTemplate.from_template(
    """You are a grader assessing whether an answer resolves a question.

For each question-answer pair:
1. Give a binary score for both answers: '1' for the answer that resolves the question better, and '0' for the other answer.
   - '1' means the answer resolves the question more effectively.
   - '0' means the answer is less relevant or doesn't resolve the question as well.
2. Provide a brief explanation for your scoring.
3. If one answer is clearly better than the other, give it a score of '1', and the other a score of '0'.
4. If both answers are equally relevant or inadequate, give them both a score of '1' if both answers are perfectly resolving the question.
5. The answer that addresses the most important aspects of the question (e.g., mentions specific details, facts, or directly answers the question) should get a score of '1' and the other should get '0'.

### Instructions:
- Question: {question}
- RAG Answer: {rag_answer}
- Web Answer: {web_answer}

Provide a binary score (0 or 1) for each answer. The answer with the higher score is considered more relevant to the question.
"""
)


web_answer_grader = web_answer_grader_prompt | llm.with_structured_output(WebAnswerGrader)


def grade_web_answer(state: state.InternalRAGState):
    """
    Determines which generated answer satisfies the query or not.
    Compares both the RAG and web-generated answers and assigns a binary score to each answer.

    Args:
        state (dict): The current graph state.

    Returns:
        dict: Updates the state with the selected answer (the one with score '1').
    """
    question_group_id = state.get("question_group_id", 1)
    log_message(
        "------COMPARING RAG ANSWER WITH WEB ANSWER------",
        f"question_group{question_group_id}",
    )

    question = state["original_question"]
    rag_answer = state.get("doc_generated_answer", "")
    web_answer = state.get("web_generated_answer", "")

    # id = str(uuid.uuid4())
    # child_node = nodes.grade_web_answer.__name__ + "//" + id
    # parent_node = state.get("prev_node" , "START")
    # log_tree = {}
    # log_tree[parent_node] = [child_node]

    if rag_answer == "":

        id = str(uuid.uuid4())
        child_node = nodes.grade_web_answer.__name__ + "//" + id
        parent_node = state.get("prev_node" , "START")
        log_tree = {}

        if not LOGGING_SETTINGS['grade_web_answer']:
            child_node = parent_node 

        log_tree[parent_node] = [child_node]

        log_message(
            "------NO RAG ANSWER FOUND : RETURNING WEB GENERATED ANSWER------",
            f"question_group{question_group_id}",
        )

        

        output_state = {
            "answer" : web_answer,
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
        return output_state


    res = web_answer_grader.invoke({"question" : question  , "rag_answer" : rag_answer , "web_answer": web_answer} )

    try:
        rag_score = res.rag_score 
        web_score = res.web_score 

        log_message(
            f"RAG Answer Score: {rag_score}, Web Answer Score: {web_score}",
            f"question_group{question_group_id}",
        )

        # Select the answer with the higher score
        if rag_score == "1":
            answer = rag_answer
        else:
            answer = web_answer

    except Exception as e:
        log_message(f"Error grading answers: {str(e)}", f"question_group{question_group_id}")
        answer = state.get("answer" , "")

    ###### log_tree part
    id = str(uuid.uuid4())
    child_node = nodes.grade_web_answer.__name__ + "//" + id
    parent_node = state.get("prev_node" , "START")
    log_tree = {}

    if not LOGGING_SETTINGS['grade_web_answer'] or state.get("send_log_tree_logs" , "") == "False":
        child_node = parent_node  

    log_tree[parent_node] = [child_node]
    ######
    
    ##### Server Logging part

    

    output_state = {
        "answer" : answer,
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
