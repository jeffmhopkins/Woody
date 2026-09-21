# Instrument power entry — schematic

**Status:** Split out of `carrier.md` 2026-09-21 (Phase B). Every line below was
moved verbatim; nothing was reworded and no value was touched in the move. The
board-level context this circuit sits in — the one dev-board socket, the block
diagram, the board outline — stays on [`carrier.md`](../carrier.md).

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

`Dir` is this circuit's side of the net — `in`, `out`, `in/out`, `ref` (a
return or reference) or `—` (no connection here, the row is context). `Peer`
is a bare `board/circuit` id when the other end is a circuit in this tree, a
reference designator or part name when it is not, and `—` when there is
nothing on the other end.

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `UMBILICAL +12V` at `J-UMB` | in | `module/umbilical-load-switch` | `umbilical-pinmap`, `umbilical-current` | Arrives down the umbilical from the module's load switch. `D-REVSHUNT` sits at the connector, ahead of `L-BUCK-IN` |
| `PWR_GND` at `J-UMB` | ref | `module/power-entry` | `umbilical-pinmap` | This board's only supply return, down the umbilical to the module star |
| `+12V` strip feed | out | `carrier/led-strip-drive` | — | Taken direct off the input node. `C-STRIP-BULK` is this circuit's part |
| `+12V` analog | out | `carrier/breath-excitation-reference` | — | REF5050 `VIN`, and the V+ of both OPA2197 halves |
| 5 V, buck A | out | `HDR-DEV`, `carrier/led-strip-drive` | `matrix-led-current` | Through `D-USBOR` onto the dev board's 5 V pin, and on to the 74AHCT125 |
| 5 V, buck B | out | `carrier/display-and-service-uart` | — | On `J-DISP`. Buck B's location is open — see *Still open* |
| `PWR_GND` pour | ref | `carrier/breath-adc`, `carrier/breath-excitation-reference`, `carrier/display-and-service-uart`, `carrier/led-strip-drive` | `dig-gnd-topology` | The whole board returns here, and the aluminium key plate through `MECH-GNDBOND`, which can only originate here. `AGND_INST` reaches it on a single tie |

## §1 Power entry

```
 J-UMB pin 3  +12V ──┬──[D-REVSHUNT SS34]──┐
                     │   cathode to +12V   │
                     ├──[D-TVS-PWR SMAJ15A]┤
                     │                     │
                     ├─────────────────────┼──── WS2815 strips, direct
                     │                     │     (J-LED-L, J-LED-R)
                     │                     │     [C-STRIP-BULK 470–1000 µF ×2]
                     │                     │
                     ├──[REF5050]──┬────────┼──── §2 analog
                     │   in  out   │        │
                     │   │    [C-REF-OUT#2] │
                     │  [C-REF-OUT#1]       │
                     │                      │
                     ├── OPA2197 V+ ────────┤
                     │                      │
                     ├──[L-BUCK-IN]──┬──────┼──[R-78E5.0 A]──▷|──┬── dev board 5V
                     │   10–47 µH    │      │                 D-USBOR  ├── 74AHCT125
                     │        [C-BUCK-IN    │                         └── (8×8 matrix,
                     │         100 µF 25V]  │                              via the board)
                     │               │      │
                     │               └──────┼──[R-78E5.0 B]──▷|──── J-DISP 5V
                     │                      │                 D-USBOR   ?? see Still open
 J-UMB pin 6 PWR_GND ┴──────────────────────┴──── PWR_GND pour
                                             │
                                             └──[MECH-GNDBOND]── aluminium key plate
```

**`D-REVSHUNT` goes at the connector, ahead of `L-BUCK-IN`.** Its job is a
rollover patch lead swapping pins 3 and 6 `[repo] 0004`; it has to conduct
immediately and let the module's LT1641-1 latch off. An inductor between the
fault and the diode is the wrong way round.

**There is no fuse and no power switch on this board** (ADR 0005). The current
limit is at the module.

