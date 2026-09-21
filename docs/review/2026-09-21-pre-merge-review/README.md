# Pre-merge review wave — method

**Opened 2026-09-21**, against the restructure branch before it replaces
`main`. Twenty cold agents.

## Why this wave exists

The restructure moved every path in the repository, split eight schematic
pages into twenty-three circuit directories, made two files generated, and
added five checks. Two cold reviewers have audited the *move* — conservation
of content, and the tooling. **Neither audited the engineering.**

Every prior wave found that the last round's fixes were partial. This one
assumes the same about the restructure.

## The rules, unchanged from every prior wave

- **Cold.** No agent may read `docs/review/**` — not this file's siblings,
  not the design wave, not the two audits already done. Agreement between
  agents that cannot see each other is evidence; agreement with a document
  they just read is not.
- **Slice by fact domain, not by file.** The defect is one fact across five
  files. Slicing by file gets five agents reporting one defect from one side.
  These slices follow signal chains and cross-cutting properties, and most of
  them deliberately span several directories.
- **Provenance on every claim** — `[repo] path:line`, `[calc]` with the
  arithmetic shown, `[datasheet]` with the document and page, `[web]` with
  the URL, `[from memory]`. An unmarked claim is a defect in the report.
- **Node-indexed findings**, filed against a circuit node, a net or a BOM
  reference rather than a file and line, so two agents reporting one defect
  from opposite ends collide visibly.
- **A finding is a claim.** Several findings in this project's history have
  been wrong. Say what would settle an uncertain one; a confident wrong
  finding is worse than an uncertain right one, because the next reader
  cannot tell.
- **Report, do not fix.** The corpus is under a content freeze until the
  merge decision.

## The slices

**The signal chains and the physics** — A1–A10 follow current and signal
rather than directories.

**The cross-cutting registers** — B1–B6 audit the things every circuit shares:
the figure register, the BOM, the banked datasheets, the ADRs, the firmware
contract, the roadmap.

**The restructure itself** — C1–C4, including the mandatory audit of this
round's own fixes and a second adversarial pass on tooling that the first
pass's findings cannot be used to guide.

`VERIFIED.md` records what was checked by hand afterwards and where an agent
was wrong. `STATUS.md` records what actually landed versus what was reported.
