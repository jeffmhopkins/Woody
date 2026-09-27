# 0019 — The KiCad sheets are the source of truth

**Status:** Accepted. Decided by the owner, 2026-09-27. Migration in progress:
the key-board circuits and both key boards are done (see *Consequences*).

## Context

Every circuit in `hardware/` was a Markdown page with an ASCII drawing and a
hand-written `netlist.yaml`, which `CLAUDE.md` made authoritative for
connectivity. KiCad sheets arrived on 2026-09-27 as **generated pictures** of
those netlists (`tools/sch.py`), then as whole key boards assembled from the
circuits (`tools/board.py`).

That left the thing a board is actually made from — a KiCad schematic, then a
PCB — downstream of YAML. Every change would have to be made in YAML and
regenerated, and anything done in KiCad (placement, a part moved, a footprint)
would be overwritten on the next build.

## Decision

**The KiCad sheets own the design.** (Owner: "it's probably important that
these KiCad schematics actually be the source of truth of all the things.")

- **Scope: connections and parts.** A circuit's `<circuit>.kicad_sch` owns
  every connection and each part's identity as KiCad fields: `Row` (the BOM
  row it buys from), `Pins` (the pin map, with KiCad's own pin names where it
  names them), `Pins_source` (the datasheet page that proves the map) and
  `Note`. Ports are hierarchical labels, carrying their direction, peer and
  register figure as fields. The design prose and derivations stay in the
  circuit's `.md` page, which is where arguments read and review best (the
  owner's choice over moving prose onto the sheet).
- **Replicated circuits are hierarchical sheets.** A circuit is drawn once;
  a board places it as a sub-sheet once per instance — a key board places
  the register once and the key network once per key. KiCad gives each
  instance its own references (`R-KEY-PU-RH1`). Change the circuit once and
  every instance follows (the owner's choice over a flat sheet per board).
- **Boards are KiCad projects** under `hardware/boards/`. Their flattened
  netlist, `board-netlist.yaml`, is what a PCB is laid out from.
- **Everything else the repository reads is exported.** `netlist.yaml` is
  written from the sheet by `tools/kicad.py export`, so
  `tools/check-netlist.py`, `hardware/nets.yaml` and the BOM checks keep
  running unchanged — on the sheet's truth. `tools/kicad.py check` fails on
  an export or a render that no longer matches its sheet, the same contract
  `tools/cad.py` keeps for the body.

## Options considered

- **Keep YAML authoritative, sheets generated.** The state before this ADR.
  Rejected: KiCad work would be overwritten, and the board would still be
  made from something that is not the source.
- **Connectivity only in KiCad, parts in the BOM fragments.** Smaller, but
  part facts in two places. Not chosen.
- **Prose on the sheets too.** Long arguments read badly on a sheet and
  review badly in a diff. Not chosen.
- **A flat sheet per board.** Simpler files, but a change to the key network
  would be made six times on one board and nineteen in all. Not chosen.

## Consequences

- **Migrated, 2026-09-27:** `cluster/key-register`, `cluster/key-switch-network`,
  `cluster/key-marker-and-bits`, and the boards `key-board-rh` and
  `key-board-lh`. **Proved, not assumed:** each circuit's exported netlist
  was compared part by part and net by net with the hand-written one it
  replaces, and each KiCad board's flattened netlist with the board assembled
  by the retired `tools/board.py` — identical, and KiCad's ERC over both board
  hierarchies is clean.
- **One circuit changed shape to fit.** `key-marker-and-bits` held three
  free-bit pull-ups and eight marker straps that were not parts. It is now
  one pull-up, placed once per free bit (`replicated: 3`); the marker straps
  are drawn as the plain wiring they are, on each board. The BOM count is
  unchanged.
- **Not yet migrated:** the main board's circuits, the module's, and the
  interfaces. Their `netlist.yaml` stays hand-written and authoritative until
  each gets its sheet; `tools/sch.py` writes a circuit's first sheet from its
  YAML, and from then the sheet is edited instead.
- **The BOM fragments are a second phase.** A fragment's quantity is a total
  over every board, so it can only be counted from the sheets once every
  board is in KiCad. Until then the fragments stay hand-written, and
  `check-netlist.py` keeps proving the sheets' parts against them.
- **`allocation.yaml` stays data until the main board is drawn**, because two
  of its four rows are registers on the main board. `kicad.py check` proves
  the key boards' wiring against it, and it against the page's table.
- **`kicad.py check` needs KiCad 9**, so it is not in the commit hook, which
  runs before every shell command. It is run by hand, and
  `docs/reference/tooling.md` says when.
