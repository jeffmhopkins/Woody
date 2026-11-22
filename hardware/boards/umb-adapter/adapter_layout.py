#!/usr/bin/env python3
"""The umbilical adapter laid out by hand (ADR 0021, ADR 0030). NO ROUTER OF ANY KIND IS
CALLED: both parts are placed from the body CAD's exports and every track is written out below.

    python3 hardware/boards/umb-adapter/adapter_layout.py     # writes umb-adapter.kicad_pcb
    python3 tools/pcb.py check hardware/boards/umb-adapter

THE RECORD of this board's copper. Run twice it writes the same board.

THE FRAME below is the etherCON's own, as its footprint is drawn: the origin on the
connector's axis, x to the right and y DOWN, seen from the tail (the panel side), which is
the board's front face. Across the body the far side is on the right.

THERE IS NOTHING TO PLACE. The etherCON (J1) stands on the body CAD's axis on the front
face. J-UMB's posts (J2) come through from the rear on the row the header on the main board
holds them in, 7.7 below the axis, and pin k is where the main board's pin k stands
(tools/pcb_adapter.py check_cad holds each pad to it).

WHAT IS DECIDED HERE IS HOW EIGHT LINES CHANGE SIDES. Seen from the tail the etherCON's
pin 1 is on the LEFT (an RJ45 jack with its latch notch down) and J-UMB's pin 1, as the main
board numbers it, is on the RIGHT. So every line must end on the other side of the board
from where it starts, in the reverse of the order it left in, and no two can do that on one
face by the short way: any two direct lines cross.

1. THE TWO MIDDLE LINES GO STRAIGHT DOWN, ONE ON EACH FACE. SCLK (pin 4) on the rear face
   and MOSI (pin 5) on the front, crossing each other as an X between the etherCON's pins
   and the row. They are the shortest lines on the board and the fastest signals.
2. THE THREE LINES EACH SIDE OF THEM GO OVER THE TOP. Pins 6, 7 and 8 leave upward on the
   front face, run across above the etherCON's contacts, and come down the LEFT side into the
   row's left half. Pins 1, 2 and 3 do the same on the rear face down the RIGHT side. The
   line that starts furthest from its side takes the outermost lane and lands on the
   outermost pad, so within a face nothing crosses.
3. THE PAIRS STAY SIDE BY SIDE (hardware/interfaces/spi-link/spi-link.md): BREATH_SENSE
   with AGND_SENSE (1, 2) down the right, CS_MOD with DIG_GND (7, 8) down the left.
4. NO VIA, NO POUR. Every pad is a through-hole, so each line starts and ends on the face
   it runs on. No conductor of the umbilical is a plane's: PWR_GND, DIG_GND and AGND_SENSE
   are three separate returns until the main board joins them (ADR 0018), so a pour here
   would belong to one of them and couple it to the other two.
5. THE LANES. Over the top they run between the upper contact row and the latch's plated
   slot; down each side between the end contact and the housing's post hole (unplated).
"""
import json
import os
import sys

import pcbnew
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import pcb          # noqa: E402  frames, the sheet's netlist, the silkscreen helpers; nothing that routes
import pcb_adapter  # noqa: E402  the body CAD's exports for this board

NAME = "umb-adapter"
OUT = os.path.join(HERE, NAME + ".kicad_pcb")
F, B = pcbnew.F_Cu, pcbnew.B_Cu
TW, PW = 0.25, 0.5            # layout.yaml rules: track, power_track
PITCH = 2.54
ROW = 7.7                     # J-UMB's row below the axis: this layout is drawn for it (main() checks the body CAD still says so)

# the etherCON's contacts in its own frame (hardware/lib/woody.pretty/Neutrik_NE8FAV_etherCON_Vertical):
# odd pins on the lower row, even pins on the upper, 1.27 apart across
LOWER, UPPER = -2.11, -4.65
def j1(k):
    return (-4.445 + 1.27 * (k - 1), LOWER if k % 2 else UPPER)

