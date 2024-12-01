from langgraph.graph import END, StateGraph, START
from typing import Dict,List,Optional,Callable
import state,nodes,edges
import nodes.analysis,edges.analysis
def dummy_query_creator_node(state:state.OverallState)->state.InternalRAGState:
    return {"analysis_question_groups": ["Hi, how are you?","Bonjour, ca va?"]}
def dummy_agent_rag(state:state.InternalRAGState)->state.OverallState:
    return {"analysis_subquestions":state["analysis_question_groups"],"analysis_subresponses":["ok hi, I'm doing fine."]}

## TODO: check type of analysis_workflow ##
## ENFORCE: query_creator_node returns in the List[str] format for queries
## ENFORCE: actual workflow has create_analysis already called before entering this
## Original Queries -> Analyses -> Queries for Each -> Retrieve -> Combine
def analysis_workflow_simple(query_creator_node:Callable,rag_workflow:Callable,):
    graph = StateGraph(state.OverallState)
    graph.add_node("analysis_queries",query_creator_node)
    graph.add_node("agent_rag",rag_workflow)
    graph.add_node(nodes.analysis.combine_analysis_questions.__name__,nodes.analysis.combine_analysis_questions)
    
    graph.add_edge(START,"analysis_queries")
    graph.add_conditional_edges("analysis_queries",edges.analysis.send_analysis_questions,["agent_rag"])
    
    graph.add_edge("agent_rag",nodes.analysis.combine_analysis_questions.__name__)
    graph.add_edge(nodes.analysis.combine_analysis_questions.__name__,END)   
    
    return graph.compile()

if __name__=="__main__":
    import dotenv
    dotenv.load_dotenv()
    ## just to check state mgmt
    dummy_analysis_workflow = analysis_workflow_simple(dummy_query_creator_node,dummy_agent_rag)
    dummy_analysis_workflow.invoke({"question": "How are you?"})