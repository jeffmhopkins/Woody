# Roadmap

## Principle: three tracks in parallel, converging late

Mechanical and electrical work are independent until final integration. Running
them in sequence wastes months; the slow track (outsourced cutting, PCB
turnaround) should always be in flight while the other progresses.

| Track | Covers | Gated by |
|---|---|---|
| **M — Mechanical** | Key mounting, layout, laminated stack, body | Switches arriving; key count decided |
| **E — Electronics** | Board bring-up, sensors, ADC, DAC, CV module | Nothing — can start immediately |
| **F — Firmware** | Instrument firmware, routing matrix, UI | Follows E |

Bring-up firmware — the throwaway fixtures that prove a DAC or an ADC works —
is not tracked under F. It belongs to whichever E milestone needs it. F is the
real instrument firmware, and it genuinely is the tail end of this project.

## The shortest path to a playable instrument

Deliberately skips CV entirely:

> **E1 → E2 → E4 → E5 on a bench, mounted to M2.**
>
> Dev board, breath sensor, key scan, USB MIDI, on a laser-cut test plate.

That is a real instrument you can play into a DAW. It validates the ergonomics
and the fingering system with actual playing, and it is a working fallback if
the CV track runs long. Everything else — the module, the aluminium, the wood —
comes after and none of it blocks the others.

---

## Track E — Electronics

The module track (E6 onward) can run start to finish without the instrument
existing. Drive it from any dev board with a test pattern and a multimeter.

| ID | Milestone | Done when |
|---|---|---|
| E1 | Board bring-up | Waveshare ESP32-S3-Matrix + LilyGO T-Display-S3 AMOLED (ADR 0008). Both running; **PSRAM confirmed quad, not octal**, and **idle current measured** before the carrier is laid out (ADR 0007) |
| E2 | Breath sensing | **Port orientation confirmed with a syringe first** — a reversed DP reads zero, not backwards. Then **a human plays it for 20 minutes** through a real mouthpiece, tube and trap — not a syringe. Ambient zeroing tracks, no condensation artefacts. **The restrictor is sized by ring-down, not by frequency**: tap the mouthpiece end and watch the sensor settle — one time constant, or a decaying oscillation that needs a denser plug. The 214–429 Hz pipe mode is below the filter corner and independent of trap volume, so it is damped, not placed (ADR 0003). **Also settles the tube bore** by playing a bare tube in two or three sizes. Sensor + ADC at the bottom with the real-time board |
| E3 | IMU | Tilt and roll angles read reliably at rate |
| E4 | Key scan | 74HC165 chain reads all switches; debounce asymmetric (instant press, filtered release) |
| E4b | **Inter-MCU link** | Framed UART between the two boards, status flowing, logic-analyser clean (ADR 0013) |
| E5 | **USB MIDI out** | Plays into a DAW. Fingering table exercised. First playable milestone |
| E6 | Module power | ±12V from rack via keyed header + reverse protection, local 5.21V DAC regulator and bus +5V logic rail up, input filtering, load switch limits and ramps the umbilical feed, no noise injected back into the rack |
| E7 | DAC raw | Commanded codes produce expected voltages on the meter, all six channels. **Select `R-REG-SET` here** — and **never below AVDD = 5.00 V**: the DAC8568's **C grade is specified only for 5.0–5.5 V** (SBAS430E, `datasheets/analog/DAC8568CIPW.pdf`), and this step otherwise optimises for top-code compression across a 0.66 V spread with no floor. Added 2026-09-21; the step had no lower bound before |
| E8 | Pitch channel scaled | Raw analog gain and offset trimmed to target, linear across the span. The 5%-over kludge is deleted — trimmers go both ways (ADR 0006) |
| E9 | **Pitch calibration** | **Multi-point fit** — one point per octave, which is what every surveyed design does (Yarns 11, O&C 11, PER|FORMER 11) and what ADR 0006 asks for; this row said "two-point" and contradicted it. Stored in NVS with a version and a checksum, in its own slot away from presets; 1V/oct verified against a real VCO, not just a meter, loaded the way it will be played (ADR 0006) |
| E10 | Remaining channels | Analog breath stage: in-amp receiver with **`REF` trimmed, not grounded** — grounding it makes the panel knobs interact, and leaves `TRIM-BREATH-ZERO` nothing to drive (`breath-receive-stage.md`; this row said "grounded" *and* "set the trimmer first", which are the two mutually exclusive options). **Set `TRIM-BREATH-ZERO` first**, until the in-amp output reads 0 V — then gain, then the panel offset, in that order. **Commission with a meter on the jack, not the display** — the analog and digital representations are calibrated separately on purpose (ADR 0003). **Pull the umbilical mid-note with the mouthpiece at rest.** Three things to observe, not one: breath parks quietly (no DAC in that path, so no reset reaches it); **pitch and the four mod jacks hold their last value indefinitely** — that is the accepted cost of deleting the frame watchdog, not a fault; and with the instrument absent the breath jack then sits wherever the panel OFFSET knob was left, anywhere in ±5 V (ADR 0004, ADR 0006). Four mod channels trimmed |
| E11 | Umbilical link | SPI **at 2 MHz** (not the stale 0.6 MHz — see ADR 0004; the old figure came from a 2 kHz rate and does not close at 4 kHz) and the analog breath pair over the real cable at length, **on the T568B pin mapping in ADR 0004** — the mapping is reasoned, not measured. Breath output clean while display, LEDs and WiFi are exercised (ADR 0003) |
| E12 | Module PCB + panel | 10HP panel cut, module assembled and racked. etherCON braced to the PCB — good practice at `panel-width` rather than the structural necessity it was at the original 6HP. **Ground laid out to the star rule in ADR 0004** — one origin at the power inlet, `PWR_GND` and `DIG_GND` each on their own copper, `AGND` not a return at all. Free now, a bodge wire or a respin afterwards |
| E13 | Carrier + cluster PCBs | **Passive** carrier: dev board plugs in, carrier holds ADC, reference, buffer, level shifter, regulators, connectors. **No MCU, no USB, no RF, and no shift registers** — those went back to the four cluster boards, one each, with their key networks (ADR 0001, ADR 0013) |
| E14 | **Carrier re-validation** | E1–E11 re-run on the carrier, not on dev boards. Everything before this was proven on a different physical thing |

