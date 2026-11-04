#!/bin/bash
############
# set up variables and directories
############
base_dir=/path/to/QUANTUM_4S
tool_dir=/path/to/software
out_dir=${base_dir}/ROIs
group_dir=${base_dir}/RSA_group
hcp_atlas=${tool_dir}/afni_atlases_dist/MNI_Glasser_HCP_v1.0.nii.gz
aal_atlas=${tool_dir}/AAL3/AAL3v1.nii.gz
afni="singularity exec -B /path/to:/path/to ${tool_dir}/afni_withr_24.0.08.sif"

context_z=${group_dir}/context_model_context_Z.nii.gz
subtask_z=${group_dir}/context_model_task_Z.nii.gz
cue_z=${group_dir}/context_model_cue_resp_Z.nii.gz

mkdir -p ${out_dir}

#### resample atlases to 2mm ####
${afni} 3dresample -master ${context_z} -input ${hcp_atlas} \
    -prefix ${out_dir}/HCP_2mm.nii.gz -overwrite -rmode NN
${afni} 3dresample -master ${context_z} -input ${aal_atlas} \
    -prefix ${out_dir}/AAL3_2mm.nii.gz -overwrite -rmode NN
hcp=${out_dir}/HCP_2mm.nii.gz
aal=${out_dir}/AAL3_2mm.nii.gz

#### anatomical masks ####
# DLPFC left, HCP: 63 67 68 73 83 84 85 86
${afni} 3dcalc -a ${hcp} -expr 'step(amongst(a,63,67,68,73,83,84,85,86))' \
    -prefix ${out_dir}/anat_DLPFC_L.nii.gz -overwrite
# IFC left, HCP: 74 75 76 77 79 80 81
${afni} 3dcalc -a ${hcp} -expr 'step(amongst(a,74,75,76,77,79,80,81))' \
    -prefix ${out_dir}/anat_IFC_L.nii.gz -overwrite
# MD bilateral, AAL3: 135 136 137 138
${afni} 3dcalc -a ${aal} -expr 'step(amongst(a,135,136,137,138))' \
    -prefix ${out_dir}/anat_MD_bilateral.nii.gz -overwrite

#### functional x anatomical ####
${afni} 3dcalc -a ${context_z} -b ${out_dir}/anat_DLPFC_L.nii.gz -expr 'step(a-2.8)*step(b)' \
    -prefix ${out_dir}/mask_context_DLPFC.nii.gz -overwrite
${afni} 3dcalc -a ${subtask_z} -b ${out_dir}/anat_DLPFC_L.nii.gz -expr 'step(a-2.8)*step(b)' \
    -prefix ${out_dir}/mask_subtask_DLPFC.nii.gz -overwrite
${afni} 3dcalc -a ${subtask_z} -b ${out_dir}/anat_IFC_L.nii.gz -expr 'step(a-2.8)*step(b)' \
    -prefix ${out_dir}/mask_subtask_IFC.nii.gz -overwrite
${afni} 3dcalc -a ${cue_z} -b ${out_dir}/anat_IFC_L.nii.gz -expr 'step(a-2.8)*step(b)' \
    -prefix ${out_dir}/mask_effective_cue_IFC.nii.gz -overwrite
