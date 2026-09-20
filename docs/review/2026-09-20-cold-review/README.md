# Cold review, round 2 — findings register

Twenty-three agents. The ten analog reviewers and the fault reviewer were
**forbidden from reading `docs/review/` or `docs/log/`** — they had never heard
of the first review's 53 findings or the eight decisions taken from it. That
blindness is the method: a finding that two blind agents reach by different
routes is evidence; a finding only the previous review made is a hypothesis.

Full documents are in this directory, ~19,500 lines. This file is the register.

## Verification status

Every item below marked **[verified]** was re-derived independently in the main
session against the repository or a datasheet — not taken on the agent's word.
Items marked **[agent]** are reported as received and still need checking.
Several vendor domains are blocked by this sandbox's egress proxy, so some
datasheet figures could only be reached through search summaries; those are
called out where they carry weight.

---

## Showstoppers

### S1. `U-LOADSW` TPS2553 is a 2.5–6.5 V part specified on the +12 V rail — 5 agents, [verified]

It does not survive first power-on. The *function* ADR 0005 specifies is right;
the part is wrong. ADR 0005 defends it on package grounds and never states its
voltage rating, which is the tell.

Not a simple swap: every modern one-chip 12 V eFuse checked fails the package
policy (TPS2592Ax is VSON-10, TPS27S100 is HTSSOP PowerPAD). The proposal on the
table is **LT1641-2CS8 (SO-8, 9–80 V) + N-FET + sense resistor**, latch-off
rather than auto-retry, because auto-retry reproduces the oscillating-protection
failure ADR 0014 analyses. This is a design decision, not a substitution.

**Four decisions across ADRs 0004, 0005 and 0014 depend on this limiter working.**

### S2. The ambient-zero injection has the wrong polarity — 4 agents, [verified]

The MPXV4006DP sits at **+0.2 V at zero pressure by design**. Through the in-amp
at G ≈ 2.13 that is +0.43 V at the output, so nulling it requires a **negative**
REF. DAC channel 6 spans 0–5 V and can only add.

Consequences: 4–9 % of full scale sits at the breath jack at rest; ADR 0006's
power-on table claiming "Breath — 0 V" is false whenever the instrument is on;
the panel offset knob is conscripted into the technical role, which is exactly
the two-offset-authorities split-brain ADR 0006 warns against; and the
continuous auto-zero cannot correct warm-up drift in the direction it needs to.

Two proposals, both reusing parts already in the BOM: make the downstream stage
inverting, or drive REF from a difference of two DAC channels as the mod
channels already do.

### S3. The in-amp has no common-mode bias return — 5 agents, [verified]

ADR 0003 mandates the pulldown **differentially across BREATH–AGND, not on one
leg**. That is correct for CMRR and provides no DC path for input bias current.
Unplugged — a normal, designed state — both inputs ramp at tens of volts per
second and the in-amp saturates in well under a second.

**The breath jack goes to a rail**, which is the exact inverse of ADR 0005's
"or unplugged — presents 0 V", and the frame watchdog cannot catch it because
breath never passes through the DAC. Switching the instrument off does this
every time.

Fix: 1 MΩ from each input to module analog ground, series resistance
symmetrised. The current diverted into AGND is tens of nanoamps against a
350 mA power return, so R35's no-current rule survives in substance — but R35
as written forbids the thing that makes the receiver work and must be restated.

### S4. The shared `CLR` zeroes the mod channels' offset — 1 agent, [verified]

Decision 4 sources the mod offset from DAC channel 7 *because* it makes power-on
safe: both terms clear to zero. True at reset. **False after watchdog recovery**
— firmware rewrites the signal channels and not the offset channel, so
`Vout = 4 × Vdac` and all four mod jacks pin at the positive rail (~+11.45 V).
Trigger is routine; with MISO deleted there is no readback, so it is undetectable.

