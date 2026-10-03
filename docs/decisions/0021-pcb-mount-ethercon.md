# 0021 — The instrument's etherCON is PCB-mounted, on an adapter joined to the main board

**Status:** Accepted. Decided by the owner, 2026-09-29. It settles ADR 0004's
open question *which etherCON variant at each end* **for the instrument's end
only**; the module's end is [ADR 0023](0023-module-ethercon-and-two-boards.md). **Amended 2026-10-02** (the main board's tail end runs full width, *Amendment* below).

## Context

The instrument's etherCON was a feedthrough (Neutrik NE8FDP, `J-UMBILICAL`)
with an RJ45 socket at its back. A short patch lead (`CBL-UMB-PATCH`) ran from
that socket to a latching header (`J-UMB`) on the main board. That added two
contact interfaces to every conductor of the umbilical, including the +12 V
path and the breath pair. ADR 0004 recorded that as the cost of the
feedthrough and deferred the choice. The patch plug and its boot were also
the longest item behind the last key, so they set the body's length
(`mechanical/drc.echo`, *what the tail end needs*).

Owner, 2026-09-29: *"it's about time that we convert the ethercon connector
to a PCB type, if we need to make a little adapter board to hook the flex
connector to that's fine, otherwise, it might just be easier to extend the
main board down and mount it directly to that."*

## Decision

1. **The instrument's etherCON is a Neutrik NE8FAV** (`J-UMBILICAL-INST`):
   an A-series receptacle for a vertical PCB, mounted from behind the panel.
   Its drawing, data sheet and 3D model are banked
   (`datasheets/connectors/NEUTRIK-NE8FAV-*`). Every number the body CAD uses
   is in `config/body.yaml` `ethercon:`, each with its source.

2. **It is soldered to a small board of its own, the umbilical adapter**
   (`PCB-UMB-ADAPTER`). The adapter stands parallel to the tail cap, the
   flange's outline in size. Its tracks run each etherCON pin to the
   same-numbered pin of `J-UMB`, and it carries nothing else.

3. **`J-UMB` is now a 1 × 8, 2.54 mm right-angle pin header, soldered into
   both boards.** Its insulator lies on a **tongue of the main board**, its
   tails go down through the tongue and its posts through the adapter. The
   tongue runs from the main board's tail end to the adapter's rear face.
   Pin N is still etherCON pin N, so
   every "`J-UMB` pin N" on the carrier's pages still means the same
   conductor. There is no cable and no mated contact between the etherCON
   and the main board. `CBL-UMB-PATCH` is gone.

4. **Latch up.** ADR 0009 turned the NE8FDP 90° so that its 26 × 31 flange
   fitted the body's height. The NE8FAV's flange is square, so that reason
   no longer applies. The PUSH tab is on top, where a thumb finds it. The
   contact rows sit above the axis, which leaves the band below the axis
   for `J-UMB`'s row (`ethercon.rotated`).

5. **The tail cap has a recess from outside for it.** The NE8FAV allows a
   3 mm panel at most (`ethercon.panel_max`) and the oak cap is thicker, so
   a router pocket leaves exactly that much oak where the flange clamps. The
   recess takes the flange's outline, the PUSH tab and a margin
   (`ethercon.recess_margin`, decided with the cable connector in hand).
   Two of Neutrik's A-series screws go through its floor into the flange
   (`MECH-ETHERCON-SCREW`).

6. **Its two locating pegs are cut off flush.** They stand below the flange
   (`ethercon.peg_below`) and, with the connector on the floor latch up,
   point into the oak bottom. Drilling the floor for them would locate the
   connector a second time, against the cap's screws, across oak that moves;
   standing it higher would take more body than `body-thickness` has.

## Why not mount it on the main board directly

That was the owner's first suggestion, and the NE8FAH (the same connector
for a horizontal PCB) would do it. Both the NE8FAH and the NE8FAV put the
axis 12.5 mm above the flange's lower edge
[ds `NEUTRIK-NE8FAH-DRAWING.pdf`, `NEUTRIK-NE8FAV-DRAWING.pdf`]. On a
horizontal board that is also the height above the board's top face, and
the main board's top face is fixed by the thumb switches soldered into it
(`switch.thumb_pcb_below_seat`). The connector's body, a flange's height
above that face, would then stand 3 mm above the oak top's underside. Its
PUSH tab, which rises above the flange's outline, would stand about 7 mm
above it, through the cap's top edge [calc from `mechanical/drc.echo`'s
tail Z levels and the NE8FAH model]. The main board cannot drop at the tail
because it is one flat board, so the body would have to grow by at least
the first figure and the cap would lose its top edge to the second. The vertical-PCB part
on an adapter stands on the floor as the NE8FDP did.

