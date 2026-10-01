# Mod channels 1–4 — schematic

**Status:** Drawn 2026-09-21. Third module page, after
[breath](../breath-receive-stage/breath-receive-stage.md) and
[pitch](../pitch-stage/pitch-stage.md).

Four identical channels at `Vout = 4·Vdac − 3·V_ref`, `V_ref` = **3.3333 V**
from DAC channel 7, built from `R-MODGAIN-IN` and `R-MODGAIN-FB`, 10k/30k 0.1 % thin-film discretes, in a
two-resistor non-inverting form at **k = 3**.

> ADR 0006 originally specified `Vout = 4 × (Vdac − 2.5 V)` and contradicted
> itself about how to build it — its topology section offered a superseded
> LT5400 ratio, its calibration section ordinary 1 % discretes. Both halves are
> now corrected there. **Writing the old 2.5 V into channel 7 against the
> current network gives a −7.5…+12.5 V window and clips positive**, which is why
> `firmware/README.md` states the value rather than deriving it.

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `DAC ch7` | in | `module/dac8568` | `mod-reference` | The shared offset reference. Through `R-OPAMP-IN` into the follower's (+) input, and from there to all four channels |
| `DAC ch2`–`ch5` | in | `module/dac8568` | `dac-rail` | One signal channel per mod channel, through `R-OPAMP-IN` into the (+) input |
| `CLR` | — | `module/dac8568` | — | Not a net inside this circuit — it acts on the DAC. Listed because this stage's park-at-0 V property is entirely downstream of it, including for channel 7 |
| `MOD 1`–`MOD 4` | out | `module/panel` | — | The four panel jacks. Feedback is taken at the op-amp output, not at the jack, so `R-OUT-PROT` isolates `C-FILT-MOD` from the loop |
| `MODULE ANALOG +12V`, `MODULE ANALOG −12V` | in | `module/power-entry` | — | `D-JACK-CLAMP` returns to both rails |
| `AGND_MOD` | ref | `module/power-entry` | `dig-gnd-topology` | The module analog star, drawn `AGND`. `C-FILT-MOD` shunts to it. Not a return path — see the figure |

## The circuit — one channel of four

*Connectivity is **[`netlist.yaml`](netlist.yaml)**, not this drawing.
The drawing is a representation of it, `tools/check-netlist.py` checks that
the two agree, and where they do not the netlist wins. The drawing shows one
channel; the netlist writes out all four.*


