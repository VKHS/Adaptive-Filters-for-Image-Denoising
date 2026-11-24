function nz = make_noisy(key, x, seed)
%MAKE_NOISY Corrupt the clean image x (double, [0, 1]) with noise model KEY.
%   nz = make_noisy(key, x, seed) returns a struct with fields
%     key, label : model name and display label
%     y          : the noisy image (not clipped)
%     side       : side information a real system would measure with the image (reference columns,
%                  reference output channel, dark calibration frame, known PSF), used by scenario F
%     params     : the parameters used
%   Keys: gaussian, correlated, poisson, blur, salt_pepper, impulse, burst, telegraph_pixel,
%   telegraph_readout, periodic, banding. Raster (readout) order is row by row, left to right.
%   The parameters are the same as in the Python code; the random streams differ.
if nargin < 3
    seed = 0;
end
[keys, labels] = noise_keys();
idx = find(strcmp(keys, key));
if isempty(idx)
    error('make_noisy:key', 'unknown noise model %s', key);
end
rng(1000 * idx + seed, 'twister');
[H, W] = size(x);
side = struct();
switch key
    case 'gaussian'
        sigma = 20 / 255;
        y = x + sigma * randn(H, W);
        params = struct('sigma', sigma);
    case 'correlated'
        sigma = 20 / 255;
        corr_px = 1.0;
        n = gaussian_blur(randn(H, W), corr_px);
        n = n * (sigma / std(n(:), 1));
        y = x + n;
        params = struct('sigma', sigma, 'corr_px', corr_px);
    case 'poisson'
        peak = 60;
        y = poisson_sample(peak * x) / peak;
        params = struct('peak', peak);
    case 'blur'
        psf_sigma = 1.6;
        sigma = 0.005;
        y = gaussian_blur(x, psf_sigma) + sigma * randn(H, W);
        side.psf_sigma = psf_sigma;
        side.noise_sigma = sigma;
        params = struct('psf_sigma', psf_sigma, 'sigma', sigma);
    case 'salt_pepper'
        density = 0.10;
        y = x;
        hit = rand(H, W) < density;
        y(hit) = double(rand(nnz(hit), 1) < 0.5);
        side.mask = hit;
        params = struct('density', density);
    case 'impulse'
        density = 0.10;
        y = x;
        hit = rand(H, W) < density;
        y(hit) = rand(nnz(hit), 1);
        side.mask = hit;
        params = struct('density', density);
    case 'burst'
        p_gb = 0.004;
        p_bg = 0.125;
        p_hit = 0.9;
        bad = unraster(two_state_chain(H * W, p_gb, p_bg), H, W) > 0;
        hit = bad & (rand(H, W) < p_hit);
        y = x;
        y(hit) = rand(nnz(hit), 1);
        side.mask = hit;
        params = struct('p_gb', p_gb, 'p_bg', p_bg, 'p_hit', p_hit);
    case 'telegraph_pixel'
        fraction = 0.05;
        amp_min = 0.10;
        amp_max = 0.30;
        sigma = 0.01;
        rts = rand(H, W) < fraction;
        a = amp_min + (amp_max - amp_min) * rand(H, W);
        st = 0.5 * ones(H, W);
        st(rand(H, W) >= 0.5) = -0.5;
        y = x + rts .* a .* st + sigma * randn(H, W);
        side.mask = rts;
        params = struct('fraction', fraction, 'amp_min', amp_min, 'amp_max', amp_max, 'sigma', sigma);
    case 'telegraph_readout'
        amp = 0.06;
        dwell = 60;
        sigma = 0.01;
        ref_gain = 0.8;
        ref_sigma = 0.01;
        t = amp * (2 * unraster(two_state_chain(H * W, 1 / dwell, 1 / dwell), H, W) - 1);
        y = x + t + sigma * randn(H, W);
        side.ref_out = ref_gain * t + ref_sigma * randn(H, W);
        td = amp * (2 * unraster(two_state_chain(H * W, 1 / dwell, 1 / dwell), H, W) - 1);
        side.dark = td + sigma * randn(H, W);
        side.dark_ref = ref_gain * td + ref_sigma * randn(H, W);
        side.truth = t;
        params = struct('amp', amp, 'dwell', dwell, 'sigma', sigma, 'ref_gain', ref_gain, 'ref_sigma', ref_sigma);
    case 'periodic'
        comps = periodic_components();
        p = plane_waves(H, W, comps);
        y = x + p;
        side.freqs = comps(:, 2:3);
        side.truth = p;
        params = struct('components', comps);
    case 'banding'
        sigma_row = 0.05;
        sigma = 0.01;
        n_ob = 16;
        c = sigma_row * randn(H, 1);
        y = x + repmat(c, 1, W) + sigma * randn(H, W);
        side.ob = repmat(c, 1, n_ob) + sigma * randn(H, n_ob);
        cd = sigma_row * randn(H, 1);
        side.dark = repmat(cd, 1, W) + sigma * randn(H, W);
        side.dark_ob = repmat(cd, 1, n_ob) + sigma * randn(H, n_ob);
        side.truth = c;
        params = struct('sigma_row', sigma_row, 'sigma', sigma, 'n_ob', n_ob);
end
nz = struct('key', key, 'label', labels{idx}, 'y', y, 'side', side, 'params', params);
end
