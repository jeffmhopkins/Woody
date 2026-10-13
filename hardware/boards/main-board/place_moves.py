#!/usr/bin/env python3
"""Placement moves on a placed main board, each with why: the loop the owner set, 2026-10-13
(ADR 0029 as amended) - route with Freerouting (fr_trial.py), read the scorecard, move the
parts in a family's way, route again.

    python3 hardware/boards/main-board/place_moves.py <placed.kicad_pcb> <out.kicad_pcb>

Each move seats parts round an anchor part with the cold trial's packer (pcb_pack.Packer.pack:
the full rule list, and the same escape bands - J-MCU's 3.5 mm in front of its rows), so a move
is legal or it is not made. A move is a fact about the design, cited, not a nudge.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "tools"))

# (anchor, parts, why[, sides to try, in order[, rotations to try]])
MOVES = [
    # R-CHAIN-SER is "series at the driving end on SCK, SH/LD and the chain-end SER"
    # (hardware/carrier/carrier.md). The cold placement left all three in one cluster at
    # x 302-307, at neither end: the Freerouting trial of 2026-10-13 crossed IO33 and CHAIN_SHLD
    # there (all ten of its DRC errors) and ran IO33 2.1 times its airwire.
    # R34 and R35 (SCK, SH/LD) belong at J-MCU by the same rule, but it has no legal seat for
    # them nearer than where they stand: tried 2026-10-13, the packer's only row was at x 293,
    # 24 mm from J1.6 and J1.8 - further than the cold placement's. They stay; J-MCU's crowd
    # (U1, U6 and their parts) is the next placement question
    ("U9", ["R36"], "SER is driven from the chain's end, U9 (the LH chain's last register): its series resistor there"),
    # U-TVS-SPI clamps the pad side of R-SPI-SER (IO35, IO36, IO34 - spi-link), so it "stands on
    # the J-MCU side of the resistors" (layout.yaml, U1's note), beside R1, R2 and R40 east of
    # J-MCU. The cold placement put it WEST of J-MCU, across its top row's way out: the second
    # trial left nine connections there, IO35 open at U1.1 itself (2026-10-13)
    ("R2", ["U1"], "the SPI clamp beside the SPI series resistors it clamps, on their J-MCU side",
     ["W", "S", "N", "E"]),
    # C-VCAP (C207) is U13's VCAP capacitor, U13.1 (VCAP) to U13.6 (BUCK_A_OUT), which stand one
    # above the other on U13's west edge. The cold placement had it beside U13 turned the wrong
    # way, its pads crossing U13's: BUCK_A_OUT C207.2 - U13.6 was the last connection left on the
    # best Freerouting board (2026-10-13). Turned in its seat, its airwire 6.3 -> 4.9 mm, 1 -> 0
    # crossings
    ("U13", ["C207"], "U13's VCAP capacitor against the two pins it joins, turned to match them",
     ["W"], (0, 90, 180, 270)),
]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 0
    import pcbnew
    import yaml
    import pcb_pack
    import cold_trial as C
    src, dst = (os.path.abspath(a) for a in sys.argv[1:3])
    lay = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))
    board = pcbnew.LoadBoard(src)
    rails = [p["net"] for p in lay.get("planes") or []]
    bd = pcb_pack.board_of(board, rails=rails)
    log = []
    pk = pcb_pack.Packer(bd, (), log, escape=C.escape_rows(bd, C.ESCAPE_DEPTH + 0.4, header_depth=C.HEADER_ESCAPE))
    for anchor, parts, why, *more in MOVES:
        sides = more[0] if more else [None]
        turns = more[1] if len(more) > 1 else (0,)
        before = {r: pk.placed[r].centroid for r in parts}
        for side in sides:
            # the first side with a legal row, 15 mm out at most (J-MCU's west is full: U1, U6)
            rep = pk.pack(anchor, parts=parts, side=side, grow=15.0, rotations=turns)
            if isinstance(rep, dict) and rep.get("result") == "packed":
                break
        after = {r: pk.placed[r].centroid for r in parts}
        moved = {r: (round(after[r][0] - before[r][0], 1), round(after[r][1] - before[r][1], 1)) for r in parts}
        print(f"place_moves: {', '.join(parts)} round {anchor}: {moved} - {why}")
        if rep:
            print(f"place_moves:   {str(rep)[:200]}")
    n = pk.apply(board)
    pcbnew.SaveBoard(dst, board)
    print(f"place_moves: {n} part(s) moved; {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
