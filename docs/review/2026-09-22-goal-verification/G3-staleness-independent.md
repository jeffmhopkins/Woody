# G3 — Staleness, decided independently of the checker

**Slice:** G3, cold. **Brief:** decide for myself whether the design corpus is
self-consistent, without using `tools/check-staleness.py`'s verdict as
evidence.

**Revision measured:** the corpus at `a4b80b1`. I verified this is also the
corpus at `HEAD` (`25cc740`): `[test] git diff --stat a4b80b1 HEAD` → one file
changed, `docs/review/2026-09-22-goal-verification/README.md`, +81 lines. No
corpus file differs, so every finding below reproduces at either revision.
`tools/` is **not** pinned by me and I did not modify it.

**Cold compliance:** I read nothing under `docs/review/`, `docs/log/` or
`docs/research/`. I did not open the wave README that `c46487d` added. I did
read `tools/check-staleness.py` (to learn *what it cannot see*, not to take its
verdict) and, at the end, `.staleness/report.txt` — but only after deriving my
own untracked-quantity list, and only to report where we differ. Every
value-level finding below comes from my own greps.

**Method.** I built a normalising scanner
(`scratchpad/norm.py`) that folds the whole corpus into one
stream per file with: all whitespace removed, U+2010–U+2015/U+2212/U+FF0D
normalised to ASCII `-`, `×` → `x`, `·` → `*`, and backticks, asterisks, pipes
and underscores dropped, with an index back to the original line. So `97mm`,
`97 mm`, `**97 mm**` and `| 97 mm |` are one query, and `-9.6V` and `−9.6 V`
are one query. That is the class of escape this repository keeps paying for,
and it is the class a literal case-sensitive `find()` cannot cover.

On top of that I extracted every *number + unit* token in the corpus and
grouped by file spread, to derive the untracked-shared-quantity list from the
tree rather than from anyone's register.

**Verdict, stated plainly: the corpus is NOT self-consistent.** I find
**thirteen live contradictions** (class a), of which four are the repository's
named failure shape — a header or a table was corrected and the numbers
computed under it were not. The checker reports `PASS` against all thirteen,
correctly by its own rules: none of the thirteen is a spelling of anything in
a `forbidden` list.

Findings are numbered `G3-n`. Class is marked **(a)** live contradiction,
**(b)** restated-not-cited, **(c)** untracked shared quantity.

---

## Class (a) — genuinely contradictory values, live in the corpus now

### G3-1 **(a) `docs/decisions/0004-cv-interface-module.md:282,286–287` — the table header was corrected to 359 mA and both of its values are still computed at 290 mA.**

`[repo] docs/decisions/0004-cv-interface-module.md:281-287`:

```
it **rules out the series-resistor variant**, which is harmless at 50 mA and is
not at 290 mA:

| Series R | Drop at 359 mA |
|---|---|
| 2.2 Ω | 0.64 V |
| 10 Ω | 2.90 V |
```

`[calc]` at the header's own current: `2.2 × 0.359 = 0.790 V`, not 0.64;
`10 × 0.359 = 3.59 V`, not 2.90.
`[calc]` at 290 mA: `2.2 × 0.290 = 0.638 ≈ 0.64 V`; `10 × 0.290 = 2.90 V`. Exact.

So the header moved to the tracked `umbilical-current` (359 mA) and the two
derived cells did not, and the prose sentence immediately above the table still
carries the retired 290 mA as a live claim. This is the *identical* shape the
register already records for `sensor-full-scale` and it is sitting two lines
apart. The register has a `forbidden` pattern `"Drop at 290 mA"` for
`umbilical-current` — which is the one spelling that is **not** here, because
that phrase is exactly what got fixed. Node: `FB-IN` / module +12 V entry.

### G3-2 **(a) The module's own +12 V total is 404 mA in the ADR and 392 mA in the hardware pages, the BOM and `figures.yaml`'s own derivation.**

- `[repo] docs/decisions/0004-cv-interface-module.md:276` — “**~404 mA
  typical** (45 mA module incl. the DAC regulator + **359 mA** instrument)”.
- `[repo] hardware/module/power-entry/power-entry.md:116` — “`r_d` is
  69 mΩ at **392 mA**”.
- `[repo] hardware/module/power-entry/bom.csv:8` (`FB-IN`) and its generated
  copy `hardware/bom.csv:61` — “31.4 mV at the **392 mA** module total”.
- `[repo] config/figures.yaml`, `ferrite-bias-impedance` derivation — “the
  module +12V total of **392 mA** gives ~245-275”.

`[calc]` `404 − 359 = 45 mA` of module-local draw; `392 − 359 = 33 mA`. Two
different numbers for the module's own +12 V consumption, feeding two tracked
figures (`diode-split-rationale` cites 392 mA in its value string;
`ferrite-bias-impedance` derives its FB2 interpolation from it). Whichever is
right, one of `diode-split-rationale`'s and `ferrite-bias-impedance`'s inputs
is wrong. Node: `FB-IN` / `D-REVPOL` / `U-REG-DAC`.

### G3-3 **(a) `docs/reference/latency-budget.md:49` — “632 µs” is the sum of the *superseded* 531 Hz pole and the current 480 Hz pole, printed three lines under the table that refutes 531 Hz.**

