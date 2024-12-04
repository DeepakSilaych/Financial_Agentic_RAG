from langchain_core.prompts import ChatPromptTemplate
from utils import log_message
import state
from llm import llm
from langchain_core.tools import tool
from state import Value, Give_Output
from .calculator import execute_task_and_get_result

# ----------------- prompts -----------------#

is_visualizable_prompt = """
You are an intelligent assistant specialized in analyzing financial documents.
Your task is to analyze input financial text data and determine if insights and charts can be generated.

Here are some examples to guide you:

Example 1:
Input: "What was the annual revenue growth rate for 2023?" Output: True
Reason: The input data contains numerical data that can be used to generate a chart or insight related to revenue growth.

Example 2:
Input: "What are the risks associated with the new product line in 2023?" Output: False
Reason: The input data is qualitative and cannot be directly visualized in charts or insights.

Now, analyze the input and return True if insights or charts can be generated or False if not.

#### OUTPUT ####
Always return the output in the following format:
Output: <True/False>
Reason: <Brief explanation for the decision>
"""

get_metrics_prompt = """
You are a financial data expert tasked with generating 3 financial metrics which can give some insights to the use, based on a given description of financial data. For each data description, ensure the following: 

########
Important: Never generate or invent data that is not explicitly mentioned in the provided description. Only use the exact data mentioned by the user. If the description lacks specific data (such as numerical values or clear categories), do not attempt to fill in gaps or create assumptions. 
Note that you need to provide all the data required to calculate the corresponding metric.
Choose the metric from which a singular numerical value could be calculated.
You will be penalised if you generate a lot of metrics which are not helpful for a financial analyst.
########


#### Guidelines ####
1. **"metric_name"**:
   - Represents the **name of the identified metric**.
   - The name should be **clear** and **relevant** to the calculation being performed.
2. **"metric_description"**:
   - Represents a **task description** based on the data required for the metric calculation.
   - The description should be **clear, concise**, and directly related to the specific calculation to be performed.
   - Focus on how the **identified metric** should be calculated using the given data.
3. **"data_required"**:
   - Takes **only the data provided by the user**—**do not generate or invent data**.
   - The data should be presented in a **single string**, listing all relevant values required for the metric calculation.
   - The format should be **consistent** and **precise**, detailing all data points clearly.


Here are some examples to guide you:
Input:
- Microsoft reported a profit of 2.1 billion dollars in 2020, 0.8 billion dollars in 2021, and 15 billion dollars in 2022.
- Amazon posted a profit of 5.1 billion dollars in 2020, 1.9 billion dollars in 2021, and 22 billion dollars in 2022.
Output:
{{
    "output": [
        {{
            "metric_name": "Profit Growth Rate",
            "metric_description": "This metric calculates the year-over-year growth rate of profit for a company.",
            "data_required": "Microsoft 2020 Profit: 2.1 billion dollars, Microsoft 2021 Profit: 0.8 billion dollars, Microsoft 2022 Profit: 15 billion dollars, Amazon 2020 Profit: 5.1 billion dollars, Amazon 2021 Profit: 1.9 billion dollars, Amazon 2022 Profit: 22 billion dollars"
        }},
        {{
            "metric_name": "Average Profit Comparison",
            "metric_description": "This metric calculates the average profit for Microsoft and Amazon over the years 2020-2022.",
            "data_required": "Microsoft 2020 Profit: 2.1 billion dollars, Microsoft 2021 Profit: 0.8 billion dollars, Microsoft 2022 Profit: 15 billion dollars, Amazon 2020 Profit: 5.1 billion dollars, Amazon 2021 Profit: 1.9 billion dollars, Amazon 2022 Profit: 22 billion dollars"
        }}
    ]
}}

#### OUTPUT ####
Return a dictionary which should contain the following keys:

{{
    "output": [
        {{
            "metric_name": <Name of Metric>,
            "metric_description": <Description of Metric>,
            "data_required": <Data Required>
        }},
        {{
            ...
         }},
         ...
    ]
}}
    
"""