**E9 is the milestone that decides whether this is an instrument or a thing
that is always slightly out of tune.** Verify against a VCO — and against the
VCO **loaded the way it will be played**, because E9 will otherwise pass while
being wrong (ADR 0006).

## Track M — Mechanical

Width and thickness are set at 2.25 × 1.5 in (ADR 0009). **The length is
derived** — minimized around the keys, a little at the mouth, the connector at
the tail — by the body CAD (`mechanical/drc.echo`, "overall length"). It was
18 in until 2026-09-26.


| ID | Milestone | Done when |
|---|---|---|
| M1 | Switch characterisation | **Cutout is 14.0 × 14.0 mm**, measured from a working KS-33 build ([reference](docs/reference/ks33-geometry.md)); body geometry from Gateron's STEP model, not calipers. Test coupon cut at ±0.1mm around 14.0 to find the *achieved* fit in real material; retention verified by hand; **bounce and the actuation/reset hysteresis gap scoped** on fast press, slow press, fast release, slow release and a worn switch — neither is published; **action assessed by hand** — fingertip vs thumb-tip, and whether the four thumb keys want a lighter spring than the eleven finger keys |
| M2 | Layout mule | Full key count on a laser-cut plate, hand-wired, mounted to a mock body; playable |
| M3 | Layout locked | Ergonomics settled after 2–3 iterations of M2. No aluminium cut before this |
| M4 | Stack design | Full laminated stack in CAD, every layer a 2D part, **modelled against the real KS-33 STEP solid** rather than a nominal box (ADR 0002) |
| M5 | Aluminium top plate | Cut, fitted, switches retained solidly, **bonded to `PWR_GND`**. Not before E13 — see the ordering rules below |
| M6 | Body | Oak top and bottom, frosted acrylic sides, LEDs, strap points, **matrix window + diffuser on the top face after the keys, and the USB-C slot** (ADR 0009) |
| M7 | Integration | Electronics mounted in the body, umbilical connector fitted and strain-relieved |
| M8 | **Final-assembly gate** | Assembled, lid on, but not signed off. (This row said **Pre-bond gate / assembled but not bonded** until 2026-09-21. The body is no longer bonded shut — it closes on six fasteners onto an RTV gasket, ADR 0009 — so M8 is the last gate before the instrument is treated as finished rather than the last moment it can be opened.) Full E11 breath-noise test re-run on the *final* harness, **thermal soak at the lighting clamp, watching temperature *and the breath zero* at the sensor**, two-hour play test, failure injection, self-test, **pitch scoped while the LEDs sweep** (ADR 0006 — the one test the plan was missing), and **recover both boards through the service header** so the last route in is known good, not assumed (ADR 0009). Nothing closes until this passes |

