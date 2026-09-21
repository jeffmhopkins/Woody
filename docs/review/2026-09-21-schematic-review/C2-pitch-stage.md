# C2 — Pitch stage, cold review

**Subject:** `hardware/module/pitch-stage.md`, `docs/decisions/0006-cv-channel-allocation.md`,
and the pitch rows of `hardware/bom.csv` (`R-PRECISION`, `TRIM-GAIN`, `TRIM-OFFSET`,
`C-FB-PITCH`, `R-OPAMP-IN`, `R-OUT-PROT`, `D-JACK-CLAMP`, `U-OPA-PITCH`, `U-DAC`).

**Cold pass.** `docs/review/` and `docs/research/` were not read. Every claim below is
marked `[repo]` (with the file), `[calc]` (arithmetic shown), `[datasheet]`, or
`[from memory]`. No datasheet was reachable; anything that needs one is marked
**GATED** and is not asserted.

**Note on a mid-review revision.** `pitch-stage.md`, `bom.csv` and ADR 0006 were all
edited on disk while this review was being written. Every line quoted below was
re-verified against the **post-edit** files. The edit fixed two things I had flagged
(the `TRIM-GAIN` value in the Component values table, and `R-OFFINJ`/`C-FILT-PITCH`
lingering as live rows) and **made F2 worse**: the page's own component table has now
adopted the BOM's wording for the one net where the wording decides whether the stage
oscillates. F5, F8 and F11 are re-scoped accordingly. No finding was withdrawn.

**Method note.** The loop algebra was derived by hand and then checked numerically
(nodal admittance, ideal-integrator op-amp model `A(s) = A₀/(1+s/ω_d)`,
GBW = 10 MHz, A₀ = 2×10⁶). Script: `/tmp/.../scratchpad/loop.py`, `cl.py` — scratch,
not committed. Hand and machine agree to <1° everywhere.

---

## Severity table — ranked by retrofittability

The module is behind four screws, so anything that is a *value* or a *firmware constant*
is cheap. Anything that is a **net, a footprint or a missing footprint** is a re-fab.
Ranked worst-first on that axis.

| # | Finding | Cost to fix after fab | Sev |
|---|---|---|---|
| **F1** | **`C-FB-PITCH` is not a reconstruction filter.** In a non-inverting stage a feedback cap cannot roll the gain below **+1**; the measured response is a **6.02 dB shelf** (pole 14.5 kHz, zero 28.9 kHz), not a pole. Deleting `C-FILT-PITCH` removes **all** HF filtering at the pitch jack: **−6.0 dB at 1 MHz vs −36.0 dB** for the part that was deleted. The footprint is gone, so it cannot be added back. | **Re-fab** (deleted footprint) | **Critical** |
| **F2** | **`pitch-stage.md` now contradicts itself about the one net that decides whether the stage oscillates.** Its drawing (`:29`) and its handover table (`:163`) say `C-FB-PITCH` goes **op-amp output → (−)**; its Component values table (`:134`) now says "**across the feedback resistor**", matching `bom.csv:107` ("across R2") and ADR 0006 (`:602`). These are not the same circuit: as drawn, PM ≈ the op-amp's own unity-gain margin at every load; "across R2", PM = **18.1°** into a 2 m cable and **9.8°** into four. Three of the four places that name this net now name the wrong one. | **Re-fab** (wrong net) | **Critical** |
| **F3** | **`TRIM-OFFSET` cannot be built as specified.** `V_ref` = 2.500 V *is* `VREFOUT`; a divider across `VREFOUT` can only produce **less**. The ±60 cents of range the BOM claims needs "range resistors" that `pitch-stage.md` names twice (`:15`, `:131`) and that appear **in no BOM row**. As drawn (bare 10 k across `VREFOUT`) the span is 0–2.500 V ≈ **3000 cents**, i.e. ~250 cents per turn — not trimmable. | **Re-fab** (2 missing parts) | **Major** |
| **F4** | **The op-amp's (+) input has no DC path to ground.** Its only connection is `R-OPAMP-IN` to a DAC pin that is high-Z before the DAC's POR completes. The same defect was found and fixed on the breath in-amp (`R-BIAS-INAMP`, 1 M, `[repo] bom.csv:61`); pitch did not get the fix. Undefined (+) ⇒ the output can sit at **either rail** during the power-up window. | **Re-fab** (missing footprint) | **Major** |
| **F5** | **`TRIM-GAIN` is one-sided, and nothing now justifies the direction.** The page's load-divider justification was removed in the mid-review edit and replaced with the bare assertion "a series trimmer can only add, **which is the right direction**" (`:130`). It is not: the load divider it used to absorb is gone, and what remains — LT5400 ratio tolerance, wiper contact resistance — is **bipolar**, with the trimmer having **zero** authority to reduce gain. Range is also ~200× the residual error. Separately, a 2-terminal series trimmer **fails open** ⇒ `k → ∞` ⇒ output to the rail; the wiper must be strapped to an end, which is a footprint decision. | **Re-fab** (footprint/pinout) | **Major** |
| **F6** | **Jack-side feedback opens the DC loop when the jack is shorted.** β(DC) = 0 exactly; the op-amp saturates to **+11.5 V**. Every plug insertion wipes the sleeve across the tip, so **every patching action produces a full-rail event at the jack**, ~11.8 V into the destination as the plug seats. Not present with op-amp-side feedback. The page does not mention it. | Module-side / behavioural | **Major** |
| **F7** | **The power-on state is 0 V, not "below −2 V".** With `VREFOUT` disabled by default, both terms are zero ⇒ `Vout = 0 V` — a musically real note, not subsonic. ADR 0006's own table says "Pitch \| Bottom of its range, below −2 V \| Subsonic", and the `U-WATCHDOG` BOM row says `CLR` gives the "same state as rack power-on". After the reference is enabled, `CLR` gives −2.5 V. **The two states differ and the documents assert they are the same.** | Firmware + docs | **Moderate** |
| **F8** | **The page now states the 200 Ω trimmer in one place and the old 1 kΩ one in three others.** `:130` says 200 Ω / 0→+2 %; `:208` still says "the gain trim's **±5 %** range"; `:214` still computes the accuracy budget from "~**5 %** of the ratio"; `:229-231` still lists "**Whether `TRIM-GAIN` is 1 kΩ or 500 Ω**" as open, which its own `:130` has already closed at 200 Ω. The accuracy table therefore rests on a part that is not in the BOM, and calls that term "the largest line here" when the BOM part gives ~**0.07 cents** — 35× smaller than stated and 6× *smaller* than the DAC reference term. | Docs | **Moderate** |
| **F9** | **"The load-divider error is gone, for any load" is false at the ends.** True and excellent for R_L ≳ **1.7 kΩ**; below that the op-amp clips and the error returns unbounded; at a short it is total. Also true only at **DC** — above the ~14.5 kHz handover the divider is fully back. | Docs | **Moderate** |
| **F10** | **Three documents compute cents about three different pivots** for the same error, which is the whole of the "6× discrepancy … have not been reconciled" the page flags. It is arithmetic, not a real disagreement, and **both** published numbers are wrong. | Docs | **Moderate** |
| **F11** | *(Resolved by the mid-review edit — `R-OFFINJ` and `C-FILT-PITCH` are now marked deleted in the Component values table rather than listed as live parts. Kept as a numbered row so the finding numbering is stable.)* | — | **Closed** |
| **F12** | `R-PRECISION`'s note — "the other two [LT5400 sections] are available for the mod channels, which want 1:3 (three sections against the fourth)" — is **arithmetically impossible**: 1:3 consumes all four sections, pitch has already taken two, and four mod channels would need sixteen. | BOM | **Minor** |
| **F13** | "an OPA2197 on ±12 V less **two** Schottky drops" — there is **one** `D-REVPOL` per rail (`bom.csv:37`, qty 3, one each for analog +12, umbilical, −12). The repo carries three different headroom numbers: 11.45 V (this page), 11.65 V (ADR 0006), 11.9 V (`U-OPA-PITCH` row). | Docs | **Minor** |
| **F14** | **`VREFOUT` total DC load is unverified.** `TRIM-OFFSET` (10 k) + `TRIM-BREATH-ZERO` ("0 to ~+0.6 V from VREFOUT", `bom.csv:108`) ⇒ ≳500 µA continuous from an internal bandgap. | Gated on SBAS430 | **Open** |

