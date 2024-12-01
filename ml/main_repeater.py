from dotenv import load_dotenv
import os

load_dotenv()
# from utils import log_message
import config

# from workflows.generator_critic import final_workflow as app
# from workflows.final_workflow_without_hallucinator import final_workflow as app
from workflows.repeater_with_HITL import repeater_with_HITL as app

# from workflows.final_workflow_with_contregen import final_workflow as app
# from workflows.contregen import final_workflow_with_contregen as app


# Initialize the chatbot
def chatbot():
    # log_message("Initializing Chatbot...")

    # Thread for maintaining state
    thread = {"configurable": {"thread_id": "1"}}

    # Conversation loop
    while True:
        # Get user input
        user_query = input("You: ")
        if user_query.lower() in {"exit", "quit"}:
            print("Chatbot: Goodbye!")
            break

        # Input to the workflow
        input_data = {"question": user_query,
                      "image_path": "./images/image3.jpeg"}

        # Run the workflow
        # log_message("---PROCESSING QUERY---")
        for event in app.stream(input_data, thread, stream_mode="values"):
            print(f"Chatbot: {event}")

        # Check for clarifying questions
        state = app.get_state(thread).values
        clarifying_questions = state.get("clarifying_questions", [])
        clarifications = []

        if clarifying_questions:
            # log_message("---ASKING USER FOR CLARIFICATIONS---")
            for question in clarifying_questions:
                user_response = input(f"Chatbot (Clarification needed): {question}: ")
                clarifications.append(f"{question}: {user_response}")

            # Update state with clarifications
            app.update_state(thread, {"clarifications": clarifications})

            # Resume the workflow with clarifications
            # log_message("---RESUMING WITH CLARIFICATIONS---")
            for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
                print(f"Chatbot: {event}")

    # log_message("Chatbot session ended.")

    # Clear pipeline logs after session
    with open("pipeline_log.txt", "w") as file:
        pass


if __name__ == "__main__":
    chatbot()
