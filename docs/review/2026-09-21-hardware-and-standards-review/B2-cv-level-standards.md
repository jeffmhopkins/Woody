# B2 — CV level and scaling standards review

**Date:** 2026-09-21
**Reviewer:** cold standards reviewer (B2). I did **not** read `docs/review/**` or
`docs/research/**`. Two `grep` calls over the whole repo incidentally printed a
handful of matching *lines* from those trees before I narrowed the globs; I have
discarded them and nothing below is derived from them.
**Scope:** every signal that leaves the 8HP module on a jack — PITCH, MOD 1–4,
BREATH — plus the gate/trigger output that does not exist.
**Repo inputs read:** `hardware/module/pitch-stage.md`, `mod-channels.md`,
`breath-output-stage.md`, `breath-receive-stage.md` (partial),
`digital-and-supervision.md` (partial), `hardware/bom.csv`,
`docs/decisions/0006-cv-channel-allocation.md`, `0004-cv-interface-module.md`
(partial), `0003-breath-sensing-path.md` (partial).

---

## 0. Network: what I could and could not reach

Direct HTTPS fetch was refused by the egress proxy (`403` on CONNECT) for every
one of these:

- `https://doepfer.de/a100_man/a100t_e.htm` — **blocked** (also `www.doepfer.de`)
- `https://en.wikipedia.org/wiki/Eurorack`, `/wiki/CV/gate` — **blocked**
- `https://vcvrack.com/manual/VoltageStandards` — **blocked**
- `https://www.modwiggler.com/...` (all threads) — **blocked**
- `https://mutable-instruments.net/`, `https://pichenettes.github.io/...` — **blocked**
- `https://intellijel.com`, `https://www.befaco.org`, `https://www.musicthing.co.uk`,
  `https://makenoisemusic.com`, `https://www.expert-sleepers.co.uk`,
  `https://learningmodular.com`, `https://northcoastsynthesis.com`,
  `https://www.njohnson.co.uk`, `https://modulargrid.net`, `https://www.thonk.co.uk`,
  `https://sdiy.info`, `https://muffwiggler.com` — **all blocked**

Two channels did work and everything below rests on them:

1. **A search tool that returns page content** from the blocked hosts. Where I
   cite such a source I mark it `[web]` with the URL and the words *via search
   index, direct fetch blocked*. Treat those as secondary.
2. **`github.com` / `raw.githubusercontent.com`**, which were reachable. This
   let me read **primary published source** for three shipping designs —
   Mutable Instruments (`pichenettes/eurorack`), Music Thing Modular
   (`TomWhitwell/Workshop_Computer`) and Winterbloom (`wntrblm/Sol`). These are
   the strongest citations in this report: they are the actual scaling constants
   the products ship with, not a marketing page. Mutable's *schematics* are in
   that repo but are **binary Eagle `.sch`** and could not be parsed here; the
   firmware constants substitute for them and in two cases (Plaits, Warps)
   the firmware contains the input network as an arithmetic comment.

---

## 1. Correction to the brief before anything else

The tasking says pitch is *"a gain-2 non-inverting stage with a 2.500 V
intercept, giving roughly ±5 V / 10 octaves."* **The repository does not build
that.**

`[repo] hardware/module/pitch-stage.md` and `[repo] docs/decisions/0006-cv-channel-allocation.md`:

```
Vout = 2·Vdac − 2.500          (intercept −2.500 V, not +2.500 V)
Vdac 0.25 … 4.75 V  →  jack −2.000 … +7.000 V   (9.000 V, 9 octaves)
Vdac 0.00 … 5.00 V  →  jack −2.500 … +7.500 V   (10.000 V, 10 octaves)
```

So: **10 octaves is right, "±5 V" is wrong.** The window is asymmetric,
−2…+7 V in the calibrated range. Everything in §2 is judged against the repo's
numbers, not the brief's. If any downstream document has been written against
"±5 V", it is wrong and the error is 2.5 V of transposition.

---

## 2. PITCH jack

### 2.1 The 1 V/oct convention, and what 0 V means

**There is no universal reference octave.** This is the single most important
thing to get right and the repo never states it. 1 V/oct fixes the *interval*
(1 V = 1 octave, 1/12 V = 83.333 mV = 1 semitone) and says nothing about which
note sits at 0 V. Published practice, primary sources first:

| Design | What sits at 0 V | Output window | Source |
|---|---|---|---|
| Music Thing **Workshop Computer** | **MIDI note 60 (middle C)** — `MIDIToDAC()` computes from `(midiNote − 60)` against the 0 V calibration anchor | **−6 V … +6 V** | `[web] https://github.com/TomWhitwell/Workshop_Computer/blob/main/Demonstrations%2BHelloWorlds/PicoSDK/ComputerCard/ComputerCard.h` (read from a local clone) |
| Mutable **Plaits** | its note 0; calibration is taken at **C1 = 1 V** and **C3 = 3 V** | accepts **−2.86 V … +7.14 V** (derived, §2.3) | `[web] https://github.com/pichenettes/eurorack/blob/master/plaits/ui.cc` (local clone, `CalibrateC1`/`CalibrateC3`) |
| Mutable **Yarns** | 11-point table, `kNumOctaves = 11`, span `kMaxNote = 120<<7` = 10 octaves | **−3 V … +7 V** | `[web] https://github.com/pichenettes/eurorack/blob/master/yarns/voice.h` + `voice.cc` (local clone); range from `[web] https://pichenettes.github.io/mutable-instruments-documentation/modules/yarns/manual/` *(via search index, direct fetch blocked)* |
| Winterbloom **Sol** | user-calibrated table keyed in volts | **−5 V … +8 V** | `[web] https://sol.wntr.dev/` *(via search index, direct fetch blocked)*; calibration mechanism confirmed in `[web] https://github.com/wntrblm/Sol/blob/master/firmware/winterbloom_sol/_calibration.py` (fetched raw) |
| Doepfer **A-190-x** MIDI→CV | **user-selectable reference note** (A-190-9 default MIDI 36) | **0 V … +5 V** | `[web] https://doepfer.de/a100_man/A190_2_man.pdf`, `https://doepfer.de/a100_man/A190_4_man.pdf` *(via search index, doepfer.de blocked)* |

