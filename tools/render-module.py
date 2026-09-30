#!/usr/bin/env python3
"""
The Eurorack module, rendered in Blender (Cycles) - the photographic pictures
(ADR 0026). Run by `python3 tools/cad.py build`, which ledgers and stamps them;
never by hand into mechanical/module/renders/.

    python3 tools/render-module.py --view hero|front|detail --out <png> [--preview]

Blender is used as a Python module (`import bpy`, bpy 5.0), so this runs under
plain python3. `--preview` renders at a quarter of the pixels and few samples,
for iterating on the scene; cad.py never passes it.

WHAT IT READS (each printed as `READ:`, cross-checked by cad.py):
    config/module.yaml                       the knob, plug and cable sizes; the texture's roughness
    mechanical/module/export/panel.dxf         the panel's outline and cuts - the mesh is this, extruded
    mechanical/module/export/panel-art.echo    where every part sits, from module.scad
    mechanical/module/art/tex-*.png            the print, from tools/panel-art.py, mapped 1:1
    mechanical/cad/vendor/{ne8fav,ne8mx,pj398sm}.stl   the banked vendor solids, meshed by cad.py
    mechanical/module/blender/studio_small_08_1k.hdr   the studio light probe (Poly Haven, CC0)

WHAT IS MODELLED HERE, not read: the knob (the Thonk 1900h clone, 12 across
the base and 16 tall per config/module.yaml knob.*, fluted, a white line), the
toggle's bushing, nut and lever (NKK's numbers from config toggle.*), the nuts,
the panel screws, the patch plugs and cables, the case's rails, cheek and
neighbouring blank panels. The last are scenery: they are drawn to the
Doepfer A-100 dimensions config/module.yaml already holds, and nothing is
measured off them.

Numbers below that are not read from those files are PICTURE conventions -
camera, lights, colours of scenery, cable routing - and are named as such.
"""
import argparse
import math
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = "config/module.yaml"
DXF = "mechanical/module/export/panel.dxf"
ECHO = "mechanical/module/export/panel-art.echo"
TEX = {k: f"mechanical/module/art/tex-{k}.png" for k in ("albedo", "roughness", "height")}
STL = {k: f"mechanical/cad/vendor/{k}.stl" for k in ("ne8fav", "ne8mx", "pj398sm")}
HDRI = "mechanical/module/blender/studio_small_08_1k.hdr"


def rd(p):
    print(f"READ: {p}", flush=True)
    return os.path.join(ROOT, p)


def cfg_value(cfg, dotted):
    node = cfg
    for k in dotted.split("."):
        node = node[k]
    if "ref" in node:
        path, _, d = node["ref"].partition(":")
        return cfg_value(yaml.safe_load(open(rd(path), encoding="utf-8")), d)
    return node["value"]


def load_echo():
    parts, zones, size = {}, {}, None
    for line in open(rd(ECHO), encoding="utf-8"):
        m = re.match(r'ECHO: "PANEL", (.*)$', line.strip())
        if not m:
            continue
        f = eval("[" + m.group(1).replace("true", "True").replace("false", "False") + "]")
        if f[0] == "size":
            size = f[1:4]
        elif f[0] == "part":
            parts[f[1]] = f[2:]
        elif f[0] == "zone":
            zones[f[1]] = f[2:6]
    return size, parts, zones


# ------------------------------------------------------------------- scene ----
import bpy          # noqa: E402  (after the READ helpers, so a missing bpy fails clearly below)
import bmesh        # noqa: E402
from mathutils import Matrix, Vector, geometry   # noqa: E402

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


def link(m, a, b):
    m.node_tree.links.new(a, b)


def new_obj(name, mesh, parent, mat=None):
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.parent = parent
    if mat is not None:
        if isinstance(mat, (list, tuple)):
            for x in mat:
                o.data.materials.append(x)
        else:
            o.data.materials.append(mat)
    return o