`[repo] latency-budget.md:42-43` states the two poles as **482 Hz → 330 µs**
(explicitly “**Not 531 Hz**”) and **480 Hz → 332 µs**.
`[repo] latency-budget.md:49` then says “The real figure is **632 µs**”.

`[calc]` `1/(2π×482) = 330.2 µs`; `1/(2π×480) = 331.6 µs`; sum = **661.8 µs**.
`[calc]` with the refuted pole: `1/(2π×531) = 299.7 µs`; `299.7 + 331.6 =`
**631.3 µs ≈ 632**.

So the paragraph that announces the correction is itself computed from the
value it corrects — “a fix whose own explanation restates the wrong value”.
The conclusion (“three times what was written”) survives either way
(`632/200 = 3.2`, `662/200 = 3.3`), which is why nobody noticed.

### G3-4 **(a) `docs/reference/latency-budget.md:133` — “the 125 µs the key network's RC contributes” against a tracked `key-release-time` of 119.9 µs.**

`[repo]` the sentence reads: “the release window has to outlast the bounce
burst rather than the **125 µs** the key network's RC contributes”. It
attributes 125 µs to the RC by name, so it is not the 125 µs mean sampling
period that appears at `:59`, `:97`, `:177` and `:199`.

`key-release-time` = **119.9 µs** (owner
`hardware/cluster/key-switch-network/key-switch-network.md:105`), and its
`forbidden` list already carries `"at ~125us"` and `"~125us"`. `[repo]
cat -A` shows this line spells it `125 M-BM-5s` — a space and `µ`, no tilde.
**The patterns miss by one space and one character**, which is the escape mode
`sensor-full-scale`'s `escape_note` was written to prevent. Node:
`R-KEY-PU` / `C-KEY`.

### G3-5 **(a) The OPA2197 half count: “TWO SPARE” in two places, “there is still one” in a third, and `U-RESP` is a *separate* package that claims to consume spares belonging to six others.**

- `[repo] hardware/bom.csv:80` (`U-OPA-PITCH`, qty **6**): “Six packages,
  twelve halves, TEN used: pitch, mod 1-4, mod offset follower, VREFOUT
  follower, breath REF-zero buffer, breath gain buffer, breath summer. **TWO
  SPARE** - and U-RESP claims both of them if it is fitted”. `[calc]` the
  named list is `1 + 4 + 1 + 1 + 1 + 1 + 1 = 10` ✓ internally consistent.
- `[repo] hardware/module/breath-output-stage/breath-output-stage.md:157` —
  “Ten of twelve halves used across the module, **two spare**.”
- `[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:171-172`
  — “It costs the last spare OPA2197 half, and `U-OPA-PITCH` goes to six
  packages so **there is still one**.” The half it is spending (“breath
  REF-zero buffer”) is *already inside* the BOM's list of ten, so this page
  reaches 11 used / 1 spare where the other two reach 10 / 2.

Separately, and worse: `U-RESP` is its own BOM row, qty **1**, a seventh
OPA2197IDR package `[repo] hardware/bom.csv:93`. Its note says “**THIS PACKAGE
CONSUMES BOTH OF THE MODULE'S REMAINING SPARE OPA2197 HALVES**”. A seventh
package cannot consume halves of the first six — it adds two. Either
`U-OPA-PITCH` should drop to qty 5 when `U-RESP` is fitted (and the “twelve
halves” arithmetic then describes 5+1 packages), or the module has 14 halves
and “no spare op-amp capacity left” is false. As the BOM stands,
`merge-bom.py` totals 7 dual packages for a design that says it has 6.
Node: `U-OPA-PITCH` / `U-RESP` / `U-BUF`.

### G3-6 **(a) The DAC internal-reference pitch error is 0.42 cents on the owner page and 0.54 cents in ADR 0006, and the owner page quotes the ADR's figure and asserts it “survives”.**

- `[repo] hardware/module/pitch-stage/pitch-stage.md:286` — “| **DAC internal
  reference** | **0.42 cents** | **The largest term, and untrimmable** |”.
- `[repo] docs/decisions/0006-cv-channel-allocation.md:395` — “**The DAC's
  internal reference is sufficient.** At **0.54 cents** over 10 °C it is …”.
- `[repo] hardware/module/pitch-stage/pitch-stage.md:119-121` — “*(This is also
  why the ADR's “the DAC's internal reference is sufficient, at **0.54 cents**
  over 10 °C” survives: that figure is a gain term.)*”

29 % apart on the term both documents call the largest in the budget, 167 lines
apart in the same file, and the owner page reproduces the other number without
reconciling it. `hardware/module/pitch-stage/notes.md:54` already says “the DAC
internal reference is **0.42 cents**, not `~0.5`. Neither figure is tracked” —
so this was seen once and the ADR was never reached. Node: `U-DAC` /
`R-PRECISION`.

### G3-7 **(a) `docs/reference/repo-maintenance.md:204` — “`hardware/unplaced.csv` holds the 50 rows of 138”. It holds 32 rows of 140.**

`[test] python3 -c "import csv; print(len(list(csv.reader(open('hardware/unplaced.csv')))) - 1)"` → **32**.
`[test] python3 tools/merge-bom.py --check` → `bom.csv: checked 140 rows from
26 fragments | 0 problems`.

