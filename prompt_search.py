import os
import random
import re

import openai
from langchain.llms import OpenAI

from winogrande.winogrande import get_random_questions, eval_answer_against_question

openai.api_key = os.environ["OPENAI_API_KEY"]

# A high temperature is worse but noisier, which gives us more data because it increases entropy
llm = OpenAI(temperature=0.9)


def extract_bracket_words(string):
    return [word.strip('{}') for word in re.findall(r'{\s*\w+\s*}', string)]


class Template:
    def __init__(self, named_output, template):
        self.named_output = named_output
        self.template = template
        self.input_variables = extract_bracket_words(template)
        self.num_participations = 0
        self.num_correct = 0

    def format(self, **kwargs):
        return self.template.format(**kwargs)

    def __repr__(self):
        shortened = self.template.replace("\n", " ")[0:20]
        return f"Template({self.named_output}, {shortened})"

    def key(self):
        return self.template.replace("\n", " ").replace(",", "").replace("\"", "")

    def performance(self):
        if self.num_participations == 0:
            return 1.0  # Optimism!
        raw_performance = self.num_correct / self.num_participations
        return raw_performance ** 2


class AnswerChainSearcher:
    def __init__(self):
        self.templates: list[Template] = []

    def try_answer(self, prompt: str, answer: str):
        known_data = {"prompt": prompt}
        sequence = []
        while "answer" not in known_data:
            # Pick a random template biased by performance
            template = random.choices(self.templates, weights=[template.performance() for template in self.templates])[0]
            # Make sure we have all the data we need
            if not all(variable in known_data for variable in template.input_variables):
                continue
            # Make sure we're not overwriting anything
            if template.named_output in known_data:
                continue
            sequence.append(template)
            prompt = template.format(**known_data)
            known_data[template.named_output] = llm(prompt)
        return sequence, known_data["answer"]

    def teach(self, sequence, answer, correct):
        for template in sequence:
            template.num_participations += 1
            if correct:
                template.num_correct += 1

    def load_template_data_from_file(self, filename):
        # Return early if the file doesn't exist
        if not os.path.exists(filename):
            return
        with open(filename, "r") as f:
            for line in f:
                key, num_correct, num_participations, _ = line.split(",")
                # Find matching template
                for template in self.templates:
                    if template.key() == key:
                        template.num_correct = int(num_correct)
                        template.num_participations = int(num_participations)

    def save_template_data_to_file(self, filename):
        with open(filename, "w") as f:
            for template in self.templates:
                f.write(f"{template.key()},{template.num_correct},{template.num_participations},{template.num_correct / template.num_participations * 100:.2f}\n")


templates = [
    # Template("answer", "Think this question through carefully: {prompt}"),
    # Template("answer", "Thing this through step by step: {prompt}"),
    # Template("answer", "What is the answer to this question: {prompt}"),
    # Template("answer", "What is the correct answer to this question: {prompt}"),
    # Template("answer", "Do a good job with this, it's important: {prompt}"),
    # Template("answer", "Please choose an answer randomly: {prompt}"),
    Template("strategy", "What is the best strategy to solve this problem: {prompt}"),
    Template("strategy", "What is the best way to solve this problem: {prompt}"),
    Template("emotion", "What is the best emotion to feel about this problem: {prompt}"),
    Template("tricky", "Why is this problem tricky?: {prompt}"),
    Template("tricky", "Why is this problem hard?: {prompt}"),
    Template("thoughts", "Using this strategy: {strategy}\n\nAnswer this question: {prompt}"),
    Template("thoughts", "The trick to this problem is: {tricky}\n\nAnswer this question: {prompt}"),
    Template("thoughts", "The best emotion to feel about this problem is: {emotion}\n\nAnswer this question: {prompt}"),
    Template("answer", "You have these thoughts{thoughts}\n\nGive a short and correct answer: {prompt}\n\nAnswer:"),
]

if __name__ == "__main__":
    num_questions = 1000
    save_file = "template_data.csv"

    answer_searcher = AnswerChainSearcher()
    answer_searcher.templates = templates
    answer_searcher.load_template_data_from_file(save_file)
    winogrande_questions = get_random_questions(num_questions)
    correct_count = 0
    for i, question in enumerate(winogrande_questions):
        sequence, answer = answer_searcher.try_answer(question["sentence"], question["answer"])
        if answer.strip() == "":
            print("\n\nEmpty answer! :(\n\n")
        is_correct, correct_answer = eval_answer_against_question(answer[:20], question)
        print(f"{'✅' if is_correct else '❌'}: Answer/Correct: {answer.strip()}/{correct_answer} using Sequence: {sequence} from \"{question['sentence']}\"")
        correct_count += is_correct
        # Teaching
        answer_searcher.teach(sequence, answer, is_correct)
        if (i + 1) % 10 == 0 or i == num_questions - 1:
            print(f"Number correct: {correct_count}/{i + 1}")
            # Save the template data to a file
            answer_searcher.save_template_data_to_file(save_file)
    print(f"Number correct: {correct_count}/{num_questions}")

    # How did the templates do?
    for template in templates:
        print(f"Template: {template} Number correct: {template.num_correct}/{template.num_participations} == {template.num_correct / template.num_participations * 100:.2f}%")
