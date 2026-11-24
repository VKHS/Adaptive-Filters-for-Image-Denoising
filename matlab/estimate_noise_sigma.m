function s = estimate_noise_sigma(img)
%ESTIMATE_NOISE_SIGMA Robust white-noise level: finest diagonal Haar detail, median(|d|) / 0.6745.
H = floor(size(img, 1) / 2) * 2;
W = floor(size(img, 2) / 2) * 2;
x = img(1:H, 1:W);
d = (x(1:2:end, 1:2:end) - x(1:2:end, 2:2:end) - x(2:2:end, 1:2:end) + x(2:2:end, 2:2:end)) / 2;
s = median(abs(d(:))) / 0.6745;
end
