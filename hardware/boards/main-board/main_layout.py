#!/usr/bin/env python3
"""The main board laid out by hand (issue #48, ADR 0030): every part placed on purpose here,
and every track and via written out below the placement.
NO ROUTER OF ANY KIND IS CALLED: not tools/pcb_route*.py, not Freerouting, not KiCad's.

    python3 hardware/boards/main-board/main_layout.py                             # rewrites main-board.kicad_pcb
    python3 hardware/boards/main-board/main_layout.py --place-only --out <file>   # a trial: the placement alone
    python3 hardware/boards/main-board/main_layout.py --copper --out <file>       # a trial: with the copper, unfinished

From the board it keeps what the body CAD and the sheets fix - the outline, the switches, the
mounts, the LEDs, J-MCU, J-UMB, the sensor - refreshes every pad's net from the sheet, seats
both chain headers where the body CAD puts them, and seats every other part where PLACE
says. Then the copper, a stage a function in STAGES, each line in the order its signal runs;
the planes and islands from layout.yaml; the silkscreen; and the planes poured. Body frame
throughout: x along the body from the mouth, y across it from the near side, mm, seen from
above; every part but the switches is on the top face.

THE LAYERS. 1, the top face: the parts, the analog block's lines, the LED data line, the
power paths, each header's short lines into its register. 2: PWR_GND, one piece, and the
AGND_INST island under the analog block. 3: INST_POS12, one piece, and the AGND strip under
the breath pair. 4, the bottom face: the breath pair along the far edge, the chain's trunk
north of the LED row, the ADC's four lines and 3V3 south of it, and each near-row key's line
where it crosses under the row. Neither outer face has a pour.

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
of the far band on one of two lines, y 33.2 and y 46.5, but the combs that stand in a gap
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
JX, JY2 = 77.865, 39.29       # J-CHAIN's signal column (even pins, the mouth side), pin 2; pins 4..10 each 1.27 toward the far edge
UX, UY = 65.5, 38.5           # the register: a clamp's width from the header, so the chain's lines are short (owner, 2026-11-21)
CX = 73.0                     # the column between the register and the header's body
LOW, HIGH = 33.2, 46.5        # the two lines every row and comb of the far band stands on
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
        r["FB"]: (CX + dx, 44.0, "-x"),                              # pad 2 just under the header's pad 10, one line and a short 45 away
        r["C16"]: (CX - 1.3 + dx, 35.25, ("3V3", "N")),              # on end hard beside pin 16
    }
    p.update(comb(62.5 + dx, HIGH, "N", *r["far_mouth"]))            # above the register
    p.update(comb(98.5 + dx, HIGH, "N", *r["far_tail"]))             # past the tail-side switch
    p.update(comb(108.5 + dx, HIGH, "N", *r["near_tail"]))
    return p


PLACE = {}
PLACE.update(block(0, {"U": "U7", "TVS": "U9", "FB": "FB1", "C16": "C13",
                       "far_mouth": ("R15", "C16", "R14"), "far_tail": ("R19", "C18", "R18"), "near_tail": ("R17", "C17", "R16")}))
PLACE.update(block(RH, {"U": "U8", "TVS": "U11", "FB": "FB2", "C16": "C205",
                        "far_mouth": ("R23", "C20", "R22"), "far_tail": ("R27", "C22", "R26"), "near_tail": ("R25", "C21", "R24")}))
# the near-row key on the mouth side, in a gap between LEDs: the left hand's under its header's nose, the right hand's before its register
PLACE.update(comb(74.0, GAP, "N", "R13", "C15", "R12"))
PLACE.update(comb(150.5, GAP, "N", "R21", "C19", "R20"))
# the right hand's two spare positions, in the next two gaps
PLACE.update(comb(190.5, GAP, "N", "R29", "C23", "R28"))
PLACE.update(comb(210.5, GAP, "N", "R31", "C24", "R30"))
PLACE.update({
    # REG-LT's row, in the order of the pins it serves so that no two of its lines cross: the
    # hop's resistor (pin 9), the two unused inputs' pull-ups (pins 11 and 12), and pin 13's
    # capacitor with each pad under its own pin
    "R44": (54.7, LOW, ("QH", "E")), "R33": (58.6, LOW, ("FREE", "E")),
    "R32": (62.5, LOW, ("FREE", "E")), "C206": (67.09, LOW, ("3V3", "W")),
    # REG-RT's: the capacitor of pins 11 and 12, each pad under its own pin
    "C14": (172.23, LOW, ("3V3", "E")),
})
# ---- the tail end: J-MCU's fan-out, the LED driver, the umbilical ---------------------------------
# J-MCU's odd pins can only leave toward the near edge and its even pins toward the far one,
# so which line leaves on which face, and round which end, is settled before any part stands:
#   top, round the TAIL end, nested: IO6, 3V3, IO36, IO35, IO34 (inside to outside)
#   top, straight out from the even row: QH, and 5 V from pins 1-2 past the header's mouth end
#   bottom, under the odd row and north past the mouth end, six lanes: IO35, IO36, IO37,
#   IO38, IO7, IO39 (inside to outside). IO39 turns toward the mouth first, IO7 and IO38
#   end on vias under their resistors, the ADC's three turn next. IO33 goes the same way
#   round on the top face: the row's pads leave room for six lanes under them, not seven.
#   bottom, from the even row toward the tail: IO1, IO2, the service UART, 5 V to the LED driver
#   3V3 has no lane toward the mouth: its trunk starts at a via by R49, runs the bottom face
#   north of the even row's lines and comes down to R37, then lies south of the chain's trunk
#   (whose lines must rise to the chain headers) and north of the ADC's.
# Under the three 1206 bodies pass 5 V (south) and QH (north) on the top face; each chain
# line takes a via between two of their pads to the bottom trunk.
# Each resistor then stands where its line arrives, and nothing crosses on a face.
TRIO = 24.35                  # the chain's three series resistors: fed from J-MCU's mouth end by vias under them
SPI_Y = 19.65                  # the umbilical's SPI resistors, a row under its pins; 3V3 and IO36 pass under their bodies
BUS_U, BUS_G = 16.4, 14.5     # the inrush switch's two buses, UMBILICAL_POS12 over INRUSH_GATE
COL = (293.95, 296.4, 298.85) # ...and its three columns
PLACE.update({
    "R35": (248.3, TRIO, ("IO7", "S")), "R34": (251.3, TRIO, ("IO38", "S")), "R36": (254.3, TRIO, ("IO33", "S")),
    "R37": (256.7, TRIO + 0.55, ("3V3", "S")),   # SER's pull-up, its SER pad level with R36's; QH passes under its body
    "C45": (252.0, 28.5, "-x"),            # in the LED capacitors' row, a millimetre from the first one
    "L1": (246.3, 17.9, ("BUCK_IN", "W")),
    "Q2": (237.9, 19.45, ("INST_5V", "E")), "C208": (241.35, 23.0, ("INST_5V", "N")),   # its regulator side toward the regulator
    "R45": (43.8, 19.55, ("3V3", "E")),    # the ADC chip-select pull-up over R47, sharing its 3V3
    # the LED driver, pin 1 toward the tail, on the mouth side of the Matrix ribbon's rise. Its
    # LED output leaves under the body to R11; its MIDI outputs leave the far end
    "U6": (264.4, 30.0, ("1", "SE")),
    "R11": (265.5, 23.6, ("GATE_A_OUT", "N")), "C12": (261.93, 23.6, ("INST_5V", "N")),
    "R10": (269.1, 24.8, ("IO1", "N")),
    "R51": (261.93, 37.94, ("RING_DRV", "S")), "R50": (264.93, 37.94, ("TIP_DRV", "S")),
    "R49": (258.75, 32.54, ("IO2", "E")),   # IO2's pull-up at the driver's pin, its 3V3 from the line going north there
    # the first LED stands in the row's tail-end place, clear of the Matrix ribbon (owner,
    # 2026-11-20). On its mouth side in the row: the surge diode, then the LED's capacitor,
    # whose 12 V passes between the diode's pads
    "D3": (276.35, 28.5, ("UMBILICAL", "N")), "C26": (272.4, 28.5, "+x"),
    "C46": (274.6, 34.2, ("INST_POS12", "W")),
    # the nest round J-MCU's tail end, in the order the lines arrive: IO6's pull-up where it
    # crosses 3V3, IO2's on a branch of 3V3, the clamp astride the three SPI lines, the three
    # series resistors, and CS's pull-up closing the row
    "R48": (276.72, 21.7, ("IO6", "N")),
    "U1": (277.0, 16.85, ("1", "NE")),
    "R1": (280.3, SPI_Y, ("SCLK", "N")), "R2": (283.3, SPI_Y, ("MOSI", "N")), "R3": (286.3, SPI_Y, ("CS_MOD", "N")),
    "R40": (289.0, SPI_Y - 0.55, ("IO34", "S")),
    "R46": (285.5, 15.6, ("TXD_HDR", "W")),
    # at the umbilical's pins: the reverse-polarity diode astride SCLK and MOSI, its pads on
    # the 12 V pin and the ground pin; the surge diode on a stub beside it
    "D2": (290.5, 28.2, ("UMBILICAL", "N")),
    "NT1": (293.6, 19.61, ("DIG_GND", "E")),
    # the breath pair's resistors on their pins' own lines; a clamp hanging from each line
    "R38": (281.3, 37.39, ("BREATH_SENSE", "E")), "R39": (281.3, 34.85, ("AGND_SENSE", "E")),
    "D5": (292.2, 36.36, ("BREATH", "E")), "D6": (292.2, 34.15, ("AGND_SENSE", "E")),
    # MIDI: each bead in line with its pin of J-MIDI
    "FB3": (275.4, 39.4, ("TIP_R", "W")), "FB4": (275.4, 41.95, ("RING_R", "W")),
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
    # turned a quarter turn (2026-11-21, with the LED row): its output pin faces its capacitors and
    # its input pin its input parts, and its pads stand clear of the LEDs' band
    "U4": (32.85, 22.0, ("5", "NW")),
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
KEEP_CAP = ("C38", "C26")     # the mouth-end LED's stands north of it, off the sensor; the first LED's is beyond the surge diode
PLACE["C11"] = (237.0, 12.5, ("BUCK_IN", "N"))   # its input pad level with the inductor and the regulator
PLACE["C43"] = (220.0, 18.3, ("BUCK_A_OUT", "E"))   # its output pad over the regulator's output pin
PLACE["C38"] = (26.3, 33.0, ("INST_POS12", "W"))

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
    T("SENSOR_RAW", ["U10.4", (10.34, 46.0), (9.2, 44.86), (9.2, 28.01), (9.8, 27.41), "U3.5"])
    # the buffer's output: one trunk under its own body, pins 6 and 7 a stub each. North it
    # leaves between pins 5 and 4 for the breath pair's via; south between pins 8 and 1, round
    # the mouth side of the feedback capacitor, into the ADC's divider
    T("SENSOR_BUFFERED_OUT", ["U3.6", (12.9, 26.14)])
    T("SENSOR_BUFFERED_OUT", ["U3.7", (12.9, 24.86)])
    T("SENSOR_BUFFERED_OUT", [(16.6, 28.4), (13.2, 28.4), (12.9, 28.1), (12.9, 22.9), (11.9, 21.9), (11.9, 18.6),
                              (13.25, 17.25), "R4.1"])
    via("SENSOR_BUFFERED_OUT", 16.6, 28.4)
    # the divider, the anti-alias capacitor, the ADC's input: under the row, clear of CS over it
    T("ADC_IN", ["R4.2", "R5.1", (19.09, 16.5), (19.39, 16.2), (23.55, 16.2)])
    T("ADC_IN", ["C1.1", (23.55, 13.9), (24.57, 12.88), "U2.2"])
    # the reference: straight out of its pin, through its two capacitors, between R-ISO-REF's
    # pads, up under R-FB-REF's body, into the buffer's + input
    T("REF_5V", ["U4.6", (29.14, 22.64), (27.0, 20.5), (19.75, 20.5), (19.55, 20.7), (19.55, 25.49), (18.9, 26.14), "U3.3"])
    # the reference buffer's loop
    T("BUF_OUT", ["U3.1", (16.5, 23.59), "R9.1"])
    T("BUF_OUT", ["R9.1", (17.2, 21.41), (19.02, 19.59), "R7.1"])
    T("AC_FB_MID", ["C9.2", (13.5, 19.57), (16.5, 19.57), "R9.2"])
    T("REF_MINUS", ["U3.2", (17.4, 24.86), (18.2, 24.06)])
    T("REF_MINUS", ["U3.2", (15.5, 24.86), (13.5, 22.86), "C9.1"])
    # VS: from R-ISO-REF through R-FB-REF's pad, straight up to the sensor's pin and its capacitors
    T("VS", [(20.5, 21.41), (20.5, 44.95), (19.75, 45.7), (16.22, 45.7), (15.42, 46.5), "U10.2"], PWR)
    T("VS", [(20.5, 44.95), (21.75, 46.2), "C202.1"], PWR)
    T("VS", ["C202.1", "C201.1", "C8.1"], PWR)
    # the reference's input: one bus through the north pads of its parts, then down between
    # C-REF-IN's pads and the reference's own into pin 2
    T("REF_VIN", ["R6.2", (48.25, 24.5), (37.44, 24.5), (37.04, 24.1), (37.04, 21.77), (36.64, 21.37), "U4.2"], 0.3)
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
                      ("C7.2", 24.0, 23.5), ("C5.2", 28.45, 23.44), ("U4.4", 33.5, 23.91), ("R5.2", 20.91, 18.4),
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
    T("DEV_3V3", [(46.72, 23.6), (46.72, 17.75), (46.22, 17.25), "R47.1"])
    T("DEV_3V3", [(46.72, 19.55), "R45.1"])
    # the five bottom lanes from J-MCU end here; tail() draws them as far as HWY
    T("IO39", [(HWY, MOUTH["IO39"]), (43.35, 21.55), (42.0, 20.2)], FINE, "B")
    T("IO37", [(HWY, MOUTH["IO37"]), (34.4, 21.95), (34.0, 21.55), (34.0, 11.62)], FINE, "B")
    T("IO36", [(HWY, MOUTH["IO36"]), (33.75, 22.35), (33.35, 21.95), (33.35, 10.99), (32.7, 10.34)], FINE, "B")
    T("IO35", [(HWY, MOUTH["IO35"]), (33.1, 22.75), (32.7, 22.35), (32.7, 12.88)], FINE, "B")
    T("DEV_3V3", [(HWY, MOUTH["DEV_3V3"]), (46.72, 23.6)], 0.3, "B")


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


def jx(n):
    """J-MCU pin n's x: two rows of twelve, the odd row nearest the near edge."""
    return 255.28 + 1.27 * ((n - 1) // 2)


TRUNK, LANE_D1, LANE_DI = 28.3, 29.05, 29.75   # three bottom lanes under the LED driver: 3V3, and the first LED's two data lines
HWY = 48.0      # where tail()'s bottom lanes hand over to analog()'s
# The five lines that run the board's length on the bottom face, south of the LED row and
# north of the near-row switches. They hold LANE, which clears the U-bolt's leg, in one
# straight run to the analog block (owner, 2026-11-21: no jog on the way). There, where 3V3
# leaves them, they step once, together, to MOUTH, which lets 3V3 come up inside the analog
# island south of REF_VIN's line.
LANE = {"IO39": 22.3, "IO37": 22.7, "IO36": 23.1, "IO35": 23.5, "DEV_3V3": 24.0}
MOUTH = {"IO39": 21.55, "IO37": 21.95, "IO36": 22.35, "IO35": 22.75, "DEV_3V3": 23.6}
STEP_X = 49.6    # the step, at the analog block's tail side


def step(net):
    """A lane's step from LANE to MOUTH, each a little before the one south of it so the
    diagonals keep the lanes' spacing."""
    i = list(LANE).index(net)
    x = STEP_X - 0.166 * i - (0.1 if net == "DEV_3V3" else 0)
    d = LANE[net] - MOUTH[net]
    return [(x, LANE[net]), (x - d, MOUTH[net]), (HWY, MOUTH[net])]


def two(net, x, y, up=1.5):
    """Two vias side by side beside a wide pad, each on its own track straight out of it:
    the pad's centre line is `up` from the vias."""
    for dx in (-0.6, 0.6):
        T(net, [(x + dx, y - up), (x + dx, y)], PWR)
        VIAS.append((net, x + dx, y))


def power():
    """STAGE 2: POWER. 12 V comes in at J-UMB pin 3, passes the inrush switch and drops into the
    layer-3 plane beside it; the plane carries it to the regulator's inductor. The regulator's
    loop is on top and short: inductor, input capacitor, U5, output capacitor. 5 V leaves the
    OR-ing switch on top, under the three 1206 bodies, to J-MCU pins 1 to 3, and goes on under
    the header on the bottom face to the LED driver. 3V3 is J-MCU pin 15 round the tail end (drawn in
    stage 3); its trunk starts by R49 and runs the bottom face toward the mouth."""
    # 12 V entry and the inrush switch
    T("UMBILICAL_POS12", ["J6.3", (290.5, 32.31)], 0.8)
    T("UMBILICAL_POS12", [(290.5, 32.31), (278.16, 32.31), "D3.1"], 0.6)   # to the surge diode, north of the first LED
    T("UMBILICAL_POS12", ["J6.3", (296.4, 32.31), (297.6, 31.11), (297.6, 16.4)], 0.6)
    T("UMBILICAL_POS12", ["Q1.2", "C39.1", (297.6, 16.4), (298.85, 16.4)], 0.5)
    T("INRUSH_GATE", ["Q1.1", "C39.2", (298.25, 14.5), (298.85, 13.9), "R42.1"])
    T("INRUSH_GATE", ["Q1.1", "C40.1"])
    T("INRUSH_GATE", ["C39.2", "D21.1"])
    T("INRUSH_MILLER", ["C40.2", (293.95, 8.8)])
    # the switch's drain into the plane carries the whole instrument: three vias on one bar (#8-6)
    via("INST_POS12", 291.0, 15.45, "Q1.3", 0.5)
    T("INST_POS12", [(291.0, 14.5), (291.0, 16.4)], 0.5)
    VIAS.extend([("INST_POS12", 291.0, 14.5), ("INST_POS12", 291.0, 16.4)])
    via("INST_POS12", 291.1, 8.8, "R43.2")
    T("PWR_GND", ["J6.6", (291.5, 24.69)], 0.8)
    T("DIG_GND", ["J6.8", "NT1.1"], 0.5)
    # the regulator: 12 V up from the plane below the inductor, then the loop
    for at, x in (((248.1, 15.5), 248.1), ((249.0, 15.5), 249.0)):
        via("INST_POS12", x, 14.9, at, PWR)
    # the bulk capacitors, the regulator's input capacitor and its output capacitor: two vias a
    # pad, since each carries a supply's pulse current (#8-6)
    two("INST_POS12", 209.5, 20.2)       # C44.1
    two("INST_POS12", 209.5, 13.0)       # C10.1
    T("BUCK_IN", [(244.05, 15.4), (237.0, 15.4), (226.1, 15.4)], 0.6)   # one straight line: inductor, input capacitor, regulator
    T("BUCK_A_OUT", ["U5.3", (221.02, 17.84), "C43.1", (222.63, 19.45), "C207.2", "U13.3"], 0.5)
    T("BUCK_A_OUT", ["U13.3", (232.16, 18.5), "Q2.2"], 0.5)
    T("BUCK_A_OUT", ["U13.3", (233.0, 19.45), (233.3, 19.75), (233.3, 21.05), (233.6, 21.35), "U13.6"])
    T("USBOR_GATE", ["U13.5", "Q2.1"])
    T("USBOR_VCAP", ["C207.1", "U13.1"])
    for pad, x, y in (("U13.2", 231.0, 20.4), ("C208.2", 241.35, 20.6), ("C43.2", 217.1, 18.3)):
        via("PWR_GND", x, y, pad, PWR)
    T("PWR_GND", [(217.1, 18.3), (217.1, 17.2)], PWR)
    VIAS.append(("PWR_GND", 217.1, 17.2))
    two("PWR_GND", 237.0, 12.15, 2.35)   # C11.2, under its body
    two("PWR_GND", 214.9, 20.2)          # C44.2
    two("PWR_GND", 214.9, 13.0)          # C10.2
    # 5 V
    T("INST_5V_A", ["J1.3", "J1.1", "J1.2"], 0.5)
    T("INST_5V_A", ["J1.2", (255.58, 19.1), (255.58, 23.65), (255.28, 23.95), (240.4, 23.95), (238.84, 22.39), "Q2.3"], PWR)
    T("INST_5V_A", ["Q2.3", "U13.4"], 0.5)
    T("INST_5V_A", ["J1.2", (255.285, 20.0), (255.585, 20.3), (259.0, 20.3), (263.25, 24.55)], PWR, "B")
    via("INST_5V_A", 263.25, 24.55, "C12.1", PWR)
    T("INST_5V_A", ["U6.14", "C12.1"], PWR)
    # the 3V3 trunk
    # the 3V3 trunk: from a via between IO6's pull-up and the SPI resistors, north-west under
    # the surge diode to a lane under the LED driver, south of the two LED data lines there,
    # and down to R37's via
    via("DEV_3V3", 278.4, 21.5, (278.4, 20.25), FINE)
    T("DEV_3V3", [(278.4, 21.5), (271.6, TRUNK), (256.7, TRUNK), (256.7, 22.2), (256.2, 22.2), (254.4, 24.0)] + step("DEV_3V3"), 0.3, "B")
    via("DEV_3V3", 256.7, 22.2, "R37.2")


def tail():
    """STAGE 3: THE TAIL END'S DIGITAL LINES. J-MCU stands straight up in the middle of the
    board, and nothing passes between its pads, so its odd row can only leave toward the near
    edge. Five of its lines turn toward the tail on top, in lanes hard under the row, each
    straight to its part; six turn toward the mouth on the bottom, in lanes under the same
    row, and north past the header's mouth end to the chain resistors and the lines running
    toward the mouth; pin 5 goes the same way on top. No line goes round the header's far
    end (owner, 2026-11-21). The even row's lines go straight out toward the far side."""
    c = 0.3

    def low(net, n, y, xc, rest, cc=c):
        x = jx(n)
        T(net, [f"J1.{n}", (x, y + c), (x - c, y)] + ([(xc + cc, y), (xc, y + cc)] if cc else [(xc, y)]) + rest, FINE, "B")

    # the odd row's lines toward the tail: five lanes on top hard under the row's pads, each
    # straight from its pin to its part
    T("IO34", ["J1.7", (259.095, 14.95), (259.395, 14.65), (281.9, 14.65), (283.9, 16.65), (284.76, 16.65), "R3.1", "R40.2"], FINE)
    T("IO34", [(276.05, 14.65), "U1.4"])
    T("IO35", ["J1.9", (260.365, 15.35), (260.665, 15.05), (272.18, 15.05), (273.98, 16.85), (278.96, 16.85), "R1.1"], FINE)
    T("IO35", [(277.95, 16.85), "U1.1"])
    T("IO36", ["J1.11", (261.635, 15.75), (261.935, 15.45), (271.1, 15.45), (275.5, 19.85), (281.64, 19.85), "R2.1"], FINE)
    T("IO36", [(276.05, 19.85), "U1.3"], FINE)
    T("DEV_3V3", ["J1.15", (264.175, 16.15), (264.475, 15.85), (270.9, 15.85), (275.3, 20.25), (289.0, 20.25)], FINE)
    T("DEV_3V3", [(276.72, 20.25), "R48.1"], FINE)
    # IO6 turns north past the header's end, between R10 and the first LED's capacitor, to
    # the driver; its pull-up hangs on a branch
    T("IO6", ["J1.21", (267.985, 16.55), (268.285, 16.25), (270.1, 16.25), (270.4, 16.55), (270.4, 29.6), (268.73, 31.27), "U6.5"], FINE)
    T("IO6", [(270.4, 17.0), (270.8, 17.0), (276.41, 22.61), "R48.2"], FINE)
    # the module's SPI, from its resistors to J-UMB: SCLK comes down the tail side of the first LED
    T("SCLK", ["J6.4", (290.07, 29.77), (281.41, 21.11), "R1.2"])
    T("MOSI", ["J6.5", (288.3, 27.23), (283.3, 22.23), "R2.2"])
    T("CS_MOD", ["J6.7", (287.34, 22.15), "R3.2"])
    # the breath pair's last step to J-UMB
    T("BREATH_SENSE", ["J6.1", "R38.2"])
    T("BREATH_SENSE", [(293.25, 37.39), "D5.1"])
    T("AGND_SENSE", ["J6.2", "R39.2"])
    T("AGND_SENSE", [(293.25, 34.85), "D6.1"])
    # MIDI out
    T("MIDI_TIP_DRV", ["U6.6", (265.73, 32.54), (264.93, 33.34), "R50.1"])
    T("MIDI_RING_DRV", ["U6.8", "R51.1"])
    T("MIDI_TIP_R", ["R50.2", "FB3.1"])
    T("MIDI_RING_R", ["R51.2", (261.93, 40.5), (263.38, 41.95), "FB4.1"])
    T("MIDI_TIP", ["FB3.2", (283.75, 39.4), (285.0, 40.65)])
    T("MIDI_TIP", [(282.9, 39.4), (282.9, 40.0)])
    T("MIDI_RING", ["FB4.2", (278.9, 41.95), (279.55, 42.6), (284.4, 42.6)])
    T("MIDI_RING", ["U12.3", (282.64, 42.6)])
    via("PWR_GND", 281.5, 41.0, "U12.2")
    T("PWR_GND", [(280.55, 40.05), (281.5, 41.0), (280.55, 41.95)])
    # the LED driver. Under its body, between the pin rows: its LED output going south to R11,
    # and IO2 coming north from a via to pin 9
    T("GATE_A_OUT", ["U6.3", (265.8, 28.73), (265.5, 28.43), "R11.1"])
    VIAS.append(("IO2", 264.17, 22.3))
    T("IO2", [(264.17, 22.3), (264.17, 31.9), (263.53, 32.54), "U6.9"])
    T("IO2", ["R49.2", "U6.9"])
    via("DEV_3V3", 256.7, 32.54, "R49.1")
    VIAS.append(("IO1", 268.3, 27.46))
    T("IO1", ["U6.2", (268.3, 27.46), (269.1, 26.66), "R10.1"])
    # the even row, bottom face
    T("IO1", ["J1.12", (261.63, 20.79), (268.3, 27.46)], FINE, "B")
    T("IO2", ["J1.16", (264.17, 22.3)], FINE, "B")
    T("U0TXD", ["J1.22", (267.985, 19.8), (268.285, 20.1), (270.5, 20.1), (275.0, 15.6), (287.6, 15.6)], FINE, "B")
    T("U0RXD", ["J1.18", (265.445, 20.2), (265.745, 20.5), (271.3, 20.5), (275.4, 16.4), (288.2, 16.4), (288.8, 15.8), (288.8, 10.45),
                (287.75, 9.4)], FINE, "B")
    via("U0TXD", 287.6, 15.6, "R46.1")
    T("TXD_HDR", ["R46.2", (284.0, 15.01), "J2.1"])
    via("U0RXD", 287.75, 9.4, "J2.2")
    # the odd row, bottom face: under the row, north past the header's mouth end
    # the four lane lines turn once, 45 degrees, from under the row straight into their lanes;
    # IO7 and IO38 end at vias between them and go north on top to their resistors
    def lane_in(net, n, y, xc):
        d = LANE[net] - y
        T(net, [f"J1.{n}", (jx(n), y + c), (jx(n) - c, y), (xc, y), (xc - d, LANE[net])] + step(net), FINE, "B")

    lane_in("IO39", 23, 14.25, 251.0)
    lane_in("IO37", 13, 15.45, 253.6)
    lane_in("IO36", 11, 15.85, 254.0)
    lane_in("IO35", 9, 16.25, 254.4)
    low("IO7", 19, 14.65, 251.9, [(251.0, 15.55)], 0.0)
    low("IO38", 17, 15.05, 252.75, [(252.3, 15.5)], 0.0)
    T("IO33", ["J1.5", (257.825, 16.45), (257.525, 16.15), (254.6, 16.15), (254.3, 16.45), "R36.1"])
    VIAS.append(("IO7", 251.0, 15.55))
    T("IO7", [(251.0, 15.55), (251.0, 20.19), "R35.1"])
    VIAS.append(("IO38", 252.3, 15.5))
    T("IO38", [(252.3, 15.5), (252.3, 21.89), "R34.1"])
    # the chain's three outputs: a via between the pads, then the bottom face toward the mouth
    via("CHAIN_SHLD", 249.2, 25.81, "R35.2")
    via("CHAIN_SCK", 252.2, 25.81, "R34.2")
    T("CHAIN_SER_LH", ["R36.2", (255.2, 25.81), "R37.1"])
    VIAS.append(("CHAIN_SER_LH", 255.2, 25.81))
    # the chain's return to J-MCU pin 24, on top under the three bodies to a via beyond them
    T("CHAIN_QH_RT", ["J1.24", (269.25, 20.8), (268.95, 21.1), (260.1, 21.1), (258.1, 23.1), (258.1, 24.45),
                      (257.65, 24.9), (246.35, 24.9), (245.6, 25.65)])
    VIAS.append(("CHAIN_QH_RT", 245.6, 25.65))


LED_PITCH = 19.7                       # the step toward the mouth from each LED of the even row to the next
# The body CAD's places (lighting.led_tail_x, led_ribbon_x, led_pitch): D8 past the Matrix
# ribbon, D9 before it, the same distance from its edge, and D9 to D20 at one pitch to the
# mouth end
LED_X = {"D8": 282.85, **{f"D{9 + k}": round(243.0 - LED_PITCH * k, 3) for k in range(12)}}
PLACE.update({d: (x, 28.5, None) for d, x in LED_X.items()})


def leds():
    """STAGE 4a: THE LED DATA CHAIN, all of it on top. Each LED's output goes to the next LED's
    data pad and to the backup pad of the one after. The first is a straight line along the
    row of data pads. The second starts at the same data pad, runs under that LED between its
    two columns of pads, comes out on the far side over the unused pad, and drops to the row
    of backup pads. So two lines lie in every gap, one on each row, and none cross."""
    x = LED_X
    nets = [("LED_DI", None, "D8", "D9")] + [(f"LED_D{k}", f"D{7 + k}", f"D{8 + k}", f"D{9 + k}") for k in range(1, 13)]
    # round the first LED, which stands beyond the driver: each of its two lines takes a lane
    # under the driver on the bottom face. The driver's output goes north from R11 to a via,
    # and on along the top to the second LED's backup pad
    T("LED_DI", ["R11.2", (265.5, 21.9), (265.2, 21.6), (260.4, 21.6), (259.3, 22.7), (259.3, 30.65), (259.0, 30.95), (246.3, 30.95), "D9.6"])
    VIAS.append(("LED_DI", 259.3, LANE_DI))
    T("LED_DI", [(259.3, LANE_DI), (280.45, LANE_DI), (283.3, 26.9)], SIG, "B")
    via("LED_DI", 283.3, 26.9, "D8.4")
    via("LED_D1", 278.45, 26.9, "D8.3")
    T("LED_D1", [(278.45, 26.9), (276.3, LANE_D1), (258.0, LANE_D1)], SIG, "B")
    VIAS.append(("LED_D1", 258.0, LANE_D1))
    T("LED_D1", [(258.0, LANE_D1), (255.85, 26.9), "D9.4"])
    for net, a, b, c in nets:
        if a and a != "D8":
            T(net, [f"{a}.3", f"{b}.4"])
        if c not in x or c == "D21" or b == "D8":
            continue
        xb = x[b]
        over = [(xb + 1.6, 26.9), (xb + 1.2, 27.3), (xb + 1.2, 30.15), (xb + 0.4, 30.95)]
        T(net, [f"{b}.4"] + over + [(xb - 3.5, 30.95), (xb - 4.35, 30.1), f"{c}.6"])


def legs():
    """STAGE 4b: THE NEAR ROW'S FOUR KEYS. Each switch's line has the bottom lanes and the LED
    row between it and its resistor. It crosses the lanes on top, takes a via between the
    lanes and the LED row, passes under the LED row on the bottom face, and comes up beside
    its resistor."""
    v = 25.4                                   # the row of vias between the lanes and the LED data pads
    T("/LT1/SWITCH_LEG", ["SW1.1", (54.4, 14.7), (65.1, v)])
    T("/LT1/SWITCH_LEG", [(65.1, v), (70.6, 30.9), (72.75, 30.9)], SIG, "B")
    T("/LT1/SWITCH_LEG", [(72.75, 30.9), (74.0, 30.9), "R13.2"])
    T("/LT3/SWITCH_LEG", ["SW3.1", (94.4, v)])
    T("/LT3/SWITCH_LEG", [(94.4, v), (94.4, 30.9)], SIG, "B")
    T("/LT3/SWITCH_LEG", [(94.4, 30.9), (94.4, 31.49), "R17.2"])
    T("/RT1/SWITCH_LEG", ["SW5.1", (162.4, 20.4), (157.4, v), (153.4, v)])
    T("/RT1/SWITCH_LEG", [(153.4, v), (153.4, 29.4), (151.9, 30.9)], SIG, "B")
    T("/RT1/SWITCH_LEG", [(151.9, 30.9), (150.5, 30.9), "R21.2"])
    T("/RT3/SWITCH_LEG", ["SW7.1", (202.4, 18.3), (209.5, v), (218.0, v)])   # one 45 past the bulk capacitor's corner
    T("/RT3/SWITCH_LEG", [(218.0, v), (218.0, 30.9)], SIG, "B")
    T("/RT3/SWITCH_LEG", [(218.0, 30.9), (218.0, 44.09), "R25.2"])
    for n, pts in (("/LT1/SWITCH_LEG", ((65.1, v), (72.75, 30.9))), ("/LT3/SWITCH_LEG", ((94.4, v), (94.4, 30.9))),
                   ("/RT1/SWITCH_LEG", ((153.4, v), (151.9, 30.9))), ("/RT3/SWITCH_LEG", ((218.0, v), (218.0, 30.9)))):
        for x, y in pts:
            VIAS.append((n, x, y))


# The chain's lines on the bottom face, north of the LED row and south of the registers.
# Toward the tail from the right hand's header they are QH, SER, SH/LD, SCK from the LED row
# outward; between the headers SER, SH/LD, the hop between the hands, SCK.
BAND = {"CHAIN_QH_RT": 31.6, "CHAIN_SER_LH": 32.0, "CHAIN_SHLD": 32.4, "HOP_LT_RH": 33.05, "CHAIN_SCK": 33.7}
SCK_E = 32.8                  # SCK's lane on the tail side of the right hand's header, where the hop is not


def chain():
    """STAGE 4c: THE CHAIN'S TRUNK, bottom face. The three outputs and the return pass under
    the LED row at the tail end, where their vias already stand, and run toward the mouth in
    BAND. At each header a line reaches its pin from the side the pin faces: SCK straight up
    into pin 2; SH/LD and SER round the header's mouth side into pins 4 and 6. The right
    hand's header turns SCK onto the top face; it comes back down beside the register and goes
    on to the left hand's. The hop between the hands leaves the right header's pin 6 and ends
    on a via beside the left header, the one place it changes face."""
    q, e, h, lt, k = (BAND[n] for n in ("CHAIN_QH_RT", "CHAIN_SER_LH", "CHAIN_SHLD", "HOP_LT_RH", "CHAIN_SCK"))
    c = 0.3
    y4, y6 = jpin(4)[1], jpin(6)[1]
    xh, xe = JX - 1.65, JX - 2.05     # SH/LD's and SER's ways up, on the mouth side of the header's pads
    # the return, to a via under the right register's QH pin
    T("CHAIN_QH_RT", [(245.6, 25.65), (245.6, q - c), (245.6 - c, q), (170.9, q), (170.5, q - 0.4)], FINE, "B")
    VIAS.append(("CHAIN_QH_RT", 170.5, q - 0.4))
    T("CHAIN_QH_RT", [(170.5, q - 0.4), (169.06, 32.64), "U8.9"])
    # SER, to the left header's pin 6
    T("CHAIN_SER_LH", [(255.2, 25.81), (254.34, 24.95), (248.2, 24.95), (247.9, 25.25), (247.9, e - c), (247.9 - c, e),
                       (xe + c, e), (xe, e + c), (xe, y6 - c), (xe + c, y6), "J4.6"], FINE, "B")
    # SH/LD, to pin 4 of both
    T("CHAIN_SHLD", [(249.2, 25.81), (249.2, h - c), (249.2 - c, h), (xh + RH, h)], FINE, "B")
    T("CHAIN_SHLD", [(xh + RH, h), (xh + RH, y4 - c), (xh + RH + c, y4), "J5.4"], FINE, "B")
    T("CHAIN_SHLD", [(xh + RH, h), (xh + c, h), (xh, h + c), (xh, y4 - c), (xh + c, y4), "J4.4"], FINE, "B")
    # SCK, to pin 2 of both
    T("CHAIN_SCK", [(252.2, 25.81), (252.2, SCK_E - c), (252.2 - c, SCK_E), (JX + RH + 1.5, SCK_E), (JX + RH, SCK_E + 1.5), "J5.2"], FINE, "B")
    VIAS.append(("CHAIN_SCK", 178.3, 38.32))
    T("CHAIN_SCK", [(178.3, 38.32), (178.3 - (38.32 - k), k), (JX + 1.0, k), (JX, k + 1.0), "J4.2"], FINE, "B")
    # the hop between the hands
    # straight down beside SH/LD past the clamp, then one 45 into its lane
    T("HOP_LT_RH", ["J5.6", (xh + RH, y6), (xh + RH - 0.9, y6 - 0.9), (xh + RH - 0.9, 35.0), (xh + RH - 0.9 - (35.0 - lt), lt), (82.2, lt)], FINE, "B")
    VIAS.append(("HOP_LT_RH", 82.2, lt))
    T("HOP_LT_RH", [(82.2, lt), (81.15, 32.0), (70.9, 32.0), (70.35, 31.45), (55.62, 31.45), "R44.2"])
    T("HOP_LT_QH", ["R44.1", (57.23, 34.9), (59.93, 34.9), "U7.9"])


HOP_Y = 42.65                 # each hop's line from its header's pin 8 toward the mouth, on the bottom face


HOP_TOP = 42.75               # ...and the right hand's on the top face, between the clamp's pad 4 and the bead's pad 2


def hop_out(y8, y=HOP_Y):
    """From pin 8 straight out past its neighbours' pad ends, then one 45 down to y."""
    return [(JX - 1.3, y8), (JX - 1.3 - (y8 - y), y)]


def registers():
    """STAGE 4d: THE TWO REGISTERS, top face but for each hop's line under its register. What
    both hands share is drawn once and placed twice."""
    for dx, u, tvs, j, fb, hop, x1, x2, x3, x4, sw_far, sw_tail, far_mouth, far_tail, near_tail in (
            (0, "U7", "U9", "J4", "FB1", "HOP_LH_LT", "KEY_LT1", "KEY_LT2", "KEY_LT3", "KEY_LT4", "SW2", "SW4",
             ("R15", "C16", "R14"), ("R19", "C18", "R18"), ("R17", "C17", "R16")),
            (RH, "U8", "U11", "J5", "FB2", "HOP_RH_RT", "KEY_RT1", "KEY_RT2", "KEY_RT3", "KEY_RT4", "SW6", "SW8",
             ("R23", "C20", "R22"), ("R27", "C22", "R26"), ("R25", "C21", "R24"))):
        def X(x):
            return x + dx
        lh = dx == 0
        leg2, leg4 = (("/LT2/SWITCH_LEG", "/LT4/SWITCH_LEG") if lh else ("/RT2/SWITCH_LEG", "/RT4/SWITCH_LEG"))
        # SCK: out of pin 2 below the clamp, a stub up to the clamp, in under the register to pin 2
        y2, y4, y6, y8, y10 = (jpin(k)[1] for k in (2, 4, 6, 8, 10))
        # (it passes the clamp 0.4 lower than it enters the register, so the clamp's ground via stands
        # between it and the pad and not in the pad)
        T("CHAIN_SCK", [f"{j}.2", (X(JX - (y2 - 37.5)), 37.5), (X(72.05), 37.5), (X(71.12), 37.5), (X(70.3), 38.32), (X(68.67), 39.95),
                        f"{u}.2"])   # one diagonal into pin 2; x 70.3: where the right hand's via stands
        T("CHAIN_SCK", [(X(72.05), 37.5), f"{tvs}.1"])
        # SH/LD: straight from pin 4 between the clamp's rows into pin 1
        T("CHAIN_SHLD", [f"{j}.4", (X(73.95), y4), (X(69.94), y4), f"{u}.1"])
        T("CHAIN_SHLD", [(X(73.95), y4), f"{tvs}.3"])
        # pins 6 and 10 of the header
        T("CHAIN_SER_LH" if lh else "HOP_LT_RH", [f"{tvs}.4", (X(JX - 0.1325), y6 - 0.1325), f"{j}.6"])
        T("V3V3_CHAIN_LH" if lh else "V3V3_CHAIN_RH", [f"{fb}.2", (X(JX - (y10 - 44.0)), 44.0), f"{j}.10"])
        # the hop into this register: from the header's pin 8 on the bottom face to a via under the body
        # (it leaves the pad straight, then drops to HOP_Y past pad 6's end: 3V3's line lies just north)
        T(hop, [f"{j}.8"] + [(X(x), y) for x, y in hop_out(y8)] + [(X(62.33 + HOP_Y - 38.0), HOP_Y), (X(62.33), 38.0)], FINE, "B")
        VIAS.append((hop, X(62.33), 38.0))
        T(hop, [(X(62.33), 38.0), f"{u}.10"])
        # the far row's two keys: each switch's line south of its ground pin to its resistor
        T(leg2, [f"{sw_far}.1", (X(46.95), 41.85), (X(58.76), 41.85), f"{far_mouth[0]}.2"])
        T(leg4, [f"{sw_tail}.1", (X(86.95), 41.85), (X(94.76), 41.85), f"{far_tail[0]}.2"])
        # each comb's key line: resistor, capacitor, pull-up
        for n, (r, cp, pu) in ((x2, far_mouth), (x4, far_tail), (x3, near_tail)):
            T(n, [f"{r}.1", f"{cp}.1", f"{pu}.2"])
        # the far mouth-side key: down between its resistor and capacitor to pin 5
        T(x2, [(X(64.0), 47.41), (X(64.0), 44.36), (X(64.86), 43.5), f"{u}.5"])
        # the two tail-side keys: along the far band over the header, down beside the register
        T(x4, [f"{far_tail[0]}.1", (X(70.4), 47.41), (X(70.1), 47.11), (X(70.1), 42.7), (X(69.8), 42.4), (X(67.71), 42.4),
               (X(67.41), 42.1), f"{u}.3"])
        T(x3, [f"{near_tail[0]}.1", (X(107.61), 48.3), (X(69.9), 48.3), (X(69.6), 48.0), (X(69.6), 43.2), (X(69.3), 42.9),
               (X(66.44), 42.9), (X(66.14), 42.6), f"{u}.4"])
    # the hop's line reaches the right register's clamp on top
    T("HOP_RH_RT", ["J5.8"] + [(x + RH, y) for x, y in hop_out(jpin(8)[1], HOP_TOP)] + [(CX + RH - 0.95 + HOP_TOP - (jpin(4)[1] + 1.1375), HOP_TOP), "U11.5"])
    # the left hand's near mouth-side key: up past the supply capacitor, under the register to pin 6
    T("KEY_LT1", ["R13.1", "C15.1", "R12.2"])
    T("KEY_LT1", ["R13.1", (74.0, 36.24), (73.2, 37.04), (70.9, 37.04), (70.54, 37.4), (64.39, 37.4), (63.59, 38.2), "U7.6"])
    # the right hand's: round the register's mouth end and under it to pin 6
    T("KEY_RT1", ["R21.1", "C19.1", "R20.2"])
    T("KEY_RT1", ["R20.2", (166.91, 32.91), (168.0, 34.0), (168.0, 38.5), (168.8, 39.3), (171.29, 39.3), (171.59, 39.6), "U8.6"])
    # the left register's two unused inputs
    T("KEY_FREE2", ["R33.2", (60.76, 34.45), (63.14, 34.45), (63.59, 34.9), "U7.11"])
    T("KEY_FREE1", ["R32.2", (64.86, 34.65), "U7.12"])
    # the right register's two spare keys: SW- through the other's comb between its pads
    T("KEY_SWP", ["R29.1", "C23.1", "R28.2"])
    T("KEY_SWM", ["R31.1", "C24.1", "R30.2"])
    T("KEY_SWP", ["R29.1", (175.71, 32.91), (175.41, 33.21), "U8.14"])
    T("KEY_SWM", ["R31.1", (209.59, 32.91), (208.68, 32.0), (174.43, 32.0), (174.13, 32.3), "U8.13"])


def v3():
    """STAGE 4e: 3V3. One lane on the bottom face south of the LED row (tail() and analog()
    draw it); from it a line goes north under the LED row to each via, and each via's parts
    hang from it on top. North of the right hand's header a second lane leaves the trunk at
    the tail end and passes under SW8's pole."""
    lane = lambda x: LANE["DEV_3V3"] if x > STEP_X else MOUTH["DEV_3V3"]   # noqa: E731
    W = 0.3

    def tap(x, y, top):
        T("DEV_3V3", [(x, lane(x)), (x, y)], W, "B")
        VIAS.append(("DEV_3V3", x, y))
        T("DEV_3V3", [(x, y)] + top)
    # the left register: one via under pin 16; the row's parts on a bus along their south side
    T("DEV_3V3", [(64.2, lane(64.2)), (64.2, 32.4), (67.94, 32.4), (69.94, 34.4)], W, "B")
    VIAS.append(("DEV_3V3", 69.94, 34.4))
    T("DEV_3V3", [(69.94, 34.4), "U7.16"])
    T("DEV_3V3", ["U7.16", (70.115, 36.2), "C13.1"])
    T("DEV_3V3", [(69.94, 34.4), (69.94, 32.3), (69.64, 32.0), (58.19, 32.0), (57.69, 32.5), "R33.1"])
    T("DEV_3V3", [(61.59, 32.0), "R32.1"])
    T("DEV_3V3", [(66.14, 32.0), "C206.1"])
    T("DEV_3V3", ["C206.1", "U7.13"])
    # ...and round the hop's via to the far side: the far key's pull-up and the header's bead
    T("DEV_3V3", [(64.2, 32.4), (61.9, 32.4), (61.2, 33.1), (61.2, 42.8), (61.9, 43.5), (68.1, 43.5), (68.5, 43.9), (68.6, 44.0), (70.9, 44.0)], W, "B")
    via("DEV_3V3", 68.5, 43.9, "R14.1")
    via("DEV_3V3", 70.9, 44.0, "FB1.1")
    # the left hand's other pull-ups
    tap(80.2, 30.9, [(80.2, 31.05), "R12.1"])
    tap(89.81, 30.9, ["R18.1"])
    tap(117.4, 30.9, [(117.4, 42.69), "R16.1"])
    # the right hand's
    tap(158.2, 30.9, [(156.5, 30.9), "R20.1"])
    tap(173.18, 30.9, ["C14.1", (173.18, 34.2), (172.87, 34.51), "U8.12"])
    T("DEV_3V3", ["U8.12", (172.87, 37.05), (173.17, 37.35), (177.64, 37.35), (177.94, 37.05), "U8.16"])
    T("DEV_3V3", ["U8.16", (178.115, 36.2), "C205.1"])
    T("DEV_3V3", [(173.5, 37.35), (173.5, 43.4), (175.69, 45.59), "R22.1"], FINE)
    tap(198.0, 30.9, [(196.5, 30.9), "R28.1"])
    T("DEV_3V3", [(213.4, lane(213.4)), (213.4, 29.3), (215.0, 30.9)], W, "B")     # round C28's ground via
    VIAS.append(("DEV_3V3", 215.0, 30.9))
    T("DEV_3V3", [(215.0, 30.9), (216.5, 30.9), "R30.1"])
    # north of the right header
    T("DEV_3V3", [(256.7, TRUNK), (256.7, 34.6), (256.0, 35.3), (191.55, 35.3), (190.85, 36.0), (190.85, 44.6)], W, "B")
    VIAS.append(("DEV_3V3", 190.85, 44.6))
    T("DEV_3V3", [(190.85, 44.6), (190.85, 46.0), (190.55, 46.3), (180.24, 46.3), (179.94, 46.0), "FB2.1"])
    for x, r in ((222.5, "R24.1"), (212.5, "R26.1")):
        T("DEV_3V3", [(x, 35.3), (x, 44.3)], W, "B")
        via("DEV_3V3", x, 44.3, r)


def planes_in():
    """STAGE 5: GROUND AND 12 V INTO THE PLANES. Every surface pad on either net gets a via
    beside it, on the side nothing passes: one via per pad, or one between two pads that
    face each other."""
    G, P12 = "PWR_GND", "INST_POS12"
    x = LED_X
    cap = {"D8": "C26", "D9": "C27", "D10": "C28", "D11": "C29", "D12": "C30", "D13": "C31", "D14": "C32",
           "D15": "C33", "D16": "C34", "D17": "C35", "D18": "C36", "D19": "C37"}
    for d, xb in x.items():
        via(G, xb + 3.6, 28.5, f"{d}.5", PWR)                       # the LED's ground pad, toward the tail
        if d in cap:                                                # its capacitor a step toward the mouth
            T(P12, [f"{cap[d]}.1", f"{d}.2"], PWR)
            if d == "D8":                                           # ...the first LED's beyond the surge diode
                VIAS.append((P12, 278.5, 28.5))
                via(G, 271.45, 26.75, "C26.2", PWR)
            else:
                VIAS.append((P12, xb - 4.0, 28.5))
                via(G, xb - 8.6, 28.5, f"{cap[d]}.2", PWR)
    T(G, ["D8.5", "D8.6"], PWR)
    via(G, 254.25, 28.5, "C45.2", PWR)
    via(P12, 250.0, 28.5, "C45.1", PWR)
    # the mouth-end LED, whose capacitor stands north of it: 12 V passes between its two columns of pads
    T(P12, ["D20.2", (24.1, 28.5), (25.35, 29.75), "C38.1"], PWR)
    via(P12, 25.35, 34.4, "C38.1", PWR)
    via(G, 28.45, 33.0, "C38.2", PWR)
    via(P12, 37.9, 34.0, "C47.1", PWR)
    via(G, 40.95, 32.65, "C47.2", PWR)
    # the key combs' capacitors
    for pad, vx, vy in (("C15.2", 75.5, 30.9), ("C19.2", 155.0, 30.9), ("C23.2", 192.0, 30.9), ("C24.2", 212.0, 30.9),
                        ("C16.2", 65.5, 44.3), ("C18.2", 101.5, 44.3), ("C17.2", 111.5, 44.3),
                        ("C20.2", 172.75, 44.6), ("C22.2", 209.5, 44.3), ("C21.2", 219.5, 44.3)):
        VIAS.append((G, vx, vy))
        py = 31.05 if vy < 40 else 45.55
        px = float({"C15": 77.0, "C19": 153.5, "C23": 193.5, "C24": 213.5}.get(pad[:3], vx))
        T(G, [(vx, vy), (px, vy), pad] if vy < 40 else [(vx, vy), pad] if pad != "C20.2" else [(vx, vy), (173.5, 45.35), pad], PWR)
    # the registers
    via(G, 59.9, 40.97, "U7.8", PWR)
    via(G, 169.06, 42.65, "U8.8", PWR)
    VIAS.append((G, 68.04, 34.5))
    T(G, ["C206.2", (68.04, 34.5)], PWR)
    T(G, ["U7.14", (67.41, 35.13), (68.04, 34.5), (68.67, 35.13), "U7.15"])
    via(G, 71.7, 33.0, "C13.2", PWR)                 # south of it: the key's line passes its tail side
    via(G, 181.1, 34.3, "C205.2", PWR)
    via(G, 73.0, 38.18, "U9.2")            # the clamps' ground vias: just off the pad, between it and SCK
    via(G, 181.0, 38.18, "U11.2")
    VIAS.append((G, 171.59, 34.55))        # on the line from pin 11 to its capacitor: D13 stands where a via south of it would
    T(G, ["U8.11", (171.59, 33.51), "C14.2"])
    via(G, 176.68, 34.4, "U8.15", PWR)
    # the tail end. The LED driver: pins 12 and 13 share a via under the body, the others
    # one each, all clear of the three lanes on the bottom face
    T(G, ["U6.13", "U6.12"])
    via(G, 263.4, 27.46, "U6.13")
    via(G, 263.4, 31.27, "U6.10")
    VIAS.append((G, 268.5, 30.5))
    T(G, ["U6.4", (268.0, 30.0), (268.5, 30.5)])
    via(G, 268.6, 33.81, "U6.7")
    VIAS.append((G, 266.88, 24.5))                                  # between pin 1 and R10's ground end
    T(G, ["U6.1", (266.88, 24.5), (267.49, 23.89), "R10.2"])
    VIAS.append((G, 260.75, 23.2))
    T(G, ["C12.2", (261.3, 22.65), (260.75, 23.2)], PWR)
    via(G, 277.0, 19.2, "U1.2")                                     # U1's ground via: just off the pad, IO36 and 3V3 passing north of it
    via(P12, 272.3, 34.2, "C46.1", PWR)
    via(G, 275.55, 35.6, "C46.2", PWR)
    via(G, 276.35, 24.6, "D3.2", PWR)                               # the clamp's two (#8-6)
    via(G, 274.5, 26.5, "D3.2", PWR)
    via(G, 283.6, 45.0, "J7.3", PWR)
    via(G, 290.4, 12.6, "J2.3", PWR)
    VIAS.append((G, 291.6, 19.61))                                  # in the net tie's own pad: bare copper, no solder
    VIAS.append((G, 290.0, 33.5))
    T(G, ["D6.2", (290.65, 34.15), (290.0, 33.5)])
    via(G, 289.9, 36.36, "D5.2")
    via(G, 296.4, 8.15, "D21.2", PWR)
    via(G, 298.85, 9.45, "R42.2", PWR)


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
    # every soldered ground pin meets its plane through relief spokes, as on the key boards
    # (pcb_hand.relieve); vias stay solid, and so does a mount's pad, which is clamped under
    # a screw and never soldered
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == "PWR_GND":
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    # J-MCU's four ground pins too: a 1.27 mm header leaves room for one spoke where the
    # rules ask two, the same exception the carrier's end of this ribbon takes (ADR 0030)
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            if ref.startswith("H") or (ref == "J1" and pad.GetNetname() == "PWR_GND"):
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    return lay


STAGES = [analog, breath_pair, power, tail, leds, legs, chain, registers, v3, planes_in]


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
        if n.startswith("/") and board.FindNet(n):
            return n                           # a full name, for the nets several sheets share a short one of
        if len(full.get(n, [])) != 1:
            raise SystemExit(f"main_layout: {n} names {len(full.get(n, []))} nets on the board")
        return full[n][0]
    for n, face, w, pts in tracks:
        cu.track(net(n), square(n, pts, pad), w, pcbnew.F_Cu if face == "F" else pcbnew.B_Cu)
    for n, x, y in vias:
        cu.via(net(n), (x, y))
    cu.draw(board)
    # the breath pair's two lines are locked: layout.yaml pairs: guard is checked against them
    for t in board.GetTracks():
        if t.GetLayer() == pcbnew.B_Cu and t.GetNetname() in ("/SENSOR_BUFFERED_OUT", "AGND_INST") and not isinstance(t, pcbnew.PCB_VIA):
            t.SetLocked(True)
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
        if not rect.is_empty:      # the vertical J-MCU fills the Matrix ribbon's area itself: nothing left to keep out
            rects[kname] = rect
    for z in list(board.Zones()):
        if z.GetIsRuleArea() and z.GetZoneName() in spec_all:
            board.Remove(z)
            GONE.append(z)
    for kname, rect in rects.items():
        pcb_main.rule_area(board, rect, kname, ["F.Cu"], footprints=True, copper=False)


def finish(board, lay, comps):
    """The date and the silkscreen, saved and the planes poured: pcb_hand.finish's steps, less
    its ground-pour rules (planes() has set this board's), and two places where the silkscreen
    step leaves legends under the fab's silk clearance of each other."""
    board.GetTitleBlock().SetDate(lay["silk"]["date"])
    pcb.add_silk_generic(board, lay, comps)
    for d in board.GetDrawings():
        # R32's reference stands a hair under the clearance from C36's: a step toward its own part, between the two
        if d.GetClass() == "PCB_TEXT" and d.GetText() == "R32":
            d.Move(pcbnew.VECTOR2I(0, -pcbnew.FromMM(0.07)))
    for g in board.FindFootprintByReference("D2").GraphicalItems():
        # D-TVS's outline runs on past its pad to D6's: both strokes stop level with the pad's end
        if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() == "PCB_SHAPE" and g.GetStart().x == g.GetEnd().x:
            ys = sorted((g.GetStart().y, g.GetEnd().y))
            g.SetStart(pcbnew.VECTOR2I(g.GetStart().x, ys[0] + pcbnew.FromMM(0.3)))
            g.SetEnd(pcbnew.VECTOR2I(g.GetStart().x, ys[1]))
    pcb.silk_off_vias(board)
    pcbnew.SaveBoard(SRC, board)
    pcb_hand.fill(SRC)


def main():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    trial = {"--place-only", "--copper"} & set(sys.argv)
    if trial and not out:
        raise SystemExit("main_layout: --place-only and --copper write a trial to --out <file>; with neither, the board itself is written")
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
    pcb_hand.refit(board, comps, nets)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for cname, ch in geo["chains"].items():
        side = cname.split("-")[-1]
        ref = [r for r, c in comps.items() if c["row"] == "J-CHAIN" and r in fps and fps[r].FindPadByNumber("10").GetNetname().endswith("_" + side)][0]
        pcb_hand.seat_chain(fps[ref], {"chain": ch}, lambda k, dx=(RH if side == "RH" else 0.0): jpin(k, dx))
    # J-MCU where the body CAD stands it (layout.yaml connectors:), as pcb_main.build seats it
    import yaml
    cspec = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))["connectors"]["J-MCU"]
    pcb_main.place_connector(board, fps["J1"], {**cspec, "cad": "J-MCU"}, geo)
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
    if "--place-only" in sys.argv:
        pcbnew.SaveBoard(out, board)
        print(f"main_layout: {len(place)} part(s) seated, no copper; wrote {out}")
        return
    cu = draw_copper(board)
    strip_into_yaml()
    lay = planes(board, geo)
    if out:
        pcbnew.SaveBoard(out, board)
    else:
        finish(board, lay, comps)
    print(f"main_layout: {len(place)} part(s) seated, {cu.segments()} track segment(s), {len(cu.vias)} via(s), all by hand; "
          f"wrote {out or os.path.relpath(SRC, ROOT)}")

if __name__ == "__main__":
    sys.exit(main())
