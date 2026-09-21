# A3 — Carrier power, reviewed cold

**Reviewer:** cold hardware review, 2026-09-21. No other review or research
document in this repo was read; every conclusion below was rebuilt from the
schematic pages, the ADRs, `hardware/bom.csv` and what the network would give up.

**Sources read:** `hardware/controller/carrier.md` §1 and §5 (with §2, §6, §7
and the component table for context), `hardware/bom.csv`,
`docs/decisions/0005-power-architecture.md`, `0013-two-mcu-split.md`,
`0014-lighting.md`, `hardware/module/power-entry.md`.

**Network:** `recom-power.com`, `ti.com`, `nxp.com`, `waveshare.com`,
`digikey.com`, `mouser.com`, `farnell.com`, `octopart.com`, `lcsc.com`,
`cdn.sparkfun.com`, `g.recomcdn.com` and `en.wikipedia.org` were all refused by
the egress proxy (403 on CONNECT). `raw.githubusercontent.com` and web search
were reachable. **I got the LilyGO display board's actual schematic** and the
R-78E's headline electrical data; I did **not** get the R-78E derating graph or
the Waveshare board's schematic, and those two gaps are marked everywhere they
matter.

Evidence marking: `[repo] <file>`, `[calc]` with the arithmetic inline,
`[web] <url>`, `[from memory]` = **unverified, check before ordering.**

---

## Findings, ranked

| # | Node / ref | Finding | Rank | Confidence |
|---|---|---|---|---|
| 1 | `C-BUCK-IN` / `12V_BUCK` | No low-ESR HF capacitor at either R-78E input. The deliberately-high-ESR electrolytic is the *only* input cap, giving ~170–194 mV rms of 330 kHz ripple at the regulator pin and exceeding the part's ripple-current rating | **Showstopper** | High |
| 2 | `MATRIX` / `U-BUCK` | The 928 mA that sizes both regulators is 600 mA of 8×8 matrix, and 3 W on a 25 mm dev board is thermally impossible regardless of regulator. The instrument-wide clamp needs a matrix sub-cap | **Showstopper** | High |
| 3 | `+12V_UMB` / `D-REVSHUNT` | Reverse polarity is defended by a shunt and a race. SS34 clamps to −0.33…−0.50 V, which is past the −0.3 V abs max of `U-REF-BREATH`, `U-BUF` and `U-ADC`; and any partial fault that does not reach 1.0 A never latches at all | **High** | Medium |
| 4 | `VBUS_DISP` / `D-USBOR` | The display board's header pin is **USB-C VBUS itself**, with the board's own Schottky behind it. `D-USBOR` puts a *second* series Schottky in the path (4.25 V at the internal buck) and drives 4.6 V onto a sealed-in, unreachable USB-C receptacle | **High** | High |
| 5 | `C-BUCK-IN`, `C-STRIP-BULK` | No temperature grade, hour rating or ESR band on any electrolytic in a body that cannot be opened. An 85 °C/1000 h part is at end of life in **0.9 years** of continuous use | **High** | High |
| 6 | `J-LED-*` DI / `R-LED-PD` | The proposed pull-downs are on the buffer's *inputs*. They do nothing in the 12 ms window where the strips have a rail and the 74AHCT125 does not. The pull-down that fixes power-up has to be on DI/BI at the connector | **High** | High |
| 7 | `5V_B` / `U-BUCK` B | A regulator 360 mm from its load delivers none of ADR 0013's stated isolation benefit. Move it to the display board and send 12 V up the loom | **High** | High |
| 8 | `12V_BUCK` | The LC analysis is framed correctly but evaluated at the wrong operating point: 220× is typical play, the worst case is **56×** | **Medium** | High |
| 9 | `L-BUCK-IN` / `C-BUCK-IN` | Qty 1 against qty 2 — resolve by adding a second inductor, not deleting a cap. The choice moves R_neg by 2× | **Medium** | High |
| 10 | `5V_A` / `U-BUCK` A | R-78E short-circuit protection is **auto-recovery** `[web]`, i.e. the retry behaviour ADR 0005 rejected one node upstream. Benign, but say so | **Medium** | High |
| 11 | `LED-SIDE` | 1.19 W of WS2815 quiescent current buys no light and is **58 % of the instrument's idle power**. This reopens 30/m vs 60/m on grounds ADR 0014 explicitly withdrew | **Medium** | Medium |
| 12 | `C-BULK-DISP` | R-78E capacitive load rating is **220 µF** `[web]`. `C-BULK-DISP` is `TBD` and the project's house habit is 470–1000 µF | **Medium** | High |
| 13 | `3V3_RT` / `F-CHAIN` | The fault F-CHAIN covers is real and quantified (4.6 W into a SOT-23 LDO). F-CHAIN is **not in the BOM at all** | **Medium** | High |
| 14 | `IO1`/`IO2` → `U-LVLSHIFT` | On power-down the buffer's VCC collapses while the dev board still drives its inputs at 3.3 V — ~52 mA into the input clamp for a few ms | **Low** | Medium |
| 15 | `CH0` / `R-ADCDIV-U` | The ADC's input is driven 2.8 V above an unpowered VDD for ~15 ms at every power-up. It survives **only** because the divider is 10 kΩ (210 µA) | **Low** | Medium |
| 16 | `D-USBOR` | BOM package says `DO-41 THROUGH-HOLE`, carrier says SS14 (DO-214AC). And the BOM's "shared 5 V node" wording describes a *different circuit* that would put 928 mA behind one 1 A part | **Low** | High |
| 17 | `R-LED-SER` | carrier.md §5 calls it "PROPOSED"; `bom.csv` has carried it as 330 R × 4 since ADR 0014. Stale cross-reference | **Note** | High |
| 18 | `+12V_UMB` / breath | **Confirms the design.** Conducted LED noise into the breath reading through the rails is ~0.002 LSB — three orders below anything. The path that matters is the ground return, which ADR 0014 already owns | **Note** | Medium |

---

## Node `12V_BUCK` — the input LC, `L-BUCK-IN` + `C-BUCK-IN`

### The arithmetic checks out

```
L = 22 µH, C = 100 µF
f0 = 1/(2π√(22e-6 × 100e-6)) = 1/(2π × 4.690e-5) = 3393 Hz    [calc]  ✓ matches 3.39 kHz
Z0 = √(22e-6 / 100e-6)      = √0.22 = 0.4690 Ω                [calc]  ✓
```

The Q claim is right and its formula is right. For an LC damped by the
capacitor's own ESR the peak output impedance is a parallel resonance whose
equivalent parallel resistance is `Z0²/ESR`, so `Q = Z0/ESR` `[from memory,
standard series-to-parallel transform]`:

```
ESR 0.5 Ω → Q = 0.469/0.5 = 0.94,  peak |Z_out| = Q·Z0 = 0.44 Ω    [calc]
ESR 1.0 Ω → Q = 0.469/1.0 = 0.47,  peak |Z_out| = 0.22 Ω           [calc]
```

