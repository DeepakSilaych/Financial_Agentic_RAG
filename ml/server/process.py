import asyncio
import json
from sqlalchemy.orm import Session
from fastapi import WebSocket
Disconnect
from . import models, schemas
import os
import random
import logging
import uuid

logger = logging.getLogger(__name__)

async def process_message(chat_id: int, message_text: str, websocket, db: Session):
    try:
        if not message_text or not message_text.strip():
            await websocket.send_json({
                'type': 'error',
                'content': 'Message cannot be empty'
            })
            return

        # Create user message in database
        user_message = models.Message(
            chat_id=chat_id,
            content=message_text,
            is_user=True,
            mode="chat"
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Acknowledge user message
        await websocket.send_json({
            'type': 'message_received',
            'message_id': user_message.id,
            'message': message_text
        })

        await asyncio.sleep(1)  # Wait for 1 second

        # Randomly decide to add clarification question
        clarification_answer = None
        if random.random() < 1:
            clarification_data = generate_clarification_question(message_text)
            if clarification_data:
                # Create bot message for clarification
                clarification_message = models.Message(
                    chat_id=chat_id,
                    content=clarification_data['question'],
                    is_user=False,
                    mode="clarification"
                )
                db.add(clarification_message)
                db.commit()
                db.refresh(clarification_message)

                # Create clarification question record
                clarification = models.IntermediateQuestion(
                    message_id=clarification_message.id,
                    question=clarification_data['question'],
                    question_type=clarification_data['type'],
                    options=json.dumps(clarification_data['options']) if clarification_data.get('options') else None
                )
                db.add(clarification)
                db.commit()
                db.refresh(clarification)
                
                # Send clarification
                await websocket.send_json({
                    'type': 'clarification',
                    'message_id': clarification.id,
                    'question': clarification_data['question'],
                    'question_type': clarification_data['type'],
                    'options': clarification_data.get('options', [])
                })

                # Wait for clarification response
                try:
                    response = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=300.0
                    )
                    if response.get('type') == 'clarification_response':
                        clarification_answer = response.get('answer')
                        
                        # Save user's clarification answer
                        if isinstance(clarification_answer, list):
                            clarification.answer = json.dumps(clarification_answer)
                        else:
                            clarification.answer = clarification_answer
                        db.commit()

                        # Send acknowledgment of answer
                        await websocket.send_json({
                            'type': 'clarification_response',
                            'message_id': clarification.id,
                            'answer': clarification_answer
                        })

                        # Create message for user's clarification answer
                        answer_content = (
                            ', '.join(clarification_answer) 
                            if isinstance(clarification_answer, list) 
                            else clarification_answer
                        )
                        clarification_response = models.Message(
                            chat_id=chat_id,
                            content=answer_content,
                            is_user=True,
                            mode="clarification_response"
                        )
                        db.add(clarification_response)
                        db.commit()
                        
                except asyncio.TimeoutError:
                    logging.warning("Timeout waiting for clarification response")

        # Generate final response content
        response_content = await generate_response(message_text, clarification_answer)
        
        # Create final bot response message
        bot_response = models.Message(
            chat_id=chat_id,
            content=response_content,
            is_user=False,
            mode="chat"
        )
        db.add(bot_response)
        db.commit()
        db.refresh(bot_response)
        
        # Send final response
        await websocket.send_json({
            'type': 'response',
            'message_id': bot_response.id,
            'content': response_content
        })
            
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        await websocket.send_json({
            'type': 'error',
            'content': 'An error occurred while processing your message'
        })

def generate_clarification_question(content):
    """Generate a clarification question with different types (text, single, multi)"""
    # Randomly choose question type for demonstration
    question_type = random.choice(['text', 'single', 'multi'])
    
    if question_type == 'text':
        return {
            'type': 'text',
            'question': "Could you please provide more details about your request?",
            'options': None
        }
    elif question_type == 'single-choice':
        return {
            'type': 'single',
            'question': "Which aspect are you most interested in?",
            'options': [
                "Market Analysis",
                "Investment Strategy",
                "Risk Assessment",
                "Portfolio Management"
            ]
        }
    else:  # multi
        return {
            'type': 'multiple-choice',
            'question': "Which areas would you like to focus on? (Select all that apply)",
            'options': [
                "Stocks",
                "Bonds",
                "Cryptocurrencies",
                "Real Estate",
                "Commodities"
            ]
        }

async def generate_response(content, clarification_answer=None):
    # TODO: implement response generation logic
    # Example response with citations
    if clarification_answer:
        if isinstance(clarification_answer, list):
            return (
                f"Based on your selections {', '.join(clarification_answer)}, here's what I found: "
                f"According to recent market analysis [[1/https://finance.example.com/market-trends]], "
                f"the sectors you selected show strong growth potential. "
                f"The detailed risk assessment [[2/financial-report-2023.pdf/15]] suggests a balanced approach. "
                f"You might also be interested in this market overview [[3/https://finance.example.com/overview]]."
            )
        return (
            f"Based on your clarification '{clarification_answer}', here's what I found: "
            f"The latest research [[1/research-paper.pdf/7]] supports your approach. "
            f"Market indicators [[2/https://finance.example.com/indicators]] suggest positive trends."
        )
    return (
        f"Here's what I found about {content}: "
        f"Recent market data [[1/https://finance.example.com/data]] shows interesting patterns. "
        f"The quarterly report [[2/q2-report.pdf/23]] provides additional context."
    )

def generate_follow_up_response(answer):
    # TODO: implement follow-up response generation logic
    return f"Thanks for clarifying. You said: {answer}"