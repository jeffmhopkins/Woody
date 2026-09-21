# S1 — Arithmetic audit

**Scope:** recompute every number in the five module schematic pages,
`docs/reference/latency-budget.md`, and ADRs 0003, 0004, 0005, 0006 and 0014,
from the premises those documents themselves state. Topology and judgement are
out of scope except where a premise and its result cannot both be true.

**Snapshot:** working tree at commit `42a716d`, 2026-09-21. The repository was
being edited by other agents throughout this audit — `breath-receive-stage.md`,
`pitch-stage.md`, `mod-channels.md`, `digital-and-supervision.md`, ADR 0003,
ADR 0004, ADR 0006 and `bom.csv` all changed under me between first read and
final read. **Every line number below was re-resolved against `42a716d`.**
Unchanged since `b9beb48`: `latency-budget.md`, `power-entry.md`, ADR 0005,
ADR 0014.

**Datasheet-blocked:** nxp.com, ti.com, analog.com are unreachable. Where a
figure rests on a datasheet value (INA828 50 k, MPXV4006DP tempco, LT5400
tracking, 1N5817 V_f, WS2815 per-LED current, LM317 reference tolerance,
OPA2197 swing) the datasheet value is taken as stated and only the arithmetic
downstream of it is checked. Those are marked **[ds]**.

---

## Discrepancy table

| # | File:line | Stated | Recomputed | Which is wrong |
|---|---|---|---|---|
| 1 | breath-receive-stage.md:149 | C_diff 15 nF → **531 Hz** differential pole | **482 Hz** (R1+R2+R1b+R3 = 22 kΩ) | The figure. 531 Hz assumes 20 kΩ, i.e. the circuit before `R1b` was added |
| 2 | breath-receive-stage.md:59, 94 | in-amp reaches **−9.6 V** at full | **−9.94 V** | The figure. The page's own line 164 computes the span as 9.94 V |
| 3 | breath-receive-stage.md:76 | pedestal leaves **4–9 %** of full scale | **3.3–8.3 %** | The figure |
| 4 | breath-receive-stage.md:213 | bias pair diverts **tens of nA**, **0.2 ppm** | **0.2–4.8 µA**, **0.6–13.7 ppm** | The premise. Conclusion ("negligible") survives |
| 5 | breath-receive-stage.md:222 | single-ended cap caps CMRR at **~15 dB at 100 Hz** | **~20 dB** | The figure (or an unstated R) |
| 6 | breath-receive-stage.md:56 vs :152 | REF trimmer **"from VREFOUT"** vs **"From the LM317 rail, never `VREFOUT`"** | — | Line 56. ADR 0003:574-581 and `bom.csv:108` both say LM317 |
| 7 | breath-receive-stage.md:70, 273 | "`REF` ties to ground" / "now that `REF` is grounded" | REF = +0.437 V from a trimmer | Both lines. Stale premise |
| 8 | breath-receive-stage.md:64, 133 | downstream stage is **½ OPA2197**; six packages leave **one** spare | BOM: **two** halves for that stage, **two** spare | Breath page. `bom.csv:13` now says "TEN used … Two spare" |
| 9 | breath:261 / 0003:595 / 0006:223 | **20 mV** / **23 mV** / **23 mV** of warm-up drift | **21.6–21.9 mV** | All three. Same quantity, three values |
| 10 | pitch-stage.md:165 | `C-FB-PITCH` **1 nF**, handover **~16 kHz** | 2.2 nF → **7.2 kHz** | Line 165. Line 134 adopts 2.2 nF |
| 11 | pitch-stage.md:175 | pole **15.9 kHz**, zero **31.8 kHz** | 2.2 nF → **7.23 / 14.5 kHz** | The figures. Computed for the superseded 1 nF |
| 12 | pitch-stage.md:271-279 | table lists LT5400 twice (**0.027** and **~0.1** cents) and DAC ref twice (**0.42** and **~0.5**) | — | The stale rows 276-279 |
| 13 | pitch-stage.md:279 | DAC INL ±4 LSB = **~0.4 cents** | **0.73 cents** | The figure (×2 output gain omitted) |
| 14 | pitch-stage.md:276 | two discrete 0.1 % parts = **~1.2 cents** | **0.38 cents** | The figure. The page's own line 289 says 0.38 |
| 15 | pitch-stage.md:275 | `TRIM-GAIN` tempco **0.068 cents** | **0.055 cents** | The figure (minor) |
| 16 | pitch-stage.md:199 | composite **−3 dB at 12.2 kHz** | cascade gives **~7.5 kHz** | Not derivable from stated premises — see detail |
| 17 | pitch-stage.md:200 | **−41 dB** at 1 MHz | **−42.0 dB** | Rounding (minor) |
| 18 | pitch-stage.md:248 vs :130 | "the exact DC solve gives gain **2.020000**" vs "Nominal is dead on **2.000**" | 2.02 = trimmer at full | Line 248 states the trimmed-to-max case as if nominal |
| 19 | pitch:140, mod:101 | "±12 V less **two** Schottky drops" | power-entry shows **one** diode per rail; 0006:120 says "~0.35 V of Schottky" | The "two drops" premise. The 11.45 V answer is roughly right by luck |
| 20 | pitch:294 vs mod:57, BOM R-PRECISION | two spare LT5400 sections can make 1:3 | 1:3 needs **3+1 = 4** sections; 2 are used | mod-channels.md:57 and the BOM note |
| 21 | mod-channels.md:120-124 | zero **±81 mV**, span **19.70–20.51 V**, **±2 %**, **±24 cents** | **±50 mV**, **19.70–20.30 V**, **±1.5 %**, **±18 cents** | All four. Computed for the superseded four-resistor 40.2 kΩ stage |
| 22 | mod-channels.md:132, 146, 152, 157 | gain **4.02**, range **±10.05 V**, **−10.05 V** | **4.000**, **±10.000 V**, **−10.000 V** | Stale coefficients. The Values table (93-95) is now correct |
| 23 | mod-channels.md:168 | "At 2.5 V into 2.5 kΩ that is **1 mA**" | **1.33 mA** | Line 168. Line 16 already says ~1.3 mA |
| 24 | power-entry.md:145 | LED current on the 5 V rail **~3.8 mA** | **3.66 mA** | The figure (uses 800 Ω, not the specified 820 Ω) |
| 25 | 0004:374-387 vs digital-and-supervision.md:99-110 + BOM:100 | sense **the BREATH node**, threshold **+100 mV** vs sense **the in-amp output**, threshold **V_REF/2 ≈ 218 mV** | — | ADR 0004. Two of three agree |
| 26 | digital-and-supervision.md (tap loading) | tap must present **≥ 9.75 MΩ** for 60 dB | **≥ 10.8 MΩ** | Minor |
| 27 | latency-budget.md:60 vs :146 | SAR ADC **50–200 µs** vs loop pass "ADC **24 µs**" | at 200 µs one pass is **312 µs** > the 250 µs period | One of the two. **4 kHz does not close on the slow figure** |
| 28 | latency-budget.md:96 vs :146 | key chain **< 10 µs** vs **16 µs** | 4 × 8 bits at 2 MHz = **16 µs** | Line 96 |
| 29 | latency-budget.md:100 | "DAC update + settle **~60 µs**" | **106 µs** (96 + 10) | Line 100; no derivation given |
| 30 | latency-budget.md:65 | digital total **~2.9–3.1 ms** | min **2.70 ms**, mean 2.91, max 3.11 | The low end is the *mean*, not the minimum |
| 31 | latency-budget.md:42 | receive filter **531 Hz → 300 µs** | **482 Hz → 330 µs**; analog total **2.84 ms** | Follows from #1 |
| 32 | 0005:96 | 5 V umbilical would draw **862 mA** | **872 mA** | The figure |
| 33 | 0005:160 | clamp-legal worst umbilical **579 mA** | **571 mA** | The figure. Its own body-heat cell (6.5 W) agrees with 571 |
| 34 | 0005:161 | 5 V **1023 mA** / 12 V **1023 mA** / umbilical **1132 mA** / **12.2 W** | 1132 mA implies 5 V ≈ **226 mA**; with 1023 mA the umbilical is **1522 mA**; heat is **12.6–12.9 W** | The 5 V cell (duplicated from 12 V) and the heat cell |
| 35 | 0005:164-165 | 531 vs 579 mA is "a **5 %** difference" | **9.0 %** | The figure |
| 36 | 0005:263 | "clamp-legal worst case of **630 mA**" | table says **579 mA** (recomputed 571) | One of the two |
| 37 | 0005:292 | 12 V on a 7 V abs-max is "roughly **66 %** over" | **71 %** | The figure |
| 38 | 0005:307 vs power-entry:95, 98 | fault timer must pass "the **75 ms** start" | at the adopted 1.0 A limit the start is **26 ms**; timer set to **50 ms** | 0005:307 carries a 500 mA-limit figure into a 1.0 A design |
| 39 | 0005:159 | typical + WiFi umbilical **414 mA** | **412 mA** | Minor |
| 40 | 0005:208 | "**928 mA** … does not fit behind one 1 A part" | 928 mA < 1000 mA | Needs a derating premise that is not given |
| 41 | 0005:74, 0003:101, :116, :518, BOM:46 | sensor output **0.2–4.7 V** | **0.2–4.80 V** from ADR 0003:121's own transfer function | The "4.7 V" figure, in five places |
| 42 | 0006:126 | 305 µV/LSB is "**0.003 %** of full scale" | **0.0015 %** of the 20 V span | Ambiguous "full scale"; on the stated 20 V it is 0.0015 % |
| 43 | 0006:388-390 | net ratio tempco **22 / 34 / 58 ppm/°C** | implies a **250 ppm/°C** trimmer; 0006:368 + BOM say **100** → **14.5 / 19 / 28** | The unstated 250 ppm/°C premise |
| 44 | 0006:388 | 5 % trim = **2.4 cents** over 10 °C | **0.4–0.6 cents** | The figure. Gain error applied to 9 V instead of the 2.25 V lever |
| 45 | 0006:414 | ±4 LSB = **0.66 cents**, ±12 LSB = **2.0** | **0.73** and **2.20** | The figures (LSB taken on 9 V, not 10 V) |
| 46 | 0006:527 | "**Eighty-six** decibels off the right node" | **66 dB** | The figure |
| 47 | 0006:532, :678 | LM317 at **5.25 V** | **5.21 V** (0004:157, power-entry:18-19) | The 5.25 V figure |
| 48 | 0006:140 | `Vout = 4 × (Vdac − Voffset)` with Voffset = **3.3333 V** | at Vdac 2.5 that gives **−3.33 V**, not 0 V | The formula, once Voffset became 3.3333 V |
| 49 | 0006:186 | "Mod offset \| written once at boot \| the shared **2.5 V**" | **3.3333 V**, refreshed **every pass** | Both cells |
| 50 | 0006:185 | row "Breath zero offset \| continuous, slow" | that channel is deleted | Stale row |
| 51 | 0003:416 | **7 channels** at 4 kHz = **0.90 Mbit/s** | **6 channels** = **0.77 Mbit/s** (0004:54) | ADR 0003 |
| 52 | 0003:533, :543-544 | **220 nF** at the ADC, "**~600 Hz**", "**58 dB** at 500 kHz" | 220 nF on 6 kΩ = **121 Hz**; BOM specifies **47 nF** (564 Hz, 55 dB at 330 kHz) | ADR 0003, in full |
| 53 | 0003:539 | buck "running at **500 kHz**" | BOM:45 says the R-78E5.0 switches at **330 kHz** | ADR 0003's premise |
| 54 | 0003:450 | ratiometric path "roughly **30 dB** worse" than 0.13 mV | **44–58 dB** | The figure |
| 55 | 0003:364 | in-amp absorbs "the **~2.13×** scaling stage" | **2.174** needed, **2.185** built | The figure (uses 4.7 V as a span) |
| 56 | 0003:402 | 8 MHz against 160 Hz is "**six** orders of margin" | **5 × 10⁴** = 4.7 orders | The figure |
| 57 | 0003:717 | bore moves first resonance by **20–40 Hz** | **< 2 Hz** at any plausible bore | The figure |
| 58 | 0003:19-27 | latency table: SPI to DAC **~50 µs**, total **< 1.5 ms** | **96 µs**; current total **2.9–3.1 ms** | Stale table |
| 59 | 0003:254 | breath path "**~2.6 ms**" | **2.84 ms** analog / **2.70–3.11 ms** digital | Stale |
| 60 | 0004:70 | 220 Ω with 200 pF is a **~7.9 MHz** corner | **3.6 MHz** | The figure (7.9 MHz is the 100 Ω case) |
| 61 | 0004:82 | "SPI to the DAC, **~1 MHz**" | **2 MHz** (0004:37, :54) | Line 82 |
| 62 | 0004:280 | power-tree box "LM317LZ **5.25V**" | **5.21 V** (0004:157) | Line 280 |
| 63 | 0004:199 | OPA2197 on ±12 V "reaches roughly **11.9 V**" | rail after the Schottky is ~11.6 V → **~11.45 V** | Line 199 ignores the entry diode |
| 64 | 0004:246 vs :252-254 | table **~320 mA**; text **290 mA** | — | Same quantity, two values |
| 65 | 0004:176 | shrinking R2 "**halves** the I_ADJ contribution" | 475/768 = a **38 %** reduction | Wording vs arithmetic |
| 66 | 0014:327-328 | matrix shares **one** 1 A R-78E5.0 with **both** dev boards | ADR 0005:189-193 splits into **two** bucks | ADR 0014 (stale) |
| 67 | 0014:146 | matrix adds **5.6 W** (total 17.7 W) | 4.8 W / 0.90 = **5.33 W** → **17.4 W** | Uses the 85 % efficiency ADR 0005:171 retracted |
| 68 | 0014:173 | 3 W = "a full field at around **60 % of one channel**" | 3 W = **63 % of a full white field**; one channel full field is only **1.6 W** | The phrasing/figure |

