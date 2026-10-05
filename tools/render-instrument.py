#!/usr/bin/env python3
"""
The instrument, rendered in Blender (Cycles) - the photographs of the
controller: the shell, the cassette (ADR 0025) and the REAL boards, with their
parts and copper. Run by `python3 tools/cad.py build`, which ledgers and
stamps them; never by hand into mechanical/renders/.

    python3 tools/render-instrument.py --view <view> --out <png> [--preview]
    python3 tools/render-instrument.py --prepare      # export the solids and boards only

Blender is a Python module here (`import bpy`, bpy 5.0), as in
tools/render-module.py, whose studio probe, Cycles settings and stamp this
follows. `--preview` renders at a quarter of the pixels and few samples, for
iterating on a view; cad.py never passes it.

WHERE THE GEOMETRY COMES FROM - nothing is modelled twice:

  the shell, the cassette's metal,   mechanical/cad/woody_body.scad, ONE STL PER NAMED
  keycaps, Matrix, tail equipment    SOLID (P(c, shell, id) - the clash check's inventory),
                                     exported with OpenSCAD's `only=<id>` as it is
                                     assembled (explode = 0). ~50 s of model evaluation
                                     each, so they are cached under ~/.cache/woody/,
                                     keyed by the git blob id of every file OpenSCAD
                                     reads - the cache can be stale only if the
                                     fingerprint is
  the main board, the key boards     their .kicad_pcb, exported by kicad-cli as GLB with
                                     every component's 3D model, the copper, pads, mask
                                     and silkscreen. The body CAD's frame and the PCB's
                                     are tools/pcb.py's (pcb x = body x + OX, pcb y =
                                     OY - body y), so `--user-origin OX x OY` puts a
                                     board in body coordinates; its height is the body
                                     CAD's own solid for that board, and the two outlines
                                     must agree in plan (checked, below: a board in the
                                     wrong place fails the render rather than shows it)
  mask, silk and finish colours      each board's layout.yaml `fab:` (mask, silk, finish)
  the parts' colours                 each part's own 3D model, rewritten for the export by
                                     tools/lib-models.py --assembly (kicad-cli drops the
                                     colours otherwise: coloured_models); a part that still
                                     arrives uncoloured fails the render. How each colour is
                                     surfaced - metal, epoxy, ceramic - is PART_FINISH
  explode distances                  config/render.yaml (picture conventions)

The CAD solids a board export REPLACES - its own envelope, the parts envelopes,
the switches the boards carry, the connectors on them, the LED row's envelope -
are not drawn (BOARD_OWNS). What remains of the CAD is everything no board
file holds: oak, plates, columns, the U-bolt, keycaps, the IDC plugs and
ribbons, the Matrix, the etherCON and its adapter, USB-C, the breath tube.

WHAT IT READS (each printed as `READ:`, cross-checked by cad.py): config/render.yaml;
mechanical/cad/woody_body.scad and every file it reads (also cross-checked against
OpenSCAD's own depfile); each board's .kicad_pcb, layout.yaml and every in-repository
3D model it names; mechanical/module/blender/studio_small_08_1k.hdr; and
branding/export/spec.json + branding/build.py, through cad.branding(), for the
maker's mark's epoxy colours (`EPOXY`, branding/README.md 'Colour fill').

Numbers below that are not read from those files are PICTURE conventions -
cameras, lights, colours, the wood's figure - and are named as such.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import cad  # noqa: E402  (scad_deps, blob_id: the same walk the fingerprint uses)

CONFIG = "config/render.yaml"
SCAD = "mechanical/cad/woody_body.scad"
HDRI = "mechanical/module/blender/studio_small_08_1k.hdr"
BOARDS = {   # board directory -> the body CAD solid that is the same board
    "main-board": "main board",
    "key-board-lh": "board left_hand",
    "key-board-rh": "board right_hand",
}
OX, OY = 60.0, 150.0          # tools/pcb.py: pcb x = body x + OX, pcb y = OY - body y
CACHE = os.path.expanduser("~/.cache/woody")
EXPORT_RECIPE = "1"           # bump when how the solids or boards are exported changes

# The CAD solids a board's own export replaces (fnmatch patterns on the solid id).
BOARD_OWNS = ["main board", "board left_hand", "board right_hand", "parts *", "tall parts main board",
              "tails *", "LED row", "breath sensor", "switch *", "J-CHAIN *", "J-MCU", "J-UMB"]
# Never drawn: a volume, not a part (the switch's travel envelope).
NOT_PARTS = ["travel *"]


def rd(p):
    print(f"READ: {p}", flush=True)
    return os.path.join(ROOT, p)


def cfg_value(cfg, dotted):
    node = cfg
    for k in dotted.split("."):
        node = node[k]
    return node["value"]


def fnm(sid, pats):
    import fnmatch
    return any(fnmatch.fnmatchcase(sid, p) for p in pats)


# ------------------------------------------------------------ the solids ----

def scad_inputs():
    deps = sorted(cad.scad_deps(SCAD))
    for p in deps:
        rd(p)
    return deps


def solids_dir(deps):
    r = subprocess.run(["openscad", "--version"], capture_output=True, text=True)
    h = hashlib.sha256(f"{EXPORT_RECIPE}\n{(r.stdout + r.stderr).strip()}\n".encode())
    for p in deps:
        h.update(f"{p}\0{cad.blob_id(p)}\n".encode())
    return os.path.join(CACHE, "instrument-solids", h.hexdigest()[:16])


def safe(sid):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", sid)


def export_solids(deps, jobs):
    """Every named solid of the assembly as its own STL, in the model's frame
    (mm, X from the mouth face). Resumable: a solid already exported is kept."""
    d = solids_dir(deps)
    index = os.path.join(d, "index.json")
    if os.path.exists(index):
        return d, json.load(open(index))
    os.makedirs(d, exist_ok=True)
    base = ["-D", "explode=0", "-D", 'cut="none"', "-D", "ghost_shell=false", "-D", 'origin="mouth"']
    with tempfile.TemporaryDirectory() as td:
        echo, dep = os.path.join(td, "ids.echo"), os.path.join(td, "deps")
        r = subprocess.run(["openscad", "-o", echo, "-d", dep] + base + ["-D", "list_solids=true", rd(SCAD)],
                           capture_output=True, text=True, cwd=ROOT)
        if r.returncode:
            raise SystemExit(f"render-instrument: could not list the solids:\n{r.stderr[-2000:]}")
        # OpenSCAD's own record of what it read, against the walk the fingerprint uses
        txt = open(dep).read().replace("\\\n", " ")
        seen = {cad.rel(p if os.path.isabs(p) else os.path.join(ROOT, p)) for p in txt.split(":", 1)[1].split()}
        missed = sorted(p for p in seen if p not in deps and not p.startswith(".."))
        if missed:
            raise SystemExit(f"render-instrument: OpenSCAD read {missed}, which cad.scad_deps() did not find")
        ids = []
        for line in open(echo):
            m = re.match(r'ECHO: "SOLID", "(.*)"$', line.strip())
            if m and m.group(1) not in ids:
                ids.append(m.group(1))
    # a solid a board's export replaces is exported only if it is the board itself (its outline and height place the export)
    want = [s for s in ids if not fnm(s, NOT_PARTS) and (not fnm(s, BOARD_OWNS) or s in BOARDS.values())]
    print(f"render-instrument: {len(want)} solids to export into {d}", flush=True)

    def one(sid):
        out = os.path.join(d, safe(sid) + ".stl")
        if os.path.exists(out):
            return sid, "kept"
        tmp = out + ".part.stl"
        r = subprocess.run(["openscad", "-o", tmp] + base + ["-D", f"only={json.dumps(sid)}", os.path.join(ROOT, SCAD)],
                           capture_output=True, text=True, cwd=ROOT)
        if r.returncode or not os.path.exists(tmp):
            return sid, "empty" if "empty" in (r.stdout + r.stderr).lower() else (r.stdout + r.stderr)[-600:]
        os.replace(tmp, out)
        return sid, "ok"

    done = {}
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for n, (sid, res) in enumerate(ex.map(one, want), 1):
            if res not in ("ok", "kept", "empty"):
                raise SystemExit(f"render-instrument: solid {sid!r} failed:\n{res}")
            done[sid] = None if res == "empty" else safe(sid) + ".stl"
            print(f"  [{n}/{len(want)}] {sid}: {res}", flush=True)
    json.dump(done, open(index, "w"), indent=1)
    return d, done


# ------------------------------------------------------------ the boards ----

def kicad_env():
    env = dict(os.environ)
    env.setdefault("KICAD9_3DMODEL_DIR", "/usr/share/kicad/3dmodels")
    env.setdefault("KICAD9_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
    return env


def board_inputs(name):
    """The board file, its fab spec, and every in-repository 3D model it names."""
    bdir = f"hardware/boards/{name}"
    pcb = f"{bdir}/{name}.kicad_pcb"
    ins = [pcb, f"{bdir}/layout.yaml"]
    for m in sorted(set(re.findall(r'\(model "([^"]+)"', open(os.path.join(ROOT, pcb)).read()))):
        p = m.replace("${KIPRJMOD}", bdir)
        if "${" in p:
            continue          # a KiCad library model: outside the repository, as tools/pcb.py renders it
        p = os.path.normpath(p)
        if not os.path.exists(os.path.join(ROOT, p)):
            raise SystemExit(f"render-instrument: {pcb} names {m}, which does not exist - "
                             f"run tools/setup-env.sh (tools/lib-models.py)")
        ins.append(p)
    for p in ins:
        rd(p)
    return ins


LIB_MODELS = "tools/lib-models.py"


def coloured_models(name, pcb_text, env):
    """Every 3D model the board names, as an ASSEMBLY of coloured parts, cached by the
    model's own bytes: {the board's model string: the file to export with}.

    WHY. kicad-cli's GLB export (KiCad 9) carries a model's colours only through an
    assembly's components. KiCad's own library models (CadQuery-made: one solid, its
    colours on its faces) arrive in the GLB with no material at all, and Blender draws
    a primitive with no material white: every SOIC, chip resistor, MLCC, electrolytic
    and pin header on the boards was white in these photographs until 2026-10-02.
    tools/lib-models.py --assembly rewrites a model into the shape the export keeps
    (a model that is already one is copied unchanged)."""
    out = {}
    bdir = os.path.join(ROOT, "hardware", "boards", name)
    for m in sorted(set(re.findall(r'\(model "([^"]+)"', pcb_text))):
        p = re.sub(r"\$\{(\w+)\}", lambda g: bdir if g.group(1) == "KIPRJMOD" else env.get(g.group(1), g.group(0)), m)
        p = os.path.normpath(p if os.path.isabs(p) else os.path.join(bdir, p))
        if not os.path.exists(p):
            raise SystemExit(f"render-instrument: {name} names model {m}, which does not exist ({p}) - "
                             f"it would be left out of the photograph")
        h = hashlib.sha256(open(p, "rb").read() + f"\0{cad.blob_id(LIB_MODELS)}".encode()).hexdigest()[:16]
        dst = os.path.join(CACHE, "instrument-models", h, os.path.basename(p))
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            r = subprocess.run([sys.executable, os.path.join(ROOT, LIB_MODELS), "--assembly", p, dst + ".part"],
                               capture_output=True, text=True)
            if r.returncode or not os.path.exists(dst + ".part"):
                raise SystemExit(f"render-instrument: could not recolour {p}:\n{(r.stdout + r.stderr)[-1500:]}")
            os.replace(dst + ".part", dst)
        out[m] = dst
    return out


def uncoloured_parts(glb, pcb_text):
    """The references whose parts came out of the export with a mesh and no material -
    the ones Blender would draw white - or with no mesh at all (a nested assembly the
    export drops). Read from the GLB's own JSON chunk."""
    import struct
    raw = open(glb, "rb").read()
    j = json.loads(raw[20:20 + struct.unpack("<I", raw[12:16])[0]])
    nodes, meshes = j["nodes"], j.get("meshes", [])

    def bare(i):
        n = nodes[i]
        if "mesh" in n and any(p.get("material") is None for p in meshes[n["mesh"]]["primitives"]):
            return True
        return any(bare(c) for c in n.get("children", []))
    def empty(i):
        n = nodes[i]
        return "mesh" not in n and all(empty(c) for c in n.get("children", []))
    refs = set(re.findall(r'\(property "Reference" "([^"]+)"', pcb_text))
    return sorted({n["name"] + (" (no mesh at all)" if empty(i) else "")
                   for i, n in enumerate(nodes) if n.get("name") in refs and (bare(i) or empty(i))})


