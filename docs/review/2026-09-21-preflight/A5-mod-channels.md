# A5 — Mod channels 1–4

**Slice:** `hardware/module/mod-channels.md` + `docs/decisions/0006-cv-channel-allocation.md`
**Method:** cold (no prior review directory read). Every figure re-derived or
re-read against a banked PDF.
**Banked documents used:** `datasheets/texas-instruments/DAC8568CIPW.pdf`
(SBAS430E rev E, Jan 2014, 62 pp), `datasheets/texas-instruments/OPA2197.pdf`
(SBOS737C), `datasheets/texas-instruments/REF5050.pdf` (SBOS410O — not used;
no REF5050 appears in this stage, see N-12).

Findings are indexed by **node or refdes**, not by file and line.

---

## Summary of the ten that matter

| # | Node | Finding | Severity |
|---|---|---|---|
| **F1** | `MODn_JACK` | The stage is a **1.00 kΩ unbuffered source**. "Exactly ±10.000 V" is an **unloaded** number; a single 100 kΩ Eurorack input costs **−99 mV** at +10 V, twice the whole stated tolerance budget. A passive mult to four costs **−385 mV**. A 1 kΩ input **halves it**. | **HIGH — must be stated** |
| **F2** | `U-DAC` pin 9 `CLR` | The page and ADR 0006 both attribute clear-to-zero-scale to the **grade**. It is not. The grade fixes **power-on reset** only; the `CLR` pin clears to the **clear code register**, which is firmware-writable to midscale, full scale, or *ignore*. A `ClearFullScale` write puts **+5.00 V on all four jacks**. | **HIGH — safety** |
| **F3** | `MODn_DRV` | "A B or D part would put **+2.5 V** on all four jacks" is **wrong for B**. B is gain 1, so its midscale is **1.250 V**, giving **+1.250 V**. Only D gives +2.5 V. Stated wrong in two files. | **MEDIUM — datasheet-refuted** |
| **F4** | `VREF_MOD` | "At **2.5 V** into 2.5 kΩ that is 1 mA" (line 199) is the **stale pre-redraw reference value**, and the load model is wrong regardless — the far end of each 10 kΩ sits at `Vdac`, not at ground. `check-staleness.py` cannot see it: the string is not in `forbidden`. | **MEDIUM — staleness, checker-invisible** |
| **F5** | `DAC_MODn` | **`R-BIAS-DAC` (100 kΩ, qty 6, `bom.csv:128`) is not on this drawing at all** — five of its six instances belong to this page. Without it the op-amp `(+)` inputs have no DC path to ground. A part whose BOM row states a specific failure mode is missing from the schematic that would be used to stuff the board. | **HIGH — netlist-blocking** |
| **F6** | `U-DAC` channel numbering | Nothing in the corpus maps "channel 1…8" to the DAC8568's **`VOUT-A`…`VOUT-H`**. Netlist cannot be written. | **HIGH — netlist-blocking** |
| **F7** | `AGND` | Two different nets share one token: module analog return (this page) and the umbilical's in-amp sense conductor. `breath-receive-stage.md` already writes `AGND(module)` to survive it. | **HIGH — netlist-blocking** |
| **F8** | tolerance table | The **±50.5 mV / 19.703–20.303 V budget is arithmetically correct and covers only the resistors.** Adding the DAC's own specified offset, gain and INL roughly **doubles** worst-case zero error to **±115 mV**. | MEDIUM |
| **F9** | `U-DAC` | `C-DECOUPLE` books "DAC8568 AVDD+**DVDD** = 2". **The DAC8568 has no DVDD** — one supply pin. The count of 2 is right only if the second cap is the **100 nF on `VREFIN/VREFOUT`** that SBAS430E requires. | MEDIUM — right answer, wrong reason |
| **F10** | lines 104–259 | The italic parenthetical opened `*(` at line 104 **is never closed**. 46 lines — including the page's only numeric budget — render inside a run-on aside. | LOW — but it hides F8 |

Plus: **ADR 0006's own table calls Mod 1–4 "Trimmed" and `ROADMAP.md` E10 books
"Four mod channels trimmed", and there is no mod trimmer anywhere in
`bom.csv`.** (F16, below.)

---

## 1. The transfer function, end to end

### 1.1 The algebra

Two-resistor non-inverting form, reference at the bottom of the feedback
divider `[repo hardware/module/mod-channels.md:19-46]`:

```
Vout = (1 + R2/R1)·Vdac − (R2/R1)·V_ref
     = (1 + k)·Vdac − k·V_ref              k = R2/R1
```

`R1` = 10 kΩ, `R2` = 30 kΩ `[repo hardware/bom.csv:67 R-MODGAIN]` → `k = 3`,
gain `1 + k` = **4 exactly**, intercept `k·V_ref`.

**`V_ref` should be written `10/3 V`, not `3.3333 V`.** The page's own target
is an intercept of exactly 10.000 V, which requires `V_ref = 10/3 =
3.333333… V`. `3.3333 V` gives an intercept of 9.99990 V — a 100 µV error,
harmless, but it is a *rounded* figure presented as an exact one, and the
executable model should carry the fraction. `[calc: 3 × 3.3333 = 9.99990;
3 × 10/3 = 10.000000]`

**CONFIRMED.** The form, the ratio, the gain and the intercept all check out.

### 1.2 Is 3.3333 V reachable on channel 7? — YES, at code 43691

SBAS430E Equation 1 `[datasheet SBAS430E p.30, Figure 120 and Eq. 1]`:

```
VOUT = VREF × Gain × D_IN / 2^n        Gain = 1 for A/B, 2 for C/D
```

Internal reference 2.500 V `[datasheet SBAS430E p.4, "REFERENCE OUTPUT,
Output voltage, TA = +25°C, all grades: 2.4975 / 2.5 / 2.5025 V"]`, C grade →
Gain 2 → **full-scale asymptote 5.000 V**, LSB = 5.000/65536 = **76.2939 µV**
`[calc]`.

```
D_ideal = 65536 × (10/3) / 5 = 65536 × 2/3 = 43690.667
```

| Code | `V_ref` | Error | Intercept `3·V_ref` | Jack offset error |
|---|---|---|---|---|
| 43690 | 3.333282 V | −50.9 µV | 9.999847 V | +152.7 µV |
| **43691** | **3.333359 V** | **+25.4 µV** | **10.000076 V** | **−76.3 µV** |

**Write 43691 (0xAAAB).** It is 66.67 % of full scale, so nothing about
reachability is marginal — and it sits comfortably inside ADR 0006's
0.25–4.75 V pitch-channel reserve window as well, which removes a reader's
likely objection before it is raised. `[calc, from datasheet SBAS430E p.30
Eq. 1]`

The −76 µV of jack offset it leaves is **0.25 LSB** and 1/660th of the
resistor tolerance term. Nothing to do.

> **`0xAAAB` is a pleasant mnemonic for 2/3 of full scale and should go on the
> page**, because a reader reaching for "3.3333 V" on a meter has no way to
> know which of the two adjacent codes was meant.

### 1.3 The endpoints are not exactly ±10.000 V, and cannot be

Two separate reasons, neither of them the resistors:

**(a) Code 65535 is one LSB short of the 5.000 V asymptote.** `D_IN` ranges
0…65535 `[datasheet SBAS430E p.30, "It can range from … 0 to 65535 for
DAC8568 (16 bit)"]`, so the top code gives 4.999924 V, and

```
Vout(65535) = 4 × 4.999924 − 10.000076 = +9.999620 V     [calc]
Vout(0)     = 4 × 0        − 10.000076 = −10.000076 V    [calc]
```

The window is **asymmetric by one output LSB, 305 µV**. Irrelevant in
service, wrong in a simulation that asserts symmetry.

**(b) The DAC's own specified errors are ~100× larger than that.**
`[datasheet SBAS430E p.3, STATIC PERFORMANCE]`

| Term | Typ | Max |
|---|---|---|
| Zero-code error (all '0's) | 1 mV | **4 mV** |
| Full-scale error (all '1's) | ±0.03 % FSR | **±0.2 % FSR = ±10 mV** |
| Offset error | ±1 mV | ±4 mV |
| Gain error | ±0.01 % FSR | ±0.15 % FSR |
| Relative accuracy (INL) | ±4 LSB | ±12 LSB = ±0.92 mV |

So, before a single resistor tolerance:

```
Vout at code 0      = −10.000 V  …  −9.984 V        [calc: 4 × (0…4 mV)]
Vout at code 65535  =  +9.960 V  … +10.040 V        [calc: 4 × (4.990…5.010 V)]
```

**RECOMMENDATION.** Replace "**exactly ±10.000 V**" (lines 70, 81, and the
`bom.csv:67` `R-MODGAIN` row) with "**±10.000 V nominal**". The word "exactly"
is doing rhetorical work in a comparison against the superseded four-resistor
version, and it is the kind of claim a bench measurement at E7 will contradict
by 40 mV and cause somebody to hunt for a fault that is not there.

### 1.4 Resolution — confirmed, with one arithmetic slip in ADR 0006

```
1 LSB at the jack = 4 × 76.2939 µV = 305.18 µV        [calc]
```

ADR 0006 `[repo docs/decisions/0006-cv-channel-allocation.md, "The cost"]`:
"Resolution goes from 153 µV/LSB on a 10 V span to **305 µV/LSB** on 20 V"
— **both confirmed** `[calc: 10/65536 = 152.59 µV; 20/65536 = 305.18 µV]`.

"**That is 0.003 % of full scale**" — **wrong, and wrong in an instructive
way.** One LSB of a 16-bit converter is 1/65536 = **0.00153 %** of span, for
*every* span. The fraction cannot change with the range; that is what "16-bit"
means. The sentence computes 305 µV against 10 V while having just said
"on 20 V". `[calc]`

