# R1 — How published Eurorack modules build a 1 V/oct CV output from a DAC

**Date:** 2026-09-21
**Subject under review:** `hardware/module/pitch-stage.md`, with `docs/decisions/0006-cv-channel-allocation.md`
and the `R-PRECISION` / `TRIM-*` / `R-OFFINJ` / `R-OUT-PROT` / `U-OPA-PITCH` / `U-DAC` rows of `hardware/bom.csv`.

## Provenance markers

| Tag | Means |
|---|---|
| `[schematic]` | I opened and read the actual schematic sheet in this session. The file is named at the point of use. |
| `[bom]` | I opened the manufacturer's own bill of materials in this session. |
| `[source]` | I opened the firmware source file in this session. |
| `[arith]` | Arithmetic I did in this session on values that came from a `[schematic]`, `[bom]` or `[source]`. |
| `[docs]` | A vendor/community document I opened. |
| `[memory]` | I did **not** open a source. Treat as a lead, not a fact. |

**Nothing in this document is tagged `[datasheet]`.** Every semiconductor vendor site was blocked
(see *Network* below), so no datasheet was opened. Where a datasheet fact would be load-bearing I
have either derived it from a schematic plus arithmetic, or marked it `[memory]` and said so.

---

## Summary table

| # | Question | What published designs actually do | Agrees with Woody? |
|---|---|---|---|
| 1 | **Topology** | Three forms in use. **Non-inverting, reference at the bottom of the feedback divider** (Winterbloom Sol, Befaco MIDI Thing) — Woody's exact shape. **Inverting, reference on the (+) pin** (MI Yarns, Ornament & Crime). **Inverting summer, reference summed into the virtual ground** (Music Thing Workshop Computer). | **Yes.** Woody is not inventing anything; Sol is the same circuit. But the "A = 1 + B boundary" is *not* a lucky coincidence — see §1.1. |
| 2 | **Offset source** | Most common: **the DAC's own internal 2.5 V reference output**, divided down (Yarns, O&C, Sol). Next: a **negative reference** (Music Thing: TL431 shunt off −12 V; Marbles: LM4040-10). Nobody divides a bare supply rail. | **Yes, strongly.** Woody's "divide the offset from `VREFOUT`" is mainstream, and the drift-cancels-as-gain argument is provably true of Yarns too. |
| 3 | **Matched network vs discretes** | **Nobody ships a matched network.** Mutable (Yarns, Stages, Marbles) ships plain **1 % thick-film 0402/0603**. Winterbloom ships **0.1 % discretes**. O&C and Befaco ship ordinary 1 %. | **No.** Woody's LT5400 is the single most over-specified part in the design, and the gain trimmer in series with it destroys most of its benefit. |
| 4 | **Trimmers** | **Zero trimmers** in every DAC-based module I read: Yarns, Marbles, Stages, O&C, Sol, Befaco MIDI Thing, Music Thing Computer. All calibrate in firmware with an **11-point-per-channel, one-per-octave** table entered against a voltmeter. | **No.** ADR 0006's claim that "every commercial 1 V/oct module has scale and offset trimmers" is false for DAC outputs. It is true of analog VCO expo converters, which is a different circuit. |
| 5 | **Below-ground range** | Universal. Yarns **−3.000 … +7.000 V** `[arith]`, O&C **−3 … +6 V**, Sol **−5.0 … +8.0 V**, Music Thing **−6.07 … +6.06 V**. Every one of them gets it from a reference subtracted in the op-amp, never from a negative DAC. | **Yes.** Woody's −2 V is conservative by comparison. |
| 6 | **Op-amps / sequencing** | OPA4171 (Yarns, Marbles), OPA2172 (O&C), **OPA4197** (Sol), TL07x (Befaco, Music Thing, Stages). **No design has any explicit DAC→op-amp supply-sequencing protection.** The inverting designs get it free from their 10.7 k–47 k input resistor; the two non-inverting designs have none at all. | **Op-amp: yes** (Woody's OPA2197 is Sol's part). **Sequencing: Woody is ahead of prior art**, and correctly so. |
| — | **The 1 kΩ output resistor** | **Four of four designs I read put it *inside* the DC feedback loop** (feedback tapped at the jack), three of them with a single 18–22 pF feedforward cap. Woody explicitly rejected this. | **No — this is the most valuable disagreement in the document.** See §7. |

---

## Network: what I could and could not reach

Reachable: `raw.githubusercontent.com` (curl), `github.com` HTML (WebFetch only).

**Blocked by the egress proxy** — I substituted nothing for these and no claim below depends on them:
`doepfer.de`, `mutable-instruments.net`, `pichenettes.github.io` (the official MI documentation
mirror, which is where the Yarns/Marbles schematic **PDFs** live), `bgr360.github.io`,
`ornament-and-cri.me`, `modwiggler.com`, `electro-music.com`, `aisynthesis.com`,
`bartonmusicalcircuits.com`, `nonlinearcircuits.com`, `expert-sleepers.co.uk`, `befaco.org`,
`musicthing.co.uk`, `thonk.co.uk`, `ti.com`, `analog.com`, `archive.org` / `web.archive.org`,
`cdn.jsdelivr.net`, `api.github.com`.

Consequences, stated plainly:

- **No Doepfer schematics were read.** Anything about the A-190 / A-185 family is unknown to me.
- **No forum reasoning was read.** Modwiggler and electro-music were unreachable, so the "why"
  behind these choices is my inference from the circuits, not quoted from the designers — except
  where a designer wrote it on the sheet (Winterbloom and Music Thing both annotate their
  schematics, and I quote those annotations verbatim).
