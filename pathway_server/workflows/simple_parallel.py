from langgraph.graph import END, StateGraph, START
import uuid

import state, nodes, edges
from utils import log_message
from nodes.question_decomposer import question_combiner
from .rag_e2e import rag_e2e


# def rag1_to_rag2(state: state.InternalRAGState):
#     if len(state["question_group"][-1]) == 1:
#         return nodes.combine_answer_v1.__name__
#     else:
#         return rag2.__name__


# def rag2_to_rag3(state: state.InternalRAGState):
#     if len(state["question_group"][-1]) == 2:
#         return nodes.combine_answer_v1.__name__
#     else:
#         return rag3.__name__


def rag1(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    res = rag_e2e.invoke(
        {
            "question": state["question_group"][-1][0],
            "question_group_id": question_group_id,
        }
    )
    print(f"\n\n {res} \n\n")
    answer = res["answer"]
    return {
        "decomposed_answers": [answer],
        "combined_documents": res.get("documents",[]),
        "question_group": [state["question_group"]],
    }


# def rag2(state: state.InternalRAGState):
#     question_group_id = str(uuid.uuid4())
#     question = question_combiner.invoke(
#         {
#             "next_question": state["question_group"][-1][1],
#             "prev_question": state["question_group"][-1][0],
#             "prev_answer": state["decomposed_answers"][0],
#         }
#     ).combined_question
#     log_message(f"Combined question:  {question}", f"question_group{question_group_id}")
#     res = rag_e2e.invoke({"question": question, "question_group_id": question_group_id})
#     print(f"\n\n {res} \n\n")
#     answer = res["answer"]

#     return {
#         "decomposed_answers": [answer],
#         "combined_documents": res.get("documents",[]),
#         "question_group": [state["question_group"]],
#     }


# def rag3(state: state.InternalRAGState):
#     question_group_id = str(uuid.uuid4())
#     question = question_combiner.invoke(
#         {
#             "next_question": state["question_group"][-1][2],
#             "prev_question": state["question_group"][-1][1],
#             "prev_answer": state["decomposed_answers"][1],
#         }
#     ).combined_question
#     log_message(f"Combined question:  {question}", f"question_group{question_group_id}")
#     res = rag_e2e.invoke({"question": question, "question_group_id": question_group_id})
#     print(f"\n\n {res} \n\n")
#     answer = res["answer"]

#     return {
#         "decomposed_answers": [answer],
#         "combined_documents": res.get("documents",[]),
#         "question_group": [state["question_group"]],
#     }


# fmt: off
graph = StateGraph(state.OverallState)
graph.add_node(nodes.decompose_question_v2.__name__, nodes.decompose_question_v2)
graph.add_node(nodes.expand_question.__name__, nodes.expand_question)
graph.add_node(rag1.__name__, rag1)
# graph.add_node(rag2.__name__, rag2)
# graph.add_node(rag3.__name__, rag3)
graph.add_node(nodes.combine_answer_v1.__name__, nodes.combine_answer_v1)
graph.add_node(nodes.append_citations.__name__,nodes.append_citations)
graph.add_edge(START,nodes.expand_question.__name__)
graph.add_edge(nodes.expand_question.__name__, nodes.decompose_question_v2.__name__)
graph.add_conditional_edges(nodes.decompose_question_v2.__name__, edges.send_decomposed_question_groups_with_serial_hack, [rag1.__name__])  # type: ignore
# graph.add_conditional_edges(
#     rag1.__name__, rag1_to_rag2,
#     [
#         nodes.combine_answer_v1.__name__,
#         rag2.__name__,
#     ],
# )
# graph.add_conditional_edges(
#     rag2.__name__, rag2_to_rag3,
#     [
#         nodes.combine_answer_v1.__name__,
#         rag3.__name__,
#     ]
# )
graph.add_edge(rag1.__name__, nodes.combine_answer_v1.__name__)
graph.add_edge(nodes.combine_answer_v1.__name__,nodes.append_citations.__name__)
graph.add_edge(nodes.append_citations.__name__ ,END)
# fmt: on

simple_parallel = graph.compile()
