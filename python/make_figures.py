"""Result and theory figures for the README and the docs.

    python run_benchmark.py      # first: computes every scenario on every noise and caches the outputs
    python make_figures.py       # then: writes figures/results/*.png
    python make_figures.py A F   # only the figures of scenarios A and F (keys: gallery spectra matrix cascade A B C D E F blur)

All numbers printed on the figures are computed here or read from results/benchmark_python.csv.
"""
import csv
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt                                                                   # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm                               # noqa: E402
from matplotlib.patches import Rectangle, Circle                                                  # noqa: E402

from adaptive_denoise import noise, scenario_a, scenario_b, scenario_c, scenario_d, scenario_e, scenario_f   # noqa: E402
from adaptive_denoise import spectral, baselines, inverse_model                                   # noqa: E402
from adaptive_denoise.imageio import load_test_image, REPO                                        # noqa: E402
from adaptive_denoise.metrics import psnr, ssim                                                   # noqa: E402
from adaptive_denoise.pipeline import SCENARIOS, BASELINES, apply_scenario, cascade               # noqa: E402
from adaptive_denoise.plotstyle import (setup, clean_axes, panel_label, show_image, INK, INK2, MUTED, GRID,  # noqa: E402
                                        BLUE, ORANGE, AQUA, YELLOW, RED, NEUTRAL)

OUT = REPO / "figures" / "results"
CACHE = REPO / "results" / "cache"
CROPS = {"camera": (80, 272, 160, 352), "lena": (210, 402, 220, 412)}

X, NAME = load_test_image()
CROP = CROPS.get(NAME.lower(), (160, 352, 160, 352))


def crop(img):
    r0, r1, c0, c1 = CROP
    return img[r0:r1, c0:c1]


def cached(key, method):
    """Output of ``method`` on noise ``key`` from the benchmark cache, recomputed if missing."""
    p = CACHE / f"{key}__{method}.npy"
    if p.exists():
        return np.load(p).astype(float)
    nz = noise.make(key, X)
    if method == "noisy":
        return nz.y
    return apply_scenario(method, nz) if method in SCENARIOS else BASELINES[method](nz.y)


def qual(img):
    return f"{psnr(X, img):.2f} dB, SSIM {ssim(X, img):.3f}"


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  wrote", name, flush=True)


def signed_show(ax, img, title, lim=None):
    lim = lim if lim is not None else float(np.percentile(np.abs(img), 99.5)) + 1e-9
    ax.imshow(img, cmap="gray", vmin=-lim, vmax=lim, interpolation="nearest")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(title, fontsize=8.5, color=INK, pad=3)


# ------------------------------------------------------------------------------------------------ overview
def fig_gallery():
    fig, axs = plt.subplots(3, 4, figsize=(11, 8.6))
    ax = axs[0, 0]
    show_image(ax, X, f"clean ({NAME}), 512 x 512")
    r0, r1, c0, c1 = CROP
    ax.add_patch(Rectangle((c0, r0), c1 - c0, r1 - r0, fill=False, ec=ORANGE, lw=1.5))
    ax.text(c0, r0 - 6, "zoom", color=ORANGE, fontsize=7.5, va="bottom")
    for k, key in enumerate(noise.ORDER):
        y = cached(key, "noisy")
        a = axs.flat[k + 1]
        show_image(a, crop(y), f"{noise.LABELS[key]}\nPSNR {psnr(X, y):.2f} dB")
    fig.suptitle("The test image and the eleven corruptions (zoomed region)", fontsize=11, color=INK, y=0.995)
    fig.tight_layout()
    save(fig, "fig_noise_gallery.png")


def fig_spectra():
    fig, axs = plt.subplots(3, 4, figsize=(11, 8.6))
    f = np.fft.fftshift(np.fft.fftfreq(512))
    ext = [f[0], f[-1], f[-1], f[0]]

    def spec(img):
        S = spectral.log_spectrum(img)
        return S

    ax = axs[0, 0]
    S = spec(X)
    ax.imshow(S, cmap="gray_r", extent=ext, vmin=np.percentile(S, 5), vmax=np.percentile(S, 99.9))
    ax.set_title("clean image", fontsize=8.5)
    for k, key in enumerate(noise.ORDER):
        nz = cached(key, "noisy") - X
        S = spec(nz)
        a = axs.flat[k + 1]
        a.imshow(S, cmap="gray_r", extent=ext, vmin=np.percentile(S, 5), vmax=np.percentile(S, 99.95))
        a.set_title(noise.LABELS[key], fontsize=8.5)
    for a in axs.flat:
        a.set_xticks([-0.5, 0, 0.5])
        a.set_yticks([-0.5, 0, 0.5])
        a.tick_params(labelsize=7, length=2)
    axs[2, 0].set_xlabel("horizontal frequency v (cycles/pixel)", fontsize=8)
    axs[2, 0].set_ylabel("vertical frequency u", fontsize=8)
    fig.suptitle("Where each corruption lives: log-magnitude spectrum of (noisy - clean); darker = more power",
                 fontsize=11, color=INK, y=0.995)
    fig.tight_layout()
    save(fig, "fig_noise_spectra.png")


def read_benchmark():
    rows = {}
    with open(REPO / "results" / "benchmark_python.csv") as fh:
        for r in csv.DictReader(fh):
            rows[(r["noise"], r["method"])] = r
    return rows


