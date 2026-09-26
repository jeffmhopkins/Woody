# Real-time carrier — schematic

**Status:** **First draft 2026-09-21; §3 rebuilt the same day** after ADR 0001
moved the shift registers back to the cluster boards. The draft was written
against the tail-register topology and every figure that depended on it — the
block diagram, §3, the loom count, the component table — has been redone. Not
checked against a single datasheet — `waveshare.com`, `ti.com`, `nxp.com` and `analog.com` were all
blocked from this sandbox. Read it as a proposal with its uncertainties marked,
not as a design.

The one board inside the instrument. It has no MCU on it (ADR 0013): a
Waveshare ESP32-S3-Matrix plugs into it and everything else on the board is
passive, slow, or analog.

Evidence marking follows the module pages: `[repo]` names a file, `[calc]` shows
the arithmetic, `[from memory]` means **I could not open the datasheet and you
must check it before ordering.** `[board-def]` means an open-source board
definition file fetched in this session and named.

**Where a value is not known, the row says `TBD` and says what decides it.**
There are more of those here than is comfortable. That is the correct state for
a page written on a day when nothing could be verified; the gap list is
`docs/review/2026-09-21-schematic-review/S3-carrier.md`.

## One dev board, not two

ADR 0013's build-approach section says the carrier holds "headers the dev boards
plug into" and two regulators, "one per dev board" `[repo] 0013`, and
`HDR-DEV` in the BOM budgets header strips for both. **The display board is
360 mm away at the top of the instrument** (ADR 0013's own zone table; ADR 0008's
60 mm display band, mounted lengthwise) `[repo] 0013, 0008`. It reaches this
board through a loom, not a socket.

This page therefore draws **one** dev-board socket pair and leaves the second
regulator's location open — see *Still open*.

---

## Block diagram

```
                              TAIL FACE
   ┌─────────────────────────────────────────────────────────────┐
   │  etherCON (on the plate stack, NOT on this PCB — ADR 0009)  │
   │  USB-C slot ── aligned to the dev board's own connector     │
   └──────────────┬──────────────────────────────────────────────┘
                  │ 8 conductors, T568B pairs (ADR 0004)
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
              +12V ──────────────┼─────────────────────┼──── J-LED-L/R (strips)
               5V ───────────────┤                     │
                                 │                     │
       ┌─────────────────────────▼─────────────────────▼──────────────┐
       │              HDR-DEV  —  ESP32-S3-Matrix socket              │
       │   5V GND 3V3 | IO7 IO6 IO5 IO4 IO3 IO2 IO1                   │
       │   IO33 … IO40 | IO43 IO44                                    │
       │   (onboard: IMU GPIO10-13, 8×8 matrix GPIO14, USB GPIO19/20) │
       └──┬──────┬──────────┬────────────┬───────────┬────────────────┘
          │      │          │            │           │
      3V3 │  SPI3+latch  SPI2+2×CS   IO1/IO2     IO5/IO6  IO43/IO44
          │      │          │            │           │        │
   ┌──────▼──────▼───┐   ┌──▼────────┐ ┌─▼────────┐ ┌▼────────▼──────┐
   │ CHAIN DRIVE §3  │   │ ADC  §2   │ │'125  §5  │ │ J-DISP   §6    │
   │ no registers,   │   │ MCP3202   │ │ LED data │ │ HDR-SERVICE    │
   │ no key networks │   └───────────┘ └──────────┘ └────────────────┘
   └───┬─────────────┘
       │
   J-CHAIN   2x6 IDC, chained through all four cluster boards (ADR 0001)
```

---

*§1 power entry — the reverse shunt, the TVS, the two R-78E5.0 bucks, the OR
diodes, the strip bulk, the plate bond and the input-LC damping analysis —
moved verbatim to
[`power-entry-instrument/`](power-entry-instrument/power-entry-instrument.md).*

---

## §2 Analog front end — sensor, reference, buffer, ADC