The conclusion ("irrelevant against anything a modulation CV drives") is
unaffected and correct — see §3.4, where the DAC's own noise floor is shown to
be 0.066 LSB rms.

---

## 2. The DAC grade — and it is thinner than the page thinks

### 2.1 `4X − 3X = X` — confirmed, and the page is right to be worried

`[calc]` For any uniform reset state `X` on all channels including ch 7:
`Vout = 4X − 3X = X`. The four-resistor form gave `4X − 4X = 0` for any `X`.
The page's central safety claim is **correct**.

### 2.2 But the grade→jack map is stated wrong

`[datasheet SBAS430E p.38, "POWER-ON RESET TO ZERO SCALE OR MIDSCALE"]`
verbatim: *"For device grades A and C on power-up, all DAC registers are
filled with zeros and the output voltages of all DAC channels are set to zero
scale. For device grades B and D all DAC registers are set to have all DAC
channels power up in midscale."*

`[datasheet SBAS430E p.30, Eq. 1]` Gain = 1 for A/B, 2 for C/D. Therefore
midscale is **not the same voltage on B as on D**:

| Grade | Gain | FS | Power-on `X` | **Mod jacks at power-on** |
|---|---|---|---|---|
| A | 1 | 2.500 V | zero scale, 0 V | **0 V** — safe |
| **B** | 1 | 2.500 V | midscale, **1.250 V** | **+1.250 V** |
| **C** *(specified)* | 2 | 5.000 V | zero scale, 0 V | **0 V** — safe |
| **D** | 2 | 5.000 V | midscale, **2.500 V** | **+2.500 V** |

**`mod-channels.md:188` and ADR 0006 both say "a B or D part would put
+2.5 V on all four jacks". That is true of D and false of B by a factor of
two.** `[calc from datasheet SBAS430E p.30 Eq. 1 and p.38]`

This is not pedantry about a part nobody will order. It is the *only* worked
example of the `4X − 3X = X` hazard anywhere in the corpus, it appears in two
files, and it is the sentence a future reader will use to decide whether some
other uniform state is safe. Getting `X` from the grade requires reading the
gain *and* the reset state together, and the corpus reads only the reset state.

**Note also that A is mod-safe.** A is rejected for the pitch channel and the
reference gain (ADR 0006), not for this. The page's "the grade lock is now
load-bearing twice" would be more precisely "**the grade lock excludes B and D
for this reason, and A for the other one**".

### 2.3 The `CLR` pin does NOT clear by grade — it clears by register

**This is the most important finding in the section.**

`[datasheet SBAS430E p.40, "CLEAR CODE REGISTER and CLR PIN"]` verbatim:
*"Bringing the CLR pin low clears the content of all DAC registers and all DAC
buffers, and replaces the code with the code determined by the clear code
register."* Table 13 gives four settings via feature bits F1/F0:

| F1 F0 | Clear code | Uniform `X` (C grade) | **All four mod jacks** |
|---|---|---|---|
| **0 0** | zero scale **(default)** | 0 V | **0 V** — this is the design |
| 0 1 | midscale | 2.500 V | **+2.500 V** |
| 1 0 | **full scale** | 4.999924 V | **+4.99992 V** |
| 1 1 | **ignore external `CLR` pin** | — | `LK-CLR` does nothing |

`[calc from datasheet SBAS430E p.30 Eq. 1 and p.40 Table 13]`

So the page's sentence —

> "On a `CLR`, the C-grade DAC8568 (the grade is **locked** — it selects reference
> gain as well as reset state, ADR 0006) clears **every** channel to zero
> scale (ADR 0006)."

— attributes to the **grade** a behaviour that is set by a **firmware-writable
register**. The grade governs *power-on reset*. The `CLR` pin governs nothing
by itself; the clear code register does.

The corpus knows this in exactly one place: `bom.csv:68` (`R-CLR-PU`) says
*"Leave the DAC's clear-code register at its default so a manual CLR still
parks at zero scale. Do NOT write ClearIgnore"*, and `firmware/README.md:72`
names the clear-code register among the write-once registers that must be
refreshed. **Neither `mod-channels.md` nor ADR 0006 mentions it** — and
`mod-channels.md` is, by its own closing line, *"the page someone will read
while stuffing the board"*, and by §"The offset is a DAC channel" the page
where the safe-clear argument is supposed to live in full.

This is the project's named failure mode verbatim: the fix landed in the BOM
row where the editing was happening, and not on the page where the argument
is made.

**RECOMMENDATION — add to `mod-channels.md`, in the `CLR` section:**

> **Two registers, not one, make this safe.** The *grade* fixes the
> **power-on** state (C → zero scale, `[datasheet SBAS430E p.38]`). The
> **clear code register** fixes what the `CLR` *pin* does, independently of
> grade, and it defaults to zero scale `[datasheet SBAS430E p.40, Table 13]`.
> Writing `ClearMidscale` puts **+2.5 V** on all four jacks; writing
> `ClearFullScale` puts **+5.0 V**; writing `ClearIgnore` makes `LK-CLR`
> inert and silently deletes the bring-up path `R-CLR-PU` exists to provide.
> Firmware refreshes this register (`firmware/README.md`) and must never write
> any value but `00`.

A `ClearFullScale` write is a **two-bit firmware typo that puts +5 V on four
CV outputs and holds it there with no `MISO` to notice** — strictly worse than
the B/D hazard the page does warn about, and one that a correct BOM cannot
prevent.

*(One relieving detail: `[datasheet SBAS430E p.40, "SOFTWARE RESET FUNCTION"]`
— "When performing a software reset of the device, the clear code register is
set back to its default mode (DB1 = DB0 = '0')". A software reset is therefore
a recovery path from a bad clear code. Worth recording; it is the only one.)*

### 2.4 Rider 1 — the AVDD floor. Confirmed, and it should be 5.10 V not 5.00 V

`[datasheet SBAS430E p.4, REFERENCE section]`: *"VREFIN Reference input range:
Grades A/B, AVDD = 2.7 V to 5.5 V → 0 to AVDD; **Grades C/D, AVDD = 5.0 V to
5.5 V → 0 to AVDD/2**"*.

`[datasheet SBAS430E p.3, OUTPUT CHARACTERISTICS]`: *"Output voltage range
0 to AVDD. AVDD ≥ 2.7 V; grades A and B: maximum output voltage 2.5 V when
using internal reference. **AVDD ≥ 5 V; grades C and D: maximum output voltage
5 V when using internal reference.**"*

**The ADR's and `bom.csv`'s "the C grade is specified only for AVDD 5.0–5.5 V"
is a fair reading, but it is assembled from two different rows** — the
`VREFIN` row carries the explicit 5.0–5.5 V window; the output-range row
carries `AVDD ≥ 5 V`. The global EC header is *"At AVDD = 2.7 V to 5.5 V"*
`[p.3]` with no grade split. A reviewer who greps for a single "C grade:
5.0–5.5 V" row will not find one and may conclude the corpus invented it. It
did not; cite both rows.

**The floor should be higher than 5.00 V for this stage.** Full scale is
5.000 V *from the reference at gain 2, independent of AVDD* — `ROADMAP.md:196`
already says this and it is right. What AVDD buys is **output-buffer
headroom**. At AVDD selected to exactly 5.00 V, the top codes of every channel
sit **at the rail**, and the mod channel's `+10 V` endpoint is precisely the
top code. The DAC's output amplifier is rail-to-rail but not rail-reaching
under load, and each `DAC_MODn` pin carries `R-BIAS-DAC` (50 µA at 5 V).

```
AVDD 5.21 V nominal → 210 mV of headroom above the 5.000 V asymptote   [calc]
AVDD 5.00 V         →   0 mV — top codes compress                      [calc]
```

**RECOMMENDATION.** Keep `5.00 V` as the absolute in-spec floor (it is), and
add a **selection floor of 5.10 V** to the E7 step and to
`config/figures.yaml`'s `dac-rail` entry, so the bench step has ≥100 mV of
buffer headroom. E7 already measures "where the top codes start compressing"
`[repo ROADMAP.md:196]`; this just gives that measurement a number to beat.
Without it, an E7 selection of exactly 5.00 V is *in spec* and *breaks the
+10 V endpoint*, which is the worst combination.

### 2.5 Rider 2 — external `VREFIN` ≤ AVDD/2 on C/D. Confirmed, not binding

`[datasheet SBAS430E p.4]`, quoted above. Internal reference is used
`[repo docs/decisions/0006-cv-channel-allocation.md]`, so this forecloses only
a future external-reference retrofit above **2.605 V** (AVDD/2 at 5.21 V), not
~2.6 V-and-something-vague. `[calc: 5.21/2 = 2.605]` A 2.5 V external part
(REF5025 class) fits; a 5.0 V one (`REF5050`, which the project already
stocks for the carrier) **does not**, which is the retrofit somebody would
actually reach for. Worth saying plainly.

### 2.6 One more grade-adjacent item the corpus has right

`[datasheet SBAS430E p.4, REFERENCE OUTPUT]`: output voltage temperature drift
is **grade-dependent** — A/B 5 typ / 25 max ppm/°C, **C/D 2 typ / 5 max**.
`bom.csv:12` states this. **Confirmed.** It matters here more than the corpus
says — see §3.5, where the reference drift is shown to be a pure *gain* term
with **zero** offset contribution.

---

## 3. Impedance, loading and crosstalk

### 3.1 What each output presents — and the page does not say

The feedback tap `R2` is taken at the **op-amp output**
`[repo hardware/module/mod-channels.md:33-37]`, not at the jack. `R-OUT-PROT`
1 kΩ is therefore **outside the loop**. (Pitch is the opposite — `C-FB-PITCH`'s
row records *"with the tap at the jack"* `[repo hardware/bom.csv:112]`.)

