# B8 — Noise, interference and crosstalk

Independent review of Woody at Phase 0, working only from `README.md`,
`ROADMAP.md`, `docs/decisions/*`, `docs/reference/*` and `hardware/bom.csv`.
No schematic or layout exists yet, so every coupling below is estimated from the
topology and part values the documents commit to. Where a document gives a
number I use it and say so; where I supply one I say whether I verified it or am
working from memory.

**Headline.** The analog architecture is right. The `AGND` sense-return, the
REF5050 ratiometric supply and the 500 Hz band-limit together put the breath
jack's total coupled noise at roughly **60 µV RMS on a 10 V output (−104 dB)**,
and I could not find a path that breaks it. Nothing reaches the pitch CV above
**0.03 cents**. The problems are not in the analog channel the ADRs spend their
effort on — they are in **the sampler** (an anti-alias filter whose corner is
five times lower than claimed, and a single pole guarding a 4 kHz sampler), in
**the instrument's own digital wiring** (the fastest edges in the system are the
only ones with no series termination), and in **one DC reference that is never
defined**.

---

## Aggressor inventory

Bold = not inventoried anywhere in the documents; I added it.

| Aggressor | Fundamental | Amplitude at source | Lives | Worst victim |
|---|---|---|---|---|
| R-78E5.0 buck switching | ~500 kHz *(assumed by ADR 0003; unverified)* | ~200 mA input pulses, 30–50 mV output ripple | bottom cluster | ADC via aliasing |
| **Buck in pulse-skip / PFM at light load** | **unknown, 10–100 kHz** | same | bottom cluster | ADC via aliasing |
| WS2815 strip supply current | ~2 kHz PWM | 206 mA pk fundamental @ 40 % duty | side channels, full length | +12 V, `PWR_GND` |
| WS2815 data | 800 kbit/s, 74AHCT125 edges ~3 ns | 5 V into 420 mm unterminated | side channels | key chain |
| **WS2815 backup-data conductor** | same | same | side channels | key chain |
| 8×8 WS2812C matrix supply | ~2 kHz PWM | 300–960 mA @ 5 V | **on the real-time board, at the analog star** | ADC reference/ground |
| 8×8 matrix data (GPIO14) | 800 kbit/s | 3.3 V, short | on-board | — |
| AMOLED panel current | content-dependent steps | tens of mA @ 3.3 V | top | 5 V rail |
| **AMOLED ELVDD/ELVSS supply** | **a boost/charge pump, freq unknown** | — | top, on the LilyGO board | 5 V rail, radiated |
| WiFi TX bursts | 250 µs–2 ms bursts | ~350 mA @ 3.3 V → 176 mA @ 12 V | top | umbilical, rack bus |
| **WiFi burst *envelope*** | **60 Hz (F6 telemetry), 9.8 Hz (beacons)** | same | top | everything — no filter in the design attenuates 60 Hz |
| Umbilical SPI: SCLK / MOSI / CS | **~2 MHz, not 0.6 MHz** (finding 5) | 3.3 V, 32 % bus duty | 2 m cable | `BREATH`/`AGND` pair |
| 74x165 chain SCK / SH-LD / QH | ~1 MHz, LVC edges | 3.3 V over 75–205 mm | mid-body | itself |
| Inter-MCU UART | 921.6 kbaud | 3.3 V over 170 mm | top↔mid | — |
| USB 2.0 (bring-up only) | 480 Mbit/s + **a second earth reference** | — | tail | in-amp common mode |
| TPS2553 inrush ramp | one-shot | 0→400 mA | module | rack bus |

## Victim inventory

| Victim | Node impedance | Band that matters | What defends it |
|---|---|---|---|
| MPXV4006DP supply (`VS`) | ~0.02 Ω (OPA2197 buffered) | DC–500 Hz, **ratiometric** | REF5050 PSRR |
| Sensor output 0.2–4.7 V | ~1 kΩ internal | DC–159 Hz | short run, bottom placement |
| `BREATH` on the umbilical | **~9.1 kΩ at the module end** | DC–500 Hz | twisted pair, band-limit |
| `AGND` | 0.17 Ω at instrument, **open at module** | DC–500 Hz | carries no current by construction |
| In-amp differential input | GΩ, 10 kΩ series | **DC–1 MHz** (no filter in front) | nothing (finding 7) |
| ADC input (MCP3202 CH0) | 6 kΩ ‖ 220 nF | DC–2 kHz + **every alias band** | one RC pole (findings 2, 6) |
| MCP3202 V<sub>REF</sub> = V<sub>DD</sub> = dev-board 3V3 | LDO | DC–10 kHz | AMS1117-class PSRR |
| DAC8568 AVDD | LM317LZ, 50 µV RMS | DC–100 kHz | LM317 + ADJ bypass |
| DAC internal 2.5 V reference | on-die | DC | — |
| Pitch CV (1 cent = 833 µV) | 1 kΩ out | DC–20 kHz | OPA2197 PSRR, LT5400 |
| Mod 1–4 CV | 1 kΩ out | DC–2 kHz | as above |
| Module ±12 V at the op-amps | shared node with the umbilical feed | 60 Hz–500 kHz | ferrite + bulk (ineffective <10 kHz) |
| Key-chain `QH` / `SH-LD` | high-Z at one end | DC–50 MHz | marker pattern, series R |

---

# Findings

## 1. The breath receiver's input common-mode voltage is never defined, so an unplugged instrument leaves the breath jack at an arbitrary level — the exact failure ADR 0005 added the pulldown to prevent

**Severity: MAJOR**

**Where.** ADR 0005: *"Pull down the module's breath receive input, so that an
instrument which is switched off — **or unplugged** — presents 0 V rather than a
floating buffer output."* ADR 0003: *"Put the pulldown **differentially across
BREATH–AGND**, not on one leg. A shunt on a single leg does not symmetrise the
way a series element does — 100 kΩ on the + input alone would cap CMRR near
19 dB."* `hardware/bom.csv`: *"R-PD-BREATH, 100k, **DIFFERENTIAL across
BREATH-AGND** not one leg."*

**Why.** Both statements are individually correct and together they leave the
in-amp with **no DC path from either input to module ground**. Trace every
element: `BREATH` → 10 kΩ → connector; `AGND` → 10 kΩ → connector; 100 kΩ
*between* them; INA821 inputs at GΩ; the `REF` pin sets the *output* reference,
not the input common mode. With the cable in, common mode is defined by
`PWR_GND` — fine. With the cable **out**, the only remaining currents are the
in-amp's input bias currents.

