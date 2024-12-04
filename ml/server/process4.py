from dotenv import load_dotenv
import os

load_dotenv()
from utils import log_message, visualize_workflow
import config
# from workflows.series_parallel import final_workflow as app
from workflows.post_processing import visual_workflow as visual_workflow_app
from workflows.rag_e2e import rag_e2e as app
import time

####### Debugging ####

# initial_input = {
# #     # "question": "In the 2023 financial reports of Alphabet Inc., the parent company of Google, what specific factors led to the growth in Google Services' operating income and what percentage did Google Cloud revenues increase by during the same year? Please provide insights into the overall financial performance and strategic developments that drove these results, as outlined in the company's 10-K documents for the year 2023."
# #     # "question": "How does google utilize financial instruments to manage foreign currency risks across different aspects of its operations, and what specific strategies or tools are implemented to mitigate the impact of fluctuations in exchange rates?"
# #     # "question": "What was the Total Demand creation expense for NIKE for year ending May 31, 2023"
# #     # "question": "How many employees did apple have globally as of June 30, 2023?"
# #     "question": "What was the effective tax rate for Apple in 2023?"
# #     # "question": "What were some significant announcements made by Apple in the first quarter of 2023?"
# #     # "question": "What are the key software-enabled services General Motors(GM)  offers in its vehicles in 2023?"
#     "question": "What were Apple's total employee count and why it is small?"
# }

# res = app.invoke(initial_input)
# answer = {"input_data":res['answer']}
# print(answer)

answer = {"input_data":"From September 2018 to September 2023, Apple Inc. saw its value increase from $100 in September 2018 to $317 in September 2023. Over the same period, the S&P 500 Index grew from $100 in September 2018 to $160 in September 2023, while the Dow Jones U.S. Technology Supersector Index rose from $100 in September 2018 to $226 in September 2023. In September 2019, Apple’s value was $98, compared to the S&P 500 Index at $104 and the Dow Jones U.S. Technology Supersector Index at $105. By September 2020, Apple’s value had surged to $204, while the S&P 500 Index reached $118 and the Dow Jones U.S. Technology Supersector Index increased to $154. In September 2021, Apple’s value continued to rise to $269, with the S&P 500 Index at $161 and the Dow Jones U.S. Technology Supersector Index at $227. By September 2022, Apple had reached $277, while the S&P 500 Index had decreased to $136 and the Dow Jones U.S. Technology Supersector Index stood at $164."}
visualize_workflow(visual_workflow_app)

vis = visual_workflow_app.invoke(answer)
import json
import state
# Function to serialize Pydantic models or plain objects
def serialize_obj(obj):
    if isinstance(obj, state.BaseModel):  # Check if it's a Pydantic model
        return obj.dict()  # Convert Pydantic model to dictionary
    return obj  # Return as-is for non-Pydantic models

# Print the variables in a pretty format
print("is_visualizable:", json.dumps(serialize_obj(vis.get("is_visualizable", {})), indent=4))
for idx,i in enumerate(vis.get("metrics", [])):
    print(f"metrics {idx}:")
    for attr, value in vars(i).items():
        print(f"{attr} : {value}")
print()

for idx,i in enumerate(vis.get("values", [])):
    print(f"values {idx}:")
    for attr, value in vars(i).items():
        print(f"{attr} : {value}")
print()

for idx,i in enumerate(vis.get("final_insights", [])):
    print(f"insights: {idx}", json.dumps(serialize_obj(i), indent=4))
print()


print("final_output:", vis.get("final_output", {}))
print()

for idx,i in enumerate(vis.get("chart_names", [])):
    print(f"chart_names {idx}:")
    for attr, value in vars(i).items():
        print(f"{attr} : {value}")
print()

for idx,i in enumerate(vis.get("charts", [])):
    print(f"charts {idx}:")
    for attr, value in vars(i).items():
        print(f"{attr} : {value}")
    

exit(0)

######################
# Debug to plot
import os
import matplotlib.pyplot as plt
from state import BarChart, LineChart, PieChart, Chart  # Assuming these are imported from your state management library
import numpy as np
# Function to create a "chart" directory if it doesn't exist
def create_chart_folder():
    if not os.path.exists("chart"):
        os.makedirs("chart")

