# Real-time carrier — schematic

**Status:** **First draft, 2026-09-21.** Not reviewed, not checked against a
single datasheet — `waveshare.com`, `ti.com`, `nxp.com` and `analog.com` were all
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
   │ J-UMB   1 BREATH   2 AGND   3 +12V   6 PWR_GND   4 MOSI   5 CS      │
   │         7 SCLK     8 DIG_GND                                        │
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
   │ KEY SCAN  §3    │   │ ADC  §2   │ │'125  §5  │ │ J-DISP   §6    │
   │ 4 × 74LVC165    │   │ MCP3202   │ │ LED data │ │ HDR-SERVICE    │
   │ 21 RC networks  │   └───────────┘ └──────────┘ └────────────────┘
   └───┬─────────────┘
       │
   J-KEY-LH / -LT / -RH / -RT      → four ribbons up the body
```

---

## §1 Power entry

```
 J-UMB pin 3  +12V ──┬──[D-REVSHUNT SS34]──┐
                     │   cathode to +12V   │
                     ├──[D-TVS-PWR SMAJ15A]┤
                     │                     │
                     ├─────────────────────┼──── WS2815 strips, direct
                     │                     │     (J-LED-L, J-LED-R)
                     │                     │     [C-STRIP-BULK 470–1000 µF ×2]
                     │                     │
                     ├──[REF5050]──┬────────┼──── §2 analog
                     │   in  out   │        │
                     │        [C-REF-OUT]   │
                     │                      │
                     ├── OPA2197 V+ ────────┤
                     │                      │
                     ├──[L-BUCK-IN]──┬──────┼──[R-78E5.0 A]──▷|──┬── dev board 5V
                     │   10–47 µH    │      │                 D-USBOR  ├── 74AHCT125
                     │        [C-BUCK-IN    │                         └── (8×8 matrix,
                     │         100 µF 25V]  │                              via the board)
                     │               │      │
                     │               └──────┼──[R-78E5.0 B]──▷|──── J-DISP 5V
                     │                      │                 D-USBOR   ?? see Still open
 J-UMB pin 6 PWR_GND ┴──────────────────────┴──── PWR_GND pour
                                             │
                                             └──[MECH-GNDBOND]── aluminium key plate
```

**`D-REVSHUNT` goes at the connector, ahead of `L-BUCK-IN`.** Its job is a
rollover patch lead swapping pins 3 and 6 `[repo] 0004`; it has to conduct
immediately and let the module's LT1641-1 latch off. An inductor between the
fault and the diode is the wrong way round.

**There is no fuse and no power switch on this board** (ADR 0005). The current
limit is at the module.

**`MECH-GNDBOND` ties the aluminium plate to `PWR_GND`, never to `AGND`**
`[repo] 0009`. This board is the only place that bond can originate.

### Derivations

**The input LC is stable** `[calc]`, which partly closes `power-entry.md`'s
"damping the input LC" open item — for the instrument end only:

```
L = 22 µH (mid range), C = 100 µF
f0 = 1/(2π√LC) = 3.39 kHz
Z0 = √(L/C)    = 0.469 Ω
ESR of a 100 µF / 25 V radial ≈ 0.5–1 Ω [from memory] → Q ≈ 0.5–0.9, no peaking

Constant-power load at typical play:
  226 mA × 5 V = 1.13 W out ÷ 0.90 = 1.26 W in at 11.4 V   [repo] 0005
  R_neg = −V²/P = −103 Ω
Margin: |R_neg| / Z0_peak = 103 / 0.47 ≈ 220× (47 dB)
```

> **This result depends on `C-BUCK-IN` being an electrolytic with real ESR.**
> Substituting a low-ESR ceramic raises Q and the paragraph stops being true.
> The BOM row says electrolytic; keep it that way.

**Regulator loading** `[calc]`, from ADR 0005's load table:

```
Clamp-legal worst on the 5 V rail, total                        928 mA  [repo] 0005
Less the display board, which is on buck B                  ~150–250 mA  ESTIMATED
Buck A (real-time board + matrix + 74AHCT125)                ~680–780 mA
R-78E5.0-1.0 rating                                            1000 mA
                                                              → 68–78 %
