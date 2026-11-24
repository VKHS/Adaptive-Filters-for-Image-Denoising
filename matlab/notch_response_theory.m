function Hz = notch_response_theory(omega0, mu2C2, omega)
%NOTCH_RESPONSE_THEORY Closed-loop response of the two-weight LMS notch at frequencies omega (rad/sample):
%   H(z) = (z^2 - 2 cos(omega0) z + 1) / (z^2 - 2 (1 - mu2 C^2 / 2) cos(omega0) z + 1 - mu2 C^2).
z = exp(1i * omega);
Hz = (z.^2 - 2 * cos(omega0) * z + 1) ./ (z.^2 - 2 * (1 - mu2C2 / 2) * cos(omega0) * z + 1 - mu2C2);
end
