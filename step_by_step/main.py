import json
import random

from gpt.gpt import prompt_completion_chat
from utils.filer import *


class StepType:
    def __init__(self, name: str, text: str, is_final: bool = False):
        self.name: str = name
        self.text: str = text
        self.is_final: bool = is_final  # If True, this is the last step in the problem, and the answer is the answer to the Problem

        if not is_final:
            self.text += " I don't want you to find the final answer, just this step."

        self.text += " Please be concise."


class Step:
    def __init__(self, type_of_step: StepType):
        self.type_of_step: StepType = type_of_step
        self.step_response: str = ""

        # These are used during reflection after the problem is solved and the answer is checked
        self.was_useful: bool = False
        self.usefulness_commentary: str = ""


class Problem:
    def __init__(self, problem_text: str):
        self.problem_text: str = problem_text
        self.steps: list[Step] = []
        self.solved_correctly: bool = False
        self.commentary_on_process: str = ""
        self.types_of_steps: list[StepType] = []
        self.final_answer = ""

    def messages_for_chat(self):
        messages = [
            {"role": "system", "content": "You are a thoughtful question answering bot. You give short but correct answers to questions. You like to think things through carefully."},
            {"role": "user", "text": self.problem_text},
            {"role": "assistant", "text": "I need to think this through step by step."},
        ]
        for step in self.steps:
            messages.append({"role": "user", "text": step.type_of_step.text})
            messages.append({"role": "assistant", "text": step.step_response})
        return messages


def choose_step_type(problem: Problem) -> StepType:
    return random.choice(problem.types_of_steps)  # TODO Call out to ChatGPT


def solve_problem_for_train(problem: Problem):
    while True:
        if random.random() < 0.1:  # Mix it up sometimes, for exploration
            step_type = random.choice(problem.types_of_steps)
        elif len(problem.steps) > 4:  # That's enough steps
            step_type = next(step_type for step_type in problem.types_of_steps if step_type.is_final)
        else:
            step_type = choose_step_type(problem)
        if step_type.is_final and len(problem.steps) == 0:
            step_type = random.choice([step_type for step_type in problem.types_of_steps if not step_type.is_final])  # Always do at least one step

        print("Next step type:", step_type.name)

        # Complete this step with chat
        messages = problem.messages_for_chat()
        messages.append({"role": "user", "text": step_type.text})
        response = prompt_completion_chat(messages)
        print("Got response:", response)
        step = Step(step_type)
        step.step_response = response
        problem.steps.append(step)

        if step_type.is_final:
            problem.final_answer = response
            break


def reflect_on_problem(problem: Problem, solved_correctly: bool):
    problem.solved_correctly = solved_correctly
    # TODO reflect on each step


if __name__ == "__main__":
    problem = Problem("Rhonda has 12 marbles more than Douglas. Douglas has 6 marbles more than Bertha. Rhonda has twice as many marbles as Bertha has. How many marbles does Douglas have?")
    problem.types_of_steps = [
        StepType("strategy", "What is the best strategy to solve this problem?"),
        StepType("obvious answer", "What is the obvious answer to this problem?"),
        StepType("math", "Step through the math to solve this problem."),
        StepType("guess and check", "Guess and check to solve this problem."),
        StepType("find the trick", "I think there might be a clever trick for solving this problem. What is it?"),
        StepType("more information", "What other information might help us solve this problem?"),
        StepType("ready to find answer", "Given what we know, what is the answer to this problem?", is_final=True),
    ]
    print("Problem:", problem.problem_text)
    solve_problem_for_train(problem)
    print(problem)
    save_to_file("../saved_runs/marbles_count.json", json.dumps(problem, default=lambda o: o.__dict__, sort_keys=True, indent=4))
    print("Final answer:", problem.final_answer)
