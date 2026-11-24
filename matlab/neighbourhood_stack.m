function S = neighbourhood_stack(img, s)
%NEIGHBOURHOOD_STACK H x W x s^2 array of the s x s neighbourhood of every pixel (mirror boundary,
%   edge not repeated), for median, minimum and maximum filters without toolboxes.
h = (s - 1) / 2;
[H, W] = size(img);
P = pad_reflect(img, h);
S = zeros(H, W, s * s);
n = 0;
for a = 0:s - 1
    for b = 0:s - 1
        n = n + 1;
        S(:, :, n) = P(1 + a:H + a, 1 + b:W + b);
    end
end
end
