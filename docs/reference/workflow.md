# Work tracking: issues, labels, milestones

GitHub issues on `jeffmhopkins/woody` track work and its status. They are
**never where a design fact lives**: an issue names the `config/figures.yaml`
key, the circuit node or the owning page, and does not quote the value. The
corpus (CLAUDE.md §6) stays the only place a number is stated.

## Kinds

One template each in `.github/ISSUE_TEMPLATE/`.

| Kind | For | Closes when |
|---|---|---|
| `kind: feature` | New capability | Its "done when" check passes on the integration branch |
| `kind: task` | Defined work, usually under a feature or review | Its "done when" holds |
| `kind: review` | A review's findings, one id each | Every id is fixed, refuted with evidence, or split out into its own issue |
| `kind: defect` | Something in the corpus is wrong | Fixed, with the check that now catches it |

A review issue and a `docs/review/<wave>/` directory are the same thing when
both exist: the wave's `FINDINGS.csv` ids are the issue's checklist, and both
close by id, never in prose.

## Labels

Every open issue carries exactly one `kind:`, one `status:` and at least one
`area:` label. An open issue without a `status:` is a tracking defect.

- `status: queued` — accepted, not started.
- `status: in progress` — someone is working on it; the latest comment says what.
- `status: needs owner decision` — work is done up to a choice that has been
  put to the owner **in the working chat**; the issue comment names the choice
  and says it was asked there, and is updated with the answer.
- `status: gated` — waits on a milestone, which the issue names.
- `area:` module, controller, key-boards, mechanical, sims, tooling, docs, bom.

## Milestones are build gates

| Milestone | Means |
|---|---|
| Design freeze | Every schematic, sim and decision closed; nothing open changes a netlist |
| Rev A layout | Every board routed, `tools/kicad.py check` clean, mechanical fit pass against the body CAD |
| Rev A order | Fab outputs, BOM and parts ordered |
| Bring-up | Assembled, rails checked, E-series bench tests passed |
| Finish | Assembly guide, carry case |

Gates may be added when the work needs one (for example a Rev B); add it on
GitHub and to this table in the same change.

"What is left before we order" is the open list of the first three milestones.

## Commits, not pull requests

Work goes straight to the integration branch. Every push, to any branch, is
checked by CI, which reports and does not block
([`tooling.md`](tooling.md), *CI*); look at the run before calling a push
done. Each commit that does work for
an issue names it in the subject or body (`#9 G2: …`, `Refs #7`). A commit that
finishes an issue says `Closes #n` only when the push really completes it;
otherwise the issue is closed by hand with its outcome comment.

## The loop

1. **New work asked for in chat becomes an issue before it starts.**
   **Decisions are not issues.** They are asked and answered in the working
   chat, recorded in an ADR or ADR amendment with the owner's words quoted,
   and the issue that needed them is commented with the answer and the ADR.
2. **Starting:** set `status: in progress` and comment with the plan.
3. **Finishing:** comment with the outcome **per finding id or checklist
   item**, with commit links; then close, or move to
   `status: needs owner decision` after asking the choice in chat.
4. Comments end with the Claude Code attribution footer.

Closed issues are history, like `docs/review/`: not edited afterwards. A
later correction is a new comment or a new issue.
