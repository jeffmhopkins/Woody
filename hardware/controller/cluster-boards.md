# Key cluster boards — schematic

**Status:** **First draft, 2026-09-21.** The last board in the instrument. No
datasheet was reachable from this sandbox, so the 74HC165 pin map below is
`[from memory]` and **must be checked against a vendor drawing before layout.**

Evidence marking follows the other hardware pages: `[repo]` names a file,
`[calc]` shows the arithmetic, `[from memory]` means I could not open the
datasheet, `TBD` means the value is not known and the row says what decides it.

Four boards, **one circuit**. They differ in three ways only: how many switch
positions are fitted, whether the board carries one chain connector or two, and
which of its eight register bits are switches, markers or free. Everything else
— the device, the decoupling, the network, the connector pinout — is identical,
and the boards should be laid out from one schematic with a variant table.

These boards exist because ADR 0001 put the shift registers back where their
switches already are `[repo] 0001`. The switches need a rigid PCB regardless
(ADR 0002), so the register is nearly free there: every switch-to-chip
connection becomes a trace, and six signals leave the board instead of
twenty-one `[repo] 0002`.

---

## The four boards, and where they physically are

```
                      MOUTHPIECE (top of the instrument)
   ┌──────────────────────────────────────────────────────────────────┐
 T │        LH 5 keys                     RH 6 keys                   │
 O │     ┌─────────────┐               ┌───────────────┐              │
 P │     │ PCB-CLUSTER │               │  PCB-CLUSTER  │              │
   │     │   left_hand │               │   right_hand  │              │
   │     └─────────────┘               └───────────────┘              │
   │      under PLATE-TOP, aluminium, 14.0 mm cutouts  [repo] 0002    │
   ├──────────────────────────────────────────────────────────────────┤
 B │   ┌────────────┐      ~50 mm      ┌────────────┐                 │
 O │   │PCB-CLUSTER │     U-BOLT       │PCB-CLUSTER │     CARRIER     │
 T │   │ left_thumb │      BAND        │right_thumb │     (tail)      │
 T │   └────────────┘   [repo] 0009    └────────────┘                 │
 O │    LT 4 keys                       RT 3 keys                     │
 M │      both on PLATE-THUMB, inside face of the oak bottom          │
   └──────────────────────────────────────────────────────────────────┘
                              TAIL (umbilical, USB-C)
```

**Left hand is upper, right hand lower** `[repo] key-layout.yaml`, so the right
clusters are the ones near the carrier.

**The two thumb clusters share one plate but cannot share one board.** ADR 0009
puts the U-bolt in the ~50 mm band between the left thumb arc and the right
thumb rest `[repo] 0009` — exactly where a single bottom board would have to
span. Two boards it is, and the four-board count in ADR 0001 survives for a
mechanical reason rather than an electrical one.

### The chain order crosses the body three times, and it needn't

`config/key-layout.yaml` fixes the chain as
`right_thumb → right_hand → left_thumb → left_hand` `[repo]`, chosen so serial
data flows *toward* the clock source and propagation skew eats setup margin
rather than hold margin (ADR 0001 fix 3). Read against the faces above, that
order alternates top and bottom at **every** hop:

| Order | Hops | Body-thickness crossings |
|---|---|---|
| `RT → RH → LT → LH` — as written | bottom→top, top→bottom, bottom→top | **3** |
| `RT → RH → LH → LT` — swap the last two | bottom→top, top→top, top→bottom | **2** |

**ADR 0001 is unusually honest about what the ordering rule is worth**, and its
own words decide this: adjacent-cluster skew is ~0.5 ns against an HC165's tens
of nanoseconds of propagation delay, so a wrong order *"costs a few percent of
hold margin rather than violating it… The rule is still worth following because
it is free"* `[repo] 0001`.

`LT` and `LH` are both in the upper region of the body, at roughly equal
distance from the carrier, so **swapping them is free in skew terms and saves a
crossing** — a crossing being a run through the 38 mm body thickness, past the
LED channel, terminated by hand, inside something that bonds shut.

