# D15 — `docs/reference/latency-budget.md`, rebuilt so the key path closes

Slice D15 of the fix-audit wave. Cold: nothing under `docs/review/**` was read
except this wave's `README.md`. Git log and diff were read.

Subject: the key path rebuild in **c65083d** *"docs/reference/ catches up with
the restructure"*, plus everything downstream of it.

Provenance marks on every claim: `[repo] path:line`, `[calc]` with the
arithmetic shown, `[datasheet]` with document and page, `[test]` with the
command, `[from memory]`.

---

## Verdict in one paragraph

**The fix is correct where it is arithmetic and wrong where it is argument.**
Every number added to the key path re-derives, the total follows from the rows
to the digit, and the two terms it added really are 80 % of the path. But the
same edit (a) wrote a **stale `125 µs`** into the one sentence that carries the
bounce conclusion, against a figure tracked at 119.9 µs since before the batch;
(b) books the DAC step **46 µs cheaper than the breath table books the same
operation**, in defiance of the rule stated four lines above it; (c) concluded
**"the key path is not the one at risk"** while leaving unbooked the key path
that two other corpus documents identify as the risky one — the
**release-initiated** note change, which does not close against 5 ms; and
(d) sized the release filter from the 5 ms bounce figure when `ROADMAP.md` and
ADR 0002 both say the dominant release term is the **unpublished reset gap**, at
tens of milliseconds. Separately, **ADR 0003 still carries a complete, stale
copy of this page's own budget** — `< 1.5 ms` total, `50–200 µs` ADC — untouched
by the batch, and one of its values is a `loop-budget` forbidden pattern that
the checker **structurally cannot match** because the value sits in a table cell
with pipes. Checker verdict today: `PASS`.

---

## 1. The key path, re-derived independently

`[repo] docs/reference/latency-budget.md:93-104`. Row by row, finger to CV out.

| Row | As booked | Independent check | Verdict |
|---|---|---|---|
| Switch mechanical actuation | "mechanical" | non-numeric | ok |
| Key network RC, press | `key-press-time` | register: **5.92 µs**, τ = (2.2 kΩ ∥ 100 Ω) × 47 nF = 4.4957 µs `[repo] config/figures.yaml:239-245`; owner states 5.92 `[repo] hardware/cluster/key-switch-network/key-switch-network.md:106` | ok — and **cited, not restated**, which is rule 1 done right |
| Sampling period | 0–250 µs | `[calc]` 1/4 kHz = 250 µs; 4 kHz pinned at `[repo] firmware/README.md:22` | ok |
| 74HC165 chain read | 32 µs | `[calc]` 32 bits / 1 MHz = 32 µs; 1 MHz and 32 bits from `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:300,196` | ok |
| Note-on gate | +250 µs | ADR 0001 verbatim: *"Require two consecutive agreeing samples before a note-on. At the 4 kHz loop rate that is 250 µs of added latency — inaudible, and a twentieth of the 5 ms budget"* `[repo] 0001-mcu-and-board-partitioning.md:316-318`. `[calc]` 250 µs / 5 ms = 1/20 ✓ | **faithful to the ADR**, and the old row it replaced ("Debounce (press) — 0, fire immediately") really did contradict it |
| Debounce (release) | "filtered" | no number anywhere in the corpus — see §3 and §6 | **load-bearing blank** |
| Firmware note resolution | < 20 µs | no citation; identical to ADR 0003's row of the same name `[repo] 0003-breath-sensing-path.md:22` | assertion |
| DAC update + settle | ~60 µs | **disagrees with this page's own breath table by 46 µs** — see finding D15-4 | **defect** |
| Pitch filter | ~10 µs | `[calc]` 1/(2π × 15.9 kHz) = 10.01 µs; 15.9 kHz corner confirmed `[repo] hardware/module/pitch-stage/pitch-stage.md:134` | ok |

### Does the total follow from the rows?