- **No datasheets were read.** See the provenance table.
- Mutable's own Yarns and Marbles schematics in `pichenettes/eurorack` are **Eagle 5 binary**
  (`yarns/hardware_design/pcb/yarns_v03.sch`, `marbles/hardware_design/pcb/marbles_v70.sch`). I
  could extract part and net names from them with `strings` but **not connectivity**. For Yarns I
  therefore read topology from a faithful third-party redraw
  (`TOILmodular/Yarns`, `Schematic/Schematic_Yarns.pdf`) and **cross-checked every value and part
  against Mutable's own BOM** (`yarns/hardware_design/Yarns.xlsx`) and against Mutable's own
  firmware. All three agree; the numbers close to four significant figures (§1.3). The clone's one
  deviation — it substitutes a TL074 where Mutable specifies an OPA4171 `[bom]` — is noted where
  it matters.

### Files actually opened in this session

| File | Repo / path | Used for |
|---|---|---|
| `Schematic_Yarns.pdf` | `TOILmodular/Yarns` `Schematic/` | Yarns output-stage topology `[schematic]` |
| `Yarns.xlsx` | `pichenettes/eurorack` `yarns/hardware_design/` | Mutable's own Yarns BOM `[bom]` |
| `Marbles.xlsx` | `pichenettes/eurorack` `marbles/hardware_design/` | Marbles BOM `[bom]` |
| `Stages.xlsx` | `pichenettes/eurorack` `stages/hardware_design/` | Stages BOM `[bom]` |
| `yarns_v03.sch`, `marbles_v70.sch` | `pichenettes/eurorack` | part/net-name extraction only (binary) |
| `voice.cc`, `voice.h`, `ui.cc` | `pichenettes/eurorack` `yarns/` | Yarns calibration model `[source]` |
| `o_c_rev2e_schematic.pdf` | `mxmxmx/O_C` `hardware/` | O&C full schematic `[schematic]` |
| `OC_DAC.h`, `OC_calibration.ino`, `OC_calibration.h` | `mxmxmx/O_C` `software/o_c_REV/` | O&C calibration `[source]` |
| `mainboard.pdf`, `mainboard.sch`, `precision-dac-cv-scaler.lib` | `wntrblm/Sol` `hardware/rev1/mainboard/` | Sol full schematic `[schematic]` |
| `Midi_Thing _V1_Schematic.pdf` | `Befaco/midithing` `hardware/` | Befaco MIDI Thing `[schematic]` |
| `computer_Rev_1_0_0_Schematic.pdf` | `TomWhitwell/Workshop_Computer` `documentation/` | Music Thing Computer `[schematic]` |
| `README.md` | `Befaco/midithing` | Befaco calibration lineage `[docs]` |

---

## 1. Topology

### 1.1 Woody's topology exists, shipped, and is not a numerical accident

**Winterbloom Sol** `[schematic: wntrblm/Sol hardware/rev1/mainboard/mainboard.pdf, block "Range Amplifiers"]`
is Woody's pitch stage, part for part:

```
DAC_OUT_A (AD5686, 0–2.5 V) ──────────────► (+) OPA4197 ──► R15 1k ──► CV_A jack
                                                (−)
MIDVREF 1.190 V ──[R7 2.15k 0.1%]──┬────────────┘
                                   └──[R9 9.10k 0.1%]──► (jack side of R15)
```

Gain `1 + 9.10/2.15 = 5.2326`; offset `−1.1905 × 4.2326 = −5.039 V`; so
`Vout = 5.2326·Vdac − 5.039`, i.e. **−5.04 V at zero scale, +8.04 V at full scale** `[arith]`.
The designer's own note on the sheet reads: *"Scale 0–2.5v input from DACs to −5v to +8v"* and
*"Vout max: 8.1v / Vout min: −5.1v"* `[schematic]`.

**Befaco MIDI Thing v1** `[schematic: Befaco/midithing hardware/Midi_Thing _V1_Schematic.pdf]` is the
same circuit with the bottom of the divider on ground instead of a reference: MCP4728 → (+) of a
TL072, `R16 47k` from (−) to GND, `R15 68k` feedback, `C7 22p`, `R14 1k` to the jack.
Gain `1 + 68/47 = 2.447`, unipolar 0–10 V `[arith]`.

**So the answer to "does anyone else do this" is yes, twice, and one of them (Sol) uses the same
op-amp family and the same reference strategy Woody chose.**

But the framing in `pitch-stage.md` needs correcting. The page says:

> A single-op-amp stage producing `Vout = A·Vdac − B·V_ref` can reach at most `A = 1 + B`. Here
> A = 2 and B = 1 … **exactly on that boundary**

`A = 1 + B` is not a boundary Woody's numbers happened to land on. It is the **defining identity of
this topology**: with the two-resistor non-inverting form, `Vout = Vdac(1+k) − V_ref·k`, so
`A = 1 + k` and `B = k` *identically, for every k*. The design freedom is `V_ref`, not the ratio.
Given a wanted gain `A` and a wanted offset `O`, you need

```
V_ref = O / (A − 1)
```

Woody wants `A = 2`, `O = 2.5 V` → `V_ref = 2.5 V`, which happens to equal `VREFOUT`. That is a
genuine convenience worth keeping. Sol wants `A = 5.2326`, `O = 5.039 V` → `V_ref = 1.190 V`, and
Sol simply **divided the DAC's 2.5 V down to 1.190 V with a 1.10k/1.00k 0.1 % pair and buffered it
with an OPA388** `[schematic]`. That is the general method, and it means the two-resistor
non-inverting form is reachable for *any* gain and *any* offset. It is never blocked.

**This has a direct consequence for the mod channels.** ADR 0006 says pitch "collapses to two
resistors" because A = 2, B = 1, while "the mods want A = 4, B = 4, which is off it, so they need
all four." That is only true because the mod offset was fixed at 2.5 V. `A = 4` needs `k = 3` and
therefore `V_ref = 10/3 = 3.3333 V`. The mod offset already comes from a DAC channel that can
output any voltage in 0–5 V `[docs: ADR 0006]` — so writing **3.3333 V instead of 2.5 V** at boot
collapses each mod channel to two resistors as well, in a 1:3 ratio, which is exactly three
LT5400 sections in series against the fourth. The power-on argument survives untouched: at
zero-scale reset both terms are still zero, so `Vout = 4·0 − 3·0 = 0 V`. That is out of scope for
this page, but it is free and it uses up the "two spare LT5400 resistors" the pitch page lists as
still open.