def export_board(name, ins):
    r = subprocess.run(["kicad-cli", "version"], capture_output=True, text=True)
    h = hashlib.sha256(f"{EXPORT_RECIPE}\n{r.stdout.strip()}\n".encode())
    for p in ins + [LIB_MODELS]:
        h.update(f"{p}\0{cad.blob_id(p)}\n".encode())
    rd(LIB_MODELS)
    d = os.path.join(CACHE, "instrument-boards", h.hexdigest()[:16])
    out = os.path.join(d, name + ".glb")
    if not os.path.exists(out):
        os.makedirs(d, exist_ok=True)
        env = kicad_env()
        txt = open(os.path.join(ROOT, ins[0]), encoding="utf-8").read()
        models = coloured_models(name, txt, env)
        # the board as it is, but every model the recoloured copy: a copy beside the
        # GLB, its model paths absolute (nothing else in it changes)
        tmp_pcb = os.path.join(d, name + ".kicad_pcb")
        open(tmp_pcb, "w", encoding="utf-8").write(
            re.sub(r'\(model "([^"]+)"', lambda g: f'(model "{models[g.group(1)]}"', txt))
        r = subprocess.run(["kicad-cli", "pcb", "export", "glb", "--include-tracks", "--include-pads", "--include-zones",
                            "--include-silkscreen", "--include-soldermask", "--user-origin", f"{OX}x{OY}mm",
                            "-f", "-o", out + ".part.glb", tmp_pcb],
                           capture_output=True, text=True, env=env)
        if r.returncode or not os.path.exists(out + ".part.glb"):
            raise SystemExit(f"render-instrument: kicad-cli could not export {name}:\n{(r.stdout + r.stderr)[-1500:]}")
        bare = uncoloured_parts(out + ".part.glb", txt)
        if bare:
            raise SystemExit(f"render-instrument: {name}: these parts came out of the export with no colour, and "
                             f"would render white: {', '.join(bare)}")
        os.replace(out + ".part.glb", out)
    return out


