# C2 — Breaking the breath signal path

**Falsification pass, 2026-09-21.** Cold: `docs/review/**` and `docs/research/**`
were not read. Sources are `hardware/controller/carrier.md` §1–2,
`hardware/module/breath-receive-stage.md`, `hardware/module/breath-output-stage.md`,
`docs/decisions/0003`, `docs/decisions/0004`, `docs/decisions/0006`,
`hardware/bom.csv`, plus two datasheet lookups.

Every claim is marked `[repo] <file>`, `[calc]`, `[web] <url>` or `[from memory]`.

---

## 0. The unit, and the transfer function everything below uses

`[calc]`, from `[repo] carrier.md` §2 Derivations and `[repo] breath-receive-stage.md`:

```
sensor (ratiometric, VS = 5.000 V):  Vout = 5 × (0.1533·P + 0.04) = 0.766 V/kPa + Voff
real playing tops at 2.8 kPa      →  sensor swing = 2.145 V          [repo] 0003
bias/series loading                   1M/(1M+11k)          = 0.98912
in-amp                                G = 1 + 50k/42.2k    = 2.1848  → effective 2.1612
downstream, commissioned              −(R-FB/R-IN)·a = 4.02·a, a = 0.537 → 2.157
TOTAL sensor → jack                   2.1612 × 2.157       = 4.662 V/V
                                      2.145 V × 4.662      = 10.00 V at the jack ✓
```

**The count.** `[repo] carrier.md` §2 puts the playable ADC span at **1594 counts
of 4096**. The same 0–2.8 kPa is 10 V at the jack. So throughout this document:

```
1 breath count = 10 V / 1594 = 6.274 mV at the jack = 1.346 mV at the sensor
```

