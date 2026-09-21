# D1 — Arithmetic audit

**Date:** 2026-09-21
**Scope:** every `[calc]` block, every table of figures and every inline number in
`hardware/module/*.md` (six pages), `hardware/controller/carrier.md`,
`hardware/controller/cluster-boards.md`, ADRs 0001/0003/0004/0005/0006/0013/0014,
`docs/reference/latency-budget.md` and the notes column of `hardware/bom.csv`.

**Method.** Every figure was recomputed from first principles in Python, from the
component values the BOM actually specifies, without reading any prior review.
Nothing was accepted because it looked plausible. Where the same quantity appears
in more than one file, the files were checked against each other; those
disagreements are called out separately because they are the highest-value
findings. Inputs I could not verify (datasheet parameters, op-amp output
impedance, trimmer tempco) are marked `[from memory]` and the verdict is only as
good as that input.

**Counts:** 312 distinct numeric claims checked. **~232 correct**, **54 wrong**
(of which 17 are disagreements between two files about the same quantity),
**26 unverifiable-inputs**.

**The headline:** the arithmetic in this project is unusually good. Almost every
derivation that is *shown* is right. The defects are overwhelmingly of one kind —
**a value changed and the numbers derived from it did not follow** — and they
cluster in exactly four places: the breath in-amp's full-scale output, the pitch
compensation capacitor, the DAC-channel count in the loop budget, and the
marker-bit allocation. Four numbers, each wrong in two or three documents at once.

---

## 1. Summary — every wrong number, claimed vs correct

Ordered by severity. "Also in" means the same wrong number appears there too.

