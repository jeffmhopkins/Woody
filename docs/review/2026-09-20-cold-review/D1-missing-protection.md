# D1 — Missing protective and supervisory circuitry

**Scope of this review:** absence only. Nothing here is a claim that a circuit
that *is* specified is wrong; other reviewers have that. Every finding is a
circuit, a rule or a supervisory function that a design of this shape normally
has and this one does not.

**Judged against the stated scope:** one-off, tethered, home studio, bench
available, generous rack supply, hand assembly, **body bonded shut and never
reopened**. The last of those changes the arithmetic more than anything else in
the brief. In an ordinary one-off, the cost of an unprotected node is a part and
an afternoon. Here, for everything inside the instrument, it is the instrument.
That does not justify protecting everything — it justifies protecting the small
number of nodes where an *external* event can reach an *internal* part.

**What is already there,** so the absences are read against it: 1N5817 reverse
diodes on ±12 V at the module; ferrites ≥1 A and bulk at the load; a
current-limited load switch on the umbilical feed; a 500 mA PPTC at the
instrument entry; a TVS array at the instrument's umbilical entry; 1 kΩ + BAV99
on every CV jack; 1 kΩ on every op-amp input driven by the DAC; a ≥10 kΩ ADC
divider sized for 5 V-before-3.3 V sequencing; SPI idle pulls and OE gating at
the module; a retriggerable monostable asserting DAC `CLR` when frames stop;
the aluminium plate bonded to `PWR_GND`; internal current limit and thermal
shutdown inside the LM317, the R-78E5.0, the load switch and the OPA2197.

That is a better-than-average protection story for a hobby instrument. The gaps
below are what it does not cover.

**Summary**

| # | Missing | Sev | Verdict |
|---|---|---|---|
| 1 | Bias-current return for the module's in-amp inputs | High | **ADD** |
| 2 | Reverse-polarity protection at the instrument's umbilical entry | High | **ADD** |
| 3 | Clamp on `BREATH` for the case where the instrument's own rail is absent | High | **ADD** |
| 4 | Defined level on the 18 key-switch inputs, and input filtering | High | **ADD** |
| 5 | Reverse blocking between the instrument's 5 V rail and USB VBUS | High | **ADD** |
| 6 | A 12 V-capable current limiter (the specified part is a 5 V part) | High | **ADD** (precondition) |
| 7 | Power-on reset and undervoltage hold on the DAC `CLR` watchdog | Med-High | **ADD** |
| 8 | Closed-loop thermal protection; any temperature sensor at all | Med-High | **ADD** (free) |
| 9 | TVS array at the *module* end of the umbilical | Medium | **ADD** |
| 10 | Series current limiting on `SCLK` and `CS` at the driving end | Medium | **ADD** |
| 11 | Defined state on the WS2815 data lines with the 5 V rail absent | Medium | **ADD** |
| 12 | Idle pulls on the DAC side of the level shifter | Medium | **ADD** |
| 13 | Any fault or presence indication on the module panel | Medium | **ADD** |
| 14 | Watchdog discipline, link liveness, reset-reason reporting | Medium | **ADD** (firmware) |
| 15 | Shield and connector-shell bonding rule | Medium | **ADD** (rule) |
| 16 | Overvoltage clamps on the module's rack rails and on +5 V | Low-Med | **ADD** |
| 17 | USB-port ESD protection is assumed, not verified | Medium | **VERIFY**, then decide |
| 18 | Inrush limiting from the rack bus into the module | Low | **ACCEPT** + rule |
| 19 | Anything preventing the umbilical being plugged into a network port | Low | **ACCEPT** + label |
| 20 | Isolation between sections | — | **ACCEPT** explicitly |
| 21 | Decided protection that never reached the BOM | Med | **ADD** (bookkeeping) |

---

## 1. There is no bias-current return path for the module's instrumentation-amplifier inputs, so the breath CV goes to a rail whenever the instrument is off

**Severity: High.** This one fires in normal use, every time, not in a fault.

**Where it goes:** module, at the INA821/INA828's two input pins.

**What fails without it.** ADR 0003's R35 rule is explicit: at the module end
`AGND` connects to *"the receiver's inverting input and nothing else — not to a
ground pour, not to a stitching via."* `R-PD-BREATH` is a 100 kΩ pulldown placed
**differentially across BREATH–AGND**, which sets the *differential* input to
zero and leaves the *common mode* completely undefined.

An instrumentation amplifier needs a DC path from each input to its own supply
common for input bias current. There is none. With the instrument switched off
or unplugged — which ADR 0004 states is *"the state the instrument spends most of
its life in"* — both inputs are tied to each other through 100 kΩ and to nothing
else. Bias current charges the floating node:

- INA821 input bias ≈ 0.4–0.7 nA per input, so ~1–1.4 nA into the common node
- Node capacitance with the cable removed: in-amp input capacitance plus board
  stray, ~10–20 pF
- dV/dt = 1.2 nA / 15 pF = **80 V/ms**

The common-mode node hits the in-amp's input range limit in **well under a
millisecond** and the amplifier saturates. The breath output parks at a rail
instead of at zero.

Even with the cable attached but the instrument unpowered, the cable's ~200 pF
only slows it to 6 V/ms — a few milliseconds.

The consequence is the exact inverse of what ADR 0005 claims the pulldown buys:

> *"it means powering down the instrument silences the patch instead of leaving a
> stuck level"*

What actually happens is that switching the instrument off drives the breath CV
— the channel that normally opens a VCA — to full scale. A drone, at the moment
you turn the thing off, every time.

**The circuit.** Two resistors: **1 MΩ 1 % 0805 from each in-amp input pin to the
module's analog ground**, placed at the in-amp, downstream of the 10 kΩ
protection resistors.

Why this does not break the sense-return scheme R35 exists to protect:

| | Value |
|---|---|
| Worst-case `PWR_GND` offset (ADR 0003, 350 mA) | 59 mV |
| Current now diverted through the 1 MΩ into `AGND` | 59 nA |
| As a fraction of the 350 mA power return | **0.17 ppm** |
| Error it develops across `AGND`'s 0.17 Ω | 10 nV |

R35's rule is about a *parallel return*, i.e. a path that carries a meaningful
share of power current. 59 nA is not that. The rule should be restated as "no
low-impedance connection to the module ground pour; a ≥1 MΩ bias return is
required and is not a violation," because as written it forbids the thing that
makes the receiver work.

Gain cost: 1 MΩ against the 10 kΩ series resistor plus ~1 kΩ of source is a
1.1 % loss, symmetric on both legs so CMRR is untouched (the in-amp's buffered
inputs make source impedance irrelevant anyway — ADR 0003 argues this at
length). The panel gain knob absorbs 1.1 % without noticing.

**Cost:** 2 × 0805 1 MΩ, ~$0.02, two pads, zero assembly difficulty.

**ADD.** The cheapest fix in this document and it removes a failure that would
otherwise be blamed on the in-amp, the cable, or the player for a year.

---

## 2. Nothing protects the instrument against reverse polarity on the umbilical

**Severity: High.** This is the project's one unrecoverable electrical failure.

**Where it goes:** instrument, at the umbilical +12 V entry — in the footprint
`F-POLY` currently occupies.

**What fails without it.** ADR 0004 is emphatic about reverse protection at the
rack header: *"Reversed ribbon cable is the classic Eurorack failure and the
keying alone is not worth trusting."* Two Schottkys are fitted accordingly. The
other end of the same power path — a **2 m generic Ethernet patch lead, declared
a consumable, replaced at the first intermittency, possibly hand-made up with
etherCON carriers** — is trusted completely.

