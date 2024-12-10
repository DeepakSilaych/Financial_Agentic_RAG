from datetime import datetime
import config
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
from workflows.gen_critic_rag import generator_critic as app
from workflows.kpi import kpi_workflow
import sys


initial_input = {
    "question": "In the fiscal year 2023, what was the total amount of cash that EA (Electronic Arts) returned to shareholders in the form of dividends, and what was Apple's quarterly cash dividend per share as of September 30, 2023, as reported in their respective 10-K documents and reports?"
}

res = app.invoke(initial_input)

print(res["final_answer"])

print(f"\nFinal Answer : {res}\n")

"""
SERIES PARALLEL
'final_answer_with_citations': "In the fiscal year 2023, Electronic Arts (EA) returned a total of $202 million to shareholders in the form of dividends, according to their 10-K filing [[1/goog-10-k-2023.pdf/Page 45/data/goog-10-k-2023.pdf]]. This reflects EA's ongoing commitment to returning value to its investors through consistent dividend payments [[2/goog-10-k-2023.pdf/Page 46/data/goog-10-k-2023.pdf]].\n\nAs for Apple Inc., as of September 30, 2023, the company declared a quarterly cash dividend of $0.24 per share [[3/apple-financial-report-2023.pdf/Page 22/data/apple-financial-report-2023.pdf]]. This dividend reflects Apple's strategy to provide returns to shareholders while maintaining a strong financial position, as indicated in their financial reports [[4/apple-financial-report-2023.pdf/Page 23/data/apple-financial-report-2023.pdf]].\n\nTogether, these figures illustrate the different approaches both companies take in rewarding th
"""

"""
SIMPLE PARALLEL 
In the fiscal year 2023, Electronic Arts (EA) returned a total of $246 million to shareholders through dividends. This reflects EA's ongoing commitment to returning value to its shareholders amidst a competitive gaming industry landscape.        

On the other hand, Apple reported a quarterly cash dividend of $0.24 per share as of September 30, 2023. This amount showcases Apple's consistent strategy of providing regular returns to its investors, reinforcing its position as a major player in the technology sector.

Both companies exhibit a strong commitment to shareholder returns, albeit in different magnitudes and contexts, highlighting the importance of dividends as a component of total shareholder return.
"""