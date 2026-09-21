# Mod channels 1–4 — schematic

**Status:** Drawn 2026-09-21. Third module page, after
[breath](breath-receive-stage.md) and [pitch](pitch-stage.md).

Four identical channels at `Vout = 4·Vdac − 3·V_ref`, `V_ref` = **3.3333 V**
from DAC channel 7, built from `R-MODGAIN` 10k/30k 1 % discretes in a
two-resistor non-inverting form at **k = 3**.

> ADR 0006 originally specified `Vout = 4 × (Vdac − 2.5 V)` and contradicted
> itself about how to build it — its topology section offered a superseded
> LT5400 ratio, its calibration section ordinary 1 % discretes. Both halves are
> now corrected there. **Writing the old 2.5 V into channel 7 against the
> current network gives a −7.5…+12.5 V window and clips positive**, which is why
> `firmware/README.md` states the value rather than deriving it.

## The circuit — one channel of four

```
   DAC ch7 ──[1k]──┬── ½ OPA2197 ──┬── V_ref = 3.3333 V
   (shared)        │   follower    │   to all four channels
                   └───────────────┘   (~1.3 mA total into 4 × 10k)
                                   │
                          ┌────────┴────────┐
                          │                 │
                     [R1 10k 1%]     (ch3, ch4, ch5
                          │           identical)
                          │
   DAC ch2 ──[1k]──┐      │
   0…5 V           │      │
                   │  ┌───┴─────────┐
                   └──┤ +           │
                      │  ½ OPA2197  ├──┬── op-amp output
                   ┌──┤ −           │  │
                   │  └─────────────┘  │
                   │                   │
                   └──[R2 30k 1%]──────┤
                                       │
                            [D-JACK-CLAMP BAV99]── ±12 V
                                       │
                            [R-OUT-PROT 1k, 1206]
                                       │
                                       ├──[C-FILT-MOD 82nF]── AGND
                                       │
                                  MOD n jack
```

## Two resistors, not four — settled

The first version of this page argued that pitch collapsed to two resistors
because `A = 1 + B` was a boundary its numbers landed on, and that the mods miss
it. **That reasoning was wrong.** `A = 1 + B` is the defining identity of the
two-resistor non-inverting form, true for every ratio; the free parameter is
`V_ref`, not the ratio:

```
k = A − 1          V_ref = offset / (A − 1)
```

So the mods can take the same two-resistor form: **`k = 3`, with the shared
offset channel writing 3.3333 V instead of 2.500 V.** Eight resistors instead of
sixteen, one matching requirement instead of two per channel, and a 1:3 ratio
that three sections of an LT5400 give directly against the fourth.

**Crucially the safe-state property survives.** On `CLR` both `Vdac` and
`V_ref` go to zero, so `Vout = 0` — which is the whole reason the offset lives
on a DAC channel (below).

**Adopted, and it is drawn above.** Eight resistors instead of sixteen, and it
lands on **exactly ±10.000 V** where the four-resistor version needed a 40.2 kΩ
fudge to reach ±10.05 and still did not hit the number. The offset channel
writes 3.3333 V instead of 2.500 V, and `R-OPAMP-IN` comes back — correctly
this time, because the two-resistor form drives a true high-impedance (+) input
where a 1 kΩ costs nothing, unlike the four-resistor version where the input
resistor *was* the gain network.

| | Four-resistor difference amp | **Two-resistor, k = 3** |
|---|---|---|
| Resistors | 16 | **8** |
| Matching | two ratios per channel | **one** |
| Range | ±10.05 V (40.2 kΩ fudge) | **exactly ±10.000 V** |
| `R-OPAMP-IN` | unbalances it — 196 mV zero error | harmless, feeds a (+) input |
| Safe on `CLR` | `4X − 4X` = **0 for ANY uniform state** | `4X − 3X` = **X** — 0 V only because the grade is zero-scale |