### 1.2 The inverting form, and why it is the more common one

**Mutable Instruments Yarns** `[schematic: TOILmodular/Yarns Schematic/Schematic_Yarns.pdf sheet 2/3;
every value cross-checked against pichenettes/eurorack yarns/hardware_design/Yarns.xlsx]`:

```
CHA (DAC8564 VOUTD, 0–2.500 V) ──[R25 47k]──┬──► (−) OPA4171
                                            │      (+) ◄── VREF/2 = 1.250 V
                                            ├──[C3 18p C0G]──► op-amp output
                                            └──[R26 240k]────► jack side of R27
                                                   op-amp out ──[R27 1k]──► CHA jack
```

**Ornament & Crime rev 2e** `[schematic: mxmxmx/O_C hardware/o_c_rev2e_schematic.pdf]` is the same
shape with different values: `24k9` in, `100k` feedback from the jack side of a `220 R`, `22p` to
the op-amp output, `(+)` at `V_bias = 1.25 V` from a `47k/47k` divider on the DAC8565's
`VREF_2v5`, op-amp OPA2172.

**Music Thing Workshop Computer** `[schematic: TomWhitwell/Workshop_Computer
documentation/computer_Rev_1_0_0_Schematic.pdf, sheet 2]` uses the third form — a true inverting
summer with the reference summed into the virtual ground:

```
MCP4822 out (0–2.048 V) ──[R46 10.7K]──┐
−5V_REF ─────────────────[R41 52.3K]──┴──► (−) TL074HIPWR, (+) to GND
                                        feedback R47 63.4K ∥ C28 68p
                                        output ──[R48 1k]──► jack
```
The sheet's own annotation: *"These should turn 0-2.048v from the DAC to −6.07v to +6.06v"*
`[schematic]`. My arithmetic: `Vout = −(63.4/10.7)·Vdac + (63.4/52.3)·5 = −5.925·Vdac + 6.061`
`[arith]` — agrees to the millivolt.

**Why inverting is common, and what Woody gives up by not using it.** Three things fall out of the
inverting form for free:

1. **The DAC-to-op-amp series resistor is already there.** 47 k (Yarns), 24.9 k (O&C), 10.7 k
   (Music Thing). This is exactly the "small protective part" ADR 0006 adds as `R-OPAMP-IN`.
2. **The DAC never sees an op-amp input's leakage or bias current** — it drives a resistor.
3. **You can sum more than one thing** (Music Thing sums a PWM and a reference into one node).

And what it costs, which is why Woody is right not to use it: the sign inverts, so **DAC zero-scale
becomes the top of the pitch range**. Yarns parks at **+7.63 V** and O&C at **+6.27 V** at power-on
before firmware writes `[arith]`. Woody's non-inverting stage parks below −2 V, which ADR 0006
correctly calls out as the right power-on state for pitch. That is a real, defensible reason to
differ from the more common form.

### 1.3 The Yarns numbers close exactly, which is why I trust the redraw

With `VREF = 2.500 V` (the DAC8564's own `VREFH/VREFOUT`, `ENABLE#` strapped to ground
`[schematic]`) and hence a 0–2.500 V DAC span:

```
VREF/2 = 1.250 V            (R37/R38, 47k/47k)
gain   = −240k/47k = −5.1064
Vout   = 1.250 × 6.1064 − 5.1064·Vdac = 7.633 − 5.1064·Vdac
```
- 1 V at the jack = `65536 / (5.1064 × 2.5)` = **5133.7 DAC codes** `[arith]`.
- Yarns' firmware default calibration is `calibrated_dac_code_[i] = 54586 - 5133 * i`
  `[source: yarns/voice.cc:69]` — **5133**, to the code.
- Code 54586 → `Vout = −3.000 V`; code 3256 (i = 10) → `Vout = +6.999 V` `[arith]`.
- `kNumOctaves = 11` `[source: yarns/voice.h:37]`, and `calibrated_dac_code_[3]` is commented
  `// 0V.` `[source: yarns/voice.cc:228]` — so index 3 = 0 V and the table spans −3 V to +7 V.

Four independent numbers agree. The topology and values above are safe to rely on.

---

## 2. Where the negative offset comes from

| Design | Offset source | Buffered? | Value |
|---|---|---|---|
| Yarns | **DAC8564's own internal 2.5 V `VREFOUT`**, 47k/47k divider | **No** — straight to the OPA4171 (+) pin with a 100 n `[schematic]` | 1.250 V |
| Ornament & Crime | **DAC8565's own internal 2.5 V `VREF_2v5`**, 47k/47k divider | **No** — straight to the OPA2172 (+) pin with a 100 n `[schematic]` | 1.250 V |
| Winterbloom Sol | **AD5686's own internal 2.5 V `VREF`**, 1.10k/1.00k 0.1 % divider | **Yes — a dedicated OPA388** `[schematic]` | 1.190 V |
| Befaco MIDI Thing | none — bottom of the divider is ground | n/a | 0 V (unipolar) |
| Music Thing Computer | **TL431ASA shunt reference off the −12 V rail** through `R52 3.3k`, programmed by `R53/R54` 3.3k/3.3k | shunt, not buffered | −5 V |
| Marbles | net named `AREF_-10`, part `LM4040B10` `[strings from marbles_v70.sch]` — a **−10 V reference**. Topology not confirmed; the Eagle file is binary. | unknown | −10 V |

**Nobody divides a bare supply rail.** ADR 0006's condemnation of the bare ±12 V divider is
supported by every design I read — but note *how* Music Thing solves it when it does want to work
off the rail: it does not divide, it puts a **TL431 shunt reference** in the −12 V leg. The sheet
annotation reads *"200 uA required for 4 x op amps / 3.3k gives ~2mA"* `[schematic]`. A shunt
reference's rail rejection is its dynamic impedance against the series resistor, which is a very
large number for two parts. If Woody ever needs a rail-referenced voltage again, that is the
two-part way to do it properly.

