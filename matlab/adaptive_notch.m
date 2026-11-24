function [out, freqs] = adaptive_notch(img, freqs, mu2)
%ADAPTIVE_NOTCH Scenario A end to end: detect the interference frequencies (unless given as a K x 2 matrix
%   of [u v]) and cancel them with NOTCH_LMS. With no detected peak the image is returned unchanged.
if nargin < 2
    freqs = [];
end
if nargin < 3 || isempty(mu2)
    mu2 = 0.001;
end
if isempty(freqs)
    pk = detect_peaks(img);
    freqs = pk(:, 1:2);
end
if isempty(freqs)
    out = img;
    return
end
out = notch_lms(img, freqs, mu2, 1, 2);
end