```

ADR 0005 says "neither is near its rating". Seventy-odd percent, inside a body
running 10–20 K above ambient, is near enough to want the derating curve.
**ADR 0005's load table has one 5 V column and the two-regulator decision needs
it split per buck. That split is not written anywhere and it is what sizes both
parts.**

---

## §2 Analog front end — sensor, reference, buffer, ADC

```
  +12V ──[REF5050]── 5.000 V ──┬──[½ OPA2197 buffer]──┬── SKT-BREATH pin VS
             │                 │                      │
        [C-REF-OUT 10 µF]  [100 nF]                   │   U-BREATH MPXV4006DP
             │                 │                      │   case 1351-01
            AGND-local        AGND-local              │
                                                      │   P1 ◄── 400 mm tube
                                                      │           + PTFE plug
                                                      │           + ≤1 mL trap
                                                      │   P2 ◄── OPEN TO CAVITY
                                                      │           never blocked
                                                      │
              MPXV4006DP Vout  0.2 – 4.7 V ───────────┘
                     │
                     ├──[½ OPA2197 buffer]──┬──[R-SER-BREATH-INST 1k]── J-UMB pin 1
                     │   (V+ = +12V)        │                            BREATH
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
  J-UMB pin 2 AGND ──┴── analog star point ──[single tie]── PWR_GND
                            [D-TVS-BREATH]
```

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

### Derivations

**Divider** `[calc]`, matching `R-ADCDIV` `[repo] bom.csv`:

```
ratio      = 15k / (10k + 15k) = 0.600
full scale = 4.7 V × 0.6 = 2.82 V  against VREF 3.3 V → 85 % of range, 3502 counts
real play  = 2.8 kPa → 0.2 + 0.766 × 2.8 = 2.34 V → 1.40 V → 1743 counts
                                          [2.8 kPa from breath-receive-stage.md]
playable span above rest ≈ 1594 counts of 4096
```

**Why the upper leg is ≥10 kΩ** `[calc]` — the 5 V rail comes up before the dev
board's 3V3, so for a few milliseconds the divider drives the ADC input above its
own supply:

```
worst case, 3V3 at 0 and the clamp holding the pin at ~0.7 V:
  (4.7 − 0.7) / 10 kΩ = 400 µA   against a family-typical ±2 mA  [from memory]
```

The same resistor covers a saturated buffer: if the sensor or the op-amp fails
high at +12 V, `(12 − 0.7 − 3.3)/10 kΩ ≈ 800 µA`, still inside the clamp rating.

**Anti-alias** `[calc]`, matching `C-AA-ADC` `[repo] bom.csv`:

```
R_th = 10k ∥ 15k = 6.0 kΩ
f_c  = 1/(2π × 6k × 47 nF) = 564 Hz
τ    = 6 kΩ × 47 nF        = 282 µs
attenuation at the R-78E5.0's ~330 kHz switching rate = 20·log10(330k/564) = 55 dB
```

> **τ = 282 µs exceeds the 250 µs loop period, and the note-on threshold is read
> through it.** `latency-budget.md` and ADR 0003 book "SAR ADC conversion
> ~50–200 µs" and no RC term at all `[repo]`. About 5.6 % of the 5 ms budget —
> not fatal, but it belongs in the table that chose 4 kHz over 8 kHz. Found by
> `R10-keyscan-and-adc.md` §B-2 and still unapplied.

**Sample-cap charge sharing** `[calc]`, from R10's datasheet quote (20 pF sample
cap, 1.5 clocks of acquisition) `[repo] R10 B-2`:

```
I_avg = 20 pF × 4 kHz = 80 nA per volt
ΔV    = 80 nA/V × 6 kΩ = 480 µV/V = 0.048 % — about 2 LSB at full scale,
        proportional to V_in, therefore a pure constant gain term
