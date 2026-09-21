# 0004 — CV interface module and umbilical

**Status:** Accepted

## Context

The instrument's output target is a Eurorack system. The original plan put the
DAC, analog scaling, bipolar supply and jacks inside the instrument body, on
battery power (see ADR 0005, superseded).

Putting the analog section in a rack module instead — connected to the
instrument by a single cable — solves several problems at once.

## Decision

**An 8HP Eurorack module holding all analog output hardware, connected to the
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

```
+12V, GND, GND      power (3.3V derived locally in the instrument, small buck)
SCLK, MOSI, CS      SPI to the DAC, ~2 MHz
MISO                unused today — module ID and presence detect
spare               reserved
```

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
of Cat5 at a speed the instrument turns out to need. `R-MOSI-SER` at 220 Ω with
~200 pF of cable is a ~7.9 MHz corner, so 2 MHz has margin; if E11 wants more,
that resistor comes down toward 100 Ω, which is closer to a real source match
on Cat5's ~100 Ω anyway.

Plain single-ended SPI at a couple of MHz over twisted pair is still
unremarkable. **RS-485 returns to contingency status**, not a likely
requirement.

### Revised conductor budget

```
+12V      / PWR_GND     power, and the presence signal
SCLK      / DIG_GND     SPI to the DAC, ~1 MHz
MOSI      / CS
BREATH    / AGND        analog, band-limited ~500 Hz, sense return
```

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

- **A local 5.25 V regulator off the protected +12 V rail** for the DAC's AVDD
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

**The 8HP panel is laser or waterjet cut from DXF — same vendor and ideally the
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
| +12 V | ~320 mA (45 module incl. the DAC regulator, ~275 instrument) — **estimated, and a review put it nearer 410–430 mA. Measure at E6 before sizing the load switch** |
| −12 V | ~40 mA |
| +5 V | ~10 mA (level shifter only) |

That is about 15% of a modern rack supply's +12 V capacity — unremarkable, but
it **rules out the series-resistor variant**, which is harmless at 50 mA and is
not at 290 mA:

| Series R | Drop at 290 mA |
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
           │                                └──[LM317LZ 5.25V]── DAC AVDD
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
~80 mV — about **20 cents of breath-correlated pitch bend**, needing no ground
path at all and visible by inspection of the diagram itself. The second diode
costs about twenty cents and is the whole fix. (`D-REVPOL` qty 3, ADR 0006.)

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

**So pull them, and gate the buffer:**

- **CS pulled to +5 V; SCLK and MOSI pulled to ground**, at the module end.
- **Gate the 74AHCT125's output enable from a real presence detect**, so
  "instrument absent" is a state the hardware knows about rather than one it
  stumbles into.

That OE gating is the reason the power switch had to move to the module
(ADR 0005). With a switch at the instrument end, "+12 V present on the
umbilical" would no longer mean "instrument alive", and the gating would fail in
exactly the state it exists for. The relocation was load-switch-shaped but this
is what made it necessary.

### Presence detect is a comparator on the breath line, not +12 V on the cable

**Sensing umbilical +12 V does not detect the instrument.** That node is
downstream of the module's *own* load switch, so it is present whenever the
panel toggle is on — with nothing plugged in at all. It fails in precisely the
state it exists to detect, and part of the argument above rests on it.

A free and much better detect already exists in the circuit, and it comes from
the breath receiver's own resting behaviour:

| State | At the in-amp |
|---|---|
| Cable unplugged | R4/R5 pull both inputs to module `AGND` → output sits **at 0 V** |
| Instrument alive | Sensor's designed +0.2 V zero-pressure floor → output sits **at −437 mV** |

**One comparator against a fixed threshold — say −200 mV — reports all of it at
once**: cable connected, +12 V actually reaching the far end, REF5050 alive,
sensor alive, buffer alive, and both analog conductors intact. Nothing else in
the design reports any of those, and nothing extra is needed to get them.

**Fixed is the operative word, and it only became true recently.** While the
in-amp's `REF` pin was driven by a firmware ambient-zero, both rows of that
table moved with it — the comparator would have been chasing a threshold that
the auto-zero was walking, and a slow drift could have tripped it. Grounding
`REF` (ADR 0003) turns the detect into a comparison against a rail.

