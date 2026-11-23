#!/usr/bin/env python3
"""3D models drawn here, from banked drawings, for parts whose maker's model
could not be had (a login, a Cloudflare challenge) or does not match the part
bought. Written to hardware/lib/woody.3dshapes/<name>.step, which the matching
footprint in hardware/lib/woody.pretty names.

    python3 tools/lib-models.py            # (re)write every model
    python3 tools/lib-models.py --check    # exit 1 if a model file's solids or part colours differ from what this builds
    python3 tools/lib-models.py --assembly in.step out.step   # any model as an assembly of coloured parts (render-instrument.py)
    python3 tools/lib-models.py --glb in.step out.glb         # any model meshed, with its own tree and colours (render-instrument.py: the Matrix)

`--check` compares the solids (volume and bounding box of each), not the bytes:
OpenCASCADE's STEP writer orders its colour records differently from one run to
the next.

EVERY MODEL IS BUILT IN ITS FOOTPRINT'S FRAME: x as KiCad's, y NEGATED (a STEP
model's +y is the footprint's -y), z up from the board's top face. So each
footprint places its model with offset 0, rotation 0, scale 1, and the pads and
the model's tails line up by construction.

These are render and clearance models: boxes, cavities and bent pins at the
drawing's nominal dimensions. Where the drawing does not dimension something
(a shroud's wall, a pin's length inside the mouth) the value below says so
[est]. The sources are the banked drawings named on each part; the numbers
here must not be read back as datasheet figures.
"""
import os
import re
import sys
import tempfile

from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone
from OCP.gp import gp_Pnt, gp_Ax2, gp_Dir
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf
from OCP.Interface import Interface_Static
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "hardware", "lib", "woody.3dshapes")

BLACK = (0.12, 0.12, 0.12)
GREY = (0.30, 0.30, 0.30)
GOLD = (0.86, 0.74, 0.40)
TIN = (0.80, 0.80, 0.78)
WHITE = (0.92, 0.92, 0.90)
PBT = (0.02, 0.02, 0.02)      # a black moulding as KiCad's own models colour one (BLACK, above, photographs as mid grey on a large face)


def box(x0, x1, y0, y1, z0, z1):
    """A box in FOOTPRINT coordinates (y down), returned in model coordinates (y up)."""
    xa, xb = sorted((x0, x1)); ya, yb = sorted((-y0, -y1)); za, zb = sorted((z0, z1))
    return BRepPrimAPI_MakeBox(gp_Pnt(xa, ya, za), gp_Pnt(xb, yb, zb)).Shape()


def fuse(*shapes):
    s = shapes[0]
    for t in shapes[1:]:
        s = BRepAlgoAPI_Fuse(s, t).Shape()
    return s


def cut(s, *tools):
    for t in tools:
        s = BRepAlgoAPI_Cut(s, t).Shape()
    return s


def rt_pin(x_tail, y, z_row, x_tip, w, tail):
    """A right-angle pin, square section w: down through the board at x_tail from
    z_row to -tail, and along +x from x_tail to x_tip at height z_row."""
    h = w / 2
    return fuse(box(x_tail - h, x_tail + h, y - h, y + h, -tail, z_row + h),
                box(x_tail - h, x_tip, y - h, y + h, z_row - h, z_row + h))


def port(x, y0, z, length, d_root, d_tip):
    """A barbed port along -y (footprint) from y0, as a cylinder then a cone."""
    ax = gp_Ax2(gp_Pnt(x, -y0, z), gp_Dir(0, 1, 0))           # model +y = footprint -y
    c = BRepPrimAPI_MakeCylinder(ax, d_root / 2, length * 0.55).Shape()
    ax2 = gp_Ax2(gp_Pnt(x, -y0 + length * 0.55, z), gp_Dir(0, 1, 0))
    k = BRepPrimAPI_MakeCone(ax2, d_tip / 2, d_root / 2 * 0.9, length * 0.45).Shape()
    return fuse(c, k)


