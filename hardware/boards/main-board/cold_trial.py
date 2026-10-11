"""The main board placed COLD and routed in FAMILIES by the new tools (issue #46): the cluster
packer (tools/pcb_pack.py) seats every part that is not fixed, the centreline router
(tools/pcb_route2.py, Router.stage) routes one family of nets at a time, each reviewed -
its detours routed again, the liquid pass over it - and locked before the next is let near
it. It READS main-board.kicad_pcb and WRITES main-board.cold.kicad_pcb beside it (and one
checkpoint per family, main-board.cold.<k>-<family>.kicad_pcb, in --out): a trial, not the
source.

    python3 hardware/boards/main-board/cold_trial.py [--place-only] [--force] [--out DIR] [--plot DIR]

After placement each net's airwires are compared with the source's; a net more than three
times as long and 20 mm longer stops the run before routing (--force routes anyway).

FIXED (the owner, 2026-10-10: "Body CAD + analog block"): every part the body CAD places
(the switches, the mounts, the connectors, U-BREATH, the LED row and each LED's cap by
its rule, U-BUCK and the one part the regulator block lets in beside it), J-UMB's three
protection parts, whose places a rule sets at its pins (#8-9, ADR 0018), and the analog
block - every part on the AGND_INST island, its tie, and the breath pair's far ends with
their clamps, which the pair's locked copper reaches. Everything else starts unplaced and
is seated by pcb_pack's cold planner: one key network stamped at every switch, then each
IC round the placed part it shares most nets with, then the passives round theirs - under
the body CAD's height rooms, the iron room and the island rule, with the LEDs' cone a
cost (a tall bulk part goes where it rises least into it).

COPPER: every unlocked track and via goes; a locked one stays only if every pad its copper
reaches is a fixed part's (the pair and its guards, the analog block's hand routes, the
fixed parts' plane vias). The zones stay, emptied for a refill.

FAMILIES (the pcb-routing skill's order): power and rails, the analog block's own nets,
the key chain, the keys, the SPI and the Matrix's lines, MIDI, then the rest. The plane
fanout comes first, as it always does.
"""
import glob
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pcbnew       # noqa: E402
import yaml         # noqa: E402
from shapely.geometry import LineString, Point, Polygon, box   # noqa: E402
from shapely.ops import unary_union                             # noqa: E402
from shapely.strtree import STRtree                            # noqa: E402
import pcb          # noqa: E402
import pcb_main     # noqa: E402
import pcb_pack     # noqa: E402
import pcb_route2   # noqa: E402

SRC = os.path.join(HERE, "main-board.kicad_pcb")
OUT = os.path.join(HERE, "main-board.cold.kicad_pcb")

# the families, in order, each with why it is there (the pcb-routing skill, "The order")
FAMILIES = [
    # power and rails: the layer-limited power classes cannot hop a signal via, so they go
    # before anything can wall them in (layout.yaml route_first: says the same)
    {"name": "power", "nets": ["INST_5V_A", "BUCK_IN", "/power-entry-instrument/BUCK_A_OUT", "UMBILICAL_POS12", "DEV_3V3",
                               "/V3V3_CHAIN_*"]},
    # the analog block's own nets, over their island (the pair is already laid and locked)
    {"name": "analog", "nets": ["/SENSOR_RAW", "/breath-adc/*", "/breath-excitation-reference/*", "REF_VIN", "VS",
                                "BREATH_SENSE", "AGND_SENSE", "*BREATH*"]},
    # the key chain: SCK, SH/LD and the hops run the board's length together. The clock leads
    # and SH/LD beside it - laid last (shortest first), SCK found the corridor taken (run 3)
    {"name": "chain", "nets": ["/CHAIN_*", "/HOP_*"], "first": ["/CHAIN_SCK", "/CHAIN_SHLD", "/CHAIN_SER_LH"]},
    # each key's T into its register
    {"name": "keys", "nets": ["/KEY_*", "*/SWITCH_LEG"]},
    # the Matrix's lines from J-MCU: SPI, the LED data, the service UART
    # J-MCU's top row and U1 by place, before the rest of the mcu lines (the owner,
    # 2026-10-11: "breaking up families geographically"). Routed as one family the crowd
    # walled in one of its own each time: IO2 looped round U1 pin 3 (IO36), and with IO36
    # leading, J1.4 (IO1) - each a pad-to-pad hop of a few mm that a long line crossed first
    # The box reaches north over U6 too (review of family 6, 2026-10-11): at 124 it took the
    # long lines with a pad at J-MCU (IO2, IO39, IO35) ahead of U6's own hops, which were
    # then walled in on both layers - GATE_A_OUT, IO6 and LED_D1 open. U6 shares IO1 and
    # IO2 with J-MCU: one crowd, not two
    {"name": "mcu-fanin", "nets": ["/IO*", "*TXD*", "*RXD*", "/led-strip-drive/*"], "near": [300.0, 108.0, 334.0, 138.0],
     "first": ["/IO36", "/IO1"]},
    {"name": "mcu", "nets": ["/IO*", "/SPI*", "*TXD*", "*RXD*", "/led-strip-drive/*", "/LED_*"]},
    {"name": "midi", "nets": ["*MIDI*"]},
]


