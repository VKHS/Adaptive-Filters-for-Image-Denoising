function [out, off] = interline_canceller(img, mu2, passes, hp_rows)
%INTERLINE_CANCELLER Scenario B, image form for row banding: a bias weight on the line-to-line difference.
%   For row i the primary is the row and the reference is the previous corrected row; the bias weight b_i
%   adapts along the row with a sign-error update on e = (row - previous) - b_i (so b_i converges to the
%   median line-to-line difference) and the corrected row is row - b_i. With hp_rows > 0 the slow part of
%   the sequence b_i (Gaussian, hp_rows rows) is put back, so slow scene shading survives.
if nargin < 2 || isempty(mu2), mu2 = 0.001; end
if nargin < 3 || isempty(passes), passes = 2; end
if nargin < 4, hp_rows = 16; end
[H, W] = size(img);
out = img;
off = zeros(H, 1);
for i = 2:H
    dif = img(i, :) - out(i - 1, :);
    b = 0;
    for p = 1:passes
        for j = 1:W
            e = dif(j) - b;
            if e > 0
                b = b + mu2;
            elseif e < 0
                b = b - mu2;
            end
        end
    end
    off(i) = b;
    out(i, :) = img(i, :) - b;
end
if ~isempty(hp_rows) && hp_rows > 0
    L = fix(4 * hp_rows);
    t = -L:L;
    g = exp(-t.^2 / (2 * hp_rows^2));
    g = g / sum(g);
    slow = conv(pad_reflect(off, L, 1), g(:), 'valid');
    out = out + repmat(slow, 1, W);
    off = off - slow;
end
end