---

## Detail

### Breath receive stage

**1. The differential pole is 482 Hz, not 531 Hz.**
`[repo]` `hardware/module/breath-receive-stage.md:149` — "**C_diff** | 15 nF C0G | 531 Hz differential pole".
`[repo]` `:145-147` — R1 1 kΩ, **R1b 1 kΩ** (its new twin in the AGND leg), R2/R3 10 kΩ.
`[calc]` differential source resistance seen by C_diff = (R1+R2) + (R1b+R3) = 11 kΩ + 11 kΩ = 22 kΩ.
f = 1/(2π · 22 000 · 15e-9) = 1/(2.0735e-3) = **482.3 Hz**.
531 Hz = 1/(2π · 20 000 · 15e-9) = 530.5 Hz — i.e. R2+R3 only, which was the circuit *before* `R1b` was added by the same revision. (Before `R1b`, with R1 on one leg only, it was 21 kΩ → 505 Hz. 531 Hz has never matched the drawing.) Including C_cm's differential contribution (15 + 1.5/2 = 15.75 nF) gives 459 Hz.
This is a premise-changed-later error: `R1b` was added for CMRR and nobody re-ran the corner. It propagates to `latency-budget.md:42` (#31).

**2. −9.6 V contradicts the page's own 9.94 V.**
`[repo]` `:58-59` — "Vout = −2.185·(V_BREATH − V_AGND) + V_REF = 0 V at rest, −9.6 V at full"; `:94` repeats it.
`[repo]` `:164` — "effective 2.1611 | **jack span 9.94 V**"; `:159` — sensor span 4.6 V.
`[calc]` with REF trimmed so rest = 0 V, full output = −(effective gain) × (sensor span) = −2.1611 × 4.6 = **−9.941 V**. Using the untrimmed G = 2.1848: −2.1848 × 4.6 = −10.05 V. Neither is −9.6 V. **−9.6 V is wrong; it should be −9.94 V.**

**3. 4–9 % of full scale is 3.3–8.3 %.**
`[repo]` `:72-77` — pedestal spec band 0.152–0.378 V, "That left 4–9 % of full scale standing at the jack".
`[calc]` at G = 2.185 the pedestal appears at the in-amp output as 0.152 × 2.185 = 0.332 V and 0.378 × 2.185 = 0.826 V. Against the 10 V wanted span: **3.32 % and 8.26 %**. Against the 9.94 V achieved span: 3.34 % and 8.31 %. Not 4–9 %.
Note the page's *new* line 91 does this same conversion correctly (see Verified, V-b).

**4. "Tens of nanoamps" is off by one to two orders.**
`[repo]` `:212-213` — "1 MΩ to module analog ground diverts tens of nanoamps against a ~350 mA power return — about 0.2 ppm." Identical claim at `0003:386-387`.
`[calc]` the signal-leg input sits at the sensor voltage, 0.2 V at rest to 4.8 V at full. I = V/R4 = 0.2/1e6 = **200 nA** at rest, 4.8/1e6 = **4.8 µA** at full.
Ratio to a 350 mA return: 200e-9/0.35 = 5.7e-7 = **0.57 ppm**; 4.8e-6/0.35 = 1.37e-5 = **13.7 ppm**.
"Tens of nanoamps" would be ~70 nA, which is where 0.2 ppm comes from; no node in the circuit carries that. **The conclusion — the sense-return rule survives in substance — is unaffected**, but both numbers are wrong.

**5. A single-ended 15 nF gives ~20 dB, not 15 dB.**
`[repo]` `:220-222` — "a single-ended capacitor to ground on one leg … would cap effective CMRR at about 15 dB at 100 Hz". The capacitor value is not stated in the sentence; the only differential cap on the page is C_diff = 15 nF (`:149`) and the leg resistance is 11 kΩ (`:145-147`).
`[calc]` imbalance = |1 − 1/(1 + jωRC)| / 1, ωRC = 2π · 100 · 11 000 · 15e-9 = 0.1037.
|j0.1037/(1+j0.1037)| = 0.1037/1.00536 = 0.10315 → CMRR = 20·log₁₀(1/0.10315) = **19.7 dB**.
15 dB would need ωRC ≈ 0.181, i.e. ~26 kΩ or ~26 nF. **Unsourced premise; recomputed ~20 dB.** The argument (dominant differential cap) is unaffected.

**6–8. Contradictions on the same page.**
`[repo]` `:56` "buffered **from VREFOUT**" vs `:152` "**From the LM317 rail, never `VREFOUT`**"; `bom.csv:108` and ADR 0003:574-581 both say the LM317 rail, and give the reason (VREFOUT is disabled at power-on). **Line 56 is wrong.**
`[repo]` `:70` section heading "`REF` ties to ground" and `:273` "now that `REF` is grounded it touches the breath stage in no way at all" — both contradict `:86` and `:152`. The conclusion at `:272-277` survives (a trimmer off the LM317 rail is equally untouched by `CLR`), but the stated reason does not. The same stale sentence is in `firmware/README.md:70`.
`[repo]` `:64` draws the downstream gain/offset stage as "**½ OPA2197**" and `:133` says six packages leave "**still one**" spare; `bom.csv:13` says "**TWO** for the breath gain/offset stage … **Two spare**".
`[calc]` halves used per the BOM list: pitch 1 + mods 4 + mod-offset follower 1 + VREFOUT follower 1 + breath REF buffer 1 + breath gain/offset 2 = **10**; 6 packages = 12 halves → **2 spare**. Per the schematic's 1 half for the breath stage: **9 used**, so 5 packages would suffice with 1 spare. The two documents cannot both be right.

**9. Warm-up drift: 20 mV, 23 mV, 23 mV, none of them right.**
`[repo]` `breath:261-264` "on the order of **20 mV** in 10 V … offset tempco of ~0.5 mV/K"; `0003:595` "a 20 K interior rise moves the jack about **23 mV** out of 10 V — 0.23 %"; `0006:223` "**~23 mV** in 10 V".
`[calc]` **[ds]** 0.5 mV/K at the sensor × 20 K = 10 mV; × the effective in-amp gain 2.1611 = **21.6 mV** (× the untrimmed 2.1848 = 21.8 mV). Not 20, not 23. 23 mV would need a gain of 2.30.
The ΔT is stated only in ADR 0003 (20 K); `breath:261` gives none.

---

### Pitch stage

**10-11. `C-FB-PITCH` is 2.2 nF in one place and 1 nF in two others.**
`[repo]` `:134` "**C-FB-PITCH** | **2.2 nF C0G**"; `:198` "**`C-FB-PITCH` goes to 2.2 nF**"; but `:165` still reads "`C-FB-PITCH` **1 nF** … above ~16 kHz" and `:164` "DC to ~16 kHz", and `:175` "**Pole at 15.9 kHz**, zero one octave above at **31.8 kHz**".
`[calc]` pole = 1/(2π·R2·C). At 1 nF: 1/(2π·10 000·1e-9) = **15.92 kHz**, zero at 2× = 31.83 kHz — so lines 165/175 are internally consistent *with the deleted 1 nF*.
At the adopted 2.2 nF: pole = 1/(2π·10 000·2.2e-9) = **7.234 kHz**, zero = **14.47 kHz**, handover ~7 kHz not ~16 kHz.

**12. The accuracy table contains two copies of itself.**
`[repo]` `:271-279`:
```
| DAC internal reference   | 0.42 cents  |   ← new
| LT5400 ratio tracking    | 0.027 cents |   ← new
| TRIM-GAIN tempco         | 0.068 cents |   ← new
| LT5400 ratio tracking    | ~0.1 cents  |   ← old, same term again
| DAC internal reference   | ~0.5 cents  |   ← old, same term again
| OPA2197 offset drift     | <0.1 cents  |
| DAC INL, ±4 LSB typical  | ~0.4 cents  |   ← old
```
Two terms appear twice with different values. The new rows are the correct ones:
`[calc]` DAC reference **[ds]** 5 ppm/°C × 10 °C = 50 ppm; reference drift pivots at Vout = 0 with a 7 V lever → 7 × 50e-6 = 350 µV → 350 µV × 1.2 cents/mV = **0.42 cents** ✓.
`[calc]` LT5400 **[ds]** 1 ppm/°C × 10 °C = 10 ppm of ratio; ratio drift pivots at V_ref = 2.5 V, lever = 4.75 − 2.5 = 2.25 V → dVout = 2.25 × 1e-5 = 22.5 µV → **0.027 cents** ✓.

**13. DAC INL ±4 LSB is 0.73 cents, not 0.4 and not 0.66.**
`[repo]` `pitch:279` "±4 LSB typical | ~0.4 cents"; `0006:414` "±4 LSB typical is 0.66 cents, ±12 LSB is 2.0 cents".
`[calc]` 16-bit, DAC full scale 5.000 V → 1 LSB = 5/65536 = 76.29 µV. Stage gain 2 → **152.59 µV/LSB at the jack**. 4 LSB = 610.4 µV. One semitone = 1/12 V = 83.333 mV, so cents = 610.4e-3/83.333 × 100 = **0.732 cents**. 12 LSB → **2.20 cents**.
`~0.4` = 0.366 cents = 4 LSB measured *at the DAC*, forgetting the ×2. `0.66` = 4 × (9 V/65536), i.e. the LSB taken on the 9 V used window instead of the 10 V full span. Both understate.

**14. "1.2 cents" for discretes contradicts the same page's 0.38 cents.**
`[repo]` `:276` "two discrete 0.1 % parts, which would be ~1.2 cents"; `:288-289` "two 0.1 % / 10 ppm discretes give **0.38 cents**"; `bom.csv:15` "14.1ppm/degC of ratio drift, about **1.2 cents at +7V** over 10 degC".
`[calc]` two independent 10 ppm/°C parts → RSS ratio tempco = 10√2 = **14.14 ppm/°C**; over 10 °C = 141.4 ppm. A *ratio* drift pivots at V_ref: dVout = 2.25 × 141.4e-6 = 318 µV → **0.382 cents**. Applying it instead about Vout = 0 with a 7 V lever gives 7 × 141.4e-6 = 990 µV → 1.19 cents — which is exactly the 1.2 cents figure, computed with the wrong pivot. **0.38 cents is right; 1.2 cents is the same pivot error the page's own line 266 identifies.** `bom.csv:15` still carries it.

**15. TRIM-GAIN tempco.** `[repo]` `:275` "**0.068 cents** | 200 Ω cermet".
`[calc]` **[ds]** 200 Ω is 200/10 200 = 1.96 % of the ratio; cermet ~100 ppm/°C → contribution 1.96 ppm/°C; over 10 °C = 19.6 ppm of ratio → dk = 1.02 × 19.6e-6 = 2.00e-5 → dVout = 2.25 × 2.00e-5 = 45.0 µV → **0.054 cents**. 0.068 cents needs ~25 ppm. Minor, and the conclusion (second smallest term) holds either way.

**16-17. The composite filter figures.**
`[repo]` `:198-200` "**`C-FB-PITCH` goes to 2.2 nF**, which with the jack cap restored is maximally flat: **−3 dB at 12.2 kHz** … and **−41 dB at 1 MHz** against the 6 dB the shelf gives alone."
`[calc]` −41 dB: the shelf asymptote is 20·log₁₀(2) = **6.02 dB** and the jack RC (1 kΩ × 10 nF, f₀ = 15.92 kHz) at 1 MHz gives 20·log₁₀(1/√(1+(1000/15.92)²)) = **−35.96 dB**. Sum = **−41.98 dB**, so −42 dB, not −41.
`[calc]` −3 dB point: cascading the 2.2 nF shelf |H₁| = √(4+x²)/(2√(1+x²)), x = f/7.234 kHz, with the jack pole |H₂| = 1/√(1+(f/15.92)²):
at f = 7.5 kHz → |H₁| = 0.7819, |H₂| = 0.9042, product 0.7071 = **−3.01 dB**;
at f = 12.2 kHz → |H₁| = 0.6671, |H₂| = 0.7937, product 0.5295 = **−5.5 dB**.
So a straight cascade puts −3 dB at **~7.5 kHz**, *below* ADR 0006's 10–20 kHz window, not at 12.2 kHz. The 12.2 kHz figure may come from a closed-loop analysis in which the jack cap sits inside the DC loop — but **no derivation is given**, and the number cannot be reproduced from the page's own component values. Same for the "18° of phase margin … under 10° with four destinations" at `:207-208`. Both need their working written down.

**18. Nominal gain quoted two ways.** `[repo]` `:130` "Nominal is dead on **2.000** and the trimmer has no downward authority" vs `:248` "the exact DC solve gives gain **2.020000** for every load".
`[calc]` gain = 1 + (R2 + TRIM)/R1 = 1 + (10 000 + 200)/10 000 = **2.020** with the trimmer at full; = **2.000** at zero. The load-independence claim is the point and is unaffected, but the solve is quoted at one end stop and called "the" gain.

**19. "Two Schottky drops."** `[repo]` `pitch:140`, `mod:101` — "±12 V less two Schottky drops reaches ~±11.45 V".
`[repo]` `power-entry.md:15, 22, 39` — D1 feeds module analog +12 V, D2 feeds the umbilical branch (parallel, not in series), D3 feeds −12 V. **One diode is in series with any given analog rail.**
`[repo]` `0006:120` — "±12 V rails less ~0.35 V of Schottky leaves ±11.65 V, and an OPA2197 reaches ~±11.45 V".
`[calc]` ADR 0006's route: 12 − 0.35 = 11.65 rail, op-amp within 0.20 V of it → 11.45 V. The schematic pages' route: 12 − 2×0.275 = 11.45 V with the op-amp reaching its rail exactly. Same answer, incompatible premises, and only one diode exists. ADR 0004:199's "roughly 11.9 V" ignores the diode entirely — three values for one quantity.

**20. Two spare LT5400 sections cannot make 1:3.** `[repo]` `pitch:294-295` says so explicitly; `mod-channels.md:57` still says "a 1:3 ratio that three sections of an LT5400 give directly against the fourth" and `bom.csv:15` says "the other two are available for the mod channels, which want 1:3".
`[calc]` 1:3 from equal 10 kΩ sections = three in series against one = **4 sections**. Two of four are committed to pitch. 2 ≠ 4.

---

### Mod channels

**21. The tolerance table is still the four-resistor table.**
`[repo]` `:93-95` now specifies the two-resistor form: R1 = 10 kΩ, **R2 = 30 kΩ**, k = 3, V_ref = 3.3333 V.
`[repo]` `:113-124` still reports "Enumerating all sixteen corners of **four** 1 % resistors": zero point **±81 mV**, span **19.70–20.51 V**, "**±2 %** of gain", "**±24 cents** per octave".
`[calc]` for the adopted two-resistor stage, Vout = Vdac(1+k) − k·V_ref, k = R2/R1.
Zero point (Vdac = 2.5): Vout = 2.5 − 0.83333·k. Worst corners k = 30.3/9.9 = 3.06061 → −50.5 mV; k = 29.7/10.1 = 2.94059 → +49.5 mV → **±50 mV**, not ±81 mV.
Span = 5(1+k): 5 × 4.06061 = **20.303 V**; 5 × 3.94059 = **19.703 V** → **19.70–20.30 V**, not 19.70–20.51 V.
Gain tolerance = 4.0606/4 = +1.52 %, 3.9406/4 = −1.49 % → **±1.5 %**, not ±2 %.
Cents: ±1.5 % of a 1 V octave = 15.2 mV × 1.2 = **±18 cents**, not ±24.
*(The old figures were right for the four-resistor amp: I reproduce span 19.698–20.506 V and ±2.02 % of gain, and a zero point of 78.8 mV exact / 80.1 mV first-order against the stated ±81 mV.)* **The two-resistor redraw made this stage better and the table was not updated**; the conclusion "anything pitch-like belongs on channel 1" survives at 18 cents.

**22. 4.02 and ±10.05 V survive in four places.**
`[repo]` `:132` "±10.05 V uses the DAC's full 0–5 V span"; `:146` "Vout = 4.02 × (0 − 0) = 0 V"; `:152` "4.02 × (0 − 2.5) = −10.05 V"; `:157` "4.02 × Vdac ≈ +11.45 V".
`[calc]` adopted stage: gain = 1 + k = **4.000 exactly**; intercept = k·V_ref = 3 × 3.3333 = **10.000 V**; range **±10.000 V** (`:64`, `:75`, `:95` all say so). The CLR-standing-offset case is Vout = −k·V_ref = **−10.000 V**, not −10.05. The refresh-failure case is Vout = 4 × Vdac, clipping at ~11.45 V — the conclusion holds, the coefficient does not.

**23. One buffer, two currents.** `[repo]` `:16` "(**~1.3 mA** total into 4 × 10k)" vs `:168` "At **2.5 V** into 2.5 kΩ that is **1 mA**".
`[calc]` worst case is all four Vdac at 0: I = 4 × (V_ref − 0)/R1 = 4 × 3.3333/10 000 = **1.333 mA** = V_ref/2.5 kΩ. Line 16 is right; line 168 still uses the superseded 2.500 V.

---

### Power entry

**24. LED current.** `[repo]` `:145` — "`(5.21 − 2.0) / 4 mA ≈ 800 Ω → 820 Ω`, and on the 5 V rail it is ~3.8 mA."
`[calc]` sizing: (5.21 − 2.0)/0.004 = **802.5 Ω** → 820 Ω ✓. On the bus rail: (5.00 − 2.0)/820 = **3.66 mA**. 3.8 mA is (5.00 − 2.0)/800 — the ideal value, not the specified part. Minor.

Everything else on this page recomputes exactly — see Verified.

---

### Digital path and supervision

**25. Three documents, two different presence detectors.**
`[repo]` `digital-and-supervision.md:99-110` (current): unplugged = **+0.437 V** at the in-amp output, alive = **0 V**, "**Threshold at `V_REF`/2**". `bom.csv:100` agrees: "SENSE THE IN-AMP OUTPUT, THRESHOLD AT V_REF/2".
`[repo]` `0004:374-380` (current): "**Sense the `BREATH` conductor against `AGND` at the module end** … | Cable unplugged | **0 V** | Instrument alive | **+0.2 V** | … threshold — say **+100 mV**".
`[calc]` both are individually correct. Unplugged, R4/R5 hold both inputs at AGND so Vout = G·0 + V_REF = **+0.437 V**; alive and trimmed, Vout = **0 V** — a 437 mV split, inverted sense. At the conductor node the split is 0 V vs 0.2 × 1M/1.011M = **+198 mV**. But they are **different circuits with different thresholds**, and ADR 0004 is the odd one out.
`[calc]` the digital page's own supporting numbers check: comparator bias 100–250 nA × 1 MΩ = **100–250 mV** against a 198 mV signal ✓ — which is precisely why the ADR 0004 version fails.
`[calc]` tap loading for 60 dB: the unloaded legs differ by 1/1.011 − 1/1.010 = 9.793e-4 (60.2 dB). For a tap R_t on one leg to hold ≥60 dB, the parallel R_p must satisfy 0.98912 − R_p/(R_p+11 k) ≤ 1e-3 → R_p ≥ 915 kΩ → R_t ≥ **10.8 MΩ**. Stated 9.75 MΩ — minor, same conclusion.

`[calc]` `:194` in `breath-receive-stage.md` — |1M/1.011M − 1M/1.010M| = |0.9891197 − 0.9900990| = **9.793e-4** → 20·log₁₀(1/9.793e-4) = **60.18 dB** ✓ exactly as stated, and 0.1 % parts give 1.96e-5 → **94.2 dB** ✓, a ratio of 10^((94.2−60.2)/20) = **49×** ✓ "fifty times". This block is correct.

---

### Latency budget

**27. The two ADC figures cannot both stand, and one of them breaks 4 kHz.**
`[repo]` `:60` — "SAR ADC conversion | **50–200 µs**".
`[repo]` `:146-148` — "one pass costs **ADC 24 µs** + key chain 16 µs + six DAC channels at 2 MHz 96 µs = **136 µs** … At 4 kHz it is 136 µs of 250 µs — **54 %** duty".
`[calc]` 24 + 16 + 96 = 136 ✓ and 136/250 = **54.4 %** ✓ — the rule's own arithmetic is right. But substituting the table's own ADC figure: best case 50 + 16 + 96 = **162 µs** (65 % duty); worst case 200 + 16 + 96 = **312 µs against a 250 µs period — the 4 kHz loop does not close either.** The "4 kHz is the number" conclusion rests on 24 µs while the budget table books up to 200 µs for the same operation. One of them has to go, and the answer decides whether the loop rate is buildable.

**28. Key chain read.** `[repo]` `:96` "74HC165 chain read | **< 10 µs** via SPI DMA" vs `:146` "key chain **16 µs**".
`[calc]` four 74HC165s = 32 bits; at 2 MHz = **16.0 µs**. Line 146 is right; line 96 is wrong (and "< 10 µs" excludes 16 µs).

**29. DAC update.** `[repo]` `:100` "DAC update + settle | **~60 µs**" vs `:62-63` "SPI to DAC over umbilical **~96 µs** … DAC settling **~10 µs**", and `:62` explicitly says "the whole burst is the latency, not one word".
`[calc]` 6 × 32 bits / 2 MHz = **96 µs**, + 10 µs settling = **106 µs**. A single word would be 16 + 10 = 26 µs. **60 µs matches neither and has no derivation.**

**30. Digital total.** `[repo]` `:56-65` table; "**Total | ~2.9–3.1 ms**".
`[calc]` sum of minima: 2.17 + 0.282 + 0 + 0.050 + 0 + 0.096 + 0.010 + 0.082 = **2.690 ms**.
Sum of maxima: 2.17 + 0.282 + 0.250 + 0.200 + 0.020 + 0.096 + 0.010 + 0.082 = **3.110 ms** ✓.
Sum using the table's own means (125 µs sampling, 125 µs ADC): **2.910 ms**. So "2.9" is the *mean* and "3.1" is the *maximum* — the row mixes two statistics and the true minimum is **2.70 ms**.

**31. Consequence of #1.** `[repo]` `:42` "Receive filter, **531 Hz** | **300 µs** | `1/(2πf)`".
`[calc]` 1/(2π·531) = 299.7 µs ✓ *for 531 Hz*. At the correct 482 Hz: 1/(2π·482) = **330 µs**, and the analog total goes 1.17 + 1.0 + 0.010 + 0.330 + 0.332 = **2.84 ms** (stated `:44` ~2.80 ms). Also `:49-50` "a 500 Hz pole has 318 µs of group delay … The real figure is 632 µs" → recompute **662 µs**. The 5 ms target still holds.

---

### ADR 0005 — power architecture

**Conversion factor, established first.** `[repo]` `:169-172` — "convert at the **arriving** voltage, not 12.00 V … the buck is **~90 % efficient**"; `:95` gives ~11.4 V arriving.
`[calc]` umbilical mA per 5 V-rail mA = 5/(0.90 × 11.418) = **0.4873**. `:174-175` claims ADR 0014's ×0.49 survives as a coincidence of two ~6 % errors: 5/(0.85 × 12.00) = 0.4902, and 0.4902/0.4873 = 1.006 — **confirmed**, the two premise errors (efficiency 5.9 %, voltage 4.9 %) do cancel to 0.6 %.

**32. 5 V umbilical current.** `[repo]` `:96` — "| 5 V | **862 mA** | ~290 mV cable alone | ~4.7 V | 6%+ |", premises 4.1 W and 0.34 Ω round trip (`:90-91`).
`[calc]` constant power: I(5 − 0.34I) = 4.1 → 0.34I² − 5I + 4.1 = 0 → I = (5 − √(25 − 5.576))/0.68 = (5 − 4.40727)/0.68 = **0.8717 A = 872 mA**. Drop 0.34 × 0.8717 = **296 mV** ✓ (~290). Arrives 4.704 V ✓ (~4.7). Error 5.9 % ✓ (6 %+). **Only the current cell is wrong: 872 mA, not 862.** (At 862 mA the delivered power is 4.06 W, not 4.1.)

**33-34. The load table.** `[repo]` `:155-161`.
`[calc]` umbilical = 12 V-direct + 0.4873 × (5 V rail); body heat = umbilical × 11.418 V:

| Row | 5 V | 12 V | Umbilical stated | **recomputed** | Heat stated | **recomputed** |
|---|---|---|---|---|---|---|
| Quiescent | 180 | 123 | 212 | **211** ✓ | 2.4 W | **2.41** ✓ |
| Typical play | 226 | 248 | 359 | **358** ✓ | 4.1 W | **4.09** ✓ |
| Typical + WiFi | 336 | 248 | 414 | **412** (#39) | 4.7 W | **4.70** ✓ |
| **Clamp-legal worst** | 928 | 119 | **579** | **571** | 6.5 W | **6.52** (agrees with 571, not 579) |
| **Clamp fails** | **1023** | 1023 | **1132** | **1522** | **12.2 W** | **12.6–12.9** |

Rows 1–3 recompute within a milliamp. **Row 4's umbilical cell is 8 mA high and its own body-heat cell proves it** — 0.579 × 11.418 = 6.61 W would have been printed as 6.6, whereas 0.571 × 11.418 = 6.52 W prints as the stated 6.5.
**Row 5 is internally inconsistent three ways.** 1023 mA on the 5 V rail with 1023 mA of 12 V-direct gives 1023 + 498 = **1522 mA**, not 1132. Conversely, 1132 mA with 1023 mA direct implies a 5 V rail of (1132−1023)/0.4873 = **224 mA** — which is the typical-play figure, 226 mA. **The 5 V cell looks like a copy of the 12 V cell.** And 1.132 A × 11.418 V = **12.93 W** (12.63 W if the arriving voltage is recomputed at that current), against the stated 12.2 W.
This matters: `:264` sets the 1.0 A limit "below the 1.13 A a brownout-latched full-white strip set draws", and 1.13 A is row 5's umbilical cell.

**35. "A 5 % difference."** `[repo]` `:163-167` — "The same 3 W of light costs **531 mA** on the umbilical if it is spent on the strips and **579 mA** if spent on the matrix — a **5 %** difference."
`[calc]` 579/531 − 1 = **9.04 %**. 531/579 − 1 = −8.3 %. Neither is 5 %.
`[calc]` reconstructing both cases from the doc's own basis (base 5 V rail 328 mA, base 12 V direct 119 mA, `:160`, `:165-166`): light on the matrix = 119 + 0.4873 × (328 + 3 W/5 V) = 119 + 0.4873 × 928 = **571 mA**; light on the strips = (119 + 3 W/11.418 V) + 0.4873 × 328 = 381.7 + 159.8 = **541 mA** (or 529 mA if the strips are converted at 12.00 V). The real spread is **~8 %**, whichever convention. The sentence's own point — that the 5 V rail is where the danger is — is untouched, and `328 → 928 mA` is correctly "a factor of three" (2.83×).

**36. 630 mA vs 579 mA.** `[repo]` `:263` "above the clamp-legal worst case of **630 mA** plus ramp current" vs `:160` "| **Clamp-legal worst** | … | **579 mA** |". Same quantity, two values, 9 % apart, and the 0.9 A lower bound of the limit window is derived from it (0.63 + 0.26 ≈ 0.89; from 0.571 it would be 0.83).

**37. TPS2553 overvoltage.** `[repo]` `:291-293` — "a **2.5–6.5 V** USB power switch with a **7 V** absolute maximum, specified here on a **+12 V** rail — roughly **66 %** over abs-max".
`[calc]` 12/7 − 1 = **71.4 %**. (Against the 6.5 V operating max it is 84.6 %.) 66 % would correspond to 11.62 V. The conclusion is unaffected.

**38. 75 ms belongs to the rejected 500 mA limit.**
`[repo]` `:267-273` — this paragraph is about the **500 mA** proposal: "It boots — in about **75 ms** of constant-current start".
`[repo]` `:306-307` — "Programmable ramp rate and a programmable fault timer come with the part, which is what **the 75 ms start above** needs."
`[repo]` `power-entry.md:95, 98` — "1.0 A into 2.2 mF to 12 V is **26 ms** … **Timer ≈ 50 ms**, comfortably past 26 ms."
`[calc]` at the adopted 1.0 A limit, t = C·V/I = 2.2e-3 × 12/1.0 = **26.4 ms** ✓. At 500 mA, t = 52.8 ms with no load, more with one — so 75 ms is plausible *for 500 mA*. **The 50 ms timer the module actually specifies is shorter than the 75 ms ADR 0005 says the timer must exceed.** They are consistent only once it is stated that 75 ms is a figure for an option that was not adopted; as written the two documents disagree about the timer requirement.

**40. 928 mA and a 1 A part.** `[repo]` `:208` — "**928 mA** of clamp-legal worst case does not fit behind one 1 A part."
`[calc]` 928 mA is **93 %** of 1.0 A — it fits, with 7 % margin. The claim needs a stated derating (thermal, or the R-78E5.0's own derating curve **[ds]**) to be true. The two-buck decision has an independent reason (`:206-207`, ADR 0013) and is unaffected.

**41. 0.2–4.7 V.** See #52 below; ADR 0005:74 carries the same figure.

---

### ADR 0006 — CV channel allocation

**42. Resolution as a percentage.** `[repo]` `:125-126` — "Resolution goes from 153 µV/LSB on a 10 V span to **305 µV/LSB** on 20 V. That is **0.003 %** of full scale".
`[calc]` 10/65536 = **152.59 µV** ✓; 20/65536 = **305.18 µV** ✓. As a fraction of the stated 20 V span: 305.18e-6/20 = 1.526e-5 = **0.0015 %** — which is just 1/65536, as it must be for any 16-bit converter. 0.003 % is 1 LSB against 10 V, i.e. against half the span the sentence just quoted. Ambiguous at best.

**43-44. The trimmer tempco table has an unstated, contradicted premise, and a pivot error.**
`[repo]` `:375-382` (current `:378-390`) — "Against a fixed 0.1 % **10 ppm/°C** resistor: | 5 % | **22 ppm/°C** | **2.4 cents** | 10 % | 34 | 3.7 | 20 % | 58 | 6.3 |".
`[calc]` solving for the trimmer's tempco T from 0.95×10 + 0.05·T = 22 gives **T = 250 ppm/°C**; the 10 % and 20 % rows give 250 as well, so the column is self-consistent — **on a 250 ppm/°C trimmer that appears nowhere.** `0006:368` itself says "its ~100 ppm/°C then contributes ~2 ppm/°C" at 200 Ω (2 %), i.e. **100 ppm/°C**; `pitch-stage.md:249` and `bom.csv:105` also say ~100 ppm/°C. At 100 ppm/°C the column reads **14.5 / 19 / 28 ppm/°C**.
`[calc]` the cents column follows from the ppm column only by applying the drift to the full 9 V span: 22 ppm/°C × 10 °C × 9 V = 1.98 mV → 1.98 × 1.2 = **2.376 cents** ✓ 2.4. But a **ratio** drift pivots at V_ref = 2.5 V with a lever of 2.25 V, as `pitch-stage.md:266-269` now states: dVout = 2.25 × 220e-6 = 495 µV → **0.59 cents**. With the correct 14.5 ppm/°C premise: 2.25 × 145e-6 = 326 µV → **0.39 cents**.
**So ADR 0006's 2.4 cents is wrong twice over** — a 2.5× trimmer tempco and a 4× pivot error — and that is the whole of the "6× disagreement" `pitch-stage.md` used to flag. At the adopted 200 Ω the figure is **0.054 cents**.

**45. INL.** See #13.

**46. "Eighty-six decibels off the right node."**
`[repo]` `:516-527` — sensitivity of a bare ±12 V divider is "roughly **0.21 V/V**"; the WS2815 square wave gives "**~22 cents p-p**"; ADR 0004 "defended the *op-amp's supply pins* for **80 dB** of PSRR and **0.011 cents** … **Eighty-six decibels** off the right node."
`[calc]` 2.5/12 = **0.2083 V/V** ✓. Back-solving the ripple: 22 cents = 18.33 mV at the jack = 18.33/0.2083 = **88 mV** of rail ripple (never stated — see U9). Through 80 dB of PSRR: 88 mV/10⁴ = 8.8 µV → × 1.2 = **0.0106 cents** ✓ 0.011.
`[calc]` the gap between the two paths: 22/0.011 = 2000 → 20·log₁₀(2000) = **66.0 dB**. Equivalently 80 dB of PSRR against a divider sensitivity of 20·log₁₀(0.2083) = −13.6 dB → 80 − 13.6 = **66.4 dB**. **The figure should be sixty-six decibels, not eighty-six.** (86 dB would need a PSRR of 100 dB, which contradicts the 0.011 cents in the same sentence.)

**47. 5.25 V vs 5.21 V.** `[repo]` `0006:532` "off the LM317's own **5.25 V**"; `0006:678` "its own **5.25 V** regulator"; `0004:280` power-tree box "LM317LZ **5.25V**" — against `0004:157` "an LM317LZ set to **~5.21 V**", `power-entry.md:18` "DAC AVDD **5.21V**", `digital-and-supervision.md:36, 47`, `0004:188`, `bom.csv:108`.
`[calc]` from the specified divider: Vout = 1.25 × (1 + 475/150) = 1.25 × 4.16667 = **5.208 V**, plus I_ADJ × R2 = 50 µA × 475 = 24 mV → **5.232 V** **[ds]**. 5.21 V is the right nominal; 5.25 V is stale in three places, and `0004:188`'s threshold arithmetic (0.7 × 5.21 = 3.65 V ✓) uses 5.21.

**48. The mod transfer function no longer matches its own offset value.**
`[repo]` `:15, :21-22` — DAC ch7 carries "**3.3333 V**"; `:138-140` — "```Vout = 4 × (Vdac − Voffset) = 4 × (0 − 0) = 0 V```".
`[calc]` the built stage is Vout = 4·Vdac − 3·V_ref (`firmware/README.md:49`, `mod-channels.md:94-95`). At Vdac = 2.5 V, V_ref = 3.3333 V: Vout = 10 − 10 = **0 V**. But the ADR's formula gives 4 × (2.5 − 3.3333) = **−3.33 V**. The formula is only valid for the superseded four-resistor stage where Voffset was 2.5 V. The CLR conclusion (both terms zero → 0 V) survives; the equation used to justify it does not.

**49-50. Two stale rows in the update-rate table.** `[repo]` `:185` "| Breath zero offset | continuous, slow |" — that channel was deleted (`:25-31`). `[repo]` `:186` "| Mod offset | **written once at boot** | The shared **2.5 V** reference point |" — the value is 3.3333 V and `firmware/README.md:64-67` plus `mod-channels.md:158` require it refreshed **every pass**; the "written once" rule is the exact failure the statelessness section exists to close.

---

### ADR 0003 — breath sensing path

**41/52. The sensor's top of range is 4.80 V, and the ADR proves it itself.**
`[repo]` `0003:101` "~0.2–4.7 V out"; `:116` table "Output span | 0.2–4.7 V | 0.2–4.7 V"; `:518` "full scale, **0.2–4.7 V**"; `0005:74` "outputting **0.2–4.7 V**"; `bom.csv:46` "Sensor reaches 4.7V".
`[repo]` `0003:120-122` — "`Vout = VS × (0.1533·P + 0.04)` at VS = 5 V is **0.7665 V/kPa** with **0.20 V** at zero"; `:135` — range 0–6 kPa.
`[calc]` 5 × 0.1533 = 0.7665 ✓; 5 × 0.04 = 0.200 ✓. At full scale: 5 × (0.1533 × 6 + 0.04) = 5 × 0.9598 = **4.799 V**. Equivalently 0.766 V/kPa × 6 kPa + 0.20 = **4.80 V**. Span = **4.60 V**.
**`breath-receive-stage.md:159` ("0.2 → 4.8 V | 4.6 V") is the correct one**; the 4.7 V figure in five other places is wrong and is what produces #55.

**51. Seven channels became six and one table did not follow.**
`[repo]` `0003:413-416` — "| **Breath analog, 7 channels at 4 kHz** | **0.90 Mbit/s** | **2 MHz** |"; `:419` "the loop refreshes **seven**".
`[repo]` `0004:54` — "| **Breath analog, 6 channels at 4 kHz** | **0.77 Mbit/s** | ≥1.5 MHz → specify 2 MHz |"; `0004:63-65` and `latency-budget.md:153-155` both state the seventh channel was deleted.
`[calc]` 7 × 4000 × 32 = 896 kbit/s ✓ 0.90 — arithmetically right *for seven*. Six: 6 × 4000 × 32 = **768 kbit/s = 0.77 Mbit/s** ✓ ADR 0004. ADR 0003 is stale; the 2 MHz conclusion survives.

**52/53. The anti-alias cap: wrong value, wrong corner, wrong attenuation, wrong switching frequency.**
`[repo]` `0003:533` — "put a **220 nF** cap at the ADC input pin"; `:543-544` — "220 nF gives a **~600 Hz** corner and **58 dB at 500 kHz**"; `:539` — "A buck running at **500 kHz**".
`[repo]` `bom.csv:45` — "C-AA-ADC, **47nF** C0G/NP0 … **564Hz** with the divider's 6k Thevenin (10k||15k) … **WAS 220nF, which is 121Hz** … the R-78E5.0 switches at **330kHz** not 496kHz. **55dB at 330kHz**."
`[repo]` `bom.csv:46` — divider is 10 k / 15 k → Thevenin 10k‖15k = **6.0 kΩ**, ratio 15/25 = **0.6** ✓.
`[calc]` 220 nF against 6 kΩ: f = 1/(2π · 6000 · 220e-9) = **120.6 Hz** — a fifth of the claimed 600 Hz, and 1.32 ms of group delay against the 282 µs the latency budget books. For ~600 Hz you need 47 nF: 1/(2π · 6000 · 47e-9) = **564.4 Hz** ✓, which is the value the BOM now carries and `latency-budget.md:58` already uses.
`[calc]` attenuation of a 564 Hz pole at 500 kHz = 20·log₁₀(500 000/564) = **58.95 dB** ✓ the stated 58 dB — so **the 58 dB figure was computed for the 600 Hz corner, not for the 220 nF part**. At the real 330 kHz **[ds]**: 20·log₁₀(330 000/564) = **55.3 dB** ✓ BOM.
`[calc]` the aliasing example is internally correct: 500 kHz/4 kHz = 125 exactly → folds to DC ✓; 498 − 4×124 = **2 kHz** ✓; 496.1 − 496 = **100 Hz** ✓. But the premise frequency is contradicted by the BOM (330 kHz). **ADR 0003 is three revisions behind the BOM on this component.**

**54. "Roughly 30 dB worse."**
`[repo]` `0003:443-451` — table "| 0.4 % | **21 mV** | 1 % | 52 mV | 2 % | 104 mV |"; "the AGND common-mode path … contributes **0.13 mV**. The ratiometric path is roughly **30 dB worse**".
`[calc]` the 0.13 mV figure reproduces exactly: the shared-ground common mode is 58.9 mV (`:329`), rejected by the 60 dB CMRR budget → 58.9 µV, × the in-amp gain 2.1611 = **127 µV = 0.13 mV** ✓.
`[calc]` the ratio: 21/0.13 = 162 = **44.2 dB**; 52/0.13 = 400 = **52.0 dB**; 104/0.13 = 800 = **58.1 dB**. **None is 30 dB** (30 dB would be 4.1 mV). The point — the ratiometric path dominates — is understated, not overstated.

**55. "~2.13× scaling stage."** `[repo]` `0003:364-365`.
`[calc]` 2.13 = 10 V / 4.7 V, i.e. the old top-of-range treated as if it were the span. The correct raw gain is 10 / 4.60 = **2.174** (`breath:161`), the built gain is **2.185**, the effective gain **2.161**. Downstream of #52.

**56. "Six orders of margin."** `[repo]` `0003:401-403` — "~200 pF of cable and a 100 Ω source the corner sits at **8 MHz** against a 160 Hz signal — **six orders** of margin".
`[calc]` 1/(2π · 100 · 200e-12) = **7.96 MHz** ✓. 7.96e6/160 = **4.97 × 10⁴** — **4.7 orders**, not six. Six orders would be 160 MHz.

**57. Bore and resonance.** `[repo]` `0003:717` — "the bore moves the tube's first resonance by **20–40 Hz** and never changes the verdict".
`[repo]` `0003:265-266` — the model is a distributed pipe, f = c/4L = 214 Hz or c/2L = 429 Hz; `:272` — "It is **independent of trap volume**."
`[calc]` in a distributed-pipe model the only bore dependence is the open-end correction, ≈ 0.6r. At a 3 mm bore that is 0.9 mm on 400 mm = 0.22 % → **0.5 Hz** at 214 Hz. Even a 10 mm bore gives 0.6 × 5 = 3 mm = 0.75 % → **1.6 Hz**. To move 214 Hz by 20–40 Hz needs a 9–19 % length change, i.e. 37–75 mm of end correction — a bore of 60–125 mm. **The 20–40 Hz figure has no derivation and is two orders too large**; the conclusion ("a mouth-fit decision, not an acoustic one") is *strengthened* by the correct number.

**58-59. ADR 0003's own latency table and summary are stale.**
`[repo]` `0003:19-27` — "| SPI to DAC over the umbilical | **~50 µs** | … | **Total** | **< 1.5 ms** |"; `:254` — "Breath path goes from ~1.5 ms to **~2.6 ms**".
`[calc]` the table sums correctly on its own terms (1000 + 50…200 + 20 + 50 + 10 + 160 = 1290–1440 µs ✓ < 1.5 ms), and `:254` follows from it (1.5 − 0.09 + 1.17 = 2.58 ✓ ~2.6). But it omits the tube, both 500 Hz poles, the anti-alias pole, the restrictor and the sampling period, and books the umbilical burst at 50 µs where the current figure is **96 µs** (`0004:62`). `latency-budget.md` supersedes it at **2.84 ms** analog / **2.70–3.11 ms** digital. Both figures should be deleted rather than left to be quoted.

---

### ADR 0004 — CV interface module

**60. The MOSI series corner.** `[repo]` `0004:69-72` — "`R-MOSI-SER` at **220 Ω** with ~200 pF of cable is a **~7.9 MHz** corner, so 2 MHz has margin; if E11 wants more, that resistor comes down toward **100 Ω**".
`[calc]` 1/(2π · 220 · 200e-12) = 1/(2.765e-7) = **3.62 MHz**. 7.96 MHz is the figure for **100 Ω** — the value the sentence names as the *improvement*. So the stated corner already assumes the change it offers as a contingency.
This matters: at 3.6 MHz against a 2 MHz clock the margin is 1.8×, not 4×, and SCLK's edges — not MOSI's fundamental — are what E11 is meant to check.

**61. SPI clock, two values, ten lines apart.** `[repo]` `0004:37` "SCLK, MOSI, CS | SPI to the DAC, **~2 MHz**" and `:54` "specify **2 MHz**" vs `:82` "SCLK / DIG_GND | SPI to the DAC, **~1 MHz**".

**63. OPA2197 swing.** `[repo]` `0004:198-199` — "rated to ±18 V, so on ±12 V it reaches roughly **11.9 V**". `[calc]` the op-amp sits on the *post-diode* rail: 12 − 0.35 to 0.40 V = 11.6–11.65 V (`0006:120`, `0005:95`), less its own ~0.2 V headroom → **~11.45 V**, which is what `0006:120`, `pitch:140` and `mod:101` all use for margin arithmetic. `0004:199` and `bom.csv:13` both still say 11.9 V.

**64. 320 mA or 290 mA.** `[repo]` `0004:244-257` — the table says "+12 V | **~320 mA**"; two lines later "harmless at 50 mA and is not at **290 mA**", and the drop table is headed "Drop at **290 mA**". `[calc]` the drops themselves are right: 2.2 Ω × 0.29 = **0.638 V** ✓ 0.64; 10 Ω × 0.29 = **2.90 V** ✓. Only the current is given twice. (Both are superseded by ADR 0005's 359 mA, which the same rows flag.)

**65. "Halves."** `[repo]` `0004:175-176` — "**Shrink R2** — 150 Ω / 475 Ω instead of 240 Ω / 768 Ω — which **halves** the I_ADJ contribution to **24–48 mV**."
`[calc]` **[ds]** I_ADJ 50–100 µA: 768 Ω → 38.4–76.8 mV; 475 Ω → **23.75–47.5 mV** ✓ the stated 24–48. But 475/768 = 0.618 — a **38 % reduction**, not a halving.

---

### ADR 0014 — lighting

**66. One buck or two.** `[repo]` `0014:326-328` — "It is also **more than the instrument's 5 V regulator can supply.** The matrix shares **the 1 A R-78E5.0 with both dev boards**, which take roughly 330–400 mA between them, so a full-field matrix would ask for about **1.36 A** from a 1 A part."
`[repo]` `0005:189-193, 206-211` — **two** bucks: buck A carries the real-time board, the matrix and the level shifter; buck B carries the display board alone.
`[calc]` 960 + 400 = **1.36 A** ✓ arithmetically, but only under the single-buck premise ADR 0005 replaced. Under the split, buck A carries the matrix plus the real-time board alone.

**67. The matrix's contribution to interior rise.** `[repo]` `0014:142-146` — "| Both strips full white at 60/m | **12.1 W** | ~36 K | | Matrix full white as well | **~17.7 W** | ~53 K |"; `:153` — matrix "asks for **960 mA** on its own" (at 5 V).
`[calc]` strips: 50.4 LEDs × 20 mA × 12 V = **12.10 W** ✓ **[ds]**. Matrix at the wall: 960 mA × 5 V = **4.80 W** ✓ `:323`. Grossed up for the buck: at ADR 0005's corrected **90 %** that is **5.33 W** → total **17.43 W**; at the retracted **85 %** it is 5.65 W → **17.75 W** ✓ the stated 17.7. **The figure uses the efficiency ADR 0005:171-172 explicitly withdrew.** Rise: 17.4 × 3 K/W = 52 K rather than 53 K — the conclusion is untouched.

**68. "60 % of one channel."** `[repo]` `0014:171-173` — "on the matrix it is a sparse display at full brightness or a **full field at around 60 % of one channel**."
`[calc]` matrix full white field = **4.80 W**; 3 W/4.80 W = **62.5 %** of a full *white* field. One channel at full field = 64 × 5 mA × 5 V = **1.60 W**, so 60 % of one channel is **0.96 W** — under a third of the budget. The percentage is right and the noun is wrong.

---

## Figures with no derivation

These are not contradictions; they are numbers with no stated premises, which the brief asks to be named as findings.

| Ref | Figure | Note |
|---|---|---|
| U1 | `0004:165` — worst-case LM317 spread "about **0.66 V** against a window of roughly **0.55 V**" | No tolerances stated. With the adopted 0.1 % divider and a ±4 % reference I get 5.016–5.472 V = **0.46 V**; 0.62 V is reproducible only with the *old* 1 % 240/768 divider. The window's 0.55 V has no source at all |
| U2 | `0004:518` — "**5.7–7.2 cents**"; `:536` — "**~4.8 cents**" | No shared-copper length or resistance. Back-solving: 5.7–7.2 cents = 4.75–6.0 mV of IR drop at 360 mA = **13–17 mΩ**, plausible for ~1 cm of trace, but unstated. Both feed `0006:545-546` |
| U3 | `0004:545` — "**107 mm** of ~110 mm"; `:597` — 6HP "overran by **0.5 mm**"; `:603` — "**7.17 mm** of visible panel each side of the flange" | No itemised height budget anywhere. 7.17 mm implies a **26.0 mm** flange (40.34 − 2×7.17), which is never stated **[ds]**. The 8HP/6HP bore arithmetic itself is exact — see Verified |
| U4 | `0005:270-271` — "the buck starts at **~17 ms**", "boots in about **75 ms**" | No premises. 500 mA into 2.2 mF to 12 V is 52.8 ms unloaded; 17 ms at 500 mA reaches 3.9 V, which is below any stated buck start voltage |
| U5 | `0005:288` — "**50 mW** less inside the sealed body" | Implies a polyfuse resistance of 0.05/0.359² = **0.39 Ω**, never stated |
| U6 | `0014:239` — "Loop gain is around **0.004**" | No derivation, and the mechanism stated ("`AGND` rises") is the one ADR 0003's separate sense return exists to prevent — `0014:391-393` says so on the same page |
| U7 | `breath:256` — "the downstream stage needs about **0.6× to 2.5×**" | The 2.5× checks: at 2.5 kPa the in-amp gives (4.6 × 2.5/6) × 2.1611 = 4.14 V, and 10/4.14 = **2.42** ✓. The 0.6× has no stated basis |
| U8 | `0003:445-447` — ratiometric error 21 / 52 / 104 mV | Mutually consistent on a **5.2 V** base (0.004 × 5200 = 20.8; 0.01 × 5200 = 52; 0.02 × 5200 = 104) that is never stated. At the jack's 10 V full scale the same excursions give **40 / 100 / 200 mV** — the table is a half-scale figure presented as the error |
| U9 | `0006:523` — "**~22 cents p-p**" of WS2815 FM | Requires **88 mV** of rail ripple; that number appears nowhere. The 80 mV shared-diode figure (`0006:544`, `power-entry:52`) *is* derived and checks out |
| U10 | `pitch:207-208` — "**18°** of phase margin with 2 m of cable and under **10°** with four destinations" | Loop analysis not shown; not reproducible by hand |
| U11 | `breath:206-208` — "At ±5 % the common-mode capacitor mismatch alone gives **~46 dB**; ±1 % is needed to clear 60" | Reproduces exactly at **500 Hz** (ωRΔC = 2π·500·11k·0.15 nF = 5.18e-3 → 45.7 dB; ±1 % → 59.7 dB) but the frequency is unstated, and the neighbouring 15 dB figure uses 100 Hz |
| U12 | `0003:311-314` — "| 100 kΩ | **50 µA** | 8.4 µV |" | 50 µA implies a **5 V** signal; the same section says "a 153 µV LSB on a **10 V** output", which would be 100 µA and 16.8 µV. Internally consistent at 0.168 Ω either way |
| U13 | `0003:530` — "puts **~2.5 mA** into that diode" | Divider impedance not given (implies ~1.6 kΩ) |
| U14 | `breath:261-264` — "on the order of **20 mV** … over a full warm-up" | No ΔT stated (ADR 0003 gives 20 K; that yields 21.6 mV) |

---

## Verified correct

Recomputed and in agreement. Listed because a clean result is evidence too, and because several of these are the numbers most likely to be "corrected" by mistake.

**Breath page** — G = 1 + 50 000/42 200 = **2.1848** ✓ **[ds]**; the whole gain derivation table (4.6 V span, 10/4.6 = 2.174, 1M/(1M+11k) = 0.98912, 2.174/0.98912 = 2.198, 2.1848 × 0.98912 = 2.1611, × 4.6 = **9.94 V**, shortfall 0.59 % ✓ "0.6 %"); REF = 2.1848 × 0.200 = **0.437 V** ✓; the new spec-band range (0.152 × 2.185 = **0.332 V**, 0.378 × 2.185 = **0.826 V**, 0.6/2.185 = **0.275 V**, residual 0.226 V × the 0.6–2.5× downstream gain / 10 V = **1.4–5.6 %** ✓, 1.0/2.185 = **0.458 V** ✓); R1 fault power (12 − 0.2)/1 kΩ = **11.8 mA**, I²R = **139 mW** ✓ against an 0805's 125 mW; the CMRR imbalance block **9.793e-4 → 60.2 dB**, 0.1 % → **94.2 dB**, ratio **49×** ✓; output RC 1/(2π·1000·330e-9) = **482 Hz** ✓ "~480"; C_diff/C_cm = **10** ✓; the knob-interaction example (0.2 × 2.1611 = 0.432 V; 2.4 × 0.432 − 0.432 = **+0.605 V** ✓ "+0.6 V"); hard blow (4.6 × 2.8/6) × 2.1611 = **4.64 V** ✓ "roughly 4.5 V"; the 100 kΩ pulldown's **17.4 %** ✓.

**Pitch page** — window table (4.5 V, 9 V, **2.000**, −2 − 2(0.25) = **−2.500**) ✓; Vout = Vdac(1+k) − k·V_ref with k = 1 ✓; headroom 2×0 − 2.5 = **−2.5**, 2×5 − 2.5 = **+7.5**, 0.5 V = **600 cents** ✓; the error-type table (1 mV = **1.2 cents** at both ends ✓; 100 ppm × 2 V = 0.2 mV = **0.24 cents**, × 7 V = 0.7 mV = **0.84 cents** ✓); load divider 100/101 = **0.9901** → −9.901 mV/V → **−11.88 cents/oct** ✓, 50/51 = **0.9804** → **−23.53** ✓; R-OFFINJ gain error 1 + 1 + 10/470 = **2.02128** ✓ "2.0213"; the shelf identity (2 + sRC)/(1 + sRC), max attenuation 20·log₁₀2 = **6.02 dB** ✓; the deleted 10 nF at 100 kHz = **−16.07 dB** ✓ and at 1 MHz = **−35.96 dB** ✓; C-AA-PITCH 1/(2π·1000·10e-9) = **15.92 kHz** ✓; the ringing block — Q = √(1000×82e-9/(10 000×2.2e-9)) = 1.931 → ζ = 0.259 → overshoot **43.1 %** ✓ "44 %"; at 330 nF Q = 3.873 → ζ = 0.129 → **66.4 %** ✓ "67 %"; at 10 nF Q = 0.674 → **3 %** ✓ "safe"; two 10 ppm discretes 10√2 = **14.14 ppm/°C** → **0.382 cents** ✓ "0.38"; DAC reference **0.42 cents** ✓; LT5400 **0.027 cents** ✓; 0.068 − 0.027 = **0.041** ✓ "0.04".

**Mod channels** — k = 30/10 = **3**, gain **4.000**, intercept 3 × 3.3333 = **10.000 V**, range **±10.000 V** ✓; V_ref/(4×10 kΩ) = 3.3333/2500 = **1.333 mA** ✓ "~1.3 mA"; C-FILT-MOD 1/(2π·1000·82e-9) = **1941 Hz** ✓ "1.94 kHz"; 1 kΩ unbalancing the four-resistor version — V+ = Vdac × 40.2/51.2 = 0.78516, × 5.02 = 3.9415, at 2.5 V → **−196.3 mV** ✓, at 5 V → **+9.657 V** ✓, 196/81 = **2.4×** ✓ "more than twice"; 39 k → gain **3.90**, **±9.75 V** ✓; 11.45 − 10.05 = **1.40 V** ✓; the inverting alternative −4·Vdac + 5×2.0 → **+10 … −10 V** ✓ and its CLR case **+10 V** ✓; `R-OPAMP-IN` qty **7** ✓ (1 + 4 + 1 + 1); 8 vs 16 resistors ✓; **and, for the record, the superseded four-resistor tolerance figures were right**: span 19.698–20.506 V ✓ "19.70–20.51", ±2.02 % ✓, ±24 cents ✓, zero point 78.8 mV exact / 80.1 mV first-order against the stated ±81 mV.

**Power entry** — LM317 1.25 × (1 + 475/150) = **5.208 V** ✓ "5.21"; 80 mV × (2.5/12) × 1.2 cents/mV = **20.0 cents** ✓; R_SENSE 50 mV/1.0 A = **50 mΩ** ✓; 0.36 × 0.05 = **18 mV**, 0.36² × 0.05 = **6.48 mW** ✓; bulk 2×100 + 2×1000 = **2.2 mF** ✓; **the entire ramp table** — 12/0.05 = **240 V/s**, 12/0.1 = **120 V/s**; 2.2e-3 × 240 = **0.528 A**, × 120 = **0.264 A**; 12 × 0.528 = **6.34 W**, 12 × 0.264 = **3.17 W**; ∫ = I·V·T/2 = **0.158 J** both ways = ½CV² = 0.5 × 2.2e-3 × 144 = **0.158 J** ✓ (and the "same either way" claim is exactly right); 2.2e-3 × 12/1.0 = **26.4 ms** ✓; 12 W × 50 ms = **0.6 J** ✓; 802.5 Ω → 820 Ω ✓; 47/22 to 47/10 = **2.1–4.7×** ✓ "2–5×".

**Digital and supervision** — 0.45 × 1e6 × 220e-9 = **99.0 ms** ✓; 99 ms/250 µs = **396** ✓ "~400"; 1/4000 = **250 µs** ✓; 0.7 × 5.21 = **3.647 V** ✓; unplugged output = V_REF = **+0.437 V** ✓; alive = **0 V** ✓; split **437 mV** ✓; conductor-node alive level 0.2 × 1M/1.011M = **198 mV** ✓; comparator bias 100–250 nA × 1 MΩ = **100–250 mV** ✓; the old fixed divider 5.21 × 10/110 = **0.474 V** ✓ (`bom.csv:100`).

**Latency budget** — tube 0.4/343 = **1.166 ms** ✓; 1/(2π·480) = **332 µs** ✓; 1/(2π·564) = **282 µs** ✓ (and 47 nF × 6 kΩ = **564 Hz** ✓); 1/4000 = **0–250 µs**, mean **125 µs** ✓; 6 × 32/2 MHz = **96 µs** ✓; 1/(2π·1940) = **82 µs** ✓; 1/(2π·15915) = **10 µs** ✓; sensor-output sub-total 1.17 + 1.0 = **2.17 ms** ✓; 24 + 16 + 96 = **136**, /250 = **54.4 %** ✓; 10/65536 = **152.6 µV** ✓ "~150"; 10 ms/250 µs = **40** ✓; 5/3.11 = **1.61×** ✓ "about 1.6×"; 192 bits at 0.6 MHz = **320 µs** > 250 µs ✓.

**ADR 0005** — 24 AWG round trip 4 m × 0.0842 = **0.337 Ω** ✓ "~0.34"; 12 V row: 0.359 × 0.34 = **122 mV** ✓, 122+400+60 = 582 mV → **11.418 V** ✓ "~11.4", 582/12 = **4.85 %** ✓ "5 %"; 5 V row's drop, arrival and error ✓ (only the current is wrong); the old 3 W case → 0.627 A, 0.213 V, **4.787 V** ✓ "4.80 V"; rack +5 V at −5 % = **4.75 V** ✓; 2000 mAh/400 mA = **5 h** ✓; WS2812 3 × 20 mA = **60 mA** ✓ **[ds]**; ⅔ × 1.5 A = **1.0 A** ✓; conversion factor **0.4873** and the ×0.49 coincidence ✓; 928/328 = **2.83×** ✓ "a factor of three"; load-table rows 1–3 ✓.

**ADR 0006** — 153 and **305 µV/LSB** ✓; ±11.65 and ±11.45 → **1.45 V** ✓; ZOH image at 2 kHz update: sinc(1600/2000) = 0.2339 → **−12.62 dB** ✓ "12.6"; at 4 kHz: sinc(3600/4000) = 0.1093 → **−19.23 dB** ✓ "19.2"; one semitone = 1/12 V = **83.33 mV** ✓; the full tempco table (5 ppm/°C × 10 × 9 V = **0.45 mV** = **0.54 cents**; 2 × 25 ppm/°C × 10 × 9 = **4.50 mV** = **5.40 cents**; 1 ppm/°C × 10 × 9 = **0.09 mV** = **0.11 cents**; ratio **10.0:1** ✓); the cents column of the trim table follows its own ppm column exactly (2.376 / 3.672 / 6.264 ✓); VCO 0.35 cents/K × 10 = **3.5 cents** ✓; 200 Ω = **2 %** of 10 kΩ, × 100 ppm/°C = **2 ppm/°C** ✓; load table 0.9901 / 0.9804, −11.88 / −23.53 cents, × 5 = **59.4 / 117.6** ✓; the affine argument — (1 − 0.980392/0.990099) × 2.5 V = 24.51 mV = **29.4 cents** ✓, into 33 kΩ = 49.27 mV = **59.1 cents** ✓; 0.980392/0.990099 = **−0.98 %** → 11.76 cents/oct × 5 = **58.8 cents** ✓; divider sensitivity 2.5/12 = **0.2083 V/V** ✓; 12 mV → **3.0 cents** ✓, 50 mV → **12.5 cents** ✓; 80 dB PSRR → **0.0106 cents** ✓; BAT54S 2 µA × 1 kΩ = 2 mV = **2.4 cents** ✓; 9/5 = **1.8** ✓; 0.25 V = **600 cents** ✓ both ends; corner table 15.9 kHz / 1.94 kHz / 482 Hz ✓.

**ADR 0003** — transfer function → 0.7665 V/kPa and 0.200 V ✓; sealed cavity 15/293 = **5.12 %** × 101.3 = **5.19 kPa** = **86.4 %** of 6 kPa ✓; tube 0.03/343 = **87 µs** ✓ "0.09 ms", c/4L = **2858 Hz** ✓ "~2.9 kHz", 0.4/343 = **1.166 ms** ✓, c/4L = **214.4 Hz** and c/2L = **428.8 Hz** ✓ "214–429"; π(1.5e-3)²(0.4) = **2.827 mL** ✓; shared-ground table at 0.1684 Ω — **16.8 / 33.7 / 58.9 mV** ✓; patch-cable table at 0.168 Ω ✓ internally; 74 dB at 10 Ω scaled to 1 kΩ = **34 dB** ✓ and to 3.3 kΩ = **23.6 dB** ✓ "~24"; sensor bandwidth 1/(2π×1 ms) = **159 Hz** ✓; 96 kHz × 32 + 5 × 2 kHz × 32 = **3.392 Mbit/s** ✓ and ×2 = **6.8 MHz** ✓; REF5050 5 ppm/V × 1 V × 5 V = **25 µV** ✓ **[ds]**; fault current (12 − 5.6)/1 kΩ = **6.4 mA**, (12 − 5.7)/2 mA = **3.15 kΩ → 3.3 kΩ** ✓; alias folding 500/498/496.1 kHz ✓; 6/(101.3+6) = **5.6 %** ✓ "about 6 %"; 0.23 % ✓ internally.

**ADR 0004** — SPI table: 0.32 and **0.77 Mbit/s**, 0.64 and **1.54 MHz** ✓; 192 bits/0.6 MHz = **320 µs** ✓; 96/250 = **38.4 %** ✓; DAC VDD table 9/2.5 = **3.6×** and 9/5 = **1.8×** ✓; 0.7 × 5.21 = **3.65 V** ✓ with **0.95 V** of margin from 4.6 V ✓; I_ADJ 24–48 mV ✓; series-R drops 0.64 / 2.90 V ✓; 12 − 0.4 − 0.12 = **11.48 V** ✓ "~11.5"; 320 mA at ~15 % of a 2.1 A rail ✓; 400/500 mA = **80 %** ✓; **the entire panel block** — (8 × 5.08) − 0.3 = **40.34 mm** ✓, (40.34 − 23.8)/2 = **8.27 mm** ✓, 6HP = (6 × 5.08) − 0.3 = **30.18 mm** ✓, (30.18 − 23.8)/2 = **3.19 mm** ✓, M12 (40.34 − 16)/2 = **12.2** and (30.18 − 16)/2 = **7.1** ✓, Hirose (40.34 − 10.2)/2 = **15.1** and (30.18 − 10.2)/2 = **10.0** ✓.

**ADR 0014** — 2 × 0.42 = **0.84 m** ✓; 30/m → **25.2** LEDs, 60/m → **50.4** ✓; at 20 mA/LED **[ds]**: **0.504 / 1.008 A** ✓, single hue ÷3 = **0.168 / 0.336** ✓, at 40 % = **0.067 / 0.134** ✓; 1.008 × 12 = **12.10 W** ✓; 10–20 K / 5 W = **2–4 K/W** ✓ "~3"; 12.1 × 3 = **36.3 K** ✓, 17.7 × 3 = **53.1 K** ✓; 3 W × 3 = **9 K** ✓, 3/1.5 = **2×** ✓, 17.7/3 = **5.9** ✓ "a sixth"; 3/12.1 = **24.8 %** ✓ "a quarter", 3/4.03 = **74.4 %** ✓ "~75 %"; 64 × 15 mA = **960 mA** ✓, × 5 V = **4.8 W** ✓; the whole ×0.49 matrix table — 40/64 → **19.6/31.4**, 5 → **2.45**, 10 → **4.9**, 160 → **78.4**, 960 → **470.4** ✓; 960 + 400 = **1.36 A** ✓ (under its own premise).

**BOM spot checks** — `C-DECOUPLE` 12 + 2 + 2 + 2 + 4 = **22** ✓; `C-AA-ADC` 564 Hz and 55 dB at 330 kHz ✓; `TRIM-BREATH-ZERO` 1.0/2.185 = **0.458 V** ✓; `R-PRESENCE` 0.474 V and 0.198 V ✓; `U-OPA-PITCH` ten halves of twelve, two spare ✓ (against the breath page — see #8).

---

## Count

**Approximately 360 distinct numeric claims were recomputed** from the premises their documents state:

| Source | Figures checked | Discrepancies |
|---|---|---|
| `breath-receive-stage.md` | 34 | 9 |
| `pitch-stage.md` | 38 | 11 |
| `mod-channels.md` | 27 | 3 (spanning 8 cells) |
| `power-entry.md` | 19 | 1 |
| `digital-and-supervision.md` | 13 | 2 |
| `latency-budget.md` | 27 | 5 |
| `0003-breath-sensing-path.md` | 57 | 9 |
| `0004-cv-interface-module.md` | 38 | 6 (+4 unsourced) |
| `0005-power-architecture.md` | 46 | 10 (+2 unsourced) |
| `0006-cv-channel-allocation.md` | 48 | 9 (+1 unsourced) |
| `0014-lighting.md` | 34 | 3 (+1 unsourced) |
| `bom.csv`, `firmware/README.md` (cross-check only) | ~12 | contributory |
| **Total** | **~360** | **68 discrepancies + 14 unsourced** |

Of the 68: **11 are numbers that are simply wrong** (#1, 2, 3, 4, 5, 24, 32, 37, 42, 45, 46, and the whole of #21, #43-44, #52, #54, #56, #57, #60); **24 are the same quantity given two or three different values**; **21 are figures that were correct when written and became wrong when a premise moved underneath them** — the single largest class, and the same class as the five errors this project has already found and fixed.

The three most load-bearing:

1. **#27** — the 4 kHz loop rate. `latency-budget.md` books the same ADC read at 24 µs in the rule that proves 4 kHz closes and at 50–200 µs in the table. At 200 µs it does not close. Everything downstream of the loop rate rests on this.
2. **#52** — ADR 0003 still specifies a 220 nF anti-alias cap and calls it 600 Hz. It is 121 Hz, the BOM has already moved to 47 nF, and the ADR is the document a builder would read.
3. **#34** — ADR 0005's clamp-fail row. Its 5 V cell, its umbilical cell and its body-heat cell are mutually inconsistent, and the 1.13 A that sets the load switch's upper bound comes from it.
