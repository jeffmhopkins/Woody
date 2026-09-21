# C1 — Breath receive stage, cold review

**Reviewer:** C1, cold pass. **Date:** 2026-09-21.
**Scope:** `hardware/module/breath-receive-stage.md` line by line, then
`docs/decisions/0003-breath-sensing-path.md`, the breath parts of
`docs/decisions/0006-cv-channel-allocation.md`, and the breath rows of
`hardware/bom.csv`. Cross-checks into `hardware/module/pitch-stage.md` and
`hardware/module/digital-and-supervision.md` where the breath stage borrows a
node from them.

**Independence:** `docs/review/` and `docs/research/` were not opened. Nothing
below was informed by an earlier reviewer's conclusions.

**Evidence markers** are on every claim: `[repo]` with the file named, `[calc]`
with the arithmetic shown, `[datasheet]`, `[from memory]`, `[gated]` where a
conclusion needs a number I could not fetch (every vendor domain was blocked).
No datasheet figure has been invented. Where I needed one, the part and the
parameter are named and the conclusion is marked as depending on it.

---

## Severity-ranked findings

Rank weights **retrofittability**: an error on the instrument carrier is behind
a bonded body; an error on the module is behind four screws.

| # | Severity | Where | Retrofit | Finding |
|---|---|---|---|---|
| **1** | **Showstopper** | Module (drawing) | Free now, silent later | **The ASCII schematic wires the in-amp inputs backwards from every line of text on the same page.** `R2`→`IN−` comes from `AGND`; `R3`→`IN+` comes from `BREATH`. The prose, the stated transfer function, and `bom.csv` all say BREATH on `IN−`. Built as drawn, breath CV goes *negative* and the trimmer pushes the zero the wrong way. |
| **2** | **High** | **Instrument** | **UNRETROFITTABLE after bonding** | `R-SER-BREATH-INST` (R1, 1 kΩ, **0805**) dissipates **139 mW** in the sustained +12 V fault ADR 0003 names as the design case. 0805 is 125 mW by this BOM's own reckoning. The same argument is already made in full for `R-OUT-PROT` and was not carried across. |
| **3** | **High** | Module | Yes | **CMRR does not close.** The resistive term alone is **60.2 dB** — the entire budget — because R1 (1 kΩ) is on the signal leg and nothing matches it on the return leg. C_cm mismatch at commonly stocked ±5 % C0G adds a **46 dB** asymptote. Combined worst case ≈ **44 dB** against a 60 dB requirement. |
| **4** | **High** | Module | Yes | **`TRIM-BREATH-ZERO` is referenced to `VREFOUT`, which is the DAC8568's internal reference — disabled by default at power-on and clearable by a mis-framed SPI word.** Today's trimmer puts the "analog end to end, firmware cannot touch it" path back under DAC firmware state. The breath jack is **not 0 V at power-on**; it is +0.26…+1.08 V. |
| **5** | **High** | Module | Yes | **The downstream stage cannot do independent gain and offset in one op-amp half.** With an inverting summer, *any* offset injected at the virtual ground is multiplied by the gain setting. The WX5 interaction the REF trimmer was introduced to kill is reproduced exactly, displaced from the pedestal onto the OFFSET knob. |
| **6** | **Med-High** | Module | Yes | **`TRIM-BREATH-ZERO`'s specified range (0…+0.6 V) is 36 % too small.** A sensor at the top of the offset spec *this page prints* (0.378 V) needs **+0.817 V** of REF. Such a unit cannot be nulled. |
| **7** | **Medium** | Module | Yes | **Nothing mutes breath, and the BREATH conductor is undefined while the umbilical +12 V ramps.** The 330 nF RC (τ = 330 µs) cannot hide a multi-millisecond hot-swap ramp. Credible full-scale breath spike into a VCA at every power-on. The part that could gate it (`U-PRESENCE`) is already in the BOM and is used only for SPI `OE`. |
| **8** | **Medium** | Module | Yes | **The presence comparator's 1 MΩ hysteresis resistor injects 54 mV of DC straight into the in-amp's signal node** — 27 % of the whole sensor pedestal, 118 mV at the in-amp output, up to 292 mV at the jack, and state-dependent. |
| **9** | **Medium** | Docs | Yes | **The unplugged and power-on states are stated wrongly in three places.** Unplugged, the in-amp rests at **+V_REF = +0.437 V**, not 0 V. ADR 0006's power-on table still credits the deleted 100 kΩ differential pulldown. |
| **10** | **Medium** | Docs/BOM | Yes | **`bom.csv` row 28 (`U-DIFFRX`) still describes the pre-trimmer circuit** — "REF ties HARD to module AGND", "−0.44 V at rest". It is the build document, it contradicts the page, and it contradicts rows 99/100/108 of the same file. |
| **11** | **Low-Med** | Module | Yes | **330 nF film in 1206 is almost certainly not a buyable part**, by the identical argument `bom.csv` already makes against 82 nF C0G in 0805. 15 nF C0G in 0805 is marginal and was not flagged. And the better topology — a feedback lead cap — is the one pitch already converged on in ADR 0006. |
| **12** | **Low** | Module | Yes | **An open `AGND` conductor is silent and undetected** and reinstates the full shared-ground offset (up to 320 mV of LED-correlated error at the jack). An open `BREATH` conductor *is* detected. |
| **13** | **Low** | Docs | Yes | **Numbers on the page that do not survive re-derivation:** the 531 Hz pole is 481 Hz; the filter's latency contribution is 661 µs against 160 µs budgeted; "−9.6 V at full" and "9.94 V span" are the same node; the sensor span is 4.5 V or 4.6 V depending on which document you read, which moves the "0.6 % shortfall" to 0.6–2.8 %; the thermal drift figure omits the downstream gain. |

---

## 1. The drawing wires the in-amp inputs backwards *(Showstopper)*

**This is the single decision the page spends its longest section defending, and
the drawing does the opposite of the text.**

Column positions in the ASCII art, measured rather than eyeballed `[repo,
hardware/module/breath-receive-stage.md, lines 22–49]`:

| Element | Column |
|---|---|
| `BREATH (pin 1)` vertical | **70** |
| `AGND (pin 2)` vertical | **68** |
| `R2 10k` right terminal `┘` | **68** → ties to **AGND** |
| `R2 10k` left terminal `┌` | **36** |
| `R3 10k` right terminal `┘` | **70** → ties to **BREATH** |
| `R3 10k` left terminal `┌` | **44** |
| `IN−` label and its `▼` | **36** |
| `IN+` label and its `▼` | **44** |

So the drawing is **`AGND → R2 → IN−`** and **`BREATH → R3 → IN+`**.

