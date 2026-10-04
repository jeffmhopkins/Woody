# Breath receive stage — simulation

`sims.yaml` says what is simulated and what every run must show; `cmrr.cir` is
the deck; `results.yaml` is what the last run found, **generated** by
`python3 tools/sim.py run hardware/module/breath-receive-stage/sim`.
`python3 tools/sim.py show <this dir>` prints it as a table.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The deck spans both ends of the link, so it
reads two netlists: `interfaces/breath-sense-link` for `R1` and `R1b`, and this
circuit's for the rest. The models are TI's INA828 (`U-DIFFRX`) and OPA2197
(`U-REF-BUF`), banked in `datasheets/analog/` with their SHA-256.

## What it shows

The link's common-mode rejection, sensor buffer to in-amp output: `VCM` moves
the instrument's ground against the module's, so the common-mode drive reaches
both legs through their own source impedances, as the cable delivers it. CMRR is
the differential gain over the common-mode gain, both at the INA828's output.

**The claim is a worst case over tolerance**, so every part that sets the
balance is a corner: `R1`, `R1b`, `R2`, `R3`, `R4`, `R5` at their netlisted
tolerance, both `C_cm` at ±0.5 % — `C-CM-BREATH` is a matched pair, each
within 0.5 % of the pair's mean (owner, 2026-10-03, "Tighten cap matching";
its row says how it is matched) — and `U-BW-SW`'s pin capacitance on each leg
at ±10 % (its datasheet gives no channel match; an assumption, with a what-if
at the typ-to-max spread). 1025 runs per mode.

**Since #32 the filter has three modes** (owner, 2026-10-04, "Panel 3-way
toggle", "500 Hz / 1.5 kHz / wide"), and each is held to the page's 58.5 dB
requirement over **its own band**, DC to its corner: a common-mode
disturbance anywhere in the band the player has chosen reaches the jack.
`U-BW-SW` is its datasheet: `R_ON` at its 210 Ω maximum, each pin's
capacitance off and on at its maximum, an open channel's 0.2 pF across it.

| Sim | What | Holds |
|---|---|---|
| `cmrr-500` | 500 Hz mode: the corner; CMRR at DC, 50, 60 and 500 Hz; the least in DC–500 Hz | corner **493 Hz**; least in the band **71.0 dB** at the worst corner; mains **71.7 dB**; the page's 73 dB bias-pair floor within 3 dB |
| `cmrr-1k5` | 1.5 kHz mode: the same to 1.5 kHz | corner **1555 Hz**; least in the band **68.3 dB** at the worst corner (68.1 dB at 1.5 kHz) |
| `cmrr-wide` | WIDE: the same to 10 kHz | corner **10.09 kHz**; 69.1 dB at 1.5 kHz; **FAILS above ~7.4 kHz**: the worst corner first falls through 58.5 dB at 7.4 kHz and reaches **56.0 dB at 10 kHz** — for the owner (below) |
| `cmrr-sw-spread` | WIDE, the switch's pins at its typ-to-max spread, one leg each way | what-if: 68.8 dB at 1.5 kHz, 55.4 dB at 10 kHz |
| `cmrr-without-r1b` | the 500 Hz mode with `R1b` shorted | the page's 60.2 dB at the nominal (60.1), 58.2 dB worst: below the requirement |
| `cmrr-ccm-5pct` | the 1.5 kHz mode with `C_cm` at ±5 % | 62.1 dB at 1.5 kHz against a 71.7 dB floor: the pair's mismatch is what sets the top |
| `cmrr-supply-low`, `-high` | WIDE, the rails at 10.8 and 12.6 V, nominal parts | 114.8 dB at 60 Hz, 82.8 dB at 10 kHz: the INA828's supply is not what limits it |

**The result is `breath-link-cmrr`**, the worst corner at the mains
fundamental, the same in every mode: **71.7 dB worst case at 60 Hz**.

What the runs say:

- **At any one frequency the CMRR is the same in every mode**: `C_cm` and the
  switch's capacitance are fixed, and below each corner `C_diff` does not
  enter the conversion. What the toggle changes is how far the band reaches,
  so what each mode is held to is its own top.
- **WIDE does not hold the requirement to 10 kHz.** The common-mode
  capacitance on each leg — `C_cm` and the switch's pins — converts common
  mode in proportion to frequency; at 10 kHz the worst corner's 1 % pair
  mismatch and 20 % switch-pin mismatch together leave 56.0 dB. The
  requirement was not moved to make it pass. **Owner's choice** (#32, asked in
  the working chat), each estimated against an ideal difference amplifier,
  which reads about 0.5 dB above the INA828 here `[calc]`:
  1. **WIDE at ~7 kHz**: the fixed `C_diff` 680 pF → 1.0 nF, 7.1 kHz, about
     59.4 dB at its top. One value on the sheet.
  2. **Keep ~10 kHz and hold WIDE's requirement to ~7 kHz**, with a reason for
     the band: the common mode the requirement is derived from is the
     umbilical's `PWR_GND` drop, and what of it lies at 7–10 kHz is the LED
     row's PWM harmonics, which `interfaces/system/sim` holds at the jack end
     to end.
  3. **Keep ~10 kHz and tighten the match**: `C_cm` to ±0.25 % alone reaches
     about 57.5 dB, not enough; the switch's channel match is the larger term
     and no catalogue part states it — it would have to be measured.
- **Without `R1b` the margin was negative, not 1.7 dB.** 60.2 dB is the
  nominal. At the worst tolerance corner the unmatched link is 58.2 dB at DC,
  below the requirement. `R1b` is fitted, so this argues for the part, not
  against it.
- **`R1b` buys about 13.5 dB of worst case** (from 58.2 to 71.7 dB at DC), which
  settles the page's two readings: "about 13 dB" was right, "fifty times" was
  not.

## What a result is worth

**A simulated CMRR is a screen, not a spec.** It is a ratio of two large
numbers, sensitive to exactly the parasitics a macromodel does not carry — the
pour asymmetry under the `BREATH`/`AGND` pair is in no netlist. The `D-CLAMP`
diodes are left out (reverse-biased, the same part on both legs), and so is the
Cat5 pair's own resistance (balanced, about 0.2 Ω a conductor). A number from
here either agrees with the bench at E9 or tells you where to look.
