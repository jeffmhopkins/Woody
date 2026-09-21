# X3 — Analog loading and stability audit: every op-amp in the module

**Scope:** every OPA2197 half in the project — what drives it, what it drives,
and whether it is stable, in common-mode range, in swing, in current, and in
its offset budget.

**Sources read:** all five pages in `hardware/module/`, `hardware/bom.csv`,
ADR 0003, 0004, 0006, `docs/reference/latency-budget.md`. `docs/review/` and
`docs/research/` were not opened.

**Network:** ti.com, analog.com, nxp.com and every distributor were blocked.
**No OPA2197 number in this document was read from a datasheet.** Every
conclusion that depends on one is marked `[gated]` and the parameter is named
in §7. Where a figure was needed to make arithmetic concrete I state the
assumption inline and mark it — those are assumptions, not specifications.

**Evidence markers:** `[repo]` = read in a named file. `[calc]` = arithmetic
shown in full here. `[gated]` = depends on a specification this sandbox cannot
reach. `[from memory]` = recalled, unverified, treat as a hypothesis.
There are no `[datasheet]` marks in this document because no datasheet was
readable.

---

## 0. Findings, in severity order

| # | Finding | Where | Severity |
|---|---|---|---|
| **D1** | A unity-gain buffer drives **100 nF with no isolation** (REF5050 buffer → MPXV4006DP `VS` + its decoupling cap). This is the one place the part is inadequate *as connected*. | ADR 0003 L468 + BOM `C-DECOUPLE-CARRIER` | **High** |
| **D2** | The **mod channels keep the load divider** that pitch was redesigned to remove. −1 % to −2 % of span into ordinary Eurorack loads, the same size as the "dominant" tolerance term the page tabulates, and absent from that table. | `mod-channels.md` | **High** |
| **D3** | The breath **OFFSET knob has authority in one direction only, and it is the useless direction**. Same defect class the breath page removed at the in-amp `REF` pin; it moved downstream to the panel. The module has no negative reference to fix it with. | `breath-receive-stage.md` | **High** |
| ~~D4~~ | The umbilical was not balanced — 1 kΩ on the signal leg, nothing on the `AGND` leg, capping CMRR at **60.2 dB**. **Fixed in the repo while this audit was being written** (`R1b`). Independently derived here; arithmetic confirms the page. **One residual: BOM row 66 still says qty 1, 0805.** | `breath-receive-stage.md` | **Closed → D4b** |
| **D4b** | `R-SER-BREATH-INST` (BOM row 66) is still **qty 1 in 0805**, while the page now specifies **two** 1 kΩ in **1206 ≥250 mW** (`R1`, `R1b`). Both are instrument-side and therefore unretrofittable. | `bom.csv` row 66 vs `breath-receive-stage.md` | **High** |
| **D18** | The presence detect now trips at **exactly half the resting pedestal** — 0.10–0.25 kPa of *negative* mouthpiece pressure, i.e. **10–25 mm H₂O**. A trip disables `OE`, stops the DAC refresh, and 99 ms later **clears every CV output**. The threshold sits inside the signal's own range. | `digital-and-supervision.md`, BOM row 100 | **High** |
| **D19** | The new presence threshold is derived from **stage 10's output**, so a `REF`-buffer failure *to zero* leaves the unplugged state sitting exactly **on** the threshold. The page claims the circuit "degrades correctly"; it does so for a rail failure and **latches at "present" forever** for a low failure. | `digital-and-supervision.md` | Medium |
| **D5** | The **count is wrong three ways**. BOM row 13 says eleven and lists ten; row 28 contradicts row 13 and makes it nine; the instrument-side buffer is on a different board and was never inside the six; and a **twelfth stage (the REF5050 buffer) is counted nowhere at all**. | `bom.csv` rows 13, 26, 27, 28 | Medium |
| **D6** | Breath output **clips at the top of the GAIN knob** — saturates above 46 % of sensor range at 2.5×, with 0.4 V of margin on a hard blow *before* the offset knob adds anything, and the saturated level is 1.4 V outside the module's own ±10 V convention. | `breath-receive-stage.md` | Medium |
| **D7** | **Jack-side feedback makes a shorted PITCH jack saturate the amplifier** where op-amp-side feedback would not. Every patch-cable insertion momentarily shorts tip to sleeve. New failure mode, introduced by the redesign, unmentioned. | `pitch-stage.md` | Medium |
| **D8** | `TRIM-GAIN` is **one-sided upward with the nominal design point at its bottom stop**. Any error needing gain < 2.000 is untrimmable. The page simultaneously claims the load error is zero *and* that the trimmer exists to absorb it. | `pitch-stage.md` | Medium |
| **D9** | **R-OUT-PROT exceeds its 250 mW rating** in the output-to-output case the BOM claims it survives: 269 mW against a 220 Ω-source module. The BOM's 101 mW models a dead short only. | `bom.csv` row 42 | Medium |
| **D10** | The breath stage has **no component values at all** and no feedback capacitor, with a B50k pot and panel wiring in the loop. Its noise-gain zero lands near 557 kHz. It is the stage with the most demanding requirements and the least specification. | `breath-receive-stage.md` | Medium |
| **D11** | Four op-amp outputs return **20 mA cap-charging transients into `AGND`, which is an in-amp input**, not a ground. | `mod-channels.md` + `power-entry.md` | Medium |
| **D12** | BOM row 13's "**RRIO on ±12 V reaches ~11.9 V**" is unphysical — above the rail after `D1`. Three different swing numbers are in circulation (11.45 / 11.6 / 11.9). | `bom.csv` row 13 | Medium |
| **D13** | The pitch reconstruction corner is **14.2 kHz, not 15.9 kHz** — `R-OUT-PROT` is now inside the feedback leg and nobody re-did the arithmetic. | `pitch-stage.md`, BOM `C-FB-PITCH` | Low |
| **D14** | The breath output's **330 µs reconstruction pole is in no latency table**, while ADR 0003's summary line says the whole op-amp-and-filter term is 160 µs. | `latency-budget.md` L64, ADR 0003 L26 | Low |
| **D15** | Two stale LT5400 claims survive: "the other two [sections] are available for the mod channels, which want 1:3". **Arithmetically impossible** — 1:3 needs three sections against the fourth, there are two left, there are four channels, and the mods use discretes. | `pitch-stage.md` "Still open", BOM row 15 | Low |
| **D16** | The **mod-offset follower's load is modelled wrongly** — "2.5 V into 2.5 kΩ" uses the superseded reference and a topology the page itself replaced. Right magnitude, wrong mechanism, and it hides that the load is signal-dependent. | `mod-channels.md` | Low |
| **D17** | **Nothing in the repo assigns the halves to packages.** The shared-package question is currently answered by whoever does the layout. | everywhere | Low |

**Answer to "is there any role where this part is not adequate":** yes, exactly
one — **D1**, and the inadequacy is the connection, not the part. Everywhere
else the OPA2197 is comfortable to over-specified. See §6.

---

## 1. All twelve halves — the inventory

Not eleven. **Twelve**, across **two boards** and **seven packages**.

| # | Stage | Board / package | Driven by | Input CM | Drives | Peak I_out | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **Pitch amp**, non-inv G = 2 | module, `U-OPA-PITCH` | DAC ch1 via `R-OPAMP-IN` 1 k | 0.25–4.75 V | 11.2 kΩ feedback leg (incl. `R-OUT-PROT`, tapped at jack) + 1 nF + BAV99 + patch load | 245 µA no-load; 11.4 mA into a shorted jack | **OK, with D7, D8, D13** |
| 2 | **Pitch V_ref follower** (`VREFOUT` follower) | module, `U-OPA-PITCH` | `TRIM-OFFSET` wiper off `VREFOUT`, via 1 k | ≈ 2.500 V | one 10 kΩ (`R1`) into the pitch inverting node | ±225 µA, signal-dependent | **OK.** One of only two DC-critical halves |
| 3 | **Mod 1**, non-inv G = 4 | module, `U-OPA-PITCH` | DAC ch2 via 1 k | 0–5.000 V | 30 kΩ feedback (at op-amp output) + 1 k → 82 nF → jack | 167 µA static; **20 mA** transient | **D2, D9** |
| 4 | **Mod 2** | module | DAC ch3 via 1 k | 0–5.000 V | as above | as above | **D2, D9** |
| 5 | **Mod 3** | module | DAC ch4 via 1 k | 0–5.000 V | as above | as above | **D2, D9** |
| 6 | **Mod 4** | module | DAC ch5 via 1 k | 0–5.000 V | as above | as above | **D2, D9** |
| 7 | **Mod-offset follower** | module, `U-OPA-PITCH` | DAC ch7 via 1 k | 3.3333 V | four 10 kΩ into four inverting nodes | **+1.33 mA / −0.67 mA**, signal-dependent | **OK, with D16** |
| 8 | **Breath gain stage** | module, `U-OPA-PITCH` | INA828 output, 0 → −9.94 V | ≈ 0 V | 1 k → 330 nF → jack | 5.0 mA at the corner; 11 mA shorted | **D3, D6, D10** |
| 9 | **Breath offset stage** | module — **claimed by BOM row 13, denied by BOM row 28** | — | — | — | — | **D5.** May not exist |
| 10 | **Breath `REF`-zero buffer** | module, `U-OPA-PITCH` | `TRIM-BREATH-ZERO` wiper, **off the LM317 5.21 V rail** | 0 – 1.0 V | INA828 `REF` pin | ~9 µA `[gated]` | **OK** — see §10 on the rail's tempco |
| 11 | **Instrument breath buffer** | **carrier**, `U-BUF` half B, single +12 V | MPXV4006DP OUT | 0.152–4.8 V | 1 k → 2 m Cat5 → 11 kΩ/1 MΩ network; plus 25 kΩ ADC divider + 220 nF | ~8 µA at rest; 4.8 mA if the umbilical shorts | **D4** |
| 12 | **REF5050 buffer** | **carrier**, `U-BUF` half A, single +12 V | REF5050 OUT, 5.000 V | 5.000 V | MPXV4006DP `VS`, **~10 mA**, **+ 100 nF decoupler, no isolation** | ~10 mA continuous | **D1 — the one real inadequacy** |