# J-UMB's posts: pin 1 on the right, as the main board's row stands
def j2(k):
    return (8.89 - PITCH * (k - 1), ROW)

NET = {1: "/BREATH_SENSE", 2: "/AGND_SENSE", 3: "/UMBILICAL_POS12", 4: "/SCLK",
       5: "/MOSI", 6: "/PWR_GND", 7: "/CS_MOD", 8: "/DIG_GND"}      # checked against the sheet in main()
WIDTH = {3: PW, 6: PW}

# OVER THE TOP: three lanes between the upper contact row (its pads' tops at -5.25) and the
# latch slot's plated pad (its lower edge at -8.75). The outermost lane is the top one.
LANE = (-8.2, -7.6, -6.75)
# DOWN A SIDE: three columns between the end contact (its pad's edge 5.05 from the axis) and
# the post hole (8.425 out, 1.7 across, unplated: its edge at 7.58). The outermost is nearest
# the hole. The middle one is the row's own pad, so that line comes straight down into it.
COL = (6.85, 6.35, 5.725)
C = 1.0                       # the corner cut where a lane turns down a side


def over_the_top(k, lane, side):
    """Pin k of the etherCON up to its lane, across, down its column on `side` (-1 the left,
    +1 the right) and into J-UMB's pad k. The outer and inner lines step sideways at 45
    degrees onto their pads; the middle one meets its pad straight."""
    x, y = j1(k)
    cx, ly = side * COL[lane], LANE[lane]
    tx, ty = j2(k)
    pts = [(x, y), (x, ly), (cx - side * C, ly), (cx, ly + C)]
    step = abs(tx - cx)
    pts += [(cx, ty - step), (tx, ty)] if step > 1e-6 else [(tx, ty)]
    return pts


def straight_down(k):
    """Pin k straight down between the lower row's contacts, then at 45 onto its pad."""
    x, y = j1(k)
    tx, ty = j2(k)
    return [(x, y), (x, ty - abs(tx - x)), (tx, ty)]


def routes():
    """(net, width, points, layer) for all eight lines."""
    out = []
    # the front face: MOSI straight down; PWR_GND, CS_MOD, DIG_GND over the top and down the left
    out.append((5, straight_down(5), F))
    for lane, k in enumerate((8, 7, 6)):
        out.append((k, over_the_top(k, lane, -1), F))
    # the rear face: SCLK straight down; BREATH_SENSE, AGND_SENSE, +12 V over the top and down the right
    out.append((4, straight_down(4), B))
    for lane, k in enumerate((1, 2, 3)):
        out.append((k, over_the_top(k, lane, +1), B))
    return [(NET[k], WIDTH.get(k, TW), pts, layer) for k, pts, layer in out]