| # | Quantity | File | Claimed | Correct | Note |
|---|---|---|---|---|---|
| A1 | In-amp output at full sensor range | `breath-receive-stage.md` L58, L101 | **−9.6 V** | **−9.94 V** | Its own table says 9.94 V span; `breath-output-stage.md` says −10.05 V. Three values, one quantity |
| A2 | In-amp output at rest | `bom.csv` `U-DIFFRX` | **−0.44 V at rest to −10 V at full** | **0.00 V at rest, −9.94 V at full** | −0.44 V is the pre-trimmer (REF grounded) circuit |
| A3 | Presence comparator levels | `digital-and-supervision.md` L54–56 | 0 V absent, **−0.44 V** alive, threshold **−200 mV** | **+0.44 V absent, 0.00 V alive, threshold ≈ +0.2 V** | Derived for REF grounded; REF is now a +0.437 V trimmer. Polarity of the whole detect inverts |
| A4 | REF state | `breath-receive-stage.md` L287 | "now that **`REF` is grounded**" | REF is a buffered trimmer at +0.437 V | Flatly contradicts the same page's §"REF carries a trimmer" |
| A5 | `C-FB-PITCH` | `pitch-stage.md` L29, L179 | **1 nF**, pole **15.9 kHz**, handover "~16 kHz" | **2.2 nF**, pole **7.23 kHz**, handover ~7 kHz | Same page's values table, its Q derivation and `bom.csv` all say 2.2 nF |
| A6 | `C-FB-PITCH` | ADR 0006 L611 | **1 nF**, "**across the feedback resistor**" | 2.2 nF, **op-amp output to (−)** | `pitch-stage.md` and `bom.csv` both say "across R2" is the wrong net (18° phase margin) |
| A7 | Pitch −3 dB, combined | `pitch-stage.md` L213, `bom.csv` `C-FB-PITCH` | **12.2 kHz** | **13.3 kHz** | Exact 2nd-order solve, ζ = 0.742. Still inside the 10–20 kHz window |
| A8 | Pitch attenuation at 1 MHz | `pitch-stage.md` L214 | **−41 dB** | **−42.0 dB** | |
| A9 | Loop budget, key chain | `latency-budget.md` rule 1 | **16 µs** | **32 µs** (32 bits @ 1 MHz) | ADR 0001 and `carrier.md` both say 32 µs. Pass becomes 152 µs (61 %), not 136 µs (54 %) |
| A10 | Digital breath path total | `latency-budget.md` L65 | **~2.9–3.1 ms** | **2.68–2.93 ms** | Its own rows: 2.17 + (514…764 µs) |
| A11 | Two-pole group delay | `latency-budget.md` L50 | **632 µs** | **662 µs** | Its own rows are 330 µs + 332 µs |
| A12 | Analog breath path total | `latency-budget.md` L44 | ~2.83 ms | **2.84 ms** | Same page says 2.80 ms at L76 |
| A13 | Marker / free bit split | `carrier.md` "The 32 bits" table | **6 marker, 5 free** | **8 marker, 3 free** | Decided 2026-09-21 in ADR 0001, `key-layout.yaml` and `cluster-boards.md` |
| A14 | Free-bit network option | `carrier.md` L465 | "5 free bits … **15 passives**" | 3 free bits → **9 passives** | Follows A13 |
| A15 | SPI payload | ADR 0003 L416 | **7 channels, 0.90 Mbit/s** | **6 channels, 0.77 Mbit/s** | ADR 0004 carries the corrected row; ADR 0003 was not updated |
| A16 | Umbilical bandwidth | ADR 0001 L95 | "six 16-bit channels at 4 kHz is **~576 kbit/s**" | **384 kbit/s** payload, **768 kbit/s** in 32-bit frames | Neither is 576 |
| A17 | Precision budget lever | ADR 0006 L297–299 | 0.54 / **5.40** / **0.11** cents | 0.42 / **1.35** / **0.027** cents | Uses the 9 V lever `pitch-stage.md` identifies as a pivot error; ∂Vout/∂k lever is 2.25 V |
| A18 | LT5400 / DAC-ref drift | `pitch-stage.md` L301–304 | ~0.1 / ~0.5 / ~0.4 cents | 0.027 / 0.42 / 0.73 cents | A **second, contradictory table** left in the same document, four lines below the corrected one |
| A19 | DAC INL in cents | ADR 0006 L417 | ±4 LSB = **0.66**, ±12 LSB = **2.0** cents | **0.73** and **2.2** cents | Uses a 9 V/65536 LSB; the stage's LSB is 10 V/65536 = 152.6 µV |
| A20 | Power-on state, pitch | ADR 0006 power-on table | "Bottom of its range, **below −2 V**" | **0.000 V** until the reference enable, then −2.500 V on `CLR` | The same ADR says 0 V 12 lines later; `pitch-stage.md` says they are 2.5 V apart |
| A21 | Power-on state, breath | ADR 0006 power-on table | 0 V, "the **differential pulldown** holds it there" | **+0.44 V**; the pulldown is deleted (1 MΩ bias pair) | |
| A22 | Trimmer tempco | ADR 0006 L368 | 200 Ω at 2 % → "**~2 ppm/°C**" | **5 ppm/°C** on the same ADR's own 250 ppm/°C trimmer | Its trim-range table (5 % → 22 ppm/°C) implies 250 ppm/°C; the 2 ppm/°C line implies 100 |
| A23 | Mod offset update rate | ADR 0006 rate table | "**written once at boot**" | refreshed every pass | Contradicts the six-channel loop budget used everywhere, incl. this ADR |
| A24 | ZOH image at 2 kHz | ADR 0006 L199 | **12.6 dB** | **12.04 dB** | Exactly 400/1600 = ¼ |
| A25 | ZOH image at 4 kHz | ADR 0006 L203 | **−19.2 dB** | **−19.08 dB** | |
| A26 | 15 kHz filter at 1.6 kHz | ADR 0006 L200 | **0.07 dB** | **0.049 dB** | |
| A27 | Mod LSB as % of FS | ADR 0006 L125 | **0.003 %** of full scale | **0.0015 %** of the 20 V span | 0.003 % is of 10 V |
| A28 | Ratiometric vs AGND term | ADR 0003 L450 | "roughly **30 dB** worse" | **44 dB** worse | 21 mV / 0.13 mV = 162× |
| A29 | Saving from a fully analog path | ADR 0003 L30 | "roughly **400 µs**" | **130–280 µs** | Its own table's digital-only rows |
| A30 | Cable-corner margin | ADR 0003 L403 | "**six orders** of margin" | **4.7 orders** (8 MHz / 160 Hz = 5×10⁴) | |
| A31 | AA filter at switching rate | ADR 0003 L544 | **58 dB at 500 kHz** | 59 dB at 500 kHz — and the part switches at **330 kHz → 55 dB** | `bom.csv` `C-AA-ADC` and `carrier.md` both say 330 kHz |
| A32 | Sensor thermal drift at jack | ADR 0003 L596, ADR 0006 L223 | **23 mV** in 10 V | **21.9 mV** (0.5 mV/K × 20 K × 2.185) | `breath-receive-stage.md` says 20 mV for the same quantity |
| A33 | Offset endpoints, CCW/CW | `breath-output-stage.md` L98–100, `bom.csv` `POT-OFFSET` | **+5.04 / +0.07 / −4.89 V** | **+5.06 / +0.075 / −4.91 V** | Computed with R-FB = 40 k; the values table and `bom.csv` specify **40.2 k** |
| A34 | Summer fixed gain | `breath-output-stage.md` L39, L79 | ASCII "**R-FB 40k**", "= **4**", range 0.5–4.0 | 40.2 k → **4.02**, range **0.503–4.02** | Drawing and table disagree within one page |
| A35 | Clip combination | `breath-output-stage.md` L137 | hard blow at **+23 V** | **+23.8 V** (40 k) / +23.9 V (40.2 k) | |
| A36 | OPA2197 halves used | `breath-receive-stage.md` L144 | REF buffer takes "the **last spare** half … still **one**" (11/1) | **10 used, 2 spare** | `bom.csv` `U-OPA-PITCH` enumerates all ten; `breath-output-stage.md` agrees |
| A37 | Pedestal standing at the jack | `breath-receive-stage.md` L98, `bom.csv` `TRIM-BREATH-ZERO` | **1.4–5.6 %** of span | **0–2.3 %** | Not reproducible from any input; also asserted to be "the same band" as the 4–9 % below, which it is not |
| A38 | Un-nulled pedestal | `breath-receive-stage.md` L83 | **4–9 %** of full scale | **3.3–8.3 %** | |
| A39 | Single-ended cap CMRR | `breath-receive-stage.md` L233 | "about **15 dB** at 100 Hz" | **19.7 dB** (11 kΩ, 15 nF) | Conclusion survives |
| A40 | Reference-buffer load pole | `breath-receive-stage.md` L322, `bom.csv` `R-ISO-REF` | **21 kHz** driving 100 nF **+ 10 µF** | **~210 Hz** with the 10 µF present | 21 kHz is the 100 nF-only figure. `bom.csv` `U-BUF` hedges "(or 200 Hz)" — the other two rows do not. `[from memory]` on Ro ≈ 75 Ω |
| A41 | ADC full-scale counts | `carrier.md` §2 | **3502** counts | **3500** counts | And at the sensor's real 4.80 V top it is 2.88 V → **3575** counts, 87 % |
| A42 | ADC play-point counts | `carrier.md` §2 | **1743** counts, span **1594** | **1746** counts, span **1597** | |
| A43 | Sensor top of range | `bom.csv` `U-BREATH`, ADR 0005 L74, `carrier.md`, `D-TVS-BREATH` | **4.7 V** | **4.80 V** | ADR 0003's transfer function gives 4.799 V and the whole gain derivation uses 4.8 (span 4.6) |
| A44 | Loop conductor split | ADR 0001 L135 | "12 per hop — **6 signals-and-supply, 5 grounds, 2 spare**" | 4 signals + 1 supply + 5 grounds + 2 spare = **12** | 6+5+2 = 13 |
| A45 | Hand-terminated joints | ADR 0001 L136, `bom.csv` `PCB-CLUSTER` | "**~4 connectors**" | **8 connectors** (4 ribbon assemblies) | ADR 0001's own fix 1 says eight, ten lines later |
| A46 | Chain connector count | `bom.csv` `WIRE-LOOM` | "**five connectors** must match" | **eight** | `bom.csv` `J-CHAIN` qty 8 says "EIGHT of them, not five" |
| A47 | GPIO broken out | `bom.csv` `U-MCU-RT` | **16** (1–7, 34–40, 43, 44) | **17** (IO33 omitted) | `HDR-SERVICE`, `carrier.md` §6 and ADR 0013 all say 17; `carrier.md` §3 drives **IO33** as SER |
| A48 | Pin headroom | ADR 0013 L~40 | "**Fourteen** chip pins of headroom" | **12** (18 of ~30) | |
| A49 | Panel LED | `power-entry.md` L145 | 820 Ω, "(5.21 − 2.0)/4 mA", "~3.8 mA" on 5 V | On bus +5 V: 750 Ω by that method, **3.66 mA** with 820 Ω | Superseded anyway — `bom.csv` `R-LED-PANEL` is **2.2 kΩ off +12 V**, ~4.5 mA |
| A50 | Entry bulk | `power-entry.md` L15–41, L182 | **4 × 47 µF** | **100 µF** on +12 V, 47 µF elsewhere | `bom.csv` `C-BULK-RAIL` gives the arithmetic for why 47 µF on +12 V is wrong (2.2× faster collapse) |
| A51 | Load-switch pulse energy | `bom.csv` `U-LOADSW` | 1.0 A ramp, ~6 V mean, **75 ms → 0.45 J** | **26 ms → 0.16 J** into 2.2 mF | 75 ms is ADR 0005's *500 mA* boot figure; `power-entry.md` and `C-TIMER-LOADSW` both use 26 ms |
| A52 | Clamp-legal worst, umbilical | ADR 0005 load table | **579 mA** | **571 mA** | From its own 928/119 mA and its own ×0.487 convention; its 6.5 W heat column implies 571 |
| A53 | Clamp-legal worst, restated | ADR 0005 L274 | "**~630 mA**" | 571–579 mA | Third value for the same state in the same ADR |
| A54 | TPS2553 overvoltage | ADR 0005 L305 | "roughly **66 %** over abs-max" | **71 %** (12 V on 7 V) | |
| A55 | Buck start time | ADR 0005 L284 | "the buck starts at **~17 ms**" | **26 ms** at 500 mA net (38 ms at the 350 mA the 75 ms figure implies) | |
| A56 | I_ADJ reduction | ADR 0004 L177 | "**halves** the I_ADJ contribution" | **−38 %** (475/768 = 0.62) | The 24–48 mV result is right |
| A57 | Op-amp rail headroom | `pitch-stage.md` L154, `mod-channels.md` L101 | "less **two Schottky drops** reaches ~±11.45 V" | One series Schottky (0.35 V) + 0.2 V swing loss | ADR 0006's derivation is right; the value 11.45 V is right; the derivation quoted twice is not. ADR 0004 says **±11.9 V** for the same quantity |
| A58 | Key network timing | `bom.csv` `R-KEY-SER` | press **~1 µs** (100 R × 10 nF), release **~93 µs** (10 k × 10 nF) | **5.7 µs / 125 µs** (100 R, 2.2 k, 47 nF) | `C-KEY`'s note was updated to the new parts; this row was not |
| A59 | Matrix share of the 3 W clamp | ADR 0014 L~"clamp restated" | "a full field at around **60 % of one channel**" | one channel full-field is **1.88 W** → 3 W is **160 %** of it (or 53 % of full-field white) | |
| A60 | `R-OUT-PROT` rating | `pitch-stage.md` values table | **1206 ≥250 mW** | **≥500 mW** | `bom.csv` and `breath-output-stage.md` both say ≥500 mW, off a 192 mW worst case |
| A61 | 3 W light, strips vs matrix | ADR 0005 L165 | **531 mA** vs 579 mA, "a 9 % difference" | A 3 W load difference through the buck is **~29 mA**, not 48 mA | 531 mA is not derivable from the table; unverifiable as stated |