Closed-loop output impedance at `MODn_DRV`, noise gain 4 so β = 1/4:

```
Z_out,cl(f) = Z_O(f) / (1 + β·A_OL(f))
```

with `Z_O` = **375 Ω** plateau, 100 Hz–300 kHz `[datasheet SBOS737C p.8 and
p.10, "ZO Open-loop output impedance | f = 1 MHz, IO = 0 A, See Figure 26 |
375 | Ω"; Figure 26 p.16 digitised in datasheets/MANIFEST.csv]`, and
`A_OL` = 143 dB typ / **120 dB min** at RL = 10 kΩ, **110 dB min over
temperature** `[datasheet SBOS737C p.7, OPEN-LOOP GAIN]`, rolling off at
GBW = 10 MHz `[datasheet SBOS737C p.8]`.

| f | `A_OL` | `Z_out,cl` at `MODn_DRV` | at `MODn_JACK` |
|---|---|---|---|
| DC (110 dB min) | 3.16e5 | **13 mΩ** | 1.000 kΩ |
| 2 kHz | 5 000 | 0.30 Ω | 1.000 kΩ |
| 20 kHz | 500 | 2.98 Ω | 1.003 kΩ |
| 2.5 MHz (crossover) | 4 | ~100 Ω | 1.10 kΩ |

`[calc from datasheet SBOS737C p.7-8,10 and the Figure 26 digitisation]`

**So the jack presents a flat 1.00 kΩ from DC to past 1 MHz.** That is the
Eurorack convention and it is a genuine virtue of *not* taking jack-side
feedback: the source impedance does not peak near crossover, and no cable or
destination capacitance is inside a loop. **The page should claim this; it is
one of the two real advantages the mod topology has over pitch** (the other is
§3.6).

### 3.2 F1 — what a load actually does. This is the finding.

```
V_jack = α · (4·Vdac − 3·V_ref)        α = R_L / (R_L + 1 kΩ)      [calc]
```

| Destination | `α` | **Error at +10 V** | vs the page's whole ±50.5 mV budget |
|---|---|---|---|
| open / meter | 1.0000 | 0 | — |
| 100 kΩ (common Eurorack CV in) | 0.99010 | **−99.0 mV** | **2.0×** |
| 2 × 100 kΩ (passive mult) | 0.98039 | **−196 mV** | 3.9× |
| 3 × 100 kΩ | 0.97087 | **−291 mV** | 5.8× |
| 4 × 100 kΩ | 0.96154 | **−385 mV** | 7.6× |
| 20 kΩ | 0.95238 | **−476 mV** | 9.4× |
| **1 kΩ** | **0.5000** | **−5.000 V** | 99× |

`[calc]`

**The page spends 30 lines defending a ±50.5 mV zero point and ±1.5 % span,
and the first thing anybody plugs into the jack costs 1 % of span
deterministically.** That is not a design error — 1 kΩ out is exactly what
Mutable, Make Noise and everything else in the rack do, and ADR 0006's
"linear and repeatable, not calibrated" tolerates it easily. It is a
**documentation** error, because the page's headline number is unloaded and
does not say so, and because the tolerance section invites a reader to believe
the ±50.5 mV is the dominant term. It is the *fourth* largest term.

**Two things the page should say, and one is genuinely good news:**

1. **The zero is load-invariant.** Because the offset is subtracted *before*
   `R-OUT-PROT`, `α` scales both terms identically, so `V_jack = 0` whenever
   `Vout = 0` for **any** load. `[calc: α·(4·Vdac − 3·V_ref) = 0 ⟺
   4·Vdac = 3·V_ref, independent of α]` A load can never shift the mod
   channels' zero crossing — only their span. This is exactly the property
   pitch could *not* have (a load there moves the whole −2…+7 V line, which is
   why pitch took jack-side feedback), and it is why the mods are correct to
   have left it alone. **The page should claim this instead of "exactly
   ±10.000 V".**

2. **State the loaded transfer function** as the headline, with the unloaded
   one as the `R_L → ∞` case. The executable model needs `α` as a parameter or
   it will silently model a meter.

**Do not "fix" this by shrinking `R-OUT-PROT`.** Its 1 kΩ is what holds the
back-powering current to 7.6 mA/jack and is the only part in the module at
real risk from a jack fault `[repo hardware/bom.csv:42, 52]`. Jack-side
feedback would fix the divider and cost the flat output impedance, the
absence of a compensation cap (§3.6), and a stability argument that pitch
needed three reviews to settle.

### 3.3 F1b — the reconstruction corner moves with the load too

`C-FILT-MOD` 82 nF sits at the jack, so the impedance charging it is
`1 kΩ ‖ R_L`, not 1 kΩ:

| Destination | corner | at 400 Hz | at the 3.6 kHz ZOH image |
|---|---|---|---|
| open | **1.941 kHz** | −0.18 dB | −6.5 dB |
| 100 kΩ | 1.960 kHz | −0.18 dB | −6.5 dB |
| 20 kΩ | 2.038 kHz | −0.17 dB | −6.3 dB |
| 1 kΩ | 3.881 kHz | −0.05 dB | −2.6 dB |

`[calc: f = 1/(2π·(1k‖R_L)·82n); 1/(2π·1000·82e-9) = 1940.7 Hz]`

**`1k × 82nF = 1.94 kHz` confirmed** `[repo hardware/bom.csv:66]`. Signal loss
at 400 Hz is negligible as claimed. Total image rejection at 4 kHz update is
**−25.7 dB** (ZOH's own −19.2 dB `[repo docs/decisions/0006…]` plus −6.5 dB
here) `[calc]` — a number neither the ADR nor this page states, and the one a
reader wants.

### 3.4 Crosstalk through the shared reference buffer — quantified, and the
brief's premise is confirmed

**The mechanism the page never states.** Each channel's `R1` runs from
`VREF_MOD` to that channel's `(−)` node, which its own loop holds at `Vdac_n`.
So the current each channel draws from the shared reference is
**signal-dependent**:

```
i_n = (V_ref − Vdac_n) / 10 kΩ                                        [calc]

  Vdac = 0     (Vout = −10 V):  +333.3 µA   (buffer sources)
  Vdac = 2.5   (Vout =   0 V):   +83.3 µA
  Vdac = 3.333 (Vout = +3.33 V):      0
  Vdac = 5     (Vout = +10 V):  −166.7 µA   (buffer SINKS)
```

Total across four channels: **+1.333 mA** sourcing (all four at −10 V) to
**−0.667 mA** sinking (all four at +10 V). Against ±65 mA `I_SC`
`[datasheet SBOS737C p.8]` this is nothing, but note the buffer **reverses
direction** over the range, which the page's "1 mA, comfortable for the part"
does not hint at and a simulation must model.

**Crosstalk.** A full-scale step on one channel is `Δi = 5 V / 10 kΩ =
500 µA`. It lands on `VREF_MOD` through `Z_out,cl` of the follower (β = 1),
and every channel — including the aggressor — sees it multiplied by `−k = −3`:

| f | `A_OL` | `Z_O` | `Z_out,cl` | `ΔV_ref` | **at `MODn_DRV` (×3)** | after the 1.94 kHz RC |
|---|---|---|---|---|---|---|
| DC | 110 dB min | 3.26 kΩ | 10.3 mΩ | 5.2 µV | **15.5 µV** | 15.5 µV |
| 2 kHz | 5 000 | 375 Ω | 75.0 mΩ | 37.5 µV | **113 µV** | 80 µV |
| **35 kHz** *(DAC settling edge, 0.35/10 µs)* | 286 | 375 Ω | 1.31 Ω | 656 µV | **1.97 mV** | **109 µV** |
| all four stepping together | — | — | — | ×4 | 7.9 mV | 437 µV |

`[calc from datasheet SBOS737C p.7-8,10 (A_OL, GBW, Z_O) and the Figure 26
digitisation in datasheets/MANIFEST.csv; DAC settling 5 µs typ / 10 µs max
from datasheet SBAS430E p.3]`

**The brief's premise is confirmed and its conclusion is not what one would
expect.** Every one of these numbers is **4.95× larger** than the same
calculation at the corpus's back-solved 75.8 Ω `[calc: 375/75.8 = 4.947]`.
And **every one is still under one 305 µV LSB at the jack.** The 375 Ω
correction is real, it moves this by 5×, and it changes no decision on this
page. That is worth writing down explicitly, because the `opa2197-output-impedance`
figure's note says *"EVERY POLE DERIVED FROM 75.8 OHM MOVES BY ~5x IN THE
WRONG DIRECTION … Not recomputed yet"* `[repo config/figures.yaml]` — for the
mod channels, **it is now recomputed and it is benign**. One fewer open item.

**The single-buffer argument survives.** `mod-channels.md:205-208` argues one
shared buffer is better because "a residual appears as a common shift across
the mod set rather than as four channels disagreeing". The mechanism above
**confirms** this: `ΔV_ref` reaches all four channels identically and
simultaneously. **Verified, keep.**

**⚠ WARNING — do NOT propagate the carrier's `R-ISO-REF` fix to this buffer.**
`config/figures.yaml`'s `riso-ref-topology` is a live dispute about the
carrier's OPA2197 reference buffer, and TI's own worked answer for that
circuit is `R_ISO` = 37.4 Ω `[datasheet SBOS737C section 8.2.3 p.30,
Figure 56]`. **This buffer must not get one.** Its load is *purely resistive*
— 2.5 kΩ (four 10 kΩ to driven nodes) plus ~20 pF of trace, against a part
that drives 1 nF unaided `[datasheet SBOS737C p.1 Features and section 7.3.5
p.22]`. It is unconditionally stable as drawn. An out-of-loop 10 Ω here would
multiply the shared-impedance crosstalk by **133×** (10 Ω against 75 mΩ),
turning 113 µV into **15 mV — 49 LSB, and the largest error on the page.**
`[calc: 500 µA × 10 Ω × 3 = 15.0 mV]`

