#!/usr/bin/env python3
"""Recover a gate-level netlist from a FLAT layout with no cell library and no
cell/pin annotations -- only the graphical rectangles + the technology layer map.

    flat polygons
      -> transistors            KLayout device extraction (poly&diff = channel,
                                 diff-poly = S/D, nwell splits n/p) -- anonymous nets
      -> power rails            structural: the high-degree, gate-free, single-type
                                 source nets are VPWR (PMOS side) and VGND (NMOS side)
      -> channel-connected regions   union S-D through transistors, cut at the rails;
                                 each region bridging the rails is one static CMOS gate
      -> per-gate function      switch-level evaluation of each region -> Boolean op
                                 (a region that stays bistable is a latch/flop -> sequential)

No hierarchy, no cell names, no pin labels, no Liberty are read at any point. The
only technology input is which GDS layer number is poly / diff / nwell / li1 / ...
(the same concession as gds_to_logic). Output: a netlist of virtual gates wired by
anonymous net ids, each with a derived function.
"""
import sys
from collections import Counter, defaultdict

import klayout.db as db

from gds_to_logic import eval_pattern, name_op, sop

# technology layer map (drawing layers + the metal stack for signal nets)
DEV = dict(nwell=(64, 20), diff=(65, 20), poly=(66, 20), licon=(66, 44))
ROUTE = [("li1", 67, 20), ("mcon", 67, 44), ("met1", 68, 20), ("via", 68, 44),
         ("met2", 69, 20), ("via2", 69, 44), ("met3", 70, 20), ("via3", 70, 44),
         ("met4", 71, 20), ("via4", 71, 44), ("met5", 72, 20)]


# ------------------------- polygons -> transistors -------------------------
def extract_transistors(gds_path, flatten=True):
    """Return (trans, gate_nets, sd_deg) from a flat layout.

    trans:     [{type: 'nmos'|'pmos', s, g, d}]  with integer net ids
    gate_nets: set of net ids used as a transistor gate
    per-net stats used later for rail detection.
    """
    ly = db.Layout()
    ly.read(gds_path)
    top = ly.top_cells()[0]
    if flatten:
        top.flatten(-1, True)                     # drop ALL hierarchy -> pure rectangles

    l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(ly, top, []))

    def layer(l, d, nm):
        return l2n.make_polygon_layer(ly.layer(l, d), nm)

    nwell = layer(*DEV["nwell"], "nwell")
    diff = layer(*DEV["diff"], "diff")
    poly = layer(*DEV["poly"], "poly")
    licon = layer(*DEV["licon"], "licon")
    route = {}
    for nm, l, d in ROUTE:
        if ly.find_layer(l, d) is not None:
            route[nm] = layer(l, d, nm)

    gate = poly & diff
    ngate, pgate = gate - nwell, gate & nwell
    nsd, psd = (diff - poly) - nwell, (diff - poly) & nwell

    # connectivity: S/D diffusion, poly, and the whole routing stack via contacts
    for r in (nsd, psd, poly, *route.values()):
        l2n.connect(r)
    l2n.connect(nsd, licon)
    l2n.connect(psd, licon)
    l2n.connect(poly, licon)
    if "li1" in route:
        l2n.connect(licon, route["li1"])
    # metal stack: liK <-> viaK <-> metK+1
    for i in range(0, len(ROUTE) - 1, 2):
        cut, (lo, hi) = ROUTE[i + 1][0], (ROUTE[i][0], ROUTE[i + 2][0])
        if cut in route and lo in route:
            l2n.connect(route[lo], route[cut])
        if cut in route and hi in route:
            l2n.connect(route[cut], route[hi])

    l2n.extract_devices(db.DeviceExtractorMOS3Transistor("NMOS"),
                        {"SD": nsd, "G": ngate, "P": poly})
    l2n.extract_devices(db.DeviceExtractorMOS3Transistor("PMOS"),
                        {"SD": psd, "G": pgate, "P": poly})
    l2n.extract_netlist()

    nl = l2n.netlist()
    circ = max(nl.each_circuit(), key=lambda c: sum(1 for _ in c.each_device()))
    nid = {}

    def netid(net):
        if net is None:
            return None
        k = net.expanded_name()
        return nid.setdefault(k, len(nid))

    trans = []
    gate_nets = set()
    sd_pmos = defaultdict(int)
    sd_nmos = defaultdict(int)
    for d in circ.each_device():
        typ = d.device_class().name.lower()
        s = netid(d.net_for_terminal("S"))
        g = netid(d.net_for_terminal("G"))
        dd = netid(d.net_for_terminal("D"))
        if s is None or dd is None or g is None:
            continue
        trans.append(dict(type=typ, s=s, g=g, d=dd))
        gate_nets.add(g)
        for t in (s, dd):
            (sd_pmos if typ == "pmos" else sd_nmos)[t] += 1
    return trans, gate_nets, sd_pmos, sd_nmos


