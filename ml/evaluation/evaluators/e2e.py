import numpy as np
from pydantic import BaseModel, Field

from langchain import hub
from langchain.prompts import ChatPromptTemplate
from langsmith.schemas import Example, Run
from langsmith.evaluation import EvaluationResult
from langsmith.evaluation.llm_evaluator import LLMEvaluator, ContinuousScoreConfig
from pysbd import Segmenter

from llm import llm
from embeddings import embedder
from .base import BaseEvaluator


def binary_scoring(key: str, desc: str):
    return ContinuousScoreConfig(
        key=key, min=0, max=1, description=desc, include_explanation=True
    )


class BaseLLMJudge(BaseEvaluator):
    evaluator: LLMEvaluator

    def evaluate(self, run: Run, example: Example) -> EvaluationResult:
        return self.evaluator.evaluate_run(run, example)


class LLMEvaluatorCustom(BaseLLMJudge):
    def __init__(self, prompt_template, score_config, map_variables, model_name):
        self.evaluator = LLMEvaluator(
            prompt_template=prompt_template,
            score_config=score_config,
            map_variables=map_variables,
            model_name=model_name,
        )


class LLMCorrectnessBinary(LLMEvaluatorCustom):
    """
    Checks the correctness of the answer with respect to the reference answer
    Does binary scoring 0-1
    """

    def __init__(self, model_name="gpt-4o"):
        prompt = hub.pull("answer-correctness-binary")

        map_variables = lambda run, example: {
            "question": example.inputs["question"],
            "correct_answer": example.outputs["answer"],
            "student_answer": run.outputs["answer"],
        }

        super().__init__(
            prompt_template=prompt.messages,
            score_config=binary_scoring(
                self.__class__.__name__,
                desc="Correctness of the answer with respect to the reference answer. 1 if correct, 0 if incorrect.",
            ),
            map_variables=map_variables,
            model_name=model_name,
        )


# class LLMCorrectness(LLMEvaluatorCustom):
#     """
#     Checks the correctness of the answer with respect to the reference answer
#     Does 0-3 scoring
#     """

#     def __init__(self, model_name="gpt-4o"):
#         prompt = hub.pull("answer-correctness-4scale")

#         map_variables = lambda run, example: {
#             "question": example.inputs["question"],
#             "correct_answer": example.outputs["answer"],
#             "student_answer": run.outputs["answer"],
#         }

#         super().__init__(
#             prompt_template=prompt.messages,
#             score_config=ContinuousScoreConfig(
#                 key=self.__class__.__name__,
#                 min=0,
#                 max=3,
#                 description="Correctness of the answer with respect to the reference answer. Integer upto 3 if correct, 0 if incorrect.",
#                 include_explanation=True,
#             ),
#             map_variables=map_variables,
#             model_name=model_name,
#         )


class LLMHelpfullness(LLMEvaluatorCustom):
    """
    Evaluates the helpfulness of the answer
    does not require the correct answer

    Scores binary 0-1
    """

    def __init__(self, model_name="gpt-4o"):
        prompt = hub.pull("answer-helpfullness-metric-binary")
        map_variables = lambda run, example: {
            "question": example.inputs["question"],
            "output": run.outputs["answer"],
        }

        super().__init__(
            prompt_template=prompt.messages,
            score_config=binary_scoring(
                self.__class__.__name__,
                desc="Helpfulness of the answer. 1 if helpful, 0 if not helpful.",
            ),
            map_variables=map_variables,
            model_name=model_name,
        )


class LLMUsefullness(LLMEvaluatorCustom):
    """
    Evaluates the usefulness of the answer
    does not require the correct answer

    Scores binary 0-1
    """

    def __init__(self, model_name="gpt-4o"):
        prompt = hub.pull("answer-usefulness-binary")
        map_variables = lambda run, example: {
            "question": example.inputs["question"],
            "answer": run.outputs["answer"],
        }
        super().__init__(
            prompt_template=prompt.messages,
            score_config=binary_scoring(
                self.__class__.__name__,
                desc="Usefulness of the answer. 1 if useful, 0 if not useful.",
            ),
            map_variables=map_variables,
            model_name=model_name,
        )


class SimplifiedSentence(BaseModel):
    sentence_index: int = Field(description="The index of the sentence in the input")
    simplified_sentences: list[str] = Field(description="The simplified sentences")


