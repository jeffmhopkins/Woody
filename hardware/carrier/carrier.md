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
> connected to it by flat flex ribbons (`mechanical/DESIGN.md`). The block
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
   │  etherCON J-UMBILICAL, in the tail cap, NOT on this PCB     │
   │  USB-C receptacle ── CBL-USB-EXT to the Matrix's own port   │
   └──────────────┬──────────────────────────────────────────────┘
                  │ CBL-UMB-PATCH, straight: 8 conductors, T568B pairs (ADR 0004)
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
       │   5V GND 3V3 | IO7 … IO1  (IO2–IO6 spare)                    │
       │   IO33 … IO40 | IO43 IO44                                    │
       │   (onboard: IMU GPIO10-13, 8×8 matrix GPIO14, USB GPIO19/20) │
       └──┬──────┬──────────┬────────────┬───────────┬────────────────┘
          │      │          │            │           │
      3V3 │  SPI3+latch  SPI2+2×CS   IO1                  IO43/IO44
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
          REF5050                  ½ OPA2197  "reference buffer"
  +12V ──┬─┤VIN VOUT├─┬── 5.000 V ─┤+IN                         U-BREATH
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
                     │                                         │      ** PROPOSED **
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
this board, the two flat flex ribbons to the key boards, and this board's
chain parts — `R-CHAIN-SER`, `R-SER-TERM`, `U-TVS-CHAIN`, `F-CHAIN` and its two
`J-CHAIN`. The section number is kept because other pages cite `carrier.md`
§3.*

---

## §4 SPI egress to the umbilical

```
  IO35 SCK  ──[R-SPI-SER 100R]───┬──── J-UMB pin 4   ┐ pair (4,5)
  IO36 MOSI ──[R-SPI-SER 100R]───┼──── J-UMB pin 5   ┘
  IO34 CS   ──[R-SPI-SER 100R]───┼──── J-UMB pin 7   ┐ pair (7,8)
                                 │     J-UMB pin 8 ──┘ DIG_GND
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
  ON THE LID                                  IN THE TAIL CAP
  U-MCU-RT  ESP32-S3-Matrix                   J-UMBILICAL  etherCON, a feedthrough
    two pad rows, ten pads each                 rear RJ45 socket
        │                                           │
        │ CBL-MCU-RIBBON                            │ CBL-UMB-PATCH
        │ soldered to the pads                      │ straight, pin N to pin N,
        │                                           │ S-bend at its minimum bend radius
        ▼                                           ▼
  J-MCU  2 × 10, 1.27 mm ──── main board, tail end ──── J-UMB  8-way, latching
```

**`J-MCU` replaces the dev-board sockets.** The Matrix is on the lid, so it
cannot plug into this board; its ribbon is soldered to its pad rows and
plugs in here, and it unplugs when the lid comes off. A dead Matrix is
still a bench job and not a strip-down: unplug `J-MCU`, take the lid off,
desolder the ribbon from the pad rows and solder it to the replacement —
nothing on this board is touched. The ribbon's length is `mechanical/drc.echo`
*"Matrix ribbon length"* plus build slack; the builder's notes are on the
`CBL-MCU-RIBBON` row.

**Twenty conductors, and the Matrix has one ground pad.** Fifteen are fixed by
[`netlist.yaml`](netlist.yaml): the twelve GPIO the instrument uses, 5V, 3V3
and GND. The pad rows carry three power pads and seventeen GPIO, and only one
of the power pads is ground `[repo] datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-pinout.png`
(`5V GND 3V3 GP7…GP1 | GP33…GP40 TX RX`). So the other five are **open**:

- **the spare GPIO pads, IO2–IO6** — ADR 0009's spare conductors reach this
  board, and one conductor returns the Matrix's LED current and every signal;
- **five more grounds** — what the body model's first sizing of this ribbon assumed. They have to be
  soldered to ground points on the Matrix off its pad rows, and the ribbon
  then carries no spares.

**What decides it:** M4 with the Matrix in hand (where a ground can be
soldered), and E11 — breath output clean while the matrix is exercised. The
reason it reaches the breath channel: the Matrix's 3V3 is the MCP3202's
reference (`carrier/breath-adc`), regulated against the *Matrix's* ground, so
LED return current in the ribbon's ground conductor moves that reference
against this board's. `[calc]`, on `[from memory]` inputs — a 0.635 mm-pitch
ribbon conductor is ~30 AWG, ~0.34 Ω/m; the length is illustrative, not the
model's:

```
100 mm × 0.34 Ω/m          = 34 mΩ per ground conductor
100 mA of LED current      → 3.4 mV of ground shift
3.4 mV / 3.3 V × 4096      = 4.2 LSB on the breath ADC, moving with the display
```

Six grounds in parallel divide that by six. Whatever the allocation, `J-MCU`
should put a ground between the SPI clock (`IO35`) and the chain clock
(`IO38`).

**`J-UMB` is where the umbilical reaches this board.** `J-UMBILICAL` is a
feedthrough, and `CBL-UMB-PATCH` runs straight from its rear RJ45 socket to
`J-UMB`, pin N to pin N — so every "`J-UMB` pin N" on these pages is this
board's connector *and* the same conductor as the etherCON's pin N, and the
pin map is `umbilical-pinmap` either way. `J-UMB` sits as far in as the
patch lead's bend needs (`mechanical/drc.echo` *"J-UMB on the main board, the
patch lead at its bend radius"*). The clamps and the reverse shunt drawn "at
the connector" on these pages are at `J-UMB`. Its contacts must be rated
above the module's current limit (`R-ILIM`,
[`umbilical-load-switch`](../module/umbilical-load-switch/umbilical-load-switch.md)),
not only `umbilical-current`: a short is carried at the limit until the load
switch times out.

**Netlisted where the connector's pin map is.** `J-MCU` is in this board's
[`netlist.yaml`](netlist.yaml), in series with every Matrix net. `J-UMB` is in
[`../interfaces/spi-link/netlist.yaml`](../interfaces/spi-link/netlist.yaml)
beside both etherCONs, because it carries the umbilical's pin map and all
eight of its nets; the carrier's nets reach it as that circuit's ports, as
they reached the etherCON before. Neither cable is a component: each is
straight, with no pin map of its own, so each connector pin shares a net with
the pin at the cable's other end.

---

## Component table

