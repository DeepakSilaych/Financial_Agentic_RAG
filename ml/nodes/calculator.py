from typing import Dict
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils import log_message
from llm import llm

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
                print(f"Reattempting with feedback: {prompt}")

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
            exec(code[0], safe_globals)

            # Retrieve the result
            result = safe_globals.get("result", None)
            if result is None:
                return {"answer": "Error: No result found."}
            return {"answer": result}

        except Exception as e:
            # If there is an error in executing the code, print and handle the error
            print(f"Error during execution: {str(e)}")
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


# Example usage
# task = "What is year on year growth of NVIDIA?Year1:76 Year2:78 Year3:80 Year4:87"
# result = execute_task_and_get_result(task)
# print(result)  # This will print the final answer or error message