# ------------------------------------------------------------------ the parts
def hanxia_pz254_1x8p_wz():
    """J-UMB. hanxia HX PZ2.54-1x8P WZ, datasheets/connectors/HANXIA-HX-PZ2.54-1x8P-WZ.pdf:
    insulator 2.50 x 2.50, (B - 0.2) = 20.12 long for 8 pins; the posts 6.00 past
    it; 4.30 from its mating face back to the tail row, so the tails are 1.80
    behind its back; tails 3.00 past the seating plane; pins 0.64 square on 2.54.
    The row's height is not dimensioned: the insulator's middle, 1.25 [calc]."""
    n, p = 8, 2.54
    yc = (n - 1) * p / 2
    x0 = 4.30 - 2.50
    ins = box(x0, 4.30, yc - 20.12 / 2, yc + 20.12 / 2, 0, 2.50)
    pins = [rt_pin(0.0, k * p, 1.25, 4.30 + 6.00, 0.64, 3.00) for k in range(n)]
    return [("insulator", ins, BLACK), ("pins", fuse(*pins), GOLD)]


def nxp_case_1351_01():
    """U-BREATH. NXP MPXV4006DP, case 1351-01, datasheets/analog/MPXV4006DP.pdf p.20
    (nominal): D = E1 12.06 square, A 9.65 over all, A1 0.15, E 17.53 tip to
    tip, L 1.27 foot, b 1.0 wide, P 0.25 thick, e 2.54; ports F 6.35 out of
    one face, N 4.32 apart across it. The ports' heights are config/body.yaml
    boards.sensor_port_z (8.5 and 1.4, scaled off p.7), and a barb of T's
    minimum 2.79 so the upper port's top stays inside A's maximum 9.91 [calc
    8.5 + 1.40 = 9.90]. The foot's rise into the body is drawn (Detail G) but
    not dimensioned: 1.0 [est].
    In the footprint's frame the ports point to -y and pin 1 is top left: the
    datasheet's top view turned 180 deg. The UPPER port (P1, the marked side,
    p.6) is on the pins 5-8 side - read off the p.20 end view as a
    third-angle projection (ASME Y14.5), which the drawing does not state."""
    b = 12.06 / 2
    body = box(-b, b, -b, b, 0.15, 9.65)
    ports = fuse(port(+4.32 / 2, -b, 8.5, 6.35, 2.4, 2.79),
                 port(-4.32 / 2, -b, 1.4, 6.35, 2.4, 2.79))
    leads = []
    tip, t, rise = 17.53 / 2, 0.25, 1.0
    for k in range(4):
        y = -3.81 + k * 2.54
        for s in (-1, 1):
            xa, xb = sorted((s * (b - 0.2), s * (tip - 1.27 + t)))
            leads.append(box(xa, xb, y - 0.5, y + 0.5, rise, rise + t))                        # out of the body
            xa, xb = sorted((s * (tip - 1.27), s * (tip - 1.27 + t)))
            leads.append(box(xa, xb, y - 0.5, y + 0.5, 0, rise + t))                           # the bend down
            xa, xb = sorted((s * (tip - 1.27), s * tip))
            leads.append(box(xa, xb, y - 0.5, y + 0.5, 0, t))                                  # the foot
    return [("body", fuse(body, ports), WHITE), ("leads", fuse(*leads), TIN)]


def box_header_vertical(n, L):
    """A vertical 1.27 mm shrouded box header of the pattern CNC Tech's 3220 and XKB's
    X1270WV share: n positions a row and L long, 5.1 across (3.7 inside), 5.40 high (3.5
    deep inside), posts 0.40 square, tails 2.1 past the seating plane, key slot in the wall
    over the odd row. The cavity's length, the slot's width (XKB gives 2.35) and the posts'
    height inside the mouth are not dimensioned on CNC Tech's drawing [est]."""
    p = 1.27
    xc, yc = p / 2, (n - 1) * p / 2
    W, H = 5.1, 5.40
    body = box(xc - W / 2, xc + W / 2, yc - L / 2, yc + L / 2, 0, H)
    cav = box(xc - 3.7 / 2, xc + 3.7 / 2, yc - (L - 1.4) / 2, yc + (L - 1.4) / 2, H - 3.5, H + 1)   # [est] 0.7 end walls, as the long walls
    key = box(xc - W / 2 - 1, xc, yc - 2.35 / 2, yc + 2.35 / 2, H - 3.5, H + 1)
    body = cut(body, cav, key)
    pins = [box(x - 0.2, x + 0.2, k * p - 0.2, k * p + 0.2, -2.1, H - 0.6) for k in range(n) for x in (0.0, p)]   # [est] tips 0.6 under the mouth
    return [("body", body, BLACK), ("pins", fuse(*pins), GOLD)]


def cnctech_3220_10_0100_00():
    """J-CHAIN. CNC Tech 3220-10-0100-00, datasheets/connectors/CNCTECH-3220-XX-0100-00-1.27MM-BOX-HEADER-VERTICAL.pdf
    rev A: 10 positions, C 12.65."""
    return box_header_vertical(5, 12.65)


