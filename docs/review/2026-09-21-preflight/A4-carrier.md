# A4 — `hardware/controller/carrier.md`, cold review

**Slice:** the real-time carrier board. **Method:** cold — no prior review
directory was opened. Sources are the design corpus and the banked PDFs in
`datasheets/`, plus `ngspice` runs written for this review.

**Provenance key.** `[datasheet <doc> p.N]` is a page I opened in this session.
`[repo file]` is a corpus file. `[calc]` shows the arithmetic. `[sim]` is an
ngspice run described in §2.4 — a screen, not a measurement. `[from memory]`
means no document backs it. `[not-in-document]` means I looked in the named
datasheet and the claim is **not there**.

**Two decisions are taken here** (§1, §2). Everything else is a finding.

---

## Contents

1. `cref-out-node` — **DECIDED**
2. `riso-ref-topology` — **DECIDED**, with adapted values
3. Impedance: reference, sensor, ADC, level shifter, regulators
4. Current draw per rail, from datasheets
5. Provenance audit — every `[from memory]` and `[calc]` on the page
6. Netlist readiness

---

# 1. `cref-out-node` — DECIDED

## 1.1 The decision

> **`C-REF-OUT` sits on the REF5050's `VOUT` — the buffer's INPUT.
> `carrier.md`'s drawing is correct. `bom.csv`'s `R-ISO-REF` row and
> `breath-receive-stage.md` line 341 are wrong, and both must be corrected.**
>
> **The buffer drives 100 nF and nothing else.**
>
> Qty 2 resolves as: one 10 µF at REF5050 `VIN`, one 10 µF at REF5050 `VOUT`.
> Neither is on the buffer's output. There is no third capacitor, and none is
> wanted.

## 1.2 Why — four independent reasons, any one of which is sufficient

**(a) The REF5050 cannot be built without a capacitor on its own `VOUT`.**
`[datasheet SBOS410O p.26 §8.4.1]`, verbatim:

> *"Confirm that a output capacitor (CL) is connected from VOUT to GND. For
> output stability, verify that the equivalent series resistance (ESR) value of
> CL less than or equal to 1.5Ω."*

and Figure 8-6's caption `[datasheet SBOS410O p.26]`:
*"CL = 1µF to 50µF for REF50xxI, REF50xxAI"*.

So a `C_L` in the 1–50 µF window at REF5050 `VOUT` **exists in every valid
topology of this circuit**. It is not a design choice; it is a condition of the
part working. A 10 µF part satisfies it exactly. The question "which side is it
on" therefore has a forced answer for *one* of the two capacitors, and a
`qty 2` row with the note *"input plus output"* `[repo bom.csv:76]` accounts
for both of them at REF5050 pins. **There is nothing left over to put on the
buffer's output.**

**(b) The part's own name and its cited authority both say REF5050.**
`bom.csv`'s description field is *"Output capacitor on the REF5050"* and its
justification is *"Per the REF50xx datasheet's recommended output
capacitance"* `[repo bom.csv:76]`. That authority is §8.4.1 above, which is
about the REF5050's `VOUT`. The same row then contains the sentence that
created the contradiction — *"this row and breath-receive-stage.md both say the
buffer DRIVES it"* — which is a report of the disagreement, not an assertion of
the other side. **The row's own content already supports the decision; only
`R-ISO-REF`'s row (`bom.csv:130`, *"the follower drives 100nF + 10uF
directly"*) actually asserts the wrong node.**

**(c) Putting 10 µF on the buffer's output is a specification violation of the
buffer.** The OPA2197 is rated *"High Capacitive Load Drive Capability: 1 nF"*
on its front page and again in §7.3.5: *"in a unity-gain configuration, directly
drives up to 1 nF of pure capacitive load"* `[datasheet SBOS737C p.1, p.22]`.
10 µF is **10 000×** that. A design would only ever put it there deliberately,
with TI's Figure 56 network around it — which nothing in the corpus does. Its
presence on that node in two documents is an editing artefact, not an intent.

**(d) Once the node is settled, the REF5050 sees no load current at all — and
that is a benefit nobody has written down.** With the buffer between the
reference and the sensor, the REF5050's only load is the OPA2197's input, which
is ±5 pA typ / ±20 pA max at 25 °C `[datasheet SBOS737C p.7]`. The reference's
load regulation — **20 ppm/mA typ, 30 ppm/mA max, 50 ppm/mA over temperature**
`[datasheet SBOS410O p.7]` — therefore contributes **zero** to the breath scale
factor. On the other topology, 10 mA of sensor current through 30 ppm/mA would
be 300 ppm, which is 1.0 LSB `[calc, §3.2]`. **Settling the node this way
deletes a whole error term rather than budgeting it.**

## 1.3 What must change, and where

| File | Text today | Must become |
|---|---|---|
| `hardware/controller/carrier.md` §2 drawing | 10 µF **and** 100 nF both on the REF5050 output node; nothing drawn at `VS` | 10 µF + 100 nF at REF5050 `VOUT`; **10 µF at REF5050 `VIN`**; **100 nF drawn explicitly at `SKT-BREATH` `VS`** |
| `hardware/controller/carrier.md` §2 prose | *"this page draws its 10 µF on the REF5050 output … settle the node"* | The node is settled; state it once and cite `cref-out-node` |
| `hardware/bom.csv:130` `R-ISO-REF` | *"the follower drives 100nF + 10uF directly"* | *"the follower drives 100 nF"* |
| `hardware/module/breath-receive-stage.md:341` | *"the sensor's `VS` pin — which carries a 100 nF decoupler and `C-REF-OUT`'s 10 µF"* | *"the sensor's `VS` pin — which carries a 100 nF decoupler"* |
| `config/figures.yaml: cref-out-node` | `DISPUTED` | `settled`, value *"REF5050 VOUT (the buffer's input); the buffer drives 100 nF"*, owner `hardware/controller/carrier.md` |

**Add to `forbidden` when the figure is settled** — these are the strings that
must not come back:

```
"100nF + 10uF directly"
"a 100 nF decoupler and `C-REF-OUT`'s 10 µF"
"100 nF decoupler and C-REF-OUT's 10 µF"
"plus C-REF-OUT's 10uF"
```

## 1.4 A second node ambiguity of exactly the same class, found while doing this

`C-DECOUPLE-CARRIER` is qty 7 and its row enumerates them:
*"MCP3202, REF5050 **in**, OPA2197 +12V, 74AHCT125, MPXV4006DP, and both
R-78E5 inputs"* `[repo bom.csv:75]` — seven, exactly.

But **`carrier.md` §2 draws a 100 nF on the REF5050's *output*** (beside
`C-REF-OUT`), **and** `C-REF-OUT`'s own row says *"with a 100nF from
`C-DECOUPLE-CARRIER` alongside"* `[repo bom.csv:76]` — also at the output.
That is the same 100 nF being spent twice, on two different pins, in three
places. Meanwhile the §2 *prose* says the load at the sensor's `VS` pin is
*"100 nF of `C-DECOUPLE-CARRIER`"* — but **no capacitor is drawn at `VS` at
all**.

**Resolution, and it needs one more part:** the REF5050 wants *both*
`[datasheet SBOS410O p.29 §9.4.1.1]` — a `VIN` bypass *and* *"a
high-frequency, 1µF capacitor in parallel between the output and ground"*
`[datasheet SBOS410O p.30]`. So the correct allocation is

