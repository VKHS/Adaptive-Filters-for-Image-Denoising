function y = gaussian_blur(x, sigma, radius)
%GAUSSIAN_BLUR Separable Gaussian smoothing with edge-repeating mirror boundaries.
if nargin < 3
    radius = ceil(3.5 * sigma);
end
g = gaussian_kernel(sigma, radius);
y = conv2(pad_symmetric(x, radius, 1), g(:), 'valid');
y = conv2(pad_symmetric(y, radius, 2), g, 'valid');
end