Both numbers in the sentence are stale, in the document CLAUDE.md names as the
place to read before touching `bom.csv`. The two example clusters given with it
— “six identical jack-protection networks drawn three times, and nineteen
decoupling capacitors with no home” — are also gone: `[repo]` the current
`hardware/unplaced.csv` contains no jack-protection rows and no decoupling
capacitors at all (its 32 rows are keycaps, IMU, display, LED reel, cable,
mechanical and the two board blanks).

### G3-8 **(a) `docs/reference/pcb-pipeline.md:151-166` — a table headed “Re-measured against the current tree, 2026-09-21” whose six numbers are all wrong, and a worked example whose row has moved.**

Stated `[repo] pcb-pipeline.md:153-155`:

| | Rows | Units |
|---|---|---|
| `hardware/bom.csv`, the generated master | 138 | 388 |
| In the 23 per-circuit fragments | 104 | 313 |
| **In `hardware/unplaced.csv`** | **34** | **75** |

Measured `[test]` by summing the `qty` column:
master **140 / 391**; `unplaced.csv` **32 / 67**; so everything else is
**108 / 324**. Also “the 23 per-circuit fragments” is wrong as a count of
fragments: `[repo]` 23 directories carry a `circuit.yaml`, but
`hardware/module/link-supervision/` has **no** `bom.csv`, so there are 22
circuit fragments plus 3 board-level ones plus `unplaced.csv` — which is the
26 that `merge-bom.py --check` names.

The worked example under it has decayed too. `[repo] pcb-pipeline.md:158-160`
lists five module-netlist rows still in `unplaced.csv`: `J-CV ×6`,
`U-TVS-MODULE`, `D-CLAMP-BREATH ×2`, `R-BREATH-SUM ×2`, `R-BREATH-OFF ×2`,
“**Thirteen units**”. `[repo]` of those, only `U-TVS-MODULE`, `R-BREATH-SUM`
and `R-BREATH-OFF` remain (**3 rows, 5 units**); `J-CV` is gone and
`D-CLAMP-BREATH` now lives at
`hardware/module/breath-receive-stage/bom.csv:7`. The paragraph at `:163-170`
that uses `D-CLAMP-BREATH` as “the shape of the problem” asserts “**its row is
still in `unplaced.csv`**”, which is false. This is the same section that ends
by narrating its own earlier correction, so the fix landed once and was not
re-run.

### G3-9 **(a) `hardware/carrier/breath-adc/breath-adc.md:52` — the ADC clamp-current worst case is still computed from the retired 4.7 V sensor full scale.**

```
worst case, 3V3 at 0 and the clamp holding the pin at ~0.7 V:
  (4.7 − 0.7) / 10 kΩ = 400 µA   against a family-typical ±2 mA  [from memory]
```

`sensor-full-scale` is **4.86 V**, and this page cites it correctly ten lines
above (`:38`, `:42`). `[calc] (4.86 − 0.7)/10 kΩ = 416 µA`, not 400 µA. 4.7 V
is not the op-amp's limit either: `[repo] hardware/carrier/carrier.md:117` the
breath buffer is “`(V+ = +12V)`”, so nothing clips it below the sensor's own
full scale. 4.7 V is the retired figure, and it is the one spelling of it left
in the corpus that is a *positive sensor-output* claim — the other bare 4.7 V
hits are the in-amp's −4.7 V at a realistic blow and ADR 0005's 5 V-umbilical
arrival voltage, both legitimately different quantities. `sensor-full-scale`
has 34 `forbidden` patterns and none matches a bare parenthesised `(4.7 −`.
Node: `R-ADCDIV` / `U-ADC`.

### G3-10 **(a) `hardware/unplaced.csv:19` / `hardware/bom.csv:127` (`PCB-MODULE`) — a live 8HP derivation inside a `.csv`, where rule 2b allows no refutation exemption.**

`[repo]` the note reads: “10HP, via 8HP, not 6HP: the D24.0mm bore leaves
**8.17mm of panel each side at 40.34mm** (ADR 0004; this said 23.8mm/8.27mm
until the vendor drawing landed) | 2026-09-21: 8HP -> 10HP, so the board widens
~35mm to ~45mm.”

`[calc] (40.34 − 24.0)/2 = 8.17 mm` — correct arithmetic for the *retired*
panel width. `[calc] (50.50 − 24.0)/2 = 13.25 mm` is the live figure, and
`[repo] docs/decisions/0004-cv-interface-module.md:695` tables exactly that,
with the 8.17 mm row italicised as “*(at 8HP)*”. So the ADR handles it
correctly and the BOM cell states the 8HP number as the live one, with the
correction appended after a `|` further along the cell. CLAUDE.md §2b:
“In a `.csv` or a `.yaml` a forbidden value is a defect, full stop.” This cell
is also a log of what the row used to say, which §2b's cut line sends to git.
Two file copies, one edit site (`unplaced.csv`). Node: `PCB-MODULE` /
`J-UMBILICAL`.

### G3-11 **(a) The playable breath span is 1598 counts on one page and ~1594 on three others.**

- `[repo] hardware/carrier/breath-adc/breath-adc.md:43` — “playable span above
  rest ≈ **1598** counts of 4096”. `[calc]` from its own rows: `1795 − 197 =
  1598` ✓.
