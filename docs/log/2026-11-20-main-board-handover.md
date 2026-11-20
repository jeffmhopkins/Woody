# 2026-11-20 — What the main board's new layout inherits

A dated record, written when the two key boards and the Matrix carrier had been
laid out by hand (issue #48, ADR 0030) and the main board had not. It says what
those three boards changed that the main board must now meet. Values are as of
this date; the files named own them.

## 1. The Matrix ribbon's pin order has changed

The owner chose to re-order the ribbon's pins so the Matrix carrier routes on
one face with no crossing (ADR 0030, *Amendment, 2026-11-20*). The carrier's
sheet owns the order: `hardware/boards/matrix-carrier/matrix-carrier.kicad_sch`,
tabled in that board's README, *The ribbon's pins*.

The main board's `J-MCU` pin is still 25 minus the `J-MCU-C` pin. So `J-MCU`
must become:

| J-MCU pin | Net | J-MCU pin | Net |
|---|---|---|---|
| 1 | INST_5V_A | 2 | INST_5V_A |
| 3 | INST_5V_A | 4 | PWR_GND |
| 5 | IO33 | 6 | no net |
| 7 | IO34 | 8 | PWR_GND |
| 9 | IO35 | 10 | IO3 |
| 11 | IO36 | 12 | IO1 |
| 13 | IO37 | 14 | PWR_GND |
| 15 | DEV_3V3 | 16 | IO2 |
| 17 | IO38 | 18 | U0RXD |
| 19 | IO7 | 20 | PWR_GND |
| 21 | IO6 | 22 | U0TXD |
| 23 | IO39 | 24 | IO40 |

Until it does, `python3 tools/kicad.py check` prints 21 `matrix:` lines, one
per pin that disagrees. They clear when `J-MCU` matches this table.

What still describes the old order, all of it the main board's to move in the
same change as `J-MCU`:

- `hardware/carrier/carrier.kicad_sch`: `J-MCU`'s wiring, and the notes on
  `J-MCU` and `U-MCU-RT` that name pins 23 and 24 and `carrier_routes.py`
  (a script that no longer exists). Re-export `hardware/carrier/netlist.yaml`.
- `hardware/carrier/midi-out/midi-out.md`, *The ribbon conductors*: IO6's and
  IO2's pins, and the paragraph on the conductor that could not be reached.
- `docs/decisions/0018-*.md`: its amendments' account of `J-MCU` pins 23
  and 24.
- ADR 0018's rule that the three SPI lines and their grounds sit together on
  the ribbon was written for an earlier ribbon; check what of it still binds
  before treating the new order as final. The owner has said the order may
  move again if the main board routes better for it. If it moves, the carrier
  moves with it: change `PINS` in `carrier_layout.py` and the sheet together.

## 2. Both key boards' chain headers have turned

Both hands' chain headers now face the mouth, so neither ribbon lies over its
board's register (ADR 0017, the two amendments of 2026-11-20;
`config/body.yaml` `routing.chain_fold`). The main board's `J-CHAIN-LH` and
`J-CHAIN-RH` turn with them, since each sits straight under its key board's
header. Their places and facing are in
`mechanical/export/pcb-geometry.echo`, cluster `main`, rows `chain`.

- `tools/pcb.py check hardware/boards/main-board` fails its header position
  checks for both until the board is laid out again.
- The right-hand header's place moved along the body when it turned. Read both
  headers from the echo, not from the old board.
- The chain headers' pin order on the main board is open in the same way as
  the Matrix ribbon's: the owner allows re-ordering it if the main board
  routes better. The key boards' ends are in `lh_layout.py` and
  `rh_layout.py`, and their sheets own the order.

## 3. How the three finished boards were laid out

The rules are ADR 0030's, and each board's README has a section *How this
board is laid out*. The mechanics are in `tools/pcb_hand.py`; each board has
one script beside it that writes every track and via. No router of any kind is
run, at the owner's instruction.

## 4. The clash check, run after the headers turned

`mechanical/clash.txt` was rebuilt the same day. Two of its clashes come from
the turned headers, and both are the main board's:

- `switch LT4 x tails J-CHAIN-LH` and `switch RT4 x tails J-CHAIN-RH`. With
  its mouth toward the mouthpiece, each main-board chain header's through-hole
  tails come down where a thumb switch stands under the main board. The key
  boards' own headers are clear.

The main board's new layout has to settle this before copper: move
`J-CHAIN-LH` and `J-CHAIN-RH` off the thumb switches (the ribbon's fold in
`config/body.yaml` `routing` moves with them), or use a header with no tails
through the board. It is the owner's choice if it changes the ribbon's path.

The report's other findings (every key cap against the oak, the breath sensor
and the MIDI lead against the main board, the Matrix's LEDs against the oak
top) are not near the headers. The report had last been rebuilt on 2026-10-05,
before issues #40, #42, #43 and #45 changed the body, so they were probably
there unseen; that is an inference from the dates, not something checked
finding by finding.