**Verdict on Woody's −2…+7 V:** it is squarely inside published practice and is
close to Yarns' −3…+7 V. It is **not** a compatibility problem. **[Note]**

**But the missing piece is real:** nowhere in the four documents I was given
does the project say *which fingering produces 0 V*. `[repo] 0006` only says
"the instrument's fingering spans roughly 2.5–3 octaves inside a 9 V output
range". A wind instrument that drives a rack must have a documented default
mapping (e.g. written C4 = 0 V), because that is the number the player uses to
set the VCO's coarse knob once and never again. **Finding P-1, Medium.**

### 2.2 Is ±5 V the right window, or 0–10 V, or 0–8 V?

For **pitch specifically**, none of these is "the" convention — the field ships
−6…+6, −5…+8, −3…+7 and 0…+5 (table above). The 0–8 V and ±5 V numbers people
quote are the **modulation** conventions (§3.1), not the pitch ones. Woody's
−2…+7 V is fine.

The one thing an asymmetric window costs: **it cannot carry the full MIDI note
range.** MIDI 0…127 is 127 semitones = **10.583 octaves** `[calc]`, so a 9 V
calibrated span cannot cover it and even the 10 V full-scale span cannot. That
only matters if the instrument is ever asked to pass external MIDI through to
the pitch jack. For its own 2.5–3 octave fingering it is a non-issue.

### 2.3 What real VCOs actually accept — and what happens at the extremes

**Primary source, and this is the best data point in the report.** Plaits'
firmware carries its own V/OCT input network as an arithmetic comment
`[web] https://github.com/pichenettes/eurorack/blob/master/plaits/ui.cc`:

```
// (-33/100.0*1 + -33/140.0 * -10.0) / 3.3 * 2.0 - 1 = 0.228     (jack at C1 = 1 V)
// (-33/100.0*1 + -33/140.0 * -10.0) / 3.3 * 2.0 - 1 = -0.171    (jack at C3 = 3 V)
```

Reading it out `[calc]`: the jack drives an inverting stage,
`V_adc = 2.3571 − 0.33·V_jack`, into a 0–3.3 V ADC. Solving the two rails:

| ADC rail | V at the jack |
|---|---|
| `V_adc = 3.3 V` | **V_jack = −2.858 V** |
| `V_adc = 0 V` | **V_jack = +7.143 V** |

**Plaits' 1 V/oct input accepts −2.86 V to +7.14 V — exactly a 10.00 V window,
and Woody's −2…+7 V sits inside it with ~0.86 V and ~0.14 V to spare.** That is
a strong independent confirmation that the chosen window is right, and it is
not luck: Woody and Plaits landed on nearly the same span because it is the
span a 10-octave 1 V/oct system needs.

Two more, same repo, giving the accepted span if not its position:

- **Rings / Elements**: `pitch_scale = −84.26` semitones over the full ADC span
  → **7.02 octaves accepted** `[calc]`
  `[web] https://github.com/pichenettes/eurorack/blob/master/rings/settings.cc`,
  `.../elements/cv_scaler.cc`
- **Warps**: `pitch_scale = −110.0` → **9.17 octaves accepted** `[calc]`
  `[web] https://github.com/pichenettes/eurorack/blob/master/warps/settings.cc`

**Analog VCOs are the tighter constraint, and they are tighter than the
converter.** Doepfer's own A-110-1 documentation is quoted as tracking
faithfully over **about 8 octaves**, with a frequency range of 15 Hz–8 kHz
(~9 octaves) `[web] https://doepfer.de/a100_man/a110_man.pdf` *(via search
index, doepfer.de blocked)*.

**So at the extremes:**

- **At +7 V** (7 octaves above base): past most analog VCOs' tracking; the top
  one to two octaves will read flat. Plaits clips 0.14 V above it. Not harmful.
- **At −2 V**: accepted by Plaits (−2.86 V limit) and by any VCO whose expo
  converter sums the CV; a unipolar-input digital module clamps at 0 V and
  simply stops going lower. Not harmful.
- **At −2.5 V** (`CLR` park, `[repo] pitch-stage.md`): subsonic, still inside
  Plaits' window. Correct behaviour.
- **At +7.5 V** (full-scale firmware reserve): **0.36 V outside Plaits' input
  window** `[calc]`. Harmless (the ADC saturates) but the reserve's top end is
  not usable with that class of module. Worth knowing, not worth changing.

**Verdict: the pitch window is correct and well-chosen. [Note, positive.]**

### 2.4 Pitch accuracy — is this competitive, over-engineered, or short?

Unit conversion first: at 1 V/oct, **1 cent = 1/1200 V = 833.33 µV** `[calc]`.

Published claims and the arithmetic behind them:

| Design | Published claim | What the arithmetic says |
|---|---|---|
| Music Thing **Workshop Computer** | *"The precision of the voltage output is roughly 5.9 mV (7 cents at 1 volt per octave)"* — `[web] https://github.com/TomWhitwell/Workshop_Computer/blob/main/Demonstrations%2BHelloWorlds/PicoSDK/ComputerCard/ComputerCard.h` (local clone, `CVOutMIDINote` docs) | 12 V span / 2048 steps = 5.86 mV = **7.03 cents** `[calc]`. The claim is exact and honest. |
| Befaco **MIDI Thing** | *"12-bit conversion that allows V/Oct control with around 1 cent precision"* — `[web] https://www.befaco.org/midi-thing/` *(via search index, befaco.org blocked)* | 12 bits over a 10 V span = 2.44 mV = **2.93 cents** `[calc]`; over 0–5 V = 1.22 mV = 1.46 cents. **"Around 1 cent" is optimistic unless the span is ≤4 V.** |
| Expert Sleepers **FH-2** | users report **~2 cents over 5 octaves** after the module's auto-calibration sweep — `[web] https://www.modwiggler.com/forum/viewtopic.php?t=200590&start=1300`, `https://www.expert-sleepers.co.uk/downloads/manuals/fh2_user_manual_1.22.pdf` *(via search index, both blocked)* | — |
| Mutable **Yarns** | 11-point per-octave table in NVS, no trimmer anywhere — `[web] https://github.com/pichenettes/eurorack/blob/master/yarns/voice.h` (`kNumOctaves = 11`) and `voice.cc` (`calibrated_dac_code_[i] = 54586 − 5133·i`, i.e. **5133 codes per octave on a 16-bit DAC**) | 1 LSB = 1/5133 octave = **0.234 cents** `[calc]` |
| **Woody** | 16-bit, ref gain 2, jack gain 2 → 10.000 V full scale | 1 LSB = 10.000/65536 = **152.6 µV = 0.183 cents** `[calc]` |

