"""Block diagrams of the canceller principle and of the six scenarios.

    python make_diagrams.py                   # writes figures/diagrams/*.png
    python make_diagrams.py decision_guide    # only the named diagrams
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adaptive_denoise.plotstyle import (Diagram, setup, INK, INK2, MUTED, BLUE, ORANGE, AQUA, RED, NEUTRAL,   # noqa: E402
                                        BLUE_LIGHT, ORANGE_LIGHT, AQUA_LIGHT, GRID)
from adaptive_denoise.imageio import REPO                                                                    # noqa: E402

OUT = REPO / "figures" / "diagrams"


def principle():
    D = Diagram(9.2, 3.9, "Adaptive noise canceller")
    D.block(0.95, 3.0, 1.2, 0.5, "signal\nsource", fill=BLUE_LIGHT)
    D.block(0.95, 1.35, 1.2, 0.5, "noise\nsource", fill=ORANGE_LIGHT)
    s1 = D.sum(3.25, 3.0, signs=dict(l="+", b="+"))
    D.wire([(1.55, 3.0), s1["l"]], color=BLUE)
    D.text(2.4, 3.17, "$s$", fs=10)
    D.block(3.25, 2.08, 1.05, 0.42, "channel $H$", fill="white", fs=8.5)
    D.wire([(1.55, 1.35), (2.0, 1.35), (2.0, 2.08), (2.72, 2.08)], color=ORANGE)
    D.dot(2.0, 1.35, ORANGE)
    D.wire([(3.25, 2.29), s1["b"]], color=ORANGE)
    D.text(3.55, 2.55, "$n$", fs=10)
    s2 = D.sum(6.65, 3.0, signs=dict(l="+", b="\u2212"))
    D.wire([s1["r"], s2["l"]], color=INK)
    D.text(4.95, 3.2, "primary input   $d = s + n$", fs=9)
    f = D.adaptive(4.95, 1.35, 1.6, 0.62, "adaptive filter\n$W(z)$")
    D.wire([(2.0, 1.35), f["l"]], color=ORANGE)
    D.text(3.0, 1.12, "reference input  $x$", fs=9)
    D.wire([f["r"], (6.65, 1.35), s2["b"]], color=INK)
    D.text(6.95, 1.95, r"$y = \hat n$", fs=9.5)
    D.wire([s2["r"], (8.95, 3.0)], color=INK)
    D.text(7.9, 3.22, r"$e = d - y = \hat s$", fs=9.5)
    D.text(7.9, 2.72, "system output", fs=8, color=INK2)
    D.dot(7.45, 3.0)
    D.wire([(7.45, 3.0), (7.45, 0.55), (4.95, 0.55), (4.95, 1.04)], color=RED, lw=1.1)
    D.note(5.1, 0.82, "LMS:  $w \\leftarrow w + \\mu_2\\, e\\, x$", fs=8.5, color=INK)
    D.note(0.25, 0.62, "$s$ is uncorrelated with $x$, so  $E[e^2] = E[s^2] + E[(n-\\hat n)^2]$:\n"
           "minimising the output power minimises the noise error.  $W \\to W_{opt} = S_{xd}/S_{xx}$.",
           fs=8, color=INK2)
    D.save(OUT / "diagram_principle.png")


def raster_icon(D, x0, y0, s=0.16, n=6, label=True):
    for i in range(n):
        for j in range(n):
            D.rect(x0 + j * s, y0 - i * s, s * 0.9, s * 0.9, fc=NEUTRAL, ec=GRID, lw=0.5)
    for i in range(n):
        y = y0 - i * s + s * 0.45
        D.wire([(x0 + 0.02, y), (x0 + n * s - 0.05, y)], color=BLUE, lw=0.9)
        if i < n - 1:
            D.ax.plot([x0 + n * s - 0.05, x0 + 0.02], [y, y - s], color=MUTED, lw=0.6, ls=(0, (2, 2)))
    if label:
        D.note(x0 - 0.05, y0 - n * s + 0.02, "raster order: row by row,\nweights carried across rows", fs=7.5)


def scenario_a():
    D = Diagram(9.6, 4.1, "A  Adaptive notch filter (synthetic sinusoidal reference)")
    D.text(0.25, 3.25, "primary  $d(i,j) = s + \\sum_k A_k \\cos(\\theta_k + \\phi_k)$", fs=9, ha="left")
    s = D.sum(7.6, 3.25, signs=dict(l="+", b="\u2212"))
    D.wire([(2.62, 3.25), s["l"]], color=BLUE)
    D.wire([s["r"], (9.35, 3.25)], color=INK)
    D.text(8.5, 3.46, "$e$ = output", fs=9)
    D.block(1.45, 1.85, 2.2, 0.95, "reference generator\n$\\theta_k = 2\\pi(u_k i + v_k j)$\nfor each frequency $k$",
            fill=ORANGE_LIGHT, fs=8.3)
    m1 = D.block(4.25, 2.3, 0.75, 0.42, "$\\times\\, w_{2k}$", fill="white")
    m2 = D.block(4.25, 1.4, 0.75, 0.42, "$\\times\\, w_{2k+1}$", fill="white")
    D.wire([(2.55, 2.3), m1["l"]], color=ORANGE)
    D.wire([(2.55, 1.4), m2["l"]], color=ORANGE)
    D.text(3.15, 2.5, "$C\\cos\\theta_k$", fs=8.5)
    D.text(3.15, 1.6, "$C\\sin\\theta_k$", fs=8.5)
    sy = D.sum(5.6, 1.85, signs=dict(t="+", b="+"))
    D.wire([m1["r"], (5.6, 2.3), sy["t"]], color=INK)
    D.wire([m2["r"], (5.6, 1.4), sy["b"]], color=INK)
    D.wire([sy["r"], (7.6, 1.85), s["b"]], color=INK)
    D.text(6.6, 2.05, "$y$ = interference estimate", fs=8.5)
    D.dot(8.95, 3.25)
    D.wire([(8.95, 3.25), (8.95, 0.75), (4.25, 0.75), (4.25, 1.19)], color=RED, lw=1.1)
    D.note(4.45, 1.03, "LMS:  $w \\leftarrow w + \\mu_2\\, e\\, [C\\cos\\theta_k,\\ C\\sin\\theta_k]$", fs=8.3, color=INK)
    D.note(0.25, 0.95, "frequencies $(u_k, v_k)$: known from system timing,\nor detected as sharp peaks of the 2-D spectrum",
           fs=8, color=INK2)
    D.note(6.0, 0.55, "notch width $\\approx \\mu_2 C^2$ rad/sample;  null depth: infinite", fs=8, color=INK2)
    raster_icon(D, 8.05, 2.55, s=0.13, n=5, label=False)
    D.note(7.95, 1.85, "raster scan", fs=7.5)
    D.save(OUT / "diagram_A_notch.png")


def scenario_b():
    D = Diagram(9.8, 4.4, "B  Bias (drift) canceller: one weight on a constant reference")
    D.note(0.25, 3.85, "textbook form, along a scan line", fs=8.5, color=INK2)
    s = D.sum(3.6, 3.15, signs=dict(l="+", b="\u2212"))
    D.wire([(0.3, 3.15), s["l"]], color=BLUE)
    D.text(1.4, 3.35, "$d(j)$ = pixel of the line", fs=8.5)
    D.wire([s["r"], (4.55, 3.15)], color=INK)
    D.text(4.25, 3.35, "$e$", fs=9.5)
    D.text(0.55, 2.2, "1", fs=10, color=ORANGE)
    b = D.block(2.1, 2.2, 0.7, 0.4, "$\\times\\, b$", fill="white")
    D.wire([(0.7, 2.2), b["l"]], color=ORANGE)
    D.wire([b["r"], (3.6, 2.2), s["b"]], color=INK)
    D.text(3.1, 2.4, "$y = b$", fs=8.5)
    D.dot(4.2, 3.15)
    D.wire([(4.2, 3.15), (4.2, 1.55), (2.1, 1.55), (2.1, 2.0)], color=RED, lw=1.1)
    D.note(0.3, 1.35, "$b \\leftarrow b + \\mu_2 e$  (LMS)\n$b \\leftarrow b + \\mu_2\\,\\mathrm{sgn}(e)$  (median)\n"
           "update only if $|e|<\\tau$  (gated)", fs=8, color=INK)
    D.note(0.3, 0.55, "$H(z) = (z-1)/(z-(1-\\mu_2))$: a high-pass.\nIt flattens slow scene brightness too.", fs=8, color=INK2)
    D.ax.plot([4.9, 4.9], [0.3, 3.9], color=GRID, lw=1.0)
    D.note(5.15, 3.85, "image form for row banding: line to line", fs=8.5, color=INK2)
    s2 = D.sum(8.45, 3.15, signs=dict(l="+", b="\u2212"))
    D.wire([(5.2, 3.15), s2["l"]], color=BLUE)
    D.text(6.3, 3.35, "row $i$ of the image", fs=8.5)
    dl = D.block(6.1, 2.35, 1.15, 0.45, "previous\ncorrected row", fill="white", fs=7.8)
    sb = D.sum(7.45, 2.35, signs=dict(l="+", b="+"))
    D.wire([dl["r"], sb["l"]], color=INK)
    D.text(6.1, 1.62, "1", fs=10, color=ORANGE)
    bb = D.block(6.75, 1.62, 0.6, 0.36, "$\\times\\, b_i$", fill="white", fs=8.5)
    D.wire([(6.25, 1.62), bb["l"]], color=ORANGE)
    D.wire([bb["r"], (7.45, 1.62), sb["b"]], color=INK)
    D.wire([sb["r"], (8.45, 2.35), s2["b"]], color=INK)
    D.wire([s2["r"], (9.6, 3.15)], color=INK)
    D.text(9.2, 3.35, "$e$", fs=9.5)
    D.dot(9.25, 3.15)
    D.wire([(9.25, 3.15), (9.25, 1.15), (6.75, 1.15), (6.75, 1.44)], color=RED, lw=1.1)
    D.note(5.15, 0.95, "$b_i \\leftarrow b_i + \\mu_2\\,\\mathrm{sgn}(e)$ along the row: $b_i \\to$ median of the\n"
           "line-to-line difference.  Corrected row = row $i - b_i$.\n"
           "The slow part of the sequence $b_i$ is put back (a high-pass\nacross rows), so slow scene shading survives.",
           fs=8, color=INK)
    D.save(OUT / "diagram_B_bias.png")


def scenario_c():
    D = Diagram(9.8, 4.0, "C  Periodic interference without a reference (delayed primary, error output)")
    D.text(0.3, 3.1, "row $d$", fs=9, ha="left")
    D.dot(1.05, 3.1)
    lp = D.block(2.55, 3.1, 1.6, 0.48, "low band\nGaussian, $\\sigma$ = 4 px", fill="white", fs=8)
    D.wire([(0.85, 3.1), lp["l"]], color=BLUE)
    so = D.sum(8.7, 3.1, signs=dict(l="+", b="+"))
    D.wire([lp["r"], so["l"]], color=INK)
    D.wire([so["r"], (9.65, 3.1)], color=INK)
    D.text(9.3, 3.32, "output", fs=8.5)
    sh = D.sum(2.55, 2.05, signs=dict(l="+", t="\u2212"))
    D.wire([(1.05, 3.1), (1.05, 2.05), sh["l"]], color=BLUE)
    D.wire([(2.55, 2.86), sh["t"]], color=INK)
    D.text(3.45, 2.25, "high band $h$", fs=8.5)
    se = D.sum(7.3, 2.05, signs=dict(l="+", b="\u2212"))
    D.wire([sh["r"], se["l"]], color=INK)
    D.dot(3.3, 2.05)
    dl = D.block(4.0, 1.05, 0.75, 0.42, "$z^{-\\Delta}$", fill=ORANGE_LIGHT)
    D.wire([(3.3, 2.05), (3.3, 1.05), dl["l"]], color=ORANGE)
    f = D.adaptive(5.55, 1.05, 1.55, 0.55, "$W(z)$, $L$ taps", fs=8.5)
    D.wire([dl["r"], f["l"]], color=ORANGE)
    D.wire([f["r"], (7.3, 1.05), se["b"]], color=INK)
    D.text(6.82, 1.42, "$y$ = periodic\npart", fs=8.3)
    D.wire([se["r"], (8.7, 2.05), so["b"]], color=INK)
    D.text(8.0, 2.25, "$e$", fs=9.5)
    D.dot(8.05, 2.05)
    D.wire([(8.05, 2.05), (8.05, 0.45), (5.55, 0.45), (5.55, 0.77)], color=RED, lw=1.1)
    D.note(0.3, 1.55, "In the high band the image is\nnearly white, the interference is\nstill a pure sinusoid:\n"
           "$\\tau_{image} < \\Delta < \\tau_{periodic}$", fs=8, color=INK2)
    D.note(5.75, 0.72, "LMS on $e$", fs=8, color=INK)
    D.save(OUT / "diagram_C_noref.png")


def window_icon(D, x0, y0, r=2, hole=0, s=0.17, title=None):
    k = 2 * r + 1
    for a in range(k):
        for b in range(k):
            inside = abs(a - r) <= hole and abs(b - r) <= hole
            fc = "#0b0b0b" if (a == r and b == r) else (MUTED if inside else BLUE_LIGHT)
            D.rect(x0 + b * s, y0 - a * s, s * 0.92, s * 0.92, fc=fc, ec="white", lw=0.4)
    if title:
        D.note(x0, y0 - k * s - 0.02, title, fs=7.5)


def scenario_d():
    D = Diagram(9.8, 4.3, "D  Self-tuning filter: blind-spot predictor, filter output kept")
    D.text(0.3, 3.2, "noisy image $d(i,j)$", fs=9, ha="left")
    D.dot(1.85, 3.2)
    se = D.sum(7.15, 3.2, signs=dict(l="+", b="\u2212"))
    D.wire([(1.75, 3.2), se["l"]], color=BLUE)
    D.wire([se["r"], (8.0, 3.2)], color=INK)
    D.text(8.75, 3.2, "$e$: noise estimate\n(impulse detector)", fs=8.2)
    bs = D.block(3.05, 1.95, 1.8, 0.7, "neighbours of $(i,j)$\ncentre pixel removed", fill=ORANGE_LIGHT, fs=8.2)
    D.wire([(1.85, 3.2), (1.85, 1.95), bs["l"]], color=ORANGE)
    f = D.adaptive(5.35, 1.95, 1.55, 0.6, "$W$: $(2r{+}1)^2{-}1$\ntaps", fs=8.2)
    D.wire([bs["r"], f["l"]], color=ORANGE)
    D.dot(6.55, 1.95)
    D.wire([f["r"], (7.15, 1.95), se["b"]], color=INK)
    D.wire([(6.55, 1.95), (6.55, 1.15), (8.0, 1.15)], color=AQUA, lw=1.6)
    D.text(8.75, 1.15, "$y$: image estimate\n(output)", fs=8.5)
    D.text(7.4, 2.35, "$y$", fs=9.5)
    D.dot(7.7, 3.2)
    D.wire([(7.7, 3.2), (7.7, 0.55), (5.35, 0.55), (5.35, 1.65)], color=RED, lw=1.1)
    D.note(5.5, 0.85, "LMS on $e$", fs=8, color=INK)
    window_icon(D, 0.35, 2.15, r=2, hole=0, s=0.15, title="5 x 5 window,\nblind spot = centre")
    D.note(0.3, 0.62, "error-gated variant (sparse noise): output $y$ where $|e| > k\\,\\hat\\sigma_e$, else $d$;\n"
           "adapt only on pixels kept as clean.", fs=8, color=INK2)
    D.save(OUT / "diagram_D_selftuning.png")


def scenario_e():
    D = Diagram(9.8, 4.2, "E  Adaptive line enhancer: L taps, prediction distance \u0394")
    D.text(0.3, 3.2, "$d(n)$", fs=10, ha="left")
    D.dot(0.95, 3.2)
    se = D.sum(8.3, 3.2, signs=dict(l="+", b="\u2212"))
    D.wire([(0.8, 3.2), se["l"]], color=BLUE)
    D.wire([se["r"], (9.6, 3.2)], color=INK)
    D.text(9.15, 3.4, "$e$", fs=9.5)
    dl = D.block(1.75, 2.1, 0.7, 0.42, "$z^{-\\Delta}$", fill=ORANGE_LIGHT)
    D.wire([(0.95, 3.2), (0.95, 2.1), dl["l"]], color=ORANGE)
    xs = [2.95, 4.15, 5.35, 6.55]
    prev = dl["r"]
    labels = ["$w_0$", "$w_1$", "$w_2$", "$w_{L-1}$"]
    for k, x in enumerate(xs):
        if k > 0:
            z = D.block(x - 0.6, 2.1, 0.5, 0.36, "$z^{-1}$" if k < 3 else "...", fill="white", fs=8)
            D.wire([prev, z["l"]], color=ORANGE)
            prev = z["r"]
        D.dot(x, 2.1, ORANGE) if k < 3 else None
        D.wire([prev, (x, 2.1)], color=ORANGE, head=False)
        m = D.block(x, 1.4, 0.55, 0.36, labels[k], fill="white", fs=8.5)
        D.wire([(x, 2.1), m["t"]], color=ORANGE)
        prev = (x, 2.1)
    sy = D.sum(7.6, 0.75, signs=dict(l="+"))
    for x in xs:
        D.wire([(x, 1.22), (x, 0.75), sy["l"]] if x == xs[0] else [(x, 1.22), (x, 0.75)], color=INK, head=(x == xs[0]))
    D.dot(7.98, 0.75)
    D.wire([sy["r"], (8.3, 0.75), se["b"]], color=INK)
    D.wire([(8.3, 0.75), (9.6, 0.75)], color=AQUA, lw=1.6)
    D.text(9.15, 0.98, "$y$: enhanced line", fs=8.5)
    D.note(2.45, 0.45, "converged peak gain at a line of power ratio SNR:  $G = (L/2)\\,\\mathrm{SNR}\\,/\\,((L/2)\\,\\mathrm{SNR} + 1)$\n"
           "a longer filter: gain $\\to$ 1 and a narrower band, but more weight noise", fs=8, color=INK)
    window_icon(D, 0.3, 1.55, r=3, hole=1, s=0.12, title="image: $L$ = window taps,\n$\\Delta$ = blind spot $(2h{+}1)^2$")
    D.save(OUT / "diagram_E_ale.png")


def scenario_f():
    D = Diagram(9.8, 4.4, "F  Reference-sensor canceller (the sidelobe canceller, on a sensor)")
    x0, y0, w, h, n_rows = 0.35, 0.95, 2.3, 2.3, 9
    D.rect(x0, y0, 0.4, h, fc="#2b2b2b")
    D.rect(x0 + 0.4, y0, w - 0.4, h, fc=BLUE_LIGHT)
    pitch = h / n_rows
    for k in range(1, n_rows):
        D.ax.plot([x0, x0 + w], [y0 + k * pitch] * 2, color="white", lw=0.6, zorder=2)
    yr = y0 + 5.5 * pitch
    D.ax.plot([x0 + 0.03, x0 + w - 0.03], [yr, yr], color=ORANGE, lw=2.4, zorder=3)
    D.note(x0, y0 + h + 0.42, "sensor frame, row $i$ highlighted\nmasked columns (left) | image pixels", fs=7.8, color=INK2)
    se = D.sum(7.6, 3.0, signs=dict(l="+", b="\u2212"))
    D.dot(x0 + w - 0.03, yr)
    D.wire([(x0 + w - 0.03, yr), (2.95, yr), (2.95, 3.0), se["l"]], color=BLUE)
    D.text(4.95, 3.22, "pixel of row $i$:  $d = s + c_i + $ read noise", fs=8.5)
    D.wire([se["r"], (9.6, 3.0)], color=INK)
    D.text(8.7, 3.22, "$e$ = output", fs=8.5)
    D.dot(x0 + 0.2, yr)
    m = D.block(4.25, 1.95, 1.7, 0.5, "mean of the $K$ masked\npixels of row $i$", fill=ORANGE_LIGHT, fs=8)
    D.wire([(x0 + 0.2, yr), (x0 + 0.2, 0.6), (3.05, 0.6), (3.05, 1.95), m["l"]], color=ORANGE)
    f = D.adaptive(6.15, 1.95, 0.75, 0.42, "$\\times\\, w$")
    D.wire([m["r"], f["l"]], color=ORANGE)
    D.text(5.05, 1.45, "$x_i = c_i + $ noise$/\\sqrt{K}$", fs=8.2)
    D.wire([f["r"], (7.6, 1.95), se["b"]], color=INK)
    D.note(3.3, 1.12, "$w$ is trained on a dark frame (shutter closed), or adapted only while the\n"
           "masked pixels are read. A reference output channel, read at the same instants\n"
           "as the pixels, plays the same role for readout telegraph noise.", fs=7.8, color=INK2)
    D.note(3.3, 0.38, "noise reduction $= (1 + R_{prin})\\,/\\,(R_{prin} + R_{refn}/(1 + R_{refn}))$", fs=8.2, color=INK)
    D.save(OUT / "diagram_F_reference.png")


def decision_guide():
    """Which configuration fits a corruption: questions from the top, the first 'yes' decides.

    The gains are read from results/benchmark_python.csv and results/examples_python.csv, so the diagram follows
    the stored runs (run_benchmark.py and make_examples.py write them).
    """
    import csv

    def table(name, key):
        path = REPO / "results" / name
        with open(path) as fh:
            return {tuple(r[k] for k in key): r for r in csv.DictReader(fh)}

    bench = table("benchmark_python.csv", ("noise", "method"))
    ex = table("examples_python.csv", ("example", "method"))

    def g(noise, method):
        return f"{float(bench[(noise, method)]['gain']):+.1f} dB"

    def gx(example, method):
        return f"{float(ex[(example, method)]['psnr']) - float(ex[(example, 'noisy')]['psnr']):+.1f} dB"

    W, H = 10.4, 8.2
    D = Diagram(W, H, "Which scenario?  Go down the questions; the first \"yes\" picks the canceller")
    rows = [
        ("A sensor or channel sees the interference but not the scene?\n"
         "(optical-black columns, a reference output channel)", "F  reference-sensor canceller",
         f"banding {g('banding', 'F')}, readout telegraph {g('telegraph_readout', 'F')}", ORANGE_LIGHT),
        ("Periodic interference at a known frequency,\nor a sharp, stable peak in the spectrum?", "A  adaptive notch",
         f"periodic {g('periodic', 'A')}, LED flicker {gx('A flicker', 'A, log domain')}", ORANGE_LIGHT),
        ("Periodic, but the frequency is unknown or drifts?", "C  canceller without a reference",
         f"periodic {g('periodic', 'C')}, drifting stripes {gx('C drifting stripes', 'C')}", ORANGE_LIGHT),
        ("An offset per line, or a slow drift along the scan?", "B  bias canceller",
         f"row banding {g('banding', 'B')}, probe scan {gx('B probe microscopy', 'B, gated')}", ORANGE_LIGHT),
        ("Sparse: a few pixels far off\n(impulses, bursts, dead or hot pixels)?", "D  error-gated self-tuning filter",
         f"impulses {g('impulse', 'Dg')}, bursts {g('burst', 'Dg')}", BLUE_LIGHT),
        ("Broadband and independent from pixel to pixel\n(Gaussian, Poisson)?", "D  blind-spot predictor",
         f"Gaussian {g('gaussian', 'D')}, Poisson {g('poisson', 'D')}", BLUE_LIGHT),
        ("A periodic texture to keep under heavy noise,\nor noise correlated over a few pixels?",
         "E  line enhancer (blind spot > correlation)",
         f"noisy lattice {gx('E lattice', 'E, 9x9')}, brick texture {gx('E periodic texture', 'E, 11x11')}", BLUE_LIGHT),
    ]
    qx, qw, ax_, aw, bh, y0, dy = 2.95, 5.3, 8.35, 3.6, 0.64, H - 0.95, 0.9
    for k, (q, name, gain, fill) in enumerate(rows):
        y = y0 - k * dy
        qb = D.block(qx, y, qw, bh, q, fill=NEUTRAL, fs=8.2)
        ab = D.block(ax_, y, aw, bh, None, fill=fill, fs=8.2)
        D.text(ax_, y + 0.12, name, fs=8.6, color=INK, fontweight="bold")
        D.text(ax_, y - 0.14, gain, fs=7.8, color=INK2)
        D.wire([qb["r"], ab["l"]], color=INK, lw=1.2)
        D.text((qb["r"][0] + ab["l"][0]) / 2, y + 0.13, "yes", fs=7.8, color=INK2)
        yn = y - dy + (0.25 if k == len(rows) - 1 else bh / 2)      # top of the next box (the blur box is 0.5 high)
        D.wire([qb["b"], (qx, yn)], color=MUTED, lw=1.1)
        D.text(qx + 0.2, (y - bh / 2 + yn) / 2, "no", fs=7.8, color=MUTED)
    yb = y0 - len(rows) * dy
    D.block(qx, yb, qw, 0.5, "Blur?  A convolution, not added noise: none of the six.\n"
            "Wire the same LMS as an inverse model (docs/beyond_blur.md).", fill="white", fs=8.0, edge=MUTED)
    D.rect(6.75, yb + 0.1, 0.22, 0.14, fc=ORANGE_LIGHT, ec=INK2, lw=0.6, z=3)
    D.note(7.05, yb + 0.25, "the filter predicts the noise; the output is $e = d - y$", fs=7.8)
    D.rect(6.75, yb - 0.24, 0.22, 0.14, fc=BLUE_LIGHT, ec=INK2, lw=0.6, z=3)
    D.note(7.05, yb - 0.09, "the filter predicts the image; the output is $y$", fs=7.8)
    stages = sorted((m, float(r["psnr"])) for (n, m), r in bench.items() if n == "mixed" and m.startswith("stage"))
    D.note(0.3, yb - 0.42, "Several corruptions at once: remove them in this order, top to bottom. The cascade "
           f"F (twice), A, D gated, E raises\nthe all-noise image from {stages[0][1]:.2f} dB to {stages[-1][1]:.2f} dB. "
           "Gains: PSNR over the noisy input (camera benchmark, then the application example).", fs=7.8, color=INK2)
    D.save(OUT / "diagram_decision_guide.png")

if __name__ == "__main__":
    setup()
    OUT.mkdir(parents=True, exist_ok=True)
    every = [principle, scenario_a, scenario_b, scenario_c, scenario_d, scenario_e, scenario_f, decision_guide]
    names = set(sys.argv[1:])
    for fn in every:
        if not names or fn.__name__ in names:
            fn()
    print("diagrams written to", OUT)
