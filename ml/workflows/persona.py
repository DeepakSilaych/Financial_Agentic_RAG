from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

import state
from workflows.rag_e2e import rag_e2e

# Cannot put it in nodes.__init__ because of circular imports
from nodes import persona as persona_nodes
from edges import persona as persona_edges


def should_continue(state: state.PersonaState):
    last_question = state["persona_generated_questions"][-1]
    if last_question is not None:
        return "rag_tool"
    return persona_nodes.combine_persona_generated_answers.__name__


def rag_tool_node(state: state.PersonaState):
    res = rag_e2e.invoke({"question": state["persona_generated_questions"][-1]})
    return {"persona_generated_answers": [res["answer"]]}


# fmt: off
persona_agent_graph = StateGraph(state.PersonaState)
persona_agent_graph.add_node("agent", persona_nodes.generate_question_using_persona)
persona_agent_graph.add_node(persona_nodes.combine_persona_generated_answers.__name__, persona_nodes.combine_persona_generated_answers)
persona_agent_graph.add_node("rag_tool", rag_tool_node)

persona_agent_graph.add_edge(START, "agent")
persona_agent_graph.add_conditional_edges("agent", should_continue, ["rag_tool", persona_nodes.combine_persona_generated_answers.__name__])
persona_agent_graph.add_edge("rag_tool", "agent")
persona_agent_graph.add_edge(persona_nodes.combine_persona_generated_answers.__name__, END)

persona_agent = persona_agent_graph.compile()
# fmt: on

graph = StateGraph(state.OverallState)

# fmt: off
graph.add_node(persona_nodes.create_persona.__name__, persona_nodes.create_persona)
graph.add_node(persona_nodes.create_persona_specific_questions.__name__, persona_nodes.create_persona_specific_questions)
graph.add_node("agent_with_persona", persona_agent)
graph.add_node(persona_nodes.combine_persona_specific_answers.__name__, persona_nodes.combine_persona_specific_answers)

graph.add_edge(START, persona_nodes.create_persona.__name__)
graph.add_edge(persona_nodes.create_persona.__name__, persona_nodes.create_persona_specific_questions.__name__)
graph.add_edge(persona_nodes.create_persona_specific_questions.__name__, END)
graph.add_conditional_edges(persona_nodes.create_persona_specific_questions.__name__, persona_edges.send_personas_and_questions, ["agent_with_persona"])
graph.add_edge("agent_with_persona", persona_nodes.combine_persona_specific_answers.__name__)
# fmt: on

memory = MemorySaver()
persona_workflow = graph.compile(checkpointer=memory)
