#!/usr/bin/env python3
"""Bottom-up concept recovery from a flat gate netlist.

A compiler-style pipeline: the netlist is a graph of leaf nodes (gates,
flops, constants); passes are pure candidate-generators that recognize a
pattern and emit higher-level CONCEPTS (register bit -> register -> shift
reg / LFSR / operand bus -> ...). A worklist driver runs passes until a
fixed point (no pass adds/changes anything).

Design notes
------------
* Passes are *candidate* generators: they attach evidence + confidence,
  they do not destructively commit. Overlapping proposals are allowed and
  reconciled later; this keeps the process stable (a wrong guess is a
  low-confidence candidate, not a corrupted graph).
* Per-seed work in every pass (per flop, per chain, per sink) is an
  independent pure function of the immutable base graph, so a pass is
  embarrassingly parallel (map over seeds). The driver only sequences
  passes; it never shares mutable state inside a pass. We run serial here
  (728 gates is instant) but the structure is map-parallel by construction.
* Everything a pass asserts is structural/exact (control equivalence,
  fan-in support, graph connectivity) -- no fuzzy matching yet. Functional
  operator identification (adder/LFSR/compare) is a later, verifiable pass.
"""
import json
import sys
from collections import defaultdict, Counter
from dataclasses import dataclass, field

OUTPUT_PINS = {"X", "Y", "Q", "Q_N", "HI", "LO", "COUT", "COUT_N", "SUM", "SUM_N"}
FLOPS = {"dfrtp", "dfstp", "dfxtp", "dfbbn", "dfbbp", "dfrbp", "dfsbp", "dfxbp"}
BUF1 = {"buf", "clkbuf", "dlygate4sd1", "dlygate4sd2", "dlygate4sd3"}
INV1 = {"inv", "clkinv", "clkinvlp"}
RST_KIND = {"dfrtp": "reset0", "dfstp": "set1", "dfxtp": "none"}


def short(cell):
    return cell.split("__")[-1].rsplit("_", 1)[0]


# --------------------------------------------------------------------------
# base graph: immutable view of the netlist with driver/load maps
# --------------------------------------------------------------------------
class Base:
    def __init__(self, js):
        self.js = js
        self.inst = {i["name"]: i for i in js["instances"]}
        self.ports = js["ports"]
        self.portnet = {v: k for k, v in js["ports"].items()}
        self.in_ports = {js["ports"][p] for p in ("clk", "rst_n", "enable", "I")
                         if p in js["ports"]}
        self.driver = {}     # netid -> (inst, pin)
        self.loads = defaultdict(list)
        for i in js["instances"]:
            for pin, nid in i["pins"].items():
                if pin in ("VPWR", "VGND"):
                    continue
                (self.driver.__setitem__(nid, (i["name"], pin)) if pin in OUTPUT_PINS
                 else self.loads[nid].append((i["name"], pin)))
        self.flops = [n for n, i in self.inst.items() if short(i["cell"]) in FLOPS]
        self.qnet = {}       # netid -> flop name (that flop's Q)
        for f in self.flops:
            for pin, nid in self.inst[f]["pins"].items():
                if pin == "Q":
                    self.qnet[nid] = f

    def in_pins(self, name):
        i = self.inst[name]
        return {p: n for p, n in i["pins"].items()
                if p not in OUTPUT_PINS and p not in ("VPWR", "VGND")}

    def trace_source(self, net):
        """Follow single-input buffer/inverter chain back to a primary port
        or the first real gate. Returns (kind, id, parity)."""
        parity = 0
        seen = set()
        while net not in seen:
            seen.add(net)
            if net in self.in_ports:
                return ("port", self.portnet[net], parity)
            drv = self.driver.get(net)
            if not drv:
                return ("net", net, parity)
            base = short(self.inst[drv[0]]["cell"])
            if base in INV1 or base in BUF1:
                a = self.inst[drv[0]]["pins"].get("A")
                if a is None:
                    return ("gate", drv[0], parity)
                if base in INV1:
                    parity ^= 1
                net = a
                continue
            return ("gate", drv[0], parity)
        return ("net", net, parity)

    def support(self, start_net):
        """Combinational cone of a net, back to flop-Q nets and input ports.
        Returns (set of source flops incl. self if fed back, set of inputs)."""
        seen, stack, fl, ins = set(), [start_net], set(), set()
        while stack:
            nid = stack.pop()
            if nid in seen:
                continue
            seen.add(nid)
            if nid in self.qnet:
                fl.add(self.qnet[nid]); continue
            if nid in self.in_ports:
                ins.add(self.portnet.get(nid, nid)); continue
            drv = self.driver.get(nid)
            if not drv:
                continue
            di = self.inst[drv[0]]
            if short(di["cell"]) in FLOPS:
                fl.add(drv[0]); continue
            for pin, n2 in self.in_pins(drv[0]).items():
                stack.append(n2)
        return fl, ins


