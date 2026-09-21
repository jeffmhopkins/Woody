# A7 — Digital path and supervision, preflight review

**Slice:** `hardware/module/digital-and-supervision.md`, plus the SPI half of
`docs/decisions/0004-cv-interface-module.md`.
**Date:** 2026-09-21. **Cold:** no prior review directory was read.
**Primary sources now banked and read for this review:**

| Document | File | Used for |
|---|---|---|
| TI SCLS264O, `SN54AHCT125/SN74AHCT125`, Dec 1995 rev Jul 2003, 24 pp | `datasheets/texas-instruments/SN74AHCT125.pdf` | thresholds, drive, transition-rate limit, `Cpd`, `ΔICC` |
| TI SBAS430E, `DAC7568/DAC8168/DAC8568`, Jan 2009 rev Jan 2014, 62 pp | `datasheets/texas-instruments/DAC8568CIPW.pdf` | input thresholds, abs max, `f_SCLK`, `LDAC`, `CLR`, `I_DD` |
| Neutrik `NE8FDP` datasheet + drawing | `datasheets/connectors/NE8FDP-DATASHEET.pdf`, `.pdf`, `.dxf` | 1.5 A/contact, CAT5e component spec, 1–100 MHz |
| ADI LT1641-1, `164112fc` | `datasheets/discrete-and-power/LT1641.pdf` | `PWRGD` polarity and `V_OL` — see F-07 |

Provenance is marked on every claim: `[datasheet <doc> p.N]`, `[repo file:line]`,
`[calc]`, `[from memory]`. Everything not so marked in this document is a
restatement of an adjacent marked claim.

---

## Findings index, by node

| # | Node / refdes | Severity | One line |
|---|---|---|---|
| **F-01** | `N_LDAC` / `R-LDAC` | **BLOCKING** | `LDAC` is pulled to `AVDD`. SBAS430E says tie it to **GND**. As drawn, with the `LDAC` register at its default, the six populated channels never update — a dead module |
| **F-02** | `N_CS_CABLE` / `R-SPI-PULL` | **BLOCKING (netlist)** | The cable-side `CS` pull-up goes to **`3V3`, a net that does not exist on the module.** The module has +12 V, −12 V, bus +5 V and `AVDD` and nothing else |
| **F-03** | `DIG_GND` ↔ DAC `GND` | **HIGH** | The DAC8568 has **one** ground pin for analog and digital. If the shifter's return and the DAC's return meet only at the power-inlet star, the shifter→DAC loop is ~200 nH and the DAC's digital pins ring to **6.2–8.3 V / −1.2 to −3.3 V** against an absolute maximum of `AVDD+0.3` = 5.51 V |
| **F-04** | pins 4,5,7,8 (ADR 0004 conductor budget) | **FIXED MID-REVIEW — verified** | Found: ADR 0004's "authoritative 8-of-8 mapping" block still paired `SCLK/DIG_GND` and `MOSI/CS`, the exact pairing the same ADR refutes 730 lines later, with `check-staleness.py` passing. **Corrected on disk while this review was being written** (commit `b43e823` era). Re-verified; the residue is in §8 |
| **F-05** | `N_SCLK_DAC`, `N_DIN_DAC`, `N_SYNC_DAC` | **MEDIUM** | Bus +5 V at its +5 % limit against an `AVDD` trimmed to the E7 floor of 5.00 V leaves **50 mV** against the DAC's digital-input absolute maximum. Three 0805s fix this and F-03 together |
| **F-06** | six DAC channels, `CLR` exit | **MEDIUM** | SBAS430E has a **software simultaneous update** (`SW LDAC`, Table 11 p.36) that costs nothing and removes the 100–200 µs intermediate-value window entirely. The corpus does not know it exists |
| **F-07** | `N_CLR` ← LT1641 `PWRGD` | **recommendation** | Two of the four "not caught" rows in the page's own supervision table become "caught" for **zero parts and one net**, because `PWRGD` is an open collector that is low exactly when the umbilical rail is bad |
| **F-08** | breath path, on cable loss | **MEDIUM (corrects the page)** | `R4`/`R5` bias the in-amp to zero differential when the cable opens, so **breath falls to 0 V with τ ≈ 30 ms**. "The rack drones" is patch-dependent, not general — and this is what decides the supervision question |
| **F-09** | module panel toggle | **MEDIUM** | The page's stated recovery — "until you flip the module's toggle" — **does not work.** The toggle gates the umbilical's +12 V only; `AVDD` and the DAC are on a different branch and keep holding |
| **F-10** | `R-SPI-PULL`, DAC side | **LOW (stale argument)** | The stated justification is "with `OE` disabled the buffer's outputs are Hi-Z". `OE` is tied enabled 25 lines later. The parts are right; the reason has been refuted on its own page |
| **F-11** | `C-DECOUPLE` | **LOW** | Counted as "DAC8568 `AVDD`+`DVDD` = 2". **There is no `DVDD`** — TSSOP-16 has one supply pin and one ground pin. Qty 19 → 18 |
| **F-12** | `U-TVS-SPI` note | **LOW** | "~29 ns of edge" is computed with the RC-corner model this corpus refuted on 2026-09-21. The transmission-line answer is **~3.9 ns** |
| **F-13** | `IO34/35/36` drive strength | **LOW (firmware)** | The whole 100 Ω argument holds only while the ESP32-S3's output impedance is **< 130 Ω** `[calc]`. Nothing sets the drive-strength class |
| **F-14** | `U-LVL-MOD` gate 4 | **LOW** | The spare gate's `A` input is unassigned. SCLS264O p.3 Note 4 requires every unused input at `V_CC` or GND |
| **F-15** | DAC logic-high threshold, ADR 0004:147 | **LOW** | "a 5 V DAC wants roughly 3.5 V for a logic high" is the `0.7 × AVDD` ratio, which SBAS430E applies **only below 4.5 V**. At `AVDD` = 5.21 V the real figure is **3.256 V** |

---

## 1. Signal integrity over 2 m of Cat5 — verified against the datasheets

### 1.1 The direction of the link, first, because one premise is inverted

The 74AHCT125 is **not** the cable driver. The cable arrives at the module and
lands on the **inputs** of the shifter `[repo hardware/module/digital-and-supervision.md:23-33]`;
the shifter's outputs run a few centimetres of board to the DAC. The cable is
driven by the ESP32-S3 through `R-SPI-SER` at the instrument
`[repo hardware/controller/carrier.md:574-577]`.

Everything below therefore splits into two independent problems, and the corpus
has only ever analysed the first:

| Segment | Driver | Load | Analysed in the corpus |
|---|---|---|---|
| ESP32 → 2 m Cat5 → `74AHCT125` inputs | ESP32-S3 GPIO + `R-SPI-SER` 100 Ω | `C_i` ≤ 10 pF + three 10 kΩ pulls | yes |
| `74AHCT125` outputs → DAC `SCLK`/`DIN`/`SYNC` | AHCT125, `R_on` 33–87 Ω | 3 pF/pin + `C_o` 15 pF + trace | **no** — see §2 and F-03 |

### 1.2 What SCLS264O actually guarantees

| Parameter | Value | Cite |
|---|---|---|
| `V_IH` | **2.0 V min** (TTL, not ratioed to `V_CC`) | `[datasheet SCLS264O p.3, recommended operating conditions]` |
| `V_IL` | **0.8 V max** | `[datasheet SCLS264O p.3]` |
| Dynamic `V_IH(D)` / `V_IL(D)` | 2.0 V / 0.8 V — **identical, so no hysteresis** | `[datasheet SCLS264O p.4, noise characteristics]` |
| `Δt/Δv`, input transition rate | **≤ 20 ns/V** | `[datasheet SCLS264O p.3]` |
| `I_OH` / `I_OL` | ±8 mA | `[datasheet SCLS264O p.3]` |
| `V_OH` | 4.4 V min at −50 µA; **3.8 V min / 3.94 V typ at −8 mA**, `V_CC` = 4.5 V | `[datasheet SCLS264O p.4]` |
| `V_OL` | 0.1 V max at 50 µA; **0.44 V max / 0.36 V typ at 8 mA** | `[datasheet SCLS264O p.4]` |
| `C_i` / `C_o` | 10 pF / 15 pF max | `[datasheet SCLS264O p.4]` |
| `C_pd` | 14 pF typ | `[datasheet SCLS264O p.5, operating characteristics]` |
| `t_PLH`/`t_PHL` | 1–8.5 ns at `C_L` = 50 pF; `t_sk(o)` ≤ 1 ns | `[datasheet SCLS264O p.4]` |

**SCLS264O publishes no output edge rate and no output impedance.** The corpus's
"2–5 ns edges" `[repo docs/decisions/0004-cv-interface-module.md:79]` is not
sourced from it and cannot be — that figure belongs to the ESP32 anyway, which
is the driver. What the datasheet *does* allow is a two-sided bound on the
AHCT125's output resistance, taken from the two guaranteed DC points:

```
[calc]  p-side, V_CC = 4.5 V:  typ (4.50 − 3.94)/(8 mA − 50 µA) = 70.4 Ω
                               worst (4.50 − 3.80)/8 mA          = 87.5 Ω
        n-side:                typ (0.36 − 0.10)/(8 mA − 50 µA)  = 32.7 Ω
                               worst (0.44 − 0.10)/8 mA          = 42.5 Ω
```

This is the near-rail linear-region resistance and it is used below only where
that is the right number. It is worth recording because the folklore value for
this family is ~30 Ω `[from memory]`, and the p-side is more than twice that.

### 1.3 What SBAS430E guarantees at the DAC

| Parameter | Value at `AVDD` = 5.21 V | Cite |
|---|---|---|
| `V_INH` | **0.625 × AVDD** for 4.5 V ≤ AVDD ≤ 5.5 V → **3.256 V** | `[datasheet SBAS430E p.4]` `[calc]` |
| `V_INL` | 0.3 × AVDD → **1.563 V** | `[datasheet SBAS430E p.4]` `[calc]` |
| Digital input abs max | **−0.3 V to AVDD + 0.3 V = 5.51 V** | `[datasheet SBAS430E p.2]` |
| Input current | ±1 µA | `[datasheet SBAS430E p.4]` |
| Pin capacitance | 3 pF | `[datasheet SBAS430E p.4]` |
| `f_SCLK` max | **50 MHz**, `t2` cycle 20 ns min | `[datasheet SBAS430E p.7, note 3]` |
| `SYNC`, `DIN`, `SCLK` | **all three are Schmitt-Trigger inputs** | `[datasheet SBAS430E p.6, pin descriptions]` |
| Timing assumed | `t_R` = `t_F` = 3 ns, 10–90 % of AVDD | `[datasheet SBAS430E p.7, note 1]` |

Note the **0.625 ratio**, not 0.7. Nothing in the corpus states the DAC's input
thresholds at all; at 5.21 V the correct `V_INH` is 3.256 V, and had anyone
assumed 0.7 × AVDD they would have used 3.65 V. Both clear comfortably, so this
is a gap rather than an error — but it is the kind of gap that produced the
74HC165 and WS2815 findings this project already has.

### 1.4 First-step amplitude at the far end, 100 Ω, from the transmission-line model

Cat5 is a ~100 Ω line `[datasheet NE8FDP-DATASHEET.pdf p.2: CAT5e per TIA/EIA
568A/B component specs, frequency range 1–100 MHz]`. Velocity factor
0.64–0.70 `[from memory]`:

```
[calc]  one-way transit  2 m / (0.67 × 3e8 m/s) = 9.95 ns
        round trip       19.9 ns                          → the corpus's "~20 ns" ✓
```

The far end is genuinely open: the AHCT input is ≤ 10 pF `[datasheet SCLS264O p.4]`
in parallel with 10 kΩ `[repo hardware/bom.csv:49]`. 10 kΩ against 100 Ω is an
open to within 1 %, and 10 pF charged through `Z0` = 100 Ω is τ = 1 ns
`[calc]` — 5 % of a round trip. **The unterminated-far-end model the corpus
uses is correct**; nobody had checked that.

Source-series termination into an open line, first step at the receiver:

```
[calc]  V_far = 2 × V_S × Z0 / (Z0 + R_ser + Z_out)
        V_S = 3.3 V, Z0 = 100 Ω
```

| `R_ser` | `Z_out` = 35 Ω | `Z_out` = 40 Ω | vs `V_IH` 2.0 V |
|---|---|---|---|
| 68 Ω | 3.251 V | 3.173 V | clear, but 48.5 mA DC fault `[calc]` |
| **100 Ω** | **2.809 V** | **2.750 V** | **clear by 0.75–0.81 V**, 33.0 mA DC fault `[calc]` |
| 220 Ω | 1.859 V | 1.833 V | **below threshold** |

This reproduces `figures.yaml: spi-series-r` and `carrier.md` §4 **exactly**
(2.75 V, 1.83–1.86 V, 3.25 V, 33 mA, 48.5 mA) `[repo config/figures.yaml:103-108]`
`[repo hardware/controller/carrier.md:598-604]`. Back-solving, the corpus used
`Z_out` = 35–40 Ω for the ESP32-S3 pad. That value is nowhere sourced — no
Espressif document is banked `[repo datasheets/MANIFEST.csv]` — so I state the
robustness instead of the point estimate:

```
[calc]  break-even for V_far = V_IH = 2.0 V:
        R_ser + Z_out = 2 × 3.3 × 100 / 2.0 − 100 = 230 Ω
        with R_ser = 100 Ω:  Z_out must stay below 130 Ω
```

**The design is correct for any ESP32-S3 drive setting with `Z_out` < 130 Ω, and
has 0.75 V of margin at the assumed 40 Ω.** → **F-13**: make that a firmware
requirement (`gpio_set_drive_capability()` on IO34/35/36), because it is the
only unstated condition the whole termination argument rests on.

### 1.5 The forbidden-band dwell, and why it is a datasheet violation rather than a preference

Reflection ladder, `Γ_s` = (`R_ser`+`Z_out`−`Z0`)/(`R_ser`+`Z_out`+`Z0`):

```
[calc]  R_ser = 100, Z_out = 40:  Γ_s = +0.167
        far end (t ns, V): (10, 2.750) (30, 3.208) (50, 3.285) (70, 3.297) → 3.3
        R_ser = 220, Z_out = 40:  Γ_s = +0.444
        far end (t ns, V): (10, 1.833) (30, 2.648) (50, 3.010) (70, 3.171) → 3.3
```

At 100 Ω the waveform is **monotonic and clears `V_IH` on the first step**, and
the only "dwell" is the sub-nanosecond RC of the receiver's own input
capacitance. Effective transition rate through the 0.8–2.0 V band:

```
[calc]  100 Ω: the band is crossed inside one edge, ~2–4 ns/V   → ≤ 20 ns/V ✓
        220 Ω: 0.8 V crossed at ~1.3 ns, 2.0 V not crossed until
               the second step at ~30 ns → 28.7 ns / 1.2 V = 24 ns/V  ✗
```

So the corpus's refutation of 220 Ω is confirmed, and **it can now be stated as
a spec violation rather than as judgement**: SCLS264O p.3 lists
`Δt/Δv ≤ 20 ns/V` under *recommended operating conditions*, and the 220 Ω
waveform exceeds it. Worse than the number: the 220 Ω waveform has
`dV/dt` = 0 for 20 ns **inside** the transition band, which is precisely the
condition that limit exists to forbid, on a part whose own noise-characteristics
table shows zero hysteresis `[datasheet SCLS264O p.4]`.

**Consequence for the open "74AHCT14 edge cleanup" proposal (§5 below):** at
100 Ω the AHCT125's input-transition spec is met with an order of magnitude to
spare, so the Schmitt buffer is **not needed for edge cleanup**. That removes
one of the three jobs the page assigns it.

### 1.6 Does 2 MHz close?

`f_SCLK` max is 50 MHz `[datasheet SBAS430E p.7 note 3]`; 2 MHz is 4 % of it.
Every individual timing requirement has three to four orders of margin:

| Requirement | Spec | At 2 MHz | Margin |
|---|---|---|---|
| `t2` SCLK cycle | ≥ 20 ns | 500 ns | 25× |
| `t6`/`t7` SCLK low/high | ≥ 8 ns | 250 ns | 31× |
| `t9` data setup | ≥ 6 ns | 250 ns (DIN changes on the opposite edge) | 41× |
| `t10` data hold | ≥ 4 ns | 250 ns | 62× |
| `t1` SCLK fall → SYNC fall | ≥ 10 ns | firmware-controlled | — |
| `t4` SYNC high | ≥ 80 ns | firmware-controlled | — |
| `t5` SYNC → SCLK fall setup | ≥ 13 ns | firmware-controlled | — |

`[datasheet SBAS430E p.7, timing requirements]`

The two things that *could* have failed both pass:

- **Skew between `SCLK` and `DIN`.** Same package, `t_sk(o)` ≤ 1 ns
  `[datasheet SCLS264O p.4]`; Cat5 pair-to-pair delay skew is ≤ 45 ns/100 m
  `[from memory]` → **0.9 ns over 2 m** `[calc]`. `SCLK` and `MOSI` share pair
  (4,5) so they see almost none of even that. Total ≲ 2 ns against a 250 ns
  setup window.
- **Reflection settling inside a bit.** 20 ns round trip, essentially settled
  after two `[calc, §1.5 ladder]`, against a 500 ns bit period — 4 %. Even the
  refuted 220 Ω case settles in 60 ns. **Bandwidth was never the reason 220 Ω
  failed**; the threshold dwell was, and the corpus is right about that.

**2 MHz closes with very large margin.** `t1`, `t4` and `t5` are ESP-IDF
`spi_device_interface_config_t` settings (`cs_ena_pretrans`, `cs_ena_posttrans`)
and are written nowhere — a firmware line, not a part change.

---

## 2. The SPI return path — the loop, what it costs, and the recommended tie

