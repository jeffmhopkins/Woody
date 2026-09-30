# R1 — The register and the key timing

**Slice:** R1, cold. Read only `CLAUDE.md` and this wave's `README.md` under
`docs/review/`.
**Revision measured:** `eebcdfb`. HEAD was `36341bf`, which differs from it only
by the wave README `[run: git diff eebcdfb HEAD --stat]`.
**Tools:** run unmodified, never edited. Break tests were done on a
`git archive` copy under the scratchpad (`…/scratchpad/R1/repo`).
**Datasheet text:** `pdftotext -layout` of the banked PDFs. Page numbers are
the PDF's printed page numbers.

## Summary

The part change itself is sound. `U-KEYS` is TI's SN74HCS165DR on the sheet,
in both exported netlists, in the LH fab BOM, and at LCSC. The pin map matches
TI's Table 5-1. Both key-timing figures re-derive to the stated digits. The
threshold direction is right, and TI states it in its own words. None of the
forbidden patterns match correct live text.

What did not follow the part change are the arguments built on the part's
extremes. Three of them take the extreme from the wrong side:

- **The glitch filter:** it needs VT+ **min**, not max.
- **The lumped-load argument:** it needs the **fastest** output edge, not the
  maximum transition time.
- **The hold argument:** it needs the **minimum** tpd.

The new, lower VT− bound also quietly closes most of an open `R-KEY-SER` trade.

---

## Findings

### R1-1 [medium] The RC's stated job, "swallows a contact opening shorter than `key-release-time`", is bounded by VT+ min, which guarantees only about 40 µs

**Node:** key input node; `key-release-time` (`role_note`); `C-KEY`.
`hardware/cluster/key-switch-network/key-switch-network.md` §2 ("It swallows a
contact opening shorter than `key-release-time`").

**Evidence.**
- `key-release-time` is taken at VT+ **max**, the slowest possible release
  `[config/figures.yaml key-release-time]`. That is the right bound for the
  latency claim.
- It is the wrong bound for a *rejection* claim. The page says openings shorter
  than 138.7 µs are swallowed. A glitch is swallowed only if the node never
  reaches VT+. The input that reads high **earliest** has VT+ at its
  **minimum**.
- TI's VT+ min ratios `[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.6]`:
  - 0.7/2 = 0.35
  - 1.7/4.5 = 0.378
  - 2.1/6 = 0.35
- Taking the extreme ratio, the same method the figure uses:
  `[calc]` VT+min = 0.35 × 3.3 = 1.155 V, and
  t = 103.4 µs × ln((3.3 − 0.1435)/(3.3 − 1.155)) = 103.4 × 0.3863 = **39.9 µs**.
- Nexperia's 74HCS165 3.0–3.6 V row gives VT+ min = 0.4 × VCC = 1.32 V
  `[datasheets/logic/74HCS165-nexperia.pdf p.6]`. `[calc]` That is
  103.4 × ln(3.1565/1.98) = **48.2 µs**.
- With C-KEY at −10 % (CL21B473**K**BCNNNC on the sheet) and X7R at −15 %:
  `[calc]` 39.9 × 0.99 × 0.90 × 0.85 = **30.3 µs**.

**So:**
- Openings under about 30–40 µs are guaranteed to be swallowed.
- Openings between about 40 µs and 138.7 µs may or may not be read as a
  release, depending on the part.
- The stated capability is about 3.5× what the part guarantees.

No conclusion elsewhere depends on the larger number, because firmware's
release window does the debouncing (`firmware/README.md`). The owner page's
statement of the RC's only role is still wrong by the part's own table.

**Fix:** in the owner page and the `role_note`, state the rejection side
separately. For example: "always swallows an opening shorter than ≈ 40 µs (VT+
min, 0.35 × VCC); an opening longer than `key-release-time` always reads as a
release; in between depends on the part." If a number is wanted in the
register, make it its own figure with its own derivation, not a restatement.

### R1-2 [medium] The "HC-family output edges keep each hop a lumped load" argument is carried by a *maximum* transition time, the HCS165's edges are faster than the part it replaced, and the corpus's own 1/6 rule does not return "lumped" for a hop

**Node:** `U-KEYS` `QH` → next `SER` (the `HOP_*` nets, and `right_thumb`'s
`QH` to the MCU).

