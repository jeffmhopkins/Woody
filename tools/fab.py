#!/usr/bin/env python3
"""
The controller body's FABRICATION FILES (issue #42): what goes to a laser or
waterjet shop for the aluminium plates and to a CNC shop for the oak parts.

    python3 tools/fab.py step    --stl <part.stl> --name <output> --out <part.step> --fingerprint <fp>
    python3 tools/fab.py drawing --part <part>    --name <output> --out <part.pdf>  --fingerprint <fp>
    python3 tools/fab.py open    --name <output>  --out <open-figures.csv> --fingerprint <fp>
    python3 tools/fab.py open --print            # the same list, to the terminal; writes nothing

tools/cad.py runs the first three (`scripts:` in mechanical/outputs.yaml).
Never write into mechanical/fab/ by hand: those files are ledgered, and
`cad.py check` fails on a file the ledger did not see built.

WHERE EACH THING COMES FROM - nothing is restated here:
  * the solids: mechanical/fab/*.stl, the body model's own solids, one per
    part, moved into the part's frame by mechanical/cad/fab_parts.scad;
  * every outline and cut: the part's DXFs (mechanical/export/*.dxf, and
    mechanical/fab/tail-cap-recess.dxf);
  * every thickness, depth, face and hole position: mechanical/export/
    fab-geometry.echo, which fab_parts.scad prints from the model's variables;
  * material, finish, revision and tolerances: config/body.yaml `fabrication`;
    the plate thickness: config/key-layout.yaml (the register's
    `plate-thickness`);
  * hardware part numbers: hardware/bom.csv, by the BOM ref the echo names;
  * the open figures: config/body.yaml statuses, reached by a static walk of
    the OpenSCAD source (below).

STEP. OpenSCAD 2021.01 writes STL and no STEP; FreeCAD is not installed. The
OpenCASCADE kernel is (OCP, as gmsh's), so the STEP is the STL sewn into one
closed shell, made a solid, and its coplanar triangles merged back into
planar faces (ShapeUpgrade_UnifySameDomain). Flat faces, walls and pocket
floors come out as true planes; a hole or a rounded edge stays faceted at
the model's $fn, exactly as in the DXF the laser gets. A part whose solid is
not one valid closed shell fails the build.

THE OPEN-FIGURE WALK. For each part, every config/body.yaml figure its
geometry can depend on: the identifiers its layers' 2D modules, its
fab_geom() echo lines and its 3D finish (sanded_panel / sanded_cap) use,
followed through every top-level variable, function and module of
woody_body.scad and fab_parts.scad to the params they read. It is
CONSERVATIVE - a figure on a branch the model does not take still counts - so
a figure listed here may change nothing; one missing would be a defect. A
`tbd` figure is BLOCKING (no document gives the number; the part would be
cut to a placeholder) unless NOT_BLOCKING below names it with its reason; a
`nominal` one is a working estimate the part can be ordered on.
"""
import argparse
import csv
import datetime
import importlib.util
import io
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODY = "config/body.yaml"
KEY_LAYOUT = "config/key-layout.yaml"
BOM = "hardware/bom.csv"
GEOM = "mechanical/export/fab-geometry.echo"
SPEC = "mechanical/outputs.yaml"
MODEL = "mechanical/cad/woody_body.scad"
FAB_SCAD = "mechanical/cad/fab_parts.scad"
PARAMS = "mechanical/cad/generated/params.scad"

# Each part: its title, what it is cut from, its BOM row, and the 3D finish
# module its solid adds to its layers (the walk's extra root).
PARTS = {
    "plate_top":    dict(title="Key plate", stock="metal", bom="PLATE-TOP", finish_root=None),
    "plate_bottom": dict(title="Bottom plate", stock="metal", bom="PLATE-BOTTOM", finish_root=None),
    "oak_top":      dict(title="Oak top", stock="wood", bom="BODY-OAK", finish_root="sanded_panel"),
    "oak_bottom":   dict(title="Oak bottom", stock="wood", bom="BODY-OAK", finish_root="sanded_panel"),
    "mouth_cap":    dict(title="Mouth cap", stock="wood", bom="ENDCAP-MOUTH", finish_root="sanded_cap"),
    "tail_cap":     dict(title="Tail cap", stock="wood", bom="ENDCAP-TAIL", finish_root="sanded_cap"),
}

