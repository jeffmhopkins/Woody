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

### Two parts this drawing was missing, both unretrofittable

Both are in `bom.csv`, both are marked instrument-side and unretrofittable
there, and **neither appeared on this page** — the page that says of itself
"layout is now". Two reviewers found them independently, from opposite
directions.

**`R1b` — the twin 1 kΩ in the `AGND` leg.** `bom.csv` carries
`R-SER-BREATH-INST` at **qty 2**, and `breath-receive-stage.md`'s 482 Hz
differential pole is derived with 1 kΩ in *both* legs. Only one was drawn.

Its real job is **source-impedance balance on the twisted pair** — 1 kΩ
against ~0 Ω is what a difference amplifier's CMRR actually responds to —
and that justification appears nowhere in the repo. Without it the link
CMRR falls from **70.2 dB to 60.2 dB** `[calc, A2]` against an independently
derived requirement of 58.5 dB: **1.7 dB of margin**, resting on two parts'
tolerance, inside a body that cannot be reopened.

> One correction to the receive page's own case for `R1b`: it claims the
> part buys "fifty times" the rejection. With `R1b` fitted the real floor
> is **73 dB**, set by the 1 MΩ bias pair, so `R1b` buys about **13 dB**.
> Still worth fitting. The stated reason overstates it.

*The `R-ISO-REF` half of this section — the compensation network, why TI's
Figure 56 transfers, and what it buys — moved verbatim to
[`breath-excitation-reference/`](breath-excitation-reference/breath-excitation-reference.md),
along with the record of the two blockers that closed with it. The drawing
above stays here because it is one connected picture and dividing it would mean
redrawing it.*

### Two things this drawing settles that no ADR does

**1. The analog star point is on this board, and `AGND` is sense-only.**
ADR 0003 names the star point as "the analog ground pour on the bottom cluster
board" `[repo] 0003` — a board that does not exist; it means this one. What it
leaves open is whether the analog section's supply return goes home on `AGND` or
on `PWR_GND`.

**Proposed: `PWR_GND`.** `AGND` leaves the board carrying nothing but the in-amp
sense reference, which is what ADR 0004's rule says and what makes the 2 m run
work `[repo] 0004`. The local analog pour joins `PWR_GND` at **one** tie, at the
umbilical connector.

The cost of getting it the other way `[calc]`, using ADR 0003's own cable figure
(0.168 Ω for 2 m of 24 AWG, implied by its 8.4 µV / 50 µA row):

```
REF5050 ~1 mA + OPA2197 2 × ~1 mA + MPXV4006DP 10 mA = ~13 mA   [repo] 0003
13 mA × 0.168 Ω = 2.2 mV on the sense pair
× the in-amp's G = 2.185 → 4.8 mV at the breath jack = 0.048 % of 10 V
```

Survivable either way, because it is DC-constant and `TRIM-BREATH-ZERO` nulls it
at commissioning `[repo] breath-receive-stage.md`. **`PWR_GND` anyway**, because
it is free and it keeps the rule true instead of approximately true.

**2. There is no band-limit capacitor at the instrument end of `BREATH`.**
ADR 0003 says "band-limit at both ends, around 500 Hz" `[repo] 0003`;
`breath-receive-stage.md` puts the whole 500 Hz filter at the receive end, ahead
of the in-amp, "because that is the only place it can stop RF rectification", and
`R-SER-BREATH-INST`'s note says the ADR is superseded `[repo] bom.csv`. **Drawn
that way here. Do not add a cap at `R-SER-BREATH-INST`.**

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

**The registers are not on this board.** ADR 0001's *"One register per cluster"*
put one 74HC165 on each cluster board, with that cluster's 2.2 kΩ/100 Ω/47 nF
networks beside it, because the switches need a rigid PCB regardless (ADR 0002)
and putting the register on it makes every switch-to-chip connection a trace
`[repo] 0001, 0002`. **This page's first draft drew all four registers and all
21 networks here.** That was the superseded topology; what follows replaces it.

**Decided: a ground return per signal, laid out as an alternating-ground
ribbon.** ADR 0001 fix 1 calls this the highest-value item on its list, and it
is the only thing in the loom that can still be corrupted — a glitch on `SH/LD`
does not cost one wrong note, it reloads all four registers mid-shift and
corrupts the whole 32-bit word `[repo] 0001`. Four signals, five grounds, one
supply:

```
  HDR-DEV                                   J-CHAIN  (2×6 IDC, 12-way ribbon,
                                                      10 wired + 2 spare)
   GND  ────────────────────────────────────►  1  GND
   IO38  SPI3 SCK ──[R-CHAIN-SER 100R]─────►  2  SCK     ** R PROPOSED **
   GND  ────────────────────────────────────►  3  GND
   IO7   latch    ──[R-CHAIN-SER 100R]─────►  4  SH/LD   ** R PROPOSED **
   GND  ────────────────────────────────────►  5  GND
   IO33  SER out  ──[R-CHAIN-SER 100R]─────►  6  SER     (into the far device)
   GND  ────────────────────────────────────►  7  GND
   IO40  MISO     ◄─────────────────────────  8  QH      (out of the near one)
   GND  ────────────────────────────────────►  9  GND
   3V3  ───────[F-CHAIN, see below]─────────► 10  3V3     → 24 pull-ups,
                                              11  spare      4 × VCC, 4 × 100 nF
                                              12  spare

              [U-TVS-CHAIN 4-ch array to DIG_GND]   ** PROPOSED **

  Every signal has ground on both sides; 3V3 sits against pin 9's ground.
  The two spares are ADR 0009's rule and they are FREE: IDC comes in 2xN, so
  a 2x6 costs what a 2x5 costs and the ribbon is 2 mm wider. Under the tail
  topology a spare conductor bought a spare KEY; under this one it buys a
  REPAIR - expansion now lands on a spare register BIT, which needs no wire.

  EIGHT connectors, not five. The chain is four hops, and SER/QH cannot be a
  pass-through bus: each board's QH feeds the PREVIOUS board's SER, which is
  point-to-point and changes meaning every hop. So every cluster board except
  the last carries an IN and an OUT - carrier 1, RT 2, RH 2, LT 2, LH 1 - with
  four ribbon assemblies between them. Same 2x6 pinout at all eight.

  Pin 6 SER is the exception: it IS a pass-through, riding every hop to reach
  the far device's serial input. ADR 0001 has that input "terminated at the
  far device", which would make this conductor redundant. Driving it instead
  costs nothing and buys an end-to-end chain self-test - shift a known pattern
  in at LH and read it back at RT, with no keys pressed. That distinguishes
  "the loom is broken" from "one bit is stuck", which the static marker
  pattern cannot. NOT yet decided; it is a cluster-board question.

  Chained, not starred (ADR 0001 fix 2): ONE run leaves this connector and
  passes through right_thumb → right_hand → left_thumb → left_hand in turn.
  bit 0 is the first bit clocked out = QH of right_thumb, the device nearest
  the MCU (ADR 0001 fix 3, and config/key-layout.yaml).
```

**`CLK INH` is tied low and `SER` is terminated at the far device** — both on
the cluster boards, not here `[repo] 0001`.

### What this board still owes the chain

**1. The 3V3 rail, and it is a bigger load than it was** `[calc]`. The pull-ups
went 10 kΩ → 2.2 kΩ when the register moved back beside its switch `[repo]
bom.csv`:

```
3.3 V / (2.2 kΩ + 100 Ω) = 1.43 mA per CLOSED key
18 closed                = 25.8 mA, as a step, at play rate
plus 4 × 74HC165 quiescent, negligible
```

> **That current comes out of the dev board's 3V3 LDO, which is also the
> MCP3202's voltage reference** — the part has no `VREF` pin, `VDD` *is* the
> reference `[repo] R10 B4`. At a load regulation of ~0.3 % per 100 mA
> `[from memory]`, 25.8 mA moves the reference **0.077 %, about 3.2 LSB**, in
> step with how many keys are held.
>
> 3.2 LSB against a playable breath span of ~1594 counts is 0.2 % — almost
> certainly inaudible, and it is the *reference* moving, so it scales the
> reading rather than offsetting it. **Recorded rather than fixed, because the
> symptom of being wrong about it is "the breath reading moves when I press
> keys", which gets blamed on firmware for a week.** The first draft costed
> this at 5.9 mA and 0.7 LSB, against the old 10 kΩ. See *Still open*.

**2. A ground return per clocked signal** `[repo] 0001 fix 1` — the highest
value item on ADR 0001's list, and now the *only* thing in the loom that can be
corrupted. With the registers distributed, a disturbed key line no longer
exists as a loom signal; what runs the body is four clocked lines whose blast
radius is the whole 32-bit word, and a glitch on `SH/LD` reloads every register
mid-shift `[repo] 0001`. **Six conductors is the signal count, not the
conductor count.** Whether this connector is 6-way or 10-way is a decision this
page cannot take alone — see *Still open*.

