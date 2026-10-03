# 0016 — One LED strip, on the centre board

**Status:** Accepted. Placement amended by [ADR 0017](0017-one-main-board.md): the
centre board became the main board, and the strip runs down its centreline
with the breath sensor at the mouth end. **The strip is replaced by
[ADR 0028](0028-on-board-leds.md), 2026-09-30**: the option this page left
open, "LEDs populated directly on the centre board", is taken — thirteen
WS2815B-V1 in one row down the main board's centreline, on the same data
line, at one pitch since ADR 0028's amendments of 2026-10-03 (fourteen
for a day from its amendment of 2026-10-02, thirteen again since). One data line, the indirect light path and the cavity as the diffuser
stand; `J-LED` and the `LED-STRIP` reel are gone.

Amends [ADR 0014](0014-lighting.md): its geometry ("two runs, one chain") and
its wiring choice (two independent data lines). Everything else in ADR 0014 —
the 12 V WS2815, the level shifter, the shared current budget and clamp, and
blanking at boot — stands. Decided by the owner, 2026-09-26.

## Context

ADR 0014 put one WS2815 run against the inside of each acrylic side, on two
data lines, because "a single strip down the middle is not available —
switch bodies occupy the centreline for the full length of both key runs."

That was true of the body ADR 0014 was written against. It is not true of
the one the CAD model now derives (`mechanical/`): the carrier's circuits
are on **one flat centre board** lying between the thumb boards and the key
boards, the length of both hands. Its top face is a clear, flat surface down
the middle of the cavity.

The side strips were also costing the layout. Each took a strip's width and a
diffusion gap off both side channels, so the tube lane and the centre board
were pushed inboard by that much on each side.

## Decision

**One WS2815 strip, lying LEDs-up along the centre board's tube-side edge,
lighting both acrylic sides through the cavity.** (Owner: "one led strip, on
the center board. It'll diffuse to both sides.")

- **One data line, GPIO1.** GPIO2 becomes spare. One gate of the 74AHCT125 is
  used; three are spare.
- **One connector, `J-LED`**, on the same board, with one series resistor,
  one pull-down and one bulk capacitor. There is no LED loom any more.
- **The strip's length is derived**: the centre board's length less an inset
  at each end (`config/body.yaml` `lighting`), printed in `mechanical/drc.echo`
  "LED strip on the centre board", with its LED count at the ordered density.
- **The side channels are free.** The tube lane moves out to just inboard of
  the fastener line, and the centre board widens to the far side. That put
  the regulator block beside the key boards rather than under them, where it
  has the height it needs (`mechanical/drc.echo`).
- **The breath sensor moves to the far side of the centre board**, away from
  the strip, still in the gap between the hands. The tube rises to the
  sensor's port height before it crosses the strip.
- **The middle fastener pair moves towards the mouth** when the gap's middle
  would put the far-side screw through the sensor's leads; the centre board
  has a notch for it (`mechanical/cad/woody_body.scad`, `fastener_x`).
  *(Since ADR 0025 there are no body fasteners, no notches and no
  `fastener_x`; the tube lane is placed inboard of the main board's mouth-end
  mounts instead.)*

## Options considered

- **Keep two side strips** (ADR 0014). Light immediately behind each acrylic
  panel, and the evenest result. Rejected by the owner in favour of one strip
  and a cleaner build: no second data line, no loom across the body.
- **One strip, chained or in parallel across both sides** (ADR 0014's A and
  C). Still two runs against the sides, with the costs above.
- **LEDs populated directly on the centre board** instead of a strip. Possible
  now that the lights are on a board we are laying out anyway, and worth
  weighing when the board is drawn. Not decided here.

## Consequences

- **The light is indirect, and that is the risk.** The strip faces the key
  boards' undersides, a few millimetres above it, not the acrylic. The sides
  are lit by what bounces around the cavity. **The cavity is the diffuser**:
  white solder mask on the centre board and on the cavity side of the key
  and thumb boards is the cheap way to make it a better one. How even and how
  bright the sides look is an **M6 prototype** question, and it decides the
  LED density (`config/body.yaml` `lighting.strip_per_m`).
- **Far fewer LEDs.** One run the length of the hands instead of two of
  ~420 mm. The strip rows of ADR 0005's load table and ADR 0014's density
  table were sized for two runs and are now upper bounds; E6 and M6 measure
  the real figures.
- **The strip sits by the breath path.** The strip and the breath sensor now
  share a board. ADR 0003's "keep LED runs away from the breath wiring" is a
  layout rule for the centre board: the strip is on the opposite edge from
  the sensor, and the strip's 12 V return goes straight to the power entry,
  not under the analog section.
- **The hardware pages** changed with this ADR: `hardware/carrier/led-strip-drive/`,
  `power-entry-instrument/`, `carrier.md`, `hardware/nets.yaml`, and the reel
  row `LED-STRIP` in `hardware/unplaced.csv`.
