function [out, w] = notch_lms(img, freqs, mu2, C, passes)
%NOTCH_LMS Adaptive notch (scenario A) with synthetic 2-D plane-wave references, raster order.
%   For each frequency [u v] (a row of freqs) the reference pair C cos(theta), C sin(theta) with
%   theta = 2 pi (u i + v j) feeds two weights; the output is the error e = d - w.x. The image mean is
%   removed before and restored after. The first pass lets the weights converge; the last pass is returned.
if nargin < 3 || isempty(mu2), mu2 = 0.001; end
if nargin < 4 || isempty(C), C = 1; end
if nargin < 5 || isempty(passes), passes = 2; end
[H, W] = size(img);
m = mean(img(:));
z = img - m;
K = size(freqs, 1);
w = zeros(2 * K, 1);
out = zeros(H, W);
Rt = zeros(2 * K, W);
jj = 0:W-1;
for p = 1:passes
    for i = 1:H
        for k = 1:K
            th = 2 * pi * (freqs(k, 1) * (i - 1) + freqs(k, 2) * jj);
            Rt(2 * k - 1, :) = C * cos(th);
            Rt(2 * k, :) = C * sin(th);
        end
        d = z(i, :);
        for j = 1:W
            x = Rt(:, j);
            e = d(j) - w.' * x;
            w = w + (mu2 * e) * x;
            out(i, j) = e;
        end
    end
end
out = out + m;
end
