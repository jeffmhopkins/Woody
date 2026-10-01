#!/usr/bin/env python3
"""
The Eurorack module's PANEL ARTWORK (ADR 0026), generated from the CAD.

    python3 tools/panel-art.py --check            # lay it out, run every rule, print the report
    python3 tools/panel-art.py --out <file>       # write one product (tools/cad.py does this)

Never run `--out` into mechanical/module/art/ by hand: those files are
ledgered outputs of `python3 tools/cad.py build`, and `check` fails on a file
the ledger did not see built.

WHAT IT READS - nothing else, and it says so (`READ:` lines, which cad.py
cross-checks against the spec's `inputs`):
    config/module.yaml                     art.* - inks, font, sizes, words, floors
    mechanical/module/export/panel-art.echo  every zone's POSITION, every keep-out,
                                           from module.scad (part="art"), DRC-checked there
    mechanical/module/export/panel.dxf       the cut, for the CUT layer and the
                                           print-to-cut pull-back
    datasheets/fonts/Inter-*.ttf             the typeface, set to outlines

WHAT IT WRITES, by the name of --out:
    panel-art.svg            the master: Inkscape layers CUT (non-printing),
                             UNDERBASE, SLATE, BAR, WHITE; text as outlines
    panel-art.pdf            the print file: 1:1, one optional-content layer per
                             ink, each a named Separation (spot) colour with a
                             CMYK alternate; overprint on, so the plates stay
                             separate; CUT and a PREVIEW of the anodise are
                             non-printing. Schaeffer takes PDF, not SVG.
    panel-art.png            the proof picture (stamped by cad.py)
    panel-art-check.txt      the placement report - every item, its zone, its air
    tex-albedo.png, tex-roughness.png, tex-height.png
                             the rasters the Blender scene maps onto the panel,
                             art.texture.px_mm per mm, (0,0)-(W,H) -> (0,0)-(1,1)

THE RULES it enforces, and FAILS on (the spec's check-list, ADR 0026):
    every text's ink inside its CAD zone; every print >= art.min.print_cut from
    any cut; no text on a nut, a washer's reach, a knob budget or a plug grip;
    font size >= art.min.text; stem >= art.min.stroke (knocked-out text
    >= art.min.stroke_knockout), the stem measured off the banked font's `l`;
    contrast >= art.min.contrast (WCAG 2.1) for every ink a word is read
    against; a pill's knocked-out word art.text_pad inside its ends; every
    word but the name and the maker line on an island (those two off it);
    two words sharing a zone art.word_gap apart.
"""
import argparse
import colorsys
import io
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zlib

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = "config/module.yaml"
ECHO = "mechanical/module/export/panel-art.echo"
DXF = "mechanical/module/export/panel.dxf"

INKS = ["UNDERBASE", "SLATE", "BAR", "WHITE"]       # print order, bottom up
EPS = 1e-6


def rd(path):
    print(f"READ: {path}")
    return os.path.join(ROOT, path)


# ------------------------------------------------------------------ inputs ----

def leaf(node, dotted):
    for k in dotted.split("."):
        node = node[k]
    return node["value"]


def load_art():
    cfg = yaml.safe_load(open(rd(CONFIG), encoding="utf-8"))
    a = cfg["art"]
    get = lambda d: leaf(a, d)
    return get, cfg


def load_echo():
    zones, keep, parts, size = {}, [], {}, None
    for line in open(rd(ECHO), encoding="utf-8"):
        m = re.match(r'ECHO: "PANEL", (.*)$', line.strip())
        if not m:
            continue
        f = eval("[" + m.group(1).replace("true", "True").replace("false", "False") + "]")
        if f[0] == "size":
            size = f[1:4]
        elif f[0] == "zone":
            zones[f[1]] = {"rect": tuple(f[2:6]), "kind": f[6]}
        elif f[0] == "keepout":
            keep.append((f[1], f[2], f[3:]))
        elif f[0] == "part":
            parts[f[1]] = f[2:]
    if size is None:
        raise SystemExit(f"panel-art: {ECHO} has no size line - rebuild it (cad.py build module-art-echo)")
    return size, zones, keep, parts


