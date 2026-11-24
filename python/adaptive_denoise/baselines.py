"""Non-adaptive reference filters used for comparison. Written out explicitly so the MATLAB versions match."""
import numpy as np
from scipy.ndimage import median_filter, minimum_filter, maximum_filter, uniform_filter

from .metrics import estimate_noise_sigma


def median3(img):
    """3 x 3 median filter (mirror boundary)."""
    return median_filter(img, size=3, mode="mirror")


def adaptive_median(img, smax=7):
    """Adaptive median filter: grow the window (3, 5, ..., smax) until its median is not an extreme value;
    keep the pixel if it is not an extreme of that window, otherwise replace it by the median."""
    out = median_filter(img, size=smax, mode="mirror")
    done = np.zeros(img.shape, bool)
    for s in range(3, smax + 1, 2):
        zmed = median_filter(img, size=s, mode="mirror")
        zmin = minimum_filter(img, size=s, mode="mirror")
        zmax = maximum_filter(img, size=s, mode="mirror")
        ok = (zmin < zmed) & (zmed < zmax) & ~done
        keep = ok & (zmin < img) & (img < zmax)
        out[keep] = img[keep]
        rep = ok & ~keep
        out[rep] = zmed[rep]
        done |= ok
    return out


def local_wiener(img, size=5, sigma=None):
    """Local-statistics Wiener filter: m + max(v - s^2, 0) / max(v, s^2) * (y - m) in a size x size window.
    The noise variance s^2 is estimated from the image when not given."""
    s2 = estimate_noise_sigma(img) ** 2 if sigma is None else sigma ** 2
    m = uniform_filter(img, size, mode="mirror")
    v = uniform_filter(img * img, size, mode="mirror") - m * m
    return m + np.maximum(v - s2, 0.0) / np.maximum(v, s2) * (img - m)
