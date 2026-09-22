# A1 — The breath signal chain, end to end, as one transfer function

**Agent:** A1, cold. Read no directory under `docs/review/**`.
**Date:** 2026-09-21.
**Slice:** mouthpiece → tube/restrictor → MPXV4006DP → excitation reference and
buffer → `R1`/`R1b` → 2 m pair → `R2`/`R3`/`C_diff`/`C_cm`/bias pair → INA828
with its `REF` trimmer → gain/offset stage → optional shaper → `BREATH` jack.

**Report only. Nothing was changed.**

Provenance on every claim: `[repo] path:line`, `[calc]` with arithmetic shown,
`[datasheet]` with document and page, `[from memory]`, `[tool]` for a command I
ran.

Findings are indexed by **net or BOM reference**, not by file. Where a defect
has two ends, both ends are named in the heading so a colliding agent lands on
the same row.

---

## Summary

The chain's **core arithmetic reproduces**. Sensor transfer function, span,
in-amp raw and effective gain, `inamp-full-scale`, `breath-zero-ref`, the
482 Hz differential pole, the ADC divider and counts, the output stage's
attenuator-then-×4 topology and the shaper's diode currents all re-derive from
the stated parts without adjustment. The design is sound end to end.

What does not close is **everything one hop downstream of a figure that moved**,
plus one node-identity error and one part-accounting error:

| # | Node / ref | What |
|---|---|---|
| 1 | `U-DIFFRX` | **`-9.6V` is live in `bom.csv` and `unplaced.csv`** — a forbidden value of `inamp-full-scale`, missed by one space |
| 2 | `U-BREATH`, `R-ADCDIV`, `D-TVS-BREATH`, ADR 0003, ADR 0005 | **Nine live statements of the refuted `0.2–4.7 V` sensor range**, all missed by one or two characters |
| 3 | in-amp output node | `−4.7 V` vs `−4.64 V` — the receive page carries the value the output page refutes |
| 4 | `TRIM-BREATH-ZERO` / `REF` | The spec-band endpoints `0.332–0.826 V` are computed with the **raw** gain three lines below the typical computed with the **effective** gain |
| 5 | `BREATH` jack, power-on | ADR 0006's `0.2 to 1.7 V` is `0.437 × 0.5…4` — the **refuted** `breath-zero-ref`. Correct is `0.29 to 2.29 V` |
| 6 | `BREATH`/`AGND` pair | Link CMRR: **four** values, **two** requirements, **no stated frequency**, and the quoted margin belongs to the configuration the design does not build |
| 7 | `R-BIAS-INAMP` | The part that sets the CMRR floor is filed in **`pitch-stage/bom.csv`**, and its tolerance is absent from the page that derives the floor |
| 8 | `U-DIFFRX`, `R-GAIN-INAMP`, `R-SER-BREATH`, `C-FILT-BREATH`, `D-CLAMP-BREATH`, `R-BREATH-SUM`, `R-BREATH-OFF` | Seven drawn parts sit in `unplaced.csv` |
| 9 | `U-RESP` / `U-OPA-PITCH` / `C-DECOUPLE` | The shaper's two halves are counted twice; `C-DECOUPLE` does not count them at all |
| 10 | `POT-OFFSET` / `R-OFF` | The page budgets the **less** sensitive rail and ignores the more sensitive one (1.91× vs 0.42×) |
| 11 | `BREATH` jack, `SW-POWER` | A 0.29–2.30 V step on the jack every time the instrument is switched on or off, undocumented |
| 12 | in-amp output node | `inamp-full-scale` is called "**jack span**" in two documents. It is not the jack |
| 13 | breath latency | Three totals in ADR 0003 (`< 1.5 ms`, `~2.6 ms`, `~3.1 ms`), and no budget at all for the analog channel the jack carries |
| 14 | `breath-working-point` | A **disputed** figure is used as settled in five corpus files, and two of them derive part values from it |

`tools/check-staleness.py` reports **PASS, no live stale values** `[tool]`
against every one of findings 1–5. The checker is a literal, case-sensitive
substring find (`text.find(bad, start)`) `[repo] tools/check-staleness.py:169`,
so all five escaped on spelling.

---

## 1. Does the arithmetic close end to end?

Recomputed every step from the parts as drawn. **It closes.**

```
[calc] SENSOR                                     [datasheet MPXV4006DP, transfer fn]
  Vout = VS x (0.1533*P + 0.053),  VS = 5.000 V
  P=0    : 5 x 0.053            = 0.265 V     = pedestal
  P=6 kPa: 5 x (0.9198 + 0.053) = 4.864 V     = sensor-full-scale
  span                          = 4.599 V     (datasheet VFSS typ 4.6 V)

[calc] IN-AMP                                     [repo] breath-sense-link.md:140,153
  G_raw  = 1 + 50k/42.2k                     = 2.18483
  divider= 1M/(1M + 11k)                     = 0.989130
  G_eff  = 2.18483 x 0.989130                = 2.16106
  full   = 4.599 x 2.16106                   = 9.9386 V  -> -9.94 V   MATCHES
  REF    = 0.265 x 2.16106                   = 0.5727 V  -> 0.573 V   MATCHES

[calc] GAIN TABLE on breath-sense-link.md:146-153   every row reproduces
  10 / 4.6            = 2.1739  ("raw gain needed 2.174")     MATCHES
  2.1739 / 0.98913    = 2.1978  ("gain needed 2.198")         MATCHES
  (2.1978-2.18483)/2.1978 = 0.59 %  ("the 0.6 % shortfall")   MATCHES

[calc] OUTPUT STAGE                               [repo] breath-output-stage.md
  attenuator floor 7.15/(7.15+50) = 0.12511                   MATCHES 0.125
  working point 10 / 4.638        = 2.156                     MATCHES 2.16x

[calc] ADC BRANCH                                 [repo] breath-adc.md:34-41
  4.864 x 0.6 = 2.918 -> /3.3 x 4096 = 3622 counts            MATCHES
  0.265 x 0.6 = 0.159 -> 197 counts                           MATCHES
  2.410 x 0.6 = 1.446 -> 1795 counts                          MATCHES

[calc] FILTERS
  1/(2*pi*22k*15n)   = 482.3 Hz   ("482 Hz", both legs 11k)   MATCHES
  1/(2*pi*20k*15n)   = 530.5 Hz   ("not 531")                 MATCHES
  1/(2*pi*1k*330n)   = 482.3 Hz   (output RC)                 MATCHES
  1/(2*pi*6k*47n)    = 564.2 Hz   (anti-alias)                MATCHES

[calc] SHAPER, all five rows                      [repo] breath-response-shaper.md:98-104
  (2.32-0.6)/15k = 114.7 uA -> "115 uA"; (232+115)/232 = 1.496 -> "1.494"
  (1.25-0.6)/15k =  43.3 uA -> "43 uA";  (125+43)/125  = 1.347 -> "1.347"
  (4.97-0.6)/15k = 291.3 uA -> "291 uA"; (497+291)/497 = 1.586 -> "1.586"
                                                              ALL MATCH
```

