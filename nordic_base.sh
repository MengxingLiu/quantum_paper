#!/bin/bash

module load matlab/2021a
#sub_id=10263
#sess_id=20240308
#base_dir=/cluster/home/mliu23/lab_home/QUANTUM_4S
#root_dir=/cluster
#tool_dir=/cluster/home/mliu23/lab_home/softwares
func_dir=${base_dir}/Nifti/sub-${sub_id}/ses-${ses_id}/func


for task in Quantum4S VisMotor
do
    for run in {001..005}
    do
    for ext in json nii.gz
    do
        source_file=${func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_bold.${ext}
        dest_file=${func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_part-mag_bold.${ext}
        if [ -f ${source_file} ]; then
            cp ${source_file} ${dest_file}

        fi
    done
    done
done



for task in Quantum4S VisMotor
do
    for run in {001..005}
    do
        input_abs=${func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_part-mag_bold.nii.gz
        input_real=${func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_bold_real.nii.gz
        input_imag=${func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_bold_imaginary.nii.gz
        nordic_func_dir=${base_dir}/Nifti_nordic/sub-${sub_id}/ses-${ses_id}/func/
        output_cpx=${nordic_func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_bold_complex.nii.gz
        output_phase=${nordic_func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_bold_phase.nii.gz
        output_abs=${nordic_func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_bold_abs.nii.gz
        if [ ! -f ${input_abs} ]; then
            continue
        fi        

        # post-nordic files will be in a separate Nifti folder: Nifti_nordic
        if [ ! -d ${nordic_func_dir} ];then
            mkdir -p ${nordic_func_dir}
        fi

        output_nordic=sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_part-mag_bold
        echo ${output_nordic}
        # convert real and imaginary data to complex-valued data
        singularity run -B ${root_dir} \
            ${tool_dir}/afni_23.1.10.sif \
            3dTwotoComplex -prefix ${output_cpx} -RI ${input_real} ${input_imag} -overwrite
        # calculate phase image from complex-valued data
        singularity run -B ${root_dir} \
            ${tool_dir}/afni_23.1.10.sif \
           3dcalc -prefix ${output_phase} -cx2r PHASE -a ${output_cpx} -expr 'a' -overwrite
        # calculate magnitude image from complex-valued data
        singularity run -B ${root_dir} \
            ${tool_dir}/afni_23.1.10.sif \
           3dcalc -prefix ${output_abs} -cx2r ABS -a ${output_cpx} -expr 'a' -overwrite
        # run nordic
        matlab -nodesktop \
            -batch "addpath('/cluster/home/mliu23/GIT/NORDIC_Raw/'); ARG.DIROUT='${nordic_func_dir}', NIFTI_NORDIC('${output_abs}','${output_phase}','${output_nordic}', ARG);exit"
        gzip ${nordic_func_dir}/${output_nordic}.nii
        # cp
        cp ${func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_part-mag_bold.json \
            ${nordic_func_dir}/sub-${sub_id}_ses-${ses_id}_task-${task}_run-${run}_part-mag_bold.json
    done
done

# copy anat and fmap to nordic folder. symlink not accepted
if [ -d ${base_dir}/Nifti_nordic/sub-${sub_id}/ses-${ses_id} ]; then
    cp -r ${base_dir}/Nifti/sub-${sub_id}/ses-${ses_id}/anat \
          ${base_dir}/Nifti_nordic/sub-${sub_id}/ses-${ses_id}/
    cp -r ${base_dir}/Nifti/sub-${sub_id}/ses-${ses_id}/fmap \
          ${base_dir}/Nifti_nordic/sub-${sub_id}/ses-${ses_id}/    
fi

            
