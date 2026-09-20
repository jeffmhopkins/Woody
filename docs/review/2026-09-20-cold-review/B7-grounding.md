# B7 — Grounding and return-current topology, end to end

Independent analog design review of **Woody**. Scope: where every return current
actually goes, across two enclosures, 2 m of Cat5, a metal plate under the
player's hands, and an LED system whose current is modulated by the primary
expressive control.

**Read:** `README.md`, `ROADMAP.md`, all of `docs/decisions/`,
`docs/reference/`, `hardware/bom.csv`, `config/key-layout.yaml`,
`firmware/README.md`. **Not read, by instruction:** `docs/review/`,
`docs/log/`. No repository file was modified.

---

## 0. Provenance of the numbers I use

Every finding below shows its arithmetic. The inputs come from three places and
I mark which:

**From the repository (quoted, verified by reading):**

| Figure | Source |
|---|---|
| ~0.34 Ω round trip, 2 m, 24 AWG | ADR 0005, power-drop table |
| Instrument draw ~275 mA; total +12 V ~320 mA; review estimate 410–430 mA | ADR 0004 |
| Lighting clamp ~3 W total (strips + matrix) | ADR 0014 |
| Strips: 0.34 A single hue full, 0.13 A at 40 %, 60/m, 0.84 m | ADR 0014 |
| Matrix: +78 mA at 12 V for a full-field breath bar at 50 % | ADR 0014 |
| WS2815 PWM ~2 kHz; modulation "200–400 mA square wave" | ADR 0004, ADR 0014 |
| Sensor 0.2–4.7 V, gain to 0–10 V ≈ 2.13× | ADR 0003 |
| 16-bit LSB on 10 V = 153 µV | ADR 0006 (10/65536 = 152.6 µV — checked) |
| Pitch 1 V/oct; matched network 0.11 cents; trimmer 2.4 cents/10 °C; VCO ~3.5 cents/10 °C | ADR 0006 |
| Pin map: 1,2 BREATH/AGND · 3,6 +12V/PWR_GND · 4,5 MOSI/CS · 7,8 SCLK/DIG_GND | ADR 0004 |

**Computed here (arithmetic shown inline, verified):** conductor drops, current
splits, pour drops, cents conversions (1 V/oct → 83.33 mV/semitone →
0.8333 mV/cent), FM sideband levels, CMRR residuals.

**From memory, flagged as such at each use, and each falsifiable on the bench:**

- 24 AWG copper 0.0842 Ω/m; 26 AWG 0.1339 Ω/m; 28 AWG 0.2127 Ω/m (solid, 20 °C).
  *Corroborated:* ADR 0005's own 0.34 Ω for 2 m × 2 conductors implies
  0.0842 Ω/m exactly, so at least the 24 AWG figure is consistent with the
  project's own arithmetic. Stranded patch conductors run ~10–15 % higher.
- 1 oz copper ≈ 0.5 mΩ/square; 2 oz ≈ 0.25 mΩ/square.
- RJ45 contact resistance ≈ 20 mΩ new, ≈ 40 mΩ end-of-life, per contact.
- Eurorack 16-pin bus: 4–6 of 16 conductors are ground; flying-bus ribbon is
  typically 28 AWG. **I am least sure of the ground-pin count** and compute both.
- 74LVC at 3.3 V: V_IL 0.8 V, V_IH 2.0 V. 74HC at 3.3 V: 0.99 V / 2.31 V.
  74AHCT: TTL thresholds 0.8 V / 2.0 V, input leakage ±1 µA max.
- INA821/INA828 CMRR ≈ 90–100 dB minimum at low gain; input bias ≈ 1 nA.
  OPA2197 quiescent ≈ 1 mA per amplifier.
- Human-body ESD model: 100 pF / 1.5 kΩ; 8 kV → 5.3 A peak, ~1–10 ns rise.
- Body-to-mains capacitive coupling ~3–10 pF; perception threshold for 50 Hz
  contact current ~0.5 mA.

Where a finding's severity would change if a memory figure were wrong, I say so.

---

## 1. The topology as it must actually be — and it is written down nowhere

Before the findings, the reconstruction they rest on. **No document in this
repository states where the three grounds join.** ADR 0004 names them
(`PWR_GND`, `DIG_GND`, `AGND`), ADR 0003 defines an analog star point *inside
the instrument*, ADR 0009 says the plate bonds to `PWR_GND`, ADR 0014 says LED
return flows in `PWR_GND`. Nothing says what connects to what, at either end.

There is exactly one topology consistent with all the accepted rules:

```
                    2 m Cat5e, 8 conductors
 INSTRUMENT                                              MODULE
 ──────────                                              ──────

 one physical ground node                    ┌── module 0 V ──┬── bus header GND
 (the carrier's copper)                      │                │   (2–6 pins)
   │                                         │                │
   ├─ analog sub-pour ── AGND (pin 2) ═══════╪═► in-amp − input + 100k diff
   │    (sensor, REF5050, OPA2197,           │   ↑ NOT tied to module 0 V
   │     ADC divider)                        │     (ADR 0003 forbids it)
   │                                         │
   ├──────────────────── PWR_GND (pin 6) ════┤  ← ~half the instrument's return
   │                                         │
   ├──────────────────── DIG_GND (pin 8) ════┘  ← the other half
   │
   ├─ LED strip returns (pulsed, up to 250 mA)
   ├─ buck return (~400 mA at 5 V)
   ├─ key-chain loom returns × 4 clusters
   ├─ aluminium key plate, one bond (MECH-GNDBOND)
   └─ etherCON shell → backing plate → key plate (unstated, see F8)
```

**The consequence the documents miss: `DIG_GND` is not a digital return. It is a
second power-return conductor in parallel with `PWR_GND`.** The instrument has
one ground node; the module ties both conductors to its 0 V; two conductors
between the same two nodes carry current in inverse proportion to their
resistance. Only `AGND` is genuinely separate, and only because ADR 0003
forbids tying it at the far end.

So the design has **two** grounds, not three: a combined power/digital return
(two conductors) and an analog sense return (one). Every statement in the
repository that treats `PWR_GND` and `DIG_GND` as serving different jobs is
describing an intent the wiring does not implement.

---

## 2. Findings

### F1 — The module pushes 300–430 mA of breath-correlated current through the rack's shared ground, and pitch CV is single-ended against it: 2–5 cents of pitch error that tracks how hard you blow

**Severity: MAJOR.** *This is the most important item in this review. It becomes
a SHOWSTOPPER if the mitigations below are all declined, because it is designed
into the module's topology and the module exists to make pitch accurate.*

**Where.** ADR 0004, "It passes the instrument's current":

> "A typical module draws 20–100 mA. This one draws its own analog current
> *plus* everything the instrument consumes: **+12 V ~320 mA** … a review put it
> nearer 410–430 mA."

and ADR 0003, justifying the whole umbilical scheme:

> "**A module's power returns through the bus board's ground rail, not through
> the patch cable.** The patch cable's ground carries only the signal current
> flowing into a high-impedance input — microamps … The patch cable works
> because **its ground does exactly one job.**"