**M1 no longer gates M4.** An earlier revision made the cutout measurement the
single most important input to the mechanical design, on the assumption it could
only come from calipers. Gateron publishes the drawing and a STEP model
(ADR 0002), so **CAD can start now** — M1 narrows to confirming the *achieved*
fit in real material, and to the two timing figures nobody publishes.

**Nothing expensive gets cut before M3.** The ergonomic iteration ladder is
paper at 1:1, then laser-cut acrylic, then aluminium — cheapest first, and
every expensive mistake made in the cheap material.

### Three ordering rules a design review found violated

**M5 must not precede E13.** As originally sequenced, the aluminium plate — the
most expensive irreversible part — was cut in Phase 3, while the carrier PCB it
has to accommodate was not designed until Phase 4. Cut the plate after the
carrier layout exists.

**The body does not close until the carrier is revision-final and burned in.**
E13 and M7 sat in the same phase with a hard dependency in one direction, and
the carrier *will* spin at least once — the SPI split alone changes its
topology. A closed body around a board that needs a revision is the most
expensive mistake available in this project. It stopped being *unrecoverable*
when the body became serviceable (ADR 0009); the ordering rule stands anyway,
because "recoverable" here means a full strip-down.

**M8 exists because E11 tests a topology that does not survive to the finished
instrument.** At E11 the LED strips are not installed — they arrive at M6 — and
the body is not closed, so the loom under test is not the final loom. The
single test that validates the entire analog-breath decision was running
against a configuration that changes afterwards.
**This was the most important missing milestone in the project.**

### Why M1 measures slow presses, not just bounce

The release window was being sized from the wrong number. For an MX-style switch
the dominant release-side effect is not contact bounce — it is the **gap between
the actuation point and the reset point**. A slow, deliberate release, which is
exactly what a woodwind player does on a legato phrase, can park the plunger
inside that gap and chatter for tens of milliseconds. **Partly refuted
2026-09-21, now that the vendor drawing is banked** (`datasheets/mechanical/
GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`): Gateron *does* publish a bounce figure
— **5 ms max at 16 in/sec** — and plots both the operating and reset points on
an undimensioned Force-Travel diagram, off which the gap scales to roughly
0.3 mm. The **hysteresis gap is still not stated numerically**, and a figure
scaled off an undimensioned chart brackets the problem rather than settling it,
so both still have to be measured, on a worn switch as well as a fresh one.

**And release latency is not free on a woodwind.** On a keyboard, filtering the
release costs nothing because the note is already sounding. Here fingerings are
combinational: **lifting a finger is how you start the next note.** A 10 ms
release window delays that new note by 10 ms, landing squarely in the territory
the attack-latency work exists to protect.

So: **apply the release filter to the note decision, not to each key
independently.** A key that opens while others close is part of a transition,
not a release, and should not be filtered as though the phrase were ending.

## Track F — Firmware

