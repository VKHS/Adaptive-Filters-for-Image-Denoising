"""Scenario C: cancelling periodic interference without a reference.

When no separate reference exists, a delayed copy of the primary serves as one:

    x(n) = d(n - Delta),   y(n) = sum_k w_k x(n - k),   e(n) = d(n) - y(n)   (output = error)

The broadband part of d decorrelates within Delta samples, so the filter cannot predict it; the periodic part
stays correlated at any delay, so the filter learns to predict it and the error output keeps only the
broadband part. The delay must satisfy tau_broadband < Delta < tau_periodic.

Applied to raw image rows this fails: neighbouring pixels are strongly correlated, so most of the image is
"periodic enough" to be predicted and is cancelled together with the stripes (``delayed_canceller``).

The fix is a two-band split (``subband_canceller``). Each row is divided into a low band (Gaussian
smoothing, sigma = 4 px) and the high band that remains. The low band, which holds most of the image, is
passed through untouched. In the high band the image is close to white (edges and texture), while the
interference above ~0.05 cycles/pixel is still a pure sinusoid, so the delayed-reference canceller works as
intended there. Output = low band + error output of the high-band canceller. No frequency has to be known.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.ndimage import gaussian_filter1d


def _rows_lms(z, L, delay, mu2, record=False):
    """LMS predictor run along each row of z (weights carried between rows).
    Returns the prediction y with z(n) predicted from z(n - delay - k), k = 0..L-1."""
    H, W = z.shape
    P0 = delay + L - 1
    w = np.zeros(L)
    y = np.empty((H, W))
    for i in range(H):
        p = np.pad(z[i], (P0, 0), mode="reflect")
        X = sliding_window_view(p, L)[:W][:, ::-1]      # X[j] = [z(j-delay), z(j-delay-1), ...]
        d = z[i]
        yi = y[i]
        for j in range(W):
            x = X[j]
            yj = w @ x
            w += (mu2 * (d[j] - yj)) * x
            yi[j] = yj
    return (y, w) if record else y


def delayed_canceller(img, L=32, delay=64, alpha=0.01):
    """The canceller exactly as in the 1-D theory, on raw rows. Returns the error output."""
    m = img.mean(axis=1, keepdims=True)
    z = img - m
    mu2 = alpha / (L * float(z.var()))
    y = _rows_lms(z, L, delay, mu2)
    return img - y


def subband_canceller(img, L=128, delay=8, alpha=0.002, split_sigma=4.0, record=False):
    """Delayed-reference canceller run on the high band of each row; the low band is kept as it is.

    Returns the cleaned image (and, with record=True, a dict with the interference estimate, the high band
    and the final predictor weights, whose frequency response shows the lines the filter found by itself).
    """
    z = img - img.mean(axis=1, keepdims=True)
    high = z - gaussian_filter1d(z, split_sigma, axis=1, mode="reflect")
    mu2 = alpha / (L * float(high.var()))
    y, w = _rows_lms(high, L, delay, mu2, record=True)
    out = img - y
    if record:
        return out, dict(interference=y, high=high, weights=w, mu2=mu2)
    return out


def predictor_response(w, delay, nfft=2048):
    """Frequency response of the prediction filter sum_k w_k z^-(delay + k), on [0, 0.5] cycles/pixel."""
    h = np.zeros(delay + len(w))
    h[delay:] = w
    Hf = np.fft.rfft(h, nfft)
    return np.fft.rfftfreq(nfft), Hf