def fig_matrix():
    R = read_benchmark()
    methods = SCENARIOS + list(BASELINES)
    names = ["A\nnotch", "B\nbias", "C\nno ref.", "D\nself-tuning", "D\ngated", "E\nline enh.", "F\nreference",
             "median\n3 x 3", "adaptive\nmedian", "Wiener\n5 x 5"]
    G = np.full((len(noise.ORDER), len(methods)), np.nan)
    for i, key in enumerate(noise.ORDER):
        for j, m in enumerate(methods):
            v = R[(key, m)]["gain"]
            G[i, j] = float(v) if v not in ("", "nan") else np.nan
    cmap = LinearSegmentedColormap.from_list("div", ["#b42f2f", RED, "#f2a3a2", NEUTRAL, "#9ec5f4", "#3987e5", "#184f95"])
    norm = TwoSlopeNorm(vmin=-6, vcenter=0, vmax=20)
    fig, ax = plt.subplots(figsize=(11.2, 6.4))
    xs = np.array([j + (0.45 if j >= 7 else 0) for j in range(len(methods))])
    for i in range(G.shape[0]):
        finite = G[i][np.isfinite(G[i])]
        best = finite.max()
        for j in range(G.shape[1]):
            v = G[i, j]
            x = xs[j]
            if np.isnan(v):
                ax.add_patch(Rectangle((x - 0.47, i - 0.46), 0.94, 0.92, fc="white", ec=GRID, lw=0.8))
                ax.text(x, i, "n/a", ha="center", va="center", fontsize=7.5, color=MUTED)
                continue
            c = cmap(norm(np.clip(v, -6, 20)))
            ax.add_patch(Rectangle((x - 0.47, i - 0.46), 0.94, 0.92, fc=c, ec="none"))
            lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
            tc = "white" if lum < 0.5 else INK
            ax.text(x, i, "0.0" if abs(v) < 0.05 else f"{v:+.1f}", ha="center", va="center", fontsize=8, color=tc,
                    fontweight="bold" if v == best and v > 0.5 else "normal")
            if v == best and v > 0.5:
                ax.add_patch(Rectangle((x - 0.47, i - 0.46), 0.94, 0.92, fill=False, ec=INK, lw=1.4))
    ax.set_xlim(-0.6, xs[-1] + 0.6)
    ax.set_ylim(len(noise.ORDER) - 0.5, -0.5)
    ax.set_xticks(xs)
    ax.set_xticklabels(names, fontsize=8)
    ax.set_yticks(range(len(noise.ORDER)))
    ax.set_yticklabels([f"{noise.LABELS[k]}  ({float(R[(k, 'noisy')]['psnr']):.1f} dB)" for k in noise.ORDER], fontsize=8.5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.xaxis.tick_top()
    ax.text(3.0, -1.55, "the six scenarios (fixed default parameters)", ha="center", fontsize=8.5, color=INK2)
    ax.text(xs[8], -1.55, "non-adaptive references", ha="center", fontsize=8.5, color=INK2)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.015, ticks=[-6, -3, 0, 5, 10, 15, 20])
    cb.set_label("PSNR gain over the noisy input (dB)", fontsize=8.5, color=INK2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=7.5)
    ax.set_title(f"Which scenario fits which corruption: PSNR gain in dB on the 512 x 512 '{NAME}' image "
                 "(outlined = best of the row)", fontsize=10, color=INK, pad=48)
    save(fig, "fig_benchmark_matrix.png")


def fig_cascade():
    nz = noise.mixed(X)
    stages = []
    for k in range(10):
        p = CACHE / f"mixed__stage{k}.npy"
        if not p.exists():
            break
        stages.append(np.load(p).astype(float))
    if len(stages) < 6:
        st = cascade(nz)
        stages = [im for _, im in st]
    labels = ["input: all corruptions", "F  optical-black ref.\n(row banding)", "F  reference output\n(readout telegraph)",
              "A  adaptive notch\n(periodic)", "D  error-gated\n(impulses, bursts)", "E  line enhancer\n(broadband rest)"]
    fig = plt.figure(figsize=(13, 6.2))
    gs = fig.add_gridspec(2, 6, height_ratios=[1, 1.08], hspace=0.1, wspace=0.08)
    for k in range(6):
        a = fig.add_subplot(gs[0, k])
        show_image(a, crop(stages[k]), f"{labels[k]}\n{psnr(X, stages[k]):.2f} dB")
    a = fig.add_subplot(gs[1, 0:2])
    ps = [psnr(X, s) for s in stages]
    a.plot(range(6), ps, color=BLUE, marker="o", ms=6, mec="white", mew=1.5)
    for k, p in enumerate(ps):
        a.text(k - 0.12, p + 0.35, f"{p:.1f}", ha="right", va="bottom", fontsize=7.5, color=INK2,
               bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))
    b_med = psnr(X, baselines.median3(nz.y))
    b_amf = psnr(X, baselines.adaptive_median(nz.y))
    for v, lab in [(b_med, "median 3 x 3 on the input"), (b_amf, "adaptive median on the input")]:
        a.hlines(v, -0.5, 6.5, color=MUTED, lw=1.0, zorder=0)
        a.text(-0.45, v + 0.2, lab, fontsize=7.5, color=INK2, ha="left", va="bottom")
    a.set_xticks(range(6))
    a.set_xticklabels(["input", "F", "F", "A", "D gated", "E"], fontsize=8)
    a.set_ylabel("PSNR (dB)")
    a.set_xlim(-0.6, 6.6)
    a.set_ylim(min(ps) - 1.5, max(ps) + 2.0)
    clean_axes(a)
    a.set_title("PSNR after each stage", fontsize=9)
    a2 = fig.add_subplot(gs[1, 2:4])
    show_image(a2, stages[0], "input (full frame)")
    a3 = fig.add_subplot(gs[1, 4:6])
    show_image(a3, stages[5], "after the cascade (full frame)")
    fig.suptitle("All corruptions at once: each scenario removes the part it is built for", fontsize=11, color=INK, y=0.995)
    save(fig, "fig_cascade.png")