get_metrics_value_prompt = """
You are given with a metric name and it's description and the data required to calculate the metric.
You are required to calculate the value of the metric using the calculator tool.
give your output in JSON format with keys as metric name and value as their calculated value.
"""

get_insights_prompt = """
You are a Financial Insight Generator and generate useful and meaningful insights for financial analysts. Keep the Insights short and precise making it easier to understand. 

########
Important: Never generate or invent data that is not explicitly mentioned in the provided description. Only use the exact data mentioned by the user. If the description lacks specific data (such as numerical values or clear categories), do not attempt to fill in gaps or create assumptions. 
You will be peanalised to generate long insights which are difficult to analyse or read by financial analyst.
########

Given the following financial data for [metric_name] and its value, along with the input data, generate insights without calculating new values. The insight should be based solely on the provided data. Also, provide a grade from 1 to 5, where 5 represents the most useful insight for a financial analyst.

Data:
Metric Name: [metric_name]
Metric Value: [value]
Input Data: [Entire input data]

Task:
Analyze the relationship between [metric_name] and the provided input data.
Highlight trends, anomalies, correlations, or any patterns that can be derived from the given data.
Assess the usefulness of this insight for a financial analyst and assign a grade based on its value in guiding investment decisions or financial strategies.

Output:
{{
    Insight: [Generated financial insight],
    Grade: [Grade from 1 to 5]
}}

"""

get_charts_name_prompt = """
You are a financial data visualization expert tasked with generating 2 chart titles, each paired with the most appropriate chart type and a reason for its selection, based on a given description of financial data. For each data description, ensure the following: 

########
Important: Never generate or invent data that is not explicitly mentioned in the provided description. Only use the exact data mentioned by the user. If the description lacks specific data (such as numerical values or clear categories), do not attempt to fill in gaps or create assumptions. 
You will be penalised if you generate a lot of charts which are not helpful for a financial analyst.
########

########
Note:  The number of charts given to you are maximum number of charts to generate do not exceed them in any case. Limit your output to chart title and type which are relevant to given data. DO NOT try to create or generate data that is not explicitly mentioned in the provided description just for generating the specified number of charts. 
******
Generate a graph title that incorporates all relevant information provided by the user, ensuring the title fully reflects the data being presented. Avoid using partial details that could lead to repetitive or generic titles. The title should be accurate, informative, and directly aligned with the content of the graph, capturing the key elements such as the data type, time period, and categories being compared
########

**Chart Types and Use Cases:**

### **Bar Charts**
- **Best for**: Comparing financial categories (e.g., revenue, profit, expenses) across companies or years, ranking data, or displaying discrete financial data points.
- **Required**: Categories (such as company names or financial metrics) and corresponding numeric values (e.g., revenue or profit figures).
- **Use case example**: Comparing annual revenue of different companies.

### **Line Charts**
- **Best for**: Displaying financial trends over time, analyzing time series data (e.g., stock prices, market indices), or tracking continuous financial metrics.
- **Required**: A time-based x-axis (e.g., months, quarters, or years) and numeric y-values (e.g., price or returns).
- **Use case example**: Showing stock price changes over the last year.

### **Pie Charts**
- **Best for**: Visualizing proportions or part-to-whole relationships in financial data (e.g., market share or expense breakdown).
- **Use sparingly**: Only for clear proportional data where the parts significantly contribute to the whole.
- **Use case example**: Showing the percentage share of different expense categories in a company's budget.

Here are some examples to guide you:
Input:
Text description: Microsoft reported a profit of 2.1 billion dollars in 2020, 0.8 billion dollars in 2021, and 15 billion dollars in 2022. Amazon, on the other hand, posted a profit of 5.1 billion dollars in 2020, 1.9 billion dollars in 2021, and 22 billion dollars in 2022. For Apple, the revenues are 2.1, 2.5, 2.8, and 3.3 billion dollars across four quarters. Google’s revenues are 3.4, 2.5, 4.8, and 10.3 billion dollars for the year 2021. 
Output:
{{
    data : 
        [
        {{
            "title": "Profit Comparison Between Microsoft and Amazon (2020-2022)",
            "type": "Line Chart",
            "reason": "Line charts are best for showing trends over time, such as the profit changes of companies over the years."
        }},
        {{
            "title": "Quarterly Revenue Comparison for Apple and Google (2020-2022)",
            "type": "Bar Chart",
            "reason": "Bar charts are ideal for comparing discrete categories like revenues across different quarters for multiple companies."
        }},
        ]
}}

#### OUTPUT ####
Return a dictionary which should contain the following keys:

{{
    data : 
        [{{
            "title": <title>,
            "type": <"Line Chart" or "Bar Chart" or "Pie Chart">,
            "reason": <reason>
        }},{{
            "title": <title>,
            "type": <"Line Chart" or "Bar Chart" or "Pie Chart">,
            "reason": <reason>
        }}
        <Other title with graph ONLY if required>
        ]
}}
"""

