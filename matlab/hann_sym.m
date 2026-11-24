function w = hann_sym(n)
%HANN_SYM Symmetric Hann window with zero end points (as numpy.hanning), column vector.
w = 0.5 - 0.5 * cos(2 * pi * (0:n-1)' / (n - 1));
end