Free fix: the latency budget already books six DAC words per pass while five are
written. Refresh the offset every pass. **With no readback, shared state can only
be made safe by being made stateless** — the same rule applies to the
reference-enable and clear-code registers.

### S5. The LM317 cannot meet its own specification — 2 agents, [verified]

| | |
|---|---|
| Worst low (V_ref 1.20, ±1 % divider) | 4.964 V |
| Nominal as specified | 5.250 V |
| Worst high (V_ref 1.30, + I_ADJ·R2) | **5.622 V** |

Required window: **4.95 V floor** (DAC window + headroom) to **5.50 V ceiling**
(DAC8568 recommended max). Spread 0.66 V against a 0.55 V window — **no nominal
value fits.** ADR 0005 applied ±4 % to the output and ignored both the divider
tolerance and the adjust-pin current.

Options: 0.1 % divider with a smaller R2 to shrink the I_ADJ term; an LP2951
with a 0.5 % reference; or delete the LM317 and use a second REF5050 buffered by
half an OPA2197 — a part number already in the BOM.

### S6. `U-TVS-UMB` is a ~5 V array drawn across a bus carrying +12 V — 3 agents, [agent]

V_RWM 5.0 V. It conducts continuously on the +12 V conductor and destroys itself
on first power-up, inside the bonded body. It also cannot cover eight conductors
in a SOT-23-6, and distributor data says the part is discontinued and in a
14-UDFN package the policy forbids — so the BOM's package field is wrong too.

Split by voltage: a 4-channel 5 V array on the SPI lines, a 12 V-standoff part
on BREATH, an SMAJ15A on the power pair. And fit protection at the **module**
end, which the BOM omits entirely.

### S7. Both current limits are set below the design's own worst case — 5 agents, [verified in part]

Independently rebuilt load tables converge at **390–650 mA** depending on
assumptions, against ADR 0005's 250 mA and ADR 0004's ~275 mA. The 500 mA
limiter and the 500 mA-hold polyfuse are **both below a state the firmware
thermal clamp explicitly permits.**

Two further consequences:
- **The limiter may prevent boot.** Constant-current charging ~1–2.7 mF of strip
  bulk at 500 mA takes 22–65 ms, during which the buck never reaches its 8 V UVLO.
- **The polyfuse is downstream of the load switch**, so the load switch does not
  break the runaway loop ADR 0014 believes it deleted. ADR 0014 added the switch
  and never deleted the device it named as the problem.

The polyfuse is also the largest resistance in the 12 V path (0.11–0.44 V, more
than the Schottky and the whole cable), dissipates ~0.26 W inside the sealed box,
derates to ~300–400 mA hold at the documented interior rise, and behind a fast
module-side limiter can never trip cleanly. **Multiple agents recommend deleting
it outright.**

---

## Major — things that are simply missing

### M1. Every output reconstruction capacitor — 4 agents, [verified]

ADR 0006 specifies corners for all six outputs and says the pitch filter's
"corner is set by its own R and C". `R-OUT-PROT` is the R. **The C appears
nowhere in the BOM, and no value appears anywhere in the repository.**

Dielectric is load-bearing, not a detail: X7R in a pitch reconstruction filter
is a literal microphonic detuning element, and its DC-bias coefficient moves the
corner ~30 % at 10 V. C0G or film.

### M2. The mod channels' gain network — 2 agents, [verified]

`Vout = 4 × (Vdac − Voffset)` needs 16 discretes or four matched networks.
Neither is in the BOM. ADR 0006 also contradicts itself on which it wants.

### M3. The in-amp's gain resistor — 2 agents, [verified]

ADR 0003 says the in-amp "absorbs the ~2.13× scaling stage". **An in-amp is
unity gain without an external R_G.** As specified the breath receiver has a
gain of 1 and the scaling stage does not exist. The value is not portable
between the two candidate parts, so the unresolved "INA821 or INA828" blocks it.

