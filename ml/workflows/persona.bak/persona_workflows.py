from langgraph.graph import END, StateGraph, START
from typing import Dict,List,Optional,Callable
import state,nodes,edges

### Building different type of workflows

## Function calls might be susceptible to Subgraph Error, can just copy the structure
## TODO: check if checkpoint gets passed into subgraphs

### PERSONA BASED ANALYSIS ###

## Change state.OverallState to the persona's relevant state
## ENFORCE that create_persona has run before

## Persona_Centralised: The series setup
## Persona_parallel: explains itself @geet 
##TODO: In parallel, state has to be managed 
## TODO: Tool use has to be unified

## persona with supervisor, the persona has access to tool
def persona_centralised(ToolMappings:Dict[state.Tool,Callable]):
    graph = StateGraph(state.OverallState)
    graph.add_node("supervisor",nodes.supervisor_basic) 
    graph.add_node("analyst_node",nodes.agent_node_centralised_tooled)
    graph.add_node(nodes.combine_discussion.__name__,nodes.combine_discussion)
    graph.add_node("tool_input",nodes.tool_input)
    graph.add_node("tool_output",nodes.update_conversation_with_tool)
    for tool,tool_func in ToolMappings.items():
        graph.add_node(tool.tool_name,tool_func)
    
    graph.add_edge(START,"supervisor")
    
    graph.add_conditional_edges(
        "analyst_node", edges.next_step_decision,
        {
            "tool_node": 'tool_input',
            "end_of_conversation":nodes.combine_discussion.__name__
        }
    )
    graph.add_conditional_edges(
        "supervisor", edges.next_step_supervisor,
        {
            "analyst_node":'analyst_node',
            "end_of_conversation":nodes.combine_discussion.__name__
        }
    )
    
    ### TODO: Testing: worst case tool dealing has to be changed ###
    graph.add_conditional_edges(
        "tool_input",
        lambda state: state["next_step"],
        {tool.tool_name: tool.tool_name for tool in ToolMappings.keys()}    
    )
    for tool in ToolMappings.keys():
        graph.add_edge(tool.tool_name,"tool_output")
    graph.add_edge("tool_output","analyst_node")
    graph.add_edge("analyst_node","supervisor") 
    
    graph.add_edge(nodes.combine_discussion.__name__,END)
    return graph.compile()

### Persona with decomposer, parallelly combined
def persona_parallel(ToolMappings:Dict[state.Tool,Callable]):
    graph = StateGraph(state.OverallState)
    graph.add_node("decomposer",nodes.persona_decomposer) 
    graph.add_node("analyst_node",nodes.agent_node_centralised_tooled)
    graph.add_node(nodes.combine_discussion.__name__,nodes.combine_discussion)
    graph.add_node("tool_input",nodes.tool_input)
    graph.add_node("tool_output",nodes.update_conversation_with_tool)
    for tool,tool_func in ToolMappings.items():
        graph.add_node(tool.tool_name,tool_func)
    
    graph.add_edge(START,"decomposer")
    
    graph.add_conditional_edges(
        "analyst_node", edges.next_step_analyst,
        {
            "tool_node": 'tool_input',
            "end_of_conversation":nodes.combine_discussion.__name__
        }
    )
    graph.add_conditional_edges(
        "decomposer", edges.send_to_personas,
        ["analyst_node"]
    )
    
    ### TODO: Testing: worst case tool dealing has to be changed ###
    graph.add_conditional_edges(
        "tool_input",
        lambda state: state["next_step"],
        {tool.tool_name: tool.tool_name for tool in ToolMappings.keys()}    
    )
    for tool in ToolMappings.keys():
        graph.add_edge(tool.tool_name,"tool_output")
    graph.add_edge("tool_output","analyst_node")
    graph.add_edge("analyst_node","supervisor") 
    
    graph.add_edge(nodes.combine_discussion.__name__,END)
    return graph.compile()


## Persona with decomposer, no tool
def persona_parallel_no_tool():
    graph = StateGraph(state.OverallState)
    graph.add_node("decomposer",nodes.persona_decomposer) 
    graph.add_node("analyst_node",nodes.agent_node_centralised_tooled)
    graph.add_node(nodes.combine_discussion.__name__,nodes.combine_discussion)
    
    
    graph.add_edge(START,"decomposer")
    
    graph.add_conditional_edges(
        "decomposer", edges.send_to_personas,
        ["analyst_node"]
    )
    graph.add_edge("analyst_node",nodes.combine_discussion.__name__)
    ## TODO: @geet
    ## ISSUE, parallel combine discussion not done yet
    graph.add_edge(nodes.combine_discussion.__name__,END)
    return graph.compile()

    


## centralised persona, all the context is already present. OLD CODE
def persona_centralised_no_tool():
    graph = StateGraph(state.OverallState)
    
    graph.add_node("supervisor",nodes.supervisor_basic)
    graph.add_node("analyst_node",nodes.agent_node_centralised)
    graph.add_node(nodes.combine_discussion.__name__,nodes.combine_discussion)
    
    graph.add_edge(START,"supervisor")
    graph.add_conditional_edges(
        "supervisor", edges.next_step_decision,
        {
            "analyst_node":'analyst_node',
            "end_of_conversation":nodes.combine_discussion.__name__
        }
    )
    graph.add_edge("analyst_node","supervisor") 
    graph.add_edge(nodes.combine_discussion.__name__,END)
    
    return graph.compile()

## persona with swarm, all the context is already present, OLD CODE
def persona_swarm():
    graph = StateGraph(state.OverallState)
    
    graph.add_node("analyst_node",nodes.agent_node_swarm)
    graph.add_node(nodes.combine_discussion.__name__,nodes.combine_discussion)
    
    graph.add_edge(START,"analyst_node")
    graph.add_conditional_edges(
        "analyst_node", edges.next_step_decision,
        {
            "analyst_node":'analyst_node',
            "end_of_conversation":nodes.combine_discussion.__name__
        }
    )
    graph.add_edge(nodes.combine_discussion.__name__,END)
    return graph.compile()
    

## OLD CODE
## persona with supervisor, the supervisor has access to tools
def persona_with_supervisor_tool(ToolMappings:Dict[state.Tool,Callable]):
    graph = StateGraph(state.OverallState)
    
    graph.add_node("analyst_node",nodes.agent_node_centralised) ### We are not giving the analyst tools
    graph.add_node(nodes.combine_discussion.__name__,nodes.combine_discussion)
    graph.add_node("tool_input",nodes.tool_input)
    graph.add_node("tool_output",nodes.update_conversation_with_tool)
    for tool,tool_func in ToolMappings.items():
        graph.add_node(tool.tool_name,tool_func)
    
    graph.add_edge(START,"supervisor")
    
    graph.add_conditional_edges(
        "supervisor", edges.next_step_decision,
        {
            "analyst_node":'analyst_node',
            "tool_node": 'tool_input',
            "end_of_conversation":nodes.combine_discussion.__name__
        }
    )
    
    ### TODO: Testing: worst case tool dealing has to be changed ###
    graph.add_conditional_edges(
        "tool_input",
        lambda state: state["next_step"],
        {tool.tool_name: tool.tool_name for tool in ToolMappings.keys()}    
    )
    for tool in ToolMappings.keys():
        graph.add_edge(tool.tool_name,"tool_output")
    graph.add_edge("tool_output","supervisor")
    graph.add_edge("analyst_node","supervisor") 
    
    graph.add_edge(nodes.combine_discussion.__name__,END)
    return graph.compile()



#############################################
