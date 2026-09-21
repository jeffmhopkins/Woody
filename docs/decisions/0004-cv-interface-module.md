# 0004 — CV interface module and umbilical

**Status:** Accepted

## Context

The instrument's output target is a Eurorack system. The original plan put the
DAC, analog scaling, bipolar supply and jacks inside the instrument body, on
battery power (see ADR 0005, superseded).

Putting the analog section in a rack module instead — connected to the
instrument by a single cable — solves several problems at once.

## Decision

**A 10HP Eurorack module holding all analog output hardware, connected to the
instrument by an 8-conductor ruggedised umbilical.**

The instrument loses its **output** analog: no jacks, no bipolar rails, no
battery. It takes power from the rack and sends channel data down the same
cable.

**It does not become purely digital, and an earlier version of this line said it
did.** That claim was already false when written and it let a review finding
through unchallenged. The instrument still carries the pressure sensor, a
precision reference, two op-amp stages and the analog drive onto the umbilical —
which is where most of the project's analog risk actually lives (ADR 0003). What
moved to the module is the *scaling, conversion and output* analog, not all of
it.

### What goes over the cable

Digital down, analog stays in the module:

> ~~```~~
> ~~+12V, GND, GND      power (3.3V derived locally in the instrument, small buck)~~
> ~~SCLK, MOSI, CS      SPI to the DAC, ~2 MHz~~
> ~~MISO                unused today — module ID and presence detect~~
> ~~spare               reserved~~
> ~~```~~
>
> **Superseded 2026-09-21 by the Revised conductor budget below**, which is the
> authoritative 8-of-8 mapping and the one E11 and E12 build to. Three things
> changed: `MISO` is deleted, the second `GND` and the `spare` are gone, and
> the three grounds are named and distinct — `PWR_GND`, `DIG_GND` and `AGND`,
> which is not an aesthetic distinction (`AGND` carries no power current). The
> block is kept struck through rather than removed because the rest of this
> section argues from it.

No −12V goes up the cable; nothing in the instrument is bipolar any more.

With real Cat5/6 each signal sits against a ground in its own twisted pair.

**Bandwidth is modest again.** A 96 kHz digital breath channel would have
needed ~6.8 MHz on the wire and probably RS-485 transceivers. With breath going
analog instead (ADR 0003), the digital link carries only DAC words.

| | Payload | SPI clock at 50% use |
|---|---|---|
| Breath digital at 96 kHz + 5 channels | 3.39 Mbit/s | ~6.8 MHz |
| ~~Breath analog, 5 channels at 2 kHz~~ | ~~0.32 Mbit/s~~ | ~~0.6 MHz~~ |
| **Breath analog, 6 channels at 4 kHz** | **0.77 Mbit/s** | **≥1.5 MHz → specify 2 MHz** |

**The 0.6 MHz figure was stale and it did not close.** It came from a 2 kHz mod
rate that ADR 0006 revised to 4 kHz, and from five channels where the
statelessness rule in `firmware/README.md` refreshes every populated one. Six
32-bit words is 192 bits; at 0.6 MHz that is 320 µs against a 250 µs loop
period. **The loop would simply not have completed.** Five agents found it.

At 2 MHz the same six words take 96 µs, which is 38 % of the period and leaves
room for the MCP3202 sharing the host. (Seven channels were populated until the
breath ambient-zero was deleted — ADR 0003 — which is slack, not a reason to
drop the clock: 0.6 MHz still does not close.)

**This number has a deadline.** E11 validates the real cable at the real rate
and it is a gate before the body bonds — there is no second chance to test 2 m
of Cat5 at a speed the instrument turns out to need. > **The RC-corner arithmetic that stood here is refuted, 2026-09-21.** It read
> "220 Ω with ~200 pF of cable is a 3.6 MHz corner". Two metres of Cat5 is a
> **100 Ω transmission line**, not a lumped capacitor: the round trip is ~20 ns
> against 2–5 ns edges, so this is a reflection problem and the RC corner is
> the wrong model. Three reviewers agreed (`carrier.md`).

The settled part is **`R-SPI-SER` ×3 at 100 Ω** — one each on `SCLK`, `MOSI`
and `CS` at the driving end, a source match into the cable's own impedance.
220 Ω drives the far end to **1.83–1.86 V** against the 74AHCT125's 2.0 V
`V_IH`, dwelling ~20 ns per edge in the forbidden band, so it is not merely
conservative but wrong.

Plain single-ended SPI at a couple of MHz over twisted pair is still
unremarkable. **RS-485 returns to contingency status**, not a likely
requirement.

### Revised conductor budget

```
+12V      / PWR_GND     power. NOT presence - see below
SCLK      / DIG_GND     SPI to the DAC, 2 MHz (was ~1 MHz here)
MOSI      / CS
BREATH    / AGND        analog, band-limited ~500 Hz, sense return
```

> **This block said `power, and the presence signal` until 2026-09-21.** There
> is no presence signal. Both presence-detect schemes are deleted further down
> this ADR and `OE` is tied permanently enabled, so nothing at the module end
> watches the far end of the cable. `+12 V` on the umbilical is power and
> nothing else — a conductor is not budgeted for a deleted feature.

Eight of eight, paired to suit Cat5's four twists. **`AGND` carries no power
current** — it is a sense reference only, which is the whole reason the analog
channel survives the cable (ADR 0003). Keep it twisted with `BREATH` and away
from the SPI clock pair.

MISO goes, and with it the planned module-ID line. No loss worth engineering
around: the instrument is rack-powered, so +12V on the umbilical is itself
evidence the module is connected, and the only other case is sitting on the
bench under USB power during development.