def load_cut():
    import ezdxf
    from shapely.geometry import LineString
    from shapely.ops import polygonize
    doc = ezdxf.readfile(rd(DXF))
    lines = [LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
             for e in doc.modelspace() if e.dxftype() == "LINE"]
    faces = list(polygonize(lines))
    if not faces:
        raise SystemExit(f"panel-art: no closed outline in {DXF}")
    panel = max(faces, key=lambda f: f.area)      # the outline, with every cut as a hole
    return panel


# -------------------------------------------------------------------- type ----

class Face:
    """One banked TTF: glyph outlines as shapely polygons in em units, advances, pair kerning."""

    def __init__(self, path):
        from fontTools.ttLib import TTFont
        self.path = path
        self.f = TTFont(rd(path))
        self.upm = self.f["head"].unitsPerEm
        self.cmap = self.f.getBestCmap()
        self.gs = self.f.getGlyphSet()
        self.hmtx = self.f["hmtx"]
        self.asc = self.f["hhea"].ascent / self.upm
        self.desc = self.f["hhea"].descent / self.upm        # negative
        self.xh = self.f["OS/2"].sxHeight / self.upm
        self._kern = self._load_kern()
        self._cache = {}
        self.stem = self.glyph_poly("l").bounds[2] - self.glyph_poly("l").bounds[0]

    def _load_kern(self):
        """GPOS 'kern' pair adjustments (PairPos formats 1 and 2), in font units."""
        pairs, classes = {}, []
        if "GPOS" not in self.f:
            return (pairs, classes)
        g = self.f["GPOS"].table
        idx = set()
        for fr in g.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                idx.update(fr.Feature.LookupListIndex)
        for i in sorted(idx):
            lk = g.LookupList.Lookup[i]
            for st in lk.SubTable:
                if lk.LookupType == 9:
                    st = st.ExtSubTable
                if getattr(st, "LookupType", 2) != 2 and lk.LookupType not in (2, 9):
                    continue
                if not hasattr(st, "Format"):
                    continue
                cov = st.Coverage.glyphs
                if st.Format == 1:
                    for gi, ps in zip(cov, st.PairSet):
                        for pvr in ps.PairValueRecord:
                            v = getattr(pvr.Value1, "XAdvance", 0) or 0
                            if v:
                                pairs.setdefault((gi, pvr.SecondGlyph), v)
                elif st.Format == 2:
                    classes.append((set(cov), st.ClassDef1.classDefs, st.ClassDef2.classDefs, st.Class1Record))
        return (pairs, classes)

    def kern(self, a, b):
        pairs, classes = self._kern
        if (a, b) in pairs:
            return pairs[(a, b)]
        for cov, c1, c2, recs in classes:
            if a in cov:
                v = getattr(recs[c1.get(a, 0)].Class2Record[c2.get(b, 0)].Value1, "XAdvance", 0) or 0
                if v:
                    return v
        return 0

    def glyph_name(self, ch):
        if ord(ch) not in self.cmap:
            raise SystemExit(f"panel-art: {self.path} has no glyph for {ch!r}")
        return self.cmap[ord(ch)]

    def glyph_poly(self, ch):
        """The glyph's filled outline, em units, even-odd from its contours."""
        from fontTools.pens.recordingPen import DecomposingRecordingPen
        from shapely.geometry import Polygon
        if ch in self._cache:
            return self._cache[ch]
        pen = DecomposingRecordingPen(self.gs)   # composites (i, j: a dotless stem and a dot) drawn whole
        self.gs[self.glyph_name(ch)].draw(pen)
        rings, cur, start = [], [], None
        step = 0.004 * self.upm        # flattening: ~0.01 mm at a 2.4 mm em

        def quad(p0, p1, p2):
            n = max(2, int(math.dist(p0, p1) + math.dist(p1, p2)) // int(step) + 2)
            return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                     (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
                    for t in (i / n for i in range(1, n + 1))]

        def cubic(p0, p1, p2, p3):
            n = max(2, int(math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)) // int(step) + 2)
            out = []
            for i in range(1, n + 1):
                t = i / n
                a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
            return out

        for op, args in pen.value:
            if op == "moveTo":
                cur, start = [args[0]], args[0]
            elif op == "lineTo":
                cur.append(args[0])
            elif op == "qCurveTo":
                # TrueType: implied on-curve points between consecutive off-curve ones.
                pts = list(args)
                if pts[-1] is None:          # closed contour of off-curve points only
                    pts = pts[:-1]
                    on = ((pts[-1][0] + pts[0][0]) / 2, (pts[-1][1] + pts[0][1]) / 2)
                    cur, start = [on], on
                    pts = pts + [on]
                p0 = cur[-1]
                offs, end = pts[:-1], pts[-1]
                for k, c in enumerate(offs):
                    nxt = end if k == len(offs) - 1 else ((c[0] + offs[k + 1][0]) / 2, (c[1] + offs[k + 1][1]) / 2)
                    cur += quad(p0, c, nxt)
                    p0 = nxt
            elif op == "curveTo":
                cur += cubic(cur[-1], *args)
            elif op in ("closePath", "endPath"):
                if len(cur) >= 3:
                    rings.append(cur)
                cur = []
        poly = Polygon()
        for r in rings:
            p = Polygon([(x / self.upm, y / self.upm) for x, y in r]).buffer(0)
            poly = poly.symmetric_difference(p)
        self._cache[ch] = poly
        return poly

    def advance(self, ch):
        return self.hmtx[self.glyph_name(ch)][0] / self.upm


def set_line(face, s, size, tracking):
    """-> (MultiPolygon at the origin, baseline y 0, mm; advance width, mm)."""
    from shapely import affinity
    from shapely.geometry import MultiPolygon
    from shapely.ops import unary_union
    x, parts, prev = 0.0, [], None
    for ch in s:
        if prev is not None:
            x += face.kern(face.glyph_name(prev), face.glyph_name(ch)) / face.upm * size + tracking * size
        if ch != " ":
            g = face.glyph_poly(ch)
            if not g.is_empty:
                parts.append(affinity.translate(affinity.scale(g, size, size, origin=(0, 0)), x, 0))
        x += face.advance(ch) * size
        prev = ch
    geom = unary_union(parts) if parts else MultiPolygon()
    return geom, x


# ------------------------------------------------------------------- shapes ----

def rrect(x0, y0, x1, y1, r):
    from shapely.geometry import box
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=24)


