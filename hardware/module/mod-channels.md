# Mod channels 1–4 — schematic

**Status:** Drawn 2026-09-21. Third module page, after
[breath](breath-receive-stage.md) and [pitch](pitch-stage.md).

Four identical channels. ADR 0006 specifies `Vout = 4 × (Vdac − 2.5 V)` and
contradicts itself about how to build it — the topology section offers an
LT5400 1:4 ratio, the calibration section says ordinary 1 % discretes. The
discretes won (ADR 0006, `R-MODGAIN`), and this page is what they build.

## The circuit — one channel of four

```
   DAC ch7 ──[1k]──┬── ½ OPA2197 ──┬── V_OFF = 2.500 V
   (shared)        │   follower    │   to all four channels
                   └───────────────┘   (~1 mA total into 4 × 10k)
                                   │
                                   │
                          ┌────────┴────────┐
                          │                 │
   DAC ch2         [R1 10k 1%]       (ch3, ch4, ch5
   0…5 V                  │           identical)
      │                   │
   [1k R-OPAMP-IN]        │
      │                   │
      ├──[R3 10k 1%]──┬───┼──────────┐
      │               │   │          │
                      │   │    ┌─────┴──────┐
                      │   └────┤ −          │
                      │        │  ½ OPA2197 ├──┬───────────┐
                      ├────────┤ +          │  │           │
                      │        └────────────┘  │           │
              [R4 40.2k 1%]                    │           │
                      │                        │           │
                 AGND(module)                  │           │
                                               │           │
                      ┌────[R2 40.2k 1%]───────┘           │
                      │                                    │
                      └────────────────────────────────────┘
                                                            │
                                              ┌─────────────┘
                                              │
                                [R-OUT-PROT 1k]
                                              │
                                              ├──[C-FILT-MOD 82nF C0G]── AGND
                                              │
                                              ├──[D-JACK-CLAMP BAV99]── ±12 V
                                              │
                                        MOD n jack
```

## Why this one *is* a difference amplifier, where pitch is not

Pitch collapsed to two resistors because its `A = 1 + B` landed exactly on the
single-op-amp boundary. The mods do not: `Vout = 4·Vdac − 4·V_OFF` needs
**A = 4 and B = 4**, and `A = 1 + B` would require B = 3. So the reference has
to enter through its own input rather than through the feedback divider, which
is the four-resistor difference amp above.

Worth noting side by side, because it is the same designer's instinct producing
two different right answers:

| | Pitch | Mod 1–4 |
|---|---|---|
| Wanted | `2·Vdac − 2.5` | `4·Vdac − 10` |
| A vs 1+B | 2 = 1 + 1 ✓ | 4 ≠ 1 + 3 ✗ |
| Topology | Non-inverting, 2 matched resistors | Difference amp, 4 resistors |
| Precision | LT5400, 1:1 | Ordinary 1 %, 1:4 |

## Values

| Ref | Value | Why |
|---|---|---|
| **R1, R3** | 10 kΩ 1 % | |
| **R2, R4** | **40.2 kΩ 1 %** | Nearest E96 to 40 k. Gain 4.02, so the jack reaches **±10.05 V** |
| **V_OFF** | 2.500 V from DAC ch7, buffered | Shared by all four |
| **C-FILT-MOD** | 82 nF C0G | 1.94 kHz, jack side of the 1 kΩ |

**40.2 kΩ rather than 39 kΩ.** E24's 39 k would give gain 3.90 and a jack that
stops at ±9.75 V, visibly short of the specified ±10. Going slightly over costs
nothing: an OPA2197 on ±12 V less two Schottky drops reaches ~±11.45 V, so
±10.05 V has 1.4 V of margin.

**Matching matters more than absolute value, and barely at all here.** The only
"common mode" this difference amp sees is the fixed 2.500 V offset, so a ratio
mismatch between the two sides appears as a *static output offset*, not as
rejected noise. With 1 % parts the worst case is roughly
`2.5 V × 2 % × 4 ≈ 50 mV`, which is 0.25 % of the ±10 V span. ADR 0006 is
explicit that these channels need to be "linear and repeatable, not
calibrated", and 0.25 % is well inside that.

Buying the four sets from one reel makes it much better than worst case for
free, since reel-adjacent parts track.

## The offset is a DAC channel, and that is the whole reason `CLR` works

This is the S4 fix, and it is worth stating where the circuit is, because the
circuit is what makes it true.

On a watchdog `CLR`, an A/C-grade DAC8568 clears **every** channel to zero
scale (ADR 0006). Channel 7 goes to 0 V with the rest, so:

```
Vout = 4.02 × (0 − 0) = 0 V
```

All four jacks park at 0 V, which is the same state as rack power-on. **Had the
2.5 V come from a fixed divider or the internal reference directly**, `CLR`
would zero the signal channels and leave the offset standing, and every mod
jack would pin at `4.02 × (0 − 2.5) = −10.05 V` — a hard rail on four outputs,
indefinitely, with no `MISO` to notice it.

The mirror-image failure is the one the review actually found: firmware
refreshing the five signal channels after a `CLR` and *not* channel 7, which
pins the jacks at `4.02 × Vdac` ≈ **+11.45 V**. That is closed by the
statelessness rule in `firmware/README.md` — refresh all six populated
channels every pass — and the latency budget already paid for it.

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

## Still open

- **Per-channel scale and offset are firmware, not hardware.** ADR 0006 puts
  source, scale, offset, curve and slew on the instrument's display. This stage
  is a fixed ±10 V window and stays that way.
- **Whether all four channels need the full ±10 V.** They are generic by
  decision, so yes for now — but if E10 finds that nothing in the rack wants
  bipolar on more than two of them, two channels could go unipolar 0–10 V and
  halve their resolution cost. Not a change to make speculatively.
