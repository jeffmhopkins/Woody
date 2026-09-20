# B2 — The analog breath link across the umbilical

Independent review. Scope: sensor buffer → series protection → Cat5 umbilical →
etherCON → module receiver → gain/offset → breath jack. Sources read: `README.md`,
`ROADMAP.md`, `docs/decisions/0001`–`0014`, `docs/reference/`, `hardware/bom.csv`.
No prior review material was consulted.

## Datasheet figures used, and how they were obtained

| Figure | Value used | Provenance |
|---|---|---|
| MPXV4006 transfer function | `Vout = VS(0.1533·P + 0.04)` | **Verified** (matches ADR 0003's own statement and the NXP/ST datasheet summary) |
| MPXV4006 VFSS typ | **4.6 V** | **Verified** via datasheet search |
| MPXV4006 Voff | **0.152 / 0.265 / 0.378 V** (min/typ/max) | **Verified** via datasheet search. Note ADR 0003 and the BOM both use "0.2 V", which is the *transfer-function* value, not the spec limit |
| MPXV4006 accuracy, 10–60 °C | **±2.46 % VFSS with auto-zero, ±5.0 % VFSS without** | **Verified** via datasheet search. This is the single most load-bearing number in this review |
| INA821 input bias current | **150 pA typ** | Verified via search summary; TI PDF was blocked by the egress proxy, so min/max not confirmed |
| INA821 CMRR at G=1 | **≥92 dB over the full CM range** | Verified via search summary; not read from the PDF |
| INA821 Vos / drift | 35 µV RTI; input-stage drift ~0.35 µV/°C | Partly verified (35 µV confirmed); the RTO offset and RTO drift terms are **from memory** and are flagged where used |
| INA821/INA828 internal difference-amp resistors ≈ 10 kΩ, REF referred through them | 10 kΩ | **From memory.** The REF-impedance arithmetic in Finding 7 scales linearly with this and should be checked against the datasheet before it is acted on |
| In-amp CMRR roll-off with frequency (≈ −20 dB/decade above ~1 kHz at low gain) | generic | **From memory**, class behaviour, not this part specifically |
| INA134 internal resistors 25 kΩ | 25 kΩ | **From memory.** It reproduces ADR 0003's own quoted "10 Ω mismatch → 74 dB" exactly (20·log₁₀(2/(10/25 000)) = 74.0 dB), which is a good independent check on both |
| Cat5e 24 AWG solid DC resistance | 0.0842 Ω/m | Standard copper table, **verified by calculation**; matches ADR 0003's own 16.8 mV/100 mA figure |
| RJ45 mated contact resistance | ≤20 mΩ initial (IEC 60603-7) | **From memory** |

---

## Working the link: what is actually on the wire

### The common-mode voltage that AGND develops

`AGND` carries no current by design, so the common-mode voltage the receiver sees is
the potential of the instrument's analog star point relative to module ground — i.e.
the IR drop in the **power return**, not in AGND itself.

Two things change ADR 0003's arithmetic, and they pull in opposite directions.

**Up: conductor gauge is unspecified.** ADR 0003's table (100 mA → 16.8 mV etc.)
assumes one 24 AWG conductor: 0.0842 Ω/m × 2 m = 0.168 Ω. That reproduces exactly.
But `CABLE-UMB` specifies only *"Cat5e STP patch lead, STRANDED, ~2 m"*. Stranded
patch cord is commonly 26 AWG, and slim patch cords are 28 AWG; stranding adds a
further ~5 %. Four mated RJ45 interfaces (two if a solder-tag etherCON is chosen,
four if the feedthrough variant of ADR 0004's open question wins) add ~40–80 mΩ.

**Down: the return is two conductors, not one.** `PWR_GND` (pin 6) and `DIG_GND`
(pin 8) are the same net, bonded at both ends — `DIG_GND` must be, or it is not an
SPI return. They parallel.

| Gauge | R per 2 m conductor | Effective return (PWR‖DIG + contacts) | V_cm at 430 mA |
|---|---|---|---|
| 24 AWG stranded | 0.177 Ω | 0.108 Ω | **47 mV** |
| 26 AWG stranded | 0.281 Ω | 0.161 Ω | **69 mV** |
| 28 AWG stranded | 0.447 Ω | 0.243 Ω | **105 mV** |
| 26 AWG, *if* DIG_GND is left unbonded | 0.281 Ω | 0.321 Ω | **138 mV** |

**Take V_cm(DC) ≈ 70 mV**, with a plausible range of 47–140 mV. ADR 0003's 59 mV at
350 mA is in the right order but is right for the wrong reason: it over-counts the
return resistance by 2× and under-counts the current by ~25 %.

### The spectrum of the disturbance — which matters more than the amplitude

| Component | In-band? | Amplitude of V_cm |
|---|---|---|
| Steady DC offset (instrument quiescent draw) | no (constant) | ~50 mV |
| **LED animation envelope** — 3 W clamp = 250 mA at 12 V, swinging at note rate | **yes, 1–50 Hz** | **~40 mV, correlated with breath itself** |
| **WiFi TX bursts** — ~200 mA steps, ms envelopes | **yes, 10–100 Hz** | **~32 mV** |
| WS2815 PWM carrier ~2 kHz | no (above the 500 Hz filter) | ~15 mV (after the 470–1000 µF at the feed point shunts ~62 %) |
| Buck switching 500 kHz | no | µV, killed by `L-BUCK-IN` |

**The in-band CM disturbance is ~40 mV and it tracks the playing.** That is the
number the link has to reject. A static 50 mV would be harmless (the gain/offset
knobs and the auto-zero absorb anything slow); 40 mV that moves with the light show
and the radio is audible as breath-correlated wobble at ~0.4 % of full scale if
unrejected. **ADR 0003 is right that this matters and right about why.**

### The gain chain, corrected

ADR 0003 quotes "~2.13×" for the in-amp (= 10 V / 4.7 V). Two corrections:

- The zero pedestal (0.265 V typ) is not signal, so the span is VFSS = 4.6 V, not 4.7 V.
- The 10 kΩ series protection resistor and the 100 kΩ differential pulldown form a
  **divider of 100/110 = 0.9091**, which nothing in the documents accounts for.

G = 10 V / (4.6 V × 0.9091) = **2.39**, not 2.13 — a 12 % error in the one number
the module's breath stage is designed around.

---

# Findings

## 1. The in-amp has no common-mode bias return, so unplugging the instrument sends breath CV to a rail — the exact opposite of the stated behaviour

**SHOWSTOPPER**

**Where.** ADR 0005: *"**Pull down the module's breath receive input**, so that an
instrument which is switched off — or unplugged — presents 0 V rather than a floating
buffer output."* `hardware/bom.csv`, `R-PD-BREATH`: *"100k … **DIFFERENTIAL across
BREATH-AGND not one leg** — a single-leg shunt caps CMRR near 19dB."* ADR 0003:
*"Put the pulldown **differentially across BREATH–AGND**, not on one leg."*
ADR 0006's power-on table: *"Breath | 0 V | The receiver's differential pulldown
holds it there."*

**Why.** A purely differential pulldown provides a **differential** path and no
**common-mode** path. When the cable is plugged in, the in-amp's bias currents return
through AGND → instrument analog ground → instrument power ground → `PWR_GND` →
module ground. That works. **When the cable is unplugged, that path is gone** and both
in-amp inputs are floating on ~10 pF of pin and PCB capacitance with nothing to hold
them:

```
dV/dt = I_bias / C = 150 pA / 10 pF = 15 V/s
```

Both inputs ramp together toward a rail; within ~1 s the input common-mode range is
exceeded and the in-amp output saturates. The 100 kΩ across the inputs holds the
*differential* voltage at I_os × 100 kΩ ≈ 50 µV, which is exactly the quantity that
does not matter. The output does not go to 0 V; it goes wherever the saturated in-amp
and the downstream knob stage land, i.e. **near +11 V on a rail-limited output, into a
VCA, indefinitely.**

The same mechanism makes a **single broken AGND conductor** — in a cable the design
explicitly treats as a consumable that will fail — produce a full-scale drone rather
than a degraded signal.

The documents are also silent on the alternative, and the alternative is worse: if a
layout engineer instead ties `AGND` directly to module ground at the module end (a
natural reading of "analog ground"), the sense-return scheme is defeated outright —
the AGND conductor becomes a third parallel power return, the in-amp measures against
local ground, and V_cm reappears as 70 mV × 2.39 = **167 mV of signal error**.
**Both obvious readings of the documents fail; the correct one is written down
nowhere.**

**Proposal.** Specify the module-end input network completely:

- **2 × 1 MΩ from each in-amp input to module analog ground** (a matched pair or a
  two-resistor array), providing the common-mode bias return. Delete the 100 kΩ
  differential part — the two 1 MΩ give 2 MΩ differentially, which is ample.
- **Symmetrise the series resistance** (see Finding 3) — otherwise the bias pair
  re-introduces the source-impedance-balance problem the buffered in-amp was bought to
  delete: 10 kΩ on one leg against 1 MΩ bias caps CMRR at 20·log₁₀(1 M/10 k) = **40 dB**.
  With both legs at 10 kΩ ±1 % (200 Ω mismatch) the cap is 20·log₁₀(1 M/200) = **74 dB**.
- State in ADR 0005 that `AGND` is **never** DC-bonded to module ground except through
  these two 1 MΩ resistors.

Cost: two resistors, zero risk, one sentence in the ADR.

**Confidence: high (0.9).** The physics is elementary and the omission is explicit
rather than implied — the BOM line actively forbids the leg shunt that would have
saved it.

**Falsifying measurement.** At E10, with the module powered and **no cable plugged in**,
put a DMM on the breath jack. If it reads within a few mV of 0 V, something in the
built board is providing a bias path the documents do not describe and this finding is
wrong. If it reads a rail, it is right. Repeat with the cable plugged and the
instrument unpowered — that case should read 0 V either way, and the contrast between
the two is the diagnostic.

---

## 2. The ambient-zero injection requires a negative REF voltage that a 0–5 V DAC channel cannot produce, so the continuous auto-zero cannot subtract anything

**SHOWSTOPPER**

**Where.** ADR 0003: *"**The zero is injected at the module, into the in-amp's `REF`
pin, from DAC channel 6**."* ADR 0006: *"DAC channel 6 drives the ambient-zero offset
into the in-amp's REF pin. So **decay the zero toward the current reading** …"*
`hardware/bom.csv`, `U-DIFFRX`: *"REF pin takes the ambient-zero injection."* The DAC
is a `DAC8568` on a 5.25 V regulator with a 0–5 V unipolar output (ADR 0004, ADR 0006).

**Why.** The in-amp transfer function is

```
V_out = G·(V_BREATH − V_AGND) + V_REF
```

At zero breath, V_BREATH − V_AGND is the sensor's offset, Voff. To null it:

```
V_REF = −G · Voff
      = −2.39 × 0.265 V  =  −0.63 V    (Voff typ, verified datasheet value)
      = −2.39 × 0.378 V  =  −0.90 V    (Voff max)
      = −2.39 × 0.152 V  =  −0.36 V    (Voff min)
```

**V_REF must be negative in every case, and the DAC channel can only produce 0 to
+5 V.** The injection as specified can only *raise* the floor. The pedestal it exists
to remove is between **+0.36 V and +0.90 V at the jack — 3.6 % to 9.0 % of full
scale** — and it sits there permanently, opening any VCA patched to it.

This is not a rounding issue that the panel offset knob quietly absorbs. Three
consequences compound:

- The offset knob, which ADR 0006 assigns to *"position where the floor sits"* for the
  player, is consumed by a fixed manufacturing pedestal instead.
- **The *continuous* auto-zero — the whole mechanism ADR 0006 introduces against the
  10–20 K warm-up drift — is non-functional in the subtract direction**, which is the
  only direction a warming gauge sensor drifts in a sealed body.
- The verified datasheet accuracy is **±2.46 % VFSS with auto-zero and ±5.0 % VFSS
  without**, over 10–60 °C. At G = 2.39 on a 4.6 V span that is **±270 mV vs ±550 mV
  at the jack**. Breaking the auto-zero doubles the dominant error term in the entire
  budget.

**Proposal.** Drive REF from a **bipolar** stage, which the module already has rails
for:

```
DAC ch6 (0–5 V) ──[R1 100k]──┬──[R2 18k]──┐
                             │            │
                     module AGND       OPA2197 (inverting, ±12 V)  ──► in-amp REF
```

Gain −0.18 gives 0 → −0.90 V, covering the full Voff distribution with 14 µV of
resolution per DAC LSB. This costs **no extra op-amp** — DAC ch 6 needed a buffer
anyway, and the inverting stage *is* that buffer. Put the DAC reconstruction RC
**inside or before** this stage (e.g. as the feedback capacitor), never in series with
the REF pin — see Finding 7.

Alternative, if a negative supply at that node is unwelcome: give the in-amp a second
input pedestal instead by taking the AGND-side input to (AGND + DAC ch 6 / 2.39)
through a matched divider — but that destroys source-impedance balance and I would
not recommend it.

**Confidence: very high (0.95).** The sign is not ambiguous, the DAC's polarity is not
ambiguous, and the sensor's offset polarity is a verified datasheet figure.

**Falsifying measurement.** At E10, with the sensor at ambient and DAC ch 6 swept
across its full code range, measure the breath jack. If the output can be driven
*below* the reading obtained with ch 6 at code 0, a level shift exists somewhere and
this finding is wrong. If code 0 is already the minimum and the floor sits at
+0.4…+0.9 V, it is right.

---

## 3. ADR 0004 still specifies the INA134, which with the design's own 10 kΩ protection resistor achieves 14 dB of CMRR, not 90

**MAJOR**

**Where.** ADR 0004, *"Module parts, chosen for build ease"*: *"**INA134 for the
breath difference amp.** On-chip matched resistors give ~90 dB CMRR against the 60 dB
needed (ADR 0003), with no external matching network to place or match."* This
directly contradicts ADR 0003 (*"**But the receiver is a true instrumentation
amplifier (INA821 / INA828), not a difference amplifier**"*) and `hardware/bom.csv`
(`U-DIFFRX = INA821 or INA828`).

**Why.** ADR 0003 already worked this out and ADR 0004 was never updated. The
arithmetic, using the INA134's 25 kΩ internal resistors, reproduces ADR 0003's own
cited figures exactly, which is a good cross-check on both:

```
CMRR ≈ 20·log₁₀[ (1 + R2/R1) / (ΔR_source/R1) ]
  ΔR =    10 Ω → 20·log₁₀(2 / 0.0004) =  74.0 dB   (ADR 0003 quotes "~74 dB")
  ΔR =  3.3 kΩ → 20·log₁₀(2 / 0.132)  =  23.6 dB   (ADR 0003 quotes "~24 dB")
  ΔR =   10 kΩ → 20·log₁₀(2 / 0.400)  =  14.0 dB   ← the value actually specified
```

At 14 dB, the ~40 mV of in-band, breath-correlated common mode becomes 8 mV of
differential error, ×1 (the INA134 is fixed unity gain) and then ×2.39 through the
scaling stage the INA134 cannot absorb = **19 mV at the jack, moving with the LED
animation and the WiFi**. And the INA134 is fixed-gain, so a separate 2.39× stage
comes back, undoing ADR 0003's part-count argument.

This matters more than an ordinary doc inconsistency because ADR 0004 is the
*module build* document — it is where someone assembling the board will look for "what
chip goes here", and it is the more specific-sounding of the two.

**Proposal.** Delete the INA134 paragraph from ADR 0004 and replace it with a pointer
to ADR 0003's receiver decision and the `U-DIFFRX` BOM line. While there, correct the
"~2.13× scaling stage" figure in ADR 0003 to 2.39× (Finding 4) and state the resulting
R_G value so the number is checkable: G = 1 + 49.4 k/R_G ⟹ R_G = 49.4 k/1.39 = **35.5 kΩ**
(nearest E96: 35.7 kΩ → G = 2.384).

**Confidence: very high (0.95)** on the contradiction; **medium-high (0.8)** on the
14 dB figure, which depends on the 25 kΩ INA134 value I am recalling from memory —
though it self-validates against the two figures ADR 0003 quotes.

**Falsifying measurement.** None needed for the contradiction. For the CMRR figure: at
E10, drive both in-amp inputs from a common source through the real 10 kΩ, inject
100 mV p-p at 100 Hz, measure the output.

---

## 4. "Band-limit at both ends, around 500 Hz" is unspecified as to balance — a single-ended filter capacitor at the module throws away the entire CMRR the in-amp was bought for

**MAJOR**

**Where.** ADR 0003: *"**Band-limit at both ends, around 500 Hz.** The sensor only has
~159 Hz of real bandwidth, so a narrow channel costs nothing and rejects almost
everything that could couple in."* Nothing anywhere states whether the module-end
capacitor is differential (BREATH–AGND) or single-ended (BREATH–module ground). The
BOM has no line item for it at all.

**Why.** The obvious implementation — a capacitor from the BREATH input to module
analog ground, forming 500 Hz against the instrument's 10 kΩ — is a common-mode-to-
differential-mode converter. With the 10 kΩ series source, the 100 kΩ differential
pulldown and C = 32 nF:

```
V_diff / V_cm  =  sC / (1/10k + 1/100k + sC)
```

| Frequency | CM→DM conversion | Effective CMRR | Error at the jack from 40 mV of in-band CM |
|---|---|---|---|
| 100 Hz | 0.180 | **14.9 dB** | 7.2 mV × 2.39 = **17 mV** (0.17 % FS) |
| 500 Hz | 0.675 | **3.4 dB** | 65 mV (0.65 % FS) |
| 2 kHz (WS2815 PWM) | 0.965 | **0.3 dB** | 15 mV CM → 14.5 mV × 2.39 = **35 mV** (0.35 % FS), a tone |

An INA821 at ≥92 dB is irrelevant in the face of this: the imbalance is upstream of
the amplifier and the amplifier cannot recover it. **This one component choice is
worth 75–90 dB**, which is more than every other decision in the link combined, and it
is the only term in the whole budget large enough to be heard.

It is also the mirror image of the mistake ADR 0003 *did* catch — *"Put the pulldown
**differentially across BREATH–AGND**, not on one leg"* — applied to the resistor but
never to the capacitor.

**Proposal.** Collapse the two filters into one balanced pole and write it into the BOM:

- Keep the **10 kΩ series protection at the buffer output** in the instrument.
- Put the **only** capacitor as **33 nF C0G or film across BREATH–AGND at the module**
  (f = 1/(2π·10 k·33 n) = **482 Hz**). This is inherently balanced, it re-uses the
  protection resistor, and it is one part.
- **No capacitor from either input to module ground.** If a common-mode HF shunt is
  ever wanted, the standard rule applies: C_diff ≥ 10 × C_cm, and the two C_cm must be
  a matched pair.
- Delete the instrument-end pole entirely (see Finding 8 — it costs 318 µs and buys
  nothing the module-end pole does not).

**Confidence: high (0.85)** that the filter is underspecified and that the naive
implementation is the one that would be built; **very high (0.95)** on the arithmetic
given that implementation.

**Falsifying measurement.** At E11, with the real cable: inject 200 mV p-p at 100 Hz
and 2 kHz between the instrument's analog star point and module ground (a signal
generator in series with the PWR_GND conductor is the clean way), and measure the
breath jack. Achieved CMRR below ~40 dB at 100 Hz indicts the input network; above
~70 dB exonerates it.

---

## 5. The module end of the analog pair has no series resistance and no clamp, and on hot-plug AGND can briefly be the instrument's only current return

**MAJOR**

**Where.** ADR 0003 puts the protection at the instrument end only: *"the instrument
end needs **only a buffer** — an op-amp follower, band-limited, with a series resistor
for protection."* The module's protective parts (ADR 0006, *"Small protective parts on
the module"*) cover the DAC-to-op-amp inputs and the CV jacks, and `U-TVS-UMB` sits at
the **instrument** umbilical entry. **Nothing protects the module's umbilical entry.**

**Why.** Two distinct exposures:

*Hot-plug / partial insertion.* An RJ45's eight contacts wipe in with mechanical
tolerance and bounce. If `+12 V` makes contact while `PWR_GND` and `DIG_GND` are
bouncing, the instrument's inrush seeks whatever return is available — and `AGND` is a
candidate, because at the instrument end it is bonded to the analog star point, which
is bonded to instrument ground. The current is bounded only by the TPS2553's limit,
set *"~500 mA"* per the BOM. **500 mA into an in-amp input pin destroys it.** ADR 0004
notes plugging is routine (*"the instrument moves constantly while being played"*) and
the ROADMAP's E6 line explicitly calls for *"inrush … on switch-on **and hot-plug**"*.

*Cable fault.* The design calls the cable a consumable that will fail. A crushed pair
shorting BREATH to +12 V is handled correctly at the instrument end (Finding "correct"
#2 below) but at the module end it puts +12 V directly on an in-amp input with no
series resistance, at or beyond the input common-mode range on ±12 V rails.

The irony is that the design already bought exactly the property that makes the fix
free: *"**A buffered-input in-amp dissolves that conflict entirely** — gigaohm inputs
make source impedance irrelevant, so protection resistors can be 10 kΩ and unmatched
with no CMRR penalty."* That argument applies at the module end too, and the module
end is where the external cable actually is.

**Proposal.**

- **10 kΩ 1 % in series in *each* leg at the module end**, BREATH and AGND. Matching
  them to each other is what Finding 1 needs anyway; 1 % parts give 200 Ω of mismatch
  and a 74 dB CMRR floor against the 1 MΩ bias pair. Fault current becomes
  (12 − 0.7)/10 k = **1.1 mA**.
- **BAV99 (silicon, not Schottky — same reasoning as `D-JACK-CLAMP`) from each input
  to the ±12 V rails.** Leakage through 10 kΩ at BAV99 levels is sub-microvolt.
- Note this also symmetrises the instrument-end 10 kΩ: BREATH leg = 20 kΩ, AGND leg =
  10 kΩ is a 10 kΩ imbalance and a 40 dB CMRR cap. **So either put a matching 10 kΩ in
  the AGND leg at the instrument end too** (it carries ~70 nA and its drop cancels in
  the matched arm), **or** drop the module-end BREATH resistor to 1 kΩ and accept a
  1 kΩ imbalance → 20·log₁₀(1 M/1 k) = 60 dB, which still meets ADR 0003's own
  requirement. My preference is the first: full symmetry, 74 dB, and the cheapest
  possible analysis.

**Confidence: medium-high (0.8)** on the hot-plug path (it depends on contact-timing
details I cannot measure from here, and DIG_GND makes a simultaneous ground contact
likely); **high (0.9)** that the module's umbilical entry being unprotected is a real
gap given that the instrument's is protected and the module's is the end with the
precision part on it.

**Falsifying measurement.** At E6, with a current probe on the AGND conductor,
hot-plug the umbilical thirty times with the toggle on and capture peak current. Any
excursion above a few mA in AGND confirms the path. Also: pull the plug halfway and
rock it.

---

## 6. The 10 kΩ / 100 kΩ divider is an unaccounted 9.1 % gain error, and it is the largest link-side term in the budget

**MINOR**

**Where.** `hardware/bom.csv`, `R-PD-BREATH`: *"100k … DIFFERENTIAL across
BREATH-AGND"*, against ADR 0003's *"protection resistors can be **10 kΩ**"* and its
*"absorbs the ~2.13× scaling stage"*.

**Why.** 100 k/(100 k + 10 k) = **0.9091**. Consequences:

- The fixed gain is 2.39, not 2.13 — a 12 % error in the design's stated figure.
- Tolerance: with 1 % parts, ∂(ratio)/ratio ≈ 0.0909 × 1 % per resistor, RSS
  **0.13 % = 13 mV at the jack**. Absorbed by the gain knob, so harmless — but it is
  three orders of magnitude larger than every common-mode term and nobody wrote it down.
- Tempco: two 0805 thick-film parts at ±100 ppm/K drifting oppositely over a 15 K rack
  warm-up: 0.0909 × 200 ppm/K × 15 K = 273 ppm = **2.7 mV**. Not absorbed by anything,
  because nothing re-calibrates the breath channel. This is **20× the total
  common-mode error** the ADR spends its longest section on.

**Proposal.** Make the differential element **1 MΩ** (or delete it in favour of the
2 × 1 MΩ common-mode pair of Finding 1, which gives 2 MΩ differentially). Divider
becomes 0.990; tolerance contribution falls to 0.014 % (1.4 mV) and tempco to 0.3 mV.
Specify the resistors as **metal film, ≤50 ppm/K**, which costs nothing. Then set
G = 10/(4.6 × 0.990) = **2.20**, R_G = 49.4 k/1.20 = **41.2 kΩ** (E96 exact).

**Confidence: very high (0.95)** on the arithmetic. The divider exists as specified.

**Falsifying measurement.** At E10, apply a known DC to the instrument-end buffer
output (or substitute a bench supply behind the real 10 kΩ) and measure the ratio at
the in-amp inputs with the module's pulldown fitted. It should read 0.909 with 100 kΩ.

---

## 7. The REF pin's drive impedance is an unstated hard cap on CMRR, and the natural place to put the DAC's reconstruction filter is the place that destroys it

**MINOR** (but it interacts with Finding 2's fix, so decide them together)

**Where.** ADR 0003: *"its **REF pin is the natural injection point** for the firmware
ambient-zero, driven from a low-impedance buffer rather than a divider."* Correct as
far as it goes, and then it stops.

**Why.** In a three-op-amp in-amp the REF pin enters the output difference amp through
one of its internal resistors, so *any* series impedance at REF is a resistor mismatch
in that difference amp and caps CMRR directly. With R_internal ≈ 10 kΩ (**from
memory** — this whole table scales linearly with that value):

| REF source impedance | CMRR cap |
|---|---|
| 0.1 Ω (op-amp output, direct) | 106 dB |
| **1 Ω** | **86 dB** |
| 10 Ω | 66 dB |
| 100 Ω (a series "isolation" resistor someone adds for stability) | 46 dB |

A DAC output almost always gets a reconstruction RC. Put a 1 kΩ + 100 nF on the REF
pin — an entirely reasonable-looking thing to draw — and the link's CMRR drops to
26 dB, below what a difference amp would have given.

**Proposal.** Two lines in ADR 0003 and one in the BOM: *the REF pin is driven
directly from an op-amp output with no series element of any kind; any filtering of
DAC channel 6 goes **before** that op-amp or **inside its feedback loop**, never
between its output and REF.* If the inverting stage of Finding 2 is adopted, a
feedback capacitor across R2 does the filtering with zero output impedance, which is
the right answer anyway.

Also: check the op-amp count. I counted 10–11 OPA2197 halves needed in the module
(pitch scale, pitch buffer/filter, mod ×4, mod 2.5 V offset buffer, breath REF driver,
breath gain stage, breath offset summer, breath output buffer) against `U-OPA-PITCH`
qty 5 = 10 halves. It is tight to one short.

**Confidence: medium (0.7)** — high on the mechanism, medium on the 10 kΩ internal
value and therefore on the exact dB figures. Verify against the INA821/INA828
datasheet's own "REF pin" application note before quoting the table.

**Falsifying measurement.** At E10, deliberately insert 100 Ω in series with REF and
repeat the CMRR injection test of Finding 4. If CMRR does not degrade by ~40 dB, the
internal resistor value I assumed is wrong.

---

## 8. The latency line for the analog link is understated 3× by its own filter decision

**MINOR**

**Where.** `docs/reference/latency-budget.md`: *"Buffer, cable, in-amp, output filter |
**< 0.2 ms** | Propagation plus filter group delay only"*, total **~2.4 ms**. Against
ADR 0003's *"Band-limit at both ends, around 500 Hz."*

**Why.** A single-pole 500 Hz filter has DC group delay 1/(2π × 500) = **318 µs**. Two
of them — which is what "both ends" means — is **637 µs**. Cable propagation is ~10 ns
and irrelevant. So the line is ~0.65 ms, not <0.2 ms, and the analog breath total is
**~2.8 ms**, not 2.4 ms.

Still comfortably inside the 5 ms target, so this is a bookkeeping error rather than a
design error — but the budget document's own stated purpose is that it is *"the thing
most likely to be violated accidentally by a change that looks harmless — … a filter
corner set too low"*, and this is that change, already made.

**Proposal.** Adopt the single-pole recommendation of Finding 4 (one 482 Hz pole at
the module, 330 µs) and correct the table to 0.35 ms / 2.5 ms total. If both poles are
kept for some reason, write 0.65 ms.

**Confidence: very high (0.95).** Arithmetic only.

**Falsifying measurement.** The latency budget already schedules it: *"End-to-end, in
one shot — two scope channels: one on the sensor output, one on the CV jack."* Step
the pressure and read the delay difference between sensor output and jack; it should be
~330 µs for one pole, ~640 µs for two.

---

## 9. Pin 3 should be PWR_GND, not +12 V — the "guard" conductor nearest the analog pair is the noisiest in the cable

**MINOR**

**Where.** ADR 0004: *"**The power pair's two DC conductors sit between the analog pair
and both digital pairs, acting as a guard.** BREATH at pin 1 is adjacent only to its
own sense return."* Table assigns pins 3,6 = `+12V / PWR_GND` without saying which is
which.

**Why.** The pin-1 placement of BREATH is genuinely good and I want to credit it: in
the ~13 mm untwist region inside the plug, pin 1 is at the edge of the row and its only
neighbour is pin 2, its own return. That is the right conductor to put at the edge.

But the *adjacent* conductor to the pair is pin 3, and as written that is `+12 V` — the
one conductor carrying the WS2815 PWM current with fast edges, and the one whose
voltage actually moves (250 mA through ~0.44 Ω of loop = ~110 mV at 2 kHz with
sub-microsecond edges). `PWR_GND` moves by the return drop only and is the quieter of
the two. Worse, (3,6) is T568B's **split pair**: its two conductors fan around pins 4
and 5, giving it the longest untwisted run and the largest loop area in the connector —
so it is the biggest radiator in the plug, sitting next to the analog pair.

Estimated magnetic injection into the BREATH–AGND loop over 13 mm of adjacency, at
~5–10 nH of mutual inductance and a WS2815 edge of 250 mA in ~100 ns:
V = 10 nH × 2.5×10⁶ A/s ≈ **25 mV spikes**. The 482 Hz differential filter integrates
these to ~8 nV each, so they are harmless **provided Finding 4 is fixed** — which is a
second, independent reason the filter has to be differential.

**Proposal.** One line in the ADR 0004 table: **pin 3 = `PWR_GND`, pin 6 = `+12 V`.**
Free, and it moves the loudest conductor two positions further from the analog pair.
Also add to `CABLE-UMB`: **24 AWG stranded**, not just "stranded" — the difference
between 24 and 28 AWG is a factor of 2.5 on V_cm and on the +12 V drop.

**Confidence: medium (0.65)** — the polarity swap is unambiguously an improvement, but
the injection estimate is a bounding calculation with a mutual inductance I have not
measured.

**Falsifying measurement.** E11 already exists for this. Scope the breath jack
differentially with the LED strips running an animation, first with pin 3 = +12 V and
then with the assignment swapped (a crossover adapter makes this a two-minute test).

---

## 10. Shield termination is unspecified, and the natural build bonds it at both ends

**NIT**

**Where.** ADR 0004: *"**Shielded (STP/FTP) preferred.** … the shield is free at this
price."* No termination stated. ADR 0009 bonds the instrument's aluminium plate to
`PWR_GND`; a chassis etherCON's shell bonds to whatever it is mounted to at both ends.

**Why.** Bonded at both ends, the shield becomes a third parallel power return. That
*reduces* V_cm (good) but routes an estimated 20–25 % of the instrument's return
current — ~100 mA — through the module panel, the rack rails and every other module's
panel-to-jack-sleeve bond. Rack rail resistance is milliohms, so the resulting
inter-module offsets are well under 1 mV and nothing audible follows; but it makes the
breath channel's reference depend on how tightly the rack screws are done up, which is
an unpleasant thing not to have decided.

**Proposal.** State it: **shield bonded to the module panel/chassis at the module end;
at the instrument end bonded to `PWR_GND` (never `AGND`)**, consistent with ADR 0009's
plate rule, *or* left floating and capacitively coupled — but pick one and write it in
`CABLE-UMB`. Also note `U-TVS-UMB` is an **SP3012-06UTG, a 6-channel array, for 8
conductors**. Two conductors go unprotected and the BOM does not say which. If the
answer is "the analog pair", that is exactly backwards.

**Confidence: high (0.85)** that it is unspecified; **low-medium (0.5)** that the
consequences matter at all in this build. It is cheap to close.

**Falsifying measurement.** Clamp-meter or current probe around the assembled cable
with the instrument running: net current ≠ 0 means the shield is carrying return.

---

# Where the design is right

These are not filler. Several are decisions I would have flagged if they had gone the
other way, and three of them I checked arithmetically and found correct.

1. **The sense-return concept itself.** Giving the analog signal a return that carries
   no power current, and sensing against it, is the correct fix and the analogy to a
   Eurorack patch cable is exactly right. The static budget under-sells it — a 70 mV DC
   error would calibrate out — but the real justification is dynamic: without AGND the
   error is ~167 mV *correlated with the light show and the radio*, and that is audible
   where a static 167 mV would not be. ADR 0003 gets to the right answer; I would just
   state the reason as "correlated, not large".

2. **Moving the buffer to +12 V to dissolve the protection/CMRR conflict.** The
   arithmetic checks: (12 − 5 − 0.7)/1 k = 6.3 mA against a ~2 mA clamp rating; ≥3.3 kΩ
   gives (12 − 5.7)/3.3 k = 1.9 mA. And the conclusion — that a +12 V fault against a
   +12 V rail sources no clamp current at all — is correct and elegant. This is the
   best single decision in the link.

3. **Rejecting the difference amp for a buffered-input in-amp.** The source-impedance-
   balance argument is right, and ADR 0003's quoted figures reproduce exactly from
   first principles (74 dB at 10 Ω, ~24 dB at 3.3 kΩ, 19 dB for a 100 kΩ single-leg
   shunt). Someone did this arithmetic properly. My Findings 1 and 5 are about what
   the buffered inputs do **not** excuse, not about the choice.

4. **The ratiometric-supply decision.** Putting the MPXV4006DP on a REF5050 rather
   than the shared buck is the highest-value analog decision in the instrument, and
   ADR 0003's observation that it is ~30 dB worse than the common-mode path it had been
   agonising over is correct and honest. My budget agrees: REF5050 at 3 ppm/°C over
   15 K contributes 0.5 mV at the jack, versus 104 mV for a 2 % rail excursion.

5. **BREATH at pin 1 of the RJ45.** Edge of the row, adjacent only to its own return
   through the untwist region. Correct, and the reasoning about where crosstalk actually
   happens (in the 13 mm fan-out, not in the twisted run) is the right model.

6. **The open-BREATH failure mode.** With the differential pulldown, a broken BREATH
   conductor gives 0 V at the jack. That is the graceful direction and it is correct.
   (The broken-**AGND** case is Finding 1.)

7. **Not going fully differential.** The 6 dB argument is right, and at 160 Hz of
   signal bandwidth over 2 m a driver would be pure cost.

8. **One thing the documents are more pessimistic about than they need to be:**
   ADR 0014's light-show feedback loop through the CV path — *"more breath → brighter
   LEDs → `AGND` rises → the CV reads lower … 0.4 % of gain compression"* — computes
   34 mV/10 V, i.e. it assumes **zero** common-mode rejection. With the in-amp in place
   and the input network balanced, that 34 mV is rejected by ~90 dB and the compression
   is 1 part in 10⁷. **The CV-path half of that loop does not exist.** The ADC-path
   half (note-gate chatter) is real and its two fixes are good.

---

# The error budget at the jack

Full scale 10 V. Assumes Findings 1, 2, 4 and 5 are fixed; where a finding is *not*
fixed, its row is called out separately at the bottom.

| Term | mV at jack | % FS | Character |
|---|---|---|---|
| **Sensor accuracy, ±2.46 % VFSS over 10–60 °C, with working auto-zero** *(verified datasheet)* | **±270** | **2.70 %** | slow, partly calibratable |
| In-amp gain error + R_G tolerance (1 %) | ±60 | 0.60 % | fixed, absorbed by the gain knob |
| 10 k/100 k divider tolerance (1 %) | ±13 | 0.13 % | fixed, absorbed by the gain knob |
| Auto-zero residual: ADC branch is open-loop through a 3.3 V dev-board reference (±2 %) and a 1 % divider | ±12 | 0.12 % | slow |
| 10 k/100 k divider tempco, 2 × 100 ppm/K over 15 K | ±2.7 | 0.027 % | **drift, uncorrected** |
| REF5050 3 ppm/°C over 15 K (ratiometric) | ±0.5 | 0.005 % | drift |
| In-amp Vos, 35 µV RTI + ~300 µV RTO/G *(RTO from memory)* | ±0.4 | 0.004 % | fixed |
| Local AGND copper: 10 mA sensor supply return × 10 mΩ of shared pour | ±0.24 | 0.002 % | layout-dependent |
| In-amp drift over 15 K | ±0.1 | 0.001 % | drift |
| DAC ch 6 REF resolution (1 LSB) | ±0.08 | 0.0008 % | quantisation |
| REF5050 line regulation, 5 ppm/V × 1 V on +12 V | ±0.06 | 0.0006 % | dynamic |
| **Common-mode rejection: 40 mV in-band at ~90 dB** | **±0.003** | **0.00003 %** | dynamic |

**Which term dominates: the sensor, by a factor of 4 over the next term and by five
orders of magnitude over the common-mode path.** The link that ADR 0003 spends its
longest section defending contributes **3 microvolts**, and the second-largest
link-side term is a resistor divider the documents do not mention.

That is not an argument for doing less — it is an argument that the link is *already*
over-designed relative to what it feeds, and that the remaining risk is in the three
things the documents leave unspecified (bias return, filter balance, REF polarity)
rather than in anything they decided.

**If the findings are not fixed, the same table looks like this:**

| Unfixed finding | mV at jack | % FS |
|---|---|---|
| **F2** — auto-zero cannot subtract: fixed pedestal, Voff 0.152–0.378 V × G | **+360 to +900** | **3.6–9.0 %** |
| **F2** — and sensor accuracy degrades from ±2.46 % to ±5.0 % VFSS | ±550 | 5.5 % |
| **F4** — single-ended filter cap: 40 mV in-band CM at 14.9 dB | ±17, breath-correlated | 0.17 % |
| **F4** — 15 mV of 2 kHz CM at 0.3 dB | ±35, a tone | 0.35 % |
| **F3** — INA134 instead of the in-amp | ±19, animation-correlated | 0.19 % |
| **F1** — cable unplugged | ~+11 000 | rail |

---

# What CMRR is genuinely achieved

| Reading of the documents | Achieved CMRR in-band | Meets the 60 dB ADR 0003 requires? |
|---|---|---|
| ADR 0004 as written (INA134 + 10 kΩ) | **14 dB** | no |
| ADR 0003/BOM (INA821) + single-ended 500 Hz cap at the module | **15 dB @ 100 Hz, 0.3 dB @ 2 kHz** | no |
| ADR 0003/BOM + differential cap + CM bias added naively (unmatched series R) | **40 dB** | no |
| ADR 0003/BOM + differential cap + symmetrised series R + 1 MΩ bias pair + REF from an op-amp output | **74 dB** (bias/series limited) to **92 dB** (part limited) | **yes, with 14–32 dB of margin** |

**Three of the four plausible builds fail the design's own requirement.** The fourth
comfortably exceeds it and costs four resistors and one capacitor more than the third.
That gap — between a scheme that is right in principle and a scheme that is specified
completely enough to be built right — is the whole of this review.

---

# Behaviour on disconnection, power-down and cable fault

| Condition | As specified today | With Findings 1 and 5 fixed |
|---|---|---|
| Cable plugged, module toggle off (the *normal* idle state per ADR 0004) | Instrument grounds still continuous through PWR_GND, so AGND is referenced; 100 kΩ holds BREATH at AGND; buffer unpowered. **0 V. Correct.** | 0 V |
| **Cable unplugged** | Both inputs float at 15 V/s; in-amp saturates within ~1 s. **Rail, indefinitely.** | 0 V |
| **AGND conductor open** (consumable cable, as designed to fail) | Same as unplugged. **Rail.** | Falls back to sensing against module ground: ~167 mV of light-show-correlated error. Degraded but playable, and diagnosable |
| BREATH conductor open | 100 kΩ holds BREATH at AGND. **0 V. Correct.** | 0 V |
| BREATH shorted to PWR_GND | 0 V. Correct. | 0 V |
| **BREATH shorted to +12 V** | No fault current in the instrument (correct, and well reasoned). At the module the input CM is at the positive rail: in-amp saturates. **Full-scale drone, no damage.** | Unchanged — 10 kΩ + BAV99 prevents damage but not saturation. **Accept and document**, or extend the DAC `CLR` watchdog concept to mute breath when the in-amp saturates |
| Hot-plug with the toggle on | Up to the ~500 mA load-switch limit can transit an in-amp input pin | 1.1 mA, clamped |
| Instrument on USB with the cable connected (bench case) | Mains-leakage ground loop adds ~80 µV of 50 Hz CM — rejected. Harmless. | Harmless |

The two rows in bold are the ones worth acting on. The rest of this table is a credit
to the design: most of the fault space already lands on 0 V, which is the right answer.

---

# Summary of recommended changes

| # | Change | Cost |
|---|---|---|
| 1 | 2 × 1 MΩ from each in-amp input to module analog ground; delete the 100 kΩ differential pulldown | 2 R |
| 2 | Invert DAC ch 6 through a ±12 V op-amp stage, 0 → −0.9 V, into REF | 1 op-amp half + 2 R (op-amp half already needed as the buffer) |
| 3 | Delete the INA134 paragraph from ADR 0004; correct "2.13×" to 2.20× and state R_G = 41.2 kΩ | doc only |
| 4 | The 500 Hz pole is **one** 33 nF across BREATH–AGND at the module; no cap to module ground anywhere | 1 C, −1 C |
| 5 | 10 kΩ 1 % in each leg at the module end + BAV99 to the rails; matching 10 kΩ in the AGND leg at the instrument end | 4 R, 2 D |
| 6 | Metal-film ≤50 ppm/K for the two resistors that set the divider | none |
| 7 | Rule: nothing in series with REF; DAC filtering before or inside the buffer | doc only |
| 8 | Correct the latency budget's analog line to 0.35 ms / 2.5 ms | doc only |
| 9 | Pin 3 = PWR_GND, pin 6 = +12 V; `CABLE-UMB` specifies **24 AWG** stranded | doc only |
| 10 | State shield termination; resolve the 6-channel TVS array against 8 conductors | doc + 1 part |

Everything above is pre-layout and costs about a dollar. Nine of the ten are one line
in a document or one passive on a board that has not been drawn yet; none of them
requires a topology change, because **the topology is right.**
