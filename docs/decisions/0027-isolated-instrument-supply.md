# 0027 — The instrument's supply is isolated, drawn rail to rail

**Status:** Accepted, 2026-09-30. Decided by the owner's requirement, the
design chosen here: *"There needs to be another way to avoid the breath
affecting pitch. This is unacceptable. We are powering the controller through
the rack, there has to be a valid way to do this."* Numbering: 0025 and 0026
are taken on other branches (the instrument's drop-in module, the panel
graphics), so this is 0027.

## Context

The instrument is powered from the rack, down the umbilical, through the
module's load switch (ADR 0005). Until this decision the load switch took the
Eurorack **+12 V** and the instrument's current came back on `PWR_GND` to the
module's star, **out through the power ribbon's ground conductors and along
the bus board** to the rack's supply.

That current is breath-correlated: the instrument's lights follow breath
(ADR 0014), and since the owner's change of 2026-09-30 they are thirteen
WS2815B-V1 on the main board, 170–195 mA at 12 V full white `[owner brief
2026-09-30, not yet in the corpus]`. Every CV output of the module is a voltage
above the module's star; the receiving module (the VCO the pitch jack drives)
reads it against *its* ground, which is the bus at its own tap. The drop the
instrument's current makes between the two is in series with the pitch CV.

Three reviews found it in 2026-09-21 (`power-entry.md` carried their table:
7.4 cents for the ribbon, 8–18 cents for the bus board), and
`pitch-cents-budget` excludes it by name. Simulated now
(`hardware/module/power-entry/sim/`, `gnd-before`), with the rack's copper as
parameters with their provenance:

