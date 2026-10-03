# LED data line — simulation

`sims.yaml` says what is simulated and what every run must show; `data.cir` is
the deck; `results.yaml` is **generated** by
`python3 tools/sim.py run hardware/carrier/led-strip-drive/sim`.
`docs/reference/tooling.md` §5 explains the tool.

**No part value is written here.** The deck reads this circuit's netlist
(`R-LED-SER`, the two inputs on `LED_DI`). The 74AHCT125's output is
behavioural — a 5 V source behind the resistance its banked `V_OH`/`V_OL`
table gives (55–88 Ω) — and each WS2815B-V1 input is its 15 pF maximum `C_I`.
The trace is an assumption until the main board is laid out (~100 mm since the fourteenth LED put `D-LED-1` in the tail corner), varied −50/+100 %.
Only the first stage is this circuit's: every LED re-times the data for the
next.

## What it shows

| Sim | Page's claim | Result |
|---|---|---|
| `t0h` | 22 ns edge (330 Ω × 30 pF, × 2.2), a tenth of T0H | **37 ns** 10–90 % at the nominal, 30–50 ns over the corners: the gate's own resistance and the trace to the tail corner's LED and back to the row (~100 mm, `c_trace` 12 pF −50/+100 %) add two thirds. Under a quarter of T0H |
| | T0H arrives intact | a 220 ns high at the gate reads as **216–239 ns**, depending where in 1.5–2.7 V the LED's threshold sits: at the `V_IH` end 4 ns short of T0H's 220 ns minimum. The edge costs a few nanoseconds, not a fraction of the pulse |
| | no overshoot past the 5.7 V input maximum | 5.00 V: an RC, nothing rings |

## What a result is worth

The edge and the pulse are arithmetic on an RC; the run confirms it with the
gate's resistance included. The firmware's T0H must not sit at the 220 ns
minimum: with the edge's few nanoseconds taken off, the LED could read it as
under the minimum. Anything a few tens of nanoseconds above it is clear.
