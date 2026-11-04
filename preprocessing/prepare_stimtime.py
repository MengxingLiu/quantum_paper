#!/bin/python3
import os,glob
import pandas as pd
import numpy as np

base_dir="/path/to/QUANTUM_4S"
code_dir="/path/to/code"
output_dir=f"{base_dir}/GLM_1Ds"

def write_list_to_file(file_path, list_of_lists):
    with open(file_path, 'w') as file:
        for item_list in list_of_lists:
            # Convert each item in the list to a string and join them with a space
            line = ' '.join(map(str, item_list))
            # Write the line to the file
            file.write(line + '\n')

def extende_quantum_beh_df(df_data):
    # add feedback timestamp
    name_maps={"time_since_run_cue_prez":"cue_time",
            "time_since_run_photo_prez":"probe_time"}
    df_data=df_data.rename(columns=name_maps)
    df_data["feedback_time"]=df_data.after_feed_back_T-0.5
    # create column of believed state
    conditions=[(df_data.subj_task_resp_answer.isin(["male", "female"]) &
                (df_data.subj_cue_resp_answer=="left")),
                (df_data.subj_task_resp_answer.isin(["city", "landscape"]) &
                (df_data.subj_cue_resp_answer=="right")),
                (df_data.subj_task_resp_answer.isin(["city", "landscape"]) &
                (df_data.subj_cue_resp_answer=="left")),
                (df_data.subj_task_resp_answer.isin(["male", "female"]) &
                (df_data.subj_cue_resp_answer=="right")),
                (df_data.subj_task_resp_answer.isin(["male", "female"]) &
                (df_data.subj_cue_resp_answer=="red")),
                (df_data.subj_task_resp_answer.isin(["city", "landscape"]) &
                (df_data.subj_cue_resp_answer=="yellow")),
                (df_data.subj_task_resp_answer.isin(["city", "landscape"]) &
                (df_data.subj_cue_resp_answer=="red")),
                (df_data.subj_task_resp_answer.isin(["male", "female"]) &
                (df_data.subj_cue_resp_answer=="yellow"))] 
    subj_state=[-2,-2,-1,-1,1,1,2,2]
    df_data["subjective_state"]=np.select(conditions,subj_state)
    return df_data


def convert_quantum_to_afni_1D(sub_id,ses_id):
    deconv_dir=f"{output_dir}/sub-{sub_id}/ses-{ses_id}"
    if not os.path.isdir(deconv_dir):
        print("creating subj directory now")
        os.makedirs(deconv_dir)   
    csv_dir = f"{base_dir}/CSVs/"
    all_logs=sorted(glob.glob(f"{csv_dir}/HDM_beta_*full*_block*_sub-{sub_id}_ses-{ses_id}*csv"))
    if len(all_logs) != 5:
        raise ValueError('Check log, should be 5 logs')
    event_time_list=['cue_time', 'probe_time', 'feedback_time']
    for event_time in event_time_list:
        list_tmp=[]
        for single_log in all_logs:
            df = pd.read_csv(single_log)
            df=extende_quantum_beh_df(df)
            # clean list by remove np.nan 
            list_run = [i for i in list(df[event_time]) if ~np.isnan(i)]
            list_tmp.append(list_run)
        write_list_to_file(f"{deconv_dir}/{event_time}.1D",list_tmp)


subseslist=os.path.join(code_dir,"subSesList.txt")

dt = pd.read_csv(subseslist, sep=",", header=0)

for row in dt.itertuples(index=True, name='Pandas'):
    sub  = str(row.sub)
    ses  = str(row.ses)
    convert_quantum_to_afni_1D(sub,ses)


