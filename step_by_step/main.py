import re
import time

from termcolor import colored

from drop.drop import *
from gpt.gpt import prompt_completion_chat
from step_by_step.next_step import *
from step_by_step.problem import *
from utils.filer import *


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


def reflect_on_problem(problem: Problem, solved_correctly: bool):
    problem.solved_correctly = solved_correctly
    # TODO reflect on each step


if __name__ == "__main__":
    # Logging what paths it takes:
    paths = []
    problems = []

    for i in range(10):
        start_time = time.time()

        drop_data = download_data()
        passage_id, passage_text, question, answer = sample_questions(drop_data, 1)[0]
        question_id = passage_id + "_" + re.sub("\W", "_", question[:40])
        prompt = format_prompt(passage_text, question)

        problem = Problem(prompt)
        problem.types_of_steps = define_step_types()
        print(f"Problem {i}:", problem.problem_text)
        solve_problem_for_train(problem, randomness=0.0)
        save_to_file("../saved_runs/" + question_id + ".json", json.dumps(problem, default=lambda o: o.__dict__, sort_keys=True, indent=4))
        print("Final answer:", problem.final_answer)
        problem.solved_correctly = is_correct_answer(problem.final_answer, answer)
        print("Compare correct answer: ", answer, "Correct? ", problem.solved_correctly)
        print(f"Took time: {time.time() - start_time} seconds\n")

        # Add to log
        paths.append(question + ":\n" + "\n".join(["* " + step.type_of_step.name for step in problem.steps]) + "\n" + str(problem.solved_correctly))
        problems.append(problem)

    print("Paths taken:")
    print("\n\n".join(paths))

    print(f"Num correct: {sum([1 for problem in problems if problem.solved_correctly])} / {len(problems)}")