# ------------------------------------------------------------------------------------------------ scenario A
def fig_A():
    nz = noise.make("periodic", X)
    out, used = scenario_a.adaptive_notch(nz.y, mu2=0.001)
    fig, axs = plt.subplots(1, 4, figsize=(13, 3.6))
    show_image(axs[0], crop(nz.y), f"(a) stripes + harmonic + moire\n{qual(nz.y)}")
    R, f = spectral.peak_ratio_map(nz.y)
    ax = axs[1]
    lr = np.log10(np.maximum(R, 1e-3))
    ax.imshow(lr, cmap="gray_r", extent=[f[0], f[-1], f[-1], f[0]], vmin=0, vmax=2.6)
    for (u, v) in used:
        for sgn in (1, -1):
            ax.add_patch(Circle((sgn * v, sgn * u), 0.025, fill=False, ec=ORANGE, lw=1.6))
    ax.set_xlim(-0.3, 0.3)
    ax.set_ylim(0.3, -0.3)
    ax.set_xlabel("v (cycles/pixel)", fontsize=8)
    ax.set_ylabel("u (cycles/pixel)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.set_title("(b) spectrum / local median (log)\ndetected peaks circled", fontsize=8.5)
    show_image(axs[2], crop(out), f"(c) adaptive notch output\n{qual(out)}")
    signed_show(axs[3], crop(nz.y - out), "(d) removed component (d - e)", lim=0.25)
    fig.tight_layout()
    save(fig, "fig_A_image.png")
    print("    A detected:", [(round(u, 4), round(v, 4)) for u, v in used])

    fig, axs = plt.subplots(1, 4, figsize=(14, 3.5), gridspec_kw=dict(width_ratios=[1.25, 0.8, 1, 1]))
    ax = axs[0]
    om0 = 2 * np.pi * 0.1
    om = np.linspace(0.3, 0.95, 600)
    for c, m in zip([BLUE, ORANGE, AQUA], [0.02, 0.05, 0.1]):
        Ht = np.abs(scenario_a.notch_response_theory(om0, m, om))
        ax.plot(om / (2 * np.pi), Ht, color=c, lw=2, label=f"$\\mu_2C^2$ = {m}")
        omm, Hm = scenario_a.notch_response_measured(om0, m, n=2 ** 17)
        sel = (omm > 0.3) & (omm < 0.95)
        ax.plot(omm[sel][::3] / (2 * np.pi), np.abs(Hm[sel][::3]), "o", color=c, ms=3.2, mec="none", alpha=0.85)
    ax.set_xlabel("frequency (cycles/sample)")
    ax.set_ylabel("|H|")
    ax.set_title("(a) notch response: lines theory, dots LMS", fontsize=8.5)
    ax.legend(loc="lower left", fontsize=7.5)
    clean_axes(ax)
    ax = axs[1]
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), color=AXIS_C, lw=1.0)
    zr, pl = scenario_a.notch_poles_zeros(om0, 0.1)
    ax.plot(zr.real, zr.imag, "o", mfc="white", mec=INK, ms=7, mew=1.5, label="zeros")
    ax.plot(pl.real, pl.imag, "x", color=ORANGE, ms=8, mew=2, label="poles")
    ax.set_aspect("equal")
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)
    ax.axhline(0, color=GRID, lw=0.8)
    ax.axvline(0, color=GRID, lw=0.8)
    ax.set_title("(b) poles and zeros, $\\mu_2C^2$ = 0.1", fontsize=8.5)
    ax.text(0.0, 0.12, f"zeros on the unit circle\npole radius {abs(pl[0]):.3f}", fontsize=7.5, color=INK2, ha="center")
    ax.legend(loc="lower left", fontsize=7.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax = axs[2]
    mus = [0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05]
    pd, pt, pc = [], [], []
    truef = nz.side["freqs"]
    for m in mus:
        pd.append(psnr(X, scenario_a.adaptive_notch(nz.y, mu2=m)[0]))
        pt.append(psnr(X, scenario_a.notch_lms(nz.y, truef, mu2=m)))
        pc.append(psnr(X, scenario_a.notch_lms(X, truef, mu2=m)))
    ax.semilogx(mus, pt, color=BLUE, lw=3.2, label="true frequencies")
    ax.semilogx(mus, pc, color=AQUA, lw=0, marker="o", ms=6, mfc="white", mew=1.6,
                label="clean image in: the distortion alone")
    ax.semilogx(mus, pd, color=ORANGE, marker="o", ms=5, mec="white", label="detected frequencies")
    ax.axhline(psnr(X, nz.y), color=MUTED, lw=1)
    ax.text(mus[-1], psnr(X, nz.y) + 0.6, "noisy input", fontsize=7.5, color=INK2, ha="right")
    ax.set_xlabel("$\\mu_2 C^2$ (notch width, rad/sample)")
    ax.set_ylabel("PSNR (dB)")
    ax.set_title("(c) narrower notch: less image removed", fontsize=8.5)
    ax.legend(fontsize=7.5, loc="lower left", bbox_to_anchor=(0.0, 0.1))
    clean_axes(ax)
    ax = axs[3]
    xs = np.arange(512)
    f0 = 0.0925
    stripes = X + 0.12 * np.sin(2 * np.pi * f0 * xs + 0.7)[None, :]
    offs = [0, 0.1, 0.25, 0.5, 1.0, 2.0]
    for c, m in zip([BLUE, ORANGE, AQUA], [0.002, 0.01, 0.05]):
        ps = [psnr(X, scenario_a.notch_lms(stripes, [(0.0, f0 + db / 512)], mu2=m)) for db in offs]
        ax.plot(offs, ps, color=c, marker="o", ms=5, mec="white", label=f"$\\mu_2C^2$ = {m}")
    ax.axhline(psnr(X, stripes), color=MUTED, lw=1)
    ax.set_xlabel("reference frequency error (FFT bins of 512)")
    ax.set_ylabel("PSNR (dB)")
    ax.set_title("(d) ...but a narrow notch needs an exact frequency", fontsize=8.5)
    ax.legend(fontsize=7.5)
    clean_axes(ax)
    fig.tight_layout()
    save(fig, "fig_A_theory.png")


# ------------------------------------------------------------------------------------------------ scenario B
def fig_B():
    nz = noise.make("banding", X)
    tb, _ = scenario_b.bias_canceller(nz.y, mu2=0.02, update="lms")
    il0, off0 = scenario_b.interline_canceller(nz.y, mu2=0.001, hp_rows=None)
    il, off = scenario_b.interline_canceller(nz.y, mu2=0.001, hp_rows=16)
    fig = plt.figure(figsize=(13.5, 3.7))
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 1, 1, 1.5], wspace=0.12)
    a = [fig.add_subplot(gs[0, k]) for k in range(5)]
    show_image(a[0], crop(nz.y), f"(a) row banding\n{qual(nz.y)}")
    show_image(a[1], crop(tb + 0.5), f"(b) textbook canceller along rows\n{psnr(X, tb + X.mean()):.2f} dB: scene flattened")
    show_image(a[2], crop(il0), f"(c) line-to-line, no high-pass\n{qual(il0)}")
    show_image(a[3], crop(il), f"(d) line-to-line + high-pass\n{qual(il)}")
    ax = a[4]
    true_c = nz.side["truth"]
    n = 160
    rows = np.arange(n)
    ax.plot(rows, true_c[:n] - true_c[:n].mean(), color=BLUE, lw=2.2, label="true row offset $c_i$")
    ax.plot(rows, off0[:n] - off0[:n].mean(), color=ORANGE, lw=1.0, label="correction $b_i$, no high-pass")
    ax.plot(rows, off[:n] - off[:n].mean(), color=AQUA, lw=1.0, label="correction $b_i$ + high-pass")
    ax.set_xlabel("row")
    ax.set_title("(e) per-row corrections: without the high-pass\nthey drift with the scene's own vertical changes",
                 fontsize=8.5)
    ax.legend(fontsize=7.2, loc="lower left", ncol=1)
    clean_axes(ax)
    fig.subplots_adjust(left=0.02, right=0.99, top=0.83, bottom=0.14, wspace=0.18)
    save(fig, "fig_B_image.png")

    fig, axs = plt.subplots(1, 3, figsize=(13.5, 3.6), gridspec_kw=dict(width_ratios=[1, 1.6, 1.1]))
    ax = axs[0]
    om = 2 * np.pi * np.logspace(-4, np.log10(0.5), 800)
    for c, m in zip([BLUE, ORANGE, AQUA], [0.005, 0.02, 0.1]):
        ax.semilogx(om / (2 * np.pi), 20 * np.log10(np.abs(scenario_b.bias_response_theory(m, om))), color=c, label=f"$\\mu_2$ = {m}")
    ax.set_ylim(-40, 3)
    ax.set_xlabel("frequency (cycles/pixel)")
    ax.set_ylabel("|H| (dB)")
    ax.set_title("(a) $H(z) = (z-1)/(z-(1-\\mu_2))$: a high-pass", fontsize=8.5)
    ax.legend(fontsize=7.5, loc="lower right")
    clean_axes(ax)
    ax = axs[1]
    rng = np.random.default_rng(5)
    s = scenario_b.afm_scene(n_obj=60)
    ys = s + scenario_b.row_offsets_and_tilt(s.shape, rng) + 0.01 * rng.standard_normal(s.shape)
    o_lms, _ = scenario_b.bias_canceller(ys, 0.01, "lms")
    o_gate, _ = scenario_b.bias_canceller(ys, 0.02, "gated")
    strip = np.concatenate([s[:256, :256], ys[:256, :256] - ys.mean() + s.mean(),
                            o_lms[:256, :256] + s.mean(), o_gate[:256, :256] + np.median(s)], axis=1)
    ax.imshow(strip, cmap="gray", vmin=0.1, vmax=0.8)
    ax.set_xticks([128, 384, 640, 896])
    ax.set_xticklabels(["flat-background scene", f"offsets + tilt\n{scenario_b.offset_aligned_psnr(s, ys):.1f} dB",
                        f"LMS (report)\n{scenario_b.offset_aligned_psnr(s, o_lms):.1f} dB",
                        f"gated LMS\n{scenario_b.offset_aligned_psnr(s, o_gate):.1f} dB"], fontsize=7.5)
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title("(b) where the textbook form works: flat backgrounds (probe microscopy, documents)", fontsize=8.5)
    ax = axs[2]
    covs = [20, 60, 120, 200]
    res = {k: [] for k in ["none", "LMS", "sign-error", "gated"]}
    cov_frac = []
    for nobj in covs:
        sc = scenario_b.afm_scene(n_obj=nobj, seed=1)
        r2 = np.random.default_rng(9)
        yy = sc + scenario_b.row_offsets_and_tilt(sc.shape, r2) + 0.01 * r2.standard_normal(sc.shape)
        cov_frac.append(100 * np.mean(sc > 0.36))
        res["none"].append(scenario_b.offset_aligned_psnr(sc, yy))
        res["LMS"].append(scenario_b.offset_aligned_psnr(sc, scenario_b.bias_canceller(yy, 0.01, "lms")[0]))
        res["sign-error"].append(scenario_b.offset_aligned_psnr(sc, scenario_b.bias_canceller(yy, 0.002, "sign")[0]))
        res["gated"].append(scenario_b.offset_aligned_psnr(sc, scenario_b.bias_canceller(yy, 0.02, "gated")[0]))
    for c, (k, v) in zip([MUTED, BLUE, ORANGE, AQUA], res.items()):
        ax.plot(cov_frac, v, color=c, marker="o", ms=5, mec="white", label=k)
    ax.set_xlabel("share of pixels covered by objects (%)")
    ax.set_ylabel("PSNR (dB)")
    ax.set_title("(c) the more scene, the more it is mistaken for drift", fontsize=8.5)
    ax.legend(fontsize=7.5, ncol=2)
    clean_axes(ax)
    fig.tight_layout()
    save(fig, "fig_B_theory.png")


