import json
import random

from termcolor import colored

from drop.drop import format_prompt
from gpt.gpt import prompt_completion_chat
from step_by_step.next_step import choose_step_type
from step_by_step.problem import *
from use_finetune import get_steps_from_finetuned_model


def solve_problem_for_train(problem: Problem, randomness=0.1, max_steps=5, min_steps=1):
    while True:
        if random.random() < randomness:  # Mix it up sometimes, for exploration
            step_type = random.choice(problem.types_of_steps)
        elif len(problem.steps) >= max_steps:  # That's enough steps, final now
            step_type = next(step_type for step_type in problem.types_of_steps if step_type.is_final)
        else:
            step_type = choose_step_type(problem)
        if step_type.is_final and len(problem.steps) < min(min_steps, max_steps):
            # Always do at least min_steps steps before the final answer
            step_type = random.choice([step_type for step_type in problem.types_of_steps if not step_type.is_final])

        print("Next step:", step_type.name)

        # Complete this step with chat
        messages = problem.messages_for_chat()
        st = step_type.text
        if step_type.is_final and problem.question_alone is not None:
            st += "\n\nQuestion: " + problem.question_alone
        print("Step text: ", st)
        messages.append({"role": "user", "content": st})
        response = prompt_completion_chat(messages=messages)
        print(colored(f"Got response: {response}", "blue"))
        step = Step(step_type)
        step.step_response = response
        problem.steps.append(step)

        if step_type.is_final:
            problem.final_answer = response
            break


def solve_problem_at_inference(problem: Problem):
    # Add this text so that the model knows it's solved correctly, and the ### so that it knows the prompt is done
    steps = get_steps_from_finetuned_model(problem.problem_text + "\n\nSolved correctly: True\n\n\n###\n\n")

    for i, step in enumerate(steps.steps):
        print("Next step:", step["question"])

        # Complete this step with chat
        messages = problem.messages_for_chat()
        st = step["question"]
        is_final = i == len(steps.steps) - 1  # Assume the last step is the final one
        if is_final and problem.question_alone is not None:
            if "\n\nQuestion:" in step["question"]:
                # Remove the question, then re-add it:
                st = st[:st.index("\n\nQuestion:")]
                st += "\n\nQuestion: " + problem.question_alone
        messages.append({"role": "user", "content": st})
        response = prompt_completion_chat(messages=messages)
        print(colored(f"Got response: {response}", "blue"))

        # Add this step
        step = Step(StepType(step["question"], step["question"], is_final=is_final))
        step.step_response = response
        problem.steps.append(step)

        if is_final:
            problem.final_answer = response
            break


if __name__ == "__main__":
    question = "How many is the difference in the yards of the TD pass to Gates and the TD pass to Moeaki?"
    problem = Problem(format_prompt("The Chargers began their season at Arrowhead Stadium for a division rivalry match against the Kansas City Chiefs. In the first quarter the Chargers took the early lead as QB Philip Rivers completed a 3-yard TD pass to TE Antonio Gates. The Chiefs replied when RB Jamaal Charles made a 56-yard TD run. In the 2nd quarter the Chargers fell behind when QB Matt Cassel completed a 2-yard TD pass to TE Tony Moeaki. This was followed by WR Dexter McCluster returning a punt 94&#160;yards to the endzone for a touchdown. In the third quarter the Chargers cut the lead when QB Philip Rivers threw a 59-yard TD pass to WR Legedu Naanee. In the 4th quarter the Chiefs defense prevented any more scoring from the Chargers.", question), question)
    solve_problem_at_inference(problem)
    print("\n\nFinished!\n")
    print(json.dumps(problem, default=lambda o: o.__dict__, indent=4))
    print("yay")
