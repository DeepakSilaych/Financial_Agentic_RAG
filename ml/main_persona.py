from dotenv import load_dotenv
import os

load_dotenv()

from utils import log_message
import config
from workflows.persona_workflow_v1 import final_workflow as app

ques = input(
    "Question: "
)  # "What is Google's net expected revenue for next year?" #"Compare the RnD activities of Apple and Google, and how do these affect the future outlook of the companies."
initial_input = {
    "question": ques,
    "max_analysts": 3,
}  # "Compare the Research and Development expenses of Apple and Google"}

# Thread
thread = {"configurable": {"thread_id": "1"}}

# Run the graph until the first interruption
for event in app.stream(initial_input, thread, stream_mode="values"):
    print(event)

log_message("---ASKING USER FOR CLARIFICATION---")
try:
    state = app.get_state(thread).values
    clarifying_questions = state["clarifying_questions"]
    clarifications = []

    for question in clarifying_questions:
        # log_message("CLARIFYING QUESTION:"+ str(question))
        user_response = input(f"{question}: ")
        clarifications.append(f"{question}: {user_response}")
    app.update_state(thread, {"clarifications": clarifications})
except:
    log_message("---NO CLARIFYING QUESTIONS---")

for event in app.stream(None, thread, stream_mode="values"):
    print(event)

log_message("---ASKING USER FOR ANALYSIS TYPE QUERY---")
try:
    state = app.get_state(thread).values
    analysis_question = state["analysis_question"]
    if "No Analysis Required" not in analysis_question:
        user_response = input(f"{analysis_question}: ")
        app.update_state(thread, {"user_response_for_analysis": user_response})
    else:
        log_message("---NO ANALYSIS QUESTIONS---")
except:
    log_message("---NO ANALYSIS QUESTIONS---")

for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
    print(event)

state = app.get_state(thread).values
for msg in state["messages"]:
    print(msg)
print("FINAL ANSWER:", state["final_answer"])

with open("pipeline_log.txt", "w") as file:
    pass
