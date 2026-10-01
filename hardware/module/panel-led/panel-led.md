# Panel LED — schematic

**Status:** Split out of [`power-entry.md`](../power-entry/power-entry.md)
2026-09-21. One resistor and a header on the main board, and a panel-mount
LED on a lead (ADR 0024 point 16, 2026-10-01).

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `UMBILICAL +12V` | in | `module/umbilical-load-switch` | `umbilical-current` | The LT1641's output, through `R-LED-PANEL` on the main board and `J-LED-PANEL` pin 1 into `LED-PANEL` on the panel (ADR 0024 point 16); it does not cross `J-B2B-MOD` |
| `AGND_MOD` | ref | `module/power-entry` | `dig-gnd-topology` | The LED's cathode, back through `J-LED-PANEL` pin 2 to the main board's `AGND_MOD` |
| panel cutout | — | `module/panel` | `panel-height-budget` | A cutout, not a net: `LED-PANEL`'s own hole (`led.hole_d`), in the toggle's row, left of the toggle (ADR 0024 point 11); the figure's `toggle_row` note is what establishes that the row fits |
| comparator collector node | — | `module/link-supervision` | — | **Not fitted.** The deleted presence comparator shared this node |

## The circuit

**Where it is.** `LED-PANEL` is a **panel-mount indicator**, a Dialight
605-2211-110F: a 3 mm green LED recessed in a chrome M5 housing, in its own
hole in the panel and held by its own nut (`config/module.yaml` `led.*`).
Nothing of it is on a board. Its leads are cut short and soldered to
**`CBL-LED-PANEL`**, a two-wire lead whose JST XHP-2 plugs into
**`J-LED-PANEL`**, a B2B-XH-A on the main board's front face below the LED
(`mechanical/module/export/pcb-geometry.echo` *J-LED-PANEL*): **pin 1 is the
anode** (`LED_ANODE`, the red wire), pin 2 the cathode (`AGND_MOD`). The
header is polarised by its shroud, and the anode is the lead the dot on the
housing's back marks `[ds DIALIGHT-605-SERIES-PMI-CATALOG-2021-EXCERPT.pdf]` —
confirm it with a meter's diode test and mark it before the leads are cut,
because cut they are the same length (the 2026 page says only "these
indicators are non-polarized", which reads as the housing, not the LED). Plug the lead in before the main board goes onto the
panel studs. What it all stands behind the panel, and the lead's run, are
`mechanical/module/drc.echo` *LED-PANEL behind the panel* and
*CBL-LED-PANEL's run, LED to header* (ADR 0024 point 16).

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

**Two banked catalogues disagree on what LED is inside.** The 2021 page
gives every 605 part 2 V at 15 mA, green 70 mcd typical
`[ds DIALIGHT-605-SERIES-PMI-CATALOG-2021-EXCERPT.pdf]`; the 2026 one gives
the same part number 3 V at 20 mA and 900–1400 mcd, an InGaN die
`[ds DIALIGHT-605-SERIES-PMI-CATALOG-2026-EXCERPT.pdf p.2]`. `R-LED-PANEL`
holds either: `[calc]` `(12.0 − 3.0 V) / 2.2 kΩ` ≈ **4.1 mA** to
`(12.0 − 2.0 V) / 2.2 kΩ` ≈ **4.5 mA**, taken from the umbilical branch —
under 0.5 % of the 940 mA limit, and inside either catalogue's operating
current. The LED lights as the output passes 2–3 V, so it also shows a
slow start. The sim (`sim/`) holds both across `U-ISO`'s tolerance and the
resistor's. **How it looks is the first build's to see**: the newer part at
4 mA is far brighter than the older one at the same current
`[calc: 900 mcd × 4.1/20 ≈ 185 mcd against 70 × 4.5/15 ≈ 21 mcd, linear
in current]`; `R-LED-PANEL` moves if it glares or is dim.

**What it does not say**: whether the instrument is plugged in. With the
toggle on and nothing on the cable the output is still delivered and the LED
is lit. That knowledge moved to the instrument with the presence detect
(`module/link-supervision`).

*(The circuits it replaced — the presence comparator's shared node, the
LED on the analog +12 V rail, and the 0805 under a light pipe — are in
[`notes.md`](notes.md).)*
