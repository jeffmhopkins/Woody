# V4 — Fix conflicts in the 2026-09-20 cold review

**Assignment.** Build the full list of proposed changes, then find the pairs that cannot
both be applied as written. Nothing in the register has been applied yet, so every
conflict below is still cheap to resolve — and every one of them is invisible from inside
the document that proposes either half.

**Method.** All 23 review documents read in full or in the sections that carry proposals,
plus `README.md`, `ROADMAP.md`, all fourteen ADRs, `docs/reference/`, `hardware/bom.csv`
and `docs/log/2026-09-20-review-resolution.md`. Proposals were indexed by the **node or
resource they touch** rather than by the document that raised them, which is the only way
this class of defect becomes visible — the register groups by subsystem, and every reviewer
was assigned a subsystem.

**Headline.** The review contains roughly 190 distinct proposals. **Thirty-one of them
collide in twenty-four pairs or clusters.** Six clusters are three-way or worse. The
densest are:

- **the module's breath input network** — five documents propose five different networks
  for the same four component positions, and **six different in-amp gain values** fall out
  of them (2.13 / 2.143 / 2.20 / 2.229 / 2.384 / 2.39), each arithmetically correct for a
  different combination;
- **the DAC's supply rail** — four mutually exclusive regulators, one of which silently
  destroys the exactly-2.000 pitch gain that three other findings depend on;
- **the current limiter's setting** — five numbers spanning 700 mA to 1.5 A, pulling in
  opposite directions, against a window that is nearly empty;
- **the F-POLY footprint** — three parts proposed for one pad.

Eight shared budgets are over-subscribed. The op-amp count, the umbilical conductors, the
ADC's spare channel and the module panel are each claimed by more proposals than they can
hold, and in every case each claimant says "and it is free".

---

# Part 1 — The conflicting pairs

Ordered by consequence. Each entry states both fixes, why they cannot both be applied as
written, and the combined correct version.

---

## Cluster A — The module's breath input network

Five documents rewrite the same four component positions — the series resistors, the
pulldown, the common-mode bias return and the band-limit capacitor — and **no two of them
produce the same network.** Every one is internally correct. The gain of the receiver is a
function of all four, and every document computes it against its own network only.

### A1. The common-mode bias return: 2 × 1 MΩ vs a centre-grounded split shunt vs one 1 MΩ

**Fix α (B2 §1, B8 §1, B9 §2, D1 §1, C2 F3):** 1 MΩ from **each** in-amp input to module
analog ground. Symmetric, so with 0.1 % series resistors the CMRR floor is 94 dB.

**Fix β (B7 F3):** split the existing 100 kΩ pulldown into 49.9 kΩ + 49.9 kΩ and ground the
centre. B7 then explicitly forbids α's shape: *"Do not use the naive single 1 MΩ from
`AGND` to module 0 V. That unbalances the legs… 844 µV at the jack."*

**Fix γ (D3 §4):** 1 MΩ differential **plus one** 1 MΩ from the −IN leg only to module
analog ground.

**Why they cannot all be applied.** β and α are alternative networks for the same two pads.
Applying both gives 100 kΩ differential in parallel with 2 MΩ, and 25 kΩ of common-mode
impedance in parallel with 1 MΩ — a 95.2 kΩ differential shunt against series resistors
that three other fixes are simultaneously raising, which is a 30 % attenuator (see A4). γ is
the asymmetric arrangement β warns against, drawn by a different reviewer: one leg sees
1 MΩ to ground, the other sees nothing, which is exactly the leg imbalance that caps CMRR.
B7's own arithmetic condemns D3's diagram, and neither document cites the other.

**Combined correct version.** Take α's shape, β's balance discipline, and γ's rejection of
the 100 kΩ:

- **2 × 499 kΩ, 0.1 %, one from each in-amp input to module analog ground** (1 MΩ
  differential, 249.5 kΩ common-mode per leg — β's sensitivity to the *ratio* is what
  matters, not the absolute value).
- **Delete `R-PD-BREATH`'s 100 kΩ entirely.** The 1 MΩ differential the pair provides is
  ample for the instrument-off case and removes the attenuator of A4.
- Series resistance symmetrised (A3), which is what makes any of these meet 60 dB.
- Restate ADR 0003's R35 rule as B2/D1 both ask: *no low-impedance connection to the module
  ground pour; a ≥499 kΩ bias return is required and is not a violation.* As written, R35
  forbids the thing that makes the receiver work.

### A2. The differential pulldown: delete / keep at 100 kΩ / raise to 1 MΩ and move it

**Fix α (B2 §1):** delete the 100 kΩ.
**Fix β (B8 §1, B9 §2, C2 F3, B7 F3):** keep the 100 kΩ.
**Fix γ (D3 §4, B2 §6):** raise it to 1 MΩ **and move it to the connector side** of the
protection resistors.

**Why they conflict.** β is chosen by four documents on the grounds that "it now does only
the job it was bought for". But B2 §6 and D3 §4 show that keeping it at 100 kΩ is a silent
attenuator: 100/(100+10) = 0.909 with one series resistor, 100/(100+10+10) = **0.833** once
the series resistance is symmetrised, and 0.704 once module-end series resistors are added
too. Three of the four documents that vote to keep it never compute the divider; the one
that does (C2 F3) computes it against a 1 kΩ series resistor it recommends elsewhere in the
same document and not against the 10 kΩ it also recommends in its own missing-parts table.

γ's *move* is the load-bearing half and is stated by only one reviewer: on the connector
side of the series resistors the pulldown is not in the signal divider at all. The register
records the 17 % figure but not the move.

**Combined correct version.** Delete the 100 kΩ. If a differential element is still wanted
for the BREATH-conductor-open case, it is **1 MΩ on the connector side of the series
resistors**, not 100 kΩ behind them. With A1's pair fitted, the case is already covered and
the part is redundant.

### A3. The series protection resistor: 10 kΩ, 1 kΩ, or 10 kΩ in four places

Four incompatible specifications for the same protective element:

| Source | Instrument end | Module end |
|---|---|---|
| ADR 0003 (current) | 10 kΩ, one leg (BREATH only) | none |
| B2 §5 | 10 kΩ **both** legs | 10 kΩ **both** legs + BAV99 |
| B8 §1 | 10.0 kΩ **0.1 %** both legs | — |
| D1 §3, C2 F3, register W8 | **1 kΩ** | — |
| C2 §4 item 4 (same document as C2 F3) | **10 kΩ** (as the band-limit R) | 2.2 kΩ |

**Why they conflict.** These are not stylistic. The value sets four different things at
once, and each document optimises one:

- **B2 §5** wants 10 kΩ at the module for hot-plug fault current — but stacking it on top of
  the instrument's 10 kΩ gives 40 kΩ differential, which moves the 500 Hz pole of A5 to
  169 Hz and turns the 100 kΩ pulldown into a 0.71 divider.
- **D1 §3 and C2 F3** want 1 kΩ, because with the buffer on +12 V there is no fault current
  to limit and a 1 kΩ costs only 1 % of gain. But 1 kΩ is *also* the fault limit that B7 F9
  identifies as the module's only protection during asymmetric mating
  (`12 V / 10 kΩ = 1.2 mA` becomes 12 mA at 1 kΩ), and it is the resistor that C2 F22 uses
  to form the 482 Hz pole — at 1 kΩ that pole becomes 4.8 kHz unless C moves by 10×.
- **C2 contradicts itself**: Finding 3 recommends 1 kΩ "not 10 kΩ"; its own consolidated
  missing-parts list recommends 10 kΩ + 33 nF.

**Combined correct version.** Separate the three jobs that have been collapsed onto one
resistor:

- **Instrument end, BREATH leg: 1 kΩ 1 %** — fault limiting against a crossover cable
  (D1 §3), with **BAV99 to the local +12 V and PWR_GND** at the connector. A matching
  **1 kΩ in the AGND leg** for symmetry (it carries ~70 nA).
- **Module end: 10 kΩ 0.1 % in each leg**, which is where the external cable actually is,
  which bounds in-amp input current to 1.1 mA on a 12 V fault (B2 §5), and which is the leg
  resistance the A1 bias pair is balanced against (B8 §1). **BAV99, not a TVS array, on
  these two inputs** — see L2.
- Total differential series resistance: **22 kΩ**, fixed and known. Every downstream number
  (A4, A5) is computed from this and nothing else.

### A4. Six in-amp gain values, each correct for a different network

This is the composed consequence of A1–A3 and no document states it.

| Source | G | Network assumed |
|---|---|---|
| ADR 0003 / BOM | 2.13 | 10 V / 4.7 V, pedestal counted as signal, no divider |
| C2 F24 | 2.143 | as above, R_G 43.2 kΩ |
| B2 §6 | 2.20 | 0.990 divider (1 MΩ pulldown, one 10 kΩ) |
| B9 §8 | 2.229 | pedestal removed, no divider, R_G 40.2 kΩ |
| B2 §3 | 2.384 | 0.9091 divider, R_G 35.7 kΩ |
| B2 "working the link" | 2.39 | 0.9091 divider, VFSS 4.6 V |
| *register* | — | 0.833 divider ("silently a 17 % attenuator") |

**Why this matters more than it looks.** `R_G` is a single resistor on a part that is not
yet chosen (INA821 `1 + 49.4 k/R_G` vs INA828 `1 + 50 k/R_G`, A3 F1). Fitting the wrong one
does not break anything visibly — the panel gain knob absorbs it — but the knob then has no
neutral position, and B9 §8 shows that if G is too low the channel **cannot reach 10 V at
any knob setting**, permanently, because a pot can only attenuate.

**Combined correct version.** Compute `R_G` once, last, from the network A1–A3 settles:

```
divider  = 1.0            (100 kΩ pulldown deleted; 2 × 499 kΩ bias to ground
                           is common-mode only and cancels in the difference)
span     = VFSS 4.6 V     (pedestal is removed by the zero, not amplified — B9 §8)
G        = 10.00 / 4.60   = 2.174
R_G      = 49.4 k / 1.174 = 42.08 kΩ  → 42.2 kΩ E96 (INA821, G = 2.170)
```

and **choose INA821 vs INA828 before `R_G` is ordered** — C1 F7's recommendation. Write the
divider assumption into the BOM line, because it is what makes the number checkable.

### A5. The 500 Hz band-limit: one pole, two poles, and four capacitor values in four places

Six proposals for a filter ADR 0003 specifies in one sentence and the BOM does not
implement at all:

| Source | Where | Parts | Corner |
|---|---|---|---|
| B2 §4 | module, across BREATH–AGND | 33 nF | 482 Hz (assumes 10 kΩ total) |
| B8 §7 | module, **ahead of** the in-amp | 16 nF diff + 2 × 100 pF CM | 497 Hz |
| D3 §5 | module, **ahead of** the in-amp | 15 nF diff + 2 × 150 pF CM | 530 Hz |
| C2 F22 | module, **after** the in-amp | 2.2 kΩ + 150 nF | 482 Hz |
| C2 F22 | instrument, **before** the buffer | 10 kΩ + 33 nF | 482 Hz |
| D3 §7 | instrument, **before** the buffer | 1 kΩ + 330 nF | 482 Hz |
| B1 §7 / B2 §4 / B8 §8 | instrument | **delete the pole**, 100 Ω + 10 nF at 159 kHz | — |

**Why they conflict.**

1. **C2 F22 puts the module pole after the in-amp.** D3 §5 and B8 §7 both give the reason
   this is wrong and neither cites it: an in-amp's input stage **rectifies** out-of-band
   energy into a DC shift, and a filter downstream of the amplifier cannot undo it. The
   instrument has a 2.4 GHz radio and 2 m of shared-jacket SPI; a WiFi TX burst is
   amplitude-modulated at the packet envelope, so rectification lands it in the audio band
   by a path that scoping the rail will not find. **C2 F22's placement reintroduces exactly
   the failure D3 §5 and B8 §7 place the filter forward to prevent.**
2. **Every capacitor value is computed against a different series resistance.** B2 §4's
   33 nF assumes 10 kΩ. Under B2's *own* §5 (10 kΩ in each leg at both ends) the
   differential resistance is 40 kΩ and the same capacitor gives **169 Hz** — below the
   sensor's own bandwidth, i.e. the failure mode B1 §1 spends four pages on for the ADC
   branch, reproduced on the CV branch. Under A3's resolution (22 kΩ) it gives 219 Hz.
3. **Two poles or one is undecided and costs 318 µs.** B2 §8, B8 §8 and B1 §2 all want one
   pole and say so; D3 §5 fits both and then notes the 0.64 ms cost against a budget line
   that allows 0.2 ms; C2 F22 fits both and revises the budget instead.
4. **B1 §7's stability warning survives all of this and is addressed by none of them**: the
   band-limit capacitor must not sit on the OPA2197's output. D3 §7 and C2 F22 both dodge it
   by putting the instrument pole *before* the buffer, which is right and is stated as an
   aside rather than as the rule.