```

Invisible: the zero is auto-tracked in firmware and the span is set by a panel
knob `[repo] 0003, 0006`.

**`C-ADC-BULK` is new and is proposed, not decided.** The MCP3202 has no `VREF`
pin — `VDD` *is* the reference `[repo] R10 B4` — so the ADC's scale factor is the
dev board's LDO output, and it has no anti-alias filter of its own. The repo's
own `C-STRIP-BULK` note puts the WS2815 PWM rate at ~2 kHz `[repo] bom.csv`,
which is exactly Nyquist for a 4 kHz sampler. 10 µF plus the existing 100 nF,
treating that pin as an analog reference rather than a logic supply.

**Key pull-ups load that same reference** `[calc]`:

```
3.3 V / (10 kΩ + 100 Ω) = 327 µA per closed key
18 keys closed = 5.9 mA step on the ADC's reference
at an LDO load regulation of ~0.3 % per 100 mA [from memory]: 0.018 % = 0.7 LSB
```

Checked and fine. Recorded because the symptom of getting it wrong is "the
breath reading moves when I press keys", which gets blamed on firmware.

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

## §3 Key scan — four 74LVC165 and 21 networks

```
  3V3 (from the dev board)
   │
   ├──[R-KEY-PU 10k]──┬──────────────► 74LVC165 parallel input
   │                  │
   │           [C-KEY 10 nF]
   │                  │
   │                 GND
   │                  │
   └── loom ──[R-KEY-SER 100R]────────┘
        conductor
        to the switch, which shorts it to GND when pressed

  ×21  (18 fitted switches + 3 reserved spare-switch positions)


   SPI3 SCK (IO38) ──┬────────┬────────┬────────┐
                     │        │        │        │
   latch    (IO7)  ──┼──┬─────┼──┬─────┼──┬─────┼──┬──  SH/LD, all four
                     │  │     │  │     │  │     │  │
                  ┌──▼──▼──┐┌─▼──▼──┐┌─▼──▼──┐┌─▼──▼──┐
  MISO   ◄────QH──┤ U-KEYS ││U-KEYS ││U-KEYS ││U-KEYS │
  (IO40)          │   RT   ││  RH   ││  LT   ││  LH   │──SER── 3V3
                  │bits 0-7││ 8-15  ││ 16-23 ││ 24-31 │
                  └────────┘└───────┘└───────┘└───────┘
                  CLK INH tied LOW on all four
                  [C-DECOUPLE-165 100 nF] × 4, one per device
```

**Chain order and `bit 0`** follow `key-layout.yaml` `[repo]`: `bit 0` is the
first bit clocked out, which is `QH` of the `right_thumb` device. **Which
parallel input (`H`…`A`) maps to which switch inside each device is not
specified anywhere** and is a layout decision — see *Still open*.

### The 100 Ω has to be at the connector, and the 10 nF at the register

ADR 0001's decisive arithmetic is `180 pC / 10 nF = 18 mV` `[repo] 0001`. In the
topology above the charge lands on the **loom** side of `R-KEY-SER`, not directly
in `C-KEY`, so the conclusion needs checking. It survives `[calc]`:

```
Loom conductor ≈ 40 pF; 180 pC injected → +4.5 V spike at the loom node
Redistribution into C-KEY through R-KEY-SER:
  τ = 100 Ω × (40 pF ∥ 10 nF) = 100 Ω × 39.8 pF = 4.0 ns
  final common voltage = 180 pC / 10.04 nF = 17.9 mV
```

The loom node spikes for about twenty nanoseconds and the register input never
moves more than 18 mV. **The mechanism is charge sharing in nanoseconds, not RC
filtering in microseconds** — which is a layout rule: `C-KEY` must be at the
register input and `R-KEY-SER` must be short and at the connector. Split them
across the board and the 4 ns becomes whatever the trace inductance says.

**The other two numbers** `[calc]`, both matching ADR 0001:

```
Release: τ = 10 kΩ × 10 nF = 100 µs
         to V_IH = 2.0 V (74LVC165A at 3.3 V [from memory]):
         t = −100 µs × ln(1 − 2.0/3.3) = 93.2 µs        ✓ "~93 µs"
Press:   τ = 100 Ω × 10 nF = 1 µs
         to V_IL = 0.8 V: t = −1 µs × ln(0.8/3.3) = 1.4 µs   ✓ "~1 µs"
