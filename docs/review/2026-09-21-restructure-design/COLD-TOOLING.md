# COLD review — tooling and structure of the 2026-09-21 restructure

**Method.** Cold: no file under `docs/review/**` was opened, including this
wave's own design reports and any STATUS or VERIFIED file. `git log` and
`git show` were read. Every "the check is fooled" claim below was reproduced in
a throwaway `git archive HEAD` tree under the session scratchpad; the working
tree was never modified (`git status --porcelain` empty before and after).

Provenance: `[repo] path:line` · `[cmd]` a command run · `[test]` a defect
constructed in the throwaway tree and observed · `[calc]`.

Ranked by what it costs if left.

---

## F1 — One non-UTF-8 byte in any BOM fragment turns the generated-file guard off, silently, and flips FAIL to PASS

`check_bom_generated()` shells out to `merge-bom.py --check`, and on a non-zero
return it harvests **stdout only**:

```
if r.returncode == 0:
    return []
return [l.strip() for l in r.stdout.splitlines() if l.strip() and "problems" not in l]
```
`[repo] tools/check-staleness.py:182-185`

A crash in `merge-bom.py` writes a traceback to **stderr** and leaves stdout
empty, so the list comprehension returns `[]` — indistinguishable from "no
problems". `generated_problems` is falsy, `fail` is never set, and the tool
prints `PASS`.

`merge-bom.py` opens every fragment as UTF-8 `[repo] tools/merge-bom.py:94-95`,
so one Latin-1 byte — a `µ` or `Ω` pasted from a spreadsheet export into a
`description` — is enough.

**[test] Reproduction** (throwaway tree):

```
# 1. a genuine defect the guard exists to catch
$ python3 - <<'X'
t=open("hardware/bom.csv",encoding="utf-8",newline="").read().replace("10k","47k",1)
open("hardware/bom.csv","w",encoding="utf-8",newline="").write(t)
X
$ python3 tools/check-staleness.py
FAIL 0 shape + 0 owners + 0 links + 0 sections + 0 deps + 1 generated + 0 stale + 0 bom | ...
exit=1                                                     # correct

# 2. leave that hand-edit in place, add ONE byte to ONE fragment
$ python3 -c "b=open('hardware/module/pitch-stage/bom.csv','rb').read().replace(b'Pitch',b'Pitch \xb5',1); open('hardware/module/pitch-stage/bom.csv','wb').write(b)"
$ python3 tools/merge-bom.py --check
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb5 in position 402
exit=1
$ python3 tools/check-staleness.py
PASS no live stale values | corpus 118 files, 23 circuits | 5 unresolved (tracked)
exit=0                                                     # the hand-edit is still live
```

This is the fourth instance of the exact class `repo-maintenance.md` §6
tabulates as "used to fail open … all three were fixed on 2026-09-21"
`[repo] docs/reference/repo-maintenance.md:189-202`. The table does not list
`merge-bom.py`, which is the tool that now has the defect.

Secondary, same mechanism: `check_figures()` swallows any read error with
`except Exception: continue` `[repo] tools/check-staleness.py:122-125`, so that
same fragment is also dropped from the staleness scan — while the corpus file
count, which the tool explicitly nominates as the number a reader should check
(`[repo] tools/check-staleness.py:676-678`), still reads **118**, because
`corpus_files()` counts names, not successful reads. **[test]** verified: 118
with and without the unreadable file.

**Fix shape:** treat a non-zero return with empty stdout as a problem, and
include `r.stderr`. Three lines.

---

## F2 — `bom.csv` became generated today and the two documents a reader is told to read first still tell them to hand-edit it

This is the project's named failure mode, landed in commit `c483829`, in the
two files `CLAUDE.md` nominates as authority.

- `[repo] CLAUDE.md:132-135` (Hardware conventions): "`hardware/bom.csv` is 11
  columns **and CRLF**. Validate column count and duplicate refdes **after any
  edit** — and pass `lineterminator="\r\n"` to `csv.writer`". This describes
  editing the master. `CLAUDE.md` §4 names only `MANIFEST.csv` as generated.