Two plausible cables reverse the power pair:

- A **rollover / console cable** (pin *n* ↔ pin 9−*n*) swaps pins 3 and 6.
  ADR 0004's map puts +12 V on 3 and `PWR_GND` on 6. The instrument's supply
  arrives **backwards**.
- A hand-punched replacement lead with the green pair inverted at one end. Same
  result.

Neither the PPTC nor the module's load switch blocks reverse current. What is on
the instrument's +12 V node:

| Part | Reverse survivability |
|---|---|
| R-78E5.0-1.0 | Recom specifies no reverse-polarity protection; the input structure conducts and the module is destroyed |
| WS2815, 50 LEDs | Reverse across the strip destroys the driver ICs |
| REF5050 | V_IN abs max −0.3 V; destroyed |
| OPA2197 ×1 (reference buffer + breath buffer) | Supply abs max −0.5 V; destroyed |
| 74AHCT125 | V_CC abs max −0.5 V; destroyed |

Fault energy: the module's current limiter sources its full limit — 500 mA at
12 V, **6 W** — into forward-biased parasitic diodes. Junction destruction is a
matter of milliseconds, and every one of those parts is inside a body that is
bonded shut.

Note the asymmetry the design has arrived at by accident: a $0.20 diode guards a
keyed, shrouded, once-per-lifetime rack connection, and nothing guards a
connection made with whatever lead is in the drawer.

**The circuit.** A **shunt Schottky at the instrument's umbilical entry: SS34
(SMA, 3 A, 40 V) or 1N5822 (DO-41), cathode to the +12 V node, anode to
`PWR_GND`.**

Under correct polarity it is reverse-biased: ~20 µA of leakage, **zero voltage
drop**, which matters because ADR 0005's whole 12 V-up-the-cable argument is
built on an 84 mV budget and the strips run on the unregulated rail.

Under reverse polarity it forward-conducts, holding the instrument's rail within
~0.45 V of ground while the module's limiter folds back:

- Diode dissipation during the fault: 0.5 A × 0.45 V = **0.22 W**, indefinite for
  an SS34
- The limiter drops the remaining 11.5 V at 0.5 A = 5.8 W and enters thermal
  shutdown in milliseconds
- Nothing downstream ever sees more than −0.45 V

A series diode is the alternative and is worse here: 0.42 V at 0.4 A costs
0.17 W of heat *inside the sealed body* and takes 0.42 V off the WS2815 feed for
no benefit the shunt does not give.

**Precondition:** the shunt works because the upstream limiter is real. See
finding 6.

