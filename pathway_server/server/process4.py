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

def get_all_available_financial_analyses():
    """
    Function to get all available financial analyses.
    """
    print("DEBUG: Getting all available financial analyses")
    with open("experiments/kpis/kpis.json") as f:
        data = json.load(f)
    analyses = [val["topic"] for val in data]
    print(f"DEBUG: Available analyses: {analyses}")
    return analyses

logger = logging.getLogger(__name__)

class MessageProcessor(BaseMessageProcessor):
    def __init__(self, mode):
        super().__init__(mode)
        print(f"DEBUG: MessageProcessor initialized with mode: {mode}")

    async def run(self, chat_id: int, space_id: int, message_text: str, websocket, db: Session):
        print(f"DEBUG: Processing message for chat_id: {chat_id}, space_id: {space_id}")
        logger.info(f"Processing message for chat_id: {chat_id}, space_id: {space_id}")
        chat_exist = await self.check_chat_exists(chat_id, space_id, db)
        if not chat_exist:
            print(f"DEBUG: Chat not found: chat_id={chat_id}, space_id={space_id}")
            logger.error(f"Chat not found: chat_id={chat_id}, space_id={space_id}")
            await websocket.send_json({
                'type': 'error',
                'content': 'Chat not found'
            })
            return

        user_message = await self.save_user_message(chat_id, message_text, websocket, db)

        await asyncio.sleep(.1)
        print(f"DEBUG: User message saved: {user_message}")
  
        initial_input = {
            "question": message_text,
            "fast_vs_slow": self.mode,
            "user_id": chat_id
        }
        print(f"DEBUG: Initial input: {initial_input}")

        thread: RunnableConfig = {"configurable": {"thread_id": "1"}}
        to_restart_from: Optional[RunnableConfig] = None
        num_question_asked = 0
        user_id = chat_id

        clarifications = []

        run = True
        while run:
            try:
                print("DEBUG: Starting main processing loop")
                inp = None if to_restart_from else initial_input
                for event in app.stream(inp, thread, stream_mode="values", subgraphs=True):
                    next_nodes = app.get_state(thread).next
                    print(f"DEBUG: Next nodes: {next_nodes}")
                    if len(next_nodes) == 0:
                        run = False
                        break

                if not run:
                    print("DEBUG: Thread completed, breaking out of loop")
                    break

                print("DEBUG: Asking user for clarification")
                while num_question_asked < config.MAX_QUESTIONS_TO_ASK:
                    state = app.get_state(thread).values
                    clarifying_questions = state.get("clarifying_questions", [])
                    print(f"DEBUG: Clarifying questions: {clarifying_questions}")

                    if (
                        len(clarifying_questions) == 0
                        or clarifying_questions[-1]["question_type"] == "none"
                    ):
                        print("DEBUG: No further clarifications required")
                        break

                    question = clarifying_questions[-1]
                    question_text = question.get("question", "")
                    question_options = question.get("options", None)
                    question_type = question.get("question_type", "direct-answer")
                    print(f"DEBUG: Asking clarification: {question_text}")

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
                    print(f"DEBUG: User response: {user_response}")
                    clarifications.append(user_response)

                    app.update_state(thread, {"clarifications": clarifications})
                    num_question_asked += 1

                    for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
                        print(f"DEBUG: Stream event: {event}")

                for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
                    print(f"DEBUG: Stream event after clarifications: {event}")

                state = app.get_state(thread).values
                missing_company_year_pairs = state.get("missing_company_year_pairs", [])
                reports_to_download = []
                print(f"DEBUG: Missing company year pairs: {missing_company_year_pairs}")

                if missing_company_year_pairs:
                    for x in missing_company_year_pairs:
                        company = x["company_name"]
                        year = x["filing_year"]

                        company_question = {
                            "question": f"Do you have data for {company} for year {year}? \n Do you want to download it from the web? ",
                            "options": ["yes", "no"]
                        }

                        company_response = await self.handle_intermediate_message(
                            chat_id=chat_id,
                            question=company_question,
                            websocket=websocket,
                            db=db
                        )
                        print(f"DEBUG: Company response: {company_response}")

                        if company_response.strip().lower() == "yes":
                            reports_to_download.append(x)

                if reports_to_download:
                    print(f"DEBUG: Reports to download: {reports_to_download}")
                    app.update_state(thread, {"reports_to_download": reports_to_download})

                for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
                    print(f"DEBUG: Stream event after report download: {event}")

                state = app.get_state(thread).values

                if self.mode == "slow":
                    print("DEBUG: Entering slow mode analysis")
                    # Skip analysis question and assume "no" as default
                    analysis_response = "no"
                    print(f"DEBUG: Analysis response: {analysis_response}")

                    if analysis_response.strip().lower() == "yes":
                        combined_metadata = state["combined_metadata"]
                        options = [
                            {
                                "company_name": x["company_name"],
                                "filing_year": x["filing_year"],
                            }
                            for x in combined_metadata
                        ]
                        analysis_options_question = {
                            "question": "Select the company/year you want to run analysis on:",
                            "options": [f"{i+1}. {option['company_name']} ({option['filing_year']})" for i, option in enumerate(options)]
                        }
                        
                        selected_options = await self.handle_intermediate_message(
                            chat_id=chat_id,
                            question=analysis_options_question,
                            websocket=websocket,
                            db=db
                        )
                        selected_options = [int(option.split('.')[0]) - 1 for option in selected_options.split(',')]
                        print(f"DEBUG: Selected options: {selected_options}")

                        analysis_suggestions = state.get("analysis_suggestions", None)
                        
                        if analysis_suggestions is None or len(analysis_suggestions) == 0:
                            analysis_suggestions = get_all_available_financial_analyses()

                        analysis_topics_question = {
                            "question": "Select the type of analysis you want to get done",
                            "options": analysis_suggestions
                        }
                        
                        selected_analyses = await self.handle_intermediate_message(
                            chat_id=chat_id,
                            question=analysis_topics_question,
                            websocket=websocket,
                            db=db
                        )
                        
                        analysis_topics = [suggestion.lower() for suggestion in selected_analyses.split(',')]
                        print(f"DEBUG: Selected analysis topics: {analysis_topics}")

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
                    print(f"DEBUG: Final stream event: {event}")

                state = app.get_state(thread).values
                print(f"\nDEBUG: FINAL ANSWER: {state['final_answer']}\n")

                ''' charts '''
                res = visual_workflow.invoke({"input_data":state["final_answer"]})
                
                print("DEBUG: Chart response:", res['charts'])
                
                # Transform charts to match frontend format
                charts = []
                try:
                    for chart in res["charts"]:
                        # Handle both string and model object responses
                        if isinstance(chart, str):
                            # Skip invalid chart data
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
                except Exception as e:
                    print(f"ERROR transforming charts: {str(e)}")
                    print(f"Chart data: {res['charts']}")

                await self.handle_response(
                    chat_id, state["final_answer"], websocket, db, charts=charts
                )
                break
            except Exception as e:
                print(f"DEBUG: Error occurred: {e}")
                print(f"DEBUG: Traceback: {traceback.format_exc()}")

                error_question = {
                    "question": "An error occurred. Would you like to retry?",
                    "options": ["yes", "no"]
                }
                error_response = await self.handle_intermediate_message(
                    chat_id=chat_id,
                    question=error_question,
                    websocket=websocket,
                    db=db
                )
                print(f"DEBUG: Error response: {error_response}")
                if error_response.strip().lower() not in ["y", "yes"]:
                    break

                last_state = next(app.get_state_history(thread))
                overall_retries = last_state.values.get("overall_retries", 0)
                if overall_retries >= config.MAX_RETRIES:
                    print("DEBUG: Max retries exceeded! Exiting...")
                    break

                to_restart_from = app.update_state(
                    last_state.config,
                    {"overall_retries": overall_retries + 1},
                )
                print(f"DEBUG: Retrying... Retry count: {overall_retries + 1}")
