# Real-time carrier — schematic

**Status:** **First draft 2026-09-21; §3 rebuilt the same day** after ADR 0001
moved the shift registers back to the cluster boards. The draft was written
against the tail-register topology and every figure that depended on it — the
block diagram, §3, the loom count, the component table — has been redone. Not
checked against a single datasheet — `waveshare.com`, `ti.com`, `nxp.com` and `analog.com` were all
blocked from this sandbox. Read it as a proposal with its uncertainties marked,
not as a design.

The instrument's support circuits. They have no MCU (ADR 0013): a Waveshare
ESP32-S3-Matrix on the lid, under its window at the tail (§7), connects to
them by a flat ribbon soldered to its pad rows and plugged into `J-MCU` on
this board (ADR 0017), and everything else here is passive, slow, or analog.

> **There is no carrier board (owner, 2026-09-26).** These circuits are built
> on **the main board** (ADR 0017): one long board at the thumb level that
> also carries the thumb switches and their registers, with the key boards
> connected to it by 1.27 mm IDC ribbons (`mechanical/DESIGN.md`). The block
> diagram and §§ below describe the circuits, which have not changed; where a
> line talks about "the board", read the main board. Its size and the room its
> parts have are in `mechanical/drc.echo`. The breath sensor is at its mouth
> end, so the buffered breath signal runs the board's length (ADR 0017).

Evidence marking follows the module pages: `[repo]` names a file, `[calc]` shows
the arithmetic, `[from memory]` means **I could not open the datasheet and you
must check it before ordering.** `[board-def]` means an open-source board
definition file fetched in this session and named.

**Where a value is not known, the row says `TBD` and says what decides it.**
There are more of those here than is comfortable. That is the correct state for
a page written on a day when nothing could be verified; the gap list is
`docs/review/2026-09-21-schematic-review/S3-carrier.md`.

## One dev board

