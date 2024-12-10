import asyncio
import json
from sqlalchemy.orm import Session
from fastapi import WebSocketDisconnect
from . import models, schemas
import os
import random
import logging
import uuid
import traceback
from .process_base import BaseMessageProcessor

logger = logging.getLogger(__name__)

class MessageProcessor(BaseMessageProcessor):
    
    async def process_message(self, chat_id: int, space_id: int, message_text: str, websocket, db: Session):
        """Process incoming messages with error handling"""
        logger.info(f"Processing message for chat_id: {chat_id}, space_id: {space_id}")
        try:
            # Verify chat exists
            chat = db.query(models.Chat).filter(
                models.Chat.id == chat_id,
                models.Chat.space_id == space_id
            ).first()
            
            if not chat:
                logger.error(f"Chat not found: chat_id={chat_id}, space_id={space_id}")
                await websocket.send_json({
                    'type': 'error',
                    'content': 'Chat not found'
                })
                return

            # Save user message and handle initial setup
            try:
                user_message = await self.save_user_message(chat_id, message_text, websocket, db)
                if not user_message:
                    logger.error("Failed to save user message")
                    return
            except Exception as e:
                logger.error(f"Error saving user message: {str(e)}")
                await websocket.send_json({
                    'type': 'error',
                    'content': 'Failed to save message'
                })
                return

            # Generate and handle clarification
            try:
                clarification_question = generate_clarification_question(message_text)
                logger.info(f"Generated clarification question: {clarification_question}")
                
                clarification_answer = await self.handle_intermediate_message(
                    chat_id, 
                    clarification_question, 
                    websocket, 
                    db
                )
                
                if not clarification_answer:
                    logger.warning("No clarification answer received")
                    return
                
                logger.info(f"Received clarification answer: {clarification_answer}")
            except Exception as e:
                logger.error(f"Error in clarification flow: {str(e)}")
                await websocket.send_json({
                    'type': 'error',
                    'content': 'Failed to process clarification'
                })
                return

            # Generate final response with charts
            try:
                response = await generate_response(message_text, [])
                response_text = response["text"]
                charts_data = response["charts"]
                logger.info("Generated response and charts")

                # Save response message with charts
                response_message = models.Message(
                    chat_id=chat_id,
                    content=response_text,
                    is_user=False,
                    mode=self.mode
                )
                db.add(response_message)
                db.flush()
                
                # Save charts
                for chart_data in charts_data:
                    chart = models.Chart(
                        message_id=response_message.id,
                        chart_type=chart_data["chart_type"],
                        title=chart_data["title"],
                        data=chart_data["data"],
                        description=chart_data.get("description")
                    )
                    db.add(chart)
                
                db.commit()
                db.refresh(response_message)
                logger.info(f"Saved response message with id: {response_message.id}")

                # Send response with charts
                await websocket.send_json({
                    'type': 'response',
                    'message_id': response_message.id,
                    'content': response_text,
                    'charts': charts_data
                })
                
            except Exception as e:
                logger.error(f"Error generating/saving response: {str(e)}")
                await websocket.send_json({
                    'type': 'error',
                    'content': 'Failed to generate response'
                })
                return

        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Error in process_message: {str(e)}\n{error_trace}")
            await websocket.send_json({
                'type': 'error',
                'content': 'An unexpected error occurred'
            })

async def generate_response(content, chat_history):
    """Generate response with citations and charts"""
    try:
        logger.info(f"Generating response for content: {content}")
        response_text = (
            f"Here's what I found about {content}: "
            f"Recent market data [[1/https://finance.example.com/data]] shows interesting patterns. "
            f"The quarterly report [[2/q2-report.pdf/23]] provides additional context."
        )
        
        charts = generate_charts(content)
        return {
            "text": response_text,
            "charts": charts
        }
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise

def generate_charts(content):
    """Generate chart data based on the content"""
    try:
        logger.info("Generating charts...")
        charts = []
        
        # Sample line chart
        line_data = {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
            "datasets": [{
                "label": "Dataset 1",
                "data": [12, 19, 3, 5, 2],
                "borderColor": "rgb(75, 192, 192)",
                "tension": 0.1
            }]
        }
        
        line_chart = {
            "chart_type": "line",
            "title": "Performance Over Time",
            "data": json.dumps(line_data),
            "description": "Performance metrics over the past 5 months"
        }
        charts.append(line_chart)
        
        # Sample bar chart
        bar_data = {
            "labels": ["Category A", "Category B", "Category C"],
            "datasets": [{
                "label": "Values",
                "data": [65, 59, 80],
                "backgroundColor": [
                    "rgba(255, 99, 132, 0.5)",
                    "rgba(54, 162, 235, 0.5)",
                    "rgba(75, 192, 192, 0.5)"
                ]
            }]
        }
        
        bar_chart = {
            "chart_type": "bar",
            "title": "Category Comparison",
            "data": json.dumps(bar_data),
            "description": "Comparison across different categories"
        }
        charts.append(bar_chart)
        
        return charts
    except Exception as e:
        logger.error(f"Error generating charts: {str(e)}")
        return []

def generate_clarification_question(content):
    """Generate a clarification question based on the content"""
    try:
        questions = [
            {
                "question": "Would you like to see the historical trend or current status?",
                "options": ["Historical Trend", "Current Status"]
            },
            {
                "question": "Which aspect interests you most?",
                "options": ["Financial", "Operational", "Market Share"]
            },
            {
                "question": "What time period should we focus on?",
                "options": ["Last Quarter", "Last Year", "Last 5 Years"]
            }
        ]
        return random.choice(questions)
    except Exception as e:
        logger.error(f"Error generating clarification question: {str(e)}")
        return {
            "question": "Could you please provide more details?",
            "options": ["Yes", "No"]
        }

def generate_follow_up_response(answer):
    """Generate a follow-up response based on the clarification answer"""
    try:
        return f"I understand you're interested in {answer}. Let me focus on that aspect."
    except Exception as e:
        logger.error(f"Error generating follow-up response: {str(e)}")
        return "I'll proceed with generating a response."


def process_message(chat_id: int, space_id: int, message_text: str, websocket, db: Session):
    """Process incoming messages with error handling"""
    return MessageProcessor().process_message(chat_id, space_id, message_text, websocket, db)