def prepare(jobs):
    rd(CONFIG)
    deps = scad_inputs()
    boards = {}
    for name in BOARDS:
        boards[name] = export_board(name, board_inputs(name))
    rd(HDRI)
    sdir, solids = export_solids(deps, jobs)
    return sdir, solids, boards


# ---------------------------------------------------------------- groups ----
# Every drawn solid belongs to exactly one group: what moves together in an
# exploded view and what a view hides. "@<board>" is that board's export.
# config/render.yaml names these groups; a group it names that is not here,
# or a solid in no group, fails the render.
GROUPS = {
    "oak top": ["oak top", "matrix window", "logo fill *"],
    "oak bottom": ["oak bottom"],
    "side left": ["side left"],
    "side right": ["side right"],
    "mouth cap": ["mouth cap", "breath inlet insert", "breath inlet barb", "breath inner barb"],
    "tail cap": ["tail cap", "USB-C receptacle"],
    "key plate": ["key plate"],
    "bottom plate": ["bottom plate", "main board stud *"],
    "main board spacers": ["main board spacer *", "U-bolt spacer *"],
    "main board": ["@main-board", "IDC plug * main board", "main board nut *", "breath tube"],
    "thumb caps": ["cap LT*", "cap RT*", "cap socket LT*", "cap socket RT*"],
    "U-bolt": ["U-bolt"],
    "U-bolt nuts": ["U-bolt nut *", "U-bolt washer *"],
    "column standoffs": ["column standoff *"],
    "key boards": ["@key-board-lh", "@key-board-rh", "IDC plug * key board"],
    "key-board spacers": ["key-board spacer *"],
    "keycaps": ["cap LH*", "cap RH*", "cap socket LH*", "cap socket RH*"],
    "column screws": ["column screw *"],
    # the carrier hung from the oak top (#23): its board, HDR-MATRIX, its mounts
    "Matrix": ["Matrix board", "Matrix LEDs", "Matrix underside parts", "Matrix USB-C receptacle", "Matrix harness *",
               "USB-C plug", "Matrix carrier", "Matrix carrier *", "Matrix header *", "J-MCU-C",
               "IDC plug Matrix carrier"],
    "tail equipment": ["etherCON", "umbilical adapter"],
    # flexible runs between groups: drawn assembled, left out of an explode
    "ribbons": ["ribbon *", "Matrix ribbon", "USB-C lead"],
}
SHELL = ["oak top", "oak bottom", "side left", "side right", "mouth cap", "tail cap"]

# The views. Each: the groups it hides, the explode it uses, the camera
# (PICTURE CONVENTIONS: a direction from the subject, a lens, and the box in
# model mm it frames - None frames everything drawn), the picture's size, and
# whether the LED row is lit.
VIEWS = {
    "hero": dict(hide=["ribbons"], explode=None,
                 cam=(-0.62, -1.0, 0.40), lens=60, frame=None, size=(1920, 1080), leds=False),
    # the maker's mark on the oak top (body.yaml logo), from the tail side so it reads upright
    "logo": dict(hide=["ribbons"], explode=None,
                 cam=(0.55, -0.40, 1.0), lens=60, frame=((0, 0, 30), (62, 57, 39)), size=(1920, 1080), leds=False),
    "open": dict(hide=["oak top", "key plate", "side left", "column screws"], explode=None,
                 cam=(-0.45, -1.0, 0.95), lens=60, frame=None, size=(1920, 1080), leds=False),
    "exploded": dict(hide=["ribbons"], explode="explode_instrument",
                     cam=(-0.55, -1.0, 0.38), lens=50, frame=None, size=(1920, 1440), leds=False),
    "cassette": dict(hide=SHELL + ["keycaps", "thumb caps", "Matrix", "tail equipment", "ribbons", "U-bolt nuts"],
                     explode="explode_cassette", cam=(-0.5, -1.0, 0.62), lens=60, frame=None, size=(1920, 1200), leds=False),
    "board-mouth": dict(hide=["oak top", "key plate", "keycaps", "side left", "mouth cap", "column screws", "Matrix"], explode=None,
                        cam=(-0.95, -0.85, 0.42), lens=55, frame=((0, 0, 4), (150, 57, 34)), size=(1920, 1080), leds=True),
    "board-tail": dict(hide=["oak top", "key plate", "keycaps", "side left", "column screws", "key boards", "key-board spacers",
                             "Matrix", "tail cap", "column standoffs", "ribbons"], explode=None,
                       cam=(0.75, -0.95, 0.85), lens=55, frame=((205, 2, 5), (326, 55, 30)), size=(1920, 1080), leds=True),
    "underside": dict(hide=["oak bottom", "ribbons"], explode=None,
                      cam=(-0.35, -0.55, -1.0), lens=50, frame=((100, 0, 0), (326, 57, 39)), size=(1920, 1080), leds=False),
}


