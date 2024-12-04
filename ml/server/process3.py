from dotenv import load_dotenv
import os

load_dotenv()


import json
import uuid
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage

import config
import server.models as models
from utils import log_message
from workflows.repeater_with_HITL import repeater_with_HITL as app

import asyncio

logger = logging.getLogger(__name__)



async def process_message(chat_id: int, space_id: int, message_text: str, websocket, db: Session):

    try: 
        if not message_text or not message_text.strip():
          await websocket.send_json({
            'type': 'error',
            'content': 'Message cannot be empty'
          })
          return

        user_message = models.Message(
          chat_id=chat_id,
          content=message_text,
          is_user=True,
          mode="chat"
        )

        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        await websocket.send_json({
          'type': 'message_received',
          'message_id': user_message.id,
          'message': message_text
        })

        try:
            if len(db.query(models.Message).filter(models.Message.chat_id == chat_id).all()) == 1:
                chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
                chat.title = message_text
                db.commit()
                db.refresh(chat)
        except Exception as e:
            logger.error(f"Error updating chat title: {str(e)}")

        await asyncio.sleep(.1)

        thread = {"configurable": {"thread_id": "1"}}

        clarifications = []

        input_dict = {
          "question": message_text,
          "chat_id": chat_id,
          "message_id": user_message.id,
          "space_id": space_id
        }

        for event in app.stream(input_dict, thread, stream_mode="values"): pass

        log_message("---ASKING USER FOR CLARIFICATION---")

        while True:
            log_message("---ASKING USER FOR CLARIFICATION2---")
            state = app.get_state(thread).values
            clarifying_questions = state.get("clarifying_questions", [])

            log_message(f"clarifying_questions: {clarifying_questions}")

            if clarifying_questions and clarifying_questions[-1]["question_type"] != "none" and len(clarifying_questions) <3:
                question = clarifying_questions[-1]
                question_text = question.get("question", "")
                question_options = question.get("options", None)
                question_type = question.get("question_type", "direct-answer")

                print("question_text", question_text)

                intermediate_questions = models.IntermediateQuestion(
                    message_id=user_message.id,
                    question=question_text,
                    question_type=question_type,
                    options=json.dumps(question_options) if question_options else None
                )

                db.add(intermediate_questions)
                db.commit()
                db.refresh(intermediate_questions)

                await websocket.send_json({
                    'type': 'clarification',
                    'message_id': intermediate_questions.id,
                    'question': question_text,
                    'question_type': question_type,
                    'options': question_options
                })

                try:
                    response = await asyncio.wait_for(
                      websocket.receive_json(), 
                      timeout=300
                    )

                    if response.get('type') == 'clarification_response':
                      clarification_answer = response.get('answer')

                      # JSON serialize the answer if it's a list
                      if isinstance(clarification_answer, list):
                          intermediate_questions.answer = json.dumps(clarification_answer)
                      else:
                          intermediate_questions.answer = clarification_answer

                      db.commit()
                      db.refresh(intermediate_questions)

                      # Send confirmation back to UI
                      await websocket.send_json({
                          'type': 'clarification_response',
                          'message_id': intermediate_questions.id,
                          'answer': clarification_answer,
                          'status': 'confirmed'
                      })

                      clarifications.append({
                          "question": question_text,
                          "response": clarification_answer,
                          "question_type": question_type
                      })

                      app.update_state(thread, {"clarifications": clarifications})
                    else:
                      log_message("No further clarifications required.")
                      break
                except asyncio.TimeoutError:
                    log_message("User did not respond in time.")
                    break

            for event in app.stream(None, thread, stream_mode="values", subgraphs=True):pass


        state = app.get_state(thread).values
        missing_company_year_pairs = state.get("missing_company_year_pairs", [])
        reports_to_download=[]
        if missing_company_year_pairs:
            for x in missing_company_year_pairs:
                company=x["company_name"]
                year=x["filing_year"]

                intermediate_questions = models.IntermediateQuestion(
                    message_id=user_message.id,
                    question=f"We dont have data for {company} for year {year}, Do you want to download it from the web? (Y/N)",
                    question_type="single",
                    options=["yes","no"]
                )
                db.add(intermediate_questions)
                db.commit()
                db.refresh(intermediate_questions)

                try:
                    response = await asyncio.wait_for(
                      websocket.receive_json(), 
                      timeout=300
                    )

                    if response.get('type') == 'clarification_response':
                      clarification_answer = response.get('answer')

                      intermediate_questions.answer = clarification_answer
                      db.commit()
                      db.refresh(intermediate_questions)
                    if clarification_answer.strip()[0] == "y":
                        reports_to_download.append(x)
                except asyncio.TimeoutError:
                    log_message("User did not respond in time.")
                    break
        if reports_to_download:
            app.update_state(thread, {"reports_to_download":reports_to_download})

        response = ""
        for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
            try: 
                print(event)
                if event[1]["final_answer_with_citations"]:
                    response = event[1]["final_answer_with_citations"]
                    break
            except:
                pass

        bot_response = models.Message(
            chat_id=chat_id,
            content=response,
            is_user=False,
            mode="chat"
        )
        db.add(bot_response)
        db.commit()
        db.refresh(bot_response)
        
        await websocket.send_json({
            'type': 'bot_response',
            'message_id': bot_response.id,
            'content': response
        })

    except Exception as e:
        log_message(f"Error processing message: {str(e)}")
        await websocket.send_json({
            'type': 'error',
            'content': str(e)
        })