Every other statement in the repository says the opposite:

- Same page, line 77: *"The first fix was to swap the inputs. With BREATH on
  `IN−`…"* `[repo]`
- Same page, line 56: `Vout = −2.185·(V_BREATH − V_AGND) + V_REF` — the minus
  sign is only obtainable with BREATH on `IN−` `[repo]`
- Same page, line 85: *"+0.437 V … nulls the sensor's +0.200 V pedestal"* — a
  **positive** REF only subtracts if BREATH is on `IN−` `[repo]`
- `bom.csv` row 28, `U-DIFFRX`: *"BREATH drives IN−, AGND drives IN+"* `[repo]`

**What gets built if the drawing is followed** `[calc]`: `Vout = +2.161·V_BREATH
+ V_REF`. At rest that is `2.161 × 0.198 + 0.437 = +0.865 V`, not 0 V. The
trimmer can only push it further up — the trimmer's authority is now in the
wrong direction, which is the *original showstopper this page was written to
close*, reinstated by the drawing. Downstream the inverting stage then delivers
**−0.5…−2.2 V at rest and −10 V at full breath**: breath CV that goes *down*
when you blow.

This is not a cosmetic slip. The page's own framing is that *"the ADR names the
parts and none of the topology"* and that *"two expert reviewers built two
different schematics from the same ADR prose"* `[repo]`. The drawing exists
precisely to stop that, and on the one decision it was written to fix, the
drawing and the prose disagree. A builder working from the picture — which is
what a picture is for — builds the wrong circuit, and the error is invisible
until a meter goes on the jack.

**Fix:** swap the `R2`/`R3` terminations in the art. Free today.

---

## 2. R1's power rating in the fault the ADR designed around *(High, instrument-side, unretrofittable)*

ADR 0003 names a **sustained +12 V fault on the BREATH conductor** as the design
case, and resolves it by moving the buffer to +12 V `[repo,
docs/decisions/0003-breath-sensing-path.md]`:

> *"With the buffer on +12 V there is no conflict, because there is no fault
> current. … the worst case is the op-amp sinking a few milliamps within its
> linear output range."*

**That conclusion is correct about the op-amp and was never checked for the
resistor.**

`[calc]` Buffer holding its rest output of 0.2 V; the conductor pinned at
+12 V by a short to the umbilical's power conductor:

```
I  = (12 − 0.2) / 1 kΩ                = 11.8 mA
P(R1) = I² · R = (11.8e-3)² × 1000    = 139.2 mW
P(op-amp) = 11.8 mA × 0.2 V           = 2.4 mW      (negligible — ADR is right)
```

`bom.csv` row 66 specifies `R-SER-BREATH-INST` as **1 kΩ 1 % metal film,
0805** `[repo]`. `bom.csv` row 42 states this project's own figure for an
0805: **"~125mW for an 0805 — no margin"**, and on that basis specifies
`R-OUT-PROT` as **1206 at 250 mW** with the heading **"POWER RATING IS NOT
OPTIONAL and this row had none."** `[repo]`

So: **139 mW into a 125 mW part, continuously, in the fault case the ADR
explicitly designs for** — 111 % of rating. The identical argument was made
correctly one row away, for a part on the *module*, and was not carried to the
part on the *instrument carrier*, which is the one inside a bonded body.

`[gated]` The 125 mW figure for 0805 is the BOM's own; standard thick-film 0805
is 100–125 mW depending on vendor, so the overload is 111–139 %. Either way it
is outside rating.

**Two further consequences nobody has written down:**

- **If R1 cooks open, the instrument goes completely dead, not just breath.**
  `U-PRESENCE` senses the BREATH node; with R1 open the node falls to 0 V,
  presence de-asserts, `74AHCT125` `OE` goes high, and the SPI link to the DAC
  is disabled `[repo, hardware/module/digital-and-supervision.md; bom.csv rows
  35, 99]`. Pitch and all four mod channels die with it.
- **During the fault the breath jack sits at the positive rail and stays
  there.** `[calc]` BREATH at 11.88 V at the in-amp node → in-amp output
  `−2.161 × 11.88 + 0.437 = −25.3 V` → clips at the negative rail → inverting
  downstream → jack clips at **≈ +11.4 V**. A VCA wide open, indefinitely, while
  the instrument looks dead. The presence comparator reads the node at 11.88 V,
  well above its +100 mV threshold, and reports **"present"** `[repo, bom.csv
  row 100]`. Nothing in the design detects this.

**Fix:** `R-SER-BREATH-INST` → **1206, ≥ 250 mW**, identical to `R-OUT-PROT`.
Cost zero. **This must land before the body is bonded.** It is the only finding
here that is not repairable with four screws.

---

## 3. CMRR: every term, and it does not close *(High)*

The requirement is 60 dB `[repo, docs/decisions/0003-breath-sensing-path.md]`,
derived from a shared-ground offset that reaches 58.9 mV at 350 mA.

I enumerated four terms. **Two of them each consume the entire budget on their
own.**

### 3a. The bias pair converts source-impedance imbalance back into a differential error

The design's stated reason for relaxing source-impedance matching is
`bom.csv` row 62 `[repo]`:

> *"Matched. Gigaohm in-amp inputs make source impedance irrelevant to CMRR, so
> 10k is free."*

**That is true for a bare in-amp and false once R4/R5 are added.** The 1 MΩ
bias pair is a resistive divider on each leg, and an unmatched series resistance
divides the two legs unequally. A common-mode voltage therefore appears at the
in-amp as a differential one — the exact mechanism ADR 0003 believed it had
deleted by choosing a buffered in-amp over a difference amp.