# ------------------------------------------------------------------------------------------------ scenario C
def fig_C():
    nz = noise.make("periodic", X)
    raw = scenario_c.delayed_canceller(nz.y)
    sub, info = scenario_c.subband_canceller(nz.y, record=True)
    fig, axs = plt.subplots(1, 4, figsize=(13, 3.6))
    show_image(axs[0], crop(nz.y), f"(a) periodic interference\n{qual(nz.y)}")
    show_image(axs[1], crop(raw), f"(b) delayed canceller on raw rows\n{qual(raw)}")
    show_image(axs[2], crop(sub), f"(c) two-band canceller\n{qual(sub)}")
    signed_show(axs[3], crop(nz.y - sub), "(d) removed component", lim=0.25)
    fig.tight_layout()
    save(fig, "fig_C_image.png")

    fig, axs = plt.subplots(1, 2, figsize=(12, 3.5))
    ax = axs[0]
    fr, Hf = scenario_c.predictor_response(info["weights"], 8)
    ax.plot(fr, np.abs(Hf), color=BLUE, lw=1.6)
    top = float(np.abs(Hf).max())
    for k, (A, u, v, ph) in enumerate(noise.DEFAULTS["periodic"]["components"]):
        ax.axvline(v, color=ORANGE, lw=1.0, zorder=0)
        ax.text(v + 0.006, 0.5 * top, f"{v:.4f}", color=INK2, fontsize=7.5, ha="left",
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))
    ax.set_xlabel("frequency along the row (cycles/pixel)")
    ax.set_ylabel("|gain| of the learned predictor")
    ax.set_title("(a) the filter found the interference lines by itself (orange: true along-row frequencies)", fontsize=8.5)
    ax.set_xlim(0, 0.5)
    clean_axes(ax)
    ax = axs[1]
    for img, c, lab in [(nz.y, MUTED, "noisy"), (sub, BLUE, "two-band canceller"), (X, AQUA, "clean")]:
        fq, P = spectral.row_spectrum(img)
        ax.semilogy(fq, P, color=c, lw=1.3 if c != MUTED else 1.0, label=lab)
    ax.set_xlabel("frequency along the row (cycles/pixel)")
    ax.set_ylabel("row-averaged power")
    ax.set_xlim(0, 0.5)
    ax.set_title("(b) row spectra: the lines are gone, the image spectrum is kept", fontsize=8.5)
    ax.legend(fontsize=7.5)
    clean_axes(ax)
    fig.tight_layout()
    save(fig, "fig_C_theory.png")


