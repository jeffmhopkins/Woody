# G2 — Cross-references: does the cited thing say what the citing text implies?

**Slice:** G2, cold. I did not open anything under `docs/review/` — not this
wave's README, not any prior wave. Nothing in this report is informed by
another reviewer.

**Revision measured against:** `a4b80b1`. `git diff a4b80b1 HEAD --stat` is one
file, this wave's own `docs/review/…/README.md`, which I did not read.

**Tree instability, and how I handled it.** Partway through this slice the
working tree changed under me: `hardware/module/pitch-stage/circuit.yaml` and
`hardware/module/power-entry/circuit.yaml` each gained an appended comment
(`# G10: this row previously said -9.6 V…`, `# This field previously said ~275
instrument mA…`), and the `PreToolUse` staleness hook flipped
`PASS → FAIL (1 stale) → FAIL (2 stale) → PASS` across read-only calls of mine.
The coordinator has since confirmed this was an injection-testing slice working
in the same tree, and that `tools/check-staleness.py` was itself patched at one
point.

**So every finding below was re-derived against a pinned checkout**
(`git clone /home/user/Woody /tmp/g2-check && git checkout a4b80b1`), and every
line number and quotation was re-read from that pinned tree. At the moment of
the final verification run `git status --short` in `/home/user/Woody` showed no
modified tracked files (only untracked `docs/review/…` files belonging to other
slices, which I did not open). **I quote no tool output from
`tools/check-staleness.py` as evidence for any finding** — every check below is
one I wrote and ran myself, in the pinned tree.

---

## Summary