`[calc]` Leg attenuations, using the page's own values `[repo]` — signal leg
`R1 + R3 = 1 kΩ + 10 kΩ = 11 kΩ`, return leg `R2 = 10 kΩ` (there is no R1 on the
return leg; the instrument's analog star is a ~0 Ω source):

```
a_signal = 1M / (1M + 11k) = 0.98911968
a_return = 1M / (1M + 10k) = 0.99009901
Δa       =                   0.00097933
CMRR     = 20·log10(1/Δa)  = 60.18 dB
```

**60.2 dB against a 60 dB requirement, from this term alone, with every other
term still to come.** And R4/R5 are specified at **1 %** `[repo, bom.csv row
61]`, which makes it worse:

```
worst case 1% skew: |11k/0.99M − 10k/1.01M| = 0.0011851  →  58.5 dB
```

Note what this does to the 0.1 % thin films: `R2`/`R3` at ±0.1 % of 10 kΩ is
±10 Ω, giving `Δa ≈ 2.0e-5 → 94 dB` `[calc]`. **The design pays for 0.1 %
matched resistors on the module and then destroys the match fifty-fold with an
unmatched 1 kΩ at the far end of the cable.** The page's own wording conceals
it: *"Loss in the 2 × 1 MΩ bias pair against 2 × 11 kΩ series"* `[repo]` — there
is no 11 kΩ on the return leg, only 10 kΩ, and the 1 kΩ difference the phrase
glosses over is the whole defect. (The *number* 0.9891 is nonetheless right, for
a different reason — see finding 13d.)

**Fix — module-side, one resistor:** make the **return** leg 11 kΩ (`R2` → 11 kΩ,
or 10 kΩ + 1 kΩ in series), so both legs present 11 kΩ. `Δa` then collapses to the
0.1 % tolerances, ≈ 94 dB `[calc]`. **The differential signal gain is unchanged**,
because the return leg carries no signal — so this costs nothing in the gain
budget and needs no re-derivation. Raising R4/R5 to 10 MΩ also works arithmetically
(80 dB) but trades against in-amp bias-current offset — see 3e.

### 3b. C_cm mismatch — 46 dB at the tolerance most likely to be stocked

The page claims the 10:1 ratio makes C_cm mismatch benign: *"a mismatch between
the two common-mode capacitors is divided by the ratio before it reaches the
difference signal"* `[repo]`. **It is divided by the ratio; the ratio is not
large enough, and the tolerance is unspecified anywhere.**

`[calc]` Nodal solution of the actual network (Rs per leg, C_cm to ground each,
C_diff across), first order in the mismatch δ = C1 − C2:

```
Vd/Vcm = jω·δ·Rs / (1 + jω·Rs·(C_cm + 2·C_diff))
high-frequency asymptote → δ / (C_cm + 2·C_diff)
```

Sanity check of the model against the repository's own published figure: for a
*single-ended* 15 nF on one leg, the model gives **20.1 dB at 100 Hz**, against
ADR 0003's "caps CMRR near 19 dB" and the page's "about 15 dB at 100 Hz"
`[calc]` vs `[repo]`. The model reproduces their number, so the numbers below
are on the same footing.

With C_cm = 1.5 nF, C_diff = 15 nF, Rs = 10.5 kΩ `[repo]`:

| C_cm tolerance | δ (worst) | 100 Hz | 500 Hz | HF asymptote |
|---|---|---|---|---|
| ±5 % (J, common stock) | 150 pF | 60.3 dB | 49.3 dB | **46.4 dB** |
| ±2 % (G) | 60 pF | 68.2 dB | 57.3 dB | 54.4 dB |
| **±1 % (F)** | 30 pF | 74.3 dB | 63.3 dB | **60.4 dB** |

`[repo, bom.csv row 63]` specifies `15nF C0G (diff) + 1.5nF C0G (cm x2)` with
**no tolerance at all**. At the tolerance a distributor will ship by default,
the capacitor term alone is 46 dB.

**Fix:** specify the C_cm pair at **±1 % (F)**, and say so in the BOM. Even then
the asymptote is 60.4 dB — *at* budget, no margin. If margin is wanted, raise
C_diff to 22 nF (asymptote 63.6 dB `[calc]`) and accept the corner moving to
~340 Hz, or hand-match the pair from one reel with a meter, which on a one-off
costs ten minutes.

### 3c. The REF pin's source impedance — this part is sound

The page's argument is correct and I want to say so plainly: source impedance at
an in-amp's `REF` pin adds directly to its internal difference-amp network and
degrades CMRR roughly one-for-one `[from memory — standard in-amp behaviour;
the specific internal network value for INA828 is gated on the TI datasheet,
ti.com blocked]`. Buffering the trimmer with an op-amp follower reduces the
source impedance to milliohms at DC, which makes this term negligible. **The
buffer is correctly specified and correctly justified.**

### 3d. The in-amp's own CMRR

`[gated]` INA828 CMRR at G ≈ 2. Precision in-amps are weakest at low gain and
this stage runs at 2.185. If it is ≥ 90 dB at G = 2 the term is irrelevant next
to 3a and 3b; if it is nearer 80 dB it still is. Named for completeness. The
budget is consumed by the passives, not the chip.

### 3e. Bias current through the 1 MΩ pair — an unmentioned DC term

`[gated]` INA828 input offset current `I_OS` and its drift. `I_OS × 1 MΩ` is a
*differential* error added ahead of the gain. At `I_OS` = 1 nA that is 1 mV,
2.2 mV at the in-amp output, up to 5.4 mV at the jack. Commissioning trims the
DC out; the **drift** is not trimmed. The page never mentions this term, and it
is the reason "just raise R4/R5 to 10 MΩ" is not a free fix for 3a. Fix 3a with
the series resistor instead.

### CMRR summary

`[calc]` Worst case, as currently specified (1 % bias resistors, 5 % C0G, at
500 Hz): `0.001185 + 0.003431 = 0.004616 → **46.7 dB**`. With the R1 match added
and 1 % C_cm: **≈ 63 dB at 500 Hz, 60.4 dB asymptotic.**

**Honest statement of consequence:** at 46 dB, a 58.9 mV common-mode offset
lands as ~0.29 mV at the in-amp input, ~0.6 mV at the jack at max gain `[calc]`
— about −84 dB of LED-correlated gain modulation on a breath CV. Almost
certainly inaudible. **The reason this is still a High finding is not the
audible consequence; it is that the design believes it has 60 dB and has used
that belief to delete matching requirements elsewhere** (`bom.csv` row 62,
quoted above). Both fixes cost one line each.

---

## 4. The REF trimmer puts breath back under DAC firmware state *(High)*

**This is the finding I would most want caught, because the change is one day
old and it quietly undoes the property the whole channel is built around.**

`bom.csv` row 108 `[repo]`: *"Range 0 to ~+0.6V **from VREFOUT**"*.

`VREFOUT` is not a generic node. `hardware/module/pitch-stage.md` establishes it
as **the DAC8568's own internal reference output**, 2.500 V, and builds the
pitch stage's entire error argument on the fact that the DAC's full scale is
`2 × VREFOUT` `[repo, hardware/module/pitch-stage.md, lines 14, 99–106]`.

And the repository states twice, emphatically, that **this reference is disabled
by default**:

- `docs/decisions/0006-cv-channel-allocation.md`: *"the internal reference is
  disabled by default and needs an explicit enable write at boot. … the outputs
  sit at 0 V from rack power-on until firmware enables the reference"* `[repo]`
- `hardware/module/digital-and-supervision.md`: *"a DAC8568 frame carries the
  software reset, the clear-code register and the internal-reference enable — so
  a mis-framed word is a **sticky** failure that the 4 kHz refresh does not
  clear"* `[repo]`

**So `V_REF` at the in-amp is 0 V until firmware writes, and can be returned to
0 V mid-performance by one corrupted `CS` edge.**

`[calc]` With the instrument connected and at rest, `V_REF = 0`:

```
in-amp out = −2.161 × 0.198 V + 0 = −0.428 V
jack       = +0.428 × (0.6 … 2.5) = +0.26 V … +1.07 V   (plus the OFFSET knob)
```

ADR 0006's power-on table promises `| Breath | 0 V |` `[repo]`. It is up to
**+1.07 V** — a VCA held partly open from rack power-on until firmware finishes
booting, on the channel the design describes as immune to digital state.

**Three claims in the repository become false as of today's change:**

1. `hardware/module/breath-receive-stage.md`: *"`CLR` reaches the DAC channels;
   breath touches none of them, and **now that `REF` is grounded** it touches
   the breath stage in no way at all"* `[repo]`. This sentence is a fossil of
   the previous revision — the same page, forty lines earlier, says `REF` is
   trimmed to +0.437 V. The author changed the circuit and did not revisit the
   section that depends on it. The narrow claim about `CLR` survives (`CLR`
   clears DAC *registers*, not the reference enable `[from memory; DAC8568
   register map gated — ti.com blocked]`); the broad claim does not.
2. `hardware/module/digital-and-supervision.md`: *"Breath never passes through
   the DAC and now that `REF` carries a trimmer rather than a DAC channel, `CLR`
   touches the breath stage in no way at all"* `[repo]` — same fossil, and the
   trimmer is precisely *why* it is no longer true in general.
3. ADR 0006's whole justification for deleting DAC channel 6: *"firmware still
   corrects only the representation it can measure"* `[repo]`. The channel is
   gone, but the **dependency** came back through the reference pin instead of
   the data pin. It is a weaker dependency — a fixed voltage rather than a
   servo — but it is the same coupling, entering by a door nobody was watching,
   which is exactly the failure mode the page's own paragraph on "a decision
   whose original justification has been removed survives by inertia" warns
   about.

**Fix — module-side, one part:** source `TRIM-BREATH-ZERO` from a **local shunt
or series reference off the protected +12 V** (LM4040-2.5, REF3025 or similar,
~30 ¢), not from `VREFOUT`. Breath then has no dependency on the DAC, its
reference, its registers, or firmware — which is what ADR 0003 claims the
channel is.

**Better still, if an instrument-side change is ever on the table:** the sensor's
pedestal is *exactly* 4 % of its own supply — `Vout = VS(0.1533·P + 0.04)`, so
`0.04 × 5.000 = 0.200 V` `[repo, ADR 0003; calc]`. A null derived from the
instrument's REF5050 would be **ratiometric to the thing it is nulling** and
immune to every drift term at once. Cat5 has spare pairs. This is not worth
reopening the body for on its own, but if anything else forces the carrier open
before bonding, it is the correct circuit.

**Minor, related, and *not* a defect:** hanging the breath trimmer's divider on
`VREFOUT` loads the node the pitch calibration references. Because the DAC's
full scale scales with the same node, a load-induced droop is a pure **gain**
error on pitch, which `pitch-stage.md`'s own argument shows is the benign kind
`[repo, calc]`. It does mean **pitch must be calibrated after the breath zero is
trimmed, not before** — a commissioning-order note, worth one line. `[gated]`
DAC8568 `VREFOUT` load regulation and drive capability would set the magnitude.
Note also that `pitch-stage.md` line 129 describes `V_ref` as *"Shared with
nothing else"* `[repo]`, which is now true only of the buffered node.

---

## 5. The downstream stage cannot do what the page claims in one op-amp half *(High)*

The page's argument for keeping BREATH on `IN−` rests entirely on the downstream
topology `[repo]`:

> *"an inverting summer does gain and offset with two pots into one virtual
> ground, where a non-inverting stage would have the offset injection interact
> with the gain setting"*

and the commissioning section promises `[repo]`:

> *"Because step 1 nulled the pedestal ahead of the gain pot, step 2 no longer
> disturbs this."*

**Work the algebra through the block the page declines to draw.**

**Topology A — gain in the feedback path** (the natural reading of "two pots
into one virtual ground", and the only use that suits the linear 50 kΩ pot
already in the BOM):

```
Vout = −(Rf/Ri)·Vi  −  (Rf/Ro)·Voff
```

At rest `Vi = 0` (the trimmer did its job), so `Vout|rest = −(Rf/Ro)·Voff`.
**`Rf` is the GAIN pot.** Turning GAIN changes the rest point. The player sets
the floor with OFFSET, turns GAIN, and the floor moves — *"so you may have to
repeat"*, which is the Yamaha WX5 sentence the page quotes **against** the
alternative it rejected `[repo]`. The interaction is not removed; it is
relocated from the pedestal onto the OFFSET knob.

This holds for every injection point in an inverting stage. Offset at the
non-inverting terminal gives `Vout = −(Rf/Ri)Vi + Voff(1 + Rf/Ri)` — worse. A
current source into the summing node gives `Vout = −I·Rf` — same scaling. **With
an inverting summer, any offset referred to the virtual ground is multiplied by
the gain, without exception.**

**Topology B — gain as an input attenuator ahead of a fixed-gain summer:**

```
Vout = −A·k·Vi − (Rf/Ro)·Voff       k ∈ [0,1]
Vout|rest = −(Rf/Ro)·Voff           independent of k   ✓
```

This is the only arrangement that delivers the page's promise. It has two
costs the page does not mention:

- **The wiper's source impedance warps the gain law.** `[calc]` With the BOM's
  `POT-BREATH` = **B50k linear** `[repo, bom.csv row 17]` into a 10 kΩ summing
  resistor: at mid-rotation the wiper impedance is `50k/4 = 12.5 kΩ`, so the
  realised gain is `k/(1 + 12.5/10) = 0.5/2.25 = 0.222` instead of 0.5 — **44 %
  of the dialled value**, and the error varies across rotation. Keeping this
  under 5 % needs `Ri ≥ 250 kΩ` (noise and bias-current offset) **or a buffered
  wiper**. The page lists "whether the gain pot's wiper needs a buffer" as open
  `[repo]`. It is not open: in the only topology that meets the page's own
  independence claim, **it is required.**
- **An attenuator only attenuates**, so the fixed gain must be 2.5× and the pot
  spans `k = 0.24 … 1.0` — the bottom quarter of the rotation is dead. `[calc]`
  `0.6/2.5 = 0.24`. Fixed with a **15.6 kΩ resistor from the pot's cold end to
  ground**, which gives `k_min = 15.6/(15.6+50) = 0.238` and restores full
  rotation `[calc]`.

**So the stage needs two op-amp halves, not one.** And **`bom.csv` already pays
for two** — row 13 enumerates *"breath gain, breath offset"* as separate halves
`[repo]`. The BOM is right and the schematic page is wrong, on the exact claim
the input-swap decision is argued from.

`[calc]` Half-count audit of row 13: it says *"Twelve halves, eleven used"* and
then lists **ten** — pitch, mod 1–4, mod offset buffer, breath gain, breath
offset, VREFOUT follower, breath REF-zero buffer. Six packages is twelve halves,
so there are **two** spares, not one. **The fix costs nothing; the halves are
already bought.**

**Is 0.6×–2.5× the right range?** `[calc]`, reconstructing the page's own
reasoning from `Vout = VS(0.1533·P + 0.04)` `[repo, ADR 0003]`:

| Blow | Sensor | In-amp out (×2.161) | Gain for 10 V |
|---|---|---|---|
| 2.5 kPa | 2.116 V | 4.14 V | 2.41× |
| 2.8 kPa | 2.346 V | 4.64 V | 2.16× |
| 6.0 kPa (FS) | 4.799 V | 9.94 V | 1.01× |

So the top of the range checks out — the page's "roughly 4.5 V at the in-amp"
and "about 0.6× to 2.5×" are both defensible. One consequence to record: at
2.5× a 2.8 kPa blow asks for 11.6 V, above the OPA2197's ~±11.45 V swing
`[repo, ADR 0006]`, so **above ~2.16× a hard blow clips at the rail rather than
at 10 V.** That is correct behaviour for a performance knob (set full scale at a
soft blow, let hard blows clip), but it should be stated rather than discovered.

---

## 6. The trimmer's range cannot null a sensor at the top of its own spec *(Med-High)*

The page prints the sensor's zero-pressure spec as **0.152–0.378 V** `[repo,
hardware/module/breath-receive-stage.md line 71]`. `bom.csv` row 108 specifies
the trimmer's range as **"0 to ~+0.6V from VREFOUT"** `[repo]`.

`[calc]` Required `V_REF` to null a pedestal, through the 0.98912 divider and
the in-amp's 2.18483:

```
pedestal 0.152 V → REF = 2.18483 × 0.98912 × 0.152 = 0.329 V
pedestal 0.200 V → REF =                            0.432 V
pedestal 0.378 V → REF =                            0.817 V   ← 36 % beyond range
```

**A sensor anywhere in the top third of its published offset tolerance cannot be
nulled.** The failure is quiet: the zero cannot be brought to 0 V at
commissioning, and the residual sits *ahead* of the gain pot, which is the exact
condition the trimmer exists to prevent — the circuit degrades into the grounded-
`REF` case it was built to escape.

Note also that the page's stated **+0.437 V** is computed against the *nominal*
gain 2.185 and not the *effective* 2.161 it derives four lines later; the correct
figure for a 0.200 V pedestal is **+0.432 V** `[calc]`. Immaterial in itself —
it is a trimmer — but it is the same "forgot the loading term" slip as
finding 13.

**Fix:** specify the range **0 to +1.0 V** (the divider around `TRIM-BREATH-ZERO`
is two resistors). A 25-turn 10 kΩ cermet over 1.0 V gives 40 mV/turn, ≈ 18 mV
at the sensor — ample resolution `[calc]`. Combine with the fix in finding 4
and set the range from the new local reference.

**And this part is genuinely well chosen, which is worth recording:** because the
MPXV4006**DP** measures across its own diaphragm with the reference chamber open
to the body cavity, **barometric pressure cancels** and the trimmer never has to
chase the weather `[repo, ADR 0003; from memory — differential-cell behaviour]`.
A gauge part would have made this trim a running calibration.

---

## 7. Power-on, power-off, unplug, and the +12 V fault

### Power-on — the BREATH conductor is undefined during the umbilical ramp *(Medium)*

Umbilical +12 V is **downstream of the module's own load switch** `[repo,
bom.csv row 35; LT1641 in row 43]`, so the module's ±12 V rails and the INA828
are alive **before** the instrument's buffer is.

During that ramp the instrument's OPA2197 is below its minimum supply and its
output is not defined by its input `[gated — OPA2197 minimum supply; 4.5 V
[from memory], and behaviour below it is not specified anywhere]`. The BREATH
conductor can therefore sit anywhere from 0 V up to the instantaneous rail while
the ramp passes through the region below the amplifier's minimum supply.

`[calc]` BREATH at 4.5 V → in-amp out `−2.161 × 4.5 + V_REF ≈ −9.3 V` →
inverting downstream → **jack at +10 V or the rail.** The output RC does not
help: `τ = 1 kΩ × 330 nF = 330 µs` against an LT1641 ramp of milliseconds to tens
of milliseconds `[calc]`. Compounded with finding 4 (`V_REF` = 0 during the same
window), the honest statement is: **the breath jack's power-on behaviour is
undefined and can be full scale for several milliseconds.**

**Nothing mutes breath.** `U-PRESENCE` (LM311) already senses exactly the
condition that distinguishes "instrument alive" from "anything else", and its
output drives only the SPI buffer's `OE` `[repo, hardware/module/
digital-and-supervision.md]`. **Fix:** take a second output from the same
comparator to a JFET or analog-switch shunt at the jack, or to an `OE`-gated
clamp on the in-amp output. One part, module-side, and the sensing circuit is
already bought and already positioned. This also cleans up the unplugged case
below.

### Unplugged mid-note — safe, but not for the reason given *(Medium)*

The page says `[repo]`:

> *"An analog path cannot latch at a level the player is not producing: it
> follows the sensor, and the sensor follows the room."*

**With the cable pulled, the path does not follow the sensor — there is no
sensor.** `[calc]` R4/R5 pull both inputs to module AGND, so `V_diff = 0` and:

```
in-amp out = 0 + V_REF = +0.437 V      (not 0 V)
jack moves by −(0.437 × 0.6 … 2.5) = −0.26 V … −1.09 V relative to rest
```

The **direction is safe** — a negative excursion closes a VCA, so a yanked cable
silences the note, which is the desired behaviour. But the jack does not go to
0 V, it goes *below* rest by up to 1.09 V, and if the OFFSET knob has been used
to set a positive floor the jack can end up at a negative voltage. Three places
state this wrongly:

- `hardware/module/digital-and-supervision.md` table: *"Cable unplugged → R4/R5
  pull both inputs to AGND → **0 V**"* `[repo]` — true before the trimmer, false
  now.
- ADR 0006's power-on table: *"Breath | 0 V | The receiver's differential
  pulldown holds it there (ADR 0003)"* `[repo]` — cites the **100 kΩ
  differential pulldown that this very page deleted** `[repo,
  breath-receive-stage.md, "What this settles"]`.
- The page's own E10 rationale, quoted above.

One more, low: unplugged, two 1 MΩ nodes sit on the ends of 2 m of open wire — a
good mains-hum antenna. Both legs pick up similar common mode and the CMRR terms
of finding 3 reject it, so this is probably a non-issue, but it is a reason to
prefer the mute in finding 7 over relying on the bias pair.

### Power-off — sound

`[calc]` The 330 nF discharges through 1 kΩ plus the op-amp's collapsing output
stage, `τ = 330 µs`. No thump mechanism. Rail-collapse skew between ±12 V can
produce a brief output excursion, as it can in every Eurorack module. Accepted.

### +12 V on the BREATH conductor — see finding 2

Covered above: 139 mW in R1, jack pinned at the positive rail, presence
comparator reports "present". `[gated]` INA828 maximum differential input
voltage and input protection, with 11.88 V across the inputs at G = 2.185 —
`R_G` current is `11.88/42.2k = 282 µA` `[calc]`, which is small, but survival
depends on the part's internal input clamp structure. The module-side BAV99
does **not** conduct in this case (the node is at the rail, not above it), which
is correct and intentional.

---

## 8. The presence comparator's hysteresis lands in the signal *(Medium)*

`bom.csv` row 100 `[repo]` places the LM311's input on the in-amp's own signal
node — *"sense the module end of BREATH against AGND through the existing 10 kΩ
protection resistors"* — and specifies *"**1M from output to IN+ for
hysteresis**, which is the value Expert Sleepers ships"*.

**Those two sentences are individually correct and jointly a defect: the
hysteresis current is injected into the node the INA828 is measuring.**

`[calc]` Node Thévenin impedance: `11 kΩ ∥ 1 MΩ = 10.88 kΩ`. Node voltage with
the instrument alive: `0.2 × 1M/1.011M = 0.1978 V`. Hysteresis injection when
the LM311's open collector releases to the 5.21 V pull-up `[repo, bom.csv row
101]`:

```
ΔV_node = (5.21 − 0.1978) × 10.88k / (1M + 10.88k) = 53.9 mV
at the in-amp output: 53.9 mV × 2.185 = 118 mV
at the jack:          × (0.6 … 2.5)   = 71 … 292 mV
```

**54 mV is 27 % of the entire sensor pedestal**, injected differentially (the
return leg has no such path), by a supervision circuit, into a stage whose whole
purpose is DC accuracy. Commissioning absorbs it *only in the comparator state
it was trimmed in*. If the comparator ever sits near threshold and chatters, it
puts a 54 mV square wave directly into breath.

**Fix — standard and free:** apply the hysteresis at the comparator's **reference**
input rather than its signal input. Same hysteresis, zero injection into the
measurement node. Alternatively buffer the tap with one of the two spare op-amp
halves from finding 5.

**Two related checks while in this circuit:**

- `[calc]` Threshold margin. Worst-case pedestal at the node is
  `0.152 × 0.98912 = 0.150 V` against the specified +100 mV threshold `[repo,
  bom.csv row 100]` — **50 mV of margin**, before the LM311's own input offset.
  `[gated]` LM311 `V_OS`. It is workable but it should be stated as a margin
  rather than assumed from the 0.200 V typical.
- `[gated]` LM311 input bias current through the 10.88 kΩ node impedance is a
  further differential offset — at 150 nA that is 1.6 mV, ~9 mV at the jack
  `[calc]`, trimmed out at DC but not its drift.

---

## 9. An open AGND conductor is silent *(Low)*

`[calc]` If the `AGND` sense conductor opens while `BREATH` stays intact, R4
holds `IN+` at module ground and the in-amp reverts to measuring BREATH against
**local** ground — which reinstates the full shared-ground offset the entire
scheme exists to remove: up to 58.9 mV `[repo, ADR 0003]`, ×2.161 ×(0.6…2.5) =
**76 to 318 mV of LED-and-WiFi-correlated error at the jack**.

The presence comparator does not catch it: its reference leg is held at 0 V by
R4, so the BREATH node still reads +0.198 V and presence stays asserted `[repo,
bom.csv row 100; calc]`. `digital-and-supervision.md` claims *"One comparator
reports … both analog conductors intact"* `[repo]` — it reports the BREATH
conductor intact. An open AGND is exactly the failure it does not see.

The asymmetry is worth recording rather than fixing: **open BREATH is detected,
open AGND is not**, in a cable that gets flexed for years. Detecting it needs a
second comparator or a small bias current down AGND, neither of which is worth
it on a one-off — but a bench step at E10 ("pull pin 2 only, confirm the jack
gets noisy") costs nothing and turns an invisible failure into a known one.

---

## 10. The output RC *(Low-Medium)*

### Is it stable driving 2 m of patch cable? — Yes, as specified.

`[calc]` With the 330 nF on the **jack side** of the 1 kΩ, the op-amp sees the
capacitance through 1 kΩ and is unconditionally isolated; a 2 m patch cable's
~200 pF is four orders below the 330 nF already there and moves nothing. `bom.csv`
row 64 states the placement explicitly and correctly — *"ON THE JACK SIDE of
R-OUT-PROT, never the op-amp side"* `[repo]`. **Sound, and correctly reasoned.**

`[calc]` Loading: 1 kΩ into a 100 kΩ Eurorack input is 1.0 % of gain, absorbed by
the GAIN knob; the corner moves from 482.3 Hz to 487 Hz. Non-issue.

### But the drawing is ambiguous, on a page that exists to remove ambiguity

`[repo]` Line 65 reads:

```
                                   [1k]─┴─[C 330nF]── BREATH jack
