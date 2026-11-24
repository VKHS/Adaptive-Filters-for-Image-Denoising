"""Beyond the six scenarios: blur, handled by adaptive inverse modelling.

Blur is a convolution, not an additive interference, so none of the six cancellers removes it. The same LMS
machinery does, in a different wiring: show the system a calibration target whose sharp version is known,
feed the *blurred* target to the adaptive filter, and use the *sharp* target as the desired signal. The filter
converges to the Wiener solution W = S_xd / S_xx; with a noise-free reference that is the inverse 1/H of the
blur, and with noise in the blurred input it becomes the Wiener deconvolution filter, which stops amplifying
frequencies where noise dominates.

The learned kernel is then applied to the blurred image. LMS needs many samples here: blur makes the
eigenvalue spread of the input correlation matrix large, so the high-frequency modes converge slowly.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.ndimage import correlate


def dead_leaves(shape=(512, 512), n=6000, rmin=1.5, rmax=60.0, seed=0):
    """Calibration target: overlapping discs with power-law radii (scale-invariant, like natural images)."""
    rng = np.random.default_rng(seed)
    H, W = shape
    img = np.full(shape, 0.5)
    i, j = np.mgrid[0:H, 0:W]
    u = rng.random(n)
    radii = (rmin ** -2 - u * (rmin ** -2 - rmax ** -2)) ** -0.5     # density ~ r^-3
    for k in range(n):
        ci, cj, r = rng.uniform(-rmax, H + rmax), rng.uniform(-rmax, W + rmax), radii[k]
        i0, i1 = max(int(ci - r), 0), min(int(ci + r) + 2, H)
        j0, j1 = max(int(cj - r), 0), min(int(cj + r) + 2, W)
        if i0 >= i1 or j0 >= j1:
            continue
        sub = (i[i0:i1, j0:j1] - ci) ** 2 + (j[i0:i1, j0:j1] - cj) ** 2 <= r * r
        img[i0:i1, j0:j1][sub] = rng.uniform(0.05, 0.95)
    return img


def train_inverse_filter(sharp, blurred, r=4, alpha=0.05, passes=2, record=False, w_ref=None):
    """LMS inverse model: predict sharp(i, j) from the (2r+1)^2 window of the blurred target around (i, j).
    Returns the kernel (2r+1, 2r+1) for ``correlate``. With record=True also a dict with the learning curve
    (mean squared error per row) and, if ``w_ref`` is given, the relative distance to it after every row."""
    H, W = blurred.shape
    k = 2 * r + 1
    m = float(blurred.mean())
    pad = np.pad(blurred - m, r, mode="reflect")
    d_all = sharp - float(sharp.mean())
    mu2 = alpha / (k * k * float(np.var(blurred)))
    w = np.zeros(k * k)
    w[(k * k) // 2] = 1.0
    curve = []
    dist = []
    ref = None if w_ref is None else np.asarray(w_ref, float).ravel()
    for _ in range(passes):
        for i in range(H):
            X = sliding_window_view(pad[i:i + k], (k, k))[0].reshape(W, k * k)
            d = d_all[i]
            acc = 0.0
            for j in range(W):
                x = X[j]
                e = d[j] - w @ x
                w += (mu2 * e) * x
                acc += e * e
            curve.append(acc / W)
            if ref is not None:
                dist.append(float(np.linalg.norm(w - ref) / np.linalg.norm(ref)))
    kern = w.reshape(k, k)
    if record:
        return kern, dict(curve=np.array(curve), dist=np.array(dist))
    return kern


def least_squares_inverse_filter(sharp, blurred, r=4):
    """Closed-form solution of the same problem (normal equations R w = p): what LMS converges to."""
    H, W = blurred.shape
    k = 2 * r + 1
    m = float(blurred.mean())
    pad = np.pad(blurred - m, r, mode="reflect")
    X = sliding_window_view(pad, (k, k)).reshape(H * W, k * k)
    d = (sharp - float(sharp.mean())).ravel()
    w = np.linalg.solve(X.T @ X, X.T @ d)
    return w.reshape(k, k)


def apply_filter(img, kern):
    """Apply a learned kernel (correlation, mirror boundary), keeping the mean."""
    m = float(img.mean())
    return correlate(img - m, kern, mode="mirror") + m
