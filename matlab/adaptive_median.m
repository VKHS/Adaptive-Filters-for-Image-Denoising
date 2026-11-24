function out = adaptive_median(img, smax)
%ADAPTIVE_MEDIAN Adaptive median filter: grow the window (3, 5, ..., smax) until its median is not an
%   extreme value; keep the pixel if it is not an extreme of that window, otherwise use the median.
if nargin < 2 || isempty(smax)
    smax = 7;
end
out = median(neighbourhood_stack(img, smax), 3);
done = false(size(img));
for s = 3:2:smax
    S = neighbourhood_stack(img, s);
    zmed = median(S, 3);
    zmin = min(S, [], 3);
    zmax = max(S, [], 3);
    ok = (zmin < zmed) & (zmed < zmax) & ~done;
    keep = ok & (zmin < img) & (img < zmax);
    out(keep) = img(keep);
    rep = ok & ~keep;
    out(rep) = zmed(rep);
    done = done | ok;
end
end
