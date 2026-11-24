function [out, w] = row_reference_online(y, ob, mu2, mode)
%ROW_REFERENCE_ONLINE Online variants of the banding canceller, for comparison.
%   mode = 'scene'   : adapt on every scene pixel. Fails: the scene's row means swamp the update.
%   mode = 'ob_gated': adapt only on the optical-black pixels (each predicted from the mean of the other
%                      masked pixels of its row), then correct the scene pixels of that row.
if nargin < 3 || isempty(mu2), mu2 = 0.5; end
if nargin < 4 || isempty(mode), mode = 'ob_gated'; end
[H, W] = size(y);
K = size(ob, 2);
out = zeros(H, W);
w = 0;
for i = 1:H
    xr = mean(ob(i, :));
    if strcmp(mode, 'ob_gated')
        s = sum(ob(i, :));
        for k = 1:K
            xk = (s - ob(i, k)) / (K - 1);
            w = w + mu2 * (ob(i, k) - w * xk) * xk;
        end
        out(i, :) = y(i, :) - w * xr;
    else
        for j = 1:W
            e = y(i, j) - w * xr;
            out(i, j) = e;
            w = w + mu2 * e * xr;
        end
    end
end
end
