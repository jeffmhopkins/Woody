# VERIFIED — how the r2 findings were checked, and where someone was wrong

`STATUS.md` answers every id in `FINDINGS.csv`. This file says how, and
separates what the orchestrator re-ran from what only a fixing agent ran.

## Re-run or re-read by the orchestrator

- **The mount's figures** (R2-4, R4-2, R4-9, and the new standard), read on the
  banked drawings with `pdftotext -layout`:
  - Würth 9774020943R: bore 2.25 ±0.05, OD 4.35, L 2 ±0.1.
  - ISO 4762 M2×8: dk 3.80, k 2.00.
  - ISO 4032 M2 nut: s max 4.0, m max 1.6. **The table's e is a minimum (4.3)**,
    so the keep-out uses e at its largest, s max / cos 30° = 4.62 `[calc]`. The
    research agent reported 4.32 as the figure; that is DIN 439's e min, and
    neither minimum is right for a keep-out.
  - ISO 7092 washer: 4.50 −0.30 OD, 0.30 ±0.05 thick.
- **R3-1**: the decoupler's return path is 10.37 mm of track after the
  re-layout `[run: pcb.track_path_mm]`.
- **R3-2, R3-3, R3-4, R6-1, R6-4**: `pcb.py check` on the re-laid-out board
  reports 0 errors, and each check is one that fails on the defect. The
  breakages that prove each check fires were run in part 1.
- **The mount's rules** all print PASS in `mechanical/drc.echo`, apart from
  the tolerance-stack NOTE (3.3–3.7 against the 3.2–3.6 window). `clash.txt`
  has 0 clashes across 156 solids, the new plug, screw, spacer, washer and nut
  solids included. `section-kb-mount.png` shows the stack as modelled.
- **The first build of the new model failed its own bore rule** at both ends:
  1.125 mm of wood against 1.5. The side groove, not the cap slot, was the
  nearer cut. `kb_mount_inset` went to 3.4 and `kb_tail_margin` to 10.1. Both
  rules now report 1.525 mm.
- **Gates**: all re-run on the final tree (`STATUS.md` header).

## Only an agent ran, and how it can be trusted

- **The part-2 docs agent** (README, tooling.md, sheet MPN). Its gates were
  re-run by the orchestrator and passed. The orchestrator spot-checked the
  README's test-pad claim against `layout.yaml`. It was still wrong (R3-9),
  so the orchestrator fixed it.
- **The part-3 docs agent** (ADRs, unplaced.csv, pages). The orchestrator read
  ADR 0020 Amendment 2's superseded markers and re-ran the BOM and netlist
  gates. The agent listed the leftovers in files it was barred from:
  `body.yaml` sources, the `pcb.py` comment, and rule names that did not
  exist. The orchestrator fixed all of them.
- **The part-1 docs agent** (R1, R5 non-mechanical). Its dispositions were
  accepted at 425f536 after its gates passed. On R1-9, the agent's reading is
  that SPI modes 0, 2 and 3 capture the chain correctly and only mode 1 loses
  bit 0, and the page now says so. That was **not re-derived by the
  orchestrator**.

## Where a slice, an agent or the orchestrator was wrong

- **R5-11 rejected**: the superseded ADRs carry supersession headers, and
  their text is the record of what was decided then.
- **The orchestrator**, in the brief to the part-2 agent, gave `04.48` as the
  FFSD example. The derived length had already moved to 4.47 with the new tail
  margin. The agent caught it and cited the drc line instead.
- **The research agent** gave `kb_nut_e` 4.32 as ISO 4032's figure. It is
  DIN 439's minimum (above).

## Not checked

- US stock counts that the vendors' pages do not show (Fastener Express,
  BelMetric). They are marked [UNVERIFIED] in the rows.
- Whether Samtec builds a 0.01 in FFSD length.
- `hardware.kb_bore_wall` and `kb_plug_min_depth`: both are from memory, and
  M2 decides them on a scrap of the chosen wood.
