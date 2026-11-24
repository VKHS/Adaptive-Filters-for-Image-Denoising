function img = dead_leaves(H, W, n, rmin, rmax, seed)
%DEAD_LEAVES Calibration target: overlapping discs with power-law radii (density ~ r^-3).
if nargin < 3 || isempty(n), n = 6000; end
if nargin < 4 || isempty(rmin), rmin = 1.5; end
if nargin < 5 || isempty(rmax), rmax = 60; end
if nargin < 6 || isempty(seed), seed = 0; end
rng(seed, 'twister');
img = 0.5 * ones(H, W);
u = rand(n, 1);
radii = (rmin^-2 - u * (rmin^-2 - rmax^-2)).^(-0.5);
for k = 1:n
    ci = -rmax + (H + 2 * rmax) * rand;
    cj = -rmax + (W + 2 * rmax) * rand;
    r = radii(k);
    i0 = max(fix(ci - r), 0);
    i1 = min(fix(ci + r) + 2, H);
    j0 = max(fix(cj - r), 0);
    j1 = min(fix(cj + r) + 2, W);
    if i0 >= i1 || j0 >= j1
        continue
    end
    [jj, ii] = meshgrid(j0:j1 - 1, i0:i1 - 1);
    sub = (ii - ci).^2 + (jj - cj).^2 <= r * r;
    blk = img(i0 + 1:i1, j0 + 1:j1);
    blk(sub) = 0.05 + 0.9 * rand;
    img(i0 + 1:i1, j0 + 1:j1) = blk;
end
end
