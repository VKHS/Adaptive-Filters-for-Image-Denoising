function out = local_wiener(img, sz, sigma)
%LOCAL_WIENER Local-statistics Wiener filter in an sz x sz window (default 5):
%   m + max(v - s^2, 0) / max(v, s^2) (y - m); the noise level is estimated when sigma is not given.
if nargin < 2 || isempty(sz), sz = 5; end
if nargin < 3 || isempty(sigma), sigma = estimate_noise_sigma(img); end
s2 = sigma^2;
h = (sz - 1) / 2;
k = ones(sz) / sz^2;
m = conv2(pad_reflect(img, h), k, 'valid');
v = conv2(pad_reflect(img .* img, h), k, 'valid') - m .* m;
out = m + max(v - s2, 0) ./ max(v, s2) .* (img - m);
end
