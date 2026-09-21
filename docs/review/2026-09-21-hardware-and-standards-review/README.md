# Hardware and standards review — 2026-09-21

**20 agents.** The third review wave, and the first to cover every board in the
instrument. It ran after the last schematic was drawn, so for the first time
the whole design is on paper and can be checked as one thing.

## Why this wave exists

The two earlier waves each reviewed a moving target. The 2026-09-20 cold review
predated the module schematics; the 2026-09-21 schematic review predated the
carrier rewrite, the cluster boards, and six decisions taken afterwards. This
wave is the first with a stable corpus: six module pages, two controller pages,
14 ADRs, a 119-row BOM and a key layout, all current.

It has a second axis the earlier waves did not. Half of this project's module is
a Eurorack module, and Eurorack has published standards and a large body of
published open-hardware schematics. **Six of the twenty agents do nothing but
compare this design against that field.** Being internally consistent and being
conventional are different properties, and only one of them was ever being
checked.

## The rules every agent ran under

These are method, not bureaucracy — each one exists because its absence cost
this project something.

1. **Cold.** No agent may read `docs/review/**` or `docs/research/**`. Prior
   waves and the prior-art research are off limits. An agent that reads them
   reproduces their conclusions instead of testing them, and the whole point of
   a second opinion is that it is second.
2. **Read-only.** No agent edits any file but its own report. Fixes are applied
   afterwards, by hand, one at a time, with the reasoning visible.
3. **Provenance on every claim.** `[repo] <file>`, `[calc]` with the arithmetic
   shown inline, `[web] <url>` with the URL always given, or `[from memory]`.
   An unmarked claim is a defect in the report, not a finding.
4. **Node-indexed, not document-indexed.** Findings are filed against a circuit
   node or a BOM reference — `R-KEY-PU`, the `BREATH` net — never against a file
   and line. The same defect usually lives in one node and three documents, and
   only node-indexing catches the copies.
5. **Arithmetic or it did not happen.** A number without its derivation is not a
   finding.

## The twenty

### A — cold design review, by subsystem

| | Scope |
|---|---|
| `A1` | Cluster boards — the register, the key network, the 32-bit allocation, the marker |
| `A2` | Carrier analog front end — sensor, reference, buffers, ADC |
| `A3` | Carrier power — LC damping, the two regulators, thermal, diode-OR |
| `A4` | Carrier digital — GPIO assignment, two SPI hosts, LED data, reset states, recovery |
| `A5` | Module breath — the in-amp receive stage and the gain/offset output stage |
| `A6` | Module pitch and mod — the cents budget, jack-tapped feedback, ±10 V channels |
| `A7` | Module power entry — diodes, the LT1641 load switch, the LM317 |
| `A8` | Interconnect — all four looms treated as one subsystem, which nobody had done |

### B — against published Eurorack practice

| | Scope |
|---|---|
| `B1` | Mechanical and electrical standards: 8HP, the 16-pin header, current declaration, jacks |
| `B2` | Signal levels: 1V/oct convention, ±10 V modulation, output impedance, gate |
| `B3` | Power entry, against real published module schematics |
| `B4` | Output and jack protection, against real published module schematics |
| `B5` | Tethered links — who else sends power, analog and clocked digital down one cable |
| `B6` | Wind controllers — breath pressure ranges, moisture, response curves, note-on latency |

### C — falsification

Told to break a named claim, not to review. "This looks reasonable" is a failed
report; the verdicts are BROKEN, SURVIVES with proof, or UNDECIDABLE with the
measurement that would settle it.

| | Target |
|---|---|
| `C1` | The key chain and the 8-bit marker — find the corruption it misses |
| `C2` | The breath path — find the fault that produces a wrong or dangerous output |
| `C3` | Power sequencing — find the order that damages something or latches badly |
| `C4` | The shared 3V3 / ADC reference — was the accepted 3.2 LSB the right number |

### D — cross-cutting

| | Scope |
|---|---|
| `D1` | Arithmetic audit: recompute every number, and flag where two files disagree |
| `D2` | Consistency sweep: the staleness pattern that has bitten this project six times |

## What happens to the findings

Nothing automatically. Every finding gets read, checked, and applied or
rejected by hand — several findings in earlier waves were wrong, and at least
two fixes derived from a correct finding were applied to one document and left
stale in another, which is the failure `D2` exists to catch.
