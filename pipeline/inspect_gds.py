#!/usr/bin/env python3
"""Inspect a GDS: top cells, child cell usage, layers, labels."""
import sys
from collections import Counter

import klayout.db as db


def main(path):
    ly = db.Layout()
    ly.read(path)
    print(f"== {path}")
    print(f"dbu: {ly.dbu}")
    tops = [c.name for c in ly.top_cells()]
    print(f"top cells: {tops}")
    print(f"total cells: {ly.cells()}")

    for top in ly.top_cells():
        counts = Counter()
        for inst in top.each_inst():
            counts[inst.cell.name] += 1
        print(f"-- instances under top '{top.name}' ({sum(counts.values())} total):")
        for name, n in counts.most_common():
            print(f"   {n:5d}  {name}")
        bbox = top.bbox()
        print(f"   bbox: {bbox} (um: {bbox.width()*ly.dbu:.1f} x {bbox.height()*ly.dbu:.1f})")

    print("-- layers:")
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        shapes = sum(ly.cell(ci).shapes(li).size() for ci in ly.each_cell_top_down())
        print(f"   {info.layer}/{info.datatype}: {shapes} shapes")

    # labels on any layer, top cell only
    for top in ly.top_cells():
        print(f"-- labels in top '{top.name}':")
        for li in ly.layer_indexes():
            info = ly.get_info(li)
            for sh in top.shapes(li).each():
                if sh.is_text():
                    t = sh.text
                    print(f"   {info.layer}/{info.datatype} @ ({t.x*ly.dbu:.2f},{t.y*ly.dbu:.2f}): {t.string}")


if __name__ == "__main__":
    main(sys.argv[1])