### Why this partitioning is right

- Deletes the entire battery subsystem (ADR 0005).
- Moves precision analog into a shielded metal box inches from its jacks,
  instead of running pitch CV down two feet of wooden instrument alongside LED
  power.
- Splits the project into two deliverables with different risk profiles that can
  be built in parallel: the instrument's risk is mechanical, the module's is
  analog precision.
- **The module can be brought up entirely standalone** — driven from any dev
  board with a test pattern and a multimeter — long before the instrument
  exists. This de-risks the whole CV problem on its own schedule.
- The module is independently useful. "Digital controller to six-channel CV over
  Cat5" stands on its own.

### The module needs its own logic rail

Easy to miss: **the DAC8568 is a 2.7–5.5 V part and cannot run on the rack
rails.** The module therefore derives a low-voltage rail from +12 V, and the
choice of which interacts with noise more than it looks:

| DAC VDD | Output span | Gain the scaling stage must supply |
|---|---|---|
| 3.3 V | 0–2.5 V (ref × 1) | **3.6×** |
| **5 V** | **0–5 V (ref × 2)** | **1.8×** |

Everything the scaling stage amplifies — op-amp noise, offset, drift — is
amplified by that factor. **5 V halves it.**

The cost is that a 5 V DAC wants roughly 3.5 V for a logic high while the
instrument sends 3.3 V, so SPI needs shifting. That turns out to be free in
parts terms:

- **A local 5.21 V regulator off the protected +12 V rail** for the DAC's AVDD
  — not the rack's +5 V bus. See below.
- **74AHCT125** for the shifter, running from the **bus +5 V rail** — the *same
  part* as the instrument's LED data lines (ADR 0014), with a spare gate left
  over.

One part number shared across both boards rather than one more to source.

### The DAC gets a local regulator; the level shifter keeps the bus rail

The obvious move is to take the module's 5 V straight from the rack. It is
inches from the bus board, the load is milliamps, and the rail is right there on
the 16-pin header. That was the original decision, and it is wrong for the DAC.

**The rack's +5 V is the least-regulated rail in Eurorack** — ±5 % is normal, and
it moves with whatever else in the case is drawing from it. Two consequences:

- **The DAC's full-scale output is its supply.** DAC8568 at internal reference
  × 2 spans 0–5 V, so full scale *equals* AVDD. TI does not specify the headroom
  needed to actually reach it, and wants AVDD ≈ 5.5 V for a true 5 V full scale.
  At a bus rail sagging to 4.75 V the DAC saturates somewhere around 4.55–4.65 V
  — and the top calibration point lands in the nonlinear region, which corrupts
  the whole two-point fit rather than just clipping the top.
- **It puts a rail the rack moves underneath the pitch calibration.** Pitch is
  calibrated once against a real VCO (ADR 0006). A supply that shifts when
  another module powers up shifts the calibration with it.

**So: an LM317LZ set to ~5.21 V, fed from +12 V downstream of the module's own
reverse-protection diode** (its own — see the power tree below). TO-92, two
resistors and two capacitors, ten-odd milliamps of load, under 100 mW — the
lowest-effort regulator that exists, and it buys back both properties.

**The tolerance argument here used to be wrong, and the answer is a meter, not
a better part.** This ADR applied ±4 % to the *output* and ignored both the
divider tolerance and the adjust-pin current. Done properly the worst-case
spread is about 0.66 V against a window of roughly 0.55 V — **no nominal value
fits on paper.** Two reviewers found it independently and both are right.

They proposed an LP2951, or a second REF5050 buffered by an op-amp half. Both
are declined, because the premise behind "no value fits" is a statistical
statement about a population, and **this is a population of one**. There is a
TO-92 regulator, two through-hole resistors, a bench and a voltmeter.

What is adopted is the free part of the fix:

- **Shrink R2** — 150 Ω / 475 Ω instead of 240 Ω / 768 Ω — which halves the
  I_ADJ contribution to 24–48 mV.
- **0.1 % divider parts**, which cost pennies and arrive in the same order.
- **Select R2 on the bench at E7**, against the real DAC: raise the top codes
  and find where they start compressing against AVDD. That is the floor that
  actually matters, and it is measured rather than assumed — the "4.95 V floor"
  the review argued against was never derived from anything.

For one instrument that is strictly better information than a tolerance stack,
and if the selected value lands badly you find out at E7 with a meter, on a
board with four screws in it.

**The 74AHCT125 stays on the bus +5 V rail.** Its job is to get 3.3 V logic over
the DAC's 0.7 × AVDD input threshold — 3.65 V at AVDD = 5.21 V. An AHCT gate on
a rail sagging to 4.75 V still drives 4.6 V, with a volt of margin. Leaving it
there keeps its switching current off the DAC's supply, and it means the only
thing hanging on the unprotected bus +5 V pin is a $0.30 buffer. A reversed or
row-offset ribbon that puts +12 V onto that pin kills the buffer and nothing
else, which is why the +5 V entry gets no protection network of its own.

### Module parts, chosen for build ease

**One op-amp part throughout: OPA2197.** Pitch scaling, all four mod channels
and the breath stage use the same dual RRIO part. It is rated to ±18 V, so on
±12 V it reaches roughly 11.9 V — comfortably past the 10 V output. Using a
cheaper part for the non-precision channels would save a few dollars on a
one-off and introduce a whole class of "which chip goes here" assembly error.
Not worth it.

