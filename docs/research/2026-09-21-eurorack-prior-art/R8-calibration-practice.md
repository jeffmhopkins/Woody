# R8 — How 1 V/oct calibration is actually done, in hardware and in open firmware

**Date:** 2026-09-21 · **Topic:** prior art for Woody's pitch calibration
(ADR 0006, `hardware/module/pitch-stage.md`, ROADMAP E8/E9)

## Evidence markers used here

- `[source]` — I read the code, schematic or BOM in this session. The file is named.
- `[docs]` — I opened the manual or documentation text. The file or URL is named.
- `[search]` — a web-search result summary only; the underlying page is **blocked**
  from this sandbox and I could not open it. Treat as weak.
- `[analysis]` — arithmetic I did here from Woody's own numbers or from a source's
  numbers. Not prior art. Check it.
- `[from memory]` — no source in this session. Treat as a lead, not a fact.

**Network:** GitHub (clone, raw, API) is reachable. The following were **blocked by
the egress proxy** and I could not read them: `pichenettes.github.io`,
`ornament-and-cri.me`, `www.expert-sleepers.co.uk`, `www.musicthing.co.uk`,
`northcoastsynthesis.com`, `files.northcoastsynthesis.com`, `learningmodular.com`,
`www.modwiggler.com`, `www.soundonsound.com`, `www.ti.com`/`www.analog.com`.
Where those matter I say so rather than guessing.

## Repositories read in full

| Project | What I read |
|---|---|
| Mutable Instruments (`pichenettes/eurorack`) | `yarns/voice.{h,cc}`, `yarns/ui.cc`, `yarns/multi.h`, `yarns/storage_manager.cc`, `yarns/midi_handler.cc`, `yarns/drivers/dac.h`, `yarns/hardware_design/Yarns.xlsx` (BOM), `marbles/settings.{h,cc}`, `marbles/marbles.cc`, `marbles/cv_reader.h`, `marbles/ui.cc`, `ripples/hardware_design/Ripples.xlsx` |
| Mutable docs (`pichenettes/mutable-instruments-documentation`) | Yarns, Braids, Rings, Clouds, Plaits, Elements, Warps, Edges, Ripples, Tides manuals; Marbles/Stages spec pages; `tech_notes/life_of_a_cvpal_midi_note.md` |
| Ornament & Crime (`mxmxmx/O_C`) | `OC_calibration.{h,ino}`, `OC_DAC.{h,cpp}`, `OC_ADC.cpp`, `OC_autotune{,_presets}.h`, `OC_autotuner.h`, `APP_REFS.ino`, `hardware/o_c_rev2e_schematic.pdf` (text extracted) |
| CVpal (`pichenettes/cvpal`) | `cvpal/calibration_table.{h,cc}`, `cvpal/midi_handler.cc` |
| Befaco MIDI Thing v1 (`Befaco/midithing`) | `firmware/MultiPointConv.{h,ino}`, `firmware/MIDILearn.ino`, `README.md` |
| Music Thing Workshop Computer (`TomWhitwell/Workshop_Computer`) | `releases/00_Simple_MIDI/**` — `calibration.h`, `DACChannel.h`, `Simple_Midi_0_6_6.ino`, `TECHNICAL_NOTES.md`, `README.md` |
| elkayem/midi2cv | `midi2cv.ino`, `README.md` |

---

## Findings vs Woody