`[calc]` Worst case `0.250 + 0.032 + 0.250 + 0.020 + 0.060 + 0.010 = 0.622 ms`.
Best case, sampling at zero: `0.372 ms`. Both match the stated `[calc]` line
`[repo] :106-108` **exactly**. Adding the cited RC press time: `0.622 + 0.00592
= 0.6279 → ~0.63 ms` and `0.372 + 0.00592 = 0.3779 → ~0.38 ms`, which is
precisely the table's `~0.38–0.63 ms` `[repo] :104`. So the table total and the
`[calc]` line differ by exactly the RC term, and both are internally right.
`[calc]` 5 / 0.622 = 8.04× ✓ "roughly 8×". `[calc]` 0.50 / 0.62 = 80.6 % ✓
"80 % of the path". **The arithmetic of this fix is clean.**

### One thing the derivation gets right that is worth recording

The 32 µs chain read is booked **once** while the gate needs **two** reads, and
that is correct, not an omission. `[calc]` closure at t₀; pass N starts at
t₁ ∈ [t₀, t₀+250); pass N+1 starts at t₁+250 and its read ends at t₁+282; then
20 + 60 + 10 → t₁+372. Total = (t₁−t₀) + 372 = 372–622 µs. The second read's
32 µs is the only one outside the 250 µs period, and that is the one booked.
Whoever built this row got the queueing right.

### Terms still omitted from the press path

- **Marker-check retry.** ADR 0001: a frame failing its marker *"holds the
  previous frame"* `[repo] 0001:325-327`. A held frame costs one more loop
  period and restarts the two-agreeing-sample gate: **+250 µs**, unbooked. Fault
  case, so low priority — but it is a latency term and the page's stated policy
  is that the table carries terms "so the table is complete".
- **Bounce delaying the gate** — finding D15-12, and not low priority.

---

## 2. The other paths — nobody has checked whether they close

Both breath tables *do* have totals `[repo] :44, :65`. Neither total is right.

**D15-6 — the breath digital total does not follow from its rows.**
`[calc]` from `[repo] :56-65`: `282 + 250 + 24 + 20 + 96 + 10 + 82 = 764 µs`;
plus the stated 2.17 ms to the sensor output = **2.934 ms worst case**, and with
the sampling period at zero **2.684 ms**. The table states **"~2.9–3.1 ms"**.
The low end is the *worst* case and the high end is **170 µs that no row
produces**. This matters beyond rounding: the page's headline margin claim —
*"about 1.6×"* `[repo] :23, :84` — is `[calc]` 5 / 3.1 = 1.61, i.e. **the
margin figure is computed from the un-derivable end of the range**. Against the
rows it is 5 / 2.934 = 1.70×. The same 1.6× has been propagated into ADR 0003
`[repo] 0003-breath-sensing-path.md:35`. *What would settle it:* whichever term
was intended at ~170 µs — most likely a second filter pole or a driver
allowance — needs a row, or the range needs to become 2.68–2.93.

**D15-7 — line 49 contradicts the table above it.** The prose says *"The real
figure is 632 µs"* for the two breath poles `[repo] :49`. `[calc]` the table's
own rows are 330 + 332 = **662 µs** `[repo] :42-43`, and
1/(2π×482) + 1/(2π×480) = 330.2 + 331.6 = 661.8 µs. 632 is 30 µs short and
matches nothing; it looks like the pre-482 Hz era (`[calc]` 2 × 318 = 636 for
two 500 Hz poles). Corners themselves verified: 482 Hz `[repo]
hardware/interfaces/breath-sense-link/breath-sense-link.md:150`, 480 Hz
`[repo] :154`, 564 Hz `[repo] hardware/carrier/breath-adc/breath-adc.md:62`,
1.94 kHz `[repo] hardware/module/mod-channels/mod-channels.md:115`. All four
agree with the latency page.

**D15-8 — the analog total omits a row, the same way the key path used to.**
`[calc]` 1.17 + 1.0 + 0.330 + 0.332 = 2.832 → "~2.83 ms" `[repo] :44`, which
means the **"Buffer and cable propagation < 10 µs"** row `[repo] :41` is not in
its own table's total (with it, 2.842 → ~2.84). Small, but it is the exact
defect shape this page was rebuilt to remove.

**D15-8b — and the section below the table restates a third number.** "**2.80 ms**
against a 5 ms target" `[repo] :76` against the table's ~2.83 ms `[repo] :44`
and the prose's 3.1 ms `[repo] :81`. Three totals for the breath path on one
page.

