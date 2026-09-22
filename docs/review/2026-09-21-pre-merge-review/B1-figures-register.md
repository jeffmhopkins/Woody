# B1 — `config/figures.yaml`, the register itself

Cold pre-merge review, 2026-09-21. Slice: all 35 entries in the shared-figure
register — arithmetic, owner statements, status, forbidden coverage,
restatement violations, and what should be tracked and is not.

Method: every derivation recomputed by hand `[calc]`; every `owner` opened and
read; every old value the entry records grepped across the design corpus
(`hardware/**`, `docs/decisions/**`, `docs/reference/**`, `config/**`,
`firmware/**`, `README.md`, `ROADMAP.md`) with the checker's own matching
semantics reproduced in a scratch script. `docs/review/**` not read.

Baseline: `python3 tools/check-staleness.py` reports
**`PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved`**.
Three of the findings below are live stale values that it scores as clean.

---

## Ranked by what it costs if wrong

| # | Finding | Cost |
|---|---|---|
| 1 | `sensor-full-scale`: a live, unguarded, unrefuted old value in ADR 0005 | **Highest** — the named failure mode, live, checker green |
| 2 | Six figures whose `owner` no longer states them; `check_owners` passes on drawing labels and on `OPA2197` | **Highest** — the one check that enforces rule 1 is returning false passes |
| 3 | `breath-working-point` is `disputed` but spent as settled in five files, and `decided_by` names a milestone that will not decide it | **High** — sets a component value already in the BOM |
| 4 | `ROADMAP.md:203` — `chain-conductors` stale, missed on capitalisation *and* shielded by the refutation exemption | High |
| 5 | `ROADMAP.md:53` — `panel-width` stale, same double escape | High |
| 6 | Four figures name the **generated** `hardware/bom.csv` as `owner` | High |
| 7 | `dig-gnd-topology`: all three candidate citations point at lines that no longer hold the claim; one is 322 lines past EOF | Medium |
| 8 | `pitch-cents-budget`: `decided_by` describes a condition that has been fixed | Medium |
| 9 | `diode-split-rationale`: the `value` contradicts its own `derivation` by 4.7× | Medium |
| 10 | Nine derived quantities with no register entry; two already divergent | Medium |
| 11 | `loop-budget`: the `derivation` does not reproduce the `value`, and its input appears nowhere | Medium |
| 12–17 | Arithmetic slips, restatement counts, latent forbidden-list traps | Low |

---

## 1. `sensor-full-scale` — a LIVE stale value, unrefuted, checker green

`[repo] docs/decisions/0005-power-architecture.md:74`

```
The MPXV4006DP is a 5 V part outputting **0.2–4.7 V** (ADR 0003). A buffer
running on 3.3 V would clip the top 30% of the breath range. So the analog front
end needs 5 V, and a rail-to-rail op-amp on 5 V reaches 4.7 V with margin to
spare.
```

The dash is **U+2013 with no surrounding spaces** `[repo] cat -A gives
`0.2M-bM-^@M-^S4.7 V``. The `sensor-full-scale` forbidden list carries
`"0.2-4.7 V"` (ASCII hyphen) and `"0.2 – 4.7 V"` (en dash **with** spaces), and
separately carries `"0.2–4.80 V"` — the tight-en-dash form, but only for the
`4.80` spelling. The tight-en-dash form of `4.7` is the one spelling nobody
added `[repo] config/figures.yaml:40`.

Reproduced against the checker's own matcher: **zero forbidden hits, and
`REFUTATION` does not fire** — the line carries no refutation wording at all. It
asserts the refuted transfer function as live fact and cites ADR 0003, which
refutes it `[repo] docs/decisions/0003-breath-sensing-path.md:101-102, 123-125`.

Two further statements on the same three lines depend on it: *"would clip the
top 30% of the breath range"* and *"reaches 4.7 V with margin to spare"*. At the
real full scale of 4.86 V `[repo] figures.yaml sensor-full-scale` the second
claim is materially tighter than written — this is the ADR that decides the 5 V
rail exists at all.

This is the **sixth** recorded instance of the project's named failure mode and
it is exactly the mechanism `escape_note` describes: *"an en dash with no
spaces"*. The note was written; the pattern was added for `4.80` and not for
`4.7`.

**Fix:** add `"0.2–4.7 V"` (U+2013, no spaces) to `sensor-full-scale.forbidden`
and correct ADR 0005:74 in the same commit.

---

## 2. Six figures whose `owner` does not state them — and `check_owners` passes anyway

Rule 1 says the owner *states* the figure. `check_owners` was added to enforce
exactly that. I ran its algorithm over every settled entry and then opened every
owner. Six fail, and each one passes the check for a reason the check cannot
see.

### 2a. `loadswitch-gate-cap` — passes on `OPA2197`

`owner: hardware/module/power-entry/power-entry.md`. Value `"82 nF, ramp 49-197
ms (98 ms typ)"`. The longest distinctive token is `197`. Its only two
occurrences in the owner are:

- `[repo] hardware/module/power-entry/power-entry.md:40` — `│ OPA2197 ×6, INA828`
- `[repo] hardware/module/power-entry/power-entry.md:103` — `→ OPA2197 PSRR (**110.5 dB worst case**…`

**The check is satisfied by the op-amp's part number.** The page states neither
82 nF nor any ramp figure; the only trace of the capacitor is the ASCII label
`[C-GATE 82nF]` at line 61. The actual statement and derivation live in
`[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:253-265`
(`**C-GATE is set to 82 nF** (E24; 83 nF is not a stock value)`, with the
61/122/244 V/s table and the 49–197 ms conclusion).

This is `loop-budget`'s escape_note recurring in a new form. That note concluded
*"a check that matches ANY token of a multi-token value can be satisfied by the
least informative one"* and the fix was to take **the longest** token. The
longest token is still a substring of an unrelated part number.

### 2b. `loadswitch-fb-divider` — passes on a drawing label

`owner: power-entry.md`. Token `35.7`. Sole occurrence:
`[repo] hardware/module/power-entry/power-entry.md:64` —
`│                          [R-FB-HI 35.7k 1%]                  │`, inside the
ASCII schematic. The sizing derivation — `k = V_FB / V_OUT = 1.313 V / 10.5 V`,
the E96 choice, the 10.05–10.93 V worst case — is at
`[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:144-178`.

### 2c. `loadswitch-timer` — reported UNCHECKED, owner has only a label

`owner: power-entry.md`. Value `"10 uF"` has no token ≥3 characters, so the
checker lists it as *"UNVERIFIABLE"* rather than passing it — correctly. But the
owner contains only `[C-TIMER 10µF]` at `[repo] power-entry.md:60`. The
statement is at `[repo] umbilical-load-switch.md:232-248` (`**C-TIMER is set to
10 µF**`, the 9.30/9.37 µF comparison, the 587/160/95.6 ms table).

All three LT1641 figures were assigned to `power-entry.md` and the load switch
has had its own circuit directory since the Phase B split. The drawing stayed
behind; the derivations moved.

### 2d. `dac-rail` — passes on a drawing label; the derivation is in the BOM

`owner: power-entry.md`. Token `5.21`. Sole occurrence:
`[repo] power-entry.md:42` — `└──[LM317LZ]──┬── DAC AVDD 5.21V`, with
`150R/475R` as the label beneath it at line 43. The page's interface table at
line 26 *cites* `dac-rail` — the owner citing its own figure rather than stating
it. The derivation `Vout = 1.25*(1+475/150) = 5.21V` exists only in the
`R-REG-SET` row `[repo] hardware/bom.csv:111`.

`dac-rail` is the most widely restated figure in the corpus (see §12), and its
owner states it only as art.

### 2e/2f. `cref-out-node` and `riso-ref-topology` — the owner says the material moved

Both name `owner: hardware/carrier/carrier.md`. That page says so itself:

> `[repo] hardware/carrier/carrier.md:146-151` — *"The `R-ISO-REF` half of this
> section — the compensation network, why TI's Figure 56 transfers, and what it
> buys — moved verbatim to `breath-excitation-reference/`… The drawing above
> stays here because it is one connected picture."*

What is left in `carrier.md` is the drawing: `REF5050` at line 92 and
`──[37.4 Ω]──` at line 95. `check_owners` tokenises `cref-out-node`'s value to
`5050` (from the part number in the prose value) and `riso-ref-topology`'s to
`37.4`, and both are in that drawing.

The statements are at
`[repo] hardware/carrier/breath-excitation-reference/breath-excitation-reference.md:37,40,43,56,97`.
That page's own interface table cites the two figures back at the register
(`| REF5050 VOUT | internal | — | cref-out-node | …Settled`), so the citation
graph is circular: the register points at `carrier.md`, `carrier.md` points at
`breath-excitation-reference.md`, and that page points at the register.

**Cost.** This is the class of defect `check_owners` was written to catch, and
it is passing six of them. A reader following `owner:` to check a load-switch
number lands on a page that shows the part and derives nothing.

**Fix:** reassign `loadswitch-timer`, `loadswitch-gate-cap` and
`loadswitch-fb-divider` to `hardware/module/umbilical-load-switch/umbilical-load-switch.md`;
`cref-out-node` and `riso-ref-topology` to
`hardware/carrier/breath-excitation-reference/breath-excitation-reference.md`;
and either move the LM317 derivation into `power-entry.md` or make the
`R-REG-SET` fragment the owner of `dac-rail`. Separately, `check_owners` should
reject a token that only occurs inside a longer alphanumeric run (`197` in
`OPA2197`) and should not count a match inside a fenced code block.

---

## 3. `breath-working-point` — `disputed`, and spent everywhere as settled

`status: disputed`, `value: "DISPUTED"`, `forbidden: []`. Because the status is
not `settled`, `check_owners` skips it; because `forbidden` is empty,
`check_figures` has nothing to match. **Nothing in the toolchain touches this
figure at all.** Meanwhile 2.8 kPa is live, unqualified, in five corpus files:

| Where | What it asserts | `[prov]` |
|---|---|---|
| `hardware/module/breath-output-stage/breath-output-stage.md:39` | `Hard blow, real playing (~2.8 kPa) \| 2.411 V \| **−4.64 V**` | `[repo]` |
| `…breath-output-stage.md:42` | *"Real playing only reaches about 2.8 kPa … **(ADR 0003)**"* | `[repo]` |
| `hardware/carrier/breath-adc/breath-adc.md:37-38` | `real play = 2.8 kPa → … → 1795 counts` `[2.8 kPa from breath-receive-stage.md]` | `[repo]` |
| `hardware/module/breath-response-shaper/breath-response-shaper.md:91,95,103,139` | the whole `R-RESP` sizing, `hard blow 4.64 V`, *"targeting ~1.5× at a hard blow"* | `[repo]` |
| `hardware/bom.csv:74` / `…/breath-response-shaper/bom.csv:3` | `R-RESP … targeting ~1.5x gain ratio at a hard blow (4.64V at the in-amp)` | `[repo]` |

**Both citations for it are dangling**, which is the register's own candidate
note still live:

- `breath-output-stage.md:42` attributes 2.8 kPa to **ADR 0003**. ADR 0003 says
  *"playing sits around 0–5 kPa"* `[repo] docs/decisions/0003-breath-sensing-path.md:140`
  and contains no 2.8.
- `breath-adc.md:38` attributes it to **`breath-receive-stage.md`**. That page
  now states it in the past tense — *"The knob does more work than **this page
  used to say**: real playing tops out around 2.8 kPa"*
  `[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:192-194`.
  The cited page has retracted the number the citing page rests on, and
  `breath-adc.md` is a **third** page added to the circle since the register
  described it as two.

**`decided_by` names the wrong milestone.** It says *"M1, with a player and a
manometer."* ROADMAP M1 is **Switch characterisation** — KS-33 cutout, bounce,
actuation hysteresis, spring weight
`[repo] ROADMAP.md:71`. It contains nothing about breath. The milestone that
could decide it is E2, *"Breath sensing … a human plays it for 20 minutes
through a real mouthpiece"* `[repo] ROADMAP.md:42`, and E2 does **not** ask for
a pressure measurement. Grepping ROADMAP for `manometer|kPa|hard blow|breath
pressure` returns one hit, unrelated `[repo] ROADMAP.md:167`. **So the plan
contains no step that resolves this figure**, while the figure's own
`decided_by` says it *"Sets the panel gain range AND the ADC headroom."*

**Cost.** `R-RESP` is a specified 15 kΩ part in the BOM whose value is sized
against 4.64 V, which is 2.8 kPa × the in-amp gain. If M1/E2 comes back at the
3–4 kPa of the third candidate, `R-RESP`, the `POT-GAIN` working point
(*"near 2.1×"*, `breath-receive-stage.md:195`) and the 1795/1598-count ADC
figures all move, and none of them is guarded.

**Fix:** give the entry a provisional value plus `forbidden` patterns so the
chain is at least *visible* when it moves; correct `decided_by` to E2 and add
the measurement to E2's row in ROADMAP.

---

## 4. `chain-conductors` — live stale in ROADMAP, missed on one capital letter

`[repo] ROADMAP.md:203`

```
| **Does the chained key loom fit the side channel?** | M4 | Six conductors per
hop rather than the 32–44 the tail-mounted alternative needed — …
```

The loom is **12 conductors per hop** `[repo] config/figures.yaml
chain-conductors`, `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:81,160,252`.

The forbidden list carries three casings — `"six conductors per hop"`,
`"SIX conductors per hop"`, `"6 conductors per hop"` — and not **`"Six
conductors per hop"`**, Title case, which is what a sentence-initial cell
produces `[repo] config/figures.yaml:192`.

**And it is double-shielded.** Reproduced against the checker: zero forbidden
hits, `REFUTATION` **fires** (`rather than`). So even if the Title-case pattern
were added today, the line would be scored *refuted-in-place* and stay live.
The refutation exemption cannot tell *"X rather than Y"* used as a correction
from *"X rather than Y"* used as a live comparison against a rejected
alternative — and the second form is how ROADMAP's whole "Why" column is
written.

## 5. `panel-width` — live stale in ROADMAP, identical mechanism

`[repo] ROADMAP.md:53` (E12): *"etherCON braced to the PCB — good practice **at
8HP** rather than the structural necessity it was at 6HP."*

The panel is 10HP, and ADR 0004 carries the corrected sentence verbatim: *"**At
10HP** this is good practice rather than a structural necessity."*
`[repo] docs/decisions/0004-cv-interface-module.md:830`. The fix landed in the
ADR and not in ROADMAP — the named failure mode, again.

Forbidden has `"at 8HP this"`; the live spelling is `at 8HP rather`
`[repo] config/figures.yaml:276`. Zero hits, and `REFUTATION` fires on `rather
than`. `ROADMAP.md:190` shows the same fact written safely — *"Was called
comfortable at the superseded 8HP"* — so the corpus has both forms and only one
was fixed.

