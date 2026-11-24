"""Application examples, overview figures and animations.

    python make_examples.py                 # everything
    python make_examples.py examples        # only the six application examples
    python make_examples.py hero oned gifs  # only the overview figure, the 1-D figure, the animations
    python make_examples.py density         # only the impulse-density sweep of the gated filter

Writes
    figures/overview/fig_hero.png           six corruptions, six cancellers (README banner)
    figures/overview/fig_1d_intuition.png   each scenario first on a 1-D signal
    figures/examples/example_*.png          one realistic application per scenario, and the density sweep of D
    figures/animations/*.gif                the adaptation running in raster order
    data/examples/*.png                     the example images (CC0 / public domain), also used by MATLAB
    results/examples_python.csv             the numbers printed on the example figures
    results/gated_density_sweep.csv         D gated (k = 3, 4) and the medians against impulse density

The example images come from scikit-image's bundled data (coffee, chelsea, gravel and brick are CC0; the
Hubble Deep Field is public domain). They are converted to 512 x 512 grayscale once and stored in
data/examples/, so later runs and the MATLAB demo read the same files.
"""
import csv
import io
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt                                                       # noqa: E402
from matplotlib.colors import LinearSegmentedColormap                                # noqa: E402
from PIL import Image                                                                 # noqa: E402
from skimage import io as skio                                                        # noqa: E402

from adaptive_denoise import noise, scenario_a, scenario_b, scenario_c, scenario_d, scenario_e, scenario_f  # noqa: E402
from adaptive_denoise import baselines                                                # noqa: E402
from adaptive_denoise.imageio import load_test_image, REPO, to_gray                    # noqa: E402
from adaptive_denoise.metrics import psnr, ssim                                       # noqa: E402
from adaptive_denoise.predictor import tap_mask, _row_taps                             # noqa: E402
from adaptive_denoise.plotstyle import (setup, clean_axes, show_image, INK, INK2, MUTED, GRID, BLUE, ORANGE,  # noqa: E402
                                        AQUA, RED, NEUTRAL, VIOLET)

FIG = REPO / "figures"
EXD = REPO / "data" / "examples"
ROWS = []          # (example, method, psnr, ssim) for results/examples_python.csv
DIV = LinearSegmentedColormap.from_list("div", [RED, "#f2a3a2", NEUTRAL, "#9ec5f4", "#184f95"])
LATTICE = ((0.22, 0.071, 0.043, 0.4), (0.14, 0.118, -0.067, 1.1))      # two plane waves, as in make_figures.py


def save(fig, sub, name, dpi=150):
    out = FIG / sub
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print("  wrote", f"figures/{sub}/{name}", flush=True)


def record(example, method, ref, est, offset_aligned=False):
    if offset_aligned:
        p = scenario_b.offset_aligned_psnr(ref, est)
        s = ssim(ref, est - np.mean(est - ref))
    else:
        p, s = psnr(ref, est), ssim(ref, est)
    ROWS.append((example, method, p, s))
    return p


def signed(ax, img, title, lim):
    ax.imshow(img, cmap="gray", vmin=-lim, vmax=lim, interpolation="nearest")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(title, fontsize=8.5, color=INK, pad=3)


# ------------------------------------------------------------------------------------------- example images
def example_images():
    """The five example images as 512 x 512 floats in [0, 1] (created in data/examples/ on first use)."""
    names = ["coffee", "chelsea", "gravel", "brick", "hubble"]
    EXD.mkdir(parents=True, exist_ok=True)
    if not all((EXD / f"{n}.png").exists() for n in names):
        from skimage import data
        from skimage.transform import resize

        def square(img, n=512):
            H, W = img.shape
            s = min(H, W)
            i0, j0 = (H - s) // 2, (W - s) // 2
            return np.clip(resize(img[i0:i0 + s, j0:j0 + s], (n, n), order=3, anti_aliasing=True), 0, 1)

        imgs = {"coffee": square(to_gray(data.coffee())), "chelsea": square(to_gray(data.chelsea())),
                "gravel": to_gray(data.gravel()), "brick": to_gray(data.brick()),
                "hubble": to_gray(data.hubble_deep_field())[100:612, 200:712]}
        for n, im in imgs.items():
            skio.imsave(EXD / f"{n}.png", np.round(np.clip(im, 0, 1) * 255).astype(np.uint8), check_contrast=False)
    return {n: to_gray(skio.imread(EXD / f"{n}.png")) for n in names}


