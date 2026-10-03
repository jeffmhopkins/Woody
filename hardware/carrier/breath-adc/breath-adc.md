# Breath ADC — schematic

**Status:** Split out of `carrier.md` 2026-09-21 (Phase B). Every line below was
moved verbatim; nothing was reworded and no value was touched in the move.

The divider, the anti-alias capacitor and the MCP3202 that turn the buffered
sensor output into counts for the ESP32-S3.

**The schematic is drawn in [`carrier.md`](../carrier.md) §2 and is not redrawn
here.** That drawing is one connected picture spanning the reference, the sensor
and this circuit's `VDD`/`VREF` node; dividing it would mean redrawing it, and a
redrawn schematic is not a moved one.

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| buffered sensor output | in | `interfaces/breath-sense-link` | `sensor-full-scale`, `breath-working-point` | The breath buffer, drawn in `carrier.md` §2. Arrives at `R-ADCDIV-U`; the same node feeds `R1` and the umbilical |
| `VDD`/`VREF` 3V3 | in | `J-MCU`, `interfaces/key-chain-loom` | — | The dev board's LDO. The MCP3202 has no `VREF` pin. **The key pull-ups load this same node** — that argument stays in `carrier.md` §2. It arrives down `CBL-MCU-RIBBON`, regulated against the Matrix's ground, so the Matrix's LED return current can move it: `carrier.md`, *The Matrix and the umbilical at the tail end* |
| SPI2 `SCLK`, `MOSI`, `DOUT` | in/out | `J-MCU`, `interfaces/spi-link` | `loop-budget` | One host shared with the DAC8568, clocked slower than the DAC, per `carrier.md` §4 |
| `CS_ADC` (IO39) | in | `J-MCU` | — | This device's own chip select on the shared host, and a carrier-local net. **Not `CS_MOD`**, the DAC's, which leaves on `J-UMB` |
| `AGND_INST` | ref | `carrier/power-entry-instrument` | — | The instrument analog star, drawn `AGND-local` in `carrier.md` §2 and tied to `PWR_GND` at one point. `R-ADCDIV-L` and `C-AA-ADC` return here. **Not `AGND_SENSE`** (the umbilical conductor) and **not `AGND_MOD`** |
| CH1 | — | — | — | Spare input, unconnected |

### Derivations

**Divider** `[calc]`, matching `R-ADCDIV-U`/`R-ADCDIV-L` `[repo] bom.csv`:

```
ratio      = 15k / (10k + 15k) = 0.600
full scale = 4.86 V × 0.6 = 2.92 V  against VREF 3.3 V → 88 % of range, 3622 counts
rest       = 0.265 V         × 0.6 = 0.159 V →  197 counts
real play  = 2.8 kPa → 0.265 + 0.766 × 2.8 = 2.41 V → 1.447 V → 1795 counts
                                          [2.8 kPa: one candidate of breath-working-point, open until E2]
                                          [0.265 and 4.86 from sensor-full-scale]
playable span above rest ≈ 1598 counts of 4096
```

**Why the upper leg is ≥10 kΩ** `[calc]` — the 5 V rail comes up before the dev
board's 3V3, so for a few milliseconds the divider drives the ADC input above its
own supply:

```
worst case, 3V3 at 0 and the clamp holding the pin at ~0.7 V, the buffer
at the sensor's full scale (sensor-full-scale, 4.86 V - not rounded down,
because this is a worst case):
  (4.86 − 0.7) / 10 kΩ = 416 µA
```

