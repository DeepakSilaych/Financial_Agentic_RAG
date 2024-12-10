# This module defines various classes and functions for persona-based question answering.
# The goal is to create multiple personas, generate specific questions for each persona,
# and combine their answers to form a final response. Additionally, there is functionality
# to handle persona selection and question generation based on context.

# 1. Persona Class: Represents an individual persona's role and description.
# 2. PersonasGenerationOutput: Holds the generated list of personas.
# 3. Question Generation: Includes logic to generate specific questions for each persona.
# 4. Answer Combination: Combines answers from various personas into a cohesive response.
# 5. Logging: Captures and sends logs related to persona generation and answer combinations.

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from prompt import prompts
import state, config
from llm import llm
from utils import send_logs, log_message
from config import LOGGING_SETTINGS
import uuid


class Persona(BaseModel):
    role: str = Field(
        description="Role of the persona in the context of the question.",
    )
    description: str = Field(
        description="Description of the persona. Its focus, concerns, and motives.",
    )

    @property
    def persona(self) -> str:
        return f"Role: {self.role}\nDescription: {self.description}\n"


class PersonasGenerationOutput(BaseModel):
    personas: List[Persona] = Field(
        description="Comprehensive list of personas with their roles and descriptions.",
    )


# 2. The user wants these personas to perform the following types of analysis: {analysis_type}.
_create_personas_system_prompt = prompts._create_personas_system_prompt
create_personas_prompt = ChatPromptTemplate.from_template(
    _create_personas_system_prompt
)

personas_creator = create_personas_prompt | llm.with_structured_output(
    PersonasGenerationOutput
)


# Maybe add this generalist persona to handle any questions that are not covered by the other analysts
# generalist = Persona(
#     role="Generalist Financial Expert",
#     affiliation="None",
#     specialisation="This agent is an expert at answering any type of financial question that cannot be answered by the other analysts. They are the last resort for the team. They are assigned tasks that are not covered by the other analysts.",
# )


