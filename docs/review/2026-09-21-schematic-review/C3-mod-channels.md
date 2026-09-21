# C3 — Mod channels 1–4

Cold review, 2026-09-21. Subject: `hardware/module/mod-channels.md`, with
`docs/decisions/0006-cv-channel-allocation.md` and the relevant rows of
`hardware/bom.csv`. Reviewer read no prior review or research material.

## Evidence markers

- `[repo]` — read in this repository, file named.
- `[calc]` — arithmetic performed here and shown in full.
- `[from memory]` — general engineering knowledge, no document consulted.
- `[confirm]` — a parameter that **must** come from a datasheet and could not,
  because vendor domains are proxy-blocked. **No claim in this document carries
  a `[datasheet]` marker, because no datasheet was reachable.** Every
  conclusion that depends on a device parameter is gated and says so.

## Severity table

| # | Severity | Finding |
|---|---|---|
| **C3-1** | **Critical** | The page documents **two different circuits**. Diagram and top prose are the two-resistor `k = 3` / 3.3333 V form; the **Values table, the tolerance table, the `CLR` arithmetic and the buffer-load section are the superseded four-resistor 40.2 kΩ / 2.500 V design, unchanged**. Building from the page's own parts table against the page's own diagram gives gain 5.02 and clips both rails. |
| **C3-2** | **Critical** | `hardware/bom.csv` `R-MODGAIN` has **`qty` = 16** while its own note says "EIGHT, not sixteen", and one row carries two different values (10 k and 30 k) with one quantity. The row cannot be ordered from. |
| **C3-3** | **Major** | **The 1 kΩ output resistor is an uncompensated divider against the destination.** −0.99 % into 100 kΩ, −4.76 % into 20 kΩ. This is precisely the error the pitch stage was redrawn *today* to eliminate with jack-side feedback. The mod page does not mention it, and it dominates the V/oct answer the page gives. |
| **C3-4** | **Major** | The tolerance section — the part of the page that presents itself as the rigorous one — reports **the old circuit's numbers**. Correct values for the drawn circuit are **zero ±50.5 mV** (page: ±81 mV) and **span 19.703–20.303 V** (page: 19.70–20.51 V). The page understates its own improvement while appearing exact. |
| **C3-5** | **Major** | `82 nF C0G` is carried on the page with no caveat, while the project's own BOM row for the same part says the package is **probably wrong and unverifiable**. The page is behind the BOM on a part that has no confirmed source. |
| **C3-6** | **Major** | **No defined state on the op-amp (+) inputs or on the shared `V_ref` node** if the DAC is unpowered or high-Z while ±12 V is up. Four jacks indeterminate to the op-amp rails. Needs a pulldown, and its **placement is the whole finding**. |
| **C3-7** | **Moderate** | **Refresh order / `LDAC` is unspecified.** A non-atomic six-channel refresh drives the mod jacks to `4 × Vdac` (clipping, ~+11.5 V) for the duration of every pass if the signal channels land before channel 7. |
| **C3-8** | **Moderate** | `R-OUT-PROT` at 250 mW does **not** survive output-to-output patching, which its own BOM note claims it does: **274 mW** against a 220 Ω output, **493 mW** against a stiff one. |
| **C3-9** | **Moderate** | The buffer-load model is **wrong in kind**, not just in value. The far end of each `R1` sits at `Vdac`, not at ground; the load is bidirectional and signal-dependent (**+1.333 mA to −0.667 mA**), not a static 1 mA. |
| **C3-10** | **Moderate** | **30.000 kΩ is an E24 value and is not in E96.** An exact 3:1 ratio does not exist in E96 at all. "Exactly ±10.000 V" is contingent on a procurement fact the page never states. |
| **C3-11** | **Minor** | "Exactly ±10.000 V" and "Exactly 0 V" on `CLR` are both overclaims: **+9.99969 V** at the top code, and the `CLR` park is **1× the DAC's zero-code error**, where the superseded four-resistor version cancelled it to zero. A small, unstated regression. |
| **C3-12** | **Minor** | The closing "**strictly better**" recommendation for the inverting alternative is not supported, and the page credits the wrong cause for hitting ±10.000 V. |
| **C3-13** | **Minor** | The shared reference is a **single point of failure for four of six jacks**. The page presents the shared node only as an advantage. |
| **C3-14** | **Minor** | "less two Schottky drops" — the mechanism is wrong. One Schottky per rail, and the BAV99 clamps are silicon, to the rails, out of the signal path. |
| **C3-15** | **Minor** | "One matching requirement instead of two" is true by count and misleading in substance. |
| **C3-16** | **Minor** | Cross-document drift: `firmware/README.md` still says 2.5 V; ADR 0006 calls the mods "Trimmed" with no trimmer; `R-PRECISION`'s note claims two spare LT5400 sections can build a 1:3, which is arithmetically impossible. |
| **C3-17** | **Minor** | `10/3 V` is **not exactly representable**. The residual is harmless (76 µV, common to all four), but the page writes a truncated decimal where it should write a code. |
| **C3-18** | **Minor** | Layout note for E9: four 82 nF at the jack field dump **1.64 µC** into AGND on a full-scale step, next to the pitch jack, whose feedback is now tapped at that jack. |

---

# Detail

## The transfer function, re-derived

`[calc]` The (+) input draws no current, so no drop across `R-OPAMP-IN`, and
`V+ = Vdac`. Feedback forces `V− = V+ = Vdac`. The current through `R1` from the
reference node into the summing node is `(V_ref − Vdac)/R1`; the same current
continues through `R2` to the output, so

```
Vout = Vdac − (V_ref − Vdac)·R2/R1
     = Vdac·(1 + R2/R1) − V_ref·(R2/R1)
     = Vdac·(1 + k) − k·V_ref          with k = R2/R1
```

With `R1 = 10 kΩ`, `R2 = 30 kΩ`, `k = 3`, gain `1 + k = 4`:

```
Vout = 4·Vdac − 3·V_ref
```

For `Vout = 4·(Vdac − 2.5)` as ADR 0006 specifies `[repo: 0006]`, we need
`3·V_ref = 10`, so `V_ref = 10/3 = 3.333333… V`. Then

```
Vdac = 0.000 V → −10.000 V
Vdac = 2.500 V →   0.000 V
Vdac = 5.000 V → +10.000 V
```

**The derivation checks out.** The topology, the ratio and the reference value
are mutually consistent, and they reproduce ADR 0006's specified law exactly.
That much of the redraw is right.

### What it actually gives at the DAC's real limits — C3-11

`[repo: bom.csv]` The part is grade-locked to C: reference gain 2, full scale
5.000 V. `[calc]` 16 bits over 5.000 V gives

```
1 LSB = 5 / 65536 = 76.29395 µV
```

The DAC cannot reach 5.000 V. Its top code is 65535, which is one LSB short:

```
Vdac(65535) = 5 × 65535/65536 = 4.99992371 V
Vout        = 4 × 4.99992371 − 10 = +9.99969482 V
```

**305.18 µV short of +10.000 V** — exactly 4 LSB, because the shortfall is
multiplied by the gain. `[calc]`

The bottom end is not 0 V either. Zero-scale output is set by the DAC output
buffer's swing toward ground and by its zero-code error. `[confirm]` DAC8568
**zero-code error** and **output swing to GND under load**, SBAS430. Not
fabricating a number. What can be said without one:

`[calc]` Let `Z` be the DAC's zero-code error, common to both channels (same
die, same output stage). At `CLR` or at a zero-scale reset:

```
Vout = 4·Z − 3·Z = Z
```

So the mod jacks park at **1× the DAC's zero-code error**, not at zero. The
superseded four-resistor difference amp gave `4Z − 4Z = 0` — it cancelled the
term exactly, because both legs had the same gain. **This is a real, small,
unstated regression**, and it makes both the page's "`Vout = 0`" and ADR 0006's
table entry "**Exactly 0 V**" `[repo: 0006]` overclaims. The magnitude is
single-digit millivolts for a part of this class `[from memory]`, so the
practical consequence is nil — but the word "exactly" is load-bearing in a
safe-state argument and should not be used where it is not true.

`[calc]` With the reference at its best available code (see C3-17), the honest
nominal endpoints are **−10.00008 V and +9.99962 V**, before any tolerance.

---

## C3-1 (Critical) — the page describes two circuits

This is the finding that subsumes several others. The redraw was applied to the
diagram and to the top three sections. **Everything from "## Values" down was
left as it was.**

What the page says, in the same document `[repo: mod-channels.md]`:

| Quantity | Diagram + top prose | "Values" table and below |
|---|---|---|
| Topology | two-resistor non-inverting | four-resistor difference amp |
| `R2` | **30 kΩ** (diagram) | **40.2 kΩ** (Values table, twice) |
| `V_ref` | **3.3333 V** (diagram, twice) | **2.500 V** (`V_OFF` row, `CLR` section) |
| Gain | **4** | **4.02** |
| Jack range | **±10.000 V** | **±10.05 V** |
| `CLR` arithmetic | `Vout = 0` | `Vout = 4.02 × (0 − 0) = 0 V` |
| Stale-ch7 rail | — | `4.02 × Vdac ≈ +11.45 V` |
| Tolerance corners | — | "all sixteen corners of four 1 % resistors" |

The page carries a comparison table whose right-hand column says
"**exactly ±10.000 V**" and whose row immediately below is a Values table
saying "Gain 4.02, so the jack reaches **±10.05 V**". Both are bolded. They are
four lines apart.

**This is not cosmetic.** The Values table is the section a person stuffing the
board reads — the page says so itself: *"It is written here because this is the
page someone will read while stuffing the board."* `[repo]` Stuffing 40.2 kΩ
into the drawn two-resistor topology, with the drawn 3.3333 V reference, gives
`[calc]`:

```
k    = 40.2 / 10 = 4.02
gain = 1 + k     = 5.02
Vout = 5.02·Vdac − 4.02 × 3.3333

  Vdac = 0 V → −13.40 V   (clips at the negative rail)
  Vdac = 5 V → +11.70 V   (clips at the positive rail)
```

**Both rails clipped, on all four channels, from a board built exactly as this
page's own parts table specifies.** The two errors do not cancel; they compound,
because the redraw changed the reference in the direction that makes a too-large
`k` worse.

**Action.** Rewrite `## Values`, `## The offset is a DAC channel`, and
`## One buffer, four loads` against the drawn circuit. Delete the "40.2 kΩ
rather than 39 kΩ" paragraph entirely — it argues for a value the circuit no
longer uses, on a gain the circuit no longer has.

*Note in fairness:* every piece of arithmetic in those stale sections is
**correct for the circuit it was written about**. Checked: the −196 mV
`R-OPAMP-IN` error `[calc: a = 40.2/51.2 = 0.785156, b = 4.02,
2.5(a − b(1−a)) = −196.29 mV]` ✓, the +9.657 V endpoint
`[calc: 5 × 0.785156 × 5.02 − 10.05 = +9.6574 V]` ✓, the ±81 mV zero
`[calc, below]` ✓, the 19.70–20.51 V span `[calc, below]` ✓. The defect is
entirely that it is the wrong circuit's arithmetic, presented as this one's.

---

## C3-4 (Major) — tolerance, actually enumerated

The page: *"Enumerating all sixteen corners of four 1 % resistors gives…"*
`[repo]`. **The drawn circuit has two resistors per channel, so there are four
corners, not sixteen.** Here they are.

`[calc]` `k = R2/R1`, `gain = 1 + k`, `zero = Vout(Vdac = 2.5) = 2.5(1+k) − (10/3)k`:

| `R2` | `R1` | `k` | gain | span (0–5 V) | zero error |
|---|---|---|---|---|---|
| 29.7 k | 9.9 k | 3.000000 | 4.000000 | 20.0000 V | 0.00 mV |
| 30.3 k | 10.1 k | 3.000000 | 4.000000 | 20.0000 V | 0.00 mV |
| 29.7 k | 10.1 k | 2.940594 | 3.940594 | 19.7030 V | **+49.50 mV** |
| 30.3 k | 9.9 k | 3.060606 | 4.060606 | 20.3030 V | **−50.51 mV** |

**Worst-case zero error: ±50.5 mV. Worst-case span: 19.703–20.303 V, i.e.
−1.485 % / +1.515 % of gain.**

Two of the four corners are **exactly** nominal, because `k` is a ratio and
same-sign tolerance cancels in it completely. That is a genuine property of the
topology and the page does not mention it.

### Against the four-resistor version it replaced

`[calc]` Sixteen corners of `R1 = R3 = 10 k`, `R2 = R4 = 40.2 k`, `V_ref = 2.5 V`,
with `a = R4/(R3+R4)`, `b = R2/R1`, `gain = a(1+b)`, `zero = 2.5[a − b(1−a)]`:

| | Four-resistor, 40.2 k | **Two-resistor, k = 3** | Change |
|---|---|---|---|
| Worst zero error | −81.38 / +78.81 mV | **−50.51 / +49.50 mV** | **1.6× better** |
| Gain tolerance | −1.980 % / +2.020 % | **−1.485 % / +1.515 %** | **1.33× better** |
| Worst span | 19.702–20.506 V | **19.703–20.303 V** | better at the top |

The page's ±81 mV and 19.70–20.51 V are **reproduced exactly** by this
enumeration — for the four-resistor circuit. They are the old numbers.

**So the page is wrong in the direction of pessimism.** The new topology is
better on both terms, and the page's own table row "±2 % of gain — the dominant
term" understates the redraw's benefit by a third. The corrected figure is
**±1.5 %**, which in the page's own cents units is **±18 cents per octave**,
not ±24 `[calc: 1200 × 0.0152 = 18.2]`.

**Why the gain error shrank**, since the page does not say: the gain is `1 + k`,
and the `1` is exact. A ±2.02 % error in `k` becomes a ±1.51 % error in `1 + k`
because the error is diluted by the unity term. That is a structural advantage
of the non-inverting form and is worth stating in the comparison table, in place
of the number that is there now.

### "One matching requirement instead of two" — C3-15

**True by count, misleading in substance.** `[calc]`

In the four-resistor difference amp, if the two legs match *each other*
(`a = b/(1+b)`) then

```
zero = 2.5[a − b(1−a)] = 2.5[b/(1+b) − b/(1+b)] = 0
```

**exactly, for any value of `b`.** The zero point of a difference amp is
insensitive to the absolute ratio; it depends only on leg-to-leg matching. That
second "matching requirement" was buying something.

The two-resistor form has no such property. Its zero is

```
zero = 2.5 − (10/3)·k
```

