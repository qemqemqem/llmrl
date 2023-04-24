import json
import os
import random
import zipfile

import inflect
import openai
import requests

# Install the openai package if not already installed
# !pip install openai

# Set up your API key for OpenAI
openai.api_key = os.environ["OPENAI_API_KEY"]

# Download the DROP dataset if it's not saved locally
drop_data_url = "https://s3-us-west-2.amazonaws.com/allennlp/datasets/drop/drop_dataset.zip"
drop_filename = "drop_dataset.zip"
train_data_file = "drop_dataset_train.json"

if not os.path.exists("drop_dataset/" + train_data_file):
    print("Downloading DROP dataset...")
    response = requests.get(drop_data_url)
    with open(drop_filename, "wb") as f:
        f.write(response.content)

    # Unzip the dataset
    with zipfile.ZipFile(drop_filename, "r") as zip_ref:
        zip_ref.extractall(".")

# Load the dataset
with open("drop_dataset/" + train_data_file, "r") as f:
    drop_data = json.load(f)


# Function to answer a question using the OpenAI API
def answer_question(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
    )
    answer = response.choices[0].text.strip()
    return answer


num_random_questions = 10

# Randomly select 10 questions from the DROP dataset
random_passages = random.sample(list(drop_data.items()), num_random_questions)  # We'll use one question from each passage

correct = 0
total = 0

# Create an inflect engine to convert numbers
inflect_engine = inflect.engine()


def is_correct_answer(predicted_answer, gold_answers):
    # Check if the predicted answer matches any of the gold numbers or their word forms
    correct_numbers = [gold_answers["number"], inflect_engine.number_to_words(gold_answers["number"])]
    # for number in gold_answers["number"]:
    #     correct_numbers.append(inflect_engine.number_to_words(number))

    for number in correct_numbers:
        # TODO This isn't correct (3 != 37), but it's good enough for now
        if number.lower() in predicted_answer.lower().replace(",", ""):
            return True

    # Check if the predicted answer matches any of the gold text spans
    for span in gold_answers["spans"]:
        if predicted_answer.lower() == span.lower():
            return True

    return False


# Iterate through the selected questions and answer them using the OpenAI API
for passage_id, passage_data in random_passages:
    passage_text = passage_data["passage"]

    # for qa_pair in passage_data["qa_pairs"]:
    good_questions = [pd for pd in passage_data["qa_pairs"] if pd["answer"]["number"] != ""]
    if len(good_questions) == 0:
        continue  # Skip this passage if it doesn't have any good questions. Oh well.
    qa_pair = random.choice(good_questions)

    question = qa_pair["question"]

    # Create a prompt for the OpenAI API
    prompt = f"{passage_text}\nQuestion: {question}\nAnswer (digits only):"

    # Get the answer from the OpenAI API
    predicted_answer = answer_question(prompt)

    # Evaluate the answer for correctness
    is_correct = is_correct_answer(predicted_answer, qa_pair["answer"])
    if is_correct:
        correct += 1
    total += 1

    # Print the results
    print(f"Question: {question}\nPassage: {passage_text}\n{'✔️' if is_correct else '❌'} Answer: {predicted_answer} (correct: {qa_pair['answer']['number']})\n")

# Calculate the accuracy
accuracy = correct / total
print(f"Accuracy: {accuracy:.2f}")
