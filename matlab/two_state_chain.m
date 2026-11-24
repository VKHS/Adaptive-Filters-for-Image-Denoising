function s = two_state_chain(n, p01, p10, start)
%TWO_STATE_CHAIN Two-state Markov chain (states 0/1) of length n from geometric run lengths.
%   p01 = P(0 -> 1) and p10 = P(1 -> 0) per sample; mean dwell times are 1/p01 and 1/p10.
pi1 = p01 / (p01 + p10);
if nargin < 4
    state = double(rand < pi1);
else
    state = start;
end
s = zeros(n, 1);
pos = 0;
while pos < n
    if state == 0
        p_leave = p01;
    else
        p_leave = p10;
    end
    run = floor(log(1 - rand) / log(1 - p_leave)) + 1;
    s(pos + 1:min(pos + run, n)) = state;
    pos = pos + run;
    state = 1 - state;
end
end
