"""Noise and interference models.

Every model takes a clean image ``x`` (float, [0, 1]) and a ``numpy.random.Generator`` and returns a
:class:`Noisy` record with the corrupted image and, where the physics provides one, the *side information*
that a real system would measure together with the image (optical-black reference columns, a reference
output channel, a dark calibration frame, a known point-spread function). Scenario F uses that side
information; the other scenarios use the image only.

The raster order is row-major: row ``i`` is read left to right, then row ``i + 1``. Processes that live
in readout time (telegraph switching, transmission bursts) are generated along that order.

Images are not clipped after corruption. Metrics clip the *estimate* to [0, 1].
"""
from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import convolve1d

# Default parameters (pixel values in [0, 1]). The MATLAB code uses the same numbers.
DEFAULTS = {
    "gaussian": dict(sigma=20 / 255),
    "correlated": dict(sigma=20 / 255, corr_px=1.0),
    "poisson": dict(peak=60.0),
    "blur": dict(psf_sigma=1.6, sigma=0.005),
    "salt_pepper": dict(density=0.10),
    "impulse": dict(density=0.10),
    "burst": dict(p_gb=0.004, p_bg=0.125, p_hit=0.9),
    "telegraph_pixel": dict(fraction=0.05, amp_min=0.10, amp_max=0.30, sigma=0.01),
    "telegraph_readout": dict(amp=0.06, dwell=60.0, sigma=0.01, ref_gain=0.8, ref_sigma=0.01),
    "periodic": dict(components=((0.10, 0.0, 0.0925, 0.7),    # (amplitude, u [cyc/row], v [cyc/col], phase)
                                 (0.04, 0.0, 0.1850, 0.3),
                                 (0.06, 0.137, 0.061, 1.9))),
    "banding": dict(sigma_row=0.05, sigma=0.01, n_ob=16),
}

LABELS = {
    "gaussian": "Gaussian (white)",
    "correlated": "Gaussian (correlated)",
    "poisson": "Poisson (shot)",
    "blur": "Blur + weak noise",
    "salt_pepper": "Salt & pepper",
    "impulse": "Impulse (random-valued)",
    "burst": "Burst (bursty impulses)",
    "telegraph_pixel": "Telegraph (pixel RTS)",
    "telegraph_readout": "Telegraph (readout)",
    "periodic": "Periodic interference",
    "banding": "Row banding",
    "mixed": "All noises together",
}

ORDER = ["gaussian", "correlated", "poisson", "blur", "salt_pepper", "impulse", "burst",
         "telegraph_pixel", "telegraph_readout", "periodic", "banding"]


@dataclass
class Noisy:
    key: str
    label: str
    y: np.ndarray
    side: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------------------------- helpers
def two_state_chain(n, p01, p10, rng, start=None):
    """Two-state Markov chain of length n (states 0/1), generated from geometric run lengths.

    p01 = P(0 -> 1) and p10 = P(1 -> 0) per sample, so the mean dwell times are 1/p01 and 1/p10.
    """
    pi1 = p01 / (p01 + p10)
    state = int(rng.random() < pi1) if start is None else int(start)
    out = np.empty(n, dtype=np.int8)
    pos = 0
    while pos < n:
        p_leave = p01 if state == 0 else p10
        run = int(np.floor(np.log(1.0 - rng.random()) / np.log(1.0 - p_leave))) + 1
        out[pos:pos + run] = state
        pos += run
        state = 1 - state
    return out


def gaussian_kernel(sigma, radius=None):
    radius = int(np.ceil(3.5 * sigma)) if radius is None else radius
    t = np.arange(-radius, radius + 1)
    g = np.exp(-t ** 2 / (2.0 * sigma ** 2))
    return g / g.sum()


def gaussian_blur(img, sigma):
    g = gaussian_kernel(sigma)
    out = convolve1d(img, g, axis=0, mode="reflect")
    return convolve1d(out, g, axis=1, mode="reflect")