def mesh_from_bm(name, bm, smooth_angle=35.0):
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if e.is_manifold:
            e.smooth = e.calc_face_angle(0) < math.radians(smooth_angle)
        else:
            e.smooth = False
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def lathe(profile, n=128, radial=None, cap_top=True, cap_bot=True):
    """A solid of revolution about the panel frame's z (out of the panel).
    profile: [(r, z)], bottom to top. radial(theta, z, r) -> r, to flute it."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        ring = []
        for i in range(n):
            t = 2 * math.pi * i / n
            rr = radial(t, z, r) if radial else r
            ring.append(bm.verts.new((rr * math.cos(t), rr * math.sin(t), z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_bot:
        bm.faces.new(list(reversed(rings[0])))
    if cap_top:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def box_bm(x0, y0, z0, x1, y1, z1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0), (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    return bm


def prism_bm(loops, z0, z1):
    """Extrude a polygon with holes (loops[0] the outline, the rest holes)
    from z0 to z1: both caps triangulated, the walls quads."""
    bm = bmesh.new()
    top = [[bm.verts.new((x, y, z1)) for x, y in lp] for lp in loops]
    bot = [[bm.verts.new((x, y, z0)) for x, y in lp] for lp in loops]
    # Caps by bmesh's constrained triangle fill, which takes holes as loops of
    # edges; tessellate_polygon left a sliver out between two holes.
    for loopset, flip in ((top, False), (bot, True)):
        edges = [bm.edges.new((lp[i], lp[(i + 1) % len(lp)])) for lp in loopset for i in range(len(lp))]
        res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges, normal=(0, 0, -1 if flip else 1))
    for lt, lb in zip(top, bot):
        n = len(lt)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((lt[i], lt[j], lb[j], lb[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def circle(r, n, a0=0.0):
    return [(r * math.cos(a0 + 2 * math.pi * i / n), r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def hexnut(name, corners_d, h, hole, rig, mat):
    """A hex nut, across corners `corners_d`, bored `hole`, its edges chamfered."""
    o = new_obj(name, mesh_from_bm("nut", prism_bm([circle(corners_d / 2, 6, math.pi / 6), circle(hole / 2, 64)], 0, h)), rig, mat)
    b = o.modifiers.new("chamfer", "BEVEL")
    b.width = 0.25
    b.segments = 2
    b.limit_method = "ANGLE"
    b.angle_limit = math.radians(50)
    return o


# ------------------------------------------------------------------- build ----

def build(view, preview):
    cfg = yaml.safe_load(open(rd(CONFIG), encoding="utf-8"))
    V = lambda d: cfg_value(cfg, d)
    (W, H, T), parts, zones = load_echo()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"

    # THE PANEL FRAME: x across, y up, z out of the panel toward the viewer, in mm.
    # Blender's world is metres, Z up: the rig turns the frame so the panel
    # stands in the X-Z plane facing -Y, and scales mm to m.
    rig = bpy.data.objects.new("panel frame", None)
    sc.collection.objects.link(rig)
    # picture: the case leans back, as a desktop skiff's rows do (front: upright, to check the print)
    lean = 0.0 if view == "front" else 14.0
    rig.matrix_world = Matrix.Rotation(math.radians(90 - lean), 4, "X") @ Matrix.Scale(MM, 4)

    # ---------------------------------------------------------- materials --
    ink_panel = V("art.ink.panel")
    nickel = principled("nickel", "#C9C7C2", 0.22, 1.0)
    chrome = principled("chrome", "#E4E4E6", 0.08, 1.0)
    steel = principled("stainless", "#B8B8BA", 0.3, 1.0, **{"Anisotropic": 0.5})
    black_plastic = principled("black plastic", "#141415", 0.42, 0.0, **{"Specular IOR Level": 0.5})
    knob_plastic = principled("knob", "#0E0E0F", 0.30, 0.0, **{"Coat Weight": 0.25, "Coat Roughness": 0.25})
    white_paint = principled("pointer", "#F0F0EC", 0.4)
    neutrik = principled("etherCON", "#1A1A1C", 0.35, 0.0, **{"Coat Weight": 0.2})
    alu_brushed = principled("brushed alu", "#BDBEC1", 0.28, 1.0, **{"Anisotropic": 0.7})
    case_black = principled("case", "#0C0C0D", 0.55, 0.0)
    blank_black = principled("blank anodise", ink_panel, 0.5, 0.35)
    rubber = principled("plug grip", "#1C1C1E", 0.55)
    cable_mats = [principled("cable A", "#F26B1D", 0.38, 0.0, **{"Coat Weight": 0.3, "Coat Roughness": 0.2}),
                  principled("cable B", "#18B5A4", 0.38, 0.0, **{"Coat Weight": 0.3, "Coat Roughness": 0.2})]
    umb_cable = principled("umbilical cable", "#101012", 0.45)
    led_mat = principled("LED", "#39E36A", 0.15, 0.0, **{"Transmission Weight": 0.6, "Emission Color": srgb("#48FF6E"),
                                                          "Emission Strength": 6.0})

    # The panel: the print (albedo, roughness, relief) on black anodise, with
    # a brushed direction, a bead-blast grain and the cut edges catching light.
    pm = bpy.data.materials.new("panel")
    nt = pm.node_tree
    N = nt.nodes
    bsdf = N["Principled BSDF"]
    uv = N.new("ShaderNodeUVMap")

    def img(path, colour):
        t = N.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(rd(path))
        t.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        t.interpolation = "Cubic"
        link(pm, uv.outputs["UV"], t.inputs["Vector"])
        return t
    t_alb, t_rough, t_h = img(TEX["albedo"], True), img(TEX["roughness"], False), img(TEX["height"], False)
    rp, ri = V("art.texture.rough_panel"), V("art.texture.rough_ink")
    inkmask = N.new("ShaderNodeMapRange")
    inkmask.inputs["From Min"].default_value = rp
    inkmask.inputs["From Max"].default_value = ri
    link(pm, t_rough.outputs["Color"], inkmask.inputs["Value"])
    anod = N.new("ShaderNodeMath")
    anod.operation = "SUBTRACT"
    anod.inputs[0].default_value = 1.0
    link(pm, inkmask.outputs["Result"], anod.inputs[1])
    # bead-blast grain in the roughness, only on the bare anodise
    grain = N.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 4000.0
    grain.inputs["Detail"].default_value = 2.0
    gmul = N.new("ShaderNodeMapRange")
    gmul.inputs["To Min"].default_value = -0.06
    gmul.inputs["To Max"].default_value = 0.06
    link(pm, grain.outputs["Fac"], gmul.inputs["Value"])
    gm2 = N.new("ShaderNodeMath")
    gm2.operation = "MULTIPLY"
    link(pm, gmul.outputs["Result"], gm2.inputs[0])
    link(pm, anod.outputs["Value"], gm2.inputs[1])
    radd = N.new("ShaderNodeMath")
    radd.operation = "ADD"
    link(pm, t_rough.outputs["Color"], radd.inputs[0])
    link(pm, gm2.outputs["Value"], radd.inputs[1])
    link(pm, radd.outputs["Value"], bsdf.inputs["Roughness"])
    # anodise: a dark oxide over metal - part metallic, anisotropic along y
    mm_ = N.new("ShaderNodeMath")
    mm_.operation = "MULTIPLY"
    mm_.inputs[1].default_value = 0.25
    link(pm, anod.outputs["Value"], mm_.inputs[0])
    link(pm, mm_.outputs["Value"], bsdf.inputs["Metallic"])
    am = N.new("ShaderNodeMath")
    am.operation = "MULTIPLY"
    am.inputs[1].default_value = 0.2
    link(pm, anod.outputs["Value"], am.inputs[0])
    link(pm, am.outputs["Value"], bsdf.inputs["Anisotropic"])
    # the brushing runs up the panel: a constant object-space tangent (a UV
    # tangent interpolated over the caps' long triangles drew their edges)
    tang = N.new("ShaderNodeVectorTransform")
    tang.vector_type = "VECTOR"
    tang.convert_from = "OBJECT"
    tang.convert_to = "WORLD"
    tang.inputs["Vector"].default_value = (0.0, 1.0, 0.0)
    link(pm, tang.outputs["Vector"], bsdf.inputs["Tangent"])
    bsdf.inputs["Anisotropic Rotation"].default_value = 0.0
    # edge wear: where the bevelled normal leaves the true one, lighten a little
    bev = N.new("ShaderNodeBevel")
    bev.inputs["Radius"].default_value = 0.35 * MM
    geo = N.new("ShaderNodeNewGeometry")
    dot = N.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    link(pm, bev.outputs["Normal"], dot.inputs[0])
    link(pm, geo.outputs["Normal"], dot.inputs[1])
    wear = N.new("ShaderNodeMapRange")
    wear.inputs["From Min"].default_value = 0.995
    wear.inputs["From Max"].default_value = 0.93
    link(pm, dot.outputs["Value"], wear.inputs["Value"])
    col = N.new("ShaderNodeMix")
    col.data_type = "RGBA"
    link(pm, wear.outputs["Result"], col.inputs["Factor"])
    link(pm, t_alb.outputs["Color"], col.inputs["A"])
    col.inputs["B"].default_value = srgb("#6A6B70")
    link(pm, col.outputs["Result"], bsdf.inputs["Base Color"])
    # the ink's relief, and the grain as a whisper of bump
    bump = N.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = V("art.texture.relief") * MM
    bump.inputs["Strength"].default_value = 1.0
    link(pm, t_h.outputs["Color"], bump.inputs["Height"])
    bump2 = N.new("ShaderNodeBump")
    bump2.inputs["Strength"].default_value = 0.04
    link(pm, grain.outputs["Fac"], bump2.inputs["Height"])
    link(pm, bump.outputs["Normal"], bump2.inputs["Normal"])
    link(pm, bev.outputs["Normal"], bump.inputs["Normal"])
    link(pm, bump2.outputs["Normal"], bsdf.inputs["Normal"])

    # ------------------------------------------------------------- panel --
    panel_mesh(W, H, T, rig, pm)

    # ------------------------------------------------------------- parts --
    knob_d, knob_h, knob_gap = V("knob.d"), V("knob.h"), V("knob.gap")
    angles = {"POT-GAIN": -38.0, "POT-OFFSET": 0.0, "POT-RESP": 52.0}   # picture: where the knobs are turned
    for name in ("POT-GAIN", "POT-OFFSET", "POT-RESP"):
        p = parts[name]
        knob(name, p[0], p[1], knob_d, knob_h, knob_gap, angles[name], rig, knob_plastic, white_paint)
    jack_stl = import_stl(STL["pj398sm"])
    for name, p in parts.items():
        if p[2] == "jack":
            x, y, hole, nut_d, nut_h, proud = p[0], p[1], p[3], p[4], p[5], p[6]
            o = jack_stl.copy()
            bpy.context.collection.objects.link(o)
            o.parent = rig
            # the STL's origin is the jack board's front face; its barrel along +z
            o.location = (x, y, -(T + V("jack.body_d")))
            o.rotation_euler = (0, 0, math.radians(90 if x < W / 2 else -90))
            bore_dark(o, nickel, black_plastic)
            hexnut(f"nut {name}", nut_d, nut_h, 6.0, rig, nickel).location = (x, y, 0.0)
    bpy.data.objects.remove(jack_stl)
    # the LED, lit - the +12 V rail is on
    x, y, lens_d, proud = parts["LED-PANEL"][:2] + parts["LED-PANEL"][3:5]
    r = lens_d / 2
    led = lathe([(r, -1.0), (r, proud - r)] + [(r * math.cos(math.radians(t)), proud - r + r * math.sin(math.radians(t))) for t in range(10, 90, 10)]
                + [(0.01, proud)], n=48, cap_top=False)
    new_obj("LED-PANEL", mesh_from_bm("led", led, 80), rig, led_mat).location = (x, y, 0)
    toggle(parts["SW-POWER"], V, rig, chrome, nickel, T)
    # the etherCON, its A-screws, and the umbilical's NE8MX mated
    ex, ey = parts["J-UMBILICAL"][:2]
    fav = import_stl(STL["ne8fav"])
    fav.parent = rig
    fav.location = (ex, ey, -T)
    fav.data.materials.append(neutrik)
    mx = import_stl(STL["ne8mx"])
    mx.parent = rig
    # NE8MX: its nose (+z in the STL) fully home at the NE8FAV's PCB face
    mx.rotation_euler = (0, math.radians(180), 0)
    setback = V("ethercon.pcb_setback")
    mx.location = (ex, ey, -(T + setback) + 14.9)
    mx.data.materials.append(black_plastic)
    for name, p in parts.items():
        if p[2] == "screw":
            hd, hh = p[3], p[4]
            head = lathe([(hd / 2, 0.0), (hd / 2, hh * 0.35), (hd / 2 * 0.8, hh * 0.85), (hd / 2 * 0.45, hh), (0.01, hh)], n=48, cap_top=False)
            new_obj(name, mesh_from_bm("ascrew", head), rig, black_plastic).location = (p[0], p[1], 0)
        if p[2] == "mount":
            hd, hk, wod, wt = p[3], p[4], p[5], p[6]
            w = lathe([(3.2 / 2, 0), (wod / 2, 0), (wod / 2, wt), (3.2 / 2, wt)], n=64)
            new_obj(f"{name} washer", mesh_from_bm("washer", w), rig, steel).location = (p[0], p[1], 0)
            head = lathe([(hd / 2, 0), (hd / 2, hk * 0.45), (hd / 2 * 0.86, hk * 0.9), (hd / 2 * 0.6, hk), (0.01, hk)], n=64, cap_top=False)
            ho = new_obj(f"{name} head", mesh_from_bm("pan", head), rig, steel)
            ho.location = (p[0], p[1], wt)
            cross(ho, hk, rig)
    # the umbilical's cable: out of the plug's boot, bending down into the drop zone
    boot = -(T + setback) + 14.9 + 49.6
    cable([(ex, ey, boot - 3), (ex, ey, boot + 10), (ex, ey - 8, boot + 22), (ex, ey - 40, boot + 26), (ex, -160, boot + 22)],
          V("ethercon.umb_od") / 2, rig, umb_cable)

    # --------------------------------------------------- patch cables ----
    if view != "front":
        plug_d = V("jack.plug_d")
        routes = {  # picture: two patch cables, out of MOD3 and MOD2, clear of the pitch and breath pills
            "J-CV-MOD3": [(0, 0, 32), (-10, -6, 50), (-40, -30, 62), (-80, -100, 56), (-110, -230, 40)],
            "J-CV-MOD2": [(0, 0, 30), (22, 6, 36), (64, 12, 40), (125, -10, 38), (180, -130, 30)],
        }
        for i, (name, rel) in enumerate(routes.items()):
            x, y = parts[name][:2]
            patch_plug(name, x, y, plug_d, parts[name][6], rig, rubber, cable_mats[i])
            cable([(x + a, y + b, c) for a, b, c in [(0, 0, 24)] + rel], 1.8, rig, cable_mats[i])

    # ------------------------------------------------------------ case ----
    case(W, H, T, V, rig, case_black, alu_brushed, blank_black, nickel)

    return sc, rig, parts, (W, H, T)


def panel_mesh(W, H, T, rig, mat):
    import ezdxf
    from shapely.geometry import LineString, Polygon, Point
    from shapely.ops import polygonize
    doc = ezdxf.readfile(rd(DXF))
    lines = [LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]) for e in doc.modelspace() if e.dxftype() == "LINE"]
    panel = max(polygonize(lines), key=lambda f: f.area)
    loops = [list(panel.exterior.coords)[:-1]]
    for r in panel.interiors:
        pts = list(r.coords)[:-1]
        # A round hole the DXF carries as a 48-gon is re-drawn round, so a
        # close-up shows a bore and not facets; any other shape is kept.
        c = Polygon(pts).centroid
        ds = [math.dist((c.x, c.y), p) for p in pts]
        if max(ds) - min(ds) < 0.02 * max(ds):
            rr = sum(ds) / len(ds) / math.cos(math.pi / len(pts)) ** 0.5
            pts = [(c.x + rr * math.cos(2 * math.pi * i / 192), c.y + rr * math.sin(2 * math.pi * i / 192)) for i in range(192)]
        loops.append(pts)
    bm = prism_bm(loops, -T, 0.0)
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for l in f.loops:
            l[uvl].uv = (l.vert.co.x / W, l.vert.co.y / H)
    me = mesh_from_bm("panel", bm, 30)
    # The cut edges are rounded in the shader (the Bevel node in the panel
    # material): a bevel modifier on these long cap triangles drew their edges.
    return new_obj("panel", me, rig, mat)


def import_stl(path):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=rd(path))
    o = (set(bpy.data.objects) - before).pop()
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    return o


def bore_dark(o, outer, inner):
    """The jack's bore and its insulator black, its bushing and body metal."""
    o.data = o.data.copy()
    o.data.materials.clear()
    o.data.materials.append(outer)
    o.data.materials.append(inner)
    for p in o.data.polygons:
        c = p.center
        p.material_index = 1 if (math.hypot(c.x, c.y) < 2.4 or c.z < 9.0) else 0


