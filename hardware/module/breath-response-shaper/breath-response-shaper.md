# §4 Response control — `POT-RESP`, log ← linear → exp

*Moved verbatim from `hardware/module/breath-output-stage/breath-output-stage.md`,
2026-09-21, where it was a second `#`-level section inside that page; the `§4`
in the heading is the numbering it carried there. The panel-geometry block that
sat under `What it costs, and the decision it forces` is now
`hardware/module/panel/panel.md`.*

**Proposed 2026-09-21; adopted and fully drawn 2026-09-30.** Requested after the review wave, and independently
asked for by it: `B6` found that the nearest commercial equivalent
(ADDAC310 Pressure-to-CV) ships Response — exp ↔ lin ↔ log — alongside
slew, offset and gain, and that NuEVI ships thirteen curves and does not
default to linear. This module has two knobs and no shaping at all. `B6`
ranked that a High finding and noted "the module has two spare OPA2197
halves".

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| in-amp output | in | `module/breath-receive-stage` | `inamp-full-scale`, `breath-working-point` | The drawing's `in-amp out`. `R1` and the `2 × 10 k` divider that makes `V_in/2` both hang on it |
| `BREATH_SHAPED` | out | `module/breath-output-stage` | — | The restoring half's output, into `POT-GAIN` — the top of the gain attenuator — on `J-B2B-MOD` pin 1. Equal to the in-amp's output at centre detent. Where it inserts is argued below |
| `MODULE ANALOG +12V`, `MODULE ANALOG −12V` | in | `module/power-entry` | — | `U-RESP`'s two halves — the last two on the module |
| `AGND_MOD` | ref | `module/power-entry` | `dig-gnd-topology` | The module analog star. The `2 × 10 k` divider's bottom leg returns to it. It meets the module's other grounds only at the star — see the figure |
| `POT-RESP` | — | `module/panel` | `panel-width`, `panel-height-budget` | The third pot and the third knob — a panel cutout, not a net that leaves this circuit. What that costs the panel is on the panel page |

## The property the circuit is built around

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing: the
shaping half is drawn below, and the restoring half — `U-RESP` B with
`R-RESTORE-IN` 10 k and `R-RESTORE-FB` 20 k, ×2 inverting from `V_shaped` to
`BREATH_SHAPED` — is on the sheet.*


An inverting stage sits at a virtual ground. Span a pot between **a signal
that is `+V/2`** and **the stage's own output, which is `−V/2`**, and the
wiper voltage is

```
   V_wiper = (V/2) + p·(−V/2 − V/2) = (V/2)(1 − 2p)
```

which is **exactly zero at p = 0.5, for every input voltage**. So a
nonlinear branch hung off the wiper carries no current at all at centre
detent — **the stage is mathematically linear in the middle, not
approximately linear.** Turn either way and the wiper develops a voltage
proportional to the signal, which drives that branch into one leg or the
other.

```
                              R1 20k
   in-amp out ──┬──────────[====]────┬───── X (virtual gnd)
     (0…−9.94V) │                    │        │
                │   R2 10k           │        │
                │  ┌──[====]─────────┴────────┴──► V_shaped = −V_in/2
                │  │                          │
           [10k]│  │                     ┌────┴────┐
                ├──┼─────────────────────┤ ½ U-RESP│
           [10k]│  │                     └─────────┘
                │  │
               GND │
                │  │      POT-RESP 50k LINEAR
       V_in/2 ──┴──┼──────[===========]──────┘  (other end = V_shaped)
                   │            │
                   │          wiper
                   │            │
                   │        [R-RESP 15k]
                   │            │
                   └──────[▷|◁]─┴──► X          D-RESP, 1N4148 antiparallel
                        two diodes
```

**CW (wiper toward `V_in/2`)** → the branch injects extra *input* current
at high breath → gain rises with pressure → **expansive, "exponential"**.
Harder to get loud; more expression at the top.

**CCW (wiper toward `V_shaped`)** → extra *feedback* current at high breath
→ gain falls with pressure → **compressive, "logarithmic"**. Easier to get
loud; the top compresses.

**Centre detent** → wiper at 0 V → no diode current → **linear**, exactly.
This is the one place a centre detent is honestly warranted on this panel,
and unlike `POT-OFFSET` (whose detent the review found lands ~20° off its
true zero) this null is set by the topology, not by resistor tolerance.

## Scaling — and the mistake this nearly shipped with

