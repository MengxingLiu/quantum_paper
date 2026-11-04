#!/usr/bin/env python3
# example session trajectory
# python example_session.py --subject <sub> --session <ses> --block <block>

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from config import get_paths
from utils.plotting import save_figure


# config

# figure size: 80mm x 20mm
FIG_WIDTH_MM = 80
FIG_HEIGHT_MM = 20
MM_TO_INCH = 1 / 25.4

# remap states: clustered within hypercontext, gap between groups
# motion group (M1, M2) at bottom, Color group (C1, C2) at top
STATE_Y_MAP = {-2: 0, -1: 0.55, 1: 1.45, 2: 2.0}

# font settings
FONT_SIZE = 6
FONT_FAMILY = 'Arial'

# colors - dots
C_CORRECT = "#4CAF50"    # green - correct choices
C_TRUE_CTX = "#d85a30"   # coral - true context/ground truth
C_WRONG = "#000000"      # black - X for wrong selection
C_SWITCH = "#666666"     # gray - switch lines


# background colors for each state, same as panel c
STATE_BG_COLORS = {
    -2: "#1d9e75",  # M1 - dark teal
    -1: "#9fe1cb",  # M2 - light teal
    1: "#f5c4b3",   # C1 - light coral
    2: "#d85a30",   # C2 - dark coral
}
BG_ALPHA = 0.2


def setup_plotting():
    # setup matplotlib for publication-quality figures with editable text
    plt.rcParams.update({
        'font.family': FONT_FAMILY,
        'font.size': FONT_SIZE,
        'axes.labelsize': FONT_SIZE,
        'axes.titlesize': FONT_SIZE,
        'xtick.labelsize': FONT_SIZE,
        'ytick.labelsize': FONT_SIZE,
        'legend.fontsize': 5,
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
        'svg.fonttype': 'none',
        'axes.linewidth': 0.5,
        'xtick.major.width': 0.5,
        'ytick.major.width': 0.5,
    })


# plotting

