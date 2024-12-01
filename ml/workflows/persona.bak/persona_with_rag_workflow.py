from langgraph.graph import END, StateGraph, START
import nodes.analysts
from utils import log_message

import state, nodes, edges
from nodes.question_decomposer import question_combiner
import uuid
from .retriever_without_hallucination import retriever_without_hallucination


def rag1_to_rag2(state: state.InternalRAGState):
    if len(state["question_group"][-1]) == 1:
        return nodes.combine_answers.__name__
    else:
        return rag2.__name__


def rag2_to_rag3(state: state.InternalRAGState):
    if len(state["question_group"][-1]) == 2:
        return nodes.combine_answers.__name__
    else:
        return rag3.__name__


def agent_rag1_to_agent_rag2(state: state.InternalRAGState):
    if len(state["question_group"][-1]) == 1:
        return nodes.combine_analysis_questions.__name__
    else:
        return agent_rag2.__name__


def agent_rag2_to_agent_rag3(state: state.InternalRAGState):
    if len(state["question_group"][-1]) == 2:
        return nodes.combine_analysis_questions.__name__
    else:
        return agent_rag3.__name__


# def _rag_subgraph(state: state.InternalRAGState):
#     prev_question = None
#     prev_answer = None
#     question_group_id=str(uuid.uuid4())
#     for question in state["question_group"]:
#         # question_group_id=state.get("question_group_id", 1)
#         if prev_answer:
#             question = question_combiner.invoke(
#                 {
#                     "next_question": question,
#                     "prev_question": prev_question,
#                     "prev_answer": prev_answer,
#                 }
#             ).combined_question
#             log_message(f"Combined question:  {question}",f"question_group{question_group_id}")

#         prev_question = question
#         prev_answer = retriever_without_hallucination.invoke({"question": question,"question_group_id":question_group_id})["answer"]

#     return {
#         "decomposed_questions": [prev_question],
#         "decomposed_answers": [prev_answer],
#     }


def rag1(state: state.InternalRAGState):
    # prev_question = None
    # prev_answer = None
    question_group_id = str(uuid.uuid4())
    # for question in state["question_group"]:
    # question_group_id=state.get("question_group_id", 1)
    # if prev_answer:
    #     question = question_combiner.invoke(
    #         {
    #             "next_question": question,
    #             "prev_question": prev_question,
    #             "prev_answer": prev_answer,
    #         }
    #     ).combined_question
    #     log_message(f"Combined question:  {question}",f"question_group{question_group_id}")

    # prev_question = question
    answer1 = retriever_without_hallucination.invoke(
        {
            "question": state["question_group"][-1][0],
            "question_group_id": question_group_id,
        }
    )["answer"]

    return {
        # "decomposed_questions": [prev_question],
        "decomposed_answers": [answer1],
        "question_group": [state["question_group"]],
        # "number_of_question" : [len(state["question_group"])]
    }


def rag2(state: state.InternalRAGState):
    # prev_question = None
    # prev_answer = None
    question_group_id = str(uuid.uuid4())
    # for question in state["question_group"]:
    #     # question_group_id=state.get("question_group_id", 1)
    #     if prev_answer:
    question = question_combiner.invoke(
        {
            "next_question": state["question_group"][-1][1],
            "prev_question": state["question_group"][-1][0],
            "prev_answer": state["decomposed_answers"][0],
        }
    ).combined_question
    log_message(f"Combined question:  {question}", f"question_group{question_group_id}")
    answer = retriever_without_hallucination.invoke(
        {"question": question, "question_group_id": question_group_id}
    )["answer"]

    # decomposed_answers = state["decomposed_answers"][-1].append(answer)

    return {
        # "decomposed_questions": [prev_question],
        "decomposed_answers": [answer],
        "question_group": [state["question_group"]],
        # "number_of_question" : [len(state["question_group"])]
    }


def rag3(state: state.InternalRAGState):
    # prev_question = None
    # prev_answer = None
    question_group_id = str(uuid.uuid4())
    # for question in state["question_group"]:
    #     # question_group_id=state.get("question_group_id", 1)
    #     if prev_answer:
    question = question_combiner.invoke(
        {
            "next_question": state["question_group"][-1][2],
            "prev_question": state["question_group"][-1][1],
            "prev_answer": state["decomposed_answers"][1],
        }
    ).combined_question
    log_message(f"Combined question:  {question}", f"question_group{question_group_id}")
    answer = retriever_without_hallucination.invoke(
        {"question": question, "question_group_id": question_group_id}
    )["answer"]

    # decomposed_answers = state["decomposed_answers"][-1].append(answer)

    return {
        # "decomposed_questions": [prev_question],
        "decomposed_answers": [answer],
        # "number_of_question" : [len(state["question_group"])]
        "question_group": [state["question_group"]],
    }