---

## 1. Stability — the loop, worked

### 1.1 The network

With the (+) input at `Vdac` (no current through `R-OPAMP-IN`), the loop is entirely
in three nodes: `Vo` (op-amp output), `Vj` (jack), `Vn` (inverting input).

```
G1 = 1/R1 = 1e-4        R1 = 10 k       (Vn → V_ref, AC ground)
G2 = 1/10.2k = 9.804e-5 R2+trim         (Vn → Vj)
Gs = 1/Rs  = 1e-3       R-OUT-PROT 1 k  (Vo → Vj)
Yc = sCf   , Cf = 1 nF                  (Vo → Vn)
YL = 1/R_L + sC_L                       (Vj → ground)
```

Solving the two KCL equations for β = Vn/Vo (`[calc]`, derivation in full):

```
Vn(G1+G2+Yc) = Vo·Yc + Vj·G2
Vj(Gs+G2+YL) = Vo·Gs + Vn·G2          , D ≡ Gs+G2+YL

        Yc·D + G2·Gs
β(s) = ───────────────────────
       (G1+G2+Yc)·D − G2²
```

Written out with C_L, the numerator and denominator are both quadratics that share
their s² coefficient:

```
N(s) = Cf·C_L·s² + Cf(Gs+G2+G_L)·s + Gs·G2
M(s) = Cf·C_L·s² + [Cf(Gs+G2+G_L) + C_L(G1+G2)]·s + [G1(Gs+G2+G_L) + G2·G_L + Gs·G2]
```

so `M = N + a·s + b` with `a = C_L(G1+G2) ≥ 0` and `b = G1(Gs+G2+G_L) + G2·G_L ≥ 0`
for every passive load. **β(0) < 1 and β(∞) = 1 exactly**, because at high frequency
`Cf` shorts `Vn` to `Vo` and `R-OUT-PROT` then isolates whatever is on the jack. That
is the structural reason the arrangement works, and it is the one sentence the page
should have written and did not.

### 1.2 Phase margin, by load

`[calc]` — crossover and margin from `A(s)·β(s)`, GBW 10 MHz, A₀ 2×10⁶.
The op-amp's *own* excess phase near GBW is **GATED** (needs the OPA2197/OPA197
open-loop phase plot), so the right way to read this column is: **the feedback network
contributes ≈ 0° at crossover, therefore PM ≈ the op-amp's unity-gain phase margin.**

| Load at the jack | 1/β at DC | β zeros / poles | arg β at f_c | f_c | Verdict |
|---|---|---|---|---|---|
| **Nothing plugged in** (≈2 pF) | 2.10 | z 14.5 k / p 30.4 k | **+0.1°** | 10.0 MHz | Lead, max **+20.8°** at 21 kHz |
| **2 m cable, 200 pF, 100 kΩ** | 2.12 | z 14.6 k, 869 k / p 30.4 k, 885 k | **+0.2°** | 10.0 MHz | HF pair self-cancels; net lead |
| 200 pF, 33 kΩ (3 VCOs multed) | 2.16 | as above | **+0.2°** | 10.0 MHz | Lead |
| 800 pF, 25 kΩ (4 × 2 m, passive mult) | 2.18 | z 15.0 k, 212 k / p 30.2 k, 228 k | **+0.2°** | 10.0 MHz | Lead |
| 10 nF deliberately at the jack | 2.12 | complex z, ω_n 15.9 k ζ 0.55 / p 15.9 k, 33.4 k | **+0.2°** | 10.0 MHz | Lead, +19.5° at 15.9 kHz |
| **Jack shorted** | ∞ (β_DC = **0**) | single pole 31.8 kHz | **+0.2°** | 10.0 MHz | No oscillation — see §1.4 |

**So: yes, 1 nF compensates it, and by a wide margin.** `Cf` = 1 nF is ~50× larger than
the 18–22 pF the ADR's own prior-art note reports, and at 22 pF the loop is *still* a
lead network (`[calc]`: z 759 kHz ζ 0.58 / p 795 kHz, 1.53 MHz). Cable capacitance is
structurally incapable of putting lag in this loop, because `Cf` bypasses the jack path
entirely above the handover.

