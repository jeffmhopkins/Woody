# Umbilical load switch — decision history

**Past tense only.** Every live value lives in
[`umbilical-load-switch.md`](umbilical-load-switch.md) or `hardware/bom.csv`.
If a number here is still true, it is in the wrong file.

This is the circuit's superseded shelf, on the same convention
`docs/decisions/README.md` runs at project scope. Nothing is deleted from it: a
deleted superseded value stops warning the next person, and the refutation
wording is what lets `tools/check-staleness.py` tell a quoted old value from a
live one, so the two always travel together.

---

## The `VCC` UVLO maximum — refuted 2026-09-21

*Moved verbatim from the page, 2026-09-21. "The one refutation" is the `VCC`
UVLO row of `## The electrical picture, now read off the document` in
`umbilical-load-switch.md`, which is where the live value still is.*

The one refutation is small but it is the kind this project exists to catch:
**9.8 V was never in the document.** Nothing was derived from it, so nothing
downstream moves — but it had been sitting in a table headed "the rest of the
electrical picture" for a day, and a reader sizing the `ON` divider against a
9.8 V worst-case UVLO would have given away a volt of nothing.
