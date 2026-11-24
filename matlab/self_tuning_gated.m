function [out, flags] = self_tuning_gated(img, r, alpha, k, passes)
%SELF_TUNING_GATED Scenario D, error-gated version for sparse noise (see BLINDSPOT_GATED).
if nargin < 2 || isempty(r), r = 2; end
if nargin < 3 || isempty(alpha), alpha = 0.01; end
if nargin < 4 || isempty(k), k = 4.0; end
if nargin < 5 || isempty(passes), passes = 3; end
[out, flags] = blindspot_gated(img, r, alpha, k, passes);
end