# ------------------------------------------------------------------------------------------------ examples
def example_A(imgs):
    """LED flicker in a rolling-shutter camera: multiplicative bands at a frequency known from sensor timing."""
    x = imgs["coffee"]
    H, W = x.shape
    rng = np.random.default_rng(11)
    u = 0.0185                                    # PWM frequency x line time = cycles per row
    mod = 1 + 0.25 * np.cos(2 * np.pi * u * np.arange(H) + 0.4)[:, None]
    y = x * mod + 0.005 * rng.standard_normal(x.shape)
    eps = 0.02
    L = np.log(np.clip(y, 0, None) + eps)         # multiplicative -> additive
    out = np.exp(scenario_a.notch_lms(L, [(u, 0.0), (2 * u, 0.0)], mu2=1e-5, passes=3)) - eps
    lin = scenario_a.notch_lms(y, [(u, 0.0), (2 * u, 0.0)], mu2=1e-5, passes=3)
    p0, p1, p2 = record("A flicker", "noisy", x, y), record("A flicker", "A, log domain", x, out), \
        record("A flicker", "A, linear", x, lin)
    fig = plt.figure(figsize=(14.5, 3.9))
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 1, 0.22, 1.25], wspace=0.08)
    show_image(fig.add_subplot(gs[0]), x, "clean")
    show_image(fig.add_subplot(gs[1]), y, f"LED flicker bands, {p0:.2f} dB")
    show_image(fig.add_subplot(gs[2]), out, f"A in the log domain, {p1:.2f} dB\n(linear-domain notch: {p2:.2f} dB)")
    ax = fig.add_subplot(gs[4])
    rows = np.arange(H)
    ax.plot(rows, y.mean(axis=1), color=MUTED, lw=1.2, label="corrupted")
    ax.plot(rows, out.mean(axis=1), color=BLUE, lw=1.6, label="after A")
    ax.plot(rows, x.mean(axis=1), color=INK, lw=0.8, label="clean")
    ax.set_xlabel("row")
    ax.set_ylabel("row mean")
    ax.set_title("row-mean profile: the bands are a sinusoid\nin rows, at a frequency the sensor timing gives", fontsize=8.5)
    ax.legend(fontsize=7.5, loc="lower left")
    clean_axes(ax)
    ax.set_box_aspect(0.95)
    fig.suptitle("A  Adaptive notch with a known frequency: LED flicker in a rolling-shutter camera",
                 fontsize=11, color=INK, x=0.42, y=1.04)
    save(fig, "examples", "example_A_flicker.png")


def example_B():
    """Probe microscopy: particles on a substrate, offsets between lines and drift along each fast-scan line."""
    rng = np.random.default_rng(7)
    s = scenario_b.afm_scene(n_obj=90, seed=3)
    H, W = s.shape
    j = np.arange(W)[None, :]
    wander = (0.05 + 0.03 * rng.random((H, 1))) * np.sin(2 * np.pi * 0.8 * j / W + 2 * np.pi * rng.random((H, 1)))
    y = s + 0.05 * rng.standard_normal((H, 1)) + wander + 0.1 * j / W + 0.01 * rng.standard_normal(s.shape)
    rm = y - np.median(y, axis=1, keepdims=True)
    lms, _ = scenario_b.bias_canceller(y, 0.02, "lms")
    gate, track = scenario_b.bias_canceller(y, 0.05, "gated", tau=0.08)
    p = {k: record("B probe microscopy", k, s, v, offset_aligned=True)
         for k, v in [("noisy", y), ("row median", rm), ("B, LMS", lms), ("B, gated", gate)]}
    fig = plt.figure(figsize=(15, 3.9))
    gs = fig.add_gridspec(1, 6, width_ratios=[1, 1, 1, 1, 0.2, 1.35], wspace=0.08)
    disp = lambda a, im, t: show_image(a, im - np.median(im) + 0.3, t, vmin=0.1, vmax=0.75)  # noqa: E731
    disp(fig.add_subplot(gs[0]), y, f"raw scan, {p['noisy']:.1f} dB")
    disp(fig.add_subplot(gs[1]), rm, f"row-median levelling, {p['row median']:.1f} dB")
    disp(fig.add_subplot(gs[2]), lms, f"B, LMS update, {p['B, LMS']:.1f} dB")
    disp(fig.add_subplot(gs[3]), gate, f"B, gated update, {p['B, gated']:.1f} dB")
    ax = fig.add_subplot(gs[5])
    i = 200
    ax.plot(y[i] - np.median(y[i]), color=MUTED, lw=1.0, label="raw line")
    ax.plot(track[i] - np.median(y[i]), color=ORANGE, lw=1.6, label="bias b (gated)")
    ax.plot(gate[i] - np.median(gate[i]), color=BLUE, lw=1.2, label="corrected")
    ax.set_xlabel(f"pixel along line {i}")
    ax.set_title("one fast-scan line: the gated weight follows the\nsubstrate and pauses on the particles", fontsize=8.5)
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(0.0, 1.0), handlelength=1.2)
    clean_axes(ax)
    ax.set_box_aspect(0.95)
    fig.suptitle("B  Bias canceller along the scan: line offsets and thermal drift in a probe-microscopy image "
                 "(PSNR after removing the global offset)", fontsize=11, color=INK, x=0.47, y=1.04)
    save(fig, "examples", "example_B_probe_microscopy.png")


