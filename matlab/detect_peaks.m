function peaks = detect_peaks(img, thresh, contrast, fmin, max_peaks, block, step)
%DETECT_PEAKS Periodic-interference peaks of the 2-D spectrum. Returns one row [u v ratio] per +-(u, v)
%   pair, strongest first; u = vertical frequency (cycles per row), v = horizontal (cycles per column).
%   A bin is accepted when it is a local maximum (5 x 5), exceeds THRESH times the local median (9 x 9) of the
%   averaged spectrum, lies beyond FMIN from DC, and exceeds CONTRAST times its neighbours along both
%   frequency axes (a point, not a line such as row banding). The location is refined on the
%   zero-padded full-image spectrum.
if nargin < 2 || isempty(thresh), thresh = 30; end
if nargin < 3 || isempty(contrast), contrast = 10; end
if nargin < 4 || isempty(fmin), fmin = 0.03; end
if nargin < 5 || isempty(max_peaks), max_peaks = 6; end
if nargin < 6 || isempty(block), block = 128; end
if nargin < 7 || isempty(step), step = 64; end
P = welch2d(img, block, step);
R = P ./ max(circ_filter(P, 9, 'median'), 1e-30);
f = fftshift(fftfreq(block));
[V, U] = meshgrid(f, f);
rad = sqrt(U.^2 + V.^2);
half = (V > 0) | ((V == 0) & (U > 0));
cand = (R == circ_filter(R, 5, 'max')) & (R > thresh) & (rad > fmin) & half;
idx = find(cand);
[~, order] = sort(R(idx), 'descend');
peaks = zeros(0, 3);
for q = order(:).'
    [ki, kj] = ind2sub(size(R), idx(q));
    if directional_contrast(P, ki, kj, 5) < contrast
        continue
    end
    [u, v] = refine_peak(img, f(ki), f(kj), 1.5 / block, 2);
    peaks(end + 1, :) = [u, v, R(ki, kj)]; %#ok<AGROW>
    if size(peaks, 1) == max_peaks
        break
    end
end
end

function out = circ_filter(P, s, kind)
% Median or maximum over an s x s window with periodic (wrap-around) boundaries.
h = (s - 1) / 2;
stack = zeros([size(P), s * s]);
n = 0;
for a = -h:h
    for b = -h:h
        n = n + 1;
        stack(:, :, n) = circshift(P, [a b]);
    end
end
if strcmp(kind, 'median')
    out = median(stack, 3);
else
    out = max(stack, [], 3);
end
end

function c = directional_contrast(P, ki, kj, reach)
% Peak height over the median of its neighbours along u and along v (centre +-1 excluded), the smaller.
n = size(P, 1);
offs = [-reach:-2, 2:reach];
along_u = median(P(mod(ki - 1 + offs, n) + 1, kj));
along_v = median(P(ki, mod(kj - 1 + offs, n) + 1));
c = min(P(ki, kj) / max(along_u, 1e-30), P(ki, kj) / max(along_v, 1e-30));
end

function [u, v] = refine_peak(img, u0, v0, search, padf)
% Parabolic refinement (in log power) on the zero-padded full-image spectrum.
[H, W] = size(img);
win = hann_sym(H) * hann_sym(W).';
NU = padf * H;
NV = padf * W;
F = abs(fft2((img - mean(img(:))) .* win, NU, NV)).^2;
fu = fftfreq(NU);
fv = fftfreq(NV);
iu = find(abs(mod(fu - u0 + 0.5, 1) - 0.5) <= search);
iv = find(abs(mod(fv - v0 + 0.5, 1) - 0.5) <= search);
sub = F(iu, iv);
[~, lin] = max(sub(:));
[a, b] = ind2sub(size(sub), lin);
ku = iu(a);
kv = iv(b);
du = parab(F(mod(ku - 2, NU) + 1, kv), F(ku, kv), F(mod(ku, NU) + 1, kv));
dv = parab(F(ku, mod(kv - 2, NV) + 1), F(ku, kv), F(ku, mod(kv, NV) + 1));
u = mod((ku - 1 + du) / NU + 0.5, 1) - 0.5;
v = mod((kv - 1 + dv) / NV + 0.5, 1) - 0.5;
if v < 0 || (v == 0 && u < 0)
    u = -u;
    v = -v;
end
end

function d = parab(l, c, r)
l = log(l + 1e-30);
c = log(c + 1e-30);
r = log(r + 1e-30);
den = l - 2 * c + r;
if den == 0
    d = 0;
else
    d = 0.5 * (l - r) / den;
end
end
