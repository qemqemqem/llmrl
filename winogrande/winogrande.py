# Data from https://winogrande.allenai.org/

import json
import os
import random

import openai

# Replace 'your_api_key_here' with your actual OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

# Load the dataset
with open("/home/keenan/Downloads/winogrande_1.1/winogrande_1.1/dev.jsonl", "r") as file:
    dataset = [json.loads(line) for line in file]


def get_random_questions(num_questions):
    # Randomly choose 100 questions
    random_questions = random.sample(dataset, num_questions)
    if num_questions > len(dataset):
        print(f"Warning: num_questions ({num_questions}) is greater than the number of questions in the dataset ({len(dataset)}).")
    return random_questions


# Function to generate answers using the OpenAI API
def generate_answer(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].text.strip()


# Function to check if the generated answer is correct
def is_correct_answer(generated_answer, correct_option, option1, option2):
    if correct_option == '1' and generated_answer.lower() == option1.lower():
        return True
    if correct_option == '2' and generated_answer.lower() == option2.lower():
        return True
    return False


if __name__ == "__main__":
    # Iterate through the randomly chosen questions, generate answers, and check correctness
    correct_count = 0
    random_questions = get_random_questions(10)
    for question in random_questions:
        prompt = f"Question: {question['sentence']} Options: {question['option1']} or {question['option2']}? Answer:"
        answer = generate_answer(prompt)
        correct = is_correct_answer(answer, question['answer'], question['option1'], question['option2'])

        if correct:
            correct_count += 1

        print(f"Prompt: {prompt}\nGenerated Answer: {answer}\nCorrect: {'✅' if correct else '❌'}, ({question['option1'] if question['answer'] == 1 else question['option2']})\n")

    # Calculate and print the accuracy
    accuracy = (correct_count / len(random_questions)) * 100
    print(f"Accuracy: {accuracy:.2f}%")