A flex cable between the adapter and the main board was the other way to
join them. A right-angle header does the same job with no connector and no
cable. Its pins carry more current than the etherCON's own contacts do, and
ADR 0004 counted every contact interface as a cost.

## Consequences

- **Two contact interfaces fewer in every umbilical conductor**, and one
  cable fewer to make by hand.
- **The tail is shorter.** Removing the patch plug took away the claim that
  set the tail's length. The Matrix, centred after the keys, now sets it,
  and the body shortens by what `mechanical/drc.echo` *overall length*
  reports. The gap between the hands follows the keys-to-Matrix gap (owner,
  2026-09-26) and is now at its minimum, `layout.gap`. So the right-hand
  cluster moved toward the mouth. The left-hand ribbon's hairpin moved
  because it clears the lid screw between the hands. Both key boards were
  re-laid out from the body CAD. *(Since ADR 0025 there are no lid screws;
  the hairpins clear the cassette's columns.)*
- **The body could be thinner.** `mechanical/drc.echo` *body thickness takes
  the etherCON on the floor* reports the spare. `body-thickness` is the
  owner's figure and was not changed here.
- **The main board is longer, by the tongue.** The tongue is as wide as the
  adapter and notched where the last lid screws pass. It has standoffs
  under J-UMB's end. *(Since ADR 0025: no notches; the tongue's pair of mounts
  stands on the bottom plate, which stops short of J-UMB.)* *(2026-09-30,
  the owner, on a marked-up render: "I'm ok with it being more narrow, but
  ... my red line is inset just slightly which is not needed." On the side
  where the adapter's edge falls just inside the main board's, the tongue
  now runs straight on from the main board's edge with no step; the other
  side keeps its step to the adapter's width. `mechanical/drc.echo`
  *"main board's tongue flush with its edge on the near side of the
  adapter"* says which side and by how much.)* *(2026-10-02: no step on
  either side now. The board runs full width to the adapter. See the
  amendment below and `mechanical/drc.echo` *"main board's tail end runs
  full width beside the etherCON adapter"*.)*
- **Taking the main board out means unscrewing the etherCON from outside
  first.** The connector, the adapter and the board come out as one piece.
  The nose sits in the cap's bore, so the assembly slides back before it
  lifts.
- **The cable connector is unconfirmed.** The NE8FAV names "NE8MC* or any
  standard RJ45 plug" and excludes the NE8MC6-MO and NKE6S* cables. It does
  not name the NE8MX, the NE8MC's successor (`J-UMBILICAL-CABLE`).

**`J-UMB`'s part** was chosen the same day: hanxia HX PZ2.54-1x8P WZ
(`hardware/interfaces/spi-link/bom.csv`). Its drawing
(`datasheets/connectors/HANXIA-HX-PZ2.54-1x8P-WZ.pdf`) settles the insulator
and row height in `boards.umb_joint_*`. The 6.00 mm posts pass the adapter
with enough standing in front to trim, and the 3.00 mm tails pass the 1.2 mm
tongue.

## Open, and what decides each

| Item | Decided by |
|---|---|
| The recess margin round the flange and the PUSH tab | M4, with the cable connector in hand |
| The mounting screws' part and length for a 3 mm panel | M4, with the connector |
| Whether the NE8MX latches in the NE8FAV | Before buying the cable connectors |
| The module's end | E12/M7 (ADR 0004) |

## Amendment, 2026-10-02 — the main board's tail end runs full width

**Owner, 2026-10-02**, on the main board's tail: *"can you explain why we
have this cut out on the bottom main board? I feel like it's not necessary,
and that maybe we can get another LED down there"*, and *"I think maybe
because we changed how the ethercon connector is mounted that we have a
longer standing decision on the main board that is no longer valid. I feel
like the USB is high enough in the bottom of the controller that we can run
a cable without having to muck around with the PCB."*

**Why the cut-away was there.** Decision 3 made the tongue *as wide as the
adapter*, and the Consequences above say why it stayed narrow: it was
*notched where the last lid screws pass*. ADR 0025 removed the lid screws and
the notches; the narrow tongue outlived its reason. The 2026-09-30 note only
trimmed its near side. Nothing else ever claimed the corner.

**What stands in the corner, from the body CAD** (`[repo]` the model's
solids intersected with the corner past the right-hand key board and beside
the adapter's width, full cavity height; numbers as `mechanical/drc.echo`
and `mechanical/export/pcb-geometry.echo` print them):

| Solid | Where, over the corner | At the board's height? |
|---|---|---|
| USB-C extension receptacle (`CBL-USB-EXT`) | its back face reaches 0.1 mm over the board's end; the rest stands behind the adapter's rear face, beside the flange | no: its underside was 2.55 mm above the board's top face, inside the board's 2.62 mm parts height, so it now rises (below) |
| USB-C extension lead | from the Matrix's mouth edge down to the receptacle's back, over the corner | no: its underside stays more than 5 mm above the parts |
| Matrix ribbon, level run into `J-MCU` | its edge overhangs the old tongue's edge by about 2 mm | already over the board, with its own parts keep-out |
| Bottom plate | under the board, as everywhere | under it |
| Key plate, Matrix, its harness and parts | 19 mm and more above the board | no |

The etherCON, its adapter and `J-UMB` stand at and past the board's end
across the adapter's width only. So the corner held nothing at the board's
height, and the owner is right that the USB-C cable needs no cut in the board.

**Decision.** `boards.main_tail` = `full` (`config/body.yaml`): the main
board runs its whole width from the right-hand key board's end to the
adapter's rear face, so its outline is a plain rectangle. The corner it gains
is the 48.6 × 15.5 mm that *"main board's tail end runs full width beside the
etherCON adapter"* prints; `tongue` keeps the old outline if it is ever
wanted back. The tongue's two end mounts, `J-UMB`, the bottom plate's end
and the parts band at `J-UMB` do not move.

**The USB-C receptacle stands higher.** The receptacle's body reaches back to
the board's end, so it now stands `boards.board_clear` above the parts the
corner may carry (`boards.smt_h`), the clearance a key board keeps from the
parts under it, instead of centred in the cavity. It rises 1.57 mm `[calc:
10.1 + 2.62 + 1.5 + 12.5 / 2 = 20.47, against the centred 18.9]`, and the
tail-face slot and overmould pocket follow it; every USB-C rule still passes.
A receptacle bought deeper than `openings.usb_ext_depth` would now stand over
the board, which is why the clearance is vertical and not a gap along the body.
`pcb-geometry.echo` carries a *USB-C receptacle and lead* keep-out over the
corner: parts to `boards.smt_h`, nothing through-hole and tall.

**What the layout has to do** (the `.kicad_pcb` is the source; this
amendment does not touch it): take the new `main-board.dxf` outline and
the new keep-out; extend the pours and planes (`INST_POS12` on layer 3,
`PWR_GND`) into the corner; re-check the edge clearance along the old
tongue's far edge, where parts placed against it (`Q-INRUSH`'s gate network,
`R43`/`D20` at y 30.8) now have board beyond them. No placed part has to
move, and no net changes.