def knob(name, x, y, d, h, gap, turn, rig, mat, paint):
    """The Thonk 1900h clone: a skirt, a fluted body tapering to a flat top,
    a white line from the top's centre to its edge."""
    R = d / 2
    skirt_h = h * 0.22
    prof = [(R * 0.94, 0.0), (R, 0.35), (R, skirt_h - 0.4), (R * 0.97, skirt_h), (R * 0.86, skirt_h + 0.5)]
    body = [(R * 0.86 - (R * 0.86 - R * 0.72) * t, skirt_h + 0.5 + (h - 1.0 - skirt_h - 0.5) * t) for t in [i / 12 for i in range(1, 13)]]
    top = [(R * 0.70, h - 0.5), (R * 0.64, h - 0.08), (0.01, h)]
    flutes = 12

    def radial(t, z, r):
        if z <= skirt_h:            # a fine knurl on the skirt
            return r * (1 - 0.012 * (0.5 + 0.5 * math.cos(60 * t))) if 0.5 < z < skirt_h - 0.5 else r
        if z >= h - 0.5:
            return r
        w = 0.5 + 0.5 * math.cos(flutes * t)
        return r * (1 - 0.07 * w ** 3)
    bm = lathe(prof + body + top, n=240, radial=radial, cap_top=False)
    o = new_obj(f"knob {name}", mesh_from_bm("knob", bm, 50), rig, mat)
    o.location = (x, y, gap)
    o.rotation_euler = (0, 0, math.radians(-turn))
    # the pointer: a white line on the top face, centre to edge
    ln = box_bm(-0.28, 0.4, h - 0.12, 0.28, R * 0.66, h + 0.02)
    lo = new_obj(f"knob {name} line", mesh_from_bm("line", ln), o, paint)
    return o