```
   DAC ch7 ──[1k]──┬── ½ OPA2197 ──┬── V_ref = 3.3333 V
   (shared)        │   follower    │   to all four channels
                   └───────────────┘   (~1.3 mA total into 4 × 10k)
                                   │
                          ┌────────┴────────┐
                          │                 │
                     [R1 10k 0.1%]   (ch3, ch4, ch5
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
                   └──[R2 30k 0.1%]────┤
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

`A = 1 + B` is the defining identity of the two-resistor non-inverting form,
true for every ratio; the free parameter is `V_ref`, not the ratio:

```
k = A − 1          V_ref = offset / (A − 1)
```

*(The version of this argument that called `A = 1 + B` a boundary the mods
miss is in [`notes.md`](notes.md).)*

So the mods can take the same two-resistor form: **`k = 3`, with the shared
offset channel writing 3.3333 V instead of 2.500 V.** Eight resistors instead of
sixteen, one matching requirement instead of two per channel, and a 1:3 ratio
that three sections of an LT5400 give directly against the fourth.

**Crucially the safe-state property survives.** On `CLR` both `Vdac` and
`V_ref` go to zero, so `Vout = 0` — which is the whole reason the offset lives
on a DAC channel (below).

**Adopted, and it is drawn above.** Eight resistors instead of sixteen, and it
lands on **exactly ±10.000 V at the op-amp output** where the four-resistor
version needed a 40.2 kΩ fudge and still did not hit the number. **At the jack
it is less**, because `R-OUT-PROT` is outside the loop: `mod-jack-range`,
below. The offset channel
writes 3.3333 V instead of 2.500 V, and `R-OPAMP-IN` comes back — correctly
this time, because the two-resistor form drives a true high-impedance (+) input
where a 1 kΩ costs nothing, unlike the four-resistor version where the input
resistor *was* the gain network.

| | Four-resistor difference amp | **Two-resistor, k = 3** |
|---|---|---|
| Resistors | 16 | **8** |
| Matching | two ratios per channel | **one** |
| Range | missed ±10 V (40.2 kΩ fudge) | **exactly ±10.000 V at the op-amp output**; at a jack, `mod-jack-range` |
| `R-OPAMP-IN` | unbalances it — 196 mV zero error | harmless, feeds a (+) input |
| Safe on `CLR` | `4X − 4X` = **0 for ANY uniform state** | `4X − 3X` = **X** — 0 V only because the grade is zero-scale |

*(The third option that surfaced in the same research — a single inverting
amp, recorded rather than adopted, and still the author's call — is in
[`notes.md`](notes.md).)*

## Values

| Ref | Value | Why |
|---|---|---|
| **R1** | 10 kΩ 0.1 % | To the shared reference |
| **R2** | **30 kΩ 0.1 %** | Feedback. `k = 3`, gain `1 + k` = **exactly 4** |
| **V_ref** | **3.3333 V** from DAC ch7, buffered | Shared by all four. Intercept is `k · V_ref` = 10.000 V |
| **C-FILT-MOD** | 82 nF C0G | 1.94 kHz, jack side of the 1 kΩ. The jacks are on the jack board and these are on module-main, so **place each at `J-B2B-MOD`**, at its jack's pin — the connector end is where a shunt is wanted |

*(The four-resistor version this replaced, and the `R-OPAMP-IN` trap that only
it had, are in [`notes.md`](notes.md).)*

**Tolerance — and this section has now been wrong twice.** The original said
"2.5 V × 2 % × 4 ≈ 50 mV", which evaluates to 200 mV and modelled only the zero
point. The replacement enumerated "sixteen corners of four 1 % resistors",
which is **the four-resistor circuit's answer, kept after the redraw**. There
are two resistors and four corners, and in two of them same-sign tolerance
cancels in the ratio. **Both are specified 0.1 %** (owner, 2026-10-01, pre-layout
review A2-12): Yageo `RT0805BRD07`, 0.1 % and 25 ppm/°C thin film, both values
from one series and TCR grade (`R-MODGAIN-IN`). Two values cannot come off one
reel; one series is what makes the two legs' tempcos match. At 0.1 %, `k` runs
2.9940–3.0060 `[calc: 3 × 0.999/1.001, 3 × 1.001/0.999]`:

| Term | Worst case |
|---|---|
| Zero point, op-amp output | **±5.0 mV** `[calc: (5/6) × 0.0060]` |
| Span, op-amp output | **19.970–20.030 V** (−0.15 %/+0.15 %) `[calc: 5 × (1 + k)]` |
| **At the jack, into one 100 kΩ input** | **`mod-jack-range`** — the load term |

**The first two rows are at the op-amp output.** `R-OUT-PROT` is outside the
loop, so at the jack the whole transfer is also divided by the load: 1 kΩ into
a 100 kΩ input reads 100/101, 0.99 % low `[calc]`, confirmed in `sim/`
(`range`), where the output follows the law to 0.1 mV and neither end clips.
**That is `mod-jack-range`:** ±9.90 V at the jack, and a worst-case span of
19.77–19.83 V, −1.14 %/−0.84 % `[calc: 19.970 × 100/101, 20.030 × 100/101;
sim range, jack_lo/jack_hi]` — at 0.1 % the load is nearly all of it. On something pitch-like that is −11.9 cents per
octave nominal and −13.7 to −10.1 worst case `[calc: 1200 × the span error,
1 V/oct]`; the resistors alone are ±1.8, the load the rest. Firmware cannot buy
the ±10 V back at a loaded jack: the DAC is already at 0 and full scale at the
ends. It can scale anything inside it, which is what the per-channel range
setting does.

**"One matching requirement instead of two" is true by count and misleading.**
The difference amp's zero was `2.5[b/(1+b) − b/(1+b)] = 0` for *any* absolute
ratio — it depended only on leg-to-leg matching. The two-resistor zero, at the
mid-scale code 2.5 V, is `2.5(1 + k) − (10/3)k = 2.5 − (5/6)k`: 0 at `k = 3`,
and ∓5.0 mV for `k`'s ±0.0060 worst case `[calc]` — directly proportional to
the ratio error. Fewer requirements,
but the deleted one was buying something. ADR 0006 says these channels need to be "linear
and repeatable, not calibrated", and they still are — but "repeatable" is doing
more work than a count of requirements implies, and anything pitch-like belongs on
channel 1.

**On the range:** ±10.000 V uses the DAC's *full* 0–5 V span. ADR 0006's
0.25–4.75 V window is a **pitch-channel reserve** — it exists to give firmware
±600 cents of offset authority on 1 V/oct — and does not apply here. Stated
because the two numbers look contradictory side by side and are not.

## The offset is a DAC channel, and that is the whole reason `CLR` works

This is the S4 fix, and it is worth stating where the circuit is, because the
circuit is what makes it true.

On a `CLR`, the C-grade DAC8568 (the grade is **locked** — it selects reference gain as well as reset state, ADR 0006) clears **every** channel to zero
scale (ADR 0006).

> **What asserts `CLR`, now that the watchdog is gone.** Two things, both of
> which survive: the DAC's own **power-on reset**, which happens on every rack
> power-up, and the **`LK-CLR` solder pad** that lets `CLR` be asserted by hand
> during E7–E10 bring-up (`bom.csv`). This page and the one below used to say
> "on a watchdog `CLR`", and the 74HC123 frame watchdog is deleted
> (`digital-and-supervision.md`). Nothing about the argument changes — `CLR`
> still happens, still clears every channel, and the offset channel still
> clears with them — but the trigger had to be renamed or the next reader
> checks the premise, finds no watchdog, and concludes the argument is dead. Channel 7 goes to 0 V with the rest, so:

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
parallel. At `mod-reference` into 2.5 kΩ that is **1.33 mA**, comfortable for
the part. *(This read "At 2.5 V into 2.5 kΩ that is 1 mA" until 2026-09-21 —
a survival from the four-resistor circuit, on the page that owns the figure,
contradicting its own drawing three sections above. `[calc: 3.3333/2500]`)*

It wants its own `R-OPAMP-IN` on the way in, like every other DAC-driven
op-amp input (`R-OPAMP-IN` covers pitch, the four mods and this buffer; the
pitch stage's `VREFOUT` follower has `R-VREF-SER` instead, a thin-film part
because it also sets `V_ref`).

**Do not be tempted to split it into four buffers.** One shared node means all
four channels share exactly the same offset error, so a residual appears as a
common shift across the mod set rather than as four channels disagreeing with
each other — which is both cheaper and more useful.

## Still open

- **Per-channel scale and offset are firmware, not hardware.** ADR 0006 puts
  source, scale, offset, curve and slew in the instrument's configuration
  (over USB, ADR 0015). This stage
  is a fixed ±10 V window and stays that way.
- **Whether all four channels need the full ±10 V.** They are generic by
  decision, so yes for now — but if E10 finds that nothing in the rack wants
  bipolar on more than two of them, two channels could go unipolar 0–10 V and
  halve their resolution cost. Not a change to make speculatively.
