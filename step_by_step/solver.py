import random

from gpt.gpt import prompt_completion_chat
from step_by_step.next_step import choose_step_type
from step_by_step.problem import *
from termcolor import colored


def solve_problem_for_train(problem: Problem, randomness=0.1):
    while True:
        if random.random() < randomness:  # Mix it up sometimes, for exploration
            step_type = random.choice(problem.types_of_steps)
        elif len(problem.steps) > 4:  # That's enough steps
            step_type = next(step_type for step_type in problem.types_of_steps if step_type.is_final)
        else:
            step_type = choose_step_type(problem)
        if step_type.is_final and len(problem.steps) == 0:
            step_type = random.choice([step_type for step_type in problem.types_of_steps if not step_type.is_final])  # Always do at least one step

        print("Next step:", step_type.name)

        # Complete this step with chat
        messages = problem.messages_for_chat()
        messages.append({"role": "user", "content": step_type.text})
        response = prompt_completion_chat(messages=messages)
        print(colored(f"Got response: {response}", "blue"))
        step = Step(step_type)
        step.step_response = response
        problem.steps.append(step)

        if step_type.is_final:
            problem.final_answer = response
            break
