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

> **That holds for an ideal `V/2` source, and the netlist's is not one.** The
> `R-RESP-DIV` pair is a 5 kΩ source and the pot loads it, so the wiper's zero
> lands about 5 % of the rotation clockwise of `p = 0.5` for every input, and
> at the detent itself the stage is linear within 0.4 % across real playing
> rather than exactly `[sim]` (the note under *Scaling*, `sim/README.md`).

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
                   │        [R-RESP 2.7k]
                   │            │
                   │        [TRIM-RESP 10k]     wiper strapped to its CCW end
                   │            │
                   └──────[▷|◁]─┴──► X          D-RESP, 1N4448W antiparallel
                        two diodes
```

**CW (wiper toward `V_in/2`)** → the branch injects extra *input* current
at high breath → gain rises with pressure → **expansive, "exponential"**.
More expression at the top.

**CCW (wiper toward `V_shaped`)** → extra *feedback* current at high breath
→ gain falls with pressure → **compressive, "logarithmic"**. The top
compresses.

**The knob changes the level as well as the shape.** The stage's gain is
above 1 at every breath level at CW (×1.12 at *pp* to `shaper-exp-gain` at a
hard blow) and below 1 at every level at CCW (×0.83 at *pp* to ×0.49 at a hard
blow) `[sim, sim/README.md, TRIM-RESP as commissioned]`. So **at a fixed GAIN setting, CW is louder at
every breath level and CCW quieter**; "harder to get loud" (CW) and "easier to
get loud" (CCW) describe the curve only once GAIN has been re-set to put a hard
blow back where it was. What that does one stage later, at the commissioned
gain, is `breath-chain-curve-clip`, and whether it should is open with the owner
(`breath-output-stage.md`, *Headroom*).

**Centre detent** → wiper at 0 V → no diode current → **linear**, exactly.
This is the one place a centre detent is honestly warranted on this panel,
and unlike `POT-OFFSET` (whose detent the review found lands ~20° off its
true zero) this null is set by the topology, not by resistor tolerance — to
within the divider's loading, which puts it about 14° off the click and costs
0.4 % of linearity at a hard blow `[sim]`.

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

> **Simulated 2026-09-30, and the table over-states the curve** (`sim/`). It
> computes the diode branch from a node at exactly `V_in/2`. On the netlist
> that node is the `R-RESP-DIV` pair's midpoint, a 5 kΩ source, and
> `POT-RESP`'s 50 kΩ track from it to `V_shaped` loads it to about 0.41 `V_in`
> at the CW end `[calc]`. The fully-exponential gain at a hard blow is
> `shaper-exp-gain`, not the 1.494 above, and the curve is not exactly linear
> below the knee (1.12× at *pp*, with `TRIM-RESP` as commissioned). The same loading moves the centre detent's
> null about 5 % of the rotation clockwise: at the detent the stage is linear
> within 0.4 % across real playing, not exactly — the diodes see a few
> hundred millivolts at full scale and barely conduct. The table is kept as the
> arithmetic it is; `sim/README.md` has the curve as netlisted.

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
| Passives | `POT-RESP` 50 k lin (same part as `POT-GAIN`), `R-RESP` 2.7 k and `TRIM-RESP` 10 k in series, `D-RESP` ×2 1N4448W, R1 20 k, R2 10 k, divider 2 × 10 k |
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
- **The diode branch is trimmed: `R-RESP` 2.7 kΩ fixed, `TRIM-RESP` 10 kΩ in
  series** (owner, 2026-10-01, *"with trimmer again?"*, pre-layout review A1-3).
  The owner requires at least 1.5× at a hard blow at the fully-exponential end
  (2026-09-30: *"need 1.5x gain"*), and no fixed value can hold it everywhere:
  the diode's guaranteed spread, the 1 % resistors, `POT-RESP`'s track and the
  temperature move that gain by more than the margin any one value leaves —
  the best fixed value held 1.5× at 27 °C and fell under it below about 20 °C.
  So each unit is set at commissioning (*Commissioning*, below) to
  `shaper-exp-gain`'s target, and the sim proves three things at every corner
  of the stage `[sim, sim/]`: the target is **reachable** — the trimmer's
  clockwise end is above it and its counter-clockwise end below it, from a
  15 °C to a 30 °C workshop; a unit trimmed there **holds the 1.5× floor at
  0 °C**; and the trimmer's strongest end still clips `BREATH_SHAPED` only
  past 1.3× a hard blow (*Headroom*, next). The table above (*Scaling*) was
  sized at 15 kΩ on unloaded arithmetic and is kept as that arithmetic.
- **`TRIM-RESP` fails safe.** Its wiper is strapped to its counter-clockwise
  end, so clockwise lowers the branch's resistance and raises the gain — the
  panel knob's sense — and an open wiper leaves the whole track in series:
  the exp end then bends *less* (the trimmer's CCW end, `sim/`), never more. A
  track that opens altogether takes the branch out and leaves the stage
  linear. It is a Bourns 3296X, sealed, 25-turn and side-adjust (`TRIM-RESP`
  row), at the main board's side edge with the other trimmers, set with the
  module out of the rack (ADR 0024, *The calibration trimmers are
  side-adjust*).
- **Where it inserts** is between the in-amp and `POT-GAIN`, for the reason
  given above: the scale there is fixed by the in-amp, so the knee sits at a
  known fraction of full breath and the gain knob cannot move it.
- **Headroom.** At the full-exponential end `BREATH_SHAPED` clips at the
  OPA2197's rail before the in-amp reaches its full scale. Where it starts is
  `shaper-exp-gain` `[sim]` (`sim/`): about three-quarters of the sensor's range
  as commissioned, and at least 1.3× a hard blow at every corner — at 40 °C,
  and with `TRIM-RESP` at its strongest end as well as where it is set,
  where a hard blow is the 2.8 kPa candidate of the disputed
  `breath-working-point` (open until E2; at its 3–4 kPa candidate the nominal
  clip is within 5 % of a hard blow). The linear and log settings never clip
  here. **That is `BREATH_SHAPED` only:** one stage later, at the GAIN
  commissioning sets, the exp end puts the jack on the rail inside real
  playing — `breath-chain-curve-clip`, and *Headroom* on
  `breath-output-stage.md`.
- **Diode matching** is not a requirement: breath is unipolar, so only one of
  the pair conducts in play; the second is there for the power-on and fault
  excursions. `D-RESP` is Vishay's `1N4448W` (row): the part whose
  guaranteed forward-voltage window the 1.5× floor is simulated against.
- **The pot** is Alpha's centre-click RV09 on the R0904N footprint
  (`POT-RESP` row).

## Still open

- **How strong "fully exponential" feels is E10's to judge, with a real
  player and the sensor** — but not below 1.5× at a hard blow: the owner set
  that floor on 2026-09-30, and `TRIM-RESP` is set to hold it
  (`shaper-exp-gain`, `sim/`). A stronger curve is a higher target, within the
  trimmer's clockwise end, and it moves the clip earlier.
- **"A hard blow" is a candidate, not a measurement.** The 1.5× floor, the
  clip margin, the trimmer's range and the commissioning point are all
  evaluated at an in-amp output of −4.64 V, which is `breath-working-point`'s
  2.8 kPa candidate. E2 decides it; the range is re-checked then
  (`shaper-exp-gain`, `conditional_on`).

## Commissioning — `TRIM-RESP`

Once, at build (ROADMAP E10), after `TRIM-BREATH-ZERO` and before the panel
GAIN — on the bench with the module out of the rack, where the trimmers on the
main board's rear face can be reached, at room temperature (the sim covers a
15–30 °C workshop):

1. **`POT-RESP` fully clockwise.** The trim acts on the exp end only; at the
   centre click the branch carries almost no current.
2. **Hold the in-amp at a hard blow with a known DC, not a breath.** With the
   instrument unplugged, drive the umbilical's breath pair — `BREATH_SENSE`
   against `AGND_SENSE` (`umbilical-pinmap`) — from a bench supply through a
   breakout, and raise it until the in-amp's output reads −4.64 V
   (`breath-working-point`'s candidate) at `R-RESP-IN`'s input end. A breath
   cannot be held to the 1 % this needs; a supply can, and the ratio below
   does not care what pressure a volt stands for.
3. **Turn `TRIM-RESP` until `BREATH_SHAPED` reads the target times that
   voltage** — `shaper-exp-gain`'s target, read at `U-RESP` pin 7 (or
   `R-RESTORE-FB`'s output end). Clockwise raises it. One meter, two readings:
   both are DC.
4. Note the temperature. The sim's corners assume 15–30 °C; outside that,
   re-check against `sim/`.

`TRIM-RESP` ranges from about 2.7 kΩ to 12.7 kΩ in the branch; a unit that
cannot reach the target from either end is outside every simulated corner,
and the first suspect is `POT-RESP`'s track (measure it, CW lug to CCW lug).
