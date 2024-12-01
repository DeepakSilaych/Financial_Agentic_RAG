from typing import Optional
import json
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import state
from llm import llm
from retriever import retriever
from nodes.calculator import execute_task_and_get_result
from nodes.missing_reports import company_year_extractor


class Value(BaseModel):
    company_name: str
    year: Optional[str]
    key: str
    value: Optional[str]


get_required_value_prompt = ChatPromptTemplate.from_template(
    """You are a financial analyst. You have been given the task to answer the following question: {question}.

# Instructions
1. You should extract the required information from the given documents and provide the answer.
2. Make sure the answer is only from the documents provided.
3. Make sure the numbers are not written as words.
   Eg. Write 1000 instead of one thousand, 1000000 instead of one million.
4. Also don't use any commas in the numbers.
5. If the answer is not present in the documents, give None in the `value` field.

You are given the following documents:
{docs}
"""
)

value_llm = get_required_value_prompt | llm.with_structured_output(Value)


def _get_required_value(input: dict[str, str]):
    question = f"What is the {input['key']} for {input['company_name']} in the year {input['year']}?"
    docs = retriever.similarity_search(question)
    res = value_llm.invoke({"question": question, "docs": docs})

    return Value(
        company_name=input["company_name"],
        year=input["year"],
        key=input["key"],
        value=res.value,
    )


def get_required_kpis(state: state.OverallState):
    analyses_to_be_done = state["analyses_to_be_done"]  # filled in by query clarifier

    kpis = []
    for analysis in analyses_to_be_done:
        with open(f"experiments/kpis/kpis/{analysis}.json") as f:
            _kpis = json.load(f)["kpis"]
        kpis.extend(_kpis)

    company_year_pairs = company_year_extractor.invoke(
        {"query": state["question"]}
    ).company_year_pairs

    analyses_kpis = []
    for company_year_pair in company_year_pairs:
        company_name = company_year_pair.company_name
        year = company_year_pair.filing_year
        analyses_kpis.append(
            {
                "company_name": company_name,
                "year": year,
                "kpis": kpis,
            }
        )

    return {
        "analyses_kpis_by_company_year": analyses_kpis,
    }


def get_required_values(state: state.OverallState):
    kpis_by_company_year = state["analyses_kpis_by_company_year"]

    required_values = []
    for kpi in kpis_by_company_year[0]["kpis"]:  # type: ignore
        required_values.extend(kpi["values_need_in_formula"])
    required_values = list(set(required_values))

    company_year_pairs = [
        (kpi["company_name"], kpi["year"]) for kpi in kpis_by_company_year
    ]

    inputs = []
    for required_value in required_values:
        for company_year_pair in company_year_pairs:
            inputs.append(
                {
                    "key": required_value,
                    "company_name": company_year_pair[0],
                    "year": company_year_pair[1],
                }
            )

    with ThreadPoolExecutor() as executor:
        values = list(
            executor.map(
                lambda inp: _get_required_value(inp),
                inputs,
            )
        )

    for value in values:
        if value.value is None:
            for kpis in kpis_by_company_year:
                if (
                    kpis["company_name"] == value.company_name
                    and kpis["year"] == value.year
                ):
                    kpis["kpis"] = list(
                        filter(
                            lambda kpi: value.key not in kpi["values_need_in_formula"],
                            kpis["kpis"],
                        )
                    )

    return {
        "analyses_values": [
            {
                "key": value.key,
                "value": value.value,
                "company_name": value.company_name,
                "year": value.year,
            }
            for value in values
            if value.value is not None and value.value != "None"
        ],
        "analyses_kpis_by_company_year": kpis_by_company_year,
    }


def calculate_kpis_for_company_year(kpis, values, company_name, year):
    if len(kpis) == 0:
        return {
            "company_name": company_name,
            "year": year,
            "calculated_kpis": {},
        }

    formulae = "\n".join(
        [f"{i+1} => {kpi['kpi']}: {kpi['formula']}" for i, kpi in enumerate(kpis)]
    )
    values = "\n".join(
        [
            f"{value['key']}: {value['value']}"
            for value in values
            if value["company_name"] == company_name and value["year"] == year
        ]
    )

    task = f"""
Calculate the following KPIs using the given formula:
{formulae}

Use these values for the calculation:
{values}
"""

    calculated_kpis = execute_task_and_get_result(task)["answer"]

    # If only one KPI is calculated, it is returned as a string. Convert it to a dictionary.
    if not isinstance(calculated_kpis, dict):
        calculated_kpis = {kpis[0]["kpi"]: calculated_kpis}

    return {
        "company_name": company_name,
        "year": year,
        "calculated_kpis": calculated_kpis,
    }


def calculate_kpis(state: state.OverallState):
    kpis_by_company_year = state["analyses_kpis_by_company_year"]

    with ThreadPoolExecutor() as executor:
        results = list(
            executor.map(
                lambda kpi: calculate_kpis_for_company_year(
                    kpi["kpis"],
                    state["analyses_values"],
                    kpi["company_name"],
                    kpi["year"],
                ),
                kpis_by_company_year,
            )
        )

    return {
        "analyses_kpis_by_company_year_calculated": results,
    }


generate_answer_from_kpis_prompt = ChatPromptTemplate.from_template(
    """You are a financial analyst. You have been given the task to answer the following question: {question}.

# Instructions
1. Some useful KPIs have already been calculated. The values are obtained from the company's financial statements. You should use the KPIs to appropriately answer the question.
2. Make sure the answer contains all the necessary numbers and information.
3. Make sure that you don't provide any unnecessary information.
4. Make sure that you don't use any facts that are not provided/inferred from the given KPIs.

NOTE: You will be strictly punished if you provide any information that is not provided or cannot be inferred from the information provided.

Here are the KPIs calculated for the companies:
{kpis}

"""
)
_generate_answer_from_kpis = generate_answer_from_kpis_prompt | llm | StrOutputParser()


def generate_answer_from_kpis(state: state.OverallState):
    kpis = ""
    for kpi_by_company_year in state["analyses_kpis_by_company_year_calculated"]:
        if kpi_by_company_year["calculated_kpis"] == {}:
            continue

        kpis += f"Company Name: {kpi_by_company_year['company_name']}"
        if kpi_by_company_year["year"] is not None:
            kpis += f"\tYear: {kpi_by_company_year['year']}"
        kpis += "\n"
        kpis += "\n".join(
            [
                f"{kpi}: {value}"
                for kpi, value in kpi_by_company_year["calculated_kpis"].items()
            ]
        )
        kpis += "\n\n"

    res = _generate_answer_from_kpis.invoke(
        {
            "question": state["question"],
            "kpis": kpis,
        }
    )

    return {
        "final_answer": res,
    }
