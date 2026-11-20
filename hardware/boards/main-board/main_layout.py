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
7. THE CHAIN'S SERIES RESISTORS STAND IN ONE ROW AT J-MCU'S MOUTH END, SER's pull-up the
   fourth in the row; R-LED-SERIES stands below the first LED's data pad.
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
   resistors at the header's mouth end; the LED driver beside the first LED, pin 1
   tailward; the SPI resistors a row under the umbilical's pins, the reverse-polarity
   diode astride two of those lines at the pins; the breath resistors on their own pins'
   lines; the inrush switch in the corner beyond the pins; the MIDI clamp between the
   beads and J-MIDI's pins, clear of the lead that plugs in from the tail. The regulator
   stands as reviewed (#33, #34, #45) but for two turns: the inductor's input pad faces
   the regulator, and the OR-ing switch faces its controller so gate and 5 V run straight.

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
#   top, straight out from the even row: QH, and 5 V from pins 1-2 past the header's mouth end
#   bottom, under the odd row and north past the mouth end, seven lanes: IO33, IO35, IO36,
#   IO37, IO38, IO7, IO39 (inside to outside). IO39 turns toward the mouth first, IO7 and
#   IO38 end on vias under their resistors, the ADC's three turn next, IO33 ends last.
#   bottom, from the even row toward the tail: IO1, IO2, the service UART, 5 V to the LED driver
#   3V3 has no lane toward the mouth: its trunk starts at a via by R49, runs the bottom face
#   north of the even row's lines and comes down to R37, then lies south of the chain's trunk
#   (whose lines must rise to the chain headers) and north of the ADC's.
# Under the three 1206 bodies pass 5 V (south) and QH (north) on the top face; each chain
# line takes a via between two of their pads to the bottom trunk.
# Each resistor then stands where its line arrives, and nothing crosses on a face.
TRIO = 23.9                   # the chain's three series resistors: fed from J-MCU's mouth end by vias under them
SPI_Y = 19.5                  # the umbilical's SPI resistors, a row under its pins; 3V3 and IO36 pass under their bodies
BUS_U, BUS_G = 16.4, 14.5     # the inrush switch's two buses, UMBILICAL_POS12 over INRUSH_GATE
COL = (293.95, 296.4, 298.85) # ...and its three columns
PLACE.update({
    "R35": (247.7, TRIO, ("IO7", "S")), "R34": (250.7, TRIO, ("IO38", "S")), "R36": (253.7, TRIO, ("IO33", "S")),
    "R37": (256.7, TRIO + 0.55, ("3V3", "S")),   # SER's pull-up, its SER pad level with R36's; QH passes under its body
    "C45": (252.6, 28.5, "-y"),
    "L1": (247.8, 17.9, ("BUCK_IN", "W")),
    "Q2": (237.9, 19.45, ("INST_5V", "E")), "C208": (242.1, 20.6, ("INST_5V", "W")),   # its regulator side toward the regulator
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
    "FB3": (275.4, 38.96, ("TIP_R", "W")), "FB4": (275.4, 41.95, ("RING_R", "W")),
    "U12": (281.5, 41.0, ("1", (1.14, -0.95))),
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
    "R7": (20.6, REF_LINE, ("VS", "N")), "R8": (19.55, 24.0, ("VS", "E")),
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
    "NT2": (32.15, 15.2, None),          # astride the island's edge where the ADC's three SPI lines cross it
    # the sensor's supply capacitors beside its far pins, 3 mm apart
    "C202": (21.75, 47.4, ("VS", "S")), "C201": (24.75, 47.4, ("VS", "S")), "C8": (27.75, 47.4, ("VS", "S")),
})
LED_CAP_DX = -6.5             # each LED's 100 nF: this far from its LED's centre, in the row, a millimetre between courtyards
KEEP_CAP = ("C37", "C38")     # the two at the analog island keep their places (#33)

# Every part not named above keeps the place the reviewed board gave it.


# ============================== THE COPPER, BY HAND ==============================================
# Every track and via of the board is written out here: a net, a face, a width and the points
# it runs through, body frame, at 0, 45 and 90 degrees. A point given as "R7.2" is that pad's
# centre. Nothing below searches for a path.
CU, VIAS = [], []             # (net, "F" or "B", width, points); (net, x, y)
SIG, FINE, PWR = 0.25, 0.2, 0.4


def T(net, pts, w=SIG, face="F"):
    CU.append((net, face, w, list(pts)))


def via(net, x, y, pad=None, w=SIG):
    """A via, and with `pad` the short top-face track from that pad to it."""
    VIAS.append((net, x, y))
    if pad:
        T(net, [pad, (x, y)], w)


def analog():
    """STAGE 1: the analog block, at the mouth. Each line in the order its signal runs."""
    A = "AGND_INST"
    # the sensor's output: down the mouth edge clear of the sensor's unused pads, through its
    # capacitor's pad, into the buffer's + input
    T("SENSOR_RAW", ["U10.4", (10.34, 46.0), (9.2, 44.86), (9.2, 27.41), "U3.5"])
    # the buffer's output: one trunk under its own body, pins 6 and 7 a stub each. North it
    # leaves between pins 5 and 4 for the breath pair's via; south between pins 8 and 1, round
    # the mouth side of the feedback capacitor, into the ADC's divider
    T("SENSOR_BUFFERED_OUT", ["U3.6", (12.9, 26.14)])
    T("SENSOR_BUFFERED_OUT", ["U3.7", (12.9, 24.86)])
    T("SENSOR_BUFFERED_OUT", [(16.6, 28.4), (13.2, 28.4), (12.9, 28.1), (12.9, 22.9), (11.9, 21.9), (11.9, 18.6),
                              (13.25, 17.25), "R4.1"])
    via("SENSOR_BUFFERED_OUT", 16.6, 28.4)
    # the divider, the anti-alias capacitor, the ADC's input: under the row, clear of CS over it
    T("ADC_IN", ["R4.2", "R5.1", (19.09, 16.5), (19.39, 16.2), (23.25, 16.2), (23.55, 16.5), "C1.1"])
    T("ADC_IN", ["C1.1", (23.55, 13.9), (24.57, 12.88), "U2.2"])
    # the reference: from its pin under the row of its own pads, through its two capacitors,
    # between R-ISO-REF's pads, up under R-FB-REF's body, into the buffer's + input
    T("REF_5V", ["U4.6", (31.36, 19.4), (31.11, 19.15), (28.35, 19.15), (27.0, 20.5), (19.75, 20.5), (19.55, 20.7),
                 (19.55, 26.14), "U3.3"])
    # the reference buffer's loop
    T("BUF_OUT", ["U3.1", (16.5, 23.59), "R9.1"])
    T("BUF_OUT", ["R9.1", (17.2, 21.41), (19.02, 19.59), "R7.1"])
    T("AC_FB_MID", ["C9.2", (13.5, 19.57), (16.5, 19.57), "R9.2"])
    T("REF_MINUS", ["U3.2", (17.4, 24.86), (18.2, 24.06)])
    T("REF_MINUS", ["U3.2", (15.5, 24.86), (13.5, 22.86), "C9.1"])
    # VS: from R-ISO-REF through R-FB-REF's pad, straight up to the sensor's pin and its capacitors
    T("VS", [(20.5, 21.41), (20.5, 44.95), (19.75, 45.7), (15.42, 45.7), "U10.2"], PWR)
    T("VS", [(20.5, 44.95), (21.75, 46.2), "C202.1"], PWR)
    T("VS", ["C202.1", "C201.1", "C8.1"], PWR)
    # the reference's input: one bus through the north pads of its parts, under the unused pin 1
    T("REF_VIN", ["R6.2", (48.25, 24.5), (35.0, 24.5), (34.6, 24.1), (32.64, 24.1), "U4.2"], 0.3)
    # the ADC's supply: a bus under the row, a stub up into each capacitor, into pin 8
    T("ADC_VDD", ["R47.2", (42.89, 16.3), (42.54, 15.95), (30.47, 15.95), "U2.8"], PWR)
    T("ADC_VDD", [(37.47, 15.95), "C2.1"], PWR)
    T("ADC_VDD", [(32.03, 15.95), "C42.1"], PWR)
    T("ADC_VDD", [(30.47, 15.95), (29.6, 15.95), "C3.1"], PWR)
    # 12 V for the buffer, its capacitor at the pin; and for the reference's input resistor
    T("INST_POS12", ["U3.8", (10.6, 23.59), (9.96, 22.95), "C204.1"], PWR)
    via("INST_POS12", 8.9, 24.25, "C204.1", PWR)
    T("INST_POS12", ["R6.1", (47.5, 22.64), (47.5, 20.6)], PWR)
    via("INST_POS12", 47.5, 20.6)
    # every analog ground pad to the island under it, by its own via
    for pad, x, y in (("U10.3", 12.88, 45.3), ("C203.2", 9.95, 25.55), ("C204.2", 8.9, 19.9), ("U3.4", 17.9, 27.41),
                      ("C7.2", 24.0, 23.5), ("C5.2", 28.45, 23.44), ("U4.4", 30.09, 23.7), ("R5.2", 20.91, 18.4),
                      ("C1.2", 25.45, 18.45), ("C3.2", 27.7, 16.1), ("C42.2", 36.22, 17.25), ("C2.2", 41.69, 17.25),
                      ("U2.3", 23.75, 11.62), ("C6.2", 38.5, 21.2),
                      ("C202.2", 23.25, 48.35), ("C201.2", 26.25, 48.35), ("C8.2", 29.25, 48.35), ("NT2.1", 31.5, 15.2)):
        via(A, x, y, pad, PWR)
    T(A, ["U2.3", "U2.4"], PWR)
    T(A, ["D1.2", (45.9, 21.2), (45.9, 20.9)], PWR)
    via(A, 45.9, 20.9)
    T(A, ["C4.2", (40.76, 21.56), (40.3, 21.1)], PWR)
    via(A, 40.3, 21.1)
    # the one tie: NT-AGND astride the island's edge beside the ADC's digital pins, its plane side
    # taken clear of the three bottom-face lines to its via
    T("PWR_GND", ["NT2.2", (34.2, 15.2), (34.8, 14.6)], PWR)
    via("PWR_GND", 34.8, 14.6)
    # the ADC's four digital lines and its 3V3 arrive on the bottom face (digital(), below) and
    # come up here: CS at its pull-up, then on the top face over the row and down between two
    # ground pads into pin 1; the other three by a via each beside their pins
    via("IO39", 42.0, 20.2)
    T("IO39", [(42.0, 20.2), (42.65, 19.55)])
    T("IO39", ["R45.2", (41.99, 18.65), (27.23, 18.65), (26.58, 18.0), (26.58, 14.76), (25.98, 14.16)])
    via("IO35", 32.7, 12.88, "U2.7")
    via("IO37", 34.0, 11.62, "U2.6")
    via("IO36", 32.7, 10.34, "U2.5")
    via("DEV_3V3", 46.72, 23.6)
    T("DEV_3V3", [(46.72, 23.6), (46.72, 17.25), "R47.1"])
    T("DEV_3V3", [(46.72, 19.55), "R45.1"])
    X = 56.0                  # where digital() takes the bottom lanes up
    T("IO39", [(X, 21.55), (43.35, 21.55), (42.0, 20.2)], FINE, "B")
    T("IO37", [(X, 21.95), (34.4, 21.95), (34.0, 21.55), (34.0, 11.62)], FINE, "B")
    T("IO36", [(X, 22.35), (33.75, 22.35), (33.35, 21.95), (33.35, 10.99), (32.7, 10.34)], FINE, "B")
    T("IO35", [(X, 22.75), (33.1, 22.75), (32.7, 22.35), (32.7, 12.88)], FINE, "B")
    T("DEV_3V3", [(X, 23.6), (46.72, 23.6)], 0.3, "B")


MOUNTS_FAR = (37.8, 121.7, 145.8, 247.7)      # the far column mounts the breath pair steps round
PAIR_Y = (47.1, 47.6)                         # the pair along the far edge: AGND leg, signal


def breath_pair():
    """STAGE 1: THE BREATH PAIR, bottom face, the buffer's output and its AGND leg side by side
    from the buffer along the far edge to their series resistors at J-UMB, over an AGND strip
    in layer 3. The signal is the far-side line, so the AGND leg is between it and every key.
    Round each far mount both step inboard at 45 degrees, pass under it and step back."""
    ya, yo = PAIR_Y
    sig = [(16.6, 28.4), (16.6, yo - 0.3), (16.9, yo)]
    ret = [(17.9, 27.41), (17.9, 28.6), (17.1, 29.4), (17.1, ya - 0.3), (17.4, ya)]
    for cx in MOUNTS_FAR:
        lo, bo = 42.7, 1.33                   # the signal's line under the mount, and its half-length there
        la, ba = 42.2, 1.53
        sig += [(cx - bo - (yo - lo), yo), (cx - bo, lo), (cx + bo, lo), (cx + bo + (yo - lo), yo)]
        ret += [(cx - ba - (ya - la), ya), (cx - ba, la), (cx + ba, la), (cx + ba + (ya - la), ya)]
    # down past H11's mouth side to the resistors: the AGND leg inside the turn, so it arrives
    # on the mouth side of the signal's via and steps in under it
    ret += [(271.3, ya), (277.9, 40.5), (277.9, 35.55), (278.6, 34.85)]
    sig += [(271.3 + 0.707, yo), (278.6, yo - (278.6 - 271.3 - 0.707)), (278.6, 37.39)]
    T("SENSOR_BUFFERED_OUT", sig, SIG, "B")
    T("AGND_INST", ret, SIG, "B")
    via("SENSOR_BUFFERED_OUT", 278.6, 37.39, "R38.1")
    via("AGND_INST", 278.6, 34.85, "R39.1")


def breath_strip():
    """The AGND strip in layer 3 under the breath pair: both lines' paths grown by a
    millimetre, square at the ends so each end via stands on it. layout.yaml's islands:
    holds this outline for the checks; main() writes it there when the pair moves."""
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    lines = [pts for n, face, w, pts in copper()[0] if face == "B" and n in ("SENSOR_BUFFERED_OUT", "AGND_INST") and len(pts) > 8]
    g = unary_union([LineString(pts).buffer(1.0, cap_style=3, join_style=2) for pts in lines]).buffer(0.3, join_style=2).buffer(-0.3, join_style=2)
    g = g.simplify(0.02)
    return [[round(x, 2), round(y, 2)] for x, y in list(g.exterior.coords)[:-1]]


def strip_into_yaml():
    path = os.path.join(HERE, "layout.yaml")
    text = open(path).read()
    mark = "    # WRITTEN BY main_layout.py from the pair's own points (breath_strip): do not edit\n    outline: "
    i = text.index(mark) + len(mark)
    j = text.index("\n\n", i)
    pts = breath_strip()
    rows = [", ".join(f"[{x}, {y}]" for x, y in pts[k:k + 6]) for k in range(0, len(pts), 6)]
    new = "[" + (",\n              ".join(rows)) + "]"
    if text[i:j] != new:
        open(path, "w").write(text[:i] + new + text[j:])
        print("main_layout: layout.yaml's breath strip outline rewritten from the pair")


def planes(board, geo):
    """The planes and islands drawn again from layout.yaml (planes:, islands:), as
    pcb_main.build draws them; the router's moat keep-outs go, since nothing is routed."""
    lay = pcb.layout_yaml(HERE)
    outline = pcb_main.board_polygon(pcb_main.outline_segments(lay, geo))
    for z in list(board.Zones()):
        if not z.GetIsRuleArea() or z.GetZoneName().endswith(" moat"):
            board.Remove(z)
            GONE.append(z)
    isl = pcb_main.island_polys(lay)
    for pl in lay.get("planes") or []:
        region = outline
        for spec, p, moat in isl:
            if spec["layer"] == pl["layer"]:
                region = region.difference(moat)
        if region.geom_type == "MultiPolygon":
            region = max(region.geoms, key=lambda g: g.area)
        pcb_main.copper_zone(board, pl["net"], pl["layer"], region, 0, pl.get("name", pl["net"]))
    for spec, p, moat in isl:
        pcb_main.copper_zone(board, spec["net"], spec["layer"], p.intersection(outline), 1, spec["net"] + " island")
    return lay


STAGES = [analog, breath_pair]


def copper():
    """The lists, built once."""
    if not CU:
        for stage in STAGES:
            stage()
    return CU, VIAS


def square(n, pts, pad, slack=0.06):
    """A line's points with its pads' centres in. A pad's centre is not on the 0.05 grid the
    points are written on, so a track's end at a pad is moved by up to `slack` inside the pad
    to keep the track at 0, 45 or 90 degrees; a written point is never moved."""
    isp = [isinstance(q, str) for q in pts]
    out = [list(pad[tuple(q.split("."))]) if isinstance(q, str) else list(q) for q in pts]
    for _ in range(3):
        for i in range(len(out) - 1):
            a, b = out[i], out[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            if abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-6:
                continue
            m, f = (b, a) if isp[i + 1] else (a, b)      # the end that may move, the fixed one
            if not (isp[i] or isp[i + 1]):
                raise SystemExit(f"main_layout: {n}: {a} -> {b} is not at 0, 45 or 90 degrees")
            if abs(dx) < slack:
                m[0] = f[0]
            elif abs(dy) < slack:
                m[1] = f[1]
            elif abs(abs(dx) - abs(dy)) < slack:
                m[1] = f[1] + (abs(dx) if (m[1] > f[1]) else -abs(dx))
            else:
                raise SystemExit(f"main_layout: {n}: {a} -> {b} is not at 0, 45 or 90 degrees")
    return [tuple(q) for q in out]


def draw_copper(board):
    """The lists onto the board: pad names to their centres, short net names to the board's."""
    full = {}
    for name in (n.GetNetname() for n in board.GetNetInfo().NetsByName().values()):
        full.setdefault(str(name).split("/")[-1], []).append(str(name))
    pad = {(fp.GetReference(), p.GetNumber()): pcb_hand.body_xy(p.GetPosition()) for fp in board.GetFootprints() for p in fp.Pads()}
    cu = pcb_hand.Copper()
    tracks, vias = copper()

    def net(n):
        if len(full.get(n, [])) != 1:
            raise SystemExit(f"main_layout: {n} names {len(full.get(n, []))} nets on the board")
        return full[n][0]
    for n, face, w, pts in tracks:
        cu.track(net(n), square(n, pts, pad), w, pcbnew.F_Cu if face == "F" else pcbnew.B_Cu)
    for n, x, y in vias:
        cu.via(net(n), (x, y))
    cu.draw(board)
    return cu


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
    if not ({"--place-only", "--copper"} & set(sys.argv)) or not out:
        raise SystemExit("main_layout: --place-only --out <file> for the placement alone, --copper --out <file> with the copper drawn so far")
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
    if "--copper" in sys.argv:
        cu = draw_copper(board)
        strip_into_yaml()
        lay = planes(board, geo)
        print(f"main_layout: {cu.segments()} track segments and {len(cu.vias)} vias drawn by hand")
    pcbnew.SaveBoard(out, board)
    print(f"main_layout: {len(place)} part(s) moved to their new places, the rest as reviewed; wrote {out}")


if __name__ == "__main__":
    sys.exit(main())
