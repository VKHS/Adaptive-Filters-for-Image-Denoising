function [y, w] = rows_lms(z, L, delay, mu2)
%ROWS_LMS LMS predictor along each row (weights carried from row to row): z(n) is predicted from
%   z(n - delay - k), k = 0..L-1, with mirror padding at the start of the row. Returns the prediction y.
[H, W] = size(z);
P0 = delay + L - 1;
w = zeros(L, 1);
y = zeros(H, W);
for i = 1:H
    row = z(i, :);
    p = [row(P0 + 1:-1:2), row];
    for j = 1:W
        x = p(j + L - 1:-1:j).';
        yj = w.' * x;
        w = w + (mu2 * (row(j) - yj)) * x;
        y(i, j) = yj;
    end
end
end