# WHAT A REVIEW ACCEPTED, by family: a review reason (or its start) that asks for no second
# look, each with why. Reported in the family's record, not paused for.
ACCEPT = {
    # 2026-10-10: J5 pin 10 can only leave its 1.27 mm header round the end; 9.6 mm for a
    # 3.4 mm airwire is the way round (the source's run was 23.5 mm)
    "power": ["still long: /V3V3_CHAIN_RH",
              # 2026-10-11: 39.4 mm (the source's 28.5; this placement's buck corner has given
              # 35-54 in every run) - C207 and C43 at U13 and U5, the rail between them
              "still long: /power-entry-instrument/BUCK_A_OUT"],
    "chain": [
        # 2026-10-11 (ae771009): CHAIN_SCK's first route and its rescue (683 s) failed; the
        # push routed it shoving nothing - a re-route from clean. Routed whole; the family is
        # complete. Why the first attempt failed is the router's to answer, not this board's
        "pushed in: /CHAIN_SCK",
    ],
    "mcu": [
        # 2026-10-11 (3dfb6b8f): 87.9 mm and 12 vias for a 35.1 mm airwire, D10 - D11 - D12.
        # The way along y 123 crosses DEV_3V3's front line at x 270 and the keys and chain
        # families' locked copper round D11-D12, the board's densest place. A WS2815 data
        # line at 800 kHz: length and vias cost it nothing electrically. The cure is the
        # placement - the drivers' chain in one row, clear of the key lines - not this family
        "still long: /led-strip-drive/LED_D3",
    ],
    "keys": [
        # 2026-10-11: 9.1 mm for a 4.5 mm airwire - U7's pin rows' room puts R33 that far off;
        # the source's run was 10.5 mm
        "still long: /KEY_FREE2",
        # 2026-10-11: 20.3 mm, 2 vias, for 8.9 mm: H3's bearing keep-out stands between SW4
        # and R19, and the chain's CHAIN_SER_LH hugs its top edge, 0.5 mm off - no lane over
        # it. A chain-family `clear` would open one (12 mm, 2 vias on this line); left for the
        # whole board's review, with the keys' total (446 mm / 44 vias vs the source's 366 / 22)
        "still long: /LT4/SWITCH_LEG",
        # 2026-10-11 (a89e362b placement): 47.5 mm / 6 vias for a 24.5 mm airwire (the source's
        # 38.8 / 2) - U8 pin 3 up to RT4's network crosses the chain's corridor between the
        # switches and the registers, as every key line does; the family's via count is the
        # whole board's review's, not this line's
        "still long: /KEY_RT4",
    ],
}


# KiCad's findings a placement may not have (pcb_route2.drc on the placed board, before a fill)
PLACE_FINDINGS = ("courtyards_overlap", "items_not_allowed", "shorting_items", "clearance", "hole_clearance",
                  "solder_mask_bridge", "tracks_crossing")