def toggle(p, V, rig, chrome, nickel, T):
    x, y, _, onx, ony, lev_len, lev_d, lev_ang, proud, nut_d, nut_h = p[:11]
    hole_d, flat = V("toggle.hole_d"), V("toggle.flat")
    # the keyed, threaded bushing, standing `proud` in front of the face
    bm = lathe([(hole_d / 2 - 0.05, 0.0), (hole_d / 2 - 0.05, proud - 0.3), (hole_d / 2 - 0.35, proud)], n=96)
    bush = new_obj("SW-POWER bushing", mesh_from_bm("bush", bm, 40), rig, nickel)
    bush.location = (x, y, 0)
    # a thin lock washer and the nut
    lw = lathe([(hole_d / 2 + 0.1, 0), (nut_d / 2 + 0.6, 0), (nut_d / 2 + 0.6, 0.5), (hole_d / 2 + 0.1, 0.5)], n=96)
    new_obj("SW-POWER washer", mesh_from_bm("tw", lw), rig, nickel).location = (x, y, 0)
    nut = hexnut("SW-POWER nut", nut_d, nut_h, hole_d, rig, nickel)
    nut.location = (x, y, 0.5)
    # the lever, thrown to ON: a slim chrome bat, a ball at its root
    lev = lathe([(0.01, 0.0), (lev_d * 0.55, 0.3), (lev_d * 0.42, 1.5), (lev_d * 0.5, lev_len * 0.55), (lev_d * 0.55, lev_len - 0.9),
                 (lev_d * 0.45, lev_len - 0.25), (0.01, lev_len)], n=64, cap_top=False, cap_bot=False)
    lo = new_obj("SW-POWER lever", mesh_from_bm("lever", lev, 60), rig, chrome)
    lo.location = (x, y, proud - 0.6)
    lo.rotation_mode = "AXIS_ANGLE"
    lo.rotation_axis_angle = (math.radians(lev_ang), -ony, onx, 0)
    ball = lathe([(0.01, -1.2)] + [(1.55 * math.sin(math.radians(a)), -1.2 + 1.55 - 1.55 * math.cos(math.radians(a))) for a in range(10, 180, 10)] + [(0.01, 1.9)], n=48)
    new_obj("SW-POWER pivot", mesh_from_bm("pivot", ball, 60), rig, chrome).location = (x, y, proud - 0.9)


