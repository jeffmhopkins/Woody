# Key boards and the thumb clusters — schematic

<!-- netlist: none (this page's drawing is a physical layout - where the four
     registers sit inside the instrument, two on the main board and one on
     each key board - not a schematic. The circuits are key-register/,
     key-switch-network/ and key-marker-and-bits/, and the two that carry
     nets have netlist.yaml beside them.) -->

**Status:** **First draft, 2026-09-21; board split reworked 2026-09-26** for
[ADR 0017](../../docs/decisions/0017-one-main-board.md). The 74HC165 pin map is
**CONFIRMED pin for pin** `[74HC165-nexperia.pdf Table 2, p.4]`.

Evidence marking follows the other hardware pages: `[repo]` names a file,
`[calc]` shows the arithmetic, `[from memory]` means I could not open the
datasheet, `TBD` means the value is not known and the row says what decides it.

**Four key clusters, one circuit, on three boards.** Each cluster is one
74HC165 with its decoupling, its switches and a network per switch position.
Since ADR 0017:

- **`right_hand` and `left_hand` are the two key boards** (`PCB-CLUSTER`),
  hanging from the lid under `PLATE-TOP`. Each connects to the main board by
  one flat flex ribbon.
- **`right_thumb` and `left_thumb` are on the main board** (`PCB-CARRIER`),
  their switches soldered to it and clipped into `PLATE-THUMB`, their
  registers and networks beside them.

The four clusters differ only in how many switch positions are fitted and which
of their eight register bits are switches, markers or free. The device, the
decoupling, the network and the chain wiring are identical, and they should be
laid out from one schematic with a variant table. **The two key boards are
identical in the chain** — one connector each, `SER` in on pin 6 and `QH` out
on pin 8 — so they differ only in switch count and strapping.

These registers sit where their switches already are because ADR 0001 put
them there `[repo] 0001`: the switches need a rigid PCB regardless (ADR 0002),
so the register is nearly free there, and every switch-to-chip connection is a
trace.

*Split 2026-09-21 into this page and three circuit directories: the
device is [`key-register/`](key-register/key-register.md), the switch network
is [`key-switch-network/`](key-switch-network/key-switch-network.md), and the
32-bit allocation with its marker straps is
[`key-marker-and-bits/`](key-marker-and-bits/key-marker-and-bits.md). The chain
that joins the four registers is
[`../interfaces/key-chain-loom/`](../interfaces/key-chain-loom/key-chain-loom.md).
The section numbers are left as they were written.*

---

## The four clusters, and where they physically are

```
                      MOUTHPIECE (top of the instrument)
   ┌──────────────────────────────────────────────────────────────────┐
 T │        LH 5 keys                     RH 6 keys                   │
 O │     ┌─────────────┐               ┌───────────────┐              │
 P │     │  KEY BOARD  │               │   KEY BOARD   │              │
   │     │  left_hand  │               │   right_hand  │              │
   │     └──────┬──────┘               └───────┬───────┘              │
   │      under PLATE-TOP, hung from the lid   │                      │
   │            │ ribbon                        │ ribbon              │
   ├────────────┼───────────────────────────────┼──────────────────────┤
 B │   ┌────────┴───────────── MAIN BOARD ──────┴───────────────────┐  │
 O │   │ left_thumb       U-BOLT band        right_thumb   carrier  │  │
 T │   │ LT 4 keys       (holes over nuts)   RT 4 keys     circuits │  │
 T │   └────────────────────────────────────────────────────────────┘  │
 O │      thumb switches in PLATE-THUMB, inside face of the oak bottom │
 M │                                                                   │
   └──────────────────────────────────────────────────────────────────┘
                              TAIL (umbilical, USB-C)
```

Positions are the body model's (`mechanical/DESIGN.md`); the drawing shows
arrangement, not placement.

**Left hand is upper, right hand lower** `[repo] key-layout.yaml`, so the right
clusters are the ones near the MCU at the tail.

**The two thumb clusters now share one board.** ADR 0009 puts the U-bolt in the
band between the left thumb line and the right thumb rest `[repo] 0009`, which
was once the reason for two thumb boards. The main board spans it instead, with
holes over the U-bolt's nuts (ADR 0017).

**The chain order is `config/key-layout.yaml`'s and stays**:
`right_thumb → right_hand → left_thumb → left_hand`, chosen so serial data
flows toward the clock source (ADR 0001 fix 3). Each key board's hop is its own
ribbon out and back, so every order uses the same two ribbons and there is no
crossing to save by reordering — the key-chain page has the hop map.

---

## §3 The chain connectors

*§3 lives in [`../interfaces/key-chain-loom/`](../interfaces/key-chain-loom/key-chain-loom.md):
the ribbon, its connectors, the pinout (and why the key board numbers it in
reverse) and the chain-end pull-up. The section number is kept here because
sibling pages cite `cluster-boards.md` §3.*

---

## §5 Mechanical

*Written for the key boards under `PLATE-TOP`. The thumb switches sit in
`PLATE-THUMB` the same way, with the main board beneath them, so the
standoff and height rules below hold for the main board's thumb areas too —
which suits it, because its parts face the other way (ADR 0017).*

**Plate, then switch, then board.** The switch clips into a 14.0 × 14.0 mm
cutout in the aluminium plate — the same as standard MX, measured across 47
cutouts in a working KS-33 build `[repo] ks33-geometry.md` — and its pins solder
into the PCB beneath. ADR 0002 calls the cutout *"the precision feature of the
entire build"*, and the reason is in the geometry file: **a KS-33 is located by
its cutout alone.** There are no alignment posts, unlike MX `[repo]
ks33-geometry.md`.

**Footprint: see `docs/reference/ks33-geometry.md`, and do not copy it here.**

