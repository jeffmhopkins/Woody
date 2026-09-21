# Pre-merge wave — what it found, and the recommendation

**Closed 2026-09-21.** Twenty-two cold slices, 18,500 lines of report,
twenty-four findings verified by hand and recorded in `VERIFIED.md`. This
file is the answer to the question the wave was opened to answer.

## Outcome: all five items done, 2026-09-21

**The recommendation below was acted on in full.** Kept as written, because a
wave's STATUS is a record of what it found and not of what happened next, and
because the escape table underneath it is the evidence.

| # | What it asked for | State |
|---|---|---|
| 1 | Fix the four checks, then re-run the wave's mechanical claims | **Done.** Each fix is proved by reproducing the attack that defeated it, in a throwaway tree: the documented resistor-change procedure, an owner repointed to an unrelated ADR, a check commented out, a broken link to a non-`.md` file, a BOM hand-edit masked by a manifest problem, a re-introduced stale value, and a deleted page heading. All seven CAUGHT; intact tree still clean |
| 2 | Add the check nobody has — a value in 3+ files with no register entry | **Done**, as `check_restated`. ADVISORY, because `check_refdes` sat unwired for the tool's whole life after being switched on with an unusable noise floor. 233 today |
| 3 | Re-run conservation with a head comparison | **Done.** `check-conservation.py` compares both ends and multiplicity |
| 4 | Link `hardware/README.md` from the front door | **Done**, and the `## Interfaces` definition that sat inline in all 23 circuit pages now lives there once and is cited |
| 5 | Adjudicate the umbilical topology | **NOT done, and deliberately.** Two live topologies, one of them a settled tracked figure. It needs a decision, not an edit, and inventing one would be worse than leaving it visible |

**Three things the fixes then found that no reviewer had:** a fourth instance
of the raw-gain error, in a drawing whose stated formula does not produce the
result written one line below it; the `SCLK` collision, where both nets are on
**one page's own table**, so merging them shorts a buffer across itself; and
the Gateron drawing's text layer, which yields 9,680 characters including the
5 ms contact-bounce figure three documents said the vendor does not publish.

**And three patterns that had to be withdrawn within minutes of being written**,
each because it fired on a sentence that is true. That is the counterpart to
grepping first, and it is now in `CLAUDE.md`: most hits will be legitimate, and
a pattern whose cheapest fix is to make a correct sentence wrong is a trap, not
a check.

## Recommendation: merge the tree, do not merge the green light

**The restructure did what it was asked to do.** Content conservation is not
in doubt, and it is not in doubt because three independent things say so:

- `rewrite-paths.py --invert` — 34 files byte-identical under inverse
  rewrite, and **C2 could not fool it** after thirteen successful attacks on
  the other tools. That is the proof that Phase A changed no content.
- **C1 re-ran the largest conservation proof at HEAD**, cold, rather than at
  the split commit: `carrier.md`, 8,709 words into 16 files, four gaps, all
  four legitimate. **No later commit dropped text.**
- B3 re-read every vector-CAD dimension off the banked artefacts and
  confirmed all of them, including the 1.20 mm plate on both citations.

**What must not merge is the belief that `PASS` means anything.** Five checks
were added during this restructure. This wave established, by reproduction,
that the central ones do not do what their own docstrings say.

### The four that decide it

**1. The documented procedure produces the project's named failure, green.**
Following the three written steps — edit the fragment, regenerate, run the
checker — to change `R-SPI-SER` from 100R to 220R gives `0 problems` and
`PASS no live stale values`, while the register and the owner page both still
say 100 Ω. 220 Ω is *the value that figure's derivation exists to reject*.
Nothing relates a BOM row to the figure governing it; `check_owners` compares
register against owner and after the edit **those two still agree with each
other**. A newcomer following every rule correctly manufactures the exact
defect this repository exists to prevent.

**2. The conservation check is blind at the head of a passage.** Deleting the
first six words of `pitch-stage.md` — its entire H1 and status label —
gives `REAL GAPS: 0, rc=0`. Deleting the last six gives `rc=1`. The tail
comparison exists *because* someone noticed the argument at the end; the
symmetric sentence about the start was never written. **Deleting words off
the front of a passage is what a Phase B split does.** Every "0 REAL GAPS"
in the design wave's STATUS is a weaker claim than it was written as.

**3. `check_owners` passes on part numbers.** Its tokens come from a
digits-only regex, so "the most distinctive token" for `spi-series-r` is
`100` — the exact token its docstring names as the reason the *previous*
version was broken. Repointing that figure's owner to the enclosure ADR gives
`PASS`, exit 0. A quarter of the settled register is verified against a part
number (`OPA2197` for `loadswitch-gate-cap`, `REF5050` for `cref-out-node`)
or an unrelated component value.

**4. A green run and a run with no coverage are byte-identical.** Emptying
every `forbidden` list produces the same PASS line. Four of 35 entries
already carry an empty list; 23 of the 59 current suppressions ride on the
bare word `was`; one pattern contains a literal newline and can never fire.
The report says nothing about how much was actually checked.

