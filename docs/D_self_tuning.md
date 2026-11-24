# D. Adaptive self-tuning filter: the blind-spot predictor

[back to README](../README.md) · [principle](0_principle.md)

<p align="center"><img src="../figures/diagrams/diagram_D_selftuning.png" width="820"></p>

## Idea

The wiring of scenario C, with the other output. The primary, delayed, is the reference, and the **filter
output** $y$ is kept. The filter can reproduce only what is predictable across the delay. When the wanted
signal is the predictable part and the noise is broadband, $y$ is the cleaned signal. The filter tunes itself to
the signal's spectrum without being told where the signal is, hence "self-tuning".

## Image form: a blind spot instead of a delay

In an image the delay becomes a **blind spot**. Pixel $(i,j)$ is predicted from its $(2r+1)\times(2r+1)$
neighbourhood with the centre pixel left out:

$$y(i,j) = \sum_{(a,b) \neq (0,0)} w_{ab}\, d(i+a, j+b), \qquad e(i,j) = d(i,j) - y(i,j).$$

White noise in the centre pixel is uncorrelated with every tap, so it cannot be predicted. The image is
correlated with its neighbours, so it can be. Minimising $E[e^2]$ is therefore the same as minimising the error
of the prediction against the clean image, without ever seeing the clean image. The weights adapt with LMS in
raster order and follow the local statistics as the scan moves across the image.

Two outputs, two uses:

* **filter output $y$**: the image estimate, for broadband noise (Gaussian, Poisson);
* **error output $e$**: the noise estimate. For **sparse** noise it is a detector: small on clean pixels,
  large on impulses.

## The error-gated variant for sparse noise

Impulses break plain LMS twice over. They enter the taps, which spoils the prediction of their neighbours, and
they enter the error, which throws the weights. The gated version turns the error output into a switch:

1. flag $(i,j)$ when $|e| > \max(k\,\hat\sigma_e,\ t_{min})$, with $\hat\sigma_e$ a running robust scale of the
   error ($k$ = 4, $t_{min}$ = 0.1). The floor matters on flat, noise-free areas: there the error scale shrinks
   towards zero, and without a floor every small texture step would be flagged and replaced;
2. output $y$ on flagged pixels and the untouched $d$ on clean ones;
3. adapt only on clean pixels;
4. on the next pass, take the taps from the previous output, so flagged neighbours no longer spoil the
   prediction. This matters for bursts, whose neighbours along the row are corrupted too.

Clean pixels are passed through unchanged. That is the advantage over any smoothing filter, and the reason this
variant beats the 3 x 3 median on random-valued impulses and on bursts.

## Implementation

| | Python | MATLAB |
|---|---|---|
| self-tuning filter | `scenario_d.self_tuning(img, r=2, alpha=0.01, passes=2)` | `self_tuning(img, r, alpha, passes)` |
| error-gated | `scenario_d.self_tuning_gated(img, r=2, alpha=0.01, k=4, passes=3, t_min=0.1)` | `self_tuning_gated(img, r, alpha, k, passes, t_min)` |
| the predictor | `predictor.blindspot_lms(img, r, hole, alpha, mu2, passes, update)` | `blindspot_lms(...)` |

Defaults: a 5 x 5 window (24 taps), normalised step $\alpha = 0.01$ (misadjustment about 0.5 %), two raster
passes, image mean removed.

## Results

<img src="../figures/results/fig_D_image.png" width="900">

| noise | noisy | D | D gated | median 3 x 3 | adaptive median | Wiener 5 x 5 |
|---|---|---|---|---|---|---|
| Gaussian, $\sigma$ = 20/255 | 22.42 | 27.15 | - | 26.95 | 24.68 | **28.82** |
| Poisson, peak 60 | 20.97 | **26.83** | - | 26.10 | 23.61 | 24.76 |
| random-valued impulses, 10 % | 17.84 | 24.42 | **30.94** | 29.58 | 25.18 | 17.96 |
| bursts of impulses | 23.68 | 25.81 | **31.76** | 30.08 | 27.77 | 23.68 |
| salt and pepper, 10 % | 14.85 | 23.34 | 32.23 | 29.50 | **33.16** | 14.91 |

(PSNR in dB. Wiener 5 x 5 uses the noise level estimated from the image.)

* **Gaussian noise:** +4.7 dB. D trails a local Wiener filter by 1.7 dB. The Wiener filter adapts its
  smoothing to the local variance at every pixel; the predictor carries one set of weights through the scan
  and can only follow slowly.
* **Poisson noise:** D beats both. A single global noise level does not fit signal-dependent noise, while the
  predictor never needs one.
