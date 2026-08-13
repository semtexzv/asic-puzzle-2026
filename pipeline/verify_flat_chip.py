#!/usr/bin/env python3
"""Scale test: recover the whole puzzle chip from FLAT rectangles (no hierarchy,
no cell names, no pin labels, no Liberty) and check every recovered combinational
cell's function against the sky130 library it was built from. Liberty is used
only to grade the blind result."""
import glob
import itertools
import json
import sys
import time
from collections import Counter

sys.path.insert(0, "pipeline")
import flat_to_gates as F
from gds_to_logic import liberty, eval_liberty


def lib_dictionary():
    js = json.load(open("build/puzzle_netlist.json"))
    bases = sorted({i["cell"].split("__")[-1].rsplit("_", 1)[0]
                    for i in js["instances"]})
    tabs = {}
    for b in bases:
        if not glob.glob(f"lib/sky130_fd_sc_hd/cells/{b}/*.lib.json"):
            continue
        lp = liberty(b)
        if not lp or not lp[1]:
            continue
        ins, outs = lp
        rows = []
        for f in outs.values():
            if f in ("0", "1") or not f:
                continue
            try:                                   # skip flop fns referencing internal pins (IQ, ...)
                rows.append((len(ins), [eval_liberty(f, {ins[k]: bt[k] for k in range(len(ins))})
                                        for bt in itertools.product((0, 1), repeat=len(ins))]))
            except NameError:
                pass
        if rows:
            tabs[b] = rows
    return tabs


def match(cell, tabs):
    n = len(cell["inputs"])
    if n > 6:
        return None
    for info in cell["outputs"].values():
        tt = info["truth"]
        for base, rows in tabs.items():
            for arity, ltt in rows:
                if arity != n:
                    continue
                for perm in itertools.permutations(range(n)):
                    permd = [0] * (1 << n)
                    for idx in range(1 << n):
                        bits = [(idx >> (n - 1 - k)) & 1 for k in range(n)]
                        j = 0
                        for k in range(n):
                            j = (j << 1) | bits[perm[k]]
                        permd[j] = tt[idx]
                    if permd == ltt:
                        return base
    return None


def main():
    t0 = time.time()
    print("recovering whole chip from flat rectangles...", flush=True)
    # On a fully-wired chip the netlist is ONE connected graph, so we don't
    # re-group primitives into 'cells' -- the product is the primitive gate
    # netlist. Derive each channel-connected region's function standalone.
    res = F.recover_netlist("puzzle.gds", flatten=True)
    rails = res["rails"]
    print(f"transistors: {res['n_trans']}  primitive channel-connected gates: "
          f"{len(res['gates'])}  ({time.time() - t0:.1f}s)", flush=True)

    tabs = lib_dictionary()
    kinds = Counter()
    ops = Counter()
    recognized = 0
    comb = 0
    for g in res["gates"]:
        fn = F.component_function([g], rails)
        if fn is None:
            kinds["pass/sequential"] += 1
            continue
        comb += 1
        for info in fn["outputs"].values():
            ops[info["op"] or "SOP"] += 1
        b = match(fn, tabs)
        if b:
            recognized += 1
    print(f"combinational primitive gates (function derived): {comb}")
    print(f"  recognized as a standard sky130 primitive (fn match): {recognized}/{comb}")
    print(f"  operator histogram: {dict(ops.most_common(14))}")
    print(f"pass/transmission or flop-loop regions: {kinds['pass/sequential']}")
    print(f"total time: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
