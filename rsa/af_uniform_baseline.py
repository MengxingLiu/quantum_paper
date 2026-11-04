# PFC <-> target (default MD) in both directions, real vs uniform seed
# uniform seed = constant vector, so the prediction only uses FC

import pandas as pd
from scipy import stats

import activity_flow as af

ANALYSIS = "uniform_baseline"


def run_subject(sub):
    out_csv = f"{af.per_subject_dir(ANALYSIS)}/sub-{sub}.csv"
    masks = af.build_masks()
    tgt_name = af.TARGET_NAME
    e1, e2, ts1, ts2 = af.load_subject(sub, {k: masks[k] for k in af.PFC_SOURCES + [tgt_name]})

    rows = []
    for direction in ["pfc2md", "md2pfc"]:
        for src in af.PFC_SOURCES:
            seed, target = (src, tgt_name) if direction == "pfc2md" else (tgt_name, src)
            fc1 = af.run_all_pca_fc(ts1[seed], ts1[target])
            fc2 = af.run_all_pca_fc(ts2[seed], ts2[target])
            real, uni = af.score(e1[seed], e2[seed], fc1, fc2, e1[target], e2[target],
                                 uniform=True)
            rows.append(dict(subject=sub, direction=direction, source=src,
                             ncaf=real, ncaf_uniform=uni))
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"sub-{sub} saved {out_csv}")


def aggregate():
    res = af.combine_csvs(ANALYSIS)
    rows = []
    for (d, src), g in res.groupby(["direction", "source"]):
        t, p = stats.ttest_rel(g["ncaf"], g["ncaf_uniform"])
        rows.append(dict(direction=d, source=src, ncaf=g["ncaf"].mean(),
                         ncaf_uniform=g["ncaf_uniform"].mean(), t=t, p=p, n=len(g)))
    pd.DataFrame(rows).to_csv(f"{af.OUT_DIR}/{ANALYSIS}/summary.csv", index=False)
    print(pd.DataFrame(rows).round(4).to_string(index=False))


if __name__ == "__main__":
    af.main(run_subject, aggregate)
