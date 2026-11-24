function [y, e, w] = ale_lms(d, L, delay, mu2)
%ALE_LMS One-dimensional LMS adaptive line enhancer: y(n) = w.[d(n-delay), ..., d(n-delay-L+1)].
n = numel(d);
w = zeros(L, 1);
y = zeros(n, 1);
e = zeros(n, 1);
for t = delay + L + 1:n
    x = d(t - delay:-1:t - delay - L + 1);
    x = x(:);
    y(t) = w.' * x;
    e(t) = d(t) - y(t);
    w = w + mu2 * e(t) * x;
end
end
