# R2 — How published Eurorack modules turn a unipolar DAC into bipolar CV

**Date:** 2026-09-21 · **Subject:** `hardware/module/mod-channels.md`, ADR 0006 mod channels 1–4
**Scope:** the mod stage only. Pitch and breath appear where they share the mechanism.

Provenance markers are strict. `[schematic]` means I opened the file named in
[Sources](#sources-opened-in-this-session) in this session. `[source]` means firmware I read.
`[BOM]` means a manufacturer's own parts list. `[docs]` means a manual or datasheet-like
document. `[from memory]` means I did not open a source and the claim is only as good as
recall. Several vendor sites were **blocked by the egress proxy** — see
[What I could not check](#what-i-could-not-check).

---

## Findings vs Woody — the short table

| # | What published modules do | What Woody does | Verdict |
|---|---|---|---|
| 1 | **Single inverting amp**, gain −4…−5, mid-reference into the **(+) input**. Four of four designs opened. `[schematic]` | Four-resistor difference amp, DAC into the (+) leg | **Differs.** Woody's own note says `A = 1 + B` fails at A=4 — true, but only because it insists on *non-inverting*. Inverting reaches gain 4 with two resistors and gets the offset injection for free |
| 2 | Offset = **passive divider off the DAC's own `VREFOUT`**, straight into the (+) input. No buffer, no DAC channel. Ornament & Crime (DAC8565) and Westlicht Performer (DAC8568C) `[schematic]` | Buffered DAC channel 7 + `R-OPAMP-IN` + ½ OPA2197 | **Woody reinvents.** The divider gets the same "both terms die together at power-on" property for 2 resistors. Woody's version buys *only* the CLR case — and the Performer disables CLR entirely (`setClearCode(ClearIgnore)` + `CLR` pin strapped high) `[source][schematic]` |
| 3 | Everyone ships a **10 V span**: 0–8, 0–10, ±5, −3…+7, ±6. Max magnitude 10 V, never ±10 `[docs][schematic]` | ±10 V, 20 V span | **Unusual.** No module I opened asks its op-amp for both +10 and −10. O_C's VOR moves a 10 V window instead of widening it |
| 4 | **1 % 0402/0603 discretes everywhere**, including on 1 V/oct channels; accuracy comes from a per-channel calibration table `[BOM][source]` | 1 % 0805 discretes, no per-channel calibration for mods | **Right on parts, wrong on firmware.** Every module opened calibrates *every* channel, because any channel may carry pitch |
| 5 | Gain set loosely, **range clamped in firmware**. Performer's hardware could do −15.7 V; firmware limits codes to `0x7FFF` `[source]` | E96 value chosen so the jack lands on exactly ±10.05 V | **Differs.** And ±10.05 V contradicts ADR 0006's own "the DAC cannot reach its rails" window |
| 6 | The **gain-setting input resistor (24 k–47 k) is the only** clamp-current limit; no dedicated series part anywhere `[schematic]` | Extra 1 kΩ `R-OPAMP-IN` **inside the gain network** | **Bug, not a preference.** Costs 196 mV of zero error and 0.39 V of span — 2.4× the entire 1 % tolerance budget the page computes |

Two of these are defects with numbers attached (rows 6 and, in a smaller way, 4).
The rest are judgement calls where a one-off may legitimately differ, and I say which.

---

## 1. Topology: what people actually build

Four designs, opened this session, all the same shape:

| Module | DAC | Amp | Rin / Rf | Gain | Mid-ref | Range |
|---|---|---|---|---|---|---|
| **Ornament & Crime** rev2e | DAC8565, AVDD 3.3 V | OPA2172 | 24k9 / 100k | −4.016 | `V_bias` = `VREF_OUT` ÷2 (47k/47k) → **(+) input** | −3…+6 V |
| **Westlicht PER\|FORMER** | **DAC8568C**, AVDD 3.3 V | OPA4172 | 24k / 100k | −4.167 | `VBIAS` = `VREF` ×22/(33+22) = 1.0 V → **(+) input** | ±5 V |
| **Mutable Yarns** v0.3 | DAC8564 | OPA4171 | 47k / 240k | −5.106 | `VREF/2` (47k/47k) → **(+) input** | −3…+7 V |
| **MTM Workshop Computer** r1.0.0 | PWM | TL074-HIPWR | 75k / 270k (MFB) | −3.6 | **−5 V reference** via 226k into the summing node | ±6 V |
| **Befaco Midi Thing** V1 | — | TL072 | 47k / 68k | −1.45 | (source off-crop) | — |

`[schematic]` for all rows: O\_C from `o_c_rev2e_schematic.pdf` (I extracted its text *and*
read the rendered output-stage crop, and the two agree on 24k9/100k/220R/22p/47k/`V_bias`);
Performer from `dac.sch` + `sequencer.net` (I traced the netlist node by node);
Yarns from the TOILmodular redraw `toil_yarns.pdf` cross-checked against Mutable's own
`Yarns.xlsx` `[BOM]` (6×47k + 4×240k = 4 channel inputs + one 2-resistor divider, exactly
the redraw); Workshop Computer from the rendered `computer_Rev_1_0_0_Schematic.pdf` page.

**So: answer (a) "four-resistor difference amp" is not what anyone does. Answer (b)
"inverting summer" is, in two variants** — reference into the (+) input (O\_C, Performer,
Yarns) or a negative reference into the summing node (Workshop Computer). I found **no**
published example of Woody's arrangement, a non-inverting difference amp with the DAC on
the (+) leg. Answer (c), a DAC with a native bipolar output (AD5754/AD5764, ±10 V,
software-selectable span) exists and *is* used in Eurorack — `newdigate/teensy-eurorack`
uses 2× AD5754 for 8× ±10 V outputs — but I did not open that design `[from memory, via
web search]`.

### Why the inverting form keeps winning, and why it matters to Woody

Three reasons, all of which apply to the mod stage:

1. **The offset injection is free.** The (+) input draws no current, so the mid-reference
   can be an unbuffered resistor divider. Woody's difference amp makes the reference drive
   a resistor network, which is the entire reason it needs `½ OPA2197` + `R-OPAMP-IN` +
   a dedicated DAC channel. That cost is a consequence of the topology choice, not of the
   requirement.
2. **There is only one ratio to get right.** In `Vout = −k·Vdac + (1+k)·V+`, gain and
   intercept both fall out of the *same* `k = Rf/Rin`. A four-resistor difference amp has
   two independent ratios, and their mismatch is a distinct error term that does not exist
   in the inverting form (see §4).
3. **No common-mode swing.** The inverting node sits pinned at `V+` (1.0–1.25 V in the
   designs above) for all signals, so op-amp CMRR and input-stage nonlinearity contribute
   nothing. In Woody's difference amp the (+) input swings 0→3.93 V with the signal.

`mod-channels.md` says the mods "need A = 4 and B = 4, and `A = 1 + B` would require B = 3.
So the reference has to enter through its own input." That is correct *given* a
non-inverting stage. It is not correct in general — the constraint `A ≤ 1+B` is an artefact
of insisting on positive gain. Inverting, `A` and `B` are independent: `A = Rf/Rin`,
`B = (1+A)·(divider ratio)`. The published gain-of-4 stages are exactly this.

---

## 2. Where the mid-scale offset comes from — the important finding

**Two published modules, both using this exact TI DAC family, take the offset from the
DAC's own reference output through a passive divider.** `[schematic]`

- **Ornament & Crime rev2e**: `DAC8565` pin 3 `VREF_OUT` → net `VREF_2v5` → 47k/47k divider
  → `V_bias` = 1.25 V, decoupled with 100 nF → the (+) input of all four OPA2172 halves.
- **Westlicht PER|FORMER**: `DAC8568C` pin 8 `VREF` → 33k/22k → `VBIAS` = 1.0 V (netlist
  net `/DAC/VBIAS`), decoupled by `C25`, → the (+) inputs of **all eight** op-amp channels
  (`U4.3, U4.5, U4.10, U4.12, U15.3, U15.5, U15.10, U15.12`). No buffer. No DAC channel.

This matters because **it has the same power-on property Woody spent a DAC channel to get.**
At rack power-on the DAC8568C's internal reference is off, so `VREFOUT ≈ 0`, so `VBIAS ≈ 0`,
so every output is `−4.167 × 0 = 0 V`. Both terms die together, for the same reason Woody's
do: they come from the same reference. Two resistors, not a channel plus an op-amp half plus
a series resistor.

**Where Woody's version is genuinely stronger, and where it is not:**

- On a **runtime `CLR`**, the divider version does *not* collapse — `VREFOUT` is still alive,
  so the outputs go to the positive end of range. Woody's does collapse. That is a real
  difference and Woody's mechanism wins it.
- But **the Performer does not use `CLR` at all**: `~CLR` (pin 9) is strapped to `+3.3VA`
  in hardware `[schematic, sequencer.net]` *and* firmware writes
  `setClearCode(ClearIgnore)` at init `[source, Dac.cpp]`. Belt and braces. The failure
  Woody designed around is one that published practice removes by declining the feature.
- And the failure is **less severe in the inverting form anyway**. A stuck offset on an
  inverting stage drives the outputs to the *top* of their normal range (+6.3 V on O\_C,
  +5.17 V on the Performer) — an in-range CV. On Woody's non-inverting stage a stuck offset
  drives −10.05 V, which is out of range for the receiving module rather than merely wrong.

**Correction to a datasheet claim in ADR 0006.** The ADR says "On a watchdog `CLR`, an
A/C-grade DAC8568 clears **every** channel to zero scale (ADR 0006)". The Performer's driver
shows `CLR` behaviour is a **software-loaded register**, not a grade property:

```c
enum ClearCode { ClearZeroScale=0, ClearMidScale=1, ClearFullScale=2, ClearIgnore=3 };
#define LOAD_CLEAR_CODE_REGISTER 5
```
`[source: perf-fw/src/platform/stm32/drivers/Dac.cpp]`

Grade sets the **power-on reset** value; the clear-code register sets what the `CLR` *pin*
does, and it has four settings including "ignore". ADR 0006 conflates the two. I could not
open the DAC8568 datasheet to state the register's default — **ti.com is blocked** — so
treat this as "the ADR's sentence is not supported by the one primary-ish source I could
read, and needs a datasheet check", not as a proven error.

**A second grade trap the Performer hit, which Woody's BOM is exposed to.** `U-DAC` reads
*"DAC8568C (or A grade)"* and treats them as interchangeable. The Performer's firmware
carries a persistent hardware-config byte specifically to support A-grade parts, because
the SPI data field is **shifted by one bit** between them:

```c
case Type::DAC8568C: _dataShift = 0; break;
case Type::DAC8568A: _dataShift = 1; break;
```
`[source: Dac.cpp, Dac.h, HardwareConfig.h; CHANGELOG: "Added a hwconfig to support DAC8568A
(in addition to the default DAC8568C)"]`

A shipped project added a config option and a flash page rather than call A and C
interchangeable. If Woody's firmware is written against a C part and an A part is fitted,
every output lands at half (or twice) the commanded voltage. ADR 0006 is already emphatic
that "the grade letter is the whole decision" — it should say *which single grade*, not
"A or C".

---

## 3. What ranges people actually ship

Everything I could verify, from manuals and firmware rather than marketing:

| Module | Output range | Source |
|---|---|---|
| Mutable **Yarns** | **−3 V to +7 V**, calibrated at 11 points, one per volt | `[docs]` manual §Calibration; `[source]` `kNumOctaves = 11`, `voice.cc` |
| Mutable **Marbles** | **−5 V to +5 V** CVs, 0…+8 V gates | `[docs]` `marbles/index.md`; `[source]` `CONSTRAIN(voltage,-5,5)` |
| Mutable **Stages** | 0 V…+8 V (to −8 V only under CV modulation) | `[docs]` `stages/index.md` |
| Mutable **Peaks** | 0…+8 V envelopes, 10 Vpp LFOs | `[docs]` `peaks/index.md` |
| Mutable **Tides** | ±5 V on BI, 0…+8 V elsewhere | `[docs]` `tides_original/index.md` |
| **Ornament & Crime** stock | −3 V…+6 V | `[schematic]` + `[source]` |
| **O\_C "VOR"** (Plum Audio) | switchable **0→10 V**, **−3→+7 V**, **−5→+5 V** | `[source]` `VBiasManager.h` popup text and bias constants |
| **PER\|FORMER** | **±5 V** (`MinVoltage=-5, MaxVoltage=5`) | `[source]` `Calibration.h` |
| **Workshop Computer** | ±6 V | `[schematic]` (derived from 270k/75k and the −5 V ref) |
| **Befaco Midi Thing v2** | selectable **0/+10, −5/+5, −10/0, 0/+8, 0/+5** | `[docs]` `VCVRack/Befaco/docs/MIDIThingV2.md` |

**Every single one is a 10 V span or less, and the largest magnitude anywhere is 10 V.**
Nobody asks the op-amp for +10 *and* −10. The clearest statement of the industry's thinking
is the VOR variant of O\_C: when its users wanted more range, the designer did not widen the
span — he made the 10 V window **slide**, by making `V_bias` adjustable. All three VOR
settings are 10 V wide; only the offset moves.

Arithmetic from the VOR constants, which also validates my reading of the whole stage
`[source: OC_DAC.h, VBiasManager.h]`:

| VOR mode | `V_bias` | `Vout = −4.016·Vdac + 5.016·V_bias`, Vdac 0…2.5 V | Displayed |
|---|---|---|---|
| Unipolar | 3900/4095 × 1.2 V × 1.75 = 2.001 V | +10.04 → 0.00 | "0V -> 10V" |
| Asymmetric | 2760 → 1.416 V | +7.10 → −2.94 | "-3V -> 7V" |
| Bipolar | 2000 → 1.026 V | +5.15 → −4.89 | "-5V -> 5V" |

Consequences of ±10 V that Woody has not written down:

- **Resolution.** Woody's 305 µV/LSB over 20 V is *identical* to what the Performer gets
  over ±5 V — because the Performer deliberately uses only 15 of its 16 bits (below). Woody
  pays a full bit for range it says it will not use by default ("default every mod range to
  0–8 V").
- **What receivers expect.** ±5 V and 0–10 V are the two conventions; a lot of Eurorack
  input stages are scaled for ±5 V and will clip, fold, or simply run out of headroom above
  that. Sending ±10 V into an attenuverter or a VCA CV input is not neutral `[from memory —
  Doepfer's own standards page is blocked]`.
- **Jack-to-jack patching.** Woody already fits `BAV99` clamps to the ±12 V rails, which is
  more protection than any module here has (O\_C, Performer and Yarns have *no* output
  clamp diodes at all `[schematic]`). At ±10 V out the clamps sit only ~1.5 V from
  conducting, so a modest rail sag on a neighbouring module puts the clamps into
  conduction on signal peaks. At ±5 V that never happens.

**Where Woody is entitled to differ:** ADR 0006's reasoning — "the point is not to *output*
±10 V routinely, it is to be **able** to" — is a legitimate one-off argument that a
commercial module cannot make, because a commercial module has to be safe in racks it will
never see. In *one known rack*, owned by the person who will patch it, the argument holds.
But see §5: the current numbers do not actually deliver ±10 V, and the honest version of
this decision is "±9 V, on purpose".

---

## 4. Resistor tolerance, and what mismatch does on a modulation output

**What people buy.** Plain 1 %, in the smallest package that fits:

- Yarns v0.3: *"Resistor, 1%"*, 0603, for **all** of R18–R23 (47k) and R26–R29 (240k) `[BOM]`
- Marbles v7.0a: *"<=1%, 100mW"*, **0402**, throughout `[BOM]`
- O\_C rev2e: 24k9 / 100k / 47k, no tolerance called out on the schematic `[schematic]`
- Performer: 24k / 100k / 33k / 22k, `bom/bom.csv` present in the repo `[schematic]`

**No matched networks anywhere**, including on 1 V/oct pitch outputs. Woody's LT5400 for
pitch is *above* commercial practice, not at it — which is a defensible choice for a one-off
(ADR 0006 already argues it honestly, and then correctly notes that the trimmer's tempco
puts it back in the same league as discretes).

**Where the accuracy actually comes from, in every one of these designs: a per-channel
calibration table in non-volatile memory.**

| Module | What is stored | Points |
|---|---|---|
| Yarns | `calibrated_dac_code_[11]` per voice, all 4 channels | 11 (one per volt, −3…+7) `[source]` |
| PER\|FORMER | `CvOutput::ItemArray` per channel, all 8 channels | 11 (`MinVoltage=-5 … MaxVoltage=5`, `ItemsPerVolt=1`) `[source]` |
| Marbles | `dac_scale[ch]` + `dac_offset[ch]`, all 4 channels | 2 floats (affine) — defaults `−6212.8` and `32768.0` `[source]` |
| O\_C | `calibrated_octaves[ch][OCTAVES+1]`, all 4 channels, plus autotune against a real VCO | 11 `[source]` |

Two things follow for Woody.

**(a) A small correction.** ADR 0006 says *"Mutable's Yarns uses twelve [points] for exactly
this reason"*. It uses **eleven** — `const uint16_t kNumOctaves = 11;` `[source: yarns/voice.h:37]`,
and the manual walks the user from −3 V to +7 V inclusive `[docs]`. Harmless, but it is the
kind of number that gets quoted onwards.

**(b) A real one.** ADR 0006 says *"Mod channels stay trimmer-free … firmware scaling is
sufficient there"*, and `mod-channels.md` says *"per-channel scale and offset are firmware"*
while the ADR text only ever promises **scaling**. The pitch section of the same ADR already
learned this lesson the hard way ("Nothing implemented `b`" / "store an affine (gain, offset)
pair, not a scale factor"). **The mod channels need the same two numbers, for the same
reason, and the arithmetic is worse than the page thinks.**

Here is the corrected tolerance arithmetic. `mod-channels.md` states:

> With 1 % parts the worst case is roughly `2.5 V × 2 % × 4 ≈ 50 mV`, which is 0.25 % of the
> ±10 V span.

That expression evaluates to 200 mV, not 50 mV, and in any case it is the wrong model: it
only considers the zero point, and it ignores that the two ratios share `R2`, which partly
cancels. I enumerated all sixteen 1 % corners of the actual network
(`R1=R3=10k`, `R2=R4=40.2k`):

| Quantity | Nominal | 1 % worst case |
|---|---|---|
| Output at `Vdac = 2.5 V` (the "0 V" point) | 0 mV | **±81 mV** |
| Output at `Vdac = 5 V` | +10.05 V | +10.25 V |
| Total span | 20.10 V | **19.70 … 20.51 V (±2 %)** |

So the offset term is *better* than the page claims (±81 mV, not 200 mV) but **the dominant
error is gain, ±2 %, which the page does not mention at all.** A difference amp has two
independent ratios; a mismatch between them is a gain error first and an offset error
second. This is exactly the error term the inverting topology does not have.

**Consequence on a modulation output specifically — the honest version.** ADR 0006's
"nobody's ear cares whether a modulation CV is 2 % off" is true *if the channel drives a
VCA, a filter cutoff or a wavefolder*. It is false for three uses that Woody has explicitly
enabled by making the channels **generic**:

1. **A mod channel patched to a 1 V/oct input.** ±2 % gain is ±24 cents per octave,
   cumulative; ±81 mV of zero error is ±1 semitone of transposition. Nothing in Woody stops
   a user assigning a mod channel to a second pitch CV — the ADR advertises "a gate can be
   assigned to one".
2. **A mod channel driving a quantiser.** Same numbers, and the error shows up as wrong
   *notes*, not as a slightly wrong depth.
3. **A channel whose "bipolar" setting is expected to be symmetric.** An 81 mV zero error on
   a ±5 V LFO means the waveform is not centred; patched to a through-zero or ring-mod
   input, an off-centre zero is audible as a residual carrier rather than as "2 % off".

Practice agrees: **O\_C, Yarns and the Performer calibrate every channel identically**, at
one point per volt, precisely because a generic channel might be a pitch channel. Woody
already builds the NVS table for pitch. Extending Marbles' two floats to the four mod
channels is eight floats and no hardware.

---

## 5. Headroom and the gain-of-4 problem

**What real modules do about the rails: they do not go near them.**

- Maximum output magnitude found anywhere in this session: **+10.04 V** (O\_C VOR unipolar
  mode, OPA2172 on ±12 V) and that is one-sided — the same hardware's most negative output
  is −4.89 V `[source, derived from VOR constants]`.
- The Performer's hardware is capable of −15.7 V and never produces it, because
  **firmware clamps the code space**: `defaultItemValue` and `setItem` both
  `clamp(..., 0, 0x7fff)` and the comment reads
  ```
  // In ideal DAC/OpAmp configuration we get:
  // 0     ->  5.17V
  // 32768 -> -5.25V
  ```
  `[source: Calibration.h]`. They set the resistors for convenience (24k/100k = 4.1667), then
  **threw away a bit of DAC range to land on ±5 V.** That is the opposite of Woody's approach
  of selecting 40.2 kΩ from E96 so the jack lands on exactly ±10.05 V.

**And Woody's ±10.05 V is not actually reachable as specified.** ADR 0006 establishes, for
pitch, that *"the DAC8568 at AVDD = 5 V cannot reliably swing to its own supply"* and
therefore uses a **0.25–4.75 V window**. The mod channels use the same chip on the same
5.21 V rail, and `mod-channels.md` assumes `Vdac` reaches 0.000 V and 5.000 V exactly. With
the ADR's own window the mod stage reaches:

```
4.02 × (0.25 − 2.5) = −9.05 V        4.02 × (4.75 − 2.5) = +9.05 V
```

**±9.05 V, not ±10.05 V.** One of the two statements has to give. Three coherent options:

1. Accept **±9 V** and say so (still more span than anything published).
2. Keep ±10 V and raise the gain to suit the window: `20 / 4.5 = 4.444`, so 44.2 kΩ (gain
   4.42, ±9.95 V) or 45.3 kΩ (gain 4.53, ±10.19 V) against 10 kΩ.
3. Do what the Performer does: pick the resistors for a comfortable gain, clamp the usable
   code range in firmware, and stop caring where the hardware's theoretical limit is.

Option 3 is what practice does and is the least brittle. It also removes the "40.2 kΩ rather
than 39 kΩ" paragraph's whole reason for existing.

On the op-amp itself: an OPA2197 is RRIO and ±10 V on ±11.65 V rails is within its
capability at these load currents `[from memory — TI datasheets are blocked]`. The headroom
concern with ±10 V is not the op-amp, it is (a) the `BAV99` clamps sitting 1.5 V from
conduction, and (b) the −12 V rail in a real rack, which is routinely 200–400 mV low under
load and is not regulated by anything Woody controls.

---

## 6. Power-up sequencing: DAC on 5 V, op-amps on ±12 V

**Every design opened has exactly this problem and none of them adds a part for it.**

| Module | DAC rail | Op-amp rails | Series R between them |
|---|---|---|---|
| O\_C rev2e | `3V3_A` (ADP150) | ±12 V | 24 k9 — *the gain resistor* |
| PER\|FORMER | `+3.3VA` | ±12 V | 24 k — *the gain resistor* |
| Yarns | 5 V | ±12 V | 47 k — *the gain resistor* |

`[schematic]` for all three. **The inverting topology's input resistor is the clamp-current
limiter.** At 24 kΩ the worst-case current into a dead op-amp's input clamp is about
`(2.5 − 0.7)/24k ≈ 75 µA`. Nobody adds a dedicated series part, because the topology already
contains one.

Woody's `R-OPAMP-IN` exists for exactly this reason and ADR 0006 argues for it well. On the
**pitch** stage and the two **followers** it is correct and costs nothing — a follower's
(+) input is driven directly and genuinely has no series impedance (`pitch-stage.md` makes
this argument correctly). **On the four mod channels it is wrong twice over:**

**(a) It is redundant.** The difference amp already has 10 kΩ in series with the DAC leg.
That alone bounds the clamp current to ~430 µA, about 20× inside a typical op-amp's ±10 mA
input-current rating `[from memory — OPA2197 datasheet blocked]`, and it is the same
mechanism the three published designs rely on with 24 k–47 k.

**(b) It is inside the gain-setting network, and it breaks the bridge.** This is the one
hard defect in this report. `mod-channels.md` draws `DAC → [1k R-OPAMP-IN] → [R3 10k] → …`,
and `bom.csv` confirms the count (`R-OPAMP-IN` qty 7 = pitch + **4 mods** + offset buffer +
`VREFOUT` follower). So the DAC leg is **11 kΩ against the reference leg's 10 kΩ**:

| | Nominal (no 1 k) | With the 1 kΩ as drawn |
|---|---|---|
| `Vout` at `Vdac = 2.5 V` | 0.000 V | **−0.196 V** |
| `Vout` at `Vdac = 5 V` | +10.05 V | **+9.657 V** |
| `Vout` at `Vdac = 0 V` | −10.05 V | −10.05 V |
| Span | 20.10 V | 19.71 V, **asymmetric** |

A deterministic **−196 mV** zero error — 2.4× the *entire* ±81 mV worst case of the 1 %
resistor budget the page spends three paragraphs on — and a range that is no longer
symmetric. Reel-matching the resistors, which the page recommends, does nothing about it.

Three notes on this:

- **The `CLR` property survives.** With `Vdac = 0` and `V_OFF = 0` the output is 0 V
  regardless of the ratios, so the load-bearing argument of the page is untouched.
- **The drawing is also ambiguous about orientation.** As the ASCII art literally reads,
  `R3` from the DAC lands on the **(−)** input and `R1` from `V_OFF` on the **(+)**, which
  would give `Vout = −3.65·Vdac + …` — the wrong sign for `Vout = 4·(Vdac − 2.5)`. I have
  assumed the intended orientation (DAC on the (+) leg) throughout. Whichever it is, the
  page needs redrawing before anyone stuffs a board from it.
- **The fix is deletion, not a value change.** Drop `R-OPAMP-IN` on the four mod channels
  (qty 7 → 3: pitch, offset buffer, `VREFOUT` follower). Every published design does the
  same thing implicitly.

**One sequencing failure mode Woody has not considered, which is a direct consequence of
the DAC-channel offset.** In O\_C and the Performer the mid-reference is a passive divider:
there is no register to write, no channel to refresh, nothing firmware can forget. Woody's
offset is **firmware state**, shared by four outputs. `mod-channels.md` already identifies
the mirror-image failure (refresh the five signal channels but not channel 7 → all four
jacks pin at +11.45 V) and closes it with a firmware rule. That is the right fix, but note
what it means: **four CV outputs are now protected from a rail-pin by a software
convention, on a module with no `MISO` to notice.** Published practice deliberately keeps
the offset out of firmware's reach. If the DAC-channel offset is kept, this is the argument
that should be written next to it — not the `CLR` argument, which the published designs
sidestep entirely.

Two smaller sequencing/robustness points from the same comparison:

- **`V_OFF` has no filter capacitor.** O\_C puts 100 nF on `V_bias`; the Performer puts
  `C25` on `VBIAS` `[schematic]`. Reference noise at that node is multiplied by `(1+k) ≈ 5`
  onto every channel. Woody's node is an op-amp output (low-Z, so no divider noise) but the
  DAC channel's own output noise and its LSB dither land on all four mod jacks, correlated.
  A 100 nF (or an RC) on `V_OFF` is free.
- **The offset is the DAC's slowest-settling obligation.** ADR 0006 writes it "once at boot".
  The Performer and O\_C get a node that is correct from the instant the reference comes up.

---

## What Woody should change

Ordered by how much it costs to fix after fab.

1. **Delete `R-OPAMP-IN` from the four mod channels.** `bom.csv` qty 7 → 3. It is redundant
   (the 10 kΩ already limits clamp current, as 24 k–47 k does in three published designs) and
   as drawn it puts a deterministic −196 mV zero error and a 0.39 V span error into the
   stage — larger than the whole 1 % tolerance budget. Impossible to fix after fab.
   **(§6)**
2. **Redraw the mod channel.** The ASCII art does not unambiguously show which leg the DAC
   is on, and as literally read it has the wrong sign. This is the page someone stuffs a
   board from. **(§6)**
3. **Seriously consider inverting the stage.** `Vout = −4·(Vdac − 1.25 V)`, with the 1.25 V
   from a 2-resistor divider off `VREFOUT` into the (+) input, buys: one fewer DAC channel,
   one fewer op-amp half, one fewer `R-OPAMP-IN`, no common-mode swing, one ratio instead of
   two (killing the ±2 % gain-mismatch term), and the same 0 V-at-power-on property. Cost:
   firmware inverts the code (`65535 − code`, which is what O\_C does verbatim:
   `uint32_t _data = OC::DAC::MAX_VALUE - data;` `[source: OC_DAC.cpp]`) and a `CLR` would
   park the outputs at +10 V instead of 0 V. Given the `CLR` sentence in ADR 0006 is itself
   unverified (§2), this trade deserves to be made deliberately rather than by default.
   **(§1, §2)**
4. **Give the mod channels a per-channel affine `(gain, offset)` pair in NVS**, exactly as
   pitch got, and exactly as Marbles stores `dac_scale` + `dac_offset` for all four of its
   channels. The tolerance analysis in `mod-channels.md` is one term short: the dominant 1 %
   error is a **±2 % gain error**, not the ±81 mV offset. Eight floats, no hardware.
   **(§4)**
5. **Resolve ±10.05 V against the 0.25–4.75 V DAC window.** With the ADR's own window the
   stage reaches ±9.05 V. Either say ±9 V, or raise the gain (44.2 k/45.3 k), or adopt the
   Performer's approach: loose gain, range clamped in firmware. The "40.2 kΩ rather than
   39 kΩ" justification is currently precision applied to a number that is wrong for a
   different reason. **(§5)**
6. **Name one DAC grade in the BOM, not "C (or A)".** The Performer needed a persistent
   hardware-config byte and a one-bit data shift to support A-grade parts alongside C.
   `U-DAC` should name a single orderable part. **(§2)**
7. **Fix two quoted facts.** Yarns uses **11** calibration points, not twelve
   (`kNumOctaves = 11`). And the `CLR`-clears-to-zero-scale claim is a software register
   (four settings, including "ignore"), not a grade property — check the datasheet before
   ADR 0006 rests an argument on it. **(§2, §4)**
8. **Put 100 nF on `V_OFF`.** Both comparable designs decouple that node. Free. **(§6)**

## What Woody should keep

1. **A DAC-derived offset rather than a rail-derived or bandgap-derived one.** This is
   exactly right, and it is what O\_C and the Performer do (from `VREFOUT`, via a divider).
   The reasoning in ADR 0006 — "both routes track the same reference … so the drift argument
   is a wash, and the DAC channel wins on the power-on state" — is sound and matches
   practice. Only the *implementation* (a channel plus a buffer) is more than practice needs.
2. **One shared offset node for all four channels.** `mod-channels.md`'s argument — a
   residual appears as a common shift across the set rather than four channels disagreeing —
   is precisely why O\_C and the Performer share one `V_bias` across four and eight channels
   respectively. Do not split it.
3. **Bipolar rather than unipolar, decided in hardware.** ADR 0006's reasoning (unipolar is
   permanent, firmware can never recover it) is correct, and O\_C's VOR history is the
   evidence: the module shipped unipolar-ish, and the community's response was to add an
   adjustable bias so the window could move. Woody gets that on day one.
4. **1 % discretes on the mod channels.** Yarns, Marbles, O\_C and the Performer all use
   plain 1 % parts on channels that carry pitch. Woody is at practice, not below it. The
   "buy from one reel" note is good.
5. **Defaulting the mods to 0–8 V with bipolar opt-in per channel.** 0–8 V and ±5 V are the
   two conventions confirmed here from four vendors' own documentation. Making ±10 V
   available but not default is the right shape of decision.
6. **A one-off's right to exceed commercial practice.** The `BAV99` clamps, the LT5400 on
   pitch, the ±10 V capability and the per-load calibration presets are all things no
   commercial module would pay for. For one instrument in one known rack, owned by the person
   patching it, each is defensible — and ADR 0006 mostly argues them honestly. The problems
   found here are not "Woody is over-built", they are "two numbers are wrong and one resistor
   is in the wrong place".

## One thing Woody rejected that practice does not

ADR 0006 rejects feeding the op-amp's feedback from the jack side of the 1 kΩ output
resistor, on the grounds that it "puts the patch cable's capacitance inside the loop, and the
correct compensated version of that (TI's dual-feedback topology) has to be designed as one
piece with the output filter it replaces. That is real stability work, on a board without
one."

**All three multichannel modules I traced do exactly this, with one small capacitor.**
From the Performer's netlist, channel 1, traced node by node `[schematic: sequencer.net]`:

```
DAC1 ──[R44 24k]──┬── U4.2 (−)          U4.3 (+) ── VBIAS
                  ├──[R35 100k]──┐
                  └──[C16 18pF]──┤
                                 │
        U4.1 (out) ──[R43 220R]──┴── CV1 jack
```

`R35` (the feedback) returns from **the jack**, not from the op-amp output; `C16` (18 pF)
returns from the op-amp output. That is the compensated dual-feedback arrangement,
implemented with one 0402. O\_C does the identical thing (100 k from the jack side of the
220 Ω, 22 pF from the op-amp output) and Yarns does it too (240 k from the jack side of the
1 kΩ, 18 pF from the op-amp output) `[schematic]`.

This is not a recommendation to change Woody's pitch stage — ADR 0006's conclusion (keep the
1 kΩ, absorb it in calibration, use a buffered mult) is defensible and the per-load affine
pair is a real fix. But the ADR's premise, that this is exotic stability work, is not
supported: it is what the three most-cited open multichannel CV modules all do, and it is one
capacitor. If the pitch channel's load-dependence ever becomes annoying in practice, this is
a cheaper escape than the ADR implies. On the **mod** channels it would also remove the 1 %
divider error against whatever they are patched into — which, on a generic channel that
might be feeding a quantiser, is the same argument as §4.

---

## Sources opened in this session

Cloned to the session scratchpad
(`/tmp/claude-0/-home-user-Woody/b013df0e-2676-5ab4-a382-d73979c2fcee/scratchpad/`):

| Source | What I read |
|---|---|
| `mxmxmx/O_C` | `hardware/o_c_rev2e_schematic.pdf` (text-extracted, plus rendered crops `oc_dac.png`, `oc_out_right.png`); `software/o_c_REV/OC_DAC.{h,cpp}`, `VBiasManager.h`, `OC_calibration.ino`, `OC_gpio.h` |
| `westlicht/performer-hardware` | `dac.sch`, `jacks.sch`, `sequencer.net` (full netlist trace), `sequencer-cache.lib` (DAC8568 pinout) |
| `westlicht/performer` (firmware) | `src/platform/stm32/drivers/Dac.{h,cpp}`, `src/apps/sequencer/model/Calibration.h`, `src/apps/hwconfig/HardwareConfig.h`, `CHANGELOG.md` |
| `pichenettes/eurorack` | `yarns/hardware_design/Yarns.xlsx`, `marbles/hardware_design/Marbles.xlsx` (Mutable's own BOMs); `yarns/voice.{h,cc}`; `marbles/marbles.cc`, `marbles/settings.cc` |
| `pichenettes/mutable-instruments-documentation` | `docs/modules/{yarns,marbles,stages,peaks,tides_original}/*.md` |
| `TOILmodular/MARBLES`-style Yarns redraw (`toil_yarns.pdf`) | pages 1–3 text + rendered output-stage crop `yarns_out.png` |
| `TomWhitwell/Workshop_Computer` | `documentation/computer_Rev_1_0_0_Schematic.pdf` (no text layer — read as a rendered page crop, `wc_cvout.png`) |
| `Befaco/midithing` | `hardware/Midi_Thing _V1_Schematic.pdf` (no text layer — rendered crop `mt_cv.png`) |
| `VCVRack/Befaco` | `docs/MIDIThingV2.md` (fetched raw) |

**Caveat on the rendered crops.** The PNG crops of the O\_C, Yarns-redraw, Workshop Computer
and Midi Thing schematics were rendered into this scratchpad by an earlier process in this
session directory, not by me. I read them myself, and for O\_C and Yarns I cross-checked them
against sources I *did* open directly (my own text extraction of `o_c_rev2e_schematic.pdf`,
and Mutable's `Yarns.xlsx` BOM) — the component values agree exactly in both cases. The
Workshop Computer and Midi Thing crops have no such cross-check; treat those two rows as
one-source claims.

## What I could not check

The egress proxy returned **403 on CONNECT** for every vendor site:

- `doepfer.de` — **blocked**. No Doepfer schematic PDFs, and no primary source for the
  Eurorack voltage-standard claims. Everything I say about "what Eurorack expects" comes from
  module manuals I *could* read, not from Doepfer.
- `mutable-instruments.net` and `pichenettes.github.io` — **blocked**. Mutable's own schematic
  PDFs were unreachable; the Eagle files in the git repo are Eagle *binary*, not XML, so the
  Yarns topology above rests on the TOILmodular redraw plus Mutable's own BOM. The two agree
  on resistor values and counts, but I could not confirm the exact reference plumbing (how
  the `REF02` 5 V becomes the `VREF`/`VREF/2` nets) from a Mutable-authored document.
- `befaco.org`, `expert-sleepers.co.uk`, `musicthing.co.uk`, `nonlinearcircuits.blogspot.com`
  — **blocked**. No Expert Sleepers data at all; ES-8/ES-9/FH-2 output ranges are not in this
  report because I could not verify them.
- `ti.com` — **blocked**. **No datasheet claims in this report are first-hand.** Specifically
  unverified: the DAC8568 clear-code register default, the A-vs-C grade differences, the
  OPA2197 absolute-maximum input current and output swing. Where those matter I have said so
  in place.