# ------------------------------------------------------------------------------------------------ scenario D
def fig_D():
    g = noise.make("gaussian", X)
    yD, info = scenario_d.self_tuning(g.y, record=True)
    wien = baselines.local_wiener(g.y)
    imp = noise.make("impulse", X)
    yG, flags = scenario_d.self_tuning_gated(imp.y)
    med = baselines.median3(imp.y)
    fig, axs = plt.subplots(2, 4, figsize=(12.5, 6.9))
    show_image(axs[0, 0], crop(g.y), f"(a) Gaussian, sigma = 20/255\n{qual(g.y)}")
    show_image(axs[0, 1], crop(yD), f"(b) D: filter output\n{qual(yD)}")
    signed_show(axs[0, 2], crop(g.y - yD), "(c) error output e = d - y\n(the removed noise)", lim=0.25)
    show_image(axs[0, 3], crop(wien), f"(d) Wiener 5 x 5 (reference)\n{qual(wien)}")
    show_image(axs[1, 0], crop(imp.y), f"(e) impulse noise, 10 %\n{qual(imp.y)}")
    show_image(axs[1, 1], crop(yG), f"(f) D, error-gated\n{qual(yG)}")
    m = imp.side["mask"]
    viz = np.ones(X.shape + (3,))
    viz[flags & m] = (0.16, 0.47, 0.84)
    viz[flags & ~m] = (0.92, 0.41, 0.20)
    viz[~flags & m] = (0.10, 0.10, 0.10)
    axs[1, 2].imshow(crop(viz), interpolation="nearest")
    axs[1, 2].set_xticks([])
    axs[1, 2].set_yticks([])
    for sp in axs[1, 2].spines.values():
        sp.set_visible(False)
    rec = (flags & m).sum() / m.sum()
    fa = (flags & ~m).sum() / (~m).sum()
    axs[1, 2].set_title(f"(g) pixels flagged by |e|: blue hit ({100 * rec:.0f}%),\norange false ({100 * fa:.1f}%), black missed",
                        fontsize=8.5)
    show_image(axs[1, 3], crop(med), f"(h) median 3 x 3 (reference)\n{qual(med)}")
    fig.tight_layout()
    save(fig, "fig_D_image.png")

    fig, axs = plt.subplots(1, 3, figsize=(13, 3.6), gridspec_kw=dict(width_ratios=[0.8, 1.2, 1.1]))
    ax = axs[0]
    k = info["weights"]
    lim = np.abs(k).max()
    cmap = LinearSegmentedColormap.from_list("d2", [RED, "#f2a3a2", NEUTRAL, "#9ec5f4", "#184f95"])
    ax.imshow(k, cmap=cmap, vmin=-lim, vmax=lim)
    for a_ in range(k.shape[0]):
        for b_ in range(k.shape[1]):
            if a_ == 2 and b_ == 2:
                ax.text(b_, a_, "blind\nspot", ha="center", va="center", fontsize=6.5, color=INK2)
            else:
                ax.text(b_, a_, f"{k[a_, b_]:.2f}", ha="center", va="center", fontsize=7, color=INK)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"(a) learned 5 x 5 weights (sum {k.sum():.2f})", fontsize=8.5)
    ax = axs[1]
    c = info["curve"]
    H = X.shape[0]
    ax.plot(np.arange(H), c[:H], color=BLUE, lw=1.2, label="pass 1")
    ax.plot(np.arange(H), c[H:2 * H], color=ORANGE, lw=1.2, label="pass 2")
    ax.axhline((20 / 255) ** 2, color=MUTED, lw=1.0)
    ax.text(H * 0.98, (20 / 255) ** 2 * 0.97, "noise variance", fontsize=7.5, color=INK2, ha="right", va="top")
    ax.set_xlabel("image row (raster time)")
    ax.set_ylabel("mean squared error output")
    ax.set_title("(b) learning curve: $e^2$ cannot go below the noise", fontsize=8.5)
    ax.legend(fontsize=7.5)
    clean_axes(ax)
    ax = axs[2]
    alphas = [0.001, 0.003, 0.01, 0.03, 0.1]
    for col, r in zip([BLUE, ORANGE, AQUA], [1, 2, 3]):
        ps = [psnr(X, scenario_d.blindspot_lms(g.y, r=r, alpha=a)) for a in alphas]
        ax.semilogx(alphas, ps, color=col, marker="o", ms=5, mec="white", label=f"r = {r} ({(2 * r + 1) ** 2 - 1} taps)")
    ax.axhline(psnr(X, wien), color=MUTED, lw=1.0)
    ax.text(alphas[0], psnr(X, wien) + 0.08, "Wiener 5 x 5", fontsize=7.5, color=INK2)
    ax.set_xlabel("normalised step $\\alpha$  (misadjustment ~ $\\alpha$/2)")
    ax.set_ylabel("PSNR (dB)")
    ax.set_title("(c) window size and step size", fontsize=8.5)
    ax.legend(fontsize=7.5, loc="upper right", bbox_to_anchor=(1.0, 0.9))
    clean_axes(ax)
    fig.tight_layout()
    save(fig, "fig_D_theory.png")