def create_persona(state: state.OverallState):
    question = state["question"]

    personas: list[Persona] = personas_creator.invoke({"question": question, "max_analysts": config.MAX_PERSONAS_GENERATED}).personas  # type: ignore

    if len(personas) > config.MAX_PERSONAS_GENERATED:
        personas = personas[: config.MAX_PERSONAS_GENERATED]

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = "create_persona" + "//" + id
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not LOGGING_SETTINGS["create_persona"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "personas": [persona.model_dump() for persona in personas],
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


class PersonaSpecificQuestion(BaseModel):
    analyst_index: int = Field(
        description="Index of the analyst in the list of analysts.",
    )
    question: str = Field(
        description="Specific question for the analyst to answer.",
    )


class PersonaSpecificQuestionGenerationOutput(BaseModel):
    questions: List[PersonaSpecificQuestion] = Field(
        description="List of specific questions for each analyst.",
    )


_persona_specific_question_creator_system_prompt = prompts._persona_specific_question_creator_system_prompt
persona_specific_question_creator_prompt = ChatPromptTemplate.from_template(
    _persona_specific_question_creator_system_prompt
)
persona_specific_question_creator = (
    persona_specific_question_creator_prompt
    | llm.with_structured_output(PersonaSpecificQuestionGenerationOutput)
)


def create_persona_specific_questions(state: state.OverallState):
    question = state["question"]
    personas = state["personas"]

    persona_specific_questions: list[
        PersonaSpecificQuestion
    ] = persona_specific_question_creator.invoke(
        {
            "question": question,
            "analysts": "\n".join(
                [
                    f"{index + 1}. {persona['role']}: {persona['description']}"
                    for index, persona in enumerate(personas)
                ]
            ),
        }
    ).questions  # type: ignore

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = "create_persona_specific_questions" + "//" + id
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not LOGGING_SETTINGS["create_persona_specific_questions"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "persona_specific_questions": [
            persona_specific_question.question
            for persona_specific_question in persona_specific_questions
        ],
        "prev_node" : child_node,
        "log_tree" : log_tree ,
        # "combine_answer_parents" : child_node ,
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

    # return {
    #     "persona_specific_questions": [
    #         persona_specific_question.question
    #         for persona_specific_question in persona_specific_questions
    #     ]
    # }


class PersonaGeneratedQuestion(BaseModel):
    question: Optional[str] = Field(description="Question generated by the persona.")


_question_generation_using_persona_system_prompt = prompts._question_generation_using_persona_system_prompt

question_generation_using_persona_prompt = ChatPromptTemplate.from_template(
    _question_generation_using_persona_system_prompt
)
_question_generation_using_persona = (
    question_generation_using_persona_prompt
    | llm.with_structured_output(PersonaGeneratedQuestion)
)


def generate_question_using_persona(state: state.PersonaState):
    question = state["persona_question"]
    persona = state["persona"]

    prev_questions = state["persona_generated_questions"]
    prev_answers = state["persona_generated_answers"]
    combined_qas = "\n\n".join(
        [f"Q: {q}\nA: {a}" for q, a in zip(prev_questions, prev_answers)]
    )

    if len(prev_questions) >= config.MAX_QUESTIONS_GENERATED_BY_EACH_PERSONA:
        return {"persona_generated_questions": [None]}

    generated_question = _question_generation_using_persona.invoke(
        {
            "role": persona["role"],
            "description": persona["description"],
            "question": question,
            "previous_questions_and_answers": combined_qas,
            "max_questions": config.MAX_QUESTIONS_GENERATED_BY_EACH_PERSONA,
        }
    ).question

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    # child_node = generate_question_using_persona + "//" + id
    child_node = "agent" + "//" + id
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not LOGGING_SETTINGS["generate_question_using_persona"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "persona_generated_questions": [generated_question],
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


def generate_question_using_persona_with_supervisor(state: state.OverallState):
    question = state["question"]
    persona = state["current_persona"]

    if persona is None:
        # Should never be reachable
        raise ValueError("current_persona is None")

    prev_questions = state["persona_generated_questions_using_supervisor"]
    prev_answers = state["persona_generated_answers_using_supervisor"]
    combined_qas = "\n\n".join(
        [f"Q: {q}\nA: {a}" for q, a in zip(prev_questions, prev_answers)]
    )

    generated_question = _question_generation_using_persona.invoke(
        {
            "role": persona["role"],
            "description": persona["description"],
            "question": question,
            "previous_questions_and_answers": combined_qas,
            "max_questions": config.MAX_QUESTIONS_GENERATED_BY_PERSONAS_SUPERVISOR,
        }
    ).question

    return {"persona_generated_questions_using_supervisor": [generated_question]}


_answer_combiner_using_persona_system_prompt = prompts._answer_combiner_using_persona_system_prompt

answer_combiner_using_persona_prompt = ChatPromptTemplate.from_template(
    _answer_combiner_using_persona_system_prompt
)
_answer_combiner_using_persona = (
    answer_combiner_using_persona_prompt | llm | StrOutputParser()
)


def combine_persona_generated_answers(state: state.PersonaState):
    question = state["persona_question"]
    persona = state["persona"]

    prev_questions = state["persona_generated_questions"]
    prev_questions = [q for q in prev_questions if q is not None]
    prev_answers = state["persona_generated_answers"]
    combined_qas = "\n\n".join(
        [f"Q: {q}\nA: {a}" for q, a in zip(prev_questions, prev_answers)]
    )

    combined_answer = _answer_combiner_using_persona.invoke(
        {
            "role": persona["role"],
            "description": persona["description"],
            "question": question,
            "previous_questions_and_answers": combined_qas,
        }
    )

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = "combine_persona_generated_answers" + "//" + id
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not LOGGING_SETTINGS["combine_persona_generated_answers"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "persona_specific_answers": [combined_answer],
        "prev_node": child_node,
        "log_tree": log_tree,
        "persona_last_nodes": child_node,
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


_answer_combiner_using_persona_with_supervisor_system_prompt = prompts._answer_combiner_using_persona_with_supervisor_system_prompt

answer_combiner_using_persona_with_supervisor_prompt = ChatPromptTemplate.from_template(
    _answer_combiner_using_persona_with_supervisor_system_prompt
)
_answer_combiner_using_persona_with_supervisor = (
    answer_combiner_using_persona_with_supervisor_prompt | llm | StrOutputParser()
)


def combine_persona_with_supervisor_generated_answers(state: state.OverallState):
    question = state["question"]

    prev_questions = state["persona_generated_questions_using_supervisor"]
    prev_answers = state["persona_generated_answers_using_supervisor"]
    combined_qas = "\n\n".join(
        [f"Q: {q}\nA: {a}" for q, a in zip(prev_questions, prev_answers)]
    )

    personas = "\n".join(
        [
            f"{index + 1}. {persona['role']}: {persona['description']}"
            for index, persona in enumerate(state["personas"])
        ]
    )

    combined_answer = _answer_combiner_using_persona_with_supervisor.invoke(
        {
            "personas": personas,
            "question": question,
            "previous_questions_and_answers": combined_qas,
        }
    )

    return {"final_answer": combined_answer}


def combine_persona_specific_answers(state: state.OverallState):
    question = state["question"]

    persona_specific_questions = state["persona_specific_questions"]
    persona_specific_answers = state["persona_specific_answers"]
    combined_qas = "\n\n".join(
        [
            f"Q: {q}\nA: {a}"
            for q, a in zip(persona_specific_questions, persona_specific_answers)
        ]
    )

    personas = "\n".join(
        [
            f"{index + 1}. {persona['role']}: {persona['description']}"
            for index, persona in enumerate(state["personas"])
        ]
    )

    # NOTE: This prompt is the same as the one used for combining answers with supervisor (not a mistake)
    combined_answer = _answer_combiner_using_persona_with_supervisor.invoke(
        {
            "personas": personas,
            "question": question,
            "previous_questions_and_answers": combined_qas,
        }
    )

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = "combine_persona_specific_answers" + "//" + id
    # parent_node = state.get("prev_node" , "START")
    parent_node = state.get("persona_last_nodes", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if not LOGGING_SETTINGS["combine_persona_specific_answers"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "final_answer": combined_answer,
        "prev_node" : child_node,
        "log_tree" : log_tree ,
         "combine_answer_parents" : child_node ,
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


_persona_selection_using_supervisor_system_prompt = prompts._persona_selection_using_supervisor_system_prompt


class PersonaSelectionUsingSupervisorOutput(BaseModel):
    next_persona: Optional[Persona] = Field(
        description="Next persona to ask a question."
    )


persona_selection_using_supervisor_prompt = ChatPromptTemplate.from_template(
    _persona_selection_using_supervisor_system_prompt
)
_persona_selection_using_supervisor = (
    persona_selection_using_supervisor_prompt
    | llm.with_structured_output(PersonaSelectionUsingSupervisorOutput)
)


def select_next_persona(state: state.OverallState):
    prev_questions = state["persona_generated_questions_using_supervisor"]

    if len(prev_questions) >= config.MAX_QUESTIONS_GENERATED_BY_PERSONAS_SUPERVISOR:
        return {"current_persona": None}

    prev_answers = state["persona_generated_answers_using_supervisor"]
    combined_qas = "\n\n".join(
        [f"Q: {q}\nA: {a}" for q, a in zip(prev_questions, prev_answers)]
    )

    personas = "\n".join(
        [
            f"{index + 1}. {persona['role']}: {persona['description']}"
            for index, persona in enumerate(state["personas"])
        ]
    )

    next_persona = _persona_selection_using_supervisor.invoke(
        {
            "personas": personas,
            "question": state["question"],
            "previous_questions_and_answers": combined_qas,
            "max_questions": config.MAX_PERSONAS_GENERATED,
        }
    ).next_persona

    if next_persona is None:
        return {"current_persona": None}

    return {"current_persona": next_persona.model_dump()}