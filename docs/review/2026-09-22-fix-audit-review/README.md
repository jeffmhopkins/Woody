# Round 2 — a review of the fix-audit wave

**Opened 2026-09-22.** The fix-audit wave produced twenty reports and roughly
a hundred findings, and every one of them is a **claim**. This round audits
the auditors.

`CLAUDE.md` is explicit about why:

> Findings are claims. Several have been wrong, and one was wrongly marked
> disputed by me — **which is worse, because a wrong finding gets caught by
> the next reviewer while a finding filed as handled does not.**

## What is different about the cold rule here

Round 2's **subject** is `docs/review/2026-09-22-fix-audit/**`, so you read it.
What you may **not** read is:

- any other file in `docs/review/2026-09-22-fix-audit-review/` — your siblings
  in this round;
- any earlier wave (`2026-09-20-*`, `2026-09-21-*`).

Agreement between agents that cannot see each other is evidence. Agreement
with a sibling you just read is not.

## One thing you must know before you trust any measurement

**The checker was broken while the wave ran.** Two defects, both confirmed:

- `check_owners` picks its comparison token with `sorted(set(...), key=len)`,
  so ties break on set iteration order. Ten identical runs with a real
  violation live gave **6 PASS / 4 FAIL**.
- The refutation exemption covers ~48 % of the corpus, and **all 68
  forbidden-pattern matches are currently exempted** — the live list is empty.

So any finding of the form "the checker reports PASS on this" was measured
with an instrument whose verdict is not reproducible. Where a report leans on
a tool run, re-run it yourself, several times, and say so.

## The rules, unchanged

- **Provenance on every claim** — `[repo] path:line`, `[calc]` with the
  arithmetic, `[datasheet]` with document and page, `[test]` with the command
  and its output.
- **Report, do not fix.** The corpus is frozen.
- **A finding is a claim**, including the findings you are auditing and the
  ones you file about them.
- **Say when a report was right.** A slice that only lists errors gives no way
  to tell a careful report from a lucky one.
