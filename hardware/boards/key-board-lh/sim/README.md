# Left-hand key board — simulation

The whole board as it is wired. The deck is **generated** by `tools/sim.py` from
`../board-netlist.yaml`:
- every part is placed by its BOM row (`sims.yaml` `parts:`), on the nets the
  sheets connect it to;
- `drive:` puts the bench of *Bring-up* on J1: 3V3, SH/LD high, the clock low,
  SER tied low.

A wrong value, a pull-up on the wrong rail or an input wired to the wrong key
therefore shows up in the board's own simulation. `results.yaml` is generated;
`check-staleness.py` holds it to the netlist, the decks and the cited figures.

The switch and register model, and the thresholds, are imported from the key
network's simulation (`params_from:`), so they are stated once.

| Sim | Holds, at every corner |
|---|---|
| `all-keys-released` | every key input (H..D) above VT+ max; the free input (A, R11) and the high marker (B) above VT+ max; the board draws only leakage and the register's static current |
| `all-keys-pressed` | every key input below VT− min; the free input still high; the draw is the switch count × `key-scan-current` |

**Not simulated here:**
- The low marker (C) is on ground, which SPICE holds at 0 V. `kicad.py check`'s
  allocation test holds that wiring.
- The register's outputs.
- The rail and the chain's signals over the ribbon need the main board's end:
  the bead, the driver and the ribbon (see `sims.yaml`'s sims as they are added).