### Open — for the owner, with numbers

**A fourteenth LED.** The corner is off the centreline. On the centreline
past `J-MCU` an LED stands under the Matrix ribbon's level run and sees
11–15 % of the side faces past the key board (below), so it is not worth
having. In the corner it works. Sightlines from the emitter (board top +
`lighting.led_h`) to each acrylic side's inside face, through the CAD's
solids (`[calc]`, ray cast; a wall point counts if nothing stands between;
85 % is all of it above the board):

| LED | far side, x 250–270 / 270–290 / 290–320 | near side, same bands |
|---|---|---|
| `LED1` today (centreline, x 224.7) | 18 / 35 / 13 % | 0 / 2 / 4 % |
| **at x 274.7 (LED1 + 3 × `lighting.led_pitch`), 13.5 mm off the centreline toward the near side** | 17 / 59 / 36 % | 85 / 85 / 85 % |
| at x 258.0 (LED1 + 2 pitches), same offset | 48 / 29 / 7 % | 85 / 85 / 85 % |

The tail's near side is almost unlit today. The regulator block, 12.5 mm
tall on that side in front of `J-MCU`, shadows `LED1`. One LED in the corner
lights it. The far side gains most past the Matrix ribbon's drop. The near
side is 9 mm away against the row's ~22.5 mm, about six times the
irradiance `[calc: (22.5 / 9)²]`, so firmware would scale that LED down to
match. The diffusion test (ADR 0028) is the judge. What it changes:
`lighting.led_count` 13 → 14, plus the row's placement (it is off the
centreline, so the body CAD needs a second row record), and
`led-row-current` scaled by 14/13 `[calc: 14 × 0.18 W / 12 V = 210 mA upper,
14 × 13.1 mA = 183 mA lower, 28 mA blanked]`. The +15 mA is under 1 % of
U-ISO's rating. The register's `umbilical-current` upper bound would move
by the same 15 mA. `led-pwm-rail-ripple` and `led-pwm-pitch` scale with the
row's swing and should be re-simulated, not scaled. The new LED has to be
first in the data chain, because the data arrives at the tail:
`R-LED-SER` → the corner LED → `LED1`. That adds about 50 mm of feed and
55 mm of return across the `J-MCU` area. The backup line follows ADR 0028
point 5: the corner LED's `DIN2` to GND, and `LED1`'s `DIN2` from the
feed. The refdes are renumbered in chain order. Firmware: one more pixel
(~30 µs more per frame at 800 kbit/s) and a per-LED gain for it. **Added
2026-10-02** by the owner ("Add it"; ADR 0028's amendment of that date).

**`HDR-SERVICE` where it is, or elsewhere.** ADR 0018 point 4 puts it on the
main board, reached with the lid off. Since ADR 0025 that means cutting the
oak top free, with the key boards still over the main board. So it must sit
outside both key boards' outlines and near `J-MCU`, whose pins 21–24 it
takes. `EN` has no capacitor on the Matrix, so the shortest trace is worth
keeping. Its place on the tongue is the first layout's (`layout.yaml`
`J2`), recorded as `boards.service_hdr_at` (nominal). It is a vertical 1 × 5.
Nothing stands over it, so a right-angle or lower part gains nothing in
height. It can move into the new corner if the owner wants the tongue's far
side clear, as long as it stays out of the 14th LED's light. Its tails then
stand past the bottom plate's end, over oak, and its plate window goes.

