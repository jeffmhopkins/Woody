# D8 — the two figures newly tracked on 2026-09-22, and which others should be

**Slice:** the register's two new entries — `breath-sensor-slope` and
`ks33-contact-bounce` — verified against the banked documents, followed out
into every place the corpus writes those values, plus the wider question of
what else is load-bearing and untracked.

**Method.** Both PDFs read with PyMuPDF (`pip install pymupdf` per this wave's
README); sheet 6 of the Gateron drawing also rendered at 150 dpi and read by
eye, because the extractable-text route is exactly the route that failed here
once. Pattern behaviour tested by re-implementing `check_figures`'s joined
stream and its ±300-char refutation window rather than by reading the code and
believing it. Git history used; no file under `docs/review/**` was opened.

---

## Verdict

| # | Finding | Severity |
|---|---|---|
| **D8-1** | `ROADMAP.md`:71 still says bounce is **not published** — a live contradiction of `ks33-contact-bounce` and of the ROADMAP's own §112, missed by all five of the entry's patterns | **high** |
| **D8-2** | `key-release-time` is restated as a stale **125 µs** in two live places, one of them the fix batch's own new paragraph and one the owner page | **high** |
| **D8-3** | `bounce duration and the reset point` is a pattern that will fire on a true sentence — it matches M1's own job description, and breaks the rule its own `false_positive_note` states | medium |
| **D8-4** | The bounce consequence did **not** land in ADR 0001, whose parenthetical about scanning faster is now backwards; nor in `firmware/README.md` or ADR 0002 | medium |
| **D8-5** | `breath-adc.md`:40 still restates `0.766` uncited — the register's own note names it as "the one that would go stale silently" and it was not fixed | medium |
| **D8-6** | `bom.csv`:42 asserts "Full scale **CONFIRMED** as 0.2 to 4.8V" — the refuted cover-page span, live and unguarded in the generated master | medium |
| **D8-7** | `ks33-contact-bounce`'s owner claim is **UNCHECKED** by `check_owners`; its value has no token ≥3 characters | low |
| **D8-8** | Three `breath-sensor-slope` patterns that never existed in the corpus, guarding nothing, while the one real restatement has no pattern | low |
| **D8-9** | Two corpus files give two sizes for the drawing's text layer (9,680 vs 11 kB); the measured figure is 11,053 | low |
| **D8-10** | Ranked list of untracked load-bearing quantities, and the two reasons the advisory cannot nominate the best of them | advisory |

Both values are **correct**. Both derivations are **sound**. The defects are all
in completeness and in the patterns.

---

## 1. `breath-sensor-slope` — 0.7665 V/kPa

### 1.1 The value is right, verbatim

`[datasheet]` `datasheets/analog/MPXV4006DP.pdf` p.5, in the axis block of both
Figure 4 and Figure 5:

> `Transfer Function (kPa): Vout = VS*[(0.1533*P) + 0.053] ± 5.0% VFSS`

with `VS = 5.0 Vdc` / `TEMP = 10 to 60°C` stated on the same plot. `[calc]`
5 × 0.1533 = **0.7665 V/kPa**. The entry's `derivation` reproduces the
transfer function character for character — I compared it against the extracted
text, not against another document's copy of it.

`[datasheet]` p.3, Table 1 corroborates from the other side: `Sensitivity V/P
— | 766 | — mV/kPa`, and `Offset Voff 0.152 / 0.265 / 0.378 V`, which is
`0.053 × 5 = 0.265` `[calc]`. The 0.265 V pedestal `sensor-full-scale` and
`breath-zero-ref` are built on is the same line of the same table.

**One over-claim in the `derivation` string.** It says the datasheet's
sensitivity line "says 766 mV/kPa, which is the same number rounded."
`[calc]` 0.7665 V/kPa is 766.5 mV/kPa, which rounds half-up to 767, not 766;
and read the other way, 766 mV/kPa implies a coefficient of 0.1532, not
0.1533. The two datasheet statements disagree by 0.065 %. Nothing downstream
cares at that size, but "the same number rounded" is not what the document
says — it is two independently rounded statements of one quantity. Suggest
"766 mV/kPa on p.3 is the same quantity to three digits".

### 1.2 Ratiometry: the entry says so, but only in the prose the citers do not read

`quantity` carries the condition (`… at VS = 5 V`) and `note` states the
ratiometry outright `[repo] config/figures.yaml:137,147`. So the entry is
honest. **But `value` is the bare string `0.7665 V/kPa`**, and `value` is what
a citation resolves to. Compare `ks33-contact-bounce`, whose `value` is
`5 ms max at 16 in/sec actuation` — condition inside the value, where it cannot
be dropped. The two new entries use opposite conventions for the same problem.
Recommend `value: "0.7665 V/kPa at VS = 5.000 V"`.

