# VERIFIED — preflight wave

## A11 — `+12V` is three nets, and that is worse than `AGND`

**Re-checked, 2026-09-21. CONFIRMED** at `hardware/module/power-entry.md:13-24`.
One `+12V` label at the IDC branches through `D1` to the module analog rail and
through `D2` to the umbilical export rail. A transcription taking the label
literally **merges all three and shorts out `D1`, `D2`, `FB1`, `FB2`, `C1`,
`C2` and the entire LT1641 load switch** — i.e. exactly the split whose whole
stated purpose is keeping instrument current out of the analog rail, and which
`D-REVPOL` is qty 3 to achieve.

## A11's own self-check — it was right to ask, and the answer is no

A11 closed by flagging that if an earlier wave had already named the module
analog return, it had invented a second name and made things worse. **It had —
there are now three proposals, A11's included:**

| Source | Sense conductor | Module analog return |
|---|---|---|
| First cold review, `D3` | — | `AGND_MODULE` |
| Pipeline wave, `P11` | `AGND_SENSE` | `AGND` or `AGND_MOD` |
| **A11** | `UMB_BREATH_N` | `M_ARET` |

**Not adopting any of them unilaterally.** A11's argument for avoiding the
`AGND` token in *either* name is the strongest one on the table — after the
rename, `grep -rn AGND` finds only sites still needing work, which the other
two schemes do not give you. But this is a convention decision, it is cheap for
the owner to settle, and settling it three different ways is how the problem
started.

## ADR 0004 carried two contradictory umbilical pin maps — FIXED

A11 reported it; **confirmed and repaired in the same pass.**
`docs/decisions/0004-cv-interface-module.md:97-98` paired
`SCLK / DIG_GND` and `MOSI / CS`, against its own corrected table 730 lines
later at `:828-831` and against `config/figures.yaml: umbilical-pinmap`, both
of which say `SCLK / MOSI` and `CS / DIG_GND`.

**Why the checker missed it:** `umbilical-pinmap`'s `forbidden` list matched the
**table-cell** spelling (`| MOSI / CS |`) and not the **code-block** spelling
(`MOSI      / CS`, runs of spaces). Both spellings are now listed.

**This is the fourth time a forbidden pattern has missed a different formatting
of the same value** — and I had edited that exact block earlier today without
noticing the pairing was wrong.

## A12 — two blind spots in my own tooling, both fixed

**Claim 1:** `verify-datasheets.py` checks rows↔files, so it **cannot see a BOM
part with no manifest row at all** — which is exactly where the ESP32-S3, the
QMI8658C and the PESD12VS1UB were hiding.

**CONFIRMED and fixed.** The check now walks `bom.csv` for manufacturer part
numbers absent from the whole manifest. Two iterations were needed: matching on
the manifest's `part` column alone gave 8 hits with false positives (a document
banked as "Gateron KS-33 low-profile switch" does not match a BOM row reading
"KS-33 Red (linear)"), and a naive token rule flagged values like `330nF` and
`500mW`. It now searches the whole manifest text and rejects the
value-with-unit shape. **Three real gaps remain and are now permanently
visible:** `SW-POWER`, `U-ESD-USB` (USBLC6-2SC6), `D-TVS-BREATH` (PESD12VS1UB).

**Claim 2:** `merge-manifests.py` under-reports historical rows because it uses
exact lowercase equality. **CONFIRMED and fixed** — it now normalises and
matches on containment, so "MPXV4006 AN1646" resolves against "MPXV4006DP".

## A12 — three corpus corrections, verified and applied

| Claim | Verified | Fixed |
|---|---|---|
| `D-REVSHUNT` SS34 is specified `DO-214AC`; the datasheet says **SMC (DO-214AB)** | `[datasheet SS34.pdf p.1]` — "MECHANICAL DATA / Case: SMC (DO-214AB)", repeated 3× more. DO-214AC is the **SS14** | Package corrected. Wrong footprint on unretrofittable reverse-polarity protection |
| `0004:743` "13.35 mm of aluminium each side" | `[calc]` (50.50 − 24.0)/2 = **13.25**. 13.35 implies a ⌀23.8 bore, **below the drawing's stated minimum** | Corrected |
| `carrier.md:847` says `U-TVS-SPI` is SOT-23-6; `bom.csv` says -5 | The 4-channel part is the **-5**. `bom.csv` is right, the schematic page is wrong | Corrected |
| `F-CHAIN` package column still said 1206 | The row's **own notes** already said 0805 | Corrected — the fix had landed in the prose and not the field |