# ------------------------------------------------------------------------------------------------ scenario E
LATTICE = ((0.22, 0.071, 0.043, 0.4), (0.14, 0.118, -0.067, 1.1))


def fig_E():
    fig, axs = plt.subplots(1, 4, figsize=(14.5, 3.5))
    ax = axs[0]
    Ls = np.arange(4, 513)
    for c, snr in zip([BLUE, ORANGE, AQUA], [0.01, 0.1, 1.0]):
        ax.semilogx(Ls, scenario_e.ale_peak_gain(Ls, snr), color=c, label=f"SNR = {snr}")
        Lp = np.array([8, 16, 32, 64, 128, 256, 512])
        ex = [abs(scenario_e.ale_response(scenario_e.ale_wiener_weights(L, 1, snr, 2 * np.pi / 16), 1, 2 * np.pi / 16)[0])
              for L in Lp]
        ax.semilogx(Lp, ex, "o", color=c, ms=5, mec="white")
    ax.set_xlabel("number of weights L")
    ax.set_ylabel("peak gain at the line")
    ax.set_title("(a) $G = (L/2)$SNR$/((L/2)$SNR$+1)$:\nlines formula, dots exact Wiener-Hopf", fontsize=8.5)
    ax.legend(fontsize=7.5, loc="upper left")
    clean_axes(ax)
    ax = axs[1]
    rng = np.random.default_rng(3)
    n = 40000
    om0 = 2 * np.pi * 0.12
    d = np.sqrt(2 * 0.5) * np.cos(om0 * np.arange(n) + 0.3) + rng.standard_normal(n)
    for c, L in zip([BLUE, ORANGE], [16, 64]):
        _, _, w, _ = scenario_e.ale_lms(d, L, 1, 0.5 / (L * np.var(d)) * 0.05)
        om = np.linspace(0, np.pi, 1500)
        ax.plot(om / (2 * np.pi), np.abs(scenario_e.ale_response(w, 1, om)), color=c, lw=1.6, label=f"LMS, L = {L}")
        ww = scenario_e.ale_wiener_weights(L, 1, 0.5, om0)
        ax.plot(om / (2 * np.pi), np.abs(scenario_e.ale_response(ww, 1, om)), color=c, lw=0.9, alpha=0.6)
    ax.axvline(0.12, color=MUTED, lw=0.8)
    ax.set_xlabel("frequency (cycles/sample)")
    ax.set_ylabel("|H|")
    ax.set_title("(b) converged ALE = band-pass on the line\n(thin: Wiener solution), SNR = 0.5", fontsize=8.5)
    ax.legend(fontsize=7.5)
    clean_axes(ax)
    ax = axs[2]
    H = 192
    lat = scenario_e.lattice((H, H), LATTICE)
    rngl = np.random.default_rng(21)
    draws = [lat + 0.2 * rngl.standard_normal(lat.shape) for _ in range(2)]
    taps, lms_p, lim_p = [], [], []
    for r in [1, 2, 3, 4]:
        taps.append((2 * r + 1) ** 2 - 1)
        best = max(np.mean([psnr(lat, scenario_d.blindspot_lms(dd, r=r, mu2=m, passes=3)) for dd in draws])
                   for m in [5e-5, 1e-4, 2e-4, 5e-4])
        lms_p.append(best)
        lim_p.append(scenario_e.wiener_limit_2d(LATTICE, 0.2, r))
    ax.plot(taps, lim_p, color=MUTED, marker="s", ms=5, mec="white", label="Wiener limit (infinite data)")
    ax.plot(taps, lms_p, color=BLUE, marker="o", ms=5, mec="white", label="LMS, best step")
    ax.set_xlabel("taps (2-D window minus blind spot)")
    ax.set_ylabel("PSNR (dB)")
    ax.set_title("(c) lattice texture in white noise:\nmore taps, more gain; LMS trails the limit", fontsize=8.5)
    ax.legend(fontsize=7.5, loc="lower right")
    clean_axes(ax)
    ax = axs[3]
    rngc = np.random.default_rng(23)
    white = lat + 0.2 * rngc.standard_normal(lat.shape)
    nc = noise.gaussian_blur(rngc.standard_normal(lat.shape), 1.0)
    corr = lat + nc * (0.2 / nc.std())
    holes = [0, 1, 2, 3]
    pw = [psnr(lat, scenario_d.blindspot_lms(white, r=5, hole=h, mu2=0.001, passes=3)) for h in holes]
    pc = [psnr(lat, scenario_d.blindspot_lms(corr, r=5, hole=h, mu2=0.001, passes=3)) for h in holes]
    ax.plot(holes, pw, color=BLUE, marker="o", ms=5, mec="white", label="white noise")
    ax.plot(holes, pc, color=ORANGE, marker="o", ms=5, mec="white", label="correlated noise (1 px)")
    ax.set_xticks(holes)
    ax.set_xticklabels(["1 x 1", "3 x 3", "5 x 5", "7 x 7"])
    ax.set_xlabel("blind spot (the delay $\\Delta$)")
    ax.set_ylabel("PSNR (dB)")
    ax.set_title("(d) the blind spot must outlast\nthe noise correlation", fontsize=8.5)
    ax.legend(fontsize=7.5, loc="center left")
    clean_axes(ax)
    fig.tight_layout()
    save(fig, "fig_E_theory.png")

    noisy_l = lat + 0.2 * np.random.default_rng(31).standard_normal(lat.shape)
    yE = scenario_d.blindspot_lms(noisy_l, r=4, mu2=1e-4, passes=3)
    wl = baselines.local_wiener(noisy_l)
    cor = noise.make("correlated", X)
    yD0 = cached("correlated", "D")
    yE2, inf2 = scenario_e.line_enhancer(cor.y, record=True)
    fig, axs = plt.subplots(1, 6, figsize=(15, 3.1))
    for a, im, t in [(axs[0], noisy_l, f"(a) lattice + noise\n{psnr(lat, noisy_l):.2f} dB"),
                     (axs[1], yE, f"(b) E, 80 taps\n{psnr(lat, yE):.2f} dB"),
                     (axs[2], wl, f"(c) Wiener 5 x 5\n{psnr(lat, wl):.2f} dB")]:
        show_image(a, im[:128, :128], t, vmin=0, vmax=1)
    show_image(axs[3], crop(cor.y), f"(d) correlated noise\n{psnr(X, cor.y):.2f} dB")
    show_image(axs[4], crop(yD0), f"(e) D, blind spot 1 x 1\n{psnr(X, yD0):.2f} dB")
    hh = inf2["hole"]
    show_image(axs[5], crop(yE2), f"(f) E, blind spot {2 * hh + 1} x {2 * hh + 1} (measured)\n{psnr(X, yE2):.2f} dB")
    fig.tight_layout()
    save(fig, "fig_E_image.png")


