# 2026-09-20 — Resolving the analog design review

Third session entry. Seven research agents and a verification pass produced 53
numbered findings plus a systems review, a fix stress-test and a falsification
pass. This entry records what happened to all of it.

The review document is preserved unedited at
[`docs/review/2026-09-20-analog-design-review.md`](../review/2026-09-20-analog-design-review.md).
It is the record of what was argued. The ADRs are the record of what was
decided, and where the two disagree, the ADRs win.

## Eight decisions, taken one at a time

| # | Decision | Outcome |
|---|---|---|
| 1 | Breath sensor placement | **Bottom**, with the real-time board |
| 2 | Side channels | LEDs both sides; the looms carry only digital traffic |
| 3 | Breath receiver | INA821/INA828 instrumentation amp |
| 4 | Mod channel range | **±10 V**, `4 × (Vdac − Voffset)` |
| 5 | DAC supply | Local LM317LZ at 5.25 V off protected +12 V |
| 6 | Pitch series resistor | **1 kΩ stays** — the trimmer has full authority |
| 7 | Instrument power switch | **Deleted**; TPS2553 load switch at the module |
| 8 | Breath sensor supply | REF5050 + buffer, off the shared 5 V rail |

Three went against the review's recommendation. Two of those — the closed breath
tube and the pitch trim pots — were called by the player rather than by
analysis, and both were right.

## The findings that mattered most

**The 74x165 chain could never have worked.** `QH` is a permanently driven
totem-pole output with no output enable. Sharing MISO with the MCP3202 meant the
ADC could not be read *at all* — not degraded, unreadable. Both SPI hosts are
free now that the display moved to its own MCU, so the chain gets one to itself.
A show-stopper found on paper for the cost of a datasheet read.

**The breath sensor's supply was its scale factor.** The MPXV4006GP is
ratiometric by specification, and it was sharing a 5 V rail with an AMOLED and a
WiFi radio. This was roughly 30 dB worse than the common-mode path ADR 0003
spends several pages resolving. A precision reference fixed a problem nobody had
noticed while the document argued at length about a smaller one.

**Two accepted ADRs contradicted each other outright.** ADR 0009 and ADR 0014
assigned the same two side channels to different things, both marked Accepted.
No individual reviewer could see it, because each was reading one document.

**The firmware LED brightness clamp did not survive the failure it guarded.**
Brownout resets the MCU; WS2815s latch. The clamp is gone at exactly the moment
it is needed. It is now a comfort feature backed by a hardware current limit.

**The U-bolt adjustment was impossible as written** — adjustable after assembly,
with the backing plate inside a bonded cavity.

**E11 tested a topology that does not survive to the finished instrument.** The
single measurement validating the entire analog-breath decision ran before the
LED strips existed and before the body was bonded, and could not be re-run after.
That gap is now milestone M8.

## The findings that were wrong

A seventh agent was told to falsify the others rather than extend them, and
earned its keep:

- The claim that the LT5400 comes only in 1:1:1:1 or 10:1 ratios — **false**.
  LT5400-7 builds the required gain exactly.
- 30 A hot-plug arcing — **impossible**. Minimum arc voltage on gold is ~15 V, so
  a 12 V rail cannot arc.
- The complementary-filter finding was **self-defeating**: capture-on-press
  already subtracts the term it objected to. Its proposed replacement fails
  *worse* — 20 °/s of real motion captured as bias is a 60° error over a gesture.
- Four proposed fixes were **mutually incompatible in pairs**, including two that
  turned out to be the same physical capacitor.
- The "feedback from the jack side" fix would have **oscillated** as described.

Five findings were dropped outright and several more were materially rewritten
before being applied.

## What the process was worth

The reviews found one show-stopper, one 30 dB error, one direct contradiction
between accepted documents, and a missing validation gate — none of which were
visible from inside the design. They also produced confident arithmetic that was
wrong, a fix that would oscillate, and a mechanism that failed worse than what it
replaced.

**Both halves of that are the result.** The adversarial pass was worth running,
and it was worth not trusting. The verification agent — one agent, told to
falsify rather than extend — was the highest-value single thing in the exercise.

## Still open

- ~~Buy 3–5 MPXV4006GP now.~~ **Resolved later the same day.** The
  MPXV4006**DP** has an identical transfer function and is still in production,
  so the part switches and the hoarding problem disappears. Buy two as ordinary
  spares (ADR 0003).
- LED density: 30/m needs no firmware clamp to stay inside budget; 60/m diffuses
  better. The diffusion prototype decides.
- Connector choice, pending a panel fit check.
- Which real-time board — needs an onboard 6-axis IMU and ≥14 free GPIO.
