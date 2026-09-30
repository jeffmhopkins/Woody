# LED strip drive — decision history

**Past tense only.** Every live value lives in
[`led-strip-drive.md`](led-strip-drive.md), `config/figures.yaml` or
`hardware/bom.csv`. If a number here is still true, it is in the wrong file.

This is the circuit's superseded shelf — the same convention
`docs/decisions/README.md` runs at project scope, one level down. Nothing is
deleted from it: a deleted superseded value stops warning the next person, and
the refutation wording is what lets `tools/check-staleness.py` tell a quoted old
value from a live one, so the two always travel together.

---

## The WS2815 threshold and `BI` — closed 2026-09-21

*Moved verbatim from `carrier.md`'s `Still open` list, 2026-09-21, where it was
already struck through as closed. The argument it closes on is live and is in
[`led-strip-drive.md`](led-strip-drive.md); "§5" is that page.*

- ~~**The WS2815's data threshold, and whether `BI` needs driving**~~ —
  **closed 2026-09-21** against the datasheet, §5. 5 V logic is correct,
  `BI` is grounded at the head, two gates stay spare.

## Two strips, until 2026-09-26

Until ADR 0016 there were two WS2815 runs, one against each acrylic side,
~420 mm each, on two data lines (GPIO1 and GPIO2, gates A and C) with a
connector, a series resistor and a pull-down each (`J-LED-L`/`J-LED-R`). The
owner moved to one strip lying on the centre board, lighting both sides
through the cavity; GPIO2 and gate C became spare.

## One WS2815 strip, 2026-09-26 to 2026-09-30

From ADR 0016 until ADR 0028 the lights were one WS2815 strip (60/m, 12 V)
stuck down the main board's top-face centreline, its four leads soldered into
four pads, `J-LED` (12 V, `DI`, `BI`, GND). The data line ran through
`R-LED-SER` to `J-LED`'s `DI`; `BI` was a ground connection at the head of the
strip, and from the second pixel on the backup line ran inside the tape. The
strip's data threshold was read off the WS2815 V1.1 sheet: `V_IH = 0.7 × VDD`
in a table whose header declared `VDD = 4.5…5.5 V`, so 3.15–3.85 V; reading
that `VDD` as the 12 V supply pin had given an impossible 8.4 V. The strip
itself was an unplaced BOM row (`LED-STRIP`), a reel.

On 2026-09-30 the owner replaced it with thirteen WS2815B-V1 reflowed onto the
board (ADR 0028). `J-LED` and `LED-STRIP` went; the backup line, which the tape
had carried internally, became board traces; and the threshold is now the
B-V1's own, whose table is stated at the 12 V supply.
