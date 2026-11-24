"""Run every scenario and every baseline on every noise model; write the results tables.

    python run_benchmark.py            # writes results/benchmark_python.csv and results/benchmark_python.md

All parameters are the fixed defaults of ``adaptive_denoise.pipeline`` - nothing is tuned on the clean image.
Outputs are cached in results/cache/ (not tracked by git) for make_figures.py.
"""
import csv
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adaptive_denoise import noise                                                    # noqa: E402
from adaptive_denoise.imageio import load_test_image, REPO                             # noqa: E402
from adaptive_denoise.metrics import psnr, ssim                                        # noqa: E402
from adaptive_denoise.pipeline import SCENARIOS, SCENARIO_NAMES, BASELINES, apply_scenario, cascade   # noqa: E402

RESULTS = REPO / "results"
CACHE = RESULTS / "cache"


def main():
    RESULTS.mkdir(exist_ok=True)
    CACHE.mkdir(exist_ok=True)
    x, name = load_test_image()
    np.save(CACHE / "clean.npy", x.astype(np.float32))
    methods = SCENARIOS + list(BASELINES)
    rows = []
    t_all = time.time()
    for key in noise.ORDER:
        nz = noise.make(key, x)
        np.save(CACHE / f"{key}__noisy.npy", nz.y.astype(np.float32))
        base_p, base_s = psnr(x, nz.y), ssim(x, nz.y)
        rows.append(dict(noise=key, method="noisy", psnr=base_p, ssim=base_s, gain=0.0, seconds=0.0))
        print(f"{key:18s} noisy {base_p:6.2f} dB", flush=True)
        for m in methods:
            t0 = time.time()
            out = apply_scenario(m, nz) if m in SCENARIOS else BASELINES[m](nz.y)
            dt = time.time() - t0
            if out is None:
                rows.append(dict(noise=key, method=m, psnr=np.nan, ssim=np.nan, gain=np.nan, seconds=0.0))
                continue
            np.save(CACHE / f"{key}__{m}.npy", out.astype(np.float32))
            p, s = psnr(x, out), ssim(x, out)
            rows.append(dict(noise=key, method=m, psnr=p, ssim=s, gain=p - base_p, seconds=dt))
            print(f"    {m:8s} {p:6.2f} dB ({p - base_p:+6.2f})  SSIM {s:.3f}  {dt:5.1f} s", flush=True)

    nz = noise.mixed(x)
    stages = cascade(nz)
    for k, (label, im) in enumerate(stages):
        np.save(CACHE / f"mixed__stage{k}.npy", im.astype(np.float32))
        rows.append(dict(noise="mixed", method=f"stage{k}: " + label.replace("\n", " "),
                         psnr=psnr(x, im), ssim=ssim(x, im), gain=psnr(x, im) - psnr(x, nz.y), seconds=0.0))
    for m, f in BASELINES.items():
        out = f(nz.y)
        rows.append(dict(noise="mixed", method=m, psnr=psnr(x, out), ssim=ssim(x, out),
                         gain=psnr(x, out) - psnr(x, nz.y), seconds=0.0))

    with open(RESULTS / "benchmark_python.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["noise", "method", "psnr", "ssim", "gain", "seconds"])
        wr.writeheader()
        for r in rows:
            wr.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
    write_markdown(rows, name)
    print(f"total {time.time() - t_all:.0f} s")


def write_markdown(rows, image_name):
    methods = SCENARIOS + list(BASELINES)
    head = ["Noise", "Noisy"] + [m if m != "Dg" else "D gated" for m in methods]
    lines = [f"PSNR in dB on the 512 x 512 `{image_name}` image (gain over the noisy input in brackets). "
             "Bold: best of the row (when it gains more than 0.5 dB). "
             "n/a: the scenario needs a reference that this noise does not provide.", "",
             "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for key in noise.ORDER:
        r = {d["method"]: d for d in rows if d["noise"] == key}
        best = max(r[m]["psnr"] for m in methods if not np.isnan(r[m]["psnr"]))
        cells = [noise.LABELS[key], f"{r['noisy']['psnr']:.2f}"]
        for m in methods:
            p = r[m]["psnr"]
            if np.isnan(p):
                cells.append("n/a")
            else:
                g = r[m]["gain"]
                c = f"{p:.2f} ({'0.0' if abs(g) < 0.05 else f'{g:+.1f}'})"
                cells.append(f"**{c}**" if p == best and g > 0.5 else c)
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "All noises at once, scenarios chained:", "", "| Stage | PSNR (dB) | SSIM |", "|---|---|---|"]
    for d in rows:
        if d["noise"] == "mixed":
            lines.append(f"| {d['method']} | {d['psnr']:.2f} | {d['ssim']:.3f} |")
    (RESULTS / "benchmark_python.md").write_text("\n".join(lines) + "\n")


def markdown_from_csv():
    """Rebuild results/benchmark_python.md from the CSV without rerunning anything."""
    rows = []
    with open(RESULTS / "benchmark_python.csv") as fh:
        for r in csv.DictReader(fh):
            rows.append(dict(noise=r["noise"], method=r["method"], psnr=float(r["psnr"]), ssim=float(r["ssim"]),
                             gain=float(r["gain"]), seconds=float(r["seconds"])))
    write_markdown(rows, load_test_image()[1])


if __name__ == "__main__":
    if "--markdown-only" in sys.argv:
        markdown_from_csv()
    else:
        main()