| Pin | Part | Why |
|---|---|---|
| REF5050 `VIN` | 10 µF (`C-REF-OUT` #1) **+ 100 nF** (`C-DECOUPLE-CARRIER`) | §8.4.1 supply bypass 1–10 µF |
| REF5050 `VOUT` | 10 µF (`C-REF-OUT` #2) **+ 100 nF** | §8.4.1 `C_L`; §9.4.1.1 parallel HF cap |
| `SKT-BREATH` `VS` | **100 nF** (`C-DECOUPLE-CARRIER`) | the buffer's load — this is the capacitance §2 of this report compensates for |

That is **8** instances of `C-DECOUPLE-CARRIER`, not 7. **`bom.csv:75` qty must
go 7 → 8** and the row's enumeration must say *"REF5050 in **and out**"*.

## 1.5 Two datasheet claims in `bom.csv:76` that are over-read

**(a) *"A SERIES 1-1.5 OHM RESISTOR IS MISSING from this row"* — it is not
missing; TI calls it optional.** The row reads the ESR requirement backwards.
`[datasheet SBOS410O p.26 §8.4.1]` says ESR *"less than or equal to 1.5Ω"*
**for stability** — an **upper** bound, which a 10 µF X7R at a few milliohms
satisfies trivially. The 1–1.5 Ω window is a separate, *noise* recommendation
(*"To minimize noise, the recommended ESR of CL is from 1Ω and 1.5Ω"*), and
`[datasheet SBOS410O p.29 §9.4.1.1]` states plainly: *"A resistor in series
with the output capacitor is **optional**."* The §9.2.1.2 gain-peaking argument
the row cites is from a 16-bit 250 kSPS data-acquisition example.

**Does it matter here?** `[calc]` The REF5050's own output noise is
0.9 µV_rms/V over 10 Hz–1 kHz `[datasheet SBOS410O p.7]`, i.e. **4.5 µV_rms**
on 5.000 V. One ADC LSB referred to `VS` is **1.46 mV** (§3.2). That is a
margin of **325×**. Gain-peaking of a few dB on a term 325× below one LSB is
not a defect.

> **Finding A4-1.** `bom.csv:76`'s "missing series resistor" is a
> misreading of a stability bound as a requirement. **Fit the 1.0 Ω only if a
> bench measurement at E13 shows peaking**; a 0 Ω/1.0 Ω footprint in series
> with `C_L` costs nothing and settles it. It is electrically free either way —
> the resistor is in series with the capacitor to ground, not in the signal
> path, so it introduces no DC error.

**(b) The `TRIM/NR` capacitor is not needed, and should be declined explicitly
rather than left as an unnamed gap.** §9.4.1.1 asks for *"a 1µF noise filtering
capacitor between the NR pin and ground"*; §8.3.6 p.26 says it *"decreases the
overall noise measured on the VOUT pin by half"* and *"increases start-up
time"*. `[calc]` Halving 4.5 µV_rms to 2.25 µV_rms improves a term already
325× below one LSB, at the cost of a longer turn-on. **Decline it, with the
arithmetic.** Say so on the page so the next reviewer does not re-raise it.

---

# 2. `riso-ref-topology` — DECIDED

## 2.1 The decision

> **Adopt TI's Figure 56 dual-feedback network. It transfers. The reason it
> transfers is that `R_ISO` is set by the op-amp's `Zo`, not by the load
> capacitance — which is why TI chose 37.4 Ω for 10 µF where Table 3 would have
> suggested ~1.5 Ω.**
>
> | Part | Value | Node |
> |---|---|---|
> | `R-ISO-REF` | **37.4 Ω, 1 %, 0805** (was 10 Ω) | OPA2197 output → `VS_BREATH` |
> | **`R-FB-REF`** (new) | **10 kΩ, 1 %** | `VS_BREATH` → OPA2197 `−IN` |
> | **`R-FBX-REF`** (new) | **100 Ω, 1 %** | OPA2197 output → `C-FB-REF` |
> | **`C-FB-REF`** (new) | **1 nF, C0G** | `R-FBX-REF` → OPA2197 `−IN` |
>
> Simulated phase margin **85.9° at 896 kHz** `[sim]`, DC error across `R_ISO`
> **exactly zero by topology**, worst-case DC error 50 µV from input bias
> current `[calc, §2.5]`, and |Z_out| at `VS` of **1.20 Ω at 500 Hz**.
>
> **This dissolves the dilemma the corpus has been stuck in.** The choice was
> never "unstable in-loop" versus "2 % of the ratiometric scale factor
> out-of-loop". Dual feedback gives stability *and* zero DC error, because at
> DC the only feedback path is `R-FB-REF` from `VS` and no current flows in it.

## 2.2 Does it transfer? Yes — and here is the mechanism

TI's Figure 56 drives 10 µF; we drive 100 nF, 100× less. TI warns *"Any other
load capacitances require recalculation of the stability components: RF, RFx,
CF, and RISO"* `[datasheet SBOS737C p.30 §8.2.3]`. So the transfer has to be
argued, not assumed.

**`R_ISO` does not scale with `C_L`. It scales against `Zo`.** With feedback
taken at the amplifier output (which is what the `R_Fx`/`C_F` path does above
the handover), the transfer from the internal source to the amplifier pin is

```
[calc]  V_A / V_i = (1 + s·R_ISO·C_L) / (1 + s·(Zo + R_ISO)·C_L)

  pole  f_p = 1 / (2π·(Zo + R_ISO)·C_L)
  zero  f_z = 1 / (2π·R_ISO·C_L)
```

Both the **attenuation above the zero** — `R_ISO/(Zo + R_ISO)` — and the
**pole–zero ratio** — `(Zo + R_ISO)/R_ISO` — depend only on `R_ISO/Zo`. `C_L`
moves both corners together and cancels out of the phase margin, provided both
stay well below crossover.

With `Zo` = **375 Ω** `[datasheet SBOS737C p.8, p.10: "ZO Open-loop output
impedance | f = 1 MHz, IO = 0 A, See Figure 26 | 375 | Ω"]` and
`R_ISO` = 37.4 Ω:

```
[calc]  attenuation = 37.4 / 412.4 = 0.0907  = −20.9 dB
        crossover   = 0.0907 × 10 MHz (GBW)  = 907 kHz
        at 907 kHz:  dominant pole −90°, load pole (f_p) −89.8°,
                     zero (f_z)     +87.3°   →  net −92.5°
        phase margin ≈ 87.5°, less the amplifier's own excess phase
```

**37.4 Ω is ≈ `Zo`/10.** That is the actual design rule behind TI's number, and
it is the reason TI's 37.4 Ω sits an order of magnitude *above* what Table 3
p.23 gives for a 10 µF load by the out-of-loop method (extrapolating 1 µF→4.7 Ω
downward). Table 3 is a different circuit.

**Confirmation:** the same calculation with TI's own `C_L` = 10 µF gives the
same 907 kHz and the same ~87.5°, against TI's published **89°**
`[datasheet SBOS737C p.30]`. The hand model reproduces TI's answer to within
1.5°. That is the transfer argument.

## 2.3 What only `C_L` sets: the handover, and hence `R_F`, `R_Fx`, `C_F`

Reading TI's Figure 56 values back `[datasheet SBOS737C p.30]`:

```
[calc]  R_ISO · C_L  = 37.4 Ω × 10 µF  = 374 µs
        R_Fx · C_F   = 10 kΩ × 39 nF   = 390 µs      (E24 rounding of 37.4 nF)
        → TI's rule is  R_Fx · C_F = R_ISO · C_L
        → for our 100 nF: 37.4 Ω × 100 nF = 3.74 µs
```

The second constant is `R_F · C_F`, which sets the **handover frequency** —
below it the loop closes on `VS` (accurate), above it on the amplifier output
(stable):

```
[calc]  TI:   1/(2π × 1 MΩ × 39 nF)  =    4.08 Hz
        ×100: 1/(2π × 1 MΩ × 390 pF) =  408 Hz
```

**408 Hz is not enough for us and 4 Hz would be a disaster, for a reason TI's
circuit does not have: our load draws 10 mA.** Above the handover, the
amplifier regulates its *own* output, so any load-current change appears at
`VS` across `R_ISO`. TI's load is a pure capacitor and never does this. Ours is
the sensor's excitation, and `VS` **is the ratiometric scale factor**. The
handover must therefore sit above the 500 Hz breath channel, not at its edge.

`[sim]` Sweeping `C_F` with `R_F` = 100 kΩ / `R_Fx` = 1 kΩ:

| `C_F` | handover `1/(2πR_F C_F)` | phase margin | \|Z_out(`VS`)\| @ 100 Hz | @ 500 Hz | @ 5 kHz |
|---|---|---|---|---|---|
| 3.9 nF | 408 Hz | 85.0° | 8.87 Ω | 27.7 Ω | 34.5 Ω |
| 1 nF | 1.59 kHz | 85.0° | 2.35 Ω | 11.2 Ω | 34.0 Ω |
| 390 pF | 4.08 kHz | 85.2° | 0.92 Ω | 4.57 Ω | 29.1 Ω |
| **100 pF** | **15.9 kHz** | **85.9°** | **0.24 Ω** | **1.20 Ω** | **11.7 Ω** |

**Phase margin is essentially independent of `C_F` across two decades, while
output impedance in the breath band improves 30×.** So push the handover up.
100 pF at 100 kΩ works, but 100 pF is only 15× the OPA2197's 6.4 pF
common-mode input capacitance `[datasheet SBOS737C p.7]` and invites layout
parasitics into the compensation.

**Take the handover up by lowering `R_F` instead of `C_F`** — which also
collapses the input-bias-current error (§2.5). `R_F` = 10 kΩ, `R_Fx` = 100 Ω,
`C_F` = 1 nF: `R_Fx·C_F` = 100 ns, `R_F·C_F` handover = 15.9 kHz. `[sim]`:
**PM 85.9° at 896 kHz, |Z_out(VS)| = 1.20 Ω at 500 Hz.** Same result, no
100 pF in a feedback path.

> `R_Fx · C_F` = 100 ns rather than the 3.74 µs the TI rule gives. The sim says
> this costs nothing (85.9° either way), because the `R_Fx C_F` corner only has
> to be far below crossover, and 1.59 MHz... no: `1/(2π×100Ω×1nF)` = 1.59 MHz
> is *above* the 896 kHz crossover, which is exactly what makes `C_F` look like
> a short at crossover. The binding condition is `|R_Fx + 1/(2πf C_F)| ≪ R_F`
> **at crossover**: `[calc]` at 896 kHz that is 100 + 178 = 205 Ω against
> 10 kΩ — a 49× margin. Satisfied.

## 2.4 The simulation, and what it is worth

`ngspice`, behavioural amplifier: `A_OL` = 5.01×10⁶ (134 dB, the tabulated
`R_LOAD` = 10 kΩ figure `[datasheet SBOS737C p.7]`), dominant pole 2 Hz giving
GBW 10 MHz `[datasheet SBOS737C p.8]`, a second pole at 20 MHz, and **`Zo` =
375 Ω as specified** `[datasheet SBOS737C p.8]`. Loop broken at the inverting
input; loop gain `T = −V(summing node)`. Sensor modelled as 500 Ω to ground
(5.000 V / 10 mA max `[datasheet MPXV4006 p.3 Table 1]`) in parallel with
`C_L`.

**Model anchor:** unloaded follower gives crossover 8.83 MHz, PM **66.2°** —
the right region for this part.

**Model validation against TI's published answer:** Figure 56 as printed
(`R_ISO` 37.4, `R_F` 1 MΩ, `R_Fx` 10 kΩ, `C_F` 39 nF, `C_L` 10 µF) gives
**87.4°** against TI's stated **89°**. **1.6° apart.** That is the strongest
check available without a bench.

| Case | crossover | phase margin |
|---|---|---|
| **A.** Follower, no `R_ISO`, 100 nF (the 2026-09-21 hazard) | 206 kHz | **1.5°** |
| **B.** `R_ISO` 10 Ω **in-loop**, feedback at `VS` — **as drawn and as `bom.csv` specifies** | 203 kHz | **1.5°** |
| **B2.** `R_ISO` 37.4 Ω in-loop, feedback at `VS` | 197 kHz | **1.5°** |
| **C.** `R_ISO` 15.8 Ω **out-of-loop** (TI Table 3, 0.1 µF, 60°) | 417 kHz | 75.8° |
| **D.** TI Figure 56 as printed, `C_L` = 10 µF | 899 kHz | **87.4°** (TI: 89°) |
| **E. RECOMMENDED** — 37.4 Ω, `R_F` 10 kΩ, `R_Fx` 100 Ω, `C_F` 1 nF, `C_L` 100 nF | 896 kHz | **85.9°** |

**Two independent confirmations of prior work, from a different model.** Case A
at 206 kHz reproduces the corpus's reported 215 kHz / 8.8° to within the error
bar, and Case C at 75.8° reproduces the reported 75.2°. **Case B2 is new and
is the important one: in-loop `R_ISO` buys nothing at *any* value** — 1.5° at
10 Ω and 1.5° at 37.4 Ω. The corpus's finding that in-loop is no better than
no resistor is confirmed and generalised.

> **The published 2.6° / 458 kHz in `carrier.md` §2 is dead** and its
> replacement is **~1.5° / ~206 kHz** (or the corpus's 8.8° / 215 kHz — the
> difference is second-pole placement, and both mean "oscillator"). The page
> already flags this as pending; it can now be closed.

**Robustness of Case E** `[sim]` — this is what makes it a design rather than a
tuned point:

| Varied | Range | Phase margin |
|---|---|---|
| `Zo` (TI Figure 26 spans 3.26 kΩ @ 0.1 Hz → 73 Ω @ 10 MHz) | 75 Ω | 80.5° |
| | 375 Ω (spec) | **85.9°** |
| | 1 kΩ | 84.8° |
| | 3.26 kΩ | 76.2° |
| `C_L` at `VS` | 47 nF | 83.1° |
| | 100 nF (nominal) | **85.9°** |
| | 220 nF | 87.3° |
| | 1 µF | 88.2° |
| | 10 µF | 88.4° |

**The network never drops below 76° across the entire published range of `Zo`
and across a 200× range of `C_L`.** Two consequences worth recording:

1. The X7R's DC-bias and temperature derating (a 100 nF 0805 X7R can lose
   tens of percent) cannot destabilise it.
2. **Bulk capacitance may be added at `VS` later without recompensating.** If
   E13 finds the reference rail needs stiffening against strip PWM, a 10 µF at
   `VS` costs 2.5° of phase margin and nothing else. The old topology could not
   have survived that.

## 2.5 DC accuracy — the thing the old argument was trading against

**At DC the error across `R_ISO` is exactly zero, by topology.** `C_F` blocks,
so no current flows in `R_Fx`; the amplifier's input current is pA, so no
current flows in `R_F`; therefore the summing node sits at `V(VS)` and the
amplifier forces `V(VS) = V(+) = 5.000 V`. **`R_ISO`'s value and tolerance stop
mattering entirely** — the 2 % objection in `bom.csv:130` and
`breath-receive-stage.md` is answered, not traded away.

What is left `[calc]`, against 1 LSB at `VS` = 1.46 mV (§3.2):

| Term | Worst case | As ppm of 5.000 V | LSB |
|---|---|---|---|
| `I_B` × `R_F` = 5 nA × 10 kΩ `[datasheet SBOS737C p.7, −40…+125 °C]` | 50 µV | 10 | 0.034 |
| `I_B` × `R_F` at 25 °C: 20 pA × 10 kΩ | 0.2 µV | 0.04 | 0.0001 |
| `V_OS` ±100 µV max `[datasheet SBOS737C p.7]` | 100 µV | 20 | 0.068 |
| `V_OS` drift ±2.5 µV/°C × 50 K `[datasheet SBOS737C p.7]` | 125 µV | 25 | 0.086 |
| REF5050 load regulation (now zero — see §1.2d) | 0 | 0 | 0 |

**Total buffer contribution ≤ 0.19 LSB worst case.** Compare the alternatives:

- **Out-of-loop `R_ISO` 15.8 Ω** (TI Table 3, 0.1 µF, 60° `[datasheet SBOS737C
  p.23]`): 15.8 Ω × 10 mA = **158 mV = 3.2 % = 108 LSB**, and it tracks the
  sensor's own supply current, which the datasheet specifies **only as a
  maximum** `[datasheet MPXV4006 p.3]`. That is not a 2 % error, it is an
  **undocumented** error of order 2–3 %.
- **In-loop, as drawn:** 1.5° of phase margin. Not a trade at all.

> **This is why `R_F` is 10 kΩ and not TI's 1 MΩ.** At 1 MΩ the
> guaranteed-over-temperature bias current gives 5 nA × 1 MΩ = **5 mV =
> 1000 ppm = 3.4 LSB**, on a rail that is the scale factor. TI's circuit has
> the same exposure and TI does not mention it, because their reference buffer
> is not feeding a ratiometric sensor. **Do not transfer 1 MΩ.** The
> `R_F`:`R_Fx` ratio is what must be preserved (100:1, so that the HF loop
> closes on the amplifier output with only 1 % of `VS` leaking in), and 10 kΩ :
> 100 Ω preserves it.

## 2.6 Secondary consequences to write down

- **Headroom.** The amplifier output sits at `5.000 + 10 mA × 37.4 Ω = 5.374 V`
  `[calc]` on a +12 V single supply. No issue. Power in `R_ISO` is
  `(10 mA)² × 37.4 = 3.74 mW` in an 0805 `[calc]` — 3 % of a 125 mW part.
- **`R_ISO` tolerance is irrelevant.** 1 % is fine; 5 % would be fine. Its only
  jobs are isolation (set by `R_ISO/Zo`) and, with `R_Fx C_F`, the handover.
- **Startup.** The `R_F`/`C_F` network has no DC path from the summing node to
  anywhere except `VS`, which is correct, but SPICE needs a leak resistor for
  convergence and **a real board does not** — the amplifier's input leakage
  provides it. Note this for whoever builds the SPICE deck properly against
  TI's macromodel.
- **Use TI's macromodel to confirm.** The brief notes the OPA2197, INA828 and
  REF5050 macromodels are on GitHub. Everything above is a behavioural model
  plus hand algebra; it agrees with TI's own published 89° to 1.6°, but the
  vendor model is the cheap next check before layout.

## 2.7 What must change

| File | Change |
|---|---|
| `hardware/bom.csv:130` `R-ISO-REF` | 10 R → **37.4 R 1 %**; replace the in-loop/out-of-loop justification with dual feedback; delete *"the follower drives 100nF + 10uF"* |
| `hardware/bom.csv` | **Three new rows**: `R-FB-REF` 10 k 1 % 0805, `R-FBX-REF` 100 R 1 % 0805, `C-FB-REF` 1 nF C0G 0805. All three are **instrument-side and unretrofittable** and must say so |
| `hardware/controller/carrier.md` §2 | Redraw with the dual-feedback network; delete the "feedback zero inequality" paragraph and the R–C snubber alternative — both are superseded |
| `hardware/module/breath-receive-stage.md:337–353` | The whole subsection is now wrong in its conclusion (*"`R-ISO-REF` goes inside the loop"*). Replace with a citation of `riso-ref-topology` |
| `config/figures.yaml: riso-ref-topology` | `DISPUTED` → `settled`, value *"dual feedback per SBOS737C Fig. 56: R_ISO 37.4 Ω, R_F 10 kΩ at VS, R_Fx 100 Ω + C_F 1 nF at the op-amp output"* |
| `config/figures.yaml` `forbidden` for `riso-ref-topology` | `"INSIDE THE LOOP, with feedback taken at the SENSOR"`, `"R-ISO-REF` goes inside the loop"`, `"2.6° of phase margin"`, `"oscillation near 458 kHz"`, `"R-ISO-REF,controller,10R"` |

---

# 3. Impedance

## 3.1 The reference chain, end to end

| Node | Source impedance | Provenance |
|---|---|---|
| REF5050 `VOUT` (DC) | 0.10 Ω typ, **0.15 Ω max**, 0.25 Ω over temperature | `[calc]` from 20/30/50 ppm/mA × 5 V `[datasheet SBOS410O p.7]` |
| REF5050 `VOUT` (AC) | set by `C-REF-OUT` 10 µF; a few mΩ above ~1 kHz | `[calc]` |
| Buffer input load on it | ±5 pA typ / ±20 pA max | `[datasheet SBOS737C p.7]` |
| **`VS_BREATH`, DC** | ~0 (zero by topology, §2.5) | `[calc]` |
| **`VS_BREATH`, 100 Hz** | **0.24 Ω** | `[sim]` |
| **`VS_BREATH`, 500 Hz** | **1.20 Ω** | `[sim]` |
| **`VS_BREATH`, 5 kHz** | **11.7 Ω** | `[sim]` |
| `VS_BREATH`, ≫ handover | → `R_ISO` = 37.4 Ω | `[calc]` |

## 3.2 What the sensor's `VS` pin demands ratiometrically

```
[calc]  1 LSB at the ADC   = V_DD/4096 = 3.3 / 4096      =  805.7 µV
        referred to the sensor output (÷ 0.600 divider)  =  1.343 mV
        as a fraction of the 4.6 V full-scale span       =  292 ppm
        so VS must hold to 292 ppm of 5.000 V            =  1.46 mV
```

`[datasheet MPXV4006 p.3 Table 1]`: `V_FSS` = 4.6 V typ; supply 4.75–5.25 V,
*"Device is ratiometric within this specified excitation range"*; `I_S` **max
10 mA, no typical given**.

**Therefore the requirement on the buffer is: ≤1.46 mV of movement at `VS` for
whatever the sensor's supply current does.** The recommended network meets it
for a **1 mA** breath-rate current modulation (1 mA × 1.20 Ω = 1.20 mV =
0.82 LSB) `[calc]`, with no knowledge of the sensor's actual dynamic current
required. The out-of-loop alternative would give 15.8 mV = 10.8 LSB for the
same 1 mA. **That is the quantitative form of the argument the corpus has been
making qualitatively.**

> **Finding A4-2, gap.** `I_S` is specified as a maximum only. Nothing in the
> corpus or the datasheet says whether it varies with pressure or temperature.
> **Add it to E1: measure `I_S` at 0 kPa and at 4 kPa.** It is a two-minute
> measurement that closes the last unknown in the reference chain.

**And the grade question, quantified for the first time** `[calc]`, using
`ref5050-grade`'s two candidates against the 292 ppm/LSB scale:

| Grade | Initial accuracy | Drift, 50 K | Drift, ±5 °C autozero window |
|---|---|---|---|
| `REF5050AIDR` (Standard, as ordered) | ±0.1 % = 3.4 LSB — **static, trims out** | 8 ppm/°C → 400 ppm = **1.4 LSB** | 40 ppm = 0.14 LSB |
| `REF5050IDR` (High) | ±0.05 % = 1.7 LSB — static | 3 ppm/°C → 150 ppm = **0.5 LSB** | 15 ppm = 0.05 LSB |

`[datasheet SBOS410O p.7]` for both grades. **The grade is worth ~0.9 LSB of
drift over a full 50 K warm-up and ~0.09 LSB within the ±5 °C window the
sensor's own ±2.46 % FSS accuracy assumes** `[datasheet MPXV4006 p.3 note 5]`.
That is a small number, and it is the number `ref5050-grade` needs to be
decided with. My read: the initial-accuracy half of the difference is
irrelevant (both trim out), and 0.9 LSB of drift does not justify a part
change on its own — **but the order code is one letter and the part is
unretrofittable, so order the `I` grade.** Cost of being wrong is asymmetric.

## 3.3 The ADC input — does the divider settle to 12 bits in 1.5 clocks?

`[datasheet MCP3202 DS21034F p.2, p.13–14]`: `C_SAMPLE` 20 pF, `C_PIN` 7 pF,
internal sampling-switch `R_S` 1 kΩ, `t_SAMPLE` 1.5 clock cycles, and §4.1
verbatim: *"the source impedance (RS) adds to the internal sampling switch
(RSS) impedance, directly affecting the time that is required to charge the
capacitor"*.

**Answer: yes, with ~7× of margin — but only because `C-AA-ADC` is at the pin.
A bare 6 kΩ source would violate Microchip's own Figure 4-2.**

```
[calc]  t_SAMPLE = 1.5 / 900 kHz = 1.667 µs
        12-bit settling needs ln(4096) = 8.32 time constants

  WITH C-AA-ADC (47 nF) AT THE PIN — the actual circuit:
        during acquisition the pin is driven by 47 nF, i.e. ~2350 x C_SAMPLE,
        so the dynamic source impedance is the cap's ESR + trace, < 1 Ω
        tau = 1 kΩ × (20 pF + 7 pF) = 27 ns
        8.32 tau = 225 ns   against 1667 ns          →  7.4× margin  ✔

  WITHOUT C-AA-ADC — the case Figure 4-2 is drawn for:
        tau = (1 kΩ + 6 kΩ) × 27 pF = 189 ns
        8.32 tau = 1573 ns against 1667 ns           →  6 % margin   ✘
```

**And Microchip's Figure 4-2 confirms the bare case fails**: read off the
`V_DD` = 2.7 V curve at `R_S` = 6 kΩ, the maximum clock for *"less than a
0.1 LSB deviation in INL"* is **≈0.65 MHz** `[datasheet MCP3202 DS21034F p.14,
read by rendering at 260 dpi]`, against the design's 0.9 MHz. **The 47 nF is
not a nicety; it is what makes the 6 kΩ Thevenin legal.**

> **Finding A4-3.** `carrier.md` §2 and `bom.csv:45` both describe `C-AA-ADC`
> as an anti-alias filter and mention "the ADC's charge reservoir" only in
> passing. **That second job is the load-bearing one** — without it the source
> impedance is out of spec by Microchip's own curve. Say it explicitly, and
> mark `C-AA-ADC` as not-optional and not-reducible below ~20 nF (1000 ×
> `C_SAMPLE`). `bom.csv:46` `R-ADCDIV`'s *"Needs C-AA-ADC to still settle"* is
> the right instinct stated without the number.

**The residual error the reservoir cannot remove** — the page's own
calculation, **confirmed correct** `[calc]`:

```
I_avg   = C_SAMPLE × f_SAMPLE × V = 20 pF × 4 kHz × V = 80 nA per volt
ΔV      = 80 nA/V × 6.0 kΩ = 480 µV/V = 0.048 %
at 2.88 V full scale: 1.354 mV ÷ 805.7 µV = 1.68 LSB
```

`carrier.md` says *"about 2 LSB at full scale, proportional to V_in, therefore
a pure constant gain term"*. **Both the arithmetic and the characterisation are
right.** (It is a gain term because it is proportional to `V_in`; it is
absorbed by the panel span knob.)

**A second residual, not on the page** `[calc]`: the per-sample droop on the
47 nF is `20 pF × 2.88 V / 47 nF = 1.23 µV`, recovering through
`τ = 6 kΩ × 47 nF = 282 µs` against a 250 µs frame, so steady state is
`1.23 µV × 1/(1−e^(−250/282)) = 2.1 µV` = **0.0026 LSB**. Negligible. Recorded
so nobody re-derives it as a worry.

**Headroom, and a full-scale figure this page gets wrong** — see Finding A4-6
in §5.

## 3.4 The level shifter, and a mismatch in the brief

**Nothing on this board drives 2 m of cable through a level shifter.** The
carrier's `74AHCT125` drives ~420 mm to each LED strip; the 2 m umbilical is
driven **directly by ESP32-S3 GPIO** through `R-SPI-SER`, and the
`74AHCT125` at the *module* end is a receiver `[repo carrier.md §4,
bom.csv:35]`. Both are covered below.

**(a) `74AHCT125` → 420 mm → WS2815 `DI`.**

```
[datasheet SCLS264O p.4]  V_OH ≥ 4.4 V at I_OH = −50 µA
                          V_OH ≥ 3.8 V at I_OH = −8 mA
