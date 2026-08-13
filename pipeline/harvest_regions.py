#!/usr/bin/env python3
"""Harvest region-valid grids by a random walk in region-valid space.

Start from known region-valid grids; apply 2x2 rectangle swaps (which
preserve 2-per-row and 2-per-column); keep the swapped grids the chip
still calls count-valid ("TWO ..." message => also 2-per-region). Each
kept grid is another data point pinning the region partition.
"""
import json
import random
import subprocess

random.seed(3)
VVP = ["vvp", "build/tb_batch.vvp"]


def stars(bits):
    return {(i // 11, i % 11) for i in range(121) if bits[i]}


def bits_of(st):
    b = [0] * 121
    for (r, c) in st:
        b[r * 11 + c] = 1
    return b


def swap_candidates(st, k):
    st = list(st)
    out = []
    tries = 0
    while len(out) < k and tries < k * 40:
        tries += 1
        (r1, c1), (r2, c2) = random.sample(st, 2)
        if r1 == r2 or c1 == c2:
            continue
        if (r1, c2) in set(st) or (r2, c1) in set(st):
            continue
        ns = set(st)
        ns.discard((r1, c1)); ns.discard((r2, c2))
        ns.add((r1, c2)); ns.add((r2, c1))
        out.append(frozenset(ns))
    return out


def chip_test(grids):
    """Return list of messages for the given grids (as star-sets)."""
    with open("build/grids.mem", "w") as f:
        for st in grids:
            f.write("".join(map(str, bits_of(st))) + "\n")
    r = subprocess.run(VVP + [f"+ng={len(grids)}"], capture_output=True, text=True)
    msgs = {}
    for line in r.stdout.splitlines():
        if line.startswith("G"):
            idx, msg = line.split(" ", 1)
            msgs[int(idx[1:])] = msg.strip()
    return [msgs.get(i, "") for i in range(len(grids))]


def main():
    S = frozenset(stars(json.load(open("build/ANSWER_input.json"))))
    H = frozenset(stars(json.load(open("build/in_hidden.json"))[:121]))
    valid = {S, H}
    target = 5000
    for rnd in range(80):
        seeds = random.sample(list(valid), min(len(valid), 120))
        cands = []
        seen = set(valid)
        for s in seeds:
            for c in swap_candidates(s, 30):
                if c not in seen:
                    seen.add(c); cands.append(c)
        if not cands:
            break
        msgs = chip_test(cands)
        added = 0
        for c, m in zip(cands, msgs):
            if "TWO" in m:            # TWO STARS or TWO NOT TOUCH => region-valid
                if c not in valid:
                    valid.add(c); added += 1
        print(f"round {rnd+1}: tested {len(cands)}, +{added} valid, total {len(valid)}")
        if len(valid) >= target:
            break
    grids = [bits_of(v) for v in valid]
    json.dump(grids, open("build/region_valid_grids.json", "w"))
    print(f"harvested {len(grids)} region-valid grids")


if __name__ == "__main__":
    main()
