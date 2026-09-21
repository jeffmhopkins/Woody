# R4 — What published Eurorack modules put between an op-amp and an output jack

**Date:** 2026-09-21 · **Scope:** prior art only. This is not a review of Woody
and it does not try to justify Woody's choices.

## Evidence key

| Marker | Means |
|---|---|
| `[schematic]` | A schematic or netlist I opened in this session. The file is named. |
| `[BOM]` | A bill of materials I opened and parsed in this session. The file is named. |
| `[docs]` | Vendor design documentation I opened in this session. |
| `[search]` | A web-search result *snippet* only. The page itself was unreachable. Weak. |
| `[calc]` | Arithmetic I did here from numbers marked above. |
| `[from memory]` | Not verified in this session. Treat as a lead, not a fact. |

**Network:** only `github.com`, `raw.githubusercontent.com` and `git clone` over
HTTPS were reachable. **Blocked by the egress proxy (confirmed, not guessed):**
`doepfer.de`, `modwiggler.com`, `thonk.co.uk`, `aisynthesis.com`,
`mutable-instruments.net`, `pichenettes.github.io`, `ornament-and-cri.me`,
`northcoastsynthesis.com`, `web.archive.org`, `ti.com`, `mouser.com`,
`digikey.com`, `octopart.com`, `tdk.com`, `lcsc.com`. So: **no Doepfer
schematics, no modwiggler threads, no Thonk build docs, no TI or passive-component
datasheets were read.** Where those were the only possible source, I say so
rather than filling the gap.

Twelve independent published designs were opened. Mutable's own schematics are
binary Eagle 5 files that cannot be parsed, so Mutable appears here through its
published BOMs plus one third-party recreation, and I flag exactly where that
limits the claim.

---

## Findings vs Woody

