from langgraph.graph import END, StateGraph, START
import uuid

import state, nodes, edges
from utils import log_message
from nodes.question_decomposer import question_combiner
from .rag_e2e import rag_e2e


def _rag_subgraph(state: state.InternalRAGState):
    prev_question = None
    prev_answer = None
    question_group_id = str(uuid.uuid4())
    for question in state["question_group"]:
        # question_group_id=state.get("question_group_id", 1)
        if prev_answer:
            question = question_combiner.invoke(
                {
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


# fmt: off
graph = StateGraph(state.OverallState)
graph.add_node(nodes.check_safety.__name__, nodes.check_safety)
graph.add_node(nodes.decompose_question_v2.__name__, nodes.decompose_question_v2)
graph.add_node(nodes.ask_clarifying_questions.__name__,nodes.ask_clarifying_questions)
graph.add_node(nodes.refine_query.__name__,nodes.refine_query)
graph.add_node("rag", _rag_subgraph)

graph.add_node(nodes.combine_answers.__name__, nodes.combine_answers)
graph.add_edge(START, nodes.check_safety.__name__)
graph.add_conditional_edges(
    nodes.check_safety.__name__,
    edges.query_modified_or_not,
    {
        nodes.process_query.__name__: nodes.ask_clarifying_questions.__name__,
        nodes.ask_clarifying_questions.__name__: nodes.ask_clarifying_questions.__name__,
        END:END
    }
)
graph.add_conditional_edges(
        nodes.ask_clarifying_questions.__name__,
        edges.refine_query_or_not,
        {
            nodes.decompose_question_v2.__name__:nodes.decompose_question_v2.__name__,
            nodes.refine_query.__name__:nodes.refine_query.__name__
        }
)
graph.add_edge(nodes.refine_query.__name__,nodes.decompose_question_v2.__name__)
graph.add_conditional_edges(nodes.decompose_question_v2.__name__, edges.send_decomposed_question_groups, ["rag"]) # type: ignore
graph.add_edge("rag", nodes.combine_answers.__name__)
graph.add_edge(nodes.combine_answers.__name__, END)
# fmt: on

# Set up memory
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
final_workflow = graph.compile(
    checkpointer=memory, interrupt_before=[nodes.refine_query.__name__]
)
