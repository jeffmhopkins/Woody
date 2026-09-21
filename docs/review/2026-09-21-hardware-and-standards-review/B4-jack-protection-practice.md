# B4 — Output jacks and jack protection, against published Eurorack practice

**Reviewer:** cold comparative review, 2026-09-21. No prior `docs/review/**` or
`docs/research/**` was read. Everything below is either a primary schematic I
opened myself, a number I calculated, or a clearly-marked memory claim.

**Scope:** the six output jacks of the 8HP CV module — `PITCH`, `MOD 1–4`,
`BREATH` — and everything between an op-amp output pin and the tip of a
PJ398SM.

**Repo sources read:** `[repo] hardware/module/pitch-stage.md`,
`[repo] hardware/module/mod-channels.md`,
`[repo] hardware/module/breath-output-stage.md`,
`[repo] hardware/module/power-entry.md`,
`[repo] hardware/module/digital-and-supervision.md`,
`[repo] hardware/bom.csv`,
`[repo] docs/decisions/0004-cv-interface-module.md`,
`[repo] docs/decisions/0006-cv-channel-allocation.md`.

---

## 0. What the module actually has at each jack

From `[repo] hardware/module/pitch-stage.md`, `[repo] mod-channels.md`,
`[repo] breath-output-stage.md`, `[repo] hardware/bom.csv`:

| Jack | Driver | Series R | Where DC feedback is taken | Cap on the **jack** side | Clamp | Jack |
|---|---|---|---|---|---|---|
| PITCH | ½ OPA2197, G=2, −2…+7 V (−2.5…+7.5 V full scale) | `R-OUT-PROT` 1 kΩ | **at the jack** (R2 10 k + 200 Ω trim spans jack → (−)) | `C-FILT-PITCH` **10 nF C0G** | BAV99 to ±12 V, driver side | PJ398SM |
| MOD 1–4 | ½ OPA2197, G=4, ±10.00 V | `R-OUT-PROT` 1 kΩ | at the **op-amp output** (R2 30 k) | `C-FILT-MOD` **82 nF** | BAV99 to ±12 V, driver side | PJ398SM |
| BREATH | ½ OPA2197 summer, G=4 fixed after panel attenuator | `R-OUT-PROT` 1 kΩ | at the **op-amp output** (`R-FB` 40.2 k) | `C-OUT-BREATH` **330 nF film** | BAV99 to ±12 V, driver side | PJ398SM |

Additionally `[repo] pitch-stage.md`: `C-FB-PITCH` 2.2 nF from the op-amp
**output** to the (−) input — the HF half of a split feedback loop. No jack
uses the PJ398SM switch contact.

---

## 1. What the field actually puts between an op-amp and a 3.5 mm output jack

