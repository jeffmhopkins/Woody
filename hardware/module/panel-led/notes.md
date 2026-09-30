# Panel LED — decision history

**Past tense only.** Every live value lives in
[`panel-led.md`](panel-led.md) or `hardware/bom.csv`. If a number here is still
true, it is in the wrong file.

This is the circuit's superseded shelf, on the same convention
`docs/decisions/README.md` runs at project scope. Nothing is deleted from it: a
deleted superseded value stops warning the next person, and the refutation
wording is what lets `tools/check-staleness.py` tell a quoted old value from a
live one, so the two always travel together.

---

## The panel LED — superseded, and its job has changed

*Moved verbatim from `power-entry.md`, 2026-09-21. The sentence this block ran
into — the one that names the circuit that replaced it — stayed on the page, in
`## The circuit`.*

**This whole section described a circuit that no longer exists.** It put
the LED and the level shifter's `OE` pins on one node — the presence
comparator's open collector — with `R-OE-PU` 10 kOhm and `R-LED` 820 Ohm
pulled to bus +5 V. The comparator is deleted, `OE` is tied low and
permanently enabled, and neither `R-OE-PU` nor `R-LED` ever had a BOM row.

The bug the old section found was real — pulling a 5 V part's input toward
12 V through an LED resistor — and it is moot now that nothing shares that
node.

---

## On the analog +12 V rail — superseded 2026-09-30

*Moved from the page, 2026-09-30, when the LED moved to the load switch's
output.*

From 2026-09-21 the LED hung on `MODULE ANALOG +12V` through
`R-LED-PANEL`. **That rail is live whenever the rack is**, so the LED was lit
in every one of the latching faults — hot-plug, LED-boot overcurrent, a
current-limited start, a soft short — and the one indication the design has
for "the load switch has latched" indicated nothing. The review proposed
driving it from `TIMER` or `GATE`, pending the datasheet read that
`C-TIMER` also needed. The datasheet, once banked, showed neither node holds
a "latched" level; the output does.
