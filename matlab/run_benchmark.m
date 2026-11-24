%RUN_BENCHMARK Every scenario and every baseline on every noise model, plus the all-noise cascade.
%   Writes results/benchmark_matlab.csv and prints a table of PSNR gains. Parameters are the fixed defaults;
%   the noise is generated with MATLAB's own random streams, so numbers differ slightly from the Python run.
root = adf_setup();
[x, name] = load_test_image();
[keys, labels] = noise_keys();
methods = {'A', 'B', 'C', 'D', 'Dg', 'E', 'F', 'median3', 'AMF', 'Wiener5'};
fid = fopen(fullfile(root, 'results', 'benchmark_matlab.csv'), 'w');
fprintf(fid, 'noise,method,psnr,ssim,gain,seconds\n');
G = nan(numel(keys), numel(methods));
P0 = zeros(numel(keys), 1);
for k = 1:numel(keys)
    nz = make_noisy(keys{k}, x, 0);
    p0 = psnr_db(x, nz.y);
    P0(k) = p0;
    fprintf(fid, '%s,noisy,%.4f,%.4f,0,0\n', keys{k}, p0, ssim_index(x, nz.y));
    fprintf('%-18s noisy %6.2f dB\n', keys{k}, p0);
    for m = 1:numel(methods)
        tic;
        switch methods{m}
            case 'median3'
                out = median3(nz.y);
            case 'AMF'
                out = adaptive_median(nz.y);
            case 'Wiener5'
                out = local_wiener(nz.y);
            otherwise
                out = apply_scenario(methods{m}, nz);
        end
        dt = toc;
        if isempty(out)
            fprintf(fid, '%s,%s,nan,nan,nan,0\n', keys{k}, methods{m});
            continue
        end
        p = psnr_db(x, out);
        G(k, m) = p - p0;
        fprintf(fid, '%s,%s,%.4f,%.4f,%.4f,%.2f\n', keys{k}, methods{m}, p, ssim_index(x, out), p - p0, dt);
        fprintf('    %-8s %6.2f dB (%+6.2f)  %5.1f s\n', methods{m}, p, p - p0, dt);
    end
end
nz = make_mixed(x, 0);
[stages, slabels] = run_cascade(nz);
for k = 1:numel(stages)
    fprintf(fid, 'mixed,stage%d: %s,%.4f,%.4f,%.4f,0\n', k - 1, slabels{k}, psnr_db(x, stages{k}), ...
            ssim_index(x, stages{k}), psnr_db(x, stages{k}) - psnr_db(x, nz.y));
end
fclose(fid);

fprintf('\nPSNR gain (dB) on the 512 x 512 ''%s'' image\n%-24s %6s', name, 'noise', 'noisy');
fprintf(' %7s', methods{:});
fprintf('\n');
for k = 1:numel(keys)
    fprintf('%-24s %6.2f', labels{k}, P0(k));
    for m = 1:numel(methods)
        if isnan(G(k, m))
            fprintf(' %7s', 'n/a');
        else
            fprintf(' %+7.2f', G(k, m));
        end
    end
    fprintf('\n');
end
fprintf('\nAll noises at once, chained scenarios:\n');
for k = 1:numel(stages)
    fprintf('  %-45s %6.2f dB\n', slabels{k}, psnr_db(x, stages{k}));
end
