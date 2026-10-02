#!/usr/bin/env python3
"""3D models drawn here, from banked drawings, for parts whose maker's model
could not be had (a login, a Cloudflare challenge) or does not match the part
bought. Written to hardware/lib/woody.3dshapes/<name>.step, which the matching
footprint in hardware/lib/woody.pretty names.

    python3 tools/lib-models.py            # (re)write every model
    python3 tools/lib-models.py --check    # exit 1 if a model file's solids or part colours differ from what this builds
    python3 tools/lib-models.py --assembly in.step out.step   # any model as an assembly of coloured parts (render-instrument.py)

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
def xkb_x1270wr_2x12a_9tv01():
    """J-MCU. XKB X1270WR-2x12A-9TV01, datasheets/connectors/XKB-X1270WR-2x12A-9TV01.pdf
    rev A1: C 21.54 long, B 20.14 inside, 5.10 high (3.70 inside), 5.40 deep (3.50
    inside), key slot 2.35 in the wall over the odd row; tails 0.40 square, 2.10
    past the seating plane; far (odd) tail row 2.60 behind the back face, the
    near row 1.27 in front of it (side view). Rows at half the height +/- 0.635."""
    n, p = 12, 1.27
    yc = (n - 1) * p / 2
    back, depth, h = 2.60, 5.40, 5.10
    body = box(back, back + depth, yc - 21.54 / 2, yc + 21.54 / 2, 0, h)
    zc = h / 2
    cav = box(back + depth - 3.50, back + depth + 1, yc - 20.14 / 2, yc + 20.14 / 2, zc - 3.70 / 2, zc + 3.70 / 2)
    key = box(back + depth - 3.50, back + depth + 1, yc - 2.35 / 2, yc + 2.35 / 2, zc, h + 1)
    body = cut(body, cav, key)
    tip = back + depth - 0.6                                              # [est] post tip inside the mouth
    pins = []
    for k in range(n):
        y = k * p
        pins.append(rt_pin(0.0, y, zc + p / 2, tip, 0.40, 2.10))          # odd: upper row, far tails
        pins.append(rt_pin(p, y, zc - p / 2, tip, 0.40, 2.10))            # even: lower row, near tails
    return [("body", body, BLACK), ("pins", fuse(*pins), GOLD)]


def samtec_shf_106_01_l_d_ra():
    """J-CHAIN. Samtec SHF-106-01-L-D-RA, datasheets/connectors/SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf:
    length 6 x 1.27 + 6.35 = 13.97 (sheet 1), body 5.08 on 0.51 ribs, 5.33 deep,
    mouth centre 3.05 up (section C-C), the far (odd) row 1.26 + 1.27 behind the
    back face and the near row 1.26, tails 0.41 square 2.15 past the seating
    plane; the key in the wall on the board side (fig 2). The cavity's walls and
    the key's width are not dimensioned on the print [est]."""
    n, p = 6, 1.27
    back, depth = 2.53, 5.33
    y0, y1 = -3.81, 10.16
    yc = (y0 + y1) / 2
    zc = 3.05
    body = box(back, back + depth, y0, y1, 0.51, 0.51 + 5.08)
    ribs = fuse(box(back, back + depth, y0, y0 + 1.0, 0, 0.6), box(back, back + depth, y1 - 1.0, y1, 0, 0.6))
    cav = box(back + depth - 4.0, back + depth + 1, yc - 11.2 / 2, yc + 11.2 / 2, zc - 3.3 / 2, zc + 3.3 / 2)  # [est]
    key = box(back + depth - 4.0, back + depth + 1, yc - 1.0, yc + 1.0, 0, zc)                                 # [est] 2.0 wide
    body = cut(fuse(body, ribs), cav, key)
    tip = back + depth - 1.0                                              # [est]
    pins = []
    for k in range(n):
        y = k * p
        pins.append(rt_pin(0.0, y, zc + p / 2, tip, 0.41, 2.15))
        pins.append(rt_pin(p, y, zc - p / 2, tip, 0.41, 2.15))
    return [("body", body, BLACK), ("pins", fuse(*pins), GOLD)]


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


MODELS = {
    "XKB_X1270WR-2x12A-9TV01": xkb_x1270wr_2x12a_9tv01,
    "Samtec_SHF-106-01-L-D-RA": samtec_shf_106_01_l_d_ra,
    "Hanxia_HX_PZ2.54-1x8P_WZ": hanxia_pz254_1x8p_wz,
    "NXP_Case1351-01_MPXV4006DP": nxp_case_1351_01,
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
    """Any STEP model rewritten as an ASSEMBLY of one part per colour, each part the
    faces that colour covers - what kicad-cli's GLB export needs to carry a model's
    colours (write(), above). KiCad's own library models put their colours on the
    faces of one solid, and reach the GLB uncoloured. A model that is already an
    assembly is copied as it is. The faces keep their geometry and placement; the
    solids are not kept as solids (a render does not need them)."""
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopoDS import TopoDS_Compound
    from OCP.BRep import BRep_Builder
    import shutil
    doc = read_xcaf(src)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    free = children(st.BaseLabel())
    if any(st.IsAssembly_s(L) for L in free):
        shutil.copyfile(src, dst)
        return "copied (already an assembly)"
    groups = {}

    def faces(shape):
        e = TopExp_Explorer(shape, TopAbs_FACE)
        while e.More():
            yield e.Current(); e.Next()

    for L in free:
        base = label_colour(L)
        own = {}                      # face -> colour, from the label's coloured sub-shapes
        for k in children(L):
            if st.IsSubShape_s(k) and label_colour(k):
                for f in faces(st.GetShape_s(k)):
                    own.setdefault(hash(f), []).append((f, label_colour(k)))
        for f in faces(st.GetShape_s(L)):
            hit = next((c for g, c in own.get(hash(f), []) if g.IsSame(f)), None)
            groups.setdefault(hit or base, []).append(f)
    out = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    ost = XCAFDoc_DocumentTool.ShapeTool_s(out.Main())
    oct_ = XCAFDoc_DocumentTool.ColorTool_s(out.Main())
    asm = ost.NewShape()
    name = os.path.splitext(os.path.basename(dst))[0]
    TDataStd_Name.Set_s(asm, TCollection_ExtendedString(name))
    for i, (rgb, fs) in enumerate(sorted(groups.items(), key=lambda kv: (kv[0] is None, kv[0] or ()))):
        b, comp = BRep_Builder(), TopoDS_Compound()
        b.MakeCompound(comp)
        for f in fs:
            b.Add(comp, f)
        lab = ost.AddShape(comp, False)
        TDataStd_Name.Set_s(lab, TCollection_ExtendedString(f"{name}_{i}"))
        if rgb:
            oct_.SetColor(lab, Quantity_Color(*rgb, Quantity_TOC_RGB), XCAFDoc_ColorSurf)
        ost.AddComponent(asm, lab, TopLoc_Location())
    ost.UpdateAssemblies()
    save(out, name, dst)
    return f"{len(groups)} colour(s)" + (", some faces uncoloured" if None in groups else "")


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--assembly":
        print(as_assembly(sys.argv[2], sys.argv[3]))
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
