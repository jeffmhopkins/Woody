# 0028 — The lights are thirteen LEDs on the main board, not a strip

**Status:** Accepted, 2026-09-30. Decided by the owner. It amends
[ADR 0014](0014-lighting.md) (the strip, its density and the diffusion
prototype's timing) and [ADR 0016](0016-one-strip-on-the-centre-board.md)
(one strip on the centre board, whose "LEDs populated directly on the centre
board ... not decided here" this decides). Each carries a dated note pointing
here. Numbering: 0025–0027 are taken.

## Context

Since ADR 0016 the lights were one WS2815 strip, 60/m, stuck LEDs-up down the
main board's top-face centreline, its four leads hand-soldered to pads
(`J-LED`). The strip was the one adhesive part and the one hand-soldered lead
set in the lighting, and it cost the board more than its own area:

- **a centreline band with nothing in it** — no parts, no mounts — the
  strip's width plus a margin, the length of the board;
- **the U-bolt held to M3**, because an M4 or M5 nut's keep-out reached under
  the strip (`hardware.ubolt_rod_d`);
- **the breath tube had to clear the strip** where it crossed the board;
- **the near thumb row turned 180°** so its pins pointed away from the strip
  (`config/key-layout.yaml`).

A trade study (2026-09-29, research only, kept in the session's scratchpad
rather than the corpus) compared the strip with discrete LEDs on the board,
five LED families and the power paths; its figures are cited below where they
are used, each with its own provenance.

## Decision

The owner's decisions, 2026-09-30, relayed with the brief for this change:

1. **Thirteen LEDs.** `lighting.led_count` in `config/body.yaml`.
2. **WS2815B-V1** (Worldsemi, LCSC C5446699), 5050 PLCC6, reflowed by the
   board house. It is the only stocked, individually addressable, integrated
   part found that is both 12 V and has a backup data input
   `[web LCSC C5446699 and JLC's part page, 2026-09-29, via the study]`.
   Its sheet is banked: `datasheets/led/WS2815B-V1.pdf`.
3. **On the main board's top face, one row on the centreline.** The body CAD
   places them (`lighting.*`, the `led` records in
   `mechanical/export/pcb-geometry.echo`).
4. **12 V**, the same rail the strip ran from. No new rail, no new level
   shifting beyond the existing 74AHCT125, no new firmware protocol.
5. **The backup input chained** (`DIN2`, the datasheet's second input): each
   LED's `DIN2` from the `DIN1` of the LED before it — the `DO` of the LED two
   back — and LED 1's `DIN2` to GND, as the WS2815's recommended circuit
   draws it `[ds datasheets/led/WS2815.pdf p.4]`. One dead LED goes dark and
   the rest keep working. In a body that is glued shut (ADR 0025) that is the
   repair.
6. **100 nF at every LED**, `VDD` (pin 2) to GND. Pin 1 is NC on the B-V1
   `[ds WS2815B-V1.pdf p.2]`.
7. **White solder mask on the main board.** The top face is the row's first
   reflector (ADR 0016 named white mask as the cheap improvement). Recorded
   on `PCB-CARRIER` and in `hardware/boards/main-board/README.md`.

`R-LED-SER`, `R-LED-PD` and `C-STRIP-BULK` stay. The circuit, its derivation
against the B-V1's `V_IH` and the row's current are
[`led-strip-drive.md`](../../hardware/carrier/led-strip-drive/led-strip-drive.md);
the current is the tracked figure `led-row-current`, blocked on E6.

## What the strip forced, and what happens to each

- **The empty centreline band goes.** Parts and mounts keep clear of each
  LED's footprint instead of a band (`so_clear` in the body CAD; *"LED row on
  the main board"* in `mechanical/drc.echo`). Everything the last placement
  put outside the band is still clear of the row, because the LEDs lie inside
  the band's old footprint.
- **The U-bolt could be M4 or M5 again.** The row is shifted along the body
  so that the U-bolt station falls midway between two LEDs (below), so no
  LED stands between the legs and the nuts' keep-out reaches nothing at the
  station. The neck of board between the legs keeps its width for traces.
  `hardware.ubolt_rod_d` stays M3 until the strap hardware is chosen (ADR
  0025's open item), but the strip no longer bounds it.
- **The breath tube's crossing.** The check that the tube clears the strip is
  now a check that it clears the LEDs' tops, which are lower
  (*"breath tube crosses the LED row clear of it"*).
- **The near thumb row stays turned 180°**, for a new reason: its pins still
  point away from the centreline, which now keeps the band clear for the LED
  row, its 100 nF and its three data traces. Unturned, a near-row switch's
  pin stubs would reach 25.55 mm across the board against an LED courtyard
  starting at 25.75 `[calc: 18.5 + 5.75 + 1.3; 28.5 − 2.75]`, 0.2 mm — the
  placement rule's whole margin. No switch was flipped, so no pin moved and
  no board was laid out again for it.
- **LED 7 off the U-bolt station: the row is shifted, no station is skipped.**
  The thirteen at `lighting.led_pitch`, centred in the span the board allows,
  would put one LED within a couple of millimetres of the station. The body
  CAD shifts the whole row toward the mouth until the station is midway
  between two LEDs, and fails if that pushes the row out of its span
  (*"LED row off the U-bolt station"*). Skipping a position instead would
  leave a double gap in the light at the middle of the body.

## The light path

The requirement is unchanged: both frosted acrylic sides lit, indirectly, with
the cavity as the diffuser (ADR 0014, ADR 0016). Two things move:

- **The emitters sit about 0.85 mm lower** than on the strip, on the board at
  the LED's 1.65 mm `[ds WS2815B-V1.pdf p.2]` rather than on tape at
  ~2.5 mm `[from memory, the old lighting.strip_t]` — under 5 % of the
  18.8 mm to the key boards and the ~21 mm to each side `[calc]`. Not
  significant, but the diffusion test should be run at board level.
- **Count and pitch are fixed when the board is fabricated.** A strip could
  be re-bought at another density after M6; a board cannot. **The diffusion
  test moves ahead of the main board's layout** (ROADMAP, *Side-light
  diffusion*): a strip offcut at board height under a white-masked mock key
  board, with the real acrylic at the side distance. It decides
  `lighting.led_count` and `lighting.led_pitch`.

## Consequences

- **Power.** The row at full white is `led-row-current`, a fifth of an amp
  at 12 V, where ADR 0014's reading of the WS2815's "15 mA" as per channel
  would have made it three times the B-V1's own stated maximum power
  (`led-strip-drive.md`, *The current*). It comes from the module's isolated
  converter through the load switch (ADR 0027), and a latched full-white row
  after a brownout sits on 12 V, not on the MCU's 5 V buck. ADR 0005's load
  table rows for the strips are upper bounds that no longer describe the
  lights; E6 measures the row.
- **Quiescent draw is always on.** Under 2 mA per LED blanked `[ds p.3]`,
  ~0.3 W for the row `[calc: 13 × 2 mA × 12 V]`, part of the interior's heat.
- **MSL 5a.** The LEDs must be baked before reflow `[ds p.6]`; the board
  house does this for moisture-sensitive LEDs `[web, via the study; not a
  per-order guarantee]`. After reflow they are not repairable, which is what
  the backup line is for.
- **The body's chamfer marks pin 4, not pin 1** `[ds p.2]`. The footprint
  (`hardware/lib`) draws it that way; check the assembler's rotation for
  this part on the first order.
- **Operating range −40 to +65 °C** `[ds p.2]`, against an interior 10–20 K
  above ambient (ADR 0014). Fine in a room; worth remembering under stage
  lights.
- **The LEDs are on the board from the first E-stage build**, so the
  LED-induced breath step (ADR 0014) is measured on the real layout, and E11
  runs with the lights in place.

## Open, and what decides each

| Item | Decided by |
|---|---|
| The row's current at full white (`led-row-current`) | E6, a current probe on the row's feed |
| `lighting.led_count` and `lighting.led_pitch` | The side-light diffusion test, before the main board's layout |
| Whether the assembler's rotation for the B-V1 matches the footprint (chamfer at pin 4) | The first board order's placement preview |
| The U-bolt's size, now unbounded by the lights | ADR 0025's open item: the strap hardware chosen (M4) |
