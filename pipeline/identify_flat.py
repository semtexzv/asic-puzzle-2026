#!/usr/bin/env python3
"""Flattened-layout cell identification (the 'no hierarchy' case).

Flattens the whole die into one cell, then for each placement carves the
device geometry in that footprint out of the flat layout and identifies
it blind against the library -- proving the geometric mapper still works
when cell boundaries have been dissolved.

Uses only CELL-LOCAL device layers (diff/poly/licon/npc): nwell and tap
run continuously across abutting neighbors, so they can't be clipped per
cell. diff/poly/licon/npc are local to each cell and suffice to pin down
the standard cell.
"""
import argparse
import json
import random
import sys

import klayout.db as db

from cell_mapper import (build_db, orientations, pts_to_region, shared_norm,
                         region_to_pts, _moved)

LOCAL = [("diff", 65, 20), ("poly", 66, 20), ("licon", 66, 44), ("npc", 95, 20)]
ROW_H = 2720  # dbu


def flat_regions(ly, top):
    """Merged device-local Regions for the whole (flattened) die."""
    regs = {}
    for name, l, d in LOCAL:
        li = ly.find_layer(l, d)
        r = db.Region() if li is None else db.Region(top.begin_shapes_rec(ly.layer(l, d)))
        r.merge()
        regs[name] = r
    return regs


def local_db(libdir, cache):
    """Fingerprint DB restricted to the cell-local device layers."""
    full = build_db(libdir, cache)  # ensures library GDS are read once
    import glob, os
    entries = {}
    for path in sorted(glob.glob(f"{libdir}/cells/*/*.gds")):
        base = os.path.basename(path)[:-4]
        if not base.startswith("sky130_fd_sc_hd__"):
            continue
        ly = db.Layout()
        try:
            ly.read(path)
        except Exception:
            continue
        top = next((c for c in ly.top_cells() if c.name == base), None)
        if top is None:
            continue
        regs = {}
        for name, l, d in LOCAL:
            li = ly.find_layer(l, d)
            r = db.Region() if li is None else db.Region(top.begin_shapes_rec(ly.layer(l, d)))
            r.merge()
            regs[name] = r
        keys = [k for k, _, _ in LOCAL]
        norm = shared_norm(regs, keys)
        entries[base] = {k: region_to_pts(v) for k, v in norm.items()}
    return entries


def identify_window(win_regs, entries):
    keys = [k for k, _, _ in LOCAL]
    wn = shared_norm(win_regs, keys)
    best = []
    for name, e in entries.items():
        cand = {k: pts_to_region(v) for k, v in e.items()}
        # quick reject on per-layer area mismatch
        if any(abs(wn[k].area() - cand[k].area()) > 300_000 for k in keys):
            continue
        bx = None
        for tr in orientations():
            rot = shared_norm({k: win_regs[k].transformed(tr) for k in keys}, keys)
            a = sum((rot[k] ^ cand[k]).area() for k in keys)
            bx = a if bx is None else min(bx, a)
            if bx == 0:
                break
        best.append((bx, name))
    best.sort()
    return best[:3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gds")
    ap.add_argument("netlist_json")
    ap.add_argument("--lib", default="lib/sky130_fd_sc_hd")
    ap.add_argument("--cache", default="build/libdb.pkl")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    entries = local_db(args.lib, args.cache)

    ly = db.Layout()
    ly.read(args.gds)
    top = ly.top_cells()[0]
    # fully flatten: dissolve all cell boundaries
    top.flatten(-1, True)
    flat = flat_regions(ly, top)
    dbu = ly.dbu

    insts = [i for i in json.load(open(args.netlist_json))["instances"]
             if not any(s in i["cell"] for s in ("decap", "tap", "fill", "diode", "conb"))]
    rng = random.Random(args.seed)
    sample = rng.sample(insts, min(args.n, len(insts)))

    ok = 0
    for inst in sample:
        # footprint = abutment box (width from library bbox) at placement
        w_um = None
        # width from the cell def bbox
        ci = ly.cell_by_name  # noqa
        llx = round(inst["llx"] / dbu)
        lly = round(inst["lly"] / dbu)
        # library width in dbu
        libname = inst["cell"]
        wdb = _lib_width_dbu(args.lib, libname)
        box = db.Box(llx, lly, llx + wdb, lly + ROW_H)
        clip = db.Region(box)
        win = {k: (flat[k] & clip) for k, _, _ in LOCAL}
        res = identify_window(win, entries)
        got = res[0][1] if res else "?"
        good = (got == inst["cell"])
        ok += good
        flag = "" if good else "  <-- MISMATCH"
        print(f"{'OK ' if good else 'XX '}{inst['name']:6s} truth={inst['cell']:34s} "
              f"got={got} xor={res[0][0] if res else '-'}nm2{flag}")
    print(f"\nflattened-instance accuracy: {ok}/{len(sample)}", file=sys.stderr)


_WIDTH_CACHE = {}


def _lib_width_dbu(libdir, cellname):
    """Exact abutment-box width (dbu) from the library LEF SIZE line."""
    if cellname in _WIDTH_CACHE:
        return _WIDTH_CACHE[cellname]
    import re
    base = cellname.replace("sky130_fd_sc_hd__", "")
    fam = base.rsplit("_", 1)[0]
    path = f"{libdir}/cells/{fam}/{cellname}.lef"
    w_um = None
    for line in open(path):
        m = re.search(r"SIZE\s+([\d.]+)\s+BY\s+([\d.]+)", line)
        if m:
            w_um = float(m.group(1))
            break
    w = round(w_um * 1000)
    _WIDTH_CACHE[cellname] = w
    return w


if __name__ == "__main__":
    main()
