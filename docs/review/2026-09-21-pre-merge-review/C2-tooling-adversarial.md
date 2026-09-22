# C2 — tooling, adversarial

Agent C2, cold. Slice: break the six tools and the commit hook.

**Method.** Every claim below that a check can be fooled was reproduced in a
throwaway tree: `git archive HEAD | tar -x -C <scratch>/base`, then
`cp -a base <scratch>/eN` per experiment. The repository was never modified.
Commands are in §9. `[test]` means I ran it and the transcript is the quoted
output; `[repo] path:line` means I read it; `[calc]` shows the arithmetic.

**Cold-rule compliance.** I read nothing under `docs/review/`. I know from the
brief that another agent has audited these tools; I do not know what it found.
Where a defect I report is already described *in a tool's own comments* as
found-and-fixed, I say so explicitly, because that is evidence about the fix,
not about the finding.

**Baseline.** `[test]` On `HEAD` (61060ed) all six tools are green:

```
check-staleness.py   PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)   rc=0
merge-bom.py --check       bom.csv: checked 138 rows from 24 fragments | 0 problems                      rc=0
merge-manifests.py --check MANIFEST.csv: 98 rows from 8 fragments | 77 ok, 20 blocked, 1 other            rc=0
verify-datasheets.py       datasheets: 77 verified, 21 recorded as blocked or not-fetched, 0 problems     rc=0
```

Wall time of the hook's command: **9.0 s** `[test]`.

---

## 1. The sixth

> a scanner that walked a moved directory · a check defined and never called ·
> an owner check matching on a token too weak to be evidence · a guard that
> harvested stdout while its tool crashed to stderr · a conservation checker
> that printed findings and exited 0

**`check-conservation.py` loses content off the FRONT of the source and exits 0.**

The file already knows this shape. `[repo] tools/check-conservation.py:63-68`:

> `# A TAIL LOSS HIDES BELOW N. In the interior a 1-word deletion breaks N`
> `# shingles and is reported; at the very end only k shingles exist to break,`
> `# so deleting the last 1/3/5/7 words scores seams:1 REAL GAPS:0. Verified.`

That is correct, and it was fixed — with a `tail_lost` comparison of the last
`N` words. **The head was never considered.** The shingle walk starts at `i=0`,
so a loss of the first *k* words breaks exactly *k* shingles (those starting at
`0 … k-1`), and `seams = [l for l in lost if l[1] < N]`
`[repo] tools/check-conservation.py:56` classifies any `k < 8` as a seam.

`[calc]` Interior loss of *k* words breaks `k + N - 1 ≥ N` shingles → REAL GAP.
Head loss of *k* words breaks `k` shingles → seam whenever `k ≤ 7`.

`[test]` Scratch repo, source is an 85-word page, destination is the same page
with the first *k* words of the stream removed:

```
drop first 1 words -> seams: 1   REAL GAPS: 0     exit 0
drop first 4 words -> seams: 1   REAL GAPS: 0     exit 0
drop first 7 words -> seams: 1   REAL GAPS: 0     exit 0
drop first 8 words -> seams: 0   REAL GAPS: 1   gap 8 words @ 0: "Breath response shaper The transfer curve is piecewise…"
```

`[test]` The realistic form. Destination drops the page title and the first
three words of the lead sentence — `"# Breath response shaper\n\nThe transfer
curve is"` → `"The"` — six words including the page's own name:

```
source src/page.md@HEAD: 85 words
destinations: 79 words across 1 file(s)
seams (new text inserted between preserved passages): 1
REAL GAPS (source text with no home): 0
rc=0
```

Compare the same six words removed from the *end*: `TAIL: the source's last 8
words are not in any destination`, `rc=1` `[test]`.

Why this is the one worth naming: a Phase B split moves a section into a new
file and the characteristic edit at the seam is *at the top* — the old heading
is replaced by the new page's heading, the lead sentence is reworded to stand
alone. That is exactly where the check is blind, and `--check`-style callers
(`&&` chains, the hook pattern) read exit 0.

### Two more of the same family in `check-conservation.py`

`[test]` **A passage the source states twice can be halved for free.** `have` is
a `set()` of destination shingles `[repo] tools/check-conservation.py:38-41`, so
a second occurrence contributes nothing and its loss is undetectable. Source: a
26-word grounding warning repeated under two headings. Destination: the second
copy deleted outright.

```
source src/page.md@HEAD: 75 words
destinations: 49 words across 1 file(s)
seams: 2    REAL GAPS: 0    rc=0
```

A quarter of the page gone, exit 0. Deduplicating shared boilerplate while
splitting a page is a normal restructure move, and it is free here.

`[test]` **Reordering is invisible.** Moving the SPI paragraph under the
breath-link heading and vice versa: `75 words → 75 words, REAL GAPS: 0, rc=0`.
A set of shingles cannot see position, so "the caveat is now under the wrong
circuit" passes. This one is arguably inherent to the design; the duplicate-
passage hole is not, and the head hole is not.

### Runner-up nominations

If the intended sixth is elsewhere, these two are the strongest alternatives and
both sit **inside the guards written to close earlier instances**:

- §2.1 — `check_bom_generated()` returns on the manifests result before it ever
  looks at `merge-bom.py --check`, so a `.moves.csv` typo makes a hand-edited
  `hardware/bom.csv` vanish from the report entirely.
- §2.2 — `check_checks()` asserts a *string* is present in `main()`'s source,
  not that a check runs or that its result is consulted. Both defeats are
  one-line edits and produce `PASS`.

---

## 2. Findings — `tools/check-staleness.py`

### 2.1 `check_bom_generated()`: a manifests-side refusal masks a hand-edited `bom.csv`, and is misdiagnosed as a crash

`[repo] tools/check-staleness.py:209-213` runs `merge-manifests.py --check`
first and, on a non-zero exit, **returns immediately** — `merge-bom.py --check`
has already been run but its result is never examined.