Three **untracked** numbers between the tracked ones do **not** reproduce, and
all three are listed as findings below: the working-point in-amp voltage
(finding 3), the `REF` spec-band endpoints (finding 4), and the power-on jack
offset (finding 5). A fourth, the offset-table endpoints, is off by 0.5 %
because the page computes them with `R-FB` = 40 k while its own Values table
and `bom.csv` specify **40.2 k** `[repo] breath-output-stage.md:82,122-124,147`:

```
[calc]  -40.2k x (-12/95.3k)               = +5.061 V   page says +5.04 V
        -40.2k x (5.21/21.0k - 12/95.3k)   = -4.913 V   page says -4.89 V
        R-FB/R-IN = 40.2/10 = 4.02, not 4.00; so the stage is 0.503x - 4.02x
```
Harmless to the conclusion, but the drawing says `[R-FB 40k]` and the Values
table says `40.2 kΩ`, which is two values for one part on one page.

---

## 2. Does each stage's stated input match the previous stage's stated output?

Walked every boundary. **One mismatch, and it is the split's own signature.**

| Boundary | Upstream states | Downstream states | |
|---|---|---|---|
| sensor → buffer | `0.265 – 4.86 V` `[repo] 0003:101` | `0.265 – 4.86 V` `[repo] carrier.md:112` | ok |
| buffer → `R1` / ADC | `0.265 – 4.86 V` | `0.265` / `4.86` `[repo] breath-adc.md:35-39` | ok |
| pair → in-amp | span 4.6 V | span 4.6 V `[repo] breath-sense-link.md:148` | ok |
| in-amp → gain stage | `0 … −9.94 V` full, **`−4.7 V` working** `[repo] breath-receive-stage.md:126,194` | `−4.64 V` working `[repo] breath-output-stage.md:39` | **MISMATCH** |
| in-amp → shaper | as above | `4.64 V` hard blow `[repo] breath-response-shaper.md:91,103` | **MISMATCH** |
| gain stage → jack | 10 V at 2.156× | — | ok |

### Finding 3 — in-amp output node: `−4.7 V` vs `−4.64 V`

`breath-output-stage.md:47-53` carries an explicit, dated correction:

> `−4.69 V` was computed with the in-amp's *raw* 2.18483, and the working point
> is the *effective* 2.1611 … `[calc] (2.411 − 0.265) × 2.1611 = 4.638`

That correction reproduces `[calc]`: `2.146 × 2.16106 = 4.638`, against
`2.146 × 2.18483 = 4.689`. It is right.

**It did not land on the page the reader reaches first.**
`breath-receive-stage.md` — the page that owns the in-amp — still says
`−4.7 V` twice, at `:126` ("about −4.7 V in real playing") and at `:194`
("a hard blow reaches about **−4.7 V** at the in-amp"). `−4.7` is a rounding
of the refuted `−4.69`, not of `−4.638`, which rounds to `−4.6`. So the
in-amp's owner page carries the raw-gain value that the downstream page
identifies by name as the error.

`breath-output-stage.md` then repeats `−4.7 V` twice more in its own prose and
drawing (`:43`, `:59`), fourteen lines below its own correction.

Same class as `breath-zero-ref`'s `0.579` and `inamp-full-scale`'s `−10.05`:
**the 1 MΩ bias divider omitted.** Third live instance of that one omission.

No grep can reach it. `4.7` is not in any forbidden list and cannot be — it is
a legitimate numeral in several other quantities.

---

## 3. The CMRR budget

### Finding 6 — `BREATH`/`AGND` pair: four values, two requirements, no frequency

**Re-derived both ends.**

**The `60.2 dB` (`R1b` omitted) reproduces; the page's intermediate does not.**

```
[calc]  BREATH leg = R1 1k + R3 10k = 11k ;  AGND leg = R2 10k (no R1b)
        1e6/1.011e6 = 0.98912957
        1e6/1.010e6 = 0.99009901
        difference  = 9.6944e-4        page states 9.79e-4
        20*log10(1/9.6944e-4) = 60.27 dB    -> "60.2 dB"  MATCHES
        20*log10(1/9.79e-4)   = 60.18 dB    -> also "60.2 dB"
```
`[repo] breath-sense-link.md:192`. The printed **9.79e-4 is wrong** — it is
9.69e-4. Both round to the same dB so the conclusion survives, but a reader
re-deriving from the intermediate gets a different number than a reader
re-deriving from the resistors.

**The `73 dB` floor reproduces exactly, at ±1 %:**

