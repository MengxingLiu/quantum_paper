# shared functions for activity flow, adapted from Chen et al. 2024
# prediction = zscore(zscore(seed) @ FC), FC from residual time series (pca on seed + regression)
# cross-validated across session halves and divided by the noise ceiling
# set the data path with QUANTUM4S_DIR
# source ROIs and target region default to the prefrontal set / MD below, override via
# -roi_dir DIR (one source per mask file in the folder, named after the file) and
# -target FILE (same naming) on any script that calls af.main()

import os
import argparse
from glob import glob

import numpy as np
import pandas as pd
import nibabel as nib
from nibabel import affines
from scipy.stats import zscore
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

# configuration
PROJ = os.environ.get("QUANTUM4S_DIR", "/path/to/QUANTUM_4S")
DECONV_DIR = f"{PROJ}/Deconvolve_afni"      # session GLMs and single-trial (LSS) betas
AFNIPROC_DIR = f"{PROJ}/afni_proc"          # GLM residuals (errts) as .npy
ROI_DIR = f"{PROJ}/ROIs"           # masks from create_FC_masks.sh
BEH_CSV = f"{PROJ}/GLM_1Ds/df_beh.csv"
GLASSER = f"{PROJ}/Masks/MNI_Glasser_HCP_v1.0_res.nii"
AAL3 = f"{ROI_DIR}/AAL3_2mm.nii.gz"
OUT_DIR = f"{PROJ}/Activity_Flow"

EVENT = "cue"          # all analyses use the cue period
CUE_SUBBRICK = 2       # cue#0_Coef in Quantum4S_..._stats_events.nii.gz
N_RESAMPLE = 100       # random subsamples for size matching
N_PERM = 5000          # permutations per null


# subjects, sessions, masks
def load_behavior():
    return pd.read_csv(BEH_CSV)


def all_subjects():
    return sorted(int(s) for s in load_behavior()["subid"].unique())


def get_sessions(sub, df):
    # sessions with behavioral data, split into halves (sessions 1-2, 3-4)
    usable = set(str(s) for s in df.loc[df["subid"] == sub, "ses"].unique())
    on_disk = sorted(os.path.basename(p).split("ses-")[1]
                     for p in glob(f"{DECONV_DIR}/sub-{sub}/ses-*"))
    ses = [s for s in on_disk if s in usable]
    return ses[:2], ses[2:4]


def load_mask(path):
    return nib.load(path).get_fdata() > 0


def _roi_name(path):
    # derive a short ROI name from a mask filename, e.g. mask_context_DLPFC.nii.gz -> context_DLPFC
    name = os.path.basename(path)
    name = name[:-7] if name.endswith(".nii.gz") else os.path.splitext(name)[0]
    return name[5:] if name.startswith("mask_") else name


def rois_from_dir(path, pattern="*"):
    # one source ROI per mask file in a directory matching pattern (default: all)
    files = sorted(glob(f"{path}/{pattern}.nii") + glob(f"{path}/{pattern}.nii.gz"))
    if not files:
        raise SystemExit(f"no {pattern}.nii/.nii.gz files found in {path}")
    return {_roi_name(f): f for f in files}


def build_masks():
    # prefrontal ROIs, their union, and the target region (bilateral, split into L/R)
    global CORTEX_ROIS, PFC_SOURCES, TARGET_NAME, MD_BILATERAL
    if not globals().get("CORTEX_ROIS"):
        CORTEX_ROIS = rois_from_dir(ROI_DIR, pattern="mask_*")
        PFC_SOURCES = ["union"] + list(CORTEX_ROIS)
    if not globals().get("TARGET_NAME"):
        TARGET_NAME, MD_BILATERAL = "MD", f"{ROI_DIR}/anat_MD_bilateral.nii.gz"
    masks = {name: load_mask(path) for name, path in CORTEX_ROIS.items()}
    masks["union"] = np.logical_or.reduce([masks[n] for n in CORTEX_ROIS])

    tgt = nib.load(MD_BILATERAL)
    masks[TARGET_NAME] = tgt.get_fdata() > 0
    ijk = np.array(np.where(masks[TARGET_NAME]))
    x = affines.apply_affine(tgt.affine, ijk.T)[:, 0]
    for side, sel in [(f"{TARGET_NAME}_L", x < 0), (f"{TARGET_NAME}_R", x > 0)]:
        m = np.zeros(masks[TARGET_NAME].shape, dtype=bool)
        m[tuple(ijk[:, sel])] = True
        masks[side] = m
    return masks


