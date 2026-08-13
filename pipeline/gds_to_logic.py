#!/usr/bin/env python3
"""Reverse a sky130 standard cell from *layout polygons* to a logical operator,
using no PDK Liberty at all. The chain:

    GDS rectangles
      -> transistors        gate = poly & diff ; n/p split by nwell ; S/D = diff - poly
      -> nets               union-find through licon/mcon contacts ; pin names from labels
      -> Boolean function   switch-level fixed-point evaluation over every input pattern
      -> named operator     match the truth table to AND/OR/XOR/MUX/... + a minimal SOP

The only technology input is the *layer map* (which GDS layer number is poly,
diff, nwell, ...), never the cell library or its functions. Liberty is read
back only to *verify* the blind derivation. Sequential cells (cross-coupled
storage loops) don't reduce to a combinational table and are reported as such.

CLI:
    gds_to_logic.py <cell.gds>            derive one cell, print the virtual cell
    gds_to_logic.py --verify              derive every puzzle cell, check vs Liberty
"""
import glob
import itertools
import json
import sys

import klayout.db as db

# --- technology layer map (the only PDK-level input; not the cell library) ---
LAYER = dict(nwell=(64, 20), diff=(65, 20), poly=(66, 20),
             licon=(66, 44), li1=(67, 20), mcon=(67, 44), met1=(68, 20),
             li1_lbl=(67, 5), met1_lbl=(68, 5))
POWER = {"VPWR", "VDD", "VGND", "VSS", "VNB", "VPB"}


# ------------------------------- union-find --------------------------------
class UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


# --------------------------- geometry -> transistors -----------------------
def _region(top, ly, key):
    l, d = LAYER[key]
    idx = ly.find_layer(l, d)
    return db.Region(top.begin_shapes_rec(ly.layer(l, d))) if idx is not None else db.Region()


def _components(reg):
    """One single-polygon Region per orthogonally-connected component."""
    return [db.Region(p) for p in reg.merged().each()]


def extract_devices(gds_path):
    """From polygons alone: a transistor list and a named-net map.

    Returns dict with:
      devices: [{type: nmos|pmos, gate: net, sd: [net, net]}]
      pin_nets: sorted labelled pin nets (excludes power rails)
      power:   {net: 0|1}   (VGND->0, VPWR/VDD->1)
      term_count: {net: #transistor terminals on it}
    """
    ly = db.Layout()
    ly.read(gds_path)
    top = ly.top_cells()[0]

    nwell = _region(top, ly, "nwell")
    diff = _region(top, ly, "diff")
    poly = _region(top, ly, "poly")
    licon = _region(top, ly, "licon")
    mcon = _region(top, ly, "mcon")

    sd = diff - poly            # source/drain diffusion (channel removed)
    gates = poly & diff         # transistor channels

    # nodes: every connected conductor piece across the layers that carry nets
    kinds = []                  # parallel arrays: kind + single-poly Region
    regs = []
    for key in ("li1", "met1"):
        for r in _components(_region(top, ly, key)):
            kinds.append(key)
            regs.append(r)
    for r in _components(sd):
        kinds.append("sd")
        regs.append(r)
    for r in _components(poly):
        kinds.append("poly")
        regs.append(r)

    uf = UF(len(regs))

    def hits(pred, creg):
        return [i for i in range(len(regs)) if pred(kinds[i]) and regs[i].interacting(creg).count()]

    # licon ties li1 down to diff (S/D) or poly (gate); mcon ties li1 to met1
    for c in licon.each():
        cr = db.Region(c)
        for a in hits(lambda k: k in ("sd", "poly"), cr):
            for b in hits(lambda k: k == "li1", cr):
                uf.union(a, b)
    for c in mcon.each():
        cr = db.Region(c)
        for a in hits(lambda k: k == "li1", cr):
            for b in hits(lambda k: k == "met1", cr):
                uf.union(a, b)

    # net names from text labels: li1 carries pin names, met1 the power rails
    name = {}
    for lay, want in (("li1_lbl", ("li1",)), ("met1_lbl", ("li1", "met1"))):
        l, d = LAYER[lay]
        idx = ly.find_layer(l, d)
        if idx is None:
            continue
        for s in top.begin_shapes_rec(ly.layer(l, d)):
            if not s.shape().is_text():
                continue
            t = s.shape().text.transformed(s.itrans())
            box = db.Region(db.Box(t.x - 2, t.y - 2, t.x + 2, t.y + 2))
            for i in range(len(regs)):
                if kinds[i] in want and regs[i].interacting(box).count():
                    name[uf.find(i)] = t.string
                    break

    def netname(nid):
        return name.get(nid, f"n{nid}")

    # transistors: each channel polygon is one device
    devices = []
    term_count = {}
    for g in gates.merged().each():
        gr = db.Region(g)
        gate_poly = next((i for i in range(len(regs))
                          if kinds[i] == "poly" and regs[i].interacting(gr).count()), None)
        sds = [i for i in range(len(regs))
               if kinds[i] == "sd" and regs[i].interacting(gr).count()]
        typ = "pmos" if (gr & nwell).area() > 0.5 * gr.area() else "nmos"
        gnet = netname(uf.find(gate_poly)) if gate_poly is not None else "?"
        snets = [netname(uf.find(i)) for i in sds]
        for s in snets:
            term_count[s] = term_count.get(s, 0) + 1
        devices.append(dict(type=typ, gate=gnet, sd=snets))

    power = {}
    for nid, nm in name.items():
        u = nm.upper()
        if u in ("VGND", "VSS"):
            power[nm] = 0
        elif u in ("VPWR", "VDD"):
            power[nm] = 1
    pin_nets = sorted(nm for nm in set(name.values()) if nm.upper() not in POWER)
    return dict(devices=devices, pin_nets=pin_nets, power=power, term_count=term_count)


