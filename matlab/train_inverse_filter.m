function [kern, curve] = train_inverse_filter(sharp, blurred, r, alpha, passes)
%TRAIN_INVERSE_FILTER Adaptive inverse modelling (blur): LMS predicts sharp(i, j) from the
%   (2r+1) x (2r+1) window of the blurred calibration target around (i, j). Returns the kernel for
%   APPLY_FILTER and the learning curve (mean squared error per row).
if nargin < 3 || isempty(r), r = 4; end
if nargin < 4 || isempty(alpha), alpha = 0.02; end
if nargin < 5 || isempty(passes), passes = 2; end
[H, W] = size(blurred);
k = 2 * r + 1;
m = mean(blurred(:));
pad = pad_reflect(blurred - m, r);
d_all = sharp - mean(sharp(:));
mu2 = alpha / (k * k * var(blurred(:), 1));
[~, ao, bo] = tap_mask(r, -1);
n_taps = numel(ao);
w = zeros(n_taps, 1);
w((n_taps + 1) / 2) = 1;
curve = zeros(H * passes, 1);
cols = 1:W;
Xt = zeros(n_taps, W);
for p = 1:passes
    for i = 1:H
        for t = 1:n_taps
            Xt(t, :) = pad(i + ao(t), cols + bo(t));
        end
        d = d_all(i, :);
        acc = 0;
        for j = 1:W
            x = Xt(:, j);
            e = d(j) - w.' * x;
            w = w + (mu2 * e) * x;
            acc = acc + e * e;
        end
        curve((p - 1) * H + i) = acc / W;
    end
end
kern = zeros(k, k);
kern(sub2ind([k k], ao + 1, bo + 1)) = w;
end
