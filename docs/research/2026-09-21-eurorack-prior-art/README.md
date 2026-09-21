# Eurorack prior-art research — 2026-09-21

Ten researchers, one per subsystem, asked the same question: **what do published
designs already do here, and where is Woody reinventing or diverging?**

Each was told to read the repo first so it compared against what is decided
rather than against a generic module; to mark provenance strictly (`[schematic]`
means a file opened in that session and nameable); and explicitly *not* to
validate Woody — the valuable finding is practice that exists because of a
failure mode this design has not considered. Each was also told to say plainly
where Woody is right to differ, since this is a one-off for one known rack and
"everyone does X" is not an argument by itself.

**All ten in.**

| | Topic |
|---|---|
| R1 | 1 V/oct output stages |
| R2 | Bipolar CV from a unipolar DAC |
| R3 | Eurorack power entry and protection |
| R4 | What goes between an op-amp and a jack |
| R5 | Off-board links: expanders, RJ45, SPI over a cable |
| R6 | Breath control as actually built |
| R7 | Multichannel DAC practice |
| R8 | 1 V/oct calibration, from real code |
| R9 | Fail-safe and supervision on CV outputs |
| R10 | Key scanning over a long loom, and SAR ADC front ends |

## Four parts that would have been soldered wrong

Applied already; each is in the BOM with the reasoning.

| | |
|---|---|
| **`U-DAC`** | The grade letter selects **reference gain**, not just reset state. A/B are gain 1, C/D gain 2 — corroborated in the PER|FORMER's firmware, which supports both parts and shifts the data word one bit between them. The row read "DAC8568C (or A grade)". An A part halves every output |
| **`U-PRESENCE`** | An LM393 cannot see an input below its own V−, and on a split supply its open-collector output pulls to −12 V and kills the level shifter's `OE` pins. LM311 has a separate emitter pin — which is why synth circuits use it |
| **`U-LOADSW`** | The pass FET was SOT-23. A 1.0 A ramp at ~6 V mean for 75 ms is 6 W and 0.45 J — hundreds of degrees of junction rise. DPAK or SO-8 against a single-pulse SOA curve, with the LT1641's foldback programmed |
| **`D-JACK-CLAMP`** | Clamping to the **rails at the jack** is a back-powering path: a neighbour driving 10 V through its own 220 Ω pushes 42 mA per jack into our +12 V when this module is off — 254 mA across six. Moved to the driver side of the 1 kΩ: 7.6 mA, and the diode's leakage error goes to zero because the op-amp absorbs it |

## Three arithmetic errors in pages written the same day

`R-OPAMP-IN` drawn into the mod gain network (a deterministic −196 mV zero
error, verified); `mod-channels.md`'s tolerance line evaluating to 200 mV
rather than the 50 mV it claimed, and omitting the dominant span term
altogether; and `pitch-stage.md` drawing `TRIM-GAIN` in parallel with `R2`
where the text says series.

## One conceptual error, which propagated

`pitch-stage.md` called `A = 1 + B` a *boundary* that pitch's numbers happened
to land on, and concluded the mod channels miss it and need four resistors. It
is the **defining identity** of the two-resistor non-inverting form, true for
every ratio — the free parameter is `V_ref`. Winterbloom's Sol ships the same
circuit with its reference divided to 1.190 V. The mod channels can use two
resistors at `k = 3` with the offset channel writing 3.3333 V, and the
`CLR`-safe property survives.

## Claims of ours that the corpus contradicts

- **"Every commercial 1 V/oct module has scale and offset trimmers."** Two
  independent surveys found **zero** across eight published DAC-driven designs.
  All calibrate in firmware, at one point per octave. Trimmers are universal on
  analog expo *inputs*, which is a different circuit.
- **"The in-loop `Cf` and the output filter are the same part and cannot both
  exist."** Seven designs carry both. A cap across the feedback resistor is a
  lead network that *raises* phase margin.
- **"Yarns uses twelve calibration points."** Eleven — `kNumOctaves = 11`.
- **"A constant transposition is worse to play than a progressive error."**
  Backwards: a constant offset comes out on the VCO's tune knob, which every
  VCO has. A spread across the range does not.

## What the corpus says we are right about

The `AGND` sense return (textbook automotive sensor-ground practice, and the
documented failure mode of the alternative); taking the mod offset from a DAC
channel rather than a divider, which is the only route that gives 0 V at the
jacks on both power-on *and* `CLR`; declining a breath mute FET; the
non-inverting pitch stage, which is shipped prior art in Winterbloom's Sol;
`R-OPAMP-IN` where it belongs, which is ahead of practice; the current-limited
load switch, where Eurorack's answer is "turn the rack off first" and a
hot-plugged umbilical cannot use it; and the three-way Schottky split, which
has no prior art because no published module passes 360 mA of someone else's
load through its entry diode.

Two surveys also found that **power-on transients are worse everywhere else**:
the inverting output stages in PER|FORMER and O&C sit at +5.17 V and ≈+6.3 V on
every jack from rack power-on until their processor boots. Woody's non-inverting
stage plus a DAC-channel offset makes zero-scale and "safe" the same state.

## A note on what the proxy allowed

Both agents so far report the same thing: **GitHub clone works and almost
nothing else does.** doepfer.de, ti.com, analog.com, nxp.com, neutrik.com,
modwiggler, electro-music, hackaday and Wikipedia were all blocked. So there is
very little `[datasheet]` evidence in this wave and a good deal of
`[search-summary]` — search-engine summaries of pages nobody could open.

That tier is explicitly flagged in each document and should be treated as
hearsay until someone with an unblocked browser checks it. It is not nothing —
it pointed at real things — but it is not a datasheet.

What the agents *could* do was clone and read source: five wind-controller
firmwares, several Eurorack module repos, and the author's own 2021
`Open-Woodwind-Project`. The strongest findings in this wave all came from
reading code and netlists, not from the web.
