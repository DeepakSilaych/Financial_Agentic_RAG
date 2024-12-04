from langgraph.graph import END, StateGraph, START

import state, nodes
from config import WORKFLOW_SETTINGS

web_rag = StateGraph(state.InternalRAGState)
web_rag.add_node(nodes.generate_web_answer.__name__, nodes.generate_web_answer)
web_rag.add_node(nodes.search_web.__name__, nodes.search_web)

web_rag.add_edge(START, nodes.search_web.__name__)
web_rag.add_edge(nodes.search_web.__name__, nodes.generate_web_answer.__name__)
web_rag.add_edge(nodes.generate_web_answer.__name__, END)

if WORKFLOW_SETTINGS["with_site_blocker"]:
    web_rag = web_rag.compile(interrupt_after=[nodes.search_web.__name__])
else:
    web_rag = web_rag.compile()