# THE REVIEWER'S MOVES, by family, each with why (Router.edit: reroute / through / clear).
# The record of every review of this trial; replayed by every run from that family on.
EDITS = {
    "mcu-fanin": [
        # Review of family 5 (mcu-fanin), 2026-10-11 (3dfb6b8f): IO35 open at J1.10. IO1 left
        # J1.4, the westmost of these pins, up and EAST on F.Cu to R10 across pins 6, 8 and 10;
        # IO7 and IO38, both bound west, were forced east between diagonals and doubled back,
        # over pin 10's way out. A first try clearing IO38 alone failed: "still in the
        # rectangle" - IO1 had closed the west. J-MCU is THT: IO1 can take the back at its pad
        {"clear": "/IO1", "rect": [317.2, 128.8, 323.0, 136.8],
         "why": "IO1 bound east across the row's westbound exits"},
        {"clear": "/IO7", "rect": [318.4, 128.8, 325.0, 136.8],
         "why": "IO7's detour east over J1.10; R35 is west"},
        {"clear": "/IO38", "rect": [319.7, 128.8, 325.0, 136.8],
         "why": "IO38's detour east over J1.10; R34 is west"},
        {"reroute": "/IO35", "why": "J1.10, free once IO38 is out"},
    ],
    "chain": [
        # Review of family 5 (mcu), 2026-10-11 (3dfb6b8f): IO1 and IO36 open - J-MCU pins 4 and
        # 12, and U1 pin 3, walled in above J-MCU's top row (y 131-138). The mcu family's own
        # lines there its rescue could move; what it could not was CHAIN_QH_RT, run across the
        # whole area on B.Cu (and round U1 on F.Cu), so nothing could drop to the back to pass
        # under them. Kept out of that area but where it reaches its own pin.
        {"clear": "/CHAIN_QH_RT", "rect": [308.0, 128.0, 326.0, 138.2],
         "why": "leave the back under J-MCU's top row to the Matrix's lines"},
    ],
    "power": [
        # Review of family 1, 2026-10-10: U13 (U-USBOR) pin 3 left open, "budget". INST_5V_A
        # leaves pin 4 over the part's top and down its right side, and pin 2's locked plane
        # via stands in the one lane left on the front: pin 3 is boxed in, and the back, at the
        # power class's layer cost, is a search that runs out. Pins 3 and 6 are EN and ANODE,
        # tied (power-entry-instrument.md, the 5 V OR; [ds TI-LM74700-Q1.pdf]): the load
        # current runs in Q-USBOR, not here - this link carries the controller's bias only. So
        # it is joined under the part's body, between its rows of pads (0.94 mm apart: the
        # rail's 0.5 mm does not fit), at signal width.
        # No points: at signal width the way under the body is the shortest, and points in
        # board millimetres go stale the moment a placement moves the part (it moved 0.25 mm
        # when the packer learned to keep off kept copper)
        {"connect": ["U13.3", "U13.6"], "track": 0.25,
         "why": "EN tied to ANODE under U13's body; no load current in it"},
        # Review of family 2 (analog), 2026-10-10: DEV_3V3 rose from R45 to R47's top pad
        # BETWEEN R47 and C2 - the digital rail through the ADC supply filter, between its
        # output (R47.2, ADC_VDD) and its capacitor (C2) - and ADC_VDD hooked round it. The
        # rail goes round R47's west end instead; ADC_VDD then runs straight along its bus
        # (layout.yaml parts: R47 "into the ADC_VDD bus", C2/C42/C3 on it).
        {"clear": "DEV_3V3", "rect": [91.5, 124.9, 93.1, 126.3],
         "why": "keep the digital 3V3 out from between R-ADC-VDD and C-ADC-BULK"},
    ],
}


def comps_of():
    comps, _ = pcb.sheet_netlist(os.path.join(HERE, "main-board.kicad_sch"))
    return comps


def to_pcb_poly(pts):
    return Polygon([pcb.to_pcb(x, y) for x, y in pts])