carrier.md's "Q ≈ 0.5–0.9" is those two numbers, correct, and its `Z0_peak
= 0.47` is the Q≈1 peak. **The framing of the Middlebrook check is also right**:
f0 = 3.4 kHz sits below any plausible loop crossover for a 330 kHz module, which
is the region where the converter's input really does look like a negative
resistance. Nothing wrong with the method.

### Finding 8 — the margin is evaluated at typical play, not worst case

`R_neg = −V²/P_in` is *most negative* where the power is largest. carrier.md
uses typical play. Rebuilt across ADR 0005's own load table `[repo] 0005`,
converting at the arriving voltage per that ADR's own convention `[calc]`:

| State | 5 V rail | P_out | P_in (÷0.90) | V_arr | **R_neg** | margin vs 0.44 Ω |
|---|---|---|---|---|---|---|
| Quiescent | 180 mA | 0.90 W | 1.00 W | 11.85 V | −140 Ω | 319× |
| Typical play | 226 mA | 1.13 W | 1.26 W | 11.4 V | **−103 Ω** | **234×** ← quoted |
| Typical + WiFi | 336 mA | 1.68 W | 1.87 W | 11.3 V | −68 Ω | 155× |
| **Clamp-legal worst** | **928 mA** | 4.64 W | 5.16 W | 11.3 V | **−24.8 Ω** | **56×** |

So the honest number is **56× (35 dB)**, not 220× (47 dB). That is still an
enormous margin and **the stability conclusion survives intact** — but 4× is the
distance between "no thought required" and "check which capacitor you bought",
and the page should carry the worst-case row.

Even on a low-ESR lot (0.15 Ω, Q = 3.13, peak |Z| = 1.47 Ω `[calc]`) the margin
is 24.8/1.47 = **17× (24 dB)**. **The loop is not going to oscillate.** The
problem with `C-BUCK-IN` is not stability. It is finding 1.

### Finding 1 (Showstopper) — there is no HF input capacitor

The R-78E5.0-1.0 is a buck. Its input current is a ~330 kHz square wave
`[web: 330 kHz at Vin = 12 V —
https://www.digikey.com/htmldatasheets/production/1615502/0/0/1/r-78e-1-0-series-datasheet.html]`.
At D = 5/11.3 = 0.442 the input ripple current is `[calc]`:

```
I_rms = I_out × √(D(1−D)) = 0.78 × √(0.442 × 0.558) = 0.78 × 0.497 = 0.387 A rms
```

`L-BUCK-IN` is 45.6 Ω at 330 kHz (`2π × 330e3 × 22e-6`) `[calc]`, so **100 % of
that ripple current must come out of `C-BUCK-IN`.** At 330 kHz the 100 µF is
4.8 mΩ of reactance and its ESR is 0.5–1 Ω, so ESR dominates completely:

```
ripple at the regulator pin = 0.387 A × 0.5 Ω = 194 mV rms   (0.5 Ω lot)   [calc]
                            = 0.387 A × 1.0 Ω = 387 mV rms   (1.0 Ω lot)   [calc]
                            ≈ 0.4–0.8 V rms at end of life (ESR 2× )       [calc]
```

Two consequences:

- **The capacitor is outside its ripple-current rating.** A 100 µF/25 V radial is
  typically rated 200–300 mA rms at 100 kHz `[from memory]`. 387 mA rms, in a
  body running 10–20 K above ambient, drives the self-heating that accelerates
  exactly the ESR-rise and capacitance-loss curve in finding 5. If both bucks
  share one cap (the `L-BUCK-IN` qty-1 reading), it is √(0.343² + 0.224²) =
  **0.41 A rms** `[calc]`.
- **Hundreds of millivolts of 330 kHz on the node that feeds `U-REF-BREATH` and
  `U-BUF`.** How much escapes past `L-BUCK-IN` depends on what shunts the 12 V
  node at 330 kHz:
  - **Strips fitted:** `C-STRIP-BULK` 2 × 940 µF, ESR ~0.05 Ω each, ESL ~20 nH
    → node |Z| ≈ 65 mΩ. Attenuation 0.065/45.6 = **−57 dB** → 0.28 mV rms on the
    12 V rail `[calc]`. Fine.
  - **Strips not fitted (E5/E6 bring-up, and any build where the strips are the
    last thing wired):** the only shunt is 2 m of cable, ~1 µH of pair loop
    inductance `[from memory, ~0.5 µH/m for a Cat5 pair]` = 2.07 Ω at 330 kHz.
    Attenuation 2.07/47.7 = −27 dB → **8.4 mV rms on the 12 V rail**, and it is
    also driven 2 m up the umbilical into the rack's +12 V, where every other
    module in the case sees it `[calc]`.

  **The instrument's conducted emissions onto a shared rack rail depend on
  whether the LED strips happen to be plugged in.** That is not a design.

**The fix is one part per regulator and it is missing entirely: a 10 µF X7R
ceramic at each R-78E input pin.**

```
|Z| of 10 µF at 330 kHz = 48 mΩ, ESR ~5 mΩ
ripple becomes 0.387 A × ~0.05 Ω = 19 mV rms        — 10× better   [calc]
```

### The warning box in §1 is wrong-by-omission, and it is a trap

carrier.md §1 says:

> This result depends on `C-BUCK-IN` being an electrolytic with real ESR.
> Substituting a low-ESR ceramic raises Q and the paragraph stops being true.

**Substituting is bad. Adding is essential, and adding is safe.** With 10 µF of
ceramic in parallel with 100 µF of electrolytic, the AC current at 3.4 kHz splits
roughly 10:1 in favour of the electrolytic (|Z| 0.686 Ω vs 4.69 Ω `[calc]`), so
the effective damping resistance falls only to ~0.41 Ω:

```
Q rises from 0.94 to ≈ 1.1      peak |Z_out| 0.44 → 0.51 Ω
margin at clamp-legal worst: 24.8 / 0.51 = 48×    (was 56×)        [calc]
```

A 15 % Q degradation against a 10× ripple improvement. **The correct rule to
write on the page is: the ceramic must be ≤ ~1/5 of the electrolytic.** As
written, a reader who takes the warning at face value omits the part the
regulator cannot work without.

### Is one 100 µF electrolytic the right damping element? No — for a reason that is not stability

It works today and it will keep working. The objection is that **it is the only
element doing the job and none of its relevant parameters are specified**:

- **ESR has no specified minimum.** Manufacturers publish max ESR or max tan δ.
  A "100 µF 25 V radial" can be 0.5 Ω from one series and 0.15 Ω from a low-ESR
  long-life series in the same catalogue. Q then swings 0.94 → 3.13, and peak
  |Z_out| 0.44 → 1.47 Ω `[calc]`. Still stable, but the 12 V rail now rings at
  3.4 kHz with Q = 3 (+10 dB) on every load step — on the rail that carries the
  precision reference and the op-amp. **Nobody can order the right part from
  "100 µF 25 V electrolytic".**
- **Cold:** aluminium electrolytic ESR rises 3–6× at −20 °C `[from memory]`.
  Damping improves; ripple voltage (finding 1) gets 3–6× worse.
- **End of life:** the standard criteria are ΔC ≤ −20 % and ESR ≤ 2–3× initial
  `[from memory]`. Both move at once:

```
C → 80 µF:  f0 = 1/(2π√(22e-6 × 80e-6)) = 3.79 kHz,  Z0 = √(22/80) = 0.524 Ω
ESR → 1–2 Ω: Q = 0.524/1.0 = 0.52 … 0.26                            [calc]
```

  **End of life is *more* damped, not less** — so the stability paragraph is
  robust to ageing. What ages badly is the ripple voltage, which goes to
  0.4–0.8 V rms.

**Recommended damping arrangement, three parts per buck:**

| | Value | Job |
|---|---|---|
| `C-BUCK-IN-HF` | **10 µF X7R 25 V, 0805/1206, at the regulator pin** | supplies the 330 kHz ripple current. **Missing today** |
| `C-BUCK-IN` | 100 µF 25 V **105 °C, ≥5000 h** electrolytic | the filter C, f0 and Z0 unchanged |
| `R-DAMP` (optional) | **0.47 Ω** in series with a second 100 µF electrolytic | makes Q deterministic instead of lot-dependent. Fit the footprint; populate only if E11 measures peaking |

The optional leg costs two 0805 footprints and is the difference between "Q is
whatever the capacitor turned out to be" and "Q ≈ 1 by construction".

### Finding 9 — `L-BUCK-IN` qty 1 vs `C-BUCK-IN` qty 2

`bom.csv` has `L-BUCK-IN` qty **1** and `C-BUCK-IN` qty **2** ("one per buck")
`[repo] bom.csv`. carrier.md flags the contradiction; here is what it costs.

- **One L, both bucks behind it:** the constant-power load on the single LC is
  the *sum*, so R_neg is −24.8 Ω as tabulated, and the one capacitor carries
  0.41 A rms of combined ripple.
- **One L per buck:** each LC sees its own load. R_neg per branch roughly
  doubles (−36 Ω for buck A alone at 690 mA `[calc]`), each cap carries only its
  own ripple, and the two LCs in parallel present half the peak |Z_out| to the
  12 V node.

**Two inductors is better on every axis and it is what `C-BUCK-IN` qty 2 already
budgets. Add the inductor; do not delete the capacitor.** If finding 7 is
accepted and buck B moves to the display board, the second LC moves with it and
the contradiction resolves itself.

---

## Node `+12V_UMB` — what actually arrives, and headroom

Rebuilt from ADR 0005's drop chain `[repo] 0005` extended to the worst case
`[calc]`:

```
Clamp-legal worst, 579 mA umbilical:
  cable 0.34 Ω round trip × 0.579 A          = 197 mV
  module entry Schottky 1N5817 @ 579 mA      ≈ 450 mV  [from memory]
  R-ILIM 50 mΩ + FET                         ≈  60 mV
                                        total ≈ 707 mV
Rack rail at −5 % = 11.40 V  →  arrives at 10.69 V
```

`R-78E5.0-1.0` minimum input is **8 V** `[web:
https://www.digikey.com/htmldatasheets/production/1615502/0/0/1/r-78e-1-0-series-datasheet.html]`.
**2.7 V of headroom at the worst legal operating point.** `REF5050` needs
V_OUT + ~0.2 V ≈ 5.2 V `[from memory]`. Neither is close to dropout even in the
pathological latched-full-white state (2 A on 12 V → node at ~10.3 V `[calc]`).

**This closes a worry the repo circles several times: there is no brownout
mechanism on the 12 V node at any load the module will pass.** The limiter trips
long before dropout does.

### Finding 18 (Note) — the LED conducted-noise path into breath, quantified

ADR 0014 says a WS2815 run "modulates its draw by hundreds of milliamps at the
~2 kHz PWM rate" `[repo] 0014`. Take ΔI = 300 mA at 2 kHz.

```
Node impedance at 2 kHz, strips fitted:
  C-STRIP-BULK 2 × 940 µF = 1.88 mF → |Z_C| = 1/(2π·2000·1.88e-3) = 42.3 mΩ
  ESR 2 × ~0.08 Ω in parallel                                      ≈ 40 mΩ
  → |Z_node| ≈ 58 mΩ   (the 0.34 Ω cable behind it barely participates)
Rail ripple = 0.300 A × 0.055 Ω = 16.5 mV pk at 2 kHz              [calc]
```

Into the breath signal:

| Path | Rejection | At the ADC |
|---|---|---|
| 12 V → `REF5050` → sensor excitation (ratiometric) | PSRR ~70 dB at 2 kHz `[from memory]` → 5.3 µV on 5.000 V = **1.06 ppm** | 1743 counts × 1.06e-6 = **0.0018 LSB** `[calc]` |
| 12 V → `OPA2197` V+ → buffer output | PSRR ~90 dB at 2 kHz `[from memory]` → 0.5 µV, ×0.6 divider | **0.0004 LSB** `[calc]` |
| 12 V → DC sag between strips-dark and strips-lit (0.7 V) → `REF5050` line reg 5 ppm/V `[repo] bom.csv` | 3.5 ppm | **0.006 LSB** `[calc]` |
| 330 kHz buck ripple → `OPA2197` PSRR ~40 dB `[from memory]` → 84 µV → ÷560 by `C-AA-ADC`'s 564 Hz corner `[repo]` | −55 dB `[repo] bom.csv` | **0.0001 LSB** `[calc]` |

Even if every PSRR figure above is 20 dB optimistic, nothing reaches 0.05 LSB.

**Conclusion: putting the WS2815 strips on the same raw 12 V rail as the
`REF5050` and the `OPA2197` is fine, and the `REF5050` is doing exactly the job
it was bought for.** I went looking for a reason to move them and there isn't
one.

**The 330 kHz aliasing question is worth stating because it is the bug that eats
a week if it ever appears:** 330 kHz against a 4 kHz sampler aliases to
|330000 − 82 × 4000| = **2000 Hz** `[calc]`, straight into the breath band, and
the MCP3202's sample-and-hold aperture passes 330 kHz happily. The only thing
standing between that and the signal is `C-AA-ADC`'s 564 Hz corner (−55 dB) and
the op-amp's PSRR. **Both of those are load-bearing. Do not let anyone "simplify"
`C-AA-ADC` away, and do not let the 330 kHz onto the 12 V node in the first
place (finding 1).**

### The path that *does* carry LED noise is not on this rail

It is the shared `PWR_GND` return, which ADR 0014 already found and put at 34 mV
`[repo] 0014` — consistent with my 16.5 mV of rail ripple, same order.

**My contribution is a layout rule the BOM does not state.** `C-STRIP-BULK`'s
row says "at each strip feed point, which is this board" `[repo] carrier.md`.
That is a restatement, not a constraint. The constraint is:

> **Each `C-STRIP-BULK` goes between the 12 V and GND pins of *its own*
> `J-LED-*` connector, within a few millimetres, so the 2 kHz AC loop is
> connector-to-cap and never crosses the board. The analog star point and the
> `AGND` tie go at the opposite end of the board from both LED connectors.**

That is the difference between 34 mV of ground offset and ~3 mV, and it is free.

### Separately: the cable + strip-bulk resonance is dead, which nobody has checked

`power-entry.md`'s *Still open* worries about "2 m of cable and ~2 mF at the far
end". Work it out `[calc]`:

```
L_cable ≈ 1 µH (2 m of a T568B pair — pins 3 and 6 ARE a twisted pair)  [from memory]
C = 1.88 mF  →  f0 = 3.67 kHz,  Z0 = √(1e-6/1.88e-3) = 23.1 mΩ
Cable DC resistance is IN SERIES with L: Q = Z0/R = 0.0231/0.34 = 0.068
```

**Q = 0.07 — massively overdamped by the cable's own resistance.** There is no
cable resonance to damp, and the 12 V node is genuinely a stiff source for the
`L-BUCK-IN` filter, which is the assumption §1 makes without justifying it.
That open item can be closed for the instrument end.

---

## `U-BUCK` — regulator loading and derating

### Finding: the split, rebuilt from the repo's own numbers

carrier.md calls the display board "~150–250 mA ESTIMATED" and lands on 68–78 %
for buck A. Rebuilt from primary figures rather than subtraction `[calc]`:

**Buck A** — real-time board + matrix + `U-LVLSHIFT`:

```
ESP32-S3, radio off (ADR 0012 puts WiFi on the display board)   ~80 mA  [repo] 0005
8×8 matrix at the full 3 W lighting clamp = 3.0 W / 5 V        600 mA   [repo] 0014
74AHCT125: 4 gates × CV²f at 800 kHz, 50 pF ≈ 1 mA/gate + quiescent ~10 mA
                                                        TOTAL  690 mA  = 69 %
```

**Buck B** — display board only, through its own internal buck:

```
ESP32-S3 WiFi TX burst ~350 mA @ 3.3 V  [from memory]
  = 1.16 W ÷ 0.90 ÷ 4.25 V (its input, see finding 4)          ~300 mA  burst
1.91" AMOLED + AXPM65611 bias                                 ~100-150 mA  [from memory]
                                                        TOTAL ~450 mA  = 45 %  (bursty)
```

**Buck A is ~69 %, not 78 %.** carrier.md's figure is high because it put the
whole unknown display load on A's side of the subtraction. The sum 690 + 450 =
1140 mA exceeds ADR 0005's 928 mA because the 928 mA row has the radio off;
the two are not contradictory.

### The derating curve — I could not get it

Every route to the graph was blocked. What I did get `[web]`:

- Operating range **−40 to +85 °C** with natural convection and derating; the
  0.5 A sibling is quoted as "**+70 °C without derating**"
  `[web: https://www.digikey.com/en/product-highlight/r/recom-power/r-78e-switching-regulator-module]`
- Efficiency **up to 91 % at 5 V/1 A**; 93 % at min Vin, 85 % at max Vin (28 V)
  — **ADR 0005's 90 %-at-12 V figure is correct**
- **330 kHz** at Vin = 12 V; **capacitive load rating 220 µF**; no-load input
  current 1.5 mA; **short-circuit protection with automatic recovery**
  `[web: https://www.digikey.com/htmldatasheets/production/1615502/0/0/1/r-78e-1-0-series-datasheet.html]`
- Package SIP-3, 11.6 × 8.5 × 10.4 mm `[web]`

`[from memory]` the R-78E-1.0 derating graph is flat at 100 % load to roughly
**+60 °C** ambient, then falls roughly linearly toward 40–50 % at +85 °C.
**This must be read off the actual graph before the BOM is committed.**

### The ambient the part actually sees

```
Clamp-legal worst body heat                              6.5 W    [repo] 0005
Interior rise at ~3 K/W                       6.5 × 3 = 19.5 K    [repo] 0014
Room ambient 25 °C  →  cavity air              25 + 19.5 = 44.5 °C
Local rise, SIP-3 in still air in a sealed cavity beside two dev
  boards, ~0.4 W of its own                          +10…15 K     [from memory]
                                          LOCAL AMBIENT 55–60 °C  [calc]
Room ambient 30 °C instead                    LOCAL AMBIENT ~65 °C
```

**Verdict: 69 % at 55–65 °C is inside any plausible derating curve, but the
margin to the knee is 10–15 K, not comfortable.** The part is adequately sized
*if and only if* the matrix stays inside the clamp — see finding 2, which is the
real answer to "is this sized right".

Regulator dissipation `[calc]`:

```
Buck A at 690 mA:  P_out 3.45 W, η 0.90 → P_diss 0.38 W
Buck A at play (180 mA on A): P_out 0.90 W  → P_diss 0.10 W
Buck B at 450 mA burst: P_out 2.25 W        → P_diss 0.25 W
Buck B at 150 mA:                            → P_diss 0.08 W
```

### Finding 10 — the 5 V rail's own protection is auto-retry

ADR 0005 and ADR 0014 argue at length that **auto-retry into a persistent fault
is the failure mode the design exists to avoid** — it is why the part is
`LT1641-1` and not `-2`, and why the polyfuse was deleted `[repo] 0005, 0014`.
The R-78E's short-circuit protection is **automatic recovery** `[web]`. One node
downstream, the stated principle is inverted.

It is **fine**: hiccup at a switching regulator has no self-heating resistive
element and no positive-feedback thermal term, so it is genuinely a different
mechanism from the polyfuse runaway. But the design documents should say so,
because the next reader will notice the contradiction and will not know whether
it was considered.

### Finding 12 — the 220 µF capacitive load ceiling

`C-BULK-DISP` is `TBD`/`open` in the BOM `[repo] bom.csv`, and this project's
habit with bulk electrolytics is 470–1000 µF (`C-STRIP-BULK`). **The R-78E's
rated capacitive load is 220 µF** `[web]`; the `D-USBOR` diode is forward-biased
during start-up so it provides no isolation from that load.

**Specify `C-BULK-DISP` as 100 µF electrolytic + 10 µF X7R and write the 220 µF
ceiling into both `C-BULK-DISP` and `C-STRIP-BULK`'s rows** (the latter is on
the 12 V node, not a regulator output, so it is unaffected — but the row should
say so or someone will move it).

