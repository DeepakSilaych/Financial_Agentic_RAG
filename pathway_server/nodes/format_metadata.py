# -------------------------------
# Metadata Conversion and Parent Extraction
# -------------------------------
# This module provides functionality to:
# 1. Convert metadata (represented as a dictionary) into JMESPath expressions, which are useful for filtering metadata
#    in queries.
# 2. Extract the parent company or product name from a given metadata input using a language model (LLM).
#
# The conversion of metadata to JMESPath is done through a prompt template and LLM interaction, where the system 
# is instructed to process the metadata and return the corresponding filtering expressions.
#
# The parent extraction process uses another prompt to extract the name of the parent company from the metadata provided.
#
# Functions:
# - convert_metadata_to_jmespath_llm: Converts metadata into JMESPath expressions for filtering using LLM interaction.
# - convert_metadata_to_jmespath: Converts metadata into JMESPath expressions manually by iterating over key-value pairs
#   and forming conditions for list and non-list values.
# - (Optional) _extract_parent_system_prompt: A prompt used to extract the parent company or product name.
# -------------------------------

import json
from typing import Dict, Optional

from langchain.prompts import ChatPromptTemplate
from prompt import prompts
from llm import llm
from utils import log_message

_system_prompt = prompts.format_metadata_system_prompt
# Define the prompt template for processing metadata to JMESPath expressions
metadata_prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        (
            "human",
            "Metadata: {metadata}\nConvert this metadata into JMESPath expressions for filtering.",
        ),
    ]
)

metadata_converter = metadata_prompt_template | llm.with_structured_output(list)

_extract_parent_system_prompt = prompts._extract_parent_system_prompt

extract_parent_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _extract_parent_system_prompt),
        (
            "human",
            "Give the name of the parent company for the company or product mentioned in the metadata: {metadata}.",
        ),
    ]
)

parent_extractor = extract_parent_prompt | llm


# Not working pretty well (output format is not always JMESpath)
def convert_metadata_to_jmespath_llm(metadata: Dict) -> list[str]:
    """
    Convert the input metadata (dictionary) into JMESPath expressions for filtering.

    Args:
        metadata (Dict): The metadata to be converted.

    Returns:
        list[str]: The list of JMESPath expressions that can be used for filtering.
    """

    log_message(metadata)
    result = metadata_converter.invoke({"metadata": json.dumps(metadata)})
    log_message("---FORMATTED METADATA: " + str(result))

    return result  # type: ignore


def convert_metadata_to_jmespath(metadata: dict[str, str | list[str]]) -> str:
    jmespath_parts = []

    # if metadata_filters is None:
    #     metadata_filters = metadata.keys()

    for key, value in metadata.items():
        if value is None:
            continue

        if isinstance(value, list):
            conditions = []
            for item in value:
                if item is None or item.lower() == "none" or item.lower() == "unknown":
                    continue
                conditions.append(f"{key} == `{item}`")
            jmespath_parts.append(f"({' || '.join(conditions)})")

        # Handling non-list values (company_name, year, etc.)
        else:  # Being used for company_name , year
            if value == None or value.lower() == "none" or value.lower() == "unknown":
                continue
            jmespath_parts.append(f"{key} == `{value}`")

    return " && ".join(jmespath_parts)