**Woody's "the drift becomes a pure gain error" argument is correct and is what Yarns does too.**
It is worth writing down that the property is not unique to the non-inverting form. For Yarns:

```
Vout = (VREF/2)(1+k) − k·Vdac,  and  Vdac = (code/65536)·VREF
     = VREF · [ (1+k)/2 − k·code/65536 ]
```

`VREF` factors out completely, so a reference drift scales the whole transfer function and produces
**zero offset error** `[arith]`. Same result as Woody's §"Why the offset reference must be
`VREFOUT`", reached from the opposite topology. This is the single strongest agreement between
Woody and established practice, and it is the reason three of the four DAC designs take the offset
from the DAC's own reference pin rather than from a separate precision part.

**Where Woody differs, correctly: buffering.** Yarns and O&C hang a 94 kΩ divider directly on the
DAC's `VREFOUT` pin, unbuffered. Woody buffers, and ADR 0006 gives the right reason: a *trimmer*
hung on `VREFOUT` would move the reference as it is turned, coupling the offset adjustment into
full scale. Sol, which also has no trimmer, nevertheless buffers with an OPA388 `[schematic]` —
so the buffer is not exotic. Keep it.

---

## 3. Matched networks versus discrete resistors

This is the clearest place where Woody is over-built relative to everything published.

| Design | Pitch-path resistors, as shipped |
|---|---|
| **Yarns** | `R18–R23` 6 × **47k 1 %** `CR0603FX-4702ELF`; `R26–R29` 4 × **240k 1 %** `CR0603FX-2403ELF` `[bom]` |
| **Marbles** | every resistor **≤1 %, 0402**, Panasonic `ERJ-2RKF` series `[bom]` |
| **Stages** | every resistor **≤1 %, 0402**, `ERJ-2RKF`; output series resistors `R34–R39` 1.0 k **0603 ≥200 mW** `[bom]` |
| **Ornament & Crime** | `24k9`, `100k`, `47k` with no tolerance called out on the sheet `[schematic]` |
| **Winterbloom Sol** | `2.15k 0.1 %`, `9.10k 0.1 %` per channel; `1.10k 0.1 %` / `1.00k 0.1 %` in the reference divider `[schematic]` |
| **Befaco MIDI Thing** | `47k`, `68k`, no tolerance on the sheet `[schematic]` |
| **Music Thing Computer** | E96 values (`10.7K`, `52.3K`, `63.4K`) with no tolerance on the sheet `[schematic]` |

**No matched network anywhere.** Not one. The highest-specified part in the whole survey is
Winterbloom's 0.1 % discrete pair.

The reason is structural, and it is worth Woody internalising: **when the gain is calibrated in
firmware, the resistors' initial accuracy is worth nothing. Only their tracking tempco matters.**
Mutable ships 1 % thick-film 0402 — whose absolute tempco is typically around ±100 ppm/°C and
uncorrelated `[memory — I could not open a resistor datasheet]` — and absorbs the result with an
11-point table. Woody's own ADR 0006 arrives at 5.4 cents over 10 °C for uncorrelated 25 ppm/°C
discretes; Mutable evidently considers something in that class acceptable against a VCO that is
itself drifting.

**And Woody then negates most of the LT5400's benefit anyway.** `TRIM-GAIN` is a cermet trimmer in
series with `R2`, i.e. **inside the ratio the LT5400 was bought to protect**, and the BOM says so:
*"Its tempco is IN the ratio and at ~100ppm/degC contributing ~5% it is the LIMITING accuracy
term, ahead of the LT5400."* `[docs: bom.csv TRIM-GAIN]`. Buying a 1 ppm/°C tracking network and
then putting a 100 ppm/°C part in series with one of its two legs is paying for precision and
immediately spending it.

Note also that `pitch-stage.md` and ADR 0006 give **two different numbers for the same term**: the
pitch page's table says `TRIM-GAIN tempco ~0.4 cents at +7 V`, while ADR 0006's trim-cost table
says a 5 % trim range gives `22 ppm/°C` and **2.4 cents** over 10 °C. Those cannot both be right.

---

## 4. Trimmers, and what the documented procedures actually are

**Every DAC-based module in this survey has zero trimmers.**

- **Yarns** — no trimpot in Mutable's BOM `[bom]`. Calibration is a front-panel mode: pick a voice,
  step through `kNumOctaves = 11` notes, adjust the stored DAC code per octave with the encoder
  against a voltmeter, save to flash `[source: yarns/ui.cc OnClickCalibrationSelectVoice /
  OnClickCalibrationSelectNote / OnIncrementCalibrationAdjustment]`. Between octaves the firmware
  interpolates linearly `[source: yarns/voice.cc NoteToDacCode]`.
- **Ornament & Crime** — no trimpot on the sheet `[schematic]`. Calibration is a boot-held menu that
  walks **DAC A/B/C/D, −3 V through +6 V in 1 V steps**, each adjusted against a voltmeter
  `[source: OC_calibration.ino, steps `DAC_A_VOLT_3m` … `DAC_A_VOLT_6`]`. Stored size is asserted
  at `sizeof(DAC::CalibrationData) == 88` `[source: OC_calibration.h:66]` = 4 channels × 11 ×
  uint16 — again **11 points per channel**.
- **Winterbloom Sol** — no trimpot on the sheet `[schematic]`. There is a test point `TP3 "MIDV"`
  on the reference node, which is the give-away: the reference is *measured*, not *adjusted*.
- **Befaco MIDI Thing** — no trimpot on the sheet `[schematic]`; the README says
  *"Calibration method inspired on Mutable instruments CVpal"* `[docs]`.
