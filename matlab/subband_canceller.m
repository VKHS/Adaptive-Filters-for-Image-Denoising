function [out, info] = subband_canceller(img, L, delay, alpha, split_sigma)
%SUBBAND_CANCELLER Scenario C on images: the delayed-reference canceller run on the high band of each row.
%   Each row is split into a low band (Gaussian, split_sigma pixels) that is passed through untouched and a
%   high band in which the image is nearly white while the interference is still a pure sinusoid. The
%   canceller (delay, L taps, error output) runs on the high band; output = low band + error output.
%   No frequency has to be known. info.weights holds the final predictor (its response shows the lines).
if nargin < 2 || isempty(L), L = 128; end
if nargin < 3 || isempty(delay), delay = 8; end
if nargin < 4 || isempty(alpha), alpha = 0.002; end
if nargin < 5 || isempty(split_sigma), split_sigma = 4; end
z = img - repmat(mean(img, 2), 1, size(img, 2));
rad = fix(4 * split_sigma + 0.5);
g = gaussian_kernel(split_sigma, rad);
low = conv2(pad_symmetric(z, rad, 2), g, 'valid');
high = z - low;
mu2 = alpha / (L * var(high(:), 1));
[y, w] = rows_lms(high, L, delay, mu2);
out = img - y;
info = struct('interference', y, 'high', high, 'weights', w, 'mu2', mu2);
end