get_bar_chart_prompt = """
You are a financial data visualization expert. Your task is to generate charts to visualize the data based on a given text description of financial data. The chart title is given as {title}, and you should use this title to accurately visualize the financial information provided.

########
Important: Never generate or invent data that is not explicitly mentioned in the provided description. Only use the exact data mentioned by the user. If the description lacks specific data (such as numerical values or clear categories), do not attempt to fill in gaps or create assumptions.
########

########
Note:  Limit your output data from given data which are relevant to this TITLE: {title}. DO NOT try to create or generate data that is not explicitly mentioned in the provided description just for generating the specified number of charts.
******
* Do not automatically generate x-axis values as 1, 2, 3, ... unless explicitly specified by the user.
* Always take the x-axis and y-axis values directly from the user input.
* Ensure that the data provided for both the x-axis and y-axis is used exactly as provided by the user for generating the chart.
########

Here are some examples to guide you:

Example 
Title: Comparison of Microsoft and Amazon across Profit
Text description: Microsoft reported a profit of 2.1 billion dollars in 2020, 0.8 billion dollars in 2021, and 15 billion dollars in 2022. Amazon, on the other hand, posted a profit of 5.1 billion dollars in 2020, 1.9 billion dollars in 2021, and 22 billion dollars in 2022. For Apple, the revenues are 2.1, 2.5, 2.8, and 3.3 billion dollars across four quarters. Google’s revenues are 3.4, 2.5, 4.8, and 10.3 billion dollars for the year 2021. 
Output:
{{
"type": "Bar Chart",
"data": {{
    "microsoft": [[2020, 2.1], [2021, 0.8], [2022, 15]],
    "amazon": [[2020, 5.1], [2021, 1.9], [2022, 22]]
}},
"x_labels": ["Years"],
"y_label": "Profit (in billion $)",
"title": "Comparison of Microsoft and Amazon across Profit"
}}

########
Important notes:
- **x** and **y** values must be of type **float**.
- The `data` dictionary should contain company names as keys and their associated data in a list of tuples 
- The list format is strictly `("x_value", "y_value")` where `x_value` and `y_value` are both **float** types.
- Make sure the **x_label**, **y_label**, and **title** are strings.
- The final dictionary must match the format exactly as shown.
########

#### OUTPUT ####
Return a dictionary which should contain the following keys:
{{
"type": "Bar Chart",
"data": {{
    <company name>: <List of x,y lists>,
}},
"x_label" : <x_label>,
"y_label" : <y_label>,
"title" : <title>
}}
"""