---

## Finding 7 (High) — `5V_B`: a regulator 360 mm from its load

ADR 0013's reason for two regulators is specific: "give each board its own
regulator from the umbilical +12V, with local bulk capacitance on the display
board, **so WiFi bursts are absorbed locally rather than reaching the analog
section**" `[repo] 0013`.

**A regulator at the carrier end does not do that.** Work the loom `[calc]`:

```
J-DISP, 360 mm, 24 AWG (0.0842 Ω/m):  loop R = 2 × 0.36 × 0.0842 = 60.6 mΩ
                       26 AWG:                                     96.5 mΩ
                       28 AWG (ribbon):                           153.4 mΩ
IR drop at a 300 mA WiFi burst:  18 mV (24 AWG) … 46 mV (28 AWG)
Loom inductance, 5 V and GND adjacent, ~1 µH/m → 0.36 µH
Transient at the display board, 300 mA in ~1 µs:
        V = L·dI/dt = 0.36e-6 × 3e5 = 108 mV
```

108 mV of transient at the load, and **the 300 mA return flows in the loom's
GND conductor back into the carrier's `PWR_GND` pour — the board that carries
the analog star point and the `AGND` tie.** That is precisely the current ADR
0013 wanted kept away from the analog section, delivered to it by wire.

With buck B at the **display board** and +12 V up the loom `[calc]`:

```
Loom current for the same power: 450 mA × 5 V / (0.90 × 11.3 V) = 221 mA
→ half the current, half the IR drop, and the loom no longer carries the
  load's transient current at all — only the buck's filtered input current
Conductor count is unchanged: the "5 V" conductor becomes a "12 V" conductor
```

**Recommendation: buck B and its LC move to the display board. J-DISP carries
+12 V.** §6 already contemplates this ("5 V (or +12 V — see Still open)"). Costs:
a 20 × 15 mm power island at the top of the instrument (SIP-3 + 22 µH + two
caps), against ADR 0013's "the display board needs four broken-out pins".

A point in its favour nobody has made: it also moves a 330 kHz switcher **away
from the breath sensor and the reference**, which ADR 0003 spent real effort
isolating from everything else, and puts it next to an AMOLED that does not care.

**If it is rejected on build-effort grounds, then two things become mandatory:**

1. `C-BULK-DISP` stops being `TBD` and becomes **100 µF electrolytic + 10 µF
   X7R at the display board's power pin** — it is then the *only* thing doing
   the job ADR 0013 asked for.
2. **ADR 0013's isolation claim is downgraded in writing** to "headroom split
   only", so nobody later builds on an isolation guarantee that does not exist.

**What I would not do: delete buck B.** 690 + 450 = 1140 mA behind one 1 A part,
or 880 mA on a realistic worst case `[calc]`, is 88 % of rating at 60 °C. Two
regulators is the right call; only the *location* is wrong.

---

## Finding 4 (High) — `D-USBOR` and what is actually behind the dev boards' power pins

**I obtained the display board's schematic.** `[web:
https://raw.githubusercontent.com/Xinyuan-LilyGO/LilyGo-AMOLED-Series/master/schematic/T-Display-S3-AMOLED-Touch.pdf`
— this is the file the repo's own README maps to "T-Display-S3 AMOLED", dated
2023-11-20, RM67162, i.e. the base part `bom.csv` specifies]

The power page, reconstructed:

```
USB-C receptacle (VBUS pins A4/A9/B4/B9) ──┬── net "VBUS" ──► header pin "VBUS"
                                           ├── D5  SMF5.0A TVS
                                           ├── U6  TP4065 Li-ion charger (VCC)
                                           └── D4  B5819WS Schottky ──┬── net VCC5V
                                                                      │
                     VBAT ──[Q1 NCE3401A P-FET]──────────────────────┘
                                                                      │
                             U4 SY8089A1AAC buck + L4 1 µH ───────────┴──► DC3V3
                             U5 AXPM65611 ──► ELVDD +4.6 V / ELVSS −2.2 V
                             L5 ferrite 300 Ω@100 MHz: DC3V3 → 3V3
                             R2/R3 = 5.1 kΩ on CC1/CC2  (Rd — declares a SINK)
```

Four things follow, none of which is in the repo.

**(a) The header pin is not a "5 V pin". It is the USB-C connector's VBUS net,
with nothing in series.** ADR 0005 says "driving their `5V`/`VBUS` pins lets
that circuitry do its job" `[repo] 0005` — the circuitry is there, but the pin
is *upstream* of it, not at its input.

**(b) `D-USBOR` puts a second Schottky in series with the board's own.**

```
R-78E out           5.00 V
 − SS14 Vf @ 300 mA  0.40 V   [from memory]     → VBUS pin  4.60 V
 − D4 B5819WS @ 300 mA ~0.35 V [from memory]    → VCC5V     4.25 V
```