| # | Woody (as committed) | What published designs actually do | Verdict |
|---|---|---|---|
| 1 | "Every CV output gets a 1 kΩ series resistor — standard Eurorack practice" (`bom.csv` R-OUT-PROT, ADR 0006) | **There is no single standard value.** Opened: 1 kΩ (Mutable ×7 modules, Yarns, Befaco Midi Thing, Befaco Muxlicer analog, Music Thing Computer, Erica MIDI-CV, Super Synthesis, Telex TXo, Winterbloom Sol + C&P), 470 Ω (all 8 Expert Sleepers analogue modules), 220 Ω (Ornament & Crime, westlicht Per\|Former CV), 120 Ω (Befaco Muxlicer gates) | **Woody's value is the most common, but the claim "standard" is overstated.** 1 kΩ is right for Woody; see #2 for why. |
| 2 | 1 kΩ on pitch, load-divider error absorbed in calibration; reviewers wanted 100 Ω | **Nobody senses from the jack. Nobody compensates.** But the two DAC-driven precision-CV modules split the value by channel type: **Per\|Former = 220 Ω on CV, 1 kΩ on gates; O&C = 220 Ω on CV.** That split is exactly the trade Woody's reviewers were pointing at, made by two designers, silently. | **Partly a real miss.** 1 kΩ→220 Ω cuts the uncalibrated load error 4.5× (−11.9 → −2.6 cents/oct). But it also raises short-circuit dissipation 4.5×, and *Mutable and Winterbloom both explicitly uprate the 1 kΩ's power rating* — which is the published reasoning Woody was looking for. See #1 detail. |
| 3 | 1 kΩ, 0805, **no power rating in the BOM** | **Mutable specifies `≤1%, ≥200 mW` for its output 1 kΩ while every other resistor is 100 mW** `[BOM]`. **Winterbloom marks its output 1 kΩ `150mW/5%` while every signal resistor is `100mW/1%`** `[schematic]`. Two designers independently uprate exactly this part. | **Change.** Woody's mod channel at ±10.05 V into a short is 101 mW in an 0805 typically rated 125 mW. Works, but the margin is unstated and it is the one resistor in the design whose job is to be abused. |
| 4 | BAV99 clamp to **±12 V rails**, on the **jack side** of the 1 kΩ, on **all six** outputs | **No design I opened clamps a CV output to the supply rails.** Protection devices at jacks do exist, but: Winterbloom puts a **bidirectional ESD device to GND at the pitch CV *input***; Mutable fits a **TDK B72500D160H60 CeraDiode** (bidirectional ceramic ESD suppressor, to GND) at jacks in its post-2018 modules; Erica Synths fits **BAT85 Schottky to GND on gate/clock outputs only**, and — importantly — on the **driver side** of the 1 kΩ. | **Change the placement, keep the part.** Woody's leakage argument for BAV99-over-BAT54S is correct *given the placement*, but the placement is what creates the error. Move the clamp inside the loop and the error is identically zero. Also, ±12 V rail clamps back-power a dead module; GND clamps cannot. |
| 5 | Reconstruction RC **between the resistor and the jack** (1 kΩ + 10 nF pitch / 82 nF mod / 330 nF breath); ADR 0006 says the in-loop `Cf` and the output filter "are physically the same part and cannot both exist" | **All six DAC/PWM-driven designs do both, and none of them has a capacitor on the jack side.** Every one puts a small lead capacitor **across the feedback resistor** and then a bare series resistor to the jack: Telex TXo 82 pF/81.6 kΩ (**annotated "Fc = ~24 kHz"**), Per\|Former 18 pF/100 kΩ (88 kHz), O&C 22 pF/100 kΩ (72 kHz), Yarns 18 pF/240 kΩ (37 kHz), Befaco Midi Thing 22 pF/68 kΩ (106 kHz), Winterbloom C&P 18 pF/33 kΩ (**annotated "Output low-pass corner: 220 kHz"**). | **The stated conflict is false.** A cap *across the feedback resistor* is not a capacitive load on the output; it raises phase margin. Woody declined a fix it did not need to decline. Woody's *placement* is still fine for stability — the problem is the value and the package (#6). |
| 6 | `C-FILT-MOD 82 nF C0G/NP0, 0805`; `C-FILT-PITCH 10 nF C0G/NP0, 0805` | Where prior art filters hard, it does it **upstream of the output amplifier**: Erica MIDI-CV puts 1 kΩ + **2.2 µF** on the DAC output *before* the scaling amp; Music Thing uses a **two-pole active multi-feedback** filter and documents changing from Sallen-Key to MFB "for reduced 60 kHz ripple" `[docs]`. | **Change.** 82 nF in C0G/NP0 in an 0805 is almost certainly not a buyable part `[from memory — vendor sites blocked, MUST VERIFY]`, and a general C0G dielectric spec returned by search puts 0805 C0G maxima at single-digit nF `[search]`. Woody's dielectric call is right; the package has not caught up with it. |
| 7 | Jacks: PJ398SM ("De facto eurorack standard. Standard panel hole") | Published designs name **five different parts**: PJ-301-M-12 (Mutable, all modules `[BOM]`), WQP-PJ301BM (Befaco, westlicht), PJ301M (O&C), WQP518MA (Super Synthesis, with datasheet), PJ398SM (Winterbloom), **Cliff 3.5 mm** (all Expert Sleepers). | **Mostly fine, with one correction.** Winterbloom's own C&P names *PJ398SM* in the schematic and lays it out on a footprint named *AudioJack_WQP518MA*, whose pads are **pad-for-pad identical** to Sol's *WQP-PJ301M-12* footprint: T(0,−5), switch(0,+3.5), sleeve(0,+6.5), 1.1 mm drills. So PJ398SM / PJ301M / WQP518MA are one footprint in practice. Cliff is not. |
| 8 | Output-to-output patching and shorts to ground cited as the reason for the resistor | **Every single output in all twelve designs has a current-limiting element.** Zero direct op-amp-to-jack connections. Where there is no series resistor (Music Thing pulse out), the limit comes from a 10 kΩ pull-up instead. | **Keep.** This is the one place where Woody's "standard practice" claim is fully supported. |

---

## Detail

### 1. The series resistor: what real modules ship

Every value below was read off a schematic or BOM opened in this session.

