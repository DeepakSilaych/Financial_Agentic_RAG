from dotenv import load_dotenv

load_dotenv()

import json
import os
import jsonlines
import uuid
from typing import Optional

from langchain_core.runnables import RunnableConfig
import config
from utils import log_message
from workflows.e2e import e2e as app


def store_conversation_with_metadata(conversation_data, folder="data_convo/"):
    # Ensure the folder exists
    os.makedirs(folder, exist_ok=True)

    # Define the file path
    file_path = os.path.join(folder, "conversation_history.jsonl")

    # Append the data to the JSONL file
    with jsonlines.open(file_path, mode="a") as writer:
        writer.write(
            {
                "record_id": conversation_data["user_id"],
                "query": conversation_data["question"],
                "answer": conversation_data["answer"],
                "type": "conversational_awareness",
            }
        )

    print(f"Conversation successfully stored in {file_path}")


def get_all_available_financial_analyses():
    """
    Function to get all available financial analyses.
    """
    with open("experiments/kpis/kpis.json") as f:
        data = json.load(f)
    return [val["topic"] for val in data]


def chatbot():
    print("Welcome to the 10-K Analyzer Chatbot. Ask your question below.")
    question = input("Question: ")
    user_id = str(uuid.uuid4())
    print("Your USER ID is", user_id)
    initial_input = {
        "question": question,
        "fast_vs_slow": "slow",
        "user_id":user_id,
        # "image_path": "./images/image6.png"
    }
    final_answer=""
    thread: RunnableConfig = {"configurable": {"thread_id": "1"}}
    to_restart_from: Optional[RunnableConfig] = None
    num_question_asked = 0

    # Initialize clarifications list
    clarifications = []

    print("\nProcessing your query...\n")
    run = True
    while run:
        # try:
        inp = None if to_restart_from else initial_input
        # Run the graph until the first interruption
        for event in app.stream(inp, thread, stream_mode="values", subgraphs=True):
            print("#1", app.get_state(thread).next)
            next_nodes = app.get_state(thread).next
            if len(next_nodes) == 0:
                run = False
                break

        # If the thread has completed, break out of the loop
        # This happens when split_path_decider_1 has chosen `general`
        if not run:
            state = app.get_state(thread).values
            final_answer=state.get("final_answer","")
            break

        # first interrupt: after ask_clarifying_questions
        log_message("---ASKING USER FOR CLARIFICATION---")
        while num_question_asked < config.MAX_QUESTIONS_TO_ASK:
            # Get the latest state
            state = app.get_state(thread).values
            clarifying_questions = state.get("clarifying_questions", [])

            if (
                len(clarifying_questions) == 0
                or len(clarifying_questions) > config.MAX_QUESTIONS_TO_ASK
                or clarifying_questions[-1]["question_type"] == "none"
            ):
                log_message("No further clarifications required.")
                break

            question = clarifying_questions[-1]
            question_text = question.get("question", "")
            question_options = question.get("options", None)
            question_type = question.get("question_type", "direct-answer")

            if (
                question_type in ["multiple-choice", "single-choice"]
                and question_options
            ):
                idx = list(range(1, len(question["options"]) + 1))
                options = "\n".join(
                    [
                        f"({i}) {option}"
                        for i, option in zip(idx, question["options"])
                    ]
                )
                user_response = (
                    input(
                        f"{question_text}\nOptions:\n{options}\nChoose any option: "
                    )
                    .replace(" ", "")
                    .split(",")
                )
                answers = "; ".join(
                    [question["options"][int(i) - 1] for i in user_response]
                )
                clarifications.append(answers)
            else:
                user_response = input(f"{question_text}: ")
                clarifications.append(user_response)

            app.update_state(thread, {"clarifications": clarifications})
            num_question_asked += 1

            # Continue the conversation till all clarifications are asked
            for event in app.stream(
                None, thread, stream_mode="values", subgraphs=True
            ):
                print("#2", app.get_state(thread).next)

        for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
            print("#3", app.get_state(thread).next)
            next_nodes = app.get_state(thread).next
            if len(next_nodes) == 0:
                run = False
                break
        if not run:
            state = app.get_state(thread).values
            final_answer=state.get("final_answer","")
            break
        # second interrupt: after identify missing reports
        state = app.get_state(thread).values
        missing_company_year_pairs = state.get("missing_company_year_pairs", [])
        reports_to_download = []
        if missing_company_year_pairs:
            for x in missing_company_year_pairs:
                company = x["company_name"]
                year = x["filing_year"]
                print(f"We don't have data for {company} for year {year}")
                response_download = input(
                    "Do you want to download it from the web? (Y/N): "
                )
                if response_download.strip().lower() == "y":
                    reports_to_download.append(x)
        if reports_to_download:
            app.update_state(thread, {"reports_to_download": reports_to_download})

        for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
            print("#4", app.get_state(thread).next)
            next_nodes = app.get_state(thread).next
            if len(next_nodes) == 0:
                run = False
                break
        if not run:
            state = app.get_state(thread).values
            final_answer=state.get("final_answer","")
            break
        # third interrupt: after download missing reports
        state = app.get_state(thread).values
        fast_vs_slow = state.get("fast_vs_slow", "slow")
        if fast_vs_slow.strip() == "slow":
            analysis_or_not = input(
                "Do you want to get analysis done for a particular year/company? (Y/N): "
            )
            if analysis_or_not.strip().lower() in ["y", "yes"]:
                # Let the user choose the company/year to run analysis on

                combined_metadata = state["combined_metadata"]
                options = [
                    {
                        "company_name": x["company_name"],
                        "filing_year": x["filing_year"],
                    }
                    for x in combined_metadata
                ]
                print("Select the company/year you want to run analysis on:")
                for i, option in enumerate(options, start=1):
                    print(
                        f"{i}: {option['company_name']} ({option['filing_year']})"
                    )

                # Get the user input as a number
                selected_options = (
                    input("Enter the option number: ").replace(" ", "").split(",")
                )
                selected_options = [int(i) - 1 for i in selected_options]

                analysis_suggestions = state.get("analysis_suggestions", None)
                if analysis_suggestions is None or len(analysis_suggestions) == 0:
                    analysis_suggestions = get_all_available_financial_analyses()

                # Let the user choose the type of analysis to run
                idx = list(range(1, len(analysis_suggestions) + 1))
                analysis_options = "\n".join(
                    [
                        f"({i}) {option}"
                        for i, option in zip(idx, analysis_suggestions)
                    ]
                )
                analysis_topics = (
                    input(
                        f"Select the type of analysis you want to get done:\n{analysis_options}\nChoose any options: "
                    )
                    .replace(" ", "")
                    .split(",")
                )
                analysis_topics = [
                    analysis_suggestions[int(i) - 1].lower()
                    for i in analysis_topics
                ]

                app.update_state(
                    thread,
                    {
                        "analyses_to_be_done": analysis_topics,
                        "analysis_companies_by_year": [
                            options[selected_option]
                            for selected_option in selected_options
                        ],
                    },
                )

        for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
            print("#5", app.get_state(thread).next)
            next_nodes = app.get_state(thread).next
            if len(next_nodes) == 0:
                run = False
                break
        if not run:
            state = app.get_state(thread).values
            final_answer=state.get("final_answer","")
            break
        for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
            print("#6", app.get_state(thread).next)

        # If we reach here, it means the thread has completed successfully
        state = app.get_state(thread).values
        final_answer=state.get("final_answer","")
        break
    # except Exception as e:
        #     print(f"Error: {e}")
        #     inp = input("An error occurred, would you like to retry? ")
        #     if inp.lower() not in ["y", "yes"]:
        #         break

            # last_state = next(app.get_state_history(thread))
            # overall_retries = last_state.values.get("overall_retries", 0)
            # if overall_retries >= config.MAX_RETRIES:
            #     print("Max retries exceeded! Exiting...")
            #     break

            # to_restart_from = app.update_state(
            #     last_state.config,
            #     {"overall_retries": overall_retries + 1},
            # )
            # print("Retrying...")
    try:
        print("\nFINAL ANSWER:", final_answer)
        history={"question":state["question"],
                    "answer":state["final_answer"],
                    "user_id":user_id,
                }
        store_conversation_with_metadata(history)
    except Exception as e:
        print(f"Error:{e}")


if __name__ == "__main__":
    chatbot()