| # | What real designs do | What Woody does | Verdict |
|---|---|---|---|
| 1 | **Digital CV sources ship no trimmers at all.** Yarns' BOM has zero trimmers `[source]`; O&C's schematic has zero `[source]`; Marbles, Stages, Music Thing Computer, CVpal, Befaco MIDI Thing: all firmware-only `[source]`. Trimmers appear on the **analog** side — Ripples has exactly one, a 25-turn scale trim on its exponential converter `[source]` `[docs]` | Two multiturn cermet trimmers on the pitch output, "which is also why every commercial 1 V/oct module has scale and offset trimmers" (ADR 0006) | **Woody's premise is false as stated.** Not one of the seven digital CV sources I read has an output trimmer. The claim is true of analog V/oct *inputs*, not of DAC *outputs* |
| 2 | Calibration reference is a **4½-digit multimeter** for the module's own output (Yarns `[docs]`, O&C `[source]`, Music Thing `[docs]`). A real VCO is used only where the VCO is *inside a closed loop* (O&C autotune) `[source]` | E9: "verified against a real VCO, not just a meter" | **Right instinct, wrong instrument for the measurement.** Practice: measure with a meter, *verify* with a VCO. Woody conflates the two |
| 3 | Storage is **raw DAC codes or floats, per channel, in a dedicated slot**, guarded: Yarns uses flash slot 0 separate from preset slots 1..n `[source]`; CVpal checksums `[source]`; Music Thing has magic + format version + CRC `[source]`; Marbles clamps any loaded constant >10 % off nominal back to default `[source]` | "per-load affine `(gain, offset)` pair … two stored floats", NVS | **Model is fine; the guards are missing.** Woody has no stated corruption guard, no format version, no separation from other NVS data |
| 4 | Point count tracks DAC resolution: 16-bit parts get **1 point/octave** (Yarns 11, O&C 10) `[source]`; 12-bit parts get **2 points/octave** (CVpal 9 @ 0.5 V, Befaco 21 @ 6 semitones) `[source]`. Factory-calibrated modules use **2 parameters** (Marbles, Music Thing) `[source]` | Multi-point table, "roughly one point per octave — Mutable's Yarns uses twelve" (ADR 0006); ROADMAP E9 says "Two-point fit" | **One point/octave is correct for a 16-bit DAC.** But Yarns uses **eleven**, not twelve, and not for the reason Woody gives. And ADR 0006 and ROADMAP E9 contradict each other |
| 5 | **Nobody stores a per-load calibration preset.** The nearest thing is O&C's two slots per channel — `dflt.` (meter) and `auto.` (through the actual VCO) — user-switchable `[source]`. Everyone else's answer is a lower output impedance (O&C: **220 Ω**, vs Woody's 1 kΩ) `[source]` or a buffered mult `[search]` | Named affine preset per patch: "one VCO", "two multed" | **Genuinely novel, and probably unnecessary.** Woody already names the real fix (buffered mult). See §5 — and see the sign error in the argument for it |
| 6 | Published accuracy for a calibrated CV output: Marbles **"error below 1 mV"** ≈ 1.2 cents; Stages **"below 2 mV"** ≈ 2.4 cents `[docs]`. Yarns' calibration UI resolves ~0.2 mV ≈ 0.24 cents/click `[docs]` | Static budget ≈ 1–2 cents | **Ordinary.** Exactly the industry norm. Not optimistic, not exceptional |
| 7 | **Nothing compensates temperature.** No warm-up guidance in any manual read. Ripples states outright: "designed to track well over 4 octaves, but is **not temperature-stabilized**" `[docs]` | ~0.4–2.4 cents over 10 °C, dominated by the gain trimmer's cermet tempco | **Woody matches practice in outcome but is worse in cause** — the dominant drift term is a part Woody added on purpose, in series with the precision part bought to prevent exactly that |

---

## The headline finding

**Both original reasons for adding trimmers have since been withdrawn by Woody's own
documents, but the trimmers stayed.**

ADR 0006 gives two reasons (`docs/decisions/0006-cv-channel-allocation.md`, "Why
firmware alone was not enough"):

1. *"Firmware calibration has no offset authority … Nothing implemented `b`."*
   Retracted later in the same ADR: *"the hardware authority already exists … firmware
   can shift the DAC code. 'Nothing implemented b' was true of the model and never of
   the part."*
2. *"The gain ratio was not buildable. The 1.8× gain … is 9/5, which cannot be made
   from a matched resistor quad. **Any external resistor added to reach it puts its
   absolute tempco inside the ratio — exactly the failure the matched network was
   bought to prevent.**"*
   Retracted by `hardware/module/pitch-stage.md`: with the 0.25–4.75 V window the slope
   is *exactly* 2.000 and the ratio is **1:1**, the easiest match there is, with the
   intercept supplied by the same `VREFOUT` the DAC references.

Reason 2's own sentence now condemns the trimmer. `TRIM-GAIN` **is** an external
resistor inside the ratio. Woody's numbers, both of them:

| | Over 10 °C |
|---|---|
| LT5400 1:1 ratio tracking alone | **0.11 cents** (ADR 0006) |
| With a 5 % cermet trim in series | **2.4 cents** (ADR 0006) or **0.4 cents** (pitch-stage.md) |

Those two Woody figures disagree by 6× — ADR 0006 assumes ~250 ppm/°C cermet over the
full 9 V span, pitch-stage.md assumes ~100 ppm/°C referred to +7 V `[analysis]`. Either
way the trimmer is **4× to 20× the matched network it is soldered in series with**, and
it is the largest single line in the pitch-stage static budget table. The LT5400 is
being bought and then thrown away.

Meanwhile every digital module I read solves the same problem with 1 % resistors and a
firmware table, and publishes 1–2 mV of accuracy while doing it `[source]` `[docs]`.

---

## 1. Trimmers vs firmware — what published designs actually ship

**Mutable Yarns** (4× 16-bit CV out, the closest analogue to Woody's pitch channel).
BOM `yarns/hardware_design/Yarns.xlsx` `[source]`: DAC8564 quad 16-bit, REF02 5 V
reference, OPA4171 quad op-amp, resistors "Resistor, 1%" 0603 throughout (51 R, 1.0 k,
10 k, 47 k, 240 k). **There is no trimmer in the BOM.** I also searched the Eagle
board file for trimmer footprints and package names and found none `[source]`.
All gain, all offset and all curvature come from an 11-entry table.

**Ornament & Crime rev 2e**, schematic text extracted from
`hardware/o_c_rev2e_schematic.pdf` `[source]`. Output stage, per channel: DAC8565 →
`R 24k9` into an OPA2172 inverting node, `R 100k` feedback, `R 75k` from the `OFFSET`
net (`AREF_-5V`) also into the node, `C 22p`, then **`R 220`** in series to the
PJ301M jack. **No trimpots anywhere on the sheet** — I read the whole extracted netlist
text. Ten firmware points per channel do everything.

**Marbles / Stages**: `CalibrationData` is four float arrays —
`adc_offset[]`, `adc_scale[]`, `dac_offset[]`, `dac_scale[]` `[source:
marbles/settings.h]`. Applied at the output as literally
`voltage * scale + offset` `[source: marbles/marbles.cc:140]`. Two numbers per channel,
set at the factory, no trimmer.

**Music Thing Workshop Computer**: three measured points per channel collapsed by
least-squares into a slope `m` and an intercept `b`
`[source: DACChannel.h::calculateCalibrationConstants]`. No trimmer.

**elkayem/midi2cv** states the trade-off explicitly `[source: README.md]`:
> "If precise tuning is desired, a trim pot can be added *or* the constant `NOTE_SF`
> can be adjusted in the code. I opted for the latter."

Its firmware correction is a **scale factor only**, `NOTE_SF 47.069f`
`[source: midi2cv.ino:225]` — and that is *correct* for its topology, because its
DAC zero maps to output zero with no offset injection. Woody's stage injects −2.500 V
downstream of nothing, so it genuinely needs two numbers. Woody is right about its own
topology and wrong to generalise: "a two-point firmware fit could not implement an
offset" was never a property of firmware, only of a stage that needs an intercept and a
model that did not carry one.

**Where the trimmers actually live.** Mutable Ripples — an *analog* filter with V/oct
tracking — has exactly one trimmer, a 25-turn cermet, and the manual says `[docs:
modules/ripples_2020/manual.md]`:

> "Adjust the trimmer resistor on the side of the circuit board until the musical
> intervals played on the keyboard are correctly reproduced (actual note values do not
> matter, but when playing an octave, it must sound like an octave). The filter is
> designed to track well over 4 octaves, but is not temperature-stabilized."

Note the shape of that: **one** trimmer (scale), no offset trimmer, tuned **by ear**
against octaves, absolute pitch explicitly not calibrated because the FREQ knob supplies
the intercept. The BOM has thin-film 0.1 %/25 ppm resistors in the exponential converter
and **no tempco resistor** `[source: Ripples.xlsx]`.

So the industry division of labour is: **trimmer on the analog exponential converter;
table in firmware on the digital CV source.** Woody has a digital CV source with an
analog scaling stage and has put the trimmers on the digital side.

## 2. The calibration procedure, as documented

**Yarns** `[docs: modules/yarns/manual.md, "Calibration procedure"]` — verbatim:

> "A multimeter with at least 4 1/2 digits of precision is needed for this step. …
> connect a patch cable from this output to your multimeter. The display indicates the
> voltage, in Volts, that should be read on the multimeter (-3 at the beginning of the
> procedure) … rotate the encoder until the target voltage is reached. **Each increment
> corresponds to about 0.2 mV.** … **Calibration has to be done for all voltages between
> -3 V and +7 V.** … Calibrate the other CV output channels if necessary."

Eleven points, one per volt, per channel, against a meter. No VCO, no tuner. Code
agrees: `kNumOctaves = 11` `[source: yarns/voice.h:37]`, display strings
`{"-3","-2","-1"," 0","+1"…"+7","OK"}` `[source: yarns/ui.cc:265]`. Coarse adjust is
6 mV/click with a button held `[source: ui.cc:503]` — 7.2 cents; fine is ~0.24 cents.

**Ornament & Crime** `[source: OC_calibration.ino]`. Entered by holding the left encoder
at power-on. Forty DAC steps: four channels × ten points, **−3 V through +6 V in 1 V
steps**, each screen reading e.g. `"DAC A -3 volts" / "-> -3.000V"`, adjusted with the
right encoder against a meter. Then four ADC zero steps, then a two-point ADC pitch
calibration at **1 V (C2) and 3 V (C4)**. The first screen is `"Use defaults? "` —
`no`/`yes` — so entering the menu is non-destructive until you say otherwise. The ADC
routine carries this comment `[source: OC_ADC.cpp:115]`:

> "This is the method used by the Mutable Instruments calibration and extrapolates from
> two octaves."

**Mutable's CV *input* calibration is universally two points, 1 V and 3 V** — Braids,
Rings, Clouds, Plaits, Elements, Warps, Edges, Tides all say "Play a C2 note, or send a
1 V voltage … Play a C4 note, or send a 3 V voltage" `[docs]`. Two octaves apart, both
inside the musically-used range, not at the extremes. That is the same conclusion
ADR 0006 reaches ("Put the two pitch calibration anchor points inside the musically used
range") — arrived at independently, and it is right.

Braids' manual adds a generalisation worth stealing `[docs: modules/braids/manual.md]`:

> "Because Braids uses this software calibration procedure, it is compatible with the
> 1.2 V/Oct standard too! … you can very well perform the calibration procedure with
> another pair of notes 2 octaves apart, and with the COARSE knob in another position."

**Ornament & Crime autotune** — the only closed-loop procedure I found `[source:
APP_REFS.ino, OC_autotuner.h]`. Patch the channel to a VCO's V/oct, patch the VCO's
square out back into the module's TR4 digital input (an FTM frequency-capture pin).
The routine:

1. Outputs 0 V, measures the VCO's frequency with `FreqMeasure`, averages 8 readings.
2. Computes ten target frequencies as baseline × `{0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32,
   64}` — i.e. −3 V … +6 V `[source: `target_multipliers[]`]`.
3. For each octave, runs a successive-approximation search on the DAC code
   (`F_correction_factor_ >>= 1` on each direction reversal) until the measured
   frequency converges on the target, with `CONVERGE_PASSES 5` and a sanity check that
   throws an error if the frequency fails to roughly double between steps.
4. Writes the ten corrected codes into a **second**, separate
   `Autotune_data.auto_calibrated_octaves[11]` with a `use_auto_calibration_` flag.

Documented patching instructions (the module's own site is blocked; this is a search
summary) `[search]`: tune the VCO to 50–150 Hz at 0 V before arming, and the frequency
reading "shouldn't jump around overly erratically (in which case the procedure is bound
to fail)".

**Music Thing Workshop Computer**: three points per channel, **−2 V, 0 V, +2 V**, in a
fixed order (0 V, +2 V, −2 V, then the other channel) `[source: `calibrationOrder[6][2]`,
`kExpectedCoreVoltages`, `defaultVoltages[3] = {-20, 0, 20}` in tenths of a volt]`. The
technical notes concede `[docs: TECHNICAL_NOTES.md]`:

> "The calibration memory map reserves ten calibration points for each of the two
> channels. Simple MIDI currently uses three points per channel: -2 V, 0 V, and +2 V.
> The current manual process could be automated further to improve precision and ease
> of use."

**CVpal and Befaco MIDI Thing** calibrate **by ear or against a tuner, through MIDI
notes**, with no meter at all. CVpal listens on MIDI channels 15/16; playing the note
one semitone *below* an anchor decrements that anchor's DAC code, one semitone *above*
increments it `[source: cvpal/midi_handler.cc:210-227]`. Befaco copied the idea and says
so: "Calibration method inspired on Mutable instruments CVpal" `[source:
midithing/README.md:59]`, with the same ±1-semitone nudge scheme
`[source: MultiPointConv.ino::Processnote]` and a 55-second inactivity timeout that
exits calibration mode `[source: MIDILearn.ino:82]`.

**How often?** No manual I read specifies a cadence. No manual mentions warm-up. There
is no "recalibrate every N months" anywhere. Calibration is treated as a one-time,
per-unit event; O&C's autotune is the exception and is treated as per-VCO.

## 3. Storage and the output path

| Project | Stored | Where | Guards |
|---|---|---|---|
| Yarns | `uint16 calibrated_dac_code_[4][11]` — **raw DAC codes** | Flash **slot 0**, separate from preset slots 1..n `[source: storage_manager.cc]` | Separation from presets; also settable/dumpable over SysEx `[source: midi_handler.cc:210]` |
| O&C | `uint16 calibrated_octaves[4][11]` (88 B) + ADC cal + display offset + encoder config = 116 B, **plus** a second per-channel `Autotune_data` | EEPROM `PageStorage` with FOURCC `'CAL',1` `[source: OC_calibration.h]` | `static_assert` on struct size; "Use defaults?" prompt; explicit legacy-import path |
| Marbles | `float dac_offset[], dac_scale[]` per channel (+ ADC pair) | Flash `PersistentData`, tag `0x494C4143` `[source: settings.h]` | **`FIX_OUTLIER`**: any loaded constant >10 % from nominal is silently replaced by the default `[source: settings.cc:155]` |
| CVpal | `uint16 dac_codes_[9]` per channel | AVR EEPROM at `table_index << 5` | 16-bit checksum; regenerates the ideal table on mismatch `[source: calibration_table.cc:23-41]` |
| Music Thing | 10 slots/channel × 4 B (4-bit target voltage + 24-bit setting); 3 used | Shared I²C EEPROM page `0x50`, readable by **other program cards** `[docs: TECHNICAL_NOTES.md]` | Magic `2001`, format version byte, CRC over the block |
| Befaco | `int DACPoints[21]` per channel | EEPROM, written on calibration exit | 55 s timeout |

**Application in the output path.** Two shapes only:

- *Piecewise linear over a table* — Yarns, O&C, CVpal, Befaco. Yarns:
  ```
  int32_t a = calibrated_dac_code_[octave];
  int32_t b = calibrated_dac_code_[octave + 1];
  return a + ((b - a) * note / kOctave);
  ```
  `[source: yarns/voice.cc:99-102]`. O&C is character-for-character the same idea
  `[source: OC_DAC.h::pitch_to_dac]`.
- *Affine* — Marbles `voltage * scale + offset` `[source: marbles.cc:140]`; Music Thing
  `m * voltage + b` `[source: DACChannel.h::midiToDac]`.

Two details worth copying. First, **Yarns reuses the calibration table for everything
else the DAC does** — velocity, mod wheel and aux CVs are rendered through
`DacCodeFrom16BitValue()`, which scales between `calibrated_dac_code_[3]` (0 V) and
`[8]` (+5 V) `[source: yarns/voice.h:152-157]`. Calibrating the pitch channel calibrates
the modulation channels for free. Woody has six channels and currently plans to
calibrate one; the same trick applies if all six share a topology.

Second, **the table is stored as raw DAC codes, not as volts.** That is why the Yarns
procedure needs no arithmetic at the bench: turn the encoder until the meter reads the
number on the display, click, next. There is no fit, no interaction, no convergence.

## 4. Multi-point vs two-point

The split is not "good vs cheap". It is **who does the arithmetic**:

- **User-calibrated modules use many points** (Yarns 11, O&C 10, Befaco 21, CVpal 9)
  because each point is independent and the procedure is mechanical.
- **Factory-calibrated modules use two parameters** (Marbles, Music Thing) because a jig
  measures two forced codes and computes the fit. Marbles literally forces DAC codes
  `0xaf35` and `0x1d98`, waits for the rig to measure them, then receives
  `dac_scale`/`dac_offset` back as nibbles `[source: marbles/ui.cc,
  FACTORY_TESTING_FORCE_DAC_CODE]`.

Point **density tracks DAC resolution**, cleanly, across every project I read
`[source]`:

| DAC | Projects | Spacing |
|---|---|---|
| 16-bit (DAC8564/8565) | Yarns, O&C | **1 V** — one point per octave |
| 14-bit | Marbles, Stages | affine only |
| 12-bit (MCP49xx class) | CVpal, Befaco MIDI Thing | **0.5 V** — two points per octave |

Nobody uses finer than one point per octave on a 16-bit part. **Woody's DAC8568 is
16-bit; one point per octave is exactly right, and finer would be wasted.**

Does multi-point measurably help? On Woody's own INL figures (±4 LSB typical, ±12 LSB
worst case, quoted in ADR 0006 — I could not open the TI datasheet, `ti.com` is blocked)
the curvature a table removes and a two-point fit cannot is **0.66 to 2.0 cents**
`[Woody]`. That is the same order as the *entire* published accuracy of a calibrated
Mutable output (1–2 mV) `[docs]`. So: real, but small, and only worth having because it
is nearly free.

**But the reason Yarns uses eleven points is not the reason ADR 0006 gives.** ADR 0006
says "Firmware handles what trimmers cannot: DAC integral nonlinearity … Mutable's Yarns
uses twelve for exactly this reason." Two corrections `[source]`:

1. It is **eleven** (`kNumOctaves = 11`, −3 V … +7 V), not twelve.
2. Yarns has **no trimmers**, so its table carries gain *and* offset *and* curvature.
   It is not an INL corrector bolted onto a trimmed stage; it is the whole calibration.
   Yarns' 1 % resistors can be 2 % off in ratio — 240 cents at +7 V — and the table
   absorbs that without anyone ever touching a screwdriver.

That is the actual lesson, and it points the opposite way from the one ADR 0006 drew
from it.

## 5. The load-dependence problem

**Does anyone acknowledge it?** Partially, and never in the way Woody proposes.

- **O&C lowered the output impedance to 220 Ω** `[source: o_c_rev2e schematic]`. Against
  a 100 kΩ VCO input that is 2.63 cents/octave; against 50 kΩ, 5.26 `[analysis]`.
  Woody's 1 kΩ gives 11.9 and 23.5 `[Woody, and my arithmetic reproduces both]`.
  **O&C's choice is 4.5× better than Woody's and nobody calls it unsafe.**
- **O&C's autotune makes the load part of the calibration by construction** — the VCO is
  physically in the loop, so the 220 Ω, the cable, the VCO's input impedance and the
  VCO's own exponential-converter error are all absorbed into one table `[source]`. And
  because it lands in a *second* slot with a `use_auto_calibration_` flag, a user can
  keep a meter calibration and a through-the-VCO calibration and switch per channel
  `[source: OC_DAC.cpp::choose_calibration_data]`. **That is the closest published thing
  to Woody's per-load preset, and it is only two slots, not named presets.**
- **Yarns does not acknowledge it at all** — and worse, its documented procedure
  calibrates **into a multimeter**, i.e. into ~10 MΩ, i.e. into an open circuit, which is
  the worst possible reference load `[docs]`. Whatever series resistance Yarns has
  (its BOM contains ten 1.0 kΩ 1 % resistors and eight CV/gate jacks — I could not
  confirm from the binary Eagle file which are the output series parts `[source]`),
  the calibration is made against a load the module will never see. Woody has spotted a
  real hole in the most directly comparable commercial design.
- **The community answer is a buffered mult**, and the numbers quoted match Woody's:
  "standard eurorack output impedance of 1 k and sound source input impedance of 100 k,
  a single passive connection produces a 1 % error … 1 % for one connection, 2 % for
  two" `[search — modwiggler/North Coast/Learning Modular, all blocked here]`.
- **Yarns gives the user a runtime intercept knob instead.** `TF (FINE TUNING)` applies
  a transposition "expressed in 1/128th of a semitone (**0.65 mV increments**)" and
  `TR` transposes in semitones `[docs: yarns/manual.md:187]`. So the `b` term exists in
  Yarns as a *playing* control, per part, not as a calibration constant.

### Where I think Woody's argument has the sign backwards

ADR 0006 says a one-number (slope-only) correction is *worse* than doing nothing:

> "A one-number correction therefore converts a progressive tracking error into a
> *constant* transposition, which is worse to play than the error it replaced."

Check the two cases. Trimmed at 100 kΩ (`k_trim` = 0.990099), then played into 50 kΩ
(`k_new` = 0.980392) `[analysis]`:

| | at −2 V | at 0 V | at +7 V |
|---|---|---|---|
| **Do nothing** | **+23.5 cents** | 0 | **−82.4 cents** |
| **Correct slope only** | +29.4 | +29.4 | +29.4 |

Woody's +29 and +59 cents figures are right — I reproduce both exactly. But a *constant*
+29 cents is **fixable with the VCO's coarse/fine tune knob, which every VCO has.** The
uncorrected 106-cent spread across the range is not fixable by anything. Converting a
spread into a constant offset is not a regression; it is what a tuning knob is *for*,
and it is precisely what Yarns' `TF` control exists to absorb `[docs]`.

So the conclusion ADR 0006 draws (store two numbers, not one) is correct and cheap — but
the justification is upside-down, and the ADR uses that justification to argue the 1 kΩ
"survives". It survives on the trimmer's authority and on the buffered-mult advice, not
on this.

**And the firmware authority is ample.** Correcting the 50 kΩ case in firmware alone
needs the DAC to reach 0.2296 V instead of 0.2500 V at the −2 V end — 41 mV of extra
output swing, **49 cents out of the ±600 cents of reserve** the 0.25–4.75 V window
deliberately provides `[analysis, from pitch-stage.md's own window figures]`. The
arithmetic closes with an order of magnitude to spare. A trimmer is not needed to absorb
the load divider.

## 6. Accuracy actually achieved

| Claim | Source |
|---|---|
| Marbles: "14-bit DAC with accurate software calibration — **error below 1 mV**" | `[docs: modules/marbles/index.md:84]` |
| Stages: "16-bit CV capture, 14-bit CV generation with accurate software calibration. **Error below 2 mV**" | `[docs: modules/stages/index.md:56]` |
| Yarns: "highly accurate 16-bit DACs … capable of very precise control over tuning"; calibration resolution ~0.2 mV/click | `[docs: modules/yarns/manual.md:183, 308]` |
| Ripples (analog): tracks "well over **4 octaves**", not temperature-stabilized | `[docs: modules/ripples_2020/manual.md:48]` |

At 1 V/oct, 1 mV = 1.2 cents and 2 mV = 2.4 cents `[analysis]`. **Woody's 1–2 cent
static budget is ordinary: it is the published state of the art for a Eurorack CV
output, neither ambitious nor optimistic.** No source states an accuracy over a
temperature range or over a voltage range — the figures are bench figures at room
temperature. Nobody publishes a cents-vs-temperature curve.

Two things Woody should note about the comparison:

- Mutable's 1–2 mV is achieved with **1 % resistors and no trimmer**. The precision is
  bought in firmware, not in the BOM.
- Woody's budget is a *static* budget and ADR 0006 is right that it "was never the
  problem" — the LED-correlated and rail-coupled terms (~20 cents) dominate by an order
  of magnitude. That framing is sound and no published module I read even discusses
  those terms. Woody is ahead of practice here, not behind it.

## 7. Temperature

**Nothing in any project I read compensates for temperature.** No temperature sensor
feeds any calibration path. No manual mentions warm-up before calibrating. No manual
specifies a recalibration interval. The only explicit acknowledgement is Ripples
conceding it is "not temperature-stabilized" — about an *analog* exponential converter,
which is the one place in a Eurorack signal chain where drift is genuinely large
`[docs]`, and even there Mutable declined to fit a tempco resistor (none in the BOM
`[source: Ripples.xlsx]`).

The practical consequence: **in a real rack the dominant drift term is the VCO, not the
CV source.** ADR 0006 already says this ("a well-compensated analog VCO drifts around
0.35 cents/K … The trimmer is therefore not the limiting term") — I could not verify the
0.35 cents/K figure from a primary source in this session (vendor sites blocked), so it
remains `[from memory / unverified]`. The reasoning is sound, but it proves less than
ADR 0006 uses it for: the VCO's drift is a *constant transposition* you retune away,
while the trimmer's drift is a *slope* change you cannot. They are not interchangeable
just because they are the same number of cents.

---

## What Woody should change

1. **Re-open the trimmer decision.** Both stated reasons for it have been retracted
   inside Woody's own documents, and the part Woody added is now the largest static drift
   term in its own budget table, in series with a precision network bought to prevent
   exactly that. Seven published digital CV sources ship none. At minimum, ADR 0006's
   "which is also why every commercial 1 V/oct module has scale and offset trimmers"
   must be deleted — it is false for every digital module I could read.
   If the trimmers stay, the reason should be stated as what it now is: *they absorb the
   load divider in hardware so the DAC window stays comfortable*, which is a real but
   modest benefit worth ~49 cents of a 600-cent reserve.
2. **Fix ROADMAP E9 vs ADR 0006.** E9 says "Two-point fit stored in NVS"; ADR 0006 says
   a multi-point table at one point per octave. Pick one. Practice says: build the
   multi-point table (11 points, −2 V … +7 V, one per volt), because with raw DAC codes
   per point the bench procedure has no arithmetic and no interaction — turn, read the
   meter, click, next. That is measurably easier than the interacting two-trim procedure
   in `pitch-stage.md`, which requires "Repeat twice. It converges quickly."
3. **Correct the Yarns citation.** Eleven points, not twelve — and the table is Yarns'
   *entire* calibration, not an INL corrector on top of a trim. Cite
   `yarns/voice.h:37` and `yarns/ui.cc:265`.
4. **Fix the "worse to play" claim.** A constant transposition is *better* to play than
   a progressive tracking error, because every VCO has a tune knob and none has a scale
   knob. Keep the two-number model (it costs one float), drop the argument.
5. **Drop the 1 kΩ to ~220 Ω on pitch, or justify keeping it against O&C.** O&C ships
   220 Ω on all four 16-bit CV outputs and cuts the load error by 4.5×. ADR 0006 only
   considers 100 Ω ("gives up an order of magnitude of short-circuit protection") and
   never considers the value the most comparable open design actually chose. *(I could
   not check the OPA2197's internal short-circuit current limit — `ti.com` is blocked —
   so the protection arithmetic needs doing at the bench.)*
6. **Add the storage guards everyone else has.** A format version byte, a CRC, a
   magic number, and Marbles' `FIX_OUTLIER` idea — reject any loaded constant more than
   ~10 % from nominal and fall back to defaults `[source: marbles/settings.cc:155]`. Keep
   calibration in its own NVS namespace, as Yarns keeps it in flash slot 0 away from the
   preset slots `[source: storage_manager.cc]`. A corrupted calibration should make the
   instrument default-accurate, not silent or wildly sharp.
7. **Make the calibration mode hard to enter and non-destructive.** Braids guards it
   with a 1-second hold — "this is not an option you want to select by mistake during a
   performance" — and Plaits' troubleshooting lists accidental entry as a known failure
   mode `[docs]`. O&C opens with "Use defaults? no/yes" so entering is harmless
   `[source]`. Woody has a display and an encoder; this is free.
8. **Automate the sweep.** Yarns exposes `SYSEX_COMMAND_CALIBRATE` so a host can drive
   each point and write codes back `[source: midi_handler.cc:210-220]`; Music Thing's
   notes explicitly regret not doing this. Woody already has USB MIDI (E5) and a
   host-side path. E9 with a scripted sweep and a bench DMM is hours of work saved and
   better data.
9. **Reconsider the per-load preset before building it.** Nobody ships one. ADR 0006
   already names the actual fix — a buffered mult — and Woody is a one-off instrument
   for one rack. The cheaper prior art is O&C's *two slots*: one calibration made with a
   meter, one made through the patch, user-switchable. If the presets stay, put an
   **octave-spacing check in the UI**, not just the numbers — O&C's autotune throws an
   error if the frequency fails to roughly double between steps `[source: APP_REFS.ino]`,
   which is the check that catches a mis-set preset by ear.
10. **Reuse the pitch calibration on the other five channels.** Yarns renders velocity,
    mod and aux CVs through the same calibrated table `[source: voice.h:152]`. Woody's
    mod channels share the DAC and (per ADR 0006) a shared 2.5 V offset; one table can
    serve them all, which also resolves the ADR's own internal contradiction between
    "Mod 1–4 … Trimmed" in the channel table and "Mod channels stay trimmer-free" later.

## What Woody should keep

1. **Anchor points inside the musically used range.** ADR 0006's "Put the two pitch
   calibration anchor points inside the musically used range" matches every Mutable
   input procedure (1 V and 3 V, two octaves apart, never at the extremes) `[docs]` and
   Music Thing's −2/0/+2 V `[source]`. Independently arrived at, and correct.
2. **A per-unit calibration in non-volatile storage, applied in the DAC code path.**
   Universal. Woody's `(gain, offset)` affine model is exactly Marbles' and Music
   Thing's; the multi-point table is exactly Yarns' and O&C's.
3. **Two numbers, not one.** Correct for a stage that injects its intercept upstream of
   the load divider. midi2cv gets away with one number only because its intercept is
   structurally zero `[source]`.
4. **"Verify against a real VCO, loaded the way it will be played."** No commercial
   module's documented procedure does this and Yarns' calibrates into an open circuit
   instead `[docs]`. Woody has identified a genuine gap in the most comparable design.
   Keep the E9 wording — but measure with the meter and *verify* with the VCO; that is
   how O&C splits it, and the frequency-counter loop is a verification instrument, not a
   substitute for the meter.
5. **The `VREFOUT`-referenced offset.** Making reference drift a pure gain term rather
   than an offset term (`pitch-stage.md`) is better reasoning than anything I found in a
   published design, and the 1:1 LT5400 with the reference at the bottom of the feedback
   divider is a genuinely elegant result. Keep it — and keep the trimmer out of that
   ratio if at all possible.
6. **Treating the dynamic, LED- and rail-correlated terms (~20 cents) as the real
   problem.** No published module discusses them. ADR 0006's priority ordering is ahead
   of practice.
7. **The E9 load sweep (open / 100 k / 50 k / 33 k).** Nobody publishes this measurement.
   It is the right experiment and it will settle items 1 and 5 above with numbers instead
   of argument.

---

## Gaps in this research

- Yarns' and Marbles' schematics are Eagle 5 binary and their PDF exports have no text
  layer, so I could read their **BOMs** but not their **netlists**. I cannot state
  Yarns' output series resistance, only that its BOM has ten 1.0 kΩ 1 % parts and no
  trimmer.
- Every module-vendor and forum domain I needed was blocked (list at the top). The
  Expert Sleepers Silent Way VCO calibration, the Music Thing calibration guide, the
  O&C user manual and the North Coast passive-mult paper are all `[search]`-only here.
  Anything I attribute to them is a search summary, not a read.
- I could not open TI or Analog datasheets, so every DAC INL, op-amp offset and
  short-circuit-current figure in this document is either Woody's own or unverified.
- I found **no** project with temperature compensation on a CV output, but that is a
  negative result from the projects I read, not an exhaustive survey.