**3. `F-CHAIN`, or not.** The 3V3 conductor leaves this board, runs 265 mm
through a bonded body next to 12 V LED power, and comes back as nothing. A
short on it browns out the dev board's LDO and takes the instrument down with
no diagnosis. A 100 mA polyfuse or a 0603 fuse is two millimetres of board.
**Proposed, not in the BOM.**

### Why the old charge-sharing derivation is gone

The first draft carried ADR 0001's `180 pC / 10 nF = 18 mV`, and a companion
figure of **+4.5 V on the loom node** from `180 pC / 40 pF`. Both are dead, for
two independent reasons, and neither should be reintroduced:

- **The model was wrong.** ADR 0001 now records it: there is no 12 V edge (the
  WS2815 rail is held by 470–1000 µF and its LED current is PWM'd at ~2 kHz),
  `Q/C` is the wrong model because coupling is a *divider*, and a passive
  divider cannot exceed the aggressor's own swing — so 4.5 V was 37 % above
  the ceiling of its own mechanism. Corrected, an unfiltered wire sees
  **1.36 V** `[repo] 0001`.
- **The node no longer exists.** The key network sits on the cluster board, a
  few millimetres from its switch. There is no loom conductor between the
  switch and the register input for anything to couple into.

**The key networks are still fitted** — see ADR 0001 for why (a floating CMOS
input has no defined state, in a cavity that is breathed into for hours) — but
they are a bounce filter and cheap insurance, not the thing that makes the
topology safe, and they are not this board's parts.

### The 32 bits, and where each decision now lives

From `config/key-layout.yaml` `[repo]`:

| Bits | Use | Whose board |
|---|---|---|
| 18 | Fitted switches | **Cluster boards** — network + trace to the switch |
| 3 | Reserved spare switches (octave up, octave down, hold/preset) | **Cluster boards** — network fitted, pad unloaded. Plate cutouts at M3 `[repo] 0010` |
| 8 | Marker pattern | **Cluster boards** — hard-wired at the register input. Unretrofittable. **Decided 2026-09-21: 8, not 6** |
| 3 | Genuinely free | **Cluster boards** — must be pulled `[repo] key-layout.yaml` |
| **32** | | **None of them on this carrier** |

**Which eight bits carry the marker, and their levels, was decided 2026-09-21**
(`key-marker-and-bits.md`, `key-layout.yaml`). The mapping inside each device is
still open, and
it is now a cluster-board decision** — as is the `H`…`A`-to-switch mapping
inside each device. Both still have to be settled before *those* boards are
made, and firmware has to be told about both. They are off this page's critical
path, not off the project's.

**The option worth costing has got cheaper.** Giving the 3 free bits the full
network too is now 15 passives spread across four boards that already carry
21 sets, with no extra loom conductors at all — under the tail topology it also
needed five more wires down the body. If "add a switch later" is worth
anything, this is the moment it costs least.

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

**All three are `R-SPI-SER`, and the value is 100 Ω.** The refdes matters:
this page previously drew `R-SCLK-SER`, `R-MOSI-SER` and `R-CS-SER`, **none
of which exist in `bom.csv`**, while the BOM carries `R-SPI-SER` at qty 3
used by no schematic. Same three parts, two naming schemes, neither side
aware of the other. (This page also claimed "only `R-MOSI-SER` reached the
BOM, qty 1" — it is not in the BOM at all.)

**The value is 100 Ω, not 220, and the old derivation used the wrong
model.** Two m of Cat5 is a **100 Ω transmission line**: the round trip is
~20 ns against 2–5 ns edges, so this is a reflection problem, not an RC
corner. Three reviewers agreed on that and two of them computed what 220 Ω
costs `[calc]`:

| Source R | First step at the far end | vs `V_IH` 2.0 V |
|---|---|---|
| **220 Ω** | **1.83–1.86 V** | **below threshold, dwelling ~20 ns per edge in the forbidden band** |
| 100 Ω | **2.75 V** | clean single step |
| 68 Ω | 3.25 V | clean, but **48 mA fault current against a 40 mA pad spec** |

**100 Ω** is the answer: it resolves in one transit and draws 33 mA into a
clamp. 68 Ω is electrically ideal and exceeds what the pin can source.
(ADR 0004's old "7.9 MHz corner" was the figure for 100 Ω all along, quoted
against 220 Ω — the schematic review caught that separately.)

The receiving end has no hysteresis, which is what makes the dwell matter:
a 74AHCT125 given 20 ns in its indeterminate band on every clock edge is
being asked to guess.

### The two SPI hosts, and what claims them

| Host | Devices | Clock |
|---|---|---|
| **SPI2** | DAC8568 down the umbilical, **and** MCP3202 on this board | **2 MHz for the DAC, 900 kHz for the ADC — not one clock** |
| **SPI3** | 74HC165 chain alone, because `QH` is always driven (ADR 0001) | **1 MHz, and not much more** — the chain crosses four connectors and ~265 mm of loom, and HC's slow edges are what keep that a lumped load `[repo] 0001` |

> **The MCP3202 cannot run at 2 MHz.** `[repo, verified]` against Microchip
> DS21034F, now at `datasheets/other-semi/MCP3202-CI-SN.pdf`. The Timing
> Parameters table gives `fCLK` max = **1.8 MHz at VDD = 5 V** and **0.9 MHz at
> VDD = 2.7 V**. There is no 3.3 V row. ADR 0003, ADR 0004,
> `latency-budget.md` and `power-entry.md` all say "SPI2 at 2 MHz", and ADR 0004
> explicitly says that leaves room "for the MCP3202 sharing the host" `[repo]`.
>
> **0.9 MHz is safer than this page claimed, not shakier.** Two documents called
> it "an interpolation from a search summary". It is not an interpolation at
> all — it is the datasheet's *guaranteed maximum at 2.7 V*, so applying it at
> 3.3 V is strictly conservative. A straight-line interpolation to 3.3 V would
> give ≈1.14 MHz, so there is ~25 % of headroom the design is not claiming.
> Both `fCLK` rows carry Note 2: established by characterisation, not 100 %
> tested.
>
> **And there is a minimum nobody had.** §6.2: the sample capacitor holds
> charge for at least 1.2 ms at 85 °C, so the end of the sample period to the
> last data bit must fit inside that — an effective **`fCLK` ≥ ~10 kHz**. Not
> binding at 900 kHz, but it forecloses "slow the ADC down" as a way to buy
> loop time.
>
> ESP-IDF sets `clock_speed_hz` per *device* on a shared host, so this is a
> firmware line and not a part change. **It is written nowhere.**

**Loop budget with the ADC costed properly** `[calc]` — ADR 0004's version left
it out:

```
SPI2  DAC    6 × 32 bits @ 2.0 MHz =  96.0 µs
SPI2  ADC    24 clocks    @ 0.9 MHz =  26.7 µs
SPI2  total                         = 122.7 µs of 250 µs → 49 %
SPI3  keys   32 bits      @ 1.0 MHz =  32.0 µs, concurrent → 13 %
             (+ four HC165 propagation delays, tens of ns each — noise)
```

**SPI2 cannot use IO_MUX and does not need to.** The S3's FSPI IO_MUX pins are
GPIO9–14 `[from memory]`, and the board spends GPIO10–13 on the QMI8658C and
GPIO14 on the matrix `[board-def] circuitpython .../pins.c`. SPI2 on
GPIO35/36/37 therefore routes through the GPIO matrix, capped around 40 MHz
rather than 80 `[from memory]`. Irrelevant at 2 MHz; recorded so it is not
rediscovered as a problem.

---

*§5 LED data — the 74AHCT125 gates, `R-LED-PD`, `R-LED-SER`, `J-LED-L/R` and
the WS2815 `V_IH`/`BI` argument — moved verbatim to
[`led-strip-drive/`](led-strip-drive/led-strip-drive.md). §6 display loom and
service header — `J-DISP` and `HDR-SERVICE` — moved verbatim to
[`display-and-service-uart/`](display-and-service-uart/display-and-service-uart.md).*

---

## §7 Dev board mounting and the matrix window

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
| **`F-CHAIN`** | **100 mA polyfuse** | **Proposed — the 3V3 conductor runs 265 mm beside 12 V LED power in a bonded body, and a short on it takes the LDO and the instrument down** | proposed |
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
`U-ADC`, `R-ADCDIV`, `C-AA-ADC` and `C-ADC-BULK` to `breath-adc/`;
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
loom that is hand-terminated once and then bonded shut.

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
