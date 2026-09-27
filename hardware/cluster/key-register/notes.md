# Key register — decision history

**Past tense only.** Every live value lives in `key-register.md`,
[`../cluster-boards.md`](../cluster-boards.md) or `hardware/bom.csv`. If a
number here is still true, it is in the wrong file.

This is the circuit's superseded shelf, on the convention
[`../../module/pitch-stage/notes.md`](../../module/pitch-stage/notes.md) sets.
Nothing is deleted from it: a deleted superseded value stops warning the next
person.

---

## The pin map and the 3.3 V thresholds — closed 2026-09-21

*Moved verbatim from the `Still open` list of `cluster-boards.md`, 2026-09-21.
The `§Derivations` it points at is now the `### Derivations` of
[`../key-switch-network/key-switch-network.md`](../key-switch-network/key-switch-network.md);
`§1` is this circuit and `§2` is that one.*

- ~~**The 74HC165 pin map and its 3.3 V thresholds** (§1, §2).~~ **CLOSED
  2026-09-21.** The pin map is confirmed against Nexperia's Table 2 and the
  thresholds against onsemi's published 3.0 V row — see §Derivations. It did
  take rather more than five minutes, and it moved twice.

---

## 2026-09-27 — the part became the SN74HCS165

The register changed from the 74HC165 to TI's SN74HCS165 (ADR 0001's
amendment): Schmitt-trigger inputs with no input transition-rate limit,
because every key edge broke the plain HC165's limit
([`../key-switch-network/notes.md`](../key-switch-network/notes.md)). The pin
map above was confirmed against Nexperia's 74HC165 Table 2; the page now
cites TI's own pin table for the part bought, and it is the same pin for pin
(`SN74HCS165-ti-scls828a.pdf` p.3, Table 5-1). The load/shift function it
cited from Nexperia's Table 3 is TI's Table 8-1 (p.13), the same function.
The ESD figure the key-chain and cluster pages quoted was the 74HC165's HBM
over 2000 V (Nexperia p.1); the HCS165's is ±4000 V (TI p.4).