**Combined correct version.**

- **One differential pole, at the module, ahead of the in-amp**, formed against A3's 20 kΩ
  of module-end series resistance:
  `C_diff = 1/(2π × 20 kΩ × 482 Hz) = 16.5 nF` → **16 nF C0G across the two inputs**, plus
  **2 × 100 pF C0G 5 % from each input to module analog ground** (`C_diff/C_cm = 160`, so CM
  capacitor mismatch cannot convert common mode to differential in band — B8 §7's ratio rule
  is the load-bearing part).
- **The CM capacitors return to module analog ground, never to `AGND`** (D3 §5's rule —
  returning them to AGND puts their current in the sense return).
- **Instrument end: no 500 Hz pole.** A **1 kΩ + 10 nF (16 kHz) at the sensor output, before
  the buffer** — enough to keep the sensor's own noise and any HF pickup off the cable,
  costing 10 µs instead of 318 µs, and it satisfies B1 §7 by construction because the buffer
  never drives it.
- Latency budget line becomes **0.33 ms**, not "< 0.2 ms" and not 0.64 ms.
- Delete the vestigial 2 kHz breath reconstruction filter (B8 §11: breath never enters the
  DAC, so there are no steps to reconstruct). 80 µs recovered for nothing given up.

---

## Cluster B — The breath ambient zero

### B1. Six mutually exclusive schemes for one REF pin

| Source | Scheme | REF range | Cost |
|---|---|---|---|
| register S2 opt 1 | make the downstream stage inverting | 0 … +5 V usable | topology |
| register S2 opt 2 / B1 §4 | `0.4 × (V_DAC6 − V_DAC7)` | −1.00 … +1.00 V | ½ op-amp + 2 R |
| B2 §2 | inverting, gain −0.18 | 0 … −0.90 V | ½ op-amp + 2 R |
| D3 §1 | inverting, gain −0.25, with a 1.06 Hz pole ahead of it | 0 … −1.19 V | ½ op-amp + 3 passives |
| B9 §1(a) | **swap the in-amp inputs**, keep the DAC unipolar | 0 … +5 V | a wire, plus an inverting downstream stage |
| B9 §1(c) | level-shift ch6 against −12 V | ±1.25 V | 2 R, puts the rack rail into the zero |

**Why they cannot coexist.** They are alternatives for one pin, and three of them consume a
different number of op-amp halves (see the budget audit). Two of them have **opposite
consequences for the in-amp's input polarity**, which is stated in no ADR — B9 §1 flags this
as itself a defect: *"the sign of the whole channel depends on it and no document currently
states it."*

The couplings that decide it, none of which appear in any single document:

- **B1 §4's `0.4 × (DAC6 − DAC7)` binds the breath zero to the mod-channel offset.** DAC ch7
  is the shared mod pedestal. S4's whole point is that ch7 is cleared by the frame watchdog
  and must be refreshed every pass; routing it into the breath REF means a corrupted or
  un-refreshed ch7 word moves the **breath floor as well as all four mod jacks**, which is
  B10 §9's failure with one more channel attached to it. Attractive on parts count, wrong on
  fault containment.
- **B9 §1(a)'s input swap is the cheapest and it collides with A1/A5.** Swapping inputs
  changes which leg carries the 1 kΩ and which the 10 kΩ, and it makes the downstream gain
  stage mandatorily inverting — which is the same op-amp half D3 §6 and B9 §10 want as a
  *follower* to buffer the gain pot's wiper. Both are possible only with two halves.
- **B9 §1(c) reintroduces the rail-derived-DC failure** that D3 §2 and B3 §1 exist to
  delete on the pitch channel. Rejected on its own document's advice.

**Combined correct version.**

- **Keep `BREATH` on +IN** (write it into ADR 0003; the sign of the channel is currently
  undocumented).
- **Drive REF from an inverting stage on the ch6 buffer half that ADR 0003 already budgets**
  — the buffer was always needed, and an inverter *is* a buffer. Gain **−0.25**, giving
  0 → −1.19 V (D3 §1's range), which covers the full `Voff` distribution (0.152–0.378 V ×
  G = 0.33–0.82 V) with headroom in the direction warm-up drift actually moves.
- **Do not use ch7 in the expression.** The breath zero must not be a function of the mod
  offset register.
- **Nothing in series between that op-amp's output and the REF pin.** This is C2 F21's and
  B2 §7's rule and it is the one the register singles out as a trap: a 1 kΩ there caps CMRR
  at 26 dB using a resistor visually identical to the six correct `R-OPAMP-IN` parts. Put it
  in ADR 0003 in bold, and put the `R-OPAMP-IN` on the *input* of that stage where the DAC
  drives it (C2 F21 — count 7, not 5).

### B2. The smoothing RC on DAC channel 6 — and the rule that forbids it

**Fix α (D3 §1):** 100 kΩ + 1.5 µF (τ = 0.15 s) at the **input** of the REF stage.
**Fix β (B10 §10):** an RC with τ ≈ 100 ms "between DAC channel 6 and its buffer".
**Rule γ (C2 F21, B2 §7, D3 §1):** no series impedance at the REF pin, ever.

These are compatible **only** because α and β both say *ahead of the amplifier*. The
conflict is that **β's phrasing does not say which side of the buffer it is on**, and the
BOM line it would become ("RC on ch6") is exactly the kind of instruction that gets drawn on
the output side at layout. D3 §1 is the only document that states the ordering as the reason
the stage must be an amplifier rather than an RC plus a resistor.

**Combined correct version.** One RC, **100 kΩ + 1 µF film (τ = 0.1 s)**, in series with the
DAC output *before* the inverting stage's summing resistor, with the BOM note stating why
the position is not negotiable. Both α's and β's numbers land in the same decade; take β's
100 ms because D3's own auto-zero decays over ~2 s and 100 ms is invisible to it.

### B3. Two different breath mutes, in two different places, both driven by the watchdog

**Fix α (B6 §6):** a 74HC4066 gate shunting `BREATH` to `AGND` **at the module input**,
driven by the same 74HC123 output that asserts `CLR`.
**Fix β (D3 §11):** a 2N7002 shunting the **post-gain, pre-summing node**, driven from the
watchdog's complementary output.

**Why they conflict.** They are two parts for one function and they mute different amounts
of the channel:

- α shorts the in-amp's differential input, so the output goes to **`V_REF`**, which after
  B1's inverter is 0 V at `CLR` — but `CLR` also clears DAC ch6, so REF goes to 0 and the
  output is 0. Correct. However, α also shorts `BREATH` to `AGND` **at the module**, which
  is a low-impedance path between the sense return and the signal conductor — the exact
  thing A1's 499 kΩ resistors are sized in nanoamps to avoid. During a mute it does not
  matter; if the FET's off-leakage is poor it becomes a permanent leg imbalance.
- β mutes after the gain stage, so **the panel offset knob's contribution still reaches the
  jack.** ADR 0006 assigns that knob to "position where the floor sits". If the player has
  set a floor of 2 V, β mutes to 2 V.

**Neither is a mute.** And both are driven from the watchdog, which Cluster I shows has an
undecided `CLR` polarity and an undecided default for a failed watchdog.

**Combined correct version.** One shunt, **at the output summing node, after the offset
injection and before `R-OUT-PROT`** — a 2N7002 (or an ADG419-class switch if its off-leakage
measures badly) across the last stage's feedback or from the output node to analog ground
through the existing 1 kΩ. That is the only point at which "0 V at the jack" is true
regardless of knob position. Drive it from the watchdog output that asserts `CLR`, and make
the **failure direction "muted"** — with I4's pull resolved so that a dead watchdog does not
leave breath live.

### B4. The free presence-detect comparator depends on the floor that B1 and B3 remove

**Fix (register W10, D2 §19):** one comparator on the in-amp output at a ~100 mV threshold
reports cable connected, +12 V reaching the far end, reference alive, sensor alive, buffer
alive, both analog conductors intact. *"There is no instrument attached ⇒ 0 V; healthy
instrument ⇒ ~0.2 V × G before any breath."*

**Why it breaks.** Its threshold sits on the sensor's +0.43 V pedestal at the in-amp output.
That pedestal is what B1's whole cluster exists to **null**, and D2 §19's own escape —
*"the boot value [of the zero] is zero, so this is comfortable"* — is true only until D4 §12
and S4's rule is applied, which requires the zero to be **written and refreshed every
pass**. After the refresh fix, the pedestal is nulled continuously and the comparator reads
"no instrument" whenever the instrument is working. B3's mute then holds it low as well.

**Combined correct version.** Take the comparator **at the in-amp's `+IN` pin, not at its
output** — i.e. sense `BREATH − AGND` directly, upstream of the REF injection and upstream
of the mute. Threshold ~100 mV differential. It then reports the same six facts and is
immune to every downstream fix. This costs the same one part and it is the only placement
that survives the rest of the review.

---

## Cluster C — The pitch offset reference

### C1. Four sources for −2.5 V, and the deciding constraint is the power-on park

| Source | Proposal | Power-on park | Op-amp halves |
|---|---|---|---|
| B3 §1 | DAC8568 `VREFOUT`, +2.5 V, non-inverting | **0 V — audible** (B3 accepts this) | 0–1 |
| D3 §2 | `VREFOUT` buffered to +2.5 V, plus an inverter for −2.5 V | 0 V | 2 |
| C2 F14 | `VREFOUT` inverted to −2.5 V by ½ OPA2197 | 0 V | 1 |
| B9 §3 | **REF3025/REF5025 series reference**, +2.5 V, non-inverting summing | **−2.500 V — subsonic** | 0 |
| *default nobody chose* | divider from −12 V | −2.5 V | 0 |

**Why they conflict.** All four delete the rail divider and are right to. But three of them
take the offset from the DAC's own reference, and **the DAC's internal reference is disabled
at reset** (ADR 0006, verified in B4 §3). So at rack power-on, before firmware runs, both
terms of `V_out = 2·V_dac − V_off` are zero and pitch parks at **0 V — mid-range on a VCO,
audible, held indefinitely.** ADR 0006's power-on table promises "bottom of its range, below
−2 V. Subsonic. A VCO there is inaudible", and B10 §20's whole rail-order enumeration is
built on that promise.

B3 §1 notices and accepts it on the grounds that breath parks at 0 V so the VCA is shut.
That argument **does not survive Cluster B**: B6 §6, B9 §2, B8 §1, D1 §1 and C2 F3 all
establish that breath does *not* reliably park at 0 V today, and D3 §11 shows it parks at
+0.43–0.55 V even after the bias fix, until the mute of B3 is fitted. Two independently
correct arguments — "take the offset from VREFOUT" and "breath parks at 0 V so it doesn't
matter" — compose into an audible note at every power-on.

B9 §3 is the only proposal that keeps the promise, and it is the only one that costs zero
op-amp halves, which matters given the budget audit.

**Combined correct version.**

- **A series 2.5 V reference on the protected +12 V — REF5025, the same family as the
  already-specified REF5050** (B3 §1's own alternative, B9 §3's recommendation). Alive with
  the rails, before firmware, so pitch parks at −2.500 V as ADR 0006 claims.
