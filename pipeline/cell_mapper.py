#!/usr/bin/env python3
"""Name-blind standard-cell identifier.

Builds a geometric fingerprint database of the sky130_fd_sc_hd library,
then maps an unknown cell (or every cell in a GDS) to its library
identity purely from polygon geometry -- independent of the instance
name and robust to the 8 placement orientations.

Two-tier fingerprint:
  * DEVICE layers (nwell/diff/tap/poly/licon/npc): determine the
    transistor network; invariant to routing. Primary signature.
  * FULL layers (device + li1/mcon/met1): exact-geometry confirmation.

A cell is IDENTIFIED when some orientation makes its device geometry
XOR to empty against a library cell. Otherwise we report the nearest
library cell and the XOR distance, so tampered or novel cells surface
instead of being silently forced onto a wrong match.
"""
import argparse
import glob
import os
import pickle
import sys
from collections import defaultdict

import klayout.db as db

DEVICE = [("nwell", 64, 20), ("diff", 65, 20), ("tap", 65, 44),
          ("poly", 66, 20), ("licon", 66, 44), ("npc", 95, 20)]
EXTRA = [("li1", 67, 20), ("mcon", 67, 44), ("met1", 68, 20)]

# 8 dihedral orientations as KLayout ICplxTrans (rot*90, mirror)
def orientations():
    for mirror in (False, True):
        for rot in (0, 1, 2, 3):
            yield db.ICplxTrans(1.0, rot * 90, mirror, 0, 0)


def cell_regions(ly, cell, layers):
    regs = {}
    for name, l, d in layers:
        li = ly.find_layer(l, d)
        r = db.Region() if li is None else db.Region(cell.begin_shapes_rec(ly.layer(l, d)))
        r.merge()          # collapse stacked/duplicate shapes -> canonical geometry
        regs[name] = r
    return regs


def shared_norm(regs, keys):
    """Translate ALL layers by one common origin (union bbox lower-left of
    `keys`), preserving inter-layer registration so per-layer XOR is
    meaningful."""
    u = db.Region()
    for k in keys:
        u += regs[k]
    if u.is_empty():
        return {k: regs[k].dup() for k in regs}
    b = u.bbox()
    return {k: _moved(r, -b.left, -b.bottom) for k, r in regs.items()}


def _moved(region, dx, dy):
    r = region.dup()
    r.move(dx, dy)
    return r


def region_to_pts(region):
    """Serialize a Region to a picklable list of (hull, [holes])."""
    out = []
    for p in region.each():
        hull = [(pt.x, pt.y) for pt in p.each_point_hull()]
        holes = [[(pt.x, pt.y) for pt in p.each_point_hole(i)]
                 for i in range(p.holes())]
        out.append((hull, holes))
    return out


def pts_to_region(data):
    r = db.Region()
    for hull, holes in data:
        poly = db.Polygon([db.Point(x, y) for x, y in hull])
        for hole in holes:
            poly.insert_hole([db.Point(x, y) for x, y in hole])
        r.insert(poly)
    return r


def feature_vec(regs):
    """Orientation-invariant scalar signature for fast clustering. Uses
    merged area + perimeter (robust to stacked duplicates); no raw
    polygon counts."""
    v = []
    for name, _, _ in DEVICE:
        r = regs[name]                       # already merged
        v.append(r.area())
        v.append(int(sum(p.perimeter() for p in r.each())))
    b = db.Region()
    for r in regs.values():
        b += r
    bb = b.bbox()
    v.append(min(bb.width(), bb.height()))   # sorted dims -> rotation invariant
    v.append(max(bb.width(), bb.height()))
    return tuple(v)


def fingerprint(ly, cell):
    dev = cell_regions(ly, cell, DEVICE)
    dev_keys = [k for k, _, _ in DEVICE]
    return {
        "feat": feature_vec(dev),
        "dev": shared_norm(dev, dev_keys),
        "bbox": cell.dbbox(),
    }


def build_db(libdir, cache):
    if os.path.exists(cache):
        with open(cache, "rb") as f:
            return pickle.load(f)
    db_entries = {}
    paths = sorted(glob.glob(f"{libdir}/cells/*/*.gds"))
    for path in paths:
        base = os.path.basename(path)[:-4]
        if not base.startswith("sky130_fd_sc_hd__"):
            continue
        ly = db.Layout()
        try:
            ly.read(path)
        except Exception:
            continue
        for top in ly.top_cells():
            if top.name != base:
                continue
            fp = fingerprint(ly, top)
            # store polygons as serialized dbu points for pickling
            db_entries[base] = {
                "feat": fp["feat"],
                "dev": {k: region_to_pts(r) for k, r in fp["dev"].items()},
                "w": round(fp["bbox"].width(), 3),
                "h": round(fp["bbox"].height(), 3),
            }
    with open(cache, "wb") as f:
        pickle.dump(db_entries, f)
    print(f"built library DB: {len(db_entries)} cells -> {cache}", file=sys.stderr)
    return db_entries


