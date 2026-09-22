# G8 — `config/figures.yaml`: register health

**Slice:** G8, cold. I read no file under `docs/review/` — not this wave's
`README.md`, not any prior wave. Everything below comes from the corpus, from
`tools/`, from banked datasheets and from `git`.

**Revision measured.** The brief named `a4b80b1`. `HEAD` is `25cc740`
`[repo] git log`. `git diff --stat a4b80b1 25cc740` is **one file**,
`docs/review/2026-09-22-goal-verification/README.md`, +81 lines — outside the
§6 corpus, so the corpus under review is byte-identical at the two revisions
and the discrepancy is immaterial. I measured against **`25cc740`**.

**Pinning.** The working tree moved under me twice during this slice (see
**G8-20**), so every mechanical result below was **re-run from a private clone
checked out at `25cc740` with `git status --short` empty**, and every number
reproduced byte-identically against the run I had made in the live tree.
Findings marked `[pinned]` rest on that clone. `tools/check-staleness.py` in
the live tree currently matches the pinned copy byte for byte
`[test] md5sum → 26da4e7ba11002bee0b4d6b55d381c88 both`, so tool-level
tampering did not reach any result here — but note that **my pattern sweep
never used the checker**; it is a 40-line reimplementation of `check_figures`'
line-joining loop, which is why the `check_links([])` patch could not have
touched it.

**Headline.** The register is *factually* in very good shape — I re-derived 30
derivations and re-read six banked datasheets and found the physics almost
entirely right. What is not in good shape is the **enforcement half**:
**57 of 217 forbidden patterns (26 %) have never matched any revision of this
repository, ever**, and one entry silently loses a field to a duplicate YAML
key. Two entries contain a number that contradicts their own derivation.

---

## Summary of findings

| # | Severity | What |
|---|---|---|
| G8-1 | **high** | Duplicate YAML key silently drops a `false_positive_note` |
| G8-2 | **high** | `key-pullup-qty`'s owner does not state its own value — rule 1 broken at the root |
| G8-3 | **high** | `diode-split-rationale`: `r_d 69 mΩ` is refuted by its own entry and by the datasheet |
| G8-4 | medium | `umbilical-current`: `value` 359 mA ≠ its own `derivation`'s 358.1 mA |
| G8-5 | **high** | 57/217 patterns never matched any revision — 26 % of the guard is decorative |
| G8-6 | **high** | `sensor-full-scale`: 12 of 34 patterns never matched, in the entry that preaches grep-first |
| G8-7 | medium | `ks33-contact-bounce`: 4 of 5 patterns are paraphrases that miss the real sentences |
| G8-8 | medium | `breath-working-point`'s `decided_by` names M1; the breath gate is E2 |
| G8-9 | medium | 2.8 kPa is live in two circuits, cited to the page that withdrew it; disputed entries have no guard at all |
| G8-10 | medium | `pitch-cents-budget`'s `decided_by` describes a page state that no longer exists; candidate list is missing a term |
| G8-11 | low | `loadswitch-fb-divider`'s stated arithmetic does not reproduce (right answer, wrong working) |
| G8-12 | low | `loadswitch-timer`'s "worst case" mixes a max bound with a typical |
| G8-13 | low | `riso-ref-topology`: "Zo/10" is 37.5 not 37.4, and TI's own recalculation caveat is unrecorded |
| G8-14 | medium | Seven load-bearing quantities used in 3+ files with no register entry |
| G8-15 | medium | 392 mA vs 404 mA for the module's +12 V total — untracked, and the register restates 392 twice |
| G8-16 | low | 480 Hz and 482 Hz are the same 482.3 Hz corner written two ways across 8 files |
| G8-17 | low | 22 of 28 register keys are read by no tool; a typo'd key is undetectable |
| G8-18 | low | Line references inside the register have drifted |
| G8-19 | low | `spi-series-r` guards two of three retired refdes bare and the third only in one phrasing |
| G8-20 | **process** | The corpus and `tools/` were being edited by other slices during a read-only review |
| G8-21 | low | `check_restated` builds its exclusion set from `value` + `forbidden` only |
| G8-22 | — | What I verified against banked documents and found **correct** |

---

## 1. Schema consistency

**G8-1 — `panel-height-budget` defines `false_positive_note` twice, and PyYAML
silently drops the first one.**

`[test] [pinned]` A duplicate-key-detecting loader over the pinned file:

```
entries: 37   unique ids: 37
DUPLICATE KEYS: [('false_positive_note', 408, 423)]
```

`[repo] config/figures.yaml:408` and `:423`. `yaml.safe_load` keeps the **last**
occurrence, so the entry that loads carries only `:423` — "The candidates
107 / 97 / 112 / 124 may be quoted in text that explains why they were
superseded". The text at `:408` is gone from every loaded view of the file.

This is not a cosmetic loss. The dropped note is the false-positive guidance
for **two specific patterns in this entry's own list** —
`"~115 mm against ~110 mm usable"` and `"115 mm against ~110 mm"` — and the
surviving note covers only the 107/97/112/124 group and says nothing about the
115/110 pair. A reader who opens the loaded register sees a pattern with no
warning attached to it, and the sentences it would fire on are
`[repo] hardware/module/panel/panel.md:50` and
`[repo] docs/decisions/0004-cv-interface-module.md:745`, both of which
correctly narrate the review that produced the figure. That is exactly the
"cheapest fix is to make a true sentence wrong" trap the file elsewhere
documents at length.

Nothing reports this. `check_patterns` looks for newlines and self-refuting
markers; no tool loads the file with a duplicate-key check. **37 entries, 37
unique `id`s** — no duplicate ids, that half is clean.

**G8-17 — 22 of the 28 distinct keys in the register are read by no tool.**

`[test] [pinned]` The only keys any tool dereferences are `id`, `owner`,
`status`, `value`, `forbidden` (`tools/check-staleness.py`), plus `blocked_on`
`[repo] grep -noE 'fig\["[a-z_]+"\]|fig\.get\("[a-z_]+"' tools/check-staleness.py`.
Everything else — `derivation`, `false_positive_note`, `escape_note`,
`escape_note_2`, `escape_note_3`, `false_positive_note_2`, `threshold_note`,
`conservative_bound`, `provenance_note`, `companion`, `floor`, `toggle_row`,
`consequence`, `adaptation`, `dc_error`, `robustness`, `caught_late_note`,
`supersedes_the_constraint`, `note`, `quantity`, `candidates`, `decided_by` —
is prose for humans.

I found no *misspelled* key (the numbered variants `escape_note_2/_3` and
`false_positive_note_2` are deliberate). But the consequence is worth stating
plainly: because no schema is enforced, a typo like `forbiddden:` would remove
a figure's entire guard and produce a `PASS` line byte-identical to a healthy
run — the same failure `check_patterns`' docstring already records for empty
lists. G8-1 is the proof that silent field loss happens here in practice.

