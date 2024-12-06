from langchain_core.prompts import ChatPromptTemplate
from utils import log_message

import state
from llm import llm
from utils import send_logs

# System prompt for LLM to refine the final query, using the original query, clarifying questions, and responses
_system_prompt_for_final_query = """You are a query refiner who takes an initial query, clarifying questions, and user responses to create a final, well-structured query.\n
    Use the original question, the clarifying questions, and the user's answers to form a clear and comprehensive query ready for retrieval."""
final_query_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_final_query),
        (
            "human",
            "Original query: {original_query}\nClarifying questions and responses: {clarifications}",
        ),
    ]
)
final_query_generator = final_query_prompt | llm


def refine_query(state: state.OverallState):
    # Fetch clarifying questions and responses from the state
    clarifying_questions = state["clarifying_questions"]
    query = state["question"]
    clarifications = state.get("clarifications", [])

    # Process clarifying questions and responses into a structured format
    combined_clarifications = " | ".join(
        f"Q: {q['question']}   A: {a}"
        for q, a in zip(clarifying_questions, clarifications)
    )
    # Generate the final refined query using the original query and the combined clarifications
    final_query = final_query_generator.invoke(
        {"original_query": query, "clarifications": combined_clarifications}
    )
    
    log_message("----FINAL REFINED QUERY FOR RETRIEVAL---")
    log_message("----" + final_query.content)

    ###### log_tree part
    import uuid , nodes 
    id = str(uuid.uuid4())
    child_node = nodes.refine_query.__name__ + "//" + id
    parent_node = state.get("prev_node" , "START")
    log_tree = {}
    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "question": final_query.content,
        "prev_node" : child_node,
        "log_tree" : log_tree ,
    }
    send_logs(
        parent_node , 
        child_node , 
        input_state=state , 
        output_state=output_state , 
        text=child_node.split("//")[0] ,
    )
    
    ######
    return output_state