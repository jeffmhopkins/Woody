# 2026-09-26 — netlist audit

## What this wave is for

Twenty-two `netlist.yaml` files and `hardware/nets.yaml` were written between
2026-09-22 and 2026-09-23 **by one agent, reading ASCII drawings**, and merged
as `#2`. They are now authoritative: `CLAUDE.md` and `hardware/README.md` both
say the drawing is a representation of the netlist, so where they disagree the
*drawing* is the defect.

`tools/check-netlist.py --strict` reports 0 problems, and that proves less than
it looks like it proves. It proves **internal consistency**: every refdes
exists in `bom.csv` with a matching value, every net has two endpoints or is
declared external, every pin is used exactly once, both halves of every
boundary net agree, no row is placed more times than the BOM buys, and every
`[REFDES value]` label in a drawing agrees with the netlist that owns the part.

**It cannot prove that a net is the net the page's derivation means.** Nothing
has checked a single topology choice. That is the largest unverified surface in
the repository and it is load-bearing.

This wave exists to check it.

## The revision, and the freeze

**Measured against `d1f0cb7`** (`main` at the time of writing).

**`tools/` IS PINNED.** No commit to `tools/` while this wave runs. The last
wave's orchestrator declared a freeze and then committed a tooling fix during
round 2, so two slices running one command twenty minutes apart got opposite
verdicts and every `[test]` baseline in twenty reports stopped reproducing.
`tools/` is not in `CLAUDE.md` §6's corpus, so that freeze held on the letter
and broke on the substance.

**Nobody injects a defect into the shared working tree.** A previous wave's
orchestrator told two slices to inject and revert in the tree ten cold
reviewers were reading; one of them patched `check-staleness.py` to skip link
checking, and the sabotaged checker reported PASS on a tree containing a broken
link it had just added. Six slices reported it independently and one finding
had to be withdrawn. **Clone to `/tmp/<slice>-clone` and inject there.**

## Method

- **Cold.** No slice may read any directory under `docs/review/`, including
  this one, including this file's neighbours. Agreement between agents that
  cannot see each other is evidence; agreement with a report they just read is
  not.
- **Sliced by claim type, not by circuit.** A wrong feedback node and a wrong
  ground return are different failures; one circuit contains both. Slicing by
  circuit would get twenty-two agents each reporting one defect from one side.
- **Provenance on every claim** — `[repo]` with the path, `[calc]` with the
  arithmetic shown, `[datasheet]` with the banked file and page, `[test]` with
  the command and its output, `[from memory]`. An unmarked claim is a defect in
  the report.
- **Node-indexed.** File a finding against a net name, a refdes, or a
  `<circuit>.<pin>` — not against a file and line.
- **Numbered ids**, `N<slice>-<n>`, one per finding, so `tools/extract-findings.py`
  can build the ledger and `VERIFIED.md` can close it *by id*. The last wave
  produced 377 findings and closed none by id, which is the measured reason ten
  consecutive rounds were judged partial.
- **A finding is a claim.** Several findings in this repository's history have
  been wrong, and one was wrongly marked disputed — which is worse, because a
  wrong finding gets caught by the next reviewer and a finding filed as handled
  does not. Say what would have to be true for yours to be wrong.

## The slices

| id | Claim type |
|---|---|
| N1 | Feedback and loop topology — every net that closes a loop |
| N2 | Grounds and references — which pin returns where, and what must not merge |
| N3 | Rails, supplies and decoupling, including every `rails:` declaration |
| N4 | Pin names and numbers against the banked datasheets |
| N5 | The deliberate holes — every `external_endpoints` entry |
| N6 | The master's directions against both pages of every boundary |
| N7 | Instance counts, `replicated:`, and which circuit places which part |
| N8 | The author's own claims — are the defects the commits announce real? |

`STATUS.md` records what landed. `VERIFIED.md` records what was checked by
hand, by id, and where a slice was wrong.
