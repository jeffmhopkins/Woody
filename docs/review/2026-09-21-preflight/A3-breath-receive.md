# A3 — Breath receive stage: the CMRR chain, rebuilt from documents

**Cold reviewer.** No prior review directory was read. Sources are the design
corpus, `config/figures.yaml`, `hardware/bom.csv`, and the banked datasheets.

**Documents used, and how they are cited below**

| Tag | Document |
|---|---|
| `[SBOS792A p.N]` | INA828, SBOS792A Aug 2017 rev Jan 2018, `datasheets/texas-instruments/INA828IDR.pdf` |
| `[SBOS737C p.N]` | OPA197/OPA2197/OPA4197, SBOS737C Jan 2016 rev Mar 2018, `datasheets/texas-instruments/OPA2197.pdf` |
| `[MPXV4006 r3 p.N]` | MPXV4006 series, **Rev 3, 1/2009**, Freescale, `datasheets/other-semi/MPXV4006DP.pdf` |
| `[NE8FDP-DS]` | Neutrik NE8FDP data sheet, `datasheets/connectors/NE8FDP-DATASHEET.pdf` |
| `[repo file:line]` | this repository |
| `[calc]` | arithmetic shown inline |
| `[from memory]` | not in any banked document — flagged for fetching or measurement |

**Headline.** The 1.7 dB of margin does not survive contact with the datasheets,
in both directions. It is not 1.7 dB — rebuilt from documents the budget is
**−4.6 dB worst case / +0.0 dB RSS** against the corpus's own 60 dB, because
every capacitive term was omitted from the old calculation. But the 60 dB
requirement itself is **derived nowhere in the corpus**, and against an
audibility-based requirement the same circuit has ~30 dB of margin. Both halves
matter: the arithmetic is worse than claimed, and the thing it is measured
against was never established.

---

## 1. The CMRR budget, rebuilt

### 1.1 What the corpus claims, and where each claim lives

| Claim | Where | Status after this review |
|---|---|---|
| link CMRR requirement = **60 dB** | `[repo docs/decisions/0003-breath-sensing-path.md:354,510]`, `[repo hardware/module/breath-receive-stage.md:143,217]` | **Asserted, never derived.** No document in the corpus contains a derivation. |
| requirement = **58.5 dB**, "independently derived" | `[repo hardware/controller/carrier.md:219-220]` | **Not reproducible.** No derivation exists in the corpus either. |
| CMRR **70.2 dB with `R1b`, 60.2 dB without**; margin **1.7 dB** | `[repo hardware/controller/carrier.md:219-221]` | **Refuted as a total.** It is a single-term (DC resistive) calculation presented as a budget. |
| with `R1b` the floor is **73 dB**, set by the 1 MΩ pair; `R1b` buys **13 dB** | `[repo hardware/controller/carrier.md:224-226]` | **73 dB confirmed as the DC term** `[calc]`; **superseded as a floor** — above ~100 Hz the cap terms are 13 dB worse. The "13 dB" figure for `R1b` is **right, by a different mechanism** than the one given. |
| `|1M/1.011M − 1M/1.010M| = 9.79e-4 → 60.2 dB` | `[repo hardware/module/breath-receive-stage.md:213-215]` | **Arithmetic verified** `[calc]`: 9.79326e-4, 60.09 dB referred to the 0.98912 differential gain. |
| `C_cm` at ±5 % gives ~46 dB, ±1 % "is needed to clear 60" | `[repo hardware/module/breath-receive-stage.md:226-228]` | **46.3 dB reproduced** `[calc]`. **"Clear 60" is false** — ±1 % lands *on* 60.3 dB, and that is the whole budget. |

### 1.2 The model

Both legs are driven from a low impedance referenced to the *instrument's*
analog star; the star floats above module analog ground by the `PWR_GND` IR
drop. Each leg is a series `R` into a node shunted by `C_cm` and `R_bias`, with
`C_diff` across the pair.

```
  V_cm + V_sig ──[R_a = R1 + R2]──┬── IN−      R = 1k + 10k = 11 kΩ
                                  ├─[C_cm + δC/2]── AGND_MOD
                                  ├─[R_bias]─────── AGND_MOD
                                  │
                              [C_diff]
                                  │
  V_cm         ──[R_b = R1b + R3]─┴── IN+
```

Two facts the old calculation missed, and they are what change the answer:

1. **Series-resistance mismatch works against `C_cm`, not only against the
   1 MΩ pair.** This is precisely what `[SBOS792A p.9 Figure 18]` —
   *"CMRR vs Frequency (RTI, 1-kΩ Source Imbalance)"* — is a picture of: with
   1 kΩ of imbalance every gain converges to ~75 dB at 1 kHz and ~60 dB at
   10 kHz, where Figure 17 (balanced) holds 100 dB to ~300 Hz at G = 1.
2. **Above the differential pole both conversion terms go flat, not away.**
   `C_diff` shunts the converted error *and* the wanted signal equally, so the
   ratio asymptotes. The closed form `[calc]`:

```
   A(cm→diff)  =  [ ΔR/R  +  ΔC/C_cm ]  ×  C_cm / (2·C_diff + C_cm)

   the second factor is 1/(2·ratio + 1), ratio = C_diff/C_cm = 10  →  0.04762
```

That factor is the entire design lever. It does **not** depend on `R`, so
raising `R2`/`R3` cannot help; only the capacitor *ratio* and the capacitor
*tolerance* can.

### 1.3 The budget, as drawn