[datasheet WS2815 p.3]    V_IH = 0.7 × VDD, table header VDD = 4.5–5.5 V
                          → V_IH = 3.15–3.85 V;  C_I ≤ 15 pF
```

The WS2815's `DI` is a CMOS input drawing leakage only, so **the −50 µA row is
the one that governs the static level**: 4.4 V against a 3.85 V worst-case
threshold, **0.55 V of margin**. `carrier.md`'s *"~4.4 V minimum"* is correct
and correctly sourced.

**Edge rate, which is not on the page** `[calc]` — 420 mm of loom wire is
~60–100 pF, plus 15 pF of `C_I`, call it 115 pF:

| `R-LED-SER` | τ | time to the 3.85 V threshold (80 % of 4.4 V) | as a fraction of `T0H`min = 220 ns |
|---|---|---|---|
| 330 Ω (`bom.csv:117`) | 38 ns | 61 ns | **28 %** |
| 100 Ω (`carrier.md` low end) | 11.5 ns | 19 ns | 8 % |

Both work. But **`carrier.md` and `bom.csv` disagree on this part** — the page
says *"`R-LED-SER` ×2–4, 100–330 Ω, proposed"*, the BOM says **330 R, qty 2,
candidate** with a dated 2026-09-21 decision on the quantity `[repo
bom.csv:117]`. The quantity is settled and the page is stale; **the value is
not argued anywhere.** Note that the reflection model used for `R-SPI-SER` does
**not** apply here: 420 mm of untwisted loom wire is not a controlled-impedance
line, so this is genuinely edge-rate damping, where larger is better for EMI
and smaller is safer for the WS281x timing window. 330 Ω eating 28 % of the
shortest pulse's edge is acceptable but is the kind of margin that should be
chosen rather than inherited.

**(b) ESP32-S3 GPIO → `R-SPI-SER` 100 Ω → 2 m of Cat5 → module `74AHCT125`.**

`carrier.md` §4's table is **arithmetically reconstructible and correct**, but
it rests on an input it never states. `[calc]`, reverse-engineering it:

```
far-end first step = 2 × V × Z0 / (Z0 + R_SER + R_driver)     (open far end)

  R_SER 220 Ω, R_driver 40 Ω:  2 × 3.3 × 100/360 = 1.83 V   ← table says 1.83–1.86 ✔
  R_SER 100 Ω, R_driver 40 Ω:  2 × 3.3 × 100/240 = 2.75 V   ← table says 2.75    ✔
  R_SER  68 Ω, R_driver 33 Ω:  2 × 3.3 × 100/201 = 3.28 V   ← table says 3.25    ✔
  fault current at 68 Ω:       3.3 / 68 = 48.5 mA           ← table says 48 mA   ✔