The `SY8089` buck runs happily at 4.25 V (its input minimum is ~2.5–2.7 V
`[from memory]`) and so does the display bias, so **nothing breaks** — but:
- `bom.csv`'s note says "leaving ~4.7 V at the dev boards' 5V pins — fine for
  their onboard LDOs". Both halves need correcting: it is 4.25 V **behind** the
  pin, and it is a **buck**, not an LDO.
- A buck is a constant-power load. At 4.25 V instead of 5.00 V it draws **18 %
  more current** for the same output, which raises the SS14 drop and the loom
  drop. Converging, not runaway, but the loom current and the diode dissipation
  are both under-estimated.
- SS14 dissipation: 0.40 V × 0.30 A = **0.12 W**, in a DO-214AC with θ_JA
  ~100 °C/W on a small pad → ~12 K rise `[calc, from memory for θ_JA]`. Small,
  but it is 0.12 W more into a sealed body, twice.

**(c) The instrument drives ~4.6 V onto a USB-C receptacle that is sealed
inside the body and can never be connected.** The tail-face USB-C slot aligns to
the **real-time** board's connector `[repo] carrier.md §7, 0009`. The display
board is 360 mm away, bonded in. **`D-USBOR` on buck B is OR-ing against a
source that cannot exist after M8.**

> **Concrete, free change: delete one `D-USBOR`** — unless the display board is
> flashed over its own USB during build with the umbilical also live. It is
> (ADR 0013: two firmware images, two flashing procedures). So the honest
> statement is: *the diode exists for the pre-bond build window only.* Either
> keep it and say that, or delete it and add "do not apply 12 V while flashing
> the display board" to the build procedure. **Deleting it recovers 0.4 V on the
> longest power run in the instrument.** Right now the page says neither.

**(d) A USB-C sink sourcing VBUS is non-compliant**, and while the display
board's port is unreachable, **the real-time board's port is the one in the tail
slot**. I could not get the Waveshare schematic (`waveshare.com` blocked), but
its sibling ESP32-S3-Zero is documented as an **ME6217C33M5G LDO, 800 mA**, with
the 5 V pad specified as a **3.7–6 V input** `[web:
https://www.espboards.dev/esp32/esp32-s3-zero/]` — which implies the same
direct, unprotected pad-to-VBUS arrangement. Consequences for the real-time
board, which *is* reachable:

- With USB plugged in, the host at 5.0–5.25 V beats buck A's 4.60 V, the SS14
  reverse-blocks, **and the host carries the whole 5 V load including the
  matrix — up to 690 mA from a port budgeted for 500 mA** `[calc]`. It will sag
  until buck A takes over, messily. **Bench rule: blank the matrix before
  plugging USB.**
- A C-plug shell shorting VBUS during insertion is caught by the R-78E's
  auto-recovery limit `[web]`, not by anything on this board.

**(e) Unverified and it gates the 5 V budget:** is the 8×8 matrix on the
ESP32-S3-Matrix board's **5 V** net or its **3V3** net? WS2812C-2020 is a 5 V
part and ADR 0014 quotes 5 mA/channel at 5 V `[repo] 0014, from memory`, so it
is almost certainly the 5 V net. **If it is on 3V3, 600 mA passes through an
800 mA SOT-23-5 LDO dropping 4.6 − 3.3 = 1.3 V = 0.78 W `[calc]`, which
destroys it.** E1 must measure the 5 V-pin current and the 3V3-pin current
*separately* with the matrix lit. Nobody has written that down.

### Finding 13 — `3V3_RT` can it be backfed, and `F-CHAIN`

The direction is out of the dev board: `3V3` feeds the MCP3202, the four 74HC165
and the pull-ups `[repo] 0005 power tree, carrier.md §2` — **and runs 265 mm
down the body beside 12 V LED power** `[repo] carrier.md`. The hazard is a short
on that conductor:

```
ME6217C33-class LDO, ~1 A current limit  [from memory]
Dissipation into a dead short: (4.6 − 0) × 1 A = 4.6 W in a SOT-23-5
→ thermal shutdown in milliseconds, then cycling, forever
The dev board resets forever; the matrix latches; buck A never hiccups
  because 1 A at 5 V is inside its rating
```

**`F-CHAIN` is correct and it is not in the BOM** (`grep -c "F-CHAIN"
hardware/bom.csv` → 0 `[repo]`). Sizing: real chain load is four 74HC165 (µA) +
MCP3202 (~1 mA `[from memory]`) + the pull-ups' 25.8 mA of play-rate load
`[repo] carrier.md §2` ≈ 30 mA. A 100 mA polyfuse derates to ~60–70 mA at
45–60 °C `[from memory]` — **2× margin, acceptable.**

But note the tension: ADR 0005 deleted the entry polyfuse partly because "a
polyfuse above hold does not trip cleanly; it creeps into current-limiting"
`[repo] 0005`. That is equally true here, and the thing downstream is the key
scan, which would read garbage rather than fail cleanly.

**Cleaner alternative worth costing: give the chain its own SOT-23 LDO on the
carrier, off the 5 V rail.** One part, isolates the fault completely, and removes
the whole key scan's dependency on a dev-board pin. ~30 mA × 1.7 V = 51 mW.

---

## `D-REVSHUNT` (SS34) + `D-TVS-PWR` (SMAJ15A) — the reverse-polarity sequence

The trigger is a rollover/console patch lead swapping pins 3 and 6 `[repo]
bom.csv` — on T568B those are a twisted pair (pair 3), so the swap reverses the
power pair cleanly and the instrument sees **−12 V**.

### What conducts

- **`D-REVSHUNT` SS34**, cathode to the +12 V pin: reversed, forward-biased.
  Vf ≈ 0.33 V at 0.5 A, 0.40 V at 1 A, 0.50 V at 3 A `[from memory]`.
- **`D-TVS-PWR` SMAJ15A is unidirectional**, so under reversal it is also a
  **forward diode**, ~0.9–1.1 V at high current `[from memory]`. It conducts in
  parallel and takes the minority share.
- Everything else on the rail is then held at the clamp voltage.

### The sequence, with timing

**Case (i) — toggle thrown with the bad lead already in (the normal case).**

The LT1641-1 has a programmed 50–100 ms ramp, dV/dt 240 or 120 V/s `[repo]
power-entry.md`. It is ramping into a clamp, not into 2.2 mF, so the voltage
never rises, the gate drives fully on, and the current runs to the **1.0 A sense
limit**.

```
SS34 dissipation:  1.0 A × 0.40 V = 0.40 W                         [calc]
  DO-214AB, θ_JA ~60–80 °C/W on a modest pad → 24–32 K rise  [from memory]
LT1641-1 fault timer ≈ 50 ms  [repo] power-entry.md
Energy into the SS34:  0.40 W × 50 ms = 20 mJ                      [calc]
Energy into the module's FET: 12 V × 1.0 A × 50 ms = 0.6 J         [calc]
```

**The SS34 sees 1.0 A, not 3 A, and 20 mJ is nothing.** And **0.6 J is exactly
the single-pulse figure `power-entry.md` already sized the DPAK against** —
so *the reverse-polarity fault imposes no new requirement at the module*, which
nobody has stated and which is a genuinely useful result. With foldback
programmed (V_DS is near maximum here) the limit drops well below 1.0 A
`[from memory, LT1641 foldback reduces toward ~25 % at full V_DS]`, making the
SS34's job easier still.

**Case (ii) — the bad lead hot-plugged with the toggle already ON.** No ramp.

```
I_pk = (12 − 0.4_SS34 − 0.4_D2) / (0.34 cable + 0.05 sense + 0.03 FET)
     = 11.2 / 0.42 = 26.7 A                                        [calc]
Duration: until the LT1641's gate discharges — few µs  [from memory]
Supplied by C-BULK-RAIL (100 µF): 100e-6 × 4 V / 5 µs = 80 A available
  → the module's local bulk supplies it; the rack barely notices   [calc]
SS34 I_FSM ≈ 100 A for 8.3 ms  [from memory]  → 26.7 A for 5 µs is far inside
etherCON contact rated 1.5 A  [repo] 0005  → 26.7 A for µs is inside any I²t
```