**This is finding F-zero, and it is an inverted honesty marker.** The page says
"**This is the highest-risk item on the page**" and ADR 0006 says "**This is the
highest-risk change in the module**." The arithmetic says the opposite: the loop is
the most robust thing on the page. The risk that *was* taken — deleting the only
low-pass at the jack (F1) — is presented as "the same corner in a better place."
The two markers are exactly swapped.

### 1.3 What *would* make it oscillate

1. **Building the words instead of the drawing.** `bom.csv:107` says "Feedback capacitor
   **across R2**", ADR 0006 (`:602`) says "1 nF **across the feedback resistor**", and
   since the mid-review edit `pitch-stage.md:134` says "**across the feedback resistor**"
   too — while the same page's drawing (`:29`) and handover table (`:163`) say **op-amp
   output**. Wire `Cf` from `Vn` to the **jack** and `β(∞) → Gs/(sC_L) → 0`, i.e. a −90° lag at
   crossover. `[calc]`: PM **18.1°** with 200 pF / 100 kΩ (f_c 2.75 MHz), **9.8°** with
   800 pF / 25 kΩ (f_c 1.40 MHz), **4.8°** if a 10 nF jack cap is also fitted. 18° is
   ~60 % overshoot and a visible ring on every note; 10° is an oscillator with a cable
   as its tuning element. **The drawing is right and the three prose lines are wrong**,
   and prose is what a layout gets read from. Fix the words, not the picture.
2. **Any capacitance from the op-amp output `Vo` to ground.** Above the handover
   `Vn = Vo`, so a cap there is a bare capacitive load with nothing in series. The
   `D-JACK-CLAMP` pads sit on exactly that node; a BAV99's ~1.5 pF is harmless, a
   "just in case" 100 pF footprint is not. Worth an explicit *do-not-populate-here*
   note on the schematic since ADR 0006 already identifies this as "genuinely dangerous"
   and the parts are now physically adjacent to it.
3. **Layout.** The DC feedback trace now runs from the jack back to the summing node —
   the longest, highest-impedance net on the board, ending at a 5 kΩ node, routed past
   the op-amp output and (in 8 HP) past the DAC's SPI. Guard it, keep it short, and keep
   it off the SPI. Cable capacitance is not the hazard; this trace is.
4. Not on this list: **200 pF, 800 pF, 10 nF, or a short.** None of them.

### 1.4 Shorted jack — the real finding (F6)

With `Vj` forced to 0, `β(s) = sCf/(G1+G2+sCf)`: a high-pass, **β(DC) = 0**. There is no
DC feedback at all. The inverting node is held by the R1/R2 divider at
`2.5 × R2/(R1+R2) = 1.262 V` `[calc]`, and for any `Vdac > 1.262 V` the op-amp output
**slams to the positive rail** and stays there.

- Op-amp output ≈ **+11.5 V** (±12 rack, one 1N5817 ≈ 0.35 V, RRIO to ~0.2 V of its rail —
  the 0.2 V figure is `[from memory]`, **GATED** on the OPA2197 swing spec).
- Into the short: 11.5 mA, 132 mW in `R-OUT-PROT` `[calc]` — inside the 250 mW the BOM
  specifies (`bom.csv:42`). ✅
- **Loop gain is zero only at DC.** Above the op-amp's dominant pole the loop retains
  `A₀·ω_d·Cf/(G1+G2)` = **314 (50 dB)** flat to 31.8 kHz `[calc]`, so it rails on a DC
  basis without oscillating. Confirmed numerically: PM ≈ 90° at f_c = 10 MHz.
- **The transient on release is the problem.** As a TS plug seats, the sleeve wipes the
  tip contact. Each break-then-make leaves the op-amp at +11.5 V, and the instant the
  short clears, `Vj` jumps to `11.5 × 100k/101k = 11.4 V` `[calc]` before the loop pulls
  it to +7 V. With op-amp-side feedback this event does not exist — the op-amp stays in
  its linear region throughout and the jack never exceeds the commanded voltage.