**Woody's converter resolution is the finest in this set** — 16× finer than the
Workshop Computer, ~1.3× finer than Yarns. Its static error budget as stated
`[repo] pitch-stage.md` (DAC reference 0.42 cents over 10 °C; LT5400 tracking
0.027; trimmer 0.068; INL ~0.4 cents pre-correction) puts it at roughly
**0.5–1 cent**, which is at or better than the best published number I could
find for any of the above.

**Judgement: over-engineered relative to the load, and the repo already says
so.** `[repo] 0006` concedes "a well-compensated analog VCO drifts around
0.35 cents/K, so 3.5 cents over the same 10 °C". That is the right comparison
and it is **7× the whole static budget**. Nothing here is *wrong* — it is a
one-off instrument and the parts are cheap — but **no finding should ever be
raised against this channel's static accuracy again**; the dynamic,
LED-correlated ~20-cent terms `[repo] 0006` are two orders of magnitude more
important and the repo has correctly prioritised them. **[Note.]**

### 2.5 The pitch output is NOT a 1 kΩ source, and that is a standards deviation

See §5 — this is the one genuine interop deviation on the panel.

---

## 3. MOD 1–4 jacks — ±10.000 V

`Vout = 4·Vdac − 10.000` `[repo] mod-channels.md`; full DAC span 0–5 V gives
**−10.000 … +10.000 V**, 1 LSB = 305.2 µV `[calc]`.

### 3.1 Is ±10 V a normal Eurorack level?

**It is at the extreme upper edge of normal, and it is not the convention.**

The convention, from the two most-cited published statements:

| Source | Bipolar CV | Unipolar CV | Audio | Gate |
|---|---|---|---|---|
| **Doepfer A-100** original definition | LFO **≈ −5 … +5 V**; the A-100 spec as usually quoted is LFO ±2.5 V (5 Vpp) | ADSR **0 … +8 V** | audio inputs want **≥ ~1 Vpp**, every audio input has an attenuator | typical **0/+5 V**; all A-100 modules withstand gate/trigger/clock **up to +12 V**; **>+3 V reads high, <+1 V reads low** | `[web] https://doepfer.de/a100_man/a100t_e.htm` *(via search index, doepfer.de blocked)* |
| **VCV Rack** Voltage Standards | **±5 V** | **0 … 10 V** | **±5 V** | 0 V off, **typically 10 V** on | `[web] https://vcvrack.com/manual/VoltageStandards` *(via search index, vcvrack.com blocked)* |

Primary-source confirmation from a shipping module — **Marbles**' own
calibration constants `[web] https://github.com/pichenettes/eurorack/blob/master/marbles/settings.cc`:

```
fill(&c.dac_scale[0],  ..., -6212.8f);
fill(&c.dac_offset[0], ..., 32768.0f);      // dac_code = volts·(−6212.8) + 32768
```

`[calc]` code 0 → **+5.274 V**, code 65535 → **−5.274 V**, code 32768 → **0 V**.
**Marbles' bipolar CV hardware is ±5.27 V** — a ±5 V design with 5 % of
headroom. And its own range menu is explicit
`[web] https://github.com/pichenettes/eurorack/blob/master/marbles/random/x_y_generator.h`:

```
VOLTAGE_RANGE_NARROW,    // +2V
VOLTAGE_RANGE_POSITIVE,  // +5V
VOLTAGE_RANGE_FULL       // +/- 5V
```

**±10 V does exist, in one very widely-owned module.** Make Noise Maths: Ch.1
Variable Output range **±10 V**, Ch.2 offset **±10 V**, Ch.3 offset **±5 V** —
but note that **Maths' own signal input range is stated as ±8 V**
`[web] https://www.makenoisemusic.com/wp-content/uploads/2024/03/MATHSmanual2013.pdf`
*(via search index, makenoisemusic.com blocked)*. That asymmetry is the whole
story in one module: **a ±10 V source is a real thing, and the inputs it will
meet are mostly specified for less.**

**Verdict:** ±10 V is **unconventional but not unprecedented**, and this module
is right to treat it as headroom. `[repo] 0006`'s firmware rule — *"Default
every mod and breath range to 0–8 V… Bipolar is opt-in per channel"* — is
**exactly the correct mitigation** and matches the Doepfer envelope convention
precisely. **[Note, positive.]** The residual risk is that the default is a
firmware promise on hardware that can always reach ±10 V; see §3.3.

### 3.2 What happens when ±10 V is patched into a module expecting ±5 V — quantified

**Damage risk: LOW.** Three independent lines:

1. The stated community norm: *"Any Eurorack input, for whatever purpose,
   should be able to survive any voltage within the range of the power supplies
   without damage — for example, a 0–5 V gate input should be able to survive a
   ±12 V signal"*
   `[web] https://www.modwiggler.com/forum/viewtopic.php?t=265155` *(via search
   index, modwiggler.com blocked)*.
2. Doepfer states its modules withstand gate/trigger/clock **up to +12 V**
   `[web] https://doepfer.de/a100_man/a100t_e.htm` *(via search index)*.
3. `[calc]` ±10 V into the de-facto 100 kΩ input impedance
   (`[web] https://www.modwiggler.com/forum/viewtopic.php?t=240552`, *via search
   index*) is **100 µA**. Into a module on ±12 V rails whose input clamps to its
   own rails, nothing conducts at all — 10 V is 2 V inside the rail.

