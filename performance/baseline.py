"""
calculate statistics on the following
Using NO thinkout loud
Using thinkout loud
Correlated to number of steps
Correlated to types of steps o

1. Multithread - raw answers
2. Run with Step -1 on N samples
3. Compare results WRT N steps -> and performance
    Correct, Incorrect
"""
import os
import json
import pandas as pd
from sklearn import metrics

def load_files(directory):
    files = os.listdir(directory)
    problems = []
    for file in files:
        problems.append(json.loads(open(directory+file).read()))
    return problems
if __name__ == '__main__':
    #load all dictionaries from a given directory as list
    #convert that to dataframe
    directory = "saved_runs_maxsteps_0/"
    problems = load_files(directory)

    directory = "saved_runs/"
    problems2 = load_files(directory)

    merged = problems2 + problems
    #merge the two lists
    df_version = pd.DataFrame(merged)
    df_version["num_steps"] = df_version["steps"].apply(lambda x: len(x))
    #get accuracy for all df where max_steps = 0
    #group by num steps and get mean num steps for each group

    grouped_results = df_version.groupby("num_steps")
    #get mean oof steps for each group
    mean_steps = grouped_results["solved_correctly"].mean()
    print(mean_steps)
    print(df_version[df_version["num_steps"]==1]["solved_correctly"].mean())
    print(df_version[df_version["num_steps"] > 1]["solved_correctly"].mean())

    unique_occurence = df_version.problem_text.value_counts()
    overlap = df_version[df_version.problem_text.isin(unique_occurence[unique_occurence >= 2].index)]

    group1 = overlap[overlap["num_steps"] == 1][["problem_text", "solved_correctly"]]
    group2 = overlap[overlap["num_steps"] > 1][["problem_text", "solved_correctly"]]

    #create new dataframe of group1 and group2 joined on problem text with solved_correctly_x and solved_correctly_y
    merged_df = pd.merge(group1, group2, on="problem_text", how="inner")

    print(merged_df[['solved_correctly_x', 'solved_correctly_y']].corr())

    print(merged_df[['solved_correctly_x', 'solved_correctly_y']].mean())
    print(merged_df[['solved_correctly_x', 'solved_correctly_y']].std())

    #get kohen's kappa
    print(metrics.cohen_kappa_score(merged_df['solved_correctly_x'], merged_df['solved_correctly_y']))

    print(group1.num_steps.mean())
    print(group2.num_step.mean())
