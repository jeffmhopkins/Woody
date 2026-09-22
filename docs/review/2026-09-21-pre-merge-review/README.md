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

## Roster

Twenty ran concurrently; two were queued behind the concurrency ceiling and
launched as slots freed.

### The signal chains and the physics

| ID | Slice |
|---|---|
| **A1** | The breath chain end to end, as one transfer function and one error budget |
| **A2** | The pitch channel, and whether it can actually be tuned |
| **A3** | The four mod channels and the one reference they share |
| **A4** | Module power: rails, the load switch, and what powers up in what order |
| **A5** | The instrument end of the power system, and the cable between |
| **A6** | The key chain, from finger to firmware |
| **A7** | The digital path from MCU to DAC output register |
| **A8** | Grounds and return paths across three boards and the cable |
| **A9** | Lighting, and every route by which it reaches an analog output |
| **A10** | Everything physical — does it fit, and can it be built? |

### The cross-cutting registers

| ID | Slice |
|---|---|
| **B1** | `config/figures.yaml` itself — all 35 entries, derivation by derivation |
| **B2** | Can this BOM actually be ordered and built? |
| **B3** | Every number claimed to be read off a banked document, re-read |
| **B4** | Do the fourteen ADRs still describe what is drawn? |
| **B5** | What the hardware requires of firmware, and whether firmware knows |
| **B6** | Is the plan buildable in the order it states? |

### The restructure itself

| ID | Slice |
|---|---|
| **C1** | Audit of this round's own fixes — the rule every wave has vindicated |
| **C2** | Break the tooling. Five fail-open holes are known; find the sixth |
| **C3** | Failure injection — what happens when things go wrong |
| **C4** | The `## Interfaces` tables, the only new content, written by eight agents in parallel and never checked against each other |
| **C5** | Can someone who has never seen this repository use it? |
| **C6** | The gaps — what the design needs that no document owns |

## Why these slices and not others

Four of them exist because of a specific property of *this* change rather
than of the design:

- **C4** audits the one exception to the content freeze. Eight agents wrote
  those tables independently, the dependency graph was seeded from them, and
  a PCB netlist would be transcribed from them. If two ends disagree about a
  net, that is a short.
- **C1** exists because every wave this project has run found the previous
  round's fixes partial, and today made roughly forty commits claiming fixes.
- **C2** is a second adversarial pass that may not see the first one's
  findings, because a reviewer steered by a prior list checks that list.
- **C5** stands in for a newcomer. Everyone who has looked at this tree
  already knew where everything was, so nobody has tested the thing the
  restructure was *for*.
