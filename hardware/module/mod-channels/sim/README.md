# Mod channels — simulation

`sims.yaml` says what is simulated and what every run must show; `mod.cir`
(all four channels and the shared reference) and `mod-loop.cir` (channel 1's
loop) are the decks; `results.yaml` is **generated** by
`python3 tools/sim.py run hardware/module/mod-channels/sim`.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read this circuit's netlist and,
for the loads a passive mult joins to a MOD jack, the other outputs' jack parts
(`C-OUT-BREATH`, `C-FILT-PITCH`, another channel's `C-FILT-MOD` and
`R-OUT-PROT`). All six used op-amp halves are TI's OPA2197 model, banked in
`datasheets/analog/`. `V_ref` is `mod-reference`, cited. The DAC is an ideal
source (no DAC8568 model is published, fragment R29).

## What it shows

| Sim | What | Result |
|---|---|---|
| `range` | code 0 and full scale, at the corners of `R-MODGAIN-IN`/`-FB` | the op-amp output follows `4·Vdac − 3·V_ref` within 0.1 mV at both ends: **neither end clips** on ±12 V. Span 19.970–20.030 V at `R-MODGAIN-IN`/`-FB`'s 0.1 % (since 2026-10-01, A2-12), the page's figures exactly |
| `range` (the jack) | the same at the jack, into a 100 kΩ input | **0.99 V/V**: `R-OUT-PROT` is outside the loop, so the jack reads 1 % low, −9.90…+9.90 V at the nominal — a load-dependent span error, which is `mod-jack-range` on the page's tolerance table |
| `clr-ref-stale` | channel 7 at 0 V, a signal channel at full scale | the output pins at +11.97 V (+11.82 V at the jack) on the deck's ideal +12.0 V rail: the OPA2197 model swings to within 30 mV of it. The page's "+11.45 V" is the same clip on the module's rails less their Schottky drops (`notes.md`), so the two agree |
| `wrong-ref-2v5` | the old 2.5 V written into channel 7 | −7.50 V at code 0; the top clips at the rail short of +12.5 V: the page's "clips positive" reproduces |
| `step-mult`, `step-real-mult` | a 1 V step into a VCO, and passive mults to the BREATH, PITCH and another MOD jack | **no overshoot at any load** (under 0.02 %): `C-FILT-MOD` and whatever a patch adds sit behind `R-OUT-PROT`, outside the loop — unlike pitch (`pitch-mult-overshoot`) |
| `loop` | channel 1's loop gain at the same loads | 91.6° at every load, crossover 2.3 MHz |
| `crosstalk` | channel 1 full scale in one edge | the others' jacks move 0.1 mV; `VREF_MOD` 2.2 mV transiently |
| `ref-current` | every channel at code 0 | 1.333 mA from the follower, the page's figure — its heaviest case. At full scale a channel draws the other way, (3.333 − 5.0)/10 kΩ = −0.17 mA `[calc]` |

## What a result is worth

A screen against TI's macromodel with an ideal DAC. The loop is broken by THE
STATED BREAK (a), 1 GH / 1 GF at the (−) input, with `.options rshunt=1e10`.
A simulated phase margin is a screen with a ±10° bar.
