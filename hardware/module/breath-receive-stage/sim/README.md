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
tolerance and both `C_cm` at ±0.5 % — `C-CM-BREATH` is a matched pair, each
within 0.5 % of the pair's mean (owner, 2026-10-03, "Tighten cap matching";
its row says how it is matched). 257 runs per sim.

| Sim | What | Holds |
|---|---|---|
| `cmrr-as-netlisted` | CMRR at DC, 50 Hz, 60 Hz, 500 Hz, 1 kHz, and where it first falls to 58.5 dB | the page's 58.5 dB requirement over its whole band, DC to 500 Hz, at the worst corner (62.8 dB least; it first falls to 58.5 dB near 830 Hz); the page's 73 dB bias-pair floor within 3 dB |
| `cmrr-without-r1b` | the same with `R1b` shorted | the page's 60.2 dB, at the nominal only |
| `cmrr-ccm-5pct` | `C_cm` at ±5 % | the page's "~46 dB", at 500 Hz |

**The result is `breath-link-cmrr`**, the worst corner at the mains
fundamental: **71.3 dB worst case at 60 Hz**.

Three things the run says that the page did not:

- **The band's top is set by `C_cm`'s match.** Their mismatch converts
  common mode to differential in proportion to frequency. The band is DC to
  500 Hz, the breath channel's (`breath-sense-link.md`, defined 2026-10-03 for
  #5 finding 5), and `cmrr-as-netlisted` asserts the least CMRR in it
  (`cmrr_band`). With two independent ±1 % parts the worst corner fell through
  58.5 dB near 480 Hz and failed by under 0.5 dB at the edge; the owner chose
  **"Tighten cap matching"** (2026-10-03), so the pair is matched to ±0.5 %
  about its mean and the worst corner holds **62.8 dB** across the band,
  first reaching 58.5 dB near 830 Hz (`f_req`).
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