```
[calc]  with R1b fitted both legs are 11k; the residue is the bias pair
        d(ratio)/dRb * dRb = Rs/(Rb+Rs)^2 * dRb
        = 11e3 / (1.011e6)^2 * 2e4    (two 1M parts at 1%, 2% relative)
        = 2.1524e-4   ->  20*log10(1/2.1524e-4) = 73.3 dB     MATCHES "73 dB"
        at 0.1% parts the same formula gives 93.3 dB
```
`[repo] breath-sense-link.md:83`. `R-BIAS-INAMP` is `1M 1%` `[repo] bom.csv:77`,
so 73 dB is the ±1 % answer and it is correct.

**The `70.2 dB` does not reproduce from anything stated.**

```
[calc]  10^(-70.2/20) = 3.09e-4, i.e. an equivalent bias mismatch of 1.44%
        adding R1/R1b 1% and R2/R3 0.1% series mismatch (worst case 40 ohm):
          1e6/(1.011e6)^2 * 40 = 3.913e-5  -> 88.1 dB alone
          linear sum with the bias term: 2.544e-4 -> 71.9 dB
          RSS:                            2.188e-4 -> 73.2 dB
        Neither is 70.2 dB.
```
`[repo] breath-sense-link.md:77`, marked `[calc, A2]`. I cannot reconstruct it.

**So the corpus holds four answers to "what does `R1b` buy":**

| Claim | Source | R1b buys |
|---|---|---|
| "fifty times" the rejection | `breath-sense-link.md:197` (moved from the receive page) | ~34 dB |
| 60.2 → 70.2 dB | `breath-sense-link.md:77`, `[calc, A2]` | 10 dB |
| 60.2 → 73 dB | `breath-sense-link.md:83` (moved from `carrier.md` §2) | 13 dB |
| — | `breath-receive-stage/sim/README.md:19-29` repeats the 60.2 / 73 / "fifty times" trio | |

`breath-sense-link.md`'s closing section flags **one** of the three pairs —
"fifty times" against "about 13 dB" — and says "No winner was picked here"
`[repo] :234-240`. **The 70.2 against 73 pair is not flagged at all**, and the
two sit six lines apart in the same file, both inside the passage the
consolidation moved verbatim.

**Two requirements, not one.**

| Requirement | Where |
|---|---|
| **60 dB** | `[repo] 0003:358`, `[repo] 0003:517`, `[repo] breath-sense-link.md:195` ("the **entire** 60 dB budget"), `[repo] breath-receive-stage.md:164` |
| **58.5 dB** | `[repo] breath-sense-link.md:78`, `[repo] sim/README.md:20,75` |

The 58.5 dB is described as "an independently derived requirement" and **the
derivation appears nowhere in the corpus**. I reconstructed it and it is almost
certainly this:

```
[calc]  common mode = the PWR_GND drop, ADR 0003's own 350 mA row = 58.9 mV
        target error = 1 LSB of 10 V at 16 bit = 152.6 uV at the in-amp output
        referred to input: 152.6u / 2.16106 = 70.6 uV
        58.9e-3 / 70.6e-6 = 834  ->  58.4 dB          reconstructs to 0.1 dB
```
Plausible, but it is a claim resting on nothing *in the repository*, and it
differs from the round 60 dB asserted in four other places. **At 60 dB the
`R1b`-omitted case has 0.2 dB of margin, not 1.7 dB.**

**The margin is quoted against the configuration the design does not build.**
`breath-sense-link.md:77-79` reads "Without it the link CMRR falls from 70.2 dB
to 60.2 dB … : **1.7 dB of margin**". `60.2 − 58.5 = 1.7`, so the 1.7 dB is the
**`R1b`-omitted** margin — an argument *for* fitting the part. With `R1b`
fitted the margin is 11.7 dB or 14.5 dB depending on which of the two
with-`R1b` numbers is right.

`sim/README.md:19-21` then reads it the other way: *"puts the link at 60.2 dB …
against … 58.5 dB — 1.7 dB, resting on two parts' tolerance"* — asserting 60.2
as **the design's** CMRR. `pcb-pipeline.md` ranks this simulation **first of
five** on that 1.7 dB. The first-ranked simulation in the project is justified
by the margin of a circuit that is not being built.

**No figure in this budget carries a frequency, and the terms are not
frequency-flat.** The resistive terms (60.2 / 70.2 / 73 dB) are essentially DC.
The capacitor term is not:

```
[calc]  CM-to-DM from C_cm mismatch, Rs << |Z_C|:  delta = Rs * 2*pi*f * dC
        Rs = 11k, C_cm = 1.5 nF, dC = full relative spread
        +-5% (dC = 0.15 nF) at 482 Hz: 11e3*3029*1.5e-10 = 5.00e-3 -> 46.0 dB
        +-1% (dC = 0.03 nF) at 482 Hz: 11e3*3029*3.0e-11 = 1.00e-3 -> 60.0 dB
```
Both of the page's capacitor figures — "~46 dB" at ±5 % and "±1 % is needed to
clear 60" `[repo] breath-sense-link.md:204-206` — reproduce **exactly**, and
only if the frequency is the 482 Hz differential corner and `dC` is the full
relative spread. Neither assumption is stated.

The consequence matters: at ±1 % the capacitor term is **60 dB at 482 Hz**,
which is *below* both resistive with-`R1b` figures and at or below the
requirement on its own. At 50 Hz the same term is ~80 dB and irrelevant.
`sim/README.md:71` says "The band that matters is the mains harmonics and the
SPI hash, not DC" — so the corpus is aware the answer is frequency-dependent
and still states every term as a single number.

### What would settle it — stated without picking a winner

I do not have a bench and did not run the deck, so I file this as an open
question with a decision procedure, not a verdict.

1. **Run the `ngspice` deck `sim/README.md` already specifies**, worst-case over
   tolerance, `R1b` fitted and omitted, **sweeping frequency** rather than
   reporting one number, and with the `REF` buffer modelled (TI's 5 Ω source-
   impedance spec, `[repo] bom.csv:103` quoting SBOS792A §8.1). That directly
   discriminates 10 dB from 13 dB from "fifty times" and it discriminates the
   resistive terms from the capacitive one.