def agent_rag(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    answer1 = retriever_without_hallucination.invoke(
        {
            "question": state["question_group"][-1][0],
            "question_group_id": question_group_id,
        }
    )["answer"]
    return {
        "analysis_subresponses": [answer1],
        "question_group": [state["question_group"]],
    }


def agent_rag2(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    prev_question = state["question_group"][-1][0]
    question = question_combiner.invoke(
        {
            "next_question": state["question_group"][-1][1],
            "prev_question": state["question_group"][-1][0],
            "prev_answer": state["analysis_subresponses"][0],
        }
    ).combined_question
    answer = retriever_without_hallucination.invoke(
        {"question": question, "question_group_id": question_group_id}
    )["answer"]
    return {
        "analysis_subquestions": [prev_question],
        "analysis_subresponses": [answer],
        "question_group": [state["question_group"]],
    }


def agent_rag3(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    prev_question = state["question_group"][-1][1]
    question = question_combiner.invoke(
        {
            "next_question": state["question_group"][-1][2],
            "prev_question": state["question_group"][-1][1],
            "prev_answer": state["analysis_subresponses"][1],
        }
    ).combined_question
    answer = retriever_without_hallucination.invoke(
        {"question": question, "question_group_id": question_group_id}
    )["answer"]
    return {
        "analysis_subquestions": [prev_question],
        "analysis_subresponses": [answer],
        "question_group": [state["question_group"]],
    }


## Test Function
def rag_tool(state: state.InternalRAGState) -> state.OverallState:
    answer = naive_rag.invoke({"question": state["tool_query"]})

    return {"tool_response": answer["answer"]}


def calc_tool(state: state.OverallState):
    return {"tool_response": "I am unable to perform calculations at the moment"}


# fmt: off
graph = StateGraph(state.OverallState)
graph.add_node(nodes.check_safety.__name__, nodes.check_safety)
graph.add_node(nodes.create_persona.__name__, nodes.create_persona)
graph.add_node(nodes.decompose_question_v2.__name__, nodes.decompose_question_v2)
graph.add_node(nodes.ask_clarifying_questions.__name__,nodes.ask_clarifying_questions)
graph.add_node(nodes.refine_query.__name__,nodes.refine_query)

graph.add_node(rag1.__name__, rag1)
graph.add_node(rag2.__name__, rag2)
graph.add_node(rag3.__name__, rag3)
graph.add_node("agent_rag", agent_rag)
graph.add_node(agent_rag2.__name__, agent_rag2)
graph.add_node(agent_rag3.__name__, agent_rag3)

graph.add_node("tool_rag",rag_tool)
graph.add_node("tool_calc",calc_tool)

graph.add_node(nodes.combine_answers.__name__, nodes.combine_answers)
graph.add_node(nodes.agent_node_v2.__name__, nodes.agent_node_v2)
graph.add_node(nodes.combine_discussion.__name__, nodes.combine_discussion)
graph.add_node(nodes.ask_analysis_question.__name__, nodes.ask_analysis_question)
graph.add_node(nodes.get_relevant_questions.__name__, nodes.get_relevant_questions)
graph.add_node(nodes.combine_analysis_questions.__name__, nodes.combine_analysis_questions)

graph.add_node(nodes.update_conversation.__name__, nodes.update_conversation)

graph.add_edge(START, nodes.check_safety.__name__)
graph.add_conditional_edges(
    nodes.check_safety.__name__,
    edges.query_modified_or_not,
    {
        nodes.process_query.__name__:nodes.ask_clarifying_questions.__name__,
        nodes.ask_clarifying_questions.__name__:nodes.ask_clarifying_questions.__name__,
        END:END
    }
)
graph.add_conditional_edges(
        nodes.ask_clarifying_questions.__name__,
        edges.refine_query_or_not,
        {
            nodes.ask_analysis_question.__name__:nodes.ask_analysis_question.__name__,
            nodes.refine_query.__name__:nodes.refine_query.__name__
        }
)
graph.add_edge(nodes.refine_query.__name__,nodes.ask_analysis_question.__name__)
graph.add_conditional_edges(
        nodes.ask_analysis_question.__name__,
        edges.check_query_type,
        {
            nodes.decompose_question_v2.__name__:nodes.decompose_question_v2.__name__,
            nodes.create_persona.__name__:nodes.create_persona.__name__
        }
)
graph.add_edge(nodes.create_persona.__name__, nodes.get_relevant_questions.__name__)
graph.add_conditional_edges(nodes.get_relevant_questions.__name__, edges.send_analysis_questions, ["agent_rag"])
graph.add_conditional_edges("agent_rag", agent_rag1_to_agent_rag2,
                                {
                                nodes.combine_analysis_questions.__name__,
                                agent_rag2.__name__
                                })
graph.add_conditional_edges(agent_rag2.__name__, agent_rag2_to_agent_rag3,
                                {
                                nodes.combine_analysis_questions.__name__,
                               agent_rag3.__name__
                                })
graph.add_edge(agent_rag3.__name__, nodes.combine_analysis_questions.__name__)


graph.add_edge(nodes.combine_analysis_questions.__name__, nodes.agent_node_v2.__name__)
graph.add_conditional_edges(
    nodes.agent_node_v2.__name__,
    edges.agent_response_v2,
    {
        nodes.agent_node_v2.__name__:nodes.agent_node_v2.__name__,
        "analysis_retrieve":"tool_rag",
        "analysis_calculator":"tool_calc",
        nodes.combine_discussion.__name__:nodes.combine_discussion.__name__
    }
)
graph.add_edge("tool_rag", nodes.update_conversation.__name__)
graph.add_edge("tool_calc", nodes.update_conversation.__name__)
graph.add_edge(nodes.update_conversation.__name__,nodes.agent_node_v2.__name__)

graph.add_edge(nodes.combine_discussion.__name__, END)

graph.add_conditional_edges(nodes.decompose_question_v2.__name__, edges.send_decomposed_question_groups_with_serial_hack, [rag1.__name__]) # type: ignore


graph.add_conditional_edges(rag1.__name__, rag1_to_rag2,
                                {
                                nodes.combine_answers.__name__,
                                rag2.__name__
                                })
graph.add_conditional_edges(rag2.__name__, rag2_to_rag3,
                                {
                                nodes.combine_answers.__name__,
                               rag3.__name__
                                })
graph.add_edge(rag3.__name__, nodes.combine_answers.__name__)
graph.add_edge(nodes.combine_answers.__name__, END)
# fmt: on
# Set up memory
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
final_workflow = graph.compile(
    checkpointer=memory,
    interrupt_before=[nodes.refine_query.__name__, nodes.create_persona.__name__],
)
