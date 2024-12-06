import aiohttp
import asyncio
from datetime import datetime, timezone
import os
import openai
import base64
import requests
import config
import json

from langgraph.graph.graph import CompiledGraph
from langchain_core.runnables.graph import MermaidDrawMethod

import config

def visualize_workflow(graph: CompiledGraph, filename="graph.png"):
    img = graph.get_graph(xray=True).draw_mermaid_png(
        draw_method=MermaidDrawMethod.API,
    )

    with open(filename, "wb") as f:
        f.write(img)


async def _send_log(message, component="main"):
    async with aiohttp.ClientSession() as session:
        log_data = {
            "message": message,
            "level": "INFO",
            "component": component,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            async with session.post(
                "http://localhost:8000/log", json=log_data
            ) as response:
                return await response.json()
        except Exception as e:
            print(f"Failed to send log: {str(e)}")


def log_message(text, level=0):
    """Log a message to both file and websocket."""
    # # Format the message with timestamp
    # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # formatted_msg = f"[{timestamp}] {'  ' * int(level)}{text}"
    
    # log_queue.put(formatted_msg)


def tree_log(message, component="main"):
    if config.LOG_FILE_NAME == "stdout":
        print(message)
    elif config.LOG_FILE_NAME == "server":
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_send_log(message, component))
        finally:
            loop.close()
    else:
        with open(f"logs/tree_log.txt", "a") as log_file:
            log_file.write(message + "\n")

def hover_text_func(curr_node , output_state , input_state):
    if curr_node.split("//")[0] == "extract_metadata":
        return f"Decomposed_Question : {output_state.get('question' , '')} \n Metadata : {output_state.get('metadata', '')}"
    elif curr_node.split("//")[0] == "generate_answer_with_citation_state":
        return f"Answer : {output_state.get('answer', '')}"
    elif curr_node.split("//")[0] == "generate_web_answer":
        return f"Web answer : {output_state.get('answer', '')}"
    elif curr_node.split("//")[0] == "combine_answer_analysis":
        return f"Final Answer : {output_state.get('final_answer', '')}"
    elif curr_node.split("//")[0] == "rag_tool_node":
        if output_state.get('final_answer', '') != '':
            return f"Question : {input_state.get("question", "")} , Final Answer : {output_state.get('final_answer', '')}"
            # return f"Final Answer : {output_state.get('final_answer', '')}"
    elif curr_node.split("//")[0] == "agent":
        if input_state.get("persona", {}) != '':
            if input_state != {}:
                return f"Persona : {input_state.get("persona", {})}"
        else:
            return ""
    # elif curr_node.split("//")[0] == "":
    else : 
        return ""

def send_logs(parent_node=None, curr_node=None, child_node=None, text=None, input_state=None, output_state=None):
    # Construct the JSON payload
    payload = {
        "parent_node": parent_node,
        "current_node": curr_node,
        "child_node": child_node,
        "text": text,
        "text_state": hover_text_func(curr_node , output_state, input_state),
    }

    print(f"text_state: {hover_text_func(curr_node , output_state , input_state)}")


    print(f"payload: {payload}")
    # Send to WebSocket via queue
    # log_queue.put(json.dumps(payload))

    try:
        response = requests.post( "http://localhost:6969/receive_nodes"
            , json=payload)
    #     if response.status_code == 200:
    #         return response.json()  # Return the JSON response from the server
    #     else:
    #         print(f"ERROR: Request failed with status code: {response.status_code}")
    #         return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


from functools import lru_cache


@lru_cache
def get_from_analysts(name, lst):
    for analyst in lst:
        if analyst.role == name:
            return analyst
    return None


@lru_cache
def get_from_tools(name, lst):
    for tool in lst:
        if tool.tool_name == name:
            return tool
    return None


## check semantic similarity with roles
def get_closest_from_analysts(name, lst):
    """TODO: perhaps just do a soft search over roles"""
    return


def image_to_description(image_path):
    if not image_path or image_path == "":
        return "", ""

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    THIS_MODEL = "gpt-4o"
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    # image_path = "image.png"

    # Getting the base64 string
    base64_image = encode_image(image_path)

    # Send the request to the API
    response = client.chat.completions.create(
            model=THIS_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": [
                        {"type": "text",
                        "text": """
                        You are a part of the financial assistant built by our team. Your goal is to describe what is in the image provided as a file to the greatest detail possible. If it contains any numbers or has informatics, ypu should include that in your description. If it has any text, please include that as well. No information is too small. Please provide a detailed description of the image.
                        You should include every little detail you can see in the image.
                        You need to keep in mind that every text and number in the image is important.
                        
                        It should include:
                        - Detailed description of the image in high detail
                        - Text in the image - Don't miss any text with explanation and analysis
                        - Numbers in the image - This is very important - These should be understandable to the user individually like not just random numbers but it should be explained
                        - Detailed Analysis of the details in the image
                        
                        Strictly follow all the instructions given above.
                        """
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type":"text",
                            "text": "Do your job on the image"
                            },
                        {
                            "type": "image_url",
                            "image_url": 
                                {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                        }
                    ]
                }
            ],
        )
    # print(f"response: {response}")
    # Extract the description
    description = response.choices[0].message.content
    # print(f"Desription: {description}")
    return base64_image, description


def block_urls(urls, block_list, allow_list):
    """
    Block urls based on block_list and allow_list

    Args:
        urls (List[str]): List of urls
        block_list (List[str]): List of urls to block
        allow_list (List[str]): List of urls to allow

    Returns:
        List[str]: List of urls after blocking
    """
    query_urls = []
    new_urls = []
    for i in range(len(urls)):
        if sum([urls[i] in block_domain for block_domain in block_list]):
            continue
        if sum([urls[i] in allow_domain for allow_domain in allow_list]):
            new_urls.append(urls[i])
        else:
            query_urls.append(urls[i])

    return query_urls, new_urls