### 2.1 The fact that decides it

> **`DAC8568CIPW` has one ground pin.** TSSOP-16 pin 14: *"GND — Ground
> reference point for all circuitry on the device"* `[datasheet SBAS430E p.6]`.
> There is no `DVDD` and no `DGND`. Pin 3 `AVDD` is the only supply.

So the DAC's `SCLK`/`DIN`/`SYNC` input currents **already exit into the analog
return**, unavoidably, by the part's construction. ADR 0004 puts the DAC's
return in the analog region `[repo docs/decisions/0004-cv-interface-module.md:628-629]`;
that is not a choice, it is the only option.

The choice that remains is **where the 74AHCT125's ground pin ties** — and
nothing in the corpus says. It is absent from the page, from ADR 0004's
four-return table `[repo docs/decisions/0004-cv-interface-module.md:606-611]`,
and from `power-entry.md`'s grounding section. It is the single most consequential
unstated net in this slice.

### 2.2 The loop, costed

If the shifter sits on `DIG_GND` and `DIG_GND` reaches the analog region only at
the power-inlet star `[repo docs/decisions/0004-cv-interface-module.md:627]`,
then every shifter→DAC edge current returns **the long way round**: out of the
DAC's GND pin, across the analog pour, to the star, back up `DIG_GND`.

```
[calc]  rectangular-loop inductance, round-conductor radius a = 0.15 mm
        (0.6 mm trace), standard closed form

        local  (10 × 2 mm, return directly under the trace)   L =  11 nH
        split  (60 × 40 mm, via the inlet star)               L = 200 nH
        worst  (100 × 45 mm, 10HP corner to corner)           L = 305 nH

        net capacitance C = DAC pin 3 pF + AHCT C_o 15 pF + trace ~10 pF = 28 pF
        [datasheet SBAS430E p.4] [datasheet SCLS264O p.4]

        series R = AHCT R_on: 70 Ω rising (p-side), 33 Ω falling (n-side)   [§1.2]

        Q = (1/R)·√(L/C),  overshoot = exp(−πζ/√(1−ζ²)), ζ = 1/(2Q)
```

| Return | Edge | `f_ring` | `Q` | Overshoot | Pin voltage |
|---|---|---|---|---|---|
| local, 11 nH | rising | 282 MHz | 0.29 | 0 % | 5.00 V |
| local, 11 nH | falling | 282 MHz | 0.61 | 1 % | −0.06 V |
| **split, 200 nH** | rising | 67 MHz | 1.21 | **24 %** | **6.20 V** |
| **split, 200 nH** | falling | 67 MHz | 2.56 | **53 %** | **−2.67 V** |

**Against a digital-input absolute maximum of `AVDD` + 0.3 = 5.51 V and
−0.3 V** `[datasheet SBAS430E p.2]`.

That is the cost, and it is not a noise-hygiene preference. **The return-path
choice decides whether the DAC's digital pins stay inside their absolute
maximum rating.** The falling edge is the worse one, because the AHCT's n-side
is half the impedance of its p-side — and `SYNC` falling is the edge that frames
the word, which the page already identifies as the one failure that does not
self-heal `[repo hardware/module/digital-and-supervision.md:96-102]`.

Secondary cost, for completeness: the charge moved per edge is
`Q = C·V` = 28 pF × 5 V = 140 pC `[calc]`, and at ~2.4 × 10⁶ edges/s across the
three nets that is **~340 µA of average current** `[calc]` injected into
whichever pour carries it. Through a copper pour that is sub-microvolt and
irrelevant. **The DC/IR argument that governs `PWR_GND` does not govern
`DIG_GND`** — 360 mA versus 340 µA, a factor of a thousand. `DIG_GND` is an
*inductive* problem, and inductance is set by loop area, not by which star the
net eventually reaches.

### 2.3 Recommended tie

> **Tie `U-LVL-MOD` pin 7 (GND) to the DAC's `GND` net, at the DAC's GND pin.**
> Place the shifter immediately beside the DAC. Bring `DIG_GND` from the
> etherCON to that same node on its own copper, with its return pour directly
> under its trace for the whole run, and let it make **exactly one** connection
> to the analog region — **at the DAC, not at the power-inlet star.**

This keeps both loops local:

- **Cable-side loop** — the 2 m line's charging current, `3.3 V / (100 + 40 + 100)`
  = 13.8 mA per conductor during each transit `[calc]` — returns in `DIG_GND`
  under its own trace, from the etherCON to the shifter's GND pin.
- **Board-side loop** — the 140 pC edges of §2.2 — is 11 nH, `Q` ≤ 0.61, no
  overshoot.

And it satisfies the three arguments that are currently in conflict, rather than
picking a winner among them. `PWR_GND`'s 360 mA still runs to the inlet on its
own copper, untouched — that argument is about a current a thousand times larger
and is not affected.

### 2.4 Recommendation on `figures.yaml: dig-gnd-topology`

The entry records three mutually exclusive answers and says the dispute is
`decided_by` the 2-layer-vs-4-layer decision
`[repo config/figures.yaml:235-250]`. **It is not, and that framing is what has
kept it open.** The three candidates are answering two different questions:

| Candidate | Really asserts | Verdict |
|---|---|---|
| "its own path to the star" (ADR 0004:627) | *routing*: `DIG_GND` shares copper with nothing on its way | **keep** — it is about isolation from `PWR_GND` |
| "the pour directly under its trace" (power-entry.md:495-498) | *return geometry*: minimum loop area | **keep** — §2.2 shows this is the binding constraint |
| "the analog star, single tie" (this page:53) | *tie count and location*: one, and only one | **keep the count, relocate it** — to the DAC, not the inlet |

They are compatible. **Proposed value for the entry:**

> `value: "DIG_GND runs etherCON → DAC/shifter island on its own copper, return
> pour directly under the trace, joining the analog return at exactly one point:
> the DAC8568's GND pin. It does NOT run to the power-inlet star."`
> `status: settled`
> `owner: hardware/module/digital-and-supervision.md`
> `derivation: "DAC8568CIPW has a single GND pin for all circuitry (SBAS430E
> p.6), so the SPI return is in the analog region whatever we do. The only free
> variable is loop area, and a 200 nH loop rings the DAC's digital pins to
> 6.2/−2.7 V against a 5.51/−0.3 V abs max."`

This also **unblocks the 2-layer-vs-4-layer decision instead of depending on
it**: with the tie at the DAC, no boundary-crossing trace loses its return, and
the two-layer option stops being self-contradictory. Four layers remains better
for other reasons; it is no longer a prerequisite.

`ADR 0004:627` must change in the same commit, and `power-entry.md`'s claim
that *"ADR 0004 was corrected on this point"* — which `figures.yaml` already
records as false — becomes true.

---

## 3. Impedance and drive

### 3.1 What the shifter drives

Per output, DC and AC:

| Load term | Value | Cite |
|---|---|---|
| DAC input leakage | ±1 µA | `[datasheet SBAS430E p.4]` |
| DAC pin capacitance | 3 pF | `[datasheet SBAS430E p.4]` |
| AHCT own `C_o` | 15 pF max | `[datasheet SCLS264O p.4]` |
| `R-SPI-PULL` DAC side | 10 kΩ → 500–521 µA when opposed | `[repo hardware/bom.csv:49]` `[calc]` |
| trace | ~10 pF `[from memory]` | — |

```
[calc]  worst DC load = 521 µA (SYNC low against the 10 k pull-up to AVDD 5.21 V)
        = 6.5 % of the ±8 mA recommended output current
        V_OL at 521 µA ≈ 0.10 V + 521 µA × 42.5 Ω = 0.122 V
        against V_INL = 1.563 V  → 1.44 V of margin              ✓
        V_OH at 500 µA ≈ V_CC − 500 µA × 87.5 Ω = V_CC − 0.044 V
        = 4.96 V against V_INH = 3.256 V → 1.70 V of margin       ✓
```

Both margins are >1.4 V. **10 kΩ is right on the DAC side** and could be 4.7 kΩ
if anyone wanted more static immunity; there is no reason to.

### 3.2 F-05 — the one place the DAC-side numbers get tight

`AVDD` is set by `R-REG-SET` selected on the bench at E7, with a **hard floor of
5.00 V** for the C grade `[repo config/figures.yaml:128]` `[repo hardware/bom.csv:12]`.
The shifter runs from raw bus +5 V `[repo hardware/module/power-entry.md:50]`
and its `V_OH` under a 500 µA load is `V_CC` − 44 mV `[calc, §3.1]`.

```
[calc]  worst case: AVDD trimmed to its 5.00 V floor
        digital input abs max = 5.00 + 0.3 = 5.30 V     [datasheet SBAS430E p.2]
        bus +5 V at a +5 % rack tolerance = 5.25 V      [from memory]
        shifter V_OH ≈ 5.25 − 0.044 = 5.21 V
        margin = 90 mV
```

90 mV, and negative for any rack whose +5 V sits above 5.35 V. This is a
continuous absolute-maximum condition, not a transient. The same three resistors
that fix F-03 fix this:

> **Proposed: `R-DAC-SER` ×3, 220 Ω, 0805, 1 %** — one each on `SCLK`, `DIN` and
> `SYNC` between the shifter's outputs and the DAC's pins.

Four jobs for three parts:

1. **F-05**: overdrive current becomes `(5.35 − 5.30)/220` = **0.23 mA** `[calc]`,
   into a pin whose clamp will take it, instead of an uncontrolled violation.
2. **F-03 backstop**: with 220 Ω added, even the 200 nH split loop gives
   `Q` = 0.43 and **zero overshoot** `[calc]` — so the board survives a layout
   that ignores §2.3.
3. Damps the shifter→DAC trace, which at 33 Ω n-side drive into a ~55 Ω
   microstrip `[from memory]` is otherwise an undamped source.
4. Cuts the edge current circulating in the ground loop by ~3×.

Cost: `τ` = 220 Ω × 28 pF = **6.2 ns** `[calc]`, which is 2.5 % of a 250 ns half
period and close to the `t_R` = `t_F` = 3 ns the DAC's timing table assumes
`[datasheet SBAS430E p.7 note 1]`. The DAC's inputs are Schmitt-triggered
`[datasheet SBAS430E p.6]`, so a softened edge costs nothing there.

### 3.3 F-02 — the cable-side `CS` pull-up, and the 430 µA

The current first. `bom.csv` claims that pulling cable-side `CS` to +5 V through
10 kΩ drives "430 µA continuously through the unpowered ESP32's input clamp",
and that the node then sits at ~0.7 V `[repo hardware/bom.csv:49]`.

```
[calc]  ESP32 pad clamp to an unpowered rail conducts at ≈ 0.7 V [from memory]
        (5.0 − 0.7) / 10 kΩ = 430 µA        ✓ reproduces exactly
```

**Confirmed.** Now the part nobody checked:

```
[calc]  (3.3 − 0.7) / 10 kΩ = 260 µA
```

**Pulling to 3V3 does not fix the problem, it scales it by 0.6.** The node still
clamps at ~0.7 V, so the BOM's second reason — *"the node sits at ~0.7 V so 'CS
idle high' is not even achieved"* — applies to the 3V3 pull with equal force.
And 0.7 V is below `V_IL` = 0.8 V `[datasheet SCLS264O p.3]` by 100 mV, so the
shifter reads `CS` **asserted** in the design's declared normal resting state
`[repo docs/decisions/0004-cv-interface-module.md:368-374]` and drives the DAC's
`SYNC` actively low — a shift register left enabled indefinitely. Benign only
because `SCLK` is pulled down at both ends and never edges.

**And `3V3` is not a net on this board.** The module's rails are, in full:
umbilical +12 V behind the LT1641, module analog +12 V, module analog −12 V,
bus +5 V (the 74AHCT125 alone) and the LM317's `AVDD`
`[repo hardware/module/power-entry.md:20-53]`. A grep of `hardware/module/**`
finds `3V3` nowhere. The BOM row specifies an **unbuildable net**, and it is the
only instruction in the row that a netlist cannot satisfy.

> **Proposed: cable-side `CS` pull-up becomes 100 kΩ to bus +5 V.**

```
[calc]  unplugged:  V_node ≥ 5.0 − (1 µA × 100 kΩ) = 4.9 V
                    against V_IH 2.0 V → 2.9 V of margin        ✓
                    (1 µA is the AHCT125 input leakage max, SCLS264O p.4)
        plugged, instrument off:  (5.0 − 0.7)/100 kΩ = 43 µA
                    a 10× reduction on the 430 µA the row objects to,
                    and 6× better than the 3V3 pull it proposes
```

43 µA is below any plausible phantom-powering threshold for an ESP32-S3 board
whose 3V3 rail carries an ME6217 LDO and its decoupling
`[repo datasheets/MANIFEST.csv:62]`. **The value moves, not the rail** — which
is the change that can actually be drawn.

The asymmetry with the other two is deliberate and should be stated on the page:
`SCLK` and `MOSI` pull **down**, in the same direction the ESP32's clamp pulls,
so they are not fighting it and 10 kΩ is free. Only `CS` pulls against the clamp.
**Keep `R-SPI-PULL` at qty 6, change one value.** If the BOM prefers a single
value, 100 kΩ on all six is also fine: the DAC-side numbers in §3.1 have >1.4 V
of margin and 100 kΩ only improves the shifter's DC loading.

### 3.4 F-10 — the DAC-side three have outlived their stated reason

The page justifies them with *"with `OE` disabled the buffer's outputs are
Hi-Z"* `[repo hardware/module/digital-and-supervision.md:123]`, and declares
`OE` **tied enabled** twenty-four lines later `[repo hardware/module/digital-and-supervision.md:147]`.
The state the parts are bought for does not exist. This is the class-4 defect
`CLAUDE.md` describes — an argument surviving its own refutation — on one page,
twenty-four lines apart, and no grep finds it.

**The parts are still right; the reason is different and it is stronger.**
SCLS264O's own description says *"To ensure the high-impedance state during
power up or power down, `OE` should be tied to `V_CC` through a pullup
resistor"* `[datasheet SCLS264O p.1]` — advice this design deliberately
contradicts. With `OE` hard low, the shifter's outputs are **undefined, not
Hi-Z, while bus +5 V ramps**, and `AVDD` (LM317 off module analog +12 V) and
bus +5 V come up on different branches with no sequencing statement anywhere.
The DAC-side pulls are what hold `SYNC` high and `SCLK`/`DIN` low through that
window. Restate the justification as **power-sequencing between bus +5 V and
`AVDD`, plus an absent or dead shifter** — and note the small consequence that
`AVDD` (5.21 V) exceeds bus +5 V, so the `SYNC` pull-up back-feeds ~21 µA into
the +5 V rail through the AHCT output clamp in normal operation, and ~450 µA
per line if bus +5 V is absent `[calc]`. Both are trivial against the ±20 mA
output clamp rating `[datasheet SCLS264O p.3]`.

---

## 4. Current draw for this section

### 4.1 DAC8568, on `AVDD`

```
                                          typ      max
  Normal mode, internal reference ON     1.25 mA   2.0 mA     ← this design
  Normal mode, internal reference OFF    0.95 mA   1.4 mA
  All power-down modes                   0.18 µA   3 µA
  (AVDD = 3.6 V to 5.5 V, V_INH = AVDD and V_INL = GND)
```
`[datasheet SBAS430E p.5, power requirements]`

**The internal reference is enabled** — the pitch full scale is set by it
`[repo hardware/module/power-entry.md:78-80]` — so **2.0 mA max** is the number
to budget, not 1.4 mA.

Two riders the corpus should carry:

1. *"The internal reference is powered off/down by default and remains that way
   until a valid reference-change command is executed"* `[datasheet SBAS430E
   p.38]`, and *"when performing a power cycle to reset the device, the internal
   reference is switched off (default mode)"* `[datasheet SBAS430E p.31]`.
   `firmware/README.md` already treats the reference-enable as a register to
   re-assert periodically `[repo firmware/README.md:77-79]` — correct, and the
   datasheet is the reason.
2. The `I_DD` figures are specified with `V_INH` = `AVDD` and `V_INL` = GND.
   SBAS430E p.33 warns: *"To assure the lowest power consumption of the device,
   care should be taken that the levels are as close to each rail as possible."*
   The six `R-SPI-PULL` resistors are what guarantee that at idle, and the
   74AHCT125 is what guarantees it while driving — a second, previously
   unstated, reason the level shifter exists.

### 4.2 74AHCT125, on bus +5 V

Three contributions, and the corpus names none of them.

```
[calc]  quiescent    I_CC ≤ 20 µA                        [SCLS264O p.4]

        dynamic      I = (C_pd + C_L) · V_CC · f,  C_pd = 14 pF [SCLS264O p.5]
                     C_L ≈ 15 pF (DAC 3 pF + trace 10 pF + margin)
                     SCLK  at 2 MHz : 29 pF × 5 V × 2.0e6   = 290 µA (in burst)
                     MOSI  at ≤1 MHz: 29 pF × 5 V × 1.0e6   = 145 µA (in burst)
                     SYNC  12 kHz    :                       =   3.5 µA
                     duty = 96 µs of 250 µs = 38.4 %  [repo carrier.md:647]
                     → average 168 µA

        ΔI_CC        1.5 mA PER INPUT held at a TTL level rather than a rail
                                                          [SCLS264O p.4]
```

**`ΔI_CC` is the dominant term and it is invisible in the corpus.** The
74AHCT125's inputs are driven by 3.3 V logic — which is the entire point of the
part — and 3.3 V is neither `V_CC` nor GND, so every HIGH input pays up to
1.5 mA:

```
[calc]  worst case, all three inputs high simultaneously: 4.5 mA
        realistic average:
          SCLK  high 50 % of a 38.4 % burst = 19.2 %  → 0.29 mA
          MOSI  same                                   → 0.29 mA
          CS    high whenever not framing ≈ 62 %       → 0.93 mA
                                                  total ≈ 1.5 mA
        four OE inputs tied to GND: no contribution
