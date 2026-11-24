function y = pad_symmetric(x, r, dims)
%PAD_SYMMETRIC Mirror padding that repeats the edge sample: [b a | a b c d | d c].
%   This is numpy.pad(mode='symmetric') and scipy.ndimage mode 'reflect'.
if nargin < 3
    dims = [1 2];
end
y = x;
for d = dims
    n = size(y, d);
    idx = [r:-1:1, 1:n, n:-1:n-r+1];
    if d == 1
        y = y(idx, :);
    else
        y = y(:, idx);
    end
end
end