**The one path that can actually hurt something**, quantified: a module whose
CV input is a *low-value* series resistor into a 3.3 V ADC pin with only the
MCU's internal clamp. With, say, 1 kΩ on their side and Woody's 1 kΩ, a +10 V
output drives `(10 − 3.9)/2 kΩ = 3.05 mA` `[calc]` into that clamp — above the
~2 mA per-pin limit many MCUs specify `[from memory]`. This is a defect in
*their* module, but it exists: a published survey found *"over half of 15
manufacturers surveyed didn't add any extra protection, or were unaware of the
problem altogether"*
`[web] https://learningmodular.com/2020-09-newsletter/` *(via search index,
learningmodular.com blocked)*.

**Misbehaviour risk (not damage): MEDIUM, and this is the real cost.**
- Into an **audio** input: 20 Vpp against the ±5 V / 10 Vpp convention is
  **+6.02 dB** `[calc]`. Doepfer notes every A-100 audio input has an
  attenuator, so it is recoverable by turning a knob.
- Into a **VCA CV** input whose unity gain is at +5 V — the commonly reported
  case `[web] https://learningmodular.com/2023-02-newsletter/` *(via search
  index)* — +10 V is **2× over unity**, which clips the VCA rather than the
  envelope.
- Into **Maths** (±8 V input range): the top 2 V of every mod channel is
  outside the specified input range.
- Into an **attenuverter** set for a ±5 V world: the useful knob range halves.

**Finding M-1, Medium.** Not "will not work with other modules"; it is
"unconventional, will clip in several common destinations, and the design has
already chosen the right default". The action is documentation, not silicon:
the per-channel range menu `[repo] 0006` should say **±5 V** and **0–8 V** as
the two named presets and put ±10 V behind a deliberate choice, and the
display/web app should show the selected range next to the channel name.

### 3.3 Where ±10 V *does* become a hardware-level problem

`[repo] mod-channels.md` documents a fault state that puts **+11.45 V on all
four mod jacks indefinitely**: firmware refreshes the five signal channels after
a `CLR` and not channel 7, so `Vout = 4·Vdac` with no offset term. `[repo]`
also documents the mirror case (offset standing, signals cleared) at **−10.00 V**
on four jacks.

Against the published survival expectation (±12 V) this is *still* survivable by
other modules `[calc: 11.45 V is 0.55 V inside the rail]`. But it is 0.55 V from
the rail on four jacks at once with nothing watching, and §6 shows there is now
no supervision left to end it. **Finding M-2, Medium** — the level itself is
tolerable; the *indefiniteness* is the problem, and it belongs to §6.

### 3.4 Mod-channel resolution and filtering, as levels

- 1 LSB = 305 µV on a 20 V span = 0.0015 % FS `[calc]`. Irrelevant for
  modulation. If a mod channel is ever used for pitch, 305 µV = **0.37 cents**
  `[calc]` at the LSB, but the ±1 % resistor tolerance quoted
  `[repo] mod-channels.md` ("about ±18 cents per octave") dominates by 50×.
  The repo's own advice — "anything pitch-like belongs on channel 1" — is right.
- `C-FILT-MOD` 82 nF against 1 kΩ = 82 µs, −3 dB at 1.94 kHz `[calc]`. Fine for
  modulation; see §4 for what it does to a gate.

---

## 4. BREATH jack

### 4.1 Is an envelope-like CV conventionally unipolar, and what do VCAs/filters expect?

**Yes, unipolar is the convention, and the number is 0–8 V.**

- Doepfer: ADSR outputs **0 V … +8 V**
  `[web] https://doepfer.de/a100_man/a100t_e.htm` *(via search index)*.
- *"The Doepfer 'envelope' spec is 8 V, used to set CV input sensitivity on
  modules so that a 0 to 8 V source should sweep the parameter over its full
  range"*; *"The CV level at which unity gain is achieved is typically 5 V, 8 V
  or 10 V"* `[web] https://modwiggler.com/forum/viewtopic.php?t=264649` *(via
  search index)*.
- VCV: unipolar CV **0–10 V**
  `[web] https://vcvrack.com/manual/VoltageStandards` *(via search index)*.
- *"For a VCA, 0 V is 'off'… any input times zero is zero"* — a negative CV into
  a VCA is simply more off `[web] https://noiseengineering.us/blogs/loquelic-literitas-the-blog/cv-what-is-it/`
  *(via search index)*.

`[repo] 0006` specifies breath as **0–10 V, offsettable ±5 V**, with a firmware
default of **0–8 V**. The 0–8 V default is exactly right. The 0–10 V ceiling
with a **panel GAIN knob 0.5–4×** is *better* than right: it is the one control
that makes a single output work into a 5 V-unity VCA, an 8 V-unity filter and a
10 V-unity digital input without a utility module. **[Note, positive.]**

Arithmetic check `[calc]` on `[repo] breath-output-stage.md`: real playing
delivers 0 → −4.69 V at the in-amp, the stage inverts with fixed ×4.02
(`R-FB` 40.2 kΩ / `R-IN` 10 kΩ, `[repo] bom.csv`) behind a 0.125–1.000
attenuator, so the jack reaches +10 V at ≈2.12× and the **0–8 V default needs
≈1.71×** — mid-travel on the knob. Good sizing.

One quiet advantage worth recording: breath **never enters the digital path on
its way out** `[repo] 0006`. Every MIDI-derived breath CV in the field is
quantised to 7-bit CC — **128 steps, 78 mV on a 10 V span** `[calc]`. Woody's
breath CV is continuous. That is a real, audible differentiator for a wind
controller and it is not stated as such anywhere I read. **[Note, positive.]**

### 4.2 Does the ±5 V offset control damage or confuse other modules?

**Damage: no.** Nothing about ±5 V on a CV jack is outside any published
expectation, and the source impedance is 1 kΩ.

**Confuse: yes, in one specific and avoidable way — and the repo's own power-on
table is wrong about it.**

