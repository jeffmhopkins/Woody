# D3 — the `REFUTATION` change in `tools/check-staleness.py`, and every exemption it grants

**Slice:** the refutation exemption as `0e68f25` left it — narrowed vocabulary,
a 300-character window, and a separate case-sensitive `REFUTATION_SHOUT`.
**Method:** the corpus at `HEAD` (`092b364`), extracted with
`git archive HEAD | tar -x` into a scratchpad and re-driven through a harness
that reproduces `check_figures()` exactly. Everything marked `[test]` was run;
everything marked `[repo]` was read.

Report only. Nothing in the corpus or the tools was changed.

---

## 0. The headline, before the detail

`[test]` `python3 tools/check-staleness.py`:

```
PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 218 patterns
```

`[test]` Harness over the same 218 patterns and the same 123 files:

```
TOTAL forbidden-pattern MATCHES in the corpus:  68
    exempted by REFUTATION / REFUTATION_SHOUT:  68
                             reported as live:   0
```

**Every single match the staleness check finds is currently exempted.** The
`live` list is not small; it is empty, and it is empty because the exemption
consumed all of it. The `STALE VALUES STILL LIVE` block has not been printed by
this tool on this corpus at all — 68 of 68.

That is the fact this slice exists to state. The check's entire visible output
is the exemption count, and `CLAUDE.md` says of exactly this shape that a run
with no coverage "used to print the same PASS line as a healthy one". It still
does, one level further in: not an empty pattern list, but a pattern list whose
every hit is waved through.

Four of those 68 records are laundering something live and four more are
marginal — 8 records, 4 distinct pieces of text, each appearing once in
`hardware/bom.csv` and once in the fragment it is generated from. Separately,
three of the register's 218 patterns are structurally incapable of ever firing
anywhere. Details below.

---

## 1. Every exemption, enumerated

`[test]` All 68, with the marker that does the exempting and its signed
character distance from the match (negative = marker precedes the match).
"Verdict" is my hand judgement of each, argued in §2.