**INA828 for the breath receiver.** ~~INA134~~ — this ADR named a *difference
amp* with on-chip matched resistors. It is an **instrumentation amp**, and the
distinction is the whole design: a difference amp's input impedance is its
resistor network, so source-impedance mismatch caps its effective CMRR, while
an in-amp's gigaohm inputs remove that coupling entirely and let the protection
resistors be whatever the filter wants. Topology, values and derivation are in
`hardware/module/breath-receive-stage.md`, which supersedes this paragraph and
ADR 0003's prose where they disagree.

**Standard eurorack hardware elsewhere:** PJ398SM jacks, Alpha 9 mm vertical
pots (linear taper — predictable for CV scaling), a rated SPST toggle for power,
and a 16-pin shrouded keyed IDC power header with Schottky diodes behind it.
Reversed ribbon cable is the classic Eurorack failure and the keying alone is
not worth trusting.

**1 kΩ series resistors on every CV output.** Standard practice, and it means
the module survives a short or someone patching output to output.

**The 10HP panel is laser or waterjet cut from DXF — same vendor and ideally the
same order as the aluminium key plate** (ADR 0009). Which also disposes of the
last objection to etherCON: its cutout is more complex than a round hole, and on
a laser-cut panel complexity is free.

### Power entry, and why this module is not a typical one

Eurorack practice for module power entry is well settled, and converges on:

- **Series Schottky diodes** on +12 V and −12 V for reverse polarity, 1N5817
  being the common choice for its low drop at module currents
- **A ferrite bead** in series for RF suppression — or, in many designs, a small
  series resistor of 2.2–10 Ω instead
- **Bulk electrolytics**, typically 10–100 µF per rail, for ripple and as a
  local reservoir
- **100 nF ceramics** at every IC

Two things make this module unusual, and both change the answer.

**It passes the instrument's current.** A typical module draws 20–100 mA. This
one draws its own analog current *plus* everything the instrument consumes:

| Rail | Draw |
|---|---|
| +12 V | **~404 mA typical** (45 mA module incl. the DAC regulator + **359 mA** instrument, derived in ADR 0005) — this row said "~320 mA (… ~275 instrument)" until 2026-09-21. Clamp-legal worst is higher. Measure at E6 before sizing the load switch** |
| −12 V | ~40 mA |
| +5 V | ~10 mA (level shifter only) |

That is about 15% of a modern rack supply's +12 V capacity — unremarkable, but
it **rules out the series-resistor variant**, which is harmless at 50 mA and is
not at 290 mA:

| Series R | Drop at 359 mA |
|---|---|
| 2.2 Ω | 0.64 V |
| 10 Ω | 2.90 V |

**So: ferrite beads, not resistors.** A 1N5817 drops roughly 0.3–0.4 V at this
current, leaving ~11.5 V at the instrument after cable drop, against a buck that
needs more than 6 V in. Ample.

**The instrument figure is the least trustworthy number in this document.** It
has already moved twice — once for the DAC regulator, once for the ~50 mA of
idle LED drivers on the real-time board (ADR 0007) — and a review's independent
estimate lands 100 mA above it, mostly on LED strip assumptions. Nothing
downstream should be sized from it. **E6 measures the real draw with a current
probe**, and the load switch's current limit is set from that measurement.

**It has two filtering jobs, not one.** Most modules only need to keep rack hash
out of themselves. This one also has to keep *itself* out of the rack, because
the instrument's buck converter is a switching load drawing pulsed current
through this module.

Those are different problems and they want separate treatment:

```
bus +12V ──┬──[1N5817]──[ferrite]──[bulk]──┬── module analog (op-amps)
           │                                │
           │                                └──[LM317LZ 5.21V]── DAC AVDD
           │                                                      │
           │                                              VREFOUT ─┴─[½ OPA2197]
           │                                              → pitch offset divider
           │
           └──[1N5817]──[ferrite]──[bulk]──[LT1641-1 + FET]── umbilical +12V
                                                  ↑                to the instrument
                                            panel toggle (enable only)

bus -12V ──[1N5817]─────[ferrite]──[bulk]── module analog
bus +5V  ────────────────[ferrite]──[bulk]── 74AHCT125 level shifter only
```

**Branch the two +12 V paths *before* the protection diode, each with its own
diode, ferrite and bulk capacitance.** An earlier revision of this diagram
branched *after* a shared 1N5817, and four reviewers arrived at the consequence
by four different routes: the instrument's current flows through the same diode
as the module's analog rail, so it modulates that diode's forward voltage by
~80 mV. **This ADR used to call that "about 20 cents of breath-correlated pitch
bend"; it is 0.00018 cents** (`power-entry.md`) — pitch references the DAC's
*internal* reference, not this rail, so the path is 75 mV -> LM317 line reg ->
39 uV on AVDD -> OPA2197 PSRR.

**Keep both diodes anyway, on the reasons that hold**: fault isolation between
the exported umbilical rail and the module's own analog rail, and HF isolation
between the two branches (`power-entry.md`). The split is visible by inspection
of the diagram above and needs no ground path to matter, which is why four
reviewers found it independently. A diode costs about twenty cents.
(`D-REVPOL` qty 3, ADR 0006.)

**The effect that genuinely *is* breath-correlated is the shared ground path**,
at 5.7–7.2 cents for the module's internal ground and ~4.8 cents for the rack
bus — two and three orders of magnitude above the diode term, and still open
(`power-entry.md`). Ranking the diode above them, as the old figure did,
inverted the priority order for the grounding work.

Branching also means the buck's pulsed draw is absorbed locally instead of
modulating the rail the pitch scaling stage is referenced to
— which is the whole point, since this module's analog section is precision and
most modules' are not.

**The branching survives review; the reasoning above does not.** A design review
found two errors in it, and the corrections change the parts rather than the
topology.

