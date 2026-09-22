# D11 — `datasheets/`, the R9 fragment, and the DAC order-code chain

**Slice:** `datasheets/**`, `datasheets/.manifest-R9.csv`, the
`DAC8568CIPW` → `DAC8568ICPW` chain, and the provenance of figures read off
banked documents.
**Method:** cold. `docs/review/**` not read except this wave's `README.md`.
Git log and `git diff` used. PDFs read with `pymupdf` per the wave README.
**Corpus state:** `0e68f25~1..HEAD`; the datasheet work is all in `b32c557`.

Provenance markers on every claim: `[repo]`, `[calc]`, `[datasheet]`,
`[test]`, `[from memory]`.

---

## Verdict in one page

**The order code is right.** `DAC8568ICPW` is the correct orderable C-grade
part, the whole C-grade argument holds for it, and `CLAUDE.md` §4 was obeyed —
no prior fragment was touched. Ten datasheet-sourced figures spot-checked
against the banked documents; **nine confirmed verbatim, one has a wrong
supporting detail** and one restated character count is wrong.

**What is not complete** is everything downstream of the order code, and the
pattern is the project's named failure mode in its purest form: the fix landed
in the three files the fixer was editing and in none of the three places a
*reader* arrives from.

| # | Finding | Severity |
|---|---|---|
| D11-1 | The stated reason for not renaming the banked file is **false** — `.moves.csv` exists for exactly this and already rewrites this file's path. Repeated in three places. | **High** |
| D11-2 | `MANIFEST.csv` still carries `DAC8568CIPW` as a live `OK` row with no marker, sorted **above** the corrected one; R9's `SUPERSEDES` keyword is invisible to `merge-manifests.py` by construction. | **High** |
| D11-3 | `D-TVS-BREATH`'s three unsourced numbers are **still unmarked in `hardware/bom.csv`**. The caveat exists only inside a 127 kB generated CSV. The `U-TVS-SPI` row two lines away does it correctly. | **High** |
| D11-4 | The new `BLOCKED` row misattributes those numbers: two of the three are about a *rejected* part and one is `[calc]` off a tracked figure. The datasheet it blocks on can never settle them. | Medium |
| D11-5 | `datasheets/README.md` §"What is still missing" was not updated; the new highest-consequence gap is absent while three lesser ones are listed. Its "one row per part" rule is now contradicted. | Medium |
| D11-6 | Both new rows put the literal string `BLOCKED` in the **`sha256`** column. Schema violation, unchecked, inconsistent with all 21 other no-file rows. | Medium |
| D11-7 | `verify-datasheets.py`'s "78 verified" counts **rows, not documents**: 76 files, two counted twice. R9 raised that number by one while banking nothing. | Medium |
| D11-8 | The BOM-coverage claim is true but weak: **26 of 139 BOM rows are tested**. `ESP32-S3-Matrix` — one of the three parts the tool's own comment says were hiding in this blind spot — is still skipped. | Medium |
| D11-9 | `check_datasheets()` returns `[]` on exit 0, so **the advisory half of `verify-datasheets`' output never reaches the commit hook**. Wiring it in captured the exit code and discarded the report. | Medium |
| D11-10 | `check_verified_against()` has **zero inputs**. No `circuit.yaml` in the tree declares `verified_against`; all 23 were rewritten in this batch and none gained one. The SHA-256 bank has no machine link to any figure. | Medium |
| D11-11 | "Package Option Addendum (p.54-57)" — it is p.54–55. Restated in four places. | Low |
| D11-12 | The two `BLOCKED` rows record *candidate* URLs with no attempt evidence, unlike every other blocked row in the manifest. | Low |
| D11-13 | `panel-toggle-hole`'s derivation says the NKK drawing has "no text layer". `repo-maintenance.md` §3 already corrects that claim for this exact document. | Low |
| — | **Sibling claim confirmed.** The Gateron character count: `11 kB` is right, **`~9,680` in `config/figures.yaml` is wrong**. | Medium |

---

## 1. The order code — confirmed, and the C-grade argument holds

`[datasheet] datasheets/analog/DAC8568CIPW.pdf` = TI **SBAS430E**,
DAC7568/DAC8168/DAC8568, Jan 2009 rev Jan 2014, 62 pp, sha
`a9b54fefecaa…`. Read with `pymupdf`, 132,163 characters extracted.

`[test]` Every `DAC8568*` token in the document, with counts:

```
190  DAC8568          1  DAC8568IAPW     1  DAC8568IBPW
  1  DAC8568A         3  DAC8568IAPWR    3  DAC8568IBPWR
  1  DAC8568B         1  DAC8568ICPW     1  DAC8568IDPW
  1  DAC8568C         3  DAC8568ICPWR    3  DAC8568IDPWR
  1  DAC8568D
"CIPW": 0 occurrences        "ICPW": 12 occurrences
```

**`DAC8568CIPW` appears zero times. `DAC8568ICPW` is the C grade.**
`[datasheet] p.54`, PACKAGING INFORMATION table:
`DAC8568ICPW | ACTIVE | TSSOP | PW | 16 | 90 | Green (RoHS & no Sb/Br) |
CU NIPDAU | Level-2-260C-1 YEAR | -40 to 125 | DA8568C`.

**The C-grade argument holds for `ICPW` on every leg.** The structure is
`DAC8568` + `I` (temperature grade, −40 to +125 °C) + `C` (product grade) +
`PW` (TSSOP-16), so `ICPW` *is* the C-grade part and inherits every C-grade
property `[calc]`:

| Corpus claim | Datasheet | Verdict |
|---|---|---|
| C/D are gain 2, 5 V full scale; A/B gain 1, 2.500 V | `[datasheet] p.2 Table 1`: `DAC8568C … 5V` reference-mode full scale; p.24 and p.48 *"Gain = 1 for A/B grades or 2 for C/D grades"* | **Confirmed** |
| C clears to **zero** scale; B/D to midscale | `[datasheet] p.38`, verbatim: *"For device grades A and C on power-up, all DAC registers are filled with zeros and the output voltages of all DAC channels are set to zero scale. For device grades B and D all DAC registers are set to have all DAC channels power up in midscale."* | **Confirmed** |
| Reference tempco is grade-dependent: C/D 2 typ / 5 max, A/B 5 typ / 25 max ppm/°C | `[datasheet] p.4` Reference Output block: *grades A/B* `5 … 25`, *grades C/D* `2 … 5`; corroborated by the three drift histograms p.7 (`Typ: 2ppm/°C Max: 5ppm/°C` and `Typ: 5ppm/°C Max: 25ppm/°C`) and p.46 *"The internal reference (grade C only) … 2ppm/°C … a maximum drift coefficient of 5ppm/°C (grade C only)"* | **Confirmed** |
| External `VREFIN` ≤ AVDD/2 on C/D, ≤ AVDD on A/B | `[datasheet] p.6 footnote (1)`, verbatim; and p.4 reference-input-range rows | **Confirmed** |

