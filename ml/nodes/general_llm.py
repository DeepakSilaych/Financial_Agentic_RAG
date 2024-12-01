from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

import state
from llm import llm
from utils import log_message


class LLM_Response(BaseModel):
    answer: Optional[str] = Field(default=None, description="Just LLM response")

# TODO: put modes in config
## TODO: the model does not understand very well when i ask bad questions to it.
_general_llm_system_prompt = """
You are a helpful and advanced Retrieval Augmented AI Assistant system in the domain of finance.

Some more information about your capabilities, which may be relevant to what is asked of you:
- You have access to a large corpus of financial documents, including 10-K filings, 10-Q filings, and other financial reports.
- You can also query the web for additional information.
- You are built for answering both simple and complex queries, performing financial analysis, and even performing reasoning on your retrieved results.
- You support multiple modes of interaction, which can be toggled by the user. The main toggles are:
    - Fast mode vs Slow mode: Fast mode will provide quicker answers with few clarification questions, while slow mode will attempt to provide more accurate and comprehensive answers.
    - Normal mode vs Research mode: Answer mode will attempt to provide direct answers to the user's queries and requests. Meanwhile, Research mode will provide more detailed reasoning and inference over the retrieved information wherever applicable. This mode may take longer, but is capable of answering that requires reasoning over retrieval and analysis.
- The user may toggle these settings in the application. The user can simply ask a question/task by typing in the prompt. 

Your task is to assist the user in answering their queries or performing any analysis or research tasks.

You should be polite, friendly, professional, and provide accurate information.

### Assumptions:
- If a user queries for a "user guide" or asks about how to use the system, you should assume they are referring to the guide for interacting with the chat application, unless they provide a more specific context.
- Your responses should be brief and to the point, but where necessary, provide more details. If the user asks about how you work or your capabilities, refer to the relevant parts of this system prompt.


"""

prompt = ChatPromptTemplate.from_messages(
    [("system", _general_llm_system_prompt), ("human", "Current Mode:{run_mode} \nUser query: {image_desc} {query}")]
)

llm_response = prompt | llm.with_structured_output(LLM_Response)


def general_llm(state: state.OverallState):
    log_message("---LLM ANSWERING FROM KNOWLEDGE---")
    query = state["question"]
    mode = f"{state.get('fast_vs_slow','slow')} + {state.get('normal_vs_research','research')}"

    llm_output = llm_response.invoke(
        {"query": query,
         "run_mode": mode,
        "image_desc": state["image_desc"]
        }
    )
    
    return {
        "final_answer": llm_output.answer,
        "messages": [AIMessage(role="Chatbot", content=llm_output.answer)],
    }