def plane_waves(shape, components):
    H, W = shape
    i, j = np.mgrid[0:H, 0:W]
    p = np.zeros(shape)
    for A, u, v, ph in components:
        p += A * np.cos(2 * np.pi * (u * i + v * j) + ph)
    return p


# ----------------------------------------------------------------------------------------------- models
def gaussian(x, rng, sigma=DEFAULTS["gaussian"]["sigma"]):
    """Additive white Gaussian noise."""
    return Noisy("gaussian", LABELS["gaussian"], x + sigma * rng.standard_normal(x.shape), params=dict(sigma=sigma))


def correlated(x, rng, sigma=DEFAULTS["correlated"]["sigma"], corr_px=DEFAULTS["correlated"]["corr_px"]):
    """Spatially correlated Gaussian noise: white noise blurred by a Gaussian of ``corr_px`` pixels."""
    n = gaussian_blur(rng.standard_normal(x.shape), corr_px)
    n *= sigma / n.std()
    return Noisy("correlated", LABELS["correlated"], x + n, params=dict(sigma=sigma, corr_px=corr_px))


def poisson(x, rng, peak=DEFAULTS["poisson"]["peak"]):
    """Photon shot noise: counts ~ Poisson(peak * x), image = counts / peak. Variance = x / peak."""
    return Noisy("poisson", LABELS["poisson"], rng.poisson(peak * x) / peak, params=dict(peak=peak))


def blur(x, rng, psf_sigma=DEFAULTS["blur"]["psf_sigma"], sigma=DEFAULTS["blur"]["sigma"]):
    """Gaussian point-spread function followed by weak white noise. Blur is a convolution, not additive noise."""
    y = gaussian_blur(x, psf_sigma) + sigma * rng.standard_normal(x.shape)
    return Noisy("blur", LABELS["blur"], y, side=dict(psf_sigma=psf_sigma, noise_sigma=sigma),
                 params=dict(psf_sigma=psf_sigma, sigma=sigma))


def salt_pepper(x, rng, density=DEFAULTS["salt_pepper"]["density"]):
    """A fraction ``density`` of pixels is set to 0 or 1 with equal probability."""
    y = x.copy()
    hit = rng.random(x.shape) < density
    y[hit] = (rng.random(int(hit.sum())) < 0.5).astype(float)
    return Noisy("salt_pepper", LABELS["salt_pepper"], y, side=dict(mask=hit), params=dict(density=density))


def impulse(x, rng, density=DEFAULTS["impulse"]["density"]):
    """Random-valued impulse noise: a fraction ``density`` of pixels is replaced by U(0, 1) values."""
    y = x.copy()
    hit = rng.random(x.shape) < density
    y[hit] = rng.random(int(hit.sum()))
    return Noisy("impulse", LABELS["impulse"], y, side=dict(mask=hit), params=dict(density=density))


def burst(x, rng, p_gb=DEFAULTS["burst"]["p_gb"], p_bg=DEFAULTS["burst"]["p_bg"], p_hit=DEFAULTS["burst"]["p_hit"]):
    """Bursts of impulses along the raster (two-state good/bad channel).

    In the bad state each pixel is replaced by a U(0, 1) value with probability ``p_hit``. Mean burst
    length is 1/p_bg pixels and the bad state covers p_gb / (p_gb + p_bg) of the raster.
    """
    H, W = x.shape
    bad = two_state_chain(H * W, p_gb, p_bg, rng).reshape(H, W).astype(bool)
    hit = bad & (rng.random(x.shape) < p_hit)
    y = x.copy()
    y[hit] = rng.random(int(hit.sum()))
    return Noisy("burst", LABELS["burst"], y, side=dict(mask=hit),
                 params=dict(p_gb=p_gb, p_bg=p_bg, p_hit=p_hit))


