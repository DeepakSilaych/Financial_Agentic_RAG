# This module refines the original user query by incorporating clarifying questions and their responses.
# The process enhances the specificity and clarity of the query for improved document retrieval.

# 1. Refine Class: Defines the structure for the refined query output.
# 2. Final Query Refinement: Combines the original query with clarifications to generate a more focused query.
# 3. Logging: Records the refined query and associated logs to ensure traceability.
# 4. Server Communication: Sends logs about the final query and clarifications for future reference.

from langchain_core.prompts import ChatPromptTemplate
from utils import log_message
from pydantic import BaseModel, Field
import state
from llm import llm
from utils import send_logs
from prompt import prompts
# System prompt for LLM to refine the final query, using the original query, clarifying questions, and responses
_system_prompt_for_final_query = prompts._system_prompt_for_final_query
final_query_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_final_query),
        (
            "human",
            "Original query: {original_query}\nClarifying questions and responses: {clarifications}",
        ),
    ]
)


class Refine(BaseModel):
    content: str = Field(description="Refined query")


final_query_generator = final_query_prompt | llm.with_structured_output(Refine)


def refine_query(state: state.OverallState):
    # Fetch clarifying questions and responses from the state
    clarifying_questions = state["clarifying_questions"]
    query = state["question"]
    clarifications = state["clarifications"]
    # Process clarifying questions and responses into a structured format
    combined_clarifications = " | ".join(
        f"Q: {q['question']} options: {q['options']}  A: {a}"
        for q, a in zip(clarifying_questions, clarifications)
    )
    # Generate the final refined query using the original query and the combined clarifications
    final_query = final_query_generator.invoke(
        {"original_query": query, "clarifications": combined_clarifications}
    )

    log_message("----FINAL REFINED QUERY FOR RETRIEVAL---")
    log_message("----" + final_query.content)

    ###### log_tree part
    import uuid, nodes

    id = str(uuid.uuid4())
    child_node = nodes.refine_query.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}
    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    if clarifications[-1].strip()=="ignore":
        clar_out = {
            "question": None,
            "question_type": "none",
            "options": None,
        }
        output_state = {"clarifying_questions":clar_out,
        "prev_node" : child_node,
        "log_tree" : log_tree}
        send_logs(
            parent_node , 
            child_node , 
            input_state=state , 
            output_state=output_state , 
            text=child_node.split("//")[0] ,
        )
        return output_state
    
    output_state = {
        "question": final_query.content,
        "prev_node": child_node,
        "log_tree": log_tree,
    }
    send_logs(
        parent_node,
        child_node,
        input_state=state,
        output_state=output_state,
        text=child_node.split("//")[0],
    )

    ######
    return output_state
