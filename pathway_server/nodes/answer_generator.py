"""
This module contains functions for generating answers based on documents and questions using a Language Learning Model (LLM). 

Key Features:
1. **Document Metadata Management**: Functions like `remove_unnecessary_metadata_for_generation` ensure that only relevant document metadata is passed to the LLM for answer generation.
   
2. **Answer Generation**: 
   - `generate_answer`: Generates a response to a given question using the provided documents.
   - `generate_answer_with_citation_state`: Generates a response and includes structured citations from the document metadata.

3. **Citation Models**: 
   - `Citation` and `WebCitation` models define the structure for handling document and web citations, including content, page numbers, file names, and URLs.

4. **Citation Handling**: 
   - Functions like `append_citations` and `append_citations_internal` integrate citations into the final answers, either using document-based or web-based citations.
   
5. **Web Answer Generation**: 
   - `generate_web_answer`: Tailored for generating answers using web-based content, ensuring that inline citations are accurately added and a list of sources is provided at the end.

6. **Logging and Tracking**:
   - The module includes logging capabilities for tracking answer generation, citation processing, and related metadata.

Dependencies:
- Pydantic for data modeling and validation.
- LangChain for prompt templates and LLM interaction.
- External utilities like `state`, `config`, and `log_message` for state management and logging.

Usage:
- The functions are primarily designed to handle internal states (`InternalRAGState`, `OverallState`) and manage the flow of document-based and web-based content to generate answers and citations in structured formats.
"""


from pydantic import BaseModel, Field, root_validator
from typing import Optional
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from prompt import prompts
import state, config, nodes
from llm import llm
import uuid
from utils import log_message, send_logs, tree_log
from config import LOGGING_SETTINGS


def remove_unnecessary_metadata_for_generation(docs: list[Document]) -> list[Document]:
    """
    Remove unnecessary metadata from the document for generation.
    """
    for doc in docs:
        for key in config.WORKFLOW_SETTINGS[
            "field_to_ignore_from_metadata_for_generation"
        ]:
            doc.metadata.pop(key, None)
    return docs


def remove_unnecessary_metadata_for_generation(docs: list[Document]) -> list[Document]:
    """
    Remove unnecessary metadata from the document for generation.
    """
    for doc in docs:
        for key in config.WORKFLOW_SETTINGS[
            "field_to_ignore_from_metadata_for_generation"
        ]:
            doc.metadata.pop(key, None)
    return docs


basic_citation_prompt = prompts.basic_citation_prompt


def generate_answer(state: state.InternalRAGState):
    """
    Generates the answer based on the documents and the question present in the state.
    """

    log_message("---GENERATE---")
    question = state.get("original_question", state["question"])
    documents = state["documents"]
    image_url = state.get("image_url", "")

    chat_prompt_template = ChatPromptTemplate.from_messages(
        messages=[
            SystemMessage(content=basic_citation_prompt),
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": f"Context: {remove_unnecessary_metadata_for_generation(documents)}",
                    },
                    {"type": "text", "text": f"Question: {question}"},
                ]
            ),
        ]
    )

    # print(chat_prompt_template)
    rag_chain_basic = chat_prompt_template | llm | StrOutputParser()
    # print(rag_chain_basic)
    # RAG generation
    answer: str = rag_chain_basic.invoke({"context": documents, "question": question})
    return {"answer": answer, "citation": []}


# TODO: how to have inline citations ( how to uniquely identify citations when combing them in the answer)
class Citation(BaseModel):
    """Schema for a single citation."""

    citation_content: Optional[str] = Field(
        default=None,
        description="The exact sentence for which citation is being added.",
    )
    page: Optional[int] = Field(
        default=None, description="Page number of the cited content."
    )
    file_name: Optional[str] = Field(
        default=None, description="Name of the PDF file or document."
    )
    file_path: Optional[str] = Field(
        default=None, description="Path of the PDF file or document."
    )


class WebCitation(BaseModel):
    """Schema for a single citation."""

    citation_content: Optional[str] = Field(
        default=None,
        description="The exact sentence for which citation is being added.",
    )
    title: Optional[str] = Field(default=None, description="")
    website: Optional[str] = Field(
        default=None, description="exact website url from where context is retrived."
    )