ADR 0004 works the supply side hard — diodes, branched ferrites, bulk at the
load, an LC into the buck. **The return side is never mentioned once.** The
power-tree diagram in ADR 0004 shows two `+12 V` branches and a single, unnamed
ground.

**Why.** The pitch output is a single-ended voltage referenced to *module*
ground. The receiving VCO reads it against *its own* ground. The error is the
potential difference between the two modules' ground taps, and this module is
injecting 5–20× a normal module's current into the copper that sets it.

Instrument current at the +12 V bus pin: 320 mA nominal, 430 mA on the
review's estimate. The **modulated** part is what matters, and it is not random
noise — the LEDs track breath (ADR 0014: default source breath, strips driven
by the post-gate breath value). The 3 W lighting clamp at 12 V is 250 mA, so
breath from zero to full swings the module's bus current by up to **250 mA**.

Shared bus-ground resistance from this module's tap to the PSU (28 AWG ribbon,
300 mm, memory figures):

| Ground conductors in the ribbon | R | Plus 2× IDC contacts |
|---|---|---|
| 2 | 31.9 mΩ | ~41 mΩ |
| 4 | 16.0 mΩ | ~21 mΩ |
| 6 | 10.6 mΩ | ~14 mΩ |

Take the middle case, 16 mΩ, and ignore the contacts:

```
ΔV = 250 mA × 16 mΩ = 4.0 mV
1 V/oct → 1 cent = 0.8333 mV
4.0 mV / 0.8333 = 4.8 cents
```

At 150 mA of realistic modulation it is 2.4 mV = **2.9 cents**. At 6 ground
conductors and 150 mA it is 1.5 mV = **1.8 cents**.

Set against the project's own precision budget (ADR 0006): matched network
0.11 cents, trimmer tempco 2.4 cents per 10 °C, the VCO itself 3.5 cents per
10 °C. **This term is the largest in the system and it is the only dynamic
one.** The others are slow drift you tune out; this one moves with the
performance.

Audibility, as FM sidebands on a 440 Hz tone (computed):

| Error | Modulation rate | β | Sideband |
|---|---|---|---|
| 2.9 cents | 40 Hz (frame rate) | 0.018 | **−41 dBc** |
| 4.8 cents | 40 Hz | 0.031 | **−36 dBc** |
| 4.8 cents | 10 Hz (breath envelope) | 0.122 | **−24 dBc** |

The breath-envelope case is the one that matters: a note that goes sharp by up
to 5 cents as you push into it, on every note. On a wind controller that will be
diagnosed as the breath sensor, the fingering table, or the player, forever.

Three aggravating details:

- **The patch cable is dragged into it.** The pitch patch cable's sleeve ties
  module ground to VCO ground in parallel with the bus. Bus ~20 mΩ, patch cable
  ~150 mΩ; the patch branch takes 150/(150+20) → about **10 % of the
  instrument's return current flows down the pitch patch cable's sleeve**
  (≈ 40 mA nominal, 25 mA modulated). This is exactly the property ADR 0003
  identifies as why patch cables work, and this module breaks it for every cable
  plugged into it.
- **The magnitude depends on rack layout.** If the VCO sits between this module
  and the PSU, the instrument's current flows through the segment between them
  and the error is full. If the VCO sits beyond this module, the error is near
  zero. **So E9's calibration is implicitly a calibration of the rack's physical
  arrangement**, and moving a module invalidates it. Nothing in ADR 0006 or the
  roadmap says this.
- **The test plan watches the wrong channel.** `docs/reference/latency-budget.md`
  has exactly one test for this class of problem, and it is on breath:
  > "**Breath channel noise** | Scope the breath jack while sweeping display
  > brightness, LED animation and a WiFi burst"

  Breath is the channel that is *immune* (it is differentially received against
  `AGND`); 4 mV on a 10 V breath CV is 0.04 %, −68 dB, inaudible in a VCA.
  Pitch is the channel that is exposed, and nobody ever scopes it while sweeping
  the LEDs.

**Proposal.**

1. **Take the instrument's +12 V and its return to the PSU separately from the
   module's signal ground.** A one-off rack usually has spare PSU screw
   terminals or a second header. Feeding the umbilical branch from its own pair
   removes the instrument's current from the segment shared with every other
   module. This is the fix; the rest are palliatives.
2. Failing that: **join the umbilical return to module 0 V only at the 16-pin
   header's ground pins** (see F4), use every ground pin the header offers,
   keep the ribbon short, and place this module as close to the PSU tap as the
   case allows.
3. **Make the lighting draw constant.** The firmware already computes a total
   budget and scales proportionally (ADR 0014). Change the animation contract so
   breath moves a *bar or dot position* on a fixed-total-current field rather
   than a brightness. Same expressiveness, and it removes the correlation
   between the primary control and the rail current. This costs one line of
   firmware and is the single cheapest mitigation available.
4. **Add the missing measurement to E9**, below.

**Confidence: high** on the mechanism and on the cents conversion; **medium** on
the magnitude, because the bus ribbon resistance and the ground-pin count are
memory figures and the PSU-to-module path is rack-specific. The mechanism does
not depend on those; only the multiplier does.

**Falsified by:** scope the pitch jack, DC-coupled, 1 mV/div, into the actual
VCO, while firmware sweeps the LED animation from blank to the full 3 W clamp
with pitch held at a fixed code. Simultaneously measure module-0 V to VCO-0 V
with a second channel. If the pitch jack moves by less than 0.5 mV (0.6 cents)
and the ground delta is under 0.5 mV, the finding is wrong for this rack. Do it
at E6 (module alone, dummy load on the umbilical) and repeat at E9.

---

### F2 — The grounds' joining points are never stated, and the only consistent topology makes `DIG_GND` a second power return carrying ~half the instrument's current

**Severity: MAJOR** (documentation and build-rule gap with electrical consequences)

**Where.** ADR 0004's conductor budget:

> ```
> +12V      / PWR_GND     power, and the presence signal
> SCLK      / DIG_GND     SPI to the DAC, ~1 MHz
> MOSI      / CS
> BREATH    / AGND        analog, band-limited ~500 Hz, sense return
> ```
> "**`AGND` carries no power current** — it is a sense reference only"

ADR 0003 defines the instrument-side analog star point, and stops there:

> "The star point is the analog ground pour on the bottom cluster board … `AGND`
> leaves the board straight into the umbilical."

