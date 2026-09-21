# LED strip drive — decision history

**Past tense only.** Every live value lives in
[`led-strip-drive.md`](led-strip-drive.md), `config/figures.yaml` or
`hardware/bom.csv`. If a number here is still true, it is in the wrong file.

This is the circuit's superseded shelf — the same convention
`docs/decisions/README.md` runs at project scope, one level down. Nothing is
deleted from it: a deleted superseded value stops warning the next person, and
the refutation wording is what lets `tools/check-staleness.py` tell a quoted old
value from a live one, so the two always travel together.

---

## The WS2815 threshold and `BI` — closed 2026-09-21

*Moved verbatim from `carrier.md`'s `Still open` list, 2026-09-21, where it was
already struck through as closed. The argument it closes on is live and is in
[`led-strip-drive.md`](led-strip-drive.md); "§5" is that page.*

- ~~**The WS2815's data threshold, and whether `BI` needs driving**~~ —
  **closed 2026-09-21** against the datasheet, §5. 5 V logic is correct,
  `BI` is grounded at the head, two gates stay spare.