- `[repo] hardware/carrier/carrier.md:177-178` and `:373`, and
  `hardware/interfaces/key-chain-loom/key-chain-loom.md:129` — “~**1594**-count
  playable span”, used three times to size the 3.2 LSB reference shift.

Untracked on both sides, so nothing can catch it. The downstream conclusion
(0.2 %) is unchanged, which is why it has survived.

### G3-12 **(a) `hardware/module/power-entry/bom.csv:8` / `hardware/bom.csv:61` (`FB-IN`) — a number has been deleted from the branch list, leaving a bare unit.**

`[repo]` “PER BRANCH: **FB4 (+5V, mA)**, FB3 (-12V, 10-20mA) and FB1 (+12V
analog, ~45mA) all sit on the flat part”. The +5 V branch current is missing —
the cell reads `(+5V, mA)`. ADR 0005 puts that branch at ~10 mA
`[repo] docs/decisions/0005-power-architecture.md:122`. Two file copies, one
edit site.

### G3-13 **(a) `hardware/carrier/breath-adc/breath-adc.md:38` — the count does not follow from the voltage printed on the same line.**

```
full scale = 4.86 V × 0.6 = 2.92 V  against VREF 3.3 V → 88 % of range, 3622 counts
```

`[calc] 4.86 × 0.6 = 2.916; 2.916/3.3 × 4096 = 3619.4` → 3619, not 3622.
`[calc]` with the unrounded 4.864: `4.864 × 0.6 / 3.3 × 4096 = 3622.4` → 3622.
So the line prints 4.86 and computes 4.864. The other three rows of the same
block reproduce exactly (`197`, `1795`, `1598` — all verified `[calc]`), which
makes this one the odd row rather than a rounding convention. Three LSB, but it
is the only row in the block that cannot be re-derived from what it shows.

### G3-14 **(a) `docs/decisions/0004-cv-interface-module.md:530-533` still reasons from a `CLR` that fires, and `hardware/module/breath-receive-stage/breath-receive-stage.md:231-233` says the jacks hold their last value indefinitely.**

`[repo] 0004:530-533`: “on a sagging cable the buck drops out at 8 V while the
REF5050 and OPA2197 hold regulation to ~7.2 V, so the MCU dies, SPI stops,
**`CLR` fires**, and breath keeps working.”

`[repo] breath-receive-stage.md:231-233`: “the same pull leaves pitch and the
four mod jacks **holding their last value indefinitely**, which is the accepted
cost of **deleting the watchdog**.”

ADR 0004 contradicts *itself* as well: its own withdrawal banner at `:491-500`
says “**pull the umbilical mid-note and the rack holds the note until the
module's toggle is flipped**”, 33 lines above the paragraph that says `CLR`
fires. The banner's closing sentence — “The paragraphs below are kept because
the problem they describe is still real” — is what let the mechanism claims
below it stay un-struck. `hardware/module/mod-channels/mod-channels.md:160-168`
and `firmware/README.md:70-73` both took this correction; ADR 0004 did not.
This is CLAUDE.md §5's case (“an argument survives its own refutation”) still
live, in a different document from the one §5 names. Node: `R-CLR-PU` /
`U-WATCHDOG` (deleted).

### G3-15 **(a) `hardware/interfaces/key-chain-loom/key-chain-loom.md:134,143` — two “see *Still open*” pointers to a section that does not exist, and the open question they point at was settled.**

`[test] grep -n "Still open" hardware/interfaces/key-chain-loom/key-chain-loom.md`
→ only the two *references* (`:134`, `:143`); there is no `## Still open`
heading in the file. The question they defer is `[repo] :141-143`: “**Six
conductors is the signal count, not the conductor count.** Whether this
connector is 6-way or 10-way is a decision this page cannot take alone”. But
`chain-conductors` is **settled at 12 on a 2×6 IDC**, and this same page's own
interfaces table (`:30-36`) allocates all twelve pins. Neither 6-way nor 10-way
is the answer, and the page states the answer forty lines earlier. Node:
`J-CHAIN` / `WIRE-LOOM`.

### G3-16 **(a) `hardware/unplaced.csv:17` (`CABLE-UMB`) — two of its three line-number citations no longer point at what they name.**

`[repo]` the note says: “0005:91 computes a ~0.34 ohm round trip,
breath-sense-link.md:100 a 0.168 ohm return term, and 0003:315 a whole
signal-drop table”.

`[test] sed -n` checks: the 0.34 Ω statement is at
`docs/decisions/0005-power-architecture.md:**92**`; the 0.168 Ω term is at
`hardware/interfaces/breath-sense-link/breath-sense-link.md:**112**` (line 100
is an unrelated sentence about the analog star point); `0003:315` is correct.
This matters more than usual because the same cell says the three derivations
are the *reason* the gauge decision is blocked — the pointer is the whole
content of the finding. Node: `CABLE-UMB`.

### G3-17 **(a) `key-pullup-qty`'s owner document never states the value.**

