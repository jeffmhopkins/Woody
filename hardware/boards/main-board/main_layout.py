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
   face without a via at that end. The chain's trunk (SCK, SH/LD, SER, the two hops, QH
   back) runs on the bottom face from pad to pad, and each near-row key's leg crosses the
   LED row there; the top face carries each header's short lines into its register.
2. EACH REGISTER STANDS ON THE MOUTH SIDE OF ITS HEADER, key row toward the far edge, pin 1
   at the header end. SH/LD then runs from the header's pad 4 through the clamp into pin 1,
   and SCK passes under the clamp and turns up into pin 2 from inside. Its place along the
   body is the nearest that leaves the far-row switch's ground pin its iron room.
3. THE CLAMP (U-TVS-CHAIN) STANDS IN THE COLUMN BETWEEN THE REGISTER AND THE HEADER'S BODY,
   turned so the lines pass through it in the order the header gives them. That column is
   4.5 mm for a 3.5 mm part; it is the one tight place, and it is tight on purpose.
4. EVERY KEY'S THREE PARTS ARE ONE COMB: series resistor, capacitor, pull-up, standing side
   by side at 3 mm, their KEY pads at one end in a line. Every comb is the same.
   - the far-row key by the register: above the register, KEY end toward its pins;
   - the two keys on the tail side of the header: in the far band past the switch, their
     KEY lines passing over the header's last pins;
   - the near-row key on the mouth side: in the gap between two LEDs, its KEY line round
     the register's mouth end;
   - the two spare positions (right hand only): in the next two gaps between LEDs.
5. THE REGISTER'S OWN SMALL PARTS STAND IN ONE ROW between it and the LED row, level with
   the combs there; the capacitor of pin 16 stands on end beside that pin.
6. EACH LED'S 100 nF STANDS IN THE ROW, on the mouth side of its LED, a millimetre clear.
7. THE CHAIN'S SERIES RESISTORS STAND IN ONE ROW AT J-MCU, under the Matrix ribbon's fold,
   with R-LED-SERIES among them below the first LED's data pad.
8. THE ANALOG BLOCK IS LAID OUT ALONG ITS SIGNAL, from the sensor's pins outward (owner,
   2026-11-20: a fresh approach, best analog first):
   - the sensor's three live pins are on its far edge, RAW nearest the mouth, then AGND,
     then VS. The buffer stands under the sensor's near edge turned so RAW drops into its
     mouth-side column and VS leaves its tail-side column: the two run down under the
     sensor side by side with AGND between them. They used to cross there.
   - the reference buffer's feedback stands under and beside the pins it serves; REF_5V
     comes in along one line from the reference, tailward of the buffer, passing between
     R-ISO-REF's pads and R-FB-REF's so that it reaches its pin inside VS without a via.
   - the reference's input parts hang from REF_VIN's bus beyond the reference, the 12 V
     end last, nearest the supply.
   - the ADC stands in the band below, its analog pins toward the mouth and its SPI pins
     toward the tail; the divider, the anti-alias capacitor, its decoupling, its bulk and
     its supply resistor are ONE row above it, in signal order from the mouth.
   - nothing analog is within the LEDs' row, and no analog line crosses it on the top face.