get_line_chart_prompt = """
You are a financial data visualization expert. Your task is to generate charts to visualize the data based on a given text description of financial data. The chart title is given as {title}, and you should use this title to accurately visualize the financial information provided.

########
Important: Never generate or invent data that is not explicitly mentioned in the provided description. Only use the exact data mentioned by the user. If the description lacks specific data (such as numerical values or clear categories), do not attempt to fill in gaps or create assumptions.
******
* Do not automatically generate x-axis values as 1, 2, 3, ... unless explicitly specified by the user.
* Always take the x-axis and y-axis values directly from the user input.
* Ensure that the data provided for both the x-axis and y-axis is used exactly as provided by the user for generating the chart.
########


Here are some examples to guide you:

Example 
Title: Apple's Quarterly Revenue vs Google's Quarterly Revenue
For Apple, the revenues are 2.1, 2.5, 2.8, and 3.3 billion dollars across four quarters. Google’s revenues are 3.4, 2.5, 4.8, and 10.3 billion dollars for the year 2021. 
Output:
{{
"type": "Line Chart",
"data": {{
    "apple": [[1, 2.1], [2, 2.5], [3, 2.8], [4, 3.3]],
    "google": [[1, 3.4], [2, 2.5], [3, 4.8], [4, 10.3]]
}},
"x_label" : "Quarters",
"y_label" : "Revenue(in billion $)",
"title" : "Apple's Quarterly Revenue vs Google's Quarterly Revenue"
}}

########
Important notes:
- **x** and **y** values must be of type **float**.
- The `data` dictionary should contain company names as keys and their associated data in a list of tuples 
- The list format is strictly `("x_value", "y_value")` where `x_value` and `y_value` are both **float** types.
- Make sure the **x_label**, **y_label**, and **title** are strings.
- The final dictionary must match the format exactly as shown.
########

#### OUTPUT ####
Return a dictionary which should contain the following keys:
{{
"type": "Line Chart",
"data": {{
    <company name>: <List of x,y lists>,
}},
"x_label" : <x_label>,
"y_label" : <y_label>,
"title" : <title>
}}
"""

get_pie_chart_prompt = """
You are a financial data visualization expert. Your task is to generate charts to visualize the data based on a given text description of financial data. The chart title is given as {title}, and you should use this title to accurately visualize the financial information provided.

########
Important: Never generate or invent data that is not explicitly mentioned in the provided description. Only use the exact data mentioned by the user. If the description lacks specific data (such as numerical values or clear categories), do not attempt to fill in gaps or create assumptions.
########

Here are some examples to guide you:

Example 
Title: Company's revenue stream from different geographical location
Text description: "The company has a diverse revenue stream with the majority of sales coming from its North American market (50%), followed by Europe (30%) and Asia (20%) 
Output:
{{
"type": "Pie Chart",
"labels": ["North America", "Europe", "Asia"],
"values": [50, 30, 20]
"title" : "Company's revenue stream from different geographical location"
}}

########
Important notes:
- **values** and **labels** must be of type **list** of same size
- A element of **values**  must be of type **float**
- A element of **labels**  must be of type **str**
- Make sure the **title** are strings.
- The final dictionary must match the format exactly as shown.
########

#### OUTPUT ####
Return a dictionary which should contain the following keys:
{{
"type": "Pie Chart",
"labels": <List of Labels>,
"values": <List of Values>,
"title" : <title>
}}
"""


# ----------------- llm -----------------#

llm_bool = llm.with_structured_output(state.Visualizable)
llm_metrics_structured = llm.with_structured_output(state.Metrics)
llm_insights_structured = llm.with_structured_output(state.Insights)
llm_gen_charts_structured = llm.with_structured_output(state.GenCharts_instructions)
llm_code_structured = llm.with_structured_output(state.CodeFormat)
llm_gen_charts_name_structured = llm.with_structured_output(state.Chart_Name_data)
get_bar_chart_structured  = llm.with_structured_output(state.BarChart)
get_line_chart_structured  = llm.with_structured_output(state.LineChart)
get_pie_chart_structured  = llm.with_structured_output(state.PieChart)

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
    #2sec to exec
    response = is_visualizable_route.invoke({"input": state["input_data"]})
    return {"is_visualizable": response}

def get_metrics(state: state.VisualizerState):
    log_message("--- GET METRICS ---")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", get_metrics_prompt),
            ("user", "Here is the input data: {input}"),
        ]
    )
    metrics_descriptor = prompt | llm_metrics_structured
    #8sec to exec
    response = metrics_descriptor.invoke({"input": state["input_data"]})
    return {"metrics": response.output}

