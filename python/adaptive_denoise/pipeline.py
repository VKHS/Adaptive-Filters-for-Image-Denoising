"""Running the scenarios on any noisy image, alone or chained.

``apply_scenario`` runs one scenario with its default (fixed, documented) parameters. Nothing is tuned on
the clean image. A scenario that needs side information the noise model does not provide returns None.

``cascade`` chains them for an image that carries every corruption at once: each stage removes the
interference it is built for, using the reference it needs, and hands the rest on.
"""
import numpy as np

from . import scenario_a, scenario_b, scenario_c, scenario_d, scenario_e, scenario_f
from . import baselines
from .inverse_model import dead_leaves, train_inverse_filter, apply_filter
from .noise import gaussian_blur

SCENARIOS = ["A", "B", "C", "D", "Dg", "E", "F"]
SCENARIO_NAMES = {
    "A": "A  adaptive notch",
    "B": "B  bias / drift canceller",
    "C": "C  no-reference canceller",
    "D": "D  self-tuning filter",
    "Dg": "D  error-gated",
    "E": "E  line enhancer",
    "F": "F  reference canceller",
}
BASELINES = {"median3": baselines.median3, "AMF": baselines.adaptive_median, "Wiener5": baselines.local_wiener}


def apply_scenario(key, nz):
    """Run scenario ``key`` on the Noisy record ``nz``. Returns the output image or None (not applicable)."""
    y = nz.y
    if key == "A":
        return scenario_a.adaptive_notch(y, mu2=0.001)[0]
    if key == "B":
        return scenario_b.interline_canceller(y, mu2=0.001, hp_rows=16)[0]
    if key == "C":
        return scenario_c.subband_canceller(y)
    if key == "D":
        return scenario_d.self_tuning(y)
    if key == "Dg":
        return scenario_d.self_tuning_gated(y)[0]
    if key == "E":
        return scenario_e.line_enhancer(y)
    if key == "F":
        s = nz.side
        if "ob" in s and "ref_out" not in s:
            w = scenario_f.train_row_weight(s["dark"], s["dark_ob"])
            return scenario_f.row_reference_canceller(y, s["ob"], w)
        if "ref_out" in s and "ob" not in s:
            return scenario_f.channel_reference_canceller(y, s["ref_out"], train=(s["dark"], s["dark_ref"]))[0]
        return None
    raise KeyError(key)


def calibrate_inverse(psf_sigma, noise_sigma, r=4, seed=5):
    """Learn an inverse (Wiener-deconvolution) kernel from a calibration target seen through the same blur."""
    tgt = dead_leaves(seed=seed)
    rng = np.random.default_rng(seed + 1)
    cal = gaussian_blur(tgt, psf_sigma) + noise_sigma * rng.standard_normal(tgt.shape)
    return train_inverse_filter(tgt, cal, r=r, alpha=0.02, passes=2)


def cascade(nz, deblur=False):
    """Chain the scenarios on an image with every corruption. Returns a list of (stage label, image).

    Order: interference with a physical reference first (F), then the deterministic periodic part (A), then
    the sparse part (D, error-gated), then the broadband remainder (E). Deblurring at the end is optional:
    after denoising, the inverse filter amplifies the residual noise more than it restores detail.
    """
    s = nz.side
    stages = [("input", nz.y)]
    y = nz.y
    w = scenario_f.train_row_weight(s["dark"], s["dark_ob"])
    y = scenario_f.row_reference_canceller(y, s["ob"], w)
    stages.append(("F: optical-black ref.\n(row banding)", y))
    y = scenario_f.channel_reference_canceller(y, s["ref_out"], train=(s["dark"], s["dark_ref"]))[0]
    stages.append(("F: reference output\n(readout telegraph)", y))
    y = scenario_a.adaptive_notch(y, mu2=0.001)[0]
    stages.append(("A: adaptive notch\n(periodic)", y))
    y = scenario_d.self_tuning_gated(y)[0]
    stages.append(("D, error-gated\n(impulses, bursts)", y))
    y = scenario_e.line_enhancer(y)
    stages.append(("E: line enhancer\n(broadband rest)", y))
    if deblur:
        k = calibrate_inverse(s["psf_sigma"], 0.01)
        y = apply_filter(y, k)
        stages.append(("inverse model\n(blur)", y))
    return stages
