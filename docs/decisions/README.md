# Architecture Decision Records

Every non-obvious choice in this project gets a numbered record here: what was
decided, what the alternatives were, and why. Six months from now, "why did I
pick that sensor" should have a written answer.

## Scope

Decisions here are made for **one case: a tethered rack instrument**, powered by
and patched into a Eurorack system. See the design scope in the
[README](../../README.md).

Battery operation, wireless output, standalone use and touring durability are
explicit non-goals. An argument that only holds away from the rack is not a
reason to do anything — several ADRs here previously carried justifications of
that kind and have been trimmed.

## Status values

| Status | Meaning |
|---|---|
| **Accepted** | Decided. Build to this |
| **Open** | Options identified, decision not made. Usually blocking something |
| **Superseded** | Replaced by a later ADR. Kept for the reasoning trail |

## Format

Context, Options, Decision, Consequences. Keep the options that were rejected —
the reasoning behind a rejection is often more useful later than the decision
itself, especially when circumstances change and the rejected option comes back.

When a decision is reversed, do not edit the old ADR. Mark it `Superseded` and
write a new one that says what changed. ADR 0005 is an example: the battery
architecture was real work that got deleted by a better idea, and the record of
why it was deleted is worth keeping.

A **partial** reversal, where most of the decision stands, may instead be
recorded in the same ADR as a dated `## Amendment, <date>` section, with a
dated italic note at each point it changes, and the amendment named in the
`**Status:**` line. ADRs 0017, 0019 and 0020 are examples.

## Index

> **This table is hand-maintained, and on 2026-09-21 three of its fourteen rows
> disagreed with the ADR they point at** — 0007 and 0008 read "(board open)"
> while both files name a selected board, and 0011 read "Open" while the ADR
> says `Accepted`. Each row restates a fact its own target owns, which is
> rule 1 in `CLAUDE.md` broken in the project's own index. **It should be
> generated from the `**Status:**` line of each ADR.** Until it is, check the
> file before trusting the row.

| # | Title | Status |
|---|---|---|
| [0001](0001-mcu-and-board-partitioning.md) | MCU selection and board partitioning | Accepted (partitioning revised by 0013, one MCU since 0015) |
| [0002](0002-key-switches-and-mounting.md) | Key switches and mounting | Accepted |
| [0003](0003-breath-sensing-path.md) | Breath sensing signal path | Accepted |
| [0004](0004-cv-interface-module.md) | CV interface module and umbilical | Accepted |
| [0005](0005-power-architecture.md) | Power architecture | Accepted |
| [0006](0006-cv-channel-allocation.md) | CV channel allocation and calibration | Accepted |
| [0007](0007-imu-selection.md) | IMU selection | Accepted. Board selected: Waveshare ESP32-S3-Matrix |
| [0008](0008-display-selection.md) | Display selection | Superseded by 0015 |
| [0009](0009-enclosure-construction.md) | Enclosure construction | Accepted; how the body closes amended 2026-09-29 by 0025 (no body fasteners, glued shut round the cassette) |
| [0010](0010-key-layout-as-data.md) | Key layout as data | Accepted |
| [0011](0011-licensing.md) | Licensing | Accepted |
| [0012](0012-configuration-interface.md) | Configuration interface | Superseded by 0015 |
| [0013](0013-two-mcu-split.md) | Two-MCU split | Superseded by 0015 |
| [0014](0014-lighting.md) | Lighting | Accepted (geometry amended by 0016) |
| [0015](0015-one-mcu-no-display.md) | One MCU, no display board | Accepted |
| [0016](0016-one-strip-on-the-centre-board.md) | One LED strip, on the centre board | Accepted (placement amended by 0017) |
| [0017](0017-one-main-board.md) | One main board | Accepted (wiring details in 0018; key-chain connectors amended to through-hole IDC 2026-09-27) |
| [0018](0018-main-board-wiring-decisions.md) | Main board wiring: five decisions | Accepted |
| [0019](0019-kicad-sheets-are-the-source.md) | The KiCad sheets are the source of truth | Accepted, amended 2026-09-27 (the sheet names the bought part; migration in progress) |
| [0020](0020-key-boards-screw-to-the-plate.md) | The key boards are screwed to the key plate | Accepted, amended 2026-09-29 (1.6 mm boards pressed against the switches; Amendment 7: held by the cassette's columns, Amendment 5's bond superseded, by 0025), 2026-09-27 (a mount at each corner, 1.2 mm boards; twice more the same day) and 2026-09-28 (Amendment 4: a PEM flush-head stud pressed into the plate, nothing above it) |
| [0021](0021-pcb-mount-ethercon.md) | The instrument's etherCON is PCB-mounted, on an adapter joined to the main board | Accepted (the instrument's end of ADR 0004's open variant question) |
| [0022](0022-main-board-mount.md) | How the main board is held, and how thick it is | Accepted, amended 2026-09-29 by 0025 (every mount on the bottom plate) |
| [0023](0023-module-ethercon-and-two-boards.md) | The module's etherCON is the NE8FAV too, and the module is two boards | Accepted (the module's end of ADR 0004's open variant question); amended 2026-09-29 by 0024 (no PUSH-tab slot) |
| [0024](0024-module-panel-layout-and-stack.md) | The module's panel layout and board stack | Accepted |
| [0025](0025-the-cassette.md) | The cassette: the internals are one bonded unit, dropped into the shell | Accepted |
| [0026](0026-module-panel-graphics.md) | The module panel's graphic language (dark Lifeforms-style islands, Inter lowercase, spot-colour UV print) | Accepted |
| [0027](0027-isolated-instrument-supply.md) | The instrument's supply is isolated, drawn rail to rail | Accepted |
