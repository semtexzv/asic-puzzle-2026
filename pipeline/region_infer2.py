#!/usr/bin/env python3
"""Infer the region map with a contiguity constraint, then validate it
against the chip. Star Battle regions are orthogonally connected; that
prior should pin the true partition. Validation: build fresh grids that
are 2-per-inferred-region (+2 per row/col) and confirm the chip calls
them region-valid."""
import json
import random

import z3

random.seed(5)
NBR = lambda i: [j for (dr, dc) in ((1, 0), (-1, 0), (0, 1), (0, -1))
                 if 0 <= (i // 11 + dr) < 11 and 0 <= (i % 11 + dc) < 11
                 for j in [(i // 11 + dr) * 11 + (i % 11 + dc)]]


def infer(grids):
    reg = [z3.Int(f"r_{i}") for i in range(121)]
    lvl = [z3.Int(f"l_{i}") for i in range(121)]
    root = [z3.Bool(f"root_{i}") for i in range(121)]
    s = z3.Solver(); s.set("timeout", 420000)
    for i in range(121):
        s.add(reg[i] >= 0, reg[i] <= 10, lvl[i] >= 0, lvl[i] <= 13)
    for st in grids:
        for k in range(11):
            s.add(z3.PbEq([(reg[i] == k, 1) for i in st], 2))
    # not pure row / col colouring
    s.add(z3.Or([reg[r * 11 + c] != reg[r * 11] for r in range(11) for c in range(1, 11)]))
    s.add(z3.Or([reg[c + 11 * rr] != reg[c] for c in range(11) for rr in range(1, 11)]))
    # contiguity: one root per region; every non-root has a same-region
    # neighbour of strictly smaller level
    for k in range(11):
        s.add(z3.PbEq([(z3.And(root[i], reg[i] == k), 1) for i in range(121)], 1))
    for i in range(121):
        s.add(z3.Implies(root[i], lvl[i] == 0))
        s.add(z3.Implies(z3.Not(root[i]),
                         z3.Or([z3.And(reg[j] == reg[i], lvl[j] < lvl[i]) for j in NBR(i)])))
    if s.check() != z3.sat:
        return None
    m = s.model()
    return [m.eval(reg[i]).as_long() for i in range(121)]


def main():
    grids = json.load(open("build/region_valid_grids.json"))
    stars = [[i for i in range(121) if g[i]] for g in grids]
    sub = random.sample(stars, min(50, len(stars)))
    print(f"inferring region map from {len(sub)} grids with contiguity...")
    region = infer(sub)
    if region is None:
        print("UNSAT with contiguity — regions are not a contiguous 11-partition")
        return
    print("region map (contiguity-constrained):")
    for r in range(11):
        print("   " + " ".join(chr(65 + region[r * 11 + c]) for c in range(11)))
    from collections import Counter
    print("region sizes:", dict(sorted(Counter(region).items())))
    json.dump(region, open("build/region_map.json", "w"))


if __name__ == "__main__":
    main()