| Breath swing | Receiver in the next slot | Receiver at the PSU end of a 0.25 m bus |
|---|---|---|
| 0.195 A (the new LEDs) | **4.2 cents** | **11.2 cents** |
| 0.367 A (ADR 0005's quiescent → clamp-legal worst) | **7.9 cents** | **21.1 cents** |

`[sim; r_rib_gnd 17 mΩ, r_bus_seg 1–31 mΩ — sims.yaml gives each source;
1 cent = 1/1200 V at 1 V/oct]`. Against a pitch stage whose whole thermal
budget is `pitch-cents-budget`, this is an order of magnitude larger, and
because it follows breath it is heard as the instrument doing something, not as
noise.

The requirement kept: **the controller is powered through the rack.**

## Options

**(a) An isolated DC/DC for the instrument, its input across +12 V and −12 V.**
The instrument's power is drawn from the rack as a current that leaves on the
+12 V rail and returns on the −12 V rail: the rack's supply sources it from
+12 V and sinks it into −12 V, and **its ground carries none of it**. The
converter's output is a floating 12 V whose return is the umbilical's
`PWR_GND`, tied to the module's ground at one point so the SPI and breath
signals keep a common reference — with no DC current in the tie, because the
instrument's current has nowhere to go but back to the converter.

**(b) A ground sense.** One of the ribbon's six ground conductors left
unconnected at the module and used, current-free, as the pitch reference.

**(c) A constant instrument current.** A dummy load in the instrument that
burns whatever the LEDs do not, so the total never moves.

| | (a) isolated supply | (b) ground sense | (c) balanced load |
|---|---|---|---|
| Breath-correlated pitch error, 0.195 A swing `[sim]` | **< 10⁻⁷ cents** in the model; **< 0.01 cents** with what the model leaves out (below) | 0.23 cents next slot, **7.3 cents** at the PSU end | 0.04–0.11 cents at 1 % balance |
| Same, 0.367 A swing `[sim]` | same | 0.44 / **13.7 cents** | 0.08–0.21 cents |
| Removes the ribbon term | yes | yes | yes |
| Removes the bus-board term | **yes** | **no** — the sense line ends at this module's tap, not the receiver's | yes |
| Cost in power | the converter's loss, ~0.7 W, in the module | none | **2.3 W** (0.195 A × 12 V) to 4.4 W burned all the time, **inside the sealed wooden body**, which ADR 0005 already puts at 4.1 W |
| Rack budget | −12 V now carries the instrument (below) | unchanged | +12 V always at its worst |
| Parts | a converter, a filter, three fuses' worth of protection — module only | none, but one fewer ground conductor (+20 % ribbon resistance) and a non-standard reference | a current regulator and a heat sink in the instrument |
| Depends on the receiver's position in the case | no | **yes** | no |

**(b) cannot work alone** — its residual is exactly the bus-board term, which
is the larger one and the one that depends on where the owner patches.
**(c) works**, at the price of heat where heat is least wanted and a rack draw
pinned at worst case. **(a) is chosen.** It removes both terms at their source
rather than compensating for them, it lives entirely in the module, and its
cost is a converter the size of a postage stamp.

## Decision

1. **`U-ISO`, a MORNSUN URB2412YMD-15WR3** (15 W, 9–36 V in, 12 V at
   1.25 A, 1500 VDC) `[ds datasheets/discrete-and-power/MORNSUN-URB_YMD-15WR3.pdf]`,
   on `module/power-entry`. Its **input is across the rack's +12 V and −12 V**
   (24 V nominal): +12 V through `PTC-ISO`, `D2`, `FB2` and `L-ISO-IN`; −12 V
   through `D4` (cathode to the bus, like `D3`) and `FB4`; `C2` (100 µF 50 V
   electrolytic) and `C-ISO-IN` (4.7 µF) across it. Its output, `ISO_POS12`,
   feeds the load switch; its return is `PWR_GND`.
2. **The load switch moves to the converter's output.** `U-LOADSW`'s `VCC`,
   `R-ILIM` and the `ON` divider are on `ISO_POS12`, and every value on
   `umbilical-load-switch.md` is unchanged: the instrument still sees an
   LT1641 that latches on a fault, ramps a cold start and limits a hot-plug.
   On the input side it would see only the converter's hiccup, which is
   auto-retry — the behaviour ADR 0005 rejected. The converter's own
   over-current protection starts at 110 % of 1.25 A `[ds p.2]`, above the
   LT1641's 1.10 A worst-case trip, so the LT1641 decides every start and
   every fault.
3. **`PWR_GND` is the isolated return.** It is `U-ISO`'s 0V, the load
   switch's ground and the umbilical's pin 6, on its own layer-4 copper. It
   joins `DIG_GND` at the etherCON through `NT-UMB-MOD` (pins 6 and 8, the
   mirror of the instrument's `NT-DIG`, ADR 0018), and the two reach the
   Eurorack ground only through `NT-DIG-MOD` at the star. The star itself is
   now a net of its own inside `module/power-entry`, `BUS_GND`. This is the
   tracked figure `dig-gnd-topology`.
4. **`C-ISO-Y`, 1 nF across the barrier at the converter** (`ISO_VIN_POS` to
   `PWR_GND`), gives the switching common-mode current, driven through the
   converter's 2000 pF isolation capacitance `[ds p.3]`, a way home beside
   the converter instead of round the star and the ribbon.
5. **The rails get fuses** (owner, same day: *"You're good to add the
   PTCs"*): `PTC-POS12` and `PTC-NEG12` on the module's analog rails, and
   `PTC-ISO` on the converter's +12 V leg, all at the header, ahead of the
   reverse diodes. Sizing is `power-entry.md`'s.

## What is left, and the residual

The model (`gnd-isolated`) shows no breath-correlated current in the rack's
ground at all — **< 3 × 10⁻⁸ cents** and **< 0.3 nA** in the tie, the latter
the isolation capacitance at breath frequency. What the model leaves out, each
`[calc]`, 1 cent = 0.833 mV:

| Residual | Size |
|---|---|
| The module's own CV outputs driving their receivers: the breath jack's 0–10 V into 100 kΩ is 0.1 mA, returning through the bus between the receiver and the PSU | 0.1 mA × 48 mΩ (ribbon + whole bus) = 4.8 µV → **0.006 cents** — the module's own signal, not the instrument's supply |
| The ±12 V rails at the header move by 9.3 mV (0.195 A swing) as `U-ISO`'s input current follows breath `[sim, rail_mv]` | OPA2197 at 3 µV/V worst `[SBOS737C p.8]` → 28 nV → **0.00003 cents**; the LM317 at 0.02 %/V passes 1.9 µV to `DAC_AVDD`, which does not set full scale (ADR 0005) |
| `U-ISO`'s switching, 270 kHz at full load and lower below half load `[ds p.3]` | out of band; its reflected ripple current is 30 mA into the input filter `[ds p.2]` — see `power-entry.md` |

**Residual breath-correlated pitch error: under 0.01 cents**, with the rack's
copper as `sims.yaml` states it, the new LEDs' swing, and the receiver
anywhere on the bus. That is below `pitch-cents-budget` by two orders.

**What it is not**: a claim about a shield. The etherCON shells are plastic
and their G tabs are on no net (ADR 0021, ADR 0023), so the cable-shield row
of the old table does not apply. And the static part — the module's own
~50 mA of analog current through the ribbon's ground, about 1 mV — is
constant; it is part of what the owner tunes out, as in every Eurorack module.

## Consequences

- **The rack's −12 V now carries the instrument.** Typical play:
  `umbilical-current` × 12 V ≈ 4.3 W out of `U-ISO`, ~86 % efficient at that
  load `[ds p.4]`, from ~23.4 V → **~0.21 A on each of +12 V and −12 V**
  `[calc]`, where it was ~0.36 A on +12 V and none on −12 V. The module's own
  analog load adds ~45 mA and ~40 mA. At the clamp-legal worst (ADR 0005)
  it is ~0.36 A per rail; an overload the load switch holds just under its
  0.78 A minimum trip is ~0.48 A per rail; a hot-plug start draws up to
  ~0.68 A per rail for tens of milliseconds. **Check the case's −12 V
  rating** — many Eurorack supplies give −12 V less than +12 V. The rack
  total rises by the converter's ~0.7 W loss.
- **The module dissipates ~0.8 W more**: `U-ISO` ~0.7 W, `D2`/`D4` ~0.1 W.
- **A mechanical item for the module CAD**: `U-ISO` is 25.4 × 25.4 mm and
  **11.7 mm tall** above module-main `[ds p.3]`, and `L-ISO-IN`, `C2`,
  `C-ISO-IN`, `C-ISO-OUT` sit beside it. Where it goes on the board, against
  the jack board's clearance, is `config/module.yaml`'s to decide — not
  decided here.
- **Supply**: MORNSUN's datasheet is current (rev 2025.03.28-A/9), but
  DigiKey marks the part "not for new designs" with one in stock
  `[web DigiKey 2026-09-30]`, and the part under that MPN at LCSC is a
  different brand. `U-ISO`'s row names two alternates, each needing its own
  footprint. **Decided by: owner** — buy the MORNSUN part through a MORNSUN
  distributor, or move to an alternate before layout.
- **The instrument must have no other path to the rack's ground.** A USB lead
  to a computer while the umbilical is plugged in (ADR 0005's bench-only OR)
  joins the isolated return to mains earth; the instrument's current still
  returns to the converter, but the computer's ground loop is back. Bench
  only, as ADR 0005 already says.
- **What the bench checks (E6/E11)**: the pitch jack against a second
  module's ground with the lights sweeping full scale — the measurement this
  decision predicts at under a hundredth of a cent — and the case's −12 V
  under the instrument's load.