`config/figures.yaml` gives `key-pullup-qty: "24"`, owner
`hardware/cluster/key-switch-network/key-switch-network.md`.
`[test] grep -n "24" hardware/cluster/key-switch-network/key-switch-network.md`
→ no match anywhere in the file. The page cites `key-pullup-qty` in its
interfaces table (`:20`) but the number 24 lives only in the `qty` column of
`R-KEY-PU`'s BOM row. Rule 1 says the owner states it and everyone else cites
it; here nobody states it in prose, so the register points at a document that
cannot be checked against it and the figure is unfalsifiable in the direction
that matters. (I later saw that `.staleness/report.txt` lists this among eight
owners it calls "UNCHECKED"; the stronger and checkable statement is that the
owner does not contain the value at all, which is a defect rather than a gap.)

### G3-18 **(a, minor) `docs/decisions/0005-power-architecture.md:157-162` — the load table is not reproducible from the conversion convention the same section states.**

Stated convention `[repo] :169-172`: “convert at the **arriving** voltage …
only ~11.4 V arrives; and the buck is **~90 % efficient**”.

`[calc]` applying it to each row (`5V_mA × 5 / (0.9 × 11.4) + 12V_mA`):
- Typical play: `226×5/10.26 + 248 = 358.1` → table says **359** (the tracked
  `umbilical-current`, whose own `derivation` string in `figures.yaml`
  likewise computes 358.1 and then declares 359).
- Quiescent: `180×5/10.26 + 123 = 210.7` → table says **212**.
- Typical + WiFi: `336×5/10.26 + 248 = 411.7` → table says **414**.
- Clamp-legal worst: `928×5/10.26 + 119 = 571.2` → table says **579** (1.4 %).
- Clamp fails: `1023×5/10.26 + 1023 = 1521.5` → table says **~1522** ✓.

Four of five rows are high by 1–8 mA, consistently, which is what a *lower*
arriving voltage per row would produce — but no row states its own arriving
voltage, so the table cannot be reproduced. The dependent claims all survive
(`[calc] (579−531)/531 = 9.0 %` ✓; `928/328 = 2.83` ≈ “a factor of three” ✓).
I report it because `umbilical-current` is a tracked figure whose stated
derivation returns a different number from its stated value.

### G3-19 **(a, minor) `docs/reference/latency-budget.md:65` — the digital breath total is ~0.2 ms above the sum of its own rows.**

`[calc]` from `:53-64`: base `2.17` + `0.282 + 0.024 + 0.020 + 0.096 + 0.010 +
0.082` = **2.684 ms** with the sampling period at 0, **2.934 ms** at 250 µs.
The Total row states “**~2.9–3.1 ms + restrictor**”. The analog table above it
*does* reproduce (`[calc] 1.17 + 1.00 + 0.330 + 0.332 = 2.832` ≈ “~2.83 ms” ✓),
and so does the key table (`[calc] 0.25+0.032+0.25+0.02+0.06+0.01 = 0.622` ✓,
best case 0.372 ✓). So this is one table out of three, and it is the one whose
poles G3-3 also touches.

### G3-20 **(a, register) `pitch-cents-budget`'s `candidates` list no longer corresponds to the owner page's table.**

`config/figures.yaml` lists four candidates: `0.42 cents`, `0.85 cents RSS`,
`1.35 cents linear sum`, `~1.2 cents RSS`. The owner page's live table
`[repo] hardware/module/pitch-stage/pitch-stage.md:285-288` has three rows:
0.42, 0.027, 0.068. `[calc]` linear sum `= 0.515`; RSS `= sqrt(0.42² + 0.027²
+ 0.068²) = 0.426`. Neither 0.85/1.35 nor ~1.2 is derivable from the current
table, so the dispute is recorded against numbers the corpus no longer
contains. A `disputed` entry whose candidates have gone stale cannot be closed
by reading the owner page, which is the only way it is ever going to close.

---

## Class (b) — a tracked value restated rather than cited: correct today, fragile tomorrow

This is where I differ most from the checker. Its `RESTATED, NOT CITED (211)`
advisory is, by its own definition, “a value written out in three or more files
**with no entry in the register**” — so it is silent about precisely the values
rule 1 exists to protect. Every item below is a **tracked** figure written out
in full somewhere other than its owner, and none of them appears in the 211.

### G3-21 **(b) `dac-rail` (5.21 V) is written out in 17 files.**

`[test]` normalised search for `5.21 V`/`5.21V` → 36 occurrences in **17
files**, including six ADRs (`0003:375,622`, `0004:151,178,209,310`,
`0005:126`, `0006:192,621,811`), `ROADMAP.md:47`, five hardware pages, four
BOM fragments and their generated master copies. The owner is
`hardware/module/power-entry/power-entry.md`. This is the most-restated tracked
figure in the corpus and the largest single staleness surface it has: a change
to `R-REG-SET` moves 36 strings across 17 files.

### G3-22 **(b) `key-scan-current`'s derivation is duplicated verbatim, not cited, in four files besides the owner.**

`[test]` `1.43 mA` appears in `hardware/cluster/key-switch-network/key-switch-network.md:108`
(owner), `docs/decisions/0001-mcu-and-board-partitioning.md:230`,
`hardware/carrier/carrier.md:172`,
`hardware/interfaces/key-chain-loom/key-chain-loom.md:118`, and the `F-CHAIN`
BOM note (`hardware/interfaces/key-chain-loom/bom.csv:5` + master). Three of
them reproduce the *whole* derivation line
`3.3 V / (2.2 kΩ + 100 Ω) = 1.43 mA per closed key` / `18 closed = 25.8 mA`,
character for character. `[calc]` both are right today:
`3.3/2300 = 1.4348 mA`; `18 × 1.4348 = 25.83 mA`.

