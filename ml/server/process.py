import asyncio
import json
from sqlalchemy.orm import Session
from fastapi import WebSocketDisconnect
from . import models, schemas
import os
import random
import logging
import uuid

logger = logging.getLogger(__name__)

async def process_message(chat_id: int, space_id: int, message_text: str, websocket, db: Session):
    print(f"Processing message for chat_id: {chat_id}")
    try:
        chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
        print(f"Chat found: {chat is not None}")
        if not chat:
            print("Chat not found, sending error")
            await websocket.send_json({
                'type': 'error',
                'content': 'Chat not found'
            })
            return

        print(f"Received message: {message_text}")
        if not message_text or not message_text.strip():
            print("Empty message, sending error")
            await websocket.send_json({
                'type': 'error',
                'content': 'Message cannot be empty'
            })
            return

        print("Creating user message in database")
        user_message = models.Message(
            chat_id=chat_id,
            content=message_text,
            is_user=True,
            mode="fast"
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        print(f"User message created with id: {user_message.id}")
        
        print("Acknowledging user message")
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

        print("Generating clarification question")
        clarification_question = generate_clarification_question(message_text)
        print(f"Generated clarification question: {clarification_question}")

        print("Saving clarification question")
        clarification_message = models.Message(
            chat_id=chat_id,
            content=clarification_question['question'],
            is_user=False,
            mode="fast"
        )
        db.add(clarification_message)
        db.commit()
        db.refresh(clarification_message)
        print(f"Clarification message saved with id: {clarification_message.id}")

        print("Sending clarification question to client")

        await websocket.send_json({
            'type': 'clarification',
            'message_id': clarification_message.id,
            'question': clarification_question['question'],
            'options': clarification_question['options']
        })

        while True:
            try:
                clarification_response = await websocket.receive_json()
                if clarification_response['type'] == 'clarification_response':
                    clarification_message.answer = clarification_response['answer']
                    db.commit()
                    break
            except WebSocketDisconnect:
                break

        print("Generating response")
        response = await generate_response(message_text, [])
        response_text = response["text"]
        charts_data = response["charts"]

        print("Generated charts data:", charts_data)
        
        print("Saving response message")
        response_message = models.Message(
            chat_id=chat_id,
            content=response_text,
            is_user=False,
            mode="fast"
        )
        db.add(response_message)
        db.flush()  # Get message ID without committing
        
        # Save charts
        for chart_data in charts_data:
            chart = models.Chart(
                message_id=response_message.id,
                chart_type=chart_data["chart_type"],
                title=chart_data["title"],
                data=chart_data["data"],  # Already JSON string
                description=chart_data.get("description")
            )
            db.add(chart)
        db.commit()

        print("Sending response to client with charts")
        await websocket.send_json({
            'type': 'response',
            'message_id': response_message.id,
            'content': response_text,
            'charts': charts_data
        })

    except Exception as e:
        print(f"Error in process_message: {str(e)}")
        logger.error(f"Error in process_message: {str(e)}")
        await websocket.send_json({
            'type': 'error',
            'content': 'Failed to process message'
        })

async def generate_response(content, chat_history):
    print(f"Generating response for content: {content}")
    print(f"Chat history length: {len(chat_history)}")
    # TODO: implement response generation logic
    # Example response with citations
    response_text = (
        f"Here's what I found about {content}: "
        f"Recent market data [[1/https://finance.example.com/data]] shows interesting patterns. "
        f"The quarterly report [[2/q2-report.pdf/23]] provides additional context."
    )
    print(f"Generated response: {response_text}")
    
    # Generate chart data
    charts = generate_charts(content)
    print("Generated charts:", charts)
    
    return {
        "text": response_text,
        "charts": charts
    }

def generate_charts(content):
    """Generate chart data based on the content"""
    print("Generating charts...")
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
    print("Generated line chart:", line_chart)
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
        "title": "Comparison Analysis",
        "data": json.dumps(bar_data),
        "description": "Comparison of different categories"
    }
    print("Generated bar chart:", bar_chart)
    charts.append(bar_chart)
    
    return charts

def generate_clarification_question(content):
    print(f"Generating clarification question for content: {content}")
    question_type = random.choice(['text', 'single', 'multi'])
    print(f"Selected question type: {question_type}")
    
    if question_type == 'text':
        question = {
            'type': 'text',
            'question': "Could you please provide more details about your request?",
            'options': None
        }
    elif question_type == 'single':
        question = {
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
        question = {
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
    print(f"Generated question: {question}")
    return question

def generate_follow_up_response(answer):
    print(f"Generating follow-up response for answer: {answer}")
    response = f"Thanks for clarifying. You said: {answer}"
    print(f"Generated follow-up response: {response}")
    return response