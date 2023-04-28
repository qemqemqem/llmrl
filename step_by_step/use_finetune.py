import json

import openai


class SuggestedSteps:
    def __init__(self):
        self.steps = []
        self.expected_correct = False
        self.expected_answer = None
        self.reflection = None


def get_steps_from_finetuned_model(prompt, model="curie:ft-vast-2023-04-28-22-00-30", temperature=0.1):
    response = openai.Completion.create(model=model, prompt=prompt, max_tokens=1000, n=1, stop="\n###", temperature=temperature)
    # print("Got response: ", response["choices"][0]["text"])
    steps = SuggestedSteps()
    cur_question = ""
    cur_answer = ""
    cur_commentary = ""
    cur_useful = False
    cur_is_final = False
    cur_is_reflection = False
    is_reflecting = False  # Note that this is different from the "cur_" variables
    for l in response["choices"][0]["text"].split("\n"):
        if l != "" and is_reflecting:
            steps.reflection = l.strip()
            is_reflecting = False
        if l.startswith("Step") and l.endswith(":"):
            # Save the previous step
            if cur_question:
                steps.steps.append({"question": cur_question, "answer": cur_answer, "commentary": cur_commentary, "useful": cur_useful, "is_final": cur_is_final, "is_reflection": cur_is_reflection})
            # Start a new step
            cur_question = ""
            cur_answer = ""
            cur_commentary = ""
            cur_useful = False
            cur_is_final = False
            cur_is_reflection = False
        elif l.startswith("Question:"):
            cur_question = l[9:].strip()
            # Check if "Final." or "Reflection." is in the question, as it is in finetuning.py
            if "Final." in cur_question:
                cur_is_final = True
            elif "Reflection." in cur_question:
                cur_is_reflection = True
        elif l.startswith("Answer:"):
            cur_answer = l[7:].strip()
        elif l.startswith("Commentary:"):
            cur_commentary = l[11:].strip()
        elif "useful" in l.lower() and "not useful" not in l.lower():
            cur_useful = True
        elif l.startswith("Reflection:"):
            is_reflecting = True
        elif l.startswith("I think I got this right") or l == "Correct":
            steps.expected_correct = True
        elif l.startswith("Final answer:"):
            steps.expected_answer = l[13:].strip()
    if cur_question and ("the correct answer was" not in cur_question and "your answer was" not in cur_question.lower()):
        # Attempt to filter out the reflection step. This if statement will almost never happen.
        steps.steps.append({"question": cur_question, "answer": cur_answer, "commentary": cur_commentary, "useful": cur_useful, "is_final": cur_is_final, "is_reflection": cur_is_reflection})
    return steps


if __name__ == "__main__":
    prompt = "Context:\nThe Chargers began their season at Arrowhead Stadium for a division rivalry match against the Kansas City Chiefs. In the first quarter the Chargers took the early lead as QB Philip Rivers completed a 3-yard TD pass to TE Antonio Gates. The Chiefs replied when RB Jamaal Charles made a 56-yard TD run. In the 2nd quarter the Chargers fell behind when QB Matt Cassel completed a 2-yard TD pass to TE Tony Moeaki. This was followed by WR Dexter McCluster returning a punt 94&#160;yards to the endzone for a touchdown. In the third quarter the Chargers cut the lead when QB Philip Rivers threw a 59-yard TD pass to WR Legedu Naanee. In the 4th quarter the Chiefs defense prevented any more scoring from the Chargers.\n\nQuestion:\nHow many is the difference in the yards of the TD pass to Gates and the TD pass to Moeaki?\n\nSolved correctly: True\n\n\n###\n\n"
    steps = get_steps_from_finetuned_model(prompt)
    print(json.dumps(steps.__dict__, indent=4, sort_keys=True))