- **Non-inverting pitch stage with the offset at the bottom of the gain resistor**
  (B9 §3's topology): `V_out = V_dac(1 + Rf/R1) − V_off(Rf/R1)`, so the reference is
  **positive** and no inverter half is needed. This is the decisive practical difference
  between B9 §3 and C2 F14/D3 §2 and neither of those two notices it.
- Drift: 2.5 V × 3 ppm/°C × 10 K = 75 µV = **0.09 cents**, against the 30 cents a rail
  divider costs and the 0.30 cents `VREFOUT` would give.
- Record explicitly, as B9 §3 asks, that a **fixed** reference plus a trimmer is not the
  "two offset authorities in series" that ADR 0006 forbids — otherwise someone deletes one
  of them later.
- **Reserve the `VREFOUT` footprint** as the fallback, per D3 §2, and decide at E7. Do not
  build both.

### C2. The LT5400: keep it as the trimmer's matched leg, or delete it

**Fix α (register, "one over-specification worth acting on"):** *"the LT5400 is 20–30×
over-specified now that the trimmer sits in the gain ratio. It buys 0.11 cents against the
trimmer's 2.4. Two 0.1 % / 10 ppm thin-film 0805s do better, and dropping it removes the
design's only MSOP part."*

**Fix β (B3 §3):** shrink the gain trim to ±1.5 % **and put it on an LT5400 leg**, which
takes the trimmer's tempco contribution from 2.4 cents to **0.08 cents**.

**Fix γ (C2 F15):** specify **LT5400A** specifically, 10 kΩ, 1:1 quad — because the 1 ppm/°C
tracking that the 0.11-cent figure rests on is the A grade only, and C/D grades carry the
same name.

**Why α and β cannot both be applied.** B3 §3's entire result depends on the cancellation
`d(ratio)/ratio per K = f × (α_trim − α_network)` — the *matched pair's own absolute tempco
cancels out of the ratio* and only the difference survives. That cancellation exists because
the two legs are on one die. With two discrete 0.1 %/10 ppm 0805s, the legs track only to
the sum of their individual tempcos, and the trimmer's contribution reverts to roughly the
weighted-average model ADR 0006 used — 22 ppm/°C at ±5 %, 14 ppm/°C at ±1.5 %, i.e.
**1.6–2.4 cents, not 0.08.** α's "two 0.1 %/10 ppm 0805s do better" is true for the *fixed*
ratio and false for the ratio-with-a-trimmer-in-one-leg, which is the configuration β
proposes and the ADR already chose.

**Combined correct version.** The two fixes are only compatible if the trimmer leaves the
ratio:

- If the **trimmer stays in the gain leg** (ADR 0006's decision, endorsed by B3 §3 and
  C2 F14): **keep the LT5400, grade A, 10 kΩ, 1:1** (C2 F15). The register's deletion is
  wrong in this configuration and would cost ~2 cents.
- If the **trimmer is removed from the ratio entirely** — which B3 §2 makes possible, by
  giving firmware an affine `(gain, offset)` pair so it owns the load correction — then α is
  right and two 0.1 %/10 ppm 0805s are enough.
- **These are one decision, not two.** Decide "who owns fine gain" first (B3 §4's authority
  split: *hardware owns coarse gain; firmware owns offset, fine gain and curvature*), then
  the resistor question answers itself. Neither document frames it that way.

---

## Cluster D — The DAC's supply rail

### D1. Four regulators for one rail, and one of them moves the pitch gain

The problem is agreed (S5, B5 §5, C1 F3, C2 F4): the LM317L's worst case is 4.96–5.62 V
against a required window of 4.95–5.50 V. **Spread 0.66 V against a 0.55 V window — no
nominal value fits.** Four fixes:

| Source | Fix | AVDD | Consequence |
|---|---|---|---|
| C1 F3 fix 1 | keep the LM317, tighten to 120 R / 383 R 0.1 % | 5.25 V ±1.7 % | divider current 10.4 mA |
| B5 §5 fix 1 | LP2951-class, ±0.5 % ref, target 5.10 V | 5.03–5.17 V | new part number |
| C2 F4 / register S5 | **delete the LM317; second REF5050 + ½ OPA2197** | 5.000 V ±0.05 % | 250 mV of DAC headroom, zero margin |
| B5 §5 fix 2 | keep the LM317, **narrow the DAC window to 4.50 V** | 5.10 V | see below |

**Why B5's fix 2 cannot be applied as written.** Narrowing the used DAC window from
0.25–4.75 V to 0.25–4.50 V changes the pitch gain from `9/4.5 = 2.000` to `9/4.25 = 2.118`.
That single change breaks four other findings that are each correct on their own:

- **B3 §7 and B9 §3** both establish that the 0.25–4.75 V window makes the pitch gain
  *exactly* 2.000, which is what a matched quad builds directly — the finding that
  "dissolves the 9/5-is-not-constructible objection that drove the trimmer decision". At
  2.118 the ratio is no longer constructible from a 1:1 quad and C2's whole Cluster-C
  resolution changes.
- **B4 §9** computes the mod range as ±9 V from the same window; at 4.50 V it is **±8.5 V**,
  and a third preset drops off the reachable list.
- **B3 §2's ±600 cents of firmware offset authority** is derived from the reserved 0.25 V at
  each end; the number changes.
- Every cents figure in ADR 0006 recomputed at 2.0× (B3 §7) would need recomputing again.

**Why S5's REF5050 option needs a measurement first.** At AVDD = 5.000 V the top of the
window (4.75 V) has exactly the 250 mV of output-buffer headroom B5 §5 states as the
minimum. That is the floor, not a margin. The ROADMAP already schedules **"DAC saturation vs
AVDD — record the actual saturation code at the actual rail"** at E7, and B4 §12(a) points
out the measurement should look for a *knee*, not a slope. **This option must not be
committed before E7.**

**Combined correct version.**

- **Target 5.10 V with a ≤1 % reference** (B5 §5 fix 1), which clears the 5.50 V ceiling by
  400 mV and the 4.95 V floor by 150 mV and **keeps the 0.25–4.75 V window intact**, so
  nothing in Clusters C or H moves.
- Reserve the REF5050 + buffer footprint as the alternative and settle it at E7 against the
  measured saturation knee. If E7 shows the DAC is linear to within 50 mV of AVDD, S5's
  option becomes the better one (5.000 V, 0.05 %, 3 ppm/°C, one fewer tolerance stack under
  the pitch calibration).
- **Reject the window-narrowing fix outright** and say why in the ADR, because it is the
  cheapest-looking of the four and it silently costs four other findings.
- Whichever is chosen, write the **two-sided inequality** into the ADR rather than a nominal
  (B5 §5's third point), so the next person sizing a divider sees the constraint.

### D2. Moving the 74AHCT125 onto that rail, while replacing the regulator with a 10 mA reference

**Fix α (C1 F5, B10 §2):** power the module's level shifter from the DAC's own 5.25 V rail,
deleting the module's dependence on the rack's unprotected bus +5 V. Costs ~3 mA on the
LM317L; removes a clamp event on every power-on and a 10 mV V_IH margin.

**Fix β (C2 F4, register S5):** delete the LM317 and derive that rail from a **REF5050
(10 mA capability) buffered by half an OPA2197**.

**Why they compose badly.** α is computed against an LM317L — a 100 mA regulator with a hard
current limit and thermal shutdown. β turns the same rail into a precision voltage reference
followed by a unity-gain buffer, and then α adds a **three-line 2 MHz CMOS switching load**
to it. The OPA2197 can source 65 mA so nothing fails, but the DAC's supply rail is now
generated by an op-amp that is simultaneously absorbing nanosecond digital transients, on
the one rail the whole precision argument sits on. ADR 0004's original concern ("keep the
buffer's switching current off the DAC's supply") is dismissed by C1 F5's arithmetic against
an LM317 and never re-evaluated against a reference buffer.

**Combined correct version.** Take α (it removes three findings — B10 §2, §3 and §16(c)) and
resolve D1 in favour of a **regulator, not a reference** — the LP2951-class part at 5.10 V.
If E7 later forces the REF5050 option, α must be revisited: put the level shifter on its own
small LDO off the protected +12 V (B5 §6's "delete the bus +5 V dependency" variant, ~66 mW)
rather than on the reference buffer.

Independent of which: **fit 470 Ω–1 kΩ in series in each of `SCLK`, `MOSI` and `CS` between
the buffer and the DAC** (C1 F5, B5 §6). At 1 kΩ into ~10 pF that is 10 ns against a 500 ns
bit period at 2 MHz and it bounds any residual clamp current to ~5 mA. Note this is a
*third* series resistor on each SPI line — see Cluster F for why that is not a contradiction.

---

## Cluster E — The current limiter and the polyfuse

### E1. Three different parts for the `F-POLY` footprint

**Fix α (B5 §2, B6 §3, B10 §1, C1 F19, C3 F16, D1 §2):** **delete** `F-POLY`. It sits at
88–109 % of its hold current in normal play, derates to ~360 mA in a 46 °C cavity, is the
largest resistance in the 12 V path, dissipates 0.26 W inside the sealed body, and — the
structural argument — **is downstream of the module's load switch, so the switch cannot
break the thermal-runaway loop ADR 0014 believes it deleted.**

**Fix β (C2 F6, A1 F10, and as an alternative in C1 F19 and C3 F16):** **resize** it to a
1812, 1.1 A hold, ≥16 V, R_init ≤ 0.1 Ω part.

**Fix γ (D1 §2):** put a **shunt SS34 reverse-polarity Schottky in the footprint the
polyfuse vacates** — *"the highest value-per-cent in the document"*, and the only fix for
the one unrecoverable electrical failure in the project (a rollover or crossover patch lead
reversing the power pair into a bonded body).

**Why they conflict.** γ explicitly assumes α. β occupies the pad γ needs. And β keeps a
thermally-hysteretic series element in the one place ADR 0014's load-switch decision exists
to remove it from — β is the fix that reintroduces the failure another fix exists to
prevent, at 1.1 A instead of 500 mA.

**Combined correct version.** α then γ: **delete the PPTC, fit the SS34 shunt (cathode to
+12 V, anode to `PWR_GND`) in its footprint.** Under correct polarity it is reverse-biased
with zero drop, which matters because the strips run on the unregulated rail and β's 0.04 V
is still 0.04 V they cannot regulate away. Under reverse polarity it holds the instrument's
rail within 0.45 V of ground while the upstream limiter folds back. **Record the
precondition in the BOM note: the shunt works only because a real 12 V current limiter
exists upstream and latches off** (E4/E5 below). Nothing else in the review states that
dependency.

### E2. Five settings for the current limit, pulling in opposite directions

| Source | Limit | Rationale |
|---|---|---|
| D1 §8 | **700 mA** | *Lower.* The limit is the de-facto thermal fuse: 8.4 W ceiling → 25 K at 3 K/W |
| A1 F10 | ~800 mA | Leave TBD at E6; expect ~800 mA |
| B6 §2 | 1.0 A | 1.7× the clamp-legal load, with a 110 ms programmed ramp |
| C2 F7, B10 §1 | 1.2 A | ~2× typical, ~1.5× WiFi peak |
| B10 §1 | 1.2–1.5 A | Must clear the *clamped* worst case, not the idle case |

**Why the window is nearly empty.** Independently rebuilt load tables converge at
**555–650 mA** for a state the firmware thermal clamp explicitly permits (B5, B6 §0.1,
B10 §1). Startup adds the charging current unless `dV/dt` is programmed. So the limit must
be **≥ ~1.0 A**. But D1 §8's table shows 1.0 A is a **12 W** instrument ceiling — 35 K of
interior rise at B6's measured 2.89 K/W, **50 K with the player's hands over 31 % of the
escape path**, which is B6 §9's "too hot to hold" region. The two requirements do not
overlap at any single setting.

**Combined correct version — separate the two jobs, which no document does:**

- **The limiter is fault protection only. Set it at 1.2 A** from the E6 measurement, with a
  **programmed 20–110 ms `dV/dt` ramp** so it never enters regulation on a normal start
  (B5 §4's point 3 — "program the ramp by dV/dt, not by letting the current limit do it").
- **The thermal bound is the firmware clamp, re-denominated in rail current, not LED watts**
  (B6 §7 option 2). ADR 0014's clamp cannot tell 3 W on the strips (which never touch the
  buck) from 3 W on the matrix (which is 600 mA of a 1 A converter). Track commanded matrix
  current separately.
- **Close the thermal loop on measurement**, per D1 §8 and D4 §10: the QMI8658C's
  die-temperature register, free, on a bus already in use, centimetres from the breath
  sensor. Fold the lighting budget back above 45 °C. That is what makes a 1.2 A electrical
  limit safe, and it is the only reason D1 §8's 700 mA can be given up.
- **Per-branch limiting** (B10 §22): raising the global limit raises the energy available to
  a shorted WS2815 to 14 W in one 5 mm package inside a sealed oak body. B10 §22's two
  500 mA fast-blow fuses in the strip feeds are the containment — **but see E3.**

### E3. The per-strip fuse is sized against the clamp, and the clamp is gone in the failure that matters

**Fix (B10 §22):** one 500 mA fast-blow fuse in each strip's 12 V feed, "2–4× headroom"
because realistic use is ~130 mA per strip and both strips at the 3 W clamp is 250 mA total.

**The composition it misses.** ADR 0014's own failure analysis — repeated in the register as
*"the firmware LED brightness clamp did not survive the failure it guarded. Brownout resets
the MCU; WS2815s latch"* — means the strips can sit at their **last latched** value with no
firmware running. B6 §0.1 puts 50 px at full white at **1.01 A, i.e. ~0.5 A per strip.** A
500 mA fast-blow fuse in that state blows, and the strip is permanently dark **inside a body
that cannot be reopened**, from a brownout rather than from a fault.

**Combined correct version.** Size the branch fuse above the *latched-full-white* current,
not above the clamp: **1 A fast-blow per strip**. Against the 14 W single-LED-short case
that is still 12 W → the fuse clears, and against a latched strip it does not. Alternatively
resolve it at the source — B10 §22's own falsifying test (short one LED on a strip offcut
and see whether it self-clears) at E6/M6, on scrap.

### E4. Four candidate limiter parts, with different package and latch behaviour

`LT1641-2CS8 (SO-8) + N-FET + sense` (register S1) · `LM5069 MSOP-10 + DPAK FET` (B5 §1) ·
`TPS2592BA SOT-23-8` (D1 §6) · `TPS1663 / TPS26600 HTSSOP-PowerPAD` (B6 §1, D1 §6).

**The constraints that select between them, each stated in only one place:**

- **Package policy** (ADR 0013): TPS26600 and TPS1663 are HTSSOP with a thermal pad — B6 §1
  proposes them and D1 §6 flags the policy violation in the same breath.
- **Latch-off, not auto-retry** — register S1 and B10 §17 both give the reason: auto-retry
  reproduces the oscillating-protection failure ADR 0014 analyses, and turns a sustained
  short into a repeating ~1 A pulse train on the rack's +12 V bus that every other module
  hears. **Only S1 states it as a requirement.**
- **86 mJ of inrush energy** (B5 §4) — `½CV²` is independent of ramp rate, so the pass
  element must absorb it. A SOT-23-6 cannot; a DPAK FET at ~3 K/W sees a 10 K rise. This
  argues against TPS2592BA in SOT-23-8 and for the external-FET topologies.
- **Overvoltage cutoff** — D1 §16 notes TPS26600 would close the instrument's OVP gap for
  free, which is the one argument for accepting the package violation.

**Combined correct version.** **S1's LT1641-2CS8 + external N-FET + sense resistor**, in
SO-8, latch-off. It is the only proposal that satisfies the package policy, the 86 mJ
requirement and the latch requirement simultaneously, and it is the one the register already
has on the table. Accept that the instrument then has **no overvoltage cutoff** and close
that separately with D1 §16's SMAJ15A at the umbilical entry — which B6 §11 and C2 F18 also
want for the TVS-splitting reason (L1), so one part serves both.

**Do not order `R_ILIM` values from C2 F7.** Its 13.4 kΩ is computed from the TPS2553's
`R_ILIM = 16100 / I_OS` relation, for a part that S1 deletes.

---

## Cluster F — Series resistors on the umbilical SPI lines

### F1. 68 Ω, 220 Ω, or 220 Ω at both ends — one resistor asked to do two incompatible jobs

**Fix α (B4 §6, C2 F11):** the existing 220 Ω on MOSI is **not source termination** —
`R_s + Z_driver` should be ≈ `Z_0` = 100 Ω. At 220 Ω the far end sits 110 mV below the
74AHCT125's 2.0 V `V_IH` for a full round trip and staircases through the threshold over
~80 ns. **Change MOSI to 68 Ω and add the same on SCLK and CS.**

**Fix β (D1 §10, B1 §9):** add **220 Ω** on SCLK and CS at the driving end, because in the
bench configuration ADR 0005 supports (instrument on USB, module unpowered, umbilical
connected — the normal E5 setup) the ESP32 drives 3.3 V into the unpowered buffer's input
clamp. `(3.3 − 0.7)/220 = 11.8 mA`, inside the AHCT's ±20 mA `I_IK`.

**Fix γ (B10 §16):** **220 Ω at both ends**, for the cable-short case (+12 V on pin 3 is
adjacent to MOSI on pin 4 in the T568B map).

**Why they cannot all be applied.** α and β are the **same resistor** with opposite
requirements. At 68 Ω, β's clamp current is `2.6/68 = 38 mA` — nearly twice the rating β
exists to respect. At 220 Ω, α's staircase is exactly the "plain buffer, not a Schmitt
trigger" problem ADR 0004 itself notes. γ makes it worse: 440 Ω total launches even less
into the line. And B8 §5 wants a *third* thing from the same component — a **20–30 ns edge**
for crosstalk, which correct source termination specifically does not give.

**Combined correct version — put each job where it does not fight the others:**

| Position | Value | Job |
|---|---|---|
| Instrument, at the GPIO (driving end) | **68 Ω 1 %** ×3 | Source termination. `68 + ~32 = 100 Ω` → one full-amplitude step, no staircase (α) |
| Module, in series before the 74AHCT125 input | **220 Ω 1 %** ×3 | Clamp/fault limiting (β, γ). In series with a high-impedance input it does **not** change the line's far-end reflection, so α is untouched; it only isolates the input capacitance |
| Module, between the AHCT output and the DAC pin | **470 Ω–1 kΩ** ×3 | Cross-rail clamp limiting into the DAC (C1 F5, B5 §6) |
| Firmware | lowest working `GPIO_DRIVE_CAP` | Edge rate (B8 §5, D3 §10, C2 F11–12). **This is the lever for edge rate, not the resistor** |

Nine resistors, about twenty cents, and all three requirements are met. The key insight none
of the three documents reaches: **source termination must be at the driver and fault
limiting must be at the receiver, and they are therefore different parts.**

One residual, stated honestly: neither 68 Ω nor 220 Ω protects the ESP32 GPIO against
`+12 V` shorted onto MOSI in the cable (`12/220 = 55 mA` into a clamp). That case is the
TVS array's, and see E5/L1 — at a 1.2 A limiter setting the array must survive it
**indefinitely**, which is a requirement no document states.

---

## Cluster G — The ADC branch

### G1. `C-AA-ADC`: 4.7 nF vs 47 nF

**Fix α (B1 §1):** **4.7 nF** → 5.64 kHz, 39 dB at 500 kHz, **28 µs** of group delay,
recovering 1.29 ms. B1's argument: the disturber is *"~0.2 LSB before any filtering at
all"*, so 220 nF is one to two orders more than the job needs, paid for in milliseconds on
the most latency-sensitive path in the instrument.

**Fix β (B6 §8, B8 §2, B9 §4, C1 F9, C2 F1, D3 §13, and the register):** **47 nF** →
564 Hz, 58.9 dB at 500 kHz, 282 µs. Six documents converge on it because it delivers
*exactly* the two numbers ADR 0003 asserts, which is strong evidence 47 nF is what the
arithmetic was done for and 220 nF was a transcription error.

**Why it matters which.** These are not interchangeable. 4.7 nF puts the ADC's corner at
5.6 kHz while the analog CV path is band-limited at 482 Hz (Cluster A5) — **the digital copy
and the analog copy of breath then have different bandwidths by a factor of twelve.** ADR
0003's curve shaping, the mod-channel breath source, USB MIDI and the display are all fitted
to the digital copy; the jack carries the other one. B8 §2 names this explicitly: *"the
response the player tunes against is not the response at the jack."*

Against that, B8 §6's aliasing analysis shows a **single pole is not an anti-alias filter
for a 4 kHz sampler** at any value — the WS2815 PWM's second harmonic lands in
`|2·f_pwm − 4000| ∈ [0, 400] Hz`, inside the breath band, with only 16 dB of rejection at
564 Hz and 0 dB at 5.6 kHz.

**Combined correct version.** **47 nF C0G 1206 50 V** (C2 F1's dielectric argument is
independent and correct: X7R is microphonic in an instrument that is held, tapped and blown
into, and its voltage coefficient moves the corner with signal). Then take **B8 §6's second
pole**, but not where B8 puts it — see G3. Add the resulting **282 µs as an explicit row in
`latency-budget.md`**, which every one of the seven documents asks for.

### G2. The second ADC pole cannot go in the buffer's feedback

**Fix (B8 §6):** *"Make the ADC filter two-pole. The OPA2197 buffer is already there; an RC
in its feedback plus the existing RC gives a 2-pole ~500 Hz response."*

**Why it cannot be applied as written.** That buffer is `U-BUF`'s second half, and its output
is **not** the ADC branch — it drives the umbilical as well (ADR 0003's split). An RC in its
feedback band-limits the **analog CV path** to the same corner, which is exactly what A5's
resolution moves *off* the instrument end to save 318 µs, and B1 §7 warns the capacitor must
not land on that output at all.

**Combined correct version.** Put the second pole in the **ADC branch only**: a small RC in
the divider leg (e.g. split the 10 kΩ upper leg into 5 kΩ + 5 kΩ with 47 nF at the midpoint,
or add 4.7 kΩ + 22 nF between the divider and the ADC pin). Two poles at ~560 Hz give 32 dB
at 3.6 kHz instead of 16, cost one resistor and one capacitor, and leave the CV path alone.
Alternatively take B8 §6's *other* proposal — **phase-lock the LED update to the ADC sample
at a fixed offset** — which is free, is firmware-only, and is the only fix that also
addresses B8 §4's matrix ground bounce.

### G3. Four claimants for the MCP3202's one spare channel — and one of them needs both

| Source | Use of CH1 | Channels consumed |
|---|---|---|
| B1 §5 | **Pseudo-differential**: CH1 to the analog star point, so the carrier's ground offset cancels in the difference | **2 (CH0 + CH1)** |
| D3 §14, D2 §22, C1 F10 | Divided copy of the buffered **5.000 V reference**, so `breath_code / ref_code` is independent of the dev board's 3.3 V LDO | 1 |
| D4 §6 | Divided **umbilical +12 V**: presence detect, brownout evidence, cable-intermittency detection | 1 |

**Why only one can be built.** B1 §5's pseudo-differential mode consumes the converter
entirely — there is no spare channel afterwards. The other two are one channel each and
mutually exclusive. All three are described by their own document as free, and two of them
(D2 §22, D4 §6) are tagged **one-shot, unretrofittable after bonding**.

Additionally, **B6 §10 proposes a dedicated 3.3 V LDO for the MCP3202** at the analog star
point, which achieves most of what the ratiometric fix achieves by a different route — and
which, if built, makes D3 §14's divider reference a different and less useful number.

**Combined correct version, ranked by what is unrecoverable:**

1. **CH1 → divided umbilical +12 V** (D4 §6). It is the only one of the three that is
   *structurally* unobtainable later: the instrument has no other way to observe the module,
   the cable is a declared consumable whose expected failure is intermittency, and there is
   no brownout evidence anywhere in the system today (D4 §15). It also serves D2 §17's
   highest-ranked GPIO claim, freeing GPIO3/4 for the display-board recovery path.
2. **B1 §5's ground-offset problem is solved structurally instead**, by B6 §10's separate
   3.3 V LDO for the converter referenced to the analog star, plus B8 §4's Kelvin rule for
   the carrier layout. That is the fix B1 §5 itself calls "a structural fix for a structural
   problem", reached from the supply side rather than the input side.
3. **The ratiometric reference check (D3 §14) moves to firmware**: with the converter on its
   own LDO the residual is a fixed scale error, and the breath span is calibrated anyway.

If the +12 V sense is instead routed to **GPIO4** (both GPIO3 and GPIO4 are ADC1 channels,
per ADR 0007 and C5 F5), CH1 is free for the reference divider and both are had. **That is
the better answer and it requires D2 §17's pin ranking to be decided before E13.** Note
C5 F5's caution: GPIO3 is a strapping pin; prefer GPIO4.

### G4. The MCP3202 cannot run at the clock the DAC needs

**Fact (C1 F10):** the MCP3202's maximum clock is ~1.1 MHz at 3.3 V. **Fix (A1 F4, B4 §5,
B8 §5, C5 F3):** the umbilical SPI must run at **2 MHz** or the 4 kHz loop does not close.
Both devices are on **SPI2** (ADR 0001).

**Why this is a conflict and not a note.** Over-clocking a SAR produces subtly wrong codes
with no error flag. The fix is per-device clock configuration on a shared host — a one-line
firmware matter that is **written down nowhere**, and which C5 F13 then complicates: the
module's watchdog must **not** be retriggered by ADC traffic on the shared bus, or a firmware
fault that stops updating the DAC while breath sampling continues retriggers it forever.

**Combined correct version.** Three statements, all in ADR 0001 or `firmware/README.md`:
per-device SPI clocks (DAC 2 MHz, ADC 1 MHz); the watchdog retriggers from the **DAC's
`CS`/`SYNC` edge only** (C5 F13, D1 §7); and the 2 m umbilical is a permanently attached stub
on the ADC's bus, so `R-MOSI-SER` and the module-side idle pulls are load-bearing for the
ADC too and must not be "simplified away".

---

## Cluster H — The output stage

### H1. The BAV99 clamps: at the jack, or inboard of the 1 kΩ

**Fix α (C2 F20, B9 §5, ADR 0006 as written):** clamps on the **jack side** of
`R-OUT-PROT`. *"On the op-amp side they clamp nothing useful and put the op-amp's output
directly across an external fault."*

**Fix β (B10 §8):** clamps **inboard**, between the op-amp output and the 1 kΩ. A +15 V
bench supply through ~0.5 Ω of patch cable into a jack-side clamp is **5.4 A** against a
BAV99's ~200 mA rating — the diode is destroyed in microseconds and the op-amp is then
exposed. **First part to fail: the BAV99.** Inboard it is 2.7 mA.

**Who is right, and the thing neither notices.** β's fault analysis is correct and α's is
not — α assumes the external source is current-limited, and a bench supply is not. But β has
two composed consequences it states and one it does not:

- β moves the whole fault to the resistor: an external +12 V against an output at −10 V puts
  22 V across 1 kΩ = **484 mW**, which is ~2× a 1206's rating. B10 §7 and C2 F5 both
  independently upgrade `R-OUT-PROT` from 0805 to 1206 — so **the two fixes together still
  overrun the upgraded part.**
- β **deletes the argument that chose the part.** ADR 0006 picked BAV99 over BAT54S because
  *"2 µA of Schottky leakage through the 1 kΩ output resistor is 2 mV, which is 2.4 cents"*.
  Inboard, the leakage flows out of the op-amp's low-impedance output node and the error is
  **exactly zero for any diode**. B10 §8 notices this as a benefit; C2 F20 and C1 F19
  simultaneously confirm BAV99-over-BAT54S as *"one of the best calls in the document set"*,
  which after β it no longer is.

**Combined correct version.**

- **Clamps inboard** (β): `op-amp → BAV99 to ±11.65 V → R-OUT-PROT → filter C → jack`.
- **`R-OUT-PROT` at 1206, and rated for the fault**: 1206 at 250 mW covers the sustained
  short (141 mW) and the output-to-output case (100 mW). The 484 mW external-rail case is a
  **transient fault**, and the right answer is to accept an open resistor — B10 §8's own
  argument, worth stating explicitly in the BOM note: *"this resistor is the sacrificial
  element; open-circuit is the designed failure and it kills one channel, not the module."*
- **Keep BAV99, and record that the reason changed.** It is still the right part (leakage,
  ratings, the SOT-23 series pair maps onto a rail clamp exactly) but the 2.4-cent argument
  is void once the clamp is inboard, and C2 F20 / C1 F19 / B9's confirmations of it need
  amending or someone will "optimise" to BAT54S on the strength of an obsolete comparison.

### H2. Six output filter capacitors, three sets of values, and one channel that should have none

| Channel | B3 §7 / B9 §5 | B4 §4 | C2 F2 | D3 §8 |
|---|---|---|---|---|
| Pitch | 10 nF (15.9 kHz) | — | 33 nF (4.8 kHz) | 33 nF (4.8 kHz) |
| Mod ×4 | — | 82 nF at the jack **+ 10 nF at the summing node** | 82 nF (1.94 kHz) | 150 nF (1.06 kHz) |
| Breath | — | — | 330 nF (482 Hz) | 330 nF (482 Hz) |

**The conflicts.**

- **Pitch, 10 nF vs 33 nF.** B3 §7 verifies 1 kΩ × 10 nF settles a one-octave leap to within
  1 cent in **71 µs** and matches the latency budget's "~10 µs". C2 F2 and D3 §8 both cite "a
  review resolved 5 kHz" and land at 307 µs. Both are musically fine; they are not the same
  part and the budget line differs by 30×. This needs deciding, not averaging.
- **Mod, 82 nF vs 150 nF vs two poles.** B4 §4 computes the image at −25.2 dB with one 2 kHz
  pole — *"the ADR rejected the 2 kHz update rate because −12.6 dB was unacceptable and then
  accepted −25.2 dB without computing it"* — and proposes **two** poles. D3 §8 reaches −38 dB
  with one pole at 1.06 kHz. B9 §13 reaches the same −25.5 dB number and calls it a judgement
  rather than a calculation.
- **B4 §4's first pole is at the summing node and collides with `R-OPAMP-IN`** — see H3.
- **Breath's 330 nF may be the wrong part entirely.** B8 §11 and B9's inventory both note the
  ~2 kHz breath reconstruction filter is *"vestigial from the digital-breath era"* — breath
  never enters the DAC, so there are no steps to reconstruct. A5 already places one 482 Hz
  pole at the module input. **A second 482 Hz pole at the breath jack would give 660 µs of
  group delay for nothing**, which is C2 F22's arithmetic arriving by a different route.

**Combined correct version.**

| Channel | Part | Corner | Why |
|---|---|---|---|
| Pitch | **10 nF C0G 1206** | 15.9 kHz | B3 §7's settling number is the one that is verified against a musical requirement (1 cent in 71 µs), and it is what the latency budget already carries. C0G is non-negotiable — an X7R here is a literal microphonic detuning element |
| Mod ×4 | **82 nF film + a second pole at the stage input** (B4 §4) | ~1.9 kHz × 2 | Two poles give −31 dB against a 400 Hz source and −41 dB against the realistic 160 Hz breath source. Film, not X7R: 20–40 % DC-bias loss at 10 V moves the corner 30 % and makes it signal-dependent |
| Breath | **none at the jack** | — | The 482 Hz pole already exists at the module input (A5). Delete the row |
| Mod 4 only | reserve a **10 nF** alternate footprint | 16 kHz | D3 §20's gate provision — but see N3 for which channel the gate actually is |

### H3. `R-OPAMP-IN`: three incompatible placements for one 1 kΩ resistor

**Fix α (B4 §4):** use it as part of the mod channels' first filter pole —
*"(1 k + 10 k) ∥ 40 k = 8.63 kΩ; 10 nF C0G to AGND gives 1.84 kHz"*. That arithmetic places
the 1 kΩ **between the DAC and the divider**.

**Fix β (C2 F21):** *"The 1 kΩ must go between the divider midpoint and the op-amp pin. If
it goes between the DAC and the divider it is inside the ratio and corrupts the matched
network — the exact failure ADR 0006 bought the LT5400 to prevent."*

**Fix γ (D3 §17):** it is already inside the network; quantified as **2 % gain error and a
1 % zero error**, absorbed by firmware — so make the input leg `9 kΩ + 1 kΩ` and be correct
by construction.

**Why they conflict.** α's stated arithmetic requires exactly the placement β forbids. γ
accepts the error and fixes it by re-splitting the resistor, which changes α's Thévenin
impedance and therefore α's capacitor value.

**Combined correct version.** Take γ's construction and recompute α against it:
**input leg = 9 kΩ + 1 kΩ**, so the network ratio is exact and the 1 kΩ still exists as a
discrete clamp limiter; the filter capacitor then sees `10 k ∥ 40 k = 8.0 kΩ`, giving
**10 nF → 1.99 kHz** (α's target, one component value changed). Keep the full 1 kΩ
**outside** the network wherever the DAC really drives a follower — the ch6 zero stage and
the ch7 mod-offset buffer — where the original reasoning holds exactly, and **increase the
quantity from 5 to 7** (B9 §9, C2 F21). Add C2 F21's bolded counter-rule for the REF pin
(B1 above).

---

## Cluster I — The watchdog

### I1. `CLR`'s idle pull has two opposite specifications

**Fix α (D1 §7):** *"a pull on `CLR` that holds it **asserted** through the microseconds of
indeterminate monostable output at power-up"*, plus an MCP131-450 supervisor that forces the
safe state whenever the DAC rail is out of spec.

**Fix β (D3 §16):** *"`CLR` pulled to its **inactive** state through 10 kΩ so that the
watchdog is the only thing that asserts it — and so that an unpopulated or failed watchdog
leaves the DAC running rather than held in reset."*

**Why they cannot both be applied.** One resistor, two polarities. And the choice decides
what happens on **three other fixes**: B6 §6 and D3 §11's breath mute are driven from the
same node, so β's "failed watchdog leaves the DAC running" also means *failed watchdog leaves
breath live* — reinstating the exact stuck-CV failure the watchdog exists to prevent, on the
channel the register already identifies as the one the watchdog cannot reach (W13).

**Combined correct version.** α. The failure direction of a safety device must be *safe*, and
D3 §16's convenience argument ("a failed watchdog leaves the DAC running") is a bring-up
argument, not an operating one. Serve the bring-up case with **D2 §10's explicit disable
jumper** instead — clearly labelled, fitted during E7–E10, removed at E12 as a checklist
item — which is a deliberate act rather than a latent default. Add D2 §10's test pad on
`CLR` and D4 §6's panel LED so the state is never in doubt.

### I2. Four retrigger sources, and one of them defeats the device

**α:** `SCLK` (the obvious reading of "SPI traffic").
**β (C5 F13):** the **DAC's `CS`/`SYNC` falling edge only** — because the DAC and the
MCP3202 share SPI2, so with α a firmware fault that stops updating the DAC while a healthy
breath-sampling task keeps reading the ADC **retriggers the watchdog forever.**
**γ (D1 §7):** `CS` **rising** edge, so the output loop's sanity check can stop asserting
`CS` when it fails.
**δ (B10 §6):** whichever it is, it must come from the **buffered 5 V side**, because 3.3 V
does not meet a 74HC part's `V_IH` of 0.7 × 5.25 = 3.68 V.

α and β/γ are mutually exclusive; β and γ differ only in edge and are compatible. δ is a
constraint on all of them and interacts with the OE gating (B10 §4): if `OE` is deasserted
when the instrument is absent, the buffered side is Hi-Z, so the trigger must have a defined
level there — which is exactly what B10 §4's DAC-side pulls provide.

**Combined correct version.** **Retrigger from the DAC `CS` rising edge, taken from the
buffered (5 V) side, with the DAC-side idle pulls fitted** (`SYNC` to AVDD, `SCLK`/`DIN` to
ground, 10 kΩ each — B10 §4, D1 §12, which are the same fix proposed twice). Rail: the DAC's
own 5.10 V, so "DAC alive" implies "watchdog alive" (B10 §6, D1 §7). Timing:
**220 kΩ + 1 µF PET film → 99 ms** (C2 F23), and film specifically — an electrolytic's
leakage corrupts a monostable's timing ramp and X7R's DC-bias coefficient makes the timeout
wander by tens of percent.

### I3. The OE gating polarity, and the bench mode that needs it inverted

**Fix α (B10 §4):** the `'125`'s OE is **active low**, so the naive divider from umbilical
+12 V enables the buffer in exactly the state the gating exists for. Needs one NPN or N-FET
to invert. **Failure direction must be "disabled".**

**Fix β (D3 §9):** the same gating needs a **supervisor or FET with hysteresis**, because the
limiter *deliberately ramps* the rail and a plain divider crosses the AHCT's indeterminate
band over ~313 µs on every switch-on — recreating the crowbar condition the gating was added
to eliminate.

**Fix γ (D2 §11):** a **three-way link — gated / forced-on / forced-off** — because ADR 0004
also claims the module can be brought up standalone, and a bench dev board driving SPI has no
reason to be feeding +12 V back up a cable.

These compose, but only if drawn together: γ's forced-on position must not defeat α's failure
direction, and β's hysteresis must be in the sense path, not the link. **Combined:** an
N-FET with a 1 MΩ hysteresis feedback from drain to the divider node (D3 §9's version (b)),
inverted per α, with γ's 3-pin link on the OE net itself and a 100 nF across the lower
divider leg for toggle bounce.

One consequence worth recording, from B5 §6: **the OE gating is also what makes the
power-down sequencing safe** for the three SPI lines — the umbilical node collapses in ~6 ms
against 40 ms for the DAC's rail. That is an undocumented second purpose, and γ's forced-on
link defeats it if left fitted. Add it to the E12 removal checklist alongside I1's jumper.

---

## Cluster J — The key inputs

### J1. Three different pull-up/filter networks for 18 switches

| Source | Pull-up | Cap | Series | Release filter | Rationale |
|---|---|---|---|---|---|
| D1 §4 | 10 kΩ | 1 nF | — | 10 µs | LED-edge charge injection: 20 pC into 1 nF = 20 mV |
| D3 §3, register W14 | 10 kΩ | 10 nF | 100 Ω | 93 µs | −54 dB at 800 kHz; free hardware release filter |
| B10 §23 | **2.2 kΩ** | — | — | — | **A saliva film bridging a switch pin to the grounded plate is ~10 kΩ; at a 10 kΩ pull-up a press is read below 3.2 kΩ.** One order of margin is not enough |

**Why they conflict.** The value is a single number and the three requirements pull
differently. B10 §23's is the one the other two miss entirely, and it is specific to *this*
instrument: the cavity must leak for the pressure reference (18 unsealed cutouts), the plate
is bonded to `PWR_GND`, and the switch pins sit 1–2 mm from it. Neither D1 §4 nor D3 §3
considers moisture. Conversely B10 §23 has no capacitor, and D1 §4's arithmetic shows a
pull-up alone cannot hold the node during a WS2815 edge — `C·dV/dt = 4 pF × 1 GV/s = 4 mA`,
which no resistor holds down.

**Combined correct version — one network that satisfies all three:**

```
3V3 ──[2.2 kΩ]──┬──── 74x165 input
                │
              [47 nF]
                │
               GND        switch ──[100 Ω]── same node, other side to GND
```

- **Saliva:** trip threshold moves to `R < 700 Ω`, which a condensation film will not reach.
- **LED coupling:** 180 pC into 47 nF = **3.8 mV**; pole at 1.54 kHz, −54 dB at 800 kHz.
- **Release filter:** `2.2 k × 47 n = 103 µs`, crossing `V_IH` at ~96 µs — D3 §3's free
  hardware release filter, preserved.
- **Press:** the 47 nF discharges through 100 Ω in ~5 µs; the leading edge stays instant, so
  ADR 0001's asymmetric debounce is untouched.
- **Cost:** `3.3 V / 2.2 kΩ = 1.5 mA` per *closed* key; a fingering closes ≤8, so ~12 mA,
  plus the spare bits (J2). Against an instrument drawing 400–600 mA this is free, but it
  is 3× the entire 3.3 V rail load the design currently assumes (B6 §0.1: ~5 mA) and belongs
  in the budget table.

### J2. The 14 spare chain bits are committed five times over

| Claimant | Bits | Source |
|---|---|---|
| Fixed marker pattern | 4–6 | ADR 0001, A2 §24 |
| Config-mode input | 1 | ADR 0012, C5 F5 |
| Per-segment marker localisation | +3 (one per additional segment) | D2 §12 |
| Two to three extra switches (octave, hold, preset) | 2–3 | D5 §5 |
| `IO0` for display-board recovery flashing | 1 | D2 §17 |
| Hardware heartbeat LED | 1 | D2 §20 |
| **Total claimed** | **12–15** | against **14** |

Two of these are also wrong as written. D2 §20 proposes taking the heartbeat *"from a spare
74x165 bit's LED driver"* — a 74x165 is an **input-only** shift register and cannot drive
anything. And D1 §4's *"the 14 unused bits get tied hard to a rail"* is incompatible with
D5 §5's extra switches and with D2 §17's `IO0`, both of which need them live.

**Combined correct version.** Allocate them once, in `config/key-layout.yaml`, before **M3**
— which is the real deadline, because a switch that is not in the plate DXF never exists
(register, "the missing dimension"):

| Bits | Use |
|---|---|
| 4 | Marker pattern, mixed polarity, **one per cluster board** — which gives D2 §12's per-segment localisation for free rather than for three more bits |
| 1 | Config-mode input |
| 3 | Extra switches: octave up, octave down, hold — decided at M2, in the DXF by M3 |
| 6 | Tied hard to a rail, mixed polarity, documented as reserved |

`IO0` goes to GPIO3/4 or the external diagnostic connector (D2 §17's own fallback), and the
heartbeat LED to a real GPIO or an AHCT125 spare gate (D2 §20's own alternative).

---

## Cluster K — Instrument power

### K1. Two USB-OR elements with opposite side effects on a third part

**Fix α (C1 F14):** a **Schottky** (PMEG4050EP or SS54, ~0.35 V at 1 A) between the buck
output and the dev boards' `5V` pins, with the LED level shifter kept on the **undiodéd**
5.0 V. C1 F14 names a side benefit: dropping the boards' supply to 4.65 V moves the onboard
WS2812C matrix's `V_IH` from 3.5 V to 3.26 V and puts the board's 3.3 V GPIO14 drive
**above** threshold, fixing a known Waveshare marginality **for free**.

**Fix β (D1 §5):** an **LM66100 ideal diode** (79 mΩ, 32 mV at 400 mA), explicitly *because*
"a plain SS14 costs 0.35 V… do not spend 350 mV there", citing the WS2815 threshold as the
reason.

**Why they conflict.** They are alternatives for one part, and **β's stated reason is void**:
the register resolves the WS2815 threshold question in the design's favour — the part drops
12 V to 5 V internally, `V_IH ≈ 3.5 V`, and a 74AHCT125 on 5 V clears it with ~1.1 V of
margin even at the R-78E's worst-case 4.75 V. So β pays a part and a footprint to protect a
margin that does not need protecting — **and in doing so it forfeits α's free fix for the
onboard matrix**, which is a real marginality on the board actually selected.

**Combined correct version.** α: **a Schottky, with the LED level shifter upstream of it.**
Check the dev boards' own LDO dropout at 4.65 V in at E1 (C1 F14's caveat: an AMS1117 at
400 mA is thin). Record the matrix-threshold side benefit in the ADR so nobody later
"improves" the diode to an ideal one and reintroduces a marginal 3.3 V drive into a 5.0 V
part inside a bonded body.

### K2. One buck or two — and the fixes that assume each

**ADR 0013 and `latency-budget.md` specify one regulator per board.** ADR 0005 quietly
reduced it to one and did not argue the reduction (B6 §7, A3 F12). B6 §7 wants the second
restored; at the clamp-legal worst case state (B) the single R-78E5.0 carries **995 mA on a
1 A part**.

**The compositions nobody traced:** a second buck needs a **second input LC filter** (K3),
a **second OR diode** (K1), and it changes the inrush energy the limiter must ramp (E2). And
B6 §7's own numerical argument evaporates if B6 §7's *other* recommendation is taken —
re-denominating the clamp in rail current rather than LED watts caps the matrix at ~400 mA
and brings the single buck back inside rating. **The two halves of one finding make each
other unnecessary, and the document proposes both.**

**Combined correct version.** Take the firmware half first (free, and it is required anyway
for E2's thermal bound), then decide the second buck at **E1 from the measured idle and
WiFi-active currents** — which E1 already schedules. If both boards together stay under
300 mA with WiFi active, the isolation argument stands on its own merits but the headroom
argument does not, and one buck plus `C-BULK-DISP` is sufficient.

### K3. Three specifications for the buck's input filter, and one that fights its own document

| Source | L | C | Damping |
|---|---|---|---|
| B6 §4 | 22 µH | 10 µF X7R | 100 µF/25 V electrolytic (ESR 0.5–1 Ω) |
| B10 §29 | 47 µH | (unstated) | electrolytic with ~0.2 Ω ESR |
| C2 F9 | 47 µH, I_sat ≥1.5 A, DCR ≤0.15 Ω | **470 µF 25 V** | 100 µF + 1 Ω series branch |

**Why C2 F9 fights itself.** C2's own Finding 7 concludes *"hold the total instrument bulk
to ≤1.5 mF"* because the limiter must charge it. Finding 9 then adds **570 µF** at the buck
input, in the same document, without counting it. With 2 × 470 µF at the strips + 330 µF at
the display board + 330 µF at the real-time board (C2 F23) + 570 µF at the buck input, the
total is **2.17 mF**, over its own ceiling.

**Combined correct version.** B6 §4's numbers, which give the margin the criterion asks for
at the lowest capacitance: **22 µH shielded, I_sat ≥1.5 A, DCR ≤0.15 Ω; 10 µF X7R + 100 µF
25 V 105 °C electrolytic whose ESR does the damping.** `Z_out,peak ≈ 0.7 Ω` against the
converter's `−20.8 Ω` — a 30× margin, against C2 F9's own 2.8×. Total instrument bulk then
lands at ~1.7 mF, and the limiter's programmed ramp (E2) covers it. **Add the resulting
number to one place** and keep the running total there, because four documents each add
capacitance and none subtracts.

### K4. Module entry bulk: add 1000 µF, or remove 1.1 mF

**Fix α (B5 §8):** add **1000 µF + 10 µF at the module's entry node**, downstream of the
reverse diode and upstream of the branch beads. *"Branching cannot isolate a shared node —
but a low-impedance shunt at that node can, and that is precisely what entry bulk is."*
7.5 dB less injected ripple on the rack bus, and it is the only component assigned to E6's
exit criterion *"no noise injected back into the rack"*.

**Fix β (C2 F10):** the existing `4 × 470 µF = 1.88 mF` of module entry capacitance is large
by Eurorack standards and is the inrush the earlier review flagged; **use 100 µF on the
+12 V analog, −12 V and +5 V branches**, dropping the total to 770 µF.

**Why they conflict.** Opposite directions on the same node, each correct about a different
thing: β is right that 470 µF on a 45 mA op-amp branch buys nothing and costs hot-plug
inrush; α is right that the *umbilical* branch needs a low-impedance shunt at the shared
node. They are compatible only if stated as **per-branch**, which neither does.

**Combined correct version.** β's reduction on the three quiet branches (100 µF each) **plus**
α's bulk on the umbilical branch (1000 µF + 10 µF). Net 1.31 mF — less than today, with the
shunt where the current actually swings. Then B5 §8's restated rule belongs in ADR 0004:
*bulk at the load bounds the current the load pulls from upstream; bulk at the entry bounds
the voltage that current develops on the shared node. They are different jobs and you need
both.*

---

## Cluster L — Protection parts

### L1. Two documents re-specify the TVS array that three others delete

**Established (S6, C1 F2, C2 F18, B6 §11, B10 §13):** `U-TVS-UMB` is an **SP3012-06UTG, a
~5 V working-voltage array**, drawn across a bus that includes the +12 V conductor. It
conducts continuously and destroys itself on first power-up, **inside the bonded body**. The
register adds that distributor data says it is discontinued and in a 14-UDFN package the
policy forbids. Fix: split by voltage — a 4-channel 5 V array on the signal lines, a 15 V
standoff part on +12 V.

**Fix α (D1 §9):** add *"a second **SP3012-06UTG** (or equivalent 6-line array) at the
module's etherCON, clamping the five signal conductors (**+12 V**, SCLK, MOSI, CS, BREATH)"*
— and, as the closing argument, *"same part number already in the BOM, so no new sourcing."*

**Fix β (D3 §12):** *"One SP3012-class 6-channel array at the module etherCON covering SCLK,
MOSI, CS **and +12 V**."*

**Why this is the clearest case in the review.** Both α and β **reproduce the showstopper**
at the other end of the cable, and α's efficiency argument — reuse the part already in the
BOM — is precisely why: the part in the BOM is the wrong one. Two documents that never read
S6 propose adding a second instance of the defect.

**Combined correct version.** The module end genuinely needs protection (B10 §14's ESD
analysis is good: a discharge to the key plate arrives at the module as a ~1.9 kV wavefront
into a 74AHCT125 that has the least series impedance in front of it). Fit at **both** ends:

- **A 4-channel 5 V-class array on `SCLK`, `MOSI`, `CS`** only — not on +12 V, not on
  `BREATH`.
- **A 15 V standoff unidirectional TVS (SMAJ15A) on the +12 V conductor**, at each end. One
  part also closes D1 §16's instrument OVP gap and E4's loss of the TPS26600's OVP feature.
- **`BREATH` and `AGND` get BAV99, not the array** — D3 §12 is the only document that gives
  the reason and it is decisive: array leakage of ~1 µA through the 10 kΩ protection
  resistors is **10 mV of temperature-dependent offset** on the breath channel, which is the
  same argument ADR 0006 already accepted for the CV jacks, with 10× the series resistance.
  D1 §9 puts `BREATH` on the array.
- Source a **currently-orderable** part number. The SP3012 line item is not just mis-voltaged.

### L2. The raised current limit makes every clamp a continuous-duty part

**Composed, from E2 + F1 + L1, stated nowhere.** With the limiter at 1.2 A, no
conductor-level fault the TVS arrays exist to clamp will ever trip it:

| Fault | Current through the clamp | Trips a 1.2 A limiter? |
|---|---|---|
| +12 V → MOSI through 220 Ω at the module | 55 mA | no |
| +12 V → BREATH through 10 kΩ | 1.1 mA | no |
| Crossover cable: +12 V onto the buffer output through 1 kΩ | 11 mA | no |

So each clamp must survive its fault **indefinitely**, not as a transient. A BAV99 at 11 mA
is comfortable (250 mA rating). An ESD array at 55 mA is not — ESD arrays are rated for
8/20 µs pulses, not DC. **Requirement to add:** either raise the module-end series resistance
on the SPI lines to ≥1 kΩ (which F1 shows is free, because that position is a receiver
isolation resistor and not a termination), or specify a clamp rated for continuous
conduction. 1 kΩ gives 12 mA and the problem disappears.

---

## Cluster M — Panel and mechanical

### M1. The module panel is already 0.5 mm over, and seven more indicators are proposed

**Established (C3 §4):** usable height is 108.5 mm; the honest budget with real part sizes
runs to **118.5 mm at a 13 mm jack pitch**, closing with ~5 mm to spare only at 11 mm.
Separately, C3 §4 shows the **knobs do not fit**: two Alpha 9 mm pots on a 30.18 mm panel
leave `D ≤ 13 mm`, which excludes essentially every knob a Eurorack builder owns.

**Claimants on the remaining space:**

| Source | Ask |
|---|---|
| D1 §13 | 2 LEDs (green from the limiter output, red from `FAULT`) |
| D4 §6 | 1 module health LED (green/amber/red from the watchdog) |
| D2 §18 | **5** LEDs (+12 V, −12 V, +5 V, FAULT, LINK LOST) |
| D2 §19 | 1 INSTRUMENT ALIVE LED |
| D2 §10 | watchdog-disable jumper |
| D2 §11 | 3-way OE link |
| C3 §4 | move the etherCON to the bottom of the panel |
| C3 §3 / W9 | make it a **two-board module**, because the etherCON cannot be braced to a single ≤28 mm board |

**Combined correct version.** The jumpers are not panel items — put them on the PCB, where
D2 §11's own three-pin header belongs. For indicators, take D2 §18's *diagnostic* reasoning
and D1 §13's *part count*: **one RGB LED or two bicolour LEDs**, multiplexed by state rather
than one per rail, driven by discrete logic from `FAULT`, `CLR` and the −12 V presence —
which is three signals and one visible position. Rail-presence LEDs go on the **PCB edge**,
visible with the module out of the case, where they are worth as much and cost no panel.
Take C3 §4's etherCON relocation to the bottom: free, frees the top for the knobs, and stops
the 60 mm carrier draping the cable over both knobs and all six jacks.

**Order dependency:** the two-board module (W9, C3 §3) must be decided **before** the panel
layout and before B5 §3 / B7 F4's ground-topology rule, because *"`PWR_GND` runs from the
etherCON to the bus header's ground pins as a dedicated wide pour"* becomes a pour **plus a
board-to-board connector**, and the connector's resistance is exactly the quantity that rule
is trying to hold under 5 mΩ.

---

## Cluster N — Firmware and the loop

### N1. The RC on DAC channel 7 reintroduces the transient the LDAC fix deletes

**Fix α (B4 §2):** the mod offset and the four mod codes are two DAC registers inside one
transfer function, so *any* interval in which one has been updated and the other has not is
full-scale error on four outputs. Use the part's **software LDAC** — `WriteToInputRegister`
for all five, then one `UpdateRegister` — so they move together. Without it, every power-on
and every watchdog recovery puts a **5.5–9.3 V, 0.1–0.2 ms spike on four modulation
outputs**.

**Fix β (B10 §9):** *"RC the channel-7 output before its buffer, τ ≈ 100 ms… a corrupt word
never reaches the output at all."*

**Why they cannot both be applied.** β makes ch7 a **slow** node. α's entire mechanism is
that ch7 and the mod codes change **simultaneously**. With β fitted, at power-on the mod
codes arrive in microseconds and the offset ramps over ~500 ms, so
`V_out = 4 × (V_dac − V_offset(t))` sweeps from +11.45 V down to 0 V across half a second on
all four jacks. β does not reduce α's transient; it **extends it by a factor of 2500** and
converts an audible thump into an audible sweep.

**Combined correct version.** α, unmodified, plus the **stateless-refresh rule** (S4,
B4 §1, D4 §12): rewrite ch7, the internal-reference enable, the clear-code register and the
LDAC mask on every pass or on a slow cycle. That is what protects against a corrupted ch7
word — self-correction in 250 µs, which is strictly better than β's 100 ms ramp — and it is
free against a loop budget that already books six words while five are written. **Reject the
RC on ch7.** B10 §10's identical RC on **ch6** is fine and should be kept (B2 above), because
ch6 is not inside a difference with a fast-moving partner.

### N2. The loop budget is spent more than once

`latency-budget.md` books **136 µs of a 250 µs period** (six DAC channels at 16 µs + ADC
24 µs + keys 16 µs = 54 % duty), at 2 MHz. The proposals add:

| Addition | Source | Cost |
|---|---|---|
| ch7 refreshed every pass (7 words, not 6) | S4, B4 §1, B10 §9 | +16 µs |
| Software-LDAC update command | B4 §2 | +16 µs |
| Control-register / reference-enable / clear-code re-assertion | S4, D4 §12 | +16 µs amortised |
| Second ADC channel read (rail sense or reference, G3) | D4 §6, D3 §14 | +24 µs |
| Immediate pitch write on note change | ADR 0006 | +16 µs, occasional |
| ADC clocked at 1 MHz, not 2 MHz (G4) | C1 F10 | ADC transactions ~2× longer |

Running total ≈ **192–216 µs of 250 µs, 77–86 % duty**, before the per-key chatter
statistics, rise-time tracking, σ computation and gyro/accel comparison that D4 adds in
firmware. It closes — but only at 2 MHz, which is a **precondition** (A1 F4, B4 §5, B8 §5,
C5 F3: at 0.6 MHz six words alone take 320 µs and the loop does not close at all). Nothing
says so.

### N3. Which mod channel is the gate — hardware says 4, firmware says 1

**Fix α (D3 §20):** *"Assign **Mod 4** as the gate by convention… Reserve a footprint to cut
Mod 4's filter capacitor to 10 nF (16 kHz, 22 µs rise) if a destination ever needs a fast
edge."*

**Fix β (D5 §7):** *"**mod 1 = gate, mod 2 = retrigger** is a sensible shipping state, with
mods 3–4 free for IMU/colour, and the write-on strip on the panel reflecting it."*

**Why it matters.** α is a **hardware** provision on one specific channel — a footprint on a
board that is fabbed once. β is a firmware default and a panel silkscreen. If they disagree,
the one channel with a fast-edge option is not the one the gate is on, and the provision is
wasted on a board that cannot be revised.

**Combined correct version.** Take β's assignment (gate on mod 1, retrigger on mod 2 — the
musical argument is the stronger one, and the write-on strip makes it visible) and move α's
alternate-capacitor footprints to **mods 1 and 2**. Better: fit the alternate footprint on
**all four**, since it is a second pad on a capacitor that is being placed anyway.

### N4. The auto-zero's three gates

Three independently correct additions to the same decay rule:

- **W11 / D4 §3:** gate the decay on *"sub-threshold **AND quiet**"* — σ below 2× the
  commissioning at-rest noise — which removes the sustained-pianissimo failure.
- **D4 §3:** absolute and rate bounds (|zero − 149| > 330 counts = fault; > 28 counts/min
  after 30 min = leak or blockage) so the mechanism stops concealing the three faults the DP
  reference-port decision depends on detecting.
- **D5 §3:** a **dropout hold window** for circular breathing, with the auto-zero interlocked.

These compose, and the composition needs stating in one place because the three gates are
in three documents and the second **depends on the commissioning baseline** (D4 §1) which
does not exist yet and which must be written **before M8** or the numbers evaporate.

---

# Part 2 — The shared-budget audit

Every row is a resource with a fixed capacity that more than one proposal spends. Each
claimant's own document describes its claim as free.

| Resource | Capacity | Committed today | Claimed by proposals | Over? | Resolution |
|---|---|---|---|---|---|
| **OPA2197 halves, module** | 10 (`U-OPA-PITCH` qty 5) | 9–10 (B9 §0: zero spare once the gain pot is buffered) | **14–15**: pitch ×1–2, mod ×4, mod-offset buffer, ch6 zero inverter (B1), gain-pot wiper buffer (B9 §10 / D3 §6), breath gain, breath offset summer, pitch-offset buffer + inverter (D3 §2 / C2 F14), DAC-AVDD reference buffer (S5), presence comparator (D2 §19) | **Yes, by 4–5** | Resolve C1 in favour of **B9 §3's non-inverting pitch topology** (saves 2 halves) and D1 in favour of a **regulator not a reference** (saves 1). Use a dedicated comparator, not an op-amp half, for D2 §19 (saves 1). Lands at 11–12 → **buy 6 duals**, not 5 (D3) and not 7 (C1 F11); tie off the spare as a grounded follower (D3 §16) |
| **DAC8568 channels** | 8 | 7 (pitch, mod ×4, ch6 zero, ch7 offset) | 8 — B9 §3 considers ch8 for the pitch offset | Borderline | Reject ch8 for pitch (it parks at 0 V — see C1). Keep one spare, unpopulated, and **state it** |
| **MCP3202 channels** | 2 | 1 (CH0 breath) | **4 claims on CH1**, one of which (B1 §5 pseudo-differential) needs **both** | **Yes** | Rail sense → **GPIO4** (ADC1, per C5 F5); reference divider → CH1; B1 §5's ground problem → B6 §10's separate 3.3 V LDO. All three had, no channel double-spent |
| **Umbilical conductors** | 8 | 8 (all assigned) | **11**: two "spares" for paralleled power (B6 §12 — *premise false, there are none*), a MISO for DAC readback (D4 §6), a second DIG_GND (B8 §9) | **Yes, by 3** | B6 §12's premise is wrong and its fix must be withdrawn. D2 §6(b)'s "trade DIG_GND for MISO" is **not free**: B7 F2 shows `DIG_GND` carries **160–215 mA** as a parallel power return, so the trade doubles the `PWR_GND` drop and the common-mode voltage the in-amp must reject. **Accept no readback** (B10 §12, D4 §6), and spend the freed effort on module-side indicators |
| **Real-time board GPIO** | **17** broken out (C5 F4 — not the 16 ADR 0007 states) | 14 (ADR-stated) | 16 honest (C5 F5: +2 for display-board recovery), plus D2 §17's rail monitor, config-mode input and heartbeat LED | **1 spare against 3–4 further claims** | Rank them in ADR 0007 **before E13** (D2 §17). Recommended: GPIO4 = umbilical +12 V sense; GPIO3 = display `EN`. Push `IO0` and config-mode onto chain bits; heartbeat onto an AHCT125 spare gate |
| **Spare 74x165 chain bits** | 14 | 5–7 (markers + config mode) | **12–15** (see J2) | **Yes** | Allocate once, in `key-layout.yaml`, **before M3**. One marker bit per cluster board gives D2 §12's segment localisation free |
| **Loop time** | 250 µs | 136 µs booked (54 %) | **192–216 µs** (see N2) | Closes only at 2 MHz | **2 MHz is a precondition, not an option.** Fix it in ADR 0004, the conductor table and ROADMAP E11 before any refresh fix is counted as free |
| **SPI2 clock** | one host | DAC + ADC share it | DAC needs 2 MHz; MCP3202 ceiling is ~1.1 MHz at 3.3 V (C1 F10) | **Yes** | Per-device clock config, written into `firmware/README.md`. And the watchdog must retrigger from DAC `CS`, not `SCLK` (C5 F13) |
| **Module panel height** | 108.5 mm usable | **118.5 mm** already needed at 13 mm jack pitch (C3 §4) | +7 LEDs, +2 jumpers | **Already over before any addition** | 11 mm jack pitch; jumpers to the PCB; rail LEDs to the PCB edge; one or two multiplexed panel indicators; etherCON to the bottom |
| **Module panel width** | 30.18 mm | 2 × Alpha 9 mm pots | knobs ≤13 mm, and *"that excludes essentially every knob a Eurorack builder owns"* | **Yes** | Specify a 12 mm knob and the shaft type (6.35 mm round vs 18T knurled — the BOM says neither) |
| **Module board area** | 6HP, one board | — | Two boards required by the etherCON brace (W9, C3 §3); dual LED-driver footprints (C3 §11); +40 passives (D1) | **Yes** | Two-board module is forced. Decide it before the ground plan (B5 §3, B7 F4), which crosses the board-to-board joint |
| **Instrument bulk capacitance** | ≤1.5 mF wanted (C2 F7, for a startable limiter) | ~1.2 mF | **2.17–2.7 mF** if C2 F9 (+570 µF), C2 F23 (+660 µF) and 1000 µF strips are all taken | **Yes** | Keep one running total. K3's resolution lands at ~1.7 mF with a programmed ramp |
| **Module entry bulk** | — | 1.88 mF (4 × 470 µF) | +1000 µF (B5 §8) **and** −1.11 mF (C2 F10) | Contradictory | Per-branch: 1000 µF on the umbilical branch, 100 µF on the three quiet ones (K4) |
| **+12 V series drop** | 84 mV originally budgeted; the buck needs >8 V | ~0.6–1.15 V measured across proposals | Polyfuse 0.22–0.44 V, cable gauge ±0.30 V, L-BUCK-IN DCR 0.06–0.13 V, diode 0.35 V | Survivable, but 8–10× the stated budget | Delete the PPTC (−0.22 V), specify **24 AWG stranded** (B2 §9, B5 §9, B6 §12, B7 F11, B8 §10, B10 §19 — six documents, one line), specify DCR ≤0.15 Ω |
| **Instrument interior dissipation** | ~6 W for 17 K (B6 §9's proposed total-budget restatement) | 4.6 W typical | 6.9 W clamp-legal; **12 W at a 1.0 A limiter ceiling**; 29 K with hands on the plate | **Yes** | E2's split: limiter = fault protection at 1.2 A; thermal bound = the firmware clamp in **rail current**, closed on the IMU die temperature |
| **3.3 V rail, real-time board LDO** | ≥500 mA | ~5 mA (B6 §0.1) | +12–21 mA of key pull-ups at 2.2 kΩ (J1) | No | Fine, but update the number — it is 3–4× today's assumption |
| **`F-POLY` footprint** | 1 pad | PPTC | 3 claimants (E1) | **Yes** | Delete the PPTC, fit D1 §2's SS34 shunt |
| **`R-OUT-PROT`** | 1 resistor ×6 | protection | + filter R + clamp isolation + sacrificial fault element (H1, H2) | Over-loaded but reconcilable | 1206, clamps inboard, open-circuit is the designed failure |
| **74AHCT125 gates** | 4 per package | 3 SPI lines | OE inversion needs an **inverter**, and *"the two spare gates in the SOIC-14 are buffers, not inverters"* (B10 §4); D2 §20 wants a spare gate for the heartbeat | Tight | One NPN/N-FET for the OE inversion; one spare gate free for the heartbeat |

---

# Part 3 — Ordering

## Tier 0 — Measurements that must exist before the fixes they gate

None of these is a fix. Each is a number that decides between fixes that are currently both
on the table, and in every case applying the fix first forecloses the measurement.

| Measurement | Milestone | Gates |
|---|---|---|
| **Does the Waveshare board's header `5V` pin connect to raw VBUS?** | E1 | K1 (the OR element) — and it is the "highest bench-damage risk in the project" |
| **Is the USB ESD array fitted on the dev board?** | E1 | D1 §17 (a $5 panel-mount breakout vs nothing) |
| **SY6970 PMU stable on 5 V with no battery?** | E1 | C1 F15 / C5 F11 — a board swap is a firmware retarget, but only before M7 |
| **Real-time board idle and WiFi-active current** | E1 | K2 (one buck or two), E2 (the limiter setting), the whole lighting budget |
| **Umbilical current at the clamp-legal worst case, with a probe** | E6 | **E2 — the limiter setting. ADR 0004 already says nothing downstream may be sized from the estimate, and the BOM sizes it anyway** |
| **DAC saturation vs AVDD — look for a knee, not a slope** (B4 §12) | E7 | D1 (whether the 5.000 V REF5050 option has real headroom) |
| **Tube resonance, swept, with the trap volume varied** (B1 §3) | E2 | W7's restrictor decision, the bore specification, and the E2 row's own wording |
| **Author's own playing pressure, with a U-tube** (B1 §10) | E2 | 6 kPa vs 10 kPa sensor range — and the part has to be bought **before M8** |
| **Key-chain error counter, bussed common vs per-cluster** (B7 F7) | E4 | The switch-common return rule, unrecoverable after M6 |
| **SCLK edge at the module end, at full cable length, at 2 MHz** | E11 | F1's termination values |
| **Pitch jack, DC-coupled, while sweeping the LED animation, referenced to the VCO's ground** (B7 F1) | E6, repeated E9 | W4 — the most-converged finding in the review, and **the measurement the plan does not contain** |

**Rule:** the limiter's `R_ILIM`, the sensor range, the restrictor size and the DAC rail are
the four places where a fix is currently being written down ahead of the measurement that
decides it. All four are in ADR 0004's own words *"sized from measurement rather than from a
guess"* and all four currently have a guess in the BOM.

## Tier 1 — Blocking decisions, in dependency order

Each of these has three or more fixes downstream of it. Nothing below them can be finalised
first.

1. **The 12 V current limiter part and its latch behaviour** (E4). Blocks: the module PCB
   (it is the largest part on the entry), D1 §2's shunt diode (which requires latch-off),
   B10 §17's hot-plug behaviour, D1 §13's `FAULT` LED, and four decisions across ADRs 0004,
   0005 and 0014.
2. **The DAC's supply rail** (D1). Blocks: the pitch gain (Cluster C), the mod range
   (B4 §9), the level shifter's rail (D2), the supervisor threshold (D1 §7), and every cents
   figure in ADR 0006.
3. **The SPI clock at 2 MHz**, propagated into ADR 0004's conductor table, ADR 0004's
   bandwidth table and ROADMAP E11. Blocks: every refresh fix in N2, and E11 currently
   validates a bus speed the instrument cannot use.
4. **The breath receiver's input network as one block** (A1+A2+A3+A4+A5, decided together,
   not as five findings). Blocks: `R_G`, the band-limit capacitor, D2 §19's presence
   comparator, and the CMRR the whole architecture rests on.
5. **The pitch offset reference and the trimmer's home** (C1+C2, decided together). Blocks:
   the LT5400 question, the trim range, ADR 0006's power-on table, and the op-amp count.
6. **ADR 0013's zone table** — the register's own first block. Five agents flagged it; four
   further findings reference it for geometry that gets bonded shut.
7. **One board or two at the module** (W9, C3 §3). Blocks: the panel layout, the ground plan
   (B5 §3, B7 F4), and the etherCON family choice (both ends must be chosen together —
   NE8FDX-P6 does not mate with NE8MC6-MO).

## Tier 2 — Apply as a set, never individually

Each set is internally coherent and individually dangerous.

**Set A — Breath input network.** A1 (2 × 499 kΩ bias pair) + A2 (delete the 100 kΩ) +
A3 (1 kΩ instrument / 10 kΩ 0.1 % module, both legs) + A4 (`R_G` = 42.2 kΩ) + A5 (one
differential pole ahead of the in-amp). *Applying any subset changes the gain without
changing `R_G`.*

**Set B — Breath zero and mute.** B1 (inverting REF stage, −0.25, ch6 only) + B2 (RC ahead
of it) + the no-series-impedance rule + B3 (mute at the output node) + B4 (comparator moved
to `+IN`) + S4's stateless refresh. *B1 alone leaves the channel un-muted on watchdog; B3
alone mutes to the offset knob's value.*

**Set C — Mod channel integrity.** B4 §2's software LDAC + S4's every-pass ch7 refresh +
D4 §12's re-assertion of the reference enable and clear-code register. **Explicitly excludes
B10 §9's RC on ch7** (N1). *LDAC without the refresh leaves S4's stuck-at-rail; the refresh
without LDAC gives a 5.5–9.3 V spike on every recovery.*

**Set D — Umbilical SPI.** 68 Ω at the driving end + 220 Ω at the module input + 470 Ω–1 kΩ
between buffer and DAC + reduced GPIO drive strength + the 2 MHz clock. *Any two of the
three resistor positions without the third leaves one of the three jobs undone.*

**Set E — Power entry.** Delete `F-POLY` + SS34 shunt in its footprint + LT1641-2 latch-off
limiter at 1.2 A with a programmed ramp + firmware clamp in rail current + IMU die
temperature + 1 A per-strip fuses. *The shunt without a latching limiter pulses; the raised
limit without the branch fuses and the thermal clamp is B10 §22's 14 W in one LED.*

**Set F — Watchdog.** CLR pull asserted + MCP131 supervisor + `CS`-edge retrigger from the
buffered side + DAC-side idle pulls + 220 kΩ/1 µF film timing + disable jumper + panel
indicator. *I1's polarity alone decides whether B3's mute works.*

**Set G — Key inputs.** 2.2 kΩ + 47 nF + 100 Ω per input + the spare-bit allocation + the
switch-common return rule (B7 F7) + `74HC` vs `74LVC` decided with the termination value
(C2 F12: 33 Ω is correct only at a GPIO drive strength nobody has specified).

**Set H — Output stage.** Clamps inboard + 1206 + the filter values of H2 + `R-OPAMP-IN` at
qty 7 with D3 §17's 9 kΩ + 1 kΩ split.

## Tier 3 — Safe to apply independently, now

Documentation-only or genuinely isolated. These are where the round should start, because
they cost nothing and reduce the surface for everything above.

- `C-AA-ADC` → **47 nF C0G 1206** and add the 282 µs row to `latency-budget.md` (G1).
- Delete the INA134 paragraph from ADR 0004 (A1 §3, B1 §12, B2 §3, B8 §11, A2 §9, A3 F36 —
  **six documents, one paragraph**).
- Delete the README's second `## Licensing` section; set the ADR index rows to Accepted
  (A1 §9, A2 §1–2).
- Delete the README's *"purely digital and carries no analog signal path"* sentence — the
  exact wording two ADRs were edited to kill, which *"let a review finding through
  unchallenged"* (A1 §11).
- Fix ADR 0007's pin list: **17 broken out, not 16**, and the octal-PSRAM case is 17 → 12
  (C5 F4).
- Strike *"(or A grade)"* from `U-DAC`; specify the orderable C-grade part number with the
  reason (B4 §3, C1 F4, A3 F30).
- Correct `U-BREATH`'s package field to **8-SOP surface mount**, and record that the
  wear-part plan therefore needs a mezzanine PCB with a 0.1" header (C1 F13).
- Specify **24 AWG stranded pure copper** in `CABLE-UMB`, with the 30-second loop-resistance
  acceptance check (six documents).
- Correct the **330 kHz** buck frequency in ADR 0003 and the BOM (B5 §7, B6 §8).
- Correct `U-REG-DAC`'s 135 mW to 34 mW; move the 74HC-vs-LVC note off the keycap row
  (register, A2 §22, A3 F29).
- Specify **105 °C, ≥2000 h, 25 V low-ESR** for every electrolytic in the body (B6 §9,
  C2 F8). It is the only wear-out part class in a body that cannot be reopened.
- Enable TWDT and IWDT on the real-time board, fed **only from the 4 kHz output loop**
  (B10 §21, D1 §14) — the software watchdog is what makes the hardware watchdog sufficient.
- Record *"do not optimise the output loop to write-on-change"* as a non-negotiable
  architecture constraint with its reason (B10 §9, D4 §12, register).
- Reset-reason counters and a boot banner (D4 §15) — the cheapest detector in the review.
- Tie-off rules for unused op-amp halves, AHCT gates, the 74HC123 half and `LDAC`
  (D3 §16) — zero cost, and a floating op-amp input on ±12 V in the same package as the
  pitch amplifier is not a theoretical concern.
- `NOT ETHERNET` engraving at both ends and on the cable (D1 §19).

## Tier 4 — Must not be applied until a measurement exists

| Fix | Blocked on |
|---|---|
| `R_ILIM` / the limiter setting | E6 current probe at the clamp-legal worst case |
| The REF5050-as-AVDD option | E7 DAC saturation knee |
| Restrictor size and tube bore | E2 swept resonance, with the trap volume varied |
| MPXV4006DP vs MPXV5010DP | E2 manometer measurement of the author's own playing pressure — **and the part must be bought before M8** |
| One buck or two | E1 measured board currents with WiFi active |
| 68 Ω vs a slower edge on SCLK | E11 scope at the module end at 2 MHz |
| Note-gate hysteresis size | E4 measured LED-induced ADC step |
| Every "it got worse" detector in D4 | **D4 §1's commissioning fingerprint, written before M8** — eleven detectors lose their reference permanently if M8 runs without it |

---

# Part 4 — Fixes that compose *well*, recorded so they are not separated

Three cases where independently-proposed fixes reinforce each other and no document notices:

1. **The diode upgrade partly fixes W4's 20-cent breath-correlated pitch error.** The
   register's W4 names *"a shared 1N5817: the module's analog rail and the umbilical feed are
   on the same diode, so instrument current modulates V_f by ~80 mV"* — and offers no fix
   except a firmware animation change. C1 F19, C2 F19 and D1 §16 independently upgrade
   `D-REVPOL` to a 1N5822/SS34 for **unrelated** reasons (reverse voltage, current rating). A
   3 A part at 0.5 A has substantially lower dynamic resistance, which attacks W4's second
   mechanism directly. **Take the upgrade and re-measure W4 at E6 before spending anything
   else on it.** B5 §8's entry bulk on that node helps again.

2. **Constant-total-current lighting serves three findings at once.** W4/B7 F1's *"drive the
   animation as a moving dot or bar on a constant-total-current field"* removes the
   breath-correlation from the rail (W4), from the rack's shared ground (B7 F1), and from
   the ADC's reference depression (B8 §4, ADR 0014's chatter loop) — **and it is compatible
   with D5 §13's proposal that the strips display breath against its ceiling**, because a bar
   position on a fixed-total field is exactly that display. One firmware line, four findings.

3. **The OE gating's undocumented second job.** B5 §6 discovers that gating the level
   shifter from umbilical +12 V presence is also what makes power-down sequencing safe for
   the three SPI lines (6 ms of umbilical decay against 40 ms of DAC rail). Write it down as
   load-bearing — D2 §11's bench link and C3's panel rework both touch it, and a future
   revision that moves the gating for a good-looking reason reintroduces the hazard silently.

---

# Part 5 — What I could not resolve

Stated so they are decisions rather than gaps.

- **Pitch filter, 10 nF vs 33 nF** (H2). Both are musically defensible; they differ 30× in
  the latency-budget line. Needs the author's call on whether a 307 µs settle on a
  nine-octave leap is acceptable, which is a taste question, not an arithmetic one.
- **How many 500 Hz poles the breath channel should have** (A5). I have taken one, at the
  module, on D3 §5's and B8 §7's rectification argument. If E11 shows the instrument end
  needs its own pole for cable emission, the 318 µs comes back and the latency budget needs
  it.
- **Whether the module-end SPI series resistance should be 220 Ω or 1 kΩ** (F1, L2). 1 kΩ
  removes L2's continuous-clamp-duty requirement; 220 Ω is what two documents propose. The
  deciding number is the ESD array's DC handling, which is a datasheet lookup on a part that
  has to be re-sourced anyway.
- **The two-board module's ground joint** (M1). B5 §3 and B7 F4 both require the umbilical
  return to reach the bus header as a dedicated pour under 5 mΩ. With two boards there is a
  connector in that path. Nobody has costed it.
- **Whether `AGND` should have a clamp at all.** D3 §12 wants BAV99 on it; B7 F10 shows
  `AGND` is the one conductor with no low-impedance return at the module end, so a clamp
  there has nowhere to dump. I believe D3 is right (the clamp goes to the module's rails,
  not to `AGND`) but the two documents describe the node differently enough that the
  schematic should be drawn before this is settled.