**All 37 entries carry `id`, `quantity`, `value`, `status`, `owner`,
`forbidden`.** `candidates` and `decided_by` appear on exactly the 5 unresolved
entries — correct. Seven entries have no `derivation`: the five unresolved ones
(fine), plus `free-bits` (value `3`) and `pitch-compensation`
(`2.2 nF, op-amp OUTPUT to the (−) input`), which are choices rather than
calculations and carry a `note` instead. Acceptable.

---

## 2. Does the owner actually own it?

All 37 `owner:` paths resolve `[test] [pinned]`. `check_owners` verifies 24 of
them mechanically and reports 8 as `UNCHECKED` because the value has no
distinctive token `[repo] .staleness/report.txt:3-11`. **I hand-checked all
eight.** Seven are fine:

| figure | where the owner states it |
|---|---|
| `marker-bits` (8) | `config/key-layout.yaml:147` `spare_bits_marker: 8` |
| `free-bits` (3) | `config/key-layout.yaml:149` `spare_bits_free: 3` |
| `chain-conductors` (12) | `0001:81`, `0001:160` "12 conductors per hop" |
| `chain-connectors` (8) | `key-chain-loom.md:88` "EIGHT connectors, not five" |
| `umbilical-pinmap` | `0004:900-903`, the pin table |
| `loadswitch-timer` (10 µF) | `umbilical-load-switch.md:241` |
| `ks33-contact-bounce` (5 ms) | `ks33-geometry.md:206` |

**G8-2 — `key-pullup-qty`'s owner does not state its own value. Two other
documents do.**

`[repo] [pinned]` `config/figures.yaml:299-311` names
`hardware/cluster/key-switch-network/key-switch-network.md` as owner of
`value: "24"`.

```
$ grep -c "24" hardware/cluster/key-switch-network/key-switch-network.md
0
```

`[test] [pinned]` The string "24" does not occur in that file at all, in any
form — no "24", no "twenty-four". What the page does say is
`[repo] key-switch-network.md:33` "`R-KEY-PU 2k2 1%`" and
`:125` "`R-KEY-PU` is 2.2 kΩ" — the **value** of the part, never its
**quantity**, which is what this figure tracks.

The document that states it authoritatively is a different circuit:
`[repo] hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:107`
— "`R-KEY-PU` is now **qty 24**. Found in review." And a third restates it
inside an ASCII drawing:
`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:76`
"`→ 24 pull-ups,`". Plus the BOM fragment's qty column
`[repo] hardware/cluster/key-switch-network/bom.csv:3`.

So rule 1 is inverted: the owner is silent, a non-owner asserts, and two more
restate. This is the same "a split moves a derivation into a sibling directory
and the register goes on naming the file it left" failure that
`check_owners`' own docstring says the check was written to catch — and it is
live, in the one class of figure the check skips by design. The skip is
honest (`weak`, not `pass`), but nothing has ever come back to close the eight
it hands off.

**Does any other document state a figure as if authoritative?** Beyond G8-2,
the register itself records one open case it has not closed:
`key-scan-current`'s `escape_note` says "DEDUPLICATING it is still owed: rule 1
says the owner states it and the other two cite it, and today all three
restate it" `[repo] config/figures.yaml:212-214`. I confirmed that is still
true `[repo] key-switch-network.md:131,144` and
`key-chain-loom.md:134`, all three carrying the 5.9 mA / 10 kΩ comparison
independently.

---

## 3. Is `value` correct?

I redid every derivation that has one. **`[calc]`, all arithmetic shown** —
the full script is reproducible; the line-by-line results follow in condensed
form.

### Correct, reproduced exactly

`inamp-full-scale` `1 + 50000/42200 = 2.184834`; `× 1e6/1.011e6 = 2.161062`;
`× 4.6 = 9.9409` → **−9.94 V** ✓.
`sensor-full-scale` `5×(0.1533×6 + 0.053) = 4.864` → **4.86 V** ✓;
pedestal `5×0.053 = 0.265` ✓; span `4.864 − 0.265 = 4.599` ≈ the datasheet's
4.6 VFSS ✓.
`breath-sensor-slope` `5 × 0.1533 = 0.7665` ✓.
`breath-zero-ref` `0.265 × 2.161062 = 0.5727` → **0.573 V** ✓, and both
rejected variants reproduce: `0.265 × 2.184834 = 0.579`,
`0.200 × 2.184834 = 0.437` ✓.
`key-scan-current` `3.3/2300 = 1.4348 mA` → 1.43 ✓; `× 18 = 25.83` → 25.8 ✓.
`key-release-time` node `3.3×100/2300 = 0.1435` ✓; `τ = 2200×47n = 103.40 µs` ✓;
`−103.40·ln(0.99/3.1565) = 119.894 µs` → **119.9** ✓; the 2.475 V bound gives
`138.747` → 138.7 ✓; from 0 V, `124.491` → the 124.5 the note names ✓.
`key-press-time` `τ = (2200‖100)×47n = 4.4957 µs` ✓;
`−4.4957·ln(0.8465/3.1565) = 5.9167` → **5.92** ✓; 0.825 V bound `6.8914` →
6.89 ✓; margins `250/5.92 = 42.2×` and `250/6.89 = 36.3×` ✓.
`dac-rail` `1.25×(1 + 475/150) = 5.2083` → **5.21 V** ✓.
`panel-width` `10×5.08 − 0.3 = 50.50` ✓.
`panel-height-budget` all four clear heights reproduce: `128.5 − 2×(3.0+2.8)
= 116.9`; `− 2×(3.0+3.5) = 115.5`; `− 2×(3.0+5.0) = 112.5`; content
`5+22+39+31+13 = 110`; spare `115.5 − 110 = 5.5` ✓.
`mod-reference` `k = R2/R1 = 30k/10k = 3`; gain `1+k = 4`; load
`3.3333/2500 = 1.3333 mA` → 1.33 ✓. (I first read "k=3 from R1 10k / R2 30k"
as a gain and got 4; the owner page `[repo] mod-channels.md:113` defines
`k = 3, gain 1 + k = exactly 4` and the register is consistent with it. Not a
defect — but the register's one-line `derivation` is ambiguous without the
page.)
`loadswitch-timer` `77µ × 0.150 / 1.233 = 9.367 µF` → 9.37 ✓; ADI shorthand
`62 × 150 = 9300 nF` ✓; fault times at 10 µF with net currents
`24−3 = 21 µA → 587.1 ms`, `80−3 = 77 → 160.1`, `132−3 = 129 → 95.6` ✓;
`95.6/47.5 = 2.013×` ✓; 9.4 µF worst `89.85/47.5 = 1.891×` → 1.89 ✓.
`loadswitch-gate-cap` `5µ/82n = 61.0 V/s → 12/61 = 196.8 ms`;
`10µ → 122.0 V/s → 98.4 ms`; `20µ → 243.9 V/s → 49.2 ms` → **49–197 (98 typ)** ✓.
`loadswitch-fb-divider` `35.7/5.11 = 6.9863` → 6.986 ✓;
`1.313×(1+6.9863) = 10.486` → 10.49 ✓; `0.5×(1+6.9863) = 3.993` → 3.99 ✓;
`0.5/1.313 = 0.3808` → 0.381 ✓; and the 1 %-resistor window checks:
`1.345×(1 + 35.7×1.01/(5.11×0.99)) = 10.93` and
`1.280×(1 + 35.7×0.99/(5.11×1.01)) = 10.05` ✓.
`riso-ref-topology` `1/(2π·10k·1n) = 15.92 kHz` ✓; TI's
`1/(2π·1M·39n) = 4.08 Hz` ✓; `5 nA × 1 MΩ = 5 mV = 1000 ppm of 5 V` ✓;
`5 nA × 10 kΩ = 50 µV` ✓; ratio `100:1` preserved (`1M/10k` = `10k/100`) ✓.