def fixed_parts(board, lay, comps):
    """The parts that stay where the source has them, each with why."""
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    why = {}
    rows = {r: comps.get(r, {}).get("row", r) for r in fps}
    for r in fps:
        if r.startswith(("SW", "H")):
            why[r] = "body CAD (switch / mount)"
    for r in ("J1", "J2", "J4", "J5", "J6", "J7"):
        why[r] = "body CAD (connector)"
    for r in fps:
        if rows[r] in ("D-LED", lay["led_caps"]["row"]):
            why[r] = "body CAD (LED row and each LED's cap by its rule, ADR 0028)"
        if rows[r] in [v["row"] for v in (lay.get("cad_parts") or {}).values()]:
            why[r] = "body CAD (cad_parts:)"
    for k in (lay.get("keepouts") or {}).values():
        for row in k.get("except_rows") or []:
            for r in fps:
                if rows[r] == row and r not in why:
                    why[r] = "the regulator block's own (keepouts: except_rows)"
    # the power entry's protection, placed by a rule at J-UMB's pins, not by taste: the
    # packer seats ICs first and J-UMB's side fills, which put them 16-30 mm off the pins
    for r, rule in (("D3", "D-TVS-PWR at J-UMB pins 3 and 6 (#8-9)"), ("D2", "D-REVSHUNT across J-UMB pins 3 and 6"),
                    ("NT1", "NT-DIG at J-UMB pin 8 (ADR 0018)")):
        why[r] = f"J-UMB's protection: {rule}"
    # the analog block: every part whose courtyard is on the In1 island, and its tie
    isl = next(i for i in lay["islands"] if i.get("layer") == "In1.Cu")
    ip = to_pcb_poly(isl["outline"]).buffer(0.3)
    for r, f in fps.items():
        cy = pcb_pack.courtyard_of(f, pcbnew)
        if r not in why and cy.intersection(ip).area > 0.5 * cy.area:
            why[r] = "analog block (on the AGND_INST island)"
    why[isl["tie"]] = "analog block (the island's tie)"
    # the breath pair's far ends, and the clamps on the nets past them
    for pr in lay.get("pairs") or []:
        for end in pr["to"]:
            ref = end.split(".")[0]
            why[ref] = "analog block (the breath pair's end)"
            other = {p.GetNetname() for p in fps[ref].Pads()} - set(pr["nets"])
            for r, f in fps.items():
                if r not in why and not r.startswith("J") and other & {p.GetNetname() for p in f.Pads()}:
                    why[r] = "analog block (a clamp on the breath pair's far side)"
    return why


def strip(board, fixed):
    """Every unlocked track and via goes; locked copper goes unless every pad it reaches
    belongs to a fixed part. Connectivity is per net and per layer, a via joining all."""
    tracks = list(board.GetTracks())
    gone = [t for t in tracks if not t.IsLocked()]
    locked = [t for t in tracks if t.IsLocked()]
    L = lambda v: pcbnew.ToMM(v)

    def shape(t):
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            return Point(L(c.x), L(c.y)).buffer(L(t.GetWidth(pcbnew.F_Cu)) / 2), None
        a, b = t.GetStart(), t.GetEnd()
        return LineString([(L(a.x), L(a.y)), (L(b.x), L(b.y))]).buffer(L(t.GetWidth()) / 2), t.GetLayer()
    items = [(t, *shape(t)) for t in locked]
    pads = []
    for f in board.GetFootprints():
        for p in f.Pads():
            for lid in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(lid) and p.GetNetname():
                    pads.append((f.GetReference(), p.GetNetname(), lid, pcb_route2._poly_of(p.GetEffectivePolygon(lid))))
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    tree = STRtree([g for _, g, _ in items])
    for i, (t, g, lay_) in enumerate(items):
        for j in tree.query(g):
            j = int(j)
            if j <= i:
                continue
            u, gu, lu = items[j]
            if u.GetNetname() != t.GetNetname() or not g.intersects(gu):
                continue
            if lay_ is None or lu is None or lay_ == lu:
                parent[find(i)] = find(j)
    bad = set()
    for ref, net, lid, pg in pads:
        if ref in fixed:
            continue
        for j in tree.query(pg):
            t, g, lay_ = items[int(j)]
            if t.GetNetname() == net and (lay_ is None or lay_ == lid) and g.intersects(pg):
                bad.add(find(int(j)))
    lost = [t for i, (t, _, _) in enumerate(items) if find(i) in bad]
    gone += lost
    for t in gone:
        board.Delete(t)
    for z in board.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    return len(gone), len(locked) - len(lost)


