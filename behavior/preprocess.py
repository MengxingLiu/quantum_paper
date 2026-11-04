#!/usr/bin/env python3
# load behavioral logs, add derived columns and save df_beh_clean.csv

import glob
import numpy as np
import pandas as pd

from config import get_paths



SWITCH_WINDOW = (-3, 7)  # trials before/after switch to label


# data loading

def load_all_behavioral_data(paths: dict) -> pd.DataFrame:
    # load and merge behavioral logs with model parameters
    
    subses_list = pd.read_csv(paths["code_dir"] / "subSesList.txt", sep=",", header=0)
    
    all_data = []
    for row in subses_list.itertuples():
        sub = str(row.sub)
        ses = str(row.ses)
        
        # find behavioral log files
        pattern = (
            f"{paths['csv_dir']}/HDM_beta**_full_block-[0-6]*"
            f"_sub-{sub}_ses-{ses}*csv"
        )
        log_files = sorted(glob.glob(pattern))
        
        if not log_files:
            continue
        
        # load behavioral data from all blocks
        beh_dfs = []
        for fpath in log_files:
            df = pd.read_csv(fpath)
            df["ses"] = ses
            if "method" not in df.columns:
                df["method"] = "BEH"
            beh_dfs.append(df)
        
        beh_df = pd.concat(beh_dfs, ignore_index=True)
        
        # load model parameters
        params_path = paths["model_file_dir"] / f"{sub}-{ses}-model.csv"
        if not params_path.exists():
            print(f"no parameter file for {sub}-{ses}")
            continue
        
        params_df = pd.read_csv(params_path)
        
        if len(params_df) != len(beh_df):
            raise ValueError(f"Length mismatch for {sub}-{ses}: beh={len(beh_df)}, params={len(params_df)}")
        
        # merge
        params_df.index = beh_df.index
        merged = pd.concat([beh_df, params_df], axis=1)
        all_data.append(merged)
        print(f"{sub}-{ses}: {len(merged)} trials")
    
    return pd.concat(all_data, ignore_index=True)


# feature computation

def compute_subjective_state(df: pd.DataFrame) -> pd.Series:
    # infer subjective state from task and cue responses
    task = df["subj_task_resp_answer"]
    cue = df["subj_cue_resp_answer"]
    
    is_face = task.isin(["male", "female"])
    is_scene = task.isin(["city", "landscape"])
    
    conditions = [
        is_face & (cue == "left"),
        is_scene & (cue == "right"),
        is_scene & (cue == "left"),
        is_face & (cue == "right"),
        is_face & (cue == "red"),
        is_scene & (cue == "yellow"),
        is_scene & (cue == "red"),
        is_face & (cue == "yellow"),
    ]
    states = [-2, -2, -1, -1, 1, 1, 2, 2]
    
    return pd.Series(np.select(conditions, states, default=0), index=df.index)


def find_switch_indices(df: pd.DataFrame) -> list:
    # find trial indices where objective state changes
    switches = []
    for (sub, ses, block), group in df.groupby(["subid", "ses", "block"]):
        state_changes = group["state"].diff() != 0
        switch_idx = group[state_changes].index[1:]  # skip first trial of block
        switches.extend(switch_idx)
    return switches


def categorize_state_change(current, previous):
    # categorize the type of state change from previous to current trial
    if current == previous:
        return "no change"
    elif (current in [-2, -1] and previous in [1, 2]) or (current in [1, 2] and previous in [-2, -1]):
        return "different feature"
    else:
        return "different state"


