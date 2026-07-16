import os


def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes


def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where

    allowed template fields - follow python string module:

    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """
    info=[]
    t1w = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w')
    fm_pe0 = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_dir-pe0_run-{item:03d}_epi')
    fm_pe1 = create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_dir-pe1_run-{item:03d}_epi')
    task_QUANTUM_4S = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-Quantum4S_run-{item:03d}_bold')
    task_VisMotor = create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-VisMotor_run-{item:03d}_bold')
    info = {t1w: [], fm_pe0: [], fm_pe1:[], task_QUANTUM_4S:[], task_VisMotor:[] }
    for idx, seq in enumerate(seqinfo):
        
        x,y,z,n_vol,protocol,dcm_dir, TR, TE, image_type, series, total = (seq[6], seq[7], seq[8], seq[9], seq[12], seq[3], seq[10], seq[11], seq[19], seq[18], seq[0] )
        print("image_type",image_type)
        print(seq)
        type(seq)
        for i in range(len(seq)):
            print(i,seq[i])
        #x,y,z,n_vol,protocol,dcm_dir, TR, TE, image_type, series, total = (seq[6], seq[7], seq[8], seq[9], seq[12], seq[3], seq[10], seq[11], seq[19], seq[18], seq[0] )

        # t1_mprage --> T1w
        if (image_type == 'MP-RAGE') and ( z == 220 ):
            info[t1w] = [seq[2]]
        if (image_type == "epi") and (z == 18360 ):
            info[task_VisMotor].append({'item': seq[2]})
        if (image_type == "epi") and (z == 87720):
            info[task_QUANTUM_4S].append({'item': seq[2]})
        if (series == 'SE EPI') and (z==408):
            info[fm_pe0].append({'item': seq[2]})

        if (series == 'SE EPI REVPE') and (z==408):
            info[fm_pe1].append({'item': seq[2]})
        """
        The namedtuple `s` contains the following fields:

        * total_files_till_now
        * example_dcm_file
        * series_id
        * dcm_dir_name
        * unspecified2
        * unspecified3
        * dim1
        * dim2
        * dim3
        * dim4
        * TR
        * TE
        * protocol_name
        * is_motion_corrected
        * is_derived
        * patient_id
        * study_description
        * referring_physician_name
        * series_description
        * image_type
        """

    return info
