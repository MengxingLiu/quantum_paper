#!/usr/bin/env python3
# draw the context and hypercontext model RDMs of one example session
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import pdist, squareform

#### style ####
mpl.rcParams.update({
    'font.family'       : 'Arial',
    'font.size'         : 6,
    'axes.labelsize'    : 6,
    'axes.titlesize'    : 6,
    'xtick.labelsize'   : 6,
    'ytick.labelsize'   : 6,
    'axes.linewidth'    : 0.5,
    'xtick.major.width' : 0.5,
    'ytick.major.width' : 0.5,
    'xtick.major.size'  : 2,
    'ytick.major.size'  : 2,
    'xtick.direction'   : 'out',
    'ytick.direction'   : 'out',
    'pdf.fonttype'      : 42,
    'ps.fonttype'       : 42,
    'svg.fonttype'      : 'none',
})

MM = 1 / 25.4
FIG_W_MM = 55
FIG_H_MM = 32
CMAP = 'Oranges'

base_dir   = "/path/to/QUANTUM_4S"
figure_dir = f"{base_dir}/figures"

sub_id = "10305"
ses_id = "2"

df_all = pd.read_csv(f"{base_dir}/GLM_1Ds/df_beh.csv",
                     dtype={'subid': 'str', 'ses': 'str'})
df = df_all.query("subid == @sub_id & ses == @ses_id")

context = df["subjective_state"].to_numpy().reshape(-1, 1)
feature = df["believed_cue"].map({"color": 1, "motion": 2}).to_numpy().reshape(-1, 1)

def hamming_with_nan(u, v):
    if np.isnan(u) or np.isnan(v):
        return np.nan
    return np.mean(u != v)

rdm_context = squareform(pdist(context, metric=hamming_with_nan))
rdm_feature = squareform(pdist(feature, metric=hamming_with_nan))

# remove within-run pairs
run_labels = np.repeat(np.arange(5), 40)
within_run = np.equal.outer(run_labels, run_labels)
rdm_context = np.where(within_run, np.nan, rdm_context)
rdm_feature = np.where(within_run, np.nan, rdm_feature)

fig = plt.figure(figsize=(FIG_W_MM * MM, FIG_H_MM * MM), dpi=300)
gs  = fig.add_gridspec(1, 2, wspace=0.15,
                       left=0.11, right=0.98,
                       bottom=0.30, top=0.85)
ax_c = fig.add_subplot(gs[0, 0])
ax_f = fig.add_subplot(gs[0, 1])

# ticks at run boundaries
tick_positions = np.array([0, 40, 80, 120, 160, 200])
tick_labels    = np.array([0, 40, 80, 120, 160, 200])

for ax, rdm, title in zip([ax_c, ax_f],
                          [rdm_context, rdm_feature],
                          ["context", "hypercontext"]):
    mask = np.triu(np.ones_like(rdm, dtype=bool))            # lower triangle only
    sns.heatmap(rdm, cmap=CMAP, mask=mask, square=True,
                vmin=0, vmax=1, cbar=False,
                rasterized=True, ax=ax)
    ax.set_xticks(tick_positions, tick_labels, rotation=0)
    ax.set_yticks(tick_positions, tick_labels, rotation=0)
    ax.set_xlabel('Trial')
    ax.set_title(f'{title} RDM', pad=2)
ax_c.set_ylabel('Trial')
ax_f.set_ylabel('')
# binary RDM, dark = different, light = same

out = f"{figure_dir}/RDM_context_hypercontext.svg"
fig.savefig(out, dpi=600, bbox_inches='tight', pad_inches=0.02)
print("saved", out)
