from dotenv import load_dotenv

load_dotenv()

import json
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel
from llm import llm

NUM_KPIS = 8


class KPIDescription(BaseModel):
    kpi: str
    description: str
    values_need_in_formula: list[str]
    formula: str


class KPIDescriptionOutput(BaseModel):
    kpis: list[KPIDescription]


kpis_describer_prompt = ChatPromptTemplate.from_template(
    """
You are a financial analyst.
You have been given some key performance indices on the topic {topic}:
{kpis}
You have to give the description of each of the KPIs and the values needed to calculate each of them.
"""
)
kpis_describer = kpis_describer_prompt | llm.with_structured_output(
    KPIDescriptionOutput
)


class KPISelectionOutput(BaseModel):
    kpis: list[str]


kpis_selector_prompt = ChatPromptTemplate.from_template(
    """
You are a financial analyst.
You have been given some key performance indices on the topic {topic}:
{kpis}
You have to choose 5 KPIs from them. Choose the most important ones.
"""
)
kpis_selector = kpis_selector_prompt | llm.with_structured_output(KPISelectionOutput)


def get_kpis_descriptions(topic: str, kpis: list[str]):
    selected_kpis = kpis_selector.invoke({"topic": topic, "kpis": kpis}).kpis
    if len(selected_kpis) >= NUM_KPIS:
        selected_kpis = selected_kpis[:NUM_KPIS]

    res = kpis_describer.invoke({"topic": topic, "kpis": selected_kpis})
    with open(f"kpis/{topic}.json", "w") as f:
        return json.dump(res.model_dump(), f)


with open("kpis.json", "r") as f:
    kpis = json.load(f)

for kpi in kpis:
    get_kpis_descriptions(kpi["topic"], kpi["kpis"])