**Survivable — but only because of ratings nobody wrote down.** Put the I_FSM
requirement in the `D-REVSHUNT` row.

**Case (iii) — repeated toggling.** `LT1641-1` latches, so it is once per toggle
cycle. Someone hunting the fault will cycle it. **Ten cycles is 6 J into a DPAK
and 200 mJ into the SS34** `[calc]`. Build-note it: *if it latches, unplug the
lead; do not keep toggling.*

### Finding 3 (High) — two things the shunt cannot do

**(a) −0.4 V is past the abs max of three parts on the rail.** `REF5050`,
`OPA2197` and the MCP3202's supply-referenced pins all carry a typical
−0.3 V absolute maximum on their supply/input pins `[from memory — this is the
single most important thing to check off the datasheets]`. An SS34 at any real
current sits at −0.33…−0.50 V. The exposure is ~50 ms, abs-max ratings are not
cliffs, and it will probably be fine — but carrier.md says the SS34 "conducts
hard" as though that ended the discussion, and it does not. **It clamps to
−0.4 V, and −0.4 V is out of spec for three parts.**

**(b) The whole scheme is a race, and it only runs if the fault reaches 1.0 A.**
"The load switch becomes the fuse" `[repo] bom.csv` requires the LT1641-1 to
*enter current limit* and keep its timer running. Any fault that does not — a
partial reversal, a lead that grounds the rail through a signal conductor, an
SS34 that has gone open (Schottkys fail open as often as short), a
2-of-8-conductor miswire — leaves the instrument reverse-powered at
−11 V and **nothing latches**. In a bonded, unopenable body, triggered by a
consumable patch lead that is visually identical to a good one.

**Recommendation: a series P-FET ideal-diode on the +12 V entry, ahead of
everything.** It is the proportionate answer and it pays for itself:

```
Series P-FET, 30 mΩ:  0.36 A² × 0.03 Ω = 4 mW at typical play      [calc]
Schottky alternative: 0.36 A × 0.4 V   = 144 mW                    [calc]
```

A SOT-23 or DPAK part plus a gate resistor and a 12 V zener. It protects the
`REF5050`, the `OPA2197`, both bucks and both strips at once, makes the abs-max
question in (a) disappear, and **removes 144 mW from a sealed body** compared
with the series-Schottky alternative. Keep the SS34 as well — it costs nothing
and it catches the transient before the FET's body diode orientation matters.

**Rank: High. This is the one change I would make if I could make only one.**

---

## Thermal — per part, sealed oak body

Built from ADR 0005's clamp-legal-worst row and each part's own figure `[calc]`:

| Part / node | Dissipation | Basis |
|---|---|---|
| 8×8 matrix (on the dev board) | **3.00 W** | the 3 W clamp itself `[repo] 0014` |
| WS2815 strips, quiescent | **1.34 W** | 119 mA × 11.3 V `[repo] 0005` |
| Display board (ESP32-S3 + AMOLED + SY8089) | **0.64 W** | 150 mA × 4.25 V |
| `U-BUCK` A (R-78E5.0 #1) | **0.38 W** | 3.45 W out ÷ 0.90 |
| `U-MCU-RT` ESP32-S3 + its LDO | **0.37 W** | 80 mA × 4.6 V (LDO share 0.10 W) |
| `D-USBOR` ×2 (SS14) | **0.34 W** | (0.69 + 0.15) A × 0.4 V |
| `U-BUCK` B (R-78E5.0 #2) | **0.08 W** avg / 0.25 W burst | 0.75 W out ÷ 0.90 |
| `U-REF-BREATH` + `U-BUF` + sensor | **0.15 W** | 13 mA × 11.3 V `[repo] carrier.md §2` |
| Key chain + `U-ADC` on 3V3 | **0.10 W** | ~30 mA × 3.3 V |
| `U-LVLSHIFT` 74AHCT125 | **0.05 W** | ~10 mA × 5 V |
| **Total** | **≈ 6.45 W** | vs ADR 0005's **6.5 W** ✓ |

**ADR 0005's 6.5 W closes against a part-by-part build-up to within 1 %.** That
is not something anyone has checked and it is worth recording: the load table is
arithmetically sound.

```
Interior rise at 3 K/W:  6.45 × 3 = 19.4 K  →  cavity 44–45 °C at 25 °C ambient
At realistic play (4.1 W [repo] 0005):       12 K rise  →  cavity ~37 °C
```

### Finding 2 (Showstopper) — 3 W of clamp is not fungible

**46 % of the entire instrument's worst-case dissipation is the 8×8 matrix, and
it is concentrated on one 25 × 25 mm dev board behind an acrylic window with no
airflow** `[repo] 0014, carrier.md §7`.

```
3.0 W on a ~25 × 25 mm PCB = 6.25 cm² → 0.48 W/cm²                 [calc]
Still air behind acrylic, no heatsink: θ ≈ 30–50 K/W   [from memory]
→ board-level rise 90–150 K                                        [calc]
(per-LED junction rise is fine: 3 W / 64 = 47 mW each ≈ 14 K)
```

**The board cannot dissipate 3 W. Not "it runs warm" — it cannot.**

ADR 0014 explicitly rejected a per-device cap: "a per-device cap cannot see that
both are drawing" `[repo] 0014`. That reasoning is right about the *shared*
budget and wrong to conclude that a device ceiling is therefore unnecessary.
**Both are needed:** an instrument-wide 3 W budget *and* a matrix ceiling,
because 3 W spread over 0.84 m of strip is a different thermal object from 3 W
on one dev board.

A matrix ceiling of **~0.75 W (150 mA at 5 V)** would:

```
drop buck A's worst case from 690 mA to 240 mA = 24 % of rating    [calc]
remove 2.25 W from the body = 6.8 K of interior rise               [calc]
make the whole "is 1 A enough at 60 °C" question disappear
```

**This is the highest-leverage finding in my scope.** The 928 mA that sizes both
regulators, that drives carrier.md's 68–78 % anxiety, and that ADR 0005 cites as
the second reason for two regulators, is *entirely* the matrix — and the matrix
cannot thermally accept its share of the budget in the first place.

### Finding 5 (High) — electrolytic grade in a body that cannot be opened

`C-BUCK-IN` is "100uF 25V electrolytic" and `C-STRIP-BULK` is "470-1000uF
electrolytic, 16V" `[repo] bom.csv`. **Neither row states a temperature grade,
an hour rating, an ESR band or a ripple-current rating.** Local cap temperature
is the cavity's 45 °C plus its own self-heating — call it 55 °C. Life doubles
per 10 K below rating `[from memory]`:

```
 85 °C / 1000 h part at 55 °C:  1000 × 2^3   =   8,000 h = 0.9 years continuous
105 °C / 2000 h part at 55 °C:  2000 × 2^5   =  64,000 h = 7.3 years continuous
105 °C / 5000 h part at 60 °C:  5000 × 2^4.5 = 113,000 h = 12.9 years continuous
```

**An 85 °C/1000 h part — the default thing in a parts drawer — is at end of life
inside a year of continuous use, in a body that cannot be opened.**

**Specify: 105 °C, ≥5000 h, ripple-current rating ≥0.5 A rms at 100 kHz, ESR
0.3–1.0 Ω at 100 kHz** for `C-BUCK-IN`, and 105 °C/≥5000 h for `C-STRIP-BULK`.
Note the tension with the damping argument: **long-life low-ESR parts have
*lower* ESR**, which is precisely why the damping should not depend on the
electrolytic's ESR (see the three-part arrangement above). Free at order time,
impossible afterwards.

### Finding 11 (Medium) — 1.19 W of WS2815 quiescent buys no light

```
WS2815 quiescent < 2.1 mA per LED  [web:
  https://sheetsdata.com/parts/WS2815 — datasheet summary; VIH = 0.7 VCC]
60/m × 0.84 m = 50 LEDs:  50 × 2.1 mA = 105 mA × 11.3 V = 1.19 W   [calc]
30/m × 0.84 m = 25 LEDs:                52 mA × 11.3 V = 0.59 W    [calc]
```

Cross-check: ADR 0005's quiescent row has **123 mA on the 12 V direct branch**
`[repo] 0005` — the 105 mA figure accounts for 85 % of it. The load table and
the datasheet agree.

```
At the QUIESCENT state (2.4 W body heat), the LED chips doing nothing at all
account for 1.39 W = 58 % of the instrument's idle power                [calc]
Going 60/m → 30/m saves 0.60 W permanently = 1.8 K of interior rise     [calc]
```

ADR 0014 withdrew the current-draw argument and concluded "nothing distinguishes
them on current any more" `[repo] 0014`. **Something does**: half of a permanent,
lightless, always-on 1.19 W. That is a quarter of idle power and it is spent
whether or not anything is lit.

Confidence Medium — 2.1 mA is a maximum; typical may be ~1 mA, halving the
stake. **Measure it at E1 before M6 settles the density**, because M6 is the
last chance.

---

## Sequencing — rail order at power-up and power-down

### Power-up, under the module's programmed 50 ms ramp (240 V/s `[repo] power-entry.md`)

| t | Event | Source |
|---|---|---|
| 0 | Toggle → LT1641-1 begins ramping | `[repo] power-entry.md` |
| ~19 ms | 12 V node at 4.5 V — `OPA2197` alive (min supply 4.5 V `[from memory]`) | `[calc]` 4.5/240 |
| **~21 ms** | 12 V node at 5 V — **WS2815 internal regulators alive, logic running** | `[calc]` 5/240 |
| **~33 ms** | 12 V node at 8 V — **R-78E minimum input** `[web]`; both bucks start | `[calc]` 8/240 |
| ~34 ms | Dev board LDOs up → `3V3`, `U-ADC` VDD/VREF, chain, `U-LVLSHIFT` VCC | |
| ~48 ms | Ramp complete, 11.4 V | |
| ~130–330 ms | ESP32-S3 bootloader window ends, firmware's blank-at-boot runs | `[repo] carrier.md §5` |

*(Note: ADR 0005's "the buck starts at ~17 ms" is the current-limited-start
scenario without the programmed ramp. Under the 50 ms ramp it is 33 ms `[calc]`.
Both are right about different cases; the page should say which.)*

### Finding 6 (High) — the 12 ms window, and `R-LED-PD` is on the wrong side

**Between t = 21 ms and t = 33 ms the WS2815s have a rail and the 74AHCT125 does
not.** With `OE` tied LOW and VCC below threshold, the buffer's outputs are
indeterminate and the strips' `DI`/`BI` pins float on 420 mm of unterminated
wire beside a 12 V power conductor.

carrier.md §5's proposed `R-LED-PD` 10 k is on the **74AHCT125's inputs**
(IO1/IO2). **That is the right fix for the failure §5 describes** — GPIO1/2
high-impedance through the MCU's bootloader window, when the buffer *is*
powered. **It does nothing for the 12 ms window**, because in that window the
buffer is the thing that is dead.

The pull-down that fixes power-up has to be **on `DI` and `BI` at the
`J-LED-*` connectors**:

```
10 kΩ from each DI/BI to GND, at the connector
Cost when driven high, through R-LED-SER 330 Ω:
  V_high = 5 × 10k/(10k + 330) = 4.84 V                            [calc]
  current = 0.5 mA per line
```

Is the 12 ms window destructive? No — the WS2815 drives three LEDs in series
from 12 V, so at a 5 V rail nothing can light `[from memory]`. But the strip
**latches** whatever it shifts in, and then displays it from ~t = 30 ms until
firmware blanks it at ~t = 130–330 ms. **Random pixels for a quarter of a second
at every power-on**, in a design whose stated rule is "blank both strips as the
first act at boot". Two resistors, unretrofittable.

> **Both resistor pairs are needed. `R-LED-PD` on the inputs (as §5 proposes) for
> the bootloader window, and a second pair on `DI`/`BI` at the connectors for
> the supply-sequencing window. They fix different failures.**

*(Separately: `[web]` the WS2815 spec gives **VIH = 0.7 VCC**. If VCC in that
line means the 12 V supply pin, VIH = 8.4 V and the 74AHCT125 cannot drive it at
all — ADR 0014's open question. If it means the internal ~5 V rail, VIH = 3.5 V
and the buffer is fine. Not my scope to settle, but the threshold question is
now a *sourced* open question rather than a remembered one.)*

### Finding 15 (Low) — `CH0` is driven above an unpowered VDD for ~15 ms

`U-BUF`'s breath buffer runs on the raw 12 V and is alive at t ≈ 19 ms. The
MCP3202's VDD/VREF comes from the dev board's 3V3 at t ≈ 34 ms `[repo]
carrier.md §2`. **For ~15 ms the ADC's CH0 sits at up to 2.82 V with VDD at 0 V.**

```
MCP3202 input abs max ≈ VDD + 0.3 V  [from memory]
Clamp current limited by R-ADCDIV-U: (2.82 − 0.7) / 10 kΩ = 212 µA  [calc]
CMOS input damage threshold ~2 mA  [from memory]  →  ~10× margin
```

**It survives by accident, because the divider is 10 kΩ.** Write that down in
the `R-ADCDIV` row: *do not lower these values; they are the ADC's power-sequence
protection.* Anyone optimising the divider for noise will halve them.

### Finding 14 (Low) — power-down, and the 74AHCT125's input clamp

```
Load switch opens (gate pull-down, µs). The 12 V node is then held up by
  C-STRIP-BULK (0.94–2.0 mF) + C-BUCK-IN (0.1–0.2 mF) ≈ 1.88 mF
At typical play the 12 V-node load is 248 mA  [repo] 0005
  dV/dt = 0.248 / 1.88e-3 = 132 V/s
  11.4 V → 8 V (R-78E minimum) takes 26 ms                         [calc]
```

**The instrument runs for ~26 ms after the rail is cut.** Then buck A's 5 V
collapses while the dev board's LDO holds 3.3 V until its own input falls below
~3.4 V. In that window:

```
74AHCT125 inputs at 3.3 V, VCC decaying toward 0
Clamp current through the ESP32's ~50 Ω output impedance: 2.6 / 50 = 52 mA
AHCT input clamp abs max ≈ ±20 mA  [from memory]                   [calc]
```

Lasts a few milliseconds per power-down. Fix: **1 kΩ in series with each of
IO1/IO2 at the buffer's inputs** — bounds it to ~3 mA, costs nothing, and damps
the 800 kHz edge on the way in as a bonus.

### What the patch does at power-down — cross-check, passes

The module keeps its own rails (D1/D2 branch *before* the load switch `[repo]
power-entry.md`), so it converts whatever the instrument last sent. With
`R-SPI-PULL` idling CS high and SCLK/MOSI low `[repo] bom.csv`, **the DAC holds
its last pitch and mod values indefinitely.** The patch does not scream, because
ADR 0005's "pull down the module's breath receive input" `[repo] 0005` takes the
*analog* breath channel to 0 V and the VCA closes.

**That one resistor is load-bearing for the entire power-down behaviour, not
just for the breath channel.** Worth saying so in ADR 0005, because it currently
reads as a courtesy.

### Bench state (USB only, no umbilical) — write it down

The raw 12 V node is dead, so `REF5050`, `OPA2197` and the sensor have no
excitation. The MCP3202 is alive on dev-board 3V3 and reads **zero breath**. The
74AHCT125 is alive at 5 V driving unpowered WS2815 data pins:

```
(5 − 0.7) / 330 Ω = 13 mA into the strip's input clamp             [calc]
```

Harmless — **and it is harmless because `R-LED-SER` is there.** That is a third
independent justification for a part carrier.md §5 still calls "PROPOSED" while
`bom.csv` has carried it as `330R 1%, qty 4, candidate` since ADR 0014 `[repo]
bom.csv`. **Stale cross-reference; the BOM is ahead of the page** (finding 17).

**Add to the E5 bring-up notes: on USB alone the breath channel reads zero and
that is correct.** Someone will otherwise spend an afternoon on a dead sensor.

### Finding 16 — `D-USBOR`'s two contradictions

- **Package:** `bom.csv` says `DO-41 THROUGH-HOLE`; part is "1N5817 **or SS14**";
  carrier.md's table says SS14, which is DO-214AC (SMA). One of them is wrong,
  and it changes both the footprint and the thermal path `[repo] bom.csv,
  carrier.md`.
- **Topology:** the BOM note says "One diode per source into the **shared 5V
  node**". carrier.md correctly says it should be one per *regulator output*
  into two *separate* dev-board pins. **Both readings give qty 2, which is why
  this has survived.** But if the BOM's wording is what gets built, buck A and
  buck B are OR'd into one node — and two Schottky-OR'd regulators do not share
  load, the higher one carries everything until it current-limits. **928 mA
  behind one 1 A part: exactly the failure the two-regulator decision exists to
  prevent.** The BOM is the document that gets ordered from and read at the
  bench. Fix the note, not just the page.

---

## Things I checked and found correct

Recorded because a review that only lists faults is not a review.

- **`REF5050` and `OPA2197` on the raw 12 V.** The DC sag between strips-dark
  and strips-lit is ~0.7 V; at 5 ppm/V line regulation `[repo] bom.csv` that is
  3.5 ppm = **0.006 LSB** on the breath reading `[calc]`. The right part, on the
  right rail, for the right reason.
- **12 V up the umbilical rather than 5 V.** ADR 0005's drop argument is sound
  and the headroom survives the worst case with 2.7 V to spare `[calc]`.
- **`R-SPI-PULL`'s cable-side CS pull to 3V3, not +5 V.** The module's 74AHCT125
  runs from the rack's bus +5 V, which is live before the panel toggle, so its
  inputs are driven by an unpowered ESP32 whenever the instrument is off. The
  BOM row has already reasoned this through correctly `[repo] bom.csv`.
- **The cable + strip-bulk resonance is overdamped (Q = 0.07)** by the cable's
  own 0.34 Ω `[calc]`. `power-entry.md`'s open item can be closed for the
  instrument end.
- **ADR 0005's load table closes to within 1 %** against an independent
  part-by-part build-up `[calc]`.
- **The LC's stability conclusion holds** at every operating point, on every
  plausible capacitor lot, at end of life, and cold.

---

## What I could not verify

| Gap | Why it matters | How to close |
|---|---|---|
| **R-78E5.0-1.0 derating graph** | Sets whether 69 % at 55–65 °C is inside the curve. `recom-power.com`, DigiKey, Mouser, Farnell, Octopart, LCSC, SparkFun CDN and the Recom CDN all 403'd | Open `recom-power.com/pdf/Innoline/R-78E-1.0.pdf` on any unfiltered machine; read the knee temperature and the slope |
| **ESP32-S3-Matrix schematic** | Whether the matrix is on the board's 5 V or 3V3 net (0.78 W through a SOT-23 LDO if the latter), and whether the 5 V pad has any series element | `waveshare.com` blocked. Measure at E1: 5 V-pin and 3V3-pin currents *separately*, matrix lit |
| **Abs-max V_supply on `REF5050`, `OPA2197`, `MCP3202`** | Decides whether SS34's −0.4 V clamp is acceptable (finding 3) | `ti.com` and `nxp.com` blocked. Three datasheet lines |
| **SS34 I_FSM, SMAJ15A forward surge** | Case (ii) hot-plug survival, 26.7 A for µs | Vendor datasheets; put the numbers in the BOM rows |
| **WS2815 VIH reference rail** | `[web]` gives VIH = 0.7 VCC but not whether VCC is 12 V or the internal rail. Decides whether `U-LVLSHIFT` works at all | Five minutes with the reel's datasheet, as carrier.md §5 already says |
| **PSRR vs frequency for `REF5050` and `OPA2197`** | My noise figures use `[from memory]` 70/90 dB at 2 kHz. Even 20 dB pessimism leaves 0.04 LSB, so the conclusion is robust — but the numbers are not verified | Datasheet curves |

---

## Recommended change list, in the order I would make them

1. **Add a 10 µF X7R at each R-78E input pin**, and rewrite §1's warning box to
   *"the ceramic must be ≤ 1/5 of the electrolytic"* rather than *"do not add a
   ceramic"*. (Finding 1 — Showstopper, and the cheapest fix on this page.)
2. **Add a matrix sub-cap to ADR 0014's clamp**, ~0.75 W. It resolves finding 2
   and it retires the regulator-sizing question entirely. (Showstopper.)
3. **Series P-FET ideal-diode on the +12 V entry**, keeping the SS34. Removes
   the abs-max exposure, removes the race, and saves 140 mW. (Finding 3 — High.)
4. **Move buck B to the display board; J-DISP carries +12 V.** Or, if not,
   specify `C-BULK-DISP` and downgrade ADR 0013's isolation claim in writing.
   (Finding 7 — High.)
5. **Grade every electrolytic: 105 °C, ≥5000 h, with a ripple-current figure.**
   Free now, impossible after bonding. (Finding 5 — High.)
6. **Add 10 kΩ pull-downs on `DI`/`BI` at the `J-LED-*` connectors**, in addition
   to §5's `R-LED-PD` on the buffer inputs. (Finding 6 — High.)
7. **Add the second `L-BUCK-IN`** (or move it with buck B). (Finding 9.)
8. **Decide `D-USBOR` on buck B**: delete it, or keep it and write down that it
   covers the pre-bond flashing window only. Fix the package and the
   "shared 5 V node" wording either way. (Findings 4, 16.)
9. **Put `F-CHAIN` in the BOM**, or replace it with a dedicated chain LDO.
   (Finding 13.)
10. **1 kΩ series on IO1/IO2** into the 74AHCT125. (Finding 14.)
11. **Write the `C-STRIP-BULK` layout rule** (cap between the 12 V and GND pins
    of its own connector; analog star at the far end of the board).
12. **Measure WS2815 quiescent at E1 before M6 settles density.** (Finding 11.)

---

## Sources

- [R-78E-1.0 series datasheet (DigiKey HTML mirror)](https://www.digikey.com/htmldatasheets/production/1615502/0/0/1/r-78e-1-0-series-datasheet.html) — 330 kHz at Vin 12 V, 220 µF capacitive load, 8–28 V input, auto-recovery short protection, 1.5 mA no-load input current
- [RECOM R-78E product highlight (DigiKey)](https://www.digikey.com/en/product-highlight/r/recom-power/r-78e-switching-regulator-module) — −40 to +85 °C with derating, +70 °C without, 91 % at 5 V/1 A
- [LilyGO T-Display-S3-AMOLED schematic (base, RM67162, 2023-11-20)](https://raw.githubusercontent.com/Xinyuan-LilyGO/LilyGo-AMOLED-Series/master/schematic/T-Display-S3-AMOLED-Touch.pdf) — VBUS header pin wired to the USB-C receptacle, D4 B5819WS, D5 SMF5.0A, U4 SY8089A1AAC buck, U6 TP4065 charger, Q1 NCE3401A, 5.1 kΩ CC pulldowns
- [LilyGo-AMOLED-Series README](https://raw.githubusercontent.com/Xinyuan-LilyGO/LilyGo-AMOLED-Series/master/README.MD) — maps "T-Display-S3 AMOLED" to that schematic file
- [LilyGO T-Display-S3-AMOLED-Plus schematic](https://raw.githubusercontent.com/Xinyuan-LilyGO/LilyGo-AMOLED-Series/master/schematic/T-Display-S3-AMOLED-Plus.pdf) — sibling board, BQ25896 + RT9080-33 path, same VBUS-to-header arrangement
- [ESP32-S3-Zero pinout and specifications](https://www.espboards.dev/esp32/esp32-s3-zero/) — ME6217C33M5G LDO 800 mA, 5 V pad rated 3.7–6 V (sibling to the ESP32-S3-Matrix)
- [WS2815 parameter summary](https://sheetsdata.com/parts/WS2815) — quiescent current < 2.1 mA per LED, VIH = 0.7 VCC, VIL = 0.3 VCC
