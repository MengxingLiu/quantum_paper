#!/usr/bin/env python3
# model behavior panels, reads plot_model.h5
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker
import h5py

import config
from utils.plotting import save_figure

# style
matplotlib.rcParams.update({
    'font.family':      'Arial',
    'font.size':         6,
    'axes.linewidth':    0.5,
    'xtick.major.width': 0.5,
    'ytick.major.width': 0.5,
    'xtick.major.size':  2,
    'ytick.major.size':  2,
    'xtick.direction':   'out',
    'ytick.direction':   'out',
    'pdf.fonttype':      42,
    'svg.fonttype':      'none',
})

FIG_WIDTH_MM  = 173
FIG_HEIGHT_MM = 107
MM_TO_INCH    = 1 / 25.4
FONT_SIZE   = 6
COLOR_A = "#888888"   # medium gray   (easy / primary)
COLOR_B = "#333333"   # dark charcoal (hard  / secondary)
CTX_C   = "#d85a30"   # coral  (color context)
CTX_M   = "#1d9e75"   # teal   (motion context)
LGRAY   = "#bbbbbb"
MGRAY   = "#999999"

# load data
paths   = config.get_paths()
h5_path = paths["base_dir"] / "BEH" / "plot_model.h5"

with h5py.File(h5_path, 'r') as f:
    def _grp(key):
        return {k: f[key][k][()] for k in f[key].keys()}

    D = {
        'loo_violin':       _grp('loo_violin'),
        'stacking_weight':  _grp('stacking_weight'),
        'subj_switch_time': _grp('hierarchical_smoothed_hyper/subj_switch_time'),
        'accuracy':         _grp('hierarchical_smoothed_hyper/accuracy_by_difficuly'),
        'switch_summary':   _grp('hierarchical_smoothed_hyper/switch_summary'),
        'reversal_hyper':   _grp('hierarchical_smoothed_hyper/reversal_hypercontext'),
        'cpe':              _grp('hierarchical_smoothed_hyper/cpe_by_difficuly'),
    }

