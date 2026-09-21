# A6 — Pitch stage and mod channels (cold hardware review)

**Reviewer:** cold reviewer, A6. **Date:** 2026-09-21.
**In scope:** `hardware/module/pitch-stage.md`, `hardware/module/mod-channels.md`.
**Supporting:** `hardware/bom.csv`, `docs/decisions/0004`, `docs/decisions/0006`,
`hardware/module/digital-and-supervision.md`, `hardware/module/power-entry.md`,
`firmware/README.md`, `docs/reference/latency-budget.md`.
**Not read, deliberately:** anything under `docs/review/**` or `docs/research/**`.

Every claim below is tagged `[repo]`, `[calc]`, `[web]` or `[from memory]`.
Findings are indexed by **circuit node or BOM reference**, not by document.

---

## 0. THE HEADLINE — pitch accuracy in cents, 0–40 °C

**Conversion used throughout** `[calc]`: 1 V/oct at the jack ⇒ 1 V = 1200 cents,
so **1 mV = 1.2 cents**; one semitone = 83.333 mV.

**Quantisation floor** `[calc]`: DAC full scale 5.000 V, 16 bit ⇒ 1 LSB =
5.000/65536 = 76.294 µV at the DAC; × gain 2 ⇒ **152.6 µV = 0.183 cents at the
pitch jack**. Nothing below ~0.2 cents is worth arguing about. The 0.25–4.75 V
window uses 58,982 of 65,536 codes (90 %) `[calc]`.

### Device data used

| Parameter | Value | Source |
|---|---|---|
| DAC8568 internal ref drift | **2 ppm/°C typ, 5 ppm/°C max** | `[web]` TI search result for SBAS430 (ti.com itself proxy-blocked) |
| DAC8568 internal ref initial accuracy | 0.004 % typ | `[web]` same |
| DAC8568 grade C | **gain = 2 (5 V FS), reset to ZERO scale**; internal ref **disabled by default** | `[web]` https://www.ti.com/product/DAC8568 + TI search result: "Gain = 1 for A/B grades or 2 for C/D"; "Grades A and C reset to zero scale and B and D grades reset to midscale" |
| DAC8568 settling | **5 µs typ, full scale, unloaded**; slew 0.75 V/µs; drives 2 kΩ ∥ 3000 pF; DC Rout at mid-code **4 Ω**; AC crosstalk −109 dB | `[web]` same |
| OPA2197 Vos / drift | ±25 µV typ, **±100 µV max**; **±0.25 µV/°C typ, ±2.5 µV/°C max** | `[web]` https://www.ti.com/lit/ds/symlink/opa2197.pdf (via search summary; PDF itself proxy-blocked) |
| OPA2197 GBW / SR / Iout / Cload | 10 MHz, 20 V/µs, **±65 mA**, **direct capacitive load to 1 nF** | `[web]` same |
| LT5400 matching / matching drift | A 0.01 %, B 0.025 %; **0.2 ppm/°C matching drift** (1 ppm/°C also quoted); absolute drift 8 ppm/°C | `[web]` https://www.analog.com/en/products/lt5400.html (datasheet PDF proxy-blocked) |
| DAC8568 INL | ±4 LSB typ, ±12 LSB max | `[repo]` ADR 0006; `[from memory]` — could not confirm, ti.com blocked |
| DAC8568 gain/offset error drift | ~1 ppm/°C, ~1 µV/°C | `[from memory]`, unverified |

### The budget

Assumptions, stated so they can be attacked `[calc]`: calibration (trim + the
11-point firmware table) is performed at **25 °C**; operating range **0–40 °C**;
worst excursion from calibration **ΔT = 25 K**. All terms are *post*-calibration.
Levers are the ones `pitch-stage.md` derives and which I have re-checked:

- Reference (VREFOUT) drift is a **pure gain term**, `Vout = V_R·(4c − α)`
  `[calc]` — see §2.1 — so it pivots at `Vout = 0` and its lever is **|Vout|,
  max 7 V**.
- Ratio (`k`) drift pivots at `Vdac = V_ref = 2.5 V`, i.e. `Vout = +2.5 V`, lever
  `|Vdac − V_ref|` **max 2.25 V** `[calc]` — confirms `pitch-stage.md`.
- Offset terms have lever 1, at every pitch.

| # | Term | Arithmetic `[calc]` | Cents at **+7 V** | Cents at **+3 V** |
|---|---|---|---|---|
| 1 | **DAC internal reference, 5 ppm/°C max** | 5e-6 × 25 K = 125 ppm; × 7 V = 875 µV | **1.050** | 0.450 |
| 2 | LT5400 ratio tracking (0.2 ppm/°C) | 5 ppm × 2.25 V = 11.3 µV | 0.014 | 0.002 |
| 3 | `TRIM-GAIN` 200 Ω cermet @100 ppm/°C | 200×100e-6 = 0.02 Ω/°C on 10.2 kΩ = 1.96 ppm/°C; ×25 K = 49 ppm × 2.25 V = 110 µV | 0.132 | 0.015 |
| 4 | OPA2197 main amp Vos drift (max) | 2.5 µV/°C × noise gain 2 × 25 K = 125 µV | 0.150 | 0.150 |
| 5 | OPA2197 `VREFOUT` follower Vos drift | 2.5 µV/°C × 25 K × k(=1) = 62.5 µV | 0.075 | 0.075 |
| 6 | **`TRIM-OFFSET` network drift — uncounted anywhere in the repo** | ±50 mV adjustable portion, cermet vs metal-film mismatch ~150 ppm/°C × 25 K = 3750 ppm × 50 mV = 187 µV | **0.225** | 0.225 |
| 7 | DAC gain-error drift (est.) | 1 ppm/°C × 25 K = 25 ppm × 2·Vdac (9.5 V) = 238 µV | 0.285 | 0.165 |
| 8 | DAC zero-code drift (est.) | 1 µV/°C × 25 K × 2 = 50 µV | 0.060 | 0.060 |
| 9 | Resistor self-heating | see §2.6 — **625 µW max, shared die** | **< 0.01** | < 0.01 |
| 10 | INL residual after the 11-point table | ±4 LSB typ = 0.73 cents raw; ~1/3 between points | ~0.25 | ~0.25 |
| | **RSS** | | **≈ 1.2 cents** | **≈ 0.6 cents** |
| | **Arithmetic worst-case sum** | | **≈ 2.5 cents** | **≈ 1.4 cents** |

**Verdict: musically acceptable, with a large margin, and the module is not the
limiting term.** Justification, quantified:

- The usual just-noticeable difference for a sustained tone against a reference
  is ~5 cents `[from memory]`. The worst corner of this budget is half of that,
  at the extreme top of a nine-octave span that the instrument's 2.5–3 octave
  fingering never reaches `[repo]` ADR 0006.
- ADR 0006's own figure for a well-compensated analog VCO is **0.35 cents/K**
  `[repo]`, i.e. **8.75 cents over the same 25 K** `[calc]`. The VCO being
  driven drifts **7× the whole module** at the top of the range and **16× it**
  in the playing range. Spending more on this stage buys nothing audible.
- Raw INL before firmware correction is the one term that can exceed the ear:
  ±12 LSB max = 12 × 152.6 µV = 1.83 mV = **2.20 cents** `[calc]`. The 11-point
  NVS table is therefore load-bearing for the accuracy claim, not optional.

**Correction to the repo's stated numbers.** `pitch-stage.md` and ADR 0006 both
state the budget **"over 10 °C"** `[repo]`. A Eurorack case in a room is a
0–40 °C part. Simply rescaling to a 25 K excursion makes the dominant term
**2.5× larger** (0.42 → 1.05 cents) and it becomes 87 % of the RSS total. The
conclusion does not change; the number in the documents does.

**What the repo's budget leaves out** (items 6, 7, 8 above, plus self-heating,
which the brief asked for and which I have now bounded). None of them change the
verdict. Item 6 is the only one worth a design change — see F7.

---

## 1. RANKED FINDINGS

Confidence is my honest belief that the finding is real as stated.

| ID | Rank | Node / BOM ref | Finding | Conf. |
|---|---|---|---|---|
| **F1** | **Showstopper (as drawn)** | `CLR` net / `R-CLR-PU` | The schematic draws a **pull-DOWN** on the DAC's active-low `CLR`; the BOM specifies a pull-**UP**. As drawn, with the watchdog deleted, `CLR` is asserted forever and all six outputs are dead at 0 V | High |
| **F2** | **High** | DAC ch7 / `R-MODGAIN` | ADR 0006 says ch7 is **"written once at boot"**; `firmware/README.md` and `mod-channels.md` say refresh **all six every pass**. The once-at-boot reading is the exact latent failure that pins four jacks at +11.45 V after any `CLR` | High |
| **F3** | **High** | `R-OUT-PROT` | Stated worst case (192 mW) is **1.7× low**. Output-to-output against a 220 Ω source at **+10 V** (not −5 V) gives **322 mW**. The ≥500 mW spec survives at 1.55×, not 2.6× | High |
| **F4** | **High** | PITCH jack | Every plug insertion shorts tip to sleeve; the loop's DC feedback goes to zero and the op-amp rails. On plug seat the **destination sees ~+11.9 V for ~50–100 µs** (≈12 octaves). Repo calls this "a brief rail excursion" without the number or the destination | Med-High |
| **F5** | **Medium** | `C-FB-PITCH` | The drawing and one prose table say **1 nF**; the value table and BOM say **2.2 nF**. Q differs 0.61 vs 0.91, corner 9.1 vs 19.3 kHz. Neither produces the **12.2 kHz** both documents claim | High |
| **F6** | **Medium** | `C-FILT-PITCH` + `C-FB-PITCH` | The real closed-loop corner is **9.1 kHz**, *below* ADR 0006's own 10–20 kHz pitch window. The "−3 dB at 12.2 kHz, maximally flat" claim does not reproduce | High |
| **F7** | **Medium** | `TRIM-OFFSET` / `R-TRIM-RANGE` | Unbuildable as described (repo admits it) — and **it should be deleted, not fixed**. With α = 1 the residual is a *pure gain* error that firmware's affine already carries; deleting removes a part, the open `R-TRIM-RANGE` row, and the 0.225-cent drift term (budget item 6) | Med-High |
| **F8** | **Medium** | `TRIM-GAIN` | One turn of a 25-turn 200 Ω trimmer = 8 Ω = **0.08 % of ratio = 8× the entire LT5400 ratio error it exists to correct**. It is ~100× too coarse and its range is one-sided in the wrong direction. It only *adds* drift (budget item 3 is 10× item 2) | High |
| **F9** | **Medium** | `R-BIAS-DAC` | 100 kΩ against the DAC's 4 Ω Rout is a **−40 ppm, code-dependent** divider. **1 MΩ** — exactly the value the cited precedent `R-BIAS-INAMP` uses — makes it 4 ppm for free | High |
| **F10** | **Medium** | `C-AA-PITCH` | 10 nF × 1 kΩ contributes **~93 µs of settling to 1 cent**, more than the entire output stage, and the latency budget books **10 µs** for the whole pitch filter — ~20× under | High |
| **F11** | **Medium** | DAC ch7 write order / `R-LDAC` | "No write order avoids it" is true but misleading: **ch7-first bounds the exit-from-`CLR` excursion to −10.000 V (in range); ch7-last gives +11.45 V (clipped rail)**. A 21 V difference for one line of firmware | High |
| **F12** | **Medium** | PITCH power-on state | ADR 0006 justifies the C grade with "Pitch: below −2 V, subsonic, a VCO there is inaudible". The real power-on state is **0.000 V = the VCO's base note**, which `pitch-stage.md` states correctly. The *justification* for the grade lock is therefore stale even though the *choice* is right | High |
| **F13** | **Low** | `U-DAC` AVDD / LM317 | LM317 Vref is ±4 %; 1.20 V × (1 + 475/150) = **5.000 V worst case**, i.e. AVDD = DAC full scale, zero headroom. The "exactly ±10.000 V" mod claim evaporates there (≈ +9.92 V). 0.1 % divider resistors around a ±4 % reference is precision in the wrong place | Med-High |
| **F14** | **Low** | PITCH jack load floor | "gain 2.020000 for every load from open circuit to **2 kΩ**" is invalid at the top of the reserve: at **+7.5 V into 2 kΩ the op-amp is at the rail** `[calc]`. Floor is 2.03 kΩ at +7.5 V, 1.67 kΩ at +7 V | High |
| **F15** | **Low** | `pitch-stage.md` §"What limits accuracy" | The table is **textually corrupted** — two merged revisions, prose inside the table, and duplicate rows giving contradictory values for the same term (0.027 vs ~0.1 cents; 0.42 vs ~0.5 cents). There is no single coherent cents budget in the repo | High |
| **F16** | **Low** | `mod-channels.md` | An **unclosed parenthesis** opened at "*(The four-resistor version this replaced…" runs ~45 lines, burying *current* facts (the ±50.5 mV / ±18 cents-per-octave tolerance result) inside what reads as a historical aside | High |
| **F17** | **Note** | `mod-channels.md` "One buffer, four loads" | "At 2.5 V into 2.5 kΩ that is **1 mA**" is stale — V_ref is 3.3333 V. Real load is **signal-dependent: +1.333 mA source to −0.667 mA sink** `[calc]`. The buffer must sink; OPA2197 RRIO on ±12 V does | High |
| **F18** | **Note** | `mod-channels.md` drawing | `R1 10k`'s line does not reach the (−) input in the ASCII; `R-BIAS-DAC` and the DAC-side filter are absent from the drawing though the BOM populates them on all six DAC pins | High |
| **F19** | **Note** | `mod-channels.md` §"alternative topology" | The inverting alternative is called **"strictly better than what is drawn above"** and left unadopted, in a page headed "settled", and duplicated in two places. Its arithmetic checks out `[calc]`, and the pitch-side objection to inverting (§3) does *not* bite for mods | High |
| **F20** | **Note** | `mod-channels.md` §"Two resistors" | "a 1:3 ratio that **three sections of an LT5400 give directly against the fourth**" dangles an LT5400 for the mods, while the BOM builds them from `R-MODGAIN` discretes and `pitch-stage.md` states (correctly) that pitch + mods cannot share one quad | High |

