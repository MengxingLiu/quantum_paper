#!/bin/bash
# Build the amplitude-modulated feedback timing file for the CPE GLM:
# feedback onset * feedback correctness * CPE (AFNI 1dMarry).
software_dir=/path/to/software
base_dir=/path/to/QUANTUM_4S
code_dir=/path/to/code
subSesList=${code_dir}/subSesList.txt
root_dir=/path/to

# Read the file line by line, skipping the first line (header)
tail -n +2 ${subSesList} | while IFS=, \
    read -r sub_id ses_id RUN anat dwi func age ses; do
    stim_timing_dir=${base_dir}/GLM_1Ds/sub-${sub_id}/ses-${ses_id}
    if [ ! -f ${stim_timing_dir}/feedback_params_correctness_cpe_time.1D ]; then
        singularity run --cleanenv -B ${root_dir} \
        ${software_dir}/afni_withr_24.0.08.sif \
            1dMarry ${stim_timing_dir}/feedback_time.1D \
                ${stim_timing_dir}/correct_bin.1D \
                ${stim_timing_dir}/cpe.1D \
                > ${stim_timing_dir}/feedback_params_correctness_cpe_time.1D
    fi
done