| # | file:line | figure (now) | pattern | nearest marker | d | verdict |
|---|---|---|---|---|---|---|
| E01 | `docs/decisions/0003-breath-sensing-path.md`:118 | `sensor-full-scale` = 4.86 V | `0.2–4.80 V` | `refuted` | -87 | ok |
| E02 | `docs/decisions/0003-breath-sensing-path.md`:118 | `sensor-full-scale` = 4.86 V | `0.2–4.80 V` | `refuted` | -100 | ok |
| E03 | `docs/decisions/0004-cv-interface-module.md`:78 | `spi-series-r` = 100 ohm, R-SPI-SER, qty 3 | `220 Ω with` | `2026-09-21` | -25 | ok |
| E04 | `docs/decisions/0004-cv-interface-module.md`:276 | `umbilical-current` = 359 mA | `~275 instrument` | `until 2026` | +3 | ok |
| E05 | `docs/decisions/0004-cv-interface-module.md`:328 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `20 cents of breath-correlated` | `used to` | -25 | ok |
| E06 | `docs/decisions/0004-cv-interface-module.md`:328 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `about 20 cents` | `used to` | -19 | ok |
| E07 | `docs/decisions/0004-cv-interface-module.md`:335 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `0.00018 cents` | `superseded` | -12 | ok |
| E08 | `docs/decisions/0004-cv-interface-module.md`:558 | `spi-series-r` = 100 ohm, R-SPI-SER, qty 3 | `R-CS-SER` | `previously` | -47 | ok |
| E09 | `docs/decisions/0004-cv-interface-module.md`:558 | `spi-series-r` = 100 ohm, R-SPI-SER, qty 3 | `R-SCLK-SER` | `previously` | -17 | ok |
| E10 | `docs/decisions/0006-cv-channel-allocation.md`:265 | `mod-reference` = 3.3333 V | `written once at boot` | `until 2026` | +14 | ok |
| E11 | `docs/decisions/0006-cv-channel-allocation.md`:657 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `0.00027 cents` | `until 2026` | +4 | ok |
| E12 | `docs/decisions/0006-cv-channel-allocation.md`:722 | `pitch-compensation` = 2.2 nF, op-amp OUTPUT to the (-) input | `1 nF across the feedback resistor` | `until 2026` | -74 | ok |
| E13 | `docs/reference/latency-budget.md`:183 | `loop-budget` = 196-241 us of 250 us | `136 µs` | `superseded` | -12 | ok |
| E14 | `docs/reference/latency-budget.md`:184 | `loop-budget` = 196-241 us of 250 us | `54 % duty` | `superseded` | -12 | ok |
| E15 | `docs/reference/repo-maintenance.md`:43 | `sensor-full-scale` = 4.86 V | `0.2 + 0.766` | `superseded` | -12 | ok |
| E16 | `hardware/bom.csv`:30 | `chain-connectors` = 8 | `five connectors must match` | `2026-09-21` | -222 | **LAUNDERED** |
| E17 | `hardware/bom.csv`:36 | `key-release-time` = 119.9 us | `~93us` | `SUPERSEDED` | -40 | ok |
| E18 | `hardware/bom.csv`:37 | `key-press-time` = 5.92 us | `~5.7us` | `CORRECTED` | +28 | ok |
| E19 | `hardware/bom.csv`:37 | `key-release-time` = 119.9 us | `~125us` | `CORRECTED` | +12 | ok |
| E20 | `hardware/bom.csv`:47 | `spi-series-r` = 100 ohm, R-SPI-SER, qty 3 | `R-CS-SER` | `used to` | -48 | ok |
| E21 | `hardware/bom.csv`:47 | `spi-series-r` = 100 ohm, R-SPI-SER, qty 3 | `R-SCLK-SER` | `used to` | -22 | ok |
| E22 | `hardware/bom.csv`:57 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `0.00029 cents` | `THIS ROW CARRIED` | -17 | ok |
| E23 | `hardware/bom.csv`:57 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `20 cents of breath-correlated` | `2026-09-21` | +57 | ok |
| E24 | `hardware/bom.csv`:57 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `20 cents of breath-correlated` | `2026-09-21` | -17 | ok |
| E25 | `hardware/bom.csv`:57 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `by ~80mV` | `NOT` | -61 | **LAUNDERED** |
| E26 | `hardware/bom.csv`:61 | `ferrite-bias-impedance` = ~580-614 ohm on FB1/FB3/FB4; ~280-310 ohm on FB2 | `Rated >=1A - the common 0805 600R part i…` | `2026-09-21` | +152 | ok |
| E27 | `hardware/bom.csv`:63 | `panel-toggle-hole` = 6.5 mm diameter with a 5.8 mm D-flat | `6.00 and 6.35 need different holes` | `2026-09-21` | +34 | ok |
| E28 | `hardware/bom.csv`:67 | `loadswitch-fb-divider` = 35.7 kohm / 5.11 kohm, both 1% | `VALUES NOT SET` | `NOT` | +0 | ok / **dead pattern** |
| E29 | `hardware/bom.csv`:71 | `loadswitch-timer` = 10 uF | `2.4x the ~62ms` | `2026-09-21` | +261 | **marginal** |
| E30 | `hardware/bom.csv`:71 | `loadswitch-timer` = 10 uF | `the reviewers disagree and the datasheet…` | `2026-09-21` | +109 | **marginal** |
| E31 | `hardware/bom.csv`:72 | `loadswitch-gate-cap` = 82 nF, ramp 49-197 ms (98 ms typ) | `a ramp spec with an unbounded tolerance` | `2026-09-21` | -75 | ok |
| E32 | `hardware/bom.csv`:72 | `loadswitch-gate-cap` = 82 nF, ramp 49-197 ms (98 ms typ) | `so ~83nF` | `2026-09-21` | +3 | ok |
| E33 | `hardware/bom.csv`:80 | `breath-zero-ref` = 0.573 V | `0.579 V` | `THIS ROW SAID` | -39 | ok |
| E34 | `hardware/bom.csv`:80 | `breath-zero-ref` = 0.573 V | `to ~0.579 V` | `THIS ROW SAID` | -35 | ok |
| E35 | `hardware/bom.csv`:80 | `breath-zero-ref` = 0.573 V | `~0.437 V` | `THIS ROW SAID` | -26 | ok |
| E36 | `hardware/bom.csv`:81 | `inamp-full-scale` = -9.94 V | `-10.05 V` | `until 2026` | +88 | ok |
| E37 | `hardware/bom.csv`:81 | `inamp-full-scale` = -9.94 V | `-9.6V` | `until 2026` | +165 | ok |
| E38 | `hardware/carrier/bom.csv`:6 | `chain-connectors` = 8 | `five connectors must match` | `2026-09-21` | -222 | **LAUNDERED** |
| E39 | `hardware/cluster/key-marker-and-bits/key-marker-and-bits.md`:103 | `key-pullup-qty` = 24 | `21 pull-ups` | `carried a superseded` | -30 | ok |
| E40 | `hardware/cluster/key-switch-network/bom.csv`:4 | `key-release-time` = 119.9 us | `~93us` | `SUPERSEDED` | -40 | ok |
| E41 | `hardware/cluster/key-switch-network/bom.csv`:5 | `key-press-time` = 5.92 us | `~5.7us` | `CORRECTED` | +28 | ok |
| E42 | `hardware/cluster/key-switch-network/bom.csv`:5 | `key-release-time` = 119.9 us | `~125us` | `CORRECTED` | +12 | ok |
| E43 | `hardware/interfaces/spi-link/bom.csv`:3 | `spi-series-r` = 100 ohm, R-SPI-SER, qty 3 | `R-CS-SER` | `used to` | -48 | ok |
| E44 | `hardware/interfaces/spi-link/bom.csv`:3 | `spi-series-r` = 100 ohm, R-SPI-SER, qty 3 | `R-SCLK-SER` | `used to` | -22 | ok |
| E45 | `hardware/interfaces/spi-link/spi-link.md`:59 | `spi-series-r` = 100 ohm, R-SPI-SER, qty 3 | `R-CS-SER` | `previously` | -48 | ok |
| E46 | `hardware/interfaces/spi-link/spi-link.md`:59 | `spi-series-r` = 100 ohm, R-SPI-SER, qty 3 | `R-SCLK-SER` | `previously` | -17 | ok |
| E47 | `hardware/module/breath-receive-stage/bom.csv`:3 | `breath-zero-ref` = 0.573 V | `0.579 V` | `THIS ROW SAID` | -39 | ok |
| E48 | `hardware/module/breath-receive-stage/bom.csv`:3 | `breath-zero-ref` = 0.573 V | `to ~0.579 V` | `THIS ROW SAID` | -35 | ok |
| E49 | `hardware/module/breath-receive-stage/bom.csv`:3 | `breath-zero-ref` = 0.573 V | `~0.437 V` | `THIS ROW SAID` | -26 | ok |
| E50 | `hardware/module/breath-receive-stage/bom.csv`:4 | `inamp-full-scale` = -9.94 V | `-10.05 V` | `until 2026` | +88 | ok |
| E51 | `hardware/module/breath-receive-stage/bom.csv`:4 | `inamp-full-scale` = -9.94 V | `-9.6V` | `until 2026` | +165 | ok |
| E52 | `hardware/module/breath-receive-stage/breath-receive-stage.md`:95 | `inamp-full-scale` = -9.94 V | `−10.05 V` | `this line carried` | -18 | ok |
| E53 | `hardware/module/breath-receive-stage/breath-receive-stage.md`:123 | `breath-zero-ref` = 0.573 V | `+0.579 V` | `until 2026` | +1 | ok |
| E54 | `hardware/module/breath-receive-stage/breath-receive-stage.md`:123 | `breath-zero-ref` = 0.573 V | `0.579 V` | `until 2026` | +1 | ok |
| E55 | `hardware/module/mod-channels/mod-channels.md`:201 | `mod-reference` = 3.3333 V | `At 2.5 V into 2.5 k` | `until 2026` | +16 | ok |
| E56 | `hardware/module/power-entry/bom.csv`:4 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `0.00029 cents` | `THIS ROW CARRIED` | -17 | ok |
| E57 | `hardware/module/power-entry/bom.csv`:4 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `20 cents of breath-correlated` | `2026-09-21` | +57 | ok |
| E58 | `hardware/module/power-entry/bom.csv`:4 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `20 cents of breath-correlated` | `2026-09-21` | -17 | ok |
| E59 | `hardware/module/power-entry/bom.csv`:4 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `by ~80mV` | `NOT` | -61 | **LAUNDERED** |
| E60 | `hardware/module/power-entry/bom.csv`:8 | `ferrite-bias-impedance` = ~580-614 ohm on FB1/FB3/FB4; ~280-310 ohm on FB2 | `Rated >=1A - the common 0805 600R part i…` | `2026-09-21` | +152 | ok |
| E61 | `hardware/module/power-entry/power-entry.md`:102 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `20 cents of breath-correlated` | `used to` | -44 | ok |
| E62 | `hardware/module/power-entry/power-entry.md`:102 | `diode-split-rationale` = fault isolation and HF isolation (r_d 69 mohm at 392 mA) | `about 20 cents` | `used to` | -38 | ok |
| E63 | `hardware/module/umbilical-load-switch/bom.csv`:2 | `panel-toggle-hole` = 6.5 mm diameter with a 5.8 mm D-flat | `6.00 and 6.35 need different holes` | `2026-09-21` | +34 | ok |
| E64 | `hardware/module/umbilical-load-switch/bom.csv`:6 | `loadswitch-fb-divider` = 35.7 kohm / 5.11 kohm, both 1% | `VALUES NOT SET` | `NOT` | +0 | ok / **dead pattern** |
| E65 | `hardware/module/umbilical-load-switch/bom.csv`:10 | `loadswitch-timer` = 10 uF | `2.4x the ~62ms` | `2026-09-21` | +261 | **marginal** |
| E66 | `hardware/module/umbilical-load-switch/bom.csv`:10 | `loadswitch-timer` = 10 uF | `the reviewers disagree and the datasheet…` | `2026-09-21` | +109 | **marginal** |
| E67 | `hardware/module/umbilical-load-switch/bom.csv`:11 | `loadswitch-gate-cap` = 82 nF, ramp 49-197 ms (98 ms typ) | `a ramp spec with an unbounded tolerance` | `2026-09-21` | -75 | ok |
| E68 | `hardware/module/umbilical-load-switch/bom.csv`:11 | `loadswitch-gate-cap` = 82 nF, ramp 49-197 ms (98 ms typ) | `so ~83nF` | `2026-09-21` | +3 | ok |