```

**Section total, 74AHCT125: ~1.7 mA average, 4.7 mA worst case, on bus +5 V.**
Small, but it is 85× the quiescent figure anyone would have assumed from `I_CC`,
and bus +5 V is the rail three reviewers want to delete
`[repo hardware/module/digital-and-supervision.md:108-116]`. If that rail is ever
derived locally from +12 V by "one TO-92 and two capacitors", **the TO-92 must be
sized for ~5 mA at a 7 V drop = 35 mW**, not for the 20 µA an `I_CC` reading
suggests. That is the number that argument needs and does not have.

### 4.3 The pull resistors

| Pull | Rail | Current when opposed | Duty | Average |
|---|---|---|---|---|
| cable `SCLK` ↓ 10 k | `DIG_GND` | 330 µA `[calc]` | 19 % | 63 µA (instrument's rail) |
| cable `MOSI` ↓ 10 k | `DIG_GND` | 330 µA | 19 % | 63 µA (instrument's) |
| cable `CS` ↑ **100 k** (proposed) | bus +5 V | 50 µA `[calc]` | 38 % | 19 µA |
| DAC `SCLK` ↓ 10 k | DAC GND | 500 µA `[calc]` | 19 % | 96 µA |
| DAC `DIN` ↓ 10 k | DAC GND | 500 µA | 19 % | 96 µA |
| DAC `SYNC` ↑ 10 k | `AVDD` | 521 µA `[calc]` | 38 % | 200 µA |
| `R-CLR-PU` 10 k | `AVDD` | 0 (leakage only, ±1 µA) | — | ~0 |
| `R-LDAC` 10 k | `AVDD` | 0 (leakage only) | — | ~0 |

### 4.4 Section total

| Rail | Average | Worst case |
|---|---|---|
| bus +5 V | **~1.9 mA** | ~4.8 mA |
| `AVDD` (LM317) | **~2.3 mA** | ~2.6 mA (DAC 2.0 mA max + 0.52 mA pull) |
| `DIG_GND` return | ~0.35 mA avg, **~45 mA peak for ~20 ns per edge** `[calc, §2.3]` | — |

The DAC's **output** currents — six channels into the pitch and mod stages, up
to ±20 mA capability `[datasheet SBAS430E p.3]` — belong to those pages, not
this one.

---

## 5. The page's two open items

### 5.1 "Whether to restore link supervision at all, and at what cost"

> **Recommendation: accept the loss. Do not restore the comparator.** Then take
> F-07, which buys back half the coverage for zero parts, and F-06, which makes
> `CLR` safe enough to be worth wiring to anything.

Four reasons, in order of weight.

**(a) F-08 — the accepted loss is not what the page says it is.** The page's
table says cable-unplugged-mid-note means *"the DAC holds and the rack drones"*
`[repo hardware/module/digital-and-supervision.md:176]`. The breath receiver
biases both in-amp inputs to module analog ground through `R4`/`R5`, 1 MΩ each,
*"without these the in-amp's inputs float when the cable is unplugged and it
saturates to a rail"* `[repo hardware/module/breath-receive-stage.md:159]`. With
the cable open, `V_BREATH − V_AGND` → 0, and the stage's own transfer function
gives `Vout = 0 V at rest` `[repo hardware/module/breath-receive-stage.md:57]`.

```
[calc]  differential settling on cable loss:
        τ = (R4 + R5) · C_diff = 2 MΩ × 15 nF = 30 ms
        → breath CV reaches 5 % of its value in ~90 ms