# ----------------------- switch-level evaluation ---------------------------
def eval_pattern(devices, driven):
    """Resolve every net for one assignment of the driven (input+rail) nets.

    A transistor conducts when NMOS gate=1 or PMOS gate=0. Nets joined by
    conducting transistors form components; a component takes the unique known
    value present in it (rail or pass-through input). Iterated to a fixed
    point. Returns the value map; nets left absent are undriven/bistable.
    """
    val = dict(driven)
    nets = set()
    for d in devices:
        nets.add(d["gate"])
        nets.update(d["sd"])
    idx = {n: i for i, n in enumerate(nets)}
    for _ in range(len(nets) + 4):
        uf = UF(len(nets))
        for d in devices:
            gv = val.get(d["gate"])
            if gv is None:
                continue
            on = (d["type"] == "nmos" and gv == 1) or (d["type"] == "pmos" and gv == 0)
            if on and len(d["sd"]) >= 2:
                for k in range(1, len(d["sd"])):
                    uf.union(idx[d["sd"][0]], idx[d["sd"][k]])
        comp = {}
        for n in nets:
            comp.setdefault(uf.find(idx[n]), []).append(n)
        changed = False
        for members in comp.values():
            known = {val[m] for m in members if m in val}
            if len(known) == 1:
                v = next(iter(known))
                for m in members:
                    if m not in val:
                        val[m] = v
                        changed = True
        if not changed:
            break
    return val


def derive(devices, pin_nets, power, term_count):
    """Return a virtual cell: inputs, outputs, per-output truth table + name,
    or {'kind':'sequential'} if it doesn't reduce to a combinational table."""
    if not devices:                              # e.g. conb: constant tie, no FETs
        return dict(kind="special", inputs=[], outputs=pin_nets, n_dev=0)
    gate_nets = {d["gate"] for d in devices}
    struct_inputs = [p for p in pin_nets if p in gate_nets]
    sd_only = [p for p in pin_nets if p not in gate_nets]
    # output(s): the sd-only pin(s) that are convergence nodes (most terminals).
    # pass-source inputs (e.g. a transmission-gate mux) sit on fewer terminals.
    if len(sd_only) <= 1:
        outputs = sd_only
    else:
        mx = max(term_count.get(p, 0) for p in sd_only)
        outputs = [p for p in sd_only if term_count.get(p, 0) == mx]
    inputs = [p for p in pin_nets if p not in outputs]

    if not outputs:                              # nothing to solve for
        return dict(kind="degenerate", inputs=inputs, outputs=outputs)

    tables = {o: [] for o in outputs}
    for bits in itertools.product((0, 1), repeat=len(inputs)):
        driven = dict(power)
        driven.update(dict(zip(inputs, bits)))
        val = eval_pattern(devices, driven)
        for o in outputs:
            v = val.get(o)
            if v is None:                        # bistable / undriven -> sequential
                return dict(kind="sequential", inputs=inputs, outputs=outputs,
                            n_dev=len(devices))
            tables[o].append(v)

    outs = {}
    for o in outputs:
        tt = tables[o]
        outs[o] = dict(truth=tt, expr=sop(inputs, tt), op=name_op(inputs, tt))
    return dict(kind="combinational", inputs=inputs, outputs=outs, n_dev=len(devices))