# ----------------------------- power rails --------------------------------
def find_rails(gate_nets, sd_pmos, sd_nmos):
    """VPWR = the highest-degree net touched only by PMOS S/D; VGND the NMOS dual.
    On a real chip the rails carry thousands of sources and dwarf every internal
    series node. (They may also gate decap/tie cells, so purity -- not 'drives no
    gate' -- is the discriminator.)"""
    def pick(primary, other):
        cands = [(n, primary[n]) for n in primary if other.get(n, 0) == 0]
        return max(cands, key=lambda x: x[1])[0] if cands else None
    return pick(sd_pmos, sd_nmos), pick(sd_nmos, sd_pmos)


# ------------------- channel-connected-region decomposition ----------------
class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def channel_regions(trans, rails):
    """Group nets into CCRs: union a transistor's S and D unless one is a rail.
    Returns {region_root: {nets}} and each transistor tagged with its region."""
    uf = UF()
    for t in trans:
        s, d = t["s"], t["d"]
        if s not in rails and d not in rails:
            uf.union(s, d)
        else:
            uf.find(s)
            uf.find(d)
    for t in trans:
        nonrail = [x for x in (t["s"], t["d"]) if x not in rails]
        t["region"] = uf.find(nonrail[0]) if nonrail else None
    regions = defaultdict(set)
    for t in trans:
        if t["region"] is not None:
            regions[t["region"]].update(x for x in (t["s"], t["d"]) if x not in rails)
    return uf, regions


# --------------------- per-region gate recovery ---------------------------
def recover_gate(members, trans_in, gate_nets, rails):
    """Classify one channel-connected region and find its output node(s). The
    output of a static CMOS gate is the push-pull node touched by BOTH a PMOS and
    an NMOS S/D; internal series nodes touch only one type. A region that reaches
    neither rail is a pass/transmission network (output = highest-degree node).
    Returns region metadata incl. its transistors; the Boolean function is derived
    later at the *component* level so pass-logic composes correctly."""
    devs = [dict(type=t["type"], gate=t["g"], sd=[t["s"], t["d"]]) for t in trans_in]
    ptype, ntype, deg = defaultdict(bool), defaultdict(bool), defaultdict(int)
    touches_rail = False
    for t in trans_in:
        for x in (t["s"], t["d"]):
            if x in rails:
                touches_rail = True
                continue
            (ptype if t["type"] == "pmos" else ntype).__setitem__(x, True)
            deg[x] += 1
    pushpull = [n for n in members if ptype[n] and ntype[n]]
    if pushpull:
        kind, outs = "static", pushpull
    else:                                                # pass / transmission net
        gated = [n for n in members if n in gate_nets]
        outs = gated or ([max(deg, key=deg.get)] if deg else sorted(members)[:1])
        kind = "pass"
    return dict(kind=kind, out_nets=outs, trans=trans_in, members=members,
                n=len(trans_in))


def recover_netlist(gds_path, flatten=True):
    trans, gate_nets, sd_pmos, sd_nmos = extract_transistors(gds_path, flatten)
    vpwr, vgnd = find_rails(gate_nets, sd_pmos, sd_nmos)
    rails = {vpwr: 1, vgnd: 0}
    uf, regions = channel_regions(trans, rails)
    by_region = defaultdict(list)
    for t in trans:
        if t["region"] is not None:
            by_region[t["region"]].append(t)
    gates = []
    for root, members in regions.items():
        g = recover_gate(members, by_region[root], gate_nets, rails)
        g["region"] = root
        gates.append(g)
    return dict(n_trans=len(trans), vpwr=vpwr, vgnd=vgnd, gates=gates,
                gate_nets=gate_nets, rails=rails)


