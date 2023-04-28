from collections import defaultdict

from step_by_step.finetuning import load_all_files_in_directory, parse_file_as_json


def compute_accuracy_on_all_files(save_dir="saved_runs"):
    all_files = load_all_files_in_directory("saved_runs/" + save_dir)
    num_correct = 0
    num_total = 0
    for filename, file in all_files.items():
        problem = parse_file_as_json(file)
        if problem["solved_correctly"]:
            num_correct += 1
        num_total += 1
    print(f"Num correct: {num_correct} / {num_total} = {num_correct / num_total * 100:.2f}%")


def compute_accuracy_all_files_by_step_count(save_dir="saved_runs"):
    all_files = load_all_files_in_directory("saved_runs/" + save_dir)
    num_correct = defaultdict(int)
    num_total = defaultdict(int)
    for filename, file in all_files.items():
        problem = parse_file_as_json(file)
        num_total[len(problem["steps"])] += 1
        if problem["solved_correctly"]:
            num_correct[len(problem["steps"])] += 1
    print("Num correct / Num total = Accuracy for each step count")
    for step_count in sorted(num_total.keys()):
        print(f"Num correct: {num_correct[step_count]} / {num_total[step_count]} = {num_correct[step_count] / num_total[step_count] * 100:.2f}% for {step_count} steps")


def compute_per_step_accuracy(save_dir="saved_runs"):
    all_files = load_all_files_in_directory("saved_runs/" + save_dir)
    num_useful = defaultdict(int)
    num_correct = defaultdict(int)
    num_total = defaultdict(int)
    for filename, file in all_files.items():
        problem = parse_file_as_json(file)
        for step in problem["steps"]:
            if step["was_useful"]:
                num_useful[step["type_of_step"]["name"]] += 1
            if problem["solved_correctly"]:
                num_correct[step["type_of_step"]["name"]] += 1
            num_total[step["type_of_step"]["name"]] += 1
    print(f"Useful / Total = Usefulness\t\tCorrect / Total = Accuracy\t\tStep")
    print(f"--------------------------------------------------------------")
    for step in sorted(num_total.keys(), key=lambda x: num_total[x]):
        print(f"{num_useful[step]} / {num_total[step]} = {num_useful[step] / num_total[step] * 100:.2f}%\t\t{num_correct[step]} / {num_total[step]} = {num_correct[step] / num_total[step] * 100:.2f}%\t\t{step}")


if __name__ == "__main__":
    save_dir = "saved_runs_no_steps"
    print(f"\nStatistics for {save_dir}")
    compute_accuracy_on_all_files(save_dir=save_dir)
    compute_per_step_accuracy(save_dir=save_dir)

    save_dir = "saved_runs_2"
    print(f"\nStatistics for {save_dir}")
    compute_accuracy_on_all_files(save_dir=save_dir)
    compute_per_step_accuracy(save_dir=save_dir)
    compute_accuracy_all_files_by_step_count(save_dir=save_dir)

    save_dir = "saved_runs_finetune_guided"
    print(f"\nStatistics for {save_dir}")
    compute_accuracy_on_all_files(save_dir=save_dir)
    compute_per_step_accuracy(save_dir=save_dir)
    compute_accuracy_all_files_by_step_count(save_dir=save_dir)
