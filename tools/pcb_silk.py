#!/usr/bin/env python3
"""A board's silkscreen completed in place, and nothing else touched (#54).

    python3 tools/pcb_silk.py hardware/boards/main-board            # the board itself
    python3 tools/pcb_silk.py hardware/boards/main-board --dry-run  # say what it would do
    python3 tools/pcb_silk.py hardware/boards/main-board --audit    # what is printed, and what is not

pcb.add_silk_generic tries eight fixed places beside a part and leaves its reference off
when all are taken, so a dense board fabricates with parts nobody can name. `complete`
runs after it (each board's layout script calls it; this command applies it to a board as
it stands) and adds only what is missing:

  a reference   for every part of the sheets that has none, at the nearest clear place
                within `REACH` of its body, reading across or along, and nearer its own
                part than any other so it cannot be read as a neighbour's
  a name        beside each connector layout.yaml `silk:` `names:` lists (what plugs in)
  a pin 1 dot   beside pad 1 of every connector with three pins or more, outside its body
  a pin legend  beside each pin of a connector in `silk:` `pins:` (a probe header)
  a leader      where no place beside a part is clear: its reference at the nearest clear
                place farther off (`LEAD`), joined to it by a line

`silk:` `no_ref:` names a part that gets none, with the reason (its face is never seen).

and takes off a reference printed twice. It is idempotent: a second run adds nothing. It
moves no part, track, via or zone, and `pcb.py check` judges the result (check_silk).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcb  # noqa: E402
import pcbnew  # noqa: E402
from shapely.geometry import LineString, Point, box  # noqa: E402
from shapely.ops import nearest_points, unary_union  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

REACH = 3.0        # mm from a part's body to its reference, at most
PIN_REACH = 2.0    # a pin's name farther from its pad than this names nothing
LEAD = 4.0         # and on a leader line, where there is no place that near
STEP = 0.1         # the search grid
TEXT_GAP = 0.2     # between two legends: over fab silk clearance, and a row of 0805s at their closest pitch still takes one each
OWN = 0.25         # a legend stands this much nearer its own part than any other
NO_REF = ("H", "NT", "TP", "FID")   # board features with nothing to fit: a hole, a net tie


def _mm(v):
    return pcbnew.ToMM(v)


_W = {}


def ink_w(board, text):
    """A legend's printed width, stroke included, off its real stroked shape. pcb.text_w
    reads KiCad's bounding box, which stands about half a millimetre wider than the ink:
    that half millimetre is why a row of 0805s had room for one reference in three."""
    if text not in _W:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetTextSize(pcb.V(pcb.SILK_H, pcb.SILK_H))
        t.SetTextThickness(pcb.MM(pcb.SILK_W))
        t.SetLayer(pcbnew.F_SilkS)
        x0, _, x1, _ = pcb.item_shape(t, pcbnew.F_SilkS).bounds
        _W[text] = x1 - x0
    return _W[text]


def _silk_layer(top):
    return pcbnew.F_SilkS if top else pcbnew.B_SilkS


class Face:
    """Everything a new legend on one face must keep off, as check_silk and KiCad's DRC
    will judge it, with the margins they hold."""

    def __init__(self, board, lay, top):
        self.board, self.top = board, top
        fab = lay["fab"]
        gap = float(fab["silk_to_pad"]) + 0.06
        silk, mask = _silk_layer(top), (pcbnew.F_Mask if top else pcbnew.B_Mask)
        crt = pcbnew.F_CrtYd if top else pcbnew.B_CrtYd
        ol = pcbnew.SHAPE_POLY_SET()
        board.GetBoardPolygonOutlines(ol)
        self.inside = pcb.shapely_of(ol).buffer(-0.5)
        self.bodies = {}        # ref: its courtyard on this face
        hard = []
        for fp in board.GetFootprints():
            fp.BuildCourtyardCaches()
            cy = fp.GetCourtyard(crt)
            if cy.OutlineCount():
                self.bodies[fp.GetReference()] = pcb.shapely_of(cy)
                hard.append(self.bodies[fp.GetReference()].buffer(0.1))
            for pad in fp.Pads():
                if pad.IsOnLayer(mask):
                    hard.append(pcb.item_shape(pad, mask, pad.GetSolderMaskExpansion(mask)).buffer(gap))
                elif pad.HasHole():
                    b = pad.GetBoundingBox()
                    hard.append(box(_mm(b.GetLeft()), _mm(b.GetTop()), _mm(b.GetRight()), _mm(b.GetBottom())).buffer(gap))
            try:
                items = list(fp.GraphicalItems())
            except TypeError:
                items = []
            for it in items:
                if it.GetLayer() == silk:
                    try:
                        hard.append(pcb.item_shape(it, silk).buffer(gap))
                    except AttributeError:
                        b = it.GetBoundingBox()
                        hard.append(box(_mm(b.GetLeft()), _mm(b.GetTop()), _mm(b.GetRight()), _mm(b.GetBottom())).buffer(gap))
        for v in board.GetTracks():
            if isinstance(v, pcbnew.PCB_VIA):
                c = v.GetPosition()
                hard.append(Point(_mm(c.x), _mm(c.y)).buffer(_mm(v.GetWidth(pcbnew.F_Cu)) / 2 + 0.1))
        for d in board.GetDrawings():
            if d.GetLayer() == silk:
                hard.append(pcb.item_shape(d, silk).buffer(TEXT_GAP if isinstance(d, pcbnew.PCB_TEXT) else gap))
        self.hard = hard
        self.tree = STRtree(hard)
        self.added = []

    def free(self, g, margin=TEXT_GAP):
        if not self.inside.contains(g):
            return False
        if any(g.intersects(self.hard[i]) for i in self.tree.query(g)):
            return False
        return not any(g.distance(a) < margin for a in self.added)

    def body(self, fp):
        """The part as a reader sees it on this face: its courtyard, or its pads' box."""
        ref = fp.GetReference()
        if ref in self.bodies:
            return self.bodies[ref]
        bs = [p.GetBoundingBox() for p in fp.Pads()]
        return unary_union([box(_mm(b.GetLeft()), _mm(b.GetTop()), _mm(b.GetRight()), _mm(b.GetBottom())) for b in bs])

    def others(self, ref):
        return [g for r, g in self.bodies.items() if r != ref]

    def place(self, text, fp, reach=REACH, own=OWN, angles=(0, 90), target=None):
        """The clear place for `text` nearest fp's body (or `target`, one of its pads):
        (x, y, angle, shape) or None."""
        me = target if target is not None else self.body(fp)
        rest = self.others(fp.GetReference())
        rtree = STRtree(rest) if rest else None
        x0, y0, x1, y1 = me.bounds
        w, h = ink_w(self.board, text) / 2 + 0.05, pcb.SILK_H / 2 + 0.16    # the stroke stands past the glyph box
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        best = None
        for ang in angles:
            hw, hh = (w, h) if not ang else (h, w)
            nx, ny = int((x1 - x0 + 2 * (reach + hw)) / STEP) + 1, int((y1 - y0 + 2 * (reach + hh)) / STEP) + 1
            for i in range(nx):
                px = x0 - reach - hw + i * STEP
                for j in range(ny):
                    py = y0 - reach - hh + j * STEP
                    g = box(px - hw, py - hh, px + hw, py + hh)
                    d = g.distance(me)
                    if d > reach or d < 0.15:
                        continue
                    # square on to the part's middle reads as its own; a turned legend costs a little
                    cost = d + 0.8 * min(abs(px - cx), abs(py - cy)) + (0.35 if ang else 0)
                    if best is not None and cost >= best[0]:
                        continue
                    if not self.free(g):
                        continue
                    if rtree is not None and own is not None:
                        near = min((g.distance(rest[k]) for k in rtree.query(g.buffer(d + own))), default=9e9)
                        if near < d + own:
                            continue
                    best = (cost, px, py, ang, g)
        return best and best[1:]

    def place_led(self, text, fp, reach=LEAD):
        """A place farther off, with a straight line from the legend to the part that
        crosses no pad, via, part or other legend: (x, y, angle, shape, line) or None."""
        me = self.body(fp)
        x0, y0, x1, y1 = me.bounds
        w, h = ink_w(self.board, text) / 2 + 0.05, pcb.SILK_H / 2 + 0.16
        best = None
        for ang in (0, 90):
            hw, hh = (w, h) if not ang else (h, w)
            nx, ny = int((x1 - x0 + 2 * (reach + hw)) / 0.2) + 1, int((y1 - y0 + 2 * (reach + hh)) / 0.2) + 1
            for i in range(nx):
                px = x0 - reach - hw + i * 0.2
                for j in range(ny):
                    py = y0 - reach - hh + j * 0.2
                    g = box(px - hw, py - hh, px + hw, py + hh)
                    d = g.distance(me)
                    if d > reach or d < 0.6 or (best is not None and d + (0.35 if ang else 0) >= best[0]):
                        continue
                    if not self.free(g):
                        continue
                    # the line: straight between the two at their nearest, else from the middle of
                    # one of the legend's sides to the middle of one of the part's
                    gb = g.bounds
                    ends_a = [nearest_points(g, me)[0]] + [Point(*q) for q in (((gb[0] + gb[2]) / 2, gb[1]), ((gb[0] + gb[2]) / 2, gb[3]),
                                                                              (gb[0], (gb[1] + gb[3]) / 2), (gb[2], (gb[1] + gb[3]) / 2))]
                    ends_b = [nearest_points(g, me)[1]] + [Point(*q) for q in (((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1),
                                                                              (x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2))]
                    line = None
                    for k, (a, b) in enumerate(sorted(((a, b) for a in ends_a for b in ends_b), key=lambda ab: ab[0].distance(ab[1]))):
                        full = LineString([a, b])
                        if full.length < 0.9 or full.length > reach + 1:
                            continue
                        cand = LineString([full.interpolate(0.3), full.interpolate(full.length - 0.35)])
                        # it leaves the legend and meets the part without crossing either
                        if cand.distance(g) < 0.28 or cand.buffer(pcb.SILK_W / 2).intersects(me):
                            continue
                        if self.free(cand.buffer(pcb.SILK_W / 2 + 0.02), margin=0.2):
                            line = cand
                            break
                    if line is None:
                        continue
                    best = (d + (0.35 if ang else 0), px, py, ang, g, line)
        return best and best[1:]

    def leader(self, line):
        (ax, ay), (bx, by) = line.coords
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(_silk_layer(self.top))
        s.SetStart(pcb.V(ax, ay))
        s.SetEnd(pcb.V(bx, by))
        s.SetWidth(pcb.MM(pcb.SILK_W))
        self.board.Add(s)
        self.added.append(line.buffer(pcb.SILK_W / 2))

    def text(self, text, x, y, angle, g):
        pcb.silk_text(self.board, text, x, y, top=self.top, angle=angle)
        self.added.append(g)

    def dot(self, x, y, r=0.3):
        pcb.silk_dot(self.board, x, y, r=r, top=self.top)
        self.added.append(Point(x, y).buffer(r + pcb.SILK_W / 2))


def silk_texts(board):
    return [d for d in board.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]


def labelled(board):
    """{reference: [its silkscreen texts]}: a legend whose first word is the reference."""
    refs = {fp.GetReference() for fp in board.GetFootprints()}
    out = {}
    for d in silk_texts(board):
        first = d.GetText().split(" ")[0]
        if first in refs:
            out.setdefault(first, []).append(d)
    for fp in board.GetFootprints():
        f = fp.Reference()
        if f.IsVisible() and f.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            out.setdefault(fp.GetReference(), []).append(f)
    return out


def has_dot(board, top, spots):
    """A filled silk circle already at one of these places (the pin 1 mark of an earlier run)."""
    for d in board.GetDrawings():
        if d.GetLayer() == _silk_layer(top) and isinstance(d, pcbnew.PCB_SHAPE) and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            p = d.GetCenter()
            if any(abs(_mm(p.x) - x) < 0.02 and abs(_mm(p.y) - y) < 0.02 for x, y in spots):
                return True
    return False


def strip_refs(board, comps):
    """Every bare reference legend taken off (a switch's `SW1 LT1` and every other text
    stay), and a reference field shown on the silkscreen sent to the fab layer as the
    rest are: `--redo` then places them all afresh, the crowded parts first."""
    n = 0
    for d in silk_texts(board):
        t = d.GetText()
        ref = t.split(" ")[0]
        if ref in comps and t in (ref, ref + " DNP") and not ref.startswith(NO_REF):
            board.Delete(d)
            n += 1
    for fp in board.GetFootprints():
        f = fp.Reference()
        if f.IsVisible() and f.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            f.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
            f.SetPosition(fp.GetPosition())
            f.SetTextSize(pcb.V(0.5, 0.5))
            f.SetTextThickness(pcb.MM(0.08))
            n += 1
    return n


def complete(board, lay, comps, say=print, dry=False, redo=False):
    """Add what the silkscreen lacks (the module's docstring). Returns the references still
    without a legend."""
    pcb._TWB[0] = board
    if redo:
        say(f"silk: {strip_refs(board, comps)} reference legend(s) taken off, to be placed afresh")
    spec = lay.get("silk") or {}
    names, pins = spec.get("names") or {}, spec.get("pins") or {}
    skip = set(spec.get("no_ref") or {})        # a part whose face is never seen, with the reason
    faces = {}

    def face(top):
        if top not in faces:
            faces[top] = Face(board, lay, top)
        return faces[top]

    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    # a footprint's own reference field left on the silkscreen (it stands where the library
    # drew it, not where there is room): to the fab layer as the rest are, and placed below
    for ref, fp in sorted(fps.items()):
        f = fp.Reference()
        if ref in comps and f.IsVisible() and f.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            say(f"silk: {ref}'s reference field was on the silkscreen - moved to the fab layer, placed afresh")
            if not dry:
                f.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
                f.SetPosition(fp.GetPosition())
                f.SetTextSize(pcb.V(0.5, 0.5))
                f.SetTextThickness(pcb.MM(0.08))
    # a reference printed twice: the one nearer its part stays
    for ref, ds in sorted(labelled(board).items()):
        if len(ds) > 1 and ref in fps:
            top = ds[0].GetLayer() == pcbnew.F_SilkS
            me = face(top).body(fps[ref])
            ds.sort(key=lambda d: (round(pcb.item_shape(d, d.GetLayer()).distance(me), 2), d.GetTextAngleDegrees() != 0))
            for d in ds[1:]:
                say(f"silk: {ref} was printed twice - the farther one taken off")
                if not dry:
                    board.Delete(d)
            faces.clear()
    have = labelled(board)
    left = []

    def order(r):
        return (-len(fps[r].Pads()), r)       # the big parts first: they have the fewest places

    # pin 1 marks first, then the pins' names, then what plugs in: the nearer the pad, the sooner
    for ref, fp in sorted(fps.items()):
        if not ref.startswith("J") or ref not in comps or ref in skip or len(fp.Pads()) < 3:
            continue
        p1 = next((p for p in fp.Pads() if p.GetNumber() == "1"), None)
        top = not fp.IsFlipped()
        if p1 is None:
            continue
        f = face(top)
        me = f.body(fp)
        c = p1.GetPosition()
        px, py = _mm(c.x), _mm(c.y)
        x0, y0, x1, y1 = me.bounds
        r = 0.3
        off = r + pcb.SILK_W / 2 + 0.25
        spots = sorted([(abs(px - x0), x0 - off, py), (abs(px - x1), x1 + off, py), (abs(py - y0), px, y0 - off), (abs(py - y1), px, y1 + off)])
        if has_dot(board, top, [(dx, dy) for _, dx, dy in spots[:2]]):
            continue
        for _, dx, dy in spots[:2]:        # the two sides pad 1 is nearest: a dot past the far side marks the wrong pin
            g = Point(dx, dy).buffer(r + pcb.SILK_W / 2)
            if f.free(g, margin=0.2):
                say(f"silk: {ref} pin 1 dot")
                f.dot(dx, dy, r) if not dry else f.added.append(g)
                break
        else:
            say(f"silk: NO CLEAR PLACE for {ref}'s pin 1 dot")
            left.append(f"{ref} pin 1")
    # a connector's own reference before its pins' names take the room beside it
    for ref in sorted(r for r in fps if r.startswith("J") and r in comps and r not in have and r not in skip):
        f = face(not fps[ref].IsFlipped())
        at = f.place(ref, fps[ref]) or f.place(ref, fps[ref], own=0.0)
        if at is not None:
            say(f"silk: {ref} labelled")
            f.text(ref, *at) if not dry else f.added.append(at[3])
            have[ref] = [None]
    # a probe header's pins, each named at the nearest clear place to its own pad
    for ref, legend in sorted(pins.items()):
        fp = fps[ref]
        f = face(not fp.IsFlipped())
        for num, text in sorted(legend.items(), key=lambda kv: str(kv[0])):
            if any(d.GetText() == text for d in silk_texts(board)):
                continue
            b = next(p for p in fp.Pads() if p.GetNumber() == str(num)).GetBoundingBox()
            pad = box(_mm(b.GetLeft()), _mm(b.GetTop()), _mm(b.GetRight()), _mm(b.GetBottom()))
            at = f.place(text, fp, reach=PIN_REACH, own=None, target=pad)
            if at is None:
                say(f"silk: NO CLEAR PLACE for {ref} pin {num}'s name {text!r}")
                left.append(f"{ref} pin {num}")
                continue
            say(f"silk: {ref} pin {num} named {text!r}")
            f.text(text, *at) if not dry else f.added.append(at[3])
    for ref in sorted((r for r in names if r in fps), key=order):
        fp = fps[ref]
        f = face(not fp.IsFlipped())
        if any(d.GetText() == names[ref] for d in silk_texts(board)):
            continue
        at = f.place(names[ref], fp, reach=4.0, own=None)
        if at is None:
            say(f"silk: NO CLEAR PLACE for {ref}'s name {names[ref]!r}")
            left.append(f"{ref} name")
            continue
        say(f"silk: {ref} named {names[ref]!r}")
        f.text(names[ref], *at) if not dry else f.added.append(at[3])
    # every reference still missing: the most crowded parts choose first
    missing = [r for r in fps if r in comps and r not in have and r not in skip and not r.startswith(NO_REF)]

    def crowd(r):
        f = face(not fps[r].IsFlipped())
        me = f.body(fps[r])
        return (-sum(1 for g in f.others(r) if g.distance(me) < 2.0), -len(fps[r].Pads()), r)

    far = []
    for ref in sorted(missing, key=crowd):
        fp = fps[ref]
        f = face(not fp.IsFlipped())
        text = ref + (" DNP" if fp.IsDNP() else "")
        at = f.place(text, fp) or f.place(text, fp, own=0.0)
        if at is None:
            far.append(ref)
            continue
        say(f"silk: {ref} labelled")
        f.text(text, *at) if not dry else f.added.append(at[3])
    # no place beside it: the nearest clear place farther off, joined to the part by a line
    for ref in far:
        fp = fps[ref]
        f = face(not fp.IsFlipped())
        text = ref + (" DNP" if fp.IsDNP() else "")
        at = f.place_led(text, fp)
        if at is None:
            left.append(ref)
            continue
        x, y, ang, g, line = at
        say(f"silk: {ref} labelled, on a leader {line.length:.1f} mm long")
        if dry:
            f.added += [g, line.buffer(pcb.SILK_W / 2)]
        else:
            f.text(text, x, y, ang, g)
            f.leader(line)
    if left:
        say(f"silk: still without a legend ({len(left)}): {', '.join(sorted(left))}")
    return left


def audit(board, comps):
    have = labelled(board)
    refs = sorted(fp.GetReference() for fp in board.GetFootprints() if fp.GetReference() in comps and not fp.GetReference().startswith(NO_REF))
    miss = [r for r in refs if r not in have]
    print(f"silk: {len(refs)} part(s), {len(refs) - len(miss)} with a reference on the silkscreen")
    if miss:
        print("silk: without one: " + ", ".join(miss))
    for r, ds in sorted(have.items()):
        if len(ds) > 1:
            print(f"silk: {r} printed {len(ds)} times")
    return miss


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    bdir = os.path.abspath(sys.argv[1])
    name = os.path.basename(bdir)
    path = sys.argv[sys.argv.index("--board") + 1] if "--board" in sys.argv else os.path.join(bdir, name + ".kicad_pcb")
    lay = pcb.layout_yaml(bdir)
    comps, _ = pcb.sheet_netlist(os.path.join(bdir, name + ".kicad_sch"))
    board = pcbnew.LoadBoard(path)
    if "--audit" in sys.argv:
        return 1 if audit(board, comps) else 0
    dry = "--dry-run" in sys.argv
    left = complete(board, lay, comps, dry=dry, redo="--redo" in sys.argv)
    if not dry:
        pcbnew.SaveBoard(path, board)
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main())
