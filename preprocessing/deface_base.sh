#!/bin/bash
# deface T1w/T2w of one session with pydeface (needs FSL), for openneuro upload
# writes a copy of the session to Nifti_defaced, other files are hard-linked
set -u -o pipefail

SRC_SES=${base_dir}/Nifti/sub-${sub_id}/ses-${ses_id}
DST_SES=${base_dir}/Nifti_defaced/sub-${sub_id}/ses-${ses_id}

if [ ! -d "${SRC_SES}" ]; then
    echo "no session folder ${SRC_SES}" >&2
    exit 1
fi

# hard-link all files except the anat images
while IFS= read -r -d '' f; do
    rel="${f#"${SRC_SES}"/}"
    out="${DST_SES}/${rel}"
    b="$(basename "$f")"
    if [[ "$f" == */anat/* && "$b" == *.nii.gz && ( "$b" == *T1w*.nii.gz || "$b" == *T2w*.nii.gz ) ]]; then
        continue
    fi
    mkdir -p "$(dirname "$out")"
    [ -e "$out" ] || ln "$f" "$out" 2>/dev/null || cp -p "$f" "$out"
done < <(find "${SRC_SES}" -type f -print0)

# deface anat images
mkdir -p "${DST_SES}/anat"
n_fail=0
shopt -s nullglob
for in in "${SRC_SES}"/anat/*T1w*.nii.gz "${SRC_SES}"/anat/*T2w*.nii.gz; do
    out="${DST_SES}/anat/$(basename "$in")"
    if [ -s "$out" ]; then
        continue
    fi
    echo "deface $(basename "$in")"
    if ! (pydeface "$in" --outfile "$out" --force && [ -s "$out" ]); then
        echo "failed $in" >&2
        rm -f "$out"        # remove partial output
        n_fail=$((n_fail+1))
    fi
done
shopt -u nullglob

[ "${n_fail}" -eq 0 ] || exit 1