- **Music Thing Computer** — no trimpot in the CV or audio output path `[schematic]`.
- **Stages, Marbles** — the pots in the BOMs are panel controls (`10k linear pot, 15mm shaft`,
  `20k linear slide pot`), not trimmers `[bom]`.

**So ADR 0006's sentence — "which is also why every commercial 1 V/oct module has scale and offset
trimmers" — is not supported by any design I was able to open.** It is true of *analog* VCOs, whose
exponential converter has scale and offset trims because there is no digital domain to correct in.
It is not true of DAC CV outputs, where the correction is free and multi-point.

**Woody's two-step convergent procedure** (top note → gain, bottom note → offset, repeat) is the
standard analog-VCO procedure and it is correctly described. But note that Woody already has
firmware with **both** authorities — ADR 0006 resolves this explicitly: *"the 0.25–4.75 V window
reserves ±600 cents of firmware offset precisely because firmware can shift the DAC code"*, and
*"store an affine (gain, offset) pair per load preset"*. Once firmware has gain **and** offset
authority and a multi-point table, the trimmers are doing a job that is already done, with worse
tempco than the parts they are adjusting.

---

## 5. Below-ground pitch ranges

Universal, and always produced the same way: a **positive** reference subtracted (or a **negative**
reference added) inside the output amplifier. Nobody uses a bipolar DAC or a negative DAC supply.

| Design | Range at the jack | Mechanism |
|---|---|---|
| Yarns | **−3.000 … +7.000 V** `[arith]` (hardware reaches −5.13 … +7.63) | (+) pin at `VREF/2` = 1.25 V, inverting gain −5.106 |
| Ornament & Crime | **−3 … +6 V** `[source + arith]` (hardware reaches −3.77 … +6.27) | (+) pin at `V_bias` = 1.25 V, inverting gain −4.016 |
| Winterbloom Sol | **−5.04 … +8.04 V** `[arith]`, annotated "−5v to +8v" `[schematic]` | `MIDVREF` 1.190 V at the bottom of the feedback divider, non-inverting gain 5.233 |
| Music Thing Computer | **−6.07 … +6.06 V**, annotated `[schematic]` | −5 V TL431 reference summed into the virtual ground |
| Befaco MIDI Thing | 0 … +10 V | none — bottom of the divider on ground |
| **Woody** | **−2 … +7 V** | `VREFOUT` 2.500 V at the bottom of the feedback divider, non-inverting gain 2 |

Two observations.

1. **Woody's −2 V is the shallowest below-ground range in the survey.** Three of the five go to
   −3 V or lower. Nothing is wrong with −2 V for a woodwind controller, but it is worth knowing
   that it is not a conservative choice relative to practice — it is the *least* headroom anyone
   allows below zero.
2. **Every design leaves DAC codes unused at both ends.** Yarns' calibrated range uses codes
   3256…54586 of 0…65535 `[arith]` — 78 % of the converter, deliberately. Woody's 0.25–4.75 V
   window is 90 %. Woody is *less* generous with margin than Yarns, which is fine given the
   ±600 cents of firmware offset reserve, but the two documents should not both describe 90 % as
   conservative.

---

## 6. Op-amps, and whether anyone worries about supply sequencing

**Op-amp choices** `[bom]` / `[schematic]`:

| Design | CV output op-amp |
|---|---|
| Yarns | **OPA4171** (Mutable's BOM entry reads *"OPA4171 quad op-amp, low offset"*) |
| Marbles | **OPA4171** |
| Ornament & Crime | **OPA2172** |
| Winterbloom Sol | **OPA4197** (and an **OPA388** for the reference buffer) |
| Stages | TL074 |
| Befaco MIDI Thing | TL072 |
| Music Thing Computer | TL074HIPWR |

**Woody's OPA2197 is precisely Sol's part** — Sol's own KiCad library file is literally named
`precision-dac-cv-scaler.lib` and defines `OPA4180` with `ALIAS OPA4197` `[schematic]`. ADR 0006's
"OPA2197-class, not TL072" sits in the top tier of what is actually shipped. Nobody uses anything
better for a pitch output.

**Supply sequencing: nobody addresses it.**

- Yarns: DAC8564 on `+5V` (from a **REF02 used as the analog supply**, an elegant trick worth
  noting `[schematic]`), op-amps on ±12 V. Protection: the 47 k input resistor, incidentally.
- O&C: DAC8565 on `3V3_A` (LM1117-5 → ADP150-3v3), op-amps on ±12 V. Protection: 24k9, incidentally.
- Music Thing: MCP4822 on 3V3 (RT9193 off USB `VBUS`!), op-amps on ±12 V from the rack — these
  supplies genuinely can come up in either order. Protection: 10.7 k, incidentally.
- **Sol: AD5686 on +3V3, OPA4197 on ±12 V, DAC output wired straight to the (+) pin with nothing in
  between** `[schematic]`.
- **Befaco: MCP4728 on +5 V, TL072 on ±12 V, DAC output straight to the (+) pin with nothing in
  between** `[schematic]`.

So the two designs that share Woody's topology are also the two with no protection at all, and they
ship. The failure mode Woody guards against is real — with the op-amp rails at 0 V and the DAC
driving 5.21 V, the only current limit is the DAC's own short-circuit current — but the empirical
evidence is that it is survivable. `R-OPAMP-IN` is cheap insurance that prior art does not buy, and
`pitch-stage.md` is right that it costs nothing in accuracy on a (+) input. **Keep it.**

**One genuinely useful sequencing-adjacent find.** ADR 0006 spends a paragraph on getting the
DAC8568 grade letter right because *"A and C reset to zero scale; B and D reset to midscale"*, and
warns that the grade is invisible in the generic part name. **Sol's AD5686 makes this a pin:**
`RSTSEL` (pin 16) is strapped on the board `[schematic]`, alongside a `GAIN` pin (pin 10) that
selects the output span. The polarity of `RSTSEL` I cannot confirm `[memory]`, but the existence of
the strap is on the sheet. ADR 0006 already lists the AD5676 as an alternative to the DAC8568; if
the power-on state is as load-bearing as the ADR says, choosing a part where it is a solderable
strap rather than a letter in an order code removes a whole class of procurement error — and makes
it *changeable* after fab, which the grade letter is not.

**Also worth copying:** Yarns strapped the DAC8564's `ENABLE#` pin low in hardware `[schematic]`, so
its internal reference is on from power-on with no firmware write. That is the hardware answer to
the trap ADR 0006 flags (*"the internal reference is disabled by default … a board that looks dead
at E7 with every channel reading 0 V"*). The DAC8568 has no such pin `[memory]`, so Woody's
software-enable is unavoidable with that part — but the AD5676/AD5686 family is again worth a look.

---

## 7. The finding: everyone puts the output resistor *inside* the feedback loop

This is the one place where established practice exists because of a failure mode Woody has
considered and then dismissed.

`docs/decisions/0006` says:

> Feeding the op-amp's feedback from the jack side eliminates the error properly but puts the patch
> cable's capacitance inside the loop, and the correct compensated version of that (TI's
> dual-feedback topology) has to be designed as one piece with the output filter it replaces. That
> is real stability work, on a board without one, to fix something a screwdriver already fixes.

**Four of four designs I read do exactly this**, and three of them "design it as one piece" with a
single capacitor:

| Design | Output R | DC feedback tapped | HF feedback |
|---|---|---|---|
| Yarns | `R27 1k` | **jack side** of R27, via `R26 240k` | `C3 18p C0G` from (−) to the **op-amp output** |
| Ornament & Crime | `220 R` | **jack side**, via `100k` | `22p` from (−) to the **op-amp output** |
| Befaco MIDI Thing | `R14 1k` | **jack side**, via `R15 68k` | `C7 22p` from (−) to the **op-amp output** |
| Winterbloom Sol | `R15 1k` | **jack side**, via `R9 9.10k` | **none** |
| Music Thing Computer | `R48 1k` | op-amp side (feedback before the 1 k) | `C28 68p` across the feedback resistor |
| **Woody** | `R-OUT-PROT 1k` | **op-amp side** | none (the 10 nF is outside, to ground) |

All four of Yarns, O&C, Befaco and Sol are `Riso`-inside-the-loop. Yarns, O&C and Befaco are the
textbook **dual-feedback** form — the resistor keeps the load's capacitance off the op-amp's output
node at high frequency, while the DC loop still closes at the jack, so the load divider error is
**zero by construction**. It is one 18–22 pF capacitor. It is not "real stability work"; it is a
cap that three separate designers chose independently, in the same value decade, for the same
reason.

**What this costs Woody, in Woody's own numbers** `[docs: ADR 0006]`:

- 100 kΩ load → −11.9 cents/octave, 59.4 cents at five octaves.
- 50 kΩ load → −23.5 cents/octave, 117.6 cents at five octaves.
- Re-patching from one VCO to two on a passive mult → ~58 cents at five octaves.
- The mitigations bought instead: calibrate with the real patch; use a buffered mult; store a
  per-load affine `(gain, offset)` pair; a named preset per patch with a display line; and the
  gain trimmer's whole ±5 % range exists to absorb this one error (`bom.csv TRIM-GAIN`:
  *"+-5% of the 10k ratio, which is what the output resistor's load divider needs"*).

That is a user-visible operating procedure, a firmware feature, a display page and a trimmer's
entire range, traded against one capacitor.

**The honest complication, and it is real.** Woody wants a 10 nF reconstruction filter to ground at
the jack (15.9 kHz). None of the four in-loop designs has a capacitor to ground at the jack at all
— their only pole is in the feedback (`18p‖240k` = 36.8 kHz on Yarns, `22p‖100k` = 72 kHz on O&C
`[arith]`). So Woody cannot simply copy them: 10 nF at the jack inside the loop is a much larger
capacitive load than a cable, and the feedforward cap would have to be sized against it. Two ways
out, both used in the field:

- **Move the pole into the feedback.** `Cf ‖ R2` at 1 nF across 10 kΩ gives 15.9 kHz `[arith]` —
  the same corner ADR 0006 specifies, in the place Yarns and O&C put theirs, and it band-limits the
  DAC's steps before the 1 kΩ rather than after. The 10 nF to ground then disappears and the 1 kΩ
  can go inside the loop with a small feedforward cap. This is the configuration all three of
  Yarns, O&C and Befaco are in.
- **Keep the 10 nF and keep the 1 kΩ outside the loop** — Woody's current design — and accept the
  per-load calibration. Music Thing does this (feedback before the 1 k, `68p` across the feedback
  resistor) and is the one design in the survey that agrees with Woody here.

Either is defensible. What is not defensible is the sentence in ADR 0006 that treats the in-loop
option as exotic and expensive. It is what most of the field ships.

---

## 8. Arithmetic checks on `pitch-stage.md` itself

These came out of trying to compare Woody's circuit with the others, and each is independent of the
prior art.

### 8.1 The drawn schematic puts `TRIM-GAIN` in parallel with `R2`, not in series

Read literally, the ASCII drawing has both `R2 10k` and `TRIM-GAIN 1k` connected between the
inverting node and the op-amp output node:

```
                                     ├───[R2 10k]──────────┘        │
                                     │    LT5400                    │
                                     └───[TRIM-GAIN 1k cermet]──────┘
```

Both right-hand stubs land on the output net. In parallel, `10k ∥ 1k = 909 Ω` and the gain becomes
1.09, not 2. The component table and `bom.csv` both say **in series with R2**, which is clearly the
intent. The drawing contradicts both. Since the whole point of the page is that drawing the
schematic changed the answer, the drawing should be the thing that is right.

Related, and worth one line in the procedure: when a trimmer sits in a feedback path as a rheostat,
**tie the wiper to one end**, so a dirty or lifted wiper degrades to the end resistance instead of
opening the feedback loop.

### 8.2 `R-OFFINJ` adds ~1.06 % of gain, and the offset trim range is one-sided