`C_cm` = 1.5 nF ±1 % (the page's own specification), `C_diff` = 15 nF,
`R4`/`R5` = 1 MΩ **1 %** `[repo hardware/bom.csv:60]`, `R1`/`R1b` 1 kΩ 1 %,
`R2`/`R3` 10 kΩ 0.1 % → worst-case ΔR = 2·(1 %·1k) + 2·(0.1 %·10k) = 40 Ω.
Evaluated at and above ~200 Hz, referred to the network's 0.98912 differential
gain. All `[calc]`.

| Term | Conversion | CMRR | Share |
|---|---|---|---|
| **`C_cm` tolerance, ±1 %** | 9.63e-4 | **60.3 dB** | **56.5 %** |
| 1 MΩ bias pair mismatch, ±1 % | 2.18e-4 | 73.2 dB | 12.8 % |
| cable pair-to-ground C unbalance, 6.6 pF | 2.12e-4 | 73.5 dB | 12.4 % |
| series-R mismatch × `C_cm`, 40 Ω | 1.75e-4 | 75.1 dB | 10.3 % |
| in-amp `z_ic` + PCB stray mismatch, 2 pF | 6.42e-5 | 83.9 dB | 3.8 % |
| series-R mismatch, DC term vs 1 MΩ | 3.96e-5 | 88.1 dB | 2.3 % |
| INA828 intrinsic, `G = 1` MIN spec | 3.16e-5 | 90.0 dB | 1.9 % |
| REF-pin source impedance (buffered) | 2.34e-7 | 132.6 dB | 0.0 % |
| **TOTAL, worst case (linear sum)** | **1.70e-3** | **55.4 dB** | |
| **TOTAL, RSS** | **1.03e-3** | **59.8 dB** | |

**Against the corpus's 60 dB: −4.6 dB worst case, −0.2 dB RSS. There is no
margin.** The claimed +1.7 dB is optimistic by ~6 dB and was computed from one
term out of eight.

**And yes — that one term spends the entire budget.** `C_cm` tolerance alone is
60.3 dB, 56 % of the linear sum and **87 % of the RSS energy**. The page's
sentence *"±1 % is needed to clear 60"* is the finding stated one notch too
weakly: ±1 % *is* 60 dB, with seven other terms still to pay for.

**Worse: `bom.csv` never received the ±1 %.** `C-FILT-BREATH` reads
`15nF C0G (diff) + 1.5nF C0G (cm x2)` with **no tolerance field**
`[repo hardware/bom.csv:62]`, while the page that owns the requirement says
"Specify ±1 % C0G" `[repo hardware/module/breath-receive-stage.md:228]`. C0G
stock tolerance is ±5 %. At ±5 % the budget is **45.1 dB worst case / 46.3 dB
RSS** `[calc]` — the term swamps everything else at 87 % of the linear sum.
This is the project's named failure mode exactly: the fix landed on the
schematic page and not in the file the purchaser reads.

### 1.4 What `R1b` is actually worth

Re-running the same budget with ΔR = 1000 Ω (`R1` unmatched):

| | worst case | RSS | dominant term |
|---|---|---|---|
| no `R1b` | **43.3 dB** | 46.7 dB | series-R × `C_cm`, **47.2 dB** |
| with `R1b` | 55.4 dB | 59.8 dB | `C_cm` tolerance, 60.3 dB |

`R1b` buys **12.1 dB worst case / 13.1 dB RSS** `[calc]`. So `carrier.md`'s
"about 13 dB" is **correct** — I confirm it independently and by a different
route. The receive page's own "fifty times" (60.2 → 94 dB) is arithmetically
right and materially misleading: 94 dB was never reachable, because the 1 MΩ
pair and the capacitors cap it 20 dB lower. And note that the *dominant*
mechanism without `R1b` is not the 60.2 dB the page computes from the 1 MΩ
divider — it is the 47.2 dB from 1 kΩ working against `C_cm`, which is the case
`[SBOS792A p.9 Figure 18]` is drawn for. **`R1b` is more necessary than the
page's argument makes it, and the page's argument is the weaker of the two.**

### 1.5 The requirement, derived — because nobody has

Common-mode disturbance: `PWR_GND` is one 24 AWG conductor, 2 m, 0.168 Ω
`[repo docs/decisions/0003-breath-sensing-path.md:325-329, calc]`, carrying the
tracked `umbilical-current` 359 mA `[repo config/figures.yaml:285-288]` →
**`V_cm` = 60.3 mV**, moving with display brightness, LED animation and WiFi
bursts.

Error at the jack = `V_cm × A(cm→diff) × G × G_downstream`, with `G` = 2.1848
and the working downstream gain 2.18 (§4 below):

| CMRR | error at the BREATH jack | as % of a 10 V span |
|---|---|---|
| 45 dB | 1.6 mV | 0.016 % |
| 55.4 dB (as drawn, worst case) | **489 µV** | 0.0049 % |
| 60 dB | 287 µV | 0.0029 % |
| 65.5 dB | 153 µV | 0.0015 % |

Three candidate anchors, all `[calc]`:

- **Audibility.** Program-correlated AM on a VCA is inaudible well below 0.1 %;
  even 20 mV at the jack is −54 dB. → **23 dB required.**
- **Do not be the dominant error.** The chain's other terms are the sensor
  (§5, ±1.08 V at the jack), the REF5050 grade (±10 mV), op-amp offsets
  (~1 mV). To stay under 1 mV → **49 dB required.**
- **Match the module's own resolution.** 153 µV is 1 LSB of a 16-bit 10 V
  channel — the standard pitch and the mods are held to. → **65.5 dB.**

**Recommendation: adopt 60 dB and give it this derivation** — *"the moving
ground offset shall reach the BREATH jack at under 2 LSB of the module's other
channels (287 µV on 10 V)"*. It sits between the two defensible anchors, it is
the number three documents already use, and it is now sourced.

**But record the proportion honestly.** Against audibility the as-drawn circuit
has ~32 dB of margin. `docs/reference/pcb-pipeline.md:126` calls this the
project's thinnest margin; on the arithmetic it is the thinnest margin against
a *requirement that was never derived*, not against a failure. The capacitor
fix below is two BOM edits and costs nothing, so take it — but this is not a
showstopper, and treating it as one has already cost three review waves.

### 1.6 Proposed values

**`C_cm` → 470 pF ±1 % C0G; `C_diff` stays 15 nF; `R4`/`R5` → 1 MΩ 0.1 %.**

| Term | Conversion | CMRR |
|---|---|---|
| `C_cm` tolerance ±1 % | 3.12e-4 | 70.1 dB |
| **cable pair-to-ground C unbalance** | 2.19e-4 | **73.2 dB** |
| in-amp `z_ic` + PCB stray, 2 pF | 6.64e-5 | 83.6 dB |
| series-R × `C_cm`, 40 Ω | 5.67e-5 | 84.9 dB |
| series-R DC term | 3.96e-5 | 88.1 dB |
| INA828 intrinsic | 3.16e-5 | 90.0 dB |
| 1 MΩ pair at 0.1 % | 2.18e-5 | 93.2 dB |
| **TOTAL worst case / RSS** | 7.47e-4 / 3.95e-4 | **62.5 dB / 68.1 dB** |

**+2.5 dB worst case, +8.1 dB RSS.** `[calc]`

Ratio goes 10:1 → 32:1, so the lever factor falls 0.0476 → 0.0154. Costs:
the common-mode corner against 11 kΩ moves 9.6 kHz → 30.8 kHz, i.e. 10 dB less
shunting of out-of-band CM energy at 800 kHz (WS2815 data) and 2 MHz (SPI).
That is affordable: the INA828 carries an integrated RFI filter with a −3 dB
corner at **53 MHz** `[SBOS792A p.5]`, and `bom.csv` already records its EMIRR
table. If E11 shows RF ingress, the right answer is a common-mode choke on the
pair, not a bigger `C_cm` — a bigger `C_cm` buys RF rejection by spending CMRR
one-for-one through the factor above.

**Then the cable becomes the #2 term, and it is unmeasured.** 6.6 pF is
2 m × the TIA-568 limit of 330 pF/100 m for capacitance unbalance
pair-to-ground `[from memory]`. **No cable datasheet is banked** —
`datasheets/MANIFEST.csv` has the etherCON connectors and no cable. Either bank
a real Cat5e spec or measure the unbalance at E11; at 60 dB-class budgets a
guessed 6.6 pF is carrying 29 % of the linear sum.

Connector contribution is negligible and now sourced: NE8FDP contact resistance
**< 50 mΩ** `[NE8FDP-DS]`, two mated pairs → ≤100 mΩ of leg-to-leg imbalance →
(0.1/11k) × 0.0476 = 4.3e-7, **127 dB** `[calc]`.

### 1.7 The INA828's own number, at the gain actually used

`R_G` = 42.2 kΩ → **G = 1 + 50 k/42.2 k = 2.184834** `[SBOS792A p.5 gain
equation; calc]`. TI specifies CMRR only at G = 1/10/100/1000, **dc to 60 Hz,
RTI**: **90 dB MIN / 100 dB typ at G = 1**, 110/120 at G = 10
`[SBOS792A p.5]`. The 20 dB per decade of gain confirms the limit is the output
difference amplifier referred to input, so at G = 2.185 the min is
90 + 20·log10(2.185) = **96.8 dB**. **The budget above takes no gain credit and
uses 90 dB** — deliberately conservative, and it costs nothing because the term
is 1.9 % of the total.

**Do not use the dc figure above audio, and here is the shape of it**
`[SBOS792A p.9 Figure 17, read off the curve]`: the G = 1 trace holds 100 dB to
~300 Hz, ~93 dB at 1 kHz, ~75 dB at 10 kHz, ~62 dB at 100 kHz. At 10 kHz the
part's own rolloff becomes comparable with the network terms; at 100 kHz it is
co-dominant. The channel is band-limited to ~460 Hz ahead of the amplifier, so
this only matters for out-of-band CM energy that the amplifier can rectify —
which is the argument the page already makes for filtering ahead of the in-amp,
and the datasheet supports it.

### 1.8 The REF pin: TI's 5 Ω, and whether the buffer achieves it

**The requirement, verbatim** `[SBOS792A §8.1 p.22]`: *"any resistance at the
reference terminal (shown as `R_REF` in Figure 61) is in series with one of the
internal 40-kΩ resistors… For the best performance, keep the source impedance
to the REF terminal, `R_REF`, below 5 Ω."* Figure 63 p.23 shows the remedy as
literally an op-amp buffering a divider — the topology this page already has.

The mechanism, in closed form `[calc]`: `R_REF` unbalances one arm by
δ = `R_REF`/40 kΩ, and a unity difference amplifier with one arm off by δ has
`A_cm` = δ/2, so

```
   CMRR(diff-amp stage)  =  2 / δ  =  80 kΩ / R_REF
   R_REF = 5 Ω    →  84.1 dB      (×G = 90.9 dB referred to the in-amp input)
   R_REF = 2.5 kΩ →  30.1 dB
```

**The buffer achieves it, with three decades to spare.** OPA2197 closed-loop
output impedance `Z_out(f) = Z_O/(1 + A_OL(f))` with `Z_O` = **375 Ω**
`[SBOS737C p.8]` — a plateau from 100 Hz to 300 kHz per Figure 26
`[repo config/figures.yaml:314-318]` — `A_OL` ≥ 120 dB at DC and GBW = 10 MHz
`[SBOS737C p.7-8]`:

| f | `A_OL` | `Z_out` | CMRR from REF |
|---|---|---|---|
| DC | ≥1e6 | ≤0.4 mΩ | >165 dB |
| 500 Hz | 20 000 | **18.7 mΩ** | 132.6 dB |
| 10 kHz | 1 000 | 0.375 Ω | 106.6 dB |
| **135 kHz** | 74 | **5.0 Ω** | **84.1 dB** |

`[calc]` **`R_REF` < 5 Ω holds to 135 kHz.** PCB trace is a non-issue: 5 Ω is
~1.5 m of 6-mil 1 oz trace `[from memory, 0.5 mΩ/square]`.

**Two design rules fall out, and neither is written down anywhere:**

- **Do not decouple the REF node.** The instinct to put 100 nF on it is wrong:
  the OPA2197 drives ≤1 nF in unity gain with ~40 % overshoot
  `[SBOS737C §7.3.5 p.22, Figures 27/28]`, and the standard fix — an isolation
  resistor — goes *in series with REF* and is exactly the 5 Ω budget. Any
  `R_ISO` at REF ≥ 5 Ω is a CMRR defect. Put nothing on that net but the
  buffer output and the INA828 pin.
- **The REF pin sources real current, and it is signal-dependent.**
  `I_REF = (V_o1 − V_REF)/80 kΩ`, and `V_o1` (the input stage's non-inverting
  output) swings to −2.85 V at full sensor range → **up to 43 µA** `[calc]`.
  This quantifies the page's "a bare trimmer would spend the entire 60 dB
  budget": a bare 10 kΩ pot has a worst Thévenin of 2.5 kΩ, giving **30 dB** of
  CMRR *and* 43 µA × 2.5 kΩ = **107 mV of signal-dependent output shift** —
  a ~1 % gain error on top. The page understates its own case by 30 dB.

### 1.9 Bias current, offset, and the 1 MΩ pair

`[SBOS792A p.5]`: `I_B` 0.15 nA typ / **0.6 nA max** (2 nA over temperature);
`I_OS` the same; `z_id` 100 GΩ‖1 pF, `z_ic` 100 GΩ‖10 pF.

- **Connected.** The impedance from each input node back to its driving source
  is 11 kΩ ‖ 1 MΩ = 10.88 kΩ, so `I_OS` × 10.88 kΩ = **6.5 µV** RTI max
  (21.8 µV over temperature) `[calc]` — negligible beside `V_OS`.
- **Unplugged.** `I_B` flows only in the 1 MΩ. Each input rises to
  0.6 nA × 1 MΩ = 0.6 mV (2 mV hot); the differential from `I_OS` is the same
  → **≤4.4 mV at the in-amp output** `[calc]`. The bias pair does its job:
  the jack stays at zero, which is what ADR 0005 promises.
- **Offset.** `V_OSI` 50 µV max, `V_OSO` 250 µV max (500 µV hot), drifts
  0.5 and 5 µV/°C `[SBOS792A p.5]`. At G = 2.185:
  `V_OS(RTI) = 50 + 250/2.185 =` **164 µV max** → 359 µV at the output;
  drift `√(0.5² + (5/2.185)²) =` **2.34 µV/°C** RTI → 5.1 µV/°C out →
  **102 µV over a 20 K warm-up** `[calc]`. Trimmed out at commissioning and
  irrelevant beside the sensor (§5).
- **Noise**, for the record so nobody re-raises it: `e_N(RTI)` =
  `√(7² + (90/2.185)²)` = 41.8 nV/√Hz `[SBOS792A p.5]` → ~1.0 µV RMS over the
  460 Hz channel → **~4.8 µV at the jack** `[calc]`. 0.00005 % of span.

**One correction to the page's wording.** *"1 MΩ… diverts tens of nanoamps"*
`[repo hardware/module/breath-receive-stage.md:233]` is true of the **`AGND`
sense conductor** (60 mV of CM / 1 MΩ = 60 nA, 0.17 ppm of 359 mA — the 0.2 ppm
claim is confirmed `[calc]`) and **false of the `BREATH` leg**, where `R4`
carries `V_node`/1 MΩ = 0.26 µA at rest and **4.8 µA at full scale**. That
current returns to the instrument through `PWR_GND`, not through `AGND`. State
it, because a SPICE run will show 4.8 µA in a resistor the page calls
"tens of nanoamps" and somebody will file a bug.

---

## 2. Impedance, end to end

| Node | Source impedance | Load presented | Verdict |
|---|---|---|---|
| MPXV4006DP `Vout` | **not specified** `[MPXV4006 r3 p.3]` — Table 1 has no output impedance or source-current row | as drawn on this page, the **0.6× ADC divider** (§6.3) | **Flagged.** ADR 0003 and `carrier.md` both say divide *after* the buffer; this page's drawing branches at the sensor. |
| OPA2197 buffer out | `375/(1+A_OL)`: 0.4 mΩ DC, 18.7 mΩ at 500 Hz, 3.7 Ω at 100 kHz `[SBOS737C p.8; calc]` | `R1` 1 kΩ then 2 m of cable then 1 MΩ; 4.8 µA peak | fine. Drives ±65 mA `[SBOS737C p.8]`; the +12 V fault needs 11.8 mA. |
| `R1` / `R1b` | 1 kΩ 1 % each | — | The *imbalance* between the legs is what matters: 40 Ω worst case including `R2`/`R3`, which is §1.3's term. |
| 2 m Cat5 | 0.168 Ω/conductor `[calc, 24 AWG 0.0842 Ω/m]`; ~100–200 pF differential `[from memory]`; ≤50 mΩ per contact `[NE8FDP-DS]` | — | Resistance and its imbalance are negligible. **The capacitance *unbalance* is not** — §1.6. |
| `R2`/`R3` 10 kΩ 0.1 % | — | INA828 inputs, 100 GΩ‖10 pF `[SBOS792A p.5]` | Free, exactly as `bom.csv:61` says. |
| 1 MΩ bias pair | — | loads each leg | **Gain effect verified**, below. |
| INA828 `REF` | buffered, <5 Ω to 135 kHz `[calc]` | 40 kΩ internal, 43 µA signal-dependent `[calc]` | **Meets `[SBOS792A §8.1 p.22]`.** |
| INA828 `OUT` | — | `POT-GAIN` 50 kΩ + `R-GAIN-FLOOR` 7.15 kΩ = 57.15 kΩ `[repo hardware/module/breath-output-stage.md]` | fine. |
| Summer out | — | `R-OUT-PROT` 1 kΩ + a Eurorack input (~100 kΩ) | −0.86 % of span from the 1 kΩ — **not accounted anywhere**; it shifts the working gain from 2.156 to 2.178. |

**The effective 2.1611 is verified** `[calc]`:

```
   G        = 1 + 50 kΩ/42.2 kΩ                 = 2.184834
   divider  = 1 MΩ / (1 MΩ + 11 kΩ)             = 0.9891197
   effective                                     = 2.1610624
   × 4.6 V (VFSS typ, MPXV4006 r3 p.3)          = 9.9409 V
```

Matching `config/figures.yaml:25-32` to six figures. **`inamp-full-scale` =
−9.94 V stands**, and it stands for a reason worth recording: it is derived
from the *span*, and the span (4.6 V) is the one sensor number the corpus has
right (§5). Note the page's own description — *"loss in the 2 × 1 MΩ bias pair
against 2 × 11 kΩ series"* — describes a 2 MΩ/22 kΩ divider; the correct model
is one 1 MΩ against one 11 kΩ per leg, which happens to give the same ratio.
Harmless, but a SKiDL author reading it will build the wrong thing.

**No source drives a load it cannot.** The only impedance that fails a spec is
the *reference buffer* at the far end of the chain — see §7.

---

## 3. The page's open item: stale in three parts, live in four others

> *"The downstream gain/offset stage is drawn as a block, and three things about
> it are open…"* `[repo hardware/module/breath-receive-stage.md:317-335]`

`hardware/module/breath-output-stage.md` now exists, and **all three bullets are
resolved**:

| Bullet | Resolution |
|---|---|
| offset reference from the LM317 rail, not `VREFOUT` | **Resolved.** `POT-OFFSET` spans the buffered 5.21 V rail. |
| needs two op-amp halves, gain as a buffered attenuator ahead of the summing node | **Resolved.** `POT-GAIN` 50 k attenuator → follower → `R-IN` 10 k → summer, `R-FB`/`R-IN` = 4.02. |
| drawn at last | **Resolved.** |

**So the item is stale and should be deleted.** But four things *are*
unresolved across that boundary, and none of them is in the list:

1. **The op-amp half census is over-subscribed by one.** This page says the REF
   buffer *"costs the last spare OPA2197 half… so there is still one"*
   `[repo hardware/module/breath-receive-stage.md:143-144]`.
   `bom.csv:13` says ten of twelve used, two spare. `breath-output-stage.md` §4
   then spends **both** remaining halves on `POT-RESP`, and in the same box says
   the `POT-OFFSET` buffering fix *"wants a half, and this stage takes the last
   two."* Three claims on two halves. `bom.csv:84` adds `U-RESP` as a seventh
   package, which resolves it by adding a part — but no page says so.
2. **Polarity has never been re-derived with `POT-RESP` inserted.**
   `breath-output-stage.md` raises this against itself and it lands on this
   page, because this page owns the in-amp's sign. §4 below re-derives it.
3. **`POT-OFFSET`'s centre.** `breath-output-stage.md`'s own values table says
   centre = **+0.07 V**; its §4 box says the unbuffered wiper puts the true zero
   ~20° past centre at **+0.605 V**. Two numbers, one page, and this page
   repeats the first as *"±5 V, zero at centre"*
   `[repo hardware/module/breath-receive-stage.md:280-281]`.
4. **This page draws parts the output-stage page owns.** *"Output RC | 1 kΩ +
   330 nF film"* `[repo hardware/module/breath-receive-stage.md:164]` is
   `R-OUT-PROT` + `C-OUT-BREATH` `[repo hardware/bom.csv:52,63]`. Two drawings
   of one RC with no refdes on one of them is a duplicate-instantiation trap in
   a netlist. Also: *"reconstruction"* is a word left over from the digitised
   design — breath never passes a DAC, so there is nothing to reconstruct. It
   is an anti-alias/slew-limit filter.

**Replace the open item with those four.**

---

## 4. The chain end to end — sensor to jack

Using datasheet values throughout (see §5 for why the sensor numbers change).

```
 P (kPa) ──sensor──► V_s = 5.000 × (0.1533·P + 0.053)          [MPXV4006 r3 p.5]
         ──buffer──► ×1
         ──link────► ×0.9891197                                 [calc]
         ──INA828──► ×(−2.184834), + V_REF                       [SBOS792A p.5]
         ──RESP?───► ×(−0.5) then ×(−2)  = ×1 small-signal, ≤1.5× shaped
         ──POT-GAIN► ×0.12511 … 1.000                            [repo output-stage]
         ──summer──► ×(−4.02), + V_offset
         ──R-OUT───► ×0.9901 into 100 kΩ
```

**Net polarity: positive-going at the jack.** In-amp inverts (BREATH on `−IN`),
summer inverts, `POT-RESP` inverts twice. Four inversions → breath pushes the
jack **up**. `[calc]` The §4 question is answered: inserting `POT-RESP` does not
change polarity.

**Gain and headroom.** In-amp sensitivity is **1.6565 V/kPa** `[calc]`.

| P | sensor | in-amp out | jack at working gain 2.178× |
|---|---|---|---|
| 0 | 0.265 V | 0.000 V | 0.00 V + offset |
| 1.0 kPa | 1.031 V | −1.656 V | +3.57 V |
| 2.8 kPa ("hard blow") | 2.411 V | **−4.638 V** | **+10.00 V** |
| 6.0 kPa (full scale) | 4.864 V | −9.939 V | +21.4 V — **clipped** |

**The corpus says −4.69 V; it is −4.64 V.** `breath-output-stage.md`'s table
applies the raw G = 2.185 where the same page's full-scale row applies the
effective 2.1611. 1.1 % inconsistency, and it propagates into "≈2.13×" — the
gain that actually reaches 10 V is **2.156×**, or **2.178×** once the 1 kΩ
output resistor's 0.86 % is included `[calc]`.

**Where headroom runs out.** OPA2197 swings to within 125 mV of its rails at
10 kΩ `[SBOS737C p.8]`; module rails are ~±11.65 V after `D-REVPOL`, so
**±11.5 V** — which is exactly the figure `breath-output-stage.md` uses, and it
is now sourced. Clip pressure `[calc]`:

| GAIN | OFFSET | clips above |
|---|---|---|
| 0.503× (full CCW) | 0 | 13.8 kPa — never |
| **2.178× (working)** | 0 | **3.19 kPa** |
| 2.178× | +5.04 V | **1.79 kPa** |
| 4.02× (full CW) | 0 | 1.73 kPa |
| 4.02× | +5.04 V | 0.97 kPa |

**This is the number the corpus does not have.** `breath-output-stage.md` states
the clip qualitatively ("offset at +5 V and gain at 4× puts a hard blow at
+23 V") but never in pressure. At the *working* setting the jack clips at
3.19 kPa against a 2.8 kPa hard blow — **14 % of margin**, and the sensor's
±5 %VFSS span tolerance (§5) is ±5 % of that. With the offset knob anywhere
above about +1 V a hard blow clips. That is a legitimate performance
characteristic, but it should be on the panel-legend/manual list, and it makes
`breath-working-point` (currently **disputed**, `[repo config/figures.yaml:165]`)
a *headroom* question, not only a gain-range one.

**Total offset at the jack, breath at zero** `[calc]`:

| Contributor | at the jack |
|---|---|
| `TRIM-BREATH-ZERO` setting resolution (10 k multiturn, 1.0 V span) | ±1 mV |
| INA828 `V_OS` drift, 20 K | ±0.22 mV |
| OPA2197 offsets (buffer ×4.02 + summer × noise gain 7.36) | ±1.1 mV |
| LM317 rail movement, 1 % (§7) | ±21 mV |
| **sensor, ±5.0 %VFSS over 10–60 °C** | **±1.08 V** |
| `POT-OFFSET` | ±5 V by design |

Every electronic term is three orders below the sensor. §5.

---

## 5. Provenance re-check: what the sensor datasheet actually says

**This is the largest single finding in this slice, and it is not about CMRR.**

`[MPXV4006 r3 p.3, Table 1 and p.5, Figures 4/5]`, verbatim:

```
   Transfer function:  Vout = VS × [(0.1533 × P) + 0.053]
   Voff   min 0.152   typ 0.265   max 0.378  V
   VFSS         —     typ 4.6       —        V
   Accuracy, 10 to 60 °C:  ±2.46 %VFSS with auto zero
                           ±5.0  %VFSS without auto zero
   Operating temperature:  +10 °C to +60 °C
   Supply current: 10 mA max
```

| Corpus claim | Where | Verdict |
|---|---|---|
| `Vout = VS × (0.1533·P + 0.04)` | `[repo docs/decisions/0003-breath-sensing-path.md:121, L33]` | **REFUTED.** The constant is **0.053**. 0.04 is the MPXV5004 family's `[from memory]`. |
| pedestal **0.200 V typ**, *"by design"* | `[repo hardware/module/breath-receive-stage.md:79-80,96]` | **REFUTED.** Typ is **0.265 V**. 0.200 V comes from the datasheet's *front-page marketing line* "0.2 to 4.8 V Output" `[MPXV4006 r3 p.1]`, which contradicts its own Table 1. |
| pedestal band **0.152–0.378 V** | same | **CONFIRMED** `[MPXV4006 r3 p.3]`. The one sensor figure the corpus has exactly right. |
| `sensor-full-scale` = **4.80 V**, "settled" | `[repo config/figures.yaml:34-40]` | **WRONG.** 0.265 + 4.6 = **4.865 V typ** (band 4.752–4.978 V). |
| span **4.6 V** | `[repo hardware/module/breath-receive-stage.md:170]` | **CONFIRMED** — `VFSS` typ 4.6 V. |
| sensitivity **766 mV/kPa** | `[repo docs/decisions/0003-breath-sensing-path.md:115]` | **CONFIRMED** `[MPXV4006 r3 p.3]`. |
| `V_REF` = **+0.437 V** nulls the pedestal | `[repo hardware/module/breath-receive-stage.md:56,96]` | **WRONG twice.** Wrong pedestal *and* the raw G instead of the effective one. Correct: **0.573 V** = 2.1611 × 0.265 `[calc]`. |
| `V_REF` range needed **0.332–0.826 V** | `[repo hardware/module/breath-receive-stage.md:96-97]` | **0.3285–0.8169 V** with the effective gain `[calc]`. Conclusion (range 0→+1.0 V) unaffected. |
| 0→0.6 V "covers pedestals only to 0.275 V" | same | **CONFIRMED** (0.2776 V with the effective gain) `[calc]`. |
| "leaving **1.4–5.6 %** of span standing" | same | **Not reproducible.** I get **up to 2.2 %** (0.378 − 0.2776 = 0.100 V × 2.1611 = 0.217 V on 9.94 V) `[calc]`. |
| "response ~1 ms = ~159 Hz corner" | `[repo hardware/bom.csv:5]`, ADR 0003 latency table | **NOT IN DOCUMENT.** Rev 3 has **no response-time specification at all**. `[from memory]` — needs AN1646 or a bench measurement. |
| `TcOffset` **0.5 mV/K** | `[repo docs/decisions/0003-breath-sensing-path.md:L227]`, and the "20 mV in 10 V" claim `[repo hardware/module/breath-receive-stage.md:283-286]` | **NOT IN DOCUMENT, confirming the brief.** `TcOffset` appears only as a *named component of the accuracy budget* (footnote 4), with no number. |

**What can and cannot be claimed about thermal drift.**

- **Cannot:** any mV/K figure. Neither 0.5 mV/K nor a derived 2.34 mV/K is
  sourced, and the datasheet does not decompose the budget. The receive page
  already says the figure is unverified — **it is now confirmed unverifiable
  from this document.**
- **Can:** the *bounded* claim. Total error over **10–60 °C** is **±5.0 %VFSS
  without auto zero** = ±0.230 V at the sensor = **±0.497 V at the in-amp
  output = ±1.08 V at the jack** at the working gain `[calc]`.
- **And the ±2.46 % column does not apply to the analog path.** Footnote 5
  requires auto-zeroing *and* *"a maximum temperature change of ±5 °C between
  autozero and measurement"* `[MPXV4006 r3 p.3]`. `TRIM-BREATH-ZERO` is set once
  at commissioning against an interior that then rises 10–20 K. **The analog CV
  is in the ±5.0 % column by construction.** The digital copy, which firmware
  re-zeros continuously (ADR 0006), is in the ±2.46 % column — which is a real,
  previously unstated argument *for* the split-authority design.

So: *"thermal drift on the order of 20 mV in 10 V… a quarter turn if it ever
bothers you"* is unsupported and optimistic by up to ~50×. Rewrite it as the
bounded claim. **This does not break the design** — breath is a performance
control with a knob, not a calibrated instrument — but it is the term that
actually sets what the OFFSET knob is for, and the corpus currently attributes
that role to a 20 mV number.

**Two further datasheet facts nobody has recorded:**

- **Operating temperature is +10 °C to +60 °C** `[MPXV4006 r3 p.4]`. A cold
  room is out of spec. Not a defect — a statement the corpus should carry.
- **Footnote 5 says mounting stress moves the zero** and the 0.152–0.378 V band
  is quoted *with* the auto-zero caveat. A mounted, un-auto-zeroed part may sit
  outside the band, which is the band `TRIM-BREATH-ZERO`'s 0→+1.0 V was sized
  against. **Propose widening to 0→+1.2 V**; it is one resistor value and costs
  no headroom (the in-amp reaches −10.8 V at `V_REF` = 0 on ±11.65 V rails).

**`R-TRIM-RANGE` is still `open` with no values** `[repo hardware/bom.csv:126]`.
Proposing one, since SPICE needs it: **`R-TRIM-RANGE-BREATH` = 42.2 kΩ 1 %**
from the 5.21 V rail to the top of the 10 kΩ pot, pot bottom to `AGND_MOD` →
5.21 × 10/52.2 = **0.998 V** `[calc]`. For a 1.2 V ceiling use **33.2 kΩ** →
1.206 V. Wiper Thévenin ≤2.5 kΩ, buffered, so it is invisible to CMRR.

---

## 6. Netlist readiness

### 6.1 The two collisions, and the canonical naming

`AGND` names **three** distinct nodes in this slice and `BREATH` names **two**:

| Name as used | Node | Where |
|---|---|---|
| `AGND` | the umbilical **sense conductor**, pin 2 — a signal net that carries 60 nA | `[repo hardware/module/breath-receive-stage.md:28]`, `[repo docs/decisions/0004-cv-interface-module.md:99]` |
| `AGND` | the **instrument** analog star pour | `[repo docs/decisions/0003-breath-sensing-path.md:L282]` |
| `AGND(module)` | the **module** analog return pour | `[repo hardware/module/breath-receive-stage.md:39,43,47]` |
| `BREATH` | the umbilical conductor / in-amp input, pin 1 | `[repo hardware/module/breath-receive-stage.md:22]` |
| `BREATH` | the **output jack** net | `[repo hardware/module/breath-receive-stage.md:74]` |

They appear **in the same ASCII drawing, 52 lines apart**. A naïve SKiDL
transcription shorts the in-amp's inverting input to its own output through the
whole downstream stage, and ties the sense conductor to module ground —
destroying the one property the ADR exists to protect.

**Proposed canonical net names.** Rule: `BREATH` and `AGND` are **banned as
net identifiers**; they survive only as *pin-function labels* on the umbilical
connector symbols, which is what `umbilical-pinmap`
`[repo config/figures.yaml:111-115]` tracks and which therefore does not change.

| Canonical net | Node | Members |
|---|---|---|
| `BREATH_SENSE` | sensor output | `U-BREATH.Vout`, `U-BUF.A+` |
| `BREATH_BUF` | instrument buffer output | `U-BUF.A_OUT`, `R-SER-BREATH-INST(R1)`, `R-ADCDIV-U` — **see §6.3** |
| `UMB_BREATH` | umbilical conductor, pin 1 | `R1`, `D-TVS-BREATH.1`, `J-UMB.1` … `SKT-UMB.1`, `R-SER-BREATH(R3)` |
| `UMB_AGND` | umbilical **sense** conductor, pin 2 | `R1b`, `D-TVS-BREATH.2`, `J-UMB.2` … `SKT-UMB.2`, `R-SER-BREATH(R2)` |
| `AGND_INST` | instrument analog star pour | sensor GND, REF5050 GND, both OPA2197 halves' references, ADC divider low leg, `R1b` |
| `AGND_MOD` | module analog return pour | `R4`, `R5`, both `C_cm`, `TRIM-BREATH-ZERO` low, `R-GAIN-FLOOR`, `C-OUT-BREATH` |
| `PWR_GND`, `DIG_GND` | unchanged | — |
| `BR_INN` | INA828 pin 2 (`−IN`) | `R3`, `R5`, `C_cm(N)`, `C_diff`, `D-CLAMP-BREATH(N)` |
| `BR_INP` | INA828 pin 3 (`+IN`) | `R2`, `R4`, `C_cm(P)`, `C_diff`, `D-CLAMP-BREATH(P)` |
| `BR_RG_A` / `BR_RG_B` | INA828 pins 1 and 8 | `R-GAIN-INAMP` only — nothing else, ever |
| `BR_REF` | INA828 pin **5** | REF-buffer output **and nothing else** (§1.8) |
| `BR_REF_SET` | trimmer wiper | `TRIM-BREATH-ZERO.W`, REF buffer `+` |
| `BREATH_INAMP` | INA828 pin 6 (`OUT`) | → `POT-RESP` if fitted, else `POT-GAIN` top |
| `BREATH_SHAPED` | `POT-RESP` stage output | (only if §4 of the output page is built) |
| `BREATH_ATT` | gain-buffer output | `R-IN` |
| `BREATH_SUM` | summer virtual ground | `R-IN`, `R-OFF`, `R-OFFNEG`, `R-FB` |
| `BREATH_OUT` | summer output | `R-FB`, `D-JACK-CLAMP`, `R-OUT-PROT` |
| `BREATH_JACK` | jack tip — *this* is what `BREATH` means downstream | `R-OUT-PROT`, `C-OUT-BREATH`, `J-BREATH.T` |
| `V5R21` | LM317 rail | `TRIM-BREATH-ZERO` top via `R-TRIM-RANGE-BREATH`, `POT-OFFSET` top, DAC `AVDD` — **§7** |

### 6.2 Pin numbers — one transcription trap, from TI

**`REF` is pin 5. `OUT` is pin 6.** `[SBOS792A p.3, Pin Functions]`:
`RG` 1, `−IN` 2, `+IN` 3, `−VS` 4, `REF` 5, `OUT` 6, `+VS` 7, `RG` 8.

**§8.1 of the same datasheet says "the reference pin (pin 6)"**
`[SBOS792A §8.1 p.22]`. TI contradicts itself, and §8.1 is the section this
project quotes. A SKiDL author following the prose wires `TRIM-BREATH-ZERO`'s
buffer **onto the in-amp's output**. Put the pin table's numbers in the
netlist and a comment saying why.

Also required and absent from the drawing: **`C-DECOUPLE` 100 nF on pins 4 and
7** — `bom.csv:43` allocates 2 for the INA828, the schematic page shows none.
The INA828 has **no ground pin**; its output is referenced entirely to `BR_REF`.

### 6.3 Four ambiguities that block a clean transcription

1. **`C_diff`'s far end is not drawn to a node.** Lines 41–48 run `C_diff`'s
   right-hand rail down the right margin past the in-amp. It must connect
   `BR_INP`–`BR_INN`. As drawn it is unresolvable.
2. **`D-CLAMP-BREATH` is on the wrong side of `R2`/`R3`, or the BOM is.** The
   drawing puts "BAV99 to ±12 V, both legs" at the connector, *ahead* of
   `R2`/`R3` `[repo hardware/module/breath-receive-stage.md:33]`; `bom.csv:125`
   says *"behind the 10k series resistors"*. **The BOM is right** — behind the
   10 kΩ the fault current is (12+12)/10 kΩ = 2.4 mA `[calc]`; ahead of them it
   is limited only by `R1` and the cable. Fix the drawing.
   BAV99 wiring for the netlist: centre pin = signal, one end to −12 V, one to
   +12 V `[from memory — verify against a BAV99 datasheet; none is banked]`.
3. **The ADC divider taps the wrong node.** This page's drawing branches
   `0.6× divider → C-AA-ADC → MCP3202` off the **sensor**
   `[repo hardware/module/breath-receive-stage.md:22-26]`. ADR 0003 says
   *"Divide after the buffer, not before, so the divider does not load the
   sensor"* `[repo docs/decisions/0003-breath-sensing-path.md:L158]` and
   `carrier.md` draws it after the buffer. **`carrier.md` and the ADR are
   right**; this page's tree is wrong.
4. **`R2` is the `AGND` leg and `R3` is the `BREATH` leg**, which is the reverse
   of reading order. Verified consistent between the drawing's annotations and
   its geometry `[repo hardware/module/breath-receive-stage.md:23,29,35-37]` —
   but it is a trap, so name them by leg in the netlist
   (`R-SER-BREATH-P` / `R-SER-BREATH-N`) rather than by number.

---

## 7. Two live stale values on this page, which the checker cannot see

Both are in the page's last section, "The instrument-side reference buffer is
not stable as connected", and both are tracked as **disputed** in
`config/figures.yaml` while this page states them as settled — a direct
violation of CLAUDE.md rule 1 (cite, do not restate).

1. **"a pole at 21 kHz inside its own loop, three decades below crossover"**
   `[repo hardware/module/breath-receive-stage.md:342-343]`. The 21 kHz was
   back-solved from `Ro` ≈ 75.8 Ω. TI specifies **`Z_O` = 375 Ω**
   `[SBOS737C p.8]`, so **the pole is 4.24 kHz** and it is 3.4 decades below
   crossover `[repo config/figures.yaml:314-324; calc]`. `figures.yaml` lists
   only the two `75.8` strings as `forbidden`, so `tools/check-staleness.py`
   passes this page while it carries the derived value.
   **Propose adding to `opa2197-output-impedance.forbidden`:**
   `"pole at 21 kHz inside its own loop"` and `"three decades below crossover"`.
2. **"`R-ISO-REF` goes inside the loop"** `[repo hardware/module/breath-receive-stage.md:350-352]`,
   stated as decided. `riso-ref-topology` is **disputed**
   `[repo config/figures.yaml:248-275]`, simulation puts in-loop at 8.4° of
   phase margin (worse than fitting nothing), and TI publishes a worked answer
   for this exact circuit — `R_ISO` 37.4 Ω with dual feedback, 89° —
   `[SBOS737C §8.2.3 p.30 Figure 56]`. The page's in-loop/out-of-loop dichotomy
   is a **false dichotomy** against the banked datasheet. The page also asserts
   `C-REF-OUT` sits on the buffer's output, which is the `cref-out-node`
   dispute `[repo config/figures.yaml:214-234]`.
   **Replace both paragraphs with a citation to the two `figures.yaml` entries.**
   The arithmetic the page does give is correct: 10 Ω × 10 mA = 100 mV = 2 % of
   5.000 V `[calc]`, and 10 mA is the datasheet **max** supply current
   `[MPXV4006 r3 p.3]`.

A third, smaller, on the same page: **the differential pole is 459 Hz, not
482 Hz.** `[calc]` 482.3 Hz is `1/(2π·22 kΩ·15 nF)` and omits the two `C_cm`
in series across the differential port (0.75 nF), giving 15.75 nF →
**459.3 Hz**. With the §1.6 proposal (470 pF) it becomes **474.8 Hz**, closer to
the page's stated intent. The "~480 Hz" output RC is correct at 482.3 Hz.

**And one cross-cutting finding that belongs to this stage.** The breath zero
(`TRIM-BREATH-ZERO`) and the breath offset (`POT-OFFSET`) are both referenced to
the LM317 5.21 V rail, which is **the DAC8568's own `AVDD`**
`[repo hardware/module/power-entry.md:18]`. `V_REF` moves 1:1 with that rail
into the in-amp's output: 1 % of rail = 52 mV at the top of the trim divider →
~10 mV at `BR_REF` → **21 mV at the jack** at working gain `[calc]`. The DAC
switches six channels at 4 kHz on that supply. This is the failure class ADR
0003 spends five pages eliminating from the *umbilical* — breath CV modulated by
digital activity — re-entering from the module side, through the rail this page
chose precisely because it is *"up whenever +12 V is"*. Not quantified here
(AVDD ripple is not in any document I read); **flagged as needing either a
measurement at E13 or a separate quiet tap.**

---

## 8. Summary of proposed values

| Item | Now | Proposed | Why |
|---|---|---|---|
| `C_cm` ×2 | 1.5 nF C0G, **no tolerance in BOM** | **470 pF ±1 % C0G** | §1.6 — the 10:1 ratio is the whole budget; 32:1 buys 10 dB |
| `C_diff` | 15 nF C0G | 15 nF C0G ±2 % | pole 474.8 Hz; tolerance is second-order here |
| `R4`/`R5` | 1 MΩ **1 %** | **1 MΩ 0.1 %** thin film | §1.6 — 73.2 → 93.2 dB for a reel change |
| `V_REF` at commissioning | +0.437 V | **+0.573 V** (typ part) | §5 — datasheet pedestal is 0.265 V |
| `TRIM-BREATH-ZERO` range | 0 → +1.0 V | **0 → +1.2 V** | §5 — mounting stress moves the zero outside the quoted band |
| `R-TRIM-RANGE-BREATH` | **open, no value** | **42.2 kΩ 1 %** (0→0.998 V) or **33.2 kΩ** (0→1.206 V) | §5 — SPICE cannot run without it |
| `BR_REF` decoupling | unstated | **none, and say so** | §1.8 — any cap there forces an `R_ISO` that is the 5 Ω budget |
| `sensor-full-scale` | 4.80 V, "settled" | **4.865 V typ** (4.752–4.978) | §5 |
| link CMRR requirement | 60 dB, underived | **60 dB, = 287 µV at the jack, <2 LSB** | §1.5 |
| CMRR margin | "1.7 dB" | **+2.5 dB worst case / +8.1 dB RSS after the fixes** | §1.6 |

**First simulation, and what it should be asked.** The CMRR chain is queued
first. Do not sweep CMRR as a scalar — sweep **`V_cm` → `V_BREATH_JACK` from
1 Hz to 1 MHz** with the capacitor tolerances as Monte Carlo parameters, and
read the *absolute* error, not the ratio. The ratio degrades without limit above
the pole while the error flattens, and every scalar CMRR number in this corpus
— mine included — is a single point on a curve whose shape nobody has drawn.