def telegraph_pixel(x, rng, fraction=DEFAULTS["telegraph_pixel"]["fraction"],
                    amp_min=DEFAULTS["telegraph_pixel"]["amp_min"], amp_max=DEFAULTS["telegraph_pixel"]["amp_max"],
                    sigma=DEFAULTS["telegraph_pixel"]["sigma"]):
    """Random telegraph signal (RTS) pixels, one frame.

    A fraction of pixels switches between two levels +a/2 and -a/2 (a ~ U(amp_min, amp_max)); in a single
    frame each RTS pixel is caught in one of its two states. Weak white read noise is added everywhere.
    """
    rts = rng.random(x.shape) < fraction
    a = rng.uniform(amp_min, amp_max, x.shape)
    state = np.where(rng.random(x.shape) < 0.5, 0.5, -0.5)
    y = x + rts * a * state + sigma * rng.standard_normal(x.shape)
    return Noisy("telegraph_pixel", LABELS["telegraph_pixel"], y, side=dict(mask=rts),
                 params=dict(fraction=fraction, amp_min=amp_min, amp_max=amp_max, sigma=sigma))


def telegraph_readout(x, rng, amp=DEFAULTS["telegraph_readout"]["amp"], dwell=DEFAULTS["telegraph_readout"]["dwell"],
                      sigma=DEFAULTS["telegraph_readout"]["sigma"], ref_gain=DEFAULTS["telegraph_readout"]["ref_gain"],
                      ref_sigma=DEFAULTS["telegraph_readout"]["ref_sigma"]):
    """Telegraph (popcorn) noise of the shared output amplifier, in readout time.

    Every pixel passes through the same amplifier, so a two-level offset +-amp that switches with mean
    dwell ``dwell`` pixels draws horizontal streaks. A reference output channel, read at the same instants,
    sees ``ref_gain`` times the same switching plus its own noise: that is the side information.
    """
    H, W = x.shape
    t = amp * (2.0 * two_state_chain(H * W, 1.0 / dwell, 1.0 / dwell, rng) - 1.0)
    t = t.reshape(H, W)
    y = x + t + sigma * rng.standard_normal(x.shape)
    ref = ref_gain * t + ref_sigma * rng.standard_normal(x.shape)
    td = amp * (2.0 * two_state_chain(H * W, 1.0 / dwell, 1.0 / dwell, rng) - 1.0)
    td = td.reshape(H, W)
    dark = td + sigma * rng.standard_normal(x.shape)
    dark_ref = ref_gain * td + ref_sigma * rng.standard_normal(x.shape)
    return Noisy("telegraph_readout", LABELS["telegraph_readout"], y,
                 side=dict(ref_out=ref, dark=dark, dark_ref=dark_ref, truth=t),
                 params=dict(amp=amp, dwell=dwell, sigma=sigma, ref_gain=ref_gain, ref_sigma=ref_sigma))


def periodic(x, rng, components=DEFAULTS["periodic"]["components"]):
    """Sum of 2-D sinusoidal interference patterns A cos(2 pi (u i + v j) + phase): stripes, harmonics, moire."""
    p = plane_waves(x.shape, components)
    return Noisy("periodic", LABELS["periodic"], x + p, side=dict(freqs=[(u, v) for _, u, v, _ in components], truth=p),
                 params=dict(components=components))


def banding(x, rng, sigma_row=DEFAULTS["banding"]["sigma_row"], sigma=DEFAULTS["banding"]["sigma"],
            n_ob=DEFAULTS["banding"]["n_ob"]):
    """Row banding: one random offset per row (shared row readout) plus white read noise.

    The sensor also has ``n_ob`` optical-black (masked) columns per row; they see the same row offset and
    their own read noise, but no light. A dark frame (shutter closed) with its own optical-black columns is
    returned as well, for calibration.
    """
    H, W = x.shape
    c = sigma_row * rng.standard_normal(H)
    y = x + c[:, None] + sigma * rng.standard_normal(x.shape)
    ob = c[:, None] + sigma * rng.standard_normal((H, n_ob))
    cd = sigma_row * rng.standard_normal(H)
    dark = cd[:, None] + sigma * rng.standard_normal(x.shape)
    dark_ob = cd[:, None] + sigma * rng.standard_normal((H, n_ob))
    return Noisy("banding", LABELS["banding"], y, side=dict(ob=ob, dark=dark, dark_ob=dark_ob, truth=c),
                 params=dict(sigma_row=sigma_row, sigma=sigma, n_ob=n_ob))