**Proposed, not applied**, because the physical positions are all `null` until
M3 `[repo] key-layout.yaml` and the crossing count is an assumption about
geometry that does not exist yet. **If the order changes, the bit allocation in
§4 changes with it** — `left_thumb` and `left_hand` swap their eight-bit
groups. Decide it before the plate DXF is generated, not after. See *Still open*.

---

## §1 The device

```
                        74HC165  SOIC-16          [from memory: pin map]
                     ┌────────────∪────────────┐
       SH/LD  ──────►│ 1  SH/LD        VCC  16 │◄──── 3V3 ──┬── [C-DECOUPLE-165
        SCK   ──────►│ 2  CLK       CLK INH 15 │──── GND     │   100 nF, AT the
         E    ──────►│ 3  E (D4)       D  14   │◄──  key D   │   package]
         F    ──────►│ 4  F (D5)       C  13   │◄──  key C  GND
         G    ──────►│ 5  G (D6)       B  12   │◄──  key B
         H    ──────►│ 6  H (D7)       A  11   │◄──  key A
    (no connect) ────│ 7  QH_bar      SER 10   │◄──── serial in
                GND ─│ 8  GND          QH  9   │─────► serial out
                     └─────────────────────────┘

  CLK INH (pin 15) is tied LOW, permanently.       [repo] 0001 fix 6
  QH_bar (pin 7) is an output and is left open — do NOT ground it.
  C-DECOUPLE-165 goes at the package, on this board, which is the whole
  point of the part: a 74x165's output edges brown out a local rail that
  has no reservoir.                                [repo] 0001 fix 5
```

**Bit order inside the device is `H` first, then `G F E D C B A`.** On the
falling edge of `SH/LD` the parallel inputs load; `H` (D7) appears at `QH`
immediately, and each clock shifts the next one toward the output `[from
memory]`. Combined with ADR 0001's *"bit 0 is the first bit clocked out"*
`[repo] 0001, key-layout.yaml`, that fixes **bit 0 = the `H` input of the
`right_thumb` device** and settles the `H`…`A` question the carrier page left
open — the ordering half of it, anyway. Which *switch* lands on which input is
§4.

**The part is 74HC, not 74LVC**, and that is load-bearing rather than
incidental. HC's slow edges make 265 mm of loom an ordinary lumped load instead
of a transmission line, which is what removed the hazards that briefly sent
these registers to the tail `[repo] 0001, bom.csv`. Same SOIC-16 footprint, so
LVC with proper source termination remains the way back if E4 disagrees.

---

## §2 The key network — 21 of these, spread across four boards

```
   3V3 (from the loom, pin 10 of J-CHAIN)
    │
    ├──[R-KEY-PU 2k2 1%]──┬────────────────────► 74HC165 parallel input
    │                     │
    │              [C-KEY 47 nF X7R]
    │                     │
    │                    GND
    │                     │
    └────── SW ──[R-KEY-SER 100R 1%]────────────┘
           KS-33
       shorts to GND
        when pressed

   Both passives are AT the register input, millimetres from the switch.
   On this board that is automatic; under the tail topology it was a layout
   rule with a 265 mm loom in between.
```

### Derivations

`[calc]`, at 3.3 V into 74HC165 thresholds (`V_IH` = 0.7 × VCC = 2.31 V,
`V_IL` = 0.3 × VCC = 0.99 V `[from memory]`):

| | |
|---|---|
| Release, τ = 2.2 kΩ × 47 nF | 103 µs; crosses `V_IH` at **125 µs** |
| Press, τ = 100 Ω × 47 nF | 4.7 µs; crosses `V_IL` at **5.7 µs** — 44× inside the 250 µs scan |
| Pole | 1.54 kHz → **54 dB** at the WS2815's 800 kHz data rate |
| Static | **1.43 mA** per closed key; 18 closed = **25.8 mA** off the loom's 3V3 |

