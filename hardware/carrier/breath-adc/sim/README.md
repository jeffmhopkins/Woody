# Breath ADC — simulation

`sims.yaml` says what is simulated and what every run must show; `adc-ac.cir`
(the anti-alias filter, small-signal), `adc.cir` (the input with the
MCP3202 sampling it), `adc-powerup.cir` (the input through the power-up, #12)
`adc-vdd.cir` (the converter's ripple into VDD, which is the reference,
#12) and `adc-vddload.cir` (the conversion's own current through the
reference's filter) are the decks; `results.yaml` is **generated** by
`python3 tools/sim.py run hardware/carrier/breath-adc/sim`.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read this circuit's netlist;
the sensor's full scale is `sensor-full-scale`, cited. **The MCP3202 is
behavioural** (no model is published): its datasheet's input model, a 1 kΩ
sampling switch into 20 pF, closed for 1.5 clocks (1.67 µs at 900 kHz) once
per 250 µs loop — both typicals only, so both are varied — and, the worst
case, the sample capacitor discharged by each conversion.

## What it shows

| Sim | Page's claim | Result |
|---|---|---|
| `filter` | 1.47 kHz; 47 dB at the buck's ~330 kHz; what it leaves at 2 kHz and 4 kHz (*The sample rate*) | **1474 Hz** (1390–1567 Hz at the 1 %/5 % corners); **47.0 dB** (46.5 dB worst); 4.5 dB at 2 kHz, 9.2 dB at 4 kHz |
| `step` | τ = 108 µs, the latency term | **108 µs** (102–115 µs at the corners); the sampling does not move it |
| `kickback` | 480 µV/V, "a pure gain term" | **4.4 LSB** at the nominal, **5.7 LSB** at the worst corner, proportional to the input: a gain term, as the page says, and larger. The sample capacitor charges fully inside its window at every corner (R_SS × C_SAMPLE = 20 ns against 1.67 µs) |
| `kickback-8k`, `kickback-16k` | what-ifs (#32): two and four conversions per pass | **5.8 / 7.4 LSB** at 8 kHz, **9.0 / 11.5 LSB** at 16 kHz (nominal / worst): still gain terms; the loop budget, not this, is what keeps the rate at 4 kHz (breath-adc.md, *The sample rate*) |
| `powerup-rest` | "At rest the divider sits at 0.16 V … inside the −0.6 V … +0.6 V window even with 3V3 at zero" | **Holds**: ADC_IN 0.16 V over VDD at most through the whole power-up; the clamp carries under 1 nA |
| `powerup-blow` | 416 µA into the clamp while 3V3 is down, at full scale | **0.39 mA** nominal, **0.40 mA** worst, for 56–158 ms of the ramp (until the dev board's 3V3 is up); nothing once it is |
| `powerup-blow-no3v3` | — (no 3V3 ever: no Matrix, or its LDO dead) | 0.39–0.40 mA, held for as long as the sensor reads full scale |
| `powerup-rail` | "Whether the buffer swings high during power-up" (left open) | **Bounded without answering it**: U-BUF B at INST_POS12 for the whole power-up gives **0.72 mA** peak, **0.59 mA** stuck there once 3V3 is up — under the 1 mA judged against at every corner |
| `vdd-ripple` | the reference's filter as netlisted (owner, 2026-10-03, D1: `R-ADC-VDD` 10 Ω, `C-ADC-VDD` 22 µF beside `C-ADC-BULK` and `C-DEC-ADC`) holds the converter's ripple under E9's 2 LSB | **0.03 LSB** at full scale nominal, **0.32 LSB** at the worst corner, on the conservative model below |
| `vdd-load` | and the conversion's own current through `R-ADC-VDD` sags `VDD` = `VREF` under 1 LSB inside a conversion | **0.45 LSB** nominal, **0.74 LSB** worst; DC drop 0.31–0.42 mV |
| `vdd-ripple-without-filter` | what-if, recorded: `DEV_3V3` straight to the pin, as before D1 | 13 mV p-p on VDD, **14.5 LSB** nominal, 2.8–115 LSB across the corners: why the filter is fitted (asserted to miss the budget) |

## What it says that the page does not

The page's 480 µV/V is the *average* current, 20 pF × 4 kHz per volt, through
6 kΩ. Each sample also takes an instantaneous share of `C-AA-ADC`'s charge,
20 pF/18 nF = 0.11 % `[calc]`, which the 108 µs time constant has 90 %
restored by the next sample 250 µs later. The two together are what
the run measures. It stays invisible for the page's reason — the zero is
tracked in firmware and the span is a panel knob — so nothing changes but the
number.

## The power-up, and the converter's ripple (#12)

**The power-up sequencing the page cites now exists** (`adc-powerup.cir`).
`INST_POS12` ramps through `Q-INRUSH` (0.093–0.24 s, from
`power-entry-instrument/sim`'s start times); `VS` and the sensor follow it as
soon as the reference can (behaviourally, *earlier* than the REF5050 can);
the 5 V rail waits for the buck's input to pass 8 V and starts over 1–10 ms
(the R-78E5.0 publishes no start-up time); the dev board's 3V3 follows it. The
MCP3202's clamps are diodes to an ideal VDD — the most current — and, because
the datasheet prints no injection rating, **the 1 mA they are judged against
is a limit stated here, not Microchip's**. Every case is under it, including
the bound that answers the page's open question without a macromodel: the
buffer at its positive rail for the whole power-up, 0.72 mA. What the run also
shows: with the sensor at full scale while 3V3 is down, ADC_IN sits
**0.52–0.64 V over VDD** (the clamp's own drop, varied a decade either way) —
at the weak-clamp corner just past the datasheet's "VDD + 0.6 V" absolute
maximum, current-limited to 0.4 mA by `R-ADCDIV-U`. It is reported, not
asserted: the real clamp's drop is unpublished.

**The converter's ripple through VDD** (`adc-vdd.cir`). The MCP3202's VDD is
its reference, so ripple there is a gain error on every reading:
(V_in / VREF) × (ΔVREF / VREF) × 4096, 1.1 LSB per mV p-p at full scale. The
path is `INST_5V_A` → the ribbon's three 5 V conductors → the Matrix's
11.1 µF → its ME6217 → its 10 µF → the ribbon's one 3V3 conductor →
`R-ADC-VDD` → `ADC_VDD`, with `C-ADC-VDD`, `C-ADC-BULK` and `C-DEC-ADC` at the
pin. Two numbers the run needs are not published, so it takes both
pessimistically and says so: the R-78E5.0's whole 120 mV p-p
ripple-and-noise maximum as a sine at the switching rate from an ideal
source (no credit for its output impedance, `C-BUCK-OUT`, `D4` or `C12`),
and the ME6217's rejection at ~330 kHz as a flat −20 dB (−30 to −10 dB at
the ends; its sheet gives 65 dB at 1 kHz only).

**Without the filter it failed at every corner** — 14.5 LSB nominal, 2.8 at
the best corner, 115 at the worst, where the ribbon's inductance resonates
with the capacitors at either end inside the 200–500 kHz band searched. The
drawn ribbon is 37.6 mm, ~26 nH: it filters nothing at 330 kHz.
**With it** (`vdd-ripple`): `R-ADC-VDD` damps that LC and makes a pole with
the pin's capacitance, and the worst corner is 0.32 LSB. `rip_budget_mv`
says what the bench can be held to — the largest 330 kHz ripple on
`INST_5V_A` that keeps 2 LSB on this network: **7.7 V p-p** at the nominal
(−20 dB rejection), 0.74 V at the worst corner, both far beyond anything the
converter makes. **E9 still measures it**: scope `INST_5V_A` and U-ADC pin 8
at 20 MHz bandwidth, and log the reading's p-p at a steady **full-scale**
blow with the LEDs off.

**The filter's other side** (`adc-vddload.cir`, `vdd-load`): the MCP3202
draws its operating current only while it converts, taken here as its 5 V
maximum, 550 µA, for the whole 24-clock frame (pessimistic at 3.3 V). Through
`R-ADC-VDD` that is a reference error inside the conversion, and the pin's
capacitance holds it to 0.74 LSB at the worst corner — the reason the 22 µF
is part of the decision, not an extra.

## In the register

This README owns, in `config/figures.yaml`:

- `adc-sample-kickback`: 4.4 LSB nominal, 5.7 LSB worst corner

## What a result is worth

A screen: the sampling model is the datasheet's typical, with an assumed
spread and a pessimistic reset. The filter and time constant are the
netlist's RC and exact. The power-up is behavioural at every source and
bounds the op-amp rather than modelling it. The ripple run is linear and
exact on its network, and its two inputs that matter — the converter's
fundamental and the LDO's rejection at 330 kHz — are pessimistic assumptions,
not data: with the filter the budget holds with an order of magnitude to
spare on them, which is what the filter was chosen for.
