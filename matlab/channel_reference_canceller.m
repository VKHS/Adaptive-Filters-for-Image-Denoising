function [out, w] = channel_reference_canceller(y, ref, L, alpha, dark, dark_ref, online_alpha)
%CHANNEL_REFERENCE_CANCELLER Scenario F with a concurrent reference channel, in raster order.
%   x(n) = [ref(n), ..., ref(n-L+1)], output e(n) = y(n) - w.x(n). When a dark frame (dark, dark_ref) is
%   given, the weights are adapted on it and frozen for the scene (default). Otherwise they adapt online on
%   the scene with the tiny step online_alpha, and the row mean of the primary is removed from the error that
%   drives the update (the scene is a strong uncorrelated "signal" in the LMS gradient).
if nargin < 3 || isempty(L), L = 1; end
if nargin < 4 || isempty(alpha), alpha = 1e-3; end
if nargin < 5, dark = []; end
if nargin < 6, dark_ref = []; end
if nargin < 7 || isempty(online_alpha), online_alpha = 1e-4; end
w = zeros(L, 1);
if ~isempty(dark)
    [~, w] = run_canceller(dark, dark_ref, w, alpha, L, true, false);
    out = run_canceller(y, ref, w, alpha, L, false, false);
else
    [out, w] = run_canceller(y, ref, w, online_alpha, L, true, true);
end
end

function [out, w] = run_canceller(d_img, r_img, w, a, L, adapt, demean)
[H, W] = size(d_img);
r = [zeros(L - 1, 1); raster(r_img)];
d = raster(d_img);
if demean
    dm = raster(d_img - repmat(mean(d_img, 2), 1, W));
else
    dm = d;
end
mu2 = a / (L * var(r_img(:), 1));
o = zeros(H * W, 1);
for t = 1:H * W
    x = r(t + L - 1:-1:t);
    yv = w.' * x;
    o(t) = d(t) - yv;
    if adapt
        w = w + (mu2 * (dm(t) - yv)) * x;
    end
end
out = unraster(o, H, W);
end
