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

    async def run(self, chat_id: int, space_id: int, message_text: str, websocket, db: Session):
        print(f"DEBUG: run() called with chat_id: {chat_id}, space_id: {space_id}, message_text: {message_text}")
        user_message = await self.save_user_message(chat_id, message_text, websocket, db)
        await asyncio.sleep(.1)

        print(f"DEBUG: User message saved: {user_message}")

        initial_input = {
            "question": message_text,
            "fast_vs_slow": self.mode,
            "user_id": uuid.uuid4()
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
            inp = None if to_restart_from else initial_input
            # Run the graph until the first interruption
            for event in app.stream(inp, thread, stream_mode="values", subgraphs=True):
                print(f"DEBUG: Event: {event}")
                print("#1", app.get_state(thread).next)
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
                        "question_type": question_type
                    },
                    websocket=websocket,
                    db=db
                )

                clarifications.append(",".join(user_response))
                


                app.update_state(thread, {"clarifications": clarifications})
                num_question_asked += 1

                for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
                    print(f"DEBUG: Event: {event}")
                    print("#2", app.get_state(thread).next)

            for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
                print(f"DEBUG: Event: {event}")
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
                    if isinstance(response_download, str) and response_download.strip().lower() == "yes":
                        reports_to_download.append(x)

            if reports_to_download:
                app.update_state(thread, {"reports_to_download": reports_to_download})

            for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
                print(f"DEBUG: Event: {event}")
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
                # Ensure analysis_or_not is a string
                if isinstance(analysis_or_not, str) and analysis_or_not.strip().lower() == "yes":
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

                    analysis_response = await self.handle_intermediate_message(
                        chat_id=chat_id,
                        question={
                            "question": "Select the company/year you want to run analysis:",
                            "options": [str(i) for i in range(1, len(options) + 1)],
                            "question_type": "multiple-choice",
                        },
                    )
                    selected_options = (
                        analysis_response.replace(" ", "").split(",")
                    )
                    selected_options = [int(i) - 1 for i in selected_options]

                    analysis_suggestions = state.get("analysis_suggestions", None)
                    if analysis_suggestions is None or len(analysis_suggestions) == 0:
                        analysis_suggestions = get_all_available_financial_analyses()

                    idx = list(range(1, len(analysis_suggestions) + 1))
                    analysis_options = "\n".join(
                        [
                            f"({i}) {option}"
                            for i, option in zip(idx, analysis_suggestions)
                        ]
                    )
                    analysis_topics = await self.handle_intermediate_message(
                        chat_id=chat_id,
                        question={
                            "question": f"Select the analysis topics you want to run:\n{analysis_options}",
                            "options": [str(i) for i in range(1, len(analysis_suggestions) + 1)],
                            "question_type": "multiple-choice",
                        },
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
                print(f"DEBUG: Event: {event}")
                print("#5", app.get_state(thread).next)
                next_nodes = app.get_state(thread).next
                if len(next_nodes) == 0:
                    run = False
                    break
            if not run:
                state = app.get_state(thread).values
                final_answer = state.get("final_answer", "")
                break
            for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
                print(f"DEBUG: Event: {event}")
                print("#6", app.get_state(thread).next)

            state = app.get_state(thread).values
            final_answer = state.get("final_answer", "")
            break

        try:
            print("\nFINAL ANSWER:", final_answer)
            history = {
                "question": state["question"],
                "answer": state["final_answer"],
                "user_id": chat_id,
            }
            store_conversation_with_metadata(history)

            try:
                res = visual_workflow.invoke({'input_data': state["final_answer"]})

                charts = []
                for chart in res["charts"]:
                    if isinstance(chart, str):
                        print(f"WARNING: Received string instead of chart object: {chart}")
                        continue

                    chart_data = chart.model_dump()
                    transformed_chart = {
                        "chart_type": chart_data["type"].lower().split()[0],
                        "data": {
                            "labels": [],
                            "datasets": []
                        },
                        "title": chart_data.get("title", "")
                    }

                    if chart_data["type"] in ["Bar Chart", "Line Chart"]:
                        transformed_chart["data"]["labels"] = [str(x[0]) for x in next(iter(chart_data["data"].values()))]
                        for label, values in chart_data["data"].items():
                            transformed_chart["data"]["datasets"].append({
                                "label": label,
                                "data": [x[1] for x in values]
                            })
                    elif chart_data["type"] == "Pie Chart":
                        transformed_chart["data"] = {
                            "labels": chart_data["labels"],
                            "datasets": [{
                                "data": chart_data["values"]
                            }]
                        }

                    charts.append(transformed_chart)

                await self.handle_response(
                    chat_id, state["final_answer"], websocket, db, charts=charts
                )
            except Exception as e:
                print(f"Error: {e}")
                await self.handle_response(chat_id, state["final_answer"], websocket, db)

        except Exception as e:
            print(f"Error: {e}")