# --------------------------- naming & expressions --------------------------
def name_op(inputs, tt):
    """Best-effort operator name from the truth table; else None."""
    n = len(inputs)
    def table(f):
        return [1 if f(b) else 0 for b in itertools.product((0, 1), repeat=n)]
    cand = {}
    if n == 0:
        return "CONST1" if tt == [1] else "CONST0" if tt == [0] else None
    if n == 1:
        cand = {"BUF": table(lambda b: b[0]), "INV": table(lambda b: not b[0])}
    if n >= 2:
        cand["AND%d" % n] = table(lambda b: all(b))
        cand["OR%d" % n] = table(lambda b: any(b))
        cand["NAND%d" % n] = table(lambda b: not all(b))
        cand["NOR%d" % n] = table(lambda b: not any(b))
    if n == 2:
        cand["XOR2"] = table(lambda b: b[0] ^ b[1])
        cand["XNOR2"] = table(lambda b: not (b[0] ^ b[1]))
    for nm, t in cand.items():
        if t == tt:
            return nm
    if n == 3:
        # MUX2 over any choice of select input: out = sel ? a1 : a0
        for s in range(3):
            rest = [i for i in range(3) if i != s]
            for a0, a1 in ((rest[0], rest[1]), (rest[1], rest[0])):
                if table(lambda b, s=s, a0=a0, a1=a1: b[a1] if b[s] else b[a0]) == tt:
                    return "MUX2(sel=%s)" % inputs[s]
    return None


def _qm(minterms, n):
    """Quine-McCluskey prime implicants over n vars; returns list of (bits,mask)."""
    if not minterms:
        return []
    groups = {m: (m, 0) for m in minterms}      # (value, dash-mask)
    primes = set()
    terms = set(groups.values())
    while terms:
        nxt = set()
        used = set()
        tl = list(terms)
        for i in range(len(tl)):
            for j in range(i + 1, len(tl)):
                (v1, m1), (v2, m2) = tl[i], tl[j]
                if m1 != m2:
                    continue
                diff = v1 ^ v2
                if diff and (diff & (diff - 1)) == 0:   # exactly one bit differs
                    nxt.add((v1 & ~diff, m1 | diff))
                    used.add(tl[i])
                    used.add(tl[j])
        primes |= (terms - used)
        terms = nxt
    return list(primes)


def sop(inputs, tt):
    """Minimal-ish sum-of-products string for the truth table (QM + greedy cover)."""
    n = len(inputs)
    minterms = [i for i, v in enumerate(tt) if v]
    if not minterms:
        return "0"
    if len(minterms) == (1 << n):
        return "1"
    primes = _qm(minterms, n)

    def covers(term, m):
        v, mask = term
        return (m & ~mask) == v

    # greedy set cover of minterms by primes
    remaining = set(minterms)
    chosen = []
    while remaining:
        best = max(primes, key=lambda p: sum(1 for m in remaining if covers(p, m)))
        chosen.append(best)
        remaining -= {m for m in remaining if covers(best, m)}
        primes.remove(best)

    def lit(term):
        v, mask = term
        parts = []
        for b in range(n):
            bit = 1 << (n - 1 - b)               # input[0] is MSB
            if mask & bit:
                continue
            parts.append(inputs[b] if (v & bit) else "!" + inputs[b])
        return "&".join(parts) if parts else "1"
    return " | ".join("(%s)" % lit(t) for t in chosen)