# What each kind of part's drawing reads from config/body.yaml `fabrication`,
# besides its geometry - so the open-figure list counts them too.
FAB_LEAVES = {
    "metal": ["fabrication.revision", "fabrication.plate_alloy", "fabrication.plate_finish",
              "fabrication.plate_profile_tol", "fabrication.cutout_tol", "fabrication.stud_hole_tol"],
    "wood": ["fabrication.revision", "fabrication.wood_species", "fabrication.wood_finish",
             "fabrication.wood_profile_tol", "fabrication.wood_depth_tol"],
}

# tbd figures a part can be ordered without, and why. Anything not here that
# is tbd blocks the part it reaches.
NOT_BLOCKING = {
    "stack.edge_r": "the sanded roundover: the STEP shows it, but it goes on by hand after the parts are cut (config/body.yaml), so a shop may leave the edges square",
    "logo.laser_min_gap": "a check on the etch (drc.echo 'logo'), not a dimension of the cut; the etch test on an offcut answers it",
}


def read(path, mode="r"):
    print(f"READ: {path}")
    return open(os.path.join(ROOT, path), mode, **({} if "b" in mode else {"encoding": "utf-8"}))


# ------------------------------------------------------------------ data ----

def geom():
    """fab-geometry.echo -> {part: {"stock": ..., "layers": [...], "holes": [...], "cutouts": ...}}"""
    import ast
    out = {p: {"layers": [], "holes": []} for p in PARTS}
    for line in read(GEOM):
        m = re.match(r'ECHO: "FAB", (.*)$', line.strip())
        if not m:
            continue
        v = ast.literal_eval("[" + m.group(1).replace("undef", "None") + "]")
        part, kind, rest = v[0], v[1], v[2:]
        g = out[part]
        if kind == "stock":
            g["stock"] = dict(t=rest[0], x=rest[1], y=rest[2], faces=rest[3])
        elif kind == "layer":
            g["layers"].append(dict(dxf=rest[0], face=rest[1], depth=rest[2], what=rest[3]))
        elif kind == "hole":
            g["holes"].append(dict(what=rest[0], x=rest[1], y=rest[2], d=rest[3], face=rest[4], depth=rest[5], bom=rest[6]))
        elif kind == "cutouts":
            g["cutouts"] = dict(n=rest[0], s=rest[1])
    for p, g in out.items():
        if "stock" not in g:
            raise SystemExit(f"fab.py: {GEOM} has no stock for {p} - rebuild it (cad.py build fab-geometry)")
    return out


def body():
    return yaml.safe_load(read(BODY))


def bom():
    return {r["ref"]: r for r in csv.DictReader(read(BOM))}


def plate_thickness():
    return yaml.safe_load(read(KEY_LAYOUT))["meta"]["plate_thickness"]