## A12 — a container fact that invalidates advice I wrote

**`pdftotext` and `pdfinfo` are not installed here.** I had warned in
`pcb-pipeline.md` that some PDFs have no text layer; the sharper truth is that
**any script shelling out to `pdftotext` in this container returns nothing from
every document.** Use `pymupdf`, which is present.

And A12 corrected my own list twice: the **TE socket catalogue is fully
text-bearing** (2294 chars/page over 104 pages) and should not have been on it —
while the **Gateron drawing is the dangerous case**, averaging 1841 chars/page
of spec prose so a script "gets something", with the dimensioned page carrying
only `0.2/0.4/1.7/3.0`. **Silent partial failure beats a blank.**

## A3 — the sensor transfer function was wrong, and it was a SETTLED figure

**Claim:** the MPXV4006's transfer function is `VS × [(0.1533·P) + 0.053]`, not
`+ 0.04`. So the pedestal is **0.265 V**, not 0.200 V, and full scale is
**4.864 V**, not 4.80.

**Re-checked, 2026-09-21. CONFIRMED VERBATIM** from
`datasheets/other-semi/MPXV4006DP.pdf`:

```
Transfer Function (kPa):  Vout = VS*[(0.1533*P) + 0.053] ± 5.0% VFSS
```

`[calc]` at VS = 5.0: P=0 → **0.265 V**; P=6 kPa → **4.864 V**. The corpus had
0.200 → 4.796.

**Where 0.200 came from:** the datasheet's own **cover-page line**, "0 to
6 kPa, 0.2 to 4.8 V Output" — which contradicts the transfer function printed
inside the same document. The sensitivity was always right (5 × 0.1533 =
0.7665 ≈ 0.766 V/kPa); only the offset coefficient was wrong, and 0.04 belongs
to the **MPXV5004** family.

`sensor-full-scale` corrected 4.80 → **4.86 V**. This is the first time a
figure the register marked **settled** has been refuted by a banked document —
which is the outcome this wave was created to produce.

**What survives:** `inamp-full-scale` (−9.94 V) is derived from the **span**,
and the span is unchanged — 4.864 − 0.265 = 4.599, the datasheet's 4.6 V VFSS.
The one sensor number the corpus had right is the one everything downstream
rests on.

## A10 — two corrections to things I wrote myself

**1. `F-CHAIN`: I used the wrong current, and overstated the objection 3.9×.**

I wrote into `bom.csv` that the polyfuse's 1.0–7.5 Ω gives "0.1 to 0.75 V of
drop" — computed at the **fuse's 100 mA hold current** rather than the
circuit's actual draw.

`[calc]` at the real 25.8 mA: **26–194 mV**, not 100–750 mV. And A10 adds the
reason it is harmless that I missed: the 74HC165's thresholds and the key
pull-ups are **on the same rail**, so the RC crossing time is independent of
`VCC` and `key-release-time` does not move.

**Objection withdrawn on the voltage drop.** The confirmed defects remain: the
package column said 1206 where the drawing says 0805 (already fixed), and a PTC
does not cover the 12 V short the row names.

**2. `riso-ref-topology`: I filed TI's answer as a "fourth option". It is not.**

SBOS737C Figure 56 takes `R_F` **at `V_OUT`** — so the DC loop closes at the
load. **It IS the in-loop topology, with an AC feedback path added.** The
in-loop-versus-out-of-loop framing the dispute opened with is a false
dichotomy; the real question is not *which side* but *whether the AC path
exists*. Entry corrected.

## A4 — both decisions verified at source before landing

A4 decided two things that had been blocking schematic finalisation. Findings
are claims, so the decisive citation for each was re-read by hand out of the
banked PDF — not out of A4's report — before anything was edited.

**1. `cref-out-node`. CONFIRMED.** Re-extracted from
`datasheets/texas-instruments/REF5050.pdf` (SBOS410O, pp. 26 and 29):

