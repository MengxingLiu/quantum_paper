#!/bin/bash
# dicom to BIDS with heudiconv, using heuristic.py
singularity run \
	${tool_dir}/heudiconv_1.0.1.sif \
	-d ${base_dir}/Raw/{subject}/{session}/scans/*/resources/DICOM/files/*.dcm  \
    -o ${base_dir}/Nifti/ \
    -f ${code_dir}/heuristic.py \
	-s $sub_id \
    --ses $ses_id \
	-c dcm2niix -b \
    --overwrite


# post heudiconv: rename magnitude/real/imaginary data
func_dir=${base_dir}/Nifti/sub-${sub_id}/ses-${ses_id}/func
task=Quantum4S
for run in {001..005}
do
    for ext in json nii.gz
    do
        source_file=${func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_bold1.${ext}
        dest_file=${func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_part-mag_bold.${ext}
        if [ -f ${source_file} ]; then
            mv ${source_file} ${dest_file}
        fi
    done
done
