# Review wave 2026-09-27 — the left-hand key board as the worked example

**Goal (owner):** make the left-hand key board "basically 100% complete —
documentation, project layout, part demand, routing, boards, products", so it
serves as the example every other board follows. This wave looks for anything
that stops it being that.

**Revision measured:** `d46a3b0` on `claude/car-instrument-cad-design-xvqwv2`.
**`tools/` is frozen for the wave.** Slices may run the tools but not change
them, and the orchestrator commits nothing under `tools/`, the corpus or the
board until every report is in.

## Method (CLAUDE.md, "Review waves")

- **Cold.** No slice reads `docs/review/**` except this README. Agreement
  between slices that cannot see each other is evidence.
- **Sliced by fact domain, not by file.** Each slice follows its facts across
  every file they appear in.
- **Provenance on every claim:** `[repo path]`, `[calc]` with the arithmetic,
  `[datasheet path, page]`, `[web URL]`, `[run: command]`, `[from memory]`.
  An unmarked claim is a defect in the report.
- **Node-indexed findings.** A finding is filed against a reference (`R-KEY-SER-LH1`),
  a net (`/CHAIN_SCK`), a figure or rule (`boards.chain_plug_proud`,
  drc.echo "key-chain ribbon length (derived)") or a file's fact, not only a
  line number.
- **Numbered:** `K<slice>-<n>`, each with a severity (high / medium / low /
  advisory). `python3 tools/extract-findings.py docs/review/2026-09-27-lh-key-board`
  builds `FINDINGS.csv` from the reports. `VERIFIED.md` answers the findings
  by id, and `STATUS.md` records what landed.
- **One slice audits this round's own fixes** (K8), for the four recorded
  shapes: a fix that did not reach the pages citing it; a fix whose own
  explanation restates the wrong value; a stated count that moved under the
  sentence stating it; a conclusion its own corrected number refutes.

## Slices

| Slice | Fact domain |
|---|---|
| K1 | The circuit: the 74HC165 at 3.3 V, the key networks' values and timing, the marker and free bits, decoupling, test points, against the banked datasheets |
| K2 | The chain across the ribbon: every pin from the main board's J-CHAIN to the key board's, the cable option, the header and socket orientation, against the banked Samtec prints |
| K3 | The PCB: layout, routing, pours, clearances, silkscreen, and the fabrication outputs, against KiCad's DRC and JLCPCB's banked limits |
| K4 | Parts and assembly: the sheets' part numbers against the BOM rows' requirements and the datasheets, the JLC BOM/CPL/hand list, quantities, sourcing |
| K5 | The board in the body: outline, standoffs, screw heads, plate window, pin protrusion, the header stack and the ribbon's hairpin and service length, against the body CAD's derivations |
| K6 | The documentation: the board README, ADRs 0017/0019/0020, tooling.md, the circuit and interface pages, against the data they describe and CLAUDE.md's rules |
| K7 | Reproducibility: can the board, its renders and `fab/` be regenerated from the sources by the documented commands, and does every check hold what it claims? |
| K8 | Fix audit: today's fixes, for the four recorded shapes |
