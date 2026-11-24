function out = apply_scenario(key, nz)
%APPLY_SCENARIO Run scenario KEY ('A', 'B', 'C', 'D', 'Dg', 'E', 'F') on the noisy record NZ with its fixed,
%   documented default parameters (nothing is tuned on the clean image). Returns [] when the scenario needs
%   a reference that this noise does not provide (F on noise without a physical reference).
y = nz.y;
s = nz.side;
switch key
    case 'A'
        out = adaptive_notch(y, [], 0.001);
    case 'B'
        out = interline_canceller(y, 0.001, 2, 16);
    case 'C'
        out = subband_canceller(y);
    case 'D'
        out = self_tuning(y);
    case 'Dg'
        out = self_tuning_gated(y);
    case 'E'
        out = line_enhancer(y);
    case 'F'
        if isfield(s, 'ob') && ~isfield(s, 'ref_out')
            w = train_row_weight(s.dark, s.dark_ob);
            out = row_reference_canceller(y, s.ob, w);
        elseif isfield(s, 'ref_out') && ~isfield(s, 'ob')
            out = channel_reference_canceller(y, s.ref_out, 1, 1e-3, s.dark, s.dark_ref);
        else
            out = [];
        end
    otherwise
        error('apply_scenario:key', 'unknown scenario %s', key);
end
end
