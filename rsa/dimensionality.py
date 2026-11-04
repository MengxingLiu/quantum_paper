# participation ratio of single-trial cue patterns, MD vs PFC and LGN vs V1
# cortex is subsampled to the thalamus voxel count
# python3 dimensionality.py -subject <id>, then -aggregate

import numpy as np
import pandas as pd
import nibabel as nib
from scipy import stats

import activity_flow as af

ANALYSIS = "dimensionality"
PAIRS = {"md_pfc": ("MD", "PFC"), "lgn_v1": ("LGN", "V1")}   # (thalamus, cortex)


def build_masks():
    aal = nib.load(af.AAL3).get_fdata().astype(int)
    glasser = nib.load(af.GLASSER).get_fdata().astype(int)
    m = af.build_masks()
    return {"MD": m["MD"], "PFC": m["union"],
            "LGN": np.isin(aal, [139, 140]),            # AAL3 Thal_LGN_L/R
            "V1": np.isin(glasser, [1, 1001])}          # glasser V1 L/R


def load_trials(sub, masks):
    # single-trial cue betas pooled over all sessions -> {region
    g1, g2 = af.get_sessions(sub, af.load_behavior())
    parts = {r: [] for r in masks}
    for ses in g1 + g2:
        fn = f"{af.DECONV_DIR}/sub-{sub}/ses-{ses}/Quantum4S_sub-{sub}_ses-{ses}_{af.EVENT}_LSS.nii.gz"
        d = nib.load(fn).get_fdata()                      # (x, y, z, trials)
        for r, m in masks.items():
            parts[r].append(d[m].T)
    return {r: np.concatenate(parts[r], 0) for r in masks}


def zscore_voxels(M):
    # z-score each voxel across trials
    sd = M.std(0, keepdims=True)
    sd[sd == 0] = 1.0
    return (M - M.mean(0, keepdims=True)) / sd


def participation_ratio(M):
    s = np.linalg.svd(M - M.mean(0), full_matrices=False, compute_uv=False)
    lam = s ** 2
    lam = lam[lam > 1e-10]
    return float(lam.sum() ** 2 / np.sum(lam ** 2)) if lam.size else 0.0


def matched_pr(M, k, rng):
    # mean PR over random k-voxel subsamples
    n = M.shape[1]
    if n <= k:
        return participation_ratio(M)
    return float(np.mean([participation_ratio(M[:, rng.choice(n, k, replace=False)])
                          for _ in range(af.N_RESAMPLE)]))


def run_subject(sub):
    out_csv = f"{af.per_subject_dir(ANALYSIS)}/sub-{sub}.csv"
    masks = build_masks()
    data = {r: zscore_voxels(x) for r, x in load_trials(sub, masks).items()}
    rows = []
    for pair, (thal, ctx) in PAIRS.items():
        rng = np.random.default_rng(sub)
        k = data[thal].shape[1]
        rows.append(dict(subject=sub, pair=pair, region=thal, n_vox=k,
                         PR=participation_ratio(data[thal])))
        rows.append(dict(subject=sub, pair=pair, region=ctx, n_vox=k,
                         PR=matched_pr(data[ctx], k, rng)))
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"sub-{sub} saved {out_csv}")


def aggregate():
    res = af.combine_csvs(ANALYSIS)
    for pair, (thal, ctx) in PAIRS.items():
        d = res[res.pair == pair].pivot(index="subject", columns="region", values="PR")
        t, p = stats.ttest_rel(d[ctx], d[thal])
        print(f"{pair}: {ctx} {d[ctx].mean():.1f} vs {thal} {d[thal].mean():.1f}, "
              f"t({len(d) - 1}) = {t:.2f}, p = {p:.3g}")


if __name__ == "__main__":
    af.main(run_subject, aggregate)
