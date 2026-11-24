function out = apply_filter(img, kern)
%APPLY_FILTER Apply a learned kernel as a correlation (mirror boundary), keeping the image mean.
r = (size(kern, 1) - 1) / 2;
m = mean(img(:));
out = conv2(pad_reflect(img - m, r), rot90(kern, 2), 'valid') + m;
end