**`MECH-GNDBOND` ties the aluminium plate to `PWR_GND`, never to `AGND`**
`[repo] 0009`. This board is the only place that bond can originate.

### Derivations

**The input LC is stable** `[calc]`, which partly closes `power-entry.md`'s
"damping the input LC" open item — for the instrument end only:

```
L = 22 µH (mid range), C = 100 µF
f0 = 1/(2π√LC) = 3.39 kHz
Z0 = √(L/C)    = 0.469 Ω
ESR of a 100 µF / 25 V radial ≈ 0.5–1 Ω [from memory] → Q ≈ 0.5–0.9, no peaking

Constant-power load at typical play:
  226 mA × 5 V = 1.13 W out ÷ 0.90 = 1.26 W in at 11.4 V   [repo] 0005
  R_neg = −V²/P = −103 Ω
Margin: |R_neg| / Z0_peak = 103 / 0.47 ≈ 220× (47 dB)
```

> **This result depends on `C-BUCK-IN` being an electrolytic with real ESR.**
> Substituting a low-ESR ceramic raises Q and the paragraph stops being true.
> The BOM row says electrolytic; keep it that way.

**Regulator loading** `[calc]`, from ADR 0005's load table:

```
Clamp-legal worst on the 5 V rail, total                        928 mA  [repo] 0005
Less the display board, which is on buck B                  ~150–250 mA  ESTIMATED
Buck A (real-time board + matrix + 74AHCT125)                ~680–780 mA
R-78E5.0-1.0 rating                                            1000 mA
                                                              → 68–78 %
```

ADR 0005 says "neither is near its rating". Seventy-odd percent, inside a body
running 10–20 K above ambient, is near enough to want the derating curve.
**ADR 0005's load table has one 5 V column and the two-regulator decision needs
it split per buck. That split is not written anywhere and it is what sizes both
parts.**

---

## Strip bulk at the feed points

*Moved verbatim from `carrier.md`'s LED section, now `led-strip-drive.md`,
where it sat beside the LED data drive.*

**`C-STRIP-BULK` (470–1000 µF ×2) sits at the strip feed points**, which are on
this board — "bulk capacitance belongs where the current swings" `[repo] 0014`.
Two radial electrolytics are a height item in a ~20 mm cavity; see *Still open*.

---

## Component table

*Rows moved verbatim from `carrier.md`'s component table. Existing BOM rows are
named as they stand; **proposed** rows have no BOM entry yet.*

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-BUCK` ×2 | R-78E5.0-1.0 SIP-3 | One per dev board. **Buck B's location is open** | `[repo]` |
| `L-BUCK-IN` | 10–47 µH ≥1 A | **Qty 1 against `C-BUCK-IN`'s qty 2 "one per buck" — the two rows describe different topologies** | `[repo]`, contradictory |
| `C-BUCK-IN` ×2 | 100 µF 25 V electrolytic | **Must have real ESR; a ceramic breaks the damping** | `[repo]` + `[calc]` |
| `D-USBOR` ×2 | SS14 | **One per regulator output, not "one per source" — the OR node is a dev-board pin** | `[repo]` note is wrong |
| `D-REVSHUNT` | SS34 | At the connector, ahead of `L-BUCK-IN` | `[repo]` |
| `D-TVS-PWR` | SMAJ15A | Across the power pair | `[repo]` |
| `C-STRIP-BULK` ×2 | 470–1000 µF 16 V | At each strip feed point, which is this board | `[repo]` |

---

## Still open

*Moved verbatim from `carrier.md`'s `Still open` list.*

- **Where buck B lives.** ADR 0013's carrier list puts both regulators here;
  ADR 0013's own reasoning wants the display board's WiFi transients absorbed
  locally, which a regulator 360 mm away does not do. Either it moves to the
  display board and +12 V goes up the loom, or `C-BULK-DISP` does the job and
  the location is arbitrary. Pick one before `J-DISP`'s conductor list is fixed.
- **`L-BUCK-IN` qty 1 against `C-BUCK-IN` qty 2.** One LC and one bulk cap, or
  two LCs and a missing inductor.
