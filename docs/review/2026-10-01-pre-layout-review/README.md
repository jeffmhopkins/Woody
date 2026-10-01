# Pre-layout review wave — method

**Opened 2026-10-01**, before the boards are laid out and ordered. Nine cold
agents. The owner's word: finish the design up to the line before layout.

**Revision measured:** `REV` on `claude/car-instrument-cad-design-xvqwv2`.
**`tools/` is pinned at the same revision**: reviewers run the checkers from a
`git archive REV` copy, so a tooling commit landing while the wave runs cannot
change a slice's verdict. Work that lands on the branch after `REV` (main-board
routing, module photographs) is out of scope.

## Why this wave exists

Since the last wave (2026-09-27, the LH key board) the design took the
cassette, the isolated instrument supply (ADR 0027), the 13-LED row (ADR 0028),
the panel and its graphics (ADRs 0024, 0026), a four-layer main board with its
sheets, a hot-plug soft start, the SPI receiver, a gain change, the DAC
sequencing fix, a jack swap, and twenty SPICE decks. Every prior wave found the
previous round's fixes partial; assume the same of these.

## The rules, unchanged

- **Cold.** No agent reads `docs/review/**` except this README. Agreement
  between agents that cannot see each other is evidence.
- **Slice by fact domain**, not by file.
- **Provenance on every claim** — `[repo] path:line`, `[calc]` with the
  arithmetic, `[ds] file p.N`, `[sim] dir/run`, `[web] URL`, `[from memory]`.
  An unmarked claim is a defect in the report.
- **Node-indexed findings**: against a net, a refdes or a BOM row, not a file.
- **Findings carry ids** `A<slice>-<n>` (e.g. `A3-7`), each with a severity
  (blocking / high / medium / low / advisory), so `tools/extract-findings.py`
  can build the ledger.
- **A finding is a claim.** Say what would settle an uncertain one.
- **Report, do not fix.**
- **The four recorded shapes of a partial fix**, for every slice: a fix that
  did not reach the pages citing it; a fix whose own explanation restates the
  wrong value; a stated count that has moved under the sentence stating it; a
  conclusion that its own corrected number refutes.

## Roster

| ID | Slice |
|---|---|
| **A1** | The breath chain end to end: sensor, link, receive, shaper (R-RESP, curve), output stage — one transfer function, one error budget |
| **A2** | Pitch and the four mod channels: DAC8568, its reference, power-on state, the jack allocation after the swap, tuning |
| **A3** | Module power and sequencing: rack entry, PTCs, U-ISO (RPA20), the load switch, LOGIC_5V, DAC_AVDD, every rail's order up and down |
| **A4** | Instrument power, lighting and grounds: the umbilical's conductors, Q-INRUSH, the buck, the WS2815 row, return paths into the analog |
| **A5** | The digital link: SPI over Cat5 (R-SPI-SER, U-TVS-SPI, U-RX-MOD), MCU pin allocation, the key chain's timing, the firmware contract |
| **A6** | The instrument's boards physically: main and key board footprints, 3D models, mounts, the cassette stack, body CAD DRC and clash, JLC assembly fields |
| **A7** | The module physically: panel layout and art, jacks/pots/toggle/LED, the stack and standoffs, module-main and module-jack allocation |
| **A8** | The registers: `config/figures.yaml` entry by entry, the BOM's orderability (LCSC/JLC, CRLF, 11 columns), the datasheet bank, sim coverage |
| **A9** | Audit of this round's fixes (commits since `05a5bf3`, 2026-09-27), sliced by the four shapes above |

`VERIFIED.md` records what was checked by hand and where an agent was wrong;
`STATUS.md` what landed. `FINDINGS.csv` is generated.