def example_C(imgs):
    """Vibration stripes whose frequency drifts down the image: no fixed reference exists."""
    x = imgs["chelsea"]
    H, W = x.shape
    ii = np.arange(H)[:, None]
    f = 0.08 + 0.04 * ii / H
    y = x + 0.10 * np.cos(2 * np.pi * np.cumsum(np.repeat(f, W, axis=1), axis=1) + 2 * np.pi * 0.013 * ii)
    peaks = scenario_a.adaptive_notch(y, mu2=0.001)[1]
    out, info = scenario_c.subband_canceller(y, alpha=0.005, record=True)
    p0, p1 = record("C drifting stripes", "noisy", x, y), record("C drifting stripes", "C", x, out)

    def rowspec(img):
        z = img - img.mean(axis=1, keepdims=True)
        S = np.abs(np.fft.rfft(z * np.hanning(W), axis=1)) ** 2
        return np.log10(S + 1e-6)

    fig = plt.figure(figsize=(15, 4.0))
    gs = fig.add_gridspec(1, 6, width_ratios=[1, 1, 1, 0.12, 1.0, 1.0], wspace=0.14)
    show_image(fig.add_subplot(gs[0]), y, f"stripes 0.08 -> 0.12 cyc/px, {p0:.2f} dB")
    show_image(fig.add_subplot(gs[1]), out, f"C, two-band canceller, {p1:.2f} dB")
    signed(fig.add_subplot(gs[2]), y - out, "removed component", 0.25)
    for k, (img, t) in enumerate([(y, "per-row spectrum, input"), (out, "per-row spectrum, output")]):
        ax = fig.add_subplot(gs[4 + k])
        S = rowspec(img)
        ax.imshow(S, cmap="gray_r", aspect="auto", extent=[0, 0.5, H, 0], vmin=np.percentile(S, 40), vmax=np.percentile(S, 99.8))
        ax.set_xlim(0, 0.25)
        ax.set_xticks([0, 0.1, 0.2])
        ax.set_xlabel("cycles/pixel along the row")
        if k == 0:
            ax.set_ylabel("row")
        else:
            ax.set_yticklabels([])
        ax.set_title(t, fontsize=8.5)
        ax.tick_params(labelsize=7)
    found = "no peak" if not peaks else f"{len(peaks)} peak{'s' if len(peaks) != 1 else ''}"
    fig.suptitle(f"C  No reference, no fixed frequency: vibration stripes that drift (A's peak detector finds {found})",
                 fontsize=11, color=INK, x=0.47, y=1.04)
    save(fig, "examples", "example_C_drifting_stripes.png")


def example_D(imgs):
    """Dead/hot pixels and bit errors on fine texture: the median smears it, the gated predictor keeps it."""
    x = imgs["gravel"]
    rng = np.random.default_rng(5)
    y = x.copy()
    hit = rng.random(x.shape) < 0.10
    y[hit] = rng.random(int(hit.sum()))
    dead = rng.random(x.shape) < 0.005
    y[dead] = (rng.random(int(dead.sum())) < 0.5).astype(float)
    out, flags = scenario_d.self_tuning_gated(y)
    med = baselines.median3(y)
    amf = baselines.adaptive_median(y)
    p = {k: record("D impulses on texture", k, x, v)
         for k, v in [("noisy", y), ("D, error-gated", out), ("median 3x3", med), ("adaptive median", amf)]}
    c = (slice(150, 310), slice(180, 340))
    fig, axs = plt.subplots(1, 5, figsize=(15, 3.6))
    show_image(axs[0], x[c], "clean (zoom)")
    show_image(axs[1], y[c], f"10 % bit errors + dead/hot pixels\n{p['noisy']:.2f} dB")
    show_image(axs[2], out[c], f"D, error-gated, {p['D, error-gated']:.2f} dB\nSSIM {ssim(x, out):.3f}")
    show_image(axs[3], med[c], f"median 3 x 3, {p['median 3x3']:.2f} dB\nSSIM {ssim(x, med):.3f}")
    m = hit | dead
    viz = np.ones(x.shape + (3,))
    viz[flags & m] = (0.16, 0.47, 0.84)
    viz[flags & ~m] = (0.92, 0.41, 0.20)
    viz[~flags & m] = (0.25, 0.25, 0.25)
    axs[4].imshow(viz[c], interpolation="nearest")
    axs[4].set_xticks([])
    axs[4].set_yticks([])
    for s in axs[4].spines.values():
        s.set_visible(False)
    axs[4].set_title("replaced pixels: blue correct, orange false,\ngrey missed (small deviations)", fontsize=8.5)
    fig.suptitle("D  Error-gated self-tuning filter: only the flagged pixels change, so fine texture survives "
                 f"(adaptive median: {p['adaptive median']:.2f} dB)", fontsize=11, color=INK, y=1.05)
    fig.tight_layout()
    save(fig, "examples", "example_D_impulses_texture.png")


