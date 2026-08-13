#!/usr/bin/env python3
"""Tests for the polygons -> logic toolchain (gds_to_logic.py).

These pin down the two claims that make it trustworthy: (1) the Boolean
function derived purely from a cell's layout matches the PDK Liberty for
every logic cell the puzzle uses, and (2) the switch-level / naming /
minimisation helpers behave on hand-built inputs. No PDK function strings
are used to *derive* anything here -- only to check.
Run: .venv/bin/python pipeline/test_gds_to_logic.py
"""
import glob
import itertools
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
os.chdir(os.path.join(HERE, ".."))            # lib/ paths are repo-relative

import gds_to_logic as G                       # noqa: E402


def _gds(base):
    return sorted(glob.glob(f"lib/sky130_fd_sc_hd/cells/{base}/*_*.gds"))[0]


def _derive(base):
    d = G.extract_devices(_gds(base))
    return G.derive(d["devices"], d["pin_nets"], d["power"], d["term_count"])


# -- unit tests on the pure helpers ----------------------------------------
def test_sop_minimises_constants():
    assert G.sop(["A"], [0, 0]) == "0"
    assert G.sop(["A", "B"], [1, 1, 1, 1]) == "1"


def test_sop_and_expr_roundtrips():
    # AND2 truth table -> a single product term
    tt = [0, 0, 0, 1]
    assert G.sop(["A", "B"], tt) == "(A&B)"


def test_name_op_basic_gates():
    assert G.name_op(["A"], [1, 0]) == "INV"
    assert G.name_op(["A"], [0, 1]) == "BUF"
    assert G.name_op(["A", "B"], [0, 0, 0, 1]) == "AND2"
    assert G.name_op(["A", "B"], [0, 1, 1, 0]) == "XOR2"
    assert G.name_op(["A", "B"], [1, 0, 0, 1]) == "XNOR2"


def test_eval_pattern_inverter():
    # hand-built 2-FET inverter: A gates both; pull-up to VPWR, pull-down to VGND
    devs = [dict(type="pmos", gate="A", sd=["VPWR", "Y"]),
            dict(type="nmos", gate="A", sd=["Y", "VGND"])]
    hi = G.eval_pattern(devs, {"VPWR": 1, "VGND": 0, "A": 1})
    lo = G.eval_pattern(devs, {"VPWR": 1, "VGND": 0, "A": 0})
    assert hi["Y"] == 0 and lo["Y"] == 1


def test_liberty_eval_matches_python():
    assert G.eval_liberty("(A&!B) | (!A&B)", {"A": 1, "B": 0}) == 1
    assert G.eval_liberty("(A&!B) | (!A&B)", {"A": 1, "B": 1}) == 0
    assert G.eval_liberty("1", {}) == 1


# -- end-to-end: derived operator names on real layouts --------------------
def test_named_operators_from_layout():
    expect = {"inv": "INV", "buf": "BUF", "and2": "AND2", "or2": "OR2",
              "nand2": "NAND2", "nor2": "NOR2", "xor2": "XOR2",
              "xnor2": "XNOR2", "and4": "AND4", "nand4": "NAND4"}
    for base, op in expect.items():
        vc = _derive(base)
        assert vc["kind"] == "combinational", f"{base}: {vc['kind']}"
        got = {i["op"] for i in vc["outputs"].values()}
        assert op in got, f"{base}: expected {op}, got {got}"


def test_mux2_recovered_as_mux():
    vc = _derive("mux2")
    assert vc["kind"] == "combinational"
    op = next(iter(vc["outputs"].values()))["op"]
    assert op == "MUX2(sel=S)", op


def test_flops_are_sequential():
    for base in ("dfxtp", "dfrtp", "dfstp"):
        assert _derive(base)["kind"] == "sequential", base


# -- the headline claim: every logic cell matches Liberty ------------------
def test_all_puzzle_logic_cells_match_liberty():
    import json
    js = json.load(open("build/puzzle_netlist.json"))
    bases = sorted({i["cell"].split("__")[-1].rsplit("_", 1)[0]
                    for i in js["instances"]})
    comb = mismatched = 0
    for b in bases:
        g = sorted(glob.glob(f"lib/sky130_fd_sc_hd/cells/{b}/*_*.gds"))
        if not g:
            continue
        rep, vc = G.check_cell(g[0], b)
        if vc["kind"] == "combinational":
            comb += 1
            if not rep["ok"]:
                mismatched += 1
    assert comb >= 55, f"only {comb} combinational cells tested"
    assert mismatched == 0, f"{mismatched} cells disagree with Liberty"


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