```

The `┴` is a tee with the stem going **up** to the op-amp. Read literally, the
1 kΩ goes off to the left and the **330 nF sits in series with the jack** — a
DC-blocking capacitor on a DC control voltage. The "~480 Hz" annotation does not
disambiguate it: `1/(2π·1k·330n) = 482 Hz` is the same number for a high-pass as
for a low-pass `[calc]`. The BOM has it right; the drawing does not say so. On a
page whose stated purpose is that *"the ADR names the parts and none of the
topology"*, an ambiguous output filter is the same class of defect as finding 1.

### Is 330 nF film a real part in a sane package? — Not in the package specified.

`bom.csv` row 64 says **"1206 or THT"** `[repo]`. The same file, row 67, already
makes the argument that kills the 1206 option `[repo]`:

> *"82nF in C0G/NP0 almost certainly does not exist in 0805 — C0G permittivity
> puts that value in 1210 or larger."*

Film dielectrics have **lower** permittivity than C0G, not higher `[from
memory]`. If 82 nF C0G does not fit an 0805, 330 nF film does not fit a 1206 —
by a wide margin. `[gated]` distributor stock (mouser/digikey blocked). SMD film
at this value lives in ~4.5 × 3.0 mm or larger "box" packages; the through-hole
option (5 mm pitch polyester, ~7 × 2.5 × 6.5 mm) is an ordinary stock part and
is almost certainly the right answer `[from memory]`. **Specify THT and delete
the 1206.**

**The same check was not applied to `C-FILT-BREATH`:** 15 nF C0G in **0805**
`[repo, bom.csv row 63]` is marginal by the identical permittivity argument and
was flagged nowhere. `[gated]` — but it is the same question, one row apart, and
only one row asked it.

### The better topology is the one pitch already moved to

ADR 0006 records that pitch abandoned the jack-side capacitor for a **feedback
lead capacitor**, on the grounds that *"no DAC-driven module in the corpus puts
a capacitor on the jack side of the series resistor"* `[repo]`. Breath kept the
jack-side part. The arguments transfer: a lead cap across the downstream stage's
feedback resistor gives the same corner, **raises** phase margin, needs ~10 nF
instead of 330 nF (ordinary C0G, ordinary package), and leaves a bare 1 kΩ at the
jack. It does move the corner with the GAIN setting if gain is in the feedback —
which is a further reason to adopt the attenuator topology of finding 5, where
the feedback resistor is fixed and the corner is not.

**One label to correct either way:** the page calls this *"~480 Hz
**reconstruction** at the jack"* `[repo]`. There is nothing to reconstruct —
ADR 0006 says so itself four lines from where it tabulates the part: *"Breath is
the odd one because it never passes through the DAC: it has no zero-order-hold
image to attenuate"* `[repo]`. It is a band-limit and RF filter. Wrong labels
keep parts alive for the wrong reasons.

---

## 11. The gain derivation — it holds, with two caveats

I re-derived every line of the page's gain table independently `[calc]`:

| Page's line | My value | Verdict |
|---|---|---|
| Sensor span 0.2 → 4.8 V = 4.6 V | 4.799 − 0.200 = 4.599 V from `VS(0.1533P+0.04)` at P = 6, VS = 5 | ✓ consistent with ADR 0003's transfer function |
| Raw gain needed 2.174 | 10 / 4.6 = **2.17391** | ✓ |
| Bias-pair loading ×0.9891 | 1M/(1M+11k) = **0.98912** | ✓ (but see below) |
| Gain needed at in-amp 2.198 | 2.17391 / 0.98912 = **2.19783** | ✓ |
| `R_G` = 42.2 kΩ → G = 2.1848 | 1 + 50k/42.2k = **2.18483** | ✓ `[gated: INA828 gain equation, 50 kΩ assumed]` |
| Effective 2.1611 | 2.18483 × 0.98912 = **2.16106** | ✓ |
| Jack span 9.94 V | 2.16106 × 4.6 = **9.9409** | ✓ |
| Shortfall 0.6 % | (10 − 9.9409)/10 = **0.591 %** | ✓ |

**The arithmetic is internally consistent and I could not break it.** Say that
plainly. Two caveats:

**11a — the loading term is right for the wrong stated reason.** The page says
*"Loss in the 2 × 1 MΩ bias pair against 2 × 11 kΩ series"* `[repo]`. There is
only one 11 kΩ leg (the return leg is 10 kΩ), and only one leg carries signal, so
the correct derivation applies the divider **once**, on the signal leg. Applying
it twice as the wording implies would give `0.98912² = 0.97837` and a different
answer. The number lands right because the correct single-leg calculation is
what was actually computed. **This matters because the asymmetry the wording
erases is finding 3.**

**11b — the input span is 4.5 V or 4.6 V depending on which document you open.**
`[repo]` ADR 0003's parts table and `bom.csv` row 5 both say **0.2–4.7 V**;
ADR 0003's transfer function and this page say **4.8 V**. `[calc]` At 4.5 V of
span the effective gain gives `2.16106 × 4.5 = 9.725 V`, a **2.75 %** shortfall,
not 0.6 %. Both are absorbed by the GAIN knob, so nothing breaks — but the page
asserts a precision it does not have, and ADR 0003 contradicts itself on the
same page. `[gated]` MPXV4006DP full-scale output: typical from the transfer
function is 4.799 V, and 4.7 V is most likely the spec limit; nxp.com blocked.
Record both and stop quoting 0.6 %.

`[gated]` If the INA828's gain equation uses 49.4 kΩ rather than 50 kΩ, `G` =
2.1706 and the span becomes 9.88 V `[calc]` — a further 0.6 %, still inside the
knob. The choice of `R_G` is insensitive to this, which is worth knowing.

---

## 12. Numbers on the page that do not survive re-derivation *(Low)*

**12a — the 531 Hz pole is 481 Hz.** `[calc]` The differential source resistance
is `R1 + R3 + R2 = 11k + 10k = 21 kΩ`, and the differential capacitance is
`C_diff + C_cm/2 = 15.75 nF`:

```
stated:  1/(2π × 20k × 15 nF)     = 530.5 Hz   ← omits R1 and the C_cm term
actual:  1/(2π × 21k × 15.75 nF)  = 481.2 Hz
```

The target is "around 500 Hz", so nothing breaks — but 531 Hz is quoted as a
specification in `bom.csv` row 63 and again in ADR 0006 (*"already a 531 Hz
channel by the time it reaches the module"*) `[repo]`, and both omissions are
the same one that produced finding 3.

**12b — the filter's latency contribution is 4× the budget.** `[calc]` The
breath output path now has **two** ~481 Hz poles — the differential filter ahead
of the in-amp and the output RC — each contributing `1/(2πf) = 331 µs` of group
delay, **661 µs total**. ADR 0003's latency table budgets *"Op-amp and
reconstruction filter — ~160 µs"* `[repo]`, which corresponds to a single pole
near 1 kHz. Rebuilt: `1.0 ms (sensor) + 1.17 ms (tube) + 0.66 ms (filters) =
2.83 ms` against ADR 0003's stated ~2.6 ms and a 5 ms target. **Still comfortably
inside the target** — this is a bookkeeping error, not a design error — but the
latency budget is a centrepiece of ADR 0003 and it is 500 µs light on the one
channel that is supposed to be latency-critical.

**12c — "−9.6 V at full" and "9.94 V span" are the same node.** `[calc]`
`−2.185 × 4.6 + 0.437 = −9.614 V` uses the *nominal* gain; `−2.1611 × 4.6 =
−9.941 V` uses the *effective* one. Both appear on the same page, twelve lines
apart `[repo]`, and `bom.csv` row 28 gives a third figure ("−0.44 V at rest to
−10 V at full") for the pre-trimmer circuit.

**12d — the thermal-drift figure omits the downstream gain.** The page says
*"20 mV in 10 V over a full warm-up"* `[repo]`. `[calc]` At the stated
~0.5 mV/K over 20 K: `10 mV × 2.161 = 21.6 mV` at the in-amp output, but the
jack is downstream of a 0.6–2.5× stage, so it is **13 to 54 mV**. The page's
own honesty marker on this figure (*"That figure is unverified"* — offset tempco
`[gated]`, nxp.com blocked) is correct and well placed; the arithmetic on top of
it is the part that slipped.

---

## 13. `bom.csv` row 28 describes a circuit that no longer exists *(Medium)*

`bom.csv` is the build document. Row 28, `U-DIFFRX` `[repo]`:

> *"BREATH drives IN−, AGND drives IN+, **REF ties HARD to module AGND — no
> divider** … Output is **−0.44V at rest** to −10V at full; the downstream stage
> inverts, which is also the topology that does gain-then-offset with two pots
> **in one op-amp half**."*

Every clause after the first is now wrong, and the same file's rows **99, 100
and 108** are written against the *new* circuit (they discuss the trim, the
pedestal null, and why the old −200 mV presence threshold stopped working)
`[repo]`. **`bom.csv` contradicts itself internally about the state of the node
this stage is built on.** ADR 0003 likewise still states *"the in-amp's `REF`
pin ties to module analog ground and stays there"* `[repo]`, which the page
says it supersedes — but the page says that about *topology*, and a reader
checking the REF decision specifically will find two "settled" statements in
opposite directions.

This is the mechanism that produced finding 1 and finding 4: today's change was
made on one page and the dependent statements elsewhere were not swept. **List
of statements that need sweeping:** `bom.csv` row 28; ADR 0003's `REF`
parenthesis; ADR 0006's power-on table row for breath; `digital-and-supervision.md`'s
"cable unplugged → 0 V" and "`CLR` touches the breath stage in no way at all";
and `breath-receive-stage.md`'s own line 223 fossil, *"now that `REF` is
grounded"*.

---

## What I checked and found sound

Not a list of things I skimmed — each of these I tried to break and could not.

- **The gain derivation is arithmetically correct end to end**, and every
  intermediate value reproduces to four figures (section 11). The two caveats
  are about inputs and wording, not about the derivation.
- **The whole-chain polarity is correct** *as written in prose*: breath rises →
  BREATH conductor rises → `IN−` rises → in-amp goes negative → inverting
  downstream → jack goes positive. `[calc]` The drawing contradicts this
  (finding 1), but the intended circuit is right.
- **Buffering the `REF` pin is necessary and correctly justified.** Source
  impedance at an in-amp `REF` adds to the internal network one-for-one; a bare
  trimmer there would have been the dominant CMRR term. The page's reasoning is
  correct and the op-amp half is well spent.
- **`C_diff` ≫ `C_cm` is the right topology**, and the page's reasoning about
  single-ended capacitors is correct. My independent model reproduces the
  repository's own published "~19 dB" figure for the single-ended case to within
  1 dB `[calc]`, which is what gave me confidence in the numbers in finding 3b.
  The ratio is right; it is the *tolerance* that is unspecified.
- **Filtering ahead of the in-amp rather than after it is correct**, for exactly
  the reason given: a post-amplifier filter cannot prevent RF rectification at
  the input stage, and there is a 2.4 GHz radio on the same bundle.
- **The BAV99 is on the correct side of the 10 kΩ resistors.** `[calc]` At the
  connector its leakage faces a ~1 kΩ source and produces nanovolts; behind the
  10 kΩ it would face 1.011 MΩ and produce millivolts. The drawing puts it
  upstream, which is right, and the 10 kΩ then protects the in-amp from whatever
  the clamp lets through.
- **R1 = 1 kΩ genuinely does isolate the buffer from ~200 pF of cable.** `[calc]`
  The zero sits at 796 kHz against an op-amp GBW two orders higher; 1 kΩ is far
  more isolation than 200 pF needs. `bom.csv` row 66's reasoning is sound. (Its
  *package* is not — finding 2.)
- **R4/R5 do not violate the sense-return rule.** `[calc]` The common-mode
  current through `R2 + R4` is `58.9 mV / 1.01 MΩ = 58 nA`, against a ~350 mA
  power return: 0.17 ppm. The page's "tens of nanoamps, about 0.2 ppm" is
  correct, and the restatement of the rule as "no *power* current" is the right
  call.
- **The output capacitor's placement on the jack side of the 1 kΩ is correct**
  and the stability question is genuinely closed (section 10). The package is
  wrong; the topology is not.
- **The DP part's reference-chamber arrangement makes barometric pressure cancel**,
  which is why the zero trim can be a once-at-commissioning trim rather than a
  running calibration (section 6).
- **The split of zero authority by job — trimmer for calibration, panel knob for
  performance — is the right architecture**, and the parallel drawn to pitch's
  `TRIM-OFFSET`/firmware split is exact. My objection in finding 4 is to the
  trimmer's *reference source*, not to the trimmer.
- **Deleting the 100 kΩ differential pulldown in favour of a symmetric bias
  pair is correct**, and the reasoning (a purely differential element gives the
  inputs no DC path) is right.

---

## Recommended order of work

1. **Before the instrument carrier is laid out or bonded:** `R-SER-BREATH-INST`
   → 1206 ≥ 250 mW (finding 2). This is the only item that cannot be fixed later.
2. **Before anyone builds from the drawing:** fix the input swap in the ASCII
   art (finding 1) and disambiguate the output RC tee (finding 10).
3. **Module BOM, all one-line changes:** 1 kΩ added to the return leg (3a);
   `C_cm` at ±1 % (3b); trimmer range to 0–1.0 V (6); trimmer reference moved
   off `VREFOUT` to a local shunt reference (4); `C-OUT-BREATH` package to THT
   (10); LM311 hysteresis moved to its reference input (8).
4. **Draw the downstream stage** as a buffered attenuator plus a fixed-gain
   inverting summer, two op-amp halves, with the 15.6 kΩ taper resistor (5). The
   halves are already in the BOM.
5. **Sweep the stale statements** listed in finding 13.
6. **Consider the breath mute** off the existing LM311 (7).
