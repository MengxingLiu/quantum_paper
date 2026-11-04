#!/bin/python3
# RSA for one session, searchlight (default) or whole-ROI mode
# neural RDM = 1 - pearson r of cue LSS betas, cross-run pairs only, regressed on the behavior RDMs

import os, copy, argparse, datetime
import numpy as np
import pandas as pd
import nibabel as nib
import statsmodels.api as sm
from scipy.spatial.distance import pdist, squareform
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler
from joblib import Parallel, delayed

base_dir = os.environ.get("QUANTUM4S_DIR", "/path/to/QUANTUM_4S")
DD_dir_base = f"{base_dir}/Deconvolve_afni"
out_root = f"{base_dir}/RSA"
beh_csv = f"{base_dir}/GLM_1Ds/df_beh.csv"
default_mask = f"{base_dir}/Masks/GM_mask_res.nii.gz"
n_trials = 200                                   # 5 runs x 40 trials
run_labels = np.repeat(np.arange(5), 40)         # 0 for run 1, 1 for run 2, ..., 4 for run 5

# regression models, context, hypercontext and context belief are fit separately since they are nested
nuisance = ["beh_task", "beh_cue_resp", "beh_task_resp", "beh_cue_resp_key", "beh_task_resp_key",
            "beh_prop_red", "beh_motion_coh", "beh_face_type", "beh_scene_type"]
MODELS = {"context_model": ["beh_context"] + nuisance,
          "hypercontext_model": ["beh_feature"] + nuisance,
          "belief_model": ["beh_alpha"] + nuisance}
# trial pairs with nan in any of these are removed from all models
mask_keys = ["beh_context", "beh_feature", "beh_task", "beh_cue_resp",
             "beh_task_resp", "beh_cue_resp_key", "beh_task_resp_key"]


# native hamming does not support nan values;
# define custom function to deal with
def hamming_with_nan(u, v):
    if np.isnan(u) or np.isnan(v):
        return np.nan
    return np.mean(u != v)


class RunRDM:
    def __init__(self, df_ses):

        task = df_ses["attended_task"]
        # convert to 0/1
        task = np.where(task == 'face', 1, 2)
        context = df_ses["subjective_state"]
        # map believed_cue to values
        feature_mapping = {"color": 1, "motion": 2}
        believed_cue = df_ses["believed_cue"].map(feature_mapping)
        # map cue response to values
        cue_mapping = {"left": 1, "right": 2, "red": 3, "yellow": 4}
        cue_resp = df_ses["subj_cue_resp_answer"].map(cue_mapping)
        cue_resp_key = df_ses["subj_cue_resp_key"]
        # map task response to values
        task_mapping = {"male": 1, "female": 2, "city": 3, "landscape": 4}
        task_resp = df_ses["subj_task_resp_answer"].map(task_mapping)
        task_resp_key = df_ses["subj_task_resp_key"]
        # cue color and motion, probe images
        prop_red = df_ses["prop_red"]
        motion_coh = df_ses["motion_coherence"]
        face_type = pd.factorize(df_ses["face_type"])[0]
        scene_type = pd.factorize(df_ses["scene_type"])[0]
        # context belief from the behavioral model, posterior of the four contexts
        alpha = df_ses[["alpha1", "alpha2", "alpha3", "alpha4"]].to_numpy(dtype=float)

        self.models_to_test = {"context": context, "feature": believed_cue, "task": task,
                               "cue_resp": cue_resp, "task_resp": task_resp,
                               "cue_resp_key": cue_resp_key, "task_resp_key": task_resp_key,
                               "prop_red": prop_red, "motion_coh": motion_coh,
                               "face_type": face_type, "scene_type": scene_type}

        # beh rdm
        self.rdms = {}  # store all RDMs
        for model, values in self.models_to_test.items():
            values = np.asarray(values, dtype=float).reshape(-1, 1)
            if model in ["prop_red", "motion_coh"]:
                self.rdms[f"beh_{model}"] = squareform(pdist(values, metric='cityblock'))  # cityblock is Manhattan
            else:   # categorical variables
                self.rdms[f"beh_{model}"] = squareform(pdist(values, metric=hamming_with_nan))
        # graded context belief, jensen-shannon distance between belief vectors
        self.rdms["beh_alpha"] = squareform(pdist(alpha, metric='jensenshannon'))

    def preprocess_data(self, data, nb):
        # remove features that have constant values across samples and normalize across feature space
        self.data = data[:, nb]
        self.data = VarianceThreshold(threshold=0).fit_transform(self.data)
        self.data = StandardScaler().fit_transform(self.data)

    def calculate_rdm(self):
        # calculate correlation coef
        self.rdms["neural"] = 1 - np.corrcoef(self.data)
        # release memory
        del self.data

        # upper triangle, only pairs from different runs
        rows, cols = np.triu_indices(n_trials, k=1)
        valid = run_labels[rows] != run_labels[cols]
        rows, cols = rows[valid], cols[valid]
        for key, rdm in self.rdms.items():
            self.rdms[key] = rdm[rows, cols]

    def regression_model(self):
        mask = np.ones(self.rdms["neural"].shape, dtype=bool)
        for key in mask_keys:
            mask &= ~np.isnan(self.rdms[key])

        result_dic = {}
        for model, beh_rdm_labels in MODELS.items():
            X = np.column_stack([self.rdms[key][mask] for key in beh_rdm_labels])
            y = self.rdms["neural"][mask].reshape(-1, 1)
            # using statsmodel for linear regresion, same as LinearRegression from sklearn
            ols_model = sm.OLS(y, sm.add_constant(X), missing='drop').fit()
            for key, beta, tvalue in zip(beh_rdm_labels, ols_model.params[1:], ols_model.tvalues[1:]):
                result_dic[f"{model}/{key}_beta"] = float(beta)
                result_dic[f"{model}/{key}_tvalue"] = float(tvalue)
        return result_dic