`[repo] 0006` power-on table:

| Output | At rack power-on, before firmware writes |
|---|---|
| Breath | **0 V** — "The receiver's differential pulldown holds it there" |

That is true of the **in-amp output**, not of the **jack**. The offset legs sum
in *after* the gain stage `[repo] breath-output-stage.md`, so at zero breath the
jack sits at whatever the OFFSET knob says. I re-derived the endpoints from the
component values `[calc]`:

```
R-OFF 21.0k from the buffered 5.21 V wiper, R-OFFNEG 95.3k from −12 V, R-FB 40.2k
wiper 0 V    : Vjack = −40.2k · (−12/95.3k)                = +5.06 V
wiper 2.605 V: Vjack = −40.2k · (2.605/21.0k − 12/95.3k)   = +0.07 V
wiper 5.21 V : Vjack = −40.2k · (5.21/21.0k − 12/95.3k)    = −4.91 V
```

— which reproduces the repo's own +5.04 / +0.07 / −4.89 table to within a
milligram of rounding, so the circuit is right and only the ADR's power-on row
is wrong.

**Consequence:** with the OFFSET knob at full CCW and *no instrument attached at
all*, the BREATH jack sits at **+5.06 V** from the moment the rack powers up. A
VCA patched to it is wide open; a filter patched to it is parked halfway up.
**The rack makes sound at power-on with the instrument absent, and the only cue
is a knob position.** That is precisely the "surprise at first power-on" class
the ADR's bring-up section exists to prevent.

**Finding B-1, High.** It is not a damage risk and it is not a redesign — the
fixes are cheap and additive:
- correct the ADR's power-on row to *"breath jack = OFFSET knob setting; 0 V
  only at knob centre"*;
- adopt the centre-detent `POT-OFFSET` already listed as an E10 open in
  `[repo] breath-output-stage.md`, which turns "knob centred" from a hope into a
  tactile default;
- silkscreen a centre mark.

### 4.3 The combination that clips, restated as a level

`[repo] breath-output-stage.md` is already honest about this: OFFSET +5 V with
GAIN 4× demands **+23 V** at a hard blow and the OPA2197 stops at ≈±11.5 V, a
hard rail clip with no soft region. Two things to add as *standards* points:

- **+11.5 V is still a legal Eurorack level** (inside the rails, inside the
  published ±12 V survival expectation `[web] modwiggler redux, above`), so the
  clip harms nothing downstream. It is a musical problem only.
- The honest operating rule the page gives — *"the offset sets where breath
  rests, the gain sets how far it travels; their sum has to fit in ±11.5 V"* —
  should be on the **panel or the display**, not only in a repo page. A
  clipping indicator would be one comparator and one LED. **[Note.]**

### 4.4 Breath output filtering as a level/timing question

`C-OUT-BREATH` 330 nF film against 1 kΩ = 330 µs, −3 dB at 482 Hz; 10–90 % rise
= 2.197·RC = **725 µs** `[calc]`. Against the repo's own figure for the fastest
physical gesture — a hard tongue attack at **5–15 ms** rise
`[repo] docs/decisions/0003-breath-sensing-path.md` — the filter costs **5–15 %
of the attack**. That is fine. **[Note, no action.]**

---

## 5. All six jacks — source impedance and patch-level behaviour

### 5.1 The convention and why it exists

**~1 kΩ series is the de-facto Eurorack output impedance**, and it is a
*convention*, not a standard:

- *"Many synthesizer modules in all formats do indeed have a 1K output
  impedance… whether that's a 'standard' is more and more up for debate"*;
  the value is traced to a widely-copied newsletter circuit
  `[web] https://www.njohnson.co.uk/index.php?menu=2&submenu=2&subsubmenu=16`
  *(via search index, njohnson.co.uk blocked)*.
- *"Eurorack is designed around the assumption that input impedances are 'high'
  and output impedances are 'low' and as long as there's a big gap between
  those two it doesn't matter exactly what the values are"*
  `[web] https://www.modwiggler.com/forum/viewtopic.php?t=253092` *(via search
  index)*.
- The de-facto input impedance is **100 kΩ**
  `[web] https://www.modwiggler.com/forum/viewtopic.php?t=240552` *(via search
  index)*.
- Its two jobs: survive a short to ground (a 3.5 mm plug shorts tip to sleeve on
  every insertion) and survive output-to-output patching. Doepfer states plainly
  that *"a short circuit between two outputs may damage the modules"* in the
  CV/Gate bus context `[web] https://doepfer.de/a100_man/a100t_e.htm` *(via
  search index)* — which is exactly what the series resistor is there to
  prevent at the jack.

`[repo] 0004` states the convention correctly ("1 kΩ series resistors on every
CV output. Standard practice, and it means the module survives a short or
someone patching output to output").

### 5.2 What this module actually presents — and the one deviation

| Jack | DC source impedance | Shunt at the jack | Conventional? |
|---|---|---|---|
| MOD 1–4 | **1 kΩ** (`R-OUT-PROT`, outside the loop) | 82 nF | **Yes** |
| BREATH | **1 kΩ** (outside the loop) | 330 nF | **Yes** |
| **PITCH** | **≈ 0 Ω at DC** — `R-OUT-PROT` is *inside* the DC feedback loop, which is tapped at the jack `[repo] pitch-stage.md`; 1 kΩ only above the ~16 kHz handover | 10 nF | **No** |

`[calc]` with the OPA2197's open-loop gain (≈126 dB `[from memory]`, ti.com
blocked), 1 kΩ inside the loop becomes ≈0.5 mΩ at DC. The pitch jack is a
near-ideal voltage source.

### 5.3 Multing — what it costs

`[calc]`, for the five **conventional** outputs (1 kΩ outside the loop):

| Destinations on a passive mult | Load | Error |
|---|---|---|
| 1 × 100 kΩ | 100 kΩ | −0.990 % |
| 2 × 100 kΩ | 50 kΩ | −1.961 % |
| 4 × 100 kΩ | 25 kΩ | −3.846 % |

