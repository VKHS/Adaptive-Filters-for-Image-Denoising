function G = ale_peak_gain(L, snr)
%ALE_PEAK_GAIN Peak gain of the converged line enhancer at the line: (L/2) SNR / ((L/2) SNR + 1).
G = (L / 2 .* snr) ./ (L / 2 .* snr + 1);
end
