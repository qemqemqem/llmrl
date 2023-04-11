import os

import openai
from langchain.llms import OpenAI

from winogrande.winogrande import get_random_questions, eval_answers_against_questions

openai.api_key = os.environ["OPENAI_API_KEY"]

llm = OpenAI(temperature=0.9)

templates = [
    "Think this question through carefully: {prompt}",
    "Thing this through step by step: {prompt}",
    "What is the answer to this question: {prompt}",
    "What is the correct answer to this question: {prompt}",
    "Do a good job with this, it's important: {prompt}",
    "Please choose an answer randomly: {prompt}",
]

for template in templates:
    num_questions = 10
    winogrande_questions = get_random_questions(num_questions)
    answers = []
    for question in winogrande_questions:
        prompt = template.format(prompt=question["sentence"])
        answers.append(llm(prompt))
    correct_count = eval_answers_against_questions(answers, winogrande_questions)
    print(f"Template: {template} Number correct: {correct_count}/{num_questions}")
