#!/usr/bin/env python3
"""Emit yosys/Verilator-friendly behavioral models for the sky130 cells the
puzzle uses. Combinational cells come straight from the PDK Liberty function
strings (authoritative); the 3 flop types are simple behavioral models with
their reset value baked into `initial` (so a solver starts from the post-reset
state and we drive rst_n=1). No UDPs, no `include, no macros -> clean RTLIL."""
import glob
import json
import re
import sys

LIB = "lib/sky130_fd_sc_hd"


def cell_dirs(cell):
    fam = cell.rsplit("_", 1)[0]
    return sorted(glob.glob(f"{LIB}/cells/{fam}/*__*.lib.json"))


def liberty_pins(cell):
    """Return (inputs, outputs{pin:func}) from any strength's lib.json."""
    cands = cell_dirs(cell)
    if not cands:
        return None
    d = json.load(open(cands[0]))
    ins, outs = [], {}
    for k, v in d.items():
        if not k.startswith("pin,") or not isinstance(v, dict):
            continue
        pin = k[4:]
        if v.get("direction") == "input":
            ins.append(pin)
        elif v.get("direction") == "output":
            outs[pin] = v.get("function")
    return ins, outs


def to_verilog(expr):
    return expr.replace("!", "~") if expr else expr


def emit_comb(base, ins, outs):
    ports = ins + list(outs)
    lines = [f"module sky130_fd_sc_hd__{base} (" + ", ".join(ports) + ");"]
    for p in ins:
        lines.append(f"  input {p};")
    for p in outs:
        lines.append(f"  output {p};")
    for p, fn in outs.items():
        if fn in ("1", "0"):
            lines.append(f"  assign {p} = 1'b{fn};")
        else:
            lines.append(f"  assign {p} = {to_verilog(fn)};")
    lines.append("endmodule")
    return "\n".join(lines)


FLOP_SRC = {
    "dfrtp": """module sky130_fd_sc_hd__dfrtp (CLK, D, RESET_B, Q);
  input CLK, D, RESET_B; output reg Q;
  initial Q = 1'b0;
  always @(posedge CLK or negedge RESET_B)
    if (!RESET_B) Q <= 1'b0; else Q <= D;
endmodule""",
    "dfstp": """module sky130_fd_sc_hd__dfstp (CLK, D, SET_B, Q);
  input CLK, D, SET_B; output reg Q;
  initial Q = 1'b1;
  always @(posedge CLK or negedge SET_B)
    if (!SET_B) Q <= 1'b1; else Q <= D;
endmodule""",
    "dfxtp": """module sky130_fd_sc_hd__dfxtp (CLK, D, Q);
  input CLK, D; output reg Q;
  initial Q = 1'b0;
  always @(posedge CLK) Q <= D;
endmodule""",
}


PHYSICAL = {"decap", "diode", "tapvpwrvgnd", "fill", "tap"}


def main():
    js = json.load(open("build/puzzle_netlist.json"))
    # module names in the netlist are BASE names (strength stripped)
    bases = sorted({i["cell"].split("__")[-1].rsplit("_", 1)[0]
                    for i in js["instances"]})
    out = ["// auto-generated yosys-friendly sky130 cell models",
           "`default_nettype none"]
    for base in bases:
        if base in ("dfrtp", "dfstp", "dfxtp"):
            out.append(FLOP_SRC[base]); continue
        if base in PHYSICAL:
            continue                       # not instantiated (emitter skips them)
        # find liberty via any strength of this family
        lp = None
        for cand in sorted(glob.glob(f"{LIB}/cells/{base}/*__*.lib.json")):
            d = json.load(open(cand))
            ins, outs = [], {}
            for k, v in d.items():
                if k.startswith("pin,") and isinstance(v, dict):
                    if v.get("direction") == "input":
                        ins.append(k[4:])
                    elif v.get("direction") == "output":
                        outs[k[4:]] = v.get("function")
            if outs:
                lp = (ins, outs); break
        if lp is None:
            print(f"WARN no liberty function for {base}", file=sys.stderr); continue
        out.append(emit_comb(base, *lp))
    open("build/cells_yosys.v", "w").write("\n\n".join(out) + "\n")
    print(f"wrote build/cells_yosys.v ({len(bases)} base cell types)")


if __name__ == "__main__":
    main()