**D15-9 — the transducer's ~1 ms is called a datasheet figure and the banked
datasheet has no such row.** `[repo] :39` books ~1 ms; the characterisation
table calls it *"A large term and a datasheet figure"* `[repo] :146`; ADR 0003
books the same ~1 ms `[repo] 0003:21`. The part is the MPXV4006DP `[repo]
0003:99`, banked and SHA-verified `[test] python3 tools/verify-datasheets.py →
"78 verified, 23 recorded as blocked or not-fetched, 0 problems"`.
`[datasheet] datasheets/analog/MPXV4006DP.pdf`, MPXV4006 Rev 3 1/2009, 22 pp,
**Table 1 Operating Characteristics, p.3**: Pressure Range, Supply Voltage,
Supply Current, Full Scale Span, Offset, Sensitivity, Accuracy — **there is no
response-time or rise-time row**. `[test] pymupdf` over all 22 pages: the text
layer yields 19,556 characters and the strings `response` / `Response` /
`Rise` / `rise` / `10% to 90` appear **nowhere**, and `ms` appears once, in
boilerplate on p.22. So the second-largest term in the breath budget is an
unsourced assertion presented as a datasheet number. This is CLAUDE.md §3's
exact pattern — the 74HC165's absent 3.3 V row — on a document that is already
banked and already readable. *What would settle it:* either a Freescale
MPXV4006/MPX4006 revision that does tabulate response time, cited by page, or
the E-track step response measurement; until then the row should be marked
`[from memory]`, not `[datasheet]`.

**Paths that exist and are not booked at all:** the release-initiated note
change (§3, D15-3) and any IMU/tilt → mod-CV path. The page books the mod
reconstruction filter `[repo] :64` but no mod *acquisition* path; whether that
needs a row depends on ADR 0007's sample rate and is not asserted here.

---

## 3. The note-on gate, and whether the release filter is sized for bounce

### The gate argument checks out against ADR 0001's actual wording

`[repo] :125-135` claims (a) ADR 0001's gate is two samples 250 µs apart,
(b) Gateron publishes 5 ms max bounce, (c) 250 µs is twenty times shorter,
(d) both samples can fall inside one burst, (e) therefore rejecting bounce is
the release filter's job. (a) is verbatim ADR 0001 `[repo] 0001:316-318`.
(b) is verbatim the vendor drawing via the register: *"Bounce Time: 5msec
Max.(at 16 in/sec. actuation speed)"* `[repo] config/figures.yaml:635-641`,
owner `[repo] docs/reference/ks33-geometry.md:206`. (c) `[calc]` 5000/250 = 20 ✓.
(d) follows. **(e) is where it goes wrong — twice.**

### D15-13 — what the published bounce actually demands, and what the RC gives

`[calc]` A release filter that outlasts the published burst needs
**≥ 5 ms = 20 loop passes** at 250 µs, and a 20-agreeing-sample confirmation
costs 21 passes = **5.25 ms**.

`[calc]` The fitted 2k2/47 nF network gives **119.9 µs** (`key-release-time`,
τ = 2.2 kΩ × 47 nF = 103.4 µs, crossing `V_IH` = 2.31 V) `[repo]
config/figures.yaml:216-222`. That is **0.48 of one loop pass**, and
5 ms / 119.9 µs = **41.7× short**. The RC contributes nothing to bounce
rejection.

`[calc]` For the RC *alone* to span 5 ms: τ = 5 ms / ln((3.3−0.1435)/(3.3−2.31))
= 5 / 1.1596 = **4.31 ms**, i.e. C ≈ **1.96 µF** at 2.2 kΩ — 42× the fitted
47 nF. The press then charges through the parallel combination:
τ_press = 95.65 Ω × 1.96 µF = 187 µs, crossing `V_IL` at
187 × ln(3.1565/0.8465) = **246 µs** — **the entire scan period**, destroying
the asymmetry the design exists to protect.