Two pages describe what looks like the same circuit. One needs a series
resistor and one is destroyed by it. Say so on both.

### 3.5 Two crosstalk paths the page should also carry

**(a) Inside the DAC.** `[datasheet SBAS430E p.3]` *"Channel-to-channel dc
crosstalk, full-scale swing on adjacent channel: **0.1 LSB**"* and
*"Channel-to-channel ac crosstalk, RL = 2 kΩ, CL = 420 pF, 1 kHz full-scale
sine wave: **−109 dB**"*.

```
0.1 LSB = 7.63 µV at the DAC pin                                     [calc]
  onto a signal channel  → ×4 = 30.5 µV at the jack   (0.10 LSB)
  onto channel 7         → ×3 = 22.9 µV on ALL FOUR   (0.08 LSB)
  five aggressors on ch 7 → 0.5 LSB = 38 µV → 114 µV common shift    [calc]
AC: −109 dB on a 5 Vpp aggressor = 17.8 µVpp → ×4 = 71 µV            [calc]
```

Comparable to the shared-buffer path and equally negligible. **Worth stating
precisely because it is the term a reader will assume dominates.**

**(b) The reference cancels, and nobody has noticed.** Both terms of
`Vout = 4·Vdac − 3·V_ref` are proportional to the *same* internal `V_REF`:

```
Vout = 2·V_REF · (4·D_n − 3·43691) / 65536                            [calc]
```

so reference error, drift and noise are a **pure gain error with exactly zero
offset contribution** — they vanish identically at `Vout = 0` and are largest
at the endpoints. With the C grade's 5 ppm/°C max `[datasheet SBAS430E p.4]`:

```
10 °C × 5 ppm/°C × 10 V = 500 µV at full output, 0 V at the zero point  [calc]
```

1.6 LSB at ±10 V, nothing at 0 V, against a resistor term of ±150 mV. The
0.1–10 Hz reference noise of 12 µVpp `[datasheet SBAS430E p.4]` is 4.8 ppm →
**48 µVpp at ±10 V**. `[calc]`

**This is a second, independent reason the offset belongs on a DAC channel**,
and it is stronger than the corpus's version. ADR 0006 currently says the
drift argument "is a wash" because "both routes track the same reference". It
is not a wash — it is a **cancellation**, and only because the offset comes
from the same converter. A fixed 3.3333 V from a separate reference part would
put that part's full drift straight into the intercept with no cancellation
at all. **Upgrade the ADR's bullet from "a wash" to "cancels".**

### 3.6 No compensation capacitor is needed, and that is not an accident

The op-amp sees `R2` (30 kΩ) in parallel with `R-OUT-PROT` (1 kΩ) —
**resistive at every frequency**, because the 82 nF is behind the 1 kΩ. Plus
`D-JACK-CLAMP` BAV99 junction capacitance, a few pF. The OPA2197 drives 1 nF
bare `[datasheet SBOS737C p.1, section 7.3.5 p.22]`; it sees ~5 pF.

