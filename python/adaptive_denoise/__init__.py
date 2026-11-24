"""Adaptive noise cancelling for images: the six LMS canceller configurations.

Modules
-------
noise          eleven noise / interference models and the all-noise mixture, with side information
scenario_a     adaptive notch filter (synthetic sinusoidal reference)
scenario_b     bias / drift canceller (constant reference)
scenario_c     periodic interference without a reference (delayed primary, error output)
scenario_d     self-tuning filter (blind-spot predictor, filter output; error-gated variant)
scenario_e     adaptive line enhancer (window size and blind spot; 1-D theory)
scenario_f     reference-sensor canceller (optical-black columns, reference output channel)
predictor      the 2-D blind-spot LMS predictor used by D and E
spectral       averaged 2-D spectrum and periodic-peak detection
inverse_model  adaptive inverse modelling for blur
baselines      median 3 x 3, adaptive median, local Wiener
pipeline       one call per scenario, and the cascade for the all-noise image
metrics        PSNR, SSIM, noise-level estimate
"""