def key_roles(board):
    """Each switch's network in role order - series R (its SWITCH_LEG), pull-up R, C - read
    off the nets (as the left key board's trial does)."""
    nets = {f.GetReference(): {p.GetNetname() for p in f.Pads()} for f in board.GetFootprints()}
    roles = {}
    for sw in sorted(r for r in nets if r.startswith("SW")):
        leg = next(n for n in nets[sw] if n.endswith("SWITCH_LEG"))
        series = next(r for r, ns in nets.items() if r != sw and leg in ns)
        key = next(n for n in nets[series] if n != leg)
        pull = next(r for r, ns in nets.items() if r.startswith("R") and key in ns and r != series)
        cap = next(r for r, ns in nets.items() if r.startswith("C") and key in ns)
        roles[sw] = [series, pull, cap]
    return roles


def drivers(board, comps, rails):
    """Each series termination (a row R-*-SER) round its DRIVING end, as the board places them
    (layout.yaml parts: "the SPI and chain series resistors at their driving end", R-HOP-SER
    "at U7's QH"): J-MCU, the Matrix's connector, where it is on the part's nets; else the IC
    on them with the most pins (U7, not the TVS U11 beside J5). The nets alone cannot say which end drives - both ends give one airwire length."""
    nets = {f.GetReference(): {p.GetNetname() for p in f.Pads()} - set(rails) - {""} for f in board.GetFootprints()}
    mcu = next((r for r in nets if comps.get(r, {}).get("row") == "J-MCU"), None)
    out = {}
    for r, ns in nets.items():
        if not re.match(r"^R-.*-SER$", comps.get(r, {}).get("row", "")):
            continue
        ends = [q for q in nets if q != r and ns & nets[q]]
        ics = sorted((q for q in ends if q.startswith("U")), key=lambda q: (-len(list(board.FindFootprintByReference(q).Pads())), q))
        d = mcu if mcu in ends else (ics[0] if ics else None)       # the IC with the most pins: not a clamp
        if d:
            out[r] = d
    return out


ESCAPE_DEPTH = 1.2            # mm: Router.reserve_escapes' bands, and the packer's room for them


def escape_rows(bd, depth, min_pins=8, pitch_max=1.3):
    """{ref: ("pins", depth)} for each fine-pitch part (as Router.reserve_escapes picks them):
    the packer keeps parts out of a band `depth` deep along each side its pins leave by,
    read from the part as it stands once it is seated (Packer.escape_bands)."""
    out = {}
    for r, p in bd.parts.items():
        # surface-mount parts only, as the router's bands (Router.reserve_escapes smd_only)
        if p.item is not None and any(q.GetAttribute() != pcbnew.PAD_ATTRIB_SMD for q in p.item.Pads()):
            continue
        geo = [g for n, f, g in p.padgeo if f == p.side and n and not n.startswith("unconnected")]
        allp = [g for n, f, g in p.padgeo if f == p.side]          # a through-hole pin is on its face too
        if len(allp) < min_pins or not geo:
            continue
        cs = [g.centroid for g in allp]
        gaps = sorted(math.dist((a.x, a.y), (b.x, b.y)) for a in cs for b in cs if a is not b)
        if not gaps or gaps[0] > pitch_max:
            continue
        out[r] = ("pins", depth)        # its sides read as it stands when the band is drawn
    return out


