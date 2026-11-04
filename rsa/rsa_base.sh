#!/bin/bash
# job for one session, submitted with qsub_generic.py (tool = rsa)
source ~/.bashrc
conda activate searchlight
ulimit -c 0
export JOBLIB_TEMP_FOLDER=/path/to/cache/
python3 -u ${code_dir}/rsa_searchlight.py -sub_id ${sub_id} -ses_id ${ses_id}
