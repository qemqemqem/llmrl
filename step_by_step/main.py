import re

from drop.drop import *
from step_by_step.next_step import *
from step_by_step.reflecting import reflect_on_finished_problem, reflect_on_each_step
from step_by_step.solver import *
from utils.filer import *
from utils.thread_helper import api_call_limited_parallel


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


def train_on_question(passage_id, passage_text, question, answer, save_dir, logger: RunsLogger = None, max_steps=5, min_steps=1, do_reflection=True):
    start_time = time.time()

    # Create a Problem
    question_id = passage_id + "_" + re.sub("\W", "_", question[:40])
    prompt = format_prompt(passage_text, question)
    problem = Problem(prompt, question_alone=question)
    problem.types_of_steps = define_step_types()
    solve_problem_for_train(problem, randomness=0.0, max_steps=max_steps, min_steps=min_steps)

    # Reflect
    problem.gold_correct_answer = answer
    problem.solved_correctly = is_correct_answer(problem.final_answer, answer)
    if do_reflection:
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


def generate_train_data_threaded(save_dir: typing.Optional[str] = "saved_runs/", num_questions: int = 5000, max_threads=10, filter_func=None, max_steps=5, min_steps=1, do_reflection=True):
    drop_data = download_data()
    logger = RunsLogger()

    # Sample outside the loop to avoid duplicates
    question_tuples = sample_questions(drop_data, num_questions, filter_func=filter_func)

    args = []

    for i in range(num_questions):
        # Get the question
        passage_id, passage_text, question, answer = question_tuples[i]
        args.append((passage_id, passage_text, question, answer, save_dir, logger, max_steps, min_steps, do_reflection))

    # Open AI tokens per min. Limit: 90000 / min. This seems to be approximately 10 max_threads for our use case.
    api_call_limited_parallel(train_on_question, args, max_threads=max_threads)

    # Final summary
    if logger is not None:
        logger.print_summary()


if __name__ == "__main__":
    start_time = time.time()
    generate_train_data_threaded(save_dir="saved_runs_no_steps/", num_questions=100, max_threads=10, filter_func=lambda qa_pair: qa_pair["answer"]["number"] != "" or len(qa_pair["answer"]["spans"]) > 0, max_steps=5, min_steps=1, do_reflection=True)
    # compute_per_step_accuracy("saved_runs")
    print(f"Overall Took time: {time.time() - start_time} seconds\n")