### G8-3 — `diode-split-rationale`: `r_d 69 mΩ at 392 mA` contradicts its own derivation **and** the banked datasheet

**This is the sharpest finding in the entry set.** The `value` field
`[repo] config/figures.yaml:621` reads:

> `"fault isolation and HF isolation (r_d 69 mohm at 392 mA)"`

The `derivation` field two lines down `[repo] :623` reads:

> `"Vf modulation is 120 mV: 0.24 V at 245 mA -> 0.36 V at 612 mA, digitised
> off Fig. 2 of Diodes Inc DS23001 Rev.8"`

Those two statements are about the same diode at the same operating point and
they cannot both be true.

`[calc]` The derivation's own two points give a chord slope of
`(0.360 − 0.240) V / (0.612 − 0.245) A = 0.120/0.367 = 327 mΩ`. For a diode
`dV/dI` falls monotonically with current, so the slope anywhere inside
[245, 612] mA — and 392 mA is inside it — is **bounded below by the chord's
value at the upper end and above by its value at the lower end**; it cannot be
a fifth of the chord.

`[datasheet]` Independently, from the banked document itself —
`datasheets/discrete-and-power/1N5817.pdf`, DS23001 Rev. 8, p.1, read with
`pymupdf`, verbatim: `Forward Voltage (Note 2) @ IF = 1.0A / @ IF = 3.0A |
VFM | 0.450 | 0.750 | V`. `[calc]` The guaranteed-max chord from 1 A to 3 A is
`(0.750 − 0.450)/2.0 = 150 mΩ`. Since `r_d` decreases with current, `r_d` at
**392 mA must exceed 150 mΩ**. 69 mΩ is impossible for this part.

Where 69 mΩ comes from is recoverable: `[calc]` `nV_T/I` at 392 mA with
`n ≈ 1.05` is `1.05 × 0.0257 / 0.392 = 68.8 mΩ`. It is the textbook
ideal-diode small-signal resistance with the bulk series resistance dropped —
and the bulk resistance is precisely what the 120 mV curve read says dominates
here.

**Why it survived.** The entry's `provenance_note` records that the Vf
modulation was corrected on 2026-09-21 from a 75–80 mV review estimate to the
120 mV read off the curve. The `r_d` in the `value` field is the residue: the
fix reached the number being edited and not the number one field above it.
That is finding shape #2 from CLAUDE.md's standing list — *a fix whose own
explanation restates the wrong value* — inside the register.

It is restated once in the corpus, in the owner page
`[repo] hardware/module/power-entry/power-entry.md:116`: "HF isolation (`r_d`
is 69 mΩ at 392 mA)".

**The conclusion is not at risk, and that matters for how this gets fixed.**
Higher `r_d` means *more* HF isolation, so "keep both diodes" is strengthened.
Nobody should be tempted to keep the number because the argument needs it.

### G8-4 — `umbilical-current`: the `value` is 359 mA and its own `derivation` computes 358.1 mA

`[repo] config/figures.yaml:614-616`:

```
value: "359 mA"
derivation: "226 mA x 5 V / (0.9 x 11.4 V) + 248 mA = 358.1 mA.
             This is the only derived figure; eight others are asserted."
```

`[calc]` `226 × 5 / (0.9 × 11.4) = 1130/10.26 = 110.14`; `+ 248 = 358.14 mA`.
The derivation's own stated result, 358.1, rounds to **358**, not 359. A
reader who follows the working gets a different number from the one the
register publishes.

The owner agrees with the `value`, not the derivation:
`[repo] docs/decisions/0005-power-architecture.md:159` gives
`| Typical play | 226 mA | 248 mA | **359 mA** |` and `:96` repeats 359.

`[calc]` Back-solving the ADR's table for the efficiency it actually used, at
the stated 11.4 V arriving: row 2 needs `1130/(111 × 11.4) = 0.893`; the
quiescent row needs 0.887; the WiFi row 0.888; clamp-legal 0.885; the
latched-white row 0.899. So the table was built at roughly **88.5–89 %**, not
the "~90 %" the ADR states at `:167` and the register's derivation copies.
The published figure 359 mA is defensible; the *derivation recorded for it* is
not the one that produced it.

Magnitude is 0.3 % and nothing downstream breaks. It is filed because this
entry advertises itself as "the only derived figure" — it is the one place in
the register where the arithmetic is the whole claim.

### G8-11 — `loadswitch-fb-divider`: right answer, working that does not reproduce

`[repo] config/figures.yaml:513`: *"the nominal target is 10.5 V, giving
R-FB-HI/R-FB-LO = 1.313/10.5 inverted = 7.00"*.

`[calc]` `10.5/1.313 = 7.997`, not 7.00. The ratio 7.00 is
`(10.5/1.313) − 1 = 6.997`, because the divider sets
`V_OUT = V_FBH × (1 + R_HI/R_LO)`, so the **"−1" is missing from the written
form**. Every downstream number in the entry is computed correctly with the
−1 (I reproduced 6.986, 10.486, 3.993 above), so the figure is right and only
the sentence is wrong. But a reader redoing the sizing from the sentence as
written lands on 7.997 and picks 40.8 k/5.11 k.

### G8-12 — `loadswitch-timer`: "the worst case is 95.6 ms" mixes a bound with a typical

`[datasheet]` `datasheets/discrete-and-power/LT1641.pdf`, 164112fc p.2, read
verbatim: `ITIMERUP ... –24 | –80 | –132 µA` and
`ITIMERON ... 1.5 | 3 | 5 µA`. The register `[repo] :488` uses the pull-up's
three bounds but subtracts the **typical** 3 µA pull-down from each.

