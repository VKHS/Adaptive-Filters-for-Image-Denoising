function [stages, labels] = run_cascade(nz)
%RUN_CASCADE Chain the scenarios on an image that carries every corruption (MAKE_MIXED).
%   Order: references first (F: optical-black columns for row banding, reference output for readout
%   telegraph), then the periodic part (A), then the sparse part (D, error-gated), then the broadband rest
%   (E). Returns a cell array of images (input first) and their labels.
s = nz.side;
stages = {nz.y};
labels = {'input'};
y = nz.y;
w = train_row_weight(s.dark, s.dark_ob);
y = row_reference_canceller(y, s.ob, w);
stages{end + 1} = y;
labels{end + 1} = 'F: optical-black reference (row banding)';
y = channel_reference_canceller(y, s.ref_out, 1, 1e-3, s.dark, s.dark_ref);
stages{end + 1} = y;
labels{end + 1} = 'F: reference output (readout telegraph)';
y = adaptive_notch(y, [], 0.001);
stages{end + 1} = y;
labels{end + 1} = 'A: adaptive notch (periodic)';
y = self_tuning_gated(y);
stages{end + 1} = y;
labels{end + 1} = 'D, error-gated (impulses, bursts)';
y = line_enhancer(y);
stages{end + 1} = y;
labels{end + 1} = 'E: line enhancer (broadband rest)';
end