**Fix for 4 and 5:** these two are not pattern bugs, they are a structural gap.
`ROADMAP.md` is in the corpus, is written in a comparative voice that trips
`REFUTATION` on almost every row, and is not where anyone edits when a figure
moves. Worth considering a rule that a `REFUTATION` exemption requires the
refutation token *and* an explicit marker (`superseded`, `this row said`) rather
than any of 25 common English words.

---

## 6. Four figures name the **generated** `hardware/bom.csv` as `owner`

`key-pullup-qty`, `panel-toggle-hole`, `ferrite-bias-impedance` and
`ref5050-grade` all carry `owner: hardware/bom.csv`
`[repo] config/figures.yaml:206,309,532,541`.

`hardware/bom.csv` is generated by `tools/merge-bom.py` from per-circuit
fragments, and *"a direct edit … survives until the next run of that tool and
then disappears without a word"* `[repo] CLAUDE.md, Hardware conventions;
[repo] tools/merge-bom.py:1-14`.

So rule 1 — *"the owning document states it"* — directs a maintainer to state
the figure in the one file where the statement cannot survive. The real homes
are:

| Figure | Fragment that actually holds it | `[prov]` |
|---|---|---|
| `key-pullup-qty` | `hardware/cluster/key-switch-network/bom.csv:3` | `[repo]` |
| `panel-toggle-hole` | `hardware/module/umbilical-load-switch/bom.csv:2` | `[repo]` |
| `ferrite-bias-impedance` | `hardware/unplaced.csv:25` | `[repo]` |
| `ref5050-grade` | `hardware/carrier/breath-excitation-reference/bom.csv:2` | `[repo]` |

`check_owners` reads the generated master, so it would go green on a value
present in the master and absent from the fragment — i.e. precisely during the
window in which the value is about to be silently deleted.

Note also that `ferrite-bias-impedance`'s real home is `hardware/unplaced.csv`,
*"the rows no schematic page names"*. A tracked figure whose owner is a part
nobody has drawn is worth flagging on its own.

`panel-toggle-hole` has a second version of the same problem: it is a **panel
machining dimension** whose only statement is a BOM row
(`"THROUGH-HOLE, M6x0.75 bushing mount, 6.5mm panel hole with a 5.8mm D-flat"`,
`[repo] hardware/bom.csv:54`). `hardware/module/panel/panel.md` — the page
someone will have open when the DXF is cut — does not mention it.

---

## 7. `dig-gnd-topology` — all three candidate citations are broken

`[repo] config/figures.yaml:392-396`. Each candidate carries a `file:line`:

| Candidate cites | Actually at | `[prov]` |
|---|---|---|
| `docs/decisions/0004-cv-interface-module.md:627` | **:637** — `- **DIG_GND likewise** — its own path to the star.` | `[repo]` |
| `hardware/module/power-entry/power-entry.md:495-498` | **the file is 173 lines long**; the claim is at **:153** | `[repo] wc -l` |
| `hardware/module/digital-and-supervision/digital-and-supervision.md:53` | **:26**; line 53 is ASCII art | `[repo]` |

One citation points 322 lines past the end of its file. `check_sections`
validates `page.md §N` references and `check_links` validates markdown links;
nothing validates `path:line`, and `config/figures.yaml` is the corpus file
that uses that form most.

The entry's `note` inherits the error: *"IT WAS NOT — **line 627** still says
the opposite."* The claim is still true; the locator is not. A reader who
follows it finds a paragraph about IR drop and may conclude the finding was
fixed.

**Status check:** the dispute itself is genuine — the three positions are
mutually exclusive and all three are live. `decided_by` (the 2-layer vs 4-layer
decision) is a real, upstream, decidable question. Keep `disputed`; fix the
three line numbers or drop them for section references.

---

## 8. `pitch-cents-budget` — `decided_by` describes a condition that has been fixed

`decided_by: "pitch-stage.md has two contradictory budget tables back to back
and states no total. One coherent table, then cite it."`
`[repo] config/figures.yaml:330`.

**The first half is no longer true.** `pitch-stage.md` now carries one budget
table `[repo] hardware/module/pitch-stage/pitch-stage.md:281-285` and says
explicitly: *"(The superseded version of this table, which contradicted the live
one twelve lines above it, is in `notes.md`.)"* `[repo] pitch-stage.md:298-299`.

The second half still holds: the page states no total.

Two consequences:

1. Half the work `decided_by` names is done and the register does not know. This
   is the *"`disputed` on something that has since been settled"* half of the
   failure — it will look unresolved to the next reviewer for a reason that has
   already been dealt with, and the remaining work (state a total) is one line.
2. **The live table's total is a fifth number, in no candidate list.**
   `[calc]` from `pitch-stage.md:283-285`: 0.42 + 0.027 + 0.068 = **0.515 cents
   linear**; RSS = √(0.42² + 0.027² + 0.068²) = **0.426 cents**. The four
   candidates are 0.42 (a row, not a total), 0.85, 1.35 and ~1.2. None matches.

**Fix:** rewrite `decided_by` to *"pitch-stage.md's live table states no total;
state the RSS and the linear sum and cite it"*, and add 0.43 / 0.52 as the
candidate derived from the current table.

