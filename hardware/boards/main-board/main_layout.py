#!/usr/bin/env python3
"""The main board laid out by hand (issue #48, ADR 0030): every part placed on purpose here,
and every track and via written out below the placement.
NO ROUTER OF ANY KIND IS CALLED: not tools/pcb_route*.py, not Freerouting, not KiCad's.

    python3 hardware/boards/main-board/main_layout.py --place-only --out <file>   # the placement alone, to another file

THIS IS STAGE 2b: THE PLACEMENT, FOR REVIEW. No copper is written yet and the board file is
not rewritten: --out names the file the placement goes to. From the board it keeps what the
body CAD and the sheets fix - the outline, the switches, the mounts, the LEDs, J-MCU, J-UMB,
the sensor, the zones - refreshes every pad's net from the sheet (J-MCU's order moved,
carrier.md), seats both chain headers where the body CAD puts them, and seats every other
part where PLACE says. Body frame throughout: x along the body from the mouth, y across it
from the near side, mm, seen from above; every part but the switches is on the top face.

THE FLOORPLAN, and why each part is where it is.

1. A THROUGH-HOLE PIN IS A FREE LAYER CHANGE. Each chain header's pads, J-MCU's and the
   switches' reach both faces, so a line that starts or ends on one can run on the bottom
   face without a via at that end. The top face cannot carry the chain past a header
   without crossings: a header's five signal pads stand in one column that only opens
   toward the mouth, and the register behind it wants the same lines. So the chain's
   trunk (SCK, SH/LD, SER, the two hops, QH back) runs on the bottom face from pad to
   pad, and the top face carries only each header's short lines into its register.
2. EACH REGISTER STANDS ON THE MOUTH SIDE OF ITS HEADER, key row toward the far edge, pin 1
   at the header end. SH/LD then runs dead straight from the header's pad 4 through the
   clamp's body into pin 1, and SCK passes under the clamp and turns up into pin 2 from
   inside. The four key inputs (pins 3..6) face the far band, where the far-row keys'
   networks stand; the supply pins and the unused inputs face the LED row.
3. THE CLAMP (U-TVS-CHAIN) STANDS IN THE COLUMN BETWEEN THE REGISTER AND THE HEADER'S BODY,
   turned so the lines pass through it in the order the header gives them: SCK under its
   near row, SH/LD between its rows, the serial line into its far row.
4. THE FAR-ROW KEYS' NETWORKS STAND ABOVE THE REGISTER, the mouth-side key's on the mouth
   side and the tail-side key's on the tail side, so neither line crosses the other. THE
   NEAR-ROW KEYS' NETWORKS STAY AT THEIR SWITCHES, where #34 gave them their iron room;
   each of those four lines crosses the LED row on the bottom face.
5. EACH LED'S 100 nF STANDS IN THE ROW, on the mouth side of its LED beside the supply
   pad, not across the body from it: the bands either side of the row stay clear.
6. THE CHAIN'S SERIES RESISTORS STAND AT J-MCU, under the Matrix ribbon's fold, where the
   pins arrive; R-SER-TERM beside the one it pulls up.
7. THE ANALOG BLOCK, THE POWER BLOCK AND THE TAIL are as reviewed (#8, #33, #34, #45).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pcbnew       # noqa: E402
import pcb          # noqa: E402
import pcb_hand     # noqa: E402
import pcb_main     # noqa: E402

NAME = "main-board"
SRC = os.path.join(HERE, NAME + ".kicad_pcb")
RH = 108.0                    # the right hand's header, switches and register stand this far along from the left's
P = 1.27

# ---- a chain header and its register: the left hand's; the right's is RH further along ---------
JX, JY2 = 79.55, 38.84        # J-CHAIN's signal column (even pins), pin 2; pins 4..12 each 1.27 toward the far edge
UX, UY = 61.4, 38.4           # the register. y: its pin 1 pad takes SH/LD straight off pad 4. x: its courtyard 2 mm of iron room from the switch's ground pin


def jpin(k, dx=0.0):
    return (JX + dx + (P if k % 2 else 0), JY2 + P * ((k - 1) // 2))


def block(dx, r):
    """One hand's register block. r maps this function's names to that hand's references."""
    p = {
        r["U"]: (UX + dx, UY, ("1", (4.445, 2.475))),             # key row toward the far edge, pin 1 at the header end
        r["TVS"]: (69.0 + dx, jpin(4)[1], ("1", (-0.95, -1.1375))),  # SH/LD passes between its rows, level with pad 4
        r["FB"]: (69.0 + dx, jpin(10)[1], "-x"),                  # pad 2 level with the header's pad 10
        # the supply pins' capacitors, in the strip between the register and the LED row
        r["C16"]: (UX + dx + 3.5, 33.1, "+x"),                    # its 3V3 pad under pin 16
        # the far-row keys' networks, above the key row
        r["Cm"]: (58.3 + dx, 44.4, "+x"), r["Sm"]: (57.8 + dx, 47.3, "+x"), r["Pm"]: (61.35 + dx, 47.3, "+x"),
        r["Pt"]: (64.95 + dx, 44.4, "-x"), r["Ct"]: (64.95 + dx, 47.3, "+x"), r["St"]: (68.6 + dx, 47.3, "-x"),
    }
    return p


PLACE = {}
PLACE.update(block(0, {"U": "U7", "TVS": "U9", "FB": "FB1", "C16": "C13",
                       "Cm": "C16", "Sm": "R15", "Pm": "R14", "Pt": "R18", "Ct": "C18", "St": "R19"}))
