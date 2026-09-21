# Latency budget

The constraint that shapes most of the electrical design. Written down because
it is the thing most likely to be violated accidentally by a change that looks
harmless — a blocking display refresh, an oversampled ADC, a filter corner set
too low.

> **The display and radio are on a separate MCU**
> ([ADR 0013](../decisions/0013-two-mcu-split.md)), so neither can preempt the
> loop these figures describe. That isolation is physical rather than a
> scheduling discipline.
>
> What remains is the **current transient** a WiFi burst puts on the rail, which
> reaches the analog section through shared power rather than shared CPU. Each
> board gets its own regulator and local bulk capacitance for that reason. Verify
> by measurement before trusting configuration-while-playing.

## Target

**Under 5 ms from gesture to output.** That is roughly the line between an
instrument and a toy.

**The margin is about 1.6×, not the 10× that was claimed elsewhere**, and one
term — the pneumatic restrictor — is not measured yet. This budget is close
enough to its target that a change which looks harmless can break it, which is
the reason the page exists.

## Breath path

**These are two different paths and they used to be one table.** The breath CV
at the jack is analog from the sensor onward and is never sampled. The digital
copy — thresholds, note gating, mod routing, MIDI — is sampled, and pays for it.

### Breath CV at the jack (analog, no sampling)

| Stage | Time | Notes |
|---|---|---|
| Tube propagation | **~1.17 ms** | 400 mm. The sensor sits at the bottom with the real-time board (ADR 0003) |
| **Pneumatic restrictor** | **? — sized at E2** | A deliberate low-pass, added to damp the tube's pipe mode (ADR 0003). **Not previously in this budget at all**, and the term most able to break it |
| Pressure transducer | **~1 ms** | A property of the sensor, not the design |
| Buffer and cable propagation | < 10 µs | |
| Receive filter, **482 Hz** | **330 µs** | `1/(2πf)`. **Not 531 Hz** — that assumed 20 kΩ of series resistance, and adding `R1b` to the return leg makes both legs 11 kΩ. One pole, not two |
| Output RC at the jack, 480 Hz | **332 µs** | |
| **Total** | **~2.83 ms + restrictor** | |

**The filter line used to read "< 0.2 ms" and it was the design's own
specified corners that broke it.** Three reviewers found the same thing: a
500 Hz pole has 318 µs of group delay by definition, and this path has two of
them. The real figure is 632 µs — three times what was written, though still
inside the target.

### Breath digital copy (sampled)

Everything above as far as the sensor output — **~2.17 ms** — then:

| Stage | Time | Notes |
|---|---|---|
| **Anti-alias filter, 564 Hz** | **282 µs** | `C-AA-ADC` against the divider's 6 kΩ. **Omitted entirely before**, like the restrictor |
| Sampling period | **0–250 µs** | At a 4 kHz loop, a change waits up to one period to be seen. Mean 125 µs |
| SAR ADC conversion | **~24 µs** | 18 clocks at the MCP3202's ~0.9 MHz ceiling on 3.3 V. **This row said 50–200 µs**, which is a generic SAR allowance and not this part — and it is the same read the loop-duty rule books at 24 µs. See the warning below |
| SPI to MCU + firmware | < 20 µs | |
| SPI to DAC over umbilical | ~96 µs | Six 32-bit words at 2 MHz. The loop refreshes all of them every pass (`firmware/README.md`), so the whole burst is the latency, not one word |
| DAC settling | ~10 µs | |
| Reconstruction filter | ~82 µs | Mod channels, 1.94 kHz. Pitch is 15.9 kHz and costs ~10 µs |
| **Total** | **~2.9–3.1 ms + restrictor** | |

The sampling period was previously omitted from this table entirely, which
understated the digital path by up to a quarter of a millisecond. It is not a
conversion time — it is quantisation in *time*, and it is there whether or not
the converter is fast.

### The tube is now the largest single term

