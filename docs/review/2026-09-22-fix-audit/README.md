# Fix-audit wave — method

**Opened 2026-09-22**, against the fix batch `0e68f25~1..HEAD` — the work done
after the pre-merge wave closed, and before this branch replaces `main`.

## Why this wave exists

The pre-merge wave reviewed the tree **as it was before the fixes**. Since
then **85 corpus files changed, +2,684 / −1,228 lines**, and nothing has
looked at any of it. The only eyes on that diff belong to whoever wrote it.

`CLAUDE.md` says, of what makes these waves work:

> **At least one agent auditing the previous round's fixes.** Every wave has
> found that the last round's fixes were partial.

Nine waves. Every one. This wave assumes the same about the tenth.

There is specific reason to. In the space of one session the fixer:

- broke a freshly-written rule **three times in twenty minutes**, writing
  `forbidden` patterns that fired on sentences that are true;
- twice built a commit with `git add -A` and swept another agent's
  half-finished work into it;
- cited a tracked figure by an id that did not exist;
- and wrote a `derivation` string that broke the YAML because the text was
  appended after the closing quote.

Every one of those was caught. The question this wave answers is what was not.

## The rules

- **Cold.** No agent may read anything under `docs/review/**` — not this
  file's siblings, not the pre-merge wave, not `VERIFIED.md` or `STATUS.md`.
  Agreement between agents that cannot see each other is evidence; agreement
  with a document they just read is not. **You may read the git log and
  `git diff`** — the change is the subject.
- **Slice by fact domain, not by file.** A defect is one fact across five
  files; slicing by file gets five agents reporting it from one side.
- **Provenance on every claim** — `[repo] path:line`, `[calc]` with the
  arithmetic shown, `[datasheet]` with document and page, `[test]` with the
  command and its output, `[from memory]`. An unmarked claim is a defect in
  the report.
- **A finding is a claim.** Several findings in this project's history have
  been wrong. Say what would settle an uncertain one.
- **Report, do not fix.** The corpus is frozen again for the duration.
- **Two questions, not one.** Is the fix *correct*? And is it *complete* —
  did it land everywhere the value it changed is read? The second is the one
  every previous wave found wanting.

## Reading a PDF in this container

`pdftotext` is not installed and `pypdf` raises a `pyo3` panic from the system
`cryptography` binding. Either stub those modules before importing pypdf, or
use `pip install pymupdf`, which is the better route and also renders.
`docs/reference/repo-maintenance.md` §3 has both, and the limits of each.

## The slices

**The tooling** — D1–D5. The checks were rebuilt; five fail-opens were known
and a sixth was found in the conservation proof. Find the seventh.

**The register** — D6–D8. Nine owners repointed, patterns added *and removed*,
two figures newly tracked.

**The BOM** — D9–D11. Eighteen rows left `unplaced.csv`, two fragments were
created, and an order code changed.

**The content** — D12–D15. Six ADRs, a reversed mechanical conclusion, and a
latency budget rebuilt to close.

**The tables and the graph** — D16–D17. Nets renamed in the transcription
source while the drawings kept the old names.

**Cross-cutting** — D18–D20, including the mandatory conservation check and
the mandatory audit of completeness.

`VERIFIED.md` records what was checked by hand afterwards and where an agent
was wrong. `STATUS.md` records what actually landed.