class SimplifiedSentenceOutput(BaseModel):
    simplified_sentences: list[SimplifiedSentence] = Field(
        description="The simplified sentences"
    )


sentence_simplification_system_prompt = """Given a question, an answer, and sentences from the answer analyze the complexity of each sentence given under 'sentences' and break down each sentence into one or more fully understandable statements while also ensuring no pronouns are used in each statement.

These are some examples to show how to perform the above instruction:

input: {"question": "Who was Albert Einstein and what is he best known for?", "answer": "He was a German-born theoretical physicist, widely acknowledged to be one of the greatest and most influential physicists of all time. He was best known for developing the theory of relativity, he also made important contributions to the development of the theory of quantum mechanics.", "sentences": {0: "He was a German-born theoretical physicist, widely acknowledged to be one of the greatest and most influential physicists of all time.", 1: "He was best known for developing the theory of relativity, he also made important contributions to the development of the theory of quantum mechanics."}}
output: [{"sentence_index": 0, "simplified_sentences": ["Albert Einstein was a German-born theoretical physicist.", "Albert Einstein was widely acknowledged to be one of the greatest and most influential physicists of all time."]}, {"sentence_index": 1, "simplified_sentences": ["Albert Einstein was best known for developing the theory of relativity.", "Albert Einstein made important contributions to the development of the theory of quantum mechanics."]}]

input: {"question": "How many authorized dealerships and agents did Volkswagen have as of December 31, 2023?", "answer": As of December 31, 2023, Volkswagen had 4,618 authorized dealerships and agents., "sentences": {0: 'As of December 31, 2023, Volkswagen had 4,618 authorized dealerships and agents.'}}
output: [{"sentence_index": 0, "simplified_sentences": ["As of December 31, 2023, Volkswagen had a total of 4,618 authorized dealerships and agents."]}]
"""

sentence_simplification_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            sentence_simplification_system_prompt.replace("{", "{{").replace("}", "}}"),
        ),
        (
            "human",
            """input: \n\n {{"question": {question}, "answer": {answer}, "sentences": {sentences}}}""",
        ),
    ]
)

sentence_simplifier = sentence_simplification_prompt | llm.with_structured_output(
    SimplifiedSentenceOutput
)


class FaithfulnessVerdict(BaseModel):
    sentence: str = Field(description="The statement")
    reason: str = Field(description="The reason for the verdict")
    verdict: int = Field(description="1 if the statement is faithful, 0 if not")


class FaithfulnessVerdictOutput(BaseModel):
    verdicts: list[FaithfulnessVerdict] = Field(
        description="The verdicts for each statement"
    )


