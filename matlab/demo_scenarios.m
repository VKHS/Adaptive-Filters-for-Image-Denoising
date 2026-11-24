%DEMO_SCENARIOS The six scenarios on the test image, one figure per scenario, plus the all-noise cascade.
%   Run the whole script or one cell at a time (Ctrl+Enter). Figures are saved to results/matlab_figures/.
%   Base MATLAB only. Uses data/lena.png when present, otherwise data/camera.png.

%% setup
root = adf_setup();
outdir = fullfile(root, 'results', 'matlab_figures');
if ~exist(outdir, 'dir')
    mkdir(outdir);
end
[x, name] = load_test_image();
if strcmpi(name, 'camera')
    rows = 81:272; cols = 161:352;
elseif strncmpi(name, 'len', 3)
    rows = 211:402; cols = 221:412;
else
    rows = 161:352; cols = 161:352;
end
crop = @(im) im(rows, cols);
cols3 = [0.16 0.47 0.84; 0.92 0.41 0.20; 0.11 0.69 0.48];   % blue, orange, aqua
fprintf('test image: %s\n', name);

%% A  adaptive notch (synthetic sinusoidal reference)
nz = make_noisy('periodic', x);
[outA, fA] = adaptive_notch(nz.y, [], 0.001);
fprintf('A: detected [u v] =\n'); disp(fA);
fig = figure('Color', 'w', 'Position', [60 60 1500 380]);
subplot(1, 4, 1); show_img(crop(nz.y), sprintf('periodic interference\n%.2f dB', psnr_db(x, nz.y)));
subplot(1, 4, 2);
P = welch2d(nz.y);
f = fftshift(fftfreq(128));
imagesc(f, f, log10(P)); axis image; colormap(gca, flipud(gray)); hold on;
plot(fA(:, 2), fA(:, 1), 'o', 'Color', [0.92 0.41 0.20], 'MarkerSize', 12, 'LineWidth', 1.5);
plot(-fA(:, 2), -fA(:, 1), 'o', 'Color', [0.92 0.41 0.20], 'MarkerSize', 12, 'LineWidth', 1.5);
xlabel('v (cycles/pixel)'); ylabel('u (cycles/pixel)'); title(sprintf('averaged spectrum (log)\ndetected peaks'));
subplot(1, 4, 3); show_img(crop(outA), sprintf('adaptive notch output\n%.2f dB', psnr_db(x, outA)));
subplot(1, 4, 4);
om0 = 2 * pi * 0.1;
om = linspace(0.3, 0.95, 400);
hold on;
mus = [0.02 0.05 0.1];
for k = 1:3
    plot(om / (2 * pi), abs(notch_response_theory(om0, mus(k), om)), 'Color', cols3(k, :), 'LineWidth', 2);
end
xlabel('frequency (cycles/sample)'); ylabel('|H|'); grid on; box off;
legend(arrayfun(@(m) sprintf('\\mu_2C^2 = %g', m), mus, 'UniformOutput', false), 'Location', 'southwest');
title('notch response H(z)');
print(fig, fullfile(outdir, 'A_notch.png'), '-dpng', '-r130');

%% B  bias (drift) canceller
nz = make_noisy('banding', x);
tb = bias_canceller(nz.y, 0.02, 'lms');
[il, off] = interline_canceller(nz.y, 0.001, 2, 16);
fig = figure('Color', 'w', 'Position', [60 60 1500 380]);
subplot(1, 4, 1); show_img(crop(nz.y), sprintf('row banding\n%.2f dB', psnr_db(x, nz.y)));
subplot(1, 4, 2); show_img(crop(tb + mean(x(:))), sprintf('textbook canceller along rows\n%.2f dB (scene flattened)', psnr_db(x, tb + mean(x(:)))));
subplot(1, 4, 3); show_img(crop(il), sprintf('line-to-line canceller + high-pass\n%.2f dB', psnr_db(x, il)));
subplot(1, 4, 4);
c = nz.side.truth;
plot(1:160, c(1:160) - mean(c(1:160)), 'Color', cols3(1, :), 'LineWidth', 2); hold on;
plot(1:160, off(1:160) - mean(off(1:160)), 'Color', cols3(3, :), 'LineWidth', 1);
legend('true row offset', 'correction b_i', 'Location', 'southwest'); xlabel('row'); grid on; box off;
title('per-row corrections');
print(fig, fullfile(outdir, 'B_bias.png'), '-dpng', '-r130');