**A board-mount USB-C at the tail face** (owner's follow-up, 2026-10-02).
Candidate part: HRO `TYPE-C-31-M-12` (LCSC C165948, banked
`datasheets/connectors/HRO-TYPE-C-31-M-12.pdf`). It is 8.94 wide, 7.35
long and 3.26 tall over the board, and its shell stands only 0.40 past the
board's edge. On a finger of the main board beside the adapter, run on to
the tail cap's inside face, it fits across the lane and in height. Its
face would then be the cap's thickness behind the tail face, so the
plug's overmould needs a through-opening the overmould's size. Lying flat,
that is `openings.usb_overmold`'s wide side across the lane. From the
etherCON recess's 2 mm web to the cavity's side that leaves 14 mm against
the 15 the allowance asks, so it fails by 1 mm. The Matrix's `D+`/`D−`
(`IO19`/`IO20`) are on none of its pads or test points
`[ds WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf]`. They reach the board only
by soldering to its USB-C's 0.5 mm-pitch contacts or by a short plug pigtail
into it, which is a cable again. All 24 ribbon conductors are allocated.
`IO2`/`IO3` are the spares that shield `IO7`, and they are not adjacent. The
board would carry CC1/CC2 5.1 kΩ to ground, an ESD array, and `VBUS` through
a Schottky onto the 5 V OR node beside `D-USBOR`. **Not adopted.** Decided
by the owner. A Matrix carrier board under the Matrix (headers on its pad
rows, an IDC header to `J-MCU`) fits the height under the Matrix. It leaves
the same `D+`/`D−` problem.

**The Matrix on an extension of the right-hand key board** (owner's
follow-up, 2026-10-02: *"would that be better to attach as a extension of
the right hand PCB?"*). Heights from the body CAD:

- The key board's top face is 30.5 (the plate's top, less
  `switch.pcb_below_seat`).
- The Matrix's underside is 31.4 (its top against the oak, less
  `boards.matrix_t`).
- So an extension would stand 0.9 mm below the Matrix's underside.
- The Matrix's back-side parts (`boards.matrix_under_h`: its USB-C, the
  ESP32-S3, the buttons) hang 3.2 mm, down to 28.2, through the board's
  plane at 28.9–30.5.

The extension therefore cannot lie flat under the Matrix. It would be two
rails under the pad rows, at 28.5 ± 11.43 across, with the middle open for
those parts. The opening also takes the extension cable's right-angle plug,
which stands at 24.4–31.4 in front of the Matrix's mouth edge. The 0.9 mm
gap needs bare header pins through both boards on a 0.9 mm shim. Without
the shim, the Matrix sits on the rails and drops 0.9 mm from the oak, and
its LED tops go from 2 to 2.9 mm under the acrylic. The key plate ends 1 mm
short of the Matrix (`plate_x1`), above the board's plane, so it is not in
the way. The extension adds about 46 mm to the board's 107 mm length, and
it cantilevers 37 mm past the board's tail columns to the Matrix's centre.
`CBL-MCU-RIBBON` would become a plain IDC ribbon from a header under the
extension straight down to `J-MCU`, with the same pin map. `EN`, `IO0` and
the extra 5 V and GND still need short wires from the Matrix's button pads
and test pads to the rails. The `D+`/`D−` problem is unchanged. **Not
adopted.** Decided by the owner.

**Found doing this:** the Matrix has **no ESD protection on its USB-C**.
`J1`'s D± run straight to the ESP32-S3
`[ds WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf, USB block]`, so the tail-face
receptacle exposes the MCU's USB pins with nothing in between. `U-ESD-USB`'s
note (*"Dev boards carry these"*) is wrong for this board. That is a finding
for the owner and the BOM fragment's owner, not fixed here.
