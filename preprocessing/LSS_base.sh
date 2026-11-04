#!/bin/bash

#base_dir=/path/to/QUANTUM_4S
#tool_dir=/path/to/software/
#root_dir=/path/to
#nordic=false

space=tlrc
Deconvolve=Deconvolve_afni
func_dir=${base_dir}/afni_proc/sub-${sub_id}/ses-${ses_id}

result_dir=${base_dir}/${Deconvolve}/sub-${sub_id}/ses-${ses_id}
timing_dir=${base_dir}/GLM_1Ds/sub-${sub_id}/ses-${ses_id}

#### QUANTUM4S task
task=Quantum4S
task_dir=${func_dir}/task-${task}


# remove nuisance, or clean the data to only keep meaningful signal
if [ ! -f ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_cleansignal.nii.gz ];then
echo ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_cleansignal.nii.gz
singularity run \
    -B ${root_dir}:${root_dir} \
    ${tool_dir}/afni_withr_24.0.08.sif \
    3dDeconvolve -input $(ls ${task_dir}/pb03.${sub_id}.r*.scale+${space}.HEAD | sort -V) \
    -mask ${task_dir}/mask_anat.${sub_id}+${space}.HEAD                              \
    -CENSORTR *:0-3                                                \
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
    -jobs 50                                                                         \
    -nobucket                                                                        \
    -errts ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_cleansignal.nii.gz
fi



# generate mrtrix from 3dd, later being used by 3dLSS

# Define associative arrays for stimulus mapping
for event in cue probe feedback
do
    if [[ ${event} == "cue" ]];then
        mapped_events=(probe feedback)
    elif [[ ${event} == "probe" ]];then
        mapped_events=(cue feedback)
    elif [[ ${event} == "feedback" ]];then
        mapped_events=(cue probe)
    fi
    echo "##########"
    echo running IM of ${event}
    echo take events of ${mapped_events[0]} and ${mapped_events[1]} as one single regressor
    echo "##########"

if [ ! -f ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_${event}_LSS.nii.gz ];then

echo ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_${event}_LSS.nii.gz
singularity run \
     -B ${root_dir}:${root_dir} \
    ${tool_dir}/afni_withr_24.0.08.sif \
    3dDeconvolve -input ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_cleansignal.nii.gz \
    -concat '1D: 0 430 860 1290 1720'                                                  \
    -mask ${task_dir}/mask_anat.${sub_id}+${space}.HEAD                              \
    -polort 5                                                                        \
    -num_stimts 3                                                                    \
    -CENSORTR *:0-3                                                                  \
    -stim_times_IM 1 ${timing_dir}/${event}_time.1D 'BLOCK(1,1)' -stim_label 1 ${event}                 \
    -stim_times 2 ${timing_dir}/${mapped_events[0]}_time.1D 'BLOCK(1,1)' -stim_label 2 ${mapped_events[0]}             \
    -stim_times 3 ${timing_dir}/${mapped_events[1]}_time.1D 'BLOCK(1,1)' -stim_label 3 ${mapped_events[1]}       \
    -x1D ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_${event}_IM.xmat.1D \
    -x1D_stop -allzero_OK

singularity run \
     -B ${root_dir}:${root_dir} \
    ${tool_dir}/afni_withr_24.0.08.sif \
    3dLSS -input ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_cleansignal.nii.gz \
        -mask ${task_dir}/mask_anat.${sub_id}+${space}.HEAD \
        -matrix ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_${event}_IM.xmat.1D \
        -prefix ${result_dir}/${task}_sub-${sub_id}_ses-${ses_id}_${event}_LSS.nii.gz

fi

done