class GeneratedAnswerOutput(BaseModel):
    """Schema for the structured output of the generate_answer_with_citation_state function."""

    main_answer: str = Field(
        description="The main answer as a single markdown formatted string."
    )
    citations: Optional[list[Citation]] = Field(
        default=None, description="A list of citations relevant to the answer."
    )
    # @root_validator(pre=True)
    # def ensure_citations_is_list(cls, values):
    #     """Ensure that citations is always a list, even if None."""
    #     if values.get('citations') is None:
    #         values['citations'] = []
    #     return values


class WebAnswerOutput(BaseModel):
    """Schema for the structured output of the generate_web_answer function."""

    main_answer: str = Field(
        description="The main answer as a single markdown formatted string."
    )
    citations: Optional[list[WebCitation]] = Field(
        default=None, description="A list of citations relevant to the answer."
    )


ans_with_structured_citations_prompt = prompts.ans_with_structured_citations_prompt


def generate_answer_with_citation_state(state: state.InternalRAGState):
    """
    Generates the answer based on the documents and the question present in the state.
    Returns structured output.
    """
    question = state.get("original_question", state["question"])
    documents = state["documents"]
    image_url = state.get("image_url", "")
    image_desc = state.get("image_desc", "")

    if image_url == "":
        chat_prompt_template = ChatPromptTemplate.from_messages(
            messages=[
                SystemMessage(content=ans_with_structured_citations_prompt),
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": f"Context: {remove_unnecessary_metadata_for_generation(documents)}",
                        },
                        {"type": "text", "text": f"Question: {question}"},
                    ]
                ),
            ]
        )
    else:
        image_url = f"data:image/jpeg;base64,{image_url}"
        chat_prompt_template = ChatPromptTemplate.from_messages(
            messages=[
                SystemMessage(content=ans_with_structured_citations_prompt),
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": f"Context: {remove_unnecessary_metadata_for_generation(documents)} \nImage description being shared may or may not be relevant to the question.",
                        },
                        {"type": "text", "text": {f"Image Description: {image_desc}"}},
                        {"type": "text", "text": f"Question: {question}"},
                    ]
                ),
            ]
        )
    rag_chain = chat_prompt_template | llm.with_structured_output(GeneratedAnswerOutput)
    res: GeneratedAnswerOutput = rag_chain.invoke({})  # type: ignore

    doc_generated_answer = res.main_answer
    answer = res.main_answer
    # if res.citations :
    if res.citations:
        citations = [
            citation.model_dump() for citation in res.citations
        ]  # Convert Citation objects to dictionaries
    else:
        citations = []
    for cit in citations:
        cit["unique_id"] = str(uuid.uuid4())

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = nodes.generate_answer_with_citation_state.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    # tree_log(f" tree_log_parent_node : {parent_node}" , 1)
    log_tree = {}

    if (
        not LOGGING_SETTINGS["generate_answer_with_citation_state"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part
    output_state = {
        "answer": answer,
        "doc_generated_answer": doc_generated_answer,
        "citations": citations,
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


class AnswerWithCitationOutput(BaseModel):
    """Schema for the output with citations."""

    final_answer: str = Field(
        description="The final answer with inline citations and sources."
    )


format1 = prompts.format1

format2 = prompts.format2

citation_adder_prompt = prompts.citation_adder_prompt


citation_adder_prompt_template = ChatPromptTemplate.from_template(citation_adder_prompt)

citation_adder = citation_adder_prompt_template | llm.with_structured_output(
    AnswerWithCitationOutput
)

web_citation_adder_prompt = """
You are tasked with adding inline citations and a list of sources to a given answer. 
The citations are provided as a list of dictionaries containing citation content , url of the source . 

Your tasks:
1. Identify where each citation's `citation_content` matches the `final_answer`. It may not be an exact match but if the data or information from the citation content is used in a sentence in the final answer then citation needs to be added there in the final answer.
2. Add an inline citation in the format mentioned below immediately after the matching sentence / used information  in the answer.
3. Make sure there is a list of sources at the end of the answer. 
4. At the end of the answer, include a "Sources" section listing all the citations with their corresponding numbers
Example 1 : 
    Sources:
    [1] <title> , <website_link>

 [If there is a url in the citation then use format_for_web_sources]
 Format_for_web_sources (If citation has a website) : {format1}

Ensure:
- Inline citations are correctly numbered. 
- Make sure you do not miss any citation from the combined citations.
- Always use exact urls if present. Do not use urls if not present. Never create artificial urls for a citation in any case.

Input:
- Final Answer: {final_answer}
- Citations: {combined_citations}

Output:
The answer with inline citations and the sources list.
"""


web_citation_adder_prompt_template = ChatPromptTemplate.from_template(web_citation_adder_prompt)

web_citation_adder = web_citation_adder_prompt_template | llm.with_structured_output(
    AnswerWithCitationOutput
)


def append_citations(state: state.OverallState):
    """
    Generate final answer with inline citations and sources using LLM.
    """
    combined_citations = state["combined_citations"]
    print(f"\n Combined citations : \n {combined_citations} \n")
    final_answer = state["final_answer"]

    # for citation in combined_citations:
    #     if citation
    # Prepare input for the LLM
    input_data = {
        "final_answer": final_answer,
        # "combined_citations": [
        #     {
        #         "citation_content": citation.citation_content,
        #         "page": citation.page,
        #         "file_name": citation.file_name,
        #         "file_path": citation.file_path,
        #     }
        #     for citation in combined_citations
        # ],
        "combined_citations": combined_citations,
        "format1": format1,
        "format2": format2,
    }

    # Invoke the LLM with the prompt
    result = citation_adder.invoke(input_data)
    final_answer_with_citations = result.final_answer

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = nodes.append_citations.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}
    if not LOGGING_SETTINGS["append_citations"]:
        child_node = parent_node
    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "final_answer": final_answer_with_citations,
        "prev_node": child_node,
        "log_tree": log_tree,
        "combine_answer_parents": child_node,
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


def append_citations_internal(state: state.OverallState):
    """
    Generate final answer with inline citations and sources using LLM.
    """

    combined_citations = state["citations"]
    final_answer = state["answer"]

    print(f"combine_citations : {combined_citations}")
    print(f"final_answer : {final_answer}")

    # for citation in combined_citations:
    #     if citation
    # Prepare input for the LLM
    input_data = {
        "final_answer": final_answer,
        "combined_citations": combined_citations,
        "format1": format1,
    }

    # Invoke the LLM with the prompt
    result = web_citation_adder.invoke(input_data)
    final_answer_with_citations = result.final_answer

    ###### log_tree part
    # import uuid , nodes
    # id = str(uuid.uuid4())
    # child_node = nodes.append_citations_internal.__name__ + "//" + id
    # parent_node = state.get("prev_node", "START")
    # log_tree = {}
    # if not LOGGING_SETTINGS["append_citations"]:
    #     child_node = parent_node
    # log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part
    print(final_answer_with_citations)
    output_state = {
        "answer": final_answer_with_citations,
        # "prev_node": child_node,
        # "log_tree": log_tree,
        # "combine_answer_parents": child_node,
    }

    # send_logs(
    #     parent_node=parent_node,
    #     curr_node=child_node,
    #     child_node=None,
    #     input_state=state,
    #     output_state=output_state,
    #     text=child_node.split("//")[0],
    # )

    ######

    return output_state


rag_citation_adder_prompt = """

You are tasked with adding inline citations and a list of sources to a given answer. 
The citations are provided as a list of dictionaries containing specific content, page numbers, file names, and file paths.

Your tasks:
1. Identify where each citation's `citation_content` matches the `final_answer`. It may not be an exact match but if the data or information from the citation content is used in a sentence in the final answer then citation needs to be added there in the final answer.
2. Add an inline citation in the format mentioned below immediately after the matching sentence / used information  in the answer.
3. Make sure there is a list of sources at the end of the answer. 
4. At the end of the answer, include a "Sources" section listing all the citations with their corresponding numbers
Example 1 : 
    Sources:
    [1] goog-10-k-2021.pdf, Page 60, data/goog-10-k-2021.pdf



 [Use format_from_document_sources: ]
 Format_for_document_sources : {format2}

Ensure:
- Inline citations are correctly numbered.
- Make sure there is a list of Sources at the end of the answer 
- The numbers in the sources list at the end should correspond accurately to the inline citations. 
- Make sure you do not miss any citation from the combined citations.
- Always use exact pdf names if present. Do not use urls if not present. Never create artificial pdf names for a citation in any case.

Input:
- Answer: {final_answer}
- Citations: {combined_citations}

Output:
The answer with inline citations and the sources list.
"""


rag_citation_adder_prompt_template = ChatPromptTemplate.from_template(rag_citation_adder_prompt)

rag_citation_adder = rag_citation_adder_prompt_template | llm.with_structured_output(
    AnswerWithCitationOutput
)


def append_citations_internal_rag(state: state.OverallState):
    """
    Generate final answer with inline citations and sources using LLM.
    """
    combined_citations = state["combined_citations"]
    print(f"\n Combined citations : \n {combined_citations} \n")
    final_answer = state["final_answer"]

    # for citation in combined_citations:
    #     if citation
    # Prepare input for the LLM
    input_data = {
        "final_answer": final_answer,
        # "combined_citations": [
        #     {
        #         "citation_content": citation.citation_content,
        #         "page": citation.page,
        #         "file_name": citation.file_name,
        #         "file_path": citation.file_path,
        #     }
        #     for citation in combined_citations
        # ],
        "combined_citations": combined_citations,
        # "format1": format1,
        "format2": format2,
    }

    # Invoke the LLM with the prompt
    result = rag_citation_adder.invoke(input_data)
    final_answer_with_citations = result.final_answer

    ###### log_tree part
    # # import uuid , nodes
    # id = str(uuid.uuid4())
    # child_node = nodes.append_citations.__name__ + "//" + id
    # parent_node = state.get("prev_node", "START")
    # log_tree = {}
    # if not LOGGING_SETTINGS["append_citations"]:
    #     child_node = parent_node
    # log_tree[parent_node] = [child_node]
    # ######

    ##### Server Logging part

    output_state = {
        "final_answer": final_answer_with_citations,
        # "prev_node": child_node,
        # "log_tree": log_tree,
        # "combine_answer_parents": child_node,
    }

    # send_logs(
    #     parent_node=parent_node,
    #     curr_node=child_node,
    #     child_node=None,
    #     input_state=state,
    #     output_state=output_state,
    #     text=child_node.split("//")[0],
    # )

    ######

    return output_state

## WEB ANSWER TEMPLATE
web_generator_prompt = ChatPromptTemplate.from_template(
    prompts.web_generator_prompt
)
rag_chain_web = web_generator_prompt | llm.with_structured_output(WebAnswerOutput)


def generate_web_answer(state: state.InternalRAGState):
    """
    Generates the answer based on the documents and the question present in the state.
    """
    question_group_id = state.get("question_group_id", 1)

    # log_message("---GENERATE---",f"question_group{question_group_id}")
    question = state.get("original_question", state["question"])
    documents = state["documents"]

    if config.WORKFLOW_SETTINGS["with_site_blocker"]:
        for doc in documents:
            url = doc.metadata["url"]
            if sum([allowed_url in url for allowed_url in state.get("urls", [])]) == 0:
                documents.remove(doc)

    log_message(f"web_documents: {documents}", f"question_group{question_group_id}")
    res: WebAnswerOutput = rag_chain_web.invoke(
        {
            "context": remove_unnecessary_metadata_for_generation(documents),
            "question": question,
        }
    )  # type: ignore 

    web_generated_answer = res.main_answer
    answer = res.main_answer
    if res.citations:
        citations = [
            citation.model_dump() for citation in res.citations
        ]  # Convert Citation objects to dictionaries
    else:
        citations = []
    for cit in citations:
        cit["unique_id"] = str(uuid.uuid4())
    log_message(
        f"-------FINAL ANSWER GENERATION--------\n------ {res}",
        f"question_group{question_group_id}",
    )



    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = nodes.generate_web_answer.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}

    if (
        not LOGGING_SETTINGS["generate_web_answer"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "web_generated_answer" : web_generated_answer , 
        "answer" : answer ,
        "citations" : citations ,
        "prev_node" : child_node,
        "log_tree" : log_tree ,
        # "web_generated_answer": web_generated_answer,
        # "answer": answer,
        # "citations": citations,
        # "prev_node": child_node,
        # "log_tree": log_tree,
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
