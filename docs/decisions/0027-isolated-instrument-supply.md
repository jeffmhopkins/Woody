# 0027 — The instrument's supply is isolated, drawn rail to rail

**Status:** Accepted, 2026-09-30. Decided by the owner's requirement, the
design chosen here: *"There needs to be another way to avoid the breath
affecting pitch. This is unacceptable. We are powering the controller through
the rack, there has to be a valid way to do this."* Numbering: 0025 and 0026
are taken on other branches (the instrument's drop-in module, the panel
graphics), so this is 0027. **Amended 2026-10-01**, three times (the
converter's common-mode current; the choke is fitted; the `INST_POS12` range
is accepted), the *Amendment* sections below.

**Amended 2026-09-30 — `U-ISO` is RECOM's RPA20-2412SAW.** The owner: *"I
thought the point was to do a RECOM that was in stock."* It replaces the
MORNSUN URB2412YMD-15WR3 in point 1 below, on the same land pattern — same
six hole positions, the same function in each; RECOM numbers the pins
differently `[ds datasheets/discrete-and-power/RECOM-RPA20-AW.pdf PD-8]`. It
is in stock: DigiKey `RPA20-2412SAW-ND`, 20 on the shelf, $53.19 `[web
DigiKey 2026-09-30]`. Why not the other two:

- **MORNSUN URB2412YMD-15WR3** — DigiKey lists it "not for new designs" with
  one in stock, and the part under that MPN at LCSC is another brand `[web
  DigiKey, LCSC 2026-09-30]`.
- **RECOM RP20-2412SAW** — the RPA20's named successor, and Active, but none
  on DigiKey's shelf: eight expected 16-Dec-2026, 11 weeks from the maker,
  $91.76 `[web DigiKey 2026-09-30]`.