*A ferrite bead is a wire at the frequencies that actually matter here.* The
WS2815 strips modulate their current at the PWM rate, around 2 kHz. A bead is a
few hundred milliohms at 2 kHz and 47 µF does not hold a rail against a
200–400 mA square wave. The outcome is probably survivable — the op-amps have
~90 dB of PSRR down there — but it is survivable by accident, not by design.

*And the second claimed job is not done at all.* "Keeping the module out of the
rack" cannot work by branching, because both branches are common upstream at the
bus header. Filtering downstream of a shared node does not isolate that node.

Three corrections:

- **Bulk belongs at the load, not at the entry.** 470–1000 µF at each WS2815
  feed point, where the current actually swings, rather than at the module end
  of a 14-inch cable.
- **A real LC between the umbilical node and the buck input** — 10–47 µH of
  inductance, not a bead. That is the component that does the job the bead was
  credited with.
- **Ferrites rated ≥1 A, 1206 or 1210.** The common 0805 600 Ω part is rated
  around 300 mA, and both +12 V branches exceed that at the corrected current
  budget. A saturated bead loses its impedance entirely.

### The module's normal "off" state has the SPI bus floating

The panel switch cuts +12 V to the umbilical while the module stays powered from
the bus. So the ordinary powered-down state is: **module alive, DAC alive, and
SCLK / MOSI / CS floating** at the level shifter's inputs. That is a designed-in
operating mode, not a fault case, and it is the state the instrument spends most
of its life in.

Floating CMOS inputs oscillate and draw crowbar current — inside the precision
analog box — and a stray edge on CS latches a garbage word into the pitch DAC.

> ~~**So pull them, and gate the buffer:**~~
>
> - ~~**CS pulled to +5 V; SCLK and MOSI pulled to ground**, at the module end.~~
> - ~~**Gate the 74AHCT125's output enable from a real presence detect**, so~~
>   ~~"instrument absent" is a state the hardware knows about rather than one it~~
>   ~~stumbles into.~~
>
> **Superseded 2026-09-21, both bullets.** The gating is deleted — see "There is
> no presence detect" fifteen lines below — and `OE` is tied to ground,
> permanently enabled.
>
> **The pulls survive, but not as written.** `bom.csv` specifies `R-SPI-PULL`
> ×**6**, three at each end, and the cable-side `CS` pulls to **3V3, not +5 V**:
> pulled to 5 V it drives 430 µA continuously through the unpowered ESP32's
> input clamp. The floating-input problem this section identifies is real and
> the pulls are the whole answer to it.

**It needs a bench override.** ADR 0004 and the ROADMAP both promise the
module can be brought up standalone from "any dev board with a test pattern and
a multimeter" (E6–E12), and a dev board on a patch lead drives nothing into the
breath pair — so the comparator reads "absent" and the buffer stays disabled,
and the module produces no CV at all. A jumper or a solder link that forces
`OE` low is two pads. Without it the gating locks out every module milestone
before the instrument exists.

> ~~That OE gating is the reason the power switch had to move to the module~~
> ~~(ADR 0005). With a switch at the instrument end, "+12 V present on the~~
> ~~umbilical" would no longer mean "instrument alive", and the gating would fail~~
> ~~in exactly the state it exists for. The relocation was load-switch-shaped but~~
> ~~this is what made it necessary.~~
>
> **Withdrawn 2026-09-21.** With the gating deleted, this paragraph claims to
> identify what "made it necessary" and points at nothing. **The relocation is
> unaffected**, because ADR 0005 gives two independent and sufficient reasons
> that never involved `OE`: the Recom R-78E5.0 **has no enable pin**, so a
> switch at the instrument end has nothing to switch; and the WS2815 strips run
> on raw +12 V *upstream* of the buck, so killing the buck would leave an
> instrument still lit and still drawing current with its logic dead.

### There is no presence detect, and the buffer runs unconditionally

**Both versions are deleted.** The original gated the level shifter's `OE` from
"+12 V present on the umbilical", which is downstream of the module's own load
switch and therefore reads *present* with nothing plugged in — it failed in
exactly the state it existed to detect. Its replacement watched the breath line
through an LM311, and review found three independent faults with it: the
threshold sat **inside the breath signal's own range** (the sensor is a
differential part with its reference port open to the cavity, so drawing breath
moves toward the trip point), it **locked out every standalone module
milestone** because a dev board on a patch lead drives nothing into that pair,
and it **failed toward "present"** if the reference buffer died or a trimmer
wiper opened.

**`OE` is tied enabled.** What the gating was protecting against — floating
CMOS at the DAC while the instrument is off — is what `R-SPI-PULL`'s six
resistors are for, and running the buffer unconditionally is what every
surveyed Eurorack module does.

**The panel LED becomes an ordinary power indicator** off the module's own
rail, like every other module's.

### Why the module does not need to know, and where the knowing went

The module has no processor and the umbilical is write-only, so anything it
decides has to be decided from analog signals at its own end. That is all the
comparator ever was. The question is therefore not *how* it should sense the
instrument but *whether it needs to* — and each of its three jobs has a better
home:

| Job | Where it goes |
|---|---|
| Gating the buffer | Deleted — the idle pulls do it, as they do everywhere else |
| Panel LED | The module's own rail, which is what a power LED means |
| Health reporting | **The instrument**, which has a display, a web app and the data |

**The instrument already digitises breath** for note gating, and that copy also
drives the strips and the matrix (ADR 0014). Nothing about the lights ever
needed to travel to the module, through the panel knobs, and back.

