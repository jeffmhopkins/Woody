#!/usr/bin/env python3
"""What every hand-laid board's script shares (ADR 0030): seating a part, the one pattern a
key's network is placed and wired in, a list of tracks and vias and the drawing of it, and
the ground plane's rules. NOTHING HERE ROUTES: a board's script (hardware/boards/<board>/
*_layout.py) gives every point of every track, and this module puts them on the board.

Body frame throughout: x along the body from the mouth, y across it from the near side, mm,
seen from above; all parts but the switches are on the underside.
"""
import math
import subprocess
import sys

import pcbnew
import pcb          # frames, the sheets' netlist, the silkscreen steps; nothing that routes

TW, PW = 0.25, 0.4            # signal and 3V3 (layout.yaml rules: track, power_track)
VIA, DRILL = 0.7, 0.3         # layout.yaml rules: via, via_drill
GND = "GND_CHAIN"
PITCH = 1.27                  # the register's and the header's pin pitch
BODY = ("SW", "J", "H")       # what the body CAD places, not a board's script


def body_xy(p):
    return (pcbnew.ToMM(p.x) - pcb.OX, pcb.OY - pcbnew.ToMM(p.y))


def seat(fp, x, y, way):
    """fp to body (x, y), turned so its pad 1 lies toward `way` from its centre. The turn is
    found by trying the four: on the underside KiCad mirrors rotation."""
    fp.SetPosition(pcb.V(*pcb.to_pcb(x, y)))
    if way is None:
        return
    want = {"+x": (1, 0), "-x": (-1, 0), "+y": (0, 1), "-y": (0, -1)}[way]
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        px, py = body_xy(fp.FindPadByNumber("1").GetPosition())
        d = (px - x, py - y)
        n = math.hypot(*d)
        if n > 1e-6 and abs(d[0] / n - want[0]) < 1e-3 and abs(d[1] / n - want[1]) < 1e-3:
            return
    raise SystemExit(f"pcb_hand: no turn puts {fp.GetReference()}'s pad 1 toward {way}")


