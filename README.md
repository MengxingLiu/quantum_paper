# Code release

Analysis code for the manuscript. Organized by stage of the pipeline:

- `preprocessing/` — BIDS conversion, defacing, fMRIPrep-style reconstruction
  (`heudiconv_base.sh`, `reconall_base.sh`, `nordic_base.sh`, `deface_base.sh`),
  NORDIC denoising, and GLM setup (`afniproc_base.sh`, `Deconvolve_base.sh`,
  `LSS_base.sh`, `prepare_stimtime.py`, `marry_model_params.sh`, `cpe_1d.py`,
  `read_data_h5.py`).
- `behavior/` — behavioral preprocessing and analysis (`preprocess.py`,
  `analysis_switch.py`), psychometric fits (`psychometric.py`), and plotting
  (`plot_beh_observations.py`, `plot_model_behaviors.py`).
- `rsa/` — representational similarity analysis (`rsa_searchlight.py`,
  `plot_model_rdms.py`), dimensionality (`dimensionality.py`), and
  thalamocortical activity-flow mapping (`activity_flow.py` and the
  `af_*.py` analyses, launched via `submit_af.sh`).
- `utils/` — shared plotting helpers.

`config.py` resolves data/code paths per machine/user — edit `get_paths()`
for your own environment before running anything. `qsub_generic.py` is a
generic SLURM/qsub job submitter used by the shell launchers.
`environment.yml` is the conda environment used to run this code.

This code is released for transparency and reproducibility alongside the
paper; it assumes the original data paths and cluster environment and is not
packaged as a turnkey pipeline. See the manuscript's Methods for the
scientific description of each analysis.