# ------------------------------------------------------------------------------------------------ scenario F
def fig_F():
    b = noise.make("banding", X)
    s = b.side
    w = scenario_f.train_row_weight(s["dark"], s["dark_ob"])
    yb = scenario_f.row_reference_canceller(b.y, s["ob"], w)
    t = noise.make("telegraph_readout", X)
    yt, wt = scenario_f.channel_reference_canceller(t.y, t.side["ref_out"], train=(t.side["dark"], t.side["dark_ref"]))
    fig = plt.figure(figsize=(14.5, 6.4))
    gs = fig.add_gridspec(2, 5, width_ratios=[1, 1, 1, 0.16, 1.6], hspace=0.35, wspace=0.1)
    a = fig.add_subplot(gs[0, 0])
    show_image(a, crop(b.y), f"(a) row banding\n{qual(b.y)}")
    a = fig.add_subplot(gs[0, 1])
    show_image(a, crop(yb), f"(b) F, optical-black reference\n{qual(yb)}")
    a = fig.add_subplot(gs[0, 2])
    signed_show(a, crop(b.y - yb), f"(c) removed (w = {w:.3f})", lim=0.15)
    a = fig.add_subplot(gs[0, 4])
    n = 96
    a.plot(np.arange(n), s["truth"][:n], color=BLUE, lw=1.6, label="true row offset $c_i$")
    a.plot(np.arange(n), s["ob"][:n].mean(axis=1), "o", color=ORANGE, ms=3.2, mec="none",
           label="reference: masked-pixel mean")
    a.set_xlabel("row")
    a.set_title("(d) the reference sees the offset, not the scene", fontsize=8.5)
    a.legend(fontsize=7.5, loc="lower right")
    clean_axes(a)
    a = fig.add_subplot(gs[1, 0])
    show_image(a, crop(t.y), f"(e) readout telegraph\n{qual(t.y)}")
    a = fig.add_subplot(gs[1, 1])
    show_image(a, crop(yt), f"(f) F, reference output channel\n{qual(yt)}")
    a = fig.add_subplot(gs[1, 2])
    signed_show(a, crop(t.y - yt), f"(g) removed (w = {wt[0]:.3f})", lim=0.15)
    a = fig.add_subplot(gs[1, 4])
    row = CROP[0] + 40
    j = np.arange(512)
    a.plot(j, t.side["truth"][row], color=BLUE, lw=1.6, label="true telegraph offset")
    a.plot(j, t.side["ref_out"][row], color=ORANGE, lw=0.8, label="reference channel (gain 0.8 + noise)")
    a.set_xlabel(f"pixel along row {row}")
    a.set_title("(h) two-level switching in readout time", fontsize=8.5)
    a.legend(fontsize=7.5, loc="lower right", ncol=1)
    a.set_ylim(-0.14, 0.12)
    clean_axes(a)
    save(fig, "fig_F_image.png")

    fig, axs = plt.subplots(1, 2, figsize=(12.5, 3.6))
    ax = axs[0]
    rr = np.logspace(-4, 1, 200)
    for c, rp in zip([BLUE, ORANGE, AQUA], [0.01, 0.04, 0.16]):
        ax.semilogx(rr, 10 * np.log10(scenario_f.noise_reduction_theory(rp, rr)), color=c, label=f"$R_{{prin}}$ = {rp}")
    p = b.params
    Rp = p["sigma"] ** 2 / p["sigma_row"] ** 2
    for K in [1, 4, 16, 64]:
        meas = []
        for sd in range(3):
            rngk = np.random.default_rng(700 + 10 * K + sd)
            H = 512
            cc = p["sigma_row"] * rngk.standard_normal(H)
            yy = X + cc[:, None] + p["sigma"] * rngk.standard_normal(X.shape)
            ob = cc[:, None] + p["sigma"] * rngk.standard_normal((H, K))
            cd = p["sigma_row"] * rngk.standard_normal(H)
            dark = cd[:, None] + p["sigma"] * rngk.standard_normal(X.shape)
            dob = cd[:, None] + p["sigma"] * rngk.standard_normal((H, K))
            wk = scenario_f.train_row_weight(dark, dob)
            out = scenario_f.row_reference_canceller(yy, ob, wk)
            meas.append(10 * np.log10(np.mean((yy - X) ** 2) / np.mean((out - X) ** 2)))
        Rr = (p["sigma"] ** 2 / K) / p["sigma_row"] ** 2
        ax.plot(Rr, np.mean(meas), "o", color=ORANGE, ms=7, mec="white", mew=1.5)
        ax.text(Rr * 1.15, np.mean(meas) + 0.35, f"K = {K}", fontsize=7.5, color=INK2)
    ax.set_xlabel("$R_{refn}$ = uncorrelated / correlated noise in the reference")
    ax.set_ylabel("noise reduction (dB)")
    ax.set_title("(a) theory (lines) and measured banding canceller (dots, $R_{prin}$ = 0.04)", fontsize=8.5)
    ax.legend(fontsize=7.5, loc="lower left")
    clean_axes(ax)
    ax = axs[1]
    hist = {}
    H = 512
    wv = 0.0
    tr = []
    xr = s["dark_ob"].mean(axis=1)
    for i in range(H):
        for jj in range(512):
            wv += 0.5 * (s["dark"][i, jj] - wv * xr[i]) * xr[i]
        tr.append(wv)
    hist["dark-frame training"] = tr
    for mode, lab, mu in [("ob_gated", "online, masked pixels only", 2.0), ("scene", "online, on scene pixels", 0.005)]:
        tr = []
        wv = 0.0
        K = s["ob"].shape[1]
        for i in range(H):
            xri = float(s["ob"][i].mean())
            if mode == "ob_gated":
                tot = float(s["ob"][i].sum())
                for kk in range(K):
                    xk = (tot - s["ob"][i, kk]) / (K - 1)
                    wv += mu * (s["ob"][i, kk] - wv * xk) * xk
            else:
                for jj in range(512):
                    wv += mu * (b.y[i, jj] - wv * xri) * xri
            tr.append(wv)
        hist[lab] = tr
    for c, (k, v) in zip([BLUE, ORANGE, RED], hist.items()):
        ax.plot(np.arange(H), v, color=c, lw=1.5, label=k)
    wopt = 1.0 / (1.0 + (p["sigma"] ** 2 / p["n_ob"]) / p["sigma_row"] ** 2)
    ax.axhline(wopt, color=MUTED, lw=1.0, zorder=0)
    ax.text(H * 0.99, wopt - 0.06, f"Wiener weight {wopt:.3f}", fontsize=7.5, color=INK2, ha="right", va="top",
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))
    ax.set_xlabel("row")
    ax.set_ylabel("weight w")
    ax.set_title("(b) the scene must stay out of the update", fontsize=8.5)
    ax.legend(fontsize=7.5, loc="lower right", bbox_to_anchor=(1.0, 0.04))
    clean_axes(ax)
    fig.tight_layout()
    save(fig, "fig_F_theory.png")