# data
def extract_evoke(sub, ses_list, region_masks):
    # cue-period beta averaged over a half's sessions -> {region
    acc = {r: [] for r in region_masks}
    for ses in ses_list:
        fn = f"{DECONV_DIR}/sub-{sub}/ses-{ses}/Quantum4S_sub-{sub}_ses-{ses}_stats_events.nii.gz"
        vol = nib.load(fn).get_fdata().squeeze()[..., CUE_SUBBRICK]
        for r, m in region_masks.items():
            acc[r].append(vol[m])
    return {r: np.mean(acc[r], axis=0) for r in region_masks}


def load_errts_ts(sub, ses_list, region_masks):
    # residual time series concatenated over a half's sessions -> {region
    out = {r: [] for r in region_masks}
    for ses in ses_list:
        vol = np.load(f"{AFNIPROC_DIR}/sub-{sub}/ses-{ses}/task-Quantum4S/errts.{sub}.npy",
                      mmap_mode="r")                    # (x, y, z, t)
        for r, m in region_masks.items():
            out[r].append(np.asarray(vol[m, :]).T)
    return {r: np.concatenate(out[r], axis=0) for r in region_masks}


def load_subject(sub, region_masks):
    # evoked patterns and residual time series for both session halves
    g1, g2 = get_sessions(sub, load_behavior())
    e1, e2 = extract_evoke(sub, g1, region_masks), extract_evoke(sub, g2, region_masks)
    ts1, ts2 = load_errts_ts(sub, g1, region_masks), load_errts_ts(sub, g2, region_masks)
    print(f"sub-{sub}: halves {g1} / {g2}")
    return e1, e2, ts1, ts2


# activity flow
def run_all_pca_fc(seed_ts, target_ts):
    # FC matrix (seed_vox x target_vox)
    keep = np.mean(target_ts, axis=1) != 0              # drop censored time points
    seed_ts, target_ts = seed_ts[keep], target_ts[keep]
    n_comps = np.amin([target_ts.shape[0] - 1, target_ts.shape[1] - 1, seed_ts.shape[1] - 1])
    pca = PCA(n_components=n_comps, svd_solver="full")
    reg = LinearRegression().fit(pca.fit_transform(seed_ts), target_ts)
    return pca.inverse_transform(reg.coef_).T


def predict(seed, fc):
    return zscore(np.dot(zscore(seed), fc))


def cal_nc(pred1, pred2):
    # noise ceiling
    y = np.r_[pred1, pred2]
    x = np.r_[pred2, pred1]
    vU = np.sum((x - np.mean(x)) ** 2)
    vE = np.sum((y - x) ** 2)
    return np.sqrt(vU) / np.sqrt(vU + vE)


def noise_ceiling(seed1, seed2, fc1, fc2):
    return cal_nc(predict(seed1, fc1), predict(seed2, fc2))


def cal_af(seed1, seed2, fc1, fc2, target1, target2, nc):
    # cross-validated prediction
    af = (np.corrcoef(target1, predict(seed2, fc2))[0][1]
          + np.corrcoef(target2, predict(seed1, fc1))[0][1]) / 2
    return af, af / nc


def cal_af_uniform(seed1, seed2, fc1, fc2, target1, target2, nc):
    pred1 = zscore(np.dot(np.ones(seed1.shape), fc1))
    pred2 = zscore(np.dot(np.ones(seed2.shape), fc2))
    af = (np.corrcoef(target1, pred2)[0][1] + np.corrcoef(target2, pred1)[0][1]) / 2
    return af, af / nc