### Eight more escapes of the one class, all verified

Every one is a live superseded value that the checker scores clean, and every
one misses by one or two characters:

| Where | Spelling | Missed by |
|---|---|---|
| `0005:74` | `0.2–4.7 V` | tight en dash |
| `0003:565` — **the owner document** | `reaches 4.7 V` | phrasing, 4 lines after stating it right |
| `ROADMAP.md:203` | `Six conductors per hop` | one letter's case |
| `ROADMAP.md:53` | `at 8HP rather than` | phrasing |
| `bom.csv:103`, `unplaced.csv:15` | `-9.6V` | one space |
| `bom.csv:62`, `panel-led/bom.csv:2` | `97mm`, `13mm spare` ×4 | one space, four times |
| `key-switch-network/bom.csv:4-5` | `~5.7us`, `~125us`, `44x` | CSV vs markdown spelling |

`CLAUDE.md` says `sensor-full-scale` was spelled seven ways. It is now nine.

### And three that no pattern could ever catch

- `plate-thickness` is **settled at 1.20 mm**; `key-layout.yaml` says
  `plate_thickness: null` and `cluster-boards.md:167` says it is "still open",
  citing `key-layout.yaml` as its authority. The citation chain is intact and
  both ends agree — with each other. **The register protects a wrong number
  and cannot protect a missing one.**
- The path map is stale in 22 of 287 rows and misses 143 tracked files, 95 of
  them the `hardware/` files Phase B created after the map was written.
  `CLAUDE.md` §6 sends readers there to resolve stale paths.
- `hardware/README.md` has **zero inbound links** from anywhere in the corpus.
  The page explaining the whole `<board>/<circuit>/` scheme cannot be reached
  from the front door.

## Engineering findings the wave surfaced

Not caused by the restructure, and not for it to fix — but now on the record.

**The strongest convergence: three cold agents, one topology.** A5, A4 and C3
independently found that both Interfaces tables say the umbilical branch is
taken *before* the entry diodes, while the drawing, the qty-3 diode row, the
qty-4 bead row and the **settled** `ferrite-bias-impedance` all require it
*after* `D2`. The same sentence was copied into both pages during the split,
so cross-checking the two ends returns agreement. **Needs a decision, not an
edit.**

**From banked documents, four numbers that block or mislead:**
- `DAC8568CIPW` **does not exist** — zero occurrences in its own datasheet.
  The C grade orders as `DAC8568ICPW`. The transposition is in the BOM, ADR
  0006 twice, `MANIFEST.csv`, and the banked file's own name.
- ADR 0004 reads the DAC's input threshold off the wrong row: `0.7 × AVDD`
  applies below 4.5 V; this rail is 5.21 V, so it is **3.26 V, not 3.65 V**.
- The strips' 20.2 mA/LED has nothing behind it; the WS2815 datasheet says
  **45 mA/LED**. ADR 0014 says so itself — 284 lines below the table still
  using the low figure, which is the numerator of the whole thermal budget.
- The carrier's 74AHCT125 has a guaranteed worst-case VCC of **4.25 V**
  against a 4.5 V minimum, from three banked documents whose numbers appear
  nowhere in the corpus.

**Two netlist shorts in the tables written to prevent netlist shorts:** the
DAC's `SCLK`/`DIN`/`SYNC` has two declared drivers in byte-identical rows,
and `bus +5V` has two mutually exclusive sources.

**`CABLE-UMB` specifies no conductor gauge** while three derivations compute
from 24 AWG — and the row's own well-argued insistence on *stranded* is
exactly what makes 26/28 AWG likely, at 1.6–2.6× the assumed resistance.

## What I would do before this replaces `main`

In order, and none of it is large:

1. **Fix the four checks above**, then re-run the whole wave's mechanical
   claims against the fixed tooling. Items 1–5 on C2's list are one-to-four
   line edits.
2. **Add the check nobody has**: assert that a value appearing in three or
   more corpus files has a register entry. Every defect in the escape table
   above is downstream of a number restated rather than cited, and C6 notes
   it is mechanically detectable from files the checker already reads.
3. **Re-run the conservation proof with a head comparison** before trusting
   any "0 REAL GAPS" from the design wave.
4. **Link `hardware/README.md` from the front door.**
5. Adjudicate the umbilical topology. Everything else is a normal fix.

## The honest summary

This wave found roughly ninety findings across twenty-two slices and I
verified twenty-four of them by hand. **Six of the verified defects are mine,
introduced or left by this restructure**, and the worst of them are in the
checks I wrote to prevent exactly this. `CLAUDE.md`'s first paragraph says
the failure "is not carelessness that more care fixes — it has happened
inside commits whose own message was about it." This session produced a
docstring that names a case it does not catch, and a fail-open inside the fix
for a fail-open, six lines apart, in one function, in one commit.

**The tree is better than what it replaces and should land. The green light
on it should not be believed until items 1–3 are done.**