**The pedestal is not 0.200 V.** `[web]` The MPXV4006 `Voff` is **min 0.152 V,
typ 0.265 V, max 0.378 V**
([nxp.com/docs/en/data-sheet/MPXV4006.pdf](https://www.nxp.com/docs/en/data-sheet/MPXV4006.pdf),
via search snippet; the PDF itself is proxy-blocked). The repo uses 0.200 V —
the *transfer function's* nominal intercept (`0.04 × 5 V`), not the part's
specified typical. `[repo] breath-receive-stage.md` says "+0.437 V nulls a
*typical* +0.200 V pedestal"; a typical part actually needs
`0.265 × 2.1612 = 0.573 V` `[calc]`. The **trimmer range conclusion is
unaffected and vindicated** — see N-REF-1 for where it does bite.

---

## Index of findings, by node

| ID | Node / BOM ref | Finding | Verdict |
|---|---|---|---|
| **N-AGND-1** | `J-UMB` pin 2 | AGND's current is ≤65 nA and *structurally* capped at 11.9 µA by `R-BIAS-INAMP` | claim's premise **SURVIVES** |
| **N-AGND-2** | `J-UMB` pin 2 / pin 6 | "…which is what makes the 2 m run work" misattributes the mechanism by 3600× | **BROKEN** |
| **N-AGND-3** | `C-FILT-BREATH` | No tolerance in the BOM; ±5 % costs 20 dB of AC CMRR. Also: receive page's "46 dB at 100 Hz" is a 1 kHz number | **BROKEN** (arithmetic), cost 0.09 counts |
| **N-AGND-4** | `CABLE-UMB` | 0.168 Ω is optimistic by up to 2×; contact resistance unbounded over life | matters only in N-INP-1 |
| **N-INM-1** | `INA828` IN− | Open BREATH parks the jack at **−1.24 V**, not 0 V | **BROKEN** |
| **N-INP-1** | `INA828` IN+ | Open AGND leaves the instrument **fully playable** with 44 counts of light-show wobble — the exact failure ADR 0003 exists to prevent | **BROKEN**, worst case in the set |
| **N-JACK-1** | `J-UMB` unplugged | Module standalone rests at **−1.24 V + offset**, i.e. anywhere in −6.15…+3.80 V. ADR 0006 promises 0 V | **BROKEN** |
| **N-INM-2** | BREATH↔+12 V | Jack pinned at **+11.45 V**, unreducible by either knob, no damage | **BROKEN** (stuck full-scale) |
| **N-PIN-1** | `J-UMB` pin map | The pin map makes the isolated BREATH↔+12 V short nearly unreachable — undocumented protection | **SURVIVES**, credit due |
| **N-SENSE-1** | `U-BREATH` | Post-commissioning thermal drift is **35 counts**, not the 3.7 the ADR implies — 9.5× | **BROKEN** |
| **N-SENSE-2** | `U-BREATH` / cavity | Cavity leak time constant is unspecified and must be **≤0.31 s** | **UNDECIDABLE** |
| **N-SENSE-3** | `SKT-BREATH` | Datasheet: mounting stress shifts the zero. Socketed, tubed, bonded shut, no number | **UNDECIDABLE** |
| **N-REF-1** | `TRIM-BREATH-ZERO` | 0→1.0 V does **not** cover a max-pedestal part that has also drifted: 1.082 V needed | **BROKEN** |
| **N-BUF-1** | `U-BUF` / `R-SER-BREATH-INST` | The instrument buffer is the one active device on the line with **no** RF filter, by an explicit decision in `carrier.md` §2 | **BROKEN**, unretrofittable |
| **N-FILT-1** | `C-FILT-BREATH` | The 482 Hz RC delivers **27 dB at 2.4 GHz**, not 134 dB. Demodulated GSM lands at 217 Hz, in-band | mechanism **BROKEN**, outcome survives on `INA828` EMIRR |
| **N-SUM-1** | `R-BREATH-SUM` | offset→span coupling is **exactly zero**. One-pass convergence, never iterative | **SURVIVES**, with proof |
| **N-POTG-1** | `POT-GAIN` | gain→zero coupling is `3.517 × V_inamp_residual`; 0.56 counts cold, **31 counts warm** | SURVIVES cold, **BROKEN** warm |
| **N-POTG-2** | `POT-GAIN` | Usable gain range is a function of the offset setting: 0.50–2.45× at centre, 0.50–1.37× at CCW | **BROKEN** |
| **N-POTG-3** | `POT-GAIN` | "linear does most of its work in the last quarter turn" is backwards — the *first 14 %* covers the first octave | **BROKEN** (arithmetic) |
| **N-JACK-2** | unplug mid-note | It is **not** a drone. 31.5 ms τ, silent in 158 ms — *unless* the offset knob is off centre | **BROKEN** (both directions) |

---

## Claim 1 — "AGND is sense-only and carries no power current, which is what makes the 2 m run work"

### N-AGND-1 — the current, enumerated. The premise SURVIVES.

`[repo] carrier.md` §2, `breath-receive-stage.md`: `AGND` (pin 2) runs from the
instrument's analog star to the module, where it terminates at `R-SER-BREATH`
(10 kΩ) → `INA828` IN+, and at `R-BIAS-INAMP` R5 (1 MΩ) → module analog ground.

The common-mode offset that drives everything `[calc]`:

```
instrument draw, typical play   ~360 mA        [repo] 0004 §grounding table
2 m of 24 AWG                    0.168 Ω       [repo] 0003 (implied by 8.4 µV / 50 µA)
V(instrument star) − V(module star) = 60.5 mV
```

Every candidate current in the `AGND` conductor:

| Source | Current | Drop in 0.168 Ω | At the jack | Counts |
|---|---|---|---|---|
| `INA828` input bias, **max 0.6 nA** `[web]` | 0.6 nA | 0.10 nV | 0.5 pV | 8e-14 |
| R5 (1 MΩ) across the 60.5 mV CM offset `[calc]` | **60.5 nA** | 10.2 pV | 47 pV | 8e-12 |
| `C_cm` displacement at the WS2815 2 kHz PWM rate, 50 mV CM `[calc]` `i = ωCV` | 0.94 nA | 0.16 pV | — | — |
| `D-TVS-BREATH` leakage | **0 A in the conductor** — the AGND TVS is at the *instrument* end, on the star side. `U-TVS-MODULE` is deliberately unfitted `[repo] bom.csv` | | | |
| SCLK (pin 7) capacitive coupling `[calc]` (5 pF over 2 m, 25 pC/edge, 1.52e6 edges/s) | 38 nA avg, 568 µA 44 ns peaks | 95 µV peaks | — | see below |
| **Fault: BREATH↔AGND short** | 2.4 mA through `R1b` | 403 µV | irrelevant — differential is zero | 0 |

**Total in normal operation: ~65 nA → 11 pV of conductor drop → 5e-11 V at the
jack → 8e-12 counts.** The premise is true by eleven orders of magnitude.

**And it is structurally enforced, not merely declared.** `[calc]` The only
DC path from the `AGND` conductor into module ground is `R-SER-BREATH` (10 kΩ)
in series with `R-BIAS-INAMP` R5 (1 MΩ). **Even a full 12 V across that path is
`12 / 1.01 MΩ = 11.9 µA`.** So `AGND` *cannot* become a power return, in any
fault, including `PWR_GND` opening entirely:

> **`PWR_GND` open.** 360 mA has to go home. `DIG_GND` (pin 8) is a parallel
> conductor to the same instrument copper — the carrier draws one `PWR_GND` pour
> `[repo] carrier.md` §1/§4 — so the current simply moves to pin 8 and the CM
> offset stays at ~60 mV. `AGND` takes 11.9 µA at most. **Both power grounds
> open:** the instrument brownouts; `AGND` still takes 11.9 µA, so the pair's
> common mode rises toward +12 V and the in-amp saturates — but nothing in the
> `AGND` conductor carries power current at any point.

**`PWR_GND` with added resistance** `[calc]`: a worn etherCON contact at 1 Ω
gives 360 mV of CM; at 71 dB (below) that is 16.5 µV RTI → **0.012 counts**. At
10 Ω the instrument drops 3.6 V out of 12 and browns out long before the breath
error matters. The *healthy* path is indifferent to `PWR_GND` resistance. (It is
not indifferent once `AGND` opens — see **N-INP-1**.)

**The SPI-coupling term, since the prompt names it** `[calc]`: 25 pC per SCLK
edge into `AGND` (0 Ω to the star) vs ~15 pC into `BREATH` (1 kΩ to the buffer
through `R1`) gives an asymmetric 75 µV step decaying at τ = 200 ns; integrated
at 1.52e6 edges/s it is **23 µV of DC at the in-amp input = 0.017 counts**, and
the twisted SCLK/DIG_GND pair cancels most of even that. It is DC and constant
(the loop refreshes all six channels every pass, `[repo] 0006`), so
`TRIM-BREATH-ZERO` removes it. **Non-issue.**

### N-AGND-2 — the causal claim is BROKEN

**The case:** delete the no-current property and keep everything else. The error
does not change.

`[calc]` The in-amp measures `V_BREATH − V_AGND`. Both are referenced to the
*instrument's* star. The 60.5 mV that `PWR_GND` develops appears at the module
as **common mode**, and is rejected by:

```
resistive balance, worst case:
  R-BIAS-INAMP is 1 MΩ 1 %   → two legs 2 % apart
    1.000/1.011 = 0.9891196 ; 1.020/1.031 = 0.9893307 ; Δ = 2.11e-4 → 73.5 dB
  series legs: 10k 0.1 % + 1k 1 %  → ΔR ≤ 40 Ω on 11 kΩ
    1M/1.011M vs 1M/1.01104M ; Δ = 6.09e-5 → 84.3 dB
  combined worst case 2.72e-4        → 71.3 dB
INA828's own CMRR, G ≈ 2.185         > 90 dB at G = 1 [web] — not dominant
net 71 dB:  60.5 mV × 2.72e-4 = 16.5 µV RTI → 77 µV at the jack = 0.012 counts
```

Against the "no current" property, which buys **11 pV**.

> **The 2 m run works because of 71 dB of common-mode rejection, purchased with
> `R1b`, the two 0.1 % series resistors and the matched 1 MΩ pair — not because
> `AGND` carries no current. The no-current rule is worth 3600× less than the
> balance it sits beside.**

This is not pedantry. The claim as written directs attention to the wrong
budget. `[repo] breath-receive-stage.md` itself shows the consequence — one
unmatched 1 kΩ resistor spent "the **entire** 60 dB budget" — which is a CMRR
finding, not a current finding, and it was found *despite* the rule rather than
because of it. **What the rule actually protects is the absence of a
`0.168 Ω × 360 mA` term in the *differential* path**, and that is guaranteed by
`R5` (11.9 µA ceiling), not by the phrase.

For scale, the counterfactual the scheme avoids `[calc]`: sensing `BREATH`
against module local ground puts the whole 60.5 mV in the signal →
`60.5 mV × 4.662 = 282 mV at the jack = 45 counts, moving with the light show`.
That is the real payoff — 45 counts → 0.012 counts — and **N-INP-1 shows it
arriving anyway through a single broken conductor.**

### N-AGND-3 — `C-FILT-BREATH` has no tolerance in the BOM, and the receive page's number is a decade off

`[repo] bom.csv` row `C-FILT-BREATH`: *"15nF C0G (diff) + 1.5nF C0G (cm x2)"* —
**no tolerance**. `[repo] breath-receive-stage.md` says *"At ±5 % the common-mode
capacitor mismatch alone gives ~46 dB at 100 Hz; ±1 % is needed to clear 60.
Specify ±1 % C0G."* The BOM row never got it.

**The 46 dB is a 1 kHz number, not a 100 Hz one** `[calc]`:

```
CM→DM conversion ≈ R_ser · ω · ΔC ,  ΔC = 5 % × 1.5 nF = 75 pF , R_ser = 11 kΩ
  100 Hz : 11k × 2π·100 × 75p  = 5.18e-4 → 65.7 dB
  1 kHz  : 11k × 2π·1000 × 75p = 5.18e-3 → 45.7 dB   ← this is the "46 dB"
```

**Quantify the real cost, at the frequency that matters** `[calc]`.
`[repo] 0014` says *"a WS2815 run modulates its draw by hundreds of milliamps at
the ~2 kHz PWM rate"*. Take 300 mA p-p:

```
CM on the pair        300 mA × 0.168 Ω             = 50.4 mV p-p at 2 kHz
CM→DM at ±5 %         11k × 2π·2000 × 75p          = 1.037e-2
differential rolloff  |1 + j(2000/482)|            = 4.27
net conversion                                      = 2.43e-3  (52.3 dB)
error RTI             50.4 mV × 2.43e-3            = 122 µV
at the jack           × 2.1612 × 2.157             = 571 µV  = 0.09 counts
at ±1 %                                             = 114 µV  = 0.018 counts
```

**Verdict: the arithmetic in the receive page is BROKEN (wrong decade); the
design consequence SURVIVES** — 0.6 mV of 2 kHz LED-correlated ripple is
inaudible. Specify ±1 % anyway, it is free, and **put it in the BOM row**, which
is where parts get ordered from.

**One purchase check while you are there** `[from memory]`: the BOM already
flags that *"82nF in C0G/NP0 almost certainly does not exist in 0805"* for
`C-FILT-MOD`. **15 nF C0G in 0805 is in the same marginal band** (C0G 0805 tops
out near 22 nF at low voltage). `C-FILT-BREATH` carries no such warning.
Distributor sites are proxy-blocked; verify before ordering.

### N-AGND-4 — the 0.168 Ω is optimistic

`[repo] bom.csv` `CABLE-UMB` specifies **stranded** Cat5e. `[from memory]`
stranded patch cord is 24 AWG stranded (~0.095 Ω/m) or, very commonly, 26 AWG
(~0.143 Ω/m), plus **two mated contact pairs per conductor** at the etherCON
ends. Realistic range for 2 m: **0.19 Ω to 0.35 Ω fresh**, unbounded as the
consumable ages under constant flexing. At 0.35 Ω the CM offset is 126 mV rather
than 60.5 mV. Healthy path: still 0.025 counts. **It matters only in N-INP-1,
where it doubles the damage.**

---

## Claim 2 — "A broken BREATH or AGND conductor is invisible to the instrument, and that is accepted"

The instrument's ADC is upstream of the umbilical `[repo] 0004`, so *all six*
cases below leave the display, the mod channels and USB MIDI reading a perfectly
healthy breath channel. ADR 0004 accepts that on the grounds that *"in practice
it is audible immediately"*. **That justification is false for the case that
matters.**

Common numbers `[calc]`, using a typical part (`Voff` = 0.265 V `[web]`, so
`TRIM-BREATH-ZERO` is set to `V_REF = 2.1612 × 0.265 = 0.573 V`), the
commissioned `a = 0.537` (2.157× downstream) and offset at centre (+0.07 V):

| Case | IN+ | IN− | In-amp out | **Jack** | Counts | Damage? |
|---|---|---|---|---|---|---|
| **healthy, at rest** | 0 | 0.262 | 0.000 V | **+0.07 V** | 0 | — |
| **A. BREATH open** | 0 | +0.6 mV (bias × 1 MΩ) | **+0.572 V** | **−1.17 V** | **−187** | none |
| **B. AGND open** | 0 | 0.322 | **−0.131 V** | **+0.35 V** + 44 cts of wobble | **+45** | none |
| **C. both open** | bias × 1 MΩ | bias × 1 MΩ | **+0.573 V** | **−1.17 V** | **−187** | none |
| **D. BREATH↔AGND short** | 0.131 | 0.131 | **+0.573 V** | **−1.17 V** | **−187** | none |
| **E. BREATH↔+12 V** | 0 | 11.88 V | **−11.9 V** (rail) | **+11.45 V** (rail) | **+1825** | see below |
| **F. AGND↔+12 V** | 11.88 V | — | — | — | — | LT1641-1 latches, module dark |

### N-INM-1 — open BREATH parks the jack at −1.17 V, and three documents say 0 V

`[calc]` With `BREATH` open, `R-BIAS-INAMP` R4 pulls IN− to module ground and
the differential goes to zero. An in-amp's output at zero differential is
**`V_REF`**, and `V_REF` is the commissioning trimmer:

```
Vout(in-amp) = G·(V+ − V−) + V_REF  →  0 + 0.573 V
jack         = −4.02 × 0.537 × 0.573 + V_offset = −1.24 V + V_offset
```

Range over the sensor spec band `[calc]`: `V_REF = 2.1612 × Voff` is 0.328 V
(min part) to 0.817 V (max part), so the park is **−0.71 V to −1.77 V** at the
commissioned gain and **−1.32 V to −3.28 V at full gain** — i.e. *which sensor
you were shipped* sets where a broken cable leaves your rack.

This contradicts, directly:

- `[repo] 0006`, the power-on table: *"Breath | 0 V | The receiver's differential
  pulldown holds it there (ADR 0003)"*. Wrong twice — the differential pulldown
  was deleted `[repo] 0003`, and its replacement parks at `V_REF`, not 0 V.
- `[repo] breath-receive-stage.md`: *"Without these the in-amp's inputs float
  when the cable is unplugged and it saturates to a rail"* — true, and the
  implied "with them it goes to 0 V" is false by exactly `V_REF`.
- `[repo] 0005` is cited by 0006 as promising 0 V at the jack.

**Mechanism of the defect:** the `REF` trimmer was added to fix the pedestal
polarity problem. It moved the unplugged rest point off zero by exactly the
pedestal it nulls, and no document followed the change through. **The fix
created the finding.**

### N-INP-1 — open AGND: the worst case in the set, because it plays

`[calc]` IN+ falls to module ground through R5. IN− still carries
`0.98912 × (60.5 mV + V_sensor)` — referenced to the *instrument's* ground,
which is 60.5 mV up. Two things happen:

1. **A standing +45-count offset** (0.35 V at the jack), which is a VCA sitting
   2.8 % open at rest, indefinitely.
2. **The entire common-mode rejection is gone.** The instrument's draw now
   appears in the signal one-for-one:

```
draw swing, quiescent → full light   180 → 530 mA   [repo] 0005 load table
ΔCM on the pair                      350 mA × 0.168 Ω  = 58.8 mV
at the jack                          58.8 mV × 4.662   = 274 mV = 44 counts
  — in-band (animation rates of Hz to tens of Hz), unfiltered
plus the 2 kHz PWM component         50 mV /4.27 × 4.662 = 55 mV p-p
with an aged cable at 0.35 Ω         ×2.1 → 92 counts
```

**Span is unchanged** (the 0.98912 factor survives), so the instrument feels
completely normal. There is no intermittency, no dropout, no dead note.
`[repo] bom.csv` `CABLE-UMB` says to *"replace at the first intermittency"* —
**this fault has no intermittency to notice.**

> **Verdict: BROKEN.** A single broken conductor in a consumable patch lead
> silently reinstates the exact defect — breath CV modulated by the light show,
> at 44 counts — that ADR 0003 spends five pages and a dedicated conductor
> eliminating. "In practice it is audible immediately" is false: it is audible
> as *noise*, which gets blamed on the rack, the module, or firmware.

**The measurement that would settle it costs nothing.** With the mouthpiece at
rest, put a meter on the breath jack and blank/unblank the WS2815 strips from
the display. Healthy: <0.1 mV. Open `AGND`: **274 mV.** Add it to E10 and E11;
it is also the only diagnostic anyone will have in the field, because nothing in
the instrument can see the far end of that cable by design `[repo] 0004`.

### N-JACK-1 — the module's *normal* standalone state is not 0 V

`[repo] 0004`: *"module alive, DAC alive … that is a designed-in operating mode
… the state the instrument spends most of its life in."* In that state cases A/C
apply `[calc]`:

```
jack = −1.24 V + V_offset ,  V_offset ∈ [−4.91 V, +5.04 V]   [repo] breath-output-stage.md
     → anywhere in  −6.15 V … +3.80 V
```

**A module on the bench with no instrument attached, offset knob full CCW, puts
+3.80 V on the BREATH jack from rack power-on.** ADR 0006's power-on table says
0 V. This is also the state every standalone module milestone (E6–E12) runs in.

### N-INM-2 — BREATH shorted to +12 V: no damage, permanent full-scale note

`[calc]`, module side:

```
IN− = 12 V × 1M/(1M + 10k) = 11.88 V   → below the BAV99 clamp at +12.6 V, so the
                                         clamp never conducts and the node sits there
INA828 abs max input ≈ rail ±0.5 V = 12.5 V  → survives, does not conduct
internal A1/A2 would need V_cm ± (G/2)·Vdiff = 5.94 ± 12.98 V → hard saturation
output → negative rail ≈ −11.9 V
jack  = −4.02 × 0.537 × (−11.9) + offset = +25.7 V → clips at ≈ +11.45 V
```

- **The jack sits at +11.45 V indefinitely.** Neither the GAIN knob nor the
  OFFSET knob can reduce it — both stages are saturated. This is the stuck
  full-scale note.
- **`D-JACK-CLAMP` (BAV99 to ±12 V) does not conduct** at 11.45 V, and it is on
  the driver side of `R-OUT-PROT` anyway `[repo] bom.csv`.
- **Damage to a patched module: unlikely.** 11.45 V through `R-OUT-PROT` 1 kΩ is
  within the ±12 V any Eurorack input sees on its own rails. Into a 100 kΩ CV
  input: 114 µA. The one exposed class `[from memory]` is a microcontroller
  module with a 5 V input clamp and a 10 kΩ input resistor — 585 µA back into
  its 5 V rail; survivable, but it will back-power.
- **Instrument side:** `R1` dissipates `(12 − 0.2)²/1k` → **139 mW**, which is
  why `R-SER-BREATH-INST` is a 1206 `[repo] bom.csv`. That fix holds.
- **`D-TVS-BREATH` (PESD12VS1UB, 12 V standoff) correctly does not conduct.**
  The 12 V-not-5 V choice holds.

### N-PIN-1 — the pin map already blocks this fault, and nobody claimed the credit

`[repo] 0004` maps pins as `1 BREATH / 2 AGND / 3 +12V / 6 PWR_GND`. `[calc]`
**A crush or pierce that shorts pin 1 to pin 3 must pass through pin 2.** So a
mechanical BREATH↔+12 V short arrives with an AGND↔+12 V short, and `AGND` ties
to the instrument's `PWR_GND` at the single star tie `[repo] carrier.md` §2 →
+12 V into `PWR_GND` → the module's `LT1641-1` latches off and the panel LED
goes out `[repo] bom.csv`. **The designed-safe-but-nasty case N-INM-2 is only
reachable by a mis-terminated connector, not by cable damage.** The pin map is
doing protective work that ADR 0004 justifies only on crosstalk grounds. Record it.

**One case the diode does not cover** `[calc]`: a **crossover** lead (T568A↔B)
swaps (1,2) with (3,6). The module's +12 V then feeds the instrument through
`R1` (1 kΩ) — 11.8 mA against a 360 mA appetite, so the instrument brownouts
while `D-REVSHUNT` sees correct polarity and `LT1641-1` never trips. **A silent
dead instrument with the module's LED lit and the breath jack at −1.24 V +
offset.** ADR 0004 considered and declined a pin-map reorder for exactly this
family of leads; this is the residual symptom, and it should be in the
troubleshooting notes.

---

## Claim 3 — "TRIM-BREATH-ZERO nulls any DC offset at commissioning, so DC errors do not matter"

### N-SENSE-1 — the sensor's own offset drift is 9.5× what the repo carries. BROKEN.

`[repo] 0003`: *"the MPXV4006DP's offset drifts roughly 0.5 mV/K, so a 20 K
interior rise moves the jack about **23 mV out of 10 V — 0.23 %**"*, flagged as
unverified because nxp.com was unreachable. `[repo] breath-receive-stage.md`
repeats it as *"~20 mV in 10 V … a quarter turn if it ever bothers you"*.

**Two errors compound.**

**(a) It is the in-amp's output, not the jack.** `[calc]` `0.5 mV/K × 20 K = 10 mV`
at the sensor; `× 2.1612 = 21.6 mV` at the in-amp; **`× 2.157 = 46.6 mV` at the
jack**, and `× 4.02` = 87 mV at full gain. The quoted 23 mV omits the whole
downstream stage.

**(b) The 0.5 mV/K is 4.7× optimistic.** `[web]`
([nxp.com](https://www.nxp.com/docs/en/data-sheet/MPXV4006.pdf) /
[st.com](https://www.st.com/resource/en/datasheet/mpxv4006dp.pdf), via search
snippets — both PDFs proxy-blocked):

```
Accuracy, 10 °C to 60 °C :  ±2.46 % VFSS  WITH auto zero
                            ±5.00 % VFSS  WITHOUT auto zero
VFSS = 4.6 V
"To obtain the 2.46 % FSS accuracy, the device output must be autozeroed
 after installation."
```

**The analog path to the jack has no auto-zero** — that is the whole point of
ADR 0003's one-authority-per-representation rule. So the ±5.0 % column is the
analog path's column `[calc]`:

```
±5.00 % × 4.6 V = ±230 mV at the sensor  → × 4.662 = ±1.072 V = ±171 counts
±2.46 % × 4.6 V = ±113 mV                → × 4.662 = ±0.527 V =  ±84 counts   (digital copy)
the difference, 2.54 % VFSS = 117 mV, is the term a once-set trimmer cannot follow
  → 545 mV at the jack = 87 counts over the datasheet's 50 K
  → implied offset tempco 117 mV / 50 K = 2.34 mV/K   (vs the repo's 0.5)
prorated to the instrument's own 20 K rise  [repo] 0003, 0009:
  → 218 mV at the jack = 35 counts = 2.2 % of span
```

> **BROKEN: 35 counts, not 3.7.** And the sign is the bad one — a piezoresistive
> bridge's zero typically walks positive with temperature `[from memory]`, so
> after warm-up the jack rests ~0.22 V *high*, which through a VCA is **a note
> that never fully stops**, not a silent offset.

**This reopens a justification, though not the decision.** ADR 0003 deleted DAC
channel 6 for two reasons: (i) it corrected a signal firmware cannot measure —
**still sound, still decisive**; (ii) what it bought was *"a quarter-turn of a
knob you will probably never touch."* **Reason (ii) is 9.5× wrong.** The
decision survives on (i) alone; the cost line needs correcting so nobody
re-derives (ii) and thinks the drift is negligible.

### The full post-commissioning budget

`[calc]`, all referred to the jack at the commissioned 2.157× (a term at the
in-amp output multiplies by 2.157; a term at the sensor by 4.662):

| Term | Source | Two-hour session (20 K body / 10 K module) | Counts |
|---|---|---|---|
| Sensor offset drift, datasheet-implied 2.34 mV/K | `[web]` | **218 mV** | **35** |
| *(same, on the repo's assumed 0.5 mV/K)* | `[repo] 0003` | *46.6 mV* | *7.4* |
| **Cavity leak lag** — see N-SENSE-2 | `[calc]` | **0 … 1.25 V** | **0 … 199** |
| **Mounting-stress shift** — see N-SENSE-3 | `[web]` | **no number exists** | **?** |
| `INA828` V_OS drift, RTI `0.4 + 2/2.185 = 1.3 µV/K × 20 K` | `[from memory]` | 0.12 mV | 0.02 |
| `U-BUF` OPA2197 V_OS drift, 1.5 µV/K × 20 K | `[from memory]` | 0.14 mV | 0.02 |
| `U-REF-BREATH` REF5050 3 ppm/K × 20 K on the `0.04 × VS` pedestal | `[repo] bom.csv` | 0.06 mV | 0.01 |
| `TRIM-BREATH-ZERO` divider TCR mismatch, cermet vs metal film, ~200 ppm/K × 10 K on 0.573 V | `[from memory]` | 2.5 mV | 0.39 |
| `U-REG-DAC` LM317 rail tempco ~50 ppm/K × 10 K, seen through the 0.11× trim divider | `[from memory]` | 0.62 mV | 0.10 |
| `R-SPI-PULL` / SPI charge injection asymmetry | `[calc]` (N-AGND-1) | 0.11 mV | 0.02 |
| **Session total, cavity and stress excluded** | | **≈ 0.22 V** | **≈ 36** |

| Term | One year | Counts |
|---|---|---|
| Sensor long-term offset stability, ±0.5 % FSS/yr `[from memory]` — NXP publishes none | 107 mV | 17 |
| Cermet trimmer long-term stability ±0.5 % of setting `[from memory]` | 6.2 mV | 1 |
| Gel swelling from a year at ~100 % RH `[repo] 0003` / `[web]` "not compatible with water vapors" | **unbounded, no number** | ? |
| Socket contact creep + mounting stress in a bonded body | **unbounded, no number** | ? |
| Barometric | 0 — the leaking reference chamber rejects it at DC | 0 |
| **Year total, quantifiable terms + session** | **≈ 0.34 V** | **≈ 54** |

**Verdict on the claim: BROKEN.** `TRIM-BREATH-ZERO` nulls the DC error at one
temperature, at one moment, for one mounting state. **The dominant post-
commissioning term — the sensor's own offset tempco — is 35 counts per warm-up
and is not a DC error at all.** The three op-amp/reference terms the design
spent real money on (REF5050, OPA2197, INA828) together contribute **0.05
counts**, i.e. **700× less than the part they are conditioning.** The precision
is in the wrong place, and that is the finding.

`[repo] breath-receive-stage.md`'s *"a quarter turn if it ever bothers you"*:
`[calc]` 0.22 V out of a ±5 V offset range over ~300° of rotation is **13°** —
a nudge, not a quarter turn. The page is wrong in the other direction. Both
figures should be replaced with 35 counts and 13°.

### N-SENSE-2 — the cavity leak is the largest unbounded term. UNDECIDABLE, with the measurement.

`[repo] 0003` states the requirement — *"The cavity must leak"* — proves the
sealed case is catastrophic (5.2 kPa, 86 % of range), and then asserts the leak
is *"fast enough that the thermal rise over 10–20 minutes never builds
pressure"*. **No time constant is given anywhere.** Here is the number it needs:

```
[calc]  sealed rise:  ΔP/P = ΔT/T ;  15 K on 295 K, over 15 min
        ΔP = 101 325 × 15/295 = 5152 Pa over 900 s  →  ramp rate r = 5.72 Pa/s
        a first-order leak of time constant τ lags a ramp by a STEADY offset r·τ
        (it does not decay away — it persists for as long as the body is warming)

        offset = 5.72 Pa/s × τ ;  1 count = 1.346 mV at the sensor = 1.76 Pa

           τ = 0.31 s  →   1 count
           τ = 3.1  s  →  10 counts
           τ = 10   s  →  33 counts  (0.20 V at the jack — as large as N-SENSE-1)
           τ = 60   s  → 199 counts  (1.25 V at the jack — 12.5 % of span)
```

> **The design needs τ ≤ 0.31 s and nobody has said what τ is.** Eighteen
> unsealed switch cutouts probably deliver far better than that — but "probably"
> is the entire content of the current argument, and the requirement is
> sub-second, not "it leaks".

**The sign makes it worse, and it collides with ADR 0003's own diagnostic.**
Cavity pressure rises → P2 rises → `P1 − P2` falls → the sensor output falls
below `Voff` and a unidirectional part clips. ADR 0003 tells you to distinguish
a blocked reference port from ordinary drift by *"output that falls rather than
drifts"* — but **a sluggish leak produces exactly the same falling output.** The
prescribed diagnostic cannot tell the two apart.

**The measurement that settles it:** at M8's thermal soak, which already puts a
thermocouple at the sensor, **step the cavity pressure** (a syringe through one
switch cutout, ~1 kPa) **and log the sensor's decay.** One exponential fit gives
τ directly. Cost: a syringe and the log you are already taking. Do it *before*
`MECH-COAT` and before any gasketing decision, because the constraint —
`τ ≤ 0.31 s` — is a permanent constraint on every future moisture-control move,
and ADR 0003 already anticipates one.

### N-SENSE-3 — the datasheet names a drift mechanism the repo has never mentioned. UNDECIDABLE.

`[web]`, from the MPXV4006 datasheet's own auto-zero note:

> *"Due to the sensitivity of the MPXV4006, **external mechanical stresses and
> mounting position can affect the zero pressure output reading.**"*

The design, against that sentence `[repo] bom.csv`, `[repo] 0003`:

- `SKT-BREATH`, a **machined SIP socket** — the part is held by four spring
  contacts, not by solder.
- A **400 mm silicone tube** plus a PTFE plug and a ≤1 mL trap hanging off P1.
- Inside an **oak and acrylic body that is bonded shut** and that rises 10–20 K
  every session, with differential expansion between the carrier, the backing
  plate and the shell.
- The part is a declared **wear part** — so at least once in its life someone
  pulls it out of the socket and pushes a new one in, **after** commissioning,
  changing exactly the mounting state the datasheet warns about.

**There is no number anywhere for this, and it is the one drift term that cannot
be trimmed out remotely, because re-trimming requires opening a bonded body.**
Measurement that settles it: at E2/M8, with the sensor socketed and the tube
fitted, record the zero; unplug and reseat the sensor five times and record the
zero each time. The spread is the number. If it exceeds ~10 counts (13 mV at the
sensor), `SKT-BREATH` is buying serviceability at the cost of a calibration that
does not survive the service.

### N-REF-1 — the 0→1.0 V trimmer range does not cover a worst-case part that has also drifted. BROKEN.

`[repo] bom.csv` `TRIM-BREATH-ZERO`: *"RANGE 0 TO +1.0V … nulling the top of it
needs 0.826V at REF … +1.0V covers 0.458V with margin."* That arithmetic covers
the *spec band at 25 °C*. It does not cover the band plus the drift `[calc]`:

```
worst-case pedestal      Voff(max)          = 0.378 V        [web]
plus offset drift        2.54 % VFSS        = 0.117 V        [web], N-SENSE-1
                                              0.495 V
required REF             0.495 × 2.1612     = 1.070 V   →  > 1.000 V
```

A part at the top of its own spec band, commissioned at 10 °C and played at
40 °C, **runs out of trimmer** — leaving up to `(1.070 − 1.000) × 2.157 = 151 mV
= 24 counts` standing at the jack with the knob at the end stop. That is the
same class of failure the range was widened from 0.6 V to fix. **Specify
0 → +1.25 V** and set `R-TRIM-RANGE` (still `open` in the BOM) accordingly. Note
that this is a *module*-side part, so unlike everything else in this section it
is retrofittable — fix it in the BOM now and it costs nothing.

---

## Claim 4 — "The 482 Hz differential band limit ahead of the in-amp stops RF rectification"

### N-FILT-1 — the corner frequency is not the attenuation. BROKEN as a mechanism.

An RC's attenuation collapses at the capacitor's self-resonance and at the
resistor's shunt capacitance. `[calc]`, with `[from memory]` parasitics
(0805 ESL ≈ 2 nH including pads/vias; 0805 thick-film resistor shunt
C ≈ 0.1 pF):

```
C_diff 15 nF  SRF = 1/(2π√(2 nH × 15 nF)) =  29.1 MHz
C_cm   1.5 nF SRF = 1/(2π√(2 nH × 1.5 nF)) = 91.9 MHz
R-SER-BREATH 10 kΩ 0805: |Z| = 1/(2πfC) → 1.77 kΩ at 900 MHz, 663 Ω at 2.4 GHz
```

| Frequency | Nominal from the stated corner | **Real, with parasitics** | Shortfall |
|---|---|---|---|
| 330 kHz (`R-78E5.0`) `[repo] bom.csv` | 57 dB diff | **57 dB** (below both SRFs) | none |
| 2 MHz (SPI) `[repo] 0004` | 72 dB diff | **72 dB** | none |
| 100 MHz (SPI edge harmonics, 44 ns edges → 7.2 MHz knee) | 106 dB | **78 dB** | 28 dB |
| 900 MHz (GSM, common mode) | 99 dB cm | **44 dB** | **55 dB** |
| 2.4 GHz (WiFi/BT, common mode) | 108 dB cm | **27 dB** | **81 dB** |
| 2.4 GHz, differential | 134 dB | **33 dB** | **101 dB** |

> **The switching regulator and the SPI clock are non-threats — the filter really
> does deliver 57 dB and 72 dB there. The 2.4 GHz radio, which is the threat the
> filter's placement was argued from `[repo] breath-receive-stage.md`, gets
> 27 dB, not 134.**

**And the common-mode path — which is the path an antenna actually drives — was
deliberately given ten times *less* filtering.** `[repo] breath-receive-stage.md`:
*"`C_cm` 1.5 nF ×2, deliberately 1/10 of `C_diff`."* That choice is correct for
CM→DM conversion (N-AGND-3) and it is the wrong direction for RF, because
**rectification does not care whether the RF is differential or common mode** —
common-mode RF swings the input transistors' operating points just as well.

**The demodulated product lands inside the passband, where nothing removes it.**
`[from memory]`: GSM 850/900 is TDMA-framed at **217 Hz**; WiFi beacons at
102.4 ms → **9.8 Hz**. Both are below 482 Hz. The filter is *upstream* of the
rectifier by design, so the product it creates is downstream of the only filter
that could have caught it, and the output RC (`R-OUT-PROT` × `C-OUT-BREATH`,
482 Hz `[repo] bom.csv`) passes it too. **The "filter ahead, not behind"
argument is correct and incomplete: a filter ahead only helps to the extent it
attenuates at RF, and this one attenuates by 27 dB.**

### Does it matter? Outcome SURVIVES, on a spec nobody has read.

`[web]` The INA828 datasheet contains *"Differential Mode EMIRR Testing"* and
*"Table 2. INA828 EMIRR for Frequencies of Interest"* — so the part is
characterised for this. `[from memory]` TI's in-amp EMIRR runs ~65 dB at
400 MHz, ~70 dB at 900 MHz, ~90 dB at 2.4 GHz. On those numbers `[calc]`:

```
1 count RTI = 1.346 mV of rectified DC
at 70 dB EMIRR, RF needed at the pins = 1.346 mV × 3162 = 4.25 V peak
before the 44 dB of real filtering    = 672 V on the cable   → impossible
at a pessimistic 40 dB EMIRR          = 134 mV at the pins = 3.0 V on the cable
```

**So: a phone on the desk cannot do it** (`E = √(30PG)/d = √(30×2×1.6)/2 =
4.9 V/m at 2 m` `[calc]`, giving at most a few hundred mV of induced CM on a 2 m
conductor). **A 5 W handheld at arm's length, or a nearby transmitter into an
unshielded cable, can** — and `[repo] bom.csv` `CABLE-UMB` says shielded is
*"preferred"*, not required, while `U-TVS-MODULE` (a module-end RF shunt) is
deliberately unfitted.

**The protection diodes are not the rectifier, checked** `[calc]`:
`D-CLAMP-BREATH` (BAV99) sits at the in-amp pins *behind* the 10 kΩ, so it sees
≤45 mV of RF — an order of magnitude below where silicon conducts. It is clean.
`D-TVS-BREATH` at the connector sees the unattenuated field, but at 12 V
standoff it does not conduct; its voltage-dependent junction capacitance makes it
a weak *mixer*, producing intermod rather than DC. Second order.

### N-BUF-1 — the real exposure is the instrument's buffer, and `carrier.md` §2 removed its protection on purpose. BROKEN.

`[repo] carrier.md` §2: *"There is no band-limit capacitor at the instrument end
of `BREATH` … **Do not add a cap at `R-SER-BREATH-INST`**"*, overriding
ADR 0003's *"band-limit at both ends, around 500 Hz"*, on the grounds that the
filter belongs ahead of the in-amp.

**That reasoning covers the in-amp and leaves the other active device on the line
completely unprotected.** `U-BUF` (½ OPA2197) drives the 2 m cable through
`R-SER-BREATH-INST` (1 kΩ) and nothing else. RF induced on the cable arrives at
the buffer's *output*, is carried back to its summing junction by the feedback
loop, and rectifies there — and whatever DC the buffer produces is not an error
on the line, **it is the signal**, seen by both the jack and the instrument's own
ADC, at full 4.662× gain.

**The fix is two capacitors and it is free, but it is instrument-side and
therefore unretrofittable** `[calc]`:

```
1 nF C0G from the cable side of R1  to the analog star
1 nF C0G from the cable side of R1b to the analog star      ← MATCHED, both legs
  common-mode pole   1/(2π × 1 kΩ × 1 nF)                = 159 kHz
  differential pole  1/(2π × 2 kΩ × 0.5 nF)              = 159 kHz
  effect on the 482 Hz differential corner: none (0.3 %)
  effect on CM balance: none — the pair is matched, which is the whole rule
  op-amp stability: the caps sit BEHIND R1, outside the loop, isolated —
    the same rule the module already applies to C-OUT-BREATH  [repo] bom.csv
```

This also happens to reconcile `carrier.md` §2 with ADR 0003 instead of
overriding it. **Decide before M7; the instrument bonds shut.**

**The measurement that settles all of Claim 4:** IEC 61000-4-6 style, 3 V
conducted, 150 kHz–80 MHz, and 61000-4-3, 3 V/m radiated, 80 MHz–3 GHz, both
with 1 kHz 80 % AM, watching the breath jack on a meter with the mouthpiece at
rest. Anything above 6 mV of shift is one count. That is an E11 bench test with a
signal generator and a loop, not a chamber.

---

## Claim 5 — "The offset and gain controls are independent"

### N-SUM-1 — offset → span: coupling is exactly zero. SURVIVES, with proof.

`[repo] breath-output-stage.md`: `POT-GAIN` attenuates *ahead* of a buffer, the
buffer drives `R-IN` into a **virtual ground**, and both offset legs inject
current into that same virtual ground.

```
[calc]  V_jack = −(R-FB/R-IN)·V_buf − (R-FB/R-OFF)·V_w − (R-FB/R-OFFNEG)·(−12)
               = −4.02·V_buf − 1.914·V_w + 5.063
  check:  V_w = 0     → +5.06 V   (page says +5.04)  ✓
          V_w = 2.605 → +0.077 V  (page says +0.07)  ✓
          V_w = 5.21  → −4.909 V  (page says −4.89)  ✓
```

`V_buf` is a voltage source into a summing node; the offset currents cannot
change it. The only coupling is through the summing node's finite impedance:

```
[calc]  virtual-ground error = V_out / A_OL = 10 V / 2e6 (OPA2197, 126 dB) = 5 µV
        → 8e-4 counts of span change over the offset knob's entire range
```

The unbuffered `POT-OFFSET` wiper (source impedance 0 → R/4 = 2.5 kΩ) changes
the *offset* gain by −10.6 % at centre — which the page correctly calls feel —
and changes the summer's **noise gain** from 7.26 to 7.05 `[calc]`, worth 21 µV
= **0.003 counts** of `V_OS` contribution. Nothing.

> **Offset does not change span. Exactly. This half of the claim is airtight and
> the topology is the reason.**

### N-POTG-1 — gain → zero: one-way, and the coupling is Claim 3's drift

`[calc]` The jack at rest is:

```
V_jack(rest) = −4.02·a·V_inamp_residual + V_offset ,   4.02·a ∈ [0.503, 4.020]
zero shift over a full sweep of the gain knob = 3.517 × V_inamp_residual
```

`TRIM-BREATH-ZERO` nulls the pedestal **at the in-amp output, upstream of the
gain pot**, which is exactly the right place and is what makes this small. But
the residual is not zero:

| State | `V_inamp_residual` | Zero shift over the full gain sweep | Counts |
|---|---|---|---|
| At commissioning, trimmer set to ~0.1 % of its 1 V range `[from memory]` | 1 mV | 3.5 mV | **0.56** |
| After warm-up, on the repo's 0.5 mV/K | 21.6 mV | 76 mV | 12 |
| **After warm-up, on the datasheet's implied tempco** (N-SENSE-1) | **101 mV** | **356 mV** | **57** |
| With a 10 s cavity leak constant (N-SENSE-2) | 200 mV | 704 mV | 112 |

Realistically the player moves the gain knob a fraction of its range, not all of
it. From the commissioned 2.157× to 4.02× `[calc]`:
`(4.02 − 2.157) × 0.101 = 188 mV = **30 counts** of zero shift`.

> **Verdict: SURVIVES at commissioning (0.56 counts — genuinely independent, and
> a real improvement on the Yamaha WX5 the page cites). BREAKS after warm-up
> (30 counts per gain change) — but the defect is not in this stage. It is
> N-SENSE-1's drift being multiplied by a knob that is correctly placed.**

**How many turns to converge: one of each, always.** `[calc]` Because the
coupling matrix is strictly triangular —

```
∂(span)/∂(offset) = 0        exactly
∂(zero)/∂(gain)   = 3.517 × V_residual
```

— setting GAIN and *then* OFFSET converges in a single pass, with no iteration,
for any residual. **The WX5's documented *"you may have to repeat"* arises only
when the coupling is two-way**, and this topology makes one of the two terms
identically zero. That is the correct and defensible claim, and it is stronger
than the one the pages make. State it that way.

### N-POTG-2 — the usable gain range is a function of the offset setting. BROKEN.

`[repo] breath-output-stage.md` acknowledges the +23 V corner case and calls it
"the player's business". **The interaction is much closer to the middle of the
knob than that framing suggests** `[calc]`, with a hard blow at −4.636 V at the
in-amp and the OPA2197 stopping at ±11.45 V:

| `POT-OFFSET` | Jack at rest | Max usable gain before a hard blow clips | Fraction of `POT-GAIN`'s rotation usable |
|---|---|---|---|
| Full CCW, +5.04 V | +5.04 V | **1.37×** | **24 %** |
| Centre, +0.07 V | +0.07 V | **2.45×** | **55 %** |
| Full CW, −4.91 V | −4.91 V | **3.52×** | **86 %** |
| *(the spec)* | | *4.02×* | *100 %* |

The commissioned working point is **2.157× with the offset at centre — 13 %
below the clip.** A player who nudges the offset up to lift the VCA's floor
brings the ceiling down onto the working point, and `[repo]
breath-output-stage.md` notes the clip is *"a wall rather than compression"*.

> **"Independent" is true of the algebra and false of the panel.** The two knobs
> do not interact through the circuit; they interact through ±11.45 V of rail.
> The honest statement is the one the page already has buried at the end — *their
> sum has to fit in ±11.5 V* — promoted to the top and given the table above.

### N-POTG-3 — the taper argument is backwards. BROKEN.

`[repo] breath-output-stage.md`, *Still open*: *"Linear gives a knob that does
most of its work in the last quarter turn."*

`[calc]` With `R-GAIN-FLOOR` 7.15 kΩ under a 50 kΩ track and a fixed ×4.02:

```
G(x) = 4.02 × (50x + 7.15)/57.15 = 3.517·x + 0.503      — LINEAR in rotation
  G = 0.503× at x = 0.000
  G = 1×     at x = 0.141     ← the first octave takes 14 % of the rotation
  G = 2×     at x = 0.426
  G = 2.157× at x = 0.471     ← the commissioned point, mid-knob ✓ (page is right here)
  G = 4.02×  at x = 1.000     ← the last octave takes 57 % of the rotation
```

**A linear pot in an attenuator-ahead-of-fixed-gain topology crowds the *low*
gains at the CCW end and stretches the high ones — the exact opposite of what
the page says.** The feel complaint will be "the knob does nothing for the last
third of its travel", not "everything happens at the end".

The law that gives even octaves `[calc]`, since the range is exactly three
octaves (4.02/0.503 = 7.99):

```
R_below(x) = 7.15 kΩ × (8^x − 1)  →  26 % of track at half rotation
```

**26 % at half rotation is between a linear pot (50 %) and a standard audio
taper (~10–15 %)** `[from memory]`. So E10's bench task is *"a pseudo-log taper,
or a second floor resistor across part of the track"* — the page's own second
option — and **not** a plain log/audio part, which overshoots. Correct the
reasoning so the bench does not order the wrong pot.

---

## Claim 6 — "Unplug mid-note now drones until the module toggle is flipped, and that is accepted"

### N-JACK-2 — BROKEN in both directions. Breath does not drone; the offset knob does.

`[repo] 0004`: *"pull the umbilical mid-note and the rack holds the note until
the module's toggle is flipped."*

**Breath is analog and it collapses in 158 ms** `[calc]`:

```
differential node: two R-BIAS-INAMP 1 MΩ in series across the input pair = 2 MΩ
                   C_diff 15 nF + two C_cm 1.5 nF in series (0.75 nF) = 15.75 nF
                   + 2 m of Cat5 mutual capacitance, 56 pF/m [from memory] = 112 pF
τ_diff = 2 MΩ × 15.86 nF = 31.7 ms      →  5τ = 158 ms to settle
τ_cm   = 0.5 MΩ × 3 nF   = 1.5 ms
```

**The voltage, the duration, and what the patched module does:**

| Moment | In-amp out | Jack (offset centred) | Jack (offset full CCW) |
|---|---|---|---|
| Hard blow, cable intact | −4.64 V | **+10.0 V** | +15.0 V (clipped, +11.45 V) |
| t = 0, unplug | −4.64 V | +10.0 V | +11.45 V |
| t = 31.7 ms (1τ) | −1.34 V | +3.00 V | +8.04 V |
| t = 158 ms (5τ) | **+0.573 V** | **−1.17 V** | **+3.87 V** |
| t = ∞ | +0.573 V | **−1.17 V, forever** | **+3.87 V, forever** |

- **Into a VCA, offset at centre: the note ENDS.** A 158 ms exponential release,
  then a negative CV that every VCA reads as closed. **There is no drone.**
  ADR 0004 is wrong about breath. What *does* drone is `PITCH` and `MOD 1–4`,
  which are DAC-held and genuinely latch — the pitch you were playing is held,
  silently, under a closed VCA.
- **Into a VCA, offset knob anywhere CCW of centre: THIS is the drone.**
  `[calc]` At full CCW the jack rests at **+3.87 V** — a VCA ~39 % open,
  indefinitely, with the pitch DAC holding the last note. **The drone is not
  the breath channel latching. It is the OFFSET knob's standing output with no
  signal left to modulate it**, and it is cured by turning the offset knob, not
  by the module toggle. Nothing in the repo says this.
- **Into a VCO (breath → 1 V/oct or linear FM):** a **downward glide of
  `(V_play + 1.17)` octaves over ~150 ms**, landing on a held, wrong pitch,
  forever. On a 1 V/oct input from a +10 V hard blow that is an eleven-octave
  descending swoop. Audible, alarming, and not what "drone" prepares anyone for.
- **Damage: none, in any configuration.** ±11.45 V maximum behind
  `R-OUT-PROT` 1 kΩ, with `D-JACK-CLAMP` on the driver side limiting
  back-drive to 7.6 mA `[repo] bom.csv`.

### The E10 test as written will fail, and nobody has predicted the result

`[repo] breath-receive-stage.md`: *"E10 verifies it by pulling the umbilical
mid-note with the mouthpiece at rest."* `[calc]` With the mouthpiece at rest and
the cable intact the in-amp output is 0.000 V. Unplugged it is **+0.573 V**.

> **E10 will show a −1.17 V step at the jack the instant the plug leaves, and
> every document in the repo predicts no step at all.** The bench will read that
> as a broken module. It is not — it is `V_REF`, working exactly as designed,
> appearing at an output that three documents promise will be at 0 V.

**The end state does not depend on what you were playing**, either, so the test
as written does not measure what it claims to. Rewrite it: *"pull the umbilical
at rest and at a hard blow; record the step, the decay constant and the final
level at three offset-knob positions."* Expected: −1.17 V step, τ = 32 ms,
final level = `V_offset − 1.17 V`.

### The accepted-ness

`[repo] 0004` accepts the drone because the watchdog that would have caught it
was withdrawn for good reasons. **The acceptance is fine; the description is
not.** Replace it with:

> Pulling the umbilical mid-note releases breath over ~150 ms and then parks the
> breath jack at `V_offset − 1.17 V` (−1.17 V at centre, up to +3.87 V full CCW),
> while pitch and the four mod channels hold their last values until the module
> toggle is flipped. **If the offset knob is CCW of centre, the rack drones.**

---

## What to change, ordered by whether it can be done later

**Unretrofittable — instrument-side, decide before M7:**

1. **N-BUF-1** — two matched 1 nF C0G caps on the cable side of `R1`/`R1b` to the
   analog star. Reverses `carrier.md` §2's *"do not add a cap"*, restores
   ADR 0003's *"band-limit at both ends"*, protects `U-BUF` from RF, costs
   nothing, preserves balance, and does not move the 482 Hz corner.
2. **N-SENSE-2** — measure the cavity leak time constant at M8, with a syringe
   step. **Required: τ ≤ 0.31 s.** It is currently unknown and it bounds every
   future moisture-control decision.
3. **N-SENSE-3** — measure the reseat-to-reseat zero spread of `SKT-BREATH` at
   E2. If it exceeds 10 counts, the socket's serviceability is buying a
   calibration that does not survive being serviced.

**Retrofittable — module-side, fix in the BOM now:**

4. **N-REF-1** — `TRIM-BREATH-ZERO` range **0 → +1.25 V**, not +1.0 V. Set
   `R-TRIM-RANGE` (still `open`) from that.
5. **N-AGND-3** — put **±1 % C0G** into the `C-FILT-BREATH` row, and verify that
   15 nF C0G exists in 0805 before ordering.

**Documentation, where the numbers are wrong:**

6. **N-INM-1 / N-JACK-1** — ADR 0006's power-on table: breath is **`V_offset` −
   `4.02·a·V_REF`**, not 0 V, and the justification it cites (the differential
   pulldown) was deleted.
7. **N-SENSE-1** — replace "23 mV out of 10 V, 0.23 %" with **218 mV, 2.2 %,
   35 counts**, in ADR 0003 and in `breath-receive-stage.md` ("~20 mV … a quarter
   turn" → "~0.22 V … 13°").
8. **N-AGND-2** — restate the rule: the 2 m run works on **71 dB of common-mode
   rejection**; `AGND` carrying no current is what makes that rejection
   *achievable*, and `R5`'s 11.9 µA ceiling is what *enforces* it.
9. **N-POTG-2 / N-POTG-3** — the usable-gain-versus-offset table, and the taper
   law `R_below = 7.15 kΩ (8^x − 1)`.
10. **N-JACK-2** — rewrite the unplug paragraph and the E10 test.

**Bench tests that settle the undecidables:**

| Test | Where | What it settles |
|---|---|---|
| Blank/unblank the WS2815 strips, meter on the breath jack, mouthpiece at rest | E10, E11, and field | **N-INP-1** — healthy <0.1 mV, open `AGND` = 274 mV. The only detector that exists for a fault the design accepts as invisible |
| Syringe step into a switch cutout, log the sensor decay | M8 | **N-SENSE-2** — τ, against a 0.31 s requirement |
| Reseat the sensor 5×, record the zero each time | E2 | **N-SENSE-3** — mounting-stress spread |
| 3 V/m radiated, 80 MHz–3 GHz, 1 kHz AM, meter on the jack | E11 | **N-FILT-1 / N-BUF-1** — 6 mV = 1 count |
| Unplug at rest and at a hard blow, 3 offset positions, scope the jack | E10 | **N-JACK-2** — expect a −1.17 V step, τ = 32 ms |
| Cold-to-warm soak, meter on the jack, offset knob untouched | M8 | **N-SENSE-1** — expect 0.22 V of walk, not 0.02 V |

---

## Sources

- [INA828 datasheet, Texas Instruments](https://www.ti.com/lit/ds/symlink/ina828.pdf) — I_B typ 150 pA / max 0.6 nA; CMRR > 90 dB at G = 1; the datasheet contains *"Table 2. INA828 EMIRR for Frequencies of Interest"* and *"Differential Mode EMIRR Testing"*. **ti.com is blocked by the egress proxy (403 on CONNECT); these figures come from search snippets and the EMIRR values themselves were not readable. Read Table 2 before trusting N-FILT-1's outcome verdict.**
- [MPXV4006 datasheet, NXP](https://www.nxp.com/docs/en/data-sheet/MPXV4006.pdf) and [ST's MPXV4006DP](https://www.st.com/resource/en/datasheet/mpxv4006dp.pdf) — `Voff` 0.152 / 0.265 / 0.378 V; VFSS 4.6 V; accuracy ±2.46 % VFSS **with** auto zero and ±5.0 % **without**, 10–60 °C; *"external mechanical stresses and mounting position can affect the zero pressure output reading."* **Both PDFs blocked; figures from search snippets. The `TcOffset` table row was not readable — N-SENSE-1's 2.34 mV/K is inferred from (5.00 − 2.46) % VFSS and should be replaced with the datasheet's own number when someone can open the PDF.**
- [MPXV4006DP at Farnell](https://uk.farnell.com/nxp/mpxv4006dp/ic-pressure-sensor/dp/1555615) — 766 mV/kPa, 0–6 kPa, 4.75–5.25 V, confirming the repo's transfer function.

Everything not marked `[web]` is `[repo]`, `[calc]` or `[from memory]` as tagged
inline. Distributor and manufacturer sites (ti.com, nxp.com, st.com, mouser.com,
digikey, datasheet mirrors) are all blocked by this sandbox's egress proxy —
`curl -sS "$HTTPS_PROXY/__agentproxy/status"` confirms policy 403s on CONNECT.
