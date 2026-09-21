# S5 — Staleness sweep: pitch stage, mod channels, DAC, and their numbers

**Date:** 2026-09-21
**Domain:** the pitch output stage, the four mod channels and their shared offset
channel, the DAC8568 and its supervision nets, and every number attached to them.
**Corpus audited:** `hardware/**`, `docs/decisions/**`, `config/**`,
`docs/reference/**`, `ROADMAP.md`, `README.md`, `firmware/README.md`.
**Read but not audited** (historical records, never reported as stale):
`docs/review/**`, `docs/log/**`, `docs/research/**`.

**No file was edited.** This report is the only thing written.

Findings are indexed by the **disputed fact**, not by document. Each one quotes
every side.

---

## Verdict summary

| # | Disputed fact | Rank |
|---|---|---|
| F1 | Where `C-FB-PITCH` connects | **Showstopper** |
| F2 | `R-OUT-PROT` power rating vs. its own stated worst case | **Showstopper** |
| F3 | `C-FB-PITCH` value: 1 nF or 2.2 nF | **Showstopper** |
| F4 | `C-FILT-PITCH`: deleted or restored | **High** |
| F5 | The pitch cents budget — two tables, one page, no total | **High** |
| F6 | The lever length behind every pitch drift number (9 V / 7 V / 2.25 V) | **High** |
| F7 | How the mod gain-of-4 is built: LT5400 1:4, LT5400 1:3, or 10k/30k discretes | **High** |
| F8 | Mod offset (ch7) update rate: once at boot or every pass | **High** |
| F9 | Mod offset voltage: 2.5 V or 3.3333 V | **High** |
| F10 | Pitch at rack power-on: 0.000 V or "below −2 V, subsonic" | **High** |
| F11 | Whether the module has a watchdog | **High** |
| F12 | Pitch stage nominal gain: 2.000 or 2.020000 | **High** |
| F13 | `LDAC`: "not in this design anywhere" vs `R-LDAC` qty 1 | **Medium** |
| F14 | Whether the 1 kΩ load-divider error still exists | **Medium** |
| F15 | The 2.4-cent BAT54S leakage argument | **Medium** |
| F16 | DAC INL in cents: 0.66 / ~0.4 / (derived 0.73) | **Medium** |
| F17 | Pitch trim range: "5 to 10 %" vs 200 Ω = 2 % | **Medium** |
| F18 | Mod jack range: ±10.000 V or ±10.05 V | **Medium** |
| F19 | Current out of the ch7 buffer: 1 mA or 1.3 mA | **Medium** |
| F20 | The pitch drawing omits three parts its own value table specifies | **Medium** |
| F21 | DAC grade: "C, locked" vs "A/C grade part" | **Medium** |
| F22 | Which DAC channel breath is on; what "channels 2–6" means | **Medium** |
| F23 | "20 cents of breath-correlated pitch bend" | **Medium** |
| F24 | `R-MODGAIN` cited as the 40.2 kΩ part it no longer is | **Medium** |
| F25 | DAC AVDD rail: 5.21 V or 5.25 V | **Low** |
| F26 | Feedback handover frequency "~16 kHz" | **Low** |
| F27 | Spare OPA2197 halves: two, or "the last" | **Low** |
| F28 | "DAC8568 or AD5676" against a grade-locked safety argument | **Low** |
| F29 | A-grade pitch range −2…+2.25 V | **Low** |
| F30 | What deleting `C-FILT-PITCH` cost at 1 MHz: 30 dB or 35 dB | **Low** |
| F31 | B/D-grade mod jack voltage "+2.5 V" | **Low** |
| F32 | Pitch reconstruction corner in the latency budget: 15.9 kHz vs 12.2 kHz | **Low** |

Of the two changes said to have landed today, **`R-CLR-PU` propagated cleanly
(see "Verified consistent") and `R-OUT-PROT` did not (F2).**

---

## F1 — Where `C-FB-PITCH` connects. **Showstopper**

The `pitch-stage.md` drawing and its value table put the capacitor from the
op-amp **output** to the (−) input, and the page states in a boxed warning that
the alternative net is the one that destabilises the stage.

`hardware/module/pitch-stage.md:216–225`:

> ### ⚠ `C-FB-PITCH` goes from the op-amp OUTPUT to the (−) input
>
> **Not "across the feedback resistor".** With the tap at the jack, `R2` spans
> *jack → (−)*, so a capacitor across `R2` connects the same two nodes and
> leaves `R-OUT-PROT` inside the loop at every frequency — which is the
> capacitive-load-in-the-loop case, at **18° of phase margin with 2 m of cable
> and under 10° with four destinations.**
>
> The drawing above is right. Three other places said "across the feedback
> resistor" and were wrong, and prose is what a layout gets built from.

`hardware/bom.csv:108` (`C-FB-PITCH`) agrees:

> FROM THE OP-AMP OUTPUT TO THE (-) INPUT. NOT 'across the feedback resistor' -
> with the tap at the jack, R2 spans jack-to-(-), so a cap across R2 connects
> the same two nodes and leaves R-OUT-PROT inside the loop at every frequency:
> 18 degrees of phase margin with 2m of cable, under 10 with four destinations.
> Three documents said 'across R2' and were wrong.

**ADR 0006 still specifies the bad net, in the sentence that adopts the change.**
`docs/decisions/0006-cv-channel-allocation.md:611–614`:

> **Adopted.** Pitch now closes its DC loop at the jack, with `C-FB-PITCH` (1 nF
> across the feedback resistor) taking the loop back to the op-amp output above
> ~16 kHz — which is also the reconstruction pole, so it is one part doing both
> jobs.

And ADR 0006 independently blesses that placement as safe, in the table two
sections earlier, `docs/decisions/0006-cv-channel-allocation.md:595`:

> | Cap **across the feedback resistor** | A *lead* network — it **raises** phase margin | Not the same thing, and not in conflict with anything |

That row is true of a stage whose feedback is tapped at the op-amp output. It is
false for pitch **as now drawn**, which is precisely the case the box above
quantifies at 18°.

**Why Showstopper.** ADR 0006 is the decision of record and is the document the
pitch page defers to for behaviour. It names a specific net, at a specific
value, in bold, in a paragraph headed "Adopted". A layout taken from it builds
the 18°/<10° version. Nothing in ADR 0006 marks the sentence as superseded.

*Residual:* `pitch-stage.md:182` also uses the phrase — "A capacitor across the
feedback resistor of a **non-inverting** stage cannot take the gain below
unity" — but there it is generic topology maths, not a placement instruction.
Worth rewording only to stop the phrase surviving a grep. Note also that the
claim "**three** other places said it" can no longer be verified: only ADR 0006
still does, twice.

---

## F2 — `R-OUT-PROT` power rating vs. its own stated worst case. **Showstopper**

The rating was raised today. **It did not reach a single one of the four places
that state it**, including the `part` column of the BOM row that carries the
raise.

Stated worst cases, all in `hardware/bom.csv:41` (one cell, two generations):

> Pitch shorted now rails the op-amp across this resistor: **142mW**. Pitch
> against a 220R output at -5V in output-to-output patching: **192mW** steady
> state […] The old stated worst case (a mod at 10.05V into a short, 101mW) is
> no longer the worst. 250mW would be 1.3x; specify >=500mW

> | 2026-09-21: RATING RAISED. Two reviewers independently found the stated
> worst case understated ~2x - **322mW** (output-to-output against a 220R source
> at +/-10V) and **269/312/464mW** on a fuller ladder. Thick-film derating at a
> 50C rack interior leaves a 500mW 1206 delivering 350-420mW, so margin was
> ~1.1x not 2.6x. Specify **0.66-1W** 1206 (ERJ-P08 class, confirmed to exist).
> This is the ONLY part in the module at real risk from any jack fault

Specified ratings now in the corpus:

| Where | Text | Status |
|---|---|---|
| `hardware/bom.csv:41`, `part` column | `"1k 1%, >=500mW"` | **Contradicts its own notes cell** |
| `hardware/bom.csv:41`, notes | `Specify 0.66-1W 1206 (ERJ-P08 class…)` | current |
| `hardware/module/pitch-stage.md:133` | `| **R-OUT-PROT** | 1 kΩ 1 %, **1206 ≥250 mW** | Short protection, **inside the DC feedback loop** |` | **two generations stale** |
| `hardware/module/breath-output-stage.md:127` | `| **R-OUT-PROT** | 1 kΩ, 1206 ≥500 mW | Shared spec with the other five outputs |` | one generation stale |
| `hardware/module/mod-channels.md:35` | `[R-OUT-PROT 1k, 1206]` | silent on rating |
| `hardware/module/pitch-stage.md:33` | `[R-OUT-PROT 1k, 1206]` | silent on rating |

**Quantitatively:**

- `pitch-stage.md`'s **250 mW is 1.9× under** the BOM's own worst case of 464 mW,
  and 1.29× under even the superseded 322 mW figure.
- **≥500 mW is also insufficient by the BOM's own arithmetic**: it says a 500 mW
  1206 derated at a 50 °C rack interior delivers 350–420 mW, against 464 mW.
  So `breath-output-stage.md`'s "≥500 mW … **Shared spec with the other five
  outputs**" is not merely stale — it propagates an under-rating to all six.
- The single-cell disagreement between `192mW` and `464mW` means the BOM states
  the worst case twice, 2.4× apart, with no marker saying which governs.

Worse, `breath-output-stage.md:127` claims the spec is *shared*, and
`breath-receive-stage.md:192` claims `bom.csv` "makes exactly this argument, in
full, for the module-side `R-OUT-PROT`". Two pages therefore assert a single
governing number for this part while three different numbers are in force.

**Required to close:** one number, propagated to `bom.csv`'s `part` column,
`pitch-stage.md:133` and `breath-output-stage.md:127`, with the superseded
142/192/101 mW ladder struck or dated inside `bom.csv:41`.

---

## F3 — `C-FB-PITCH` value: 1 nF or 2.2 nF. **Showstopper**

This is worse than the reported "one drawing and one prose table": **the entire
frequency-domain analysis on `pitch-stage.md` is computed at 1 nF** while the
page's own value table specifies 2.2 nF.

**Says 2.2 nF:**

- `hardware/module/pitch-stage.md:134` — `| **C-FB-PITCH** | **2.2 nF C0G** | **From the op-amp OUTPUT to the (−) input — NOT "across R2".** …`
- `hardware/module/pitch-stage.md:212` — "**`C-FB-PITCH` goes to 2.2 nF**, which with the jack cap restored is maximally flat: −3 dB at 12.2 kHz, inside ADR 0006's own 10–20 kHz window, and −41 dB at 1 MHz against the 6 dB the shelf gives alone."
- `hardware/bom.csv:108` — `C-FB-PITCH,module,2.2nF C0G/NP0,…`

**Says 1 nF:**

- `hardware/module/pitch-stage.md:29` (the drawing, which the page declares authoritative at line 224 — "The drawing above is right"):
  `├──[C-FB-PITCH 1nF]──────────┤   ← AC feedback`
- `hardware/module/pitch-stage.md:179` — `| `C-FB-PITCH` 1 nF from the **op-amp output** | above ~16 kHz | Takes over before `R-OUT-PROT` and the cable can put phase in the loop |`
- `docs/decisions/0006-cv-channel-allocation.md:611` — "`C-FB-PITCH` (1 nF across the feedback resistor)"

**And the arithmetic is silently pinned to 1 nF.** `pitch-stage.md:186–189`:

> ```
> G(s) = 1 + (R2/R1)/(1 + sR2C) = (2 + sRC)/(1 + sRC)
> ```
>
> Pole at 15.9 kHz, **zero one octave above at 31.8 kHz**, flattening at gain 1.

With `R2 = 10 kΩ`, a pole at 15.9 kHz requires **C = 1.0 nF**. At 2.2 nF the pole
is at **7.2 kHz** and the zero at 14.5 kHz. So lines 178–179 ("DC to ~16 kHz",
"above ~16 kHz") and 186–189 describe the 1 nF part, and line 212 describes the
2.2 nF part, on the same page, with no reconciliation. The handover frequency
that ADR 0006 calls "also the reconstruction pole" (line 613) is likewise a
1 nF result.

**Consequence:** a builder reading the drawing fits 1 nF; a builder reading the
BOM fits 2.2 nF; the stability case — the page's own "highest-risk item"
(line 229) — is argued at neither value consistently.

---

## F4 — `C-FILT-PITCH`: deleted or restored. **High**

**Deleted.** `docs/decisions/0006-cv-channel-allocation.md:614–615`:

> `C-FILT-PITCH` is deleted: a capacitor to ground at the jack would now sit
> inside the DC loop at exactly the handover.

ADR 0006 repeats the consequence at line 627 of its filter table: pitch's
"filter sits *ahead* of the op-amp instead (`C-AA-PITCH`)", and the table at the
end of the ADR lists only `10 nF C0G` against `R-OPAMP-IN`, with nothing at the
pitch jack.

**Restored.** `hardware/module/pitch-stage.md:136`:

> | **C-FILT-PITCH** | **10 nF C0G** | Restored at the jack. The low-impedance shunt at the connector, which nothing else provides |

`hardware/module/pitch-stage.md:205–211`:

> - **`C-FILT-PITCH`**, 10 nF back at the jack. **The reason given for deleting
>   it does not survive**: two independent loop analyses put 10 nF at the jack
>   and found the phase margin unchanged, because `C-FB-PITCH` ties the (−) input
>   to the op-amp *output*, so β(∞) = 1 exactly and `R-OUT-PROT` isolates the
>   jack above the handover.

`hardware/bom.csv:119`:

> C-FILT-PITCH,module,10nF C0G/NP0,,Reconstruction and RF shunt at the pitch jack,…
> "**RESTORED.** It was deleted on the reasoning that a cap on the feedback node
> sits inside the DC loop at the handover; two independent loop analyses then put
> 10nF there and found phase margin UNCHANGED…"

ADR 0006 is the lone holdout, and it is the document that created the deletion,
so nothing points a reader from the deletion to the restoration. Note also that
the restoration is load-bearing on F3: the "maximally flat, −3 dB at 12.2 kHz"
justification for 2.2 nF is only true *with* the jack cap present.

---

## F5 — The pitch cents budget. **High — this is the headline**

**There is no single coherent cents budget in the repository.** `pitch-stage.md`
contains two error-budget tables, printed back to back with six lines of prose
between them, disagreeing by up to 4× on the same terms, and the page's own
narrative disowns the numbers in one of them while leaving them in place.

`hardware/module/pitch-stage.md:277–304`, in full order:

> ## What limits accuracy, in order
>
> **The 6× disagreement this table used to flag is resolved, and both published
> numbers were wrong.** It was a pivot error: `∂Vout/∂k = Vdac − V_ref`, so a
> *ratio* drift pivots at `Vout` = +2.5 V with a maximum lever of 2.25 V, while a
> *reference* drift pivots at `Vout` = 0 with a lever of 7 V. Three documents
> used 9 V, 7 V and 2.5 V for the same term.
>
> | Term | Over 10 °C | Note |
> |---|---|---|
> | **DAC internal reference** | **0.42 cents** | **The largest term, and untrimmable** |
> | LT5400 ratio tracking | 0.027 cents | |
> | `TRIM-GAIN` tempco | **0.068 cents** | 200 Ω cermet. Second *smallest*… |

then, after three paragraphs arguing the network is kept:

> | LT5400 ratio tracking | ~0.1 cents | The reason it is not two discrete 0.1 % parts, which would be ~1.2 cents |
> | DAC internal reference | ~0.5 cents | A gain term, per above |
> | OPA2197 offset drift | <0.1 cents | An offset term, but a tiny one |
> | DAC INL, ±4 LSB typical | ~0.4 cents | Curvature; firmware's multi-point correction, not a trimmer's job |

The second block is a bare table continuation — it has no header row of its own;
it is glued to the end of a prose paragraph ("The option-code lookup is.") and
renders as a stray table. It is the **pre-correction** budget: its `~0.5` and
`~0.1` are ADR 0006's 0.54 and 0.11 rounded, i.e. the 9 V-lever numbers the same
page's opening paragraph calls a pivot error.