**Press is instant on the scan's timescale and release is filtered**, which is
the asymmetric-debounce shape ADR 0001 wants — instant attack, filtered release
`[repo] 0001`. The 125 µs release filter is half a scan period and costs
nothing musically; note-off is filtered in firmware anyway.

> **Why the network is fitted at all, stated honestly.** The argument that
> originally bought these parts — a 12 V LED edge through ~15 pF injecting a
> false level — was wrong, and ADR 0001 now records why: there is no 12 V edge,
> `Q/C` is the wrong model because coupling is a divider, and a divider cannot
> exceed its aggressor's swing `[repo] 0001`. **The pull-up is still
> mandatory**, because a floating CMOS input has no defined state at all — and
> this cavity is breathed into for hours at 10–20 K above ambient, with the
> switch contacts open. The 47 nF is a bounce filter and cheap insurance. It is
> not what makes the topology safe.

**`R-KEY-PU` is 2.2 kΩ and the reason it is no longer 10 kΩ has expired.**
`bom.csv` says so itself: the 2.2 kΩ was chosen when the node ran 265 mm down an
uncoated loom, *"that reason is gone now the register is back on the cluster
board"*, and it was kept as cheap insurance `[repo] bom.csv`. **Keeping it is
not free any more**, because 25.8 mA of play-rate load lands on the rail that is
also the MCP3202's voltage reference — worth 3.2 LSB, accepted on the carrier
page `[repo] carrier.md §2`. Going back to 10 kΩ would cut that to 5.9 mA and
0.7 LSB, at the price of a 100 µs τ in a humid cavity. **Recorded as a live
trade, not re-opened here.**

---

## §3 The two connectors, and the one link that makes all four boards identical

`J-CHAIN` is a 2×6 IDC boxed header on a 12-way ribbon, alternating ground,
decided 2026-09-21 `[repo] 0001, bom.csv`:

```
   1 GND    2 SCK      3 GND    4 SH/LD    5 GND    6 SER
   7 GND    8 QH       9 GND   10 3V3     11 spare 12 spare
```

Boxed and keyed at all eight positions, because a reversed connector puts 3V3
onto the `QH` net.

```
   J-CHAIN-IN                                          J-CHAIN-OUT
   (toward the carrier)                        (away, to the next board)

    2 SCK   ─────────────┬──────────────────────────────► 2 SCK
    4 SH/LD ─────────────┼──┬───────────────────────────► 4 SH/LD
   10 3V3   ─────────────┼──┼──┬────────────────────────► 10 3V3
   GND ×5   ─────────────┼──┼──┼──┬─────────────────────► GND ×5
    6 SER   ─────────────┼──┼──┼──┼──┬──────────────────► 6 SER
                         │  │  │  │  │
                    ┌────▼──▼──▼──▼──┴─────┐
                    │  74HC165             │
                    │  CLK  SH/LD  VCC GND │
                    │                      │
    8 QH   ◄────────┤ QH (pin 9)           │
                    │                      │        ┌──── 8 QH
                    │  SER (pin 10) ◄──────┼──[LK-SER]
                    └──────────────────────┘        └──── from pin 6 above
                                                      ▲
                          LK-SER: a 3-pad solder link.
                          Position A (boards 1-3): SER comes from OUT pin 8,
                            i.e. the next board's QH. Normal chaining.
                          Position B (last board): SER comes from the IN pin 6
                            passthrough, which reaches all the way back to the
                            carrier.
```

**`SCK`, `SH/LD`, `3V3` and the five grounds are a straight bus** — IN to OUT,
1:1, so a plain straight-through ribbon works between any two boards.

**`QH` and `SER` are not a bus, and that is what forces two connectors.** Each
board's `QH` goes *toward* the carrier on `IN` pin 8; the *next* board's `QH`
arrives on `OUT` pin 8 and becomes this board's serial input. Pin 8 therefore
carries a different net on each side of the board, which is why the chain is
eight connectors across five boards rather than five `[repo] carrier.md §3`.

### `LK-SER` and `R-SER-TERM` close the self-test question for free

