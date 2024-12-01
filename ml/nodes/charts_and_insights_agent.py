from langchain_core.prompts import ChatPromptTemplate
from utils import log_message
import state, config
from llm import llm
from langchain_core.tools import tool
import numexpr
import math
import base64
from e2b_code_interpreter import Sandbox
from pydantic import BaseModel
import os


class FileName(BaseModel):
    pngfilename: str


# ----------------- prompts -----------------#

is_visualizable_prompt = """
You are a visualization agent that analyzes the input financial text data and determines if insights and charts can be generated.
Give your output strictly a bool value. 
"""

get_metrics_prompt = """
You are given with an output from our Financial Analysis chatbot.
You are required to identify the {num_metrics} most important metrics to calculate.
give your output in JSON format with keys as metric names and values as their descriptions and corresponding data from output analysis given to you which is required to calculate the metric.
note that you need to provide all the data required to calculate the corresponding metric.
"""

get_metrics_value_prompt = """
You are given with a metric name and it's description and the data required to calculate the metric.
You are required to calculate the value of the metric using the calculator tool.
give your output in JSON format with keys as metric name and value as their calculated value.
"""

get_insights_prompt = """
You are given with an output from our Financial Analysis chatbot and the calculated values of the metrics and their names.
You are required to make a meaningful insight from each metric.
give your output in list of string with each string as an insight.
"""

get_charts_desc_prompt = """
You are a financial data visualization expert.
Given a text description of financial data, your goal is to generate {num_charts} most appropriate charts to visualize the data. 
Consider these chart types and their use cases in no particular priority order:
1. Bar Charts
   - Best for: Category comparison, ranking, discrete data
   - Required: Categories and numeric values
2. Line Charts
    - Best for: Trend analysis, time series data, continuous metrics
    - Required: Time-based x-axis, numeric y-axis
3. Pie Charts
    - Best for: Composition analysis, part-to-whole relationships
    - Use sparingly, only when showing proportions
Output should be a list of dictionaries with keys as type, data and instructions.
Where type is the type of chart, data is the data to be visualized and instructions are the instructions 
you need to give to the code writer for generating the code for the chart.
"""

generate_chart_code_prompt = """    
You are a data visualization code writer.
You are given with the chart type, data and instructions to generate the code snippet for the chart please use that to generate the code snippet.
You should generate code snippet for the given data to create the chart type described in the prompt.
Guidelines:
- You can use Python libraries like Matplotlib, Seaborn, or Plotly for chart creation
- Do not print text or save anything in your code
- the chart should be showed at last line of the code using imshow method only and no other method
- ensure that the figure size is atleast (10, 6)
- Return a dictionary with keys as pngfilename and code, where pngfilename is the filename of the chart and code is the code snippet.
"""

generate_final_text_chart_prompt = """
You are given with the filenames of the charts are generated and saved.
But if there is a error in generating the chart then the filename would be "error".
You are required to give the final output as telling user that these all charts are generated and saved.
If some filename is "error" then you should not tell anything about that chart.
"""

# ----------------- tool -----------------#


@tool
def calculator(expression: str) -> float:
    """Calculate a financial metric using a mathematical expression.
    Expression should be a mathematical formula that gives the metric value.
    Example: "250000000/100000000*100" for percentage calculation"""
    local_dict = {"pi": math.pi, "e": math.e}
    cleaned_expr = expression.strip()
    try:
        result = float(
            numexpr.evaluate(cleaned_expr, global_dict={}, local_dict=local_dict)
        )
        return result
    except:
        return 0.0


# ----------------- llm -----------------#

llm_bool = llm.with_structured_output(state.Visualizable)
llm_metrics_structured = llm.with_structured_output(state.Metrics)
llm_calculator_structured = llm.bind_tools([calculator]).with_structured_output(
    state.Value
)
llm_insights_structured = llm.with_structured_output(state.Insights)
llm_gen_charts_structured = llm.with_structured_output(state.GenCharts_instructions)
llm_code_structured = llm.with_structured_output(state.CodeFormat)