- `[repo] docs/reference/repo-maintenance.md:126-143` §4 is titled
  "`hardware/bom.csv` — eleven columns, CRLF" and says "**Validate column count
  and duplicate refdes after any edit**". It never says the file is generated.
  (§1's table at line 19 *does* say so, and even notes "this table did not say
  so for several hours" — so the file contradicts itself across two sections.)
- `[repo] docs/reference/repo-maintenance.md:177-183` §6 "Running the tools"
  lists four commands, omits `merge-bom.py` entirely, then says "**All three**
  are expected to pass before a commit".
- `[cmd] grep -rl merge-bom` over the corpus: the only file in the repository
  that mentions `tools/merge-bom.py` is `tools/check-staleness.py`. Not
  `CLAUDE.md`, not `repo-maintenance.md`, not `README.md`.
- `[repo] README.md:102` still says `hardware/ BOM, schematics, PCB, split by
  board`. It is now split by *circuit* under board directories, plus
  `hardware/interfaces/`, which is not a board.

Compounding: `[cmd]` there are now **25 files called `bom.csv`** and **47 bare
backticked `` `bom.csv` `` references** in the corpus. "Edit bom.csv" no longer
names a file.

Cost if left: the next person follows the instruction, edits the master, the
edit survives until the next `merge-bom.py` run and then disappears. That is
verbatim the accident `CLAUDE.md` §4 was written about.

---

## F3 — `MANIFEST.csv`, the file that actually had the accident, is still the one with no `--check`

`bom.csv` got a byte-comparison guard wired into the commit path. The manifest
did not. `merge-manifests.py` has no `--check` flag at all
`[repo] tools/merge-manifests.py:1-8`, and nothing in `check-staleness.py`
reconciles `MANIFEST.csv` against its fragments.

**[test] Reproduction:**

```
$ python3 -c "t=open('datasheets/MANIFEST.csv').read().replace('BLOCKED','BLOCKED - closed by R9, see bench log',1); open('datasheets/MANIFEST.csv','w').write(t)"
$ python3 tools/check-staleness.py   ; echo exit=$?   # exit=0
$ python3 tools/verify-datasheets.py ; echo exit=$?   # exit=0
$ python3 tools/merge-bom.py --check ; echo exit=$?   # exit=0
$ python3 tools/merge-manifests.py   ; echo exit=$?   # exit=0
$ grep -c "closed by R9" datasheets/MANIFEST.csv
0                                     # destroyed, no warning, all checks green
```

Related, same file: `merge-manifests.py` **writes `MANIFEST.csv` at line 142
before it prints any problem at line 269**. A fragment with a bad header is
skipped whole `[repo] tools/merge-manifests.py:95-96`, so a header typo silently
drops that researcher's rows out of the manifest on disk, and only *then* exits
1. The zero-fragment case is guarded `[repo] tools/merge-manifests.py:21-26`;
the one-broken-fragment case is not.

Also dead: `historical` is computed at `[repo] tools/merge-manifests.py:232-239`
and never printed or used. Same shape as the `check_refdes` defect the repo
already found once.

---

## F4 — `check_owners`' "distinctive token" filter still passes the exact figure its own docstring names as the counter-example

The docstring says a weak value must be reported UNVERIFIABLE rather than
passed, and names two: `chain-connectors` ("8") and `spi-series-r`, which
"tokenises to 100 and 3" `[repo] tools/check-staleness.py:458-469`.

The implemented filter is `len(t) >= 3` on `\d+\.?\d*`
`[repo] tools/check-staleness.py:470`. `"100"` is three characters, so
`spi-series-r` passes the filter and is checked against a bare substring search
for `100` — and the match is `any()`, not `all()`
`[repo] tools/check-staleness.py:481`.

The owner page contains `100` in at least two places that have nothing to do
with the resistor: `[repo] hardware/interfaces/spi-link/spi-link.md:62` "a
**100 Ω transmission line**" (the Cat5 characteristic impedance, a different
quantity that coincidentally equals it) and `:101` "not 100 %".

**[test] Reproduction** — removed every statement of the figure from its owner,
left the two unrelated `100`s:

```
$ sed  # "the value is 100 Ω" -> "the value is derived elsewhere now", 4 sites
$ python3 tools/check-staleness.py --detail | grep -i "owner\|PASS"
figure owners this check CANNOT verify (7) ...        # spi-series-r NOT among them
PASS no live stale values | corpus 118 files, 23 circuits | 5 unresolved (tracked)
```