**There is one dev board, the ESP32-S3-Matrix, and one regulator** (owner,
2026-09-26, ADR 0015: the display board was removed, and the 8×8 matrix is the
instrument's only display). This page draws its one connector, `J-MCU`, and
the ribbon to it (*The Matrix and the umbilical at the tail end*, below).

---

## Block diagram

```
                              TAIL FACE
   ┌─────────────────────────────────────────────────────────────┐
   │  etherCON J-UMBILICAL-INST, on its adapter, behind the cap  │
   │  USB-C receptacle ── CBL-USB-EXT to the Matrix's own port   │
   └──────────────┬──────────────────────────────────────────────┘
                  │ PCB-UMB-ADAPTER: 8 tracks, pin N to pin N (ADR 0021)
                  │
   ┌──────────────▼──────────────────────────────────────────────────────┐
   │ J-UMB   1 BREATH   2 AGND   3 +12V   6 PWR_GND   4 SCLK   5 MOSI      │
   │         7 CS       8 DIG_GND                                        │
   └───┬──────────┬──────────────┬─────────────────────┬─────────────────┘
       │          │              │                     │
   ┌───▼──────────▼───┐   ┌──────▼──────┐        ┌─────▼──────┐
   │ ANALOG FRONT END │   │ POWER ENTRY │        │ SPI EGRESS │
   │  §2              │   │  §1         │        │  §4        │
   └──────────────────┘   └──────┬──────┘        └─────┬──────┘
                                 │                     │
              +12V ──────────────┼─────────────────────┼──── J-LED (strip)      
               5V ───────────────┤                     │
                                 │                     │
       ┌─────────────────────────▼─────────────────────▼──────────────┐
       │  J-MCU — CBL-MCU-RIBBON to the ESP32-S3-Matrix, on the lid   │
       │   5V×3 GND×4 3V3 | IO7 … IO1 | IO33 … IO40 | IO43 IO44       │
       │   EN IO0 (button pads) | IO2 IO3 spare — 24 conductors       │
       │   (onboard: IMU GPIO10-13, 8×8 matrix GPIO14, USB GPIO19/20) │
       └──┬──────┬──────────┬────────────┬───────────┬────────────────┘
          │      │          │            │           │
      3V3 │  SPI3+latch  SPI2+2×CS   IO1          IO43/IO44, EN/IO0
          │      │          │            │           │        │
   ┌──────▼──────▼───┐   ┌──▼────────┐ ┌─▼────────┐ ┌▼────────▼──────┐
   │ CHAIN DRIVE §3  │   │ ADC  §2   │ │'125  §5  │ │ SERVICE  §6    │
   │ + RT, LT thumb  │   │ MCP3202   │ │ LED data │ │ HDR-SERVICE    │
   │   registers     │   └───────────┘ └──────────┘ └────────────────┘
   └───┬─────────────┘
       │
   right_thumb, left_thumb registers on this board; J-CHAIN to each key board
```

---

*§1 power entry — the reverse shunt, the TVS, the two R-78E5.0 bucks, the OR
diodes, the strip bulk, the plate bond and the input-LC damping analysis —
moved verbatim to
[`power-entry-instrument/`](power-entry-instrument/power-entry-instrument.md).*

---

## §2 Analog front end — sensor, reference, buffer, ADC

*Connectivity for **this board itself** — the dev board, `J-MCU` and the
SPI egress in §4 — is [`netlist.yaml`](netlist.yaml), beside this page. The
analog front end drawn below is **three other circuits' parts**, declared
`foreign:` there and netlisted in
[`breath-excitation-reference/`](breath-excitation-reference/breath-excitation-reference.md),
[`breath-adc/`](breath-adc/breath-adc.md) and
[`../interfaces/breath-sense-link/`](../interfaces/breath-sense-link/breath-sense-link.md)
against this drawing. Where a netlist and this drawing disagree, the netlist
wins.*


```
  +12V ──[R-REF-IN 330R 1%]──┬── REF_VIN      the reference's input clamp:
                             │                the rail's TVS lets through more
                  [D-REF-CLAMP 15V zener]     than the REF5050's VIN may see
                             │                (breath-excitation-reference.md)
                        AGND-local

          REF5050                  ½ OPA2197  "reference buffer"
REF_VIN──┬─┤VIN VOUT├─┬── 5.000 V ─┤+IN                         U-BREATH
         │            │            │              R-ISO-REF     pin 2 VS
    [C-REF-OUT#1]  [C-REF-OUT#2]   │     OUT ───┬──[37.4 Ω]───┬──── = the
      10 µF          10 µF   ┌─────┤−IN         │             │     sensor's
    [100 nF]       [100 nF]  │     └────────────┘             │     excitation
         │            │      │                                │
    AGND-local   AGND-local  │                            [100 nF]
                             │  two feedback                  │
                             │  paths:                    AGND-local
                             │                                │
       DC ─[R-FB-REF 10 kΩ]──┤◄─────────────────┼─────────────┤
       AC ─[C-FB-REF 1 nF]───┤◄─[R-FBX-REF 100Ω]┘             │
                                                              │   U-BREATH MPXV4006DP
                                                              │   case 1351-01, SMT,
                                                              │   soldered down
                                                              │   P1 ◄── breath tube
                                                              │           + PTFE plug
                                                              │           + ≤1 mL trap
                                                              │   P2 ◄── OPEN TO CAVITY
                                                              │           never blocked
                                                              │
              MPXV4006DP Vout  0.265 – 4.86 V ────────────────┘
                     │
                     ├──[½ OPA2197 buffer]──┬──[R-SER-BREATH-INST 1k]── J-UMB pin 1
                     │   (V+ = +12V)        │        R1                  BREATH
                     │                      │        [D-TVS-BREATH 12 V standoff]
                     │                      │
                     │                      └──[R-ADCDIV-U 10k]──┬──[R-ADCDIV-L 15k]──┐
                     │                                           │                    │
                     │                            [C-AA-ADC 47 nF C0G]              AGND
                     │                                           │                  -local
                     │                                           │
                     │                                     ┌─────▼─────────┐
                     │                                     │ MCP3202  CH0  │
                     │                                     │ VDD/VREF = 3V3│
                     │                                     │  from the dev │
                     │                                     │  board's LDO  │
                     │                                     │ CH1 = spare   │
                     │                                     └───┬───────────┘
                     │                                    [100 nF] [C-ADC-BULK 10 µF]
                     │                                         │
  J-UMB pin 2 AGND ──[R-SER-BREATH-INST 1k]──┴── analog star point
                       R1b  ** WAS MISSING **      │
                                                   └──[single tie]── PWR_GND
                            [D-TVS-BREATH ×2, AT THE CONNECTOR]
```

*The `R1b` half of this section — the twin in the `AGND` leg, the link-CMRR
argument for it, and the correction it files against the receive page's own
case for the part — moved verbatim to
[`../interfaces/breath-sense-link/`](../interfaces/breath-sense-link/breath-sense-link.md),
which holds both ends of the breath sense chain. The drawing above stays here.*

*The `R-ISO-REF` half of this section — the compensation network, why TI's
Figure 56 transfers, and what it buys — moved verbatim to
[`breath-excitation-reference/`](breath-excitation-reference/breath-excitation-reference.md),
along with the record of the two blockers that closed with it. The drawing
above stays here because it is one connected picture and dividing it would mean
redrawing it.*

*"Two things this drawing settles that no ADR does" — the analog star point
with `AGND` as sense-only, and the absent band-limit capacitor at the
instrument end of `BREATH` — moved verbatim to
[`../interfaces/breath-sense-link/`](../interfaces/breath-sense-link/breath-sense-link.md)
as well. Both are statements about the conductor pair rather than about this
board alone, and the second is answered at the other end of it.*

### The key pull-ups and the ADC reference

*The divider, the anti-alias derivation, the charge-sharing derivation and
`C-ADC-BULK` moved verbatim to [`breath-adc/`](breath-adc/breath-adc.md). This
argument stayed, because it is owned by neither circuit: it is the key chain
loading the ADC's reference.*

**Key pull-ups load that same reference, and they are 4.4× heavier than this
page first costed them** `[calc]` — `R-KEY-PU` is 2.2 kΩ, not the 10 kΩ of the
tail-register draft `[repo] bom.csv`:

```
3.3 V / (2.2 kΩ + 100 Ω) = 1.43 mA per closed key
19 keys closed           = 27.3 mA step on the ADC's reference
at an LDO load regulation of ~0.3 % per 100 mA [from memory]: 0.082 % = 3.4 LSB
```

**The Matrix ribbon adds to it.** The same current reaches this board on
`CBL-MCU-RIBBON`'s one 3V3 conductor, which is also the reference's feed, so it
drops there on top of the LDO's regulation `[calc]`, on the
[tail-end section](#the-matrix-and-the-umbilical-at-the-tail-end)'s
`[from memory]` ~34 mΩ per conductor: `key-scan-current` at 19 closed ×
34 mΩ ≈ 0.93 mV ≈ **1.1 LSB** full scale (0.806 mV per LSB). Its return on
the ribbon's four grounds is a quarter of that — about another 0.3 `[calc:
27.3 mA × 8.5 mΩ = 0.23 mV]`. Same kind of error, same E11 test.

**Still fine, and no longer negligible.** 3.4 LSB is 0.2 % of the ~1594-count
playable span, and because it is the reference moving it is a gain error rather
than an offset — it scales with how hard you are blowing, which is the
direction that hides it. Recorded because the symptom of getting it wrong is
"the breath reading moves when I press keys", which gets blamed on firmware.
See §3 and *Still open*: if this is ever to be removed rather than tolerated,
the fix is a separate rail for the pull-ups or a real reference for the ADC,
and both are board decisions, not firmware ones.

### Mechanical rules that live with this section

- **The sensor is surface-mount and solders straight to the board — no
  socket.** At the board's mouth end, far side from the tube, ports towards
  the tail (ADR 0017). Land pattern, pinout, the swap procedure and why not a
  breakout board: [`breath-sense-link.md`](../interfaces/breath-sense-link/breath-sense-link.md),
  *Mounting*.
- **Both ports on the same face** (case 1351-01) `[ds MPXV4006DP p.7]`. Route
  the tube so it cannot cover, kink or blow adhesive across the reference port,
  and so it does not pull on P1.
- **P1 is the side with the part marking** `[ds MPXV4006DP p.6, Table 3]`:
  marked face up, P1 is the upper port.
- **Mask both ports before `MECH-COAT`** `[repo] 0009`. A sealed reference
  chamber gains ~5.2 kPa when the body warms and the sensor reads as dead.

---
## §3 Chain drive

*§3 is
[`../interfaces/key-chain-loom/`](../interfaces/key-chain-loom/key-chain-loom.md),
which holds the whole chain: the `right_thumb` and `left_thumb` registers on
this board, the two IDC ribbons to the key boards, and this board's
chain parts — `R-CHAIN-SER`, `R-SER-TERM`, `U-TVS-CHAIN`, the two `FB-CHAIN`
and its two `J-CHAIN`. The section number is kept because other pages cite `carrier.md`
§3.*

---

## §4 SPI egress to the umbilical

```
  IO35 SCK  ──[R-SPI-SER 100R]───┬──── J-UMB pin 4   ┐ pair (4,5)
  IO36 MOSI ──[R-SPI-SER 100R]───┼──── J-UMB pin 5   ┘
  IO34 CS   ──[R-SPI-SER 100R]───┼──── J-UMB pin 7   ┐ pair (7,8)
                                 │     J-UMB pin 8 ──┘ DIG_GND ── PWR_GND at J-UMB
                                 │
                        [U-TVS-SPI 4-ch array to PWR_GND]
  IO37 MISO ── MCP3202 DOUT only (never leaves the board)
  IO39 CS   ── MCP3202 CS
```

*The rest of §4 — `R-SPI-SER` and the 100 Ω derivation, the two SPI hosts and
what claims them, the loop budget and the IO_MUX note — moved verbatim to
[`../interfaces/spi-link/`](../interfaces/spi-link/spi-link.md), which holds
both ends of the link. The drawing above stays here: it also carries the
MCP3202's board-local `MISO` and `CS`, and dividing it would mean redrawing it.
The section number is kept because other pages cite `carrier.md` §4.*

---

*§5 LED data — the 74AHCT125 gates, `R-LED-PD`, `R-LED-SER`, `J-LED` and
the WS2815 `V_IH`/`BI` argument — moved verbatim to
[`led-strip-drive/`](led-strip-drive/led-strip-drive.md). §6 service header —
`HDR-SERVICE` — is in [`service-uart/`](service-uart/service-uart.md).*

---

## §7 Dev board mounting and the matrix window

> **Superseded 2026-09-26: the matrix is on the TOP face** (owner, ADR 0009).
> The ESP32-S3-Matrix is **not on a carrier at all**: it sits face up
> against the oak top under a window at the tail, wired to the main board
> by a ribbon soldered to its pad rows and plugged into `J-MCU` (ADR 0017,
> *The Matrix and the umbilical at the tail end* below), so there is no
> cutout to argue about and the underside mounting below is not needed. Its
> USB-C port reaches the tail face through `CBL-USB-EXT`, so no board edge
> has to align with a slot either. `mechanical/renders/main-board.png` shows
> where the circuits went. Kept as the record of the arithmetic that was.

**Proposed: mount the ESP32-S3-Matrix on the carrier's *underside*, LED face
outward, and delete the cutout.** ADR 0009 and ADR 0014 both name underside
mounting as the fallback `[repo]`; this page proposes it as the default, for a
reason that is arithmetic rather than preference `[calc]`, on `[from memory]`
inputs that E1 will replace:

```
8×8 at 2.6 mm pitch (ADR 0014's own figure) → 20.8 mm of emitters
10 header pins at 2.54 mm = 22.86 mm → board ≥ ~25.4 mm in the header direction
Header row spacing must clear the matrix → ~22–25 mm, call it 23.5 mm
Largest hole that fits between the rows on the carrier:
   23.5 − 2 × (0.8 mm pad radius + 0.5 mm clearance) = 20.9 mm
                                        against a ~22 mm requirement
```

A 2-layer carrier with a ~21 mm hole between its header rows has two ~1 mm
strips of copper carrying twenty pins, joined only round the ends of the slot,
with every dev-board signal routed the long way. Mounting the board underneath
removes the hole, removes the routing detour, and puts the LEDs closer to the
diffuser, which ADR 0014 wants anyway ("thin, and close to the LEDs").

**It depends on one fact nobody has: which face carries the matrix relative to
the header rows.** ADR 0009 says "Confirm on arrival" `[repo]`. That confirmation
is now a gate on the board outline. Draw the oak window either way; draw the PCB
cutout as the fallback.

**The USB-C edge must align with the tail-face slot** `[repo] 0009`, on a face
that also carries a ~26 × 31 mm etherCON flange on a face 57 mm wide and `body-thickness` tall. That is a 1:1
paper check at M4, and the ROADMAP already lists it.

---

## The Matrix and the umbilical at the tail end

Two connectors on this board's tail end, one for each thing that is not on it
(owner, 2026-09-26, ADR 0017; `mechanical/DESIGN.md`, clash list item 5;
`mechanical/renders/breakdown-tail-wiring.png`):

```
  ON THE LID                                  BEHIND THE TAIL CAP
  U-MCU-RT  ESP32-S3-Matrix                   J-UMBILICAL-INST  etherCON NE8FAV,
    two pad rows, TP2/TP3, Key1/Key2            soldered to PCB-UMB-ADAPTER
        │                                           │
        │ CBL-MCU-RIBBON, 24-way                    │ the adapter's tracks,
        │ soldered to the pads                      │ pin N to pin N
        │                                           │
        ▼                                           ▼
  J-MCU  2 × 12, 1.27 mm ──── main board, tail end ──── J-UMB  1 × 8, 2.54 mm, right-angle,
                                                        soldered into the adapter and the tongue
```

**`J-MCU` replaces the dev-board sockets.** The Matrix is on the lid, so it
cannot plug into this board; its ribbon is soldered to it and plugs in here,
and it unplugs when the lid comes off. A dead Matrix is still a bench job and
not a strip-down: unplug `J-MCU`, take the lid off, desolder the ribbon and
solder it to the replacement — nothing on this board is touched. The ribbon's
length is `mechanical/drc.echo` *"Matrix ribbon length"* plus build slack;
the builder's notes are on the `CBL-MCU-RIBBON` row.

**Twenty-four conductors, allocated** (owner, 2026-09-26,
[ADR 0018](../../docs/decisions/0018-main-board-wiring-decisions.md)):

| Conductors | Count | At the Matrix | Why |
|---|---|---|---|
| GPIO the instrument uses | 12 | their pads | [`netlist.yaml`](netlist.yaml) |
| 5V | 3 | two on the 5V pad, one on `TP2` (`VCC_5V`) | current, below |
| GND | 4 | one on the GND pad, three on `TP3` (`GND`) | current, and the ADC's reference, below |
| 3V3 | 1 | the 3V3 pad | the Matrix's LDO: the chain's rail and the ADC's reference |
| `EN`, `IO0` | 2 | `Key1` and `Key2` (BOOT), the terminal on the pull-up side | in-place recovery at `HDR-SERVICE` ([`service-uart`](service-uart/service-uart.md)) |
| spare GPIO `IO2`, `IO3` | 2 | their pads | ADR 0009's spare conductors; `IO2`–`IO6` are spare (ADR 0007) |

The pad rows carry one ground pad and one 5 V pad
`[repo] datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-pinout.png`, so the
extra ones land on the vendor schematic's extension pads, `TP2` = `VCC_5V` and
`TP3` = `GND` `[repo] datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf`.
If `TP3` will not take three joints, the three conductors are twisted and
tinned as one joint; each is still its own path to `J-MCU`.

**Current decides the power count.** Fed from the 5 V pad, the Matrix's LEDs
bypass its USB diode (`matrix-led-current`, `power_path`), so nothing on the
Matrix limits their draw short of the firmware clamp. The 5 V and GND
contacts are therefore rated against what the regulator can deliver —
`U-BUCK`'s 1 A (R-78E5.0-1.0,
[`power-entry-instrument`](power-entry-instrument/power-entry-instrument.md))
— not against `matrix-led-current`. `[calc]`, sharing equally: 1 A ÷ 3 ≈
**0.33 A per 5 V contact** and 1 A ÷ 4 = 0.25 A per ground, against ~1 A per
1.27 mm box-header contact `[from memory]`. One of each would have sat at the
limit.

**The ground count is also the ADC's.** The Matrix's 3V3 is the MCP3202's
reference (`carrier/breath-adc`), regulated against the *Matrix's* ground, so
return current in the ribbon's grounds moves that reference against this
board's — a gain error. `[calc]`, on `[from memory]` inputs — a
0.635 mm-pitch ribbon conductor is ~30 AWG, ~0.34 Ω/m; the length is
illustrative, not the model's:

```
100 mm × 0.34 Ω/m          = 34 mΩ per ground conductor
100 mA of return current   → 3.4 mV of ground shift
3.4 mV / 3.3 V × 4096      = 4.2 LSB full scale on the breath ADC, per 100 mA, one ground

at the regulator's 1 A:
  one ground    1 A × 34 mΩ          = 34 mV   → 34 mV / 3.3 V × 4096  = 42 LSB
  four grounds  1 A × (34 mΩ ÷ 4)    = 8.5 mV  → 8.5 mV / 3.3 V × 4096 = 10.5 LSB
```

**~42 LSB full scale on one ground, ~10 on four**, moving with the display.
The four-way split assumes the conductors share equally, which needs equal
lengths and sound joints; E11 — breath output clean while the matrix is
exercised — is what confirms it.

**The pin map** — ribbon conductor n is `J-MCU` pin n
`[from memory: IDC numbering; confirm on the socket's drawing]`, and
[`netlist.yaml`](netlist.yaml) is authoritative:

```
  pin  1 5V     2 GND    3 5V     4 IO1    5 IO2    6 IO7
  pin  7 IO3    8 IO38   9 GND   10 IO35  11 GND   12 IO36
  pin 13 3V3   14 IO34  15 GND   16 IO39  17 5V    18 IO37
  pin 19 IO33  20 IO40  21 IO44  22 IO43  23 IO0   24 EN
```

The order is for the ribbon's length, where conductors sit side by side for
~100 mm; at the header they are millimetres apart. **Every fast line has a
ground, a supply or a static line on both sides**: `IO35` (`SCLK`) between
two grounds; `IO38` (chain `SCK`) between spare `IO3` and ground, and pin 9
is **the ground between the SPI clock and the chain clock**; `IO36`
(`MOSI`) between ground and 3V3; `IO34` (`CS_MOD`) between 3V3 and ground;
`IO7` (`SH/LD`) between the two spares. The board-local lines are covered
the same way — `IO39` between ground and 5V, `IO37` between 5V and `IO33`,
`IO1` (LED data) between 5V and `IO2` — using lines that are quiet in play:
`IO33` moves only for the chain self-test, and `IO44` (`RX`) only with
something on the service header. `IO43` (`TX`) sits between `RX` and `IO0`.
**`EN` is on the edge with only `IO0` beside it**, because the Matrix has no
capacitor on `EN` — `R8` and `Key1` are all that is on its `RESET` net — and
a glitch there is a reset. **The spares must be quiet to shield:** firmware
drives `IO2` and `IO3` low (`firmware/README.md`).

**`J-UMB` is where the umbilical reaches this board** (ADR 0021). The
instrument's etherCON, `J-UMBILICAL-INST`, is soldered to its own small board,
`PCB-UMB-ADAPTER`, behind the tail cap; the adapter's tracks run its pin N to
pin N of `J-UMB`, a right-angle header soldered into the adapter and into a
**tongue** of this board that runs on from its tail end. So every "`J-UMB`
pin N" on these pages is this board's end of the umbilical *and* the same
conductor as the etherCON's pin N, and the pin map is `umbilical-pinmap`
either way. The clamps and the reverse shunt drawn "at the connector" on
these pages are at `J-UMB`, on this board. The +12 V and `PWR_GND` path must
be rated above the module's current-limit trip (`R-ILIM`,
[`umbilical-load-switch`](../module/umbilical-load-switch/umbilical-load-switch.md)),
not only `umbilical-current`. The worst case is not a hard short — that folds
the limit back to the floor the `R-ILIM` row gives — but an overload just under
the trip, which the load switch carries indefinitely. The etherCON's contacts
are the limit, at `J-UMBILICAL-INST`'s rating; `J-UMB`'s header pins carry
more.

**Netlisted where the connector's pin map is.** `J-MCU` is in this board's
[`netlist.yaml`](netlist.yaml), in series with every Matrix net. `J-UMB` is in
[`../interfaces/spi-link/netlist.yaml`](../interfaces/spi-link/netlist.yaml)
beside both etherCONs, because it carries the umbilical's pin map and all
eight of its nets; the carrier's nets reach it as that circuit's ports.
Neither the Matrix's ribbon nor the adapter's tracks are components: each is
straight, with no pin map of its own, so each connector pin shares a net with
the pin at the other end.

---

## Component table

Existing BOM rows are named as they stand; **proposed** rows are new to this
page and have no BOM entry yet.

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-MCU-RT` | ESP32-S3-Matrix | The instrument. On the lid, not on this board; wired by `CBL-MCU-RIBBON` | `[repo]` |
| `J-MCU` | 2 × 12, 1.27 mm shrouded box header, right-angle | The Matrix's connector, at the tail end. Pin map decided (ADR 0018) — *The Matrix and the umbilical at the tail end* | pin map decided; `[from memory]` part; part **open**, M4 |
| `CBL-MCU-RIBBON` | 24-way flat ribbon, 0.635 mm | Soldered to the Matrix's pad rows, `TP2`/`TP3` and its two button pads; IDC socket into `J-MCU` | `[repo]` pad map and schematic; `[from memory]` ribbon; part **open**, M4 |
| `J-UMB` | 1 × 8, 2.54 mm right-angle pin header | Where the umbilical reaches this board, on its tongue: soldered into it and into `PCB-UMB-ADAPTER` (ADR 0021); `interfaces/spi-link`'s row | `[from memory]` envelope; part **open**, M4 |
| `J-UMBILICAL-INST`, `PCB-UMB-ADAPTER` | NE8FAV on its adapter board | The instrument's etherCON behind the tail cap, and the board that carries it to `J-UMB`; `interfaces/spi-link`'s rows | `[ds]` NE8FAV; adapter **open**, M4 |
| `U-KEYS`, `R-KEY-PU`, `R-KEY-SER`, `C-KEY`, `C-DECOUPLE-165` | — | **Half of them are on this board since ADR 0017**: the `right_thumb` and `left_thumb` clusters. The other two clusters are on the key boards. Counts per cluster are `cluster-boards.md`'s component table | `[repo] 0017, bom.csv` |
| **`R-CHAIN-SER`** ×3 | **100 Ω** | **Open — series at the driving end on `SCK`, `SH/LD` and the chain-end `SER`. Edge-rate damping, not termination; E14 decides. `key-chain-loom.md`** | open |
| `U-TVS-CHAIN` | SP0504BAHTG, 4-ch array, SOT-23-5 | **Fitted** (ADR 0018) — the three MCU nets the ribbon connectors expose, for service handling with the lid off; fourth channel spare. `key-chain-loom.md` | candidate |
| `FB-CHAIN` ×2 | Ferrite bead, 0805, low DCR | One per key-board ribbon on its 3V3 conductor: isolation. **No fuse** — a skewed ribbon's short is limited by the Matrix LDO itself (ADR 0018). `key-chain-loom.md` | part **open** |
| `U-BUF` | OPA2197IDR | ½ reference buffer, ½ breath buffer, both on +12 V | `[repo]` |
| `U-BREATH` | MPXV4006DP, case 1351-01, surface mount, soldered down | P1 to the tube, P2 open to the cavity | `[ds]` pp.1, 6, 7 |
| `R-SER-BREATH-INST` | 1 kΩ | Output protection. **No series cap here** | `[repo]` |
| `D-TVS-BREATH` ×2 | 12 V standoff, SOD-323 | `BREATH` and `AGND` legs | `[repo]` |
| `R-SPI-SER` ×3 | **100 Ω** | Series at the driving end on `SCLK`, `MOSI`, `CS`. **Was drawn as three refdes that are not in the BOM, at 220 Ω, derived from an RC model** — see §4 | `[repo] bom.csv` |
| `U-TVS-SPI` | SP0504BAHT, **SOT-23-5** | `SCLK`, `MOSI`, `CS` + spare, to `PWR_GND` | `[repo]` |
| **`J-CHAIN`** ×2 here | **2×6 1.27 mm shrouded IDC header, right-angle, through-hole** | **One per key-board ribbon (`CBL-CHAIN`), in the far band beside the LED strip, under its key board's; the mates are on the key boards (`chain-connectors` in all). 4 signals, 5 alternating grounds, 3V3, 2 spare. Part open until M4. `key-chain-loom.md`** | ribbon decided (ADR 0017), part open |
| `PCB-CARRIER` | 2-layer, outline derived by the body CAD | The main board (ADR 0017). See *Still open* | `[repo]` `mechanical/drc.echo` "main board (derived)" |
| `TP-*`, `LK-*` | none | A review (`D2`) asked for test points, shunt links and an LA header. **Not fitted** (owner, 2026-09-29): this is a one-off build, probed by hand at the parts' own pins | decided |

*Rows for the five circuits that now have their own directories moved with them:
`U-ADC`, `R-ADCDIV-U`/`R-ADCDIV-L`, `C-AA-ADC` and `C-ADC-BULK` to
`breath-adc/`;
`U-REF-BREATH`, `C-REF-OUT` and `R-FB-REF`/`R-FBX-REF`/`C-FB-REF` to
`breath-excitation-reference/`; `U-LVLSHIFT`, `R-LED-PD`, `R-LED-SER` and
`J-LED` to `led-strip-drive/`; `U-BUCK`, `L-BUCK-IN`, `C-BUCK-IN`,
`D-USBOR`, `D-REVSHUNT`, `D-TVS-PWR` and `C-STRIP-BULK` to
`power-entry-instrument/`; `HDR-SERVICE` to `service-uart/`. `U-BUF` stayed: one half of it is the reference
buffer and the other is the breath buffer.*

---

## What plugs into this board

**There are no internal looms** (ADR 0017). The key chain is two IDC
ribbons, the LED strip is on this board (ADR 0016), the console is a header on
it, and power arrives down the umbilical. What terminates here:

| From | Conductors | Connector |
|---|---|---|
| The two key boards, one IDC ribbon each (`CBL-CHAIN`) | `chain-conductors` each: four chain signals, five alternating grounds, 3V3, two spare — `key-chain-loom.md` | `J-CHAIN` IDC header, one per ribbon here; `chain-connectors` counts both ends |
| The Matrix, on the lid | 24 | `J-MCU` |
| The umbilical, from the tail cap | 8 | `J-UMB` |
| WS2815 strip — on this board (ADR 0016): 12 V, GND, `DI`, `BI` to ground | 4 | `J-LED` |
| The console, and the Matrix's `EN` and `IO0` | 5 | `HDR-SERVICE` |

The Matrix and the umbilical are the section above. The board's outline and
what it keeps clear of are derived in `mechanical/` — `mechanical/drc.echo`
"main board (derived)" gives the size.

---

## Still open

Ordered by what blocks what. The first two block layout.

- **`J-MCU` and its mate, and `J-UMB`, are envelopes, not parts** — the
  envelopes in `config/body.yaml` are `[from memory]`. Decided at M4 with the
  parts.
- **The board outline** is now derived by the body CAD (the main board,
  ADR 0017, `mechanical/DESIGN.md`), with the strip on it (ADR 0016). What is still open
  is the routing inside that outline.
- **E11 on the real ribbon**: breath output clean while the matrix is
  exercised, which is what shows the four grounds share the return as
  *The Matrix and the umbilical at the tail end* assumes.

> **Decided 2026-09-26 (ADR 0018):** the Matrix ribbon's allocation and
> `J-MCU`'s pin map; `U-TVS-CHAIN` fitted; no fuse on the chain's 3V3, one
> `FB-CHAIN` per ribbon instead; `EN` and `IO0` wired to `HDR-SERVICE`; and
> `DIG_GND` tied to this board's ground at `J-UMB` (§4,
> [`spi-link`](../interfaces/spi-link/spi-link.md)).

> **Two items were decided rather than left open.** `J-CHAIN` is **12-way**
> with a ground between every signal (§3). And the key pull-ups **may** share the
> ADC's reference: 27.3 mA of play-rate load worth 3.4 LSB on a ~1594-count
> playable span, as a gain term rather than an offset. **Accepted, not
> ignored** — §2 exists so that when the breath reading twitches on a chord,
> nobody spends a week in the firmware.

> **Two items left this page with the registers.** The **marker pattern**
> (which six bits, to what levels) and the **`H`…`A`-to-switch mapping** are
> now `PCB-CLUSTER` decisions `[repo] 0001, 0002`. Both are still
> unretrofittable, both still have to be told to firmware, and neither is any
> less urgent — they are just not on this board's critical path. They are now
> on `hardware/cluster/cluster-boards.md`, which proposes an answer to both.
- **The etherCON at the instrument end is decided** (ADR 0021): an NE8FAV on
  its own adapter, joined to this board's tongue by `J-UMB`. `J-UMB`'s part
  is chosen. What is open is the tail cap's recess margin (M4) and whether the
  NE8MX cable connector latches in it (`J-UMBILICAL-CABLE`).
- **The breath trap "clearable without disassembly"** (ADR 0003). The sensor
  is reached with the lid off and replaced with an iron (`breath-sense-link.md`,
  *Mounting*); the trap is a separate question, decided with the trap's own
  design.
- ~~**The MCP3202's maximum clock at 3.3 V**~~ — **closed 2026-09-21**, §4.
  0.9 MHz is not an interpolation; it is the datasheet's *guaranteed* 2.7 V
  maximum, so using it at 3.3 V is conservative rather than approximate.
- **Test points, shunt links and an LA header.** `D2-missing-testability.md`
  asked for them on this board; the BOM has none. E14 re-runs E1–E11 on this
  board and M8 does failure injection on it, and neither has a documented means
  of measurement. One-shot.
- **Conformal coating and the sensor ports.** `MECH-COAT` must mask both
  `[repo] 0009`. The sensor is soldered down and coated with the board, so a
  swap breaks the coating at its joints and the ports are re-masked before it
  is touched up.
