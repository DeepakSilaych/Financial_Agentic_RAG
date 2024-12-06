from typing import Optional
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import pathway as pw
from pathway.udfs import DiskCache

import state
from llm import llm
from retriever import retriever
from nodes.calculator import execute_task_and_get_result
from utils import send_logs, log_message
import config


class PWValue(pw.Schema):
    company_name: str
    filing_year: str
    key: Optional[str]


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


def retriever_helper(retriever, question, num_docs, filter):
    docs = []
    if filter == "":
        docs = retriever.similarity_search(question, num_docs)
    else:
        docs = retriever.similarity_search(question, num_docs, metadata_filter=filter)
    return docs


@pw.udf(cache_strategy=DiskCache())
def _get_required_value_with_pw(
    company_name: str, year: str, key: str
) -> dict[str, str | Optional[str]]:
    """Retrieve the required value based on the input using quantitative and qualitative logic."""
    question = f"What is the {key} for {company_name} in the year {year}?"

    docs = []
    # metadata_text = "table == `False`"
    # metadata_table = "table == `True`"
    # metadata_kv = "is_table_value == `True`"
    # metadata = {"company_name": input["company_name"], "year": input["year"]}
    # formatted_metadata = nodes.convert_metadata_to_jmespath(
    #     metadata, ["company_name", "year"]
    # )

    # if formatted_metadata:
    #     metadata_text += f" && {formatted_metadata}"
    #     metadata_table += f" && {formatted_metadata}"
    #     metadata_kv += f" && {formatted_metadata}"
    # else:
    #     metadata_text += " && is_table_value == `False`"
    #     metadata_kv += " && table == `False`"
    # if config.WORKFLOW_SETTINGS["with_table_for_quant_qual"]:
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         future_text = executor.submit(
    #             retriever_helper,
    #             retriever,
    #             question,
    #             config.NUM_DOCS_TO_RETRIEVE,
    #             metadata_text,
    #         )
    #         future_table = executor.submit(
    #             retriever_helper,
    #             retriever,
    #             question,
    #             config.NUM_DOCS_TO_RETRIEVE_TABLE,
    #             metadata_table,
    #         )
    #         future_kv = executor.submit(
    #             retriever_helper,
    #             retriever,
    #             question,
    #             config.NUM_DOCS_TO_RETRIEVE_KV,
    #             metadata_kv,
    #         )
    #         docs += future_text.result() + future_table.result() + future_kv.result()
    # else:
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         future_text_table = executor.submit(
    #             retriever_helper,
    #             retriever,
    #             question,
    #             config.NUM_DOCS_TO_RETRIEVE,
    #             formatted_metadata,
    #         )
    #         future_kv = executor.submit(
    #             retriever_helper,
    #             retriever,
    #             question,
    #             config.NUM_DOCS_TO_RETRIEVE_KV,
    #             metadata_kv,
    #         )
    #         docs += future_text_table.result() + future_kv.result()

    # If no docs were retrieved, retrieve again without metadata
    if len(docs) == 0:
        docs += retriever.similarity_search(question, config.NUM_DOCS_TO_RETRIEVE)

    res = value_llm.invoke({"question": question, "docs": docs})

    return {
        "company_name": company_name,
        "year": year,
        "key": key,
        "value": res.value,
    }


def _get_required_value(inp: dict[str, str]):
    table = pw.debug.table_from_rows(
        PWValue, [(inp["company_name"], inp["year"], inp["key"])]
    )
    res = table.select(
        value=_get_required_value_with_pw(
            pw.this.company_name,
            pw.this.filing_year,
            pw.this.key,
        )
    )
    res = list(pw.debug.table_to_dicts(res)[1]["value"].values())[0].as_dict()
    return {
        "company_name": inp["company_name"],
        "year": inp["year"],
        "key": inp["key"],
        "value": res["value"],
    }


def get_required_kpis(state: state.KPIState):
    # log_message(f"---- GETTING REQUIRED KPIs FOR : {analyses_to_be_done}")
    analyses_to_be_done = state["analyses_to_be_done"]  # filled in by query clarifier
    print(
        f"---- GETTING REQUIRED KPIs FOR {len(analyses_to_be_done)} analyses: {analyses_to_be_done}"
    )
    log_message(
        f"---- GETTING REQUIRED KPIs FOR {len(analyses_to_be_done)} analyses: {analyses_to_be_done}",
    )
    kpis = []
    for analysis in analyses_to_be_done:
        with open(f"experiments/kpis/kpis/{analysis.lower()}.json") as f:
            _kpis = json.load(f)["kpis"]
        kpis.extend(_kpis)

    company_year_pairs = state["analysis_companies_by_year"]

    analyses_kpis = []
    for company_year_pair in company_year_pairs:
        company_name = company_year_pair["company_name"]
        year = company_year_pair["filing_year"]
        analyses_kpis.append(
            {
                "company_name": company_name,
                "year": year,
                "kpis": kpis,
            }
        )

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = "get_required_kpis" + "//" + id
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not config.LOGGING_SETTINGS["get_required_kpis"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "analyses_kpis_by_company_year": analyses_kpis,
        "prev_node": child_node,
        "log_tree": log_tree,
    }

    send_logs(
        parent_node=parent_node,
        curr_node=child_node,
        child_node=None,
        input_state=state,
        output_state=output_state,
        text=child_node.split("//")[0],
    )

    # ######

    return output_state


def get_required_values(state: state.KPIState):
    log_message(f"---- GETTING REQUIRED VALUES ----", 1)
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
        if value["value"] is None:
            for kpis in kpis_by_company_year:
                if (
                    kpis["company_name"] == value["company_name"]
                    and kpis["year"] == value["year"]
                ):
                    kpis["kpis"] = list(
                        filter(
                            lambda kpi: value["key"]
                            not in kpi["values_need_in_formula"],
                            kpis["kpis"],
                        )
                    )

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = "get_required_values" + "//" + id
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not config.LOGGING_SETTINGS["get_required_values"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "analyses_values": [
            {
                "key": value["key"],
                "value": value["value"],
                "company_name": value["company_name"],
                "year": value["year"],
            }
            for value in values
            if value["value"] is not None and value["value"] != "None"
        ],
        "analyses_kpis_by_company_year": kpis_by_company_year,
        "prev_node": child_node,
        "log_tree": log_tree,
    }

    send_logs(
        parent_node=parent_node,
        curr_node=child_node,
        child_node=None,
        input_state=state,
        output_state=output_state,
        text=child_node.split("//")[0],
    )

    ######

    return output_state


def calculate_kpis_for_company_year(kpis, values, company_name, year):
    if len(kpis) == 0:
        output_state = {
            "company_name": company_name,
            "year": year,
            "calculated_kpis": {},
        }

    else:
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

        output_state = {
            "company_name": company_name,
            "year": year,
            "calculated_kpis": calculated_kpis,
        }

    # ###### log_tree part
    # # import uuid , nodes
    # id = str(uuid.uuid4())
    # child_node = "calculate_kpis_for_company_year" + "//" + id
    # parent_node = state.get("prev_node" , "START")
    # log_tree = {}
    # log_tree[parent_node] = [child_node]
    # ######

    # ##### Server Logging part

    # if not LOGGING_SETTINGS['calculate_kpis_for_company_year']:
    #     child_node = parent_node

    # send_logs(
    #     parent_node = parent_node ,
    #     curr_node= child_node ,
    #     child_node=None ,
    #     input_state=state ,
    #     output_state=output_state ,
    #     text=child_node.split("//")[0] ,
    # )

    return output_state


def calculate_kpis(state: state.KPIState):
    log_message(f"---- CALCULATING KPIS ----", 1)
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

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = "calculate_kpis" + "//" + id
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not config.LOGGING_SETTINGS["calculate_kpis"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "analyses_kpis_by_company_year_calculated": results,
        "prev_node": child_node,
        "log_tree": log_tree,
    }

    send_logs(
        parent_node=parent_node,
        curr_node=child_node,
        child_node=None,
        input_state=state,
        output_state=output_state,
        text=child_node.split("//")[0],
    )

    ######

    return output_state


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


def generate_answer_from_kpis(state: state.KPIState):
    log_message("---- GENERATING ANSWER FROM KPIS ----")
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

    companies_and_years = list(
        set(
            [
                f"{kpi_by_company_year['company_name']}({kpi_by_company_year['year']})"
                for kpi_by_company_year in state[
                    "analyses_kpis_by_company_year_calculated"
                ]
            ]
        )
    )
    companies_and_years = (
        ", ".join(companies_and_years[:-1]) + " and " + companies_and_years[-1]
    )
    res = _generate_answer_from_kpis.invoke(
        {
            "question": f"Analyze the financial performance of {companies_and_years} on the basis of the given KPIs.",
            "kpis": kpis,
        }
    )

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = "generate_answer_from_kpis" + "//" + id
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not config.LOGGING_SETTINGS["generate_answer_from_kpis"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "partial_answer": res,
        "prev_node": child_node,
        "log_tree": log_tree,
    }

    send_logs(
        parent_node=parent_node,
        curr_node=child_node,
        child_node=None,
        input_state=state,
        output_state=output_state,
        text=child_node.split("//")[0],
    )

    ######

    return output_state