def cad_module():
    print("READ: tools/cad.py")   # its flatten() names the params, so the walk ends on its names
    spec = importlib.util.spec_from_file_location("cad", os.path.join(ROOT, "tools/cad.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ walk ----

def scad_symbols(path):
    """Top-level definitions of an OpenSCAD file: {name: set(identifiers used)}.
    Comments and string literals are dropped first, so a solid's id or a label
    is never read as a dependency."""
    src = read(path).read()
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    raw = src
    src = re.sub(r'"(?:\\.|[^"\\])*"', '""', src)
    defs, i, n = {}, 0, len(src)

    def stmt_end(j):
        """The end of the statement starting at j: a `;` at depth 0, or a
        balanced { } block that closes at depth 0."""
        depth = 0
        while j < n:
            c = src[j]
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
                if depth == 0 and c == "}":
                    k = j + 1
                    while k < n and src[k] in " \t\r\n":
                        k += 1
                    # `} else ...` continues the statement
                    if not src.startswith("else", k):
                        return j + 1
            elif c == ";" and depth == 0:
                return j + 1
            j += 1
        return n

    ident = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
    while i < n:
        while i < n and src[i] in " \t\r\n;":
            i += 1
        if i >= n:
            break
        j = stmt_end(i)
        s = src[i:j]
        m = re.match(r"(module|function)\s+([A-Za-z_]\w*)", s) or re.match(r"()([A-Za-z_$]\w*)\s*=(?!=)", s)
        if m:
            defs.setdefault(m.group(2), set()).update(ident.findall(s[m.end():]))
        i = j
    return defs, raw


def walk(roots, defs):
    seen, todo = set(), list(roots)
    while todo:
        s = todo.pop()
        if s in seen:
            continue
        seen.add(s)
        todo.extend(defs.get(s, ()))
    return seen


def part_roots(part, model_src, fab_src, geom_src):
    """The identifiers a part's geometry starts from: its layers' 2D modules
    (outputs.yaml says which part= or fab= each DXF is; the dispatch line says
    which module that is), its fab_geom() lines, and its 3D finish module."""
    spec = yaml.safe_load(read(SPEC))
    by_out = {e["out"]: e for e in spec.get("exports") or []}
    roots = set()
    ident = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
    stmts = [re.sub(r'"[^"]*"', '""', l) for l in geom_src.split(";")]
    # fab_geom()'s own locals (o, po): a part reaches one only if its lines use it
    local = {m.group(1): set(ident.findall(l[m.end():])) for l in stmts for m in [re.match(r"\s*(\w+)\s*=(?!=)", l)] if m}
    for l, raw in zip(stmts, geom_src.split(";")):
        if f'"{part}"' in raw:
            ids = set(ident.findall(l))
            roots.update(ids)
            for n in ids & set(local):
                roots.update(local[n])
    for l in re.findall(r'layer\("' + part + r'", "([^"]+)"', geom_src):
        e = by_out.get(l)
        if e is None:
            raise SystemExit(f"fab.py: {part}'s layer {l} is no export in {SPEC}")
        d = e.get("defines") or {}
        key, val, src = ("p", d["part"], model_src) if "part" in d else ("fab", d["fab"], fab_src)
        m = re.search(r'\(' + key + r' == "' + re.escape(val) + r'"\)([^\n]*)', src)
        if not m:
            raise SystemExit(f"fab.py: no dispatch for {key} == {val!r} - teach part_roots() its new shape")
        roots.update(ident.findall(m.group(1)))
    if PARTS[part]["finish_root"]:
        roots.add(PARTS[part]["finish_root"])
    return roots


def open_figures():
    """[(part, yaml path, status, value, decided_by, blocking, why)] for every
    tbd and nominal config/body.yaml figure each part's geometry can reach."""
    cad = cad_module()
    b = body()
    leaves = []
    cad.flatten("", {k: v for k, v in b.items() if k != "meta"}, leaves)
    # the scad name -> the YAML path it came from
    paths = {}

    def index(prefix, node):
        for k, v in node.items():
            name = f"{prefix}_{cad.scad_name(k)}" if prefix else cad.scad_name(k)
            dotted = f"{index.dot}.{k}" if index.dot else k
            if isinstance(v, dict) and "value" in v:
                paths[name] = dotted
            elif isinstance(v, dict):
                was, index.dot = index.dot, dotted
                index(name, v)
                index.dot = was
    index.dot = ""
    index("", {k: v for k, v in b.items() if k != "meta"})
    model_defs, model_src = scad_symbols(MODEL)
    fab_defs, fab_src = scad_symbols(FAB_SCAD)
    read(PARAMS)   # the names the walk ends on are its; read so the fingerprint covers it
    defs = dict(model_defs)
    for k, v in fab_defs.items():
        defs.setdefault(k, set()).update(v)
    fab_body = re.search(r"module fab_geom\(\)\s*\{(.*?)\n\}", open(os.path.join(ROOT, FAB_SCAD), encoding="utf-8").read(), re.S)
    if not fab_body:
        raise SystemExit(f"fab.py: no fab_geom() in {FAB_SCAD}")
    rows = []
    for part in PARTS:
        reach = walk(part_roots(part, model_src, fab_src, fab_body.group(1)), defs)
        # and what its drawing tells the shop (config/body.yaml `fabrication`)
        reach |= {n for n, d in paths.items() if d in FAB_LEAVES[PARTS[part]["stock"]]}
        for name, spec in leaves:
            st = spec.get("status")
            if name not in reach or st not in ("tbd", "nominal"):
                continue
            dotted = paths[name]
            blocking = st == "tbd" and dotted not in NOT_BLOCKING
            why = (spec.get("decided_by") or "") if blocking else NOT_BLOCKING.get(dotted, "a working estimate the part can be cut to")
            rows.append((part, dotted, st, spec["value"], spec.get("decided_by", ""), "yes" if blocking else "no", why))
    return rows


# ------------------------------------------------------------------ step ----

def cmd_step(a):
    from OCP.StlAPI import StlAPI_Reader
    from OCP.TopoDS import TopoDS_Shape, TopoDS
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.TopExp import TopExp_Explorer
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.Interface import Interface_Static
    import tempfile
    print(f"READ: {a.stl}")
    mesh = TopoDS_Shape()
    if not StlAPI_Reader().Read(mesh, os.path.join(ROOT, a.stl)):
        raise SystemExit(f"fab.py: could not read {a.stl}")
    sew = BRepBuilderAPI_Sewing(1e-4)
    sew.Add(mesh)
    sew.Perform()
    shells = []
    ex = TopExp_Explorer(sew.SewedShape(), TopAbs_SHELL)
    while ex.More():
        shells.append(TopoDS.Shell(ex.Current()))
        ex.Next()
    if len(shells) != 1:
        raise SystemExit(f"fab.py: {a.stl} sews into {len(shells)} shells, not one closed part")
    solid = BRepBuilderAPI_MakeSolid(shells[0]).Solid()
    u = ShapeUpgrade_UnifySameDomain(solid, True, True, True)
    u.Build()
    shape = u.Shape()
    if not BRepCheck_Analyzer(shape).IsValid():
        raise SystemExit(f"fab.py: {a.stl} does not make a valid solid")
    w = STEPControl_Writer()
    Interface_Static.SetCVal_s("write.step.unit", "MM")
    w.Transfer(shape, STEPControl_AsIs)
    with tempfile.TemporaryDirectory() as td:
        tmp = os.path.join(td, "part.step")
        w.Write(tmp)
        txt = open(tmp, encoding="utf-8").read()
    # The header names the part and the CAD state it shows, as a render's
    # stamp does; no timestamp, so the same model writes the same file.
    stem = os.path.splitext(os.path.basename(a.out))[0]
    txt = re.sub(r"FILE_DESCRIPTION\(\(.*?\),", f"FILE_DESCRIPTION(('Woody body {stem}, mm','cad {a.fingerprint[:12]}',"
                 f"'verify: python3 tools/cad.py explain {a.name}'),", txt, count=1, flags=re.S)
    txt = re.sub(r"FILE_NAME\('.*?','.*?',", f"FILE_NAME('{stem}.step','2000-01-01T00:00:00',", txt, count=1, flags=re.S)
    txt = re.sub(r"PRODUCT\('Open CASCADE STEP translator[^']*','Open CASCADE STEP translator[^']*'",
                 f"PRODUCT('{stem}','{stem}'", txt, count=1)
    open(a.out, "w", encoding="utf-8", newline="\n").write(txt)
    import OCP
    print(f"TOOL: fab.py step; OCP {getattr(OCP, '__version__', '?')}")


# ------------------------------------------------------------------ open ----

OPEN_COLS = ["part", "figure", "status", "value", "decided_by", "blocking", "why"]


def cmd_open(a):
    rows = open_figures()
    if a.print:
        for r in rows:
            print(f"{r[0]:13} {r[5]:3} {r[2]:8} {r[1]:34} {r[3]}")
        return
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(OPEN_COLS)
    for r in rows:
        w.writerow([r[0], r[1], r[2], yaml.safe_dump(r[3], default_flow_style=True).strip().removesuffix("...").strip(), r[4], r[5], r[6]])
    open(a.out, "w", encoding="utf-8", newline="").write(buf.getvalue())
    print("TOOL: fab.py open")


# --------------------------------------------------------------- drawing ----

def dxf_lines(path):
    import ezdxf
    print(f"READ: {path}")
    doc = ezdxf.readfile(os.path.join(ROOT, path))
    segs = []
    for e in doc.modelspace():
        if e.dxftype() == "LINE":
            segs.append(((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))
        elif e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
            pts = [(p[0], p[1]) for p in (e.get_points() if e.dxftype() == "LWPOLYLINE" else e.points())]
            if e.closed:
                pts.append(pts[0])
            segs += list(zip(pts, pts[1:]))
    return segs


def fmt(v):
    if isinstance(v, (list, tuple)):
        return " / ".join(fmt(x) for x in v)
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".")
    return str(v)


def tol(v):
    lo, hi = v
    return f"+/-{fmt(hi)}" if -lo == hi else f"+{fmt(hi)} / {fmt(lo)}"


def cmd_drawing(a):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    part = a.part
    P = PARTS[part]
    G = geom()[part]
    b = body()
    fb = b["fabrication"]
    B = bom()
    opens = [r for r in open_figures() if r[0] == part]
    st = G["stock"]
    metal = P["stock"] == "metal"

    fig = plt.figure(figsize=(16.54, 11.69))   # A3 landscape, inches
    fig.patch.set_facecolor("white")
    # ---- plan view
    ax = fig.add_axes([0.03, 0.47, 0.94, 0.47])
    ax.set_aspect("equal")
    ax.axis("off")
    colours = ["#1f4e9c", "#b5651d", "#2e8b57", "#8b2e8b", "#c0392b", "#7f8c8d"]
    through = [l for l in G["layers"] if l["depth"] == "through"]
    feats = [l for l in G["layers"] if l["depth"] != "through"]
    outline = []
    for l in through:
        segs = dxf_lines(l["dxf"])
        outline += segs
        l["colour"] = "black"
        ax.add_collection(LineCollection(segs, colors="black", linewidths=0.8))
    for i, l in enumerate(feats):
        l["colour"] = colours[i % len(colours)]
        ax.add_collection(LineCollection(dxf_lines(l["dxf"]), colors=l["colour"], linewidths=0.7,
                                         linestyles="--" if l["face"] == st["faces"][0] else "-"))
    # overall dimensions: the cut outline's extent, and where it sits in the frame
    xs = [p[0] for sg in outline for p in sg]
    ys = [p[1] for sg in outline for p in sg]
    x0_, x1_, y0_, y1_ = min(xs), max(xs), min(ys), max(ys)
    X, Y = x1_, y1_
    off = max(X, Y) * 0.04
    ax.annotate("", (x0_, y0_ - off), (x1_, y0_ - off), arrowprops=dict(arrowstyle="<->", lw=0.7))
    ax.text((x0_ + x1_) / 2, y0_ - off * 1.25, f"{fmt(x1_ - x0_)}" + (f"  (X {fmt(x0_)} to {fmt(x1_)})" if x0_ else ""),
            ha="center", va="top", fontsize=9)
    ax.annotate("", (x0_ - off, y0_), (x0_ - off, y1_), arrowprops=dict(arrowstyle="<->", lw=0.7))
    ax.text(x0_ - off * 1.25, (y0_ + y1_) / 2, f"{fmt(y1_ - y0_)}" + (f"  (Y {fmt(y0_)} to {fmt(y1_)})" if y0_ else ""),
            ha="right", va="center", fontsize=9, rotation=90)
    ax.plot([0], [0], marker="+", color="red", ms=10)
    ax.text(0, 0, "  0,0", color="red", fontsize=7, va="bottom")
    holes = sorted(G["holes"], key=lambda h: (h["what"], h["x"], h["y"]))
    for n, h in enumerate(holes, 1):
        h["id"] = f"H{n}"
        ax.text(h["x"] + h["d"] / 2 + 0.6, h["y"] + h["d"] / 2 + 0.3, h["id"], fontsize=6.5, color="#c0392b")
    ax.set_xlim(-off * 3, X + off)
    ax.set_ylim(-off * 3, Y + off)
    view = {"plate_top": "seen from above (top face up); X along the body from the mouth end, Y across",
            "plate_bottom": "seen from above (top face up, the studs' heads in the underside, away from the viewer)",
            "oak_top": "seen from above (playing face up); dashed = cut from the underside",
            "oak_bottom": "seen from above (inside face up, outside face away); dashed = cut from the outside face",
            "mouth_cap": "seen from outside the body; X across the body, Y up",
            "tail_cap": "seen from INSIDE the body (the DXF's frame); X across the body, Y up; the recess is cut from the outer face"}[part]
    fig.text(0.03, 0.955, f"{P['title']} - plan, {view}", fontsize=10)
    fig.text(0.03, 0.975, f"WOODY CONTROLLER BODY  |  {P['title'].upper()}  |  rev {fb['revision']['value']}",
             fontsize=15, weight="bold")

    # ---- tables
    def table(x, y, title, head, rows, widths, size=7.2, colours=None):
        fig.text(x, y, title, fontsize=9, weight="bold")
        y -= 0.016
        cx = x
        for h, w in zip(head, widths):
            fig.text(cx, y, h, fontsize=size, weight="bold")
            cx += w
        for i, r in enumerate(rows):
            y -= 0.0135
            cx = x
            for c, w in zip(r, widths):
                fig.text(cx, y, str(c), fontsize=size, family="monospace" if c is r[0] else None,
                         color=colours[i] if colours and c is r[0] else "black")
                cx += w
        return y - 0.02

    y = 0.43
    rows = [(h["id"], h["what"], fmt(h["x"]), fmt(h["y"]), fmt(h["d"]),
             "through" if h["depth"] == "through" else f"{fmt(h['depth'])} from {h['face']}",
             (h["bom"] + ": " + B[h["bom"]]["part"])[:60] if h["bom"] else "") for h in holes]
    y = table(0.03, y, "HOLES (part frame, mm)", ["id", "what", "X", "Y", "dia", "depth", "goes in it (hardware/bom.csv)"],
              rows, [0.03, 0.12, 0.04, 0.035, 0.035, 0.09, 0.2])
    drows = [(l["face"] or "-", fmt(l["depth"]) if l["depth"] != "through" else "through", l["what"], l["dxf"]) for l in G["layers"]]
    y = table(0.03, y, "CUTS AND DEPTH (one file per layer; depths from the face named)", ["face", "depth", "what", "file"],
              drows, [0.07, 0.05, 0.17, 0.25], colours=[l["colour"] for l in G["layers"]])

    # ---- notes, right column
    x0 = 0.60
    notes = []
    if metal:
        notes.append(f"MATERIAL: {fb['plate_alloy']['value']}, {fmt(plate_thickness())} thick "
                     f"(config/key-layout.yaml plate_thickness = register `plate-thickness`)")
        notes.append(f"FINISH: {fb['plate_finish']['value']} (config/body.yaml fabrication.plate_finish)")
        notes.append(f"PROFILE TOL {tol(fb['plate_profile_tol']['value'])}; SWITCH CUTOUTS "
                     f"{fmt(G['cutouts']['n'])} x {fmt(G['cutouts']['s'])} square {tol(fb['cutout_tol']['value'])} "
                     f"(fabrication.cutout_tol); sharp corners not required: the DXF's own")
        if part == "plate_bottom":
            studs = [h for h in holes if h["bom"] == "MECH-MB-STUD"]
            notes.append(f"PEM STUDS: {len(studs)} x {B['MECH-MB-STUD']['part']} ({B['MECH-MB-STUD']['manufacturer']}), "
                         f"pressed in from the UNDERSIDE, heads flush in it, shanks standing from the top face. "
                         f"Holes {', '.join(h['id'] for h in studs)}: {fmt(studs[0]['d'])} {tol(fb['stud_hole_tol']['value'])} "
                         f"(hardware.stud_hole), punched or drilled, NOT DEBURRED; >= hardware.stud_edge from any edge; "
                         f"squeezed flush on a flat anvil, never hammered (BOM MECH-MB-STUD)")
        else:
            notes.append("NO PRESSED HARDWARE in this plate. The column screws' heads bear on its top face (BOM MECH-COL-SCREW)")
        notes.append("COUNTERSINKS: none. Every hole is a plain through-hole")
        notes.append("GROUND: bare metal round every hole that carries a screw head or a stud (ADR 0025)")
    else:
        notes.append(f"MATERIAL: {fb['wood_species']['value']} - status {fb['wood_species']['status']} "
                     f"(config/body.yaml fabrication.wood_species)")
        notes.append(f"STOCK THICKNESS: {fmt(st['t'])}, finished (fab-geometry.echo; "
                     + ("the flush rule: switch.keycap_top_above_seat - switch.total_travel" if part.startswith("oak")
                        else f"ends.{part}_t") + ")")
        notes.append(f"FINISH: {fb['wood_finish']['value']} (fabrication.wood_finish)")
        notes.append(f"TOL: profile {tol(fb['wood_profile_tol']['value'])}, depths {tol(fb['wood_depth_tol']['value'])} "
                     f"(fabrication.wood_*_tol); holes for hardware to the hardware's own fit, below")
        for ref in ("MECH-MX-INSERT", "INLET-INSERT"):
            ins = [h for h in holes if h["bom"] == ref]
            if ins:
                r = B[ref]
                notes.append(f"THREADED INSERTS {', '.join(h['id'] for h in ins)}: {len(ins)} x {r['part']} "
                             f"({r['manufacturer']}, BOM {ref}) - {r['description']}")
        if part == "mouth_cap":
            notes.append("TAP the inlet hole to the insert's outside thread (BOM INLET-INSERT), square to the face, "
                         "before the insert is epoxied in flush with the outer face")
        if part == "tail_cap":
            notes.append("etherCON recess: a router pass from the outer face, tail-cap-recess.dxf, leaving the "
                         "connector its panel (config/body.yaml ethercon.panel_max)")
        notes.append("COUNTERSINKS: none. Pockets and counterbores are flat-bottomed")
        notes.append(f"EDGES: the model's sanded roundover, stack.edge_r = {fmt(b['stack']['edge_r']['value'])} "
                     f"({b['stack']['edge_r']['status']}), is in the STEP; it may be left for sanding by hand")
    notes.append(f"QTY PER INSTRUMENT: 1  |  BOM {P['bom']}: {B[P['bom']]['part']} ({B[P['bom']]['status']})")
    fig.text(x0, 0.43, "NOTES", fontsize=9, weight="bold")
    import textwrap
    yy = 0.413
    for n_ in notes:
        for k, ln in enumerate(textwrap.wrap(n_, 92)):
            fig.text(x0, yy, ("- " if k == 0 else "  ") + ln, fontsize=7.2)
            yy -= 0.0128
        yy -= 0.003

    yy -= 0.01
    blocking = [r for r in opens if r[5] == "yes"]
    for ln in textwrap.wrap(f"OPEN FIGURES this part depends on: {len(blocking)} tbd, so blocking, of {len(opens)} "
                            f"tbd or nominal (each with what decides it: mechanical/fab/open-figures.csv)", 80):
        fig.text(x0, yy, ln, fontsize=8.5, weight="bold", color="#c0392b" if blocking else "#2e7d32")
        yy -= 0.014
    line = ", ".join(r[1] for r in blocking) or "none - every figure it depends on is settled or a working estimate"
    for ln in textwrap.wrap(line, 100):
        fig.text(x0, yy, ln, fontsize=7, family="monospace")
        yy -= 0.012

    # ---- title block
    fp = a.fingerprint
    files = sorted({l["dxf"] for l in G["layers"]})
    stem = os.path.splitext(os.path.basename(a.out))[0]
    fig.text(0.03, 0.035, f"Files: {', '.join(os.path.basename(f) for f in files)}"
                          + ("" if metal else f"; 3D: mechanical/fab/{stem}.step (and .stl)"),
             fontsize=7.5)
    fig.text(0.03, 0.02, f"Units mm. Not to scale: the cut files govern. Woody body · {a.name} · cad {fp[:12]} · "
                         f"verify: python3 tools/cad.py explain {a.name}", fontsize=7.5, color="#444")
    fig.text(0.03, 0.006, f"Generated by tools/fab.py from {GEOM}, the DXFs, {BODY} and {BOM}; never edit by hand.",
             fontsize=6.5, color="#666")
    fig.savefig(a.out, format="pdf", metadata={"CreationDate": None, "ModDate": None, "Producer": None,
                                               "Creator": "tools/fab.py", "Title": f"Woody {P['title']} rev {fb['revision']['value']}"})
    print(f"TOOL: fab.py drawing; matplotlib {matplotlib.__version__}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("step")
    s.add_argument("--stl", required=True)
    d = sub.add_parser("drawing")
    d.add_argument("--part", required=True, choices=sorted(PARTS))
    o = sub.add_parser("open")
    o.add_argument("--print", action="store_true")
    for p in (s, d, o):
        p.add_argument("--name", default="")
        p.add_argument("--out")
        p.add_argument("--fingerprint", default="")
    a = ap.parse_args()
    if a.cmd != "open" or not a.print:
        if not a.out:
            ap.error("--out is required")
    {"step": cmd_step, "drawing": cmd_drawing, "open": cmd_open}[a.cmd](a)


if __name__ == "__main__":
    main()
