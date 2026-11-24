function p = plane_waves(H, W, comps)
%PLANE_WAVES Sum of A cos(2 pi (u i + v j) + phase) for each row [A u v phase] of comps (i, j from 0).
[j, i] = meshgrid(0:W-1, 0:H-1);
p = zeros(H, W);
for k = 1:size(comps, 1)
    p = p + comps(k, 1) * cos(2 * pi * (comps(k, 2) * i + comps(k, 3) * j) + comps(k, 4));
end
end
