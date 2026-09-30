# Key chain — main board to two key boards

**Status:** Rewritten 2026-09-26 for the one-main-board design
([ADR 0017](../../../docs/decisions/0017-one-main-board.md)); connectors and
cable changed to through-hole 1.27 mm IDC on 2026-09-27 (ADR 0017's
amendment; what they were is in [`notes.md`](notes.md)). The directory
keeps its old name so that paths into it do not break; there is no loom any
more. What this page described before — a carrier and four cluster boards on
IDC ribbons — is summarised in [`notes.md`](notes.md) and is whole in git.

The four registers (`U-KEYS`, SN74HCS165) are still one chain of 32 bits, **in the same order**, so the
bit map ([`key-marker-and-bits`](../../cluster/key-marker-and-bits/key-marker-and-bits.md))
and the firmware do not change. What changed is where the registers sit:

- **Two on the main board**, `right_thumb` and `left_thumb`, with their
  switches and networks (ADR 0017). Their part of the chain is traces.
- **Two on the key boards**, `right_hand` and `left_hand`, which hang from the
  lid under the top plate (`PCB-CLUSTER`). Each key board connects to the main
  board by **one 12-conductor 1.27 mm IDC ribbon** (`CBL-CHAIN`) with a 2×6
  IDC socket at each end, plugged into a **through-hole, right-angle, shrouded
  2×6 header** (`J-CHAIN`) on each board — `chain-connectors` in all.
  Through-hole because the board, not SMT pads, then takes the cable's pull
  (owner, 2026-09-27).

Evidence marking as on the other hardware pages: `[repo]` names a file,
`[calc]` shows the arithmetic, `[from memory]` means no datasheet was read for
it.

## Interfaces

Every net that crosses this circuit's boundary, and **which board each end is
on**. Quantities appear **only** as a citation into `config/figures.yaml` —
this table names nodes, it does not restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | End | Dir | Peer | Figure | Note |
|---|---|---|---|---|---|
| `SCK` (pin 2) | main → all four registers | out | MCU IO38 → `cluster/key-register` | `chain-conductors` | One net: two registers by trace, two over the ribbons. `R-CHAIN-SER` at the driving end |
| `SH/LD` (pin 4) | main → all four registers | out | MCU IO7 → `cluster/key-register` | `chain-conductors` | One net, like `SCK`. A glitch here reloads every register mid-shift — the whole 32-bit word |
| `SER` (pin 6) | main → key board | out | → `cluster/key-register` | `chain-connectors` | **The key board's own serial input**, on both ribbons. On the `right_hand` ribbon it is `left_thumb`'s `QH`; on the `left_hand` ribbon it is the chain end, `IO33` and `R-SER-TERM` |
| `QH` (pin 8) | key board → main | in | `cluster/key-register` → | `chain-connectors` | **The key board's own serial output**, on both ribbons. `right_hand`'s goes to `right_thumb`'s `SER`; `left_hand`'s to `left_thumb`'s |
| `QH` of `right_thumb` | main board only | in → out | `cluster/key-register` → MCU IO40 | `marker-bits`, `free-bits` | Bit 0 onward. **Reaches no connector** — a trace from the register to the MCU's pins |
| `GND` ×5 (pins 1, 3, 5, 7, 9) | both | ref | `cluster/key-register`, `cluster/key-switch-network`, `cluster/key-marker-and-bits` | `chain-conductors` | One between every signal, and against pin 10 |
| `3V3` (pin 10) | main → key boards | out | MCU board's 3V3 (`DEV_3V3`) → `right_thumb`/`left_thumb` direct, and → one `FB-CHAIN` per ribbon → the key board's `cluster/key-register`, `cluster/key-switch-network`, `cluster/key-marker-and-bits`; shared with `carrier/breath-adc` | `key-pullup-qty` | **It is also the MCP3202's reference** — `carrier.md` §2 carries that argument. No fuse (ADR 0018) |
| spare ×2 (pins 11, 12) | both | — | — | `chain-conductors` | ADR 0009's rule, free in a 12-way part |
| `J-CHAIN`, `CBL-CHAIN` | both | — | — | `chain-connectors` | This circuit's connectors and cables |
| `R-CHAIN-SER`, `R-SER-TERM`, `U-TVS-CHAIN`, `FB-CHAIN` | main | — | — | — | This circuit's parts, all on the main board |
| the 32 bits | all four registers | — | `cluster/key-marker-and-bits` | `marker-bits`, `free-bits` | Allocated in `config/key-layout.yaml`. The chain order is unchanged |

