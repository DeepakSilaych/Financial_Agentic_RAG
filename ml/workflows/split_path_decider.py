from langgraph.graph import END, StateGraph, START
import uuid
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage

import state, nodes, edges
from utils import log_message
from nodes.question_decomposer import question_combiner
from .rag_e2e import rag_e2e

from workflows.persona import persona_workflow
from workflows.final_workflow_with_path_decider import _rag_subgraph,_web_subgraph, dummy_persona, dummy_KPI

graph = StateGraph(state.OverallState)
graph.add_node(nodes.check_safety.__name__, nodes.check_safety)
graph.add_node(nodes.process_query.__name__, nodes.process_query)
graph.add_node(nodes.split_path_decider_1.__name__, nodes.split_path_decider_1)
graph.add_node(nodes.split_path_decider_2.__name__, nodes.split_path_decider_2)
graph.add_node(nodes.ask_clarifying_questions.__name__, nodes.ask_clarifying_questions)
graph.add_node("standalone_rag",_rag_subgraph)
graph.add_node("web_path", _web_subgraph)
graph.add_node("rag",_rag_subgraph)
graph.add_node(nodes.refine_query.__name__, nodes.refine_query)
graph.add_node(nodes.decompose_question_v2.__name__, nodes.decompose_question_v2)   
graph.add_node(nodes.combine_answers.__name__, nodes.combine_answers)
graph.add_node(nodes.general_llm.__name__,nodes.general_llm)
graph.add_node("KPI_analyst", dummy_KPI)
graph.add_node("persona_rag", persona_workflow)

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
        nodes.split_path_decider_1.__name__: nodes.split_path_decider_1.__name__
    }
)
graph.add_conditional_edges(
    nodes.split_path_decider_1.__name__,
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
            "decompose": nodes.decompose_question_v2.__name__,
            nodes.refine_query.__name__: nodes.refine_query.__name__
        }
)
graph.add_edge(nodes.refine_query.__name__, nodes.split_path_decider_2.__name__)
graph.add_conditional_edges(
    nodes.split_path_decider_2.__name__,
    edges.path_decided_post_clarification,
    {
        "analysis": "KPI_analyst",
        "persona": "persona_rag",
        # "naive_rag": "naive_rag",
        "rag": "standalone_rag",
        nodes.decompose_question_v2.__name__:nodes.decompose_question_v2.__name__,
    }
)

graph.add_conditional_edges(nodes.decompose_question_v2.__name__, edges.send_decomposed_question_groups, ["rag"]) # type: ignore
graph.add_edge("rag", nodes.combine_answers.__name__)
graph.add_edge("standalone_rag", END)
# graph.add_edge("naive_rag", END)
graph.add_edge(nodes.general_llm.__name__,END)
graph.add_edge("web_path", END)
graph.add_edge(nodes.combine_answers.__name__, END)
graph.add_edge("KPI_analyst", END)
graph.add_edge("persona_rag", END)
# fmt: on

# Set up memory
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
split_path_decider = graph.compile(
    checkpointer=memory, interrupt_before=[nodes.refine_query.__name__,]
)
