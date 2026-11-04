#!/usr/bin/env python3
# behavior panels, reads plot_human.h5

import h5py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker

from config import get_paths
from utils.plotting import save_figure


# config

FIG_WIDTH_MM  = 178
FIG_HEIGHT_MM =  78
MM_TO_INCH    = 1 / 25.4

FONT_SIZE   = 6
FONT_FAMILY = 'Arial'

# general palette, gray scale (clean, minimal, Science/Nature standard)
COLOR_A = "#888888"   # medium gray   (primary, easy)
COLOR_B = "#333333"   # dark charcoal (secondary, hard)

# context colors, used only in panel m
CTX_C   = "#d85a30"   # coral  (color context)
CTX_M   = "#1d9e75"   # teal   (motion context)

LGRAY   = "#bbbbbb"   # light gray (connecting lines)
MGRAY   = "#999999"   # mid gray   (reference lines)


# style

plt.rcParams.update({
    'font.family'       : FONT_FAMILY,
    'font.size'         : FONT_SIZE,
    'axes.labelsize'    : FONT_SIZE,
    'axes.titlesize'    : FONT_SIZE,
    'xtick.labelsize'   : FONT_SIZE,
    'ytick.labelsize'   : FONT_SIZE,
    'legend.fontsize'   : FONT_SIZE,
    'axes.linewidth'    : 0.5,
    'xtick.major.width' : 0.5,
    'ytick.major.width' : 0.5,
    'xtick.major.size'  : 2,
    'ytick.major.size'  : 2,
    'lines.linewidth'   : 0.8,
    'pdf.fonttype'      : 42,
    'ps.fonttype'       : 42,
    'svg.fonttype'      : 'none',
})


# load data

paths   = get_paths()
h5_path = paths["base_dir"] / "BEH" / "plot_human.h5"

D = {}
with h5py.File(h5_path, 'r') as f:
    for grp in f.keys():
        D[grp] = {}
        for k in f[grp].keys():
            D[grp][k] = f[grp][k][...]


# figure layout  (4 top + 5 bottom)

fig = plt.figure(figsize=(FIG_WIDTH_MM * MM_TO_INCH,
                           FIG_HEIGHT_MM * MM_TO_INCH), dpi=300)

# top row: g h i j
gs_top = gridspec.GridSpec(
    1, 4, figure=fig,
    top=0.96, bottom=0.57,
    left=0.07, right=0.97,
    wspace=0.48,
    width_ratios=[1.4, 1.4, 1.4, 1.1],
)

# bottom row: k l m n o
gs_bot = gridspec.GridSpec(
    1, 5, figure=fig,
    top=0.43, bottom=0.07,
    left=0.07, right=0.97,
    wspace=0.52,
    width_ratios=[0.75, 1.6, 2.2, 0.75, 0.75],
)

ax_g = fig.add_subplot(gs_top[0])
ax_h = fig.add_subplot(gs_top[1])
ax_i = fig.add_subplot(gs_top[2])
ax_j = fig.add_subplot(gs_top[3])

ax_k = fig.add_subplot(gs_bot[0])
ax_l = fig.add_subplot(gs_bot[1])
ax_m = fig.add_subplot(gs_bot[2])
ax_n = fig.add_subplot(gs_bot[3])
ax_o = fig.add_subplot(gs_bot[4])


# helpers

