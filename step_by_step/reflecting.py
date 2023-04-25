from gpt.gpt import prompt_completion_chat
from step_by_step.problem import Problem, StepType, Step


def reflect_on_each_step(problem: Problem):
    messages = problem.messages_for_chat()
    sys_msg = next(msg for msg in messages if msg["role"] == "system")
    sys_msg["content"] = "You are reflecting back on the problem you just solved. You are thinking about how you solved it and how you could have solved it better."
    steps_prompt = "Here are the steps you took to solve this problem:\n"
    for i, step in enumerate(problem.steps):
        # if step.type_of_step.is_final:
        #     continue
        if "reflection" in step.type_of_step.name.lower():
            continue
        steps_prompt += f"{str(i + 1)}. {step.type_of_step.name}\n"  #: {step.step_response}\n"
    steps_prompt += f"Look back on the steps you took. For each one, say whether it was useful or not useful. Then give a one sentence explanation of why it was useful or not."
    if not problem.solved_correctly:
        steps_prompt += " You got the problem wrong, so think about which step wasn't right."
    steps_prompt += "\n\nUse this format:\n0. Example step. Useful. I used this step to do X.\n0. Example step. Not useful. This was distracting or misleading because Y."
    messages.append({"role": "user", "content": steps_prompt})
    steps_reflection = prompt_completion_chat(messages=messages)
    # print(problem.solved_correctly)
    # print(steps_prompt)
    # print(steps_reflection)

    # Parse the reflection
    for i, l in enumerate(steps_reflection.split("\n")):
        if not l:
            continue
        matching_step = None
        for j, step in enumerate(problem.steps):
            if step.usefulness_commentary != "":
                # Already done this one. They're probably listed in order anyway
                continue
            if i == j and l.startswith(str(j + 1)):
                matching_step = step
                break
            if l.startswith(str(j + 1)):
                # Oddly out of place but we'll take it
                matching_step = step
                break
            if step.type_of_step.name in l:
                matching_step = step
                break
        if matching_step is None:
            print("ERROR: Couldn't find matching step for reflection line:", l)
            continue
        useful = False
        if "useful" in l.lower():
            useful = True
        if "not useful" in l.lower():
            useful = False
        if "not applicable" in l.lower():
            useful = False
        matching_step.was_useful = useful
        for verdict in ["ot applicable", "ot useful", "seful"]:
            if verdict in l.lower():
                try:
                    matching_step.usefulness_commentary = l.split(verdict + ".")[1].strip()
                    # print(f"Found commentary for step {matching_step.type_of_step.name}: {matching_step.usefulness_commentary}")
                    break
                except IndexError:
                    print("ERROR: Couldn't parse commentary for line:", l)
    # print("Done parsing reflection")


def reflect_on_finished_problem(problem: Problem):
    messages = problem.messages_for_chat()
    sys_msg = next(msg for msg in messages if msg["role"] == "system")
    sys_msg["content"] = "You are reflecting back on the problem you just solved. You are thinking about how you solved it and how you could have solved it better."
    overall_reflection_prompt = f"Your answer was {problem.final_answer}, {'and' if problem.solved_correctly else 'but'} the correct answer was {problem.gold_correct_answer['number']}. Please write a few sentences about how you solved the problem and how you could have solved it better."
    messages.append({"role": "user", "content": overall_reflection_prompt})
    problem.commentary_on_process = prompt_completion_chat(messages=messages)
    # print(problem.commentary_on_process)
    # Mark it as is_final so that it will be filtered in the steps reflection above
    problem.steps.append(Step(StepType("Overall reflection", overall_reflection_prompt, is_final=True), step_response=problem.commentary_on_process))