Static:  3.3 V / 10.1 kΩ = 327 µA per closed key; 18 closed = 5.9 mA
```

### The 32 bits, accounted for

From `key-layout.yaml` `[repo]`:

| Bits | Use | On this board |
|---|---|---|
| 18 | Fitted switches | Full `R-KEY-PU` / `R-KEY-SER` / `C-KEY` network + loom conductor |
| 3 | Reserved spare switches (octave up, octave down, hold/preset) | Same network, same loom conductor. Plate cutouts at M3 `[repo] 0010` |
| 6 | Marker pattern | **Hard-wired to a fixed level at the register input.** Unretrofittable |
| 5 | Genuinely free | Must be pulled — "the exact fault `R-KEY-PU` exists to fix" `[repo] key-layout.yaml` |
| **32** | | 21 networks + 11 tied inputs |

**Which six bits carry the marker, and to what pattern, is not decided.** It is
hard-wired copper, so it has to be decided before this board is made. See
*Still open*.

**An option worth costing:** give the 5 free bits the full network too (26 sets
instead of 21, +15 passives) and land them on the spare loom conductors ADR 0009
already requires. That makes "add a switch later" real rather than nominal, at
the price of fifteen 0805s. It is not what the BOM says today.

---

## §4 SPI egress to the umbilical

```
  IO35 SCK  ──[R-SCLK-SER 220R]──┬──── J-UMB pin 7   ** R PROPOSED **
  IO36 MOSI ──[R-MOSI-SER 220R]──┼──── J-UMB pin 4
  IO34 CS   ──[R-CS-SER  220R]───┼──── J-UMB pin 5   ** R PROPOSED **
                                 │
                        [U-TVS-SPI 4-ch array to PWR_GND]
  IO37 MISO ── MCP3202 DOUT only (never leaves the board)
  IO39 CS   ── MCP3202 CS
```

**`R-SCLK-SER` and `R-CS-SER` are new.** `D1-missing-protection.md` finding 10
said "Series current limiting on `SCLK` and `CS` at the driving end — **ADD**"
`[repo] D1`; only `R-MOSI-SER` reached the BOM, qty 1 `[repo] bom.csv`. The
driving end is this board. ADR 0004 calls `SCLK` "the fastest edge in the
system" and sends it down 2 m of unterminated ~100 Ω twisted pair `[repo] 0004`.

Value follows `R-MOSI-SER`'s own reasoning `[repo] 0004`: 220 Ω into ~200 pF of
cable is a 7.9 MHz corner against a 2 MHz clock; if E11 wants faster, all three
come down toward 100 Ω, which is closer to a real source match on Cat5.

### The two SPI hosts, and what claims them

| Host | Devices | Clock |
|---|---|---|
| **SPI2** | DAC8568 down the umbilical, **and** MCP3202 on this board | **2 MHz for the DAC, 900 kHz for the ADC — not one clock** |
| **SPI3** | 74LVC165 chain alone, because `QH` is always driven (ADR 0001) | ~1 MHz |

> **The MCP3202 cannot run at 2 MHz.** `[from memory]`, via `R10` §B-3: 100 ksps
> at 5 V and 50 ksps at 2.7 V, 18 clocks per 12-bit conversion → **1.8 MHz at
> 5 V, 0.9 MHz at 2.7 V**, and 3.3 V is not specified, so 0.9 MHz is the number
> to design to. ADR 0003, ADR 0004, `latency-budget.md` and `power-entry.md` all
> say "SPI2 at 2 MHz", and ADR 0004 explicitly says that leaves room "for the
> MCP3202 sharing the host" `[repo]`.
>
> ESP-IDF sets `clock_speed_hz` per *device* on a shared host, so this is a
> firmware line and not a part change. **It is written nowhere.** Check the
> MCP3202 datasheet's supply-versus-speed graph before trusting the 0.9 MHz.

**Loop budget with the ADC costed properly** `[calc]` — ADR 0004's version left
it out:

```
SPI2  DAC    6 × 32 bits @ 2.0 MHz =  96.0 µs
SPI2  ADC    24 clocks    @ 0.9 MHz =  26.7 µs
SPI2  total                         = 122.7 µs of 250 µs → 49 %
SPI3  keys   32 bits      @ 1.0 MHz =  32.0 µs, concurrent → 13 %
```

**SPI2 cannot use IO_MUX and does not need to.** The S3's FSPI IO_MUX pins are
GPIO9–14 `[from memory]`, and the board spends GPIO10–13 on the QMI8658C and
GPIO14 on the matrix `[board-def] circuitpython .../pins.c`. SPI2 on
GPIO35/36/37 therefore routes through the GPIO matrix, capped around 40 MHz
rather than 80 `[from memory]`. Irrelevant at 2 MHz; recorded so it is not
rediscovered as a problem.

---

## §5 LED data

```
  IO1 ──┬──[R-LED-PD 10k]── GND   ** PROPOSED **
        │
        └──►│ 74AHCT125 gate A ├──[R-LED-SER 220R]── J-LED-L  DI   ** R PROPOSED **
        └──►│ 74AHCT125 gate B ├──[R-LED-SER 220R]── J-LED-L  BI   ** IF NEEDED **

  IO2 ──┬──[R-LED-PD 10k]── GND   ** PROPOSED **
        │
        └──►│ gate C ├──[220R]── J-LED-R DI
        └──►│ gate D ├──[220R]── J-LED-R BI

  74AHCT125 rail = 5 V (TTL thresholds, so 3.3 V in reads high)  [repo] 0014
  OE ×4 tied LOW
  [C-DECOUPLE-CARRIER 100 nF] at the package
