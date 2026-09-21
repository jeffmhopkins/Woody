# S2 — Umbilical, looms and connectors: staleness sweep

**Date:** 2026-09-21
**Scope:** every cable in the system and the connectors at both ends — the
umbilical (`CABLE-UMB`, `J-UMBILICAL`), the key chain (`J-CHAIN`, `WIRE-LOOM`),
the display loom (`J-DISP`, `HDR-SERVICE`), the LED looms (`J-LED-L/-R`), the
dev-board sockets (`HDR-DEV`), and the nets that live on them.

**Corpus audited:** `hardware/**`, `docs/decisions/**`, `config/**`,
`docs/reference/**`, `ROADMAP.md`, `README.md`, `firmware/README.md`.
`docs/review/**`, `docs/log/**` and `docs/research/**` were read for context and
are **not** reported against — they are historical records.

**No corpus file was edited.** This report is the only file written.

Indexed by **disputed fact**, not by document. Each entry quotes both sides.

---

## Ranking summary

| # | Disputed fact | Rank |
|---|---|---|
| F1 | Umbilical pin map — which signal is on pins 4, 5 and 7 | **Showstopper** |
| F2 | Conductors per key-chain hop — 12, or 6 | **Showstopper** |
| F3 | `CABLE-UMB` conductor gauge and resistance — solid-core number, stranded cable, no AWG specified | **Showstopper** |
| F4 | Cable-side `CS` idle pull rail — +5 V, or 3V3 (a rail the module does not have) | **Showstopper** |
| F5 | SPI series resistors — refdes, value, and the derivation | **High** |
| F6 | Number of `J-CHAIN` connectors — 8, 5 or 4 | **High** |
| F7 | The `J-CHAIN` mating sockets and ribbon assemblies have no BOM row | **High** |
| F8 | `DIG_GND` — no origin at the instrument end, and a direct dispute at the module end | **High** |
| F9 | Cable shield / etherCON shell bonding policy — does not exist | **High** |
| F10 | No cable-side etherCON shell in the BOM; `CABLE-UMB` is "RJ45 both ends" | **High** |
| F11 | `J-DISP` has no BOM row, and neither does the display board's own connector | **High** |
| F12 | LED connectors — no BOM row, 6-vs-8 conductors, 220 Ω vs 330 Ω, spare gates | **High** |
| F13 | Five new BOM rows are still drawn as "proposed / not in the BOM" | **High** |
| F14 | Total loom conductor count — ~28–30, and the "~23" it refutes exists nowhere | **High** |
| F15 | `WIRE-LOOM` — one qty-1 row for four physically different harnesses | **High** |
| F16 | Chain `SER` source pin `IO33` — spare, or driving the loom | **High** |
| F17 | `HDR-SERVICE` — 2×3 or 2×5 | **Medium** |
| F18 | SPI clock over the umbilical — ~1 MHz or 2 MHz | **Medium** |
| F19 | `R-CHAIN-SER` fitted vs ADR 0001's deletion of driving-end series resistors | **Medium** |
| F20 | `HDR-DEV` quantity — 6 strips, or one board's worth | **Medium** |
| F21 | Which board the instrument end of the cable lands on | **Medium** |
| F22 | ADR 0001's own per-hop arithmetic does not add to 12 | **Medium** |
| F23 | `ADR 0005` power tree calls the chain's 3V3 load "microamps" | **Medium** |
| F24 | ROADMAP still prices the etherCON against an 8HP panel | **Low** |
| F25 | ADR 0004's pre-revision cable budget still lists `MISO` and a spare | **Low** |
| F26 | `CABLE-UMB` spec: "two things are not optional", then three bullets | **Low** |
| A1–A6 | Facts asserted but never derived | mixed |

---

# Part 1 — Contradictions

## F1. Umbilical pin map — which signal is on pins 4, 5 and 7 — **SHOWSTOPPER**

The change landed in three places and was missed in two. One of the misses is
the **first drawing a builder reads on the instrument side**.

**Current (3 documents agree):**

`docs/decisions/0004-cv-interface-module.md:755-757`
```
| 4, 5 | ✓ | **SCLK / MOSI** — *revised 2026-09-21* |
| 7, 8 | ✓ | **CS / DIG_GND** — *revised 2026-09-21* |
```

`hardware/controller/carrier.md:531-534`
```
  IO35 SCK  ──[R-SPI-SER 100R]───┬──── J-UMB pin 4   ┐ pair (4,5)
  IO36 MOSI ──[R-SPI-SER 100R]───┼──── J-UMB pin 5   ┘
  IO34 CS   ──[R-SPI-SER 100R]───┼──── J-UMB pin 7   ┐ pair (7,8)
                                 │     J-UMB pin 8 ──┘ DIG_GND
```

`hardware/module/digital-and-supervision.md:23-29` — "NEW PIN MAP - see ADR 0004",
`4 SCLK`, `5 MOSI`, `7 CS`, `8 DIG_GND`.

**Stale, same file as one of the correct drawings** — `hardware/controller/carrier.md:50-51`,
the page's top block diagram:

```
   │ J-UMB   1 BREATH   2 AGND   3 +12V   6 PWR_GND   4 MOSI   5 CS      │
   │         7 SCLK     8 DIG_GND                                        │
```

This is the **old** map. `carrier.md` therefore contains both maps, 480 lines
apart, with no cross-reference. A reader who takes the block diagram as the
summary gets `CS` on pin 5 twisted against `MOSI` on pin 4 — exactly the
365–907 mV intra-pair crosstalk case the swap was made to delete.

**Stale, in the ADR that carries the correct table** —
`docs/decisions/0004-cv-interface-module.md:82-87`:

```
### Revised conductor budget

+12V      / PWR_GND     power, and the presence signal
SCLK      / DIG_GND     SPI to the DAC, ~1 MHz
MOSI      / CS
BREATH    / AGND        analog, band-limited ~500 Hz, sense return
```

This block is titled **"Revised"** and pairs `MOSI` with `CS` — the pairing the
same ADR later calls "the most efficient coupling structure available". Line 748
then says "**The conductor budget above** has to map onto those" and maps it
differently. The ADR contradicts itself by 660 lines.

**Why Showstopper:** this is copper at both ends, unretrofittable at the
instrument end once the body is bonded (ADR 0009), and the two stale copies are
the *summary* views — the block diagram and the conductor budget — which are
what get transcribed into a netlist.

**Fix:** carrier.md:50-51 → `4 SCLK  5 MOSI  7 CS  8 DIG_GND`.
ADR 0004:84-85 → `SCLK / MOSI` and `CS / DIG_GND`, or strike the block and point
at the pin-assignment table.

---

## F2. Conductors per key-chain hop — 12, or 6 — **SHOWSTOPPER**

`J-CHAIN` went to a 2×6 IDC on a 12-way ribbon. **Seven corpus locations still
say six**, including the two files that generate manufacturing artefacts
(`config/key-layout.yaml`, which the plate DXF and board outlines come from) and
the BOM row for the boards themselves.

**Current (5 places agree):**

`docs/decisions/0001-mcu-and-board-partitioning.md:249-251`
> **`J-CHAIN` is a 2×6 IDC on a 12-way ribbon**, alternating ground:
> `GND SCK GND SH/LD GND SER GND QH GND 3V3 spare spare`.

`hardware/bom.csv` `WIRE-LOOM` — "TWELVE conductors per hop"
`hardware/bom.csv` `J-CHAIN` — "2x6 2.54mm IDC boxed header, keyed"
`hardware/controller/carrier.md:395-396` — "J-CHAIN (2×6 IDC, 12-way ribbon, 10 wired + 2 spare)"
`hardware/controller/cluster-boards.md:205` — "`J-CHAIN` is a 2×6 IDC boxed header on a 12-way ribbon"

**Stale — `config/key-layout.yaml:100-101`:**
> `# Six conductors leave each board - VCC, GND, CLK, SH/LD, SER-in, QH-out - with`
> `# a ground return per signal, chained cluster to cluster rather than starred.`

Self-contradictory on its own terms: it names **one** GND and then claims "a
ground return per signal". This file is the declared source of truth for the
chain order and the plate DXF.

**Stale — `ROADMAP.md:196`**, a milestone gate:
> | **Does the chained key loom fit the side channel?** | M4 | Six conductors per hop rather than the 32–44 the tail-mounted alternative needed …

The M4 fit check is being run against **half** the real ribbon width.

**Stale — `hardware/bom.csv`, `PCB-CLUSTER`:**
> "every switch-to-chip connection becomes a TRACE and **only six conductors leave each board**"

