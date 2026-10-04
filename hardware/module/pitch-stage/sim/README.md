# Pitch stage — simulation

`sims.yaml` says what is simulated and what every run must show;
`pitch-stage.lib` is the stage, as one subcircuit; `pitch-dc.cir`,
`pitch-step.cir` and `pitch-loop.cir` are the decks that place it;
`results.yaml` is what the last run found, **generated** by
`python3 tools/sim.py run hardware/module/pitch-stage/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read this circuit's netlist and,
for the loads a passive mult joins to `PITCH`, the other outputs' jack parts:
`mod-channels`' `C-FILT-MOD-1` and `R-OUT-PROT-1`, `breath-output-stage`'s
`C-OUT-BREATH`. Both op-amp halves are TI's OPA2197 model, banked in
`datasheets/analog/`.

## The stage, as netlisted

`pitch-stage.lib` is every part between `VREFOUT`, the DAC pin and the jack:
`TRIM-OFFSET` as its two halves about the wiper (`w_offset`), `R-VREF-SER`,
`R-VREF-INJ`, the follower at gain 1 + `R-VREF-FB`/`R-VREF-GND`,
`R-GAIN-CTR`, `RN-PITCH`'s R1 and R2, `TRIM-GAIN`'s CCW–wiper section
(`t_gain`; its CW end is strapped to the wiper), `R-OPAMP-IN`/`C-AA-PITCH`,
`C-FB-PITCH`, `R-OUT-PROT` and `C-FILT-PITCH`. Both trims sit at mid-travel
unless a sim says otherwise. `VREFOUT` is an ideal 2.5 V source.
`D-JACK-CLAMP` is in since 2026-10-03 (#5 finding 6): two diodes fitted to
the BAV99's maximum V_F, on the op-amp side of `R-OUT-PROT`. It is
reverse-biased everywhere but under abuse, and `patch` and `short` measure it.
`pitch-loop.cir` needed `gminsteps=100` to find its operating point with it.

**Every deck places the stage twice**, `XA` with `D-ESD-PITCH` on its jack and
`XB` without, on the same sources and the same load, so the clamp's effect is
one subtraction in the same run. `D-ESD-PITCH` is its datasheet capacitance,
16 pF typ, taken to twice that at the corners (no maximum is published), and
its leakage at the 15 V standoff as 300 MΩ `[ds NEXPERIA-PESD15VL1BA.pdf p.4]`.

## What it shows

| Sim | What | Holds |
|---|---|---|
| `dc-transfer` | the transfer over the DAC's 0.25–4.75 V window into a VCO | gain 2.000 and intercept −2.500 V within 1 mV at mid-travel; **`D-ESD-PITCH` moves the jack by under 1 µV** |
| `trim-gain-ccw`, `-cw` | `TRIM-GAIN` at 0 Ω and 200 Ω | the gain is `1 + R2/(R1 + R-GAIN-CTR)` and `1 + (R2 + 200 Ω)/(R1 + R-GAIN-CTR)`: 1.990 and 2.010, ±1 % |
| `trim-offset-ccw`, `-cw` | `TRIM-OFFSET`'s wiper at either end | `V_ref` is the page's formula at w = 0 and w = 1: −60 / +50 mV about 2.500 V |
| `step-vco[c_cable=…]` | an octave step into a VCO and 0, 200 pF, 800 pF or 2.2 nF on the jack beyond `C-FILT-PITCH` | under 5 % overshoot at every corner (4.8 % worst, at 2.2 nF); **`D-ESD-PITCH` changes it by under 0.1 point** |
| `step-vco-heavy[c_cable=…]` | the same at 4.7, 10 and 22 nF (#5 finding 1) | **a recorded limit**: over 5 % at the nominal and worst corner — 6.2 % at 4.7 nF (5.0 % at its best corner); 11 % and 20 % at 10 and 22 nF, nominal |
| `dc-transfer-supply`, `step-vco-supply`, `loop-supply` | the transfer, the step into 800 pF and the loop with the rails at 10.8–12.6 V each way | gain 2.000 and intercept −2.500 V within 1 mV, under 5 % overshoot, 69.4° — the rails' level does not reach the jack |
| `patch[v_ext=…,r_ext=…]` | another module's output at either rail, stiff or through 220 Ω, patched onto the jack | **Recorded, accepted by the owner** (2026-10-03, "Accept as is", #5-6): against a stiff output `R-OUT-PROT` carries 0.53 W (0.59 W at the worst corner), over the ≥500 mW its row specifies; 0.36–0.40 W through 220 Ω. Asserted only under the fitted ERJ-P08F1001V's 0.66 W. The op-amp holds the opposite rail at 24 mA; `D-JACK-CLAMP` never conducts (`pitch-stage.md`) |
| `short[v_dac=…]` | the jack shorted for 5 ms and released, the DAC at either end of its window | back within a cent in under 0.2 ms; a swing of several volts past the note on release; 0.15 W in `R-OUT-PROT` while shorted |
| `step-mult[mult=1]`, `[mult=2]` | a passive mult to a MOD jack (its 82 nF) or the BREATH jack (its 10 nF since #32) — the page's own model, the capacitor alone | **a recorded hazard**: over 8 % |
| `step-real-mult[…]` | the same, with that output's own `R-OUT-PROT` to its driver as well | recorded only |
| `loop[mult=…]`, `loop-cable[c_cable=…]` | the loop gain at all three loads and into the cable, broken at the stage's (−) input | phase margin over 45° after the ±10° screen; **`D-ESD-PITCH` moves it by under 0.1°** |

The step is an ideal DAC edge, harder than the DAC8568's own settling, from
jack 0 V to +1 V, one octave.

**The result is `pitch-mult-overshoot`: 41.6 % at 82 nF, 11.4 % at 10 nF**,
at the nominal; the corners move it
by about a point either way. An octave step overshooting by 41.6 % is 5.0
semitones `[calc: 0.416 × 12]`; into the BREATH jack, since its capacitor
went to 10 nF for #32, about 1.4.

**The AC sweep is blind to it, and the run shows why.** The phase margin at
crossover is the same at every load to a tenth of a degree, because
`C-FB-PITCH` closes the loop on the op-amp's own output there. The ringing is
lower down, in the handover between that path and the DC path through the jack,
where the loop gain is still large — no crossover, so no margin to read.

With the other output's driver on the jack as well — which is what a patch
cable actually connects — its `R-OUT-PROT` damps the ring: about 15 % at 82 nF
and none at 10 nF. The capacitor-only figure is the page's model and the
worse case.

**`D-ESD-PITCH` is invisible to all of it**: under 0.04 point of overshoot,
under 10⁻⁵ ° of margin and no measurable DC shift at any corner, because it
sits on the node the DC loop regulates and beside 10 nF of `C-FILT-PITCH`.

## How it was made to run

The loop is broken by voltage injection (`tools/sim.py`, the stated break's
option (b)): the 1 GH break found no operating point on this stage at all.
`pitch-loop.cir` states why injection is sound here.

**TI's OPA2197 model finds no operating point for this stage away from jack
0 V** once the trim network is in (2026-10-01: at DAC 2.0 V, and at the 0.25 V
start of a `.dc` sweep, ngspice fell back to its transient op, which
`tools/sim.py` refuses; adding 100 Ω in R1's leg alone was enough to lose it).
So every deck starts at DAC 1.25 V, jack 0 V, where it converges, and
`pitch-dc.cir` is a transient that walks the DAC to the window's bottom, middle
and top and reads each after a 2 ms hold.

## What a result is worth

**A simulated step is a screen, not a spec.** It either agrees with the bench
at E9 — "pitch stability into worst-case cable capacitance" is in the
measurement table — or tells you where to look.
