# Breath output stage — simulation

`sims.yaml` says what is simulated and what every run must show; `bos.cir`
(transient) and `bos-ac.cir` (the loop, and the −12 V rail's path to the jack)
are the decks; `results.yaml` is **generated** by
`python3 tools/sim.py run hardware/module/breath-output-stage/sim`.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read this circuit's netlist and,
for a passive mult, the pitch and mod jacks' parts. Both halves are TI's
OPA2197 model. `DAC_AVDD` is `dac-rail`, cited, varied over the C grade's
5.00–5.50 V window. Each pot is two resistors about its wiper.

## What it shows

| Sim | What | Result |
|---|---|---|
| `offset[p_off=…]` | breath at rest, `POT-OFFSET` at CCW, centre, the page's zero (p = 0.432) and CW | −4.88, +0.60, −0.01 and +5.03 V at the jack at the nominal — clockwise positive, as the panel's `+` says: **the page's derivation within 10 mV at every corner** (`page_err`; `dac-rail` at its nominal, the two `R-BREATH-OFFNEG` halves since #32), its wiper-impedance term included. The 1 % resistors and the rail's window move each point by up to ±0.8 V, which the knob absorbs |
| `gain[p_gain=…]` | a 1 V breath step at the gain knob's ends and noon | 0.503×, 2.156× and 4.020× (`R-BREATH-FB`/`R-BREATH-IN` is 4.02, not 4) |
| `clip` | offset +5 V, gain 4×, a hard blow | stops at **+11.89 V** on the deck's ideal +12.0 V rail: a hard wall, as the page says. Its "about ±11.5 V" is the same clip on the module's rails less their Schottky drops |
| `step-mult`, `loop` | a hard-blow step and the summer's loop, into a module input and passive mults to the PITCH and a MOD jack | no overshoot (under 0.03 %) at any load; phase margin 95.4–95.6° (`C-OUT-BREATH` 10 nF since #32) |
| `rail` | the −12 V rail's movement at 10 Hz, through `R-BREATH-OFFNEG`'s two halves and `C-BREATH-OFFNEG` (#32) | 0.233 V/V nominal (0.227–0.240 over the resistors' corners), within 5 % of `R-BREATH-FB / \|2R + jωR²C\|`: **2.26 mV at the jack** for ADR 0027's 9.7 mV, 2.32 mV worst, the page's 2.3 mV |
| `chain-centre` | the response shaper and this stage together, `POT-RESP` at its click, GAIN at noon, OFFSET at its zero | a hard blow reaches **9.96 V**; `BREATH_OUT` clips from an in-amp output of −5.56 V, 1.20× a hard blow |
| `chain[p_resp=…]`, `chain-trim` | the same with GAIN left at noon and the curve knob at CCW, ¼, centre, ¾ and CW; and at CW with `TRIM-RESP` at its ends | see below: `breath-chain-curve-clip` |
| `noise[bw=…,p_resp=…,level=…]`, `noise-amps`, `noise-ref` | the whole breath chain's noise, sensor to jack and to the instrument's `ADC_IN`, per stage, at the curve knob's ends and click, at rest and at a hard blow; and the three TI models against their datasheets | see below: `breath-jack-noise` |
| `led[led_is=…]` | the breath LED's driver (#32) on `BREATH_OUT`, against a twin of this stage without it; a ramp to the clip and a step, at `Q-LEDB`'s beta ends, with both catalogues' LEDs | the jack moves by **under 1 µV** (budget 153 µV, 1 LSB of 10 V at 16 bits); **5.00 mA** at 10 V, **5.99 mA** at the clip, under 5 nA at and below 0 V; 2.6 % overshoot on a fast edge |
| `offset-supply`, `chain-centre-supply` | the rest level and the commissioned chain with the rails at 10.8–12.6 V each way (#5 finding 6) | the page's offset arithmetic holds within 0.08 mV at every rail corner; **the rest level moves −0.54 to +0.22 V** with the −12 V rail (`R-BREATH-FB`/`R-BREATH-OFFNEG` × its error) — inside `POT-OFFSET`'s reach, so the player's zero trim recovers it; rest-to-hard-blow is 9.95 V at every corner, and at 10.8 V / −12.6 V `BREATH_OUT` clips from an in-amp output of −4.88 V, 1.05× a hard blow (−5.56 V, 1.20×, at ±12 V) |

## The curve knob after commissioning — `chain`, `chain-trim`

The shaper's own sim stops at `BREATH_SHAPED`. One stage later, with GAIN where
commissioning leaves it (noon, 2.156×), `TRIM-RESP` set by the shaper's
commissioning step (its `sims.yaml`) and the in-amp ramped to full scale,
nominal parts, `BREATH_OUT` (the op-amp output; the jack is 1 % lower into
100 kΩ):

| `POT-RESP` | Shaper at a hard blow | `BREATH_OUT` at a hard blow | Clips from an in-amp output of |
|---|---|---|---|
| CCW (log) | 0.490× | 4.87 V | does not clip (about 9.0 V at full scale `[calc: 0.421 × 9.94 × 2.156]`) |
| ¼ | 0.843× | 8.40 V | −6.76 V, 1.46× a hard blow |
| centre click | 0.998× | 9.96 V | −5.56 V, 1.20× |
| ¾ | 1.092× | 10.89 V | −5.05 V, 1.09× |
| CW (exp) | 1.554× | 11.97 V (on the rail) | **−3.67 V, 0.79× — inside real playing** |

`chain-trim`, the same at CW with `TRIM-RESP` left at an end instead of set:
its clockwise end (1.72× at a hard blow) clips from −3.38 V, 0.73×; its
counter-clockwise end — also what an open wiper gives — (1.34×) from −4.17 V,
0.90×. A mis-set trimmer moves the clip by less than a tenth of a hard blow
either way; the curve knob's own effect at noon gain is A1-1's.

A hard blow is the in-amp's −4.64 V, the 2.8 kPa candidate of the disputed
`breath-working-point`. The clip is on the deck's ideal ±12 V; the module's
rails, a Schottky drop lower, clip a little earlier.

## The breath chain's noise — `noise`, `noise-amps`, `noise-ref`

Pre-layout review A1-16: no page totalled the noise at the jack; the receive
stage's paragraph was an estimate. `noise.cir` is the whole chain as netlisted
across six circuits — the sensor, `U-BUF` B, `R1`/`R1b`, the receive stage
with TI's INA828 and its `REF` trim, the response shaper, this stage, into
100 kΩ — with `DAC_AVDD`'s noise from the LT3042's `SET` pin, GAIN at noon,
OFFSET at its zero and `TRIM-RESP` commissioned. The deck's header says how
it is built; three things in it are not obvious:

- **TI's "noiseless" resistors are not, in ngspice 42.** An OPA2197 follower
  read 868 nV/√Hz against the datasheet's 5.5 until every `R_NOISELESS`
  instance was silenced by name (`noise-amps`).
- **The chain finds no operating point joined**, so it is cut at the INA828's
  output into two disconnected pieces and recombined: piece A's spectra at the
  in-amp's output × piece B's |H|², plus piece B's own. Piece B finds no
  operating point at a hard blow either, so its noise is taken at rest and,
  at a hard blow, everything upstream is scaled by `r_b`, the curve's slope
  there over its slope at rest, read off a ramp.
- **The sensor's noise is an assumption.** No MPXV4006DP datasheet states one.
  `sims.yaml` takes NXP's AN1646 (measured on the MPX5006): 5 counts of a
  10-bit converter at 5 V peak-to-peak, Gaussian, spread evenly over its
  500 Hz–1 MHz and white below it, **3.70 µV/√Hz** at the sensor `[calc: 5 ×
  5/1024 / 6.6 / √999 500]`. AN1646 says its noise starts at 500 Hz, so in the
  breath band this is an upper bound.

At the jack (`BREATH_OUT` behind `R-OUT-PROT` and `C-OUT-BREATH`), in the
control band (1 Hz to the link's pole, which is the bandwidth toggle's since
#32: 493 Hz, 1.56 kHz or 10.1 kHz) and the audio band (20 Hz–20 kHz); "of
10 V" is against the jack at a hard blow at the commissioned setting. The
sweep runs every mode (`bw`: 2 = 500 Hz, 1 = 1.5 kHz, 0 = WIDE):

| Mode | `POT-RESP` | Breath | Control band, rms | Audio band, rms | Electronics alone, control band |
|---|---|---|---|---|---|
| 500 Hz | centre click | rest | **0.326 mV**, −89.7 dB of 10 V | 0.466 mV, −86.6 dB | 10.2 µV |
| 500 Hz | centre click | hard blow | 0.325 mV | 0.465 mV | 11.8 µV |
| 500 Hz | CCW (log) | hard blow | 0.121 mV, −98.3 dB | 0.174 mV | 8.6 µV |
| 1.5 kHz | centre click | rest | **0.579 mV**, −84.8 dB | 0.806 mV, −81.9 dB | 12.7 µV |
| 1.5 kHz | centre click | hard blow | 0.577 mV | 0.804 mV | 16.6 µV |
| WIDE | centre click | rest | **1.45 mV**, −76.8 dB | 1.63 mV, −75.8 dB | 23.9 µV |
| WIDE | centre click | hard blow | 1.44 mV | 1.62 mV | 35.9 µV |
| any | CW (exp) | hard blow | 8–16 µV — **the jack is clipped** (`breath-chain-curve-clip`); what is left is this stage's own and the `DAC_AVDD` rail's | 19 µV | the same |

At rest every curve setting is the same (the shaper is linear about 0 V). In
the 500 Hz mode 0.326 mV rms is about **2.2 mV peak-to-peak** `[calc: × 6.6]`.
The density at the jack is 16.7 µV/√Hz at 100 Hz in every mode, and at 1 kHz
7.6 µV/√Hz at 500 Hz and 16.9 µV/√Hz in WIDE (the sensor's white floor, on
the assumption above); the electronics' alone is 0.27–0.40 µV/√Hz at 1 kHz.
**The audio band rose in every mode**, not only the wide ones: `C-OUT-BREATH`'s
pole moved from ~480 Hz to 15.9 kHz (#32), so the jack no longer filters the
sensor's floor above the link's pole a second time.

**Per stage, centre click, hard blow, control band** (rms at the jack):

| Stage | 500 Hz, µV rms | WIDE, µV rms |
|---|---|---|
| sensor (the assumption above) | 324.6 | 1443.8 |
| `DAC_AVDD`: the LT3042's `SET`-pin noise on `C-SET-DAC`'s 100 nF, by both its paths (`TRIM-BREATH-ZERO` into `REF`, and `POT-OFFSET`), added in phase | 8.0 | 8.1 |
| `VS`, through the sensor's ratio (the REF5050's datasheet figure; small at rest, where the ratio is 0.053) | 6.1 | 26.9 |
| receive stage: the INA828, `R-GAIN-INAMP`, `R2`–`R5` | 4.6 | 16.5 |
| response shaper | 3.0 | 10.4 |
| this stage and the 100 kΩ load | 2.8 | 9.9 |
| `U-BUF` B, the sensor buffer | 1.1 | 2.4 |
| `TRIM-BREATH-ZERO`, `R-ZERO-TOP`, `U-REF-BUF` | 0.7 | 2.2 |
| `R1`, `R1b` | 0.5 | 2.2 |
| **all the electronics** | **11.8** | **35.9** |

**So the jack's noise is the sensor's.** The electronics are under a tenth of
it in the control band at every mode and setting where the jack is not
clipped; in the audio band under 0.15 of it — the bound was a tenth until #32,
and at `POT-RESP` CCW on a hard blow in the 500 Hz mode, where the curve is
flattest, it is 0.12, because this stage's own ~12 µV now reaches 20 kHz
unfiltered. An earlier estimate on `breath-receive-stage.md` gave ~10 mV
peak-to-peak for the sensor and 6 µV rms for the electronics, without the
`DAC_AVDD` term, which at 500 Hz is still the largest electronic one.

**The instrument's ADC input** (`ADC_IN`, behind the divider and
`C-AA-ADC`), integrated to 1 MHz because the converter folds everything it
samples into its band: **107 µV rms, 0.132 LSB** of the MCP3202 at 3.3 V,
the same at every setting and every mode of the module's toggle (the ADC's
filter is not switched) — the sensor's. It was 66 µV before `C-AA-ADC`'s pole
moved from 564 Hz to 1.47 kHz (#32).

**What the models are worth** (`noise-amps`, `noise-ref`): the quieted OPA2197
reads 6.1 nV/√Hz at 1 kHz against its datasheet's 5.5. TI's INA828 model reads
**under** its datasheet's typicals — e_NO 66 nV/√Hz against 90, e_NI 6.0
against 7 — so the receive stage's 4.3 µV could be about a third more. TI's
REF5050 model, run alone on its netlisted parts, reads **24 µV rms over
10 Hz–1 kHz at `VS` against the datasheet's 4.5** `[calc: 0.9 µV/V × 5 V]`,
almost all of it one 1.6 MΩ resistor in the model (whose notes claim only its
0.1–10 Hz noise); the deck uses the datasheet. At the model's level the `VS`
term at a hard blow would be about 30 µV `[calc: 5.5 µV × 0.78/0.143, the two
densities]`, the electronics about 31 µV: still a tenth of the sensor's.

**No page states a noise requirement**, so nothing is asserted against one.
What would set it: what the breath CV drives. A VCA at rest passes the jack's
noise as hiss only if the offset leaves it open, which `TRIM-BREATH-ZERO`
exists to prevent; in play, a VCA or a filter's cutoff modulated by 0.33 mV
rms against 10 V is −90 dB. A limit is the owner's — for instance −80 dB of
10 V (1 mV rms) in the audio band, which the 500 Hz mode clears by 6.6 dB and
the 1.5 kHz mode by 1.9 dB, **and WIDE misses by 4.2 dB** (1.63 mV), all on
the assumption — and **E11's scope of the jack** measures the sensor's term,
which is the only one that matters. The wider modes buy speed with the
sensor's own noise; that is the trade the toggle puts on the panel.

## In the register

This README owns, in `config/figures.yaml`:

- `breath-chain-curve-clip`: with GAIN at noon and `TRIM-RESP` commissioned, `POT-RESP` fully clockwise clips `BREATH_OUT` from an in-amp output of −3.66 V, 0.79× a hard blow (−3.38 V and −4.17 V with the trimmer at its ends); at the centre click from −5.54 V, 1.19×
- `breath-jack-noise`: the jack's noise, sensor to jack, at the commissioned setting, and the instrument's `ADC_IN` — 0.33 mV rms over 1-493 Hz in the 500 Hz mode (-90 dB of 10 V, about 2.2 mV peak-to-peak), 0.58 mV over 1 Hz-1.56 kHz in the 1.5 kHz mode and 1.45 mV over 1 Hz-10 kHz in WIDE; 0.47, 0.81 and 1.63 mV rms over 20 Hz-20 kHz; ADC_IN 0.13 LSB rms

## What a result is worth

A screen against TI's macromodel. `D-JACK-CLAMP` is left out (reverse-biased
inside the rails). The loop is broken by THE STATED BREAK (a) at the summer's
(−) input.