def example_E(imgs):
    """Periodic texture under heavy noise: the line enhancer learns the texture's period."""
    x = imgs["brick"]
    rng = np.random.default_rng(9)
    y = x + 0.12 * rng.standard_normal(x.shape)
    out, info = scenario_e.line_enhancer(y, r=5, hole=0, record=True)
    d2 = scenario_d.self_tuning(y)
    wie = baselines.local_wiener(y)
    med = baselines.median3(y)
    p = {k: record("E periodic texture", k, x, v)
         for k, v in [("noisy", y), ("E, 11x11", out), ("D, 5x5", d2), ("Wiener 5x5", wie), ("median 3x3", med)]}
    lat = scenario_e.lattice((192, 192), LATTICE)                 # the synthetic lattice of fig_E_image.png
    nl = lat + 0.2 * np.random.default_rng(31).standard_normal(lat.shape)
    record("E lattice", "noisy", lat, nl)
    record("E lattice", "E, 9x9", lat, scenario_d.blindspot_lms(nl, r=4, mu2=1e-4, passes=3))
    c = (slice(160, 352), slice(160, 352))
    fig = plt.figure(figsize=(15, 3.8))
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 1, 1, 1.0], wspace=0.08)
    show_image(fig.add_subplot(gs[0]), y[c], f"brick texture + noise, {p['noisy']:.2f} dB")
    show_image(fig.add_subplot(gs[1]), out[c], f"E, 11 x 11 window, {p['E, 11x11']:.2f} dB")
    show_image(fig.add_subplot(gs[2]), wie[c], f"Wiener 5 x 5, {p['Wiener 5x5']:.2f} dB")
    show_image(fig.add_subplot(gs[3]), med[c], f"median 3 x 3, {p['median 3x3']:.2f} dB")
    ax = fig.add_subplot(gs[4])
    k = info["weights"]
    lim = np.abs(k).max()
    ax.imshow(k, cmap=DIV, vmin=-lim, vmax=lim)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("learned 11 x 11 weights: they line up\nwith the mortar joints", fontsize=8.5)
    fig.suptitle(f"E  Line enhancer on a periodic texture: the prediction keeps the pattern and drops the noise "
                 f"(D with 5 x 5: {p['D, 5x5']:.2f} dB)", fontsize=11, color=INK, y=1.05)
    save(fig, "examples", "example_E_periodic_texture.png")


def example_F(imgs):
    """Astronomical frame from a CMOS camera: row banding and readout telegraph noise, with references."""
    x = imgs["hubble"]
    H, W = x.shape
    rng = np.random.default_rng(3)

    def telegraph():
        return 0.03 * (2.0 * noise.two_state_chain(H * W, 1 / 60, 1 / 60, rng) - 1.0).reshape(H, W)

    c, t = 0.03 * rng.standard_normal(H), telegraph()
    y = x + c[:, None] + t + 0.01 * rng.standard_normal(x.shape)
    ob = c[:, None] + 0.01 * rng.standard_normal((H, 16))
    ref = 0.8 * t + 0.01 * rng.standard_normal(x.shape)
    cd, td = 0.03 * rng.standard_normal(H), telegraph()
    dark = cd[:, None] + td + 0.01 * rng.standard_normal(x.shape)
    dark_ob = cd[:, None] + 0.01 * rng.standard_normal((H, 16))
    dark_ref = 0.8 * td + 0.01 * rng.standard_normal(x.shape)
    w = scenario_f.train_row_weight(dark, dark_ob)
    y1 = scenario_f.row_reference_canceller(y, ob, w)
    y2, _ = scenario_f.channel_reference_canceller(y1, ref, train=(dark, dark_ref))
    bs, _ = scenario_b.bias_canceller(y, 0.002, "sign")
    bs = bs + np.median(x)
    p = {k: record("F astronomy", k, x, v)
         for k, v in [("noisy", y), ("F, optical-black only", y1), ("F, both references", y2),
                      ("B, sign-error", bs), ("median 3x3", baselines.median3(y))]}
    c0 = (slice(250, 442), slice(40, 232))
    st = lambda a: np.arcsinh(np.clip(a, 0, None) / 0.03) / np.arcsinh(1 / 0.03)    # noqa: E731
    fig, axs = plt.subplots(1, 5, figsize=(15, 3.6))
    show_image(axs[0], st(x[c0]), "clean (asinh stretch)")
    show_image(axs[1], st(y[c0]), f"banding + readout telegraph\n{p['noisy']:.2f} dB")
    show_image(axs[2], st(y1[c0]), f"F, optical-black reference\n{p['F, optical-black only']:.2f} dB")
    show_image(axs[3], st(y2[c0]), f"F, + reference output\n{p['F, both references']:.2f} dB")
    show_image(axs[4], st(bs[c0]), f"B without references (sign-error)\n{p['B, sign-error']:.2f} dB")
    fig.suptitle("F  Reference-sensor canceller on a faint astronomical field: the references reveal what the "
                 "streaks hid", fontsize=11, color=INK, y=1.05)
    fig.tight_layout()
    save(fig, "examples", "example_F_astronomy.png")


