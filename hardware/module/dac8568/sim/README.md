# DAC8568C — simulation

`sims.yaml` says what is simulated and what every run must show; `poweron.cir`
is the deck; `results.yaml` is what the last run found, **generated** by
`python3 tools/sim.py run hardware/module/dac8568/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The deck reads `module/dac8568`
(`C-VREF-DAC`), `module/pitch-stage` and `module/mod-channels`.

## What it shows

The DAC at rack power-on, before firmware writes, into the pitch jack and mod
jack 1: every channel at its zero-scale reset plus the datasheet's power-on
glitch, and `VREFIN/VREFOUT` 3-state (the internal reference is off by
default) with `C-VREF-DAC` and a leakage swept −1, 0 and +1 µA. This is what
[`power-entry/sim`](../../power-entry/sim/) left open: it holds the channel and
`VREFOUT` as ideal 0 V sources.

| Sim | Holds |
|---|---|
| `poweron[i_leak=…]` | the pitch jack within 100 mV of 0 V through the glitch at either sign and width (about ±36 mV at the worst corner), and parked within 15 mV with 1 µA of pin leakage — about 9 mV per µA through `TRIM-OFFSET`'s track; mod jack 1 parked within 2 mV of 0 V. **Recorded: the mod jack swings about ±0.12 V for a fraction of a millisecond** when its channel's glitch and channel 7's have opposite signs (4 × V_dac − 3 × V_ref7) |

**What that means for the claims.** `pitch-stage.md`'s *Power-on is 0.000 V*
holds as a parked state, and its mechanism — `TRIM-OFFSET` holding a 3-state
pin — holds for any pin leakage under about 10 µA. ADR 0006's *mod 1–4
exactly 0 V* is true of where the jacks park, not of the moment `DAC_AVDD`
arrives: a short spike of up to about 0.12 V is the datasheet's glitch,
multiplied by the mod stage's gains. Neither is a design question; the spike
is recorded.

## What it does not show

- **`DAC_AVDD` itself.** The glitch is placed in time, not produced by a
  supply ramp: the DAC is behavioural and TI publishes no model. Whether
  `SYNC` disturbs the power-on reset while it back-feeds `DAC_AVDD` is
  [`digital-and-supervision/sim`](../../digital-and-supervision/sim/)'s
  finding and is open.
- **The glitch's size at this load.** Figure 57 is at 470 pF ∥ 2 kΩ; here each
  channel drives `R-OPAMP-IN` into a filter capacitor with `R-BIAS-DAC` at the
  pin. The larger of the figure's ~18 mVpp and the table's 10 mV is used at
  either sign.
- **The reference pin's real leakage.** Not published; the result is linear in
  it, so a bench number rescales it.

## What a result is worth

TI's OPA2197 model for every op-amp half; the DAC is its datasheet's figures.
A simulated transient is a screen, not a spec.
