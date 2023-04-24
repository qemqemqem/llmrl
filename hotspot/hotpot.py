import json
import os
import random
import openai
import requests

from hotspot.hotpot_evaluation import normalize_answer, f1_score, exact_match_score

# Load the dataset
with open("/home/keenan/Downloads/hotpot/hotpot_dev_distractor_v1.json", "r") as f:
    data = json.load(f)

# Initialize OpenAI API
openai.api_key = os.environ["OPENAI_API_KEY"]

# Select 100 random questions
random_questions = random.sample(data, 5)

# Function to call OpenAI Chat API
def answer_question(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].text.strip()

num_good_enough = 0

# Iterate through the questions and get answers
for question in random_questions:
    question_text = question["question"]
    context = ""
    for context_for_person in question["context"]:
        context += context_for_person[0] + ": " + " ".join(context_for_person[1]) + "\n"
    context = context.strip()
    prompt = f"Answer the following question based on the provided context:\n\nContext: {context}\n\nQuestion: {question_text}\n\nAnswer:"

    # Get the answer from the OpenAI Chat API
    prediction = answer_question(prompt)

    # Compare against the correct answer
    ground_truth = question["answer"]
    normalized_prediction = normalize_answer(prediction)
    normalized_ground_truth = normalize_answer(ground_truth)
    em = exact_match_score(prediction, ground_truth)
    subset_em = normalized_ground_truth in normalized_prediction
    f1, precision, recall = f1_score(prediction, ground_truth)
    good_enough = em or subset_em or recall > 0.5
    num_good_enough += 1 if good_enough else 0

    # Print
    print(f"Question: {question_text}\nContext: {context}\n{'✔️' if good_enough else '❌'} Answer: {prediction} (correct: {ground_truth})\n")

print(f"Num Good Enough: {num_good_enough / len(random_questions)}")