def get_metric_value(state: state.Metric_Value):
    log_message("--- GET METRIC VALUE ---")
    task = f"""
        Given the following details:

        - **Metric Name**: {state["metric"].metric_name}
        - **Metric Description**: {state["metric"].metric_description}
        - **Data Required**: {state["metric"].data_required}

        Calculate the value of the metric using the provided data and return the result.
        """
    #3sec * 6
    answer = execute_task_and_get_result(task)['answer']
    return_ans = Value()
    if isinstance(answer, float) or isinstance(answer, int):
        return_ans.name_of_the_metric = state["metric"].metric_name
        return_ans.value = answer
        ans = get_insights(state["metric"].metric_name, answer, state["input_data"])
        return {"values": [return_ans], "final_insights" : ans["final_insights"]}
    return {"values": [return_ans], "final_insights" : [""]}

def get_insights(metric_name, metric_value, input_data):
    log_message("--- GET INSIGHTS ---")
    prompt_for_insight = f"""
        Given the following details:
        - **Metric Name**: {metric_name}
        - **Metric Value**: {metric_value}
        - **All the data**: {input_data}
        """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", get_insights_prompt),
            ("user", prompt_for_insight)
        ]
    )
    insights_generator = prompt | llm_insights_structured
    if(metric_name == ""):
        {"final_insights" : [""]} 
    response = insights_generator.invoke(
                    {
                        "input_data": input_data,
                        "metric_name": metric_name,
                        "metric_value": metric_value,
                    }
                )
    if(response.grade<=2):
        return {"final_insights" : [""]}        
    return {"final_insights" : [response.insights]}

def get_final_insights(state: state.VisualizerState):
    final_answer = state["final_insights"]
    prompt_for_final_answer = "The following insights have been noted, listed in no particular order:\n"
    prompt_for_final_answer += '\n'.join([f"{i+1}. {final_answer[i]}" for i in range(len(final_answer))])
    prompt_for_summary = """
    Extract the key points from the following insights, focusing on results that are important for financial analysis. Present them in a concise and easy-to-read bullet point format. If multiple insights convey similar information, or if they are sequential or imply each other, combine them into a single point. Avoid repeating similar information or stating redundant points. Ensure each point is based only on the provided data, with no additional generation or assumptions. Make the key points clear, distinct, and straightforward to help quickly grasp the essential insights, emphasizing the financial outcomes and implications.
  """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_for_summary),
            ("user", prompt_for_final_answer)
        ]
    )
    #5sec
    final_answer_generator = prompt | llm.with_structured_output(Give_Output)
    result = final_answer_generator.invoke({})
    return {"final_output":result.output}

def get_charts_name(state: state.VisualizerState):
    log_message("--- GENERATING CHART NAMES ---")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", get_charts_name_prompt),
            ("user", "Here is the input data: {input_data}")
        ]
    )
    chart_name_generator = prompt | llm_gen_charts_name_structured
    #2sec
    response = chart_name_generator.invoke({"input_data": state["input_data"]})
    return {"chart_names": response.data}

def get_charts_data(state: state.Chart_Name_for_data):
    log_message("--- GET CHARTS DATA ---")
    prompt = ""
    structured = ""
    if (state["state"].type == "Bar Chart"):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", get_bar_chart_prompt),
                ("user", "Here is the input data: {input_data}")
            ]
        )
        structured = get_bar_chart_structured

    elif (state["state"].type == "Line Chart"):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", get_line_chart_prompt),
                ("user", "Here is the input data: {input_data}")
            ]
        )
        structured = get_line_chart_structured
    else:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", get_pie_chart_prompt),
                ("user", "Here is the input data: {input_data}")
            ]
        )
        structured = get_pie_chart_structured
        
    generator = prompt | structured
    try:
        #2.6sec * 2
        response = generator.invoke({"input_data": state["input_data"], "title" : state["state"].title})
    except:
        response = ""
    return {"charts": [response]}