---

## 2. Cross-file disagreements (the same quantity, two answers)

These are the ones to fix first: in each case a reader of one file gets a
different number from a reader of another, and in most of them neither file
flags the disagreement.

| Quantity | File A | File B | Which is right |
|---|---|---|---|
| In-amp output at full scale | `breath-receive-stage.md`: **−9.6 V** | `breath-output-stage.md`: **−10.05 V**; `bom.csv`: **9.94 V span** | **−9.94 V** (bias-pair loss included, as the receive page itself derives) |
| In-amp output at rest | `breath-receive-stage.md`: **0.00 V** | `bom.csv` `U-DIFFRX`, `digital-and-supervision.md`: **−0.44 V** | **0.00 V** (REF trimmer nulls the pedestal) |
| `C-FB-PITCH` value | `pitch-stage.md` drawing + ADR 0006: **1 nF** | `pitch-stage.md` table + `bom.csv`: **2.2 nF** | **2.2 nF** — and the Q/overshoot figures (44–67 %) on the same page only work with 2.2 nF |
| `C-FB-PITCH` connection | ADR 0006: "across the feedback resistor" | `pitch-stage.md`, `bom.csv`: op-amp **output** to (−) | Output to (−). ADR 0006 is one of the "three other places [that] were wrong" |
| Key-chain read time | `latency-budget.md`: **16 µs** | ADR 0001, `carrier.md`: **32 µs** | **32 µs** at the stated 1 MHz |
| Loop duty | `latency-budget.md`: **136 µs, 54 %** | `carrier.md` §4: **122.7 µs + 32 µs = 154.7 µs, 62 %** | `carrier.md` (it also costs the ADC at 24 clocks, not 18) |
| ADC frame | `latency-budget.md`: **18 clocks, 24 µs** | `carrier.md` §4: **24 clocks, 26.7 µs** | Both defensible; they must agree before the 4 kHz margin means anything |
| DAC channels in the loop | ADR 0003: **7** | ADR 0004, ADR 0006, `latency-budget.md`, `carrier.md`: **6** | **6** (ch 6 deleted) |
| Marker / free bits | `carrier.md`: **6 / 5** | ADR 0001, `key-layout.yaml`, `cluster-boards.md`: **8 / 3** | **8 / 3** |
| Free-bit count inside one file | `key-layout.yaml` comment: "The **5** genuinely free bits" | same file, `spare_bits_free: **3**` | 3 |
| OPA2197 halves spare | `breath-receive-stage.md`: **1 spare** | `bom.csv`, `breath-output-stage.md`: **2 spare** | **2** |
| Sensor top of range | ADR 0003 transfer fn: **4.80 V** | `bom.csv`, ADR 0005, `carrier.md`: **4.7 V** | **4.80 V** — and the ADC divider headroom should be recomputed at 2.88 V |
| Entry bulk caps | `power-entry.md`: **4 × 47 µF** | `bom.csv`: **100 / 47 / 47 / 47 µF** | `bom.csv` (it carries the rail-collapse argument) |
| Panel LED | `power-entry.md`: **820 Ω off bus +5 V** | `bom.csv`: **2.2 kΩ off +12 V** | `bom.csv` (the shared OE node it was sized for is gone) |
| `R-OUT-PROT` rating | `pitch-stage.md`: **≥250 mW** | `bom.csv`, `breath-output-stage.md`: **≥500 mW** | ≥500 mW |
| Chain connectors | ADR 0001 table + `bom.csv` `WIRE-LOOM`: **~4 / five** | ADR 0001 fix 1, `J-CHAIN`, both board pages: **eight** | **eight** |
| GPIO broken out | `bom.csv` `U-MCU-RT`: **16** | `carrier.md`, `HDR-SERVICE`, ADR 0013: **17** | **17** (IO33 is used) |
| Op-amp swing | ADR 0004: **±11.9 V** | ADR 0006, pitch, mod, breath pages: **±11.45 V** | **±11.45 V** at the jack (after the entry Schottky) |
| Instrument current | ADR 0004: **~275 mA** and **~360 mA** (same file) | ADR 0005: **359 mA typical** | **359 mA** typical, 571 mA clamp-legal |
| Precision budget | ADR 0006: 0.54 / 5.40 / 0.11 cents | `pitch-stage.md`: 0.42 / 0.38 / 0.027 cents | `pitch-stage.md` (correct pivot); ADR 0006 unrevised |
| DAC INL in cents | ADR 0006: **0.66** | `pitch-stage.md` stale table: **~0.4** | Neither — **0.73** cents |
| Switching frequency | ADR 0003: **500 kHz** | `bom.csv`, `carrier.md`: **330 kHz** | 330 kHz `[from memory]`, but the two files must agree |