MODELS = {
    "gaussian": gaussian, "correlated": correlated, "poisson": poisson, "blur": blur,
    "salt_pepper": salt_pepper, "impulse": impulse, "burst": burst, "telegraph_pixel": telegraph_pixel,
    "telegraph_readout": telegraph_readout, "periodic": periodic, "banding": banding,
}


def make(key, x, seed=0, **params):
    """Corrupt ``x`` with noise model ``key`` using a seed derived from ``seed`` and the model's position."""
    rng = np.random.default_rng(1000 * (ORDER.index(key) + 1) + seed)
    return MODELS[key](x, rng, **params)


def make_all(x, seed=0):
    return {k: make(k, x, seed) for k in ORDER}


def mixed(x, seed=0):
    """All corruptions at once, at reduced strength, in physical order.

    optics (blur) -> photon shot noise -> pixel RTS -> row banding and readout telegraph (with their
    references) -> periodic pickup -> white read noise -> transmission errors (bursts, impulses, salt & pepper).
    """
    rng = np.random.default_rng(99000 + seed)
    H, W = x.shape
    y = gaussian_blur(x, 0.8)
    y = rng.poisson(200.0 * np.clip(y, 0, None)) / 200.0
    rts = rng.random(x.shape) < 0.02
    y = y + rts * rng.uniform(0.1, 0.3, x.shape) * np.where(rng.random(x.shape) < 0.5, 0.5, -0.5)
    c = 0.04 * rng.standard_normal(H)
    t = 0.04 * (2.0 * two_state_chain(H * W, 1 / 60.0, 1 / 60.0, rng) - 1.0)
    y = y + c[:, None] + t.reshape(H, W)
    comps = tuple((0.7 * A, u, v, ph) for A, u, v, ph in DEFAULTS["periodic"]["components"])
    y = y + plane_waves(x.shape, comps)
    y = y + 0.02 * rng.standard_normal(x.shape)
    ob = c[:, None] + 0.02 * rng.standard_normal((H, 16))
    ref = 0.8 * t.reshape(H, W) + 0.01 * rng.standard_normal(x.shape)
    cd = 0.04 * rng.standard_normal(H)
    td = 0.04 * (2.0 * two_state_chain(H * W, 1 / 60.0, 1 / 60.0, rng) - 1.0)
    dark = cd[:, None] + td.reshape(H, W) + 0.02 * rng.standard_normal(x.shape)
    dark_ob = cd[:, None] + 0.02 * rng.standard_normal((H, 16))
    dark_ref = 0.8 * td.reshape(H, W) + 0.01 * rng.standard_normal(x.shape)
    bad = two_state_chain(H * W, 0.0015, 0.125, rng).reshape(H, W).astype(bool) & (rng.random(x.shape) < 0.9)
    y[bad] = rng.random(int(bad.sum()))
    imp = rng.random(x.shape) < 0.01
    y[imp] = rng.random(int(imp.sum()))
    sp = rng.random(x.shape) < 0.02
    y[sp] = (rng.random(int(sp.sum())) < 0.5).astype(float)
    return Noisy("mixed", LABELS["mixed"], y,
                 side=dict(ob=ob, dark=dark, dark_ob=dark_ob, ref_out=ref, dark_ref=dark_ref, psf_sigma=0.8,
                           noise_sigma=0.02, mask=bad | imp | sp, freqs=[(u, v) for _, u, v, _ in comps]),
                 params=dict(note="blur 0.8, Poisson peak 200, RTS 2%, banding 0.04, telegraph 0.04, "
                                  "periodic x0.7, read noise 0.02, bursts, impulses 1%, salt & pepper 2%"))
