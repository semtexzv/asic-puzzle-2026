#!/usr/bin/env python3
"""Evaluate the output-generator ROM: given a machine state, compute the
16-char message O displays as the address counter cycles. Used to probe
which state bits select the message and to enumerate all messages the
generator can emit."""
import glob
import json
import re
import sys

LIB = "lib/sky130_fd_sc_hd"
OUTPUT_PINS = {"X", "Y", "Q", "Q_N", "HI", "LO"}
FLOPS = {"dfrtp", "dfstp", "dfxtp"}
COUNTER = ["i7", "i8", "i9", "i461"]   # the 4-bit address counter


def base_of(c):
    return c.split("__")[-1].rsplit("_", 1)[0]


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


def make_eval(expr):
    toks = re.findall(r"[A-Za-z0-9_]+|[()&|!]", expr)
    pos = [0]
    peek = lambda: toks[pos[0]] if pos[0] < len(toks) else None
    def nxt():
        t = toks[pos[0]]; pos[0] += 1; return t
    def atom(env):
        t = nxt()
        if t == "(":
            e = orx(env); nxt(); return e
        if t == "!":
            return not atom(env)
        if t == "1":
            return True
        if t == "0":
            return False
        return env[t]
    # need parse tree, not eager eval; build closure
    pos[0] = 0
    def p_atom():
        t = nxt()
        if t == "(":
            e = p_or(); nxt(); return e
        if t == "!":
            a = p_atom(); return ("not", a)
        if t in ("0", "1"):
            return ("const", t == "1")
        return ("var", t)
    def p_and():
        e = p_atom()
        while peek() == "&":
            nxt(); e = ("and", e, p_atom())
        return e
    def p_or():
        e = p_and()
        while peek() == "|":
            nxt(); e = ("or", e, p_and())
        return e
    tree = p_or()
    def ev(node, env):
        op = node[0]
        if op == "var":
            return env[node[1]]
        if op == "const":
            return node[1]
        if op == "not":
            return not ev(node[1], env)
        if op == "and":
            return ev(node[1], env) and ev(node[2], env)
        return ev(node[1], env) or ev(node[2], env)
    return lambda env: ev(tree, env)


class Out:
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
        self._treecache = {}

    def eval_net(self, net, state, cache):
        if net in cache:
            return cache[net]
        if net in self.qnet:
            cache[net] = state[self.qnet[net]]; return cache[net]
        if net in self.portnet:
            p = self.portnet[net]
            cache[net] = {"rst_n": True, "enable": False, "I": False}.get(p, False)
            return cache[net]
        drv = self.driver.get(net)
        if not drv:
            cache[net] = False; return cache[net]
        iname, opin = drv
        base = base_of(self.inst[iname]["cell"])
        if base == "conb":
            cache[net] = (opin == "HI"); return cache[net]
        outs = self.funcs.get(base, {})
        if opin not in outs:
            cache[net] = False; return cache[net]
        key = (base, opin)
        if key not in self._treecache:
            self._treecache[key] = make_eval(outs[opin])
        env = {}
        for p, n in self.inst[iname]["pins"].items():
            if p in ("VPWR", "VGND") or p in OUTPUT_PINS:
                continue
            env[p] = self.eval_net(n, state, cache)
        cache[net] = self._treecache[key](env); return cache[net]

    def message(self, state):
        """16-char message: for each counter value 0..15, set the counter
        flops and read O[7:0]."""
        chars = {}
        onets = [self.ports[f"O[{b}]"] for b in range(8)]
        for cv in range(16):
            st = dict(state)
            for bit, f in enumerate(COUNTER):
                st[f] = bool((cv >> bit) & 1)
            cache = {}
            val = 0
            for b in range(8):
                if self.eval_net(onets[b], st, cache):
                    val |= (1 << b)
            chars[cv] = val
        return chars   # counter value -> byte


def parse_state(hexstr, flops):
    v = int(hexstr, 16)
    # STATE = {dut.f0.Q, ...} : f0 is MSB
    n = len(flops)
    return {flops[i]: bool((v >> (n - 1 - i)) & 1) for i in range(n)}


if __name__ == "__main__":
    flops = json.load(open("build/flops.json"))
    o = Out()
    state = parse_state(sys.argv[1], flops)
    msg = o.message(state)
    # order by counter value; also render
    order = [msg[cv] for cv in range(16)]
    txt = "".join(chr(c) if 32 <= c < 127 else "." for c in order)
    print("message by counter value 0..15:", txt)