**Where it is stated:**
- ADR 0001's amendment ("The family argument above stands … So each hop is
  still a lumped load")
- `key-register.md` §1
- the `U-KEYS` row (`hardware/cluster/key-register/bom.csv`, and so
  `hardware/bom.csv`)
- the `U-KEYS` sheet `Note` ("its edges keep each hop an ordinary lumped load")
- `key-chain-loom.md` (the parenthetical after `R-CHAIN-SER`)
- `spi-link.md` (the SPI3 row)
- ADR 0001 lines 315 and 431 ("HC165's slow edges")

**Evidence.**
- TI gives `tt` for any output as **max only**: 5 ns at 4.5 V and 25 °C, 8 ns
  over temperature, 9/17 ns at 2 V `[SN74HCS165-ti-scls828a.pdf p.8]`.
- A maximum bounds the slow side. The reflection hazard is set by the
  **fastest** edge, and no minimum is published.
- The replaced part is slower. The 74HC165 is 7 ns **typ** and 15 ns max at
  4.5 V and 25 °C `[datasheets/logic/74HC165-nexperia.pdf p.8]`. The
  HCS165's guaranteed maximum is below the HC165's typical. The amendment
  quotes both numbers and concludes that nothing changed. That is the recorded
  shape "a conclusion its own corrected number refutes".
- `key-chain-loom.md` sets the lump criterion as a one-way delay under ⅙ of
  the edge, at about 6 ns/m.
  `[calc]` For a 5 ns edge: 5/6/6 × 1000 = **139 mm**. For the 8 ns
  over-temperature maximum: 222 mm.
- The ribbon alone is **104.37 mm** `[mechanical/drc.echo "key-chain ribbon
  length (derived)"]`. A hop is that ribbon plus the key-board trace to
  `J-CHAIN` plus a main-board run. The main board is 239.5 mm long
  `[drc.echo "main board (derived)"]`.
- So even at the **maximum** edge, the hop exceeds the lump length as soon as
  the board traces add about 35 mm. At a realistic faster edge it exceeds it
  outright.

**Why the chain is still very likely fine, and why that should be the stated
argument:**
- `QH` → `SER` is **data**, sampled at the *next* rising `CLK`, 1 µs later at
  1 MHz.
- `SER` setup is ≤ 14 ns and hold is 0 ns over temperature at every rail
  `[p.7]`. Ringing on `QH` settles in a few round trips of about 1–2 ns each,
  hundreds of nanoseconds before it is sampled.
- The receiving `SER`, `CLK` and `SH/LD` inputs are now Schmitt inputs, with
  ΔVT ≥ 0.2 V at 2 V and ≥ 0.4 V at 4.5 V `[p.6]`, and Nexperia gives ≥ 0.1 × VCC
  at 3.0–3.6 V `[74HCS165-nexperia.pdf p.6]`. That is a real immunity gain the
  corpus does not claim.
- The edge-sensitive nets are `SCK` and `SH/LD`. The MCU drives them, not the
  register, and they are E14's scope item behind `R-CHAIN-SER`.

**Fix:**
- Replace "HC-family edges keep each hop a lumped load" wherever it appears
  with the sampled-data argument above.
- Keep "LVC is the way back / E4, E14 measure it".
- Stop citing `tt` max as evidence of slowness.
- The sheet `Note` and the BOM row carry the same sentence, so fix the
  fragment and the sheet, then re-export and re-merge.

### R1-3 [medium] The lower VT− bound nearly closes the open `R-KEY-SER` trade, and the page does not say so: the ceiling is ≈ 388 Ω and the "≈ 330 Ω" option has 57–65 mV of margin

**Node:** `R-KEY-SER`; the pressed-node divider; `key-press-time`.
`key-switch-network.md` §2 ("A larger `R-KEY-SER` (≈ 330 Ω brings the peak to
the rating) raises the pressed-node voltage and slows the press; that trade is
open").

**Evidence.**
- A pressed key reads low only if the divider voltage sits below VT−, and the
  design now takes VT− min = 0.495 V `[config/figures.yaml key-press-time]`.
- `[calc]` The ceiling is R_ser < 2200 × 0.495/(3.3 − 0.495) = **388 Ω**.
  Contact resistance is at most 200 mΩ and negligible
  `[docs/reference/ks33-geometry.md:218]`.