**A sharper point the entry misses.** `[datasheet]` p.3, footnote 1 to the
Supply Voltage row: *"Device is ratiometric within this specified excitation
range"* — and that range is **4.75 / 5.0 / 5.25 Vdc**. So at 3.3 V the part is
not a sensor with a smaller slope; it is **outside its specified excitation
range entirely** and nothing about its output is guaranteed. The entry's
`forbidden` list contains `0.5059 V/kPa`, which is `[calc]` 3.3 × 0.1533 — i.e.
whoever wrote that pattern was guarding against a *scaled* 3.3 V slope, which
concedes the wrong premise. If a 3V3 proposal ever comes back, the answer is
not "the slope would be 0.5059" but "the datasheet does not cover it".
Worth one line in the `note`.

### 1.3 Does anything downstream assume a supply it will not get? No.

`[repo] docs/decisions/0003-breath-sensing-path.md:475` — the sensor's `VS`
comes from `+12V → REF5050 5.000 V → OPA2197 buffer half → MPXV4006DP VS`.
That is inside 4.75–5.25 V, and **the 10 mA max supply current lands on the
op-amp, not on the reference**, which is the arrangement that makes the
ratiometric claim safe `[repo]
hardware/carrier/breath-excitation-reference/breath-excitation-reference.md:6,99-100`.
The REF5050 needs 5.2–18 V in and gets 12 V `[repo] 0003:479`.

Two residual exposures, both already tracked elsewhere and neither a defect
here: `ref5050-grade` is **disputed** at ±0.1 % vs ±0.05 % initial accuracy,
and a ratiometric sensor turns supply error into scale-factor error one for one
— so the slope's fifth significant figure is decorative until that is settled.
The ADC chain is consistent with 5 V excitation: `[calc]` 4.864 × 0.6 = 2.918 V
→ 2.918/3.3 × 4096 = 3622 counts, which is what
`hardware/carrier/breath-adc/breath-adc.md:38` prints.

### 1.4 Owner: right file, states the value, does not name the id