```

**`R-LED-PD` is new and it is the fix for a real hole.** ADR 0014's defence
against latched strips is "blank both strips and the matrix as the first act at
boot" `[repo] 0014` — a firmware rule that cannot run in the window it matters.
On reset GPIO1 and GPIO2 are high-impedance inputs for the bootloader window
(order 100–300 ms `[from memory]`), `OE` is tied low so the buffer is enabled,
and an AHCT input floating near its threshold does not sit still. The buffer
squares up whatever it sees into clean 5 V edges and sends it to 25 addressable
LEDs on a 12 V rail. WS281x has no framing beyond a reset gap, so that is random
pixel data — the exact state the thermal clamp exists to prevent, at the moment
no firmware is running to clamp it. Two 0805s, and they cannot be added later.

The module page has the same idea for the same reason: `R-SPI-PULL`, six of them,
both sides of its 74AHCT125 `[repo] digital-and-supervision.md`. The instrument
end has none.

**Two open questions that change this section's part count:**

- **Does the WS2815 accept 5 V logic?** ADR 0014 flags it: "if its logic
  threshold is referenced to 12 V rather than an internal rail, 5 V shifting will
  not be enough and the part choice needs revisiting" `[repo] 0014`. If it needs
  12 V logic, the 74AHCT125 is the wrong part and this section is rebuilt.
- **Does the first pixel's `BI` need driving?** `[from memory]` the backup path
  works by each pixel taking the previous-but-one pixel's output, which leaves
  the head of the strip with nothing to take, so strips bring out four wires —
  12 V, GND, `DI`, `BI`. If so, **all four gates are used, none spare**, against
  the BOM's "Two spare gates" `[repo] bom.csv`, and the LED loom is 8 conductors
  rather than 6. Five minutes with the datasheet or the reel decides it.

**`R-LED-SER` is proposed** on the same grounds as §4: each gate drives ~420 mm
of wire to a strip, and nothing damps it. 100–330 Ω at the buffer.

**`C-STRIP-BULK` (470–1000 µF ×2) sits at the strip feed points**, which are on
this board — "bulk capacitance belongs where the current swings" `[repo] 0014`.
Two radial electrolytics are a height item in a ~20 mm cavity; see *Still open*.

---

## §6 Display loom and service header

```
  J-DISP  ──  10–11 conductors, 360 mm, up a side channel

    5 V (or +12 V — see Still open)        1
    GND                                     1
    IO5 → display RX, IO6 ← display TX      2      UART1, 921600 baud
    EN                                      1  ┐
    IO0                                     1  │  service, per ADR 0009
    U0TXD                                   1  │  and firmware/README.md
    U0RXD                                   1  │
    GND                                     1  ┘
    two spare conductors (ADR 0009)         2

  EN and IO0 each get, at this end:
     [10k to 3V3] + [100R series] + [10 nF to GND]     ** PROPOSED **
     — same network as a key line, same reason


  HDR-SERVICE  2×5, under the tail-underside cover:

    real-time board:  EN?  IO0?  U0TXD(IO43)  U0RXD(IO44)  GND
    display board:    EN   IO0   U0TXD        U0RXD        GND