%% C  periodic interference without a reference
nz = make_noisy('periodic', x);
raw = delayed_canceller(nz.y);
[sub, info] = subband_canceller(nz.y);
fig = figure('Color', 'w', 'Position', [60 60 1500 380]);
subplot(1, 4, 1); show_img(crop(nz.y), sprintf('periodic interference\n%.2f dB', psnr_db(x, nz.y)));
subplot(1, 4, 2); show_img(crop(raw), sprintf('delayed canceller on raw rows\n%.2f dB', psnr_db(x, raw)));
subplot(1, 4, 3); show_img(crop(sub), sprintf('two-band canceller\n%.2f dB', psnr_db(x, sub)));
subplot(1, 4, 4);
h = [zeros(8, 1); info.weights];
Hf = abs(fft(h, 2048));
fr = (0:1024) / 2048;
plot(fr, Hf(1:1025), 'Color', cols3(1, :), 'LineWidth', 1.5); hold on;
comps = periodic_components();
for k = 1:size(comps, 1)
    plot([comps(k, 3) comps(k, 3)], [0 max(Hf)], 'Color', cols3(2, :));
end
xlabel('frequency along the row (cycles/pixel)'); ylabel('|gain|'); grid on; box off;
title('learned predictor: peaks at the lines');
print(fig, fullfile(outdir, 'C_noref.png'), '-dpng', '-r130');

%% D  self-tuning filter (blind-spot predictor) and its error-gated version
g = make_noisy('gaussian', x);
[yD, infoD] = self_tuning(g.y);
im = make_noisy('impulse', x);
[yG, flags] = self_tuning_gated(im.y);
fig = figure('Color', 'w', 'Position', [60 60 1500 720]);
subplot(2, 4, 1); show_img(crop(g.y), sprintf('Gaussian\n%.2f dB', psnr_db(x, g.y)));
subplot(2, 4, 2); show_img(crop(yD), sprintf('D: filter output\n%.2f dB', psnr_db(x, yD)));
subplot(2, 4, 3); show_img(crop(g.y - yD) + 0.5, 'error output (removed noise)');
subplot(2, 4, 4); imagesc(infoD.weights); axis image off; colormap(gca, parula); colorbar;
title(sprintf('learned weights (sum %.2f)', sum(infoD.weights(:))));
subplot(2, 4, 5); show_img(crop(im.y), sprintf('impulse noise\n%.2f dB', psnr_db(x, im.y)));
subplot(2, 4, 6); show_img(crop(yG), sprintf('D, error-gated\n%.2f dB', psnr_db(x, yG)));
subplot(2, 4, 7); show_img(double(crop(flags)), 'flagged pixels');
md = median3(im.y);
subplot(2, 4, 8); show_img(crop(md), sprintf('median 3 x 3\n%.2f dB', psnr_db(x, md)));
print(fig, fullfile(outdir, 'D_selftuning.png'), '-dpng', '-r130');

%% E  adaptive line enhancer
fig = figure('Color', 'w', 'Position', [60 60 1500 380]);
subplot(1, 4, 1);
Ls = 4:512;
snrs = [0.01 0.1 1];
for k = 1:3
    semilogx(Ls, ale_peak_gain(Ls, snrs(k)), 'Color', cols3(k, :), 'LineWidth', 2); hold on;
    Lp = [8 16 32 64 128 256 512];
    ex = zeros(size(Lp));
    for q = 1:numel(Lp)
        ex(q) = abs(ale_response(ale_wiener_weights(Lp(q), 1, snrs(k), 2 * pi / 16), 1, 2 * pi / 16));
    end
    semilogx(Lp, ex, 'o', 'Color', cols3(k, :), 'MarkerFaceColor', cols3(k, :));