def keep_shape(k):
    from shapely.geometry import Point, box
    name, kind, v = k
    return Point(v[0], v[1]).buffer(v[2], quad_segs=48) if kind == "c" else box(*v[:4])


# ------------------------------------------------------------------- colour ----

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lum(h):
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in hex_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def cmyk(h):
    r, g, b = hex_rgb(h)
    k = 1 - max(r, g, b)
    if k >= 1 - EPS:
        return (0, 0, 0, 1)
    return tuple(round(x, 4) for x in ((1 - r - k) / (1 - k), (1 - g - k) / (1 - k), (1 - b - k) / (1 - k), k))


# ------------------------------------------------------------------- layout ----

def layout():
    from shapely.geometry import box, Point
    from shapely.ops import unary_union
    get, cfg = load_art()
    (W, H, T), zones, keeps, parts = load_echo()
    panel = load_cut()
    low = (lambda s: s.lower()) if get("lowercase") else (lambda s: s)
    fonts = {"medium": Face(get("font.medium")), "semibold": Face(get("font.semibold"))}
    trk = get("tracking")
    size = {k: get(f"size.{k}") for k in ("title", "header", "label", "row", "small", "maker")}
    ink = {k: get(f"ink.{k}") for k in ("panel", "slate", "bar", "white")}
    art_in = get("island_r") / 2

    def Z(name):
        if name not in zones:
            raise SystemExit(f"panel-art: {ECHO} has no zone {name!r} - module.scad and this tool disagree")
        return zones[name]["rect"]

    items = []     # each: dict(name, zone, text, cls, weight, geom, adv, knockout)

    def place(name, zone, text, cls, weight="medium", h="center", v="middle", dx=0.0, baseline=None, tracking=None):
        f = fonts[weight]
        sz = size[cls]
        t = trk if tracking is None else tracking
        geom, adv = set_line(f, low(text), sz, t)
        x0, y0, x1, y1 = zone
        x = {"left": x0, "right": x1 - adv, "center": (x0 + x1) / 2 - adv / 2}[h] + dx
        if baseline is None:
            baseline = {"top": y1 - f.asc * sz, "bottom": y0 - f.desc * sz,
                        "middle": (y0 + y1) / 2 - (f.asc + f.desc) / 2 * sz}[v]
        from shapely import affinity
        g = affinity.translate(geom, x, baseline)
        it = dict(name=name, zone=zone, text=low(text), cls=cls, size=sz, weight=weight, geom=g,
                  x=x, adv=adv, baseline=baseline, knockout=False, face=f)
        items.append(it)
        return it

    # -- the name, on the frame between the top screws; the maker line under it, subdued
    it = place("name", Z("name"), get("text.title"), "title", "semibold", tracking=0.0)
    it["frame"] = True
    it = place("maker", Z("title"), get("text.maker"), "maker")
    it["frame"] = True
    it["ink"] = "BAR"
    # -- island A: header pill, knob labels, the OFFSET marks
    hdrs = []
    z = Z("header breath")
    hdrs.append(("header breath", rrect(*z, get("header_r"))))
    it = place("header breath", z, get("text.header_breath"), "header", "semibold")
    it["knockout"] = True
    it["pill"] = z
    pot_words = get("text.pots")
    for i, pz in enumerate(("POT-GAIN legend", "POT-OFFSET legend", "POT-RESP legend")):
        place(pz, Z(pz), pot_words[i], "label", v="top")
    marks = []
    bl, bw = get("mark.bar")
    for zname, sign in (("scale OFFSET-", -1), ("scale OFFSET+", 1)):
        x0, y0, x1, y1 = Z(zname)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        g = box(cx - bl / 2, cy - bw / 2, cx + bl / 2, cy + bw / 2)
        if sign > 0:
            g = g.union(box(cx - bw / 2, cy - bl / 2, cx + bw / 2, cy + bl / 2))
        marks.append(dict(name=zname, zone=(x0, y0, x1, y1), text="-" if sign < 0 else "+", cls="mark",
                          size=None, weight=None, geom=g, knockout=False, stroke=bw))
    # -- island B: every jack an output, each word knocked out of a BAR pill
    # filling its legend zone from the jack's side to art_in inside the island
    jw = get("text.jacks")
    jz = [["J-CV-PITCH legend", "J-CV-BREATH legend"], ["J-CV-MOD1 legend", "J-CV-MOD2 legend"], ["J-CV-MOD3 legend", "J-CV-MOD4 legend"]]
    isl = {n: zones[n]["rect"] for n in zones if zones[n]["kind"] == "island"}
    ix0, _, ix1, _ = isl["island B"]
    for r in range(3):
        for c in range(2):
            z = Z(jz[r][c])
            pz = (max(z[0], ix0 + art_in), z[1], z[2], z[3]) if c == 0 else (z[0], z[1], min(z[2], ix1 - art_in), z[3])
            hdrs.append((jz[r][c] + " pill", rrect(*pz, get("header_r"))))
            it = place(jz[r][c], pz, jw[r][c], "header", "semibold")
            it["knockout"] = True
            it["pill"] = pz
    # -- island C: the toggle's two words only - the LED, the switch's purpose
    # and the umbilical need none (the owner, 2026-10-01)
    z = Z("LED-PANEL legend")
    off, on = get("text.toggle")
    place("SW-POWER off", z, off, "row", h="right")
    place("SW-POWER on", Z("SW-POWER legend"), on, "row", h="left")

    # -- surfaces
    keep = panel.buffer(-get("min.print_cut"), quad_segs=24)          # where ink may be
    islands = unary_union([rrect(*r, get("island_r")) for r in isl.values()])
    pills = unary_union([p for _, p in hdrs])
    knock = unary_union([it["geom"] for it in items if it["knockout"]])
    bar_text = unary_union([it["geom"] for it in items if it.get("ink") == "BAR"])
    bar = pills.difference(knock).union(bar_text).intersection(keep)
    slate = islands.difference(pills).intersection(keep)
    white = unary_union([it["geom"] for it in items if not it["knockout"] and it.get("ink") is None] + [m["geom"] for m in marks])
    layers = {"UNDERBASE": slate.union(bar), "SLATE": slate, "BAR": bar, "WHITE": white}
    return dict(W=W, H=H, T=T, panel=panel, zones=zones, keeps=keeps, parts=parts, items=items, marks=marks,
                hdrs=hdrs, layers=layers, islands=islands, get=get, ink=ink, fonts=fonts, isl=isl,
                keep=keep)