def score(seed1, seed2, fc1, fc2, target1, target2, uniform=False):
    # normalized prediction score, and optionally the uniform-seed score
    nc = noise_ceiling(seed1, seed2, fc1, fc2)
    _, real = cal_af(seed1, seed2, fc1, fc2, target1, target2, nc)
    if not uniform:
        return real
    _, uni = cal_af_uniform(seed1, seed2, fc1, fc2, target1, target2, nc)
    return real, uni


# permutation nulls
def _batched_pearson(P, v):
    # pearson r between each row of P (B, n) and v (n,)
    Pc = P - P.mean(axis=1, keepdims=True)
    vc = v - v.mean()
    return (Pc @ vc) / np.sqrt((Pc ** 2).sum(axis=1) * (vc ** 2).sum())


def null_shuffle_seed(seed1, seed2, fc1, fc2, target1, target2, nc, n_perm, rng, chunk=2000):
    # seed-shuffle null
    out = np.empty(n_perm)
    done = 0
    while done < n_perm:
        b = min(chunk, n_perm - done)
        S1 = zscore(rng.permuted(np.broadcast_to(seed1, (b, seed1.size)), axis=1), axis=1)
        S2 = zscore(rng.permuted(np.broadcast_to(seed2, (b, seed2.size)), axis=1), axis=1)
        af = (_batched_pearson(S2 @ fc2, target1) + _batched_pearson(S1 @ fc1, target2)) / 2
        out[done:done + b] = af / nc
        done += b
    return out


def null_shuffle_fc(seed1, seed2, fc1, fc2, target1, target2, nc, n_perm, rng):
    # FC-shuffle null
    s1, s2 = zscore(seed1), zscore(seed2)
    shape = fc1.shape
    flat1, flat2 = fc1.ravel().copy(), fc2.ravel().copy()
    out = np.zeros(n_perm)
    for p in range(n_perm):
        rng.shuffle(flat1)
        rng.shuffle(flat2)
        af = (np.corrcoef(target1, s2 @ flat2.reshape(shape))[0][1]
              + np.corrcoef(target2, s1 @ flat1.reshape(shape))[0][1]) / 2
        out[p] = af / nc
    return out


# per-subject jobs and aggregation
def per_subject_dir(analysis):
    d = f"{OUT_DIR}/{analysis}/per_subject"
    os.makedirs(d, exist_ok=True)
    return d


def combine_csvs(analysis):
    # concatenate per-subject CSVs -> {OUT_DIR}/{analysis}/results.csv
    files = sorted(glob(f"{per_subject_dir(analysis)}/sub-*.csv"))
    res = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    out = f"{OUT_DIR}/{analysis}/results.csv"
    res.to_csv(out, index=False)
    print(f"{len(files)} subjects, saved {out}")
    return res


def main(run_subject, aggregate):
    # CLI shared by the analysis scripts
    ap = argparse.ArgumentParser()
    ap.add_argument("-subject", type=int, help="run one subject")
    ap.add_argument("-aggregate", action="store_true", help="combine subjects")
    ap.add_argument("-roi_dir", help="directory of source ROI mask files (.nii/.nii.gz), "
                    "one source per file; overrides the default (mask_*.nii.gz in ROI_DIR)")
    ap.add_argument("-target", help="target region mask file; overrides the default (MD, bilateral)")
    a = ap.parse_args()

    global CORTEX_ROIS, PFC_SOURCES, TARGET_NAME, MD_BILATERAL
    if a.roi_dir:
        CORTEX_ROIS = rois_from_dir(a.roi_dir)
        PFC_SOURCES = ["union"] + list(CORTEX_ROIS)
    if a.target:
        TARGET_NAME, MD_BILATERAL = _roi_name(a.target), a.target

    if a.aggregate:
        aggregate()
    elif a.subject is not None:
        run_subject(a.subject)
    else:
        for s in all_subjects():
            run_subject(s)
        aggregate()
