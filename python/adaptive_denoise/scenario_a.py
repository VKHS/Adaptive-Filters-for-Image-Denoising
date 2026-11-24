"""Scenario A: adaptive notch filter with a synthetic sinusoidal reference.

Primary  d = s + n, with n a sum of sinusoids.
Reference: for every interference frequency a pair C cos(theta), C sin(theta). Two weights per frequency
can build any amplitude and phase, so only the frequency must be known, not the phase.
Output   e = d - sum_k (w_2k C cos theta_k + w_2k+1 C sin theta_k), which is also the LMS error.

For a 1-D sinusoid theta = omega0 n the closed loop is the time-invariant notch

    H(z) = (z^2 - 2 cos(omega0) z + 1) / (z^2 - 2 (1 - mu2 C^2 / 2) cos(omega0) z + 1 - mu2 C^2)

with zeros on the unit circle (infinite null), poles at radius ~ 1 - mu2 C^2 / 2 and a -3 dB width of
about mu2 C^2 rad/sample (mu2 is the full LMS step, w <- w + mu2 e x).

In an image the reference is a 2-D plane wave theta = 2 pi (u i + v j) scanned in raster order, so the
weights only learn the amplitude and phase once and keep them from row to row. The frequencies (u, v) are
either known (system timing: mains flicker in a rolling shutter, scanner vibration) or detected from the
image spectrum (spectral.detect_peaks).
"""
import numpy as np

from .spectral import detect_peaks


def notch_response_theory(omega0, mu2C2, omega):
    """Closed-loop frequency response H(e^{j omega}) of the two-weight LMS notch."""
    z = np.exp(1j * np.asarray(omega))
    num = z ** 2 - 2 * np.cos(omega0) * z + 1
    den = z ** 2 - 2 * (1 - mu2C2 / 2) * np.cos(omega0) * z + 1 - mu2C2
    return num / den


def notch_poles_zeros(omega0, mu2C2):
    zeros = np.roots([1, -2 * np.cos(omega0), 1])
    poles = np.roots([1, -2 * (1 - mu2C2 / 2) * np.cos(omega0), 1 - mu2C2])
    return zeros, poles


def notch_response_measured(omega0, mu2, C=1.0, n=2 ** 18, seed=0, nfft=4096):
    """Run the LMS notch on white noise and estimate its transfer function from cross spectra."""
    rng = np.random.default_rng(seed)
    d = rng.standard_normal(n)
    k = np.arange(n)
    x1, x2 = C * np.cos(omega0 * k), C * np.sin(omega0 * k)
    w1 = w2 = 0.0
    e = np.empty(n)
    for t in range(n):
        et = d[t] - (w1 * x1[t] + w2 * x2[t])
        w1 += mu2 * et * x1[t]
        w2 += mu2 * et * x2[t]
        e[t] = et
    seg = nfft
    win = np.hanning(seg)
    Sxy = np.zeros(seg // 2 + 1, complex)
    Sxx = np.zeros(seg // 2 + 1)
    for s0 in range(seg, n - seg, seg // 2):
        D = np.fft.rfft(d[s0:s0 + seg] * win)
        E = np.fft.rfft(e[s0:s0 + seg] * win)
        Sxy += E * np.conj(D)
        Sxx += np.abs(D) ** 2
    om = 2 * np.pi * np.fft.rfftfreq(seg)
    return om, Sxy / Sxx


def plane_wave_refs(shape, freqs, C=1.0):
    H, W = shape
    i, j = np.mgrid[0:H, 0:W]
    refs = np.empty((H, W, 2 * len(freqs)))
    for k, (u, v) in enumerate(freqs):
        th = 2 * np.pi * (u * i + v * j)
        refs[..., 2 * k] = C * np.cos(th)
        refs[..., 2 * k + 1] = C * np.sin(th)
    return refs


def notch_lms(img, freqs, mu2=0.002, C=1.0, passes=2, record=False):
    """Two-weight-per-frequency LMS notch in raster order. Returns the error output (cleaned image).

    The image mean is removed before and restored after, so the DC level does not jitter the weights.
    The first pass lets the weights converge; the output of the last pass is returned.
    """
    H, W = img.shape
    m = float(img.mean())
    z = img - m
    refs = plane_wave_refs(img.shape, freqs, C)
    nw = refs.shape[-1]
    w = np.zeros(nw)
    out = np.empty((H, W))
    hist = np.empty((H * passes, nw)) if record else None
    for p in range(passes):
        for i in range(H):
            R = refs[i]
            d = z[i]
            o = out[i]
            for j in range(W):
                x = R[j]
                e = d[j] - w @ x
                w += (mu2 * e) * x
                o[j] = e
            if record:
                hist[p * H + i] = w
    out += m
    if record:
        return out, dict(weights=w, history=hist)
    return out


def adaptive_notch(img, freqs=None, mu2=0.002, C=1.0, passes=2, **detect_kw):
    """Scenario A end to end: detect the interference frequencies (unless given) and cancel them.

    Returns (cleaned image, list of frequencies used). With no detected peak the image is returned unchanged.
    """
    if freqs is None:
        freqs = [(u, v) for u, v, _ in detect_peaks(img, **detect_kw)]
    if not freqs:
        return img.copy(), []
    return notch_lms(img, freqs, mu2=mu2, C=C, passes=passes), list(freqs)


def notch_rows_1d(img, v, mu2=0.02, C=1.0):
    """The report's single-frequency notch applied along each row (reference cos/sin(2 pi v j)), weights
    carried from row to row. Equivalent to notch_lms with u = 0 and one pass."""
    return notch_lms(img, [(0.0, v)], mu2=mu2, C=C, passes=1)