INA821 I<sub>B</sub> ≈ 0.5 nA (from memory, unverified) into the pin plus board
capacitance, call it 5 pF:

```
dV/dt = 0.5 nA / 5 pF = 100 V/s  →  a rail in ~120 ms
```

The 100 kΩ holds the *difference* at 0 V while both inputs ramp together to a
supply rail. INA821's input common-mode range on ±12 V does not reach the rails,
so the part leaves its linear region and the output goes wherever its internal
topology takes it — typically hard to a rail. **The breath jack then sits at up
to +10 V into whatever it is patched to**, indefinitely, which is a drone in the
rack: the same failure class ADR 0004 built the watchdog for, arriving by a path
the watchdog cannot see because the DAC is not involved.

The naive fix fails for exactly the reason ADR 0003 gives. Adding 100 kΩ from
`BREATH` to ground alone, against a leg whose source impedance is 10 kΩ versus
`AGND`'s 0.17 Ω:

```
CMRR = 20·log10( (100k + 10k) / 10k ) = 20·log10(11) = 20.8 dB
```

which is the "19 dB" the ADR quotes. So the requirement and the CMRR constraint
really are in tension — but the tension is resolvable, and the resolution is not
recorded.

**Proposal.** Restore balance and define the common mode:

- **Matched series resistors in *both* legs**, 10.0 kΩ **0.1 %**, not "10 kΩ and
  unmatched". The in-amp does not need them matched; the CM-defining network
  below does.
- **1 MΩ from each input leg to module analog ground.** Leg attenuation
  1M/(1M+10k) = 0.990099 on both sides. With 0.1 % series parts the worst-case
  mismatch is 20 Ω, giving a leg-gain difference of 2×10⁻⁵ and a **CMRR floor of
  94 dB** — at or above the chip's own spec, so it costs nothing measurable. With
  1 % parts the floor is 74 dB, which is below the 60 dB the scheme needs but
  wastes margin; 0.1 % 10 kΩ resistors are commodity.
- DC current drawn through `AGND` by this network at 67 mV of common mode is
  67 mV / 1.01 MΩ = **66 nA**, which develops **11 nV** across the conductor.
  `AGND` still "carries no power current."
- Keep the 100 kΩ differential pulldown; it now does the job it was specified for
  (0 V out when the instrument is off) on top of a defined common mode rather
  than instead of one.

**Confidence: high** that the common mode is undefined as specified — it follows
from the three quoted sentences with no assumptions. **Medium** on the exact
behaviour when it saturates, which depends on INA821 internals I have not
verified.

**Falsified by:** at E10, power the module with no umbilical attached and scope
the BREATH jack for 60 s from power-on. If it sits within a few millivolts of
0 V and stays there, either the part self-biases or something else provides a CM
path, and this finding is wrong. Repeat with a finger near the open etherCON —
if the output moves, the inputs are floating.

---

## 2. The anti-alias filter's corner is 121 Hz, not the 600 Hz claimed, because the divider's Thévenin impedance is 6 kΩ — costing 1.3 ms of unbudgeted latency on the note-gate path and 4.4 dB of droop inside the sensor's own bandwidth

**Severity: MAJOR**

**Where.** ADR 0003: *"**220 nF gives a ~600 Hz corner and 58 dB at 500 kHz**"*
and *"Together with the divider it **settles well inside the 250 µs loop
period**."* `hardware/bom.csv`: `R-ADCDIV, 10k / 15k 1% metal film, 0.6x divider`
and `C-AA-ADC, 220nF X7R, ~600Hz corner, 58dB at 500kHz`.

**Why.** The cap sees the divider's Thévenin resistance, not one leg:

```
R_th = 10k ‖ 15k = 6.00 kΩ
f_c  = 1 / (2π · 6000 · 220 nF) = 120.6 Hz      (claimed: 600 Hz)
τ    = 6000 · 220 nF = 1.32 ms                  (claimed: < 250 µs)
```

The 600 Hz figure requires R = 1/(2π·600·220 nF) = **1206 Ω**, so the ADR's
arithmetic is self-consistent against a 1.2 kΩ source — it was simply never
re-run when the divider was pushed to ≥10 kΩ for the ESD-clamp reason in the same
section. Two consequences:

- **Latency.** A single pole with τ = 1.32 ms delays a threshold crossing on a
  realistic 10 ms breath ramp by roughly τ. The latency budget's digital-copy
  total is 2.6–2.9 ms against a 5 ms target; this adds **1.32 ms** to it,
  reaching ~4.2 ms, and the filter appears **nowhere in that table**. It is
  consumed silently. The note gate is the one thing on the digital path that is
  latency-critical.
- **Signal droop.** At the sensor's own 159 Hz corner the filter is already
  −4.4 dB, so the two poles interact: the ADC copy is not a faithful copy of the
  CV, it is a slower one. Breath curve shaping (ADR 0003) and the mod-channel
  source are both fitted to the ADC copy, so the response the player tunes
  against is not the response at the jack.
- The "settles well inside the 250 µs loop period" claim is wrong by **5.3×**.

**Proposal.** **Change C-AA-ADC to 47 nF.** With the same 10 k/15 k divider:

```
f_c  = 1 / (2π · 6000 · 47 nF) = 564 Hz
τ    = 282 µs
atten at 500 kHz = 20·log10(500k / 564) = 58.9 dB
```

which hits the ADR's own 58 dB target exactly, restores the intended 600 Hz-class
corner, and cuts the added latency from 1.32 ms to 282 µs. Check the second job
the cap does — the MCP3202's sample-capacitor reservoir. At C<sub>s</sub> ≈ 20 pF
(from memory, unverified), charge redistribution is 20 pF/47 nF = 4.3×10⁻⁴ =
1.7 LSB, recovering 59 % between 250 µs samples, so the steady-state error is
~2.9 LSB ≈ 0.07 % of span. That is a fixed gain error, not noise, and it
calibrates out. **Then add the filter, explicitly, as a row in
`docs/reference/latency-budget.md`** — a 282 µs term that is currently invisible.

**Confidence: very high.** The arithmetic is unambiguous and the 1206 Ω
back-solve pins down exactly how the error was made.