```

**Pull the umbilical mid-note and the breath jack falls to zero in about a
tenth of a second.** In the design's own intended patch — breath into a VCA,
which is what ADR 0004 assumes when it calls breath *"the one jack that is
usually driving a VCA"* `[repo docs/decisions/0004-cv-interface-module.md:498]` —
the note fades out. Pitch and the mods do hold, but they hold *silently*.

"The rack drones" is true only for a patch that deliberately takes amplitude
from something other than breath. That is a real case and it should stay in the
table — but it is a **patching** exposure, not an unconditional one, and the
page currently prices the restoration against the wrong failure.

**(b) Restoring supervision makes the worst state in the design reachable by
accident.** The restoration drives `CLR` `[repo hardware/module/digital-and-supervision.md:203-207]`.
`firmware/README.md` is explicit that `CLR` is *"the most load-bearing firmware
constraint in the repo"*, because exiting it puts every mod jack at
`4 × Vdac` ≈ **+11.45 V** until channel 7 is rewritten
`[repo firmware/README.md:56-58]`. Today `CLR` is asserted by exactly two
things, both deliberate: the DAC's power-on reset and the `LK-CLR` pad
`[repo firmware/README.md:60-64]`. **A comparator watching a 2 m analog line
that the page itself says has a threshold sitting inside the breath signal's own
range** `[repo hardware/module/digital-and-supervision.md:140-143]` **would add a
third, and it would be the only one that can fire while someone is playing.**
The supervision trades a silent hold for a loud, rail-clipped transient on four
jacks. That trade is bad, and nobody in the corpus has priced it.

**(c) The cost is four parts with no rows, in a module with no room.** LM311,
two decoupling caps, `R-PRESENCE`, 74AHCT14
`[repo hardware/module/digital-and-supervision.md:196-200]`, against a panel at
107 mm of ~110 mm usable `[repo docs/decisions/0004-cv-interface-module.md:657-659]`.
And §1.5 removes one of the 74AHCT14's three jobs: at 100 Ω the AHCT125's
`Δt/Δv` limit is met with an order of magnitude to spare, so **there is no
edge-cleanup case for it.** The "one part, three jobs" argument is now a
two-job argument, and both remaining jobs belong to a circuit this review
recommends against.

**(d) It must still answer the three faults that deleted it**, and two of them —
threshold inside the breath range, failing toward "present" — are properties of
*watching the breath line*, not of the implementation
`[repo docs/decisions/0004-cv-interface-module.md:426-434]`.

#### F-09 — but the page's stated recovery does not exist, and that must be fixed

> *"pull the umbilical mid-note and the rack holds that note until you flip the
> module's toggle"* `[repo hardware/module/digital-and-supervision.md:181-183]`

**Flipping the toggle does not park the outputs.** The toggle gates the LT1641,
which gates the **umbilical's** +12 V only `[repo hardware/module/power-entry.md:26-46]`.
`AVDD` comes from the LM317 on the *module analog* +12 V branch, behind `D2`
`[repo hardware/module/power-entry.md:48-50]`, which the toggle does not touch.
The DAC stays powered and keeps holding its registers. The only recoveries that
actually exist today are the `LK-CLR` solder pad — inside the module, behind
four screws — and a rack power cycle.

#### F-07 — the recommended restoration, for zero parts

`PWRGD` on the LT1641-1 is *"Open Collector Output to GND. The `PWRGD` pin is
pulled low whenever the voltage at the FB pin falls below the High-to-Low
threshold voltage. It goes into a high impedance state when the voltage on the
FB pin exceeds the Low-to-High threshold"* `[datasheet LT1641.pdf p.5]`, with
`V_OL` ≤ 0.4 V at 2 mA `[datasheet LT1641.pdf p.2]` and `t_PHL(FB)` = 3.2 µs typ
`[datasheet LT1641.pdf p.3]`. Leakage when released is ≤ 10 µA at 80 V
`[datasheet LT1641.pdf p.2]`.

> **Proposed: tie `PWRGD` to `N_CLR` through a 0 Ω link `LK-PWRGD-CLR`.**

- `R-CLR-PU` 10 kΩ to `AVDD` is already there and becomes the pull-up the
  open collector needs `[repo hardware/bom.csv:68]`.
- Asserted: `V_OL` at 521 µA is well under the 0.4 V/2 mA spec, against
  `V_INL` = 1.563 V `[calc]` — over 1.1 V of margin.
- Released: 10 µA × 10 kΩ = 0.1 V of droop → `CLR` at 5.11 V against
  `V_INH` = 3.256 V `[calc]` — 1.85 V of margin.
- `PWRGD` is referenced to `PWR_GND` and `CLR` to the DAC's ground. The DC
  offset between them is microvolts at 360 mA across a pour; the
  falling-edge-triggered, **non-Schmitt** `CLR` pin
  `[datasheet SBAS430E p.6 — SYNC, DIN and SCLK are named as Schmitt inputs,
  CLR and LDAC are not]` is the part that wants protecting, which is why the
  100 nF below is recommended alongside.

This converts the page's supervision table:

| Failure | Page today | With `PWRGD` → `CLR` |
|---|---|---|
| Firmware hangs above the output loop | not caught | not caught (nothing ever caught it) |
| Cable unplugged mid-note | not caught | **not caught** — unplugging removes a load, the rail stays up |
| Instrument loses power mid-note | not caught | not caught by this — the module powers the instrument |
| **Load switch latches off mid-note** | not caught | **caught** |
| **Toggle switched off mid-note** | (absent from the table) | **caught** — and this is F-09's missing recovery |
| Module powered, instrument off | pulls | pulls, unchanged |

Two rows, one net, zero parts. It also holds every output at 0 V through the
whole rack power-up ramp, which is strictly better than today.

Three riders:
1. **`LK-PWRGD-CLR` must be a removable 0 Ω, not a trace.** With the toggle off
   during E7–E10 standalone bring-up, `CLR` would otherwise be asserted and the
   module would produce no CV — the same lockout that killed the presence
   comparator `[repo docs/decisions/0004-cv-interface-module.md:429-431]`. A link
   that lifts answers it; so does "toggle ON during bring-up", but the link is
   what makes that recoverable when someone forgets.
2. **Adopt F-06 first.** Making `CLR` reachable is only safe once exiting it is
   atomic.
3. **Add 100 nF from `N_CLR` to the DAC's GND.** `τ` = 10 kΩ × 100 nF = 1 ms
   `[calc]`, so a `PWR_GND` transient cannot glitch a non-Schmitt edge-triggered
   pin, while `LK-CLR` and `PWRGD` both discharge it in nanoseconds and easily
   meet `t15` ≥ 80 ns `[datasheet SBAS430E p.7]`. One 0805, and `C-DECOUPLE` is
   already 100 nF X7R 0805.

### 5.2 "An ESP32-S3 NVS commit or OTA write disables the instruction cache"

**The page's conclusion is right and its reasoning is now stronger, not weaker.**
With the watchdog deleted there is no `CLR` to fire mid-stall, so the outcome is
a *stalled refresh*: the jacks hold their last value for the duration, which is
benign `[repo hardware/module/digital-and-supervision.md:225-230]`.

Three things the page should add.

**(a) The magnitude.** ESP-IDF disables the instruction cache on both cores for
the duration of any SPI-flash operation; a page program is order 1 ms and a
4 kB sector erase order 30–50 ms `[from memory — no Espressif document is
banked, `datasheets/MANIFEST.csv` has the Waveshare board schematic and the
ME6217 LDO and nothing from Espressif]`. Against a 250 ns... against a **250 µs**
loop period `[repo firmware/README.md:22]`, a sector erase is **120–200 missed
passes.** An OTA image write is thousands.

**(b) IRAM alone is not sufficient, and saying "the DAC service routine belongs
in IRAM" understates what that costs.** For the refresh to survive a cache
disable, *all* of it must be off flash: the ISR (`IRAM_ATTR`), everything it
calls, and its constant data in DRAM rather than `.rodata`. ESP-IDF's SPI master
driver only tolerates this if the interrupt is allocated with
`ESP_INTR_FLAG_IRAM` and no callback touches flash `[from memory]`. That is a
real constraint on the driver choice, not an attribute on one function.

**(c) The cheap total answer, which costs nothing.** **Gate NVS commits and OTA
writes on "not playing."** The instrument digitises breath anyway
`[repo hardware/module/digital-and-supervision.md:150-151]`; a rule of "no flash
writes while breath has been above threshold in the last N seconds, and never
during OTA except from an explicit maintenance mode" removes the exposure
entirely and needs no IRAM discipline. ADR 0012 puts configuration on the
display, which is already a not-playing context. **Recommend both**: the policy
because it is free and total, IRAM because it bounds the residual.

One correction to the page's framing: with F-07 adopted, a stall still does not
assert `CLR` — `PWRGD` watches the umbilical rail, not SPI traffic. The benign
direction is preserved. This is a further argument for `PWRGD` over any
traffic-counting watchdog, and it is the argument the deleted 74HC123 failed
`[repo hardware/module/digital-and-supervision.md:164-168]`.

---

## 6. `R-LDAC` and `R-CLR-PU`

### 6.1 F-01 — `R-LDAC` is pulled the wrong way, and it is the CLR defect again

The page draws `LDAC ◄── [R-LDAC] 10k` to `AVDD`, annotated *"PULL-UP. Active
low. TIED, not driven."* `[repo hardware/module/digital-and-supervision.md:49-50]`,
and `bom.csv` agrees: *"Ties the DAC8568 `LDAC` pin to its inactive level"*
`[repo hardware/bom.csv:129]`.

SBAS430E p.38, **SYNC INTERRUPT**, verbatim:

> *"In synchronous mode, data are updated with the falling edge of the 32nd SCLK
> cycle, which follows a falling edge of SYNC. For such synchronous updates, the
> LDAC pin is not required and **it must be connected to GND permanently**."*

And SBAS430E p.38, **LDAC FUNCTIONALITY**, on the internal `LDAC` register whose
*"default value for each bit, and therefore for each DAC channel, is zero"*:

> *"If the LDAC register bit is set to '1', it overrides the LDAC pin (the LDAC
> pin is internally tied low for that particular DAC channel) and this DAC
> channel updates synchronously after the falling edge of the 32nd SCLK cycle.
> However, **if the LDAC register bit is set to '0', the DAC channel is
> controlled by the LDAC pin.**"*

Put together: the `LDAC` register powers up at `0x00`, every channel is therefore
gated by the pin, and the pin is held **high**. TI's instruction for exactly this
use of the part is the opposite level.

**This is the `CLR` pull-down defect of the last redraw, mirrored.** That one
asserted an active-low pin permanently and gave six dead outputs
`[repo hardware/module/digital-and-supervision.md:72-77]`; this one de-asserts a
transfer-enable permanently and risks six outputs that never move at all. Both
are "the single cheapest way in the whole design to end up with a module that
does nothing", and neither is visible to a grep.

The exposure is conditional — it depends on whether the DAC8568's
`write-and-update` command paths bypass the pin in silicon, which SBAS430E does
not say — and with no `MISO` **firmware can never find out**
`[repo hardware/module/digital-and-supervision.md:99-100]`. Depending on
undocumented silicon behaviour on a write-only link is not a position to build a
board from.

> **Proposed: `R-LDAC` becomes a 0 Ω link tying `LDAC` to the DAC's `GND` pin.**
> Same refdes, same 0805 footprint, description becomes *"Strap tying the
> DAC8568 LDAC pin to GND, per SBAS430E p.38"*. If the retrofit option matters
> more than certainty, 10 kΩ to GND is acceptable — ±1 µA of leakage gives
> 10 mV `[calc]`, far below `V_INL` = 1.563 V — but a hard tie also immunises an
> edge-triggered, non-Schmitt pin against coupling from the 2 MHz bus beside it.

Two corrections that follow on the page:

- *"If E10 finds that audible it becomes a GPIO, and the pin is already broken
  out"* `[repo hardware/module/digital-and-supervision.md:252-253]`. **It is not
  broken out** — the drawing shows `LDAC` reaching one resistor and nothing else,
  with no pad, where `CLR` has an explicit `LK-CLR` `[repo hardware/module/digital-and-supervision.md:42-50]`.
  **And there is nothing to drive it with**: the module has no processor, and all
  eight umbilical conductors are allocated `[repo config/figures.yaml:112-114]`.
  A hardware `LDAC` needs a ninth conductor. The escape hatch the bullet names
  does not exist.
- The page should say what the correct inactive level *is*. "Active low, held
  inactive" is a reasonable-sounding sentence that is wrong for this pin in this
  mode, and it is the sentence that produced the defect.

### 6.2 F-06 — atomic updates across six channels are free, and the corpus does not know it

> *"a hardware `LDAC` was considered and declined, so the six populated channels
> update as each word lands rather than together. The cost is real and accepted —
> every exit from `CLR` throws intermediate values at the mod jacks for
> 100–200 µs and **no write order avoids it**."*
> `[repo hardware/module/digital-and-supervision.md:248-252]`

First, the 100–200 µs checks out:

```
[calc]  32 bits at 2 MHz                = 16.00 µs per word
        six populated channels          = 96.0 µs of clocking
        + t4 (SYNC high ≥ 80 ns) and ESP-IDF inter-transaction overhead
        ≈ 100 µs, and up to one full 250 µs pass in the worst alignment
        + DAC settling 5 µs typ / 10 µs max, 1/4→3/4 scale unloaded
                                              [datasheet SBAS430E p.3]
