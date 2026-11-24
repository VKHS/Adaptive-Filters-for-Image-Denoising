function [mask, a, b] = tap_mask(r, hole)
%TAP_MASK Taps of the 2-D blind-spot predictor: the (2r+1) x (2r+1) window without its central
%   (2h+1) x (2h+1) block. Also returns the 0-based row/column offsets a, b of the taps in row-major order
%   (the order of the weight vector, the same as in the Python code).
if nargin < 2
    hole = 0;
end
k = 2 * r + 1;
mask = true(k, k);
mask(r + 1 - hole:r + 1 + hole, r + 1 - hole:r + 1 + hole) = false;
[bb, aa] = find(mask.');
a = aa - 1;
b = bb - 1;
end
