function [y, info] = blindspot_lms(img, r, hole, alpha, mu2, passes, update)
%BLINDSPOT_LMS Two-dimensional blind-spot LMS predictor (scenarios D and E). Returns the filter output.
%   Pixel (i, j) is predicted from its (2r+1) x (2r+1) neighbourhood without the central (2h+1) x (2h+1)
%   block (h = hole). The weights adapt sample by sample in raster order, w <- w + mu2 e x.
%   alpha : normalised step, mu2 = alpha / (taps * var(img)), misadjustment ~ alpha / 2 (default 0.01)
%   mu2   : explicit step (overrides alpha when not empty)
%   passes: raster passes; the output of the last pass is returned (default 2)
%   update: 'lms' (default) or 'sign' (w <- w + mu2 sign(e) x)
%   info  : struct with the learned kernel, the step, the tap count and the learning curve (MSE per row).
if nargin < 2 || isempty(r), r = 2; end
if nargin < 3 || isempty(hole), hole = 0; end
if nargin < 4 || isempty(alpha), alpha = 0.01; end
if nargin < 5, mu2 = []; end
if nargin < 6 || isempty(passes), passes = 2; end
if nargin < 7 || isempty(update), update = 'lms'; end
[H, W] = size(img);
m = mean(img(:));
z = img - m;
[mask, ao, bo] = tap_mask(r, hole);
n_taps = numel(ao);
if isempty(mu2)
    mu2 = alpha / (n_taps * var(z(:), 1));
end
pad = pad_reflect(z, r);
w = zeros(n_taps, 1);
y = zeros(H, W);
curve = zeros(H * passes, 1);
use_sign = strcmp(update, 'sign');
cols = 1:W;
Xt = zeros(n_taps, W);
for p = 1:passes
    for i = 1:H
        for t = 1:n_taps
            Xt(t, :) = pad(i + ao(t), cols + bo(t));
        end
        d = z(i, :);
        acc = 0;
        for j = 1:W
            x = Xt(:, j);
            yj = w.' * x;
            e = d(j) - yj;
            if use_sign
                if e > 0
                    w = w + mu2 * x;
                else
                    w = w - mu2 * x;
                end
            else
                w = w + (mu2 * e) * x;
            end
            y(i, j) = yj;
            acc = acc + e * e;
        end
        curve((p - 1) * H + i) = acc / W;
    end
end
y = y + m;
k = 2 * r + 1;
kern = zeros(k, k);
kern(sub2ind([k k], ao + 1, bo + 1)) = w;
info = struct('weights', kern, 'mu2', mu2, 'n_taps', n_taps, 'curve', curve, 'mask', mask);
end
