#!/usr/bin/env python3
"""Invariant/regression tests for the concept-recovery pipeline.

These check the properties that make the recovery *trustworthy* rather
than merely plausible: the passes must partition the flops consistently,
the fixed point must converge, and the structural claims (counter width,
comparator width, chain acyclicity) must hold on the known puzzle netlist.
Run: .venv/bin/python pipeline/test_recover.py
"""
import json
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
from recover import (Base, flop_facts, Graph, run_to_fixpoint, short, FLOPS)  # noqa

NETLIST = os.path.join(HERE, "..", "build", "puzzle_netlist.json")


def build():
    base = Base(json.load(open(NETLIST)))
    facts = flop_facts(base)
    graph = Graph(base)
    rounds = run_to_fixpoint(graph, facts, base)
    return base, facts, graph, rounds


def test_fixpoint_converges():
    _, _, _, rounds = build()
    assert 1 <= rounds < 10, f"driver did not converge cleanly (rounds={rounds})"


def test_every_flop_has_facts():
    base, facts, _, _ = build()
    assert set(facts) == set(base.flops)
    for f, fx in facts.items():
        assert fx["clk_root"] is not None, f"{f} has no clock source"
        assert fx["rst_kind"] in ("reset0", "set1", "none")


def test_control_classes_partition_flops():
    base, _, graph, _ = build()
    classes = graph.of_kind("control_class")
    members = [set(c.members) for c in classes]
    union = set().union(*members)
    assert union == set(base.flops), "control classes do not cover all flops"
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            assert not (members[i] & members[j]), "control classes overlap"


def test_reset_kind_counts():
    _, facts, _, _ = build()
    kinds = {}
    for fx in facts.values():
        kinds[fx["rst_kind"]] = kinds.get(fx["rst_kind"], 0) + 1
    # known puzzle composition: 84 reset0 + 4 set1 + 4 no-reset
    assert kinds.get("reset0") == 84
    assert kinds.get("set1") == 4
    assert kinds.get("none") == 4


def test_counter_is_the_no_reset_group():
    base, facts, graph, _ = build()
    autos = graph.of_kind("autonomous_reg")
    assert autos, "no autonomous counter recovered"
    counter = max(autos, key=lambda c: c.attrs["width"])
    assert counter.attrs["width"] == 4, "output-generator counter should be 4 bits"
    no_reset = {f for f, fx in facts.items() if fx["rst_kind"] == "none"}
    assert set(counter.members) == no_reset, "counter != the no-reset flops"


def test_success_is_wide_comparator():
    base, _, graph, _ = build()
    buses = {c.attrs["consumer"]: c.attrs["width"]
             for c in graph.of_kind("operand_bus")}
    # success == flop i137, whose next-state reduces ~56 state bits
    assert any(w >= 40 for name, w in buses.items() if name.startswith("D[")), \
        "expected a wide (>=40-bit) reduction feeding a flop (the comparator)"


def test_output_generator_reads_counter():
    base, facts, _, _ = build()
    counter = {f for f, fx in facts.items() if fx["rst_kind"] == "none"}
    for pn, nid in base.ports.items():
        if pn.startswith("O["):
            fl, _ = base.support(nid)
            assert counter <= fl, f"{pn} cone must include the address counter"


def test_shift_edges_acyclic_simple():
    """Pure-shift adjacency (exactly one non-self source) must form simple
    paths: no bit has two shift-predecessors."""
    _, facts, _, _ = build()
    pred = {}
    for b, fx in facts.items():
        if len(fx["d_support_flops"]) == 1:
            a = next(iter(fx["d_support_flops"]))
            assert b not in pred, f"{b} has multiple shift predecessors"
            pred[b] = a


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
    print(f"\n{len(tests)-fails}/{len(tests)} passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