— **directly proportional to the error in `k`**, which is the same `k` that sets
the gain. One ratio now does two jobs, and any error in it shows up as a gain
error *and* a correlated offset error.

Net: on independent 1 % discretes the two-resistor form still wins on worst case
(±50.5 vs ±81.4 mV), because two independent tolerances beat four. But the
*structural* insensitivity is gone, and the page's framing — fewer requirements
is simply better — is not the whole story. It matters if anyone later tries to
improve the zero point: in the difference amp a matched quad fixes it exactly;
here a matched quad fixes `k` but leaves the accuracy of `V_ref` fully exposed
at `3×`.

**Action.** Replace the "Matching" row with something like: *"one ratio instead
of two, but that ratio now sets gain and intercept together — the difference
amp's zero was independent of its gain and this one is not."*

---

## C3-10 (Moderate) — 30 kΩ is an E24 value, and "exactly ±10.000" rests on it

`[from memory]` E96 near 30 k: **29.4, 30.1, 30.9**. There is no 30.0.
E24 contains 30 explicitly. `[calc]` More generally, an exact 3:1 ratio requires
`log10(3) × 96 = 45.8` steps of the E96 series — not an integer, so **no pair of
E96 values gives exactly 3:1**. It has to be E24 values, or a series
combination.

1 % chip resistors are stocked in E96 throughout and in E24 only in some
series `[from memory]`. `[confirm]` Whether 30.0 kΩ exists at 1 % in the
intended 0805 thin-film line — every distributor site was proxy-blocked, and the
BOM's own `R-PRECISION` and `C-FILT-MOD` rows carry the same complaint
`[repo: bom.csv]`.

**If it does not, and 30.1 kΩ is substituted** `[calc]`: `k = 3.01`,
`gain = 4.01`. With `V_ref = 10/3`: `Vout(0) = −10.033 V`, `Vout(5) = +10.017 V`.
With `V_ref` retuned to `10/3.01 = 3.32226 V`: `Vout(0) = −10.000 V`,
`Vout(5) = +10.050 V`. **You can pin one endpoint or the other, not both** —
which is exactly the position the 40.2 kΩ version was in, and the page's headline
claim evaporates.

**Better fallback, and arguably better than the nominal design:** make `R2` from
**three 10.0 kΩ resistors in series**, all four parts per channel from one reel.
`[from memory]` 10.0 kΩ is E96, E24, and the most widely stocked 1 % value there
is. The ratio becomes four identical parts from adjacent positions on one reel,
which is the best tracking available without a network, and it removes the
sourcing risk entirely. Cost: sixteen resistors instead of eight — which,
amusingly, is the quantity the BOM row already has (C3-2).

**Note also what actually earns the ±10.000 V**, because the page credits the
wrong thing (see C3-12): `[calc]` a gain of exactly 4 needs `k = 3`, and
`30 k / 10 k` is an exact E24 pair. A gain of exactly 4 in the *inverting*
alternative needs `Rf/Rin = 4`, i.e. 40 kΩ against 10 kΩ — and **40 is in
neither E12, E24 nor E96**. That is why the old design ended up at 40.2 kΩ and
4.02. The ±10.000 V is bought by the `3:1` ratio, not by the resistor count.

---

## C3-17 (Minor) — is 10/3 V representable at 16 bits from 5.000 V?

**No, and it does not matter — but the page writes it in a way that invites a
firmware transcription error.** `[calc]`

```
ideal code = (10/3) / (5/65536) = 655360/15 = 43690.667      (not an integer)
```

| Code | `V_ref` | Error | `ΔVout` = `−3 × error` |
|---|---|---|---|
| 43690 = `0xAAAA` | 3.3332824707 V | −50.86 µV | **+152.6 µV** |
| **43691 = `0xAAAB`** | **3.3333587646 V** | **+25.43 µV** | **−76.3 µV** |

`[calc]` The residual at the best code is **76.3 µV at every output**, against a
per-channel resistor error of **50.5 mV** — a factor of **662**. It is the
smallest term on the page by nearly three orders of magnitude.

**Does it matter across four channels? No, and for exactly the reason the page's
"one shared node" argument gives.** All four channels take the same `V_ref`, so
the residual is a **common** −76 µV shift across the mod set, not four channels
disagreeing. This is the one place where the page's shared-node reasoning is
fully correct and quantitatively supported — it just never supplies the number.

**The real defect is notational.** The page and ADR 0006 both write
"**3.3333 V**" `[repo: mod-channels.md, 0006]` — a truncated decimal. If firmware
transcribes that literal it lands on code 43690 and gets +152.6 µV instead of
−76.3 µV. Still negligible, but the page should specify the **code (43691,
`0xAAAB`)** or the **exact value `10/3 V`**, not a four-digit decimal that is
neither. On a value whose whole justification is that it makes the arithmetic
land exactly, writing it inexactly is a self-inflicted wound.

---

## C3-9 (Moderate) — one follower, four loads: the load model is wrong

The page: *"that half drives four 10 kΩ inputs in parallel. At 2.5 V into 2.5 kΩ
that is **1 mA**, comfortable for the part."* `[repo]`

**Three things wrong.** The 2.5 V is the stale reference (C3-1). More
importantly, **the load is not four 10 kΩ resistors to ground.** The far end of
each `R1` is the channel op-amp's inverting input, which feedback holds at
`Vdac`, not at 0 V. `[calc]`

```
I_n = (V_ref − Vdac_n) / R1 = (3.33333 − Vdac_n) / 10 kΩ
```

| All four channels at | Per channel | Four channels | Follower must |
|---|---|---|---|
| `Vdac = 0` (jacks at −10 V) | +333.3 µA | **+1.333 mA** | **source** |
| `Vdac = 3.333 V` (jacks at +3.33 V) | 0 | **0** | nothing |
| `Vdac = 5 V` (jacks at +10 V) | −166.7 µA | **−0.667 mA** | **sink** |

So the load is **bidirectional and signal-dependent**, swinging over 2 mA as the
four channels move. The follower has to sink as well as source. The diagram's
"~1.3 mA total into 4 × 10k" `[repo]` happens to give the right number for the
all-channels-at-minimum case — but only because at `Vdac = 0` the far ends
*are* at ground. It is the right answer from the wrong model, and it is the only
operating point where the model is accidentally correct.

**Is it a problem? No.** `[confirm]` OPA2197 output current capability and
dissipation, SBOS-series datasheet. 1.3 mA on ±12 V rails is trivial for any
precision op-amp `[from memory]`, and worst-case dissipation in the follower is
`(11.65 − 3.33) × 1.333 mA = 11 mW` `[calc]`. **But the page's stated reason is
wrong, and the sink requirement is invisible in it** — which matters if anyone
later tries to replace the follower with a series reference, a divider, or the
DAC output driving the four `R1`s directly. The last of those would require the
DAC8568's output buffers to sink 0.67 mA near their lower range, which is the
actual reason the buffer exists, and the page never says so.

**Action.** Replace the section's arithmetic with the table above, and state the
sink requirement explicitly as the reason the buffer is not optional.

---

## Crosstalk through the shared node — checked, real, and small

The page says nothing quantitative about this. The analysis, so it exists:

`[calc]` A channel whose DAC changes by `ΔVdac` changes its draw on the shared
node by `ΔVdac / 10 kΩ`. A channel whose output should be *quiet* sees

