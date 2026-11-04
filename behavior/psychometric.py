#!/usr/bin/env python3
# psychometric curves for each context

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.optimize import curve_fit

from config import get_paths
from utils.plotting import save_figure


# config

# figure size: 40mm x 40mm
FIG_WIDTH_MM = 45
FIG_HEIGHT_MM = 45
MM_TO_INCH = 1 / 25.4

# font settings
FONT_SIZE = 6
TICK_SIZE = 6
FONT_FAMILY = 'Arial'

# colors - distinct for each state
COLORS = {
    1: "#f5c4b3ff",   # state 1 (color context)
    2: "#d85a30ff",   # state 2 (color context)
    -1: "#1d9e75ff",  # state -1 (motion context)
    -2: "#9fe1cbff",  # state -2 (motion context) left-face
}

LINE_STYLES = {1: "-", 2: "--", -1: "-", -2: "--"}


# psychometric functions

def logistic_4p(x, a, b, c, d):
    # 4-parameter logistic function
    return a + (b - a) / (1 + np.power(10, (c - x) * d))


def fit_psychometric(x, y, bounds=([0, 0, -1, 0], [1, 1, 1, 100]),
                     p0=[0.5, 0.5, 0.1, 20]):
    # fit psychometric curve
    try:
        mask = ~(np.isnan(x) | np.isnan(y))
        x_clean, y_clean = x[mask], y[mask]
        if len(x_clean) < 10:
            return None
        popt, _ = curve_fit(logistic_4p, x_clean, y_clean,
                            bounds=bounds, p0=p0, maxfev=50000)
        return popt
    except (RuntimeError, ValueError):
        return None


