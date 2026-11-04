# seed pattern contribution (real - uniform) of each thalamic nucleus predicting PFC
# nuclei are subsampled to the smallest nucleus
# python3 af_nuclei.py -subject <id>, then -aggregate
# -roi_dir DIR overrides the PFC (union) source set in activity_flow.py; nuclei are
# defined by AAL3 label below, not by -roi_dir/-target

import numpy as np
import pandas as pd
import nibabel as nib
from scipy import stats

import activity_flow as af

ANALYSIS = "nuclei_matched"
MIN_VOXELS = 50

# AAL3 labels, L + R. MD = MDm + MDl.
NUCLEI = {
    "MD":  [135, 136, 137, 138],
    "AV":  [121, 122], "LP": [123, 124], "VA": [125, 126], "VL": [127, 128],
    "VPL": [129, 130], "IL": [131, 132], "Re": [133, 134], "LGN": [139, 140],
    "MGN": [141, 142], "PuI": [143, 144], "PuM": [145, 146], "PuA": [147, 148],
    "PuL": [149, 150],
}


def build_masks():
    aal = nib.load(af.AAL3).get_fdata().astype(int)
    masks = {n: np.isin(aal, ids) for n, ids in NUCLEI.items()}
    masks = {n: m for n, m in masks.items() if m.sum() >= MIN_VOXELS}
    masks["PFC"] = af.build_masks()["union"]
    return masks


def run_subject(sub):
    out_csv = f"{af.per_subject_dir(ANALYSIS)}/sub-{sub}.csv"
    rng = np.random.default_rng(sub)
    masks = build_masks()
    nuclei = [n for n in NUCLEI if n in masks]
    match_size = min(int(masks[n].sum()) for n in nuclei)
    e1, e2, ts1, ts2 = af.load_subject(sub, masks)

    rows = []
    for nuc in nuclei:
        n = ts1[nuc].shape[1]
        n_res = af.N_RESAMPLE if n > match_size else 1
        real, uni = [], []
        for _ in range(n_res):
            idx = rng.choice(n, match_size, replace=False) if n > match_size else np.arange(n)
            fc1 = af.run_all_pca_fc(ts1[nuc][:, idx], ts1["PFC"])
            fc2 = af.run_all_pca_fc(ts2[nuc][:, idx], ts2["PFC"])
            r, u = af.score(e1[nuc][idx], e2[nuc][idx], fc1, fc2, e1["PFC"], e2["PFC"],
                            uniform=True)
            real.append(r)
            uni.append(u)
        rows.append(dict(subject=sub, nucleus=nuc, n_vox=n, match_size=match_size,
                         ncaf=np.mean(real), ncaf_uniform=np.mean(uni),
                         ncaf_gain=np.mean(real) - np.mean(uni)))
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"sub-{sub} saved {out_csv}")


def aggregate():
    res = af.combine_csvs(ANALYSIS)
    rows = []
    for nuc, g in res.groupby("nucleus"):
        t, p = stats.ttest_1samp(g["ncaf_gain"], 0)
        rows.append(dict(nucleus=nuc, n_vox=int(g["n_vox"].iloc[0]),
                         gain=g["ncaf_gain"].mean(), t=t, p=p, n=len(g)))
    summ = pd.DataFrame(rows).sort_values("gain", ascending=False)
    summ.to_csv(f"{af.OUT_DIR}/{ANALYSIS}/summary.csv", index=False)
    print(summ.round(4).to_string(index=False))


if __name__ == "__main__":
    af.main(run_subject, aggregate)
