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
| [0001](0001-mcu-and-board-partitioning.md) | MCU selection and board partitioning | Accepted (partitioning revised by 0013) |
| [0002](0002-key-switches-and-mounting.md) | Key switches and mounting | Accepted |
| [0003](0003-breath-sensing-path.md) | Breath sensing signal path | Accepted |
| [0004](0004-cv-interface-module.md) | CV interface module and umbilical | Accepted |
| [0005](0005-power-architecture.md) | Power architecture | Accepted |
| [0006](0006-cv-channel-allocation.md) | CV channel allocation and calibration | Accepted |
| [0007](0007-imu-selection.md) | IMU selection | Accepted. Board selected: Waveshare ESP32-S3-Matrix |
| [0008](0008-display-selection.md) | Display selection | Accepted. Board selected: LilyGO T-Display-S3 AMOLED |
| [0009](0009-enclosure-construction.md) | Enclosure construction | Accepted |
| [0010](0010-key-layout-as-data.md) | Key layout as data | Accepted |
| [0011](0011-licensing.md) | Licensing | Accepted |
| [0012](0012-configuration-interface.md) | Configuration interface | Accepted |
| [0013](0013-two-mcu-split.md) | Two-MCU split | Accepted |
| [0014](0014-lighting.md) | Lighting | Accepted |
