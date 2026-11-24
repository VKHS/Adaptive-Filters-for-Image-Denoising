# Verification strategy and evidence

[Hardware overview](../README.md) · [Golden vectors](../vectors/README.md) · [Executed reference-model record](../results/reference_smoke.json)

## Scenario smoke coverage

| Test | Transactions | Core checks |
|---|---:|---|
| A | 104 | Quadrature sign, learned amplitude, frozen clean offset |
| B | 56 | Positive/negative drift, sign updates, zero-error hold, estimate/replay and slow offset |
| C | 384 | Causal warm-up, two row boundaries, delayed FIR, periodic rejection, target vs primary distinction |
| D | 40 | Ordinary prediction and gated selection, high positive/negative errors, excluded centre, clean-only update |
| E | 144 | 9×9 with 5×5 hole, poisoned excluded region, coherent texture prediction, freeze |
| F | 210 | Independent calibration phase, signed reference, frozen inference, both saturation limits |
| Frontends | directed checks | Phase progression/hold and row restart, cardinal quadratures, signed OB mean, scale update/hold |
| Window | 40 expected windows | Interior windows over two frames, coordinates, ordering, stalled ready/valid |
| Gaussian | directed checks | Signed DC preservation and centre impulse response |

The six core testbenches read golden signed integer output, prediction, error and flag for each transaction. B maps prediction to reported bias and uses zero for its unused error. Each test deliberately holds out_ready low for 1–3 cycles while checking that the registered response is unchanged and that no new input is accepted. Each checks reset and includes a watchdog. The additional helpers have directed testbenches.

## How to interpret status

The committed JSON records executed integer-reference arithmetic and assertions, **not HDL simulation**. The independent Python replay checks all committed golden vectors. Icarus Verilog testbenches verify the actual RTL when run. Yosys elaboration/structural synthesis checks are separate from functional verification and do not establish FPGA timing or utilization. The smoke parameters are intentionally small/fast (not the original image benchmark parameter policy); they cannot establish camera-image PSNR or numerical equivalence with Python/MATLAB.

## Run locally

```bash
python3 hardware/model/fixed_model.py
bash hardware/run_smoke.sh
bash hardware/run_synth.sh
```

For deeper verification add randomized legal parameter/input tests, formal ready/valid invariants, frame-border comparisons, reset mid-transaction tests, multi-harmonic A and multi-tap F tests, overflow stress, multi-image fixed-point PSNR/SSIM and hardware-in-the-loop acquisition. These are follow-on tasks, not results already obtained.
