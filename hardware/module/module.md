# Interface module — board page

The 10HP Eurorack module. It holds the DAC, all six output stages, the panel
controls and the jacks, and takes ±12 V from the rack.

This page is a board page: it says what the board carries and points at the
circuits. **The circuits own their own values** — nothing here restates one.

## Circuits on this board

| Directory | What it is |
|---|---|
| [`power-entry/`](power-entry/power-entry.md) | Rack ±12 V in: the three diodes, the beads, the LM317 rail, and the grounding origin |
| [`umbilical-load-switch/`](umbilical-load-switch/umbilical-load-switch.md) | The LT1641 that ramps and current-limits the +12 V sent up the umbilical |
| [`dac8568/`](dac8568/dac8568.md) | The converter: `CLR`, the `LDAC` strap, the grade lock |
| [`digital-and-supervision/`](digital-and-supervision/digital-and-supervision.md) | The module end of the SPI receive path |
| [`link-supervision/`](link-supervision/link-supervision.md) | **Not fitted.** The deleted watchdog and presence detect, and what restoring them would cost |
| [`breath-receive-stage/`](breath-receive-stage/breath-receive-stage.md) | The module half of the breath chain: the `REF` trimmer, commissioning, the `CLR` behaviour |
| [`breath-output-stage/`](breath-output-stage/breath-output-stage.md) | Buffered attenuator → ×4 summer with bipolar offset → jack |
| [`breath-response-shaper/`](breath-response-shaper/breath-response-shaper.md) | `POT-RESP`, the antiparallel-diode shaper |
| [`pitch-stage/`](pitch-stage/pitch-stage.md) | Two-resistor non-inverting `2·Vdac − 2.5`, loop tapped at the jack |
| [`mod-channels/`](mod-channels/mod-channels.md) | Four × `4·Vdac − 3·V_ref`, sharing one buffered reference |
| [`panel-led/`](panel-led/panel-led.md) | The panel indicator, and the job it has lost |
| [`panel/`](panel/panel.md) | Panel geometry: width, clear height, how many control rows fit |

The other half of the breath chain and of the SPI path are **not here**. They
cross a board boundary and live in
[`hardware/interfaces/`](../interfaces/README.md), because their transfer
functions and error budgets cannot be stated from one side.

## Still open at board level

- **There is no module board outline or panel DXF yet.** `panel/` settles the
  geometry; nothing has been cut.
- **Two layers or four** is undecided and gates the grounding scheme. It is
  upstream of `power-entry/`'s `dig-gnd-topology`, which is tracked as
  `disputed` for exactly this reason.
- **`hardware/unplaced.csv` holds this board's principal ICs** — the DAC, the
  in-amp, the LM317 — because BOM assignment matched on reference designator
  and these are drawn by part number. Known, recorded, not yet fixed.