# --------------------------------------------------------------------------
# concept graph
# --------------------------------------------------------------------------
@dataclass
class Concept:
    kind: str
    members: tuple            # instance names (ordered where meaningful)
    attrs: dict = field(default_factory=dict)
    evidence: str = ""
    confidence: float = 1.0


class Graph:
    def __init__(self, base):
        self.base = base
        self.concepts = []
        self._keys = set()     # dedup identical proposals

    def add(self, c):
        key = (c.kind, c.members)
        if key in self._keys:
            return False
        self._keys.add(key)
        self.concepts.append(c)
        return True

    def of_kind(self, kind):
        return [c for c in self.concepts if c.kind == kind]


# --------------------------------------------------------------------------
# per-flop register-bit facts (Pass 0 substrate) -- pure per flop
# --------------------------------------------------------------------------
def flop_facts(base):
    facts = {}
    for f in base.flops:
        i = base.inst[f]
        cell = short(i["cell"])
        pins = base.in_pins(f)
        clk = base.trace_source(pins["CLK"]) if "CLK" in pins else None
        rstpin = pins.get("RESET_B") or pins.get("SET_B")
        rst = base.trace_source(rstpin) if rstpin else None
        dnet = pins.get("D")
        fl, ins = base.support(dnet) if dnet else (set(), set())
        nonself = fl - {f}
        facts[f] = {
            "cell": cell,
            "rst_kind": RST_KIND.get(cell, "none"),
            "clk_root": clk,
            "rst_root": rst,
            "d_support_flops": nonself,
            "d_support_self": f in fl,
            "d_inputs": ins,
            "qnet": next((n for p, n in i["pins"].items() if p == "Q"), None),
            "dnet": dnet,
        }
    return facts


# --------------------------------------------------------------------------
# PASSES  (each: graph, facts -> bool changed)
# --------------------------------------------------------------------------
def pass_regbits(graph, facts):
    """Canonicalize each flop as a register-bit concept with its control."""
    changed = False
    for f, fx in facts.items():
        changed |= graph.add(Concept(
            "regbit", (f,),
            attrs={"rst": fx["rst_kind"], "clk": fx["clk_root"],
                   "reset_src": fx["rst_root"], "enable_gated": fx["d_support_self"],
                   "next_srcs": tuple(sorted(fx["d_support_flops"])),
                   "inputs": tuple(sorted(fx["d_inputs"]))},
            evidence=f"{fx['cell']} clk={_p(fx['clk_root'])} rst={_p(fx['rst_root'])}"))
    return changed


def pass_shift_chains(graph, facts):
    """Pure shift stages: a bit whose next-state is exactly one OTHER bit
    (plus optional self-hold). Chain them into ordered shift registers, and
    record where a primary input is serially injected."""
    # shift edge a -> b : b's next state (minus self) is exactly {a}
    succ, pred = {}, {}
    for b, fx in facts.items():
        srcs = fx["d_support_flops"]
        if len(srcs) == 1:
            a = next(iter(srcs))
            succ[a] = b
            pred[b] = a
    heads = [n for n in succ if n not in pred]   # chain starts
    changed = False
    used = set()
    for h in heads:
        chain, cur, seen = [], h, set()
        while cur is not None and cur not in seen:
            seen.add(cur); chain.append(cur); cur = succ.get(cur)
        if len(chain) >= 2:
            used.update(chain)
            head_inputs = facts[chain[0]]["d_inputs"]
            changed |= graph.add(Concept(
                "shift_register", tuple(chain),
                attrs={"width": len(chain), "serial_in": tuple(sorted(head_inputs)),
                       "rst": facts[chain[0]]["rst_kind"]},
                evidence=f"pure shift chain len {len(chain)}, "
                         f"serial-in={sorted(head_inputs) or 'none'}"))
    return changed