def place(board, lay, comps, fixed, log):
    geo = pcb_main.geometry()
    rails = [p["net"] for p in lay["planes"]] + [i["net"] for i in lay["islands"]] + ["DEV_3V3"]
    bd = pcb_pack.board_of(board, rails=rails)
    # the island rule on the In1 island only (the In2 strip is a return path, not a place)
    isl = next(i for i in lay["islands"] if i.get("layer") == "In1.Cu")
    bd.islands = {isl["net"]: to_pcb_poly(isl["outline"])}
    # the body CAD's height rooms (pcb_main.check_heights reads the same keep-outs)
    k = geo["keepouts"]
    rooms = []
    for name, v in k.items():
        if name != "elsewhere" and v[4] > 0:
            (x0, y0), (x1, y1) = pcb.to_pcb(v[0], v[1]), pcb.to_pcb(v[2], v[3])
            rooms.append((box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), v[4], name))
    bd.rooms, bd.room_default = rooms, k["elsewhere"][4]
    heights = lay.get("heights") or {}
    for r, p in bd.parts.items():
        name = p.item.GetFPID().GetLibItemName().wx_str()
        p.height = next((v for key, v in heights.items() if key in name), None)
    # the LEDs' cone as a cost (pcb_main.check_heights reports the same depth as a note;
    # the owner, 2026-10-03: tall parts "still away from leds"): 40 mm of airwire per mm into it
    lb = yaml.safe_load(open(os.path.join(ROOT, "config", "body.yaml")))
    t = math.tan(math.radians(float(lb["lighting"]["led_view_angle"]["value"]) / 2))
    leds = []
    for (x, y, r_, a, c, lh) in geo["leds"].values():
        (x0, y0), (x1, y1) = pcb.to_pcb(x - a / 2, y - c / 2), pcb.to_pcb(x + a / 2, y + c / 2)
        leds.append(box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
    bd.power = {n for c in (lay.get("net_classes") or {}).values() if c.get("via") for n in c.get("nets") or []}
    bd.cone = (unary_union(leds), max(v[5] for v in geo["leds"].values()), t, 40.0)
    # the iron room round the hand-soldered pads
    rowref = {}
    for r in bd.parts:
        rowref.setdefault(comps.get(r, {}).get("row", r), []).append(r)
    for rule in (lay.get("iron_room") or {}).get("rules") or []:
        for row in rule["rows"]:
            for r in rowref.get(row, []):
                cop = bd.parts[r].copper.get("F")
                if cop is not None:
                    bd.iron.append((r, "F", cop.buffer(0.25), rule["min"]))
    bd.unplaced = {r for r in bd.parts if r not in fixed}
    body = sorted(fixed)
    # every fine-pitch part's pin rows keep a band clear of parts as deep as the router's
    # escape bands (Router.reserve_escapes) and a margin: a pull-up seated against U7's pin
    # ends left its own line no way past the neighbouring pins' bands to U7 pin 11 (R33)
    pk = pcb_pack.Packer(bd, body, log, escape=escape_rows(bd, ESCAPE_DEPTH + 0.4))
    roles = key_roles(board)
    sheets = {r: comps.get(r, {}).get("sheet", "") for r in bd.parts}
    rep = pk.cold(sheets, patterns=[(list(roles), roles)], prefer=drivers(board, comps, rails))
    pk.apply(board)
    return rep, sorted(bd.unplaced), pk


def airwires(board, skip):
    """Each net's airwire length: the minimum spanning tree over its pads' centres."""
    pads = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            if n and n not in skip and not n.startswith("unconnected"):
                c = p.GetPosition()
                pads.setdefault(n, []).append((pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)))
    out = {}
    for n, pts in pads.items():
        seen, total = {0}, 0.0
        best = {j: math.dist(pts[0], pts[j]) for j in range(1, len(pts))}
        while best:
            j = min(best, key=best.get)
            total += best.pop(j)
            seen.add(j)
            for k in best:
                best[k] = min(best[k], math.dist(pts[j], pts[k]))
        out[n] = total
    return out


