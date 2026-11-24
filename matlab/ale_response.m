function Hw = ale_response(w, delay, omega)
%ALE_RESPONSE Frequency response sum_k w_k exp(-1i omega (delay + k)) of a line enhancer, at omega.
k = (0:numel(w) - 1);
Hw = exp(-1i * omega(:) * (delay + k)) * w(:);
end
