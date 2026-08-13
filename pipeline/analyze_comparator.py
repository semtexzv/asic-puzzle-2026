#!/usr/bin/env python3
"""Analyze the success comparator: build i137's D-cone as a z3 formula over
the state flops, then (a) count satisfying states (1 => pure equality
comparator with a unique target), and (b) read out the target constant."""
import glob
import json
import re
import sys

import z3

LIB = "lib/sky130_fd_sc_hd"
OUTPUT_PINS = {"X", "Y", "Q", "Q_N", "HI", "LO"}
FLOPS = {"dfrtp", "dfstp", "dfxtp"}


def short(c):
    return c.split("__")[-1]


def base_of(c):
    return short(c).rsplit("_", 1)[0]


def load_funcs():
    funcs = {}
    for lj in glob.glob(f"{LIB}/cells/*/*__*.lib.json"):
        d = json.load(open(lj))
        base = None
        outs = {}
        for k, v in d.items():
            if not k.startswith("pin,") or not isinstance(v, dict):
                continue
            if v.get("direction") == "output" and "function" in v:
                outs[k[4:]] = v["function"]
        # cell name from any pin's parent? use file name
        cell = re.search(r"(sky130_fd_sc_hd__[a-z0-9]+?)_\d+__", lj)
        if cell and outs:
            funcs.setdefault(cell.group(1).split("__")[-1], outs)
    return funcs


def parse_expr(s, pinvars):
    """Liberty boolean expr -> z3. Grammar: names, ! & | ( )."""
    toks = re.findall(r"[A-Za-z0-9_]+|[()&|!]", s)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def nxt():
        t = toks[pos[0]]; pos[0] += 1; return t

    def atom():
        t = nxt()
        if t == "(":
            e = orexpr(); nxt()  # )
            return e
        if t == "!":
            return z3.Not(atom())
        if t == "1":
            return z3.BoolVal(True)
        if t == "0":
            return z3.BoolVal(False)
        return pinvars[t]

    def notexpr():
        e = atom()
        while peek() == "!":   # postfix (rare)
            nxt(); e = z3.Not(e)
        return e

    def andexpr():
        e = notexpr()
        while peek() == "&":
            nxt(); e = z3.And(e, notexpr())
        return e

    def orexpr():
        e = andexpr()
        while peek() == "|":
            nxt(); e = z3.Or(e, andexpr())
        return e

    return orexpr()


def main():
    js = json.load(open("build/puzzle_netlist_fixed.json"))
    inst = {i["name"]: i for i in js["instances"]}
    ports = js["ports"]; portnet = {v: k for k, v in ports.items()}
    in_ports = {ports[p] for p in ("clk", "rst_n", "enable", "I") if p in ports}
    driver = {}
    for i in js["instances"]:
        for p, n in i["pins"].items():
            if p in OUTPUT_PINS:
                driver[n] = (i["name"], p)
    qnet = {}
    for i in js["instances"]:
        if base_of(i["cell"]) in FLOPS:
            for p, n in i["pins"].items():
                if p == "Q":
                    qnet[n] = i["name"]
    funcs = load_funcs()

    leaves = {}   # net -> z3 var (flop Q or primary input)
    memo = {}

    def build(net):
        if net in memo:
            return memo[net]
        if net in qnet:
            v = leaves.setdefault(net, z3.Bool(f"q_{qnet[net]}"))
            memo[net] = v; return v
        if net in in_ports:
            v = leaves.setdefault(net, z3.Bool(f"in_{portnet[net]}"))
            memo[net] = v; return v
        drv = driver.get(net)
        if not drv:
            v = z3.Bool(f"und_{net}"); memo[net] = v; return v
        iname, opin = drv
        cell = inst[iname]; base = base_of(cell["cell"])
        if base == "conb":
            memo[net] = z3.BoolVal(opin == "HI"); return memo[net]
        outs = funcs.get(base)
        if not outs or opin not in outs:
            v = z3.Bool(f"unk_{net}"); memo[net] = v; return v
        pinvars = {}
        for p, n in cell["pins"].items():
            if p in ("VPWR", "VGND"):
                continue
            if p not in OUTPUT_PINS:
                pinvars[p] = build(n)
        e = parse_expr(outs[opin], pinvars)
        memo[net] = e; return e

    dnet = inst["i137"]["pins"]["D"]
    formula = build(dnet)
    statevars = [leaves[n] for n in leaves if n in qnet]
    print(f"comparator cone: {len(statevars)} state leaves, "
          f"{sum(1 for n in leaves if n in in_ports)} input leaves")

    s = z3.Solver()
    s.add(formula == True)
    r = s.check()
    print("success satisfiable?", r)
    if r != z3.sat:
        return
    m = s.model()
    # is the target unique? block this model, re-check
    target = {}
    for n, v in leaves.items():
        if n in qnet:
            target[qnet[n]] = 1 if m.eval(v, model_completion=True) else 0
    s.add(z3.Or([leaves[n] != m.eval(leaves[n], model_completion=True)
                 for n in leaves if n in qnet]))
    r2 = s.check()
    print("second distinct target state?", r2, "=> comparator is",
          "PURE EQUALITY (unique target)" if r2 == z3.unsat else "not a simple equality")
    print(f"target state ({sum(target.values())} ones of {len(target)}):")
    ones = sorted(k for k, v in target.items() if v)
    print("  flops that must be 1:", ones)
    json.dump(target, open("build/cmp_target.json", "w"))


if __name__ == "__main__":
    main()