```

> **Finding A4-4.** The entire 100-vs-220 Ω decision — which is settled, in
> `figures.yaml` as `spi-series-r`, and in `bom.csv:50` — turns on an
> **unstated ESP32-S3 pad output impedance of ~40 Ω** and an unstated 40 mA pad
> limit. Neither is in any banked document; there is **no ESP32-S3 datasheet in
> `datasheets/`** (only board schematics and a pins file). The conclusion is
> almost certainly right, but a settled figure resting on an unrecorded
> `[from memory]` input is the pattern `CLAUDE.md` is about. **Either bank the
> ESP32-S3 datasheet and cite the pad spec, or add `esp32s3-pad-drive` to
> `figures.yaml` as `blocked`.**

Against the receiving `74AHCT125`: `V_IH` 2.0 V min, `V_IL` 0.8 V max, TTL and
not ratioed to `V_CC`, and *"input transition rate ≤ 20 ns/V"* `[repo
bom.csv:35, from SCLS264O]`. 2.75 V clears `V_IH` by 0.75 V ✔.

## 3.5 Each regulator's load

**`R-78E5.0-1.0` × 2** `[datasheet RECOM R-78E-1.0 REV 9/2024 p.1, p.3]`:
1.0 A, input **8–28 V for the 5.0 V part** (the front-page *"7V – 28V"* bullet
is the 3.3 V part's — confirmed, the Selection Guide table on p.1 gives
`R-78E3.3-1.0` = 7–28 and `R-78E5.0-1.0` = **8–28**), switching **330 kHz**,
quiescent **1.5 mA**, max capacitive load **220 µF**, output accuracy ±3 % typ
/ **±5 % max**, line reg ±1 % max, load reg ±1.5 % max, short-circuit
protection *"Continuous, automatic recovery"*. Derating graph p.3, read from a
200 dpi render: **100 % of rated load to +60 °C, linear to 60 % at +85 °C, hard
cutoff**. `[calc]` slope −1.6 %/°C → 92 % at 65 °C, 84 % at 70 °C, 78 % at
73.8 °C. **`bom.csv:10`'s reading of this graph is correct in every particular.**

`carrier.md`'s 68–78 % loading for buck A is inside the 92 % permitted at 65 °C
with ~14 points of margin ✔.

> **Finding A4-5, new.** The board's input filter is **not** Recom's.
> `[datasheet R-78E p.3]` gives an EMC filter for EN55032 — topology
> `+Vin — C1 — L1 — C2 — module`, and for the `R-78E5.0-1.0`:
> **Class A: C1 10 µF / L1 12 µH (RLS-126) / C2 10 µF, all 100 V MLCC;
> Class B: C1 10 µF / L1 68 µH (RLS-686) / C2 2.2 µF.**
> The carrier draws **`L-BUCK-IN` 10–47 µH then `C-BUCK-IN` 100 µF
> electrolytic** — i.e. `L1` and `C2` only, **with no `C1` on the raw +12 V
> side**, and with `C2` an electrolytic where Recom specifies MLCC. Three
> consequences:
> 1. Without `C1`, `L1` is fed from 2 m of umbilical inductance rather than a
>    low-impedance node, which is not the network Recom characterised.
> 2. `carrier.md`'s damping derivation **requires** `C-BUCK-IN` to be an
>    electrolytic with 0.5–1 Ω of ESR. Recom's suggestion is an MLCC. **These
>    two requirements are in direct conflict and no document notices.** The
>    damping argument should win (it is about stability, Recom's is about
>    conducted emissions) but it must be stated as a deliberate departure.
> 3. The open item *"`L-BUCK-IN` qty 1 against `C-BUCK-IN` qty 2"* has a vendor
>    answer: Recom's filter is **per module**. Two modules, two filters, two
>    inductors. That does not settle it — one shared L is defensible — but it
>    is the reference case and it is not cited.

**`ME6217C33M5G`, the dev board's 3V3 LDO** `[datasheet ME6217 V05 p.4]` —
800 mA max (at `V_IN ≥ V_OUT + 1.0 V`), dropout 100 mV typ / 180 mV max at
300 mA, `I_SS` 100 µA, `SOT23-5 θ_JA` 210 °C/W with `P_D` 0.6 W, short-circuit
350 mA. See §4.3 for the load-regulation finding, which is the important one.

> **Finding A4-6, and it is a real hole in the 5 V chain.** `[calc]` from
> `[datasheet SS14 p.1]` (`V_F` 0.50 V typ / 0.75 V max) and the Waveshare
> schematic's netlist `[repo datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf,
> net NLVCC_5V = D1 cathode + header P1.1 + the whole LED array]`:
>
> ```
> R-78E5.0 output  5.00 V nominal, 4.75 V at the −5 % max accuracy limit
> less D-USBOR (SS14)  −0.50 V typ / −0.75 V max
> → VCC_5V at the dev board = 4.50 V typical, 4.00 V worst case
> ```
>
> **Three things break at 4.00 V.** (i) The `ME6217`'s 800 mA rating is
> conditioned on `V_IN ≥ V_OUT + 1.0 V` = 4.3 V — not met, so the available
> 3V3 current is reduced by an unspecified amount. (ii) The 64 matrix LEDs run
> directly from `VCC_5V` with no regulator `[repo figures.yaml
> matrix-led-current]`, below the WS2812B family's rated supply window.
> (iii) **The USB path and the buck path arrive within ~40 mV of each other**:
> USB VBUS 5.00 V less the board's own `B5819WS` at ~0.46 V = 4.54 V, against
> the buck path's 4.50 V. Two Schottkys ORing two sources 40 mV apart do not
> hand over cleanly — they share, unpredictably, and the sharing moves with
> temperature. **The instrument's behaviour with USB plugged in is undefined,
> and USB is the second rung of the recovery ladder** `[repo carrier.md §6]`.
>
> `bom.csv:69` says *"Both sources drop ~0.3V, leaving ~4.7V at the dev boards'
> 5V pins"*. **0.3 V is the `1N5817`'s drop, not the `SS14`'s** — the corpus's
> own digitisation of the 1N5817 curve gives 0.24 V at 245 mA `[repo
> figures.yaml diode-split-rationale]`. `carrier.md`'s component table names
> `SS14`; `bom.csv` says *"1N5817 or SS14"* and gives the package as
> **DO-41 through-hole**, which is the 1N5817's package and not the SS14's
> (SMA). **The part is not actually chosen, the two candidates differ by
> ~0.2 V, and 0.2 V is the whole margin.** Choose the 1N5817, or better, state
> that neither is good enough and price a low-`V_F` OR.

---

# 4. Current draw per rail, from datasheets

## 4.1 +12 V, raw umbilical — the analog block, now fully sourced

| Load | Typ | Max | Over temp | Source |
|---|---|---|---|---|
| `REF5050` `I_Q` | 0.8 mA | 1.0 mA | 1.2 mA | `[datasheet SBOS410O p.8]` |
| `REF5050` output load | ~0 | ~0 | ~0 | §1.2d |
| `OPA2197` × 2 amplifiers | 2.0 mA | 2.6 mA | 3.0 mA | `[datasheet SBOS737C p.8]` |
| `MPXV4006DP` `I_S` | — | 10 mA | 10 mA | `[datasheet MPXV4006 p.3]` |
| **Analog subtotal** | **12.8 mA** | **13.6 mA** | **14.2 mA** | `[calc]` |
| `R-78E5.0` × 2, quiescent | 3.0 mA | — | — | `[datasheet R-78E p.1]` |

`carrier.md` §2 books *"~13 mA `[repo] 0003"`* for the analog block. **Confirmed
at 12.8 typ / 13.6 max; re-mark it `[datasheet]` and use 13.6.**