**Why.** Three named grounds, zero stated joins. Work it out and the topology is
forced (section 1 above): the instrument has one ground node, so all three tie
there; the module must tie `PWR_GND` (the umbilical feed's return) and
`DIG_GND` (the level shifter's reference) to its 0 V; `AGND` must *not* be tied
there. Therefore `PWR_GND` and `DIG_GND` are two conductors between the same
two nodes.

Current split, 2 m of 24 AWG stranded (0.0842 × 1.12 = 0.0943 Ω/m from memory,
0.189 Ω per conductor):

| | Return R | Drop at 320 mA | at 430 mA |
|---|---|---|---|
| `PWR_GND` alone (as documented) | 0.189 Ω | 60 mV | 81 mV |
| `PWR_GND` ∥ `DIG_GND` (as built) | 0.094 Ω | 30 mV | 41 mV |

So `DIG_GND` carries **160–215 mA continuously**, and the ground offset is half
what ADR 0003's shared-ground table implies. Consequences, in order:

- **A board designer reading `DIG_GND` will size it as a logic return.**
  A 0.25 mm 1 oz trace at 200 mA is thermally fine but it is not what the label
  invites, and on the module side that trace runs to the level shifter, not to
  the power entry.
- **The split is set by contact resistance as much as by copper.** Two RJ45
  contacts at 20–40 mΩ each (memory) against 189 mΩ of conductor is a 10–20 %
  term, and the design says the cable flexes constantly and is a consumable.
  The split therefore wanders. It is all common-mode, so it is rejected — but it
  means the "which conductor carries what" question has no stable answer.
- **The power pair is no longer balanced.** +12 V at pin 3 carries 320 mA out;
  pin 6 returns 160 mA. The residual 160 mA is common-mode current on the cable
  at the buck's switching frequency and the LED PWM rate. The guard argument in
  ADR 0004 (pins 3 and 6 straddling pins 4 and 5 — geometrically correct on
  T568B, I checked the pin ordering) still holds for *crosstalk*, but the power
  pair is not a tight loop and should not be credited as one.
- **Noise margin on SPI is fine and worth recording as such.** 30–41 mV DC of
  reference offset plus, say, 20 mV of LED-frame step, against a 74AHCT125's
  0.8 V V_IL / 2.0 V V_IH with a 3.3 V drive: margins of 800 mV and 1.3 V. The
  offset consumes 3–5 % of it. No action needed.

**Proposal.** Add a grounding section to ADR 0004 stating, explicitly:

- `PWR_GND` and `DIG_GND` are **parallel conductors of one return**, sized and
  routed as such at both ends. Rename them or annotate them; `DIG_GND` is a
  misleading label for a 200 mA conductor.
- `AGND` is tied to instrument ground at **one** point and to nothing at the
  module (F3 amends this).
- State which leg the polyfuse is in. `F-POLY` is specified only as "at
  umbilical entry" (BOM, ADR 0005). It must be in +12 V. A PPTC in a return is
  a 0.1–0.3 Ω thermally-modulated resistor in series with the reference for
  every signal on the cable, and ADR 0014 documents at length that this part's
  resistance rises with current.

**Confidence: high.** The topology is forced; it is not a judgement call.

**Falsified by:** at E11, with the instrument running at full lighting, put a
current probe on the individual `PWR_GND` and `DIG_GND` conductors of an opened
patch lead. If `DIG_GND` reads under 20 mA, something is isolating the grounds
that I have not found in the documents.

---

### F3 — The breath receiver has no common-mode bias return: an unplugged or intermittent `AGND` slams the breath CV to full scale, and ADR 0005 claims the opposite

**Severity: MAJOR**

**Where.** Two accepted ADRs in direct contradiction.

ADR 0005:

> "**Pull down the module's breath receive input**, so that an instrument which
> is switched off — **or unplugged** — presents 0 V rather than a floating
> buffer output. One resistor, and it means powering down the instrument
> silences the patch instead of leaving a stuck level."

ADR 0003, which overrides it on the part that matters:

> "Put the pulldown **differentially across BREATH–AGND**, not on one leg. A
> shunt on a single leg does not symmetrise the way a series element does —
> 100 kΩ on the + input alone would cap CMRR near 19 dB."

The BOM implements ADR 0003: `R-PD-BREATH … DIFFERENTIAL across BREATH-AGND not
one leg`.

**Why.** A differential shunt defines the *difference* between the two inputs
and nothing about their common-mode potential. Two cases:

- **Instrument off, cable connected** — works as ADR 0005 claims. The load
  switch cuts +12 V only; `PWR_GND`/`DIG_GND` stay connected, so the in-amp's
  inputs are still referenced to module 0 V through the cable, and the 100 kΩ
  holds them together. Output 0 V. Correct.
- **Cable unplugged, or `AGND` intermittent** — the two inputs float as a pair.
  The in-amp's input bias current (≈1 nA, memory) into the node's stray
  capacitance (a few pF) charges it at roughly
  `1 nA / 5 pF = 200 V/ms`. The inputs leave the common-mode range within
  microseconds and hit the internal clamps. The output is indeterminate and in
  practice sits at a rail: ~11.9 V from the OPA2197 scaling stage, clipped by
  the 0–10 V design span. **The breath jack goes to full scale and stays
  there.**

This is precisely the failure ADR 0004 builds a hardware watchdog to prevent:

> "**A stuck CV is worse than a dead one** … the rack drones forever. Nothing in
> the design notices."

and the watchdog does **not** cover it, because it asserts the DAC's `CLR` pin
and breath never touches the DAC (ADR 0006: "Breath never enters the digital
path on its way out"). So the one channel with no watchdog coverage is the one
channel that fails loud, in the routine case — the design's own cable spec says
"treat cable failure as routine … replace the lead at the first sign of
intermittency."

Failure matrix for a single open conductor, which I worked through and which the
documents do not contain:

| Conductor opens | Result |
|---|---|
| +12 V | instrument dies → watchdog → `CLR` → pitch subsonic, mods 0 V. Safe |
| `PWR_GND` | return moves entirely to `DIG_GND`; offset doubles to 60–80 mV. Common-mode. Benign |
| `DIG_GND` | mirror of the above. Benign |
| `BREATH` | 100 kΩ holds it at `AGND`; output 0 V. Safe |
| SCLK/MOSI/CS | watchdog → `CLR`. Safe |
| **`AGND`** | **breath CV slams to full scale, indefinitely** |

**Proposal.** Split the pulldown and ground its centre — one extra resistor,
zero cost to CMRR:

```
BREATH ──10k──┬──────────► in-amp +
              │
            49.9k (0.1%)
              │
              ├────────────── module 0 V
              │
            49.9k (0.1%)
              │
AGND  ──10k──┴──────────► in-amp −
```

Checked against every requirement it has to satisfy:

- Differential impedance unchanged at 100 kΩ, so the instrument-off case is
  exactly as before.
- Unplugged: both inputs are pulled to module 0 V, differential 0, **output
  0 V**. ADR 0005's stated behaviour is now actually obtained.
- Current in `AGND`: common-mode 40 mV across ~55 kΩ = **0.7 µA**, developing
  `0.7 µA × 0.189 Ω = 0.14 nV` in the cable. The "carries no power current"
  property survives with nine orders of margin.
- Balance: at 0.1 % matching, the CM-to-DM conversion is
  `40 mV × (50.05/60.05 − 50/60) = 5.6 µV`, or **11.8 µV at the jack
  (−118 dBc of 10 V)**. At 1 % parts it is 117 µV (−99 dBc), still acceptable.
- **Do not use the naive single 1 MΩ from `AGND` to module 0 V.** That
  unbalances the legs by `10k/1.01M = 0.99 %` and converts 40 mV of common mode
  into **844 µV at the jack** — twenty times worse than the split-shunt version
  and animation-modulated.

**Confidence: high** on the mechanism, **medium-high** on "it rails rather than
sitting somewhere harmless" — that depends on the in-amp's internal clamp
behaviour with both inputs above the positive rail, which varies by part.

**Falsified by:** at E10/E11, with the module powered and the instrument
running, pull the umbilical mid-note and scope the breath jack. If it goes to
0 V and stays there, the existing differential pulldown is sufficient. Repeat
with only pin 2 lifted (a doctored patch lead), which is the intermittency case
the cable spec anticipates.

---

### F4 — The module's internal return topology is undefined, and the instrument's 300–430 mA is the largest current on a board whose job is 153 µV resolution

**Severity: MAJOR**

**Where.** ADR 0004's power-entry diagram, which is the only module topology in
the repository:

> ```
> bus +12V ──[1N5817]──┬──[ferrite]──[bulk]──┬── module analog (op-amps)
>                      │                      │
>                      │                      └──[LM317LZ 5.25V]── DAC AVDD
>                      │
>                      └──[ferrite]──[bulk]──[TPS2553]── umbilical +12V
> ```

Three supply branches are drawn with care. **There is no ground in the diagram
at all**, and no ADR says how the module's 0 V is arranged between the level
shifter, the DAC, the precision analog, the watchdog, the jack sleeves and the
umbilical's return.

**Why.** Everything the +12 V branching buys is given back if the return is a
single undifferentiated pour, because the instrument's return current then flows
*across* the board between the etherCON and the power header, and every
reference tapped along that path rides on it.

Pour drop, 1 oz copper at 0.5 mΩ/square (memory):

| Path | Squares | R | Drop at 250 mA modulation |
|---|---|---|---|
| 25 mm-wide pour, 100 mm | 4 | 2.0 mΩ | 0.50 mV |
| 3 mm trace, 20 mm | 6.7 | 3.3 mΩ | 0.83 mV |
| 0.5 mm trace, 25 mm | 50 | 25 mΩ | 6.3 mV |

Where that lands:

- **Pitch.** If the pitch scaling network's ground leg and the pitch jack's
  sleeve are separated by 2–3 mΩ of that path, the error is 0.5–0.8 mV =
  **0.6–1.0 cents, animation-modulated**, on top of F1 and independent of it.
  The design spent an LT5400 to buy 0.11 cents.
- **The DAC's full scale.** The LM317LZ sets 5.25 V relative to its ADJ
  divider's ground. Displace that ground from the DAC's ground by 0.3 mV and
  the DAC's reference moves 57 ppm; on a 9 V pitch span that is 0.5 mV =
  **0.6 cents**. ADR 0004 bought the LM317 specifically so that "a rail the rack
  is allowed to move ±5 %" would not sit under the pitch calibration — and then
  left the regulator's own reference node unlocated.
- **Every jack sleeve.** Six sleeves tied at six different points along a pour
  carrying 300–430 mA give six different output references.

**Proposal.** Write a module ground plan into ADR 0004:

1. **The umbilical's `PWR_GND` + `DIG_GND` join module 0 V at the 16-pin
   header's ground pins and nowhere else.** Route them as a dedicated pour or a
   wide trace from the etherCON directly to the header. The instrument's current
   then never enters analog copper. This is a routing constraint, free on a
   board being laid out, impossible after fab.
2. **The jack field gets a local ground node**, tied to the analog 0 V at one
   point, with the pitch stage's reference taken at the pitch jack's sleeve.
3. **The DAC's regulator reference, the DAC's GND and the pitch network's
   ground leg share one node**, adjacent, before anything else.
4. The 74AHCT125 and the watchdog monostable are the only fast digital on the
   board; keep their return out of the analog node.

**Confidence: high** that the rule is needed, **medium** on the 0.6–1.0 cent
magnitude, because it is entirely a function of a layout that does not exist
yet. That is the point: it is cheap now and unfixable later, which is this
project's own stated criterion (ADR 0009, "Things that are free now and
impossible later").

**Falsified by:** once the module PCB exists, inject 400 mA DC between the
etherCON return and the header ground pins with the module otherwise
unpowered, and measure micro-volts between the pitch jack sleeve, the DAC GND
pin and the LM317 ADJ divider's ground. Under 100 µV across all pairs and the
layout is fine.

---

### F5 — The instrument's "analog star point" is defined as a region, not a point; the one geometric fact that decides whether it works is unwritten

**Severity: MAJOR**

**Where.** ADR 0003 explicitly claims to have closed this:

> "Several rules in this ADR refer to bonding `AGND` to 'the instrument's analog
> ground star point'. A review pointed out that **no such point was defined
> anywhere**, so the rules referenced an object that did not exist.
> It exists now … **The star point is the analog ground pour on the bottom
> cluster board, at the sensor and reference, immediately adjacent to the
> umbilical connector.**"

**Why.** A pour is a region. A star point is a node. The fix names the former and
calls it the latter, and the question it was supposed to answer is still open:
**where does the analog pour tie to the rest of the instrument's ground,
relative to where the noisy currents enter and leave?**

That board is not an analog board. Per ADR 0013 the carrier holds the shift
registers, the ADC, the REF5050, the OPA2197, the 74AHCT125, the R-78E5.0, the
polyfuse and the umbilical connector — and per ADR 0014 the LED strips' power
feeds leave from the same place. Currents converging on this one board:

| Source | Current | Character |
|---|---|---|
| WS2815 strips | up to 250 mA at 12 V | pulsed at ~2 kHz, enveloped at the frame rate, **correlated with breath** |
| R-78E5.0 output return | 330–400 mA at 5 V | switching, plus WiFi bursts |
| Buck input | ~170 mA at 12 V | pulsed; `L-BUCK-IN` handles the cable side, not the local side |
| Key chain × 4 clusters | mA, with fast edges | |
| Sensor + REF5050 + OPA2197 | ~13 mA (10 mA sensor, memory) | quiet, constant |

The breath error is whatever LED return current flows through copper shared
between the analog pour's tie and the connector's `PWR_GND` pin:

```
good layout:  250 mA × 2 mΩ  = 0.50 mV × 2.13 = 1.07 mV at the jack  (−79 dBc)
bad layout:   250 mA × 25 mΩ = 6.25 mV × 2.13 = 13.3 mV at the jack  (−58 dBc)
```

The good case is inaudible. The bad case is 0.13 % amplitude modulation of the
breath CV at the animation rate, into a VCA — audible on a quiet sustained note,
and exactly the artefact the entire `AGND` scheme was built to prevent. **The
difference between them is one unstated routing choice.** Note also that the ADC
divider hangs off the same pour, so the same drop feeds the note-gate threshold
(see F6).

**Proposal.** Replace the paragraph with a geometric rule:

> The analog pour connects to the instrument's power ground at exactly one
> point: **the umbilical connector's `PWR_GND` pin pad.** `AGND` leaves from the
> same pad by its own trace. Every other return — LED feeds, buck, dev-board
> headers, shift registers, plate bond — lands on the power pour on the far side
> of that pad. No power-return current crosses between the analog pour's tie
> point and the `AGND` takeoff.

That is a Kelvin connection at the connector, it is one sentence, and it is the
thing the E13 layout needs.

**Confidence: high** on the mechanism and the arithmetic; **medium** on which
case the built board lands in, since no layout exists. The severity is driven by
the asymmetry: the rule costs nothing to write, and the board is inside a bonded
body.

**Falsified by:** at E14, on the real carrier, scope the breath jack while
stepping the LED animation between blank and the 3 W clamp with the mouthpiece
sealed at a constant pressure. Under 1 mV of correlated movement at the jack and
the layout is in the good case. This is close to the test the latency budget
already specifies — it just needs to be done *on the carrier*, not on dev boards
(ROADMAP E14 makes exactly this point about everything else).

---

### F6 — ADR 0014's LED-to-breath coupling number describes a topology ADR 0003 deleted, and is about four decades too large — while the mechanism it treats as symmetric is not

**Severity: MINOR** (analysis error) **with one MAJOR consequence attached**

**Where.** ADR 0014:

> "**Through the CV path it is negative feedback.** More breath → brighter LEDs
> → `AGND` rises → the CV reads lower. Loop gain is around 0.004, so the effect
> is **0.4 % of gain compression**."

and, in the same ADR's Grounding section:

> "Without `AGND`, the light show would appear on the breath CV — a 34 mV ground
> offset that moves with the animation."

**Why.** Both sentences cannot be true. If `AGND` carries no current it cannot
"rise" relative to the instrument's analog reference — they are the same node.
What rises is the instrument's ground relative to the module's, which is
**common mode** at the in-amp and is rejected:

```
common mode from LED current:  250 mA × 0.094 Ω (two returns) = 23.5 mV
                               (or 42 mV on the ADR's single-return assumption)
at 90 dB CMRR:   42 mV × 10^-4.5  = 1.33 µV → ×2.13 = 2.8 µV at the jack
at 100 dB CMRR:  42 mV × 10^-5    = 0.42 µV → ×2.13 = 0.9 µV at the jack
```

ADR 0014's 0.4 % gain compression on a 10 V output is **40 mV**. The ratio to
the correct figure is about **10⁴**. The ADR's number is what you get if you
sense against local module ground — i.e. it silently analyses the topology
ADR 0003 spends five pages deleting. Neither ADR cites the other's number, and
the 0.4 % figure appears nowhere else.

**The consequence that is not cosmetic.** The same section then treats the ADC
side as the mirror image:

> "**Through the ADC it is positive feedback**, via reference depression from
> shared-ground LED current … the symptom is not gain error, it is note-gate
> chatter."

**That one is real, and it is not the mirror image.** The ADC lives in the
instrument, on the shared pour of F5, referenced to the instrument's local
ground. There is no differential receiver in front of it and no common-mode
rejection anywhere in that path. Its error is the full F5 drop — 0.5 mV in a
good layout, 6.3 mV in a bad one — referred to the divider input. Against a
12-bit MCP3202 on 3.3 V, one LSB is 805 µV, so the bad-layout case is **8 LSB of
breath-correlated step at the note-gate threshold**, which is exactly the
chatter mechanism described.

So the two halves of the loop differ by four orders of magnitude, and the ADR
presents them as comparable. The instruction that hangs off this — "Size the
note-on/note-off hysteresis from the measured LED-induced step" (ADR 0014) — is
correct and should be kept; it is the only thing in the ADR that survives.

**Proposal.** Correct the CV-path number to the CMRR-limited value (≈3 µV at the
jack) and state plainly that the CV path is protected by the receiver and the
ADC path is protected by nothing but layout. Then point the ADC-side mitigation
at F5's routing rule, which is the actual fix; hysteresis sizing is the backstop.

**Confidence: high** on the four-decade discrepancy, **medium** on the exact
residual, since it turns on the in-amp's CMRR at the animation rate (a memory
figure, and real CMRR degrades with frequency).

**Falsified by:** measure the in-amp's CMRR in circuit — inject 100 mV at 40 Hz
between instrument ground and module ground with the breath input shorted, and
read the jack. Above 500 µV at the jack, the CMRR assumption is wrong and
ADR 0014's number is closer than mine.

---

### F7 — The 18 switches' common return is specified nowhere, and the two obvious implementations create the largest loop in the instrument, alongside the pulsed LED runs

**Severity: MAJOR** (and unrecoverable after bonding)

**Where.** ADR 0001 lists five wiring fixes for the key chain and leads with:

> "1. **A ground return per signal.** The highest-value item on this list. Four
> signals down a 14-inch body sharing one return is a loop antenna next to an
> 800 kHz LED data line."

ADR 0009 repeats it:

> "**The key chain still needs a ground return per signal** (ribbon with
> alternating grounds, or twisted pairs)"

Both rules are about the **chain** signals — clock, data, latch. Neither
document, nor `config/key-layout.yaml` (which is otherwise the single source of
truth for the keys and carries `cluster` assignments for all 18), says anything
about the *switch* side: no pull-up value, no pull-up location, and no statement
of where the 18 switch commons return to.

**Why.** A KS-33 is a two-contact switch. One side goes to a 74LVC165 parallel
input, the other to "ground". Which ground, and routed how, decides whether the
input threshold is referenced to the same node as the register that reads it.

Two implementations are natural and both are wrong:

- **A common bus wire daisy-chained across all 18 switches.** That wire spans
  the full 457 mm on the plate side of the cavity while the cluster boards'
  grounds come up the loom in the side channels, 20–30 mm away. Enclosed loop
  ≈ 400 mm × 25 mm = **100 cm²**, running the length of the instrument parallel
  to two WS2815 runs carrying pulsed current.

  Mutual inductance, a wire-to-loop estimate
  `M ≈ (µ₀/2π)·l·ln(d₂/d₁) = 2×10⁻⁷ × 0.4 × ln(50/10) = 129 nH`:

  | Strip current step | Edge | Induced in the loop |
  |---|---|---|
  | 125 mA | 200 ns | 81 mV |
  | 250 mA | 200 ns | **161 mV** |
  | 250 mA | 100 ns | **322 mV** |

  Against a 74LVC165's V_IL of 0.8 V (memory), 161–322 mV is 20–40 % of the
  low-side noise margin, arriving 8000 times a second (2 kHz PWM × 2 edges ×
  2 strips). The chain reads for ~32 µs per 250 µs loop, so roughly **26 % of
  reads contain an LED edge**.

- **Using the aluminium plate as the switch common.** It is right there, it is
  bonded to `PWR_GND` (MECH-GNDBOND), and the switch pins are 1–2 mm from it.
  This is worse: the switch common then returns through a single bond wire to
  the carrier while the registers are referenced to the loom at each cluster, so
  the reference difference is the entire loom drop plus the bond wire. Nothing
  in the documents forbids it, and MECH-GNDBOND's existence invites it.

What makes this expensive rather than annoying is the interaction with two other
decisions. ADR 0001:

> "**Asymmetric debounce fires on the first closed sample**, so one corrupted
> 32-bit word becomes **one spurious note-on at full velocity, with no
> filtering**"
> "**`SH/LD` is asynchronous and level-sensitive.** Any glitch below V_IL during
> the 32-clock shift re-loads all four registers and corrupts the whole word."

And the LED strips are driven from breath, so the interference is at its worst
exactly when the player is playing.

**Proposal.** Three lines in ADR 0001 and one field in `key-layout.yaml`:

1. **Each cluster's switch commons return to that cluster board's own ground
   pad**, by the shortest path. No bus wire spans clusters.
2. **The aluminium plate is a bonded shield and an ESD path. It is never a
   circuit conductor** — not the switch common, not a return, not a shield drain
   carrying signal current.
3. **Pull-ups live on the cluster board**, one per input, 10 kΩ, referenced to
   that board's 3.3 V and ground. (18 × 3.3 V/10 kΩ = 5.9 mA worst case, all
   pressed — negligible, and it stays local.)
