# Key switch network — decision history

**Past tense only.** Every live value lives in `key-switch-network.md`,
[`../cluster-boards.md`](../cluster-boards.md) or `hardware/bom.csv`. If a
number here is still true, it is in the wrong file.

This is the circuit's superseded shelf, on the convention
[`../../module/pitch-stage/notes.md`](../../module/pitch-stage/notes.md) sets.
Nothing is deleted from it: a deleted superseded value stops warning the next
person.

---

## Why `R-KEY-PU` became 2.2 kΩ — moved from the BOM row, 2026-09-26

*Moved out of the `R-KEY-PU` notes cell under CLAUDE.md's cut line: a BOM
cell tells a builder what to do, and this is what someone used to think.*

The pull-up started at 10 kΩ, which was fine for a register beside its
switch. It went to 2.2 kΩ when the tail-register draft ran each key node
265 mm down an **uncoated** loom to a register at the tail, and a stiffer
pull-up was wanted against what that loom could couple in. ADR 0001 then moved
the registers back beside their switches — on the cluster boards then, on the
main board and the two key boards since ADR 0017 — and that reason went with
the loom. The 2.2 kΩ was kept anyway, as cheap insurance for a humid,
breathed-into cavity with open switch contacts; the live trade it now costs is
on `key-switch-network.md`.

The row also recorded that the first cluster-board draft left the free bits
(then bits 22, 23 and 31) floating — the ADR 0001 fix-6 fault — which is why they carry a
pull-up each and the row buys more pull-ups than there are networks.