**One nuance on the 5.00 V hard floor** (`figures.yaml` `dac-rail.floor`,
`ROADMAP.md:48`, `bom.csv` `U-DAC`). The value is right; the stated
*mechanism* overstates. The corpus says *"the Electrical Characteristics
table specifies grades C/D only over that range, where A/B are specified
2.7–5.5 V"*. `[datasheet]` Every EC table header in SBAS430E reads
*"At AVDD = 2.7V to 5.5V and over −40°C to +125°C"* (pp.3, 4, 5), and p.6
gives `AVDD` as *"Power-supply input, 2.7V to 5.5V"* for all grades. Exactly
**two** rows carry a grade-conditioned supply range: the output-voltage range
(*"AVDD ≥5V; grades C and D: maximum output voltage 5V when using internal
reference"*, p.3) and the `VREFIN` input range (*"Grades C/D, AVDD = 5.0V to
5.5V"*, p.4). So the floor is real and sourced — **`AVDD ≥ 5 V` is stated
verbatim for C/D** — but it is a headroom condition on two parameters, not a
whole-table restriction. **Not a defect in the number; a defect in one
sentence of its provenance, in three files.** The conclusion is unchanged.

`[datasheet]` **D11-11.** "Package Option Addendum (p.54-57)" is wrong by two
pages: the `PACKAGE OPTION ADDENDUM` header appears on pp.54–55 only (the
orderable table is entirely on p.54; p.55 is the footnote key), and pp.56–57
are headed `PACKAGE MATERIALS INFORMATION` (tape-and-reel and shipping-box
dimensions). `[repo]` The `p.54-57` spelling is restated in
`hardware/module/dac8568/bom.csv:4`, `hardware/bom.csv:77`,
`datasheets/.manifest-R9.csv:2` → `datasheets/MANIFEST.csv:3`, and
`b32c557`'s commit message. Four copies of one imprecise citation — the
restate-don't-cite shape, on a page number.

---

## 2. The chain — every remaining occurrence, classified

`[repo]` `grep -rn "DAC8568CIPW\|DAC8568ICPW"`, excluding `.git` and the
three historical trees. Thirteen live occurrences outside `docs/review/**`:

| # | Location | What it says | Class |
|---|---|---|---|
| 1 | `hardware/module/dac8568/bom.csv:4` | `part` = `DAC8568ICPW`; notes narrate the transposition | **correct** |
| 2 | `hardware/bom.csv:77` | generated from (1) | **correct** |
| 3 | `docs/decisions/0006-cv-channel-allocation.md:176` | *"locked to `DAC8568ICPW`. (This read `DAC8568CIPW` until 2026-09-21…)"* | **correct** — refutation on the same line, so the checker's neighbour rule is satisfied |
| 4 | `docs/decisions/0006:183` | file path | **correct** |
| 5 | `config/figures.yaml:352` | file path in `dac-rail.floor` | **correct** (resolves) |
| 6 | `ROADMAP.md:48` | file path in E7 | **correct** (resolves) |
| 7 | `docs/reference/path-map-2026-09-21.csv:96` | `texas-instruments/…` → `analog/…` | **correctly historical** |
| 8 | `datasheets/.moves.csv:2` | same move, the live lookup | **correct** |
| 9 | `datasheets/.manifest-R2.csv:2` | R2's own row, `part` = `DAC8568CIPW` | **correctly historical** — append-only, must not be edited |
| 10 | `datasheets/.manifest-R9.csv:2` | the corrected row | **correct** |
| 11 | `datasheets/MANIFEST.csv:2` | generated from (9) | **still wrong in effect — see D11-2** |
| 12 | `datasheets/MANIFEST.csv:3` | generated from (10) | **correct** |
| 13 | `hardware/module/dac8568/{dac8568.md:1, circuit.yaml:41, notes.md:1}` | titled *"DAC8568C — schematic"* | **correct** — `DAC8568C` is SBAS430E's own product name `[datasheet] p.2 Table 1`, not a truncated order code |

`[repo]` `firmware/**` contains no DAC part string. Nothing dangles.

### D11-1 (High). The reason for not renaming the file is false

Three documents give the same reason, in the same words:

- `[repo] b32c557` commit message: *"The file keeps its name: renaming it
  means editing another wave's fragment, which CLAUDE.md section 4 forbids."*
- `[repo] datasheets/.manifest-R9.csv:2` → `MANIFEST.csv:3`: *"The FILE keeps
  its original name because renaming it would mean editing another wave's
  fragment."*
- `[repo] hardware/bom.csv:77` (`U-DAC` notes): *"renaming it would mean
  editing another wave's manifest fragment, which CLAUDE.md 4 forbids."*

**It does not.** `datasheets/.moves.csv` exists precisely to re-file a banked
document without touching a fragment, and `tools/merge-manifests.py` says so
at length in its own comment block `[repo] tools/merge-manifests.py:30-58`:

> *"This tool ALREADY rewrites the `file` column … Path normalisation at merge
> time is therefore an established, documented, sanctioned transformation that
> does not count as editing a fragment. A move table is the same transformation
> with a lookup instead of a prefix strip. Properties that make it the right
> answer: no fragment changes: all eight `.manifest-R*.csv` stay
> byte-identical…"*

**And it is already applied to this exact file.** `[repo]
datasheets/.moves.csv:2` maps
`texas-instruments/DAC8568CIPW.pdf → analog/DAC8568CIPW.pdf`. Renaming means
changing that one row's `new_path` to `analog/DAC8568ICPW.pdf` and
`git mv`-ing the file. `[calc]` The mechanics work: R2's row and R9's row both
name the same `old_path`, so both resolve to the new name; no chain is created
(`analog/DAC8568ICPW.pdf` never appears as an `old_path`, so the tool's
chain refusal at `merge-manifests.py:98-104` does not fire); the dedup branch
already handles two rows landing on one path with the same SHA; and the two
corpus citations (`figures.yaml:352`, `ROADMAP.md:48`) would be caught
immediately by `verify-datasheets.py`'s corpus-path check if missed.

Whether to rename is a judgement call — `[calc]` the honest cost is one
`.moves.csv` edit plus two corpus citations, against the benefit of a bank
that is not filed under a part number that does not exist. **The finding is
not that the decision is wrong. It is that the recorded reason is not true,
it invokes a rule that does not apply, and it is now in three places
including the BOM row that `CLAUDE.md` calls the most-cited file in the
repository.** A reader who accepts it learns a false constraint about
`.moves.csv`. *What would settle the judgement call:* the maintainer's
preference. *What settles the reason:* `merge-manifests.py:30-58`, above.

**Is the reasoning recorded where a reader finds it?** Partly. A reader
arriving from `hardware/bom.csv` or from ADR 0006 finds it. A reader arriving
from `datasheets/README.md` or from a listing of `datasheets/analog/` finds
**nothing** — `[repo] grep -n "DAC8568\|ICPW\|CIPW" datasheets/README.md`
returns no hits. The one directory whose job is to explain the bank does not
mention that one of its 60 PDFs is named after a nonexistent part.

### D11-2 (High). The manifest still asserts the wrong code, and the `SUPERSEDES` keyword does nothing

`[repo] datasheets/MANIFEST.csv` rows 2 and 3, in file order:

```
DAC8568CIPW,…,analog/DAC8568CIPW.pdf,a9b54fe…,…,OK,"SBAS430E Rev E (Jan 2014), English, 62pp. …"
DAC8568ICPW,…,analog/DAC8568CIPW.pdf,a9b54fe…,…,OK,"SUPERSEDES the part string on the DAC8568CIPW row …"
```

Row 2 is a **live `status=OK` row asserting `DAC8568CIPW` as a part**, with
notes that say nothing about the transposition, sorted *above* the corrected
row (`rows.sort(key=lambda r: (r[2] or "zzz", r[0]))` — same path, so
`DAC8568CIPW` < `DAC8568ICPW` alphabetically). A reader grepping the manifest
for the code lands on the unqualified one first. Row 2 is correctly
*immutable* — it is generated from R2's append-only fragment — so the fix
must be visible some other way, and R9 tried the sanctioned way and it
silently failed.

`[repo] tools/merge-manifests.py` recognises a declared supersession only for
rows with **no file**:

```python
for r in rows:
    if r[2] or r[6].upper() not in ("BLOCKED", "NOT-FETCHED") or id(r) in _exact:
        continue                      # <-- r[2] is the file column
```

R2's DAC row has a file *and* status `OK`, so it is skipped twice over.
`[test] python3 tools/merge-manifests.py --check` prints
`SUPERSEDED (declared): 1 row(s)` — the NKK toggle, **not the DAC**. The
`SUPERSEDES` keyword R9 wrote in the format `datasheets/README.md` prescribes
produces no output at any time.

The `--check` guard also passes cleanly `[test] exit 0`, and
`verify-datasheets.py` passes `[test] exit 0`, so **nothing anywhere reports
that two `OK` rows disagree about the name of one document**. This is the
tooling gap the fix walked through: had R9 used the *same* part string with a
corrected file, `key = (r[0], r[2])` would have collided and `merge-manifests`
would have flagged a duplicate. Changing the part string instead makes the
pair invisible.

*Cheapest honest fix, no fragment edited:* extend the declared-supersession
rule to cover an `OK` row that names a file, so a row quoting another row's
exact part string plus `SUPERSEDES` is reported as a **part-string
correction** on every run — `repo-maintenance.md` §3 option 1 ("fix the
tooling, if what you want is for a *check* to see something") is exactly this
case.

---

## 3. Two rows, one file — it double-counts, and reports nothing

`[test] python3 tools/verify-datasheets.py`:

```
datasheets: 78 verified, 23 recorded as blocked or not-fetched, 0 problems
```

`[calc]` Measured against the same manifest: **101 rows; 78 rows name a file;
76 distinct files; 76 artefacts on disk.** Two files are named by two rows
each:

| File | Rows | Cause |
|---|---|---|
| `analog/DAC8568CIPW.pdf` | `DAC8568CIPW` (R2), `DAC8568ICPW` (R9) | **created by this fix batch** |
| `led/WS2815.pdf` | `WS2815` (R4), `WS2815` (R6) | pre-existing, documented in `repo-maintenance.md` §3 and `pcb-pipeline.md:366` |

**"78 verified" is a row count presented as a document count.** The loop does
`ok += 1` per row and re-reads and re-hashes the 2.3 MB DAC PDF twice. R9
moved the headline from 77 to 78 **while banking zero new documents** —
precisely the shape `README.md:119` removed the "77 banked documents" count to
avoid. The `listed` set used for the orphan-file walk is a `set`, so the
double row causes no false "artefact with no MANIFEST row"; the only
consequence is the count, and it is the number a reader would quote.

Nothing reports the double coverage. `verify-datasheets.py` has no
rows-per-file check at all. `merge-manifests.py` reports the WS2815 pair
(`DE-DUPLICATED: 1 row(s)`) only because that pair arose from a `.moves.csv`
move; the DAC pair has different part strings and never reaches the duplicate
branch. `[test]` Confirmed by the tool's own output above.

*Suggested:* print `N verified across M documents` and name any file carried
by more than one row. Two rows on one document is legitimate here — twice —
and both cases are worth one line of output rather than none.

---

## 4. The two `BLOCKED` rows

### The URLs

`[repo] datasheets/.manifest-R9.csv`:

```
PESD12VS1UB  https://www.nexperia.com/product/PESD12VS1UB
             https://assets.nexperia.com/documents/data-sheet/PESD12VS1UB.pdf
USBLC6-2SC6  https://www.st.com/en/protection-devices/usblc6-2.html
             https://www.st.com/resource/en/datasheet/usblc6-2.pdf
```

`[calc]` Both URL schemes are the vendors' real ones —
`nexperia.com/product/<MPN>`, `assets.nexperia.com/documents/data-sheet/<MPN>.pdf`,
`st.com/resource/en/datasheet/<doc>.pdf` — and `st.com`'s datasheet slug for
this family is the family name `usblc6-2`, not the package-suffixed
`usblc6-2sc6`, which is the right choice. `[test] curl -sSL --max-time 25`:

```
403  391 B  text/html   https://www.nexperia.com/product/PESD12VS1UB
403  423 B  text/html   https://assets.nexperia.com/documents/data-sheet/PESD12VS1UB.pdf
000    0 B              https://www.st.com/en/protection-devices/usblc6-2.html
000    0 B              https://www.st.com/resource/en/datasheet/usblc6-2.pdf
```

**Plausible and correctly formed; unreachable from this container.** So
`BLOCKED` is the right status. But note **D11-12**: the rows say only
*"NOT FETCHED"*. Every other blocked row in this manifest records the exact
failure — `(HTTP 000)`, `403 at the proxy`, `connect_rejected`, the GitHub
code-search queries tried. `[repo]` Compare the `OPA2197IDR`, `REF5050AIDR`
and `SP0504BAHT` rows, which are models of the form. `CLAUDE.md` §3 asks for
`status=BLOCKED` and *"the exact URLs"* — satisfied literally — and
`datasheets/README.md` asks for *"the exact URL **and the exact error**"* —
not satisfied. These are candidate-URL rows, not attempt records. The two
HTTP codes above are my evidence, not the row's.

### Do the rows say what decides them?

Yes for `PESD12VS1UB` (*"BLOCKING on the datasheet"*) and yes for
`USBLC6-2SC6` (*"Zero-consequence gap … status not-needed"*, which `[repo]
hardware/bom.csv:119` confirms). `[repo]` The `USBLC6-2SC6` assessment is
correct: `grep -rn "USBLC6"` over the corpus finds only its own BOM row and
`unplaced.csv`, and no figure derives from it.

### D11-3 (High). `D-TVS-BREATH`'s three numbers are still unmarked where a reader sees them

The R9 note states the problem exactly right:

> *"the BOM row makes three numeric claims about this part — a 5V array's
> `V_RWM`, the margin against it, and 1.5uA of leakage — and none of them has
> a document behind it."*

`[repo] hardware/bom.csv:44` — the row itself, unchanged by this batch:

> *"12V STANDOFF, NOT 5V. BREATH's normal top of range is sensor-full-scale
> against a 5V array's `V_RWM` - 140mV of margin, NOT the 300mV this row
> claimed while it was using a retired 4.7V on the project's DC-accurate
> output, with 1.5uA of leakage into a 1k output resistor."*

`[repo]` `grep -rn "140 ?mV\|1\.5 ?uA\|V_RWM"` across `hardware/**`,
`config/**`, `docs/decisions/**`, `docs/reference/**`, `README.md`,
`ROADMAP.md`: the three numbers appear **only** in this row (its fragment at
`hardware/interfaces/breath-sense-link/bom.csv:4` and the generated master).
There is **no unsourced marker on any of them**, and the `package` column
asserts a fourth unsourced fact, `SOD-323`.

The caveat exists in exactly one place: the `notes` column of a row in a
127 kB generated CSV nobody reads linearly. `repo-maintenance.md` §3 option 2
— *"Put it in `hardware/bom.csv`, if it is a fact about the part"* — is the
procedure the **DAC** half of this same commit followed correctly and cited by
name. The TVS half did not. And `[repo] hardware/bom.csv:48`, two rows away,
shows the convention applied properly on the same day: `U-TVS-SPI` carries
*"the 0.98W sustained-fault figure this row's protection budget assumes has
never had a source"* and *"THE 0.98 W FIGURE IS DELETED, NOT CORRECTED"*
inline, where a reader meets it. **Same commit, same file, same failure mode,
opposite treatment.**

`[repo]` There is also a machine-checkable slot for this and it is empty. The
register supports `blocked_on` (`figures.yaml` uses it), and
`tools/check-staleness.py:530-570` (`check_verified_against`) enforces
*"a `verified_against` entry that is `BLOCKED` must say what decides it — the
same rule `CLAUDE.md` applies to a `TBD`"*. `hardware/interfaces/breath-sense-link/circuit.yaml`
has no `verified_against` block — see **D11-10**, no file in the repository
does.

### D11-4 (Medium). The row blocks on a document that cannot settle two of its three numbers

`[calc]` Taking the three claims one at a time:

1. **"a 5V array's `V_RWM`"** — 5.0 V. This is a property of the **5 V array
   that was rejected**, not of `PESD12VS1UB`. The Nexperia datasheet will
   never state it.
2. **"140mV of margin"** — `[calc]` `5.00 V − 4.86 V = 0.14 V`, where 4.86 V
   is the tracked figure `sensor-full-scale` (`[repo] config/figures.yaml`,
   `status: settled`, owner `docs/decisions/0003`, which I verified in §7
   below). This is **arithmetic off a tracked figure against the rejected
   part's rating**. No datasheet for the *chosen* part is involved. It is also
   a restatement of a tracked figure's consequence rather than a citation of
   it — one of the 233 advisory restatements `[test]` the hook reports.
3. **"1.5uA of leakage"** — the only one of the three that is genuinely a
   claim about a part, and `[from memory]` 1.5 µA is a plausible `I_R` order
   of magnitude for a small unidirectional ESD diode but I cannot attach it to
   any specific part from the corpus. **This one the Nexperia datasheet would
   settle.**

So the blocked row's framing — *"three numeric claims about this part"* — is
wrong about two of the three, and the gap as written can never close: the
document arrives, and 1 and 2 are still unsourced because they were never
about that document. `[calc]` What the `PESD12VS1UB` datasheet would actually
settle, and what the row should name as `blocked_on`: the **1.5 µA leakage**,
the **`SOD-323` package** claim, and **that the part is a 12 V-standoff
device at all** — which is the entire reason it is on this node.

`[from memory]` One further item I flag as **uncertain, not as a finding**:
Nexperia's `…UB` suffix on the `PESD` line is, to my recollection, the
leadless **SOD882 / DFN1006-2** package rather than `SOD-323`. If that is
right, `[repo] docs/decisions/0013:259` (*"QFN, BGA, leadless | 0.5 mm, hidden
pads | **Avoid**"*) is engaged, and this would be the **third** part struck
from a TVS row for the same reason after `SP3012-06UTG` and `ESD7104`. I
cannot confirm it — the document is blocked, and guessing is the error this
directory exists to prevent. *What would settle it:* the Nexperia product
page's package field, or the datasheet. Recording it here so the next
researcher who reaches `nexperia.com` checks the package and not only the
leakage.

### D11-5 (Medium). `datasheets/README.md` did not follow

`[repo] datasheets/README.md:91` §*"What is still missing, and why it
matters"* lists three open gaps: `WS2812B-0807`, `5400fc.pdf`, and the Tai-Hao
`MT165`. R9's own note says `PESD12VS1UB` is *"qty 2, drawn, sits on the
DC-accurate analog output, and is unretrofittable after bonding"* — by that
description **the most consequential open gap in the bank** — and it is not in
that list. The section's closing line, *"The rest are second sources and
substitutes whose absence is recorded in the relevant BOM row"*, is now false
for this part, since the BOM row does not record the absence (D11-3).

`[repo] datasheets/README.md:16` also states the rule
*"**`MANIFEST.csv` has one row per part**"*, which R9 deliberately broke — two
rows for one document under two part strings — and which the WS2815 pair had
already broken in the other direction. The exception is documented in
`repo-maintenance.md` §3 and in `pcb-pipeline.md:366`, i.e. everywhere except
the page stating the rule.

### D11-6 (Medium). `sha256` = `BLOCKED`

`[repo] datasheets/.manifest-R9.csv`, both new rows, column 4:

```
PESD12VS1UB,Nexperia,,BLOCKED,https://www.nexperia.com/…
USBLC6-2SC6,STMicroelectronics,,BLOCKED,https://www.st.com/…
```

`[calc]` All 21 other no-file rows in the manifest leave `sha256` **empty**
(`NE8MC,Neutrik,,,https://…`). These two put the literal string `BLOCKED` in
a column whose contract is a SHA-256, and duplicate the `status` column that
already says `BLOCKED`.

Nothing catches it. `[repo] tools/verify-datasheets.py` reads `sha256` only
inside the `if fname:` branch, so a no-file row's value is never examined;
`merge-manifests.py` validates the header and the column *count* but no
column's *content*. `[repo] tools/check-staleness.py:541-543` does
`if r.get("sha256"): have.setdefault(r["sha256"].strip(), …)`, which registers
a `have["BLOCKED"] = {PESD12VS1UB, USBLC6-2SC6}` entry — **harmless today**
because the `sha == "BLOCKED"` branch at line 549 `continue`s before the
lookup, and `[repo]` no `circuit.yaml` declares `verified_against` at all. I
report it as a schema defect and a latent trap, not a live bug.

---

## 5. `CLAUDE.md` §4 — followed

`[test] git diff --name-status 0e68f25~1..HEAD -- datasheets/`:

```
A	datasheets/.manifest-R9.csv
M	datasheets/MANIFEST.csv
```

`[test] git log --oneline 0e68f25~1..HEAD --name-only -- 'datasheets/.manifest-*' 'datasheets/.moves.csv'`
→ `b32c557` / `datasheets/.manifest-R9.csv` only.

**No prior fragment was touched. `.moves.csv` was not touched. No banked file
was added, removed or modified.** `[test] merge-manifests.py --check` exit 0,
so `MANIFEST.csv` is a true regeneration and not a hand edit. §4 clean —
which makes D11-1's invocation of §4 as the reason for something else the more
worth correcting.

`[calc]` One small note in R9's favour that reads like an error and is not:
its `file` column is `texas-instruments/DAC8568CIPW.pdf`, a path that has not
existed since the 2026-09-21 re-filing. It resolves only because
`.moves.csv:2` rewrites it. Writing the pre-restructure path is the
**consistent** choice — it makes R9's row behave identically to R2's, which it
supersedes — and it works. Worth knowing rather than fixing.

---

## 6. Auditing the output, not the exit code

`[test] python3 tools/verify-datasheets.py` → exit 0:

```
datasheets: 78 verified, 23 recorded as blocked or not-fetched, 0 problems
```

**Manifest rows pointing at a missing file: 0.** `[calc]` Independently
verified — 76 distinct files named, 76 artefacts on disk, set difference empty
both ways.

**Corpus citations of a `datasheets/` path that do not resolve: 0.** `[calc]`
I re-ran the tool's own `PATH_RE` walk instrumented to print the denominator
the tool hides on success: **141 citations checked, 0 dangling.** Two
`datasheets/` references fall outside the regex and both resolve —
`datasheets/mechanical/` (a directory, in `ROADMAP.md`) and
`datasheets/README.md` (from `hardware/module/umbilical-load-switch/sim/README.md`).
`[calc]` Blind spots in the extension list — `.jpeg`, `.lib`, `.asy` are in
`ARTEFACT` but not in `PATH_RE` — are unexercised today. **This half of the
tool is genuinely clean.**

**BOM parts with no manifest row: 0 reported.** True today, but D11-8 and
D11-9 are why the number is weaker than it reads.

### D11-8 (Medium). The coverage claim tests 26 of 139 rows

`[calc]` Re-implementing the tool's own filter over `hardware/bom.csv`:

```
BOM rows                                        139
  skipped as TBD / "(none…)"                      9
  skipped: no part-number-shaped token           104
  actually tested                                 26
```

The token filter requires a token of **length ≥ 6** containing both a digit
and a letter and not matching `\d+[a-z]{1,3}`. `[calc]` Rows it therefore
never tests include `U-MCU-RT: ESP32-S3-Matrix` (`ESP32` is 5 characters),
`D-REVSHUNT: SS34`, `U-BUCK: R-78E5.0-1.0`, `SW1-n: KS-33 Red (linear)`,
`SW-THUMB: KS-33 lighter variant`, `PLATE-THUMB: 1.20mm aluminium`.

The tool's own comment `[repo] tools/verify-datasheets.py:~100` says:

> *"The ESP32-S3, the QMI8658C and the PESD12VS1UB were all hiding in exactly
> that blind spot — named parts, real manufacturers, invisible to every tool
> because nothing was looking for an absence."*

`[calc]` Of those three, `QMI8658C` is now caught (8 characters) and
`PESD12VS1UB` is now covered by R9's row — but **`ESP32-S3-Matrix` is still
invisible**, skipped before either the token test or the refdes fallback runs.
It happens to have coverage (`[repo]` 10 `ESP32` hits in `MANIFEST.csv`,
including the banked Waveshare schematic), so the comment's *claim* is true
and its *mechanism* is not: the tool would not notice if that coverage
vanished.

`[calc]` Two further softenings of the claim, both in the loose direction:
the haystack is `_norm(" ".join(all values of all rows))`, so a part number
mentioned anywhere — including inside a note saying the part was **checked and
rejected** — reads as coverage. Of the 26 rows tested, two pass only on free
text and not on any row's `part` column (`FB-IN: MI1206K601R`, legitimate —
banked under a descriptive name; `U-IMU: QMI8658C`), and one passes only on
the refdes rule (`SW-POWER: NKK M2011SD4G01`, which is the vendor-catalogue
case the rule was written for and is working as designed). **Zero uncovered is
factually right today and is not established by construction.**

### D11-9 (Medium). Wiring `verify-datasheets` into the checker captured its exit code and discarded its report

`[repo] tools/check-staleness.py:658-683`:

```python
r = subprocess.run([sys.executable, tool], capture_output=True, …)
if r.returncode == 0:
    return []
```

`[calc]` `verify-datasheets.py` prints its BOM-coverage block explicitly as
*"not a failure, but nothing else will ever mention them"* and then
`sys.exit(1 if (bad or dangling) else 0)` — coverage is **deliberately
advisory and does not affect the exit code**. So on any clean-but-incomplete
tree, `check_datasheets()` returns `[]` and the entire advisory half is thrown
away. `[repo] .claude/settings.json`'s `PreToolUse` hook then greps only
`^(PASS|FAIL)` out of the checker, so the message a committer actually sees is

```
staleness check: PASS no live stale values | corpus 123 files, 23 circuits,
37 figures / 218 patterns | 5 unresolved (tracked) | 233 restated-not-cited
```

`[test]` — verbatim, from this session's own hook output. It **never mentions
datasheets at all**: not that `verify-datasheets` ran, not the 78/23/0 line,
not a coverage count. `CLAUDE.md` §3's *"must pass before committing anything
under `datasheets/`"* is now enforced, which is the real gain of `b32c557` and
should be credited — but the half of the tool written specifically because
*"nothing was looking for an absence"* is, once again, wired to nothing.

*Cheapest fix:* have `check_datasheets()` pass the `BOM parts with NO manifest
row` lines through as advisory regardless of return code, and put the
`N verified / M blocked` line in the summary so the hook shows it.

### D11-10 (Medium). `check_verified_against` has no inputs

`[calc]` `grep -rn "verified_against"` across the whole tree returns hits in
**`tools/check-staleness.py` only** (lines 530, 547, 554, 559, 566, 1006).
`[calc]` The union of keys across all 23 `hardware/**/circuit.yaml` files is
exactly `['depends_on', 'id', 'last_reviewed', 'title']`. **No data file in
the repository declares `verified_against`.**

So the function that is the *only* machine link between a corpus figure and a
banked document's SHA-256 iterates an empty list 23 times and returns `[]`
forever. Its docstring promises:

> *"A cited datasheet SHA must still match the manifest. Catches a re-bank:
> someone replaces a PDF with a newer revision, the manifest's hash moves, and
> every figure read off the old revision is now resting on a document nobody
> has read."*

It cannot catch that. Nor can it enforce its own
`BLOCKED`-must-have-`blocked_on` rule, which is exactly the rule D11-3 needs.

**In fairness:** `[test] git log -S check_verified_against` shows it was added
in `108c633`, whose subject is *"The BOM generator and the dependency layer,
**before either has data**"* — so this is a knowingly-ahead-of-data check, not
a hidden fail-open. The finding is that it is **still** ahead of data after a
batch that rewrote all 23 `circuit.yaml` files (+68 to +79 lines each) to
rebuild the dependency graph, and did not add one `verified_against` entry
while doing so. `[repo]` Relatedly, `config/figures.yaml`'s 37 figures have no
`provenance` field; five carry a prose `provenance_note`. `CLAUDE.md` §3's
*"Mark provenance on every figure so the weak ones are visible"* is, today,
entirely a prose convention with no schema and no check.

---

## 7. Provenance spot-check — ten figures against the banked documents

`[repo]` Nine of `config/figures.yaml`'s 37 figures cite a path under
`datasheets/`; four more name a document by its TI/vendor document number.
I checked ten, all against the banked bytes, with `pymupdf`.

| Figure | Claim | Document, verbatim | Verdict |
|---|---|---|---|
| `sensor-full-scale` **4.86 V** | *"`Vout = VS*[(0.1533*P) + 0.053]`, verbatim from the datasheet … 5*(0.9198 + 0.053) = 4.864 V. The PEDESTAL IS 0.265 V"* | `[datasheet] analog/MPXV4006DP.pdf`: *"Transfer Function (kPa): `Vout = VS*[(0.1533*P) + 0.053] ± 5.0% VFSS`"*, `VS = 5.0 Vdc`; p.1 *"0 to 6 kPa"*; EC table `Voff 0.152 / 0.265 / 0.378 V` | **Confirmed.** `[calc]` `0.1533×6 = 0.9198`; `5×0.9728 = 4.864` |
| `breath-sensor-slope` **0.7665 V/kPa** | *"slope is VS × 0.1533 … datasheet's own sensitivity line says 766 mV/kPa"* | same doc: *"Sensitivity V/P — 766 … mV/kPa"* | **Confirmed** |
| `dac-rail` floor **5.00 V** | C grade specified only for AVDD 5.0–5.5 V | `[datasheet] SBAS430E p.3` *"AVDD ≥5V; grades C and D"*; p.4 *"Grades C/D, AVDD = 5.0V to 5.5V"* | **Value confirmed; one clause of the provenance overstates** — see §1 |
| `panel-height-budget` **110 / 115.5 mm** | panel 128.5 mm, holes at 3.0/125.5, 10HP width 50.50 at x 7.50/43.06 | `[repo] datasheets/mechanical/EURORACK-3U-PANEL-HP-TABLE-make_blanks.py`: `HEIGHT = 128.5`, `HOLE_Y = (3.0, 125.5)`, `HOLE_DIA = 3.2`, `10: {"width": 50.50, "holes": _holes(50.50, [7.50, 43.06])}` | **Confirmed, every number** |
| `panel-toggle-hole` **6.5 mm / 5.8 mm D-flat** | NKK bushing M6×0.75, 6.5 mm hole not 6.0; D4 flat 5.8; S4 flat 5.6 with a 2.2 mm hole | `[datasheet] connectors/NKK-SERIES-M-TOGGLE.pdf`: `M6 P0.75` ×7; *"Panel Cutouts … (6.5) Dia .256 … (5.6) .220 … (2.2) Dia .087"*; *"Threaded Splashproof with D Flat … (5.8) .228 (6.5) Dia .256"* | **Confirmed** — but see D11-13 |
| `loadswitch-timer` **10 uF** | 77 µA net ramp *"CONFIRMED VERBATIM … 164112fc p.8"*; 3 µA idle, 80 µA active | `[datasheet] discrete-and-power/LT1641.pdf`: *"the TIMER pin is pulled to GND by a 3µA current source. After the current limit circuit becomes active, an 80µA pull-up current source is connected to the TIMER pin and the voltage will rise with a slope equal to 77µA/CTIMER"*; `1.233 V` ×18; doc code `164112fc` ×12 | **Confirmed.** `[calc]` Also the identity trap cleared: 51 occurrences of `LT1641`, **zero** of `LT4256` — this is not the mislabelled RS mirror `repo-maintenance.md` warns about |
| `cref-out-node` | SBOS410O p.26 §8.4.1 ESR ≤ 1.5 Ω; *"Figure 8-6 annotates CL = 1uF to 50uF for REF50xxI, REF50xxAI"* | `[datasheet] analog/REF5050.pdf` p.26 (PDF index 25), verbatim: *"Confirm that a output capacitor (CL) is connected from VOUT to GND. For output stability, verify that the equivalent series resistance (ESR) value of CL less than or equal to 1.5Ω"*; Figure 8-6: *"CL = 1µF to 50µF for REF50xxI, REF50xxAI / CL = 1µF to 100µF for REF50xxEI"*; doc is `SBOS410O` | **Confirmed, including the page number and the revision letter** |
| `opa2197-output-impedance` **375 ohm** | *"SBOS737C EC table p.8 and p.10, 'ZO Open-loop output impedance \| f = 1 MHz, IO = 0 A, See Figure 26 \| 375 \| ohm'"* | `[datasheet] analog/OPA2197.pdf` **p.8 and p.10**, verbatim on both: *"ZO Open-loop output impedance f = 1 MHz, IO = 0 A, See Figure 26 375 Ω"* | **Confirmed — exact, including both page numbers** |
| `riso-ref-topology` | OPA2197 capacitive-load limit 1 nF, *"SBOS737C p.1 and section 7.3.5 p.22"* | same doc p.1 *"High Capacitive Load Drive Capability: 1 nF"*; p.22 *"in a unity-gain configuration, directly drives up to 1 nF of pure capacitive load"* | **Confirmed** |
| `diode-split-rationale` **120 mV** | *"0.24 V at 245 mA → 0.36 V at 612 mA, digitised off Fig. 2 of Diodes Inc DS23001 Rev.8"* | `[datasheet] discrete-and-power/1N5817.pdf`: `DS23001 Rev. 8`, *"Fig. 2 Typical Forward Characteristics"* with axes 0–2.5 V / 0.1–30 A; EC table `VFM @ IF = 1.0A: 0.450 max` | **Confirmed as far as text can go.** The values are a curve digitisation and are marked as such; its `provenance_note` states the calibration (0.454 V at 1.0 A against a 0.450 V guaranteed max) which `[calc]` is consistent with the EC table |
| `ferrite-bias-impedance` | Laird `MI1206K601R-10` *"drawing rev E"*, bias curve family 0 / 250 / 500 / 1000 / 1500 mA at 100 MHz | `[datasheet] discrete-and-power/MI1206K601R-10-ferrite-bead.pdf`: the whole text layer is 170 characters — `MI1206K601R-10`, `Z R XL`, axis decades, and exactly `0amp 250ma 500ma 1000ma 1500ma`, `Laird` | **Part and curve family confirmed.** `[calc]` *"rev E"* is not in the text layer; it is presumably in the title block, unverifiable without a render. Low importance |

**Eleven figures checked, ten fully confirmed** (I checked one more than the
ten asked for). `dac-rail`'s value is right with one overstated clause. The
quality here is high — `opa2197-output-impedance`, `cref-out-node` and
`loadswitch-timer` are quoted exactly, page numbers included, and
`loadswitch-timer` has the part-number identity check
`repo-maintenance.md` §3 demands.

### D11-13 (Low). `panel-toggle-hole` says the NKK drawing has no text layer

`[repo] config/figures.yaml`: *"read off
`datasheets/connectors/NKK-SERIES-M-TOGGLE.pdf`, **rendered at 150 dpi because
the drawing is vector with no text layer**"*. `[test]` It has 49,220
extractable characters, and every value the figure needs is in them —
`M6 P0.75`, `(6.5) Dia`, `(5.8) .228`, `(5.6) .220`, `(2.2) Dia`. `[repo]
docs/reference/repo-maintenance.md:127` already carries the correction, in
bold: *"**This page listed both as textless and was wrong**: `8.89`, `8.9` and
`6.5` are all in their text layers"*. The register was not updated when
`repo-maintenance.md` was. The number is right and was presumably read off the
render correctly; only the note about how it had to be read is stale. Same
shape as D11-11: the derived statement did not follow.

`[calc]` The document's identity, incidentally, does check out despite `NKK`
appearing **zero** times: p.1 carries `Series M / Miniature Toggles` and
`www.nkkswitches.com`, and `Series M` occurs 28 times. A literal part-number
grep would have flagged this document as suspect — worth knowing before
someone adds that grep as a check.

---

## The sibling claim — confirmed, and the wrong side identified

**Claim received:** *the Gateron drawing's extractable character count is
stated as ~9,680 in one place and ~11 kB in another, and one of those is
wrong.*

`[test]` Measured on `datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`
(6 pages), `pymupdf 1.28.2`:

```
get_text(), pages joined ""      11,053 characters
                as UTF-8 bytes   11,194 bytes
excluding all whitespace          9,375 characters
whitespace collapsed to single   11,042 characters
printable ASCII only             10,653 characters
pages joined "\n"                11,058 characters
```

`[repo]` The two statements:

- `docs/reference/repo-maintenance.md:128` — *"11 kB of extractable spec
  text"* — and `docs/reference/ks33-geometry.md:217` — *"It yields 11 kB of
  it"*. **Right**: 11,194 bytes / 11,053 characters.
- `config/figures.yaml:678` (`plate-thickness` derivation) — *"the document as
  a whole yields **9,680 characters** of prose"*. **Wrong.** `[calc]` I could
  not reproduce 9,680 under any extraction variant I tried; the nearest is
  9,375 (whitespace stripped), which is not it either.

So the sibling's claim is correct and the `9,680` is the bad number. It is
also the *load-bearing* one in the wrong direction: its sentence exists to
stop a future reader re-concluding the file is unreadable
(*"Do not re-conclude the file is unreadable"*), and it under-states the
extractable text by 12%. `[calc]` Both statements describe one measured
quantity of one banked document, restated in two units in three files — the
restate-don't-cite shape on a quantity that is not in the register. Either
one owner states it and the other two cite, or all three say *"about 11 kB"*.

The surrounding claims all hold `[test]`: *"Bounce Time: 5msec
Max.(at 16 in/sec. actuation speed)"* **is** in the extractable text layer,
confirming `ks33-contact-bounce`; and `repo-maintenance.md:120`'s *"Measured
across all 60 banked PDFs, 2026-09-21"* is **exactly right** — `find datasheets
-name '*.pdf'` returns 60.

---

## What I could not settle

- **The `PESD12VS1UB` package.** `[from memory]` suspicion that `…UB` is
  leadless SOD882 rather than the BOM's `SOD-323`. Settled only by the blocked
  datasheet or the Nexperia product page. If it is leadless, ADR 0013's
  package policy strikes a third TVS candidate.
- **The 1.5 µA leakage figure's origin.** Not traceable to any banked document
  or any other corpus statement. Settled by the blocked datasheet — and it is
  the one of the row's three numbers that the blocked datasheet *can* settle.
- **`ferrite-bias-impedance`'s "rev E"** and the digitised `1N5817` curve
  points, both of which need a render rather than a text extraction. Neither
  is load-bearing enough to be worth a reviewer's render; both are honestly
  marked as read off a curve.
- **Whether the DAC file should be renamed.** A judgement call for the
  maintainer. D11-1 establishes only that the reason currently recorded for
  not doing it is false and that the mechanism to do it exists and is already
  in use on this file.
