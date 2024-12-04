from dotenv import load_dotenv
import os
import jsonlines
import uuid

load_dotenv()

from typing import Optional
import threading

from langchain_core.runnables import RunnableConfig
import config
from utils import log_message
from workflows.e2e import e2e as app
from workflows.kpi import kpi_workflow


def store_conversation_with_metadata(conversation_data, folder="data_convo/"):
    # Ensure the folder exists
    os.makedirs(folder, exist_ok=True)

    # Define the file path
    file_path = os.path.join(folder, "conversation_history.jsonl")

    # Append the data to the JSONL file
    with jsonlines.open(file_path, mode='a') as writer:
        writer.write({
            "record_id": conversation_data["user_id"],
            "query": conversation_data["question"],
            "answer": conversation_data["answer"],
            "type":"conversational_awareness"
        })

    print(f"Conversation successfully stored in {file_path}")

def run_kpi_workflow(question, analysis_topic, analysis_subject):
    """
    Function to run the KPI workflow in a separate thread.
    """
    try:
        print("Starting KPI Workflow...")
        analysis_answer = kpi_workflow.invoke(
            {
                "question": question,
                "analyses_to_be_done": analysis_topic,
                "analysis_subject": analysis_subject,
            }
        )["final_answer"]
        print("-------------ANALYSIS ANSWER-------------")
        print(analysis_answer)
    except Exception as e:
        print(f"Error in KPI Workflow: {e}")


def chatbot():
    print("Welcome to the 10-K Analyzer Chatbot. Ask your question below.")
    # question = input("Question: ")
    question = "Compare the revenue of Google in 2021"

    initial_input = {"question": question, "fast_vs_slow": "slow"}
    thread: RunnableConfig = {"configurable": {"thread_id": "1"}}
    to_restart_from: Optional[RunnableConfig] = None
    num_question_asked = 0
    user_id = str(uuid.uuid4())
    print("Your USER ID is", user_id)

    # Initialize clarifications list
    clarifications = []

    print("\nProcessing your query...\n")
    while True:
        try:
            inp = None if to_restart_from else initial_input
            # Run the graph until the first interruption
            for event in app.stream(inp, thread, stream_mode="values", subgraphs=True):
                pass
            # first interrupt : before refine_query and before identify_missing_reports

            log_message("---ASKING USER FOR CLARIFICATION---")
            while num_question_asked < config.MAX_QUESTIONS_TO_ASK:
                # Get the latest state
                state = app.get_state(thread).values
                clarifying_questions = state.get("clarifying_questions", [])

                if (
                    clarifying_questions
                    and clarifying_questions[-1]["question_type"] != "none"
                    and len(clarifying_questions) <= 3
                ):
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
                else:
                    log_message("No further clarifications required.")
                    break

                for event in app.stream(
                    None, thread, stream_mode="values", subgraphs=True
                ):
                    pass

            for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
                pass
            # second interrupt before download_missing_reports
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
                pass

            # third interrupt before analysis
            state = app.get_state(thread).values
            kpi_thread = None
            # if state["path_decided"] == "analysis":
            analysis_suggestions = state.get("analysis_suggestions", [])
            fast_vs_slow = state.get("fast_vs_slow", "slow")
            if fast_vs_slow.strip() == "slow":
                analysis_or_not = input(
                    "Do you want to get analysis done for a particular year/company? (Y/N): "
                )
                if analysis_or_not.strip().lower() in ["y", "yes"]:
                    # Let the user choose the company/year to run analysis on

                    combined_metadata = state["combined_metadata"]
                    options = [
                        {"company_name": x["company_name"], "filing_year": x["filing_year"]}
                        for x in combined_metadata
                    ]
                    print("Select the company/year you want to run analysis on:")
                    for i, option in enumerate(options, start=1):
                        print(f"{i}: {option['company_name']} ({option['filing_year']})")

                    # Get the user input as a number
                    selected_option = int(input("Enter the option number: ")) - 1

                    # Validate the input and fetch the selected item
                    if 0 <= selected_option < len(options):
                        analysis_subject = options[selected_option]

                    # Let the user choose the type of analysis to run
                    idx = list(range(1, len(analysis_suggestions) + 1))
                    analysis_options = "\n".join(
                        [
                            f"({i}) {option}"
                            for i, option in zip(idx, analysis_suggestions)
                        ]
                    )
                    analysis_topic = (
                        input(
                            f"Select the type of analysis you want to get done:\n{analysis_options}\nChoose any options: "
                        )
                        .replace(" ", "")
                        .split(",")
                    )
                    analysis_topic = [
                        analysis_suggestions[int(i) - 1] for i in analysis_topic
                    ]

                    app.update_state(
                        thread,
                        {
                            "analyses_to_be_done": analysis_topic,
                            "analysis_subject": [analysis_subject],
                        },
                    )

                    # Run the KPI workflow in a separate thread
                    kpi_thread = threading.Thread(
                        target=run_kpi_workflow,
                        args=(
                            state.get("question", ""),
                            analysis_topic,
                            analysis_subject,
                        ),
                    )
                    kpi_thread.start()

            for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
                pass

            # If we reach here, it means the thread has completed successfully

            # wait for the KPI thread to finish
            if kpi_thread is not None:
                kpi_thread.join()
            for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
                print(app.get_state(thread).next)
        
            state = app.get_state(thread).values
            conv={}
            conv["user_id"]=user_id
            conv["question"]=state["question"]
            conv["answer"]=state['final_answer']
            conv["type"]="conversational_awareness"
        
            print("\nFINAL ANSWER:", state["final_answer"])
            break
        except Exception as e:
            print(f"Error: {e}")
            inp = input("An error occurred, would you like to retry? ")
            if inp.lower() not in ["y", "yes"]:
                break

            last_state = next(app.get_state_history(thread))
            overall_retries = last_state.values.get("overall_retries", 0)
            if overall_retries >= config.MAX_RETRIES:
                print("Max retries exceeded! Exiting...")
                break

            to_restart_from = app.update_state(
                last_state.config,
                {"overall_retries": overall_retries + 1},
            )
            print("Retrying...")

if __name__ == "__main__":
    chatbot()