---

## 9. `diode-split-rationale` — the `value` contradicts its own `derivation`

`value: "fault isolation and HF isolation (r_d 69 mohm at 392 mA)"`
`derivation: "Vf modulation is 120 mV: 0.24 V at 245 mA -> 0.36 V at 612 mA,
digitised off Fig. 2 of Diodes Inc DS23001 Rev.8"` `[repo] config/figures.yaml:470-472`.

`[calc]` The chord slope of the two digitised points the derivation names is
(0.36 − 0.24) V / (612 − 245) mA = 0.120 / 0.367 = **327 mΩ**. The value claims
**69 mΩ**, which is 4.7× smaller.

69 mΩ is reproducible only as the *ideal-diode* small-signal term with no series
resistance: `[calc]` nV_T/I = 25.9 mV / 392 mA = 66 mΩ. The banked curve the
same entry cites as authority says the real device slope in that region is five
times that.

Both numbers are also in the owner, one paragraph apart
`[repo] hardware/module/power-entry/power-entry.md:85` (120 mV over 245→612 mA)
and `:113` (*"`r_d` is 69 mΩ at 392 mA"*).

**Why it matters:** 69 mΩ is the surviving justification for keeping D1/D2 —
*"Stated correctly they are still worth twenty cents. Left as it was, the next
reviewer who checks the arithmetic deletes the part."* The arithmetic that
reviewer would check does not support it. The conclusion (keep both diodes) may
well survive at 327 mΩ, and would survive *more* strongly; the stated number is
what does not.

**Secondary, same entry:** the cents chain as written does not close.
`[calc]` 120 mV × 0.52 mV/V = 62.4 µV; × 3 µV/V (110.5 dB) = 0.187 nV; the
corpus's own pitch scale is 833 µV/cent (`[calc]` from
`hardware/module/power-entry/power-entry.md:125`: 6.2 mV → 7.4 cents), giving
**0.00022 cents**, not 0.00044. The factor of 2 is the pitch stage's gain = 2
`[repo] hardware/module/pitch-stage/pitch-stage.md:123`, which is a real part of
the circuit and is absent from both the register's `derivation` and the owner's
`→`-chain. The conclusion is unaffected; the chain is not reproducible as
written.

---

## 10. Nine derived quantities with no register entry — two already divergent

Rule from the register's own `breath-zero-ref` escape_note: *"An untracked
quantity derived from a tracked one has no protection at all."* These qualify
and are untracked.

### Already divergent (find these first)

**a. Playable breath span in counts — 1594 vs 1598.**
`[repo] hardware/carrier/breath-adc/breath-adc.md:38` derives
`playable span above rest ≈ **1598** counts of 4096` (`[calc]` 1795 − 197 =
1598 ✓). Three other places say **~1594**:
`[repo] hardware/carrier/carrier.md:177`, `:373`,
`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:126`.
The register *names* 1594 in `key-scan-current.companion` without tracking it
`[repo] config/figures.yaml:131` — so the register is one of the four places and
carries the minority value.

**b. Module +12 V total — 392 mA vs 404 mA.**
`[repo] docs/decisions/0004-cv-interface-module.md:267`:
*"**~404 mA typical** (45 mA module … + **359 mA** instrument)"* `[calc]` 45 +
359 = 404 ✓. Against
`[repo] hardware/module/power-entry/power-entry.md:113` (*"69 mΩ at **392 mA**"*)
and two places in the register itself — `diode-split-rationale.value` and
`ferrite-bias-impedance.derivation` (*"the module +12V total of 392 mA"*)
`[repo] config/figures.yaml:470,533`. Both are `umbilical-current` + a module
allowance; the allowance is 33 mA in one and 45 mA in the other.

### Derived from a tracked figure, no entry

| Quantity | Value | Where | Derived from |
|---|---|---|---|
| c. In-amp **effective** gain | 2.16106 (raw 2.18483) | 5 files `[repo]` `breath-sense-link.md:153`, `breath-receive-stage.md:83`, `breath-output-stage.md:50-53`, `bom.csv:68,118`, `unplaced.csv:30` | it is the *input* to `inamp-full-scale` and `breath-zero-ref`, and omitting the divider is the documented cause of both the −10.05 V and 0.579 V errors |
| d. Hard-blow in-amp output | −4.64 V / −4.7 V | `breath-output-stage.md:39,42`, `breath-response-shaper.md:91,103`, `bom.csv:74` | `breath-working-point` (disputed) × (c) |
| e. Sensor sensitivity | 0.766 V/kPa | `breath-adc.md:37`, `0003:123` | `sensor-full-scale` |
| f. 74HC165 thresholds | V_IH 2.31 V / V_IL 0.99 V | `key-switch-network.md:49,74-75`, `0001:221`, `cluster-boards.md` | inputs to `key-release-time` and `key-press-time`; currently duplicated as prose in two `threshold_note` fields |
| g. Voltage arriving at the instrument | ~11.4 V (and ~11.36 V worst case) | `0005:95,170`, `power-entry-instrument.md:77`, `umbilical-load-switch.md:160,162` | divisor in `umbilical-current`; sizing anchor for `loadswitch-fb-divider` |
| h. Hot-plug start time | 47.5 ms | `umbilical-load-switch.md:221,223,226,247`, `0005:276,344` | the **binding case** for `loadswitch-timer` |
| i. Pitch scale | 833 µV per cent | implicit in every cents figure: `power-entry.md:125`, `pcb-pipeline.md:198`, `pitch-stage.md:108`, `0004:319` | the conversion the whole `pitch-cents-budget` dispute runs on, written down nowhere |

