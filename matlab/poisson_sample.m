function k = poisson_sample(lambda)
%POISSON_SAMPLE Poisson random numbers with means lambda (any shape). Uses poissrnd when the Statistics
%   Toolbox is installed, otherwise the multiplication method (fine for means up to a few hundred).
if exist('poissrnd', 'file') == 2
    k = poissrnd(lambda);
    return
end
L = exp(-lambda);
k = zeros(size(lambda));
p = rand(size(lambda));
active = p > L;
while any(active(:))
    k(active) = k(active) + 1;
    p(active) = p(active) .* rand(nnz(active), 1);
    active = p > L;
end
end
