#!/usr/bin/env python3
"""Auto-segmentation of a flattened standard-cell layout.

Given only a flattened GDS (no cell boundaries, no placement info),
recover every cell footprint (row band + x-span + orientation + identity)
by exploiting the placement grid and using the library as a dictionary:

  1. ROWS   -- horizontal power rails (wide met1 stripes) sit on row
               boundaries; their centers give a fixed 2720-dbu pitch.
  2. GRID   -- all cells start on a global 460-dbu site grid.
  3. ORIENT -- per row, nwell in the top vs bottom half fixes whether the
               row is N-type (PMOS up) or flipped.
  4. TILE   -- greedy longest-exact-match tiling on ROUTING-FREE layers
               (nwell/diff/tap/poly/licon/npc): at each grid position try
               library cells widest-first and accept the one whose device
               geometry XORs to zero. Exact match is decisive (0 vs
               millions of nm^2), so a correct tiling is self-anchoring.

Filler/tap/decap cells are in the dictionary too, so they are consumed
and the logic cells between them land on their true boundaries.
"""
import argparse
import json
from collections import defaultdict

import klayout.db as db

from cell_mapper import build_db, shared_norm, pts_to_region, region_to_pts

# cell-LOCAL device layers: no inter-cell wiring AND not shared across
# neighbors (unlike nwell/tap, which run continuously and so can't be
# clipped per cell). A window on these equals the library cell exactly
# when the boundary is right -- the layer set proven by identify_flat.
SEG = [("diff", 65, 20), ("poly", 66, 20), ("licon", 66, 44), ("npc", 95, 20)]
SITE = 460
ROW_H = 2720
RAIL_DT = (68, 20)   # met1 drawing
# filler/physical families carry no local geometry: not tiled, just skipped
FILLER = ("decap", "tap", "fill", "diode", "conb", "antenna")


def orientations4():
    for mirror in (False, True):
        for rot in (0, 2):
            yield db.ICplxTrans(1.0, rot * 90, mirror, 0, 0)


def flat_seg_regions(ly, top):
    regs = {}
    for name, l, d in SEG:
        li = ly.find_layer(l, d)
        r = db.Region() if li is None else db.Region(top.begin_shapes_rec(ly.layer(l, d)))
        r.merge()
        regs[name] = r
    return regs