Stage 12 appears in **no** count anywhere in the repo. It is specified in
ADR 0003 L468 `[repo]` and in BOM row 26 ("Buffered by half of `U-BUF`")
`[repo]`, and BOM row 27 names `U-BUF` as "breath buffer + reference buffer"
`[repo]` — but row 13's eleven-item list does not include it, and neither did
the brief this review was given.

### 1.1 The count does not reach eleven, and never could

BOM row 13 `[repo]`: *"Twelve halves, eleven used: pitch, mod 1-4, mod offset
buffer, breath gain, breath offset, VREFOUT follower, breath REF-zero buffer.
One spare."*

Count that list: 1 + 4 + 1 + 1 + 1 + 1 + 1 = **10** `[calc]`. The sentence
says eleven and enumerates ten.

Three separate errors compound:

1. **Row 13 contradicts row 28 of the same file.** Row 28 (`U-DIFFRX`)
   `[repo]`: *"the downstream stage inverts, which is also the topology that
   does gain-then-offset with two pots in **one op-amp half**."* If that is
   right, "breath gain" and "breath offset" are one half, the module uses
   **nine**, and six packages leave **three** spare. `breath-receive-stage.md`
   draws it as one half too `[repo]` — the block is labelled `½ OPA2197`.
2. **The instrument-side buffer is on the other board and was never a
   candidate.** It is `U-BUF` (BOM row 27), an `OPA2197IDR` on `PCB-CARRIER`
   (BOM row 73) `[repo]`, two metres from the module. It cannot be one of
   `U-OPA-PITCH`'s twelve halves. **So no arrangement of module stages reaches
   eleven** — ten is the ceiling, nine is what the schematics draw.
3. **Row 13's history line is wrong.** *"Was 5 packages with zero spare once
   the breath zero trimmer went in"* — five packages is ten halves, which is
   exactly the ten stages the row lists, so five packages had zero spare only
   under the ten-stage reading; going to six then gives **two** spare, not one
   `[calc]`. Under the nine-stage reading it gives three.

**Correct totals** `[calc]`:

| | Packages | Halves | Used | Spare |
|---|---|---|---|---|
| Module (`U-OPA-PITCH`) | 6 | 12 | 9 or 10 | **2 or 3** |
| Carrier (`U-BUF`) | 1 | 2 | **2** | **0** |
| **Project** | **7** | **14** | **11 or 12** | 2 or 3 |

The spare count matters because **D3's fix needs exactly one spare half** (a
−1 inverter to generate −2.500 V). There is room. Fixing D3 would make row 13's
"eleven" true for the first time.

---

## 2. Input common-mode range — the short answer, with the numbers

`[calc]` from the voltages in §1, against ±11.7 V module rails (§4.1):

| Stage group | Input CM | Nearest rail | Distance |
|---|---|---|---|
| Pitch amp | 0.25–4.75 V | V+ | **6.95 V** |
| Mod 1–4 | 0–5.000 V | V+ | **6.70 V** |
| Mod-offset follower | 3.3333 V | V+ | 8.37 V |
| Pitch V_ref follower | 2.500 V | V+ | 9.20 V |
| Breath `REF` buffer | 0 – 1.0 V | V− | ≥ 11.7 V |
| Breath gain stage | ≈ 0 V | either | ≥ 11.7 V |
| Instrument buffer (0/+12 V) | 0.152–4.8 V | **V− (ground)** | **0.152 V** |
| REF5050 buffer (0/+12 V) | 5.000 V | V− | 5.00 V |

**No module stage comes within 6.7 V of either rail.** The only input in the
project that approaches a rail is the instrument-side buffer, and it approaches
the *negative* one on a single supply — the easy side for any input topology.

**Consequence worth recording:** the rail-to-rail *input* capability that BOM
row 13 names as the part's defining property (*"Dual low-drift RRIO op-amp"*
`[repo]`) is **not exercised by a single one of the twelve halves**. The
properties that are actually load-bearing are (a) input offset and drift, on
stages 1 and 2 only, and (b) output-swing-to-ground on a single supply, on
stage 11 only. That is not a reason to change the part — ADR 0004's one-part
rule is sound — but row 13 currently implies all eleven halves need RRIO, and
that is the sentence someone will rely on if the part ever has to be
substituted.

The one CM question that *would* matter on a substitute — whether the input
stage is charge-pumped or a complementary pair with a crossover region near the
positive rail — is therefore **moot here**. `[gated]` on the OPA2197's input
architecture; `[from memory]` the OPA19x "e-trim" family is charge-pumped and
has no crossover, but nothing in this audit depends on that being true.

---

## 3. Load and output current, stage by stage

### 3.1 Mod channels — and D2, the divider nobody removed

`mod-channels.md` `[repo]` shows `R2 30k` returning to the node labelled
**"op-amp output"**, before `D-JACK-CLAMP` and before `R-OUT-PROT`.
`pitch-stage.md` confirms it in as many words: *"The mod channels keep their
jack-side caps and are unaffected: their feedback comes from the op-amp
output"* `[repo]`. ADR 0006 L613 says the same `[repo]`.

So `R-OUT-PROT` 1 kΩ is **outside** the mod loop, and the jack divides against
the patch load exactly as pitch used to `[calc]`:

```
V_jack = V_out × R_load / (R_load + 1 kΩ)

one 100 kΩ VCO      10.000 × 100/101 = 9.901 V     −0.99 % of span
two on a mult (50k) 10.000 ×  50/51  = 9.804 V     −1.96 %
a 10 kΩ CV input    10.000 ×  10/11  = 9.091 V     −9.1 %
```

The page's own tolerance table calls ±2 % of span *"the dominant term, and it
was unmentioned"* `[repo]`. **The load divider is a second term of the same
size, systematic rather than random, and it is unmentioned in the same table.**
Into a passive mult it is larger than everything the sixteen-corner enumeration
produced.

This is the exact error ADR 0006 spent a page eliminating on pitch (−11.9
cents/octave into one VCO, −23.5 into two `[repo]`), and the fix — tap the DC
feedback at the jack — is already drawn, tested and argued two pages away.
It was applied to the one channel where firmware could also have corrected it,
and withheld from the four channels where the correction would have to know
the patch. The mods' scale and offset are a firmware feature
(`mod-channels.md` "Still open" `[repo]`), so a per-load preset would work —
but that is precisely the operational complexity ADR 0006 deleted from pitch.

**The headroom consequence is the part that bites.** With feedback at the
op-amp output, the op-amp pin must sit *above* the jack `[calc]`:

```
into a 10 kΩ CV input, to get ±10.000 V at the jack:
V_opamp = 10.000 × (11/11 ... ) → the loop holds V_opamp at ±10.000 V,
so the jack only reaches 9.091 V.

To reach ±10.000 V AT THE JACK into 10 kΩ the op-amp would need
V_opamp = 10.000 × 11/10 = ±11.00 V
```

±11.00 V against an output swing of roughly ±11.5 V (§4.1) is **0.5 V of
margin** `[calc]` — and against BOM row 13's imaginary ±11.9 V it looks like
0.9 V, which is D12 in action. The correct statement is: **the mods cannot
deliver ±10 V into a low-impedance load at all, and the number that makes it
look close is wrong.**

**Currents** `[calc]`, at +10.000 V:

| Path | Current |
|---|---|
| Feedback, (10.000 − 5.000)/30 kΩ | 167 µA |
| Into 100 kΩ, 10.0/101 kΩ | 99 µA |
| Into 10 kΩ, 10.0/11 kΩ | 909 µA |
| Jack shorted, 10.0/1 kΩ | **10.0 mA** |
| **Full-scale step −10 → +10 V into 82 nF**, 20.0/1 kΩ | **20.0 mA peak**, τ = 1 kΩ × 82 nF = 82 µs |

The 20 mA transient is the largest output current anywhere in the module and
it is `[gated]` on the OPA2197's linear output current. It occurs on every
full-scale code jump, which on a generic modulation channel is a normal event,
not a fault.

### 3.2 D9 — R-OUT-PROT is under-rated for the case the BOM claims it survives

BOM row 42 `[repo]`: *"1206 at 250 mW. Standard eurorack practice — survives
shorts and **output-to-output patching**."* Its arithmetic covers only the
short: 10.05²/1000 = 101 mW `[calc]`, correct.

The output-to-output case, against a module with a 220 Ω output resistor — a
value row 42 itself names ("Ornament & Crime and PER|FORMER use 220R on CV")
`[repo]` — at opposite polarity `[calc]`:

```
I = 20.0 V / (1000 Ω + 220 Ω) = 16.4 mA
P(our 1 kΩ) = (0.0164)² × 1000 = 269 mW
```

**269 mW against a 250 mW part.** Marginal, sustained (a mis-patch stays
mis-patched), and the stated justification for the rating is the very case that
exceeds it. Against a module with no output resistor at all the number is
worse. `[gated]` on the actual 1206 thick-film rating, which is 250 mW for most
series and 500 mW for some — specifying the series, not the footprint, is the
same lesson `power-entry.md` already teaches about ferrite beads `[repo]`.

The op-amp sinks 16.4 mA in that state; `[gated]` on linear output current.

### 3.3 The mod-offset follower — D16, and why the crosstalk is fine anyway

