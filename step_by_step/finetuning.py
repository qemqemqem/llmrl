import json
import random


def format_problem_for_finetuning(problem: dict):
    s = problem["problem_text"].strip() + "\n"
    s += "\nSolved correctly: " + str(problem["solved_correctly"]) + "\n"
    s += "\nSteps:\n"
    for i, step in enumerate(problem["steps"]):
        s += f"\nStep {i + 1}:\n"
        sq = step["type_of_step"]["text"].strip()
        if "Please be concise" in sq:  # This is a hack because this is added to all steps in problem.py
            sq = sq[:sq.index("Please be concise")]
        s += "Question: " + sq.strip() + "\n"
        s += "Answer: " + step["step_response"].strip() + "\n"
        s += "Commentary: " + step["usefulness_commentary"].strip() + "\n"
        s += "This was " + ("Useful." if step["was_useful"] else "Not useful.") + "\n"
    s += f"Final answer: {problem['final_answer'].strip()}\n"
    s += "\nReflection:\n"
    s += problem["commentary_on_process"].strip() + "\n"
    s += ("I think I got this right" if problem["solved_correctly"] else "I'm worried I got this wrong") + "\n"
    s += f"Correct answer: {problem['gold_correct_answer']['number']}\n"
    s += "Correct" if problem["solved_correctly"] else "Incorrect" + "\n"
    return s


def load_all_files_in_directory(directory: str):
    import os
    files = {}
    for filename in os.listdir(directory):
        with open(os.path.join(directory, filename), "r") as f:
            files[filename] = f.read()
    return files


def parse_file_as_json(file: str):
    return json.loads(file)


if __name__ == "__main__":
    all_files = load_all_files_in_directory("saved_runs")
    random_file_name, random_file = random.choice(list(all_files.items()))
    problem = parse_file_as_json(random_file)
    file = format_problem_for_finetuning(problem)
    print(random_file_name)
    print(file)