def plot_single_block(df: pd.DataFrame, sub_id: str, ses_id: str,
                      block_num: int, paths: dict = None) -> plt.Figure:
    # plot state trajectory for a single block

    # filter data
    df = df.copy()
    df["subid"] = df["subid"].astype(str)
    df["ses"] = df["ses"].astype(str)

    block_df = df[(df["subid"] == sub_id) &
                  (df["ses"] == ses_id) &
                  (df["block"] == block_num)].reset_index(drop=True)

    if len(block_df) == 0:
        print(f"no data for {sub_id} {ses_id} block {block_num}")
        return None

    # create figure
    fig_w = FIG_WIDTH_MM * MM_TO_INCH
    fig_h = FIG_HEIGHT_MM * MM_TO_INCH
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=300)

    # remap y-values (clustered within hypercontext)
    block_df["state_y"] = block_df["state"].map(STATE_Y_MAP)
    block_df["subjective_state_y"] = block_df["subjective_state"].map(STATE_Y_MAP)

    # masks
    correct_mask = block_df["state_acc"] == 1
    error_mask = block_df["state_acc"] == 0

    # background shading for each state (matching panel c)
    block_df["state_change"] = block_df["state"].ne(block_df["state"].shift()).cumsum()

    for _, grp in block_df.groupby("state_change"):
        start_idx = grp.index.min()
        end_idx = grp.index.max()
        state = grp["state"].iloc[0]
        state_y = STATE_Y_MAP[state]

        bg_color = STATE_BG_COLORS.get(state, "#cccccc")
        ax.axvspan(start_idx - 0.5, end_idx + 0.5,
                   color=bg_color, alpha=BG_ALPHA, zorder=0, linewidth=0)

    # plot correct trials
    if correct_mask.sum() > 0:
        ax.scatter(block_df.index[correct_mask],
                   block_df.loc[correct_mask, "state_y"],
                   c=C_CORRECT, s=8, alpha=0.9, linewidths=0, zorder=3)

    # plot error trials
    if error_mask.sum() > 0:
        # true state (coral dot)
        ax.scatter(block_df.index[error_mask],
                   block_df.loc[error_mask, "state_y"],
                   c=C_TRUE_CTX, s=8, alpha=0.9, linewidths=0, zorder=4)

        # believed state (black X)
        ax.scatter(block_df.index[error_mask],
                   block_df.loc[error_mask, "subjective_state_y"],
                   marker="x", c=C_WRONG, s=12, linewidth=0.8, zorder=5)

    # switch lines, style encodes cue uncertainty
    if "switch" in block_df.columns:
        switch_trials = block_df[block_df["switch"] == 0].index
        for idx in switch_trials:
            ax.axvline(x=idx, color=C_SWITCH, linestyle="--",
                       alpha=0.7, lw=0.5, zorder=1)

    # axis formatting, compact, grouped y-axis
    y_ticks = [STATE_Y_MAP[-2], STATE_Y_MAP[-1],
               STATE_Y_MAP[1], STATE_Y_MAP[2]]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(["M1", "M2", "C1", "C2"])
    ax.set_ylim(-0.3, 2.3)
    ax.set_xlim(-0.5, len(block_df) - 0.5)

    # remove top/right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
    ax.tick_params(width=0.5, length=2, pad=2)

    # legend, compact, includes switch difficulty
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=C_CORRECT,
               markersize=3, label="Correct", linestyle=""),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=C_TRUE_CTX,
               markersize=3, label="Actual", linestyle=""),
        Line2D([0], [0], marker="x", color=C_WRONG, markersize=3,
               linestyle="", markeredgewidth=0.8, label="Believed"),
    ]
    legend = ax.legend(handles=legend_elements, loc="best", ncol=3,
                       frameon=True, handletextpad=0.1, columnspacing=0.4,
                       borderpad=0.3, fontsize=5,
                       facecolor="white", edgecolor="#cccccc",
                       framealpha=0.9)
    legend.get_frame().set_linewidth(0.5)

    plt.tight_layout(pad=0.2)

    # save
    if paths is not None:
        output_dir = paths["fig_dir"] / "session_trajectories"
        output_dir.mkdir(parents=True, exist_ok=True)
        save_figure(fig, output_dir / f"traj_{sub_id}_{ses_id}_block{block_num}")
        print(f"saved traj_{sub_id}_{ses_id}_block{block_num}")

    return fig


def plot_all_sessions(df: pd.DataFrame, paths: dict):
    # generate trajectory plots for all subjects, sessions, and blocks

    df = df.copy()
    df["subid"] = df["subid"].astype(str)
    df["ses"] = df["ses"].astype(str)

    combos = df.groupby(["subid", "ses", "block"]).size().reset_index()[["subid", "ses", "block"]]

    print(f"{len(combos)} plots")

    for _, row in combos.iterrows():
        sub, ses, block = row["subid"], row["ses"], row["block"]
        fig = plot_single_block(df, sub, ses, int(block), paths)
        if fig is not None:
            plt.close(fig)

    print("saved to", paths['fig_dir'] / 'session_trajectories')


# main

def main():
    parser = argparse.ArgumentParser(description="Plot session state trajectories")
    parser.add_argument("--subject", type=str, default="10519", help="Subject ID")
    parser.add_argument("--session", type=str, default="4", help="Session ID")
    parser.add_argument("--block", type=int, default=2, help="Block number")
    parser.add_argument("--all", action="store_true", help="Generate all sessions")
    args = parser.parse_args()


    setup_plotting()
    paths = get_paths()

    # load data
    print("loading data")
    df = pd.read_csv(paths["csv_dir"] / "df_beh.csv")
    df["subid"] = df["subid"].astype(str)
    print(f"{len(df)} trials, {df['subid'].nunique()} subjects")

    if args.all:
        print("plotting all sessions")
        plot_all_sessions(df, paths)
    else:
        print(f"plotting {args.subject} {args.session} block {args.block}")
        fig = plot_single_block(df, args.subject, args.session, args.block, paths)
        plt.show()



if __name__ == "__main__":
    main()