"""Image-quality metrics and a robust noise-level estimate.

All three are written out explicitly (rather than taken from a library) so that the MATLAB versions in
``matlab/`` compute exactly the same quantities.
"""
import numpy as np
from scipy.ndimage import convolve1d


def psnr(ref, est, clip=True):
    """Peak signal-to-noise ratio in dB for images in [0, 1]. The estimate is clipped to [0, 1] first."""
    est = np.clip(est, 0.0, 1.0) if clip else est
    mse = np.mean((np.asarray(ref, float) - est) ** 2)
    return float(10.0 * np.log10(1.0 / mse))


def _gauss_filter(img, sigma=1.5, radius=5):
    t = np.arange(-radius, radius + 1)
    g = np.exp(-t ** 2 / (2 * sigma ** 2))
    g /= g.sum()
    out = convolve1d(img, g, axis=0, mode="reflect")
    return convolve1d(out, g, axis=1, mode="reflect")


def ssim(ref, est, clip=True):
    """Structural similarity (11 x 11 Gaussian window, sigma 1.5, K1 = 0.01, K2 = 0.03, range 1).

    The mean is taken over the image without a 5-pixel border, where the window would leave the image.
    """
    x = np.asarray(ref, float)
    y = np.clip(est, 0.0, 1.0) if clip else np.asarray(est, float)
    C1, C2 = (0.01 * 1.0) ** 2, (0.03 * 1.0) ** 2
    mx, my = _gauss_filter(x), _gauss_filter(y)
    sxx = _gauss_filter(x * x) - mx * mx
    syy = _gauss_filter(y * y) - my * my
    sxy = _gauss_filter(x * y) - mx * my
    s = ((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx ** 2 + my ** 2 + C1) * (sxx + syy + C2))
    return float(s[5:-5, 5:-5].mean())


def estimate_noise_sigma(img):
    """Robust estimate of the standard deviation of white noise.

    Uses the finest diagonal Haar detail: d = (a - b - c + e) / 2 on each 2 x 2 block, which removes
    constant and linear image content, and sigma = median(|d|) / 0.6745.
    """
    x = np.asarray(img, float)
    H, W = (x.shape[0] // 2) * 2, (x.shape[1] // 2) * 2
    x = x[:H, :W]
    d = (x[0::2, 0::2] - x[0::2, 1::2] - x[1::2, 0::2] + x[1::2, 1::2]) / 2.0
    return float(np.median(np.abs(d)) / 0.6745)