## 4.2 +12 V, the LED strips — and a figure the corpus has at less than half

`LED-SIDE` is a 1 m reel of WS2815 at 60/m cut into two 420 mm runs `[repo
bom.csv:11]` = **50 LEDs total** (25 per side, matching `carrier.md` §5).

```
[datasheet WS2815 p.3]  Quiescent Current              2.1 mA
                        RGB Channel Constant Current  15 mA  (per channel)

[calc]  per LED, all dark   = 2.1 mA
        per LED, full white = 2.1 + 3 × 15 = 47.1 mA
        50 LEDs, all dark   = 105 mA   at 12 V
        50 LEDs, full white = 2355 mA  at 12 V  = 28 W
```

> **Finding A4-7, and it is load-bearing well outside this page.** ADR 0005's
> load table books *"Clamp fails, strips latched full white"* at **1023 mA** on
> the 12 V-direct column `[repo 0005]`. The datasheet figure is **2355 mA —
> 2.3× higher.** Two things follow:
> 1. The quiescent number is *right*: 105 mA of strip plus ~18 mA of analog
>    against ADR 0005's 123 mA. So the error is specifically in the full-white
>    row, which is the one the thermal clamp exists to bound.
> 2. **A latched full-white strip, on its own and with everything else off,
>    exceeds the module's 1.0 A `LT1641` limit by 2.4×.** That is arguably a
>    safety property — the failure mode self-limits — but it means the
>    instrument *cannot* display full white even momentarily, and the
>    "~17 W / 1522 mA" body-heat row is understating the fault case by more
>    than a kilowatt-second of transient.
>
> This is not my slice's decision to take, but the number is from a banked
> datasheet and it contradicts a table that drives ADR 0014's brightness clamp.
> **File against ADR 0005's load table, not against `carrier.md`.**

