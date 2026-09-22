# G12 — Corpus edges: `firmware/`, `ROADMAP.md`, `README.md`, `docs/reference/`, `config/`, commit log, harness

**Slice:** G12, cold. **Measured against:** `a4b80b1` (the wave's named freeze).
**Method:** every file in `firmware/`, `config/`, `docs/reference/`, plus
`README.md` and `ROADMAP.md`, read in full; every structural and numeric claim
in them executed against the tree; a milestone-reference census over the whole
corpus; `git log` sampled for checkable claims; `.claude/settings.json` tested
behaviourally.

**Cold compliance:** I opened nothing under `docs/review/`, `docs/log/` or
`docs/research/`. Two tests needed history as *data* and were done by script
that printed only path tokens and counts, never prose: the path-map resolution
test (G12-10) and the review-wave directory count (G12-12). I did not read any
report.

**PINNING — read this before trusting any figure below.** The working tree was
being mutated by another slice during this wave (G12-26, and the coordinator's
mid-wave correction confirms it: corpus files *and* `tools/check-staleness.py`
were edited in place and later reverted, all uncommitted, so `git log` shows
none of it). **Every quotation, line number and `[test]` result in this report
has been re-verified against pinned content**, either a `git archive a4b80b1`
export or a fresh `git clone` checked out at `25cc740`.

`[test]` at the close of this slice: `git status --short --untracked-files=no`
in `/home/user/Woody` → **empty**; `diff` of `README.md`,
`tools/check-staleness.py` and `.claude/settings.json` against the pinned clone
→ **identical**. The tree had been fully reverted by then, so the pinned and
live readings agree. `README.md` in particular — mutated during the wave with an
appended broken link — is **byte-identical to `a4b80b1:README.md`**, so G12-12,
G12-13 and G12-14 stand on pinned content, not on what I happened to see.

**Baseline, taken from a pristine export of the frozen revision:**

```
[test] git archive a4b80b1 | tar -x -C <tmp> && cd <tmp>
       python3 tools/check-staleness.py
       -> PASS no live stale values | corpus 123 files, 23 circuits,
          37 figures / 217 patterns | 5 unresolved (tracked)
          | 211 restated-not-cited (advisory)
       python3 tools/merge-bom.py --check
       -> bom.csv: checked 140 rows from 26 fragments | 0 problems
       python3 tools/verify-datasheets.py
       -> datasheets: 78 verified, 23 recorded as blocked or not-fetched, 0 problems
```

All three tools pass at the freeze. Every finding below is invisible to all
three.

---

## Ranked findings

### Tier 1 — acting on these changes a build decision

---

**G12-1. `firmware/README.md:94` — "The body is bonded." It is not, and ADR 0009
says so in a paragraph that cites this file by name.**

`[repo] firmware/README.md:92-111` opens the recovery section with:

> The body is bonded. Everything here exists because a failed flash cannot be
> answered by opening the instrument.

and closes it with:

> A corrupted *bootloader* therefore ends the instrument — narrow, behind two
> mitigations, accepted.

`[repo] docs/decisions/0009-enclosure-construction.md:363-368` is the
refutation, and it is explicit that the sentence it is correcting is this one:

> The body opens on six fasteners, the dev boards are socketed, and a corrupted
> *bootloader* means taking the lid off and swapping or re-flashing a board on
> the bench. **This paragraph used to end "ends the instrument", which was true
> of a bonded body and is not true of this one.**

`[repo] docs/decisions/0009-enclosure-construction.md:653` settles the joint as
**"RTV as a gasket bead, not an adhesive… No — six fasteners"**, and
`ROADMAP.md:78` (M8) narrates the same change. ADR 0009's own version of this
paragraph, four lines above the refutation, links to `firmware/README.md` as
its authority for the MIDI opt-in — so the two files were open in the same
edit, the ADR's copy was corrected, and the firmware copy was not.

**Cost:** the whole recovery ladder is justified by an impossibility that no
longer holds. A reader either over-invests in recovery it no longer needs, or —
worse — checks the premise, finds the body opens, and relaxes the ladder that
`ROADMAP.md:78` (M8) still requires exercising. This is the exact shape
`CLAUDE.md` lists as the fourth recorded fix pattern: *a fix that did not reach
the pages citing it*.

---

**G12-2. The retired "bonded body" premise is live in ~25 places. One fact,
many files — and `docs/reference/pcb-pipeline.md` already records the
refutation and did not propagate it.**

`[test]` scripted census of `bond|cannot be reopened|cannot be opened|bonds
shut` over the §6 corpus, classifying each hit by whether refutation wording
sits within ±2 lines, and excluding the unrelated *electrical* sense
(`MECH-GNDBOND`, plate-to-`PWR_GND`) and adhesive-construction uses. **89 lines
matched; 25 are live arguments resting on the retired premise.**

`[repo] docs/reference/pcb-pipeline.md:192-197` is the proof that this was
known:

> **The CMRR row's stated reason was refuted and the ranking survives on a
> different one.** It read *"unretrofittable inside a bonded body"*. ADR 0009
> retired the bonded body — it comes apart on six fasteners…

That is one site, fixed correctly, with the reasoning re-derived. The other
twenty-five were not touched. In mine and the shared files:

| Site | Text | Why it matters |
|---|---|---|
| `[repo] firmware/README.md:94` | "The body is bonded" | G12-1 |
| `[repo] ROADMAP.md:207` | "sealed inside a **bonded body** at M6" | Contradicts `ROADMAP.md:78`, the same file's own M8 row |
| `[repo] ROADMAP.md:218` | "inside a body that **cannot be opened**" | Justifies the stuck-switch diagnostic |
| `[repo] config/key-layout.yaml:150-151` | "the body **bonds shut**, so it could never have become a switch anyway" | Justifies not cutting plate holes for the 3 free bits |
| `[repo] docs/decisions/0001-…:160, 191, 244, 337` | four separate arguments | 244 explicitly: "they **cannot be retrofitted** into a bonded body" |
| `[repo] docs/decisions/0003-…:248` | "most likely part to fail, in a body that cannot be reopened" | Sensor siting |
| `[repo] docs/decisions/0004-…:546` | "we find out before anything is bonded" | Gate rationale |
| `[repo] docs/decisions/0005-…:239` | "a bonded body that cannot be reopened to change the decision" | The reason `SW-PWR-INST` is deleted |
| `[repo] docs/decisions/0007-…:199` | "In a body that cannot be opened, two pins is a cheap price" | IMU pin budget |
| `[repo] docs/decisions/0013-…:294` | "Its own USB is inside a bonded body and reaches nothing" | Closes the display-flashing question |
| `[repo] docs/decisions/0014-…:53, 82-83, 497` | 82-83 is the sharpest: "In a **bonded** laminated body that cannot be opened casually, that matters more than it would in **a serviceable build**" | The WS2815 backup-data-line argument, now explicitly contrasted against the thing the body has become |

Plus, in `hardware/**` (other slices' territory, listed so it is not lost):
`carrier/carrier.md:286, 339, 384`; `cluster/cluster-boards.md:94`;
`cluster/key-marker-and-bits/key-marker-and-bits.md:68, 117, 133`;
`interfaces/breath-sense-link/breath-sense-link.md:14, 91, 181`;
`interfaces/key-chain-loom/key-chain-loom.md:146`;
`module/breath-receive-stage/breath-receive-stage.md:28`;
`module/breath-receive-stage/sim/README.md:22`.

**The distinction that decides each one** is drawn by
`[repo] docs/decisions/0009-…:493-497`: the body is "no longer *impossible*
later — but doing them means taking the lid off, disturbing the loom and
re-laying a gasket. That is a real cost". So sites arguing **cost** survive;
sites arguing **impossibility** ("cannot", "never", "ends the instrument",
"unretrofittable") are false. Most of the twenty-five are the second kind.

No forbidden pattern can ever catch this — the stale token is a word, not a
value. `CLAUDE.md` §5 is the rule that covers it.

---

**G12-3. `firmware/README.md:23-24` describes the pre-ADR-0013 architecture, and
the same file contradicts it fifteen lines later.**

`[repo] firmware/README.md:23-24`, inside a bullet list introduced at line 20 as
**"not negotiable"**:

> **Display renders on the other core, on its own SPI host.** A display refresh
> must never block the output loop.

`[repo] firmware/README.md:39-40`, same list:

> **WiFi and the display are on the other MCU.** They cannot preempt the output
> loop.

These are two different machines. "The other core" is the single-ESP32
architecture; ADR 0013 moved the display to a **separate MCU** with its own
image (`[repo] firmware/README.md:5-8` describes exactly that). "On its own SPI
host" is a statement about the real-time board's peripherals that no longer has
a referent — the display board owns its own panel bus.

The same residue is in `[repo] docs/reference/latency-budget.md:222-226`, where
rule 3 says "Separate SPI host, **separate core**" and rule 4, immediately
below, says "The WiFi stack and display are on a **different MCU entirely**
(ADR 0013)."

**Cost:** an implementer reads the "not negotiable" list and reserves an SPI
host and a core on the real-time board for a display that is not there. The
freed core is the one thing the 4 kHz loop would actually like to have.

---

**G12-4. `config/figures.yaml:471` — a disputed, load-bearing figure is assigned
to a milestone that does not do the work.**

`[repo] config/figures.yaml:465-471`:

```
  - id: breath-working-point
    quantity: Breath pressure at a hard blow
    status: disputed
    decided_by: "M1, with a player and a manometer. Sets the panel gain range
                 AND the ADC headroom."
```

`[repo] ROADMAP.md:71` — M1 in full — is **"Switch characterisation"**: plate
cutout, coupon fit, retention, contact bounce, hysteresis gap, spring weight. No
breath, no player, no manometer, no pressure.

The milestone that does this work is **E2**. `[repo] ROADMAP.md:42`: "**a human
plays it for 20 minutes** through a real mouthpiece, tube and trap"; and
`[repo] ROADMAP.md:193` books "Cold-start warm-up sweep | E2 | Run the sensor
from cold through 20 minutes of playing."

`breath-working-point` is cited by five circuits
(`[repo] hardware/interfaces/breath-sense-link/circuit.yaml:14`,
`hardware/module/breath-output-stage/circuit.yaml:14`,
`hardware/module/breath-response-shaper/circuit.yaml:12`,
`hardware/carrier/breath-adc/circuit.yaml:13`, plus the owning ADR) and it sets
the panel gain range and the ADC headroom. **A decider pointing at a milestone
that will not produce the measurement is an open question with nothing behind
it** — M1 can be signed off complete with this figure still disputed, and
nothing notices.

`[repo] docs/reference/repo-maintenance.md:251-253` states the rule this
violates: "A `disputed` entry must carry `decided_by` naming **what decides
it**". It names something, but not something that decides it.

---

**G12-5. `ROADMAP.md:71` (M1) tells a builder the bounce figure is unpublished.
The register, this same file, and two reference pages say it is published.**

`[repo] ROADMAP.md:71`:

> **bounce and the actuation/reset hysteresis gap scoped** on fast press, slow
> press, fast release, slow release and a worn switch — **neither is published**

Against it:

- `[repo] config/figures.yaml:648-651` — `ks33-contact-bounce`, **`status:
  settled`**, value `"5 ms max at 16 in/sec actuation"`.
- `[repo] ROADMAP.md:118-125`, fifty lines below the row, in the same file:
  "**Partly refuted 2026-09-21** … Gateron *does* publish a bounce figure —
  **5 ms max at 16 in/sec**". It then says correctly that the *hysteresis gap*
  is still unpublished. So "neither" should be "one of the two".
- `[repo] docs/reference/latency-budget.md:148`: "**No longer an unknown, only
  an unmeasured maximum** … this row used to frame it as unpublished."
- `[repo] docs/reference/ks33-geometry.md:206` — the owner, stating it.

This is `CLAUDE.md`'s named shape twice over: the fix landed in the prose
section and not in the table row a builder reads, and the corrected file
contains both versions. Note `[repo] firmware/README.md:26-34` handles the same
figure correctly — it cites `ks33-contact-bounce` by name and says the number is
"deliberately not restated here". The ROADMAP row is the outlier.

---

### Tier 2 — wrong information about how the repository works

---

**G12-6. `docs/reference/repo-maintenance.md:27` states the hook behaviour the
project has already corrected; line 278-280 of the same file states it
correctly.**

`[repo] docs/reference/repo-maintenance.md:27` — the opening sentence of §2,
the section about the checker:

> Run by a `PreToolUse` hook **before every `git commit`**, so forgetting it is
> visible rather than silent.

`[repo] docs/reference/repo-maintenance.md:278-280`, in §6:

> though note `CLAUDE.md` §2: it runs before *every* `Bash` call rather than
> before `git commit`, and it never blocks, it only tells you.

**Verified independently and behaviourally, not from `CLAUDE.md`:**

`[test]` every `Bash` call I made in this slice — `ls`, `cat`, `find`, `python3`,
`grep` — returned a `PreToolUse` `additionalContext` line beginning `staleness
check:`. None was a `git commit`. `[repo] .claude/settings.json` shows why: the
entry's `"matcher"` is `"Bash"`, and the `"if": "Bash(git commit *)"` sits
**inside the hook object alongside `command`/`timeout`/`statusMessage`**, not in
the matcher position, so nothing consumes it. The emitted JSON is
`{systemMessage, hookSpecificOutput:{hookEventName, additionalContext}}` — **no
`permissionDecision` field**, so a FAIL cannot block anything. Both halves of
`CLAUDE.md` §2's claim reproduce.

**Cost:** §2 is the section a reader opens to learn what the checker does. It
tells them a FAIL will be caught at commit time. It will not be. The correction
is 250 lines away under a different heading.

---

**G12-7. `docs/reference/repo-maintenance.md:204` — both numbers in the
`unplaced.csv` sentence are stale, inside the blockquote that exists to narrate
this exact failure.**

`[repo] docs/reference/repo-maintenance.md:204-208`:

> **`hardware/unplaced.csv` holds the 50 rows of 138 that no schematic page
> names.** … Two of its clusters name circuits this corpus has no page for — six
> identical jack-protection networks drawn three times, and nineteen decoupling
> capacitors with no home.

`[test]` `csv.reader` over both files at the freeze:

| Claim | Stated | Actual |
|---|---|---|
| `unplaced.csv` rows | **50** | **32** |
| `bom.csv` rows | **138** | **140** |
| "six identical jack-protection networks" | present | **absent** from `unplaced.csv` |
| "nineteen decoupling capacitors with no home" | present | **absent**; the largest unplaced row is `CAP1-n`, qty **21**, which is **keycaps** (`MT165-MX`), not capacitors |

`[repo] docs/reference/repo-maintenance.md:210-213`, nine lines below, is the
blockquote's own closing line:

> *This section described `bom.csv` as the file you edit for several hours after
> it stopped being one. Found by a cold reviewer. It is the project's named
> failure mode, in the document that exists to record exactly this trap.*

The paragraph corrected one instance of the failure and carries four more.

---

**G12-8. `docs/reference/pcb-pipeline.md:152-176` — a four-number table, all
four stale, and one emphatic conclusion that is now false.**

`[repo] docs/reference/pcb-pipeline.md:152-157`:

| | Rows stated | Rows actual | Units stated | Units actual |
|---|---|---|---|---|
| `hardware/bom.csv` master | 138 | **140** | 388 | — |
| 23 per-circuit fragments | 104 | **108** | 313 | — |
| `hardware/unplaced.csv` | 34 | **32** | 75 | **67** |

`[test] python3 -c` over `hardware/bom.csv`, `hardware/unplaced.csv` and
`glob('hardware/**/bom.csv')`; `[test] python3 tools/merge-bom.py --check` →
`checked 140 rows from 26 fragments`.

More serious is `[repo] docs/reference/pcb-pipeline.md:158-162` and `:174`:

> Of those 34, five are module-board netlist parts and would be missing from
> `module.net`: **`J-CV` ×6** (the CV jacks — the module's whole output
> connector set), `U-TVS-MODULE`, `D-CLAMP-BREATH` ×2, `R-BREATH-SUM` ×2 and
> `R-BREATH-OFF` ×2. **Thirteen units.**
> …
> **The CV jacks are not** [placed]**, and neither are the four rows beside
> them.**

`[test]` grep for those refdes across fragments:

- `J-CV` is at `[repo] hardware/module/bom.csv:5` — **placed.**
- `D-CLAMP-BREATH` is at `[repo] hardware/module/breath-receive-stage/bom.csv:7`
  — **placed.**
- Only `U-TVS-MODULE` (1), `R-BREATH-SUM` (2) and `R-BREATH-OFF` (2) remain in
  `unplaced.csv`. **Three refdes, five units, not five and thirteen.**

**Cost:** this is the section that tells you what the generated KiCad netlist
will be missing. It currently tells a reader the module will emit with no CV
jacks — its entire output connector set. Someone acting on that goes looking for
a bug that was fixed.

Note that `[repo] docs/reference/pcb-pipeline.md:170-176` is itself a
"*this warning used to say ~50 rows / 105 units*" correction — and
`repo-maintenance.md:204` (G12-7) still says the ~50. The two pages disagree
about the same count, in opposite directions, and both are wrong.

---

**G12-9. `docs/reference/repo-maintenance.md:191` — "24 per-circuit `bom.csv`
fragments"; `merge-bom.py` reads 26.**

`[test] python3 tools/merge-bom.py --check` → `checked 140 rows from 26
fragments`. `[test] find hardware -name bom.csv` → 25 fragments (22 circuit-level
plus three board-level aggregates at `hardware/{carrier,cluster,module}/bom.csv`),
and `[repo] tools/merge-bom.py:85,97-98` adds `hardware/unplaced.csv` as a
26th. `[repo] docs/reference/pcb-pipeline.md:154` independently says "23
per-circuit fragments", which is the `circuit.yaml` count
(`[test] find hardware -name circuit.yaml` → 23), not the fragment count. Three
documents, three different numbers, one authority (`merge-bom.py`) that prints
the right one on every run.

---

**G12-10. `docs/reference/repo-maintenance.md:339-348` — "Both assertions hold
as of this writing." One does not, for precisely the reason the same paragraph
gives.**

`[repo] docs/reference/repo-maintenance.md:339-348` publishes a four-line check
and asserts it passes:

```
tracked = set(git ls-files)
placed  = {r.new for r in rows if r.kind != "deleted"}
assert not (tracked - placed)      # no tracked file without a row
assert not (placed - tracked)      # no row pointing at nothing
```

`[test]` run verbatim against `docs/reference/path-map-2026-09-21.csv` and
`git ls-files` at HEAD:

- `placed - tracked` = **0** ✅ (the second assertion holds)
- `tracked - placed` = **35** ❌ — 33 under `docs/review/2026-09-22-fix-audit*`
  and `…-goal-verification/`, plus **`tools/audit-notes.py` and
  `tools/extract-findings.py`**

The paragraph three lines above predicted it: *"run it whenever files are added,
because **a new file is an orphan the moment it is committed**."* It was written,
the check was published, and the check was not run again. `CLAUDE.md`'s fourth
recorded fix pattern — *a fix whose own explanation restates the wrong value* —
in its purest form.

**What is verified good** (`[test]`, same script): the **old side is an exact
bijection onto `81c081d`** — 287 rows, 287 tracked files at that commit, zero in
either difference. That claim at `[repo] …:319-322` is true.

---

**G12-11. `docs/reference/repo-maintenance.md:323` — "405 tracked files, plus 4
`deleted` and 1 duplicate destination".**

`[test]` `collections.Counter` over the map's `kind` column: 410 rows total ✅;
`deleted` = 4 ✅; non-deleted rows = **406**, mapping to **406 unique** `new`
paths — **zero duplicate destinations**. So the breakdown should read "406
tracked files plus 4 deleted". The arithmetic still sums to 410, which is why
nothing caught it: the total was checked and the parts were not.

---

**G12-12. `README.md:117` — "`docs/review/` holds nine waves", in the sentence
that exists to explain why counts are not restated.**

`[repo] README.md:115-121`:

> `datasheets/` is the largest directory in the repository; `docs/review/` holds
> **nine** waves. … The counts that used to sit in this sentence — "77 banked
> documents", "seven waves" — were true when written and wrong within the week,
> **which is the whole reason this repository cites rather than restates**.

`[test] ls -d docs/review/*/ | wc -l` → **12** at HEAD, **11** at the frozen
`a4b80b1`. Nine is wrong either way.

`[repo] CLAUDE.md` § *Review waves* names this exact sentence as a recurring
defect: *"It said 'three' for months while the directory held nine, was
corrected to 'nine' on 2026-09-21, and was wrong again within a day — the third
recorded instance of this repository's named failure."* **This is the fourth.**
The sentence removed two of its three restated counts and kept the one that was
about to move; the retained count is the one being used as the illustration of
why counts must not be retained.

**Sibling claim, verified true:** "`datasheets/` is the largest directory" —
`[test] du -sh` → `datasheets` 58M vs `docs` 9.2M, `hardware` 888K. True by
size. (By *file* count `docs` has 231 to `datasheets`' 88, so the reading is
size, not files. Not a defect; worth a word if the sentence is ever rewritten.)

---

**G12-13. `README.md:111` — the repository layout does not mention
`config/figures.yaml`. Neither does any other word of `README.md` or
`ROADMAP.md`.**

`[repo] README.md:111`:

```
config/           Key layout and routing, as data
```

`[test] ls config/` → `figures.yaml` (72 KB, 37 tracked figures) and
`key-layout.yaml`. `[test] grep -c "figures.yaml" README.md ROADMAP.md
firmware/README.md` → **0, 0, 0**. `[test] grep -in "figures\|CLAUDE.md\|
check-staleness\|register" README.md` → **no matches at all**.

Two problems in one line:

1. **"routing" names a file that does not exist.** The routing matrix lives in
   NVS, not in `config/` — `[repo] firmware/README.md:147-150`: "Routing matrix
   — four mod channels… Both live in NVS and are editable from the display and
   over USB."
2. **`figures.yaml` is invisible to a new reader.** It is the mechanism
   `CLAUDE.md` rule 1 is built on, and `README.md:123-134` ("Where to start
   reading") sends a newcomer to five documents, none of which is the register.

`[repo] README.md:136-140` records the identical defect being fixed once
already — `hardware/README.md` had "**zero inbound links from anywhere in the
corpus**". The register now has the same status in the file a new reader opens
first.

---

**G12-14. `README.md:98` — `docs/reference/` is described as holding "fingering
notes". It does not.**

`[test] ls docs/reference/` → `ks33-geometry.md`, `latency-budget.md`,
`path-map-2026-09-21.csv`, `pcb-pipeline.md`, `repo-maintenance.md`.
`[test] grep -rl "fingering" docs/reference/` → **no files**. The directory's two
largest inhabitants — the PCB pipeline and the maintenance/path-map reference —
are not described by "Latency budgets, fingering notes, specs" at all.

---

**G12-15. Tracked figures are restated outside their owners in six places, and
`check-staleness.py` is structurally incapable of seeing it.**

`[test]` scripted: for each `settled` figure, take its distinctive numeric
tokens (≥4 chars) and find every corpus file other than the declared `owner`
that writes them out. Filtering substring noise by hand:

| Figure | Owner | Restated at |
|---|---|---|
| `mod-reference` `3.3333 V` | `hardware/module/mod-channels/mod-channels.md` | `[repo] docs/decisions/0006-…:15, 21, 105` (table cell, prose, and the governing equation) and **`[repo] firmware/README.md:56`** |
| `key-scan-current` | `hardware/cluster/key-switch-network/…` | `[repo] docs/decisions/0001-…:230` — "**1.43 mA** per closed key; 18 closed = **25.8 mA**" |
| `key-release-time` `119.9 us` | same | `[repo] docs/decisions/0001-…:227` |
| `key-press-time` `5.92 us` | same | `[repo] docs/decisions/0001-…:228` |
| `ks33-contact-bounce` | `docs/reference/ks33-geometry.md` | `[repo] docs/reference/latency-budget.md:126` and `:148`, and `[repo] ROADMAP.md:121` |
| `panel-height-budget` `115.5` | `docs/decisions/0004-…` | `[repo] hardware/module/panel/panel.md:58` |

(Some `docs/decisions/0006` hits at `:92` and `:117` are legitimate — they quote
the refuted `2.5 V` alongside. `:15`, `:21` and `:105` are plain restatements.)

**Why nothing catches it.** `[repo] tools/check-staleness.py:835-876`,
`check_restated`, builds a `known` set from every register `value` and
`forbidden` entry and then **skips any number in it**:

```python
for n, u in set(NUM_UNIT.findall(text)):
    if n in known or float(n) == 0:
        continue
```

Its docstring scopes it deliberately — "A number restated across three or more
files, **with no register entry**". So the advisory covers the *pre*-defect
state for untracked values (211 of them at the freeze), and the *actual rule 1
violation* — a **tracked** figure written out away from its owner — is the one
case excluded by construction. `check_owners` (`:880`) proves the owner states
the value; nothing proves that nobody else does.

**Cost:** `mod-reference` is the figure whose `escape_note`
(`[repo] config/figures.yaml:364-377`) records it going stale *inside its own
owner document* once already. It is now written out in four more files, two of
which (`ADR 0006:105`, `firmware/README.md:56`) are the ones a firmware author
reads before writing channel 7.

---

### Tier 3 — smaller, but each is someone's wasted hour

---

**G12-16. `ROADMAP.md:153-162` — the phase view omits F1, F2 and F3 entirely.**

`[test]` regex over the milestone table rows → 32 milestones defined: E1–E14 +
E4b, M1–M8, F1–F9. The phase table covers E1–E14, M1–M8 and **F4–F9**.
`F1` (key and fingering engine), `F2` (breath response) and `F3` (channel
output) appear in **no phase**. They are also the three F milestones the Phase 1
deliverable depends on — `[repo] ROADMAP.md:158` promises "Playable USB MIDI
instrument on a test plate" from `E1–E5, M1–M2`, and E5's own row
(`[repo] ROADMAP.md:46`) requires "Fingering table exercised", which is F1.
Either F1–F3 belong in Phase 1, or Phase 1's outcome is not reachable from its
contents.

Also cosmetic but confusing: the F table lists **F9 before F8**
(`[repo] ROADMAP.md:148-149`).

---

**G12-17. `firmware/README.md:81-83` states the pre-fix DAC behaviour in the
present tense, in the paragraph installing the fix.**

`[repo] firmware/README.md:81-83`:

> **The latency budget already books six DAC words per pass while five are
> written**, so the sixth channel fits inside a budget that was already paid

But `[repo] firmware/README.md:56` — twenty-five lines above, same argument —
says channel 7 is "**refreshed every pass, like the other five**", i.e. six are
written. `[repo] docs/reference/latency-budget.md:214-218` gets the tense right:
"The **old** table booked six while writing five, which is how the refresh fits
inside a budget that was already paid."

Everything else in this chain checks out `[calc]/[repo]`: 5 signal channels
(pitch + mod 1–4) + channel 7 = 6 DAC words; `latency-budget.md:62` books "Six
32-bit words at 2 MHz" = 96 µs; breath never touches the DAC
(`firmware/README.md:86-90`), consistent with `[repo] README.md:44-49`'s six CV
*jacks* being a different six.

---

**G12-18. DAC statelessness argument — verified against the banked datasheet,
and it holds.** *(Recorded because `CLAUDE.md` §3 asks for provenance on the
weak ones; this one is strong.)*

`[datasheet] datasheets/analog/DAC8568CIPW.pdf`, 62 pp, text extracted with the
pypdf/`cryptography`-stub recipe at
`[repo] docs/reference/repo-maintenance.md:155-163` (which worked as written):

- "These devices include a 2.5 V … **internal reference (disabled by default)**"
  → `firmware/README.md:78`'s "the internal-reference enable" is a real
  write-once register, and refreshing it is warranted.
- "contain a **power-on reset** circuit that … powers up at either **zero
  scale** or midscale" → `firmware/README.md:66-67`'s "The DAC's own power-on
  reset, which fires on every rack power-up" is correct. The midscale variant is
  flagged in the text as applying to **grades B and D**;
  `[repo] hardware/bom.csv:78` specifies **`DAC8568ICPW`** (grade C), and
  `[repo] ROADMAP.md:48` independently says "the DAC8568's **C grade**". Zero
  scale is right for the fitted part.
- **Table 13, "Clear Code Register"**, exists as described → the third
  write-once register named at `firmware/README.md:79` is real.

The `≈ +11.45 V` failure figure also reconciles: `[repo]
docs/decisions/0006-…:137` derives it as "an OPA2197 reaches ~±11.45 V" on ±12 V
less two Schottky drops, matching `[repo] hardware/module/mod-channels/…:182`.

---

**G12-19. `config/key-layout.yaml:150-151` — the free-bit argument rests on the
retired premise, and the comment two lines earlier already knows better.**

`[repo] config/key-layout.yaml:149-152`:

> `spare_bits_free: 3`  # was 5; two went to the marker. A free bit has no plate
> cutout and **the body bonds shut**, so it could never have become a switch
> anyway.

`[repo] config/key-layout.yaml:134` in the same block carries a `DECIDED
2026-09-21` correction, so this file was edited after ADR 0009. The identical
sentence is also at
`[repo] hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:68` and
`:133` — a verbatim triplication of a wrong premise, which is the shape
`CLAUDE.md` §2b warns about ("if you find yourself pasting, you are writing the
next defect"). All counts in this file verify: `[calc]` 5+6+4+3 = 18 total;
15 `note` + 3 `control` = 18; 4 devices × 8 = 32 bits, 18 used, 14 spare;
8 marker + 3 switches + 3 free = 14 ✅, and per-cluster spares (5+2+4+3) = 14 ✅.

---

**G12-20. Milestones nothing depends on, and one that exists only in its own
row.**

`[test]` census of `\b(E\d+b?|M\d+|F\d+)\b` across `hardware/**`,
`docs/decisions/**`, `docs/reference/**`, `config/**`, `firmware/**`,
`README.md`, excluding `ROADMAP.md` itself (part-number false positives —
`E96`, `E24`, `M12`, `M2011/M2012` — verified and discarded by inspection):

- **Zero inbound references:** `E3`, `E4b`, `E8`, `F1`, `F2`, `F3`, `F4`, `F5`,
  `F8`, `F9`.
- **One each:** `E14`, `F6`, `F7`.
- Heavily cited: `M3` (26), `E10` (25), `M8` (22), `M1` (22), `E7` (18),
  `E6` (18), `M2` (17), `M4` (16), `E2` (16), `E1` (16).

`E8` ("Pitch channel scaled") is the notable one: it sits between E7 (18
citations) and E9 (14), both of which the corpus leans on heavily as deciders,
and nothing anywhere cites E8. Worth checking whether E8's work has been
absorbed into E7 and E9.

`E4b` is referenced only by `ROADMAP.md` itself, although
`[repo] firmware/README.md:10-11` describes exactly its deliverable ("Joined by
a framed UART. Put a protocol version in the frame header from the first
commit") without naming it — a citation that would cost one token and close the
loop.

**Every milestone cited outside `ROADMAP.md` exists in `ROADMAP.md`.** No
dangling references. The named deciders in the brief all resolve:
`[repo] hardware/carrier/power-entry-instrument/bom.csv:7` "Bench affordance for
E5" ✅ (`ROADMAP.md:46`); "E7 selects `R-REG-SET`" ✅ stated explicitly at
`ROADMAP.md:48`; "E6 measures the trip" ✅ (`ROADMAP.md:199`).

One soft match: `[repo] hardware/carrier/breath-excitation-reference/bom.csv:4`
says "decide it at **E13 with a scope**", but `[repo] ROADMAP.md:54` defines E13
as the milestone where the **boards get built** — the scoping happens at E14
("E1–E11 re-run on the carrier", `ROADMAP.md:55`). Not wrong, but E14 is where
the instrument is on the bench.

---

**G12-21. `ROADMAP.md:71` — "the four thumb keys".** There are **seven**:
`[repo] config/key-layout.yaml:44-48` gives `left_thumb: 4` and `right_thumb: 3`.
The source sentence, `[repo] docs/decisions/0002-…:80-81`, says "the four
**left-thumb** keys may want a lighter spring than the eleven finger keys" —
correct. The ROADMAP row dropped "left-" and the sentence now under-scopes the
spring question by three switches.

---

**G12-22. Commit-log claims: sampled 12 recent messages against the tree. All
but one reproduce exactly.**

`git log` is 153 commits and **49,804 words** `[test] git log --format='%B' | wc
-w`, larger than any document in the tree. Checkable claims tested by
reconstructing each revision's `hardware/bom.csv` with `csv.reader` and summing
the `notes` column:

| Commit | Claim | Verdict |
|---|---|---|
| `9ac7a83` | "Trim the ten heaviest BOM notes cells: **34,184 -> 14,876** chars" | ✅ `[calc]` 34,184 − 14,876 = 19,308; measured whole-file delta 118,198 → 98,890 = **19,308** exactly |
| `192d03e` | "notes down to **70 %** of where they started" | ✅ `[calc]` 82,194 / 118,198 = **69.5 %** |
| `b183696` | "**897 lines deleted, 178 added**", "39-line header, **23 copies**" | ✅ `[test] git show --stat b183696` → `24 files changed, 178 insertions(+), 897 deletions(-)`; `[test] find hardware -name circuit.yaml` → **23** |
| `4a428e4` | "one figure of **thirty-seven**" | ✅ `[test] grep -c "^  - id:" config/figures.yaml` → **37** |
| `25cc740` | "names `a4b80b1` as the last commit that changed anything under review… HEAD is one commit later and adds only this README" | ✅ `[test] git diff --stat a4b80b1..HEAD` → 1 file, `docs/review/2026-09-22-goal-verification/README.md`, +81 |

**The one that does not:** `[repo] CLAUDE.md` §2b states "On 2026-09-22 the BOM's
notes went **118,198 → ~81,000** characters". `[test]` measured at `92afc0b` and
at HEAD: **82,129**. The start figure is exact; the end figure is ~1,100 low, and
rounds to ~82,000. Minor, but it is a derived number restated in prose in the
rules file — the shape rule 1 exists to prevent.

`[repo] CLAUDE.md` §2's other quantitative claim about the hook — that "a loop of
twenty tool calls can **blow the 60 s timeout**" — **does not reproduce as
stated.** `[test] time python3 tools/check-staleness.py` → **14.4 s real**, and
`[repo] .claude/settings.json` gives `"timeout": 60` **per hook invocation**, so
twenty calls are twenty separate 14 s runs, none near 60 s. The underlying
complaint is real and worse than a timeout: **every `Bash` call in this session
paid a ~14 s full-corpus scan**, including `ls`. The mechanism is right, the
consequence is mis-stated.

---

**G12-23. Claims I tested and found true — recorded so the next round does not
re-test them.**

- `[test]` `docs/reference/repo-maintenance.md:120-121` "Measured across all
  **60 banked PDFs**" → `find datasheets -name '*.pdf' | wc -l` = **60** ✅
- `[test]` `:351-352` "`.moves.csv` … records all **22 moves**" →
  `wc -l datasheets/.moves.csv` = 23 lines = 22 data rows ✅
- `[test]` `:319-322` old side is a bijection onto `81c081d` — **287 = 287**,
  zero in either direction ✅ (see G12-10)
- `[test]` `:310` "every tracked file has a row" — ❌, see G12-10
- `[test]` `datasheets/README.md` verification rules → `python3
  tools/verify-datasheets.py` = `78 verified, 23 blocked or not-fetched, 0
  problems`; `MANIFEST.csv` = 101 rows (76 `OK` + 2 `OK-SUBSTITUTE` + 22
  `BLOCKED` + 1 `NOT-FETCHED`). Internally consistent ✅
- `[test]` every relative Markdown link in `README.md`, `ROADMAP.md`,
  `firmware/README.md` and all five `docs/reference/` files resolves on disk —
  **zero broken links** ✅
- `[test]` `README.md:126` "`hardware/README.md`" exists ✅
- `[repo] config/key-layout.yaml` — all eight internal counts reconcile (G12-19) ✅
- `[repo] firmware/README.md:44-48` "MISO was deleted from the cable" ✅ against
  `umbilical-pinmap` (`config/figures.yaml:336`), which has no MISO pin
- `[repo] firmware/README.md:22` "4 kHz loop" ✅ against
  `docs/reference/latency-budget.md:169-180`; and firmware correctly does **not**
  restate `loop-budget`

---

**G12-24. `README.md:14` — "Status: Phase 0 … Switches and keycaps are
purchased."** `[test] grep purchased hardware/bom.csv` → `CAP1-n` (keycaps,
qty 21) and the KS-33 row carry `status=purchased`. ✅ Consistent. Flagged only
because `ROADMAP.md:157` defines Phase 0 as "This repository", and three review
waves plus a restructure have happened since — nothing in the corpus says what
ends Phase 0. Not a defect; an unclosed loop.

---

### Process

**G12-25. `tools/check-staleness.py` reports `PASS` and `0 unwired` with a live
broken link, if any one check is called with an empty file list. Demonstrated,
and it is what produced this wave's flapping verdicts.**

`[repo] tools/check-staleness.py:1048-1074`, `instrument()`, is the hardening
that closed the `check_refdes` hole. Its docstring is precise about the attack
it was built to stop:

> This assertion used to read the SOURCE TEXT of `main()` and look for the
> substring `"check_links("`. That is satisfied by a call that never happens …
> **A check that does not run reads exactly like one that passes** — which is
> the whole reason this assertion exists — so the assertion itself must not be
> satisfiable by anything short of the call actually being made.

It now wraps each check so that `RAN.add(nm)` fires on invocation
(`[repo] …:1066-1071`), and `check_checks()` (`[repo] …:1076-1090`) reports any
`check_*` not in `RAN`. **That closes "never called" and leaves "called with
nothing to check" wide open** — the wrapper records the call without looking at
its arguments.

`[test]`, in a **disposable clone** (`git clone /home/user/Woody /tmp/g12-check`,
`git checkout 25cc740`), never in the real repository, and reverted afterwards:

```
# control: append a broken link to README.md, unpatched checker
$ printf '\nSee [nothing](g12-does-not-exist.md).\n' >> README.md
$ python3 tools/check-staleness.py
FAIL 0 shape + 0 owners + 1 links + ... + 0 unwired + 0 stale + 0 bom
     | corpus 123 files, 23 circuits, 37 figures / 217 patterns

# one character class of edit, at line 1115: check_links(files) -> check_links([])
$ python3 tools/check-staleness.py
PASS no live stale values | corpus 123 files, 23 circuits, 37 figures / 217 patterns
     | 5 unresolved (tracked) | 211 restated-not-cited (advisory)

$ python3 tools/check-staleness.py | grep -i 'unwired\|never called'
(nothing)
```

**The broken link is still in the file.** The verdict flips to `PASS`, the
unwired count stays at zero, and — this is the part that matters —
`corpus 123 files` **does not move**. `[repo]
docs/reference/repo-maintenance.md:301` tells a reader that the file count is
the thing to check rather than the verdict: *"prints the corpus file count on
every run — the count is what you check, not the verdict"*. Against this edit
the count is as green as the verdict. Both instruments read normal.

This is not hypothetical: the coordinator reports an injection slice ran
precisely `check_links([])` in the shared tree during this wave, and other
slices watched the hook flip `PASS -> FAIL(1 links) -> PASS -> FAIL(1 stale)`
across read-only calls. **The tool's own docstring names the class of defect and
the current guard does not cover it.** A per-check assertion that the file list
it was handed is non-empty, or simply that it is the same `files` object
`main()` computed, would be a few lines and would have caught it.

---

**G12-26. The freeze did not hold. `README.md` was modified twice by another
agent while I was reading it.**

`[test]` `git status --short` during this slice: `M README.md` at one point,
clean at another. `[test]` the `PreToolUse` staleness line changed verdict three
times across my own calls with no action of mine:

```
PASS no live stale values | corpus 123 files …
FAIL 0 shape + 0 owners + 1 links + … 0 stale …
FAIL 0 shape + 0 owners + 0 links + … 1 stale …
PASS no live stale values | corpus 123 files …
```

At one point `README.md` carried an appended line `See [the missing
page](g10-does-not-exist.md).` — evidently a probe from another slice, not a
corpus defect. **I did not touch it and did not revert it.**

**Confirmed mid-wave by the coordinator**, who identifies the cause: an
injection-testing slice was briefed to edit corpus files *and*
`tools/check-staleness.py` in place and revert them, in the same tree as eleven
read-only reviewers. `README.md` gained a broken link;
`tools/check-staleness.py` was patched to `check_links([])` (G12-25);
`hardware/module/pitch-stage/circuit.yaml` was modified.

`[repo] CLAUDE.md` § *Review waves* asks a wave to "Name the revision a wave
measures against, and **pin `tools/`** or say you are not", because last wave's
orchestrator broke exactly this and "every `[test]` baseline in twenty reports
stopped reproducing". The freeze clause was written and committed **first** this
time (`c46487d`, `25cc740`) — and it still broke, in the half the clause does not
reach. The clause binds what gets **committed**; the damage was entirely in the
**uncommitted layer**, which `git log` cannot show and `git diff a4b80b1 HEAD`
cannot show either. `[test] git diff --stat a4b80b1 HEAD` → one file, this
wave's README: **the commit-level freeze is provably intact and was never the
thing at risk.**

**This is the sharpest finding available about the project's method.** The
repository's entire defence — "git holds every version of every cell and cannot
go stale" (`[repo] CLAUDE.md` §2b) — assumes changes reach git. A tool patched
and reverted between two agents' reads is a change to the corpus's *measured
behaviour* that leaves no trace anywhere. Two mitigations, both cheap: give
injection slices their own clone, and have every slice record
`git status --short` beside each `[test]` result. I have done the second
throughout; see the pinning note at the top.

---

## What I could not check

- **`firmware/` against real hardware.** `[test] find firmware -type f` returns
  **one file**, `firmware/README.md`. There is no code, so "does the firmware
  match the schematics" reduces to "does this design document match", which is
  what I did. SPI word counts, loop budget, debounce policy and DAC register
  handling are all checkable as prose and are reported above; **timing under a
  real ESP-IDF driver is not checkable from this repository at all**, and
  `latency-budget.md:196-212` already says the ADC round-trip measurement is a
  gate on the architecture rather than a refinement of it.
- **Gateron KS-33 bounce and hysteresis numbers** — I read them from
  `config/figures.yaml` and `ks33-geometry.md`, not from the vendor PDF. The
  dimension callouts in that file are outlined vector
  (`[repo] docs/reference/repo-maintenance.md:128`) and I did not render sheets
  3 and 6.
- **`mechanical/`** is three `.gitkeep` files
  (`[test] find mechanical -type f`), so `README.md:110`'s "CAD source, 2D cut
  exports, drawings" is aspirational rather than wrong. Not counted as a finding.
- **Whether `ROADMAP.md` milestones' *described work* has already happened** — I
  can confirm no milestone is marked done anywhere, and `README.md:14` says no
  hardware is built. I cannot distinguish "not started" from "done and
  unrecorded" from documents alone.
- **The 211 `restated-not-cited` advisory entries** — I confirmed the check's
  scope and its structural blind spot (G12-15) but did not triage the 211.
- **`docs/review/` contents** — cold, by rule. Anything in this report about
  waves is from directory names and file paths only.

## Suggested ledger seeds

**Fix these first, and do not let the fix stop at the first file:** **G12-1**
(firmware's bonded body), **G12-2** (the other 24 bonded-body sites), **G12-4**
(`breath-working-point` is decided by E2, not M1) and **G12-5** (M1's "neither
is published"). G12-2 is a single fact across twelve files; fixing the firmware
line alone reproduces the exact pattern this wave exists to find.

**Fix before the next wave runs at all:** **G12-25** — a check called with an
empty file list reads as `PASS` with `0 unwired` and an unchanged corpus count.
Every slice in this wave is reporting `[test]` results from a tool that was
demonstrably in that state at some point during the wave.

**Cheapest high-value fix in the report:** **G12-6** — one sentence at
`docs/reference/repo-maintenance.md:27`, in the section a reader opens to learn
what the checker does, which tells them a FAIL will stop a commit. It will not.

**Counting defects, all the same shape, all mechanical:** G12-7, G12-8, G12-9,
G12-10, G12-11, G12-12, G12-17. Seven stale counts across four documents, six of
them in the two files whose stated job is to tell you how this repository works.
None is catchable by `config/figures.yaml`, because a count is a value nobody
registered. If one structural change comes out of this wave, it is that
`repo-maintenance.md` and `pcb-pipeline.md` should **print** their counts from
the tools rather than restate them — `merge-bom.py --check`,
`verify-datasheets.py` and `check-staleness.py` already emit every one of the
seven on every run.
