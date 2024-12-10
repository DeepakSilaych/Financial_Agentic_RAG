from dotenv import load_dotenv

load_dotenv()

from typing import Optional
from langchain_core.runnables import RunnableConfig

from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
import state
import random


def node1(state):
    print("Node 1")
    if random.random() > 0.5:
        raise Exception("Random error from node1")
    return {
        "question": "new question from node 1",
    }


def node2(state):
    print("Node 2")
    if random.random() > 0.5:
        raise Exception("Random error from node2")
    return {
        "question": "new quesiton from node 2",
    }


# fmt: off
graph = StateGraph(state.OverallState)
graph.add_node(node1.__name__, node1)
graph.add_node(node2.__name__, node2)

graph.add_edge(START, node1.__name__)
graph.add_edge(node1.__name__, node2.__name__)
graph.add_edge(node2.__name__, END)
# fmt: on

app = graph.compile(checkpointer=MemorySaver())

MAX_RETRIES = 2

# Thread
initial_input = {"question": "What is the meaning of life?"}
thread: RunnableConfig = {"configurable": {"thread_id": "1"}}
to_restart_from: Optional[RunnableConfig] = None

while True:
    try:
        config = to_restart_from if to_restart_from else thread
        inp = None if to_restart_from else initial_input
        for event in app.stream(inp, config, stream_mode="values", subgraphs=True):
            pass

        # If we reach here, it means the thread has completed successfully
        print("Thread completed successfully!")
        break
    except Exception as e:
        print("Exception:", e)
        inp = input("An error occurred, would you like to retry? ")
        if inp.lower() not in ["y", "yes"]:
            break

        last_state = next(app.get_state_history(thread))
        overall_retries = last_state.values.get("overall_retries", 0)
        if overall_retries >= MAX_RETRIES:
            print("Max retries exceeded! Exiting...")
            break

        to_restart_from = app.update_state(
            last_state.config,
            {"overall_retries": overall_retries + 1},
        )
        print("Retrying...")

print("Final State:", app.get_state(thread))
print("Done!")
