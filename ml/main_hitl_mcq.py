from dotenv import load_dotenv
import os

load_dotenv()

from utils import log_message, block_urls
import config
# from workflows.final_workflow_without_hallucinator import final_workflow as app
from workflows.split_path_decider import split_path_decider as app

ques = input("User: ")
# ques = "Compare the RnD activities of Apple and Google, and how do these affect the future outlook of the companies."
initial_input = {
    "question": ques,
    "max_analysts": 3,
    # "analysis_required": "no",
    "fast_vs_slow": "fast",
    "normal_vs_research": "normal",
    "image_path": "./images/image4.png",
    # "image_path": "",
}  # "Compare the Research and Development expenses of Apple and Google"}


# Thread
thread = {"configurable": {"thread_id": "1"}}

# Run the graph until the first interruption
for event in app.stream(initial_input, thread, stream_mode="values"):
    print(app.get_state(thread).next)
    pass
    # print(event.get("path_decided",None))

log_message("---ASKING USER FOR CLARIFICATION---")
try:
    state = app.get_state(thread).values
    clarifying_questions = state["clarifying_questions"]
    clarifications = []
    assert (len(clarifying_questions) != 0)
    for question in clarifying_questions:
        # log_message("CLARIFYING QUESTION:"+ str(question))
        if type(question) == str:
            user_response = input(f"{question}: ")
            clarifications.append(f"{user_response}")
        else:
            idx = list(range(1,len(question['options'])+1))
            options = '\n'.join([f"({i}) {option}" for i, option in zip(idx, question['options'])])
            user_response = input(f"{question['question']}\nOptions:\n{options}\nChoose any option: ")
            user_response = user_response.replace(" ", "").split(',')
            answers = "; ".join([question['options'][int(i)-1] for i in user_response])
            clarifications.append(f"{answers}")
    app.update_state(thread, {"clarifications": clarifications})
    # print("INSIDE 2" + "\n"*5)
    for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
        # print(event)
        print(app.get_state(thread).next)
        pass
except Exception as e:
    print(e)
    print("No Clarifying Questions")
    log_message("---NO CLARIFYING QUESTIONS---")


log_message("---ASKING USER FOR ANALYSIS TYPE QUERY---")
try:
    state = app.get_state(thread).values
    analysis_question = state["analysis_question"]
    if "No Analysis Required" not in analysis_question:
        user_response = input(f"{analysis_question}: ")
        app.update_state(thread, {"user_response_for_analysis": user_response})
    else:
        log_message("---NO ANALYSIS QUESTIONS---")
    for event in app.stream(None, thread, stream_mode="values", subgraphs=True):
        # print(event)
        print(app.get_state(thread).next)
        pass
except Exception as e:
    print(e)
    print("No Analysis Questions")
    log_message("---NO ANALYSIS QUESTIONS---")

        
if (config.WORKFLOW_SETTINGS["with_site_blocker"]):
    try:
        for task in app.get_state(thread, subgraphs=True).tasks:
            # print(task)
            # print(task.state.values)
            try:
                state = task.state.values
                urls = state["urls"]
                web_searched = state["web_searched"]
                print("URLS:", urls)
                
                # This will be fetched from the user database
                block_list = ["https://www.researchgate.net/", "https://www.sciencedirect.com/", "https://www.jstor.org/"]
                allow_list = ["https://en.wikipedia.org/"]
                
                query_urls, new_urls = block_urls(urls, block_list, allow_list)
                
                allow = [input(f"Allow {url}? (y/n): ") for url in query_urls]
                
                if "y" in allow:
                    new_urls += [url for url in query_urls if allow[query_urls.index(url)] == "y"]
                    allow_list += [url for url in query_urls if allow[query_urls.index(url)] == "y"]
                else:
                    block_list += [url for url in query_urls if allow[query_urls.index(url)] == "n"]
                    
                # Update allow_list and block_list in the user database
                print("New Allow List:", allow_list)
                print("New Block List:", block_list)
                                
                app.update_state(task.state.config, {"urls": new_urls})
            except Exception as e:
                print(e)
                log_message("This Subgraph has no URLs")
            
        for event in app.stream(None, thread, stream_mode="values"):
            pass
            print(app.get_state(thread).next)
            
    except Exception as e:
        print(e)
        log_message("No Clue How It can ever reach here")


state = app.get_state(thread, subgraphs=True).values
print(state)
print("QUESTION:", state["question"])
print("FINAL ANSWER:", state["final_answer"])
# print(state["combined_citations"])

with open("pipeline_log.txt", "w") as file:
    pass
