function [out, track] = bias_canceller(img, mu2, update, tau)
%BIAS_CANCELLER Scenario B, textbook form: one weight b on a constant reference, along every row.
%   e = d - b is the output. update = 'lms' (b <- b + mu2 e), 'sign' (b <- b + mu2 sign(e), median
%   tracking) or 'gated' (LMS step only when |e| < tau, i.e. on background pixels). The weight starts each
%   row at the median of its first 8 pixels. H(z) = (z - 1) / (z - (1 - mu2)) is a high-pass, so slow scene
%   brightness is removed together with the drift unless the background is flat.
if nargin < 2 || isempty(mu2), mu2 = 0.02; end
if nargin < 3 || isempty(update), update = 'lms'; end
if nargin < 4 || isempty(tau), tau = 0.08; end
[H, W] = size(img);
out = zeros(H, W);
track = zeros(H, W);
for i = 1:H
    row = img(i, :);
    b = median(row(1:8));
    for j = 1:W
        e = row(j) - b;
        out(i, j) = e;
        track(i, j) = b;
        switch update
            case 'lms'
                b = b + mu2 * e;
            case 'sign'
                if e > 0
                    b = b + mu2;
                elseif e < 0
                    b = b - mu2;
                end
            case 'gated'
                if abs(e) < tau
                    b = b + mu2 * e;
                end
        end
    end
end
end