### M4. 34 further line items specified in ADR prose with no BOM row — 1 agent, [verified in part]

Including: no PCBs and no dev-board headers anywhere; the watchdog's R/C timing
pair, so its N is undefined; the load switch's ILIM resistor, which *is* the
limit; the OE-gating network; key-switch pull-ups and filtering; the entire
ADR 0009 fastening set (U-bolt, backing plate, thumb plate, adhesive, loom wire);
and the USB/umbilical OR-ing diode that ADR 0005 decided and the previous review
called the highest bench-damage risk in the project.

**Module decoupling is ~half-counted** (qty 10 against 16–18 supply pins) and the
controller side has decoupling only for the shift registers.

---

## Major — things that are wrong

### W1. The anti-alias filter is at 121 Hz, not 600 Hz — 5 agents, [verified]

R_th = 10k ‖ 15k = **6.00 kΩ**, not one leg. With 220 nF that is 120.6 Hz —
*below* the sensor's own 159 Hz bandwidth, so the filter attenuates the signal
it exists to pass, and adds **1.32 ms** of group delay that appears in no budget.
The adjacent claim that it "settles well inside the 250 µs loop period" is wrong
by an order of magnitude.

**This is a transcription error, not a bad calculation.** 47 nF gives 564 Hz and
58.9 dB at 500 kHz — *exactly* the two numbers ADR 0003 asserts. The arithmetic
was done correctly for a 47 nF part and 220 nF was written down.

The two specifications in that one paragraph are also mutually exclusive: 600 Hz
with 220 nF requires a 1.21 kΩ source, and the same paragraph mandates ≥10 kΩ.

### W2. "The 1 kΩ output resistor is a pure gain error" is false — 1 agent, [verified]

`Vout = k(2·Vdac − 2.5)` scales **both** the slope and the offset. A firmware
scale factor corrects the slope and leaves a constant residual:

| Trimmed at 100k, played into | Residual |
|---|---|
| 50 kΩ | **+29.1 cents on every note** |
| 33 kΩ | +58.5 cents |
| open → 100 kΩ | −29.7 cents |

So ADR 0006's stated mitigation converts a progressive tracking error into a
flat 29 cents sharp, which is worse to play. **The decision to keep the 1 kΩ
survives; the reasoning for it does not.**

The resolution is better than the original: the 0.25–4.75 V window already
reserves **±600 cents of firmware offset authority**, because firmware can shift
the DAC code. "Nothing implemented `b`" was a property of the calibration
*model*, not the hardware. Store an affine `(gain, offset)` pair per load preset.

### W3. The pitch offset has no specified voltage reference — 3 agents, [verified]

ADR 0006 names the trimmer as "the offset authority for pitch" and never says
what it divides down. The only source that exists in the committed topology is a
divider from a ±12 V rail, sensitivity ~0.21 V/V:

- 12 mV of rail thermal drift → **3.0 cents**
- 50 mV load step when another module powers up → **12.5 cents of transposition**
- The WS2815 square wave on that rail → **~22 cents p-p of pitch FM**

**ADR 0004 worried about exactly this rail and defended the op-amp's supply pins**
— 80 dB of PSRR, 0.011 cents — **while the offset reference is a bare divider
off the same rail with no rejection at all. 86 dB off the right node.**

### W4. Blow harder, the pitch bends — 3 independent mechanisms, [verified]

Three agents found breath-correlated pitch error by completely separate routes,
and they add:

| Route | Magnitude |
|---|---|
| Offset reference rail (W3) | ~22 cents p-p |
| The rack's shared bus ground | ~4.8 cents |
| The module's internal ground | 5.7–7.2 cents |

Each is larger than every term in ADR 0006's precision budget, and they are the
only *dynamic* ones. **The one test in the plan for this class of problem scopes
the breath jack — the channel that is immune. Nobody ever scopes pitch while
sweeping the LEDs.**