```

> **`EN` and `IO0` for the real-time board may not be wireable at all.**
> CircuitPython's board definition enumerates both header columns of the
> ESP32-S3-Matrix completely — `5V, GND, 3V3, IO7…IO1` and `IO33…IO40, IO43,
> IO44`, twenty pins `[board-def] .../waveshare_esp32_s3_matrix/pins.c` — and
> neither `EN` nor `IO0` is among them. Zephyr puts the BOOT button on `gpio0 0`,
> i.e. GPIO0 is a button on the board, not a header pin `[board-def]
> zephyr:.../esp32s3_matrix_esp32s3_procpu.dts`.
>
> `pins.c` lists MCU GPIOs, so a non-GPIO `EN` pad could exist and not appear
> there. **This is a meter measurement at E1, not a conclusion.** But if it
> holds, ADR 0009's "only opening in the instrument that exists for a failure"
> cannot be wired for the board it matters most for, and the alternatives —
> flying leads to the button pads, or relying on USB-Serial-JTAG plus OTA
> rollback — fight `HDR-DEV`'s "SOCKETS not solder-down" rule or weaken the
> recovery path. **Settle it before this board is laid out.**

**ADR 0013's "four broken-out pins — UART pair and power"** `[repo] 0013` is a
statement about the display board's *pin* requirement, not about the loom.
The loom is ten or eleven conductors, over 360 mm, sharing a side channel with an
800 kHz data line and 12 V LED power — two of them (`EN`, `IO0`) asynchronous,
level-sensitive and, as documented, unfiltered. Hence the proposed networks.

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
| `U-KEYS` ×4 | 74LVC165A SOIC-16 | Key chain, `CLK INH` low, on SPI3 | `[repo]` |
| `R-KEY-PU` ×21 | 10 kΩ | Pull-up at the register input | `[repo]` + `[calc]` |
| `R-KEY-SER` ×21 | 100 Ω | In the loom path, at the connector | `[repo]` + `[calc]` |
| `C-KEY` ×21 | 10 nF X7R | At the register input | `[repo]` + `[calc]` |
| `C-DECOUPLE-165` ×4 | 100 nF X7R | One per register | `[repo]` |
| `U-ADC` | MCP3202-CI/SN | `VDD` **is** `VREF`; 3V3 from the dev board | `[repo]`; clock limit `[from memory]` |
| `R-ADCDIV` | 10 kΩ / 15 kΩ 1 % | 0.6× after the buffer | `[repo]` + `[calc]` |
| `C-AA-ADC` | 47 nF C0G | 564 Hz, and the ADC's charge reservoir | `[repo]` + `[calc]` |
| **`C-ADC-BULK`** | **10 µF X7R** | **Bulk at MCP3202 `VDD`/`VREF`. Proposed — the reference has no anti-alias and the WS2815 PWM is ~2 kHz against a 4 kHz sampler** | proposed, from `[repo] R10 B-3` |
| `U-REF-BREATH` | REF5050AIDR | 5.000 V for the ratiometric sensor | `[repo]` |
| `C-REF-OUT` | 10 µF ×2 | **Qty 2 for one part — say whether that is parallel or in+out** | `[repo]`, ambiguous |
| `U-BUF` | OPA2197IDR | ½ reference buffer, ½ breath buffer, both on +12 V | `[repo]` |
| `U-BREATH` + `SKT-BREATH` | MPXV4006DP, case 1351-01 | P1 to the tube, P2 open to the cavity | `[repo]`; **P1 identity open** |
| `R-SER-BREATH-INST` | 1 kΩ | Output protection. **No series cap here** | `[repo]` |
| `D-TVS-BREATH` ×2 | 12 V standoff, SOD-323 | `BREATH` and `AGND` legs | `[repo]` |
| `R-MOSI-SER` | 220 Ω | Series at the driving end | `[repo]` |
| **`R-SCLK-SER`** | **220 Ω** | **Proposed — `D1` finding 10 was accepted and never landed** | proposed |
| **`R-CS-SER`** | **220 Ω** | **Proposed — same** | proposed |
| `U-TVS-SPI` | SP0504BAHT, SOT-23-6 | `SCLK`, `MOSI`, `CS` + spare, to `PWR_GND` | `[repo]` |
| `U-LVLSHIFT` | 74AHCT125 SOIC-14 | LED data, 5 V rail. **Gate count depends on `BI`** | `[repo]`; `BI` `[from memory]` |
| **`R-LED-PD`** ×2 | **10 kΩ** | **Proposed — holds the strips' data low through reset** | proposed |
| **`R-LED-SER`** ×2–4 | **100–330 Ω** | **Proposed — damps ~420 mm to each strip** | proposed |
| `U-BUCK` ×2 | R-78E5.0-1.0 SIP-3 | One per dev board. **Buck B's location is open** | `[repo]` |
| `L-BUCK-IN` | 10–47 µH ≥1 A | **Qty 1 against `C-BUCK-IN`'s qty 2 "one per buck" — the two rows describe different topologies** | `[repo]`, contradictory |
| `C-BUCK-IN` ×2 | 100 µF 25 V electrolytic | **Must have real ESR; a ceramic breaks the damping** | `[repo]` + `[calc]` |
| `D-USBOR` ×2 | SS14 | **One per regulator output, not "one per source" — the OR node is a dev-board pin** | `[repo]` note is wrong |
| `D-REVSHUNT` | SS34 | At the connector, ahead of `L-BUCK-IN` | `[repo]` |
| `D-TVS-PWR` | SMAJ15A | Across the power pair | `[repo]` |
| `C-STRIP-BULK` ×2 | 470–1000 µF 16 V | At each strip feed point, which is this board | `[repo]` |
| `HDR-SERVICE` | 2×5 | **See §6 — may not be wireable for the real-time board** | `[repo]`; `[board-def]` risk |
| **`J-KEY-LH/-LT/-RH/-RT`** | **2×5, 2×4, 2×6, 2×4 IDC** | **Proposed — ribbon with alternating grounds, one per cluster** | proposed |
| **`J-LED-L/-R`** | **4-way each** | **Proposed — 12 V, GND, DI, BI** | proposed |
| **`J-DISP`** | **11-way** | **Proposed — see §6** | proposed |
| `MECH-GNDBOND` | Ring terminal + M3 | Plate to `PWR_GND`. Needs a pad and a hole on this board | `[repo]` |
| `PCB-CARRIER` | 2-layer, **outline TBD** | See *Still open* | `[repo]` says ~100 × 45 mm; not checked |
| **`TP-*`, `LK-*`** | **TBD** | **Proposed — `D2` asked for test points, shunt links and an LA header on this board and none exist in the BOM** | proposed |

---

## Loom conductor count

`[calc]`, built from the repo's own rules — **not** the "~23" that ADR 0001,
`WIRE-LOOM` and the ROADMAP all carry `[repo]`:

| | Conductors |
|---|---|
| Fitted switches | 18 |
| Reserved spare-switch positions (wire must exist pre-bond) | 3 |
| Grounds, one per four signals per ribbon | 6 |
| Two spare conductors per loom × 4 | 8 |
| **Key looms** | **35** |
| WS2815: 12 V, GND, `DI` per strip (+`BI` if needed) | 6–8 |
| Display loom (§6) | 10–11 |
| Plate ground bond | 1 |
| **Terminating on this board, excluding the umbilical** | **~53** |
| Umbilical (`J-UMB`) | 8 |

**Termination is not the problem.** `[calc]` As four IDC boxed headers matching
the ribbons ADR 0001 already specifies, the key looms occupy roughly 400 mm²
including keepout on a board of ~4500 mm². Single-row 2.54 mm headers would be
the problem — 53 × 2.54 = 135 mm of board edge, which this outline does not
have.

**Where they go is the problem.** `[calc]` 57 mm external less 2 × 4 mm acrylic
`[repo] 0009` = **49 mm internal**. `PCB-CARRIER` at 45 mm leaves **2 mm per
side** for two channels that ADR 0009 and ADR 0014 jointly require to carry two
WS2815 strips (~10 mm wide each `[from memory]`), four ribbons and the 400 mm
tube. **A 45 mm-wide carrier and open side channels are mutually exclusive.**
This is the M4 plan-section item, and the board outline depends on it.

---

## Still open

Ordered by what blocks what. The first four block layout.

- **Whether `EN` and `IO0` reach the ESP32-S3-Matrix's headers** (§6). A meter
  at E1. If not, the recovery path ADR 0009 calls "the only opening in the
  instrument that exists for a failure" has to be redesigned, and the options
  all cost something the BOM currently forbids.
- **Which face of the dev board carries the matrix, and its outline and header
  row spacing** (§7). Decides underside-mount versus a ~22 mm cutout, and with
  it the whole board's routing.
- **The board outline, against a plan section at the tail** — carrier, two LED
  strips, four ribbons, the breath tube and the U-bolt in 49 mm of internal
  width and ~20 mm of cavity. "~100 × 45 mm" is an assumption, not a fit.
- **Where buck B lives.** ADR 0013's carrier list puts both regulators here;
  ADR 0013's own reasoning wants the display board's WiFi transients absorbed
  locally, which a regulator 360 mm away does not do. Either it moves to the
  display board and +12 V goes up the loom, or `C-BULK-DISP` does the job and
  the location is arbitrary. Pick one before `J-DISP`'s conductor list is fixed.
- **The marker pattern: which six bits, and to what levels.** Hard-wired copper
  on this board, and firmware checks it on every read `[repo] 0001`. Unretrofittable.
- **The `H`…`A` to switch mapping inside each 74LVC165.** `bit 0` is defined
  `[repo] key-layout.yaml`; the other 31 are a layout decision that firmware
  then has to be told about.
- **Whether the sensor is reachable after bonding**, which decides whether
  `SKT-BREATH` earns its place. ADR 0003 wants a replaceable wear part and a
  trap "clearable without disassembly"; ADR 0009 gives a 12 × 40 mm cover over a
  2×5 header. Those do not meet. Either the cover becomes a real hatch with the
  sensor and trap under it, or the socket is decoration.
- **Which port of the MPXV4006DP is P1** `[repo] 0003`. Needed for layout.
- **The etherCON variant at the instrument end** `[repo] 0004`, which decides
  whether this board carries an RJ45 jack footprint (~16 × 14 mm, not in the
  BOM) or eight wires. ADR 0004 defers it to E12/M7, which is after E13.
- **The WS2815's data threshold, and whether `BI` needs driving** (§5). Decides
  whether the 74AHCT125 is the right part at all, and whether it has spare gates.
- **The MCP3202's maximum clock at 3.3 V** (§4). 0.9 MHz is an interpolation
  from a search summary, not a datasheet reading.
- **`C-REF-OUT` qty 2** for one REF5050 — parallel, or input and output?
  The reference's stability depends on it and nobody has opened the datasheet.
- **`L-BUCK-IN` qty 1 against `C-BUCK-IN` qty 2.** One LC and one bulk cap, or
  two LCs and a missing inductor.
- **Test points, shunt links and an LA header.** `D2-missing-testability.md`
  asked for them on this board; the BOM has none. E14 re-runs E1–E11 on this
  board and M8 does failure injection on it, and neither has a documented means
  of measurement. One-shot.
- **Conformal coating and the sensor ports.** `MECH-COAT` must mask both
  `[repo] 0009`, and the part is socketed, which makes masking easier and
  retention worse.