| Design | Source file opened | Analog / CV out | Gate / trigger out |
|---|---|---|---|
| Mutable Marbles v7.0a, Stages v7.0, Tides2, Plaits v5.0, Ripples v9.0, Shades | `pichenettes/eurorack */hardware_design/*.xlsx` `[BOM]` | **1.0 kΩ, 0603, ≤1 %, ≥200 mW** — count equals output count in each module | — |
| Mutable Yarns v0.3 | `yarns/hardware_design/Yarns.xlsx` `[BOM]` (10 × 1.00 kΩ, 4 × 18 p C0G, 4 × 240 k, 6 × 47 k) | **1 kΩ** | **1 kΩ** |
| Befaco Midi Thing v1.1 | `Befaco/midithing hardware/Midi_Thing _V1_Schematic.pdf` `[schematic]` | **1 kΩ** (R14/R13/R11/R5) | **1 kΩ** (R111/R109/R107/R105/R104/R102) |
| Befaco Muxlicer v1.2 | `Befaco/muxlicer hardware/muxlicer_v1_2.pdf` `[schematic]` | **1 kΩ** (R24, COMMON) | **120 Ω** (R11/R26/R27) behind a 1k8 pull-up |
| Music Thing Workshop Computer Rev 1.0.0 | `TomWhitwell/Workshop_Computer documentation/computer_Rev_1_0_0_Schematic.pdf` sheet 3/5 `[schematic]` | **1 kΩ** (R55, R3) | none — 10 k pull-up / 15 k divider sets the limit (sheet 5/5) |
| Erica Synths DIY MIDI-CV v1.1 | `erica-synths/diy-eurorack Midi-CV DIY.zip → DIY_MIDI_CV_v1_1.pdf` `[schematic]` | **1 kΩ** (R23/R24/R25) | **1 kΩ** + BAT85 to GND |
| Super Synthesis EG rev1 / S&H / 2OPFM rev5 | `supersynthesis/eurorack Production Modules/…` `[schematic]` | **1 kΩ** (R25; R18/R8; R23) | **220 Ω** on EOC (R35) + 1 k pulldown + 1N4148 to GND |
| Ornament & Crime rev2e | `mxmxmx/O_C hardware/o_c_rev2e_schematic.pdf` `[schematic]` | **220 Ω** (DAC8565 → OPA2172 → 220 R → PJ301M) | — |
| westlicht Per\|Former v1.0 | `westlicht/performer-hardware sequencer.pdf` sheets 7/8 + 8/8, `dac.sch`, `jacks.sch` `[schematic]` | **220 Ω** (R43/R24/R23/R42/R64/R53/R52/R63) | **1 kΩ** (R68…R86) |
| Telex TXo | `bpcmusic/telex hardware/TELEXo/board/Telex-O Schematic.pdf` sheet 1/2 `[schematic]` | **1 kΩ** (R20/R17/R16/R14) | **1 kΩ** (R102…R105) |
| Winterbloom Sol rev1 | `wntrblm/Sol hardware/rev1/mainboard/mainboard.sch` `[schematic]` | **1 kΩ** (R15/R21/R14/R20) | **1 kΩ** (R10…R13) |
| Winterbloom Castor & Pollux v5 | `wntrblm/Castor_and_Pollux hardware/mainboard/mainboard.pdf` sheet 5/8 `[schematic]` | **1 kΩ, 150 mW, 5 %** (R56/R54/R55, R61) | — |
| Expert Sleepers Otterley, Cicely, Amelia, Pandora, Lorelei, Beatrix, Persephone | `expertsleepersltd/hardware analogue/*/*_A_v1*.sch` `[schematic]` | **470 Ω on every output, nothing else on the net** | **470 Ω** |

**The published reasoning, finally.** Two designers wrote it into the parts
themselves rather than into prose, and it is the same reason in both cases:

- Mutable specifies the output 1 kΩ as **`≤1 %, ≥200 mW`, 0603** while every
  other 0402/0603 resistor in the same BOM is a 100 mW part. Marbles even uses
  a *separate line item* for a 1.0 kΩ 0402 100 mW elsewhere (R68) — so the
  uprating is deliberate and only applies to the output parts. `[BOM:
  marbles/hardware_design/Marbles.xlsx, stages/…, tides2/…, plaits/…,
  ripples/…, shades/…]`
- Winterbloom marks the output 1 kΩ **`150mW/5%`** on the schematic while every
  signal-path resistor on the same sheet is marked `100mW/1%`.
  `[schematic: Castor_and_Pollux mainboard.pdf 5/8]`

That is the whole argument for 1 kΩ over 100 Ω, expressed as a power rating
`[calc]`:

| R_out | Error into 100 kΩ | Into 50 kΩ (2 VCOs multed) | I into a dead short at 11 V | P in R | P in the op-amp |
|---|---|---|---|---|---|
| 1 kΩ | −11.9 ¢/oct | −23.5 ¢/oct | 11 mA | **121 mW** | 121 mW |
| 470 Ω | −5.6 | −11.2 | 23 mA | 257 mW | 234 mW |
| 220 Ω | −2.6 | −5.3 | 50 mA | **550 mW** | 500 mW |
| 120 Ω | −1.4 | −2.9 | 92 mA | 1.01 W | 0.9 W |
| 100 Ω | −1.2 | −2.4 | 110 mA | 1.21 W | 1.1 W |