# ----------------- nodes -----------------#


def is_visualizable_route(state: state.VisualizerState):

    log_message("--- IS VISUALIZABLE ROUTE ---")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", is_visualizable_prompt),
            ("user", "Here is the input data: {input}"),
        ]
    )
    is_visualizable_route = prompt | llm_bool
    response = is_visualizable_route.invoke({"input": state["input_data"]})
    return {"is_visualizable": response}


def get_metrics(state: state.VisualizerState):

    log_message("--- GET METRICS ---")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", get_metrics_prompt.format(num_metrics=config.NUM_METRICS)),
            ("user", "Here is the input data: {input}"),
        ]
    )
    metrics_descriptor = prompt | llm_metrics_structured
    response = metrics_descriptor.invoke({"input": state["input_data"]})
    return {"metrics": response.metrics}


def get_metric_value(state: state.Metric):

    log_message("--- GET METRIC VALUE ---")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", get_metrics_value_prompt),
            (
                "user",
                "The metric name is {name} and the description is {description}. \n The data required to calculate the metric is {data}",
            ),
        ]
    )
    metric_value_calculator = prompt | llm_calculator_structured
    response = metric_value_calculator.invoke(
        {"name": state.name, "description": state.description, "data": state.data}
    )
    return {"values": [response]}


def get_insights(state: state.VisualizerState):

    log_message("--- GET INSIGHTS ---")

    unstructured_metrics_values = "\n\n".join(
        f"{v.name_of_the_metric}: {v.value}" for v in state["values"]
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", get_insights_prompt),
            (
                "user",
                "Here is the input data: {input_data} \n\n The calculated values of the metrics and their names are: {unstructured_metrics_values}",
            ),
        ]
    )
    insights_generator = prompt | llm_insights_structured
    response = insights_generator.invoke(
        {
            "input_data": state["input_data"],
            "unstructured_metrics_values": unstructured_metrics_values,
        }
    )
    return {"final_insights": response.insights}


def get_charts_desc(state: state.VisualizerState):

    log_message("--- GET CHARTS DESC ---")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", get_charts_desc_prompt.format(num_charts=config.NUM_CHARTS)),
            ("user", "Here is the input data: {input_data}"),
        ]
    )
    chart_desc_generator = prompt | llm_gen_charts_structured
    response = chart_desc_generator.invoke({"input_data": state["input_data"]})
    return {"charts": response.charts}


def generate_chart_code_and_save(state: state.Chart):

    log_message("--- GENERATE CHART ---")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", generate_chart_code_prompt),
            (
                "user",
                "The chart type is {type} and the data is {data} \n\n The instructions are as follows: \n {instructions}",
            ),
        ]
    )
    chart_code_generator = prompt | llm_code_structured
    response = chart_code_generator.invoke(
        {"type": state.type, "data": state.data, "instructions": state.instructions}
    )

    sbx = Sandbox()  # By default the sandbox is alive for 5 minutes
    execution = sbx.run_code(response.code)  # Execute Python inside the sandbox
    first_result = execution.results[0]  # Get the first result

    # Save the chart
    if not os.path.exists("charts"):
        os.makedirs("charts")

    if first_result.png:
        with open(f"charts/{response.pngfilename}", "wb") as f:
            f.write(base64.b64decode(first_result.png))
        return {"final_chart_names": [FileName(pngfilename=response.pngfilename)]}
    else:
        return {"final_chart_names": [FileName(pngfilename="error")]}


def charts_final_output(state: state.VisualizerState):

    log_message("--- FINAL OUTPUT OF CHARTS ---")

    unstructured_filenames = "\n".join(
        f"{f.pngfilename}" for f in state["final_chart_names"]
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", generate_final_text_chart_prompt),
            ("user", "The filenames of the charts are: {unstructured_filenames}"),
        ]
    )
    chart_finalOutput_writer = prompt | llm
    response = chart_finalOutput_writer.invoke(
        {"unstructured_filenames": unstructured_filenames}
    )
    return {"final_output": response}