For mod and breath this is 1–4 % of a modulation depth: **irrelevant**. Had
pitch kept the resistor outside the loop it would have been **−11.88 cents per
octave** into one 100 kΩ VCO and **−23.5 cents/octave** into two `[calc]` —
which independently reproduces the repo's own −11.9 / −23.5 figures *and* the
published rule of thumb *"if the output impedance of your controller is 1 k and
the input impedance is 100 k… about 12 cents of detuning per octave in a
1 V/octave system"*
`[web] https://learningmodular.com/when-do-you-actually-need-a-buffered-multiple/`
*(via search index)*. **The jack-side tap eliminates this entirely and is the
right call. [Note, positive — this is the strongest single decision on the
panel.]**

### 5.4 Output-to-output patching — the deviation bites here

`[calc]`, **MOD vs MOD** (both 1 kΩ, worst case +10 V against −10 V):
`I = 20 V / 2 kΩ = 10 mA`, `P = 100 mW` in each 1 kΩ. Safe, benign, exactly what
the convention is for.

**PITCH against another module's output** is different, because the op-amp is
now regulating the *jack*, not its own output pin. Let the other module drive
`V_o` through its own `R_o = 1 kΩ`. To hold the jack at its target `V_t`, the
op-amp output pin must reach:

```
V_opamp = 2·V_t − V_o        [calc]
```

- `V_t = −2 V`, `V_o = +10 V` → **−14 V demanded**, op-amp rails at −11.45 V.
- `V_t = +7 V`, `V_o = −10 V` → **+24 V demanded**, op-amp rails at +11.45 V.

So the pitch stage **fights** the other module, saturates, and the jack settles
somewhere neither module intended. Current is ≈`(11.45 + 10)/2 kΩ = 10.7 mA` and
dissipation ≈115 mW in each 1 kΩ `[calc]` — nothing is damaged (and `[repo]
bom.csv` already carries a harsher case, 192 mW against a 220 Ω output, and
specifies `R-OUT-PROT` at ≥500 mW for it). But **the convention's promise is
that joining two outputs is a harmless compromise; on this jack it is a
saturating fight.** Serge did the same thing deliberately, per
`[web] https://www.modwiggler.com/forum/viewtopic.php?t=231674` *(via search
index)* — *"Serge designed modules with protection resistors inside the feedback
loop so the op amp increases its gain as load increases, staying in tune as long
as it doesn't clip"* — so this is precedented, not novel. **Finding I-1, Medium:
unconventional but not damaging; it needs a line in the manual, not a change.**

### 5.5 The cross-jack hazard that IS worth a High

`[repo] pitch-stage.md` records it and it deserves to be louder: joining PITCH
to a MOD jack (82 nF) or the BREATH jack (330 nF) through a passive mult gives
**44–67 % overshoot** — several semitones of transient on every note. On a
normal module, multing two of its own outputs together is merely pointless. On
this module it makes the pitch output ring audibly.

There is also the insertion case, already recorded: **a 3.5 mm plug shorts tip
to sleeve on insertion, and with the jack shorted the pitch DC feedback is
exactly zero and the amp rails** `[repo] pitch-stage.md`. Every patch-in is a
brief ±11.45 V excursion on the pitch jack. Into a VCO that is an audible chirp;
into a digital module's input clamp it is 11.45 V through 1 kΩ *from the
saturated op-amp* — but the 1 kΩ is back outside the loop the instant feedback
is lost, so `I ≤ 11.45 mA` `[calc]`, which is survivable everywhere.

**Finding I-2, High (operational):** "do not passive-mult PITCH with MOD or
BREATH" is a real constraint this module imposes on the patch, it does not exist
on any conventional module, and it currently lives only in a schematic page. It
belongs on the panel-adjacent documentation and in E9's test list. The
insertion-chirp is a second-order consequence of the same choice and should be
measured at E9 rather than assumed benign.

---

## 6. GATE / TRIGGER — the output that does not exist

### 6.1 The gap

**The module has six jacks — PITCH, BREATH, MOD 1–4 — and none of them is a
gate** `[repo] 0006`. The only provision is the sentence *"a gate can be
assigned to one [mod channel] if wanted"*.

Meanwhile the instrument **already computes note-on**: `[repo] 0003` —
*"Breath crossing a threshold is what starts a note"*, with hysteresis sized
against the LED-induced step in `[repo] 0014`, and a two-consecutive-samples
rule in `[repo] 0001`. **The decision exists; it has no wire to the rack.**

### 6.2 How published wind/CV interfaces handle note-on

Every source I found says the same thing: **the gate comes from breath, not from
the keys.**

- *"By MIDI design, the WX7 only transmits new note MIDI messages when breath
  voltage is high enough to pass ADC threshold"*
  `[web] https://www.modwiggler.com/forum/viewtopic.php?t=272117` *(via search
  index)*.
- A published breath-control spec states the requirement in one sentence: *"A
  Travel Sax with nothing fingered still sends C#4, so without a breath gate the
  app drones a C# the moment it is plugged in. The gate also gives the right
  articulation for free: the note starts when you blow, not when fingers land."*
  `[web] https://github.com/pepperhorn/module/pull/8` (fetched directly).
- A dedicated Eurorack module exists for exactly this: Pantala Labs **Breath
  Control**, *"a generator of gates and CV from air pressure"*
  `[web] https://modulargrid.net/e/other-unknown-pantala-labs-breath-control`
  *(via search index)*.
- Winterbloom **Sol** ships a first-class `Trigger` helper with a **15 ms**
  default pulse width alongside its gate outputs
  `[web] https://github.com/wntrblm/Sol/blob/master/firmware/winterbloom_sol/trigger.py`
  (fetched directly).
- Mutable **Yarns** has four CV *and* four gate outputs; **Marbles**' gate
  outputs are **0 V to +8 V**
  `[web] https://pichenettes.github.io/mutable-instruments-documentation/modules/marbles/manual/`
  *(via search index)*.

