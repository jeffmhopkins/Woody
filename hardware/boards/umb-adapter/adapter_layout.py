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
face. J-UMB's socket (J2) stands on the rear face on the row the main board's header holds
its posts in, 7.7 below the axis, pin k over the main board's post k (tools/pcb_adapter.py
check_cad holds each pad to it). It is surface mount: nothing passes through the board under
the etherCON, whose body stands against the front face.

THE EIGHT LINES RUN STRAIGHT, ALL ON THE REAR FACE. Seen from the tail the etherCON's pin 1
is on the LEFT (an RJ45 jack with its latch notch down) and J-UMB's pin 1, as the main board
numbers it, is on the RIGHT. The cable's pin map is written for that (owner, 2026-11-22):
the etherCON's pin 9 - n carries J-UMB's pin n, so each line leaves its contact straight
down and steps out at 45 degrees to the socket's pad below it, and no two cross.

1. ONE FACE, NO VIA, NO POUR. Every pad is a through-hole. No conductor of the umbilical is
   a plane's: PWR_GND, DIG_GND and AGND_SENSE are three separate returns until the main
   board joins them (ADR 0018), so a pour here would belong to one of them.
2. THE ROW IS TWICE AS WIDE AS THE CONTACTS (2.54 against 1.27), so the post for the contact
   at x stands at 2x: every line drops to the row less its own |x| and then runs the diagonal.
   The diagonals each side are parallel, 1.8 apart.
3. THE UPPER ROW'S LINES PASS BETWEEN THE LOWER ROW'S PADS, 1.34 clear between pad edges:
   every line is the supply's width (owner, 2026-11-22: there is the room), with 0.37 each side.
4. THE PAIRS STAY SIDE BY SIDE (hardware/interfaces/spi-link/spi-link.md) because the order
   is kept: each of the cable's four pairs lands on the same two posts it always did.
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
TW, PW = 0.6, 0.6             # layout.yaml rules: track, power_track
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
       5: "/MOSI", 6: "/PWR_GND", 7: "/CS_MOD", 8: "/DIG_GND"}      # by J-UMB's pin n; checked against the sheet in main()
WIDTH = {3: PW, 6: PW}
def contact(n):
    """The etherCON's pin that carries J-UMB's pin n."""
    return 9 - n


SKT_OFF = 1.65                # the socket's pads either side of its row (the library footprint), turn about
FAN_Y = ROW - SKT_OFF - 0.95 - 0.5   # every diagonal is done by here: the upper pads' top edge, less half a millimetre


def straight(n, pad):
    """The etherCON's contact for J-UMB's pin n straight down, out at 45 degrees to stand over
    the socket's pad n, and down into it. A pad on the row's lower side is reached between
    two of the upper side's, 4.08 apart."""
    x, y = j1(contact(n))
    tx, ty = pad
    assert abs(tx - 2 * x) < 1e-6, (n, x, tx)
    return [(x, y), (x, FAN_Y - abs(tx - x)), (tx, FAN_Y), (tx, ty)]


def routes(pads):
    """(net, width, points, layer) for all eight lines, on the rear face."""
    return [(NET[n], WIDTH.get(n, TW), straight(n, pads[n]), B) for n in range(1, 9)]


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
    je, ju = fps[pcb.ref_of(comps, "J-UMBILICAL-INST")], fps[pcb.ref_of(comps, "J-UMB-SKT")]
    for (ref, pin), net in {(r, p): n for n, nodes in nets for r, p in nodes}.items():
        want = NET[int(pin)] if ref == ju.GetReference() else NET[9 - int(pin)]
        if want != net:
            sys.exit(f"adapter_layout: the sheet puts {ref} pin {pin} on {net}; this layout is drawn for {want}")

    # the etherCON: its origin on the axis, on the front face, latch up
    board.Add(je)
    je.SetPosition(pcb.V(*at((0, 0))))
    # J-UMB's socket stands on the REAR face, so the footprint is flipped; then turned until
    # pin 1 and pin 8 are over the main board's posts 1 and 8, its row on the body CAD's
    board.Add(ju)
    ju.SetPosition(pcb.V(*at((0, ROW))))
    ju.Flip(ju.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    own = lambda q: ((pcbnew.ToMM(q.x) - at((0, 0))[0]), (pcbnew.ToMM(q.y) - at((0, 0))[1]))
    for rot in (0, 90, 180, 270):
        ju.SetOrientationDegrees(rot)
        pads = {k: own(ju.FindPadByNumber(str(k)).GetPosition()) for k in range(1, 9)}
        if all(abs(pads[k][0] - j2(k)[0]) < 1e-3 and abs(abs(pads[k][1] - ROW) - SKT_OFF) < 1e-3 for k in range(1, 9)):
            break
    else:
        sys.exit("adapter_layout: no turn puts the socket's pads over J-UMB's posts")
    # the pad beside the etherCON's G tab must be on the row's UPPER side, away from it: with
    # the other hand of this footprint (Pin1Left) it would stand 0.25 from the tab's pad
    if pads[7][1] > ROW:
        sys.exit("adapter_layout: the socket's pad 7 is on the lower side, against the etherCON's G tab - the sheet wants the footprint's other hand")
    for fp in (je, ju):                      # their values are their BOM rows' words, longer than the board
        fp.Value().SetVisible(False)
    for k in range(1, 9):
        q = je.FindPadByNumber(str(k)).GetPosition()
        w = at(j1(k))
        assert abs(pcbnew.ToMM(q.x) - w[0]) < 1e-3 and abs(pcbnew.ToMM(q.y) - w[1]) < 1e-3, k

    n_seg = 0
    for net, w, pts, layer in routes(pads):
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
    pcb.silk_text(board, "1", *at((j2(1)[0], ROW + 3.8)))
    pcb.silk_text(board, "8", *at((j2(8)[0] - 1.6, ROW + 3.8)))
    pcb.silk_text(board, "J-UMB", *at((1.3, ROW + 3.8)))

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