**j. Fitted-switch count 18 vs 21 positions.** `key-pullup-qty` tracks 24 and
derives it as *"21 switch positions + 3 free bits"*; `key-scan-current` derives
25.8 mA from *"18 fitted switches"*. Both are right — `[calc]` from
`config/key-layout.yaml:119-122`: 3+6+4+5 = 18 used, and
`spare_bits_switches: 3` reserved gives 21 positions — but neither 18 nor 21 has
an entry, and `R-KEY-SER` is qty 21 while `R-KEY-PU` is qty 24 `[repo]
hardware/bom.csv:34,35`. A future change to the key count moves three BOM
quantities and one tracked figure with nothing linking them.

---

## 11. `loop-budget` — the derivation does not reproduce the value

`value: "196-241 us of 250 us"`, `derivation: "Bus time 148-155 us PLUS ESP-IDF
per-transaction overhead (24 us interrupt / 9 us polling)…"`
`[repo] config/figures.yaml:431-434`.

The owner's own bus-time sum is a single number, not a range:
`[repo] docs/reference/latency-budget.md:146-147` — *"ADC 24 µs + key chain 32 µs
+ six DAC channels at 2 MHz 96 µs"*, `[calc]` = **152 µs**. `148-155` appears
nowhere in the corpus (`grep` over all 121 corpus files returns only
`figures.yaml`).

Nor can the value be rebuilt from the fields given: a 7 µs spread in bus time
plus a per-transaction overhead cannot produce a 45 µs spread (196→241) without
a transaction count, which no document states. `291 µs with driver defaults` is
likewise unreproducible: `[calc]` 291 − 152 = 139 µs, which is not an integer
multiple of 24.

The owner now *states* 196–241 `[repo] latency-budget.md:148`, so
`check_owners` is satisfied and the escape_note's fix has held. But the figure
is now asserted in two places and derived in neither — which is the state the
escape_note itself warns produced the 136 µs error.

`[repo]` The owner also still carries the contradiction it flags: the table row
`SAR ADC conversion | **~24 µs**` at `:60` against the same page's warning that
*"The table above said 50–200 µs"* — resolved in prose, so this one is fine.

---

## 12. Rule 1 restatement violations, counted

The rule is *"the owning document states it and every other document cites it by
name."* Counting corpus files that carry the number itself, excluding the owner,
excluding `config/figures.yaml`, and excluding lines that carry refutation
wording:

| Figure | Non-owner files restating | Worst cases `[repo]` |
|---|---|---|
| **`dac-rail`** | **~12** | `0004:151,178,209,301`; `0003:375,621`; `0006:188,604,794`; `0005:125`; `ROADMAP:47`; `dac8568.md:35,38`; `breath-receive-stage.md:86`; `pitch-stage.md:85`; `breath-output-stage.md:67,124,127` — and the owner states it only in art (§2d) |
| **`mod-reference`** | 6 (≈14 occurrences) | `0006:15,21,92,105,117,125,127,248`; `pitch-stage/notes.md:33`; `pcb-pipeline.md:184`; `firmware/README.md:50`; `bom.csv:86` |
| **`inamp-full-scale`** | 5 | `breath-receive-stage.md:89,126`; `breath-output-stage.md:40,51-52`; `breath-response-shaper.md:51,104`; `bom.csv:118`; `unplaced.csv:30` |
| **`key-scan-current`** | 4 | `carrier.md:172-177`; `key-chain-loom.md:115-126`; **`0001:230`**; `bom.csv:50` |
| **`sensor-full-scale`** | 4 | `breath-sense-link.md:148`; `breath-output-stage.md:38,40`; `carrier.md:114`; `breath-adc.md:35-39` |
| `key-release-time`, `key-press-time` | 1 each | `0001:227-228` duplicates the owner's table `key-switch-network.md:102-103` verbatim |
| `panel-width` | 3 | `panel.md:24,31`; `bom.csv:62`; `ROADMAP:190` |
| `umbilical-current` | 3 | `0004:267,275`; `pcb-pipeline.md:144,198`; `bom.csv:113` |

Two notes on this table:

- **`key-scan-current`'s own escape_note undercounts.** It says *"today all
  three restate it"* `[repo] config/figures.yaml:147`, naming
  `key-switch-network.md`, `carrier.md` and `key-chain-loom.md`. There is a
  **fourth**: `docs/decisions/0001-mcu-and-board-partitioning.md:230` carries
  `| Static | **1.43 mA** per closed key; 18 closed = **25.8 mA** |`. ADR 0001
  also restates `key-release-time` and `key-press-time` in the same table block
  at `:227-228`. Three tracked figures, one duplicated table, in the ADR — the
  document a reader consults first.