```
ΔVout(quiet) = −k · ΔV_ref = −3 · (ΣΔVdac / 10 kΩ) · Zout
             = −6 mV per ohm of Zout, for a four-channel full-scale step
```

(four channels × 5 V DAC step = 2.0 mA into the node).

`[from memory]` A follower's closed-loop output impedance is
`Zout(f) ≈ Ro / (1 + A(f))` with `A(f) ≈ GBW/f`. `[confirm]` OPA2197 **GBW** and
**open-loop output resistance**.

| `Zout` | Quiet channel, op-amp output | At the jack, after 1 k/82 n |
|---|---|---|
| 1 mΩ (DC) | 6 µV | 6 µV |
| 0.04 Ω (≈4 kHz, 100 Ω/10 MHz) | 0.24 mV | **0.10 mV** |
| 1 Ω | 6 mV | ~2 mV |

`[calc]` At the 4 kHz refresh rate the jack-side figure is **0.10 mV = 5 ppm of
span = 0.34 LSB**. The conclusion is robust against the gated parameters: even
at `GBW = 1 MHz` the figure is ~1 mV, still twenty times below the ±50.5 mV
resistor term.

**The transient is the interesting case and is also fine.** `[calc]` For the
first `~1/(2π·GBW)` after a DAC step the loop has not responded and `Zout ≈ Ro`.
Taking a pessimistic `Ro = 200 Ω` and a 30 ns recovery gives a ~1.2 V spike at
the quiet channel's op-amp output — but the jack sees it through the 1 kΩ/82 nF,
`τ = 82 µs`, which integrates it:

```
Δv(jack) ≈ (1.2 V × 30 ns) / 82 µs = 0.44 mV
```

**0.44 mV, upper bound.** Below one output LSB × 2. Not a defect.

**Two things that follow, which the page should say:**