**The datasheet gives no injection-current rating to hold that against**:
DS21034F's only limit on an input is *"All Inputs and Outputs w.r.t.
V<sub>SS</sub> … −0.6 V to V<sub>DD</sub> + 0.6 V"* `[ds MCP3202-CI-SN.pdf
p.2]`. So the 10 kΩ is a current limit judged against nothing printed, and it
is only reached when the buffer is high while 3V3 is still down. At rest the
divider sits at 0.16 V (above), inside the −0.6 V … +0.6 V window even with
3V3 at zero. **Whether the buffer swings high during power-up no longer
needs an answer**: the sequencing simulation (`sim/`, `powerup-*`, #12) holds
the buffer at its positive rail through the whole power-up and the clamp
carries at most 0.72 mA; with the sensor at full scale and 3V3 down, 0.40 mA
`[sim]`. Both are under the 1 mA that run states as its limit — a limit of
its own, since the datasheet prints none — so the upper leg stays ≥10 kΩ.
The same run shows the pin 0.52–0.64 V over VDD while it conducts (the clamp's
drop, unpublished, varied a decade either way): at the weak end just past the
"V<sub>DD</sub> + 0.6 V" above, current-limited by this resistor.

The same resistor covers a saturated buffer: if the sensor or the op-amp fails
high at +12 V, `(12 − 0.7 − 3.3)/10 kΩ ≈ 800 µA` — 0.48–0.59 mA simulated
through the whole divider (`powerup-rail`) — under the 1 mA the power-up run
judges against; the datasheet itself rates no clamp current.

**Anti-alias** `[calc]`, matching `C-AA-ADC` `[repo] bom.csv`:

```
R_th = 10k ∥ 15k = 6.0 kΩ
f_c  = 1/(2π × 6k × 47 nF) = 564 Hz
τ    = 6 kΩ × 47 nF        = 282 µs
attenuation at the R-78E5.0's ~330 kHz switching rate = 20·log10(330k/564) = 55 dB
```

> **The 55 dB is ADC_IN's own path, not the converter's.** The breath signal
> is made from `INST_POS12`, not the 5 V rail; the R-78E5.0's ripple reaches
> the conversion through `VDD`, which is the reference, and this filter does
> not touch it. `sim/`'s `vdd-ripple` (#12) runs that path and, on
> pessimistic inputs (the converter's whole 120 mV p-p as its fundamental,
> the LDO's unpublished rejection at 330 kHz as −20 dB), **does not meet the
> 2 LSB E9 budget below**: 14.6 LSB at full scale nominal. The bench decides;
> `sim/README.md` says what to measure.
>
> **Proposed, for the owner (2026-10-03, #12 item 3), not on the sheet:**
> 10 Ω in series from the ribbon's `DEV_3V3` to `U-ADC`'s `VDD`, ahead of
> `C-ADC-BULK` and `C-DEC-ADC`, with 22 µF added at the pin. Simulated on the
> same pessimistic model (`sim/`, `vdd-ripple-proposed`): **0.03 LSB nominal,
> 0.22 LSB at the worst corner**, against the 2 LSB budget. The resistor's
> cost is the MCP3202's own current, which on `VDD` = `VREF` is a reference
> error inside each conversion: 550 µA (its 5 V maximum) through 10 Ω alone
> sags the pin 1.4–2.1 LSB within a conversion, which is why the 22 µF is part
> of it — with it, under 0.51 LSB at every corner (`vdd-load-proposed`; as
> netlisted, 0.11). Its DC drop is 0.4 mV, a gain term inside `DEV_3V3`'s own
> tolerance. The ME6217's rejection above 1 kHz is still unpublished (three
> copies of its sheet checked, 2026-10-03; none has a curve), so the
> −20 dB model, not a datasheet, is what this beats.

> **τ = 282 µs exceeds the 250 µs loop period, and the note-on threshold is read
> through it.** About 5.6 % of the 5 ms budget. It is booked as its own row,
> *Anti-alias filter, 564 Hz*, in
> [`latency-budget.md`](../../../docs/reference/latency-budget.md).

**Sample-cap charge sharing** `[calc]`, on `C_SAMPLE` 20 pF and `t_SAMPLE`
1.5 clocks `[ds MCP3202-CI-SN.pdf p.2]`:

```
I_avg = 20 pF × 4 kHz = 80 nA per volt
ΔV    = 80 nA/V × 6 kΩ = 480 µV/V = 0.048 %, the average current's share,
        proportional to V_in, therefore a pure constant gain term
```

**Simulated** (`sim/`, 2026-09-30): the shortfall at full scale is
`adc-sample-kickback`, larger than the average-current line above because each
sample also takes 20 pF/47 nF of `C-AA-ADC`'s charge at once `[calc]`, which
the 282 µs time constant has not fully restored by the next. Still a pure gain
term. The same run confirms the 564 Hz corner, the 55 dB at the buck's rate
and τ = 282 µs.

**Noise at `ADC_IN`** is in `breath-jack-noise`, from the breath chain's noise
sim (`hardware/module/breath-output-stage/sim/`, `noise`): this input shares
the sensor, `VS` and `U-BUF` B with the jack, and what reaches the converter,
integrated past `C-AA-ADC`'s pole because it folds everything it samples, is
well under 1 LSB rms and almost all the sensor's.

Invisible: the zero is auto-tracked in firmware and the span is set by a panel
knob `[repo] 0003, 0006`.

**`C-ADC-BULK` is fitted.** The MCP3202 has no `VREF` pin — `VDD` *is* the
reference — so its `VDD` pin is treated as an analog reference rather than a
logic supply: 10 µF X7R beside the 100 nF, at the pin, returned to
`AGND_INST`. It is the reservoir each conversion draws from (375 µA typical
`I_DD` `[ds MCP3202-CI-SN.pdf p.3]` for ~27 µs of a 250 µs loop), and it
takes the ribbon's inductance out of that current's path.

**What it does not do is filter LED PWM.** Against the ribbon's ~34 mΩ
conductor `[from memory]`, `carrier.md` and the LDO's output, 10 µF corners
near 1/(2π × 0.034 Ω × 10 µF) ≈ 470 kHz `[calc]`: nothing at a ~2 kHz PWM
rate. PWM ripple on the reference, if there is any, is a gain term that
aliases at a 4 kHz sample rate, and **E9 measures it**: scope `VDD` at
`U-ADC` pin 8 against `AGND_INST`, AC-coupled, with every LED sweeping full
white to off, and log the breath reading at rest and at a steady blow. It
passes if the reading's peak-to-peak moves by less than 2 LSB between LEDs off
and LEDs sweeping. A fail is closed in firmware (averaging a pair of samples
nulls a 2 kHz component at a 4 kHz rate) before it is closed in copper.

---

## Component table

*Rows moved verbatim from `carrier.md`'s component table.*

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-ADC` | MCP3202-CI/SN | `VDD` **is** `VREF`; 3V3 from the dev board | `[ds]` DS21034F, clock limit p.3 |
| `R-ADCDIV-U`, `R-ADCDIV-L` | 10 kΩ / 15 kΩ 1 % | 0.6× after the buffer | `[repo]` + `[calc]` |
| `C-AA-ADC` | 47 nF C0G | 564 Hz, and the ADC's charge reservoir | `[repo]` + `[calc]` |
| `C-ADC-BULK` | 10 µF X7R | Reservoir at MCP3202 `VDD`/`VREF`, beside the 100 nF | `[ds]` + `[calc]`; the PWM question is E9's |