| ID | Milestone | Done when |
|---|---|---|
| F1 | Key and fingering engine | Custom fingering table driven from config, not hardcoded |
| F2 | Breath response | Curve shaping, ambient zeroing **of the digital copy** (seeded at power-on, then gated on sub-threshold AND quiet), threshold and note gating |
| F3 | Channel output | Fixed-rate DAC loop, per-channel smoothing in software |
| F4 | Routing matrix | Four mod channels: source, scale, offset, curve, slew |
| F5 | **Web config app** | SoftAP, captive portal, web app served from flash. Fingering table, routing matrix, breath curves |
| F6 | Live monitoring | WebSocket telemetry to the phone: breath, IMU angles, commanded CV |
| F7 | Status display | Note, breath, active channels, mode. Status only — config lives on the phone |
| F9 | **Matrix surface** | 8×8 as a generic assignable sink: breath by default, other sources and render modes from config. Alarm states preempt and cannot be configured off (ADR 0014) |
| F8 | Persistence | Config and calibration in NVS; presets |

---

## Phase view

| Phase | Contains | Outcome |
|---|---|---|
| **0** | This repository | Decisions recorded, structure in place |
| **1** | E1–E5, M1–M2 | Playable USB MIDI instrument on a test plate |
| **2** | M3, E6–E9 | Layout locked; pitch CV calibrated and accurate |
| **3** | E10–E12, M4 | Module complete and racked; stack designed. **M5 moves to Phase 4** — the plate is cut after the carrier layout exists |
| **4** | E13, E14, M5–M7, M8 | Carrier built and re-proven; plate cut; real instrument in a real body, validated before it is called finished |
| **5** | F4–F9 | Routing matrix, web config, monitoring, presets, matrix surface |

## Out-of-order work worth pulling forward

**F6 (live monitoring) is worth building well before its phase.** A phone
showing live breath pressure, IMU angles and commanded CV over a WebSocket is a
test instrument, not just a convenience:

- **M2/M3** — see which keys actually register while trying a layout, instead of
  inferring it by ear
- **E9** — watch commanded against measured while trimming calibration, instead
  of alternating between a meter and a menu
- **E2** — see the breath response curve while playing against it

It depends only on E1 and a WiFi stack, so it can be built as soon as there is a
dev board on the bench.

## Bench measurements the review asked for

These are not milestones — they are measurements that turn assumed numbers into
known ones. Each hangs off a milestone that is happening anyway. The full
characterisation table lives in
[the latency budget](docs/reference/latency-budget.md); these are the ones that
came out of the analog design review specifically.