---

## 3. Detail by quantity

### 3.1 RC corners and time constants

| Quantity | Source | Claimed | Computed | Verdict |
|---|---|---|---|---|
| Breath differential pole, `C_diff` 15 nF, 2 × 11 kΩ | `breath-receive-stage.md`, `bom.csv` | 482 Hz | 1/(2π·22k·15n) = **482.3 Hz** | correct |
| …and "not 531 Hz" (2 × 10 kΩ) | same | 531 Hz | **530.5 Hz** | correct |
| …with the `C_cm/2` term included | — | — | **459 Hz** | the textbook in-amp form is 1/(2π·2R·(C_diff+C_cm/2)); the simple form is stated. Worth a footnote, not a defect |
| Common-mode pole, 1.5 nF × 11 kΩ | (not stated) | — | 9.65 kHz | consistent with "1/10 of C_diff" |
| Breath output RC, 1 kΩ + 330 nF | `breath-output-stage.md` 482 Hz / `breath-receive-stage.md` ~480 Hz / ADR 0006 ~480 Hz | 480–482 Hz | **482.3 Hz** | correct (480 is a rounding, and drives the 332 µs latency row) |
| Mod jack RC, 1 kΩ + 82 nF | `mod-channels.md`, ADR 0006, `bom.csv` | 1.94 kHz | **1941 Hz** | correct |
| Pitch AA filter, 1 kΩ + 10 nF | `pitch-stage.md`, `bom.csv` | 15.9 kHz | **15.92 kHz** | correct |
| Deleted 10 nF jack cap: −16 dB @ 100 kHz, −36 dB @ 1 MHz | `pitch-stage.md` | −16 / −36 | **−16.07 / −35.97 dB** | correct |
| Pitch shelf: pole 15.9 kHz, zero 31.8 kHz, 6.02 dB max | `pitch-stage.md` | as stated | correct **for 1 nF**; for the specified 2.2 nF the pole is **7.23 kHz**, zero 14.5 kHz. 6.02 dB is exact and value-independent | **A5** |
| Pitch combined −3 dB | `pitch-stage.md`, `bom.csv` | 12.2 kHz | **13.3 kHz** (ζ = 0.742, ω_n = 10.7 kHz — "maximally flat" is fair) | **A7** |
| Pitch at 1 MHz | `pitch-stage.md` | −41 dB | **−42.0 dB** | **A8** |
| Pitch ringing Q = √(R_eff·C_load / R2·C_fb) | `pitch-stage.md` | 44–67 % overshoot at 82 nF / 330 nF | **43.1 % / 66.4 %**; 10 nF → 3.1 % | correct — and only with C_fb = 2.2 nF, confirming A5 |
| ADC anti-alias, 6 kΩ ∥ × 47 nF | `carrier.md`, `bom.csv` | 564 Hz, τ = 282 µs, 55 dB @ 330 kHz | **564.4 Hz, 282 µs, 55.3 dB** | correct |
| …"5.6 % of the 5 ms budget" | `carrier.md` | 5.6 % | **5.64 %** | correct |
| …old 220 nF = 121 Hz | `bom.csv` | 121 Hz | **120.6 Hz** | correct |
| Key release, 2.2 kΩ × 47 nF, V_IH = 0.7·VCC | ADR 0001, `cluster-boards.md`, `bom.csv` | τ 103 µs, crosses at 125 µs | **τ 103.4 µs**; from 0 V, **124.5 µs**; from the real pressed level (0.143 V) **119.9 µs** | correct within its model; the 100 Ω leg shortens it ~4 % |
| Key press, 100 Ω × 47 nF, V_IL = 0.3·VCC | same | τ 4.7 µs, crosses at 5.7 µs, 44× | **5.66 µs** ideal, **5.92 µs** exact (τ = R∥R_pu·C = 4.50 µs); 250/5.7 = **43.9×** | correct within its model |
| **Logic thresholds used** | same | V_IH 2.31 V, V_IL 0.99 V | **right for 74HC at 3.3 V** (0.7/0.3 × VCC). The fitted part is 74HC165 (`bom.csv`), and ADR 0001 explicitly retired the LVC 2.0 V/0.8 V pair | correct — this is the one place the part-family question was handled properly |
| Key network pole, 54 dB at 800 kHz | ADR 0001, `cluster-boards.md` | 1.54 kHz → 54 dB | **1539.5 Hz → 54.3 dB** | correct |
| Watchdog 74HC123, 1 MΩ × 220 nF | `digital-and-supervision.md` | ≈ 99 ms | **0.45·RC = 99 ms** | correct for HC123 `[from memory: K = 0.45]` |
| Tube delay 30 mm / 400 mm | ADR 0003, `latency-budget.md` | 0.09 / 1.17 ms | **0.0875 / 1.166 ms** at 343 m/s | correct |
| Tube resonance | ADR 0003 | 2.9 kHz; 214 Hz / 429 Hz | **2858 Hz; 214.4 / 428.8 Hz** | correct (λ/4 open, λ/2 closed) |
| Tube volume at 3 mm bore | ADR 0003 | 2.83 mL | **2.827 mL** | correct |
| Input LC, 22 µH + 100 µF | `carrier.md` §1 | f₀ 3.39 kHz, Z₀ 0.469 Ω, Q 0.5–0.9 | **3393 Hz, 0.4690 Ω, Q 0.47–0.94** | correct |
| Cable corner, 220 Ω / 100 Ω / 68 Ω into 200 pF | `carrier.md` §4, ADR 0004 | 3.62 / 7.9 / 11.7 MHz | **3.617 / 7.958 / 11.70 MHz** | correct, including the explicit correction that ADR 0004 had the two the wrong way round |
| SPI corner, 100 Ω into 200 pF | ADR 0003 | 8 MHz | **7.96 MHz** | correct |