The owner no longer states the figure, the check is green, and it does not even
flag itself as unverifiable. Commit `2a9c720` ("check_owners was passing three
figures by accident, and now says so") closed the `len < 3` half and left this
half open.

**Fix shape:** distinctiveness is measurable, not guessable — require the token
to occur in few enough corpus files to be evidence (`_freq`-style, as
`merge-manifests.py:195-200` already does for part tokens), and require *all*
tokens rather than any.

---

## F5 — `circuit.yaml` `depends_on` is co-mention, not dependency, and two of the three checks over it are checks over an empty set

**[cmd]** 23 files, 294 edges: `refdes` 126, `fig` 87, `circuit` 50, `adr` 31.
No file declares `provides:` or `verified_against:` — the only keys present
across all 23 are `id`, `title`, `last_reviewed`, `depends_on`.

Consequences:

- **`check_verified_against()` can never fail.** It iterates
  `c.get("verified_against") or []` `[repo] tools/check-staleness.py:363`, which
  is empty for all 23 circuits. The re-bank detection its docstring describes
  (`:347-352`) has no data to run on. `check_checks()` confirms it is *called*;
  nothing confirms it *checks* anything.
- **The `node:` branch is unreachable-by-construction.** `provided` is built
  from `provides:` `[repo] tools/check-staleness.py:302-304`; it is empty, so
  any `node:` edge would fail. There are none. The type prefix is advertised in
  the error text at `:320` and has no instance.

**The direction of `circuit:` edges is not meaningful.** `module/power-entry`
declares `depends_on: circuit:module/pitch-stage`, and `module/pitch-stage`
declares `depends_on: circuit:module/power-entry`. Power entry does not depend
on the pitch stage. **[cmd]** the graph has 2-cycles throughout —
`power-entry↔umbilical-load-switch`, `dac8568↔digital-and-supervision`,
`dac8568↔link-supervision`, `breath-output↔breath-receive`,
`breath-response-shaper↔breath-output-stage`. `check_circuits()` resolves names
and never looks at shape, so cycles are neither detected nor a problem for it —
but they mean the field cannot answer "what does this depend on", only "what
does this page mention". The two questions are the same only for a graph nobody
traverses.

**`refdes:` edges are 40% wrong against the repository's own answer.**
**[cmd]** reconciling each `refdes:` edge against the per-circuit `bom.csv`
fragments (whose assignment rule is documented at
`[repo] tools/merge-bom.py:13-21`):

```
refdes edges whose part IS in this circuit's own bom fragment : 75
refdes edges whose part is owned by another circuit / nobody  : 51
```

Some of the 51 are legitimate crossings (`HDR-DEV`, `J-CHAIN`). Three verified
by reading the page:

| Edge | What the page actually says |
|---|---|
| `module/pitch-stage → refdes:R-BIAS-INAMP` | "This project already fixed the identical problem on the breath in-amp with `R-BIAS-INAMP`. **`R-BIAS-DAC` now does it here**" `[repo] hardware/module/pitch-stage/pitch-stage.md:322`. An explicit contrast. `tools/merge-bom.py:20-21` independently documents this exact token as the counter-example for "where it is mentioned". |
| `carrier/breath-adc → refdes:C-STRIP-BULK` | "The repo's own `C-STRIP-BULK` note puts the WS2815 PWM rate at ~2 kHz" `[repo] hardware/carrier/breath-adc/breath-adc.md:85`. A citation of a note about the LED strip's bulk cap. |
| `module/breath-receive-stage → refdes:U-OPA-PITCH` | "It costs the last spare OPA2197 half, and `U-OPA-PITCH` goes to six packages" `[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:165`. A package-count consequence. |

**Obviously missing:** **[cmd]** every `circuit:` edge in the graph originates
in `interfaces/**` or `module/**`. `carrier/**` and `cluster/**` declare **zero**
circuit-to-circuit edges between them. `module/power-entry` names seven sibling
circuits; `carrier/power-entry-instrument`, which feeds `breath-adc`,
`led-strip-drive` and `display-and-service-uart` off the same buck, names none.
Whatever seeded the graph did the module board and not the carrier board, and
because `check_circuits` only asks whether declared edges resolve, a board with
no edges is indistinguishable from a board with correct ones.

Also missing on the same page-level evidence: `module/panel-led` declares
`refdes:PANEL` but not `circuit:module/panel`; `module/pitch-stage` and
`module/mod-channels` both carry `D-JACK-CLAMP` and `R-OUT-PROT` (panel jacks)
but neither declares `circuit:module/panel`, while `breath-output-stage` and
`breath-response-shaper` do.

---

## F6 — The commit hook: blank on crash, and its one instruction points at a file that never holds the detail

`[repo] .claude/settings.json` — the hook greps stdout for
`^(STALE VALUES STILL LIVE|BOM INTEGRITY|PASS|FAIL)`.

**(a) A malformed input renders green-blank.** `check-staleness.py:52-56`
records this failure and fixes it for the case where `config/figures.yaml` or
`hardware/bom.csv` is *missing*. A **malformed** `config/figures.yaml` — the
file rule 2 tells you to edit on every figure change — still crashes before the
guard.

**[test]** appended two lines of bad YAML to `config/figures.yaml`, ran the hook
command verbatim:

```
HOOK WOULD SAY: >>>staleness: <<<
```

`|| true` swallows the exit code, the traceback matches none of the four
anchors, and the hook reports an empty string. The `additionalContext` the model
receives becomes `"staleness check:  Full list in ..."`.

**(b) The hook tells you to read the wrong file, and not to re-run.** It writes
stdout to `.staleness-report.txt` and says *"Full list in
`.staleness-report.txt` - read it when fixing, **do not re-run for detail**"*.
Without `--detail`, every detail block is `detail_only=True`
`[repo] tools/check-staleness.py:258-263`, so stdout is one line. The list is in
`.staleness/report.txt`.

**[test]** on a genuine stale value (`set to 5.25V`, a real `dac-rail`
forbidden pattern):

```
HOOK MESSAGE: staleness: FAIL ... + 1 stale + ... | detail: .staleness/report.txt or --detail
--- .staleness-report.txt (what the hook says to read) ---
FAIL ... + 1 stale + ...                     # one line. no list.
--- .staleness/report.txt (never named by the hook) ---
STALE VALUES STILL LIVE (1)
  [dac-rail] is now: 5.21 V
      hardware/module/dac8568/dac8568.md:35  found 'set to 5.25V'
```

The two halves of the same hook message contradict each other, and the half
that is wrong is the one phrased as an instruction.

**(c) Two of the four grep anchors are dead.** `STALE VALUES STILL LIVE` and
`BOM INTEGRITY` are emitted `detail_only=True`
`[repo] tools/check-staleness.py:636,651` and can never appear in hook-mode
stdout. Harmless today; misleading to anyone maintaining the regex.

**(d) The hook never blocks.** The `jq` output carries `systemMessage` and
`additionalContext` and no `permissionDecision`, so a `FAIL` is advisory. That
matches `CLAUDE.md:41-42` ("surfaces the result"), but it means the hook's only
effect is the text — which is exactly what (a) and (b) degrade.

---

## F7 — `check-conservation.py` always exits 0, loses the last seven words silently, and is referenced by nothing

**Exit code.** The script ends at the `for pos,gap,text in real:` print loop
`[repo] tools/check-conservation.py:60-61`. There is no `sys.exit`.

**[test]**

```
REAL GAPS (source text with no home): 1
  gap 14 words @ 109: ...
exit=0
```

Anything that wires this into a `&&` chain, a hook or CI reads loss as success.

**The 8-word shingle is defensible in the middle and blind at the ends.** A
deletion of *k* words from the interior loses `k + N - 1` shingles, so `k = 1`
already gives a gap of 8 and is reported — the threshold is sound there. At the
**tail** the gap is `k`, capped by the last shingle index, so it lands under the
`< N` "seam" filter `[repo] tools/check-conservation.py:56` and is never
printed.

**[test]** deleting the final *k* words of a 496-word source:

```
tail-1  -> seams: 1   REAL GAPS: 0
tail-3  -> seams: 1   REAL GAPS: 0
tail-5  -> seams: 1   REAL GAPS: 0
tail-7  -> seams: 1   REAL GAPS: 0
tail-8  -> seams: 0   REAL GAPS: 1
```

**Losses of 1–7 words at the end of a source page are invisible.** The head is
fine — deleting the first 7 words reports `gap 8 @ 0` **[test]**. The tail of a
schematic page is where the cross-references and the "see notes.md" pointers
live.

**Markdown furniture is fine in practice.** `words()` strips `` ` * ~ _ # | > ``
but not `-`, so a `---` rule and a table separator become `---` tokens. On real
content this did not mask anything: **[test]** against
`hardware/module/dac8568/dac8568.md`, deleting one line of the ASCII drawing
reported `gap 14`, and deleting one row of the `## Interfaces` table reported
`gap 27`. The `│` runs did not bridge either gap. I could not construct a
false negative from table or rule tokens on a real page.

**Nobody can find it.** **[cmd]** `grep -rl check-conservation` across the
corpus, `CLAUDE.md`, `repo-maintenance.md`, `.claude/settings.json` and the other
tools returns **nothing but the file itself**. It is the only check written
specifically for a restructure, and it is undiscoverable and green-on-loss.

---

## F8 — Structure: two of the four board directories have no board page, and the one page that says it is not a circuit is registered as one

**[cmd]** `hardware/` contains `carrier/`, `cluster/`, `interfaces/`,
`module/`. `carrier/carrier.md` (402 lines) and `cluster/cluster-boards.md`
(225 lines) are board pages. `hardware/module/` and `hardware/interfaces/` have
none, and there is no `hardware/README.md`.

`[repo] git show 9daec7f` shows why: the module board never had one — six
sibling circuit pages moved into circuit directories, and the overview that
would have become `module.md` never existed.

The visible consequence is `hardware/module/panel/panel.md`, whose first
sentence is "**A board-level page, not a circuit**, so it carries no
`## Interfaces` table" `[repo] hardware/module/panel/panel.md:3`. It sits in a
circuit directory, carries `circuit.yaml` with `id: module/panel`, and two other
circuits declare `depends_on: circuit:module/panel`. A board-level page is being
filed as a circuit because the tree has nowhere else to put one.

That page also breaks rule 1 in the sentence that claims to obey it. It says it
"cites them and does not restate them", then restates both:
`[repo] hardware/module/panel/panel.md:24` "**10HP is 50.50 mm**" against
`panel-width = 50.50 mm (10HP)`, and `:28` "**110 mm of content against 115.5 mm
of clear panel**" — the value string of `panel-height-budget`, verbatim, owned by
`docs/decisions/0004-cv-interface-module.md`.

**What is genuinely well done here, and worth protecting:** `carrier.md` keeps
the connected drawing and states in prose, at each cut, which argument went
where and why the picture stayed `[repo] hardware/carrier/carrier.md:151-166`.
That is the right call — but it leaves component values live in two places
(**[cmd]** `37.4`, `47 nF`, `1 nF`, `5.000 V`, `4.86` each appear on both the
board page and the circuit page), and no figure entry covers most of them.

**`hardware/interfaces/` is the right home** for the three crossing circuits —
`breath-sense-link`, `spi-link`, `key-chain-loom` each consolidate two halves
that previously derived from parts drawn only in the other
`[repo] hardware/interfaces/*/notes.md`. It does not duplicate the board pages;
the board pages keep the drawings and hand off the arguments. Its three
`notes.md` are, however, byte-identical boilerplate with the names swapped
(13 lines each, "This directory did not exist before 2026-09-21") — three files
whose entire content is what `git log` says.

---

## F9 — `check_sections` pools all 15 `notes.md` into one namespace

`declares` is keyed on `os.path.basename(path)`
`[repo] tools/check-staleness.py:399-404`, so every file with the same basename
shares one set of declared `§` numbers. The restructure took `notes.md` from a
handful to **15** and `README.md` to 7 **[cmd]**.

**[test]** added `## §9 …` to `hardware/module/dac8568/notes.md`, then added
`See [`notes.md`](notes.md) §9` to `hardware/module/pitch-stage/pitch-stage.md`
(whose own `notes.md` has no §9):

```
PASS no live stale values | ...
```

Control, pointing at `§77` which no `notes.md` declares:

```
hardware/module/pitch-stage/pitch-stage.md:334 points at notes.md §77,
    which that page no longer declares
```

Note the message says "**that page**". There are fifteen. Latent today (no
`notes.md §N` reference exists), created by the restructure.

Same root, wider: **[cmd]** 227 bare backticked filename references and 210
backticked path references exist in the corpus; `check_links` only inspects
`](…md)` markdown links `[repo] tools/check-staleness.py:501`. I checked all 210
pathed ones by hand — **all resolve** — but nothing checks them, and
`` `bom.csv` `` (47 uses) and `` `notes.md` `` (22 uses) no longer name a file.

---

## F10 — `MIN_CORPUS_FILES` was sized for a 33-file corpus and is now 3.9× slack

`MIN_CORPUS_FILES = 30` `[repo] tools/check-staleness.py:50`, with the comment
"Splitting files moves the count UP… **Raise it when the tree grows**". The
corpus is now **118** `[cmd]`. It was not raised. 88 files can vanish before the
tripwire moves.

In fairness, I could not construct a case where the floor was the check that
mattered: **[test]** deleting 10 of 23 circuit directories (118 → 81 files) was
caught by 18 broken links + 15 dep problems + 4 owner problems, and stripping
`docs/reference/` to two files was caught by 8 broken links. The
`isdir`/`contributed-no-files` assertions and `check_links` are doing the work.
Low cost, but the floor currently asserts nothing.

---

## F11 — Nothing checks the rule the register exists to enforce

Rule 1 is "the owning document states it and every other document **cites it by
name**". The checker only searches for values listed in `forbidden`, i.e. values
already known to be *old*. Restating the **current** value elsewhere is
undetectable — and it is the state from which every future staleness defect is
born.

**[cmd]** scanning each settled figure's most distinctive numeric token across
non-owner corpus files, excluding `notes.md` and refuted lines. The scan is
noisy for common tokens (`100`, `2.2`, `6.5`), so only the low-noise cases:

| Figure | Owner | Restated in |
|---|---|---|
| `panel-width` (50.50) | ADR 0004 | `hardware/module/panel/panel.md:24,31` |
| `panel-height-budget` (115.5) | ADR 0004 | `hardware/module/panel/panel.md:28` |
| `mod-reference` (3.3333) | `mod-channels.md` | ADR 0006, 8 lines |
| `dac-rail` (5.21) | `power-entry.md` | 19 lines across 6 module pages |
| `inamp-full-scale` (9.94) | `breath-sense-link.md` | 9 lines |
| `sensor-full-scale` (4.86) | ADR 0003 | 6 lines — *the figure `CLAUDE.md:34-39` names as the worst recorded case* |
| `loadswitch-fb-divider` (35.7) | `power-entry.md` | `umbilical-load-switch.md:173` + its own bom fragment |
| `key-press-time` / `key-release-time` | `key-switch-network.md` | ADR 0001:227-228 |
| `opa2197-output-impedance` (375) | `breath-excitation-reference.md` | ADR 0005:312 |

This is the cheapest missing check in the repository: the register already
carries `owner:`, and `false_positive_note:` already exists
`[repo] docs/reference/repo-maintenance.md:160-164` as the allowlist mechanism
for legitimate occurrences.

---

## F12 — `unplaced.csv` holds the principal IC of five circuits that now have directories

`repo-maintenance.md:148-155` describes `hardware/unplaced.csv` as "the 50 rows
of 138 that **no schematic page names**". **[cmd]** that is true for 47 of 50 —
I checked every row against every `hardware/**/*.md` by refdes and by the
documented short form. The three exceptions matter:

- `C-TIMER-LOADSW` and `C-GATE-LOADSW` are drawn (as `C-TIMER` / `C-GATE`) on
  three and two pages respectively, and they set two tracked figures,
  `loadswitch-timer` and `loadswitch-gate-cap`, both owned by
  `hardware/module/power-entry/power-entry.md`. `check-staleness.py:250-252`
  documents this exact short/long spelling pair. They are filed as unnamed.
- `U-LVL-MOD` is named outright on one page.

The deeper issue is that the rule was applied by **refdes string**, not by
reading the page, so the main active parts — which the drawings label by part
number, not refdes — fell through:

| Part | In `unplaced.csv` | Circuit directory that exists |
|---|---|---|
| `U-DAC` DAC8568CIPW | yes | `hardware/module/dac8568/` — its fragment holds 2 resistors and not the DAC |
| `U-DIFFRX` INA828IDR | yes | `hardware/interfaces/breath-sense-link/` |
| `U-REG-DAC` LM317LZ + `R-REG-SET` + `C-REG-ADJ` | yes | `hardware/module/power-entry/` — fragment holds 1 connector |
| `D-REVPOL` 1N5817 | yes | `hardware/module/power-entry/` — and `diode-split-rationale` is its tracked figure |
| `U-LVL-MOD` 74AHCT125 | yes | `hardware/module/digital-and-supervision/` |

**[cmd]** `grep -rl DAC8568 hardware --include='*.md'` returns six pages
including `hardware/module/dac8568/dac8568.md`, which draws the part in ASCII
with no refdes. The commit message for `c483829` says "138 rows into 24
per-circuit fragments"; 50 of the 138 went to a 25th file with no circuit, no
page and no `circuit.yaml`.

---

# What I checked and found genuinely sound

So the next reader knows the shape of the search and does not repeat it.

- **`corpus_files()` / `check_corpus_shape()`.** The `os.walk`-on-a-missing-
  directory blind spot is genuinely closed. `isdir`, "contributed NO files",
  `CORPUS_FILES` existence and `TOOL_INPUTS` existence all fire, and the
  `TOOL_INPUTS` branch is fatal-and-early `[repo] :555-561` so the checks below
  it cannot report on a tree they never read. Only the *floor* is slack (F10).
- **`check_figures()` line-joining.** The hard-wrap blind spot is closed; a
  forbidden phrase straddling a line break is found, and the refutation context
  spans every line the match touches `[repo] :135-159`. The remaining gap is the
  documented one: the match is a case-sensitive literal, so it only finds
  spellings someone listed (rule 2 step 2 exists for this reason).
- **`check_bom()` CRLF.** Not checked directly, but **[test]** rewriting
  `hardware/bom.csv` with LF endings and identical content is caught by
  `merge-bom --check`'s byte comparison (`FAIL … + 1 generated`). The CRLF
  convention is guarded.
- **`check_links()`.** Correct for what it covers. **[cmd]** all 210 backticked
  repository paths in the corpus resolve, and `rewrite-paths.py --verify`
  reports 0 survivors. The `HAND_EDITED` set is never verified
  `[repo] tools/rewrite-paths.py:101-102`, so I checked those 12 files by hand
  against the map: the only old-side tokens present are in
  `path-map-2026-09-21.csv`'s own `old` column and in `rewrite-paths.py`'s own
  comments, both correct. A permanent exclusion list is a standing risk, not a
  live defect.
- **`check_checks()`.** All eleven `check_*` functions are genuinely called from
  `main()`. The assertion is textual (`(n + "(") not in src`), so a call site
  inside a comment would satisfy it — noted, not exploited.
- **Duplicate `circuit.yaml` id.** **[test]** giving `module/panel` the id
  `module/pitch-stage` is caught — not by a collision check, but by the
  id-must-match-directory assertion `[repo] :313-316`, which makes a collision
  structurally impossible. Sound by construction.
- **`merge-bom.py`'s ORDER discipline.** A fragment on disk that `ORDER` does not
  name is a problem, not a silent drop `[repo] :84-88`. The refdes-ownership
  check is at the right level ("two circuits both claim it", both named).
- **`verify-datasheets.py`'s corpus half.** Genuinely closes the dangling-
  datasheet-citation gap it documents `[repo] :155-199`, and the
  `REFUSING TO REPORT` guard on a missing `bom.csv` is the right shape. **It is
  not wired to anything** — `CLAUDE.md:47-48` says it "must pass before
  committing anything under `datasheets/`", and the only hook runs
  `check-staleness.py` `[repo] .claude/settings.json`. That is a human rule with
  no mechanism, which given the rest of this report is worth knowing.
- **`merge-manifests.py`'s `.moves.csv` design.** The argument for
  re-filing at merge time rather than editing a fragment is correct and the
  guards around it (chain detection, one-destination-per-path, exact header) are
  tight `[repo] :54-82`.
- **`check-conservation.py` on real content.** Beyond the tail blind spot (F7),
  the word-stream approach works: it catches a deleted ASCII-drawing line and a
  deleted table row on a real page, and markdown furniture does not mask them.
- **`hardware/interfaces/` as a home for the three crossing circuits.** Correct
  call, and the board pages hand off rather than duplicate (F8).
- **`carrier.md` keeping the connected drawing whole** while naming, at each
  cut, where the argument went. That is the right trade and it should survive
  any fix to F8.
