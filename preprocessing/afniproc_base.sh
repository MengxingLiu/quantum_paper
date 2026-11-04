#!/bin/bash


#root_dir=/path/to
#tool_dir=/path/to/software/
#base_dir=/path/to/QUANTUM_4S/
ses_dir=${base_dir}/Nifti_nordic/sub-${sub_id}/ses-${ses_id}
timing_dir=${base_dir}/GLM_1Ds/sub-${sub_id}/ses-${ses_id}

SUMA_dir=${base_dir}/freesurfer/${sub_id}/ses-${ses_id}/sub-${sub_id}/SUMA
SS_anat_mgz=${base_dir}/freesurfer/${sub_id}/ses-${ses_id}/sub-${sub_id}/mri/brain.mgz
SS_anat=${base_dir}/freesurfer/${sub_id}/ses-${ses_id}/sub-${sub_id}/mri/brain.nii.gz


singularity run \
     -B ${root_dir}:${root_dir} \
    ${tool_dir}/freesurfer_7.3.0_reconall.sif \
    mri_convert ${SS_anat_mgz} ${SS_anat}

result_dir=${base_dir}/afni_proc/sub-${sub_id}/ses-${ses_id}/
if [ ! -d ${result_dir} ]; then
    mkdir -p ${result_dir}
fi


###### for VisMotor task ######
if [ ! -f ${result_dir}/task-VisMotor/stats.${sub_id}+tlrc.HEAD ];then

cd ${result_dir}
#if [ -d ${result_dir}/task-VisMotor ];then
#rm -rf ${result_dir}/task-VisMotor
#fi
#if [ -f proc_task-VisMotor ]; then
#rm proc_task-VisMotor
#fi


singularity run \
     -B ${root_dir}:${root_dir} \
    ${tool_dir}/afni_withr_24.0.08.sif \
    afni_proc.py                                                             \
            -script                   proc_task-VisMotor                               \
            -out_dir                  ${result_dir}/task-VisMotor            \
            -subj_id                  ${sub_id}                              \
            -copy_anat                ${SS_anat}                             \
            -anat_has_skull           no                                     \
            -dsets                    ${ses_dir}/func/sub-${sub_id}_ses-${ses_id}_task-VisMotor_run-001_part-mag_bold.nii.gz                 \
            -anat_follower            anat_w_skull anat                      \
                                      ${SUMA_dir}/sub-${sub_id}_SurfVol.nii  \
            -anat_follower_ROI        aaseg anat                             \
                                      ${SUMA_dir}/aparc.a2009s+aseg_REN_all.nii.gz  \
            -anat_follower_ROI        aeseg epi                              \
                                      ${SUMA_dir}/aparc.a2009s+aseg_REN_all.nii.gz  \
            -anat_follower_ROI        FSvent epi ${SUMA_dir}/fs_ap_latvent.nii.gz   \
            -anat_follower_ROI        FSWe epi ${SUMA_dir}/fs_ap_wm.nii.gz          \
            -anat_follower_erode      FSvent FSWe                            \
            -blocks                   tshift align tlrc volreg mask      \
                                      scale regress                          \
            -align_unifize_epi        local                                  \
            -align_opts_aea           -cost lpc+ZZ                           \
                                      -giant_move                            \
                                      -check_flip                            \
            -tlrc_base                MNI152_2009_template.nii.gz            \
            -volreg_align_to          MIN_OUTLIER                            \
            -volreg_align_e2a                                                \
            -volreg_tlrc_warp                                                \
            -volreg_compute_tsnr      yes                                    \
            -mask_epi_anat            yes                                    \
            -regress_stim_times       ${timing_dir}/block_time.1D          \
            -regress_stim_labels      checkerboard                                \
            -regress_basis            'BLOCK(27,1)'                          \
            -regress_opts_3dD         -jobs 32                                \
                                      -gltsym 'SYM: checkerboard'                \
                                      -glt_label 1 checkerboard                       \
            -regress_motion_per_run                                          \
            -regress_censor_motion    0.3                                    \
            -regress_censor_outliers  0.05                                   \
            -regress_compute_fitts                                           \
            -regress_make_ideal_sum   sum_ideal.1D                           \
            -regress_est_blur_epits                                          \
            -regress_est_blur_errts                                          \
            -regress_run_clustsim     no                                     \
            -regress_ROI_PC           FSvent 3                               \
            -regress_anaticor_fast                                           \
            -regress_anaticor_label   FSvent                                   \
            -regress_ROI_PC           FSWe 3                               \
            -regress_ROI_PC_per_run   FSWe FSvent                            \
            -regress_anaticor_fast                                           \
            -regress_anaticor_label   FSWe                                   \
            -regress_apply_mask                                              \
            -regress_reml_exec                                               \
            -html_review_style        pythonic                               \
            -execute


    # zip all BRIK files to save space
    cd ${result_dir}/task-VisMotor
    for i in *BRIK; do gzip ${i}; done