**Stale — `docs/decisions/0001-mcu-and-board-partitioning.md:160`**, in the same ADR that decided 12:
> "It wins on hand-joint count …, on loom width (**6 conductors per hop** against 40–56 mm of ribbon …)"

**Stale — `docs/decisions/0001-mcu-and-board-partitioning.md:366`:**
> "every switch-to-chip connection is a trace on the board the switch is already soldered to, and **six conductors leave each cluster**."

**Stale — `docs/decisions/0001-mcu-and-board-partitioning.md:131`:**
> "**Four conductors plus power leave each board.**"

**Stale — `hardware/controller/carrier.md:471-473`**, in §3, forty lines *below*
that page's own 12-way drawing:
> "**Six conductors is the signal count, not the conductor count.** Whether this
> connector is 6-way or 10-way is a decision this page cannot take alone — see
> *Still open*."

The decision was taken; this paragraph re-opens it, and offers 6 or 10 — neither
of which is 12.

**Stale — `hardware/controller/carrier.md:822-824` and `:846`**, twice:
> "the channels now carry **one 8–11 way loom instead of four ribbons totalling
> 40–56 mm of width**"
> "carrier, two LED strips, **one 8–11 way key loom**, the display loom, the
> breath tube and the U-bolt in 49 mm of internal width"

The width crunch — 49 mm internal against a 45 mm board — is being argued
against an 8–11 way loom that does not exist. The real ribbon is 12-way.

**Why Showstopper:** the cavity fit check (M4), the plate DXF and the side-channel
width argument are all being computed from 6–11 conductors against a decided 12.
This is the specific number that gets sealed into a bonded body.

---

## F3. `CABLE-UMB` resistance — the solid-core figure for a stranded cable, and no gauge at all — **SHOWSTOPPER**

**Nothing was corrected.** Every resistance figure in the corpus still derives
from **0.168 Ω per 2 m**, which is the **solid** 24 AWG number (84.2 Ω/km), on a
cable the BOM mandates as stranded.

**The BOM insists on stranded and specifies no gauge:**

`hardware/bom.csv` `CABLE-UMB`:
> part: `Cat5e STP patch lead, STRANDED, ~2m` · package: `RJ45 both ends`
> notes: "**STRANDED not solid-core**: solid core work-hardens and fractures
> under constant flexing, which is this cable's whole life."

There is **no AWG anywhere in the row**. Stranded Cat5e patch leads are commonly
26 AWG, and "slim"/"snagless" leads are 28 AWG.

**Every consumer assumes 24 AWG solid:**

`docs/decisions/0003-breath-sensing-path.md:311-314`
```
| Receiving input | Signal current | Drop across 2 m of 24 AWG |
| 100 kΩ | 50 µA | 8.4 µV |
```
8.4 µV / 50 µA = **0.168 Ω**.

`docs/decisions/0003-breath-sensing-path.md:322-326` — the shared-ground table,
`100 mA → 16.8 mV`, `200 mA → 33.7 mV`, `350 mA → 58.9 mV`: all 0.168 Ω.

`docs/decisions/0005-power-architecture.md:91`
> "Over 2 m of 24 AWG, **round trip ~0.34 Ω**"
…which is 2 × 0.168, and it produces the 122 mV / **~11.4 V** arrival figure that
the whole "12 V not 5 V" decision and the buck's headroom rest on.

`hardware/controller/carrier.md:269-273`
> "using ADR 0003's own cable figure (**0.168 Ω for 2 m of 24 AWG**, implied by its
> 8.4 µV / 50 µA row)"
> `13 mA × 0.168 Ω = 2.2 mV on the sense pair`

**The arithmetic of the discrepancy, for the record:**

| Cable actually bought | Ω per 2 m, one way | Round trip | vs the 0.34 Ω assumed |
|---|---|---|---|
| 24 AWG **solid** (the number in use) | 0.168 | 0.336 | 1.00× |
| 24 AWG **stranded** (what the BOM mandates) | ~0.19 | ~0.38 | ~1.13× |
| 26 AWG stranded (common patch lead) | ~0.30 | ~0.60 | ~1.78× |
| 28 AWG stranded (slim / snagless) | ~0.48 | ~0.95 | ~2.8× |

At 28 AWG the +12 V cable drop at the clamp-legal 579 mA is ~550 mV rather than
~200 mV, on a rail already losing ~400 mV to the Schottky, feeding a buck with an
8 V dropout floor. The cable is a declared **consumable** replaced "at the first
sign of intermittency" — so the gauge is not a one-time decision, it is a
purchasing rule that has to be written down or it will be got wrong in a hurry
from a drawer.

**Nothing in the corpus states the gauge, and nothing reconciles solid vs
stranded.** The only assertion of 24 AWG is inside derivation tables in ADR 0003
and ADR 0005 — it is never a specification, and it appears in no BOM row.

