function g = gaussian_kernel(sigma, radius)
%GAUSSIAN_KERNEL Normalised 1-D Gaussian (row vector) of the given radius (default ceil(3.5 sigma)).
if nargin < 2
    radius = ceil(3.5 * sigma);
end
t = -radius:radius;
g = exp(-t.^2 / (2 * sigma^2));
g = g / sum(g);
end
