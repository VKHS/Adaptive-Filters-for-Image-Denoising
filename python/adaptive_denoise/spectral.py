"""Spectral helpers: averaged 2-D power spectrum and detection of periodic-interference peaks.

A periodic pattern A cos(2 pi (u i + v j) + phase) is a pair of sharp peaks at +-(u, v) in the 2-D spectrum,
while a natural image has a smooth spectrum that falls off with frequency. Peaks are found on the ratio
of the averaged spectrum to its local median, so the 1/f slope of the image does not matter, and then
refined on the full-resolution spectrum with parabolic interpolation.
"""
import numpy as np
from scipy.ndimage import median_filter, maximum_filter


def welch2d(img, block=128, step=64):
    """Average of Hann-windowed periodograms of overlapping blocks (fftshifted, DC in the middle)."""
    H, W = img.shape
    win = np.outer(np.hanning(block), np.hanning(block))
    acc = np.zeros((block, block))
    n = 0
    for i0 in range(0, H - block + 1, step):
        for j0 in range(0, W - block + 1, step):
            b = img[i0:i0 + block, j0:j0 + block]
            b = (b - b.mean()) * win
            acc += np.abs(np.fft.fft2(b)) ** 2
            n += 1
    return np.fft.fftshift(acc / n)


def peak_ratio_map(img, block=128, step=64, bg=9):
    """Averaged spectrum divided by its local median (bg x bg bins). Returns (ratio, frequency axis)."""
    P = welch2d(img, block, step)
    B = median_filter(P, size=bg, mode="wrap")
    f = np.fft.fftshift(np.fft.fftfreq(block))
    return P / np.maximum(B, 1e-30), f


def _directional_contrast(P, ki, kj, reach=5):
    """Peak height over the median of its neighbours along u and along v (centre +-1 excluded), the smaller
    of the two. A point peak is high in both directions; a line in the spectrum (row banding, edges) is not."""
    n = P.shape[0]
    offs = [o for o in range(-reach, reach + 1) if abs(o) > 1]
    along_u = np.median([P[(ki + o) % n, kj] for o in offs])
    along_v = np.median([P[ki, (kj + o) % n] for o in offs])
    return float(min(P[ki, kj] / max(along_u, 1e-30), P[ki, kj] / max(along_v, 1e-30)))


def detect_peaks(img, thresh=30.0, contrast=10.0, fmin=0.03, max_peaks=6, block=128, step=64):
    """Detect periodic components. Returns a list of (u, v, ratio): u is the vertical frequency (cycles per
    row), v the horizontal frequency (cycles per column), one entry per +-(u, v) pair, strongest first.

    A bin is accepted when it is a local maximum, exceeds ``thresh`` times the local median of the
    averaged spectrum, and exceeds ``contrast`` times its neighbours along both frequency axes.
    """
    P = welch2d(img, block, step)
    R = P / np.maximum(median_filter(P, size=9, mode="wrap"), 1e-30)
    f = np.fft.fftshift(np.fft.fftfreq(block))
    U, V = np.meshgrid(f, f, indexing="ij")
    rad = np.hypot(U, V)
    half = (V > 0) | ((V == 0) & (U > 0))
    cand = (R == maximum_filter(R, size=5, mode="wrap")) & (R > thresh) & (rad > fmin) & half
    idx = np.argwhere(cand)
    order = np.argsort(-R[cand])
    peaks = []
    for a in order:
        ki, kj = idx[a]
        if _directional_contrast(P, ki, kj) < contrast:
            continue
        u, v = refine_peak(img, f[ki], f[kj], search=1.5 / block)
        peaks.append((u, v, float(R[ki, kj])))
        if len(peaks) == max_peaks:
            break
    return peaks


def refine_peak(img, u0, v0, search, pad=2):
    """Refine a peak location on the zero-padded full-image spectrum (parabolic fit in u and in v)."""
    H, W = img.shape
    win = np.outer(np.hanning(H), np.hanning(W))
    F = np.abs(np.fft.fft2((img - img.mean()) * win, s=(pad * H, pad * W))) ** 2
    fu = np.fft.fftfreq(pad * H)
    fv = np.fft.fftfreq(pad * W)
    iu = np.where(np.abs(((fu - u0 + 0.5) % 1.0) - 0.5) <= search)[0]
    iv = np.where(np.abs(((fv - v0 + 0.5) % 1.0) - 0.5) <= search)[0]
    sub = F[np.ix_(iu, iv)]
    a, b = np.unravel_index(np.argmax(sub), sub.shape)
    ku, kv = iu[a], iv[b]

    def parab(l, c, r):
        l, c, r = np.log(l + 1e-30), np.log(c + 1e-30), np.log(r + 1e-30)
        den = l - 2 * c + r
        return 0.0 if den == 0 else 0.5 * (l - r) / den

    du = parab(F[(ku - 1) % (pad * H), kv], F[ku, kv], F[(ku + 1) % (pad * H), kv])
    dv = parab(F[ku, (kv - 1) % (pad * W)], F[ku, kv], F[ku, (kv + 1) % (pad * W)])
    u = (ku + du) / (pad * H)
    v = (kv + dv) / (pad * W)
    u = ((u + 0.5) % 1.0) - 0.5
    v = ((v + 0.5) % 1.0) - 0.5
    if v < 0 or (v == 0 and u < 0):
        u, v = -u, -v
    return float(u), float(v)


def row_spectrum(img):
    """Row-averaged power spectrum along the raster direction (Hann window), positive frequencies."""
    z = img - img.mean(axis=1, keepdims=True)
    W = img.shape[1]
    P = (np.abs(np.fft.rfft(z * np.hanning(W), axis=1)) ** 2).mean(axis=0)
    return np.fft.rfftfreq(W), P


def log_spectrum(img):
    """Full-image log-magnitude spectrum (fftshifted) for display."""
    H, W = img.shape
    win = np.outer(np.hanning(H), np.hanning(W))
    F = np.fft.fftshift(np.abs(np.fft.fft2((img - img.mean()) * win)))
    return np.log10(F + 1e-6)