| Measure | At | Why |
|---|---|---|
| **Real-time board idle current** | E1 | 64 unlit `WS2812B-0807` drivers are an estimated ~50 mA and 0.25 W. **The part number is now read off the banked Waveshare schematic and the estimate is still an estimate** — Worldsemi publishes no WS2812B-0807 datasheet at all. Bracketing surrogates give 22 mA (XINGLIGHT 2022, 0.35 mA/device), <38 mA (Worldsemi WS2812B-2020, <0.6 mA) and **160 mA** (XINGLIGHT 2024, 2.5 mA/device), so ~50 mA is plausible but could be 3× low. E1 measures it, spent whether or not anything is displayed. The shared lighting budget is sized from this number (ADR 0014) |
| **1:1 paper fit check, both faces** | M4 | The etherCON flange against a 50.50 mm 10HP panel *and* against the 57 × 38 mm instrument tail beside the USB-C slot. Was called comfortable at the superseded 8HP; the tail is now the tight one (ADR 0004, ADR 0009) |
| **Matrix diffusion prototype** | M6 | Can an 8×8 at 2.6 mm pitch stay pixel-distinct through a window, or only as a blurred bar? Decides whether the 2-D IMU assignment is usable (ADR 0014) |
| **Interior temperature rise under load** | M8 | The lighting budget is set from an estimated 3 K/W. Soak with strips and matrix at the clamp, and measure at the breath sensor (ADR 0014) |
| **Cold-start warm-up sweep** | E2 | Run the sensor from cold through 20 minutes of playing. Output that *falls* under warming is a blocked reference chamber; output that *drifts* is ordinary thermal offset (ADR 0003) |
| **Breath zero vs cavity temperature** | M8 | The DP's reference port is open to the cavity, so the cavity must leak. Watch the zero during the same soak — a walking zero means it is sealing more than assumed. **The body opens, so a vent can be added at M8 or afterwards** — and a body that closes on a gasket rather than an adhesive is likelier to leak enough on its own (ADR 0003, ADR 0009) |
| **PSRAM mode on the ESP32-S3-Matrix** | E1 | **No longer a gate** — settled on paper two ways: the vendor board file exposes GPIO33–40 as headers, which octal PSRAM makes impossible, and `R2` is Espressif's suffix for 2 MB *quad*. 17 broken out, three spare. Print the pin list anyway; it costs thirty seconds and catches a silent board revision (ADR 0007) |
| **DAC saturation vs AVDD** | E7 | Full scale is 5.000 V from the internal reference at gain 2, *independent* of AVDD — what AVDD decides is whether the output buffer can reach it. Raise the top codes and find where they start compressing; that measurement is also what selects the LM317's divider (ADR 0004, ADR 0005) |
| **Pitch DC load sweep: open / 100k / 50k / 33k** | E9 | Quantifies the 1 kΩ divider error against the real patch, and tells you how much a re-mult actually shifts tuning (ADR 0006) |
| **Pitch stability into worst-case cable capacitance** | E9 | **A GATE, not a reassurance** — and this row used to say the opposite. The pitch stage now *is* the in-loop version: DC feedback is tapped at the jack, so the 1 kΩ and the patch cable are inside the loop and `C-FB-PITCH` is what compensates it. Sweep the load: open, 100 kΩ, a passive mult, a short (ADR 0006) |
| **Inrush with a current probe, on switch-on *and* hot-plug** | E6 | Sizes the load switch's current limit from measurement rather than from a guess (ADR 0005) |
| **Pitch jack while sweeping the LEDs, and while the rack is busy** | E6 / E9 | The test the plan was missing: the one measurement for this class scoped *breath*, the channel that is immune. Four routes put LED current onto pitch and two are fixed in hardware; this measures the two ground terms that are left — the module's own pour (5.7–7.2 cents) and the rack's shared bus return (~4.8) — rather than trusting the figures (ADR 0004, ADR 0006) |
| **Gate-press-while-moving IMU test** | E3 | The failure mode that killed the bias-snapshot proposal. Press the gate mid-gesture and check the stillness-gated estimator does not adopt motion as bias (ADR 0007) |
| **Key-chain error counter over an hour, LEDs and WiFi active** | E4 | The marker pattern's whole purpose. A non-zero count says the looms need work while the body is still openable (ADR 0001). **This covers the loom again** now that the chain runs through it — while the registers were briefly on the carrier the marker bits were board-local and could not see a switch conductor at all, and a version of this row claimed they could |
| **Does the chained key loom fit the side channel?** | M4 | `chain-conductors` per hop rather than the 32–44 the tail-mounted alternative needed — much easier, but still check it against the real cavity section alongside the LED strips and the breath tube, before the plate DXF is cut (ADR 0001, ADR 0009) |
| **Restrictor sizing by ring-down** | E2 | The tube is a distributed pipe at 214–429 Hz, below the filter corner and **independent of trap volume** — no orifice size places it, so size the plug for *damping* and measure the time constant it adds, which is a latency term the budget cannot fill in until then (ADR 0003) |

**The key-chain and restrictor measurements are the time-critical ones** — both
inform wiring and plumbing that get closed up at M6 and are awkward to reach
afterwards.

## Failures that are silent, and what makes them loud

A design review ranked the project's failure modes by *how quietly they fail*.
The quiet ones are the expensive ones, because they get blamed on the player or
on firmware for years. All three fixes are firmware and all three are free.

| Failure | Why it is silent | Made loud by |
|---|---|---|
| **Blank or corrupt NVS → default calibration** | The instrument plays. It sounds like an instrument. It is just badly out of tune, with no indication anything is wrong | CRC the calibration blob; a hard **UNCALIBRATED** state on the display the player cannot miss |
| **Stuck-closed switch** | Does not kill a note. Silently returns a *different* note for every fingering that key participates in — presents as "some fingerings feel wrong", which is unfalsifiable by ear inside a body that cannot be opened | Flag any key closed at boot, or held beyond N seconds, as suspect and report it |
| **Stale breath zero** | Thermal drift over a session moves the floor, and the player compensates with their diaphragm without noticing | Continuous auto-zero (ADR 0006), plus showing the current zero on the display |