4. Consider 74HC165 rather than 74LVC165A for the 0.99 V vs 0.80 V V_IL. The BOM
   already argues this — though the argument is in the wrong row, under `CAP1-n`
   (keycaps): *"74HC preferred over LVC for ~2x input noise margin"*. The "~2×"
   is not right (0.99/0.80 = 1.24× on the low side; LVC is actually better on
   the high side, 1.3 V vs 0.99 V), but 24 % more margin against a 161–322 mV
   disturbance is worth having, and the BOM already says it is a drop-in on the
   same footprint.

**Confidence: medium-high.** The gap in the documents is certain. The induced
voltage is an order-of-magnitude estimate — `M` depends on the real geometry and
the WS2815's output edge rate, which I do not have and which is the weakest
input here. If the strips' PWM edges are 1 µs rather than 100–200 ns, the figure
drops to 16–32 mV and this becomes a MINOR.

**Falsified by:** the roadmap already has the measurement — *"Key-chain error
counter over an hour, LEDs and WiFi active"* at E4. Run it twice: once with the
switch commons bussed and once returned per cluster, with the strips at the full
3 W clamp and animating. A non-zero delta proves the mechanism; a zero count in
both cases falsifies it. Do it at E4, while the looms are still buildable — the
roadmap correctly calls this one of the two time-critical measurements.

