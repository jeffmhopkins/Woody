# SPI link — simulation

`sims.yaml` says what is simulated and what every run must show; `cs.cir` and
`pair.cir` are the decks; `results.yaml` is what the last run found,
**generated** by `python3 tools/sim.py run hardware/interfaces/spi-link/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The decks read the carrier's netlist
(`R-SPI-SER-SCLK`, `-MOSI`, `-CS`, `R-CS-PULL-INST`) and the module's
`digital-and-supervision` (`R-PULL-SCLK`, `R-PULL-MOSI`, `R-PULL-CS`, and the
receiver's `R-RX-MOD` and `C-RX-MOD`, by row). The cable is Belden 1752A, a
stranded 24 AWG Cat5e patch cable, banked for this sim
(`datasheets/connectors/BELDEN-1752A-CAT5E-PATCH-24AWG-STRANDED.pdf`,
fragment R38): 100 ± 12 Ω, 70 % velocity, 90 Ω/km. The ESP32-S3's pad,
`U-TVS-SPI` and the receiver's input are behavioural, from their banked
sheets; `sims.yaml` gives each parameter's page.

## What is simulated, as netlisted (owner, 2026-09-30)

- **`U-TVS-SPI` on the pad side of `R-SPI-SER`**, and `R-SPI-SER` at
  `spi-series-r`.
- **The receiver is `U-RX-MOD`**, a 74AHCT14 Schmitt stage, each line reaching
  its first gate through `R-RX-MOD` and `C-RX-MOD`; the pulls stay at the cable
  node. Its thresholds are the datasheet's spread over `VCC` 4.5–5.5 V —
  `V_T+` 0.9–2.1 V, `V_T−` 0.5–1.7 V, at least 0.4 V apart
  `[ds SN74AHCT14.pdf p.5]` — and it is tested for **every** threshold pair in
  that spread: inside the band an edge must swing back less than the smallest
  hysteresis, and once past the band's far end it must never return to the
  band's near end (`sims.yaml`'s header). The `*_margin` and `*_trough`
  measures that read exactly 0.40 V are that second test passing: the worst
  value after the crossing is the crossing itself.

## The cable is two different lines

`CS_MOD` shares pair 7/8 with its own return `DIG_GND`: one line of the pair's
differential impedance. `SCLK` and `MOSI` share pair 4/5 **with each other**
and return on other pairs: two coupled lines, an odd mode at half the pair's
differential impedance (50 Ω, from the datasheet) and an even mode — both
conductors together against the returns — that no datasheet gives. The run
sweeps the pair's common-mode impedance `z_cm` over 70, 100 and 140 Ω, the
range a two-wire estimate gives (`sims.yaml`, `z_cm`), and ngspice's `CPL`
line carries both modes with the conductor's loss.

## What it shows

Every sim runs at the nominal and at every end of the pad's resistance and
edge, the TVS capacitance, the receiver's input capacitance, `C-RX-MOD`'s
tolerance and the cable's impedance: 65 runs each.

| Sim | What | Result |
|---|---|---|
| `cs-edges` | `CS_MOD` falls and rises | **Clean at `U-RX-MOD`'s input at every corner** (`cs-fall-reentry`). At the cable node the falling edge can still come back over a plain TTL `V_IL`, by 0.10 V at the worst corner (the pad at its default drive), not at the nominal |
| `cs-edges-tvs-line` | a what-if: `U-TVS-SPI` at `J-UMB`, 100 Ω, no RC — the link before 2026-09-30 | the cable node comes back over `V_IL` by 0.45 V nominal, 0.66 V at the worst corner |
| `pair-mosi-low` | `SCLK` at 2 MHz, `MOSI` held low | **`MOSI` at the Schmitt input stays under 0.33 V** at every `z_cm` and corner, against a lowest `V_T+` of 0.9 V (`spi-pair-crosstalk`); at the cable node it reaches 1.21 V |
| `pair-mosi-high` | the same, `MOSI` held high | stays at least 1.24 V over the highest `V_T−` |
| `pair-opposite-mosi-falls`, `-rises` | `MOSI` changes as `SCLK` rises | both make one edge each at the Schmitt input, every corner |
| `frame-timing` | one DAC frame's edges, all three lines (`frame.cir`), the pads held to the firmware contract: `CS_MOD` falls by `SCLK`'s first rising edge, stays low 250 ns after its last falling edge, high 250 ns between frames | **The DAC8568's t1, t4, t5, t8, t6/t7, t9 and t10 hold at its pins at every corner and `z_cm`**, for the worst pair of receiver thresholds per inequality and both gates' and the buffer's whole propagation spread. Tightest: t8 121 ns against 10, t4 206 ns against 80. What each pad interval must at least be: `CS_MOD`'s hold after the last fall 114–139 ns, its high time 117–124 ns, and it may fall up to 133 ns *after* the first rising edge (`need_*`) |
| `frame-timing-cs-released-at-last-edge` | a what-if: `CS_MOD` released on `SCLK`'s last falling edge | **t8 is −103 to −128 ns**: `SYNC` rises at the DAC before the last falling edge does, and the frame is lost. Why the contract states a hold |
| `pair-without-rc` | a what-if: the Schmitt input straight on the cable node | held low it crosses the lowest `V_T+` at every `z_cm` (by 0.69 V at 140 Ω); held high it dips past the highest `V_T−` at 140 Ω. **Hysteresis alone does not close it; the RC is why it is there** |

Every `SCLK` edge reaches the lowest `V_T+` 28–39 ns after it leaves the pad and
the highest 66–91 ns after (`s_delay_min`, `s_delay_max`), the same for
`MOSI` and `CS_MOD` through the same parts. Against the DAC's 250 ns half-period
at 2 MHz and its 6 ns setup, 4 ns hold and 13 ns `SYNC`-to-`SCLK` setup
`[ds DAC8568CIPW.pdf p.7]`, a skew of up to 63 ns between two lines
`[calc: 91 − 28]` plus two gates' 1–9 ns each `[ds SN74AHCT14.pdf p.6]` leaves
more than 150 ns `[calc: 250 − 63 − 2 × 8 − 13]`.

**That paragraph measured rising edges only, and covered `DIN` against
`SCLK`, not `CS`** (2026-10-01, pre-layout review A5-1). A falling edge
through the same RC reaches the lowest `V_T−` (0.5 V) much later than a rising
edge reaches the lowest `V_T+` (0.9 V), so the skew *across* edge directions
is larger than 63 ns, and where `CS_MOD` sits against `SCLK` is the host's
choice, not the half-period's. `frame-timing` measures every one of the
DAC's frame times across directions, at its pins, and holds them to a stated
pad timing; `firmware/README.md` carries that timing as a requirement.

## What it says that the pages did not

- **`CS_MOD`'s falling edge was the tight one, not the rising.** With the pad
  and `R-SPI-SER` above the line's impedance the falling edge's first step
  lands just under a TTL `V_IL`, and a TVS on the **line** side of
  `R-SPI-SER` sent the returning wave back inverted, up through it. Moving the
  clamp to the pad side and 82 Ω take most of that away at the cable node; the
  Schmitt stage takes the rest.
- **Pairing `SCLK` with `MOSI` is not safe by construction.** ADR 0004 reasoned
  that coupling lands "at the moment nobody is looking". The DAC clocks `DIN`
  in on `SCLK`'s **falling** edge `[ds DAC8568CIPW.pdf p.6]`, and a coupled
  glitch arrives with the edge that caused it and lasts about one cable round
  trip (~20 ns). The pairing stays; the receiver answers it.

## In the register

This README owns, in `config/figures.yaml`:

- `cs-fall-reentry`: 0.10 V past V_IL at the cable node at the worst corner, none at the nominal; none at the Schmitt receiver's input at any corner
- `spi-pair-crosstalk`: 0.21-0.29 V nominal, 0.25-0.33 V worst corner, over a common-mode impedance of 70-140 ohm

The `CS_MOD` timing `frame-timing` asserts is a firmware requirement, not a
register figure: `firmware/README.md`, *What the hardware requires*, states it
and cites this run.

## What a result is worth

**The even mode is an estimate**, and every `SCLK`/`MOSI` result moves with it:
neither the cable's datasheet nor the standard gives a common-mode impedance,
so the bench decides: **E11**, a scope on `SCLK`, `MOSI` and `CS_MOD` at
`U-RX-MOD`'s inputs, on the real cable at length, `SCLK` running. The
ESP32-S3's pad is a resistance and an edge (Espressif publishes no IBIS), and
the Schmitt input a capacitance and its datasheet thresholds: a behavioural
screen, not a signal-integrity sign-off.
