#!/usr/bin/env python3
"""Render GDS device/metal layers to a self-contained SVG, layout-view style
(fixed layer colours on a dark panel). Used for the blog figures."""
import klayout.db as db

# (name, layer, datatype, fill, stroke, opacity)  -- back to front
LAYERS = [
    ("nwell", 64, 20, "none",    "#3b4a63", 0.9),
    ("diff",  65, 20, "#2f9e5e", "#3fd07f", 0.9),
    ("poly",  66, 20, "#d64545", "#ff6b6b", 0.95),
    ("licon", 66, 44, "#1b1f27", "#f0b400", 1.0),
    ("li1",   67, 20, "#8a63d2", "#a889f0", 0.55),
    ("mcon",  67, 44, "#1b1f27", "#c9a227", 1.0),
    ("met1",  68, 20, "#3d6fe0", "#6b95ff", 0.34),
]


def clip_region(ly, cell, l, d, box):
    li = ly.find_layer(l, d)
    if li is None:
        return db.Region()
    r = db.Region(cell.begin_shapes_rec(ly.layer(l, d)))
    return r & db.Region(box)


def render(ly, cell, box, scale=44, pad=8, mirror=False, layers=LAYERS,
           panel="#0d1117"):
    dbu = ly.dbu
    x0, y0, x1, y1 = box.left * dbu, box.bottom * dbu, box.right * dbu, box.top * dbu
    W = (x1 - x0) * scale + 2 * pad
    H = (y1 - y0) * scale + 2 * pad

    def X(xu):
        u = (x1 - xu) if mirror else (xu - x0)
        return round(pad + u * scale, 2)

    def Y(yu):
        return round(pad + (y1 - yu) * scale, 2)   # flip y (GDS up -> SVG down)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {round(W,1)} {round(H,1)}" '
           f'class="gdsfig" role="img">']
    out.append(f'<rect x="0" y="0" width="{round(W,1)}" height="{round(H,1)}" fill="{panel}"/>')
    for name, l, d, fill, stroke, op in layers:
        reg = clip_region(ly, cell, l, d, box)
        if reg.is_empty():
            continue
        out.append(f'<g fill="{fill}" fill-opacity="{op}" stroke="{stroke}" '
                   f'stroke-width="0.8" stroke-opacity="{min(1,op+0.3)}">')
        for poly in reg.merged().each():
            pts = " ".join(f"{X(p.x*dbu)},{Y(p.y*dbu)}" for p in poly.each_point_hull())
            out.append(f'<polygon points="{pts}"/>')
        out.append("</g>")
    return out, W, H, X, Y


def render_patch(gds, box, cell_boxes=None, scale=44, mirror=False):
    ly = db.Layout(); ly.read(gds)
    top = ly.top_cells()[0]
    out, W, H, X, Y = render(ly, top, box, scale=scale, mirror=mirror)
    if cell_boxes:
        for (bx, by, bw, bh, label) in cell_boxes:
            x, y = X(bx), Y(by + bh)
            out.append(f'<rect x="{x}" y="{y}" width="{round(bw*scale,1)}" '
                       f'height="{round(bh*scale,1)}" fill="none" stroke="#ffd75e" '
                       f'stroke-width="1.6" stroke-dasharray="4 3"/>')
            if label:
                out.append(f'<text x="{x+3}" y="{y+12}" fill="#ffd75e" '
                           f'font-family="ui-monospace,Menlo,monospace" font-size="10">{label}</text>')
    out.append("</svg>")
    return "".join(out)


def render_cell(gds, scale=54, mirror=False, layers=None):
    ly = db.Layout(); ly.read(gds)
    cell = ly.top_cells()[0]
    box = cell.bbox()
    out, W, H, X, Y = render(ly, cell, box, scale=scale, mirror=mirror,
                             layers=layers or LAYERS)
    out.append("</svg>")
    return "".join(out)
