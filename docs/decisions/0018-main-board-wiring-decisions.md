# 0018 — Main board wiring: five decisions

**Status:** Accepted. **Amended 2026-10-01** (the module end of `DIG_GND` is
settled, *Amendment* below).

Closes five items that [ADR 0017](0017-one-main-board.md)'s rework left open
on the main board's pages. Decided by the owner, 2026-09-26, taking the
recommendation on each.

## Context

Moving to one main board, with the key boards on flat flex ribbons and the
Matrix on the lid, left five questions open in `hardware/`. A cold review of
that rework then found one fact that changed two of them: **the Matrix's 5 V
pad is `VCC_5V` itself, downstream of its `B5819WS`**
(`datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf`; ADR 0014's
2026-09-26 amendment). Fed from the pad, the Matrix's LED current is limited
only by the firmware clamp and the regulator (`U-BUCK`), so it all crosses
`J-MCU` and the ribbon.

## Decision

1. **The Matrix ribbon is 24-way, and its extra conductors carry power and
   ground.** `J-MCU` becomes a 2 × 12 1.27 mm box header and `CBL-MCU-RIBBON`
   a 24-way ribbon: the twelve used GPIO, three 5 V, four ground, 3V3, `EN`,
   `IO0` and two spare GPIO, in a pin order that puts a ground or a quiet
   line beside every fast signal. The extra 5 V and ground conductors are soldered
   to the Matrix's pads and to its test points `TP2` (`VCC_5V`) and `TP3`
   (`GND`). This shares the regulator's full current across several contacts,
   and cuts how far the Matrix's ground, and with it the breath ADC's reference,
   moves with LED current. The allocation, the pin map and the arithmetic are in
   `hardware/carrier/carrier.md`. It was 20-way, with five positions open.
2. **Fit `U-TVS-CHAIN`.** The key-chain lines that reach the ZIF connectors
   are bare to fingers whenever the lid is off and a ribbon is unplugged. The
   array cannot be added after the board is made, and costs pennies.
   *(Amended 2026-09-27: the connectors are now through-hole 1.27 mm IDC
   headers (ADR 0017's amendment); the exposure is the same — a main-board
   header with its socket unplugged — and so is the decision.)*
3. **No fuse on the chain's 3V3 (`F-CHAIN` goes); protect at the source.**
   The chain's 3V3 comes from the Matrix's own LDO. The one fault a fuse would
   cover, a ribbon seated skewed at reassembly *(since 2026-09-27 a keyed IDC
   shroud: a socket forced or a ribbon pinched)*, happens on the bench, before
   the lid goes on, and shows at once: the short pulls down the Matrix's own
   3V3, so the instrument does not start. A series ferrite per ribbon isolates
   each key board's supply. The LDO's short-circuit limit is typical-only on
   its datasheet, so E1 shorts a ribbon's 3V3 to prove it; how, and the
   ferrite's rating, are in `hardware/interfaces/key-chain-loom/`.
4. **Wire `EN` and `IO0` to the service header.** They are not on the
   Matrix's pad rows, so two conductors of the ribbon are soldered to its
   RESET and BOOT button pads and brought to `HDR-SERVICE`. The reason for
   leaving them alone (a socketed, swappable module, ADR 0009) went with ADR
   0017. A corrupted bootloader is now recovered from the service header,
   lid off, without unplugging the Matrix (`firmware/README.md`).
5. **`DIG_GND` joins the main board's ground at `J-UMB`.** It is the SPI
   return. The three SPI lines are routed over unbroken ground from `J-MCU`
   to `J-UMB`, and the breath sense return is kept off that path. This decides
   the **instrument** end only. The module end is the register's
   `dig-gnd-topology`, disputed when this was written and settled on
   2026-09-30 (amendment below).

   > **Amended 2026-10-02 (ADR 0021, *Amendment, 2026-10-02 (2)*):** the
   > ribbon is no longer soldered to the Matrix. The Matrix sits on rails of
   > the right-hand key board, its pad rows on header pins and `TP2`, `TP3`,
   > `EN` and `IO0` on four short wires, and `CBL-MCU-RIBBON` is an IDC ribbon
   > from that board's `J-MCU-KB` to `J-MCU`. The allocation and `J-MCU`'s pin
   > map are unchanged; `J-MCU-KB` numbers them from the other edge.

## Options considered

- **Ribbon:** keep 20-way and spend the five spares on 5 V and ground. That
  leaves no conductor for `EN`/`IO0`, so they would need a second lead. Or
  keep all five as spare GPIO, which leaves one ground conductor carrying
  every LED return. Not chosen.
- **ESD:** handling care only. Relies on remembering every time, and a zap
  lands on the MCU. Not chosen.
- **3V3 fuse:** fit `F-CHAIN`. Harmless electrically, but it guards a fault
  that is visible immediately. Not chosen.
- **`EN`/`IO0`:** leave them off. Recoverable anyway with the lid off, only
  less conveniently. Not chosen.
- **`DIG_GND`:** leave it open until the module-side dispute settles. An
  unterminated return on a 2 MHz link is the worst of the three, and it
  blocks the main board's layout. Not chosen.

## Consequences

- **The tail wiring is wider.** `J-MCU` and the ribbon grow by two positions.
  The body model re-derives their placement (`config/body.yaml`
  `boards.mcu_conn_l`, `routing.mcu_ribbon_w`; `mechanical/drc.echo`).
- **Soldering to the Matrix is more than its pad rows:** two test points and
  two button pads. That is M4 work, done with the board in hand. If a test
  point cannot take a wire, its conductor moves to the matching pad.
- **E11** (breath output clean while the matrix and LEDs are exercised) is
  still the test of decisions 1 and 5.

## Amendment, 2026-10-01 — the module end is settled

Decision 5 left the module end of `DIG_GND` to the register. The owner took
the module's main board to four layers on 2026-09-30, and `dig-gnd-topology`
was settled on it: its value, its layer stack and the reason the DAC's
analog ground is not bridged to `DIG_GND` are in `config/figures.yaml`, owned
by `hardware/module/power-entry/power-entry.md` *Grounding*. Nothing in
decisions 1–5 changes. Found by the 2026-10-01 pre-layout review (A8-5).
