# Breath ADC — schematic

**Status:** Split out of `carrier.md` 2026-09-21 (Phase B), and edited since.
**The KiCad sheet `breath-adc.kicad_sch` is the source** (ADR 0019); placed on
the main board ([`../../boards/main-board/README.md`](../../boards/main-board/README.md)),
its datasheets banked. Values still marked `[from memory]` below are
provisional.

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
| `DEV_3V3` → `ADC_VDD` (`VDD`/`VREF`) | in | `J-MCU`, `interfaces/key-chain-loom` | — | The dev board's LDO, into `ADC_VDD` through `R-ADC-VDD` (*The reference's filter*, below). The MCP3202 has no `VREF` pin. **The key pull-ups load this same node** — that argument stays in `carrier.md` §2. It arrives down `CBL-MCU-RIBBON`, regulated against the Matrix's ground, so the Matrix's LED return current can move it: `carrier.md`, *The Matrix and the umbilical at the tail end* |
| SPI2 `SCLK`, `MOSI`, `DOUT` | in/out | `J-MCU`, `interfaces/spi-link` | `loop-budget` | One host shared with the DAC8568, clocked slower than the DAC, per `carrier.md` §4 |
| `CS_ADC` (IO39) | in | `J-MCU` | — | This device's own chip select on the shared host, and a carrier-local net, pulled up to 3V3 by `R-CS-PULL-ADC` (below). **Not `CS_MOD`**, the DAC's, which leaves on `J-UMB` |
| `AGND_INST` | ref | `carrier/power-entry-instrument` | — | The instrument analog star, drawn `AGND-local` in `carrier.md` §2 and tied to `PWR_GND` at one point. `R-ADCDIV-L` and `C-AA-ADC` return here. **Not `AGND_SENSE`** (the umbilical conductor) and **not `AGND_MOD`** |
| CH1 | — | — | — | Tied to `AGND_INST` (owner, 2026-10-03, D5; #14 A7): firmware can read a known zero for a self-test, and no floating input sits beside CH0 |

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
> the LDO's unpublished rejection at 330 kHz as −20 dB), and without a filter
> of its own **did not meet the 2 LSB E9 budget below**: 14.5 LSB at full
> scale nominal (`vdd-ripple-without-filter`, the what-if kept on record).

### The reference's filter — `R-ADC-VDD`, `C-ADC-VDD`, `C-BUCK-OUT`

**Decided by the owner, 2026-10-03** (#11 F2, #14 A1, #12 item 3): **"10 Ω +
22 µF + 10 µF".** On the sheet:

- **`R-ADC-VDD`, 10 Ω**, in series from the ribbon's `DEV_3V3` to a node of
  its own, `ADC_VDD`, which is `U-ADC` pin 8 (`VDD` = `VREF`);
- **`C-ADC-VDD`, 22 µF** X5R 25 V 1206, at pin 8 beside `C-ADC-BULK` (kept)
  and `C-DEC-ADC` (kept), all three returned to `AGND_INST` at pin 4;
- **`C-BUCK-OUT`, 10 µF**, at the R-78E5.0's own output — RECOM's standard
  application, on [`power-entry-instrument.md`](../power-entry-instrument/power-entry-instrument.md),
  which lowers the ripple at its source. The run below gives it **no credit**:
  it still takes the converter's whole 120 mV p-p as an ideal source.

`R-CS-PULL-ADC` stays on `DEV_3V3`: a logic pull-up has no business drawing
through the reference's filter.

**Simulated as netlisted** (`sim/`, the same pessimistic model): the ripple
moves a full-scale reading by **0.03 LSB nominal, 0.32 LSB at the worst
corner** (`vdd-ripple`), against the 2 LSB budget. The resistor's cost is the
MCP3202's own current, which on `VDD` = `VREF` is a reference error inside
each conversion; the capacitance at the pin carries it, and 550 µA (its 5 V
maximum) for a whole frame sags the pin **0.45 LSB nominal, 0.74 LSB worst**
(`vdd-load`), against a 1 LSB budget. Its DC drop is 0.4 mV, a gain term the
auto-zero and the span knob absorb. The ME6217's rejection above 1 kHz is
still unpublished (three copies of its sheet checked, 2026-10-03; none has a
curve), so the −20 dB model, not a datasheet, is what the filter beats, and
E9 below still measures it.

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
term. The same run confirms the 564 Hz corner, the 55 dB at 330 kHz on
`ADC_IN`'s own path (not the converter's ripple, which arrives on `VDD`) and
τ = 282 µs.

**Noise at `ADC_IN`** is in `breath-jack-noise`, from the breath chain's noise
sim (`hardware/module/breath-output-stage/sim/`, `noise`): this input shares
the sensor, `VS` and `U-BUF` B with the jack, and what reaches the converter,
integrated past `C-AA-ADC`'s pole because it folds everything it samples, is
well under 1 LSB rms and almost all the sensor's.

Invisible: the zero is auto-tracked in firmware and the span is set by a panel
knob `[repo] 0003, 0006`.

**`C-ADC-BULK` is fitted.** The MCP3202 has no `VREF` pin — `VDD` *is* the
reference — so its `VDD` pin is treated as an analog reference rather than a
logic supply: 10 µF X7R beside the 100 nF and `C-ADC-VDD`, at the pin, on
`ADC_VDD`, returned to `AGND_INST`. It is the reservoir each conversion draws from (375 µA typical
`I_DD` `[ds MCP3202-CI-SN.pdf p.3]` for ~27 µs of a 250 µs loop), and it
takes the ribbon's inductance out of that current's path.

**Against LED PWM the filter is only a start.** `R-ADC-VDD` against the
pin's ~27 µF once DC bias is counted (22 µF at −20.5 %, 10 µF at −3.7 %,
Samsung's curves) corners near 1/(2π × 10 Ω × 27 µF) ≈ 590 Hz `[calc]`:
about −11 dB at a ~2 kHz PWM rate, not a cure. PWM ripple on the reference,
if there is any, is a gain term that
aliases at a 4 kHz sample rate, and **E9 measures it**: scope `VDD` at
`U-ADC` pin 8 against `AGND_INST`, AC-coupled, with every LED sweeping full
white to off, and log the breath reading at rest and at a steady blow. It
passes if the reading's peak-to-peak moves by less than 2 LSB between LEDs off
and LEDs sweeping. A fail is closed in firmware (averaging a pair of samples
nulls a 2 kHz component at a 4 kHz rate) before it is closed in copper.

**E9 has a second half, because the first cannot see the converter.** The
R-78E5.0's ~330 kHz ripple is on `VDD` whether the LEDs are lit or not, so an
LEDs-off-against-sweeping comparison cancels it (#11 Finding 2). So, also:
scope `VDD` at `U-ADC` pin 8 against pin 4 with the scope's 20 MHz bandwidth
limit, LEDs **off**, and record the peak-to-peak at the converter's frequency;
then log the breath reading at a **steady full-scale blow**, LEDs off, where a
reference error is largest (ratiometric, so it scales with the reading). It
passes if that reading's peak-to-peak beyond the same blow's sensor noise is
under the same 2 LSB. This is the measurement that replaces `sim/`'s assumed
LDO rejection (`vdd-ripple`) with a real one.

**`CS_ADC` is pulled up** (`R-CS-PULL-ADC`, #11 F5). `IO39` is the
ESP32-S3's `MTCK`, and its weak pull-up at reset is conditional: the pin table
marks it `IE` with a note, *"Depends on the value of EFUSE_DIS_PAD_JTAG: 0 -
WPU is enabled; 1 - pin floating"* `[ds ESP32-S3-datasheet-v2.2.pdf p.17–18]`.
A build that burns that fuse would leave the ADC's select floating from reset
until firmware drives it, on a host whose clock and data the DAC shares. The
10 kΩ makes the idle state the board's, not the fuses', as `R-CS-PULL-INST`
does for `CS_MOD`. Its static current is zero while deselected.

---

## Component table

*Rows moved verbatim from `carrier.md`'s component table.*

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-ADC` | MCP3202-CI/SN | `VDD` **is** `VREF`, on `ADC_VDD`; CH1 tied to `AGND_INST` | `[ds]` DS21034F, clock limit p.3 |
| `R-ADCDIV-U`, `R-ADCDIV-L` | 10 kΩ / 15 kΩ 1 % | 0.6× after the buffer | `[repo]` + `[calc]` |
| `C-AA-ADC` | 47 nF C0G | 564 Hz, and the ADC's charge reservoir | `[repo]` + `[calc]` |
| `C-ADC-BULK` | 10 µF X7R | Reservoir at MCP3202 `VDD`/`VREF`, beside the 100 nF | `[ds]` + `[calc]`; the PWM question is E9's |
| `R-ADC-VDD` | 10 Ω 1 % | The reference's filter: `DEV_3V3` to `ADC_VDD` (owner, 2026-10-03) | `[sim]` `vdd-ripple`, `vdd-load` |
| `C-ADC-VDD` | 22 µF X5R 25 V | The filter's capacitor at pin 8 | `[ds]` Samsung CL31A226KAHNNNE + `[web]` its DC-bias curve |
| `R-CS-PULL-ADC` | 10 kΩ 1 % | `CS_ADC`'s idle pull-up to 3V3, beside pin 1: holds the ADC deselected from reset until firmware drives `IO39` | `[ds]` ESP32-S3 datasheet p.17–18 |
