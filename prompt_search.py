import os
import random
import re

import openai
from langchain.llms import OpenAI

from winogrande.winogrande import get_random_questions, eval_answers_against_questions

openai.api_key = os.environ["OPENAI_API_KEY"]

llm = OpenAI(temperature=0.9)


def extract_bracket_words(string):
    return [word.strip('{}') for word in re.findall(r'{\s*\w+\s*}', string)]


class Template:
    def __init__(self, named_output, template):
        self.named_output = named_output
        self.template = template
        self.input_variables = extract_bracket_words(template)

    def format(self, **kwargs):
        return self.template.format(**kwargs)


class AnswerChainSearcher:
    def __init__(self):
        self.templates: list[Template] = []

    def try_answer(self, prompt: str, answer: str):
        known_data = {"prompt": prompt}
        sequence = []
        while "answer" not in known_data:
            # Pick a random template for now
            template = random.choice(self.templates)
            sequence.append(template)
            prompt = template.format(**known_data)
            known_data[template.named_output] = llm(prompt)
        return sequence, known_data["answer"]

    def teach(self, sequence, answer):
        pass


templates = [
    Template("answer", "Think this question through carefully: {prompt}"),
    Template("answer", "Thing this through step by step: {prompt}"),
    Template("answer", "What is the answer to this question: {prompt}"),
    Template("answer", "What is the correct answer to this question: {prompt}"),
    Template("answer", "Do a good job with this, it's important: {prompt}"),
    Template("answer", "Please choose an answer randomly: {prompt}"),
]

if __name__ == "__main__":
    num_questions = 10

    answer_searcher = AnswerChainSearcher()
    answer_searcher.templates = templates
    winogrande_questions = get_random_questions(num_questions)
    sequences = []
    answers = []
    for question in winogrande_questions:
        sequence, answer = answer_searcher.try_answer(question["sentence"], question["answer"])
        sequences.append(sequence)
        answers.append(answer)
    correct_count = eval_answers_against_questions(answers, winogrande_questions)
    print(f"Number correct: {correct_count}/{num_questions}")

    # for template in templates:
    #     winogrande_questions = get_random_questions(num_questions)
    #     answers = []
    #     for question in winogrande_questions:
    #         prompt = template.format(prompt=question["sentence"])
    #         answers.append(llm(prompt))
    #     correct_count = eval_answers_against_questions(answers, winogrande_questions)
    #     print(f"Template: {template} Number correct: {correct_count}/{num_questions}")
