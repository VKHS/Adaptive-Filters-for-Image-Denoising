function [y, info] = self_tuning(img, r, alpha, passes)
%SELF_TUNING Scenario D: blind-spot LMS predictor with a single-pixel blind spot; returns the filter output.
if nargin < 2 || isempty(r), r = 2; end
if nargin < 3 || isempty(alpha), alpha = 0.01; end
if nargin < 4 || isempty(passes), passes = 2; end
[y, info] = blindspot_lms(img, r, 0, alpha, [], passes, 'lms');
end