# ------------------------------ verification -------------------------------
def liberty(base):
    """Ground-truth (inputs, {out: function}) from any strength's lib.json."""
    cands = sorted(glob.glob(f"lib/sky130_fd_sc_hd/cells/{base}/*.lib.json"))
    if not cands:
        return None
    d = json.load(open(cands[0]))
    ins, outs = [], {}
    for k, v in d.items():
        if k.startswith("pin,") and isinstance(v, dict):
            if v.get("direction") == "input":
                ins.append(k[4:])
            elif v.get("direction") == "output":
                outs[k[4:]] = v.get("function")
    return ins, outs


def eval_liberty(func, assign):
    """Evaluate a Liberty function string (& | ! () and 0/1) under assign."""
    if func in ("0", "1"):
        return int(func)
    py = func.replace("!", " not ").replace("&", " and ").replace("|", " or ")
    return int(bool(eval(py, {}, {k: bool(v) for k, v in assign.items()})))


def check_cell(gds_path, base):
    """Derive from polygons, compare every output to Liberty. Returns a report."""
    dev = extract_devices(gds_path)
    vc = derive(dev["devices"], dev["pin_nets"], dev["power"], dev["term_count"])
    lib = liberty(base)
    rep = dict(base=base, kind=vc["kind"], n_dev=vc.get("n_dev"))
    if vc["kind"] == "sequential":
        rep["ok"] = (lib is not None and any(
            p.upper() in ("CLK", "GATE") for p in lib[0]))    # has a clock/gate pin
        rep["note"] = "storage loop detected"
        return rep, vc
    if vc["kind"] != "combinational":
        rep["ok"] = None
        return rep, vc
    if lib is None:
        rep["ok"] = None
        return rep, vc
    lib_ins, lib_outs = lib
    inputs = vc["inputs"]
    ok = True
    details = {}
    # match derived outputs to liberty outputs by identical truth table
    for o, info in vc["outputs"].items():
        matched = None
        for lo, lf in lib_outs.items():
            lt = [eval_liberty(lf, dict(zip(inputs, b)))
                  for b in itertools.product((0, 1), repeat=len(inputs))]
            if lt == info["truth"]:
                matched = lo
                break
        details[o] = dict(op=info["op"], expr=info["expr"], matched=matched)
        ok = ok and matched is not None
    rep["ok"] = ok and set(inputs) == set(lib_ins)
    rep["inputs"] = inputs
    rep["details"] = details
    return rep, vc


def _print_cell(base, gds_path):
    rep, vc = check_cell(gds_path, base)
    print(f"\n=== {base}  ({gds_path.split('/')[-1]}) ===")
    print(f"transistors: {vc.get('n_dev')}   kind: {vc['kind']}")
    if vc["kind"] == "combinational":
        print(f"inputs:  {vc['inputs']}")
        for o, info in vc["outputs"].items():
            tag = f"  [{info['op']}]" if info["op"] else ""
            print(f"output {o} = {info['expr']}{tag}")
        m = "PASS" if rep["ok"] else "MISMATCH"
        print(f"vs Liberty: {m}")
    elif vc["kind"] == "sequential":
        print(f"inputs:  {vc['inputs']}   outputs: {vc['outputs']}")
        print("sequential (cross-coupled storage) -> no combinational table")


def verify_all():
    js = json.load(open("build/puzzle_netlist.json"))
    bases = sorted({i["cell"].split("__")[-1].rsplit("_", 1)[0]
                    for i in js["instances"]})
    comb_ok = comb_tot = 0
    seq = []
    special = []
    skip = []
    rows = []
    for b in bases:
        gds = sorted(glob.glob(f"lib/sky130_fd_sc_hd/cells/{b}/*_*.gds"))
        if not gds:
            skip.append(b)
            continue
        try:
            rep, vc = check_cell(gds[0], b)
        except Exception as e:                   # noqa: BLE001
            rows.append((b, "ERROR", str(e)[:40]))
            continue
        if vc["kind"] == "combinational":
            comb_tot += 1
            comb_ok += 1 if rep["ok"] else 0
            ops = ",".join(sorted({d["op"] or "SOP" for d in rep["details"].values()}))
            rows.append((b, "PASS" if rep["ok"] else "MISMATCH",
                         f"{vc['n_dev']}T  {ops}"))
        elif vc["kind"] == "sequential":
            seq.append(b)
            rows.append((b, "seq", f"{vc['n_dev']}T  {vc['outputs']}"))
        else:
            special.append(b)
            rows.append((b, vc["kind"], f"outputs {vc.get('outputs')}"))
    for b, st, info in rows:
        print(f"  {b:12} {st:9} {info}")
    print(f"\ncombinational cells derived-from-polygons vs Liberty: "
          f"{comb_ok}/{comb_tot} match")
    print(f"sequential (storage loop) detected: {len(seq)} -> {seq}")
    if special:
        print(f"special (no-FET constant/tie): {special}")
    if skip:
        print(f"no-gds/physical skipped: {skip}")