**Fix:** put the gauge in `CABLE-UMB` ("24 AWG stranded pure copper, not CCA,
not 26/28 AWG slim"), give it an acceptance test (loop resistance), and either
re-run the ADR 0003 / ADR 0005 / carrier.md figures at the stranded value or say
in one place that 0.168 Ω is the solid-core value used as a lower bound.

---

## F4. Cable-side `CS` idle pull — +5 V or 3V3, and the module has no 3V3 rail — **SHOWSTOPPER**

Three documents give three answers, and the one stated most forcefully names a
rail that does not exist at the module end.

`docs/decisions/0004-cv-interface-module.md:348`
> "- **CS pulled to +5 V; SCLK and MOSI pulled to ground**, at the module end."

`hardware/bom.csv` `R-SPI-PULL` — **both answers in the same cell**:
> "Cable side: **CS to +5V**, SCLK and MOSI to ground, so the buffer's inputs do
> not float and crowbar when the instrument is absent."
> … later in the same note …
> "**CABLE-SIDE CS PULLS TO 3V3, NOT +5V**: pulled to 5V it drives 430uA
> continuously through the unpowered ESP32's input clamp in the design's NORMAL
> resting state, and the node sits at ~0.7V so 'CS idle high' is not even
> achieved."

`hardware/module/digital-and-supervision.md:30-33` — the drawing names no rail at
all:
```
        │   [R-SPI-PULL x3]
        │    SCLK↓ MOSI↓ CS↑
```

**There is no 3V3 rail on the module.** The module's rails, per
`docs/decisions/0005-power-architecture.md:190-202` and
`hardware/module/power-entry.md`, are ±12 V from the bus, bus +5 V (for the
74AHCT125 only), and `AVDD` = 5.21 V from the LM317. A grep for `3V3` / `3.3 V`
across `hardware/module/**` returns **nothing**. The instrument's 3V3 is 2 m away
and is not one of the eight conductors.

So the BOM's decided position is, as written, **unbuildable**, and the ADR's
position is the one the BOM says produces 430 µA of continuous clamp current
through an unpowered ESP32 in the design's normal resting state.

**Why Showstopper:** this is the resistor that keeps `CS` from glitching while
the module is alive and the instrument is off — which ADR 0004 itself calls "the
state the instrument spends most of its life in", and a stray `CS` edge is the
one digital failure that does not self-heal. The part is specified against a
rail nobody has drawn.

**Fix needed:** either derive a small local 3.3 V at the module (and add it to
the power tree, the BOM and `power-entry.md`), or re-derive the +5 V case, or
move the `CS` pull to `AVDD` as the DAC-side pull already is. Pick one and say so
in ADR 0004, the BOM row and the drawing together.

---

## F5. SPI series resistors — refdes, value, and the derivation — **HIGH**

Renamed `R-SCLK-SER`/`R-MOSI-SER`/`R-CS-SER` → `R-SPI-SER`, and 220 Ω → 100 Ω.
The BOM and `carrier.md` are both current. **ADR 0004 still carries the old
refdes, the old value and the discredited RC derivation, in two places.**

**Current:**

`hardware/bom.csv` `R-SPI-SER` — `100R 1%`, qty 3:
> "THREE. 100R, not 220R - revised 2026-09-21. 2m of Cat5 is a 100-ohm
> TRANSMISSION LINE (20ns round trip against 2-5ns edges), **not an RC corner**
> … carrier.md used to draw these as R-SCLK-SER / R-MOSI-SER / R-CS-SER, which
> were in no BOM"

`hardware/controller/carrier.md:540-563` — "**All three are `R-SPI-SER`, and the
value is 100 Ω**", with the 220 Ω / 1.83–1.86 V vs 2.0 V `V_IH` table.

**Stale — `docs/decisions/0004-cv-interface-module.md:69-74`:**
> "`R-MOSI-SER` at 220 Ω with ~200 pF of cable is a **3.6 MHz** corner — 7.9 MHz
> is the 100 Ω case this same sentence offers as the fix, which is the wrong way
> round. 2 MHz still has margin, but less than claimed, and transmission-line
> analysis puts the right value **nearer 68 Ω**, which is closer to a real source
> match on Cat5's ~100 Ω anyway."

Three faults in one passage: dead refdes; the RC-corner model that three
reviewers rejected; and a recommendation of **68 Ω**, which the BOM and
`carrier.md` both explicitly reject — "68R is electrically ideal but draws 48mA
against a 40mA pad spec".

**Stale — `docs/decisions/0004-cv-interface-module.md:479-481`:**
> "**220 Ω in series on MOSI at the driving end.** Source termination on **the one
> line** that runs the full umbilical carrying data."

Wrong value, wrong count (one, not three), and "the one line that runs the full
umbilical" is false — `SCLK` and `CS` run it too, and `SCLK` is the fastest edge.

**Stale — `hardware/module/digital-and-supervision.md`, *Still open* list:**
> "- **`SCLK` has no series resistor and `MOSI` does.** That is the wrong way
> round: `SCLK` is the fastest edge on the cable. Series resistors now go on all
> three lines at the driving end…"

This is listed as *open* while stating its own resolution, and the resolution
already shipped as a BOM row. It should be struck or moved to a changelog.

---

## F6. How many `J-CHAIN` connectors — 8, 5, or 4 — **HIGH**

**Current — eight, across five boards (4 documents agree):**

`hardware/bom.csv` `J-CHAIN`, **qty 8**:
> "**EIGHT of them, not five**: the chain is four hops and SER/QH are
> point-to-point rather than bus … Carrier 1, right_thumb 2, right_hand 2,
> left_thumb 2, left_hand 1, with four ribbon assemblies between."

`docs/decisions/0001-mcu-and-board-partitioning.md:251-255`, `carrier.md:416-421`,
`cluster-boards.md:230-235` and its component table (LH 1, LT 2, RH 2, RT 2 = 7,
"plus one more `J-CHAIN` on the carrier, **eight in all**") all agree.

**Stale — `hardware/bom.csv` `WIRE-LOOM`, the row that is supposed to buy the
ribbon:**
> "TWELVE conductors per hop, chained through each cluster board in turn rather
> than starred, so **five connectors must match**: one on the carrier and one per
> cluster board."

The BOM disagrees with itself: `J-CHAIN` says eight, `WIRE-LOOM` says five. This
matters because `WIRE-LOOM` is the row that buys the ribbon assemblies — at five
it buys four too few mating ends.

**Stale — "four connectors" in two places**, which understates the mating
interfaces by 2×:

`docs/decisions/0001-mcu-and-board-partitioning.md:372-374`
> "**1 MHz is the design rate and the chain should not be pushed much past it**:
> it now crosses **four connectors** and ~265 mm of loom"

`hardware/controller/carrier.md:571-573`
> "**1 MHz, and not much more** — the chain crosses **four connectors** and
> ~265 mm of loom"

A signal from the carrier to `left_hand` crosses four ribbon assemblies = **eight
mating interfaces**. The lumped-load argument that justifies 74HC and 1 MHz is
being made against half the real contact count.

**Related, same fact:** `ADR 0001:136` prices hand-termination at "**~4
connectors**" and `PCB-CLUSTER`'s note repeats "~4 connectors of hand work". The
real count is 8 board headers plus 8 IDC socket terminations on 4 ribbon
assemblies.

---

## F7. The `J-CHAIN` mating sockets and the ribbon assemblies have no BOM row — **HIGH**

`J-CHAIN` (qty 8) is `"2x6 2.54mm IDC boxed header, keyed"`, `THROUGH-HOLE,
shrouded` — those are the **board-mounted headers only**.

The four ribbon assemblies each need **two 2×6 IDC female sockets** and a length
of 12-way ribbon. That is **8 sockets and ~4 cut lengths**, and no row in
`hardware/bom.csv` supplies them. The refdes list contains no `J-CHAIN-SKT`, no
socket row, and no ribbon row other than `WIRE-LOOM` (see F15), whose part field
is `"Ribbon, ground per signal - chained cluster to cluster"` at **qty 1**.

Both documents that describe the assemblies say they exist —
`bom.csv` `J-CHAIN`: "with **four ribbon assemblies** between";
`ADR 0001:254`: "with four ribbon assemblies between them" — and nothing buys
them.

---

## F8. `DIG_GND` — no origin at the instrument end, and a live dispute at the module end — **HIGH**

### 8a. At the instrument end, `DIG_GND` exists only as a pin label

Every occurrence of `DIG_GND` on the instrument side:

- `hardware/controller/carrier.md:51` — the (stale) block-diagram pin list
- `hardware/controller/carrier.md:534` — `J-UMB pin 8 ──┘ DIG_GND` in §4
- `hardware/controller/carrier.md:410` — `[U-TVS-CHAIN 4-ch array to DIG_GND]`

**Nothing connects it.** §1 Power entry draws only a `PWR_GND` pour:
> ` J-UMB pin 6 PWR_GND ┴──────────────────────┴──── PWR_GND pour`

There is no `DIG_GND` pour, no tie to `PWR_GND`, and no statement of where the
SPI return current originates on the carrier. Pin 8 is drawn as a dangling label
on a conductor whose whole purpose (ADR 0004's swap) is to be the **return for
`CS`**.

### 8b. `U-TVS-CHAIN` and `U-TVS-SPI` reference different grounds

`carrier.md:410` — `U-TVS-CHAIN` clamps the key chain "**to `DIG_GND`**".
`carrier.md:536` and `bom.csv` `U-TVS-SPI` — the umbilical's SPI lines clamp "**to
`PWR_GND`**".

So the ESD array on the loom that never leaves the instrument is referenced to a
net that only exists on the cable, while the array on the cable is referenced to
the net that does exist. One of these two is wrong; neither page says which.

### 8c. At the module end, ADR 0004 and `power-entry.md` directly contradict

`docs/decisions/0004-cv-interface-module.md:568` (Status: **Accepted**):
> "- **`DIG_GND` likewise** — its own path to the star."

`hardware/module/power-entry.md:254-257`:
> "**`DIG_GND` is *not* given its own path to the star**, which **an earlier
> revision of ADR 0004** asked for: a 2 MHz SPI return wants the pour directly
> under its trace, and routing it to a distant star point is the classic
> split-plane mistake."

`power-entry.md` says the requirement belongs to "an earlier revision". **The
current revision still states it**, at line 568 and again in the return table at
line 550. And the ROADMAP sides with the ADR:

`ROADMAP.md:53` (E12):
> "**Ground laid out to the star rule in ADR 0004** — one origin at the power
> inlet, **`PWR_GND` and `DIG_GND` each on their own copper**, `AGND` not a return
> at all."

Two against one, and the one is the schematic page the board gets laid out from.
E12 cannot be passed as written, because its acceptance criterion contradicts the
drawing it is validating.

---

## F9. Cable shield and etherCON shell bonding — no policy exists — **HIGH**

The module page flags this itself and nothing answers it.

`hardware/module/power-entry.md:77-89`:
> | **The cable shield, if the etherCON shell bonds to the 10HP panel** | **~7 cents** |
> …
> "All three are **breath-correlated**, because they are driven by the
> instrument's own supply current. `pitch-stage.md` puts the entire pitch error
> budget at **0.42 cents**. …
> Not fixed here. It is a grounding and shield-bonding decision, and **the shield
> policy is sixteen words in the whole repo**."

The sixteen words are `docs/decisions/0004-cv-interface-module.md:713-716`:
> "- **Shielded (STP/FTP) preferred.** Twisted pairs are what make the analog
> breath channel survive (ADR 0003) and any Cat5e has those, but the shield is
> free at this price and the breath pair is the one signal with no digital margin
> to spare."

That is a **buying** preference. It says nothing about:

- whether the shield is bonded at one end, both ends, or neither;
- whether `J-UMBILICAL`'s shell is isolated from or bonded to the 10HP panel;
- whether the instrument-end shell bonds to the backing plate (which
  `MECH-GNDBOND` ties to `PWR_GND`), creating a second `PWR_GND` return path in
  parallel with pin 6 — which is precisely the ~7-cent mechanism;
- which etherCON variant is shielded. `bom.csv` `J-UMBILICAL` says
  "**Neutrik etherCON D-series chassis (variant TBD)**", and ADR 0004's *Open*
  section defers the variant to E12/M7 on feedthrough-vs-solder-tag grounds only
  — shielding is not among the criteria listed.

**Also a spec contradiction:** the BOM makes shielding **mandatory** in the part
field — `"Cat5e STP patch lead, STRANDED, ~2m"` — while its own note and ADR 0004
both say "**Shielded preferred**". If a bonding policy is ever written, a
UTP-is-acceptable reading of the cable spec breaks it.

This is a **High** rather than a Medium because the error it admits (~7 cents,
breath-correlated) is 17× the module's entire stated pitch error budget, and it
is settled by two decisions that cost nothing now — a shell washer and a cable
spec — and cannot be changed after the panel is cut and the body is bonded.

---

## F10. No cable-side etherCON shell in the BOM — **HIGH**

ADR 0004's entire case for the connector is the **cable-end** hardware:

`docs/decisions/0004-cv-interface-module.md:593-599`:
> "Bare 8P8C was rejected early — the retention tab is the most-broken connector
> in the industry and **it has no strain relief**. That matters here … because
> **the instrument moves constantly while being played** and the cable flexes at
> the connector every time. … **etherCON is an RJ45 inside a latching metal
> shell**, which keeps the electrical standard and replaces the failure mode."

But the BOM buys only the two chassis connectors:

`hardware/bom.csv` `J-UMBILICAL`, qty 2:
> `Neutrik etherCON D-series chassis (variant TBD)` · `panel mount`
> "8-conductor ruggedised connector, module panel and instrument tail"

…and the cable is specified as a plain patch lead:

`hardware/bom.csv` `CABLE-UMB`, package field: **`RJ45 both ends`**
`docs/decisions/0004-cv-interface-module.md:615`: "| Cable | **any Cat5e patch lead** |"

A bare RJ45 plug mates with an etherCON chassis jack electrically, but it gets
**no latch and no strain relief** — which is the exact failure mode ADR 0004
rejected 8P8C for. Getting the shell requires a cable-carrier part (NE8MC class)
fitted to each lead, and that part appears nowhere: no BOM row, no mention in ADR
0004, ADR 0009 or the ROADMAP.

This also collides with the consumable policy — "Keep spares. Replace the lead at
the first sign of intermittency" — because a shelled lead is an assembly step,
not a drawer item.

**Either** buy cable-carrier shells (and say so in `CABLE-UMB`, and note the
assembly step in the consumable policy), **or** record that the latch is
deliberately given up and the connector is being bought for its panel hardware
only — in which case the paragraph at 593-599 is the justification that has to
change.

---

## F11. `J-DISP` has no BOM row, and neither does the display board's connector — **HIGH**

The 11 → 9 change landed cleanly in prose. The **part** never existed.

**Current, and internally consistent** — `hardware/controller/carrier.md:679-694`:
```
  J-DISP  ──  9 conductors, 360 mm, up a side channel

    5 V (or +12 V — see Still open)        1
    GND                                     1
    IO5 → display RX, IO6 ← display TX      2      UART1, 921600 baud
    U0TXD                                   1  ┐  service, per ADR 0009
    U0RXD                                   1  │  and firmware/README.md
    GND                                     1  ┘
    two spare conductors (ADR 0009)         2
```
…matching the component table at `:783`:
> | **`J-DISP`** | **9-way** | **Proposed — see §6. Was 11-way before `EN`/`IO0` were withdrawn** | proposed |

**There is no `J-DISP` row in `hardware/bom.csv`.** The refdes list runs
`…J-CV, J-UMBILICAL, J-USB, J-PWR-EURO, J-CHAIN…` and contains no display
connector, no 9-way header, and no 360 mm loom part.

**Nor is there anything at the far end.** The display board is 360 mm away and,
per `carrier.md:26-34`, is explicitly *not* socketed on the carrier — so the loom
has to terminate on the T-Display-S3 AMOLED. Nothing in the BOM provides that
connector or socket. `HDR-DEV` (see F20) budgets strips for it, on the board it
is not mounted on.

**Consequence:** the loom that carries the inter-MCU UART, the display board's
only console path, and its power has zero purchasable parts at either end.

---

## F12. LED connectors — no BOM row, 6-vs-8 conductors, 220 Ω vs 330 Ω, spare gates — **HIGH**

Four disputes on one loom.

### 12a. `J-LED-L` / `J-LED-R` have no BOM row

`hardware/controller/carrier.md:782`:
> | **`J-LED-L/-R`** | **4-way each** | **Proposed — 12 V, GND, DI, BI** | proposed |

No such row exists in `hardware/bom.csv`. The two strip feeds, which also carry
the `C-STRIP-BULK` 470–1000 µF reservoirs, connect to the carrier through parts
nobody has bought.

### 12b. `R-LED-SER` value — 220 Ω drawn, 330 Ω specified

`hardware/controller/carrier.md:612-618`:
```
        └──►│ 74AHCT125 gate A ├──[R-LED-SER 220R]── J-LED-L  DI   ** R PROPOSED **
        └──►│ 74AHCT125 gate B ├──[R-LED-SER 220R]── J-LED-L  BI   ** IF NEEDED **
        └──►│ gate C ├──[220R]── J-LED-R DI
        └──►│ gate D ├──[220R]── J-LED-R BI
```
`hardware/controller/carrier.md:653-654`:
> "**`R-LED-SER` is proposed** … 100–330 Ω at the buffer."
`hardware/controller/carrier.md:772`:
> | **`R-LED-SER`** ×2–4 | **100–330 Ω** | **Proposed …** | proposed |

against

`hardware/bom.csv` `R-LED-SER`: **`330R 1%`, qty 4**, status `candidate`:
> "**FOUR not two**: the WS2815's BACKUP data line is cited as a reason for the
> part choice in ADR 0014 and again in ADR 0005, and **was connected to nothing**
> — the level shifter's two spare gates are exactly what it needs"

The BOM has decided: four parts, 330 Ω, `BI` driven. The drawing still says
"proposed", "220R", "×2–4", "100–330 Ω" and "IF NEEDED".

### 12c. `U-LVLSHIFT` — two spare gates, or none

`hardware/bom.csv` `U-LVLSHIFT`:
> "SOIC-14. 5V rail TTL thresholds so 3V3 reads high. **Two spare gates.**
> VERIFY WS2815 threshold"

`hardware/bom.csv` `R-LED-SER`:
> "…**the level shifter's two spare gates are exactly what it needs**"

Both rows are in the same file. If `R-LED-SER` is qty 4, the spare gates are
consumed and `U-LVLSHIFT`'s note is wrong. `carrier.md:648-651` states the
consequence explicitly and leaves it open:
> "If so, **all four gates are used, none spare**, against the BOM's 'Two spare
> gates' `[repo] bom.csv`, and **the LED loom is 8 conductors rather than 6**."

### 12d. LED loom conductor count — 6, 8, or "6–8"

`hardware/controller/carrier.md:803` (the loom table):
> | WS2815: 12 V, GND, `DI` per strip (+`BI` if needed) | **6–8** |

`hardware/controller/carrier.md:782` (component table, same page):
> | **`J-LED-L/-R`** | **4-way each** | 12 V, GND, DI, BI |

4-way each is **8**, not "6–8". And with `R-LED-SER` at qty 4 the BOM has
already chosen 8. The loom total (F14) is therefore **30**, not "~28–30".

---

## F13. Five new BOM rows are still drawn as "proposed" or "not in the BOM" — **HIGH**

`F-CHAIN`, `U-TVS-CHAIN`, `R-CHAIN-SER`, `LK-SER` and `R-SER-TERM` all landed as
BOM rows on 2026-09-21. The schematics that asked for them still say they do not
exist.

`hardware/bom.csv`:
> `F-CHAIN` · 100mA polyfuse · qty 1 · "**PROPOSED by carrier.md and never given a row until 2026-09-21.**"
> `U-TVS-CHAIN` · 4-channel TVS array · qty 1 · same wording
> `R-CHAIN-SER` · 100R 1% · qty 3 · "**PROPOSED by cluster-boards.md and carrier.md and never given a row until 2026-09-21.**"
> `LK-SER` · 3-pad solder link · qty 4 · "PROPOSED by hardware/controller/cluster-boards.md."
> `R-SER-TERM` · 10k 0805 · qty 1 · "PROPOSED by hardware/controller/cluster-boards.md."

**Stale, `hardware/controller/carrier.md`:**

`:398`, `:400`, `:402` — `** R PROPOSED **` on all three `R-CHAIN-SER`
`:410` — `[U-TVS-CHAIN 4-ch array to DIG_GND]   ** PROPOSED **`
`:477-481`:
> "**3. `F-CHAIN`, or not.** … A 100 mA polyfuse or a 0603 fuse is two millimetres
> of board. **Proposed, not in the BOM.**"

`:755`, `:757`, `:759` — component table, all three marked `proposed`, under the
heading "**proposed** rows are new to this page and **have no BOM entry yet**".

`:855-859` — *Still open*, listed as an undecided item:
> "- **`F-CHAIN`** (§3): whether the 3V3 conductor going down the body is fused.
> Two millimetres of board, unretrofittable…"

**Stale, `hardware/controller/cluster-boards.md`** component table:
> | **`LK-SER`** | **3-pad solder link** | … | **Proposed — position B only on the chain-end board** |
> | **`R-SER-TERM`** | **10 kΩ 0805** | … | **Proposed — chain-end board only…** |

**Why High:** `F-CHAIN` and `U-TVS-CHAIN` are both called unretrofittable by
their own BOM rows, and `carrier.md` still lists `F-CHAIN` as an *open decision*.
A layout done from `carrier.md` leaves out three parts the BOM will ship.

---

## F14. Total loom conductor count — ~28–30, and the "~23" it refutes exists nowhere — **HIGH**

`hardware/controller/carrier.md:790-814` is the only conductor-count table in the
corpus. Its arithmetic is sound (12 + 6–8 + 9 + 1 = 28–30), but the paragraph
that reconciles it cites three documents that do not say what it says:

`hardware/controller/carrier.md:790-792`:
> "`[calc]`, built from the repo's own rules — **not** the '**~23**' that
> **ADR 0001, `WIRE-LOOM` and the ROADMAP all carry** `[repo]`"

`hardware/controller/carrier.md:808-813`:
> "**The first draft of this table said ~53 and called the repo's '~23' wrong.**
> `[repo] 0001, WIRE-LOOM, ROADMAP` … **On the per-cluster topology the repo's
> figure is approximately right after all**, and this page withdraws the
> objection. **~28–30 against ~23**; the gap is the spare conductors and the
> display loom's console pair, not a counting error."

**The figure "~23" appears in none of the three cited sources.** Searched:
`docs/decisions/0001-mcu-and-board-partitioning.md`, `hardware/bom.csv`
`WIRE-LOOM`, and `ROADMAP.md` — no conductor total of any kind. `WIRE-LOOM` gives
"TWELVE conductors per hop"; ADR 0001 gives "12 per hop"; the ROADMAP gives "Six
conductors per hop" (F2). None gives a system total.

So: the corpus has **one** loom total (~28–30, and it should be 30 per F12d), and
a paragraph declaring agreement with a figure nobody carries. Either "~23" was
edited out of the three documents without updating `carrier.md`, or the citation
was never checked. In either case the reconciliation is unverifiable, and the
conclusion it reaches ("the repo's figure is approximately right after all") is
load-bearing for the side-channel width argument.

The three historical figures the task names — ~23, ~53, ~28–30 — reduce to:
**~53** survives only as this paragraph's description of a withdrawn draft;
**~23** survives only as this paragraph's citation; **~28–30** is the live number
and appears exactly once.

---

## F15. `WIRE-LOOM` — one qty-1 row for four physically different harnesses — **HIGH**

`hardware/bom.csv` `WIRE-LOOM`, **qty 1**, status `open`:

> part: `"Ribbon, ground per signal - chained cluster to cluster"`
> package: `n/a`
> description: `"Internal looms: key chain, LED power and data, UART, power"`
> notes: "DECIDED 2026-09-21: J-CHAIN is a 2x6 IDC on a 12-way ribbon, alternating
> ground … TWELVE conductors per hop … so **five connectors must match** …"

One row, quantity one, covers:

| Harness | Count | Conductors | Length | Source of truth |
|---|---|---|---|---|
| Key chain ribbon assemblies | **4** | 12-way IDC | hop-to-hop, ~265 mm total | `J-CHAIN`, `carrier.md §3` |
| LED power + data, left and right | **2** | 4-way (F12) | ~420 mm each | `carrier.md §5`, no BOM row |
| Display loom (`J-DISP`) | **1** | 9-way | 360 mm | `carrier.md §6`, no BOM row |
| Plate ground bond | 1 | 1 | — | `MECH-GNDBOND` (has its own row) |

Four physically different harnesses, three different termination styles, three
different conductor counts, and one of them is four separate assemblies. The row
also carries the **stale five-connector figure** (F6) and describes only the key
chain in its part field.

**Consequence:** a purchaser cannot buy from this row, and it is the only row
that could supply the ribbon for the four chain assemblies (F7) and the
conductors for `J-DISP` and `J-LED` (F11, F12a).

---

## F16. Chain `SER` source pin `IO33` — spare, or driving the loom — **HIGH**

`carrier.md` drives `J-CHAIN` pin 6 from `IO33`, `R-CHAIN-SER` (qty 3) is a BOM
row covering `SER`, and `R-SER-TERM`'s BOM note names the pin. **ADR 0007's pin
table still lists `IO33` as spare, and the BOM still says the board breaks out
16 GPIO, not 17.**

`hardware/controller/carrier.md:402`:
```
   IO33  SER out  ──[R-CHAIN-SER 100R]─────►  6  SER     (into the far device)
```

`hardware/bom.csv` `R-SER-TERM`:
> "If firmware instead **DRIVES it from the carrier's IO33**, the 100R series wins
> against 10k to within 33mV of the rail"

`hardware/bom.csv` `R-CHAIN-SER`: qty **3** — "Series damping at the chain driving
end on **SCK, SH/LD and SER**" — so a part has been bought for the `SER` driver.

**Against:**

`docs/decisions/0007-imu-selection.md:190-192`:
> | **Used** | **14 of 17** | **spare: 3, 4, 33** |

`hardware/bom.csv` `U-MCU-RT`:
> "**16 GPIO broken out (1-7, 34-40, 43, 44)** vs 14 needed"

The BOM's list omits GPIO33 entirely — which is the exact error ADR 0007 says it
already fixed:

`docs/decisions/0007-imu-selection.md:180-182`:
> "**Seventeen, not sixteen** — an earlier revision of this list omitted GPIO33
> and the error propagated into ADR 0013 and the roadmap."

ADR 0013 and `ROADMAP.md:188` ("17 broken out, three spare") were corrected. The
**BOM was not**, and ADR 0007's own assignment table was not updated for the pin
it now uses.

**Consequence:** as the BOM reads, the conductor on `J-CHAIN` pin 6 has no driver
pin, and the third `R-CHAIN-SER` has nothing to connect to. `carrier.md:423-429`
compounds it by calling the drive "**NOT yet decided**" while the BOM has already
bought the resistor and `cluster-boards.md` has designed `LK-SER` position B
around it.

---

## F17. `HDR-SERVICE` — 2×3 or 2×5 — **MEDIUM**

The 2×5 → 2×3 change landed in three places and was missed once, in the same file
as one of the correct copies.

**Current:** `hardware/bom.csv` `HDR-SERVICE` — `2x3 2.54mm pin header`, "SIX
pins, not ten"; `docs/decisions/0009-enclosure-construction.md:303-305` — "over a
**six-pin** header on the carrier"; `hardware/controller/carrier.md:673` —
"**`HDR-SERVICE` is therefore 2×3, six pins, not 2×5**".

**Stale** — `hardware/controller/carrier.md:870-873`, in *Still open*:
> "ADR 0003 wants a replaceable wear part and a trap 'clearable without
> disassembly'; **ADR 0009 gives a 12 × 40 mm cover over a 2×5 header**. Those do
> not meet."

The cover is 12 × 40 mm over a **2×3**. The argument still stands (a 2×3 is
smaller, so the sensor-access objection is if anything stronger), but the figure
is the withdrawn one.

---

## F18. SPI clock over the umbilical — ~1 MHz or 2 MHz — **MEDIUM**

`docs/decisions/0004-cv-interface-module.md:84`, in the "Revised conductor
budget":
> `SCLK      / DIG_GND     SPI to the DAC, ~1 MHz`

against, in the same ADR at line 37:
> `SCLK, MOSI, CS      SPI to the DAC, ~2 MHz`

and at line 53:
> | **Breath analog, 6 channels at 4 kHz** | **0.77 Mbit/s** | **≥1.5 MHz → specify 2 MHz** |

and `ROADMAP.md:52` (E11): "SPI **at 2 MHz** (not the stale 0.6 MHz…)";
`docs/reference/latency-budget.md:62`, `:125`; `hardware/controller/carrier.md:565-573`.

Everything says 2 MHz except the conductor budget block, which says ~1 MHz. Same
block as F1's stale pairing — the whole block is pre-revision and is not marked
as such.

---

## F19. `R-CHAIN-SER` is fitted, but ADR 0001 deleted driving-end series resistors — **MEDIUM**

`hardware/bom.csv` `R-CHAIN-SER`, qty 3, `100R 1%`, and drawn on three lines in
`carrier.md §3`. Its note anticipates the objection:
> "Edge-rate damping at the source, which is a **DIFFERENT job** from the
> `R-TERM-CHAIN` that ADR 0001 deleted - that was series TERMINATION, wrong for a
> line dropping on four boards. Same 100R as R-SPI-SER"

But ADR 0001 itself never records that distinction, and twice makes driving-end
resistors conditional:

`docs/decisions/0001-mcu-and-board-partitioning.md:182-186`:
> "**So `R-TERM-CHAIN` is not restored.** … With HC there is nothing to terminate.
> **If E4 says otherwise, series resistors at the driving end are the fallback**
> and LVC is the other way to go."

`docs/decisions/0001-mcu-and-board-partitioning.md:280-286` (fix 4, struck
through):
> "~~**33–68 Ω series termination at the MCU** on the clock and latch lines.~~
> **Deleted, for two independent reasons.**"

So ADR 0001 says "nothing to terminate, fallback only if E4 disagrees", and the
BOM ships the part unconditionally. The BOM is probably right (damping ≠
termination), but the ADR has not been told, and E4 is now testing a chain that
already has the fallback fitted — which changes what a pass at E4 means.

---

## F20. `HDR-DEV` quantity — six strips, or one board's worth — **MEDIUM**

`hardware/bom.csv` `HDR-DEV`, **qty 6**:
> "Cut to length: **2 strips for the ESP32-S3-Matrix, 2 for the T-Display-S3
> AMOLED**, 2 spare. SOCKETS not solder-down"

`hardware/controller/carrier.md:26-34` and `:753`:
> "`HDR-DEV` in the BOM budgets header strips for both. **The display board is
> 360 mm away at the top of the instrument** … It reaches this board through a
> loom, not a socket. This page therefore draws **one** dev-board socket pair"
> | `HDR-DEV` | 2 × 10-way machined socket | **Qty is one board's worth, not two** — the display board is 360 mm away |

The BOM budgets sockets for a board that is not mounted on the carrier. Two of
the six strips are for a connector that does not exist, while the connector that
*does* need to exist — the display end of `J-DISP` — has no row at all (F11).

---

## F21. Which board the instrument end of the cable lands on — **MEDIUM**

`hardware/module/breath-receive-stage.md:20`, the header of the link drawing:
```
  INSTRUMENT (bottom cluster board)                 |  2 m Cat5  |   MODULE
```

`docs/decisions/0003-breath-sensing-path.md:649`:
> "**The star point is the analog ground pour on the bottom cluster board**, at the…"

against `hardware/controller/carrier.md:288-292`:
> "**1. The analog star point is on this board, and `AGND` is sense-only.**
> ADR 0003 names the star point as 'the analog ground pour on the **bottom cluster
> board**' `[repo] 0003` — **a board that does not exist; it means this one.**"

`AGND` is one of the eight conductors and its star point is the reference the
whole 2 m analog run is sensed against. Two corpus documents still place it on a
board the topology deleted. `carrier.md` notes the error rather than fixing it at
source, which is precisely how this recurs.

Same file, `cluster-boards.md` confirms there is no "bottom" board: the two
thumb clusters share `PLATE-THUMB` but are two separate boards, split by the
U-bolt, and neither carries analog.

---

## F22. ADR 0001's own per-hop arithmetic does not add to 12 — **MEDIUM**

`docs/decisions/0001-mcu-and-board-partitioning.md:134-136`:
> | Conductors down the body | **12 per hop** — **6 signals-and-supply, 5 grounds, 2 spare** | 32–44 |

6 + 5 + 2 = **13**, not 12.

The correct decomposition, from the same ADR's own pinout at line 249
(`GND SCK GND SH/LD GND SER GND QH GND 3V3 spare spare`), is **5**
signals-and-supply (`SCK`, `SH/LD`, `SER`, `QH`, `3V3`) + 5 grounds + 2 spare = 12.
`carrier.md:392` gets it right — "Four signals, five grounds, one supply" — and
the two pages disagree by one conductor.

---

## F23. ADR 0005's power tree calls the chain's 3V3 load "microamps" — **MEDIUM**

`docs/decisions/0005-power-architecture.md:197-204`:
```
real-time board 3V3 out ──┬── 74HC165 chain
                          ├── breath ADC
                          └── I2C pull-ups
```
> "**3.3 V does not need its own converter.** The loads on it are the shift
> register chain (**microamps**), the ADC (milliamps) and pull-ups…"

against `docs/decisions/0001-mcu-and-board-partitioning.md:236-238`:
> "**25.8 mA is 4.4× the old figure** and it is drawn from the dev board's 3V3
> LDO, **down the loom**, as a play-rate step."

and `hardware/controller/carrier.md:445-451`, and `cluster-boards.md` §2
("**1.43 mA** per closed key; 18 closed = **25.8 mA** off the loom's 3V3").

The 3V3 conductor is pin 10 of `J-CHAIN` and is the one `F-CHAIN` (100 mA
polyfuse) protects. ADR 0005's power tree is the document that sizes rails, and
it is understating this load by three orders of magnitude. It also does not
mention `F-CHAIN` at all.

---

## F24. ROADMAP still prices the etherCON against an 8HP panel — **LOW**

`ROADMAP.md:53` (E12):
> "10HP panel cut, module assembled and racked. etherCON braced to the PCB —
> good practice **at 8HP** rather than the structural necessity it was at 6HP."

`ROADMAP.md:183` (1:1 paper fit check, M4):
> "The etherCON flange against a **50.50 mm 10HP panel** *and* against the
> 57 × 38 mm instrument tail … **Comfortable at 8HP**; the tail is now the tight
> one"

against `docs/decisions/0004-cv-interface-module.md:697-699`:
> "**Brace the connector to the PCB anyway.** … **At 10HP this is good practice**
> rather than a structural necessity."

Both ROADMAP rows say "10HP" in one clause and price the connector against 8HP in
the next. Harmless to the electrical design; it will mislead whoever runs the M4
paper check about how much margin the flange has.

---

## F25. ADR 0004's pre-revision cable budget still lists `MISO` and a spare — **LOW**

`docs/decisions/0004-cv-interface-module.md:33-44`:
```
### What goes over the cable

+12V, GND, GND      power (3.3V derived locally in the instrument, small buck)
SCLK, MOSI, CS      SPI to the DAC, ~2 MHz
MISO                unused today — module ID and presence detect
spare               reserved
```
> "With real Cat5/6 each signal sits against a ground in its own twisted pair."

This is superseded by "### Revised conductor budget" nine lines later, and by the
pin-assignment table at line 752 — but it is **not struck through and not
labelled**. Three of its four claims are now false: there are two power
conductors not three, `MISO` was deleted (`firmware/README.md:38-39`: "`MISO` was
deleted from the cable"), and there is no spare. The fourth claim — "each signal
sits against a ground in its own twisted pair" — is the one the same ADR later
demolishes at line 787-788:
> "This ADR also asserted twice that 'each signal sits against a ground in its own
> twisted pair'. **Its own table never did.**"

The ADR identifies the false sentence and leaves it standing.

---

## F26. `CABLE-UMB` spec: "two things are not optional", then three bullets — **LOW**

`docs/decisions/0004-cv-interface-module.md:705-719`:
> "### Cable specification, which is not 'any Ethernet cable'
> Close, but **two things** are not optional:
> - **Stranded patch cable, never solid-core installation cable.** …
> - **Shielded (STP/FTP) preferred.** …
> - **Straight-through, and this one is a hazard rather than a preference.** …"

Three bullets under "two things", and the middle one says "preferred" — i.e. it
*is* optional — while the BOM's part field makes STP mandatory (see F9). Also
note that the third bullet, straight-through, is the one that is **not** captured
in `CABLE-UMB`'s notes at all, which list stranded and shielded only.

---

# Part 2 — Facts asserted but never derived

## A1. "A reversed chain connector puts 3V3 into QH" — **the mechanism does not follow from the stated pinout**

Asserted in two corpus documents:

`hardware/bom.csv` `J-CHAIN`:
> "**BOXED AND KEYED because a reversed chain connector puts 3V3 into QH.**"

`hardware/controller/cluster-boards.md:211`:
> "Boxed and keyed at all eight positions, **because a reversed connector puts 3V3
> onto the `QH` net.**"

The pinout is `1 GND · 2 SCK · 3 GND · 4 SH/LD · 5 GND · 6 SER · 7 GND · 8 QH ·
9 GND · 10 3V3 · 11 spare · 12 spare`, on a 2×6 with the usual odd/even rows.
Work the three reversals through:

| Reversal | Mapping | Where 3V3 (pin 10) lands | Where QH (pin 8) lands |
|---|---|---|---|
| End-for-end (row-swapping, pin 1 ↔ pin 12) | rowA pos *k* ↔ rowB pos 7−*k* | pin 3 = **GND** | pin 5 = GND |
| Flipped about the long axis (odd ↔ adjacent even) | 1↔2, 3↔4, … | pin 9 = **GND** | pin 7 = GND |
| End-for-end within rows (1↔11, 2↔12) | rowA *k* ↔ rowA 7−*k* | pin 4 = **SH/LD** | pin 6 = SER |

Under none of the three does 3V3 reach `QH`. Under the two most likely ones it
reaches a **ground pin** — a dead short on the 3V3 conductor, which is a worse
outcome than the one stated and is precisely what `F-CHAIN` (100 mA polyfuse)
would then have to clear.

The conclusion (box and key it) is right. The reason given is not derived and
appears to be wrong, and it is repeated verbatim in two places — the shape this
project's failures take. Re-derive it, or state it as "any reversal shorts or
mis-drives the 3V3 conductor".

## A2. "Eight connectors have to match" — the mating sockets are never counted

`ADR 0001:251-255`, `bom.csv` `J-CHAIN` and `carrier.md:416-421` all derive
**8 board headers** correctly from "four hops, `SER`/`QH` point-to-point". None of
them takes the next step to **8 mating sockets on 4 ribbon assemblies**, which is
what actually has to be bought (F7) and hand-terminated. `ADR 0001:136`'s
"~4 connectors" of hand work is the figure that survives, and it is half of half.

## A3. The 100 Ω source-match figure is asserted against an unspecified cable

`bom.csv` `R-SPI-SER` and `carrier.md:548-563` both derive 100 Ω from "2m of Cat5
is a **100-ohm TRANSMISSION LINE**" and compute the far-end first step as
2.75 V. The 100 Ω differential characteristic impedance of Cat5e is a real
standard number — but the derivation is a **single-ended** source match into a
line whose single-ended impedance is not 100 Ω (it is roughly 50–60 Ω per
conductor to the pair's own reference, higher against a distant ground). No
document states which impedance the 100 Ω is matching, and the conclusion is
specified to 1 % tolerance. E11 is the stated gate; give it this question
explicitly.

## A4. "20 ns round trip" is used without stating the velocity factor

`bom.csv` `R-SPI-SER`, `carrier.md:549-551` and
`ADR 0004:764-766` all use "the 20 ns round trip" as the basis for calling the
crosstalk saturated and the line a transmission line. 2 m out-and-back at a
typical 0.65 c is ~20.5 ns, so the number is right — but the velocity factor
appears nowhere, and the figure is quoted in three documents as though it were
measured. One line would make it reproducible.

## A5. `DIG_GND` has no stated origin at the instrument end

See F8a. The net appears on three lines of `carrier.md` and is never tied to
anything. There is no derivation of where SPI return current enters the cable,
and `U-TVS-CHAIN` is referenced to it on a board where it does not exist.

## A6. The cable shield's ~7-cent contribution is asserted once and never modelled

`power-entry.md:79` puts "the cable shield, if the etherCON shell bonds to the
10HP panel" at "**~7 cents**" in a table whose other two rows are derived from
stated resistances (≈17 mΩ, 20–40 mΩ). The shield row has no resistance, no
current split and no reference. It is the row that argues for a shield policy
(F9), and it is the least derived of the three.

---

# Part 3 — Verified consistent

These were checked across every corpus document that mentions them and **agree**.
Listed so the next sweep does not re-do them.

**Umbilical pin map and pairing**
- `1 BREATH / 2 AGND` — `ADR 0004:755`, `carrier.md:181,199`,
  `breath-receive-stage.md:22,28`. Three drawings, one answer.
- `3 +12V / 6 PWR_GND` — `ADR 0004:756`, `carrier.md:85,106`, and the
  rollover-lead hazard analysis at `ADR 0004:722` ("3 and 6 are **+12 V and
  PWR_GND**"), which `D-REVSHUNT` is sized against. Consistent.
- The **new** map `4 SCLK / 5 MOSI`, `7 CS / 8 DIG_GND` — `ADR 0004:756-757`,
  `carrier.md:531-534`, `digital-and-supervision.md:23-29,83`. Three independent
  drawings agree (the two stale copies are F1).
- The swap's justification — 365–907 mV saturated intra-pair crosstalk, `CS`'s
  678 mV `V_IL` margin, 1.9:1 → 6200:1 — is quoted **identically** in
  `ADR 0004:764-768` and `digital-and-supervision.md:85-89`. Same figures, same
  reasoning, no drift.
- `SCLK`/`MOSI` pairing "safe by construction" (receiver samples `MOSI` only on a
  `SCLK` edge) — `ADR 0004:776-778`, `digital-and-supervision.md:99-102`.
- T568B pair groups `(1,2) (3,6) (4,5) (7,8)` — `ADR 0004:747-748`,
  `carrier.md:47`, `digital-and-supervision.md:25-26`.
- Eight conductors for eight signals — `ADR 0004:89,800`, `bom.csv`
  `J-UMBILICAL` ("8-conductor ruggedised connector"), `carrier.md:47,806`,
  `bom.csv` `D-TVS-PWR` ("six channels against eight conductors").
- `MISO` deleted from the cable — `ADR 0004:91`, `firmware/README.md:38-39`,
  `digital-and-supervision.md:93`, `carrier.md:537` ("MISO ── MCP3202 DOUT only
  (never leaves the board)"). Four documents, no survivals except the unmarked
  pre-revision block (F25).
- `AGND` carries no current and is an in-amp input, not a return — `ADR 0004:89,
  552, 573-576`, `ADR 0003:330-336`, `power-entry.md:257`, `carrier.md:294-296`,
  `bom.csv` `R-BIAS-INAMP`. Five documents, one rule, stated the same way.

**`R-SPI-SER`**
- Value, quantity and the full derivation are **identical** in `bom.csv`
  `R-SPI-SER` and `carrier.md:548-563`: 100 Ω, qty 3, 220 Ω gives 1.83–1.86 V
  against the 74AHCT125's 2.0 V `V_IH` with ~20 ns of dwell, 100 Ω gives 2.75 V
  and 33 mA, 68 Ω gives 48 mA against a 40 mA pad spec. No drift between the two.

**`U-TVS-SPI`**
- `SCLK`, `MOSI`, `CS` + one spare channel, to `PWR_GND`, SOT-23-6 — `bom.csv`
  and `carrier.md:536,769` agree, including the package-policy reason the old
  `U-TVS-UMB` part was rejected.

**`J-CHAIN` pinout**
- The twelve-position string `GND SCK GND SH/LD GND SER GND QH GND 3V3 spare
  spare` appears **verbatim and identical** in four places: `ADR 0001:249-250`,
  `bom.csv` `J-CHAIN`, `bom.csv` `WIRE-LOOM`, `cluster-boards.md:207-208`. It
  also matches `carrier.md:396-408`'s pin-by-pin drawing exactly, including which
  pins are grounds and that 3V3 sits against pin 9's ground.
- "Same pinout at all eight" / "Same 2×6 pinout at all eight" — `bom.csv`
  `J-CHAIN`, `carrier.md:421`.
- Per-board quantities reconcile: `cluster-boards.md` component table gives
  LH 1, LT 2, RH 2, RT 2 = 7, its totals line says "7 chain connectors — plus one
  more `J-CHAIN` on the carrier, **eight in all**", `bom.csv` qty is **8**, and
  `ADR 0001:254` and `carrier.md:417` both give "carrier 1, RT 2, RH 2, LT 2,
  LH 1". Four sources, same decomposition.
- Two spare conductors per ADR 0009's rule, free because IDC comes in 2×N —
  `ADR 0009:478`, `ADR 0001:257-258`, `bom.csv` `WIRE-LOOM`, `carrier.md:412-414`.

**`LK-SER` / `R-SER-TERM` behaviour** (the parts' *function*, not their
"proposed" status — see F13)
- Position A on the three boards with an OUT, position B on the chain-end board,
  `SER` from the IN pin 6 passthrough — `bom.csv` `LK-SER`,
  `cluster-boards.md:218-226`, and the component table's `B / A / A / A` row.
- The 100 Ω-beats-10 kΩ divider arithmetic ("within 33 mV of the rail") is
  identical in `bom.csv` `R-SER-TERM` and `cluster-boards.md:253-257`.

**`HDR-SERVICE` and the display loom**
- 2×3, six pins, `U0TXD`/`U0RXD`/`GND` per board — `bom.csv`, `ADR 0009:303-305`,
  `carrier.md:673-676,696-698` (one stale survival, F17).
- `EN` and `IO0` unavailable, with the same evidence (vendor board definition,
  3 power + 17 GPIO, `IO0` under the BOOT button, `EN` on the reset circuit) in
  `bom.csv` `HDR-SERVICE`, `ADR 0009:307-311` and `carrier.md:663-671`. Three
  documents, same reasoning, same conclusion.
- The three-line recovery ladder (OTA rollback → USB-Serial-JTAG through the tail
  slot → this header; corrupted bootloader ends the instrument, accepted) —
  `bom.csv`, `ADR 0009:315-334`, `carrier.md:673-677`.
- `J-DISP` = 9 conductors: the itemised list at `carrier.md:682-692` sums to
  exactly 9, matches the component table at `:783` and the loom table at `:804`.
  Internally consistent (the missing BOM row is F11).
- `U0TXD`=`IO43`, `U0RXD`=`IO44`, UART1 on `IO5`/`IO6` — `ADR 0007:192-196`,
  `ADR 0013:49-50`, `carrier.md:686,697`.
- 921600 baud on the inter-MCU link — `ADR 0013:97,188`, `carrier.md:686`.
- ADR 0013's "four broken-out pins" is about the display board's *pin*
  requirement, not the loom; `carrier.md:700-703` states the distinction
  explicitly and the two do not conflict.

**Connector mechanics**
- etherCON D: 23.8 mm cutout, 50.50 mm 10HP panel, 13.35 mm aluminium each side
  (was 8.27 mm at 8HP) — `bom.csv` `J-UMBILICAL`, `ADR 0004:608-613,682`.
- 4 mm maximum panel thickness, so the instrument end mounts to an internal
  backing plate and not through 6 mm oak — `bom.csv` `J-UMBILICAL`,
  `ADR 0004:701-703`, `ADR 0009:287-295`. Three documents agree.
- The etherCON variant (feedthrough vs solder-tag vs PCB-mount) is open at both
  ends, deferred to E12/M7 — `bom.csv`, `ADR 0004:810-817`, `carrier.md:875-878`.
  Consistently open, not contradictory.

**Cable policy**
- Stranded, never solid-core, because this cable's whole life is flexing —
  `ADR 0004:709-712`, `bom.csv` `CABLE-UMB`. Same reason, same words. (The
  *gauge* is F3.)
- The cable is a consumable; keep spares; replace at the first intermittency —
  `ADR 0004:596,632-633`, `bom.csv` `CABLE-UMB`, and `ADR 0004:409-412`'s
  acceptance of the lost far-end diagnosis on that basis.
- Rollover and crossover lead hazards, and `D-REVSHUNT` at the connector ahead of
  `L-BUCK-IN` — `ADR 0004:721-743`, `carrier.md:85,108-112,775`. The diode's
  placement rationale ("an inductor between the fault and the diode is the wrong
  way round") appears only in `carrier.md` but does not conflict with anything.

**Analog pair, instrument end**
- `R-SER-BREATH-INST` qty 2 — `R1` in the `BREATH` leg and `R1b` in the `AGND`
  leg — is now drawn on **both** `carrier.md:181,199` and
  `breath-receive-stage.md:22,28`, and the BOM row's qty 2 / 1206 / 250 mW spec
  matches. This was a prior-sweep finding and it has been closed.
- `D-TVS-BREATH` ×2 at 12 V standoff on both legs, at the connector — `bom.csv`,
  `carrier.md:183,203,766`.
- No band-limit capacitor at the instrument end; the whole 500 Hz filter is at
  the receive end ahead of the in-amp — `carrier.md:298-304`,
  `breath-receive-stage.md:39-45`, `bom.csv` `C-FILT-BREATH`,
  `bom.csv` `R-SER-BREATH-INST`. Four sources, consistent, and the ADR 0003
  supersession is stated in both places.
- The 482 Hz differential pole (not 531 Hz, because `R1b` makes both legs 11 kΩ)
  is consistent in `breath-receive-stage.md:160`, `bom.csv` `C-FILT-BREATH` and
  `docs/reference/latency-budget.md:42`.

**Chain topology**
- Chained, not starred; order `right_thumb → right_hand → left_thumb → left_hand`;
  bit 0 is the first bit clocked out = the device nearest the MCU — `ADR 0001:290-300`,
  `config/key-layout.yaml:102-121`, `carrier.md:437-440`,
  `cluster-boards.md:57-62`. The proposed `RT → RH → LH → LT` reorder is flagged
  as *proposed, not applied* in `cluster-boards.md` and is not asserted anywhere
  as current.
- `CLK INH` tied low and `QH_bar` left open at all four devices —
  `ADR 0001:294-296`, `cluster-boards.md:103-105`, `carrier.md:431-432`.
- `SER`/`QH` are point-to-point, not a bus, and pin 8 carries a different net on
  each side of a board — `cluster-boards.md:230-235`, `carrier.md:416-421`,
  `ADR 0001:252-254`.

---

# Part 4 — Spotted in passing, outside this report's fact domain

Not investigated, not ranked, and listed only so they are not lost. Another
agent's domain.

1. **`config/key-layout.yaml`** — the prose comment says "**The 5 genuinely free
   bits** are FLOATING CMOS INPUTS and must be pulled" while the machine-readable
   key eight lines below says `spare_bits_free: 3`. Same file.
2. **`ADR 0001:294-296` fix 6** — "**The five genuinely free spare bits** are
   floating CMOS inputs", against 3 everywhere else (`key-layout.yaml`,
   `cluster-boards.md §4`, `bom.csv` `R-KEY-PU` "the 3 genuinely free bits (22,
   23, 31)").
3. **`carrier.md:508-510`** — "**Which six bits** carry the marker and to what
   pattern is still undecided", and `:864` "The **marker pattern** (which six
   bits, to what levels)" — against the 8-bit marker decided 2026-09-21 and shown
   in that page's own table at `:496`.
4. **`ADR 0009:474-476`** — "**10 kΩ, 100 Ω and 10 nF** per switch position on the
   cluster boards" against `R-KEY-PU` 2k2 / `R-KEY-SER` 100R / `C-KEY` 47nF.
5. **`ADR 0004:586`** — "Roughly **107 mm of ~110 mm** usable height — full but
   workable", against the same ADR's derived **97 mm** at `:668` and its own
   statement at `:678-680` that the 107 mm figure "is asserted twice and derived
   nowhere".
6. **`ADR 0006:562`** — the shared-1N5817 effect at "**~20 cents**", against
   `power-entry.md:53-61`'s recomputation at **0.00018 cents** and its warning
   that "left as it was, the next reviewer who checks the arithmetic deletes the
   part".
7. **`bom.csv` `PCB-MODULE`** — the description field still reads "DAC, scaling,
   jacks, power entry, load switch, **watchdog**"; the row's own notes say
   "'watchdog' in this row's description is stale - that part is DELETED". The
   note was added; the description was not changed.
8. **`digital-and-supervision.md` *Still open*** — four of its seven bullets are
   about the deleted 74HC123 watchdog and the deleted LM311 presence comparator
   ("a corrected `R-PRESENCE` row", "A power-on reset RC on the '123's own
   `CLR`", "The retrigger question…", "The threshold may sit inside the breath
   signal's own range"). The page's body deletes both parts; its open list still
   maintains them.

---

## What I would fix first

1. **F1** — `carrier.md:50-51` and `ADR 0004:84-85`. Two lines. The pin map is
   copper at both ends and the stale copies are the summary views.
2. **F4** — decide the cable-side `CS` pull rail. As written the BOM specifies a
   rail the module does not have, on the resistor that protects the one digital
   failure that does not self-heal.
3. **F3** — put an AWG in `CABLE-UMB` and say once, in one place, whether
   0.168 Ω is the number being designed to. Five derivations depend on it.
4. **F2** — sweep "six conductors" out of `key-layout.yaml:100`, `ROADMAP.md:196`,
   `PCB-CLUSTER`, `carrier.md:471`, and the two "8–11 way" passages. The M4 fit
   check is currently run against the wrong ribbon.
5. **F8c** — ADR 0004, `power-entry.md` and ROADMAP E12 disagree about `DIG_GND`.
   E12's acceptance criterion contradicts the drawing it validates.
