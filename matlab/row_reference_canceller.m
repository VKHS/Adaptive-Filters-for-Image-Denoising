function out = row_reference_canceller(y, ob, w)
%ROW_REFERENCE_CANCELLER Subtract w times the optical-black row mean from every pixel of the row.
out = y - w * repmat(mean(ob, 2), 1, size(y, 2));
end