`[calc]` The genuine fast-end worst case pairs max pull-up with min pull-down:
`132 − 1.5 = 130.5 µA` → `10µ × 1.233 / 130.5µ = 94.5 ms`, and the margin
against the 47.5 ms hot-plug start is `1.99×`, not the stated `2.01×`. Slow
end: `24 − 5 = 19 µA` → `648.9 ms`, not 587.

Immaterial to the 10 µF choice (the conclusion is a 2× margin either way), but
the entry presents 95.6 ms as a guaranteed bound and it is not one.

### G8-13 — `riso-ref-topology`: two small provenance gaps

`[repo] config/figures.yaml` derivation: *"37.4 ohm is Zo/10 against the
specified Zo = 375 ohm"*. `[calc]` `375/10 = 37.5`. 37.4 Ω is the E96 value
and is also exactly what TI prints, so the number is right — but "is Zo/10"
is stated as an identity when it is a rounding, and this register has been
bitten before by a derived number that did not move with its parent.

Second: `[datasheet]` SBOS737C p.30, section 8.2.3, final sentence, verbatim:
*"Any other load capacitances require recalculation of the stability
components: RF, RFx, CF, and RISO."* The register's derivation argues at
length that the topology transfers to a 100 nF load because R_ISO depends on
Zo and not on C_L. That argument may well be right — and the `adaptation`
field does recalculate three of the four — but **the datasheet's explicit
instruction to the contrary is not recorded anywhere in the entry**, and this
is a figure whose whole authority is "TI publishes a worked answer for this
exact circuit". A reader who opens p.30 finds a caveat the register does not
mention.

### G8-22 — Verified against banked documents and found **correct**

A number read off a banked document beats one from a review, so these are
worth recording as positives, not silence. All read with `pymupdf` from the
pinned clone `[datasheet]`:

- **MPXV4006DP** `datasheets/analog/MPXV4006DP.pdf` p.5, verbatim:
  `Vout = VS*[(0.1533*P) + 0.053]`. p.3: `VFSS — 4.6 — V`;
  `Voff 0.152 | 0.265 | 0.378 V`; `Sensitivity V/P — 766 — mV/kPa`;
  `VS 4.75 | 5.0 | 5.25`. Every claim in `sensor-full-scale` and
  `breath-sensor-slope` confirmed, including the 0.053-not-0.04 correction
  and the 0.265 pedestal.
- **74HC165 (onsemi)** `datasheets/logic/74HC165-onsemi.pdf` p.4, verbatim:
  `VIH ... 2.0 | 3.0 | 4.5 | 6.0 → 1.5 | 2.1 | 3.15 | 4.2` and
  `VIL ... → 0.5 | 0.9 | 1.35 | 1.80`. The 3.0 V row **is** 0.70/0.30, the
  2.0 V row **is** 0.75/0.25, and `[calc]` interpolating 2.1@3.0 V to
  3.15@4.5 V gives exactly `2.1 + 0.3×0.70 = 2.31 V` at 3.3 V. Both
  `threshold_note`s confirmed; the register's reading of this table is exact.
- **OPA2197** `datasheets/analog/OPA2197.pdf` (SBOS737C, Jan 2016 rev Mar
  2018) p.8 and p.10 verbatim: `ZO Open-loop output impedance | f = 1 MHz,
  IO = 0 A, See Figure 26 | 375 | Ω` — `opa2197-output-impedance` confirmed.
  p.7: `PSRR ... ±1 | ±3 µV/V` → `[calc]` `20·log10(1/3e-6) = 110.46 dB`, the
  110.5 dB worst case confirmed; `IB ±5 pA typ, ±20 pA max`; p.1 "High
  Capacitive Load Drive Capability: 1 nF" → `[calc]` 10 µF/1 nF = 10000×,
  `cref-out-node`'s figure confirmed. p.30 Figure 56 confirmed verbatim:
  `RF 1 MΩ, CL 10 µF, RISO 37.4 Ω, RFx 10 kΩ, CF 39 nF`, "loop gain phase
  margin of 89°", section 8.2.3, page 30 — every element of
  `riso-ref-topology`'s citation is exactly right.
- **REF5050** `datasheets/analog/REF5050.pdf` (SBOS410O, rev Oct 2025) p.3,
  Table 4-2 verbatim: `REF50xxI | High | 3ppm/ºC | ±0.05%` and
  `REF50xxAI | Standard | 8ppm/ºC | ±0.1%`. `ref5050-grade`'s central claim —
  the 'A' suffix is the *worse* grade — confirmed, table number and page
  number both right.
- **LT1641** `datasheets/discrete-and-power/LT1641.pdf` p.2 verbatim:
  `IGATEUP –5 | –10 | –20 µA`, `ITIMERUP –24 | –80 | –132 µA`,
  `ITIMERON 1.5 | 3 | 5 µA`, `VONH 1.280 | 1.313 | 1.345`,
  `VONL 1.221 | 1.233 | 1.245`, `VONHYST 80 mV`,
  `VSENSETRIP: VFB = 0V → 8|12|17 mV; VFB = 1V → 39|47|55 mV`. p.5 verbatim:
  *"will regulate the voltage across the sense resistor (VCC – VSENSE) to
  47mV when VFB is 0.5V or higher. If VFB drops below 0.5V, the voltage
  across the sense resistor decreases linearly and stops at 12mV when VFB is
  0V."* All three `loadswitch-*` entries' datasheet citations confirmed.
- **1N5817** `datasheets/discrete-and-power/1N5817.pdf` p.1 verbatim:
  `VFM @ 1.0A = 0.450, @ 3.0A = 0.750 V`; Fig. 2 "Typical Forward
  Characteristics" present on p.2. The register's calibration claim (its
  extraction returns 0.454/0.746 against these) is consistent — which is what
  makes **G8-3** a contradiction rather than a difference of opinion.

`verify-datasheets.py` passes inside `check-staleness.py`'s run
`[test] [pinned] python3 tools/check-staleness.py → 0 datasheets`.

---

## 4. `forbidden` patterns

### The two named failure modes: neither is present today

**Hard newline in a pattern: zero.** `[test] [pinned]` No pattern contains
`\n`. The `spi-series-r` case the file documents has been split and the
unusable half removed.

**Self-exempting pattern (refutation wording inside the pattern): zero.**
`[test] [pinned]` I ran the checker's own `REFUTATION` regex over all 217
patterns; no match. `check_patterns` agrees — the pinned run reports
`0 dead-patterns`.