Pin numbers in this table are the **main-board** header's. The key board's
header numbers the same conductors differently — see *The ribbon*, below.

---

## The sheet, and which board places what

**The source is [`key-chain-loom.kicad_sch`](key-chain-loom.kicad_sch)**
(ADR 0019; render [`key-chain-loom.sch.png`](key-chain-loom.sch.png)).
[`netlist.yaml`](netlist.yaml) is exported from it
(`python3 tools/kicad.py export hardware/interfaces/key-chain-loom`) and must
not be edited. The sims read it (`sim/`). It was first written from the
hand-written netlist and compared with it part by part and net by net: no
change. The three hops, `CHAIN_QH_RT` and `DEV_3V3` each carry two ports.
On the sheet each is one wire between its two port labels, named by a local
label at its middle. A local label outranks a port label in KiCad's naming,
and `tools/kicad.py` reads the ports off the wire (`label_groups`).

**No board places this sheet, and none can as it stands.** KiCad places a
sheet whole, and this one is both ends of two ribbons: three boards, joined
by a cable that is not a part. Each board draws its own parts:

| Part on this sheet | BOM row | Board | On that board today |
|---|---|---|---|
| `J-CHAIN-MAIN-RH`, `J-CHAIN-MAIN-LH` | `J-CHAIN` | `hardware/boards/main-board` | `J5` (rail pin on `V3V3_CHAIN_RH`), `J4` (`V3V3_CHAIN_LH`) |
| `R-CHAIN-SER-SCK`, `-SHLD`, `-SER` | `R-CHAIN-SER` | `main-board` | `R34`, `R35`, `R36` |
| `R-SER-TERM` | `R-SER-TERM` | `main-board` | `R37` |
| `FB-CHAIN-RH`, `FB-CHAIN-LH` | `FB-CHAIN` | `main-board` | `FB2`, `FB1` |
| `U-TVS-CHAIN` | `U-TVS-CHAIN` | `main-board` | `U9` |
| `J-CHAIN-KEY-RH` | `J-CHAIN` | `hardware/boards/key-board-rh` | `J1` |
| `J-CHAIN-KEY-LH` | `J-CHAIN` | `hardware/boards/key-board-lh` | `J1` |
| `CBL-CHAIN` ×2 | `CBL-CHAIN` | no board: straight conductors, netted as the pins they join | — |

`C-BULK-CHAIN` is not on this sheet: it is each key board's own part, on its
root sheet.

**What holds the boards to this sheet.** `tools/kicad.py check` holds every
`J-CHAIN`, on all three boards, to this sheet's pin map (`check_chain`). On the
main board `GND_CHAIN` is `PWR_GND` and `DEV_3V3` is itself. The main board's
series resistors, terminator, beads and clamp are held by nothing. They were
compared with this sheet by hand on 2026-09-29, pin by pin, and agree
`[repo, board-netlist.yaml]`. **Open**, decided by the board owners: split
this sheet into a main-board end (everything but the two key-board headers)
that the main board places once, or extend `check_chain` to those seven
parts.

---

## The chain

*Connectivity is **[`key-chain-loom.kicad_sch`](key-chain-loom.kicad_sch)**,
not these drawings, and [`netlist.yaml`](netlist.yaml) is exported from it. It
holds the hop map — which register's `QH` feeds which register's `SER`, and
over which ribbon — as named nets. The register itself is one schematic built
four times ([`key-register`](../../cluster/key-register/netlist.yaml),
`replicated: 4`), so its side of each hop is per instance, and
`hardware/nets.yaml` marks those nets `per_board:`.*