def pass_feedback_groups(graph, facts):
    """Strongly-connected components of the flop next-state graph: mutual
    feedback = LFSR / counter / accumulator candidates."""
    nodes = list(facts)
    adj = {a: set() for a in nodes}
    for b, fx in facts.items():
        for a in fx["d_support_flops"]:
            adj[a].add(b)                  # a feeds b's next-state
    comps = _tarjan_scc(nodes, adj)
    changed = False
    for comp in comps:
        if len(comp) < 2:
            continue
        # count internal tap density: edges within the component
        internal = sum(1 for a in comp for b in adj[a] if b in comp)
        avg_taps = internal / len(comp)
        kind = "shift_or_lfsr" if avg_taps < 1.5 else "feedback_datapath"
        inputs = set().union(*(facts[n]["d_inputs"] for n in comp))
        changed |= graph.add(Concept(
            "feedback_group", tuple(sorted(comp)),
            attrs={"width": len(comp), "avg_taps": round(avg_taps, 2),
                   "guess": kind, "inputs": tuple(sorted(inputs))},
            evidence=f"SCC size {len(comp)}, avg {avg_taps:.1f} feedback taps/bit, "
                     f"inputs={sorted(inputs) or 'none'}"))
    return changed


def pass_operand_bus(graph, facts, base, min_width=4):
    """A combinational sink (a flop's D, or a primary output) whose cone
    reads many state bits with no/low input dependence = the operand bus of
    a word-level operator (comparator, adder, reducer)."""
    changed = False
    sinks = []
    for f, fx in facts.items():
        sinks.append((f"D[{f}]", fx["d_support_flops"], fx["d_inputs"]))
    for pname, nid in base.ports.items():
        if pname.startswith("O[") or pname == "success":
            fl, ins = base.support(nid)
            sinks.append((pname, fl, ins))
    for name, fl, ins in sinks:
        if len(fl) >= min_width and len(ins) <= 1:
            changed |= graph.add(Concept(
                "operand_bus", tuple(sorted(fl)),
                attrs={"width": len(fl), "consumer": name,
                       "inputs": tuple(sorted(ins))},
                evidence=f"{len(fl)} state bits reduced into '{name}'"))
    return changed


def pass_autonomous(graph, facts, closure=0.6):
    """Maximal groups of flops with NO primary-input dependence whose
    next-state stays mostly inside the group = free-running state machines
    (counters, the message-ROM address generator)."""
    auto = {f for f, fx in facts.items() if not fx["d_inputs"]}
    # directed recurrence among input-free flops; SCC = a mutually-updating
    # register that runs on its own = counter / sequence generator
    adj = {a: set() for a in auto}
    for b in auto:
        for a in facts[b]["d_support_flops"]:
            if a in auto:
                adj[a].add(b)                  # a feeds b's next state
    changed = False
    for comp in _tarjan_scc(list(auto), adj):
        if len(comp) < 2:
            continue
        comp = set(comp)
        # external flops that gate/seed it (feed in but aren't in the SCC)
        ext = set()
        for b in comp:
            ext |= (facts[b]["d_support_flops"] - comp)
        changed |= graph.add(Concept(
            "autonomous_reg", tuple(sorted(comp)),
            attrs={"width": len(comp), "gated_by": tuple(sorted(ext)),
                   "guess": "counter/sequence generator"},
            evidence=f"width {len(comp)} self-clocking counter/generator"
                     + (f", gated by {sorted(ext)}" if ext else "")))
    return changed


def pass_input_mixers(graph, facts):
    """Weakly-connected blocks among flops whose next-state consumes a
    primary input = the registers that actually absorb/scramble the serial
    input (LFSR-like mixers). WCC (not SCC) so feed-forward paths stay whole."""
    mix = {f for f, fx in facts.items() if fx["d_inputs"] & {"I", "enable"}}
    adj = defaultdict(set)
    for b in mix:
        for a in facts[b]["d_support_flops"]:
            if a in mix:
                adj[a].add(b); adj[b].add(a)
    changed = False
    for comp in _wcc(mix, adj):
        if len(comp) < 2:
            continue
        takes_I = any("I" in facts[n]["d_inputs"] for n in comp)
        # how many flops in the block have their OWN next-state read serial I
        i_bits = sum("I" in facts[n]["d_inputs"] for n in comp)
        note = ("one coupled state block (not separable into independent "
                f"registers); {i_bits} bits directly sample serial I"
                if len(comp) > 16 else
                ("reads serial I" if takes_I else "enable-only"))
        changed |= graph.add(Concept(
            "input_mixer", tuple(sorted(comp)),
            attrs={"width": len(comp), "consumes_serial_I": takes_I,
                   "i_sampling_bits": i_bits},
            evidence=f"width {len(comp)} block, {note}"))
    return changed


