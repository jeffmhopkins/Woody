# Link supervision — schematic

**NOT FITTED, BY DECISION. Nothing in this directory is on the board.** The
frame watchdog (74HC123) and the presence comparator (LM311) were both deleted
before layout, and neither ever had a `bom.csv` row. **The owner closed the
question on 2026-09-30:** *"Assume the module will be operating with an
umbilical attached to a controller."* So supervision is not restored, and the
cost the section below records — pull the umbilical mid-note and the rack
holds the note — is accepted rather than open. There is no circuit to draw
here and no part to buy; what this directory holds is the argument, so that a
future reader who reopens it starts from the cost and not from zero.

*Moved verbatim from
[`../digital-and-supervision/digital-and-supervision.md`](../digital-and-supervision/digital-and-supervision.md),
2026-09-21, when that page was split into three circuit directories. The record
of the two parts being removed from the drawing is in
[`../digital-and-supervision/notes.md`](../digital-and-supervision/notes.md).*

## Interfaces

Every net that would cross this circuit's boundary **if it were fitted**. Not
one of them is driven today. Quantities appear **only** as a citation into
`config/figures.yaml` — this table names nodes, it does not restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `CLR` | out | `module/dac8568` | — | **Not fitted.** The 74HC123 drove this. It is a net inside `module/dac8568` now, tied inactive by `R-CLR-PU`, with `LK-CLR` as the hand assert; it becomes a port again only if this circuit is restored |
| `OE_MOD` ×4 | out | `module/digital-and-supervision` | — | **Not fitted.** The comparator gated these. Tied enabled instead |
| breath pair | in | `interfaces/breath-sense-link` | `umbilical-pinmap` | **Not fitted.** The LM311 version watched `BREATH_SENSE` and `AGND_SENSE` |
| `UMBILICAL +12V` | in | `module/umbilical-load-switch` | — | **Not fitted.** The first presence version gated `OE_MOD` from this node, downstream of the module's own load switch |
| panel LED | out | `module/panel-led` | — | **Not fitted.** Shared the comparator's collector node. It is an ordinary power indicator now |

## There is no presence detect either

Deleted with the watchdog, and for converging reasons. Two versions were built:
one gating the buffer's `OE` from "+12 V on the umbilical" — a node downstream
of the module's own load switch, which reads *present* with nothing attached —
and one watching the breath line through an LM311.

The second failed review three ways: its threshold sat **inside the breath
signal's own range**, because the sensor is differential with its reference
port open to the cavity and drawing breath moves toward the trip point; it
**locked out every standalone module milestone**, since a dev board on a patch
lead drives nothing into that pair; and it **failed toward "present"** on the
most likely single fault in its own chain.

**`OE` is tied enabled**, which is what every surveyed Eurorack module does.
The floating-CMOS case it was protecting against is what the module's SPI
pulls are for — the five `R-SPI-PULL` and `R-PULL-CS`. The panel LED becomes an ordinary power indicator.

**The knowing moved to the instrument**, which digitises breath anyway and has
its LEDs (ADR 0028) and USB (ADR 0015) to report on. The accepted loss is that the instrument's ADC reads
*before* the umbilical, so a broken conductor in the cable is invisible to it —
audible immediately, and in a replaceable part rather than a sealed one. Full
reasoning in ADR 0004.

## There is no frame watchdog

**Deleted.** A 74HC123 monostable used to assert the DAC's `CLR` when SPI
traffic stopped. The part, its timing pair and its decoupling are gone; `CLR`
is pulled **inactive**, with a solder pad beside it so it can be asserted by
hand.

**It was deleted because it could not do the job it was named for.** ADR 0004
built it to catch "the real-time board hangs mid-note and the rack drones
forever" — and it counts `CS` edges, while `firmware/README.md` mandates
refreshing every channel every pass. A hang *above* the output loop emits
healthy edges indefinitely and the watchdog never fires.

**What it could catch was the link going away**, and that coverage is now
gone too:

| Failure | Watchdog | Now |
|---|---|---|
| Firmware hangs above the output loop | **never caught it** | not caught |
| Cable unplugged mid-note | caught | **not caught — the DAC holds and the rack drones** |
| Instrument loses power mid-note | caught | **not caught** |
| Load switch latches off mid-note | caught | **not caught** |
| Module powered, instrument off | `OE` gating | `OE` gating, unchanged |

So the honest cost of deleting it: **pull the umbilical mid-note and the rack
holds that note until you flip the module's toggle.** That is the everyday
case, not an exotic one.

**What it bought back**, which is why the deletion is defensible: a part that
the cold review found four separate problems with — a retrigger regime nobody
could size without a datasheet, an undefined power-up `Q` state that could
leave it disarmed with a note standing, a software-defeasible clear path
through the DAC's clear-code register, and a 99 ms timeout that would have
fought every "write a code, read the meter" step of E7 through E10.

### The obvious way to get the link coverage back — and what it actually costs

> **This section was headed "for no new parts" and written in the present tense
> until 2026-09-21.** Both were wrong. The presence comparator is deleted on
> this same page, so it reports nothing; restoring this coverage means
> restoring **an LM311, its two decoupling caps, `R-PRESENCE` and a 74AHCT14** —
> four parts, none of which has a BOM row today. The proposal may well be
> right. It has to be costed as a restoration, and it has to answer the three
> faults that deleted the comparator in the first place (ADR 0004), of which
> the threshold problem below is one.

`CLR` **could** be driven from a **restored presence comparator** instead of
from a monostable. Such a comparator would report cable connected, far-end
power, reference alive, sensor alive and both analog conductors intact — which
is precisely the set of failures the watchdog actually covered. Presence drops,
outputs park.

**The complication is polarity.** `OE` is active low and wants the comparator
*asserted* when the instrument is present; `CLR` is active low and wants the
opposite. One open-collector output cannot serve both senses, so it needs an
inversion — and the obvious way to get one is a **74AHCT14 hex Schmitt
inverter**, which two independent reviews already recommended adding as
baseline for edge cleanup on `SCLK`, `MOSI` and `CS` over 2 m of Cat5.

One part, three jobs. Not adopted here because it is a design decision rather
than a correction, and because it should be taken with the SPI edge-cleanup
question rather than separately.

## Decided — not restored (owner, 2026-09-30)

*"Assume the module will be operating with an umbilical attached to a
controller."* The module is specified as half of a pair, not as a standalone
Eurorack module: the state link supervision would have covered — module
powered, link gone mid-note — is outside that specification. So:

- **Nothing is added.** No LM311, no `R-PRESENCE`, no 74AHCT14 and no
  monostable; this directory stays without a `bom.csv`.
- **`CLR` stays tied inactive** inside `module/dac8568` (`R-CLR-PU`, with
  `LK-CLR` as the hand assert), and **`OE_MOD` stays tied enabled** on
  `module/digital-and-supervision`. Neither waits for anything, and nothing on
  either board is sized for a supervisor that might arrive later.
- **The idle state of the link without an instrument is still defined** — not
  by supervision, by the pulls: `CS_MOD`'s pull-up on the cable side and the
  DAC side's three (`interfaces/spi-link`). With the umbilical out, `SYNC` sits
  deselected and nothing reaches the DAC.
- **The accepted cost is the one in the table above**: an umbilical pulled
  mid-note holds the note until the toggle is flipped. E10 still pulls it to
  record what the jacks do.

Reopening it is an owner decision, and the section above is where the costing
starts.
