#!/bin/bash

ses_dir=${base_dir}/Nifti/sub-${sub_id}/ses-${ses_id}
export SINGULARITYENV_FS_LICENSE=/path/to/freesurfer_license.txt

if [ ! -d ${base_dir}/freesurfer/${sub_id}/ses-${ses_id}/ ]; then
    mkdir -p ${base_dir}/freesurfer/${sub_id}/ses-${ses_id}/
fi
## run recon-all
check_file=${base_dir}/freesurfer/${sub_id}/ses-${ses_id}/sub-${sub_id}/mri/aparc+aseg.mgz
if [ ! -f  ${check_file} ]; then
singularity run \
     -B ${root_dir}:${root_dir} \
    ${tool_dir}/freesurfer_7.3.0_reconall.sif                                     \
    recon-all -all \
            -subjid sub-${sub_id} \
            -i ${ses_dir}/anat/sub-${sub_id}_ses-${ses_id}_T1w.nii.gz \
            -sd ${base_dir}/freesurfer/${sub_id}/ses-${ses_id}/
fi

## import to AFNI in NIFTI format
singularity run \
     -B ${root_dir}:${root_dir} \
    ${tool_dir}/afni-freesurfer_7.3.0.sif \
    @SUMA_Make_Spec_FS -NIFTI -sid sub-${sub_id} \
                    -fspath ${base_dir}/freesurfer/${sub_id}/ses-${ses_id}/sub-${sub_id}
