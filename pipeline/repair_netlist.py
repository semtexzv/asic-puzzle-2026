#!/usr/bin/env python3
"""Repair split-net extraction artifacts.

Symptom: KLayout occasionally splits one physical pin into two terminals
when the pin's li1 has a hairline gap -- one keeps the pin label (its net
ends up undriven), the other becomes an unlabeled 'pinN' terminal that
grazes the real (driven) net. This reconnects them.

Rule (general, not hard-coded to one net): for any instance carrying an
unlabeled 'pinN' terminal on net D, and a *labeled* pin of the SAME
instance sitting on an undriven net U, merge U into D (D is the real
electrical net) and delete the phantom terminal. Any other loads of U
follow the merge.
"""
import json
import sys
from collections import defaultdict

OUTPUT_PINS = {"X", "Y", "Q", "Q_N", "HI", "LO", "COUT", "COUT_N", "SUM", "SUM_N"}


def main(inp, outp):
    js = json.load(open(inp))
    portids = {v for v in js["ports"].values()}

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
    undriven = {n for n in loads if n not in driver and n not in portids}

    merges = {}     # U -> D
    drop = []       # (inst, phantom_pin)
    for i in js["instances"]:
        phantom = [(p, n) for p, n in i["pins"].items() if p.startswith("pin")]
        if not phantom:
            continue
        for pp, pd in phantom:
            # labeled pins of this instance on an undriven net
            for p, n in i["pins"].items():
                if p == pp or p in ("VPWR", "VGND") or p in OUTPUT_PINS:
                    continue
                if n in undriven:
                    merges[n] = pd
                    drop.append((i["name"], pp))

    if not merges:
        print("no split-net artifacts found")
        json.dump(js, open(outp, "w"))
        return

    def canon(n):
        seen = set()
        while n in merges and n not in seen:
            seen.add(n); n = merges[n]
        return n

    drop_set = set(drop)
    for i in js["instances"]:
        newpins = {p: canon(n) for p, n in i["pins"].items()
                   if (i["name"], p) not in drop_set}
        i["pins"] = newpins

    newnets = {}
    for k, v in js["nets"].items():
        ck = canon(int(k))
        newnets.setdefault(str(ck), v)
        if v and not newnets[str(ck)]:
            newnets[str(ck)] = v
    js["nets"] = newnets

    json.dump(js, open(outp, "w"))
    for u, d in merges.items():
        print(f"merged undriven net {u} -> driven net {d}")
    print(f"dropped {len(drop)} phantom terminal(s); wrote {outp}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