# ------------------------------------------------------------------------------------- D: density limit
def density_sweep():
    """Error-gated D against impulse density, for two gate thresholds k (camera image, random-valued impulses)."""
    x, _ = load_test_image()
    dens = [0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    cols = ["noisy", "D gated, k = 4", "D gated, k = 3", "median 3 x 3", "adaptive median"]
    res = {c: [] for c in cols}
    for dd in dens:
        y = noise.make("impulse", x, density=dd).y
        res["noisy"].append(psnr(x, y))
        res["D gated, k = 4"].append(psnr(x, scenario_d.self_tuning_gated(y, k=4.0)[0]))
        res["D gated, k = 3"].append(psnr(x, scenario_d.self_tuning_gated(y, k=3.0)[0]))
        res["median 3 x 3"].append(psnr(x, baselines.median3(y)))
        res["adaptive median"].append(psnr(x, baselines.adaptive_median(y)))
        print(f"  density {dd:.2f}: " + ", ".join(f"{c} {res[c][-1]:.2f}" for c in cols), flush=True)
    with open(REPO / "results" / "gated_density_sweep.csv", "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["density"] + cols)
        for k, dd in enumerate(dens):
            wr.writerow([f"{dd:.2f}"] + [f"{res[c][k]:.4f}" for c in cols])
    print("  wrote results/gated_density_sweep.csv")
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    pct = 100 * np.array(dens)
    style = {"D gated, k = 4": (BLUE, "o", "-"), "D gated, k = 3": (ORANGE, "o", "-"),
             "median 3 x 3": (AQUA, "s", "-"), "adaptive median": (VIOLET, "s", "-"), "noisy": (MUTED, None, "--")}
    for c in cols:
        col, mk, ls = style[c]
        ax.plot(pct, res[c], color=col, lw=2, ls=ls, marker=mk, ms=6, mec="white", mew=1.2, label=c)
    ax.set_xlim(0, 32)
    ax.set_ylim(10, 35.5)
    ax.set_xticks(pct)
    ax.set_xlabel("random-valued impulses (% of pixels)")
    ax.set_ylabel("PSNR (dB)")
    ax.annotate("k = 4 at 30 %: the robust error scale grows with the impulse density,\n"
                "the threshold k s rises above the impulses, and the gate stops flagging",
                xy=(29.6, res["D gated, k = 4"][-1] - 0.3), xytext=(4.0, 11.0), fontsize=8, color=INK2,
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.9))
    ax.legend(fontsize=8, loc="upper right", frameon=False)
    clean_axes(ax)
    ax.set_title("D, error-gated, against impulse density: k = 4 is best up to 10 %, k = 3 holds to 25 %",
                 fontsize=10, color=INK, loc="left")
    save(fig, "examples", "example_D_density.png")


# ---------------------------------------------------------------------------------------------------- hero
def fig_hero():
    """Six corruptions, six cancellers: input, what the canceller removed, output."""
    x, _ = load_test_image()
    cache = REPO / "results" / "cache"

    def get(key, m):
        p = cache / f"{key}__{m}.npy"
        if p.exists():
            return np.load(p).astype(float)
        nz = noise.make(key, x)
        if m == "noisy":
            return nz.y
        from adaptive_denoise.pipeline import apply_scenario
        return apply_scenario(m, nz)

    crop = (slice(80, 272), slice(160, 352))
    cols = [("A", "periodic", "A  adaptive notch", "periodic interference"),
            ("B", "banding", "B  bias canceller", "row banding, no reference"),
            ("C", "periodic", "C  no-reference canceller", "periodic, frequency unknown"),
            ("Dg", "impulse", "D  self-tuning (gated)", "random-valued impulses"),
            ("E", "lattice", "E  line enhancer", "periodic texture in noise"),
            ("F", "telegraph_readout", "F  reference canceller", "readout telegraph noise")]
    fig, axs = plt.subplots(3, 6, figsize=(15.5, 8.4))
    for k, (m, key, title, sub) in enumerate(cols):
        if key == "lattice":
            ref = scenario_e.lattice((192, 192), LATTICE)
            yin = ref + 0.2 * np.random.default_rng(31).standard_normal(ref.shape)
            yout = scenario_d.blindspot_lms(yin, r=4, mu2=1e-4, passes=3)
            a_in, a_out = yin[:150, :150], yout[:150, :150]
        else:
            ref = x
            yin, yout = get(key, "noisy"), get(key, m)
            a_in, a_out = yin[crop], yout[crop]
        rem = a_in - a_out
        show_image(axs[0, k], a_in, f"{title}\n{sub}\n{psnr(ref, yin):.1f} dB")
        signed(axs[1, k], rem, "what it removed", 0.3 if m != "Dg" else 0.6)
        show_image(axs[2, k], a_out, f"output, {psnr(ref, yout):.1f} dB  ({psnr(ref, yout) - psnr(ref, yin):+.1f})")
        axs[0, k].title.set_fontsize(9)
    for r, lab in enumerate(["input", "removed", "output"]):
        axs[r, 0].text(-0.08, 0.5, lab, transform=axs[r, 0].transAxes, rotation=90, ha="center", va="center",
                       fontsize=10, color=INK2)
    fig.subplots_adjust(left=0.03, right=0.995, top=0.88, bottom=0.01, wspace=0.05, hspace=0.18)
    fig.suptitle("Six corruptions, six adaptive cancellers: the configuration decides what gets removed",
                 fontsize=13, color=INK, y=0.985)
    save(fig, "overview", "fig_hero.png", dpi=130)


# ------------------------------------------------------------------------------------------------- 1-D view
def fig_1d():
    """Each scenario first on a 1-D signal, the way the canceller was born."""
    rng = np.random.default_rng(2)
    n = 3000
    t = np.arange(n)
    fig = plt.figure(figsize=(14, 15.5))
    gs = fig.add_gridspec(6, 2, width_ratios=[2.6, 1], hspace=0.62, wspace=0.18, top=0.86)

    def tplot(ax, series, title, xl=(0, n)):
        for y, col, lw, lab in series:
            ax.plot(t[xl[0]:xl[1]], y[xl[0]:xl[1]], color=col, lw=lw, label=lab)
        ax.set_title(title, fontsize=9.5, loc="left")
        ax.legend(fontsize=7.5, loc="upper right", ncol=len(series))
        clean_axes(ax)

    # A: pulse train (ECG-like) + mains hum; quadrature reference
    s = np.zeros(n)
    for c in range(100, n, 330):
        s += 1.0 * np.exp(-0.5 * ((t - c) / 6.0) ** 2) - 0.25 * np.exp(-0.5 * ((t - c - 30) / 18.0) ** 2)
    w0 = 2 * np.pi * 0.02
    d = s + 0.6 * np.cos(w0 * t + 1.0) + 0.03 * rng.standard_normal(n)
    w = np.zeros(2)
    e = np.zeros(n)
    W = np.zeros((n, 2))
    for k in range(n):
        x = np.array([np.cos(w0 * k), np.sin(w0 * k)])
        e[k] = d[k] - w @ x
        w += 0.01 * e[k] * x
        W[k] = w
    tplot(fig.add_subplot(gs[0, 0]), [(d, MUTED, 0.9, "primary: pulses + hum"), (e, BLUE, 1.3, "output e"),
                                      (s, INK, 0.7, "clean")], "A  adaptive notch: a synthetic cos/sin reference at the hum frequency")
    ax = fig.add_subplot(gs[0, 1])
    ax.plot(t, W[:, 0], color=BLUE, lw=1.4, label="$w_{cos}$")
    ax.plot(t, W[:, 1], color=ORANGE, lw=1.4, label="$w_{sin}$")
    ax.axhline(0.6 * np.cos(1.0), color=MUTED, lw=0.8)
    ax.axhline(-0.6 * np.sin(1.0), color=MUTED, lw=0.8)
    ax.set_title("the two weights converge to the hum's\namplitude and phase (grey lines)", fontsize=9)
    ax.legend(fontsize=7.5)
    clean_axes(ax)

    # B: drifting baseline; constant reference
    s = np.zeros(n)
    for c in range(150, n, 400):
        s += 0.8 * np.exp(-0.5 * ((t - c) / 10.0) ** 2)
    drift = 0.5 * (1 - np.exp(-t / 900.0)) + 0.2 * np.sin(2 * np.pi * t / 2500)
    d = s + drift + 0.02 * rng.standard_normal(n)
    b = 0.0
    e = np.zeros(n)
    bt = np.zeros(n)
    for k in range(n):
        e[k] = d[k] - b
        bt[k] = b
        if abs(e[k]) < 0.15:
            b += 0.02 * e[k]
    tplot(fig.add_subplot(gs[1, 0]), [(d, MUTED, 0.9, "primary: peaks + drift"), (e, BLUE, 1.3, "output e"),
                                      (bt, ORANGE, 1.4, "bias weight b")], "B  bias canceller: the reference is the constant 1 (gated update)")
    ax = fig.add_subplot(gs[1, 1])
    om = 2 * np.pi * np.logspace(-4, np.log10(0.5), 400)
    for col, m in zip([BLUE, ORANGE, AQUA], [0.005, 0.02, 0.1]):
        ax.semilogx(om / (2 * np.pi), 20 * np.log10(np.abs(scenario_b.bias_response_theory(m, om))), color=col,
                    lw=1.5, label=f"$\\mu_2$ = {m}")
    ax.set_ylim(-40, 3)
    ax.set_title("a first-order high-pass with a zero at DC", fontsize=9)
    ax.set_ylabel("|H| (dB)")
    ax.legend(fontsize=7.5, loc="lower right")
    clean_axes(ax)

    # C: broadband signal + unknown sinusoid; delayed reference
    s = np.convolve(rng.standard_normal(n), np.ones(3) / 3, mode="same") * 0.5
    d = s + 0.5 * np.sin(2 * np.pi * 0.0731 * t + 0.4)
    L, delay = 32, 8
    w = np.zeros(L)
    e = np.zeros(n)
    mu = 0.002
    for k in range(delay + L, n):
        x = d[k - delay - L + 1:k - delay + 1][::-1]
        y = w @ x
        e[k] = d[k] - y
        w += mu * e[k] * x
    tplot(fig.add_subplot(gs[2, 0]), [(d, MUTED, 0.9, "primary: broadband + sinusoid"), (e, BLUE, 1.0, "output e"),
                                      (s, INK, 0.6, "clean")], "C  no reference: the primary delayed by $\\Delta$ = 8 is the reference",
          xl=(2200, 2600))
    ax = fig.add_subplot(gs[2, 1])
    fr, Hf = scenario_c.predictor_response(w, delay)
    ax.plot(fr, np.abs(Hf), color=BLUE, lw=1.4)
    ax.axvline(0.0731, color=ORANGE, lw=1.0)
    ax.set_xlim(0, 0.5)
    ax.set_title("learned predictor: a band-pass on the\nunknown frequency (orange)", fontsize=9)
    ax.set_xlabel("cycles/sample")
    clean_axes(ax)

    # D: sinusoid buried in white noise; self-tuning filter output
    s = np.sqrt(2 * 0.25) * np.sin(2 * np.pi * 0.05 * t)
    d = s + rng.standard_normal(n)
    y, e, w, _ = scenario_e.ale_lms(d, 32, 1, 0.05 / (32 * np.var(d)))
    tplot(fig.add_subplot(gs[3, 0]), [(d, MUTED, 0.7, "primary: sine + white noise (SNR 0.25)"), (y, BLUE, 1.4, "filter output y"),
                                      (s, INK, 0.8, "clean")], "D  self-tuning filter: keep the filter output, the predictable part",
          xl=(2400, 2800))
    ax = fig.add_subplot(gs[3, 1])
    om = np.linspace(0, np.pi, 1000)
    ax.plot(om / (2 * np.pi), np.abs(scenario_e.ale_response(w, 1, om)), color=BLUE, lw=1.4, label="LMS, L = 32")
    ax.plot(om / (2 * np.pi), np.abs(scenario_e.ale_response(scenario_e.ale_wiener_weights(32, 1, 0.25, 2 * np.pi * 0.05), 1, om)),
            color=MUTED, lw=1.0, label="Wiener")
    ax.axhline(scenario_e.ale_peak_gain(32, 0.25), color=ORANGE, lw=0.8)
    ax.set_title("it tuned itself to the line; peak gain\n(L/2)SNR/((L/2)SNR+1) = 0.8 (orange)", fontsize=9)
    ax.set_xlabel("cycles/sample")
    ax.legend(fontsize=7.5)
    clean_axes(ax)

    # E: chirp in noise; the ALE tracks a moving line
    f_inst = 0.03 + 0.12 * t / n
    s = np.sqrt(2 * 0.5) * np.sin(2 * np.pi * np.cumsum(f_inst))
    d = s + rng.standard_normal(n)
    y, e, w, _ = scenario_e.ale_lms(d, 48, 1, 0.3 / (48 * np.var(d)))
    ax = fig.add_subplot(gs[4, 0])
    ax.specgram(y, NFFT=128, Fs=1.0, noverlap=96, cmap="gray_r")
    ax.plot(t, f_inst, color=ORANGE, lw=0.8)
    ax.set_ylim(0, 0.25)
    ax.set_ylabel("cycles/sample")
    ax.set_title("E  line enhancer on a chirp in noise (SNR 0.5): the output spectrogram follows the moving line "
                 "(orange: true frequency)", fontsize=9.5, loc="left")
    clean_axes(ax, grid_y=False)
    ax = fig.add_subplot(gs[4, 1])
    ax.specgram(d, NFFT=128, Fs=1.0, noverlap=96, cmap="gray_r")
    ax.set_ylim(0, 0.25)
    ax.set_title("input spectrogram: the line is buried", fontsize=9)
    clean_axes(ax, grid_y=False)

    # F: reference sensor
    s = 0.6 * np.sin(2 * np.pi * 0.004 * t) * np.exp(-((t - 1500) / 900.0) ** 2)
    n0 = rng.standard_normal(n)
    n_prim = np.convolve(n0, [0.7, 0.4, -0.2], mode="full")[:n]
    d = s + n_prim + 0.02 * rng.standard_normal(n)
    xr = n0 + 0.05 * rng.standard_normal(n)
    L = 4
    w = np.zeros(L)
    e = np.zeros(n)
    W = np.zeros((n, L))
    for k in range(L, n):
        x = xr[k - L + 1:k + 1][::-1]
        e[k] = d[k] - w @ x
        w += 0.005 * e[k] * x
        W[k] = w
    tplot(fig.add_subplot(gs[5, 0]), [(d, MUTED, 0.6, "primary: signal + filtered noise"), (e, BLUE, 1.4, "output e"),
                                      (s, INK, 0.9, "clean")], "F  reference sensor: the reference sees the noise source, not the signal")
    ax = fig.add_subplot(gs[5, 1])
    for k, col in enumerate([BLUE, ORANGE, AQUA, VIOLET]):
        ax.plot(t, W[:, k], color=col, lw=1.3, label=f"$w_{k}$")
    for v in [0.7, 0.4, -0.2, 0.0]:
        ax.axhline(v, color=MUTED, lw=0.7)
    ax.set_title("the weights identify the noise path\n[0.7, 0.4, -0.2, 0] (grey lines)", fontsize=9)
    ax.legend(fontsize=7.5, ncol=4, loc="lower right")
    clean_axes(ax)
    fig.suptitle("The six configurations on 1-D signals: same LMS loop, different reference, different output kept",
                 fontsize=12.5, color=INK, y=0.91)
    save(fig, "overview", "fig_1d_intuition.png", dpi=130)


# ------------------------------------------------------------------------------------------------ animations
def frames_to_gif(frames, path, durations):
    imgs = [Image.open(io.BytesIO(f)).convert("RGB") for f in frames]
    q = [im.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for im in imgs]
    path.parent.mkdir(parents=True, exist_ok=True)
    q[0].save(path, save_all=True, append_images=q[1:], duration=durations, loop=0, optimize=True)
    print(f"  wrote figures/animations/{path.name} ({path.stat().st_size // 1024} KB)", flush=True)


def fig_to_png(fig, dpi=90):
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=dpi)
    plt.close(fig)
    return b.getvalue()


