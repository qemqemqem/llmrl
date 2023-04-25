import re
import time

from drop.drop import *
from step_by_step.next_step import *
from step_by_step.problem import *
from step_by_step.solver import *
from utils.filer import *


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