`[repo] docs/decisions/0003-breath-sensing-path.md:123` — *"`Vout = VS ×
(0.1533·P + 0.053)` at VS = 5 V is 0.7665 V/kPa with 0.265 V at zero"*. That
is the derivation's home and the right owner. `[test]` `check_owners` verifies
it: the value tokenises to `0.7665`, which is ≥3 characters and appears
anchored on that line.

The owner page never names `breath-sensor-slope`. Nor does `ks33-geometry.md`
name `ks33-contact-bounce`. Not a rule violation — rule 1 asks the owner to
*state* the figure — but it means the only way to get from the owning sentence
to the register is to already know the id exists. The one thing rule 1 gets
right about USB MIDI opt-in is that the citers point at a name.

### 1.5 Every place the corpus writes this value

`[repo]` grep for `0.7665|0.766|766 mV|766mV|0.1533|V/kPa` across
`hardware/** docs/decisions/** docs/reference/** config/** firmware/** README
ROADMAP`:

| Place | Form | Cites? |
|---|---|---|
| `0003:123` | `0.7665 V/kPa` | owner statement — correct |
| `0003:117` | `766 mV/kPa` twice, GP vs DP table | restates; **legitimate** — it is quoting the datasheet to show the two variants agree |
| `0003:436` | transfer function only, no slope | fine |
| `hardware/bom.csv:42` + `hardware/interfaces/breath-sense-link/bom.csv:2` | *"(see breath-sensor-slope and sensor-full-scale)"* | **cites by id** — the only true citations, and the ones that created this entry |
| `hardware/carrier/breath-adc/breath-adc.md:40` | `0.265 + 0.766 × 2.8` | **restates, uncited** |

**D8-5.** That last row is the defect, and the register *knows*: its own `note`
says *"breath-adc.md:37, which uses 0.766 in an arithmetic chain. The third is
the one that would go stale silently."* `[repo] config/figures.yaml:152-154`.
The entry documents the defect instead of fixing it, in a commit whose subject
is about grepping first. The line already carries two bracketed citations
(`[0.265 and 4.86 from sensor-full-scale]`), so the fix is one more of the same
shape — `[0.766 from breath-sensor-slope]` — and it was not made.

`[calc]` the chain is arithmetically right and was computed with the full
0.7665: 0.265 + 0.7665×2.8 = 2.4112 V, ×0.6 = 1.4467 V → 1795 counts. Printing
0.766 while computing 0.7665 is how the printed constant becomes unfalsifiable.

Note-in-passing, same file: `[repo] breath-adc.md:52` computes the power-up
clamp current from **`(4.7 − 0.7)/10 kΩ`**. 4.7 V is the superseded full scale;
`[calc]` at 4.864 V it is 416 µA rather than 400 µA, against a ±2 mA rating, so
the conclusion is untouched — but it is the old value inside a live
calculation, and it escapes every `sensor-full-scale` pattern because none of
them anticipate the spelling `(4.7 −`.

### 1.6 The patterns guard nothing that ever existed

`forbidden: ["0.6 V/kPa", "766.5 mV/kPa at 3.3", "0.5059 V/kPa"]`
`[repo] config/figures.yaml:142`.

`[test]` all three match **zero** places in the corpus. `[git]`
`git log --all -S` for each returns only `df22096` — *the commit that added
them to `figures.yaml`*. **None of the three has ever appeared in a corpus
file.** They were written at the desk as plausible wrong values, not grepped
out of the tree, which is the half of CLAUDE.md §2 step 2 that this fix batch's
own commit message claims to be about.

They are harmless — no false positives are reachable — but they are not
protection, and they are counted in the run line as 3 of 218 patterns. The
honest state for a figure that has never moved is an empty `forbidden` list,
and `check_patterns` would then report it as thin. **That is the incentive to
name:** three unfireable patterns convert a truthful "this figure has no
guards" into a silent "guarded", and `check_patterns` cannot tell the
difference between a pattern that matches nothing because the corpus is clean
and one that matches nothing because it is fiction.

One mechanical note: `check_figures` uses `str.find`, unanchored, so
`0.6 V/kPa` would also match a future `10.6 V/kPa`. `check_owners` learned this
lesson explicitly (`"4.86" satisfied by "14.863 mm"`); `check_figures` did not.
Tooling slice's call, not mine.

---

## 2. `ks33-contact-bounce` — 5 ms max at 16 in/sec

### 2.1 The value is right, and the drawing really does publish it

`[datasheet]` `datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`,
sheet 6 (page 6 of 6), specification block, item 5, extracted text layer:

> `5.Bounce Time: 5msec Max.(at 16 in/sec. actuation speed).`

`[datasheet]` confirmed a second way by rendering sheet 6 at 150 dpi and
reading the block by eye, alongside items 6–9 (`Operation Force: 50±15gf`,
`Pre travel: 1.7±0.4mm`, `Total travel: 3.0±0.2`, `Operation Life:60,000,000
Cycles(min)`), the title block (`KS-33 (Low Profile Red Switch 2.0)`, Part No
`KS-33H10B050NN-Y24`, Version 2, 2023-01-03, scale 5:2, third angle, sheet
`DS-02-001-A0`) and the plate-grip dimension `1.20 ±0.05`. The entry's
`derivation`, its sheet reference and its item number are all exactly right,
and so is the claim that no render is needed for this one.

**The conditional is preserved where it matters.** The `value` string itself
carries `at 16 in/sec actuation`, so a citation cannot drop it, and the owner
page goes further: *"It is a maximum at a stated actuation speed, not a
typical, and 16 in/sec (≈0.41 m/s) is a brisk keystroke"*
`[repo] docs/reference/ks33-geometry.md:220`. `[calc]` 16 in/s × 0.0254 =
0.4064 m/s — correct. **Nothing in the corpus uses the figure as
unconditional**: `latency-budget.md:126,148` and `ROADMAP.md:121` all carry
"at 16 in/sec", and 148 explicitly frames it as *"an unmeasured maximum"* whose
typical M1 must still measure. That part of the fix is complete and good.

### 2.2 D8-1 — the ROADMAP still says it is not published

`[repo] ROADMAP.md:71`, the M1 row:

> … **bounce and the actuation/reset hysteresis gap scoped** on fast press,
> slow press, fast release, slow release and a worn switch — **neither is
> published**; …

`[test]` I ran all five of the entry's patterns over the corpus with the
checker's own joined-stream logic: **every one matches zero places, including
this line.** `[test]` `python3 tools/check-staleness.py` → `PASS no live stale
values`. `[test]` the probe string `neither is published` matches exactly one
place in the corpus — `ROADMAP.md:71` — and `[test]` its ±300-char window
contains no `REFUTATION` marker and no shouted `NOT`, so a pattern added for it
would be reported **live**, not exempted.

This is the entry's whole purpose failing on the fourth spelling. Three
documents asserted the figure was unpublished; the fixer corrected three
documents — `ks33-geometry.md`, ADR 0002, `latency-budget.md` — and wrote one
pattern per spelling **found in those three**. `[git]` The ROADMAP's own §112
paragraph was corrected a wave earlier in `cfcdc6e`, so the file was known to
be in this fact's blast radius; the M1 *row* has carried "neither is published"
since `7a5236c` and has never been touched. The result is one file
contradicting itself 50 lines apart, on the milestone whose job the figure
changes.

It also makes M1's stated exit criteria wrong in substance: `ks33-geometry.md`
says M1's job *"changes from 'find out whether there is a number' to 'measure
the typical at a musical actuation speed, and confirm it comes in under the
published maximum'"* `[repo] ks33-geometry.md:221-223`, and the M1 row still
sets the old job.

Suggested pattern, given that the hysteresis half of that row is still true and
must survive the rewrite: `"— neither is published"` (dies when the row is
rewritten to "the hysteresis gap is not published"), or `"gap scoped"` if the
intent is to force the whole row through review. Not `"is published"` and not
`"published"`.

### 2.3 D8-3 — one surviving pattern will fire on a true sentence

`forbidden` also contains **`"bounce duration and the reset point"`**
`[repo] config/figures.yaml:641`. `[git]` It was grepped honestly — it is
ADR 0002's original wording, `git show 7a5236c:docs/decisions/0002-…:188`
reads *"publish.** Travel and force are specified; bounce duration and the
reset point"*. But the pattern captured the **subject**, not the assertion. The
predicate ("are not published") is outside it.

So the pattern now matches any sentence containing that noun phrase — including
the sentence M1 is supposed to grow: *"scope the bounce duration and the reset
point on fast press, slow press…"*. That is precisely what
`ROADMAP.md:71`/`ADR 0002:229-233`/`latency-budget.md:148` all tell M1 to do.
The entry's own `false_positive_note` states the rule this breaks:

> THE RULE BOTH BREAK: every pattern here must be specific to BOUNCE. Match the
> words that assert THIS figure is unknown.

Two patterns were withdrawn within twenty minutes for firing on true sentences;
a third with the same defect survived because, unlike `20 ms` and `Gateron does
not publish`, it happened to have no live hit **yet**. Its cheapest fix, when
it does fire, will be to make M1's row worse. Recommend replacing it with
`"bounce duration and the reset point are not"` or dropping it — ADR 0002's
old spelling is gone and this pattern is protecting a corrected file.

The other three survivors (`does not publish contact bounce`, `bounce is not
published`, `no published bounce figure`) are assertion-shaped and specific to
bounce; I could construct no true sentence containing any of them.
`bounce, which Gateron does not` is assertion-shaped too but leaves its verb
outside the match — the same shape as D8-3, one degree less exposed, because a
true sentence would have to put "bounce," immediately before "which Gateron
does not". Low risk; worth tightening to `"bounce, which Gateron does not
publish"` while the entry is open.

### 2.4 Patterns that can never fire anywhere — checked, and my two entries are clean

`[test]` The sibling-slice defect reproduces: because `check_figures` takes its
exemption window as `text[at-300 : at+len(bad)+300]`, **the window always
contains the match itself**, so a pattern carrying its own refutation marker is
exempt wherever it appears. Running `REFUTATION` and `REFUTATION_SHOUT` over all
218 patterns finds exactly three:

| figure | pattern | self-exempting via |
|---|---|---|
| `sensor-full-scale` | `0.2 → 4.8 V` | the `→` in `REFUTATION` |
| `loadswitch-fb-divider` | `VALUES NOT SET` | `REFUTATION_SHOUT`'s `\bNOT\b` |
| `diode-split-rationale` | `75 mV → LM317` | the `→` |

**Neither of my two entries is affected** — all eight of their patterns are
free of markers. I report the three because `sensor-full-scale` is
`breath-sensor-slope`'s companion and the arrow spelling is the one that would
guard the breath full-scale value in a drawing or a table cell. Confirming
independently: this is a real defect, and the register is carrying three
instances.

### 2.5 D8-7 — this figure's owner is not actually checked

`[test]` `.staleness/report.txt`:1-11, section *"figure owners this check CANNOT
verify (8)"*:

> `[ks33-contact-bounce] value '5 ms max at 16 in/sec actuation' has no token
> distinctive enough to locate - owner docs/reference/ks33-geometry.md is
> UNCHECKED`

`check_owners` takes numeric tokens of ≥3 characters; `5` and `16` are shorter,
and there is no `IDENT-STYLE` token, so the new entry joins the seven
pre-existing unverifiable owners. The claim happens to be true — `[repo]
docs/reference/ks33-geometry.md:206` states it in the Published-specification
table, and `:211-229` states the provenance and the consequence — but nothing
mechanical asserts it, so if `ks33-geometry.md` is ever split (and this corpus
splits pages), the owner can rot silently. This is the failure mode the check
was added for.

Cheapest fix without touching the tool: give the value a token the check can
anchor on — `5 ms max at 16 in/sec (0.406 m/s) actuation` makes `0.406`
distinctive and keeps the sentence true `[calc] 16 × 0.0254 = 0.4064`.

### 2.6 Every place the corpus writes this value

| Place | Form | Cites? |
|---|---|---|
| `docs/reference/ks33-geometry.md:206` | table row `5 ms max, at 16 in/sec actuation speed` | owner statement — correct |
| `docs/reference/ks33-geometry.md:214` | the verbatim vendor quote | owner provenance — correct |
| `docs/decisions/0002-key-switches-and-mounting.md:218` | `` `ks33-contact-bounce` `` | **cites by id — the only one in the corpus** |
| `docs/reference/latency-budget.md:126` | `5 ms max bounce at 16 in/sec` | restates; cites the *file* `ks33-geometry.md`, not the figure |
| `docs/reference/latency-budget.md:148` | `5 ms max at 16 in/sec actuation` | restates; cites the *file* |
| `ROADMAP.md:121` | `5 ms max at 16 in/sec` | restates; cites the PDF path |
| `ROADMAP.md:71` | *"neither is published"* | **contradicts it — D8-1** |
| `docs/reference/repo-maintenance.md:132-133` | the verbatim quote | restates, as a method anecdote — legitimate |
| `hardware/bom.csv:40` + `hardware/cluster/bom.csv:3` | `bounce time 5 msec max at 16 in/sec` in `PLATE-TOP`'s notes | restates ×2 (fragment + generated master) |

**One citation, six restatements, one contradiction.** Rule 1 is not met for
this figure. The three that matter are `latency-budget.md:126` and `:148`,
because that page is where the consequence is argued and it is the page a
reader lands on, and the `PLATE-TOP` BOM notes, because they are in the
most-cited file and will be copied forward.

`datasheets/MANIFEST.csv` and `.manifest-R7.csv` also carry the figure, and
that is correct and outside the corpus scan — a manifest row describing what a
banked document contains is provenance, not a derived statement.

---

## 3. The followed-through consequence, verified independently

**The reasoning is right.** `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:316`:
*"Require two consecutive agreeing samples before a note-on. At the 4 kHz loop
rate that is 250 µs of added latency"*. `[repo] docs/reference/latency-budget.md:99`
books it as a `+250 µs` row, *"One whole loop period, required by ADR 0001"*.
`[calc]` 5 ms ÷ 250 µs = **20**, so "twenty times shorter" is exact, and both
samples of the gate fall inside one bounce burst with 4.75 ms to spare. The
gate cannot reject bounce. `[repo] latency-budget.md:125-135` and
`[repo] ks33-geometry.md:226-229` both state it, and both correctly identify
the consequence — rejecting bounce is the release filter's job, and the release
window must outlast 5 ms rather than the RC.

`[repo] latency-budget.md:109` — the key path totals 0.372–0.622 ms against the
5 ms target, and `[calc]` 0.25 + 0.032 + 0.25 + 0.02 + 0.06 + 0.01 = 0.622 ms
checks. The gate is affordable; nothing about the bounce figure threatens the
budget. The conclusion is sound.

**Where it did not land.**

- **ADR 0001 — not at all, and one sentence is now backwards.** `[repo]
  0001:318-319`: *"(The chain now has its own SPI host, so it could be scanned
  faster than the output loop if the measurement at M1 says bounce demands
  it.)"* Scanning faster makes the two-sample gate span **less** wall-clock
  time, so it rejects *less* bounce, not more. To reject a 5 ms burst the gate
  window has to be ≥ the burst, which is latency by construction — which is
  exactly why `latency-budget.md` concludes the release filter owns the
  problem. The parenthetical is a live, unrefuted offer of a remedy that cannot
  work, on the page that specifies the gate. `[git]` ADR 0001 was not touched
  by the fix batch for this fact. This is the semantic residue CLAUDE.md §5
  says no grep will find, and it is in the ADR that both other pages cite.
- **`firmware/README.md` — untouched.** `[git]` `git diff 0e68f25~1..HEAD --
  firmware/README.md` is empty. `[repo] firmware/README.md:25-28` still says
  only that the release window is *"set from measured KS-33 bounce (milestone
  M1), not from the conventional 20 ms the 2021 firmware used"*. That is not
  wrong, and the register's `companion` field describes it accurately — but
  the two things the new figure adds are absent: that there is now a
  **published maximum the measurement must come in under**, and that the
  note-on gate ADR 0001 requires **is not a debounce and does not reject
  bounce**. The gate is not in the firmware constraints list at all
  `[test] grep -n "two consecutive\|note-on gate\|agreeing samples\|250 µs"
  firmware/README.md` → no hits. The one document that will be read while the
  debounce is actually written knows neither half.
- **ADR 0002 — cites the figure, does not carry the consequence.** `[repo]
  0002:217-233` is a good fix: the bounce half is corrected, the hysteresis
  half is kept as still-unpublished, the old sentence is preserved as a dated
  refutation, and it is the corpus's only citation by id. But its forward
  statement is still *"The gap still needs a scope, and it sets the debounce
  windows"* — the gap, not the bounce. A reader of ADR 0002 alone does not
  learn that the release window now has a published floor.
- **`ROADMAP.md` M1 — D8-1, the opposite of landed.** §112's paragraph carries
  the consequence well (including, honourably, that the ~0.3 mm hysteresis gap
  scaled off an undimensioned chart *brackets* rather than settles it); the M1
  row it is explaining still says neither figure is published.

### D8-2 — found on the way, and worse than what I was sent to check

`[repo] docs/reference/latency-budget.md:133`, inside the bounce-consequence
paragraph itself:

> … the release window has to outlast the bounce burst rather than **the 125 µs
> the key network's RC contributes**.

`key-release-time` is tracked at **119.9 µs** `[repo] config/figures.yaml:218`,
owned by `hardware/cluster/key-switch-network/key-switch-network.md`, whose
derivation table says *"crosses `V_IH` at **119.9 µs**"* `[repo]
key-switch-network.md:105`. `[git]` 125 µs is the **superseded** value: `git
show 7a5236c:docs/decisions/0001-…:225` reads *"103 µs; crosses `V_IH` at
**125 µs**"*, and the register carries three patterns against it —
`` "`V_IH` at **125" ``, `"at ~125us"`, `"~125us"`.

All three miss this spelling. `[test]` no pattern in the register matches
`latency-budget.md:133`, and `[test]` the string `125 µs the key network's RC`
has no refutation marker in its window, so it would report **live**. `[git]`
the sentence was written in `c65083d` — *inside this fix batch*, in the
paragraph added to carry the bounce consequence.

And a second instance, on the owner's own page: `[repo]
key-switch-network.md:112` — *"The **125 µs** release filter is half a scan
period and costs nothing musically"* — seven lines below the table that says
119.9 µs. `[test]` also unmatched, also unexempted. `[git]` It predates the fix
batch (`d88837b`, `7a5236c`), so the 2026-09-21 correction of that figure
changed the table and left the prose.

The ambiguity worth naming, because it is what will make this hard to fix:
125 µs is *also* the mean sampling latency, 250/2, and `latency-budget.md:59,97`
use it correctly in that sense. So `"125 µs"` is exactly the pattern that must
**not** be added — it would fire on two true sentences. `[test]`-verified
candidates that hit only the two stale sites: `"125 µs release filter"` and
`"125 µs the key network's RC"`.

`key-release-time` belongs to another slice; I report it here because the worse
of the two instances is in the paragraph this slice was sent to verify, and
because its `escape_note` is specifically about spellings — *"every pattern
above was written from a prose page … and the BOM rows spell the same numbers
'~125us'"*. The lesson was drawn one level too narrow: the escape was not
CSV-versus-markdown, it was **the register's patterns are written from the
sentences the fixer edited**. Both `125 µs` survivors are prose, in files the
fixer had open.

---

## 4. D8-6 — the BOM still confirms the refuted span

`[repo] hardware/bom.csv:42` and its fragment
`hardware/interfaces/breath-sense-link/bom.csv:2`, in `U-BREATH`'s notes:

> *"Full scale CONFIRMED as 0.2 to 4.8V on the cover page."*

`[datasheet]` the cover page does say `0.2 to 4.8 V Output` (p.1, under
`MPXV4006 | 0 to 6 kPa (0 to 0.87 psi)`), so the sentence is literally true
about the cover page. But the corpus's settled position is that the cover page
is **refuted by the transfer function inside the same document**: `[repo]
0003:102` and `0003:123`, and `sensor-full-scale` is 0.265–4.864 V with a
`forbidden` list of thirty-odd spellings of the 0.2/4.7/4.8 family. The word
**CONFIRMED**, in the notes cell for the part, asserts the design's full scale
is the cover-page span.

`[test]` no `sensor-full-scale` pattern matches anywhere in `hardware/bom.csv`.
The list contains `"0.2-4.80 V"`, `"0.2 – 4.80 V"`, `"0.2–4.80 V"`,
`"0.2 → 4.8 V"`, `"0.2 to 4.8 V out"` — and the BOM spells it **`0.2 to 4.8V`**,
no space before the `V` and no trailing `out`. Missed by one character, in the
CSV, which is the trap CLAUDE.md §2 names first and which this figure has
already been caught by once. `[test]` the ±300-char window around it holds no
refutation marker, so a pattern would report live.

Same row, for whoever fixes it: *"Table 3 of the datasheet"* is cited for the
port convention, but the banked Rev 3 document's port/marking information is
not in a table numbered 3 — Table 1 is Operating Characteristics and Table 2 is
Maximum Ratings `[datasheet] pp.3-4`. I did not chase which table it is; flagging
it for the BOM slice rather than claiming it is wrong.

---

## 5. D8-9 — two sizes for one text layer

- `[repo] config/figures.yaml:678` (`plate-thickness.derivation`): *"the
  document as a whole yields **9,680 characters** of prose"*.
- `[repo] docs/reference/ks33-geometry.md:216`: *"It yields **11 kB** of it"*.

`[test]` measured with PyMuPDF: **11,053 characters** over six pages
(1,266 / 2,199 / 1,356 / 3,916 / 1,495 / 821). Whitespace-stripped it is 9,375;
ASCII-only 10,976. So `ks33-geometry.md` is right, and 9,680 matches none of
the obvious measures — probably a different extractor. Trivial in itself; worth
one line because it is two corpus files stating one quantity two ways, which is
the condition rule 1 exists to prevent, and because the number is load-bearing
rhetoric: it is the evidence for *"Do not re-conclude the file is unreadable."*
Cite one or drop the digits.

Related, and a claim I would not want to see harden: `[repo]
ks33-geometry.md:232-235` says the hysteresis gap *"cannot be derived from the
published numbers"*. `[datasheet]` sheet 6's Force-Travel diagram is **gridded**
— Force 20–120 gf, Travel ticks at 1/2/3 mm — with leader-labelled operating
and reset points, and `ROADMAP.md:121-124` already scales ~0.3 mm off it.
"Not dimensioned" is true; "cannot be derived" is the same shape of sentence as
"Gateron does not publish contact bounce", and the ROADMAP paragraph is the
better version of it. Suggest `ks33-geometry.md` adopt the ROADMAP's wording.

---

## 6. What else should be tracked — ranked

Two structural notes first, because they explain why the advisory's 233 rows
cannot be read as the candidate list:

- **`NUM_UNIT` has no `kPa`, no `gf`, no `in/sec`, no counts and no bits.**
  So the advisory could never have nominated **either** of the two figures this
  slice reviews — not `0.7665 V/kPa` and not `5 ms max at 16 in/sec`. The whole
  breath-pressure domain is invisible to it.
- **`known` is polluted by single digits from other entries' values.**
  `check_restated` adds every `\d+\.?\d*` token from every `value`, so
  `umbilical-pinmap`'s `"1,2 … 3,6 … 4,5 … 7,8"` puts `1`–`8` into `known`
  corpus-wide, and `loop-budget`'s `"196-241 us of 250 us"` adds `250`. That
  suppresses **`4 kHz` (15 files)**, **`5 ms` (10 files)** and **`250 µs`
  (9 files)** — the three most-restated quantities in the instrument, all
  untracked, none of them in the advisory's output. Every one of them would
  otherwise rank above every row the advisory does print.

Ranked by (restatement count × consequence of being wrong × evidence it has
already moved):

1. **The loop rate, 4 kHz / 250 µs period.** 15 files `[test]`. Decided in
   `ADR 0006:262-263`, restated in ADRs 0001, 0003, 0004, 0008, 0012, 0013,
   `latency-budget.md`, `firmware/README.md`, `breath-adc.md` and BOM rows.
   **It has already moved once and left a documented stale derivative**: ADR
   0003:423 — *"The 0.6 MHz this table used to give came from a 2 kHz mod rate
   and five channels"* — and ADR 0004:65 is still cleaning up after the same
   move. Everything downstream is derived from it: `loop-budget`,
   `key-press-time`'s 42× margin, the note-on gate's 250 µs, the anti-alias
   corner, the SPI rate. It is the strongest untracked candidate in the corpus
   by any measure. Owner: ADR 0006; `latency-budget.md` derives `loop-budget`
   from it and should cite.
2. **The end-to-end latency target, 5 ms.** 10 files `[test]`
   (`latency-budget.md` ×4, ADR 0001:317, ADR 0003:35, `breath-adc.md:69`).
   Every "×N of budget" claim in the corpus is a ratio against it — 1.6×, 8×,
   a twentieth, 5.6 % — so if it moves, every one of those numbers is wrong at
   once and none of them is guarded. **And it now collides with
   `ks33-contact-bounce`:** `5 ms` means the latency target in six places and
   the bounce maximum in four. A future `forbidden: ["5 ms"]` would fire on
   both, and the cheaper fix would be to break a true sentence — the trap
   CLAUDE.md §2 names last. Track it *now*, while a distinctive spelling can
   still be chosen (`"5 ms target"` / `"5 ms budget"`). Owner:
   `latency-budget.md:20`.
3. **The 74HC165 input thresholds, `V_IH` 2.31 V / `V_IL` 0.99 V.** 4-5 files
   each `[repo] key-switch-network.md:52,77-78`, `0001:208,221`, plus
   `bom.csv`'s `C-KEY` row spelling them `"(0.99V at 3.3V)"` and `"(2.31V)"`.
   **They are the direct inputs to two tracked figures** (`key-press-time`,
   `key-release-time`) and are themselves untracked — the exact
   `breath-zero-ref` shape, where an untracked quantity derived from
   datasheets feeds tracked ones and "has no protection at all". CLAUDE.md §3
   records that these numbers **have already been wrong twice in one day**
   (the 0.75/0.25 extrapolation, then back). The tracked children carry
   `threshold_note` prose about them; the numbers themselves are loose in five
   files and two spellings. Owner: `key-switch-network.md:52`.
4. **The sensor pedestal, 0.265 V.** 6 files `[test]` and in the advisory,
   because `sensor-full-scale`'s `value` is only `"4.86 V"` — the pedestal is
   in its `derivation` and therefore not `known`. This is not hypothetical:
   `[repo] config/figures.yaml:167-189` records that when this number moved
   0.200 → 0.265 it *"followed it in two files, half-followed in a third and
   did not move in two more"*, producing three values for `breath-zero-ref` in
   five places. **The number that caused the corpus's best-documented
   five-place escape is still not itself a tracked figure.** Cheapest fix:
   widen `sensor-full-scale`'s value to `"0.265 V rest, 4.864 V at 6 kPa"`,
   which also puts `0.265` into `known` and stops the advisory reporting it.
5. **The 265 mm loom hop.** 11 files `[test]`, in the advisory. It carries the
   HC-versus-LVC decision (`0001:178,377`, `key-register.md:60`), the
   `F-CHAIN` polyfuse proposal (`carrier.md:286`), the 2.2 kΩ pull-up's
   expired justification (`key-switch-network.md:126`) and the cluster table
   (`0013:179`). A mechanical quantity that four electrical arguments rest on,
   and the body length is not yet frozen. Owner: `0013:179` or
   `key-chain-loom.md`.
6. **`11.45 V`, the `CLR` failure voltage.** 5 files including
   `firmware/README.md:57` `[test]`. `[calc]` 4 × 2.8625 with `Voffset` at 0 —
   i.e. a pure derivative of `mod-reference` (3.3333 V, tracked), restated in
   five places and guarded nowhere. Same shape as #3 and #4: tracked parent,
   unprotected child. When `mod-reference` moved 2.5 → 3.3333 V this number
   moved with it; next time there is nothing to say so.
7. **`2.500 V`, the DAC8568 internal reference.** 8 files `[test]`, in the
   advisory. Every CV scaling chain starts here and `ADR 0006` is still
   deciding internal-versus-external. Lower rank only because it is a
   datasheet constant rather than a derived one.
8. **`482 Hz` / `480 Hz`.** 6 files each `[test]`, both in the advisory,
   appearing in the same three files (`0006`, `latency-budget.md`,
   `breath-sense-link.md`). Two numbers 0.4 % apart for what looks like one
   corner — either one quantity spelled two ways (a defect) or an ideal and an
   E24-realised value (needs one sentence saying which is which). **Settled
   by:** reading the two derivations side by side; I did not, and would not
   want this rank trusted without it.

Not worth tracking, against the advisory's louder rows: `1.25 mm` (17 files) is
the 0805 footprint, `1.27 mm` the SOIC pitch, `2.54 mm` the header pitch, `1.6 mm`
the PCB thickness, `20 K` a thermal rise written in eight unrelated places,
`0.1 %` a resistor tolerance class, `3.3 V` a rail *name* with a dozen distinct
referents. `14.0 mm` and `1.70/3.00/12.2 mm` are vendor dimensions already
anchored by `plate-thickness`'s provenance note and the manifest row. Package
dimensions and tolerance classes do not go stale; they are coincidences of
spelling, and adding them would be the "unusable noise floor" that left
`check_refdes` switched off for this tool's whole life.

---

## 7. Two smaller things, and what would settle what I could not

- **The register cites line numbers, and one has already rotted.**
  `[repo] config/figures.yaml:152` names `breath-adc.md:37`. `[git]` It was
  :37 when written in `df22096` and is **:40** today, one day later — three
  lines were inserted above it. `0003:117` and `:123` are still accurate. Line
  numbers are the one reference form guaranteed to rot; the same note could say
  *"the `real play` line of breath-adc.md's Divider block"* and never need
  maintaining.
- **Both `note` fields say `TRACKED 2026-09-21`** `[repo]
  config/figures.yaml:145,658` while this wave's framing dates them
  2026-09-22. `[git]` The commits (`df22096`, `04b5208`) are both authored
  2026-09-21, so the entries are right and no change is needed — recording it
  so the next reader does not "fix" a correct date.

**What would settle the uncertain claims above.** (1) D8-2's `key-switch-network.md:112`
— whether "the 125 µs release filter" means the RC or a firmware half-period
filter. I read it as the RC because the paragraph is about the RC and because
`[git] 7a5236c` shows 125 µs *was* that figure, but the author knows. If it is
a firmware filter, it is an untracked quantity colliding with a tracked one,
which needs a different fix and not a pattern. (2) #8 above, the 480/482 Hz
pair. (3) Whether `0.6 V/kPa` in `breath-sensor-slope` was meant to be
something else — it matches nothing, has never existed in the tree, and I
cannot reconstruct what spelling it was aiming at.

**What I did not check:** `sensor-full-scale`'s and `key-release-time`'s
entries beyond the points where they touch these two figures; the rest of the
218 patterns beyond the self-exemption sweep in §2.4; ADR 0004's "6 channels"
versus ADR 0003's "7 channels" in the otherwise-identical SPI budget table
(`0004:62` vs `0003:420`), which looks like a third slice's finding.