---

### F8 — The cable shield and both connector shells are unspecified, and as drawn they form a third, intermittent power-return path tying the instrument to the rack chassis

**Severity: MINOR** (rising to MAJOR if the shells end up as the path of least
resistance)

**Where.** ADR 0004 specifies the shield and then says nothing about terminating
it:

> "**Shielded (STP/FTP) preferred.** Twisted pairs are what make the analog
> breath channel survive (ADR 0003) and any Cat5e has those, but the shield is
> free at this price"

And the mechanical side, ADR 0009:

> "**Mount the connector to an internal backing plate** — aluminium or ply, tied
> into the same stack that carries the keys"

**Why.** A shielded patch lead bonds its shield to the plug shell, which bonds
to the etherCON chassis shell at both ends. Follow it:

- **Instrument end:** shell → backing plate (if aluminium) → the plate stack →
  the aluminium key plate → `MECH-GNDBOND` → `PWR_GND`. So the shield is
  strapped to instrument ground.
- **Module end:** shell → 6HP panel → rack rails → chassis → the PSU's earth
  stud, which is normally where rack 0 V is earthed. Also, PJ398SM bushings
  usually tie the panel to module 0 V through the jack nuts.

Result: a third conductor in parallel with `PWR_GND` and `DIG_GND`, of *lower*
resistance than either (a foil-plus-drain is maybe 0.05–0.10 Ω over 2 m, memory)
but in series with joints whose resistance is anodising-, torque- and
oxide-dependent — anywhere from 1 mΩ to open. It will carry a share of the
instrument's 320–430 mA, and the share will change as the cable flexes, which
the design says happens constantly.

