function s = ssim_index(ref, est)
%SSIM_INDEX Structural similarity: 11 x 11 Gaussian window (sigma 1.5), K1 = 0.01, K2 = 0.03, range 1.
%   The estimate is clipped to [0, 1]; the mean excludes a 5-pixel border.
x = ref;
y = min(max(est, 0), 1);
C1 = 0.01^2;
C2 = 0.03^2;
mx = gaussian_blur(x, 1.5, 5);
my = gaussian_blur(y, 1.5, 5);
sxx = gaussian_blur(x .* x, 1.5, 5) - mx .* mx;
syy = gaussian_blur(y .* y, 1.5, 5) - my .* my;
sxy = gaussian_blur(x .* y, 1.5, 5) - mx .* my;
m = ((2 * mx .* my + C1) .* (2 * sxy + C2)) ./ ((mx.^2 + my.^2 + C1) .* (sxx + syy + C2));
m = m(6:end-5, 6:end-5);
s = mean(m(:));
end