- Good practice exists and is worth copying: `breath-adc.md:39` writes
  `[0.265 and 4.86 from sensor-full-scale]`; `spi-link.md:37` and
  `power-entry.md:30` put the figure id in a `figure` column of the interface
  table; the `FB-IN` BOM row writes *"the 359 mA of figures.yaml
  `umbilical-current`"* `[repo] hardware/unplaced.csv:25`. Three different
  citation idioms, all correct — the corpus has the habit, just not uniformly.

---

## 13–17. Smaller findings

**13. `umbilical-current`: the derivation gives 358.1, the value says 359.**
`[calc]` 226 × 5 / (0.9 × 11.4) + 248 = 110.14 + 248 = **358.1**, which is what
the `derivation` field itself writes — and then `value: "359 mA"`
`[repo] config/figures.yaml:461-463`. The owner's table says 359
`[repo] docs/decisions/0005-power-architecture.md:95,158`. The real convention
is stated at `0005:169-171` — *"convert at the **arriving** voltage, not
12.00 V"* — and the arriving voltage falls with current, so each row uses its
own: `[calc]` solving for the quiescent row gives ~11.3 V, for the clamp-legal
row ~11.2 V. The derivation field records a fixed 11.4 V, which reproduces none
of the five rows exactly (`[calc]` 212 vs 210.7, 359 vs 358.1, 414 vs 411.7,
579 vs 571.2, 1522 vs 1521.5). Either record the per-row convention or round the
value to 358.

**14. Two incompatible LSB bases.** `key-scan-current`'s consequence uses
4096-count full scale — `[calc]` 0.077 % × 4096 = 3.15 ≈ *"3.2 LSB"*
`[repo] hardware/carrier/carrier.md:174`. `cref-out-node` and
`riso-ref-topology` use the signal's 3622-count full scale — `[calc]` 300 ppm ×
3622 = 1.09 ≈ *"1.0 LSB"*; 55 ppm × 3622 = 0.199 ≈ *"0.19 LSB"*
`[repo] config/figures.yaml:370,407`. The two are not interchangeable and both
appear as "LSB" without qualification. `riso`'s *"1000 ppm = 3.4 LSB"* fits
neither: `[calc]` 1000 ppm × 3622 = **3.62 LSB**.

**15. `ref5050-grade`: a downstream claim about the dispute has gone stale.**
`pcb-pipeline.md:82-84` says the corpus *"asserts in three places"* the wrong
grade. ADR 0003 has since been corrected
`[repo] docs/decisions/0003-breath-sensing-path.md:484-490` and a grep of the
corpus finds no remaining live assertion of ±0.05 % / 3 ppm for this part. The
dispute is still genuine (the BOM still orders `REF5050AIDR`
`[repo] hardware/bom.csv:11`) and `decided_by` is actionable; only the count is
wrong.

**16. Latent trap in `inamp-full-scale`'s forbidden list.** The list guards
`"-10.05 V"` and `"−10.05 V"`. `mod-channels` legitimately uses **±10.05 V** for
an entirely different quantity, four times
`[repo] hardware/module/mod-channels/mod-channels.md:87,97,144`,
`[repo] .../notes.md:54,60`. The current patterns miss it only because `±` is
U+00B1 and not a hyphen. Anyone "tightening" the list to a bare `"10.05 V"` —
exactly the response the escape_notes encourage — fires four false positives on
a page about a different circuit. Every other entry with this hazard carries a
`false_positive_note`; this one does not. Add one.