def placement_regressions(src, board, lay, ratio=3.0, over=20.0):
    """Nets whose airwires the cold placement made much longer than the source's: more than
    `ratio` times AND `over` mm longer. Planes and islands are skipped - their pads meet a
    plane, not each other. A regression found here is a placement fault, and routing over it
    only hides it (the power family of 2026-10-10: a 1 mm Miller leg routed as 76 mm)."""
    skip = {p["net"] for p in lay["planes"]} | {i["net"] for i in lay["islands"]} | {"DEV_3V3"}
    a, b = airwires(src, skip), airwires(board, skip)
    # a PATH through a two-pad part between two signal nets (a series R, a bead) is measured
    # as one: which end the part sits at moves length from one net to the other, not more
    parent = {n: n for n in a}

    def find(n):
        while parent[n] != n:
            n = parent[n]
        return n
    for f in src.GetFootprints():
        ns = [p.GetNetname() for p in f.Pads()]
        if len(ns) == 2 and all(n in parent for n in ns) and ns[0] != ns[1]:
            parent[find(ns[0])] = find(ns[1])
    ga, gb = {}, {}
    for n in a:
        if n in b:
            g = find(n)
            ga[g] = ga.get(g, 0.0) + a[n]
            gb[g] = gb.get(g, 0.0) + b[n]
    names = {}
    for n in a:
        names.setdefault(find(n), []).append(n)
    rows = sorted(((gb[g] / max(ga[g], 1.0), " + ".join(sorted(names[g])), ga[g], gb[g]) for g in ga), reverse=True)
    return [r for r in rows if r[0] > ratio and r[3] - r[2] > over], rows


def silk(board, lay, comps):
    gone = [d for d in board.GetDrawings() if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
    for d in gone:
        board.Delete(d)
    pcb.add_silk_generic(board, lay, comps)
    return len(gone)


def measure(path):
    b = pcbnew.LoadBoard(path)
    tr = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    errs, unc = pcb_route2.drc(path)
    return {"length_mm": round(sum(pcbnew.ToMM(t.GetLength()) for t in tr), 1),
            "vias": sum(1 for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)),
            "drc_errors": len(errs), "unconnected": unc}


def place_board(lay, comps):
    """The source board stripped and placed cold, gated on its airwires. Returns the board."""
    board = pcbnew.LoadBoard(SRC)
    fixed = fixed_parts(board, lay, comps)
    n, kept = strip(board, fixed)
    print(f"cold: {len(fixed)} part(s) fixed, {len(board.GetFootprints()) - len(fixed)} to place; "
          f"{n} track(s) and via(s) stripped, {kept} locked kept")
    for r in sorted(fixed):
        print(f"cold:   fixed {r}: {fixed[r]}")
    log = []
    rep, left, pk = place(board, lay, comps, fixed, log)
    for what, refs, res in rep:
        print(f"cold: place {what}: {', '.join(refs)} - {res}")
    for line in log:
        print("cold: " + line)
    if left:
        raise SystemExit(f"cold: still unplaced: {left}")
    print(f"cold: silkscreen made again ({silk(board, lay, comps)} old drawing(s) cleared)")
    bad, rows = placement_regressions(pcbnew.LoadBoard(SRC), board, lay)
    for x, n, a, b in rows[:12]:
        print(f"cold: airwire {n}: source {a:.1f} mm, cold {b:.1f} mm (x{x:.1f})")
    tot_a, tot_b = sum(r[2] for r in rows), sum(r[3] for r in rows)
    print(f"cold: airwires in all: source {tot_a:.0f} mm, cold {tot_b:.0f} mm")
    if bad and "--force" not in sys.argv:
        raise SystemExit("cold: placement regressions (x3 and +20 mm over the source) - fix the placement, or "
                         "--force: " + ", ".join(n for _, n, _, _ in bad))
    return board


def finish(board, lay, rep):
    """After the last family: tidy, the plane orphan pass, the numbers against the source."""
    import pcb_route
    failed = {n_: v for x in rep for n_, v in x["failed"].items()}
    pcbnew.SaveBoard(OUT, board)
    board = pcbnew.LoadBoard(OUT)
    pcb_route.tidy(board, lay)
    pcbnew.SaveBoard(OUT, board)
    code = (f"import sys, json, yaml; sys.path.insert(0, {os.path.join(ROOT, 'tools')!r}); import pcb_route2; "
            f"print('ORPH ' + json.dumps(pcb_route2.fix_plane_orphans({OUT!r}, yaml.safe_load(open({os.path.join(HERE, 'layout.yaml')!r})))))")
    t = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    orph = [json.loads(line[5:]) for line in t.stdout.splitlines() if line.startswith("ORPH ")]
    if not orph:
        raise SystemExit(f"cold: the plane orphan pass failed:\n{t.stderr[-2000:]}")
    print(f"cold: plane fragments fanned out again: {orph[0][0]}; still apart: {orph[0][1] or 'none'}")
    print(f"cold: wrote {os.path.relpath(OUT, ROOT)}; failed {failed or 'none'}")
    print(f"cold: source {measure(SRC)}")
    print(f"cold: trial  {measure(OUT)}")
    return 1 if failed else 0


