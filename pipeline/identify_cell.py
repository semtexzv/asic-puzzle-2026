#!/usr/bin/env python3
"""Identify an anonymized standard cell by geometry match against the
sky130_fd_sc_hd library GDS files.

Compares polygon geometry on the layers that determine the transistor
network (diff/tap/poly/licon/li1/mcon/met1). Reports exact XOR matches.
"""
import glob
import sys

import klayout.db as db

CMP_LAYERS = [(65, 20), (65, 44), (66, 20), (66, 44), (67, 20), (67, 44), (68, 20)]


def cell_regions(ly, cell):
    regs = {}
    for l, d in CMP_LAYERS:
        li = ly.find_layer(l, d)
        if li is None:
            regs[(l, d)] = db.Region()
        else:
            regs[(l, d)] = db.Region(cell.begin_shapes_rec(ly.layer(l, d)))
    return regs


def main():
    gds_path, cell_name, libdir = sys.argv[1], sys.argv[2], sys.argv[3]
    ly = db.Layout()
    ly.read(gds_path)
    target = ly.cell(cell_name)
    tbox = target.dbbox()
    tregs = cell_regions(ly, target)
    print(f"{cell_name}: bbox {tbox.width():.2f} x {tbox.height():.2f} um")

    matches = []
    for path in sorted(glob.glob(f"{libdir}/cells/*/*.gds")):
        lly = db.Layout()
        try:
            lly.read(path)
        except Exception:
            continue
        if lly.dbu != ly.dbu:
            continue
        for cand in lly.top_cells():
            if abs(cand.dbbox().width() - tbox.width()) > 0.01:
                continue
            cregs = cell_regions(lly, cand)
            diffs = []
            for key in CMP_LAYERS:
                x = tregs[key] ^ cregs[key]
                if not x.is_empty():
                    diffs.append((key, x.count()))
            if not diffs:
                matches.append(cand.name)
                print(f"  EXACT MATCH: {cand.name}  ({path.split('/')[-1]})")
            elif len(diffs) <= 2 and sum(n for _, n in diffs) <= 4:
                print(f"  near miss: {cand.name} diffs={diffs}")
    if not matches:
        print("  no exact match found")


if __name__ == "__main__":
    main()