```
`[repo hardware/controller/carrier.md:647]` books the same 96.0 µs.

Second, **"no write order avoids it" is true and "no write order improves it"
is false.** From `Vout = 4·Vdac − 3·V_ref` with `V_ref` = 3.3333 V from channel 7
`[repo hardware/module/mod-channels.md:6,101]`:

| Order out of `CLR` | Mod jack sits at | For |
|---|---|---|
| channel 7 **first** | `4·0 − 3×3.3333` = **−10.000 V** — the bottom of the stage's own legal range | 16–80 µs |
| channel 7 **last** | `4·Vdac − 0` = up to **+11.45 V**, clipped against +12 V `[repo firmware/README.md:56-58]` | 16–96 µs |

Same 10 V excursion, but one stays inside the op-amp's linear range and the
other saturates the OPA2197 against the rail and presents >+11 V to whatever is
patched. **Write channel 7 first. One line of firmware, zero parts.**

Third, and this is the finding: **SBAS430E provides a software simultaneous
update, and it makes the whole transient disappear.** Table 11 p.36 lists, for
each channel, *"Write to DAC input register Ch X and update all DAC registers
(SW LDAC)"* — control bits `C3..C0 = 0010` `[datasheet SBAS430E p.36]`, and the
LDAC section confirms *"Alternatively, all DAC outputs can be updated
simultaneously using the built-in software function of LDAC"* `[datasheet
SBAS430E p.38]`.

> **Proposed refresh pattern, per 250 µs pass:**
> five words with *"write to DAC input register Ch X"* (no update), then the
> sixth — channel 7, the shared `V_ref` — with *"write to input register and
> update **all** DAC registers"*. All six outputs step together on the 32nd
> falling edge of the last word.

- **Same six words.** The latency budget is unchanged `[repo hardware/controller/carrier.md:647]`.
- **Same parts.** No `LDAC` conductor, no GPIO, no ninth wire.
- **The `CLR`-exit window goes from 100–200 µs to zero.** The jacks step from
  their parked 0 V straight to their correct values.
- It removes the same hazard on *every* pass, not only on `CLR` exit — including
  the one `firmware/README.md` spends a whole section on, where a `CLR` lands
  mid-pass `[repo firmware/README.md:44-70]`.
- It is fully compatible with `LDAC` strapped to GND per F-01: the pin low means
  it can never gate anything, and the `SW LDAC` command does the sequencing.

**The page's closed `LDAC` bullet should be reopened and re-closed differently.**
Its conclusion — no hardware `LDAC` — is right. Its stated consequence — that
atomic updates are therefore impossible and the transient is unavoidable — is
wrong, and it is wrong in the direction that made E10 carry a risk it does not
need to.

### 6.3 `R-CLR-PU` — verified correct

`CLR` is *"Asynchronous clear input"*, active low, and *"the CLR pin is
falling-edge triggered; therefore, the device exits clear code mode on the 32nd
falling edge of the next write sequence"* `[datasheet SBAS430E pp.6, 40]`.
`t15`, `CLR` pulse width low, ≥ 80 ns `[datasheet SBAS430E p.7]`.

| Check | Result |
|---|---|
| Polarity: pull-**up** holds it inactive | ✓ correct `[repo hardware/bom.csv:68]` |
| Rail: `AVDD`, not bus +5 V | ✓ correct — abs max is `AVDD` + 0.3 `[datasheet SBAS430E p.2]`, so a bus-rail pull-up on a 5.21 V part would be right only by luck |
| Level: 10 kΩ × ±1 µA leakage = 10 mV droop → 5.20 V vs `V_INH` 3.256 V | ✓ `[calc]` |
| `LK-CLR` pad to GND: 5.21 V / 10 kΩ = 521 µA through the link, `t15` met instantly | ✓ `[calc]` |
| Clear-code register left at default → clear parks all channels at **zero scale**, and grade C's power-on reset does the same | ✓ `[datasheet SBAS430E p.38]` `[repo hardware/bom.csv:12,68]` — so both `CLR` and power-on put the mod jacks at `4·0 − 3·0` = **0 V**, not at a rail. Worth stating on the page; it is the reason the parked state is quiet |
| Glitch immunity on a non-Schmitt, edge-triggered pin beside a 2 MHz bus | **gap** — see the 100 nF in §5.1 |

**`R-CLR-PU` is right. Add the 100 nF, especially if F-07 is adopted.**

---

## 7. Netlist readiness

Every net in this slice, with its canonical name and its state.

| Canonical net | Nodes | State |
|---|---|---|
| `SCLK_CAB` | etherCON pin 4 — `R-SPI-PULL` ↓10k — `U-LVL-MOD` 1A | **ambiguous today** — called `SCLK` on both sides of the buffer |
| `MOSI_CAB` | etherCON pin 5 — `R-SPI-PULL` ↓10k — `U-LVL-MOD` 2A | same |
| `CS_CAB` | etherCON pin 7 — `R-SPI-PULL` ↑**100k to +5V_BUS** (F-02) — `U-LVL-MOD` 3A | **blocked** on F-02 |
| `SCLK_DAC` | `U-LVL-MOD` 1Y — `R-DAC-SER` (proposed) — `R-SPI-PULL` ↓10k — `U-DAC` pin 16 | needs a distinct name |
| `DIN_DAC` | `U-LVL-MOD` 2Y — `R-DAC-SER` — `R-SPI-PULL` ↓10k — `U-DAC` pin 15 | same |
| `SYNC_DAC` | `U-LVL-MOD` 3Y — `R-DAC-SER` — `R-SPI-PULL` ↑10k to `AVDD` — `U-DAC` pin 2 | same |
| `N_CLR` | `R-CLR-PU` ↑10k to `AVDD` — `LK-CLR` pad — `C-CLR` 100 nF (proposed) — `LK-PWRGD-CLR` (proposed) — `U-DAC` pin 9 | ready once F-07 is decided |
| `N_LDAC` | `R-LDAC` → **GND** (F-01) — `U-DAC` pin 1 | **blocked** on F-01 |
| `DIG_GND` | etherCON pin 8 — `U-LVL-MOD` pin 7 — single tie at `U-DAC` pin 14 | **blocked** on F-03 / §2.4 |
| `+5V_BUS` | IDC +5 V — `FB4` — `C4` — `U-LVL-MOD` pin 14 — `C-DECOUPLE` | ready |
| `AVDD` | LM317 out — `U-DAC` pin 3 — `C-DECOUPLE` — `R-CLR-PU` — `SYNC_DAC` pull-up | ready |
| `N_OE` | `U-LVL-MOD` pins 1, 4, 10, 13 → GND | **which ground?** resolves with F-03 |
| `U-LVL-MOD` 4A (spare) | unassigned | **F-14** — SCLS264O p.3 Note 4 requires `V_CC` or GND. Recommend 4A → GND and **4OE → `V_CC`**, so the unused output is Hi-Z rather than driving a stub |

### Named ambiguities to resolve before the schematic is executable

1. **`SCLK` / `MOSI` / `CS` each name two different nets** — one on each side of
   the buffer. The page's drawing uses one label for both
   `[repo hardware/module/digital-and-supervision.md:23-40]`. A netlister will
   either merge them (shorting across the buffer) or error. Adopt the `_CAB` /
   `_DAC` suffixes above, or the DAC's own pin names on the far side.
2. **`CS` versus `SYNC`.** The DAC pin is `SYNC` `[datasheet SBAS430E p.6]`; the
   corpus says `CS` everywhere. Keep `CS` on the cable side, where it is the
   SPI-host signal, and `SYNC_DAC` on the far side. Same for `MOSI` → `DIN`.
3. **`3V3` is referenced and does not exist.** F-02.
4. **The 74AHCT125's ground pin has no net.** F-03. This is the netlist-blocking
   one: `U-LVL-MOD` pin 7 currently connects to nothing in any document.
5. **`R-SPI-SER` is on the instrument schematic** `[repo hardware/controller/carrier.md:574-576]`
   and does not appear on this page. Correct, but the page should say so — a
   reader taking this page as the module netlist will conclude the umbilical is
   unterminated.
6. **`U-TVS-MODULE` is `open`** `[repo hardware/bom.csv:106]` and is not drawn
   here. Deliberately deferred to E12, but three CMOS inputs reach a panel
   connector with no module-end protection, and the 74AHCT125 is a 2 kV HBM part
   `[datasheet SCLS264O p.1]` — a human-contact rating, not an IEC 61000-4-2 one.
   Not a new finding; recorded so the page carries it.

---

## 8. F-04 — verified, and fixed on disk while this review was open

**State when I found it.** `config/figures.yaml: umbilical-pinmap` is `settled`
at `1,2 BREATH/AGND | 3,6 +12V/PWR_GND | 4,5 SCLK/MOSI | 7,8 CS/DIG_GND`
`[repo config/figures.yaml:110-117]`, matching ADR 0004's own table at 830-831
and this page's redraw `[repo hardware/module/digital-and-supervision.md:86-94]`.
But ADR 0004's "Revised conductor budget" — the block explicitly declared *"the
authoritative 8-of-8 mapping and the one E11 and E12 build to"*
`[repo docs/decisions/0004-cv-interface-module.md:42-43]` — still read:

```
    SCLK      / DIG_GND     SPI to the DAC, 2 MHz (was ~1 MHz here)
    MOSI      / CS
```

`MOSI` paired with `CS`, no return conductor between them: the **exact** pairing
the same ADR refutes 730 lines later as *"the most efficient possible coupling
rather than the cancellation twisting is for"*, at **365–907 mV of crosstalk
against `CS`'s 678 mV `V_IL` margin**
`[repo docs/decisions/0004-cv-interface-module.md:833-846]`. And
`python3 tools/check-staleness.py` returned **`PASS no live stale values`**
`[repo, run 2026-09-21]`, because `umbilical-pinmap`'s `forbidden` list matched
the table-cell spelling with pipes and not the code-block spelling with runs of
spaces.

**State now.** Re-read at the end of this review, ADR 0004:96-99 reads:

```
[repo docs/decisions/0004-cv-interface-module.md:96-99]

    +12V      / PWR_GND     power. NOT presence - see below
    SCLK      / MOSI        SPI to the DAC, 2 MHz (was ~1 MHz here)
    CS        / DIG_GND     CS needs the ground partner - see the pin map below
    BREATH    / AGND        analog, band-limited ~500 Hz, sense return
