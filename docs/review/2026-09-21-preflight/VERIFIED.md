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