---

## 2. THE PITCH STAGE, NODE BY NODE

### 2.1 Node `V_ref` — the reference tracking argument holds, for any trim setting

Let `V_R` = VREFOUT, `c` = code/65536, `α` = the `TRIM-OFFSET` divider ratio.
Gain-2 grade ⇒ `Vdac = 2·c·V_R`. With `k = R2/R1 = 1`:

```
Vout = Vdac(1+k) − k·V_ref = 2·(2 c V_R) − α V_R = V_R·(4c − α)        [calc]
```

`Vout ∝ V_R` **for every α**. So a reference drift is a pure gain term
regardless of where the offset trimmer sits, and trimming `V_ref` away from
2.500 V does *not* break the tracking. `pitch-stage.md`'s argument is correct
and is in fact stronger than the page claims. `[repo]` + `[calc]`

Cross-check of the page's own sensitivity table `[calc]`: offset 1 mV ⇒ 1.2
cents at both −2 V and +7 V ✓; gain 100 ppm ⇒ 100e-6 × 2 V = 200 µV = 0.24 cents
and 100e-6 × 7 V = 700 µV = 0.84 cents ✓. Both rows reproduce exactly.

### 2.2 Node (+) input — what the DAC actually sees, and why non-inverting is right

**DC:** `R-BIAS-DAC` 100 kΩ at the pin (50 µA at 5 V) and nothing else; OPA2197
input bias is picoamps `[from memory]`, so `R-OPAMP-IN` 1 kΩ carries no DC and
contributes **exactly zero gain error** — `pitch-stage.md` is right `[repo]`.

**AC:** 1 kΩ in series with `C-AA-PITCH` 10 nF to AGND. At 4 kHz,
|Z| = 1 k + 1/(2π·4e3·1e-8) = 1 k + 3.98 k ≈ 4.1 kΩ `[calc]` — inside the
DAC's 2 kΩ ∥ 3000 pF drive spec `[web]`. On a code step the 10 nF is
momentarily a short, so the DAC sees **1 kΩ**; a full-scale 4.5 V step demands
4.5 mA against a ±12 mA capability `[web]` — fine, but see §2.7 for what it
costs in settling.

**Is non-inverting the right topology?** **Yes, and for a reason the repo never
states.** In an inverting stage the DAC would drive the gain resistor directly,
so the DAC's output impedance adds to `R_in`. At 4 Ω on a 10 kΩ input that is
**400 ppm of gain error** — and because `R_out` varies with code and load, it is
a *nonlinearity*, not a trimmable gain error: 400 ppm × 9 V = 3.6 mV =
**4.3 cents of bow**, on top of INL and untouchable by a two-point trim `[calc]`.
The non-inverting form removes it entirely; the only residue is the
`R-BIAS-DAC` divider, 40 ppm at 100 kΩ (F9: 4 ppm at 1 MΩ).

Counter-checks, all benign `[calc]`:
- CMRR: input common mode swings 0.25→4.75 V = 4.5 V; OPA2197 CMRR ≥114 dB
  `[from memory]` ⇒ 4.5 × 2e-6 = 9 µV input-referred × 2 = 18 µV =
  **0.02 cents**, and it is a bow. Negligible — but only because the part runs
  on ±12 V; the same circuit on a single 5 V rail would not survive this.
- Intercept precision: the intercept is `k·V_ref` and depends on **no** DAC
  property, which is the second reason non-inverting wins here.

### 2.3 Loop stability at the jack tap — the claim is CORRECT; here is the proof

Ideal-op-amp closed-loop solve of the drawn network (`R_o` = `R-OUT-PROT` 1 kΩ,
`R1`=`R2`=10 kΩ, `C_f` = `C-FB-PITCH`, `C_J` = `C-FILT-PITCH` + cable, `R_L` =
patch load) `[calc]`:

```
V_jack        go(g1+g2) + s·C_f(go+g2)
────── = ────────────────────────────────────────
V_in      s²C_f C_J + s·C_f(go+gL+g2) + go·g2

DC gain = (g1+g2)/g2 = 1 + R2/R1 = 2.000   — independent of R_L, exactly ✓

f_n = (1/2π)·√( 1 / (R_o·R2·C_f·C_J) )
Q   = √( R_o·C_J / (R2·C_f) ) / (1 + R_o/R_L + R_o/R2)
```

The DC-gain result **confirms the page's load-independence claim exactly**, and
the Q expression **confirms the page's own `Q = √(R_eff·C_load/(R2·C_fb))`**
(the page omits the `(1 + R_o/R_L + R_o/R2)` damping denominator, which is a
10–110 % correction). `[repo]` + `[calc]`

**Loop gain.** Writing β = V_(−)/V_out(op-amp), including the op-amp's ~8 pF
input capacitance `[calc]`:

```
β(s) = [H(s)/R2 + s·C_f] / [1/R2 + 1/R1 + s·C_f + s·C_in]

zero at 1/(2π·R2·C_f)          = 7.09 kHz   (C_f = 2.2 nF, R2+trim = 10.2 k)
pole at 1/(2π·(R1∥R2)·C_f)     = 14.33 kHz  (R1∥R2 = 5.05 kΩ)
β(∞)  = C_f/(C_f + C_in)       = 2200/2208 = 0.9964
```