**Falsified by:** at E2, inject a 1 V step at the buffer output and scope the ADC
pin. A 10–90 % rise of ~2.9 ms confirms 121 Hz; ~620 µs confirms 564 Hz. Or sweep
a signal generator into the buffer and find the −3 dB point.

---

## 3. The WS2815 data lines are the fastest edges in the instrument and the only signals with no series termination — they couple 370–770 mV onto key-chain conductors sharing the same side channel

**Severity: MAJOR**

**Where.** `hardware/bom.csv` terminates everything else: `R-TERM-CHAIN, 33-68R
1%, Series termination on key-chain clock and latch at the MCU`;
`R-MOSI-SER, 220R 1%, Series termination on MOSI at the driving end`. There is no
entry for the LED data lines. ADR 0014: *"A **74AHCT125** is the standard answer
— powered from 5 V with TTL input thresholds … and it **outputs a clean 5 V
edge**."* ADR 0013: the side channels are *"the natural route for the wiring
looms"*, and ADR 0014 confirms *"**Both channels carry LEDs, and the wiring looms
share them.**"*

**Why.** A 74AHCT125 transitions in ~3 ns (from memory, unverified; the family is
specified into 50 pF). Driving 420 mm of unterminated wire from a ~25 Ω output
into a high-impedance WS2815 input:

- One-way propagation over 420 mm ≈ 2.1 ns, comparable to the edge, so the line
  behaves as a transmission line. Reflection coefficient at the source is
  (25−200)/(25+200) = **−0.78**, at the open far end **+1**. The far-end step
  overshoots to ~2× and rings at 1/(4·2.1 ns) ≈ **119 MHz**, decaying ~0.78 per
  round trip — roughly **80 ns of ringing on every edge, 800 000 times per
  second**, on two conductors running the whole length of a sealed body.
- Capacitive coupling to a parallel key-chain conductor. For 24 AWG at 5 mm
  spacing, C ≈ πε₀/acosh(s/d) = 9.3 pF/m → **3.9 pF over 420 mm**. Against the
  victim conductor's own ~26 pF to ground, the asymptotic coupled step onto a
  high-impedance victim end is

```
5 V · 3.9 / (3.9 + 26) = 653 mV        (3 mm spacing: 768 mV; 10 mm: 543 mV)
```

  and onto a victim held by a ~70 Ω driver, I = C·dV/dt = 3.9 pF · 5 V/3 ns =
  6.5 mA → **455 mV**.

