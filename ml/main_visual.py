from dotenv import load_dotenv
import os

load_dotenv()
from utils import log_message
import config
from workflows.series_parallel import final_workflow as app
from workflows.post_processing import visual_workflow as visual_workflow_app


initial_input = {
    "question": "Compare the Research and Development expenses of Apple and Google and give some figures in your answer too."
}

# Thread
thread = {"configurable": {"thread_id": "1"}}

# Run the graph until the first interruption
for event in app.stream(initial_input, thread, stream_mode="values"):
    print(event)
log_message("---ASKING USER FOR CLARIFICATION---")
state = app.get_state(thread).values
clarifying_questions = state["clarifying_questions"]
clarifications = []

for question in clarifying_questions:
    # log_message("CLARIFYING QUESTION:"+ str(question))
    user_response = input(f"{question}: ")
    clarifications.append(f"{question}: {user_response}")
app.update_state(thread, {"clarifications": clarifications})
for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
    try:
        if event[1]["final_answer"]:
            print(event)
            final_response = event[1]["final_answer"]
            break
    except:
        print(event)

if final_response == "":
    print("No final answer found")
    exit()

thread = {"configurable": {"thread_id": "2"}}
# insights = []
# final_answer_charts = ''
visual_input = {"input_data": final_response}
for event in visual_workflow_app.stream(visual_input, thread, stream_mode="values"):
    print(event)