**Finding G-1, High.** Not a showstopper — a mod channel *can* carry it — but a
wind controller with no gate cannot drive an ADSR, a sequencer clock, a Bernoulli
gate, a drum module or a sample-and-hold without the player first understanding
and configuring the workaround. Every comparable product ships a gate as a
dedicated output. The cheapest fix is a **documented default**: Mod 1 is a
breath gate out of the box, relabelled on the write-on strip, and the display
says so.

### 6.3 If a mod channel carries the gate, the levels work — the timing mostly does

**Level: fine, and better than 5 V.** At the 0–8 V default `[repo] 0006` the
gate sits exactly on Doepfer's envelope convention and clears its ~+3 V high
threshold with margin `[web] doepfer a100t_e, via search index`. This matters
more than it looks: some Eurorack modules run CMOS on 12 V, where *"the CMOS
high threshold voltage jumps to 8 volts"*
`[web] https://www.modwiggler.com/forum/viewtopic.php?t=96737` *(via search
index)* — a +5 V gate is marginal for those, +8 V is not. **Do not let a mod
channel used as a gate default to ±5 V or 0–5 V.**

**Edge speed: acceptable.** `C-FILT-MOD` 82 nF × 1 kΩ = 82 µs `[calc]`:
- 10–90 % rise = 180 µs
- time from 0 V to cross a +3 V threshold on an 8 V step = `−82 µs·ln(1 − 3/8)`
  = **38.5 µs** `[calc]`

Both are far inside any gate input's requirements.

**Timing jitter: the real cost, and it is unflagged.** `[repo] 0006` gives pitch
*"4 kHz, plus immediate update on note change"* but gives the mod channels a
plain **4 kHz round-robin**. A gate on a mod channel therefore carries **up to
250 µs of quantisation jitter on note-on** `[calc]`, while pitch is pushed
immediately. The *ordering* is lucky and correct — pitch lands before the gate,
which is what you want — but a wind player's articulation is the thing being
judged, and 250 µs of jitter is free to remove: **if a channel is assigned to a
gate, give it the same immediate-update path pitch has.** **Finding G-2,
Medium.**

**Spurious triggers: a real one.** `[repo] bom.csv` `R-LDAC`: LDAC is tied
inactive, *"so six channels cannot update atomically — every exit from `CLR`
throws intermediate values at the mod jacks for 100–200 µs"*. A 100–200 µs pulse
is a perfectly valid Eurorack trigger. **On a gate-assigned channel, every exit
from `CLR` can fire a spurious note.** **Finding G-3, Medium** — the mitigation
is to keep the gate on a channel written first and last, or to promote LDAC to a
GPIO (`[repo]` notes the pin is already broken out).

### 6.4 What the module does when the instrument goes away — a levels failure

This is the finding I would fix first, and the repo has already found it from a
different direction. `[repo] hardware/module/digital-and-supervision.md`:

| Failure | Now |
|---|---|
| Cable unplugged mid-note | **not caught — the DAC holds and the rack drones** |
| Instrument loses power mid-note | **not caught** |
| Load switch latches off mid-note | **not caught** |

The watchdog is deleted, presence detect is deleted, `CLR` is pulled inactive
with only a manual solder pad `[repo] bom.csv R-CLR-PU`, and the six
`R-SPI-PULL` resistors specifically hold `CS` idle so the DAC **retains its last
codes** when the instrument is absent. So:

- pitch holds its last note voltage,
- all four mod jacks hold their last values — **including a gate-assigned
  channel, which holds HIGH**,
- breath falls to the OFFSET knob's voltage (§4.2), which may be **+5.06 V**.

**Pull the umbilical mid-phrase and the rack sustains a note indefinitely, at a
breath level set by a knob.** That is the exact failure the published wind-CV
practice in §6.2 exists to prevent.

**Finding G-4, Showstopper (functional, not electrical).** It is the only item
in this review I would rank there, and I rank it there *because* there is no
gate: with a real gate output the fix is trivial (the gate is the one signal
that must fail low, and a 10 kΩ pull-down on a gate jack does it for free). As
things stand, the `CLR`-safe-state argument that `[repo] mod-channels.md` builds
its whole topology around — "on a watchdog `CLR` all four jacks park at 0 V" —
**has no watchdog left to assert it.** The topology is still right; the safety
claim attached to it is currently unbacked, and the two pages disagree.

---

## 7. Findings, ranked