## 4.3 5 V, and the split ADR 0005 is missing

**What is datasheet-backed:**

| Load | Value | Source |
|---|---|---|
| `74AHCT125` static `I_CC` | 20 µA max | `[datasheet SCLS264O p.4]` |
| `74AHCT125` `ΔI_CC`, per input at a TTL level | **1.5 mA max**, × 2 driven inputs = **3.0 mA** | `[datasheet SCLS264O p.4]` |
| `74AHCT125` dynamic, 2 outputs × ~65 pF × 5 V × 800 kHz | ≤0.52 mA | `[calc]` |
| **`74AHCT125` total** | **≤3.6 mA** | `[calc]` |
| `MCP3202` `I_DD` (on 3V3, via the dev board LDO) | 375 µA typ / **550 µA max at `V_DD` = 5 V**; no 3.3 V row, so conservative | `[datasheet DS21034F p.3]` |
| Key pull-ups, 18 closed, through the 3V3 LDO | 25.8 mA | `[calc]` from `[repo bom.csv:91,92]`: 3.3 V / (2.2 kΩ + 100 Ω) = 1.435 mA each |

> **ADR 0003 books the level shifter at *"around 10 mA"* `[repo 0003:123]`.
> The datasheet gives ≤3.6 mA.** Overstated ~3×, harmless, but it is a number
> in a load table and should be corrected to the datasheet value.

**What is not, and cannot be:**

> **Finding A4-8 — the split cannot be produced from documents, and that is the
> answer.** `carrier.md` flags *"ADR 0005's load table has one 5 V column and
> the two-regulator decision needs it split per buck. That split is not written
> anywhere and it is what sizes both parts."* Having gone looking: **the two
> dominant terms on the 5 V rail have no datasheets.**
> - The ESP32-S3-Matrix module's total draw: no banked document. ADR 0005's
>   40–80 mA for the S3 core is `[from memory]`.
> - The 8×8 matrix: `figures.yaml matrix-led-current` is **`blocked`**, and its
>   own `decided_by` says it needs *"a current probe, not a fetch"*.
> - The LilyGO display board: no banked document (its schematic is in
>   `datasheets/mechanical/` but was not costed here).
>
> Everything I *can* source — level shifter 3.6 mA, ADC 0.55 mA, pull-ups
> 25.8 mA — totals **~30 mA**, under 5 % of `carrier.md`'s 680–780 mA estimate
> for buck A. **So the per-buck split is blocked on E1/E6 in exactly the way
> `matrix-led-current` is, and `carrier.md`'s *Still open* entry should say so
> rather than implying a document could close it.** Recommend adding
> `buck-a-5v-load` to `figures.yaml` as `blocked`, `blocked_on: E1 current
> probe`, cross-referenced to `matrix-led-current`.

## 4.4 The 3V3 reference movement — a `[from memory]` that was wrong twice over

`carrier.md` §2 and §3 both carry: *"at an LDO load regulation of ~0.3 % per
100 mA `[from memory]`: 0.077 % = 3.2 LSB"*.

**The datasheet is banked.** `[datasheet ME6217 V05 p.4, ME6217A33/C33 table]`:

```
Load Regulation   ΔV_OUT   1 mA ≤ I_OUT ≤ 300 mA    typ 10 mV    max 50 mV
Line  Regulation           V_OUT+0.5V ≤ V_IN ≤ 6.5V typ 0.1 %/V  max 0.3 %/V
```

Two findings at once:

> **Finding A4-9.** *"~0.3 % per 100 mA"* is the shape of the **line**
> regulation figure (0.3 %/V max), not the load regulation figure. The
> load-regulation spec is a **total ΔV_OUT over the whole 1–300 mA range**, in
> millivolts.
>
> `[calc]`, prorating linearly over the specified range for a 25.8 mA step:
>
> | | ΔV_OUT | as ppm of 3.3 V | LSB |
> |---|---|---|---|
> | typ (10 mV / 299 mA) | 0.863 mV | 262 | **1.07 LSB** |
> | **max (50 mV / 299 mA)** | **4.31 mV** | **1306** | **5.35 LSB** |
>
> **The page's 3.2 LSB sits between typ and max.** Its conclusion survives —
> it is a gain term, it scales with how hard you are blowing, and it is small
> against a ~1594-count playable span. But **the worst case is 5.35 LSB, 68 %
> larger than the page claims**, that is 0.34 % of the playable span, and it is
> now a datasheet number rather than a recollection. Both copies of this
> paragraph (§2 and §3) must be updated, and this is precisely the
> "fix lands where the editor is, not where the reader looks" trap — the two
> copies are 300 lines apart.

---

# 5. Provenance audit — every marker on the page

## 5.1 `[from memory]` → now sourceable