Cheapest mitigation is one firmware line: drive the animation as a moving dot or
bar on a **constant-total-current field** rather than modulating brightness.

### W5. The umbilical SPI clock does not close — 5 agents, [verified]

ADR 0004's 0.6 MHz derives from a **2 kHz** mod rate that ADR 0006 later revised
to 4 kHz, and nobody propagated it back.

| Clock | Six 32-bit words | vs 250 µs |
|---|---|---|
| 0.6 MHz | 320 µs | **fails** |
| 1 MHz | 192 µs | closes, no margin |
| 2 MHz | 96 µs | closes |

**ROADMAP E11 — a gate before the body closes — currently validates a bus speed
the instrument cannot use.**

### W6. The latency budget omits the filter poles the design specifies — 3 agents, [agent]

The analog path's "< 0.2 ms" line must carry two 500 Hz poles (636–716 µs) plus
the module filter. The digital path omits the anti-alias filter and the
pneumatic restrictor entirely. Re-summed, the note-onset path is **4.1–4.7 ms
against a 5 ms target**, and ADR 0003's "roughly 10× margin" is about 1.1×.

### W7. The Helmholtz model is invalid — 1 agent, [verified]

For a 3 mm bore the neck volume is 2.83 mL — **larger than the ≤1 mL trap**, so
the lumped assumption is violated backwards. The correct model is a distributed
organ pipe at **214–429 Hz**, below the 500 Hz corner, and **independent of trap
volume**: no restrictor size fixes it.

**The tube bore is specified nowhere in the repository**, so the two published
resonance figures describe different tubes. Restate the intent as *damping*
rather than *placement*, specify the bore, and rewrite the E2 row.

### W8. "Any Ethernet cable works" is also the hazard — 1 agent, [verified by construction]

Not every RJ45 lead is straight-through, and the wrong ones are visually
identical.

| Cable | Swaps | Against the T568B map |
|---|---|---|
| Rollover / console | 1↔8, 2↔7, **3↔6**, 4↔5 | 3 and 6 are **+12 V and PWR_GND** → reverse polarity |
| 10/100 crossover | (1,2) ↔ (3,6) | **BREATH/AGND ↔ +12 V/PWR_GND** → 12 V onto an unpowered op-amp output |

**ADR 0004 fits two Schottkys on the rack connector because "keying alone is not
worth trusting" — for a connection made once in the module's life — then trusts
a generic consumable patch lead completely.**

A pin-map reorder was considered and declined with a reason: a gigabit crossover
swaps the other pair group too, so no mapping is safe against both. Fix is a
shunt SS34 in the footprint the polyfuse vacates, plus 1 kΩ + BAV99 on BREATH.

### W9. The etherCON cannot mount as specified, at either end — 1 agent, [agent]

- **Max panel thickness is 4 mm.** ADR 0009 mounts it through 6 mm oak. Not
  unwise — outside the part's specification. The tail needs a thin metal end cap,
  which the laminated stack has no layer for.
- **"Brace it to the module PCB" is not buildable as one board.** Jacks put the
  PCB ~7 mm behind the panel; the etherCON body extends 30–40 mm; clearing it
  needs a ~26 mm notch in a ≤28 mm board, which severs it. Fix is a two-board
  module, which makes the bracing true by construction.
- **There is no solder-tag etherCON.** ADR 0004's open question is unanswerable
  as posed. The real range is feedthrough, PCB-mount, IDC and shielded CAT6A —
  and the **IDC variant is strictly better** for a body that cannot be reopened.
- **Intermate trap:** NE8FDX-P6 does not mate with the NE8MC6-MO carrier. Both
  ends must be chosen as a family, which deciding them at E12 and M7 separately
  would have walked into.

### W10. Diagnostic access is designed out — 1 agent, [verified]

- **The UART0 console costs two pins and routes to a header inside the sealed
  body.** ADR 0007 justifies the pins on the grounds that "in a body that cannot
  be opened, two pins is a cheap price for keeping a console", then buries it.