def xkb_x1270wv_2x12():
    """J-MCU and J-MCU-C. XKB X1270WV-2x12, datasheets/connectors/XKB-X1270WV-2xXXA-6TV01-1.27MM-BOX-HEADER-VERTICAL.pdf:
    24 positions, C 21.54 [calc: the series' C - A = 7.57; its table has no 24-position row]."""
    return box_header_vertical(12, 21.54)


def neutrik_ne8fav():
    """J-UMBILICAL-INST. Neutrik's own model, datasheets/connectors/NEUTRIK-NE8FAV-3D.stp,
    CUT INTO ITS MATERIALS and stood on the board. The banked STEP is one solid with no
    usable colour (a CAD system's default blue), and a model with no colour is drawn
    white in the photographs; nothing of its shape is redrawn here. The data sheet
    (NEUTRIK-NE8FAV-DATASHEET.pdf, Material): shell and insert PBTP, the locking element
    nickel plated, the contacts gold over nickel. So:
      - the PUSH tab, all of the solid above the flange's upper edge (ethercon.flange_h / 2
        above the axis): nickel. Where the latch ends inside the shell the model does
        not say, so only what stands clear of the flange is coloured [est];
      - what stands behind the board's front face (ethercon.pcb_setback behind the
        flange's front face, the model's z 0): the contacts' tails, gold, within a box
        round the two contact rows (ethercon.pin_rows); the pegs and the G tab outside it
        stay with the shell;
      - the rest: black PBTP.
    The model's frame is the footprint's (x across, y up from the axis, the flange's
    front face at z 0), moved up ethercon.pcb_setback so the board's front face is z 0."""
    from OCP.STEPControl import STEPControl_Reader
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf, gp_Vec
    src = os.path.join(ROOT, "datasheets", "connectors", "NEUTRIK-NE8FAV-3D.stp")
    r = STEPControl_Reader()
    with quiet():
        if r.ReadFile(src) != IFSelect_RetDone:
            raise SystemExit(f"could not read {src}")
        r.TransferRoots()
    solid = r.OneShape()
    setback, half = 18.3, 12.5
    mbox = lambda x0, x1, y0, y1, z0, z1: BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), gp_Pnt(x1, y1, z1)).Shape()
    tab_box = mbox(-13, 13, half, 20, -30, 10)
    tail_box = mbox(-5.5, 5.5, 1.0, 5.8, -30, -setback)
    tab = BRepAlgoAPI_Common(solid, tab_box).Shape()
    tails = BRepAlgoAPI_Common(solid, tail_box).Shape()
    shell = cut(solid, tab_box, tail_box)
    t = gp_Trsf(); t.SetTranslation(gp_Vec(0, 0, setback))
    up = lambda s: BRepBuilderAPI_Transform(s, t, True).Shape()
    return [("shell", up(shell), PBT), ("latch", up(tab), TIN), ("contacts", up(tails), GOLD)]


def banked_header(src, ins, turn, move):
    """A banked library model of a pin header, RECOLOURED to the part's materials and
    stood in its footprint's frame. The EasyEDA/LCSC library's models are the right
    shape (bent feet, chamfered posts) and the wrong colours (a white or grey
    moulding, grey posts); hanxia's drawings give black PA6T and gold flash. Every
    face inside `ins` - the insulator's box in the model's own frame, (x0, x1, y0, y1,
    z0, z1) - is the moulding, every other face a contact. Then the model is turned
    `turn` degrees about z and moved `move`, which is what puts its feet on the
    footprint's pads (checked against the board's pads when the footprint was given
    the model, 2026-11-22). Faces, not solids: for pictures only."""
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopoDS import TopoDS_Compound
    from OCP.BRep import BRep_Builder
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.STEPControl import STEPControl_Reader
    from OCP.gp import gp_Trsf, gp_Vec, gp_Ax1
    import math
    r = STEPControl_Reader()
    with quiet():
        if r.ReadFile(os.path.join(ROOT, src)) != IFSelect_RetDone:
            raise SystemExit(f"could not read {src}")
        r.TransferRoots()
    b = BRep_Builder()
    comp = {"insulator": TopoDS_Compound(), "contacts": TopoDS_Compound()}
    for c in comp.values():
        b.MakeCompound(c)
    e, tol = TopExp_Explorer(r.OneShape(), TopAbs_FACE), 0.02
    while e.More():
        bb = Bnd_Box(); BRepBndLib.Add_s(e.Current(), bb, False)
        lo, hi = bb.CornerMin(), bb.CornerMax()
        inside = (lo.X() >= ins[0] - tol and hi.X() <= ins[1] + tol and lo.Y() >= ins[2] - tol and hi.Y() <= ins[3] + tol
                  and lo.Z() >= ins[4] - tol and hi.Z() <= ins[5] + tol)
        b.Add(comp["insulator" if inside else "contacts"], e.Current())
        e.Next()
    rot = gp_Trsf(); rot.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), math.radians(turn))
    mv = gp_Trsf(); mv.SetTranslation(gp_Vec(*move))
    place = lambda sh: BRepBuilderAPI_Transform(sh, mv.Multiplied(rot), True).Shape()
    return [("insulator", place(comp["insulator"]), PBT), ("contacts", place(comp["contacts"]), GOLD)]


