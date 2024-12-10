from nodes.question_decomposer import (
    question_decomposer,
    question_decomposer_v2,
)
import csv

with open("./testing_data/qa_pairs.csv", "r") as f:
    question_answer_pairs = list(csv.reader(f))
    question_answer_pairs = question_answer_pairs[1:]

questions = [pair[0] for pair in question_answer_pairs]
print(questions)
parallel_decomposed = question_decomposer.batch([{"question": q} for q in questions])
serial_decomposed = question_decomposer_v2.batch([{"question": q} for q in questions])

parallel_decomposed = [res.decomposed_questions for res in parallel_decomposed]
serial_decomposed = [res.decomposed_question_groups for res in serial_decomposed]

print(parallel_decomposed, serial_decomposed)

with open("results.csv", "w") as f:
    writer = csv.writer(f)
    for i in range(len(questions)):
        writer.writerow([questions[i], parallel_decomposed[i], serial_decomposed[i]])