# --------- emit behavioural "virtual cells" derived from layout ------------
# The 3 flops are sequential (a storage loop, not a table); their edge/reset
# behaviour is the standard sky130 template, reused verbatim.
FLOP_SRC = {
    "dfrtp": ("module sky130_fd_sc_hd__dfrtp (CLK, D, RESET_B, Q);\n"
              "  input CLK, D, RESET_B; output reg Q; initial Q = 1'b0;\n"
              "  always @(posedge CLK or negedge RESET_B)\n"
              "    if (!RESET_B) Q <= 1'b0; else Q <= D;\nendmodule"),
    "dfstp": ("module sky130_fd_sc_hd__dfstp (CLK, D, SET_B, Q);\n"
              "  input CLK, D, SET_B; output reg Q; initial Q = 1'b1;\n"
              "  always @(posedge CLK or negedge SET_B)\n"
              "    if (!SET_B) Q <= 1'b1; else Q <= D;\nendmodule"),
    "dfxtp": ("module sky130_fd_sc_hd__dfxtp (CLK, D, Q);\n"
              "  input CLK, D; output reg Q; initial Q = 1'b0;\n"
              "  always @(posedge CLK) Q <= D;\nendmodule"),
}


def emit_module(base, vc):
    ins = vc["inputs"]
    outs = vc["outputs"]
    ports = ins + list(outs)
    lines = [f"module sky130_fd_sc_hd__{base} (" + ", ".join(ports) + ");"]
    for p in ins:
        lines.append(f"  input {p};")
    for p in outs:
        lines.append(f"  output {p};")
    for p, info in outs.items():
        v = info["expr"].replace("!", "~")       # &,| already Verilog; ! -> ~
        lines.append(f"  assign {p} = {v};")
    lines.append("endmodule")
    return "\n".join(lines)


def emit_virtual_cells(out_path):
    js = json.load(open("build/puzzle_netlist.json"))
    bases = sorted({i["cell"].split("__")[-1].rsplit("_", 1)[0]
                    for i in js["instances"]})
    chunks = ["// virtual cells derived from GDS polygons (no Liberty functions)",
              "`default_nettype none"]
    comb = seq = skip = 0
    for b in bases:
        if b in FLOP_SRC:
            chunks.append(FLOP_SRC[b])
            seq += 1
            continue
        gds = sorted(glob.glob(f"lib/sky130_fd_sc_hd/cells/{b}/*_*.gds"))
        if not gds:
            skip += 1
            continue
        d = extract_devices(gds[0])
        vc = derive(d["devices"], d["pin_nets"], d["power"], d["term_count"])
        if vc["kind"] == "combinational":
            chunks.append(emit_module(b, vc))
            comb += 1
        else:
            skip += 1                            # conb/decap/diode/tap: not instantiated as logic
    open(out_path, "w").write("\n\n".join(chunks) + "\n")
    print(f"wrote {out_path}: {comb} combinational virtual cells (from polygons) "
          f"+ {seq} flop templates, {skip} special skipped")


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--verify":
        verify_all()
        return
    if len(sys.argv) >= 3 and sys.argv[1] == "--emit":
        emit_virtual_cells(sys.argv[2])
        return
    if len(sys.argv) < 2:
        print(__doc__)
        return
    gds = sys.argv[1]
    base = gds.split("/")[-1].split("__")[-1].rsplit("_", 1)[0]
    _print_cell(base, gds)


if __name__ == "__main__":
    main()
