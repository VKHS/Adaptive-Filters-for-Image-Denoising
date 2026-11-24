function rho = noise_correlation(img, block, frac, max_lag)
%NOISE_CORRELATION Normalised noise autocorrelation at lags 1..max_lag, from the flattest tiles.
%   A plane is fitted to every block x block tile and removed; the frac tiles with the smallest residual
%   variance are kept (there the image is nearly planar, so the residual is noise). rho(k) is averaged over
%   the horizontal and vertical directions.
if nargin < 2 || isempty(block), block = 16; end
if nargin < 3 || isempty(frac), frac = 0.1; end
if nargin < 4 || isempty(max_lag), max_lag = 3; end
[H, W] = size(img);
[jj, ii] = meshgrid(0:block-1, 0:block-1);
A = [ones(block^2, 1), raster(ii), raster(jj)];
P = pinv(A);
nt = floor(H / block) * floor(W / block);
res_all = zeros(block, block, nt);
vars = zeros(nt, 1);
n = 0;
for i0 = 1:block:H - block + 1
    for j0 = 1:block:W - block + 1
        t = raster(img(i0:i0 + block - 1, j0:j0 + block - 1));
        res = unraster(t - A * (P * t), block, block);
        n = n + 1;
        res_all(:, :, n) = res;
        vars(n) = var(res(:), 1);
    end
end
[~, order] = sort(vars(1:n));
sel = order(1:max(1, floor(frac * n)));
v0 = 0;
for q = sel.'
    r = res_all(:, :, q);
    v0 = v0 + mean(r(:).^2);
end
v0 = v0 / numel(sel);
rho = zeros(max_lag, 1);
for k = 1:max_lag
    h = 0;
    v = 0;
    for q = sel.'
        r = res_all(:, :, q);
        a = r(:, k + 1:end) .* r(:, 1:end - k);
        b = r(k + 1:end, :) .* r(1:end - k, :);
        h = h + mean(a(:));
        v = v + mean(b(:));
    end
    rho(k) = 0.5 * (h + v) / numel(sel) / v0;
end
end