Moving the sensor to the bottom of the instrument (ADR 0003) traded 0.09 ms of
tube for 1.17 ms. That was a deliberate exchange for a short, quiet analog run
instead of a 400 mm one, and the budget absorbs it: **2.80 ms against a 5 ms
target**, with the two largest terms both physical rather than architectural.

For scale: a hard tongue attack has a rise time of roughly 5–15 ms. Diaphragm
dynamics are far slower. Even at 3.1 ms the chain has margin against the
fastest gesture physically available.

**But "roughly 10× margin" was never true and is not true now.** ADR 0003 used
that phrase; against a 5 ms target the real figure is about **1.6×**, and the
restrictor has not been measured yet. Two terms are unbounded until E2 — the
restrictor and the transducer's own response, which is a datasheet number — and
between them they decide whether this budget holds. The honest statement is
that the design has margin, not headroom, and the end-to-end measurement at the
bottom of this page is the one that settles it.

## Key path

| Stage | Time |
|---|---|
| Switch mechanical actuation | mechanical |
| 74HC165 chain read | **32 µs** — 32 bits at 1 MHz (ADR 0001). This row said "< 10 µs via SPI DMA"; the chain runs at 1 MHz and cannot be clocked away |
| Debounce (press) | 0 — fire immediately |
| Debounce (release) | filtered |
| Firmware note resolution | < 20 µs |
| DAC update + settle | ~60 µs |
| Pitch filter (~10–20 kHz corner) | ~10 µs |

**Debounce asymmetrically.** Fire on the leading edge and filter only the
release. Symmetric debounce puts its full window directly into the attack, which
is the one place latency is audible.

## Characterisation — measure these, do not assume them

Every figure in the tables above is a datasheet number or an estimate. A full
bench is available (scopes, logic analysers, signal generators), so these should
be replaced with measurements as the relevant milestones come up. Several are
load-bearing enough that being wrong about them would change the design.

| What | How | Why it matters |
|---|---|---|
| **Breath transducer response** | Step the pressure, scope the sensor output, measure rise time | A large term and a datasheet figure. If it is really 3 ms the margin shrinks; if it is 200 µs there is far more headroom than assumed |
| **Tube delay, ring-down, and the restrictor's time constant** | Step the pressure at the mouthpiece, scope at the sensor. Measure the delay, the ring-down, and — with the plug fitted — the added time constant | Now the **largest single term** at 400 mm, and the one term tunable by design. The restrictor is sized by damping, not by frequency (ADR 0003), and **its time constant is a latency term this budget cannot fill in until E2** |
| **KS-33 contact bounce** | Scope a switch, measure bounce duration on press *and* release | The 2021 firmware used a flat 20 ms debounce. If these switches settle in 2 ms, setting the window from data buys back 18 ms of the most latency-sensitive path in the instrument |
| **ADC + SPI round trip** | Logic analyser on the bus | Datasheet conversion time excludes driver overhead. The real number includes it |
| **SPI over the umbilical at length** | Logic analyser at the module end, cable at full length | Setup/hold margin, ringing, double-clocking. This is where a long cable bites, and it is invisible without an LA. Gates E11 |
| **DAC settling and filter corners** | Scope a commanded step | Confirm settling to within an LSB, and that the pitch and breath filters actually sit where they were designed to |
| **Rack rail ripple, both directions** | Scope +12V at the module with the instrument running | Incoming ripple lands on the CV outputs; outgoing noise from the local buck lands on every other module in the rack. Gates E6 |
| **WiFi transmit transients** | Scope the rail during a TX burst with the radio enabled | Now the *only* path by which WiFi can affect the outputs (ADR 0013). Decides whether configuration-while-playing is usable |
| **Inter-MCU UART link** | Logic analyser on the pair, under load | Frame integrity and whether status traffic is jitter-free at rate (ADR 0013) |
| **Umbilical link** | Logic analyser at the module end, cable at length | **2 MHz** — the 0.6 MHz this row used to give came from a 2 kHz mod rate and does not close at 4 kHz (ADR 0004). Confirm it is clean at the rate actually needed, and that RS-485 stays unnecessary |
| **Breath channel noise** | Scope the breath jack while sweeping display brightness, LED animation and a WiFi burst | The end test for the analog breath decision. Any of those appearing on the output means AGND is picking up power return current, or the module is sensing against local ground (ADR 0003) |
| **End-to-end, in one shot** | Two scope channels: one on the sensor output, one on the CV jack | Measures the real gesture-to-output time directly instead of summing estimates. This is the number that actually matters, and it is the one measurement that validates or refutes the entire table above |

