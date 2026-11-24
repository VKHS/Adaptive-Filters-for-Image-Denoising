function comps = periodic_components()
%PERIODIC_COMPONENTS Default periodic interference, one row per component: [amplitude u v phase].
%   u is the vertical frequency (cycles per row), v the horizontal frequency (cycles per column).
comps = [0.10, 0.000, 0.0925, 0.7;    % vertical stripes
         0.04, 0.000, 0.1850, 0.3;    % their second harmonic
         0.06, 0.137, 0.0610, 1.9];   % diagonal moire
end
