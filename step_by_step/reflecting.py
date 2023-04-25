from gpt.gpt import prompt_completion_chat
from step_by_step.problem import Problem, StepType, Step


def reflect_on_each_step(problem: Problem):
    pass


def reflect_on_finished_problem(problem: Problem):
    messages = problem.messages_for_chat()
    sys_msg = next(msg for msg in messages if msg["role"] == "system")
    sys_msg["content"] = "You are reflecting back on the problem you just solved. You are thinking about how you solved it and how you could have solved it better."
    overall_reflection_prompt = f"Your answer was {problem.final_answer}, {'and' if problem.solved_correctly else 'but'} the correct answer was {problem.gold_correct_answer['number']}. Please write a few sentences about how you solved the problem and how you could have solved it better."
    messages.append({"role": "user", "content": overall_reflection_prompt})
    problem.commentary_on_process = prompt_completion_chat(messages=messages)
    print(problem.commentary_on_process)
    problem.steps.append(Step(StepType("Overall reflection", overall_reflection_prompt), step_response=problem.commentary_on_process))
