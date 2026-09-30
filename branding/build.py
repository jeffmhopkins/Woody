#!/usr/bin/env python3
"""Space Coast Synthesizers orbit-wave mark: the single source for every file in export/.

The mark is defined once, in SPEC below, and built as filled polygons in millimetres
(no strokes, no fonts), so every export is the same geometry:

    export/scs-orbit-wave-mark.svg      production artwork, exact size, black = etched area
    export/scs-orbit-wave-mark.dxf      the same outlines as closed polylines, mm
    export/spec.json                    the numbers below plus the measured result
    export/png/scs-mark-{black,white}.png   transparent PNGs for screens and documents
    export/print/scs-mark-test-print-100pct.pdf   Letter, print at 100 %
    export/renders/*.png                simulated laser etch, and epoxy colour fill, on procedural wood

Run:  python3 branding/build.py        (requirements: branding/requirements.txt)
Output is deterministic: an unchanged SPEC rebuilds byte-identical files, so a diff
under export/ always means the mark changed.

Do not edit anything under export/ by hand; change SPEC and rebuild.
"""
import json
import math as M
import os
import sys
from pathlib import Path

# ezdxf writes its CLASS table in set-iteration order, which follows Python's per-process
# hash randomisation: without a fixed seed the DXF reorders between runs. The seed can only
# be set before the interpreter starts, so re-launch once with it pinned.
if __name__ == "__main__" and os.environ.get("PYTHONHASHSEED") != "0":
    os.execve(sys.executable, [sys.executable, *sys.argv], {**os.environ, "PYTHONHASHSEED": "0"})

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
OUT = HERE / "export"

SPEC = dict(
    ring_centre_radius=18.0,     # ring centreline radius, mm
    ring_width=3.6,              # ring band width, mm
    wave_width=2.8,              # wave width at full body, mm
    wave_amplitude=6.2,          # sine amplitude, mm
    wave_cycle_half_span=23.5,   # one sine cycle spans +-this, zero crossing at the ring centre
    wave_half_length=27.0,       # tails are drawn to +-this: tip to tip is twice it
    taper_length=9.0,            # brush lift: width eases to a point over this arc length at each end
    taper_profile=0.8,           # width ~ sin(pi/2 * s/taper_length) ** profile
    wave_gap=2.0,                # clear space around the wave where it crosses the ring
    moon_gap=2.0,                # clear space around the moon
    moon_radius=3.76,            # mm
    moon_angle_deg=-122.0,       # moon position on the ring centreline; 0 = right, negative = up
)
# Colour-fill scheme for dark woods: the etch is filled with pigmented epoxy and sanded flush.
EPOXY = dict(wave=(252, 76, 2), moon=(252, 76, 2), ring=(18, 18, 20))   # orange, orange, black

PANEL_WIDTH = 57.0   # top panel width the mark is laid out for, mm (render and test print only)


# --------------------------------------------------------------------------- geometry
def wave_centre(n=2000):
    h, b, a = SPEC["wave_half_length"], SPEC["wave_cycle_half_span"], SPEC["wave_amplitude"]
    pts = []
    for i in range(n + 1):
        x = -h + 2 * h * i / n
        pts.append((x, -a * M.sin(2 * M.pi * ((x + b) / (2 * b) - 0.5))))
    return pts


def wave_polygon():
    """Variable-width stroke: full width in the body, easing to a point at both ends."""
    P = wave_centre()
    L = [0.0]
    for i in range(1, len(P)):
        L.append(L[-1] + M.dist(P[i], P[i - 1]))
    tot = L[-1]
    left, right = [], []
    for i, (x, y) in enumerate(P):
        j0, j1 = max(i - 1, 0), min(i + 1, len(P) - 1)
        tx, ty = P[j1][0] - P[j0][0], P[j1][1] - P[j0][1]
        tn = M.hypot(tx, ty)
        tx, ty = tx / tn, ty / tn
        u = min(1.0, L[i] / SPEC["taper_length"], (tot - L[i]) / SPEC["taper_length"])
        w = SPEC["wave_width"] * M.sin(M.pi / 2 * u) ** SPEC["taper_profile"] / 2
        left.append((x - ty * w, y + tx * w))
        right.append((x + ty * w, y - tx * w))
    return Polygon(left + right[::-1]).buffer(0)


