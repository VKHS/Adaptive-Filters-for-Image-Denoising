"""Scenario B: bias (drift) canceller - one adaptive weight on a constant reference.

Reference x = 1, so the filter output is the weight itself, b, and the error is e = d - b.
With LMS, b <- b + mu2 e, the closed loop is the first-order high-pass

    H(z) = (z - 1) / (z - (1 - mu2))          (zero at DC, corner ~ mu2 rad/sample)

so b tracks the slowly varying offset and e is the input with the offset removed. The weight can share an
adaptive filter with ordinary taps (a "bias weight").

Images expose the weak point of this structure: the canceller cannot tell a drifting offset from scene
brightness, because both are slow. Three image forms are provided:

* ``bias_canceller``      - the textbook form along each scan line. A high-pass in x: it flattens the
                            scene too. Works on scenes with a flat background (probe microscopy, documents)
                            once the update is made robust: sign-error (median tracking) or gated
                            (update only when |e| < tau, i.e. on background pixels).
* ``interline_canceller`` - the bias weight tracks the offset between the current line and the previous
                            corrected line (primary = current line, reference = previous line + constant 1).
                            With a sign-error update it converges to the median line-to-line difference.
                            It removes row banding on natural images, at the cost of a random-walk error.
* ``afm_scene``           - a synthetic flat-background test scene.
"""
import numpy as np

from .noise import gaussian_blur


def bias_response_theory(mu2, omega):
    z = np.exp(1j * np.asarray(omega))
    return (z - 1) / (z - (1 - mu2))


def bias_canceller(img, mu2=0.02, update="lms", tau=0.08):
    """Bias canceller along every row. update: "lms" (report), "sign" (median tracking) or "gated".

    The weight starts each row at the median of the first 8 pixels. Returns (output e, tracked offset b).
    """
    H, W = img.shape
    out = np.empty((H, W))
    track = np.empty((H, W))
    for i in range(H):
        row = img[i]
        b = float(np.median(row[:8]))
        o = out[i]
        t = track[i]
        for j in range(W):
            e = row[j] - b
            o[j] = e
            t[j] = b
            if update == "lms":
                b += mu2 * e
            elif update == "sign":
                b += mu2 if e > 0 else (-mu2 if e < 0 else 0.0)
            elif update == "gated":
                if -tau < e < tau:
                    b += mu2 * e
    return out, track


def interline_canceller(img, mu2=0.001, passes=2, hp_rows=16):
    """Line-to-line bias canceller with a sign-error update.

    For row i the primary is the row, the reference is the previous *corrected* row, and the single bias
    weight b_i is adapted along the row (``passes`` sweeps) on e = (row - previous) - b_i. The corrected
    row is row - b_i. Because the previous row is already corrected, b_i is the full offset of row i (plus
    the scene's own line-to-line change, whose errors accumulate from row to row). With hp_rows set, the
    slow part of the sequence b_i (Gaussian, hp_rows rows) is put back, so only fast banding is removed and
    slow scene shading survives (hp_rows=None switches this off).
    Returns (corrected image, per-row offset estimates).
    """
    H, W = img.shape
    out = img.astype(float).copy()
    off = np.zeros(H)
    for i in range(1, H):
        diff = img[i] - out[i - 1]
        b = 0.0
        for _ in range(passes):
            for j in range(W):
                e = diff[j] - b
                b += mu2 if e > 0 else (-mu2 if e < 0 else 0.0)
        off[i] = b
        out[i] = img[i] - b
    if hp_rows:
        t = np.arange(-int(4 * hp_rows), int(4 * hp_rows) + 1)
        g = np.exp(-t ** 2 / (2.0 * hp_rows ** 2))
        g /= g.sum()
        slow = np.convolve(np.pad(off, len(t) // 2, mode="reflect"), g, mode="valid")
        out = out + slow[:, None]
        off = off - slow
    return out, off


def afm_scene(shape=(512, 512), n_obj=60, seed=0, background=0.3):
    """Flat background with Gaussian blobs: the kind of scene line levelling was designed for."""
    rng = np.random.default_rng(seed)
    H, W = shape
    i, j = np.mgrid[0:H, 0:W]
    s = np.full(shape, background)
    for _ in range(n_obj):
        ci, cj = rng.uniform(10, H - 10), rng.uniform(10, W - 10)
        sg = rng.uniform(3.0, 8.0)
        h = rng.uniform(0.25, 0.5)
        s += h * np.exp(-((i - ci) ** 2 + (j - cj) ** 2) / (2 * sg ** 2))
    return np.clip(s, 0, 1)


def row_offsets_and_tilt(shape, rng, sigma_row=0.05, tilt=0.15):
    """Row offsets plus a linear drift along the scan: the disturbance scenario B is meant for."""
    H, W = shape
    return sigma_row * rng.standard_normal((H, 1)) + tilt * np.linspace(0, 1, W)[None, :]


def offset_aligned_psnr(ref, est):
    """PSNR after removing the global mean error (a drift canceller cannot know the absolute level)."""
    e = est - ref
    e = e - e.mean()
    return float(10 * np.log10(1.0 / np.mean(e ** 2)))