def hanxia_pz254_1x3p_tp_yq():
    """HDR-SERVICE. The library's model for C41417360, datasheets/connectors/HANXIA-HX-PZ2.54-1x3P-TP-YQ-3D.step:
    insulator z 0..2.50 over y -0.837..1.663 (the row is 0.413 off the model's origin), feet's underside at z -0.70."""
    return banked_header("datasheets/connectors/HANXIA-HX-PZ2.54-1x3P-TP-YQ-3D.step",
                         (-1.27, 6.35, -0.837, 1.663, 0.0, 2.5), 90, (0.413, -5.08, 0.7))


def hanxia_pz254_1x10p_tp_yq():
    """HDR-MATRIX. The library's model for C41417367 (a generic staggered-foot header),
    datasheets/connectors/HANXIA-HX-PZ2.54-1x10P-TP-YQ-3D.step: insulator z -2.50..0 over y +/-1.25, feet's underside at z -3.20."""
    return banked_header("datasheets/connectors/HANXIA-HX-PZ2.54-1x10P-TP-YQ-3D.step",
                         (-1.25, 24.111, -1.25, 1.25, -2.5, 0.0), -90, (0.0, 0.0, 3.2))


MODELS = {
    "XKB_X1270WV-2x12": xkb_x1270wv_2x12,
    "CNCTech_3220-10-0100-00": cnctech_3220_10_0100_00,
    "Hanxia_HX_PZ2.54-1x8P_WZ": hanxia_pz254_1x8p_wz,
    "NXP_Case1351-01_MPXV4006DP": nxp_case_1351_01,
    "Neutrik_NE8FAV": neutrik_ne8fav,
    "Hanxia_HX_PZ2.54-1x3P_TP-YQ": hanxia_pz254_1x3p_tp_yq,
    "Hanxia_HX_PZ2.54-1x10P_TP-YQ": hanxia_pz254_1x10p_tp_yq,
}


def write(name, parts, path):
    """One ASSEMBLY of coloured parts. kicad-cli's GLB export (KiCad 9) carries a model's
    colours only through an assembly's components: colours on free top-level shapes, as
    this wrote them until 2026-10-02, reach the GLB as no material at all, and the
    instrument's photographs drew every one of these parts white."""
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    asm = st.NewShape()
    TDataStd_Name.Set_s(asm, TCollection_ExtendedString(name))
    for label_name, shape, rgb in parts:
        lab = st.AddShape(shape, False)
        TDataStd_Name.Set_s(lab, TCollection_ExtendedString(f"{name}_{label_name}"))
        ct.SetColor(lab, Quantity_Color(*rgb, Quantity_TOC_RGB), XCAFDoc_ColorSurf)
        st.AddComponent(asm, lab, TopLoc_Location())
    st.UpdateAssemblies()
    save(doc, name, path)


def save(doc, name, path):
    Interface_Static.SetCVal_s("write.step.schema", "AP214IS")
    Interface_Static.SetCVal_s("write.step.product.name", name)
    w = STEPCAFControl_Writer()
    w.SetColorMode(True); w.SetNameMode(True)
    tmp = path + ".tmp"
    with quiet():
        w.Transfer(doc, STEPControl_AsIs)
        ok = w.Write(tmp) == IFSelect_RetDone
    if not ok:
        raise SystemExit(f"could not write {tmp}")
    text = open(tmp).read()
    os.remove(tmp)
    # reproducible: no timestamp, no writer path
    text = re.sub(r"FILE_NAME\('[^']*','[^']*'", f"FILE_NAME('{name}.step','2026-09-30T00:00:00'", text, count=1)
    open(path, "w").write(text)