# ------------------------------------------------------------------- checks ----

def checks(L):
    from shapely.geometry import box
    get, ink = L["get"], L["ink"]
    fails, rows = [], []
    cut = L["panel"].boundary
    hard = [(n, keep_shape((n, k, v))) for n, k, v in L["keeps"]
            if not n.startswith("NE8MX cable drop")]       # the drop zone is below text anyway; the grip is checked
    min_cut = get("min.print_cut")

    def fail(msg):
        fails.append(msg)

    for it in L["items"] + L["marks"]:
        g = it["geom"]
        x0, y0, x1, y1 = g.bounds
        zx0, zy0, zx1, zy1 = it["zone"]
        air = min(x0 - zx0, y0 - zy0, zx1 - x1, zy1 - y1)
        dcut = g.distance(cut) if L["panel"].contains(g) else -1
        near = min(((g.distance(s), n) for n, s in hard), default=(99, ""))
        stem = None
        if it.get("size"):
            stem = it["face"].stem * it["size"]
        elif it.get("stroke"):
            stem = it["stroke"]
        on_isl = L["islands"].contains(g)
        rows.append((it["name"], it["text"], it.get("size"), it.get("weight"), (x0, y0, x1, y1), air, dcut, near, stem, on_isl))
        if air < -EPS:
            fail(f"{it['name']}: '{it['text']}' leaves its zone by {-air:.3f} mm")
        if dcut < min_cut - EPS:
            fail(f"{it['name']}: '{it['text']}' is {dcut:.3f} mm from a cut, under art.min.print_cut {min_cut}")
        if near[0] <= EPS:
            fail(f"{it['name']}: '{it['text']}' overlaps {near[1]}")
        if it.get("size") is not None and it["size"] < get("min.text") - EPS:
            fail(f"{it['name']}: {it['size']} mm type, under art.min.text")
        floor = get("min.stroke_knockout") if it.get("knockout") else get("min.stroke")
        if stem is not None and stem < floor - EPS:
            fail(f"{it['name']}: stem {stem:.3f} mm, under {floor}")
        if it.get("frame"):
            if L["islands"].intersects(g):
                fail(f"{it['name']}: on an island - it belongs on the black frame")
        elif not it.get("knockout") and not on_isl:
            fail(f"{it['name']}: '{it['text']}' is not wholly on an island")
        if it.get("knockout"):
            px0, _, px1, _ = it["pill"]
            if x0 - px0 < get("text_pad") - EPS or px1 - x1 < get("text_pad") - EPS:
                fail(f"{it['name']}: header text within art.text_pad of its pill's end")
    # two words in one zone
    words = L["items"]
    for i in range(len(words)):
        for j in range(i + 1, len(words)):
            if words[i]["zone"] == words[j]["zone"]:
                d = words[i]["geom"].distance(words[j]["geom"])
                gap = get("word_gap") if words[i]["baseline"] == words[j]["baseline"] else get("line_gap")
                if d < gap * 0.5 - EPS:
                    fail(f"{words[i]['name']} / {words[j]['name']}: {d:.3f} mm apart")
    # contrast
    pairs = [("WHITE on SLATE", ink["white"], ink["slate"]), ("WHITE on the anodise", ink["white"], ink["panel"]),
             ("the anodise through BAR (knockout)", ink["panel"], ink["bar"]),
             ("BAR on the anodise (the maker line)", ink["bar"], ink["panel"])]
    cons = [(n, contrast(a, b)) for n, a, b in pairs]
    for n, c in cons:
        if c < get("min.contrast") - EPS:
            fail(f"contrast {n}: {c:.2f}:1, under {get('min.contrast')}")
    # every ink pulled back from every cut
    for name, g in L["layers"].items():
        if g.is_empty:
            continue
        d = g.distance(L["panel"].boundary) if L["panel"].contains(g) else -1
        if d < min_cut - 1e-3:
            fail(f"ink {name}: {d:.3f} mm from a cut")
    return fails, rows, cons