2. **Pin `R-BIAS-INAMP`'s tolerance in the document that derives the floor.**
   The 73 dB result is a function of it and of nothing else. See finding 7.
3. **Derive the requirement once, in one place, and cite it.** Either 58.5 dB
   with its arithmetic shown, or 60 dB with its provenance; not both. As long
   as two live requirements exist, "1.7 dB of margin" and "0.2 dB of margin"
   are both defensible readings of the same corpus.
4. Note that step 1 cannot settle **finding 6's margin question** on its own —
   that is settled by step 3, which is a documentation act, not a simulation.

`R1` and `R1b` are instrument-side and unretrofittable `[repo]
breath-sense-link.md:14,202`, so this is decided before the body closes or not
at all.

---

## 4. The `REF` trimmer — range, what it nulls, spec band vs typical

**Verdict: the range is correct and it does cover the spec band, not the
typical. The band's endpoints are computed with the wrong gain.**

What it nulls: the sensor's zero-pressure pedestal, *ahead* of the panel gain
pot, which is what keeps GAIN and OFFSET independent `[repo]
breath-receive-stage.md:136-147`. That argument is sound and is corroborated by
the Yamaha WX5 interaction the page cites.

The band is the datasheet's own `V_off` min/typ/max, quoted in the page as
`[datasheet MPXV4006DP p.4: "Voff 0.152 0.265 0.378 V"]` `[repo]
breath-receive-stage.md:120`.

### Finding 4 — `TRIM-BREATH-ZERO`: the band endpoints omit the bias divider

```
[calc]  with the EFFECTIVE gain 2.16106 (the one breath-zero-ref uses):
          0.152 x 2.16106 = 0.3285 V
          0.265 x 2.16106 = 0.5727 V   <- stated, correct, tracked
          0.378 x 2.16106 = 0.8169 V

[calc]  with the RAW gain 2.18483 (bias divider omitted):
          0.152 x 2.18483 = 0.3321 V   <- stated as "0.332 V"
          0.378 x 2.18483 = 0.8259 V   <- stated as "0.826 V"
```

`breath-receive-stage.md:118-121` states **`0.573 V`** for the typical and
**`0.332 V to 0.826 V`** for the band, three lines apart, computed with two
different gains. The same pair appears in `TRIM-BREATH-ZERO`'s note as
"(0.332-0.826 V)" `[repo] bom.csv:68` and
`[repo] hardware/module/breath-receive-stage/bom.csv:3`.

This is the **same omission** `breath-zero-ref`'s `escape_note` names as the
project's signature error, in the document the register declares as that
figure's **owner**, immediately adjacent to the corrected value, in text
written to record the correction. Fourth live instance.

**The range decision is unaffected.** `0 → +1.0 V` covers 0.817 V and 0.826 V
alike, with 18–21 % of margin, and it covers the whole spec band rather than
the typical — which was the point of moving off the earlier `0 → +0.6 V`
`[repo] breath-receive-stage.md:121-125`. That reasoning is correct and
reproduces: `0 → +0.6 V` covers pedestals to `0.6/2.16106 = 0.2777 V` (page
says 0.275 V, using the raw gain), which is below the 0.378 V max.

**One thing the trimmer's budget does not have:** `REF` is derived from the
LM317 rail (`dac-rail`, 5.21 V), whose absolute value is bench-selected across
a **0.66 V worst-case spread** at E7 `[repo] config/figures.yaml:236`. The
trimmer nulls the rail's absolute value at commissioning, so only *drift after
commissioning* matters — and that drift is budgeted nowhere. The same rail is
also the DAC's `AVDD`, so it carries DAC load steps. See finding 10, which is
the same rail arriving at the same jack by a second path with **4.6× more
gain**.

---

## 5. Failure states

| State | What the jack does | Where stated | Correct? |
|---|---|---|---|
| **`CLR`** | Nothing | `[repo] breath-receive-stage.md:211-218` | **Yes.** Verified: `CLR` reaches only DAC channels; `REF` comes from `TRIM-BREATH-ZERO` through a buffer off the LM317 rail, never `VREFOUT`. Both Interfaces tables declare `CLR` "**Reaches no part of this circuit**" `[repo] breath-sense-link.md:52`, `breath-receive-stage.md:46`. Nothing in the chain touches the DAC. Sound |
| **Unplugged** | OFFSET knob position **less 0.2 to 1.7 V** | `[repo] 0006:197-215` | **No — see finding 5** |
| **Power-on** | Same row; "not a defined state", accepted | `[repo] 0006:201,215-220` | **Incomplete — see finding 11** |

The *structure* of the unplugged answer is right and well argued: `R-BIAS-INAMP`
holds the in-amp's inputs at module `AGND`, the differential is zero, the in-amp
rests at `V_REF`, and the inverting stage carries that to the jack. ADR 0005's
withdrawn-`R-PD-BREATH` block `[repo] 0005:357-380` and ADR 0006's table both
get the mechanism right, and ADR 0006 is the more precise of the two. Good work
that only needs its number recomputed.

### Finding 5 — `BREATH` jack, instrument absent: `0.2 to 1.7 V` is the refuted `breath-zero-ref`

```
[repo] 0006:210-213
  "the in-amp rests at V_REF = breath-zero-ref ... puts the jack at the
   OFFSET knob's position less 0.2 to 1.7 V, depending on where GAIN is set"

[calc] the downstream stage is 0.5x to 4x, inverting:
   with breath-zero-ref = 0.573 V (current):  0.573 x 0.5 = 0.287
                                              0.573 x 4   = 2.292   -> 0.29 to 2.29 V
   with 0.437 V (REFUTED, the old pedestal
                 AND the bias divider omitted): 0.437 x 0.5 = 0.219
                                                0.437 x 4   = 1.748  -> 0.2 to 1.7 V
```

