function y = pad_reflect(x, r, dims)
%PAD_REFLECT Mirror padding WITHOUT repeating the edge sample: [c b | a b c d | c b].
%   y = pad_reflect(x, r) pads both dimensions of the matrix x by r samples.
%   y = pad_reflect(x, r, dims) pads only the listed dimensions (1 = rows, 2 = columns).
%   This is numpy.pad(mode='reflect') and scipy.ndimage mode 'mirror'.
if nargin < 3
    dims = [1 2];
end
y = x;
for d = dims
    n = size(y, d);
    idx = [r+1:-1:2, 1:n, n-1:-1:n-r];
    if d == 1
        y = y(idx, :);
    else
        y = y(:, idx);
    end
end
end
