function w = train_row_weight(dark, dark_ob, mu2, passes)
%TRAIN_ROW_WEIGHT Scenario F, banding: LMS on a dark frame. d = dark pixel, x = mean of the row's
%   optical-black (masked) pixels. Returns the weight w.
if nargin < 3 || isempty(mu2), mu2 = 0.5; end
if nargin < 4 || isempty(passes), passes = 3; end
[H, W] = size(dark);
xr = mean(dark_ob, 2);
w = 0;
for p = 1:passes
    for i = 1:H
        x = xr(i);
        row = dark(i, :);
        for j = 1:W
            w = w + mu2 * (row(j) - w * x) * x;
        end
    end
end
end
