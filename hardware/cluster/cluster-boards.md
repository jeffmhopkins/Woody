# Key cluster boards — schematic

**Status:** **First draft, 2026-09-21.** The last board in the instrument.
The pin map below was `[from memory]` when this page was drafted, because no
datasheet was reachable from the sandbox. **Four are banked now** and the map
is **CONFIRMED pin for pin** `[74HC165-nexperia.pdf Table 2, p.4]`.

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

*Split 2026-09-21 into this board page and three circuit directories: the
device is [`key-register/`](key-register/key-register.md), the switch network
is [`key-switch-network/`](key-switch-network/key-switch-network.md), and the
32-bit allocation with its marker straps is
[`key-marker-and-bits/`](key-marker-and-bits/key-marker-and-bits.md). `§3`, the
chain bus, stays here because it crosses to the carrier board; `§5` and the
component table stay here because they are board facts. The section numbers are
left as they were written.*

*(That paragraph is as it was written earlier on 2026-09-21. `§3` has since
moved, for the reason it names — it crosses to the carrier board — to
[`../interfaces/key-chain-loom/`](../interfaces/key-chain-loom/key-chain-loom.md),
which holds both ends of the chain. This page keeps the heading and the
component table.)*

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

## §3 The two connectors, and the one link that makes all four boards identical

*§3 moved verbatim to
[`../interfaces/key-chain-loom/`](../interfaces/key-chain-loom/key-chain-loom.md),
together with `carrier.md` §3, because the chain is one circuit with an end on
each board. The connector pinout, the `QH`/`SER` split and the `LK-SER`
self-test argument are all there, with the drawings, unchanged. The section
number is kept here because four sibling pages cite `cluster-boards.md` §3.*

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
  through `MECH-GNDBOND` `[repo] power-entry-instrument.md, 0009`. That is useful — it
  shields the key networks from the LED channel for free — and it is also a
  short waiting to happen. Every part on the plate-facing side needs clearance
  to the plate, or the board needs its passives on the far side.
- **Plate-to-PCB standoff: there is none, and that is the answer**
  `[repo] docs/reference/ks33-geometry.md, measured off GATERON-KS-33-3D.step`.
  This bullet said the dimension was `TBD` and would come from the vendor
  drawing. It came from a solid model instead, and it is tighter than expected:
  the pins reach **5.10 mm** below the collar seat with only the last **1.9 mm**
  as narrow blade, so **the PCB top must sit within ~3.2–3.6 mm of the seat**.
  Against a 1.5–2 mm plate that leaves 1.2–2.1 mm — the board is effectively
  **hard against the plate underside**.

  **Which collides with the bullet above it.** "Every part on the plate-facing
  side needs clearance to the plate" now means *there is no plate-facing side*:
  **put every passive on the far face.** Also budget a **⌀5.25 mm clearance
  hole through both the plate and this board** for the centre pole, which
  protrudes ~2 mm below the PCB.
- **Plate thickness is still open and blocks M4/M5** `[repo] key-layout.yaml,
  0002, bom.csv`. The framing has changed: the model shows **no retention clip
  shoulder at all**, so "2 mm defeats the clips" may be the wrong worry. The
  real constraint is that **the through-cutout section is only 2.50 mm deep**,
  of which a 2 mm plate consumes 80 %. MX standard is 1.5 mm and the reference
  KS-33 build used 1.1 mm. This board does not decide it but it is fitted
  around the answer.

---

## Component table

Per board, from `bom.csv` `[repo]` unless marked **proposed**.

| Ref | Value | `LH` | `LT` | `RH` | `RT` | Notes |
|---|---|---|---|---|---|---|
| `U-KEYS` | 74HC165 SOIC-16 | 1 | 1 | 1 | 1 | `CLK INH` low, `QH_bar` open |
| `C-DECOUPLE-165` | 100 nF X7R 0805 | 1 | 1 | 1 | 1 | At the package |
| `SW1-n` | Gateron KS-33 Red | 5 | 4 | 6 | 3 | Soldered. `SW-THUMB` lighter springs are an open option for `LT` |
| `R-KEY-PU` | 2.2 kΩ 1% 0805 | **6** | **6** | 6 | 6 | **24, not 21.** `RT` carries the 3 reserved spare-switch positions; `LT` and `LH` each carry a pull-up for their *free* bits (22, 23, 31), which the first draft budgeted for switch positions only |
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

*Four of the items below moved with their circuits, 2026-09-21: the spare-switch
positions and the last 3 free bits to
[`key-marker-and-bits/`](key-marker-and-bits/key-marker-and-bits.md), `R-KEY-PU`
and the `LT` springs to
[`key-switch-network/`](key-switch-network/key-switch-network.md), and the
closed 74HC165 item to [`key-register/notes.md`](key-register/notes.md). The
intro above is as written, and counted them.*

- **The chain order, against the faces** (*The four boards*, above).
  `RT → RH → LH → LT` saves a
  body-thickness crossing over the order in `key-layout.yaml`, at a skew cost
  ADR 0001 itself prices at a few percent of hold margin. **If it changes,
  `left_thumb` and `left_hand` swap bit groups and §4's table moves with them.**
  Needs M3's geometry to confirm the crossing count is real.
- **Plate-to-PCB standoff, and plate thickness** (§5). Both come from Gateron's
  drawing; the second blocks M4/M5 already.
- **Conformal coating.** `MECH-COAT` covers the carrier; nothing says whether
  these boards are coated, and they sit under an open switch contact in a cavity
  that is breathed into. Coating a soldered mechanical switch is not obviously
  right — see ADR 0009 before deciding.
