# plotting helpers shared by the figure scripts

from pathlib import Path
from typing import List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
import seaborn as sns


# setup

def setup_plotting(style: str = "ticks", font: str = "Arial"):
    # configure matplotlib/seaborn for publication-quality figures
    sns.set_style(style)
    sns.set_palette("deep")
    mpl.rcParams["font.family"] = font
    plt.rcParams["svg.fonttype"] = "none"


# time series plots

def plot_timeseries_by_condition(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: str = None,
    hue_order: List[str] = None,
    palette: str = "gist_gray",
    title: str = None,
    xlabel: str = None,
    ylabel: str = None,
    ylim: Tuple[float, float] = None,
    ax: plt.Axes = None,
    **kwargs
) -> plt.Axes:
    # plot time series with optional condition grouping
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 4))
    
    sns.lineplot(
        data=df, x=x, y=y, hue=hue, hue_order=hue_order,
        palette=palette, marker="o", errorbar="ci", ax=ax, **kwargs
    )
    
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(ylim)
    
    sns.despine()
    return ax


# paired / group comparisons

def plot_paired_comparison(
    df: pd.DataFrame,
    x: str,
    y: str,
    subject_col: str = "subid",
    palette: List[str] = None,
    title: str = None,
    xlabel: str = None,
    ylabel: str = None,
    ylim: Tuple[float, float] = None,
    ax: plt.Axes = None,
) -> plt.Axes:
    # plot paired comparison with individual subject lines
    if ax is None:
        fig, ax = plt.subplots(figsize=(3, 4))
    
    if palette is None:
        palette = ["silver", "dimgray"]
    
    # box/strip plot
    sns.boxplot(data=df, x=x, y=y, palette=palette, showfliers=False, ax=ax)
    sns.stripplot(data=df, x=x, y=y, palette=palette, jitter=False, 
                  linewidth=1, ax=ax)
    
    # connect paired observations
    x_levels = df[x].unique()
    x_map = {level: i for i, level in enumerate(x_levels)}
    
    for subj in df[subject_col].unique():
        sub_data = df[df[subject_col] == subj]
        if len(sub_data) == len(x_levels):
            x_vals = [x_map[level] for level in sub_data[x]]
            ax.plot(x_vals, sub_data[y].values, "k-", alpha=0.3, linewidth=0.8)
    
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(ylim)
    
    sns.despine()
    return ax


def plot_group_comparison_with_subjects(
    df: pd.DataFrame,
    x: str,
    y: str,
    subject_col: str = "subject",
    colors: List[str] = None,
    xlabel: str = None,
    ylabel: str = None,
    ylim: Tuple[float, float] = None,
    figsize: Tuple[float, float] = (3, 4),
) -> plt.Figure:
    # plot group means with error bars and individual subject points
    fig, ax = plt.subplots(figsize=figsize)
    
    if colors is None:
        colors = ["silver", "dimgray"]
    
    unique_x = df[x].unique()
    x_map = {level: i for i, level in enumerate(unique_x)}
    
    # connecting lines for subjects
    for subj in df[subject_col].unique():
        sub_data = df[df[subject_col] == subj].sort_values(x)
        x_vals = [x_map[level] for level in sub_data[x]]
        ax.plot(x_vals, sub_data[y].values, "k-", alpha=0.3, linewidth=0.8, zorder=1)
    
    # individual points
    for i, level in enumerate(unique_x):
        level_data = df[df[x] == level][y]
        ax.scatter(
            [i] * len(level_data), level_data,
            color=colors[i % len(colors)], s=50, alpha=0.7,
            edgecolors="white", zorder=2
        )
    
    # group means with error bars
    stats = df.groupby(x)[y].agg(["mean", "sem"])
    for i, (level, row) in enumerate(stats.iterrows()):
        ax.errorbar(
            x_map[level], row["mean"], yerr=row["sem"],
            fmt="o", color="black", markersize=8,
            capsize=5, capthick=2, zorder=3
        )
    
    ax.set_xticks(range(len(unique_x)))
    ax.set_xticklabels(unique_x)
    if xlabel:
        ax.set_xlabel(xlabel, fontweight="bold")
    if ylabel:
        ax.set_ylabel(ylabel, fontweight="bold")
    if ylim:
        ax.set_ylim(ylim)
    ax.set_xlim(-0.5, len(unique_x) - 0.5)
    
    sns.despine()
    plt.tight_layout()
    return fig


# transition plots

def plot_transition_matrix(
    trans_df: pd.DataFrame,
    proportion_col: str = "proportion",
    group_col: str = "pair_group",
    subject_col: str = "sub_id",
    order: List[str] = None,
    labels: List[str] = None,
    chance_line: float = 1/3,
    ax: plt.Axes = None,
) -> plt.Axes:
    # plot transition proportions as grouped boxplot
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 4))
    
    if order is None:
        order = trans_df[group_col].unique()
    
    n_groups = len(order)
    palette = ["dimgrey"] * (n_groups // 2) + ["darkgrey"] * (n_groups - n_groups // 2)
    
    sns.boxplot(
        data=trans_df, x=group_col, y=proportion_col,
        order=order, palette=palette, showfliers=False, ax=ax
    )
    sns.stripplot(
        data=trans_df, x=group_col, y=proportion_col,
        order=order, palette=palette, jitter=False, linewidth=1, ax=ax
    )
    
    if chance_line is not None:
        ax.axhline(chance_line, ls="--", c="grey", alpha=0.5)
    
    if labels:
        ax.set_xticklabels(labels, rotation=45, ha="right")
    
    ax.set_ylabel("Proportion")
    ax.set_xlabel("Transition Type")
    
    sns.despine()
    return ax


# psychometric curves

def plot_psychometric_curve(
    x: np.ndarray,
    y: np.ndarray,
    fit_func: callable = None,
    fit_params: np.ndarray = None,
    label: str = None,
    color: str = None,
    ax: plt.Axes = None,
) -> plt.Axes:
    # plot psychometric curve with data points and optional fit
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 4))
    
    # plot data points
    sns.lineplot(
        x=x, y=y, marker="o", linestyle="",
        errorbar="ci", err_style="bars", label=label, color=color, ax=ax
    )
    
    # plot fit line
    if fit_func is not None and fit_params is not None:
        x_fit = np.linspace(x.min(), x.max(), 100)
        y_fit = fit_func(x_fit, *fit_params)
        ax.plot(x_fit, y_fit, color=color, alpha=0.7)
    
    ax.set_ylim(-0.1, 1.1)
    sns.despine()
    return ax


# saving

def save_figure(
    fig: plt.Figure,
    path: Union[str, Path],
    formats: List[str] = None,
    dpi: int = 600,
    **kwargs
):
    # save figure in specified formats
    if formats is None:
        formats = ["svg"]
    
    path = Path(path)
    
    for fmt in formats:
        fig.savefig(
            path.with_suffix(f".{fmt}"),
            dpi=dpi,
            bbox_inches="tight",
            **kwargs
        )
    
    print("saved", path.with_suffix('.' + formats[0]))