`mod-channels.md` `[repo]`: *"that half drives four 10 kΩ inputs in parallel.
At 2.5 V into 2.5 kΩ that is 1 mA."*

Both halves of that are wrong. The reference is 3.3333 V now, not 2.5 V (the
page's own Values table says so `[repo]`), and the four 10 kΩ resistors do
**not** go to ground — in the two-resistor non-inverting form each `R1` runs
from the buffer to that channel's inverting node, which the loop holds at
`Vdac` `[repo]`, anywhere in 0–5.000 V. So `[calc]`:

```
I_n = (3.3333 − Vdac_n) / 10 kΩ

Vdac = 0       →  +333.3 µA   (that channel's jack at −10.000 V)
Vdac = 5.000   →  −166.7 µA   (that channel's jack at +10.000 V)

all four at 0 V    →  +1.333 mA sourced
all four at 5.000  →  −0.667 mA sunk
```

The diagram's marginal note "~1.3 mA total into 4 × 10k" `[repo]` has the right
number and the wrong reason; the prose has the wrong reference voltage and the
wrong topology and lands near the right magnitude by cancellation.

It matters because the correct model shows the load is **signal-dependent and
bipolar**, which raises the crosstalk question the page never asks: does mod 1's
DAC code move mod 2's output through the shared node? `[calc]`, with
Zout(closed-loop) = Zout(open-loop)/(1 + Aβ):

```
ΔI per channel, full swing:              500 µA
loop gain at 1 kHz  = GBW/f = 10 MHz/1 kHz = 10⁴   [gated: GBW]
Zout_cl at 1 kHz    = 100 Ω / 10⁴ = 10 mΩ          [gated: Zout_ol]
ΔV_ref              = 500 µA × 10 mΩ = 5 µV
at every mod jack   = k × ΔV_ref = 3 × 5 µV = 15 µV  (1.5 ppm of a 20 V span)

at 20 kHz: loop gain 500, Zout_cl 200 mΩ, ΔV_ref 100 µV, at the jacks 300 µV
           (15 ppm)
```

**Negligible**, by three orders against the ±81 mV zero tolerance the page
already accepts `[repo]`. The page's instruction "Do not be tempted to split it
into four buffers" `[repo]` is right, and now it has a number behind it instead
of an aesthetic preference.

### 3.4 D11 — where the 82 nF charging current goes

`mod-channels.md` returns `C-FILT-MOD` to **`AGND`** `[repo]`.
`power-entry.md` says, in its grounding section: *"`AGND` is not a ground at
all — it is an in-amp input (ADR 0003)"* `[repo]`. `breath-receive-stage.md`
confirms it: `AGND` is the conductor that drives the INA828's IN+ `[repo]`.

So the four largest transient currents in the module — up to 20 mA each, and
they step together because all six DAC channels are written in one SPI pass
(`firmware/README.md` statelessness rule, cited in `mod-channels.md` `[repo]`)
— are returned into the breath receiver's reference input.

`[calc]`, with an assumed 10 mΩ of copper between the caps' return and the
in-amp's `AGND` tap (`[gated]` on layout, which does not exist yet):

```
4 × 20 mA = 80 mA transient
× 10 mΩ   = 0.8 mV at the in-amp IN+, differential (IN− is referenced to the
            instrument, two metres away, and does not move with it)
× G 2.161 = 1.73 mV at the in-amp output
× 2.5     = 4.3 mV at the breath jack   (0.04 % of a 10 V output)
```

Bounded and small at 10 mΩ; **ten times worse at 100 mΩ**, which a thin return
trace to a distant star point easily is. It is only excited by fast modulation
(a 10 V/s modulation draws 82 nF × 10 = 0.82 µA, nothing), so the audible
symptom is a tick on breath coincident with fast mod-channel movement — the
kind of defect that is found on the bench and never traced.

The breath output's own 330 nF returns to the same node: 5.0 mA (§3.5) × 10 mΩ
× 2.161 × 2.5 = 270 µV of self-feedback `[calc]`, loop gain ≈ 2.7 × 10⁻⁵ — far
from an oscillator, but it is a positive-or-negative feedback path around the
whole breath chain that exists only because the filter returns share a node
with an amplifier input.

**This is a schematic-level fact, not a layout detail:** the nets are drawn
connected. The fix is a named `AGND_SENSE` net that only the INA828 IN+, `R5`
and the `REF` buffer's reference touch, joined to the filter-return `AGND` at
one point.

### 3.5 Breath output stage load

1 kΩ then 330 nF to `AGND`, cap **outside** the loop `[repo]` — same
arrangement as the mods, correctly isolated. `[calc]`:

```
τ = 1 kΩ × 330 nF = 330 µs      corner 1/(2π × 330 µs) = 482 Hz
peak current at the corner, 10 V p-p:
  I = C·2πf·V = 330 nF × 2π × 482 Hz × 5 V = 5.0 mA
jack shorted from +11 V: 11 mA, resistor 121 mW  ✓
```

**D14:** that 330 µs is a reconstruction pole in the breath signal path and it
appears in **no** latency table. `latency-budget.md` L64 lists
*"Reconstruction filter ~82 µs | Mod channels, 1.94 kHz. Pitch is 15.9 kHz and
costs ~10 µs"* `[repo]` — breath is absent. ADR 0003 L26 summarises the whole
term as *"Op-amp and reconstruction filter | ~160 µs"* `[repo]`. The receive
filter's 300 µs *is* listed (L42) `[repo]`; the output's 330 µs is a second,
separate pole in the same chain, so the analog breath path carries **630 µs**
of filter group delay `[calc]` against a summary line that says 160 µs.

---

## 4. Output swing and headroom

### 4.1 The rails, done properly — and D12

`power-entry.md` `[repo]` puts **one** Schottky in series with each analog rail:
`D1` for +12 V analog, `D3` for −12 V. `D2` is a *parallel* path for the
umbilical, deliberately split so the instrument's 360 mA does not modulate the
analog rail's `Vf` — that argument is sound and is the best thing on the page.

So the phrase **"±12 V less two Schottky drops"**, which appears on both
`pitch-stage.md` and `mod-channels.md` `[repo]`, describes the total 24 V span,
not the per-rail headroom, and both pages use it *for* per-rail headroom. The
number comes out similar by coincidence; the reasoning is wrong and will
mislead the next person.

Analog rail current `[calc]`, `[gated]` on OPA2197 I_Q:

```
6 × OPA2197 × 2 amps × ~1 mA      ≈ 12 mA   [gated: I_Q per amplifier]
INA828 ~0.9 mA, LM311 ~3 mA, LM317+DAC ~2 mA
total on +12 V analog             ≈ 18 mA
1N5817 Vf at ~20 mA               ≈ 0.28 V  [gated: Vf curve, ti/vishay blocked]

+12.00 − 0.28 = +11.72 V          −12.00 + 0.27 = −11.73 V
```

**Three incompatible swing figures are in circulation** `[repo]`:

| Source | Claim |
|---|---|
| ADR 0006 L120–121 | rail ±11.65 V, *"an OPA2197 reaches ~±11.45 V"* — the only internally coherent version, 200 mV of saturation allowed |
| `pitch-stage.md`, `mod-channels.md` | *"±12 V less two Schottky drops reaches ~±11.45 V"* — conflates the rail with the output swing |
| **BOM row 13** | *"RRIO on ±12V reaches ~11.9V"* — **impossible** |

`[calc]`: 12.00 V minus even a best-case 0.25 V of Schottky at light current is
**11.75 V of rail**, and the *output* must sit below that by V_OL/V_OH. **11.9 V
is above the rail.** BOM row 13 is the line a person stuffing the board reads,
and it is the most optimistic of the three by 450 mV.

This document uses **rail ±11.70 V, output swing ±11.50 V** — the 200 mV
assumption is ADR 0006's, adopted here for continuity and marked
`[gated]` on the OPA2197's V_OL/V_OH-versus-load curve, which is the single
parameter every margin below depends on.

**Not accounted for anywhere:** Eurorack bus rails are commonly ±12 V ±5 %, and
a loaded case sags. At +11.4 V of bus, the rail is +11.12 V and the swing
+10.92 V `[calc]` — which still clears ±10.000 V at the jack but **not** the
±11.00 V the mods need at the op-amp pin into a 10 kΩ load (§3.1).

### 4.2 Headroom per stage

| Stage | Demanded at the op-amp pin | Margin to ±11.50 V |
|---|---|---|
| Pitch, no load | +7.745 V `[calc]` | 3.76 V |
| Pitch into 10 kΩ | +8.50 V `[calc]` | 3.00 V |
| Mod, jack at ±10.000 V, light load | ±10.000 V | 1.50 V |
| **Mod, jack at ±10.000 V into 10 kΩ** | **±11.00 V** `[calc]` | **0.50 V** |
| Breath, hard blow at GAIN = 2.5× | **+10.98 V** `[calc]` | **0.52 V** |
| **Breath, full sensor range at 2.5×** | **+24.85 V demanded** `[calc]` | **clips** |
| Instrument buffer, bottom of range | +0.152 V on a 0 V rail | `[gated]` on V_OL |
| REF5050 buffer | 5.000 V on 0/+12 V | 7 V |

Pitch's `[calc]`, worth showing because jack-side feedback moves the question
from the jack to the op-amp pin and nobody has noticed:

```
I_fb · 11.2 kΩ = (V_o − V_dac),  V_jack = V_o − I_fb · 1 kΩ = 7.500 V, V_dac = 5.000
 → I_fb · 11.2k = 2.500 + I_fb · 1k
 → I_fb · 10.2k = 2.500  →  I_fb = 245 µA,  V_o = 7.745 V

into a 10 kΩ patch load:
 V_o = 7.500 + (7.500/10 kΩ + 245 µA) × 1 kΩ = 7.500 + 0.995 = 8.50 V
```

At +7.5 V this is harmless. At ±10 V — i.e. if jack-side feedback is ever
extended to the mod channels to fix D2 — it is **not**: the op-amp would need
±11.00 V into 10 kΩ, 0.50 V of margin, and a low-impedance load would clip.
**Any fix for D2 must budget the op-amp pin, not the jack.**

---

## 5. Stability

### 5.1 Pitch — the split loop is sound, and here is the number that says so

The page calls this *"the highest-risk item on the page"* `[repo]` and defers
it to E9 without arithmetic. The arithmetic is favourable and worth having,
because it also yields the acceptance criterion.

Network `[repo]`: `R1` 10 kΩ from the summing node to the buffered `V_ref`;
feedback leg from the **jack** = `R-OUT-PROT` 1 kΩ + `R2` 10 kΩ + `TRIM-GAIN`
0–200 Ω = **11.2 kΩ**, with `R-OUT-PROT` now *inside* the loop;
`C-FB-PITCH` 1 nF from the **op-amp output** to the summing node.

```
[calc]
DC noise gain (op-amp-referred) = 1 + 11.2/10 = 2.12
Transfer to the jack            = 1 + (10.0 + 0…0.2)/10 = 2.000 → 2.020
Feedback-leg pole  = 1/(2π × 11.2 kΩ × 1 nF) = 14.21 kHz     ← D13
β rises monotonically 0.472 → ≈1 as C takes over: a phase LEAD, no dip,
   therefore no peaking from the network itself.
```

**D13:** the page and BOM row `C-FB-PITCH` both call the corner **15.9 kHz**,
from 10 kΩ × 1 nF `[repo]`. `R-OUT-PROT` is inside the leg now, so the real
corner is **14.2 kHz** — a 12 % error that E9 will measure and someone will
file as a bug. (The same 15.9 kHz appears in `latency-budget.md` L64 `[repo]`.)

The stability condition is the **separation** between the feedback handover and
the first jack-side pole `[calc]`:

```
jack-side pole = 1/(2π × 1 kΩ × C_cable)

1 m patch,   ~100 pF  → 1.59 MHz   → 112× above handover
3 m + mult,  ~500 pF  →  318 kHz   →  22× above handover
```

**22× is the whole stability argument**, and it holds. The E9 acceptance
criterion should be that ratio measured against the worst cable in the studio,
not "does it ring" — a stage with 3× of separation also does not ring on the
bench and falls over on someone else's patch.

**The build that breaks it** is a jack-side capacitor. The deleted
`C-FILT-PITCH` at 10 nF would put the jack pole at 1/(2π × 1 kΩ × 10 nF) =
**15.92 kHz** `[calc]` — **1.1× the handover instead of 22×**, two poles
co-located with roughly 700 of loop gain at that frequency `[calc]:
A_OL/NG ≈ (10 MHz/14.2 kHz)/1 = 704, [gated] on GBW`. That is the ringing case,
and it is the only capacitor value in the module that produces it.

The page's table and the BOM have both been corrected to delete it. **The
residual risk is that it comes back**, because `C-FILT-MOD` (82 nF) and
`C-OUT-BREATH` (330 nF) are the same class of part on the same 1 kΩ and are
entirely safe — those two stages take feedback at the op-amp output, so
`R-OUT-PROT` isolates the cap. **The rule is per-stage, not per-board**, and
nothing in the repo states it where a layout engineer will read it. A one-line
`DNP — see pitch-stage.md §stability` on the pitch jack footprint is the cheap
insurance.

### 5.2 D7 — jack-side feedback saturates the amp on a shorted jack

With the DC loop closed at the jack, the amplifier tries to hold **the jack** at
its commanded voltage through 1 kΩ. Short the jack and it cannot, so it runs to
the rail `[calc]`:

```
old (feedback at the op-amp output): op-amp holds +7.500 V, delivers 7.5 mA,
                                      stays in its linear region
new (feedback at the jack):          op-amp saturates at ~+11.50 V,
                                      delivers 11.5 mA, is OPEN LOOP
```

Higher current (11.5 vs 7.5 mA, both comfortable `[gated]`), but the real cost
is **saturation recovery**. A patch cable shorts tip to sleeve every time it is
inserted or withdrawn — that is how a 3.5 mm jack is built. So **every patch
into the PITCH jack momentarily drives the amplifier open-loop**, and pitch
returns only after the output recovers from overload. On a 1 V/oct output during
a held note that is an audible glitch, and its duration is `[gated]` on the
OPA2197's overload recovery time.

This failure mode is **new**, created by the jack-side-feedback redesign, and
neither `pitch-stage.md` nor ADR 0006 mentions it. It is the price of the
load-independence, and it is probably worth paying — but it should be on the
page, and E9 should scope a cable insertion, not only a cable.

### 5.3 D8 — the gain trim has no authority in the direction it needs

`TRIM-GAIN` is 200 Ω **in series with `R2`** `[repo]`, so `[calc]`:

```
gain at the jack = 1 + (10.000 kΩ + R_trim)/10.000 kΩ
R_trim = 0 Ω   → 2.000     R_trim = 200 Ω → 2.020
range: 2.000 → 2.020, ONE-SIDED UPWARD, 0 → +2.0 % of the ratio
```

With the LT5400 at 1:1 and the load divider eliminated by jack-side feedback,
**the nominal design point is exactly 2.000 — the trimmer's bottom stop.** A
perfect board trims to zero rotation, and every error that needs gain **below**
2.000 (a high DAC reference, LT5400 ratio error of the wrong sign, firmware
scale) is **untrimmable in hardware**. A trimmer whose nominal is at an end
stop is a trimmer with half its purpose.

The page contradicts itself about this within two screens `[repo]`:

- *"the divider is inside the feedback and the error is identically zero for
  any load"*
- *"Trim with the real patch connected… that error is what the gain trim's
  **±5 %** range exists to absorb"*

Both cannot hold. The first is correct. The second is left over from the
pre-redesign page, and it still says **±5 %** — which is wrong twice: the range
is 2 %, not 5 % (`[calc]`: 200 Ω/10 kΩ = 2.0 %, and BOM row 105 agrees
`[repo]`), and it is one-sided, not ±.

**Two more ±5 % fossils survive the correction** `[repo]`:

- *"What limits accuracy"* row: *"Cermet at ~100 ppm/°C contributing ~5 % of
  the ratio"* → the 0.4–2.4 cent range in that row is derived from the wrong
  fraction.
- *"Still open: Whether `TRIM-GAIN` is 1 kΩ or 500 Ω. ±5 % of a 10 kΩ ratio
  wants ~1 kΩ"* → the Values table and BOM now say 200 Ω. Three values on one
  page.

**The 6× dispute in that row can actually be closed** `[calc]`, with the
correct 2 % fraction:

```
ratio tempco = trim_fraction × cermet_tempco
             = 0.020 × 100 ppm/°C = 2.0 ppm/°C        [gated: cermet tempco]
over 10 °C   = 20 ppm of gain
at +7 V      = 7 V × 20e-6 = 140 µV
in cents     = 140 µV / 1 mV × 1.2 = 0.17 cents
```

So at 200 Ω the term is **~0.17 cents**, below the page's own 0.4 figure and
14× below ADR 0006's 2.4. Both disputed numbers were computed for a 1 kΩ
trimmer at 5–9 % of the ratio; BOM row 105 already made exactly this argument
when it changed the part `[repo]`. **The row should be rewritten and the
dispute retired**, and `TRIM-GAIN` is then no longer "the largest line here" —
`LT5400` tracking and the DAC reference are. `[gated]` on the cermet's actual
tempco, which is ±100 ppm/°C for good parts and ±250 ppm/°C for cheap ones; at
250 ppm/°C the term is 0.42 cents, still below everything else.

### 5.4 Mod channels, breath output — isolation works, with one gap

Both take feedback at the op-amp output and both put their cap on the jack side
of 1 kΩ `[repo]`. At any frequency where the cap matters the op-amp sees
approximately 1 kΩ resistive: at 1 MHz, 82 nF is 1.9 mΩ and 330 nF is 0.5 mΩ,
so the load is 1 kΩ `[calc]`. **Correctly isolated. No capacitive-load
stability issue on any of the five jack-driving stages.**

The BOM says this in two places, in capitals, with the reason `[repo]`. It is
the best-documented decision in the module.

**The gap is D10** — the breath stage's *feedback* network, not its load.

### 5.5 D10 — the breath gain/offset stage is unspecified, and the one place stray capacitance bites

`breath-receive-stage.md` draws it as a block and says `[repo]`: *"Its own
values, its offset reference… and whether the gain pot's wiper needs a buffer
are E10 work."* There are **no values anywhere in the repo** — not in the page,
not in the BOM beyond `POT-BREATH` (B50k linear, 9 mm Alpha, ×2 `[repo]`).

That matters because it is the only stage whose feedback network runs at tens
of kilohms **through panel wiring** `[calc]`, with `Rf` = 50 kΩ, an assumed
`Rin` = 20 kΩ (needed for the 2.5× the commissioning procedure asks for), and
~20 pF of inverting-node capacitance from the pot, its wiring and the pad:

```
noise-gain zero = 1/(2π × (Rf ∥ Rin) × C_in)
                = 1/(2π × 14.3 kΩ × 20 pF) = 557 kHz
noise gain at DC = 1 + 50/20 = 3.5
crossover without C_in = GBW/NG = 10 MHz/3.5 = 2.86 MHz   [gated: GBW]
```

The zero at 557 kHz is **below** the crossover, so the noise gain is rising at
+20 dB/decade where the open-loop response falls at −20 dB/decade: a
**40 dB/decade rate of closure**, which is the textbook peaking-or-ringing
condition. The standard fix is a small capacitor across `Rf`
(≈ 1/(2π × 50 kΩ × 500 kHz) = 6.4 pF `[calc]`, in practice 10–22 pF).

**No feedback capacitor is specified for this stage.** The pitch stage, whose
feedback impedance is **five times lower** and which has no panel wiring at all,
got `C-FB-PITCH`. The stage that actually needs one has none.

Compare the mods, which are fine `[calc]`: `R1 ∥ R2` = 10 k ∥ 30 k = 7.5 kΩ
against ~5 pF of on-board stray gives a zero at 4.24 MHz, above the 2.5 MHz
crossover (NG = 4) — no rate-of-closure problem, no cap needed. The difference
is entirely the panel pot.

`[gated]` on GBW and phase margin; `[calc]` on everything else; the `Rin`,
`C_in` and `Rf` values are **assumptions in place of a specification that does
not exist**, which is itself the finding.

### 5.6 D1 — the REF5050 buffer drives 100 nF with no isolation

**This is the most serious finding in the audit and the only place the part is
not adequate as connected.**

The topology, assembled from three files `[repo]`:

- ADR 0003 L468: `umbilical +12V ──[REF5050 5.000V]──[OPA2197 ½ buffer]──┬── MPXV4006DP VS`
- BOM row 26: REF5050 *"Buffered by half of `U-BUF`"*
- BOM row 78 (`C-DECOUPLE-CARRIER`, qty 7): *"One per supply pin: MCP3202,
  REF5050 in, OPA2197 +12V, 74AHCT125, **MPXV4006DP**, and both R-78E5 inputs"*

`[calc]` that list: 1+1+1+1+1+2 = 7 ✓, so the `MPXV4006DP` entry is real and
there is a **100 nF X7R sitting on the sensor's `VS` pin, which is the op-amp
buffer's output node, with nothing in between.**

A unity-gain follower has the least phase margin of any configuration — β = 1,
nothing to spend. Load capacitance forms a pole with the amplifier's open-loop
output resistance, **inside the loop** `[calc]`:

```
f_pole = 1/(2π × R_o × C_L)
       = 1/(2π × 75 Ω × 100 nF) = 21.2 kHz     [gated: R_o, assumed 75 Ω]
```

That is roughly **three decades below a ~10 MHz crossover** `[gated: GBW]`, so
the loop carries an additional ~90° of lag from 21 kHz all the way out to
crossover. **The expected outcome is sustained oscillation, or at best a
violently ringing response to any supply-current step in the sensor.**

The consequence is not cosmetic. ADR 0003's own argument for this rail
`[repo]`: *"The MPXV4006DP is ratiometric so its supply **IS** its scale
factor"* (BOM row 26), and L435: *"Its output is a fraction of its own supply."*
**Anything that appears on `VS` appears on the breath signal, multiplied by the
whole downstream chain.** A megahertz oscillation on `VS` will rectify in the
sensor's own bridge and appear as a DC offset that moves with temperature — the
symptom being a breath zero that will not stay put, which is precisely the thing
`TRIM-BREATH-ZERO` exists to set once and forget.

`[gated]`, decisively, on the OPA2197's **stable capacitive load in unity gain**
— the one specification that settles it. Note what is *not* gated: **no
general-purpose precision op-amp is unconditionally stable into 100 nF in unity
gain.** Parts that are (the "stable into any capacitive load" families) are
marketed on that basis and are a different product class. The risk is high
enough to act on before the curve can be read.

**Fixes, and why the obvious one is wrong:**

- ✗ **Plain series resistor** between the buffer and `VS`, feedback taken
  before it. The sensor draws ~10 mA `[gated: MPXV4006DP I_S]`, so 10 Ω costs
  **100 mV on 5.000 V = 2.0 % of scale** `[calc]` — against a REF5050 specified
  at ±0.05 % and 3 ppm/°C `[repo]`. This destroys the entire reason the
  reference is there.
- ✓ **Isolation resistor *inside* the loop** — 10 Ω in series, with the buffer's
  feedback taken from the **sensor's `VS` pin**, after it. The capacitor is then
  outside the loop's high-frequency path and the DC error is divided by the loop
  gain, i.e. zero. **This is the same trick the pitch stage already uses**
  (feedback tapped past `R-OUT-PROT`), and the same trick `C-FILT-MOD` relies on.
  The project has the pattern; it just has not applied it here.
- ✓ **Series-RC snubber** (≈10 Ω + 100 nF) to ground in parallel with the
  decoupler — no DC drop at all, and it damps without touching the loop.
- ✓ **Reduce the decoupler** to a value the (unreadable) C_LOAD curve permits,
  and add local bulk behind a small series R.

**Whatever is chosen, the buffer needs a stated C_LOAD limit in the BOM row.**
`U-BUF` (row 27) currently records only that it runs on +12 V `[repo]`.

**And this is the bad package pairing** (§6): `U-BUF`'s other half is the
breath buffer itself, whose output is the instrument's principal expressive
signal. ADR 0003 L477-478 chose that pairing for a reason of convenience —
*"costs nothing, because the other half of the package is the breath buffer
itself"* `[repo]` — and it is the one pairing in the project where a half in
trouble lands directly on a half that matters, through the shared supply pins
and the shared die.

---

## 6. The shared-package question — answered with arithmetic, not folklore

**D17 first:** nothing in the repo assigns any half to any package. The BOM
gives `U-OPA-PITCH` qty 6 and a prose list `[repo]`; no page maps stages to
packages. **The pairing will therefore be decided by whoever lays out the
board, from the schematic's reference designators.** That alone is worth a line
in `pitch-stage.md`.

The brief asks about three coupling mechanisms. All three were computed. **Two
are non-issues by three orders of magnitude, and saying so is the finding** —
the reflexive "never pair a hot output with a precision reference buffer" does
not survive contact with these numbers.

### 6.1 Thermal coupling — 3 orders below the budget

Worst half-dissipation anywhere in the module `[calc]`:

```
mod channel, jack shorted at +10.000 V:
  output device drops (11.70 − 10.00) = 1.70 V at 10.0 mA = 17 mW

pitch, jack shorted, worst point mid-travel (+5 V):
  output device drops (11.70 − 5.00) = 6.70 V at 5.0 mA = 34 mW   ← worst

package rise = 34 mW × 120 °C/W = 4.1 °C        [gated: SOIC-8 θJA]
far half sees roughly half the gradient          ≈ 2 °C
Vos shift on the far half = 2 °C × 1 µV/°C = 2 µV   [gated: Vos drift]
```

At pitch, 1 mV of output offset = 1.2 cents (`pitch-stage.md` `[repo]`), so
2 µV = **0.0024 cents** `[calc]`. Against a budget where the smallest tabulated
line is 0.1 cents, thermal coupling is **40× below the smallest thing anyone
bothered to write down**.

Even the pitch amplifier paired with its own reference follower — the textbook
"don't do that" — is fine, and in fact **should** be done: see §6.4.

### 6.2 Supply-pin coupling — 3 orders below the budget

Worst dynamic current at a package's supply pin is a mod channel stepping 20 mA
into its 82 nF (§3.1) `[calc]`:

```
20 mA through ~0.5 Ω of local decoupling network impedance at 100 kHz
                                                  [gated: layout, PSRR]
  = 10 mV at the V+ pin
PSRR at 100 kHz ≈ 50 dB  → 32 µV of apparent Vos on the co-packaged half
worst case: that half is the mod-offset follower
  → 32 µV × k=3 appears on ALL FOUR mod outputs = 96 µV
  → 96 µV on a 20 V span = 4.8 ppm
```

Against the ±81 mV zero tolerance the page already accepts `[repo]`, that is
**800× inside**. Not a reason to choose pairings either.

### 6.3 A fault in one half taking the other

The clamp diodes go to the **rails**, not to the package's supply pins (BOM row
52 `[repo]`), and the rails are shared by all six packages regardless of
pairing. So a back-driven jack is a rail event, not a package event. **No
pairing-specific fault mechanism exists in the module.**