```

and `forbidden` now carries both code-block spellings, with a note recording
that this is the *fourth* time a `forbidden` pattern has missed a different
formatting of the same value `[repo config/figures.yaml:116-117]`.

**Corrected independently, by someone else, while this document was being
written.** I am recording it rather than deleting it because `CLAUDE.md` asks
for verification to be recorded, and because a cold reviewer finding the same
defect from the datasheet side is evidence about the defect, not about the
reviewer. **Nothing is left to fix here.**

**The residue that is not fixed, and is the more useful finding.** Four
escapes of the same figure through four formattings is not four accidents; it
is the pattern-matching strategy. `forbidden` matches literal strings, so every
whitespace layout of a value needs its own entry and the list can only ever be
retrospective — it grows one entry per escape, always after the escape. Two of
this slice's figures have the same exposure today:

| Figure | Spellings a grep must anticipate |
|---|---|
| `umbilical-pinmap` | table cell with pipes, code block with space runs, prose, a diagram's ASCII (this page's drawing at lines 23-33 is a fifth layout) |
| `spi-series-r` | `100 Ω`, `100R`, `100 ohm`, `100Ω`, `R-SPI-SER at 100` |

**Proposed:** give `check-staleness.py` a whitespace-insensitive mode for
patterns that are pin maps or code blocks — normalise runs of spaces to one
before matching, on both the pattern and the corpus. That turns
`"SCLK / DIG_GND"` into one entry covering every layout instead of one entry per
layout, and it is the only change that stops the list growing by one per escape.
This is a tooling change and outside my slice, so it is a proposal, not a
finding.

## 9. Smaller items

**F-11 — `C-DECOUPLE` quantity.** The row's derivation counts *"DAC8568
AVDD+DVDD = 2"* `[repo hardware/bom.csv:43]`. The `DAC8568CIPW` TSSOP-16 pin
list is `1 LDAC, 2 SYNC, 3 AVDD, 4-7 VOUT/VREF, 9 CLR, 10-13 VOUT, 14 GND,
15 DIN, 16 SCLK` `[datasheet SBAS430E p.6]`. **One supply pin.** The quantity is
19 today, after the LM311's two were removed `[repo hardware/module/digital-and-supervision.md:66-68]`;
it should be **18**. (The count survives if the second cap is deliberately a
bulk part on `AVDD`, but the row says `DVDD`, and there is no `DVDD` to decouple.)

Separately, the same row's derivation omits a cap SBAS430E asks for:
*"A minimum 100 nF capacitor is recommended between the reference output and
GND for noise filtering"* on `VREFIN/VREFOUT` `[datasheet SBAS430E p.31]`. That
pin carries the reference the entire pitch scale is built on. It may be counted
elsewhere; nothing in this slice shows it.

**F-12 — the `U-TVS-SPI` edge figure.** The row says 30 pF per channel *"against
2 m of Cat5 and `R-SPI-SER` [is] ~29 ns of edge on a 250 ns half-period"*
`[repo hardware/bom.csv:103]`. That is 100 Ω × (30 pF + ~200 pF of cable), the
lumped-RC model the corpus refuted on the same day
`[repo docs/decisions/0004-cv-interface-module.md:79-83]`. Transmission-line
answer: the array sits at the launch point, between `R-SPI-SER` and the line, so
it sees the source and the line in parallel.

```
[calc]  (R_ser + Z_out) ∥ Z0 = 140 ∥ 100 = 58.3 Ω
        τ = 58.3 Ω × 30 pF = 1.75 ns,  10–90 % ≈ 3.9 ns
        at the far end that is 1.4 ns/V on a 2.75 V step, against
        the AHCT125's 20 ns/V limit                    [SCLS264O p.3]
```

**~3.9 ns, not 29 ns.** The conclusion (acceptable) is unchanged; the number is
wrong by 7× and it is wrong by the specific model this corpus spent a day
refuting. It is the last place that model survives.

**F-14 — the spare gate.** See §7.

**F-15 — the DAC's logic-high threshold in ADR 0004.** *"The cost is that a 5 V
DAC wants roughly 3.5 V for a logic high while the instrument sends 3.3 V, so
SPI needs shifting"* `[repo docs/decisions/0004-cv-interface-module.md:147]`.
3.5 V is `0.7 × 5 V`, and SBAS430E applies the 0.7 ratio **only for
2.7 V ≤ AVDD < 4.5 V**; from 4.5 V to 5.5 V the ratio is **0.625**
`[datasheet SBAS430E p.4]`. At `AVDD` = 5.21 V, `V_INH` = **3.256 V**
`[calc]`.

The conclusion is unaffected — 3.256 V is still above 3.3 V minus any realistic
margin, and the shifter is still required — but the number is 0.24 V wrong and
**it is the same shape as the 74HC165 and WS2815 findings this project already
has**: a CMOS threshold assumed to be `0.7 × VDD` when the datasheet tabulates
something else at the rail in use `[repo config/figures.yaml:48]`
`[repo hardware/bom.csv:34]`. Two of the three figures `CLAUDE.md` cites as
"moved by reading a banked document" are exactly this error. Replace 3.5 V with
3.256 V and cite SBAS430E p.4.

---

## 10. What I could not check

- **ESP32-S3 GPIO output impedance and drive-strength classes.** No Espressif
  document is banked `[repo datasheets/MANIFEST.csv]`. The corpus's implicit
  35–40 Ω is unsourced. §1.4 gives the break-even (130 Ω) instead, which is the
  robust form of the same claim, but the point estimate should be sourced before
  E11.
- **Cat5 pair-to-pair delay skew.** The NE8FDP datasheet gives CAT5e component
  conformance and a 1–100 MHz range `[datasheet NE8FDP-DATASHEET.pdf p.2]` but no
  skew figure. My 45 ns/100 m is `[from memory]`; the margin is 100× so it does
  not matter, but it is not sourced.
- **Whether the DAC8568's `write-and-update` commands bypass the `LDAC` pin in
  silicon.** SBAS430E does not say, and with no `MISO` the board cannot find out.
  This is exactly why F-01 should be fixed by following TI's explicit
  instruction rather than by reasoning about it.
- **Flash-operation durations on the ESP32-S3.** `[from memory]`, §5.2.
- **Trace capacitance and the real board stack-up.** §2.2's 10 pF and 0.6 mm
  trace width are assumptions; the conclusion (local return, or series
  resistors, or both) holds across any plausible value, but the 200 nH is an
  estimate of a loop nobody has drawn yet.

---

## Summary of proposed changes

| Change | Parts | Where |
|---|---|---|
| **`R-LDAC`: pull-up to `AVDD` → 0 Ω strap to GND** | 0 net | `bom.csv:129`, this page's drawing |
| **Cable-side `CS` pull: 10 kΩ to `3V3` → 100 kΩ to bus +5 V** | 0 net | `bom.csv:49` |
| **`DIG_GND` ties to the analog return at the DAC's GND pin; `U-LVL-MOD` pin 7 joins it there** | 0 | this page, `ADR 0004:627`, `figures.yaml: dig-gnd-topology` |
| **`R-DAC-SER` ×3, 220 Ω 0805** | **+3** | new BOM row |
| **`C-CLR` 100 nF 0805 on `N_CLR`** | **+1** | new row, or `C-DECOUPLE` +1 |
| **`LK-PWRGD-CLR`, 0 Ω link, LT1641 `PWRGD` → `N_CLR`** | **+1** | new row |
| Software `LDAC` (`C3..C0 = 0010`) on the last word of each pass; channel 7 written first | 0 | `firmware/README.md` |
| `gpio_set_drive_capability()` on IO34/35/36; NVS/OTA gated on "not playing"; DAC service in IRAM | 0 | `firmware/README.md` |
| `C-DECOUPLE` 19 → 18 | −1 | `bom.csv:43` |
| ~~ADR 0004 conductor-budget block corrected; `forbidden` list extended~~ | 0 | **already done on disk mid-review — §8** |
| ADR 0004:147 "roughly 3.5 V" → 3.256 V, cite SBAS430E p.4 | 0 | `ADR 0004:147` |
| Whitespace-insensitive matching in `check-staleness.py` (proposal, out of slice) | 0 | `tools/check-staleness.py` |
| Spare gate: 4A → GND, 4OE → `V_CC` | 0 | this page |

**Net part count: +4.** Two of those (`R-DAC-SER`, `C-CLR`) are insurance; two
(`LK-PWRGD-CLR` and the `R-LDAC` value change) are corrections. The two blocking
findings, F-01 and F-02, cost nothing at all — they are a polarity and a rail.