**Term-by-term disagreement:**

| Term | `pitch-stage` table 1 | `pitch-stage` table 2 | ADR 0006:296–299 | `bom.csv:15` | Ratio |
|---|---|---|---|---|---|
| DAC internal reference | **0.42** | **~0.5** | **0.54** | **0.42** | 1.29× |
| LT5400 ratio tracking | **0.027** | **~0.1** | **0.11** | **0.027** | 4.1× |
| Two discrete resistors | **0.38** | **~1.2** | **5.40** (25 ppm/°C) | **0.38** | 14× |
| `TRIM-GAIN` tempco | **0.068** | absent | **2.4** (at 5 %) | — | 35× |
| DAC INL ±4 LSB | absent | **~0.4** | **0.66** | — | 1.65× |
| OPA2197 offset | absent | **<0.1** | absent | — | — |

**No document anywhere states a total.** Neither table is complete: table 1 omits
INL and op-amp offset; table 2 omits the trimmer. The only place a *total* is
asserted is `hardware/module/power-entry.md:83`, which takes table 1's largest
single row and calls it the whole budget:

> `pitch-stage.md` puts the entire pitch error budget at 0.42 cents. **The
> carefully engineered part of the pitch path is one to two orders of magnitude
> below an effect that appears in no document**

That is a misreading of a term as a sum — and it is the number the grounding
argument in `power-entry.md` is scaled against.

**What a coherent budget would be** (using the corrected levers that
`pitch-stage.md:279–283` itself derives — 7 V for reference drift, 2.25 V for
ratio drift, direct for offset terms; 1 mV = 1.2 cents on 1 V/oct):

| Term | Derivation | Cents / 10 °C |
|---|---|---|
| DAC internal reference, 5 ppm/°C | 50 ppm × 7 V = 350 µV | 0.42 |
| LT5400 tracking, 1 ppm/°C | 10 ppm × 2.25 V = 22.5 µV | 0.027 |
| `TRIM-GAIN`, ~2 ppm/°C of ratio | 20 ppm × 2.25 V = 45 µV | 0.054 (page says 0.068) |
| OPA2197 offset drift | offset term, direct | <0.1 |
| DAC INL ±4 LSB | 4 × (10 V / 65536) = 610 µV | **0.73** |
| **RSS** | | **≈0.85** |
| **Linear sum** | | **≈1.35** |

Two consequences the corpus does not state:

1. **The headline ranking is wrong.** Table 1 calls the DAC reference "**The
   largest term, and untrimmable**" — true only within the three rows table 1
   prints. Once INL is included at its correctly derived value (0.73 cents, on
   the DAC's own 10 V output span), **INL is the largest static term**, and it
   is the one firmware's multi-point table exists to attack.
2. **No number between 0.42 and 1.35 cents appears anywhere**, so every
   downstream comparison — `power-entry.md`'s "one to two orders of magnitude
   below", ADR 0006's "Nothing here approaches the 20-odd cents of the dynamic
   terms" — is drawn against a figure that is not the budget.

**Verdict: there is no single coherent cents budget in the repo.** Establishing
one requires deleting table 2 outright, adding the missing INL and op-amp rows
to table 1 at the corrected levers, stating a total, and re-pointing
`power-entry.md:83` and `ADR 0006:296–299` at it.

---

## F6 — The lever behind every pitch drift number. **High**

`hardware/module/pitch-stage.md:279–283`:

> It was a pivot error: `∂Vout/∂k = Vdac − V_ref`, so a *ratio* drift pivots at
> `Vout` = +2.5 V with a maximum lever of 2.25 V, while a *reference* drift
> pivots at `Vout` = 0 with a lever of 7 V. Three documents used 9 V, 7 V and
> 2.5 V for the same term.

`docs/decisions/0006-cv-channel-allocation.md:293–299` still uses the 9 V lever
for **every** row:

> Over a 10 °C swing on a 9 V span, against one semitone at 83.3 mV:
>
> | Source | Drift | Cents |
> |---|---|---|
> | DAC internal reference, 5 ppm/°C | 0.45 mV | 0.54 |
> | **Discrete resistors, 25 ppm/°C each, drifting oppositely** | **4.50 mV** | **5.40** |
> | Matched network, 1 ppm/°C tracking | 0.09 mV | 0.11 |

I verified the ADR's arithmetic is internally correct **on its stated premise**:
5 ppm/°C × 10 °C × 9 V = 0.45 mV → 0.54 cents ✓. The premise is the error. The
9 V span is the *output range*, not the sensitivity of either term:
`Vout = (1+k)·Vdac − k·V_ref` gives `∂Vout/∂k = Vdac − V_ref ∈ [−2.25, +2.25] V`
over the 0.25–4.75 V window, and `∂Vout/∂δ_ref = Vout ∈ [−2, +7] V`. The pitch
page's derivation is sound; the ADR's is not.

**And `pitch-stage.md` endorses the wrong number in the same breath.**
`pitch-stage.md:121–122`:

> *(This is also why the ADR's "the DAC's internal reference is sufficient, at
> 0.54 cents over 10 °C" survives: that figure is a gain term.)*

So line 122 blesses 0.54 and line 287 replaces it with 0.42, 166 lines apart.
`docs/decisions/0006-cv-channel-allocation.md:316` carries the same 0.54:

> - **The DAC's internal reference is sufficient.** At 0.54 cents over 10 °C it is
>   an order of magnitude inside the resistors, so a separate precision reference
>   buys nothing measurable.

That "order of magnitude inside the resistors" is only true against the ADR's own
5.40-cent discrete figure. Against `bom.csv:15`'s and `pitch-stage.md:292`'s
0.38 cents for discretes, the reference term is now the **larger** of the two —
which is exactly what `bom.csv:15` says ("currently MASKED by a larger term") and
exactly what ADR 0006:316 still denies.

---

## F7 — How the mod gain-of-4 is built. **High**

Three incompatible constructions are live.

**(a) LT5400 1:4.** `docs/decisions/0006-cv-channel-allocation.md:111–112`:

> - **Gain of 4 is a 1:4 ratio**, which the LT5400 family offers directly — no
>   external resistor, so no absolute tempco leaks into the gain.

**(b) LT5400 1:3, three sections against the fourth.**
`hardware/module/mod-channels.md:54–57`:

> So the mods can take the same two-resistor form: **`k = 3`, with the shared
> offset channel writing 3.3333 V instead of 2.500 V.** Eight resistors instead of
> sixteen, one matching requirement instead of two per channel, and **a 1:3 ratio
> that three sections of an LT5400 give directly against the fourth.**

**(c) 10 k / 30 k 1 % discretes.** `hardware/bom.csv:66`:

> R-MODGAIN,module,**10k / 30k 1% metal film**,,Two-resistor non-inverting network
> per mod channel,…,**8**,… "EIGHT, not sixteen: R1=10k, R2=30k per channel, k=3 so
> gain = 1+k = 4 exactly…"

and `hardware/module/mod-channels.md:6–9` (same page as (b), 48 lines earlier):

> ADR 0006 specifies `Vout = 4 × (Vdac − 2.5 V)` and contradicts itself about how
> to build it — the topology section offers an LT5400 1:4 ratio, the calibration
> section says ordinary 1 % discretes. **The discretes won** (ADR 0006,
> `R-MODGAIN`), and this page is what they build.

and the drawing at `mod-channels.md:20,31` — `[R1 10k 1%]` / `[R2 30k 1%]`.

**(b) is additionally refuted by arithmetic**, in `hardware/module/pitch-stage.md:313–314`:

> The claim that two spare sections can build the mod channels' 1:3 is
> **arithmetically impossible** — three sections against the fourth is all four.

Pitch already consumes two of the LT5400's four sections (`bom.csv:15`: "Two of
four sections used"; `R-PRECISION` qty **1**). There is no second network in the
BOM. So (b) requires either a second LT5400 that nobody has bought, or taking
pitch's matched pair away.

**Status:** (c) is what the BOM builds and what `mod-channels.md` draws.
(a) survives verbatim in ADR 0006's topology section and is the source of the
self-contradiction `mod-channels.md` opens by naming. (b) survives in
`mod-channels.md`'s own adoption paragraph and is impossible.

One further ADR 0006 residual, at line 92–93, contradicts the adoption outright:

> **The mod channels can take the same form** at `k = 3` with the offset channel
> writing 3.3333 V; **whether they do is open** (`mod-channels.md`).

`mod-channels.md:63` — "**Adopted, and it is drawn above.**" It is not open.

---

## F8 — Mod offset (ch7) update rate. **High. Established exactly below.**

This was reported as a disagreement reviewers could not pin down. It is 1½
documents against six.

**"Written once at boot" — 2 instances:**

1. `docs/decisions/0006-cv-channel-allocation.md:186` (the update-rate table):

   > | Mod offset | written once at boot | The shared 2.5 V reference point |

2. `firmware/README.md:50` — present tense, and attributed to ADR 0006:

   > The mod channels are `Vout = 4·Vdac − 3·V_ref`, with `V_ref` the shared
   > **3.3333 V** from DAC channel 7 — **written once at boot** (ADR 0006).

   (This same file's line 38 states the opposite as an architecture rule:
   "**Refresh everything, every pass. Never write-on-change.**" The page is
   internally split: line 50 asserts write-once as fact, lines 64–67 then say the
   sixth channel is refreshed inside an already-paid budget.)

**"Refresh all six every pass" — 6 instances:**

1. `firmware/README.md:38` — "**Refresh everything, every pass. Never write-on-change.**"
2. `firmware/README.md:64–66` — "**The latency budget already books six DAC words per pass while five are written**, so the sixth channel fits inside a budget that was already paid…"
3. `docs/reference/latency-budget.md:169–172` — "Six channels means *all* the populated ones: **the loop refreshes the mod offset every pass rather than writing it once** (`firmware/README.md`). The old table booked six while writing five…"
4. `docs/reference/latency-budget.md:62` — "Six 32-bit words at 2 MHz. **The loop refreshes all of them every pass**"
5. `hardware/module/mod-channels.md:166–167` — "That is closed by the statelessness rule in `firmware/README.md` — **refresh all six populated channels every pass** — and the latency budget already paid for it."
6. `docs/decisions/0004-cv-interface-module.md:426` — "It retriggers on `CS` edges, and **firmware refreshes every channel every pass**"

plus corroboration at `hardware/controller/carrier.md:591`
(`SPI2  DAC    6 × 32 bits @ 2.0 MHz =  96.0 µs`) and
`hardware/module/digital-and-supervision.md:222` ("Six frames per pass").

**Established:** every-pass refresh is the decision; **ADR 0006:186 is the only
document that still states the old rule as policy**, and `firmware/README.md:50`
repeats it as a quotation of ADR 0006 without marking it superseded. The row
matters: `firmware/README.md:56–57` and `mod-channels.md:163–165` both show that
a ch7 that is not refreshed after a `CLR` pins **all four mod jacks at ≈ +11.45 V
indefinitely, undetectably** (no `MISO`).

**Same table, second stale row.** `ADR 0006:185`:

> | Breath zero offset | continuous, slow | See the auto-zero rule below |

The breath ambient-zero DAC channel was deleted by this same ADR
(`ADR 0006:25–31`: "**Channel 6 was freed deliberately**") and by
`latency-budget.md:171–172` ("The breath ambient-zero channel that briefly made
it seven is deleted"). There is no such channel to give a rate to.

---

## F9 — Mod offset voltage: 2.5 V or 3.3333 V. **High**

**3.3333 V** — `ADR 0006:15` (`| *(internal)* | DAC ch 7 | — | — | Shared **3.3333 V** offset for mod 1–4 |`), `ADR 0006:21`, `ADR 0006:92`, `mod-channels.md:14,55,66,95,160`, `pitch-stage.md:83`, `bom.csv:66`, `firmware/README.md:50`.

**2.5 V** — two live instances in ADR 0006:

- `docs/decisions/0006-cv-channel-allocation.md:113` —
  > - **The 2.5 V reference point comes from a buffered DAC channel**, not directly from the internal reference.
- `docs/decisions/0006-cv-channel-allocation.md:186` —
  > | Mod offset | written once at boot | **The shared 2.5 V reference point** |

`firmware/README.md:51–53` states exactly what this costs if believed:

> *(The value changed with the two-resistor redraw in `mod-channels.md`; writing
> the old 2.5 V into channel 7 against the current 10 k/30 k network gives a
> −7.5…+12.5 V window — wrong span, and it clips positive.)*

`ADR 0006:102` (`Vout = 4 × (Vdac − 2.5 V)`) and `:130` are **not** stale: with
`k = 3` and `V_ref = 3.3333`, `4·Vdac − 3·3.3333 = 4(Vdac − 2.5)` identically.
The defect is confined to the two places that name 2.5 V as the **voltage
channel 7 writes**.

**One instance is self-refuting.** `ADR 0006:148–150`:

> An A-grade part halves every output — pitch becomes −2…+2.25 V, the mods ±5 V,
> and **channel 7 cannot reach its reference voltage at all**.

An A-grade part has a 2.500 V full scale. It could reach 2.5 V (at full code).
It cannot reach 3.3333 V. The sentence is only true under the value the same
document contradicts 35 lines earlier.

---

## F10 — Pitch at rack power-on. **High**

**0.000 V.** `hardware/module/pitch-stage.md:138–142`:

> **Power-on is 0.000 V, not "subsonic".** `V_ref` is the DAC's internal
> reference, which is **disabled until firmware writes an enable** — so *both*
> terms are zero and the jack sits at **0 V, a VCO's base note**, until that
> write. After it, `CLR` parks at −2.500 V. ADR 0006's power-on table asserts
> "below −2 V" for both; they are different states, 2.5 V apart.

**"Below −2 V, subsonic".** `docs/decisions/0006-cv-channel-allocation.md:156–158`:

> | Output | At rack power-on, before firmware writes | Why that is right |
> |---|---|---|
> | **Pitch** | Bottom of its range, below −2 V | Subsonic. A VCO there is inaudible |

and `docs/decisions/0004-cv-interface-module.md:437–439`:

> The DAC's own `CLR` pin already does exactly what is wanted — an A/C grade part
> clears to zero scale, **which parks pitch subsonic** and the mod channels at
> 0 V (ADR 0006), the same safe state as rack power-on.

**ADR 0006 refutes its own table eight lines later**, at `:166–168`:

> It also means **the outputs sit at 0 V from rack power-on** until firmware
> enables the reference, **which happens to reinforce the table above.**

0 V does not reinforce "below −2 V"; it is the pitch page's number, contradicting
the table it claims to support. Three states are conflated across these
passages — power-on before the reference enable (**0.000 V**), post-enable `CLR`
(**−2.500 V**), and "bottom of range" (**−2 V**) — and only `pitch-stage.md`
separates them.

This is musically load-bearing: 0.000 V is a VCO's base note, −2.500 V is 2.5
octaves below it.

---

## F11 — Whether the module has a watchdog. **High**

`hardware/module/digital-and-supervision.md:153–157` is unambiguous:

> ## There is no frame watchdog
>
> **Deleted.** A 74HC123 monostable used to assert the DAC's `CLR` when SPI
> traffic stopped. The part, its timing pair and its decoupling are gone; `CLR`
> is pulled **inactive**, with a solder pad beside it so it can be asserted by
> hand.

`hardware/bom.csv:67` agrees — "THE WATCHDOG IS DELETED (U-WATCHDOG, R-WDT, C-WDT all gone)".

**Still asserting a live watchdog, in my domain:**

| Where | Text |
|---|---|
| `hardware/module/mod-channels.md:150` | "**On a watchdog `CLR`**, the C-grade DAC8568 … clears **every** channel to zero scale" |
| `hardware/module/mod-channels.md:215–218` | "**On a watchdog `CLR`** the channels go to zero and the divider does not … The PER\|FORMER avoids this by disabling `CLR` entirely; **Woody cannot, because the watchdog is the whole answer to a processor two metres away.**" |
| `firmware/README.md:53–54` | "When **the module watchdog asserts `CLR`**, every DAC channel including channel 7 goes to zero scale." |
| `ROADMAP.md:51` (E10) | "**Pull the umbilical mid-note** with the mouthpiece at rest and confirm the breath jack parks quietly: **the watchdog has no authority over it by design**, and this is the check that the design is right about why (ADR 0004)." |
| `docs/decisions/0004-cv-interface-module.md:445` | "#### The watchdog's scope is the DAC channels, and breath is outside it" (and :463 "the MCU dies, SPI stops, **`CLR` fires**, and breath keeps working") |
| `hardware/module/breath-receive-stage.md:283–290` | "## What the jack does **when the watchdog fires** — settled" |

`mod-channels.md:217–218` is the sharpest: the design's *case against* the
inverting topology rests on the watchdog existing, so a deleted watchdog
silently removes the objection to a topology the same page calls "strictly
better than what is drawn above" (line 222).

`ROADMAP.md:51` is the most actionable: with the watchdog gone,
`digital-and-supervision.md:175–177` says pulling the umbilical mid-note leaves
"**the DAC holds and the rack drones**". The E10 acceptance criterion tests for
the wrong behaviour.

`ADR 0004:418–432` does carry a strikethrough banner over its watchdog section,
so :445 and :463 are partly covered. `mod-channels.md`, `firmware/README.md` and
`ROADMAP.md` carry no such marker.

**Residual in `digital-and-supervision.md` itself** — three "Still open" bullets
(lines 210, 224, 234) are posed against the deleted part: "A power-on reset RC on
**the '123's own `CLR`**", "**Six frames per pass** means ~2400 retriggers per
timeout", and "A config save that overruns **99 ms** would assert `CLR`
mid-note." The 99 ms timeout belongs to the deleted monostable; with `CLR` tied
inactive an NVS stall cannot assert it. Two further bullets (lines 209, 231) are
posed against the deleted presence comparator. And `bom.csv:70` (`PCB-MODULE`)
already self-flags its own stale word, which is the right pattern.

---

## F12 — Pitch stage nominal gain: 2.000 or 2.020000. **High**

`hardware/module/pitch-stage.md:50` and `:128,130`:

> | Slope | 9 V / 4.5 V = **exactly 2.000** |

> | **R1, R2** | 10 kΩ, **1:1 matched** (LT5400) | Sets gain = 2 and the −2.5 V intercept together |

> | **TRIM-GAIN** | **200 Ω** … 0 → +2 % of ratio … **Nominal is dead on 2.000** and the trimmer has no downward authority |

`hardware/module/pitch-stage.md:261–263`:

> **The load no longer matters**, which is the point of the jack-side tap: **the
> exact DC solve gives gain 2.020000 for every load** from open circuit to 2 kΩ,
> with about 1 ppm of residual.

2.020000 is `1 + (10 k + 200 Ω)/10 k` — the trimmer at **full** travel, not
nominal. Presented without that qualifier, the page states two nominal gains
1 % apart. On 1 V/oct a 1 % gain error is **12 cents per octave, 60 cents at five
octaves** — the same magnitude as the load-divider error the jack-side tap was
adopted to remove. The load-independence claim is correct; the number chosen to
demonstrate it is the wrong end of the trimmer's travel.

---

## F13 — `LDAC`. **Medium**

`hardware/module/digital-and-supervision.md:218–222` ("Still open"):

> - **`LDAC` is not in this design anywhere**, which leaves a CMOS input floating
>   on the DAC and means six channels cannot update atomically. **Tie it.**

`hardware/bom.csv:121`:

> R-LDAC,module,**10k 1%**,,Ties the DAC8568 LDAC pin to its inactive level,…,**1**,candidate,…
> "LDAC appeared NOWHERE in the design, which left a CMOS input floating on the
> DAC. **Tied, not driven:** a hardware LDAC was considered and declined…"

The part exists, with a quantity, a value and a rationale. The schematic page
still lists tying it as an open action — **and the `digital-and-supervision.md`
drawing (lines 22–50) does not show the `LDAC` pin or `R-LDAC` at all**, which is
the same class of defect as F20. The consequence text is identical in both
("every exit from `CLR` … throws intermediate values at the mod jacks for
100–200 µs"), so this is purely a status disagreement: *open* vs *done*.

---

## F14 — Whether the 1 kΩ load-divider error still exists. **Medium**

**Gone.** `ADR 0006:619–620`:

> - **The load-divider error is gone**, for any load. The −11.9 and −23.5
>   cents/octave figures below become historical.

`pitch-stage.md:261–264`: "**The load no longer matters** … An earlier version of
this section said to trim against the real patch because the 1 kΩ divided
against it. **That error is gone.**"

**Still live:**

- `ADR 0006:455–458` (the table the "below" points at) prints −11.9 and −23.5
  cents/octave and "Five octaves up, that is 59.4 cents and 117.6 cents" with no
  historical marker, 160 lines *before* the line that retires it.
- `ADR 0006:500–519` ("What this costs, and how it is paid") is entirely built on
  the live error: "**The calibration is specific to the load it was made
  against.** Re-patching pitch from one VCO to two on a passive mult changes the
  gain by 0.98 % — about **58 cents at five octaves up**" and "**Calibrate with
  the real patch connected.**"
- `ADR 0006:470–474` — "Trimmed against 100 kΩ and then played into 50 kΩ, that is
  **+29 cents sharp on every note**; into 33 kΩ, **+59 cents**."
- `ROADMAP.md:190` — "| **Pitch DC load sweep: open / 100k / 50k / 33k** | E9 |
  **Quantifies the 1 kΩ divider error against the real patch**, and tells you how
  much a re-mult actually shifts tuning (ADR 0006) |"
- `ADR 0006:521–531` also still declines jack-side feedback outright — "Feeding
  the op-amp's feedback from the jack side eliminates the error properly but puts
  the patch cable's capacitance inside the loop … **That is real stability work,
  on a board without one, to fix something a screwdriver already fixes.**" —
  which the same ADR reverses at :607–614.

`ROADMAP.md:191` was correctly updated for the *other* consequence of the same
change ("**A GATE, not a reassurance**"), which shows the sweep was done on one
row and not the adjacent one.

`pitch-stage.md:161–164` retains the figures too, but explicitly as the case
being argued against, which reads correctly.

---

## F15 — The 2.4-cent BAT54S leakage argument. **Medium**

`docs/decisions/0006-cv-channel-allocation.md:695–698`:

> a BAT54S's ~2 µA of Schottky leakage through the 1 kΩ output resistor is 2 mV,
> which is **2.4 cents of temperature-dependent pitch error** — reintroducing
> exactly what the matched network and the trimmers were bought to remove.

`hardware/bom.csv:51` (`D-JACK-CLAMP`):

> (b) LEAKAGE: inside the feedback loop the op-amp absorbs it, so **the 2.4-cent
> BAT54S error goes to identically zero for any diode.** BAV99 kept anyway -
> silicon costs nothing and **the reasoning no longer depends on it**.

The clamp moved to the driver side, inside the loop, so the 2.4 cents is zero.
ADR 0006 still presents it as a live pitch error term of the same order as its
entire static budget. Part choice is unaffected (both say BAV99); the **cents
number** is stale, and it is one of the figures a reader would sum into F5.

---

## F16 — DAC INL in cents. **Medium**

- `ADR 0006:413–414`: "DAC integral nonlinearity … (±4 LSB typical is **0.66
  cents**, ±12 LSB is **2.0 cents**)"
- `pitch-stage.md:304`: "| DAC INL, ±4 LSB typical | **~0.4 cents** | Curvature…"
- Derived: 1 LSB at the pitch jack = DAC full scale 5.000 V × gain 2 ÷ 65536 =
  **152.6 µV**; ±4 LSB = 610 µV = **0.73 cents**; ±12 LSB = **2.2 cents**.

The ADR's 0.66 comes from dividing the **9 V output range** by 65536 (137 µV/LSB)
— the same 9 V-span error as F6. The pitch page's ~0.4 is not derivable from any
stated premise. The correct figure is larger than both, and (per F5) is the
largest static term in the chain.

---

## F17 — Pitch trim range. **Medium**

`docs/decisions/0006-cv-channel-allocation.md:399`:

> **Keep the trim range small — 5 to 10 % — around a fixed precision resistor.**

`docs/decisions/0006-cv-channel-allocation.md:368` and `:621`, same document:

> At **200 Ω** it contributes 2 %, which is ~2 ppm/°C against the LT5400's own drift

> - **`TRIM-GAIN` shrinks to 200 Ω** (0 → +2 %)

`bom.csv:106` and `pitch-stage.md:130` both specify 200 Ω / 2 %. The "5 to 10 %"
instruction is stale and, at 5 %, would put a 500 Ω trimmer in series with R2.

The cost table at `ADR 0006:387–390` has the same problem and is worse, because
it is quantitative:

> | Trim range | Net ratio tempco | Drift over 10 °C |
> | 5 % | 22 ppm/°C | **2.4 cents** |

It has no 2 % row; its smallest entry is **35× `pitch-stage.md:289`'s 0.068
cents** for the part actually specified. Two reasons for the gap, neither
stated: the table uses the 9 V lever (F6), and its "fixed 0.1 % 10 ppm/°C
resistor" is a **discrete** fixed leg — the topology the LT5400 decision
replaced. The series leg is now an LT5400 section tracking at 1 ppm/°C, already
counted separately. The table is arithmetic about a circuit that no longer
exists, and it is the table ADR 0006 uses to conclude "the precision-network
argument was over-engineering" (:395–396) — a conclusion `bom.csv:15` and
`pitch-stage.md:291–300` reverse.

---

## F18 — Mod jack range. **Medium**

`hardware/module/mod-channels.md:64,75,95` — "**exactly ±10.000 V**", "| Range |
±10.05 V (40.2 kΩ fudge) | **exactly ±10.000 V** |", "Intercept is `k · V_ref` =
10.000 V". Verified: `4 × 5.000 − 3 × 3.3333 = +10.000`, `4 × 0 − 3 × 3.3333 =
−10.000` ✓.

`hardware/module/mod-channels.md:140–141`, 65 lines later, states the current
range as the superseded one:

> **On the range:** **±10.05 V** uses the DAC's *full* 0–5 V span. ADR 0006's
> 0.25–4.75 V window is a **pitch-channel reserve**…

`mod-channels.md:101–102` does the same inside the historical parenthetical
("±10.05 V has 1.4 V of margin"), where it is correct in context. Line 140 is
not in that context — it is a standalone clarification of what the stage does
now.

---

## F19 — Current out of the ch7 buffer. **Medium**

`hardware/module/mod-channels.md:16` (drawing): `(~1.3 mA total into 4 × 10k)` —
correct for 3.3333 V / 2.5 kΩ = 1.333 mA.

`hardware/module/mod-channels.md:182–183`:

> DAC ch7 drives one OPA2197 half; that half drives four 10 kΩ inputs in
> parallel. **At 2.5 V into 2.5 kΩ that is 1 mA**, comfortable for the part.

Same page, 166 lines apart, on the same node. Benign for part selection (both are
comfortable), but it is the 2.5 V survival of F9 reappearing as a load figure.

---

## F20 — The pitch drawing omits three parts its own value table specifies. **Medium**

`hardware/module/pitch-stage.md:13–37` draws: `TRIM-OFFSET`, the `VREFOUT`
follower, `R1`, `R2`, `TRIM-GAIN`, `R-OPAMP-IN`, `C-FB-PITCH`, `D-JACK-CLAMP`,
`R-OUT-PROT`.

**Not drawn, though specified in the same page's Component values table:**

| Part | Specified at | Where it belongs |
|---|---|---|
| `C-AA-PITCH` 10 nF | `pitch-stage.md:135`, `bom.csv:114` | `R-OPAMP-IN` node to `AGND` — "**THE ACTUAL PITCH FILTER**" (`bom.csv:114`) |
| `C-FILT-PITCH` 10 nF | `pitch-stage.md:136`, `bom.csv:119` | at the jack |
| `R-BIAS-DAC` 100 k | `pitch-stage.md:322–325`, `bom.csv:120` (qty 6) | at the DAC pin |

Also absent: the `R-OPAMP-IN` that `bom.csv:50` allocates to the `VREFOUT`
follower (qty 7 covers "Pitch, mod 1-4, the mod offset buffer, **the VREFOUT
follower**"). `mod-channels.md:13–40` likewise omits `R-BIAS-DAC` on ch2 and ch7.

This matters because `pitch-stage.md:224` declares the drawing authoritative
("The drawing above is right") in the course of settling F1, and because
`R-BIAS-DAC` exists to stop the output sitting at a rail before power-on reset —
a part whose absence from the drawing is exactly the failure `bom.csv:120`
describes.

---

## F21 — DAC grade. **Medium**

**Locked to C.** `bom.csv:12`: "**GRADE LOCKED TO C.** The grade letter selects
REFERENCE GAIN as well as reset state - A/B are gain 1 (2.500V full scale), C/D
are gain 2 (5.000V). An A-grade part would halve everything…"
`ADR 0006:146–152`: "**Not 'A or C', which this line used to say.** … **Only C
satisfies both requirements.**"
`mod-channels.md:150,169–174`: "the grade is **locked**", "**The grade lock is now
load-bearing twice**: once for reference gain, once for this."

**Still "A/C".** `docs/decisions/0004-cv-interface-module.md:437`:

> The DAC's own `CLR` pin already does exactly what is wanted — **an A/C grade
> part** clears to zero scale, which parks pitch subsonic and the mod channels at
> 0 V (ADR 0006)

True of the reset state, false of the decision: an A-grade part halves every
output and leaves ch7 unable to reach 3.3333 V. The sentence also carries F10's
"subsonic". ADR 0004's strikethrough banner covers the *watchdog*, not the grade
claim.

---

## F22 — Channel numbering. **Medium**

Agreed allocation: `ADR 0006:9–15` — pitch ch1, **breath analog (no DAC
channel)**, mod 1–4 ch2–5, ch6 spare, ch7 mod offset; `bom.csv:12` — "Populate 6
of 8: pitch, 4 mods, mod offset; channels 6 and 8 spare"; `mod-channels.md:20,23`
draws ch2 with "(ch3, ch4, ch5 identical)" ✓.

**Stale against it, all inside ADR 0006:**

- `:428` — "**With breath locked to channel 2** there is no genericity conflict".
  Channel 2 is Mod 1. Breath is on no channel.
- `:322` — "**Channels 2–6** run on ordinary 1 % discretes". Channel 6 is spare;
  the channel that needs stating is **7**.
- `:437` — "**Channels 2–6** need only to be linear and repeatable". Same.
- `:7` / `:17` — the decision heading says "**Six channels from an octal DAC**"
  and the text ten lines later says "**only five of them come from the DAC**".

---

## F23 — "20 cents of breath-correlated pitch bend". **Medium**

`docs/decisions/0004-cv-interface-module.md:299–302`:

> it modulates that diode's forward voltage by ~80 mV — about **20 cents of
> breath-correlated pitch bend**, needing no ground path … costs about twenty
> cents and is the whole fix.

`docs/decisions/0006-cv-channel-allocation.md:562` repeats it in its dynamic-error
table: "| **The module's analog rail and the umbilical feed share one 1N5817** …
| **~20 cents** |".

`hardware/module/power-entry.md:54–61` refutes the number (not the part):

> **The "20 cents of breath-correlated pitch bend" that followed is not.** It
> implies ~21 % pitch sensitivity to the +12 V rail. Pitch full scale is set by
> the DAC's *internal* reference, and AVDD comes from the LM317, so the real path
> is 75 mV → LM317 line regulation (0.52 mV/V) → 39 µV on AVDD → OPA2197 PSRR
> (114 dB) → **0.15 µV = 0.00018 cents** `[calc, A7]`. The 20-cent figure is a
> survival from the rail-divider topology ADR 0006 already deleted.

A factor of ~10⁵ on a pitch-domain number, with the refutation on the power page
and the claim standing in two ADRs. `power-entry.md:63–66` keeps the part for
other reasons and explicitly warns "Left as it was, the next reviewer who checks
the arithmetic deletes the part."

---

## F24 — `R-MODGAIN` cited as the 40.2 kΩ part it no longer is. **Medium**

`bom.csv:66`: `R-MODGAIN` is now `10k / 30k 1% metal film`.

Two documents still source the breath summer's feedback resistor from it:

- `hardware/module/breath-output-stage.md:126` — "| **R-FB** | 40.2 kΩ 1 % | Fixed ×4. **Same E96 part as `R-MODGAIN`** |"
- `hardware/bom.csv:127` (`R-BREATH-SUM`) — "R-IN 10k, R-FB 40.2k. **Same E96 feedback part as R-MODGAIN, bought on the same reel**"

40.2 kΩ was the four-resistor mod version's fudge value, retired by
`mod-channels.md:63–64` and `bom.csv:66`. The reel-sharing argument is now void,
and `mod-channels.md:137` ("Buying the four sets from one reel makes it much
better than worst case for free") no longer has a breath part to share with.
Values themselves are fine; the sourcing rationale is stale.

---

## Low-severity findings

**F25 — DAC AVDD rail.** Derived value `1.25 × (1 + 475/150) = 5.21 V`
(`bom.csv:38`). **5.21 V**: `power-entry.md:18`, `digital-and-supervision.md:40,43`,
`pitch-stage.md:89`, `breath-output-stage.md:43,100,103`,
`breath-receive-stage.md:55`, `ADR 0004:159,190`, `ADR 0005:125`, `bom.csv:38,109,128`.
**5.25 V**: `bom.csv:37` (`U-REG-DAC` description — "**Adjustable LDO set to
5.25V**", contradicting `R-REG-SET` one row below), `ADR 0004:132`,
`ADR 0004:282` (power-tree diagram, `[LM317LZ 5.25V]`), `ADR 0006:542`,
`ADR 0006:688`, `ROADMAP.md:47`. 0.8 % — irrelevant to pitch accuracy (full scale
is the internal reference, per `ROADMAP.md:189`), but it is the number E6 will be
measured against.

**F26 — Handover frequency.** "~16 kHz" at `pitch-stage.md:178,179` and
`ADR 0006:613` is the 1 nF result; at the specified 2.2 nF it is 7.2 kHz. Rolls
up into F3.

**F27 — Spare op-amp halves.** `bom.csv:13` and `breath-output-stage.md:129–131`:
twelve halves, **ten used, two spare**. `ADR 0006:551`: "Cost: two resistors and
**the last spare op-amp half** in `U-OPA-PITCH`."

**F28 — Part alternatives vs the grade lock.** `ADR 0006:33`: "Use an **octal**
16-bit DAC (**DAC8568 or AD5676**) and populate six." The `CLR`-safety and
reference-gain arguments (F21) are specific to the DAC8568 grade suffix; the
alternative is offered with no equivalent analysis, against a BOM locked to
`DAC8568CIPW`.

**F29 — A-grade pitch range.** `ADR 0006:148`: "pitch becomes −2…+2.25 V". With
the 0.25–4.75 V window halved (0.125–2.375 V) and `V_ref` unchanged at 2.500 V,
the range is −2.25…+2.25 V. Minor, inside a counterfactual.

**F30 — Cost of deleting `C-FILT-PITCH` at 1 MHz.** `bom.csv:119`: "Deleting it
cost **30dB** at 1MHz". `pitch-stage.md:213–214`: "**−41 dB** at 1 MHz against the
**6 dB** the shelf gives alone" — a 35 dB difference. (The 10 nF figures at
`pitch-stage.md:192`, −16 dB at 100 kHz and −36 dB at 1 MHz, check out against
1 kΩ × 10 nF = 15.9 kHz ✓.)

**F31 — B/D grade mod jack voltage.** `mod-channels.md:171–173`: "a B/D part would
put **+2.5 V** on all four jacks". `Vout = 4X − 3X = X` at midscale: true for D
(gain 2, midscale 2.5 V); for B (gain 1, midscale 1.25 V) it is +1.25 V. The
safety conclusion holds; the number covers one of the two grades.

**F32 — Pitch reconstruction corner in the latency budget.**
`latency-budget.md:64`: "Pitch is **15.9 kHz** and costs ~10 µs". With
`C-FILT-PITCH` restored and `C-FB-PITCH` at 2.2 nF, `pitch-stage.md:213` gives
**−3 dB at 12.2 kHz** (~13 µs). Immaterial to the budget; the corner figure has
not been re-derived since the restoration.

---

## Facts asserted but never derived

1. **The DAC8568 grade → reference-gain mapping.** Load-bearing three times —
   full scale, `CLR` state, and ch7's ability to reach 3.3333 V — and unverified
   in both places it is stated. `ADR 0006:151–152`: "**confirm the gain/grade
   mapping against SBAS430**, which no browser in this sandbox could reach";
   `bom.csv:12`: "CONFIRM the gain/grade mapping against SBAS430 - ti.com was
   unreachable when this was written." **The single highest-value unverified fact
   in this domain.** If A/B–C/D does not map to gain 1 / gain 2, F9, F10, F18 and
   F21 all change at once.

2. **The LT5400 option code.** `pitch-stage.md:312–314` and `bom.csv:15`: "OPTION
   CODE still needs a browser this sandbox did not have." A 1:1 quad in MSOP-8 is
   asserted orderable; nothing confirms the option exists.

3. **`C-FB-PITCH` = 2.2 nF as "maximally flat".** `pitch-stage.md:212–214` asserts
   "−3 dB at 12.2 kHz … and −41 dB at 1 MHz" with no transfer function shown, and
   the page's only printed transfer function (line 186) is the 1 nF shelf. The
   prior art the ADR cites as precedent is two orders of magnitude away —
   `ADR 0006:607–608`: "All four surveyed DAC-driven designs do both, with a
   single **18–22 pF** part." No document bridges 18–22 pF to 1 nF to 2.2 nF.

4. **The 18° / <10° phase margins.** Stated identically in `pitch-stage.md:221–222`
   and `bom.csv:108`, with no model, cable capacitance per metre, op-amp GBW, or
   load set. These are the numbers that make F1 a Showstopper, so they deserve a
   derivation or a `[calc]` tag.

5. **The ringing bound.** `pitch-stage.md:267–272`: "`Q = √(R_eff·C_load / R2·C_fb)`.
   Safe to about 10 nF, but joining PITCH to the MOD (82 nF) or BREATH (330 nF)
   jacks through a passive mult gives **44–67 % overshoot** — several semitones of
   transient on every note." No value of `R_eff` is given and the overshoot range
   is not tied to either capacitance. This is a musical failure mode on the one
   channel that must be in tune.

6. **`TRIM-GAIN` tempco = 0.068 cents.** `pitch-stage.md:289`. From the stated
   premises (~100 ppm/°C cermet, 2 % of ratio, 10 °C, 2.25 V lever) I get
   0.054 cents. The trailing clause "costing 0.04 cents" is unexplained — neither
   a difference nor a ratio of any other figure on the page.

7. **"Discrete resistors 0.38 cents".** `pitch-stage.md:292` and `bom.csv:15`.
   Derivable only as an RSS of two 10 ppm/°C parts (14.1 ppm × 2.25 V = 0.38 ✓,
   and "fifteen times worse" ✓ against 0.027) — but the RSS assumption is never
   stated, and the competing figure at `pitch-stage.md:301` (~1.2 cents) is not
   derivable from any stated premise at all.

8. **The op-amp swing limit ±11.45 V.** Three derivations of one number.
   `ADR 0006:120–121`: "±12 V rails less **~0.35 V of Schottky** leaves ±11.65 V,
   and an OPA2197 reaches ~±11.45 V". `mod-channels.md:101–102` and
   `pitch-stage.md:153–155`: "an OPA2197 on ±12 V less **two Schottky drops**
   reaches ~±11.45 V". One drop or two, and whether the OPA2197's RRIO headroom is
   counted on top, changes the margin at ±10.000 V.

9. **`R-OUT-PROT`'s worst-case ladder.** `bom.csv:41` gives 269 / 312 / 322 / 464 mW
   with no circuit stated for any of them beyond "a fuller ladder". Since this is
   the number the rating must clear (F2), the four cases need writing down.

10. **`C-FILT-MOD` 82 nF C0G is probably not buyable.** `bom.csv:65`: "PACKAGE IS
    PROBABLY WRONG: 82nF in C0G/NP0 almost certainly does not exist in 0805 …
    Unverified because every distributor site was proxy-blocked." Flagged in the
    BOM, invisible in `mod-channels.md:96`, which specifies "82 nF C0G" flat.

11. **`TRIM-OFFSET` is not buildable as specified.** `pitch-stage.md:316–320`:
    "`V_ref` nominal *is* `VREFOUT`, and a divider can only go below it, so the
    nominal sits at an end stop with no downward authority." `R-TRIM-RANGE`
    (`bom.csv:118`) is status `open` with no values. The pitch offset authority
    therefore has no committed circuit, while `bom.csv:107` states its range as
    "~50mV on a 2.5V reference is ~60 cents" — a number from a network that does
    not yet exist.

---

## Verified consistent

Checked term by term and found in agreement across every document that states them:

1. **`CLR` direction and rail — today's change propagated cleanly.**
   `digital-and-supervision.md:42–48` draws `AVDD ───┤ CLR ◄── [R-CLR-PU] 10k`,
   annotated "**PULL-UP. Active low. Held INACTIVE.**", with `[LK-CLR pad]` to GND
   for bring-up. `bom.csv:67` (`R-CLR-PU`, 10 k 1 %, qty 1): "CLR has no driver and
   is tied INACTIVE - **pulled high**. A solder pad to ground beside it lets CLR be
   asserted BY HAND". No `R-CLR-PD` survives anywhere in the corpus; no document
   contradicts the direction or the rail. *Caveat:* only
   `digital-and-supervision.md` names the rail (AVDD 5.21 V), and the row is
   attributed to ADR 0004, which never mentions the pull — ADR 0004 still
   describes `CLR` as monostable-driven (F11).

2. **Channel allocation.** Pitch ch1; mods ch2–5; ch7 mod offset; ch6 and ch8
   spare; six populated. `ADR 0006:9–23`, `bom.csv:12`, `mod-channels.md:14,20,23`,
   `R-BIAS-DAC` qty 6 (`bom.csv:120`), `R-OPAMP-IN` qty 7 (`bom.csv:50`) — the
   extra one being the `VREFOUT` follower. Consistent. (The prose naming in
   ADR 0006 is not — F22.)

3. **Mod channel transfer function.** `k = 3`, gain `1 + k = 4`, `V_ref = 3.3333 V`,
   intercept `k·V_ref = 10.000 V`, `R1 = 10 k`, `R2 = 30 k`, eight resistors.
   `mod-channels.md:54,63,93–95`, `bom.csv:66`, `ADR 0006:102`. Arithmetic verified:
   ±10.000 V exactly at both ends.

4. **Mod tolerance arithmetic.** `mod-channels.md:120–126`: zero point ±50.5 mV,
   span 19.703–20.303 V (−1.49 %/+1.52 %), "About ±18 cents per octave". I
   reproduce ±50 mV (`∂Vout/∂k = Vdac − V_ref = −0.8333 V`, `Δk = ±0.06`), span
   19.70–20.30 V from `k = 3 × (1 ± 2.02 %)`, and 1.5 % × 1200 = 18 cents ✓.

5. **Mod reconstruction filter.** 82 nF × 1 kΩ = **1.94 kHz**, jack side of
   `R-OUT-PROT`. `mod-channels.md:37,96`, `bom.csv:65`, `ADR 0006:629`,
   `latency-budget.md:64` (82 µs group delay ✓). Consistent.

6. **Clamp placement.** `D-JACK-CLAMP` BAV99, qty 6, **driver side** of the 1 kΩ.
   `pitch-stage.md:31–33`, `mod-channels.md:33–35`, `breath-output-stage.md:58–60`,
   `bom.csv:51`. Consistent in all four. (The *cents* rationale is not — F15.)

7. **Pitch window and transfer function.** DAC window 0.25–4.75 V, jack −2…+7 V,
   slope exactly 2.000, intercept −2.500 V, full-scale reserve −2.500…+7.500 V =
   ±600 cents. `pitch-stage.md:46–52,152–155`, `ADR 0006:430–436` (the reserve
   box), `mod-channels.md:140–142`, `README.md:46`. Arithmetic verified.

8. **`C-AA-PITCH` = 10 nF, ahead of the op-amp, 15.9 kHz.** `pitch-stage.md:135,202`,
   `bom.csv:114`, `ADR 0006:626–627,634`. Consistent, and inside ADR 0006's own
   10–20 kHz pitch window. `1 kΩ × 10 nF = 15.92 kHz` ✓.

9. **The loop rate.** 4 kHz, six DAC words per pass, 96 µs at 2 MHz.
   `firmware/README.md:22`, `latency-budget.md:62,146`, `carrier.md:573,591`,
   `ADR 0004:53–57`, `ADR 0006:181–183`, `ROADMAP.md:47–48`. `6 × 32 bits / 2 MHz =
   96 µs` ✓. Consistent everywhere including the umbilical's 2 MHz spec.

10. **`R-OPAMP-IN` = 1 kΩ, qty 7, no gain error on pitch.**
    `pitch-stage.md:87–90,132`, `mod-channels.md:66–69,184–187`, `bom.csv:50`,
    `ADR 0006:685–690`. Consistent, including the reversal note that it *was*
    wrong on the four-resistor mod version (−196 mV) and is harmless now.

11. **`TRIM-OFFSET` ahead of the buffer, `R-OFFINJ` deleted.**
    `pitch-stage.md:129,131,235–247`, `bom.csv:107`, `ADR 0006:375–379`. Consistent;
    no `R-OFFINJ` row survives in `bom.csv`. (Buildability is separately open —
    see "asserted but never derived" #11.)

12. **`TRIM-GAIN` = 200 Ω, in series with R2, 0 → +2 %, one-sided.**
    `pitch-stage.md:130,326–329`, `bom.csv:106`, `ADR 0006:366–370,621–623`.
    The *value* is consistent everywhere; only the range instruction (F17) and the
    cost table are not.

13. **The internal reference is disabled at reset and must be enabled first.**
    `ADR 0006:163–165,650–653`, `pitch-stage.md:139–150`, `bom.csv:12`,
    `firmware/README.md:60–62`, `digital-and-supervision.md:124–126`. Consistent,
    including the sticky-register refresh requirement.

14. **The ch7-not-refreshed failure mode.** `4 × Vdac` clipping at ≈ +11.45 V on all
    four mod jacks, undetectable without `MISO`. `mod-channels.md:163–167`,
    `firmware/README.md:53–62`. Numerically and causally consistent.

15. **`D-JACK-CLAMP`, `R-OUT-PROT` and `C-FILT-*` ordering on mod and breath.**
    Cap on the **jack side**, clamp on the **driver side**, resistor between.
    `bom.csv:51,62,65`, `ADR 0006:625–628`, `mod-channels.md:231–233`,
    `pitch-stage.md:231–233`. Consistent, including pitch being the stated exception.

16. **`C-DECOUPLE` = 19.** `bom.csv:42` and `digital-and-supervision.md:60–66` agree
    on the count and on the reason it dropped (74HC123 and LM311 deleted).

---

## What to fix first

1. **F2** — one power rating for `R-OUT-PROT`, propagated to `bom.csv`'s `part`
   column, `pitch-stage.md:133` and `breath-output-stage.md:127`. Two of the three
   currently under-specify the part below its own worst case.
2. **F1 + F3** — strike "1 nF across the feedback resistor" from `ADR 0006:611`
   and `:595`; pick one value and re-derive `pitch-stage.md:178–189` at it.
3. **F5 + F6 + F16** — delete the orphaned second table at `pitch-stage.md:301–304`,
   add the INL and op-amp rows to the first at the corrected levers, **state a
   total**, then re-point `ADR 0006:293–299`, `ADR 0006:316`,
   `pitch-stage.md:121–122` and `power-entry.md:83` at it.
4. **F8 + F9** — one row of `ADR 0006:180–186`: the mod offset is **3.3333 V**,
   **refreshed every pass**; delete the "Breath zero offset" row.
5. **F11** — `mod-channels.md:150,215–218`, `firmware/README.md:54` and
   `ROADMAP.md:51` still assume a watchdog that does not exist. `ROADMAP.md:51`
   tests for behaviour the design no longer has.