In Woody's non-inverting stage the inverting node is **not** a virtual ground — it sits at `Vdac`,
which moves from 0.25 V to 4.75 V. Injecting through `R-OFFINJ` into that node therefore is not a
pure offset. Summing currents at the (−) node with `R1 = R2 = 10k`, `R3 = R-OFFINJ = 470k`, wiper
voltage `Vw`:

```
Vout = Vdac·(1 + R2/R1 + R2/R3) − V_ref·(R2/R1) − Vw·(R2/R3)
     = Vdac·2.02128 − 2.500 − Vw·0.021277
```
`[arith]`

Two consequences.

- **The nominal gain is 2.0213, not 2.000** — a +1.06 % gain error built into the topology, which
  `TRIM-GAIN` must absorb before it does anything else.
- **The offset trim span is 0 → −53.2 mV, not ±53 mV.** `Vw` runs 0…2.5 V, so the injected term is
  one-sided. As a ± figure it is **±26.6 mV ≈ ±32 cents about a centre that is itself 26.6 mV below
  nominal**, not the "±53 mV ≈ ±64 cents" claimed in both `pitch-stage.md` and the
  `R-OFFINJ` BOM row. The magnitude 53.2 mV is right; calling it "±" is not.

This is still a workable trim — ±32 cents is ample against the errors it has to absorb — but the
asymmetry should be written down, because a trimmer that can only move one way is a trap at
calibration time. If bipolar trim is wanted, the clean fix is to return the low end of
`TRIM-OFFSET` to a buffered negative reference rather than ground. (Do **not** return it to the
−12 V rail through a large resistor; that reintroduces precisely the rail coupling ADR 0006 removed.)

### 8.3 `TRIM-GAIN` is also one-sided

`R2 = 10k` fixed plus `0…1k` in series gives a gain range of **2.000 → 2.100**, i.e. **0 % to +5 %**
— not ±5 % as `pitch-stage.md` and the BOM both say. Combined with §8.2 the achievable gain is
2.0213 … 2.1213, i.e. **+1.06 % to +6.1 % of nominal, with no downward authority at all**.

For the one job the range was sized for — absorbing the `R-OUT-PROT` load divider, which always
*reduces* the delivered gain — one-sided-upward is the correct direction, so this happens to work.
But if the LT5400 pair, the DAC reference or the op-amp come out on the high side, the trimmer
cannot reach. That is fine only because firmware has gain authority too, which is another way of
saying the trimmer is redundant with firmware.

### 8.4 The two error tables use two different pivot points

`pitch-stage.md`'s error table gives "Gain, 100 ppm: 0.24 cents at −2 V, 0.84 cents at +7 V" —
that is `100 ppm × |Vout|`, i.e. a gain error pivoting about **Vout = 0 V**. That is correct for a
`VREFOUT` drift, where (as the page itself proves) the whole transfer function scales.

It is **not** correct for a resistor-ratio drift, which is what the `TRIM-GAIN` and LT5400 rows in
the same table describe. With `Vout = Vdac(1+k) − V_ref·k`, a drift in `k` alone gives
`dVout = (Vdac − V_ref)·dk`, which pivots about `Vdac = V_ref = 2.5 V`, i.e. **Vout = +2.5 V**. At
100 ppm of `k = 1`, that is ±225 µV at the two ends of the 0.25–4.75 V window — about ±0.27 cents,
symmetric `[arith]`, rather than growing monotonically to +7 V.

The practical effect is that the LT5400 and trimmer terms are smaller than the table implies in the
middle of the range and symmetric at the ends. It does not change any decision; it does mean the
table is currently mixing two different error mechanisms under one heading.

---

## What Woody should change

1. **Fix the drawing: `TRIM-GAIN` is drawn in parallel with `R2`.** (§8.1) Read literally the stage
   has a gain of 1.09. Also tie the trimmer's wiper to one end.

2. **Correct the offset trim range to 0 → −53 mV (±32 cents about a displaced centre), and record
   the +1.06 % gain that `R-OFFINJ` adds.** (§8.2) Both `pitch-stage.md` and the `R-OFFINJ` BOM row
   currently say "±53 mV ≈ ±64 cents", which is twice the achievable adjustment and wrong about the
   sign symmetry. If bipolar offset trim is actually wanted, return the low end of `TRIM-OFFSET` to
   a buffered negative reference, not to ground and not to the rail.

3. **Correct `TRIM-GAIN` to 0…+5 %, not ±5 %.** (§8.3) It has no downward authority.

4. **Delete the claim that "every commercial 1 V/oct module has scale and offset trimmers."** (§4)
   Seven published DAC-based CV modules — Yarns, Marbles, Stages, Ornament & Crime, Sol, Befaco
   MIDI Thing, Music Thing Computer — have none. The claim is true of analog VCO expo converters
   and is being applied to the wrong circuit. It is currently load-bearing for the decision that
   reversed "no trimmers anywhere", so it should be replaced by an argument that survives.

5. **Reconsider the LT5400, or reconsider the trimmer — but not both.** (§3) A 1 ppm/°C tracking
   network with a 100 ppm/°C cermet in series with one of its two legs is self-cancelling, and
   `bom.csv` already concedes the trimmer is "the LIMITING accuracy term, ahead of the LT5400". The
   published alternatives are: 0.1 % discretes and no trimmer (Sol), or 1 % thick film and no
   trimmer (Mutable, everywhere). Pick one lane. If the trimmers stay, two 0.1 % discretes plus
   firmware is what the evidence supports and it deletes a 0.65 mm-pitch MSOP and the unresolved
   option-code question the page lists as "still open".

6. **Reconcile the two different values given for the `TRIM-GAIN` tempco term** — 0.4 cents in
   `pitch-stage.md`, 2.4 cents in ADR 0006 — and separate reference drift (pivots about
   Vout = 0 V) from ratio drift (pivots about Vout = +2.5 V) in the error table. (§8.4)