def gif_notch():
    """Scenario A in raster order: the stripes vanish as soon as the six weights lock."""
    x, _ = load_test_image()
    nz = noise.make("periodic", x)
    freqs = [(u, v) for u, v, _ in __import__("adaptive_denoise.spectral", fromlist=["x"]).detect_peaks(nz.y)]
    y = nz.y[:256, 128:384]
    H, W = y.shape
    m = float(y.mean())
    z = y - m
    refs = scenario_a.plane_wave_refs((512, 512), freqs)[:256, 128:384]
    mu2 = 3e-4
    w = np.zeros(2 * len(freqs))
    out = y.copy()
    hist = []
    snaps = {0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 160, 192, 224, 255}
    frames = []
    for i in range(H):
        for j in range(W):
            xv = refs[i, j]
            e = z[i, j] - w @ xv
            w += (mu2 * e) * xv
            out[i, j] = e + m
        hist.append(w.copy())
        if i in snaps:
            fig, axs = plt.subplots(1, 2, figsize=(8.4, 3.9), gridspec_kw=dict(width_ratios=[1, 1.15]))
            show_image(axs[0], out, f"output while scanning: row {i + 1} of {H}")
            axs[0].axhline(i, color=ORANGE, lw=1.2)
            hh = np.array(hist)
            for k in range(hh.shape[1]):
                axs[1].plot(np.arange(len(hh)), hh[:, k], lw=1.4, color=[BLUE, ORANGE, AQUA, "#eda100", "#e87ba4", VIOLET][k % 6])
            axs[1].set_xlim(0, H)
            axs[1].set_ylim(-0.12, 0.12)
            axs[1].set_xlabel("row")
            axs[1].set_title("the six weights (cos/sin for 3 frequencies)", fontsize=9)
            clean_axes(axs[1])
            fig.suptitle("A  adaptive notch learning in raster order (first pass, weights start at zero)", fontsize=10.5,
                         color=INK)
            fig.tight_layout()
            frames.append(fig_to_png(fig))
    frames_to_gif(frames, FIG / "animations" / "A_notch_learning.gif", [350] * (len(frames) - 1) + [2500])