The victims are the two conductors ADR 0001 identifies as fatal to corrupt:
`QH` (high-impedance at the MCU end — *"one corrupted 32-bit word becomes one
spurious note-on at full velocity, with no filtering"*) and `SH/LD` (*"asynchronous
and level-sensitive. Any glitch below V_IL during the 32-clock shift re-loads all
four registers"*). 74LVC165A at 3.3 V has V<sub>IL</sub> = 0.8 V, so the margin
against a 455–768 mV glitch is **1.0–1.8×**, not the comfortable figure the
BOM's *"74HC preferred over LVC for ~2x input noise margin"* note implies.

**Proposal.** Three items, all free, all unrecoverable after the body is bonded:

- **100–150 Ω series at each 74AHCT125 output**, on both strip data lines and on
  the backup-data conductors if they are driven. This raises the source impedance
  to ~130–175 Ω, close to the wire's Z₀, killing the ringing in one round trip,
  and slows the edge at the wire to τ = 150 Ω · 31 pF = 4.7 ns. Coupled glitch
  drops from ~455 mV to **~68 mV** (a 20 ns edge in the table above). WS2815's
  T0H minimum is 300 ns, so a 5 ns edge is 60× faster than the protocol needs —
  this costs nothing.
- **Terminate the key chain's `SCK` *and* `QH`, not just clock and latch.** The
  BOM terminates "clock and latch"; `QH` is driven *by* the far register back
  toward the MCU and is the one line whose corruption produces a note.
- **Physically separate the LED data conductors from the key-chain loom within
  the side channel.** Doubling the spacing from 3 mm to 10 mm buys 1.4× on its
  own; running them in *different* side channels (LEDs in one, key loom in the
  other) buys far more and costs nothing at M4.

**Confidence: high** on the mechanism and the ordering. **Medium** on the
absolute millivolts — the capacitance depends on a loom geometry that does not
exist yet, so treat 400–800 mV as "same order as the noise margin", which is the
decision-relevant conclusion.

**Falsified by:** the measurement the ROADMAP already lists — *"Key-chain error
counter over an hour, LEDs and WiFi active"* at E4. A zero count with LEDs
animating at full rate over an hour, on a loom at final length and spacing, kills
this. A non-zero count confirms it. Separately: scope `SH/LD` at the far register
with a 10× probe while the strips run, and look for the 119 MHz burst.

---

## 4. The 8×8 matrix draws up to 960 mA through the same board and ground as the breath ADC and the analog star point — the LED-induced step ADR 0014 asks to measure is 4–24 LSB and comes from the matrix, not the side strips

**Severity: MAJOR** (it is a carrier-layout decision, taken at E13, inside a body
that is bonded at M6)

**Where.** ADR 0003: *"The star point is the analog ground pour on the bottom
cluster board, at the sensor and reference, immediately adjacent to the umbilical
connector."* ADR 0007: *"the very bottom tip … the real-time board."* ADR 0014:
*"**Full field white: +960 mA @ 5 V**"* on that same board, and *"the matrix is
physically **on** the MCU."* ADR 0014's grounding section says only *"Keep the LED
return off the analog section's local ground at that end"* — a rule with no
number attached.

**Why.** ADR 0003 moved the sensor to the bottom partly to escape LED current:
*"At the top, the analog pair must traverse the whole body through side channels
shared with pulsed LED current. At the bottom it sits where the umbilical
leaves."* ADR 0014 then placed 64 LEDs on the board it moved to. The two
decisions are individually sound and were not composed.

The matrix's return current leaves the dev board through its header GND pin(s)
into the carrier. A 0.1 in header pin is ~5 mΩ and 30 mm of 1 mm-wide 1 oz trace
is ~15 mΩ, so 20 mΩ of shared impedance between the dev board's ground and the
analog star is a realistic un-designed outcome:

| Matrix current | Shared 10 mΩ | Shared 20 mΩ |
|---|---|---|
| 300 mA (half the 3 W clamp) | 3.0 mV = 3.7 LSB = 6.5 Pa | 6.0 mV = 7.4 LSB = 13.1 Pa |
| 500 mA | 5.0 mV = 6.2 LSB = 10.9 Pa | 10.0 mV = 12.4 LSB = 21.8 Pa |
| 960 mA (full field, pre-clamp) | 9.6 mV = 11.9 LSB = 20.9 Pa | 19.2 mV = 23.8 LSB = 41.8 Pa |

(LSB = 3.3 V/4096 = 806 µV; referred to the sensor through the 0.6× divider and
766 mV/kPa.)

This is the number ADR 0014 says to go and get: *"Size the note-on/note-off
hysteresis from the **measured** LED-induced step."* My contribution is that its
dominant source is 20 mm away on the same PCB, not 400 mm away in the side
channels, and that the ADR's proposed fix — *"Drive the LEDs from the post-gate,
slew-limited breath value"* — **breaks the feedback loop but not this coupling.**
The ground bounce is there whenever the matrix is lit, whatever drives it,
including when an alarm state preempts (which ADR 0014 says cannot be configured
off). It is also modulated at the ~2 kHz PWM rate, which is exactly Nyquist for
the 4 kHz loop (see finding 6).

**Proposal.** All three are layout rules for E13:

- **Kelvin the analog star.** `AGND`, the REF5050 ground, the OPA2197 ground, the
  MPXV4006DP ground and the MCP3202 ground return to a single point, and the
  *only* connection from that point to the rest of the instrument's ground is one
  deliberate link, placed at the umbilical connector, downstream of every LED and
  dev-board return.
- **Give the matrix its own 5 V and ground pins on the header** if the
  ESP32-S3-Matrix breaks out more than one GND, and route them as a pair straight
  to the R-78E5.0's output and its return — never through the analog region.
- **Put the matrix's own bulk capacitance on the carrier at that header pin**
  (100–220 µF). The BOM has `C-STRIP-BULK` at the strip feed points and
  `C-BULK-DISP` at the display board; the matrix — the largest single 5 V
  transient load in the instrument — has nothing.

**Confidence: high** that the coupling exists and is in the tens-of-LSB class.
**Low-medium** on the 20 mΩ, which is a guess about a board not yet drawn; the
point is that it is a free choice now and an unfixable one after M6.

**Falsified by:** at E1/E4, drive the matrix from dark to full field while
watching the ADC's reading of a static pressure source. A step below ~2 LSB means
the shared impedance is under ~2 mΩ and this does not matter. Measure with a
differential probe between the dev board GND pin and the analog star.

---

## 5. The umbilical SPI clock is specified at ~0.6 MHz, which does not close the loop — the real rate is ~2 MHz, and E11 is written to validate the wrong number

**Severity: MAJOR**

**Where.** ADR 0004: *"**Breath analog, 5 channels at 2 kHz — 0.32 Mbit/s —
~0.6 MHz**"*, repeated verbatim in ADR 0003. ROADMAP E11: *"SPI (~0.6 MHz) and
the analog breath pair over the real cable at length."* Against ADR 0006, which
**explicitly corrects the rate**: *"The table used to say 2 kHz and it was wrong
twice over … **Mod 1–4: 4 kHz**"*, and `latency-budget.md`, which costs
*"six DAC channels 96 µs"* and *"SPI to DAC over umbilical ~50 µs, **2 MHz**"*.
ADR 0001 also says *"comfortable at **2MHz** SPI over twisted pair."*

**Why.** The DAC8568 frame is 32 bits. At the rate ADR 0006 settled:

```
5 channels × 32 bits × 4 kHz = 640 kbit/s of payload
160 bits at 0.6 MHz         = 267 µs   >  the 250 µs loop period
160 bits at 2.0 MHz         =  80 µs   =  32 % bus duty
6 × 32 bits at 2.0 MHz      =  96 µs   ←  exactly the latency budget's figure
```

So **0.6 MHz does not fit one pass inside one period**, before CS framing gaps or
the ADC transaction that shares SPI2. The 0.32 Mbit/s figure is 5 × 32 × **2 kHz**
— ADR 0004's bandwidth table was never re-run when ADR 0006 doubled the rate.
The latency budget's own loop-duty arithmetic already assumes 2 MHz, so two
documents disagree by 3.3×, and the ROADMAP inherited the stale one.

For this review the consequence is direct: **every crosstalk and emission
estimate in ADR 0004 was made against the wrong aggressor.** The bus is active
32 % of the time rather than the ~13 % implied, the fundamental moves from
0.6 MHz to 2 MHz, and E11 — the milestone that exists to catch what the pin-map
reasoning gets wrong — would pass at a clock the instrument cannot actually use.
The `latency-budget.md` "SPI to DAC ~50 µs" row is itself a 0.6 MHz number
(32 bits/0.6 MHz = 53 µs) sitting in a table whose loop arithmetic is 2 MHz.

**Proposal.** Fix the number in ADR 0004 and in ROADMAP E11 to **2 MHz**, and
run E11's logic-analyser check at 2 MHz **and** at 4 MHz, so the margin is known
rather than the operating point merely confirmed. Note that the edge *rate*, not
the clock, dominates crosstalk — so the more useful change is to add to E11:
*measure SCLK's 20–80 % transition time at the module end and, if it is under
~10 ns, raise the series termination until it is 20–30 ns.* At 2 MHz a 30 ns edge
is still 6 % of the bit period.

**Confidence: very high.** This follows entirely from the project's own numbers.

**Falsified by:** count SCLK cycles per 250 µs frame on a logic analyser at E7.
If five 32-bit channels plus an ADC transaction genuinely close inside 250 µs at
0.6 MHz, I have the frame width wrong.

---

## 6. The sampling system has one pole of alias protection sized against one assumed aggressor frequency — the WS2815 PWM's second harmonic lands on the 4 kHz sampler and folds into the breath band as a tone that wanders with temperature

**Severity: MAJOR**

**Where.** ADR 0003 makes the drift argument itself, for the buck only:
*"A buck running at 500 kHz sampled at 4 kHz folds to DC; at 498 kHz it folds to
2 kHz, and at 496.1 kHz to **100 Hz — directly into the breath band** … the alias
frequency **moves** with the converter's load-dependent switching frequency, so it
is a wandering tone rather than a fixed one."* Then ADR 0014: *"a WS2815 run
modulates its draw by hundreds of milliamps at the **~2 kHz PWM rate**."*

**Why.** The sampler runs at F<sub>s</sub> = 4 kHz, so Nyquist is **2 kHz** —
which is the WS2815's PWM fundamental. Its second harmonic sits at 4 kHz and
aliases to DC. These are uncompensated on-die RC oscillators; ±10 % over process
and over the instrument's documented 10–20 K interior rise is conservative:

```
f_pwm ∈ [1.8, 2.2] kHz  →  2·f_pwm ∈ [3.6, 4.4] kHz
alias = |2·f_pwm − 4000| ∈ [0, 400] Hz     ← inside the breath band
```

Exactly the ADR's own buck argument, for an aggressor 250× closer in frequency
and with far less filter in front of it:

| Aggressor | Filter attenuation, 121 Hz corner (as drawn) | at 564 Hz corner (finding 2) |
|---|---|---|
| Buck, 500 kHz | 72 dB | 59 dB |
| **LED PWM 2nd harmonic, 3.6 kHz** | **29.5 dB** | **16.2 dB** |
| WiFi burst envelope, 60 Hz | ~0 dB | ~0 dB |
| AMOLED content steps, DC–100 Hz | ~0 dB | ~0 dB |

The amplitude is modest — at 6 mV of matrix ground bounce (finding 4), a 25 %-duty
square's second harmonic is (2A/2π)·sin(π/2) = 0.318 A = 1.9 mV, giving ~300 µV
of in-band alias after a 564 Hz pole, about 0.4 LSB. That is not audible on its
own. What makes it a MAJOR is structural: **a single pole is not an anti-alias
filter for a 4 kHz sampler**, the design's guard was sized for one aggressor at
one assumed frequency, and there are at least four aggressors in the sampler's
alias bands whose frequencies nobody has measured.

The 60 Hz WiFi envelope deserves separate note. `F6` puts WebSocket telemetry at
60 Hz, so the radio transmits 60 times a second and the *envelope* of those
bursts is a 60 Hz component on every rail. **No filter anywhere in this design
attenuates 60 Hz** — not the 564 Hz anti-alias pole, not the 500 Hz band-limit,
not the 2 kHz module reconstruction filter. It is below all of them. The only
thing that rejects it is the in-amp's CMRR (3.2 µV at the jack, fine) and the
REF5050's PSRR. It reaches the ADC as a real in-band signal, not an alias.

**Proposal.** Three, in order of value:

- **Make the ADC filter two-pole.** The OPA2197 buffer is already there; an RC
  in its feedback plus the existing RC gives a 2-pole ~500 Hz response:
  **32 dB at 3.6 kHz** instead of 16, and >110 dB at 500 kHz. One resistor and
  one capacitor.
- **Phase-lock the LED update to the ADC sample.** Update both strips and the
  matrix at an exact submultiple of the 4 kHz loop, at a fixed offset, and take
  the ADC conversion in the quiet window between LED refreshes. This turns an
  asynchronous beat into a fixed DC offset that auto-zero absorbs. It is a
  firmware scheduling rule and it is free — and it is the only fix that also
  works against the matrix bounce in finding 4.
- **Measure, rather than assume, every aggressor's frequency.** The ROADMAP has
  no row for this. Add to E1: *the R-78E5.0's switching frequency across the full
  load range, 50 mA to 900 mA, including whether it enters pulse-skipping.* Add
  to E4: *the WS2815 PWM frequency, cold and after a 20-minute soak.* If the buck
  skips pulses at light load its repetition rate can fall to tens of kHz, where
  even a 564 Hz pole gives only ~31 dB and 20.1 kHz aliases to 100 Hz — the
  ADR's own nightmare case, at a frequency it did not consider.

**Confidence: high** on the mechanism and the filter arithmetic. **Medium** on
the ±10 % oscillator tolerance (from memory of the WS281x family; the WS2815
datasheet may specify better). **Medium** on the 2 kHz PWM rate itself — I am
taking the project's figure and have not verified it against the datasheet.

**Falsified by:** the ROADMAP already has the right instrument for this — *"A
signal generator driving a known waveform into the ADC front end also
characterises the full digitise-process-output chain's frequency response and
exposes any aliasing."* Sweep 1 Hz to 600 kHz into the buffer and plot what comes
out of the 4 kHz sampler. Every alias in this finding will appear as a spur, or
none will.

---

## 7. The in-amp is the unprotected front door: ~3.8 mV of 2 MHz differential arrives at its pins because the module's band-limit sits behind it

**Severity: MINOR**

**Where.** ADR 0003: *"**Band-limit at both ends, around 500 Hz.** … SPI edges,
LED PWM, WiFi bursts and switching-supply hash all live far above it."* And, of
the in-amp: *"it **absorbs the ~2.13× scaling stage** so net part count is flat or
lower."* If the in-amp provides the gain, the 500 Hz pole is naturally placed
*after* it — leaving nothing in front.

**Why.** Cat5e's specified pair-to-pair **capacitance unbalance** is ≤330 pF per
100 m = 3.3 pF/m (from memory of TIA-568; the mutual capacitance limit within a
pair is 5.6 nF/100 m = 56 pF/m, which I am more confident of). Over 2 m that is
6.6 pF of *uncancelled* coupling from any aggressor conductor into the
`BREATH`/`AGND` pair. The pair is grossly unbalanced in impedance — `BREATH`
presents ~9.1 kΩ at the module (10 kΩ series ‖ 100 kΩ pulldown) while `AGND`
presents 0.17 Ω — so common-mode injection converts to differential at the full
9.1 kΩ:

| Aggressor | V at the conductor | Differential at the in-amp pins | After a 500 Hz pole |
|---|---|---|---|
| LED PWM, 2 kHz | 33 mV | 25 µV | 6.2 µV |
| Buck residue, 500 kHz | 5 mV | 943 µV | 0.94 µV |
| **SPI, 2 MHz (finding 5)** | **5 mV** | **3.8 mV** | **0.94 µV** |

Post-filter the numbers are trivial — the 500 Hz band-limit is doing enormous
work and it is the single best decision in the noise design. But **millivolts of
2 MHz reach the in-amp's input pins**, and an in-amp at G ≈ 2 has perhaps 1 MHz
of bandwidth, a collapsing CMRR above ~1 kHz, and an input stage that can rectify
what it cannot amplify. INA821/828 carry integrated EMI filtering, which is
probably enough — but "probably" is load-bearing for the project's most defended
signal.

**Proposal.** Put the 500 Hz pole *in front of* the in-amp, differentially, where
it costs nothing extra. With 10.0 kΩ already in each leg, add **16 nF across the
two inputs and 100 pF from each input to module analog ground**:

```
differential corner = 1/(2π · 20 kΩ · 16 nF) = 497 Hz
common-mode corner  = 1/(2π · 10 kΩ · 100 pF) = 159 kHz
C_diff / C_cm = 160  →  5 % CM-cap mismatch degrades CMRR no further than 76 dB
```

This is the standard in-amp EMI front end, it *is* the band-limit the ADR already
asks for, and it removes the need for a separate filter after the in-amp. Keep
C<sub>diff</sub> ≥ 10× C<sub>cm</sub> so the CM caps' tolerance cannot unbalance
the pair — that ratio is the whole trick.

**Confidence: medium.** The coupling arithmetic rests on a capacitance-unbalance
figure I am quoting from memory, and real cables are usually far better than the
limit. The proposal is worth doing regardless — it is two capacitors and it
relocates a filter the design already specifies.

**Falsified by:** at E11, scope the in-amp's input pin directly (not the output)
with the SPI running at full rate. Under ~200 µV of 2 MHz there and this is
noise-floor.

---

## 8. The breath path's filter group delay is 636–716 µs, not the "< 0.2 ms" the latency budget allows for it

**Severity: MINOR**

**Where.** `latency-budget.md`, breath CV at the jack: *"Buffer, cable, in-amp,
output filter | **< 0.2 ms** | Propagation plus filter group delay only."*
Against ADR 0003's *"Band-limit at both ends, around 500 Hz"* and ADR 0006's
*"Breath wants a gentler filter, ~2 kHz."*

**Why.** A single real pole's group delay at DC is τ = 1/(2πf<sub>c</sub>):

```
500 Hz pole  → 318 µs      (specified at BOTH ends: 636 µs)
2 kHz pole   →  80 µs      (module output filter, ADR 0006)
Total        → 716 µs, against a "< 0.2 ms" allowance — 3.6× over
```

One 500 Hz pole alone exceeds the whole allowance. The corrected analog breath
total is **~2.9 ms**, not 2.4 ms. Still comfortably inside 5 ms, so nothing
breaks — but the budget's two largest terms are no longer *"both physical rather
than architectural"*, as the document claims. About a quarter of the path is now
filters the designer chose.

A second, smaller item in the same place: ADR 0006 gives breath a *"~2 kHz
reconstruction filter"* to smooth *"the steps"* — but breath is analog end to end
and has no steps. That pole is vestigial from the digital-breath era and costs
80 µs for nothing.

**Proposal.** Fold finding 7's differential network into a **single** 500 Hz pole
at the module input and raise the instrument-end buffer's corner to ~20–50 kHz
(which still gives 20–26 dB at 500 kHz and lets the module's pole do the real
work). That is 318 µs total instead of 716 µs, a 400 µs saving for no parts.
Delete the 2 kHz breath reconstruction filter or document why it survives. Then
put the real number in the budget table.

**Confidence: high** on the arithmetic (τ = 1/2πf is exact for a single pole);
**medium** on whether the design really intends two 500 Hz poles — "band-limit at
both ends, around 500 Hz" reads that way but is not a schematic.

**Falsified by:** the ROADMAP's own end-to-end measurement — *"Two scope
channels: one on the sensor output, one on the CV jack."* Subtract the sensor's
own response and read the filter delay directly.

---

## 9. The RJ45 mapping is good, but MOSI and CS share a pair with no ground — contradicting ADR 0004's own stated rule — and the power pair is the one T568B splits

**Severity: MINOR**

**Where.** ADR 0004: *"With real Cat5/6 **each signal sits against a ground in
its own twisted pair.**"* And, four paragraphs later, the final map:
`1,2 BREATH/AGND` · `3,6 +12V/PWR_GND` · `4,5 MOSI/CS` · `7,8 SCLK/DIG_GND`.

**Why.** Three of four pairs have a ground. `MOSI/CS` does not, so the rule the
ADR states for itself is broken for two of the three digital lines. Consequences,
in order:

- **MOSI's and CS's return current has no designated conductor.** At 2 MHz it
  takes the lowest-inductance path available, which is `PWR_GND` (pin 6, adjacent
  to CS) and `DIG_GND` (pin 8). Return current in `PWR_GND` adds to the
  common-mode voltage the breath in-amp must reject — at a frequency (2 MHz)
  where in-amp CMRR has long since collapsed. It is only saved by the 500 Hz
  band-limit downstream, i.e. by accident rather than by the pin map.
- **`AGND` cannot be a return path, which is correct and worth stating.** It is
  grounded only at the instrument end (the module senses against it, it is not
  tied to module ground), so it carries nothing. That is the single most
  important property in the whole umbilical and the map preserves it.
- **The power pair is on (3,6), which T568B splits.** Pins 3 and 6 are separated
  by the (4,5) pair, so inside every plug the two power conductors run apart for
  ~13 mm with the MOSI/CS pair physically inside their loop. That is the highest
  di/dt in the cable enclosing the most timing-sensitive pair. Estimating
  M ≈ 2.6 nH over 13 mm and a buck input edge of 400 mA in 20 ns, V = M·di/dt =
  52 mV — below any threshold, so survivable, but it is the worst available
  placement for the split pair.

**On the part that is right:** the guard claim holds. Physical pin adjacency is
1–2–3–4–5–6–7–8, so `BREATH` at pin 1 touches only `AGND`; `AGND` touches `+12V`;
`MOSI` is two positions away and `SCLK` is six. Putting the analog pair at the
end of the row with the DC pair inboard of it is the right call and I would not
change it.

**Proposal.** Two options, neither free of cost:

- **Cheap:** swap the (4,5) and (7,8) assignments to `SCLK/DIG_GND` on (4,5) and
  `MOSI/CS` on (7,8). This gives the highest-edge-count line its own return in
  its own pair and moves the ungrounded pair to the far end of the connector from
  `BREATH`. Strictly better on both counts; costs nothing.
- **Proper:** regenerate SYNC at the module from SCLK inactivity and free pin 5
  as a second digital ground, so every digital line has a return in its own pair.
  Note that ADR 0004's stated reason for *not* doing this is a non-sequitur:
  *"220 Ω in series on MOSI at the driving end … **also makes SYNC-signal
  regeneration at the module unnecessary**."* Series termination controls
  reflections; it has nothing to do with whether CS needs a wire. Whatever the
  real reason is, it is not recorded.

**Confidence: high** on the self-contradiction and the return-path argument;
**medium** on the 52 mV, which uses a mutual-inductance estimate rather than a
measurement.

**Falsified by:** ROADMAP E11 already calls for *"a logic analyser and a scope on
the real cable at length"*. Add: scope CS with MOSI toggling at full rate and the
instrument driving, and measure the glitch. My estimate for in-pair crosstalk is
4.4 mA of coupled current into a 30–50 Ω driver = **133–222 mV**, against
V<sub>IL</sub> = 0.8 V. Anything under 400 mV and the pairing is fine as drawn.

---

## 10. The umbilical's conductor gauge is unspecified on a part the design calls a consumable — a 28 AWG slim patch lead multiplies every drop and common-mode figure in the project by 2.5×

**Severity: MINOR**

**Where.** `hardware/bom.csv`: *"Cat5e STP patch lead, **STRANDED**, ~2m … It is
a **CONSUMABLE** — keep spares and replace at the first intermittency."*
ADR 0005's drop table and ADR 0003's offset table both assume *"2 m of 24 AWG,
round trip ~0.34 Ω"*. No gauge appears in the specification.

**Why.** 28 AWG "slim" patch leads are the common thing in a drawer, and the BOM
tells the future owner to buy replacements without saying what to buy.

| Gauge | 2 m, one way | Round trip | Drop at 400 mA | Common mode at the in-amp |
|---|---|---|---|---|
| **24 AWG (assumed)** | 0.168 Ω | 0.337 Ω | 135 mV | 67 mV |
| 26 AWG | 0.268 Ω | 0.536 Ω | 214 mV | 107 mV |
| 28 AWG | 0.426 Ω | 0.852 Ω | **341 mV** | **170 mV** |

Nothing breaks: at 170 mV of common mode and 86 dB of CMRR the breath error is
still 8.5 µV, and 11.66 V still feeds a buck that needs 6 V. But ADR 0005's
*"0.7 % error"* becomes 2.8 %, and the instrument's most-replaced part is the one
whose spec is missing. (Resistances from standard wire tables, from memory;
0.0842 Ω/m for 24 AWG I am confident of.)

**Proposal.** Write **"24 AWG stranded, shielded (F/UTP or S/FTP), 2 m"** into the
BOM line, and make "shielded" mandatory rather than *"preferred"* — the shield
costs nothing at this price, the cable is the only part of the system outside a
metal box or a wooden one, and it is the return path for common-mode current
during the USB bring-up case below. Add a sentence to ADR 0004 saying why the
gauge is not free.

**Confidence: high.** Straight table lookup.

**Falsified by:** measure the loop resistance of the actual cable with a 4-wire
meter at E11. If it is under 0.4 Ω round trip, the bought cable is 24 AWG and
this is bookkeeping.

---

## 11. Four smaller items

**Severity: MINOR / NIT**

- **The BOM and ADR 0004 specify different breath receivers, and the CMRR they
  claim differs by 55 dB.** ADR 0004: *"**INA134** for the breath difference amp.
  On-chip matched resistors give ~90 dB CMRR."* ADR 0003 rejects exactly that:
  *"a 10 Ω mismatch degrades the INA134 to ~74 dB, and this design's own
  protection resistor and pulldown would have left roughly **19–34 dB**."* The BOM
  agrees with 0003 (`U-DIFFRX, INA821 or INA828`). ADR 0004's parts paragraph is
  stale and would build the rejected part. **Confidence: very high.** Fix: delete
  the INA134 paragraph from ADR 0004 and point it at ADR 0003.
- **The AMOLED's panel supply is a switching converter nobody has inventoried.**
  AMOLED panels need an elevated ELVDD and a negative ELVSS; ADR 0008 knows this
  (*"AMOLED panels need their own supply rails … dev boards include that
  circuitry"*) but then treats it as solved rather than as a third switcher in
  the instrument. Its frequency, its ripple and its content-dependent load are
  all unknown, it sits at the top of the body, and it is on the same 5 V rail as
  everything else. **Confidence: high** that it exists; **low** on its
  significance — the top of the body is the right place for it and the breath
  path is at the other end. Add one row to E1: *scope the display board's 5 V
  input current while sweeping panel content from black to white, and find the
  panel supply's switching frequency.*
- **USB bring-up gives the instrument a second earth reference.** ADR 0005 ORs
  USB power with umbilical power through a diode. With both connected, the host
  PC's ground and the rack's ground meet through `PWR_GND`, and mains-frequency
  leakage circulates in the conductor the breath in-amp uses as its common-mode
  reference. At a typical 0.5–1 mA of Y-capacitor leakage that is 84–168 µV of
  50/60 Hz common mode — 8 nV at the jack after CMRR, so harmless. But E5 and E11
  may be run simultaneously, and 50/60 Hz is below every filter in the design.
  **Confidence: medium.** Worth one line in the E5 notes, not a design change.
- **ADR 0006 gives breath a 2 kHz reconstruction filter for steps that do not
  exist.** Breath never enters the DAC. 80 µs of group delay for nothing. NIT.

---

# Where the design is correct

These are not courtesies. Each is a result I tried to break and could not.

**The `AGND` sense-return is the right architecture and the arithmetic supports
it at every frequency I tried.** The common mode at the in-amp is the full
`PWR_GND` drop, and at 86 dB of CMRR (INA821 at G ≈ 2, from memory) the error at
the jack is:

| Source | Common mode | At the breath jack |
|---|---|---|
| DC, 400 mA | 67 mV | 7.2 µV |
| LED PWM, 2 kHz, 206 mA | 35 mV | 3.7 µV |
| WiFi burst, 176 mA @ 12 V | 30 mV | 3.2 µV |

On a 10 V output that is −120 dB. ADR 0003's argument that this reproduces the
Eurorack patch-cable condition inside the umbilical is correct, and the decision
to put the pulldown differentially rather than on one leg is correct for the
reason stated (my finding 1 is that it is *insufficient*, not that it is wrong).

**The REF5050 ratiometric-supply decision is correct and it is the largest
remaining contributor to breath-jack noise — at about 60 µV.** Working the LED
PWM path all the way through:

```
40 % duty, 0.34 A peak  →  2 kHz fundamental 206 mA peak
2 × 470 µF at the feed points: |Zc| = 85 mΩ, ESR/2 ≈ 75 mΩ  →  ~160 mΩ
ripple on the instrument's +12 V = 206 mA × 0.16 Ω = 33 mV
REF5050 at ~55 dB PSRR @ 2 kHz   →  58 µV on the 5.000 V sensor supply
ratiometric at 2.5 V output       →  29 µV
through the in-amp × 2.13         →  62 µV at the jack  (−104 dB on 10 V)
```

That is inaudible as amplitude modulation on a VCA by a wide margin. ADR 0003's
claim that the ratiometric path was *"roughly 30 dB worse than the one that was
analysed"* was right, and fixing it with a reference rather than with filtering
was the right call.

**Nothing the instrument does reaches the pitch CV.** The module's shared
impedance upstream of the branching (1N5817 dynamic resistance ~0.15–0.3 Ω at
300 mA, from memory, plus ribbon and bus trace, call it 0.3 Ω) is the path
ADR 0004 correctly identifies as unfixable by branching. At OPA2197 PSRR of
~74 dB at 2 kHz (extrapolated from 114 dB DC with a ~20 Hz pole; from memory):

| Aggressor | On the module's +12 V | At the pitch jack | In cents |
|---|---|---|---|
| LED PWM, 2 kHz | 62 mV | 22 µV | **0.027** |
| WiFi burst | 53 mV | 19 µV | **0.023** |

Against 833 µV/cent and a VCO that drifts ~3.5 cents over 10 K on its own, these
are three orders of magnitude below anything audible. ADR 0004's judgement that
the ferrite-and-bulk arrangement is *"survivable by accident, not by design"* is
honest and also, as it happens, comfortably true. The genuinely load-bearing
parts of the module's noise design — LT5400 ratio tracking over discrete
resistors, BAV99 over BAT54S (2 µA × 1 kΩ = 2 mV = 2.4 cents), the LM317LZ
instead of the rack's ±5 % +5 V rail — are all correctly identified and correctly
prioritised. The resistor-tracking-dominates-reference-drift argument in ADR 0006
is the best piece of analysis in the repository.

**The 500 Hz band-limit is the single most valuable noise decision in the
project.** It converts every coupling above 5 kHz into a rounding error. Cable
crosstalk that arrives as 943 µV at 500 kHz leaves as 0.94 µV. My finding 7 is
only about *where* the pole sits, not whether it should exist.

**Moving the sensor to the bottom was right for the reason given**, and the
`AGND`-carries-no-current property genuinely survives because `AGND` is grounded
at one end only. **The 1 kΩ output resistors, the L-BUCK-IN as a real inductor
rather than a bead, bulk at the load rather than at the entry, the ≥1 A ferrite
rating, the `R-SPI-PULL` idle-state pulls and the OE gating from +12 V presence**
are all correct and correctly reasoned. The key-chain marker pattern is the right
mitigation for finding 3 and it already exists.

---

# Figures used, and their provenance

**Derived in this review from the project's own stated values (verified by
arithmetic):** the 6 kΩ Thévenin impedance and 120.6 Hz corner; the 1206 Ω
back-solve; 564 Hz and 58.9 dB for 47 nF; group delay τ = 1/2πf<sub>c</sub>; the
160-bit frame and 267 µs at 0.6 MHz; 96 µs for six channels at 2 MHz; 206 mA of
2 kHz fundamental from a 0.34 A 40 %-duty square; 806 µV/LSB; 1.75 Pa/LSB;
833 µV/cent; all CMRR and PSRR division; the 20.8 dB single-leg-pulldown CMRR and
the 94 dB balanced-network CMRR.

**From memory, not verified against a datasheet in this session — flag these
before acting on them:** 24/26/28 AWG resistances (0.0842 / 0.1339 /
0.2129 Ω/m); Cat5e mutual capacitance ≤5.6 nF/100 m and capacitance unbalance
≤330 pF/100 m; MCP3202 sample capacitance ~20 pF; INA821 input bias ~0.5 nA and
CMRR ~86 dB min at low gain; OPA2197 PSRR 114 dB DC and 5.5 nV/√Hz; 74AHCT125
transition time ~3 ns; 74LVC165A V<sub>IL</sub> = 0.8 V at 3.3 V; ESP32-S3 WiFi
TX peak ~350 mA; 1N5817 dynamic resistance at 300 mA; WS281x PWM oscillator
tolerance ±10 %; REF5050 AC PSRR ~55 dB at 2 kHz (the ±0.05 %, 3 ppm/°C and
5 ppm/V line-regulation figures are the project's own).

**Taken from the project and not independently checked:** WS2815 PWM ≈ 2 kHz;
R-78E5.0 switching ≈ 500 kHz; the 0.34 A / 0.13 A strip current table; the
960 mA full-field matrix figure; the 330–400 mA dev-board draw; the ~2.13× breath
gain; 766 mV/kPa and 0.2–4.7 V for the MPXV4006DP.

---

# The six measurements that would settle this fastest

1. **Step the breath buffer output and scope the MCP3202 pin.** Rise time 2.9 ms
   → finding 2 stands; 620 µs → it does not. *Five minutes at E2, and it is the
   highest-value measurement on this list.*
2. **Power the module with the umbilical unplugged and watch the BREATH jack for
   a minute.** Settles finding 1 outright.
3. **Sweep a signal generator 1 Hz–600 kHz into the ADC front end and plot the
   4 kHz sampler's output.** Every alias in finding 6 appears as a spur or none
   do. The ROADMAP already calls for this; it just is not attached to a milestone.
4. **Run the key-chain error counter for an hour with the strips animating at
   full rate, on the final loom, and scope `SH/LD` at the far register.** Settles
   finding 3. Time-critical — it must happen before M6 bonds the body.
5. **Step the matrix dark→full-field with a static pressure on the sensor and
   watch the ADC in LSBs, with a differential probe between the dev board's GND
   pin and the analog star.** Settles finding 4, and it must happen before the
   carrier is fabbed at E13.
6. **Count SCLK cycles per loop frame on a logic analyser at E7, and measure
   SCLK's transition time at the module end at E11.** Settles finding 5 and gives
   the edge rate that every crosstalk estimate here actually depends on.