def report(L, fails, rows, cons):
    get = L["get"]
    out = ["# Panel artwork - placement report. GENERATED by tools/panel-art.py (ADR 0026).",
           f"# Zones: {ECHO}; cut: {DXF}; words, inks and floors: {CONFIG} art.*",
           f"# Font: {get('font.medium')} / {get('font.semibold')}; stem off the font's 'l': "
           f"medium {L['fonts']['medium'].stem:.4f} em, semibold {L['fonts']['semibold'].stem:.4f} em", ""]
    out.append(("PASS" if not fails else f"FAIL {len(fails)}") + " - every rule in the tool's docstring")
    out += ["  " + f for f in fails]
    out += ["", "item | text | type mm | ink box x0 y0 x1 y1 | air in zone | to a cut | nearest keep-out | stem mm | on island"]
    for n, t, sz, w, bb, air, dcut, near, stem, isl in rows:
        out.append(f"{n} | {t} | {sz if sz else '-'} {w or ''} | {bb[0]:.2f} {bb[1]:.2f} {bb[2]:.2f} {bb[3]:.2f} | "
                   f"{air:.2f} | {dcut:.2f} | {near[0]:.2f} {near[1]} | {stem:.3f} | {'yes' if isl else 'no'}")
    out += ["", "pills (BAR, words knocked out): x0 y0 x1 y1"]
    for it in L["items"]:
        if it.get("pill"):
            r = it["pill"]
            out.append(f"{it['name']} | {it['text']} | {r[0]:.2f} {r[1]:.2f} {r[2]:.2f} {r[3]:.2f} | {r[2] - r[0]:.2f} x {r[3] - r[1]:.2f}")
    out += ["", "contrast (WCAG 2.1, preview colours)"]
    out += [f"{n} | {c:.2f}:1" for n, c in cons]
    out += ["", "ink areas, mm^2"] + [f"{k} | {g.area:.1f}" for k, g in L["layers"].items()]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------- output ----