# helpers
def _style_ax(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for sp in ax.spines.values():
        sp.set_linewidth(0.5)
    ax.tick_params(width=0.5, length=2, labelsize=FONT_SIZE)


def violin_with_dots(ax, data, x=0, color=COLOR_A, width=0.55, dot_size=6):
    # kernel-density violin + individual dots + mean open circle
    from scipy.stats import gaussian_kde
    kde = gaussian_kde(data, bw_method=0.4)
    y_grid = np.linspace(data.min(), data.max(), 200)
    density = kde(y_grid)
    density = density / density.max() * width / 2
    ax.fill_betweenx(y_grid, x - density, x + density,
                     color=color, alpha=0.35, lw=0)
    rng = np.random.RandomState(42)
    jitter = rng.uniform(-0.06, 0.06, len(data))
    ax.scatter(x + jitter, data, s=dot_size, color=color, zorder=3, linewidths=0)
    ax.scatter([x], [np.mean(data)], s=18, facecolor='white',
               edgecolor=color, lw=0.8, zorder=5)


def subj_scatter(ax, mean, mean_h, ci, color=COLOR_A):
    # per-subject
    x = np.arange(len(mean))
    ax.errorbar(x, mean, yerr=ci, fmt='none', ecolor=LGRAY,
                elinewidth=0.5, capsize=0, zorder=1)
    ax.scatter(x, mean,   s=7, facecolor='white', edgecolor=color,
               lw=0.7, zorder=3, label='human')
    ax.scatter(x, mean_h, s=7, color=color, zorder=4, label='model')


def _add_panel_labels(fig, pairs):
    # place bold panel letter left-aligned with its y-axis label
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for ax, letter in pairs:
        bbox = ax.yaxis.get_label().get_window_extent(renderer=renderer)
        x_ax = ax.transAxes.inverted().transform((bbox.x0, 0))[0]
        ax.text(x_ax, 1.08, letter, transform=ax.transAxes,
                fontsize=8, fontweight='bold', va='top', ha='left')


# figure layout
fig = plt.figure(figsize=(FIG_WIDTH_MM * MM_TO_INCH, FIG_HEIGHT_MM * MM_TO_INCH))

# layout: top=4mm | row1(schema)=32mm | gap=4mm | row2=30mm | gap=4mm | row3=30mm | bot=3mm = 107mm
# all rows share the same left=0.07 / right=0.97, equal width

# row 1: schema placeholder (full width)
gs_schema = gridspec.GridSpec(
    1, 1, figure=fig,
    top=0.963, bottom=0.664,
    left=0.07, right=0.97,
)

# row 2: b (LOO violin), c (stacking wt), d (switch time), e (accuracy)
# bottom=0.393 -> row2=25mm, 9mm gap to row3, fits e's stacked x-axis label
gs_row2 = gridspec.GridSpec(
    1, 4, figure=fig,
    top=0.626, bottom=0.393,
    left=0.07, right=0.97,
    wspace=0.50,
    width_ratios=[1.0, 1.0, 1.6, 2.0],
)

# row 3: f (switch summary), g (reversal), h (CPE)
gs_row3 = gridspec.GridSpec(
    1, 3, figure=fig,
    top=0.308, bottom=0.028,
    left=0.07, right=0.97,
    wspace=0.45,
    width_ratios=[2.0, 1.6, 2.0],
)

ax_a = fig.add_subplot(gs_schema[0])

ax_b = fig.add_subplot(gs_row2[0])
ax_c = fig.add_subplot(gs_row2[1])
ax_d = fig.add_subplot(gs_row2[2])
gs_e = gridspec.GridSpecFromSubplotSpec(
    2, 1, subplot_spec=gs_row2[3], hspace=0.08)
ax_e_easy = fig.add_subplot(gs_e[0])
ax_e_hard = fig.add_subplot(gs_e[1], sharex=ax_e_easy)

ax_f = fig.add_subplot(gs_row3[0])
ax_g = fig.add_subplot(gs_row3[1])
ax_h = fig.add_subplot(gs_row3[2])


# a - model schema placeholder
ax_a.set_xlim(0, 1)
ax_a.set_ylim(0, 1)
ax_a.text(0.5, 0.5, '← schema from plot_model_schema.py →',
          ha='center', va='center', fontsize=FONT_SIZE, color=MGRAY, style='italic')
ax_a.set_xticks([])
ax_a.set_yticks([])
ax_a.spines['top'].set_visible(False)
ax_a.spines['right'].set_visible(False)
for sp in ax_a.spines.values():
    sp.set_linestyle('--')
    sp.set_linewidth(0.4)
    sp.set_color(MGRAY)


# b - LOO violin (delta elpd/LOO for 3 comparison models vs best)
lv        = D['loo_violin']
lv_labels = ['HSN', 'HNN', 'FNN']   # models compared against best (HSH)
lv_colors = [LGRAY, COLOR_A, COLOR_B]

for i, (label, col) in enumerate(zip(lv_labels, lv_colors)):
    violin_with_dots(ax_b, lv['y'][i], x=i, color=col, width=0.6, dot_size=3)

ax_b.axhline(0, color=MGRAY, lw=0.5, ls='--', zorder=0)
ax_b.set_xticks(range(len(lv_labels)))
ax_b.set_xticklabels(lv_labels)
ax_b.set_ylabel('Δ ELPD/LOO')
_style_ax(ax_b)


# c - stacking weight
sw     = D['stacking_weight']
sw_lbl = [l.decode() if isinstance(l, bytes) else l for l in sw['label']]

ax_c.errorbar(sw['x'], sw['mean'], yerr=sw['yerr'],
              fmt='o', color=COLOR_A, ms=3, lw=0.7,
              elinewidth=0.5, capsize=1.5, zorder=3)
ax_c.set_xticks(sw['x'])
ax_c.set_xticklabels(sw_lbl, rotation=0, ha='center')
ax_c.set_ylabel('stacking weight')
ax_c.set_ylim(-0.05, 1.05)
ax_c.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
_style_ax(ax_c)


# d - per-subject switch time (human open, model filled)
st = D['subj_switch_time']
subj_scatter(ax_d, st['mean'], st['mean_h'], st['ci'], color=COLOR_A)
ax_d.set_xlabel('subject')
ax_d.set_ylabel('trials to switch')
ax_d.set_xticks([])
legend_d = ax_d.legend(frameon=False, handletextpad=0.3,
                        handlelength=1.0, borderpad=0, markerscale=1.2)
_style_ax(ax_d)


# e - accuracy by difficulty: split into easy (top) and hard (bottom)
ac = D['accuracy']
t  = ac['t']

for ax_e, mean_k, ci_k, mh_k, col, lbl in [
        (ax_e_easy, 'easy_mean', 'easy_ci', 'easy_mean_h', COLOR_A, 'easy'),
        (ax_e_hard, 'hard_mean', 'hard_ci', 'hard_mean_h', COLOR_B, 'hard')]:
    m, c, mh = ac[mean_k], ac[ci_k], ac[mh_k]
    ax_e.fill_between(t, m - c, m + c, color=col, alpha=0.15)
    ax_e.plot(t, m,  'o-', color=col, lw=0.8, ms=2, label='human')
    ax_e.plot(t, mh, '--', color=col, lw=0.8,        label='model')
    ax_e.set_title(lbl, fontsize=FONT_SIZE, pad=2)
    ax_e.set_xlim(-3.5, 6.5)
    ax_e.set_ylim(-0.05, 1.05)
    ax_e.set_yticks([0, 0.5, 1.0])
    ax_e.legend(frameon=False, handletextpad=0.3, handlelength=1.0,
                borderpad=0, loc='lower right')
    _style_ax(ax_e)

# hide x tick labels on the top subplot
ax_e_easy.tick_params(axis='x', labelbottom=False)
ax_e_hard.set_xlabel('trial after switch')
ax_e_easy.set_xticks([-2, 0, 2, 4, 6])
ax_e_hard.set_xticks([-2, 0, 2, 4, 6])
ax_e_easy.set_ylabel('accuracy')
ax_e_hard.set_ylabel('accuracy')


# f - switch summary: C_rev/C1/C2 -> coral, M_rev/M1/M2 -> teal
ss = D['switch_summary']
# gap of 0.6 between the two groups of 3
groups_f = [
    ('C',  ss['C_rev'], CTX_C,  0.0),
    ('M1', ss['M1'],    CTX_M,  1.0),
    ('M2', ss['M2'],    CTX_M,  2.0),
    ('M',  ss['M_rev'], CTX_M,  3.6),
    ('C1', ss['C1'],    CTX_C,  4.6),
    ('C2', ss['C2'],    CTX_C,  5.6),
]

rng_f = np.random.RandomState(7)
for lbl, data, col, xpos in groups_f:
    bp = ax_f.boxplot(data, positions=[xpos], widths=0.55,
                      patch_artist=True, showfliers=False,
                      medianprops=dict(color='white', lw=1.0),
                      boxprops=dict(facecolor=col, alpha=0.40, lw=0.5, edgecolor=col),
                      whiskerprops=dict(lw=0.5, color=col),
                      capprops=dict(lw=0.5, color=col))
    jitter = rng_f.uniform(-0.10, 0.10, len(data))
    ax_f.scatter(xpos + jitter, data, s=4, color=col, zorder=3, linewidths=0)

xtick_pos    = [g[3] for g in groups_f]
xtick_labels = [g[0] for g in groups_f]
ax_f.set_xticks(xtick_pos)
ax_f.set_xticklabels(xtick_labels)
ax_f.set_xlim(-0.6, 6.2)
ax_f.set_ylabel('switch prob.')
ax_f.set_ylim(0, 1)
ax_f.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax_f.text(1.0,  -0.12, 'from C', ha='center', va='top',
          transform=ax_f.get_xaxis_transform(), fontsize=FONT_SIZE)
ax_f.text(4.6,  -0.12, 'from M', ha='center', va='top',
          transform=ax_f.get_xaxis_transform(), fontsize=FONT_SIZE)
_style_ax(ax_f)


# g - reversal hypercontext per subject
rh = D['reversal_hyper']
subj_scatter(ax_g, rh['mean'], rh['mean_h'], rh['ci'], color=COLOR_A)
ax_g.axhline(1/3, color=MGRAY, lw=0.5, ls='--', zorder=0)
ax_g.set_xlabel('subject')
ax_g.set_ylabel('switch prob.')
ax_g.set_xticks([])
ax_g.set_ylim(0.2, 1.0)
ax_g.set_yticks([0.25, 0.5, 0.75, 1.0])
ax_g.legend(frameon=False, handletextpad=0.3,
            handlelength=1.0, borderpad=0, markerscale=1.2)
_style_ax(ax_g)


# h - CPE by difficulty: human (solid) vs model (dashed)
cp = D['cpe']

for mean_k, ci_k, col, lbl in [
        ('easy_mean', 'easy_ci', COLOR_A, 'easy'),
        ('hard_mean', 'hard_ci', COLOR_B, 'hard')]:
    m, c = cp[mean_k], cp[ci_k]
    ax_h.fill_between(t, m - c, m + c, color=col, alpha=0.15)
    ax_h.plot(t, m, 'o-', color=col, lw=0.8, ms=2, label=lbl)

ax_h.set_xlabel('trial after switch')
ax_h.set_ylabel('CPE')
ax_h.set_xlim(-3.5, 6.5)
ax_h.set_xticks([-2, 0, 2, 4, 6])
ax_h.legend(frameon=False, handletextpad=0.3, handlelength=1.0, borderpad=0)
_style_ax(ax_h)


# panel labels + save
# panel a is the schema figure, label b-h here
_add_panel_labels(fig, [
    (ax_b, 'b'),
    (ax_c, 'c'), (ax_d, 'd'), (ax_e_easy, 'e'),
    (ax_f, 'f'), (ax_g, 'g'), (ax_h, 'h'),
])

out = paths["fig_dir"] / "plot_model_behaviors"
print(f"Saving to: {out}")
save_figure(fig, out, formats=["pdf", "svg", "png"])
plt.show()