def aggregate_by_x(x, y, n_bins=None, bin_range=None, decimals=3):
    # aggregate y values by x, either by binning or by unique levels
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    if len(x) == 0:
        return None, None, None
    
    if n_bins is None or n_bins == 0:
        # no binning: average at each unique x level
        x_rounded = np.round(x, decimals)
        unique_x = np.sort(np.unique(x_rounded))
        
        means, sems = [], []
        for xval in unique_x:
            y_level = y[x_rounded == xval]
            means.append(np.mean(y_level))
            sems.append(np.std(y_level) / np.sqrt(len(y_level)) if len(y_level) > 1 else 0)
        
        return unique_x, np.array(means), np.array(sems)
    
    else:
        # binning: collapse into n_bins
        if bin_range is not None:
            bin_min, bin_max = bin_range
        else:
            bin_min, bin_max = np.nanmin(x), np.nanmax(x)
        
        bins = np.linspace(bin_min, bin_max, n_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        bin_idx = np.digitize(x, bins) - 1
        bin_idx = np.clip(bin_idx, 0, n_bins - 1)
        
        means, sems, valid_centers = [], [], []
        for i in range(n_bins):
            y_bin = y[bin_idx == i]
            if len(y_bin) >= 1:  # at least 1 trial
                means.append(np.mean(y_bin))
                sems.append(np.std(y_bin) / np.sqrt(len(y_bin)) if len(y_bin) > 1 else 0)
                valid_centers.append(bin_centers[i])
        
        return np.array(valid_centers), np.array(means), np.array(sems)


def _get_motion_coherence(df, mask):
    # extract motion coherence column
    if "coherence_signed" in df.columns:
        return df.loc[mask, "coherence_signed"].values
    elif "coherence(right)" in df.columns:
        return df.loc[mask, "coherence(right)"].values
    return None


def _plot_curve(ax, x, y, state, n_bins=None, bin_range=None):
    # plot single psychometric curve with fit and aggregated data
    if len(x) == 0:
        return
    
    color = COLORS[state]
    ls = LINE_STYLES[state]
    
    # fit and plot curve
    popt = fit_psychometric(x, y)
    if popt is not None:
        x_fit = np.linspace(np.nanmin(x), np.nanmax(x), 100)
        y_fit = logistic_4p(x_fit, *popt)
        ax.plot(x_fit, y_fit, color=color, ls=ls, lw=0.8, alpha=0.8)
    
    # data points (binned or all levels)
    x_agg, y_mean, sem = aggregate_by_x(x, y, n_bins=n_bins, bin_range=bin_range)
    if x_agg is not None and len(x_agg) > 0:
        ax.errorbar(x_agg, y_mean, yerr=sem, fmt='o', color=color,
                    ms=2, lw=0.5, capsize=0, alpha=0.9)


# compact plotting

def plot_psychometric_compact(df: pd.DataFrame, paths: dict,
                               filter_by_response: bool = True,
                               n_bins_color: int = None,
                               n_bins_motion: int = None,
                               bin_range_color: tuple = (0.32, 0.68),
                               bin_range_motion: tuple = (-0.5, 0.5)):
    # compact 2x2 psychometric plot for 40x40mm panel
    
    # set global font before creating figure
    plt.rcParams.update({
        'font.family': FONT_FAMILY,
        'font.size': FONT_SIZE,
        'axes.labelsize': FONT_SIZE,
        'axes.titlesize': FONT_SIZE,
        'xtick.labelsize': TICK_SIZE,
        'ytick.labelsize': TICK_SIZE,
        'legend.fontsize': TICK_SIZE,
        'pdf.fonttype': 42,     # embeds TrueType fonts (editable)
        'ps.fonttype': 42,
        'svg.fonttype': 'none',  # use <text> elements (editable) instead of paths
    })
    
    # setup figure with exact size
    fig_w = FIG_WIDTH_MM * MM_TO_INCH
    fig_h = FIG_HEIGHT_MM * MM_TO_INCH
    
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    
    # gridSpec with tight spacing
    gs = gridspec.GridSpec(
        2, 2,
        figure=fig,
        left=0.22,    # space for y-label
        right=0.98,
        bottom=0.18,  # space for x-label + legend
        top=0.88,     # space for column headers
        wspace=0.08,
        hspace=0.08
    )
    
    axes = np.array([[fig.add_subplot(gs[i, j]) for j in range(2)] 
                     for i in range(2)])
    
    # collect x-ranges for shared axis limits
    x_color_all = []   # column 0
    x_motion_all = []  # column 1
    
    # plot data
    
    # color context (row 0): states 1, 2
    for state in [1, 2]:
        if filter_by_response:
            mask = ((df["subj_cue_resp_answer"].isin(["red", "yellow"])) & 
                    (df["subjective_state"] == state))
        else:
            mask = df["state"] == state
        
        # column 0: choice by color coherence
        x_color = df.loc[mask, "prop_red"].values
        y = (df.loc[mask, "attended_task"] == "face").astype(float).values
        x_color_all.append(x_color)
        _plot_curve(axes[0, 0], x_color, y, state, 
                    n_bins=n_bins_color, bin_range=bin_range_color)
        
        # column 1: choice by motion coherence
        x_motion = _get_motion_coherence(df, mask)
        if x_motion is not None:
            x_motion_all.append(x_motion)
            _plot_curve(axes[0, 1], x_motion, y, state, 
                        n_bins=n_bins_motion, bin_range=bin_range_motion)
    
    # motion context (row 1): states -1, -2
    for state in [-1, -2]:
        if filter_by_response:
            mask = ((df["subj_cue_resp_answer"].isin(["left", "right"])) & 
                    (df["subjective_state"] == state))
        else:
            mask = df["state"] == state
        
        # column 0: choice by color coherence
        x_color = df.loc[mask, "prop_red"].values
        y = (df.loc[mask, "attended_task"] == "face").astype(float).values
        x_color_all.append(x_color)
        _plot_curve(axes[1, 0], x_color, y, state, 
                    n_bins=n_bins_color, bin_range=bin_range_color)
        
        # column 1: choice by motion coherence
        x_motion = _get_motion_coherence(df, mask)
        if x_motion is not None:
            x_motion_all.append(x_motion)
            _plot_curve(axes[1, 1], x_motion, y, state, 
                        n_bins=n_bins_motion, bin_range=bin_range_motion)
    
    # formatting
    
    for ax in axes.flatten():
        ax.set_ylim(-0.05, 1.05)
        ax.set_yticks([0, 0.5, 1])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(width=0.5, length=2)
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
    
    # only left column gets y-tick labels
    for ax in axes[:, 1]:
        ax.set_yticklabels([])
    
    # only bottom row gets x-tick labels
    for ax in axes[0, :]:
        ax.set_xticklabels([])
    
    # compute shared x-limits from data
    def get_padded_lim(x_list, pad_frac=0.05):
        # compute min/max across arrays with padding
        x_all = np.concatenate([x[~np.isnan(x)] for x in x_list if len(x) > 0])
        xmin, xmax = np.min(x_all), np.max(x_all)
        pad = (xmax - xmin) * pad_frac
        return xmin - pad, xmax + pad
    
    # column 0: color coherence (use bin_range for symmetric limits)
    xlim_color = (bin_range_color[0] - 0.02, bin_range_color[1] + 0.02)
    axes[0, 0].set_xlim(xlim_color)
    axes[1, 0].set_xlim(xlim_color)
    # symmetric ticks around 0.5
    mid_color = (bin_range_color[0] + bin_range_color[1]) / 2
    axes[0, 0].set_xticks([bin_range_color[0], mid_color, bin_range_color[1]])
    axes[1, 0].set_xticks([bin_range_color[0], mid_color, bin_range_color[1]])
    
    # column 1: motion coherence (use bin_range for symmetric limits)
    xlim_motion = (bin_range_motion[0] - 0.02, bin_range_motion[1] + 0.02)
    axes[0, 1].set_xlim(xlim_motion)
    axes[1, 1].set_xlim(xlim_motion)
    # symmetric ticks around 0
    mid_motion = (bin_range_motion[0] + bin_range_motion[1]) / 2
    axes[0, 1].set_xticks([bin_range_motion[0], mid_motion, bin_range_motion[1]])
    axes[1, 1].set_xticks([bin_range_motion[0], mid_motion, bin_range_motion[1]])
    
    # shared labels (outside subplots)
    fig.text(0.02, 0.53, "P(Face)", va='center', ha='left',
             rotation=90, fontsize=FONT_SIZE, fontfamily=FONT_FAMILY)
    fig.text(0.35, 0.02, "Color coh.", ha='center', 
             fontsize=FONT_SIZE, fontfamily=FONT_FAMILY)
    fig.text(0.75, 0.02, "Motion coh.", ha='center', 
             fontsize=FONT_SIZE, fontfamily=FONT_FAMILY)
    
    # row labels (right side or left margin)
    fig.text(0.12, 0.68, "Color\nctx", va='center', ha='center',
             fontsize=FONT_SIZE, fontfamily=FONT_FAMILY, linespacing=0.85)
    fig.text(0.12, 0.35, "Motion\nctx", va='center', ha='center',
             fontsize=FONT_SIZE, fontfamily=FONT_FAMILY, linespacing=0.85)
    
    # legend (bottom, horizontal)
    legend_elements = [
        plt.Line2D([0], [0], color=COLORS[1], ls=LINE_STYLES[1], 
                   lw=0.8, marker='o', ms=2, label='S1'),
        plt.Line2D([0], [0], color=COLORS[2], ls=LINE_STYLES[2],
                   lw=0.8, marker='o', ms=2, label='S2'),
        plt.Line2D([0], [0], color=COLORS[-1], ls=LINE_STYLES[-1],
                   lw=0.8, marker='o', ms=2, label='S-1'),
        plt.Line2D([0], [0], color=COLORS[-2], ls=LINE_STYLES[-2],
                   lw=0.8, marker='o', ms=2, label='S-2'),
    ]
    # fig.legend(handles=legend_elements, loc='upper center',
    # bbox_to_anchor=(0.6, 0.99), ncol=4, frameon=False,
    # handlelength=1.5, columnspacing=0.8, handletextpad=0.3)
    
    # save
    suffix = "_by_response" if filter_by_response else "_by_state"
    save_figure(fig, paths["fig_dir"] / f"psychometric_compact{suffix}")
    plt.close(fig)
    
    print(f"saved psychometric_compact{suffix}")


# main

def main():
    
    paths = get_paths()
    
    # load data
    print("loading data")
    df = pd.read_csv(paths["csv_dir"] / "df_beh.csv")
    print(f"{len(df)} trials, {df['subid'].nunique()} subjects")
    
    # number of coherence bins, None to plot every level
    N_BINS_COLOR = 8    # adjust as needed (None for all levels)
    N_BINS_MOTION = 8   # adjust as needed (None for all levels)
    BIN_RANGE_COLOR = (0.32, 0.68)   # actual data range
    BIN_RANGE_MOTION = (-0.5, 0.5)   # actual data range
    
    # compact plots
    print("psychometric, by response")
    print("bins:", N_BINS_COLOR, N_BINS_MOTION)
    plot_psychometric_compact(df, paths, filter_by_response=True,
                               n_bins_color=N_BINS_COLOR,
                               n_bins_motion=N_BINS_MOTION,
                               bin_range_color=BIN_RANGE_COLOR,
                               bin_range_motion=BIN_RANGE_MOTION)
    
    print("psychometric, by state")
    plot_psychometric_compact(df, paths, filter_by_response=False,
                               n_bins_color=N_BINS_COLOR,
                               n_bins_motion=N_BINS_MOTION,
                               bin_range_color=BIN_RANGE_COLOR,
                               bin_range_motion=BIN_RANGE_MOTION)
    


if __name__ == "__main__":
    main()