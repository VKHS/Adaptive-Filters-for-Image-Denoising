function [y, hole, info] = line_enhancer(img, r, hole, alpha, passes)
%LINE_ENHANCER Scenario E: blind-spot predictor with a larger window and a blind spot (the delay) matched to
%   the measured noise correlation (CHOOSE_HOLE when hole is empty). At least two rings of taps are kept.
if nargin < 2 || isempty(r), r = 3; end
if nargin < 3 || isempty(hole), hole = choose_hole(img); end
if nargin < 4 || isempty(alpha), alpha = 0.01; end
if nargin < 5 || isempty(passes), passes = 2; end
r = max(r, hole + 2);
[y, info] = blindspot_lms(img, r, hole, alpha, [], passes, 'lms');
end