def refit(board, comps, nets):
    """A part whose sheet now names another footprint (a header changed for a different
    connector) gets that footprint: same place, side and turn, its reference, value and
    sheet path, and every pad on the net the sheets give it. pcb.py update-footprints
    refuses this on purpose - the pads move, so the copper must be redrawn - and a layout
    script redraws all of it. Returns the references changed."""
    padnet = {(r, p): n for n, nodes in nets for r, p in nodes}
    done = []
    for fp in list(board.GetFootprints()):
        ref = fp.GetReference()
        want = comps.get(ref, {}).get("footprint")
        have = f"{fp.GetFPID().GetLibNickname().wx_str()}:{fp.GetFPID().GetLibItemName().wx_str()}"
        if not want or want == have:
            continue
        new = pcb.load_fp(want)
        board.Add(new)
        pos = fp.GetPosition()
        new.SetPosition(pos)
        if fp.IsFlipped():
            new.Flip(pos, pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        new.SetOrientation(fp.GetOrientation())
        new.SetReference(ref)
        new.SetValue(comps[ref]["value"])
        new.SetPath(fp.GetPath())
        new.SetExcludedFromBOM(comps[ref]["exclude_from_bom"])
        new.SetDNP(fp.IsDNP())
        new.SetExcludedFromPosFiles(fp.IsExcludedFromPosFiles())
        for a, b in ((fp.Reference(), new.Reference()), (fp.Value(), new.Value())):
            b.SetLayer(a.GetLayer())
            b.SetTextSize(a.GetTextSize())
            b.SetTextThickness(a.GetTextThickness())
            b.SetVisible(a.IsVisible())
        for pad in new.Pads():
            n = padnet.get((ref, pad.GetNumber()))
            ni = board.FindNet(n) if n else None
            if n and ni is None:
                raise SystemExit(f"pcb_hand: {ref} pad {pad.GetNumber()} is on {n}, a net this board does not have yet")
            if ni is not None:
                pad.SetNet(ni)
        board.Delete(fp)
        done.append(ref)
    return done


def seat_chain(fp, geo, jpin, face=None):
    """J-CHAIN where the body CAD puts it and facing the way it says (pcb.chain_target): the
    turn is found, as pcb.place_chain finds it for a new board. `jpin(k)` is where the
    board's script expects pin k, and a header anywhere else stops the script: its tracks
    are drawn for those places. `face` (+1 or -1) overrides the body CAD's facing, about the
    same pad centre, FOR A PLACEMENT PROPOSAL ONLY - the body CAD decides where a header is."""
    (tx, ty), d = pcb.chain_target(geo)
    d = face or d
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        p1, p2 = fp.FindPadByNumber("1").GetPosition(), fp.FindPadByNumber("2").GetPosition()
        dx, dy = pcbnew.ToMM(p2.x - p1.x), pcbnew.ToMM(p2.y - p1.y)
        if abs(dy) < 1e-3 and dx * d > 0:
            cx, cy = pcb.pads_centre(fp)
            at = fp.GetPosition()
            fp.SetPosition(pcb.V(pcbnew.ToMM(at.x) + tx - cx, pcbnew.ToMM(at.y) + ty - cy))
            for k in (1, 2, 9, 10):
                got, want = body_xy(fp.FindPadByNumber(str(k)).GetPosition()), jpin(k)
                if math.dist(got, want) > 0.06:
                    raise SystemExit(f"pcb_hand: J-CHAIN pin {k} is at {got}, and this layout is drawn for {want} - "
                                     "the body CAD moved the header (pcb-geometry.echo); move the script's header pins and what follows from them")
            return
    raise SystemExit("pcb_hand: no turn puts J-CHAIN's even row where the body CAD faces it")


# ---- a key's network, relative to its switch's centre -------------------------------------------
# The switch's pins (hardware/lib, SW_Gateron_KS33_1u): pin 1, the leg, at (-4.4, -4.7);
# pin 2, ground, at (+2.6, -5.75); the pole's hole, 5.25 across, at the centre.
# NOTHING PASSES BETWEEN A PIN AND THE POLE (owner, 2026-11-20, of the line that did: "Each of
# these need work too"). That gap is 2 mm, and a line through it cut the ground pin's relief
# ring and dropped into the node between two pads. So each part stands OUTSIDE its own pin,
# beside it and level with it, joined by one short straight neck: the series resistor on the
# mouth side of the leg pin, the capacitor on the tail side of the ground pin. The node runs
# between the two under both pins, DROP below the centre, with the pull-up hanging from its
# middle. Its two ends are free, and the key line leaves from the one facing the register.
DROP = 8.5                    # the node: clear of the ground pin's relief ring above it; the pull-up below it clear of the board's near edge
X_SER, X_CAP = -7.8, 6.0      # the two parts' columns: a millimetre of mask between pad and pin
KEY_NET = {
    "R-KEY-SER": (X_SER, -4.7 - 0.9125, "-y"),            # pad 2 (the leg) level with pin 1, pad 1 (the node) below it
    "R-KEY-PU": (-0.94, -DROP - 0.9125, "-y"),            # pad 2 at the node, pad 1 (3V3) toward the near edge
    "C-KEY": (X_CAP, -5.75 - 0.9125, "-y"),               # pad 2 (ground) level with pin 2, pad 1 (the node) below it
}


def key_places(comps, switches):
    """Every key's three parts, by reference: the one pattern at each switch."""
    place = {}
    for key, (sx, sy, sr) in switches.items():
        assert sr == 0, f"{key}: the key network is drawn for a switch at 0 degrees"
        for row, (dx, dy, way) in KEY_NET.items():
            place[pcb.ref_of(comps, row, key)] = (sx + dx, sy + dy, way)
    return place


def seat_all(board, place):
    """Every part the body CAD does not place goes where `place` says; one without a place
    stops the script."""
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    loose = sorted(r for r in fps if not r.startswith(BODY) and r not in place)
    if loose:
        raise SystemExit(f"pcb_hand: no place given for {', '.join(loose)}")
    for ref, (x, y, way) in place.items():
        seat(fps[ref], x, y, way)


def strip(board):
    """The copper and silkscreen go; the zones' outlines stay, emptied."""
    for t in list(board.GetTracks()):
        board.Delete(t)
    for z in board.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    for d in [d for d in board.GetDrawings() if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]:
        board.Delete(d)


class Copper:
    """Every track and via of a board, by hand. All of it on the parts face (B.Cu) unless a
    track says otherwise; the switch-side face is ground and nothing else. Each line is a
    list of points in the body frame, drawn at 0, 45 and 90 degrees."""

    def __init__(self):
        self.tracks, self.vias = [], []

    def track(self, net, pts, w=TW, layer=pcbnew.B_Cu):
        for a, b in zip(pts, pts[1:]):
            dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
            assert dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-6, f"{net}: {a} -> {b} is not at 0, 45 or 90 degrees"
        self.tracks.append((net, w, pts, layer))

    def via(self, net, p):
        self.vias.append((net, p))

    def keys(self, switches):
        """Each key, the same copper at every one: a neck from each pin straight out to its
        part, and the node from the resistor's lower pad down at 45, along under both pins
        through the pull-up, and up at 45 into the capacitor's lower pad. Returns each
        node's mouth end, its tail end, and each pull-up's rail pad."""
        ser = {k: (x + X_SER, y - 4.7 - 1.825) for k, (x, y, _) in switches.items()}
        cap = {k: (x + X_CAP, y - 5.75 - 1.825) for k, (x, y, _) in switches.items()}
        pu1 = {k: (x - 0.94, y - DROP - 1.825) for k, (x, y, _) in switches.items()}
        for k, (sx, sy, _) in switches.items():
            ry, cy = sy - DROP - ser[k][1], sy - DROP - cap[k][1]
            self.track("/KEY_" + k, [ser[k], (ser[k][0] - ry, sy - DROP), (cap[k][0] + cy, sy - DROP), cap[k]])
            self.track(f"/{k}/SWITCH_LEG", [(sx - 4.4, sy - 4.7), (sx + X_SER, sy - 4.7)])
            self.track(GND, [(sx + 2.6, sy - 5.75), (sx + X_CAP, sy - 5.75)])
        return ser, cap, pu1

    def draw(self, board):
        for net, w, pts, layer in self.tracks:
            ni = board.FindNet(net)
            assert ni is not None, net
            for a, b in zip(pts, pts[1:]):
                if math.dist(a, b) < 1e-6:
                    continue
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcb.V(*pcb.to_pcb(*a)))
                t.SetEnd(pcb.V(*pcb.to_pcb(*b)))
                t.SetWidth(pcb.MM(w))
                t.SetLayer(layer)
                t.SetNet(ni)
                board.Add(t)
        for net, p in self.vias:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcb.V(*pcb.to_pcb(*p)))
            v.SetWidth(pcbnew.F_Cu, pcb.MM(VIA))
            v.SetDrill(pcb.MM(DRILL))
            v.SetNet(board.FindNet(net))
            board.Add(v)

    def segments(self):
        return sum(len(pts) - 1 for _, _, pts, _ in self.tracks)


