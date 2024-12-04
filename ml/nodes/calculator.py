from typing import Dict, List
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import state
from utils import log_message
from llm import llm
from pydantic import BaseModel, Field
import sys

code_generator_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a Python code generator."),
        ("human", "{task}"),
    ]
)
code_generator = code_generator_prompt | llm | StrOutputParser()


def execute_task_and_get_result(task: str) -> Dict:
    """
    Takes a task description (e.g., 'average of 2, 4, and 5'), generates Python code using GPT-4's chat-based API,
    executes the code in a restricted environment, and returns the result in a human-readable format.
    """
    log_message(f"--- EXECUTE TASK: {task} ---")  # Log the task

    # Max number of retries in case of errors
    max_retries = 3

    # Variables to store previous error and code
    previous_code = ""
    previous_error = ""

    for attempt in range(1, max_retries + 1):
        log_message(f"Attempt {attempt} of code generation...")

        try:
            prompt = f"Write Python code to perform the following task and store the result in a variable called 'result': {task}"

            # If there was a previous error and code, pass them to GPT-4 to fix or improve
            if previous_error:
                prompt = (
                    f"Previous error: {previous_error}\nPrevious code:\n{previous_code}\n\n"
                    + prompt
                )
                log_message(f"Reattempting with feedback: {prompt}")

            # Send a prompt to GPT-4 to generate Python code via the chat completion endpoint
            response = code_generator.invoke({"task": prompt})

            # Extract the generated code from the API response
            code = response.strip()

            if not code:
                return {"answer": "Error: No code generated."}

            code = code.split("```python", 1)
            code = code[1].split("```", 1)
            log_message(f"Generated code: {code[0]}")

            # Store the current generated code for the next attempt (if needed)
            previous_code = code[0]

        except Exception as e:
            return {"answer": f"Error generating code: {str(e)}"}

        # Execute the generated code in a restricted environment
        safe_globals = {
            # "__builtins__": None,  # Disable all built-in functions for security
            "result": None,  # Variable to hold the result
        }

        try:
            # Execute the generated code
            exec("import os;\nimport sys;\nsys.stdout = open(os.devnull, 'w')\n" + code[0], safe_globals)
            sys.stdout = sys.__stdout__
            # Retrieve the result
            result = safe_globals.get("result", None)
            if result is None:
                return {"answer": "Error: No result found."}
            return {"answer": result}

        except Exception as e:
            # If there is an error in executing the code, print and handle the error
            log_message(f"Error during execution: {str(e)}")
            previous_error = str(e)  # Store the error for the next attempt

            # If it's the last attempt, return the error
            if attempt == max_retries:
                return {
                    "answer": f"Error executing the task after {max_retries} attempts: {str(e)}"
                }

            # If not the last attempt, the loop will retry automatically with new context

    # If we reach here, it means all attempts failed
    return {
        "answer": f"Sorry, the task could not be completed after {max_retries} attempts."
    }

class CalculatorOutput(BaseModel):
    """Output that we get for the query sent into the calculator"""

    caclculator_ques: List[str] = Field(
        description="Contains the list of strings which are instructions given to the calculator"
    )


calculator_system_prompt = """

You are a task describing agent, and the current year is 2024. You will be given a question and answer. 

Follow these instructions
1. For the question input, decide if there is any calculation that needs to be performed from the answer input
2. Give a list of all these calculations that need to be performed
3. If there is no calculation required, return an empty list

Here is an example

Example 1:
##INPUT:
Question: What was the net percentage increase in revenue for Microsoft from 2022 to 2023?
Answer: Microsoft's revenue in 2022 was $23 billion and that in 2023 was $27 billion

##OUTPUT:
["Find the percentage increase from $23 billion to $27 billion"]

Example 2:
##INPUT:
Question: What was the net percentage increase in revenue for Microsoft from 2022 to 2023?
Answer: Microsoft's net percentage increase in revenue from 2022 to 2023 is 12%

##OUTPUT:
[]

Do it for this input now

"""

calculator_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", calculator_system_prompt),
        ("human", "##INPUT:\nQuestion: {question}\nAnswer:{answer}\n\n##OUTPUT:\n"),
    ]
)
calculator_input = calculator_prompt | llm.with_structured_output(
    CalculatorOutput
)

class ProcessAnswer(BaseModel):
    """Returns final answer after calculator suggestions"""

    answer: str = Field(
        description="Contains final answer after calculator suggestions"
    )


process_answer_system_prompt = """

You are a question answer auditing agent, and the current year is 2024. You will be given a question and answer, and a few other input. 

Follow these instructions
1. Study the given question and answer, and integrate the comments provided into the answer to better answer the question
2. Dont add any extra information from your side, just use the context given to you

Here is an example

Example 1:
##INPUT:
Question: What was the net percentage increase in revenue for Microsoft from 2022 to 2023?
Answer: Microsoft's revenue in 2022 was $23 billion and that in 2023 was $27 billion
Suggestion: Find the percentage increase from $23 billion to $27 billion - 17.3%

##OUTPUT:
Microsoft's net percentage increase in revenue from 2022 to 2023 is 17.3%

Do it for this input now

"""

process_answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", process_answer_system_prompt),
        ("human", "##INPUT:\nQuestion: {question}\nAnswer:{answer}\nSuggestion:{suggestion}\n\n##OUTPUT:\n"),
    ]
)
process_answer = process_answer_prompt | llm.with_structured_output(
    ProcessAnswer
)



def calc_agent(state: state.InternalRAGState):
    question=state['original_question']
    answer=state['answer']
    operations=calculator_input.invoke({
        "question":question,
        "answer":answer
    }).caclculator_ques

    if(operations):
        final_answer=answer
        
    else:
        calculator_output=[]
        for operation in operations:
            calculator_output.append(execute_task_and_get_result(operation))

        suggestion_str='' 
        for operation, value in zip(operations, calculator_output):
            suggestion_str+=f'{operation} - {value} \n'
        
        final_answer=process_answer.invoke({
            "question":question,
            "answer":answer,
            "suggestion":suggestion_str
        })

    return{
            'answer':final_answer
        }



# Example usage
# task = "What is year on year growth of NVIDIA?Year1:76 Year2:78 Year3:80 Year4:87"
# result = execute_task_and_get_result(task)
# print(result)  # This will print the final answer or error message
