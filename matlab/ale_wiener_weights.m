function w = ale_wiener_weights(L, delay, snr, omega0, noise_power)
%ALE_WIENER_WEIGHTS Exact Wiener-Hopf weights of an L-tap line enhancer (prediction distance delay) for a
%   sinusoid of power snr * noise_power at omega0 (rad/sample) in white noise.
if nargin < 5
    noise_power = 1;
end
k = 0:L + delay;
phi = snr * noise_power * cos(omega0 * k);
phi(1) = phi(1) + noise_power;
R = toeplitz(phi(1:L));
p = phi(delay + 1:delay + L).';
w = R \ p;
end
