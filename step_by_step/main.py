import re
import typing
from collections import defaultdict

from drop.drop import *
from step_by_step.finetuning import load_all_files_in_directory, parse_file_as_json
from step_by_step.next_step import *
from step_by_step.reflecting import reflect_on_finished_problem, reflect_on_each_step
from step_by_step.solver import *
from utils.filer import *
from utils.thread_helper import api_call_limited_parallel


def compute_accuracy_on_all_files():
    all_files = load_all_files_in_directory("saved_runs")
    num_correct = 0
    num_total = 0
    for filename, file in all_files.items():
        problem = parse_file_as_json(file)
        if problem["solved_correctly"]:
            num_correct += 1
        num_total += 1
    print(f"Num correct: {num_correct} / {num_total} = {num_correct / num_total * 100:.2f}%")


def compute_per_step_accuracy(save_dir="saved_runs"):
    all_files = load_all_files_in_directory(save_dir)
    num_useful = defaultdict(int)
    num_correct = defaultdict(int)
    num_total = defaultdict(int)
    for filename, file in all_files.items():
        problem = parse_file_as_json(file)
        for step in problem["steps"]:
            if step["was_useful"]:
                num_useful[step["type_of_step"]["name"]] += 1
            if problem["solved_correctly"]:
                num_correct[step["type_of_step"]["name"]] += 1
            num_total[step["type_of_step"]["name"]] += 1
    print(f"Useful / Total = Usefulness\t\tCorrect / Total = Accuracy\t\tStep")
    print(f"--------------------------------------------------------------")
    for step in sorted(num_total.keys(), key=lambda x: num_total[x]):
        print(f"{num_useful[step]} / {num_total[step]} = {num_useful[step] / num_total[step] * 100:.2f}%\t\t{num_correct[step]} / {num_total[step]} = {num_correct[step] / num_total[step] * 100:.2f}%\t\t{step}")


class RunsLogger:
    def __init__(self):
        # Logging what paths it takes:
        self.paths = []
        self.problems = []
        self.step_choices = []

    def print_summary(self):
        print("Step choice counts:")
        # Counts
        print("\n".join([f"* {choice}: {self.step_choices.count(choice)}" for choice in sorted(list(set(self.step_choices)), key=lambda x: self.step_choices.count(x), reverse=True)]))
        # print("Paths taken:")
        # print("\n\n".join(paths))
        print(f"\nNum correct: {sum([1 for problem in self.problems if problem.solved_correctly])} / {len(self.problems)}")


def train_on_question(passage_id, passage_text, question, answer, save_dir, logger: RunsLogger = None):
    start_time = time.time()

    # Create a Problem
    question_id = passage_id + "_" + re.sub("\W", "_", question[:40])
    prompt = format_prompt(passage_text, question)
    problem = Problem(prompt, question_alone=question)
    problem.types_of_steps = define_step_types()
    solve_problem_for_train(problem, randomness=0.0)

    # Reflect
    problem.gold_correct_answer = answer
    problem.solved_correctly = is_correct_answer(problem.final_answer, answer)
    reflect_on_finished_problem(problem)
    reflect_on_each_step(problem)

    # Save to file
    if save_dir is not None:
        save_to_file(save_dir + question_id + ".json", json.dumps(problem, default=lambda o: o.__dict__, sort_keys=True, indent=4))

    # Print how we did
    print("Final answer:", problem.final_answer)
    print("Compare correct answer: ", answer, "Correct? ", problem.solved_correctly)
    print(f"Took time: {time.time() - start_time} seconds\n")

    # Add to log
    if logger is not None:
        logger.paths.append(question + ":\n" + "\n".join(["* " + step.type_of_step.name for step in problem.steps]) + "\n" + str(problem.solved_correctly))
        logger.problems.append(problem)
        for step in problem.steps:
            logger.step_choices.append(step.type_of_step.name)

    return problem


def generate_train_data(save_dir: typing.Optional[str] = "saved_runs/", num_questions: int = 5000):
    drop_data = download_data()
    logger = RunsLogger()

    # Sample outside the loop to avoid duplicates
    question_tuples = sample_questions(drop_data, num_questions)

    for i in range(num_questions):
        # Get the question
        passage_id, passage_text, question, answer = question_tuples[i]
        print(f"Problem {i}:", passage_text + "\n\nQuestion: " + question)

        problem = train_on_question(passage_id, passage_text, question, answer, save_dir, logger)

    # Final summary
    if logger is not None:
        logger.print_summary()


def generate_train_data_threaded(save_dir: typing.Optional[str] = "saved_runs/", num_questions: int = 5000, max_threads=10):
    drop_data = download_data()
    logger = RunsLogger()

    # Sample outside the loop to avoid duplicates
    question_tuples = sample_questions(drop_data, num_questions)

    args = []

    for i in range(num_questions):
        # Get the question
        passage_id, passage_text, question, answer = question_tuples[i]
        args.append((passage_id, passage_text, question, answer, save_dir, logger))

    # Open AI tokens per min. Limit: 90000 / min
    api_call_limited_parallel(train_on_question, args, max_threads=max_threads)

    # Final summary
    if logger is not None:
        logger.print_summary()


if __name__ == "__main__":
    generate_train_data_threaded(save_dir=None, num_questions=100, max_threads=10)
    # compute_per_step_accuracy("saved_runs")