*Connectivity for **this board itself** — the dev board, its sockets and the
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
  +12V ──┬─┤VIN VOUT├─┬── 5.000 V ─┤+IN                         SKT-BREATH
         │            │            │              R-ISO-REF     pin VS
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
                                                              │   case 1351-01
                                                              │
                                                              │   P1 ◄── 400 mm tube
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
18 keys closed           = 25.8 mA step on the ADC's reference
at an LDO load regulation of ~0.3 % per 100 mA [from memory]: 0.077 % = 3.2 LSB
```

**Still fine, and no longer negligible.** 3.2 LSB is 0.2 % of the ~1594-count
playable span, and because it is the reference moving it is a gain error rather
than an offset — it scales with how hard you are blowing, which is the
direction that hides it. Recorded because the symptom of getting it wrong is
"the breath reading moves when I press keys", which gets blamed on firmware.
See §3 and *Still open*: if this is ever to be removed rather than tolerated,
the fix is a separate rail for the pull-ups or a real reference for the ADC,
and both are board decisions, not firmware ones.

### Mechanical rules that live with this section

- **Both ports on the same side** (case 1351-01) `[repo] 0003`. Route the tube
  so it cannot cover, kink or blow adhesive across the reference port.
- **Mask both ports before `MECH-COAT`** `[repo] 0009`. A sealed reference
  chamber gains ~5.2 kPa when the body warms and the sensor reads as dead.
- **Which port is P1 is still open** `[repo] 0003` — "confirm before layout", and
  layout is now.
- **`SKT-BREATH` only earns its place if the sensor is reachable.** See
  *Still open*.

---
## §3 Chain drive — what is left after the registers went back

*§3 moved verbatim to
[`../interfaces/key-chain-loom/`](../interfaces/key-chain-loom/key-chain-loom.md),
together with `cluster-boards.md` §3, because the chain is one circuit with an
end on each board — the conductor count and the fusing are decided here, the
pinout and the chain-end link there, and neither half states what runs down the
body. Both pages' drawings went with it whole. The section number is kept
because other pages cite `carrier.md` §3.*

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

*§5 LED data — the 74AHCT125 gates, `R-LED-PD`, `R-LED-SER`, `J-LED-L/R` and
the WS2815 `V_IH`/`BI` argument — moved verbatim to
[`led-strip-drive/`](led-strip-drive/led-strip-drive.md). §6 display loom and
service header — `J-DISP` and `HDR-SERVICE` — moved verbatim to
[`display-and-service-uart/`](display-and-service-uart/display-and-service-uart.md).*

---

## §7 Dev board mounting and the matrix window

> **Superseded 2026-09-26: the matrix is on the TOP face** (owner, ADR 0009).
> The ESP32-S3-Matrix stands face up on the carrier's top side under a window
> in the lid, so there is no cutout to argue about and the underside
> mounting below is not needed. The carrier's height now follows from that
> stack (`mechanical/drc.echo`, "carrier height"). Kept as the record of the
> arithmetic that was.

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
that also carries a ~26 × 31 mm etherCON flange in 57 × 38 mm. That is a 1:1
paper check at M4, and the ROADMAP already lists it.

---

## Component table

Existing BOM rows are named as they stand; **proposed** rows are new to this
page and have no BOM entry yet.

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-MCU-RT` | ESP32-S3-Matrix | The instrument. Socketed on `HDR-DEV` | `[repo]` |
| `HDR-DEV` | 2 × 10-way machined socket | **Qty is one board's worth, not two** — the display board is 360 mm away | `[board-def]` for the pin count |
| ~~`U-KEYS`, `R-KEY-PU`, `R-KEY-SER`, `C-KEY`, `C-DECOUPLE-165`~~ | — | **Not on this board.** 4 ICs and 63 passives moved to `PCB-CLUSTER` with ADR 0001's per-cluster decision. They are still in the BOM, against the cluster boards | `[repo] 0001, bom.csv` |
| **`R-CHAIN-SER`** ×3 | **100 Ω** | **Proposed — series at the driving end on `SCK`, `SH/LD` and `SER`. ADR 0001 deleted `R-TERM-CHAIN` because series termination is wrong for a line that drops on four boards; this is edge-rate damping at the source, which is a different job and survives that argument** | proposed |
| **`U-TVS-CHAIN`** | **4-ch array, SOT-23-6** | **Proposed — the chain's four signals leave the board and run the body. `U-TVS-SPI` does exactly this for the umbilical's three** | proposed |
| **`F-CHAIN`** | **100 mA polyfuse** | **Proposed — the 3V3 conductor runs 265 mm beside 12 V LED power through the body, and a short on it takes the LDO and the instrument down** | proposed |
| `U-BUF` | OPA2197IDR | ½ reference buffer, ½ breath buffer, both on +12 V | `[repo]` |
| `U-BREATH` + `SKT-BREATH` | MPXV4006DP, case 1351-01 | P1 to the tube, P2 open to the cavity | `[repo]`; **P1 identity open** |
| `R-SER-BREATH-INST` | 1 kΩ | Output protection. **No series cap here** | `[repo]` |
| `D-TVS-BREATH` ×2 | 12 V standoff, SOD-323 | `BREATH` and `AGND` legs | `[repo]` |
| `R-SPI-SER` ×3 | **100 Ω** | Series at the driving end on `SCLK`, `MOSI`, `CS`. **Was drawn as three refdes that are not in the BOM, at 220 Ω, derived from an RC model** — see §4 | `[repo] bom.csv` |
| `U-TVS-SPI` | SP0504BAHT, **SOT-23-5** | `SCLK`, `MOSI`, `CS` + spare, to `PWR_GND` | `[repo]` |
| **`J-CHAIN`** | **2×6 IDC boxed, keyed** | **Chained through four cluster boards. 4 signals, 5 alternating grounds, 3V3, 2 spare. EIGHT of them across five boards — `SER`/`QH` are point-to-point, so every cluster board but the last has an IN and an OUT (qty in `bom.csv`)** | **decided** |
| `MECH-GNDBOND` | Ring terminal + M3 | Plate to `PWR_GND`. Needs a pad and a hole on this board | `[repo]` |
| `PCB-CARRIER` | 2-layer, **outline TBD** | See *Still open* | `[repo]` says ~100 × 45 mm; not checked |
| **`TP-*`, `LK-*`** | **TBD** | **Proposed — `D2` asked for test points, shunt links and an LA header on this board and none exist in the BOM** | proposed |

