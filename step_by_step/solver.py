import random

from termcolor import colored

from gpt.gpt import prompt_completion_chat
from step_by_step.next_step import choose_step_type
from step_by_step.problem import *


def solve_problem_for_train(problem: Problem, randomness=0.1, max_steps=5, min_steps=1):
    while True:
        if random.random() < randomness:  # Mix it up sometimes, for exploration
            step_type = random.choice(problem.types_of_steps)
        elif len(problem.steps) >= max_steps:  # That's enough steps, final now
            step_type = next(step_type for step_type in problem.types_of_steps if step_type.is_final)
        else:
            step_type = choose_step_type(problem)
        if step_type.is_final and len(problem.steps) < min(min_steps, max_steps):
            # Always do at least min_steps steps before the final answer
            step_type = random.choice([step_type for step_type in problem.types_of_steps if not step_type.is_final])

        print("Next step:", step_type.name)

        # Complete this step with chat
        messages = problem.messages_for_chat()
        st = step_type.text
        if step_type.is_final and problem.question_alone is not None:
            st += "\n\nQuestion: " + problem.question_alone
        print("Step text: ", st)
        messages.append({"role": "user", "content": st})
        response = prompt_completion_chat(messages=messages)
        print(colored(f"Got response: {response}", "blue"))
        step = Step(step_type)
        step.step_response = response
        problem.steps.append(step)

        if step_type.is_final:
            problem.final_answer = response
            break