A fourth is hardware and already handled: a corrupted key-chain read becoming a
spurious note, made countable by the marker pattern (ADR 0001).

## Netlists — done, and what they found

**Every schematic page that carries a drawing has a machine-readable netlist
beside it. The netlist is authoritative; the ASCII drawing is a
representation of it.** `tools/check-netlist.py --strict` runs from the
commit gate, so a new drawing page with no netlist is now a failure rather
than an entry on a list.

**Counts are the tool's, not this file's.** Run it: it prints the circuits,
components, nets and master nets, every row whose placed instances differ
from what the BOM buys, and the pages it is deliberately not asking for a
netlist from. There is no number in this section for the same reason there is
no number in the review-wave sentence.

**Why this is the fix and not a tidy-up.** Every page-vs-BOM conflict found
in the 2026-09-22 review exists *because a drawing is authoritative by
accident and unreadable by any tool*:

- `R-FB` drawn **40 kΩ** against 40.2 kΩ in the parts list and the BOM — and
  40 kΩ is not an E96 value, so a layout taken off the drawing specifies a
  part that cannot be bought.
- Entry bulk drawn **4 × 47 µF** against a BOM row that opens "NOT 47uF on
  every rail". A stuffing list off that drawing under-fits +12 V by half.
- `R-LED-SER` drawn **220R** where the BOM says 330R and the prose says a
  range.
- An **unlabelled `N-FET`** where the BOM has `Q-LOADSW`.

None of these was reachable by `check-staleness.py`, `merge-bom.py` or any
other tool, because **a drawing is a picture**. Every one of them would have
been a one-line diff against a netlist.

**What it buys, concretely:** `merge-bom.py --check` already proves the BOM
master matches its fragments. A netlist makes the same proof possible for the
drawings — every refdes in a netlist must exist in `bom.csv` with a matching
value, every net must have at least two endpoints, and the drawing can be
checked against the netlist or regenerated from it. The whole class stops
being something a review has to find by reading.

**Hand-authored YAML is authoritative; KiCad is generated from it later.**
Circuits were converted one at a time and **nearly every one forced a corpus
change.** The recurring shapes, each of which had survived every review:

- **Aggregate BOM rows** — one `part` field holding two values, so no
  instance could state a value that matched it. `R-MODGAIN` and `R-ADCDIV`
  split; five others had already gone the same way.
- **Parts drawn and never listed** — `LK-CLR` on four pages, and `R1`, `R2`
  and the 2 × 10 k divider in a cost table, none with a `bom.csv` row.
- **Master nets that were bundles** — `SPI_DAC` standing for three
  conductors, `DAC_CH2_5` for four channels, `MOD_JACKS` for four jacks. No
  layout could have used any of them.
- **Nets that were not nets** — the carrier's "+12 V strip feed" and "+12 V
  analog" are the same node as the umbilical's, and `PITCH_JACK` and its five
  siblings cross no boundary at all: the far end is a `J-CV`, which is a part.
- **Two halves of one boundary disagreeing** — `ON` declared as crossing into
  `module/panel` where `panel.md` claims only the hole; `PWR_GND` claiming two
  analog circuits that return to `AGND_INST`; four master receivers seeded
  from Interfaces rows whose own text says the net "reaches no part of this
  circuit".
- **A rail that does not exist.** `R-SPI-PULL`'s row says the cable-side `CS`
  pull goes to 3V3, and there is no 3V3 on the module board.

**And the checker kept failing open.** Seven fixes to the label parser alone,
each found by a correct label being reported wrong or an injected defect not
being reported at all: a refdes may be one character, may carry `_`, may
carry `.`; a label written value-first or split across two lines is reported
rather than skipped; `foreign:` was an unconditional skip; `10R`, `10 Ω` and
`10 kΩ` are one value; `×2` and `#1` are counts, not magnitudes.

