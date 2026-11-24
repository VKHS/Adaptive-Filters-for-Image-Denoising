function s = afm_scene(H, W, n_obj, seed, background)
%AFM_SCENE Flat background with Gaussian blobs: the kind of scene line levelling was designed for.
if nargin < 3 || isempty(n_obj), n_obj = 60; end
if nargin < 4 || isempty(seed), seed = 0; end
if nargin < 5 || isempty(background), background = 0.3; end
rng(seed, 'twister');
[j, i] = meshgrid(0:W-1, 0:H-1);
s = background * ones(H, W);
for k = 1:n_obj
    ci = 10 + (H - 20) * rand;
    cj = 10 + (W - 20) * rand;
    sg = 3 + 5 * rand;
    h = 0.25 + 0.25 * rand;
    s = s + h * exp(-((i - ci).^2 + (j - cj).^2) / (2 * sg^2));
end
s = min(max(s, 0), 1);
end