- Recovery is fast (rail-to-linear on an RRIO with rail-to-rail inputs, no input phase
  reversal — **GATED**, but OPA197's inputs are specified rail-to-rail `[from memory]`),
  so this is a click, not damage. **It is still a new failure mode created by the change,
  and the page presents the change as having only "consequences, all good."**
- Same mechanism for **output-to-output patching**, which the 1 kΩ exists to survive:
  our loop now *fights* the other module instead of yielding through 1 kΩ, and loses at
  4.45 mA.

**Recommendation (module-side, cheap):** none needed for safety; but state the behaviour
in `pitch-stage.md`, and add the short-and-release case to E9. If it bothers the player,
a 1 MΩ from `Vj` to `Vn` in parallel with R2 does nothing; the correct mitigation is a
clamp on `Vo` referenced to the commanded value, which is not worth the parts. Accept
and document.

---

## 2. The transfer function — re-derived

`[calc]`, from scratch. At DC no current flows in `Cf`, and the (+) input draws none, so
`Vn = Vdac`. KCL at `Vn`:

```
(Vj − Vn)/R2 = (Vn − V_ref)/R1
Vj = Vn + k(Vn − V_ref) = (1+k)·Vdac − k·V_ref        k ≡ R2/R1
```

With `k = 1` and `V_ref = 2.500 V`:

| Vdac | Vjack |
|---|---|
| 0.000 V | **−2.500 V** |
| **0.250 V** | **−2.000 V** ✅ |
| 2.500 V | +2.500 V |
| **4.750 V** | **+7.000 V** ✅ |
| 5.000 V | **+7.500 V** |

**The specification is met exactly.** Slope 9 V / 4.5 V = 2.000, intercept −2.500 V, both
as the page states `[repo] pitch-stage.md:50-51`. The unused 0.25 V at each DAC end is
0.5 V at the jack = **600 cents** of firmware reserve `[calc]` — the page's claim checks
out. Headroom: `Vo` must exceed `Vj` by the current through `R-OUT-PROT`; at `Vj` = +7.5 V
into 33 kΩ, `Vo` = 7.5 + (227 µA + 245 µA)·1 kΩ = **8.0 V** `[calc]`, comfortable.

**One thing the page's arithmetic quietly assumes:** `k = 1` requires `TRIM-GAIN` at
**0 Ω**, i.e. the trimmer at one mechanical end. With the trimmer at mid-scale (100 Ω,
`k = 1.01`) the endpoints are **−2.023 V / +7.023 V** `[calc]` — 27 cents out at both
ends. The page must state which setting is the design centre; it states neither, and the
answer changes whether F5 is a problem or a catastrophe.

**A second thing nobody has written down:** the feedback network itself loads the jack.
`I_fb = (Vj − Vdac)/(R2+trim) = (7.000 − 4.750)/10.2 kΩ = 220.6 µA` `[calc]`, flowing out
of the op-amp through `R-OUT-PROT` whether or not anything is patched. So `Vo` sits
**221 mV above `Vj`** even with nothing plugged in. Harmless, but it is a permanent
0.22 mA the power budget does not have and the headroom sums do not include.

---

## 3. A cermet trimmer in series with one leg of an LT5400 (F5)

### 3.1 The tempco question, quantified

Composite feedback leg `R2' = R2 + R_t`. Its tempco against R1:

```
α_ratio = (R_t/(R2+R_t))·(α_cermet − α_LT5400,abs) + α_LT5400,tracking
```

With `R_t` = 200 Ω, `R2` = 10 kΩ, `α_cermet` ≈ 100 ppm/°C `[from memory]` (**GATED** —
Bourns 3296 TC), `α_LT5400,abs` ≈ 25 ppm/°C and tracking ≈ 1 ppm/°C `[from memory]`
(**GATED** — LT5400 datasheet, and the grade suffix is still unresolved `[repo]`):

```
200/10200 × (100 − 25) = 1.47 ppm/°C   +   1 ppm/°C   ≈ 2.5 ppm/°C     [calc]
```

**So: yes, the trimmer degrades the network's ratio tracking by ~2.5×.** That is the
honest answer to "does it defeat the point of buying it."

### 3.2 But the number that matters is cents, and the page's is wrong by ~35×

`∂Vout/∂k = Vdac − V_ref`, which is **zero at Vdac = V_ref = 2.5 V** and at most
**2.25 V** anywhere in the 0.25–4.75 V window `[calc]`. A *ratio* drift therefore pivots
about `Vout = +2.5 V`, not about 0 V and not about −2 V. With 1 cent = 83.3 mV/100 =
**0.833 mV**:

| Term | drift over 10 °C | × pivot | error | cents |
|---|---|---|---|---|
| **`TRIM-GAIN` 200 Ω cermet** (BOM part) | 25 ppm of k | 2.25 V | 56 µV | **0.068** |
| LT5400 alone, 1 ppm/°C | 10 ppm of k | 2.25 V | 22.5 µV | 0.027 |
| Two discrete 25 ppm/°C, opposite | 500 ppm of k | 2.25 V | 1.125 mV | 1.35 |
| Two discrete 0.1 % 10 ppm/°C | 141 ppm of k | 2.25 V | 317 µV | 0.38 |
| **DAC internal ref, 5 ppm/°C** | 50 ppm of *everything* | **7 V** | 350 µV | **0.42** |
| OPA2197 Vos drift 0.25 µV/°C `[from memory]`, **GATED** | 2.5 µV × NG 2.1 | — | 5.3 µV | 0.006 |

Reference drift is a different animal: `Vout ∝ VREFOUT` for **both** terms (the page's own
δ argument, §"Why the offset reference must be `VREFOUT`", which is **correct** and is the
best paragraph on the page), so it pivots about `Vout = 0` and scales with the full 7 V.

**Consequences:**

- The page's "**TRIM-GAIN tempco … 0.4–2.4 cents at +7 V … Either way it is the largest
  line here**" (`:214`) is wrong three ways: it is computed from "~5 % of the ratio", i.e.
  the 1 kΩ trimmer that the same page's `:130` has already replaced with 200 Ω (F8), on
  the wrong pivot (F10), and the corrected figure — **0.068 cents** — is the *second
  smallest* line in its own table. `:208` ("±5 % range") and `:229-231` ("Whether
  `TRIM-GAIN` is 1 kΩ or 500 Ω" — already answered at `:130`) carry the same stale part.
- **The trimmer does not defeat the LT5400.** It costs 0.04 cents.
- **But nothing else justifies the LT5400 either.** At 0.027 cents it is 15× inside the
  DAC's own reference term, which cannot be trimmed out. Two 0.1 %/10 ppm discretes give
  **0.38 cents** — *comparable to* the reference term, for ~$0.30 against ~$8. ADR 0006
  half-says this ("the precision-network argument was over-engineering relative to the
  load it feeds") and then keeps the part anyway. For a one-off that is a defensible
  indulgence; it should be recorded as one, not as necessity.

### 3.3 The real defects in `TRIM-GAIN`

**(a) It is one-sided and the direction is now unjustified.** Before the mid-review edit
this row read "a series trimmer can only add. That is the right direction for the load
divider, **which only ever reduces gain**" — a justification the page's own headline change
deletes, since it removes the load divider. The edit removed the justification and kept the
conclusion:

> "**0 → +2 % of ratio, one-sided** — a series trimmer can only add, **which is the right
> direction**" `[repo] pitch-stage.md:130`

It is not the right direction, and no reason is now offered. What remains —
LT5400 ratio tolerance (±0.01 % to ±0.05 % depending on grade, **GATED**), wiper contact
resistance, op-amp finite gain — is **bipolar**, and a series trimmer has no authority to
reduce `k` at all. Set the design centre at the trimmer's mid-point (100 Ω) and firmware
absorbs the resulting 27 cents; or accept that a high-reading gain is uncorrectable in
hardware. Either is fine — but the stated reasoning is stale and must not survive into
layout, because the part value follows from it.

**(b) Range is ~200× the residual error.** `[calc]` 0 → 200 Ω gives `Δk` = 0.02 ⇒
`ΔVout = 0.02 × 2.25 V = 45 mV` = **54 cents** at each end (108 cents end to end). The
LT5400 residual is 0.27 cents at grade A. So 99.5 % of the trimmer's travel corrects
nothing. On a 12-turn part that is 4.5 cents/turn `[calc]` — usable, but it is a
screwdriver with 200× more authority than the error it faces, and its whole tempco
contribution exists to provide it.

**(c) A 2-terminal series trimmer fails OPEN.** The drawing shows
`[R2 10k]─[TRIM-GAIN 200R]` as a two-terminal element in the DC feedback leg carrying
221 µA. A lifted wiper ⇒ `R2 → ∞` ⇒ `k → ∞` ⇒ **output to the rail**. Strap the unused
end to the wiper so the failure is 200 Ω, not infinity. This is a *footprint* decision
(three pads, two netted together) and is therefore a re-fab if it is missed. It is
standard practice and appears nowhere in the page or the BOM.

**(d) Wiper contact resistance is inside the pitch ratio.** 1–2 Ω of contact variation on
10.2 kΩ is 0.02 % of `k` = **0.54 cents** `[calc]`, temperature- and vibration-dependent
and not trimmable. That is **8× the trimmer's tempco term** and is the actual reason to
care about the trimmer — and it is not mentioned anywhere.

---

## 4. The offset trimmer ahead of the reference buffer (F3)

### 4.1 Does trimming `V_ref` move the intercept without touching the gain?

**Ideally, yes — the page's claim is correct.** `Vout = (1+k)·Vdac − k·V_ref`, so
`∂gain/∂V_ref = 0` identically `[calc]`. The page's diagnosis of the *old* arrangement is
also correct and well-argued: injecting into a non-inverting stage's (−) node, which sits
at `Vdac` and not at a virtual ground, does carry a gain term.

**The δ-tracking argument also survives the move**, which is worth confirming because the
page does not. With `V_ref = f·VREFOUT` for any divider fraction f, and DAC full scale
= 2·VREFOUT:

```
Vout = (1+k)·2D·VREFOUT − k·f·VREFOUT = VREFOUT·[(1+k)2D − kf]
```

— still linear in `VREFOUT`, so a reference drift is still a pure gain error for **any**
trim setting `[calc]`. ✅

### 4.2 Three things that are wrong anyway

**(a) `V_ref` = 2.500 V is not reachable.** `VREFOUT` *is* 2.500 V; a divider across it
produces `f·VREFOUT ≤ 2.500 V`, with equality only at the mechanical end of travel. So
the design's nominal value sits exactly where the trimmer has no downward… sorry, no
*upward* authority, and the entire trim is one-sided in the "make the output sharp"
direction. The page's exact arithmetic (`Vout = 2·Vdac − 2.500`) is only true at one end
stop.

**(b) The range resistors do not exist.** Both the drawing (`:14-15`) and, since the
mid-review edit, the Component values table (`:131`, "10 kΩ multiturn cermet **+ range
resistors**") name them `[repo]`. There is still **no BOM row** for them; `grep` of `bom.csv` finds `TRIM-OFFSET` alone. The BOM's claimed
"~50 mV … ~60 cents" range **requires** them. A bare 10 k pot across `VREFOUT` gives
0–2.500 V = **3000 cents**, ~250 cents per turn on a 12-turn part `[calc]` — unusable.

**(c) The two one-sided trims consume each other.** `∂intercept/∂k = V_ref`, so a
full-scale gain trim (Δk = 0.02) shifts the intercept by **50 mV = 60 cents** `[calc]` —
*the entire* offset-trim range the BOM claims. The page's iterate-twice procedure can
therefore run out of offset range with a perfectly ordinary build. The directions happen
to be complementary (gain trim in ⇒ output flat at the bottom ⇒ reduce `V_ref` ⇒ output
up), so it *can* converge, but with **zero** margin for build tolerance and **no**
authority in the opposite direction at all.

### 4.3 Buildable fix

Give up on `V_ref` = 2.500 V exactly and centre the trim below it. Firmware has 600 cents
of DAC-window reserve `[repo]` — 60 cents of intercept shift is a rounding error there:

```
VREFOUT ──┬── TRIM-OFFSET 10k ──[R_b 240k]── AGND        wiper → follower (+)
          │
        (wiper spans 2.400 … 2.500 V)
```

`[calc]` bottom of the pot = 2.500 × 240/250 = **2.400 V**; span **100 mV = 120 cents**,
centred at 2.450 V; nominal endpoints become −1.950 V / +7.050 V, which firmware shifts
back with a 25 mV DAC-code offset. Load on `VREFOUT` falls from 250 µA to **10 µA**,
which largely disposes of F14. Thévenin at the wiper ≤ 4.9 kΩ; with the OPA2197's CMOS
input bias that is < 1 µV of offset `[from memory]`, **GATED**, and 9 nV/√Hz of Johnson
noise = 1.3 µV rms over 20 kHz = **0.0016 cents** `[calc]`. One extra resistor, and the
trim becomes genuinely bipolar about its design centre.

### 4.4 `VREFOUT` loading (F14) — what is and is not a problem

- **Static loading is self-cancelling.** The pot's end-to-end resistance does not change
  with wiper position (the follower draws nothing), so turning the trimmer does **not**
  move `VREFOUT` — ADR 0006's stated reason for the buffer ("hanging a *trimmer* directly
  on `VREFOUT` would make the reference move as the trimmer is turned") is answered by
  the high-Z wiper, not by the buffer's position. Any static shift is a gain term the
  gain trim removes. ✅
- **Thermal loading is negligible.** 100 ppm/°C on 10 kΩ over 10 °C changes the load
  current by 0.25 µA `[calc]`; even at 1 Ω of reference output impedance that is 0.25 µV.
  ✅
- **What is *not* verified** is whether `VREFOUT` can source ≳500 µA at all
  (`TRIM-OFFSET` 10 k **plus** `TRIM-BREATH-ZERO`, "0 to ~+0.6 V from VREFOUT",
  `[repo] bom.csv:108`) without degrading its drift or noise spec. **GATED** on SBAS430:
  *`VREFOUT` maximum output current / load regulation / noise vs load*. The §4.3 fix
  reduces the pitch half of that load by 25×, which is a good reason to adopt it
  regardless.
- Note also that `pitch-stage.md:129` says `V_ref` is "**Shared with nothing else**".
  True of the *buffered* node; false of `VREFOUT`, which the breath zero trim also hangs
  on.

---

## 5. Power-on and rail skew (F4, F7)

Rails: `+12 → D-REVPOL → beads → LM317LZ → 5.21 V` for DAC AVDD `[repo] bom.csv:38`; the
op-amps sit directly on ±12. So **+12 leads 5.21 V by the LM317's dropout and its output
cap's charge time**, and the DAC's own POR follows that.

| Window | `Vdac` | `V_ref` | Jack | Assessment |
|---|---|---|---|---|
| Everything at 0 | 0 | 0 | 0 V | ✅ |
| **±12 up, 5.21 V not yet** | **high-Z / undefined** | 0 | **undefined — either rail** | ❌ **F4** |
| 5.21 V up, DAC POR done, reference **still disabled** | 0 V | **0 V** | **0 V** | ❌ **F7** |
| Firmware enables `VREFOUT`, before first write | 0 | 2.5 V | **−2.500 V** | ✅ subsonic |
| Watchdog `CLR` in service | 0 | 2.5 V | **−2.500 V** | ✅ subsonic |
| Power-down: 5.21 V held on its cap, ±12 collapsing | ≤5 V | ≤2.5 V | — | ✅ see below |

**F4 — the undefined window.** `R-OPAMP-IN` connects the (+) input to a DAC pin only.
Whether a DAC8568 output is high-Z before POR completes is **GATED** (SBAS430, *power-on
output state / output buffer enable*), but the design must not depend on the answer: the
(+) input of a CMOS-input op-amp with a 1 kΩ to a high-Z node has no defined potential,
and the output is then `2·V(+)`, i.e. either rail through `R-OUT-PROT` into whatever is
patched. **The project already knows this pattern** — `R-BIAS-INAMP` (1 MΩ, qty 2) exists
precisely because "without these the in-amp floats when unplugged and saturates to a rail"
`[repo] bom.csv:61`. Pitch's (+) input needs the same 1 MΩ to AGND. Cost: one 0805.
Gain error: 1 kΩ/1 MΩ = 0.1 % of `Vdac` — **not** negligible, so put the 1 MΩ on the DAC
side of `R-OPAMP-IN` where it loads the DAC output (a DAC output is low-Z) rather than the
op-amp input. Then it costs nothing and still defines the node. Missing footprint ⇒
re-fab.

**F7 — the parked voltage.** ADR 0006 states the internal reference is **disabled by
default** and that "the outputs sit at 0 V from rack power-on until firmware enables the
reference" `[repo] 0006:...` — and then its own summary table says pitch parks "Bottom of
its range, **below −2 V** \| Subsonic. A VCO there is inaudible". Both cannot be true.
With this topology, `Vout = (1+k)·0 − k·0 = 0 V` `[calc]`: **a mid-range note, not a
subsonic one**. The `U-WATCHDOG` BOM row inherits the error: "CLR parks pitch subsonic and
mods at 0 V — **same state as rack power-on**" `[repo] bom.csv:54` — `CLR` gives −2.5 V
because `CLR` does not disable the reference, power-on gives 0 V. They are different
states.

In practice breath parks at 0 V so the VCA is shut and nothing is heard — which is why
this is Moderate and not Major. But it is a **claim used to justify the grade selection**
(`U-DAC`, "GRADE LOCKED TO C … C also clears to ZERO scale"), and a design should not
carry a safety argument that is false. Fix in firmware: enable `VREFOUT` and write
`Vdac = 0` in the same boot sequence, before anything else; and correct the three
documents.

**Reverse skew is covered.** On power-down the 5.21 V rail holds on `C-REG-ADJ` while ±12
collapses; the DAC can then drive up to 5 V into an unpowered op-amp input. `R-OPAMP-IN`
bounds that at (5 − 0.7)/1 kΩ = **4.3 mA** `[calc]`, which is what ADR 0006 specifies the
part for. ✅ The same protection covers the `VREFOUT` follower, which also has an
`R-OPAMP-IN` `[repo] bom.csv:51`.

**One power-on consequence unique to jack-side feedback:** during the undefined window the
op-amp can sit at a rail while the DAC is dead, and the DC loop is closed through the
*jack*. A patched VCO therefore sees up to ±11.5 V through 1 kΩ at every rack power-up
until firmware asserts. With F4 fixed the node is defined and the output is 0 V; without
it, it is a coin flip.

---

## 6. `C-FB-PITCH`: is one part doing both jobs? (F1)

**No. It does the compensation job superbly and the filter job not at all.**

### 6.1 The response is a shelf, not a pole

`[calc]` — exact, ideal op-amp, nothing plugged in. With `τ = (R2+Rs)·Cf = 11.2 kΩ × 1 nF
= 11.2 µs`:

```
Vjack       2 + sτ
───── = ─────────────        DC gain 2  →  HF gain **1**
Vdac        1 + sτ
```

Pole **14.5 kHz**, zero **28.9 kHz**, total attenuation **6.02 dB, forever**. The reason
is structural and is the same one that makes the loop stable: at high frequency `Cf`
shorts `Vn` to `Vo`, the stage becomes a **unity-gain follower of `Vdac`**, and the (+)
input is a direct feedthrough path that no amount of feedback capacitance can attenuate.
**A feedback cap low-passes an *inverting* amplifier. In a non-inverting amplifier it
shelves.** This is textbook and both `pitch-stage.md` and ADR 0006 assert the opposite.

The stated corner is also not what the page says: "1 nF × 10 k = 15.9 kHz, the same
corner" `[repo] bom.csv:107` uses R2 alone; the actual pole is at
`1/(2π·11.2k·1n)` = **14.2 kHz** because `R-OUT-PROT` is inside the DC feedback leg. Minor
next to the shelf, but it shows the calculation was never done on the drawn circuit.

### 6.2 What was lost

`[calc]`, magnitude relative to DC gain:

| Frequency | **As drawn**, nothing plugged | **As drawn**, 2 m / 100 kΩ | Deleted `C-FILT-PITCH` (1 k + 10 nF) | Both parts fitted |
|---|---|---|---|---|
| 4 kHz | −0.16 dB | −0.16 dB | −0.27 dB | +0.37 dB |
| 16 kHz | −2.29 dB | −2.26 dB | −3.03 dB | +0.15 dB |
| 100 kHz | −5.76 dB | −5.76 dB | **−16.1 dB** | **−20.8 dB** |
| **1 MHz** | **−6.02 dB** | −9.63 dB | **−36.0 dB** | **−41.2 dB** |
| 10 MHz | −6.08 dB | −27.2 dB | −56.0 dB | −61.2 dB |

**At 1 MHz the drawn circuit is 30 dB worse than the part it deleted.** ADR 0006's stated
requirement for this filter — "enough to kill DAC step glitches" and "Corner it around
10–20 kHz" `[repo] 0006` — is not met: a code-transition glitch is a narrow spike whose
energy is decades above 29 kHz, and it now reaches the jack attenuated by 6 dB. The same
goes for SPI feedthrough on an 8 HP board where the DAC sits next to the output stage.
(DAC8568 glitch impulse magnitude: **GATED**, SBAS430.)

Worse: **how much filtering the jack gets now depends on what the player plugs in.**
Nothing plugged in ⇒ −6 dB flat. 2 m cable ⇒ a further pole at
`1/(2π·(1k∥100k)·200pF)` = **804 kHz** `[calc]` ⇒ −9.6 dB at 1 MHz. A short cable ⇒ back
to −6 dB. The reconstruction characteristic of a precision pitch output should not be a
function of the patch.

`docs/reference/latency-budget.md:64` — "Pitch is 15.9 kHz and costs ~10 µs" — is
consequently also wrong; the shelf's group delay is different and it is not a 15.9 kHz
filter at all.

### 6.3 The page's stated reason for deleting it is not supported

> "A 10 nF to ground at the jack would now sit on the feedback node, inside the DC loop,
> right at the handover — the one place it must not be." `[repo] pitch-stage.md:166-168`

`[calc]` — with 10 nF at the jack, β has **complex zeros** (ω_n 15.9 kHz, ζ 0.55) and real
poles at 15.9 kHz and 33.4 kHz. Zeros below poles ⇒ **still a lead network**; arg β = +19.5°
at 15.9 kHz; crossover unchanged at ~10 MHz with arg β = +0.2°; **PM unchanged**. The
reason it is safe is the same reason the whole topology is safe: `Cf` ties `Vn` to `Vo`
above the handover, and `R-OUT-PROT` then isolates the jack capacitance from the op-amp
output completely. The 10 nF is a *load* on the op-amp through 1 kΩ, which is the
textbook-safe way to drive a capacitive load.

(ADR 0006's own hazard table is right about the general case — "Cap to ground **at the
op-amp output**, before the series R … genuinely dangerous" — and then applies it to the
wrong node.)

### 6.4 Recommended values

`[calc]`, ideal op-amp, 100 kΩ load, sweeping both caps:

| `C-FB-PITCH` | `C-FILT-PITCH` | Peaking | −3 dB | @1 MHz | Loop |
|---|---|---|---|---|---|
| 1 nF | **deleted (as drawn)** | — | 20.5 kHz (then flat at −6 dB) | **−6.0 dB** | PM ≈ op-amp's |
| 1 nF | 10 nF C0G | +1.18 dB @ 11 kHz | 21.6 kHz | −41.3 dB | PM ≈ op-amp's |
| **2.2 nF** | **10 nF C0G** | **0.00 dB** (maximally flat) | **12.2 kHz** | **−41.3 dB** | **PM ≈ op-amp's, verified at every load incl. short** |
| 1 nF | 47 nF | +6.28 dB @ 6.8 kHz | 11.0 kHz | −54.7 dB | stable but ringing |

**Restore `C-FILT-PITCH` at 10 nF C0G on the jack side, and raise `C-FB-PITCH` to 2.2 nF.**
That gives a genuine second-order low-pass, maximally flat, −3 dB at 12.2 kHz (inside
ADR 0006's own 10–20 kHz window), −41 dB at 1 MHz, and phase margin indistinguishable
from the drawn circuit at every load I tested including a dead short. The jack cap also
**swamps the cable capacitance**, so the response stops depending on the patch.

If the 10 nF is not restored the footprint must still be there: **a DNP pad costs nothing
before fab and is impossible after.** That is the single cheapest insurance on this page.

Note this also retires the page's claim that the two capacitors "are not the same part and
three of those four designs ship both" — correct, and the page then ships only one.

---

## 7. "The load-divider error is gone for any load" (F9)

`[calc]`. DC noise gain with load: `1/β = 2.1 + 2000/R_L`. Closed-loop gain error
≈ `(1/β)/A_OL`. `A_OL` for the OPA2197 is **GATED** (SBAS…, *open-loop gain vs load*);
using 126 dB typ / 114 dB min `[from memory]`:

| Load | 1/β | Gain error (typ / min A_OL) | Error at +7 V | Verdict |
|---|---|---|---|---|
| **1 MΩ** | 2.102 | 1.05 / 4.20 ppm | 7 / 29 µV = **0.009 / 0.035 cents** | ✅ claim holds |
| **100 kΩ** | 2.120 | 1.06 / 4.24 ppm | **0.009 / 0.036 cents** | ✅ claim holds |
| **33 kΩ** | 2.161 | 1.08 / 4.32 ppm | **0.009 / 0.036 cents** | ✅ claim holds |
| 1.7 kΩ | 3.28 | 1.6 / 6.6 ppm | 0.014 / 0.055 cents | ⚠️ at the clip boundary |
| **Short** | ∞ (β = 0) | — | **unbounded** | ❌ claim fails |

**The headline claim is true, and impressively so, over the range that matters** — the
−11.9 and −23.5 cents/octave figures really do become historical, and the per-load affine
preset really does stop being load-bearing. Credit where it is due: this is the right
change and the arithmetic supports it.

**Where it fails is stated nowhere.** The binding constraint is the op-amp's headroom, at
the *top* of the range:

```
Vo,max ≈ +11.5 V   (±12 − one 1N5817 0.35 V − RRIO 0.2 V)      [calc], GATED on swing spec
at Vj = +7.000 V:  drop available across R-OUT-PROT = 4.50 V
                   I_total,max = 4.50 mA
                   I_feedback  = (7.000 − 4.750)/10.2 k = 0.221 mA
                   I_load,max  = 4.28 mA   ⇒   R_L,min = 7.000/4.28 m = **1.64 kΩ**
at Vj = +7.500 V (reserve):                    R_L,min = **2.0 kΩ**
at Vj = −2.000 V:                              R_L,min = 0.21 kΩ
```

So: **"for any load" should read "for any load above ~2 kΩ, and only at DC."** No Eurorack
CV input is below 2 kΩ, so this is a documentation defect and not a design defect — but
the page states an unqualified universal and the reader should know where it stops. The
"only at DC" half matters more than it looks: above the ~14 kHz handover the loop hands
control to `Cf` and the divider is fully back, so the *AC* gain into 100 kΩ is 0.990 of
the unloaded value. For a pitch CV that is irrelevant; it should still be written down,
because it is exactly the sentence that stops someone reusing this topology on a channel
where it is not.

---

## 8. What I checked and found sound

- **The DC transfer function.** `Vout = (1+k)Vdac − k·V_ref` re-derived from scratch;
  −2.000 V at 0.25 V and +7.000 V at 4.75 V, exactly, with k = 1 and V_ref = 2.500 V
  `[calc]`. The 600-cent firmware reserve at full DAC scale is real `[calc]`.
- **"Two resistors, not four."** Correct, and the correction notice is right: `A = 1 + B`
  is the topology's identity, not a boundary. The free parameter genuinely is `V_ref`.
  The page owns a previous error cleanly and the new reasoning is sound.
- **The δ argument** (`Vout = (1+δ)(2Vdac − 2.5)`, so reference drift is a pure gain
  error) is correct, and correct for *any* divider fraction on the reference — a stronger
  result than the page claims `[calc]`. The cents comparison between offset and gain
  errors on a 1 V/oct output is the right frame and the right conclusion.
- **`R-OPAMP-IN` costs no gain error.** True: the (+) input of a CMOS-input op-amp draws
  ~pA, so 1 kΩ contributes ~5 nV `[calc]`. Noise contribution 4 nV/√Hz against the
  op-amp's own ≈5.5 nV/√Hz `[from memory]`, **GATED**: total ~2 µV rms = **0.002 cents**
  `[calc]`. The bias-current mismatch against the (−) node's 5.1 kΩ is likewise nil.
- **Loop stability with cable capacitance**, the thing the page fears: 200 pF, 800 pF,
  10 nF and a short all leave β a **lead** network with arg β ≈ +0.2° at crossover
  `[calc]`, verified by hand and numerically. 1 nF over-compensates generously; even
  22 pF would be stable in this topology.
- **Stray capacitance at the summing node** is swamped: `Cf` (1 nF) against ~5–10 pF of
  input + PCB capacitance is a 100:1 divider, β(∞) = 0.99 `[calc]`. This is the one place
  the large `Cf` earns its keep as compensation.
- **`R-OUT-PROT` power rating.** 11.5 V into a short through 1 kΩ = 11.5 mA, **132 mW**
  `[calc]`, inside the 250 mW / 1206 the BOM specifies `[repo] bom.csv:42`. ✅
- **`D-JACK-CLAMP` leakage claim.** With the DC tap at the jack, a driver-side clamp is
  genuinely *inside* the loop, so its leakage is absorbed and the "2.4 cents of BAT54S
  error goes to identically zero" reasoning `[repo] bom.csv:52` holds for this topology.
  ✅ (It did not hold before the change; it does now.)
- **Back-powering through the feedback leg.** A neighbour driving 10 V into the pitch jack
  with this module off pushes (10 − 0.7)/10.2 kΩ = **0.91 mA** through R2 into the op-amp's
  input clamp — a path the `D-JACK-CLAMP` relocation does not cover, but 8× smaller than
  the 7.6 mA/jack the BOM already accepts `[calc]`. Not a finding.
- **`VREFOUT` load does not move when the trimmer is turned** (§4.4), and its thermal
  variation is 0.25 µA `[calc]`. The ADR's stated worry is real in general and answered
  here by the high-Z wiper.
- **Settling on a note change.** As drawn, the step response jumps immediately to 50 % (the
  +1 feedthrough) then exponentially with τ = 11.2 µs; 1-cent settling in **70 µs**
  `[calc]`. With the §6.4 fix it is second-order, maximally flat, ~1-cent settling in
  ~130 µs `[calc]` — both inside the ~10 µs–60 µs allowances in
  `docs/reference/latency-budget.md` being generous by comparison, and both well inside
  the 250 µs loop pass. Not a problem either way, but the latency table's "~10 µs" is
  optimistic for the fixed version and meaningless for the drawn one.
- **`C-FB-PITCH` dielectric and package.** 1 nF C0G in 0805 is an ordinary part, unlike
  the 82 nF C0G the BOM already flags on the mod channels `[repo] bom.csv:67`. The
  C0G-never-X7R reasoning (piezoelectricity in a pitch filter) is correct and well put.
- **Trim procedure order** (high note → gain, low note → offset, repeat) is the right
  order for this topology, and the asymmetry the page describes — offset does not touch
  gain, gain does touch offset — is exactly right `[calc]`, `∂intercept/∂k = V_ref ≠ 0`.

---

## 9. Suggested disposition

**Before fab, non-negotiable:**

1. Fix the `C-FB-PITCH` net wording in **all three** prose places — `bom.csv:107`,
   ADR 0006 `:602` and now `pitch-stage.md:134`: it is **op-amp output → (−) input**, not
   "across R2" / "across the feedback resistor". The drawing at `:29` is the correct one
   and is the only place that currently says so. (F2)
2. Restore the `C-FILT-PITCH` footprint on the jack side; populate 10 nF C0G and raise
   `C-FB-PITCH` to 2.2 nF. If the decision is to leave it empty, leave the **pad**. (F1)
3. Add the `TRIM-OFFSET` range resistor(s) — one 240 kΩ to AGND buys a buildable ±60 cent
   bipolar trim and cuts the `VREFOUT` load 25×. (F3)
4. Add a 1 MΩ from the DAC-side of `R-OPAMP-IN` to AGND. (F4)
5. Lay `TRIM-GAIN` out as a 3-pad footprint with the wiper strapped to an end. State the
   design-centre setting (mid-scale) and delete the load-divider justification. (F5)
6. Guard/shorten the jack-to-summing-node feedback trace; annotate the `Vo` node
   "no capacitance to ground". (§1.3)

**Cheap, documentation:** F7–F10, F12, F13 — in particular reconcile `pitch-stage.md`
`:208`, `:214` and `:229-231` with its own `:130` (200 Ω, 0 → +2 %), and recompute the
accuracy table on the correct pivots (§3.2). F11 was closed by the mid-review edit.

**Gated, resolve when a datasheet is reachable:** DAC8568 `VREFOUT` max output current and
load regulation; DAC8568 output state before POR; DAC8568 glitch impulse; OPA2197
open-loop gain and phase vs load, output swing, Vos drift; LT5400 grade/option code, ratio
tolerance and tracking tempco; Bourns 3296 TC and wiper contact resistance. **None of
these change any finding above** — every one of them is used only to size a margin that is
already one or two orders of magnitude on the right side.