# ------------- group regions into cells and derive each function -----------
def components(res):
    """Weakly-connected components of the recovered regions, joined through shared
    (non-rail) signal nets -- including the output net a region shares with the
    gate it drives. Each component is one recovered cell. No geometry, no labels."""
    gates = res["gates"]
    railset = set(res["rails"])
    uf = UF()
    net_reg = defaultdict(list)
    for gi, g in enumerate(gates):
        uf.find(gi)
        nets = set(g["members"]) | {t["g"] for t in g["trans"]}
        for n in nets - railset:
            net_reg[n].append(gi)
    for gis in net_reg.values():
        for k in range(1, len(gis)):
            uf.union(gis[0], gis[k])
    comps = defaultdict(list)
    for gi, g in enumerate(gates):
        comps[uf.find(gi)].append(g)
    return list(comps.values())


def component_function(regs, rails):
    """Derive a whole cell's I/O function by switch-level over ALL its transistors.
    Primary inputs are nets no region here drives (external signals + pass sources);
    primary outputs are region output nets not consumed as an internal gate. This
    resolves multi-stage and transmission-gate cells uniformly. Returns
    {inputs, outputs:{net:{op,expr,truth}}} or None if it never settles (a flop)."""
    import itertools
    trans = [t for g in regs for t in g["trans"]]
    devs = [dict(type=t["type"], gate=t["g"], sd=[t["s"], t["d"]]) for t in trans]
    railset = set(rails)
    gates_inside = {t["g"] for t in trans}
    driven = set()          # nets the component actively produces (push-pull + pass convergence)
    internal = set()        # static series nodes -- resolved, never inputs
    pass_src = set()        # transmission-gate data sources -- these ARE inputs
    for g in regs:
        driven |= set(g["out_nets"])
        rest = set(g["members"]) - set(g["out_nets"])
        (internal if g["kind"] == "static" else pass_src).update(rest)
    pin_in = sorted((gates_inside | pass_src) - driven - railset - internal)
    pin_out = sorted(driven - gates_inside)
    if not pin_in or not pin_out or len(pin_in) > 10:
        return None
    tables = {o: [] for o in pin_out}
    for bits in itertools.product((0, 1), repeat=len(pin_in)):
        d = dict(rails)
        d.update(dict(zip(pin_in, bits)))
        val = eval_pattern(devs, d)
        for o in pin_out:
            if val.get(o) is None:
                return None                          # bistable -> sequential/flop
            tables[o].append(val[o])
    names = [f"i{i}" for i in range(len(pin_in))]
    outs = {o: dict(op=name_op(names, tables[o]), expr=sop(names, tables[o]),
                    truth=tables[o]) for o in pin_out}
    return dict(inputs=pin_in, outputs=outs, n_trans=len(trans), n_regions=len(regs))


def recover_cells(gds_path, flatten=True):
    """Full pipeline: flat rectangles -> per-cell logic. Returns the rail nets and
    a list of recovered cells (each with derived function or kind='sequential')."""
    res = recover_netlist(gds_path, flatten)
    cells = []
    for regs in components(res):
        fn = component_function(regs, res["rails"])
        if fn is None:
            cells.append(dict(kind="sequential",
                              n_trans=sum(g["n"] for g in regs),
                              n_regions=len(regs)))
        else:
            fn["kind"] = "combinational"
            cells.append(fn)
    return dict(n_trans=res["n_trans"], vpwr=res["vpwr"], vgnd=res["vgnd"],
                regions=len(res["gates"]), cells=cells)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    # Report the primitive gate netlist (works on any flat layout, wired or not).
    # For a strip of INDEPENDENT cells, recover_cells() additionally groups the
    # primitives back into whole cells.
    res = recover_netlist(sys.argv[1])
    rails = res["rails"]
    ops = Counter()
    nonc = 0
    samples = []
    for g in res["gates"]:
        fn = component_function([g], rails)
        if fn is None:
            nonc += 1
            continue
        for o, info in fn["outputs"].items():
            ops[info["op"] or "SOP"] += 1
            if len(samples) < 14:
                tag = f"[{info['op']}]" if info["op"] else ""
                samples.append(f"  gate ({g['n']}T): net{o} = {info['expr']}  {tag}")
    print(f"transistors: {res['n_trans']}   rails: VPWR={res['vpwr']} VGND={res['vgnd']}")
    print(f"primitive channel-connected gates: {len(res['gates'])}  "
          f"({len(res['gates']) - nonc} combinational, {nonc} pass/flop-loop)")
    print(f"operator histogram: {dict(ops.most_common(14))}")
    print("\n".join(samples))


if __name__ == "__main__":
    main()