**So the page's conclusion is right and its proof is missing.** Bounce rejection
cannot live in the RC, must live in firmware, and must be asymmetric — and that
is the three-line calculation the page gestures at ("rather than the 125 µs the
key network's RC contributes") without ever doing. Worth adding; it is the only
place in the corpus where the 47 nF's *inadequacy* as a bounce filter is
quantified, and `[repo] hardware/cluster/key-switch-network/key-switch-network.md:122`
still calls it "a bounce filter" unqualified.

### D15-10 — the 5 ms figure does not size the release window, and two documents say so

`[repo] :134-135` — *"the vendor maximum is now the number M1 has to come in
under"* — and `[repo] :148` — *"the published maximum alone buys back 15 ms of
the release filter"* (`[calc]` 20 − 5 = 15). Both are contradicted:

- `[repo] ROADMAP.md:114-118`: *"The release window was being sized from the
  wrong number. For an MX-style switch the dominant release-side effect is not
  contact bounce — it is the gap between the actuation point and the reset
  point... can park the plunger inside that gap and chatter for tens of
  milliseconds."* And `[repo] ROADMAP.md:123`: *"The hysteresis gap is still not
  stated numerically."*
- `[repo] docs/decisions/0002-key-switches-and-mounting.md:230-234`: the gap
  *"sets the debounce windows on the most latency-sensitive path in the
  instrument"* and *"a legato release can park the plunger in the hysteresis gap
  and chatter for tens of milliseconds."*

The 5 ms maximum bounds **bounce**; it does not bound the **release window**,
because the term that sets that window is unpublished and an order of magnitude
larger. "Buys back 15 ms" is only true if bounce were the binding constraint,
and the corpus says twice that it is not. The characterisation row `[repo] :148`
compounds it: *"measure bounce duration on press and release"* — it never names
the actuation/reset gap, which is the thing M1 is actually for `[repo]
ROADMAP.md:71, 112-125`.

### D15-3 — the path that does not close is the one left unbooked

`[repo] :100` books "Debounce (release) | filtered | **Off the attack path by
construction**, which is the point of the asymmetry", and `[repo] :121-123`
generalises it: *"Symmetric debounce puts its full window directly into the
attack, which is the one place latency is audible."* `[repo] ROADMAP.md:127-131`
refutes exactly that belief:

> *"And release latency is not free on a woodwind. On a keyboard, filtering the
> release costs nothing because the note is already sounding. Here fingerings
> are combinational: **lifting a finger is how you start the next note.** A
> 10 ms release window delays that new note by 10 ms, landing squarely in the
> territory the attack-latency work exists to protect."*

`[calc]` The release-initiated note change, with the release window W and every
other term from the key table: `W + 0.250 (sampling) + 0.032 (chain) + 0.020
(firmware) + 0.106 (DAC burst, see D15-4) + 0.010 (filter) = W + 0.418 ms`.

| W | Source | Total | vs 5 ms target |
|---|---|---|---|
| 5.25 ms | 21 passes, the published bounce maximum | **5.67 ms** | **fails** |
| 10 ms | ROADMAP's worked example `[repo] ROADMAP.md:129` | 10.4 ms | fails |
| 20 ms | the 2021 firmware's value `[repo] firmware/README.md:27` | 20.4 ms | fails |
| tens of ms | reset-gap chatter `[repo] ROADMAP.md:118` | — | fails |

**On the published vendor maximum alone, this path misses the target this page
exists to defend** — and the page's summary is *"The key path is not the one at
risk"* `[repo] :109-110`. That sentence is true of the press path and false of
the path ROADMAP names as the dangerous one. The mitigation ROADMAP proposes
(*"apply the release filter to the note decision, not to each key
independently"* `[repo] ROADMAP.md:133-135`) is not in this page either.

This is the **same defect the fix was written to repair**, on the sibling path:
a table with its largest term unbooked, no total, and a margin claim that reads
comfortably. Found on the press path, fixed on the press path, left on the
release path — the shape CLAUDE.md describes as "the fix lands where the editing
is happening and not where the reader looks".

### D15-3b — a downstream document asserts the booking that is missing

`[repo] docs/reference/ks33-geometry.md:226-227`, written in this batch
(`[test] git log -L 224,230:... → 79f5c4a "docs/reference/ lands, and two
conclusions reverse"`): *"The consequence is in `docs/reference/latency-budget.md`,
which **books the release-filter window** and now states what this bound does
to it."* The latency budget books no release-filter window. The row is the word
"filtered" and there is no number, no total and no path `[repo] :100`.

### D15-12 — the converse of the gate argument is unanalysed

The page shows the gate **cannot reject** bounce. It does not ask whether bounce
can **stall** the gate. `[calc]` A 5 ms burst spans 20 sample instants at 4 kHz;
the gate needs two *consecutive agreeing* samples, so if the chatter's open
intervals reach 250 µs the gate is not satisfied until the burst settles —
up to **+5 ms**, taking the press path to ~5.4 ms and blowing the target from
the side the page declares safe. ADR 0001 anticipates precisely this and the
latency budget does not carry it: *"The chain now has its own SPI host, so it
could be scanned faster than the output loop **if the measurement at M1 says
bounce demands it**"* `[repo] 0001:318-319`. *What would settle it:* the M1
bounce waveform — specifically whether open intervals inside a burst exceed
250 µs. Until then the key path's worst case is bounded by bounce structure, not
by 0.62 ms, and the page should say so.

---

## 4. Does the loop close, and are the two budgets consistent?

**Consistent where the batch made them so.** The ADC read is 24 µs in both the
breath table `[repo] :60` and the loop-duty rule `[repo] :177`; the key chain
read is 32 µs in both `[repo] :98, :177`; the DAC burst is 96 µs in both
`[repo] :62, :177`. `loop-budget`'s owner now states its value — *"one pass is
**196–241 µs of 250 µs**"* `[repo] :178` — which is the escape the register
records as having passed on the shared denominator alone `[repo]
config/figures.yaml:577-586`. That part of the fix landed.

**The 8 kHz refutation is sound.** `[calc]` 24 + 32 + 96 = **152 µs** of bus
time against a 125 µs period at 8 kHz ✓ `[repo] :175-178`.

**D15-14 — but 196–241 µs is not reproducible from anything the corpus states.**
The register's derivation is *"Bus time 148-155 us PLUS ESP-IDF
per-transaction overhead (24 us interrupt / 9 us polling)... 291 us with driver
defaults"* `[repo] config/figures.yaml:575`. `[calc]` The 291 µs pins the
transaction count: 148 + 6 × 24 = 292 ≈ 291, so N ≈ 6. The **same** N with
polling gives 148 + 6 × 9 = **202 µs** to 155 + 54 = **209 µs** — not 196–241.
Neither endpoint falls out of any N I can fit: N = 8 gives 220–227; N = 3 gives
175–182. The page states 152 µs of bus time, which is inside the register's
148–155 but is never reconciled with it, and the page states neither the
transaction count nor the overhead. So the corpus's most load-bearing timing
figure has a derivation field that does not produce its own value. *What would
settle it:* the planned transaction count, and in particular whether the six DAC
words are one acquired-bus burst (which is how `[repo] :62` books them) or six
transactions.

**D15-15 — the coupling between the two budgets is not stated.** `[calc]`
241 µs of 250 is 96.4 % duty: **9 µs of slack**. The key path's two largest
terms are both *one loop period*, so they scale 1:1 with any overrun — at a
275 µs period the key worst case goes from 0.622 to 0.672 ms, and the breath
digital path with it. The page says of the loop *"it is not comfortable"*
`[repo] :180` and, forty lines earlier, *"The key path is not the one at risk"*
`[repo] :109`. Both budgets are downstream of the same 250 µs, and nothing on
the page says the latency table is contingent on the loop closing — which, with
ESP-IDF driver defaults, the register says it does not `[repo]
config/figures.yaml:575`.

---

## 5. Completeness — does every document that reasons about debounce use `ks33-contact-bounce`?

`[test] grep -rn "ks33-contact-bounce" --include=*.md .` (corpus only) returns
**one** hit. One of six consumers cites it.

| Document | Status | Evidence |
|---|---|---|
| `docs/reference/ks33-geometry.md` (owner) | **owner, correct** | states 5 ms max at 16 in/sec `[repo] :206`, with the verbatim quote and sheet reference `[repo] :211-219` |
| `docs/decisions/0002-key-switches-and-mounting.md` | **followed** | cites the figure by id, states no number `[repo] :218` — the only document that does |
| `docs/reference/latency-budget.md` | **not followed** | restates the value twice, `[repo] :126` and `[repo] :148`, and cites the *owner page* rather than the figure. Not stale today; two copies positioned to go stale. Rule 1 violation |
| `firmware/README.md` | **not followed** | `[repo] :25-27` names no figure and no 5 ms — only *"measured KS-33 bounce (milestone M1)"* and the refuted 20 ms. The register's `companion` field asserts *"firmware/README.md sets the release window from measured bounce at M1, and this is the number M1 must come in under"* `[repo] config/figures.yaml:667-669`, and `[repo] latency-budget.md:133-135` asserts the same. **The file carries neither half of the relationship two other places claim it carries.** |
| `docs/decisions/0001-mcu-and-board-partitioning.md` | **not followed** | never mentions the figure. It is the document that *specifies the gate* the latency budget says cannot reject bounce, and its own argument still runs off the 20 ms comparison `[repo] :194`. Nothing in ADR 0001 tells a reader the gate is 20× shorter than the published burst |
| `hardware/cluster/key-switch-network/` | **not followed, and contradicts** | `[repo] key-switch-network.md:122` calls the 47 nF *"a bounce filter"* with no figure and no number — and D15-13 shows it is 41.7× too small; `[repo] :112` restates a stale 125 µs (D15-2) |
| `ROADMAP.md` M1 row | **not followed, and contradicts** | see D15-11 |

### D15-11 — `ROADMAP.md:71` still asserts the figure is unpublished, and the checker passes

`[repo] ROADMAP.md:71`, the M1 row: *"**bounce and the actuation/reset hysteresis
gap scoped** on fast press, slow press, fast release, slow release and a worn
switch — **neither is published**"*. Forty-nine lines later the same file says
*"Gateron **does** publish a bounce figure — **5 ms max at 16 in/sec**"* and
*"The hysteresis gap is still not stated numerically"* `[repo] ROADMAP.md:120-123`.
So "neither" is half wrong, inside the file that corrects it, in the **table row
a reader of the roadmap actually reads**.

Not caught, and this is why: the figure's five forbidden patterns are *"does not
publish contact bounce"*, *"bounce duration and the reset point"*, *"bounce is
not published"*, *"no published bounce figure"*, *"bounce, which Gateron does
not"* `[repo] config/figures.yaml:642`. None matches *"neither is published"* —
the spelling that survives is the one that names the quantity **by pronoun**.
`[test] python3 tools/check-staleness.py → "PASS no live stale values | corpus
123 files, 23 circuits, 37 figures / 218 patterns | 5 unresolved (tracked) |
233 restated-not-cited (advisory)"`. A candidate pattern that is bounce-specific
and does not fire on a correct sentence: `switch — neither is published`.

---

## 6. Provenance — how many rows trace to something

**Key path, 9 rows** `[repo] :93-104`:

- **3 cited**: RC press (`key-press-time` + named owner), chain read (ADR 0001 +
  `[calc]`), note-on gate (ADR 0001, verified verbatim at `0001:316-318`).
- **2 derivable from a rate stated elsewhere on the page**: sampling period
  (4 kHz), pitch filter (15.9 kHz, and the corner is confirmed at
  `pitch-stage.md:134`).
- **2 bare assertions**: "Firmware note resolution < 20 µs"; "DAC update +
  settle ~60 µs".
- **2 non-numeric**: mechanical actuation; release debounce.

**Load-bearing assertions, in order:**

1. **"DAC update + settle ~60 µs"** — 10 % of the worst case, and the *only*
   term in the key table that contradicts another table on the same page
   (finding D15-4 below). Nothing anywhere in the corpus states 60 µs.
2. **"Debounce (release) | filtered"** — the entire bounce conclusion (§3) rests
   on a window that **no document in the corpus states a value for**, and whose
   real magnitude (5 ms to tens of ms) is 8–30× the whole booked key path.
3. **"Firmware note resolution < 20 µs"** — inherited verbatim from ADR 0003's
   stale table `[repo] 0003:22`, i.e. its provenance is a table this page
   supersedes.

**Breath tables, 13 rows** `[repo] :36-65`: 6 `[calc]` from corners each
verified against its owner page (482/480/564 Hz, 1.94 kHz, 15.9 kHz, and the
96 µs burst as `[calc]` 6 × 32 bits / 2 MHz = 96 µs); 1 `[datasheet]` (MCP3202,
18 clocks at ~0.9 MHz on 3.3 V); 1 `[calc]` confirmed elsewhere (tube 1.17 ms at
400 mm, `[repo] 0003:256`); 1 honestly open (restrictor, "? — sized at E2");
**4 assertions** — transducer ~1 ms (misattributed to a datasheet, D15-9),
buffer/cable < 10 µs, SPI to MCU < 20 µs, DAC settling ~10 µs.

### D15-4 — the DAC row contradicts the page's own rule by 46 µs

`[repo] :102` books the key path's DAC step at **~60 µs**. `[repo] :62-63` books
the same operation, for the same six-channel refresh on the same bus, at
**~96 µs + ~10 µs = 106 µs** — and states the reason four lines above the key
table's own total: *"The loop refreshes all of them every pass, so the **whole
burst is the latency**, not one word"* `[repo] :62`, restated as a rule at
`[repo] :214-216`. There is no basis for the pitch channel escaping the burst;
it is one of the six.

`[calc]` Corrected: `0.250 + 0.032 + 0.250 + 0.020 + 0.096 + 0.010 + 0.010 =
0.668 ms` worst, `0.418 ms` best. Margin `5 / 0.668 = 7.5×`, not 8×; the
sampling-plus-gate share becomes `0.50 / 0.668 = 75 %`, not 80 %. Small numbers,
but the page's position is that a total the reader cannot check is the defect —
and 60 µs is a number the reader *can* check against the table above it, and it
fails.

---

## Findings index, by node and severity

| # | Severity | Node / figure | Where | One line |
|---|---|---|---|---|
| D15-1 | **high** | `key-release-time` | `latency-budget.md:133` | stale **125 µs** written *inside* this fix batch against a tracked 119.9 µs; uncaught by all 12 patterns |
| D15-2 | **high** | `key-release-time` | `key-switch-network.md:112` | same stale 125 µs **on the figure's owner page**, and it mislabels the RC as "the release filter" |
| D15-3 | **high** | key path, release edge | `latency-budget.md:100,109,121-123` | release-initiated note change unbooked and **does not close** — 5.67 ms on the published bounce maximum alone |
| D15-3b | medium | — | `ks33-geometry.md:226` | asserts the latency budget "books the release-filter window"; it does not |
| D15-4 | **high** | DAC8568 update | `latency-budget.md:102` | 60 µs vs the same operation booked at 106 µs four lines up, against the page's own stated rule |
| D15-5 | **high** | `loop-budget` | `0003-breath-sensing-path.md:18-27` | a complete stale copy of this budget, untouched by the batch; `50–200 µs` is a **forbidden pattern the checker cannot match** through table pipes |
| D15-6 | medium-high | breath digital total | `latency-budget.md:65` | stated 2.9–3.1 ms; rows give 2.68–2.93. The **1.6× margin** is computed from the underivable end |
| D15-7 | medium | breath poles | `latency-budget.md:49` | "632 µs" against its own table's 662 µs |
| D15-8 | low | breath analog total | `latency-budget.md:41,44` | total omits the < 10 µs cable row; and `:76` states a third figure, 2.80 ms |
| D15-9 | medium-high | MPXV4006DP | `latency-budget.md:39,146` | ~1 ms called "a datasheet figure"; **the banked Rev 3 has no response-time row** (`[test]` over all 22 pages) |
| D15-10 | medium-high | `ks33-contact-bounce` | `latency-budget.md:134-135,148` | the 5 ms max does not size the release window — ROADMAP:114-125 and ADR 0002:230-234 both say the unpublished reset gap does |
| D15-11 | **high** | `ks33-contact-bounce` | `ROADMAP.md:71` | "neither is published" — live stale assertion, refuted 49 lines later, checker at PASS |
| D15-12 | medium-high | note-on gate | `latency-budget.md:125-135` | bounce **stalling** the gate is unanalysed; ADR 0001:318-319 anticipates it |
| D15-14 | medium | `loop-budget` | `figures.yaml:575`, `latency-budget.md:178` | 196–241 µs not reproducible from its own derivation (6 polling transactions give 202–209) |
| D15-15 | medium | both budgets | `latency-budget.md:109,180` | 9 µs of loop slack; both quantisation terms scale 1:1 with any overrun, and the page never says the latency table is contingent on it |

### On the two sibling claims handed to this slice

- **`latency-budget.md:133` restates a stale 125 µs — CONFIRMED.**
  `[test] git log -L 130,136:docs/reference/latency-budget.md` → the sentence was
  **added** in `c65083d`, this batch. `[test] git log -S '119.9 us' --
  config/figures.yaml` → 119.9 has been the tracked value since `37811d2`,
  before the batch. Register's own note names the trap: *"Starting from 0 V
  instead of the divider voltage gives 124.5 us, which is the error the 125 us
  figure came from"* `[repo] config/figures.yaml:237`.
- **`key-switch-network.md:112` carries the same stale value — CONFIRMED**, and
  it is the **owner page**. `[test] git log -L 110,113:...` → written at
  `d88837b` (Phase B, pre-batch); it survived a batch that rewrote the figure's
  consumer. It also reads *"half a scan period"* — `[calc]` 119.9/250 = 48 %,
  so the prose survives the correction and only the numeral is wrong.
- **The caution about patterning `"125 µs"` is right.** `[repo]
  config/figures.yaml:236` already records it: a bare 125 µs is legitimately the
  mean sampling period at `latency-budget.md:59` and `:97` and the 8 kHz period
  at `:199`. Two candidate patterns that are RC-specific and fire on neither:
  `125 µs release filter` (hits `:112` only) and `125 µs the key network's RC`
  (hits `:133` only). `[test] grep -rn "125 µs"` over the corpus returns **six**
  occurrences — `latency-budget.md:59`, `:97`, `:133`, `:177`, `:199` and
  `key-switch-network.md:112` — four of them legitimate (mean sampling period
  twice, 8 kHz period twice). `[test]` Each candidate pattern was then grepped
  and hits **exactly one** of the two stale lines and nothing else. The
  `~125us` spellings in `hardware/bom.csv:37` and
  `hardware/cluster/key-switch-network/bom.csv:5` sit inside those rows'
  `SUPERSEDED:` refutation records and are correct as written.

### On D15-5, the checker's structural miss — the test that shows it

The `loop-budget` forbidden list contains `"SAR ADC conversion ~50"` `[repo]
config/figures.yaml:576`. ADR 0003 contains the value live and unrefuted, as a
table row. `[test]` reproducing `check_figures`' own line-join and
`text.find()` over `docs/decisions/0003-breath-sensing-path.md`:

```
'SAR ADC conversion ~50'  miss
joined stream at that point:  ' | | SAR ADC conversion | ~50–200 µs | | SPI to MCU, firmware | <'
```

The pattern was written in **prose** spelling; the value lives in a **table
cell**, so ` | ` sits where the pattern expects a space. This is CLAUDE.md §2's
first trap — *"write the pattern in the spelling of the file it must match"* —
in its markdown-table form rather than its CSV form, and the same list proves
the author knew the difference, because a neighbouring pattern in it,
`"chain read | < 10"`, **does** carry the pipe. One of the two spellings was
written from the file and the other from the page in front of the author.

Three more of ADR 0003's rows are stale in the same table and guarded by
nothing: `"SPI to DAC over the umbilical | ~50 µs"` `[repo] 0003:23` against the
current 96 µs (`[calc]` 50 µs ≈ one 32-bit word at 0.6 MHz — the superseded
umbilical rate `[repo] ROADMAP.md:52`); `"Op-amp and reconstruction filter |
~160 µs"` `[repo] 0003:26` against 82 µs mod / 10 µs pitch; and the total
`"< 1.5 ms"` `[repo] 0003:27` against 2.9–3.1 ms. The table also has no tube
row, no anti-alias row, no sampling period and no restrictor — the four terms
this page was rebuilt to add. And ADR 0003 states **three** mutually
inconsistent breath totals: `< 1.5 ms` `[repo] :27`, `~2.6 ms` `[repo] :258`,
`~3.1 ms` `[repo] :35`. `[test] git log 0e68f25~1..HEAD --
docs/decisions/0003-breath-sensing-path.md` returns **nothing**: the batch that
rebuilt the latency budget never opened the ADR that restates it.

`[calc]` Coverage of the latency domain in the register: of the quantities this
page books, exactly **one** is tracked with this page as owner (`loop-budget`),
two are borrowed (`key-press-time`, `ks33-contact-bounce`) and **every
divergence in this report is in an untracked quantity** — the DAC burst, the
tube delay, the filter corners, the transducer response, the umbilical rate, the
5 ms target, the path totals. That is the completeness answer to the wave's
second question: the fix was correct arithmetic in one file, and the register
was not extended to hold any of it in place.