### 3.2 Gains, dividers and endpoint voltages

| Quantity | Source | Claimed | Computed | Verdict |
|---|---|---|---|---|
| In-amp gain, R_G = 42.2 kΩ | `breath-receive-stage.md`, `bom.csv` | 1 + 50k/42.2k = 2.185 | **2.18483** | correct `[from memory: INA828 G = 1 + 50k/R_G]` |
| Bias-pair loss, 2×1 MΩ vs 2×11 kΩ | `breath-receive-stage.md` | ×0.9891 | **0.98912** | correct |
| Raw gain needed, 10 V / 4.6 V | same | 2.174 | **2.1739** | correct |
| Gain at the in-amp | same | 2.198 | **2.1978** | correct |
| Effective gain | same, `bom.csv` | 2.1611 | **2.16106** | correct |
| Jack span | same, `bom.csv` | 9.94 V | **9.941 V** | correct |
| 0.6 % shortfall | same | 0.6 % | **0.59 %** | correct |
| **Full-scale output** | `breath-receive-stage.md` | **−9.6 V** | **−9.94 V** | **A1 — wrong** |
| Hard blow, 2.8 kPa | `breath-output-stage.md` | sensor 2.347 V → −4.69 V | **2.3467 V → −4.690 V** (raw G) / −4.64 V (effective) | correct as stated |
| Working point 10 V / 4.7 V | both breath pages | ≈2.13× | **2.128** | correct |
| REF to null the pedestal | `breath-receive-stage.md` | +0.437 V | **0.4370 V** raw / **0.4322 V** effective | correct as stated; 5 mV inconsistent with its own effective gain |
| REF range for the spec band | same, `bom.csv` | 0.332–0.826 V | **0.3321–0.8258 V** | correct |
| 0.6 V trimmer covers | same | 0.275 V | **0.2746 V** | correct |
| 1.0 V trimmer covers | `bom.csv` | 0.458 V | **0.4577 V** | correct |
| GAIN attenuator floor, 7.15/57.15 | `breath-output-stage.md`, `bom.csv` | 0.125 | **0.12511** | correct |
| Summer gain and range | same | ×4 → 0.5–4.0 | **×4.02 → 0.503–4.02** with the specified 40.2 kΩ | **A34** |
| Offset endpoints | same | +5.04 / +0.07 / −4.89 V | **+5.06 / +0.075 / −4.91 V** at 40.2 kΩ | **A33** |
| Offset rail sensitivity | same, `bom.csv` | 40k/95.3k × 50 mV = 21 mV, 0.21 % | **20.99 mV**, 0.21 % of 10 V | correct |
| Pitch slope and intercept | `pitch-stage.md` | 9/4.5 = 2.000; −2 − 2(0.25) = −2.500 | exact | correct |
| Pitch headroom | same | 0–5 V → −2.5…+7.5 V, ±600 cents | exact | correct |
| Mod two-resistor form, k = 3 | `mod-channels.md`, `bom.csv` | gain 4, intercept 3·3.3333 = 10.000, ±10.000 V | exact | correct |
| Mod four-resistor fudge | same | 40.2k/10k → ±10.05; 39k → 3.90, ±9.75 | exact | correct |
| `R-OPAMP-IN` on the four-resistor form | `mod-channels.md` | −196 mV zero, +9.657 V top | **−196.3 mV, +9.657 V** | correct — an unusually good derivation |
| Mod tolerance, zero | `mod-channels.md` | ±50.5 mV | **±50.51 mV** | correct |
| Mod tolerance, span | same | 19.703–20.303 V, −1.49/+1.52 % | **19.7025–20.3025 V, −1.485/+1.515 %** | correct |
| …"1.6× better", "1.33× better" | same | 1.6× / 1.33× | **1.61× / 1.34×** (4-resistor worst case: ±81.4 mV, 19.702–20.506 V) | correct |
| …"±18 cents per octave" | same | ±18 | **±18.2** | correct |
| **Zero-point formula** | `mod-channels.md` L131 | `2.5 − (10/3)k` | **2.5 − (5/6)k** | wrong formula, right numeric result |
| B/D-grade reset | `mod-channels.md` | +2.5 V on four jacks | 4X − 3X = X = 2.5 V | correct |
| Pitch load divider | ADR 0006, `pitch-stage.md` | −11.9 / −23.5 cents per octave | **−11.88 / −23.53** | correct |
| …at five octaves | ADR 0006 | 59.4 / 117.6 cents | **59.4 / 117.6** | correct |
| Affine mis-correction | ADR 0006 | +29 / +59 cents | **+29.4 / +59.1** | correct |
| Re-patch gain change | ADR 0006 | 0.98 %, 58 cents | **0.98 %, 58.8** | correct |
| Rail-divider sensitivity | ADR 0006 | 0.21 V/V; 3.0 / 12.5 cents | **0.2083; 3.0 / 12.5** | correct |
| "66 dB off the right node" | ADR 0006 | 22/0.011 = 2000 = 66 dB | **66.0 dB** | correct |
| PSRR term | ADR 0006 | 80 dB → 0.011 cents | **0.0096 cents** | correct |
| BAT54S leakage | ADR 0006 | 2 µA × 1 kΩ = 2 mV = 2.4 cents | exact | correct |
| ADC divider 15k/(10k+15k) | `carrier.md`, ADR 0003 | 0.600 | exact | correct |
| ADC clamp currents | `carrier.md` | 400 µA / ~800 µA | **400 / 800 µA** (conservative — the lower leg takes 47/267 µA of it) | correct |
| Sample-cap charge sharing | `carrier.md` | 80 nA/V, 480 µV/V, ~2 LSB | **80 nA/V, 480 µV/V, 1.68 LSB** | correct |
| LM317 divider 150/475 | `power-entry.md`, `bom.csv`, ADR 0004 | 5.21 V | **5.2083 V** | correct |
| …old 240/768 at ±4 % | `bom.csv` | 5.04–5.46 V | exact | correct |
| Chain self-test divider | `cluster-boards.md`, `bom.csv` | within 33 mV of the rail | **32.7 mV** | correct |
| Capacitive coupling divider | ADR 0001, `carrier.md` | 180 pC; 18 mV; 4.5 V; 37 % over; 1.36 V; lands at 1.94 V | **all exact** (5 V × 15/55 = 1.364 V) | correct — a genuinely well-done correction |
| Incident half-step at 68 Ω | ADR 0001 | 1.96 V against 2.0 V | **1.96 V** into 100 Ω | correct `[from memory: Z₀ ≈ 100 Ω]` |