class quiet:
    """OpenCASCADE prints its transfer statistics on fd 1; keep them off the terminal."""
    def __enter__(self):
        sys.stdout.flush()
        self.fd = os.dup(1)
        n = os.open(os.devnull, os.O_WRONLY)
        os.dup2(n, 1); os.close(n)

    def __exit__(self, *a):
        sys.stdout.flush()
        os.dup2(self.fd, 1); os.close(self.fd)


def solids(path):
    """(volume, bbox) of every solid in a STEP file, rounded, sorted."""
    from OCP.STEPControl import STEPControl_Reader
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_SOLID
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    r = STEPControl_Reader()
    with quiet():
        r.ReadFile(path); r.TransferRoots()
    out = []
    e = TopExp_Explorer(r.OneShape(), TopAbs_SOLID)
    while e.More():
        g = GProp_GProps(); BRepGProp.VolumeProperties_s(e.Current(), g)
        b = Bnd_Box(); BRepBndLib.Add_s(e.Current(), b, False)
        p, q = b.CornerMin(), b.CornerMax()
        out.append(tuple(round(v, 3) for v in (g.Mass(), p.X(), p.Y(), p.Z(), q.X(), q.Y(), q.Z())))
        e.Next()
    return sorted(out)


def read_xcaf(path):
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    r = STEPCAFControl_Reader()
    r.SetColorMode(True); r.SetNameMode(True)
    with quiet():
        if r.ReadFile(path) != IFSelect_RetDone or not r.Transfer(doc):
            raise SystemExit(f"could not read {path}")
    return doc


def label_colour(lab):
    from OCP.XCAFDoc import XCAFDoc_ColorTool, XCAFDoc_ColorGen
    c = Quantity_Color()
    for t in (XCAFDoc_ColorSurf, XCAFDoc_ColorGen):
        if XCAFDoc_ColorTool.GetColor_s(lab, t, c):
            return (c.Red(), c.Green(), c.Blue())
    return None


def children(lab):
    from OCP.TDF import TDF_ChildIterator
    it, out = TDF_ChildIterator(lab, False), []
    while it.More():
        out.append(it.Value()); it.Next()
    return out


def part_colours(path):
    """(is an assembly, the colours of its parts, rounded): what --check holds a drawn model to."""
    doc = read_xcaf(path)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    free = children(st.BaseLabel())
    asm = any(st.IsAssembly_s(L) for L in free)
    return asm, sorted({tuple(round(v, 3) for v in label_colour(L)) for L in free
                        if not st.IsAssembly_s(L) and label_colour(L)})