### G3-23 **(b) `key-press-time` and `key-release-time` are restated with their full derivations in ADR 0001.**

`[repo] docs/decisions/0001-mcu-and-board-partitioning.md:227-228` duplicates
`hardware/cluster/key-switch-network/key-switch-network.md:105-106` exactly,
including τ, both thresholds and both crossings. `[calc]` verified:
τ_release `= 2200 × 47n = 103.4 µs`;
`t = −103.4·ln((3.3−2.31)/(3.3−0.1435)) = 119.88 µs` ✓.
τ_press `= (2200∥100) × 47n = 4.4957 µs`;
`t = −4.4957·ln((0.99−0.1435)/(3.3−0.1435)) = 5.917 µs` ✓.
`250/5.92 = 42.2` ✓ (“42× inside the 250 µs scan”). Correct — and two copies.

### G3-24 **(b) `sensor-full-scale` and `inamp-full-scale` are written out in four and three non-owner files respectively.**

`4.86` outside its owner (`0003`): `breath-adc.md:38,42`, `carrier.md:114`,
`breath-sense-link.md:160`, `breath-output-stage.md:42,50`.
`9.94` outside its owner (`breath-sense-link.md:165`):
`breath-output-stage.md:42,53,54`, `breath-receive-stage.md:133`,
`breath-response-shaper.md:54,107`, plus the `R-GAIN-INAMP` BOM note ×2 copies.
All currently agree. Given that this pair is the register's own worst recorded
case, nine spellings deep, the restatements are the live risk.

### G3-25 **(b) `breath-sensor-slope` is restated at a rounded value that no pattern can ever match.**

`[repo] hardware/carrier/breath-adc/breath-adc.md:40` —
`0.265 + 0.766 × 2.8 = 2.41 V`. The tracked value is **0.7665 V/kPa**. A search
for the tracked spelling finds this line in **zero** files; a search for
`0.766` finds it. If the slope moves, this derivation is invisible to any
pattern written from the owner document. Node: `R-ADCDIV` / `U-BREATH`.

### G3-26 **(b) `umbilical-current` (359 mA) is restated as “~360 mA” in five files.**

`[test]` `360 mA` → `docs/decisions/0004-cv-interface-module.md:627,633`,
`hardware/module/power-entry/power-entry.md:7,170`,
`hardware/module/umbilical-load-switch/umbilical-load-switch.md:57,62,222,330`,
plus the `U-BUCK`, `R-KEY-PU` and `Q-LOADSW` BOM notes. Two of these are not
approximations: `umbilical-load-switch.md:62` uses `360 mA` as a table entry and
`:222` feeds it into `[calc] 940 − 360 = 580 mA`. Not wrong today; a second
spelling of a tracked figure, at a different value, in a fifth of the corpus.

### G3-27 **(b) `panel-height-budget` is restated in full on `hardware/module/panel/panel.md:57-58` while naming the figure in the same sentence.**

“total is the tracked figure `panel-height-budget` — **110 mm of content
against 115.5 mm of clear panel**”. The citation is right there; the numbers
did not need to follow it.

### G3-28 **(b) Two `disputed` figures are used as settled, from pages that cite the disputed figure by name in the same file.**

- `breath-working-point` (DISPUTED; its `candidates` note says 2.8 kPa is
  “cited to ADR 0003, which does not contain it; the two schematic pages cite
  each other”). `[repo] hardware/carrier/breath-adc/breath-adc.md:40-41` uses
  **2.8 kPa** in a live derivation and annotates it
  `[2.8 kPa from breath-receive-stage.md]` — a third page joining the circular
  citation, while `:25` of the same file correctly cites
  `breath-working-point` in its interfaces table.
- `pitch-cents-budget` (DISPUTED). **0.42 cents** is used as a settled input at
  `hardware/module/power-entry/power-entry.md:134` (“error budget at 0.42
  cents”) and as a table row at `pitch-stage.md:286`, and it is the exact
  candidate the register warns “is a ROW of one table, not a total”.

---

## Class (c) — untracked quantities shared by three or more files

Derived from my own token census before reading the checker's advisory. I
agree with the checker on the raw spread for the items we both list (e.g.
`360 mA` 7 files, `265 mm` 11 files, `482 Hz`/`480 Hz` 6 files each). Where I
differ: the advisory excludes tracked values by construction, so class (b)
above is entirely invisible to it; and the advisory groups by literal spelling,
so it lists `480 Hz` and `482 Hz` as two independent quantities when they are
one filter pair whose difference is the substance of G3-3. The ones below are
the ones I would track first, chosen for *how many derivations depend on them*
rather than for raw file count.

### G3-29 **(c) The OPA2197's output swing on ±12 V is 11.9 V, 11.5 V and 11.45 V in different places, with no owner.**

`[test]` normalised search:
- `11.9 V` — `docs/decisions/0004-cv-interface-module.md:229` (“on ±12 V it
  reaches roughly 11.9 V”), `U-OPA-PITCH` BOM note ×2 copies (“~11.9V swing on
  +/-12V”).