**Pattern that fires on a correct sentence: zero live cases.** All 19
currently-matching patterns land inside genuine refutation prose in `.md`
files, and I read every one. Representative:
`[repo] latency-budget.md:183-184` "It totalled the bus time as a superseded
'136 µs' of 250 µs, and called that a superseded '54 % duty'";
`[repo] mod-channels.md:201` "*(This read 'At 2.5 V into 2.5 kΩ that is 1 mA'
until 2026-09-21…)*";
`[repo] breath-receive-stage.md:95` — the `−10.05 V` match sits in an ASCII
drawing, and the correction *is on the same line as the value*
("│ Superseded: this line carried −10.05 V, the"), which is the gutter rule
being followed correctly. One is pleasingly self-referential:
`[repo] docs/reference/repo-maintenance.md:43` quotes the pattern
`0.2 + 0.766` as a worked example and says so in the next clause, so the
documentation about the guard trips the guard and then exempts itself.

So the *quality* of the surviving patterns is good. The problem is the other
81 %.

### G8-5 — 57 of 217 patterns (26 %) have never matched any revision of this repository

`[test] [pinned]` Method, fully reproducible: enumerate every unique blob
reachable from `git rev-list --all` for `.md`/`.csv`/`.yaml`/`.py` paths
outside `docs/{review,log,research}` and excluding `config/figures.yaml`
itself — **592 blobs** — join each to a single-space stream exactly as
`check_figures` does, then ask of each dead pattern whether it appears in
*any* of them.

```
TOTAL=217  LIVE=19  DEAD=198  NEVER_IN_ANY_REVISION=57
```

Identical when run in the live tree and in the pinned clone.

198 dead is not itself a defect — a pattern that fired, got fixed and now
guards against regression is doing its job. **57 that never fired in 153
commits is different.** Those patterns did not come from grepping the corpus
for the old value, which is the procedure CLAUDE.md §2 step 2 exists to
mandate; they came from imagining how the old value might have been spelled.
A pattern written that way is indistinguishable in every report from a pattern
that works, and it inflates the "217 patterns" headline on every run into a
number that overstates coverage by a quarter.

Caveat, stated because it bounds the claim: if any spelling lived only in a
file type I excluded, or in history that has been squashed away, a
"never matched" verdict would be wrong for that pattern. The repository has
153 commits and no evidence of a squash `[repo] git rev-list --all --count`,
and the corpus is entirely `.md`/`.csv`/`.yaml`, so I think the bound holds —
but it is an inference, not a proof.

Full breakdown by figure:

| figure | patterns | live | dead | **never** |
|---|---:|---:|---:|---:|
| `sensor-full-scale` | 34 | 2 | 32 | **12** |
| `key-release-time` | 12 | 0 | 12 | **4** |
| `panel-width` | 7 | 0 | 7 | **4** |
| `ks33-contact-bounce` | 5 | 0 | 5 | **4** |
| `key-press-time` | 12 | 0 | 12 | **3** |
| `breath-sensor-slope` | 3 | 0 | 3 | **3** |
| `key-scan-current` | 3 | 0 | 3 | **3** |
| `loadswitch-timer` | 7 | 0 | 7 | **3** |
| `panel-toggle-hole` | 3 | 0 | 3 | **3** |
| `inamp-full-scale` | 9 | 1 | 8 | 2 |
| `chain-conductors` | 7 | 0 | 7 | 2 |
| `umbilical-pinmap` | 6 | 0 | 6 | 2 |
| `cref-out-node` | 6 | 0 | 6 | 2 |
| `riso-ref-topology` | 9 | 0 | 9 | 2 |
| `loop-budget` | 7 | 2 | 5 | 2 |
| `chain-connectors`, `diode-split-rationale`, `marker-bits`, `mod-reference`, `pitch-compensation`, `spi-series-r` | | | | 1 each |
| `breath-zero-ref`, `dac-rail`, `panel-height-budget`, `free-bits`, `key-pullup-qty`, `loadswitch-gate-cap`, `loadswitch-fb-divider`, `umbilical-current`, `plate-thickness`, `opa2197-output-impedance`, `ferrite-bias-impedance`, `ref5050-grade` | | | | **0** |
| **TOTAL** | **217** | **19** | **198** | **57** |

The clean-zero column is the interesting one: twelve entries have forbidden
lists in which *every* pattern is evidenced. Those are what the procedure
produces when it is followed.

### G8-6 — `sensor-full-scale`: 12 of 34 patterns never matched — in the entry that teaches grep-first

`[test] [pinned]` Never matched any revision:

```
'4.7 V output'        '0.2-4.7 V'         '0.2 V + 0.766'      '0.200 V at rest'
'0.2 V at rest'       '(0.1533*P) + 0.04' '0.1533 x P) + 0.04' 'rest | 0.200 V'
'0.2-4.80 V'          '0.2 to 4.8 V out'  'typical +0.200 V'   '0.2 to 4.7 V'
```

This entry carries three `escape_note`s and 55 lines of prose whose thesis is
`[repo] config/figures.yaml:112-114`: *"when a figure moves, grep the corpus
for the OLD value first and add a pattern per spelling found, rather than
writing the forbidden list from the document in front of you."* Twelve of its
thirty-four patterns are the second thing. The entry names nine real
spellings; the list holds thirty-four.

Two of the twelve are worth separating because they are *almost* right and
show the mechanism precisely. `'0.2-4.80 V'` never matched, while the tight
en-dash `'0.2–4.80 V'` matches today at `[repo] 0003:118` — the ASCII sibling
was added on the assumption that both existed and only one ever did. Same for
`'0.2 to 4.8 V out'`: the corpus's real sentence is
`[repo] 0003:102` *"the cover page's "0.2 to 4.8 V" contradicts"*, which the
`out` suffix misses by three characters.

And that near-miss is load-bearing in the opposite direction: **if the suffix
were dropped, the pattern would fire on a correct sentence**, because `0003:102`
is a true statement *about* the cover page and the word "contradicts" is not
in the checker's `REFUTATION` vocabulary `[repo] tools/check-staleness.py:93-104`.
So the coverage gap here should be left open, and it should say so in a
`false_positive_note`. It does not.

### G8-7 — `ks33-contact-bounce`: four of five patterns are paraphrases of sentences that never existed

`[test] [pinned]` Never matched any revision:
`'does not publish contact bounce'`, `'bounce is not published'`,
`'no published bounce figure'`, `'bounce, which Gateron does not'`.

The entry's `note` asserts `[repo] config/figures.yaml`: *"Three documents
asserted that Gateron does not publish this — ks33-geometry.md, ADR 0002 and
latency-budget.md."* `[test] [pinned]` I searched every historical blob for
sentences containing "bounce" near a not-published phrase. Seven distinct
sentences exist across all of history; the ones that carried the wrong claim
are:

- `[repo] 0002` — *"**Contact bounce and the actuation/reset hysteresis gap**,
  which Gateron does not publish"*
- `[repo] latency-budget.md` — *"this row used to frame it as unpublished"*,
  *"measure bounce duration on press *and* release"*
- `[repo] repo-maintenance.md` — *"recorded contact bounce as unpublished
  through four review waves"*

