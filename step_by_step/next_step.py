import random

from gpt.gpt import prompt_completion_chat
from step_by_step.problem import *


def define_step_types():
    steps = [
        StepType("Identify relevant information", "What information is relevant to the problem?", short_name="relevant"),
        StepType("Identify the main question", "What is the main question or goal of the problem?", short_name="question"),
        StepType("Identify keywords", "Are there any keywords or phrases that can help me identify the type of problem?", short_name="keywords"),
        StepType("Break down the problem", "Can I break down the problem into smaller, more manageable parts?", short_name="break"),
        StepType("Identify patterns", "Are there any patterns or relationships between the given information that can help me solve the problem?", short_name="patterns"),
        # StepType("Visualize the problem", "Can I visualize the problem or create a diagram to better understand it?", short_name="visualize"),
        StepType("Rephrase the problem", "Can I rephrase the problem in my own words to ensure I understand it?", short_name="rephrase"),
        StepType("Use similar problems", "Are there any similar problems that I've solved before that could help guide me?", short_name="similar"),
        StepType("Make a list or table", "Can I make a list or table to organize the given information?", short_name="list"),
        StepType("Convert units", "What units or measurements are being used, and do I need to convert any of them?", short_name="measurement"),
        StepType("Make assumptions", "Are there any assumptions I need to make, or are there any constraints I should consider?", short_name="assumptions"),
        StepType("Try a different approach", "Should I try a different approach if my current strategy is not working?", short_name="different"),
        StepType("Estimate the answer", "Can I estimate the answer to check if my solution is reasonable?", short_name="estimate"),
        StepType("Double-check", "Have I double-checked my calculations and solution for accuracy?", short_name="double"),
        StepType("Choose a strategy", "What is the best strategy to solve this problem?", short_name="strategy"),
        StepType("Identify the obvious answer", "What is the obvious answer to this problem?", short_name="obvious"),
        StepType("Do math", "Step through the math to solve this problem.", short_name="math"),
        # StepType("Guess and check", "Guess and check to solve this problem."),
        StepType("Look for a clever trick", "I think there might be a clever trick for solving this problem. What is it?", short_name="trick"),
        StepType("Think about background", "What background information do we know that might help us solve this problem?", short_name="background"),
        StepType("Ready to find the final answer", "Given what we know, what is the answer to this problem? Please write the numerical answer and nothing else. Write the answer with digits, like '4' rather than 'four'.", is_final=True, short_name="final"),
    ]
    # for step_type in steps:
    #     print(step_type.text)
    return steps


def choose_step_type(problem: Problem) -> StepType:
    messages = problem.messages_for_chat()
    sys_msg = next(msg for msg in messages if msg["role"] == "system")
    sys_msg["content"] = "You specialize in cognitive strategies. You always know how to think through a difficult problem."
    present_options = "I need to figure out what to do next. Here are my options:"

    all_steps = problem.types_of_steps[:]
    # Randomize options
    random.shuffle(all_steps)
    # Put final answer option at the beginning. It could go at the end, but the model seems to slightly prefer the beginning.
    all_steps = [s for s in all_steps if s.is_final] + [s for s in all_steps if not s.is_final]
    # Remove the option if it has already been tried. In practice, it seems to perseverate.
    all_steps = [s for s in all_steps if s not in [ps.type_of_step for ps in problem.steps]]

    for i, step_type in enumerate(all_steps):
        present_options += "\n" + str(i + 1) + ") " + step_type.name
    # present_options += "\nIt is probably a good idea to pick an option that has not yet been tried."
    present_options += "\nPlease choose an option by returning the number of the option."
    # present_options += " For example, if you want to choose the first option, type '1'."
    messages.append({"role": "user", "content": present_options})

    choice = prompt_completion_chat(messages=messages)

    # Find the matching step type. Iterate multiple times, because we start with the most reliable strategy and work down to the least reliable.
    for i, step_type in enumerate(all_steps):
        if str(i + 1) == choice:
            return step_type
        if choice.startswith(str(i + 1)):
            return step_type
        if choice.startswith(step_type.name):
            return step_type
    for i, step_type in enumerate(all_steps):
        if str(i + 1) + ")" in choice:
            return step_type
    for i, step_type in enumerate(all_steps):
        if step_type.name in choice:
            return step_type
    for i, step_type in enumerate(all_steps):
        if step_type.short_name in choice:
            return step_type
    for i, step_type in enumerate(all_steps):
        if str(i + 1) in choice:
            return step_type
    # Fall back on the choice that is most similar to the choice that was made, using the longest common substring. Randomly order them, so it doesn't default to the last one.
    closest_name = max([s.name for s in random.sample(all_steps, len(all_steps))], key=lambda x: SequenceMatcher(None, choice, x).find_longest_match(0, len(choice), 0, len(x)).size)
    for step_type in all_steps:
        if step_type.name == closest_name:
            return step_type

    # If somehow we didn't find it, just choose randomly
    print("ERROR: Got a bad choice:", choice, "Choosing randomly.")
    return random.choice(all_steps)