The diode knee is fixed at ~0.6 V. **Where the playing range sits relative
to that knee is the entire design.** A first pass at ÷10 scaling was
checked and thrown out:

```
÷10:  hard blow 4.64 V at the in-amp → 0.464 V at the node
      knee is 0.6 V → the control does NOTHING until you overblow
```

At **÷2** the knee lands at about a quarter of a hard blow, so the curve
acts across the playing range rather than above it `[calc]`:

| Dynamic | In-amp | Node | `i_D` | Gain ratio |
|---|---|---|---|---|
| *pp* | 1.00 V | 0.50 V | 0 | **1.000** (below the knee — exactly linear) |
| *mp* | 2.50 V | 1.25 V | 43 µA | 1.347 |
| *mf* | 3.50 V | 1.75 V | 77 µA | 1.440 |
| hard blow | 4.64 V | 2.32 V | 115 µA | 1.494 |
| full scale | 9.94 V | 4.97 V | 291 µA | 1.586 |

## What this is, stated honestly

**A soft single-breakpoint shaper, not a true exponential law.** Below the
knee it is exactly linear; above it the gain rises smoothly toward ~1.6×
and then flattens, because once well past the knee the diode is just a
resistor. The character is *flat, then bend* — which is what most
"response" controls in this format actually are.

A mathematically exact exp/log law needs a matched log/antilog transistor
pair with tempco compensation, which is temperature-sensitive, needs a
matched pair and a tempco resistor, and is a great deal of trouble for a
breath curve. **Not recommended.** If more curvature is wanted later, the
cheap route is a *second* diode/resistor breakpoint biased through a
divider — two more parts per side, piecewise, and no thermal behaviour.

## What it costs, and the decision it forces

| | |
|---|---|
| Op-amp | **Both remaining OPA2197 halves** — one shapes at ÷2 inverting, one restores ×2 inverting to put scale and polarity back |
| Passives | `POT-RESP` 50 k lin (same part as `POT-GAIN`), `R-RESP` 15 k, `D-RESP` ×2 1N4148, R1 20 k, R2 10 k, divider 2 × 10 k |
| Panel | **A third pot and a third knob** |

## Settled before layout — 2026-09-30

- **The restoring half is drawn.** `U-RESP` B inverts `V_shaped` at
  −20 k/10 k = −2 (`R-RESTORE-IN`, `R-RESTORE-FB`), so the stage's gain is
  `(−R-RESP-FB/R-RESP-IN)·(−R-RESTORE-FB/R-RESTORE-IN)` = (−½)(−2) = **+1
  exactly at centre detent** `[calc]`, and its output `BREATH_SHAPED` feeds
  `POT-GAIN` in place of the in-amp's output.
- **Polarity, end to end** `[calc]`: the in-amp's output runs 0 → −9.94 V
  (`inamp-full-scale`) with breath; `V_shaped` = −½ × that, positive; the
  restoring half gives it back negative, as the in-amp had it. The output
  stage downstream is unchanged, so the jack's sense is unchanged.
- **Where it inserts** is between the in-amp and `POT-GAIN`, for the reason
  given above: the scale there is fixed by the in-amp, so the knee sits at a
  known fraction of full breath and the gain knob cannot move it.
- **Headroom.** At the full-exponential end the stage's gain ratio reaches
  1.586 at sensor full scale (the table above), so `BREATH_SHAPED` would be
  about −15.8 V and clips at the OPA2197's ~−11.5 V `[calc]`. Interpolating
  the table's ratio between a hard blow (1.494) and full scale (1.586), the
  clip starts near an in-amp output of −7.4 V (1.54 × 7.4 = 11.4), about 3/4
  of the sensor's range — beyond the ~2.8 kPa that real
  playing reaches (`breath-output-stage.md`). The linear and log settings
  never clip.
- **Diode matching** is not a requirement: breath is unipolar, so only one of
  the pair conducts in play; the second is there for the power-on and fault
  excursions. `D-RESP` is Vishay's `1N4148W` (row).
- **The pot** is Alpha's centre-click RV09 on the R0904N footprint
  (`POT-RESP` row).

## Still open

- **`R-RESP` at 15 kΩ is a first sizing**, targeting ~1.5× at a hard blow.
  It sets how strong "fully exponential" feels. **Decided by: E10**, with a
  real player and the sensor — 15 kΩ is what is fitted until then.