(Error per octave is `1200·(k−1)` where `k = R_load/(R_load+R_out)`. Woody's
−11.9 and −23.5 reproduce exactly.)

So the 100 Ω the reviewers asked for costs a **1.2 W** resistor and demands ~110 mA
from the op-amp — beyond an OPA197-family part's ±65 mA output-current spec
`[search — ti.com blocked, not read as a datasheet]`. That is why nobody ships
100 Ω. **220 Ω is the value the two precision-CV DAC modules actually chose**, and
neither of them uprated the resistor, i.e. they accepted that a sustained short
is a fault condition rather than a design case.

### 2. The load divider: nobody fixes it

Across all twelve designs: **no remote sensing, no jack-side feedback, no
compensation of any kind.** The only visible response to the problem is the
channel-type split — 220 Ω where the output is a pitch CV, 1 kΩ where it is a
gate — in Per|Former `[schematic: jacks.sch + dac.sch]` and O&C `[schematic:
o_c_rev2e_schematic.pdf]`. Neither states a reason, but the split has no other
explanation: a gate does not care about 1 % and a 1 V/oct output does.

A modwiggler snippet recommends "avoid putting series resistors in outputs
outside the feedback loop … allow op-amps to compensate" `[search — page
blocked]`. **Twelve out of twelve published designs do the opposite.** Treat the
snippet as a forum opinion, not as practice.

**VCO 1 V/oct input impedance — measured off schematics, since Doepfer is
blocked:**

| Module | Input network | Z_in |
|---|---|---|
| Super Synthesis 2OPFM rev5 (V/OCT jack) | R17 **100 kΩ 0.1 %** → inverting node of U10.2, R15 33 k 0.1 % feedback, C10 1 n `[schematic: 2OPFM_REV5_SCHEMATIC.pdf sheet 2]` | **100 kΩ** |
| Winterbloom Castor & Pollux v5 (CASTOR/POLLUX PITCH) | R4/R6 **100 kΩ** → MCP6004 summing node, R12/R13 48 k7 feedback, VREF−10 via 162 k `[schematic: mainboard.pdf 3/8]` | **100 kΩ** |
| westlicht Per\|Former (CV1–4 IN) | R46/R26/R27/R45 **100 kΩ** → MCP6004, 200 k to AREF−10 V, 33 k + 1 n feedback `[schematic: jacks.sch]` | **100 kΩ** |
| Ornament & Crime rev2e (CV1–4) | **100 kΩ** → MCP6004, 75 k to OFFSET, 33 k + 330–560 p feedback `[schematic: o_c_rev2e_schematic.pdf]` | **100 kΩ** |
| Super Synthesis EG rev1 (CV) | R8 **100 kΩ** `[schematic: EG_REV1_SCHEMATIC.pdf]` | **100 kΩ** |
| Expert Sleepers (all analogue modules, every input jack) | **4 k7** series at the jack, then the input network `[schematic: analogue/*/*_A_v1*.sch]` | set downstream; jack sees 4 k7 in series |

**Woody's 100 kΩ assumption is well founded** — five independent 1 V/oct-capable
inputs, all exactly 100 kΩ. **I could not verify Doepfer A-110/A-111
specifically; doepfer.de is blocked.** Do not cite Doepfer numbers from this
document, because I do not have them.

### 3. Clamp diodes at the jack

**They exist, and they are on inputs.**

- **Winterbloom Castor & Pollux v5**: D3–D6, drawn as bidirectional devices and
  labelled **"ESD"**, sit **directly on the jack tip** of every CV input,
  clamping **to GND**, upstream of the 100 kΩ. The outputs on sheet 5/8 have
  **nothing** — just 1 kΩ. `[schematic: mainboard.pdf 3/8 and 5/8]`
- **Mutable**, post-2018: an **EPCOS/TDK B72500D160H60 CeraDiode** (a
  bidirectional multilayer-ceramic ESD suppressor, ~16 V) appears at jacks in
  Plaits (8), Tides2 (8), Ripples v9 (6), Marbles (7), Stages (6), Shades (6),
  Blades (13) `[BOM]`. Yarns (2013), Braids, Clouds, Frames, Rings, Warps have
  **none** — so this is a generational change, not a house style from the start.
  **Placement caveat:** counts match the *input*-jack count in Plaits (8/8),
  Ripples (6/6) and Tides2 (8/8); Marbles (7) and Shades (6) are ambiguous. The
  Mutable schematics are binary Eagle 5 files and **cannot be parsed**, so I
  cannot state placement, only that the part is fitted at jacks and is
  bidirectional to GND.
- **Erica Synths DIY MIDI-CV v1.1**: **BAT85 Schottky, cathode to the output
  node, anode to GND**, on GATE1, GATE2 and CLOCK — and **on the driver side of
  the 1 kΩ**, so the 1 kΩ limits whatever an abuser injects into the diode. The
  **CV outputs have no clamp at all.** `[schematic: DIY_MIDI_CV_v1_1.pdf]`
- **Music Thing Workshop Computer**: BAT54S is used for the **normalisation
  probe** on the input jacks' switch contacts, not for outputs `[docs: Computer_
  Rev 1 Documentation.pdf, "GPIO4 Normalisation Probe … via a BAT54S protection
  diode"]`.
- **Super Synthesis EG rev1**: a single 1N4148W to GND on the **EOC** output,
  after a 220 Ω `[schematic]`.
- **Expert Sleepers** (8 modules): **no protection device on any jack, input or
  output.** Just 470 Ω out / 4 k7 in. `[schematic]`

**So: is Woody's Schottky-leakage argument written down anywhere else? No.** I
found no published discussion of clamp-diode leakage on a pitch output — because
nobody else clamps a pitch output. The argument is sound arithmetic (2 µA × 1 kΩ
= 2 mV = 2.4 ¢) and Woody's conclusion (silicon, not Schottky) follows. But:

> **The leakage error is an artefact of Woody's placement, not of the diode.**
> Woody's `D-JACK-CLAMP` is on the jack side of `R-OUT-PROT`, so the
> temperature- and signal-dependent net leakage develops a voltage across the
> 1 kΩ, outside the feedback loop. Move the clamp to the **op-amp side** of the
> 1 kΩ — Erica's arrangement — and the op-amp sources or sinks the leakage with
> its loop gain: **output error identically zero, for any diode.** The 1 kΩ then
> also sits between an abusing external source and the diode, which is what the
> diode needs.

**And one failure mode practice avoids that Woody does not mention:** every
protection device above clamps **to GND**. Woody's clamp to **±12 V** is a
conduction path from any patched-in signal into Woody's own rails when the
module is unpowered. Concretely: a neighbouring 220 Ω-output module (O&C,
Per|Former) driving +10 V into an unpowered Woody jack pushes ≈45 mA through the
BAV99 into the dead +12 V rail; six jacks ≈ 270 mA `[calc]`. That rail also
feeds the LM317, the op-amps and, per ADR 0004, the **umbilical to the
instrument**. Partial-power states on op-amps and MCUs are exactly what this
class of clamp is famous for. A bidirectional device to GND cannot do it.

### 4. Output filtering: where the pole goes

**Nobody puts a capacitor on the jack side of the series resistor.** Zero of
twelve. Every DAC- or PWM-driven design puts the pole either **inside the
feedback loop** (a lead capacitor across the feedback resistor) or **upstream of
the output amplifier**:

| Design | Pole | Where |
|---|---|---|
| Telex TXo | **~24 kHz** — the sheet is literally titled *"CV Outs (1-4) [Fc = ~24kHz]"*; 82 pF across 81 k6 `[schematic]` | across the feedback resistor |
| Winterbloom C&P output amps | **"Output low-pass corner: 220 kHz"** annotated on the sheet; 18 pF across 33 k. The same sheet annotates **"Output impedance: 1 kOhm"** `[schematic]` | across the feedback resistor |
| Winterbloom C&P waveform mixer | **"Output low-pass corner: 88 kHz"**; 18 pF across 100 k `[schematic]` | across the feedback resistor |
| westlicht Per\|Former | 18 pF across 100 k ≈ 88 kHz `[schematic: dac.sch]` | across the feedback resistor |
| Ornament & Crime | 22 pF across 100 k ≈ 72 kHz `[schematic]` | across the feedback resistor |
| Mutable Yarns | 18 pF C0G across 240 k ≈ 37 kHz `[BOM]`, matched component-for-component by a third-party recreation `[schematic: TOILmodular "MI Yarns" rev 1.0 sheet 2/3 — third-party clone, weaker evidence]` | across the feedback resistor |
| Befaco Midi Thing | 22 pF across 68 k ≈ 106 kHz `[schematic]` | across the feedback resistor |
| Music Thing Computer (PWM, 60 kHz) | 330 pF across 270 k ≈ 1.8 kHz, **plus** 75 k + 2 n2 ≈ 1 kHz ahead of the amp — a **two-pole active MFB** filter, documented as changed from Sallen-Key "for reduced 60 kHz ripple" `[schematic + docs]` | in the loop and before it |
| Erica Synths DIY MIDI-CV | 1 kΩ + **2.2 µF to GND on the DAC output**, before the scaling amp `[schematic]` | upstream of the amplifier |

Two things follow for Woody.

**(a) ADR 0006's claim that "the in-loop `Cf` and the separate output filter are
physically the same part and cannot both exist" is wrong, and the decision built
on it should be revisited.** They are different parts in different places. A cap
from the op-amp output to ground *is* a capacitive load and *can* oscillate —
Woody is right about that and right to have avoided it. A cap **across the
feedback resistor** is a lead network that *adds* phase margin. Seven designs
above have both a feedback lead cap and a series output resistor; several
annotate both corners on the drawing.

**(b) No DAC-driven module filters the zero-order-hold image at the output.**
Corners run 24 kHz–220 kHz, i.e. well *above* the update rate. Woody's
1.94 kHz on mod and 15.9 kHz on pitch are far more aggressive than anything in
the corpus. That is not automatically wrong — Woody's mod sources genuinely run
to 400 Hz at a 4 kHz update, which is an unusual combination — but it is a
*departure*, and the one design that does filter hard (Music Thing, PWM at
60 kHz) built an **active two-pole filter inside the amplifier** rather than a
passive RC after the series resistor, and iterated its topology to get the
ripple down.

**The practical consequence Woody has not costed:** putting the pole on the jack
side makes the capacitor large, and C0G at 82 nF is not an 0805 part.

### 5. Output-to-output patching and shorts

- **Twelve designs, zero direct op-amp-to-jack connections.** The limiting
  element is always present: 120 Ω–1 kΩ of series resistance, or (Music Thing
  pulse outs, Per|Former clock outs) a 10 kΩ / 1 kΩ pull-up on an open-collector
  stage with the jack taken straight off the collector `[schematic]`.
- **Two outputs patched together** puts the two series resistors in series.
  Worst case, two 1 kΩ outputs at opposite rails: 22 V / 2 kΩ = 11 mA, 121 mW in
  each resistor `[calc]` — survivable by both, which is the point of the value.
  A 220 Ω output against a 1 kΩ output: 18 mA, 71 mW in the 220 Ω. Also fine.
  The case that actually bites is **a short to ground**, which is why Mutable
  and Winterbloom uprated the part (see #1).
- Community position, from search snippets only (`modwiggler.com` blocked):
  "1 kΩ resistors are typically used in series with outputs, which is normal in
  eurorack"; "connecting two outputs together results in the series resistances
  adding up"; "well designed modules should tolerate any possible patching up to
  rail voltage, but this may not be true with smaller resistors" `[search]`.
  Consistent with the schematics, but I could not read the threads.

### 6. Jacks

| Named part | Used by | Source |
|---|---|---|
| PJ-301-M-12 | Mutable, *every* module | `[BOM: braids/clouds/edges/elements/kinks/rings/warps …xlsx]` |
| PJ-301-B | Mutable Streams | `[BOM]` |
| WQP-PJ301BM | Befaco Midi Thing, westlicht Per\|Former | `[schematic]` |
| PJ301M | Ornament & Crime | `[schematic]` |
| PJ301M-12 | Winterbloom Sol jackboard | `[schematic: jackboard.pretty/WQP-PJ301M-12_JACK.kicad_mod]` |
| WQP518MA | Super Synthesis (with datasheet in-repo, filed as "Thonkiconn Jack") | `[datasheet: supersynthesis/eurorack Production Modules/_datasheets/WQP-WQP518MA - Thonkiconn Jack.pdf]` |
| PJ398SM | Winterbloom Castor & Pollux (schematic symbol datasheet URL) | `[schematic]` |
| Cliff 3.5 mm PCB switched | **all eight** Expert Sleepers analogue modules | `[schematic: CLIFF3.5MM_PCB_SW_JK]` |

**Interchangeability, verified pad-for-pad in this session:** Castor & Pollux's
symbol points at the *PJ398SM* datasheet, and its PCB places
`winterbloom:AudioJack_WQP518MA`. That footprint's pads are
`T (0, −5) · TN (0, +3.5) · S (0, +6.5)`, 1.1 mm drills — **byte-identical
coordinates** to Sol's separately-authored `WQP-PJ301M-12_JACK` footprint
`[schematic: wntrblm/Winterbloom_KiCad_Library
footprints/winterbloom.pretty/AudioJack_WQP518MA.kicad_mod` vs `wntrblm/Sol
hardware/rev1/jackboard/jackboard.pretty/WQP-PJ301M-12_JACK.kicad_mod]`. So one
designer treats PJ398SM, PJ301M and WQP518MA as one footprint, and the pads
agree.

**Not universal, though.** Sol's own library also carries
`Jack_3.5mm_QingPu_WQP-PJ3010B`, whose pads are at completely different
positions with 2.8 × 1.2 mm oval drills — so "WQP-PJ3xxx" is *not* one
footprint. And the Cliff part is mechanically different entirely. Woody's
"standard panel hole" is right (6 mm threaded bushing, 4.5 mm thread on the
WQP518MA drawing `[datasheet]`); "de facto standard" for the *footprint* is true
for the PJ301/PJ398/WQP518 family only.

**No known-issues evidence.** Thonk build documents and modwiggler are both
blocked, so I have **nothing** on the reliability complaints (loose nuts, thin
thread, switch contact reliability) that circulate about these parts. Do not
treat this section as covering that.

---

## What Woody should change

1. **Move `D-JACK-CLAMP` to the op-amp side of `R-OUT-PROT`, and clamp to GND,
   not to ±12 V.** Two independent wins, both free at layout:
   - Diode leakage moves inside the feedback loop → the 2.4-cent
     temperature-dependent pitch error becomes **zero** instead of merely small,
     and the BAV99-vs-BAT54S argument stops mattering at all (keep BAV99
     anyway — same price).
   - The 1 kΩ then limits the current an external source can push into the
     diode, and — the bigger one — **a GND-referenced clamp cannot back-power
     Woody's rails or the umbilical when the module is unpowered.** ±12 V rail
     clamps on six jacks can deliver ~270 mA into a dead rail from
     220 Ω-output neighbours `[calc]`. Precedent: Erica Synths puts BAT85 on the
     driver side of its 1 kΩ; Winterbloom and Mutable clamp to GND.
   - If you prefer a single part: a bidirectional ceramic ESD suppressor to GND
     (the TDK B72500D160H60 class Mutable uses on every post-2018 module) does
     the job with no rail connection at all. **Verify its capacitance and
     leakage before putting it on the pitch jack — I could not, tdk.com is
     blocked.**

2. **Fix `C-FILT-MOD`'s package, and check `C-FILT-PITCH`'s.** 82 nF C0G/NP0 in
   0805 is very unlikely to be a purchasable part; C0G's permittivity puts that
   value in 1210/1812 at any useful voltage `[from memory — MUST VERIFY, vendor
   sites blocked]`. A general C0G spec table returned by search gives 0805 C0G
   maxima in the single-digit nF `[search]`. Either accept the larger package
   (as `C-OUT-BREATH` already does: "1206 or THT") or **move the pole where
   everyone else puts it** — see 3.

3. **Reconsider the reconstruction filter's location, since the reason for
   rejecting the alternative was wrong.** ADR 0006 declined the in-loop `Cf` on
   the grounds that it and the output filter "are physically the same part and
   cannot both exist." They are not. Seven published designs have both, and two
   of them annotate both corners on the schematic. A lead capacitor across the
   feedback resistor is not a capacitive load; it improves phase margin. If the
   mod channels really need a 2 kHz pole, the corpus says build it **in or
   before the amplifier** (Music Thing's two-pole MFB; Erica's 1 k + 2.2 µF on
   the DAC output) — which also removes the 82 nF-at-the-jack problem in #2 and
   keeps the output impedance purely resistive.

4. **Put a power rating on `R-OUT-PROT` in the BOM.** It is the only resistor in
   Woody whose design case is being shorted. A mod channel at ±10.05 V into a
   dead short is 101 mW in a part typically rated 125 mW `[calc]`. Mutable
   specifies ≥200 mW; Winterbloom specifies 150 mW; both call it out explicitly
   against 100 mW elsewhere. Copy them: `1 kΩ, 1 %, ≥200 mW, 0805`.

5. **Revisit 220 Ω for pitch only — with the power number attached, not without
   it.** The reviewers who asked for 100 Ω were over-reaching; 100 Ω is 1.2 W
   and ~110 mA, which no op-amp in this class will hold. But **220 Ω is what
   both DAC-driven precision-CV modules in the corpus actually use on their
   1 V/oct outputs, while keeping 1 kΩ on their gates** (Per|Former explicitly:
   220 Ω CV, 1 kΩ gate). It cuts the uncalibrated load error from −11.9 to
   −2.6 ¢/oct, i.e. from 59 cents to 13 cents at five octaves. The cost is
   550 mW into a sustained short, which needs a 1 W part or an accepted
   fault-condition. This is a real, documented fork in practice, and ADR 0006
   currently presents the 1 kΩ choice as if there were no fork.

6. **Soften the claim in `bom.csv`.** "Standard eurorack practice" for 1 kΩ is
   defensible as a plurality but not as a standard: 470 Ω is the house style of
   an entire commercial product line, and 220 Ω is the choice of the two designs
   closest to Woody's architecture.

7. **Check the mod channels' edge rate against what a gate needs.** ADR 0006
   allows a gate to be assigned to a mod channel; 1 kΩ + 82 nF gives a
   10–90 % rise of ~180 µs `[calc]`. Probably fine, but it is not written down
   anywhere and no prior-art module has anything like it at its output.

## What Woody should keep

1. **1 kΩ on the mod and breath outputs.** Dead centre of practice, and the
   power-dissipation argument (#1 above, Mutable's ≥200 mW, Winterbloom's
   150 mW) is exactly the published reasoning Woody was looking for. Woody
   reached the right value; it just has better support than it knows.

2. **The capacitor on the jack side rather than the op-amp side, *as stated*.**
   The specific hazard Woody names — a shunt capacitor directly on an op-amp
   output, inside the loop, as a capacitive load — is real, and calling an
   unspecified placement "a functional hazard rather than a tidiness complaint"
   is correct. Nothing in the corpus contradicts it. (What the corpus
   contradicts is the *other* claim, that this forbids a feedback lead cap.)

3. **C0G/film, never X7R.** Unanimous where visible: Mutable specifies C0G for
   every timing/filter capacitor and X5R only for bypass `[BOM]`; Winterbloom
   and Telex mark their lead caps C0G-class values. The DC-bias and
   piezoelectric arguments in ADR 0006 are right, and the microphonic-detuning
   point on a pitch filter is a good one that nobody else seems to have written
   down.

4. **Silicon rather than Schottky, if the clamp stays where it is.** The
   arithmetic holds. If recommendation 1 is taken the argument becomes moot,
   which is a better outcome than winning it.

5. **Calibrating with the real load connected, and the buffered-mult
   recommendation.** Nobody in the corpus compensates for the load divider —
   they all leave it to calibration, and the ones with the smallest resistors
   still eat −2.6 ¢/oct. Woody's affine `(gain, offset)` per-load preset is
   *more* than anyone else does, and the analysis that a single scale factor
   turns a progressive error into a constant transposition is correct and, as
   far as I can find, unpublished elsewhere.

6. **PJ398SM.** Footprint-compatible with PJ301M and WQP518MA, verified
   pad-for-pad above. The panel hole claim is right.

7. **A series resistor on every output, no exceptions.** Twelve of twelve.

---

## What I could not establish

- **Doepfer A-110 / A-111 input impedance and the A-100 "Technical Details"
  statement about 1 kΩ output resistors.** `doepfer.de` is blocked. The 100 kΩ
  figure in this document comes from five other schematics, not from Doepfer.
- **Mutable's clamp *placement*.** The `.sch` files are binary Eagle 5. BOM
  counts suggest inputs; I cannot confirm.
- **B72500D160H60 capacitance and leakage.** tdk.com blocked. Needed before
  copying it onto a pitch output.
- **OPA2197 short-circuit current and thermal behaviour.** ti.com blocked; the
  ±65 mA figure above is a search snippet, not a datasheet read.
- **82 nF / 10 nF C0G availability in 0805.** All distributor sites blocked.
  Flagged as a lead, not a fact.
- **Thonk build documents and modwiggler threads** — both blocked, so there is
  no community-practice evidence in this document beyond search snippets.