| ID | Output | Rank | Finding | Fails with other modules, or just unconventional? |
|---|---|---|---|---|
| **G-4** | all, via absence of a gate | **Showstopper** | Instrument unplugged / powered off / load-switch trip leaves the DAC holding its last codes: pitch holds, mods hold (a gate-assigned channel holds HIGH), breath sits at the OFFSET knob. The rack drones indefinitely. `CLR` has no driver; the watchdog and presence detect are both deleted, so `mod-channels.md`'s "parks at 0 V on `CLR`" safety claim is currently unbacked. | **Fails.** It is the classic wind-controller failure the field designs against. |
| **G-1** | (missing) GATE | **High** | No gate/trigger output exists. Every comparable design — Yarns, Marbles, Sol, Doepfer A-190, Pantala Breath Control — ships one, and every published wind interface derives note-on from breath threshold. The instrument already computes the threshold (`0003`, `0014`, `0001`); it has no wire to the rack. | **Fails** for any patch involving an ADSR, clock, S&H or drum module, until the player configures a workaround. |
| **B-1** | BREATH | **High** | ADR 0006's power-on table says the breath jack is 0 V at power-on. It is not: the offset legs sum after the gain stage, so the jack sits at the OFFSET knob's voltage — up to **+5.06 V with no instrument attached** `[calc]`. A patched VCA is wide open at rack power-on. | Unconventional + surprising. Not damaging. Fix: correct the ADR, fit the centre-detent pot already listed as an E10 open, silkscreen the centre. |
| **I-2** | PITCH ↔ MOD/BREATH | **High** | Passive-multing PITCH with a MOD (82 nF) or BREATH (330 nF) jack gives 44–67 % overshoot — several semitones of transient per note. A constraint no conventional module imposes, currently recorded only in a schematic page. Related: every plug insertion briefly rails the pitch jack (tip-to-sleeve short opens the DC loop). | Unconventional. Needs to be an operating instruction and an E9 measurement, not a footnote. |
| **M-1** | MOD 1–4 | **Medium** | ±10.000 V is at the far edge of Eurorack practice. Published convention is ±5 V bipolar / 0–8 V or 0–10 V unipolar (Doepfer, VCV); Marbles' own hardware is ±5.27 V; Make Noise Maths reaches ±10 V but specifies its *input* range as ±8 V. Into a 5 V-unity VCA, +10 V is 2× over; into an audio input, +6.02 dB over. | Unconventional, not damaging. The firmware 0–8 V default + bipolar opt-in is the right mitigation; make ±5 V and 0–8 V the two *named* presets and show the active range on the display. |
| **M-2** | MOD 1–4 | **Medium** | Documented fault states put **+11.45 V** (offset channel not refreshed) or **−10.00 V** (signals cleared, offset standing) on four jacks indefinitely. Both survive the published ±12 V expectation; the problem is that nothing ends them (see G-4). | Survivable. Fold into G-4. |
| **I-1** | PITCH | **Medium** | The pitch jack is a **≈0 Ω** DC source (1 kΩ is inside the loop), not the conventional 1 kΩ. Output-to-output patching therefore makes the stage *fight*: it must drive `2·V_t − V_o`, which rails beyond ±11.45 V, e.g. +24 V demanded for `V_t=+7`, `V_o=−10` `[calc]`. ~115 mW per 1 kΩ, nothing damaged. Serge-precedented. | Unconventional. Manual line + the ≥500 mW `R-OUT-PROT` already specified. |
| **G-2** | gate on a mod channel | **Medium** | Mod channels are round-robin at 4 kHz while pitch gets immediate update, so a gate carries up to **250 µs** of note-on jitter. Ordering is correct (pitch first); the jitter is free to remove. | Works, but articulation is the thing being judged. Give a gate-assigned channel the immediate-update path. |
| **G-3** | gate on a mod channel | **Medium** | LDAC tied inactive → every exit from `CLR` throws 100–200 µs of intermediate values at the mod jacks. That is a valid Eurorack trigger width: a spurious note. | Fails intermittently if a mod channel is a gate. Write order, or promote LDAC to the GPIO already broken out. |
| **P-1** | PITCH | **Medium** | No document states **which fingering produces 0 V**. 1 V/oct fixes the interval only; published designs put MIDI 60, MIDI 36, "C1 = 1 V" or a user-chosen note at 0 V. The player needs one documented number to set the VCO coarse knob. | Not a failure, a documentation gap. |
| — | PITCH | **Note, positive** | The −2…+7 V window (−2.5…+7.5 V at full scale) sits inside Plaits' derived input window of **−2.858…+7.143 V** `[calc]` and matches Yarns' −3…+7 V. It is correct and needs no change. |
| — | PITCH | **Note, positive** | Closing the DC loop at the jack removes the 1 kΩ/100 kΩ divider error entirely. That error would otherwise be **−11.88 cents/octave** into one VCO and **−23.5** into two `[calc]` — independently reproducing both the repo's numbers and the published ~12 cents/octave rule of thumb. Strongest decision on the panel. |
| — | PITCH | **Note** | Static accuracy (0.183 cents/LSB; ~0.5–1 cent budget) is **the best in the published field** — 16× finer than Music Thing's stated 7 cents, finer than Yarns' 0.234 cents/LSB, and ~7× inside the VCO's own 3.5 cents/10 °C drift. Over-engineered, harmlessly. Raise no further findings against it. |
| — | BREATH | **Note, positive** | 0–10 V ceiling with a 0.5–4× panel GAIN is the right answer to a field that has no single unity-gain convention (5 V / 8 V / 10 V all in use). The 0–8 V firmware default matches Doepfer's envelope spec exactly. |
| — | BREATH | **Note, positive** | Breath stays analog end-to-end, so it is continuous where every MIDI-derived breath CV is 7-bit — **128 steps, 78 mV on a 10 V span** `[calc]`. This is a genuine differentiator and is not claimed anywhere. |
| — | BREATH | **Note** | The GAIN×OFFSET combination that demands +23 V is documented in a schematic page only. It clips hard with no soft region. Put the "their sum must fit ±11.5 V" rule where the player is, or add a one-comparator clip LED. |
| — | BREATH | **Note** | 330 nF × 1 kΩ → 725 µs 10–90 % rise `[calc]` against a 5–15 ms tongue attack `[repo] 0003` = 5–15 % of the gesture. Fine. |
| — | all | **Note** | Repo inconsistencies found while checking levels, none of them level-critical: `R-OUT-PROT` is "≥250 mW" in `pitch-stage.md` and "≥500 mW" in `bom.csv`; `C-FB-PITCH` is 1 nF in the `pitch-stage.md` ASCII art and 2.2 nF in its own values table and the BOM; `R-FB` is 40k in the `breath-output-stage.md` art and 40.2k in its table and the BOM; `bom.csv R-BREATH-SUM` still says its 40.2k is "the same E96 part as `R-MODGAIN`", which became 10k/30k. |

---

## 8. What I could not check

- **TI datasheets (ti.com) are blocked**, so the OPA2197's short-circuit current
  and thermal behaviour, and the DAC8568's grade→reference-gain mapping (SBAS430,
  which `[repo] 0006` also flags as unverified), are `[from memory]` only. Every
  dissipation figure in §5.4 assumes the op-amp current-limits above ~11 mA
  rather than below it.
- **Mutable's schematics are in `pichenettes/eurorack` but are binary Eagle
  files** and could not be parsed in this environment. The input-network figures
  in §2.3 come from firmware comments, which is second-best but is primary
  source for the *numbers*.
- **Doepfer's `a100t_e.htm` was never read directly** — every quotation of it
  here reached me through a search index. It is the canonical reference for
  almost every convention in §3.1 and §4.1 and should be re-read by anyone with
  unrestricted network access before these numbers are treated as settled.
- **No measurement.** Everything here is arithmetic on stated values.
