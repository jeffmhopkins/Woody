# Link supervision — schematic

**NOT FITTED. Nothing in this directory is on the board.** The frame watchdog
(74HC123) and the presence comparator (LM311) were both deleted before layout,
and neither ever had a `bom.csv` row. There is no circuit to draw here and no
part to buy. What this directory holds is the argument — why each went, what
went with it, and what restoring the coverage would cost — because that
decision is live even though the hardware is not.

*Moved verbatim from
[`../digital-and-supervision/digital-and-supervision.md`](../digital-and-supervision/digital-and-supervision.md),
2026-09-21, when that page was split into three circuit directories. The record
of the two parts being removed from the drawing is in
[`../digital-and-supervision/notes.md`](../digital-and-supervision/notes.md).*

## Interfaces

Every net that would cross this circuit's boundary **if it were fitted**. Not
one of them is driven today. Quantities appear **only** as a citation into
`config/figures.yaml` — this table names nodes, it does not restate values.

`Dir` is this circuit's side of the net — `in`, `out`, `in/out`, `ref` (a
return or reference) or `—` (no connection here, the row is context). `Peer`
is a bare `board/circuit` id when the other end is a circuit in this tree, a
reference designator or part name when it is not, and `—` when there is
nothing on the other end.

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `CLR` | out | `module/dac8568` | — | **Not fitted.** The 74HC123 drove this. `R-CLR-PU` now holds it inactive and `LK-CLR` is the hand assert |
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
The floating-CMOS case it was protecting against is what the six `R-SPI-PULL`
resistors are for. The panel LED becomes an ordinary power indicator.

**The knowing moved to the instrument**, which digitises breath anyway and has
a display to report on. The accepted loss is that the instrument's ADC reads
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

## Still open

- **Whether to restore link supervision at all**, and at what cost. The section
  above is the candidate; it is four parts, not zero. This is the one open
  supervision question, and it subsumes the three that used to stand here.
