function NR = noise_reduction_theory(R_prin, R_refn)
%NOISE_REDUCTION_THEORY Noise-power reduction of the converged two-input canceller (linear, not dB):
%   (1 + R_prin) / (R_prin + R_refn / (1 + R_refn)), with R_prin and R_refn the ratios of uncorrelated to
%   correlated noise in the primary and in the reference input.
NR = (1 + R_prin) ./ (R_prin + R_refn ./ (1 + R_refn));
end
