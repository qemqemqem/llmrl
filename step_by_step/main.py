import re
import time

from drop.drop import *
from step_by_step.next_step import *
from step_by_step.reflecting import reflect_on_finished_problem, reflect_on_each_step
from step_by_step.solver import *
from utils.filer import *
import os

def parseids_from_directory(directory:str):
    #get all the file names in this directory that end in .json
    file_names = [f for f in os.listdir(directory) if f.endswith(".json")]
    #keep everything before the second underscore
    question_ids = [f.split("_")[0] + "_" + f.split("_")[1] for f in file_names]
    return question_ids

def run(num_questions, max_steps, directory = None, aligned_directory = None):
    paths = []
    problems = []
    step_choices = []

    drop_data = download_data()
    num_questions = num_questions
    max_steps = max_steps
    if (directory=="") | (directory==None):
        directory = "saved_runs_maxsteps_{}/".format(max_steps)
    if not os.path.exists(directory):
        os.makedirs(directory)

    assert aligned_directory != directory, "Aligned directory and save directory cannot be the same"

    if aligned_directory!=None:
        aligned_ids = parseids_from_directory(aligned_directory)
        subset_drop_data = {k: drop_data[k] for k in aligned_ids if k in drop_data}
        question_tuples = select_questions(list(subset_drop_data.items())[0:num_questions], num_questions)
    else:
        # Sample outside the loop to avoid duplicates
        question_tuples = sample_questions(drop_data, num_questions)

    ###actual extraction below

    for i in range(num_questions):
        start_time = time.time()

        # Choose and create a Problem
        passage_id, passage_text, question, answer = question_tuples[i]
        question_id = passage_id + "_" + re.sub("\W", "_", question[:40])
        prompt = format_prompt(passage_text, question)
        problem = Problem(prompt)
        problem.types_of_steps = define_step_types()
        print(f"Problem {i}:", problem.problem_text)
        solve_problem_for_train(problem, randomness=0.0, max_steps=max_steps)

        # Reflect
        problem.gold_correct_answer = answer
        problem.solved_correctly = is_correct_answer(problem.final_answer, answer)
        if max_steps > 0:  # nothing to think about
            reflect_on_finished_problem(problem)
            reflect_on_each_step(problem)

        # Save to file
        save_to_file(directory + question_id + ".json",
                     json.dumps(problem, default=lambda o: o.__dict__, sort_keys=True, indent=4))

        # Print how we did
        print("Final answer:", problem.final_answer)
        print("Compare correct answer: ", answer, "Correct? ", problem.solved_correctly)
        print(f"Took time: {time.time() - start_time} seconds\n")

        # Add to log
        paths.append(
            question + ":\n" + "\n".join(["* " + step.type_of_step.name for step in problem.steps]) + "\n" + str(
                problem.solved_correctly))
        problems.append(problem)
        for step in problem.steps:
            step_choices.append(step.type_of_step.name)

    # Final summary
    print("Step choice counts:")
    # Counts
    print("\n".join([f"* {choice}: {step_choices.count(choice)}" for choice in
                     sorted(list(set(step_choices)), key=lambda x: step_choices.count(x), reverse=True)]))
    # print("Paths taken:")
    # print("\n\n".join(paths))
    print(f"\nNum correct: {sum([1 for problem in problems if problem.solved_correctly])} / {len(problems)}")


if __name__ == "__main__":
    #run(num_questions=500,max_steps= 0, directory= None, aligned_directory=None)
    run(num_questions=50,max_steps= 0, directory= "saved_runs_maxsteps_0_alt/", aligned_directory="saved_runs")
