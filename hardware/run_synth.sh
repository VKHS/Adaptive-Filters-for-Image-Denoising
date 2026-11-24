#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v yosys >/dev/null || { echo "Yosys is required" >&2; exit 127; }
for top in scenario_a_notch scenario_b_bias scenario_c_periodic scenario_d_self_tuning scenario_e_line_enhancer scenario_f_reference; do
    echo "=== Elaborate and structurally check $top ==="
    yosys -Q -T -p "read_verilog hardware/rtl/*.v; hierarchy -check -top $top; proc; opt; check -assert; stat"
done
echo "All six default tops passed generic structural synthesis checks"