def group_of(sid):
    for g, pats in GROUPS.items():
        if fnm(sid, pats):
            return g
    return None


# ------------------------------------------------------------------ scene ----
import bpy          # noqa: E402
import bmesh        # noqa: E402
from mathutils import Vector   # noqa: E402

MM = 0.001


def srgb(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, a)


def principled(name, color, rough, metal=0.0, **kw):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(color) if isinstance(color, str) else color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for k, v in kw.items():
        b.inputs[k].default_value = v
    return m


def nodes(m):
    return m.node_tree.nodes, m.node_tree.links


def brushed(name, color, rough, aniso):
    """Metal brushed along the body (object X): the plates."""
    m = principled(name, color, rough, 1.0, **{"Anisotropic": aniso})
    N, Lk = nodes(m)
    t = N.new("ShaderNodeVectorTransform")
    t.vector_type, t.convert_from, t.convert_to = "VECTOR", "OBJECT", "WORLD"
    t.inputs["Vector"].default_value = (1.0, 0.0, 0.0)
    Lk.new(t.outputs["Vector"], N["Principled BSDF"].inputs["Tangent"])
    # a faint brushing streak in the roughness (object space is mm)
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.02, 4.0, 4.0)
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6.0
    nz.inputs["Detail"].default_value = 6.0
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = rough - 0.06
    mr.inputs["To Max"].default_value = rough + 0.06
    Lk.new(tc.outputs["Object"], mp.inputs["Vector"])
    Lk.new(mp.outputs["Vector"], nz.inputs["Vector"])
    Lk.new(nz.outputs["Fac"], mr.inputs["Value"])
    Lk.new(mr.outputs["Result"], N["Principled BSDF"].inputs["Roughness"])
    return m


