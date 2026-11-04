# permutation nulls (seed shuffle and FC shuffle) for PFC <-> target (default MD)
# aggregate after af_pfc_to_md_matched.py and af_uniform_baseline.py are aggregated
# -roi_dir DIR and -target FILE override the defaults in activity_flow.py

from glob import glob

import numpy as np
import pandas as pd

import activity_flow as af

ANALYSIS = "permutation"
DIRECTIONS = ["pfc2md", "md2pfc"]


def run_subject(sub):
    out_npz = f"{af.per_subject_dir(ANALYSIS)}/sub-{sub}.npz"
    rng = np.random.default_rng(sub)
    masks = af.build_masks()
    tgt_name = af.TARGET_NAME
    match_size = min(int(masks[r].sum()) for r in af.CORTEX_ROIS)
    e1, e2, ts1, ts2 = af.load_subject(sub, {k: masks[k] for k in ["union", tgt_name]})
    out = {}

    # PFC -> target, source size-matched: N_PERM / N_RESAMPLE permutations per subsample
    n_src = ts1["union"].shape[1]
    subsamples = [rng.choice(n_src, match_size, replace=False) for _ in range(af.N_RESAMPLE)]
    per_perm = af.N_PERM // af.N_RESAMPLE
    obs, null_seed, null_fc = [], [], []
    for idx in subsamples:
        fc1 = af.run_all_pca_fc(ts1["union"][:, idx], ts1[tgt_name])
        fc2 = af.run_all_pca_fc(ts2["union"][:, idx], ts2[tgt_name])
        args = (e1["union"][idx], e2["union"][idx], fc1, fc2, e1[tgt_name], e2[tgt_name])
        nc = af.noise_ceiling(*args[:4])
        obs.append(af.cal_af(*args, nc)[1])
        null_seed.append(af.null_shuffle_seed(*args, nc, per_perm, rng))
        null_fc.append(af.null_shuffle_fc(*args, nc, per_perm, rng))
    out["obs|pfc2md"] = np.mean(obs)
    out["nullseed|pfc2md"] = np.concatenate(null_seed)
    out["nullfc|pfc2md"] = np.concatenate(null_fc)

    # target -> PFC, full union
    fc1 = af.run_all_pca_fc(ts1[tgt_name], ts1["union"])
    fc2 = af.run_all_pca_fc(ts2[tgt_name], ts2["union"])
    args = (e1[tgt_name], e2[tgt_name], fc1, fc2, e1["union"], e2["union"])
    nc = af.noise_ceiling(*args[:4])
    out["obs|md2pfc"] = af.cal_af(*args, nc)[1]
    out["nullseed|md2pfc"] = af.null_shuffle_seed(*args, nc, af.N_PERM, rng)
    out["nullfc|md2pfc"] = af.null_shuffle_fc(*args, nc, af.N_PERM, rng)

    np.savez_compressed(out_npz, **out)
    print(f"sub-{sub} saved {out_npz}")


def observed_4b():
    # observed PFC-union scores from the matched and uniform analyses
    m = pd.read_csv(f"{af.OUT_DIR}/pfc_to_md_matched/results.csv")
    pfc2md = m[m.source == "union"].set_index("subject")["ncaf"]
    u = pd.read_csv(f"{af.OUT_DIR}/uniform_baseline/results.csv")
    md2pfc = u[(u.source == "union") & (u.direction == "md2pfc")].set_index("subject")["ncaf"]
    return {"pfc2md": pfc2md, "md2pfc": md2pfc}


def aggregate():
    files = sorted(glob(f"{af.per_subject_dir(ANALYSIS)}/sub-*.npz"))
    npzs = [np.load(f) for f in files]
    observed = observed_4b()
    nulls, rows = {}, []
    for d in DIRECTIONS:
        ns = np.stack([z[f"nullseed|{d}"] for z in npzs]).mean(0)
        nf = np.stack([z[f"nullfc|{d}"] for z in npzs]).mean(0)
        nulls[f"nullseed|{d}"], nulls[f"nullfc|{d}"] = ns, nf
        obs = float(observed[d].mean())
        rows.append(dict(direction=d, n=len(files), obs=obs,
                         obs_recomputed=float(np.mean([z[f"obs|{d}"] for z in npzs])),
                         null_seed_mean=float(ns.mean()), null_fc_mean=float(nf.mean()),
                         p_seed=float(np.mean(ns >= obs)), p_fc=float(np.mean(nf >= obs))))
    np.savez_compressed(f"{af.OUT_DIR}/{ANALYSIS}/group_null.npz", **nulls)
    summ = pd.DataFrame(rows)
    summ.to_csv(f"{af.OUT_DIR}/{ANALYSIS}/summary.csv", index=False)
    print(summ.round(4).to_string(index=False))


if __name__ == "__main__":
    af.main(run_subject, aggregate)
