#!/usr/bin/env bash
# End-to-end ASIC reverse-engineering pipeline.
#   GDS --extract--> netlist.json --emit--> structural Verilog + cells.v
#   then validate: warmup (functional equiv to source RTL) and
#   puzzle (I/O equiv to the recorded silicon trace).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
export PATH="/opt/homebrew/bin:$PATH"
mkdir -p build

echo "### WARMUP: extract + validate against DEF ground truth"
$PY pipeline/extract_netlist.py warmup/04_final.gds build/warmup_netlist.json
$PY pipeline/check_vs_def.py build/warmup_netlist.json warmup/03_post_place_and_route.def

echo "### WARMUP: emit Verilog + 3-way functional check vs source RTL"
cat > build/warmup_ports.json <<'EOF'
{"inputs":["clk","rst_n","en","A","B"],"outputs":[["S",""]]}
EOF
$PY pipeline/emit_verilog.py build/warmup_netlist.json build/warmup_ports.json \
    build/warmup_extracted.v build/warmup_cells.v
sed 's/module adder_demo (/module adder_demo_ext (/' build/warmup_extracted.v > build/warmup_extracted_ext.v
iverilog -g2012 -o build/tb_warmup.vvp -s tb \
    build/tb_warmup.v warmup/00_source.v build/warmup_extracted_ext.v build/warmup_cells.v
vvp build/tb_warmup.vvp

echo "### PUZZLE: extract + emit"
$PY pipeline/extract_netlist.py puzzle.gds build/puzzle_netlist.json
cat > build/puzzle_ports.json <<'EOF'
{"inputs":["clk","rst_n","enable","I"],"outputs":[["O","[7:0] "],["success",""]]}
EOF
$PY pipeline/emit_verilog.py build/puzzle_netlist.json build/puzzle_ports.json \
    build/puzzle_extracted.v build/puzzle_cells.v

echo "### PUZZLE: derive cell logic from polygons alone (no Liberty), verify vs PDK"
$PY pipeline/gds_to_logic.py --verify
$PY pipeline/gds_to_logic.py --emit build/cells_from_layout.v

echo "### PUZZLE: recover the gate netlist from FLAT rectangles (no library, no"
echo "###         cell names, no pin labels) -- transistors -> CCRs -> functions"
$PY pipeline/verify_flat_chip.py

echo "### PUZZLE: replay recorded stimulus, compare O/success to real silicon"
$PY pipeline/vcd_to_tb.py example_inputs.vcd build/tb_puzzle_replay.v
iverilog -g2012 -o build/puzzle_replay.vvp -s tb \
    build/tb_puzzle_replay.v build/puzzle_extracted.v build/puzzle_cells.v
vvp build/puzzle_replay.vvp

echo "### PUZZLE: name-blind geometric cell mapping (definition level)"
$PY pipeline/cell_mapper.py puzzle.gds > build/mapper.out   # summary -> stderr
echo "exact-geometry matches: $(grep -c '^EXACT' build/mapper.out)"
grep -v '^EXACT' build/mapper.out || true

echo "### PUZZLE: flattened-layout cell identification (known footprints)"
PYTHONPATH=pipeline $PY pipeline/identify_flat.py puzzle.gds build/puzzle_netlist.json --n 2000 \
    2>&1 | grep -E 'accuracy|MISMATCH'

echo "### PUZZLE: auto-segmentation from flattened die (no hierarchy/placement)"
PYTHONPATH=pipeline $PY pipeline/auto_segment.py puzzle.gds --truth build/puzzle_netlist.json \
    2>&1 | grep -E 'detected|recovered|recall|false'

echo "### DONE"
