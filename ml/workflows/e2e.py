from typing import Any
from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send

import state, nodes, edges
from config import WORKFLOW_SETTINGS

from .rag_e2e import rag_e2e
from .web_rag import web_rag
from .repeater import repeater
from .kpi import kpi_workflow
from .persona import persona_workflow


def map_fields_in_node(node, mapping: dict[str, Any]):
    def mapped_node(state):
        res = node.invoke(state)
        return {v: res.get(k, None) for k, v in mapping.items()}

    return mapped_node

def send_to_answer_analysis(state:state.OverallState):
    if len(state.get("analyses_to_be_done",[]))>0:
        return [Send("kpi_rag",state),Send("split_path_decider_2",{"question":state["question"]})]
    return [Send("split_path_decider_2",{"question":state["question"]})]

# fmt: off
graph = StateGraph(state.OverallState)

graph.add_node(nodes.general_llm.__name__, nodes.general_llm)
graph.add_node("standalone_rag", map_fields_in_node(rag_e2e, {"answer":"final_answer"}))
graph.add_node("web_rag", map_fields_in_node(web_rag, {"answer":"final_answer"}))
graph.add_node(nodes.identify_missing_reports.__name__, nodes.identify_missing_reports)
graph.add_node(nodes.download_missing_reports.__name__, nodes.download_missing_reports)
graph.add_node("decomposed_rag", repeater)
graph.add_node("kpi_rag", kpi_workflow)
graph.add_node("persona_rag", persona_workflow)
graph.add_node("combine_answer", nodes.combine_answer_analysis)

graph.add_node(nodes.combine_conversation_history.__name__, nodes.combine_conversation_history)

if WORKFLOW_SETTINGS["check_safety"]:
    graph.add_node(nodes.check_safety.__name__, nodes.check_safety)

    graph.add_edge(START, nodes.check_safety.__name__)
    graph.add_conditional_edges(
        nodes.check_safety.__name__,
        edges.query_safe_or_not,
        {
            "yes": nodes.combine_conversation_history.__name__,
            "no": END,
        },
    )
else:
    graph.add_edge(START, nodes.combine_conversation_history.__name__)

graph.add_node(nodes.ask_clarifying_questions.__name__, nodes.ask_clarifying_questions)
graph.add_node(nodes.refine_query.__name__, nodes.refine_query)
graph.add_node(nodes.split_path_decider_1.__name__, nodes.split_path_decider_1)
graph.add_node(nodes.split_path_decider_2.__name__, nodes.split_path_decider_2)

graph.add_conditional_edges(
    nodes.combine_conversation_history.__name__,
    edges.route_initial_query,
    {
        "direct": nodes.general_llm.__name__,
        "rag": nodes.split_path_decider_1.__name__,
    },
)

graph.add_conditional_edges(
    nodes.split_path_decider_1.__name__,
    edges.decide_path,
    {
        "ask_questions": nodes.ask_clarifying_questions.__name__,
        "web": "web_rag"
    },
)

graph.add_conditional_edges(
    nodes.ask_clarifying_questions.__name__,
    edges.refine_query_or_not,
    {
        "no": nodes.identify_missing_reports.__name__,
        "yes": nodes.refine_query.__name__,
    },
)
graph.add_edge(nodes.refine_query.__name__, nodes.ask_clarifying_questions.__name__)
graph.add_edge(nodes.identify_missing_reports.__name__,nodes.download_missing_reports.__name__)
graph.add_conditional_edges(nodes.download_missing_reports.__name__, send_to_answer_analysis ,[nodes.split_path_decider_2.__name__,"kpi_rag"])
graph.add_conditional_edges(
    nodes.split_path_decider_2.__name__,
    edges.decide_path_post_clarification,
    {
        "rag": "standalone_rag",
        "decomposed_rag": "decomposed_rag",
        "persona": "persona_rag",
    },
)

# graph.add_edge("kpi_rag", )

if WORKFLOW_SETTINGS["follow_up_questions"]:
    graph.add_node(nodes.ask_follow_up_questions.__name__, nodes.ask_follow_up_questions)
    graph.add_edge(nodes.ask_follow_up_questions.__name__, END)
    rag_end_node = nodes.ask_follow_up_questions.__name__
else:
    rag_end_node = END
    

graph.add_edge(nodes.general_llm.__name__, rag_end_node)
graph.add_edge("web_rag", rag_end_node)
graph.add_edge("standalone_rag", "combine_answer")
graph.add_edge("decomposed_rag", "combine_answer")
graph.add_edge("kpi_rag", "combine_answer")
graph.add_edge("persona_rag", "combine_answer")

graph.add_edge("combine_answer",rag_end_node)

# fmt: on

memory = MemorySaver()
e2e = graph.compile(
    checkpointer=memory,
    interrupt_before=[
        nodes.refine_query.__name__,
        nodes.download_missing_reports.__name__,
        "kpi_rag",
        nodes.identify_missing_reports.__name__
    ],
)