def add_all_features(df: pd.DataFrame, switch_window: tuple) -> pd.DataFrame:
    # compute all derived features
    
    df = df.copy()
    
    # basic cleanup
    df["subid"] = df["subid"].astype(str)
    
    # subjective state
    df["subjective_state"] = compute_subjective_state(df)
    
    # believed cue type
    cue_to_feature = {
        "left": "motion", "right": "motion",
        "red": "color", "yellow": "color",
    }
    df["believed_cue"] = df["subj_cue_resp_answer"].map(cue_to_feature)
    
    # ambiguity (difficulty of the believed cue)
    df["ambiguity"] = np.where(
        df["believed_cue"] == "motion",
        df["motion_difficulty"],
        df["color_difficulty"]
    )
    df.loc[df["believed_cue"].isna(), "ambiguity"] = np.nan
    
    ambiguity_bin_map = {
        "easy": "easy", "med": "easy", "hard": "easy",
        "harder": "hard", "hardest": "hard",
    }
    df["ambiguity_bin"] = df["ambiguity"].map(ambiguity_bin_map)
    
    # accuracy measures
    # perceptual: did they correctly identify the cue?
    df["perceptual_acc"] = (
        (df["subj_cue_resp_answer"] == df["cue_direction"]) |
        (df["subj_cue_resp_answer"] == df["cue_color"])
    ).astype(int)
    
    # state: did they infer the correct context?
    df["state_acc"] = (df["state"] == df["subjective_state"]).astype(int)
    
    # attended task
    task_to_category = {
        "male": "face", "female": "face",
        "landscape": "scene", "city": "scene",
    }
    df["attended_task"] = df["subj_task_resp_answer"].map(task_to_category)
    
    # task accuracy
    df["task_acc"] = (
        (df["subj_task_resp_answer"] == df["face_type"]) |
        (df["subj_task_resp_answer"] == df["scene_type"])
    ).astype(int)
    
    # signed coherence (for psychometric curves)
    df["coherence_signed"] = np.where(
        df["cue_direction"] == "right",
        df["motion_coherence"],
        -df["motion_coherence"]
    )
    
    # change from last trial (for RT analysis)
    df["change_from_last"] = "no change"
    
    for (sub, ses, block), group in df.groupby(["subid", "ses", "block"]):
        group = group.reset_index()
        for i in range(1, len(group)):
            idx = group.loc[i, "index"]
            current = group.loc[i, "subjective_state"]
            previous = group.loc[i - 1, "subjective_state"]
            df.loc[idx, "change_from_last"] = categorize_state_change(current, previous)
    
    # clean RT values (-1 means no response)
    df.loc[df["task_RT"] == -1, "task_RT"] = np.nan
    df.loc[df["cue_RT"] == -1, "cue_RT"] = np.nan
    
    # switch-aligned features
    switch_indices = find_switch_indices(df)
    pre, post = switch_window
    
    # initialize columns
    df["switch"] = np.nan
    df["difficulty"] = np.nan
    df["difficulty_bin"] = np.nan
    df["difficulty_cons_bin"] = np.nan
    df["context_change"] = np.nan
    
    for switch_idx in switch_indices:
        if switch_idx not in df.index:
            continue
        
        difficulty = df.loc[switch_idx, "ambiguity"]
        difficulty_bin = df.loc[switch_idx, "ambiguity_bin"]
        
        # label trials in window around switch
        for offset in range(pre, post):
            trial_idx = switch_idx + offset
            if trial_idx not in df.index:
                continue
            
            df.loc[trial_idx, "switch"] = offset
            df.loc[trial_idx, "difficulty"] = difficulty
            df.loc[trial_idx, "difficulty_bin"] = difficulty_bin
        
        # consistent difficulty: same ambiguity on trials 0 and 1
        if switch_idx + 1 in df.index:
            if df.loc[switch_idx, "ambiguity_bin"] == df.loc[switch_idx + 1, "ambiguity_bin"]:
                for offset in range(pre, post):
                    trial_idx = switch_idx + offset
                    if trial_idx in df.index:
                        df.loc[trial_idx, "difficulty_cons_bin"] = df.loc[switch_idx, "ambiguity_bin"]
        
        # context change: relative to pre-switch mode
        pre_states = df.loc[switch_idx - 5:switch_idx, "subjective_state"]
        if len(pre_states) > 0 and len(pre_states.mode()) > 0:
            pre_context = pre_states.mode().iloc[0]
            for offset in range(pre, post):
                trial_idx = switch_idx + offset
                if trial_idx in df.index:
                    df.loc[trial_idx, "context_change"] = int(
                        df.loc[trial_idx, "subjective_state"] != pre_context
                    )
    
    return df


# main

def main():
    
    paths = get_paths()
    print("data directory:", paths['csv_dir'])
    
    print("loading behavioral data")
    df = load_all_behavioral_data(paths)
    print(f"in total {len(df)} trials")
    
    print("computing features")
    df = add_all_features(df, SWITCH_WINDOW)
    
    # summary
    print("subjects:", df['subid'].nunique())
    print("sessions:", df.groupby(['subid', 'ses']).ngroups)
    print("trials:", len(df))
    print("switches:", (df['switch'] == 0).sum())
    print("acc:", round(df['correct'].mean(), 3))
    print("perceptual acc:", round(df['perceptual_acc'].mean(), 3))
    print("state acc:", round(df['state_acc'].mean(), 3))
    
    # save
    output_path = paths["csv_dir"] / "df_beh_clean.csv"
    df.to_csv(output_path, index=False)
    print("saved", output_path)
    
    return df


if __name__ == "__main__":
    df = main()