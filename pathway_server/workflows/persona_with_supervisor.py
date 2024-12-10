from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

import state
from workflows.rag_e2e import rag_e2e

# Cannot put it in nodes.__init__ because of circular imports
from nodes import persona as persona_nodes


def should_continue(state: state.OverallState):
    current_persona = state["current_persona"]
    if current_persona is not None:
        return "generate_question"
    return "combine_answer_v1"


def rag_tool_node(state: state.OverallState):
    res = rag_e2e.invoke(
        {"question": state["persona_generated_questions_using_supervisor"][-1]}
    )
    return {"persona_generated_answers_using_supervisor": [res["answer"]]}


graph = StateGraph(state.OverallState)

# fmt: off
graph.add_node(persona_nodes.create_persona.__name__, persona_nodes.create_persona)
graph.add_node(persona_nodes.select_next_persona.__name__, persona_nodes.select_next_persona)
graph.add_node(persona_nodes.generate_question_using_persona_with_supervisor.__name__, persona_nodes.generate_question_using_persona_with_supervisor)
graph.add_node("rag_tool", rag_tool_node)
graph.add_node(persona_nodes.combine_persona_with_supervisor_generated_answers.__name__, persona_nodes.combine_persona_with_supervisor_generated_answers)

graph.add_edge(START, persona_nodes.create_persona.__name__)
graph.add_edge(persona_nodes.create_persona.__name__, persona_nodes.select_next_persona.__name__)
graph.add_conditional_edges(persona_nodes.select_next_persona.__name__, should_continue,
                            {
                                "generate_question": persona_nodes.generate_question_using_persona_with_supervisor.__name__,
                                "combine_answer_v1": persona_nodes.combine_persona_with_supervisor_generated_answers.__name__
                            })
graph.add_edge(persona_nodes.generate_question_using_persona_with_supervisor.__name__, "rag_tool")
graph.add_edge("rag_tool", persona_nodes.select_next_persona.__name__)
graph.add_edge(persona_nodes.combine_persona_with_supervisor_generated_answers.__name__, END)
# fmt: on

memory = MemorySaver()
persona_workflow = graph.compile(checkpointer=memory)
