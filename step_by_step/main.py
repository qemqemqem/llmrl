import re
import time
from difflib import SequenceMatcher

from termcolor import colored

from drop.drop import *
from gpt.gpt import prompt_completion_chat
from utils.filer import *


class StepType:
    def __init__(self, name: str, text: str, is_final: bool = False, short_name=None):
        self.name: str = name
        self.short_name: str = short_name if short_name else name  # This helps for parsing the text to choose the next step
        self.text: str = text
        self.is_final: bool = is_final  # If True, this is the last step in the problem, and the answer is the answer to the Problem

        if not is_final:
            # self.text += " Answer this question, but do not proceed to the final answer yet."
            self.text += " Please be concise and professional. Do only this step and do not jump ahead."
        else:
            self.text += " Give the final answer only, using as few words as possible."


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
            {"role": "user", "content": self.problem_text},
            {"role": "assistant", "content": "I need to think this through step by step."},
        ]
        for step in self.steps:
            messages.append({"role": "user", "content": step.type_of_step.text})
            messages.append({"role": "assistant", "content": step.step_response})
        return messages


def choose_step_type(problem: Problem) -> StepType:
    messages = problem.messages_for_chat()
    sys_msg = next(msg for msg in messages if msg["role"] == "system")
    sys_msg["content"] = "You specialize in cognitive strategies. You always know how to think through a difficult problem."
    present_options = "I need to figure out what to do next. Here are my options:"
    for i, step_type in enumerate(problem.types_of_steps):
        present_options += "\n" + str(i + 1) + ") " + step_type.name
    present_options += "\nIt is probably a good idea to pick an option that has not yet been tried."
    present_options += "\nPlease choose an option by returning the number of the option. For example, if you want to choose the first option, type '1'."
    messages.append({"role": "user", "content": present_options})

    choice = prompt_completion_chat(messages=messages)

    # Find the matching step type. Iterate multiple times, because we start with the most reliable strategy and work down to the least reliable.
    for i, step_type in enumerate(problem.types_of_steps):
        if str(i + 1) == choice:
            return step_type
        if choice.startswith(str(i + 1)):
            return step_type
        if choice.startswith(step_type.name):
            return step_type
    for i, step_type in enumerate(problem.types_of_steps):
        if str(i + 1) + ")" in choice:
            return step_type
    for i, step_type in enumerate(problem.types_of_steps):
        if step_type.name in choice:
            return step_type
    for i, step_type in enumerate(problem.types_of_steps):
        if step_type.short_name in choice:
            return step_type
    for i, step_type in enumerate(problem.types_of_steps):
        if str(i + 1) in choice:
            return step_type
    # Fall back on the choice that is most similar to the choice that was made, using the longest common substring. Randomly order them, so it doesn't default to the last one.
    closest_name = max([s.name for s in random.sample(problem.types_of_steps, len(problem.types_of_steps))], key=lambda x: SequenceMatcher(None, choice, x).find_longest_match(0, len(choice), 0, len(x)).size)
    for step_type in problem.types_of_steps:
        if step_type.name == closest_name:
            return step_type

    # Notes
    # [] It seems to perseverate, choosing the same option multiple times in a row
    # [] Sometimes it says "you need to choose a strategy by typing the number", indicating that it has become confused about the wording here and the wording of the strategy option.

    # If we didn't find it, just choose randomly
    print("ERROR: Got a bad choice:", choice, "Choosing randomly.")
    return random.choice(problem.types_of_steps)


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


def define_step_types():
    return [
        StepType("Choose a strategy", "What is the best strategy to solve this problem?", short_name="strategy"),
        StepType("Identify the obvious answer", "What is the obvious answer to this problem?", short_name="obvious"),
        StepType("Do math", "Step through the math to solve this problem.", short_name="math"),
        StepType("Guess and check", "Guess and check to solve this problem."),
        StepType("Look for a clever trick", "I think there might be a clever trick for solving this problem. What is it?", short_name="trick"),
        StepType("Think about background", "What background information do we know that might help us solve this problem?", short_name="background"),
        StepType("Ready to find the final answer", "Given what we know, what is the answer to this problem? Please write the numerical answer and nothing else. Write the answer with digits, like '4' rather than 'four'.", is_final=True, short_name="final"),
    ]


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
        print(f"Took time: {time.time() - start_time} seconds")

        # Add to log
        paths.append(question + ":\n" + "\n".join(["* " + step.type_of_step.name for step in problem.steps]) + "\n" + str(problem.solved_correctly))
        problems.append(problem)

    print("Paths taken:")
    print("\n\n".join(paths))

    print(f"Num correct: {sum([1 for problem in problems if problem.solved_correctly])} / {len(problems)}")