end
xlabel('number of weights L'); ylabel('peak gain'); grid on; box off;
title(sprintf('G = (L/2)SNR/((L/2)SNR+1)\nlines formula, dots exact'));
cz = make_noisy('correlated', x);
yD0 = self_tuning(cz.y);
[yE, hole] = line_enhancer(cz.y);
subplot(1, 4, 2); show_img(crop(cz.y), sprintf('correlated noise\n%.2f dB', psnr_db(x, cz.y)));
subplot(1, 4, 3); show_img(crop(yD0), sprintf('D, blind spot 1 x 1\n%.2f dB', psnr_db(x, yD0)));
subplot(1, 4, 4); show_img(crop(yE), sprintf('E, blind spot %d x %d (measured)\n%.2f dB', 2 * hole + 1, 2 * hole + 1, psnr_db(x, yE)));
print(fig, fullfile(outdir, 'E_ale.png'), '-dpng', '-r130');

%% F  reference-sensor canceller
b = make_noisy('banding', x);
w = train_row_weight(b.side.dark, b.side.dark_ob);
yb = row_reference_canceller(b.y, b.side.ob, w);
t = make_noisy('telegraph_readout', x);
[yt, wt] = channel_reference_canceller(t.y, t.side.ref_out, 1, 1e-3, t.side.dark, t.side.dark_ref);
fig = figure('Color', 'w', 'Position', [60 60 1500 720]);
subplot(2, 3, 1); show_img(crop(b.y), sprintf('row banding\n%.2f dB', psnr_db(x, b.y)));
subplot(2, 3, 2); show_img(crop(yb), sprintf('F, optical-black reference (w = %.3f)\n%.2f dB', w, psnr_db(x, yb)));
subplot(2, 3, 3);
rr = logspace(-4, 1, 200);
semilogx(rr, 10 * log10(noise_reduction_theory(0.04, rr)), 'Color', cols3(2, :), 'LineWidth', 2);
xlabel('R_{refn}'); ylabel('noise reduction (dB)'); grid on; box off; title('theory, R_{prin} = 0.04');
subplot(2, 3, 4); show_img(crop(t.y), sprintf('readout telegraph\n%.2f dB', psnr_db(x, t.y)));
subplot(2, 3, 5); show_img(crop(yt), sprintf('F, reference output (w = %.3f)\n%.2f dB', wt(1), psnr_db(x, yt)));
subplot(2, 3, 6);
plot(t.side.truth(120, :), 'Color', cols3(1, :), 'LineWidth', 1.6); hold on;
plot(t.side.ref_out(120, :), 'Color', cols3(2, :));
legend('true telegraph offset', 'reference channel', 'Location', 'southeast'); xlabel('pixel along row 120');
grid on; box off;
print(fig, fullfile(outdir, 'F_reference.png'), '-dpng', '-r130');

%% all noises at once
nz = make_mixed(x);
[stages, labels] = run_cascade(nz);
fig = figure('Color', 'w', 'Position', [60 60 1600 330]);
for k = 1:numel(stages)
    subplot(1, numel(stages), k);
    show_img(crop(stages{k}), sprintf('%s\n%.2f dB', labels{k}, psnr_db(x, stages{k})));
end
print(fig, fullfile(outdir, 'cascade.png'), '-dpng', '-r130');
fprintf('figures written to %s\n', outdir);

%% local function
function show_img(im, ttl)
image(min(max(im, 0), 1) * 255);
colormap(gca, gray(256));
axis image off;
title(ttl, 'FontWeight', 'normal');
end