def cross(head, hk, rig):
    """A Pozidriv-ish cross in a pan head, by boolean."""
    bm = box_bm(-1.1, -0.28, hk - 0.9, 1.1, 0.28, hk + 1)
    bm2 = box_bm(-0.28, -1.1, hk - 0.9, 0.28, 1.1, hk + 1)
    me = mesh_from_bm("x1", bm)
    a = bpy.data.objects.new("cross a", me)
    bpy.context.collection.objects.link(a)
    b = bpy.data.objects.new("cross b", mesh_from_bm("x2", bm2))
    bpy.context.collection.objects.link(b)
    for c in (a, b):
        c.parent = head
        c.hide_render = True
        c.hide_viewport = True
        m = head.modifiers.new("cross", "BOOLEAN")
        m.object = c
        m.operation = "DIFFERENCE"
        m.solver = "EXACT"


def patch_plug(name, x, y, d, proud, rig, grip, cable_mat):
    """A moulded 3.5 mm patch plug seated in the jack: a knurled-looking grip
    `jack.plug_d` across, tapering to a strain-relief boot."""
    R = d / 2
    prof = [(2.6, proud + 0.2), (R * 0.82, proud + 0.6), (R, proud + 2.0), (R, proud + 11.0), (R * 0.9, proud + 13.0),
            (R * 0.58, proud + 15.0), (R * 0.42, proud + 22.0), (1.9, proud + 24.5), (1.8, proud + 25.0)]

    def rib(t, z, r):
        if proud + 2.5 < z < proud + 10.5:
            return r * (1 - 0.035 * (0.5 + 0.5 * math.cos(16 * t)) ** 2)
        return r
    o = new_obj(f"plug {name}", mesh_from_bm("plug", lathe(prof, n=160, radial=rib), 50), rig, grip)
    o.location = (x, y, 0)
    # a coloured band on the grip, the cable's colour
    band = lathe([(R * 1.002, proud + 11.2), (R * 0.95, proud + 12.6)], n=160, cap_top=False, cap_bot=False)
    o2 = new_obj(f"plug {name} band", mesh_from_bm("band", band), rig, cable_mat)
    o2.location = (x, y, 0)


