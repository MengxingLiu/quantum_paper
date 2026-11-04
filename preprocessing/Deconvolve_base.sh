#!/bin/bash


echo $nordic

space=tlrc
# preprocessed data can be in two spaces: orig or tlrc (MNI);
if [ ${space} == tlrc ]; then
    func_dir=${base_dir}/afni_proc/sub-${sub_id}/ses-${ses_id}/
    Deconvolve=Deconvolve_afni
else
    func_dir=${base_dir}/afni_proc/sub-${sub_id}/ses-${ses_id}/
    Deconvolve=Deconvolve_afni
fi

result_dir=${base_dir}/${Deconvolve}/sub-${sub_id}/ses-${ses_id}
timing_dir=${base_dir}/GLM_1Ds/sub-${sub_id}/ses-${ses_id}

# use singularity afni container instead of directly call afni command
insert_second_line() {
    local file=$1
    local text=$2
    { head -n 2 "$file"; echo "$text"; tail -n +3 "$file"; } > temp.txt && mv temp.txt "$file"
}
if [ ! -d ${result_dir} ];then
mkdir -p ${result_dir}
fi




#### QUANTUM4S task
task=Quantum4S
task_dir=${func_dir}/task-${task}

# copy one anat image to Deconvolve for better visualization
singularity run \
     -B ${root_dir}:${root_dir} \
    ${tool_dir}/afni_withr_24.0.08.sif \
3dcopy ${task_dir}/anat_final.${sub_id}+${space}. \
    ${result_dir}/anat_final.${task}.${sub_id}.nii.gz -overwrite

suffix=events
if [ ! -f ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_stats_${suffix}.nii.gz ];then
echo ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_stats_${suffix}.nii.gz
singularity run \
     -B ${root_dir}:${root_dir} \
    ${tool_dir}/afni_withr_24.0.08.sif \
    3dDeconvolve -input $(ls ${task_dir}/pb03.${sub_id}.r*.scale+${space}.HEAD | sort -V) \
    -mask ${task_dir}/mask_anat.${sub_id}+${space}.HEAD                              \
    -censor ${task_dir}/censor_${sub_id}_combined_2.1D                               \
    -ortvec ${task_dir}/ROIPC.FSvent.r01.1D ROIPC.FSvent.r01                          \
    -ortvec ${task_dir}/ROIPC.FSvent.r02.1D ROIPC.FSvent.r02                          \
    -ortvec ${task_dir}/ROIPC.FSvent.r03.1D ROIPC.FSvent.r03                          \
    -ortvec ${task_dir}/ROIPC.FSvent.r04.1D ROIPC.FSvent.r04                          \
    -ortvec ${task_dir}/ROIPC.FSvent.r05.1D ROIPC.FSvent.r05                          \
    -ortvec ${task_dir}/ROIPC.FSWe.r01.1D ROIPC.FSWe.r01                              \
    -ortvec ${task_dir}/ROIPC.FSWe.r02.1D ROIPC.FSWe.r02                              \
    -ortvec ${task_dir}/ROIPC.FSWe.r03.1D ROIPC.FSWe.r03                              \
    -ortvec ${task_dir}/ROIPC.FSWe.r04.1D ROIPC.FSWe.r04                              \
    -ortvec ${task_dir}/ROIPC.FSWe.r05.1D ROIPC.FSWe.r05                              \
    -ortvec ${task_dir}/mot_demean.r01.1D mot_demean_r01                             \
    -ortvec ${task_dir}/mot_demean.r02.1D mot_demean_r02                             \
    -ortvec ${task_dir}/mot_demean.r03.1D mot_demean_r03                             \
    -ortvec ${task_dir}/mot_demean.r04.1D mot_demean_r04                             \
    -ortvec ${task_dir}/mot_demean.r05.1D mot_demean_r05                             \
    -polort 5                                                                        \
    -num_stimts 3                                                                    \
    -CENSORTR *:0-2                                                                  \
    -stim_times 1 ${timing_dir}/cue_time.1D 'SPMG' -stim_label 1 cue                 \
    -stim_times 2 ${timing_dir}/probe_time.1D 'SPMG' -stim_label 2 probe             \
    -stim_times 3 ${timing_dir}/feedback_time.1D 'SPMG' -stim_label 3 feedback       \
    -iresp 1 ${result_dir}/cue_iresp_SPMG_${suffix}.nii.gz                           \
    -iresp 2 ${result_dir}/probe_iresp_SPMG_${suffix}.nii.gz                         \
    -iresp 3 ${result_dir}/feedback_iresp_SPMG_${suffix}.nii.gz                      \
    -num_glt 3                                                                       \
    -gltsym 'SYM: +1*cue' -glt_label 1 cue_effect                                    \
    -gltsym 'SYM: +1*probe' -glt_label 2 probe_effect                                \
    -gltsym 'SYM: +1*feedback' -glt_label 3 feedback_effect                          \
    -fout -rout -tout -x1D  ${result_dir}/${task}_${suffix}.X.xmat.1D                \
        -xjpeg  ${result_dir}/${task}_${suffix}.X.jpg                                \
    -bucket ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_stats_${suffix}.nii.gz                             \
    -jobs 32 -overwrite