# Function to save BarChart as an image
# Function to save BarChart as an image (side-by-side bars for multiple companies)

# Function to save BarChart as an image (side-by-side bars for multiple companies)
# Function to plot the bar chart
def save_bar_chart(chart: BarChart, file_name: str):
    # Create a figure and axis
    plt.subplots(figsize=(10, 6))

    # Extract all years from the data (to make sure we have all unique years)
    all_years = set()
    for company in chart.data:
        all_years.update([entry[0] for entry in chart.data[company]])

    all_years = sorted(list(all_years))  # Sort the years for proper x-axis placement
    num_years = len(all_years)
    
    # Define the bar width and the positions for each group
    bar_width = 0.15
    x_positions = np.arange(num_years)

    # Plot each company's data
    for idx, (company, values) in enumerate(chart.data.items()):
        # Create a dictionary for fast lookups for each company
        year_value_map = dict(values)
        company_values = [year_value_map.get(year, 0) for year in all_years]  # Default to 0 if no value for the year

        # Shift the bars slightly based on the index
        plt.bar(x_positions + (idx - len(chart.data) / 2) * bar_width, 
               company_values, 
               width=bar_width, 
               label=company)

    # Set labels and title
    plt.xlabel(chart.x_label)
    plt.ylabel(chart.y_label)
    plt.title(chart.title)

    # Add a legend
    plt.legend()

    # Show the p
    
    # Save the plot as PNG in the "chart" folder
    plt.savefig(f"chart/{file_name}.png")
    plt.close()

# Function to save LineChart as an image
def save_line_chart(chart: LineChart, file_name: str):
    plt.figure(figsize=(10, 6))
    for label, values in chart.data.items():
        x = [v[0] for v in values]  # Extract x values
        y = [v[1] for v in values]  # Extract y values
        plt.plot(x, y, label=label)
    plt.xlabel(chart.x_label)
    plt.ylabel(chart.y_label)
    plt.title(chart.title)
    plt.legend()
    plt.savefig(f"chart/{file_name}.png")  # Save as PNG in "chart" folder
    plt.close()

# Function to save PieChart as an image
def save_pie_chart(chart: PieChart, file_name: str):
    plt.figure(figsize=(6, 6))
    plt.pie(chart.values, labels=chart.labels, autopct='%1.1f%%', startangle=90)
    plt.title(chart.title)
    plt.savefig(f"chart/{file_name}.png")  # Save as PNG in "chart" folder
    plt.close()

# Function to save all charts in the Chart object
def save_charts(chart_object: Chart):
    create_chart_folder()  # Create chart directory if it doesn't exist
    for i, c in enumerate(chart_object):
        file_name = f"chart_{i + 1}"  # Use unique file names for each chart
        if isinstance(c, BarChart):
            save_bar_chart(c, file_name)
        elif isinstance(c, LineChart):
            save_line_chart(c, file_name)
        elif isinstance(c, PieChart):
            save_pie_chart(c, file_name)

# Example usage:
# Assuming `chart_object` is an instance of the `Chart` class with BarChart, LineChart, and PieChart objects
# Save all charts in the "chart" folder
save_charts(vis.get("charts", []))

exit(0)






initial_input = {
    "question": "Compare the Research and Development expenses of Apple and Google and give some figures in your answer too."
}

# Thread
thread = {"configurable": {"thread_id": "1"}}

# Run the graph until the first interruption
for event in app.stream(initial_input, thread, stream_mode="values"):
    print(event)
log_message("---ASKING USER FOR CLARIFICATION---")
state = app.get_state(thread).values
clarifying_questions = state["clarifying_questions"]
clarifications = []

for question in clarifying_questions:
    # log_message("CLARIFYING QUESTION:"+ str(question))
    user_response = input(f"{question}: ")
    clarifications.append(f"{question}: {user_response}")
app.update_state(thread, {"clarifications": clarifications})
for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
    try:
        if event[1]["final_answer"]:
            print(event)
            final_response = event[1]["final_answer"]
            break
    except:
        print(event)

if final_response == "":
    print("No final answer found")
    exit()

thread = {"configurable": {"thread_id": "2"}}
# insights = []
# final_answer_charts = ''
visual_input = {"input_data": final_response}
for event in visual_workflow_app.stream(visual_input, thread, stream_mode="values"):
    print(event)
