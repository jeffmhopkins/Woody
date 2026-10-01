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
| `offset[p_off=…]` | breath at rest, `POT-OFFSET` at CCW, centre, the page's zero (p = 0.432) and CW | −4.89, +0.61, 0.00 and +5.06 V at the nominal — clockwise positive, as the panel's `+` says: **the page's table to 1 mV**, its wiper-impedance term included. The 1 % resistors and the rail's window move each point by up to ±0.8 V, which the knob absorbs |
| `gain[p_gain=…]` | a 1 V breath step at the gain knob's ends and noon | 0.503×, 2.156× and 4.020× (`R-BREATH-FB`/`R-BREATH-IN` is 4.02, not 4) |
| `clip` | offset +5 V, gain 4×, a hard blow | stops at **+11.89 V** on the deck's ideal +12.0 V rail: a hard wall, as the page says. Its "about ±11.5 V" is the same clip on the module's rails less their Schottky drops |
| `step-mult`, `loop` | a hard-blow step and the summer's loop, into a module input and passive mults to the PITCH and a MOD jack | no overshoot (under 0.03 %) at any load; phase margin 95.6° at every load |
| `rail` | the −12 V rail's movement, through `R-BREATH-OFFNEG` | 0.418 V/V: **4.05 mV at the jack** for ADR 0027's 9.7 mV, the page's 4.1 mV |
| `chain-centre` | the response shaper and this stage together, `POT-RESP` at its click, GAIN at noon, OFFSET at its zero | a hard blow reaches **9.99 V**; `BREATH_OUT` clips from an in-amp output of −5.54 V, 1.19× a hard blow |
| `chain[p_resp=…]`, `chain-trim` | the same with GAIN left at noon and the curve knob at CCW, ¼, centre, ¾ and CW; and at CW with `TRIM-RESP` at its ends | see below: `breath-chain-curve-clip` |
| `noise[p_resp=…,level=…]`, `noise-amps`, `noise-ref` | the whole breath chain's noise, sensor to jack and to the instrument's `ADC_IN`, per stage, at the curve knob's ends and click, at rest and at a hard blow; and the three TI models against their datasheets | see below: `breath-jack-noise` |

## The curve knob after commissioning — `chain`, `chain-trim`

The shaper's own sim stops at `BREATH_SHAPED`. One stage later, with GAIN where
commissioning leaves it (noon, 2.156×), `TRIM-RESP` set by the shaper's
commissioning step (its `sims.yaml`) and the in-amp ramped to full scale,
nominal parts, `BREATH_OUT` (the op-amp output; the jack is 1 % lower into
100 kΩ):

| `POT-RESP` | Shaper at a hard blow | `BREATH_OUT` at a hard blow | Clips from an in-amp output of |
|---|---|---|---|
| CCW (log) | 0.490× | 4.90 V | does not clip (about 9.0 V at full scale `[calc: 0.421 × 9.94 × 2.156]`) |
| ¼ | 0.844× | 8.44 V | −6.73 V, 1.45× a hard blow |
| centre click | 0.999× | 9.99 V | −5.54 V, 1.19× |
| ¾ | 1.090× | 10.90 V | −5.05 V, 1.09× |
| CW (exp) | 1.554× | 11.97 V (on the rail) | **−3.66 V, 0.79× — inside real playing** |

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
control band (1 Hz to the link's 459 Hz pole) and the audio band
(20 Hz–20 kHz); "of 10 V" is against the jack at a hard blow at the
commissioned setting:

| `POT-RESP` | Breath | Control band, rms | Audio band, rms | Electronics alone, control band |
|---|---|---|---|---|
| centre click | rest | **0.293 mV**, −90.7 dB of 10 V | 0.321 mV, −89.9 dB | 9.8 µV |
| centre click | hard blow | **0.293 mV**, −90.7 dB | 0.321 mV, −89.9 dB | 11.2 µV |
| CCW (log) | hard blow | 0.108 mV, −99.3 dB | 0.119 mV | 8.3 µV |
| CW (exp) | hard blow | 7.4 µV, −122.6 dB — **the jack is clipped** (`breath-chain-curve-clip`); what is left is this stage's own and the `DAC_AVDD` rail's | 6.7 µV | 7.4 µV |

At rest every curve setting is the same (the shaper is linear about 0 V).
0.293 mV rms is about **1.9 mV peak-to-peak** `[calc: × 6.6]` and 29 ppm of
10 V. The density at the jack is 16.3 µV/√Hz at 100 Hz and 3.15 µV/√Hz at
1 kHz (the link's pole and `C-OUT-BREATH`'s are both near 460 Hz); the
electronics' alone is 0.10–0.12 µV/√Hz at 1 kHz.

**Per stage, centre click, hard blow, control band** (rms at the jack):

| Stage | µV rms |
|---|---|
| sensor (the assumption above) | 292.9 |
| `DAC_AVDD`: the LT3042's `SET`-pin noise on `C-SET-DAC`'s 100 nF, by both its paths (`TRIM-BREATH-ZERO` into `REF`, and `POT-OFFSET`), added in phase | 7.8 |
| `VS`, through the sensor's ratio (the REF5050's datasheet figure; 0.6 µV at rest, where the ratio is 0.053) | 5.5 |
| receive stage: the INA828, `R-GAIN-INAMP`, `R2`–`R5` | 4.3 |
| response shaper | 2.8 |
| this stage and the 100 kΩ load | 2.6 |
| `U-BUF` B, the sensor buffer | 1.0 |
| `TRIM-BREATH-ZERO`, `R-ZERO-TOP`, `U-REF-BUF` | 0.6 |
| `R1`, `R1b` | 0.5 |
| **all the electronics** | **11.2** |

**So the jack's noise is the sensor's.** The electronics are under a tenth of
it at every setting where the jack is not clipped: 11.2 µV rms is −119 dB of
10 V. An earlier estimate on
`breath-receive-stage.md` gave ~10 mV peak-to-peak for the sensor (about five
times this) and 6 µV rms for the electronics (about half this, without the
`DAC_AVDD` term, which is the largest electronic one).

**The instrument's ADC input** (`ADC_IN`, behind the divider and
`C-AA-ADC`), integrated to 1 MHz because the converter folds everything it
samples into its band: **66 µV rms, 0.082 LSB** of the MCP3202 at 3.3 V,
the same at every setting — the sensor's; the electronics (`U-BUF` B, the
divider, `VS`) add about 1.3 µV `[calc: √(66.045² − 66.033²)]`.

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
exists to prevent; in play, a VCA or a filter's cutoff modulated by 0.3 mV
rms against 10 V is −90 dB. A limit is the owner's — for instance −80 dB of
10 V (1 mV rms) in the audio band, which the sim clears by 10 dB on the
assumption — and **E11's scope of the jack** measures the sensor's term,
which is the only one that matters.

## In the register

This README owns, in `config/figures.yaml`:

- `breath-chain-curve-clip`: with GAIN at noon and `TRIM-RESP` commissioned, `POT-RESP` fully clockwise clips `BREATH_OUT` from an in-amp output of −3.66 V, 0.79× a hard blow (−3.38 V and −4.17 V with the trimmer at its ends); at the centre click from −5.54 V, 1.19×
- `breath-jack-noise`: the jack's noise, sensor to jack, at the commissioned setting, and the instrument's `ADC_IN`

## What a result is worth

A screen against TI's macromodel. `D-JACK-CLAMP` is left out (reverse-biased
inside the rails). The loop is broken by THE STATED BREAK (a) at the summer's
(−) input.