The pattern `'bounce, which Gateron does not'` misses the real ADR 0002
sentence by the six words `and the actuation/reset hysteresis gap` sitting
between them. Only the fifth pattern,
`'bounce duration and the reset point'`, ever matched anything.

This entry was written on 2026-09-21 — after every escape note in this file
had been written. The guard was built from a recollection of what the three
pages said rather than from the text, and the one clause that separated the
true half of the sentence (the hysteresis gap genuinely *is* unpublished) from
the false half is exactly the clause the pattern dropped. The entry's own
`false_positive_note` records that a bare `"Gateron does not publish"` had to
be withdrawn within twenty minutes for firing on that same true half — so the
sentence was in front of whoever wrote this, and the pattern still does not
match it.

### G8-19 — `spi-series-r` guards two retired refdes bare and the third only in one phrasing

`[repo] config/figures.yaml:329` — the list holds `R-SCLK-SER` and `R-CS-SER`
as bare strings, but `R-MOSI-SER` only as `"R-MOSI-SER at 220"` and
`` "R-MOSI-SER` at 220" ``. `[test] [pinned]` The bare two fire today at
`[repo] hardware/interfaces/spi-link/spi-link.md:59` and
`docs/decisions/0004-cv-interface-module.md:558`, both correctly exempted as
refutation records. `'R-MOSI-SER at 220'` never matched anything.

So of three refdes that were retired together, two are guarded against any
recurrence and one is guarded only if it comes back with "at 220" attached.
All three are still named in a schematic page's prose
`[repo] .staleness/report.txt:58-78, "drawn in a schematic, no BOM row"`.
Asymmetric coverage of one retirement event — small, but it is the exact
shape the file's other escape notes describe.

### Spelling coverage: where a superseded value could still hide

`[test] [pinned]` I extracted every retired numeral from every `forbidden`
list and grepped the corpus for it unglued, in all spellings, then read each
hit. Almost everything is either correctly covered or a legitimate different
quantity (the register's `false_positive_note`s are doing real work here —
the 2.185 raw gain, the negative −4.7 V, the 4.80 V LM317 rail, the 125 mV
rail-to-rail swing, the 0.75 mm plate overshoot all appear and are all fine).

Two uncovered spellings are worth naming, and **neither should be closed with
a pattern**:

- `[repo] docs/decisions/0003-breath-sensing-path.md:102` — `0.2 to 4.8 V`
  quoted as the cover-page line that "contradicts" the transfer function. No
  pattern covers this spelling; adding one would fire on a correct sentence
  that the `REFUTATION` vocabulary does not recognise (see G8-6).
- `[repo] hardware/cluster/key-switch-network/key-switch-network.md:89` —
  `2.475 / 0.825 V` as the stated TI-only conservative bound. Both
  `key-release-time` patterns spell it `0.75 x VCC = 2.475`; the corpus's live
  spelling is uncovered, and correctly so, because the bound is deliberate
  `[repo] config/figures.yaml:223 conservative_bound`.

**Three settled entries have one or two patterns and no more:**
`key-pullup-qty` (1), `ferrite-bias-impedance` (1),
`opa2197-output-impedance` (2). `ferrite-bias-impedance`'s single pattern is
a 95-character sentence — precise, but a single sentence-length literal is
the most fragile possible guard for a figure whose whole point is that a BOM
row stated a rule the datasheet refutes.

---

## 5. The unresolved entries

Five: `breath-working-point`, `pitch-cents-budget`, `dig-gnd-topology`
(disputed), `matrix-led-current` (blocked), `ref5050-grade` (disputed).
**All five disputes are real and still open** — I found nothing filed as
disputed that the corpus has since settled, which is the dangerous direction
and it is clean. `decided_by` is where the problems are.

**`ref5050-grade` — healthy.** `[datasheet]` The facts are settled (Table 4-2
verified above) and what remains is genuinely a part choice: the BOM still
orders `REF5050AIDR` in three places `[repo] hardware/bom.csv:11`,
`hardware/carrier/breath-excitation-reference/bom.csv:2`,
`breath-excitation-reference.md:99`, while ADR 0003 has been corrected and now
states the table correctly `[repo] 0003:484-488`. `decided_by` names a
concrete action ("changing one letter in the order code") and its consequence.
The `caught_late_note`'s complaint — that 0003 went on asserting 0.05 %/3 ppm
— is **resolved**; the register has not been updated to say so, which is a
one-line staleness of its own but a benign one.

**`matrix-led-current` — healthy.** `blocked_on` names a real
`datasheets/MANIFEST.csv` row `[repo] MANIFEST.csv:101` — `WS2812B-0807`,
empty `file` and `sha256`, the three attempted URLs recorded. `decided_by`
names "A BENCH MEASUREMENT AT E1", and E1 exists
`[repo] ROADMAP.md:41`, with a row at `:189` explicitly booking the real-time
board idle current to it. This is the model for how a blocked entry should
read.

**G8-8 — `breath-working-point`'s `decided_by` names the wrong milestone.**

`[repo] config/figures.yaml:471`: *"M1, with a player and a manometer."*

`[repo] ROADMAP.md:71` — `| M1 | Switch characterisation | **Cutout is
14.0 × 14.0 mm**, measured from a working KS-33 build …`. M1 is about key
switches. `[test] [pinned]` The words "manometer" and "kPa" appear nowhere in
`ROADMAP.md`.

The gate that would actually produce this number exists and has a different
id: `[repo] ROADMAP.md:42` — `| E2 | Breath sensing | … Then **a human plays
it for 20 minutes** through a real mouthpiece, tube and trap …`. That is the
measurement `decided_by` describes, under **E2**, not M1.

So the decider is real as a *kind* of evidence and misfiled as a *schedule
item*: nothing in the roadmap's M-series will ever generate the figure, and
the E-series row that will does not know it is on the hook for it.

**G8-9 — the disputed 2.8 kPa is live in two circuits, and its cited source
has withdrawn it.**

`candidates` describes the state as *"2.8 kPa (cited to ADR 0003, which does
not contain it; the two schematic pages cite each other)"*. `[test] [pinned]`
ADR 0003 still does not contain it — confirmed. But the rest has moved:

| where | what it says now |
|---|---|
| `[repo] breath-receive-stage.md:200` | *"this page **used to say**: real playing tops out around 2.8 kPa"* — **withdrawn** |
| `[repo] breath-output-stage.md:41` | `| Hard blow, real playing (~2.8 kPa) | 2.411 V | **−4.64 V** |` — **live** |
| `[repo] breath-output-stage.md:44` | *"**Real playing only reaches about 2.8 kPa**"* — **live** |
| `[repo] breath-adc.md:40` | `real play = 2.8 kPa → 0.265 + 0.766 × 2.8 = 2.41 V → 1.447 V → 1795 counts` — **live, and an arithmetic chain** |
| `[repo] breath-adc.md:41` | `[2.8 kPa from breath-receive-stage.md]` — **cites the page that withdrew it** |