def best_orientation_xor(unknown_dev, cand_regs, layers):
    """Min total XOR AREA (dbu^2) over the 8 orientations. Area-based so
    it is immune to stacked duplicates and tolerant of sub-nm slivers."""
    keys = [k for k, _, _ in layers]
    best = None
    for tr in orientations():
        rot = {k: unknown_dev[k].transformed(tr) for k in keys}
        rot = shared_norm(rot, keys)
        area = sum((rot[k] ^ cand_regs[k]).area() for k in keys)
        if best is None or area < best:
            best = area
        if best == 0:
            break
    return best


def identify(fp, db_entries, topk=3):
    # candidate prefilter by device feature vector (exact) else nearest
    exact_feat = [name for name, e in db_entries.items() if e["feat"] == fp["feat"]]
    if exact_feat:
        cands = exact_feat
    else:
        scored = sorted(db_entries.items(),
                        key=lambda kv: sum((a - b) ** 2 for a, b in zip(kv[1]["feat"], fp["feat"])))
        cands = [n for n, _ in scored[:20]]

    results = []
    for name in cands:
        e = db_entries[name]
        cand_dev = {k: pts_to_region(v) for k, v in e["dev"].items()}
        dist = best_orientation_xor(fp["dev"], cand_dev, DEVICE)
        results.append((dist, name))
    results.sort()
    return results[:topk], bool(exact_feat)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gds")
    ap.add_argument("--lib", default="lib/sky130_fd_sc_hd")
    ap.add_argument("--cache", default="build/libdb.pkl")
    ap.add_argument("--cell", help="identify only this cell (default: all defs)")
    ap.add_argument("--assume-unknown", action="store_true",
                    help="ignore instance names; report geometry identity for every cell def")
    args = ap.parse_args()

    db_entries = build_db(args.lib, args.cache)
    ly = db.Layout()
    ly.read(args.gds)

    # which cell definitions actually get instantiated as logic
    tops = {c.name for c in ly.top_cells()}
    targets = []
    if args.cell:
        targets = [ly.cell(args.cell)]
    else:
        for c in ly.each_cell():
            if c.name in tops:
                continue
            if c.name.startswith("VIA_"):
                continue
            if c.is_empty():
                continue
            targets.append(c)

    # distance is XOR area in dbu^2 (1 dbu = 1nm). Treat a few tiny slivers
    # as an exact match (mask-version rounding), larger as near/novel.
    EXACT_A = 0          # perfect geometric identity
    NEAR_A = 200_000     # ~0.2 um^2 total: sliver-level differences

    agree = renamed = novel = nonlogic = 0
    rows = []
    for cell in sorted(targets, key=lambda c: c.name):
        fp = fingerprint(ly, cell)
        empty_dev = all(fp["dev"][k].is_empty() for k, _, _ in DEVICE)
        (results, exact_feat) = identify(fp, db_entries)
        dist, name = results[0]
        truth = cell.name if cell.name.startswith("sky130_fd_sc_hd__") else None

        if empty_dev:
            verdict, name, nonlogic = "NON-LOGIC(no devices)", "-", nonlogic + 1
        elif dist <= EXACT_A:
            verdict = "EXACT"
            if truth and name == truth:
                agree += 1
            elif truth:
                verdict, renamed = "EXACT-RENAMED", renamed + 1
        elif dist <= NEAR_A:
            verdict = f"MATCH(xor={dist}nm2)"
            if truth and name == truth:
                agree += 1
            else:
                renamed += 1
        else:
            verdict, novel = f"NOVEL(xor={dist}nm2)", novel + 1
        alt = "  alts=" + ", ".join(f"{n}:{d}" for d, n in results[1:3]) if len(results) > 1 else ""
        rows.append(f"{verdict:22s} {cell.name:34s} -> {name}{alt}")
    print("\n".join(rows))

    if not args.cell:
        print(f"\nsummary: {agree} identified (name==geometry), {renamed} renamed/ambiguous, "
              f"{novel} novel, {nonlogic} non-logic (of {len(targets)} cell defs)",
              file=sys.stderr)


if __name__ == "__main__":
    main()
