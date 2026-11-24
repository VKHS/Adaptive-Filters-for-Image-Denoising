function [out, flags] = blindspot_gated(img, r, alpha, k, passes)
%BLINDSPOT_GATED Error-gated blind-spot predictor for sparse (impulsive) noise (scenario D, gated).
%   The prediction error e = d - y is small on clean pixels and large on impulses. A pixel is flagged when
%   |e| > k * s, with s a running robust scale of e. Flagged pixels are replaced by the prediction y and do
%   not update the weights; clean pixels are kept. Pass 1 takes its taps from the noisy image, later passes
%   from the previous output, so flagged neighbours no longer spoil the prediction (bursts).
if nargin < 2 || isempty(r), r = 2; end
if nargin < 3 || isempty(alpha), alpha = 0.01; end
if nargin < 4 || isempty(k), k = 4.0; end
if nargin < 5 || isempty(passes), passes = 3; end
[H, W] = size(img);
m = median(img(:));
z = img - m;
[~, ao, bo] = tap_mask(r, 0);
n_taps = numel(ao);
zc = min(max(z, -0.5), 0.5);
mu2 = alpha / (n_taps * var(zc(:), 1));
w = ones(n_taps, 1) / n_taps;
src = z;
flags = false(H, W);
out = z;
cols = 1:W;
Xt = zeros(n_taps, W);
for p = 1:passes
    pad = pad_reflect(src, r);
    s = 0.05;
    for i = 1:H
        for t = 1:n_taps
            Xt(t, :) = pad(i + ao(t), cols + bo(t));
        end
        d = z(i, :);
        for j = 1:W
            x = Xt(:, j);
            yj = w.' * x;
            e = d(j) - yj;
            ae = abs(e);
            if ae > k * s
                out(i, j) = yj;
                flags(i, j) = true;
            else
                out(i, j) = d(j);
                flags(i, j) = false;
                w = w + (mu2 * e) * x;
                s = s + 0.01 * (1.4826 * ae - s);
            end
        end
    end
    src = out;
end
out = out + m;
end