| Line | Claim | Verdict |
|---|---|---|
| 347 | *"a family-typical ±2 mA"* ESD-clamp injection rating for the MCP3202 | **`[not-in-document]`.** DS21034F specifies only an absolute-maximum **voltage** — *"All Inputs and Outputs w.r.t. VSS: −0.6 V to VDD + 0.6 V"* `[datasheet DS21034F p.2]`. **There is no injection-current rating for this part.** The ≥10 kΩ upper leg is still right, but its justification must be restated: it bounds the current at 410 µA, and the limit it is being compared against is undocumented. Re-mark `[not-in-document]` — this is a stronger and more honest statement than `[from memory]` |
| 394, 497 | *"LDO load regulation ~0.3 % per 100 mA"* | **Refuted and replaced.** See Finding A4-9. `[datasheet ME6217 V05 p.4]` |
| 836 | `U-ADC` *"clock limit `[from memory]`"* in the component table | **Stale marking.** The page's own §4 closed this on 2026-09-21 against DS21034F. Re-mark `[datasheet DS21034F p.3]` |
| 848 | `U-LVLSHIFT` *"`BI` `[from memory]`"* in the component table | **Stale marking.** The page's own §5 closed this against the WS2815 datasheet. Re-mark `[datasheet WS2815, recommended application circuit]` |
| 131 | *"ESR of a 100 µF / 25 V radial ≈ 0.5–1 Ω"* | **Still `[from memory]`.** No electrolytic datasheet is banked. This is the single input the LC damping argument stands on, and §3.5 Finding A4-5 shows Recom specifies an MLCC here instead. **Bank a specific part, or the damping paragraph is unsupported** |
| 655, 658 | S3 FSPI IO_MUX pins GPIO9–14; GPIO-matrix cap ~40 MHz | **Still `[from memory]`.** No ESP32-S3 datasheet in `datasheets/`. Irrelevant at 2 MHz, as the page says |
| 686 | GPIO1/GPIO2 high-Z for 100–300 ms at reset | **Still `[from memory]`.** Same gap. The `R-LED-PD` argument is qualitatively safe regardless of the exact window |
| 902 | WS2815 strip width ~10 mm | **Still `[from memory]`.** A mechanical measurement, not a datasheet one |
| 794 | §7's matrix-geometry inputs | **Still `[from memory]`**, correctly flagged as E1-blocked |
| §4 table | ESP32-S3 pad drive impedance ~40 Ω / 40 mA limit — **unmarked** | **Unmarked claim = defect per `CLAUDE.md`.** See Finding A4-4 |

## 5.2 `[calc]` — re-checked

**Correct, arithmetic confirmed:**

- Input LC: `f0` = 3.39 kHz, `Z0` = 0.469 Ω, `R_neg` = −103 Ω, margin 220× ✔
  `[calc]` 1/(2π√(22 µH × 100 µF)) = 3393 Hz; √(22µ/100µ) = 0.469; −11.4²/1.26 = −103.1
- Anti-alias: `R_th` = 6.0 kΩ, `f_c` = 564 Hz, τ = 282 µs, 55 dB at 330 kHz ✔
  `[calc]` 20·log₁₀(330 000/564) = 55.3 dB. The 330 kHz is confirmed
  `[datasheet R-78E p.1]`
- Sample-cap charge sharing: 480 µV/V, ~1.68 LSB at full scale ✔ (§3.3)
- Key pull-ups: 1.435 mA per closed key, 25.8 mA at 18 ✔
- `Zo` correction: 21 kHz → **4.24 kHz** against 100 nF ✔
  `[calc]` 1/(2π × 375 × 100 nF) = 4244 Hz
- AGND-return cost: 13 mA × 0.168 Ω = 2.2 mV, × 2.185 = 4.8 mV ✔
- Loop budget: 96.0 + 26.7 = 122.7 µs, 49 % ✔
- Loom conductor count and the 49 mm internal-width arithmetic ✔
- SPI first-step table ✔ (reconstructed in §3.4b)

**Dead, delete with the node decision:**

- *"200 Hz → 42 Hz against 10.1 µF"* (line 276). The arithmetic is right —
  `[calc]` 1/(2π × 375 × 10.1 µF) = 42.0 Hz — but **10.1 µF is never on that
  node** (§1). Every "or 200 Hz" / "or 42 Hz" branch on this page, in
  `bom.csv:27` and in `breath-receive-stage.md` goes with it.
- *"10 Ω × 10.1 µF = 101 µs against 10 kΩ × 1 nF = 10 µs"* — the feedback-zero
  inequality. Superseded by §2 entirely; the single-zero model is not the right
  model for this circuit.

**Wrong — and it is the `CLAUDE.md` failure mode exactly:**

> **Finding A4-10.** Line 333: *"full scale = **4.7 V** × 0.6 = 2.82 V against
> VREF 3.3 V → 85 % of range, 3502 counts"*.
>
> `config/figures.yaml: sensor-full-scale` is **4.80 V**, `settled`, owned by
> ADR 0003, derived `0.2 + 0.766 × 6 = 4.796 V` — and the MPXV4006DP cover page
> confirms **0.2 to 4.8 V** `[datasheet MPXV4006 p.1]`. **The same page draws
> "0.2 – 4.80 V" correctly in its own §2 schematic, 120 lines above.**
>
> Corrected `[calc]`: 4.80 × 0.6 = **2.88 V** → 2.88/3.3 = **87.3 %** →
> **3575 counts**, not 2.82 V / 85 % / 3502.
>
> **`tools/check-staleness.py` passes on this**, because the `forbidden`
> strings are `"4.7 V output"` and `"0.2-4.7 V"` and the live text reads
> `"4.7 V × 0.6"`. **The same escape exists in `bom.csv:46`**, whose
> `R-ADCDIV` row reads *"Sensor reaches 4.7V into a 3V3 ADC"*. And line 347's
> clamp calculation inherits it: `(4.7 − 0.7)/10 kΩ = 400 µA` should be
> `(4.80 − 0.7)/10 kΩ = 410 µA`.
>
> **Add to `sensor-full-scale`'s `forbidden`:** `"4.7 V × 0.6"`,
> `"4.7 V x 0.6"`, `"Sensor reaches 4.7V"`, `"(4.7 − 0.7)"`, `"(4.7 - 0.7)"`.
>
> Note what *survives*: the 1594-count playable span is unaffected, because it
> is `1743 − 149` and both terms come from the 2.8 kPa working point, not from
> full scale. So this is a headroom error, not a signal-chain error.

**A related headroom number nobody has** `[calc]`: `carrier.md` treats 0.2 V as
the rest output, but `[datasheet MPXV4006 p.3 Table 1]` gives `V_off` =
**0.152 / 0.265 / 0.378 V** (min/typ/max). At the maximum offset with nominal
span, the sensor's top output is `0.378 + 4.6 = 4.978 V` → ×0.6 = **2.99 V =
90.5 % of the 3.3 V reference**. Still no clipping, but the real worst-case
headroom is 9.5 %, not 15 %. And the offset spread alone is 0.226 V = 168
counts, which is why the firmware autozero is not optional.

## 5.3 Markings that are now stale in the other direction

- **`R-CHAIN-SER`, `U-TVS-CHAIN`, `F-CHAIN` all have `bom.csv` rows now**
  (lines 95, 96, 97, `status=open`, each crediting `carrier.md` for proposing
  them). The page still says *"Proposed, not in the BOM"* for `F-CHAIN` and
  marks all three `proposed` in its component table. **Stale; the BOM caught
  up and the page did not.**
- **`C-ADC-BULK` and `R-LED-PD` genuinely have no BOM rows.** `proposed` is
  correct for those two.
- **`HDR-DEV` is a live contradiction.** `carrier.md` asserts *"Qty is one
  board's worth, not two"*; `bom.csv:72` still reads qty 6, *"2 strips for the
  ESP32-S3-Matrix, 2 for the T-Display-S3 AMOLED, 2 spare"*. The page's own
  §"One dev board, not two" says the BOM budgets both — it still does. **Nobody
  has closed this and it is a footprint on an unretrofittable board.**
- The Status block still says *"Not checked against a single datasheet"* and
  names `waveshare.com`, `ti.com`, `nxp.com`, `analog.com` as blocked. **Six of
  this page's parts are now banked.** The header is the first thing a reader
  sees and it is the most out-of-date sentence on the page.
- The Status block points at `docs/review/2026-09-21-schematic-review/S3-carrier.md`
  for its gap list. **That directory does not exist** (`docs/review/` holds
  `2026-09-20-cold-review`, `2026-09-21-hardware-and-standards-review`,
  `2026-09-21-staleness-sweep`, `2026-09-21-pcb-pipeline-review`,
  `2026-09-21-preflight`). Dead cross-reference.
- Figure citation check: `carrier.md` §2 attributes the overshoot-vs-capacitive-load
  plots to *"Figures 27/28"*. **Correct** — Figures 27 and 28 are on
  `[datasheet SBOS737C p.16]`, in Typical Characteristics. They are reprinted
  as Figures 47/48 on p.23 alongside Table 3. Both citations are valid; noting
  it so the next reviewer does not "fix" a correct reference.

---

# 6. Netlist readiness

## 6.1 Proposed canonical net names

Where the page names a net inconsistently or not at all, this is the name to
adopt. Existing consistent names are unchanged.