Distribution `[test]`: the 68 records cover **46 distinct pieces of text**. 22 of
those texts appear twice — once in `hardware/bom.csv` and once in the
per-circuit fragment it is generated from — accounting for 44 of the 68 records;
the remaining 24 are unique. Per file: `hardware/bom.csv`
22, `docs/decisions/0004-cv-interface-module.md` 7,
`hardware/module/umbilical-load-switch/bom.csv` 6,
`hardware/module/breath-receive-stage/bom.csv` 5,
`hardware/module/power-entry/bom.csv` 5, and eleven files with 1–3 each.

---

## 2. The exemptions that are laundering something live

### D3-1 — `WIRE-LOOM` still says "five connectors". The commit that changed `REFUTATION` names this exact row as one of the two escapes it was closing, and it is still escaping.

`[repo]` `hardware/bom.csv`:30 and `hardware/carrier/bom.csv`:6, `WIRE-LOOM`
notes cell, in full through the match:

> DECIDED 2026-09-21: J-CHAIN is a 2x6 IDC on a 12-way ribbon, alternating
> ground … TWELVE conductors per hop, chained through each cluster board in turn
> rather than starred, **so five connectors must match: one on the carrier and
> one per cluster board.**

`[repo]` `config/figures.yaml`, `chain-connectors`:

```
value: 8
derivation: SER/QH are point-to-point, so every cluster board but the last has
            IN and OUT: carrier 1, RT 2, RH 2, LT 2, LH 1
forbidden: ['five connectors must match', 'Five connectors', '~4 connectors']
```

`[repo]` `hardware/bom.csv`, the `J-CHAIN` row — **two rows away in the same
file** — says: "EIGHT of them, not five: the chain is four hops and SER/QH are
point-to-point rather than bus … Carrier 1, right_thumb 2, right_hand 2,
left_thumb 2, left_hand 1".

So the corpus contradicts itself inside one generated file, the register carries
a pattern written for precisely this sentence, and the sentence's own arithmetic
("one on the carrier and one per cluster board" = 1 + 4) is the superseded
star-topology count.

`[repo]` `git show 0e68f25`, commit message, and the same text in the comment at
`tools/check-staleness.py`:83–86:

> WIRE-LOOM states a live "five connectors" against a tracked 8, and is excused
> by "rather than starred" 24 characters away — an unrelated clause, closer to
> the claim than any tightening could exclude.

`[test]` Under the shipped code the marker is no longer `rather than`; it is the
cell's opening `DECIDED **2026-09-21**:`, **222 characters before the match**,
which is the newly-added dated marker. The notes cell contains no refutation of
"five" anywhere. `[test]` Removing `\d{4}-\d{2}-\d{2}` from `REFUTATION` and
changing nothing else makes both instances report as live.

The fix rewrote the vocabulary that was excusing this row and simultaneously
added a marker that excuses it again. Net change to `WIRE-LOOM`: none. This is
the project's named failure mode — a fix that lands where the editing is
happening and not where the reader looks — committed inside the commit whose
message is about it.

**Two things are wrong and they need separate fixes.** The sentence is false and
belongs in D6–D8's or D9–D11's lap; the exemption is the checker's and is
addressed in §6 below.

### D3-2 — `D-REVPOL` states `~80mV` as live fact; the nearby correction corrects a different quantity.

`[repo]` `hardware/bom.csv`:57 and `hardware/module/power-entry/bom.csv`:4:

> … the module's analog +12V and the umbilical feed must NOT share a diode —
> **instrument current then modulates its Vf by ~80mV**, which is ~20 cents of
> breath-correlated pitch bend and needs no ground path at all (ADR 0006)
> **| 2026-09-21:** the '20 cents of breath-correlated pitch bend' this row used
> to cite as the reason for the THIRD diode **is refuted** …

`[repo]` `config/figures.yaml`, `diode-split-rationale`:
`derivation: Vf modulation is 120 mV: 0.24 V at 245 mA -> 0.36 V at 612 mA,
digitised off Fig. 2 of Diodes Inc DS23001 Rev.8`, and `by ~80mV` is in its
`forbidden` list. `[calc]` 0.36 − 0.24 = 0.12 V = 120 mV, so 80 mV is the
superseded estimate the register exists to reject.

The appended segment refutes **the cents**, not the millivolts. `[test]` The
markers in this window, by distance from the match: a shouted `NOT` at **−61**,
which is the live design rule "must **NOT** share a diode"; the segment's
`2026-09-21` at **+98**; `used to` at +166 and `refuted` at +216, both of which
are about the 20 cents. Nothing within 300 characters of `by ~80mV` corrects
`by ~80mV`. The nearest marker of all is an instruction, which is §3's point
arriving in a case where it matters.

The owner page shows what the correction is supposed to look like.
`[repo]` `hardware/module/power-entry/power-entry.md`:87–92 states **120 mV** and
carries "> **This page said ~80 mV, and a reviewer's independent estimate said
75 mV.**" `[repo]` The register's own `false_positive_note` for this figure
names that line as the correct form. `D-REVPOL` has no equivalent; it just
still says 80 mV.

The row's third segment says "This row had even recorded the ~80mV to 120mV
correction and still did not follow it through to the cents figure." It did not
follow it through to the millivolts either.

**What would settle it:** whether the project reads a `|`-appended dated segment
as striking everything above it in the cell. If yes, this is fine and the
convention should be written down in `repo-maintenance.md` so the checker can be
taught it. If no — and the owner page's explicit "This page said ~80 mV" says
no — the sentence is a live stale value.

### D3-3 — `C-TIMER-LOADSW`: two register-forbidden sentences stand un-struck, exempted by dates about a different dispute.

`[repo]` `hardware/bom.csv`:71 and
`hardware/module/umbilical-load-switch/bom.csv`:10, opening of the notes cell:

> … target t = 150ms, **which is 2.4x the ~62ms current-limited start that
> foldback forces**. That is 365nF if I_TIMER is 3uA and 9.25uF if it is 76uA —
> **the reviewers disagree and the datasheet decides.** READ THE LT1641
> DATASHEET BEFORE ORDERING.

`[repo]` Both strings are in `loadswitch-timer`'s `forbidden` list, and the
register's own `note` says: "The '150 ms = 2.4x the 62 ms start' justification
is **ALSO retired**: the 62 ms was integrated across the whole ramp, which is
only true while FB is unconnected." `[repo]` The row's later segments resolve the
reviewer dispute ("the dispute RESOLVES to the 76uA camp") and abandon the 150 ms
target ("THE 150ms TARGET WAS NEVER THE SPEC"), but **neither segment retires the
62 ms figure**, and neither says the opening sentences are superseded.

`[test]` `'2.4x the ~62ms'` is exempted by a `2026-09-21` **261 characters away**
— the widest exempting distance in the whole corpus, and 87 % of the window.
`'the reviewers disagree and the datasheet decides'` is exempted by one 109 away.

Marked **marginal** rather than laundered: unlike D3-1 the row *is* a narrated
history and a reader who finishes the cell learns the truth. But the register
explicitly lists these strings as forbidden *and* explicitly records the 62 ms as
retired, so the register and the checker disagree about this cell, and the
checker is the one that renders green.

### D3-4 — three of the register's 218 patterns contain a refutation marker **inside the pattern itself** and can therefore never be reported, anywhere.

`[test]` Scanning every `forbidden` pattern against `REFUTATION` and
`REFUTATION_SHOUT`:

| figure | pattern | self-matches | occurrences today |
|---|---|---|---|
| `loadswitch-fb-divider` | `VALUES NOT SET` | `NOT` (shout) | 2 |
| `sensor-full-scale` | `0.2 → 4.8 V` | `→` (arrow) | 0 |
| `diode-split-rationale` | `75 mV → LM317` | `→` (arrow) | 0 |

`[test]` synthetic confirmation, no surrounding text at all:

```
pattern 'VALUES NOT SET': self-match -> True => can NEVER be reported, anywhere
pattern '0.2 → 4.8 V':    self-match -> True => can NEVER be reported, anywhere
pattern '75 mV → LM317':  self-match -> True => can NEVER be reported, anywhere
```

The window is centred on the match and always includes the match, so a marker
inside `bad` is inside `near` unconditionally. The two arrow patterns match
nothing today, so they are dead in the strongest sense: they were added to guard
a spelling, they are counted in the `218 patterns` coverage figure, and if that
spelling ever reappeared they would exempt it.

This is the class `check_patterns()` exists to catch — "a forbidden pattern that
CANNOT match is indistinguishable from one that matches nothing" — and
`check_patterns()` only looks for embedded newlines. `[test]` Both arrow
patterns and `VALUES NOT SET` pass `check_patterns()` clean.

`sensor-full-scale` is the figure `CLAUDE.md` names as the worst recorded
staleness case, the one whose list was rewritten after eleven derived statements
survived a zero-hit run. One of its replacement patterns cannot fire.

### D3-5 — everything else (58 of 68) is a genuine correction

I read all 68 windows. The other 58 are the real thing and are working exactly
as intended: `sensor-full-scale`'s ADR 0003 comparison row is labelled "cover-page
line, refuted by the transfer function inside the same document"; the
`key-press-time`/`key-release-time` BOM fields open "SUPERSEDED: this field
carried ~5.7us…"; `spi-series-r`'s stale refdes are quoted under "carrier.md
**used to** draw these as…"; `breath-zero-ref` under "THIS ROW SAID '…'";
`inamp-full-scale` under "This field read … **until 2026-09-21**";
`loop-budget` under "**Until 2026-09-21** this paragraph was wrong twice over";
`repo-maintenance.md`:43 even explains its own exemption in the prose.

`ferrite-bias-impedance`/`FB-IN` — the *other* named escape in `0e68f25`'s
message — **is genuinely closed**: `[repo]` `hardware/bom.csv`:61 now carries
"*** 2026-09-21 PART CHOSEN, AND THIS ROW'S OWN PREMISE IS REFUTED BY THE
DATASHEET THAT CHOSE IT. ***", 152 characters after the match. That one was
fixed by editing the text, which is why it stayed fixed. `WIRE-LOOM` was left to
the regex, which is why it did not.

---

## 3. `REFUTATION_SHOUT` — it grants nothing, and it fires on instructions

`[test]` Deleting `REFUTATION_SHOUT` entirely and re-running:

```
AS SHIPPED (full, shout, w=300)      live=  0   exempt= 68
shout REMOVED       (w=300)          live=  0   exempt= 68
```

**`REFUTATION_SHOUT` is the sole support for zero exemptions.** All 68 are
already granted by the main regex. It contributes no coverage at all and only
adds surface.

It is present in 12 of the 68 windows. Classifying every one `[test]`:

| shouted `NOT` text | role | count |
|---|---|---|
| "*** 2026-09-21 … THE PANEL HOLE IS **NOT** 6.0mm ***" | a real correction | 2 |
| "**VALUES NOT SET**" — inside the forbidden pattern itself | neither (D3-4) | 2 |
| "the … feed must **NOT** share a diode" | a live design rule | 6 |
| "are deliberately **NOT** restated here" | meta-prose about rule 1 | 2 |

So **2 of 12 are corrections**, and the brief's hypothetical is in the corpus
verbatim: `[repo]` `hardware/bom.csv`:63 — "**DO NOT CUT THE PANEL HOLE** UNTIL
THE PART NUMBER IS CHOSEN — 6.00 and 6.35 need different holes" — where the
match `6.00 and 6.35 need different holes` has `DO NOT` 57 characters before it.
That exemption survives only because the genuine correction is also 34
characters after it.

Corpus-wide `[test]`: **218** shouted `NOT` occurrences across the scanned
files, of which the recurring idioms are gaps and emphasis, not corrections —
13 × `NOT-IN-DOCUMENT` (the corpus's marker for "the datasheet does not say",
i.e. the *opposite* of a correction; `\bNOT\b` matches it because `-` is a
non-word character), 13 × `DO NOT`, plus "Physical positions are NOT",
"NOT a fingering input", "NOT all available", "SEEDED, NOT VERIFIED",
"NOT BINDING HERE", "R_ISO IS SET BY Zo, NOT BY C_L", "74HC165, NOT LVC".
Those 218 occurrences alone make **10.2 %** of the corpus text unfalsifiable at
the shipped window.

**Verdict:** `REFUTATION_SHOUT` is pure downside as written. It buys nothing
measurable and mortgages a tenth of the corpus. If the shouted form is worth
keeping it should be anchored to a correction, e.g. requiring a preceding date
or `IS NOT`/`WAS NOT`/`, NOT ` rather than a bare `\bNOT\b`.

---

## 4. The dated marker — 6 of 68 rest on it alone, and 4 of those 6 are the bad ones

`[test]` Removing `\d{4}-\d{2}-\d{2}` from `REFUTATION`, changing nothing else:

```
date REMOVED (w=300)   live=  6   exempt= 62
    LIVE  hardware/bom.csv:30                                [chain-connectors] 'five connectors must match'
    LIVE  hardware/carrier/bom.csv:6                         [chain-connectors] 'five connectors must match'
    LIVE  hardware/bom.csv:71                                [loadswitch-timer] '2.4x the ~62ms'
    LIVE  hardware/module/umbilical-load-switch/bom.csv:10   [loadswitch-timer] '2.4x the ~62ms'
    LIVE  hardware/bom.csv:71                                [loadswitch-timer] 'the reviewers disagree…'
    LIVE  hardware/module/umbilical-load-switch/bom.csv:10   [loadswitch-timer] 'the reviewers disagree…'
```

The dated marker is the sole support for exactly six exemptions, and **all six
are D3-1 and D3-3** — the two findings above. Every one of the other 33
exemptions in whose window a date appears is also carried by a word that means a
correction was made.

The marker's own comment claims it matches "the dated correction marker this
corpus writes by hand — `2026-09-21: 8HP -> 10HP`". It does not: it matches
`\d{4}-\d{2}-\d{2}` anywhere, and this corpus writes dates constantly for things
that are not corrections — `DECIDED 2026-09-21:` (a decision), `2026-09-21:
SHROUD HEIGHT ESTABLISHED` (new information), `rev E 08/05/13` style datasheet
provenance, and every `Resolved 2026-09-21 from the Internet Archive's
2019-02-02 capture`. `[test]` 778 date occurrences in the scanned corpus, alone
making **22.3 %** of it unfalsifiable at w=300.

**This is the single marker that did the damage.** It was added in the same
commit that dropped ten words for being too loose, and it is looser than any
word that was dropped — a bare four-digit-dash-two-dash-two, with no requirement
that anything near it be a correction.

The arrow, for completeness: `[test]` present in 2 windows, sole support for 0.
Both are `power-entry.md`'s signal-flow prose, "120 mV → LM317 line regulation →
62 µV on AVDD → OPA2197 PSRR", which corrects nothing; those two exemptions are
legitimate on a `used to` 38–44 characters away. 269 arrow occurrences corpus-wide,
6.9 % surface. Harmless today, but it is the same shape of mistake as the date:
`->` is arithmetic, a table cell and an ASCII drawing, not a correction.

---

## 5. What the narrowing lost — the corpus's own house style for a correction no longer qualifies

`[test]` Among the 68 current matches, **nothing was lost**: 0 matches are
exempt under the pre-`0e68f25` vocabulary and live now. The narrowing broke no
existing exemption.

That is not the question that matters. The risk is prospective, and it is real.

`[repo]` The dominant way this corpus writes a refutation paragraph in an ADR is
**"An earlier revision …"**, and `earlier` was one of the ten dropped words:

> `docs/decisions/0003-breath-sensing-path.md`:262 —
> **An earlier revision** called it a **Helmholtz resonator** at ~320 Hz and
> prescribed a trap volume to place it. A Helmholtz model requires the neck
> volume to be small against the cavity …