def cable(points, r, rig, mat):
    cu = bpy.data.curves.new("cable", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 6
    cu.resolution_u = 24
    sp = cu.splines.new("NURBS")
    sp.points.add(len(points) - 1)
    for p, c in zip(sp.points, points):
        p.co = (*c, 1.0)
    sp.use_endpoint_u = True
    sp.order_u = 4
    sp.use_smooth = True
    o = bpy.data.objects.new("cable", cu)
    bpy.context.collection.objects.link(o)
    o.parent = rig
    o.data.materials.append(mat)
    return o


def case(W, H, T, V, rig, black, alu, blank, nickel):
    """Scenery: a slice of a black desktop case - two rails, a left cheek, a
    floor - with blank panels either side (Doepfer widths: 4HP 20.0, 8HP
    40.3, 6HP 30.0 [ds DOEPFER-A100-CONSTRUCTION-DETAILS Table 1])."""
    hp = V("panel.hp")
    hole_y = V("panel.hole_y")
    gap = hp * 10 - W                         # the 10HP slot less the panel: the gap either side
    rail_h = 10.0                             # picture: a Vector-style rail's front face
    x0, x1 = -4 * hp - 0.6, W + 42 * hp
    for yc in hole_y:
        bm = box_bm(x0, yc - rail_h / 2, -T - 9.0, x1, yc + rail_h / 2, -T)
        o = new_obj("rail", mesh_from_bm("rail", bm), rig, alu)
        bv = o.modifiers.new("b", "BEVEL")
        bv.width = 0.6
        bv.segments = 3
        # the rail's threaded strip slot, a dark groove along its face
        g = box_bm(x0, yc - 1.4, -T - 0.4, x1, yc + 1.4, -T + 0.01)
        new_obj("rail slot", mesh_from_bm("slot", g), rig, black)
    # case frame: top and bottom lips, a left cheek, a floor, a back
    ch = 3 * 44.45                            # 3U, 133.35 (A-100)
    ymid = H / 2
    for z0, z1, y0, y1 in ((-T - 60, -T - 9, ymid - ch / 2 - 12, ymid - ch / 2 + 2), (-T - 60, -T - 9, ymid + ch / 2 - 2, ymid + ch / 2 + 12)):
        new_obj("case lip", mesh_from_bm("lip", box_bm(x0, y0, z0, x1, y1, z1)), rig, black)
    cheek = box_bm(x0 - 12, ymid - ch / 2 - 22, -T - 70, x0, ymid + ch / 2 + 22, 3.0)
    ck = new_obj("case cheek", mesh_from_bm("cheek", cheek), rig, black)
    b = ck.modifiers.new("b", "BEVEL")
    b.width = 2.0
    b.segments = 5
    new_obj("case back", mesh_from_bm("back", box_bm(x0 - 12, ymid - ch / 2 - 22, -T - 72, x1, ymid + ch / 2 + 22, -T - 70)), rig, black)
    # blank panels: 4HP brushed aluminium on the left, 8HP and 6HP black on the right
    blanks = [(-(4 * hp) - gap / 2, 20.0, blank), (W + gap + 0, 40.3, blank), (W + gap + 8 * hp, 30.0, alu),
              (W + gap + 14 * hp, 40.3, blank), (W + gap + 22 * hp, 60.6, blank), (W + gap + 34 * hp, 40.3, blank)]
    for bx, bw, m in blanks:
        bm = box_bm(bx, 0, -T, bx + bw, H, 0)
        o = new_obj("blank", mesh_from_bm("blank", bm), rig, m)
        bv = o.modifiers.new("b", "BEVEL")
        bv.width = 0.22
        bv.segments = 3
        for hx in (7.5,) if bw < 30 else (7.5, 7.5 + (int((bw - 15) / hp)) * hp):
            for hy in hole_y:
                if bx + hx < bx + bw:
                    hd = lathe([(3.0, 0), (3.0, 1.1), (2.6, 2.0), (0.01, 2.3)], n=48, cap_top=False)
                    new_obj("blank screw", mesh_from_bm("bs", hd), rig, nickel).location = (bx + hx, hy, 0)


def setup(sc, rig, parts, dims, view, preview):
    W, H, T = dims
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02 if preview else 0.012
    sc.cycles.samples = 48 if preview else 160
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 8
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 4
    sc.cycles.seed = 0
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = -0.7
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    sc.render.film_transparent = False

    # the world: the studio probe, dim, for reflections in the metal
    wd = bpy.data.worlds.new("studio")
    sc.world = wd
    env = wd.node_tree.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(rd(HDRI))
    bg = wd.node_tree.nodes["Background"]
    bg.inputs["Strength"].default_value = 0.12
    mp = wd.node_tree.nodes.new("ShaderNodeMapping")
    tc = wd.node_tree.nodes.new("ShaderNodeTexCoord")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(200))
    wd.node_tree.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    wd.node_tree.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    wd.node_tree.links.new(env.outputs["Color"], bg.inputs["Color"])

    def P(x, y, z):   # panel frame mm -> world m
        return rig.matrix_world @ Vector((x, y, z))

    def area(name, loc, target, size, power, color=(1, 1, 1), shape="RECTANGLE", size_y=None):
        L = bpy.data.lights.new(name, "AREA")
        L.shape = shape
        L.size = size
        if size_y:
            L.size_y = size_y
        L.energy = power
        L.color = color
        o = bpy.data.objects.new(name, L)
        sc.collection.objects.link(o)
        o.location = loc
        d = (target - Vector(loc)).normalized()
        o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        return o

    c = P(W / 2, H / 2, 0)
    # picture: a large soft key from the upper left, a cool rim from the upper
    # right behind, a warm low fill, and a long strip overhead for the gradient
    area("key", c + Vector((-0.35, -0.45, 0.45)), c, 0.55, 22.0, (1.0, 0.97, 0.93))
    area("rim", c + Vector((0.45, 0.05, 0.35)), c, 0.25, 12.0, (0.85, 0.92, 1.0), size_y=0.9)
    area("fill", c + Vector((0.4, -0.5, -0.12)), c, 0.6, 3.0, (1.0, 0.93, 0.85))
    area("top", c + Vector((0.0, -0.18, 0.5)), c, 0.12, 7.0, (1, 1, 1), size_y=0.9)

    # the floor and a sweep behind, dark, so the module floats in soft light
    low = min(P(0, H / 2 - 3 * 44.45 / 2 - 22, z).z for z in (3.0, -T - 72))
    bpy.ops.mesh.primitive_plane_add(size=6.0, location=(c.x, c.y + 1.2, low))
    fl = bpy.context.object
    fl.data.materials.append(principled("floor", "#1E1E20", 0.6))
    bpy.ops.mesh.primitive_plane_add(size=6.0, location=(c.x, c.y + 1.0, c.z), rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(principled("sweep", "#161618", 0.7))

    cam = bpy.data.cameras.new("cam")
    co = bpy.data.objects.new("cam", cam)
    sc.collection.objects.link(co)
    sc.camera = co
    cam.sensor_width = 36.0
    focus = bpy.data.objects.new("focus", None)
    sc.collection.objects.link(focus)
    cam.dof.focus_object = focus
    if view == "hero":
        sc.render.resolution_x, sc.render.resolution_y = 1920, 2400
        cam.lens = 85
        tgt = P(W / 2 + 2, H / 2 + 6, 6)
        co.location = tgt + Vector((0.16, -0.36, 0.13))
        focus.location = P(parts["POT-OFFSET"][0], parts["POT-OFFSET"][1] - 12, 8)
        cam.dof.use_dof = True
        cam.dof.aperture_fstop = 5.6
        cam.shift_y = 0.0
    elif view == "front":
        sc.render.resolution_x, sc.render.resolution_y = 1100, 2420
        cam.type = "ORTHO"
        cam.ortho_scale = (H + 16) * MM
        sc.render.resolution_percentage = 100
        tgt = P(W / 2, H / 2, 0)
        co.location = tgt + Vector((0, -0.8, 0))
        cam.dof.use_dof = False
    else:   # detail
        sc.render.resolution_x, sc.render.resolution_y = 2400, 1600
        cam.lens = 100
        tgt = P(parts["POT-OFFSET"][0] - 2, parts["POT-OFFSET"][1] - 12, 4)
        co.location = tgt + Vector((0.07, -0.135, 0.075))
        focus.location = P(parts["POT-OFFSET"][0] - 9, parts["POT-OFFSET"][1] - 14.0, 5)
        cam.dof.use_dof = True
        cam.dof.aperture_fstop = 16.0
    d = (tgt - co.location).normalized()
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if preview:
        sc.render.resolution_percentage = 50


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--view", choices=["hero", "front", "detail"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fingerprint", default="")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--blend", help="also save the scene as a .blend here (for looking at it)")
    ap.add_argument("--percent", type=int, help="resolution percentage (iterating only)")
    ap.add_argument("--samples", type=int, help="samples (iterating only)")
    ap.add_argument("--no-render", action="store_true", help="build the scene only (with --blend)")
    a = ap.parse_args()
    sc, rig, parts, dims = build(a.view, a.preview)
    setup(sc, rig, parts, dims, a.view, a.preview)
    if a.percent:
        sc.render.resolution_percentage = a.percent
    if a.samples:
        sc.cycles.samples = a.samples
    sc.render.filepath = os.path.abspath(a.out)
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
    import time
    print(f"scene built in {time.process_time():.1f} s cpu", flush=True)
    if a.no_render:
        return 0
    bpy.ops.render.render(write_still=True)
    print(f"TOOL: render-module.py; Blender {bpy.app.version_string} (bpy), Cycles {sc.cycles.samples} spp adaptive, OIDN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
