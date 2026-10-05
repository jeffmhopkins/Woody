# Latency budget

The constraint that shapes most of the electrical design. Written down because
it is the thing most likely to be violated accidentally by a change that looks
harmless — a blocking display refresh, an oversampled ADC, a filter corner set
too low.

> **One MCU, no radio** ([ADR 0015](../decisions/0015-one-mcu-no-display.md),
> which superseded the two-MCU split of ADR 0013 on 2026-09-26). The 8×8
> matrix and the LED row now share the ESP32-S3 with the loop these figures
> describe, so what keeps them from preempting it is **a scheduling
> discipline, not physics**: the output loop owns one core, and lighting
> renders on the other through RMT (`firmware/README.md`, *Architecture
> constraints*). A lighting update that blocks, or that is moved onto the
> loop's core, is exactly the "blocking display refresh" above, and nothing in
> the hardware stops it.
>
> WiFi and BLE are never started, so there is no transmit burst. What remains
> is the lights' own **current** — the LED row's PWM and the matrix — which
> reaches the analog section through shared power and ground, not CPU.
> E11 measures that (*Characterisation*, below).

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
| Receive filter, **a panel toggle**: 495 Hz / 1.57 kHz / ~10 kHz | **322 / 102 / 16 µs** | `1/(2πf)`: 2 × 11 kΩ against the `C_diff` the toggle switches in and the two `C_cm` in series (`breath-sense-link.md`, *Component values*; owner, 2026-10-04, ADR 0003 *Amendment, 2026-10-04*). One pole |
| Output RC at the jack, 15.9 kHz | **10 µs** | `R-OUT-PROT` against `C-OUT-BREATH`, above every mode (#32) |
| **Total** | **~2.51 / 2.29 / 2.21 ms + restrictor** | 500 Hz / 1.5 kHz / WIDE |

**The filter line used to read "< 0.2 ms" and it was the design's own
specified corners that broke it.** Three reviewers found the same thing: a
500 Hz pole has 318 µs of group delay by definition, and this path had two of
them. Since 2026-10-04 (#32) it has one: the jack's RC moved above every mode,
and the receive filter is the player's choice on the panel.

### Breath digital copy (sampled)

Everything above as far as the sensor output — **~2.17 ms** — then:

| Stage | Time | Notes |
|---|---|---|
| **Anti-alias filter, 1.47 kHz** | **108 µs** | `C-AA-ADC` against the divider's 6 kΩ: the module's 1.5 kHz setting, not switched (#32). **Omitted entirely before**, like the restrictor |
| Sampling period | **0–250 µs** | At a 4 kHz loop, a change waits up to one period to be seen. Mean 125 µs |
| SAR ADC read | **~27 µs** | One 24-clock (three-byte) transaction at the MCP3202's 0.9 MHz ceiling on 3.3 V, as `interfaces/spi-link` books it; the conversion itself is 18 of those clocks. **This row said 50–200 µs**, a generic SAR allowance and not this part, and then "~24 µs, 18 clocks", which costed the conversion and not the transaction the bus actually carries (2026-10-01, A5-13). See the warning below |
| SPI to MCU + firmware | < 20 µs | |
| SPI to DAC over umbilical | ~96 µs | Six 32-bit words at 2 MHz. The loop refreshes all of them every pass (`firmware/README.md`), so the whole burst is the latency, not one word |
| DAC settling | ~10 µs | |
| Reconstruction filter | ~82 µs | Mod channels, 1.94 kHz. Pitch is 15.9 kHz and costs ~10 µs |
| **Total** | **~2.5–2.8 ms + restrictor** | |

The sampling period was previously omitted from this table entirely, which
understated the digital path by up to a quarter of a millisecond. It is not a
conversion time — it is quantisation in *time*, and it is there whether or not
the converter is fast.

### The tube is now the largest single term

Moving the sensor to the bottom of the instrument (ADR 0003) traded 0.09 ms of
tube for 1.17 ms. That was a deliberate exchange for a short, quiet analog run
instead of a 400 mm one, and the budget absorbs it: **2.76 ms against a 5 ms
target** (the digital copy's worst, since #32's 1.47 kHz anti-alias pole), with the two largest terms both physical rather than architectural.

For scale: a hard tongue attack has a rise time of roughly 5–15 ms. Diaphragm
dynamics are far slower. Even at 2.8 ms the chain has margin against the
fastest gesture physically available.

**But "roughly 10× margin" was never true and is not true now.** ADR 0003 used
that phrase; against a 5 ms target the real figure is about **1.8×**, and the
restrictor has not been measured yet. Two terms are unbounded until E2 — the
restrictor and the transducer's own response, which is a datasheet number — and
between them they decide whether this budget holds. The honest statement is
that the design has margin, not headroom, and the end-to-end measurement at the
bottom of this page is the one that settles it.

## Key path

| Stage | Time | Notes |
|---|---|---|
| Switch mechanical actuation | mechanical | Bounce is **not** a press-path term here — see below |
| Key network RC, press | `key-press-time` | Owned by `hardware/cluster/key-switch-network/key-switch-network.md`. Far inside the scan period (the figure's `note`); carried as a line so the table is complete, not because it moves the total |
| **Sampling period** | **0–250 µs** | The same 4 kHz loop the breath table books. A closure waits up to one period to be seen. Mean 125 µs. **This table omitted it entirely until 2026-09-21** |
| Key chain read (`U-KEYS`) | **32 µs** | 32 bits at 1 MHz (ADR 0001). This row said "< 10 µs via SPI DMA"; the chain runs at 1 MHz and cannot be clocked away |
| **Note-on gate — two consecutive agreeing samples** | **+250 µs** | One whole loop period, **required by ADR 0001**. This row read "Debounce (press) — 0, fire immediately", which contradicted the ADR that specifies it |
| Debounce (release) | filtered | Off the attack path by construction, which is the point of the asymmetry |
| Firmware note resolution | < 20 µs | |
| DAC update + settle | ~106 µs | The six-word burst (~96 µs) and settling (~10 µs), booked as the breath table books it: firmware is not required to send the pitch word first. **This row said ~60 µs** against the breath table's ~106 µs for the same burst (2026-10-01, A5-13) |
| Pitch filter (~10–20 kHz corner) | ~10 µs | |
| **Total** | **~0.42–0.67 ms** | |

`[calc]` worst case `0.25 (sampling) + 0.032 (chain) + 0.25 (note-on gate) +
0.02 (firmware) + 0.106 (DAC) + 0.01 (filter) = 0.668 ms`, plus the RC press
time; best case is the same sum with the sampling period at zero, 0.418 ms.
**Against the 5 ms target that is roughly 7.5× — nearly five times the breath
path's margin.** The key path is not the one at risk, and now the table says so
instead of leaving the reader to add it up.

> **This table had no Total and omitted its two largest terms.** The sampling
> period and the note-on gate are 0.50 ms of a 0.62 ms worst case — **80 % of
> the path** — and between them they were the difference between a table that
> closes and a list of small numbers. Found by the 2026-09-21 pre-merge wave;
> the same omission had already been fixed in the breath tables above, which is
> the shape this project keeps repeating: the fix lands where the editing is
> happening and not where the reader looks.

**Debounce asymmetrically.** Gate the leading edge only by ADR 0001's two
agreeing samples, and filter only the release. Symmetric debounce puts its full window directly into the attack, which
is the one place latency is audible.

> **The note-on gate is not a debounce, and the difference now has a number
> against it.** Gateron publishes **5 ms max bounce at 16 in/sec** for this
> exact part — see `ks33-geometry.md` — and ADR 0001's gate is two samples
> 250 µs apart, **twenty times shorter than that window**. Both samples can
> fall inside one bounce burst. That is correct for *latency*, and it is the
> intent: the gate rejects a single corrupted 32-bit frame, not contact
> chatter. What it means is that **rejecting bounce is entirely the release
> filter's job**, and the release window has to outlast the bounce burst rather
> than the key network's RC delay (`key-release-time`), which is a glitch
> filter, not a debounce. `firmware/README.md` sets
> that window from measured bounce at M1; the vendor maximum is now the number
> M1 has to come in under, instead of the 20 ms the 2021 firmware guessed.

## Characterisation — measure these, do not assume them

Every figure in the tables above is a datasheet number or an estimate. A full
bench is available (scopes, logic analysers, signal generators), so these should
be replaced with measurements as the relevant milestones come up. Several are
load-bearing enough that being wrong about them would change the design.

| What | How | Why it matters |
|---|---|---|
| **Breath transducer response** | Step the pressure, scope the sensor output, measure rise time | A large term and a datasheet figure. If it is really 3 ms the margin shrinks; if it is 200 µs there is far more headroom than assumed |
| **Tube delay, ring-down, and the restrictor's time constant** | Step the pressure at the mouthpiece, scope at the sensor. Measure the delay, the ring-down, and — with the plug fitted — the added time constant | Now the **largest single term** at 400 mm, and the one term tunable by design. The restrictor is sized by damping, not by frequency (ADR 0003), and **its time constant is a latency term this budget cannot fill in until E2** |
| **KS-33 contact bounce** | Scope a switch, measure bounce duration on press *and* release | **No longer an unknown, only an unmeasured maximum.** Gateron's banked drawing publishes **5 ms max at 16 in/sec actuation** (`ks33-geometry.md`); this row used to frame it as unpublished. The 2021 firmware used a flat 20 ms window, so the published maximum alone buys back 15 ms of the release filter — and a measured typical, likely well under it, buys back more. Actuation speed is a player variable, so measure at a musical one |
| **ADC + SPI round trip** | Logic analyser on the bus | Datasheet conversion time excludes driver overhead. The real number includes it |
| **SPI over the umbilical at length** | Logic analyser at the module end, cable at full length | Setup/hold margin, ringing, double-clocking. This is where a long cable bites, and it is invisible without an LA. Gates E11 |
| **DAC settling and filter corners** | Scope a commanded step | Confirm settling to within an LSB, and that the pitch and breath filters actually sit where they were designed to |
| **Rack rail ripple, both directions** | Scope +12V at the module with the instrument running | Incoming ripple lands on the CV outputs; outgoing noise from the local buck lands on every other module in the rack. Gates E6 |
| **Loop timing with the lights running** | A GPIO toggled at each pass's start and end, on a logic analyser, with the matrix and the LED row animating and the MIDI out sending (issue #37) | The one MCU now carries the lights and the loop (ADR 0015). Confirms the pass stays inside `loop-budget` and that lighting on the other core never stretches it. Replaces the WiFi-burst and inter-MCU UART rows, whose radio and second MCU no longer exist |
| **Umbilical link** | Logic analyser at the module end, cable at length | **2 MHz** — the 0.6 MHz this row used to give came from a 2 kHz mod rate and does not close at 4 kHz (ADR 0004). Confirm it is clean at the rate actually needed, and that RS-485 stays unnecessary |
| **Breath channel noise** | Scope the breath jack while sweeping the matrix's brightness and the LED row's animation | The end test for the analog breath decision. Any of those appearing on the output means AGND is picking up power return current, or the module is sensing against local ground (ADR 0003) |
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

   **The 8 kHz end of the old "4–8 kHz" range does not close.** Serialised,
   the bus time alone is ADC 26.7 µs + key chain 32 µs + six DAC channels at
   2 MHz 96 µs = 154.7 µs — already over the 125 µs period at 8 kHz before any
   driver overhead. At 4 kHz one pass is **186–227 µs of 250 µs**, which is
   this page's tracked figure `loop-budget`. Three documents used to disagree
   about this; 4 kHz is the number, and it is not comfortable.

   **What the range is** `[calc]` (re-derived 2026-10-01, A5-13: the range this
   paragraph carried until then did not reproduce from any transaction count).
   Per pass: SPI2 carries seven transactions, six DAC frames (`6 × 32 bits at
   2 MHz = 96 µs`) and one ADC read (`24 clocks at 0.9 MHz = 26.7 µs`); SPI3
   carries one, the key chain (`32 bits at 1 MHz = 32 µs`). ESP-IDF's
   per-transaction overhead is 9 µs polling and 24 µs interrupt-driven.

   ```
   polling, key chain concurrent on SPI3:  7 × 9 + 96 + 26.7           = 185.7 µs
   polling, key chain serialised:          8 × 9 + 96 + 26.7 + 32      = 226.7 µs
   interrupt, key chain concurrent:        7 × 24 + 96 + 26.7          = 290.7 µs
   interrupt, key chain serialised:        8 × 24 + 96 + 26.7 + 32     = 346.7 µs
   ```

   The figure is the two polling rows: the low end needs the chain's
   transaction in flight on SPI3 while SPI2 polls, the high end is the same
   work one after another. Both interrupt rows miss the period.

   > **Until 2026-09-21 this paragraph was wrong twice over.** It totalled the
   > bus time as a superseded "136 µs" of 250 µs, and called that a
   > superseded "54 % duty, with room for the loop to do work". It omitted the **ESP-IDF per-transaction overhead** — 24 µs
   > interrupt, 9 µs polling — which no document in this corpus counted, and
   > which takes a pass to **291 µs with driver defaults, i.e. it does not
   > close at 4 kHz either.** Polling transactions on an acquired bus are not
   > an optimisation here; they are what makes 4 kHz reachable at all.
   >
   > The old figure and the real one are different engineering situations -
   > half the period against nearly all of it - and this page, the figure's
   > own owner, carried the comfortable one. Found by
   > tightening the owner check: the register stated a range and the owner
   > stated neither end of it, passing only on the shared denominator.

   > **⚠ This page gave two different figures for the same ADC read, and the
   > gap decides whether 4 kHz is buildable.** The table above said 50–200 µs
   > and this rule said 24 µs. At 200 µs a pass costs **312 µs against a
   > 250 µs period and the loop does not close**; even a mid-range 125 µs
   > leaves no margin.
   >
   > ~27 µs is the right number for the specified part — a 24-clock
   > transaction (18 for the conversion, byte-aligned) at the 0.9 MHz it tops
   > out near on 3.3 V. 50–200 µs was a generic SAR allowance carried in from
   > nowhere.
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
3. **Lighting never blocks the output loop.** The matrix and the LED row
   render on the other core, through RMT, never on the loop's core and never
   by a blocking write (`firmware/README.md`). Since ADR 0015 they share the
   MCU with the loop, so this rule is the only thing between them and the
   budget above.
4. **There is no radio.** WiFi and BLE are never started (ADR 0015). Rule 4
   used to say the WiFi stack and display were on a different MCU (ADR 0013);
   that MCU is gone, and with it the physical isolation the rule leaned on —
   rule 3 is what replaces it.
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