The carrier page raised whether the far device's serial input should be tied off
(ADR 0001) or driven from the carrier, which would let firmware shift a known
pattern through all 32 bits and distinguish *"the loom is broken"* from *"one
bit is stuck"* — something the static marker cannot do `[repo] carrier.md §3`.

**It does not have to be decided in copper.** Fit, on the last board only:

```
   IN pin 6 (SER passthrough) ──┬──[LK-SER position B]──► 74HC165 SER (pin 10)
                                │
                        [R-SER-TERM 10k]
                                │
                               3V3
```

`R-SER-TERM` holds the input high if nothing drives it, which is the tied-off
case ADR 0001 specified. If firmware *does* drive `IO33`, the carrier's output
wins through its 100 Ω series resistor against a 10 kΩ pull `[calc]` — a
divider of 100/10100, so the driven level is within 33 mV of the rail. **The
self-test becomes a firmware choice rather than a board choice**, at the cost of
one resistor, and this page recommends fitting it and deciding later.

---

## §4 The 32 bits

### Allocation, on the chain order as written today

`H` is the first bit out of each device, so within a cluster the lowest-numbered
key takes the earliest bit:

| Device | Bits | `H` | `G` | `F` | `E` | `D` | `C` | `B` | `A` |
|---|---|---|---|---|---|---|---|---|---|
| `right_thumb` | 0–7 | RT1 | RT2 | RT3 | sw+ | sw− | sw? | **M** | **M** |
| `right_hand` | 8–15 | RH1 | RH2 | RH3 | RH4 | RH5 | RH6 | **M** | **M** |
| `left_thumb` | 16–23 | LT1 | LT2 | LT3 | LT4 | **M** | **M** | free | free |
| `left_hand` | 24–31 | LH1 | LH2 | LH3 | LH4 | LH5 | **M** | **M** | free |

`sw+` `sw−` `sw?` are the three reserved spare-switch positions — octave up,
octave down, hold/preset `[repo] key-layout.yaml`. **Proposed on `right_thumb`**,
because RT is already the control cluster (its three fitted keys are `role:
control`, not fingering inputs `[repo] key-layout.yaml`) and it has the spare
capacity. They need **plate cutouts at M3 even if the switches are fitted
later** `[repo] key-layout.yaml, 0010`, and the cutouts go in `PLATE-THUMB`.

**Every position above gets the full `R-KEY-PU`/`R-KEY-SER`/`C-KEY` network**,
including the three unfitted spares — 21 sets, which is what `bom.csv` budgets
`[repo]`.

### The marker pattern: 8 bits, not 6 — DECIDED 2026-09-21

`key-layout.yaml` booked 6 marker bits and 5 genuinely free ones. **It now says
8 and 3** `[repo] key-layout.yaml, 0001`, and the table above shows the 8.
The argument, for the record:

A marker is a framing check: firmware reads it every scan, and a frame that
fails it holds the previous frame and increments a visible error counter
`[repo] 0001`. Its whole value is converting an invisible intermittent fault
into a number on the display.

**Six bits cannot do that per device in both directions, and eight can.** With
two marker bits in every device, one wired high and one wired low, a device that
is dead, unclocked, stuck high or stuck low fails its own marker — whichever way
it failed, and no matter what the other three are doing. At six, two devices get
a single marker bit each and are only checkable in one direction.

**The two extra bits cost almost nothing, because "free" bits are not free —
they are useless.** A free bit has no plate cutout and no switch. The body bonds
shut. You cannot add a switch to one without cutting the plate, and the plate is
generated at M3 and fitted before bonding `[repo] 0009, 0010`. The three
positions that *are* retrofittable are the reserved spare-switch bits, which
have cutouts and are untouched by this proposal. **So the trade is: two bits
that could never be used against per-device fault detection in both
directions.**

Proposed levels:

| Device | Input | Bit | Level | | Input | Bit | Level |
|---|---|---|---|---|---|---|---|
| `right_thumb` | `B` | 6 | **1** | | `A` | 7 | **0** |
| `right_hand` | `B` | 14 | **0** | | `A` | 15 | **1** |
| `left_thumb` | `D` | 20 | **1** | | `C` | 21 | **0** |
| `left_hand` | `C` | 29 | **0** | | `B` | 30 | **1** |

Read in bit order the marker is `1 0 · 0 1 · 1 0 · 0 1`. **Not a constant and
not a repeating byte** — an all-zeros frame, an all-ones frame, a stuck bus and
a frame shifted by one position all fail it, and every device fails it on its
own whichever way it failed.

That leaves **3 free bits**: `left_thumb` `B` and `A` (22, 23) and `left_hand`
`A` (31). Pull them, per ADR 0001 fix 6 — a floating CMOS input is the exact
fault `R-KEY-PU` exists to fix `[repo] 0001, key-layout.yaml`.

> **Marker bits strap straight to the rails — no resistor, no capacitor.** A
> marker is not a switch: it never changes, so there is nothing to debounce and
> no pull-up to lose an argument with. Eight 47 nF caps on a rail that is
> already the ADC's reference, for eight nodes that are hard-wired, would be
> eight caps of pure cost. `[calc]` **16 parts saved** against wiring markers as
> if they were keys, and the network count stays exactly the 21 `bom.csv`
> budgets `[repo]`.

**This is hard-wired copper on boards that bond into the instrument. It has to
be right before the boards are ordered, and firmware has to be told the pattern.**

---

## §5 Mechanical

**Plate, then switch, then board.** The switch clips into a 14.0 × 14.0 mm
cutout in the aluminium plate — the same as standard MX, measured across 47
cutouts in a working KS-33 build `[repo] ks33-geometry.md` — and its pins solder
into the PCB beneath. ADR 0002 calls the cutout *"the precision feature of the
entire build"*, and the reason is in the geometry file: **a KS-33 is located by
its cutout alone.** There are no alignment posts, unlike MX `[repo]
ks33-geometry.md`.

**Footprint** `[repo] ks33-geometry.md`, from the `gateron-ks27` KiCad footprint
used with KS-33 in that build:

| Feature | Position | Size |
|---|---|---|
| Centre pole | (0, 0) | ⌀5.0 mm |
| Pin 1 | (2.6, 5.75) | ⌀1.5 mm drill |
| Pin 2 | (−4.4, 4.7) | ⌀1.5 mm drill |

> **Use Gateron's own drawing and STEP model, not this table.** The geometry
> file says so itself — it was measured out of an open-source keyboard project
> because `gateron.com` is unreachable from this sandbox, and the vendor drawing
> supersedes it wherever the two disagree `[repo] ks33-geometry.md`.

**The board outline cannot be drawn yet, and that is correct rather than
incomplete.** Every `x`/`y` in `key-layout.yaml` is `null` on purpose; positions
come out of ergonomic iteration at M2/M3, and the plate DXF and these outlines
are both generated from that file `[repo] key-layout.yaml, 0010`. Spacing along
the key line is deliberately non-uniform, which is why keys carry explicit
coordinates rather than a pitch parameter.

### Three layout rules that are not obvious

- **The aluminium plate sits directly above this board and is grounded**
  through `MECH-GNDBOND` `[repo] carrier.md §1, 0009`. That is useful — it
  shields the key networks from the LED channel for free — and it is also a
  short waiting to happen. Every part on the plate-facing side needs clearance
  to the plate, or the board needs its passives on the far side.
- **Plate-to-PCB standoff is `TBD` and it is a real dimension**, set by the
  KS-33's pin length below its clip shoulder. MX plates sit ~3.4 mm above the
  PCB; a 12.2 mm low-profile switch will want less `[from memory]`. It has to
  come from the vendor drawing, and it constrains component height underneath.
- **Plate thickness is still open and blocks M4/M5** `[repo] key-layout.yaml,
  0002, bom.csv`. 2 mm defeats the retention clips entirely, MX standard is
  1.5 mm, the reference KS-33 build used 1.1 mm. This board does not decide it
  but it is fitted around the answer.

