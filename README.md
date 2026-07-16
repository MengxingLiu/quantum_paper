# Thalamic contextual representation and updating

Analysis and modeling code for:

**The human thalamus selectively represents and updates contextual signals in dynamic environments**
Mengxing L., Wang M. B., Hwang K., Halassa M. M.

This repository contains the behavioral modeling, neuroimaging analysis, and
recurrent neural network code needed to reproduce the results in the paper.

## Overview

The code covers four analysis strands:

1. **Behavioral modeling** — hierarchical Bayesian observer models (FBM, HBM)
   and the constrained hierarchical model (CHM), fit with HMC/NUTS in
   JAX/NumPyro. Produces the context prediction error (CPE) used downstream.
2. **fMRI analysis** — single-trial GLM estimation, representational
   similarity analysis (RSA) searchlight and ROI analyses.
3. **Thalamocortical activity flow and dimensionality** — activity-flow
   mapping between PFC and thalamic nuclei, and participation-ratio
   estimates of effective dimensionality.
4. **Thalamocortical RNN** — an actor-critic RNN with a low-dimensional
   feedforward thalamic module and fast corticothalamic plasticity, plus
   its ablation (no fast plasticity).


## Requirements

- Python 3.11
- JAX + NumPyro (behavioral models, RNN)
- AFNI 24.0.08 (GLM / preprocessing; called from shell scripts)
- NumPy, SciPy, pandas, scikit-learn, nibabel, matplotlib

Create the environment with:

```bash
conda env create -f environment.yml
conda activate thal-context
```

AFNI must be installed separately and available on your `PATH`.

## Data

Raw 7T imaging data are available from the corresponding authors on
reasonable request, subject to the data-sharing terms of the IRB.