9. THE TAIL END follows J-MCU's fan-out (the note over its PLACE entries): the chain's
   resistors at the header's mouth end, under the gap their lines climb to the far band;
   the LED driver beside the first LED, pin 1 tailward; the SPI resistors a row under the
   umbilical's pins, the reverse-polarity diode astride two of those lines at the pins;
   the breath resistors on their own pins' lines; the inrush switch in the corner beyond
   the pins. The regulator stands as reviewed (#33, #34, #45), its inductor turned to it.

SPACING, so that nothing is tight or a little off without a reason: a millimetre between
courtyards; parts side by side at 3 mm (0805), end to end at 4.5 mm; every row and comb
of the far band on one of two lines, y 33.0 and y 46.5, but the combs that stand in a gap
between LEDs, which sit a millimetre lower to clear the header's nose.
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
UX, UY = 61.5, 38.5           # the register: the nearest to the mouth that leaves SW2's ground pin its iron room
CX = 69.0                     # the column between the register and the header's body
LOW, HIGH = 33.0, 46.5        # the two lines every row and comb of the far band stands on
GAP = 32.0                    # a comb in a gap between LEDs: a millimetre lower, clear of the header's nose above it
SIDE, END = 3.0, 4.5          # 0805s side by side, and end to end


def jpin(k, dx=0.0):
    return (JX + dx + (P if k % 2 else 0), JY2 + P * ((k - 1) // 2))


def comb(x, y, key_end, series, cap, pull):
    """One key's network: the three parts side by side from x toward the tail, KEY pads at key_end."""
    return {r: (x + i * SIDE, y, ("KEY", key_end)) for i, r in enumerate((series, cap, pull))}


def block(dx, r):
    """What both hands' register blocks share. r maps the names here to that hand's references."""
    p = {
        r["U"]: (UX + dx, UY, ("1", (4.445, 2.475))),               # key row toward the far edge, pin 1 at the header end
        r["TVS"]: (CX + dx, jpin(4)[1], ("1", (-0.95, -1.1375))),    # SH/LD passes between its rows, level with pad 4
        r["FB"]: (CX + dx, 44.0, "-x"),                              # pad 2 level with the header's pad 10
        r["C16"]: (CX + dx, 35.25, ("3V3", "N")),                    # on end beside pin 16
    }
    p.update(comb(58.5 + dx, HIGH, "S", *r["far_mouth"]))            # above the register
    p.update(comb(98.5 + dx, HIGH, "N", *r["far_tail"]))             # past the tail-side switch
    p.update(comb(108.5 + dx, HIGH, "N", *r["near_tail"]))
    return p


PLACE = {}
PLACE.update(block(0, {"U": "U7", "TVS": "U9", "FB": "FB1", "C16": "C13",
                       "far_mouth": ("R15", "C16", "R14"), "far_tail": ("R19", "C18", "R18"), "near_tail": ("R17", "C17", "R16")}))
PLACE.update(block(RH, {"U": "U8", "TVS": "U11", "FB": "FB2", "C16": "C205",
                        "far_mouth": ("R23", "C20", "R22"), "far_tail": ("R27", "C22", "R26"), "near_tail": ("R25", "C21", "R24")}))
# the near-row key on the mouth side, in a gap between LEDs: the left hand's under its header's nose, the right hand's before its register
PLACE.update(comb(73.0, GAP, "N", "R13", "C15", "R12"))
PLACE.update(comb(150.5, GAP, "N", "R21", "C19", "R20"))
# the right hand's two spare positions, in the next two gaps
PLACE.update(comb(190.5, GAP, "S", "R29", "C23", "R28"))
PLACE.update(comb(210.5, GAP, "S", "R31", "C24", "R30"))
PLACE.update({
    # REG-LT's row: the two unused inputs' pull-ups, the hop's resistor at QH, pin 13's capacitor under it
    "R32": (50.5, LOW, ("FREE", "E")), "R44": (50.5 + END, LOW, ("QH", "E")),
    "R33": (50.5 + 2 * END, LOW, ("FREE", "E")), "C206": (50.5 + 3 * END, LOW, ("3V3", "W")),
    # REG-RT's: pin 12's capacitor
    "C14": (166.5, LOW, ("3V3", "E")),
})
# ---- the tail end: J-MCU's fan-out, the LED driver, the umbilical ---------------------------------
# J-MCU's odd pins can only leave toward the near edge and its even pins toward the far one,
# so which line leaves on which face, and round which end, is settled before any part stands:
#   top, round the TAIL end, nested: IO6, 3V3, IO36, IO35, IO34 (inside to outside)
#   top, round the MOUTH end: IO33; top, straight out from the even row: QH
#   bottom: the chain's IO38 and IO7 and the ADC's four, toward the mouth; IO1, IO2 and the
#   service UART from the even row
# Each resistor then stands where its line arrives, and nothing crosses on a face.
TRIO = 23.9                   # the chain's three series resistors: fed from J-MCU's mouth end, out toward the far band
SPI_Y = 19.5                  # the umbilical's SPI resistors, a row under its pins; 3V3 and IO36 pass under their bodies
BUS_U, BUS_G = 16.4, 14.5     # the inrush switch's two buses, UMBILICAL_POS12 over INRUSH_GATE
COL = (293.95, 296.4, 298.85) # ...and its three columns
PLACE.update({
    "R35": (247.7, TRIO, ("IO7", "S")), "R34": (250.7, TRIO, ("IO38", "S")), "R36": (253.7, TRIO, ("IO33", "S")),
    "R37": (256.7, TRIO, ("3V3", "S")),   # SER's pull-up beside its resistor; QH passes under all four bodies
    "C45": (252.6, 28.5, "-y"),
    "L1": (247.8, 17.9, ("BUCK_IN", "W")),   # its regulator side toward the regulator
    "R45": (43.8, 19.55, ("3V3", "E")),    # the ADC chip-select pull-up over R47, sharing its 3V3
    # the LED driver, pin 1 toward the tail: its LED output leaves under the body to R11 below
    # the first LED's data pad, its MIDI outputs leave the far end, IO6 comes up its tail side
    "U6": (270.9, 30.0, ("1", "SE")),
    "R11": (265.43, TRIO, ("LED_DI", "N")), "C12": (268.43, 23.6, ("INST_5V", "N")),
    "R10": (275.6, 25.4, ("IO1", "N")),
    "R51": (268.43, 37.5, ("RING_DRV", "S")), "R50": (271.43, 37.5, ("TIP_DRV", "S")),
    # the nest round J-MCU's tail end, in the order the lines arrive: IO6's pull-up where it
    # crosses 3V3, IO2's on a branch of 3V3, the clamp astride the three SPI lines, the three
    # series resistors, and CS's pull-up closing the row
    "R48": (276.72, 20.81, ("IO6", "N")), "R49": (279.0, 24.5, ("IO2", "N")),
    "U1": (277.0, 16.85, ("1", "NE")),
    "R1": (280.3, SPI_Y, ("SCLK", "N")), "R2": (283.3, SPI_Y, ("MOSI", "N")), "R3": (286.3, SPI_Y, ("CS_MOD", "N")),
    "R40": (289.0, SPI_Y - 0.55, ("IO34", "S")),
    "R46": (285.5, 15.6, ("TXD_HDR", "W")),
    # at the umbilical's pins: the reverse-polarity diode astride SCLK and MOSI, its pads on
    # the 12 V pin and the ground pin; the surge diode on a stub beside it
    "D2": (290.5, 28.2, ("UMBILICAL", "N")), "D3": (283.75, 29.6, ("UMBILICAL", "N")),
    "C46": (280.6, 28.0, ("INST_POS12", "N")),
    "NT1": (293.6, 19.61, ("DIG_GND", "E")),
    # the breath pair's resistors on their pins' own lines; a clamp hanging from each line
    "R38": (281.3, 37.39, ("BREATH_SENSE", "E")), "R39": (281.3, 34.85, ("AGND_SENSE", "E")),
    "D5": (292.2, 36.36, ("BREATH", "E")), "D6": (292.2, 34.15, ("AGND_SENSE", "E")),
    # MIDI: each bead in line with its pin of J-MIDI
    "FB3": (281.85, 40.0, ("TIP_R", "W")), "FB4": (281.85, 42.0, ("RING_R", "W")),
    # the inrush switch in the free corner beyond the pins, 12 V reaching it down the tail edge:
    # three columns on two buses, each gate part under the rung it hangs from
    "Q1": (COL[0] - 0.94, (BUS_U + BUS_G) / 2, ("2", "NE")),
    "C39": (COL[1], (BUS_U + BUS_G) / 2, ("UMBILICAL", "N")), "R41": (COL[2], (BUS_U + BUS_G) / 2, ("UMBILICAL", "N")),
    "C40": (COL[0], 11.75, ("INRUSH_GATE", "N")), "D21": (COL[1], 10.85, ("INRUSH_GATE", "N")),
    "R42": (COL[2], 11.6, ("INRUSH_GATE", "N")),
    "R43": (COL[0] - 0.9, 8.8, ("MILLER", "E")),
})
# ---- the analog block, at the mouth end ---------------------------------------------------------
ADC_ROW = 17.25               # the ADC's row: divider, anti-alias, decoupling, bulk, supply resistor
REF_LINE = 20.5               # REF_5V's line from the reference to the buffer; the feedback parts stand on it
PLACE.update({
    # the buffer under the sensor's near edge, turned so SENSOR_RAW drops into pin 5 on the mouth
    # side and VS leaves on the tail side: the two no longer cross under the sensor
    "U3": (14.0, 25.5, ("5", "NW")),
    "C203": (8.9, 26.5, ("SENSOR_RAW", "N")), "C204": (8.9, 22.0, ("INST_POS12", "N")),
    # the reference buffer's feedback: C9 and R9 under the pins they serve, R7 and R8 in the
    # corridor VS climbs; REF_5V passes between R7's pads and between R8's to reach pin 3 inside VS
    "C9": (13.5, REF_LINE, ("REF_MINUS", "N")), "R9": (16.5, REF_LINE, ("BUF_OUT", "N")),
    "R7": (20.5, REF_LINE, ("VS", "N")), "R8": (19.55, 24.0, ("VS", "E")),
    # the reference, tailward on the same line: its output capacitors on the line, its input
    # parts hanging from REF_VIN's bus beyond it, the 12 V end last
    "C7": (24.0, REF_LINE + 0.95, ("REF_5V", "S")), "C5": (27.0, REF_LINE + 1.46, ("REF_5V", "S")),
    "U4": (32.0, 23.0, ("5", "SW")),
    "C6": (38.5, 23.55, ("REF_VIN", "N")), "C4": (41.75, 23.04, ("REF_VIN", "N")),
    "D1": (45.0, 22.85, ("REF_VIN", "N")), "R6": (48.25, 23.55, ("REF_VIN", "N")),
    # the ADC in the band below, analog pins toward the mouth, SPI toward the tail; everything
    # that hangs on it in ONE row above it, in signal order from the mouth
    "U2": (28.0, 12.25, ("1", "NW")),
    "R4": (15.5, ADC_ROW, ("SENSOR_BUFFERED", "W")), "R5": (20.0, ADC_ROW, ("ADC_IN", "W")),
    "C1": (24.5, ADC_ROW, ("ADC_IN", "W")), "C3": (28.65, ADC_ROW, ("ADC_VDD", "E")),
    "C42": (33.5, ADC_ROW, ("ADC_VDD", "W")), "C2": (38.95, ADC_ROW, ("ADC_VDD", "W")),
    "R47": (43.8, ADC_ROW, ("ADC_VDD", "W")),
    "NT2": (32.6, 9.0, None),
    # the sensor's supply capacitors beside its far pins, 3 mm apart
    "C202": (21.75, 47.4, ("VS", "S")), "C201": (24.75, 47.4, ("VS", "S")), "C8": (27.75, 47.4, ("VS", "S")),
})
LED_CAP_DX = -6.5             # each LED's 100 nF: this far from its LED's centre, in the row, a millimetre between courtyards
KEEP_CAP = ("C37", "C38")     # the two at the analog island keep their places (#33)

# Every part not named above keeps the place the reviewed board gave it.


def seat(fp, x, y, how):
    """how: a pcb_hand.seat way; None to keep the turn it has; (pad, (dx, dy)) for the pad
    that must lie there from the centre; (net, side) for the pad whose net's name contains
    `net` to lie on the N (far), S (near), E (tail) or W (mouth) side; (pad, corner) for an
    IC's pad to lie in the NW, NE, SW or SE corner."""
    if how is None:
        fp.SetPosition(pcb.V(*pcb.to_pcb(x, y)))
        return
    if isinstance(how, str):
        return pcb_hand.seat(fp, x, y, how)
    fp.SetPosition(pcb.V(*pcb.to_pcb(x, y)))
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        if isinstance(how[1], str) and how[1] in ("NW", "NE", "SW", "SE"):
            px, py = pcb_hand.body_xy(fp.FindPadByNumber(how[0]).GetPosition())
            if (("N" in how[1]) == (py > y)) and (("E" in how[1]) == (px > x)):
                return
        elif isinstance(how[1], str):
            pads = [q for q in fp.Pads() if how[0] in q.GetNetname().split("/")[-1]]
            if len(pads) != 1:
                raise SystemExit(f"main_layout: {fp.GetReference()} has {len(pads)} pads on a net named {how[0]}")
            px, py = pcb_hand.body_xy(pads[0].GetPosition())
            dx, dy = px - x, py - y
            if {"N": dy > 0.3, "S": dy < -0.3, "E": dx > 0.3, "W": dx < -0.3}[how[1]]:
                return
        else:
            px, py = pcb_hand.body_xy(fp.FindPadByNumber(how[0]).GetPosition())
            if abs(px - x - how[1][0]) < 0.03 and abs(py - y - how[1][1]) < 0.03:
                return
    raise SystemExit(f"main_layout: no turn puts {fp.GetReference()} as {how}")


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