| Net | Members | Note |
|---|---|---|
| `V12_UMB` | J-UMB.3, D-REVSHUNT.K, D-TVS-PWR, C-STRIP-BULK×2, J-LED-L.1, J-LED-R.1, REF5050.VIN, OPA2197.V+, L-BUCK-IN.1 | the raw rail |
| `PWR_GND` | J-UMB.6, all of the above returns, MECH-GNDBOND, U-TVS-SPI.GND | the single ground bond originates here |
| `V12_BUCK` | L-BUCK-IN.2, C-BUCK-IN, U-BUCK-A.IN, U-BUCK-B.IN | post-LC |
| `V5_A` / `V5_B` | U-BUCK-A.OUT → D-USBOR-A.A / U-BUCK-B.OUT → D-USBOR-B.A | **before** the OR diodes |
| `VCC_5V` | D-USBOR-A.K, HDR-DEV.5V, 74AHCT125.VCC | the OR node; also fed by the dev board's own `B5819WS` from USB |
| `V3V3` | HDR-DEV.3V3, MCP3202.VDD, C-ADC-BULK, J-CHAIN.10 via F-CHAIN | **is also `VREF`** |
| `VREF_5V0` | REF5050.VOUT, C-REF-OUT#2, C-DECOUPLE-CARRIER, OPA2197A.+IN | **§1's decision lives here** |
| `VS_BREATH` | R-ISO-REF.2, R-FB-REF.1, SKT-BREATH.VS, C-DECOUPLE-CARRIER | the sensor excitation |
| `REFBUF_OUT` | OPA2197A.OUT, R-ISO-REF.1, R-FBX-REF.1 | the amplifier pin, **distinct from `VS_BREATH`** |
| `REFBUF_FB` | OPA2197A.−IN, R-FB-REF.2, C-FB-REF.2 | the summing node |
| `BREATH_RAW` | SKT-BREATH.VOUT, OPA2197B.+IN | |
| `BREATH_BUF` | OPA2197B.OUT, OPA2197B.−IN, R-SER-BREATH-INST-A.1, R-ADCDIV-U.1 | |
| `BREATH_ADC` | R-ADCDIV-U.2, R-ADCDIV-L.1, C-AA-ADC.1, MCP3202.CH0 | |
| `AGND_LOCAL` | analog star; ties to `PWR_GND` at **one** point, at J-UMB | |
| `AGND_SENSE` | J-UMB.2, R-SER-BREATH-INST-B.1 | sense-only, carries no supply current |

## 6.2 Ambiguities a netlister will hit, in order of cost

1. **`C-REF-OUT`'s node** — **resolved, §1.** Was the blocker.
2. **`C-DECOUPLE-CARRIER`'s seven instances vs eight pins** — **§1.4.** The
   sensor's `VS` has no capacitor drawn and the REF5050 has one at the wrong
   pin. **Qty 7 → 8.**
3. **Where the MCP3202's `CLK`/`DIN` tap off SPI2** — not drawn. §4 shows
   `IO35 SCK` and `IO36 MOSI` going through `R-SPI-SER` to `J-UMB`, and the
   ADC hanging off the same host. **They must tap at the GPIO pin, *before*
   `R-SPI-SER`**, so the series resistor terminates the cable only. Tapped
   after, the ADC sits on the far side of a deliberately over-damped source and
   the 100 Ω termination sees a lumped 10 pF load `[datasheet DS21034F p.3,
   `C_IN` 10 pF max]` at the wrong end. **One line of text, unretrofittable if
   laid out wrong.**
4. **`HDR-DEV` quantity** — one board's worth or two (§5.3). Footprints.
5. **`D-USBOR` part** — `1N5817` or `SS14`, ~0.2 V apart, against ~0.2 V of
   margin, in two different packages (§3.5 Finding A4-6).
6. **`R-LED-SER`** — 330 Ω qty 2 (`bom.csv`) vs 100–330 Ω qty 2–4
   (`carrier.md`). BOM wins on quantity; the value is unargued (§3.4a).
7. **`L-BUCK-IN` qty 1 vs `C-BUCK-IN` qty 2** — one shared LC or two. Recom's
   own filter is per module (§3.5 Finding A4-5).
8. **Which port of the MPXV4006DP is P1** — the page lists this as open, but
   **`bom.csv:5` has settled it: *"P1 IS SETTLED: 'Side with Part
   Marking'"***, from Table 3 of the banked datasheet, with an explicit warning
   that the GP variant uses the opposite convention. **The page is stale; the
   BOM is right.** Remove it from *Still open*.
9. **`AGND_SENSE` vs `AGND_LOCAL`** — §2 of the page decides that the analog
   supply return goes home on `PWR_GND` and `AGND` is sense-only. **Good, and
   it should become a `figures.yaml` entry**, because it is exactly the kind of
   one-line topology fact that `cref-out-node` and `dig-gnd-topology` show gets
   lost. Suggest `agnd-return-topology`, `settled`, owner `carrier.md`.
10. **`J-LED-L/R` `BI` pin** — settled (grounded at the head), but the net
    name should make it explicit that `BI` ties to the strip-end `GND` net and
    is not driven, or a netlister will allocate a conductor for it.

## 6.3 What is ready

Sections 3 (`J-CHAIN` 2×6, alternating grounds, eight connectors), 4 (SPI
egress, `R-SPI-SER` 100 Ω ×3, `U-TVS-SPI`), 5 (LED data, gates B and D spare,
`BI` grounded) and 6 (`HDR-SERVICE` 2×3, `J-DISP` 9-way) are **internally
consistent, pin-complete and netlistable as written**, with the two value
questions above. Section 2 becomes netlistable once §1 and §2 of this report
are applied. Section 1 needs Finding A4-5 resolved. Section 7 is blocked on the
dev board arriving and is correctly flagged as such.

---

# Findings index

| # | Node / part | Severity | Summary |
|---|---|---|---|
| **D1** | `C-REF-OUT` | **decision** | Sits on REF5050 `VOUT`. Buffer drives 100 nF only. §1 |
| **D2** | `R-ISO-REF` + 3 new parts | **decision** | Dual feedback, 37.4 Ω / 10 kΩ / 100 Ω / 1 nF, 85.9° `[sim]`, zero DC error. §2 |
| A4-1 | `C-REF-OUT` | medium | "Missing 1–1.5 Ω series resistor" is a misread bound; optional, and 325× below one LSB |
| A4-2 | `U-BREATH` | gap | `I_S` specified as a maximum only; add to E1 |
| A4-3 | `C-AA-ADC` | **high** | Its charge-reservoir job is what makes the 6 kΩ Thevenin legal; bare 6 kΩ fails Microchip Fig. 4-2 at 0.9 MHz |
| A4-4 | `R-SPI-SER` | medium | A settled figure rests on an unrecorded ~40 Ω pad impedance; no ESP32-S3 datasheet banked |
| A4-5 | `L-BUCK-IN` / `C-BUCK-IN` | **high** | Recom's own EMC filter is C1–L–C2 per module with MLCCs; the corpus has L–C only, electrolytic, shared, and the ESR requirement conflicts with Recom's part choice |
| A4-6 | `D-USBOR` | **high** | SS14 costs 0.50–0.75 V; `VCC_5V` lands at 4.00–4.50 V, breaking the LDO's 800 mA condition and colliding with the USB path within 40 mV |
| A4-7 | `LED-SIDE` | **high** | WS2815 full white is 47.1 mA/LED → 2355 mA for 50 LEDs, against ADR 0005's 1023 mA |
| A4-8 | 5 V rail | gap | The per-buck split is blocked on a current probe, not on a document; say so |
| A4-9 | `V3V3` / `U-ADC` | medium | LDO load regulation is 10 mV typ / **50 mV max**, i.e. **1.07 / 5.35 LSB**, not the `[from memory]` 3.2; the "0.3 % per 100 mA" was the *line* regulation figure |
| A4-10 | `R-ADCDIV` | **high** | Live `4.7 V` full-scale in `carrier.md:333` and `bom.csv:46`, against a settled 4.80 V. The checker cannot see it. Correct figures: 2.88 V, 87.3 %, 3575 counts |
| A4-11 | `HDR-DEV` | medium | Page says one board's worth, BOM still budgets two. Unclosed, and it is footprints |
| A4-12 | `U-BREATH` P1 | low | Page lists P1 as open; `bom.csv:5` settled it from the banked datasheet. Page is stale |
| A4-13 | page header | low | Status block still says "not checked against a single datasheet" and points at a review directory that does not exist |

---

## Verification notes for whoever audits this report

- The ngspice decks are reproducible from the parameters in §2.4; the amplifier
  is behavioural, not TI's macromodel. **The one number that validates it is
  87.4° against TI's published 89° for Figure 56 as printed.** If that
  reproduces, the rest of the table is trustworthy to a few degrees.
- Two of my results independently reproduce prior simulated findings from a
  different model — 206 kHz vs 215 kHz for the uncompensated follower, and
  75.8° vs 75.2° for out-of-loop `R_ISO`. Agreement between models that cannot
  see each other is evidence; agreement with a number I had already read is
  not, and I had not read those before running (they appear in
  `config/figures.yaml`, which I read after). **Treat that caveat as real: I
  saw `figures.yaml`'s 75.2°/8.8° before running ngspice.** The Figure 56
  validation at 87.4° is the clean one, because TI's 89° is a measured vendor
  number and my model was not tuned to it.
- Figure 4-2 of DS21034F and the R-78E derating graph were read by rendering
  at 260 and 200 dpi respectively and reading the curves by eye. The MCP3202
  figure gives ≈0.65 MHz at 6 kΩ on the 2.7 V curve; treat that as ±0.1 MHz.
  The Recom derating graph is a straight-line construction and is exact.
- Everything marked `[datasheet …]` was read from the banked PDF in this
  session, not recalled.
