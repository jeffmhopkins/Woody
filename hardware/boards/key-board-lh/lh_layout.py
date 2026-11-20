#!/usr/bin/env python3
"""The left key board laid out by hand (issue #48): every part placed on purpose here,
and - once the placement is accepted - every track and via written out below it.
NO ROUTER OF ANY KIND IS CALLED: not tools/pcb_route*.py, not Freerouting, not KiCad's.

    python3 hardware/boards/key-board-lh/lh_layout.py            # writes key-board-lh.hand.kicad_pcb

It READS key-board-lh.kicad_pcb (rev A, which stays the source until this board is
accepted) for what the body CAD and the sheets fix - the outline, the five switches,
J-CHAIN, the four mounts and their keep-outs, the ground zones' outlines, every pad's net -
strips its copper, and seats every other part where PLACE says. Body frame throughout:
x along the body from the mouth, y across it from the near side, mm, seen from above;
all parts but the switches are on the underside.

THE FLOORPLAN, and why each part is where it is.

1. THE REGISTER'S PINOUT DECIDES THE BOARD. Going round U1: SH/LD and CLK (pins 1, 2),
   the keys LH4, LH3, LH2, LH1 (pins 3..6), ground (8), then QH and SER (9, 10), the
   free input and its rail (11, 12), ground, LH5 (14), ground, VCC (16). The chain's four
   lines sit at its four corners and LH5 sits alone on the far row. Routed from the pads
   outward, the chain lines have to wrap the register (rev A took SH/LD and SCK round the
   far edge), and LH5 crosses them.
   THE CHAIN BUS THEREFORE RUNS UNDER THE REGISTER, between its pad rows: all four lines
   enter at the pin-8/9 end and turn into their pads from inside. Across that end, from
   the key row's side, they lie SCK, SH/LD, SER, QH - which is J-CHAIN's own pin order
   (11, 9, 7, 5), so the bus leaves the header, turns once round its pin-1 end and runs
   straight into the register with no line crossing another and no via.
2. U1 stands just past the header's mouth, its pin-8/9 end toward the header and its
   key inputs (pins 3..6) facing the key row, so LH1..LH4 arrive in pin order from the
   side their switches are on, and LH5 leaves the far row toward its own switch.
3. EACH KEY'S NETWORK IS TUCKED UNDER ITS OWN SWITCH'S PINS, the same way round all
   five: the series resistor under pin 1 (the switch leg), the capacitor under pin 2
   (ground - its ground pad lands on the switch's own ground pin, no via), and the
   pull-up hanging below the node, its rail end toward the near edge.
4. 3V3 IS ONE TRUNK. With the bus from the header, round U1's end to the far row:
   C7 (the reservoir), R11 (the free input's pull-up), C8 across pins 12/13, under the
   body to pin 16 and C6 across 16/15; then on between LH5's and LH4's lines to their
   pull-ups, round LH4 and back along the near edge through the three row keys' pull-ups.
5. GROUND IS THE SWITCH-SIDE FACE, unbroken. Every switch's and the header's ground
   pin is a through-hole into it; the register's ground pins and the capacitors reach
   it by a via each. No ground track.
"""
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pcbnew       # noqa: E402
import yaml         # noqa: E402
import pcb          # noqa: E402  (frames, the sheets' netlist, the silkscreen steps; nothing that routes)

NAME = "key-board-lh"
SRC = os.path.join(HERE, NAME + ".kicad_pcb")
OUT = os.path.join(HERE, NAME + ".hand.kicad_pcb")

# ---- the register and its own parts ------------------------------------------------------------
# U1's centre. x: its body's header end 1.6 past the ribbon plug's keep-out (pcb-geometry.echo
# "ribbon left_hand"). y: the chain bus runs straight from under the header into the channel
# between the pad rows, so the channel's middle line (SER) is the bus's middle line.
UX, UY = 87.5, 36.8
PITCH = 1.27


def upin(n):
    """U1 pad n's centre: pins 1..8 on the key row's side, pin 8 at the header end."""
    if n <= 8:
        return (UX + PITCH * (4.5 - n), UY - 2.475)
    return (UX + PITCH * (n - 12.5), UY + 2.475)


Y_CAPS = UY + 4.7             # C8, C6: their courtyards clear of U1's
Y_RAIL = UY + 6.52            # the 3V3 spine past the far row: through C7.1 and R11.1

# (x, y, which way pad 1 faces) - the way is found on the board, not assumed (seat(), below)
PLACE = {
    "U1": (UX, UY, None),                                 # turned as rev A has it: pins 1..8 toward the key row
    "C7": (82.6, Y_RAIL + 0.95, "-y"),                    # C-BULK-CHAIN: first on the trunk after the bus; ground end toward the far edge
    "R11": (85.1, Y_RAIL - 0.9125, "+y"),                 # FREE3's pull-up: pad 2 down onto pin 11, pad 1 on the spine
    "C8": (upin(12)[0] + 0.95, Y_CAPS, "-x"),            # across pins 12 (3V3) and 13 (ground)
    "C6": (upin(15)[0] + 0.95, Y_CAPS, "+x"),            # across pins 16 (VCC) and 15 (ground)
}

# ---- a key's network, relative to its switch's centre -------------------------------------------
# The switch's pins (hardware/lib, SW_Gateron_KS33_1u): pin 1, the leg, at (-4.4, -4.7);
# pin 2, ground, at (+2.6, -5.75). The three KEY pads stand in one row, DROP below the centre.
DROP = 9.0
KEY_NET = {
    "R-KEY-SER": (-3.69, -DROP, "+x"),                    # pad 2 (the leg) under pin 1, pad 1 at the node
    "R-KEY-PU": (-0.94, -DROP - 0.9125, "-y"),            # pad 2 at the node, pad 1 (3V3) toward the near edge
    "C-KEY": (1.85, -DROP, "-x"),                         # pad 1 at the node, pad 2 (ground) under pin 2
}
BODY = ("SW", "J", "H")


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
    raise SystemExit(f"lh_layout: no turn puts {fp.GetReference()}'s pad 1 toward {way}")


def placement(board, comps):
    geo = pcb.cad_geometry("left_hand")
    place = dict(PLACE)
    for key, (sx, sy, sr) in geo["switches"].items():
        assert sr == 0, f"{key}: the key network is drawn for a switch at 0 degrees"
        for row, (dx, dy, way) in KEY_NET.items():
            place[pcb.ref_of(comps, row, key)] = (sx + dx, sy + dy, way)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    loose = sorted(r for r in fps if not r.startswith(BODY) and r not in place)
    if loose:
        raise SystemExit(f"lh_layout: no place given for {', '.join(loose)}")
    for ref, (x, y, way) in place.items():
        seat(fps[ref], x, y, way)
    return place


def strip(board):
    """Rev A's copper and silkscreen go; the zones' outlines stay, emptied."""
    for t in list(board.GetTracks()):
        board.Delete(t)
    for z in board.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    for d in [d for d in board.GetDrawings() if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]:
        board.Delete(d)


def main():
    lay = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))
    comps, _ = pcb.sheet_netlist(os.path.join(HERE, NAME + ".kicad_sch"))
    board = pcbnew.LoadBoard(SRC)
    strip(board)
    place = placement(board, comps)
    pcb.add_silk_generic(board, lay, comps)
    pcbnew.SaveBoard(OUT, board)
    shutil.copyfile(os.path.join(HERE, NAME + ".kicad_pro"), OUT[:-len(".kicad_pcb")] + ".kicad_pro")
    print(f"lh_layout: {len(place)} part(s) seated, no copper yet; wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