faithfulness_verdict_system_prompt = """Your task is to judge the faithfulness of a series of statements based on a given context.
For each statement you must return verdict as 1 if the statement can be directly inferred based on the context or 0 if the statement can not be directly inferred based on the context.
While checking the numbers in the statements, you should allow for a margin of error of about +-5%. For example, if the context mentions that John is 25 years old, you should consider statements like "John is in his mid-twenties" or "John is around 25 years old" as faithful". Or if the context mentions a number as 4.5, you should consider statements like "around 5" or "less than 5" or "5" or "4" as faithful. Or if the context mentions a number as $94,586 million, you should consider statements like "$94,500 million" or "$94,600 million" as faithful.

These are some examples to show how to perform the above instruction:

input: {"context": "John is a student at XYZ University. He is pursuing a degree in Computer Science. He is enrolled in several courses this semester, including Data Structures, Algorithms, and Database Management. John is a diligent student and spends a significant amount of time studying and completing assignments. He often stays late in the library to work on his projects.", "statements": ["John is majoring in Biology.", "John is taking a course on Artificial Intelligence.", "John is a dedicated student.", "John has a part-time job."]}
output: [{"sentence": "John is majoring in Biology.", "reason": "John's major is explicitly mentioned as Computer Science. There is no information suggesting he is majoring in Biology.",, "verdict": 0}, {"sentence": "John is taking a course on Artificial Intelligence.", "reason": "The context mentions the courses John is currently enrolled in, and Artificial Intelligence is not mentioned. Therefore, it cannot be deduced that John is taking a course on AI.", "verdict": 0}, {"sentence": "John is a dedicated student.", "reason": "The context states that he spends a significant amount of time studying and completing assignments. Additionally, it mentions that he often stays late in the library to work on his projects, which implies dedication.", "verdict": 1}, {"sentence": "John has a part-time job.", "reason": "There is no information given in the context about John having a part-time job.", "verdict": 0}]

input: {"context": "Photosynthesis is a process used by plants, algae, and certain bacteria to convert light energy into chemical energy.", "statements": ["Albert Einstein was a genius."]}
output: [{"sentence": "Albert Einstein was a genius.", "reason":"The context and statement are unrelated", "verdict": 0}]

input: {"context": In the 2023 financial reports, IBM's Consulting revenue was $19,985 million, reflecting a year-to-year percentage growth of 4.6%. For Google Cloud, the revenue for 2023 was $33,088 million, which represents a significant increase from $26,280 million in 2022, resulting in a percentage growth of approximately 25.5%., "statements": ["In 2023, IBM's Consulting revenue increased by 4.6% compared to the previous year.", 'Google Cloud revenues increased by 26% in 2023.']}
output: [{"sentence": "In 2023, IBM's Consulting revenue increased by 4.6% compared to the previous year.", "reason": "The context explicitly states that IBM's Consulting revenue reflected a year-to-year percentage growth of 4.6%.", "verdict": 1}, {"sentence": "Google Cloud revenues increased by 26% in 2023.", "reason": "The context mentions that Google Cloud's revenue growth was approximately 25.5%, which is close to 26%. Therefore, this statement can be considered to be approximataly correct", "verdict": 1}]

input: {"context": The net cash provided by operating activities for the year 2023 amounted to $84.9 billion, measured in millions of dollars., "statements": ['In 2023, net cash provided by operating activities amounted to a total of $84,946 million.']}
output: [{"sentence": "In 2023, net cash provided by operating activities amounted to a total of $84,946 million.", "reason": "The context states that the net cash provided by operating activities for the year 2023 amounted to $84.9 billion, which is equivalent to $84,900 million. The statement is within the margin of error of +-5% and can be considered faithful.", "verdict": 1}]
"""

faithfulness_verdict_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            faithfulness_verdict_system_prompt.replace("{", "{{").replace("}", "}}"),
        ),
        ("human", """input: {{"context": {context}, "statements": {statements}}}"""),
    ]
)

faithfulness_verdict = faithfulness_verdict_prompt | llm.with_structured_output(
    FaithfulnessVerdictOutput
)


class LLMFaithfulness(BaseEvaluator):
    """
    Evaluates the faithfulness of the answer (does not require the correct answer)

    Scores between 0 and 1
    """

    def __init__(self):
        self.sentence_segmenter = Segmenter()

    def _decompose_into_sentences(self, question: str, answer: str) -> list[str]:
        sentences = self.sentence_segmenter.segment(answer)
        sentences_with_indices = {
            idx: statement
            for idx, statement in enumerate(sentences)
            if statement.strip().endswith((".", "?", "!"))
        }

        res: SimplifiedSentenceOutput = sentence_simplifier.invoke(
            {
                "question": question,
                "answer": answer,
                "sentences": sentences_with_indices,
            }
        )  # type: ignore

        simplified_sentences = []
        for sentence in res.simplified_sentences:
            simplified_sentences.extend(sentence.simplified_sentences)
        return simplified_sentences

    def evaluate(self, run: Run, example: Example) -> EvaluationResult:
        question = example.inputs["question"]
        answer = run.outputs["final_answer"]  # type: ignore
        retrieved_contexts = run.outputs["combined_documents"]  # type: ignore
        contexts_str = "\n".join([ctx.page_content for ctx in retrieved_contexts])

        simplified_sentences = self._decompose_into_sentences(question, answer)
        if len(simplified_sentences) == 0 or all(s == "" for s in simplified_sentences):
            raise ValueError("No simplified sentences generated")

        verdicts: FaithfulnessVerdictOutput = faithfulness_verdict.invoke(
            {"context": contexts_str, "statements": simplified_sentences}
        )  # type: ignore
        num_faithful = sum([verdict.verdict for verdict in verdicts.verdicts])
        num_statements = len(simplified_sentences)
        return EvaluationResult(
            key=self.__class__.__name__,
            score=num_faithful / num_statements,
            comment=f"{num_faithful} out of {num_statements} statements are faithful",
        )