A signal generator driving a known waveform into the ADC front end also
characterises the full digitise-process-output chain's frequency response and
exposes any aliasing.

**Record the measured numbers back into this document** as they are taken, and
mark which rows are measured rather than assumed. A budget made of estimates is
a hypothesis; a budget made of measurements is a constraint.

## Rules that follow

1. **The output loop runs at 4 kHz, not 8. Breath output never digitised at
   all** — it goes
   down the umbilical as a differential analog signal (ADR 0003), so there is no
   output rate to get wrong and no staircase to filter. The ADC exists for
   thresholds, note gating, mod routing and MIDI, not for the breath jack.

   **The 8 kHz end of the old "4–8 kHz" range does not close.** Serialised, one
   pass costs ADC 24 µs + key chain 32 µs + six DAC channels at 2 MHz 96 µs =
   **136 µs**, against a 125 µs period at 8 kHz. At 4 kHz it is 136 µs of
   250 µs — 54 % duty, with room for the loop to do work. Three documents used
   to disagree about this; 4 kHz is the number.

   > **⚠ This page gave two different figures for the same ADC read, and the
   > gap decides whether 4 kHz is buildable.** The table above said 50–200 µs
   > and this rule says 24 µs. At 200 µs a pass costs **312 µs against a
   > 250 µs period and the loop does not close**; even a mid-range 125 µs
   > leaves no margin.
   >
   > 24 µs is the right number for the specified part — the MCP3202 needs 18
   > clocks and tops out near 0.9 MHz at 3.3 V, so ~20 µs of conversion plus
   > framing. 50–200 µs was a generic SAR allowance carried in from nowhere.
   >
   > **But the allowance was pointing at something real**, which the
   > characterisation table already names: *"datasheet conversion time
   > excludes driver overhead; the real number includes it."* If the measured
   > round trip comes back near 200 µs, **the answer is not a faster ADC —
   > it is that 4 kHz does not close and the loop rate has to move.** That
   > makes the "ADC + SPI round trip" measurement a gate on the architecture,
   > not a refinement of it.

   Six channels means *all* the populated ones: the loop refreshes the mod
   offset every pass rather than writing it once (`firmware/README.md`). The
   old table booked six while writing five, which is how the refresh fits
   inside a budget that was already paid. The breath ambient-zero channel that
   briefly made it seven is deleted (ADR 0003).
2. **SAR ADC, never delta-sigma.** A delta-sigma's decimation filter has real
   group delay — potentially milliseconds — which would consume the entire
   budget on its own.
3. **Display rendering never blocks the output loop.** Separate SPI host,
   separate core. A full-screen refresh on a colour LCD is orders of magnitude
   longer than the whole budget above.
4. **The WiFi stack and display are on a different MCU entirely** (ADR 0013).
   Nothing on the real-time board competes with the output loop.
5. **Pitch output filter stays fast** (10–20 kHz). A low corner is an audible
   glide on every note.
6. **Smoothing happens in software**, where it can be set per channel according
   to what that channel carries — not in the analog filter, which is fixed.

## Things that do not matter

- **Bit depth beyond 16.** One LSB at 16-bit over a 10V span is ~150 µV. The
  noise floor of human breath sits orders of magnitude above that.
- **Knob latency.** Panel knobs are turned by hand; a millisecond is nothing.
- **Stepping artefacts on slow channels.** Step size is bounded by signal slew
  rate, not full scale.