**Cost:** one SS34, ~$0.15, in a footprint that already exists. The PPTC it
replaces is doing almost nothing anyway — it is a 500 mA hold part sitting behind
a 500 mA limiter, and its 0.6–1.4 Ω initial resistance costs 0.24–0.56 V on the
one rail (the strips') that cannot regulate the drop away.

**ADD.** Highest value-per-cent in the document.

---

## 3. The breath conductor has no clamp for the case where the instrument's own +12 V is absent

**Severity: High.**

**Where it goes:** instrument, between the OPA2197 breath buffer's output and the
etherCON `BREATH` contact.

**What fails without it.** ADR 0003 retires the breath-line protection
requirement with a clean argument:

> *"With the buffer on +12 V there is no conflict, because there is no fault
> current. A +12 V conductor against a +12 V rail is at the rail, not above it."*

That is true **only while the instrument's own +12 V rail is present.** There is
a common cable fault in which +12 V lands on `BREATH` *and the instrument's rail
is simultaneously absent*, and it is the same class of cable as finding 2.

T568B pairs are (1,2), (3,6), (4,5), (7,8). ADR 0004 maps (1,2) to
`BREATH`/`AGND` and (3,6) to +12 V/`PWR_GND`. **A 10/100 crossover cable is
defined as swapping exactly those two pairs** — T568A at one end moves the green
pair to (1,2) and the orange pair to (3,6). So a crossover lead does precisely
this:

- The module's +12 V feed arrives on the instrument's **breath buffer output pin**
- The instrument's +12 V pin arrives on the module's high-impedance in-amp input,
  so the instrument gets **no power at all**

Result: 12 V is applied to an unpowered OPA2197 output. Its output ESD diode to
V+ conducts, and the whole instrument attempts to power itself through that one
diode:

| | Value |
|---|---|
| Series resistance in the path (ADR 0003's unsized "series resistor for protection", if 100 Ω) | 100 Ω |
| Current into the output clamp | (12 − 0.7)/100 = **113 mA** |
| OPA2197 output-clamp continuous rating | ~10–20 mA |
| Rail the diode establishes | ~11.3 V — enough to start the buck |

The buck starts, both dev boards boot, the strips light, and every milliamp of it
flows through one op-amp's ESD diode. It fails in seconds, and it fails inside
the bonded body.

Crossover leads are exactly the ones lying unlabelled in drawers, because
auto-MDIX made them obsolete fifteen years ago and nobody threw them out.

**The circuit.** Two parts at the connector:

- **1 kΩ 1 % 0805 in series** with the buffer output (ADR 0003 specifies "a
  series resistor for protection" and never gives it a value or a BOM line — see
  finding 21)
- **BAV99 (SOT-23)** from the connector-side node to the instrument's local
  +12 V and `PWR_GND`

Fault behaviour becomes: 12 V through 1 kΩ into the clamp = **11.3 mA**, inside
the BAV99's 200 mA continuous rating, and 11 mA cannot start a buck that needs
~300 mA at >6 V. The instrument stays dark, nothing is damaged, and swapping the
cable fixes it.

Signal cost: 1 kΩ against the module's 10 kΩ series and 1 MΩ bias return (finding
1) is a fixed 1.1 % gain loss, absorbed by the panel gain knob. CMRR is
unaffected — the in-amp's buffered inputs are why ADR 0003 allowed 10 kΩ
unmatched in the first place.

BAV99 not BAT54S, for the same reason ADR 0006 already gives at the CV jacks:
Schottky leakage through a series resistor is a temperature-dependent offset.

**A pin-map reorder was considered and is declined.** Moving the digital pairs
onto (1,2)/(3,6) would make a 10/100 crossover harmless, but a **gigabit**
crossover swaps (4,5)↔(7,8) as well, so whichever group holds power and analog is
exposed. No arrangement of four pairs is safe against both, so the reorder buys
partial protection in exchange for disturbing a crosstalk map that was carefully
reasoned and is about to be measured at E11. The clamp is the durable answer;
take the clamp and leave the map alone.

**Cost:** 1 × 1 kΩ + 1 × BAV99, ~$0.12. Both must be on the carrier before E13.

**ADD.**

---

## 4. The 18 key-switch inputs have no defined level and no input filtering

**Severity: High.** The chain does not work at all without the first half of
this, and the second half is the cheapest defence of the whole key-integrity
effort.

**Where it goes:** the four satellite shift-register boards, at the 74LVC165 `D`
inputs.

**What fails without it.** A 74LVC165's parallel inputs are plain CMOS with no
internal pull-up or pull-down. The BOM line-items 100 nF per register
(`C-DECOUPLE-165`) and 33–68 Ω termination (`R-TERM-CHAIN`) but has **no pull
resistors for the 32 inputs**, and no ADR mentions them. ADR 0001 lists five
fixes for chain integrity and this is not among them.

Two consequences:

**Static.** A floating LVC input sits near V_DD/2 where both output FETs of the
input stage conduct. 74LVC crowbar current at mid-rail is on the order of 1 mA
per input; 32 inputs is **~32 mA** of pointless draw on the 3.3 V rail, and the
inputs read arbitrarily.

**Dynamic, and this is the one that matters.** ADR 0009 and ADR 0014 put the key
loom and the WS2815 data line in the *same two side channels*, resolved as
acceptable because "digital beside pulsed LED current is a far weaker objection
than analog beside it." That is true for a terminated, driven line and false for
a floating one. Mutual capacitance between two wires sharing a 20 mm channel over
a 400 mm parallel run is on the order of 4 pF. Against a floating input's ~5 pF:

```
V_coupled = 5 V × 4 pF / (4 pF + 5 pF) = 2.2 V
```

That is a full logic swing onto a floating input, from every WS2815 data edge.
And ADR 0001 has already established what one wrong bit costs: asymmetric
debounce fires on the first closed sample, so **one corrupted read is one
spurious note-on at full velocity**.

A pull-up alone does not fix the dynamic case. During a ~5 ns WS2812-class edge
the coupled current is C·dV/dt = 4 pF × 1 GV/s = 4 mA, which a 10 kΩ resistor
cannot hold down. **The capacitor is what does the work:**

```
Q_coupled = 4 pF × 5 V = 20 pC
into 1 nF: ΔV = 20 pC / 1 nF = 20 mV
```

Two volts becomes twenty millivolts, for one part per key.

**The circuit**, at each register board:

- **10 kΩ pull-up per input**, switch to `PWR_GND`. Four 8-way 10 kΩ bussed
  resistor networks (e.g. CTS 767 series, SIP-9 through-hole) — one per cluster
  board, one part per board, consistent with the package policy.
- **1 nF C0G 0805 from each used input to the board's local ground**, 18 parts.
  RC on release is 10 kΩ × 1 nF = 10 µs, four orders below key timing, so it
  costs nothing.
- The 14 unused bits get tied hard to a rail, with the 4–6 marker bits at mixed
  polarity as ADR 0001 requires — that is wiring, not parts.

**Cost:** 4 resistor networks + 18 × 0805, ~$2, maybe 40 minutes of hand assembly
spread over four small boards. Cannot be retrofitted once bonded.

**ADD both parts.** The pull-ups are not optional — the design does not function
without them and their absence from the BOM should be treated as an omission
rather than a decision. The capacitors are what make the marker pattern and the
error counter measure looms rather than measure LED animations.

*(Series resistors in the loom line were considered and declined: 54 passives
instead of 22 for a marginal further improvement, and the capacitor already
swamps the coupling.)*

---

## 5. Nothing blocks reverse current between the instrument's 5 V rail and USB VBUS

**Severity: High.** The review already named this the highest bench-damage risk
in the project and no circuit was ever assigned to it.

**Where it goes:** instrument carrier, in series with the R-78E5.0's output.

**What fails without it.** ADR 0005 decides the behaviour:

> *"**OR the umbilical power with USB power** — it costs a diode."*

**That diode is not in the BOM and not in the power tree.** The tree shows the
buck feeding both dev boards' `5V` pins directly. The review's own bench-test
list asks the question that makes this sharp:

> *"Waveshare ESP32-S3-Matrix: is the header `5V` pin raw USB VBUS? If so,
> driving it from the buck while USB is connected for flashing parallels two
> supplies. Highest bench-damage risk in the project."*

On most ESP32-S3 dev boards it is. Then, with USB plugged in for flashing or for
E5's MIDI work — which is the *entire first playable milestone* — two independent
5 V sources are hard-paralleled:

| Source | Tolerance |
|---|---|
| R-78E5.0-1.0 | ±2 % → 4.90–5.10 V |
| USB host VBUS | 4.75–5.25 V |

Worst-case differential 0.35 V across ~0.2 Ω of board and cable = **1.75 A of
circulating current**. Two outcomes, both bad:

- Buck higher: it back-feeds the host port, which trips its 500/900 mA limit
  mid-flash — on an unprotected hub, worse.
- Host higher: the R-78E5.0's output is driven above its setpoint. Recom does not
  specify reverse-current protection for the R-78E series and states the output
  must not be driven above V_out.

And when the buck dies, it dies inside a bonded body.

**The circuit.** An **LM66100 ideal diode (SOT-23-6, 1.5 A, 79 mΩ, integrated
reverse blocking)** in series with the R-78E5.0's output.

- Forward drop at 400 mA: 400 mA × 79 mΩ = **32 mV**. Against the 84 mV cable
  drop the whole 12 V-up-the-umbilical argument is built on, that is nothing.
- Reverse blocking is inherent, so VBUS can sit above the buck's output with no
  current flowing back.
- SOT-23-6, 0.95 mm pitch — coarser than the TSSOP-16 DAC already accepted under
  ADR 0013's package policy, same package as the load switch.

A plain SS14 Schottky is the cheap alternative and costs 0.35 V at 400 mA,
dropping the 5 V rail to 4.65 V. The dev board LDOs do not care, but the
74AHCT125's output level into the WS2815 does, and that threshold is an open
question in ADR 0014. Do not spend 350 mV there.

**Cost:** one LM66100, ~$0.60, one footprint. Must be on the carrier at E13.

**ADD.** This is a decision ADR 0005 already took; it simply never became a part.

---

## 6. The specified current limiter is a 5 V part, so the 12 V current limit that four other decisions rest on does not exist

**Severity: High, as a precondition rather than as new circuitry.**

**Where it goes:** module, `U-LOADSW`.

**What fails without it.** `U-LOADSW` is a **TPS2553DBV**. The TPS2552/TPS2553
family is a USB power-distribution switch with an input range of **2.5 V to
6.5 V**. It is specified into the module's **+12 V** umbilical feed.

Four separate decisions lean on that part working:

- ADR 0005: inrush limiting into the instrument's bulk capacitance
- ADR 0005: short-circuit foldback so an umbilical fault does not pull the rack
  rail
- ADR 0014: *"the module's current-limited load switch replaces a slow,
  self-heating, thermally-hysteretic protection device with a fast fixed limit"*
  — the hardware bound underneath the firmware LED clamp
- Findings 2 and 8 in this document

**The circuit.** Substitute a 12 V-capable part:

| Candidate | Range | Notes |
|---|---|---|
| **TPS2592BA** | 4.5–18 V | Adjustable limit 0.4–5 A, programmable soft-start, thermal shutdown. SOT-23-8, 0.65 mm — acceptable under ADR 0013's policy. Closest drop-in. |
| **TPS26600** | 4.5–60 V | Adds **overvoltage cutoff and UVLO**, which closes finding 16 for the instrument at no extra parts. HTSSOP-16 with a thermal pad — against the package policy. |
| LM5060 + external P-FET | 5.5–65 V | Discrete, most work, most control. |

Recommend **TPS2592BA** unless the overvoltage cutoff in finding 16 is wanted
badly enough to accept a thermal-pad package.

**Cost:** a part substitution, ~$1.50, zero added complexity.

**ADD.** Listed here because it is a precondition for other findings, not
because absence-hunting found it — but the *absence* is real: there is currently
no working current limit on the umbilical.

---

## 7. The one supervisory circuit in the design has no power-on reset and no undervoltage hold

**Severity: Medium-High.**

**Where it goes:** module, at `U-WATCHDOG`'s reset input.

**What fails without it.** `U-WATCHDOG` is a 74HC123 retriggerable monostable
that asserts the DAC's `CLR` when SPI traffic stops. It is the only piece of
hardware in the project whose job is to supervise something else — and nothing
supervises *it*.

Two gaps:

**No defined power-on state.** A 74HC123's `Q` is indeterminate at power-up until
it is triggered or cleared. Supply-ramp noise on the `A`/`B` trigger inputs can
start a timing cycle, so `CLR` may be de-asserted at the exact moment the design
wants it asserted — before firmware exists and before the first valid frame.
ADR 0006's carefully constructed power-on table (pitch subsonic, mods at exactly
0 V) depends on the DAC being cleared, and nothing guarantees the clearing
mechanism starts in the right state.