Existing BOM rows are named as they stand; **proposed** rows are new to this
page and have no BOM entry yet.

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-MCU-RT` | ESP32-S3-Matrix | The instrument. On the lid, not on this board; wired by `CBL-MCU-RIBBON` | `[repo]` |
| `J-MCU` | 2 × 10, 1.27 mm shrouded box header, right-angle | The Matrix's connector, at the tail end. **Five of its twenty positions open** — see *The Matrix and the umbilical at the tail end* | `[from memory]`; part **open**, M4 |
| `CBL-MCU-RIBBON` | 20-way flat ribbon, 0.635 mm | Soldered to the Matrix's pad rows, IDC socket into `J-MCU` | `[repo]` pad map; `[from memory]` ribbon; **open**, M4 |
| `J-UMB` | 8-way latching wire-to-board header | Where the umbilical reaches this board; `interfaces/spi-link`'s row | `[from memory]`; part **open**, M4 |
| `CBL-UMB-PATCH` | Short Cat5e/Cat6 patch lead, RJ45 to crimp housing | etherCON rear socket to `J-UMB`, straight; `interfaces/spi-link`'s row | `[from memory]`; **open**, M4 |
| `U-KEYS`, `R-KEY-PU`, `R-KEY-SER`, `C-KEY`, `C-DECOUPLE-165` | — | **Half of them are on this board since ADR 0017**: the `right_thumb` and `left_thumb` clusters. The other two clusters are on the key boards. Counts per cluster are `cluster-boards.md`'s component table | `[repo] 0017, bom.csv` |
| **`R-CHAIN-SER`** ×3 | **100 Ω** | **Open — series at the driving end on `SCK`, `SH/LD` and the chain-end `SER`. Edge-rate damping, not termination; E14 decides. `key-chain-loom.md`** | open |
| **`U-TVS-CHAIN`** | **4-ch array, SOT-23-5** | **Open — the three MCU nets the ribbon connectors expose, for service handling with the lid off. The owner decides. `key-chain-loom.md`** | open |
| **`F-CHAIN`** | **100 mA polyfuse** | **Open — the chain's 3V3 feed; the short it covers is a ribbon seated skewed at re-assembly, which would take the LDO and the instrument down. `key-chain-loom.md`** | open |
| `U-BUF` | OPA2197IDR | ½ reference buffer, ½ breath buffer, both on +12 V | `[repo]` |
| `U-BREATH` | MPXV4006DP, case 1351-01, surface mount, soldered down | P1 to the tube, P2 open to the cavity | `[ds]` pp.1, 6, 7 |
| `R-SER-BREATH-INST` | 1 kΩ | Output protection. **No series cap here** | `[repo]` |
| `D-TVS-BREATH` ×2 | 12 V standoff, SOD-323 | `BREATH` and `AGND` legs | `[repo]` |
| `R-SPI-SER` ×3 | **100 Ω** | Series at the driving end on `SCLK`, `MOSI`, `CS`. **Was drawn as three refdes that are not in the BOM, at 220 Ω, derived from an RC model** — see §4 | `[repo] bom.csv` |
| `U-TVS-SPI` | SP0504BAHT, **SOT-23-5** | `SCLK`, `MOSI`, `CS` + spare, to `PWR_GND` | `[repo]` |
| **`J-CHAIN`** ×2 here | **12-way 1.0 mm FFC ZIF** | **One per key-board ribbon (`FFC-CHAIN`); the mates are on the key boards (`chain-connectors` in all). 4 signals, 5 alternating grounds, 3V3, 2 spare. Part open until M4. `key-chain-loom.md`** | ribbon decided (ADR 0017), part open |
| `MECH-GNDBOND` | Ring terminal + M3 | Plate to `PWR_GND`. Needs a pad and a hole on this board | `[repo]` |
| `PCB-CARRIER` | 2-layer, **outline TBD** | See *Still open* | `[repo]` says ~100 × 45 mm; not checked |
| **`TP-*`, `LK-*`** | **TBD** | **Proposed — `D2` asked for test points, shunt links and an LA header on this board and none exist in the BOM** | proposed |

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

**There are no internal looms** (ADR 0017). The key chain is flat flex
ribbon, the LED strip is on this board (ADR 0016), the console is a header on
it, and power arrives down the umbilical. What terminates here:

| From | Conductors | Connector |
|---|---|---|
| The two key boards, one flat flex ribbon each (`FFC-CHAIN`) | 12 each: four chain signals, five alternating grounds, 3V3, two spare — `key-chain-loom.md` | `J-CHAIN` ZIF, one per ribbon here; `chain-connectors` counts both ends |
| The Matrix, on the lid | 20 | `J-MCU` |
| The umbilical, from the tail cap | 8 | `J-UMB` |
| WS2815 strip — on this board (ADR 0016): 12 V, GND, `DI`, `BI` to ground | 4 | `J-LED` |
| The console | 3 | `HDR-SERVICE` |
| The key plate's ground bond | 1 | `MECH-GNDBOND` |

The Matrix and the umbilical are the section above. The board's outline and
what it keeps clear of are derived in `mechanical/` — `mechanical/drc.echo`
"main board (derived)" gives the size.

---

## Still open

Ordered by what blocks what. The first four block layout.

- **The Matrix ribbon's last five conductors**: five more grounds or the spare
  GPIO IO2–IO6 (*The Matrix and the umbilical at the tail end*). Decides
  `J-MCU`'s pinout. Decided at M4 with the Matrix in hand, checked by E11.
- **`J-MCU`, `J-UMB` and their mates are envelopes, not parts** — the
  envelopes in `config/body.yaml` are `[from memory]`. Decided at M4 with the
  parts; `J-UMB`'s contacts against `R-ILIM`, not only `umbilical-current`.
- **The board outline** is now derived by the body CAD (the main board,
  ADR 0017, `mechanical/DESIGN.md`), with the strip on it (ADR 0016). What is still open
  is the routing inside that outline.
- **`F-CHAIN`** (§3): whether the chain's 3V3 feed to the key-board ribbons
  is fused. Two millimetres of board; the short it covers is a ribbon seated
  skewed when the lid goes back on (`key-chain-loom.md`).

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
- **The etherCON variant at the instrument end** `[repo] 0004`, deferred by
  ADR 0004 to E12/M7. It no longer decides this board's footprint — that is
  `J-UMB` either way — but `CBL-UMB-PATCH`'s plug end assumes a feedthrough
  with an RJ45 socket at the back, as the body model draws the NE8FDP. A
  variant without one changes the patch lead, not this board.
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