**`hardware/nets.yaml` is the MASTER, and it is the piece a per-circuit file
cannot provide.** A circuit's `netlist.yaml` can only declare *its own side*
of a boundary-crossing net. Across 23 circuits that is up to 23
half-declarations with nobody owning the net, so two circuits can spell it
differently, two can both claim to drive it, and one can name a peer that
never names it back — none of which is visible from inside either circuit.
The master owns the net; each circuit's `ports:` must resolve to it; and the
check runs **both ways**, which is what made the `circuit:` dependency edges
trustworthy when it was applied to them.

**Settled.** Format: hand-authored YAML, `components:` and `nets:`, matching
the `circuit.yaml` already in each directory — the tie-breaker was that these
are authored by hand and KiCad is generated from them, not the other way
round. Where it sits: one `netlist.yaml` per circuit directory, beside the
page, its `bom.csv` fragment and its `circuit.yaml`.

**Still open, and each is a decision rather than a transcription job:**

1. **Whether the drawing is then generated.** If it is, the alignment drift
   recorded against five pages stops being possible. If it is not, the
   drawing-vs-netlist check `check-netlist.py` already runs is most of the
   value for a fraction of the work, and it has been catching things since
   the first circuit.
2. **The four cluster boards are one schematic with four strappings.** Which
   of a 74HC165's `A`…`H` carries a switch, a marker or a free bit differs on
   every board, so `KEY_BITS` and `MARKER_BITS` are marked `per_board:` and
   those inputs are declared unasserted. Resolving it means four board
   variants. The checker names the two nets on every run.
3. **The key chain's hop map is prose.** Eight connectors, four ribbons,
   `SER`/`QH` point-to-point and changing meaning at every hop. Only the
   carrier's connector is placed; the tool prints `J-CHAIN 1/8`.
4. **Decoupling is not netted.** Supply pins arrive through `rails:`, so the
   per-pin decouplers have no pin to hang on and `C-DECOUPLE` and
   `C-DECOUPLE-CARRIER` will read short until that changes.
5. **The seventh `R-OPAMP-IN` has no home** — `pitch-stage.md`'s "Still
   open".

## Open items blocking work

| Blocks | Question | Tracked in |
|---|---|---|
| M4, M5 | **Plate stiffening** — the thickness is **settled at 1.20 mm** by Gateron's own drawing (2026-09-21), which puts both 1.5 mm and 2 mm out of spec and makes stiffening a **requirement, not an option**. What remains is how: lamination, a structural backer, or a ribbed sub-frame | [ADR 0002](docs/decisions/0002-key-switches-and-mounting.md) |
| M4, E2, E11 | **Re-derive what was sized from the 457 mm body**, now the length is derived and much shorter: the breath tube (~400 mm — ADR 0003's pipe-mode frequencies and delay move with its length, so this is analysis, not an edit), the display and key-chain looms (360 / 265 mm — ADR 0013, `carrier.md`, `display-and-service-uart.md`, `key-chain-loom.md`; shorter only helps), and the LED strips (2 × 420 mm — ADR 0014, `led-strip-drive.md`; fewer LEDs, lower current). Current length in `mechanical/drc.echo` | [ADR 0009](docs/decisions/0009-enclosure-construction.md) |
| M4 | **The first body model's design-rule failures** — etherCON panel stack and body height at the tail, the underside display against the left-thumb recesses, thumb recess spacing, carrier vs LED strips. Current values in `mechanical/drc.echo`. (The CAD tool itself was decided 2026-09-26: OpenSCAD, `mechanical/`) | [mechanical/DESIGN.md](mechanical/DESIGN.md) |
| M1 | **MT165 cap height above the switch seat** — both oak panels' thicknesses now derive from it (keys flush with both faces at full travel, 2026-09-26), so it is the number the lamination is waiting on | [ADR 0009](docs/decisions/0009-enclosure-construction.md) |
| E4b | Inter-MCU frame format and protocol versioning | [ADR 0013](docs/decisions/0013-two-mcu-split.md) |
