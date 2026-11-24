%DEMO_EXAMPLES One application per scenario, on the example images in data/examples/.
%   The MATLAB counterpart of python/make_examples.py: the same images, corruptions and settings. MATLAB's
%   random stream differs from NumPy's, so the corrupted images and the numbers differ slightly from
%   results/examples_python.csv. Run the whole script or one cell at a time (Ctrl+Enter). Figures are saved to
%   results/matlab_figures/examples_*.png. Base MATLAB only.

%% setup
root = adf_setup();
exd = fullfile(root, 'data', 'examples');
outdir = fullfile(root, 'results', 'matlab_figures');
if ~exist(outdir, 'dir')
    mkdir(outdir);
end
pos = [60 60 1500 380];

%% A  LED flicker in a rolling-shutter camera: adaptive notch at the known frequency, in the log domain
x = load_test_image(fullfile(exd, 'coffee.png'));
[H, W] = size(x);
rng(11, 'twister');
u = 0.0185;                                          % PWM frequency x line time = cycles per row
flick = 1 + 0.25 * cos(2 * pi * u * (0:H-1)' + 0.4);
y = x .* repmat(flick, 1, W) + 0.005 * randn(H, W);
e0 = 0.02;                                           % keeps the logarithm finite on black pixels
outA = exp(notch_lms(log(max(y, 0) + e0), [u 0; 2 * u 0], 1e-5, 1, 3)) - e0;
linA = notch_lms(y, [u 0; 2 * u 0], 1e-5, 1, 3);
fig = figure('Color', 'w', 'Position', pos);
subplot(1, 4, 1); show_img(y, sprintf('LED flicker bands\n%.2f dB', psnr_db(x, y)));
subplot(1, 4, 2); show_img(outA, sprintf('A in the log domain\n%.2f dB', psnr_db(x, outA)));
subplot(1, 4, 3); show_img(linA, sprintf('A in the linear domain\n%.2f dB', psnr_db(x, linA)));
subplot(1, 4, 4);
plot(mean(y, 2), 'Color', [0.55 0.55 0.55]); hold on;
plot(mean(outA, 2), 'Color', [0.16 0.47 0.84], 'LineWidth', 1.5);
plot(mean(x, 2), 'k');
legend('corrupted', 'after A', 'clean', 'Location', 'southwest'); xlabel('row'); ylabel('row mean');
grid on; box off; title('row-mean profile');
print(fig, fullfile(outdir, 'examples_A_flicker.png'), '-dpng', '-r130');
fprintf('A flicker: noisy %.2f, A log domain %.2f, A linear %.2f dB\n', psnr_db(x, y), psnr_db(x, outA), psnr_db(x, linA));

%% B  probe microscopy: line offsets and drift along each fast-scan line, flat substrate
s = afm_scene(512, 512, 90, 3);
[H, W] = size(s);
rng(7, 'twister');
jj = repmat(0:W-1, H, 1);
amp = 0.05 + 0.03 * rand(H, 1);
ph = 2 * pi * rand(H, 1);
wander = repmat(amp, 1, W) .* sin(2 * pi * 0.8 * jj / W + repmat(ph, 1, W));
y = s + repmat(0.05 * randn(H, 1), 1, W) + wander + 0.1 * jj / W + 0.01 * randn(H, W);
rowmed = y - repmat(median(y, 2), 1, W);
lmsB = bias_canceller(y, 0.02, 'lms');
[gateB, track] = bias_canceller(y, 0.05, 'gated', 0.08);
lev = @(im) im - median(im(:)) + 0.3;
fig = figure('Color', 'w', 'Position', pos);
subplot(1, 4, 1); show_img(lev(y), sprintf('raw scan\n%.1f dB', offset_aligned_psnr(s, y)));
subplot(1, 4, 2); show_img(lev(rowmed), sprintf('row-median levelling\n%.1f dB', offset_aligned_psnr(s, rowmed)));
subplot(1, 4, 3); show_img(lev(gateB), sprintf('B, gated update\n%.1f dB', offset_aligned_psnr(s, gateB)));
subplot(1, 4, 4);
i0 = 200;
plot(y(i0, :) - median(y(i0, :)), 'Color', [0.55 0.55 0.55]); hold on;
plot(track(i0, :) - median(y(i0, :)), 'Color', [0.92 0.41 0.20], 'LineWidth', 1.6);
plot(gateB(i0, :) - median(gateB(i0, :)), 'Color', [0.16 0.47 0.84]);
legend('raw line', 'bias b (gated)', 'corrected', 'Location', 'northwest'); xlabel(sprintf('pixel along line %d', i0));
grid on; box off; title('one fast-scan line');
print(fig, fullfile(outdir, 'examples_B_probe_microscopy.png'), '-dpng', '-r130');
fprintf('B probe microscopy (offset-aligned): noisy %.2f, row median %.2f, LMS %.2f, gated %.2f dB\n', ...
    offset_aligned_psnr(s, y), offset_aligned_psnr(s, rowmed), offset_aligned_psnr(s, lmsB), offset_aligned_psnr(s, gateB));

%% C  vibration stripes whose frequency drifts down the image: no reference, no fixed frequency
x = load_test_image(fullfile(exd, 'chelsea.png'));
[H, W] = size(x);
ii = (0:H-1)';
f = 0.08 + 0.04 * ii / H;
y = x + 0.10 * cos(2 * pi * cumsum(repmat(f, 1, W), 2) + 2 * pi * 0.013 * repmat(ii, 1, W));
[~, pk] = adaptive_notch(y, [], 0.001);
outC = subband_canceller(y, 128, 8, 0.005);
fig = figure('Color', 'w', 'Position', pos);
subplot(1, 4, 1); show_img(y, sprintf('drifting stripes\n%.2f dB', psnr_db(x, y)));
subplot(1, 4, 2); show_img(outC, sprintf('C, two-band canceller\n%.2f dB', psnr_db(x, outC)));
subplot(1, 4, 3); show_img(0.5 + 2 * (y - outC), 'removed component (x2)');
subplot(1, 4, 4);
Sy = abs(fft((y - repmat(mean(y, 2), 1, W)) .* repmat(hann_sym(W)', H, 1), [], 2)) .^ 2;
imagesc((0:W/2) / W, 1:H, log10(Sy(:, 1:W/2+1) + 1e-6)); colormap(gca, flipud(gray));
xlim([0 0.25]); xlabel('cycles/pixel along the row'); ylabel('row'); title('per-row spectrum, input');
print(fig, fullfile(outdir, 'examples_C_drifting_stripes.png'), '-dpng', '-r130');
fprintf('C drifting stripes: A detects %d peaks; noisy %.2f, C %.2f dB\n', size(pk, 1), psnr_db(x, y), psnr_db(x, outC));

%% D  bit errors, dead and hot pixels on fine texture: the gated predictor replaces only flagged pixels
x = load_test_image(fullfile(exd, 'gravel.png'));
rng(5, 'twister');
y = x;
hit = rand(size(x)) < 0.10;
y(hit) = rand(nnz(hit), 1);
dead = rand(size(x)) < 0.005;
y(dead) = double(rand(nnz(dead), 1) < 0.5);
[outD, flags] = self_tuning_gated(y);
medD = median3(y);
amfD = adaptive_median(y);
rows = 151:310; cols = 181:340;
fig = figure('Color', 'w', 'Position', pos);
subplot(1, 4, 1); show_img(y(rows, cols), sprintf('10 %% impulses + dead/hot pixels\n%.2f dB', psnr_db(x, y)));
subplot(1, 4, 2); show_img(outD(rows, cols), sprintf('D, error-gated\n%.2f dB', psnr_db(x, outD)));
subplot(1, 4, 3); show_img(medD(rows, cols), sprintf('median 3 x 3\n%.2f dB', psnr_db(x, medD)));
subplot(1, 4, 4); show_img(double(~flags(rows, cols)), sprintf('replaced pixels (black)\n%.1f %% of the image', 100 * mean(flags(:))));
print(fig, fullfile(outdir, 'examples_D_impulses_texture.png'), '-dpng', '-r130');
fprintf('D impulses on texture: noisy %.2f, D gated %.2f, median %.2f, adaptive median %.2f dB\n', ...
    psnr_db(x, y), psnr_db(x, outD), psnr_db(x, medD), psnr_db(x, amfD));

%% E  periodic texture under heavy noise: the line enhancer learns the period
x = load_test_image(fullfile(exd, 'brick.png'));
rng(9, 'twister');
y = x + 0.12 * randn(size(x));
outE = line_enhancer(y, 5, 0);
wieE = local_wiener(y);
medE = median3(y);
rows = 161:352; cols = 161:352;
fig = figure('Color', 'w', 'Position', pos);
subplot(1, 4, 1); show_img(y(rows, cols), sprintf('brick texture + noise\n%.2f dB', psnr_db(x, y)));
subplot(1, 4, 2); show_img(outE(rows, cols), sprintf('E, 11 x 11 window\n%.2f dB', psnr_db(x, outE)));
subplot(1, 4, 3); show_img(wieE(rows, cols), sprintf('Wiener 5 x 5\n%.2f dB', psnr_db(x, wieE)));
subplot(1, 4, 4); show_img(medE(rows, cols), sprintf('median 3 x 3\n%.2f dB', psnr_db(x, medE)));
print(fig, fullfile(outdir, 'examples_E_periodic_texture.png'), '-dpng', '-r130');
fprintf('E periodic texture: noisy %.2f, E %.2f, Wiener %.2f, median %.2f dB\n', ...
    psnr_db(x, y), psnr_db(x, outE), psnr_db(x, wieE), psnr_db(x, medE));

%% F  faint astronomical field: row banding and readout telegraph noise, with the sensor's references
x = load_test_image(fullfile(exd, 'hubble.png'));
[H, W] = size(x);
rng(3, 'twister');
tele = @() 0.03 * (2 * unraster(two_state_chain(H * W, 1 / 60, 1 / 60), H, W) - 1);
c = 0.03 * randn(H, 1);
t = tele();
y = x + repmat(c, 1, W) + t + 0.01 * randn(H, W);
ob = repmat(c, 1, 16) + 0.01 * randn(H, 16);
ref = 0.8 * t + 0.01 * randn(H, W);
cdark = 0.03 * randn(H, 1);
td = tele();
dark = repmat(cdark, 1, W) + td + 0.01 * randn(H, W);
dark_ob = repmat(cdark, 1, 16) + 0.01 * randn(H, 16);
dark_ref = 0.8 * td + 0.01 * randn(H, W);
w = train_row_weight(dark, dark_ob);
y1 = row_reference_canceller(y, ob, w);
y2 = channel_reference_canceller(y1, ref, 1, 1e-3, dark, dark_ref);
stretch = @(a) asinh(max(a, 0) / 0.03) / asinh(1 / 0.03);
rows = 251:442; cols = 41:232;
fig = figure('Color', 'w', 'Position', pos);
subplot(1, 4, 1); show_img(stretch(x(rows, cols)), 'clean (asinh stretch)');
subplot(1, 4, 2); show_img(stretch(y(rows, cols)), sprintf('banding + readout telegraph\n%.2f dB', psnr_db(x, y)));
subplot(1, 4, 3); show_img(stretch(y1(rows, cols)), sprintf('F, optical-black reference\n%.2f dB', psnr_db(x, y1)));
subplot(1, 4, 4); show_img(stretch(y2(rows, cols)), sprintf('F, + reference output\n%.2f dB', psnr_db(x, y2)));
print(fig, fullfile(outdir, 'examples_F_astronomy.png'), '-dpng', '-r130');
fprintf('F astronomy: noisy %.2f, optical black %.2f, both references %.2f dB\n', psnr_db(x, y), psnr_db(x, y1), psnr_db(x, y2));
fprintf('figures written to %s\n', outdir);

%% local function
function show_img(im, ttl)
image(min(max(im, 0), 1) * 255);
colormap(gca, gray(256));
axis image off;
title(ttl, 'FontWeight', 'normal');
end