So: an LM393 half, open-collector, pulled to the bus +5 V rail, driving all four
`OE` pins. Hysteresis from a three-resistor network; the second half of the
package is spare. The +12 V divider that used to do this job is deleted rather
than kept alongside — it answers "is my own switch on", which the panel LED
already answers.

**The same signal is the module's only health indicator**, so bring it to the
panel LED too: lit means the instrument is there and its analog front end is
working, rather than lit means a toggle is up.

**Note the 74AHCT125 is a plain buffer, not a Schmitt trigger.** If the umbilical
turns out to need edge cleanup at length, that wants a 74AHCT14 — decide it at
E11 with a logic analyser on the real cable, not now.

### A stuck CV is worse than a dead one

If the real-time board hangs mid-note, the DAC holds its last written value and
**the rack drones forever.** Nothing in the design notices. That is a worse
failure than the module going dark, because it is loud, it is indefinite, and
the instrument in your hands will not respond to anything you do with it.

**Assert `CLR` at the module when no valid frame has arrived for N milliseconds.**
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

**220 Ω in series on MOSI at the driving end.** Source termination on the one
line that runs the full umbilical carrying data. It also makes SYNC-signal
regeneration at the module unnecessary, which was the alternative under
consideration.

Sources: Doepfer's A-100 technical documentation for the bus and supply
conventions; ModWiggler's module-power-entry threads for the community consensus
on diodes, ferrites and reservoir values.

### Module design principles

**The module is dumb.** Jacks, knobs, connector, power switch, analog. No menu,
no encoder, no screen. All UI lives on the instrument, which already has a
display and a processor. That discipline is what kept the panel inside 8HP
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

**The panel is 8HP, not 6HP** — `(8 × 5.08) − 0.3` = **40.34 mm**, +0/−0.2. See
below for why that changed after the connector was chosen.

| | **etherCON D** | M12 X-coded | Hirose HR10A |
|---|---|---|---|
| Panel hole | 23.8 mm | ~16 mm | 10.2 mm |
| Aluminium left each side, at 8HP | **8.27 mm** | ~12 mm | ~15 mm |
| *(at the original 6HP)* | *3.19 mm* | *~7 mm* | *~10 mm* |
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

### The panel went to 8HP because of this connector

At 6HP the choice was survivable but ugly: a 23.8 mm hole in a 30.18 mm panel
leaves two aluminium strips **3.19 mm** wide — a fit the panel passes and a
stiffness test it does not, with a cable that tugs sideways every time the
instrument moves. Worse, the connector body extends 30–40 mm behind the panel
while the jacks put the PCB about 7 mm behind it, so clearing it needs a ~26 mm
notch in a ≤28 mm board. **That severs the board**, which is why a review
concluded the module had to become two boards.

**8HP dissolves all of it.** The panel is 40.34 mm: **8.27 mm of aluminium each
side of the bore**, 7.17 mm of visible panel each side of the flange, and enough
web left at the notch that the module stays one board. It also frees the panel
height budget, which at 6HP overran by 0.5 mm at a 13 mm jack pitch, and it
allows a normal 16–20 mm knob instead of the ~13 mm the 15 mm pot centres
forced.

The cost is **two horizontal pitches** in a rack the design scope calls
generous, and nothing at the laser cutter — a 2 mm aluminium rectangle costs the
same whatever its width.

**Brace the connector to the PCB anyway.** It is free on a board being designed
regardless, and it puts the load path into the board rather than the panel. At
8HP this is good practice rather than a structural necessity.

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
| 4, 5 | ✓ | MOSI / CS |
| 7, 8 | ✓ | SCLK / DIG_GND |

**The power pair's two DC conductors sit between the analog pair and both
digital pairs, acting as a guard.** BREATH at pin 1 is adjacent only to its own
sense return; SCLK, the fastest edge in the system, is at the far end. Nothing
with a sharp edge is ever adjacent to the analog pair.

Confirm at E11 with a logic analyser and a scope on the real cable at length —
that milestone exists precisely to catch what this reasoning gets wrong.

## Open

**Which etherCON variant at each end.** Feedthrough (NE8FDP-class) presents a
plain RJ45 on the back, so the instrument end could take a short patch lead to a
jack on the carrier instead of eight soldered wires inside a body that cannot be
reopened — genuinely attractive. The cost is two more contact interfaces in
every signal, including the +12 V path and the analog pair. A solder-tag or
PCB-mount variant avoids that and costs a fiddlier assembly. **Decide with the
datasheets in hand at E12 and M7**, not now.