- `[calc]` At 330 Ω:
  - node = 3.3 × 330/2530 = 0.430 V, which is **65 mV** under the bound
  - with 1 % parts (333.3 Ω, 2178 Ω): 0.438 V, **57 mV**
  - press time = (2200 ∥ 330) × 47 nF × ln((3.3 − 0.430)/(0.495 − 0.430)) =
    13.49 µs × 3.79 = **51 µs**, against 9.87 µs now
- This text is unchanged from `383116e` `[run: git show
  383116e:…/key-switch-network.md | grep 330]`. It was written when V_IL was
  0.99 V and 330 Ω had about 0.56 V of margin.

**Fix:** add to the open trade that under the fitted part's bound,
`R-KEY-SER` must stay below about 390 Ω for a pressed key to read at all. 330 Ω
is at the edge. Anything that raises the rating-driven value, for example a
tighter contact-current reading, runs out of room.

### R1-4 [medium] The retired values have a CSV spelling and a no-`=` spelling that no `forbidden` pattern matches: the pre-change `C-KEY` row, restored verbatim, passes the checker

**Node:** `key-release-time` and `key-press-time` `forbidden`; `C-KEY`; rule 2
("grep the corpus for the OLD value first … one pattern per spelling").

**Evidence.**
- At `383116e` the old values appeared in these spellings `[run: git grep -E
  "119\.9|5\.92|2\.31 ?V|0\.99 ?V" 383116e -- <corpus>]`:
  - `crosses \`V_IH\` at **119.9 µs**`, which is covered
  - `\`V_IH\` = 2.31 V`, which is covered
  - `\`V_IH\` 2.31 V, \`V_IL\` 0.99 V` (ADR 0001:229), which is **not** covered
  - the `C-KEY` CSV cell `Press crosses the HC165's VIL (0.99V at 3.3V)` in
    both `hardware/bom.csv:38` and the fragment, which is **not** covered
- Test on a scratch copy: I restored `383116e`'s
  `key-switch-network/bom.csv`, re-merged, and ran the checker. The result was
  **`PASS no live stale values`**, with the retired 0.99 V live in two CSV
  files `[run: tools/merge-bom.py; tools/check-staleness.py, scratch copy]`.
  This is the escape `escape_note` describes, a third time.
- Adding `"0.99V at 3.3V"`, `"\`V_IL\` 0.99 V"`, `"\`V_IH\` 2.31 V"`,
  `"119.9 µs"` and `"5.92 µs"`:
  - on the **current** tree, still **PASS**. The only hits are
    `key-switch-network/notes.md`, where the prose refutation window excuses
    them.
  - on the restored old row, **FAIL**, naming both `bom.csv` files
  - `[run: same scratch copy, figures.yaml edited]`

**Fix:** add those five patterns. The `false_positive_note` already covers
119.9 µs as the 74HC165 and Nexperia HCS crossing in prose.

### R1-5 [low] "The release reaches firmware on the next scan either way" is false for about 55 % of releases

**Node:** `key-release-time` (`role_note`); `key-switch-network.md` §2; ADR 0001
amendment ("changes no conclusion").

**Evidence.**
- `[calc]` A release is seen at the first scan after it crosses VT+.
- With the crossing delayed by d = 138.7 µs and a uniformly distributed scan
  phase, it slips one extra scan whenever the phase is under d. That happens
  with probability d/T = 138.7/250 = **0.555**.
- The mean added latency is d = 138.7 µs. The maximum is one scan, 250 µs.