β rises 0.5 → ~1.0 between 7.1 and 14.3 kHz: **a lead**, adding phase margin, as
the page says. Crossover is therefore at ≈ **10 MHz with β ≈ 1**, i.e. the stage
crosses over as a unity-gain follower, and **phase margin ≈ the OPA2197's native
unity-gain figure, ~60°** `[calc]` + `[from memory]`.

Two things make this robust that the repo does not say:

1. **The classic C_f/C_in pole does not exist**, because `C_f` (2.2 nF) is 275×
   `C_in`; at HF the (−) node is a flat capacitive divider of 0.9964, not a
   rolloff `[calc]`. (ADR 0006 cites four surveyed designs using **18–22 pF**
   for this job `[repo]`; at 22 pF against 8 pF the HF β is 0.73 and there *is*
   a real β pole at ~1.05 MHz. It still lands as a lead at these resistor
   values, so the precedent is not wrong — but it is being cited across a 100×
   change in C without anyone checking. Note-level.)
2. **The op-amp never sees a bare capacitive load** — the OPA2197 is specified
   for only 1 nF direct `[web]`. `C_f` presents 2.2 nF **in series with
   R1∥R2 = 5.05 kΩ**, so at 10 MHz the branch is ~5 kΩ; `C_J` is behind
   `R-OUT-PROT`, so that branch is ~1 kΩ. Total load at crossover ≈ 833 Ω
   `[calc]` — resistive, and inside the part's drive. ✓

**Load-case table** (C_f = 2.2 nF, C_J = 10 nF + cable) `[calc]`:

| Load at the PITCH jack | C_J | R_L | f_n | **Q** | Step overshoot |
|---|---|---|---|---|---|
| **Nothing plugged in** | 10 nF | ∞ | 10.73 kHz | **0.613** | 1.2 % |
| One 100 kΩ VCO, 2 m ≈ 200 pF | 10.2 nF | 100 k | 10.63 kHz | **0.613** | 1.2 % |
| Three VCOs multed (33 kΩ), 200 pF | 10.2 nF | 33.3 k | 10.63 kHz | **0.603** | 1.1 % |
| Four destinations, 800 pF | 10.8 nF | 25 k | 10.32 kHz | **0.615** | 1.3 % |
| Multed to Woody's MOD jack (82 nF ∥ 1 kΩ) | 92 nF | 1 k | 3.54 kHz | **0.974** | **15.3 %** |
| Multed to Woody's BREATH jack (330 nF ∥ 1 kΩ) | 340 nF | 1 k | 1.84 kHz | **1.872** | **41.9 %** |
| Bare 82 nF (no series R) | 92 nF | ∞ | 3.54 kHz | **1.859** | **41.6 %** |
| Jack shorted | — | 0 | — | **no DC loop; amp rails** | — |

**Answers to the brief, directly:**

- **100 kΩ VCO:** no effect. Q 0.613, identical to open circuit.
- **Three VCOs multed:** no effect. Q 0.603.
- **2 m cable at ~200 pF:** no effect — and here is the real reason, which the
  repo's β(∞)=1 argument does not capture: **`C-FILT-PITCH`'s 10 nF is 50× the
  cable**, so 200 pF is a **2 %** perturbation of the jack node, and 800 pF is
  8 % `[calc]`. Cable capacitance is not merely "structurally incapable of
  putting lag in the loop" — it is **numerically invisible next to the part the
  design already fits there**. This is a stronger defence and it should be the
  one written down.
- **Nothing plugged in:** **the best-behaved case of all**, Q = 0.613, no
  peaking, ~60° phase margin. It is not a risk case.
- **Does 2.2 nF actually compensate it?** Yes — see the β analysis. It is not
  doing classic phase-lead compensation; it is making the *noise gain fall from
  2 to 1* before `R-OUT-PROT`'s pole matters, so the loop crosses over as a
  follower.
- **Does it interact with `C-FILT-PITCH`?** Yes, and productively: the two set
  the closed-loop 2nd-order pair `f_n` and `Q` together (F6). `C_f` damps `C_J`;
  the damping ratio is `ζ = ½·√(R2·C_f/(R_o·C_J))·(1+R_o/R2)`. They are a pair,
  not two independent filters, and neither document says so.
- **`C-FB-PITCH` across `R2` instead** (the error the page warns about): I did
  not re-derive the 18°/<10° figures, but the mechanism is right — that
  connection leaves `R_o` and `C_J` inside the loop at *all* frequencies, and
  `β(∞)` then falls as `C_J` rises rather than going to 1. The warning is sound.

**The genuine exposure is ringing, and the repo's own numbers are pessimistic
for the case they name.** The 44–67 % figures assume a *bare* capacitance. Woody's
own MOD/BREATH jacks present C **in parallel with their 1 kΩ** `R-OUT-PROT`,
which damps them: MOD falls to **15.3 %** overshoot (≈180 cents on an octave
step, decaying with τ = 1/(ζω_n) = 88 µs) and BREATH to **41.9 %** (≈500 cents,
τ = 324 µs — a ~1 ms audible chirp) `[calc]`. The true 44 %+ case is a *passive*
destination presenting ≥50 nF of undamped capacitance, which is unusual. **The
warning stands for BREATH and should be softened for MOD.**

### 2.4 Node PITCH jack, shorted — F4, quantified

With `R_L` = 0, the DC feedback term is `H/R2 = 0`, so β(0) = 0: **there is no
DC loop and the op-amp saturates** `[calc]` — the page is right. Consequences:

- `R-OUT-PROT` dissipates 11.9²/1000 = **142 mW** `[calc]` ✓ matches BOM.
- **On plug seat**, the short opens while the destination is already connected.
  The jack rises toward the railed op-amp output through `R_o`·`C_J`,
  τ = 1 kΩ × 10 nF = **10 µs**, while the loop recovers over
  ~7/(ζω_n) ≈ 130 µs `[calc]`. **The destination sees ≈ +11.9 V for roughly
  50–100 µs on every insertion** — about 12 octaves. Not damaging to a 100 kΩ
  VCO input, but it is an audible click/chirp on every patch, it did not exist
  with op-amp-side feedback, and neither document states the voltage or that the
  *downstream module* is what sees it.
