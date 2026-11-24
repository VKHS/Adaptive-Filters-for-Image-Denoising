function nz = make_mixed(x, seed)
%MAKE_MIXED Every corruption at once, at reduced strength, in physical order:
%   optics (blur) -> photon shot noise -> pixel RTS -> row banding and readout telegraph (with their
%   references) -> periodic pickup -> white read noise -> transmission errors (bursts, impulses, salt & pepper).
if nargin < 2
    seed = 0;
end
rng(99000 + seed, 'twister');
[H, W] = size(x);
y = gaussian_blur(x, 0.8);
y = poisson_sample(200 * max(y, 0)) / 200;
rts = rand(H, W) < 0.02;
a = 0.1 + 0.2 * rand(H, W);
st = 0.5 * ones(H, W);
st(rand(H, W) >= 0.5) = -0.5;
y = y + rts .* a .* st;
c = 0.04 * randn(H, 1);
t = 0.04 * (2 * unraster(two_state_chain(H * W, 1 / 60, 1 / 60), H, W) - 1);
y = y + repmat(c, 1, W) + t;
comps = periodic_components();
comps(:, 1) = 0.7 * comps(:, 1);
y = y + plane_waves(H, W, comps);
y = y + 0.02 * randn(H, W);
side = struct();
side.ob = repmat(c, 1, 16) + 0.02 * randn(H, 16);
side.ref_out = 0.8 * t + 0.01 * randn(H, W);
cd = 0.04 * randn(H, 1);
td = 0.04 * (2 * unraster(two_state_chain(H * W, 1 / 60, 1 / 60), H, W) - 1);
side.dark = repmat(cd, 1, W) + td + 0.02 * randn(H, W);
side.dark_ob = repmat(cd, 1, 16) + 0.02 * randn(H, 16);
side.dark_ref = 0.8 * td + 0.01 * randn(H, W);
side.psf_sigma = 0.8;
side.noise_sigma = 0.02;
bad = (unraster(two_state_chain(H * W, 0.0015, 0.125), H, W) > 0) & (rand(H, W) < 0.9);
y(bad) = rand(nnz(bad), 1);
imp = rand(H, W) < 0.01;
y(imp) = rand(nnz(imp), 1);
sp = rand(H, W) < 0.02;
y(sp) = double(rand(nnz(sp), 1) < 0.5);
side.mask = bad | imp | sp;
side.freqs = comps(:, 2:3);
nz = struct('key', 'mixed', 'label', 'All noises together', 'y', y, 'side', side, ...
            'params', struct('note', 'reduced-strength mixture of every model'));
end
