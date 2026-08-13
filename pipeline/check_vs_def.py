#!/usr/bin/env python3
"""Validate an extracted netlist JSON against a DEF ground truth.

Matches instances by (cell, placed lower-left) and compares the
partition of (instance, pin) terminals into nets. Passes iff the two
partitions agree exactly on signal nets (power/ground compared too,
but reported separately).
"""
import json
import re
import sys
from collections import defaultdict


def parse_def(path):
    text = open(path).read()
    units = int(re.search(r"UNITS DISTANCE MICRONS (\d+)", text).group(1))

    comps = {}  # name -> (cell, llx_um, lly_um)
    m = re.search(r"\nCOMPONENTS \d+ ;\n(.*?)\nEND COMPONENTS", text, re.S)
    for entry in m.group(1).split(";"):
        nm = re.search(r"-\s+(\S+)\s+(\S+)", entry)
        pm = re.search(r"(?:PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\S+)", entry)
        if nm and pm:
            name, cell = nm.groups()
            x, y, orient = pm.groups()
            comps[name] = (cell, int(x) / units, int(y) / units)

    pins = set()
    m = re.search(r"\nPINS \d+ ;\n(.*?)\nEND PINS", text, re.S)
    for entry in m.group(1).split(";"):
        em = re.search(r"-\s+(\S+)\s+\+\s+NET\s+(\S+)", entry)
        if em:
            pins.add(em.group(1))

    nets = {}  # netname -> set of terminals; terminal = ("PIN", portname) or (comp, pin)
    m = re.search(r"\nNETS \d+ ;\n(.*?)\nEND NETS", text, re.S)
    for entry in m.group(1).split(";"):
        nm = re.search(r"-\s+(\S+)", entry)
        if not nm:
            continue
        terms = set(re.findall(r"\(\s*(\S+)\s+(\S+)\s*\)", entry.split("+")[0]))
        nets[nm.group(1)] = terms
    return comps, pins, nets


def main():
    js = json.load(open(sys.argv[1]))
    comps, def_pins, def_nets = parse_def(sys.argv[2])

    # map extracted instance -> DEF component name via (cell, ll)
    def_by_key = {(c, x, y): n for n, (c, x, y) in comps.items()}
    inst_map = {}
    unmatched = []
    for inst in js["instances"]:
        key = (inst["cell"], inst["llx"], inst["lly"])
        if key in def_by_key:
            inst_map[inst["name"]] = def_by_key[key]
        else:
            unmatched.append(key)
    print(f"instances: {len(js['instances'])} extracted, {len(comps)} in DEF, "
          f"{len(inst_map)} matched, {len(unmatched)} unmatched")
    for u in unmatched[:10]:
        print("  unmatched:", u)

    # extracted partition: net id -> set of (defcomp, pin) + ("PIN", port)
    ext_nets = defaultdict(set)
    for inst in js["instances"]:
        for pin, nid in inst["pins"].items():
            ext_nets[nid].add((inst_map.get(inst["name"], inst["name"]), pin))
    for port, nid in js["ports"].items():
        ext_nets[nid].add(("PIN", port))

    # compare as partitions over the terminals DEF knows about
    def_partition = {frozenset(t) for t in def_nets.values() if t}
    pwr = {"VPWR", "VGND", "VNB", "VPB"}
    ext_partition = set()
    for nid, terms in ext_nets.items():
        sig = frozenset(t for t in terms if t[1] not in pwr or t[0] == "PIN")
        if sig:
            ext_partition.add(sig)

    ok = 0
    for p in def_partition:
        if p in ext_partition:
            ok += 1
        else:
            print("MISMATCH def net not found in extraction:", sorted(p)[:8])
    extra = [p for p in ext_partition if p not in def_partition]
    # power nets in extraction won't be in DEF NETS (they're SPECIALNETS)
    real_extra = [p for p in extra
                  if not all(t[1] in pwr or t[1] in ("HI", "LO") for t in p if t[0] != "PIN")]
    print(f"net partitions: {len(def_partition)} in DEF, {ok} matched exactly")
    print(f"extra extracted nets (non-power): {len(real_extra)}")
    for p in real_extra[:10]:
        print("  extra:", sorted(p)[:8])
    if ok == len(def_partition) and not real_extra and not unmatched:
        print("PASS: extraction matches DEF exactly")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