def as_assembly(src, dst):
    """Any STEP model rewritten as one flat ASSEMBLY with one part per colour, each part
    the faces that colour covers, placed where the model's own tree puts them - what
    kicad-cli's GLB export needs to carry a model's colours (write(), above). Two
    shapes it drops: KiCad's own library models (colours on the faces of one solid)
    reach the GLB with no material, and a nested assembly (Sunlord SWPA6028S) with no
    mesh at all. Colours keep their alpha. The solids are not kept as solids: this
    is for pictures, never for a clearance check."""
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopoDS import TopoDS_Compound
    from OCP.BRep import BRep_Builder
    from OCP.Quantity import Quantity_ColorRGBA
    from OCP.XCAFPrs import XCAFPrs_DocumentExplorer, XCAFPrs_DocumentExplorerFlags_OnlyLeafNodes
    import shutil
    from OCP.TDF import TDF_Label
    doc = read_xcaf(src)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    # one level of assembly over coloured parts already exports as it is: copy it, so
    # that what this rewrite cannot write survives (the STEP writer here drops a
    # colour's alpha - the KS33 housing's translucency)
    free = children(st.BaseLabel())
    asms = [L for L in free if st.IsAssembly_s(L)]

    def ref(c):
        r = TDF_Label()
        return r if st.GetReferredShape_s(c, r) else None
    if asms and not any(st.IsAssembly_s(ref(c)) for A in asms for c in children(A) if ref(c) is not None):
        shutil.copyfile(src, dst)
        return "copied: already one assembly of parts"
    groups = {}

    def faces(shape):
        e = TopExp_Explorer(shape, TopAbs_FACE)
        while e.More():
            yield e.Current(); e.Next()

    def rgba(lab, style=None):
        if style is not None and style.IsSetColorSurf():
            c = style.GetColorSurfRGBA()
            q = c.GetRGB()
            return (q.Red(), q.Green(), q.Blue(), c.Alpha())
        c = label_colour(lab)
        return (*c, 1.0) if c else None

    ex = XCAFPrs_DocumentExplorer(doc, XCAFPrs_DocumentExplorerFlags_OnlyLeafNodes)
    while ex.More():
        node = ex.Current()
        ref, loc = node.RefLabel, node.Location
        base = rgba(ref) or rgba(ref, node.Style)
        own = {}                      # face -> colour, from the part's coloured sub-shapes
        for k in children(ref):
            if st.IsSubShape_s(k) and rgba(k):
                for f in faces(st.GetShape_s(k)):
                    own.setdefault(hash(f), []).append((f, rgba(k)))
        for f in faces(st.GetShape_s(ref)):
            hit = next((c for g, c in own.get(hash(f), []) if g.IsSame(f)), None)
            groups.setdefault(hit or base or rgba(ref, node.Style), []).append(f.Moved(loc))
        ex.Next()
    if not groups:
        raise SystemExit(f"{src}: no faces")
    out = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    ost = XCAFDoc_DocumentTool.ShapeTool_s(out.Main())
    oct_ = XCAFDoc_DocumentTool.ColorTool_s(out.Main())
    asm = ost.NewShape()
    name = os.path.splitext(os.path.basename(dst))[0]
    TDataStd_Name.Set_s(asm, TCollection_ExtendedString(name))
    for i, (c, fs) in enumerate(sorted(groups.items(), key=lambda kv: (kv[0] is None, kv[0] or ()))):
        b, comp = BRep_Builder(), TopoDS_Compound()
        b.MakeCompound(comp)
        for f in fs:
            b.Add(comp, f)
        lab = ost.AddShape(comp, False)
        TDataStd_Name.Set_s(lab, TCollection_ExtendedString(f"{name}_{i}"))
        if c:
            oct_.SetColor(lab, Quantity_ColorRGBA(Quantity_Color(*c[:3], Quantity_TOC_RGB), c[3]), XCAFDoc_ColorSurf)
        ost.AddComponent(asm, lab, TopLoc_Location())
    ost.UpdateAssemblies()
    save(out, name, dst)
    return f"{len(groups)} colour(s)" + (", some faces uncoloured" if None in groups else "")


def as_glb(src, dst):
    """A STEP model meshed and written as binary glTF, its own tree, names and colours
    kept (OpenCASCADE's writer; metres, y up, as the format has them) - for a model
    no board file places: the Matrix, a bought board that stands on the carrier's
    header. For pictures only."""
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.RWGltf import RWGltf_CafWriter
    from OCP.TCollection import TCollection_AsciiString
    from OCP.collections import IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString
    from OCP.Message import Message_ProgressRange
    doc = read_xcaf(src)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    for lab in children(st.BaseLabel()):
        BRepMesh_IncrementalMesh(st.GetShape_s(lab), 0.03, False, 0.3, True)      # PICTURE CONVENTION: 0.03 mm, 0.3 rad
    w = RWGltf_CafWriter(TCollection_AsciiString(dst), True)
    from OCP.RWMesh import RWMesh_CoordinateSystem_Zup
    w.ChangeCoordinateSystemConverter().SetInputCoordinateSystem(RWMesh_CoordinateSystem_Zup)     # STEP's z up, to glTF's y up
    with quiet():
        ok = w.Perform(doc, IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString(), Message_ProgressRange())
    if not ok or not os.path.exists(dst):
        raise SystemExit(f"could not write {dst}")
    return "written"


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--assembly":
        print(as_assembly(sys.argv[2], sys.argv[3]))
        return
    if len(sys.argv) == 4 and sys.argv[1] == "--glb":
        print(as_glb(sys.argv[2], sys.argv[3]))
        return
    check = "--check" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    bad = 0
    for name, fn in MODELS.items():
        path = os.path.join(OUT, name + ".step")
        if check:
            with tempfile.TemporaryDirectory() as d:
                p2 = os.path.join(d, name + ".step")
                write(name, fn(), p2)
                same = os.path.exists(path) and solids(p2) == solids(path) and part_colours(p2) == part_colours(path)
            print(("ok     " if same else "DIFFERS ") + os.path.relpath(path, ROOT))
            bad += not same
        else:
            write(name, fn(), path)
            print("wrote", os.path.relpath(path, ROOT))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