`[test]` Step 1, hand-edit the generated master (`DAC8568` → `DAC8568X` in
`hardware/bom.csv`), the exact trap CLAUDE.md names on "the most-cited file in
this repository":

```
GENERATED FILE EDITED BY HAND (1)
  hardware/bom.csv does not match its fragments, first difference at line 56.
  It is GENERATED - edit the fragment, not the master, then re-run this tool
exit 1
```

Step 2, *additionally* append one bad row to `datasheets/.moves.csv` (a move
that chains, which `merge-manifests.py` refuses at line 81):

```
GENERATED FILE EDITED BY HAND (1)
  merge-manifests.py --check exited 1 and said nothing parseable - it probably crashed
```

`[test]` `grep -c "does not match its fragments"` over the full `--detail`
output: **0**. The hand edit is now mentioned nowhere, and the one message that
survives is wrong.

Two separate defects compounding:

1. **The filter throws away every guard message `merge-manifests.py` has.**
   `[repo] tools/check-staleness.py:210-211` keeps only lines containing
   `"PROBLEM:"` or `"does not match"`. Every `sys.exit("REFUSING TO WRITE: …")`
   in `merge-manifests.py` — the no-fragments guard (line 22), the `.moves.csv`
   header, column-count, empty-path, duplicate-target and chain guards (lines
   61-82), and the pre-write refusal (line 169) — contains neither token. All
   are discarded, and the fallback text tells the reader the tool "probably
   crashed" and to run it directly. It did not crash; it printed a precise,
   actionable sentence, which this function deleted.
   This is the same failure as the one documented at
   `[repo] tools/check-staleness.py:216-231` ("HARVEST STDERR TOO, AND NEVER
   RETURN AN EMPTY LIST ON A NON-ZERO EXIT") — the fix was applied to the
   `merge-bom` branch and not to the `merge-manifests` branch six lines above it.
2. **The early return.** A fault in the datasheet manifest suppresses the BOM
   report. The two are independent; both should be reported.

**Severity: high.** The mask is cheap to trigger (one bad row in a dotfile) and
it hides the single trap this project says it most wants not to repeat.

### 2.2 `check_checks()` proves a name appears in a comment, not that a check runs

`[repo] tools/check-staleness.py:587-593` — `inspect.getsource(main)` and
`(n + "(") not in src`.

`[test]` Defeat A — disable the call, leave the name in the comment (which is
what someone temporarily disabling a check actually writes):

```python
    link_problems = []   # check_links(files)  <- disabled while we split pages
```

With a genuinely broken inline link planted in `hardware/carrier/carrier.md`:
`PASS no live stale values | corpus 121 files, 23 circuits`, `UNWIRED CHECKS`
count **0**.

`[test]` Defeat B — call it, ignore the result. `if link_problems:` →
`if False and link_problems:`. Same broken link: `PASS`, `UNWIRED CHECKS` **0**.

The docstring's claim is "the tool asserts its own wiring, and the assertion is
four lines". What it asserts is that the substring `check_links(` occurs
somewhere in `main`'s source text. Defeat B is the more likely accident: a check
whose result is computed and then not folded into `fail` is indistinguishable
from a passing check, and that is the original defect restated.

### 2.3 `REFUTATION`: one common English word silences a live stale value

`[repo] tools/check-staleness.py:63-68`. The alternation includes bare `was`,
`were`, `old`, `prior`, `earlier`, `wrong`. A hit whose line matches is moved to
`refuted` and never counted in `live`; the `refuted` bucket is `detail_only` and
its members are printed only under `--verbose`
`[repo] tools/check-staleness.py:716-721`.

`[test]` Appended to `hardware/carrier/breath-adc/breath-adc.md`, using a
spelling that *is* in `sensor-full-scale`'s forbidden list:

```
The ADC input span matches the sensor: 0.2 – 4.7 V across the
full breath range, so the top code lands at the sensor ceiling.
→ FAIL … + 1 stale …
```

Insert one word — `span was set to match` — and nothing else changes:

```
→ PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
```

`[test]` It also works from the *adjacent* line when the forbidden phrase wraps,
because `ctx` spans every line the match touches
`[repo] tools/check-staleness.py:179`.

`[test]` How much this currently suppresses. Re-implementing the classifier over
the live corpus and recording which alternative fired, across the 59 hits the
tool reports as "refuted in place":

| word | hits |
|---|---|
| `was` | **23** |
| `used to` | 10 |
| `until 2026` | 4 |
| `previously` | 4 |
| `old` | 4 |
| `superseded` | 3 |
| `rather than` | 3 |
| `refuted` | 2 |
| `this row said` | 2 |
| `deleted` | 2 |
| `carried a superseded` | 1 |
| `wrong` | 1 |

Thirty-nine per cent of the suppression is carried by the single weakest word in
the list. Two examples where `was` is doing the work and the line is not a
refutation in any obvious sense:

- `hardware/bom.csv:68` — `[breath-zero-ref]` `'~0.437 V'`
- `hardware/module/breath-receive-stage/bom.csv:3` — `[breath-zero-ref]` `'~0.437 V'`

I have not adjudicated all 59 by reading; the point is structural. **59 findings
are being dismissed by a regex whose commonest trigger is the past tense of
"to be", and the dismissals are invisible without `--verbose`.**

Suggested shape of a fix, for whoever takes it: drop bare `was`/`were`/`old`
from the alternation, or require the refutation token to be within N characters
of the match rather than anywhere on the line, and print the `refuted` *count*
on the always-printed line so the bucket is not silent.

### 2.4 `check_owners()`: the "distinctive token" is a bare digit substring

`[repo] tools/check-staleness.py:521-534`. The chosen token is the single
longest `\d+\.?\d*` run of length ≥ 3, matched with `t in text` — an unanchored
substring test against the whole owner file.

`[test]` `sensor-full-scale` is `4.86 V`, owner
`docs/decisions/0003-breath-sensing-path.md`. Replace every occurrence of
`4.86` in that file with `<<REDACTED>>` (the derivation has genuinely gone), then
append one unrelated sentence:

> `The harness cable measured 14.863 mm across the strain relief.`

```
→ PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
```

Without the coincidental sentence: `FAIL … + 1 owners …` `[test]`.

The docstring at `[repo] tools/check-staleness.py:504-520` says the check "makes
exactly one claim — 'the owner states something only this figure would say'". A
four-character digit run inside a longer number does not support that claim.
The `any()`-over-all-tokens weakness was found and fixed; the substring
weakness underneath it was not.

`[test]` Live exposure — **18 of the 30 settled figures** rest on a token of four
characters or fewer:

```
[inamp-full-scale       ] '-9.94 V'                          token '9.94'
[sensor-full-scale      ] '4.86 V'                           token '4.86'
[key-scan-current       ] '1.43 mA per closed key, …'        token '1.43'
[key-press-time         ] '5.92 us'                          token '5.92'
[spi-series-r           ] '100 ohm, R-SPI-SER, qty 3'        token '100'
[dac-rail               ] '5.21 V'                           token '5.21'
[pitch-compensation     ] '2.2 nF, op-amp OUTPUT to (-)'     token '2.2'
[panel-toggle-hole      ] '6.5 mm diameter with a 5.8 mm D-flat'  token '6.5'
[loadswitch-gate-cap    ] '82 nF, ramp 49-197 ms (98 ms typ)' token '197'
[loadswitch-fb-divider  ] '35.7 kohm / 5.11 kohm, both 1%'   token '35.7'
[cref-out-node          ] 'REF5050 VOUT, i.e. the buffer's INPUT…' token '5050'
[riso-ref-topology      ] 'Dual feedback per SBOS737C Figure 56…' token '37.4'
[loop-budget            ] '196-241 us of 250 us'             token '196'
[umbilical-current      ] '359 mA'                           token '359'
[diode-split-rationale  ] 'fault isolation … (r_d 69 mohm at 392 mA)' token '392'
[plate-thickness        ] '1.20 mm'                          token '1.20'
[opa2197-output-impedance] '375 ohm'                         token '375'
[ferrite-bias-impedance ] '~580-614 ohm on FB1/FB3/FB4; …'   token '580'
```

Note `spi-series-r` → `100`: the very figure the docstring names as its
counter-example is still verified against a three-digit substring. The fix
narrowed the token set from "any" to "the longest"; it did not make the longest
one distinctive. `2.2` (pitch-compensation) and `6.5` (panel-toggle-hole) will
match essentially any engineering page.

### 2.5 `check_circuits()`: an unknown `depends_on` prefix is silently accepted

`[repo] tools/check-staleness.py:363-384`. After the `":" not in dep` guard the
code is `if kind == "fig" … elif "circuit" … elif "refdes" … elif "adr" … elif
"node"`. **There is no `else`.** Any other prefix falls through unchecked, and
the error message one line above enumerates the five legal prefixes, so the tool
knows the set and declines to enforce it.

`[test]` Control — `depends_on: refdes:R-REALLY-NOT-THERE` appended to
`hardware/module/mod-channels/circuit.yaml` → `FAIL … + 1 deps …`.

`[test]` Six typo'd spellings of the same dead edge, together:

```yaml
depends_on:
  - refdes :R-REALLY-NOT-THERE     # one space before the colon
  - refdess:R-REALLY-NOT-THERE
  - part:R-REALLY-NOT-THERE
  - Refdes:R-REALLY-NOT-THERE      # capitalised
  - nodes:no-such-node
  - figs:no-such-figure
```

```
→ PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
```

This is the same class as "a check defined and never called": the edge *looks*
declared, the tool *looks* like it checked it, and the question was never asked.

`[test]` Live corpus is clean today: 294 declared edges, kinds
`{adr: 31, fig: 87, refdes: 126, circuit: 50}`, zero outside the five. So this
is latent, not live — but a restructure that renames a prefix, or a hand-written
`circuit.yaml`, gets no warning. Also worth knowing: **no circuit declares a
`node:` edge at all**, so the `provides`/`node:` half of the design is
untested by any live data.

`[test]` Coverage of the half that does run: 126 `refdes:` edges name
**79 of the 138** BOM rows. The other 59 rows have no declared dependent, so
deleting them produces no `deps` finding.

### 2.6 `load_circuits()`: a duplicate `id` evicts a whole circuit from every check

`[repo] tools/check-staleness.py:329` — `out[data.get("id", rel)] = data`.
Two `circuit.yaml` files declaring the same `id` collapse to one dict entry; the
loser is gone from `check_circuits()` and `check_verified_against()` entirely.

`[test]` Plant a dead edge in the real circuit:
`hardware/module/pitch-stage/circuit.yaml` gains
`depends_on: [refdes:R-THIS-PART-WAS-DELETED]`.

```
CIRCUIT DEPENDENCIES (1)
  hardware/module/pitch-stage/circuit.yaml: depends_on refdes:R-THIS-PART-WAS-DELETED
    - no BOM row. Deleted with the part it belonged to?
```

Now add a later-walking directory that reuses the id — the ordinary accident of
copying a circuit directory to start a new one:

```yaml
# hardware/carrier/breath-adc/trim/circuit.yaml
id: module/pitch-stage
provides: []
```

```
CIRCUIT DEPENDENCIES (1)
  hardware/carrier/breath-adc/trim/circuit.yaml: id is 'module/pitch-stage',
    directory says 'carrier/breath-adc/trim'
```

`[test]` The dead-refdes finding is gone. The count stayed at 1, so the summary
line looks the same size; what changed is that a substantive finding was
replaced by a cosmetic-looking one, and `hardware/module/pitch-stage`'s entire
check surface — `depends_on`, `verified_against`, id/directory — went dark.

Mitigating: a collision always produces *some* finding (one of the two ids must
disagree with its directory), and fixing that finding properly restores the
evicted circuit. Aggravating: the circuit count is printed only on the **PASS**
line `[repo] tools/check-staleness.py:741-743`, so on a FAIL run there is no
"23 circuits" to notice has become 23-with-one-missing.

**Fix is one line**: detect the key collision in `load_circuits()` and report it.

### 2.7 `check_verified_against()`: a SHA from the wrong part's row passes

`[repo] tools/check-staleness.py:404-423`. `have` maps `sha256 → part`, and the
part is stored but never compared: the test is `if sha and sha not in have`.

`[test]` Append to `hardware/module/pitch-stage/circuit.yaml`:

```yaml
verified_against:
  - part: OPA2197 (pitch buffer)
    sha256: <the sha256 of analog/DAC8568CIPW.pdf>
```

```
→ PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
```

The circuit now claims its pitch buffer was verified against the DAC8568's
datasheet and the tool agrees. The docstring's stated purpose — catching a
re-bank — is served. The stronger claim a reader takes from a green run ("this
figure was read off *that* document") is not. `have[sha]` is already the part
string; comparing it to `v.get("part")` as an advisory mismatch would cost a
line.

### 2.8 `check_sections()` resolves a section against *any* file with the same basename

`[repo] tools/check-staleness.py:443-450` — `declares` is keyed by
`os.path.basename(path)`, unioned across every corpus `.md`.

`[test]` Live basename collisions in the corpus: **`notes.md` × 15**,
**`README.md` × 10**.

`[test]` Append to `hardware/carrier/carrier.md`:

> `The damping argument is in ` \`notes.md\` ` §5.`

No `notes.md` declares a §5 → `FAIL … + 1 sections …`. Now add an unrelated
`## Something else §5` heading to `hardware/interfaces/spi-link/notes.md` — a
different file, in a different subsystem, that the reference was never about:

```
→ PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
```

Today all 57 live section references target `carrier.md`, `cluster-boards.md` or
`led-strip-drive.md`, each unique, so this is latent. It stops being latent the
moment anyone writes `notes.md §N` or `README.md §N`, and both are natural
things to write.

Also note `ref = re.compile(r"`?([a-z0-9][a-z0-9-]*\.md)…")` is lowercase-only,
so a reference to `README.md §3` or `CLAUDE.md §4` is never matched at all.

### 2.9 `check_links()` checks inline `.md` links and nothing else

`[repo] tools/check-staleness.py:554` — `r"\]\(([^)#\s]+\.md)[^)]*\)"`.

`[test]` Four broken references appended to `hardware/carrier/carrier.md`:

```markdown
See the parts list in [the carrier BOM](gone/bom.csv) and the register in
[figures](../../config/figures-OLD.yaml), the drawing in
[panel drawing](../../mechanical/drawings/panel-NOPE.dxf), and the
reference-style page [the shaper page][shp].

[shp]: ../module/breath-response-shaper/no-such-page.md
```

```
→ PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
```

Control, a single broken *inline* `.md` link: `FAIL … + 1 links …` `[test]`.

So: links to `bom.csv`, to `config/figures.yaml`, to a mechanical drawing, and
every reference-style link in the corpus are unchecked. `bom.csv` is described in
CLAUDE.md as the most-cited file in the repository (37 backtick references); a
link to it is precisely the kind that a directory split breaks. Partial cover
exists for one case only: `verify-datasheets.py`'s `PATH_RE`
`[repo] tools/verify-datasheets.py:171-173` catches dangling `datasheets/…`
paths — but that tool is not in the commit path (§4.1).

### 2.10 A `status:` other than `settled`/`disputed`/`blocked` is a silent exemption

`[repo] tools/check-staleness.py:497` skips the owner check unless
`status == "settled"`; `[repo] tools/check-staleness.py:707` counts as
"unresolved (tracked)" only `disputed` and `blocked`. Nothing validates the
enum, so a fourth value falls between the two.

`[test]` Redact the owner's statement of `sensor-full-scale` →
`FAIL … + 1 owners …`. Change that figure's `status: settled` to
`status: draft`, change nothing else:

```
→ PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
```

The `5 unresolved (tracked)` count is unchanged, so the figure has left the
owner check without joining the list of things known to be open. Live statuses
today are `settled: 30, disputed: 4, blocked: 1` `[test]` — clean, but the
register has no schema check.

### 2.11 The forbidden register: five of seven spellings still walk past, and its own size is unreported

This is the class CLAUDE.md §2 describes, so it is not news — but the concrete
table is worth banking, and one consequence is not documented.

`[test]` The same stale statement about `sensor-full-scale`, appended to
`hardware/carrier/breath-adc/breath-adc.md` in seven renderings:

| rendering | result |
|---|---|
| `0.2 - 4.7 V` (ASCII hyphen **with** spaces) | **PASS** |
| `0.2 – 4.7 V` (en dash with spaces — listed) | FAIL ✓ |
| `0.2  –  4.7 V` (en dash, double spaces) | **PASS** |
| `0.2 – 4.7 V` (NBSP after the dash) | **PASS** |
| `0.2 – 4.7 V` (narrow NBSP before `V`) | **PASS** |
| `0.2 – 4.70 V` (trailing zero) | **PASS** |
| `0.2–4.7 V` (en dash, no spaces) | **PASS** |

The listed forbidden patterns include `'0.2-4.7 V'` (no spaces) and
`'0.2 – 4.7 V'` (en dash, spaces); the hyphen-with-spaces form in between is not
listed and is the most natural thing to type. The line-joining fix
`[repo] tools/check-staleness.py:149-167` joins with **one** space and leaves
internal spacing alone, so any double space inside a pattern defeats it.

**The consequence that is not documented:** the register's coverage is invisible
in the output.

`[test]` Plant three live stale values, then set every `forbidden:` list in
`config/figures.yaml` to `[]`:

```
with the register intact:           FAIL … + 4 stale …
with every forbidden list emptied:  PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
base, for comparison:               PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved (tracked)
```

The PASS line is **byte-identical** to a healthy run. The design deliberately
puts the corpus file count on the always-printed line because "PASS alone was
true while half the corpus was unscanned"
`[repo] tools/check-staleness.py:729-731` — the same argument applies to the
register, and the register is the input the primary check's power depends on
entirely. The procedure in CLAUDE.md §2 is *add patterns when a figure moves*, so
"the register did not grow" is the realistic failure and nothing reports it.

`[test]` Live: **4 of 35 figures carry an empty `forbidden` list** —
`breath-working-point`, `pitch-cents-budget`, `dig-gnd-topology`,
`matrix-led-current`. For those four the staleness check is a no-op and says so
nowhere. Contrast `check_owners`, which does the right thing: it reports 7
figures as UNVERIFIABLE rather than passing them
`[repo] tools/check-staleness.py:649-652`. The stale check should do the same
with its empty lists, and the always-printed line should carry a pattern count.

### 2.12 A symlinked directory inside `hardware/` is invisible, and the file count does not move

`os.walk` defaults to `followlinks=False`, in `corpus_files()`
`[repo] tools/check-staleness.py:78` and `load_circuits()`
`[repo] tools/check-staleness.py:318`.

`[test]` A circuit page and `circuit.yaml` (carrying a dead `refdes:` edge and a
live stale value) placed outside `hardware/` and symlinked in as
`hardware/module/new-circuit`:

```
reachable only through the symlink:  PASS no live stale values | corpus 121 files, 23 circuits | 5 unresolved
identical content, real directory:   FAIL … + 1 deps … | corpus 123 files
```

This is the shape of the first recorded instance — a scanner walking past
content it believes it covered. The `MIN_CORPUS_FILES` tripwire cannot help:
the count does not *drop*, it simply never rises, and 121 is what it was.
`verify-datasheets.py` walks `datasheets/` the same way
`[repo] tools/verify-datasheets.py:71`, so a symlinked subdirectory of banked
documents is orphan-invisible too.

### 2.13 `check_refdes()` — the one advisory check — crashes the whole tool, and takes `check_readable`'s diagnosis with it

`[repo] tools/check-staleness.py:286` — `text = open(path, encoding="utf-8").read()`
with no `try/except`. Every other reader in the file has one.

`[test]` One Latin-1 `\xb5` byte appended to `hardware/carrier/carrier.md`:

```
Traceback (most recent call last):
  File ".../tools/check-staleness.py", line 618, in main
    drawn_not_bommed = check_refdes(files, bom_refs)
  File ".../tools/check-staleness.py", line 286, in check_refdes
    text = open(path, encoding="utf-8").read()
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb5 in position 25293
```

Hook rendering `[test]`: `staleness: CHECKER CRASHED (exit 1) - it printed no
PASS or FAIL line.`

It **fails closed**, which is right. But `check_readable()` exists specifically
for this input and its message — "it is being SKIPPED by every check while still
counted in the corpus" `[repo] tools/check-staleness.py:102-104` — was computed
at line 602 and never printed, because a check documented as "ADVISORY, never
fatal" `[repo] tools/check-staleness.py:276` killed the process before the
report was emitted. The reader gets a traceback instead of the sentence written
for them. Move `check_refdes`'s `open()` behind the same `try/except` the rest of
the file uses, or emit `shape_problems` before running the optional checks.

---

## 3. Findings — the `PreToolUse` hook

`[repo] .claude/settings.json:9`.

### 3.1 On the shape-failure path the hook points the reader at a **stale, green** detail file and tells them not to re-run

`main()` writes `.staleness/report.txt` at `[repo] tools/check-staleness.py:723-727`
— *after* every `emit()`. The early return for a missing `TOOL_INPUT`
`[repo] tools/check-staleness.py:608-614` returns **before** that write. So the
detail file keeps whatever the last successful run left in it.

The hook's `additionalContext` says:

> `Detail is in .staleness/report.txt (NOT .staleness-report.txt, which holds
> only this summary) - read it when fixing, do not re-run for detail.`

`[test]` Seed a green run, then `mv hardware/bom.csv hardware/boms/bom.csv`
(a restructure touching a `TOOL_INPUT`) and execute the hook command verbatim:

```
HOOK SUMMARY -> staleness: FAIL 1 shape | corpus 121 files | checks did not run;

.staleness/report.txt (the file the hook says to read):
  corpus: 121 files | bom.csv: 138 rows x 11 cols | figures tracked: 35
  figure owners this check CANNOT verify (7) - not failures, but not confirmations either
  …

.staleness-report.txt (the file the hook says NOT to read):
  this tool reads 'hardware/bom.csv', which does not exist. Update TOOL_INPUTS and every path that names it
  FAIL 1 shape | corpus 121 files | checks did not run
```

The recommended file describes a corpus that no longer exists, right down to
"bom.csv: 138 rows x 11 cols" for a `bom.csv` that is not there — and the one
file holding the actual diagnosis is the one the reader is told to ignore. The
instruction "do not re-run for detail" closes the last exit.

The same stale-file problem applies to any traceback (§2.13), though there the
hook's crash branch does name `.staleness-report.txt` correctly.

Minimal fix: write `REPORT` on the early-return path too, or have the hook
`printf "%s" "$o"` into `.staleness/report.txt` when the checker produced no
fresh one.

### 3.2 What a PASS line does and does not anchor

The design intent is explicit: the always-printed line carries the corpus file
count because "PASS alone was true while half the corpus was unscanned". Good.
But the line carries **no** figure count, **no** forbidden-pattern count, **no**
BOM row count, and the circuit count appears on `PASS` only — so §2.11 (empty
register), §2.12 (symlinked directory) and §2.6 (evicted circuit on a FAIL run)
all leave the anchor numbers untouched.

### 3.3 Two smaller notes

- The hook is informational. Its JSON carries `systemMessage` and
  `hookSpecificOutput.additionalContext` and no `permissionDecision`
  `[repo] .claude/settings.json:9`, so **a FAIL does not stop the commit**. That
  matches CLAUDE.md ("surfaces the result … visible rather than silent") and is
  recorded here only so the next reader does not assume a gate exists.
- `timeout: 60` on the hook vs. the checker's own two nested
  `subprocess.run(…, timeout=60)` calls `[repo] tools/check-staleness.py:202,206`.
  Measured runtime is 9.0 s `[test]`, so there is 6.6× headroom today; but if
  either merge tool hangs, the checker's worst case is ~120 s and the hook
  expires first, producing hook-level failure rather than the crash message.

---

## 4. Findings — scope, and where two tools disagree

### 4.1 `verify-datasheets.py` is in no automated path

CLAUDE.md §3: "`python3 tools/verify-datasheets.py` must pass before committing
anything under it." Nothing runs it. `check_bom_generated()` runs `merge-bom.py`
and `merge-manifests.py` only `[repo] tools/check-staleness.py:200-206`.

`[test]` Ten bytes overwritten inside a banked PDF, header and size preserved:

```
check-staleness.py    PASS no live stale values | corpus 121 files, 23 circuits    rc=0
verify-datasheets.py  DAC8568CIPW: sha256 mismatch on analog/DAC8568CIPW.pdf
                      (manifest a9b54fefecaa, file f0d18499232e)                   rc=1
```

`[test]` The banked file deleted outright: `check-staleness.py` → `PASS`;
`verify-datasheets.py` → 1 × "manifest names … which does not exist", `rc=1`.

Note `check_verified_against()` in check-staleness compares a cited SHA against
the **manifest**, never against the **bytes on disk**, so the manifest and the
corpus can agree perfectly about a document that is not the document. The
banked-document rule is the one CLAUDE.md §3 calls stronger than a review
finding; it is the only rule here with no mechanical enforcement.

### 4.2 The three tools disagree about what "the corpus" is

| | `check-staleness.py` | `verify-datasheets.py` | `rewrite-paths.py` |
|---|---|---|---|
| definition | `CORPUS_DIRS`+`CORPUS_FILES` `[repo]:30-31` | `CORPUS` `[repo]:169-170` | `git ls-files` minus `HISTORY`/`HAND_EDITED` `[repo]:46-73` |
| `CLAUDE.md` | no | **yes** | excluded (hand-edited) |
| `README.md` | yes | yes | **excluded** (hand-edited) |
| `mechanical/` | no | no | yes |
| extensions | `.md .csv .yaml .yml` | `.md .csv .yaml .yml` | `.md .csv .yaml .yml .py .json .txt` |

Consequences:

- `CLAUDE.md` is scanned for dangling datasheet paths but is not part of the
  staleness corpus — so a tracked figure restated in CLAUDE.md can go stale
  unseen. (CLAUDE.md §6 defines the corpus without CLAUDE.md, so this is
  intentional; it is worth knowing that the rules file exempts itself from the
  rule.)
- `rewrite-paths.py --verify` never examines `README.md` or `CLAUDE.md`
  `[repo] tools/rewrite-paths.py:52-59`, both of which carry paths. `[test]` I
  checked all 12 `HAND_EDITED` entries against the 8 live map pairs: the only
  old-side survivors are in `tools/rewrite-paths.py`'s own comments and in
  `docs/reference/path-map-2026-09-21.csv`'s old-side column — both correct by
  design. **No live defect**; the exemption is a scope note only.
- `mechanical/` is in no staleness or datasheet corpus. `[test]` It contains
  three `.gitkeep` files and nothing else, so this is latent. When CAD notes or
  a panel drawing README land there they will be unscanned.
- Firmware: `firmware/` holds one file, `README.md` `[test]`. When real sources
  arrive, note that `corpus_files()` accepts only `.md/.csv/.yaml/.yml`
  `[repo] tools/check-staleness.py:83` — a figure hard-coded in a `.c`, `.h`,
  `.py` or `.ino` file will never be scanned, while `CORPUS_DIRS` naming
  `firmware` makes the corpus look covered.

### 4.3 `MIN_CORPUS_FILES` has 21 files of slack

`MIN_CORPUS_FILES = 100`, corpus is 121 `[repo] tools/check-staleness.py:53`.

`[test]` `find hardware -name notes.md -delete` — 15 files, every "what this
circuit used to be" record in the repository:

```
→ FAIL … + 24 links … | corpus 106 files
```

It failed, but on *broken links*, not on the floor; the floor did not trip.
`[test]` Likewise `mv docs/decisions docs/adr` gives `corpus 106 files` — the
`isdir` assertion caught it, the floor did not. The floor is doing less work
than the `isdir`/`contributed-no-files` assertions beside it; those are the load
bearing part.

### 4.4 `check_bom()` never asserts the BOM's shape

`[repo] tools/check-staleness.py:237` — `hdr, n = rows[0], len(rows[0])`. The
column count is read *from the file*, and the header is never compared to `HDR`.

`[test]` Rewriting `hardware/bom.csv` with only its first 5 columns:
`check_bom()` returns `[]` problems and reports `ncols 5`. The detail line
"bom.csv: 138 rows x 11 cols" is therefore a description, not an assertion.
Caught end-to-end by `merge-bom.py --check`'s byte compare, so this is
defence-in-depth only — but "11 columns" is a stated invariant
(CLAUDE.md, hardware conventions) and nothing states it in code except
`merge-bom.py`'s `HDR`.

### 4.5 `merge-bom.py`: a fragment named in `ORDER` but absent is skipped silently

`[repo] tools/merge-bom.py:107-109` — `if not os.path.exists(path): continue`,
with the comment "not every circuit owns parts". `merge-manifests.py` treats the
same situation as fatal ("FINDING NO FRAGMENTS IS NOT AN EMPTY MERGE, IT IS A
BROKEN TREE" `[repo] tools/merge-manifests.py:15-26`); `merge-bom.py` does not.

`[test]` `rm hardware/module/dac8568/bom.csv`, then run the documented remedy for
"master does not match its fragments":

```
merge-bom.py --check   hardware/bom.csv does not match its fragments, first difference at line 65   rc=1
merge-bom.py           bom.csv: wrote 136 rows from 23 fragments | 0 problems                       rc=0
merge-bom.py --check   bom.csv: checked 136 rows from 23 fragments | 0 problems                     rc=0
```

Two rows (`R-CLR-PU`, `R-LDAC`) left the BOM and every tool is green afterwards.
In this particular case `check_circuits` rescued it — three `refdes:` edges went
dangling and check-staleness reported `+ 3 deps` `[test]`. But that rescue only
exists for the 79 of 138 rows that some `circuit.yaml` names (§2.5); for the
other 59 the deletion is silent. The row-count delta *is* printed
(`24 fragments` → `23 fragments`, `138` → `136`) but only in `merge-bom.py`'s own
output, which is `detail_only` inside check-staleness and never reaches the hook
summary. A `MIN_BOM_ROWS`-style tripwire, or the same "refuse when a named
fragment is missing" stance as `merge-manifests.py`, would close it.

---

## 5. What is genuinely sound — do not re-attack these

Each verified by planting the defect and confirming the tool bit `[test]`.

**`merge-bom.py`** is the best-defended tool in the set.

- Fragment on disk not named in `ORDER` → reported, with the right sentence.
  `mv hardware/module/dac8568/bom.csv hardware/module/dac8568-new/` →
  `"hardware/module/dac8568-new/bom.csv exists but is not in ORDER … it would be
  silently dropped"`.
- Fragment header altered (`ref` → `refdes`) → reported with both headers printed.
- Same refdes in two fragments → `"hardware/module/dac8568/bom.csv:2 refdes
  'R-CLR-PU' is already owned by hardware/module/panel-led/bom.csv:5"`, naming
  both sides. I could not get a duplicate past it.
- Hand edit to the master → byte compare catches it and names the first
  differing line. CRLF is emitted correctly
  `[repo] tools/merge-bom.py:143-152`; I could not produce a spurious whole-file
  diff.
- `--check` never writes.

**`merge-manifests.py`**'s guards are well-built (their *reporting through
check-staleness* is not — §2.1):

- Zero fragments → refuses, explains that the fragments are dotfiles.
- Problems are evaluated **before** the write `[repo]:162-170`, so a bad fragment
  header cannot silently drop a researcher's rows.
- `.moves.csv`: header mismatch, wrong column count, empty path, one path mapped
  to two destinations, and a chained move are each refused with a specific
  message. I tried all five; all held.
- The `DISTINCTIVE`/`_freq` heuristic is computed over `all_parts` rather than
  the merge result, and the reasoning in the comment
  `[repo]:218-227` checks out: the WS2815 double-bank is the case it is tuned
  against, and it correctly reports "CHECK", never "fact".

**`verify-datasheets.py`** — everything it checks, it checks properly:

- SHA mismatch on a byte-tampered PDF: caught, `rc=1`.
- Banked file deleted: caught, `rc=1`.
- `%PDF` magic and the 10 KiB / 256 B size floors are real tests for the failure
  they name (an HTML error page saved as `.pdf`).
- Orphan artefacts on disk with no row: caught by the reverse walk.
- Missing `hardware/bom.csv` → `REFUSING TO REPORT` rather than a clean summary
  `[repo]:100-104` — the right stance, and the one `check_verified_against()`
  does not take about a missing `MANIFEST.csv`.
- The corpus dangling-path scan `[repo]:171-199` is the right general form.

**`check-staleness.py`**, the parts that hold:

- `check_corpus_shape()`: `mv docs/decisions docs/adr` → `FAIL 1 shape`, and the
  `isdir` + "contributed NO files" assertions are what actually caught it, not
  the floor.
- The `TOOL_INPUTS` early return: moving `hardware/bom.csv` produces
  `FAIL 1 shape | … | checks did not run` — the honest verdict, in the format the
  hook can see. (Its *detail file* is the problem, §3.1, not this.)
- The line-joining fix for hard-wrapped forbidden phrases works as described; the
  `lineof` bookkeeping and the multi-line `ctx` are correct.
- The `NOT_REFDES` filter and keeping `check_refdes` advisory: the reasoning
  (an inferred edge has an unusable noise floor) is right, and running it
  advisory is the right compromise.
- Reporting 7 figure owners as UNVERIFIABLE rather than passing them is the
  correct pattern — it is the pattern §2.11 asks for on empty `forbidden` lists.

**`check-conservation.py`**, outside §1:

- Any interior deletion of one word or more is a REAL GAP. `[calc]` an interior
  loss of *k* words breaks `k + N - 1 ≥ N` shingles; verified with a dropped
  25-word sentence → `gap 35 words @ 20`, `rc=1`.
- A changed *value* mid-paragraph breaks 8 shingles → REAL GAP.
- The explicit `tail_lost` comparison works.
- The word-stream design genuinely survives rewrapping and `> ` stripping, which
  is what it was built for.
- It exits non-zero on a finding.

**`rewrite-paths.py`** — I did not find a way to fool `--invert`. Byte identity
under inversion is a strong proposition, the `invert_targets()` fix (including
files that did not move) is the right one, and `HISTORY`/`HAND_EDITED` are short
and stated. The only structural note is §4.2's third bullet, which is a scope
observation with no live defect behind it.

---

## 6. Do any two checks disagree?

One real one, one near-miss.

**Real.** `check_owners()`'s docstring says a value must be *distinctive* to be
evidence and names `spi-series-r` → `100` as the case it cannot reach
`[repo] tools/check-staleness.py:509-520`. The code then verifies
`spi-series-r`'s owner against exactly that token `[test]`. The docstring and
the code make opposite claims about the same figure. (The docstring is
describing the `any()`-over-all-tokens bug that *was* fixed; the substring
weakness that remains has the same consequence for this figure.)

**Near-miss.** `verify-datasheets.py` treats a missing `hardware/bom.csv` as
grounds to refuse to report at all `[repo]:100-104`, on the argument that a
clean summary would be "a lie about half this tool's job". `check-staleness.py`'s
`check_verified_against()` treats a missing `datasheets/MANIFEST.csv` as grounds
to `return []` `[repo] tools/check-staleness.py:401-402` — the opposite stance on
the identical question. In practice `merge-manifests.py --check` would catch a
vanished manifest first, so this is a stance inconsistency rather than a live
hole; but the two functions are five hundred lines apart and reason in opposite
directions.

---

## 7. Summary table — what a PASS proves

| check | a PASS proves | it also passes |
|---|---|---|
| `check_figures` | no *listed* forbidden literal appears un-"refuted" | any unlisted spelling (§2.11 — 5 of 7 tried); any line containing `was`/`old`/`prior` (§2.3); a figure with an empty `forbidden` list (4 of 35) |
| `check_owners` | some ≥3-char digit run from the value appears somewhere in the owner file | a coincidental digit run in unrelated prose (§2.4); 18 of 30 settled figures rest on a ≤4-char token; any figure whose `status` is not `settled` (§2.10) |
| `check_links` | every inline `](*.md)` resolves | links to `.csv`, `.yaml`, `.dxf`; reference-style links; `README.md`-cased targets (§2.9) |
| `check_sections` | some corpus file **of that basename** declares that § | the wrong file of the same name — `notes.md` ×15, `README.md` ×10 (§2.8) |
| `check_circuits` | edges with one of five exact prefixes resolve | any other prefix, silently (§2.5); a circuit evicted by a duplicate id (§2.6); 59 of 138 BOM rows have no dependent |
| `check_verified_against` | the cited SHA is in *some* manifest row | a SHA from a different part's row (§2.7); anything about the bytes on disk (§4.1) |
| `check_checks` | each `check_*` name is a substring of `main`'s source | a call commented out with the name intact; a result computed and never consulted (§2.2) |
| `check_bom_generated` | `merge-manifests --check` exited 0 **and** `merge-bom --check` exited 0 | nothing — but a manifests failure hides the BOM result and is reported as a crash (§2.1) |
| `check_corpus_shape` | the named dirs exist and contributed ≥1 file each | a 21-file deletion (floor slack, §4.3); anything behind a symlinked directory (§2.12) |
| `check_bom` | rows are as wide as row 0 and refdes are unique | a 5-column `bom.csv` (§4.4) |
| `merge-bom --check` | the master is byte-identical to `ORDER`'s fragments | a fragment named in `ORDER` that has been deleted (§4.5) |
| `merge-manifests --check` | the master is byte-identical to the fragments | — sound |
| `verify-datasheets` | every banked byte matches its row, no orphans, no dangling `datasheets/…` citation | — sound, but nothing runs it (§4.1) |
| `check-conservation` | no ≥8-word interior run, and no 8-word tail, is missing | ≤7 words off the **front** (§1); a duplicated passage losing one copy; any reordering |
| `rewrite-paths --invert` | every rewritable file is byte-identical under the inverse | — sound |

---

## 8. Ranked, if only some get fixed

1. **§2.1** — manifests failure masks a hand-edited `bom.csv`, and deletes a good
   message to print a wrong one. Two small edits: harvest all output, and do not
   return early.
2. **§1** — `check-conservation.py` head loss (and duplicate-passage loss). Four
   lines, mirroring the `tail_lost` block that is already there.
3. **§2.3** — drop `was`/`were`/`old` from `REFUTATION`, and print the refuted
   *count* on the always-printed line. 59 findings currently ride on this.
4. **§3.1** — write `.staleness/report.txt` on the early-return path, or stop the
   hook telling the reader to trust it.
5. **§2.5** + **§2.6** — an `else:` clause and a dict-collision check. Two lines
   between them.
6. **§2.11** — report figures with an empty `forbidden` list the way
   `check_owners` reports UNVERIFIABLE owners, and put a pattern count on the
   PASS line.
7. **§4.1** — run `verify-datasheets.py` from `check_bom_generated()`, or say in
   CLAUDE.md that §3's "must pass" is a human rule with no enforcement.
8. **§2.13** — one `try/except` in `check_refdes`.
9. **§2.4**, **§2.7**, **§2.8**, **§2.9**, **§2.10**, **§2.12**, **§4.4**, **§4.5**
   — real, each small, none urgent on today's corpus.

---

## 9. Reproduction

Everything above ran against an unmodified export of `HEAD` (61060ed):

```sh
S=<scratch>
mkdir -p $S/base && git -C /home/user/Woody archive HEAD | tar -x -C $S/base
# per experiment
rm -rf $S/eN && cp -a $S/base $S/eN && cd $S/eN
# …mutate…
python3 tools/check-staleness.py           # or --detail / --verbose
```

The tools derive `ROOT` from their own `__file__`
(`[repo] tools/check-staleness.py:18`, `merge-bom.py:26`,
`merge-manifests.py:10`, `verify-datasheets.py:18`), so a copied tree is
self-contained. `check-conservation.py` needs a git repo, so §1's experiments
used a fresh two-commit scratch repo with the tool copied in. The hook was
reproduced by executing the `command` string from
`[repo] .claude/settings.json:9` verbatim with `CLAUDE_PROJECT_DIR` pointed at
the scratch tree.

The repository was not modified. This file is the only thing C2 wrote.