**What is genuinely given up**, recorded as accepted rather than dropped: the
instrument's ADC reads breath *before* the umbilical, so a broken `BREATH` or
`AGND` conductor is invisible to it. The instrument would report a healthy
channel while the module received garbage. The comparator was the only thing
watching the far end of that cable.

In practice it is audible immediately, and it is a fault in a **replaceable
cable** rather than in anything sealed into the body — which is the trade that
makes it acceptable.

### A stuck CV is worse than a dead one

If the real-time board hangs mid-note, the DAC holds its last written value and
**the rack drones forever.** Nothing in the design notices. That is a worse
failure than the module going dark, because it is loud, it is indefinite, and
the instrument in your hands will not respond to anything you do with it.

> **Withdrawn 2026-09-21.** The mechanism below was built and then deleted,
> because it could not catch the failure this section describes. It retriggers
> on `CS` edges, and firmware refreshes every channel every pass — so a hang
> *above* the output loop emits healthy edges forever. What it could catch was
> the link going away, and that is now uncovered: **pull the umbilical mid-note
> and the rack holds the note until the module's toggle is flipped.** The
> reasoning, the cost and the no-new-parts way to get the link coverage back
> are in `hardware/module/digital-and-supervision.md`. The paragraphs below are
> kept because the problem they describe is still real.

~~**Assert `CLR` at the module when no valid frame has arrived for N milliseconds.**~~
A few gates or a retriggerable monostable, at the module end where it is
independent of the thing that hung. The DAC's own `CLR` pin already does exactly
what is wanted — an A/C grade part clears to zero scale, which parks pitch
subsonic and the mod channels at 0 V (ADR 0006), the same safe state as rack
power-on.

Size N so a busy loop cannot trip it but a hang is caught in well under a
second. This also gives umbilical disconnection the same behaviour as a hang,
which is correct: both mean "the instrument is no longer telling me anything."

#### The watchdog's scope is the DAC channels, and breath is outside it

Stated rather than left implicit, because three reviewers read the omission as a
hole. `CLR` reaches pitch and the four mod channels. **Breath does not pass
through the DAC at all** (ADR 0003), so the watchdog has no authority over the
one jack that is usually driving a VCA — and on the face of it that is the
failure this section declares unacceptable, happening on exactly the channel the
mechanism cannot reach.

**It is not the same failure, and the difference is the whole reason breath is
analog.** A stuck CV is a *digital* artefact: a register holding a number nobody
is refreshing. An analog path has no register to hold. It follows the sensor,
the sensor follows the room, and a mouthpiece nobody is blowing into reads
ambient — so the jack falls to wherever the panel offset knob left it and stays
there. That is not a drone; it is a correct reading of "nobody is playing."

The same argument covers the second route in: on a sagging cable the buck drops
out at 8 V while the REF5050 and OPA2197 hold regulation to ~7.2 V, so the MCU
dies, SPI stops, `CLR` fires, and breath keeps working. Breath *still working*
when everything else has parked is the designed behaviour, not a gap in it.

**What is accepted, explicitly:** a genuinely stuck *sensor* — a blocked
restrictor holding pressure, or a part failing to a mid-scale output — would
drone, and nothing in the design would catch it. That is a sensor-failure mode
rather than a firmware-hang mode, it is what the logged auto-zero correction
exists to make visible (ADR 0006), and it does not argue for a mute switch: a
series FET in the project's one DC-accurate analog output would bring its own
`R_on`, leakage and charge injection to defend against a failure that path
cannot have.

**E10 checks it rather than assuming it:** with the mouthpiece at rest, pull the
umbilical mid-note and watch the jack. If it parks quietly, this paragraph is
right. If it does not, we find out before anything is bonded.

**`R-SPI-SER` ×3, 100 Ω, at the driving end** — on `SCLK`, `MOSI` and `CS`
alike. Source termination into the cable's own ~100 Ω. It also makes
SYNC-signal regeneration at the module unnecessary, which was the alternative
under consideration.

> **This read "220 Ω in series on MOSI" until 2026-09-21, and was wrong three
> ways.** One resistor, not three — which left `SCLK`, the fastest edge on the
> cable, unterminated. 220 Ω, not 100 Ω — which dwells ~20 ns per edge below
> the 74AHCT125's `V_IH`. And it was derived from an RC-corner model that does
> not apply to a 2 m transmission line. The refdes matters too: `carrier.md`
> previously drew `R-SCLK-SER` / `R-MOSI-SER` / `R-CS-SER`, none of which were
> ever in `bom.csv`. There is one part, `R-SPI-SER`, qty 3.

Sources: Doepfer's A-100 technical documentation for the bus and supply
conventions; ModWiggler's module-power-entry threads for the community consensus
on diodes, ferrites and reservoir values.

### Considered and declined: an octave switch on the panel

A three-position toggle for +1 / 0 / −1 octave was proposed and is **not
built**. Recorded because the reasoning generalises.

**It would have had to be analog**, since the module has no processor and the
umbilical is write-only — so a panel switch there cannot reach firmware. And an
analog octave shift is not cheap: the pitch stage is non-inverting, so anything
injected at its inverting node adds *gain* rather than offset (the defect
`R-OFFINJ` was deleted for). The only clean point is `V_ref`, which would have
to switch between 1.500 / 2.500 / 3.500 V — and reaching *above* 2.500 V from a
2.500 V reference needs an op-amp half and 0.1 % resistors, because 1 % on the
step is 12 cents. Plus a toggle on a panel already at 107 mm of ~110 mm usable.

**And the instrument already has octave control, twice.** The four left-thumb
keys are octave/register keys in the conventional woodwind arrangement — the
2021 firmware used three left-thumb inputs across a four-octave span — and
ADR 0010 reserves three spare chain bits for dedicated octave up/down switches
besides.