- **The presence detect senses the panel switch, not the instrument.** Umbilical
  +12 V is downstream of the module's own load switch, so it is present with no
  instrument attached — it fails in precisely the state it exists to detect. And
  ADR 0004 cites that gating as "the reason the power switch had to move to the
  module", so part of decision 7's justification rests on a mechanism that does
  not work.
- **The display board has no external access of any kind** — no USB, no console,
  no reset, no boot — and under the single-source-of-truth rule it is the only
  path from the phone to the real-time board's NVS. A bricked display board makes
  a *working* instrument permanently unconfigurable.
- **Neither board can be forced into bootloader mode once bonded.** On the S3 the
  USB-Serial-JTAG auto-reset path disappears the moment the app claims USB-OTG
  for MIDI. One bad image ends the instrument.
- **Three milestones cannot be performed as written:** E3 (the IMU's I2C is
  onboard and never broken out — permanently unobservable), E4b (no analyser
  landing), E14 (buses sit under seated dev boards).
- **The frame watchdog will fight E7–E10**, asserting CLR while E7's method is
  "write a code, read the meter".

A free presence-and-health detect exists and is unused: the sensor's 0.2 V
zero-pressure floor against the module's pulldown means **one comparator**
reports cable connected, +12 V reaching the far end, reference alive, sensor
alive, buffer alive, both analog conductors intact.

---

## Errors of my own worth naming separately

- **The 496.1 kHz buck frequency was invented** to make an aliasing example land
  on 100 Hz. The R-78E5.0 is **330 kHz**. The principle is sound; the number was
  theatre, and it is in both ADR 0003 and the BOM.
- **The Matrix board has 17 usable GPIO, not 16.** GPIO33 is broken out; I missed
  it by truncating my own source when reading it, then recorded 16 in three
  places.
- **`U-DAC`'s part field reads "full orderable P/N required"** — an instruction
  written into the field instead of obeyed, in a row whose grade letter ADR 0006
  calls "the whole decision". And **"(or A grade)" is unsafe**: A/C both reset to
  zero scale, but the letter also sets the reference gain, so an A-grade part
  halves every span.
- **`U-BREATH`'s package field says "THT leads".** The MPXV4006DP is **8-SOP
  surface mount** — which I had in front of me when I researched it. It therefore
  **cannot be socketed**, which breaks ADR 0003's wear-part plan.
- **The 74HC-vs-LVC note landed on the keycap row**, because my edit matched
  `"165" in part` and `MT165-MX` contains "165".
- **The README has two licensing sections**, one of which still says "not yet
  decided".
- **`U-REG-DAC`'s "135 mW"** is 34 mW: 6.75 V × 5 mA.

---

## Agent-versus-agent conflicts

**Resolved: the WS2815 logic threshold.** One agent claimed V_IH = 0.7 × 12 V =
8.4 V, making the 74AHCT125 out of spec and requiring a 12 V gate driver. Three
other sources and a datasheet check agree the WS2815 **drops 12 V to 5 V
internally**, logical input range 3.7–5.3 V, V_IH ≈ 3.5 V. **The 74AHCT125 is
correct with ~1.1 V of margin, and a direct 3.3 V drive genuinely would have been
marginal — so the shifter is both necessary and adequate.** An ADR 0014 open item
closes in the design's favour.

---

## What the review confirmed as right

Stated here because a confirmation is a result, and because the register above
reads worse than the design is.

- **"The analog architecture is genuinely good and I could not break it."**
  Total coupled noise at the breath jack is **~60 µV on a 10 V output (−104 dB)**,
  and nothing the instrument does reaches pitch above **0.03 cents**. The
  failures are in the sampler, the digital wiring and one undefined DC reference
  — *not* in the analog channel the ADRs spent their effort defending.