**No undervoltage hold.** If the module's 5.25 V DAC rail sags — another module's
inrush on the shared bus, a rack brownout, a bus-board fault — the DAC8568 will
continue latching whatever words arrive while its supply is out of spec. There is
no supervisor holding `CLR` through the excursion. A corrupted 32-bit word
written to the pitch channel puts the pitch CV anywhere in −2…+7 V, into a live
rack, and it stays there until the next write.

**The circuit.** One three-pin supervisor, and it does both jobs:

**MCP131-450 (SOT-23-3, open-drain, 4.5 V threshold, ~$0.35)**, sensing the
LM317's 5.25 V output, with its output driving the **74HC123's own `CLR` pin**
(plus a 100 kΩ pull-up).

- Below 4.5 V the supervisor pulls the monostable's `CLR` low, forcing `Q` low,
  which asserts the DAC's `CLR` — the safe state — for as long as the rail is bad
- At power-on the supervisor holds that state until the rail is valid plus its
  own delay, giving the whole supervisory chain a guaranteed power-on reset
- Only one net is added; the monostable's existing output path to the DAC is
  untouched

Threshold check: nominal DAC rail 5.25 V, worst case per ADR 0004's own
arithmetic 5.04–5.46 V. A 4.5 V threshold sits 540 mV below the worst-case low
end — no nuisance tripping — and 250 mV above the 4.25 V at which the DAC's used
output window (0.25–4.75 V) stops being reachable.

**A known blind spot, stated so it is a decision.** The monostable retriggers on
*edge activity*, not on *frame validity*. A real-time board that hangs with a DMA
loop still shifting out the last frame keeps the watchdog fed and the rack
droning. The cheap mitigation is firmware, not hardware: **retrigger the
monostable from the `CS` rising edge only, and have the output loop's sanity
check stop asserting `CS` when it fails.** Free. Everything else (a frame parser
at the module) is a microcontroller in a module ADR 0004 insists is dumb — and
correctly declines.

**Cost:** 1 supervisor + 1 resistor, ~$0.40, 2 pads.

**ADD.**

---

## 8. Thermal protection is entirely open-loop against an estimated 3 K/W, and nothing in the sealed body measures temperature

**Severity: Medium-High. The fix costs nothing.**

**Where it goes:** firmware on the real-time board, plus one number on the
module.

**What fails without it.** The thermal story is the one ADR 0014 calls binding:

> *"A pathological state is not a brownout any more. It is an instrument too hot
> to hold, an acrylic bond at its service limit, and a gauge sensor whose zero is
> chasing the room."*

The defence is a ~3 W firmware budget derived from an **estimated** 3 K/W that
ADR 0014 itself flags as *"a bounding estimate, not a measurement."* M8 measures
it once, with a thermocouple, and then the body is bonded and nobody ever
measures the interior again. If the real figure is 5 K/W, the same firmware
budget gives 15 K from lighting on top of the baseline's 25 K — a 60 °C interior
in a 20 °C room — and the instrument's only symptom is a breath zero that walks
and hands that get warm.

There is also nothing tying the thermal bound to the electrical one. The current
limit is the *de facto* thermal fuse for the whole instrument and nobody has said
so:

| Limit setting | Instrument ceiling | Interior rise at 3 K/W | at 5 K/W |
|---|---|---|---|
| 500 mA | 6.0 W | 18 K | 30 K |
| 700 mA | 8.4 W | 25 K | 42 K |
| 900 mA (2× a measured 430 mA — normal fault-protection practice) | 10.8 W | 32 K | 54 K |

Sized by fault-protection convention alone, E6 will choose ~900 mA and quietly
raise the thermal ceiling by 14 K.

**The circuit: there isn't one, and that is the point — the sensor is already
installed and already on the bus.** The **QMI8658C on the ESP32-S3-Matrix has an
on-chip temperature output**, readable over the same I2C transaction as the IMU
data, and ADR 0003 and ADR 0007 have both put that board at the **bottom of the
instrument, within centimetres of the breath sensor**. It is the best-placed
thermometer the design could have asked for and it is free.

What reading it buys:

- **Close the lighting budget on measurement.** Fold the LED budget back
  proportionally above a measured interior threshold (say 45 °C), instead of
  trusting 3 K/W forever.
- **A thermal alarm on the 8×8**, which ADR 0014 already reserves for alarms that
  cannot be configured off.
- **A permanent covariate for breath-zero drift**, which the roadmap lists as one
  of the three designated silent failures. "The zero moved and the interior was
  at 52 °C" is diagnosable; "the zero moved" is not.
- **M8's thermocouple soak becomes a calibration** of a sensor that stays in the
  instrument, rather than a single number that is never checked again.

Self-heating offset: the QMI8658 dissipates ~1.5 mW, so its die sits a fraction
of a kelvin above its board; a one-time offset against M8's thermocouple is
sufficient and M8 is already doing the run.

**Second action, also free: state that the load switch's current limit serves two
purposes** — fault protection and thermal bounding — and set it for the tighter
of the two. With a measured 430 mA typical, ~700 mA gives 1.6× fault headroom and
an 8.4 W ceiling.

**Cost:** zero parts. One I2C register, one comparison in the LED budget code,
one line in ADR 0014 and one in E6's done-when.

**ADD.** Best value in the document after finding 1.

---

## 9. The TVS array is at the instrument end only; the module end of the umbilical is unprotected

**Severity: Medium.**

**Where it goes:** module, at the etherCON's eight contacts.

**What fails without it.** `U-TVS-UMB` is categorised `controller` — instrument
end. The module end has nothing. That is backwards for the dominant ESD event.

Consider a 4 kV contact discharge to the aluminium key plate — the most-touched
metal in the system, bonded to `PWR_GND` exactly so it has somewhere to go. IEC
61000-4-2 at 4 kV gives ~15 A peak with a sub-nanosecond rise. The return path
runs down 2 m of 24 AWG `PWR_GND` with roughly **1.6 µH of loop inductance**. The
current cannot rise anywhere near that fast through that inductance, so what
actually happens is that **the instrument's entire ground reference lifts by
hundreds of volts to kilovolts relative to the module's, for tens of
nanoseconds.**

An instrument-end TVS clamps each conductor to the *instrument's* ground — which
is the thing that is moving. It does nothing for this case. The module-end array
is what clamps the signals to the *module's* ground, which is the reference the
module's silicon actually uses.

What is exposed at the module end:

| Node | Protection today |
|---|---|
| `SCLK`, `CS` | Straight to a 74AHCT125 input and a 10 kΩ pull. Nothing else. |
| `MOSI` | 220 Ω, at the far end of 2 m of cable |
| `BREATH`, `AGND` | 10 kΩ series into the in-amp; abs max (V−)−0.5 to (V+)+0.5 V, so ±12.5 V |
| +12 V | The load switch's output pin |

