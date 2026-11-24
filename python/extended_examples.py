"""Generate extra image panels with the original adaptive_denoise modules.

Run from the repository root:
    python python/extended_examples.py --image data/camera.png --size 256 --seed 0

The original results and figures are not modified. F uses simulated reference
channels supplied by the noise model, not a physical measurement.
"""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from adaptive_denoise import noise
from adaptive_denoise.imageio import REPO, load_test_image
from adaptive_denoise.metrics import psnr, ssim
from adaptive_denoise.pipeline import apply_scenario

CASES = [
    ("A", "periodic", "Adaptive notch / periodic interference"),
    ("B", "banding", "Interline bias / row banding"),
    ("C", "periodic", "Delayed high-band predictor / periodic interference"),
    ("D", "gaussian", "Self-tuning blind spot / white noise"),
    ("Dg", "impulse", "Error-gated self-tuning / random impulses"),
    ("E", "correlated", "Line enhancer / correlated noise"),
    ("F", "banding", "Reference canceller / simulated optical-black"),
    ("F", "telegraph_readout", "Reference canceller / simulated readout reference"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", type=Path, default=REPO / "data" / "camera.png")
    ap.add_argument("--size", type=int, choices=(256, 512), default=256)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=REPO / "results" / "extended_examples")
    args = ap.parse_args()
    if args.seed < 0:
        ap.error("--seed must be nonnegative")
    clean, name = load_test_image(args.image, size=args.size)
    if not np.all(np.isfinite(clean)) or float(clean.var()) < 1e-12:
        ap.error("Use a finite, nonconstant grayscale or RGB source image.")
    outdir = args.out.resolve() / f"{name}_{args.size}_seed{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    records = []
    # One corruption realization per key, shared by all methods using that key.
    corruptions = {key: noise.make(key, clean, seed=args.seed)
                   for key in dict.fromkeys(key for _, key, _ in CASES)}
    for method, key, title in CASES:
        nz = corruptions[key]
        est = apply_scenario(method, nz)
        if est is None or not np.all(np.isfinite(est)):
            raise RuntimeError(f"{method}/{key}: unavailable or nonfinite estimate")
        p0, p1 = psnr(clean, nz.y), psnr(clean, est)
        s0, s1 = ssim(clean, nz.y), ssim(clean, est)
        stem = f"{method}_{key}"
        err0 = np.abs(np.clip(nz.y, 0, 1) - clean)
        err1 = np.abs(np.clip(est, 0, 1) - clean)
        fig, ax = plt.subplots(1, 5, figsize=(17.5, 4.2), layout="constrained")
        panels = [
            (clean, "Clean target", "gray", 1),
            (nz.y, f"Noisy | {p0:.2f} dB", "gray", 1),
            (est, f"Restored | {p1:.2f} dB", "gray", 1),
            (err0, "Input absolute error", "magma", .25),
            (err1, "Output absolute error", "magma", .25),
        ]
        for a, (im, label, cmap, vmax) in zip(ax, panels):
            a.imshow(im, cmap=cmap, vmin=0, vmax=vmax, interpolation="nearest")
            a.set_title(label, fontsize=11)
            a.set_axis_off()
        fig.suptitle(f"{title} | {name} | {args.size} × {args.size} | seed {args.seed}\n"
                     f"PSNR gain {p1-p0:+.2f} dB; SSIM {s0:.3f} → {s1:.3f}; "
                     "error maps share [0, 0.25] scale", fontsize=14)
        fig.savefig(outdir / (stem + ".png"), dpi=160, bbox_inches="tight")
        plt.close(fig)
        records.append(dict(image=name, size=args.size, seed=args.seed,
                            scenario=method, noise=key, input_psnr_db=p0,
                            output_psnr_db=p1, gain_db=p1-p0,
                            input_ssim=s0, output_ssim=s1, figure=stem+".png"))
        print(f"{stem:24s} {p0:6.2f} -> {p1:6.2f} dB; SSIM {s0:.3f} -> {s1:.3f}")
    with (outdir / "metrics.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (outdir / "manifest.json").write_text(json.dumps({
        "image_path": str(args.image.resolve()), "size": args.size, "seed": args.seed,
        "implementation": "adaptive_denoise.pipeline.apply_scenario (original defaults)",
        "noise_parameters": {k: v.params for k, v in corruptions.items()},
        "reference_note": "All references are synthetic; F receives simulated side channels.",
        "metrics": "PSNR and SSIM clip estimates to [0, 1]; errors share display range [0, .25]."
    }, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results: {outdir}")


if __name__ == "__main__":
    main()