- **The ratiometric-supply decision was more right than argued.** Its own table
  quoted sensor-referred figures: jack-referred, 0.4 % rail excursion is 42.6 mV
  not 21 mV, and the margin over the AGND path is ~50 dB not ~30 dB.
- **The AGND sense return holds at every frequency tried** — 3–7 µV at the jack
  across DC, LED PWM and WiFi bursts. The 500 Hz band-limit turns 943 µV of
  500 kHz cable crosstalk into 0.94 µV, and is called the single most valuable
  noise decision in the project.
- **The breath buffer on +12 V** is called the best single piece of fault
  reasoning in the document set — it dissolves a conflict rather than trading it.
- **The dedicated SPI host for the 74x165 chain** is called the best single piece
  of work in the repository.
- **An independent thermal model gives 2.89 K/W** against the guessed 3 K/W.
- **The 0.25–4.75 V window makes the pitch gain exactly 2.000**, which *is*
  buildable from a matched quad — so the "9/5 is not constructible" objection
  that drove the trimmer decision is dissolved, and the ADR never noticed.
- **The out-of-loop RC** settles an octave leap to within 1 cent in 71 µs and no
  cable capacitance can destabilise it. **BAV99-over-BAT54S** re-derives exactly.
  **The T568B pin mapping** is called genuinely good work. **The A/C grade
  analysis**, the **differential pulldown's principle**, **blank-at-boot**, the
  **load switch at the module**, **M8 as a pre-bond gate**, and the **12 V-not-5 V
  umbilical** all verify.
- **Everything the design worked hardest for** — matched network, internal
  reference, op-amp grade, trimmer tempco — **RSS to ~0.8 cents over 10 K**,
  comfortably inside the 3.5 cents the VCO does by itself.

And one over-specification worth acting on: **the LT5400 is 20–30× over-specified**
now that the trimmer sits in the gain ratio. It buys 0.11 cents against the
trimmer's 2.4. Two 0.1 % / 10 ppm thin-film 0805s do better, and dropping it
removes the design's only MSOP part.

---

## Patterns

**1. Reversals get chased into the deciding ADR and not into the consuming ones.**
Three decisions account for most of the staleness — the sensor and board moving
to the tail, breath going single-ended, and the mod rate going 2 → 4 kHz. Each
was applied to its own ADR, the ROADMAP and the BOM, and not to a sibling ADR's
summary table, zone diagram or power tree. **Five agents independently flagged
ADR 0013's zone table**, which is physically impossible as written: it puts the
IMU in a different zone from the board the IMU is soldered to.

**2. The BOM buys the ICs and forgets the circuits around them.** 34 specified
items with no row, against only 4 wrong citations and 6 wrong quantities. The
ADRs are good; the gap is between the reasoning and the parts list.

**3. Fixes that are each correct alone compose into failures.** The DAC-sourced
offset plus the frame watchdog gives S4. The +12 V breath rail plus the buck's
UVLO gives the brown-out window where breath stays live while everything else is
parked. Decision 8 plus ADR 0005's USB-OR gives an instrument that can no longer
run on the bench. **This is now the dominant failure mode in the project and
nothing in the process catches it**, because every reviewer is assigned a
subsystem.

**4. Precise-looking numbers that were never computed.** The 496 kHz, the 16
GPIO, the 135 mW, the 600 Hz corner, the "<0.2 ms" filter allowance, the 250 mA
budget. Each reads as rigour. The register above should be treated as evidence
that a stated number in this repository is not yet a verified one.

---

## Not yet applied

**Nothing in this register has been applied to the design.** Edits were held for
the whole wave so that agents were not reviewing a moving target and so that
duplicates could be collapsed against a stable text.

Three items are the natural first block because everything else is downstream of
them: **S1** (the load switch blocks the module PCB), **S7** (the current budget
sizes both protective devices and the thermal clamp), and the **ADR 0013 zone
table**, which four other findings reference for geometry that gets bonded shut.