**17. `check_owners` reports 7 figures as UNVERIFIABLE.** `marker-bits`,
`free-bits`, `chain-conductors`, `chain-connectors`, `key-pullup-qty`,
`umbilical-pinmap`, `loadswitch-timer` `[repo] tools/check-staleness.py output`.
I verified all seven by hand and **six are genuinely stated**:
`key-layout.yaml:125,139,141` (marker 8, free 3);
`0001:81,160,252` (12 conductors); `key-chain-loom.md:85` (*"EIGHT connectors,
not five"*); `bom.csv:34` (qty 24); `0004:891-894` (the pin table). The seventh,
`loadswitch-timer`, is the real failure in §2c. So the UNVERIFIABLE list is
currently 6 false alarms and 1 hit — which is the ratio at which a warning stops
being read.

---

## Arithmetic: what I recomputed and what checks out

All 30 settled derivations were recomputed. Everything not named in §9, §11 and
§13 above reproduces its value. Spot values, `[calc]`:

- `inamp-full-scale` 1 + 50/42.2 = 2.18483; × 1000/1011 = 2.16106; × 4.6 = 9.941 ✓
- `sensor-full-scale` 5 × (0.1533 × 6 + 0.053) = 4.864 ✓; pedestal 5 × 0.053 = 0.265 ✓
- `breath-zero-ref` 0.265 × 2.16106 = 0.5727 ✓ (and 0.579 = ×2.18483, 0.437 = 0.200 × 2.18483 — both reconstructions in the escape_note check out)
- `key-release-time` 103.4 × ln(3.1565/0.99) = 119.88 ✓; bound 103.4 × ln(3.1565/0.825) = 138.74 ✓
- `key-press-time` (2200∥100) × 47 n = 4.4957 µs; × ln(3.1565/0.8465) = 5.918 ✓; 250/5.92 = 42.2× ✓
- `mod-reference` 4·V_dac − 3 × 3.3333 spans −10.000…+10.000 ✓; the 2.5 V case gives −7.5…+12.5 ✓; escape_note's 3.3333/2500 = 1.333 mA ✓
- `panel-width` 50.8 − 0.3 = 50.50 ✓; `panel-height-budget` 5+22+39+31+13 = 110 ✓, 128.5 − 2×6.5 = 115.5 ✓, 116.9 / 112.5 ✓, blocked bands [4.0,11.0] and [39.56,46.56] → 28.56 mm clear ✓, toggle clearances 2.88 / 3.02 / 4.52 ✓, lever sweep 10.5 sin 25° = 4.44 ✓
- `loadswitch-timer` 77 µA × 150 ms / 1.233 = 9.37 µF ✓; 62 × 150 = 9.30 µF ✓; (24/80/132 − 3) µA at 10 µF → 587/160/95.6 ms ✓; 95.6/47.5 = 2.01× ✓; 9.4 µF → 1.89× ✓
- `loadswitch-gate-cap` 5/10/20 µA ÷ 82 nF = 61/122/244 V/s ✓; 12 V ÷ those = 197/98/49 ms ✓
- `loadswitch-fb-divider` 0.5/1.313 = 0.381 ✓; 1.313 × (1 + 35.7/5.11) = 10.486 ✓; ±1 % × V_FBH window → 10.045 / 10.931 ✓; 0.5 × 7.9863 = 3.99 V ✓
- `opa2197-output-impedance` poles 21 kHz → 4.24 kHz at 100 nF ✓, 208 Hz → 42 Hz at 10.1 µF ✓
- `matrix-led-current` 960/2304/3648 mA at 5/12/19 mA/ch × 192 ✓; 2304/960 = 2.4× ✓; B5819WS 200 mW ÷ 0.46 V = 435 mA ✓, (125−60)/500 ÷ 0.46 = 283 mA ✓
- `plate-thickness` 1.5 − 1.25 = 0.25 over ✓; 2 − 1.25 = 0.75 over ✓; 1.15 − 1.10 = 0.05 under ✓
- `chain-conductors` 4+5+1+2 = 12 ✓; `chain-connectors` 1+2+2+2+1 = 8 ✓; `key-pullup-qty` 21+3 = 24 ✓
- `key-layout.yaml` self-consistency: 18 used + 14 spare = 32 = 4 devices × 8 ✓; 8 marker + 3 reserved + 3 free = 14 ✓; free bits 22, 23 (left_thumb) and 31 (left_hand) are consistent with the per-cluster spare counts ✓

`ferrite-bias-impedance`'s FB2 interpolation also checks: `[calc]` linear between
the 250 mA (431 Ω) and 500 mA (157 Ω) traces gives 312 Ω at 359 mA and 275 Ω at
392 mA, bracketing the stated ~280–310 and ~245–275 ✓.

---

## Status summary

| Status | Count | Verdict |
|---|---|---|
| `settled` and safe to cite | 24 | ✓ |
| `settled` but owner does not state it | **6** | §2 — fix `owner:` |
| `disputed`, still genuinely unresolved | 3 (`breath-working-point`, `dig-gnd-topology`, `ref5050-grade`) | ✓ keep, but §3 and §7 |
| `disputed`, condition partly satisfied | 1 (`pitch-cents-budget`) | §8 — rewrite `decided_by` |
| `blocked`, correctly | 1 (`matrix-led-current`) | ✓ — `MANIFEST.csv` carries the BLOCKED `WS2812B-0807` row with its URLs `[repo] datasheets/MANIFEST.csv:98`; E1 exists `[repo] ROADMAP.md:41`; `blocked_on` is honest |

No entry is `settled` on something the corpus openly disagrees about, with one
qualification: `diode-split-rationale` is `settled` on a value (§9) that its own
`derivation` contradicts, and `key-scan-current` is `settled` while one of its
named consequences has two live values (§10a).

---

## Suggested order of work

1. ADR 0005:74 and the missing `"0.2–4.7 V"` pattern (§1) — one line each, and
   it is the live instance of the named failure.
2. The six `owner:` reassignments (§2) — until they land, the check that
   enforces rule 1 is returning false passes on a quarter of the settled
   entries.
3. ROADMAP.md:53 and :203 (§4, §5), and a look at whether `REFUTATION` should
   require an explicit marker.
4. `breath-working-point`'s `decided_by` and the E2 ROADMAP row (§3).
5. 1594 vs 1598 and 392 vs 404 (§10a, §10b) — both are one-line divergences now
   and both are inputs to things already drawn.
6. `dig-gnd-topology`'s three line numbers (§7) and `pitch-cents-budget`'s
   `decided_by` (§8).
