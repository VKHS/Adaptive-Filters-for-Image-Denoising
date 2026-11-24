function P = welch2d(img, block, step)
%WELCH2D Average of Hann-windowed periodograms of overlapping blocks (fftshift-ed, DC in the middle).
if nargin < 2 || isempty(block), block = 128; end
if nargin < 3 || isempty(step), step = 64; end
[H, W] = size(img);
w1 = hann_sym(block);
win = w1 * w1.';
acc = zeros(block, block);
n = 0;
for i0 = 1:step:H - block + 1
    for j0 = 1:step:W - block + 1
        b = img(i0:i0 + block - 1, j0:j0 + block - 1);
        b = (b - mean(b(:))) .* win;
        acc = acc + abs(fft2(b)).^2;
        n = n + 1;
    end
end
P = fftshift(acc / n);
end