- `11.5 V` — `docs/decisions/0005-power-architecture.md:48`,
  `hardware/module/breath-output-stage/breath-output-stage.md:164,170` (“the
  OPA2197 stops at about ±11.5 V”), `0004:290`.
- `11.45 V` — `docs/decisions/0006-cv-channel-allocation.md:137`,
  `firmware/README.md:63,74`, `hardware/module/mod-channels/mod-channels.md:182`,
  `hardware/module/mod-channels/notes.md:53`,
  `hardware/module/pitch-stage/pitch-stage.md:153`.

The 11.45 V sites all qualify it as “less two Schottky drops”, so they are
probably a different condition — but nothing says so at the 11.5 V sites, and
`breath-output-stage.md` uses ±11.5 V to decide a *clipping* headroom rule that
the mod pages solve at ±11.45 V. Three numbers, one part, nine files, no
register entry. This is the shape that produces a class-(a) finding in the next
wave.

### G3-30 **(c) The 4 kHz / 250 µs loop rate is in ~18 files and is not tracked.**

`[test]` `4 kHz` → 47 occurrences in **18 files**; `250 µs`/`250 us` → 10 more
files. `loop-budget` tracks the *consumption* (196–241 µs) but not the period,
so the period can move under the budget that is measured against it. Three
independent derivations depend on it directly: the sampling-period rows in both
latency tables, the note-on gate (`+250 µs`), and the 8 kHz rejection
(`[calc] 24 + 32 + 96 = 152 µs > 125 µs` ✓).

### G3-31 **(c) The module's own +12 V draw (the 45 mA / 33 mA of G3-2) is stated nowhere as a figure** — it exists only as the difference between two totals in two different documents. That is why G3-2 could happen at all.

### G3-32 **(c) The ADC chain constants — divider 0.600, VREF 3.3 V, 4096 counts, and the ~1594/1598-count playable span — are untracked and shared by four files.**
`hardware/carrier/breath-adc/breath-adc.md`, `hardware/carrier/carrier.md`,
`hardware/interfaces/key-chain-loom/key-chain-loom.md`,
`hardware/cluster/key-switch-network/key-switch-network.md`. G3-11 and G3-13
are both inside this cluster.

### G3-33 **(c) The umbilical cable's electrical model — 2 m, 24 AWG, 0.34 Ω round trip, 0.168 Ω return leg — is untracked, and the `CABLE-UMB` row says the gauge is OPEN.**

`[repo] hardware/unplaced.csv:17`: “*** GAUGE IS OPEN AND THREE DERIVATIONS
ASSUME 24 AWG. *** … A stranded Cat5e PATCH lead is commonly 26 or 28 AWG, at
1.6x to 2.6x the resistance.” The three dependants are
`docs/decisions/0005-power-architecture.md:92` (which feeds `umbilical-current`
and therefore `ferrite-bias-impedance` and the whole G3-18 table),
`hardware/interfaces/breath-sense-link/breath-sense-link.md:112`, and
`docs/decisions/0003-breath-sensing-path.md:315`. A tracked figure with
`status: blocked` and `decided_by: E6` would make that visible; today the only
place it is written down is a BOM cell for a part in `unplaced.csv`.

### G3-34 **(c) The pitch scale constant, 1 mV = 1.2 cents, is restated in four files** (`pitch-stage.md:111` ×2, `pitch-stage/notes.md:61`,
`pcb-pipeline.md:269`) and is the multiplier under every cents figure in the
corpus, including the disputed `pitch-cents-budget` and the 5.7–7.2 cents
ground-path findings. `[calc]` `1200 cents/V × 1 mV = 1.2 cents` ✓.

### G3-35 **(c) `265 mm`, the internal body run, appears in 11 files** and is the length term in the `F-CHAIN` argument, the display loom and the LED loom. Untracked.

---

## What I checked and found sound

Worth recording, because a report of thirteen contradictions should say where
it looked and found nothing.

- **`key-press-time`, `key-release-time`, `key-scan-current`, `key-pullup-qty`,
  `marker-bits`, `free-bits`, `chain-conductors`, `chain-connectors` all
  reconcile numerically.** `[calc]` 4 devices × 8 = 32 bits; 18 used + 14 spare
  ✓; 14 = 8 marker + 3 switches + 3 free ✓; per-cluster used `3+6+4+5 = 18` ✓
  and spare `5+2+4+3 = 14` ✓; 21 switch positions (18 fitted + 3 reserved) = the
  `R-KEY-SER` qty ✓; 21 + 3 free = 24 pull-ups = the `R-KEY-PU` qty ✓; the 2×6
  IDC allocates 4 signals + 5 grounds + 3V3 (pin 10) + 2 spares = 12 ✓;
  8 connectors = `1 + 2 + 2 + 2 + 1` ✓ and the loom page says “all eight
  positions” ✓. (G3-17 and G3-15 are about how those facts are *stated*, not
  about the facts.)
- **`panel-width`** `[calc] (10 × 5.08) − 0.3 = 50.50` ✓, and the three-pot
  knob ceiling `[calc] 3×14 + 2×3 = 48` inside 50.50 ✓.
- **`panel-height-budget`** `[calc] 5 + 22 + 39 + 31 + 13 = 110` ✓ against
  115.5, and the three screw-hardware cases (116.9 / 115.5 / 112.5) are each
  `128.5 − 2×(3.0 + r)` ✓.