### 3.3 CMRR and noise terms

| Quantity | Source | Claimed | Computed | Verdict |
|---|---|---|---|---|
| Unmatched 1 kΩ against the 1 MΩ pair | `breath-receive-stage.md` | 9.79e-4 → 60.2 dB | **9.793e-4 → 60.18 dB** | correct |
| 0.1 % module-side parts | same | 94 dB | **94.2 dB** | correct |
| "throws away fifty times that" | same | 50× | **49.95×** (33.97 dB) | correct |
| C_cm ±5 % mismatch | same | ~46 dB | **46.0 dB at 482 Hz** with 10 % total mismatch | correct — but the frequency is never stated; at 100 Hz it is 59.7 dB |
| C_cm ±1 % needed for 60 dB | same | 60 dB | **60.0 dB at 482 Hz** | correct, same caveat |
| Single-ended 15 nF | same | ~15 dB at 100 Hz | **19.7 dB** | **A39** |
| AGND bias diversion | `breath-receive-stage.md`, ADR 0003, `bom.csv` | tens of nA, 0.2 ppm | 70 nA / 350 mA = **0.2 ppm**; `bom.csv`'s 60 nA → 0.17 ppm | correct, order-of-magnitude |
| AGND sense-path error | `carrier.md` §2 | 13 mA × 0.168 Ω = 2.2 mV → 4.8 mV → 0.048 % | **2.184 mV → 4.772 mV → 0.048 %** | correct |
| Cable resistance | ADR 0003 | 0.168 Ω / 2 m 24 AWG; 8.4 µV at 50 µA | **0.1684 Ω** | correct |
| Shared-ground offsets | ADR 0003 | 16.8 / 33.7 / 58.9 mV | **16.8 / 33.7 / 58.9 mV** | correct |
| LED ground offset | ADR 0014 | 34 mV | **33.6 mV** at 200 mA | correct |
| Ratiometric rail errors | ADR 0003 | 21 / 52 / 104 mV | **21.0 / 52.4 / 104.9 mV** at mid-scale | correct |
| …vs the AGND path | ADR 0003 | "30 dB worse" | **44.2 dB** | **A28** |
| 16-bit LSB on 10 V | ADR 0003, ADR 0006, `latency-budget.md` | 153 / ~150 µV | **152.6 µV** | correct |

### 3.4 Current, power and thermal budgets