The 10 kΩ resistors on the analog pair are genuinely good — they bound the in-amp
input current to 2.4 mA at a ±12 V differential. The digital pair is the exposure:
a 74AHCT125 is rated for ~2 kV HBM handling, not for system-level IEC discharges
arriving over two metres of cable.

**The circuit.** A **second SP3012-06UTG (or equivalent 6-line array) at the
module's etherCON**, clamping the five signal conductors (+12 V, `SCLK`, `MOSI`,
`CS`, `BREATH`) to the module's ground plane, placed physically at the connector
so the clamp path is short.

**Cost:** one SOT-23-6 array, ~$0.30, six pads on a board being laid out anyway.

**ADD.** Same part number already in the BOM, so no new sourcing.

---

## 10. Only `MOSI` has series current limiting at the driving end; `SCLK` and `CS` have none

**Severity: Medium. Cost: two cents.**

**Where it goes:** instrument carrier, at the ESP32-S3's SPI outputs.

**What fails without it.** `R-MOSI-SER` puts 220 Ω on `MOSI`, described as
*"source termination on the one line that runs the full umbilical carrying
data."* `SCLK` and `CS` run the full umbilical too, and ADR 0004 separately calls
`SCLK` *"the fastest edge in the system."*

The protection case is the bench configuration ADR 0005 explicitly supports:
**instrument running on USB, module unpowered or unplugged, umbilical still
connected.** That is the normal E5 setup. The ESP32 then drives 3.3 V logic into
the unpowered 74AHCT125's inputs, through its input clamp diode, into a dead
+5 V rail:

| | Value |
|---|---|
| Drive available (ESP32-S3 GPIO, configurable, up to) | 40 mA |
| 74AHCT125 input clamp current rating (I_IK) | ±20 mA |
| Unprotected lines | `SCLK`, `CS` |
| With 220 Ω | (3.3 − 0.7)/220 = **11.8 mA** — inside rating |

Two lines sitting at up to 2× their clamp rating for the length of every bench
session.

**The circuit.** Two more **220 Ω 1 % 0805**, on `SCLK` and `CS`, at the driving
end, alongside the existing `R-MOSI-SER`. The `SCLK` one also gives the fastest
edge in the system the source termination that ADR 0001 argues for on the key
chain and never applied here.

Signal check: 220 Ω into ~200 pF of cable gives a 44 ns time constant against a
~1.7 µs bit period at 0.6 MHz — 38 bit-periods of margin. Free.

**Cost:** 2 × 0805, ~$0.02.

**ADD.** Two parts, two failure modes closed, no downside.

---

## 11. The WS2815 data lines have no defined state when the 5 V rail is absent

**Severity: Medium.**

**Where it goes:** instrument, at each strip's `DIN`.

**What fails without it.** The strips run on raw umbilical +12 V; their data
comes from a 74AHCT125 on the buck's 5 V rail. Those rails do not come up
together, and ADR 0014's own failure analysis is about exactly this class of
event.

The window: +12 V is present, the buck's 5 V is not, so the level shifter is
unpowered and its outputs are undefined. Two occasions:

- **Every power-on.** The R-78E5.0 starts in 2–10 ms; the ESP32-S3 reaches its
  first RMT write in 200–400 ms even with ADR 0014's blank-first rule. **~0.4 s of
  exposure, every single time.**
- **Any 5 V fault or hiccup**, for as long as it lasts — indefinitely.

A floating `DIN` on a 12 V-powered strip lets its controller latch arbitrary
data. Fifty LEDs at a random mean of ~50 % duty is roughly **0.5 A on the
unregulated rail**, drawn while the MCU is dead and the firmware clamp does not
exist. This is precisely the latched-bright scenario ADR 0014 spends a page on,
occurring in the one window where blank-at-boot is structurally unable to help.

**The circuit.** **10 kΩ 0805 from each strip's `DIN` to `PWR_GND`**, placed at
the strip end of the run so it also defines the line if the buffer output ever
goes high-Z.

Loading check: 10 kΩ against the 74AHCT125's ~±8 mA drive is 0.5 mA — 6 % of
drive, invisible. Against an 800 kHz data rate with ~100 pF of wiring, the
pulldown's RC is 1 µs on the falling edge if the driver were high-Z, and the
driver is not high-Z when it matters.

**Cost:** 2 × 0805, ~$0.01, and it cannot be retrofitted once bonded.

**ADD.**

---

## 12. The DAC side of the level shifter has no idle pulls

**Severity: Medium.**

**Where it goes:** module, at the DAC8568's `SYNC`, `SCLK` and `DIN` pins.

**What fails without it.** ADR 0004 gets this exactly right on one side of the
buffer and stops one component short on the other:

> *"CS pulled to +5 V; SCLK and MOSI pulled to ground, **at the module end**."*

That is `R-SPI-PULL`, on the 74AHCT125's **inputs**. The reasoning — floating
CMOS oscillates, a stray `CS` edge latches a garbage word into the pitch DAC —
applies identically to the buffer's **outputs**, in one state that the design
itself creates.

The module's +5 V comes from the rack bus with no protection of any kind
(ADR 0004 declines it deliberately) and the DAC's AVDD comes from an LM317 off
the *protected* +12 V. So: **an open ferrite, a blown bus-board +5 V fuse, or a
rack without the rail leaves the buffer dead and the DAC fully alive.** Its
digital inputs float. `SYNC` drifting low with clock noise on `SCLK` is enough to
latch a word, and a random 32-bit command on the pitch channel puts the pitch CV
anywhere in −2…+7 V — into a live rack, indefinitely, with the monostable
happily untriggered because no frames are arriving.

It is a loud, confusing failure from a cause ("the +5 V rail is missing") whose
correct symptom is silence.

**The circuit.** Three resistors at the DAC pins, mirroring the ones already at
the buffer inputs:

- **10 kΩ from `SYNC` to AVDD (5.25 V)** — deasserted
- **10 kΩ from `SCLK` to AGND**
- **10 kΩ from `DIN` to AGND**

Loading: 5.25 V / 10 kΩ = 0.5 mA against the 74AHCT125's ±8 mA. Nothing.

**Cost:** 3 × 0805, ~$0.02.

**ADD.**

---

## 13. There is no fault or presence indication anywhere on the module panel

**Severity: Medium. This is the highest diagnostic value per cent in the design.**

**Where it goes:** module panel.

**What fails without it.** The module has a current limiter with an open-drain
`FAULT` output and nothing reads it. ADR 0004's panel layout lists *"Connector,
power switch and LED"* without saying what drives the LED; the obvious wiring is
from the bus rail, which makes it an indicator of "the rack is on."

Now consider the question this system will be asked most often over its life.
ADR 0004 declares the cable a consumable: *"treat cable failure as routine. Keep
spares. Replace the lead at the first sign of intermittency rather than
diagnosing it."* So the recurring event is **the instrument goes dark or
misbehaves, and the owner must decide whether it is the cable, the connector, the
instrument, or the module.**

Today the available evidence is: nothing. A crushed cable, a half-inserted
etherCON, a short inside the instrument and a dead instrument all present
identically — the limiter folds back silently and the panel LED stays lit because
the rack is still on.

**The circuit.** Two LEDs and two resistors:

- **Green from the limiter's *output* rail** through 2.2 kΩ to `PWR_GND`. Lit
  means "+12 V is actually reaching the umbilical," not "the rack is on." At
  12 V that is 4.5 mA — visible in a rack, and it moves the existing LED to the
  useful side of the switch at zero cost.
- **Red from +5 V through 1 kΩ to the limiter's `FAULT` pin** (active-low,
  open-drain). Lit means current limit or thermal shutdown. 4.3 mA.

Panel budget: ADR 0004 measures the layout at ~107 mm of ~110 mm usable. A second
3 mm LED beside the first costs nothing vertically — they sit side by side in the
space already allotted.

Optional and nearly free: use one bicolour LED instead of two, green from the
switched rail and red from `FAULT`, if panel space turns out tighter than the
1:1 paper check suggests.

**Cost:** 2 LEDs + 2 resistors, ~$0.30, one extra panel hole in a laser-cut
panel where holes are free.

**ADD.**

---

## 14. Neither processor has a stated watchdog discipline, nothing watches the display board, and no reset is ever reported

**Severity: Medium. Cost: zero — all firmware.**

**Where it goes:** firmware on both boards.

**What fails without it.** The module's monostable protects the *rack* from a
hung real-time board by parking the CVs. Nothing protects the *instrument* from
it, and nothing tells anyone it happened.

**Real-time board.** The ESP32-S3 has an RTC watchdog and a task watchdog, both
software-enabled, and no ADR says to enable them or what feeds them. A hang today
means: CVs park (good), the instrument is dead (bad), and the only recovery is
reaching the rack — which is available, since the module toggle is the system's
only power switch. But there is no reason to require a human for a fault a
watchdog resets in under a second.

- Enable the RTC watchdog and the task watchdog.
- **Feed them only from the 4 kHz output loop**, never from a housekeeping task.
  A watchdog fed by the thing that is still running while the thing that matters
  is stuck is worse than none.

**Display board.** No watchdog and nothing watches it. If it hangs, it displays a
frozen screen — including, potentially, a frozen "everything is fine" while an
alarm state exists. ADR 0013 already specifies a bidirectional framed link with
status flowing at 60 Hz, so the real-time board can time out the return traffic
and raise an alarm on the 8×8, which is on the board that is still working.
Symmetrically, the display board can detect the real-time link going quiet and
say so — which is the only thing in the instrument that could ever report "the
real-time board hung."

**Reset reporting.** Neither board reports why it restarted. `esp_reset_reason()`
distinguishes power-on, brownout, watchdog and panic. This matters because the
entire failure chain in ADR 0014 — sagging rail, MCU reset, WS2815s hold their
latched colour — turns on a brownout event that is currently **completely
invisible**. A brownout mid-performance is indistinguishable from nothing
happening.

- Persist a per-cause reset counter in NVS.
- Raise a non-dismissible alarm glyph on the 8×8 for a brownout or watchdog
  reset, alongside the UNCALIBRATED and stuck-key states the roadmap already
  requires.

**On brown-out detection in hardware: ACCEPT what is there.** The ESP32-S3's
internal BOD watches its own 3.3 V rail and is enabled by default. Nothing
watches the 5 V or 12 V rail, and a monitor there would buy early warning before
the 5 V regulator hiccups — not worth a part in a sealed body, because the reset
counter gives the same information after the fact and cannot itself fail.

**Cost:** zero parts, perhaps a day of firmware, most of it inside the E4b link
work that is happening anyway.

**ADD.**

---

## 15. There is no rule for where the cable shield and the connector shells bond

**Severity: Medium. Cost: zero. Must be decided before M7.**

**Where it goes:** a written rule in ADR 0004, and the M7/E12 assembly.

**What fails without it.** ADR 0004 specifies *"Shielded (STP/FTP) preferred …
the shield is free at this price"* and never says where it terminates. The BOM
repeats "shielded preferred." Nothing states what the two etherCON **shells**
bond to either.

Both ends of this are touchable metal, and the instrument end sits at the tail
where the player's hands and the strap are. A floating shell is a touchable
isolated conductor a millimetre from eight signal contacts, which is the worst
possible ESD geometry — the discharge arcs to the nearest contact instead of
being carried around the bundle. A floating shield is an antenna running the
length of the one analog channel in the design.

Like the plate bonding in ADR 0009, **the two possibilities look identical on a
netlist** and neither is recoverable after bonding.

**The rule:**

> The cable shield terminates to both etherCON shells. The module's shell bonds
> to the module panel, and thence to the rack chassis. The instrument's shell
> bonds to the internal backing plate that carries it (ADR 0009), which is part
> of the plate stack already bonded to `PWR_GND` by `MECH-GNDBOND`. **Never to
> `AGND`** — for the same reason the key plate is never bonded to `AGND`.

Both-ends bonding is correct here and the usual one-end advice does not apply:
`PWR_GND` already ties the two grounds together, so the shield creates no loop
that does not exist. It does become a parallel return for power current — a
24 AWG drain wire is ~0.17 Ω over 2 m, comparable to `PWR_GND`, so it carries
roughly half the return and **halves the shared-ground offset** in ADR 0003's
table (59 mV → ~30 mV at 350 mA). `AGND` is untouched, because `AGND` carries no
power current by construction. The shield helps the analysis rather than
complicating it.

**Cost:** zero parts, one paragraph, one assembly instruction.

**ADD.**

---

## 16. No overvoltage clamp on the module's rack rails, and none on +5 V

**Severity: Low-Medium.**

**Where it goes:** module, downstream of the ferrites on +12 V, −12 V and +5 V.

**What fails without it.** ADR 0004 declines +5 V protection explicitly:

> *"A reversed or row-offset ribbon that puts +12 V onto that pin kills the
> buffer and nothing else, which is why the +5 V entry gets no protection network
> of its own."*

Two observations, neither of which overturns the decision but both of which
narrow it:

**"And nothing else" is not obvious.** A 74AHCT125 at V_CC = 12 V (abs max 7 V)
does not always fail open — it can fail with outputs driven toward its supply.
Those outputs go to the DAC8568's digital inputs, whose absolute maximum is
−0.3 V to +6 V. The failure can take the most expensive IC in the module with it.

**The realistic mechanism is not misinsertion.** The verification pass is right
that a three-pair offset on a shrouded keyed header is improbable. The mechanism
that does happen is a **bus-board or PSU +5 V regulator failing short from
+12 V**, a documented Eurorack failure that has nothing to do with how the ribbon
is inserted, and which this module cannot decline because ADR 0004 makes +5 V a
hard requirement.

The ±12 V rails have reverse protection and no overvoltage protection. A rack PSU
failing high reaches the module's analog and, through the umbilical, a bonded
instrument whose WS2815 strips are rated to ~13.5 V.

**The circuit.**

- **SMAJ5.0A (SMA) on +5 V**, after the ferrite. ~$0.15.
- **SMAJ15A on +12 V and SMAJ15A (reversed) on −12 V**, after the reverse
  diodes. ~$0.20 the pair.
- **Upgrade `D-REVPOL` from 1N5817 to SS34 or SS54** — same price, 3–5 A instead
  of 1 A, **40 V reverse instead of 20 V** (the 1N5817's 20 V rating is itself
  marginal against a rail excursion), and 100+ A of surge, which also covers
  finding 18.