- Mitigation if E9 finds it objectionable: a small Schottky or a series diode is
  the wrong answer (leakage into the feedback node). The clean answer is a
  **DC-coupled feedback path that survives a short** — e.g. a second, high-value
  resistor (1 MΩ) from the op-amp output to the (−) node, which restores a
  finite DC β with the jack shorted (β = R1/(R1+1M) ≈ 1 % ⇒ the op-amp parks
  near 2·Vdac·100 rather than at the rail… no: it still rails, but through a
  known path). Realistically: accept it, and make it an E9 measurement with the
  oscilloscope on the *destination* side.

### 2.5 `TRIM-GAIN` — F8, and the case for deleting it

- Nominal `k` = 1.0000 from the LT5400, to **±0.01 %** (A grade) `[web]`.
- `TRIM-GAIN` 200 Ω in series with `R2` gives `k` = 1.0000 → 1.0200 — **entirely
  one-sided, upward** `[repo]` `[calc]`.
- The error it must correct is two-sided and centred near zero. The `R-BIAS-DAC`
  divider alone puts the *effective* slope at 2 × (1 − 40 ppm) = 1.99992
  `[calc]` — i.e. **low**, in the direction the trimmer cannot reach.
- **Resolution:** a 25-turn 200 Ω trimmer is 8 Ω/turn = **0.08 % of the ratio
  per turn**, against an LT5400 ratio error of 0.01 %. One turn is **8× the
  entire error** `[calc]`. It cannot be set to better than the part it is
  correcting.
- **Cost:** budget item 3 (0.132 cents) is **10× item 2** (0.014 cents). The
  trimmer contributes an order of magnitude more drift than the $8 network it
  sits in series with.

**Recommendation: delete `TRIM-GAIN`, strap the `R2` leg direct, and let
firmware's per-load affine `(gain, offset)` pair carry the whole correction.**
ADR 0006 already retracted both original justifications for the trimmers `[repo]`
and already records that **zero** of eight surveyed DAC-driven designs uses a
trimmer `[repo]`. This removes budget item 3, removes the two-terminal-trimmer
fail-open footprint question the page lists as open, and removes the "gain still
touches offset" coupling from the trim procedure.

### 2.6 Resistor self-heating — bounded, and it is a non-issue

The brief asked for this explicitly `[calc]`:

- Feedback-divider current at the extremes: `I = (V_jack − V_ref)/(R1+R2+trim)`.
  At V_jack = +7.5 V: (7.5 − 2.5)/20.2 k = **247.5 µA**. At −2.5 V: −247.5 µA.
- P(R2 = 10.2 k) = 247.5e-6² × 10200 = **625 µW**; P(R1 = 10 k) = 613 µW.
- The power is **symmetric about V_jack = +2.5 V** and maximal at both extremes,
  so the differential between R1 and R2 never exceeds **12 µW**.
- Both resistors are **on one LT5400 die** `[web]`, so common-mode self-heating
  cancels in the ratio by construction. Even taking a pessimistic 200 °C/W per
  element, 12 µW is **2.4 mK** of differential rise `[calc]` ⇒ at 0.2 ppm/°C,
  **0.5 ppb of ratio**. Zero.
- `TRIM-GAIN` at 247.5 µA dissipates 247.5e-6² × 200 = **12 µW** `[calc]`.
- **`R-OUT-PROT` is the one place self-heating could have mattered — 142 mW when
  shorted, ~50 mW at +7 V into 100 kΩ — and the jack-side tap puts it inside the
  DC loop, where its value and therefore its temperature are irrelevant** to
  accuracy `[calc]`. That is an unstated *win* of the topology, and it is worth
  having in the page.

**Self-heating contributes < 0.01 cents anywhere in this stage. It is not a term
in the budget.**

### 2.7 Settling — F10

Update period 250 µs at 4 kHz; SPI burst = six 32-bit words at 2 MHz = **96 µs**
`[repo]` latency-budget, confirmed `[calc]`.

Pitch chain, settling to **1 cent = 0.833 mV at the jack** `[calc]`:

| Stage | Time constant | Full-scale (4.5 V) step | One-octave (1 V) step |
|---|---|---|---|
| DAC8568 internal | 5 µs typ `[web]` | 5 µs | 5 µs |
| `R-OPAMP-IN`·`C-AA-PITCH` | 1 kΩ × 10 nF = **10 µs** | ln(4500/0.417)·10 = **93 µs** | ln(500/0.417)·10 = **71 µs** |
| Output 2nd order (f_n 10.73 kHz, ζ 0.816) | 1/(ζω_n) = **18.1 µs** | ~145 µs | **129 µs** |
| **Total** | | **≈ 243 µs** | **≈ 205 µs** |
| Same, to **5 cents** | | ≈ 175 µs | ≈ **159 µs** |

Against `docs/reference/latency-budget.md`, which books **"Pitch filter
(~10–20 kHz corner) | ~10 µs"** and "DAC settling ~10 µs" `[repo]` — that is
`1/(2πf)`, a time *constant*, not a settling time. **The analog pitch path is
under-booked by roughly 20×.** It does not break anything (200 µs is far below
the ms-scale key/debounce path and below the ~5 ms of perceptual pitch onset
`[from memory]`), but "notes land instantly" rests on a number that is not a
settling time, and E9's "scope a commanded step" row should be judged against
~200 µs, not ~10 µs.

**`C-AA-PITCH` is the dominant term and the cheapest to fix.** It filters a DAC
whose glitch impulse is ~0.1 nV·s `[from memory]`, and the output stage's 9.1 kHz
pole already does the reconstruction work. **1 nF** gives 159 kHz and 9.3 µs
(settling falls to ~140 µs); **2.2 nF** gives 72 kHz and 22 µs. The cost is less
attenuation of SPI hash in the 100 kHz–1 MHz decade — which `C-FILT-PITCH` at
the connector also covers. Recommend 1–2.2 nF, decided at E9 with the scope.

Mod channels `[calc]`: DAC 5 µs, then `R-OUT-PROT`·`C-FILT-MOD` = 1 kΩ × 82 nF =
82 µs **outside** the loop. To 0.1 % of a 20 V step: 6.9 τ = **566 µs = 2.3
update periods**. That is the intended 1.94 kHz behaviour `[repo]` ADR 0006 and
is fine for 400 Hz sources, but it should be stated: **a mod channel's effective
step response is half a millisecond**, and no firmware slew setting can make it
faster.

---

## 3. THE MOD CHANNELS, NODE BY NODE

### 3.1 `R-MODGAIN` — k = 3, V_ref, and the endpoints all reproduce

`[calc]`, all confirming `mod-channels.md`:

```
k = R2/R1 = 30k/10k = 3            gain = 1 + k = 4.000 exactly
Vout = 4·Vdac − 3·V_ref            V_ref = 3.3333 V  ⇒  3·V_ref = 9.9999 V
Vdac = 0.000 V  →  −9.9999 V
Vdac = 2.500 V  →   0.0001 V
Vdac = 5.000 V  →  +10.0001 V
```

**Code granularity check, which nobody has done** `[calc]`: 3.3333 V on a 5.000 V
16-bit scale is code 3.3333/5 × 65536 = 43690.2. Code 43690 ⇒ 3.333282 V ⇒
intercept 9.99985 V; code **43691** ⇒ 3.333359 V ⇒ intercept **10.00008 V**.
Either lands within **150 µV of ±10.000 V**. Use 43691. The "exactly ±10.000 V"
claim survives quantisation.

**Tolerance table re-derived** `[calc]`, confirming the page exactly:
k with ±1 % parts spans 3 × 0.99/1.01 = 2.9406 to 3 × 1.01/0.99 = 3.0606.
Zero point `Vout(2.5) = 2.5 − k(0.8333)`: at k = 3.0606 ⇒ **−50.5 mV** ✓.
Span `= 5(1+k)`: **19.703 – 20.303 V** ✓. Endpoints at worst k: **−10.202 V /
+10.101 V**, both inside the ~±11.45 V swing `[calc]`.

The page's **±18 cents/octave if a channel is used for something pitch-like** is
the right warning and is currently buried inside the unclosed parenthesis (F16).

### 3.2 DAC ch7 as the shared bipolar reference — the coupling answer

**Does it couple channel-to-channel? Yes, in four distinct ways, three of which
are negligible and one of which is not.**

| Mechanism | Magnitude `[calc]` | Verdict |
|---|---|---|
| Shared buffer output impedance | Load is signal-dependent: each `R1` carries (3.3333 − Vdac)/10 k, i.e. **+333 µA to −167 µA per channel**, total **+1.333 mA / −0.667 mA**. OPA2197 closed-loop Zout ≈ Zo/(1+T) ≈ 0.1 Ω at 10 kHz ⇒ 333 µA × 0.1 Ω = 33 µV on V_ref, ×3 = **100 µV on the other three outputs = 10 ppm of ±10 V** | Negligible — say so and stop worrying |
| DAC internal DC crosstalk | ≤ a few LSB ⇒ 3 × 76 µV × 3 = **~0.7 mV = 35 ppm** `[from memory]` | Negligible |
| Digital feedthrough on ch7 refreshes | ~0.1–0.3 nV·s per frame `[from memory]`, ×3, **correlated across all four jacks** rather than independent | Note — matters only if two mods drive one destination |
| **Single-point-of-failure amplification** | A one-bit SPI error in ch7's **MSB** moves V_ref by 2.5 V ⇒ **all four mod outputs move −7.5 V simultaneously** (into clip). The same error in a signal channel moves **one** output by 10 V | **This is the real coupling.** ch7 is a 4×-amplified fault node |

The last row is why **F2 matters**: the fault self-heals in ≤250 µs *if and only
if ch7 is refreshed every pass*. ADR 0006's update-rate table says **"Mod offset
| written once at boot"** `[repo]`; `firmware/README.md` says refresh all six
every pass and explicitly names the once-at-boot reading as the bug `[repo]`;
`mod-channels.md` cites the statelessness rule as the fix `[repo]`. **Two of
three documents are right and the ADR — the one with "Accepted" status — is
wrong.** Fix the ADR table, not the firmware.

**Positive finding, unstated:** because V_ref comes from a DAC channel and the
DAC's full scale is 2 × VREFOUT, `Vout = V_R(16c_sig − 12c_ref)` `[calc]` — so
reference drift on the mods is a **pure gain term too**, exactly as on pitch,
and the mods inherit the tracking property for free. Worth one line in the page.

### 3.3 `CLR`, power-on, and the grade suffix — the logic is CORRECT

Confirmed against TI `[web]`: **A/B = gain 1, C/D = gain 2; A/C reset to zero
scale, B/D to midscale; internal reference disabled by default on all grades.**
`hardware/bom.csv` row `U-DAC` and ADR 0006 both state this correctly and the
BOM's "CONFIRM the gain/grade mapping against SBAS430" is now **confirmed**.
`DAC8568CIPW` is the right part.

State table, re-derived `[calc]`:

| State | VREFOUT | ch1 | ch7 | **PITCH jack** | **MOD jacks** |
|---|---|---|---|---|---|
| Rack power-on, before any write | **0 V (ref disabled)** | 0 | 0 | **0.000 V** | **0.000 V** |
| After ref enable, before data | 2.500 V | 0 | 0 | **−2.500 V** | 0.000 V |
| Manual `CLR` (clear-code default) | 2.500 V | 0 | 0 | **−2.500 V** | 0.000 V |
| If a **B/D** part were fitted | 2.500 V | 32768 | 32768 | **+2.500 V** (4.5 oct up) | **+2.500 V** |
| ch7 stale at 0 after `CLR`, signals refreshed | 2.500 V | — | 0 | — | **4·Vdac → clips at +11.45 V** |
| ch7 stale at **2.500 V** (pre-redraw value) | 2.500 V | — | — | — | **−7.5 … +12.5 V, clips positive** `[repo]` firmware README, ✓ `[calc]` |

Three observations:

1. **F12.** ADR 0006's power-on table says "Pitch | below −2 V | Subsonic. A VCO
   there is inaudible" `[repo]`. The true state is **0.000 V — a VCO's base
   note, audible** — as `pitch-stage.md` correctly states `[repo]`. The grade
   choice is still right (for the mods and for reference gain), but its stated
   pitch justification is false and the ADR should be corrected.
2. **F11.** `LDAC` is tied inactive `[repo]` `R-LDAC`, so the six channels
   update serially ~16 µs apart. The BOM says "no write order avoids it"
   `[repo]`. True, but **which** intermediate values appear is entirely a write-
   order choice: **ch7 first** ⇒ the mods sit at **−10.000 V** (an in-range
   output) for the ~80 µs until the signal channels land; **ch7 last** ⇒ they
   sit at **4·Vdac ≈ +11.45 V, clipped**, for the same window `[calc]`. A 21 V
   difference for one line of firmware. Partially mitigated at the jack by
   `C-FILT-MOD`: τ = 1 kΩ × 82 nF = 82 µs, so an 80 µs excursion reaches only
   ~62 % of its value at the connector `[calc]`.
