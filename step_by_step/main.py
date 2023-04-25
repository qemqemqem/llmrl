import re
import time

from drop.drop import *
from step_by_step.next_step import *
from step_by_step.reflecting import reflect_on_finished_problem
from step_by_step.solver import *
from utils.filer import *

if __name__ == "__main__":
    # Logging what paths it takes:
    paths = []
    problems = []

    drop_data = download_data()
    num_questions = 10

    # Sample outside the loop to avoid duplicates
    question_tuples = sample_questions(drop_data, num_questions)

    for i in range(num_questions):
        start_time = time.time()

        # Choose and create a Problem
        passage_id, passage_text, question, answer = question_tuples[i]
        question_id = passage_id + "_" + re.sub("\W", "_", question[:40])
        prompt = format_prompt(passage_text, question)
        problem = Problem(prompt)
        problem.types_of_steps = define_step_types()
        print(f"Problem {i}:", problem.problem_text)
        solve_problem_for_train(problem, randomness=0.0)

        # Reflect
        problem.gold_correct_answer = answer
        problem.solved_correctly = is_correct_answer(problem.final_answer, answer)
        reflect_on_finished_problem(problem, answer)

        # Save to file
        save_to_file("../saved_runs/" + question_id + ".json", json.dumps(problem, default=lambda o: o.__dict__, sort_keys=True, indent=4))

        # Print how we did
        print("Final answer:", problem.final_answer)
        print("Compare correct answer: ", answer, "Correct? ", problem.solved_correctly)
        print(f"Took time: {time.time() - start_time} seconds\n")

        # Add to log
        paths.append(question + ":\n" + "\n".join(["* " + step.type_of_step.name for step in problem.steps]) + "\n" + str(problem.solved_correctly))
        problems.append(problem)

    # Final summary
    print("Paths taken:")
    print("\n\n".join(paths))
    print(f"Num correct: {sum([1 for problem in problems if problem.solved_correctly])} / {len(problems)}")
