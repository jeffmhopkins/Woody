# Review wave 2026-09-27 (round 2) — the left-hand key board after its fixes

**Goal (owner):** the left-hand key board is the project's worked example. This
round checks what changed after the first wave closed
(`docs/review/2026-09-27-lh-key-board/`, closed at `383116e`):
- **The register:** now the SN74HCS165, which moved the key timing figures.
- **The standoff:** MSO4-M2-3 with a washer, which sets the key boards' depth.
- **The owner's rule:** every key's network sits the same way round its switch.
- **The traces and silkscreen:** reworked, including the new top-side silk.
- **The first wave's fixes:** whether they held.

**Revision measured:** `eebcdfb` on `claude/car-instrument-cad-design-xvqwv2`.
**`tools/` is frozen for the wave.** Slices may run the tools, and may copy the
board to a scratch directory and break it there, but they change nothing in the
repository except their own report. The orchestrator commits nothing under
`tools/`, the corpus or the board until every report is in.

## Method (CLAUDE.md, "Review waves")

- **Cold.** No slice reads `docs/review/**` except this README. The first wave's
  reports and ledger are off limits. Agreement between slices that cannot see
  each other is evidence.
- **Sliced by fact domain, not by file.**
- **Provenance on every claim:** `[repo path]`, `[calc]` with the arithmetic,
  `[datasheet path, page]`, `[web URL]`, `[run: command]`, `[from memory]`.
- **Node-indexed findings** against a reference, a net, a figure or a rule.
- **Numbered** `R<slice>-<n>` with a severity (high / medium / low / advisory).
  `python3 tools/extract-findings.py docs/review/2026-09-27-lh-key-board-r2`
  builds the ledger. `VERIFIED.md` and `STATUS.md` answer each finding by id.

## Slices

| Slice | Fact domain |
|---|---|
| R1 | The register and the key timing: SN74HCS165 against its banked datasheet; `key-release-time`, `key-press-time` and every page that cites or restates them; the chain's timing, ESD and family arguments |
| R2 | The standoff, washer and depth: MSO4-M2-3, the washer, `switch.pcb_below_seat` / `thumb_pcb_below_seat`, the depth rules and tolerance stack, the screw, the BOM rows, ADR 0020 and its fallback, the README assembly steps, the PCB keep-out |
| R3 | The PCB as a made thing: the network pattern, routing quality, DRC, the silkscreen on both sides, the test pads, `fab/` against JLCPCB's banked limits |
| R4 | Ordering and sourcing: the JLC BOM/CPL/hand list, part numbers against the sheets, stock and US sources, the README's ordering section |
| R5 | Fix audit: every commit after `383116e`, for the four recorded shapes (a fix that did not reach the pages citing it; a fix whose explanation restates the wrong value; a count that moved under the sentence stating it; a conclusion its own corrected number refutes) |
| R6 | The tools changed today (`tools/pcb.py`, `tools/pcb_route.py`): does each check and each layout rule do what `docs/reference/tooling.md` and the board README say, shown by breaking scratch copies |
