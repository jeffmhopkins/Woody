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
| `VDD`/`VREF` 3V3 | in | `carrier/mcu` through `HDR-DEV`, `interfaces/key-chain-loom` | — | The dev board's LDO. The MCP3202 has no `VREF` pin. **The key pull-ups load this same node** — that argument stays in `carrier.md` §2 |
| SPI2 `SCLK`, `MOSI`, `DOUT` | in/out | `carrier/mcu` through `HDR-DEV`, `interfaces/spi-link` | `loop-budget` | One host shared with the DAC8568, clocked slower than the DAC, per `carrier.md` §4 |
| `CS_ADC` (IO39) | in | `carrier/mcu` through `HDR-DEV` | — | This device's own chip select on the shared host, and a carrier-local net. **Not `CS_MOD`**, the DAC's, which leaves on `J-UMB` |
| `AGND_INST` | ref | `carrier/power-entry-instrument` | — | The instrument analog star, drawn `AGND-local` in `carrier.md` §2 and tied to `PWR_GND` at one point. `R-ADCDIV-L` and `C-AA-ADC` return here. **Not `AGND_SENSE`** (the umbilical conductor) and **not `AGND_MOD`** |
| CH1 | — | — | — | Spare input, unconnected |

### Derivations

**Divider** `[calc]`, matching `R-ADCDIV-U`/`R-ADCDIV-L` `[repo] bom.csv`:

```
ratio      = 15k / (10k + 15k) = 0.600
full scale = 4.86 V × 0.6 = 2.92 V  against VREF 3.3 V → 88 % of range, 3622 counts
rest       = 0.265 V         × 0.6 = 0.159 V →  197 counts
real play  = 2.8 kPa → 0.265 + 0.766 × 2.8 = 2.41 V → 1.447 V → 1795 counts
                                          [2.8 kPa from breath-receive-stage.md]
                                          [0.265 and 4.86 from sensor-full-scale]
playable span above rest ≈ 1598 counts of 4096
```

**Why the upper leg is ≥10 kΩ** `[calc]` — the 5 V rail comes up before the dev
board's 3V3, so for a few milliseconds the divider drives the ADC input above its
own supply:

```
worst case, 3V3 at 0 and the clamp holding the pin at ~0.7 V:
  (4.7 − 0.7) / 10 kΩ = 400 µA   against a family-typical ±2 mA  [from memory]
```

The same resistor covers a saturated buffer: if the sensor or the op-amp fails
high at +12 V, `(12 − 0.7 − 3.3)/10 kΩ ≈ 800 µA`, still inside the clamp rating.

**Anti-alias** `[calc]`, matching `C-AA-ADC` `[repo] bom.csv`:

```
R_th = 10k ∥ 15k = 6.0 kΩ
f_c  = 1/(2π × 6k × 47 nF) = 564 Hz
τ    = 6 kΩ × 47 nF        = 282 µs
attenuation at the R-78E5.0's ~330 kHz switching rate = 20·log10(330k/564) = 55 dB
```

> **τ = 282 µs exceeds the 250 µs loop period, and the note-on threshold is read
> through it.** `latency-budget.md` and ADR 0003 book "SAR ADC conversion
> ~50–200 µs" and no RC term at all `[repo]`. About 5.6 % of the 5 ms budget —
> not fatal, but it belongs in the table that chose 4 kHz over 8 kHz. Found by
> `R10-keyscan-and-adc.md` §B-2 and still unapplied.

**Sample-cap charge sharing** `[calc]`, from R10's datasheet quote (20 pF sample
cap, 1.5 clocks of acquisition) `[repo] R10 B-2`:

```
I_avg = 20 pF × 4 kHz = 80 nA per volt
ΔV    = 80 nA/V × 6 kΩ = 480 µV/V = 0.048 % — about 2 LSB at full scale,
        proportional to V_in, therefore a pure constant gain term
```

Invisible: the zero is auto-tracked in firmware and the span is set by a panel
knob `[repo] 0003, 0006`.

**`C-ADC-BULK` is new and is proposed, not decided.** The MCP3202 has no `VREF`
pin — `VDD` *is* the reference `[repo] R10 B4` — so the ADC's scale factor is the
dev board's LDO output, and it has no anti-alias filter of its own. The repo's
own `C-STRIP-BULK` note puts the WS2815 PWM rate at ~2 kHz `[repo] bom.csv`,
which is exactly Nyquist for a 4 kHz sampler. 10 µF plus the existing 100 nF,
treating that pin as an analog reference rather than a logic supply.

---

## Component table

*Rows moved verbatim from `carrier.md`'s component table.*

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-ADC` | MCP3202-CI/SN | `VDD` **is** `VREF`; 3V3 from the dev board | `[repo]`; clock limit `[from memory]` |
| `R-ADCDIV-U`, `R-ADCDIV-L` | 10 kΩ / 15 kΩ 1 % | 0.6× after the buffer | `[repo]` + `[calc]` |
| `C-AA-ADC` | 47 nF C0G | 564 Hz, and the ADC's charge reservoir | `[repo]` + `[calc]` |
| **`C-ADC-BULK`** | **10 µF X7R** | **Bulk at MCP3202 `VDD`/`VREF`. Proposed — the reference has no anti-alias and the WS2815 PWM is ~2 kHz against a 4 kHz sampler** | proposed, from `[repo] R10 B-3` |