The good news, which I checked: the shield and the conductors are coincident
inside one jacket, so the shield-versus-conductor loop area is essentially zero.
There is no magnetic-pickup loop here. The consequences are current sharing
(common-mode, rejected on breath) and putting the instrument's modulated current
into the rack chassis instead of the bus ground, which makes F1 worse or better
depending on nothing anybody controls. And the etherCON D contact rating of
~1.5 A per contact (ADR 0004's own table) is comfortable at 215 mA per ground
contact, so nothing is stressed.

**Proposal.** Decide it, write it, and make it measurable:

- **Module end: bond the shell to module 0 V at the connector**, not to the
  panel — an isolating shoulder washer on the etherCON flange, which is standard
  hardware. That keeps the shield as an EMC shield and off the chassis.
- **Instrument end: bond the shell to `PWR_GND` at the same single point as the
  plate bond**, or float it. Do not let the backing plate silently become the
  bond.
- **Say which**, in ADR 0004's cable section, and put it in the M7 build notes.
  The choice is currently made by whichever hardware arrives.

**Confidence: medium.** The mechanism is certain; the magnitude depends entirely
on hardware details (anodising, whether the backing plate is aluminium or ply,
which etherCON variant — still open per ADR 0004's final section) that the
project has deliberately deferred to E12/M7. This finding's real content is that
the deferral has an electrical consequence nobody has listed.

**Falsified by:** with the instrument at full draw, clamp a current probe around
the whole umbilical cable. Net current should be zero if all return is inside
the jacket; a non-zero reading is the shield/chassis share, directly. Under
5 mA and the shield is not participating.

---

### F9 — Fault and hot-plug behaviour is survivable, but only by accident, and the module energises the instrument's dead 3.3 V rail in its declared normal state

**Severity: MINOR**

**Where.** ADR 0004:

> "The panel switch cuts +12 V to the umbilical while the module stays powered
> from the bus. So the ordinary powered-down state is: **module alive, DAC
> alive, and SCLK / MOSI / CS floating** at the level shifter's inputs … it is
> the state the instrument spends most of its life in."
> "**CS pulled to +5 V; SCLK and MOSI pulled to ground**, at the module end."

BOM: `R-SPI-PULL, module, 10k 1%`.

**Why.** Two sub-cases, one each way.

**(a) Mating order — survives on a resistor placed for a different reason.** An
8P8C mates all eight contacts at one insertion depth, but the springs differ by
fractions of a millimetre and a hand insertion takes ~100 ms, so tens of
milliseconds of skew between contacts is realistic. The interesting order is
+12 V (pin 3) mating before both power returns (pins 6 and 8). The only
conductor left that reaches module 0 V is `AGND` — through the in-amp's input
structure. Without a series element that is the entire inrush through an
input clamp, and the in-amp dies.

It does not happen, because ADR 0003 put 10 kΩ in each input leg:

> "gigaohm inputs make source impedance irrelevant, so protection resistors can
> be 10 kΩ and unmatched with no CMRR penalty"

`12 V / 10 kΩ = 1.2 mA` through the clamp — survivable, and the instrument
simply does not start because it has no return. The design is saved by a
resistor whose stated justification is "this no longer costs us CMRR". That
should be recorded as a fault-current limit so nobody value-engineers it later.
With F3's split shunt in place the case improves further: the AGND leg then also
has a 50 kΩ path to module 0 V.

**(b) The module back-powers a dead instrument, continuously.** In the declared
normal state — module on, instrument off — the 10 kΩ pull-up on `CS` sources
`5 V / 10 kΩ = 0.5 mA` down the cable into an unpowered ESP32-S3 output pin,
through that pin's ESD diode, into the instrument's dead 3.3 V rail. Half a
milliamp into an unpowered rail partially biases the die and is a classic
partial-power hazard; it is also being done for most of the instrument's life.
The `SCLK`/`MOSI` pulldowns are harmless in comparison (they sink from a pin
that is not driving).

The 74AHCT125 OE gating already specified does not help — the pulls are on the
buffer's *inputs*, which is where they need to be to stop the CMOS stage
oscillating.

**Proposal.**

- **Raise the three idle pulls to 100 kΩ.** That is still 10× firmer than the
  AHCT input leakage needs (±1 µA max × 100 kΩ = 0.1 V of input uncertainty,
  memory), and it cuts the back-feed to **50 µA**, which is below the leakage
  the instrument's own rail sinks.
- Annotate `R-OPAMP-IN`-style: add a BOM note on the in-amp's two 10 kΩ input
  resistors recording that they are also the umbilical fault-current limit at
  +12 V and during asymmetric mating, and must not be reduced.
- Add a TVS at the **module** end of the analog pair. `U-TVS-UMB` exists only at
  the instrument end ("8 conductors from outside"); the module end has eight
  conductors from outside too, and `AGND` there has no low-impedance return to
  clamp into (F10).

**Confidence: medium-high** on (b) — it follows from the ESP32's pin clamp
structure, which is standard but which I am asserting from memory. **High** on
(a), which is just the resistor being in the path.

**Falsified by:** measure the current into the umbilical's `CS` conductor with
the module powered and the instrument unpowered but connected, and measure the
instrument's 3V3 rail voltage in that state. If 3V3 sits below ~0.3 V the
back-feed is being absorbed harmlessly and (b) is a non-issue.

---

### F10 — The plate-bonding rule is right, but its stated reason is wrong by about six decades; the real reason is ESD, and that implies a requirement the design does not have

**Severity: MINOR** (the decision stands; the rationale and one consequence need
replacing)

**Where.** ADR 0009, in "Things that are free now and impossible later":

> "**Bond the aluminium plate to `PWR_GND`. Never to `AGND`.** … An unbonded
> plate means the instrument fires random notes when touched in a dry room …
> The choice of *which* ground matters as much as the bonding: tying it to
> `AGND` would put the player's body capacitance straight onto the breath
> channel's voltage reference."

**Why.** Take the stated mechanism seriously and compute it. The player's body
couples to mains wiring through a few picofarads; at 230 V, 50 Hz, 3 pF
(memory figures):

```
I = 230 × 2π × 50 × 3 pF = 217 nA
across AGND's 0.189 Ω:  217 nA × 0.189 = 41 nV
```

**41 nanovolts**, against a 153 µV LSB. Even at 10 pF of coupling it is 137 nV.
Bonding the plate to `AGND` would be invisible on the breath channel by roughly
six orders of magnitude. The stated reason does not hold at all.

The conclusion is still correct, for a reason the ADR does not give: **ESD has
to go somewhere.** `AGND` is the one conductor in the system with no
low-impedance return at the module end — by design (F3). An 8 kV HBM event
(100 pF / 1.5 kΩ: 5.3 A peak, few-nanosecond rise, memory) landing on a plate
bonded to `AGND` has no path to module 0 V except the in-amp's input clamps
through 10 kΩ. That destroys the receiver. On `PWR_GND` it has two fat
conductors and a bus header.

The same reasoning also explains the symptom the ADR names. At 50 Hz an
unbonded plate injects nothing measurable into the switch pins either — 2 V of
body potential through 0.2 pF of plate-to-pin coupling into a 10 kΩ pull-up is
`2 × 2π50 × 0.2p × 10k = 1.3 µV`. What actually fires spurious notes on a
floating plate is a triboelectric discharge, not hum.

**And that has a consequence the ADR misses.** If the bond's job is to carry
ESD, its **inductance** is the specification, not its existence:

```
bond inductance × dI/dt, at 5.3 A in 5 ns (1.07 × 10⁹ A/s):
  50 nH  (a short strap, ~50 mm)   →   53 V
  400 nH (a flying lead down the body, ~400 mm) → 427 V
```

A 400 mm ring-terminal lead from the key plate at the top of the stack to the
carrier at the tail — which is the natural build given where `MECH-GNDBOND`'s
partner board lives — lets the plate rise 400+ V relative to the registers
during an event, with 18 switch pins 1–2 mm away. A short bond to the *nearest*
cluster board's ground keeps it near 50 V.

**Proposal.** Rewrite the rationale and add the rule:

- Reason for `PWR_GND`, not `AGND`: **ESD return path.** `AGND` has no
  low-impedance return at the module end, so a discharge onto a plate bonded to
  it is forced through the in-amp's input clamps. (The body-capacitance
  argument as written is 41 nV and should be deleted before somebody re-derives
  it and reaches the opposite conclusion.)
- **Specify the bond as short and low-inductance**: a wide strap or braid to the
  nearest cluster-board ground pad, not a ring terminal on a long lead to the
  carrier, and state the target (< 100 nH, which in practice means < 100 mm).
- Keep `MECH-GNDBOND`. It is the right decision.

**Confidence: high** on the arithmetic; **medium** on the ESD figures, which are
the standard HBM model from memory.

**Falsified by:** ESD gun, ±8 kV contact discharge to the plate at M8 (pre-bond,
while it is still fixable), watching the key-chain error counter and the note
output. Repeat with a long bond and a short bond and compare counts.

---

### F11 — "Any Cat5e patch lead" spans a 2.8× range of conductor resistance, and every ground figure in the design depends on it

**Severity: MINOR**

**Where.** ADR 0004's cable spec is careful about two things and silent on a
third:

> "**Stranded patch cable, never solid-core** … **Shielded (STP/FTP)
> preferred.**"
> "**The cable is a consumable.** … Keep spares. Replace the lead at the first
> sign of intermittency rather than diagnosing it."

And ADR 0005's power table rests on a gauge nobody has pinned:

> "Over 2 m of 24 AWG, round trip ~0.34 Ω"

**Why.** 0.34 Ω for 2 m × 2 conductors implies 0.0842 Ω/m — the **solid-copper**
24 AWG figure, while the spec correctly mandates **stranded** (which is ~10–15 %
higher) and never states the gauge at all. Real patch leads in a drawer:

| Lead | Ω/m (memory) | 2 m, one conductor | vs the assumed figure |
|---|---|---|---|
| 24 AWG solid (the assumption) | 0.0842 | 0.168 Ω | 1.00× |
| 24 AWG stranded | ~0.094 | 0.189 Ω | 1.12× |
| 26 AWG stranded | ~0.150 | 0.300 Ω | 1.78× |
| 28 AWG "slim" stranded | ~0.238 | 0.476 Ω | **2.83×** |
| Copper-clad aluminium, any gauge | ×1.6 on the above | — | up to ~4.5× |

28 AWG slim patch leads are common, look identical, and are frequently what gets
grabbed. At 430 mA the parallel-return offset goes from 41 mV to 102 mV, the
+12 V drop roughly triples, and the shared-return terms in F1/F2 scale with it.
None of that breaks anything — it is all common-mode or has headroom — but the
project's stated habit of replacing the lead casually means the *electrical
behaviour changes when the cable does*, with no indication.

**Proposal.** Add to the cable spec and to `CABLE-UMB` in the BOM: **24 AWG
stranded pure copper, not CCA, not 26/28 AWG slim.** State the acceptance test:
measure loop resistance end to end on every new lead before it goes into
service; it should read under 0.45 Ω for a 2 m lead (2 × 0.189 Ω plus
contacts). That is a 30-second DMM check on a consumable and it catches CCA,
thin gauge, and a bad crimp at once.

**Confidence: high** on the gauge spread; **medium** on the specific Ω/m values,
which are from a remembered AWG table (though ADR 0005's own 0.34 Ω corroborates
the 24 AWG entry).

**Falsified by:** four-wire measure the loop resistance of the leads actually
bought. If they are all 24 AWG copper, this is a note rather than a finding.

---

## 3. Where the design is correct

Said explicitly, because several of these are unusual and were clearly hard-won.

**The `AGND` sense-return concept is right, and the reasoning behind it is
sound.** ADR 0003's derivation — a patch cable works because its ground does one
job; the umbilical breaks that only if one conductor does both; so give the
analog signal its own return — is correct, well argued, and correctly identifies
the quantity that matters. My findings attack the places the rule is not carried
through (F2, F3, F5), not the rule.

**The differential pulldown, for the reason given.** A single-leg shunt really
would cap CMRR near 19 dB. F3 changes its implementation, not its principle.

**The buffered in-amp over the difference amp.** Correct, and for the correct
reason: source-impedance balance sets a difference amp's CMRR, gigaohm inputs
make it irrelevant, and that dissolves the protection-resistor conflict. The
10 kΩ input resistors that fall out of it turn out to be the module's only fault
protection (F9) — a happy accident worth making deliberate.

**The T568B pin mapping.** I checked the physical adjacency: on an 8P8C, pin 3
sits between 2 and 4 and pin 6 between 5 and 7, so the DC power pair genuinely
does sit between the analog pair and both digital pairs, and `BREATH` at pin 1
is adjacent only to its own return. `SCLK` at pin 7 is as far from pin 1 as the
connector allows. The reasoning is right and the conclusion is right.

**Band-limiting to ~500 Hz at both ends.** This is the single most effective
thing in the whole analog channel — a 159 Hz signal in a 500 Hz channel rejects
the LED PWM (2 kHz), the LED data (800 kHz), SPI (0.6–1 MHz) and the buck
(~500 kHz) for free.

**Bonding the plate, and bonding it to `PWR_GND`.** Right decision (F10 replaces
the rationale, not the decision).

**The load switch at the module rather than a polyfuse at the instrument**, and
the analysis of the polyfuse runaway loop in ADR 0014, are both correct and the
runaway analysis is genuinely good.

**Bulk at the load, an LC not a bead into the buck, ferrites rated ≥1 A.** All
three corrections in ADR 0004 are right, and the "a bead is a wire at 2 kHz"
observation is exactly the kind of thing that normally goes unnoticed.

**The player is not a hazard and not a hum path.** I checked all three cases:

- Body-coupled mains current into the bonded plate: **217 nA** (230 V, 3 pF),
  developing 20 nV across the parallel returns. Nothing.
- Touching the plate (26–41 mV above module ground) and a grounded jack sleeve
  simultaneously: `41 mV / 1 kΩ = 41 µA`. Two orders below perception.
- Bench USB with a Class-II laptop: a 2.2 nF Y-capacitor at 115 V gives
  `115 / 1.45 MΩ = 80 µA`. Below the ~0.5 mA perception threshold. Note the
  USB/umbilical OR-diode (ADR 0005) does create a genuine mains-earth loop on
  the bench, but the circulating current through a ~1 m² loop in a 1 µT field is
  ~600 µA, developing 10 µV across the bus segment — 0.012 cents. Harmless.

**There is no meaningful mains-frequency ground loop in the performance
configuration**, because the instrument touches earth only through the player's
skin and the umbilical, and the skin path is kilohms against milliohms.

**The digital link's noise margin is fine.** 30–41 mV of reference offset plus
~20 mV of LED-frame step, against 800 mV of TTL low-side margin: 5–8 % consumed.
No action needed, and it is worth recording so it does not get re-litigated.

---

## 4. Measurements this review would add to the plan

All hang off milestones that already exist.

| Measure | At | Falsifies |
|---|---|---|
| **Pitch jack, DC-coupled, while sweeping the LED animation blank → full clamp**, with the real VCO loaded, plus module-0 V to VCO-0 V on a second channel | E6 (dummy load), repeated at E9 | F1 — the most important measurement in this review, and the one the plan currently does not contain |
| Current probe on individual `PWR_GND` and `DIG_GND` conductors at full draw | E11 | F2 |
| Unplug the umbilical mid-note; scope breath. Repeat with only pin 2 lifted | E10/E11 | F3 |
| 400 mA injected etherCON-return → header-ground, µV between jack sleeve, DAC GND, LM317 ADJ ground | E12 | F4 |
| Breath jack while stepping LED animation at constant mouth pressure, **on the carrier** | E14 | F5 |
| 100 mV, 40 Hz injected between instrument and module ground, breath input shorted | E10 | F6 |
| Key-chain error counter, LEDs at full clamp, bussed common vs per-cluster common | E4 | F7 — time-critical; the looms are sealed at M6 |
| Clamp the whole cable; net current should be zero | E11 | F8 |
| `CS` conductor current and instrument 3V3 voltage, module on / instrument off | E6 | F9 |
| ±8 kV contact discharge to the plate, long bond vs short bond | M8 (pre-bond) | F10 |
| Four-wire loop resistance of every umbilical lead bought | now | F11 |

---

## 5. Summary

| # | Finding | Severity |
|---|---|---|
| F1 | Breath-correlated pitch error via the rack's shared ground, 2–5 cents | MAJOR |
| F2 | Ground joins unstated; `DIG_GND` is a second power return | MAJOR |
| F3 | No CM bias return at the in-amp: unplugged `AGND` rails breath CV | MAJOR |
| F4 | Module's internal return topology undefined | MAJOR |
| F5 | Instrument star point defined as a region, not a point | MAJOR |
| F6 | ADR 0014's CV-path coupling number is ~10⁴ too large; ADC path is the real one | MINOR |
| F7 | Switch-common return unspecified; largest loop in the instrument | MAJOR |
| F8 | Shield and shell bonding unspecified at both ends | MINOR |
| F9 | Fault/hot-plug survivable by accident; module back-powers a dead 3V3 rail | MINOR |
| F10 | Plate-bond rationale wrong by six decades; bond inductance unspecified | MINOR |
| F11 | Cable gauge unspecified across a 2.8× range | MINOR |

**The single-sentence version.** The analog sense return is well conceived and is
carried through about two-thirds of the way — it is never told where to join, it
has no common-mode bias return, and its star point is named as a region rather
than a node — but the bigger and entirely unexamined problem is the other
direction: this module passes 300–430 mA of breath-correlated current through
the same rack ground that its single-ended pitch output is referenced to, which
is worth more pitch error than every precision part in the module is worth in
the other direction, and the test plan only ever looks at breath.