Pitch needed `C-FB-PITCH` 2.2 nF and three reviews to get it right
`[repo hardware/bom.csv:112]`. **The mod channels need nothing, and the page
should say why — otherwise the next reader "completes" the drawing by adding
a feedback cap.** `bom.csv:66` already carries the other half of this warning
(*"ON THE JACK SIDE of R-OUT-PROT, never the op-amp side — inside the loop it
is a capacitive load and the stage can oscillate"*); the page carries neither.

### 3.7 Settling — the output filter dominates, by 90×

| Stage | Time |
|---|---|
| DAC settling, ¼→¾ scale, ±0.024 %, unloaded | **5 µs typ / 10 µs max** `[datasheet SBAS430E p.3]` |
| DAC slew rate | 0.75 V/µs typ `[datasheet SBAS430E p.30]` |
| Op-amp slew, 20 V full-scale step, G = 4 | **1.0 µs** `[calc, at SR 20 V/µs, datasheet SBOS737C p.8]` |
| Op-amp small-signal settling to 0.01 % | 1.4 µs `[datasheet SBOS737C p.8]` |
| **`R-OUT-PROT` × `C-FILT-MOD`, 20 V step to 1 LSB** | **910 µs** `[calc: τ = 82 µs, 82 × ln(20/305e-6) = 910 µs]` |

**The jack never settles between updates** at a 250 µs loop pass — which is
correct, because that RC *is* the reconstruction filter and is doing its job,
but it means a simulation that steps the code and reads the jack after one
pass will read 95 %, not 100 %. State it.

`[datasheet SBOS737C p.8]` note: 20 V/µs is specified at `VS = ±18 V`; the
low-supply table (`VS = ±3 V`) gives 14 V/µs. At ±11.2 V the true figure is
between; **take 14 V/µs for the model** and the full-scale slew becomes 1.4 µs.
Still 600× inside the RC.

### 3.8 Glitch — 0.4 nV-s becomes 4.9 µV at the jack

`[datasheet SBAS430E p.3]`: code-change glitch impulse **0.1 nV-s** (1 LSB
change around major carry), digital feedthrough **0.1 nV-s**, power-on glitch
impulse **10 mV** at RL = 2 kΩ, CL = 470 pF, AVDD = 5.5 V.

```
0.1 nV-s × gain 4 = 0.4 nV-s at MODn_DRV
through τ = 82 µs:  peak ≈ 0.4e-9 / 82e-6 = 4.9 µV = 0.016 LSB       [calc]
power-on glitch:    10 mV × 4 = 40 mV at all four jacks              [calc]
```

Note the mod stage **amplifies** the DAC glitch by 4 before filtering it,
where pitch attenuates it first (`C-AA-PITCH` 10 nF ahead of the stage,
`[repo hardware/bom.csv:118]`). The mod channels have **no** anti-alias cap on
the `R-OPAMP-IN` node. At 4.9 µV that is the right call and costs nothing —
but it is an asymmetry between two adjacent pages that looks like an omission,
and one line closes it.

The 40 mV power-on glitch on four jacks is real and is the only power-on
transient in this stage. Under a ~50 ms rail ramp it is inaudible. Record it
so E10 does not discover it.

### 3.9 Noise — the DAC dominates by 8×

| Source | at `MODn_DRV` |
|---|---|
| **DAC channel, 90 nV/√Hz at zero code `[datasheet SBAS430E p.4]` × 4** | **360 nV/√Hz** |
| `R1`‖`R2` thermal, 10 k and 30 k | 44.6 nV/√Hz `[calc]` |
| OPA2197 `e_n` 5.5 nV/√Hz `[datasheet SBOS737C p.7]` × noise gain 4 | 22.0 nV/√Hz |
| Reference buffer `e_n` × 3 (common to all four) | 16.5 nV/√Hz |
| **RSS** | **364 nV/√Hz** |

```
ENB of the 1.94 kHz pole = 1.571 × 1940.7 = 3049 Hz                   [calc]
e_out = 364 nV/√Hz × √3049 = 20.1 µV rms = 0.066 LSB                  [calc]
```

Plus 0.1–10 Hz: DAC 2.6 µVpp `[datasheet SBAS430E p.4]` ×4 = 10.4 µVpp,
OPA2197 1.30 µVpp `[datasheet SBOS737C]` ×4 = 5.2 µVpp → ~12 µVpp `[calc]`.

**The analog stage contributes 12 % of the noise power.** The 1 % resistors
and the OPA2197 are not the limit and never will be — which is one more
independent confirmation of ADR 0006's "channels 2–6 run on ordinary 1 %
discretes".

---

## 4. Current draw for this section

Five OPA2197 halves (four channels + the reference follower) and five of the
DAC's eight channels.

### 4.1 Quiescent

`I_Q` = 1 mA typ / 1.3 mA max at 25 °C / **1.5 mA max over temperature**, **per
amplifier** `[datasheet SBOS737C p.8, POWER SUPPLY]`. Quiescent current flows
rail-to-rail, so it loads **+12 V and −12 V equally**.

```
5 halves × 1.0 mA typ = 5.0 mA      on each of ±12V_A               [calc]
5 halves × 1.5 mA max = 7.5 mA      on each of ±12V_A               [calc]
```

`U-DAC` `I_DD`, normal mode, **internal reference switched on**, AVDD
3.6–5.5 V: **1.25 mA typ / 2.0 mA max** `[datasheet SBAS430E p.5, POWER
REQUIREMENTS]`, whole chip, footnote (7) *"Input code = midscale, no load"* —
so output load current is **extra**. Internal reference consumption 360 µA at
AVDD 5.5 V is included in that figure `[datasheet SBAS430E p.4]`.

### 4.2 Signal current

Per channel, `R2` feedback: `(Vout − Vdac)/30 kΩ` → 167 µA at +10 V (sourced),
333 µA at −10 V (sunk) `[calc]`.
Reference buffer into the four `R1`: +1.333 mA to −0.667 mA (§3.4).
`R-BIAS-DAC` on each DAC pin: `Vdac/100 kΩ`, ≤50 µA `[repo hardware/bom.csv:128]`.

### 4.3 Totals

| Case | **+12V_A** | **−12V_A** | **AVDD (5.21 V)** |
|---|---|---|---|
| All four at 0 V, jacks open | 5.3 mA | 5.0 mA | 1.4 mA |
| All four at 0 V, 100 kΩ loads | 5.3 mA | 5.0 mA | 1.4 mA |
| All four at **+10 V** into 100 kΩ | **6.1 mA** | 5.7 mA | 1.5 mA |
| All four at **−10 V** into 100 kΩ | 5.0 mA | **7.1 mA** | 1.3 mA |
| All four at +10 V into **1 kΩ** | **26.4 mA** | 5.7 mA | 1.5 mA |
| **All four jacks shorted to ground** | **51.9 mA** | 5.7 mA | 1.5 mA |
| Worst case over temperature, add | +2.5 mA | +2.5 mA | +0.8 mA |

`[calc]` Derivations for the two that matter:

```
+10 V into 100 kΩ:  5.0 (IQ) + 4×0.167 (R2) + 4×[10/(1k+100k)] = 6.06 mA
                     −12 V rail carries IQ 5.0 + ref buffer sink 0.667 = 5.67 mA
+10 V into 1 kΩ:    5.0 + 0.667 + 4×(0.167 + 10/2k) = 26.4 mA
all four shorted:   op-amp drives 1 kΩ, rails at ~11.4 V → 11.4 mA each
                     5.0 + 0.667 + 4×(0.167 + 11.4) = 51.9 mA
```

**AVDD attribution:** this section is 5 of the DAC's 6 populated channels. The
whole-chip 1.25 mA typ / 2.0 mA max plus ≤0.23 mA of `R-BIAS-DAC` gives
**≈1.5 mA typ / 2.3 mA max on the 5.21 V rail**, against the
`~13 mA` the `U-REG-DAC` row books including the divider
`[repo hardware/bom.csv:38]`. **Consistent, with margin.** No change needed.

### 4.4 Thermal — comfortable, but check the package pairing

`R_θJA` for the **dual** OPA2197 in SOIC-8 is **107.9 °C/W** `[datasheet
SBOS737C section 6.5 p.6 — the single OPA197 table on the same page says
115.8 and is the wrong row]`. Thermal shutdown puts the output high-Z above
**140 °C** junction `[datasheet SBOS737C section 7.3.4 p.22]`.

Worst case, one package with both halves driving shorted jacks:

```
P = 2 × [24 V × 1.3 mA + (12 − 11.4) V × 11.4 mA] = 2 × 38.0 = 76.0 mW  [calc]
ΔT_j = 76.0 mW × 107.9 °C/W = 8.2 °C                                     [calc]
```

Nowhere near. **But** `[datasheet SBOS737C p.7, footnote]`: *"For OPA2197,
OPA4197: When driving high current loads on multiple channels, make sure the
junction temperature does not exceed 125 °C."* The footnote exists because
both halves heating together is the case people miss. Here it costs 8 °C.
Record the number so nobody re-derives it.

### 4.5 Headroom — the "±11.45 V" figure is from memory and is optimistic

`mod-channels.md:107-108`: *"an OPA2197 on ±12 V less two Schottky drops
reaches ~±11.45 V, so ±10.05 V has 1.4 V of margin"*. ADR 0006 says the same
with 1.45 V. **`[from memory]` — neither number is in SBOS737C, and the
topology claim is wrong.**

**Topology.** Each analog rail passes through **one** Schottky, not two: `+12V
→ D1 1N5817 → FB1`, `−12V → D3 1N5817 → FB3`
`[repo hardware/module/power-entry.md:12-48]`. "Two Schottky drops" reads as
two in series and is not what is built.

**Rail.** Module analog draw is ~25–30 mA (10 OPA2197 halves + INA828 + the
LM317 branch) `[calc from hardware/bom.csv:13,27,38,43]`, so `V_f` is well
below the 0.24 V-at-245 mA point of the banked curve
`[repo config/figures.yaml diode-split-rationale, digitised from
datasheets/discrete-and-power/1N5817.pdf Fig. 2 — extrapolated below the
digitised range, flag as such]`; take ~0.20 V.

```
Rack +12.00 V nominal → 11.80 V analog rail                            [calc]
Rack +11.40 V (−5 %)  → 11.20 V analog rail                            [calc]
```

Neither the page nor the ADR books the rack's ±5 %, which
`docs/decisions/0005-power-architecture.md:95` does book.

**Swing from rail** `[datasheet SBOS737C p.8, OUTPUT]`: no load 5 mV typ /
25 max; **RL = 10 kΩ: 95 typ / 125 max**; **RL = 2 kΩ: 430 typ / 500 max**.

| Rack | Destination | op-amp load | Swing limit | **Margin over +10 V** |
|---|---|---|---|---|
| 12.00 V | open / 100 kΩ | 23 kΩ | **+11.68 V** | 1.68 V |
| 12.00 V | 2 kΩ | 1.88 kΩ | +11.37 V | 1.37 V |
| **11.40 V** | open / 100 kΩ | 23 kΩ | **+11.08 V** | 1.08 V |
| **11.40 V** | **1 kΩ** | 0.97 kΩ | **≈ +10.3 V** | **≈ 0.3 V** |

`[calc; the 1 kΩ row is EXTRAPOLATED — SBOS737C's lightest tabulated load is
2 kΩ. Back-solving an output-stage R_on from the 2 kΩ row (430 mV/5.75 mA =
74.8 Ω typ, 500 mV/5.75 mA = 87.0 Ω max) and re-solving at 0.97 kΩ gives
10.40 V typ / 10.28 V max. Mark it [calc, extrapolated], not [datasheet].]`

**The margin is 1.7 V at nominal-and-unloaded and 0.3 V at the two worst
corners together.** It never goes negative, so nothing is broken — but "1.4 V
of margin" is a single number standing in for a 1.4 V range, and this page is
about to be simulated.

**RECOMMENDATION.** Replace the single figure with the corner table, or at
minimum change "reaches ~±11.45 V" to "reaches ±11.1 V at the rack's −5 %
corner, more when lightly loaded". And in the firmware-failure story
(`mod-channels.md:181`, `firmware/README.md:56,68`) replace "≈ **+11.45 V**"
with "**over +11 V**" — the argument needs a direction, not a decimal, and
three files currently carry a decimal that no document supports.

---

## 5. The two open items — both answerable now

### 5.1 "Whether all four channels need the full ±10 V"

**ANSWER: yes. Close it as decided, not deferred, and record the arithmetic so
it does not re-open.**

The page's own framing is slightly off: going unipolar 0–10 V would not
"halve their resolution cost" — it would **improve** resolution from 305 µV to
153 µV/LSB `[calc]`. So the question is really "is 305 µV/LSB on a bipolar
channel ever a problem?" Answer:

| Against | 305 µV LSB is |
|---|---|
| The channel's own noise floor, 20.1 µV rms ≈ 132 µV pp (§3.9) | 2.3× — **quantisation is already the floor and would stay so** |
| A 100 kΩ destination's load error, 99 mV (§3.2) | **1/325th** |
| The resistor tolerance term, ±150 mV span (§6) | **1/490th** |
| ADR 0006's own acceptance, "nobody's ear cares whether a modulation CV is 2 % off" | 0.0015 % |

**One extra bit of a quantity already 300× below the dominant error term buys
nothing.** `[calc]`

What it *costs* is the decision ADR 0006 actually made. Two unipolar channels
would need a different `k`, so `R-MODGAIN` stops being eight parts of two
values off one reel; two of the four channels stop sharing `VREF_MOD`; and the
four channels stop being interchangeable — which is the whole content of
"generic rather than fixed-function". **The cost is genericity and BOM
uniformity; the benefit is zero.**

*(Note the safety argument does **not** apply. A unipolar `Vout = 2·Vdac`
stage is also `CLR`-safe. Do not use safety to close this item; use the
arithmetic above.)*

**Proposed replacement text:**

> - ~~**Whether all four channels need the full ±10 V.**~~ **Closed
>   2026-09-21: yes, all four.** Going unipolar on two would *improve* their
>   resolution to 153 µV/LSB — which is 300× below the load-divider error at
>   the jack and 2× below the channel's own noise floor, so it buys nothing
>   measurable. It costs the property ADR 0006 bought: four interchangeable
>   channels, one shared reference, eight resistors of two values off one
>   reel. E10 cannot change this answer; only a new requirement could.

### 5.2 "Per-channel scale and offset are firmware, not hardware"

**ANSWER: confirmed. Nothing in the hardware changes. One caveat to add.**

The hardware is `V_jack = α·(4·Vdac − 3·V_ref)` — **affine and strictly
monotonic across the full 0…65535 code range** `[calc]`. Every range ADR 0006
names (0–5 V, 0–8 V, 0–10 V, ±5 V, ±2.5 V) is a contiguous code sub-range:

| Firmware range | codes | codes used |
|---|---|---|
| ±10 V | 0 … 65535 | 65536 |
| ±5 V | 16384 … 49152 | 32769 |
| 0–10 V | 32768 … 65535 | 32768 |
| 0–8 V | 32768 … 59392 | 26625 |
| ±2.5 V | 24576 … 40960 | 16385 |

`[calc: D = 65536 × (V_target/4 + 3·V_ref/4) / 5]`

Firmware has complete scale and offset authority within the window, and the
only thing it cannot do is exceed ±10 V, which nothing asks for. **Confirm and
close.**

**The caveat worth adding**, because it is the one thing firmware genuinely
cannot do: `α` (§3.2) depends on what is plugged in, firmware cannot see it,
and there is no readback. So **per-destination calibration is impossible by
construction** — which is fine, and is exactly why ADR 0006 says these
channels are *"linear and repeatable, not calibrated"*. Saying it out loud
stops a future reader proposing an output-scaling table that cannot work.

---

## 6. Re-marking every figure on the page

The page carries **zero provenance markers**. CLAUDE.md §3 asks for provenance
on every figure. Here is the full set.

| Figure (line) | Was | Verdict | Re-marked |
|---|---|---|---|
| `V_ref` = 3.3333 V (6, 101) | unmarked | **rounded** — should be 10/3 V, code 43691 | `[datasheet SBAS430E p.30 Eq.1]` + `[calc]` |
| `R1` 10 k / `R2` 30 k, `k = 3` (99-100) | unmarked | ✅ | `[repo hardware/bom.csv:67]` |
| gain `1 + k` = 4 exactly (100) | unmarked | ✅ `[calc]` | `[calc]` |
| intercept `k·V_ref` = 10.000 V (101) | unmarked | ✅ at 10/3; 9.99990 at 3.3333 | `[calc]` |
| "exactly ±10.000 V" (70, 81) | unmarked | ⚠ **unloaded and nominal only** (§1.3, §3.2) | `[calc, unloaded, ideal DAC]` |
| `k = A − 1`, `V_ref = offset/(A−1)` (57) | unmarked | ✅ identity | `[calc]` |
| **"~1.3 mA total into 4 × 10 k" (22)** | unmarked | ⚠ **right value, wrong model** — true only at `Vdac = 0`; see §3.4 | `[calc]` + restate |
| **"At 2.5 V into 2.5 kΩ that is 1 mA" (199)** | unmarked | ❌ **STALE VALUE + wrong model** | see F4 |
| `C-FILT-MOD` 82 nF → 1.94 kHz (102) | unmarked | ✅ 1940.7 Hz `[calc]`; moves with load (§3.3) | `[calc]` |
| ±50.5 mV zero (128) | unmarked | ✅ **exact** `[calc]`, incomplete (§6.1) | `[calc]` |
| 19.703–20.303 V span (129) | unmarked | ✅ **exact** `[calc]` | `[calc]` |
| −1.49 %/+1.52 % (129) | unmarked | ✅ `[calc: −1.485/+1.515]` | `[calc]` |
| "±18 cents per octave" (132) | unmarked | ✅ `[calc: 1.515 % × 1 V / 0.8333 mV = 18.2 ¢]` | `[calc]` |
| "1.6× better", "1.33× better" (128-129) | unmarked | not re-derived — describes a superseded topology | `[repo, historical]` |
| "−196 mV zero error", "+9.657 V" (82, 112) | unmarked | not re-derived — superseded four-resistor form | `[repo, historical]` |
| "OPA2197 … reaches ~±11.45 V" (108) | unmarked | ❌ **`[from memory]`, topology claim wrong** (§4.5) | replace with the corner table |
| "±10.05 V has 1.4 V of margin" (108) | unmarked | ⚠ 1.68 V nominal, 0.3 V at both worst corners | `[calc]` |
| "**±10.05 V** uses the DAC's full 0–5 V span" (146) | unmarked | ❌ **STALE** — the design is ±10.000 V (F11) | must be fixed |
| "`4 × 0 − 3 × 3.3333` = −10.00 V" (176) | unmarked | ✅ `[calc]` | `[calc]` |
| "`4 × Vdac` ≈ +11.45 V" (182) | unmarked | ⚠ over +11 V; the decimal is unsupported | `[calc]` |
| "**a B/D part would put +2.5 V**" (188) | unmarked | ❌ **B gives +1.250 V** (F3, §2.2) | `[datasheet SBAS430E p.30, p.38]` |
| "C-grade … clears every channel to zero scale" (156) | unmarked | ❌ **that is the clear-code register, not the grade** (F2, §2.3) | `[datasheet SBAS430E p.40 Table 13]` |
| "`CLR` … the DAC's own power-on reset" (160-162) | unmarked | ✅ **verbatim confirmed** | `[datasheet SBAS430E p.38]` |
| `Vout = −4·Vdac + 5·V+`, `V+` = 2.000 V (218-220) | unmarked | ✅ self-consistent `[calc]`; see F15 | `[calc]` |
| "`Vout = 5 × 2.0` = +10 V" (232) | unmarked | ✅ `[calc]` | `[calc]` |
| "four of four published designs" (85-87, 211-215) | unmarked | not re-verifiable from banked documents | `[from memory / prior-art survey]` |
| "Winterbloom Sol … 1.190 V" (ADR 0006) | unmarked | not re-verifiable from banked documents | `[from memory]` |
| `R-OPAMP-IN` "costs nothing" on a (+) input (73-75) | unmarked | ✅ `I_B` = ±5 pA → 5 pV across 1 kΩ | `[datasheet SBOS737C p.7]` |

### 6.1 The tolerance budget is exact, and covers one of four error sources

**Re-derived from scratch and confirmed.** `[calc]`

```
Vout(2.5) = (1+k)·2.5 − k·(10/3) = 2.5 − 0.83333·k
d/dk = −0.83333
k_max = 3 × 1.01/0.99 = 3.06061     k_min = 3 × 0.99/1.01 = 2.94059
Δk = ±0.06061   →   zero error = ∓50.5 mV                        ✅ EXACT
span = 5(1+k):  k_max → 20.303 V    k_min → 19.703 V             ✅ EXACT
```

The page's "four corners, two of which cancel in the ratio" reasoning is also
**correct** — only the *ratio* matters, so `+1 %/+1 %` and `−1 %/−1 %` give
exactly `k = 3`.

**What it omits.** From `[datasheet SBAS430E p.3]`:

| Term | Worst case at the zero point | Common to all four? |
|---|---|---|
| Resistor ratio (the page's number) | **±50.5 mV** | no |
| Channel 7: gain ±0.15 % FSR at ⅔ scale + offset 4 mV + INL 0.92 mV, ×3 | **±29.8 mV** | **yes** |
| Signal channel: gain ±0.15 % FSR at ½ scale + offset 4 mV + INL 0.92 mV, ×4 | **±34.7 mV** | no |
| Code-43691 quantisation, ×3 | ±0.08 mV | yes |
| **Worst-case sum** | **±115 mV** | |
| **RSS** | **±68 mV** | |

`[calc from datasheet SBAS430E p.3 STATIC PERFORMANCE]`

**The page's ±50.5 mV is 44 % of the worst-case zero error, not all of it.**
And span acquires another ±40 mV from the DAC's ±0.2 % full-scale error
`[calc: ±0.2 % × 5 V × 4]`, negligible against the resistors' ±300 mV.

This does not change any decision — ±115 mV on ±10 V is 0.58 %, against
ADR 0006's stated 2 % tolerance. But the page's tolerance section has
*already been wrong twice by its own account* and is about to be simulated
from. **Label it "resistor network only" or complete it.** Given the history,
complete it.

**And the useful structural fact the table reveals:** ±29.8 mV of the total is
**common to all four channels** (it comes from channel 7). That is the
"residual appears as a common shift across the mod set" property the
single-buffer section claims — **now quantified for the first time: 26 % of
worst-case zero error is common-mode, and the single-buffer argument is
correct.** `[calc]`

---

## 7. Netlist readiness

### 7.1 F5 — `R-BIAS-DAC` is missing from the drawing

`bom.csv:128` specifies 100 kΩ 1 %, **qty 6**, *"AT THE DAC PIN, not after
`R-OPAMP-IN` — 100 k after the 1 k would form a divider and cost 1 % of gain.
Without it the op-amp (+) inputs have no DC path to ground: their only
connection is a DAC pin that may be high-Z before power-on reset, so outputs
can sit at either rail during that window."*

**Five of those six instances are on this page** (four mods + channel 7). The
drawing at lines 19–46 shows neither. So does the drawing's `R-OPAMP-IN`,
which appears only as an unlabelled `[1k]`.

This matters beyond tidiness: **`R-BIAS-DAC` is what makes the AVDD-up-first
and ±12 V-up-first orderings both benign.** With ±12 V present and AVDD
absent, it holds every `(+)` input and `VREF_MOD` at 0 V, so all four jacks sit
at `4×0 − 3×0 = 0 V` `[calc]`. Without it they are undefined. The page's
entire safe-state argument has a silent dependency on a part it does not draw.

**Also confirmed as correct and worth a line:** the DAC pin drives
`R-BIAS-DAC` (100 kΩ) through its own 4 Ω DC output impedance
`[datasheet SBAS430E p.3, "DC output impedance, at mid-code input: 4 Ω"]`, a
gain error of 4/100000 = **0.004 %** = 200 µV at 5 V → **800 µV at the jack**
`[calc]`. 2.6 LSB, 190× under the resistor term. Fine — but it is the reason
`R-BIAS-DAC` must stay at 100 kΩ and not drop to 10 kΩ.

### 7.2 F6 — the channel numbering has no mapping to silicon

The corpus says "DAC ch 2–5", "channel 7". The DAC8568's outputs are named
`VOUT-A` … `VOUT-H`. **No file in `hardware/**`, `docs/decisions/**`,
`firmware/**` or `config/**` states the mapping** `[repo, exhaustive grep]`.
A netlist cannot be written from "channel 7".

TSSOP-16 (PW) pinout `[datasheet SBAS430E p.6, PIN CONFIGURATIONS, read from
the rendered page — the PDF text layer scrambles the pin order]`:

```
  ┌─────∪─────┐
  │ 1 LDAC    16 SCLK │      1  LDAC            16  SCLK
  │ 2 SYNC    15 DIN  │      2  SYNC            15  DIN
  │ 3 AVDD    14 GND  │      3  AVDD            14  GND
  │ 4 VOUT-A  13 VOUT-B      4  VOUT-A          13  VOUT-B
  │ 5 VOUT-C  12 VOUT-D      5  VOUT-C          12  VOUT-D
  │ 6 VOUT-E  11 VOUT-F      6  VOUT-E          11  VOUT-F
  │ 7 VOUT-G  10 VOUT-H      7  VOUT-G          10  VOUT-H
  │ 8 VREFIN/VREFOUT   9 CLR │  8 VREFIN/VREFOUT  9  CLR
  └───────────┘
```

**PROPOSED — the least-surprising mapping, 1→A … 8→H:**

| Corpus name | Pin | DAC output | Net |
|---|---|---|---|
| channel 1, pitch | 4 | `VOUT-A` | `DAC_PITCH` |
| channel 2, mod 1 | 13 | `VOUT-B` | `DAC_MOD1` |
| channel 3, mod 2 | 5 | `VOUT-C` | `DAC_MOD2` |
| channel 4, mod 3 | 12 | `VOUT-D` | `DAC_MOD3` |
| channel 5, mod 4 | 6 | `VOUT-E` | `DAC_MOD4` |
| channel 6, **spare** | 11 | `VOUT-F` | *(no net)* |
| **channel 7, mod offset** | **7** | **`VOUT-G`** | `DAC_MODREF` |
| channel 8, **spare** | 10 | `VOUT-H` | *(no net)* |

It has a memorable self-check: **channel 7 is `VOUT-G` on pin 7.**

> **A layout alternative the author may prefer, offered because nothing is
> committed yet.** `VOUT-B/D/F/H` are pins 13/12/11/10 — **four adjacent pins
> on one side**. Putting mod 1–4 there (with pitch on `A`/pin 4, the offset on
> `G`/pin 7, spares `C` and `E`) gets the four identical channels, their four
> `R-OPAMP-IN`, their four `R-BIAS-DAC` and their two op-amp packages onto one
> edge of the DAC, and keeps pitch and the offset — the two channels with
> different downstream treatment — on the other. It is strictly better for
> routing and it breaks the tidy 1→A mapping. **Either is fine; neither is
> written down, which is the defect.** Pick one and state it in ADR 0006's
> allocation table as a third column.

Firmware also needs the `A3..A0` address field → channel map
`[datasheet SBAS430E p.34 Tables 8–10 and p.35-37 Table 11 — read the rendered
tables; the PDF text layer loses the address column]`. Out of this slice, but
it is the same unstated mapping one layer up.

### 7.3 F7 — `AGND` is two nets

`mod-channels.md:43` uses bare `AGND` for the **module analog return**
(`C-FILT-MOD`'s far end). The umbilical's pin 2 is also called `AGND` and is
**an in-amp input, not a ground** — `docs/decisions/0004-cv-interface-module.md:611`
is explicit: *"`AGND`, from the etherCON | **Nothing.** It is an in-amp input,
not a ground"*, and `:630` *"`AGND` is not in this list. It terminates at the
in-amp's IN+…"*.

`breath-receive-stage.md` already writes **`AGND(module)`** eight times to
survive the collision `[repo hardware/module/breath-receive-stage.md:39-70]` —
which is a netlister-hostile workaround and direct evidence the collision is
felt today. A parenthetical qualifier is not a net name.

**PROPOSED:**

| Today | Proposed | What it is |
|---|---|---|
| `AGND` / `AGND(module)` | **`AGND_M`** | module analog return, star at the IDC ground pin |
| `AGND` (umbilical pin 2) | **`BREATH_RTN`** | the in-amp's sense conductor. **Carries signal, not return current.** |

`BREATH_RTN` over `AGND_SENSE` because the goal is to stop a reader seeing the
letters `GND` on a conductor that is an amplifier input — which is the mistake
the name has been inviting for three review waves.

*(Three grounds exist and are correctly distinguished elsewhere — `PWR_GND`,
`DIG_GND`, `AGND` `[repo hardware/module/breath-receive-stage.md:45]`. The
collision is only between `AGND` and the umbilical conductor. Note also that
`dig-gnd-topology` is an open dispute in `config/figures.yaml`; renaming
`AGND` does not touch it.)*

### 7.4 Proposed net and refdes names for this page

**Nets, per channel `n` ∈ {1,2,3,4}:**

| Net | From | To |
|---|---|---|
| `DAC_MODn` | `U-DAC` `VOUT-x` | `R-OPAMP-IN`, `R-BIAS-DAC` |
| `MODn_IN` | `R-OPAMP-IN` | op-amp `(+)` |
| `MODn_SUM` | `R-MODGAINnA` / `R-MODGAINnB` junction | op-amp `(−)` |
| `MODn_DRV` | op-amp out | `R-MODGAINnB`, `D-JACK-CLAMP`, `R-OUT-PROT` |
| `MODn_JACK` | `R-OUT-PROT` | `C-FILT-MOD`, jack tip |

**Shared:**

| Net | From | To |
|---|---|---|
| `DAC_MODREF` | `U-DAC` `VOUT-G` (pin 7) | `R-OPAMP-IN`, `R-BIAS-DAC` |
| `MODREF_IN` | `R-OPAMP-IN` | follower `(+)` |
| **`VREF_MOD`** | follower out **and** follower `(−)` | four × `R-MODGAINnA` |
| `+12V_A` / `-12V_A` | `power-entry.md` D1/FB1, D3/FB3 | op-amp rails, `D-JACK-CLAMP` |
| `AGND_M` | analog star | `C-FILT-MOD` ×4, `R-BIAS-DAC` ×5, jack sleeves |

`power-entry.md` currently labels these rails **"MODULE ANALOG +12V"** and
**"MODULE ANALOG −12V"** `[repo hardware/module/power-entry.md:15,49]` — a
description, not a net name. `+12V_A`/`-12V_A` or `VA+`/`VA-`; pick one and
put it in both places.

**Refdes.** The page calls the resistors `R1` and `R2`, which exist in no BOM
and collide with `breath-receive-stage.md`'s `R1b`. `bom.csv` has one row,
`R-MODGAIN` qty 8. For a netlist each instance needs a designator:

```
R-MODGAIN1A … R-MODGAIN4A   10 kΩ 1 %   VREF_MOD → MODn_SUM
R-MODGAIN1B … R-MODGAIN4B   30 kΩ 1 %   MODn_SUM → MODn_DRV
```

Eight, matching the row. `tools/check-staleness.py` validates duplicate
refdes; these are new and unique `[repo tools/check-staleness.py, per
CLAUDE.md]`.

**Op-amp halves.** `bom.csv:13` books six OPA2197 packages, twelve halves, ten
used, but **no page assigns halves to packages**. This section uses five.

> **PROPOSED, and it is not arbitrary.** `U-OPA-MOD-A` = mod 1 + mod 2;
> `U-OPA-MOD-B` = mod 3 + mod 4; and put the **mod reference follower in the
> same package as the `VREFOUT` follower**, not with a mod channel. Two quiet
> unity-gain followers share a die; pairing the reference with a channel that
> can drive 11 mA into a shorted jack puts that channel's 8 °C of self-heating
> (§4.4) straight into the reference follower's `V_OS` drift
> (±0.5 µV/°C typ, **±2.5 µV/°C max** `[datasheet SBOS737C p.7]`) — which is
> ×3 onto **all four** jacks at once. It is 60 µV worst case `[calc: 8 °C ×
> 2.5 µV/°C × 3]` and therefore not urgent; it is free to avoid, and it is the
> kind of pairing nobody revisits after layout.

### 7.5 F9 — `C-DECOUPLE` books a pin the DAC8568 does not have

`bom.csv:43`: *"6 × OPA2197 on ±12 V = 12, INA828 = 2, **DAC8568 AVDD+DVDD =
2**, …"*.

**The DAC8568 in TSSOP-16 has one supply pin: `AVDD`, pin 3. There is no
`DVDD`.** `[datasheet SBAS430E p.6, PIN CONFIGURATIONS and PIN DESCRIPTIONS —
16 pins: LDAC, SYNC, AVDD, VOUT-A/C/E/G, VREFIN/VREFOUT, CLR, VOUT-H/F/D/B,
GND, DIN, SCLK]`

The **count of 2 is correct** — but only if the second capacitor is the one TI
actually requires: `[datasheet SBAS430E p.31, INTERNAL REFERENCE]` *"A minimum
100 nF capacitor is recommended between the reference output and GND for noise
filtering."*

So the right reading of that row is **`AVDD` + `VREFIN/VREFOUT`**, not
`AVDD + DVDD`. As written, a reader who checks the pinout finds no `DVDD`,
"corrects" the count to 1, and deletes the reference capacitor — on the node
that feeds **both** the pitch stage's `VREFOUT` follower and, through every
channel including channel 7, this entire page.

**This is a right answer with a wrong reason, which per CLAUDE.md is the
dangerous kind**: it will not be re-checked because the number is correct.

Note also `mod-channels.md` does not draw `C-REF` either. For netlist
readiness the `VREFIN/VREFOUT` node (pin 8) needs a name — propose
**`VREFOUT_DAC`** — and its 100 nF needs a refdes distinct from `C-DECOUPLE`,
because it is a reference filter and not a supply bypass, and the distinction
is exactly what got lost.

### 7.6 Netlist checklist for this page

- [ ] Draw `R-BIAS-DAC` ×5 and label `R-OPAMP-IN` ×5 (F5)
- [ ] State the channel→`VOUT-x`→pin mapping (F6)
- [ ] Rename `AGND` → `AGND_M`; umbilical `AGND` → `BREATH_RTN` (F7)
- [ ] Per-instance refdes `R-MODGAIN1A`…`4B` (§7.4)
- [ ] Assign op-amp halves to packages (§7.4)
- [ ] Name the rails `+12V_A`/`-12V_A` here and in `power-entry.md` (§7.4)
- [ ] Add `VREFOUT_DAC` + its required 100 nF (F9)
- [ ] State `R-OUT-PROT`'s value **and its 0.66–1 W rating** on this page — the
      Values table omits the part entirely, and `bom.csv:42` calls it *"the
      ONLY part in the module at real risk from any jack fault"*
- [ ] Give the jack sleeve a net (`AGND_M`) — the drawing floats it

---

## 8. Remaining findings

**F11 — line 146 is stale.** *"**On the range:** ±10.05 V uses the DAC's
*full* 0–5 V span."* The design is ±10.000 V; ±10.05 V is the superseded
four-resistor number. Line 108's ±10.05 V is legitimate history (it is
describing the old version); **line 146 is a live claim about the current
design.** `[repo hardware/module/mod-channels.md:146]`
`config/figures.yaml`'s `inamp-full-scale` forbids `"-10.05 V"` and
`"−10.05 V"` — with minus signs — so `±10.05 V` slips through.
**Add `"±10.05 V uses the DAC"` to the `mod-reference` forbidden list.**

**F12 — F4 in detail.** Line 199: *"At **2.5 V** into 2.5 kΩ that is
**1 mA**."* Two errors compounding: 2.5 V is the pre-redraw reference, and the
`4 × 10 kΩ = 2.5 kΩ` model assumes the far end of each `R1` is at ground when
it is at `Vdac` (§3.4). The correct statement is:

> One buffer drives four 10 kΩ legs whose far ends sit at each channel's
> `Vdac`, so its load is **signal-dependent and reverses sign**: from
> **+1.333 mA** sourcing (all four at −10 V) to **−0.667 mA** sinking (all
> four at +10 V), through zero when a channel's `Vdac` passes 3.333 V.
> Against ±65 mA `I_SC` `[datasheet SBOS737C p.8]`, comfortable in both
> directions. `[calc]`

Line 22's *"~1.3 mA total into 4 × 10 k"* reaches the right number by the
wrong route — it is exact only at `Vdac = 0`, where the far ends genuinely are
at 0 V. Keep the number, fix the parenthetical.

**Proposed `config/figures.yaml` addition to `mod-reference`'s `forbidden`:**
`"At 2.5 V into 2.5 k"`, `"2.5 V into 2.5 kΩ"`, `"±10.05 V uses the DAC"`.
These are checker-visible strings for exactly the class of defect the register
exists to catch, and the current list (`"4 x (Vdac - 2.5 V)"`, `"1:4 ratio"`,
`"written once at boot"`) misses all three.

**F13 — F10, the unclosed parenthetical.** `*(` opens at line 104 and no `)*`
follows anywhere to line 259 `[repo, grep]`. Lines 104–149 — the `R-OPAMP-IN`
trap, the **entire tolerance budget**, the "one matching requirement" caveat
and the range paragraph — sit inside an unterminated italic aside. In rendered
Markdown the page's only numeric budget reads as a footnote to a parenthesis
about a deleted resistor. Close it after line 117 (`…decided entirely by the
topology around it.`) and promote the tolerance section to a `###` heading.
This is cosmetic and it is why F8 has gone unnoticed.

**F14 — the page contradicts itself about whether it is settled.** Lines 69
and 83 say the two-resistor form is *"Adopted, and it is drawn above"*. Lines
245–249 say the single-inverting-amp alternative *"is strictly better than
what is drawn above. Not adopted unilaterally"*. A reader who reaches line 247
learns the adopted topology is the worse one and that the decision is open.
`[repo hardware/module/mod-channels.md:69,83,245-249]`

**This is the shape CLAUDE.md §4 names** — an argument surviving next to its
own refutation, invisible to grep. It is not wrong to record the alternative;
it is wrong for the page's Status line to say "Drawn" while its penultimate
paragraph says the drawing should be redone. **Either move §"The alternative
topology" to a dated ADR or a review note, or give it a decision line.**

My own read, offered because the brief asks for proposals: **the alternative
is not strictly better.** It returns one OPA2197 half, and it costs the
load-invariant zero (§3.2) — an inverting stage with the reference on `(+)`
has `Vout = −(Rf/Rin)·Vdac + (1+Rf/Rin)·V+`, and `α` then scales an output
whose zero is at `Vdac = V+·(1+Rf/Rin)/(Rf/Rin)`, which a load *does* shift.
`[calc]` That is a real property to trade away for half an op-amp, and the
page does not price it.

**F15 — one nuance in the `VREFOUT`-divider argument.** Lines 88–92 and
229–236 say a divider off `VREFOUT` *"does **not** go to zero on `CLR`"*.
**True.** But the *power-on* story is different and stronger: `[datasheet
SBAS430E p.31]` *"the internal reference is disconnected from the
VREFIN/VREFOUT pin (3-state output)"* while disabled, and `[p.38]` *"The
internal reference is powered off / down by default and remains that way until
a valid reference-change command is executed."* So at rack power-on a
`VREFOUT` divider reads **0 V**, the jacks sit at 0 V — and then **jump to
+10 V the instant firmware enables the reference**. That is worse than a
standing +10 V, because it is a 10 V step onto four patched outputs at an
arbitrary moment during boot. The conclusion is unchanged and the mechanism is
more damning; say the stronger thing.

**F16 — ADR 0006 and `ROADMAP.md` book a trimmer that does not exist.**
ADR 0006's allocation table gives **Mod 1–4** the Precision value
**"Trimmed"**. `ROADMAP.md:51` (E10) ends *"Four mod channels trimmed"*.
**There is no mod trimmer in `bom.csv`** — `TRIM-OFFSET` is pitch,
`TRIM-BREATH-ZERO` is breath, and that is all `[repo hardware/bom.csv:111,113,
exhaustive grep]`. The same ADR says mods need only be *"linear and
repeatable, not calibrated"* and `mod-channels.md` draws no adjustment
anywhere. Semantic, checker-invisible, in two files, and it will send E10
looking for a screwdriver hole. **`ADR 0006` should read "Fixed" and E10
should read "Four mod channels *verified*".**

**F17 — the `LDAC` cost lands on these four jacks and is not on this page.**
`bom.csv:129` (`R-LDAC`): *"a hardware `LDAC` was considered and declined, and
six channels therefore cannot update atomically — **every exit from `CLR`
throws intermediate values at the mod jacks for 100–200 µs** and no write
order avoids it."*

**No write order avoids intermediate values — but the two orders are not
equally bad, and nobody has said which to use.** `[calc]`

| Firmware writes | Jacks during the window | Peak |
|---|---|---|
| **channel 7 first**, then mods | `4×0 − 3×3.333` | **−10.0 V** — in range, linear |
| **mods first**, then channel 7 | `4×Vdac − 0` | **+11.1 V — op-amps saturated** |

Writing **channel 7 first** keeps the transient inside the specified window
and inside the op-amps' linear region; writing it last drives all four into
the positive rail. Same 100–200 µs, one of them a normal output excursion and
the other a rail event. **`firmware/README.md`'s statelessness rule says
refresh all six every pass but does not order them.** Add: **channel 7 is
written first in every pass.** Free, and it turns a rail event into a ramp.

---

## 9. What I checked and could not settle

- **1N5817 `V_f` at ~30 mA.** The banked digitisation
  `[repo config/figures.yaml diode-split-rationale]` covers 245 mA–3 A. My
  0.20 V is an **extrapolation below the digitised range**, marked as such in
  §4.5. It moves the headroom table by ±0.1 V and no conclusion.
- **OPA2197 swing at `RL` = 1 kΩ.** SBOS737C's lightest tabulated load is
  2 kΩ `[p.8]`. §4.5's 1 kΩ row is back-solved from the 2 kΩ row and marked
  `[calc, extrapolated]`. If the 0.3 V margin matters, measure it at E7.
- **`A3..A0` → DAC channel map.** SBAS430E's Tables 8–11 do not survive text
  extraction; I read the pinout from a render but not the address tables. A
  firmware reviewer should read pp. 34–37 rendered.
- **The prior-art claims** (O&C, PER|FORMER, Yarns, MTM Workshop Computer,
  Winterbloom Sol's 1.190 V). No banked document supports them and I did not
  fetch. They are load-bearing for §"The alternative topology" and remain
  `[from memory]`. F14 does not depend on them.
- **The superseded four-resistor arithmetic** (−196 mV, +9.657 V, "1.6×
  better"). Not re-derived; it describes a topology that no longer exists and
  the page's use of it is historical.

## 10. Corrections I am confident in, ordered by what they cost to ignore

1. **F2** — the `CLR` behaviour is a firmware register, not the grade. A
   two-bit typo puts +5 V on four jacks. `[datasheet SBAS430E p.40 Table 13]`
2. **F5** — `R-BIAS-DAC` missing from the drawing; the safe-state argument
   silently depends on it. `[repo hardware/bom.csv:128]`
3. **F1** — the 1 kΩ output is unbuffered; state the loaded transfer function
   and claim the load-invariant zero instead of "exactly ±10.000 V". `[calc]`
4. **F6/F7** — channel→pin mapping and the `AGND` collision; both block the
   netlist. `[datasheet SBAS430E p.6]`, `[repo docs/decisions/0004…:611,630]`
5. **F3** — B gives +1.250 V, not +2.500 V, in two files.
   `[datasheet SBAS430E p.30, p.38]`
6. **F16** — a trimmer that does not exist, booked in an ADR table and a
   roadmap gate. `[repo hardware/bom.csv, exhaustive]`
7. **F9** — the DAC8568 has no `DVDD`; the right cap count for the wrong
   reason. `[datasheet SBAS430E p.6]`
8. **F4/F11/F12** — two stale numbers the checker cannot see; three new
   `forbidden` strings proposed. `[repo hardware/module/mod-channels.md:146,199]`
9. **§2.4** — raise the E7 AVDD *selection* floor to 5.10 V; 5.00 V is in
   spec and compresses the top codes. `[datasheet SBAS430E p.3]`
10. **F17** — write channel 7 first every pass. `[calc]`

And one thing to stop worrying about: **the 375 Ω correction has been carried
through this stage in full and every crosstalk term stays under one LSB**
(§3.4). `config/figures.yaml`'s `opa2197-output-impedance` note says the
recomputation is outstanding; for the mod channels it is done and the answer
is benign. The carrier's reference buffer is a different circuit with a real
dispute — **and this buffer must not inherit its fix.**