*Rows for the five circuits that now have their own directories moved with them:
`U-ADC`, `R-ADCDIV-U`/`R-ADCDIV-L`, `C-AA-ADC` and `C-ADC-BULK` to
`breath-adc/`;
`U-REF-BREATH`, `C-REF-OUT` and `R-FB-REF`/`R-FBX-REF`/`C-FB-REF` to
`breath-excitation-reference/`; `U-LVLSHIFT`, `R-LED-PD`, `R-LED-SER` and
`J-LED-L/-R` to `led-strip-drive/`; `U-BUCK`, `L-BUCK-IN`, `C-BUCK-IN`,
`D-USBOR`, `D-REVSHUNT`, `D-TVS-PWR` and `C-STRIP-BULK` to
`power-entry-instrument/`; `HDR-SERVICE` and `J-DISP` to
`display-and-service-uart/`. `U-BUF` stayed: one half of it is the reference
buffer and the other is the breath buffer.*

---

## Loom conductor count

`[calc]`, built from the repo's own rules — **not** the "~23" that ADR 0001,
`WIRE-LOOM` and the ROADMAP all carry `[repo]`:

| | Conductors |
|---|---|
| Chain signals: `SCK`, `SH/LD`, `SER`, `QH` | 4 |
| Grounds, alternating — one between every pair, **decided** | 5 |
| Chain supply: 3V3 | 1 |
| Two spare conductors (ADR 0009) | 2 |
| **Key loom, all four clusters, chained — `J-CHAIN` is 2×6** | **12** |
| WS2815: 12 V, GND, `DI` per strip (+`BI` if needed) | 6–8 |
| Display loom (§6) — `EN`/`IO0` withdrawn | 9 |
| Plate ground bond | 1 |
| **Terminating on this board, excluding the umbilical** | **~28–30** |
| Umbilical (`J-UMB`) | 8 |

**The first draft of this table said ~53 and called the repo's "~23" wrong.**
`[repo] 0001, WIRE-LOOM, ROADMAP` That was the tail-register arithmetic — 35
conductors of key loom, one per switch. **On the per-cluster topology the
repo's figure is approximately right after all**, and this page withdraws the
objection. ~28–30 against ~23; the gap is the spare conductors and the display
loom's console pair, not a counting error.