def build_mark():
    R, rw = SPEC["ring_centre_radius"], SPEC["ring_width"]
    ring = Point(0, 0).buffer(R + rw / 2, resolution=256).difference(
        Point(0, 0).buffer(R - rw / 2, resolution=256))
    a = M.radians(SPEC["moon_angle_deg"])
    mc = (R * M.cos(a), R * M.sin(a))
    moon = Point(*mc).buffer(SPEC["moon_radius"], resolution=128)
    moon_clear = Point(*mc).buffer(SPEC["moon_radius"] + SPEC["moon_gap"], resolution=128)
    wave = wave_polygon()
    wave_clear = wave.buffer(SPEC["wave_gap"], resolution=64)   # true offset of the real outline
    mark = unary_union([ring.difference(wave_clear).difference(moon_clear), wave, moon])
    # origin at the top-left of the bounding box, y down (SVG convention)
    minx, miny, _, _ = mark.bounds
    from shapely import affinity
    return affinity.translate(mark, -minx, -miny)


def parts(g):
    return list(g.geoms) if hasattr(g, "geoms") else [g]


def rings_of(g):
    for p in parts(g):
        yield list(p.exterior.coords)
        for h in p.interiors:
            yield list(h.coords)


# --------------------------------------------------------------------------- vector exports
def write_svg(mark, path):
    _, _, W, H = mark.bounds
    d = " ".join("M" + " L".join(f"{x:.4f},{y:.4f}" for x, y in r) + " Z" for r in rings_of(mark))
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<!-- Space Coast Synthesizers orbit-wave mark. {W:.2f} x {H:.2f} mm. "
        "Filled outlines only; black = etched area. Generated by branding/build.py. -->\n"
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.3f}mm" height="{H:.3f}mm" '
        f'viewBox="0 0 {W:.4f} {H:.4f}">\n'
        f'<path fill="#000" fill-rule="evenodd" d="{d}"/>\n</svg>\n')


def write_dxf(mark, path):
    import ezdxf
    ezdxf.options.write_fixed_meta_data_for_testing = True   # no timestamps: deterministic output
    _, _, _, H = mark.bounds
    doc = ezdxf.new(units=ezdxf.units.MM)
    msp = doc.modelspace()
    for r in rings_of(mark):
        msp.add_lwpolyline([(x, H - y) for x, y in r], close=True)   # DXF is y-up
    doc.saveas(path)