class GeneratedQuestion(BaseModel):
    question: str = Field(description="The generated question")
    non_committal: int = Field(
        description="1 if the answer is non_committal and 0 if the answer is committal"
    )


question_generation_system_prompt = """Generate a question for the given answer and Identify if answer is non_committal.
Give non_committal as 1 if the answer is non_committal and 0 if the answer is committal.
A non_committal answer is one that is evasive, vague, or ambiguous.
For example, "I don't know" or "I'm not sure" are non_committal answers.

These are some examples to show how to perform the above instruction:

input: Albert Einstein was born in Germany.
output: {"question": "Where was Albert Einstein born?", "non_committal": 0}

input: I don't know about the  groundbreaking feature of the smartphone invented in 2023 as am unaware of information beyond 2022.
output: {"question": "What was the groundbreaking feature of the smartphone invented in 2023?", "non_committal": 1}
"""
question_generation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            question_generation_system_prompt.replace("{", "{{").replace("}", "}}"),
        ),
        ("human", "input: \n\n {answer}"),
    ]
)

question_generator = question_generation_prompt | llm.with_structured_output(
    GeneratedQuestion
)


class LLMResponseRelevancy(BaseEvaluator):
    """
    Evaluates the relevancy of the answer with respect to the question

    Scores between 0 and 1
    """

    def __init__(self, strictness: int = 3):
        self.strictness = strictness

    def _calculate_similarity(self, question: str, generated_questions: list[str]):
        question_vec = np.asarray(embedder.embed_query(question)).reshape(1, -1)
        gen_question_vec = np.asarray(
            embedder.embed_documents(generated_questions)
        ).reshape(len(generated_questions), -1)
        norm = np.linalg.norm(gen_question_vec, axis=1) * np.linalg.norm(
            question_vec, axis=1
        )
        return (
            np.dot(gen_question_vec, question_vec.T).reshape(
                -1,
            )
            / norm
        )

    def evaluate(self, run: Run, example: Example) -> EvaluationResult:
        question = example.inputs["question"]
        answer = run.outputs["final_answer"]  # type: ignore

        generated_questions: list[GeneratedQuestion] = question_generator.batch(
            [{"answer": answer} for _ in range(self.strictness)]
        )  # type: ignore

        non_committal = np.any(
            [question.non_committal for question in generated_questions]
        )

        if all(q == "" for q in generated_questions):
            raise ValueError("No questions generated")

        if non_committal:
            return EvaluationResult(
                key=self.__class__.__name__,
                score=0,
                comment="Non committal answer",
            )

        similarities = self._calculate_similarity(
            question,
            [generated_question.question for generated_question in generated_questions],
        )
        score = similarities.mean()
        return EvaluationResult(key=self.__class__.__name__, score=score)


class LLMCorrectness(BaseEvaluator):
    """
    Evaluates the correctness of the answer with respect to the reference answer.
    It makes sure that all the facts present in the reference answer are also present in the generated answer.

    Scores between 0 and 1
    """

    def __init__(self):
        self.sentence_segmenter = Segmenter()

    def _decompose_into_sentences(self, question: str, answer: str) -> list[str]:
        sentences = self.sentence_segmenter.segment(answer)
        sentences_with_indices = {
            idx: statement for idx, statement in enumerate(sentences)
        }

        res: SimplifiedSentenceOutput = sentence_simplifier.invoke(
            {
                "question": question,
                "answer": answer,
                "sentences": sentences_with_indices,
            }
        )  # type: ignore

        simplified_sentences = []
        for sentence in res.simplified_sentences:
            simplified_sentences.extend(sentence.simplified_sentences)
        return simplified_sentences

    def evaluate(self, run: Run, example: Example) -> EvaluationResult:
        question = example.inputs["question"]
        reference_answer = example.outputs["answer"]  # type: ignore
        answer = run.outputs["final_answer"]  # type: ignore

        simplified_sentences = self._decompose_into_sentences(
            question, reference_answer
        )

        verdicts: FaithfulnessVerdictOutput = faithfulness_verdict.invoke(
            {"context": answer, "statements": simplified_sentences}
        )  # type: ignore
        num_faithful = sum([verdict.verdict for verdict in verdicts.verdicts])
        num_statements = len(simplified_sentences)

        return EvaluationResult(
            key=self.__class__.__name__,
            score=num_faithful / num_statements,
            comment=f"{num_faithful} out of {num_statements} statements are present in the answer",
        )
