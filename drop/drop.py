import datetime
import json
import os
import random
import time
import typing
import zipfile

import inflect
import openai
import requests

# Install the openai package if not already installed
# !pip install openai

# Create an inflect engine to convert numbers.
# Do this at the top of the file because it's slow to create.
inflect_engine = inflect.engine()


def download_data():
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

    return drop_data


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


def contains_date(string, date):
    date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y',
                    '%d %B %Y', '%d %b %Y', '%B %d, %Y', '%b %d %Y']
    for format in date_formats:
        try:
            parsed_date = datetime.datetime.strptime(string, format).date()
            if parsed_date == date:
                return True
        except ValueError:
            pass
    return False


def is_correct_answer(predicted_answer, gold_answer):
    if gold_answer["number"] != '':
        # Handle the numeric case
        # Check if the predicted answer matches any of the gold numbers or their word forms
        correct_numbers = [gold_answer["number"], inflect_engine.number_to_words(gold_answer["number"])]
        # for number in gold_answers["number"]:
        #     correct_numbers.append(inflect_engine.number_to_words(number))

        # For each variation on the correct answer, see if it appears in the predicted answer
        for number in correct_numbers:
            # TODO This isn't correct (e.g. 3 != 37), but it's good enough for now
            if number.lower() in predicted_answer.lower().replace(",", ""):
                return True
        return False

    if len(gold_answer["spans"]) > 0:
        # Check if the predicted answer matches all the gold text spans
        # This is also not correct for the same reason as above
        for span in gold_answer["spans"]:
            if span.lower() not in predicted_answer.lower():
                return False
        return True

    if "day" in gold_answer["date"] and gold_answer["date"]["day"] != "" and gold_answer["date"]["month"] != "" and gold_answer["date"]["year"] != "":
        try:
            month_str = gold_answer['date']['month']
            month_num = datetime.datetime.strptime(month_str, '%B').month
            date_obj = datetime.date(int(gold_answer['date']['year']), month_num, int(gold_answer['date']['day']))
            return contains_date(predicted_answer, date_obj)
        except ValueError:
            print("Error parsing date: " + str(gold_answer['date']))
            return False

    if "day" in gold_answer["date"] and (gold_answer["date"]["day"] != "" or gold_answer["date"]["month"] != "" or gold_answer["date"]["year"] != ""):
        date_str = gold_answer["date"]["day"] + " " + gold_answer["date"]["month"] + " " + gold_answer["date"]["year"]
        # Sometimes only the month is populated
        date_str = date_str.strip()
        return date_str.lower() in predicted_answer.lower()

    print("Error: unknown answer type: " + str(gold_answer))
    return False
    # assert False, "Unknown answer type " + str(gold_answer)


def filter_by_answer_type(types: list[str]):
    def filter_func(qa_pair, passage_id=""):
        answer = qa_pair["answer"]
        types_inr = types
        if types == []:
            types_inr = ["number", "span", "date"]  # Accept all
        if "number" in types_inr:
            if answer["number"] != "":
                return True
        if "span" in types_inr:
            if len(answer["spans"]) > 0:
                return True
        if "date" in types_inr:
            if "day" in answer["date"] and answer["date"]["day"] != "" and answer["date"]["month"] != "" and answer["date"]["year"] != "":
                return True
        return False

    return filter_func


def sample_questions(drop_data, num_random_questions, filter_func: typing.Optional[typing.Callable[[dict, str], bool]] = None):
    total_num_questions = 0
    num_questions_looked_at = 0
    question_answer_pairs = []
    num_numeric = 0
    num_span = 0
    num_multi_span = 0
    num_date = 0
    for passage_id, passage_data in drop_data.items():
        if filter_func is None:
            total_num_questions += len(passage_data["qa_pairs"])
        else:
            total_num_questions += len([qa_pair for qa_pair in passage_data["qa_pairs"] if filter_func(qa_pair, passage_id)])
    print(f"Total number of DROP questions available: {total_num_questions}")
    # Iterate over each question for each passage. This isn't the optimal algorithm, but that's fine.
    for passage_id, passage_data in drop_data.items():
        passage_text = passage_data["passage"]
        for qa_pair in passage_data["qa_pairs"]:
            if filter_func is not None and not filter_func(qa_pair, passage_id):
                continue
            ans = None
            if qa_pair["answer"]["number"] != "":
                num_numeric += 1
                ans = qa_pair["answer"]["number"]
            if len(qa_pair["answer"]["spans"]) == 1:
                num_span += 1
                ans = qa_pair["answer"]["spans"][0]
            if len(qa_pair["answer"]["spans"]) > 1:
                num_multi_span += 1
                ans = ", ".join(qa_pair["answer"]["spans"])
            if "day" in qa_pair["answer"]["date"] and qa_pair["answer"]["date"]["day"] != "":
                num_date += 1
                ans = qa_pair["answer"]["date"]
            # This check guarantees that we'll end up with the right number of questions
            if random.random() < (num_random_questions - len(question_answer_pairs)) / (total_num_questions - num_questions_looked_at):
                question = qa_pair["question"]
                answer = qa_pair["answer"]
                question_answer_pairs.append((passage_id, passage_text, question, answer))
            num_questions_looked_at += 1
    print(f"Number of numeric questions: {num_numeric}")
    print(f"Number of span questions: {num_span}")
    print(f"Number of date questions: {num_date}")
    print(f"Number of multi-span questions: {num_multi_span}")
    return question_answer_pairs


def format_prompt(passage_text, question):
    return f"Context:\n{passage_text}\n\nQuestion:\n{question}"


def drop_test():
    drop_data = download_data()

    num_random_questions = 10

    # Randomly select 10 questions from the DROP dataset
    random_passages = random.sample(list(drop_data.items()), num_random_questions)  # We'll use one question from each passage

    correct = 0
    total = 0

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


if __name__ == '__main__':
    # drop_test()
    drop_data = download_data()
    start_time = time.time()
    random_questions = sample_questions(drop_data, 100000, filter_func=filter_by_answer_type(["number", "span", "date"]))
    print(f"Sampled {len(random_questions)} questions from the DROP dataset.")
    print(f"Time elapsed: {time.time() - start_time:.2f} seconds")
    num_correct = 0
    for passage_id, passage_text, question, answer in random_questions:
        correct = is_correct_answer("5", answer)
        if correct:
            num_correct += 1
    print(f"Num correct: {num_correct} / {len(random_questions)}")
