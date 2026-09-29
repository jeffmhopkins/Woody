# 0019 — The KiCad sheets are the source of truth

**Status:** Accepted. Decided by the owner, 2026-09-27; amended the same day
(the sheet names the bought part). Migration in progress:
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
  `Note` — and, since the 2026-09-27 amendment below, the bought part:
  `Manufacturer`, `MPN`, `LCSC` and `Assembly`. Ports are hierarchical labels, carrying their direction, peer and
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
  would be made once per networked position on every board — the count
  `key-switch-network/netlist.yaml`'s `replicated:` gives. Not chosen.

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
- **Migrated, 2026-09-29:** the main board's six circuits (`carrier`,
  `breath-adc`, `breath-excitation-reference`, `power-entry-instrument`,
  `service-uart`, `led-strip-drive`) and the board `main-board`, which places
  them with the thumb clusters and draws the interfaces' main-board parts.
  Each export was compared part by part and net by net with the hand-written
  netlist it replaced; ERC over the board is clean. **What the migration
  changed, on purpose:** the OPA2197 became one part with its supply pins
  netlisted, where it had been two half-parts with the supply as metadata; the
  REF5050's unused pins are netlisted as no-connects; and the two grounds that
  meet "in copper, not a part" at one place (the analog star's tie,
  `NT-AGND`, and `DIG_GND` at `J-UMB`, `NT-DIG`) are KiCad net ties, the one
  way a board can join two named nets there and nowhere else. A lone
  no-connect pin's net is named after the pin, as the export names it.
- **Not yet migrated:** the module's circuits and the interfaces. Their
  `netlist.yaml` stays hand-written and authoritative until each gets its
  sheet; `tools/sch.py` writes a circuit's first sheet from its YAML, and from
  then the sheet is edited instead.
- **The BOM fragments are a second phase.** A fragment's quantity is a total
  over every board, so it can only be counted from the sheets once every
  board is in KiCad. Until then the fragments stay hand-written, and
  `check-netlist.py` keeps proving the sheets' parts against them.
- **`allocation.yaml` stays data until the main board is drawn**, because two
  of its four rows are registers on the main board. `kicad.py check` proves
  the key boards' wiring against it, and it against the page's table.
- **The layouts follow the same rule** (2026-09-27, the left-hand key board
  as proof of concept): `tools/pcb.py` writes a board's first layout from the
  sheets and the body CAD's exports, and from then the `.kicad_pcb` is the
  source, checked by KiCad's DRC with schematic parity and against the body
  CAD's switch positions. `docs/reference/tooling.md` §4.
- **`kicad.py check` needs KiCad 9**, so it is not in the commit hook, which
  runs before every shell command. It is run by hand, and
  `docs/reference/tooling.md` says when.

## Amendment, 2026-09-27 — the sheet names the bought part

Decided with the left-hand key board's first order (`hardware/boards/key-board-lh/`).

- **Every part on a migrated sheet carries four more fields:**
  `Manufacturer`, `MPN` (the orderable part number), `LCSC` (the board
  house's stock number, for a machine-placed part) and `Assembly` —
  `machine` (placed by the board house, so it needs an `LCSC`), `hand` (fitted
  after, listed in the hand-assembly file) or `none` (copper only: a test pad,
  a mounting hole). `tools/pcb.py` builds a board's BOM, placement and
  hand-assembly lists from these fields and refuses a part without an
  `Assembly`, or a `machine` part without an `LCSC`.
- **The BOM row says what the part must be; the sheet says which one is
  bought.** The fragment's `part`, `package` and `description` are the
  requirement (value, tolerance, dielectric, package), and its `manufacturer`
  column is the constraint on who may supply it (`multiple` means any vendor
  that meets the row). The sheet's `Manufacturer`/`MPN`/`LCSC` are the choice
  that meets it, and they win for ordering. Change the bought part on the
  sheet, then re-export and re-render; change the row only when the
  requirement changes.
- **This does not undo "part facts in two places" (Options).** The row keeps
  the requirement and the sheet the choice — two different facts. A migrated
  circuit's fragment does not restate the sheet's part number; a page that
  needs one cites the sheet (or the board's generated `fab/` BOM).