PLACE.update(block(RH, {"U": "U8", "TVS": "U11", "FB": "FB2", "C16": "C205",
                        "Cm": "C20", "Sm": "R23", "Pm": "R22", "Pt": "R26", "Ct": "C22", "St": "R27"}))
PLACE.update({
    # REG-LT's own: its second capacitor under pin 13, the two unused inputs' pull-ups on toward the mouth, the hop's resistor at QH
    "C206": (61.1, 33.1, "+x"), "R33": (57.4, 33.1, "-x"), "R32": (53.7, 33.1, "-x"), "R44": (54.5, 35.9, "+x"),
    # REG-RT's own: its second capacitor under pin 12; the two spare positions' networks under and past its header's nose
    "C14": (UX + RH - 1.6, 33.1, "+x"),
    "R28": (181.2, 33.1, "-x"), "C23": (184.8, 33.1, "-x"), "R29": (188.4, 33.1, "-x"),
    "R30": (192.3, 33.1, "-x"), "C24": (195.9, 33.1, "-x"), "R31": (199.5, 33.1, "-x"),
    # the chain's series resistors under the Matrix ribbon's fold, the pull-up beside its line
    "R34": (269.6, 22.95, "+x"), "R35": (262.4, 22.95, "+x"), "R36": (257.0, 22.95, "+x"), "R37": (256.9, 25.3, "-x"),
    "C45": (252.6, 28.75, "-y"),
})
LED_CAP_DX = -5.6             # each LED's 100 nF: this far from its LED's centre, in the row
KEEP_CAP = ("C37", "C38")     # the two at the analog island keep their places (#33)

# Every part not named above keeps the place the reviewed board gave it.


def seat(fp, x, y, how):
    if isinstance(how, str) or how is None:
        return pcb_hand.seat(fp, x, y, how)
    pad, (dx, dy) = how
    fp.SetPosition(pcb.V(*pcb.to_pcb(x, y)))
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        px, py = pcb_hand.body_xy(fp.FindPadByNumber(pad).GetPosition())
        if abs(px - x - dx) < 0.03 and abs(py - y - dy) < 0.03:
            return
    raise SystemExit(f"main_layout: no turn puts {fp.GetReference()}'s pad {pad} at {dx, dy} from its centre")


GONE = []                     # zones taken off the board, held: pcbnew hands back no outline once Python frees one


def keepouts(board, geo, comps, fps):
    """The body CAD's no-part areas drawn again where the CAD has them now: the chain
    ribbons' moved with their headers. As pcb_main.build draws them."""
    import yaml
    from shapely.geometry import box
    spec_all = yaml.safe_load(open(os.path.join(HERE, "layout.yaml"))).get("keepouts") or {}
    rects = {}
    for kname, spec in spec_all.items():
        if spec.get("part"):
            q = geo["parts"][spec["part"]]
            rect = box(q[0] - q[3] / 2, q[1] - q[4] / 2, q[0] + q[3] / 2, q[1] + q[4] / 2)
        else:
            rect = box(*geo["keepouts"][kname][:4])
        for ref, fp in fps.items():
            if comps.get(ref, {}).get("row") in spec.get("except_rows", []) and not fp.IsFlipped():
                cy = pcb_main.courtyard_body(fp)
                if cy.intersects(rect):
                    rect = rect.difference(cy.buffer(0.05))
        rects[kname] = rect
    for z in list(board.Zones()):
        if z.GetIsRuleArea() and z.GetZoneName() in spec_all:
            board.Remove(z)
            GONE.append(z)
    for kname, rect in rects.items():
        pcb_main.rule_area(board, rect, kname, ["F.Cu"], footprints=True, copper=False)


def main():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    if "--place-only" not in sys.argv or not out:
        raise SystemExit("main_layout: stage 2b writes the placement only: --place-only --out <file>")
    comps, nets = pcb.sheet_netlist(os.path.join(HERE, NAME + ".kicad_sch"))
    geo = pcb_main.geometry("main")
    board = pcbnew.LoadBoard(SRC)
    # every pad's net from the sheet
    padnet = {(r, p): n for n, nodes in nets for r, p in nodes}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            n = padnet.get((fp.GetReference(), p.GetNumber()))
            if n is None:
                continue
            ni = board.FindNet(n)
            if ni is None:
                ni = pcbnew.NETINFO_ITEM(board, n)
                board.Add(ni)
            p.SetNet(ni)
    pcb_hand.strip(board)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for cname, ch in geo["chains"].items():
        side = cname.split("-")[-1]
        ref = [r for r, c in comps.items() if c["row"] == "J-CHAIN" and r in fps and fps[r].FindPadByNumber("10").GetNetname().endswith("_" + side)][0]
        pcb_hand.seat_chain(fps[ref], {"chain": ch}, lambda k, dx=(RH if side == "RH" else 0.0): jpin(k, dx))
    place = dict(PLACE)
    order = pcb_main.led_chain(comps, nets)
    caps = sorted((r for r, c in comps.items() if c["row"] == "C-LED"), key=lambda r: int(r[1:]))
    for n, (led, cap) in enumerate(zip(order, caps), 1):
        if cap not in KEEP_CAP:
            x, y = geo["leds"][n][:2]
            place[cap] = (x + LED_CAP_DX, y, "+x")
    for ref, (x, y, how) in place.items():
        seat(fps[ref], x, y, how)
    keepouts(board, geo, comps, fps)
    pcbnew.SaveBoard(out, board)
    print(f"main_layout: {len(place)} part(s) moved to their new places, the rest as reviewed; wrote {out}")


if __name__ == "__main__":
    sys.exit(main())