> *"Confirm that a output capacitor (CL) is connected from VOUT to GND. For
> output stability, verify that the equivalent series resistance (ESR) value of
> CL less than or equal to 1.5 Ω."* — §8.4.1
>
> Figure 8-6: *"CL = 1µF to 50µF for REF50xxI, REF50xxAI"*
>
> *"A resistor in series with the output capacitor is optional."* — §9.4.1.1
>
> *"Add a high-frequency, 1µF capacitor in parallel between the output and
> ground…"* — §9.4.1.1

The argument is forced rather than preferred, which is what makes it decidable
on paper: a `C_L` on the REF5050's own `VOUT` exists in **every** valid
topology of this circuit, so one of the qty-2 parts is spoken for and the other
is the §8.4.1 supply bypass. Nothing is left over for the buffer's output.

The last clause also confirms A4's §1.5 withdrawal of the "missing series
1–1.5 Ω resistor" that `bom.csv:76` had asserted — TI calls it optional in so
many words, and the 1–1.5 Ω window is the *noise* recommendation, not the
stability bound.

**2. `riso-ref-topology`. CONFIRMED, including the numbers.** Re-extracted from
`datasheets/texas-instruments/OPA2197.pdf` (SBOS737C):

> *"For the 10-µF ceramic capacitor shown in Figure 56, RISO, a 37.4-Ω
> isolation resistor, provides separation of two feedback paths for optimal
> stability. Feedback path number one is through RF and is directly at the
> output, VOUT."* — §8.2.3 p.30
>
> `RF 1 MΩ · CL 10 µF · RISO 37.4 Ω · RFx 10 kΩ · CF 39 nF` — Figure 56
>
> *"…a loop gain phase margin of 89°. Any other load capacitances require
> recalculation of the stability components: RF, RFx, CF, and RISO."*
>
> *"ZO Open-loop output impedance | f = 1 MHz, IO = 0 A, See Figure 26 | 375 |
> Ω"* — EC table, **two occurrences** (p.8 and p.10)
>
> *"High Capacitive Load Drive Capability: 1 nF"* — p.1, and §7.3.5 p.22

Every figure A4 built on is in the document as A4 quoted it, and TI's own
warning that other load capacitances need recalculation is *why* A4 had to
argue the transfer rather than assume it.

**What was NOT independently verified, and should be said plainly:** A4's phase
margins are its own behavioural `ngspice` model, not a bench and not TI's
macromodel. The check that makes them usable is internal to the report — the
same model run on Figure 56 *as printed* returns 87.4° against TI's published
89°, and it independently reproduces two results earlier waves got by different
means (the no-resistor hazard and the out-of-loop case). That is good enough to
commit a topology and a BOM, and **not** good enough to skip the macromodel run
before copper. Recorded as a precondition on the PCB pipeline's SPICE stage.

**One thing A4 got right that I had got wrong, and it is the second time in
this wave:** I filed TI's Figure 56 as a "fourth option" in the dispute. It is
not an option — it is the in-loop topology with an AC path added. A4 reached
the same conclusion independently and from the datasheet rather than from my
note, which is the point of the cold rule.

## A4-10 and A13-4 — the same escape, found twice, hours apart

Both reviewers found that `sensor-full-scale`'s correction had not propagated,
and that `check-staleness.py` scored **zero** hits against eleven live derived
statements. A13 named the mechanism exactly: three `forbidden` patterns miss by
one character each against a case-sensitive literal `find`.

**Verified at source before propagating**, from
`datasheets/other-semi/MPXV4006DP.pdf`:

> `Voff 0.152 0.265 0.378 V` — Table, p.4. *"Offset (Voff) is defined as the
> output voltage at the minimum rated pressure."*
>
> `VFSS — 4.6 — V`
>
> *"Vout = VS*[(0.1533*P) + 0.053]"* — transfer function, p.6

Two things follow that neither reviewer stated and that changed what got
edited. **The receive page's "spec band" was always correct** — 0.152–0.378 V
is the datasheet's own min/max, and only its *typical* was wrong. And **the
span is untouched**, so `inamp-full-scale`, the −9.94 V row and the in-amp gain
all survive; the only in-amp number that moved did so for an unrelated reason
(raw 2.18483 used where the effective 2.1611 belongs), which A6 found
separately.

Eleven statements fixed, twelve patterns added, and the rule that would have
prevented it written into the entry: **when a figure moves, grep the corpus for
the OLD value first and add a pattern per spelling found** — not from the
document in front of you.
