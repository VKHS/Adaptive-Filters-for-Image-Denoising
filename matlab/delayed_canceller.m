function out = delayed_canceller(img, L, delay, alpha)
%DELAYED_CANCELLER Scenario C exactly as in 1-D (delayed primary as reference, error output), on raw rows.
%   Fails on images: neighbouring pixels are correlated, so the image is predicted and cancelled too.
if nargin < 2 || isempty(L), L = 32; end
if nargin < 3 || isempty(delay), delay = 64; end
if nargin < 4 || isempty(alpha), alpha = 0.01; end
z = img - repmat(mean(img, 2), 1, size(img, 2));
mu2 = alpha / (L * var(z(:), 1));
out = img - rows_lms(z, L, delay, mu2);
end