fi


######### for Quantum4S task ########
# skip if preprocessed
if [ ! -f ${result_dir}/task-Quantum4S/stats.${sub_id}+tlrc.HEAD ];then
cd ${result_dir}


#if [ -d ${result_dir}/task-Quantum4S ];then
#rm -rf ${result_dir}/task-Quantum4S
#fi
#if [ -f proc_task-Quantum4S ]; then
#rm proc_task-Quantum4S
#fi


singularity run \
     -B ${root_dir}:${root_dir} \
    ${tool_dir}/afni_withr_24.0.08.sif \
    afni_proc.py                                                             \
            -script                   proc_task-Quantum4S                    \
            -out_dir                  ${result_dir}/task-Quantum4S           \
            -subj_id                  ${sub_id}                              \
            -copy_anat                ${SS_anat}                             \
            -anat_has_skull           no                                     \
            -dsets                    ${ses_dir}/func/sub-${sub_id}_ses-${ses_id}_task-Quantum4S_run-00*_part-mag_bold.nii.gz                                       \
             -anat_follower            anat_w_skull anat                      \
                                      ${SUMA_dir}/sub-${sub_id}_SurfVol.nii  \
            -anat_follower_ROI        aaseg anat                             \
                                      ${SUMA_dir}/aparc.a2009s+aseg_REN_all.nii.gz  \
            -anat_follower_ROI        aeseg epi                              \
                                      ${SUMA_dir}/aparc.a2009s+aseg_REN_all.nii.gz  \
            -anat_follower_ROI        FSvent epi ${SUMA_dir}/fs_ap_latvent.nii.gz   \
            -anat_follower_ROI        FSWe epi ${SUMA_dir}/fs_ap_wm.nii.gz          \
            -anat_follower_erode      FSvent FSWe                            \
            -blocks                   tshift align tlrc volreg mask          \
                                      scale regress                          \
            -align_unifize_epi        local                                  \
            -align_opts_aea           -cost lpc+ZZ                           \
                                      -giant_move                            \
                                      -check_flip                            \
            -tlrc_base                MNI152_2009_template.nii.gz            \
            -volreg_align_to          MIN_OUTLIER                            \
            -volreg_align_e2a                                                \
            -volreg_tlrc_warp                                                \
            -volreg_compute_tsnr      yes                                    \
            -mask_epi_anat            yes                                    \
            -regress_stim_times       ${timing_dir}/cue_time.1D              \
                                      ${timing_dir}/probe_time.1D            \
                                      ${timing_dir}/feedback_time.1D          \
            -regress_stim_labels      cue probe feedback                     \
            -regress_basis            'SPMG'                                 \
            -regress_opts_3dD         -jobs 32                               \
                                      -gltsym 'SYM: cue -feedback'           \
                                      -glt_label 1 cue-feedback              \
            -regress_motion_per_run                                          \
            -regress_censor_motion    0.3                                    \
            -regress_censor_outliers  0.05                                   \
            -regress_compute_fitts                                           \
            -regress_make_ideal_sum   sum_ideal.1D                           \
            -regress_est_blur_epits                                          \
            -regress_est_blur_errts                                          \
            -regress_run_clustsim     yes                                    \
            -regress_ROI_PC           FSvent 3                               \
            -regress_anaticor_fast                                           \
            -regress_anaticor_label   FSvent                                   \
            -regress_ROI_PC           FSWe 3                               \
            -regress_anaticor_fast                                           \
            -regress_anaticor_label   FSWe                                   \
            -regress_ROI_PC_per_run   FSWe FSvent                            \
            -regress_apply_mask                                              \
            -regress_reml_exec                                               \
            -html_review_style        pythonic                               \
            -execute


fi