# A key line steps sideways off the end pad of its node, clear of the pad above it, and climbs.
def tail_end(cap, k):
    (x, y) = cap[k]
    return [(x, y), (x + 0.8, y), (x + 1.3, y + 0.5)]


def mouth_end(ser, k, to):
    """To the column x = `to`, mouth side of the resistor."""
    (x, y) = ser[k]
    return [(x, y), (to + 0.5, y), (to, y + 0.5)]


def no_parts_face_pour(board):
    """NO PARTS-FACE POUR (owner, 2026-11-20: "if we had the ground plane on the bottom, we
    don't need to fill in the top layer correct?"). Correct: the switch-side face is one whole
    ground plane under every line, and these are slow lines. The parts face's fill added
    nothing to it, and the tracks cut it into regions joined by necks, slivers between pads
    and a closed pocket by the register - each of which was then a thing to fix. Every
    ground pad on this face reaches the plane without it: the capacitors by their necks to
    the switches' through-hole pins or by their own vias, the register's pins by vias, the
    header's by its pins. So a parts-face ground zone is deleted, not refilled."""
    for z in list(board.Zones()):
        if not z.GetIsRuleArea() and z.GetNetname() == GND and z.IsOnLayer(pcbnew.B_Cu) and not z.IsOnLayer(pcbnew.F_Cu):
            board.Delete(z)


def relieve(board):
    """Every ground pad the plane meets is joined to it by relief spokes (owner, 2026-11-20:
    "Do the resistors that land on ground need their own ground pad so they can actually be
    soldered?"), so no pad to be soldered is one piece with a plane. Vias stay solid."""
    for z in board.Zones():
        if z.GetNetname() == GND:
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)


def fill(path):
    """The zones filled in a process of their own: filling a board just edited in memory
    crashes KiCad 9's Python. ZONE_FILLER pours the plane; it routes nothing."""
    code = ("import pcbnew, sys; b = pcbnew.LoadBoard(sys.argv[1]); b.BuildConnectivity(); "
            "pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1], b)")
    subprocess.run([sys.executable, "-c", code, path], check=True)


def finish(board, lay, comps, out, labels=None):
    """The date, the plane's rules, the silkscreen; saved and the plane poured. `labels` is
    {reference: (body x, body y, angle)} for a part the silkscreen step finds no clear place
    beside: its reference is put there by hand, on the parts face, near enough to be read as
    that part's and no other's (owner, 2026-11-20). pcb.py check holds it to the silk limits."""
    board.GetTitleBlock().SetDate(lay["silk"]["date"])
    relieve(board)
    no_parts_face_pour(board)
    pcb.add_silk_generic(board, lay, comps)
    for ref, (x, y, angle) in (labels or {}).items():
        pcb.silk_text(board, ref, *pcb.to_pcb(x, y), angle=angle)
    pcb.silk_off_vias(board)
    import pcb_silk
    pcb_silk.complete(board, lay, comps)       # what is still missing: references, connector names, pin 1 (#54)
    pcbnew.SaveBoard(out, board)
    fill(out)