1. `[repo: bom.csv]` **No local bypass is specified at the shared `V_ref` node**,
   and the page is silent. Someone stuffing the board will add a 100 nF "because
   references get a 100 nF" — putting a capacitive load straight on a follower's
   output. That is the exact mistake this project's own BOM warns about twice
   (`C-OUT-BREATH`: *"ON THE JACK SIDE … inside the loop it is a capacitive load
   and the stage can oscillate"*; `C-FILT-MOD`: same words). **The page should
   say "no bypass on `V_ref`" explicitly**, or specify one behind a series
   resistor.
2. **Route `V_ref` as a star from the follower's output pin to the four `R1`s**,
   not as a daisy chain. Trace resistance adds directly to `Zout` in the formula
   above — 100 mΩ of shared return between the first and fourth channel is
   0.6 mV of channel-to-channel coupling, six times the figure computed above.

---

## C3-13 (Minor) — the shared node is also a single point of failure

The page: *"**Do not be tempted to split it into four buffers.** One shared node
means all four channels share exactly the same offset error, so a residual
appears as a common shift across the mod set rather than as four channels
disagreeing."* `[repo]`

The argument is correct and C3-17 quantifies it. **But it is one-sided.** The
same node means:

- follower fails, or its `R-OPAMP-IN` opens → `V_ref` floats → **four jacks
  indeterminate**;
- channel 7 written wrong → **four jacks wrong together**, and there is no
  `MISO` to see it `[repo: firmware/README.md]`;
- channel 7 not refreshed → **four jacks at the rail** (the page's own S4 case).

Four of the module's six jacks, on one net, with no readback. The page devotes a
whole section to one of these failure modes and then, two sections later,
presents the shared node as an unalloyed good. **Both belong in the same
paragraph.** `[from memory]` This is a one-off in the author's own rack, so a
single point of failure is an acceptable engineering choice — it is the silence
about it that is the defect.

---

## Safe states: `CLR`, power-on, stale channel 7

### `CLR` — correct in principle, "exactly" is wrong

`[repo: 0006, bom.csv]` The part is grade C: `CLR` takes every channel to zero
scale. `[calc]` `Vout = 4·0 − 3·0 = 0`. ✓ The mechanism is right and the reason
the offset lives on a DAC channel is right.

The overclaim is C3-11: the park is `Z`, the DAC's zero-code error, not zero,
and the four-resistor version cancelled it and this one does not.

### Power-on — C3-6 (Major), an actual gap

`[repo: 0006]` A/C grade power-on-resets to zero scale, and the internal
reference is disabled by default, so the outputs sit at 0 V until firmware
enables it. Good.

**But there is no resistor anywhere from the op-amp (+) input to a defined
potential.** The page's own argument for why `R-OPAMP-IN` is now harmless is
that the (+) input "draws no current" `[repo]` — which is precisely what makes
the node **undriven** the moment the DAC stops driving it. `[repo: bom.csv]`
`R-OPAMP-IN`'s own note says *"DAC on 5.21 V and op-amps on ±12 V do not come up
together."*

`[confirm]` Whether the DAC8568 actively drives its outputs low before the
reference is enabled, or leaves them high-impedance — SBAS430, "power-on reset"
and output stage behaviour with the reference disabled. **This is the gating
question and it is answerable in one datasheet lookup.**

If the outputs are high-Z in that window:

- the four signal (+) nodes float → four outputs indeterminate;
- **and channel 7's input floats too**, so `V_ref` is indeterminate, which
  drives all four through `R1` as well. Both terms undefined simultaneously.

Rails are ±12 V less one Schottky ≈ ±11.65 V `[repo: power-entry.md]`, so the
excursion is up to the op-amp's swing — **~±11.5 V on four jacks** into whatever
is patched.

**Fix, and the placement is the finding:** a **100 kΩ pulldown to AGND at each
DAC output pin, on the DAC side of `R-OPAMP-IN`** — five of them (ch2–ch5 and
ch7), six with pitch.

- **On the DAC side it is free.** `[calc]` The 1 kΩ carries no DC current (the
  (+) input draws none), so the pulldown sees only the DAC's own output
  impedance — a few ohms against 100 kΩ, an error of ~0.005 %.
- **On the op-amp side it would cost 1 %.** `[calc]` 1 kΩ into 100 kΩ to ground
  is a divider of `100/101 = 0.990099`, a **−0.99 % gain error** — the same
  magnitude as the four-resistor `R-OPAMP-IN` trap the page spends a whole
  section on. The page's own lesson applies to its own fix.

**BOM addition:** `R-DAC-PD`, 100 kΩ 1 % 0805, qty 6, at the DAC pins.

### Channel 7 stale or unwritten — the page has this right

`[repo]` `Vout = 4·Vdac`, 0 to +20 V, clipping at the op-amp's positive swing.
Four jacks pinned high, undetectable without `MISO`. Closed by the statelessness
rule `[repo: firmware/README.md]`. **Correct, and correctly identified as the
more likely of the two directions.** The page deserves credit for this section;
it is the best-reasoned part of the document.

Two corrections to it:

- **C3-14.** *"an OPA2197 on ±12 V less two Schottky drops reaches ~±11.45 V"*
  `[repo]`. `[repo: power-entry.md]` There is **one** Schottky per rail
  (`D1`/`D2` on +12, `D3` on −12), and the BAV99 clamps are **silicon**, tied to
  the **rails**, on the driver side — they are not in the signal path and
  subtract nothing. `[repo: bom.csv]` The BOM says "RRIO on ±12 V reaches
  ~11.9 V". The ~±11.45 V figure is defensible (rail ≈ 11.65 V less the RRIO
  output's own headroom) but **the stated mechanism is wrong**, and the same
  wrong sentence appears on `pitch-stage.md` `[repo]`, so it is propagating.
  `[confirm]` OPA2197 output swing from rail vs load, SBOS datasheet.
- **C3-7 (Moderate), which the page does not cover at all.** The stale-channel
  analysis is about a channel not being refreshed. It says nothing about **the
  order within a refresh**. `[calc]` If a pass writes the signal channels before
  channel 7, then between those writes the outputs are at `4 × Vdac` — up to the
  positive clip — for the duration. On a `CLR` recovery at a 4 kHz round-robin
  `[repo: 0006]` that is **up to 250 µs of ~+11.5 V on four jacks, on every
  recovery**. Writing channel 7 **first** makes the transient `−10 V` instead —
  in range, non-clipping, and harmless. Better still: `[from memory]` the
  DAC8568 has an `LDAC` pin; holding it and pulsing it after all six words makes
  the six-channel update **atomic** and removes the transient entirely.
  `[confirm]` `LDAC` behaviour and whether the module's schematic brings it out
  — it is not mentioned on this page or in `firmware/README.md` `[repo]`.
  **Specify one or the other.** This is a one-line firmware rule and a
  one-net hardware question, and it closes a hole in the same class as the S4
  bug the page is celebrating.

---

## C3-5 (Major) — the 82 nF

### The corner is right

`[calc]` `f = 1/(2π × 1000 × 82 nF) = 1940.9 Hz`. The page's 1.94 kHz ✓.
`τ = 82 µs`. At the 3.6 kHz ZOH image ADR 0006 sizes it for `[repo: 0006]`:
`−6.47 dB` `[calc]`, on top of the image's own −19.2 dB.

### Is 82 nF C0G a real part in a sane package?

`[from memory]` C0G/NP0 is a class-I dielectric with low permittivity. Values in
the tens-of-nF range exist only in large cases — 1210 at the small end, more
usually 1812/2220 — and are specialty parts at a dollar or several. 82 nF is an
E12 value and class-I stock thins out sharply at E12 values in that range; 100 nF
C0G in 1210/1812 at 25–50 V is the more commonly stocked neighbour.
`[confirm]` Availability, case size and voltage rating — every distributor was
proxy-blocked.

**The defect is that the page does not say any of this and the BOM does.**
`[repo: bom.csv, C-FILT-MOD]`: *"PACKAGE IS PROBABLY WRONG: 82nF in C0G/NP0
almost certainly does not exist in 0805 … Unverified because every distributor
site was proxy-blocked."* The page says "82 nF C0G" flat, with no package, no
voltage rating and no caveat, in a Values table `[repo]`. **The page is behind
its own BOM on the one part with no confirmed source.**

**Voltage rating is also unspecified and is not a signal question.** `[calc]`
The output reaches −10.202 V worst case, and the jack can be back-driven to
±12 V by a neighbouring module — the cap is the first thing that sees it,
because the clamps are on the far side of the 1 kΩ `[repo]`. **Specify ≥50 V.**

### If it has to be X7R

`[from memory]` X7R is class II: capacitance falls with applied DC bias, and the
fall is severe in small cases at high rated-voltage fractions — order 50–70 % at
10 V on a 16 V 0805, order 10–20 % on a 50 V 1210. `[confirm]` Bias curves are
vendor- and case-specific and were unreachable; these are magnitudes, not
figures.

Three consequences, in increasing order of how much they matter:

1. **The corner moves up.** `[calc]` If `C` halves, `f` goes from 1941 Hz to
   3882 Hz, and the attenuation at the 3.6 kHz image falls from **−6.47 dB to
   −2.70 dB** — you lose about **4 dB of the image rejection the capacitor was
   bought for**, which is the entire reason ADR 0006 gives the mods a slower
   corner than pitch `[repo: 0006]`.
2. **The corner becomes signal-dependent.** The bias here is the *signal
   itself*, ±10 V around zero. So `C` varies over the waveform and **the pole
   moves as the CV moves** — the filter is mildly nonlinear, and a rising edge
   and a falling edge through the same excursion do not have the same shape. On
   an envelope or LFO assignment that is a shape error, not just a bandwidth
   error.
3. **X7R is piezoelectric.** `[from memory]` `[repo: bom.csv, C-FB-PITCH]` This
   project already rejects X7R on exactly this ground: *"C0G, never X7R —
   piezoelectric in a pitch filter is a microphonic detuning element."* A mod
   channel that is *"generic and assignable"* and may drive a VCO has the same
   objection, and the page's own tolerance section says so
   (*"anything pitch-like belongs on channel 1"*) while the BOM leaves X7R open
   as a fallback.

**Recommendation: film, not C0G and not X7R.** `[repo: bom.csv]` The project
already ships a film cap in the identical position — `C-OUT-BREATH`, 330 nF
film, 1206 or THT, *"Film not X7R: DC bias coefficient moves the corner 30 % at
10 V"*. 82 nF/50 V PPS or PET in 1206 or through-hole is cheap, linear,
non-microphonic and unambiguously buyable `[from memory]`. **Use the precedent
the project has already set one page over**, and delete the C0G sourcing risk
rather than carrying it to E9.

---

## Stability with 1 kΩ + 82 nF into a patch cable — sound, and here is why

**Stable, and the page's arrangement is correct.** The reasoning, since the page
does not give it:

`[repo]` Feedback for this stage is taken from the **op-amp output**, upstream of
`R-OUT-PROT`. The 1 kΩ is therefore **outside the loop**, and is a textbook
isolation resistor. The op-amp sees `1 kΩ` in series with everything downstream;
above the frequency where the 82 nF is a low impedance its load is ≈1 kΩ
resistive, and the RC's phase lag never enters the feedback path. Cable
capacitance — `[from memory]` ~100 pF/m, so ~300 pF for a 3 m patch, more on a
passive mult — is likewise beyond the 1 kΩ and cannot reach the loop.

This is the one place the mod channels are **better off than pitch**, and
`pitch-stage.md` says so `[repo]`: pitch moved its DC feedback to the jack to
kill the load divider, which put the RC inside the loop, forced `C-FILT-PITCH`
to be deleted and `C-FB-PITCH` to be added, and left the page calling it *"the
highest-risk item on the page."* The mods pay none of that. **Correct as drawn;
do not change it without reading C3-3 first.**

Two second-order notes:

- The BAV99 sits on the driver side, i.e. *inside* the isolation, so its junction
  capacitance is directly on the op-amp output. `[from memory]` A few pF —
  harmless.
- `[calc]` A full-scale step makes the op-amp charge 82 nF through 1 kΩ at a
  peak of `20 V / 1 kΩ = 20 mA`. That is a real transient — twenty times the
  "1 mA, comfortable" the page's load section discusses — and it happens on
  every gate edge on a mod channel. `[confirm]` OPA2197 output current limit;
  `[from memory]` 20 mA is comfortable for a precision RRIO part of this class,
  and the BOM's per-pin 100 nF decoupling `[repo: bom.csv, C-DECOUPLE]` is the
  right provision. Not a defect, but it is the number the page should have in
  place of 1 mA.

### C3-18 (Minor) — the ground return, for E9

`[calc]` That 20 mA step returns through the 82 nF into AGND **at the jack
field**: `Q = 82 nF × 20 V = 1.64 µC` per edge, per channel, up to four at once.
`[repo: 0006]` A gate assigned to a mod channel makes exactly this step, and
`[repo: power-entry.md]` the ground star point is at power entry, so that current
flows along the jack-field ground toward it — past the pitch jack, whose DC
feedback is now tapped **at the jack** `[repo: pitch-stage.md]` and is therefore
referenced to that node. `[calc]` 80 mA across 20 mΩ of shared return is 1.6 mV
of bounce = **1.9 cents of pitch error**, correlated with mod-channel gate edges.

`[repo: 0006]` This project already treats a 20-cent LED-correlated FM mechanism
as the dominant error in the whole design. This one is an order of magnitude
smaller, but it is the same shape and it is created by a part on this page.
**Add to the E9 measurement list: mod-channel gate edge vs pitch output, and
return the four `C-FILT-MOD` grounds to the jack field separately from the pitch
jack's reference return.**

---

## C3-3 (Major) — the V/oct question, and the thing the page does not mention

The page addresses this and gets an incomplete answer:

> *"On a channel that might be assigned to drive a VCO or a quantiser, ±2 % of
> span is about ±24 cents per octave … anything pitch-like belongs on
> channel 1."* `[repo]`

Two problems. The ±2 % is the old circuit's (C3-4); the correct span tolerance is
±1.5 %, **±18 cents per octave** `[calc]`. And it is **not the largest term**.

### The 1 kΩ is an uncompensated divider

`[repo]` Feedback comes from the op-amp output, so `R-OUT-PROT` divides against
whatever is plugged in. `[calc]`

| Destination `Zin` | Divider | Error | Cents/octave |
|---|---|---|---|
| 100 kΩ (common Eurorack CV input) | 0.990099 | −0.990 % | **−11.9** |
| 50 kΩ (or two 100 kΩ on a passive mult) | 0.980392 | −1.961 % | **−23.5** |
| 20 kΩ | 0.952381 | −4.762 % | **−57.1** |

`[repo: pitch-stage.md]` These are the same numbers the pitch page quotes
(−11.9 and −23.5 cents/octave) as the reason it moved its DC feedback to the
jack. **The mod channels carry that error, unmitigated, and this page does not
mention it once.** After today's pitch redraw, the mods are the only DAC-derived
outputs in the module still paying it.

### Total error, assembled

`[calc]` Worst case into one 100 kΩ VCO input:

| Term | Worst case | Nature |
|---|---|---|
| Resistor span tolerance | −1.485 % … +1.515 % | fixed per unit |
| Output divider, 100 kΩ | −0.990 % | **per destination** |
| **Combined scale** | **−29.5 … +6.1 cents/octave** | |
| Zero error (resistors) | ±50.5 mV = **±60.6 cents** | fixed per unit |
| DAC INL, ±4 LSB | ±1.22 mV = ±1.5 cents | fixed per unit |
| Resolution | 305 µV/LSB = **0.37 cents/LSB** | fine |
| Op-amp `Vos` (×4, plus follower ×3) | <0.3 cents | negligible `[confirm]` |

Over a five-octave range `[calc]`: `5 × (−29.5) − 60.6 = **−208 cents**` worst
case. **Just over two semitones at the top of the range**, and into a 50 kΩ load
it is −41.0 cents/octave, worse still.

**The answer to the question is: about 2 semitones of worst-case error over five
octaves, uncalibrated.** Unusable as a V/oct output as-is.

### What is and is not recoverable

`[repo: 0006, mod-channels.md]` Per-channel scale and offset are firmware,
configured on the instrument's display. So the **fixed per-unit** terms —
resistor span, resistor zero, INL — are all removable by calibration, and
the page's *"linear and repeatable, not calibrated"* framing holds for them.

**The divider term is not.** It changes when you repatch. ADR 0006 bought a
"per-load affine preset, a display page, an operating instruction" for exactly
this on pitch `[repo: pitch-stage.md]` and then deleted it by moving the feedback
to the jack. The mod channels have no such preset. A calibration dialled in for
one VCO is wrong for the next one by up to 45 cents/octave.

### Options, honestly priced

1. **Say it.** Cheapest and mandatory regardless of what else happens. The
   page's output spec should read "**±10 V open-circuit; −1 % into 100 kΩ,
   −2 % into 50 kΩ**", and the V/oct paragraph should name the divider as the
   term that survives calibration.
2. **Reduce `R-OUT-PROT` to 220 Ω** `[repo: bom.csv]` — the value the BOM notes
   O&C and PER|FORMER use on CV outputs. `[calc]` Divider becomes −0.220 %
   (−2.6 cents/octave). **But** short-circuit current rises to
   `10.2 V / 220 Ω = 46 mA` and dissipation to **473 mW**, making C3-8 worse, and
   cable-capacitance isolation degrades. **Not recommended without the power and
   stability work.**
3. **Jack-side DC feedback, as pitch now does.** Removes the divider exactly, for
   any load. `[calc]` The reconstruction pole would move into the feedback: a cap
   across `R2` of `1/(2π × 30 kΩ × 1941 Hz) = 2.73 nF → 2.7 nF`, which
   conveniently also disposes of the 82 nF sourcing problem (C3-5).
   **But price it honestly, because the page would not:** `[calc]` a capacitor
   across `R2` in a *non-inverting* stage shelves the gain from 4 toward **1**,
   it does not roll off to zero. Pole at 1.94 kHz, zero at
   `4 × 1.94 = 7.77 kHz`, ultimate attenuation **−12 dB**, where the jack-side RC
   keeps falling at −20 dB/decade forever. At the 3.6 kHz image the two are
   close (−5.6 dB vs −6.5 dB `[calc]`); above it they diverge, and the
   feedback cap gives **no RF ingress protection at the jack at all**, which the
   82 nF does. It also inherits the stability risk the pitch page calls its
   highest — on four channels instead of one.
   *(This also means `pitch-stage.md`'s claim that `C-FB-PITCH` is "the same
   corner in a better place" is not quite true — it is a shelf to unity gain,
   −6 dB ultimate, not a 15.9 kHz pole. Outside this page's scope, but it is the
   precedent this option rests on, so it should be checked before the mods copy
   it.)*

**Recommendation: (1) unconditionally, and do not do (3) speculatively.** The
page's own instinct — *"anything pitch-like belongs on channel 1"* — is right.
It just needs the real reason attached.

---

## C3-8 (Moderate) — `R-OUT-PROT` power rating

`[repo: bom.csv]` The row specifies "1 k 1 %, ≥250 mW", 1206, and its note says
*"POWER RATING IS NOT OPTIONAL"* and *"Standard eurorack practice — survives
shorts and **output-to-output patching**."*

`[calc]` With our output at its worst-case −10.202 V (C3-4):

| Fault | Current | Power in the 1 kΩ | vs 250 mW |
|---|---|---|---|
| Jack shorted to ground | 10.20 mA | **104 mW** | ✓ (BOM's 101 mW ✓) |
| Neighbour drives +10 V through 220 Ω | 16.56 mA | **274 mW** | ✗ **over** |
| Neighbour with a stiff +12 V output | 22.20 mA | **493 mW** | ✗ **2× over** |

**The short case is fine; the output-to-output case, which the row explicitly
claims, is not.** `[from memory]` A 1206 thick film is typically 250 mW and will
survive 274 mW briefly, but output-to-output patching is a mistake that persists
until someone notices — indefinitely, in a rack. The clamps do not help: both
nodes are inside the rails, so the BAV99s never conduct.

`[confirm]` OPA2197 output current limit — the op-amp must also sink 22 mA while
held at −10.2 V.

**Fix: specify 1206 at 0.5 W** (widely available in thick film), or 1210. On a
one-off this costs nothing, and it makes the BOM note's own claim true.
`[calc]` Note the arithmetic is worse than the row's own because the row used
10.05 V; the correct worst-case output is 10.202 V.

---

## C3-2 (Critical) — BOM rows

`[repo: bom.csv]`

- **`R-MODGAIN`** — `qty` column reads **16**; the note in the same row reads
  *"EIGHT, not sixteen."* The quantity was not updated with the note. A BOM is
  ordered from its quantity column.
- **`R-MODGAIN`** — one row, `part` = *"10k / 30k 1% metal film"*, one package,
  one quantity, two values. **Split into two rows** (4 × 10 kΩ and 4 × 30 kΩ, or
  16 × 10 kΩ if C3-10's series fallback is taken). As written it cannot be
  turned into a purchase.
- **`R-MODGAIN`** note repeats *"Lands on EXACTLY ±10.000 V"* — carries C3-10
  and C3-11 with it.
- **`C-FILT-MOD`** — `qty` 4 ✓, and the row is **more honest than the page**
  (C3-5). Sync the page to the row, not the other way round.
- **`R-OUT-PROT`** — qty 6 ✓ (six jacks). Rating: C3-8.
- **`R-OPAMP-IN`** — qty 7, and the page's breakdown checks: `[calc]` pitch 1 +
  mods 4 + mod-offset buffer 1 + `VREFOUT` follower 1 = 7 ✓. Minor: the row's
  `description` is *"on each op-amp + input **driven by the DAC**"*, but the
  `VREFOUT` follower's input comes from `VREFOUT` through `TRIM-OFFSET`, not from
  a DAC output `[repo: pitch-stage.md]`, so for that one the stated clamp-current
  rationale does not apply. Harmless; the description is wrong for 1 of 7.
- **`U-OPA-PITCH`** — 6 packages, 12 halves, 11 used, the mod offset buffer
  counted ✓ `[calc]`. Consistent. Note this leaves **one spare half**, so the
  page's *"do not split it into four buffers"* is also a parts-count fact, not
  only a design preference — splitting would need three more halves, i.e. two
  more packages.
- **`R-PRECISION`** (C3-16) — note says *"the other two are available for the mod
  channels, which want 1:3 (three sections against the fourth)."* `[calc]`
  **Three sections against the fourth is four sections — an entire LT5400.** Two
  spare sections cannot make a 1:3. Serving even one mod channel from a matched
  network needs **one additional whole LT5400 per channel, four more packages**.
  The page repeats the same claim (*"a 1:3 ratio that three sections of an LT5400
  give directly against the fourth"*), which reads as nearly free and is not.
  *(It is still the right fix if the span error ever matters: `[calc]` at 0.01 %
  matching, `k = 3.0003` gives a zero error of −0.25 mV and a span error of
  0.01 %, against ±50.5 mV and ±1.5 %. Worth ~$5/channel if a mod channel is ever
  used for pitch. Just price it correctly.)*
- **`U-DAC`** — grade locked to C, gain 2, 5.000 V full scale, clears to zero
  scale ✓ `[repo]`. This is what the whole safe-state argument rests on and it is
  correctly locked down, with its own `[confirm]` against SBAS430 already noted
  in the row. Good practice; the mod page should carry the same gate.

### Naming — C3-16

`[from memory]` The DAC8568's channels are named **A–H** in its own
documentation. `[repo]` This project says "channel 7" (1-based) throughout, and
the BOM says *"channels 6 and 8 spare"*, confirming the convention. **It is
consistent, but it is one translation step away from the part.** Given that this
exact net has already produced one stale-channel bug — the S4 finding the page
devotes a section to — the page should name the pin (`VOUTG`) alongside
"channel 7". An off-by-one here puts four jacks at a rail and nothing can see it.

### Cross-document drift — C3-16

- `[repo: firmware/README.md]` still states *"`Vout = 4 × (Vdac − Voffset)`, with
  `Voffset` the shared **2.5 V** from DAC channel 7"*. Must become 10/3 V, and
  ideally the code (C3-17). This is the file firmware is written from.
- `[repo: 0006]` The channel table lists Mod 1–4 precision as **"Trimmed"**.
  There are no trimmers on the mod channels; the adjustment is firmware
  scale/offset on the display. Should read "Firmware-scaled" or similar —
  "Trimmed" implies a screwdriver that does not exist.
- `[repo: 0006]` has been updated to 3.3333 V in its channel table and its
  drawn-now note ✓, but the body still carries `Vout = 4 × (Vdac − 2.5 V)` and
  a "2.5 V reference point" bullet. Those are the *behavioural* spec and remain
  correct as behaviour; they are only confusing next to the topology note. Low
  priority.

---

## C3-12 (Minor) — the closing recommendation is not supported

The page ends: *"Taking the reference from a **DAC channel** instead keeps the
inverting topology *and* the safe clear … That is the version worth considering,
and it is **strictly better than what is drawn above**. Not adopted
unilaterally: it is a redraw of a settled page and the call belongs to the
author."* `[repo]`

The deference is right. **The claim is not**, and it is placed where the author
will act on it — one day after the last redraw of the same page. Four things it
omits:

1. `[calc]` **The inverting form loads the DAC output.** `Rin` runs from the DAC
   pin to a virtual ground at `V+ = 2.000 V`, drawing up to
   `(5 − 2)/10 kΩ = 300 µA` of DC, varying with code. The drawn non-inverting
   form draws **nothing** from the DAC — the (+) input is high-Z and the 1 kΩ
   carries no current, which is the page's own argument two sections earlier.
   `[confirm]` DAC8568 output impedance and load regulation, SBAS430 — this puts
   a code-dependent gain error into the transfer function that the drawn circuit
   does not have.
2. `[calc]` **Reference error is multiplied by 5, not 3.** The page's own
   arithmetic: `Vout = −4·Vdac + 5·V+`. Any error in `V+` — DAC zero-code error,
   INL, op-amp `Vos` if buffered — appears at the output **5×** instead of 3×.
   That is 67 % worse offset sensitivity on the shared node.
3. `[calc]` **The 4:1 ratio has no exact standard-value pair.** 40 kΩ is in
   **neither E12, E24 nor E96** — which is precisely how the old design ended up
   at 40.2 kΩ and gain 4.02. `log10(4) × 96 = 57.8` E96 steps, not an integer.
   The inverting form therefore **cannot** land on ±10.000 V from standard
   values, while `30 k / 10 k` can.
4. **It does return an op-amp half** — that part is true and is the one real
   advantage, worth ~$1 on a one-off.

**And the page credits the wrong cause throughout.** It attributes ±10.000 V to
the two-resistor form ("Eight resistors instead of sixteen, and it lands on
exactly ±10.000 V"). `[calc]` The two-resistor form is why there are eight
resistors; **the E24 3:1 ratio is why it lands on 10.000**. A two-resistor
non-inverting stage at gain 4.02 (40.2 k / 10 k, `k = 4.02`... in fact
`1 + k = 5.02`) would not. Getting the cause right matters here because the
"strictly better" alternative needs the 4:1 the page thinks is free.

**Action.** Either delete the "strictly better" sentence or replace it with the
four points above, so the author's call is made on the real trade.

---

# What I checked and found sound

Listed so the author knows these were examined and are not silently endorsed.

- **The transfer function.** `Vout = Vdac(1+k) − k·V_ref` derives correctly from
  the drawn topology, and `k = 3`, `V_ref = 10/3` reproduces ADR 0006's
  `Vout = 4(Vdac − 2.5)` exactly. `[calc]` The `k = A − 1`,
  `V_ref = offset/(A−1)` framing in the "Two resistors, not four" section is
  correct and is a genuine correction of the earlier "boundary" reasoning.
- **`R-OPAMP-IN` on the (+) input costs nothing.** The page's central claim.
  `[calc]` The (+) input draws no current, so there is no drop across the 1 kΩ,
  so no gain or offset error — and the page's own counter-example on the
  four-resistor version (−196.3 mV, +9.657 V) reproduces exactly. Correct, and
  well explained. `[confirm]` OPA2197 input bias current — a CMOS-input precision
  part is picoamps `[from memory]`, giving ~nanovolts across 1 kΩ; if it were a
  bipolar-input part at tens of nA, 1 kΩ into an unbalanced 10 k‖30 k = 7.5 kΩ
  would matter. It is worth one sentence in the page for that reason.
- **The safe-clear mechanism.** Putting the offset on a DAC channel so that
  `CLR` zeroes both terms is correct and is the right call. The fixed-divider
  counter-case (`4 × (0 − 2.5) = −10 V` on four jacks, indefinitely, with no
  `MISO`) is correct and is the strongest argument on the page.
- **The mirror failure and the statelessness fix.** Correct, correctly
  identified as the more likely direction, and correctly closed in
  `firmware/README.md`. (Extended by C3-7 on ordering.)
- **Stability of 1 kΩ + 82 nF into a cable.** Sound, for the reason given
  above — the 1 kΩ is outside the loop and is a textbook isolation resistor.
  The page's arrangement is right and the `pitch-stage.md` parenthetical about
  it is right.
- **Crosstalk through the shared reference.** Real, quantified above at
  **0.10 mV at the jack** steady-state and **≤0.44 mV** transient, worst case,
  against a ±50.5 mV resistor error. Not a defect. The conclusion is robust
  against the gated GBW and `Ro`. (Two follow-ups filed: no bypass specified,
  star-route the node.)
- **The reference code residual.** 76.3 µV, common to all four channels, 662×
  below the per-channel resistor error. Harmless, and harmless for exactly the
  reason the page's shared-node argument gives. (Notation filed as C3-17.)
- **Follower current capability.** 1.333 mA source / 0.667 mA sink, 11 mW
  dissipation. Comfortable. (The page's *reasoning* is wrong — C3-9 — but its
  conclusion is right.)
- **Resistor dissipation and voltage rating.** `[calc]` Worst case across `R2` is
  10 V → 3.3 mW; across `R1` is 3.33 V → 1.1 mW. An 0805 at 125 mW and ~150 V
  working `[from memory]` is ample.
- **Noise.** `[calc]` `R1‖R2 = 7.5 kΩ` → 11.1 nV/√Hz, ×4 noise gain =
  44.6 nV/√Hz, integrated over the 1.94 kHz pole's 3.05 kHz noise bandwidth =
  **2.5 µV rms** at the jack. 0.008 LSB. Irrelevant, as expected.
- **Common-mode range.** The (−) node sits at `Vdac` (0–5 V) and `V_ref` at
  3.33 V, well inside a rail-to-rail input on ±12 V. No issue.
- **Resolution.** `[calc]` 305.2 µV/LSB over the 20 V span = 0.0015 % of full
  scale = 0.366 cents/LSB if used for pitch. ADR 0006's cost analysis holds.
- **Clamp arrangement.** BAV99 on the driver side is correct, and the BOM's
  back-powering arithmetic reproduces: `[calc]` module off, neighbour driving
  10 V through 220 Ω → `(10 − 0.7)/1220 = 7.62 mA`, matching the row's 7.6 mA.
  `[repo: bom.csv]`
- **Channel assignment.** Diagram's ch2 signal / ch3–5 siblings / ch7 offset
  matches ADR 0006's allocation table and the BOM's "populate 6 of 8". ✓
- **Op-amp half count.** 11 of 12 used, one spare, mod offset buffer included. ✓
  `[calc]`
- **Filter corner and its justification.** `[calc]` 1940.9 Hz ✓ (page: 1.94 kHz),
  −6.47 dB at the 3.6 kHz ZOH image, consistent with ADR 0006's reasoning for
  giving the mods a slower corner than pitch. The *choice* is sound; only the
  *part* is in question (C3-5).
- **The "±10.05 V uses the DAC's full span / 0.25–4.75 V is a pitch reserve"
  clarification.** Correct and worth keeping — it is the sort of side-by-side
  contradiction that wastes a reader's time, and the page pre-empts it. (Update
  the number to ±10.000 V.)

---

## Suggested order of work

1. **C3-1** — rewrite `## Values` and everything below it against the drawn
   circuit. Nothing else on this page can be trusted until this is done.
2. **C3-2** — `R-MODGAIN` quantity and row split.
3. **C3-6 / C3-7** — one datasheet lookup (`SBAS430`: power-on output state,
   zero-code error, `LDAC`) closes both. Add `R-DAC-PD` if needed, **on the DAC
   side of `R-OPAMP-IN`**.
4. **C3-3** — at minimum, state the load divider in the output spec and in the
   V/oct paragraph.
5. **C3-5** — resolve the capacitor to a buyable part; film is the project's own
   precedent.
6. **C3-4 / C3-9 / C3-10 / C3-11** — corrected arithmetic into the page.
7. **C3-8** — 0.5 W on `R-OUT-PROT`.
8. **C3-12** — fix or delete the "strictly better" sentence **before** the author
   acts on it.

## Parameters that must come from a datasheet

None was reachable; the proxy blocks vendor domains. Each gates a conclusion
above.

| Part | Parameter | Gates |
|---|---|---|
| DAC8568C (SBAS430) | Zero-code error | C3-11, exact `CLR` park voltage |
| DAC8568C | Output state at POR / with reference disabled | **C3-6** — whether the pulldowns are required |
| DAC8568C | `LDAC` behaviour | **C3-7** — atomic refresh option |
| DAC8568C | Output impedance / load regulation | C3-12 — the inverting alternative's DAC loading |
| OPA2197 | Output swing from rail vs load | C3-14 — the ±11.45 V figure |
| OPA2197 | GBW, open-loop output resistance | Crosstalk magnitude (conclusion robust either way) |
| OPA2197 | Output current limit / short-circuit current | C3-8, and the 20 mA capacitor-charging transient |
| OPA2197 | Input bias current | Whether the 1 k vs 7.5 kΩ source imbalance matters |
| OPA2197 | `Vos` and drift | Offset budget (expected negligible) |
| 82 nF C0G | Existence, case size, voltage rating | **C3-5** |
| X7R alternative | DC bias coefficient at 10 V for the chosen case/rating | C3-5 |
| 30.0 kΩ 1 % 0805 | Availability in the chosen series | **C3-10** |
