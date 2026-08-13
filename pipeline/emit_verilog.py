#!/usr/bin/env python3
"""Emit a simulatable structural Verilog netlist from extracted JSON,
plus a cells.v that pulls in the sky130 functional models actually used.

Module type names have their drive-strength suffix stripped so they bind
to the (strength-independent) functional.v models. Only signal pins are
wired; power pins are omitted (functional models have none).
"""
import json
import os
import re
import sys

LIB = "lib/sky130_fd_sc_hd"
# cells that carry no logic — drop them entirely from simulation
PHYSICAL = {"tapvpwrvgnd", "decap", "fill", "diode", "tap"}


def base_type(cell):
    # sky130_fd_sc_hd__nand2_2 -> nand2 ; conb_1 -> conb ; clkbuf_16 -> clkbuf
    m = re.match(r"(sky130_fd_sc_hd__[a-z0-9]+?)_\d+$", cell)
    return m.group(1) if m else cell


def short(cell):
    return base_type(cell).replace("sky130_fd_sc_hd__", "")


POWER_PINS = {"VPWR", "VGND", "VPB", "VNB"}


BUSBIT = re.compile(r"^[A-Za-z_]\w*\[\d+\]$")


def emit_netlist(js, module, inputs, outputs):
    net_name = {str(k): v for k, v in js["nets"].items()}

    def wire(nid):
        nm = net_name.get(str(nid))
        if not nm:
            return f"n{nid}"
        if BUSBIT.match(nm):          # e.g. O[3] -> connect straight to bus bit
            return nm
        return re.sub(r"[^\w]", "_", nm)

    out_base = [(re.sub(r"\[.*", "", p).strip(), w) for p, w in outputs]
    plist = list(inputs) + [p for p, _ in out_base]
    lines = [f"module {module} (" + ", ".join(plist) + ");"]
    for p in inputs:
        lines.append(f"  input {p};")
    for p, w in out_base:
        lines.append(f"  output {w}{p};")

    used_types = set()
    body = []
    skipped = 0
    dropped = []
    for inst in js["instances"]:
        if short(inst["cell"]) in PHYSICAL:
            skipped += 1
            continue
        used_types.add(base_type(inst["cell"]))
        conns = []
        for pin, nid in sorted(inst["pins"].items()):
            if pin in POWER_PINS:
                continue
            if pin.startswith("pin"):          # extraction artifact, no library pin
                dropped.append((inst["name"], inst["cell"], pin, nid))
                continue
            conns.append(f".{pin}({wire(nid)})")
        body.append(f"  {base_type(inst['cell'])} {inst['name']} ( {', '.join(conns)} );")
    lines += body
    lines.append("endmodule")
    if dropped:
        print(f"WARNING: dropped {len(dropped)} unlabeled terminal(s) as no-connect "
              f"(inspect in KLayout):")
        for name, cell, pin, nid in dropped:
            print(f"  {name} {cell} {pin} (grazes net id {nid})")
    return "\n".join(lines), used_types, skipped


def emit_cells(used_types, out):
    seq_udps = set()
    inc = ["`timescale 1ns/1ps", "`define UNIT_DELAY", "`define FUNCTIONAL",
           "`default_nettype none"]
    bodies = []
    for t in sorted(used_types):
        base = t.replace("sky130_fd_sc_hd__", "")
        path = f"{LIB}/cells/{base}/sky130_fd_sc_hd__{base}.functional.v"
        if not os.path.exists(path):
            raise SystemExit(f"missing functional model: {path}")
        src = open(path).read()
        # rewrite relative UDP includes to absolute
        for m in re.finditer(r'`include\s+"([^"]+udp[^"]+)"', src):
            rel = m.group(1)
            absu = os.path.abspath(os.path.join(os.path.dirname(path), rel))
            seq_udps.add(absu)
            src = src.replace(f'"{rel}"', f'"{absu}"')
        bodies.append(src)
    with open(out, "w") as f:
        f.write("\n".join(inc) + "\n")
        f.write("\n".join(bodies))
    return seq_udps


def main():
    js = json.load(open(sys.argv[1]))
    module = js["top"]
    spec = json.load(open(sys.argv[2]))  # {"inputs":[...], "outputs":[["O","[7:0] "],...]}
    out_v = sys.argv[3]
    cells_v = sys.argv[4]
    netlist, used, skipped = emit_netlist(js, module, spec["inputs"], spec["outputs"])
    open(out_v, "w").write(netlist)
    udps = emit_cells(used, cells_v)
    print(f"emitted {out_v}: {len(used)} cell types, skipped {skipped} physical cells")
    print(f"cells.v: {cells_v} (+{len(udps)} udp models)")


if __name__ == "__main__":
    main()