- **`mod-reference`** `[calc]` non-inverting k=3 from 10k/30k: `4·V_dac −
  3×3.3333 = 4·V_dac − 10.000`, so 0–5 V maps to ∓10.000 V ✓; and
  `3.3333/2500 = 1.333 mA` ✓ matching `mod-channels.md:200`.
- **`spi-series-r`** `[calc] 3.3/68 = 48.5 mA` ✓ and `3.3/100 = 33 mA` ✓,
  matching `spi-link.md:75,77`; `R-SPI-SER` qty 3 agrees across the BOM, the
  ADR withdrawal note and the schematic page.
- **`dac-rail`** `[calc] 1.25 × (1 + 475/150) = 5.208` ✓, and `0.625 × 5.21 =
  3.256` ✓ matching `0004:209`.
- **`inamp-full-scale`** `[calc] 1 + 50/42.2 = 2.18483`; `× 1000/1011 =
  2.16106`; `× 4.595 = 9.93` (the register's `× 4.6 = 9.941`) ✓, and the sensor
  span `4.86 − 0.265 = 4.595` ✓.
- **The key-path latency table** reproduces exactly (see G3-23/G3-19), as does
  the analog breath table.
- **The 8.4 V WS2815 `V_IH`** that CLAUDE.md §3 records as wrong is dead: all
  four corpus hits are refutations (`0014:105`, `led-strip-drive.md:78` and two
  BOM copies), none live.
- **USB MIDI opt-in — the corpus's one clean fact — is still clean.** `[repo]`
  it is stated once, `firmware/README.md:100`, and the other sites cite it by
  document: `docs/decisions/0009-enclosure-construction.md:357-358` (“That is
  the whole reason USB MIDI is opt-in rather than default
  (`firmware/README.md`)”), `0013:76`, `0008:140`, `README.md:62`. Fourteen
  mentions across eleven files and not one restatement of the mechanism. It is
  the working model and it is worth saying that it still works.
- **`merge-bom.py --check` passes** `[test]` — the master genuinely matches the
  26 fragments, so none of the BOM findings above is a stale generated file;
  they are all live in the fragments.

---

## What I could NOT check

- **Anything requiring a datasheet.** I read no banked PDF. Every
  `[datasheet]` claim in the corpus is unverified by me, including the ones the
  register calls re-verified (SBOS410O §8.4.1, SBOS737C p.8/Fig 26, the 1N5817
  Fig. 2 digitisation, the Gateron drawing's 1.20 mm and 5 ms, the MPXV4006DP
  transfer function, the LT1641 77 µA ramp). Where a figure's *arithmetic*
  could be checked from its own stated inputs I checked it; where the input is
  a datasheet reading I took it as given. G3-6 in particular may resolve to
  either 0.42 or 0.54 depending on a DAC8568 drift spec I did not open.
- **`hardware/module/link-supervision/` has a `circuit.yaml` and no
  `bom.csv`.** I noted it for G3-8's fragment count but did not determine
  whether that is correct (the directory says “NOT FITTED”, so it may be
  deliberate) or a gap `merge-bom.py` would not report.
- **`datasheets/`** — not in the §6 corpus and out of my brief. I did not run
  `verify-datasheets.py` and make no claim about MANIFEST integrity.
- **`mechanical/`** — I read neither the KiCad panel file nor `make_blanks.py`,
  both of which `panel-height-budget` derives from. Its 128.5 mm / hole-centre
  inputs are unverified by me.
- **Semantic dependency sweep.** I found G3-14 and G3-15 opportunistically
  while chasing numbers. I did **not** run a systematic pass for deleted parts
  still depended on, so there are likely more of that class. CLAUDE.md §5 is
  right that this needs a reader, and it needs a reader whose brief is that and
  not this.
- **The 211-item advisory, item by item.** I derived my own census (374
  quantities at ≥3 files by my normalisation, which folds spellings the
  checker counts separately) and compared only at the level stated in class
  (c). I did not reconcile the two lists entry by entry.
- **Whether any finding here was already filed by an earlier wave.** I am cold;
  I did not look. Several of these read like they *should* have been caught
  before — G3-7 and G3-8 especially — which is itself worth someone checking
  against the previous rounds' ledgers.

---

## The one structural conclusion

Eleven of my thirteen class-(a) findings are in text the register already
tracks the neighbourhood of. None of them is a spelling of a `forbidden`
pattern, and none of them could be: **`forbidden` lists hold values a figure
*used to have*, and nine of the thirteen are cases where a value the corpus
never tracked was derived from one it did.** 290 mA (G3-1), 531 Hz (G3-3),
40.34 mm (G3-10), 4.7 V (G3-9), 392 mA (G3-2), 0.54 cents (G3-6), 138 rows
(G3-7): every one is a *second-order* number — something computed from a
tracked figure and then written down. The register protects the input and
nothing protects the output.

That suggests the cheapest structural fix is not more patterns. It is that a
document showing a derivation should show it as arithmetic against a named
figure rather than as a finished number — `0004`'s drop table would have been
self-correcting if its cells read `2.2 Ω × umbilical-current`. The four
findings that are *not* of this shape (G3-5, G3-14, G3-15, G3-17) are all
counts or dependencies, which no checker of values can reach at all.