> This page carried its own copy of that table until 2026-09-22, and **the two
> had already diverged on the drill diameter** — the geometry page was
> independently re-confirmed against a second library and a STEP model
> (⌀1.2 mm drill, centre pole ⌀5.25 mm, because the pins are flat blades
> 2.0 × 0.45 mm at the root rather than round pins), and this copy still said
> ⌀1.5 / ⌀5.0 with no hint that anything had moved. **Two pages, one fact,
> and the one a board gets laid out from was the stale one.** Rule 1 exists
> for exactly this; the table lives in one place now.

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
- **Plate-to-PCB standoff: 2.0–2.4 mm, and it is a height limit rather than a
  ban** `[repo] docs/reference/ks33-geometry.md`. The pins reach **5.10 mm**
  below the collar seat with only the last **1.9 mm** as narrow blade, so
  **the PCB top must sit within ~3.2–3.6 mm of the seat**. Subtract
  `plate-thickness` and that is the gap.

  Against a plate that is grounded, the rule that follows is a **height**
  rule: chip passives and SOT-23 may sit on the plate-facing side; **nothing
  with a body over about 1.4 mm may** — a SOIC-16 `74HC165` at 1.75 mm leaves
  ~0.25 mm. That keeps the ICs on the far face, which is where they were
  going anyway, and stops forcing every decoupling capacitor across to join
  them.

  Also budget a **⌀5.25 mm clearance hole through both the plate and this
  board** for the centre pole, which protrudes 0.5–0.9 mm below a 1.6 mm PCB.

  > **This bullet read "there is none, and that is the answer" and derived
  > *there is no plate-facing side: put every passive on the far face*.**
  > That was arithmetic applied to a 1.5–2 mm plate, and the vendor drawing
  > has since ruled out both. The conclusion reversed when `plate-thickness`
  > settled at 1.20 mm, and it reversed on the page that owns the figure —
  > this one only cites it. Corrected 2026-09-21.
- **Plate thickness is settled** — `plate-thickness`, read off Gateron's
  banked drawing. What is still open is **stiffening**: the settled thickness
  is thinner than the 1.5 mm MX standard, and nothing has decided whether the
  plate needs a rib, a backing plate or neither. That is what gates M4/M5.

  The framing changed twice on the way here. The model shows **no retention
  clip shoulder at all**, so "2 mm defeats the clips" was the wrong worry; the
  real constraint is that **the through-cutout section is only 2.50 mm deep**.
  This board does not decide the thickness but it is fitted around it.

  *(This bullet read "Plate thickness is still open and blocks M4/M5" and
  cited `key-layout.yaml` as its authority — which said `plate_thickness:
  null`. The citation chain was intact and both ends agreed with each other,
  and neither agreed with the register. A reader who checked the source got
  the wrong answer confirmed.)*

---

## Component table

Per cluster, from `bom.csv` `[repo]`. `LH` and `RH` are the key boards; `LT`
and `RT` are on the main board.

| Ref | Value | `LH` | `LT` | `RH` | `RT` | Notes |
|---|---|---|---|---|---|---|
| `U-KEYS` | 74HC165 SOIC-16 | 1 | 1 | 1 | 1 | `CLK INH` low, `QH_bar` open |
| `C-DECOUPLE-165` | 100 nF X7R 0805 | 1 | 1 | 1 | 1 | At the package |
| `SW1-n` | Gateron KS-33 Red | 5 | 4 | 6 | 4 | Soldered. `SW-THUMB` lighter springs are an open option for `LT` |
| `R-KEY-PU` | 2.2 kΩ 1% 0805 | **6** | **6** | 6 | 6 | **24, not 21.** `RT` carries its 4 keys and the 2 reserved spare-switch positions; `LT` and `LH` each carry a pull-up for their *free* bits (22, 23, 31), which the first draft budgeted for switch positions only |
| `R-KEY-SER` | 100 Ω 1% 0805 | 5 | 4 | 6 | 6 | |
| `C-KEY` | 47 nF X7R 0805 | 5 | 4 | 6 | 6 | |
| `J-CHAIN` | 12-way FFC ZIF | 1 | — | 1 | — | One per key board; its mate is on the main board (`chain-connectors`) |
| `marker straps` | copper, no parts | 2 | 2 | 2 | 2 | **Decided** — 8-bit marker, §4. Straight to GND or 3V3, no resistor and no cap: the node never changes |

**Totals:** 4 ICs, 4 decoupling caps, 19 fitted switches in 21 networked
positions, 63 network passives. The chain's own parts — `J-CHAIN` at both ends
of each ribbon, `FFC-CHAIN`, and the chain-end `R-SER-TERM` on the main board —
are the key-chain page's.

---

## Still open

Ordered by what blocks what. **The marker pattern is no longer among them** —
8 bits, two per device, decided 2026-09-21 and recorded in `key-layout.yaml`
and ADR 0001.

*Four of the items below moved with their circuits, 2026-09-21: the spare-switch
positions and the last 3 free bits to
[`key-marker-and-bits/`](key-marker-and-bits/key-marker-and-bits.md), `R-KEY-PU`
and the `LT` springs to
[`key-switch-network/`](key-switch-network/key-switch-network.md), and the
closed 74HC165 item to [`key-register/notes.md`](key-register/notes.md).*

- **Plate-to-PCB standoff, and plate thickness** (§5). Both come from Gateron's
  drawing; the second blocks M4/M5 already.
- **Conformal coating.** `MECH-COAT` covers the main board; nothing says
  whether the key boards are coated, and they sit under an open switch contact
  in a cavity that is breathed into. Coating a soldered mechanical switch is
  not obviously right — see ADR 0009 before deciding.
