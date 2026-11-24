"""Two-dimensional blind-spot LMS predictor: the image form of the reference-less canceller.

The 1-D canceller without a reference feeds a *delayed* copy of the primary input to the adaptive filter.
The delay must outlast the correlation of the broadband part and stay shorter than the correlation of the
narrowband part. In an image the delay becomes a *blind spot*: the filter predicts pixel (i, j) from a
(2r+1) x (2r+1) window with the central (2h+1) x (2h+1) block removed. White noise in the centre pixel is
uncorrelated with every tap, so it cannot be predicted; the image is correlated with its neighbours, so it can.

* filter output y  (scenario D, self-tuning filter / E, line enhancer): the predictable part = image estimate
* error output e   (scenario C idea): the unpredictable part = noise estimate; for sparse noise it is a
  detector, which the gated variant uses to replace only the corrupted pixels.

The weights adapt with LMS, sample by sample, in raster order: w <- w + mu2 * e * x.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from .metrics import estimate_noise_sigma
from .noise import gaussian_blur


def tap_mask(r, hole=0):
    """Boolean (2r+1) x (2r+1) mask of the taps in use: the whole window minus the central (2h+1)^2 block."""
    k = 2 * r + 1
    m = np.ones((k, k), bool)
    m[r - hole:r + hole + 1, r - hole:r + hole + 1] = False
    return m


def _row_taps(pad, i, r, W, mask_flat):
    k = 2 * r + 1
    return sliding_window_view(pad[i:i + k], (k, k))[0].reshape(W, k * k)[:, mask_flat]


def blindspot_lms(img, r=2, hole=0, alpha=0.01, mu2=None, passes=2, update="lms", record=False):
    """LMS blind-spot predictor. Returns the filter output (image estimate).

    Parameters
    ----------
    r, hole : window radius and blind-spot half-width (taps = (2r+1)^2 - (2h+1)^2).
    alpha   : normalised step. mu2 = alpha / (taps * var(img)), so the misadjustment is about alpha / 2.
    mu2     : explicit step (overrides alpha).
    passes  : raster passes over the image; the output of the last pass is returned.
    update  : "lms" (w += mu2 e x) or "sign" (w += mu2 sign(e) x, robust to outliers).
    record  : also return a dict with the final weights, the step and a learning curve.
    """
    H, W = img.shape
    m = float(img.mean())
    z = img - m
    mask = tap_mask(r, hole)
    mflat = mask.ravel()
    n_taps = int(mflat.sum())
    if mu2 is None:
        mu2 = alpha / (n_taps * float(z.var()))
    pad = np.pad(z, r, mode="reflect")
    w = np.zeros(n_taps)
    y = np.empty((H, W))
    curve = np.empty(H * passes) if record else None
    sign = update == "sign"
    for p in range(passes):
        for i in range(H):
            X = _row_taps(pad, i, r, W, mflat)
            d = z[i]
            yi = y[i]
            acc = 0.0
            for j in range(W):
                x = X[j]
                yj = w @ x
                e = d[j] - yj
                if sign:
                    w += (mu2 if e > 0 else -mu2) * x
                else:
                    w += (mu2 * e) * x
                yi[j] = yj
                acc += e * e
            if record:
                curve[p * H + i] = acc / W
    out = y + m
    if record:
        kern = np.zeros(mask.shape)
        kern[mask] = w
        return out, dict(weights=kern, mu2=mu2, n_taps=n_taps, curve=curve)
    return out


def blindspot_gated(img, r=2, alpha=0.01, k=4.0, passes=3, t_min=0.1):
    """Error-gated predictor for sparse (impulsive) noise.

    The prediction error e = d - y is small on clean pixels and large on impulses. Each pixel is
    classified with |e| > max(k * s, t_min), where s is a running robust scale of e and t_min a floor on the
    threshold (deviations below it are within the range of ordinary texture, and without the floor the scale
    collapses on flat, noise-free regions so that edges get flagged). Flagged pixels are replaced by the
    prediction y and do not update the weights; clean pixels are kept as they are.
    Pass 1 builds the taps from the noisy image; later passes build them from the previous output, so
    neighbours that were flagged no longer contaminate the prediction (bursts).
    Returns (output, flag mask).
    """
    H, W = img.shape
    m = float(np.median(img))
    z = img - m
    mask = tap_mask(r, 0)
    mflat = mask.ravel()
    n_taps = int(mflat.sum())
    mu2 = alpha / (n_taps * float(np.var(np.clip(z, -0.5, 0.5))))
    w = np.zeros(n_taps)
    w[:] = 1.0 / n_taps
    src = z.copy()
    flags = np.zeros((H, W), bool)
    out = z.copy()
    for p in range(passes):
        pad = np.pad(src, r, mode="reflect")
        s = 0.05
        for i in range(H):
            X = _row_taps(pad, i, r, W, mflat)
            d = z[i]
            for j in range(W):
                x = X[j]
                yj = w @ x
                e = d[j] - yj
                ae = abs(e)
                bad = ae > max(k * s, t_min)
                if bad:
                    out[i, j] = yj
                    flags[i, j] = True
                else:
                    out[i, j] = d[j]
                    flags[i, j] = False
                    w += (mu2 * e) * x
                    s += 0.01 * (1.4826 * ae - s)
        src = out.copy()
    return out + m, flags


def noise_correlation(img, block=16, frac=0.1, max_lag=3):
    """Normalised autocorrelation of the noise at lags 1..max_lag, measured in the flattest blocks.

    The image is cut into ``block`` x ``block`` tiles; a plane is fitted and removed from each tile, and the
    ``frac`` tiles with the smallest residual variance are kept. In those tiles the image is nearly planar,
    so the residual is noise. rho(k) is averaged over the horizontal and vertical directions.
    """
    H, W = img.shape
    ii, jj = np.mgrid[0:block, 0:block]
    A = np.stack([np.ones(block * block), ii.ravel(), jj.ravel()], 1)
    P = np.linalg.pinv(A)
    tiles = []
    for i0 in range(0, H - block + 1, block):
        for j0 in range(0, W - block + 1, block):
            t = img[i0:i0 + block, j0:j0 + block].ravel()
            res = (t - A @ (P @ t)).reshape(block, block)
            tiles.append((res.var(), res))
    tiles.sort(key=lambda a: a[0])
    sel = [r for _, r in tiles[:max(1, int(frac * len(tiles)))]]
    v = np.mean([np.mean(r * r) for r in sel])
    rho = []
    for k in range(1, max_lag + 1):
        h = np.mean([np.mean(r[:, k:] * r[:, :-k]) for r in sel])
        vv = np.mean([np.mean(r[k:, :] * r[:-k, :]) for r in sel])
        rho.append(0.5 * (h + vv) / v)
    return np.array(rho)


def choose_hole(img, rho_max=0.2, max_hole=3):
    """Blind-spot half-width h from the correlation length of the noise.

    h is the largest lag k with rho(k) > rho_max (0 when the noise is white). This is the image version
    of the line-enhancer rule that the delay must outlast the correlation of the broadband component.
    """
    rho = noise_correlation(img, max_lag=max_hole)
    h = 0
    for k in range(max_hole):
        if rho[k] > rho_max:
            h = k + 1
        else:
            break
    return h


def noise_aware_alpha(img, base=0.01):
    """Normalised step used by default: smaller steps when the noise is strong (lower misadjustment)."""
    s = estimate_noise_sigma(img)
    return base if s > 0.02 else 2 * base