Doing it in firmware is free, and **the reason it is free is worth stating**
because it was briefly got wrong: the DAC's 0.25–4.75 V window reserve is
*calibration* headroom, not a transposition limit. The playable range occupies
under a third of the 9 V output span, so firmware can shift the whole mapping
by an octave with room to spare.

### Module design principles

**The module is dumb.** Jacks, knobs, connector, power switch, analog. No menu,
no encoder, no screen. All UI lives on the instrument, which already has a
display and a processor. That discipline is what kept the panel inside 10HP
rather than 10 or 12.

**The module's power switch is the only power switch in the system.** The
instrument has none (ADR 0005), so the panel toggle is the single point of
control — and it does not break the current itself. It drives a **current-limited
load switch** on the umbilical +12 V feed — an LT1641-1 and an external FET,
since every one-chip 12 V eFuse fails the package policy (ADR 0005) — which adds inrush
limiting into the instrument's bulk capacitance and short-circuit foldback on a
crushed cable or a half-inserted connector. A bare toggle would take that surge
on its contacts and pass a umbilical fault straight through to the rack's rail.

Input filtering on the +12V rail so the instrument's local buck converter does
not inject switching noise back into the rack.

### Grounding: one origin, named, before the board is laid out

This is a layout constraint rather than a part, and it is recorded here rather
than in a review document because that is the difference between a constraint
and a note nobody reads. It is free at layout and a bodge wire or a respin
afterwards.

**The origin is the Eurorack power inlet's ground pin.** Every milliamp in the
module leaves through it, so it is the one point entitled to be called ground.
Everything else is defined relative to it and joins it *there*, not wherever two
pours happen to meet.

Four returns arrive at this board and they are not comparable:

| Return | Carries |
|---|---|
| `PWR_GND`, from the etherCON | **~360 mA** of instrument current — LEDs, both dev boards, the matrix |
| `DIG_GND`, from the etherCON | SPI switching current |
| Module analog return | Op-amps, DAC `AVDD`, the pitch stage's reference |
| `AGND`, from the etherCON | **Nothing.** It is an in-amp input, not a ground (ADR 0003) |

**The mechanism, so the rule is not cargo cult.** If `PWR_GND` shares copper
with the analog return for even a centimetre, 360 mA develops an IR drop across
that shared length and the pitch stage's reference sits on top of it. The
current varies with the lighting and with what the MCU is doing, so the offset
varies with it — which is why a review measured this as **5.7–7.2 cents of
breath-correlated pitch bend** rather than as a fixed error a trimmer would
remove once. It is the same shape as the shared-Schottky term fixed above, by a
different path.

So:

- **`PWR_GND` runs from the etherCON to the star point on its own copper**,
  touching no other return on the way. It is the dirtiest net on the board and
  it is the one that must be kept to itself.
- **`DIG_GND` likewise** — its own path to the star.
- **The analog return is its own region**, joining at the star and nowhere else.
  The DAC's `AVDD` return and the in-amp's `REF` tie belong in it.
- **`AGND` is not in this list.** It terminates at the in-amp's IN+ and at the
  two 1 MΩ bias resistors, and that is all it does. Anything that makes it a
  return path breaks the reason a 2 m analog run works at all.

**The rack's own bus ground is not ours to fix**, and it contributes a further
~4.8 cents: the module shares a 16-pin ribbon return with every other module in
the case. The only lever is which slot the module sits in relative to the noisy
ones, which is a patching decision. E6 measures it rather than trusting the
figure.

### Panel, top to bottom

Connector, power switch and LED — the system's only power switch, since the
instrument has none — two breath knobs, then six jacks in two columns: **PITCH** and **BREATH** silkscreened, **MOD 1–4** numbered with a
write-on strip. Roughly 107 mm of ~110 mm usable height — full but workable.

Print the panel at 1:1 on paper and check it is actually usable before cutting.

## Connector: Neutrik etherCON, both ends

**The cable is a consumable.** That is the decision, and everything else follows
from it.

Bare 8P8C was rejected early — the retention tab is the most-broken connector in
the industry and it has no strain relief. That matters here not because of
stages or trip hazards, but because **the instrument moves constantly while
being played** and the cable flexes at the connector every time. That is true in
a studio. etherCON is an RJ45 inside a latching metal shell, which keeps the
electrical standard and replaces the failure mode.

### What the alternatives measured

**The panel is 10HP** — `(10 × 5.08) − 0.3` = **50.50 mm**, +0/−0.2. It went
6HP → 8HP when the connector was chosen, and **8HP → 10HP on 2026-09-21** when
a review found the height budget was over and a third control was added. See
below.

| | **etherCON D** | M12 X-coded | Hirose HR10A |
|---|---|---|---|
| Panel hole | **⌀24.0 mm min** | ~16 mm | 10.2 mm |
| Aluminium left each side, at 10HP | **13.25 mm** | ~17 mm | ~20 mm |
| *(at 8HP)* | *8.17 mm* | *~12 mm* | *~15 mm* |
| *(at the original 6HP)* | *3.09 mm* | *~7 mm* | *~10 mm* |

