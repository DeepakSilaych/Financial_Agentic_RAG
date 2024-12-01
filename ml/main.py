from dotenv import load_dotenv
import os

load_dotenv()
import json
import uuid
from utils import log_message
from datetime import datetime
import config
from langchain_core.messages import HumanMessage, AIMessage
# from workflows.repeater_with_HITL import repeater_with_HITL as app
# from workflows.final_workflow_with_path_decider import final_workflow_with_path_decider as app
from workflows.repeater_with_HITL import repeater_with_HITL as app

####### Debugging ####

initial_input = {
    "question": "How many employees did apple have globally as of June 30, 2023?"
}

# res = app.invoke(initial_input)

# print(res['answer'])


thread = {"configurable": {"thread_id": "1"}}

clarifications = []

for event in app.stream(initial_input, thread, stream_mode="values"):
    pass

log_message("---ASKING USER FOR CLARIFICATION---")

while True:
    # Get the latest state
    state = app.get_state(thread).values
    clarifying_questions = state.get("clarifying_questions", [])
    # Check if the last clarifying question exists and requires clarification
    if clarifying_questions and clarifying_questions[-1]["question_type"] != "none" and len(clarifying_questions)<3:
        question = clarifying_questions[-1]
        question_text = question.get("question", "")
        question_options = question.get("options", None)
        question_type = question.get("question_type", "direct-answer")

        # Display the question and handle response based on the type
        if question_type in ["multiple-choice", "single-choice"] and question_options:
            print(f"{question_text}\nOptions: {', '.join(question_options)}")
        else:
            print(question_text)

        # Get the user's response
        user_response = input("Your response: ")

        # Append the response to clarifications
        clarifications.append({
            "question": question_text,
            "response": user_response,
            "question_type": question_type
        })

        # Update the state with the user's clarifications
        app.update_state(thread, {"clarifications": clarifications})
    else:
        log_message("No further clarifications required.")
        break

    # Run the graph to generate subsequent clarifying questions
    for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
        print(event)
state=app.get_state(thread).values
analysis_suggestions=state.get("analysis_suggestions",[])
path_decided=state.get("path_decided","")
if path_decided=="analysis":
    analysis_or_not=input("Do you want to get analysis done for a particular year/company?(Y/N)")
    if analysis_or_not.strip()=="y":
        combined_metadata=state["combined_metadata"]
        options=[{x.company_name:x.filing_year} for x in combined_metadata]
        analysis_subject=input(f"Select the company/yearyou want to run analysis on : {options}")
        analysis_topic=input(f"Select the type of analysis you want to get done: {analysis_suggestions}")
        app.update_state(thread,{"analysis_topic":analysis_topic, "analysis_subject":analysis_subject})


for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
    print(event)
state = app.get_state(thread).values
missing_company_year_pairs = state.get("missing_company_year_pairs", [])
reports_to_download=[]
if missing_company_year_pairs:
    for x in missing_company_year_pairs:
        company=x["company_year"]
        year=x["filing_year"]
        print(f"We dont have data for {company} for year {year}")
        response_download=input("Do you want to download it from the web? (Y/N)")
        if response_download.strip() == "y":
            reports_to_download.append(x)
        
if reports_to_download:
    app.update_state(thread, {"reports_to_download":reports_to_download})
for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
    print(event)



# #########  ------------- Conversation Chatbot

# # # Initialize the chatbot
# # def chatbot():
# #     log_message("Initializing Chatbot...")
# #     folder_path = 'logs'
# #     for filename in os.listdir(folder_path):
# #         file_path = os.path.join(folder_path, filename)
# #         if os.path.isfile(file_path):
# #             os.remove(file_path)
    
# #     # Thread for maintaining state
# #     thread = {"configurable": {"thread_id": "1"}}
    
# #     # Conversation loop
# #     while True:
# #         # Get user input
# #         user_query = input("You: ")
# #         if user_query.lower() in {"exit", "quit"}:
# #             print("Chatbot: Goodbye!")
# #             break

# #         # Input to the workflow
# #         input_data = {"question": user_query}

# #         # Run the workflow
# #         log_message("---PROCESSING QUERY---")
# #         for event in app.stream(input_data, thread, stream_mode="values"):
# #             print(f"Chatbot: {event}")

# #         # Check for clarifying questions
# #         state = app.get_state(thread).values
# #         clarifying_questions = state.get("clarifying_questions", [])
# #         clarifications = []

# #         if clarifying_questions:
# #             log_message("---ASKING USER FOR CLARIFICATIONS---")
# #             for question in clarifying_questions:
# #                 user_response = input(f"Chatbot (Clarification needed): {question}: ")
# #                 clarifications.append(f"{question}: {user_response}")

# #             # Update state with clarifications
# #             app.update_state(thread, {"clarifications": clarifications})

# #             # Resume the workflow with clarifications
# #             log_message("---RESUMING WITH CLARIFICATIONS---")
# #             for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
# #                 print(f"Chatbot: {event}")
# #             state=app.get_state(thread).values
# #             question=state.get("question","")
# #             final_answer=state.get("final_answer","")
# #             print("--------------FINAL ANSWER-------------")
# #             print(final_answer)
# #             # data={
# #             #     "time_stamp": datetime.now().isoformat() ,
# #             #     "User":HumanMessage(content=question,role="User"),
# #             #     "Chatbot":AIMessage(content=final_answer,role="Chatbot")
# #             # }
# #             # conversation_id=str(uuid.uuid4())

# #             # with open(f"conversational_history/{conversation_id}.json", "w") as file:
# #             #     json.dump(data, file, indent=4)

# #     log_message("Chatbot session ended.")


# # if __name__ == "__main__":
# #     chatbot()