The one place where a fault in one half genuinely reaches the other is **D1**,
on the carrier, and it reaches it through a die and a supply pin that a
100 nF-induced oscillation will be sitting on. That pairing was not chosen for
electrical reasons and should be reconsidered as part of fixing D1 — though the
correct fix is to stop the oscillation, not to re-partition around it.

### 6.4 Recommended assignment — chosen on single-fault scope

Since no electrical coupling is large enough to matter, the criterion should be:
**a dead package should lose one thing, not two unrelated things.**

| Package | Half A | Half B | Why |
|---|---|---|---|
| U1 | Pitch amp | Pitch `V_ref` follower | Same DC-critical chain; a failure loses pitch and nothing else. **Also measurably better DC** — see below |
| U2 | Mod 1 | Mod 2 | |
| U3 | Mod 3 | Mod 4 | |
| U4 | Mod-offset follower | Breath `REF`-zero buffer | Both set-once reference buffers, both DC, both µA |
| U5 | Breath gain/offset | (spare, or the −2.5 V inverter that fixes D3) | |
| U6 | spare | spare | |

**Explicitly do not pair a mod channel with a breath stage** — that is the only
combination where one dead package takes two unrelated performance outputs.

**U1 is better than two packages, and here is why** `[calc]`. The pitch output
offset from the two amplifiers' input offsets is:

```
V_offset(out) = (1 + k)·Vos_A − k·Vos_B = 2·Vos_A − 1·Vos_B

two packages, independent drift δ:  √(2² + 1²) · δ = 2.24 δ
one package, common drift δ (same die, same temperature):  2δ − δ = δ
```

**A 2.24× improvement in drift from a free placement decision**, and it is the
opposite of what the "keep the reference buffer away from the output stage"
reflex would tell you to do. The thermal penalty is the 0.0024 cents computed in
§6.1.

---

## 7. Offset and drift — which stages are actually DC-accurate

| Stage | Offset appears at the output as | Threshold that matters | DC-critical? |
|---|---|---|---|
| Pitch amp | Vos × (1+k) = **×2** | 1 cent = 833 µV out → Vos budget **417 µV** `[calc]` | **Yes** |
| Pitch `V_ref` follower | Vos × k = **×1** | 1 cent = 833 µV out → Vos budget **833 µV** `[calc]`; trimmed at commissioning, so only *drift* counts | **Yes** |
| Mod 1–4 | Vos × 4 | own ±81 mV resistor-tolerance window `[repo]` | No — swamped ~1000× |
| Mod-offset follower | Vos × 3, common to all four | same ±81 mV | No |
| Breath `REF` buffer | adds to the 0.437 V null | nulled by `TRIM-BREATH-ZERO` at build | No (drift only) |
| Breath gain/offset | panel knob downstream | — | No |
| Instrument buffer | Vos on 0.2–4.8 V | panel GAIN + `TRIM-BREATH-ZERO` downstream | No |
| REF5050 buffer | Vos on 5.000 V → ratiometric scale | 25 µV/5 V = **5 ppm** `[calc]`, against the REF5050's own ±500 ppm initial `[repo]` | No |

