# Key boards and the thumb clusters — schematic

<!-- netlist: none (this page's drawing is a physical layout - where the four
     registers sit inside the instrument, two on the main board and one on
     each key board - not a schematic. The circuits are key-register/,
     key-switch-network/ and key-marker-and-bits/, and the two that carry
     nets have netlist.yaml beside them.) -->

**Status:** **First draft, 2026-09-21; board split reworked 2026-09-26** for
[ADR 0017](../../docs/decisions/0017-one-main-board.md); the circuits are KiCad
sheets ([ADR 0019](../../docs/decisions/0019-kicad-sheets-are-the-source.md))
and the key boards are laid out, screwed to the plate
([ADR 0020](../../docs/decisions/0020-key-boards-screw-to-the-plate.md)). The register is the
**SN74HCS165** since 2026-09-27 (ADR 0001's amendment), and its pin map is
**CONFIRMED pin for pin** `[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.3, Table 5-1]`.

Evidence marking follows the other hardware pages: `[repo]` names a file,
`[calc]` shows the arithmetic, `[from memory]` means I could not open the
datasheet, `TBD` means the value is not known and the row says what decides it.

**Four key clusters, one circuit, on three boards.** Each cluster is one
SN74HCS165 with its decoupling, its switches and a network per switch position.
Since ADR 0017:

- **`right_hand` and `left_hand` are the two key boards** (`PCB-CLUSTER`),
  under `PLATE-TOP`, each a board that spans the cavity with one of the
  cassette's columns at each corner (ADR 0025; ADR 0020 Amendment 7): under
  the key plate a spacer, then the board, then the column's standoff, which
  stands on the main board; a screw comes down through the plate, the spacer
  and the board into the standoff. Each connects to the main board by one 1.27 mm IDC ribbon (`CBL-CHAIN`) into a through-hole right-angle header on its underside.
- **`right_thumb` and `left_thumb` are on the main board** (`PCB-CARRIER`),
  their switches soldered to it and clipped into `PLATE-BOTTOM`, their
  registers and networks beside them.

The four clusters differ only in how many switch positions are fitted and which
of their eight register bits are switches, markers or free. The device, the
decoupling, the network and the chain wiring are identical, and they are drawn
once: hierarchical KiCad sheets placed per board, with which bit is a switch, a
marker or free held in
[`allocation.yaml`](key-marker-and-bits/allocation.yaml) (ADR 0019). **The two key boards are
identical in the chain** — one connector each, `SER` in on conductor 6 and `QH` out
on conductor 8 (key-board `J-CHAIN` pins 7 and 5; conductor k is key-board
pin 13 − k, set by the cable, `key-chain-loom.md`) — so they differ only in switch count and strapping.

**The two key boards are KiCad projects** placing these circuits' sheets, which are
the source of truth (ADR 0019):
[`key-board-rh.sch.png`](../boards/key-board-rh/key-board-rh.sch.png) and
[`key-board-lh.sch.png`](../boards/key-board-lh/key-board-lh.sch.png)
(`hardware/boards/`, `docs/reference/tooling.md` §3).

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
   │      under PLATE-TOP, on the columns      │                      │
   │            │ ribbon                        │ ribbon              │
   ├────────────┼───────────────────────────────┼──────────────────────┤
 B │   ┌────────┴───────────── MAIN BOARD ──────┴───────────────────┐  │
 O │   │ left_thumb       U-BOLT band        right_thumb   carrier  │  │
 T │   │ LT 4 keys       (legs' holes)       RT 4 keys     circuits │  │
 T │   └────────────────────────────────────────────────────────────┘  │
 O │      thumb switches in PLATE-BOTTOM, inside face of the oak bottom│
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
was once the reason for two thumb boards. The main board spans it instead,
clamped in the U-bolt's stack with a clearance hole for each leg (ADR 0022
point 7).

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
`PLATE-BOTTOM` the same way, with the main board above them, so the
height rules below hold for the main board's underside too, over its whole
length since the bottom plate runs under all of it (ADR 0025). The thumb
switches' board sits at `switch.thumb_pcb_below_seat`, set by the same spacer
on the bottom plate (ADR 0022).*

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

**The key-board outline is the body CAD's**: a rectangle across the cavity
with a column in each corner (ADR 0020 point 3, ADR 0025),
exported as `mechanical/export/key-board-*.dxf` and placed from
`config/body.yaml` `layout.*`, `boards.*` (the tail ends' `boards.kb_tail_margin`
is longer, so the tail corners' hardware clears the last keys' cutouts) and
`hardware.kb_*` (`kb_mount_inset` keeps the column standoff's keep-out on the board). **Its switch positions are
provisional until M3**: `layout.lh_gaps` and `layout.lh_offsets` stand in until
the ergonomic iteration of M2 fills `key-layout.yaml`'s `x`/`y` (all `null` on
purpose) `[repo] key-layout.yaml, 0010`. Spacing along the key line is
deliberately non-uniform, which is why keys carry explicit coordinates rather
than a pitch parameter.

### Three layout rules that are not obvious

- **The aluminium plate sits directly above this board and is grounded**
  through the cassette's columns at the main board's mounts `[repo] 0025, 0020 Amendment 7`. That is useful — it
  shields the key networks from the LED channel for free — and it is also a
  short waiting to happen. Every part on the plate-facing side needs clearance
  to the plate, or the board needs its passives on the far side.
- **The plate-to-PCB gap is a height limit rather than a ban.** How far the
  pins reach below the collar seat, and how much of that is narrow blade, is
  `docs/reference/ks33-geometry.md`'s; the band of board-top depths that
  leaves the blade in the hole and some pin to solder is
  `switch.pcb_below_seat_window`, and the design depth is
  `switch.pcb_below_seat` (`config/body.yaml`). Subtract `plate-thickness` and
  that is the gap, `mechanical/drc.echo` "key-board mount gap (derived)":
  the spacer under the plate (`MECH-KB-SPACER`, `hardware.kb_spacer_l`),
  with nothing else in the gap. The column's screw clamps the plate and the
  spacer onto the board, so the key boards' depth is the plate plus
  that spacer, checked by "key-board mount sets the board depth"; at the
  hardware's tolerance limits it prints a NOTE, and the first board
  confirms the fit (ADR 0020, Amendment 2).

  Against a plate that is grounded, the rule that follows is a **height**
  rule: chip passives and SOT-23 may sit on the plate-facing side; **nothing
  with a body over about 1.4 mm may** — the SOIC-16 register at 1.75 mm leaves
  ~0.25 mm. That keeps the ICs on the far face, which is where they were
  going anyway, and stops forcing every decoupling capacitor across to join
  them.

  Also budget a **clearance hole through this board** for the centre pole
  (its diameter: the `ks33-geometry.md` footprint). The pole's tip is
  `switch.pole_tip_below_seat` below the seat, so it protrudes below the key
  board by that less `switch.pcb_below_seat` and `boards.key_board_t`.

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
| `U-KEYS` | SN74HCS165 SOIC-16 | 1 | 1 | 1 | 1 | `CLK INH` low, `QH_bar` open. Schmitt-trigger inputs: not a plain 74HC165 (its row) |
| `C-DECOUPLE-165` | 100 nF X7R 0805 | 1 | 1 | 1 | 1 | At the package |
| `SW1-n` | Gateron KS-33 Red | 5 | 4 | 6 | 4 | Soldered. `SW-THUMB` lighter springs are an open option for `LT` |
| `R-KEY-PU` | 2.2 kΩ 1% 0805 | **6** | **6** | 6 | 6 | **24, not 21.** `RT` carries its 4 keys and the 2 reserved spare-switch positions; `LT` and `LH` each carry a pull-up for their *free* bits (22, 23, 31), which the first draft budgeted for switch positions only |
| `R-KEY-SER` | 100 Ω 1% 0805 | 5 | 4 | 6 | 6 | |
| `C-KEY` | 47 nF X7R 0805 | 5 | 4 | 6 | 6 | |
| `J-CHAIN` | 2×6 1.27 mm shrouded IDC, right-angle, through-hole | 1 | — | 1 | — | One per key board, on its underside; its mate is on the main board (`chain-connectors`). Its pin tails stop short of the key plate, which has no window over them (`drc.echo` "J-CHAIN pin tails clear of the key plate") |
| `C-BULK-CHAIN` | 10 µF X5R 0805 | 1 | — | 1 | — | The reservoir on each key board's 3V3, beside `J-CHAIN`: its ESR damps `FB-CHAIN` with `C-DECOUPLE-165` (`key-chain-loom.md`) |
| `marker straps` | copper, no parts | 2 | 2 | 2 | 2 | **Decided** — 8-bit marker, §4. Straight to GND or 3V3, no resistor and no cap: the node never changes |

**Totals:** 4 ICs, 4 decoupling caps, 19 fitted switches in 21 networked
positions; the network passives are the `R-KEY-PU` (`key-pullup-qty`),
`R-KEY-SER` and `C-KEY` rows' quantities in `hardware/bom.csv`. The chain's own parts — `J-CHAIN` at both ends
of each ribbon, `CBL-CHAIN`, and the chain-end `R-SER-TERM` on the main board —
are the key-chain page's.

**ESD: the key boards carry no protection part, and that is accepted.** The
main board's `U-TVS-CHAIN` guards the **MCU's** pins only — `SCK`, `SH/LD`
and the chain-end `SER`, at the `left_hand` `J-CHAIN`. The hop nets
(`HOP_*`, each register's `QH` to the next one's `SER`) and every signal pin
of a key board's `J-CHAIN` land on register pins, which carry the part's own
HBM rating of ±4000 V `[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.4]` —
a component handling rating (JS-001; TI's own footnote is about safe
manufacturing), not a system-level IEC 61000-4-2 rating for a contact touched
with the lid off. The exposure is accepted, not protected. The
array's spare fourth channel stays spare: one channel cannot cover the three
hops. `key-chain-loom.md` has the argument.

---

## Still open

Ordered by what blocks what. **The marker pattern is no longer among them** —
8 bits, two per device, decided 2026-09-21 and recorded in `key-layout.yaml`
and ADR 0001.

*Four items moved with their circuits, 2026-09-21, and three of them are
decided there: `R-KEY-PU` (with `R-KEY-SER`) on
[`key-switch-network/`](key-switch-network/key-switch-network.md), the last 3
free bits on
[`key-marker-and-bits/`](key-marker-and-bits/key-marker-and-bits.md). What is
left of them there is the `LT` springs (M1) and the spare-switch positions
(M2).*

- **The key-board mount's open items** (§5, ADR 0025, ADR 0020 Amendment 7).
  The spacer is chosen (`MECH-KB-SPACER`); the column's standoff and screw are
  open until bought (`MECH-COL-STANDOFF`, `MECH-COL-SCREW`), and nothing goes
  into the wood but the screws' heads, in blind pockets. Open:
  - the spacers, faced to `hardware.kb_spacer_l` (no stocked M2.5 spacer has
    that length), measured at the first fit;
  - the depth at the tolerance limits (drc.echo "key-board depth at the
    hardware's tolerance limits", a NOTE), which the first board confirms;
  - the standoff and the screw, bought, and a US source for the bottom
    plate's studs (`MECH-MB-STUD`), which the plate vendor presses.
  **Plate stiffening** (`plate-thickness` is settled; whether it needs a rib
  or a backer is not) gates M4/M5 — ADR 0002.
- **Conformal coating — decided: the key boards are coated** (ADR 0009,
  *"Conformal-coat the boards"*: every in-body board, and the key boards sit
  under open switch cutouts in the breathed-into cavity). `MECH-COAT` covers
  them. **Brush it on the parts face only** — the bottom, where every
  machine-placed part is and the switch pins are soldered — and **mask
  `J-CHAIN`'s mouth**, whose contacts must stay bare. The switch side is not
  coated: a KS-33's contacts are inside its housing, above the board, and a
  coating that wicks into the housing is a key that sticks or never makes;
  the switch's plated holes are filled with solder from the parts face, so a
  brushed coat has no path up to it `[judgment, not tested]`. Apply it last:
  after the switches are soldered at depth and the board has passed bring-up
  (the key board's README, *Assembling* step 2 and *Bring-up*), with the key
  plate off its columns and turned over, as for soldering.