import os
import random
import re

import openai
from langchain.llms import OpenAI

from winogrande.winogrande import get_random_questions, eval_answer_against_question

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

    def __repr__(self):
        shortened = self.template.replace("\n", " ")[0:20]
        return f"Template({self.named_output}, {shortened})"


class AnswerChainSearcher:
    def __init__(self):
        self.templates: list[Template] = []

    def try_answer(self, prompt: str, answer: str):
        known_data = {"prompt": prompt}
        sequence = []
        while "answer" not in known_data:
            # Pick a random template for now
            template = random.choice(self.templates)
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

    def teach(self, sequence, answer):
        pass


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
    num_questions = 10

    answer_searcher = AnswerChainSearcher()
    answer_searcher.templates = templates
    winogrande_questions = get_random_questions(num_questions)
    # sequences = []
    # answers = []
    correct_count = 0
    for question in winogrande_questions:
        sequence, answer = answer_searcher.try_answer(question["sentence"], question["answer"])
        if answer.strip() == "":
            print("Empty answer")
        # sequences.append(sequence)
        # answers.append(answer)
        is_correct, correct_answer = eval_answer_against_question(answer[:20], question)
        print(f"{'✅' if is_correct else '❌'}: Answer/Correct: {answer.strip()} / {correct_answer} using Sequence: {sequence}")
        correct_count += is_correct
    print(f"Number correct: {correct_count}/{num_questions}")