def oak(name, along="x"):
    """Oak under a dark stain, satin clearcoat (ADR 0009 'Finishes', 2026-09-28:
    dark, the grain still showing). PICTURE CONVENTION, procedural, in object
    space (mm), deliberately low contrast:
      - fine straight grain: growth rings ~1.1 mm apart round a log axis far
        below the board, so on a face they run as near-straight lines along
        the grain, wandered gently by noise;
      - open pores: thin dark streaks along the grain, rougher than the face;
      - medullary rays: short, slightly lighter flecks along the grain - the
        figure that tells oak from walnut or ash;
      - on a face across the grain (an end) the same rings read as end grain.
    `along`: the grain's axis - x along the body, y across (the end caps)."""
    m = principled(name, "#2b1f16", 0.42, 0.0, **{"Coat Weight": 0.2, "Coat Roughness": 0.3, "Specular IOR Level": 0.4})
    N, Lk = nodes(m)
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    if along == "y":
        mp.inputs["Rotation"].default_value = (0, 0, math.radians(90))
    Lk.new(tc.outputs["Object"], mp.inputs["Vector"])
    P = mp.outputs["Vector"]

    def op(kind, a, b_=None):
        n = N.new("ShaderNodeMath")
        n.operation = kind
        for i, v in enumerate((a, b_)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                Lk.new(v, n.inputs[i])
        return n.outputs[0]

    def noise(scale_xyz, detail):
        mm = N.new("ShaderNodeMapping")
        mm.inputs["Scale"].default_value = scale_xyz
        Lk.new(P, mm.inputs["Vector"])
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 1.0
        nz.inputs["Detail"].default_value = detail
        Lk.new(mm.outputs["Vector"], nz.inputs["Vector"])
        return nz.outputs["Fac"]

    def band(fac, lo, hi):
        r = N.new("ShaderNodeMapRange")
        r.inputs["From Min"].default_value = lo
        r.inputs["From Max"].default_value = hi
        Lk.new(fac, r.inputs["Value"])
        return r.outputs["Result"]

    def mixc(fac, a, colour):
        n = N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        Lk.new(fac, n.inputs["Factor"])
        Lk.new(a, n.inputs["A"])
        n.inputs["B"].default_value = srgb(colour)
        return n.outputs["Result"]

    sep = N.new("ShaderNodeSeparateXYZ")
    Lk.new(P, sep.inputs["Vector"])
    # rings round a log axis 300 mm below and 20 mm beside: near-straight lines on the face
    yy = op("ADD", sep.outputs["Y"], 20.0)
    zz = op("ADD", sep.outputs["Z"], 300.0)
    r = op("SQRT", op("ADD", op("MULTIPLY", yy, yy), op("MULTIPLY", zz, zz)))
    r = op("ADD", r, op("MULTIPLY", op("SUBTRACT", noise((0.004, 0.05, 0.05), 4.0), 0.5), 6.0))
    ring = op("FRACT", op("DIVIDE", r, 1.1))
    cr = N.new("ShaderNodeValToRGB")
    E = cr.color_ramp.elements
    E[0].position, E[0].color = 0.0, srgb("#140d08")
    E[1].position, E[1].color = 0.22, srgb("#2b1f16")
    E.new(0.78).color = srgb("#302318")
    E.new(1.0).color = srgb("#140d08")
    Lk.new(ring, cr.inputs["Fac"])
    base = cr.outputs["Color"]
    # a slow colour drift across the plank
    base = mixc(op("MULTIPLY", noise((0.01, 0.02, 0.02), 2.0), 0.5), base, "#21170f")
    # pores: fine dark streaks along the grain
    pore = band(noise((0.08, 3.5, 3.5), 1.0), 0.60, 0.72)
    base = mixc(op("MULTIPLY", pore, 0.55), base, "#1a100a")
    # medullary rays: short lighter flecks, long along the grain, thin across, scattered
    vm = N.new("ShaderNodeMapping")
    vm.inputs["Scale"].default_value = (0.35, 2.6, 2.6)
    Lk.new(P, vm.inputs["Vector"])
    vo = N.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 1.0
    Lk.new(vm.outputs["Vector"], vo.inputs["Vector"])
    ray = op("MULTIPLY", band(vo.outputs["Distance"], 0.16, 0.05), band(noise((0.05, 0.4, 0.4), 1.0), 0.48, 0.62))
    base = mixc(op("MULTIPLY", ray, 0.5), base, "#4a3828")
    Lk.new(base, b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.36
    rr.inputs["To Max"].default_value = 0.55
    Lk.new(pore, rr.inputs["Value"])
    Lk.new(rr.outputs["Result"], b.inputs["Roughness"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.04 * MM
    bump.invert = True
    Lk.new(pore, bump.inputs["Height"])
    Lk.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def epoxy(name, rgb):
    """The maker's mark's fill (body.yaml logo.fill): pigmented epoxy poured
    into the etch, sanded flush and finished with the oak, so under the same
    satin clearcoat. The COLOUR is branding's (`EPOXY` in branding/build.py,
    read by cad.branding()); the sheen is a picture convention."""
    return principled(name, "#%02X%02X%02X" % tuple(rgb), 0.30, 0.0, **{"Coat Weight": 0.2, "Coat Roughness": 0.3})


def branding_colours():
    rd(cad.BRANDING_SPEC)
    rd(cad.BRANDING_BUILD)
    return cad.branding()["epoxy"]


class Mats:
    """PICTURE CONVENTIONS, each named for what it stands for."""

    def __init__(self, side_glass, fill):
        self.fill_wave = epoxy("epoxy fill, the mark's wave and moon", fill["wave"])
        self.fill_ring = epoxy("epoxy fill, the mark's ring", fill["ring"])
        self.oak_x = oak("oak, grain along the body")
        self.oak_y = oak("oak, grain across", "y")
        self.alu = brushed("aluminium, brushed", "#C9CBCE", 0.30, 0.55)
        self.steel = principled("stainless", "#B9BABC", 0.28, 1.0)
        self.nickel = principled("nickel", "#CFCDC8", 0.22, 1.0)
        self.zinc = principled("zinc-plated steel", "#AEB2B6", 0.34, 1.0)
        # THE SIDES ARE FROSTED in the instrument (ADR 0009 'Finishes'); these
        # photographs draw them clear on purpose (config/render.yaml render.side_glass)
        if side_glass == "clear-smoke":
            self.side = principled("acrylic, clear smoke (render only)", "#B3B8BE", 0.02, 0.0, **{"Transmission Weight": 1.0, "IOR": 1.49})
        else:
            self.side = principled("frosted acrylic, dark grey", "#4A4D52", 0.48, 0.0, **{"Transmission Weight": 0.7, "IOR": 1.49})
        self.window = principled("frosted acrylic, the Matrix window", "#8A8F94", 0.32, 0.0, **{"Transmission Weight": 0.95, "IOR": 1.49})
        self.keycap = principled("PBT, black", "#141414", 0.62, 0.0, **{"Specular IOR Level": 0.4})
        self.black = principled("black plastic", "#151517", 0.42)
        self.ribbon = principled("ribbon PVC", "#9A9C9F", 0.5)
        self.silicone = principled("silicone tube", "#F2F0EA", 0.35, 0.0, **{"Transmission Weight": 0.6, "IOR": 1.41})
        self.matrix_pcb = principled("Matrix PCB", "#101012", 0.45, 0.0, **{"Coat Weight": 0.4})
        self.matrix_led = principled("5050 LED", "#B9B4A2", 0.3)
        self.adapter = principled("adapter PCB", "#1E5B33", 0.4, 0.0, **{"Coat Weight": 0.4})
        self.floor = principled("floor", "#1d1d20", 0.9, 0.0, **{"Specular IOR Level": 0.25})

    def for_solid(self, sid):
        M = self
        table = [
            (["oak top", "oak bottom"], M.oak_x), (["mouth cap", "tail cap"], M.oak_y),
            (["logo fill wave and moon"], M.fill_wave), (["logo fill ring"], M.fill_ring),
            (["side *"], M.side), (["matrix window"], M.window),
            (["key plate", "bottom plate"], M.alu),
            (["column standoff *"], M.nickel), (["U-bolt"], M.steel),
            (["main board stud *", "main board spacer *", "main board nut *", "key-board spacer *", "column screw *",
              "U-bolt nut *", "U-bolt washer *", "U-bolt spacer *"], M.zinc),
            (["cap *", "cap socket *"], M.keycap),
            (["IDC plug *", "etherCON", "USB-C plug", "USB-C receptacle", "Matrix USB-C receptacle", "Matrix harness *",
              "Matrix header *", "J-MCU-C"], M.black),
            (["ribbon *", "Matrix ribbon", "USB-C lead"], M.ribbon),
            (["breath *"], M.silicone),
            (["Matrix board", "Matrix underside parts", "Matrix carrier"], M.matrix_pcb), (["Matrix LEDs"], M.matrix_led),
            (["Matrix carrier *"], M.zinc),     # its spacers, washers, inserts and screws
            (["umbilical adapter"], M.adapter),
        ]
        for pats, m in table:
            if fnm(sid, pats):
                return m
        raise SystemExit(f"render-instrument: no material for solid {sid!r} - add it to Mats.for_solid")


def tidy_mesh(me, angle=32.0):
    """CGAL's STL: weld it, then shade smooth with every edge sharper than `angle` kept sharp."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = e.is_manifold and e.calc_face_angle(math.pi) < math.radians(angle)
    bm.to_mesh(me)
    bm.free()


def import_solid(path, sid, mat):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=path)
    o = (set(bpy.data.objects) - before).pop()
    o.name = sid
    o.scale = (MM, MM, MM)           # the mesh stays in model mm, so object coordinates are mm (the wood's figure)
    tidy_mesh(o.data)
    o.data.materials.clear()
    o.data.materials.append(mat)
    return o


def world_bbox(objs):
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in objs:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


MASK = {"white": "#F2F2EE", "green": "#1F6B3A", "black": "#121214", "blue": "#1C3E8C", "red": "#9C1F1F",
        "yellow": "#D8B42A", "purple": "#4B2A7A"}   # PICTURE CONVENTION: the mask colours a board house sells, as render colours


def board_materials(name):
    """Mask, silk and finish as the board's fab spec orders them (layout.yaml `fab:`)."""
    fab = yaml.safe_load(open(os.path.join(ROOT, f"hardware/boards/{name}/layout.yaml"), encoding="utf-8")).get("fab") or {}
    mask_c = MASK[str(fab["mask"]).lower()]
    silk_c = MASK[str(fab["silk"]).lower()]
    enig = "enig" in str(fab.get("finish", "")).lower()
    mask = principled(f"{name} mask ({fab['mask']})", mask_c, 0.32, 0.0, **{"Coat Weight": 0.35, "Coat Roughness": 0.18})
    # a thin coat: a little of the copper and laminate under it shows through
    mask.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.88 if mask_c != MASK["black"] else 0.97
    pad = principled(f"{name} pads ({fab.get('finish', '')})", "#E2C27A" if enig else "#D3D4D6", 0.22 if enig else 0.30, 1.0)
    return dict(mask=mask, silk=principled(f"{name} silk ({fab['silk']})", silk_c, 0.6),
                copper=principled(f"{name} copper", "#C9773F", 0.32, 1.0), pad=pad, via=pad,
                pcb=principled(f"{name} FR-4", "#B9A773", 0.55, 0.0))


# PICTURE CONVENTION - PART_FINISH: how a part's own model colour is SURFACED. The
# colour is the model's (KiCad's library models use its generator's few named
# colours; tools/lib-models.py's and the makers' models their own); what a colour
# alone cannot say - that it is metal, epoxy, ceramic - is said here, by the colour
# class the models use for it. First match wins; a colour matching none is a
# plastic at the model's own colour. Nothing here is a design value.
#   (test on linear RGB + alpha,                     what it is,                       colour (None: the model's), roughness, metallic)
PART_FINISH = [
    (lambda r, g, b, a: a < 0.99,                    "translucent plastic (a lens, a housing)", None, 0.25, 0.0),
    (lambda r, g, b, a: abs(r - 0.12) < 0.01 and abs(g - 0.06) < 0.01 and b < 0.05,
                                                     "MLCC ceramic (KiCad's 'brown body')", "#8E6A44", 0.6, 0.0),
    (lambda r, g, b, a: max(r, g, b) < 0.13,         "black epoxy / PBT (IC, header, connector bodies; a resistor's top)", None, 0.55, 0.0),
    (lambda r, g, b, a: r > g > b and max(r, g, b) > 0.6 and (r - b) / r > 0.4, "gold plating (header pins)", None, 0.22, 1.0),
    (lambda r, g, b, a: 0.5 <= max(r, g, b) <= 0.86 and (max(r, g, b) - min(r, g, b)) / max(r, g, b) < 0.15,
                                                     "tin / aluminium (leads, terminations, an electrolytic's can)", None, 0.3, 1.0),
]


def part_finish(m):
    if not (m and m.node_tree and "Principled BSDF" in m.node_tree.nodes) or m.get("woody_finish"):
        return
    bs = m.node_tree.nodes["Principled BSDF"]
    r, g, b, _ = bs.inputs["Base Color"].default_value
    a = bs.inputs["Alpha"].default_value
    for test, what, colour, rough, metal in PART_FINISH:
        if test(r, g, b, a):
            if colour:
                bs.inputs["Base Color"].default_value = srgb(colour)
            bs.inputs["Roughness"].default_value = rough
            bs.inputs["Metallic"].default_value = metal
            m["woody_finish"] = what
            return
    bs.inputs["Roughness"].default_value = max(bs.inputs["Roughness"].default_value, 0.4)
    bs.inputs["Metallic"].default_value = 0.0
    m["woody_finish"] = "plastic"


def led_refs(name):
    txt = open(os.path.join(ROOT, f"hardware/boards/{name}/{name}.kicad_pcb"), encoding="utf-8").read()
    refs = []
    for blk in re.split(r"\n\t\(footprint ", txt)[1:]:
        if "WS2815" in blk.split("\n", 1)[0]:
            m = re.search(r'\(property "Reference" "([^"]+)"', blk)
            if m:
                refs.append(m.group(1))
    return refs


def import_board(name, glb):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    new = set(bpy.data.objects) - before
    root = bpy.data.objects.new(f"@{name}", None)
    bpy.context.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    bm = board_materials(name)
    body = []
    for o in new:
        if o.type != "MESH":
            continue
        layer = o.data.name.split(".")[0]          # kicad-cli names the board's layers in the mesh, not the node
        if layer.startswith(name + "_"):
            key = layer[len(name) + 1:]
            o.data.materials.clear()
            o.data.materials.append(bm[{"soldermask": "mask", "silkscreen": "silk", "PCB": "pcb"}.get(key, key)])
            body.append(o)          # the laminate with its copper, mask and silk: the board as the CAD draws it
        else:
            for m in o.data.materials:      # the parts' own STEP colours, as surfaces (PART_FINISH)
                part_finish(m)
    if not any(o.data.name.startswith(name + "_PCB") for o in body):
        raise SystemExit(f"render-instrument: {name}'s export has no board body ({name}_PCB)")
    return root, body


def led_glow(root, name, lit):
    """The WS2815s: each LED's lens is the yellowish material of its model. Lit,
    each glows its own colour along the row (PICTURE CONVENTION: a soft
    teal-to-violet sweep), so the row reads as RGB."""
    import colorsys
    refs = led_refs(name)
    objs = {o.name.split(".")[0]: o for o in root.children_recursive}
    xs = sorted((objs[r].matrix_world.translation.x, r) for r in refs if r in objs)
    if len(xs) != len(refs):
        raise SystemExit(f"render-instrument: {name}: {len(refs)} WS2815s on the board, {len(xs)} in its export")
    lenses = 0
    for i, (_, r) in enumerate(xs):
        for c in objs[r].children_recursive:
            if c.type != "MESH" or not c.data.materials or c.data.materials[0] is None:
                continue
            col = c.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value
            if not (col[0] > 0.8 and col[2] < col[0] - 0.15):
                continue
            rgb = colorsys.hsv_to_rgb(0.48 + 0.30 * i / max(1, len(xs) - 1), 0.85, 1.0)
            kw = {"Emission Color": (*rgb, 1.0), "Emission Strength": 7.0} if lit else {"Transmission Weight": 0.5}
            c.data.materials.clear()
            c.data.materials.append(principled(f"LED {r}", (0.9, 0.9, 0.85, 1.0), 0.15, 0.0, **kw))
            lenses += 1
    if lenses != len(xs):
        raise SystemExit(f"render-instrument: {name}: found {lenses} LED lenses for {len(xs)} LEDs")
    return len(xs)


# ------------------------------------------------------------------ build ----

def build(view, sdir, solids, boards):
    V = VIEWS[view]
    cfg = yaml.safe_load(open(os.path.join(ROOT, CONFIG), encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    M = Mats(cfg_value(cfg, "render.side_glass"), branding_colours())

    members = {g: [] for g in GROUPS}
    drawn = {}
    for sid, fn in solids.items():
        if fn is None:
            continue
        g = group_of(sid)
        if g is None and not fnm(sid, BOARD_OWNS):
            raise SystemExit(f"render-instrument: solid {sid!r} is in no group - add it to GROUPS (or BOARD_OWNS)")
        if fnm(sid, BOARD_OWNS):
            continue
        if g in V["hide"]:
            continue
        o = import_solid(os.path.join(sdir, fn), sid, M.for_solid(sid))
        members[g].append(o)
        drawn[sid] = o

    # THE BOARDS, placed where the body CAD puts them: plan by the shared frame
    # (tools/pcb.py), height by the CAD's own solid for the board - and the two
    # outlines must agree in plan, or this is the wrong board in the wrong place.
    import trimesh
    nleds = 0
    for name, glb in boards.items():
        g = group_of("@" + name)
        if g in V["hide"]:
            continue
        cad_board = trimesh.load(os.path.join(sdir, solids[BOARDS[name]]), force="mesh").bounds
        root, body = import_board(name, glb)
        bpy.context.view_layer.update()
        lo, hi = world_bbox(body)
        lo, hi = lo / MM, hi / MM
        off = [abs(lo[i] - cad_board[0][i]) for i in (0, 1)] + [abs(hi[i] - cad_board[1][i]) for i in (0, 1)]
        if max(off) > 0.05:
            raise SystemExit(f"render-instrument: {name}'s outline in plan is [{lo[0]:.2f}..{hi[0]:.2f}] x [{lo[1]:.2f}..{hi[1]:.2f}] mm, "
                             f"the body CAD's '{BOARDS[name]}' is [{cad_board[0][0]:.2f}..{cad_board[1][0]:.2f}] x "
                             f"[{cad_board[0][1]:.2f}..{cad_board[1][1]:.2f}] - the board and the CAD disagree")
        th_pcb, th_cad = hi[2] - lo[2], cad_board[1][2] - cad_board[0][2]
        # kicad-cli lays the mask and silk as faces a few hundredths proud of the laminate
        if abs(th_pcb - th_cad) > 0.1:
            raise SystemExit(f"render-instrument: {name} is {th_pcb:.2f} mm thick, the body CAD's board {th_cad:.2f}")
        root.location.z = ((cad_board[0][2] + cad_board[1][2]) - (lo[2] + hi[2])) / 2 * MM   # mid-planes together
        print(f"render-instrument: {name} at z {cad_board[0][2]:.2f} mm, plan agrees with the body CAD to {max(off):.3f} mm", flush=True)
        if name == "main-board":
            nleds = led_glow(root, name, V["leds"])
        members[g].append(root)

    # the explode (config/render.yaml), every group it names checked against GROUPS
    if V["explode"]:
        for g, dx, dy, dz in cfg_value(cfg, "render." + V["explode"]):
            if g not in GROUPS:
                raise SystemExit(f"render-instrument: {CONFIG} render.{V['explode']} names group {g!r}, which GROUPS does not have")
            for o in members[g]:
                o.location += Vector((dx, dy, dz)) * MM
        moved = {g for g, *_ in cfg_value(cfg, "render." + V["explode"])}
        for g in members:
            if members[g] and g not in moved and g not in V["hide"]:
                raise SystemExit(f"render-instrument: view {view} explodes but {CONFIG} render.{V['explode']} leaves group {g!r} where it is")
    bpy.context.view_layer.update()
    return sc, members, nleds


def cyc(c, z, fwd, mat, R=1.0, reach=8.0, wide=14.0, back=3.0):
    """PICTURE CONVENTION: a studio sweep - the floor under the subject curving
    up (radius R) into a wall `reach` beyond it, square to the camera's
    heading, so the background is seamless."""
    hd = Vector((fwd.x, fwd.y, 0)).normalized()
    side = Vector((-hd.y, hd.x, 0))
    prof = [(-reach, 0.0)] + [(back + R * math.sin(t * math.pi / 32), R - R * math.cos(t * math.pi / 32)) for t in range(17)] + [(back + R, reach)]
    bm = bmesh.new()
    rows = []
    for u in (-wide / 2, wide / 2):
        rows.append([bm.verts.new(Vector((c.x, c.y, z)) + side * u + hd * a + Vector((0, 0, h))) for a, h in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new("cyc")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("cyc", me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(mat)


def setup(sc, members, view, preview):
    V = VIEWS[view]
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.03 if preview else 0.012
    sc.cycles.samples = 24 if preview else 160
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 8
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 6
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.seed = 0
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = -0.3 if V["leds"] else 0.3
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    sc.render.film_transparent = False
    sc.render.resolution_x, sc.render.resolution_y = V["size"]
    sc.render.resolution_percentage = 50 if preview else 100

    objs = [o for g in members.values() for top in g for o in [top] + list(top.children_recursive)]
    lo, hi = world_bbox(objs)
    c = (lo + hi) / 2
    size = (hi - lo).length

    # the world: the studio probe for light and reflections; a plain dark grey behind
    wd = bpy.data.worlds.new("studio")
    sc.world = wd
    N, Lk = wd.node_tree.nodes, wd.node_tree.links
    env = N.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(ROOT, HDRI))
    mp = N.new("ShaderNodeMapping")
    tc = N.new("ShaderNodeTexCoord")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(200))
    Lk.new(tc.outputs["Generated"], mp.inputs["Vector"])
    Lk.new(mp.outputs["Vector"], env.inputs["Vector"])
    probe = N.new("ShaderNodeBackground")
    probe.inputs["Strength"].default_value = 0.08 if V["leds"] else 0.6 if V["cam"][2] < 0 else 0.25
    Lk.new(env.outputs["Color"], probe.inputs["Color"])
    plain = N.new("ShaderNodeBackground")
    plain.inputs["Color"].default_value = srgb("#2a2a2d")
    plain.inputs["Strength"].default_value = 1.0
    lp = N.new("ShaderNodeLightPath")
    mix = N.new("ShaderNodeMixShader")
    Lk.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    Lk.new(probe.outputs["Background"], mix.inputs[1])
    Lk.new(plain.outputs["Background"], mix.inputs[2])
    Lk.new(mix.outputs["Shader"], N["World Output"].inputs["Surface"])

    def area(name, off, power, color, sz, sz_y=None):
        L = bpy.data.lights.new(name, "AREA")
        L.shape = "RECTANGLE"
        L.size = sz
        L.size_y = sz_y or sz
        L.energy = power
        L.color = color
        o = bpy.data.objects.new(name, L)
        o.visible_camera = False          # the softboxes light the subject; they are not in the picture
        sc.collection.objects.link(o)
        o.location = c + Vector(off)
        o.rotation_euler = (c - o.location).normalized().to_track_quat("-Z", "Y").to_euler()
    # picture: a big soft key from the upper front-left, a cool rim from behind,
    # a warm low fill, and a strip overhead to draw a highlight along the oak
    k = 0.25 if V["leds"] else 1.0
    area("key", (-0.30, -0.40, 0.55), 20 * k, (1.0, 0.96, 0.92), 0.6)
    area("rim", (0.5, 1.6, 1.1), 20 * k, (0.85, 0.92, 1.0), 0.3, 0.9)
    area("fill", (0.35, -0.55, -0.05 if V["cam"][2] > 0 else -0.35), 3 * k, (1.0, 0.93, 0.86), 0.7)
    area("top", (0.0, -0.10, 0.55), 6 * k, (1, 1, 1), 0.9, 0.15)
    if V["cam"][2] < 0:     # looking up: a big soft panel below for the metal to reflect
        area("under", (0.05, -0.25, -0.45), 45, (1, 0.97, 0.94), 1.4, 0.6)

    # the floor, under the lowest part, unless the camera looks up at it
    if V["cam"][2] > 0:
        cyc(c, lo.z - 0.002, -Vector(V["cam"]).normalized(), bpy.data.materials["floor"])

    cam = bpy.data.cameras.new("cam")
    co = bpy.data.objects.new("cam", cam)
    sc.collection.objects.link(co)
    sc.camera = co
    cam.sensor_width = 36.0
    cam.lens = V["lens"]
    cam.clip_start = 0.005
    if V["frame"]:
        flo, fhi = Vector(V["frame"][0]) * MM, Vector(V["frame"][1]) * MM
    else:
        flo, fhi = lo, hi
    tgt = (flo + fhi) / 2
    d = Vector(V["cam"]).normalized()
    fwd = -d
    right = fwd.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(fwd).normalized()
    W, H = V["size"]
    tx = math.tan(math.atan(18.0 / cam.lens))          # half the sensor width over the lens
    ty = tx * H / W
    margin = 0.90
    dist = 0.0
    for i in range(8):
        p = Vector((flo.x if i & 1 else fhi.x, flo.y if i & 2 else fhi.y, flo.z if i & 4 else fhi.z)) - tgt
        dist = max(dist, p.dot(d) + abs(p.dot(right)) / (tx * margin), p.dot(d) + abs(p.dot(up)) / (ty * margin))
    co.location = tgt + d * dist
    co.rotation_euler = fwd.to_track_quat("-Z", "Y").to_euler()
    cam.clip_end = 100.0          # past the sweep
    return co


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--view", choices=sorted(VIEWS))
    ap.add_argument("--out")
    ap.add_argument("--fingerprint", default="")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--prepare", action="store_true", help="export the solids and boards into the cache, and stop")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--blend", help="also save the scene as a .blend here (for looking at it)")
    ap.add_argument("--percent", type=int, help="resolution percentage (iterating only)")
    ap.add_argument("--samples", type=int, help="samples (iterating only)")
    a = ap.parse_args()
    sdir, solids, boards = prepare(a.jobs)
    if a.prepare:
        return 0
    if not (a.view and a.out):
        ap.error("--view and --out are needed to render")
    sc, members, nleds = build(a.view, sdir, solids, boards)
    setup(sc, members, a.view, a.preview)
    if a.percent:
        sc.render.resolution_percentage = a.percent
    if a.samples:
        sc.cycles.samples = a.samples
    sc.render.filepath = os.path.abspath(a.out)
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
    import time
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"render-instrument: {a.view} rendered in {time.time() - t0:.0f} s", flush=True)
    print(f"TOOL: render-instrument.py; Blender {bpy.app.version_string} (bpy), Cycles {sc.cycles.samples} spp adaptive, OIDN")
    return 0


if __name__ == "__main__":
    sys.exit(main())