**Be honest about what the +5 V TVS does and does not do.** An SMAJ5.0A clamps at
~9.2 V at 10 A — enough to save the 74AHCT125 marginally and not enough to keep
the DAC inside its 6 V input maximum. It is insurance against a rail drifting or
failing moderately high, not against a hard 12 V short. Proper protection would
be a series OVP switch, which is the kind of complexity that costs more than the
failure it prevents on a one-off — **unless** finding 6 selects a load switch with
overvoltage cutoff (TPS26600), in which case the instrument gets real OVP for
free and only the module's own +5 V remains on insurance.

**Cost:** 3 TVS + a diode substitution, ~$0.45, 6 pads.

**ADD**, on the grounds that these are ten-cent parts on a board being laid out
now and impossible to add afterwards, while being clear that the +5 V one is
insurance rather than a guarantee.

---

## 17. USB ESD protection is asserted, not verified — and the port is on a part sealed inside the body

**Severity: Medium, conditional.**

**Where it goes:** the tail USB-C opening, and E1's checklist.

**What fails without it.** The BOM marks `U-ESD-USB` (USBLC6-2SC6)
**`not-needed`**, with the reason *"Dev boards carry these."* That is an
assumption about a $12 Waveshare board, recorded as a fact, and cheap ESP32-S3
dev boards frequently run D+/D− straight from the USB-C receptacle to the module
with no array at all.

The exposure is specific to this design:

- The USB-C port is one of only two external openings, deliberately cut through
  the tail (ADR 0009) because flashing and E5 both need it in a body that cannot
  be opened
- D+/D− land directly on GPIO19/20 of the ESP32-S3, which are **not broken out**
  on the ESP32-S3-Matrix, so **there is no node on the carrier where an array
  could be added**
- An ESD strike that kills the S3 kills the instrument, because the board is
  bonded inside it

A 4 kV contact discharge into an unprotected USB data pin delivers ~15 A peak.
The S3's on-die protection is HBM-class handling protection, not system-level.

**The action, in order:**

1. **Verify at E1** — free, and E1 is already opening these boards to confirm
   PSRAM mode and idle current. Look for a 6-lead SOT-23 beside the USB-C
   receptacle and check Waveshare's published schematic. Add it to E1's
   done-when. *(While there: the review's open question about whether the header
   `5V` pin is raw VBUS is the same inspection, and finding 5 depends on it.)*
2. **If the array is present:** ACCEPT, done, nothing to build.
3. **If it is absent:** the only place left to protect is the panel. Expose the
   USB through a **panel-mount USB-C breakout carrying a USBLC6-2SC6**, joined to
   the dev board's own connector by a short internal USB-C cable. ~$5, one
   internal cable, and a change to the tail cutout — which is a through-cut in a
   laser-cut flat part and therefore free to change any time before M6.
4. **Free procedural mitigation either way:** connect the umbilical before USB,
   so the instrument is already at rack potential when the second cable arrives.

**Related, same milestone, same character:** the review's note that the LilyGO
T-Display-S3 AMOLED's **SY6970 PMU is documented unstable on 5 V without a
battery**, in a deliberately battery-free design. That is a supervisory hazard
with no circuit assigned — an unstable PMU browns out the display board's own
3.3 V and resets it, inside the bonded body. It belongs on the same E1
verification list, and if it is real the fix (a dummy load or a cell on the BAT
pin) has to be decided before M7.

**VERIFY first. ADD only on the failing branch.** Spending $5 and a connector
against a risk that may already be handled is the wrong trade; spending nothing
and finding out after bonding is a worse one.

---

## 18. Nothing limits inrush from the rack bus into the module

**Severity: Low.**

**Where it goes:** module power entry.

**What fails without it.** ADR 0004 rules out the conventional 2.2–10 Ω series
resistor correctly, on DC-drop grounds at 290 mA — and nothing replaced it as an
inrush limiter. The module's bulk is 470 µF per branch across four branches, with
**~940 µF on +12 V** at the bus header.

Hot-plugging into a live case:

| | Value |
|---|---|
| Path resistance (ribbon + bus traces + connector) | ~0.16 Ω |
| Plus the Schottky's dynamic resistance | ~0.10 Ω |
| Peak current | 12 / 0.26 ≈ **44 A** |
| Time constant | 0.26 Ω × 940 µF = **245 µs** |
| Charge delivered | 940 µF × 11.5 V = 10.8 mC |

44 A looks alarming against a 1N5817's 25 A surge rating, but the ratings are not
comparable — the rating is for an 8.3 ms half-sine and this pulse is 34× shorter.
On I²t, which is the right comparison:

```
diode rating:  25² × 8.3 ms  = 5.2 A²s
this pulse:    44² × 245 µs / 2 ≈ 0.24 A²s
```

**Twenty times inside rating.** The diode survives. And at rack power-on the PSU
soft-starts, so the brutal case only exists on hot-plug.

What actually suffers on hot-plug is the bus-board connector's gold flash
(molten-bridge transfer, not arcing — 12 V cannot sustain an arc on gold) and the
rack PSU's transient response, which may glitch other modules.

**Verdict: ACCEPT.** The fix a product would use — a soft-start controller at the
bus header — costs a part, a FET and a node inside the precision analog box, to
protect against an event the owner controls entirely.

**Two free actions instead:**

- **Write the rule:** power the case down to install or remove this module. Put
  it in ADR 0004 beside the etherCON hot-plug note.
- **Take the SS34 substitution from finding 16 anyway.** Same price, 100+ A of
  surge, 40 V reverse — it removes this concern entirely as a side effect of a
  change worth making for other reasons.

*(Inrush into the **instrument** is genuinely handled: the load switch's ramp is
the right mechanism in the right place, subject to finding 6.)*

---

## 19. Nothing prevents the umbilical being plugged into an actual Ethernet port

**Severity: Low, but the consequence is total.**

**Where it goes:** silkscreen, panel engraving, and a cable label.

**What fails without it.** The design deliberately chose a connector and a cable
that are physically and visually indistinguishable from Ethernet, and specified
that the cable is a generic patch lead which will be replaced repeatedly over the
instrument's life. Sooner or later, someone — the owner at 1 a.m., a friend
helping pack down, a curious visitor — plugs one end of a Cat5 lead into a wall
port or a switch.

802.3af/at PoE requires a 25 kΩ signature before energising, so a compliant
switch delivers nothing. **A passive PoE injector does not** — 24 V or 48 V
appears on pairs (4,5) and (7,8) with no negotiation. Under ADR 0004's map that
is ±48 V across `MOSI`/`CS` and `SCLK`/`DIG_GND`, directly into the ESP32's SPI
pins and the 74AHCT125. A TVS array clamps transients; it conducts and burns
against a sustained supply. Everything on both boards dies.

**The circuit: there isn't one that is proportionate.** Series protection rated
for 48 V on four signal lines, or a signature-detect interlock, costs far more
complexity than the failure it prevents for a one-off.

**ACCEPT, with the free mitigation that actually works:**

- Engrave or silkscreen **"NOT ETHERNET"** beside both etherCON connectors — the
  module panel is laser-cut from DXF where text is free, and the instrument's
  tail face is being cut anyway
- Put a printed sleeve or heat-shrink flag on the umbilical itself
- Keep the umbilical a visibly distinct colour from every other patch lead in the
  building

**Consequence if accepted and it happens anyway:** both boards destroyed, the
instrument unrecoverable because the body is bonded. Knowing that is exactly why
the labelling is worth the five minutes.

---

## 20. There is no isolation between sections, and there should not be

**Severity: none. Recorded so nobody adds it.**