# ------------------------------------------------------------------------------------------------ blur extra
def fig_blur():
    nz = noise.make("blur", X)
    tgt = inverse_model.dead_leaves(seed=5)
    rng = np.random.default_rng(6)
    cal = noise.gaussian_blur(tgt, nz.side["psf_sigma"]) + nz.side["noise_sigma"] * rng.standard_normal(tgt.shape)
    k_ls = inverse_model.least_squares_inverse_filter(tgt, cal, r=4)
    k_lms, info = inverse_model.train_inverse_filter(tgt, cal, r=4, alpha=0.02, passes=4, record=True, w_ref=k_ls)
    o_lms = inverse_model.apply_filter(nz.y, inverse_model.train_inverse_filter(tgt, cal, r=4, alpha=0.02, passes=2))
    o_ls = inverse_model.apply_filter(nz.y, k_ls)
    fig = plt.figure(figsize=(15.5, 3.4))
    gs = fig.add_gridspec(1, 6, width_ratios=[1, 1, 1, 1, 0.42, 1.35], wspace=0.08)
    show_image(fig.add_subplot(gs[0, 0]), tgt[:192, :192], "(a) calibration target\n(known, sharp)")
    show_image(fig.add_subplot(gs[0, 1]), crop(nz.y), f"(b) blurred image\n{qual(nz.y)}")
    show_image(fig.add_subplot(gs[0, 2]), crop(o_lms), f"(c) LMS inverse model, 2 passes\n{qual(o_lms)}")
    show_image(fig.add_subplot(gs[0, 3]), crop(o_ls), f"(d) least squares (Wiener)\n{qual(o_ls)}")
    ax = fig.add_subplot(gs[0, 5])
    dist = info["dist"]
    n_per_pass = len(dist) // 4
    t = np.arange(1, len(dist) + 1) / n_per_pass
    ax.plot(t, dist, color=BLUE, lw=1.8)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("passes over the 512 x 512 target")
    ax.set_ylabel("$||w - w_{LS}|| \\, / \\, ||w_{LS}||$")
    ax.set_title("(e) LMS creeps towards the Wiener kernel:\nblur spreads the eigenvalues", fontsize=8.5)
    clean_axes(ax)
    ax.set_box_aspect(0.8)
    save(fig, "fig_extra_blur.png")


FIGS = {"gallery": fig_gallery, "spectra": fig_spectra, "matrix": fig_matrix, "cascade": fig_cascade,
        "A": fig_A, "B": fig_B, "C": fig_C, "D": fig_D, "E": fig_E, "F": fig_F, "blur": fig_blur}
AXIS_C = "#c3c2b7"

if __name__ == "__main__":
    setup()
    keys = sys.argv[1:] or list(FIGS)
    t0 = time.time()
    for k in keys:
        print(k, flush=True)
        FIGS[k]()
    print(f"done in {time.time() - t0:.0f} s")