def _style_ax(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for sp in ax.spines.values():
        sp.set_linewidth(0.5)
    ax.tick_params(width=0.5, length=2, pad=1.5)


def _add_panel_labels(fig, pairs):
    # place each panel letter left-aligned with its y-axis label
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for ax, letter in pairs:
        bbox = ax.yaxis.get_label().get_window_extent(renderer=renderer)
        x_ax = ax.transAxes.inverted().transform((bbox.x0, 0))[0]
        ax.text(x_ax, 1.08, letter, transform=ax.transAxes,
                fontsize=8, fontweight='bold', va='top', ha='left')


def violin_with_dots(ax, data, x=0, color=COLOR_A, width=0.55, dot_size=6):
    # violin body + jittered dots + mean open circle
    vp = ax.violinplot([data], positions=[x], widths=width,
                       showmedians=False, showextrema=False)
    for pc in vp['bodies']:
        pc.set_facecolor(color)
        pc.set_alpha(0.30)
        pc.set_edgecolor('none')
    jitter = np.random.RandomState(42).uniform(-0.07, 0.07, len(data))
    ax.scatter(x + jitter, data, s=dot_size, color=color,
               alpha=0.65, zorder=3, linewidths=0)
    ax.scatter([x], [np.mean(data)], s=16, facecolor='white',
               edgecolor=color, linewidths=0.8, zorder=4)


# g - accuracy by trial after switch

ta = D['total_accuracy']
x, y, ci = ta['x'], ta['y'], ta['ci']

ax_g.fill_between(x, y - ci, y + ci, color=COLOR_A, alpha=0.18)
ax_g.plot(x, y, 'o-', color=COLOR_A, lw=0.8, ms=2, zorder=3)
ax_g.set_xlabel('trial after switch')
ax_g.set_ylabel('accuracy')
ax_g.set_xlim(-3.5, 6.5)
ax_g.set_ylim(-0.05, 1.05)
ax_g.set_xticks([-2, 0, 2, 4, 6])
_style_ax(ax_g)


# h - ACR vs SS accuracy scatter + regression

sc  = D['ss_vs_cr_accuracy']
ss  = sc['steady_state_accuracy']
cr  = sc['confirmatory_reward_accuracy']
rx  = sc['regression_x']
ry  = sc['regression_y']
hi  = sc['hi_ci']
lo  = sc['lo_ci']

ax_h.fill_between(rx, lo, hi, color=COLOR_A, alpha=0.15)
ax_h.plot(rx, ry, '-', color=COLOR_A, lw=0.8, zorder=4)
ax_h.scatter(ss, cr, s=7, color=COLOR_A, zorder=5, alpha=0.80)
ax_h.set_xlabel('accuracy (SS)')
ax_h.set_ylabel('accuracy (ACR)')
lims = [0.79, 0.95]
ax_h.set_xlim(lims)
ax_h.set_ylim(0.79, 0.95)
ax_h.xaxis.set_major_locator(ticker.MultipleLocator(0.05))
ax_h.yaxis.set_major_locator(ticker.MultipleLocator(0.05))
ax_h.plot(lims, lims, '--', color=MGRAY, lw=0.7, zorder=1)
ax_h.set_aspect('equal')
_style_ax(ax_h)


# i - accuracy by difficulty  (easy = COLOR_A, hard = COLOR_B)

ad  = D['accuracy_by_difficulty']
x10 = np.array([-3, -2, -1, 0, 1, 2, 3, 4, 5, 6])

for mean_k, ci_k, col, lbl in [
        ('easy_mean', 'easy_ci', COLOR_A, 'easy'),
        ('hard_mean', 'hard_ci', COLOR_B, 'hard')]:
    m, c = ad[mean_k], ad[ci_k]
    ax_i.fill_between(x10, m - c, m + c, color=col, alpha=0.15)
    ax_i.plot(x10, m, 'o-', color=col, lw=0.8, ms=2, label=lbl)

ax_i.set_xlabel('trial after switch')
ax_i.set_ylabel('accuracy')
ax_i.set_xlim(-3.5, 6.5)
ax_i.set_ylim(-0.05, 1.05)
ax_i.set_xticks([-2, 0, 2, 4, 6])
ax_i.legend(frameon=False, handletextpad=0.3, handlelength=1.0, borderpad=0)
_style_ax(ax_i)


# j - trials to switch: easy vs hard, paired  (COLOR_A/B)

std  = D['switch_time_by_difficulty']
easy = std['easy_mean']
hard = std['hard_mean']

rng  = np.random.RandomState(7)
jx0  = rng.uniform(-0.08, 0.08, len(easy))
jx1  = rng.uniform(-0.08, 0.08, len(hard))

for i in range(len(easy)):
    ax_j.plot([jx0[i], 1 + jx1[i]], [easy[i], hard[i]],
              '-', color=LGRAY, lw=0.5, alpha=0.75, zorder=2)

ax_j.scatter(0 + jx0, easy, s=9, color=COLOR_A, zorder=3, linewidths=0)
ax_j.scatter(1 + jx1, hard, s=9, color=COLOR_B, zorder=3, linewidths=0)
ax_j.scatter([0], [np.mean(easy)], s=24, facecolor='white',
             edgecolor=COLOR_A, lw=0.9, zorder=5)
ax_j.scatter([1], [np.mean(hard)], s=24, facecolor='white',
             edgecolor=COLOR_B, lw=0.9, zorder=5)
ax_j.set_xlim(-0.5, 1.5)
ax_j.set_xticks([0, 1])
ax_j.set_xticklabels(['easy', 'hard'])
ax_j.set_ylabel('trials to switch')
_style_ax(ax_j)


# k - delta switch time violin

delta = D['switch_time_violin']['delta']

violin_with_dots(ax_k, delta, x=0, color=COLOR_A, width=0.5)
ax_k.axhline(0, color=MGRAY, lw=0.5, ls='--', zorder=1)
ax_k.set_xlim(-0.6, 0.6)
ax_k.set_xticks([0])
ax_k.set_xticklabels(['hard − easy'])
ax_k.set_ylabel('Δ trials to switch')
ax_k.set_ylim(0, 1)
ax_k.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
_style_ax(ax_k)


# l - trials to switch by subject, sorted by mean

ed    = D['explore_dist']
n     = len(ed['mean'])
order = np.argsort(ed['mean'])
m_s   = ed['mean'][order]
lo_s  = ed['low_ci'][order]
hi_s  = ed['high_ci'][order]
opt_s = ed['expected_optimal_time'][order]
xs    = np.arange(1, n + 1)

ax_l.errorbar(xs, m_s, yerr=[m_s - lo_s, hi_s - m_s],
              fmt='o', color=COLOR_A, ms=2, lw=0.7,
              capsize=0, zorder=3, label='subject')
ax_l.scatter(xs, opt_s, s=5, color=COLOR_A, alpha=0.30,
             zorder=2, label='lower bound')
ax_l.set_xlabel('subject')
ax_l.set_ylabel('exploration trials')
ax_l.set_xlim(0.3, n + 0.7)
ax_l.set_xticks([])
ax_l.legend(frameon=False, handletextpad=0.3, loc='upper left',
            borderpad=0, handlelength=1.0)
_style_ax(ax_l)


# m - switch behavior boxplot  (coral = from color ctx, teal = from motion ctx)

sb = D['switch_behavior']

groups = [
    ('C',  sb['Color_alt'],  CTX_C),
    ('M1', sb['To_motion1'], CTX_M),
    ('M2', sb['To_motion2'], CTX_M),
    ('M',  sb['Motion_alt'], CTX_M),
    ('C1', sb['To_color1'],  CTX_C),
    ('C2', sb['To_color2'],  CTX_C),
]
positions = [0, 1, 2, 4, 5, 6]

for pos, (lbl, vals, col) in zip(positions, groups):
    ax_m.boxplot(vals, positions=[pos], widths=0.58,
                 patch_artist=True, showfliers=False,
                 medianprops=dict(color=col, lw=0.8),
                 boxprops=dict(facecolor='white', edgecolor='k', lw=0.5),
                 whiskerprops=dict(color='k', lw=0.5),
                 capprops=dict(color='k', lw=0.5))
    jitter = np.random.RandomState(pos).uniform(-0.16, 0.16, len(vals))
    ax_m.scatter(pos + jitter, vals, s=4, color=col, alpha=0.50, zorder=3)

ax_m.set_xlim(-0.7, 6.7)
ax_m.set_ylim(-0.05, 1.1)
ax_m.set_xticks(positions)
ax_m.set_xticklabels(['C', 'M1', 'M2', 'M', 'C1', 'C2'])
ax_m.set_ylabel('probability')
ax_m.text(1.0, -0.12, 'from C', ha='center', va='top',
          transform=ax_m.get_xaxis_transform())
ax_m.text(5.0, -0.12, 'from M', ha='center', va='top',
          transform=ax_m.get_xaxis_transform())
_style_ax(ax_m)


# n - within-hypercontext switch probability

stay = D['stay_hyperctx_violin']['subj_mean']

violin_with_dots(ax_n, stay, x=0, color=COLOR_A, width=0.5)
ax_n.axhline(1/3, color=MGRAY, lw=0.5, ls='--', zorder=1)
ax_n.set_xlim(-0.6, 0.6)
ax_n.set_xticks([0])
ax_n.set_xticklabels(['within\nhyperctx'])
ax_n.set_ylabel('switch prob.')
ax_n.set_ylim(0, 1)
ax_n.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
_style_ax(ax_n)


# o - switch-to-color-context probability

color_ctx = D['color_hyperctx_violin']['subj_mean']

violin_with_dots(ax_o, color_ctx, x=0, color=CTX_C, width=0.5)
ax_o.axhline(1/3, color=MGRAY, lw=0.5, ls='--', zorder=1)
ax_o.set_xlim(-0.6, 0.6)
ax_o.set_xticks([0])
ax_o.set_xticklabels(['to color\nctx'])
ax_o.set_ylabel('switch prob.')
ax_o.set_ylim(0, 1)
ax_o.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
_style_ax(ax_o)


# save

_add_panel_labels(fig, [
    (ax_g, 'g'), (ax_h, 'h'), (ax_i, 'i'), (ax_j, 'j'),
    (ax_k, 'k'), (ax_l, 'l'), (ax_m, 'm'), (ax_n, 'n'), (ax_o, 'o'),
])

out = paths["fig_dir"] / "plot_beh_observations"
print(f"Saving to: {out}")
save_figure(fig, out, formats=["pdf", "svg", "png"])
plt.show()