The brief asks about isolation, so here is the explicit answer: the module and
the instrument share one grounding domain by design, there is no mains anywhere,
and every external connection lands in the same rack. **Nothing needs isolating,
and the one place it might be proposed — the umbilical — must not be.** A digital
isolator in the SPI path would break nothing, but an isolator anywhere near the
analog pair destroys the sense-return scheme ADR 0003 spends its length building:
`AGND` works precisely *because* it is galvanically continuous to the instrument's
analog star point and carries no power current.

The one second ground reference in the system is a host computer on USB, and the
design already handles it by construction:

- A Class-II laptop supply puts the chassis at ~110 V AC through Y-capacitors,
  with ~0.25–0.5 mA available. Current flows through the USB shell into
  `PWR_GND` and out through the umbilical — harmless to silicon.
- Contact transient: ~2.2 nF of Y-capacitance at 110 V is 0.5 µC and ~13 µJ.
  Nothing.
- The resulting ground-loop current sits on `PWR_GND`, where it appears as
  **common mode** at the in-amp and is rejected — `AGND` carries none of it. This
  is the AGND scheme earning its keep against a disturbance nobody designed it
  for.

**ACCEPT, explicitly and in writing.**

---

## 21. Protection that was decided and never reached the BOM

**Severity: Medium, because a part that is in an ADR and not in the BOM does not
get bought, and half of these cannot be added after bonding.**

Each of these is specified in an accepted ADR and has no BOM line:

| Missing line | Decided in | Why it matters |
|---|---|---|
| **Series resistor on the instrument's breath buffer output** | ADR 0003: *"only a buffer — an op-amp follower, band-limited, with a series resistor for protection"* | No value, no part. Finding 3 needs it at 1 kΩ |
| **10 kΩ protection resistors at the module's in-amp inputs** | ADR 0003: *"protection resistors can be 10 kΩ and unmatched"* | These are what bound in-amp input current to 2.4 mA under a ±12 V fault. Two parts |
| **In-amp gain resistor R_G** | ADR 0003 (absorbs the ~2.13× stage) | Not protection, but the receiver does not work without it |
| **USB / umbilical OR-ing diode** | ADR 0005: *"it costs a diode"* | Finding 5 — this is the highest bench-damage risk in the project |
| **Per-board regulator for the display board** | ADR 0013: *"give each board its own regulator from the umbilical +12 V"* | The BOM has one R-78E5.0. A 0.5 A WiFi TX burst currently lands on the same 1 A rail as the matrix and the real-time board |
| **`C-BULK-DISP`** | ADR 0013 | Still marked `open`. It is the thing absorbing those bursts |
| **Band-limiting components at both ends of the breath channel** | ADR 0003: *"band-limit at both ends, around 500 Hz"* | Two R–C pairs. The 500 Hz corner is load-bearing for the entire noise argument |

And one to close rather than add: **the LM317's OUT→IN and ADJ→OUT protection
diodes are not specified and are not needed here.** TI's thresholds are an output
capacitance above ~25 µF and an output above ~25 V; this is 10 µF at 5.25 V, well
inside both. Write the sentence so the question does not get re-raised at layout.

**ADD** — this is bookkeeping, but it is the bookkeeping that decides what gets
ordered before the carrier is populated.

---

## What I looked for and found genuinely fine

Recorded so these are closed rather than silently unexamined.

- **Overcurrent on every rail.** Module 5.25 V (LM317 internal limit + thermal
  shutdown), instrument 5 V (R-78E5.0 internal), instrument 3.3 V (dev board
  LDO), sensor supply (OPA2197 short-circuit protection), umbilical +12 V (load
  switch, subject to finding 6). The module's own ±12 V analog branches are
  unfused, which is standard Eurorack practice and correct — the rack PSU is the
  protection, and a 45 mA branch does not justify its own device.
- **Thermal protection in the ICs.** LM317, R-78E5.0, TPS2592-class load switch
  and OPA2197 all carry internal thermal shutdown. Finding 8 is about the
  *enclosure*, not the silicon.
- **CV output protection.** 1 kΩ series plus BAV99 at every jack covers shorts to
  ground, output-to-output patching (11.9 mA worst case through 2 kΩ), and
  insertion transients. Back-powering through those clamps when the module's own
  rails are absent — pulling a module with patch cables still connected — is
  ~10 mA per jack into a dead rail, which is how every Eurorack module behaves
  and is harmless.
- **Cross-supply input protection where it was thought of.** `R-OPAMP-IN` (DAC on
  5.25 V into op-amps on ±12 V) and `R-ADCDIV` ≥10 kΩ (5 V before 3.3 V, 0.42 mA
  into the ADC clamp against a ±2 mA limit) are both correctly reasoned and
  correctly sized. Findings 3, 10, 11 and 12 are the same reasoning applied to the
  four places it was not.
- **Power-on output states.** The A/C-grade zero-scale reset, the DAC-channel
  offset, and the internal reference being disabled until firmware enables it
  together give the best available power-on state on every channel. A muting
  circuit would add parts for a click.
- **Power-on reset of the processors.** Internal POR plus the dev boards' own
  reset circuitry, with the module toggle as a reachable hard power-cycle. No
  external supervisor needed. *(One usage note: the instrument's ~1.5 mF of bulk
  takes ~60 ms to fall below the buck's dropout at idle load, so a fast
  off-on at the toggle can produce a brownout restart rather than a clean POR.
  Count to three — cheaper than a bleed resistor burning 144 mW inside a sealed
  body.)*
- **Broken umbilical conductors.** A broken `PWR_GND` routes the return through
  `DIG_GND` — 400 mA × 0.17 Ω = 68 mV of reference shift, survivable and not
  damaging. A broken `AGND` saturates the in-amp, which is loud rather than
  silent. R35's rule is what keeps `AGND` from becoming a power return in the
  first place, and it is doing real work.
- **ESD to the player-facing metal.** The key plate bonded to `PWR_GND` is the
  right bleed path, and the switch contacts are recessed behind plastic keycaps,
  so the plate is the realistic strike point and it has somewhere to go. Finding
  15 completes this by defining where the *connector shells* go.

---

## Recommended order

**Before the carrier and module boards are laid out** — none of these is
recoverable afterwards, and all are cheap:

1 (1 MΩ bias return) · 2 (reverse shunt) · 3 (breath clamp) · 4 (key pulls and
caps) · 5 (ideal diode) · 6 (12 V load switch) · 7 (supervisor) · 9 (module-end
TVS) · 10 (220 Ω ×2) · 11 (LED pulldowns) · 12 (DAC pulls) · 13 (panel LEDs) ·
16 (TVS trio + SS34) · 21 (BOM lines)

Total added parts: **about 40, nearly all 0805 passives.** Total added cost:
**under $10.** Total added assembly: **an hour, spread across boards that are
being built anyway.**

**At E1, before anything is committed:** finding 17's two inspections — the USB
ESD array, and whether the header `5V` pin is raw VBUS.

**Free, any time:** 8 (IMU temperature, and size the current limit as a thermal
bound) · 14 (watchdogs, link liveness, reset reasons) · 15 (shield bonding rule) ·
18 (no hot-plug rule) · 19 (NOT ETHERNET labels) · 20 (write down that isolation
is declined).

**Consciously accepted, with the consequence stated:** 18 (hot-plug wears the bus
connector; the diode survives on I²t) · 19 (a passive PoE injector destroys both
boards and the instrument is unrecoverable — which is what the label is for) ·
20 (no isolation, correctly) · the module's unfused analog branches · the
module's +5 V having insurance rather than a guarantee against a hard 12 V short.