*(A third option surfaced in the same research: four of four published designs
— Ornament & Crime, Westlicht PER|FORMER, Mutable Yarns, MTM Workshop Computer
— use a **single inverting amp** with the mid-reference on the (+) input, which
needs no buffer at all because that input draws no current. It inverts, which
is a firmware sign flip. The catch is that O&C and the PER|FORMER take that
reference from a passive divider off `VREFOUT`, which does **not** go to zero on
`CLR` — so all four jacks would slam to +10 V. The PER|FORMER avoids it by
disabling `CLR` entirely, which Woody cannot. Taking the reference from a DAC
channel keeps the inverting topology and the safe clear together.)*

## Values

| Ref | Value | Why |
|---|---|---|
| **R1** | 10 kΩ 1 % | To the shared reference |
| **R2** | **30 kΩ 1 %** | Feedback. `k = 3`, gain `1 + k` = **exactly 4** |
| **V_ref** | **3.3333 V** from DAC ch7, buffered | Shared by all four. Intercept is `k · V_ref` = 10.000 V |
| **C-FILT-MOD** | 82 nF C0G | 1.94 kHz, jack side of the 1 kΩ |

*(The four-resistor version this replaced used 40.2 kΩ against 10 kΩ, because
E24's 39 k would have given gain 3.90 and a jack that
stops at ±9.75 V, visibly short of the specified ±10. Going slightly over costs
nothing: an OPA2197 on ±12 V less two Schottky drops reaches ~±11.45 V, so
±10.05 V has 1.4 V of margin.

**Why `R-OPAMP-IN` was wrong on the old drawing, kept because it is a good
trap.** On the four-resistor version the 10 kΩ input resistor *was* the gain
network, so a 1 kΩ in series made the DAC leg 11 kΩ against the reference leg's
10 kΩ and the stage stopped being balanced — a deterministic **−196 mV** zero
error and +9.657 V instead of +10.05, more than twice the whole tolerance
budget. On the two-resistor form the same part feeds a (+) input that draws no
current, and costs nothing. Same resistor, same reason for existing, opposite
consequence, decided entirely by the topology around it.

**Tolerance — and this section has now been wrong twice.** The original said
"2.5 V × 2 % × 4 ≈ 50 mV", which evaluates to 200 mV and modelled only the zero
point. The replacement enumerated "sixteen corners of four 1 % resistors",
which is **the four-resistor circuit's answer, kept after the redraw**. There
are two resistors and four corners, and in two of them same-sign tolerance
cancels in the ratio:

| Term | Worst case | vs the four-resistor version |
|---|---|---|
| Zero point | **±50.5 mV** | 1.6× *better* |
| Span | **19.703–20.303 V** (−1.49 %/+1.52 %) | 1.33× *better* |

So the redraw improved both and the page claimed neither. About ±18 cents per
octave if a channel is assigned to something pitch-like.

**"One matching requirement instead of two" is true by count and misleading.**
The difference amp's zero was `2.5[b/(1+b) − b/(1+b)] = 0` for *any* absolute
ratio — it depended only on leg-to-leg matching. The two-resistor zero is
`2.5 − (10/3)k`, directly proportional to the ratio error. Fewer requirements,
but the deleted one was buying something. ADR 0006 says these channels need to be "linear
and repeatable, not calibrated", and they still are — but "repeatable" is doing
more work than the old number implied, and anything pitch-like belongs on
channel 1.

Buying the four sets from one reel makes it much better than worst case for
free, since reel-adjacent parts track.

**On the range:** ±10.05 V uses the DAC's *full* 0–5 V span. ADR 0006's
0.25–4.75 V window is a **pitch-channel reserve** — it exists to give firmware
±600 cents of offset authority on 1 V/oct — and does not apply here. Stated
because the two numbers look contradictory side by side and are not.

## The offset is a DAC channel, and that is the whole reason `CLR` works

This is the S4 fix, and it is worth stating where the circuit is, because the
circuit is what makes it true.

On a watchdog `CLR`, the C-grade DAC8568 (the grade is **locked** — it selects reference gain as well as reset state, ADR 0006) clears **every** channel to zero
scale (ADR 0006). Channel 7 goes to 0 V with the rest, so:

```
Vout = 4 × 0 − 3 × 0 = 0 V
```

All four jacks park at 0 V, which is the same state as rack power-on. **Had the
2.5 V come from a fixed divider or the internal reference directly**, `CLR`
would zero the signal channels and leave the offset standing, and every mod
jack would pin at `4 × 0 − 3 × 3.3333 = −10.00 V` — a hard rail on four outputs,
indefinitely, with no `MISO` to notice it.

The mirror-image failure is the one the review actually found: firmware
refreshing the five signal channels after a `CLR` and *not* channel 7, which
pins the jacks at `4 × Vdac` ≈ **+11.45 V**. That is closed by the
statelessness rule in `firmware/README.md` — refresh all six populated
channels every pass — and the latency budget already paid for it.

**The two-resistor form also made the DAC grade safety-critical**, which the
four-resistor form did not. `4X − 4X` is zero for *any* uniform reset state; 
`4X − 3X` is `X`. With the locked C grade that is 0 V and correct — but a B/D
part would put **+2.5 V on all four jacks** where the old topology gave 0 V
regardless. The grade lock is now load-bearing twice: once for reference gain,
once for this.

**So the offset channel is load-bearing in both directions**, and neither
direction is obvious from the schematic alone. It is written here because this
is the page someone will read while stuffing the board.

## One buffer, four loads

DAC ch7 drives one OPA2197 half; that half drives four 10 kΩ inputs in
parallel. At 2.5 V into 2.5 kΩ that is **1 mA**, comfortable for the part.

It wants its own `R-OPAMP-IN` on the way in, like every other DAC-driven
op-amp input (`R-OPAMP-IN` qty 7 covers pitch, the four mods, this buffer and
the `VREFOUT` follower).

**Do not be tempted to split it into four buffers.** One shared node means all
four channels share exactly the same offset error, so a residual appears as a
common shift across the mod set rather than as four channels disagreeing with
each other — which is both cheaper and more useful.

## The alternative topology, recorded rather than adopted

Prior-art research found that **four of four published designs** (Ornament &
Crime, Westlicht PER|FORMER, Mutable Yarns, MTM Workshop Computer) build this
stage as a **single inverting amplifier** with the mid-reference on the (+)
input, not as a four-resistor difference amp. It is genuinely simpler:

```
Vout = −(Rf/Rin)·Vdac + (1 + Rf/Rin)·V+
     = −4·Vdac + 5·V+        with V+ = 2.000 V  →  +10 V … −10 V
```

Two precision resistors instead of four, no matching requirement *between* two
legs, and the offset injection is free because the (+) input draws no current —
which also means the offset DAC channel would need **no buffer**, returning an
OPA2197 half.

It inverts, which is a firmware sign flip and costs nothing.

**The one thing to be careful about, and it is the thing that matters here:**
O&C and the PER|FORMER both take that reference from a *passive divider off
`VREFOUT`*. On a watchdog `CLR` the channels go to zero and the divider does
not, so `Vout = 5 × 2.0 = +10 V` — a hard rail on four jacks. The PER|FORMER
avoids this by disabling `CLR` entirely; Woody cannot, because the watchdog is
the whole answer to a processor two metres away.

Taking the reference from a **DAC channel** instead keeps the inverting
topology *and* the safe clear, because `CLR` zeroes it too. That is the version
worth considering, and it is strictly better than what is drawn above. Not
adopted unilaterally: it is a redraw of a settled page and the call belongs to
the author.

## Still open

- **Per-channel scale and offset are firmware, not hardware.** ADR 0006 puts
  source, scale, offset, curve and slew on the instrument's display. This stage
  is a fixed ±10 V window and stays that way.
- **Whether all four channels need the full ±10 V.** They are generic by
  decision, so yes for now — but if E10 finds that nothing in the rack wants
  bipolar on more than two of them, two channels could go unipolar 0–10 V and
  halve their resolution cost. Not a change to make speculatively.