The order is `config/key-layout.yaml`'s, unchanged: **bit 0 is the first bit
clocked out**, the `QH` of `right_thumb`, the device nearest the MCU, and
serial data flows toward the clock source (ADR 0001 fix 3) `[repo]`:

```
   MCU ◄── right_thumb ◄── right_hand ◄── left_thumb ◄── left_hand ◄── chain end
            (main)          (key board)     (main)         (key board)   IO33 / pull-up

   ┌─────────────────────────── MAIN BOARD ──────────────────────────────┐
   │                                                                     │
   │  IO40 ◄─ QH (RT) SER ◄─┐        ┌─► SER (LT) QH ─┐      IO33 ─┐     │
   │                        │        │                │   + pull-up│     │
   │             ┌─ pin 8 ──┘        └── pin 8 ─┐     │            │     │
   │             │  pin 6 ◄─────────────────────┼─────┘            │     │
   │             │  (right_hand J-CHAIN)        │  pin 6 ◄─────────┘     │
   │             │                              │  (left_hand J-CHAIN)   │
   └─────────────┼──────────────────────────────┼────────────────────────┘
       CBL-CHAIN, cond. 6 out / 8 back  CBL-CHAIN, cond. 6 out / 8 back
   ┌─────────────┴─────────────┐    ┌───────────┴───────────────┐
   │ KEY BOARD right_hand      │    │ KEY BOARD left_hand       │
   │  7 ──► SER (RH) QH ──► 5  │    │  7 ──► SER (LH) QH ──► 5  │
   └───────────────────────────┘    └───────────────────────────┘
   (pin numbers inside the key-board boxes are the KEY BOARD's own J-CHAIN
    pins, 13 − k for conductor k; everything above them is main-board
    numbering)

   SCK, SH/LD, 3V3 and the grounds are one net each, on every register and
   on both ribbons. Each ribbon carries its key board's SER IN on conductor 6
   (key-board J-CHAIN pin 7) and its QH OUT on conductor 8 (key-board pin 5).
```

**The existing 12-way pinout already does this, and is kept.** Each ribbon is
a single hop out and a single hop back: the key board's serial input on
conductor 6 (key-board `J-CHAIN` pin 7) and its serial output on conductor 8
(key-board pin 5), with a ground either side of both in the ribbon.

**No serial-input link is needed on any board.** The four-board design had a
solder link on every cluster board to choose where `SER` came from, because
the chain-end board was different ([`notes.md`](notes.md)). Now each key board
has one connector and its `SER` is **always** conductor 6 — key-board
`J-CHAIN` pin 7 — whatever drives main-board pin 6. Both key boards are identical in the chain;
the difference between the right-hand and left-hand hop is two traces on the
main board, which is one board with one layout anyway.

**The chain order no longer costs anything to follow.** Every key board's hop
is its own ribbon and back, so any order of the four devices uses the same two
ribbons and the same four connectors. The earlier proposal to swap `left_thumb`
and `left_hand` to save a body-thickness crossing has nothing left to save,
and `key-layout.yaml`'s order stands.

### The main-board end

```
  from the MCU                  J-CHAIN, main board, BOTH ribbons
  (MCU board pins)              (2×6 1.27 mm shrouded IDC, right-angle)

   IO38  ──[R-CHAIN-SER 100R]──────► 2 SCK    both ribbons, and RT/LT CLK

   IO7   ──[R-CHAIN-SER 100R]──────► 4 SH/LD  both ribbons, and RT/LT SH/LD

   IO33  ──[R-CHAIN-SER 100R]──┬───► 6 SER    LEFT_HAND ribbon only
                               │     (right_hand ribbon: 6 = LT's QH)
                        [R-SER-TERM 10k]
                               │
                              3V3     (the pull-up is on this net only)

   IO40  ◄───────────────────────── RT's QH  (a trace; no connector)
                                     8 QH    right_hand ribbon: RT's SER
                                             left_hand ribbon:  LT's SER

   3V3   ──┬─────────────────────────► RT/LT VCC and R-SER-TERM (DEV_3V3)
           ├──[FB-CHAIN 600R]──────────► 10 3V3  right_hand ribbon
           └──[FB-CHAIN 600R]──────────► 10 3V3  left_hand ribbon
   GND   ─────────────────────────────►  1 3 5 7 9  both ribbons
                                         11 12  spare

   [U-TVS-CHAIN SP0504BAHTG] on SCK, SH/LD and the chain-end SER, to GND_CHAIN,
   at the left_hand J-CHAIN; its fourth channel is spare. Fitted (ADR 0018).
```

