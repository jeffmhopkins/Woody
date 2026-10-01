# Interface module — board page

The 10HP Eurorack module. It holds the DAC, all six output stages, the panel
controls and the jacks, and takes ±12 V from the rack.

This page is a board page: it says what the board carries and points at the
circuits. **The circuits own their own values** — nothing here restates one.

## Circuits on this board

| Directory | What it is |
|---|---|
| [`power-entry/`](power-entry/power-entry.md) | Rack ±12 V in: the three diodes, the beads, the DAC rail (`U-REG-DAC`), and the grounding origin |
| [`umbilical-load-switch/`](umbilical-load-switch/umbilical-load-switch.md) | The LT1641 that ramps and current-limits the +12 V sent up the umbilical |
| [`dac8568/`](dac8568/dac8568.md) | The converter: `CLR`, the `LDAC` strap, the grade lock |
| [`digital-and-supervision/`](digital-and-supervision/digital-and-supervision.md) | The module end of the SPI receive path |
| [`link-supervision/`](link-supervision/link-supervision.md) | **Not fitted, by decision** (owner, 2026-09-30: the module always runs with an umbilical attached to a controller). The deleted watchdog and presence detect, and what restoring them would cost |
| [`breath-receive-stage/`](breath-receive-stage/breath-receive-stage.md) | The module half of the breath chain: the `REF` trimmer, commissioning, the `CLR` behaviour |
| [`breath-output-stage/`](breath-output-stage/breath-output-stage.md) | Buffered attenuator → ×4 summer with bipolar offset → jack |
| [`breath-response-shaper/`](breath-response-shaper/breath-response-shaper.md) | `POT-RESP`, the antiparallel-diode shaper |
| [`pitch-stage/`](pitch-stage/pitch-stage.md) | Two-resistor non-inverting `2·Vdac − 2.5`, loop tapped at the jack |
| [`mod-channels/`](mod-channels/mod-channels.md) | Four × `4·Vdac − 3·V_ref`, sharing one buffered reference |
| [`panel-led/`](panel-led/panel-led.md) | The panel indicator: lit while the load switch delivers, dark when it is off or latched |
| [`panel/`](panel/panel.md) | Panel geometry: width, clear height, how many control rows fit, and the layout (ADR 0024) |

**The module is two boards** (ADR 0023), and each circuit's KiCad sheet is
its source (ADR 0019): [`module-main`](../boards/module-main/README.md)
carries the etherCON, every IC, the trimmers and the power header;
[`module-jack`](../boards/module-jack/README.md) the jacks and pots. The
panel LED is on the main board, under a light pipe (ADR 0024 point 15).
`J-B2B-MOD` joins them; its pin allocation is in the main board's README.

The other half of the breath chain and of the SPI path are **not here**. They
cross a board boundary and live in
[`hardware/interfaces/`](../interfaces/README.md), because their transfer
functions and error budgets cannot be stated from one side.

## Still open at board level

- **The board outlines and the panel's cut file are generated** by the module
  CAD (ADR 0024): `mechanical/module/export/` holds the panel DXF, both
  boards' outlines and `pcb-geometry.echo` — every panel part's position,
  the standoffs, both connectors and each face's keep-outs — which is the
  board layout's input. `mechanical/module/README.md` has the pictures.
  Nothing has been cut yet.
- **The panel's print is generated too** (ADR 0026): `mechanical/module/art/`
  holds the spot-colour PDF and SVG master that go to the panel maker with
  the DXF, made by `tools/panel-art.py` from the same CAD. One proof panel
  before a run.
- **Four layers, 1.6 mm, for the main board; two for the jack board** — the
  owner, 2026-09-30: *"Four layer in the module board is fine."* The ground
  scheme on it is `dig-gnd-topology` (`power-entry/`, *Grounding*). The jack
  board has one ground, `AGND_MOD`, and needs no second layer pair.
- **The bus +5 V is not used** (owner, 2026-09-30): the module makes its own
  (`power-entry/`, *The logic 5 V*) and keeps the 16-pin header (ADR 0023).
- ~~`hardware/unplaced.csv` holds this board's principal ICs.~~ **Fixed
  2026-09-21.** The DAC, the in-amp, the LM317, the entry diodes, the beads,
  the bulk caps, both load-switch capacitors and the level shifter are now
  filed with the circuits that derive them. The cause was mechanical: BOM
  assignment matched on reference designator and these are drawn by part
  number or by a local label, so `hardware/module/dac8568/bom.csv` held two
  resistors and not the DAC.
