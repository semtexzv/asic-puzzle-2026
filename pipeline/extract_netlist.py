#!/usr/bin/env python3
"""Extract a structural netlist from a sky130 OpenROAD-flow GDS.

Approach: the GDS keeps standard-cell hierarchy, so we don't extract
transistors. We flatten the VIA_* cells into pure geometry, declare
inter-layer connectivity (li1..met5 + cut layers), and let KLayout's
LayoutToNetlist compute hierarchical connectivity. Each standard cell
becomes a circuit whose pins are named by the li1 pin labels inside the
cell; the top circuit's nets are named by the top-level port labels.

Output: JSON netlist {cells, instances, nets, ports}.
"""
import json
import sys
from collections import defaultdict

import klayout.db as db

# sky130 (layer, datatype) map — drawing + label layers
COND_LAYERS = [  # conducting, in stack order
    ("li1", 67, 20),
    ("mcon", 67, 44),
    ("met1", 68, 20),
    ("via", 68, 44),
    ("met2", 69, 20),
    ("via2", 69, 44),
    ("met3", 70, 20),
    ("via3", 70, 44),
    ("met4", 71, 20),
    ("via4", 71, 44),
    ("met5", 72, 20),
]
LABEL_LAYERS = {  # attach labels to these conductors
    "li1": (67, 5),
    "met1": (68, 5),
    "met2": (69, 5),
    "met3": (70, 5),
    "met4": (71, 5),
    "met5": (72, 5),
}


def extract(gds_path):
    ly = db.Layout()
    ly.read(gds_path)
    assert len(ly.top_cells()) == 1, [c.name for c in ly.top_cells()]
    top = ly.top_cells()[0]

    # Flatten VIA_* cells so vias are geometry, not subcircuits
    via_insts = []
    for cell in ly.each_cell():
        for inst in cell.each_inst():
            if inst.cell.name.startswith("VIA_"):
                via_insts.append(inst)
    for inst in via_insts:
        inst.flatten()
    for cell in [c for c in ly.each_cell() if c.name.startswith("VIA_")]:
        ly.delete_cell(cell.cell_index())

    l2n = db.LayoutToNetlist(db.RecursiveShapeIterator(ly, top, []))
    regions = {}
    for name, l, d in COND_LAYERS:
        regions[name] = l2n.make_polygon_layer(ly.layer(l, d), name)
    texts = {}
    for name, (l, d) in LABEL_LAYERS.items():
        texts[name] = l2n.make_text_layer(ly.layer(l, d), name + "_lbl")

    for name, _, _ in COND_LAYERS:
        l2n.connect(regions[name])
    for i in range(len(COND_LAYERS) - 1):
        a, b = COND_LAYERS[i][0], COND_LAYERS[i + 1][0]
        l2n.connect(regions[a], regions[b])
    for name, t in texts.items():
        l2n.connect(regions[name], t)

    l2n.extract_netlist()
    return ly, l2n  # keep l2n alive: it owns the Netlist object


def netlist_to_dict(ly, l2n, top_name):
    nl = l2n.netlist()
    il = l2n.internal_layout()  # circuit.cell_index refers to this layout
    top = nl.circuit_by_name(top_name)
    assert top is not None, [c.name for c in nl.each_circuit()]

    # pin names per cell circuit: name pins after the labeled net they
    # connect to inside the cell definition
    cell_pins = {}
    for c in nl.each_circuit():
        if c.name == top_name:
            continue
        pins = {}
        for pin in c.each_pin():
            net = c.net_for_pin(pin.id())
            pins[pin.id()] = (net.name if net is not None and net.name else None)
        cell_pins[c.name] = pins

    dbu = ly.dbu
    nets = {}
    instances = []
    for i, sc in enumerate(top.each_subcircuit()):
        cname = sc.circuit_ref().name
        t = sc.trans  # DCplxTrans in um
        # DEF-style placement lower-left from GDS origin + orientation.
        # Row height is fixed (2.72 for sky130 HD); bbox width has no
        # x-overhang, but bbox height does (nwell), so don't use bbox y.
        w = il.cell(sc.circuit_ref().cell_index).dbbox().width()
        H = 2.72
        x, y = t.disp.x, t.disp.y
        if t.is_mirror():
            llx, lly = (x, y - H) if int(t.angle) == 0 else (x - w, y)
        else:
            llx, lly = (x, y) if int(t.angle) == 0 else (x - w, y - H)
        conns = {}
        for pin in sc.circuit_ref().each_pin():
            net = sc.net_for_pin(pin.id())
            if net is None:
                continue
            nid = net.cluster_id
            nets.setdefault(nid, net.name if net.name else None)
            pname = cell_pins[cname].get(pin.id()) or f"pin{pin.id()}"
            conns[pname] = nid
        instances.append({
            "name": f"i{i}",
            "cell": cname,
            "x": round(t.disp.x, 3),
            "y": round(t.disp.y, 3),
            "llx": round(llx, 3),
            "lly": round(lly, 3),
            "orient": f"{'M' if t.is_mirror() else 'R'}{int(t.angle)}",
            "pins": conns,
        })

    ports = {}
    for net in top.each_net():
        if net.name:
            nets.setdefault(net.cluster_id, net.name)
            ports[net.name] = net.cluster_id

    return {
        "top": top_name,
        "dbu": dbu,
        "instances": instances,
        "nets": {str(k): v for k, v in nets.items()},
        "ports": ports,
    }


def main():
    gds_path, out_path = sys.argv[1], sys.argv[2]
    ly, l2n = extract(gds_path)
    top_name = ly.top_cells()[0].name
    d = netlist_to_dict(ly, l2n, top_name)
    with open(out_path, "w") as f:
        json.dump(d, f, indent=1)
    ncells = defaultdict(int)
    for inst in d["instances"]:
        ncells[inst["cell"]] += 1
    print(f"{gds_path}: {len(d['instances'])} instances, "
          f"{len(d['nets'])} nets, ports: {sorted(d['ports'])}")
    unnamed_pins = sum(1 for i in d["instances"] for p in i["pins"] if p.startswith("pin"))
    print(f"unnamed pins: {unnamed_pins}")


if __name__ == "__main__":
    main()
