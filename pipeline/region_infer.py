#!/usr/bin/env python3
"""Infer the Star Battle region map from harvested region-valid grids.

Each region-valid grid has exactly 2 stars per region, so solve for an
11-coloring of the 121 cells where every harvested grid has exactly 2
stars of each color, excluding the trivial row/column colorings. Then
test whether the harvested data pins the partition uniquely (up to
relabeling)."""
import json

import z3


def render(region):
    for r in range(11):
        print("   " + " ".join(chr(65 + region[r * 11 + c]) for c in range(11)))


def main():
    grids = json.load(open("build/region_valid_grids.json"))
    stars = [[i for i in range(121) if g[i]] for g in grids]
    print(f"{len(grids)} region-valid grids")

    reg = [z3.Int(f"r_{i}") for i in range(121)]
    s = z3.Solver()
    for i in range(121):
        s.add(reg[i] >= 0, reg[i] <= 10)
    for st in stars:
        for k in range(11):
            s.add(z3.PbEq([(reg[i] == k, 1) for i in st], 2))
    # exclude pure row coloring (some row is not monochromatic) ...
    s.add(z3.Or([reg[r * 11 + c] != reg[r * 11] for r in range(11) for c in range(1, 11)]))
    # ... and pure column coloring
    s.add(z3.Or([reg[c + 11 * rr] != reg[c] for c in range(11) for rr in range(1, 11)]))

    if s.check() != z3.sat:
        print("UNSAT"); return
    m = s.model()
    region = [m.eval(reg[i]).as_long() for i in range(121)]
    print("candidate region map:")
    render(region)
    from collections import Counter
    print("region sizes:", dict(sorted(Counter(region).items())))

    # structural uniqueness: any coloring whose PARTITION differs from this?
    same = {(i, j): (region[i] == region[j])
            for i in range(121) for j in range(i + 1, 121)}
    s.add(z3.Or([(reg[i] == reg[j]) != z3.BoolVal(same[(i, j)])
                 for i in range(121) for j in range(i + 1, 121)]))
    r2 = s.check()
    print("structurally-different partition exists?", r2)
    if r2 == z3.unsat:
        print(">>> region partition is UNIQUELY determined by the data")
        json.dump(region, open("build/region_map.json", "w"))
    else:
        print("data under-determines the partition; need more grids / contiguity")
        json.dump(region, open("build/region_map_candidate.json", "w"))


if __name__ == "__main__":
    main()