| Quantity | Source | Claimed | Computed | Verdict |
|---|---|---|---|---|
| Umbilical conversion factor | ADR 0005, ADR 0014 | ×0.49 | **5/(0.9 × 11.4) = 0.4873** | correct |
| Load table — quiescent | ADR 0005 | 212 mA, 2.4 W | **210.7 mA, 2.40 W** | correct |
| Load table — typical play | ADR 0005 | 359 mA, 4.1 W | **358.1 mA, 4.08 W** | correct |
| Load table — typical + WiFi | ADR 0005 | 414 mA, 4.7 W | **411.7 mA, 4.69 W** | correct |
| Load table — clamp-legal worst | ADR 0005 | **579 mA**, 6.5 W | **571.2 mA, 6.51 W** | **A52** — the heat column matches 571, not 579 |
| Load table — latched full white | ADR 0005 | ~1522 mA, ~17 W | **1521.5 mA, 17.35 W** | correct |
| 12 V vs 5 V delivery | ADR 0005 | 122 mV + 400 mV + 60 mV → 11.4 V, 5 %; 862 mA → 4.7 V, 6 %+ | **11.418 V, 4.85 %; 293 mV, 4.71 V, 5.8 %** | correct and internally self-consistent (constant power at the arriving voltage) |
| Regulator loading | `carrier.md` §1 | 680–780 mA, 68–78 % | **678–778 mA** | correct |
| Negative-resistance margin | `carrier.md` §1 | 1.13 W → 1.26 W, R_neg −103 Ω, 220× = 47 dB | **1.2556 W, −103.5 Ω, 219×, 46.8 dB** | correct |
| Load switch sense | `power-entry.md` | 50 mΩ; 18 mV; 6 mW at 360 mA | **50 mΩ, 18 mV, 6.48 mW** | correct |
| Inrush table (2.2 mF) | `power-entry.md` | 240/120 V/s; 0.53/0.26 A; 6.3/3.2 W; 0.16 J both | **240/120; 0.528/0.264; 6.34/3.17; 0.1584 J** | correct, including ½CV² |
| Current-limited start | `power-entry.md`, `bom.csv` | 1.0 A into 2.2 mF = 26 ms | **26.4 ms** | correct |
| Fault pulse | `power-entry.md` | 12 W × 50 ms = 0.6 J | exact | correct |
| …restated in the BOM | `bom.csv` `U-LOADSW` | 1.0 A, 75 ms, 0.45 J | **26 ms, 0.16 J** at 1.0 A | **A51** |
| Instrument bulk | `power-entry.md` | 2 × 100 µF + 2 × 1000 µF = 2.2 mF | exact | correct (an upper bound — `C-STRIP-BULK` is 470–1000 µF) |
| `R1` fault dissipation | `breath-receive-stage.md`, `bom.csv` | 11.8 mA, 139 mW vs 125 mW | **11.8 mA, 139.2 mW** | correct |
| `R-OUT-PROT` worst cases | `bom.csv` | 142 mW railed; 192 mW into a −5 V/220 Ω driver; old 101 mW; 250 mW = 1.3× | **141.6 / 192.0 / 101.0 mW; 1.30×** | correct — the 192 mW two-driver case is right |
| Jack clamp back-powering | `bom.csv` `D-JACK-CLAMP` | 42 mA/jack, 254 mA, 7.6 mA behind the 1 k | **42.3 / 253.8 / 7.62 mA** | correct |
| `R-SPI-PULL` clamp current | `bom.csv` | 430 µA | **430 µA** | correct |
| Key pull-up load | ADR 0001, `carrier.md`, `cluster-boards.md`, `bom.csv` | 1.43 mA, 18 keys = 25.8 mA, 4.4× the old 5.9 mA | **1.4348 mA, 25.83 mA, 4.39×** | correct |
| …reference shift | `carrier.md` | 0.077 % = 3.2 LSB = 0.2 % of 1594 | **0.0774 %, 3.17 LSB, 0.2 %** | correct (on the count figures of A42) |
| LM317 dissipation | `bom.csv`, ADR 0004 | ~13 mA, ~90 mW, "under 100 mW" | **88.3 mW** | correct |
| Rail bulk balance | `bom.csv` `C-BULK-RAIL` | 22 mA vs 10 mA = 2.2× | exact; 100 µF/47 µF rebalances it | correct |
| Strip current, 0.84 m | ADR 0014 | 0.50/0.17/0.07 A and 1.01/0.34/0.13 A | internally exact (25 and 50 LEDs, ⅓ per channel, ×0.4) | correct `[from memory: ~20 mA/LED white]` |
| Matrix current | ADR 0014 | 5 mA/channel, 15 mA/LED, 960 mA for 64 | exact | correct |
| Matrix umbilical conversions | ADR 0014 | 20–31 / 2 / 5 / 78 / 470 mA | **19.6 / 2.4 / 4.9 / 78.4 / 470.4** | correct |
| Thermal table | ADR 0014 | 12.1 W → 36 K; 17.7 W → 53 K; 1.5 W → 4 K, at 3 K/W | **12.12 → 36.3; 17.76 → 53.3; 4.5 K** | correct (17.7 W counts the matrix at the umbilical, which is the consistent convention) |
| 3 W clamp framing | ADR 0014 | ⅙ of pathological; ¼ of full white; ~75 % single hue; **60 % of one matrix channel** | 1/5.9; 24.8 %; 73.5 %; **160 % of one channel** | last one **A59** |
| Regulator overload | ADR 0014 | 960 + 330–400 = ~1.36 A | exact | correct |
| Dev-board bulk | ADR 0013 | 921600 baud, 60 Hz × 32 B = 2 % | **2.08 %** | correct |

### 3.5 Timing budgets

**Does the loop fit in 250 µs?** Recomputed from the parts as specified:

```
DAC     6 frames × 32 bits @ 2.0 MHz                        96.0 µs
ADC     18 clocks @ 0.9 MHz = 20.0 µs (24 clocks = 26.7)    20.0–26.7 µs
Keys    32 bits @ 1.0 MHz                                   32.0 µs
                                                           ----------
serialised total                                            148–155 µs  → 59–62 % of 250 µs
```

- `latency-budget.md` rule 1 books **136 µs / 54 %** using a **16 µs** key chain — that is 32 bits at 2 MHz, but ADR 0001 fixes the chain at **1 MHz** and says so twice ("~32 µs at 1 MHz, about 13 %"). **A9.**
- `carrier.md` §4 books **122.7 µs of SPI2 (49 %)** plus **32 µs of SPI3 "concurrent" (13 %)**. Concurrency is a firmware claim, not an arithmetic one; if the loop is serialised — which rule 1 assumes — the two pages disagree by 19 µs. **A24.**
- Both conclusions survive: 4 kHz closes with margin, 8 kHz does not (155 µs against a 125 µs period).
- The 8 kHz arithmetic in rule 1 (136 µs > 125 µs), the 200 µs case (312 µs) and the 125 µs case (237 µs) are all **correct as arithmetic**; with the corrected 32 µs chain they become 152, 328 and 253 µs, which makes the mid-range case fail outright rather than "leave no margin".
- `0.6 MHz does not close`: 192 bits / 0.6 MHz = **320 µs** ✓ correct (ADR 0004).
- Retrigger count: 6 frames per 250 µs over 99 ms = **2376** at 16 µs spacing ✓; 83 pC at 5.21 µA × 16 µs ✓ (`digital-and-supervision.md`, both correct).

**Latency budget page.** Every individual row is right; both totals are not.

| Row | Claimed | Computed |
|---|---|---|
| Receive filter 482 Hz | 330 µs | **330.2 µs** ✓ |
| Output RC 480 Hz | 332 µs | **331.6 µs** ✓ |
| "the real figure is 632 µs" | 632 | **662 µs** (A11) |
| Analog total | ~2.83 ms | **2.842 ms** (A12) |
| Digital extra (282+24+20+96+10+82, +0–250 sampling) | — | **514–764 µs** |
| Digital total | ~2.9–3.1 ms | **2.68–2.93 ms** (A10) |
| Margin against 5 ms | 1.6× | **1.7×** on the corrected total |
| Mod reconstruction 1.94 kHz | 82 µs | **82.0 µs** ✓ |
| Pitch 15.9 kHz | ~10 µs | **10.0 µs** ✓ |
| 500 Hz pole group delay | 318 µs | **318.3 µs** ✓ |

ADR 0003's own latency table sums to **1.44 ms** ("< 1.5 ms" ✓), and its "~3.1 ms"
is inherited from A10.

### 3.6 Counts and part-quantity arithmetic