def rings(g):
    polys = [g] if g.geom_type == "Polygon" else list(getattr(g, "geoms", []))
    for p in polys:
        if p.is_empty:
            continue
        yield list(p.exterior.coords)
        for r in p.interiors:
            yield list(r.coords)


def svg_path(g, H):
    d = []
    for r in rings(g):
        d.append("M" + " L".join(f"{x:.4f},{H - y:.4f}" for x, y in r[:-1]) + " Z")
    return " ".join(d)


def svg(L, fills, show_cut=True, bg=None, holes=None, only=None):
    W, H = L["W"], L["H"]
    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
         f'width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
         f'<title>Woody module panel artwork - ADR 0026 - generated by tools/panel-art.py</title>']
    if bg:
        o.append(f'<g inkscape:groupmode="layer" inkscape:label="PREVIEW (non-printing)" id="PREVIEW">'
                 f'<path d="{svg_path(L["panel"], H)}" fill="{bg}" fill-rule="evenodd"/></g>')
    for name in INKS:
        if only is not None and name not in only:
            continue
        if name not in fills:
            continue
        g = L["layers"][name]
        o.append(f'<g inkscape:groupmode="layer" inkscape:label="{name}" id="{name}">'
                 f'<path d="{svg_path(g, H)}" fill="{fills[name]}" fill-rule="evenodd"/></g>')
    if holes:
        from shapely.geometry import box
        o.append(f'<path d="{svg_path(box(0, 0, W, H).difference(L["panel"]), H)}" fill="{holes}" fill-rule="evenodd"/>')
    if show_cut:
        o.append('<g inkscape:groupmode="layer" inkscape:label="CUT (non-printing)" id="CUT">'
                 f'<path d="{svg_path(L["panel"], H)}" fill="none" stroke="#FF00FF" stroke-width="0.05"/></g>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def pdf(L):
    """A minimal PDF 1.6: one page at 1:1, one optional-content group per ink,
    each ink a Separation colour space with a CMYK alternate, overprint on."""
    W, H, ink = L["W"], L["H"], L["ink"]
    k = 72 / 25.4
    spot = {"UNDERBASE": "#FFFFFF", "SLATE": ink["slate"], "BAR": ink["bar"], "WHITE": ink["white"]}
    alt = {n: cmyk(h) for n, h in spot.items()}
    alt["UNDERBASE"] = (0.1, 0.0, 0.0, 0.0)      # a visible tint for a viewer; the plate is the underbase
    alt["WHITE"] = (0.0, 0.0, 0.0, 0.0)
    objs = []

    def add(b):
        objs.append(b if isinstance(b, bytes) else b.encode())
        return len(objs)

    def path_ops(g):
        ops = []
        for r in rings(g):
            ops.append(f"{r[0][0]:.4f} {r[0][1]:.4f} m " + " ".join(f"{x:.4f} {y:.4f} l" for x, y in r[1:-1]) + " h")
        return "\n".join(ops)

    names = ["PREVIEW (non-printing)"] + INKS + ["CUT (non-printing)"]
    ocg = {}
    for n in names:
        usage = " /Usage << /Print << /PrintState /OFF >> /View << /ViewState /ON >> >>" if "non-printing" in n else ""
        ocg[n] = add(f"<< /Type /OCG /Name ({n}){usage} >>")
    fn = {n: add(f"<< /FunctionType 2 /Domain [0 1] /C0 [0 0 0 0] /C1 [{' '.join(str(c) for c in alt[n])}] /N 1 >>") for n in INKS}
    cs = {n: add(f"[/Separation /{n} /DeviceCMYK {fn[n]} 0 R]") for n in INKS}
    gs_op = add("<< /Type /ExtGState /OP true /op true /OPM 1 >>")
    body = [f"{k:.6f} 0 0 {k:.6f} 0 0 cm"]
    pr = hex_rgb(ink["panel"])
    body.append(f"/OC /L0 BDC {pr[0]:.4f} {pr[1]:.4f} {pr[2]:.4f} rg {path_ops(L['panel'])} f* EMC")
    for i, n in enumerate(INKS):
        g = L["layers"][n]
        if g.is_empty:
            continue
        body.append(f"/OC /L{i + 1} BDC /GS0 gs /CS{i} cs 1 scn {path_ops(g)} f* EMC")
    body.append(f"/OC /L{len(INKS) + 1} BDC 1 0 1 RG 0.05 w {path_ops(L['panel'])} S EMC")
    stream = zlib.compress("\n".join(body).encode(), 9)
    content = add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(stream) + stream + b"\nendstream")
    props = " ".join(f"/L{i} {ocg[n]} 0 R" for i, n in enumerate(names))
    res = (f"<< /ColorSpace << {' '.join(f'/CS{i} {cs[n]} 0 R' for i, n in enumerate(INKS))} >> "
           f"/ExtGState << /GS0 {gs_op} 0 R >> /Properties << {props} >> >>")
    pages_n = len(objs) + 2
    page = add(f"<< /Type /Page /Parent {pages_n} 0 R /MediaBox [0 0 {W * k:.4f} {H * k:.4f}] "
               f"/TrimBox [0 0 {W * k:.4f} {H * k:.4f}] /Contents {content} 0 R /Resources {res} >>")
    add(f"<< /Type /Pages /Kids [{page} 0 R] /Count 1 >>")
    refs = " ".join(f"{ocg[n]} 0 R" for n in names)
    off = " ".join(f"{ocg[n]} 0 R" for n in names if "non-printing" in n)
    info = add("<< /Title (Woody module panel artwork - ADR 0026) /Creator (tools/panel-art.py) >>")
    cat = add(f"<< /Type /Catalog /Pages {pages_n} 0 R /OCProperties << /OCGs [{refs}] "
              f"/D << /Order [{refs}] /AS [<< /Event /Print /OCGs [{off}] /Category [/Print] >>] >> >> >>")
    out = io.BytesIO()
    out.write(b"%PDF-1.6\n%\xe2\xe3\xcf\xd3\n")
    xref = []
    for i, b in enumerate(objs, 1):
        xref.append(out.tell())
        out.write(b"%d 0 obj\n" % i + b + b"\nendobj\n")
    x = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1))
    for p in xref:
        out.write(b"%010d 00000 n \n" % p)
    out.write(b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, cat, info, x))
    return out.getvalue()


