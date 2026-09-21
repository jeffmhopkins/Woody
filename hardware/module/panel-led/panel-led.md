# Panel LED — schematic

**Status:** Split out of [`power-entry.md`](../power-entry/power-entry.md)
2026-09-21. One resistor, one LED, and an open question about what it is for.

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `+12 V analog` | in | `module/power-entry` | — | Through `R-LED-PANEL` into `LED-PANEL`. Live whenever the rack is, which is the whole of the problem below |
| LED return | ref | `module/power-entry` | `dig-gnd-topology` | **Not drawn anywhere in the corpus.** The rail it comes from is the analog one; which ground it lands on is the disputed figure |
| panel cutout | — | `PANEL` | `panel-height-budget` | The bezel sits beside the etherCON flange; the figure's `toggle_row` note is what establishes that it fits |
| `TIMER` / `GATE` of `U-LOADSW` | — | `module/umbilical-load-switch` | `loadswitch-timer` | **Proposed, not drawn.** The rework below would take the indication from here instead |

## The circuit

*The superseded circuit this sentence says "instead" of — the presence
comparator and the two resistors that hung off it — is in
[`notes.md`](notes.md).*

`bom.csv` carries `R-LED-PANEL` at **2.2 kOhm from +12 V analog** instead,
and that is the circuit.

## But the LED has lost the job it was kept for

*Moved verbatim from `power-entry.md`, 2026-09-21. "The latching faults
above" are the ones in
[`umbilical-load-switch.md`](../umbilical-load-switch/umbilical-load-switch.md),
which is where they still are.*

`bom.csv` justifies it: *"with LT1641-1 latching off on a fault, this still
says why the instrument went dark."* **On +12 V analog it cannot.** That
rail is live whenever the rack is, so the LED is lit in every one of the
latching faults above — hot-plug, LED-boot overcurrent, a current-limited
start, a soft short. The one indication the design has for "the load switch
has latched" indicates nothing.

**Cheapest high-value fix in the review**: drive it from the LT1641's
`TIMER` node, or from the gate, so that **lit = running and dark =
latched.** One resistor's worth of rework on a part that is already fitted.

Not applied here: it needs the same datasheet read as `C-TIMER`, because it
depends on what the `TIMER` pin does after a latch.