else
echo "############### ${task}_sub-${sub_id}_ses-${ses_id}_stats_${suffix} exist, skipping ##############"
fi


### feedback correctness and CPE as amplitude modulators ##########
params=cpe
suffix=cpe
if [ ! -f ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_stats_${suffix}.nii.gz ];then
echo ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_stats_${suffix}.nii.gz
singularity run \
     -B ${root_dir}:${root_dir} \
    ${tool_dir}/afni_withr_24.0.08.sif \
    3dDeconvolve -input $(ls ${task_dir}/pb03.${sub_id}.r*.scale+${space}.HEAD | sort -V) \
    -mask ${task_dir}/mask_anat.${sub_id}+${space}.HEAD                              \
    -censor ${task_dir}/censor_${sub_id}_combined_2.1D                               \
    -ortvec ${task_dir}/ROIPC.FSvent.r01.1D ROIPC.FSvent.r01                          \
    -ortvec ${task_dir}/ROIPC.FSvent.r02.1D ROIPC.FSvent.r02                          \
    -ortvec ${task_dir}/ROIPC.FSvent.r03.1D ROIPC.FSvent.r03                          \
    -ortvec ${task_dir}/ROIPC.FSvent.r04.1D ROIPC.FSvent.r04                          \
    -ortvec ${task_dir}/ROIPC.FSvent.r05.1D ROIPC.FSvent.r05                          \
    -ortvec ${task_dir}/ROIPC.FSWe.r01.1D ROIPC.FSWe.r01                              \
    -ortvec ${task_dir}/ROIPC.FSWe.r02.1D ROIPC.FSWe.r02                              \
    -ortvec ${task_dir}/ROIPC.FSWe.r03.1D ROIPC.FSWe.r03                              \
    -ortvec ${task_dir}/ROIPC.FSWe.r04.1D ROIPC.FSWe.r04                              \
    -ortvec ${task_dir}/ROIPC.FSWe.r05.1D ROIPC.FSWe.r05                              \
    -ortvec ${task_dir}/mot_demean.r01.1D mot_demean_r01                             \
    -ortvec ${task_dir}/mot_demean.r02.1D mot_demean_r02                             \
    -ortvec ${task_dir}/mot_demean.r03.1D mot_demean_r03                             \
    -ortvec ${task_dir}/mot_demean.r04.1D mot_demean_r04                             \
    -ortvec ${task_dir}/mot_demean.r05.1D mot_demean_r05                             \
    -polort 5                                                                        \
    -num_stimts 3                                                                   \
    -CENSORTR *:0-2                                                                  \
    -stim_times 1 ${timing_dir}/cue_time.1D 'SPMG'        \
    -stim_label 1 cue                                                      \
    -stim_times 2 ${timing_dir}/probe_time.1D 'SPMG'      \
    -stim_label 2 probe                                                    \
    -stim_times_AM2 3 ${timing_dir}/feedback_params_correctness_${params}_time.1D 'SPMG' \
    -stim_label 3 feedback-correctness-${params}                                            \
    -fout -rout -tout -x1D  ${result_dir}/${task}_${suffix}.X.xmat.1D                \
    -x1D_regcensored ${result_dir}/${task}_${suffix}_regcensored.X.xmat.1D                       \
        -xjpeg  ${result_dir}/${task}_${suffix}.X.jpg                                \
    -bucket ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_stats_${suffix}.nii.gz                             \
    -jobs 32 -overwrite
else
echo "############### ${task}_sub-${sub_id}_ses-${ses_id}_stats_${suffix} exist, skipping ##############"
fi