# --------------------------------------------------------------------------- raster
def rasterize(mark, ppmm, W=None, H=None, ox=0.0, oy=0.0, ss=4):
    """Anti-aliased coverage mask (0..1) of the mark at ppmm pixels per mm."""
    _, _, mw, mh = mark.bounds
    W = W or mw
    H = H or mh
    big = Image.new("L", (int(round(W * ppmm * ss)), int(round(H * ppmm * ss))), 0)
    dr = ImageDraw.Draw(big)
    k = ppmm * ss
    for p in parts(mark):
        dr.polygon([((x + ox) * k, (y + oy) * k) for x, y in p.exterior.coords], fill=255)
        for h in p.interiors:
            dr.polygon([((x + ox) * k, (y + oy) * k) for x, y in h.coords], fill=0)
    small = big.resize((big.width // ss, big.height // ss), Image.LANCZOS)
    return np.asarray(small).astype(float) / 255


def write_pngs(mark, folder, width_px=2000):
    _, _, W, _ = mark.bounds
    m = rasterize(mark, width_px / W)
    for name, rgb in (("black", (0, 0, 0)), ("white", (255, 255, 255))):
        a = np.dstack([np.full(m.shape, c, np.uint8) for c in rgb] + [(m * 255).astype(np.uint8)])
        Image.fromarray(a, "RGBA").save(folder / f"scs-mark-{name}.png", optimize=True)


# --------------------------------------------------------------------------- procedural wood
def fbm(h, w, cell_y, cell_x, octaves, rng, gain=0.5):
    """Anisotropic fractal value noise, roughly -1..1. cell sizes in pixels."""
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for _ in range(octaves):
        gy, gx = max(2, int(h / cell_y) + 2), max(2, int(w / cell_x) + 2)
        g = Image.fromarray(rng.uniform(-1, 1, (gy, gx)).astype(np.float32), "F")
        out += amp * np.asarray(g.resize((w, h), Image.BICUBIC))
        tot += amp
        amp *= gain
        cell_y, cell_x = cell_y / 2, cell_x / 2
    return out / tot


WOODS = {
    # base/zone: the ground colour and its slow darker zones; line: the figure lines;
    # line_*: spacing (mm), width (mm) and strength of the two line families; warp in line periods
    "bocote": dict(base=(210, 154, 72), zone=(150, 98, 44), zone_amt=0.35, line=(48, 29, 16),
                   fam=[(1.1, 0.14, 0.9), (2.7, 0.30, 0.95), (6.5, 0.6, 0.72)], warp=0.9, eye=0.25,
                   pores=0.25, etch=(40, 25, 15), seed=7),
    "dark-walnut": dict(base=(96, 62, 42), zone=(62, 39, 26), zone_amt=0.6, line=(45, 28, 19),
                        fam=[(0.9, 0.10, 0.35), (2.6, 0.35, 0.45)], warp=0.8, eye=0.15,
                        pores=0.45, etch=(20, 13, 9), seed=11),
    "dark-oak": dict(base=(84, 56, 36), zone=(52, 34, 22), zone_amt=0.55, line=(34, 22, 14),
                     fam=[(0.8, 0.12, 0.45), (2.4, 0.5, 0.55), (5.5, 0.9, 0.35)], warp=1.2, eye=0.35,
                     pores=0.7, etch=(18, 12, 8), seed=21),
}
BURN_RENDERS = ("bocote", "dark-walnut")          # plain laser etch
EPOXY_RENDERS = ("dark-oak", "dark-walnut")       # colour-filled, see EPOXY


def wood(kind, w, h, ppmm):
    """Straight-grain figure seen on a flat-sawn face, grain running down the image."""
    P = WOODS[kind]
    rng = np.random.default_rng(P["seed"])
    x = np.arange(w)[None, :] / ppmm
    warp_slow = fbm(h, w, 70 * ppmm, 12 * ppmm, 4, rng)
    warp_eye = fbm(h, w, 34 * ppmm, 9 * ppmm, 3, rng)
    tone = np.clip(0.5 + 0.9 * fbm(h, w, 45 * ppmm, 6 * ppmm, 4, rng), 0, 1)
    img = (np.array(P["base"])[None, None, :] * (1 - P["zone_amt"] * tone[..., None])
           + np.array(P["zone"])[None, None, :] * (P["zone_amt"] * tone[..., None]))
    lines = np.zeros((h, w))
    for period, width, strength in P["fam"]:
        ph = x / period + P["warp"] * warp_slow + P["eye"] * warp_eye + rng.uniform(0, 1)
        d = np.abs(ph - np.round(ph)) * period                               # mm to nearest line
        wv = width * (0.35 + 1.3 * np.clip(0.5 + fbm(h, w, 25 * ppmm, 4 * ppmm, 3, rng), 0, 1))
        if width < 0.5:   # fine figure lines: soft profile
            v = np.clip(1 - d / wv, 0, 1) ** 0.6
        else:             # broad bands: flat fill with a crisp ~0.1 mm edge, like real figure
            v = np.clip((wv - d) / 0.1, 0, 1)
        lines = np.maximum(lines, strength * v)
    img = img * (1 - lines[..., None]) + np.array(P["line"])[None, None, :] * lines[..., None]
    # pores: short dark streaks along the grain
    seeds = (rng.uniform(0, 1, (max(1, h // 10), w)) > 0.975).astype(np.float32) * 255
    streak = np.asarray(Image.fromarray(seeds.astype(np.uint8)).resize((w, h), Image.BILINEAR)
                        .filter(ImageFilter.GaussianBlur(0.5))).astype(float) / 255
    img *= 1 - P["pores"] * np.clip(streak * 3, 0, 1)[..., None]
    # fibre texture and a soft finish sheen
    img *= 1 + 0.04 * fbm(h, w, 3 * ppmm, 0.3 * ppmm, 2, rng)[..., None]
    yy, xx = np.mgrid[0:h, 0:w]
    sheen = np.exp(-(((xx - 0.3 * w) * 0.7 + (yy - 0.25 * h) * 0.3) / (0.35 * w)) ** 2)
    img = img * (1 + 0.08 * sheen[..., None]) + 8 * sheen[..., None]
    return np.clip(img, 0, 255), rng


def etch_onto(img, mask, kind, rng, ppmm):
    P = WOODS[kind]
    m = mask[..., None]
    halo = np.asarray(Image.fromarray((mask * 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(ppmm * 0.3))).astype(float)[..., None] / 255
    char = np.array(P["etch"])[None, None, :] * (1 + 0.12 * rng.normal(0, 1, img.shape[:2])[..., None])
    out = img * (1 - 0.25 * halo) * (1 - m) + char * m
    return np.clip(out, 0, 255).astype(np.uint8)


def split_mark(mark):
    """(wave, moon, [ring arcs]): the wave is the widest part, the moon the smallest."""
    ps = parts(mark)
    wave = max(ps, key=lambda p: p.bounds[2] - p.bounds[0])
    moon = min(ps, key=lambda p: p.area)
    return wave, moon, [p for p in ps if p is not wave and p is not moon]


def epoxy_onto(img, mask, rgb, ppmm, rng):
    """Flush, glossy pigmented fill: slight depth tint at the edges, a soft specular sheen
    (weaker on dark colours), and a thin charred rim left by the etch."""
    h, w = mask.shape
    rgb = np.array(rgb, float)
    m8 = Image.fromarray((mask * 255).astype(np.uint8))
    inner = np.asarray(m8.filter(ImageFilter.MinFilter(3))
                       .filter(ImageFilter.GaussianBlur(ppmm * 0.35))).astype(float) / 255
    col = rgb * (0.82 + 0.18 * inner[..., None])
    yy, xx = np.mgrid[0:h, 0:w]
    spec = np.exp(-(((xx - 0.35 * w) * 0.8 + (yy - 0.3 * h) * 0.6) / (0.22 * w)) ** 2)
    col = col + (255 - col) * (0.06 + 0.22 * rgb.mean() / 255) * spec[..., None] * inner[..., None]
    col = col * (1 + 0.02 * rng.normal(0, 1, (h, w)))[..., None]
    rim = np.clip(np.asarray(m8.filter(ImageFilter.MaxFilter(3))).astype(float) / 255 - mask, 0, 1)
    out = img * (1 - mask[..., None]) + col * mask[..., None]
    return np.clip(out * (1 - 0.55 * rim[..., None]), 0, 255)


def pair_image(tiles, gap):
    w, h = tiles[0].size
    out = Image.new("RGB", (len(tiles) * w + (len(tiles) - 1) * gap, h), (243, 241, 236))
    for i, t in enumerate(tiles):
        out.paste(t, (i * (w + gap), 0))
    return out


def write_renders(mark, folder, ppmm=16, panel_len=80.0):
    _, _, W, H = mark.bounds
    ox, oy = (PANEL_WIDTH - W) / 2, (panel_len - H) / 2
    w, h = int(PANEL_WIDTH * ppmm), int(panel_len * ppmm)
    mask = rasterize(mark, ppmm, PANEL_WIDTH, panel_len, ox, oy)[:h, :w]
    tiles = []
    for kind in BURN_RENDERS:
        img, rng = wood(kind, w, h, ppmm)
        tile = Image.fromarray(etch_onto(img, mask, kind, rng, ppmm))
        tile.save(folder / f"scs-mark-on-{kind}.png", optimize=True)
        tiles.append(tile)
    pair_image(tiles, int(4 * ppmm)).save(folder / "scs-mark-on-woods.png", optimize=True)

    wave, moon, ring = split_mark(mark)
    masks = {name: rasterize(unary_union(g), ppmm, PANEL_WIDTH, panel_len, ox, oy)[:h, :w]
             for name, g in (("ring", ring), ("moon", [moon]), ("wave", [wave]))}
    tiles = []
    for kind in EPOXY_RENDERS:
        img, rng = wood(kind, w, h, ppmm)
        for name in ("ring", "moon", "wave"):
            img = epoxy_onto(img, masks[name], EPOXY[name], ppmm, rng)
        tile = Image.fromarray(img.astype(np.uint8))
        tile.save(folder / f"scs-mark-epoxy-on-{kind}.png", optimize=True)
        tiles.append(tile)
    pair_image(tiles, int(4 * ppmm)).save(folder / "scs-mark-epoxy-on-dark-woods.png", optimize=True)


# --------------------------------------------------------------------------- test print
def write_test_print(mark, path):
    from reportlab import rl_config
    rl_config.invariant = 1   # no timestamps or random IDs: deterministic PDF
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    _, _, W, H = mark.bounds
    c = canvas.Canvas(str(path), pagesize=letter, invariant=1)
    c.setTitle("Space Coast Synthesizers mark - test print")
    pw, ph = letter

    def draw(x0, ytop, scale=1.0, outline=False):
        p = c.beginPath()
        for r in rings_of(mark):
            p.moveTo(x0 + r[0][0] * scale * mm, ytop - r[0][1] * scale * mm)
            for x, y in r[1:]:
                p.lineTo(x0 + x * scale * mm, ytop - y * scale * mm)
            p.close()
        if outline:
            c.setLineWidth(0.25 * mm)
            c.drawPath(p, stroke=1, fill=0)
        else:
            c.drawPath(p, stroke=0, fill=1, fillMode=0)   # even-odd

    L, top = 15 * mm, ph - 15 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(L, top, "Space Coast Synthesizers mark: test print")
    c.setFont("Helvetica", 9)
    c.drawString(L, top - 6 * mm, 'Print at 100% / "Actual size", never "fit to page". '
                                  "Measure the 50 mm bar before trusting anything below.")
    y = top - 16 * mm
    c.setLineWidth(0.3)
    c.line(L, y, L + 50 * mm, y)
    for i in range(51):
        c.line(L + i * mm, y, L + i * mm, y - (3 if i % 10 == 0 else 1.8) * mm)
    c.drawString(L, y - 7 * mm, "0")
    c.drawString(L + 45 * mm, y - 7 * mm, "50 mm")

    y = top - 32 * mm
    draw(L, y)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(L, y - H * mm - 5 * mm, f"Actual size: {W:.1f} x {H:.1f} mm")
    draw(L + W * mm + 20 * mm, y, outline=True)
    c.setFont("Helvetica", 9)
    c.drawString(L + W * mm + 20 * mm, y - H * mm - 5 * mm, "Outline: cut out and tape in place to check position")

    y = y - H * mm - 20 * mm
    panel_h = 90 * mm
    c.setLineWidth(0.25 * mm)
    c.rect(L, y - panel_h, PANEL_WIDTH * mm, panel_h)
    draw(L + (PANEL_WIDTH - W) / 2 * mm, y - 20 * mm)
    c.setFont("Helvetica", 7)
    c.drawCentredString(L + PANEL_WIDTH / 2 * mm, y - 4 * mm, "mouthpiece end")
    c.drawCentredString(L + PANEL_WIDTH / 2 * mm, y - panel_h + 3 * mm,
                        f"{PANEL_WIDTH:.0f} mm top panel, keys below")
    x = L + PANEL_WIDTH * mm + 15 * mm
    for target in (45.0, 36.0):
        s = target / W
        draw(x, y - 20 * mm, s)
        c.setFont("Helvetica", 8)
        c.drawString(x, y - 20 * mm - H * s * mm - 5 * mm, f"{target:.0f} mm wide (comparison)")
        x += target * mm + 12 * mm
    c.setFont("Helvetica", 7)
    c.drawString(L, 15 * mm, "Generated by branding/build.py. Geometry: branding/export/spec.json.")
    c.showPage()
    c.save()


# --------------------------------------------------------------------------- main
def main():
    for sub in ("", "png", "print", "renders"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    mark = build_mark()
    _, _, W, H = mark.bounds
    write_svg(mark, OUT / "scs-orbit-wave-mark.svg")
    write_dxf(mark, OUT / "scs-orbit-wave-mark.dxf")
    write_pngs(mark, OUT / "png")
    write_test_print(mark, OUT / "print" / "scs-mark-test-print-100pct.pdf")
    write_renders(mark, OUT / "renders")
    spec = dict(SPEC, overall_width_mm=round(W, 2), overall_height_mm=round(H, 2),
                separate_parts=len(parts(mark)), panel_width_mm=PANEL_WIDTH,
                side_margin_mm=round((PANEL_WIDTH - W) / 2, 2))
    (OUT / "spec.json").write_text(json.dumps(spec, indent=2) + "\n")
    print(f"mark {W:.2f} x {H:.2f} mm, {len(parts(mark))} parts -> {OUT.relative_to(HERE.parent)}/")


if __name__ == "__main__":
    main()
