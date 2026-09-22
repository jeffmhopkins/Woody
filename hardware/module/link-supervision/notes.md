# Link supervision — decision history

**Past tense only.** Nothing in this directory is fitted at all;
[`link-supervision.md`](link-supervision.md) carries what the deleted parts
were and what restoring them would cost. If a number here is still true, it is
in the wrong file.

Nothing is deleted from this shelf: a deleted superseded value stops warning
the next person.

---

*Moved verbatim from `../digital-and-supervision/digital-and-supervision.md`'s
"Still open" list, 2026-09-21, when that page was split into three circuit
directories. The one supervision question that is still open went to
[`link-supervision.md`](link-supervision.md) instead.*

### Three bullets retired here, 2026-09-21

All three designed a part that this page deletes 55 lines above. Left standing,
an engineer working the open list would have sized an RC and a retrigger regime
for a footprint that is not on the board.

| Retired bullet | Why |
|---|---|
| A power-on reset RC on the '123's own `CLR` | There is no '123 |
| The retrigger arithmetic (~2400 retriggers per timeout, the 220 nF / 83 pC question, "a dedicated watchdog IC may be better") | Same — and if supervision is ever restored, the section above is where that work starts, not here |
| The presence tap point "needs a corrected `R-PRESENCE` row" | `R-PRESENCE` is in no BOM and never was. Nothing to correct |
| The comparator threshold "may sit inside the breath signal's own range" | True, and it is one of the **three reasons the comparator was deleted** (ADR 0004), not an open item about tuning it |