3. **F1 — the showstopper.** `hardware/module/digital-and-supervision.md` draws
   `[R-CLR-PD 10k]` from `CLR` to **AGND** `[repo]`, while `hardware/bom.csv`
   row 67 specifies `R-CLR-PU`, "Pull-up holding the DAC8568 `CLR` **inactive**"
   `[repo]`. `CLR` is **active low** `[web]`. With the 74HC123 deleted, a
   pull-down leaves `CLR` **permanently asserted**: every DAC channel latched at
   zero scale, PITCH at −2.500 V, all four MODs at 0 V, and no SPI write can
   ever change them. That is a dead module that looks like a firmware fault.
   The drawing on that page is stale in three ways (it still shows the deleted
   monostable and the deleted presence comparator) and its own prose disowns it
   — but this project's stated rule is that **"prose is what a layout gets built
   from"** `[repo]` `pitch-stage.md`, and the schematic page *is* the artifact a
   layout is built from. **Redraw the `CLR` net before layout.**

### 3.4 Output protection, drive and short-circuit — all six channels

`[calc]`, solving the divider at each fault:

| Case | Jack voltage | I through `R-OUT-PROT` | **P in `R-OUT-PROT`** |
|---|---|---|---|
| **MOD** shorted to ground (op-amp holds +10.1 V) | 0 V | 10.1 mA | **102 mW** ✓ matches BOM's 101 mW |
| **PITCH** shorted (loop broken, op-amp rails +11.9 V) | 0 V | 11.9 mA | **142 mW** ✓ matches BOM |
| **PITCH** vs 220 Ω source at **−5 V** (BOM's stated worst case) | −1.952 V | 13.85 mA | **192 mW** ✓ matches BOM |
| **PITCH** vs 220 Ω source at **+10 V** | +6.05 V (op-amp rails −11.9 V) | 17.95 mA | **322 mW** ← F3 |
| **PITCH** vs 220 Ω source at **−10 V** | −6.05 V | 17.95 mA | **322 mW** |
| **MOD** vs 220 Ω source at **−10 V** | −6.375 V | 16.48 mA | **272 mW** |

**F3:** the BOM picked −5 V arbitrarily; the symmetric ±10 V cases are **1.7×
worse at 322 mW**. `R-OUT-PROT` is a common row (qty 6) so the ≥500 mW spec
covers all of them — **at 1.55× margin, not the 2.6× the BOM's number implies**,
and a "value engineering" step back to a 250 mW 1206 would be a **1.3×
overload**. Keep ≥500 mW and correct the stated worst case, because the number
is what a future reviewer will check the part against.

Other protection checks `[calc]`:

- **Op-amp output current.** Worst of the above is 17.95 mA sourced/sunk against
  OPA2197's ±65 mA `[web]`. Peak transient on a mod 20 V step into 1 kΩ + 82 nF
  is 20 mA `[calc]`. Comfortable. Pitch's steady load is the 20.2 kΩ feedback
  network plus the patch: at +7.5 V into three multed 100 kΩ, 248 + 225 µA
  ⇒ op-amp output at 7.5 + 0.473 = **7.97 V**, well inside ±11.45 V `[calc]`.
- **`D-JACK-CLAMP` BAV99 on the driver side.** Unpowered-module back-drive:
  (10 − 0.7)/(220 + 1000) = **7.6 mA/jack** `[calc]` ✓ matches BOM; 45.6 mA
  across six, against BAV99's ~215 mA continuous rating `[from memory]`. Fine.
  On **pitch** the clamp sits at the op-amp output, which with the jack tap is
  **inside** the DC loop, so its leakage is absorbed and the BOM's
  "identically zero" claim holds `[calc]` ✓.
- **F14 — the pitch load floor.** For V_jack = +7.5 V the op-amp must reach
  7.5(1 + 1k/R_L) + 0.248 ≤ 11.45 ⇒ **R_L ≥ 2.03 kΩ** `[calc]`. The page's
  "every load from open circuit to 2 kΩ" is therefore *exactly on the boundary*
  and invalid at the top of the ±600-cent reserve. At the specified +7 V ceiling
  the floor is 1.67 kΩ. Restate as "≥ 3 kΩ" and it is unambiguous.
- **Output-to-output musical consequence, unstated.** PITCH multed to a MOD
  output at −10 V: the jack settles at (11.9 − 10)/2 = **+0.95 V** while pitch
  is commanding +7 V `[calc]` — **six volts, seven octaves wrong**, because the
  jack-side loop *fights* the other module instead of averaging with it. With
  op-amp-side feedback the same mistake would have been a benign midpoint. The
  BOM records the wattage of this case but not what it sounds like.

### 3.5 `V_ref` buffer and `R-OPAMP-IN` — F17, F18

- **F17:** "At 2.5 V into 2.5 kΩ that is 1 mA" `[repo]` is stale (V_ref is
  3.3333 V) and models the wrong load. The far end of each `R1` is the (−) node,
  which sits at `Vdac` (0–5 V), so the buffer's load is **signal-dependent and
  bidirectional: +1.333 mA to −0.667 mA** `[calc]`. The drawing's "~1.3 mA" is
  the right number for the wrong reason. The buffer must **sink**; OPA2197 RRIO
  on ±12 V does, so no change — but state it, because someone will size a
  single-supply part off that sentence.
- **F18:** the mod drawing's `R1 10k` line never reaches the (−) input, and
  `R-BIAS-DAC` (BOM qty 6, "at every DAC output pin") appears on neither
  drawing. Both are drawing defects on pages this project treats as normative.
- `R-OPAMP-IN` qty 7 is correct and its "no gain error on a (+) input" reasoning
  is right `[repo]` `[calc]`.

### 3.6 The inverting alternative — F19

`mod-channels.md` states it twice and calls it **"strictly better than what is
drawn above"** while leaving it unadopted in a page headed "settled" `[repo]`.
Its arithmetic checks out `[calc]`: `Vout = −4·Vdac + 5·V+`, V+ = 2.000 V ⇒
+10 V at Vdac = 0, −10 V at Vdac = 5; on `CLR` both terms are zero ⇒ 0 V ✓.
Two things the page does not say:

1. **The pitch-side objection to inverting does not bite here.** In an inverting
   stage the DAC drives the 10 kΩ input resistor, so the DAC's 4 Ω output
   impedance is 400 ppm of the gain and code-dependent `[calc]`. On pitch that
   is 4.3 cents of untrimmable bow (§2.2). On a mod channel it is **8 mV on
   20 V** — a fifth of one 1 % resistor's contribution. Irrelevant.
2. **It genuinely returns an op-amp half**, because one DAC pin can drive four
   (+) inputs directly (each draws picoamps) `[calc]` — four `R-OPAMP-IN` in
   parallel still carry no DC. That takes `U-OPA-PITCH` from ten halves used to
   nine, i.e. three spare.

**Either adopt it or delete the section.** A "settled" page that names a better
alternative twice and declines to take it will be re-litigated by the next
reader, which is exactly what this review is evidence of.

---

## 4. SPECIFIC CORRECTIONS TO REPO TEXT

| File / ref | Says | Should say | `[calc]` |
|---|---|---|---|
| `pitch-stage.md` drawing line 29 | `C-FB-PITCH 1nF` | **2.2 nF** (or resolve the other way) | F5 |
| `pitch-stage.md` split-loop table | "`C-FB-PITCH` 1 nF from the op-amp output" | **2.2 nF** | F5 |
| `pitch-stage.md`, `bom.csv` `C-FB-PITCH` | "maximally flat: −3 dB at **12.2 kHz**" | **9.1 kHz**, Q = 0.613, f_n = 10.73 kHz. (At 1 nF: 19.3 kHz, Q = 0.909, +0.74 dB peak) | F6 |
| `pitch-stage.md` §"What limits accuracy" | corrupted, duplicate contradictory rows | one table; use §0 above | F15 |
| `pitch-stage.md`, ADR 0006 | budget "over 10 °C" | over **0–40 °C**, ΔT = 25 K from calibration ⇒ reference term **1.05 cents**, not 0.42 | §0 |
| `pitch-stage.md` | "The feedback network is a **lead** at every passive load tried — … **dead short**" | At a dead short there is no DC loop at all and the amp saturates; "lead" is not a meaningful statement about that case | §2.4 |
| `pitch-stage.md` | "gain 2.020000 for every load from open circuit to **2 kΩ**" | valid to ~**3 kΩ**; at 2 kΩ and +7.5 V the op-amp is at the rail | F14 |
| `pitch-stage.md` | "joining PITCH to the MOD (82 nF) … gives **44–67 %** overshoot" | MOD: **15.3 %** (the 1 kΩ damps it). BREATH: **41.9 %**. Bare 82 nF with no series R: 41.6 % | §2.3 |
| `mod-channels.md` | "At 2.5 V into 2.5 kΩ that is **1 mA**" | **+1.333 mA source / −0.667 mA sink**, signal-dependent | F17 |
| `mod-channels.md` | unclosed `*(` spanning ~45 lines | close it; lift the tolerance table out | F16 |
| ADR 0006 update-rate table | "Mod offset \| **written once at boot**" | **refreshed every pass**, per `firmware/README.md` | F2 |
| ADR 0006 power-on table | "Pitch \| below −2 V \| Subsonic" | **0.000 V — the VCO's base note** | F12 |
| `bom.csv` `R-OUT-PROT` | worst case "**192 mW**" | **322 mW** | F3 |
| `bom.csv` `U-DAC` | "CONFIRM the gain/grade mapping against SBAS430" | **Confirmed** `[web]`: A/B gain 1, C/D gain 2; A/C zero-scale reset, B/D midscale; internal ref disabled by default on all grades | §3.3 |
| `digital-and-supervision.md` drawing | `[R-CLR-PD 10k]` to AGND | **pull-UP** to the 5.21 V rail (`R-CLR-PU`, per BOM) | F1 |
| `latency-budget.md` | "Pitch filter ~10 µs" | **~160 µs to 5 cents, ~205 µs to 1 cent** on an octave step | F10 |

---

## 5. WHAT I COULD NOT SETTLE

- **ti.com, analog.com, bdtic.com and datasheet.octopart.com are all blocked by
  the egress proxy** (EGRESS_BLOCKED on every attempt). Everything marked
  `[web]` above came from search-result summaries of those documents, not from
  the PDFs. **Take the following off the real datasheets before layout:**
  DAC8568 INL/DNL limits, zero-code and full-scale error drift, glitch impulse,
  DC crosstalk, and output swing vs AVDD with load; OPA2197 short-circuit
  current and its `A_OL`/`Zo` curves; the LT5400 **option suffix** for a 1:1
  quad in MS8 (still the genuinely open item `[repo]`) and its A-grade matching
  drift limit (0.2 vs 1 ppm/°C changes budget item 2 by 5×, from 0.014 to 0.068
  cents — which is still negligible, so this one does not gate anything).
- **DAC8568 reference mode (static vs flexible).** `[from memory]`, the part
  has both; in flexible mode the reference powers down with the DACs. Which
  mode the enable write selects determines whether the sticky-register refresh
  in `firmware/README.md` is sufficient. Confirm against SBAS430.
- I did not re-derive the 18° / <10° phase-margin figures for the
  "cap across R2" error case; the mechanism is right and the conclusion is not
  in doubt, but those specific numbers remain unverified.

---

## 6. IF YOU CHANGE THREE THINGS

1. **Fix the `CLR` net on the drawing (F1).** Everything else here is a
   refinement; this one is the difference between a board that works and a board
   that measures 0 V on six jacks.
2. **Make ADR 0006 agree with `firmware/README.md` about ch7 (F2)**, and write
   ch7 **first** in the burst (F11). Two text edits; they close a four-jack
   rail-pin failure and bound the exit-from-`CLR` excursion by 21 V.
3. **Delete both trimmers (F7, F8).** `TRIM-OFFSET` is unbuildable and
   contributes the second-largest drift term in the budget; `TRIM-GAIN` is 8×
   too coarse to resolve the part it corrects and contributes 10× the LT5400's
   drift. Both authorities already exist in firmware's affine pair, which
   ADR 0006 already put there. This deletes two through-hole parts, the open
   `R-TRIM-RANGE` row, the fail-open footprint question, the two-trim iteration
   procedure, and 0.36 cents of the budget — and it brings the module into line
   with **all eight** DAC-driven designs the project itself surveyed.

**And the headline stands: the pitch channel is good to ~1.2 cents RSS over
0–40 °C at the top of a nine-octave range, ~0.6 cents in the playing range,
against a VCO that drifts 8.75 cents over the same span. The static accuracy
problem is solved. The remaining risk in this module is transient — insertion
excursions, exit-from-`CLR` excursions, and ringing into undamped capacitive
mults — and every one of those is a measurement at E9, not a component choice.**