**Exactly two of the twelve halves have a DC-offset requirement worth naming,
and both are on pitch.** Even there the margin is enormous: any precision
op-amp's Vos is 10–40× inside a 417 µV budget `[gated: OPA2197 Vos]`.
`pitch-stage.md`'s accuracy table already says so — *"OPA2197 offset drift
< 0.1 cents"* `[repo]` — and that is the one line in the table this audit
confirms without amendment.

**Consequence for the part choice:** the "low-drift" half of the selection is
doing work on **2 of 12 halves**, and the "RRIO" half on **0 of 12** (§2). BOM
row 13's description implies both properties are needed throughout. Under
ADR 0004's one-part rule that is a documentation defect rather than a cost
defect — but it is the sentence a substitution would be judged against.

---

## 8. The breath output stage in detail — D3 and D6

### 8.1 The signal, end to end

`[calc]` from `breath-receive-stage.md` `[repo]`:

```
sensor pedestal at rest       +0.200 V (spec 0.152–0.378 V)
sensor at 6 kPa full range    +4.800 V
in-amp, G_eff = 2.1611, REF = +0.437 V:
  at rest   −2.1611 × 0.200 + 0.437 =  0.000 V  ✓
  at full   −2.1611 × 4.800 + 0.437 = −9.937 V
  span 2.1611 × 4.600 = 9.941 V                  ✓ matches the page's 9.94 V

real playing, ~2.65 kPa of 6 kPa:
  sensor = 0.200 + (2.65/6) × 4.600 = 2.232 V
  in-amp = −2.1611 × 2.032 = −4.391 V            ✓ matches "roughly 4.5 V"
```

