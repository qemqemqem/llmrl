import json


def format_problem_for_finetuning(problem: dict, prompt_end="\n\n###\n\n", completion_end="\n###"):
    p = problem["problem_text"].strip() + prompt_end
    c = " "  # Start completion with a space for tokenization reasons
    c += "\nSolved correctly: " + str(problem["solved_correctly"]) + "\n"
    c += "\nSteps:\n"
    for i, step in enumerate(problem["steps"]):
        c += f"\nStep {i + 1}:\n"
        sq = step["type_of_step"]["text"].strip()
        if "Please be concise" in sq:  # This is a hack because this is added to all steps in problem.py
            sq = sq[:sq.index("Please be concise")]
        c += "Question: " + sq.strip() + "\n"
        c += "Answer: " + step["step_response"].strip() + "\n"
        c += "Commentary: " + step["usefulness_commentary"].strip() + "\n"
        c += "This was " + ("Useful." if step["was_useful"] else "Not useful.") + "\n"
    c += f"Final answer: {problem['final_answer'].strip()}\n"
    c += "\nReflection:\n"
    c += problem["commentary_on_process"].strip() + "\n"
    c += ("I think I got this right" if problem["solved_correctly"] else "I'm worried I got this wrong") + "\n"
    c += f"Correct answer: {problem['gold_correct_answer']['number']}\n"
    c += "Correct" if problem["solved_correctly"] else "Incorrect" + "\n"
    c += completion_end
    # Return the prompt and the completion, which is the format that OpenAI wants for finetuning
    # https://platform.openai.com/docs/guides/fine-tuning/preparing-your-dataset
    return p, c


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
    # random_file_name, random_file = random.choice(list(all_files.items()))
    # problem = parse_file_as_json(random_file)
    # file = format_problem_for_finetuning(problem)
    # print(random_file_name)
    # print(file)
    for file_name, contents in all_files.items():
        problem = parse_file_as_json(contents)
        prompt, completion = format_problem_for_finetuning(problem)
