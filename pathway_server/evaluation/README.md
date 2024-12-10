# Evaluation

We have provided python scripts to easily replicate our evaluation results

## Running Instructions

To run end-to-end evaluation:
```
python3 -m evaluation.e2e
```

To run evaluations on retriever:
```
python3 -m evaluation.retrieval
```

## More on evaluation

### E2E evaluation

We evaluate our architecture based on 3 things:

1. Correctness 
2. Faithfulness
3. Response Relevancy

#### Correctness
This metric aims to calculate the **correctness of the generated answer** by comparing it to the reference answer.

For this, we first separate each sentence of the reference answer and simplify them. Then, we check if each of the facts in these sentences is present in the generated answer or not. The final score is the number of facts correctly generated / number of facts present in the reference answer.

Check out `evaluators.e2e_evaluators.LLMCorrectness()` for more information.

#### Faithfulness
This metric aims to **check if the generated answer has any hallucinations** in it. It finds the facts present in the generated answer and tries to check if they are also present in the retrieved contexts.

For this, we separate each sentence of the generated answer and simplify them. Then, we check if each of the facts in these sentences is present in the retrieved contexts or not. The final score is the **_number of facts correctly generated / number of facts present in the generated answer_**.

Check out `evaluators.e2e_evaluators.LLMFaithfulness()` for more information.

#### Response Relevancy
This metric aims to **check if the generated answer is relevant to the question asked**.

For this, we generate questions from the generated answer such that they would have the generated answer as their answer. Then, we compare the cosine similarity of these questions with our original question and take a mean over all the generated questions.

Check out `evaluators.e2e_evaluators.LLMResponseRelevancy()` for more information.

### Retriever evaluation

We use **_Levenshtein distance_** for this evaluation. Check out `retrieval.py` for more information.