> `docs/decisions/0003-breath-sensing-path.md`:228 —
> **An earlier revision** put the sensor at the top on a 30 mm tube, reasoning
> that *"the SPI bus already runs the full length of the body …"* **That is
> wrong.**

> `docs/decisions/0013-two-mcu-split.md`:65 —
> **An earlier version** of this table showed 14 pins and one shared host, and
> **was wrong**.

> `docs/decisions/0009-enclosure-construction.md`:145 —
> Two earlier justifications in this ADR turned out not to hold … because they
> **were wrong** in the same direction.

`[test]` Counting the house-style openers (`an earlier revision|version|draft`,
`The earlier worry|reasoning|…`, `the old model|text|code|figure|…`) across the
scanned corpus:

```
house-style refutation openers:                                     60
of those, with NO surviving REFUTATION marker within 300 chars:     41
```

41 genuine refutation blocks, spread over 15 files (8 in ADR 0003, 5 each in
0007 and 0009, 4 in 0005, 3 each in 0006, 0013 and `breath-receive-stage.md`),
are now invisible to the exemption. They report nothing today only because no
`forbidden` pattern happens to sit inside one.

**And CLAUDE.md §2 step 2 walks straight into them.** It says: grep for the old
value first, and add one `forbidden` pattern per spelling you find. The
spellings you find are, in large part, the old values quoted inside these
refutation blocks — "~320 Hz", "14 pins and one shared host", "a 30 mm tube".
Add a pattern for one of those and the checker reports a correctly-refuted
sentence as a stale value. `CLAUDE.md` names what happens next: "A pattern that
fires on a correct sentence is worse than no pattern, because its cheapest fix
is to make the sentence wrong."

Dropping `was`, `wrong`, `old`, `instead of` and `rather than` was right — they
are ordinary prose here (`[test]` 380 correction-shaped uses of the dropped
words with no surviving marker, most of them plain `instead of` / `rather
than`). Dropping **`earlier`** was not: `an earlier revision` / `an earlier
version` is a fixed phrase in this corpus that means precisely "a correction
follows". It should come back as the bigram, not the bare word.

---

## 6. The window — 300 does not bite anywhere, and the data supports about 200

### It bites nothing today

`[test]` Comparing the shipped 300-character window against judging the whole
line and against judging the whole file:

```
exempt @ w=300        : 68
exempt @ w=whole file : 68      <- the window excludes NOTHING
exempt @ whole line   : 64
```

The window does not remove a single exemption that unbounded matching would
grant. Every marker that exempts anything today is already within 300
characters. The 300 was "chosen by measurement", and on this corpus it measures
identically to no window at all.

### For prose it is not a narrowing at all — it is a widening

The pre-`0e68f25` code judged `" ".join(lines[first-1:last])` — the source lines
the match physically touches. The corpus is hard-wrapped at ~78 columns, so for
a Markdown page that context was about **78 characters**; the window gives it
**600**. `[test]` That is where the 68-vs-64 difference comes from: exactly 4
exemptions have their nearest marker on a *different source line* from the
match, and all 4 are legitimate corrections written on the line above —
`0004-cv-interface-module.md`:78, `0006-cv-channel-allocation.md`:722,
`power-entry.md`:102 (×2). Whole-line judgement was wrongly rejecting those.

So the change does two opposite things at once and only one of them was
described: it narrows judgement inside a 2,800-character BOM row, and it widens
it roughly 8× inside a hard-wrapped Markdown page. The widening is the part that
is working; the narrowing is the part that measures as a no-op.

### Where the window would have to sit to bite

`[test]` Sweeping the window with the shipped vocabulary:

| window | exempt | live | what goes live |
|---|---|---|---|
| 300 (shipped) | 68 | 0 | — |
| 250 | 66 | 2 | `2.4x the ~62ms` ×2 |
| **200** | **64** | **4** | + `five connectors must match` ×2 |
| 160 | 60 | 8 | + `FB-IN` ferrite premise ×2 (**legitimate**), `-9.6V` ×2 (**legitimate**) |
| 100 | 58 | 10 | + `the reviewers disagree…` ×2 |
| 50 | 47 | 21 | — |