I opened twelve published designs (eleven modules plus Mutable's BOM evidence across five). **Every one of them puts exactly one thing
there: a bare series resistor.** Not one puts a capacitor on the jack side of
it. Not one puts a TVS on an output. Two put clamp diodes on the *driver* side.
Nobody uses series diodes. Nobody uses a dedicated protection network.

| Design | Driver | **Series R** | Feedback tap | Cap at jack | Clamp at output | Source |
|---|---|---|---|---|---|---|
| Mutable **Plaits** | op-amp | **1.0 kΩ, `<=1%, >=200mW`, 0603** (R46/R47 — *everything else on the board is 0402 100 mW*) | — | none in BOM | none in BOM | `[web] https://raw.githubusercontent.com/pichenettes/eurorack/master/plaits/hardware_design/Plaits.xlsx` |
| Mutable **Marbles** | op-amp | **1.0 kΩ, `>=200mW`, ×7** (R45,46,62,63,85,86,87 — Marbles has exactly 7 outputs) | — | none in BOM | none in BOM | `[web] https://raw.githubusercontent.com/pichenettes/eurorack/master/marbles/hardware_design/Marbles.xlsx` |
| Mutable **Stages** | op-amp | **1.0 kΩ, `>=200mW`, ×6** (R34–R39) | — | none in BOM | none in BOM | `[web] https://raw.githubusercontent.com/pichenettes/eurorack/master/stages/hardware_design/Stages.xlsx` |
| Mutable **Veils** | op-amp | **510 Ω, `<=5%, 250mW`, ×4** (R94–R97) | — | none in BOM | none in BOM | `[web] https://raw.githubusercontent.com/pichenettes/eurorack/master/veils/hardware_design/Veils.xlsx` |
| Mutable **Yarns** | OPA4171 | 1.0 kΩ ×10 / 100 Ω ×18, all 0603 1 % | — | none in BOM | none in BOM | `[web] https://raw.githubusercontent.com/pichenettes/eurorack/master/yarns/hardware_design/Yarns.xlsx` |
| **Ornament & Crime** rev2e | OPA2172, inverting 24k9/100k | **220 Ω** | **at the jack** (100 k) **+ 22 pF from the op-amp output** | none | none | `[web] https://raw.githubusercontent.com/mxmxmx/O_C/master/hardware/o_c_rev2e_schematic.pdf` |
| Westlicht **PER\|FORMER** | OPA4172, inverting 24k/100k, DAC8568 | **220 Ω** | **at the jack** — *both* the 100 k and the 18 pF | none | none | `[web] https://raw.githubusercontent.com/westlicht/performer-hardware/master/dac.sch` |
| Winterbloom **Sol** | OPA4197, non-inverting 2k15/9k10 | **1 kΩ** | **at the jack side of the 1 kΩ**, no compensation cap at all | none (jackboard has **zero** components) | none | `[web] https://raw.githubusercontent.com/wntrblm/Sol/master/hardware/rev1/mainboard/mainboard.pdf` and `.../jackboard/jackboard.sch` |
| **MTM Workshop Computer** rev 1.0.0 | TL074H inverting | **1 kΩ** (R55/R3 CV, R48/R51 audio) | op-amp output, with 330 pF / 68 pF lead cap | none | none | `[web] https://github.com/TomWhitwell/Workshop_Computer/blob/main/documentation/computer_Rev_1_0_0_Schematic.pdf` |
| **Erica Synths DIY MIDI-CV** v1.1 | TL074 non-inverting 10k/10k | **1 kΩ** (R23/R24/R25) | op-amp output, with 22 pF lead cap | none | none on CV; **BAT85 to GND and to +5 V on the *driver* side** of the gate/clock 1 kΩ | `[web] https://github.com/erica-synths/diy-eurorack/raw/master/Midi-CV%20DIY.zip` → `Midi-CV DIY/DIY_MIDI_CV_v1_1.pdf` |
| Befaco **Muxlicer** v1.2 | DG408 mux | **1 kΩ** (R24 on COMON) | n/a | none | none | `[web] https://raw.githubusercontent.com/Befaco/muxlicer/master/hardware/muxlicer_v1_2.pdf` |
| **HAGIWO** Quantizer | MCP4726 DAC direct | **470 Ω** (CV out and TRIG out) | n/a | none | **BAT43 pair to +5 V / GND on the *driver* side** | `[web] https://raw.githubusercontent.com/ijnekenamay/HAGIWOs_Module/master/Quantizer/original_schematic.jpg` |

**The count, answering the question directly:**

- **A single series resistor: 12 of 12.** No exceptions.
- **Resistor value:** 1 kΩ in 7 designs, 220 Ω in 2, 510 Ω in 1, 470 Ω in 1.
  **1 kΩ is the mode.**
- **Resistor + capacitor to ground at the jack: 0 of 12.**
- **Series diodes: 0 of 12.**
- **A dedicated protection network (TVS / ESD array) on an output: 0 of 12.**
- **Clamp diodes at the output: 2 of 12** (Erica gate/clock, HAGIWO), both on
  the **driver** side of the series resistor — the same side this module put
  them on.
- **Nothing at all between op-amp and jack: 0 of 12.**

**Why the consensus is "one resistor":** the resistor is a *fuse*, not a
filter. Mutable's BOMs prove it out loud — the output 1 kΩ is the **only**
resistor on the board specified for power. Plaits/Marbles/Stages use 0402,
`<=1%, 100mW` for every resistor in the design and then break package and
specify `<=1%, >=200mW` 0603 for precisely the output resistors, seven of them
on Marbles for seven output jacks. `[repo] hardware/bom.csv` already asserts
this about Mutable; **it is correct, and I verified it independently on four
Mutable BOMs.**

---

## 2. The 1 kΩ convention — origin, what it buys, what it costs

**Origin.** `[from memory]` The 1 kΩ output / 100 kΩ input pairing is the
Doepfer A-100 house style, carried into Eurorack wholesale; the ancestry is
ARP-era output mixing resistors. I could not cite it: `doepfer.de` is blocked
by this sandbox's egress proxy (see §9). `[web]` A web search returns the same
statement — "100k input impedance and 1k output impedance is considered
standard practice among most builders, as much as any standard exists in
Eurorack", and attributes the 1 kΩ ancestry to the ARP 2500/2600 — but every
page carrying it (modwiggler.com, northcoastsynthesis.com) is also blocked, so
treat that as secondary.

**What it protects against** `[calc]`, with OPA2197 on this module's
±11.55 V analog rails (`[repo] power-entry.md`: 1N5817 + ferrite off the rack
±12 V):

| Fault | Through 1 kΩ | Through 220 Ω (the O&C / PER\|FORMER convention) |
|---|---|---|
| Output at +10 V shorted to sleeve | 10.0 mA, 100 mW in R | 45 mA, 455 mW in R |
| Two outputs patched together at +10 V / −10 V | 16.4 mA, 269 mW in the 1 kΩ | **45.5 mA, 455 mW in *each* 220 Ω** |
| Op-amp forced into current limit? | No — 10–21 mA vs ±65 mA `[from memory, TI OPAx197: "high output current ±65 mA"; ti.com blocked]` | Marginal — 45 mA is close to a TL07x/OPA217x limit |

That table is the whole argument. **1 kΩ keeps every realistic fault in the
tens-of-milliamps region where nothing gets warm; 220 Ω does not.** Two O&C
modules patched output-to-output at opposite extremes put 455 mW into each
220 Ω resistor, which is more than an 0805 or a standard 1206 will take. The
220 Ω school is buying tracking accuracy with fault margin.

**What it costs:** a divider against the load. 1 kΩ into one 100 kΩ VCO is
−0.99 %; into a 4-way passive mult (25 kΩ) it is −3.85 %. On a 1 V/oct line
that is **−11.9 and −46.2 cents per octave** `[calc]`. Johnson noise of the
1 kΩ is 4.07 nV/√Hz, 0.58 µV RMS over 20 kHz `[calc]` — irrelevant.

**Does this module follow it?** Yes on all six jacks — `R-OUT-PROT` 1 kΩ, six
off `[repo] hardware/bom.csv`. With one important qualification: on **PITCH**
the resistor is inside the DC feedback loop, so the jack's *output impedance*
is not 1 kΩ. With OPA2197 open-loop gain and β ≈ 0.495, the DC output
impedance at the PITCH jack is on the order of **milliohms**, rising to ~10 Ω
at 100 kHz and only approaching 1 kΩ above the `C-FB-PITCH` handover `[calc]`.
So: the module follows the convention's *fault-limiting* half on all six jacks,
and deliberately abandons the *impedance* half on one of them.

---

## 3. Findings indexed by jack

Ranked Showstopper / High / Medium / Low / Note.

### 3.1 All six jacks — `R-OUT-PROT`

**[High] The BOM's worst case for `R-OUT-PROT` is understated by about 2×, and
a 500 mW part derated for rack ambient does not clear the real worst case.**

`[repo] hardware/bom.csv` states the worst cases as "Pitch shorted … 142 mW"
and "Pitch against a 220R output at −5 V … 192 mW", and specifies ≥500 mW on
that basis. The real ladder `[calc]`, at this module's ±11.55 V rails:

| Fault on one jack | Current | **Power in that 1 kΩ** |
|---|---|---|
| MOD at +10.05 V, tip shorted to sleeve | 10.05 mA | 101 mW |
| PITCH shorted (loop rails, feedback node = 0 V) | 11.55 mA | **133 mW** |
| MOD +10 V vs a foreign output at −5 V / 220 Ω | 12.3 mA | 151 mW |
| PITCH railed vs a foreign output at −5 V / 220 Ω | 13.6 mA | 184 mW ← *the BOM's stated worst case* |
| **MOD +10 V vs a foreign output at −10 V / 220 Ω** | 16.4 mA | **269 mW** |
| **PITCH railed vs a foreign output at −10 V / 220 Ω** | 17.7 mA | **312 mW** |
| MOD +10 V vs a foreign output at −10 V, ~0 Ω source | 20.0 mA | 400 mW |
| **PITCH railed vs a foreign output at −10 V, ~0 Ω source** | 21.6 mA | **464 mW** |

The BOM stopped at a −5 V antagonist. A ±10 V antagonist is the normal case —
`MOD 1–4` themselves reach ±10.00 V (`[repo] mod-channels.md`), so **two Woody
mod jacks patched to each other** through a stackcable is 10.0 mA / 100 mW
each, but a Woody mod jack against any 220 Ω-source module at −10 V is 269 mW.

Then derate. `[from memory]` A thick-film chip resistor's power rating is
specified at 70 °C ambient and derates linearly to zero at 155 °C; a Eurorack
case interior at 45–55 °C therefore leaves a 500 mW 1206 delivering roughly
350–420 mW. **Against a 312 mW realistic worst case that is 1.1–1.3×, and
against the 464 mW absolute worst it is under 1.0×.**

*Recommendation:* take the 2010 option the BOM itself offers, or a 1206 rated
0.66–1 W, not 0.5 W. The BOM's open item "VERIFY the part exists in 1206 at
500 mW; distributors were unreachable" — `[from memory]` yes: Panasonic ERJ-P06
(0805, 0.5 W) and ERJ-P08 (1206, 0.66 W) anti-surge thick film, Vishay
CRCW-HP, Yageo RT/AC high-power series all exist in 1206 at 0.5–1 W. Mutable's
own choice for the same job is Panasonic **ERJ-PA3D1001V** (0603, 0.25 W
anti-surge) on Plaits and **ERJ-3EKF1001V** on Marbles/Stages
`[web] Plaits.xlsx / Marbles.xlsx URLs above`. Every distributor domain is
blocked here (§9) so I cannot quote stock.

**[Note] Nothing in the module is damaged by any of these faults.** Op-amp
output current stays between 10 and 21.6 mA against a ±65 mA limit; when the
loop rails, the output device saturates and package dissipation is
milliwatts. `[calc]` Worst package dissipation with both halves' jacks shorted
is well under 100 mW against a SOIC-8 θJA of ~115–125 °C/W `[from memory]` —
under 13 °C of rise. **The op-amps survive every jack fault indefinitely.** The
only way to reach the ±65 mA limit is to bypass `R-OUT-PROT` (solder bridge,
or a fault at the op-amp pin), which then gives 11.55 V × 65 mA = **751 mW per
half, 1.5 W per package**, i.e. destruction. That is exactly what the 1 kΩ is
for, and it works.

### 3.2 All six jacks — the capacitor on the jack side

**[Medium] No surveyed design puts a capacitor on the jack side of the output
resistor. This module does, on all six jacks.**

`C-FILT-PITCH` 10 nF, `C-FILT-MOD` 82 nF ×4, `C-OUT-BREATH` 330 nF.
`[repo] docs/decisions/0006` already says "no DAC-driven module in the corpus
puts a capacitor on the jack side of the series resistor" — **I confirm that
across a wider corpus**: O&C, PER|FORMER, Sol, MTM Computer, Erica and Muxlicer
all have a bare resistor and nothing else, and Sol's jackboard contains
literally zero components (`[web] .../Sol/.../jackboard/jackboard.sch` — 24
jacks, no R, no C, no D).

Three consequences the repo does not state:

1. **Every plug insertion is a capacitor discharge through the plug tip.** A
   3.5 mm mono plug shorts tip to sleeve on the way in. 330 nF charged to
   10 V is 16.5 µJ dumped through a sliding contact `[calc]`; the 1 kΩ is on
   the wrong side to limit it. This is a contact-erosion and click mechanism,
   not a damage mechanism, but it is why the field leaves the node bare.
2. **A foreign module patched into a Woody output sees that capacitance
   directly** across its own output, through only its own series resistor. A
   220 Ω-source module driving 330 nF is a 2.2 kHz pole — harmless. A module
   with no series resistor at all driving 330 nF can oscillate. Low risk,
   worth knowing.
3. On PITCH the capacitor is on the **feedback node** — see 3.3.

For MOD and BREATH, items 1–2 are the only cost and the 1 kΩ correctly
isolates the op-amp; **the placement is defensible, just unprecedented.**

### 3.3 PITCH — jack-tapped ("force-sense") feedback

**Is it something published Eurorack modules do? Yes — three of the twelve
designs I opened, and all three are precision DAC-driven CV modules.** This is
the single most useful thing I found, because the repo's claim
(`[repo] pitch-stage.md`: "All four surveyed DAC-driven designs … close the DC
loop at the jack") is easy to doubt and turns out to be right.

- **Ornament & Crime rev2e** — `[web] https://raw.githubusercontent.com/mxmxmx/O_C/master/hardware/o_c_rev2e_schematic.pdf`.
  OPA2172 inverting. The 100 kΩ feedback resistor connects to the node **after**
  the 220 Ω, i.e. the PJ301M tip. The 22 pF connects to the node **before** the
  220 Ω, i.e. the op-amp output pin. **That is exactly the split loop this
  module draws** — DC from the jack, HF from the op-amp output. I confirmed it
  by rendering the PDF at 6× and reading the junction dots; the split is
  unambiguous.
- **Westlicht PER|FORMER** — `[web] https://raw.githubusercontent.com/westlicht/performer-hardware/master/dac.sch`.
  OPA4172, DAC8568 (the same DAC as this module). Per channel: 24 k in, 100 k
  feedback, **18 pF across the feedback**, 220 Ω to the jack. I traced the wire
  segments: both the 100 k *and* the 18 pF land on the node **after** the
  220 Ω. So the PER|FORMER puts the series resistor inside the loop at *every*
  frequency — the arrangement `[repo] pitch-stage.md` explicitly warns against
  ("18° of phase margin with 2 m of cable"). It ships anyway, because 220 Ω is
  4.5× gentler than 1 kΩ.
- **Winterbloom Sol** — `[web] https://raw.githubusercontent.com/wntrblm/Sol/master/hardware/rev1/mainboard/mainboard.pdf`.
  OPA4197 (the quad sibling of this module's part), non-inverting, 2.15 k /
  9.10 k, gain 5.23. The 9.10 k feedback returns from the node **after** the
  1 kΩ. **There is no compensation capacitor anywhere in Sol's range-amplifier
  block.** 1 kΩ inside the loop, uncompensated, 8 kHz-class DAC. Sol is the
  closest published relative of this module's pitch stage and it is
  *less* defended than this one.

**Counter-examples — feedback at the op-amp output, resistor outside the
loop:** MTM Workshop Computer (1 kΩ, 330 pF/68 pF lead), Erica MIDI-CV (1 kΩ,
22 pF lead), Muxlicer, HAGIWO. Mutable's topology I could not verify (Eagle
binary, see §9) but their BOM's 1 kΩ + a 1 V/oct spec calibrated in firmware
implies the conventional arrangement.

**Verdict: jack-tapped feedback is unusual in Eurorack generally and
*standard* in the precision DAC-CV niche this module belongs to. The repo is
on solid ground.**

**What the field gives up by not doing it:** the load divider — −11.9
cents/octave into one 100 kΩ VCO, −46.2 into a 4-way mult `[calc]`. The field
buys that back in one of three ways: use 220 Ω instead of 1 kΩ and cut the
error 4.5× (O&C, PER|FORMER when they don't tap at the jack); calibrate against
the real load (Yarns); or not care (mod/gate outputs).

**What the field avoids by not doing it,** and what this module therefore
inherits:

- **The shorted-jack rail-up.** `[repo] pitch-stage.md` states it. `[calc]`
  With the jack at 0 V the (−) input sits at V_ref + (0 − V_ref)·R1/(R1+R2) =
  1.25 V, so for any note above 0 V at the jack the amp slams to +11.55 V and
  stays there; below 0 V it slams negative. 11.55 mA, 133 mW in the 1 kΩ,
  indefinitely. **A half-inserted plug does this and looks exactly like a dead
  module.** Sol, O&C and the PER|FORMER all share this property, so it is
  field-accepted rather than novel — but none of them reaches ±11.5 V rails
  with a 1 kΩ, so none of them puts 133 mW into that resistor.
- **The load cliff.** `[calc]` With the tap at the jack the op-amp must supply
  V_target·(1 + 1 kΩ/R_load). For realistic loads the cost is negligible —
  7.58 V for +7.5 V at the jack into 100 kΩ, 7.80 V into a 4-way mult — and
  the ±600-cent firmware reserve survives intact. The output only clips when
  R_load drops below ~1.6 kΩ, which no CV input does. **The one thing in a
  Eurorack that presents <1.6 kΩ is another module's output.** So the cliff and
  the mispatch case are the same case.
- **Capacitance in the loop.** This is where the module diverges from all three
  precedents.

**[High] `C-FILT-PITCH` 10 nF sits on the feedback node and consumes almost the
entire stability margin — and no surveyed design puts anything there.**

I reproduced the repo's own criterion independently. With `R_out` = 1 kΩ,
`R2` = 10.2 kΩ, `C_fb` = 2.2 nF, `Q = √(R_out·C_L / (R2·C_fb))` `[calc]`:

| Load on the PITCH jack | Q | ζ | Step overshoot | Ring freq | Decay (2Q/ω₀) |
|---|---|---|---|---|---|
| Patch cable only (~300 pF) | 0.116 | 4.32 | 0 % | 61 kHz | — |
| **10 nF as specified** | **0.668** | 0.749 | **2.9 %** | 10.6 kHz | 20 µs |
| 10 nF + 2 m cable | 0.677 | 0.738 | 3.2 % | 10.5 kHz | 21 µs |
| 10 nF +5 %, `C_fb` −5 %, R2 −1 %, + cable | 0.694 | 0.721 | 3.8 % | 10.2 kHz | 22 µs |
| **+ passive mult to a MOD jack (82 nF)** | **2.03** | 0.247 | **44.9 %** | 3.5 kHz | **184 µs** |
| **+ passive mult to BREATH (330 nF)** | **3.89** | 0.128 | **66.6 %** | 1.8 kHz | **680 µs** |

Two things follow.

1. **The nominal design sits at a margin ratio of `R2·C_fb / R_out·C_L` =
   2.24, where 2.00 is the Q = 0.707 threshold the repo is implicitly
   targeting.** Ordinary ±5 % C0G tolerance plus two metres of patch cable
   takes it to 1.96 — past the threshold. The excursion is harmless in
   absolute terms (3.8 % of a step, ringing at 10 kHz, gone in 22 µs, so
   sub-cent by the time a VCO integrates it) but **the entire margin is being
   spent on a part that twelve out of twelve published designs leave off.**
   *Recommendation, free:* `C-FB-PITCH` 2.2 nF → **3.3 nF** (ratio 3.37,
   Q = 0.55) or `C-FILT-PITCH` 10 nF → **4.7 nF** (ratio 4.8, Q = 0.46).
   Either restores 2–2.4× of real margin and keeps the jack shunt.
2. **The repo's characterisation of the mult case is slightly wrong in a way
   that matters.** `[repo] pitch-stage.md` calls it "several semitones of
   transient on every note". `[calc]` It is 45 % of a step overshooting at
   3.5 kHz with a 184 µs envelope — audibly a *click*, not a pitch excursion.
   But there is a worse framing the page misses: **the DAC updates at 4 kHz,
   i.e. every 250 µs, and the 184 µs decay does not finish before the next
   update.** With an 82 nF load the pitch line carries continuous ~3.5 kHz
   ringing rather than per-note glitches. With 330 nF (680 µs decay at
   1.8 kHz) it never settles at all.

**[High] The most likely user accident is a stackcable or passive multiple
joining PITCH to a MOD or BREATH jack.** It is simultaneously (a) an
output-to-output patch, which rails the pitch loop, and (b) an 82 nF or 330 nF
load on the pitch feedback node, which is row 5 or 6 of the table above.
`[calc]` Electrically it is benign — PITCH railed at +11.55 V against BREATH at
−5 V through two 1 kΩ gives 8.3 mA and 68 mW per resistor — but both jacks
read wrong and pitch does not recover until unpatched. Passive mults and
stackcables are the most common accessory in Eurorack and joining two outputs
on one is the classic beginner mistake; in every other module it is harmless
and self-evident from the sound.

**[Note] A fault at the PITCH jack reaches the (−) input and the offset
buffer — and is self-limiting.** Because the jack *is* the feedback node, an
externally-forced jack voltage divides through R2/R1 into the (−) pin.
`[calc]` A foreign module holding the jack at −10 V puts the (−) input at
−3.69 V and asks the V_ref follower to sink 0.62 mA; at +12 V the (−) pin sits
at +7.2 V. Both are inside the OPA2197's input range on ±11.55 V rails, so no
clamp current and no error propagation. This path is safe, but it should be
written down, because it is the one path a jack fault has into the precision
network.

**[Medium] `TRIM-GAIN` has no downward authority.** `[repo] pitch-stage.md`
flags this itself ("one-sided and now pointing the wrong way"). Corroborating:
with the tap at the jack, the exact DC gain is load-independent, so the only
residual is component tolerance, which is two-sided. A 200 Ω series trimmer
that can only add is the wrong shape. Make the fixed leg 10.0 kΩ − 100 Ω and
bracket it, or delete it and let firmware's affine do the job.

### 3.4 MOD 1–4

**[Medium] `mod-channels.md` nominates channel 1 for "anything pitch-like" and
does not mention that the mod channels keep exactly the load-divider error the
pitch stage was redesigned to remove.** `[repo] mod-channels.md`: "anything
pitch-like belongs on channel 1". Mod feedback is at the op-amp output, so the
1 kΩ divides against the load: `[calc]` −11.9 cents/octave into 100 kΩ,
−23.5 into 50 kΩ, **−46.2 into a 4-way passive mult**, and 99 / 196 / 385 mV of
amplitude error on a ±10 V modulation channel. That is the same table ADR 0006
used to justify the pitch redesign. Either say plainly that a pitch-like
signal on MOD 1 gets the un-corrected error, or note that firmware can carry a
per-channel scale for it.

**[Note] The mod channels are the *best-protected* jacks on the module** — 1 kΩ
outside the loop, capacitor isolated, feedback immune to anything at the jack.
Two mod jacks patched to each other is 10 mA and 100 mW per resistor `[calc]`,
i.e. nothing. This is the field-standard arrangement and it is right.

### 3.5 BREATH

**[Medium] 330 nF is the largest jack-side capacitance on the module and is
the worst thing that can be connected to the PITCH jack by a mult.** See 3.3.
Independent of pitch, a foreign output patched into BREATH sees 330 nF across
its own output. `[calc]` 16.5 µJ of stored energy at 10 V dumped through the
plug on every insertion. The 482 Hz corner is justified by
`[repo] breath-output-stage.md`; if the corner can be moved upstream (the
breath channel is already band-limited by the time it arrives —
`[repo] docs/decisions/0004`), a smaller jack capacitor would bring this jack
in line with the field.

**[Note] BREATH's fault behaviour is the same as MOD's** — feedback at the
op-amp output, 1 kΩ outside the loop. Shorted at ±11.5 V rail clip: 11.5 mA,
132 mW. Survives indefinitely.

### 3.6 All six jacks — `D-JACK-CLAMP` (BAV99)

**[Medium] The stated primary justification for the clamp — back-powering when
the module is off — is nearly unreachable in a rack.**
`[repo] hardware/bom.csv` justifies the driver-side relocation with "a
neighbouring module driving 10 V … when this module is off — 254 mA across six
jacks". But `[repo] hardware/module/power-entry.md` shows the panel toggle
gates only the **LT1641 load switch feeding the umbilical**; `MODULE ANALOG
±12 V` comes straight off D1/D3 and is live whenever the rack is live. So "this
module is off while a neighbour drives its jacks" only happens on the bench
during bring-up (E7–E9), not in a rack. The relocation is still correct — the
leakage argument (a BAT54S's 2 µA through 1 kΩ = 2 mV = 2.4 cents) stands on
its own, and the driver-side position matches Erica and HAGIWO — but the
headline reason should be demoted.

**[Medium] Which "±12 V" the BAV99 clamps to is unspecified, and it decides
whether the part does anything.** The schematic in
`[repo] hardware/module/pitch-stage.md` just says `[D-JACK-CLAMP BAV99]── ±12 V`.
`[calc]` If that is the **raw rack** rail (before D1/D3, 12.0 V), the BAV99
conducts at ~12.7 V while the OPA2197's own output/ESD structure conducts at
V_analog + 0.7 ≈ 12.25 V — **the op-amp conducts first and the BAV99 never
sees the fault.** If it is `MODULE ANALOG ±12 V` (≈ ±11.55 V), the BAV99
conducts at ~12.25 V and shares with the op-amp roughly equally. Specify the
latter, and note that even then the BAV99 is a *sharer*, not a substitute.
Also note the back-fed current then lands on the node that feeds the LM317 and
the umbilical.

**[Note] Clamping a CV output to the rails is not unheard of.**
`[repo] hardware/bom.csv` says "no surveyed design clamps a CV output to the
RAILS at all; every clamp in the corpus goes to GND". That is too strong.
**HAGIWO's Quantizer clamps its CV output and its trigger output with a BAT43
pair to +5 V and GND** — a rail — on the driver side of a 470 Ω
`[web] .../HAGIWOs_Module/master/Quantizer/original_schematic.jpg`. **Erica's
gate and clock outputs clamp with BAT85 to GND *and* to +5 V**, also driver
side `[web] Erica DIY_MIDI_CV_v1_1.pdf`. The rest of my corpus has no output
clamp at all. So: rail clamping on outputs is rare but real, and the driver-side
placement this module chose is the placement both precedents use.

### 3.7 All six jacks — ESD and hot-patching

**[Low] A Eurorack module with no TVS on its outputs is entirely normal. This
module already has more output protection than any design I opened.**

- **Zero of twelve** surveyed designs fit a TVS, ESD array or suppressor on an
  output jack.
- Mutable is the only vendor in the corpus that fits ESD suppressors at all —
  TDK/EPCOS **CeraDiode B72500D160H60**, 16 V standoff, 0603
  `[web] Plaits.xlsx, Marbles.xlsx, Stages.xlsx`. The counts settle where they
  go: **Plaits has 8 CeraDiodes and only 2 output jacks; Stages has 6
  CeraDiodes and 12 output jacks.** The part count tracks the *input* jacks,
  not the outputs. (I could not read the Mutable schematics to confirm
  placement directly — Eagle 5 binary, §9 — but 6 parts cannot cover 12
  outputs, so the deduction holds.) Yarns fits none at all.
- The physics agrees with the practice: an output jack is a low-impedance
  driven node behind 220 Ω–1 kΩ. A human-body-model strike into the tip is
  limited by that resistor and absorbed by the op-amp's own ESD structures.
  Inputs are the vulnerable side, because they usually go to a high-impedance
  op-amp pin through a 100 kΩ.
- This module fits a **BAV99 on every output** plus the 1 kΩ plus a jack-side
  capacitor. That is strictly more than the field. `U-TVS-MODULE` being left
  open in `[repo] hardware/bom.csv` is fine as far as the *jacks* are concerned
  — that row is about the umbilical, and the jacks do not need it.

**[Note] The real hot-patching hazard in Eurorack is not ESD; it is the
tip-to-sleeve short during insertion.** Every mono plug shorts the output to
ground for a few milliseconds on the way in. For MOD and BREATH that is 10–11.5
mA for a few ms — nothing. **For PITCH it is a full rail excursion and a
loop-recovery transient on every single patch-in**, which
`[repo] pitch-stage.md` correctly notes. Sol, O&C and the PER|FORMER have the
same property.

### 3.8 All six jacks — the PJ398SM switch contact

**Is the module using it?** No. Six PJ398SM
(`[repo] hardware/bom.csv`, `J-CV`), none of the switch contacts connected, and
— more to the point — the schematics do not show them going to pads either.

**Does the field use it on *outputs*?** No. I checked three designs that draw
the switch explicitly:

- **Sol's jackboard** uses `AudioJack2_SwitchT` symbols for all 24 jacks and
  connects only tip and sleeve; the switch pins are unwired
  `[web] .../Sol/.../jackboard/jackboard.sch`.
- **O&C rev2e** draws the PJ301M switch pin with an explicit
  "no-connect" X on every CV output
  `[web] o_c_rev2e_schematic.pdf`.
- **Erica MIDI-CV** draws switched jacks on CV and gate outputs with the leaf
  unconnected `[web] DIY_MIDI_CV_v1_1.pdf`.

**Does the field use it at all?** Yes — on **inputs**, and the best example is
directly relevant. The **MTM Workshop System Computer** wires the switch
contact of `CV_IN_1`, `CV_IN_2`, `AUDIO_IN_1` and `AUDIO_IN_2` through 100 kΩ
resistors (R63–R66) to a net named **`NORMALISATION_PROBE`**, which the
firmware drives so it can detect what is plugged in and what is normalled
`[web] https://github.com/TomWhitwell/Workshop_Computer/blob/main/documentation/computer_Rev_1_0_0_Schematic.pdf`,
sheets 2 and 3.

**Should this module use it? Is there a musically useful normalling a wind
controller interface would expect?**

Short answer: **no useful *signal* normalling exists for an output-only module,
but patch *detection* would be genuinely useful and is currently impossible.**

- Signal normalling on an output jack is structurally backwards. The switch
  breaks when a plug is inserted, so any signal routed through it is present
  only when nothing is plugged in — which is precisely when nobody can hear
  it. There is no arrangement of six outputs where that helps.
- One arrangement is actively dangerous and should be written down as a
  prohibition: **never normal an output jack's tip to ground through the switch
  contact.** On MOD and BREATH that would merely short the output when
  unpatched (10 mA, harmless). **On PITCH it would ground the feedback node and
  rail the stage permanently whenever nothing is plugged in.** Someone tidying
  up the layout could do this without thinking.
- The valuable use is **detection**: firmware knowing which of the six jacks
  are patched would let the display show routing, let unpatched channels stop
  being refreshed, and — for a wind controller specifically — let the
  instrument auto-select a sensible default mapping when only PITCH and BREATH
  are patched. This is exactly the MTM trick.
- **This module cannot exploit it today.** `[repo] docs/decisions/0004`
  deleted MISO from the umbilical ("MISO goes, and with it the planned module-ID
  line"), so there is no return path from the module to the instrument, and the
  module has no ADC of its own — `[repo] hardware/module/digital-and-supervision.md`
  documents an LM311 watching breath and nothing that could read six switch
  states.

*Recommendation:* route the six switch pins to a small header or six unconnected
pads with DNF footprints. It is a footprint decision with zero BOM cost, it is
precisely the class of thing ADR 0006 says "cannot be added afterwards", and it
keeps the door open for detection if MISO or a module-side MCU ever returns.
**Do not** normal any of them to ground or to another jack.

---

## 4. Output patched into another output — quantified

Field behaviour first: this is a non-event in Eurorack, by design. Every output
has a series resistor, so two outputs fighting is a resistive divider between
two voltage sources, both of which remain in regulation. Nothing latches,
nothing is damaged, and the user hears a wrong (usually mid-scale) voltage.
That is the whole point of the 1 kΩ convention.

`[calc]` for this module:

| Case | Node settles at | Current | P in Woody's 1 kΩ | P in theirs | Damage? |
|---|---|---|---|---|---|
| MOD +10 V vs Mutable/MTM/Erica output at −10 V (1 kΩ) | 0.0 V | 10.0 mA | 100 mW | 100 mW | none |
| MOD +10 V vs O&C/PER\|FORMER output at −10 V (220 Ω) | −6.39 V | 16.4 mA | 269 mW | 59 mW | none, if the resistor is rated |
| MOD +10 V vs a 0 Ω-source output at −10 V | −10.0 V | 20.0 mA | 400 mW | — | resistor at risk |
| **PITCH vs anything** | the loop **rails to ±11.55 V** and then divides | 13.6–21.6 mA | **184–464 mW** | 40–69 mW | resistor at risk |
| (For comparison: two 220 Ω modules at ±10 V) | 0.0 V | **45.5 mA** | **455 mW each** | | *their* resistors at risk |

Op-amp dissipation in all of these is negligible: sourcing 21.6 mA from a
railed output is (11.55 − 11.55) × I ≈ 0; the worst mid-scale case (MOD
sourcing 16.4 mA at +10 V from an 11.55 V rail) is **25 mW** in that half.
`[calc]` No op-amp is at risk in any output-to-output patch.

**The difference PITCH's jack tap makes, stated plainly.** A conventional
output fights only as hard as its programmed voltage; a force-sense output
fights *as hard as it can*, because the error never goes away. Pitch therefore
draws 1.3× the fault current of a mod channel in the same mispatch and holds
it indefinitely. `[repo] hardware/bom.csv` gets this right ("the loop FIGHTS
the other module") — it just picks too gentle an antagonist.

---

## 5. Short to ground — every op-amp in the module

`[calc]`, OPA2197 on ±11.55 V, short-circuit limit ±65 mA `[from memory]`,
SOIC-8 θJA ≈ 120 °C/W `[from memory]`, quiescent ~1 mA per channel.

| Half | Drives a jack? | Behaviour with its jack shorted | Current | Package dissipation | Survives indefinitely? |
|---|---|---|---|---|---|
| PITCH amp | yes | **rails** (feedback node = 0 V) | 11.55 mA | ~25 mW | **yes** |
| MOD 1–4 amps (4 halves) | yes | holds +10 V into 1 kΩ | 10.0 mA | ~16 mW each | **yes** |
| BREATH summer | yes | holds its value into 1 kΩ, clips at rail | ≤11.5 mA | ~20 mW | **yes** |
| BREATH gain buffer | no | unaffected — behind the summer | — | — | yes |
| MOD offset follower (DAC ch7) | no | unaffected — mod feedback is at the op-amp output, jack is isolated by 1 kΩ | — | — | yes |
| `VREFOUT` follower (pitch V_ref) | no | **sinks up to 0.62 mA** through R2+R1 when the PITCH jack is forced to −10 V | 0.62 mA | negligible | yes |
| BREATH `REF`-zero buffer | no | unaffected | — | — | yes |
| INA828 breath receiver | no | no path to any jack | — | — | yes |

**All six jacks shorted at once:** 6 × ~11 mA = 66 mA of extra rail current and
about 0.8 W spread across six 1 kΩ resistors `[calc]`. The ferrites are
specified ≥1 A (`[repo] hardware/bom.csv`, `FB`), the 1N5817s are 1 A parts
`[from memory]`, so the power tree takes it. Package rise under 13 °C.
**Nothing in the module fails from a short to ground on any jack, or on all of
them, held forever.**

The only path into the ±65 mA limit is a fault that bypasses `R-OUT-PROT`.
Then: 11.55 V × 65 mA = 751 mW in one half, 1.5 W if both halves of a package
are shorted, ~180 °C of junction rise — destruction in seconds. That is the
consequence the 1 kΩ exists to prevent, and it is why the field never omits it.

---

## 6. What a Eurorack user would do by accident that this module does not
survive

In descending order of likelihood:

1. **Stackcable or passive multiple joining PITCH to MOD or BREATH.** [High]
   This is the one. It is a normal, harmless move on any other module — two
   outputs on one mult just gives you a mixed voltage. Here it (a) rails the
   pitch loop and (b) hangs 82 nF or 330 nF on the pitch feedback node,
   producing 45–67 % overshoot ringing at 1.8–3.5 kHz with a decay longer than
   the 4 kHz DAC update period, i.e. continuous audio-band garbage on the pitch
   line `[calc]`. Electrically survivable, musically destroyed, and the user
   has no way to know what they did wrong.
2. **A half-inserted plug, or a shorted patch cable, on PITCH.** [Medium]
   Permanent rail at ±11.55 V, 133 mW in the 1 kΩ, and the jack reads a rail
   voltage instead of a note. Indistinguishable from a broken module. Field
   designs in the same school share this; field designs outside it do not.
3. **Fitting a standard 250 mW or an underived 500 mW 1206 for
   `R-OUT-PROT`.** [High] `[repo] hardware/bom.csv` itself leaves "VERIFY the
   part exists in 1206 at 500 mW" open, so the risk of a 250 mW part being
   substituted at build time is real. A 250 mW 1206 fails in the 269–464 mW
   cases of §3.1; a 500 mW 1206 derated for a 50 °C rack interior is marginal
   in them. Specify 0.66–1 W or a 2010.
4. **Patching PITCH into a passive attenuator or a low-impedance load below
   ~1.6 kΩ.** [Low] Clips rather than sags. No Eurorack CV input does this, so
   the case is only reachable through another module's output — which is case
   1 again.
5. **Bench bring-up with the module unpowered and cables to a running rack.**
   [Low] `[calc]` ~9.3 mA per jack into the module's +12 V node through the 1 kΩ
   and the BAV99 (or the op-amp's own ESD diode — see §3.6); with six jacks
   driven and the module's ~500 Ω equivalent standing load, the analog rail
   settles around 7 V, the LM317 makes roughly 5.2 V, **the DAC8568 powers up
   from patch cables with SPI dead, and the op-amps run on partial, asymmetric
   rails with the panel LED off.** This is universal to every 1 kΩ-output
   module; the reason it matters more here is that this module's +12 V node
   also feeds a regulator and the umbilical. Add it to the bring-up procedure:
   unpatch before powering the module down.

**What it *does* survive that people will assume it does not:** every short to
ground, every output-to-output patch (electrically), every hot-patch, every
ESD strike into a tip that a BAV99 plus 1 kΩ can absorb. The module is
better-defended than any of the twelve published designs I opened.

---

## 7. Ranked summary

| Rank | Jack(s) | Finding |
|---|---|---|
| **High** | all six | `R-OUT-PROT` worst case is 269–464 mW, not the 142/192 mW the BOM states; ≥500 mW derated for rack ambient is marginal. Specify 0.66–1 W (1206 high-power) or 2010. §3.1 |
| **High** | PITCH | `C-FILT-PITCH` 10 nF sits on the feedback node, spends the whole stability margin (ratio 2.24 vs 2.00), and is unprecedented — 0 of 12 published designs put a capacitor there. Raise `C-FB-PITCH` to 3.3 nF or drop `C-FILT-PITCH` to 4.7 nF. §3.3 |
| **High** | PITCH | A stackcable/mult to a MOD or BREATH jack gives 45–67 % overshoot ringing longer than the 4 kHz update period, plus a railed loop. Most likely user accident; no user-visible cause. §3.3, §6 |
| **Medium** | MOD 1–4 | `mod-channels.md` recommends channel 1 for "pitch-like" material without noting it keeps the −11.9 to −46.2 cents/octave load divider the pitch stage was rebuilt to delete. §3.4 |
| **Medium** | all six | Which `±12 V` node the BAV99 clamps to is unspecified; if it is the raw rack rail the part never conducts before the op-amp's own ESD diode. §3.6 |
| **Medium** | all six | The clamp's stated back-powering justification is largely unreachable in a rack — the panel toggle gates only the umbilical, not the analog rails. The relocation is still right, for the leakage reason. §3.6 |
| **Medium** | all six | PJ398SM switch contacts are unused *and* not brought to pads. Field precedent (MTM normalisation probe) is on inputs; nobody uses them on outputs. Route to pads; never normal an output to ground — on PITCH that rails the stage whenever unpatched. §3.8 |
| **Medium** | all six | Jack-side capacitors (10/82/330 nF) are unprecedented in the corpus; every insertion is a capacitor discharge through the plug tip, up to 16.5 µJ on BREATH. §3.2, §3.5 |
| **Medium** | PITCH | `TRIM-GAIN` 200 Ω is one-sided upward with no downward authority. §3.3 |
| **Low** | all six | No TVS on outputs is the field norm (0 of 12). This module is already better-protected than any surveyed design. `U-TVS-MODULE` is not needed for the jacks. §3.7 |
| **Note** | all | The repo's central claims — 1 kΩ is standard practice, Mutable uprates its output resistor while the rest of the board stays 100 mW, four DAC-driven designs tap feedback at the jack, Erica clamps on the driver side — **all check out against primary sources.** The corrections above are to the *numbers*, not the *decisions*. |

---

## 8. Direct answers

**What does the field put between an op-amp and a 3.5 mm output jack?** One
series resistor, and nothing else. 12 of 12 designs. 1 kΩ in seven of them,
220 Ω in two, 470/510 Ω in two. Zero use a capacitor at the jack, zero use
series diodes, zero use a protection network. Two use a clamp diode pair on the
driver side. Consensus reason: the resistor is a fuse against shorts and
output-to-output patching, and everything else is either unnecessary (the node
is already low-impedance) or harmful (a capacitor at the jack is a capacitive
load the resistor no longer isolates once the loop is tapped there).

**The 1 kΩ convention.** Doepfer-derived house style, 1 kΩ out / 100 kΩ in
`[from memory]`, made visible in Mutable's BOMs, which specify the output 1 kΩ
at ≥200 mW on boards where every other resistor is 100 mW. It protects against
shorted plugs, output-to-output patching and back-driving from an unpowered
module by keeping fault current in the 10–20 mA region instead of the op-amp's
±65 mA limit. It costs a −0.99 % load divider (−11.9 cents/octave) per 100 kΩ
of load. **This module follows it on all six jacks** — and on PITCH uses it
purely as a fuse, since the jack tap drives the actual output impedance to
milliohms.

**Output into another output.** Field: a benign resistive divider, by design.
Here: 10.0–21.6 mA, 100–464 mW in this module's 1 kΩ, 25–69 mW in the other
module's resistor, ≤25 mW in any op-amp. **Nothing is damaged provided
`R-OUT-PROT` is rated for 464 mW at rack ambient.** PITCH is the outlier — it
rails and holds, drawing 1.3× the current a mod channel would, indefinitely.

**Short to ground.** Every jack: 10.0–11.6 mA, 100–133 mW in the resistor, under
25 mW in the op-amp, ≤13 °C of package rise. **Every op-amp survives
indefinitely, including all six jacks shorted at once.** The ±65 mA limit is
unreachable from the panel.

**Jack-tapped feedback.** Published, and specifically published in this
module's own niche: Ornament & Crime (identical split loop — DC from the jack,
22 pF from the op-amp output), Westlicht PER|FORMER (everything from the jack),
Winterbloom Sol (1 kΩ inside the loop, no compensation at all). Unusual in
general-purpose analog modules. The field gives up load-independence (−11.9 to
−46.2 cents/octave) and buys back immunity to shorts, mispatches, cable
capacitance and compensation mistakes.

**ESD and hot patching.** No published module in my corpus has a TVS on an
output. Mutable's CeraDiodes track the input count, not the output count. A
module without TVS on its outputs is not merely normal — it is the norm, and
this module's BAV99 + 1 kΩ + jack capacitor already exceeds every surveyed
design. The real hot-patch event is the tip-to-sleeve short on insertion, which
only PITCH reacts badly to.

**Normalled/switched contacts.** Not used here. Not used on outputs anywhere in
the corpus (Sol, O&C and Erica all draw switched jacks with the leaf
unconnected). Used on *inputs* in the field — MTM's normalisation probe. There
is no musically useful output normalling for a wind-controller interface;
the useful use is patch detection, which this module cannot act on because
ADR 0004 deleted MISO. Bring the six switch pins to pads anyway.

**What it does not survive by accident.** Ranked in §6. The short version: a
stackcable from PITCH to another Woody jack, and an under-rated `R-OUT-PROT`.

---

## 9. URLs that failed

Blocked by this sandbox's egress proxy (403 at the CONNECT tunnel, or an
explicit EGRESS_BLOCKED):

- `https://www.doepfer.de/DIY/a100_diy.htm` — the primary source for the
  1 kΩ/100 kΩ convention. Not citable from here.
- `https://www.befaco.org/` — Befaco's own schematic PDFs.
- `https://www.thonk.co.uk/` — PJ398SM datasheet/switch pinout.
- `https://www.nonlinearcircuits.com/diy` — NLC schematics. No NLC schematic
  was reachable; `github.com/Nonlinearcircuits` does not exist as a schematic
  source.
- `https://note.com/solder_state` — HAGIWO's primary publication. Worked around
  via the `ijnekenamay/HAGIWOs_Module` mirror on GitHub.
- `https://www.ti.com/lit/ds/symlink/opa2197.pdf` — OPA2197 datasheet.
  ±65 mA and θJA are therefore `[from memory]`, corroborated only by a search
  snippet quoting TI's product page.
- `https://pichenettes.github.io/mutable-instruments-documentation/` — Mutable's
  module documentation and any schematic PDFs it links.
- `https://bgr360.github.io/blog/modular/2018/06/17/mutable-instruments-schematics.html`
  — the community index of Mutable schematic PDFs.
- `https://www.modwiggler.com/forum/...` — all threads.
- `https://northcoastsynthesis.com/news/design-mistakes-in-synth-schematics/`
- `https://www.mouser.com/`, `https://www.digikey.com/`, `https://octopart.com/`,
  `https://www.vishay.com/`, `https://industrial.panasonic.com/`,
  `https://www.lcsc.com/` — all distributors and resistor vendors, so the
  "does a 1206 ≥500 mW part exist" question is answered from memory only.
- `https://api.github.com/...` — the GitHub REST API is gated in this session;
  `raw.githubusercontent.com` and GitHub HTML tree pages both work, which is
  how everything above was fetched.

Read but not machine-readable: **all Mutable Instruments `.sch` files** in
`pichenettes/eurorack` are Eagle 5 *binary*, so topology could not be
extracted; only the `.xlsx` BOMs were usable. `yarns_v03.sch`,
`marbles_v70.sch`, `plaits_v50.sch` etc. all fall in this category.