* **Impulses:** the gated predictor flags 72 % of the impulses with 1.0 % false alarms, mostly on strong edges
  (panel g). The impulses it misses are the ones whose random value landed near the true pixel: of those that
  deviate by more than 0.1, it flags 89 %. Replacing only the flagged pixels gives 30.94 dB and SSIM 0.913,
  against 0.847 for the median.
* **Bursts:** 31.76 dB. The third pass takes its taps from the second pass's output, so a run of corrupted
  pixels along a row no longer spoils the prediction of its own members.
* **Salt and pepper:** the adaptive median wins because those pixels sit at exactly 0 or 1, a give-away the
  generic error detector does not use.

<img src="../figures/results/fig_D_theory.png" width="900">

* **Panel a:** the learned weights sum to 0.96 and concentrate on the four nearest neighbours. This is a
  smoothing kernel that the data chose.
* **Panel b:** the learning curve converges within the first rows. The error never falls below the noise
  variance, which is exactly the part the blind spot makes unpredictable. Rows with more texture have a
  larger prediction error.
* **Panel c:** 24 or 48 taps are better than 8. Over a wide range of steps (0.003 to 0.03) the result changes
  by less than 0.1 dB.

## Limits

* D needs **pixel-wise independent noise**. With correlated noise, the neighbours predict the noise too, and D
  loses 0.4 dB. The blind spot must then grow, which is scenario E.
* Structured interference (stripes, banding, readout telegraph) is predictable from the neighbours and is kept.
  Those cases belong to A, B, C and F.
* Pixel RTS noise in a single frame is too weak and too similar to texture to be flagged reliably. Over a frame
  sequence, each pixel's switching history would serve as the reference.
* **Impulse density.** The running error scale grows with the fraction of corrupted pixels. With $k$ = 4 the
  threshold rises above the impulses beyond about 20 %, and at 30 % the gate stops flagging altogether. $k$ = 3
  holds up to 25 % and stays ahead of the median there:

  <img src="../figures/examples/example_D_density.png" width="680">

  Use $k$ = 4 up to about 10 % and $k$ = 3 above ([sweep](../results/gated_density_sweep.csv)).

## Try it

```python
from adaptive_denoise import noise, scenario_d
from adaptive_denoise.imageio import load_test_image
from adaptive_denoise.metrics import psnr

x, _ = load_test_image()
nz = noise.make("poisson", x)
out = scenario_d.self_tuning(nz.y)                     # broadband noise: keep the prediction y
print(f"{psnr(x, nz.y):.2f} dB -> {psnr(x, out):.2f} dB")       # 20.97 dB -> 26.83 dB

nz = noise.make("impulse", x)
out, flags = scenario_d.self_tuning_gated(nz.y)        # sparse noise: replace flagged pixels only
print(f"{psnr(x, out):.2f} dB, {flags.mean():.1%} replaced")      # 30.94 dB, 8.0% replaced
```

```matlab
x = load_test_image();
nz = make_noisy('impulse', x);
[out, flags] = self_tuning_gated(nz.y);                % k = 4; use self_tuning_gated(nz.y, [], [], 3) above ~10 %
fprintf('%.2f dB -> %.2f dB\n', psnr_db(x, nz.y), psnr_db(x, out));
```

## Application example: impulses on fine texture

<img src="../figures/examples/example_D_impulses_texture.png" width="100%">

Bit errors (10 % random-valued impulses) and dead or hot pixels on a gravel texture. The median smooths the
texture along with the impulses (27.32 dB). The gated predictor changes only the pixels it flags and keeps the
rest bit-exact: 30.99 dB, SSIM 0.944. Details in [examples](examples.md#d-bit-errors-dead-and-hot-pixels-on-fine-texture).

## Implementation atlas: controlled image example

![Scenario D data flow and synthetic image comparison](../figures/atlas/D_implementation.svg)

**Worked interpretation.** With a predicted centre of 0.48, target 0.92, and robust scale 0.05, the threshold at k = 4 is max(0.20, 0.1) = 0.20. The absolute error 0.44 triggers replacement and skips adaptation. With target 0.53 the error 0.05 permits the ordinary update. On a flat area where the robust scale has fallen to 0.01, the threshold is the floor 0.1, not 0.04. The mask is predicted from errors, not supplied by the simulator. The blind-spot tap exclusion alone is not a strict independence guarantee at reflected boundaries or over repeated adaptation passes.

Settings and PSNR are printed in the panel. More worked examples: [implementation atlas](implementation_atlas.md#2-the-six-scenarios-in-images).
