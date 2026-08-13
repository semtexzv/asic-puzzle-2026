#!/usr/bin/env python3
"""Tests for the library-blind flat->gates recovery (flat_to_gates.py).

We compose a *flattened* strip of real sky130 cell layouts (rails stitched into
a continuous power grid, exactly like a real row), then recover the gate netlist
from the rectangles alone -- no hierarchy, no cell names, no pin labels, no
Liberty. Liberty is used ONLY to check the recovered functions (up to an input
permutation, since blind recovery has no pin names).
Run: .venv/bin/python pipeline/test_flat_to_gates.py
"""
import itertools
import os
import sys
from collections import Counter

import klayout.db as db

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
os.chdir(os.path.join(HERE, ".."))

import flat_to_gates as F                              # noqa: E402
from gds_to_logic import liberty, eval_liberty          # noqa: E402

STRIP = "build/_test_strip.gds"
CELLS = ["inv", "buf", "and2", "or2", "nand2", "nor2", "o21a", "a21o",
         "a221o", "o22a", "xor2", "xnor2", "mux2", "a2111oi"] * 2


def compose_strip(cells, out_gds):
    """Place each cell's layout in a row with a gap, stitch two full-width met1
    power rails across the strip, flatten to pure geometry, write GDS."""
    ly = db.Layout()
    ly.dbu = 0.001
    top = ly.create_cell("STRIP")
    dbn = lambda um: round(um / ly.dbu)                # noqa: E731
    x = 0
    for i, base in enumerate(cells):
        src = db.Layout()
        src.read(f"lib/sky130_fd_sc_hd/cells/{base}/sky130_fd_sc_hd__{base}_1.gds")
        sc = src.top_cells()[0]
        tgt = ly.create_cell(f"C{i}_{base}")
        tgt.copy_tree(sc)
        top.insert(db.CellInstArray(tgt.cell_index(), db.Trans(db.Vector(x, 0))))
        x += dbn(sc.dbbox().width()) + dbn(0.46)
    m1 = ly.layer(68, 20)
    for y0, y1 in ((-0.24, 0.24), (2.48, 2.96)):        # continuous VGND / VPWR
        top.shapes(m1).insert(db.Box(0, dbn(y0), x, dbn(y1)))
    ly.write(out_gds)
    return list(cells)


def _lib_truths(base):
    ins, outs = liberty(base)
    return [(len(ins), [eval_liberty(f, {ins[k]: b[k] for k in range(len(ins))})
                        for b in itertools.product((0, 1), repeat=len(ins))])
            for f in outs.values()]


def _match(cell, lib_by_base):
    """Does this recovered cell's function equal some library cell's, under some
    permutation of its (anonymous) inputs?"""
    n = len(cell["inputs"])
    for info in cell["outputs"].values():
        tt = info["truth"]
        for base, tabs in lib_by_base.items():
            for arity, ltt in tabs:
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


_RES = None


def _recover():
    global _RES
    if _RES is None:
        compose_strip(CELLS, STRIP)
        _RES = F.recover_cells(STRIP)
    return _RES


def test_rails_detected_and_distinct():
    res = _recover()
    assert res["vpwr"] is not None and res["vgnd"] is not None
    assert res["vpwr"] != res["vgnd"]


def test_segmentation_cell_count():
    res = _recover()
    # every placed cell is recovered as exactly one component
    assert len(res["cells"]) == len(CELLS), (len(res["cells"]), len(CELLS))
    assert all(c["kind"] == "combinational" for c in res["cells"])


def test_multistage_cells_split_into_more_regions():
    res = _recover()
    # xor2/mux2/buf/and2/... are multi-stage, so #primitive regions > #cells
    assert res["regions"] > len(res["cells"])


def test_every_recovered_function_matches_library():
    res = _recover()
    lib_by_base = {b: _lib_truths(b) for b in set(CELLS)}
    got = Counter()
    for c in res["cells"]:
        b = _match(c, lib_by_base)
        assert b is not None, f"unmatched recovered cell: {c['inputs']}"
        got[b] += 1
    assert got == Counter(CELLS), (dict(got), dict(Counter(CELLS)))


def test_transmission_gate_mux_recovered():
    # a strip of just mux2 (transmission-gate cell) must still yield the MUX fn
    compose_strip(["mux2"] * 4, "build/_test_mux.gds")
    res = F.recover_cells("build/_test_mux.gds")
    lib = {"mux2": _lib_truths("mux2")}
    assert len(res["cells"]) == 4
    assert all(_match(c, lib) == "mux2" for c in res["cells"])


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fails = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