`[test]` The largest distance at which a **legitimate** correction sits is
**165** (`inamp-full-scale` `-9.6V`, exempted by "until 2026-09-21"), then 152
(`FB-IN`'s refutation banner). The smallest bad distance is **222** (`WIRE-LOOM`).

**So the data supports a window anywhere in [166, 221].** 200 is the round
number in that band. At 200 the checker loses no legitimate exemption at all and
reports D3-1 and half of D3-3 — which is the entire point of having a window.
300 is outside the band, and is therefore strictly worse than 200 on this
corpus: the four extra exemptions it buys are the four this slice is reporting
as defects.

This should be stated as a fact the next change has to preserve, not as a
constant with a comment: **the window's job is to be smaller than the distance
from a live claim to the nearest unrelated marker, and larger than the distance
from a correction to the thing it corrects.** On this corpus those are 222 and
165, and there are 57 characters of room between them.

### What the window cannot fix

`the reviewers disagree and the datasheet decides` is exempted at **109** — well
inside any window that keeps the legitimate exemptions. `0e68f25`'s own comment
predicted this shape for `WIRE-LOOM`: "closer to the claim than any tightening
could exclude." No window value fixes D3-3's second half. Only editing the row
does.

### The surface, which is the number I would put in the report line

`[test]` Share of the corpus's joined-stream text lying within one window of
*any* marker — i.e. where a `forbidden` pattern could never fire no matter what
it said:

| halo | unfalsifiable share of the corpus |
|---|---|
| 50 | 15.3 % |
| 100 | 24.1 % |
| 160 | 32.9 % |
| 200 | 37.9 % |
| **300 (shipped)** | **47.9 %** |
| 600 | 67.3 % |

By marker class at w=300, each alone: words 27.8 %, dates 22.3 %, shouted `NOT`
10.2 %, arrows 6.9 %.

**Nearly half the design corpus is currently a place where the staleness check
cannot report anything.** And it is not a random half — `[test]` the files that
are 85–100 % unfalsifiable are every `notes.md` (`link-supervision`,
`panel-led`, `key-register`, `led-strip-drive`, `digital-and-supervision`,
`umbilical-load-switch`, `key-marker-and-bits`, `breath-receive-stage`,
`key-chain-loom`) and the history-rich BOM fragments (`spi-link` 85.3 %,
`breath-response-shaper` 93.1 %, `breath-output-stage` 91.0 %, `panel` 100 %).
Those are precisely the files whose job is to record what a circuit *used to be*,
which is to say precisely where stale values accumulate. The exemption is
densest exactly where the defect lives.

The `PASS` line reports `218 patterns` as its coverage figure. It is not
coverage. Half of it lands on ground where nothing can be reported.

---

## 7. Two smaller things, for completeness

**The reported context does not have to contain the reason.** `[repo]`
`check_figures()`:221–231 computes `ctx` from the touched source lines and
`near` from a ±300 window, judges on `near`, and reports `ctx.strip()[:100]`.
For a match exempted by a marker four lines away, `--verbose` prints 100
characters that do not include the marker — so a reader auditing the exemption
list by eye cannot see what granted the exemption. Every finding in §2 above
required a harness rather than the tool's own output.

**A CSV window reaches into the neighbouring row.** The stream is the whole file
joined with single spaces, so nothing stops a window crossing a row boundary.
`[test]` synthetic, three-line CSV:

```
row 2: R-A,"The 220 ohm value here is superseded; it is 100 ohm now."
row 3: R-B,"This part is 220 ohm and nobody has ever questioned it."

match on source line 3 | exempt? True | marker: 'superseded' (source line 2)
```

`[test]` No current exemption crosses a CSV row boundary — the 4 cross-line
cases are all hard-wrapped Markdown, which is the intended behaviour. But
`hardware/bom.csv` is generated by sorting fragments, so the neighbour of any
row is not stable across a `merge-bom.py` run. Two rows that were never meant to
be read together can become adjacent, and one row's refutation then silences the
next row's live value, with no edit to either. That is the same class as the
trap `CLAUDE.md` §4 describes for generated files: a state that appears and
disappears without a word.

---

## 8. Summary of claims

| id | claim | confidence |
|---|---|---|
| D3-0 | 68 of 68 forbidden-pattern matches are exempted; the stale-value check reports nothing on this corpus | certain `[test]` |
| D3-1 | `WIRE-LOOM`'s "five connectors must match" is live and false against `chain-connectors` = 8, exempted by a date 222 chars away; it is the escape `0e68f25`'s message says it closed | certain `[repo]`+`[test]` |
| D3-2 | `D-REVPOL`'s "modulates its Vf by ~80mV" is a live stale value; the nearby correction is about the cents | high — depends on whether a `\|`-appended dated segment strikes the text above it |
| D3-3 | `C-TIMER-LOADSW`'s `2.4x the ~62ms` and `the reviewers disagree…` stand un-struck; the register records the first as retired | medium-high, same dependency |
| D3-4 | 3 of 218 patterns self-exempt and can never fire; `check_patterns()` does not catch them | certain `[test]` |
| D3-5 | `REFUTATION_SHOUT` is the sole support for 0 exemptions; 2 of its 12 appearances are corrections | certain `[test]` |
| D3-6 | The dated marker is sole support for 6 exemptions, and all 6 are D3-1 and D3-3 | certain `[test]` |
| D3-7 | 41 house-style "An earlier revision…" refutation blocks no longer qualify; adding a pattern per CLAUDE.md §2 near one will report a true sentence | certain `[test]` for the count; the consequence is prospective |
| D3-8 | The 300-char window excludes nothing; 200 excludes the defects and costs nothing; legitimate max is 165, bad min is 222 | certain `[test]` |
| D3-9 | 47.9 % of the corpus is unfalsifiable at w=300, concentrated in `notes.md` and BOM fragments | certain `[test]` |

Reproduction: `git archive HEAD | tar -x` into a scratchpad, then a harness that
re-implements `check_figures()`'s loop and varies `REFUTATION`,
`REFUTATION_SHOUT` and `REFUTATION_WINDOW` one at a time. Every number above
came from that harness or from `git show`/`grep` on the working tree; nothing is
from memory.