def detect_rows(ly, top):
    """Return sorted list of row-band bottom y-coords (dbu) and pitch."""
    li = ly.layer(*RAIL_DT)
    W = top.bbox().width()
    centers = set()
    r = db.Region(top.begin_shapes_rec(li)); r.merge()
    for p in r.each():
        b = p.bbox()
        if b.width() > 0.8 * W:              # spans the row -> power rail
            centers.add((b.bottom + b.top) // 2)
    centers = sorted(centers)
    # row bands sit between consecutive rail centers
    bands = [centers[i] for i in range(len(centers) - 1)]
    return bands


def seg_db(libdir, cache):
    """Library fingerprints on SEG layers, grouped by width (dbu)."""
    build_db(libdir, cache)   # ensure library present / cached
    import glob, os, re
    by_width = defaultdict(list)
    keys = [k for k, _, _ in SEG]
    for path in sorted(glob.glob(f"{libdir}/cells/*/*.gds")):
        base = os.path.basename(path)[:-4]
        if not base.startswith("sky130_fd_sc_hd__"):
            continue
        if any(f in base for f in FILLER):     # logic-only dictionary
            continue
        # width from LEF SIZE
        fam = base.replace("sky130_fd_sc_hd__", "").rsplit("_", 1)[0]
        lef = f"{libdir}/cells/{fam}/{base}.lef"
        if not os.path.exists(lef):
            continue
        w = None
        for line in open(lef):
            m = re.search(r"SIZE\s+([\d.]+)\s+BY", line)
            if m:
                w = round(float(m.group(1)) * 1000)
                break
        if not w:
            continue
        ly = db.Layout(); ly.read(path)
        cell = next((c for c in ly.top_cells() if c.name == base), None)
        if cell is None:
            continue
        regs = {}
        for name, l, d in SEG:
            lix = ly.find_layer(l, d)
            rr = db.Region() if lix is None else db.Region(cell.begin_shapes_rec(ly.layer(l, d)))
            rr.merge()
            regs[name] = rr
        norm = shared_norm(regs, keys)
        area = tuple(int(norm[k].area()) for k in keys)
        by_width[w].append({"name": base, "regs": {k: region_to_pts(v) for k, v in norm.items()},
                            "area": area})
    return by_width


def window_regions(flat, box):
    clip = db.Region(box)
    return {k: (flat[k] & clip) for k, _, _ in SEG}


def match_window(win, cands):
    """Return (name, xor_area) of best exact/near library match, or None."""
    keys = [k for k, _, _ in SEG]
    wn = shared_norm(win, keys)
    warea = tuple(int(wn[k].area()) for k in keys)
    best = None
    for c in cands:
        # cheap area prefilter (exact geometry => equal per-layer area)
        if any(abs(warea[i] - c["area"][i]) > 50_000 for i in range(len(keys))):
            continue
        cregs = {k: pts_to_region(v) for k, v in c["regs"].items()}
        bx = None
        for tr in orientations4():
            rot = shared_norm({k: win[k].transformed(tr) for k in keys}, keys)
            a = sum((rot[k] ^ cregs[k]).area() for k in keys)
            bx = a if bx is None else min(bx, a)
            if bx == 0:
                break
        if best is None or bx < best[1]:
            best = (c["name"], bx)
        if best[1] == 0:
            break
    return best


def tile_row(flat, local_all, yb, x0, x1, by_width, widths_desc, max_xor=20_000):
    """Greedy longest-exact-match tiling of one row band. Only logic cells
    are in the dictionary; positions with no local geometry (fillers/empty)
    are skipped a site at a time."""
    tiles = []
    p = x0
    while p < x1 - SITE // 2:
        # fast skip: no local device geometry starting at this site -> filler
        probe = local_all & db.Region(db.Box(p, yb, p + SITE, yb + ROW_H))
        if probe.is_empty():
            p += SITE
            continue
        matched = None
        for w in widths_desc:
            if p + w > x1 + SITE:
                continue
            box = db.Box(p, yb, p + w, yb + ROW_H)
            win = window_regions(flat, box)
            res = match_window(win, by_width[w])
            if res and res[1] <= max_xor:
                matched = (p, w, res[0], res[1])
                break
        if matched:
            tiles.append(matched)
            p += matched[1]
        else:
            p += SITE            # unmatched logic-looking site: step on
    return tiles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gds")
    ap.add_argument("--truth", help="netlist json for scoring")
    ap.add_argument("--lib", default="lib/sky130_fd_sc_hd")
    ap.add_argument("--cache", default="build/libdb.pkl")
    ap.add_argument("--rows", help="limit to N rows for a quick check", type=int)
    ap.add_argument("--out", default="build/segmentation.json")
    args = ap.parse_args()

    by_width = seg_db(args.lib, args.cache)
    widths_desc = sorted(by_width.keys(), reverse=True)

    ly = db.Layout(); ly.read(args.gds)
    top = ly.top_cells()[0]
    top.flatten(-1, True)                    # dissolve ALL hierarchy
    flat = flat_seg_regions(ly, top)
    bands = detect_rows(ly, top)
    if args.rows:
        bands = bands[:args.rows]
    print(f"detected {len(bands)} rows (pitch {ROW_H} dbu)")

    # combined local geometry (for fast empty-site skipping) + x extent
    local_all = db.Region()
    for k in ("poly", "diff"):
        local_all += flat[k]
    local_all.merge()
    x0 = (local_all.bbox().left // SITE) * SITE - SITE
    x1 = local_all.bbox().right + SITE

    seg = []
    for yb in bands:
        tiles = tile_row(flat, local_all, yb, x0, x1, by_width, widths_desc)
        for (px, w, name, xor) in tiles:
            seg.append({"x": px, "y": yb, "w": w, "cell": name, "xor": xor})
    json.dump(seg, open(args.out, "w"))
    print(f"recovered {len(seg)} tiles -> {args.out}")

    if args.truth:
        score(seg, args.truth, ly.dbu, set(bands))


def score(seg, truth_json, dbu, bands):
    js = json.load(open(truth_json))
    truth = []
    for i in js["instances"]:
        truth.append((round(i["llx"] / dbu), round(i["lly"] / dbu),
                      i["cell"].split("__")[-1]))
    truth_by_row = defaultdict(dict)
    for x, y, c in truth:
        if y in bands:
            truth_by_row[y][x] = c
    seg_by_row = defaultdict(dict)
    for t in seg:
        seg_by_row[t["y"]][t["x"]] = t["cell"].split("__")[-1]

    tot_edges = matched_edges = 0
    tot_cells = id_cells = wrong = 0
    logic = lambda c: not any(s in c for s in FILLER)
    for y in bands:
        # score only logic-cell left edges (fillers are intentionally skipped)
        tset = {x for x, c in truth_by_row[y].items() if logic(c)}
        sset = set(seg_by_row[y])
        tot_edges += len(tset)
        matched_edges += len(tset & sset)
        for x, c in truth_by_row[y].items():
            if not logic(c):
                continue
            tot_cells += 1
            if seg_by_row[y].get(x) == c:
                id_cells += 1
        for x, c in seg_by_row[y].items():       # spurious tiles not in truth
            if truth_by_row[y].get(x) != c:
                wrong += 1
    print(f"logic-boundary recall: {matched_edges}/{tot_edges} "
          f"({100*matched_edges/max(tot_edges,1):.1f}%) logic left-edges recovered")
    print(f"logic-cell recall:     {id_cells}/{tot_cells} "
          f"({100*id_cells/max(tot_cells,1):.1f}%) segmented AND correctly identified")
    print(f"false/mislabeled tiles: {wrong}")


if __name__ == "__main__":
    main()