---

## Component table

Per board, from `bom.csv` `[repo]` unless marked **proposed**.

| Ref | Value | `LH` | `LT` | `RH` | `RT` | Notes |
|---|---|---|---|---|---|---|
| `U-KEYS` | 74HC165 SOIC-16 | 1 | 1 | 1 | 1 | `CLK INH` low, `QH_bar` open |
| `C-DECOUPLE-165` | 100 nF X7R 0805 | 1 | 1 | 1 | 1 | At the package |
| `SW1-n` | Gateron KS-33 Red | 5 | 4 | 6 | 3 | Soldered. `SW-THUMB` lighter springs are an open option for `LT` |
| `R-KEY-PU` | 2.2 kΩ 1% 0805 | 5 | 4 | 6 | 6 | `RT` carries the 3 reserved spare-switch positions |
| `R-KEY-SER` | 100 Ω 1% 0805 | 5 | 4 | 6 | 6 | |
| `C-KEY` | 47 nF X7R 0805 | 5 | 4 | 6 | 6 | |
| `J-CHAIN` | 2×6 IDC boxed, keyed | 1 | 2 | 2 | 2 | `LH` is the chain end and has `IN` only |
| **`LK-SER`** | **3-pad solder link** | **B** | **A** | **A** | **A** | **Proposed — position B only on the chain-end board** |
| **`R-SER-TERM`** | **10 kΩ 0805** | **1** | — | — | — | **Proposed — chain-end board only; makes the self-test a firmware choice** |
| `marker straps` | copper, no parts | 2 | 2 | 2 | 2 | **Decided** — 8-bit marker, §4. Straight to GND or 3V3, no resistor and no cap: the node never changes |

**Totals across the four boards:** 4 ICs, 4 decoupling caps, 18 fitted switches
in 21 networked positions, 63 network passives, 7 chain connectors — **plus one
more `J-CHAIN` on the carrier, eight in all** `[repo] carrier.md §3`.

---

## Still open

Ordered by what blocks what. The first two block the plate DXF, not just this
board. **The marker pattern is no longer among them** — 8 bits, two per device,
decided 2026-09-21 and recorded in `key-layout.yaml` and ADR 0001.

- **The chain order, against the faces** (*The four boards*, above).
  `RT → RH → LH → LT` saves a
  body-thickness crossing over the order in `key-layout.yaml`, at a skew cost
  ADR 0001 itself prices at a few percent of hold margin. **If it changes,
  `left_thumb` and `left_hand` swap bit groups and §4's table moves with them.**
  Needs M3's geometry to confirm the crossing count is real.
- **Where the 3 reserved spare-switch positions go.** Proposed on `right_thumb`
  as the control cluster; placement is an M2 decision with hands on the mule
  `[repo] key-layout.yaml`, and it decides which board carries them **and which
  plate gets the cutouts.**
- **The 74HC165 pin map and its 3.3 V thresholds** (§1, §2). Every number in
  this page's timing table rests on `V_IH` = 0.7 × VCC and `V_IL` = 0.3 × VCC
  `[from memory]`. Five minutes with a datasheet.
- **`R-KEY-PU` at 2.2 kΩ versus 10 kΩ** (§2). The reason for 2.2 kΩ expired when
  the register moved back to this board, and the cost — 25.8 mA on the ADC's
  reference rather than 5.9 mA — arrived at the same moment. Live trade,
  recorded on the carrier page as accepted.
- **Plate-to-PCB standoff, and plate thickness** (§5). Both come from Gateron's
  drawing; the second blocks M4/M5 already.
- **Whether `LT` takes lighter springs** (`SW-THUMB`), which is an M1 decision by
  hand and changes nothing electrically `[repo] bom.csv, 0002`.
- **Conformal coating.** `MECH-COAT` covers the carrier; nothing says whether
  these boards are coated, and they sit under an open switch contact in a cavity
  that is breathed into. Coating a soldered mechanical switch is not obviously
  right — see ADR 0009 before deciding.
