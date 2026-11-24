function h = choose_hole(img, rho_max, max_hole)
%CHOOSE_HOLE Blind-spot half-width from the noise correlation length (the line-enhancer delay rule):
%   the largest lag k with rho(k) > rho_max, 0 for white noise.
if nargin < 2 || isempty(rho_max), rho_max = 0.2; end
if nargin < 3 || isempty(max_hole), max_hole = 3; end
rho = noise_correlation(img, 16, 0.1, max_hole);
h = 0;
for k = 1:max_hole
    if rho(k) > rho_max
        h = k;
    else
        break
    end
end
end
