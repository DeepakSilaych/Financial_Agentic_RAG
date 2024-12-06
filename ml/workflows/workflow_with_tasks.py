from langgraph.graph import END, StateGraph, START
import uuid
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage

import state, nodes, edges
from utils import log_message
from nodes.question_decomposer import question_combiner
from .rag_e2e import rag_e2e
from .task_handler import task_handler


def _rag_subgraph(state: state.InternalRAGState):
    prev_question = None
    prev_answer = None
    question_group_id = str(uuid.uuid4())
    for question in state["question_group"]:
        # question_group_id=state.get("question_group_id", 1)
        if prev_answer:
            question = question_combiner.invoke(
                {
                    "image_url": state.get("image_url", ""),
                    "next_question": question,
                    "prev_question": prev_question,
                    "prev_answer": prev_answer,
                }
            ).combined_question
            log_message(
                f"Combined question:  {question}", f"question_group{question_group_id}"
            )

        prev_question = question
        prev_answer = rag_e2e.invoke(
            {"question": question, "question_group_id": question_group_id}
        )["answer"]

    return {
        "decomposed_questions": [prev_question],
        "decomposed_answers": [prev_answer],
    }


def _standalone_rag_subgraph(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    answer = rag_e2e.invoke(
        {"question": state["question"], "question_group_id": question_group_id}[
            "answer"
        ]
    )

    return {
        "final_answer": answer,
        "messages": [AIMessage(role="Chatbot", content=answer)],
        "clarifying_questions": [],
    }
    
    
path_for_web = StateGraph(state.InternalRAGState)
path_for_web.add_node(nodes.generate_web_answer.__name__, nodes.generate_web_answer)
path_for_web.add_node(nodes.search_web.__name__, nodes.search_web)

path_for_web.add_edge(START, nodes.search_web.__name__)
path_for_web.add_edge(nodes.search_web.__name__, nodes.generate_web_answer.__name__)
path_for_web.add_edge(nodes.generate_web_answer.__name__, END)

path_for_web_ = path_for_web.compile(
    interrupt_after=[nodes.search_web.__name__]
)
    
def _web_subgraph(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    answer = path_for_web_.invoke(
        {"question": state["question"], "original_question": state["question"]})["answer"]
    
    return {
        "final_answer": answer,
        "messages": [AIMessage(role="Chatbot", content=answer)],
        "clarifying_questions": [],
    }

def dummy_KPI(state):
    log_message("--- Entered Analysis ---")
    return {}

def dummy_persona(state):
    log_message("--- Entered Persona ---")
    return {}

def _task_subgraph(state: state.OverallState):
    print(state["task"])
    code = task_handler.invoke(
        {"task": state["task"], "question": state["question_in_query"]}
    )["code"]
    
    return {
        "code": code
    }

def rag_done(state):
    print("RAG Done")
    return {}

#fmt off
# Main Path
graph = StateGraph(state.OverallState)
graph.add_node(nodes.check_safety.__name__, nodes.check_safety)
graph.add_node(nodes.path_decider.__name__, nodes.path_decider)
graph.add_node(nodes.process_query.__name__, nodes.process_query)
graph.add_node(nodes.decompose_question_v2.__name__, nodes.decompose_question_v2)
graph.add_node(nodes.ask_clarifying_questions.__name__,nodes.ask_clarifying_questions)
graph.add_node(nodes.refine_query.__name__,nodes.refine_query)
graph.add_node("rag", _rag_subgraph)
graph.add_node("standalone_rag", _standalone_rag_subgraph)
# graph.add_node("naive_rag", _naive_rag_subgraph)
graph.add_node("web_path", _web_subgraph)
graph.add_node(nodes.combine_answer_v1.__name__, nodes.combine_answer_v1)
graph.add_node(nodes.general_llm.__name__,nodes.general_llm)
graph.add_node("KPI_analyst", dummy_KPI)
graph.add_node("persona", dummy_persona)
graph.add_node(nodes.make_task_question.__name__, nodes.make_task_question)
graph.add_node("task_subgraph", nodes.do_task)
graph.add_node(nodes.combine_task_question.__name__, nodes.combine_task_question)
graph.add_node(rag_done.__name__, rag_done)

graph.add_edge(START, nodes.check_safety.__name__)
graph.add_conditional_edges(
    nodes.check_safety.__name__,
    edges.query_modified_or_not,
    {
        nodes.process_query.__name__: nodes.process_query.__name__,
        END:END
    }
)
graph.add_conditional_edges(
    nodes.process_query.__name__,
    edges.route_initial_query,
    {
        nodes.general_llm.__name__: nodes.general_llm.__name__,
        nodes.make_task_question.__name__: nodes.make_task_question.__name__,
    }
)
graph.add_conditional_edges(
    nodes.make_task_question.__name__,
    edges.task_question_router,
    {
        nodes.path_decider.__name__: nodes.path_decider.__name__,
        "task_subgraph":"task_subgraph",
    }
)
graph.add_conditional_edges(
    nodes.path_decider.__name__,
    edges.path_decided,
    {
        nodes.ask_clarifying_questions.__name__:nodes.ask_clarifying_questions.__name__,
        "rag":"standalone_rag",
        "web_path":"web_path",
        nodes.general_llm.__name__:nodes.general_llm.__name__,
    }
)
graph.add_conditional_edges(
        nodes.ask_clarifying_questions.__name__,
        edges.refine_query_or_not,
        {
            nodes.decompose_question_v2.__name__: nodes.decompose_question_v2.__name__,
            nodes.refine_query.__name__: nodes.refine_query.__name__
        }
)
graph.add_conditional_edges(
    nodes.refine_query.__name__,
    edges.naive_or_complex,
    {
        "analysis": "KPI_analyst",
        "persona": "persona",
        # "naive_rag": "naive_rag",
        "rag": "standalone_rag",
        nodes.decompose_question_v2.__name__:nodes.decompose_question_v2.__name__,
    }
)
graph.add_conditional_edges(nodes.decompose_question_v2.__name__, edges.send_decomposed_question_groups, ["rag"]) # type: ignore
graph.add_edge("rag", nodes.combine_answer_v1.__name__)
graph.add_edge("standalone_rag", rag_done.__name__)
# graph.add_edge("naive_rag", END)
graph.add_edge(nodes.general_llm.__name__,rag_done.__name__)
graph.add_edge("web_path", rag_done.__name__)
graph.add_edge(nodes.combine_answer_v1.__name__, rag_done.__name__)
graph.add_edge("KPI_analyst", rag_done.__name__)
graph.add_edge("persona", rag_done.__name__)

graph.add_edge("task_subgraph", nodes.combine_task_question.__name__)
graph.add_edge(rag_done.__name__, nodes.combine_task_question.__name__)

graph.add_edge(nodes.combine_task_question.__name__, END)

# fmt: on

# Set up memory

memory = MemorySaver()
workflow_with_tasks = graph.compile(
    checkpointer=memory, interrupt_before=[nodes.refine_query.__name__,]
)
