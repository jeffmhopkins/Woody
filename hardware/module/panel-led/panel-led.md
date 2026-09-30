# Panel LED — schematic

**Status:** Split out of [`power-entry.md`](../power-entry/power-entry.md)
2026-09-21. One resistor, one LED, and an open question about what it is for.

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `UMBILICAL +12V` | in | `module/umbilical-load-switch` | `umbilical-current` | The LT1641's output, through `R-LED-PANEL` into `LED-PANEL`. It crosses to the jack board on `J-B2B-MOD` pin 19 |
| `AGND_MOD` | ref | `module/power-entry` | `dig-gnd-topology` | The LED's cathode, back across `J-B2B-MOD`'s ground pins with every other jack-board return |
| panel cutout | — | `module/panel` | `panel-height-budget` | A cutout, not a net. The LED sits in the toggle's row, left of the toggle (ADR 0024 point 11); the figure's `toggle_row` note is what establishes that the row fits |
| comparator collector node | — | `module/link-supervision` | — | **Not fitted.** The deleted presence comparator shared this node |

## The circuit

`R-LED-PANEL` and `LED-PANEL` in series from the load switch's output to
`AGND_MOD`. **Lit means the load switch is delivering**; dark means the toggle
is off *or* the `-1` has latched on a fault — which is the one thing the
panel has to say, because a latch leaves the instrument dark until the toggle
is cycled ([`umbilical-load-switch.md`](../umbilical-load-switch/umbilical-load-switch.md),
*`-1`, not `-2`*).

**Why the output and not `TIMER` or `GATE`**, the two nodes this page used to
propose. The banked datasheet settles it `[164112fc p.5, pin functions]`:
after a latch `GATE` is pulled to ground and `TIMER` is discharged by its
3 µA pull-down, so neither holds a level that says "latched" — `TIMER`
returns towards 0 V, which is where it sits in normal running too. The output
does hold one: with `GATE` low it decays to 0 V and stays there. `PWRGD` is
an open collector that pulls low while `FB` is *below* its threshold, so an
LED on it would be lit for the fault and dark in normal running — the
opposite of a power lamp, and it would need its own supply to be lit at all.

`[calc]` `(12.0 − 2.0 V) / 2.2 kΩ` ≈ **4.5 mA**, taken from the umbilical
branch: 0.5 % of the 940 mA limit. The LED lights as the output passes about
2 V on the way up, so it also shows a slow start.

**What it does not say**: whether the instrument is plugged in. With the
toggle on and nothing on the cable the output is still delivered and the LED
is lit. That knowledge moved to the instrument with the presence detect
(`module/link-supervision`).

*(The circuits it replaced — the presence comparator's shared node, and the
LED on the analog +12 V rail — are in [`notes.md`](notes.md).)*
