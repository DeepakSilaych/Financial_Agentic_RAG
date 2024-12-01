from langgraph.graph import START, StateGraph, END
from utils import log_message

import state, nodes, edges
from .retriever_without_hallucination import with_doc_relevance
from ._1_naive_rag import naive_rag

## Series question answering


def rag_small(state: state.PersonaState):
    ## calls naive rag
    answer = naive_rag.invoke(
        {
            "question": state["rag_questions"][-1],
            "question_group_id": state["persona_id"],
        }
    )["answer"]
    return {"answer": answer}


def rag_in_depth(state: state.PersonaState):
    ## calls the full RAG agent
    answer = with_doc_relevance.invoke(
        {
            "question": state["rag_questions"][-1],
            "question_group_id": state["persona_id"],
        }
    )["answer"]
    return {"answer": answer}


# fmt: off
graph = StateGraph(state.PersonaState)
graph.add_node(nodes.create_persona.__name__, nodes.create_persona)
graph.add_node(nodes.persona_only_node.__name__, nodes.persona_only_node)
graph.add_node(nodes.persona_supervisor.__name__, nodes.persona_supervisor)
graph.add_node(nodes.persona_aggregator.__name__)
graph.add_node(rag_small.__name__,rag_small) ### Modify this
graph.add_node(rag_in_depth.__name__,rag_in_depth) ### Modify this

graph.add_edge(START, nodes.create_persona.__name__)
graph.add_edge(nodes.create_persona.__name__, nodes.persona_supervisor.__name__)
graph.add_edge(nodes.persona_supervisor.__name__, nodes.persona_only_node.__name__)
graph.add_conditional_edges(
    nodes.persona_supervisor.__name__,
    edges.agent_supervision_next_step,
    {
        "next_agent":nodes.persona_only_node.__name__,
        "done":nodes.persona_aggregator.__name__
    }
)
graph.add_conditional_edges(
    nodes.persona_only_node.__name__,
    edges.agent_answer,
    {
        "naive_rag":rag_small,
        "full_rag":rag_in_depth,
        "done":nodes.persona_supervisor.__name__
    }
)

graph.add_edge(nodes.persona_aggregator.__name__, END)

from langgraph.checkpoint.memory import MemorySaver 
persona_with_rag_series = graph.compile(checkpointer=MemorySaver())