| | |
|---|---|
| References that **do not resolve** | 4 (`G2-5`, `G2-13`, and the two halves of `G2-14`) |
| References that **resolve but are false** | 9 |
| Structural claims tested and found **true** | 8 (listed at the end — a cold slice's negatives are evidence too) |

The distinction the brief asks for holds up in the data: **the resolving-but-false
class is both larger and more damaging.** Three of them (`G2-3`, `G2-4`, `G2-9`)
are contradicted *by another file in the same corpus that says so explicitly* —
the correction was written down and the thing it corrects was never touched.
That is this repository's named failure mode expressed in citations rather than
in numbers, and no grep can reach it.

---

## A. Resolves, but is false

### G2-1 — Three documents name three different owners for `inamp-full-scale`

`config/figures.yaml:29` `[repo]`:

> `owner: hardware/interfaces/breath-sense-link/breath-sense-link.md`

`hardware/interfaces/README.md:19` `[repo]` agrees:

> And it **owns a tracked figure**, `inamp-full-scale`, whose derivation
> reaches across the umbilical.

But the file the register names as owner disclaims ownership, in its own
`## Interfaces` table — `hardware/interfaces/breath-sense-link/breath-sense-link.md:59`
`[repo]`:

> | in-amp output | … | `inamp-full-scale` | Into the panel GAIN/OFFSET stage,
> which inverts. **The figure is owned at the module end and derived here** |

and the module end claims it —
`hardware/module/breath-receive-stage/breath-receive-stage.md:45` `[repo]`:

> | in-amp output | … | `inamp-full-scale` | **Owned here.** …

**Node:** in-amp output / `U-DIFFRX`.
All four references resolve. Two of them are false, and which two depends on
which you take as authoritative. `check_owners` in `tools/check-staleness.py`
cannot see this: it asks only whether the *register's* owner file states the
value, and `breath-sense-link.md` does, so the check is green while the page
itself says the opposite of the register.

This matters beyond bookkeeping. Rule 1 is "the owner states it, everyone else
cites it". A figure with two pages each believing the other owns it is a figure
with no owner, which is the precondition for the split that
`breath-zero-ref`'s own `escape_note` records.

### G2-2 — `panel.md` says it does not restate two figures, in a page that restates both

`hardware/module/panel/panel.md:5–7` `[repo]`:

> The tracked figures for that are `panel-width` and `panel-height-budget` in
> `config/figures.yaml`, whose owner is
> `docs/decisions/0004-cv-interface-module.md` — **this page cites them and
> does not restate them.**

Forty-eight lines later, the same page states both values verbatim:

- `panel.md:54` `[repo]`: "**10HP is 50.50 mm, and the win is not the extra
  width.**" — `panel-width`'s `value` is `"50.50 mm (10HP)"`.
- `panel.md:57–58` `[repo]`: "the total is the tracked figure
  `panel-height-budget` — **110 mm of content against 115.5 mm of clear
  panel**" — which is `panel-height-budget`'s `value` string character for
  character.

**Node:** `PANEL`.
The citation resolves; the sentence around it is false about its own page.
The second one is the sharper case, because it *cites the figure by name and
then restates it in the same sentence* — the form that looks maximally
compliant from a distance.

### G2-3 — `pcb-pipeline.md` files a settled figure as one of three undecided "ground questions"

`docs/reference/pcb-pipeline.md:112` `[repo]` heads a section
"## Three ground questions that must be decided in one sitting", and line 127
`[repo]` lists:

> - **`cref-out-node`** — three drawings disagree about which side of the
>   reference buffer `C-REF-OUT` sits on.

`config/figures.yaml` `cref-out-node` is `status: settled`, with a `value`, a
`derivation` citing SBOS410O §8.4.1 verbatim, and a `consequence` paragraph.
`hardware/carrier/breath-excitation-reference/breath-excitation-reference.md:27`
`[repo]` says "Settled, and it decides the whole compensation".

**Node:** `C-REF-OUT` / REF5050 `VOUT`.
The reference resolves and is false. It also makes the section heading false
(there are two open ground questions, not three), and `cref-out-node` was never
a *ground* question in the first place.

### G2-4 — The same page's sim ranking is stale in two independent ways, and the corpus already says so

`docs/reference/pcb-pipeline.md:187` `[repo]`, the `R-ISO-REF` stability row:

> … SBOS737C §8.2.3, `R_ISO` 37.4 Ω with a dual-feedback network, 89° PM,
> **against our 10 Ω**. **Blocked on `cref-out-node` first**

Both clauses are retired, and both are refuted *in the corpus*, on the page
whose sim that row ranks —
`hardware/carrier/breath-excitation-reference/sim/README.md:23–27` `[repo]`:

> - The row records the sim as **blocked on `cref-out-node` first**. That figure
>   is now settled, so the block is lifted …
> - The compensation the page now draws is TI's dual-feedback network rather
>   than the bare series resistor the sweep condemned.

And `hardware/bom.csv` `R-ISO-REF` is `37.4R 1%` `[repo]`, not 10 Ω;
`riso-ref-topology` is `settled` at `R_ISO 37.4 ohm`.

**Node:** `R-ISO-REF`.
This is the exact shape CLAUDE.md names: the correction landed where the
editing was happening (the sim README) and not where the reader looks (the
ranked table the sim README points *back* at). A reader who opens
`pcb-pipeline.md` first — which is what it is for — gets a blocked sim and a
10 Ω circuit that no longer exists.

### G2-5 — All three of `dig-gnd-topology`'s candidate citations are wrong, and one points past end-of-file

`config/figures.yaml:547–549` `[repo]`:

| register says | pinned reality |
|---|---|
| `"Its own path to the star (docs/decisions/0004-cv-interface-module.md:627)"` | `0004:627` is a table row: `` | `PWR_GND`, from the etherCON | **~360 mA** of instrument current … | ``. The claim is at **`0004:646`** — "- **`DIG_GND` likewise** — its own path to the star." |
| `"NOT its own path … (hardware/module/power-entry/power-entry.md:495-498)"` | **`power-entry.md` is 192 lines long.** The citation does not resolve at all. The claim is at **`power-entry.md:172–175`** |
| `"The analog star, single tie (hardware/module/digital-and-supervision/digital-and-supervision.md:53)"` | `:53` is a line of ASCII art: `` └── 8 DIG_GND│  │  │              ┌────┴─────────┐ ``. The claim is at **`:65`** — "└── analog star, single tie (ADR 0004)" |

`[test]` `wc -l hardware/module/power-entry/power-entry.md` → `192`, in
`/tmp/g2-check` at `a4b80b1`.

**Node:** `DIG_GND`.
This is the register's record of the corpus's most-cited disputed figure —
`dig-gnd-topology` is cited from 15 corpus files, more than any other. It is
the input to `decided_by`, and `pcb-pipeline.md:118` calls it one of three
things "that must be decided in one sitting". Whoever sits down to decide it
has three pointers, one of which cannot be followed and two of which land on
unrelated text. Line-number citations into a corpus that is actively being
restructured are a form that guarantees this; none of the three is off by more
than 20 lines, which is exactly the range in which a reader assumes they
misread rather than that the citation is wrong.

### G2-6 — …and the note that justifies the dispute is wrong about the same line

`config/figures.yaml` `dig-gnd-topology.note` `[repo]`:

> `power-entry.md` states that ADR 0004 was corrected on this point. IT WAS NOT
> - **line 627 still says the opposite.**

The *substance* is true — `power-entry.md:173` says "which an earlier revision
of ADR 0004 asked for", and `0004:646` still asks for it. But line 627 says
nothing about it. The note is a correction whose own evidence pointer is wrong,
which is the fourth recorded shape in CLAUDE.md ("a fix whose own explanation
restates the wrong value") applied to a line number instead of a value.

### G2-7 — `2.8 kPa` is attributed to ADR 0003, which says 0–5 kPa

`hardware/module/breath-output-stage/breath-output-stage.md:44–45` `[repo]`:

> **Real playing only reaches about 2.8 kPa against the sensor's 6 kPa range**
> (ADR 0003), so the stage's working input is 0 to about −4.7 V.

`[test]` `grep -c "2.8 kPa" docs/decisions/0003-breath-sensing-path.md` → `0`
(pinned tree). What ADR 0003 actually says, at `0003:140` `[repo]`: "playing
sits around 0–5 kPa."

**Node:** in-amp output / `POT-GAIN`.
`config/figures.yaml` already knows — `breath-working-point.candidates[0]` reads
`"2.8 kPa (cited to ADR 0003, which does not contain it; the two schematic pages
cite each other)"` — and the citation is still live and still unmarked on the
page. The register recorded the defect instead of the page carrying a correction,
so a reader of `breath-output-stage.md` sees an ADR attribution and no reason to
doubt it.

Two further pages cite `breath-working-point` (status **disputed**) in their
`## Interfaces` tables and then use one of its candidates as settled fact:
`hardware/carrier/breath-adc/breath-adc.md:25` cites the figure and line 40
computes `real play = 2.8 kPa → … → 1795 counts`;
`breath-output-stage.md:22` cites it and line 41 tabulates
`Hard blow, real playing (~2.8 kPa) | 2.411 V | −4.64 V`. Citing a disputed
figure and then picking a side is not a resolution; the playable-span count and
the panel gain range both hang off it.

*(For the record, and against a reading I first took and then discarded:
`breath-receive-stage.md:199–201` does **assert** 2.8 kPa live — "the knob does
more work than this page used to say" attaches to *the knob*, not to the
pressure. `breath-adc.md:41`'s `[2.8 kPa from breath-receive-stage.md]`
provenance marker is therefore correct as to source. The defect is the ADR
attribution, not the chain.)*

### G2-8 — A quotation attributed to ADR 0001 appears nowhere in ADR 0001

`hardware/interfaces/key-chain-loom/key-chain-loom.md:95–96` `[repo]`:

> ADR 0001 has that input **"terminated at the far device"**, which would make
> this conductor redundant.

and line 108 `[repo]`, carrying an explicit provenance marker:

> **`CLK INH` is tied low and `SER` is terminated at the far device** — both on
> the cluster boards, not here `[repo] 0001`.

`[test]` `grep -n -i "terminat" docs/decisions/0001-mcu-and-board-partitioning.md`
in the pinned tree returns lines 136, 173, 177, 183, 185, 283, 285, 289, 299,
301, 303, 309 — **every one of them is about electrical series termination of
`SCK`/`SH-LD`**, and item 4 of the fix list (`0001:283`) is struck through as
deleted. ADR 0001's item 6 (`0001:292`) is the whole of what it says about
tie-offs: "**Tie `CLK INH` low at all four devices, and pull every unused
parallel input.**" It says nothing about `SER` at the far device.

**Node:** `SER` / `LK-SER` / `R-SER-TERM`.
The compound claim on line 108 is half true: `CLK INH` is ADR 0001's, `SER`
termination is not. The `[repo] 0001` marker covers both halves, so the
provenance convention that is supposed to make weak claims visible is here
laundering one. The claim is load-bearing — it is the premise for "which would
make this conductor redundant", i.e. for whether pin 6 of `J-CHAIN` earns its
place, and `R-SER-TERM` is `open` in the BOM on exactly this question.

### G2-9 — `key-scan-current`'s `companion` field describes a deduplication that did not happen

`config/figures.yaml:198` `[repo]`:

> `companion:` "Its two consequences are **stated where they land**: the ADC
> reference droop (0.077 %, 3.2 LSB, ~1594 counts) on
> `hardware/carrier/carrier.md`, and the 3V3 rail step on
> `hardware/interfaces/key-chain-loom/key-chain-loom.md`."

"Stated where they land" implies one site each. `[test]`
`grep -n "1.43 mA\|25.8 mA\|3.2 LSB\|1594"` over the pinned corpus:

| file:line | carries |
|---|---|
| `hardware/carrier/carrier.md:172,173,174,177,373` | the full derivation *and* the droop *and* the 1594-count span |
| `hardware/interfaces/key-chain-loom/key-chain-loom.md:118,119,126,129` | the full derivation *and* the droop *and* the 1594-count span |
| `hardware/cluster/key-switch-network/key-switch-network.md:108,129,130,143` | the derivation and 3.2 LSB — this is the **owner** |
| `docs/decisions/0001-mcu-and-board-partitioning.md:230,239` | the derivation again |

So the droop is in two files, not one; the step is in three; and there is a
fourth site the `companion` does not mention at all. **`key-scan-current` is
cited by name from zero corpus files** — `[test]` a scan for every register id
across `hardware/**`, `docs/decisions/**`, `docs/reference/**`, `config/**`,
`firmware/**`, `README.md`, `ROADMAP.md` puts it and `pitch-compensation` at
zero, and `breath-sensor-slope` at two (both inside the same `U-BREATH` BOM row,
master and fragment).

The entry's own `escape_note` says it plainly — "DEDUPLICATING it is still owed
… today all three restate it" — so **the entry contradicts itself between two
adjacent fields**, and the field a reader skims (`companion`, which reads like a
statement of current layout) is the false one.

### G2-10 — `U-OPA-PITCH` and `U-RESP` cross-reference each other and cannot both be true

`hardware/bom.csv:80` `[repo]`, `U-OPA-PITCH`, qty **6**:

> Six packages, twelve halves, TEN used: … **TWO SPARE — and `U-RESP` claims
> both of them if it is fitted**, so check that row before spending them.

`hardware/bom.csv:93` `[repo]`, `U-RESP`, qty **1**, `OPA2197IDR`, status `open`:

> *** THIS PACKAGE CONSUMES BOTH OF THE MODULE'S REMAINING SPARE OPA2197
> HALVES, *** because the shaper needs one and `POT-OFFSET`'s wiper needs the
> other … Fit this and the module has no spare op-amp capacity left.

`[calc]` `U-RESP` is its own row at qty 1, so fitting it puts **7** OPA2197
packages on the module = 14 halves. Demand is 10 + shaper 1 + `POT-OFFSET`
buffer 1 = **12**. That leaves **two spare**, not zero. The two rows'
mutual claim is only true if `U-RESP`'s two halves *are* `U-OPA-PITCH`'s two
spares — in which case `U-RESP` must not also be a qty-1 package, and the BOM
is double-counting one OPA2197.

Two pages take the wrong side of the same fork:
`hardware/module/breath-response-shaper/breath-response-shaper.md:30` `[repo]`
calls them "`U-RESP`'s two halves — **the last two on the module**", and
`hardware/module/breath-output-stage/breath-output-stage.md:157–158` `[repo]`
says "Ten of twelve halves used across the module, two spare."

**Node:** `U-OPA-PITCH` / `U-RESP`.
Both rows are honest attempts at the mutual reference the brief asks about;
they are consistent as *prose* and inconsistent as *arithmetic*, which is why
reading either one alone finds nothing. Either the `U-RESP` qty is wrong or the
"no spare capacity left" cost — the stated reason the row is `open` rather than
`selected` — is overstated by one package.

### G2-11 — ADR 0009's mass table is built on a plate thickness its own page refutes 117 lines earlier

`docs/decisions/0009-enclosure-construction.md:64` `[repo]`, in the stack-up:

> `aluminium top plate       1.20 mm <- SETTLED by Gateron's drawing, see ADR 0002`

`docs/decisions/0009-enclosure-construction.md:181` `[repo]`, in the mass table:

> `| Aluminium top plate, 2 mm | 157 |`

`plate-thickness` is `settled` at `"1.20 mm"`, owner
`docs/reference/ks33-geometry.md`. The `see ADR 0002` pointer on line 64 does
resolve — `0002:138` and `0002:237` both say 1.20 mm.

`[calc]` 157 g of aluminium at 2.00 mm scales to 157 × 1.20/2.00 = **94 g** at
1.20 mm, so the row is **63 g high** and the stated totals
(`0009:169` "~825 g (1.82 lb)" and `0009:186` "**~825 (1.8 lb)**") should be
~762 g (1.68 lb).

**Node:** `PLATE-TOP`.
No forbidden pattern can catch this and none should be added: "2 mm" is
legitimately `PANEL`'s aluminium, and `panel-toggle-hole`'s own
`false_positive_note` records what happens when a pattern's cheapest fix is to
make a correct sentence wrong. This is a **derived** number that did not move
when its parent did — the same class as `D-TVS-BREATH`'s "300mV of margin" in
`sensor-full-scale`'s `escape_note_3`, and the same class as
`mod-channels`' "1 mA". The conclusion ("squarely in EWI territory ~1.5–2 lb")
survives, which is why it has gone unnoticed; the number carrying it has not.

### G2-12 — `hardware/README.md` states a count of `unplaced.csv` that has moved under it

`hardware/README.md:112` `[repo]`:

> It was 50 rows and is now 34. Sixteen of them were drawn all along …

`[test]` `csv.DictReader` over `hardware/unplaced.csv` in the pinned tree →
**32 rows**. `[repo]` the history of the file:
`c483829` 50 → `0e68f25` 34 → `b32c557` 34 → **`04b5208` 32** → 32 → 32.

The internal arithmetic is self-consistent (50 − 16 = 34), which is what makes
it survive a reading: the sentence checks out against itself and not against the
file it describes. Two more rows were placed at `04b5208` and the sentence did
not follow. This is CLAUDE.md's third recorded shape — "a stated count that has
moved under the sentence stating it" — in the file that is the corpus's own
index of what is and is not drawn.

---

## B. Does not resolve

### G2-13 — `figures.yaml` cites two banked artefacts with manifest-relative paths that collide with a real repo directory

`config/figures.yaml:405` `[repo]`, inside `panel-height-budget.derivation`:

> … two independent banked artefacts agree (a FABRICATED 3HP panel,
> **`mechanical/EURORACK-3U-3HP-PANEL-apfaudio-pmod-r3.1.kicad_pcb`**, Edge.Cuts
> measured 15.000 × 128.500; and
> **`mechanical/EURORACK-3U-PANEL-HP-TABLE-make_blanks.py`**, HEIGHT=128.5 …)

Both files exist, at `datasheets/mechanical/…` (`MANIFEST.csv` rows 65 and 66,
both `status=OK`). Neither exists at `mechanical/…` — **and `mechanical/` is a
real directory in this repo**, holding `cad/`, `drawings/` and `export/`, each
containing only a `.gitkeep`.

**This is the worst case of a dangling path, not the mildest:** a reader
following the citation lands in a real, empty, plausibly-named directory and
concludes the artefacts were never banked. Every other corpus reference to a
banked document spells the full repo-relative path — e.g. `hardware/bom.csv`'s
`PLATE-TOP` row writes
`datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` `[repo]`. These
two are written in `MANIFEST.csv`'s *internal* spelling, which is relative to
`datasheets/`.

This is precisely the gap the brief flags: `verify-datasheets.py` checks the
manifest against disk and never the corpus against the manifest, and
`check_links` only sees Markdown link syntax, so a bare path in a YAML scalar is
invisible to both. `[test]` My own corpus→manifest scan (31 distinct
`datasheets/…` paths cited, pinned tree) found **every** path that *is* spelled
`datasheets/…` resolves and is banked `OK` — the only escapes are the two here,
which do not start with `datasheets/`.

`docs/reference/repo-maintenance.md:128` `[repo]` uses the same
manifest-relative spelling (`mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`,
`connectors/NE8FDP.pdf` …). **Lower severity**: that whole table is explicitly a
survey of the bank, its neighbouring cells use the same convention, and no row
collides with a real repo directory. Noted so a fix for `G2-13` does not
mechanically "correct" a table that is fine.

### G2-14 — `MANIFEST.csv` carries two rows for each of two files

`[test]` `csv` parse of `datasheets/MANIFEST.csv`, pinned: 101 rows, 76 distinct
non-blank `file` values, 23 rows with a blank `file` (all `BLOCKED`/`NOT-FETCHED`
— correct, an unfetched part has no file).

| `MANIFEST.csv` | `part` | `file` | `sha256` |
|---|---|---|---|
| line 2 | `DAC8568CIPW` | `analog/DAC8568CIPW.pdf` | `a9b54fefec…` |
| line 3 | `DAC8568ICPW` | `analog/DAC8568CIPW.pdf` | `a9b54fefec…` (identical) |
| line 56 | `WS2815` / `WorldSemi` | `led/WS2815.pdf` | `72e22d2f74…` |
| line 57 | `WS2815` / `Worldsemi` | `led/WS2815.pdf` | `72e22d2f74…` (identical) |

CLAUDE.md §3: "`datasheets/` holds the actual documents, **one `MANIFEST.csv`
row each** with a SHA-256."

The DAC pair is the interesting one, because it is a correction that was made by
*addition*. `hardware/bom.csv`'s `U-DAC` row `[repo]` says: "*** THE ORDER CODE
IS DAC8568ICPW, NOT DAC8568CIPW. *** … renaming it would mean editing another
wave's manifest fragment, which CLAUDE.md 4 forbids". The rule was followed —
but the result is that a corpus citation of
`datasheets/analog/DAC8568CIPW.pdf` now resolves to **two** manifest rows, one
of which carries the order code the BOM says is wrong, and nothing marks which
is current. `[repo]` the two rows come from different fragments
(`.manifest-R2.csv` and `.manifest-R9.csv`); `tools/merge-manifests.py` does not
dedupe on `file`.

`verify-datasheets.py` passes both, because it asks "does each manifest row's
file exist and hash correctly" and both rows point at the same real, correct
file. The duplicate is only visible from the direction nothing checks.

---

## C. Seeded-edge defects (lower severity, but they are the shape the README predicts)

### G2-15 — `refdes:PANEL` on `panel-led` is a substring artefact — a fourth known-false edge, of a *new* kind

`hardware/module/panel-led/circuit.yaml:16` `[repo]` declares `- refdes:PANEL`.
`[test]` a word-boundary search (`(?<![A-Z0-9-])PANEL(?![A-Z0-9-])`) over every
`.md` and `.csv` in `hardware/module/panel-led/` finds **no standalone `PANEL`**.
What is there is `LED-PANEL` and `R-LED-PANEL`.

`hardware/README.md:82–85` `[repo]` guarantees, for every edge kind including
seeded ones: "**What IS guaranteed for every edge, verified or seeded: it
RESOLVES.**" This one resolves — `PANEL` is a real BOM row — so the guarantee
holds on the letter. But the README's three known-false edges are all
*semantic* misreads (a contrast, a citation-of-a-note, a package-count
consequence). This one is **mechanical**: the seeder matched a substring. It is
the only such case in all 23 files, and it is worth adding to that table because
it says something different about how the graph was built — a reader told the
false edges are semantic will look for semantic causes.

`[test]` This is the **only** `adr:`/`fig:`/`refdes:` edge in the entire corpus
that is declared without a co-mention in its own directory. Every other one of
the 23 files' edges resolves *and* co-occurs.

### G2-16 — `R-BIAS-INAMP` is filed in the `pitch-stage` fragment, on the strength of the edge `hardware/README.md` already calls false

`hardware/module/pitch-stage/bom.csv:2` `[repo]` carries
`R-BIAS-INAMP,module,1M 1%,,"Common-mode bias return, one per in-amp input",…,0003,…`.

`hardware/README.md:73` `[repo]`, in the known-false table:

> | `pitch-stage` → `R-BIAS-INAMP` | the page names it as an explicit **contrast** |

`[test]` `grep -n "R-BIAS-INAMP" hardware/module/pitch-stage/pitch-stage.md`
returns exactly one hit, line 325: "the breath in-amp with `R-BIAS-INAMP`.
`R-BIAS-DAC` now does it here — at the …". That is the contrast, and it is the
page's *only* mention.

CLAUDE.md and `hardware/README.md:95` both say: "A row lives with the circuit
**whose page derives its value** — not where it is mentioned". The value is
derived at `hardware/interfaces/breath-sense-link/breath-sense-link.md:149`
`[repo]` — "| **R4, R5** | 1 MΩ | **Common-mode bias return.** Without these the
in-amp's inputs float when the cable is unplugged and it saturates to a rail |"
— with the CMRR consequence at `:95` and `:163`, and the row's `adr` column says
`0003`, not `0006`.

So the corpus has *already diagnosed* this edge as a false co-mention, and the
BOM fragment placement it produced was not revisited. The edge is annotated;
the consequence is not.

### G2-17 — `config/key-layout.yaml` says "do not restate the number here" and restates it in the preceding line

`config/key-layout.yaml:30–31` `[repo]`:

> `# SETTLED at 1.20 mm - the tracked figure is \`plate-thickness\`, read off`
> `# Gateron's banked drawing. Do not restate the number here; this field`
> `# exists so the generator has it …`

The data field `plate_thickness: 1.20` is defensible and the comment says why.
The *comment's own opening clause* is not: it states the value one line above
forbidding it. Minor, and I raise it only because this comment is the corpus's
written-down explanation of the rule-1 boundary for machine-readable files, and
it is the one place a reader would go to learn where that boundary sits.

---

## D. Claims I tested and found TRUE

A cold slice's negatives are evidence, and several of these are claims the
corpus makes about itself that nothing had checked.

**G2-18 — The `circuit:` edge rule holds exactly, in all 23 files, in both
directions.** `hardware/README.md:60–64` states the rule mechanically: "ONE
`circuit:` edge per distinct `board/circuit` id in the **Peer** column of this
circuit's `## Interfaces` table, AND every such edge is declared from **both**
ends." `[test]` I parsed each page's `## Interfaces` table, extracted the `Peer`
column by header position, and compared the set of corpus circuit ids named
there against the `circuit:` edges in that directory's `circuit.yaml`.
**Zero mismatches in either direction, across all 23.** Zero non-mutual edges.
This is the one edge class the README calls verified, and it is verified.

*(Worth recording for whoever tests this next: a naive version of this check that
searches the whole Interfaces **section** rather than the `Peer` **column**
reports three false positives — `breath-sense-link → module/dac8568`,
`breath-sense-link → module/power-entry`, `spi-link → module/link-supervision`,
`breath-receive-stage → module/dac8568`. All four are `Note`-column mentions on
rows whose `Peer` is `—`, and three of those rows exist precisely to say the net
reaches nothing here. Parse the column.)*

**G2-19 — Every `adr:`, `fig:` and `refdes:` edge resolves.** `[test]` 23 files,
all four edge kinds, against `docs/decisions/*`, the 37 register ids, and
`hardware/bom.csv`'s `ref` column: **zero unresolved**. The `hardware/README.md`
guarantee holds.

**G2-20 — Every Markdown link and every `#anchor` in the corpus resolves.**
`[test]` all `](…)` targets in `hardware/**`, `docs/decisions/**`,
`docs/reference/**`, `config/**`, `firmware/**`, `README.md`, `ROADMAP.md`,
with anchors slugged GitHub-style and checked against the target's headings:
**zero broken links, zero missing anchors.**

**G2-21 — Every figure-name citation in the corpus resolves to a register
entry.** `[test]` a scan for lowercase hyphenated identifiers following
"figure"/"tracked figure"/"figures.yaml" found no token that is not an `id` in
`config/figures.yaml`. There is no citation of a deleted or renamed figure.

**G2-22 — No `## Interfaces` table restates a tracked figure's value.** This is
the claim each of the 23 tables makes about itself in its own preamble
("Quantities appear **only** as a citation into `config/figures.yaml` — this
table names nodes, it does not restate values"). `[test]` I extracted every
number-plus-unit from every Interfaces table row. Every hit is a **net name**
(`+12V`, `−12V`, `+5V`, `±12 V`) or an untracked incidental (`100 nF`, `0 Ω`
strap, "resting at `0 V`"). **No tracked figure's value appears in any of them.**
`panel.md`'s failure (`G2-2`) is in its *page header and prose*, not its table.

**G2-23 — The ADR index's `Status` column matches all 14 ADRs.**
`docs/decisions/README.md` flags itself as hand-maintained and previously wrong
in three rows. `[test]` comparing each row against the `**Status:**` line of the
file it points at: **all 14 agree.** (0008's row omits the ADR's "(base, not
Plus)" qualifier — an omission, not a contradiction.)

**G2-24 — Every `datasheets/…` path cited in the corpus is banked and `OK`.**
`[test]` 31 distinct cited paths (excluding `path-map-2026-09-21.csv`, which is
an old→new map and whose old paths dangle by design): all resolve on disk, all
appear in `MANIFEST.csv`, **none has a non-`OK` status**. The only three
non-matches are `datasheets/.manifest-R` (my regex clipping the `*.csv` glob in
`repo-maintenance.md:18`), `datasheets/.moves.csv` and `datasheets/mechanical`
— a file and a directory, both real, neither a manifest entry.

**G2-25 — Spot-checked ADR attributions that hold.** Each verified by locating
the claim in the named ADR `[repo]`:

| citing text | verdict |
|---|---|
| `key-chain-loom.md:36,83` — the two spares are "ADR 0009's rule" | **TRUE**, `0009:524` "Run two spare conductors in every internal loom." |
| `breath-sense-link.md:125` — ADR 0003 says "band-limit at both ends, around 500 Hz" | **TRUE**, `0003:409` verbatim |
| `key-chain-loom.md:58,102,105` — ADR 0001 "fix 1 / fix 2 / fix 3" | **TRUE**, `0001:246` (highest-value item), `:267` (chain don't star), `:269` (bit order) |
| `0004:216` — "The LM317 rail is `dac-rail`, which is in the second band" | **TRUE** `[calc]`: `dac-rail` = 5.21 V, and SBAS430E's second band is 4.5–5.5 V |
| `0004:330`, `0006:652` — `diode-split-rationale` "owned by `power-entry.md` … not restated here" | **TRUE** on both counts; `[test]` neither ADR contains `69 m`, `392 mA`, `120 mV`, `0.24 V` or `0.36 V` |
| `mod-channels.md:200` — "At `mod-reference` into 2.5 kΩ that is **1.33 mA**" | **TRUE** `[calc]` 3.3333/2500 = 1.3333 mA |
| `0004:766` — "`panel-width`'s `(10 × 5.08) − 0.3`" | **TRUE**, matches the register's `derivation` |
| `ROADMAP.md:203` — "`chain-conductors` per hop rather than the 32–44 the tail-mounted alternative needed" | **TRUE**, `0001:135` tabulates 12 vs 32–44 |
| `pcb-pipeline.md:359` — "`hardware/module/power-entry/bom.csv`'s `J-UMBILICAL` row is where those dimensions live" | **TRUE**, the row is in that fragment |
| `repo-maintenance.md:120`, `pcb-pipeline.md:338` — "all 60 banked PDFs" | **TRUE**, `[test]` `find datasheets -name '*.pdf' \| wc -l` → 60 |
| `firmware/README.md:27` — `ks33-contact-bounce` "read verbatim off Gateron's own drawing" | **TRUE**, `MANIFEST.csv` row 70 records "BOUNCE TIME 5 msec Max at 16 in/sec actuation" in the banked PDF |
| `module.md:36` — `dig-gnd-topology` is `power-entry/`'s and "tracked as `disputed`" | **TRUE** on both |
| `ks33-geometry.md:108`, `breath-receive-stage.md:121`, `panel.md:62` — "this page owns it" | **TRUE** for `plate-thickness`, `breath-zero-ref`, `panel-toggle-hole` respectively |
| `dac8568.md:20` — "The figure's `floor` is a C-grade condition, not a preference" | **TRUE**, `dac-rail.floor` is exactly that |
| `mod-channels.md` watchdog argument (CLAUDE.md §5's example) | **FIXED** — `:160–168` now carries the refutation and re-derives what asserts `CLR` |

**G2-26 — Apparently-dangling refdes mentions that are legitimate refutations,
not defects.** `[test]` A strict refdes scan (BOM prefixes only, word-bounded)
over `.md` and BOM cells flags `R-SCLK-SER`, `R-MOSI-SER`, `R-CS-SER`,
`R-TERM-CHAIN`, `R-PD-BREATH` and `SW-PWR-INST` as naming no BOM row. **All six
are correct prose**: `spi-link.md:58–63` and `0004:558` say those three refdeses
"**none of which exist in `bom.csv`**"; `0001:182` says "`R-TERM-CHAIN` is not
restored"; `R-BIAS-INAMP`'s row says "REPLACES `R-PD-BREATH`"; `0005:241` says
"**So `SW-PWR-INST` is deleted.**" This is rule 2b working as intended, and I
record it so a future mechanical sweep does not "fix" six correct sentences.

*(A related non-defect worth naming: `J-UMB` appears 24 times across 11 corpus
files while the BOM row is `J-UMBILICAL`; likewise `J-DISP`, `J-LED-L/-R`,
`C-GATE`, `C-TIMER`, `LK-CLR`, `C-ADC-BULK`. These read as drawing labels and
short forms rather than refdes claims, and the `## Interfaces` tables — the
place that exists to disambiguate names — use `J-UMB` consistently. I flag it
as a naming question for whoever does the netlist precursor, **not** as a
finding.)*

---

## What I could NOT check

- **Whether `check_links` and `check_sections` actually do what they claim.** I
  read their docstrings and re-implemented link/anchor resolution
  independently (`G2-20`), but I deliberately did not rely on running
  `tools/check-staleness.py`, because the coordinator confirms the tool was
  patched in-tree during this slice. My independent implementation agrees with
  the tool's claimed scope; I cannot say whether the tool as shipped does.
- **`§N` section references.** `check_sections` owns these and I did not
  duplicate it, having decided my time was better spent on claims nothing
  checks. So `carrier.md §2`, `§3`, `§4` and their siblings are **unverified by
  me**. Given `G2-5`, the line-number class of reference in the same register is
  worth someone re-testing by hand.
- **Whether a cited *datasheet page number* says what it is cited for.** I
  verified paths, manifest entries and statuses, not page contents. `G2-25`'s
  datasheet rows rest on `MANIFEST.csv`'s own notes field, which is a corpus
  claim about a document, not the document.
- **The 211 "restated-not-cited" advisories.** I confirmed several by hand
  (`0001:227–230` restates `key-release-time` and `key-press-time`;
  `panel.md` restates two figures; `key-layout.yaml` restates
  `plate-thickness`), but I did not enumerate them. They are rule-1 violations,
  not cross-reference defects, and they are already counted.
- **Whether any of `docs/review/`, `docs/log/` or `docs/research/` cross-reference
  the corpus correctly.** Out of scope by §6, and I could not have read them
  anyway.
- **Anything about `tools/` behaviour**, per the note above. I make no `[test]`
  claim that depends on a tool I did not write in this session.

---

## One structural observation

Nine of the thirteen defects above are **correct information that exists
somewhere in the corpus and is contradicted somewhere else in the corpus**.
`sim/README.md` knows `cref-out-node` is settled while `pcb-pipeline.md` does
not. `figures.yaml` knows 2.8 kPa is not in ADR 0003 while
`breath-output-stage.md` cites it there. `key-scan-current`'s `escape_note`
knows the deduplication is owed while its `companion` says it happened.
`hardware/README.md` knows `pitch-stage → R-BIAS-INAMP` is a false edge while
`pitch-stage/bom.csv` holds the row.

In every one of those, **the correction was written as a new statement beside
the old one rather than as an edit to it.** That is the honest instinct — it
preserves the record, and rule 2b's cut line exists because the alternative
produced 118 kB of BOM logs. But in prose the same instinct produces a corpus
where the true version and the false version are both live, both cite-able, and
distinguishable only by date. The cut line ("KEEP what tells a builder WHAT TO
DO / CUT what tells them WHAT SOMEONE USED TO THINK") resolves this cleanly for
`.csv` cells. It has no counterpart for a cross-reference, and these nine are
what that gap costs.
