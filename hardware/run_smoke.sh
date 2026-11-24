#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "Icarus Verilog (iverilog) is required" >&2; exit 127; }
command -v vvp >/dev/null || { echo "vvp is required" >&2; exit 127; }
python3 hardware/model/fixed_model.py
build="$(mktemp -d)"
trap 'rm -rf "$build"' EXIT
tests=(a b c d e f frontends window gaussian)
if [[ $# -gt 0 ]]; then tests=("$@"); fi
for name in "${tests[@]}"; do
    case "$name" in a|b|c|d|e|f|frontends|window|gaussian) ;; *) echo "Unknown test: $name"; exit 2;; esac
    iverilog -g2012 -Wall -s "tb_$name" -o "$build/$name.vvp" hardware/rtl/*.v "hardware/tb/tb_$name.v"
    vvp "$build/$name.vvp"
done
echo "Requested RTL smoke tests passed"
