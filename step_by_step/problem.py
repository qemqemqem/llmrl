class StepType:
    def __init__(self, name: str, text: str, is_final: bool = False, short_name=None):
        self.name: str = name
        self.short_name: str = short_name if short_name else name  # This helps for parsing the text to choose the next step
        self.text: str = text
        self.is_final: bool = is_final  # If True, this is the last step in the problem, and the answer is the answer to the Problem

        if not is_final:
            # self.text += " Answer this question, but do not proceed to the final answer yet."
            # TODO Put this elsewhere so it doesn't get logged
            self.text += " Please be concise and professional. Do only this step and do not jump ahead."
        else:
            self.text += " Give the final answer only, using as few words as possible."


class Step:
    def __init__(self, type_of_step: StepType, step_response: str = ""):
        self.type_of_step: StepType = type_of_step
        self.step_response: str = step_response

        # These are used during reflection after the problem is solved and the answer is checked
        self.was_useful: bool = False
        self.usefulness_commentary: str = ""


class Problem:
    def __init__(self, problem_text: str, question_alone: str = None):
        self.problem_text: str = problem_text
        self.steps: list[Step] = []
        self.solved_correctly: bool = False
        self.commentary_on_process: str = ""
        self.types_of_steps: list[StepType] = []
        self.final_answer = ""
        self.gold_correct_answer = ""
        self.question_alone = question_alone

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