### The key-board end

```
   J-CHAIN, key board              U-KEYS on this key board
   conductor k = key-board pin 13 − k — see below
   cond. 2  = pin 11  SCK   ───────►  CLK
   cond. 4  = pin 9   SH/LD ───────►  SH/LD
   cond. 6  = pin 7   SER   ───────►  SER (pin 10)
   cond. 8  = pin 5   QH    ◄───────  QH  (pin 9)
   cond. 10 = pin 3   3V3   ───────►  VCC, pull-ups, marker straps
   cond. 1 3 5 7 9  = pins 12 10 8 6 4   GND
   cond. 11 12      = pins 2 1           spare, unconnected

   No link, no pull-up, no choice: both key boards are this drawing.
```

---

## The ribbon — connector, cable, fold and pin numbering

**The parts** (owner, 2026-09-27; ADR 0017's amendment). `J-CHAIN` is a
2×6, 1.27 mm pitch, **shrouded, keyed, right-angle, through-hole** IDC
header; the stand-in is Samtec SHF-106-01-L-D-RA
`[datasheets/connectors/SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf, the full print]`.
`CBL-CHAIN` is a flat IDC ribbon, 12 conductors at 0.635 mm, with a 2×6 IDC
socket at each end, bought as an assembled length; the stand-in is Samtec
**FFSD-06-D-xx.xx-01-N-RN2** — `xx.xx` is the length code below, in
inches, and **`-RN2`, the notch reversed on the second socket, is what sets
the pin map and which way each end's cable leaves** (below)
`[datasheets/connectors/SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf, sheet 2 fig 3]`. Their envelopes are `config/body.yaml` `boards.chain_hdr_*` and
`boards.chain_plug_*`, and the ribbon's `routing.chain_ribbon_w` / `_t`.
**Through-hole** is the owner's reason for the change: the cable's pull goes
into the board, not into SMT pads.

**Where they sit** — `mechanical/DESIGN.md` and the model `[repo]`: on each key
board the header hangs from the board's **underside directly over the main
board's header** — stacked, at the same position along the body — both in the
far band beside the LED row, **both mouths facing the same way along the
body**. Each header stands `boards.chain_hdr_h` off its board with its mouth
centred `boards.chain_hdr_mouth_z` above it; its pin rows are **behind the
body's back face**, the tails bending down behind it (`boards.chain_hdr_pin_back`,
from the mouth); a mated socket stands `boards.chain_plug_proud` out of the
mouth (tbd). That stand-out decides whether the cable clears the shroud's
mouth at all, not only where the ribbon folds: the cable leaves the socket a
little inside its back face, so a socket that stands out less than estimated
can pinch the cable on the shroud. It is measured on the first mated pair.
The key header's pin tails come up through the key board toward the grounded
key plate and **stop short of it**: the plate has no window over them
(`drc.echo` "J-CHAIN pin tails clear of the key plate"). The model places
both headers clear of the switches (`drc.echo` "chain headers on the
left_hand boards clear of the switches", and the `right_hand` rule).

**How the ribbon lies closed** `[repo]`: with `-RN2`, **the main board's
socket's cable leaves upward, toward the key board, and the key board's
leaves downward**, so the two exits face each other across the gap between
the plugs (*Pin numbering*, below). Each end turns out along the body and the
ribbon folds back on itself into a **flat hairpin lying along the body,
both legs between the two plugs' heights**, running the same way to the
fold, so it never stands across the LED row's light. Which way each hand's
hairpin folds is `config/body.yaml` `routing.chain_fold`, which says why.
Leg and fold radius: `mechanical/drc.echo` "key-chain ribbon closed:
hairpin leg and fold radius", held to the cable's bend radius by "key-chain
ribbon fold no tighter than its bend radius". Both hairpins are checked
inside the body ("key-chain ribbon hairpin inside the body") and off the
cassette's columns, which stand through the whole gap the hairpin lies in
("key-chain ribbon hairpin clear of the columns"; ADR 0025).

**Why it is as long as it is** (owner, 2026-09-27: long enough "to have the
top off and still connect the ribbon before tightening down"). Since the
cassette (ADR 0025), tightening down is screwing the key plate onto its
columns, on the bench or, in service, once the oak top is cut free. The
service position is the key plate, with both key boards on it, **held raised
straight up off its columns** far enough for a hand to reach the main board's
sockets (`routing.chain_service`, `routing.chain_raise`, plus
`routing.chain_slack`). It is not laid beside the body any more: a ribbon that
long folds into a hairpin that reaches the left-hand board's tail column. The free length is
`mechanical/drc.echo` "key-chain ribbon length (derived)", in millimetres.
**The part is ordered by a different line**: "key-chain cable to order
(FFSD length code)" is the FFSD length field — inches, overall, measured
over both sockets as the print measures it, with its −0.125 in tolerance
already covered — so the order is `FFSD-06-D-<that code>-01-N-RN2`. FFSD is
built to length; there are no stock lengths. **So the key plate comes off by
undoing its column screws, raising it and unplugging the main board's
sockets**; it goes back on by plugging them in with the plate held raised,
then lowering it onto its columns and screwing it down.

**Pin numbering: key-board pin = 13 − main-board pin, and the cable sets
it.** `[datasheet]`, both full prints banked:

1. **A keyed IDC socket always mates its position k to header pin k.** So
   which main-board pin reaches which key-board pin is set by **how the cable
   assembly is built**, not by the headers.
2. **On an FFSD cable, the first socket's cable leaves on the side of its
   key and the second's on the side away from it; `-RN2` reverses the
   second's notch, so both sockets' cables leave on their key's side**
   (FFSD print sheet 1 fig 1, sheet 2 fig 3). The main board's header is
   upright, its key slot in the odd-row wall, away from the board (SHF
   print), so that socket's cable leaves **upward**, toward the key board.
   The key board's header is the same part upside down on the key board's
   underside, its slot facing down, so that socket's cable leaves
   **downward**. The two face each other.
3. **The cable is ordered `-RN2`.** Both ends are then built alike, so either
   end may go on either board; the ribbon runs flat with no twist, and
   conductor k meets key-board pin 13 − k:

```
   conductor k  =  main-board J-CHAIN pin k
                =  key-board J-CHAIN pin 13 − k

   k:        1    2    3    4    5    6    7    8    9   10   11   12
   signal:  GND  SCK  GND SH/LD GND  SER  GND  QH   GND  3V3  sp   sp
   key pin: 12   11   10    9    8    7    6    5    4    3    2    1
```

**The key boards' KiCad sheets carry that map** (their exported
`hardware/boards/key-board-*/board-netlist.yaml` confirm it), and
[`netlist.yaml`](netlist.yaml) nets the ribbon by it. Place the standard
footprint on the key board's bottom side; do not hand-mirror it — the map is
in the netting, and mirroring the footprint as well would undo it. **A standard cable,
without `-RN2`, fits and looks right, and is wrong**: plugged with its
second socket on the main board, both ends' cables leave downward and the
ribbon takes a half-twist it absorbs unnoticed, and conductor k meets
key-board pin k — conductor 10's 3V3 on pin 10, a ground, and `SH/LD` and
conductor 6's signal on grounds too `[datasheet, both full prints; calc]`. **A cable whose ends both leave downward is a standard cable.**
Nothing mechanical shows it, so every cable is metered before it is first
powered (*Still open*, and the key board's README, *Bring-up*).

**What the header does to "a ground between every signal".** In the **ribbon**
every signal conductor has a ground on both sides, which is ADR 0001's rule
and the reason for the pinout. In the **header** the rows split it `[calc]`:
on the key board the signals and 3V3 are the odd pins (one row) and the
grounds the even pins (the other row); on the main board it is the other way
round. A ground sits between signals **along the ribbon, not along the header
row** — a few millimetres of adjacency inside the connector, not a return
path, and the same for any 2-row IDC part.

**The short this design can still have.** The shroud is keyed and takes the
socket only one way and on pitch, so a socket seated skewed across its
neighbours is not the failure to plan for. What is left is a socket forced or a
ribbon pinched at reassembly, across the 3V3 conductor (10) and its ground
neighbour (9). It is a service event: the sockets are plugged every time the
lid goes back on. What covers it is the source's own current limit (below).

---

## The chain-end serial input, and the self-test

`R-SER-TERM` moves to the **main board**, on the `left_hand` ribbon's pin 6,
on the connector side of `IO33`'s `R-CHAIN-SER`:

```
   IO33 ──[R-CHAIN-SER 100R]──┬──► left_hand conductor 6 ──► LH register SER
                              │
                      [R-SER-TERM 10k]
                              │
                             3V3
```

**Decided: the main board, because that keeps the two key boards identical.**
On a key board it would have to be fitted on one and not the other — a board
variant, which is what the old solder link existed to avoid.

It still does what it did. Undriven, it holds the chain-end input high — the
tied-off case ADR 0001 specified. **Driven**, `IO33` wins through 100 Ω
against 10 kΩ `[calc]`: `3.3 V × 100 / 10 100 = 33 mV` from the rail. So an
end-to-end chain self-test — shift a known pattern in at `left_hand` and read
it back at `right_thumb` with no keys pressed — is **a firmware choice, not a
board choice**. It is worth more than it was: the pattern now crosses **both
ribbons in both directions**, so it tells "a ribbon is unplugged" from
"one bit is stuck", which the static marker cannot. Fit the resistor; E4
decides whether firmware uses it.

---

## The protection parts, and the fuse that is not there

All three were proposed against a 265 mm loom that ran beside the LED strip's
12 V feed. That loom is gone (ADR 0016 moved the strip onto the main board;
ADR 0017 put the thumbs there too), so each was re-derived against the chain
as it now is ([`notes.md`](notes.md)). The owner decided two of them on
2026-09-26 ([ADR 0018](../../../docs/decisions/0018-main-board-wiring-decisions.md));
`R-CHAIN-SER` is still E14's.

**`R-CHAIN-SER` — still has a job, for a different reason.** `[calc]`, with two
inputs `[from memory]`: an MCU output edge of ~2 ns, and ~6 ns/m on FR-4 and
ribbon cable. A net behaves as a lump while its one-way delay is under about a
sixth of the edge:

```
   2 ns / 6 = 0.33 ns    →    0.33 ns / (6 ns/m) = 56 mm
```

`SCK` and `SH/LD` are single nets that run the main board — its length is
`mechanical/drc.echo` "main board (derived)", several times 56 mm — to two
registers and two ribbons (each `drc.echo` "key-chain ribbon length
(derived)" long). A fast edge sees that as a branched line, and a ring through the
register's threshold on `SCK` is a double clock that shifts the whole word. The
100 Ω at the source slows the edge and damps the ring; it is not series
termination, which ADR 0001 rejected for a line that drops on several loads.
**Open, decided at E14**: scope `SCK` at the `left_hand` register on the real
main board and ribbons. It is three 0805s either way.

*(The registers' own `QH` edges are not a lump by the rule above, and do not
need to be. TI publishes their transition time as a maximum only — 5 ns at
4.5 V and 25 °C, 8 ns over temperature `[datasheets/logic/SN74HCS165-ti-scls828a.pdf
p.8]` — and warns that the outputs "may create fast edges into light loads"
`[same, p.11 §8.3.1]`. Even the 5 ns maximum gives `[calc]` 5 / 6 = 0.83 ns →
0.83 / 6 ns/m ≈ 139 mm, and a hop is a ribbon plus key-board and main-board
traces, longer than that. What makes a hop safe is that `QH` → next `SER` is
data, sampled at the next rising `CLK` a whole period (1 µs) later, against
`SER` setup of at most 14 ns and hold of 0 ns `[same, p.7]`, into a Schmitt
input `[same, p.6]`: a ring whose round trip is a few nanoseconds has settled
long before `[calc; judgment, not measured]`. The edge-sensitive nets are
`SCK` and `SH/LD`, above. If E4 or E14 shows otherwise, LVC with source
termination is ADR 0001's way back.)*

**`U-TVS-CHAIN` — fitted, for service.** The ribbons never leave the body
and sit under the grounded plate, so in play nothing reaches them. The
contacts are handled when the lid is off and a socket is unplugged, and a
main-board `J-CHAIN` header then exposes three MCU pins through their 100 Ω — `SCK`,
`SH/LD` and the chain-end `SER` — which is where the array is netted, at the
`left_hand` `J-CHAIN`, which carries all three. The chain's `QH` into the MCU
is `right_thumb`'s and reaches no connector. **Decided: fit it** (ADR 0018).
The exposure is real every time the lid is off, the part cannot be added once
the board is made, and it costs pennies.

**It guards the MCU's pins only, and that is accepted.** The hop nets
(`HOP_LH_LT`, `HOP_LT_RH`, `HOP_RH_RT` in [`netlist.yaml`](netlist.yaml)) and
every signal pin of a key board's `J-CHAIN` land on register pins, not on the
MCU. The key board has no ESD part of its own. Those pins carry the
SN74HCS165's own rating, ±4000 V HBM (ANSI/ESDA/JEDEC JS-001) and ±1500 V CDM
`[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.4]` — a component rating for
manufacturing handling (TI's footnote to the same table: "500-V HBM allows
safe manufacturing with a standard ESD control process"), not a system-level
IEC 61000-4-2 rating for a contact touched with the lid off. **The exposure
is accepted, not protected**: a register is a part on a board that can be
replaced, where an MCU pin is not. **The fourth channel
stays spare**: there are three hops, on two ribbons, and one channel cannot
cover them.

**No fuse — the short is protected at its source.** The chain's 3V3 is the
Matrix's 3V3 pad, from its ME6217C33M5G LDO (`DEV_3V3`, the instrument's only
3V3 and the MCP3202's reference) `[repo] datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf`,
[`netlist.yaml`](netlist.yaml). The short this design can have is a socket
forced or a ribbon pinched across conductors 9/10 at reassembly (above). **What limits it is the
LDO itself** `[ds ME6217C33M5G p.1, p.4]`: p.1 describes "a built-in
overcurrent protector" and thermal shutdown at 160 °C, and the p.4
electrical characteristics give a short-circuit current `Ishort` of **350 mA
typical at `VOUT` = 0 V — typical only, with no minimum or maximum.** So the
limit is stated but not guaranteed. **Verify at E1:** short one ribbon's 3V3
to ground through 1 Ω at a main-board `J-CHAIN` (≈ 0.35 V across it at the
typical limit `[calc]`), confirm the rail limits rather than the LDO failing,
and confirm the Matrix restarts once the short is removed.

The symptom is immediate and on the bench: the whole 3V3 rail collapses, so
the Matrix does not start at all — not a dead key board — and it is seen
before the key plate is screwed down onto its columns.

**`FB-CHAIN`, one per ribbon, is isolation, not protection** (ADR 0018). A
ferrite bead in series with each ribbon's conductor 10 on the main board keeps
a key board's register edges off the rail that is also the ADC's reference;
`right_thumb`, `left_thumb` and `R-SER-TERM` stay on `DEV_3V3` directly. It is
chosen for a low `DCR` — at the chain's whole `key-scan-current` (every key
closed) a 0.1 Ω bead drops under 3 mV `[calc]` — and for a rated current above the LDO's short-circuit
current, because during a short it carries that. `≥ 600 Ω` at 100 MHz is
`[from memory]`; the part is now Murata's BLM21SP601SN1D (its row says why, and
names a second source). **Simulated** (`sim/`, 2026-09-28), with Murata's own
model of that part, which is banked. Below its resistive band the bead is
several microhenries, **not** the ~1 µH this page once assumed. Against the key
board's 100 nF `C-DECOUPLE-165` it forms a lightly damped LC, below the chain's
clock; its frequency and peak are in `sim/results.yaml` (`rail-impedance-*`).
The simulation shows two things:
- **The ring stays small.** The key board's rail stays inside its limit through
  a clock burst and every key closing at once, at every corner, with
  `C-BULK-CHAIN` fitted (`rail-as-ordered`) and without it (`rail-without-bulk`).
- **Nothing reaches the reference.** The key board's clocking moves `DEV_3V3`,
  the MCP3202's reference, by under one LSB.

So the rail does not need the bulk capacitor, and it is fitted anyway (owner,
2026-09-28): a 10 µF 0805 costs cents, and its ESR damps the LC. Murata states
the bead's model for 1 MHz to 3 GHz, so at the LC's frequency it is
extrapolated: **bring-up step 6 still scopes the key board's VCC while
shifting**, against the simulation.

---

## What the main board still owes the chain

**The 3V3 rail, and it is a real load on the ADC's reference**: every closed
key draws its pull-up's current, and the whole chain's, every key closed, is a
step at play rate — both are `key-scan-current`, stated on
[`key-switch-network.md`](../../cluster/key-switch-network/key-switch-network.md).

Unchanged by this rework — the same pull-ups (`key-pullup-qty`) on the same
rail. It lands on the MCP3202's reference and is accepted as a gain term; the
argument is `carrier.md` §2's, and the numbers are
[`key-switch-network`](../../cluster/key-switch-network/key-switch-network.md)'s.

**A ground return per clocked signal** `[repo] 0001 fix 1`, on the main board
as on the ribbons: route `SCK` and `SH/LD` over unbroken ground, away from the
LED row's data and 12 V feed and the breath signal (ADR 0017's routing note).

### The 32 bits, and which board each is on

From `config/key-layout.yaml` `[repo]`:

| Device | Bits | Board |
|---|---|---|
| `right_thumb` | 0–7 | **Main board** |
| `right_hand` | 8–15 | Key board, right-hand ribbon |
| `left_thumb` | 16–23 | **Main board** |
| `left_hand` | 24–31 | Key board, left-hand ribbon |

The allocation within each device — switches, the two reserved spare-switch
positions, the marker straps and the free bits — is
[`key-marker-and-bits`](../../cluster/key-marker-and-bits/key-marker-and-bits.md)'s,
and none of it moved.

---

## Still open

- **The `J-CHAIN` part**, decided at M4: a 2×6 1.27 mm shrouded, keyed,
  right-angle through-hole header inside `boards.chain_hdr_*`, the same part
  at all four positions (stand-in Samtec SHF-106-01-L-D-RA, full print
  banked). The pin map is the cable's, not the header's (above).
- **The `CBL-CHAIN` part**, decided at M4: stand-in Samtec
  `FFSD-06-D-<code>-01-N-RN2`, assembled, where `<code>` is `drc.echo`
  "key-chain cable to order (FFSD length code)", in inches. **Meter every
  cable before it is first powered**, not only the first: conductor 10 must
  reach the far socket's position 3, and conductor 2 its position 11. A
  standard cable goes in without any mechanical sign (above).
  `boards.chain_plug_proud` is measured on the first mated pair; it decides
  whether the cable clears the shroud's mouth.
- **`R-CHAIN-SER`** (E14) — above. **`U-TVS-CHAIN`** and the fuse are
  decided (ADR 0018); what is left of them is two tests — the LDO's short
  limit at E1 and `FB-CHAIN`'s ring at E14 — and the bead's part number.
- **The main board's hop inputs float with a ribbon unplugged.** With a ribbon out,
  `right_thumb`'s or `left_thumb`'s `SER` — the main-board end of that
  ribbon's pin 8 — has nothing on it. It costs nothing in play (the lid is on)
  and the markers show the missing board as a failed frame, not a wrong note.
  **Decided by** whether the main board is ever run with a ribbon unplugged at
  bring-up for long enough to care; if so, a pull-up on each ribbon's pin 8 at
  the main board.