**Termination is not the problem.** `[calc]` As IDC boxed headers, ~29
conductors occupy roughly 250 mm² including keepout on a board of ~4500 mm².
Even single-row 2.54 mm headers would now fit — 29 × 2.54 = 74 mm of board
edge against ~290 mm of perimeter — though IDC is still the right choice for a
loom that is hand-terminated once and then closed up.

**Where they go is the problem.** `[calc]` 57 mm external less 2 × 4 mm acrylic
`[repo] 0009` = **49 mm internal**. `PCB-CARRIER` at 45 mm leaves **2 mm per
side** for two channels that ADR 0009 and ADR 0014 jointly require to carry two
WS2815 strips (~10 mm wide each `[from memory]`), the key loom and the 400 mm
tube. **A 45 mm-wide carrier and open side channels are still mutually
exclusive**, and the board outline still depends on the M4 plan section.

**But the per-cluster decision bought real room here**, which is worth saying
because the width crunch was one of the arguments in play: the channels now
carry **one 8–11 way loom instead of four ribbons totalling 40–56 mm of
width** `[repo] 0001`. That is the difference between a narrower carrier being
a sacrifice and it being an ordinary trade.

---

## Still open

Ordered by what blocks what. The first four block layout.

- **Which face of the dev board carries the matrix, and its outline and header
  row spacing** (§7). Decides underside-mount versus a ~22 mm cutout, and with
  it the whole board's routing.
- **The board outline, against a plan section at the tail** — carrier, two LED
  strips, one 8–11 way key loom, the display loom, the breath tube and the
  U-bolt in 49 mm of internal width and ~20 mm of cavity. "~100 × 45 mm" is an
  assumption, not a fit — but a less tight one than the four-ribbon draft had.
- **`F-CHAIN`** (§3): whether the 3V3 conductor going down the body is fused.
  Two millimetres of board, unretrofittable, and the failure it covers is
  "the instrument is dead and there is no way to look inside".

> **Two items were decided rather than left open.** `J-CHAIN` is **2×6** with
> a ground between every signal (§3). And the key pull-ups **may** share the
> ADC's reference: 25.8 mA of play-rate load worth 3.2 LSB on a ~1594-count
> playable span, as a gain term rather than an offset. **Accepted, not
> ignored** — §2 exists so that when the breath reading twitches on a chord,
> nobody spends a week in the firmware.

> **Two items left this page with the registers.** The **marker pattern**
> (which six bits, to what levels) and the **`H`…`A`-to-switch mapping** are
> now `PCB-CLUSTER` decisions `[repo] 0001, 0002`. Both are still
> unretrofittable, both still have to be told to firmware, and neither is any
> less urgent — they are just not on this board's critical path. They are now
> on `hardware/cluster/cluster-boards.md`, which proposes an answer to both.
- **Whether the sensor is reachable after bonding**, which decides whether
  `SKT-BREATH` earns its place. ADR 0003 wants a replaceable wear part and a
  trap "clearable without disassembly"; ADR 0009 gives a 12 × 40 mm cover over a
  2×5 header. Those do not meet. Either the cover becomes a real hatch with the
  sensor and trap under it, or the socket is decoration.
- **Which port of the MPXV4006DP is P1** `[repo] 0003`. Needed for layout.
- **The etherCON variant at the instrument end** `[repo] 0004`, which decides
  whether this board carries an RJ45 jack footprint (~16 × 14 mm, not in the
  BOM) or eight wires. ADR 0004 defers it to E12/M7, which is after E13.
- ~~**The MCP3202's maximum clock at 3.3 V**~~ — **closed 2026-09-21**, §4.
  0.9 MHz is not an interpolation; it is the datasheet's *guaranteed* 2.7 V
  maximum, so using it at 3.3 V is conservative rather than approximate.
- **Test points, shunt links and an LA header.** `D2-missing-testability.md`
  asked for them on this board; the BOM has none. E14 re-runs E1–E11 on this
  board and M8 does failure injection on it, and neither has a documented means
  of measurement. One-shot.
- **Conformal coating and the sensor ports.** `MECH-COAT` must mask both
  `[repo] 0009`, and the part is socketed, which makes masking easier and
  retention worse.
