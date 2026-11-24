function f = fftfreq(n)
%FFTFREQ Sample frequencies of an n-point DFT in cycles/sample, in DFT order (as numpy.fft.fftfreq).
k = 0:n-1;
k(k >= ceil(n / 2)) = k(k >= ceil(n / 2)) - n;
f = k / n;
end