def run_jobs(df_ses, neighbors, data):
    print(datetime.datetime.now())
    results = []
    # instantiate once per chunk, reuse beh data
    run_rdm_template = RunRDM(df_ses)
    for nb in neighbors:
        run_rdm = copy.deepcopy(run_rdm_template)
        run_rdm.preprocess_data(data, nb)
        run_rdm.calculate_rdm()
        results.append(run_rdm.regression_model())
    return results


def parallel_searchlight(df_ses, neighbors, data, n_jobs):
    n_centers = len(neighbors)
    n_jobs = min(n_jobs, n_centers)
    chunk_size = max(1, n_centers // n_jobs)
    chunks = [neighbors[i:i + chunk_size] for i in range(0, n_centers, chunk_size)]
    results = Parallel(n_jobs=n_jobs)(delayed(run_jobs)(df_ses, chunk, data) for chunk in chunks)
    # flatten parallel return
    return [x for xs in results for x in xs]


def roi_voxels(roi_path, final_mask):
    # flat voxel indices of one ROI, respecting the same mask as the searchlight sweep
    roi = nib.load(roi_path).get_fdata().astype(bool)
    return np.flatnonzero(roi & final_mask)


def atlas_rois(atlas_path, labels_path, final_mask):
    # one ROI per labelled region of a parcellation, e.g. AAL3
    atlas = nib.load(atlas_path).get_fdata().astype(int)
    names = {}
    if labels_path:
        lab = pd.read_csv(labels_path, sep=None, engine="python")
        id_col, name_col = lab.columns[:2]
        names = dict(zip(lab[id_col].astype(int), lab[name_col].astype(str)))
    roi_names, neighbors = [], []
    for label in sorted(np.unique(atlas)):
        if label == 0:
            continue
        nb = np.flatnonzero((atlas == label) & final_mask)
        if nb.size == 0:
            continue
        roi_names.append(names.get(label, f"roi{label}"))
        neighbors.append(nb)
    return roi_names, neighbors


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument('-sub_id')
    ap.add_argument('-ses_id')
    ap.add_argument('-event', default="cue")
    ap.add_argument('-mask', default=default_mask, help="brain mask for the searchlight sweep / ROI intersection")
    ap.add_argument('-radius', type=float, default=2.5, help="searchlight radius in voxels (2.5 vox = 5mm here)")
    ap.add_argument('-threshold', type=float, default=0.5, help="get_volume_searchlight proportion-in-mask threshold")
    ap.add_argument('-jobs', type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", 12)))
    ap.add_argument('-roi', nargs='+', default=None,
                    help="one or more ROI mask files; switches to whole-ROI mode (no sliding sphere, csv output)")
    ap.add_argument('-atlas', default=None,
                    help="parcellation file (e.g. AAL3); one ROI per labelled region, also switches to whole-ROI mode")
    ap.add_argument('-atlas_labels', default=None,
                    help="optional id,name table for -atlas; falls back to roi<label> if not given")
    args = ap.parse_args()
    sub_id, ses_id, event = args.sub_id, args.ses_id, args.event

    df_all = pd.read_csv(beh_csv, dtype={'subid': 'str', 'ses': 'str'})
    df_ses = df_all.query("subid==@sub_id & ses==@ses_id").sort_values(["block", "trial"])
    if len(df_ses) != n_trials:
        raise SystemExit(f"sub-{sub_id} ses-{ses_id}: {len(df_ses)} trials")

    # prepare input data, beta series
    beta_img = nib.load(f"{DD_dir_base}/sub-{sub_id}/ses-{ses_id}/"
                        f"Quantum4S_sub-{sub_id}_ses-{ses_id}_{event}_LSS.nii.gz")
    beta_LSS = beta_img.get_fdata().transpose((3, 0, 1, 2))
    LSS_mask = (np.max(beta_LSS, axis=0) != np.min(beta_LSS, axis=0))
    beta_LSS = beta_LSS.reshape(beta_LSS.shape[0], -1)
    mask = nib.load(args.mask).get_fdata().astype(bool)
    final_mask = mask & LSS_mask

    if args.roi or args.atlas:
        # whole-ROI mode, one RDM per ROI (file and/or atlas region), no sliding sphere
        roi_names, neighbors = [], []
        if args.roi:
            roi_names += [os.path.splitext(os.path.basename(p))[0].replace(".nii", "") for p in args.roi]
            neighbors += [roi_voxels(p, final_mask) for p in args.roi]
        if args.atlas:
            n, nb = atlas_rois(args.atlas, args.atlas_labels, final_mask)
            roi_names += n
            neighbors += nb
        print(f"running RDM {sub_id} session {ses_id}, {len(neighbors)} ROIs")
        results = parallel_searchlight(df_ses, neighbors, beta_LSS, args.jobs)

        os.makedirs(out_root, exist_ok=True)
        rows = []
        for roi_name, nb, res in zip(roi_names, neighbors, results):
            rows.append(dict(sub_id=sub_id, ses_id=ses_id, roi=roi_name, n_voxels=len(nb), **res))
        out_csv = f"{out_root}/roi_{sub_id}_{ses_id}.csv"
        pd.DataFrame(rows).to_csv(out_csv, index=False)
        print(f"saved {out_csv}")

    else:
        # searchlight mode, one nifti map per predictor
        from rsatoolbox.util.searchlight import get_volume_searchlight
        centers, neighbors = get_volume_searchlight(final_mask, radius=args.radius, threshold=args.threshold)
        print(f"running RDM {sub_id} session {ses_id}, {len(centers)} spheres, radius {args.radius} vox")
        results = parallel_searchlight(df_ses, neighbors, beta_LSS, args.jobs)

        x, y, z = final_mask.shape
        for key in results[0].keys():
            model, stem = key.split("/")
            os.makedirs(f"{out_root}/{model}", exist_ok=True)
            brain_score = np.zeros([x * y * z])
            brain_score[centers] = [i[key] for i in results]
            brain_score = brain_score.reshape([x, y, z])
            nib.save(nib.Nifti1Image(brain_score, beta_img.affine),
                     f"{out_root}/{model}/{stem}_{sub_id}_{ses_id}.nii.gz")