def main():
    lay = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))
    geo = pcb_adapter.geometry()
    ax, az, _ = geo["axis"]
    (y0, z0), (y1, _), _ = geo["row"]
    if abs((az - z0) - ROW) > 0.01 or abs((y0 + y1) / 2 - ax) > 0.01:
        sys.exit(f"adapter_layout: the body CAD puts J-UMB's row {az - z0:.2f} below the etherCON's axis, centred {(y0 + y1) / 2 - ax:+.2f} "
                 f"off it; this layout is drawn for {ROW} and 0 - move ROW and what follows from it")
    at = lambda p: pcb.to_pcb(ax + p[0], az - p[1])          # this file's frame -> pcb mm

    comps, nets = pcb.sheet_netlist(os.path.join(HERE, NAME + ".kicad_sch"))
    board = pcb.new_board(HERE, lay, geo)
    pcb.add_outline(board, pcb.dxf_segments(os.path.join(ROOT, "mechanical", "export", lay["outline"])))
    netinfo, fps = pcb.load_parts(board, comps, nets)
    je, ju = fps[pcb.ref_of(comps, "J-UMBILICAL-INST")], fps[pcb.ref_of(comps, "J-UMB")]
    for (ref, pin), net in {(r, p): n for n, nodes in nets for r, p in nodes}.items():
        if NET[int(pin)] != net:
            sys.exit(f"adapter_layout: the sheet puts {ref} pin {pin} on {net}; this layout is drawn for {NET[int(pin)]}")

    # the etherCON: its origin on the axis, on the front face, latch up
    board.Add(je)
    je.SetPosition(pcb.V(*at((0, 0))))
    # J-UMB's posts: the header's insulator is against the REAR face, so the footprint is
    # flipped; then turned and moved until pin 1 and pin 8 are where the main board has them
    board.Add(ju)
    ju.SetPosition(pcb.V(*at(j2(1))))
    ju.Flip(ju.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    for rot in (0, 90, 180, 270):
        ju.SetOrientationDegrees(rot)
        p1 = ju.FindPadByNumber("1").GetPosition()
        ju.Move(pcb.V(*at(j2(1))) - p1)
        p8 = ju.FindPadByNumber("8").GetPosition()
        w = at(j2(8))
        if abs(pcbnew.ToMM(p8.x) - w[0]) < 1e-3 and abs(pcbnew.ToMM(p8.y) - w[1]) < 1e-3:
            break
    else:
        sys.exit("adapter_layout: no turn puts J-UMB's pin 8 at the row's other end")
    # the header itself is the main board's part (its sheet's J-UMB, fitted there): this
    # footprint is the holes its posts come through, so it carries no model of a header
    ju.Models().clear()
    for fp in (je, ju):                      # their values are their BOM rows' words, longer than the board
        fp.Value().SetVisible(False)
    for k in range(1, 9):
        for fp, want in ((je, j1(k)), (ju, j2(k))):
            q = fp.FindPadByNumber(str(k)).GetPosition()
            w = at(want)
            assert abs(pcbnew.ToMM(q.x) - w[0]) < 1e-3 and abs(pcbnew.ToMM(q.y) - w[1]) < 1e-3, (fp.GetReference(), k)

    n_seg = 0
    for net, w, pts, layer in routes():
        for a, b in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcb.V(*at(a)))
            t.SetEnd(pcb.V(*at(b)))
            t.SetWidth(pcb.MM(w))
            t.SetLayer(layer)
            t.SetNet(netinfo[net])
            board.Add(t)
            n_seg += 1

    # the title block and the silkscreen. Everything printed is on the REAR face: the front
    # is under the etherCON. The board's name and revision between the contacts and the row;
    # the row's two end pins numbered under it, as the main board numbers them.
    silk = lay["silk"]
    tb = board.GetTitleBlock()
    tb.SetTitle(silk["title"])
    tb.SetRevision(silk["rev"])
    tb.SetDate(silk["date"])
    pcb._TWB[0] = board
    pcb.fit_footprint_silk(board, lay["fab"])
    pcb.silk_text(board, silk["title"], *at((0, 2.2)))
    pcb.silk_text(board, f"rev {silk['rev']}  {silk['date']}", *at((0, 4.0)))
    pcb.silk_text(board, "1", *at((j2(1)[0], ROW + 3.0)))
    pcb.silk_text(board, "8", *at((j2(8)[0] - 1.6, ROW + 3.0)))
    pcb.silk_text(board, "J-UMB", *at((1.3, ROW + 3.0)))

    pcb.save(board, OUT)
    pro = os.path.join(HERE, NAME + ".kicad_pro")
    j = json.load(open(pro))
    pcb.set_net_classes(j, lay)
    # fit_footprint_silk adapts the library footprints' silkscreen to the board house on
    # purpose, so "does not match the library copy" is expected, not a finding (as tools/pcb.py layout)
    j["board"]["design_settings"]["rule_severities"]["lib_footprint_mismatch"] = "ignore"
    json.dump(j, open(pro, "w"), indent=2)
    pcb.set_stackup(OUT, lay["fab"], geo["thickness"])
    print(f"adapter_layout: {n_seg} track segment(s), no via; wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