"Costs nothing musically" is still defensible, because releases sit behind
firmware's millisecond-scale release window `[firmware/README.md;
docs/reference/latency-budget.md]`. The sentence explaining why is wrong.

**Fix:** "adds 0 or 1 scan (mean `key-release-time`), which is invisible
behind the release window."

### R1-6 [low] `latency-budget.md` says the press is "two orders of magnitude inside the scan period". It is 25×.

**Node:** `key-press-time`; `docs/reference/latency-budget.md` Key path table.

**Evidence.** `[calc]` 250/9.87 = 25.3×, about 1.4 orders of magnitude. The
figure's own `note` says 25× `[config/figures.yaml]`. Two orders of magnitude
was true of the long-retired ~1 µs press. At `383116e` it was 42×, which was
already not true.

**Fix:** "well inside the scan period (the figure's note)". Cite, do not
restate a ratio.

### R1-7 [advisory] "Guaranteed extremes" overstates what TI publishes, component tolerance is left out, and neither changes a conclusion

**Node:** `key-release-time`, `key-press-time`; `key-switch-network.md`
§Derivations ("taken at their guaranteed extremes").

**Evidence.**
- TI guarantees nothing at 3.3 V `[p.6]`. The 0.75/0.15 ratios are an
  extrapolation of the worst published ratio. That is a sound engineering
  bound, and the table's own "not interpolated" reasoning holds. It is not a
  guarantee.
- The derivation uses nominal R and C, while C-KEY is ±10 % X7R. `[calc]`
  138.7 × 1.01 × 1.10 × 1.15 (X7R over temperature) = **177 µs**.
- The conclusions are robust. `[calc]` The release stays inside 250 µs for any
  VT+ up to 3.3 − 3.1565·e^(−250/103.4) = **3.02 V = 0.915 × VCC**. The press
  stays at least 25× inside the scan.

**Fix:** say "extrapolated bound", add one line on robustness, and optionally
a tolerance line in the derivation.

### R1-8 [advisory] The hold-margin argument cites the *maximum* propagation delay; hold depends on the minimum, which TI does not publish

**Node:** chain order rule. ADR 0001 fix 3 ("~0.5 ns against an HC165's
propagation delay of tens of nanoseconds"); `config/key-layout.yaml` `chain`
comment ("SN74HCS165 CLK->QH, its datasheet p.7").

**Evidence.**
- p.7 gives tpd CLK→QH **max** only: 16/18 ns at 4.5 V and 32/45 ns at 2 V.
- Hold margin is tpd_min + flight − skew − t_h.
- p.7 does give t_h (SER data after CLK↑) = **0 ns** at every rail. So the
  0.5 ns skew needs only tpd_min > 0.5 ns. That is near certain, but it is
  not the "tens of ns" the text uses.

This is the same wrong-side-of-the-bound shape as R1-1 and R1-2.

**Fix:** "hold time is 0 ns (p.7), so skew only needs to stay under the
unpublished minimum tpd".

### R1-9 [advisory] SPI3's clock mode is specified nowhere, and `spi-link.md` adds four CLK→QH delays that do not accumulate

**Node:** SPI3 / `SCK` / right_thumb `QH` → MCU.

**Evidence.**
- A search for CPOL, CPHA, "mode", "falling", "rising" or "sample" across
  `key-chain-loom/`, `spi-link/`, `hardware/cluster/`, `firmware/`, ADR 0001
  and `latency-budget.md` finds nothing for SPI3 `[run: grep -rn -i
  "falling\|rising\|sample.*edge\|mode [0-3]\|CPOL\|CPHA" …]`.
- The register presents H on `QH` during the load and shifts on CLK↑
  `[p.11 §8.1; p.13 Table 8-1]`. So:
  - CPHA = 0 (mode 0 or 2) is required
  - CPHA = 1 samples after the first shift and drops bit 0. The marker would
    catch it as a framing error, not a silent fault.
  - Mode 2 (sample on the falling edge) samples mid-bit
- `spi-link.md`'s "(+ four register CLK→QH delays …)" treats the delays as
  cumulative. Each hop is re-sampled on the next clock, so only the last
  register's tpd plus flight matters, against the MCU's sampling edge.

**Fix:** one line in `spi-link.md`: "SPI3 mode 0 or 2 (CPHA = 0), because `QH`
shows H before the first clock". Correct "four delays" to "one".

### R1-10 [advisory] HC threshold vocabulary survives on a Schmitt part

**Node:** `R-KEY-SER` row ("press crosses V_IL … release crosses V_IH");
ADR 0001:204 ("Any glitch below V_IL during the 32-clock shift" on `SH/LD`);
ADR 0001:162–163 ("landing at 1.94 V against a 0.8 V threshold").

**Evidence.**
- The SN74HCS165 has no V_IL or V_IH. It has VT+, VT− and ΔVT `[p.6]`.
- `C-KEY`'s row was converted; `R-KEY-SER`'s, in the same fragment, was not
  `[hardware/cluster/key-switch-network/bom.csv]`.
- ADR 0001:162's 0.8 V is LVC. The same ADR's line 218 amendment corrects it,
  but the amendment is 55 lines further down.

**Fix:** VT− and VT+ in the `R-KEY-SER` row, and at `SH/LD` in ADR 0001:204.
That line can also note that `SH/LD` is now a Schmitt input, which lowers the
glitch risk it describes.

### R1-11 [advisory] "As high as 0.5 × VCC … every row" is slightly off (the 4.5 V row is 0.489), and the owner page uses τ ≈ 4.7 µs where the register says "not 4.7"

**Node:** ADR 0001:219 (coupling margin); `key-switch-network.md` "What
`R-KEY-SER` is for".

**Evidence.**
- VT− max: 1.0/2 = 0.5, 2.2/4.5 = 0.489, 3.0/6 = 0.5 `[p.6]`. The BOM's "at
  most 0.5 × VCC in every row" is exact. ADR 0001's "0.5 × VCC … every row" is
  not quite. The margin conclusion is unaffected: `[calc]` 1.94 − 1.65 =
  0.29 V.
- Separately, the owner page's discharge "τ ≈ 4.7 µs" is 100 Ω × 47 nF. The
  register's `key-press-time` `threshold_note` explicitly says the τ is
  "4.4957 us, not 100 ohm x 47 nF = 4.7 us". The discharge current decays with
  the Thévenin τ, 4.496 µs.

**Fix:** "at most 0.5 × VCC", and τ ≈ 4.5 µs.

### R1-12 [advisory] The ESD sentence quotes a component-level HBM rating as field protection

**Node:** key-board `J-CHAIN` signal pins; the `HOP_*` nets.
`key-chain-loom.md` ("Those pins carry the SN74HCS165's own rating, ±4000 V
HBM … ±1500 V CDM"); `cluster-boards.md` ESD paragraph.

**Evidence.**
- The numbers are right `[p.4]`. TI's footnote to the same table says JS-001
  HBM is a manufacturing-handling rating ("500-V HBM allows safe manufacturing
  with a standard ESD control process").
- It is not a system-level (IEC 61000-4-2) rating for a contact touched with
  the lid off.
- The pages accept the risk explicitly, because the register is replaceable.
  The rating should not read as the reason the exposure is safe.

**Fix:** one clause, "a component rating; the exposure is accepted, not
protected".

---

## Checked and found correct

**The part**
- The `U-KEYS` sheet fields `[hardware/cluster/key-register/key-register.kicad_sch]`
  are right: Value `74HCS165`, Manufacturer Texas Instruments, MPN
  SN74HCS165DR, LCSC C2864745, Assembly machine.
- `Pins` matches TI Table 5-1 pin for pin `[p.3]`: SH/LD 1, CLK 2, E–H 3–6,
  /QH 7, GND 8, QH 9, SER 10, A–D 11–14, CLK INH 15, VCC 16.
- `Pins_source` cites p.3 §5 correctly. The `Note` is correct apart from R1-2.
- SN74HCS165DR is Active, SOIC-16, MSL1 `[p. package addendum]`.
- LCSC C2864745 is SN74HCS165DR `[web https://www.lcsc.com/product-detail/C2864745.html;
  https://jlcpcb.com/partdetail/TexasInstruments-SN74HCS165DR/C2864745, 2026-09-27]`.
- The exported `key-register/netlist.yaml`, both `board-netlist.yaml` files
  (LH and RH), the LH `.kicad_pcb` and `fab/key-board-lh-bom-jlc.csv` all
  carry 74HCS165 / C2864745.
- `[run: tools/kicad.py check]` PASS (3 sheets, 2 boards, 39 renders).
  `[run: tools/check-netlist.py --strict]` 0 problems.
  `[run: tools/merge-bom.py --check]` 0 problems.
  `[run: tools/check-staleness.py]` PASS.
- The `U-KEYS` row is consistent with the sheet: the part is SN74HCS165,
  manufacturer "multiple", and a substitute must be Schmitt with no rate
  limit.
- A Nexperia 74HCS165 would qualify. It has no Δt/ΔV row
  `[74HCS165-nexperia.pdf p.6]`.
- The 74LV165A would not: 100 ns/V at 3.0–3.6 V
  `[74LV165A-nexperia.pdf p.5]`.
- The "no input signal transition rate requirements" quote is verbatim
  `[p.15 §9.2.1.2]`.

**The network values:** 2k2 1 %, 100R 1 % and 47 nF are the same on the
sheet, in the netlist, in the BOM fragment and in the drawing.

**The figures, re-derived** `[calc]`:
- Pressed node: 3.3 × 100/2300 = 0.1435 V.
- τ_rel = 103.40 µs. τ_press = 95.65 Ω × 47 nF = 4.4957 µs.
- Release at 2.475 V: **138.75 µs**. Press at 0.495 V: **9.868 µs**.
- Interpolated values: 2.358 V → 125.03 µs, and 0.612 V → 8.576 µs.
- Nexperia's 3.0–3.6 V row (0.7/0.2 × VCC = 2.31 V and 0.66 V) sits inside
  the bound, as the page says.
- The rest match: pole 1.539 kHz, 54.3 dB at 800 kHz; 1.435 mA per key and
  27.3 mA for 19 keys; 10 kΩ gives 6.2 mA, 646.9 µs, and about 137.6 µs with
  10 nF; 250/9.87 = 25.3×; 138.7/250 = 0.555.

**Threshold direction:**
- The release must pass VT+ **max**. The press must pass VT− **min**.
- This is the right worst case for *latency*. TI says it verbatim: "Input
  signals must cross Vt-(min) to be considered a logic LOW, and Vt+(max) to be
  considered a logic HIGH" `[p.15 §9.2.1.2]`.
- The table ratios on the owner page are right: 0.75/0.15, 0.70/0.20 and
  0.70/0.20.
- Hysteresis minima 0.2 V and 0.4 V are right `[p.6]`.

**Forbidden patterns:**
- All 35 patterns across the two entries match nothing in correct live text.
- The only corpus hits outside `config/figures.yaml` are in
  `key-switch-network/notes.md`: 6 patterns, all history in prose and all
  excused `[run: literal-match script over the §6 corpus]`.
- The gap is R1-4.

**Where the figures are cited:** ADR 0001's table and the `C-KEY` and
`R-KEY-SER` rows cite by name. `key-switch-network.md` is the owner. No other
live page restates 138.7, 9.87, 2.31, 0.99, 119.9 or 5.92 `[run: grep -rnE …
§6 corpus]`.

**ADR 0001 amendment:**
- "About 280× on release and 14× on press" re-derives. `[calc]` 0.99/103.4 =
  9.57 mV/µs is 104 500 ns/V, against 625 − 0.52 × 486 = 372 ns/V, so 280×.
  The press slope is 0.8465/4.4957 → 5311 ns/V, so 14×.
- fclock at the 2 V rail over temperature is 43 MHz min `[p.6]`, far above
  1 MHz.
- 74HC165 `tt` of 15 ns at 25 °C `[74HC165-nexperia.pdf p.8]` is right.
- ±4000 V HBM and ±1500 V CDM `[p.4]` are right, against the 74HC165's
  >2000 V HBM `[74HC165-nexperia.pdf p.1]`.
- The coupling margin: `[calc]` 1.94 − 1.65 = 0.29 V, so "about 0.3 V" is
  right.

**The chain at 1 MHz:**
- 32 bits take 32 µs, which is 12.8 % of 250 µs.
- `spi-link.md`'s 18–45 ns CLK→QH over temperature at 4.5–2 V matches p.7.
- Setup is ≤ 21 ns (SH/LD before CLK↑, 2 V) and ≤ 14 ns (SER), and hold is
  0 ns `[p.7]`. All are negligible at a 500 ns half period.

**`key-register.md` citations:**
- The SH/LD function citations p.13 Table 8-1 and 8-2 are right.
- "During the load H appears at QH" is stated in words on p.11 §8.1, which
  could be cited too.
- `CLK INH` tied low and /QH left open are consistent with p.15 ("Unused
  outputs can be left floating").

**Quiescent current:** "microamps" is right: ICC is 2 µA max at 6 V over
temperature `[p.6]`. This covers the LH README bring-up step and ADR 0005.

**Superseded ADRs:** ADR 0008:109 and ADR 0013:263 still say "74HC165", as the
historical wording of ADRs marked superseded. ADR 0010:19 is amended in
place. None is a live claim.