It is no longer "two schematic pages citing each other". One page has
retracted and two others still depend on it, one of them by name, and one of
them computing a 1795-count ADC target from it.

**And nothing can catch this**, because every `disputed`/`blocked` entry has
`forbidden: []` `[test] [pinned] 5 of 5`. The checker's `thin_patterns`
advisory deliberately exempts non-settled entries
`[repo] tools/check-staleness.py:337`. That is defensible for the *disputed
value* — you cannot forbid a number you have not replaced — but a dispute is
precisely the state in which one candidate silently hardens into fact across
the corpus, which is what has happened here. The register has no mechanism for
"this number is not decided, so stop restating it as though it were".

**G8-10 — `pitch-cents-budget`'s `decided_by` restates a problem, and describes
a page that has changed.**

`[repo] config/figures.yaml:480`: *"pitch-stage.md has two contradictory budget
tables back to back and states no total. One coherent table, then cite it."*

This is the one `decided_by` in the register that names no evidence source,
no measurement and no milestone — it names the symptom and an instruction.
Compare `matrix-led-current`'s "a bench measurement at E1" or
`ref5050-grade`'s "changing one letter in the order code".

And the page description is now stale. `[repo] hardware/module/pitch-stage/pitch-stage.md`
has one live budget table at `:284-288` and a marked-superseded one — `:296`
reads *"(The superseded version of this table, which contradicted the live one
twelve…"*. So "two contradictory tables back to back" has been half-fixed
while the register still describes the pre-fix state. The genuinely open part
— **the page states no total** — is still true, and is the only part of
`decided_by` that a reader can act on.

The `candidates` list is also incomplete. It holds 0.42 / 0.85 / 1.35 / ~1.2
cents. `[test] [pinned]` The corpus additionally carries **three values for
the single largest sub-term**, the DAC internal reference:

- `0.42 cents` — `[repo] pitch-stage.md:286`, `power-entry.md:134`
- `0.54 cents` — `[repo] pitch-stage.md:121`, `0006:395`
- `~0.5 cents` — `[repo] hardware/module/pitch-stage/notes.md:62`

and `notes.md:54` says outright *"reference is **0.42 cents**, not `~0.5`.
Neither figure is tracked in…"*. A dispute about a total whose largest row is
itself three-valued, with the divergence recorded in a `notes.md` and not in
the register, is a dispute that cannot be closed from the register as it
stands.

**`dig-gnd-topology` — acceptable, with one observation.** `decided_by` names
"the 2-layer vs 4-layer decision, which is upstream of it", and that decision
is genuinely open `[repo] docs/reference/pcb-pipeline.md:116` —
*"2-layers-or-4"*. So this is the only entry decided by another undecided
question rather than by evidence. That is honest and I would not change it,
but it means the entry cannot be closed by anyone working on grounding; it is
blocked on a stack-up call, and saying so in `blocked_on` rather than
`decided_by` would make the dependency visible to the tool.

---

## 6. What is missing

**G8-14 — load-bearing quantities in three or more corpus files with no
register entry.** The checker's own advisory lists 211 candidates
`[repo] .staleness/report.txt:13`, most of which are package dimensions and
rail names. These are the ones I judge genuinely load-bearing, each verified
`[test] [pinned]`:

| quantity | files | why it is the next defect |
|---|---:|---|
| **2.500 V** — pitch-stage `V_ref` | 8 | Its digits collide with `mod-reference`'s refuted 2.5 V. The register already says this collision makes a forbidden pattern impossible `[repo] config/figures.yaml:363`. An untracked figure whose spelling is unguardable is the worst combination available. |
| **0.265 V** — sensor pedestal | 6 | The single most-moved number in this corpus. It moved 0.200 → 0.265 and "followed it in two files, half-followed in a third and did not move in two more" `[repo] config/figures.yaml:176-177`. It is asserted in `sensor-full-scale`'s *derivation* and is the `value` of nothing, so `check_restated` counts it as untracked — correctly. |
| **0.378 V** — `V_off` max | 5 | Sets the trimmer range 0.332–0.826 V `[repo] breath-receive-stage.md:124-126`, which is itself untracked (3 files). Derived from a datasheet bound, restated not cited. |
| **392 mA** vs **404 mA** — module +12 V total | 3 / 1 | See **G8-15**. |
| **11.4 V** — arriving umbilical voltage | 5 | The conversion basis for `umbilical-current`. Move it and 359 mA moves; nothing connects them. |
| **47.5 ms** — hot-plug start | 4 | The sizing case for `loadswitch-timer` and the denominator of its 2.01× margin. Stated in the register's `derivation` as given fact, owned by nothing. |
| **480 / 482 Hz** — breath channel corner | 6 / 6 | See **G8-16**. |

Three more deserve mention below the 3-file threshold because **the register
itself names them as owed**: `0.077 %`, `3.2 LSB` and `~1594 counts`, the
consequences of `key-scan-current`, each in two files, with the entry's own
`escape_note` saying deduplication "is still owed"
`[repo] config/figures.yaml:212-214`. Two files is under the advisory's noise
floor, so the tool will never raise them; the register has known about them
since 2026-09-21.

**G8-15 — 392 mA and 404 mA are both the module's +12 V total.**

`[test] [pinned]` `392 mA` appears in three corpus files —
`[repo] hardware/module/power-entry/power-entry.md:116`,
`hardware/module/power-entry/bom.csv:8`, `hardware/bom.csv:61` — and **twice
inside the register**: in `diode-split-rationale`'s `value` ("r_d 69 mohm at
392 mA") and in `ferrite-bias-impedance`'s `derivation` ("the module +12V
total of 392 mA gives ~245-275").

`[repo] docs/decisions/0004-cv-interface-module.md:276` states the same
quantity as **~404 mA**: `| +12 V | **~404 mA typical** (45 mA module incl.
the DAC regulator + **359 mA** instrument, derived in ADR 0005) |`.
`[calc]` `45 + 359 = 404` — that row is internally consistent and cites
`umbilical-current` correctly.

So two numbers, 3 % apart, for one quantity, with the register endorsing the
one the ADR does not use. `ferrite-bias-impedance`'s FB2 impedance
interpolation is computed from 392; `[calc]` at 404 mA the interpolation moves
by roughly 10 Ω on a ~280–310 Ω figure — immaterial to the conclusion, which
is why nobody has noticed. `umbilical-current`'s `false_positive_note` warns
"392 mA is the MODULE total … Do not conflate" — so the register is aware of
the quantity, names it, restates its value, and does not track it.

**G8-16 — 480 Hz and 482 Hz are arithmetically the same corner.**