> **The etherCON column is now read off the vendor drawing**, not estimated:
> Neutrik **ST-NE8FDP, Aend-Index B**, held in the repo at
> `datasheets/connectors/NE8FDP.pdf` with its DXF beside it. The bore is
> **⌀24.0 mm as a minimum**, not the 23.8 mm this table carried — so 23.8 was
> not merely imprecise, it was **below the specified minimum**. Every
> derived figure moves by 0.1 mm and none of them changes a decision.
>
> The same drawing settles the mounting pattern, which three reviews recorded
> as unobtainable: **two clearance holes only, diagonally opposite, ⌀3.2 mm
> min, at 19 ±0.1 mm × 24 ±0.1 mm** — centres at (±9.5, ±12.0) from the bore.
> The holes sit **inboard of the flange edge** (11.1 mm out against the
> flange's 13.0 mm), so the flange, not the screw, is the near-edge feature.
> A review's guess that the web is "≤2.09 mm and probably less" is wrong and
> is retired.
| Current per contact | ~1.5 A | **0.5 A** | 2 A |
| Cable | **any Cat5e patch lead** | off-the-shelf M12-X | build it yourself |

**M12 X-coded is ruled out on current, not on cable.** An earlier revision of
this section listed its cost as "industrial-looking custom cable", which was
wrong twice over: M12 X-coded *is* industrial Ethernet, with off-the-shelf
shielded assemblies in 1, 3, 5 and 10 m — and its real problem is that
8-contact X-code sits at the 0.5 A end of the M12 rating range. Against an
instrument drawing ~400 mA that is 80 % of rating, on a figure that has already
moved twice.

**HR10A is mechanically better on every axis and loses on one that matters more
than all of them.** A 10.2 mm hole and 2 A per pin would solve both panel
problems outright. But the cable is the most-flexed, most-abused part of the
system, Ethernet patch lead is not flex-rated and *will* eventually fail, and
when it does the question is whether the instrument is out of action for an
afternoon with a crimp tool or for the time it takes to open a drawer.

**So: etherCON, and treat cable failure as routine.** Keep spares. Replace the
lead at the first sign of intermittency rather than diagnosing it.

### The panel is 10HP, and this is the first time the height was derived

**6HP → 8HP was the connector.** At 6HP a 24.0 mm bore in a 30.18 mm panel
leaves two aluminium strips **3.09 mm** wide — a fit the panel passes and a
stiffness test it does not, with a cable that tugs sideways every time the
instrument moves. Worse, the connector body extends 30–40 mm behind the panel
while the jacks put the PCB about 7 mm behind it, so clearing it needs a
~26 mm notch in a ≤28 mm board. **That severs the board**, which is why a
review concluded the module had to become two boards. 8HP dissolved all of it.

**8HP → 10HP was the height, and a third knob.** A reviewer rebuilt the panel
bottom-up from real component envelopes and got **~115 mm against ~110 mm
usable — already over**, taking every favourable option (toggle and LED
sharing a row, pots side by side, 13 mm jack pitch); stacking the pots gives
133 mm. It also found that **this ADR's own "107 mm of ~110 mm usable" figure
is asserted twice and derived nowhere**, and that two 20 mm knobs do not fit
side by side in 40.34 mm at all — 16 mm is the ceiling, against this ADR's
claim of "16–20 mm".

Then `POT-RESP` was added (see `breath-output-stage.md` §4), making three
controls.

**10HP is 50.50 mm**, and the win is not the width itself — it is that three
pots fit in **one row instead of two**, which deletes a whole 20+ mm row from
a budget that was already over. Derived, finally:

| | Height |
|---|---|
| Label / title band | 5 mm |
| **Three pots across** — gain, offset, response | 22 mm |
| Jacks, 3 rows × 2 columns at 13 mm pitch | 39 mm |
| etherCON (31 mm tall) with the toggle and LED beside it | 31 mm |
| **Total** | **97 mm against ~110 mm — 13 mm spare** |

Width: **13.35 mm of aluminium each side of the bore**, 12.25 mm of visible
panel each side of the flange.

> **The knob size is now the binding constraint, and it is a real cost.**
> Three pots across 50.50 mm with 3 mm gaps needs **≤14 mm knobs** `[calc]`:
>
> | Knob | 3 across + gaps | |
> |---|---|---|
> | 20 mm | 66 mm | no |
> | 16 mm | 54 mm | no |
> | 15 mm | 51 mm | no |
> | **14 mm** | **48 mm** | **fits** |
>
> So 10HP buys the height back by *spending* the knob size that 8HP was
> supposed to have bought. That is the honest trade: **three controls at
> 14 mm beats two controls at 16 mm**, but this ADR should stop claiming
> 16–20 mm knobs.

The cost is **four horizontal pitches** against the original 6HP, in a rack
the design scope calls generous, and nothing at the laser cutter — a 2 mm
aluminium rectangle costs the same whatever its width.

**Brace the connector to the PCB anyway.** It is free on a board being
designed regardless, and it puts the load path into the board rather than the
panel. At 10HP this is good practice rather than a structural necessity.

> **Still a 1:1 paper check at M4, and now it has numbers to check against.**
> The 97 mm above is built from `[from memory]` component envelopes — the
> Neutrik drawing, the Thonkiconn panel dimension and the pot bushing were all
> behind a blocked proxy through three review waves. **The layout is credible
> and it is not verified.** Print it and lay the real parts on it.

**The instrument end still needs a backing plate, not oak** — and the etherCON D
is rated for a **maximum 4 mm panel thickness**, so it cannot mount through 6 mm
oak at all. See ADR 0009.

### Cable specification, which is not "any Ethernet cable"

Close, but two things are not optional:

- **Stranded patch cable, never solid-core installation cable.** Solid core
  work-hardens and fractures under repeated flexing, which is this cable's
  entire life. This is the easiest thing in the project to get wrong by buying
  whatever is in the drawer.
- **Shielded (STP/FTP) preferred.** Twisted pairs are what make the analog
  breath channel survive (ADR 0003) and any Cat5e has those, but the shield is
  free at this price and the breath pair is the one signal with no digital
  margin to spare.
- **Straight-through, and this one is a hazard rather than a preference.** Not
  every RJ45 lead is straight-through, and the wrong ones are visually
  identical to the right ones.

| Lead type | Swaps | Against the map below |
|---|---|---|
| Rollover / console | 1↔8, 2↔7, **3↔6**, 4↔5 | 3 and 6 are **+12 V and PWR_GND** — reverse polarity into the instrument |
| 10/100 crossover | (1,2) ↔ (3,6) | **BREATH/AGND ↔ +12 V/PWR_GND** — 12 V onto a buffer output |

This ADR fits two Schottkys on the rack connector because "keying alone is not
worth trusting", for a connection made *once* in the module's life, and then
trusted a generic consumable patch lead completely. The lead is the part most
likely to be swapped in a hurry, in the dark, from a drawer.

**Neither case needs a new idea, because both are already nearly covered:**

- The crossover case is covered *by design*. ADR 0003 put the breath buffer on
  +12 V precisely so that a sustained +12 V fault on that line sits at the rail
  rather than above it, and the instrument-side 1 kΩ plus the module-side 10 kΩ
  and BAV99 bound the rest (`hardware/module/breath-receive-stage.md`).
- The rollover case needs **one shunt SS34 at the instrument's power entry**,
  cathode to the +12 V pin. Reversed, it conducts hard, the module's LT1641-1
  sees a short, **latches off**, and the panel LED goes out. The load switch
  becomes the fuse, which is what it was for.

A pin-map reorder was considered and declined: a gigabit crossover swaps the
other pair group as well, so no mapping is safe against every lead. A diode is.

### Pin assignment, which the connector choice now constrains

A standard patch lead's twisted pairs are fixed by T568B: **(1,2), (3,6), (4,5),
(7,8)**. The conductor budget above has to map onto those, and the mapping is
not arbitrary — pairs untwist for about 13 mm inside an RJ45 plug, so pin
adjacency at the connector is where crosstalk actually happens.

| Pins | Pair | Signal |
|---|---|---|
| 1, 2 | ✓ | **BREATH / AGND** |
| 3, 6 | ✓ | +12V / PWR_GND |
| 4, 5 | ✓ | **SCLK / MOSI** — *revised 2026-09-21* |
| 7, 8 | ✓ | **CS / DIG_GND** — *revised 2026-09-21* |

**`SCLK` and `CS` swapped places.** The previous map paired `MOSI` with `CS`,
which put **two unrelated fast digital signals in one twisted pair with no
return conductor between them**. Twisting exists to make a pair see identical
interference so it cancels; twisting two aggressors together instead is the
most efficient coupling structure available. Two reviewers independently
computed **365–907 mV of saturated intra-pair crosstalk** (saturated because
the 20 ns round trip far exceeds the ~2 ns edge) against `CS`'s **678 mV
`V_IL` margin**, and independently proposed this same swap. It takes the
margin from about **1.9:1 to 6200:1**.

**It had to be `CS` that got the ground.** `CS` frames the word: a glitch
restarts the bit count mid-message, so every bit lands in the wrong field —
including software-reset and internal-reference-enable. This ADR deleted
`MISO`, so firmware can never read back what the DAC received. **It is the
only corruption in the digital path that does not self-heal on the next
250 µs update.**

**Pairing `SCLK` with `MOSI` is safe by construction**, not by luck: the
receiver samples `MOSI` only on a `SCLK` edge, so whatever they couple into
each other lands at the moment nobody is looking.

> **What this section got wrong, and it is instructive.** The original
> reasoning above is about the ~13 mm untwisted region inside an RJ45 plug,
> and that reasoning is sound — a reviewer costed that effect at **15 mV**.
> It is 25–60× *smaller* than the intra-pair coupling the same paragraph
> created by pairing two aggressors. The analysis was careful about the
> visible mechanism and never asked what the pairs themselves were doing.
>
> This ADR also asserted twice that "each signal sits against a ground in its
> own twisted pair". Its own table never did.

**The power pair still guards the analog pair.** BREATH at pin 1 is adjacent
only to its own sense return, and the two DC conductors of the power pair sit
between the analog pair and both digital pairs. That part of the original
reasoning survives the swap intact, and a reviewer measured the result:
`SCLK` → `BREATH` is **57 nV at the jack**, which is **zero breath counts**.

**Considered and rejected: moving the SPI signals off pins 4/5 entirely.**
Published RJ45-for-other-purposes standards leave 4 and 5 unconnected so that
a misplug into a PoE or telephone source destroys nothing. That is a real
convention, but it protects against plugging the instrument into a network
socket — and there are exactly 8 conductors for exactly 8 signals, so 4/5
cannot be vacated without deleting one. **For a one-off instrument that lives
beside its own module, the crosstalk fix is the one worth having.** Label the
lead.

Confirm at E11 with a logic analyser and a scope on the real cable at length —
that milestone exists precisely to catch what this reasoning gets wrong, and
this time it has something specific to look for: threshold dwell and runt
pulses on `CS`.

## Open

**Which etherCON variant at each end.** Feedthrough (NE8FDP-class) presents a
plain RJ45 on the back, so the instrument end could take a short patch lead to a
jack on the carrier instead of eight soldered wires inside a body that cannot be
reopened — genuinely attractive. The cost is two more contact interfaces in
every signal, including the +12 V path and the analog pair. A solder-tag or
PCB-mount variant avoids that and costs a fiddlier assembly. **Decide with the
datasheets in hand at E12 and M7**, not now.