def rasterise(svg_text, out, px_w, px_h):
    rsvg = shutil.which("rsvg-convert")
    if not rsvg:
        raise SystemExit("panel-art: rsvg-convert is needed for the rasters (apt install librsvg2-bin)")
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f:
        f.write(svg_text)
        name = f.name
    try:
        subprocess.run([rsvg, "-w", str(px_w), "-h", str(px_h), "-o", out, name], check=True)
    finally:
        os.unlink(name)
    from PIL import Image
    im = Image.open(out)
    im.load()
    im.save(out, optimize=True)


def grey(v):
    c = max(0, min(255, round(v * 255)))
    return f"#{c:02X}{c:02X}{c:02X}"


def tool_line():
    import fontTools
    import shapely
    r = subprocess.run(["rsvg-convert", "--version"], capture_output=True, text=True)
    return f"TOOL: panel-art.py; fontTools {fontTools.version}; shapely {shapely.__version__}; {r.stdout.strip()}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out")
    ap.add_argument("--fingerprint", default="")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not a.out and not a.check:
        ap.print_help()
        return 2
    L = layout()
    fails, rows, cons = checks(L)
    rep = report(L, fails, rows, cons)
    if a.check:
        print(rep)
        return 1 if fails else 0
    if fails:
        print(rep)
        raise SystemExit(f"panel-art: {len(fails)} placement rule(s) fail - nothing written")
    get, ink = L["get"], L["ink"]
    out = a.out
    base = os.path.basename(out)
    W, H = L["W"], L["H"]
    pxmm = get("texture.px_mm")
    fills = {"SLATE": ink["slate"], "BAR": ink["bar"], "WHITE": ink["white"]}
    if base.endswith("-check.txt"):
        open(out, "w", encoding="utf-8", newline="\n").write(rep)
    elif out.endswith(".svg"):
        master = dict(fills, UNDERBASE="#FFFFFF")
        s = svg(L, master, show_cut=True).replace('id="UNDERBASE">', 'id="UNDERBASE" style="display:none">')
        open(out, "w", encoding="utf-8", newline="\n").write(s)
    elif out.endswith(".pdf"):
        open(out, "wb").write(pdf(L))
    elif base == "tex-albedo.png":
        rasterise(svg(L, fills, show_cut=False, bg=ink["panel"]), out, round(W * pxmm), round(H * pxmm))
    elif base == "tex-roughness.png":
        r = grey(get("texture.rough_ink"))
        rasterise(svg(L, {"SLATE": r, "BAR": r, "WHITE": r}, show_cut=False, bg=grey(get("texture.rough_panel"))),
                  out, round(W * pxmm), round(H * pxmm))
    elif base == "tex-height.png":
        # 0 = the anodise, 0.5 = one layer of ink over the underbase, 1 = WHITE on SLATE.
        rasterise(svg(L, {"UNDERBASE": grey(0.5), "WHITE": grey(1.0)}, show_cut=False, bg="#000000"),
                  out, round(W * pxmm), round(H * pxmm))
        from PIL import Image
        im = Image.open(out).convert("L")
        im.save(out, optimize=True)
    elif out.endswith(".png"):
        # The proof: the inks on the anodise, the cuts shown light, at 20 px/mm.
        rasterise(svg(L, fills, show_cut=False, bg=ink["panel"], holes="#C8C8CC"), out, round(W * 20), round(H * 20))
    else:
        raise SystemExit(f"panel-art: do not know how to make {base}")
    print(tool_line())
    return 0


if __name__ == "__main__":
    sys.exit(main())
