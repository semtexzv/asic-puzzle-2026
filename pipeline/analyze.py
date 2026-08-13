#!/usr/bin/env python3
"""Structural analysis of the extracted puzzle netlist: state elements,
combinational cones, and how the serial input / success relate to state."""
import json
import sys
from collections import defaultdict, Counter, deque

OUTPUT_PINS = {"X", "Y", "Q", "Q_N", "HI", "LO", "COUT", "COUT_N", "SUM", "SUM_N"}
FLOPS = {"dfrtp", "dfstp", "dfxtp", "dfbbn", "dfbbp", "dfrbp", "dfsbp",
         "dfxbp", "edfxtp", "sdfxtp"}


def short(cell):
    return cell.split("__")[-1].rsplit("_", 1)[0]


def main(path):
    js = json.load(open(path))
    nets = js["nets"]
    inst = {i["name"]: i for i in js["instances"]}
    portnet = {v: k for k, v in js["ports"].items()}  # netid->portname (some)

    # driver[netid] = (inst, pin) that drives it; loads[netid] = [(inst,pin)]
    driver = {}
    loads = defaultdict(list)
    for i in js["instances"]:
        for pin, nid in i["pins"].items():
            if pin in ("VPWR", "VGND"):
                continue
            if pin in OUTPUT_PINS:
                driver[nid] = (i["name"], pin)
            else:
                loads[nid].append((i["name"], pin))

    ports = js["ports"]
    in_ports = {ports[p] for p in ("clk", "rst_n", "enable", "I") if p in ports}
    out_ports = {ports[p]: p for p in ports if p.startswith("O[") or p == "success"}

    # inventory
    kinds = Counter(short(i["cell"]) for i in js["instances"])
    flops = [i for i in js["instances"] if short(i["cell"]) in FLOPS]
    comb = [i for i in js["instances"] if short(i["cell"]) not in FLOPS
            and short(i["cell"]) not in ("decap", "tapvpwrvgnd", "diode", "conb", "fill")]
    print(f"state elements (flip-flops): {len(flops)}")
    print("  " + ", ".join(f"{k}:{v}" for k, v in Counter(short(f['cell']) for f in flops).items()))
    print(f"combinational gates: {len(comb)}")
    print(f"constants (conb): {kinds.get('conb',0)}   fillers/taps/decap dropped")

    # backward support: for a start net, which flop-Q nets and input ports
    # its combinational cone depends on
    qnet = {}   # netid -> flop instance (this net is that flop's Q output)
    for f in flops:
        for pin, nid in f["pins"].items():
            if pin == "Q":
                qnet[nid] = f["name"]

    def support(start_net):
        seen = set()
        stack = [start_net]
        deps_flops = set()
        deps_inputs = set()
        while stack:
            nid = stack.pop()
            if nid in seen:
                continue
            seen.add(nid)
            if nid in qnet:
                deps_flops.add(qnet[nid]); continue
            if nid in in_ports:
                deps_inputs.add(portnet.get(nid, nid)); continue
            drv = driver.get(nid)
            if not drv:
                continue
            di = inst[drv[0]]
            if short(di["cell"]) in FLOPS:
                # reached a flop output that isn't Q (Q_N) -> treat as state
                deps_flops.add(drv[0]); continue
            for pin, n2 in di["pins"].items():
                if pin not in OUTPUT_PINS and pin not in ("VPWR", "VGND"):
                    stack.append(n2)
        return deps_flops, deps_inputs

    # classify each flop's D cone: shift-reg (1 flop, no input) vs feedback
    chain = 0
    feedback = 0
    input_fed = []
    fanin_hist = Counter()
    dep_edges = defaultdict(set)   # flop -> set of source flops feeding its D
    for f in flops:
        dnet = f["pins"].get("D")
        if dnet is None:
            continue
        dfl, dins = support(dnet)
        dep_edges[f["name"]] = dfl
        fanin_hist[len(dfl)] += 1
        if len(dfl) == 1 and not dins:
            chain += 1
        else:
            feedback += 1
        if dins:
            input_fed.append((f["name"], sorted(dins)))

    print(f"\nflop D-cone fan-in (how many state bits feed each flop's next-state):")
    for k in sorted(fanin_hist):
        print(f"  depends on {k} flop(s): {fanin_hist[k]} flops")
    print(f"pure shift (1 src, no input): {chain}   feedback/logic: {feedback}")
    print(f"flops whose next-state sees a primary input: {len(input_fed)}")
    for name, ins in input_fed[:12]:
        print(f"   {name} <- inputs {ins}")

    # success cone
    for nid, pname in out_ports.items():
        if pname == "success":
            sf, si = support(nid)
            print(f"\nsuccess depends on {len(sf)} state bits, inputs {sorted(si)}")

    # output generator: union of O[] cones
    ocone = set()
    for nid, pname in out_ports.items():
        if pname.startswith("O["):
            sf, _ = support(nid)
            ocone |= sf
    print(f"output bus O[7:0] combinational cone touches {len(ocone)} state bits")

    # longest shift chain via dep_edges (flop->flop where fanin==1)
    succ = {f: next(iter(s)) for f, s in dep_edges.items() if len(s) == 1}
    # find chains
    indeg = Counter()
    for a, b in succ.items():
        indeg[b] += 1
    starts = [f for f in succ if indeg[f] == 0]
    longest = 0
    for s in starts:
        L = 0; cur = s; seen = set()
        while cur in succ and cur not in seen:
            seen.add(cur); cur = succ[cur]; L += 1
        longest = max(longest, L)
    print(f"\nlongest simple shift-chain among flops: {longest}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/puzzle_netlist.json")
