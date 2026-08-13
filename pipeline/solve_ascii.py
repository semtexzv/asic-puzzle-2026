#!/usr/bin/env python3
"""Search for a PRINTABLE-ASCII serial input that raises success.

Builds the exact per-cycle transition (enable=1, rst_n=1) as z3 formulas
from the Liberty gate functions, unrolls it, constrains the input bits to
form printable ASCII bytes, and requires success (i137.Q) at the target
cycle. A satisfying model is the intended input string.
"""
import glob
import json
import re
import sys

import z3

LIB = "lib/sky130_fd_sc_hd"
OUTPUT_PINS = {"X", "Y", "Q", "Q_N", "HI", "LO"}
FLOPS = {"dfrtp", "dfstp", "dfxtp"}
SET1 = "dfstp"   # init 1


def short(c):
    return c.split("__")[-1]


def base_of(c):
    return short(c).rsplit("_", 1)[0]


def load_funcs():
    funcs = {}
    for lj in glob.glob(f"{LIB}/cells/*/*__*.lib.json"):
        d = json.load(open(lj))
        outs = {k[4:]: v["function"] for k, v in d.items()
                if k.startswith("pin,") and isinstance(v, dict)
                and v.get("direction") == "output" and "function" in v}
        m = re.search(r"(sky130_fd_sc_hd__[a-z0-9]+?)_\d+__", lj)
        if m and outs:
            funcs.setdefault(m.group(1).split("__")[-1], outs)
    return funcs


def parse_expr(s, pinvars):
    toks = re.findall(r"[A-Za-z0-9_]+|[()&|!]", s)
    pos = [0]
    peek = lambda: toks[pos[0]] if pos[0] < len(toks) else None

    def nxt():
        t = toks[pos[0]]; pos[0] += 1; return t

    def atom():
        t = nxt()
        if t == "(":
            e = orx(); nxt(); return e
        if t == "!":
            return z3.Not(atom())
        if t == "1":
            return z3.BoolVal(True)
        if t == "0":
            return z3.BoolVal(False)
        return pinvars[t]

    def andx():
        e = atom()
        while peek() == "&":
            nxt(); e = z3.And(e, atom())
        return e

    def orx():
        e = andx()
        while peek() == "|":
            nxt(); e = z3.Or(e, andx())
        return e
    return orx()


class Machine:
    def __init__(self):
        js = json.load(open("build/puzzle_netlist_fixed.json"))
        self.inst = {i["name"]: i for i in js["instances"]}
        self.ports = js["ports"]
        self.portnet = {v: k for k, v in js["ports"].items()}
        self.driver = {}
        for i in js["instances"]:
            for p, n in i["pins"].items():
                if p in OUTPUT_PINS:
                    self.driver[n] = (i["name"], p)
        self.qnet = {}
        self.flops = []
        for i in js["instances"]:
            if base_of(i["cell"]) in FLOPS:
                self.flops.append(i["name"])
                for p, n in i["pins"].items():
                    if p == "Q":
                        self.qnet[n] = i["name"]
        self.funcs = load_funcs()
        # template state vars (current-cycle Q of each flop) + serial input
        self.qv = {f: z3.Bool(f"Q_{f}") for f in self.flops}
        self.iv = z3.Bool("Iin")
        self.const = {  # enable=1, rst_n=1 folded in
            self.ports["enable"]: z3.BoolVal(True),
            self.ports["rst_n"]: z3.BoolVal(True),
            self.ports["I"]: self.iv,
        }
        self.dexpr = {f: self._build(self.inst[f]["pins"]["D"], {})
                      for f in self.flops}

    def _build(self, net, memo):
        if net in memo:
            return memo[net]
        if net in self.qnet:
            memo[net] = self.qv[self.qnet[net]]; return memo[net]
        if net in self.const:
            memo[net] = self.const[net]; return memo[net]
        drv = self.driver.get(net)
        if not drv:
            memo[net] = z3.BoolVal(False); return memo[net]   # undriven -> 0
        iname, opin = drv
        base = base_of(self.inst[iname]["cell"])
        if base == "conb":
            memo[net] = z3.BoolVal(opin == "HI"); return memo[net]
        outs = self.funcs.get(base, {})
        if opin not in outs:
            memo[net] = z3.BoolVal(False); return memo[net]
        pinvars = {p: self._build(n, memo)
                   for p, n in self.inst[iname]["pins"].items()
                   if p not in OUTPUT_PINS and p not in ("VPWR", "VGND")}
        memo[net] = parse_expr(outs[opin], pinvars); return memo[net]

    def init_state(self):
        return {f: z3.BoolVal(base_of(self.inst[f]["cell"]) == SET1)
                for f in self.flops}


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 122
    nbytes = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    msb_first = (sys.argv[3] != "lsb") if len(sys.argv) > 3 else True

    m = Machine()
    s = z3.Solver()
    S = m.init_state()
    Ibits = [z3.Bool(f"I_{t}") for t in range(N)]
    succ_at = []
    for t in range(N):
        nxt = {f: z3.Bool(f"S{t+1}_{f}") for f in m.flops}
        sub = [(m.qv[g], S[g]) for g in m.flops] + [(m.iv, Ibits[t])]
        for f in m.flops:
            s.add(nxt[f] == z3.substitute(m.dexpr[f], *sub))
        S = nxt
        succ_at.append(S["i137"])

    nbits = nbytes * 8
    # input is EXACTLY the ASCII string, then zero padding
    for t in range(nbits, N):
        s.add(Ibits[t] == False)
    for b in range(nbytes):
        byte = z3.Sum([z3.If(Ibits[8 * b + j], 1, 0) *
                       (1 << ((7 - j) if msb_first else j)) for j in range(8)])
        s.add(byte >= 0x20, byte <= 0x7e)
    # success may fire any cycle from just after the last byte to N
    s.add(z3.Or([succ_at[t] for t in range(nbits, N)]))

    print(f"solving: {nbytes} ASCII bytes ({'MSB' if msb_first else 'LSB'}-first)"
          f" + zero pad, success in [{nbits}..{N}] ...")
    r = s.check()
    print("result:", r)
    if r != z3.sat:
        return
    mod = s.model()
    bits = [1 if mod.eval(Ibits[t], model_completion=True) else 0 for t in range(N)]
    chars = []
    for b in range(nbytes):
        v = 0
        for j in range(8):
            bit = bits[8 * b + j]
            v |= bit << ((7 - j) if msb_first else j)
        chars.append(v)
    s_txt = "".join(chr(c) for c in chars)
    print("input bits:", "".join(map(str, bits)))
    print(f"ASCII string ({nbytes} chars): {s_txt!r}")
    json.dump(bits, open("build/ascii_input.json", "w"))


if __name__ == "__main__":
    main()