**`0.2 to 1.7 V` is `0.437 × [0.5, 4]` to two significant figures.**
`config/figures.yaml:103` records ADR 0006 as one of the five places that
carried `0.437 V`. The literal `0.437 V` **was** removed from ADR 0006 and
replaced with a citation — the row now reads "` V_REF` = `breath-zero-ref`",
which is exactly rule 1. **The number derived from it, on the same line, was
not recomputed.** The citation was fixed; the consequence of the citation was
not.

This is the named failure mode with the fix visible in the same sentence, and
no checker can reach it: `0.2` and `1.7` are bare numerals that cannot go in a
forbidden list.

Second-order, from the same arithmetic: ADR 0006 says the cost is "a patch left
connected can wake with up to **5 V** of standing breath CV" `[repo] 0006:219`.

```
[calc] jack = OFFSET - (0.287 ... 2.292)
       OFFSET endpoints are +5.04 V and -4.89 V   [repo] breath-output-stage.md:122-124
       worst case = -4.89 - 2.29 = -7.18 V
```
The window is **−7.2 V to +4.8 V**, not ±5 V. `R-OUT-PROT` and
`D-JACK-CLAMP` are unaffected (both rated to the ±12 V rails), so this is a
statement defect, not a hazard.

### Finding 11 — `BREATH` jack / `SW-POWER`: an undocumented step on every switch-on

The module's ±12 V comes up with the rack. The **instrument's** +12 V is behind
`U-LOADSW`, whose `ON` pin is the panel toggle `SW-POWER` `[repo]
umbilical-load-switch.md:16`, and whose output ramp is `loadswitch-gate-cap`,
**49–197 ms** `[repo] config/figures.yaml:347`.

So for 49–197 ms after rack power-on — **and for the same window every time the
player flips `SW-POWER`, mid-patch** — the module's INA828 and `REF` buffer are
live while the sensor is not. The jack sits at `OFFSET − (0.29…2.29 V)` and
then **steps** to `OFFSET` as the sensor comes up.

ADR 0006's table covers "at rack power-on, before firmware writes" and treats
breath as a static unknown. It does not record that the state is **transient**,
that the transition is a step of up to 2.3 V into whatever the patch is driving,
or that `SW-POWER` reproduces it on demand. ADR 0005's block covers "switched
off — or unplugged" `[repo] 0005:357-358` but states the jack goes "to the
OFFSET knob's position", omitting the `V_REF` term entirely — which is the
same understatement ADR 0006 corrects, so the two ADRs disagree about the
unplugged jack voltage by 0.29–2.29 V.

Worth one row in ADR 0006's power-on table and one line in `E10`, which already
pulls the umbilical mid-note `[repo] breath-receive-stage.md:223` and would see
this if it knew what to look for.

---

## 6. Is anything in this chain stated in two places?

Yes. Five duplications, one of which has already diverged.

### Finding 12 — in-amp output node: `inamp-full-scale` is stated at the wrong node, twice

`config/figures.yaml:26` defines it correctly: "**In-amp output** at full sensor
range". Two documents call the same number the **jack** span:

- `[repo] breath-sense-link.md:153` — "`R_G = 42.2 kΩ → G = 2.1848, effective
  2.1611` | **jack span 9.94 V**"
- `[repo] bom.csv:118` and `unplaced.csv:30` (`R-GAIN-INAMP`) — "Effective 2.161
  after the bias/series divider -> **9.94V jack span**"

The jack is two stages downstream, behind a 0.5–4× panel control, and the
`BREATH` jack reaches 10 V at a **2.156×** setting from a **4.64 V** hard blow
`[repo] breath-output-stage.md:44,53`. The in-amp's 9.94 V is reached only at
6 kPa, which `breath-working-point` says real playing never reaches.

The knock-on is the "0.6 % shortfall absorbed by the panel gain knob"
`[repo] breath-sense-link.md:155`. That is correct arithmetic for a design
where the in-amp alone had to make 10 V. Once the output stage exists, the
panel knob is absorbing a 2.156× working point and the 0.6 % is not a
shortfall in anything. The sentence survives its own premise.

### Finding 14 — `breath-working-point` is disputed and is being used as settled

`config/figures.yaml:315-322` marks it **DISPUTED**, value literally `"DISPUTED"`,
with three candidates, and records that `2.8 kPa` is "cited to ADR 0003, which
does not contain it; the two schematic pages cite each other".

I confirmed that: `2.8 kPa` appears nowhere in ADR 0003 `[tool]`. ADR 0003 says
"Normal wind-controller playing sits around **0–5 kPa**" `[repo] 0003:140`.

`2.8 kPa` is nevertheless stated as live fact in five corpus locations, and in
three of them it is **load-bearing**:

| Where | What it decides |
|---|---|
| `[repo] breath-receive-stage.md:193-197` | the commissioning GAIN target, "near 2.1×" |
| `[repo] breath-output-stage.md:39,42-45` | **the 0.5–4× range spec of `POT-GAIN`**, explicitly "the point of specifying the range from playing rather than from the sensor" |
| `[repo] breath-response-shaper.md:91-103` | **`R-RESP` = 15 kΩ**, sized so the diode knee lands at a quarter of a hard blow; `[repo] bom.csv:74` states the same |
| `[repo] breath-adc.md:37-38` | the playable-span count, cited to `breath-receive-stage.md` |
| four `circuit.yaml` files declare `fig:breath-working-point` | |

`breath-output-stage.md` cites it as "**(ADR 0003)**" `[repo] :42` — the same
false attribution the register already records, still live in the newest page in
the chain. And `breath-adc.md` cites it as "[2.8 kPa from
breath-receive-stage.md]", which is the circular pair the register names.

Two BOM values (`POT-GAIN`'s range floor via `R-GAIN-FLOOR`, and `R-RESP`)
therefore rest on a figure whose own register entry says it is undecided and
that `decided_by: M1, with a player and a manometer`. Both are recoverable at
E10 — `POT-GAIN`'s taper and `R-RESP` are both already flagged as bench
questions — so this is a provenance defect rather than a design error. It is
worth saying plainly in the pages: at 3–4 kPa (the published-figures candidate)
the working point moves to 1.5–2.0× and `R-RESP`'s knee moves with it.

### Finding — `~1594` vs `1598` counts (playable ADC span)

One derived quantity, two values, three files:

- `[repo] breath-adc.md:40` — "playable span above rest ≈ **1598** counts"
- `[repo] carrier.md:177` and `carrier.md:373` — "the **~1594**-count playable span"
- `[repo] key-chain-loom.md:126` — "a playable breath span of **~1594** counts"
- `config/figures.yaml:131` pins it at "~1594 counts" in `key-scan-current`'s
  `companion` field

```
[calc] 1795 - 197 = 1598   from breath-adc.md's own rows, which reproduce
```
`1598` is the arithmetic; `~1594` is what three other files and the register
carry. `key-scan-current`'s own `escape_note` already records that `~1594
counts` "appear in two or three corpus files" and that "DEDUPLICATING it is
still owed" `[repo] config/figures.yaml:132-147`. The restructure has since
added a third value-bearing site (`breath-adc.md`) that **derives** it, and it
derives a different number. The owed deduplication now has a specific answer:
`breath-adc.md` derives it, the other three cite it.

### Finding — the output RC is specified on two pages, already diverged

`breath-sense-link.md`'s moved component table carries a row that belongs to
`breath-output-stage`:

| | `breath-sense-link.md:142` | `breath-output-stage.md:151-152` | `bom.csv:69` |
|---|---|---|---|
| value | `1 kΩ + 330 nF film` | `R-OUT-PROT 1 kΩ, 1206 ≥500 mW` + `C-OUT-BREATH 330 nF film` | `1k 1%, >=500mW` |
| corner | **~480 Hz** | **~482 Hz** | **~480Hz** |
| power rating | **absent** | ≥500 mW | ≥500 mW |

`[calc] 1/(2π×1k×330n) = 482.3 Hz`. The 480/482 split is cosmetic; the missing
power rating is not — the link page's component table is where a reader lands
after following `breath-sense-link/circuit.yaml`'s own
`refdes:R-OUT-PROT` edge, and the rating is the whole of that part's spec
(`[repo] bom.csv:87` — "POWER RATING IS NOT OPTIONAL").

### Finding — `R4`/`R5` tolerance is specified in `bom.csv` and absent from the page that derives the floor

`breath-sense-link.md:137` — "**R4, R5** | 1 MΩ | Common-mode bias return".
No tolerance. Two rows below, `C_cm` gets "**±1 % C0G**" with a whole subsection
explaining why the tolerance is load-bearing `[repo] :204-206`. The 73 dB floor
is a pure function of `R4`/`R5`'s tolerance `[calc, above]` and the page states
the floor `[repo] :83` without stating the parameter that sets it.
`sim/README.md:60` knows this — the deck must vary "The bias resistors'
tolerance, which sets the floor `carrier.md` quotes". Which brings us to:

---

## 7. BOM placement in this chain

### Finding 7 — `R-BIAS-INAMP` lives in `hardware/module/pitch-stage/bom.csv`

`[tool]` `grep -rl '^R-BIAS-INAMP,' hardware/*/*/bom.csv` → `pitch-stage`.

CLAUDE.md: "A row lives with the circuit **whose page derives its value**."
`pitch-stage.md` names `R-BIAS-INAMP` as an **explicit contrast** — the
`circuit.yaml` header block says so in as many words, listing
`pitch-stage -> R-BIAS-INAMP` as one of three edges "verified as false by
reading" `[repo] hardware/*/circuit.yaml:5`. The dependency edge was identified
as false; **the BOM row it came from was never moved.**

`breath-sense-link.md` is the page that derives `R4`/`R5`'s value, their
0.2 ppm sense-return argument and the 73 dB floor. It is also the page whose
component table omits the tolerance — which is exactly what happens when the
row with `1M 1%` in it is filed under a different circuit.

### Finding 8 — seven drawn breath parts are in `unplaced.csv`

CLAUDE.md: `unplaced.csv` "holds the rows **no schematic page names** — a count
of parts nobody has drawn".

| Ref | Drawn where | What it is |
|---|---|---|
| `U-DIFFRX` | `breath-receive-stage.md:81` | **the INA828 itself** |
| `R-GAIN-INAMP` | `breath-receive-stage.md:83`, as `R_G` | the gain-set resistor |
| `R-SER-BREATH` | `breath-receive-stage.md:66-68`, as `R2`/`R3` | module-side series pair |
| `C-FILT-BREATH` | `breath-receive-stage.md:70-74`, as `C_diff`/`C_cm` | the 500 Hz filter |
| `D-CLAMP-BREATH` | `breath-receive-stage.md:64` | input clamps |
| `R-BREATH-SUM` | `breath-output-stage.md:65,80`, as `R-IN`/`R-FB` | the fixed ×4 |
| `R-BREATH-OFF` | `breath-output-stage.md:70,72`, as `R-OFF`/`R-OFFNEG` | the ±5 V offset pair |

`D-CLAMP-BREATH`'s own notes field says it outright: *"Drawn on
hardware/module/breath-receive-stage/breath-receive-stage.md and had no row"*
`[repo] unplaced.csv:48`. The row records that it is drawn, and is filed under
"nobody has drawn it".

The cause is refdes naming: the pages draw `R2`, `R3`, `C_diff`, `C_cm`,
`R-IN`, `R-FB`, `R-OFF`, `R-OFFNEG` while the BOM carries `R-SER-BREATH`,
`C-FILT-BREATH`, `R-BREATH-SUM`, `R-BREATH-OFF`. Nothing can join them.

**This is not bookkeeping.** It is the mechanism behind finding 1: the stale
`-9.6V` sits on `U-DIFFRX`, a row that no breath page owns, so nobody editing
the breath pages ever passes over it. Every one of the five staleness escapes
below is in a file the chain's own pages do not reach.

`merge-bom.py --check` passes — "138 rows from 24 fragments | 0 problems"
`[tool]` — because `unplaced.csv` is itself one of the 24 fragments
`[repo] tools/merge-bom.py:69`. The tool cannot see this and is not meant to.

### Finding 9 — `U-RESP` / `U-OPA-PITCH` / `C-DECOUPLE`: two halves counted twice, and decoupled zero times

| Statement | Source |
|---|---|
| "Six packages, twelve halves, **TEN used** … **TWO SPARE**" | `[repo] bom.csv:67` (`U-OPA-PITCH`, qty **6**) |
| "Ten of twelve halves used across the module, **two spare**" | `[repo] breath-output-stage.md:155` |
| "**Both remaining OPA2197 halves**" | `[repo] breath-response-shaper.md:125` |
| "It costs the **last spare** OPA2197 half, and `U-OPA-PITCH` goes to six packages so there is **still one**" | `[repo] breath-receive-stage.md:165` |
| `U-RESP`, **OPA2197IDR, SOIC-8, qty 1** — "Response shaper: 1/2 shapes at /2 inverting, 1/2 restores x2 inverting" | `[repo] bom.csv:76`, `breath-response-shaper/bom.csv:5` |

The shaper's two halves are claimed **both** from `U-OPA-PITCH`'s two spares
**and** from a dedicated seventh package. Either `U-RESP` should not exist, or
`U-OPA-PITCH`'s spares are still spare and every "two spare / both remaining"
sentence is wrong.

Consequence in a third row: `C-DECOUPLE` is qty **19**, derived as "6 x OPA2197
on +/-12V = 12, INA828 = 2, DAC8568 AVDD+DVDD = 2, 74AHCT125, LT1641 VCC,
LM317 in" `[repo] bom.csv:56`. `[calc] 12+2+2+1+1+1 = 19` — reproduces, and
**counts no supply pin for `U-RESP`**. If `U-RESP` is fitted, `C-DECOUPLE` is
21. The shaper is `status=open`/`proposed`, so this is correctly catchable
before it lands — but it will land silently, because `C-DECOUPLE`'s row is in
`module/bom.csv` and `umbilical-load-switch/bom.csv`, neither of which a reader
of the shaper page visits.

### Finding 10 — `POT-OFFSET` / `R-OFF`: the wrong rail is budgeted

`breath-output-stage.md:134-138` argues "Why −12 V is acceptable here and would
not be on pitch", and budgets it:

```
[repo] "Here 50 mV moves the jack by 40k/95.3k x 50 mV = 21 mV, 0.21 % of span"
[calc] 40.2/95.3 x 50 mV = 21.1 mV                              reproduces
```

The **other** offset leg is `R-OFF` 21.0 kΩ from the buffered **5.21 V LM317
rail**, and it is not budgeted at all:

```
[calc] rail-to-jack gain through R-OFF:  R-FB/R-OFF = 40.2/21.0 = 1.914
       50 mV of LM317 movement -> 95.7 mV at the jack = 0.96 % of span
       4.6x the term the page does analyse
```

That rail is `dac-rail`: the **DAC8568's AVDD**, shared with the converter's
own load steps, and set on the bench across a **0.66 V worst-case spread**
`[repo] config/figures.yaml:236`. It is also the rail the `REF` trimmer derives
from (finding 4), so it reaches the breath jack twice, through two independent
paths, and neither is budgeted. The −12 V rail, which the page *does* budget,
is the one it correctly notes "carries no LED current".

The page's conclusion is probably still fine — LM317 line regulation is
0.52 mV/V `[repo] config/figures.yaml:472`, so rack movement is not the threat;
DAC load stepping is. But the argument as written analyses the smaller term and
is silent on the larger one, which is the shape of an argument that was written
about the wrong resistor.

---

## 8. Staleness escapes — five tracked figures, nine live statements, checker PASS

All confirmed by direct string search `[tool]` and all currently reported clean
by the commit hook: *"staleness check: PASS no live stale values"*.

The matcher is `text.find(bad, start)` — literal, case-sensitive, no
normalisation `[repo] tools/check-staleness.py:169`.

### Finding 1 — `U-DIFFRX`: `inamp-full-scale` is stale on the in-amp's own row

```
[repo] hardware/bom.csv:103 and hardware/unplaced.csv:15, U-DIFFRX notes field:
  "Output is 0V at rest to -9.6V at full (Vout = -2.185*(V_BREATH - V_AGND)
   + V_REF, with TRIM-BREATH-ZERO nulling the sensor pedestal)"

config/figures.yaml:31  forbidden: ["-9.6 V", "−9.6 V", "-10.05 V", "−10.05 V"]
```

**The row spells it `-9.6V`. The forbidden list spells it `-9.6 V`.** One space.

`inamp-full-scale`'s own `note` says `-9.6 V` "is derived from nothing and
matches no configuration" `[repo] config/figures.yaml:32`. It is live, on the
row for the part whose output it describes, in the most-cited file in the
repository, and duplicated into `unplaced.csv`.

Aggravating: the same field was corrected on 2026-09-21 for a *different* stale
value (`"-0.44V at rest to -10V at full"`), and the refutation sentence sits
~80 characters after the stale `-9.6V` it left behind. The register's own
`diode-split-rationale` escape_note describes precisely this — "A refutation
can carry a wrong replacement, and the exemption cannot tell". Here the
refutation did not even need to fire: the pattern never matched.

### Finding 2 — `U-BREATH` / `R-ADCDIV` / `D-TVS-BREATH` / ADR 0003 / ADR 0005: `sensor-full-scale`

Nine live statements of the refuted `0.2–4.7 V` range. `[tool]` confirmed
counts:

| Where | Exact live text | Why the list missed it |
|---|---|---|
| `bom.csv:41`, `breath-sense-link/bom.csv:2` (`U-BREATH`) | `"766mV/kPa, 0.2-4.7V"` | list has `"0.2-4.7 V"` — **space before V** |
| `bom.csv:43`, `breath-sense-link/bom.csv:4` (`D-TVS-BREATH`) | `"top of range is 4.7V against a 5V array's V_RWM - 300mV of margin"` | no pattern for this phrasing |
| `bom.csv:20`, `breath-adc/bom.csv:4` (`R-ADCDIV`) | `"Sensor reaches 4.7V into a 3V3 ADC"` | list has `"full scale = 4.7 V"` and `"4.7 V × 0.6"` |
| `[repo] 0003:565` | `"The sensor reaches 4.7 V while the ADC runs on 3.3 V"` | same |
| `[repo] 0005:74` | `"a 5 V part outputting **0.2–4.7 V** (ADR 0003)"` | list has `"0.2-4.7 V"` (hyphen) and `"0.2 – 4.7 V"` (spaced en dash). This is an **en dash with no spaces** |
| `[repo] breath-adc.md:49` | `"(4.7 − 0.7) / 10 kΩ = 400 µA"` | bare numeral inside a calc block |

The ADR 0005 case is the sharpest. `sensor-full-scale`'s `escape_note` says, in
capitals, that the fourth recorded instance escaped through "**an en dash with
no spaces**" `[repo] config/figures.yaml:64`. The list was then extended with
`"0.2 – 4.7 V"` (spaced) and `"0.2–4.80 V"` (unspaced, but the *other* value) —
and `0.2–4.7 V` unspaced, the exact spelling the note describes, is still not
in it, still live, in an ADR, cited to ADR 0003 as its authority, with no
refutation wording on the line. I checked the refutation regex against that
line: it does not fire `[repo] tools/check-staleness.py:64`. It is a pure
spelling escape.

**Two of the nine change a derived conclusion:**

```
[calc] D-TVS-BREATH margin against a 5 V array's V_RWM:
         stated: 5.0 - 4.7   = 300 mV
         actual: 5.0 - 4.864 = 136 mV        2.2x worse
       (conclusion unaffected and strengthened: the row already specifies a
        12 V standoff part, for a separate and correct reason)

[calc] breath-adc.md's power-up clamp current:
         stated: (4.7  - 0.7)/10k = 400 uA
         actual: (4.86 - 0.7)/10k = 416 uA
       (conclusion unaffected: both are far inside the ±2 mA clamp budget)
```

One more, semantic rather than numeric: `[repo] 0003:206` — "**The instrument
sits at 0.2 V and looks dead**" — is the refuted pedestal describing a blocked
reference port. It should be 0.265 V. The list carries `"0.2 V at rest"`,
`"reach 0.2 V at the bottom"` and `"against the 0.2 V floor"`; `"sits at 0.2 V"`
is a fourth phrasing of one number in one document. Fifth live spelling in the
owner ADR, which `escape_note_2` already calls out as the place this figure
keeps escaping.

And in `breath-sense-link.md:165`, the `R1` power argument:

```
[repo] "I = (12 − 0.2) / 1 kΩ = 11.8 mA      P = 139 mW"
[calc]  (12 - 0.265)/1k = 11.735 mA ;  P = 137.7 mW
```
Still over the 125 mW 0805 rating, so **the argument for the 1206 survives
intact** — but the input to it is the refuted pedestal.

---

## What I checked and did not find a defect in

Recorded so the next reviewer does not re-derive it.

- The **sensor transfer function, pedestal and span** against the banked
  datasheet's coefficients as quoted in the corpus. `0.053` not `0.04`;
  `0.265` not `0.200`; span 4.599 V. All consistent everywhere they are cited
  by name.
- **`inamp-full-scale` and `breath-zero-ref` themselves.** Both reproduce to
  four figures. The register's explanation of why `0.579` and `−10.05` are the
  shapes they are is correct arithmetic.
- **The 482 Hz differential pole and the 10:1 `C_diff`/`C_cm` ratio.** Both
  reproduce, and the "not 531 Hz" correction is right.
- **The CM-to-DM argument for `C_diff` dominance**, and the argument that the
  filter must sit *ahead* of the in-amp. Both sound.
- **`REF` must be buffered.** Corroborated by TI's own 5 Ω spec, quoted
  verbatim in `bom.csv` from SBOS792A §8.1.
- **The `CLR` answer.** Verified independently against the Interfaces tables of
  both circuits and the `digital-and-supervision` boundary. `CLR` genuinely
  reaches nothing in this chain.
- **The `REF`-trimmed-rather-than-grounded argument**, including the knob
  interaction it prevents. The WX5 citation is apt and the mechanism is right.
- **The buffered-attenuator-ahead-of-a-fixed-×4 topology**, and the argument
  against a rheostat in the feedback path. Correct, and the same reasoning
  correctly forbids the shaper from being placed after `POT-GAIN`.
- **The shaper's centre-detent null.** `V_wiper = (V/2)(1 − 2p)` is exactly
  zero at p = 0.5 for any input, as claimed. The topology does what the page
  says it does.
- **The excitation reference's dual-feedback compensation.** `R_ISO/(Zo+R_ISO)`
  and the pole/zero ratio do depend only on `R_ISO/Zo`, so the C_L-independence
  argument is correct as stated, and the DC-error-is-zero-by-topology argument
  holds.
- **`merge-bom.py --check`** — 138 rows, 24 fragments, 0 problems `[tool]`.

## One thing I could not settle

The `70.2 dB` figure marked `[calc, A2]` at `breath-sense-link.md:77`. I could
not reconstruct it from any combination of the stated tolerances — the nearest
I get is 71.9 dB (linear sum) or 73.2 dB (RSS). It may be correct against an
assumption not written down. It is filed as part of finding 6 rather than as a
defect on its own, because the honest statement is that I cannot reproduce it,
not that it is wrong.
