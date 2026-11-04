# PFC -> target (default MD), PFC sources subsampled to the smallest ROI size

import numpy as np
import pandas as pd

import activity_flow as af

ANALYSIS = "pfc_to_md_matched"


def run_subject(sub):
    out_csv = f"{af.per_subject_dir(ANALYSIS)}/sub-{sub}.csv"
    rng = np.random.default_rng(sub)
    masks = af.build_masks()
    match_size = min(int(masks[r].sum()) for r in af.CORTEX_ROIS)
    targets = [af.TARGET_NAME]
    e1, e2, ts1, ts2 = af.load_subject(sub, {k: masks[k] for k in af.PFC_SOURCES + targets})

    rows = []
    for src in af.PFC_SOURCES:
        n_src = e1[src].shape[0]
        n_res = af.N_RESAMPLE if n_src > match_size else 1
        for tgt in targets:
            scores = []
            for _ in range(n_res):
                idx = (rng.choice(n_src, match_size, replace=False)
                       if n_src > match_size else np.arange(n_src))
                fc1 = af.run_all_pca_fc(ts1[src][:, idx], ts1[tgt])
                fc2 = af.run_all_pca_fc(ts2[src][:, idx], ts2[tgt])
                scores.append(af.score(e1[src][idx], e2[src][idx], fc1, fc2, e1[tgt], e2[tgt]))
            rows.append(dict(subject=sub, source=src, target=tgt, match_size=match_size,
                             n_resample=n_res, ncaf=float(np.mean(scores))))
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"sub-{sub} saved {out_csv}")


def aggregate():
    af.combine_csvs(ANALYSIS)


if __name__ == "__main__":
    af.main(run_subject, aggregate)