| Claim | Source | Verdict |
|---|---|---|
| 18 + 3 + 8 + 3 = 32 bits | `key-layout.yaml`, ADR 0001, `cluster-boards.md` | correct |
| 18 + 3 + 6 + 5 = 32 bits | `carrier.md` | sums correctly but uses the **superseded** 6/5 split — **A13** |
| Marker read in bit order `10·01·10·01` | `cluster-boards.md` | correct against its own bit table (6/7, 14/15, 20/21, 29/30) |
| "16 parts saved" by strapping markers | `cluster-boards.md` | correct if a strapped marker saves a pull-up and a cap (8 × 2) |
| 21 networks = 18 + 3 | everywhere | correct — **but the 3 free bits that ADR 0001 fix 6 and `cluster-boards.md` §4 say "must be pulled" have no pull-up in the 21** |
| 63 network passives = 21 × 3 | ADR 0001, `carrier.md`, `bom.csv` | correct |
| Per-board switch counts 5/4/6/3 = 18 | `cluster-boards.md`, `key-layout.yaml` | correct |
| `J-CHAIN` 1+2+2+2+1 = 8 | `carrier.md`, `cluster-boards.md`, `bom.csv` | correct — contradicted by "~4"/"five" elsewhere (**A45, A46**) |
| Loom conductors 12 + (6–8) + 9 + 1 = 28–30 | `carrier.md` | correct |
| `C-DECOUPLE` qty 21 = 12+2+2+2+1+1+1 | `bom.csv` | arithmetic correct — but it counts **2 for the LM311**, and the presence comparator is deleted (`digital-and-supervision.md`, `bom.csv` `LED-PANEL`). Should be 19, or the LM311 should be restored to the design |
| `C-DECOUPLE-CARRIER` qty 7 | `bom.csv` | correct (1+1+1+1+1+2) |
| `R-OPAMP-IN` qty 7 | `mod-channels.md`, `bom.csv` | correct (pitch, 4 mods, offset buffer, VREFOUT follower) |
| `R-BIAS-DAC` qty 6 | `bom.csv` | consistent with 6 DAC-driven nodes; note the 7-vs-6 step against `R-OPAMP-IN` is deliberate |
| OPA2197: 6 packages, 12 halves, 10 used | `bom.csv`, `breath-output-stage.md` | correct — **A36** contradicts it |
| DAC: 6 of 8 channels used, 2 spare | ADR 0006 | correct (1,2,3,4,5,7) |
| 8 BAV99 = 6 output + 2 breath input | `bom.csv` | correct |
| Panel arithmetic: (8×5.08)−0.3 = 40.34; (40.34−23.8)/2 = 8.27; 6HP → 3.19 | ADR 0004, `bom.csv` | all correct |
| Matrix window: 8 × 2.6 = 20.8 mm; 10 pins = 22.86 mm; 23.5 − 2.6 = 20.9 mm vs 22 mm | `carrier.md` §7 | all correct — the conclusion (a 22 mm hole does not fit) follows |
| 57 − 2×4 = 49 mm; 49 − 45 = 2 mm/side; 29 × 2.54 = 74 mm; 2(100+45) = 290 mm | `carrier.md` | all correct |

---

## 4. Unverifiable inputs

Results below are only as good as the marked input.

- `[from memory]` **INA828 gain equation** `G = 1 + 50 kΩ/R_G` — every breath gain figure depends on it.
- `[from memory]` **MPXV4006DP transfer function.** ADR 0003 uses `Vs·(0.1533·P + 0.04)`, which is self-consistent with 0.2 V / 4.80 V / 766 mV/kPa. I recall the datasheet constant as **0.0333** (→ 0.167 V at zero). If so, the pedestal, the REF trimmer range and the 4.6 V span all shift. Check before ordering.
- `[from memory]` **Pedestal spec band 0.152–0.378 V.** It is asymmetric about the 0.200 V typical (−48 mV/+178 mV), which is unusual for an offset spec. The entire trimmer-range argument rests on it.
- `[from memory]` **OPA2197 open-loop output impedance**, which sets A40's 21 kHz vs 210 Hz.
- `[from memory]` **74HC123 K = 0.45** for the 99 ms timeout.
- `[from memory]` **Cermet trimmer tempco.** `pitch-stage.md`'s 0.068 cents needs ~125 ppm/°C; ADR 0006's trim table needs 250 ppm/°C; ADR 0006's "2 ppm/°C" line needs 100 ppm/°C. Three values (**A22**).
- `[from memory]` **R-78E5.0 switching frequency** (330 kHz vs ADR 0003's 500 kHz, **A31**).
- `[from memory]` **WS2815 per-LED current** (~20 mA white) and **WS2812C-2020** 5 mA/channel.
- `[from memory]` **0805 ≈ 125 mW**, 1N5817 V_f, BAV99 leakage, Cat5 Z₀ ≈ 100 Ω and ~200 pF, MPXV4006DP supply 10 mA.
- **Unverifiable as stated** (no inputs given anywhere): ADR 0003's "19–34 dB" and "~24 dB" difference-amp CMRR figures (the difference amp's resistor values are never given); ADR 0004's "0.66 V against a ~0.55 V window"; ADR 0004's "5.7–7.2 cents" internal-ground and "~4.8 cents" bus-ground terms; `pitch-stage.md`'s "18°/under 10°" phase margins and "nominal gain 2.0213" (`R-OFFINJ` has no value); `bom.csv`'s "5.08 V overshoot"; ADR 0005's "531 mA" (**A61**) and "~350–375 mA" polyfuse derating; ADR 0014's "loop gain ~0.004".
- **Reproduced but unattributed:** the ~80 mV Schottky V_f modulation → "~20 cents" works out exactly at the 0.2083 V/V rail sensitivity (80 mV × 0.2083 = 16.7 mV = 20 cents). Good.

---

## 5. What is worth fixing in one pass

1. **The breath full-scale number** (A1, A2, A3, A4) — one value, wrong or stale in four places, and it inverts the presence comparator's polarity.
2. **`C-FB-PITCH`** (A5, A6, A7, A8) — 1 nF survives in the drawing that a layout gets built from, and in the ADR, against 2.2 nF everywhere else.
3. **The loop budget** (A9, A24) — settle the key-chain clock and the ADC frame length, then restate one duty figure in both files.
4. **The marker bits** (A13, A14, A37-adjacent) — `carrier.md` is the only file still on 6/5.
5. **ADR 0006's precision table** (A17, A19, A22) and **`pitch-stage.md`'s duplicate table** (A18) — the pivot error was found and corrected in one file and left standing in two others, including a second contradictory table four lines below the correction.
6. **`power-entry.md` vs `bom.csv`** (A49, A50) — the page is drawn against a superseded LED node and superseded rail capacitors.