7. **Revisit the in-loop output resistor, or at least soften the ADR's reasoning about it.** (§7)
   Yarns, Ornament & Crime, Befaco and Sol all tap DC feedback at the jack; three of them
   compensate with a single 18–22 pF cap. Woody trades that capacitor for a per-load calibration
   preset, a display page, an operating instruction and the trimmer's entire range. The clean
   version for Woody is to move the 15.9 kHz pole into the feedback (`Cf = 1 nF ‖ R2 10k`) instead
   of to ground at the jack, which is exactly where Yarns and O&C put theirs, and then bring the
   1 kΩ inside the loop. If the 10 nF-to-ground stays, the decision is defensible — Music Thing
   does the same — but the ADR should say "we chose the other tradeoff", not "that option is real
   stability work".

8. **Look at a DAC whose power-on reset state is a pin rather than a grade letter.** (§6) Sol's
   AD5686 straps `RSTSEL` and `GAIN` on the board. ADR 0006 already lists the AD5676 as an
   alternative, and spends a paragraph on the risk that the grade letter is invisible in the
   generic part name. A strap is also *changeable after fab*, which a grade letter is not.

9. **Two small factual corrections.** ADR 0006 says Yarns uses twelve calibration points; it uses
   **eleven** (`kNumOctaves = 11` `[source: yarns/voice.h:37]`), spanning −3 V to +7 V, one per
   octave, linearly interpolated. And Yarns straps its DAC's `ENABLE#` pin low in hardware so the
   internal reference is live at power-on `[schematic]` — worth citing next to the DAC8568
   reference-enable trap, because it shows the trap is a property of the part choice, not of DACs.

10. **Optional, out of scope for this page but free: collapse the mod channels to two resistors
    too.** (§1.1) `A = 4` needs `V_ref = 10/3 V`; the mod offset already comes from a writable DAC
    channel. Write 3.3333 V instead of 2.5 V at boot and each mod channel becomes a 1:3 two-resistor
    non-inverting stage — three LT5400 sections in series against the fourth, which also gives the
    "two spare resistors" a job. The zero-scale power-on-at-0 V property is unaffected.

---

## What Woody should keep, and why the difference is justified

1. **The non-inverting topology with the reference at the bottom of the feedback divider.**
   Winterbloom Sol is the same circuit with the same op-amp family, and it is the right choice for
   Woody for a reason Sol does not share: **the power-on state**. The inverting form used by Yarns
   and Ornament & Crime parks pitch at the *top* of the range at zero-scale reset — +7.63 V and
   +6.27 V respectively `[arith]`. ADR 0006 explicitly wants pitch parked subsonic. Inverting is
   more common; non-inverting is correct here.

2. **Taking the offset from the DAC's own `VREFOUT`.** Three of the four DAC designs that need a
   reference take it from the DAC's own reference pin. Woody's *reason* — that reference drift then
   becomes a pure gain error and never an offset error — is provably true of Yarns as well, and
   is the best-argued paragraph in `pitch-stage.md`. Keep the paragraph.

3. **Buffering that reference.** Yarns and O&C do not buffer, but neither has a trimmer hanging on
   it; Sol has no trimmer either and buffers anyway. Woody's stated reason — a trimmer on
   `VREFOUT` would modulate full scale as it is turned — is sound and specific to Woody's design.

4. **`R-OPAMP-IN`, the 1 kΩ on the (+) input.** No published design does this: the two that share
   Woody's topology (Sol, Befaco) wire the DAC straight to the (+) pin, and the inverting designs
   get protection incidentally from a 10 k–47 k input resistor. But Woody's DAC sits on 5.21 V, the
   op-amps on ±12 V from a different regulator, and the argument in ADR 0006 is correct. It costs
   nothing on a (+) input. This is a place where a one-off can afford to be better than the field.

5. **One op-amp part number throughout, and that part being OPA2197-class.** This is the top tier of
   what anyone ships — Sol's `precision-dac-cv-scaler.lib` defines the very same OPA4197
   `[schematic]`. Mutable uses OPA4171 on its precision outputs and TL074 where it does not care.
   Woody uses the precision part everywhere, which on a one-off with nine op-amp halves is a
   sensible refusal of a commercial compromise.

6. **BAV99 over BAT54S at the jacks.** Marbles and Stages both ship `BAT54S` `[bom]` — but neither
   has it on a precision pitch output, and Woody's arithmetic (2 µA of Schottky leakage through
   1 kΩ = 2 mV = 2.4 cents, temperature-dependent) is exactly the reason not to copy them there.
   This is a well-reasoned, correct departure.

7. **C0G on the pitch filter cap, on the jack side of the series resistor.** Mutable specifies
   `>= 50V, <= 2%, C0G` for the four 18 pF feedback caps in Yarns `[bom]` — the same care, on the
   same node's equivalent. The X7R/piezoelectric argument in ADR 0006 is right and should stay.

8. **Concentrating precision on channel 1 only.** Stages and Marbles both run their non-critical
   outputs on 1 % 0402 and a TL074 `[bom]`. Woody's split — precision on pitch, ordinary parts on
   the mods — is exactly what Mutable does, and for the same reason.

9. **The multi-point firmware table.** Yarns: 11 points, one per octave, linear interpolation
   between anchors `[source]`. Ornament & Crime: 11 points per channel, entered against a voltmeter
   `[source]`. Woody's "roughly one point per octave" is the right number and the right shape.
   ADR 0006's instruction to **anchor the two-point fit inside the musically used range** rather
   than at −2 V and +7 V is better practice than either of them, which both anchor at their
   extremes.

10. **Trimming with the real patch connected, and preferring a buffered mult.** Given that Woody
    keeps the 1 kΩ outside the loop, these are the correct mitigations, and the ADR's insistence on
    a *two-number* affine correction rather than a scale factor is a genuinely subtle point that no
    published design I read documents at all. If §7's recommendation is declined, this section of
    ADR 0006 is the thing that makes the decline safe, and it should stay exactly as written.
