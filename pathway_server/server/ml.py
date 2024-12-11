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
from workflows.post_processing import visual_workflow

import asyncio
from sqlalchemy.orm import Session
from fastapi import WebSocketDisconnect
from . import models, schemas
import random
import logging
import traceback
from .process_base import BaseMessageProcessor


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


class MessageProcessor(BaseMessageProcessor):
    def __init__(self, mode):
        super().__init__(mode)
        print(f"DEBUG: MessageProcessor initialized with mode: {mode}")

    async def run(
        self, chat_id: int, space_id: int, message_text: str, websocket, db: Session
    ):
        print(
            f"DEBUG: run() called with chat_id: {chat_id}, space_id: {space_id}, message_text: {message_text}"
        )
        user_message = await self.save_user_message(
            chat_id, message_text, websocket, db
        )
        await asyncio.sleep(0.1)

        print(f"DEBUG: User message saved: {user_message}")

        initial_input = {
            "question": message_text,
            "fast_vs_slow": self.mode,
            "user_id": str(uuid.uuid4()),
        }
        final_answer = ""
        thread: RunnableConfig = {"configurable": {"thread_id": "1"}}
        to_restart_from: Optional[RunnableConfig] = None
        num_question_asked = 0

        # Initialize clarifications list
        clarifications = []

        print("\nProcessing your query...\n")
        run = True
        while run:
            try:
                inp = None if to_restart_from else initial_input
                # Run the graph until the first interruption
                for event in app.stream(
                    inp, thread, stream_mode="values", subgraphs=True
                ):
                    next_nodes = app.get_state(thread).next
                    if len(next_nodes) == 0:
                        run = False
                        break

                if not run:
                    state = app.get_state(thread).values
                    final_answer = state.get("final_answer", "")
                    break

                log_message("---ASKING USER FOR CLARIFICATION---")
                while num_question_asked < config.MAX_QUESTIONS_TO_ASK:
                    state = app.get_state(thread).values
                    print("#1", app.get_state(thread).next)
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

                    user_response = await self.handle_intermediate_message(
                        chat_id=chat_id,
                        question={
                            "question": question_text,
                            "options": question_options if question_options else [],
                            "question_type": question_type,
                        },
                        websocket=websocket,
                        db=db,
                    )

                    clarifications.append(",".join(user_response))

                    app.update_state(thread, {"clarifications": clarifications})
                    num_question_asked += 1

                    for event in app.stream(
                        None, thread, stream_mode="values", subgraphs=True
                    ):
                        print("#2", app.get_state(thread).next)

                for event in app.stream(
                    None, thread, stream_mode="values", subgraphs=True
                ):
                    print("#3", app.get_state(thread).next)
                    next_nodes = app.get_state(thread).next
                    if len(next_nodes) == 0:
                        run = False
                        break
                if not run:
                    state = app.get_state(thread).values
                    final_answer = state.get("final_answer", "")
                    break

                state = app.get_state(thread).values
                missing_company_year_pairs = state.get("missing_company_year_pairs", [])
                reports_to_download = []
                if missing_company_year_pairs:
                    for x in missing_company_year_pairs:
                        company = x["company_name"]
                        year = x["filing_year"]
                        print(f"DEBUG: Missing data for {company} for year {year}")
                        response_download = await self.handle_intermediate_message(
                            chat_id=chat_id,
                            question={
                                "question": f"We dont have data for {company} for year {year}, Do you want to download it from the web?",
                                "options": ["yes", "no"],
                                "question_type": "single-choice",
                            },
                            websocket=websocket,
                            db=db,
                        )
                        # Ensure response_download is a string
                        if (
                            isinstance(response_download, str)
                            and response_download.strip().lower() == "yes"
                        ):
                            reports_to_download.append(x)

                if reports_to_download:
                    app.update_state(
                        thread, {"reports_to_download": reports_to_download}
                    )

                for event in app.stream(
                    None, thread, stream_mode="values", subgraphs=True
                ):
                    print("#4", app.get_state(thread).next)
                    next_nodes = app.get_state(thread).next
                    if len(next_nodes) == 0:
                        run = False
                        break
                if not run:
                    state = app.get_state(thread).values
                    final_answer = state.get("final_answer", "")
                    break

                state = app.get_state(thread).values
                fast_vs_slow = state.get("fast_vs_slow", "slow")
                # Ensure fast_vs_slow is a string
                if isinstance(fast_vs_slow, str) and fast_vs_slow.strip() == "slow":
                    analysis_or_not = await self.handle_intermediate_message(
                        chat_id=chat_id,
                        question={
                            "question": "Do you want to run analysis on the companies?",
                            "options": ["yes", "no"],
                            "question_type": "single-choice",
                        },
                        websocket=websocket,
                        db=db,
                    )
                    if analysis_or_not[0] == "yes":
                        combined_metadata = state["combined_metadata"]
                        options = [
                            {
                                "company_name": x["company_name"],
                                "filing_year": x["filing_year"],
                            }
                            for x in combined_metadata
                        ]

                        if len(options) > 1:
                            selected_options = await self.handle_intermediate_message(
                                chat_id=chat_id,
                                question={
                                    "question": "Select the company/year you want to run analysis:",
                                    "options": [
                                        f"{option['company_name']}: {option['filing_year']}"
                                        for option in options
                                    ],
                                    "question_type": "multiple-choice",
                                },
                                websocket=websocket,
                                db=db,
                            )
                            selected_options = [
                                {
                                    "company_name": x.split(":")[0].strip(),
                                    "filing_year": x.split(":")[1].strip(),
                                }
                                for x in selected_options
                            ]
                        else:
                            selected_options = options

                        analysis_suggestions = state.get("analysis_suggestions", None)
                        if (
                            analysis_suggestions is None
                            or len(analysis_suggestions) == 0
                        ):
                            analysis_suggestions = (
                                get_all_available_financial_analyses()
                            )

                        analysis_topics = await self.handle_intermediate_message(
                            chat_id=chat_id,
                            question={
                                "question": f"Select the analysis topics you want to run:",
                                "options": analysis_suggestions,
                                "question_type": "multiple-choice",
                            },
                            websocket=websocket,
                            db=db,
                        )

                        app.update_state(
                            thread,
                            {
                                "analyses_to_be_done": [
                                    topic.lower() for topic in analysis_topics
                                ],
                                "analysis_companies_by_year": selected_options,
                            },
                        )

                for event in app.stream(
                    None, thread, stream_mode="values", subgraphs=True
                ):
                    print("#5", app.get_state(thread).next)
                    next_nodes = app.get_state(thread).next
                    if len(next_nodes) == 0:
                        run = False
                        break
                if not run:
                    state = app.get_state(thread).values
                    final_answer = state.get("final_answer", "")
                    break
                for event in app.stream(
                    None, thread, stream_mode="values", subgraphs=True
                ):
                    print("#6", app.get_state(thread).next)

                state = app.get_state(thread).values
                final_answer = state.get("final_answer", "")
                break
            except Exception as e:
                print(f"Error: {e}")
                error_question = {
                    "question": "An error occurred. Would you like to retry?",
                    "options": ["yes", "no"],
                }
                error_response = await self.handle_intermediate_message(
                    chat_id=chat_id, question=error_question, websocket=websocket, db=db
                )
                print(f"DEBUG: Error response: {error_response}")
                if error_response[0] != "yes":
                    return

                last_state = next(app.get_state_history(thread))
                overall_retries = last_state.values.get("overall_retries", 0)
                if overall_retries >= config.MAX_RETRIES:
                    print("Max retries exceeded! Exiting...")
                    return

                to_restart_from = app.update_state(
                    last_state.config,
                    {"overall_retries": overall_retries + 1},
                )
                print("Retrying...")

        print("\nFINAL ANSWER:", final_answer)
        history = {
            "question": state["question"],
            "answer": state["final_answer"],
            "user_id": chat_id,
        }
        store_conversation_with_metadata(history)

        res = visual_workflow.invoke({"input_data": state["final_answer"]})
        if res["final_output"]:
            state[
                "final_answer"
            ] = f"""
{state["final_answer"]}

---

#### Insights
{res["final_output"]}
"""

        charts = []
        for chart in res["charts"]:
            if isinstance(chart, str):
                print(f"WARNING: Received string instead of chart object: {chart}")
                continue

            chart_data = chart.model_dump()
            transformed_chart = {
                "chart_type": chart_data["type"].lower().split()[0],
                "data": {"labels": [], "datasets": []},
                "title": chart_data.get("title", ""),
            }

            if chart_data["type"] in ["Bar Chart", "Line Chart"]:
                transformed_chart["data"]["labels"] = [
                    str(x[0]) for x in next(iter(chart_data["data"].values()))
                ]
                for label, values in chart_data["data"].items():
                    transformed_chart["data"]["datasets"].append(
                        {"label": label, "data": [x[1] for x in values]}
                    )
            elif chart_data["type"] == "Pie Chart":
                transformed_chart["data"] = {
                    "labels": chart_data["labels"],
                    "datasets": [{"data": chart_data["values"]}],
                }

            charts.append(transformed_chart)

        await self.handle_response(
            chat_id,
            state["final_answer"],
            websocket,
            db,
            charts=charts,
            kpiAnalysis=state.get("kpi_answer", None),
        )