(The page's narrative line *"0 V at rest, **−9.6 V** at full"* `[repo]` does not
match its own derivation table's 9.94 V. Minor, but they are in the same file.)

### 8.2 D6 — it clips at the top of the GAIN knob

Commissioning `[repo]`: *"The downstream stage needs about **0.6× to 2.5×**"*.

```
[calc], against an output swing of +11.50 V (§4.1):
hard blow at 2.5×       = 4.391 × 2.5 = +10.98 V   → 0.52 V of margin
                                                     BEFORE the OFFSET knob
full sensor range at 2.5× = 9.941 × 2.5 = +24.85 V → clips at +11.50 V
clipping begins at        11.50/2.5 = 4.60 V at the in-amp
                        = 4.60/9.94 = 46 % of sensor range
```

So at the top of the GAIN knob the jack saturates above **46 % of the sensor's
range** — reached by an overblow, a sneeze, or squeezing the mouthpiece. And
the saturated level, **+11.50 V**, is 1.5 V outside the ±10 V convention
ADR 0006 L78 states for this module `[repo]`.

Recovery from that saturation is `[gated]` on overload recovery time, same
parameter as D7.

**This is not an argument for a different op-amp** — no part on ±12 V reaches
+24.85 V. It is an argument that the GAIN knob's top of travel should be
limited by a fixed resistor so the stage cannot be set into saturation, which
costs one resistor and is exactly the specification D10 says does not exist.

### 8.3 D3 — the OFFSET knob can only go the wrong way

The stage is **inverting** (`breath-receive-stage.md` `[repo]`, and BOM row 28
`[repo]`), chosen deliberately: *"an inverting summer does gain and offset with
two pots into one virtual ground, where a non-inverting stage would have the
offset injection interact with the gain setting."*

An inverting summer's offset term is `−(Rf/Roff)·V_off`. **A positive reference
moves the output negative.**

The only reference node the module has is the buffered **+2.500 V** — which is
the node `breath-receive-stage.md`'s "Still open" nominates: *"its offset
reference (the buffered `VREFOUT` created for pitch is the obvious node)"*
`[repo]`. And the rest point is already 0 V, because `TRIM-BREATH-ZERO` nulls
the pedestal.

```
[calc]
rest point = offset term = −(Rf/Roff) × 2.500 V  ≤ 0 V, always
POT-OFFSET authority: 0 V → negative only
```

**So the panel OFFSET knob can only push the breath jack down from 0 V into
negative CV**, which most VCAs and VCFs ignore. The useful direction — lifting
the rest point so a VCA idles slightly open, or so a filter sits above its
cutoff floor — is **unreachable**.

This is the *same defect class* the breath page removed earlier in its own
narrative. Quoting it `[repo]`: *"the DAC channel proposed to drive `REF` is
unipolar 0–5 V — it can only push the floor up… an auto-zero with authority in
one direction only."* That was correctly identified and fixed at the in-amp
`REF` pin. **It reappeared at the panel knob, one stage downstream, and nobody
noticed because that stage is drawn as a block.**

**And the obvious workaround is blocked by the topology choice.** Injecting the
offset at the **(+)** input instead gives `+(1 + G)·V+` — the right direction,
but multiplied by `(1 + G)`, so the GAIN knob moves the offset. That is
precisely the interaction the inverting topology was chosen to avoid, in the
page's own words. **The topology choice and the required offset polarity are in
direct conflict, and the module has no negative reference to resolve it with.**

**Fix, and it is cheap:** one spare half (there are 2–3, §1.1) as a −1 inverter
off the existing buffered +2.500 V, giving **−2.500 V**. `POT-OFFSET` then spans
−2.500 → +2.500 V, injection stays at the virtual ground, direction is bipolar,
and the gain/offset independence the topology was chosen for is preserved
intact. `[calc]`: that inverter's own load is one `Roff` of tens of kilohms,
a few hundred microamps, and its Vos lands on a panel knob — no DC requirement
at all.

Note the second-order benefit: generating −2.500 V from the *same buffered node*
means the two ends of `POT-OFFSET` track each other and track the DAC's
reference, so the rest point does not drift against the signal.

---

## 9. D4 — closed in the repo mid-audit; D4b is what is left

**This section was written against the page as it stood, and the page changed
underneath it.** `R1b` — a matching 1 kΩ in the `AGND` leg — has been added,
together with the 60.2 dB arithmetic below, a `C_cm` ±1 % tolerance
requirement, and the 1206 uprating of `R1`. The analysis is retained because it
was derived independently and **confirms the page's numbers exactly**, and
because **D4b** — the BOM row that has not followed — is live.

### 9.1 What the defect was, and the arithmetic that confirms the fix

`breath-receive-stage.md`, as originally drawn `[repo]`:

- `R1` = 1 kΩ, **instrument end, on the signal conductor only** (BOM
  `R-SER-BREATH-INST` confirms: *"Series protection on the breath buffer output
  into the umbilical"* `[repo]`)
- `R2`, `R3` = 10 kΩ 0.1 %, module end, one per leg, **matched**
- `R4`, `R5` = 1 MΩ, bias return to module `AGND`, one per leg
- the `AGND` conductor ran **straight from the instrument's analog star to the
  cable**, with nothing in series — **this is what `R1b` now fixes**

So the two legs were **not** symmetric: signal leg = 1 kΩ + 10 kΩ = 11 kΩ,
`AGND` leg = 10 kΩ. `[calc]`:

```
signal leg divider = 1 MΩ / (1 MΩ + 11 kΩ) = 0.9891196
AGND   leg divider = 1 MΩ / (1 MΩ + 10 kΩ) = 0.9900990
difference                                 = 0.0009794

common-mode → differential conversion = 9.794 × 10⁻⁴
CMRR ceiling = 20·log₁₀(1 / 9.794e-4) = 60.2 dB
```

**60.2 dB.** ADR 0003 L356-360 states the link's requirement as **60 dB**
`[repo]` (*"3.3 kΩ unmatched leaves only ~24 dB of CMRR against the 60 dB the
link needs"*). **`R1` alone consumes the entire budget**, before the INA828
contributes its own, before the `REF` pin's source impedance, before the 0.1 %
tolerance on `R2`/`R3`.

The page spends two careful sections defending that same budget against smaller
threats `[repo]` — the `REF` pin's source impedance ("would spend the entire
60 dB budget"), and the single-ended-capacitor mistake ("would cap effective
CMRR at about 15 dB"). Both arguments are correct. **Both defend a budget that
`R1` has already spent**, and `R1` is in the same drawing.

The gain derivation *does* use the 0.98912 figure — *"Loss in the 2 × 1 MΩ bias
pair against 2 × 11 kΩ series | ×0.9891"* `[repo]` — so the asymmetry was
computed and then applied only to the **differential** gain. The **difference
between the two legs**, which is the CMRR term, was never taken. The number was
in hand and the wrong thing was done with it.

**There is also an AC term on top** `[calc]`:

```
leg time constants against C_cm 1.5 nF:
  signal leg  11 kΩ × 1.5 nF = 16.5 µs
  AGND   leg  10 kΩ × 1.5 nF = 15.0 µs
  10 % mismatch → CMRR degrades with frequency above ~10 kHz
```

which undercuts the stated purpose of making `C_diff` ten times `C_cm`.

**The fix, now in the page:** a matching **1 kΩ in the `AGND` leg at the
instrument end** (`R1b`). It costs nothing in signal terms because `AGND` is an
in-amp input, not a return — both `breath-receive-stage.md` and
`power-entry.md` say so explicitly `[repo]` — so it carries only the ~5 µA of
bias current, and 5 µA × 1 kΩ = 5 mV of common-mode offset, rejected by the
in-amp `[calc]`. It restores both the DC balance and the RC balance in one part.

Moving `R1` to the module end instead would **not** have worked: `R1`'s second
job is *"it also isolates the OPA2197 from ~200 pF of cable capacitance"* (BOM
row 66 `[repo]`), which only happens at the instrument end. Adding the twin is
the right call.

### 9.2 D4b — the BOM has not followed

`breath-receive-stage.md` Component values, current `[repo]`:

| Ref | Value |
|---|---|
| `R1` | 1 kΩ 1 %, **1206 ≥250 mW** |
| `R1b` | 1 kΩ 1 %, **1206** |

`bom.csv` row 66, current `[repo]`: `R-SER-BREATH-INST`, **qty 1**, **0805**,
and the note still describes a single resistor (*"R1 in
hardware/module/breath-receive-stage.md"*).

**Two mismatches, and both are unretrofittable**: these parts are inside the
bonded instrument body (the page says so `[repo]`). The quantity must go to
**2** and the package to **1206**. The page's own power arithmetic is the
reason `[calc, confirmed]`:

```
sustained +12 V fault on BREATH — a case ADR 0003 calls designed-safe:
I = (12 − 0.2) / 1 kΩ = 11.8 mA      P = 11.8 mA × 11.8 V = 139 mW
against an 0805's ~125 mW
```

This is the same defect shape as **D9** on the module side, one board away, and
the BOM row that already carries the argument for `R-OUT-PROT` (row 42
`[repo]`) is the one that did not carry it across.

---

## 10. Loose ends found while counting

- **D15.** `pitch-stage.md` "Still open": *"The two spare LT5400 resistors…
  Worth a look when the mod channels are laid out"*, and BOM row 15: *"the other
  two are available for the mod channels, which want 1:3 (three sections against
  the fourth)"* `[repo]`. **Arithmetically impossible** `[calc]`: a 1:3 ratio
  from a quad needs three sections in series against the fourth — all four —
  and pitch has already taken two; and there are **four** mod channels, so even
  a correct 1:3 would serve one. And the mods use discretes (`R-MODGAIN`,
  8 off, 10 k/30 k `[repo]`). Three independent reasons; the note should be
  deleted from both files.
- **Stale arithmetic in `mod-channels.md`'s `CLR` section** `[repo]`: still
  `4.02 × (0 − 2.5) = −10.05 V` and `4.02 × Vdac ≈ +11.45 V`, and *"On the
  range: ±10.05 V uses the DAC's full 0–5 V span"*, and the parenthetical's
  *"±10.05 V has 1.4 V of margin"*. Under the adopted k = 3 the figures are
  −10.000 V and, for the firmware bug, **4 × 5.000 = +20 V demanded** — i.e. a
  hard rail, which is still the right conclusion by a wider margin `[calc]`.
  The *conclusions* survive; the numbers no longer match the drawing above them.
- **`R-OPAMP-IN`'s stated justification does not survive the power tree.**
  BOM row 51 and ADR 0006 L668-671 justify it by *"DAC on 5.21 V and op-amps on
  ±12 V do not come up together"* `[repo]`. But `power-entry.md` `[repo]` feeds
  the LM317 (and therefore AVDD) **from the module's own +12 V, through `D1`** —
  so AVDD cannot be present when +12 V is absent, and in the reverse window the
  DAC outputs are at 0 V and no clamp current flows. The part is still
  justified, by a **different** case the ADR does not name: a **−12 V** failure
  (open ribbon pin, blown `D3`, a rack whose negative rail comes up late) with
  +12 V and AVDD both alive, leaving the op-amp inputs at up to 5 V with `V−`
  absent. `[calc]`: 1 kΩ limits that to ~4.3 mA, `[gated]` on the OPA2197's
  absolute-maximum input current. Worth recording so the part is not deleted by
  someone who notices the stated reason is wrong.
- **The breath `REF`-zero buffer is the one DAC-domain op-amp input with no
  `R-OPAMP-IN`.** Row 51's list of seven is *"Pitch, mod 1-4, the mod offset
  buffer, the `VREFOUT` follower"* `[repo]` = 7 `[calc]`; the `REF`-zero buffer
  is driven from `VREFOUT` through `TRIM-BREATH-ZERO`, the same 5.21 V domain,
  and is not on the list. It is **protected by accident** — the 10 kΩ trimmer's
  own source impedance limits any clamp current to ≤ 0.5 mA `[calc]`. Fine in
  substance; the BOM's stated rule and its own list disagree.
- **`VREFOUT` carries one 10 kΩ trimmer, not two.** `TRIM-BREATH-ZERO` moved to
  the LM317 5.21 V rail during this audit `[repo]`, for a good reason the BOM
  states well: `VREFOUT` is disabled at power-on until firmware writes an
  enable, so the analog breath path must not depend on it. That leaves
  `TRIM-OFFSET` alone on `VREFOUT`, a constant ~250 µA `[calc]` — constant
  because a pot across a reference draws the same current at any wiper
  position, so nothing interacts. The residual is a fixed load-regulation shift,
  which by the pitch page's own argument is a pure **gain** term and is trimmed
  out `[repo]`. `[gated]` on the DAC8568's `VREFOUT` output current and load
  regulation.
- **The breath `REF` buffer's reference is now a regulator, not a reference**,
  and that is the right trade but it should be written down. `[calc]`, with an
  LM317's ~100 ppm/°C of output tempco `[gated]`:

  ```
  5.21 V × 100 ppm/°C            = 521 µV/°C on the rail
  scaled to REF (0.437/5.21)     =  44 µV/°C at the INA828 REF pin
  through the downstream ×2.5    = 110 µV/°C at the breath jack
  over a 20 °C warm-up           = 2.2 mV on a 10 V output
  ```

  That is **10× inside** the page's own unverified 20 mV warm-up figure
  `[repo]`, so it does not change the commissioning story. But `TRIM-OFFSET`
  (pitch) stayed on `VREFOUT` and this one moved, and the asymmetry is
  **correct and deliberate** — pitch already depends on the DAC for its signal,
  breath must not. Someone will eventually try to make the two consistent.
  Record why they must not.
- **The power-on state of stage 2 follows from the same fact, and contradicts
  what two files say about `CLR`.** If `VREFOUT` is disabled until firmware
  enables it `[repo]`, then in that window the pitch `V_ref` follower sees 0 V
  and pitch sits at `2·Vdac − 0`; `R-CLR-PD` holds `Vdac` at 0, so the output is
  **0 V**. Safe `[calc]`. But BOM row 54 and `mod-channels.md` both describe the
  cleared state as *"pitch subsonic"* — i.e. −2.500 V `[repo]`. **Both are safe;
  only one is documented.** Which one actually occurs depends on whether a
  hardware `CLR`, or the mis-framed-word failure `digital-and-supervision.md`
  warns about `[repo]`, also resets the internal-reference enable — `[gated]` on
  DAC8568 behaviour. Worth resolving, because *"pitch parks subsonic"* is the
  sentence someone will test against at E9.
- **The presence detect now hangs off stage 10, and that puts it in this
  audit's scope.** It was redesigned while this was being written. It no longer
  taps the sensor pedestal; it compares the **INA828's output** against
  **half the breath `REF`-zero buffer's output** (`digital-and-supervision.md`,
  BOM row 100 `[repo]`). Two consequences follow that neither file states.

  **D18 — the threshold sits inside the signal's own range.** Write `P` for the
  sensor's resting pedestal. The trim sets `V_REF = G·P` so the in-amp rests at
  0 V, and the threshold is `V_REF/2` `[calc]`:

  ```
  V_out = −G·V_s + G·P            threshold = G·P/2
  trips  when  −G·V_s + G·P > G·P/2
         →  V_s < P/2
  ```

  **The detect trips at exactly half the resting pedestal, whatever the
  trimmer is set to.** In pressure, at 0.7667 V/kPa `[calc: 4.600 V / 6 kPa]`:

  | Pedestal `P` | Trip at | Margin | In pressure |
  |---|---|---|---|
  | 0.152 V (bottom of the spec band) | 0.076 V | 0.076 V | **0.099 kPa ≈ 10 mm H₂O** |
  | 0.200 V (typical) | 0.100 V | 0.100 V | **0.130 kPa ≈ 13 mm H₂O** |
  | 0.378 V (top of the band) | 0.189 V | 0.189 V | 0.247 kPa ≈ 25 mm H₂O |

  Blowing moves the in-amp output *negative*, away from the threshold, so no
  amount of blowing trips it `[calc]`. **Drawing does.** Ten to twenty-five
  millimetres of water column is a gentle inhale, a released embouchure, or the
  thermal contraction of a 400 mm tube's dead volume during warm-up.

  The consequence chain is entirely documented, just never joined up `[repo]`:
  comparator → `OE` high → 74AHCT125 disabled → the DAC's `SCLK`/`DIN`/`SYNC`
  held by the DAC-side pulls → no `CS` edges → the 74HC123 is not retriggered →
  **99 ms → `CLR` → every CV output to zero scale, mid-phrase.**

  The "self-centring" property is real and is a genuine improvement over the
  fixed 100 k/10 k divider it replaced — but it centres the threshold in the
  **middle of the quiescent signal**, which is the worst available place for a
  signal that can move in both directions. The sensor is an MPXV4006**DP**; its
  own floor is only `P/0.7667` ≈ 0.26 kPa of draw below rest, so *any* threshold
  expressed as a fraction of `P` lands inside the inhale range.

  Moving the divider from 1:1 to **1:4** (threshold at `0.8·V_REF`) buys 1.6×
  `[calc: margin 0.8P instead of 0.5P]` and still leaves 0.2·`V_REF` ≈ 86 mV on
  the unplugged side, ~16× the hysteresis. That is a one-resistor improvement,
  not a cure. **The real decision is whether draw is a supported gesture.** If
  it is, the detect cannot live on this node at all. If it is not, say so on the
  page, because nothing currently does and the failure is silent and total.

- **D19 — the detect does not degrade the way the page says.**
  `digital-and-supervision.md` `[repo]`: *"if the reference dies, the threshold
  goes with it and the detect reads 'absent'."* Only for one of the two
  failures `[calc]`:

  ```
  REF buffer fails HIGH (output at a rail, +11.5 V):
    threshold = 5.75 V, in-amp output saturates below it → reads ABSENT  ✓

  REF buffer fails LOW (output at 0 V — a dead half, or an open trimmer wiper):
    V_REF = 0  →  threshold = 0 V
    unplugged:  in-amp output = G·0 + V_REF = 0 V      ← exactly ON the threshold
    alive:      in-amp output = −G·P + 0 = −0.432 V    ← below it
  ```

  With 5.4 mV of hysteresis the comparator simply **latches wherever it was**,
  and if it was reading "alive" it goes on reading "alive" with the cable
  unplugged — *"which is the exact fault the detector exists to catch"*, in the
  page's own words about the version before this one `[repo]`. An open trimmer
  wiper is the most likely single failure in the whole breath chain, because it
  is a mechanical contact that is turned once and then never again.

  A commissioning error produces the same state: step 1 of the procedure says
  only *"until the in-amp output reads 0 V"* `[repo]`, and `V_REF = 0` with the
  cable unplugged also reads 0 V at the in-amp output. **The procedure does not
  distinguish the correct setting from the failure.** Step 1 should read: *with
  the umbilical connected and the mouthpiece at rest*, and should also check
  that `V_REF` itself is in the 0.33–0.83 V band.

- **D18/D19 collide with D11, and the collision is layout-critical.** The
  hysteresis is now 5.4 mV `[calc: BOM row 100 gives 54 mV at 1 MΩ, so 10 MΩ
  gives one tenth]`. §3.4 computed the mod-channel cap-charging transient
  appearing at the in-amp output as **1.73 mV at 10 mΩ of shared `AGND`
  copper** — 32 % of the hysteresis, safe. **At 100 mΩ it is 17.3 mV, three
  times the hysteresis**, and a fast mod-channel step toggles the presence
  comparator, which stops the SPI, which clears every CV output 99 ms later.

  So the `AGND` return impedance between `C-FILT-MOD` and the in-amp's
  reference tap is not a layout nicety — **it is the difference between a
  working module and one whose CV outputs drop out when a modulation channel
  moves quickly.** Nothing in the repo states a budget for it. It should:
  **≤ 20 mΩ**, or the separate `AGND_SENSE` net of §3.4.

---

## 11. Gated parameters — everything this audit could not verify

Every conclusion above that depends on a number nobody could read. **Take these
off the datasheets before laying out.**

| # | Parameter | Which finding depends on it |
|---|---|---|
| 1 | **OPA2197 stable C_LOAD in unity gain** | **D1 — the decisive one** |
| 2 | OPA2197 open-loop output resistance R_o | D1 (the 21 kHz pole), §3.3 crosstalk |
| 3 | OPA2197 V_OL / V_OH vs load current | **every headroom margin in §4**; D6, D12 |
| 4 | OPA2197 linear and short-circuit output current | §3.1 (20 mA transient), D9 (16.4 mA) |
| 5 | OPA2197 GBW and phase margin | D10 (557 kHz zero), §5.1 (22× separation) |
| 6 | OPA2197 overload recovery time | **D7** (patch insertion), D6 (clipping) |
| 7 | OPA2197 Vos and Vos drift (µV/°C) | §7 budgets, §6.1 thermal arithmetic |
| 8 | OPA2197 quiescent current per amplifier | §4.1 rail arithmetic |
| 9 | OPA2197 PSRR vs frequency | §6.2 |
| 10 | OPA2197 absolute-max input current | §10, `R-OPAMP-IN` sizing |
| 11 | OPA2197 input CM range / input architecture | §2 — **moot as built**, matters only on substitution |
| 12 | 1N5817 V_f at ~20 mA, and its tempco | §4.1, D12 |
| 13 | INA828 `REF` pin input impedance | stage 10's load |
| 14 | MPXV4006DP supply current | **D1** (buffer dissipation, the 2 % series-R penalty) |
| 15 | MPXV4006DP offset tempco | already flagged unverified by the page `[repo]` |
| 16 | DAC8568 `VREFOUT` output current / load regulation | §10, two trimmers on it |
| 17 | 1206 thick-film power rating by series | **D9** (269 mW vs 250 mW) |
| 18 | SOIC-8 θJA | §6.1 |
| 19 | Cermet trimmer tempco (100 vs 250 ppm/°C) | D8 / §5.3, closing the 6× dispute |
| 20 | Whether 82 nF C0G exists in 1210 | already flagged by BOM row 67 `[repo]` |
| 21 | LM311 input bias current and input offset | D18/D19 margins |
| 22 | LM317 output tempco on the 5.21 V rail | §10, the breath zero's new drift term |
| 23 | MPXV4006DP behaviour below zero differential pressure | **D18** — how far the output actually falls on a draw |

---

## 12. Is the OPA2197 the right part?

**For eleven of the twelve halves: yes, comfortably, and in most of them it is
over-specified** — which is the intended outcome of ADR 0004's one-part rule and
not a criticism.

- **Input common-mode:** no stage uses rail-to-rail inputs (§2). The property
  BOM row 13 names as the part's defining feature is exercised **zero** times.
- **Output swing:** the binding cases are the mods into a low-impedance load
  (±11.00 V at the pin, 0.50 V margin, §3.1) and breath at maximum gain
  (clips, D6). Neither is fixed by a different op-amp — the mod case is fixed by
  jack-side feedback or by accepting the divider, and the breath case by
  limiting the GAIN knob.
- **Output current:** the largest demand is 20 mA transient into the mod caps
  and 16.4 mA in a plausible mis-patch (§3.1–3.2), both `[gated]` but both
  ordinary for a precision op-amp `[from memory]`.
- **Offset and drift:** required on 2 of 12 halves, with ~400 µV of budget where
  any precision part gives 10–40× margin (§7).
- **Stability:** every stage that drives a jack is correctly isolated by
  `R-OUT-PROT` (§5.4). The pitch split loop is sound with 22× of pole separation
  (§5.1).

**The one role where it is not adequate as connected is stage 12, the REF5050
buffer (D1)** — and the inadequacy belongs to the connection, not the part. No
general-purpose precision op-amp is unconditionally stable driving 100 nF in
unity gain. The fix keeps the OPA2197 and costs one resistor placed inside the
feedback loop, using a pattern the project has already worked out twice
elsewhere.

**The second place the part is doing less than the BOM claims is stage 8's
feedback network (D10)** — not because the OPA2197 is wrong, but because a
557 kHz noise-gain zero on a 50 kΩ panel-wired loop needs a 10–22 pF feedback
capacitor that nothing in the repo specifies.

**Recommended BOM edits, minimum set:**

1. Row 13: correct the list (ten items, not eleven), correct the spare count
   (two or three, not one), delete *"reaches ~11.9 V"*, and note that the
   instrument-side buffer is `U-BUF` on the carrier and outside this line.
2. Row 13 or 28: settle whether the breath stage is one half or two.
3. Row 27 (`U-BUF`): add a stated **C_LOAD limit** and the isolation
   arrangement (D1).
4. Row 42 (`R-OUT-PROT`): specify a series rated ≥ 400 mW, or state the
   output-to-output fault it does **not** survive (D9).
5. Row 66 (`R-SER-BREATH-INST`): **qty 1 → 2** and **0805 → 1206 ≥250 mW**, to
   match the page's `R1` + `R1b` (**D4b**). Both parts are inside the bonded
   body.
6. Add a row for the breath stage's feedback capacitor and its gain-limiting
   resistor (D10, D6).
7. Add a row for the −2.500 V inverter, or record that breath OFFSET is
   downward-only by design (D3).
8. Row 100 (`R-PRESENCE`): state the trip pressure in kPa, not just the
   voltage ratio, and settle whether draw is a supported gesture (**D18**).
   Consider 1:4 rather than 1:1.
9. `breath-receive-stage.md` commissioning step 1: specify *umbilical
   connected*, and add a check that `V_REF` lands in 0.33–0.83 V (**D19**).
10. State an `AGND` return-impedance budget (≤ 20 mΩ) or split `AGND_SENSE`
   (**D11**, and the D18/D19 collision).
