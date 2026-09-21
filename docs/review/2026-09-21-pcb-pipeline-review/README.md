# PCB pipeline review — 2026-09-21

**Subject:** `docs/reference/pcb-pipeline.md`, the proposed headless
schematic-to-fab pipeline. Nothing has been built; this reviews the *plan*.

## Why this wave is different from the other three

The previous waves reviewed a **design**. This reviews a **procedure that makes
claims about tools**, and nearly every one of those claims is falsifiable
against source code rather than argument.

That changes the standard of evidence. `gitlab.com` and `github.com` are
reachable from this sandbox and `pypi.org` is in the proxy's bypass list, so:

| Claim about | Verify against |
|---|---|
| `kicad-cli` commands and flags | `gitlab.com/kicad/code/kicad` — the CLI source |
| `pcbnew` Python API | the same repo's SWIG bindings |
| Freerouting CLI and behaviour | `github.com/freerouting/freerouting` |
| SKiDL | `github.com/devbisme/skidl`, and the sdist from pypi |
| Anything else | download it and read it |

**A claim checked against source is a finding. A claim checked against memory is
a guess, and must be marked as one.**

## Method

- **Cold.** Reviewers may not read this directory or any prior review
  directory. Agreement between agents that cannot see each other is evidence;
  agreement with something they just read is not.
- **Sliced by technical domain**, not by section of the document. The same
  defect usually shows up in three stages at once.
- **Findings are claim-indexed** — quote the sentence being challenged, then
  give a verdict.
- **Verdicts are explicit:** `CONFIRMED` / `REFUTED` / `UNVERIFIABLE` /
  `MISSING` (something the plan should say and does not).
- **Provenance on every claim:** `[source]` with a repo path or URL, `[test]`
  with the command and its output, `[calc]` with the arithmetic, `[from
  memory]`. An unmarked claim is a defect in the report.
- **Falsify, do not extend.** The job is to find what breaks, not to add
  features.

## Slices

| | Domain |
|---|---|
| P1 | `kicad-cli` command surface |
| P2 | `pcbnew` Python API, and how a netlist gets into a board headless |
| P3 | Specctra round trip and the locked-track strategy |
| P4 | Freerouting in practice |
| P5 | SKiDL end-to-end viability |
| P6 | Headless environment and reproducibility |
| P7 | Fab deliverables — what an actual fab needs |
| P8 | The three-ground pour as a KiCad implementation |
| P9 | Alternatives and prior art |
| P10 | Audit against this repo's own design corpus |
| P11 | Layout rules — what is right, and what is missing |
| P12 | Failure modes, determinism, and re-runnability |

`VERIFIED.md` records what was checked by hand afterwards and where an agent
was wrong.