def main():
    """--start K: go on from the checkpoint of family K-1 in --out (K=1: the placement saved
    there as checkpoint 0, or placed from the source with --place or when there is none).
    --stop K: stop after family K. --pause: stop after the first family that asks for review.
    The reviewer's moves are EDITS, above, each with why."""
    arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    out = os.path.abspath(arg("--out", HERE))
    plotdir = arg("--plot")
    start = int(arg("--start", 1))
    stop = int(arg("--stop")) if arg("--stop") else None
    os.makedirs(out, exist_ok=True)
    lay = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))

    def checkpoint(k, name):
        return os.path.join(out, f"main-board.cold.{k}-{name}.kicad_pcb")
    if start == 1 and os.path.exists(checkpoint(0, "placed")) and "--place" not in sys.argv:
        board = pcbnew.LoadBoard(checkpoint(0, "placed"))
        print(f"cold: the placement of {checkpoint(0, 'placed')} (--place to place again)")
    elif start == 1:
        board = place_board(lay, comps_of())
        # the placement's own gate, by KiCad: a part on a part, on a keep-out, or on the copper
        # kept from the source (a pad on a hand route was six shorts the courtyard findings
        # alone did not show - the 2026-10-10 run's U8)
        cp0 = checkpoint(0, "placed")
        pcbnew.SaveBoard(cp0, board)
        errs, _ = pcb_route2.drc(cp0, fill=False)
        pe = [e[:3] for e in errs if e[0] in PLACE_FINDINGS]
        print(f"cold: KiCad placement findings: {pe or 'none'}")
        if "--place-only" in sys.argv:
            pcbnew.SaveBoard(OUT, board)
            print(f"cold: placed only - wrote {os.path.relpath(OUT, ROOT)}")
            return 1 if pe else 0
        if pe and "--force" not in sys.argv:
            os.remove(cp0)
            raise SystemExit("cold: the placement has KiCad findings - fix the placement, or --force")
    else:
        prev = sorted(glob.glob(os.path.join(out, f"main-board.cold.{start - 1}-*.kicad_pcb")))
        if not prev:
            raise SystemExit(f"cold: no checkpoint of family {start - 1} in {out}")
        board = pcbnew.LoadBoard(prev[0])
        print(f"cold: going on from {prev[0]}")
    m = pcb_route2.model_from_board(board, lay)
    r = pcb_route2.Router(m, flow=0.3, budget=3_000_000)

    def plot(k, name, nets, path):
        if not plotdir:
            return None
        import pcb_plot
        png = os.path.join(plotdir, f"cold-{k}-{name}.png")
        pcb_plot.plot(path, png, nets=nets, title=f"main board cold: family {k} {name}")
        return png
    rep = r.stage(FAMILIES, board=board, checkpoint=checkpoint, first=lay.get("route_first") or [], plot=plot,
                  start=start, stop=stop, pause="--pause" in sys.argv, edits=EDITS, accept=ACCEPT,
                  # every fine-pitch pin's escape band kept for its own net (Router.reserve_escapes):
                  # without them power and the chain walled in U8's pins 14 and 6 before the keys
                  escape={"depth": ESCAPE_DEPTH})
    for line in r.log:
        if not line.startswith(("route:", "rescue ")):
            print("cold: route " + line)
    for x in rep:
        print("cold: family " + json.dumps({k_: v for k_, v in x.items() if k_ not in ("checkpoint",)}, default=str))
    last = len(FAMILIES) + 1                   # the families and "rest"
    done = rep and not rep[-1].get("paused") and (stop is None or stop >= last)
    if not done:
        print(f"cold: stopped after family {start + len(rep) - 1} - review its plot, then --start {start + len(rep)}")
        return 0
    return finish(board, lay, rep)


if __name__ == "__main__":
    sys.exit(main())