`[calc]` The output reconstruction RC: `1/(2π × 1 kΩ × 330 nF) = 482.3 Hz`.
The input differential filter: `1/(2π × 22 kΩ × 15 nF) = 482.3 Hz`. Two
different circuits landing on the same number by coincidence.

`[test] [pinned]` The corpus writes the input one as **482** and the output one
as **~480**, across 8 files: `[repo] breath-sense-link.md:150` (482) and `:154`
(~480); `latency-budget.md:42` (482) and `:43` (480);
`breath-output-stage.md:154` (~482!) against its own BOM fragment
`breath-output-stage/bom.csv:2` (~480); `0006:777` (~480) and `:780` (482).
`breath-output-stage.md` and its own BOM row disagree with each other about
the same capacitor.

Neither is tracked. Two near-identical untracked numbers used interchangeably
across eight files, one of which is spelled two ways inside a single circuit
directory, is a defect waiting for the day somebody changes `C-OUT-BREATH`.

---

## 7. Process

**G8-20 — the corpus and `tools/` were being edited while eleven read-only
slices were reading them.**

I observed this directly before being told about it. `[test]` At one point
mid-slice the `PreToolUse` hook flipped from `PASS` to
`FAIL … 1 stale`, and `git status --short` showed
`M hardware/module/pitch-stage/circuit.yaml` with this appended:

```
+# G10: this row previously said -9.6 V, which is superseded and no longer correct.
```

`[repo] git diff hardware/module/pitch-stage/circuit.yaml`, timestamp
`2026-09-22 14:40:16`. It later reverted and the hook returned to `PASS`.

Three things follow that are worth recording for the wave:

1. **The probe confirms rule 2b works as designed.** The line carries
   "previously", "superseded" and "no longer" — three refutation markers — and
   the checker failed it anyway, because `prose = rel.endswith(".md")` and
   `circuit.yaml` is not prose `[repo] tools/check-staleness.py:~300`. That is
   the prose-only exemption doing exactly what CLAUDE.md §2b says it should.
2. **It is also the first time `'-9.6 V'` has ever matched anything.** That
   pattern is in my never-matched-in-any-revision list (G8-5); the only thing
   that has ever fired it is another agent injecting it. An injection test
   that draws its probe values from `forbidden:` lists will therefore mark
   dead patterns live, which is why I re-ran everything pinned.
3. **My own scratchpad is shared.** My first pinned clone was **deleted while
   I was using it** `[test] ls: cannot access …/pin: No such file or
   directory`, and the shared directory contains other slices' `inject.sh`,
   `inject2.sh`, `inj3.sh`, `g10/` and `frozen/`. I re-cloned to a
   uniquely-named path and re-ran the full sweep there; every number
   reproduced.

CLAUDE.md's wave rule says *"Name the revision a wave measures against, and
pin `tools/` or say you are not."* The commit-level freeze held. The
**uncommitted layer** is not covered by that sentence at all, and it is the
layer every tool actually reads. One line — *reviewers work from a clone,
injectors work in the tree* — would have cost nothing.

**G8-21 — `check_restated` builds its exclusion set from `value` + `forbidden`
only, so it misreports in both directions.**

`[repo] tools/check-staleness.py:857-861`. A number that appears only in a
`derivation` is treated as untracked (this is why **0.265 V** shows up in the
advisory — arguably correct, see G8-14). Conversely, **any** number appearing
anywhere in **any** figure's forbidden list is excluded corpus-wide, even for
an unrelated quantity: `2.475` is excluded because `key-release-time` retired
it, `0.04` because `sensor-full-scale` retired it, `10.05` because
`inamp-full-scale` retired it — so a genuine restatement of an unrelated
quantity sharing those digits is invisible to the advisory. The exclusion is
global where the patterns are per-figure.

---

## What I could not check

Stated plainly, because a silent gap reads as a clean result.

- **I did not re-digitise the 1N5817 Fig. 2 curve.** G8-3 proves 69 mΩ and
  120 mV are mutually inconsistent, and proves 69 mΩ is impossible against the
  datasheet's *tabulated* maxima. It does **not** establish that 120 mV is the
  right number — only that it and 69 mΩ cannot both stand. Somebody should
  re-read the plot before choosing which to keep.
- **I did not verify the vector-only documents by render.** `plate-thickness`
  (1.20 ±0.05 mm off Gateron sheet 6/sheet 3), `panel-toggle-hole` (NKK
  M6×0.75 → 6.5 mm), `ferrite-bias-impedance` (the Laird bias-curve family),
  and `matrix-led-current`'s B5819WS thermal numbers all rest on 150 dpi
  renders read by hand in earlier work. I confirmed the *files are banked and
  hash-verified* `[test] verify-datasheets.py passes` but did not re-read the
  pixels. These are the four figures in the register with the weakest
  independent confirmation from this slice.
- **`riso-ref-topology`'s simulation results** (85.9° at 896 kHz, the 76°
  robustness floor, the 200× C_L sweep) are model outputs I did not reproduce.
  I verified the TI figure they are compared against, and that comparison is
  exact.
- **`chain-connectors`, `marker-bits`, `free-bits`, `chain-conductors`** — I
  verified the owner states each value, but not that the *counts are right*
  (that 8 connectors is the correct answer for the real board set, etc.).
  That is a topology question, not a register question.
- **The 211-entry restated advisory** — I read the top 42 and judged 7 as
  load-bearing. The remaining 169 are unexamined; there may be more missing
  figures in the tail.
- **`docs/review/`, `docs/log/`, `docs/research/`** — not read, by the cold
  rule, including this wave's own `README.md`. If the wave README pins a
  revision or a method that contradicts what I did above, I would not know.

## What a fix pass should do first

In order, by ratio of risk removed to effort:

1. **G8-1** — delete one of the two `false_positive_note` keys (merge the
   text). One-line edit; until it is done, the loaded register is not the
   file on disk.
2. **G8-3** — decide between 69 mΩ and the 120 mV curve, and fix both the
   `value` field and `power-entry.md:116` in the same commit.
3. **G8-2** — either move `key-pullup-qty`'s owner to
   `key-marker-and-bits.md`, which states it, or make
   `key-switch-network.md` state it. Then check the other seven
   `UNCHECKED` owners have not drifted the same way — I found them clean
   today, but nothing will tell you when they stop being.
4. **G8-5/G8-6/G8-7** — prune. 57 patterns that have never matched anything
   are not insurance, they are noise that makes the coverage count a lie. A
   `--never-fired` mode on `check_patterns`, using the history scan above,
   would make this self-maintaining.
5. **G8-9** — the 2.8 kPa chain is the only finding here where a *wrong
   number is being computed with today*: `breath-adc.md:40` derives a
   1795-count ADC target from a disputed figure whose cited source has
   withdrawn it.