def pass_control_classes(graph, facts):
    """Coarse partition: flops sharing (reset kind, clk root, reset root).
    Catches the set-to-1 seed bits and the no-reset generator counter."""
    buckets = defaultdict(list)
    for f, fx in facts.items():
        buckets[(fx["rst_kind"], _p(fx["clk_root"]), _p(fx["rst_root"]))].append(f)
    changed = False
    for (rst, clk, rsrc), members in buckets.items():
        role = {"set1": "seed/one-init register (e.g. LFSR seed)",
                "none": "no-reset register (free-running counter?)",
                "reset0": "zero-init state"}[rst]
        changed |= graph.add(Concept(
            "control_class", tuple(sorted(members)),
            attrs={"rst": rst, "clk": clk, "reset_src": rsrc, "width": len(members)},
            evidence=f"{len(members)} flops, reset={rst} -> {role}"))
    return changed


# --------------------------------------------------------------------------
# driver: run passes to fixed point
# --------------------------------------------------------------------------
def run_to_fixpoint(graph, facts, base, max_rounds=10):
    passes = [
        ("regbits", lambda: pass_regbits(graph, facts)),
        ("shift_chains", lambda: pass_shift_chains(graph, facts)),
        ("feedback_groups", lambda: pass_feedback_groups(graph, facts)),
        ("autonomous", lambda: pass_autonomous(graph, facts)),
        ("input_mixers", lambda: pass_input_mixers(graph, facts)),
        ("operand_bus", lambda: pass_operand_bus(graph, facts, base)),
        ("control_classes", lambda: pass_control_classes(graph, facts)),
    ]
    rounds = 0
    while rounds < max_rounds:
        rounds += 1
        changed = any(fn() for _, fn in passes)
        if not changed:
            break
    return rounds


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _p(root):
    if not root:
        return "?"
    if root[0] == "port":
        return root[1] + ("~" if root[2] else "")
    return f"{root[0]}:{root[1]}"


def _wcc(nodes, adj):
    """Weakly-connected components over an undirected adjacency."""
    seen, comps = set(), []
    for s in nodes:
        if s in seen:
            continue
        comp, stack = [], [s]
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v); comp.append(v)
            stack.extend(adj[v])
        comps.append(comp)
    return comps


def _tarjan_scc(nodes, adj):
    idx = {}; low = {}; onstk = {}; stk = []; out = []; c = [0]
    import sys as _s
    _s.setrecursionlimit(10000)

    def dfs(v):
        idx[v] = low[v] = c[0]; c[0] += 1
        stk.append(v); onstk[v] = True
        for w in adj[v]:
            if w not in idx:
                dfs(w); low[v] = min(low[v], low[w])
            elif onstk.get(w):
                low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = stk.pop(); onstk[w] = False; comp.append(w)
                if w == v:
                    break
            out.append(comp)
    for v in nodes:
        if v not in idx:
            dfs(v)
    return out


def report(graph, base):
    print(f"=== concept recovery: {len(base.flops)} flops, "
          f"{len(graph.concepts)} candidate concepts ===\n")

    def dump(kind, title, min_w=1, rollup=False):
        cs = [c for c in graph.of_kind(kind) if c.attrs.get("width", 0) >= min_w]
        big = [c for c in cs if c.attrs.get("width", 0) >= (4 if rollup else 1)]
        small = [c for c in cs if c.attrs.get("width", 0) < 4]
        if not cs:
            return
        print(f"-- {title} ({len(cs)}):")
        for c in sorted(big, key=lambda x: -x.attrs.get("width", 0)):
            print(f"   w={c.attrs.get('width','?'):>3}  {c.evidence}")
        if rollup and small:
            print(f"   (+ {len(small)} small tightly-coupled clusters, "
                  f"width 2-3)")
        print()

    dump("control_class", "control classes (reset/clock partition)")
    dump("autonomous_reg", "autonomous registers (free-running: counters/generators)")
    dump("input_mixer", "input-mixing registers (absorb serial I)")
    dump("feedback_group", "raw feedback SCCs", rollup=True)
    dump("shift_register", "pure shift registers")
    dump("operand_bus", "operand buses (word-level reductions)", min_w=4)

    grouped = set()
    for k in ("autonomous_reg", "input_mixer", "shift_register"):
        for c in graph.of_kind(k):
            grouped.update(c.members)
    print(f"flops explained by a register concept: {len(grouped)}/{len(base.flops)}")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "build/puzzle_netlist.json"
    base = Base(json.load(open(path)))
    facts = flop_facts(base)
    graph = Graph(base)
    rounds = run_to_fixpoint(graph, facts, base)
    print(f"fixed point in {rounds} round(s)\n")
    report(graph, base)


if __name__ == "__main__":
    main()