**The RPA20 is end-of-life.** Every page of its datasheet is bannered *"NOT
RECOMMENDED FOR NEW DESIGNS — LAST TIME BUY: 6TH JULY 2026"*
`[ds RECOM-RPA20-AW.pdf PD-1]`, and DigiKey lists it Obsolete. **Buy spares
now**, while the 20 last. **The future supply is the RP20-2412SAW**, and the
footprint is drawn for it too (`woody:Converter_DCDC_RECOM_RPA20-RP20-xxxxSAW_THT`):
it drops into the same holes with the same function in each `[ds
RECOM-RP20-AW.pdf PD-6]`; only its numbering differs (its −Vout is pin 6 and
+Vout pin 4, the RPA20's 4 and 6, and it has no Trim pin), so moving to it
swaps two pad numbers in the footprint and symbol and changes no copper. It
differs electrically, and those deltas are re-checked then: its over-load
protection is 150 % *typical* with no minimum published `[PD-4]` against the
RPA20's 110 % minimum, its isolation capacitance 1500 pF max `[PD-4]`, its
body 9.9 mm tall `[PD-6]`.

What moved with the part is on `power-entry.md` (*The instrument's supply*)
and in the consequences below; the decision itself — isolated, rail to rail —
did not move.

## Context

The instrument is powered from the rack, down the umbilical, through the
module's load switch (ADR 0005). Until this decision the load switch took the
Eurorack **+12 V** and the instrument's current came back on `PWR_GND` to the
module's star, **out through the power ribbon's ground conductors and along
the bus board** to the rack's supply.

That current is breath-correlated: the instrument's lights follow breath
(ADR 0014), and since the owner's change of 2026-09-30 they are thirteen
WS2815B-V1 on the main board, `led-row-current` at 12 V full white (owned by
`led-strip-drive.md`; cited since 2026-10-01, A4-10). Every CV output of the module is a voltage
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
| Cost in power | the converter's loss, ~0.95 W, in the module | none | **2.3 W** (0.195 A × 12 V) to 4.4 W burned all the time, **inside the sealed wooden body**, which ADR 0005 already puts at 4.1 W |
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

1. **`U-ISO`, a RECOM RPA20-2412SAW** (20 W, 9–36 V in, 12 V at 1.67 A,
   1.6 kVDC; the plain part, no CTRL pin, Trim left open) `[ds
   datasheets/discrete-and-power/RECOM-RPA20-AW.pdf PD-1, PD-5]` — amended
   2026-09-30, above — on `module/power-entry`. Its **input is across the rack's +12 V and −12 V**
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
   over-current protection starts at 110 % of 1.67 A, 1.84 A `[ds PD-5]`,
   above the LT1641's 1.10 A worst-case trip, so the LT1641 decides every
   start and every fault **except a replug inside `Q-INRUSH`'s window**,
   whose first edge reaches the converter's own threshold
   (`hotplug-iso-ocp`; *Consequences*, the A4-9 amendment). *(Amended
   2026-10-01, pre-layout review A3-1.)*
3. **`PWR_GND` is the isolated return.** It is `U-ISO`'s 0V, the load
   switch's ground and the umbilical's pin 6, on its own layer-4 copper. It
   joins `DIG_GND` at the etherCON through `NT-UMB-MOD` (pins 6 and 8, the
   mirror of the instrument's `NT-DIG`, ADR 0018), and the two reach the
   Eurorack ground only through `NT-DIG-MOD` at the star. The star itself is
   now a net of its own inside `module/power-entry`, `BUS_GND`. This is the
   tracked figure `dig-gnd-topology`.
4. **`C-ISO-Y`, 1 nF across the barrier at the converter** (`ISO_VIN_POS` to
   `PWR_GND`), gives the switching common-mode current, driven through the
   converter's isolation capacitance (1100 pF typ `[ds PD-5]`), a way home beside
   the converter instead of round the star and the ribbon. *(Amended
   2026-10-01, A4-1: at 1 nF it does not — see* The converter's common-mode
   current *below. Decided by the owner the same day:* **`L-CM-ISO`, a 1 mH
   common-mode choke at the converter's input, and `C-ISO-Y` at 22 nF** *—
   the second amendment, below.)*
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
| The ±12 V rails at the header move by 9.7 mV (0.195 A swing) as `U-ISO`'s input current follows breath `[sim, rail_mv]` | OPA2197 at 3 µV/V worst `[SBOS737C p.8]` → 29 nV → **0.00003 cents**; `U-REG-DAC` (the LT3042 since 2026-10-01, at most 0.108 mV/V `[ds ADI-LT3042.pdf p.3; calc]`) passes 1.0 µV to `DAC_AVDD`, which does not set full scale (ADR 0005) |
| `U-ISO`'s switching, 550 kHz `[ds PD-2]` | out of band, behind the input filter — see `power-entry.md`. Its common-mode part is behind `L-CM-ISO` and goes home through `C-ISO-Y`: under 10 % of it crosses the star at every corner `power-entry/sim`'s `cm-loop` sweeps (amendments 2026-10-01, below) |
| The LED row's PWM, ~2 kHz scan and ~4 kHz refresh `[ds WS2815B-V1.pdf p.1]` | not breath-correlated in level but in the audio band, reflected through `U-ISO` and its input filter onto the case's ±12 V — an audible-band tone for other modules. **Simulated** (`power-entry/sim` `led-pwm`, amended 2026-10-01): the filter has no gain in the band and the instrument's bulk keeps half the row's current, so the rails and the pitch jack move by `led-pwm-rail-ripple` (`power-entry.md`, *The LED row's PWM*), not the review's ~13 mV bound (A4-13). That pitch figure is the jack against the module's own ground. A receiving module at the PSU end of the bus sees `led-pwm-pitch` (`interfaces/system/sim`, the whole system in one deck): about half of it is the jack board's ground moving under the receivers' as the ripple's return current splits between the ribbon and the patch-cable sleeves. At its worst corner it is over this section's 0.01 cents, and still more than fifty times under `pitch-cents-budget`. E6 scopes it |

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
  `umbilical-current` × 12 V ≈ 4.3 W out of `U-ISO`, ~82 % efficient at that
  load `[ds PD-3]`, from ~23.4 V → **~0.22 A on each of +12 V and −12 V**
  `[calc]`, where it was ~0.36 A on +12 V and none on −12 V. The module's own
  analog load adds `module-own-draw`. At the clamp-legal worst (ADR 0005)
  it is ~0.37 A per rail; an overload the load switch holds just under its
  0.78 A minimum trip is ~0.49 A per rail; a hot-plug start draws up to
  ~0.68 A per rail for tens of milliseconds. *(Amended 2026-10-01, A4-9: that
  hot-plug is the one `Q-INRUSH` removed on 2026-09-30. A hot-plug now draws
  `U-ISO` at `hotplug-iso-ocp`, about the clamp-legal load. What remains above
  it is brief: a replug within tens of milliseconds (`replug-early`,
  `power-entry-instrument/sim`) holds `U-ISO` at its over-current clamp for
  0.1–0.45 ms, ~1.2 A per rail `[calc: 1.84 A × 12 V / 0.85 / 22.2 V]`, and a
  `Q-INRUSH` short, which the LT1641's timer is sized for.)* **Check the case's −12 V
  rating** — many Eurorack supplies give −12 V less than +12 V. The rack
  total rises by the converter's ~0.95 W loss.
- **The module dissipates ~1.05 W more**: `U-ISO` ~0.95 W, `D2`/`D4` ~0.1 W.
- **A mechanical item for the module CAD**: `U-ISO` is 25.4 × 25.4 mm and
  **10.2 mm tall on 5.6 mm pins** `[ds PD-7, PD-8]`, too tall for the gap between
  module-main and the jack board, so it goes on module-main's **rear face**
  with `L-ISO-IN`, `C2`, `C-ISO-IN`, `C-ISO-OUT` beside it; the envelopes are
  `config/module.yaml`'s. *(Amended 2026-10-01: and `L-CM-ISO`, 21.6 mm over
  its terminals and 11.43 mm tall, between `L-ISO-IN` and the converter's
  input pins — its envelope is not in `config/module.yaml` yet.)*
- **Supply**: the RPA20-2412SAW is end-of-life, 20 at DigiKey on
  2026-09-30 — **buy spares with the first order**. The RP20-2412SAW is the
  path after that, on the same footprint, with its lead time (11 weeks on
  2026-09-30) as the schedule risk (above).
- **The instrument must have no other path to the rack's ground.** A USB lead
  to a computer while the umbilical is plugged in (ADR 0005's bench-only OR)
  joins the isolated return to mains earth; the instrument's current still
  returns to the converter, but the computer's ground loop is back. Bench
  only, as ADR 0005 already says.
- **What the bench checks (E6/E11)**: the pitch jack against a second
  module's ground with the lights sweeping full scale — the measurement this
  decision predicts at under a hundredth of a cent — and the case's −12 V
  under the instrument's load. *(Amended 2026-10-01: and, with the
  instrument drawing, a probe at 550 kHz on `AGND_MOD` against `BUS_GND` and
  on the pitch jack (A4-1, below), and the case's +12 V and −12 V at 2–4 kHz
  with the LED row at mid brightness (A4-13).)*

## Amendment, 2026-10-01 — the converter's common-mode current

From the pre-layout review (`docs/review/2026-10-01-pre-layout-review/`,
A4-1, verified in `VERIFIED-F3.md`).

**Point 4 claimed `C-ISO-Y` gives the switching common-mode current a way
home beside the converter. At 1 nF it does not.** The netlist gives that
current a second loop from `PWR_GND` back to the converter's input that never
passes through `C-ISO-Y`: `NT-UMB-MOD` → `DIG_GND` → `NT-DIG-MOD` → `BUS_GND`
→ `NT-AGND-MOD` → `AGND_MOD` → `C3` → `FB3` → `D3` → `PTC-NEG12` → `D4` →
`FB4` → `ISO_VIN_NEG` (`module/power-entry/netlist.yaml`), and in parallel out
through the ribbon to the rack's own decoupling and back on its ground. Every
diode in it carries forward current, so it conducts AC. At 550 kHz
`C-ISO-Y` is 289 Ω `[calc]`; that loop is a few ohms of bead, diode and
capacitor.

**An AC deck of the loop** (`docs/review/2026-10-01-pre-layout-review/F3-u-iso-cm-loop/`,
ngspice, unit common-mode drive through the 1100 pF; the beads from the
MI1206K601R-10's curve at their DC bias, the electrolytics with ESR and ESL,
the ribbon at 0.1–1 µH a conductor — every parasitic an estimate, marked in
the deck) gives, **as netlisted**:

| | 550 kHz | 1.65 MHz | 5.5 MHz |
|---|---|---|---|
| through `C-ISO-Y` | 1–2 % | 12–24 % | resonant |
| across the star (`BUS_GND` ↔ `DIG_GND`) | 88–98 % | ~100 % | 19–136 % |
| of which through `AGND_MOD` (`C3`, `C1`) | 12–43 % | 26–53 % | 39–262 % |

Shares above 100 % are circulating current in a resonance of `C-ISO-Y` with
the loop's inductance. **The review's direction is confirmed and its 95 %
reproduced.** How much current that is, RECOM does not publish (no Y-capacitor
or choke in its filter, `[ds PD-7]`), and whether it matters depends on where
`C1` and `C3` land against the analog block on `AGND_MOD`, which is a layout
fact that does not exist yet.

**Simply making `C-ISO-Y` bigger is worse, not better.** 10–47 nF puts the
loop's series resonance on the fundamental or its third harmonic: at 47 nF
the star carries three times the drive current at 550 kHz. Damping it helps
only at hundreds of nanofarads.

**OWNER — choose before the module layout** (the module's sheet is not this
fixer's to change, and nothing has been changed):

1. **A common-mode choke at `U-ISO`'s input**, between the converter's input
   capacitors (`C2`, `C-ISO-IN`, with `C-ISO-Y` on the converter's side) and
   `L-ISO-IN`/`FB4`. With ~1 mH common-mode the star's share falls to ~8 % at
   550 kHz with `C-ISO-Y` at 1 nF, and under 1 % with 10 nF. One two-line SMD
   choke rated above the converter's input current (≥ 1 A; the replug clamp
   is brief), roughly $0.5–1.5 `[from memory]`, to be chosen and banked. Its
   leakage inductance joins `L-ISO-IN`, so the input filter's damping
   (`power-entry.md`) is re-simulated with it. **Recommended.**
2. **`C-ISO-Y` 220 nF with ~1 Ω in series** (and the twin from `ISO_VIN_NEG`
   if wanted): no new magnetics, the star's share ~45 % at 550 kHz and under
   10 % above it. Two passives; a partial cure.
3. **Leave it and measure** at E6/E11 (the probe in *Consequences*). Cheapest
   now; a respin if it shows.

Moving `C1`/`C3`'s grounds onto `BUS_GND` (the review's second option) takes
the current off `AGND_MOD` but not off the star, so it is not listed alone.

## Amendment, 2026-10-01 (owner) — the choke is fitted

The owner chose option 1 above: **a common-mode choke at `U-ISO`'s input.**

- **`L-CM-ISO`, Bourns PM3700-40-RC** — 1.0 mH minimum, 4 A, 0.020 Ω a
  winding, 3.9 µH leakage, 20 dB from 500 kHz to 40 MHz, SMD, LCSC C2662215
  `[ds datasheets/discrete-and-power/BOURNS-PM3700-CM-CHOKE.pdf p.1]` —
  between the input filter (`L-ISO-IN`, `FB4`) and the converter's pins, one
  winding in each leg, so the supply current and its return cancel in the
  core. 4 A against `PTC-ISO`'s 1.5 A trip: nothing the fuse passes heats it.
- **`C-ISO-Y` is 22 nF C0G**, not 1 nF and not the 10 nF the review's deck
  suggested. That deck modelled the choke as a lossless 1 mH; a ferrite at
  550 kHz is lossy, and its datasheet gives only the 20 dB band. With the core
  loss swept to 500 Ω a winding, 10 nF leaves ~11 % on the star and 22 nF
  under 6 %. With the choke in the loop there is no resonance left for a
  larger `C-ISO-Y` to find.
- **What holds it**: `module/power-entry/sim`, `cm-loop` — the share of the
  converter's common-mode current crossing the star is under the owner's
  10 % at 550 kHz, 1.65 MHz and 5.5 MHz and anywhere from 500 kHz to 30 MHz,
  at every corner of the choke's core loss and inductance, the ribbon and
  `C-ISO-Y` (0.6–5.4 % at the fundamental); `cm-loop-y-1n` records the 1 nF
  case failing. `iso-input-z` runs the input filter with the choke's leakage
  in it: still damped, over 20× inside the converter's −104 Ω at every corner.
  The copper in both decks is estimated, as in the review's.
- **What is still open**: how much current the converter makes (RECOM does
  not publish it) — E6's probe on the star stands; and the choke's place on
  module-main, which the module CAD has not given it yet.

## Amendment, 2026-10-01 (owner) — `INST_POS12` between 13.5 V and 16.7 V is accepted

Pre-layout review A4-4: nothing clamps the instrument's rail between the
WS2815B-V1's 13.5 V absolute maximum `[ds WS2815B-V1.pdf p.2]` and `D-TVS-PWR`'s
16.7 V minimum breakdown; only a converter failing high would put it there,
and `U-ISO`'s own over-voltage protection starts at 13.8 V `[ds
RECOM-RPA20-AW.pdf PD-5]`. **The owner accepts it, 2026-10-01: no part is
added.** A converter that fails regulating high is out of this design's
scope; the LED row is what it would damage. The crowbar and the lower TVS
that were weighed are in `docs/review/2026-10-01-pre-layout-review/VERIFIED-F3.md`.
