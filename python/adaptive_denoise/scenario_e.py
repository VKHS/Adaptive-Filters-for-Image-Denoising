"""Scenario E: adaptive line enhancer (ALE) - the quantitative form of scenario D.

An L-weight predictor with prediction distance Delta, x(n) = d(n - Delta), output y = filter output.
For a sinusoid of power-to-noise ratio SNR in white noise, the converged (Wiener-Hopf) filter is a band-pass
centred on the line, with peak gain

    G = (L/2) SNR / ((L/2) SNR + 1)          (on a DFT bin; G -> 1 as L grows)

so a longer filter passes the line with less loss and a narrower band, at the price of more weight noise
(misadjustment grows with L * mu2) and slower adaptation. The delay must outlast the noise correlation.

Image form: L is the number of taps of the 2-D window, Delta is the blind-spot size. ``line_enhancer``
chooses the blind spot from the measured noise correlation (``predictor.choose_hole``).
This module also holds the 1-D theory used by the figures.
"""
import numpy as np
from scipy.linalg import toeplitz

from .predictor import blindspot_lms, choose_hole


def line_enhancer(img, r=3, hole=None, alpha=0.01, passes=2, record=False):
    """Blind-spot predictor with a larger window and a blind spot matched to the noise correlation.
    Returns the filter output (and the hole used when record=True)."""
    h = choose_hole(img) if hole is None else hole
    r = max(r, h + 2)                      # keep at least two rings of taps outside the blind spot
    out = blindspot_lms(img, r=r, hole=h, alpha=alpha, passes=passes, record=record)
    if record:
        out, info = out
        info["hole"] = h
        return out, info
    return out


# --------------------------------------------------------------------------------------------- 1-D theory
def ale_wiener_weights(L, delay, snr, omega0, noise_power=1.0):
    """Exact Wiener-Hopf weights for a sinusoid (power snr * noise_power) in white noise."""
    k = np.arange(L + delay + 1)
    phi = snr * noise_power * np.cos(omega0 * k)
    phi[0] += noise_power
    R = toeplitz(phi[:L])
    p = phi[delay:delay + L]
    return np.linalg.solve(R, p)


def ale_peak_gain(L, snr):
    """Peak gain of the converged ALE at the line frequency (line on a DFT bin)."""
    return (L / 2.0 * snr) / (L / 2.0 * snr + 1.0)


def ale_response(w, delay, omega):
    """Frequency response of the ALE from input d to output y: sum_k w_k exp(-j omega (delay + k))."""
    k = np.arange(len(w))
    omega = np.atleast_1d(omega)
    return np.exp(-1j * np.outer(omega, delay + k)) @ w


def ale_lms(d, L, delay, mu2, w0=None):
    """Sample-by-sample LMS ALE. Returns (filter output y, error e, final weights, weight history)."""
    n = len(d)
    w = np.zeros(L) if w0 is None else np.array(w0, float)
    y = np.zeros(n)
    e = np.zeros(n)
    hist = np.zeros((n, L))
    for t in range(delay + L, n):
        x = d[t - delay - L + 1:t - delay + 1][::-1]
        y[t] = w @ x
        e[t] = d[t] - y[t]
        w += mu2 * e[t] * x
        hist[t] = w
    return y, e, w, hist


def lattice(shape, components, offset=0.5):
    """Periodic test texture: offset + sum A cos(2 pi (u i + v j) + phase)."""
    H, W = shape
    i, j = np.mgrid[0:H, 0:W]
    return offset + sum(A * np.cos(2 * np.pi * (u * i + v * j) + ph) for A, u, v, ph in components)


def wiener_limit_2d(components, sigma, r, hole=0):
    """MSE-optimal (infinite data) blind-spot predictor for a lattice in white noise. Returns PSNR in dB."""
    offs = [(a, b) for a in range(-r, r + 1) for b in range(-r, r + 1) if max(abs(a), abs(b)) > hole]

    def Rss(da, db):
        return sum(A ** 2 / 2 * np.cos(2 * np.pi * (u * da + v * db)) for A, u, v, _ in components)

    n = len(offs)
    R = np.empty((n, n))
    p = np.empty(n)
    for a, (a1, b1) in enumerate(offs):
        p[a] = Rss(a1, b1)
        for b, (a2, b2) in enumerate(offs):
            R[a, b] = Rss(a1 - a2, b1 - b2)
    R += sigma ** 2 * np.eye(n)
    w = np.linalg.solve(R, p)
    mse = Rss(0, 0) - p @ w
    return float(10 * np.log10(1.0 / mse))