def gif_line_enhancer():
    """Scenario E: a noisy lattice; the prediction sharpens as the 9 x 9 weights learn the period."""
    H = 160
    lat = scenario_e.lattice((H, H), LATTICE)
    y = lat + 0.2 * np.random.default_rng(31).standard_normal(lat.shape)
    r = 4
    m = float(y.mean())
    z = y - m
    mask = tap_mask(r, 0)
    mflat = mask.ravel()
    nt = int(mflat.sum())
    mu2 = 2e-4
    w = np.zeros(nt)
    pad = np.pad(z, r, mode="reflect")
    out = np.full(y.shape, m)
    frames = []
    snaps = [(0, k) for k in (1, 3, 6, 10, 16, 24, 40, 64, 96, 128, 159)] + [(1, 159), (2, 159)]
    for p in range(3):
        for i in range(H):
            X = _row_taps(pad, i, r, H, mflat)
            for j in range(H):
                xv = X[j]
                yj = w @ xv
                w += (mu2 * (z[i, j] - yj)) * xv
                out[i, j] = yj + m
            if (p, i) in snaps:
                fig, axs = plt.subplots(1, 3, figsize=(9.6, 3.5), gridspec_kw=dict(width_ratios=[1, 1, 0.9]))
                show_image(axs[0], y, f"noisy lattice, {psnr(lat, y):.1f} dB")
                show_image(axs[1], out, f"prediction, pass {p + 1}, row {i + 1}: {psnr(lat, out):.1f} dB")
                if p == 0:
                    axs[1].axhline(i, color=ORANGE, lw=1.0)
                kern = np.zeros(mask.shape)
                kern[mask] = w
                lim = max(np.abs(kern).max(), 1e-6)
                axs[2].imshow(kern, cmap=DIV, vmin=-lim, vmax=lim)
                axs[2].set_xticks([])
                axs[2].set_yticks([])
                axs[2].set_title("9 x 9 weights (centre excluded)", fontsize=9)
                fig.suptitle("E  line enhancer learning a periodic texture in raster order", fontsize=10.5, color=INK)
                fig.tight_layout()
                frames.append(fig_to_png(fig))
    frames_to_gif(frames, FIG / "animations" / "E_line_enhancer_learning.gif",
                  [400] * (len(frames) - 1) + [2500])


def write_rows():
    path = REPO / "results" / "examples_python.csv"
    with open(path, "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["example", "method", "psnr", "ssim"])
        for e, m, p, s in ROWS:
            wr.writerow([e, m, f"{p:.4f}", f"{s:.4f}"])
    print("  wrote results/examples_python.csv")


if __name__ == "__main__":
    setup()
    what = set(sys.argv[1:]) or {"examples", "density", "hero", "oned", "gifs"}
    t0 = time.time()
    if "examples" in what:
        imgs = example_images()
        example_A(imgs)
        example_B()
        example_C(imgs)
        example_D(imgs)
        example_E(imgs)
        example_F(imgs)
        write_rows()
    if "density" in what:
        density_sweep()
    if "hero" in what:
        fig_hero()
    if "oned" in what:
        fig_1d()
    if "gifs" in what:
        gif_notch()
        gif_line_enhancer()
    print(f"done in {time.time() - t0:.0f} s")
