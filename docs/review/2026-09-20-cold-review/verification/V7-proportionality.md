# V7 — Proportionality review

**The question nobody in the register was asked:** which of these ~100 proposed
changes are not worth making?

Twenty-three agents were each told to find problems in a subsystem. Each did.
None was told to find the problems that should be left alone, and none was
costed against the one thing that actually governs here: **one instrument, one
player, built once, for the author's own rack.** This document does that costing.

---

## The yardsticks I judge against

These come out of the repository, not out of me. Every "immaterial" verdict
below is measured against one of them.

| Domain | What the design already accepts | So the threshold is |
|---|---|---|
| **Pitch, static** | Trimmer tempco **2.4 cents** over 10 K (ADR 0006, deliberately chosen over a 0.11-cent network); the driven VCO's own drift **3.5 cents** over the same 10 K | A static pitch term under **~1 cent** changes nothing. Anything the trimmer or NVS table can absorb is not an error, it is a calibration input |
| **Pitch, dynamic** | Nothing. The design has no budget for pitch that moves *while you play* | A breath-correlated or LED-correlated term of **5 cents or more is a different kind of defect** and is worth real money. This is the axis the review found and the design never had |
| **Breath** | Total coupled noise **~60 µV on a 10 V output (−104 dB)**, called a non-problem by the reviewer who tried hardest to break it | A breath-channel term under **~10 mV** (0.1 % of span) is below what a diaphragm can even command |
| **Latency** | 5 ms target; a hard tongue attack rises in **5–15 ms** | A term under **~250 µs** is not perceivable. A term over **1 ms** is worth one part |
| **Resolution** | 16-bit on 10 V = 153 µV; 12-bit ADC on 3.3 V = 806 µV | Sub-LSB findings are arithmetic, not defects |
| **Serviceability** | Module = four screws, forever. Instrument = **bonded shut at M8** | A module-side part is worth roughly a tenth of the same part inside the body. B10 got this exactly right and then did not apply it consistently |

And one the register does not state: **this player has built and played the
previous generation of this instrument.** Findings premised on a user who cannot
diagnose, cannot measure, and cannot reason about their own instrument are
findings about a product.

---

# Part 1 — The ten changes worth making, ranked

Ranked by: free × unretrofittable × "the player would experience this as their
own fault."

### 1. W14 — key-switch pull-ups and input RC on all 18 chain inputs

**Why first.** Every key input currently floats when its key is open, in a side
channel shared with 12 V WS2815 power and 800 kHz data, feeding a debounce that
fires on the *first* closed sample. A 12 V LED edge at ~120 V/µs through ~15 pF
injects a full false level. The failure is a note that is wrong, not a note that
is missing — combinational fingerings mean one spurious bit returns a *different
note*, which presents as "some fingerings feel wrong."

**Cost.** 18 × (10 kΩ + 10 nF) = 36 passives on a board being laid out anyway.
The 100 Ω series element is optional if the capacitor sits at the register pin;
I would fit the pull-up and cap and reserve the 100 Ω pads.

**Why it cannot wait.** Entombed. The day the body bonds this becomes permanent.

**What it buys beyond the fix:** the release side gains a free ~100 µs hardware
filter, which is the one place the ROADMAP is right that filtering in firmware
costs attack latency.

**Do not** fit pull-ups on the 14 spare chain bits (B10's finding 23 asks for
32). Tie unused register inputs to ground at the package with copper. Zero parts.

### 2. C5 F1/F2 — an external service header for both boards, plus OTA rollback

Five wires (EN, IO0, U0TXD, U0RXD, GND per board), a 10 mm slot and a screwed
cover at the tail. Plus, free in firmware: two OTA partitions with
`CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE`, and **USB MIDI made opt-in rather than
the default** so the USB-Serial-JTAG reset path survives boot.

**The failure it prevents is total and the mechanism is specific.** On the S3 the
internal PHY routes to USB-Serial-JTAG *or* USB-OTG, not both. The moment the
app claims OTG for MIDI, the DTR/RTS download-mode path disappears. One bad
image, or one brown-out corrupting the app partition, ends the instrument —
inside a body that cannot be opened. The display board is worse: it has no
external access of any kind and it is the only route from the phone to the
real-time board's NVS, so a bricked display board leaves a *working* instrument
permanently unconfigurable.

USB MIDI is declared a bring-up tool in the README. It should not be what costs
the instrument its recovery path.

### 3. S3 + M3 + S2 — make the breath receiver actually work

Three register entries, one circuit, one schematic revision:

- **M3: the in-amp has no gain resistor.** An in-amp is unity gain without R_G.
  As specified the "~2.13× scaling stage" does not exist and breath tops out
  around 4.5 V instead of 10 V. This is not a defect, it is a missing part.
- **S3: no common-mode bias return.** Unplugged or switched off — a *designed*
  state — both inputs ramp at tens of volts per second and the in-amp saturates
  in well under a second. The breath jack goes to a rail, which is the exact
  inverse of ADR 0005's "presents 0 V". Two 1 MΩ resistors. Tens of nanoamps
  into AGND against a 350 mA power return; R35's no-current rule survives in
  substance and needs one sentence restated.
- **S2: the ambient zero can only add.** The sensor sits at +0.2 V by design;
  through the in-amp that is +0.43 V needing a *negative* REF, and DAC channel 6
  spans 0–5 V. Fix by the difference-of-two-DAC-channels trick the mod channels
  already use — no new part number.

Module-side, therefore serviceable, therefore lower on this list than it looks.
It is here at 3 because it is the difference between a breath channel and a
breath channel that works.

### 4. W1 — `C-AA-ADC` 220 nF → 47 nF

**A five-cent part and a transcription error.** R_th = 10k ‖ 15k = 6.00 kΩ, not
one leg. 220 nF gives 120.6 Hz — below the sensor's own 159 Hz bandwidth — and
**1.32 ms of group delay that appears in no budget.** 47 nF gives 564 Hz and
58.9 dB at 500 kHz, which are *exactly* the two numbers ADR 0003 asserts. The
arithmetic was done correctly for a 47 nF part and 220 nF was written down.

One value change removes 1.3 ms from the note-onset path — more latency than any
other single item in the register, for less money than any other item in the
register.

### 5. S4 + W5 — the output loop must refresh everything, and must actually close

**S4 (free):** the mod offset is written once at boot. After any watchdog `CLR`,
firmware rewrites the five signal channels and not channel 7, so
`Vout = 4 × Vdac` and all four mod jacks pin at ~+11.45 V, indefinitely. With
MISO deleted there is no readback, so it is undetectable. The latency budget
*already books six DAC words per pass while five are written*. Refresh the
offset every pass. **Zero cost.**

Generalise it into an architecture rule in `firmware/README.md`: *with no
readback, shared state can only be made safe by being made stateless — refresh
everything, every pass, and do not optimise the loop to write-on-change.* That
one sentence also closes the reference-enable and clear-code registers, and two
diagnostics findings arrive at it from the opposite direction.

**W5 (free, and time-critical):** ADR 0004's 0.6 MHz derives from a 2 kHz mod
rate that ADR 0006 revised to 4 kHz. At 0.6 MHz six 32-bit words take 320 µs
against a 250 µs period — it does not close. **E11 is a gate before the body
bonds and it currently validates a bus speed the instrument cannot use.** Change
the number in ADR 0004 and in ROADMAP E11 to ≥2 MHz before E11 runs. There is no
second chance to test the real cable at the real rate.

### 6. W3 + W4 — give pitch a reference, and stop modulating its rail

This is the only class of pitch error large enough to hear, and it is the class
the design has no budget for, because it *moves while you play*:

| Mechanism | Magnitude | Fix |
|---|---|---|
| Offset trimmer divided off a bare ±12 V rail (W3) | ~22 cents p-p of WS2815-correlated FM; 12.5 cents of transposition when another module powers up | Divide the trimmer from the DAC's `VREFOUT` instead. Two parts |
| Module analog rail and umbilical feed share one 1N5817, so instrument current modulates V_f by ~80 mV (W4) | **~20 cents** | Separate diodes, or move the branch point upstream. One part, visible by inspection of ADR 0004's own power-tree diagram |
| LED animation modulating total current | drives both of the above | Drive the animation as a moving dot/bar on a **constant-total-current field**. One firmware line, free |

ADR 0004 defended the op-amp's supply pins for 80 dB of PSRR and 0.011 cents
while leaving the offset reference as a bare divider on the same rail with no
rejection at all. **86 dB off the right node.** Both hardware fixes are free at
layout and impossible after fab.

**And schedule the missing test:** the one measurement in the plan for this class
scopes the breath jack — the channel that is immune. Scope *pitch* while
sweeping the LEDs.

### 7. W2 — store an affine `(gain, offset)` per load preset

Free firmware, and it prevents the failure the player is most likely to blame on
themselves. `Vout = k(2·Vdac − 2.5)` scales both slope and offset, so a firmware
scale factor corrects the slope and leaves a flat residual: trimmed at 100 kΩ and
played into 50 kΩ is **+29.1 cents sharp on every note**; into 33 kΩ, +58.5. The
current mitigation converts a progressive tracking error into a constant 29 cents
sharp, which is worse to play.

The hardware authority already exists — the 0.25–4.75 V window reserves ±600
cents of firmware offset because firmware can shift the DAC code. "Nothing
implemented `b`" was a property of the calibration *model*, not the hardware.
This is the cheapest change in the register with the largest audible effect.

Keep the 1 kΩ. The decision survives; only its stated reasoning does not.

### 8. S7 — delete `F-POLY`, and size the limiter from E6's measurement

**A change with negative cost.** The polyfuse is:

- below the design's own worst case (rebuilt load tables converge at 390–650 mA
  against a 500 mA hold);
- the largest resistance in the 12 V path (0.11–0.44 V, more than the Schottky
  and the whole cable);
- 0.26 W dissipated **inside the sealed box**, derating to ~300–400 mA hold at
  the documented interior rise — i.e. limiting during normal play;
- downstream of the load switch, so it reinstates the slow current-limiting
  runaway loop ADR 0014 believed it had deleted;
- entombed, and therefore the one protective device that can never be resized.

Delete it. Then size the module-side limit from the **measured** inrush at E6
(the ROADMAP already schedules that measurement), above the load the firmware
thermal clamp explicitly permits — not below it, which is where both current
limits sit today.

### 9. M1 — the six output reconstruction capacitors

ADR 0006 specifies corners for all six outputs and says the pitch filter's
"corner is set by its own R and C." `R-OUT-PROT` is the R. **The C appears
nowhere in the BOM and no value appears anywhere in the repository.**

Two things must be written down, not one:

- **Dielectric.** X7R in a pitch reconstruction filter is a literal microphonic
  detuning element and its DC-bias coefficient moves the corner ~30 % at 10 V.
  C0G or film. Same price, same footprint.
- **Position relative to the 1 kΩ.** On the wrong side of it, the output stage
  sees a capacitive load inside its loop and can oscillate. This is the one place
  in the register where an unspecified *placement* is a functional hazard rather
  than a tidiness complaint.

### 10. D5 #2 and #5 — the mouthpiece, and the switch count, before M3

The only items in the register whose deadline is **M3, layout lock** — earlier
than everything else, because a switch that is not in the plate DXF never exists.

- **The mouthpiece does not exist.** It appears four times as a reference point,
  never as a part, dimension, material or ADR. **E2's own acceptance test
  requires one** ("a human plays it for 20 minutes through a real mouthpiece").
  The inlet geometry laminates into the stack.
- **"14 spare chain bits" are not spare switches.** The bits are free; the
  switches, keycaps and plate cutouts are not, and the BOM carries 18 for 18.
  Octave, hold and preset keys are a plate-DXF decision, not a firmware one.

Neither is electrical and neither is expensive. Both are unrecoverable at M3.

---

### Near-misses, named so they are not lost

These are good and cheap; they lost on ranking, not on merit.

- **D4 #1 — a CRC'd commissioning fingerprint in NVS at M8.** Eleven proposed
  detectors are of the form "it got worse" and have nothing to be worse *than*.
  M8 already gathers most of the numbers and stores none, and after bonding they
  can never be re-measured. Free, and it is the enabling item for everything else
  in D4.
- **W11 — gate the auto-zero decay on "sub-threshold AND quiet"** (σ below 2×
  commissioning). Free firmware; reuses ADR 0007's stillness-gated IMU pattern.
  The current rule eats sustained pianissimo and re-zeros during a
  circular-breathing catch-breath.
- **The QMI8658C die-temperature register.** Three agents found it independently.
  A free interior thermometer, on a bus already in use, centimetres from the
  breath sensor, that closes the thermal budget on measurement and discriminates
  thermal drift from a blocked reference port. Confirm at E1 — if it is usable,
  the "add a temperature sensor before bonding" finding evaporates.
- **W10's presence comparator.** ~6 parts on the *module*, reporting cable
  connected, +12 V reaching the far end, reference alive, sensor alive, buffer
  alive, both analog conductors intact — from the sensor's own 0.2 V floor
  against the module pulldown. Worth it precisely because it lives four screws
  away forever, which is the structural rule D4 got right: *put unobservable
  things in the module, never in the instrument.*
- **C3 #20 — slot the strap holes in the key plate and the backing plate.** M5
  cuts the plate, M8 finds the balance point. A slot in a laser-cut part is free
  and resolves the ordering conflict without reintroducing the adjustability the
  first review correctly killed.
- **`MECH-GNDBOND` as a stainless star washer against abraded aluminium, bonded
  short.** Pennies, and a bond measured at <0.1 Ω on the M8 checklist or never.

---

# Part 2 — The decline list

Each entry: the finding, why it should be declined, and **what declining costs**.

## A. Findings that only matter outside the design scope

### A1. The rack-rail overvoltage protection set (D1 #16)

**Proposed:** SMAJ5.0A on +5 V, SMAJ15A on +12 V and −12 V.

**Decline the +5 V and ±12 V TVS.** The named mechanism is a bus-board or PSU
+5 V regulator failing short from +12 V. That is an event in which every module
in the case is being damaged simultaneously; defending this one is defending
against a day you have much larger problems. The finding also concedes that an
SMAJ5.0A clamps at ~9.2 V — enough to marginally save a 74AHCT125 and **not**
enough to keep the DAC inside its 6 V input maximum. It is insurance that does
not cover the loss.

**Consequence of declining:** if the rack PSU fails high, the module's level
shifter and possibly the DAC die. Both are on a board that unscrews from the rack
in five minutes; together they are about $12. Nothing inside the bonded body is
at risk, because the umbilical's 12 V feed passes through the module's own
limiter.

**Keep the free half:** `D-REVPOL` 1N5817 → **SS34/SS54**. Same price, same
footprint, 40 V instead of 20 V, 3 A instead of 1 A. That is a substitution, not
a circuit.

### A2. The counterfeit-avoidance programme (C4 §2.5)

**Proposed:** authorised-distributor-only policy across six lines, Neutrik
hologram verification, grade re-marking vigilance, "no LCSC, no independent
brokers even when the pages look official."

**Decline as a programme.** This is procurement policy for an organisation
buying reels. One person buying singles buys from DigiKey or Mouser because that
is where you buy singles; the policy is already satisfied by doing the obvious
thing, and writing it down as a controlled process generates review work with no
risk reduction.

**Consequence of declining:** essentially none, because the behaviour happens
anyway. The residue worth keeping is two sentences, not a section: buy the
DAC8568 grade and the pressure sensors from a broad-line distributor and keep the
packaging, because those are the two lines where a wrong part is invisible on a
meter and one of them is entombed.

### A3. The dry-circuit gold-contact toggle (C3 #15)

**Proposed:** specify a gold-contact / low-level-switching toggle, *and* add a
wetting-current resistor.

**Decline the gold part.** The mechanism is real over a few years. The part is a
$2 panel toggle on a module that unscrews from a rack. Specifying a
contact-material suffix — with the finding's own confidence marked medium on the
part families — is precision the design cannot use.

**Consequence of declining:** in some years the power toggle becomes
intermittent and you replace it in ten minutes, having learned something. The
10 kΩ wetting resistor is one 0805 and falls naturally out of the enable network;
fit it if the enable pin wants a pull anyway, and stop there.

### A4. The umbilical cable acceptance test (B7 F11)

**Proposed:** four-wire loop-resistance measurement on every new patch lead
before it goes into service, acceptance limit <0.45 Ω.

**Decline the ritual.** The design *declares* the cable a consumable and says
"replace at the first intermittency." Attaching an incoming-inspection procedure
to a consumable contradicts the reason it is a consumable.

**Consequence of declining:** if a 28 AWG slim lead gets grabbed, the +12 V drop
roughly triples and the parallel-return offset goes from 41 mV to 102 mV. All of
that is common-mode at the in-amp and rejected; the AGND sense return measures
3–7 µV at the jack across every disturbance tried. Nothing audible changes.

**Keep the free half:** put "24 AWG stranded pure copper, not CCA, not 26/28 AWG
slim" in the `CABLE-UMB` row. That is a word, and it prevents the only version of
this that bites.

### A5. Connectorised internal looms (D2 #13)

**Proposed:** make every internal loom segment isolable, swappable and
independently measurable.

**Decline.** Connectors inside a body that is shaken for hours on a strap are a
*new* failure mode, and the classic one: intermittent contact that presents as a
wrong note. The same review document asks elsewhere for tube clips and strip
retention because things walk loose in there. Soldered looms are the correct call
for a bonded instrument; this finding imports a serviceable-product assumption
into an explicitly unserviceable object.

**Consequence of declining:** a loom fault is localised by measurement rather
than by substitution. The author has a full bench and the marker pattern already
makes chain errors countable.

### A6. Permanent pneumatic test access (D2 #4)

**Proposed:** a way to apply a known pressure to the breath path after bonding.

**Decline.** A permanent port is a permanent leak path into the one pneumatic
system in the instrument, on a sensor whose *reference* port already depends on a
controlled cavity leak. The fix creates the failure mode the design spends
several pages managing.

**Consequence of declining:** less than the finding claims. The tube is
dead-ended and the mouthpiece is its open end — the test port is the thing you
put your mouth on. With D4 #1's commissioning fingerprint stored, a later "blow a
steady note and compare zero and span to commissioning" is a real check that
costs nothing and needs no hole.

### A7. The C5 architecture alternatives A1–A6

**Proposed:** six alternative MCU/board architectures, including RP2350,
ESP32-P4 + C6 companion radio, and collapsing to a single MCU.

**Decline wholesale.** The document's own conclusion is "keep the split." No
named defect motivates the alternatives. Re-opening the board choice re-derives
the pin map, the carrier outline, the zone table, the loom lengths and three
ADRs, to arrive where the design already is.

**Consequence of declining:** none. The three real items inside C5 (F1, F2, F13)
are on my keep list and are independent of the board choice.

---

## B. Fixes that cost more than the failure they prevent

### B1. The pre-emptive feedback compensation capacitors (B9 #7)

**Proposed:** 5–10 pF C0G across each feedback resistor on five stages, on the
basis of an assumed 15 pF of inverting-node stray giving 14–39° of phase margin.

**Decline the capacitors; adopt the resistor values.** The resistor values
(10 k/40 k mod, 10 k/10 k pitch) have to be chosen anyway and choosing them
correctly is free — the finding's real contribution. The capacitors are sized
against a stray capacitance that is a *layout property nobody has laid out yet*,
and the finding's own falsification test is "step it and scope it." This is a
one-off with a full bench and a module that opens.

**Consequence of declining:** if a mod channel overshoots at E10, you solder a
5 pF across the feedback resistor in ten minutes. **Reserve the five footprints**
— that is free at layout and is the proportionate version of this finding.

### B2. A supervisor IC for the frame watchdog (D1 #7)

**Proposed:** power-on reset and undervoltage hold on `U-WATCHDOG`.

**Decline.** The watchdog exists to stop a drone. A supervisor watching the
watchdog is a part whose own failure mode is *holding `CLR` asserted*, which
mutes pitch and all four mod channels permanently. A protection circuit that can
fail is not free, and this one fails toward silence on the channel the instrument
is for.

**Consequence of declining:** during the power-on ramp the monostable's state is
undefined for a few milliseconds. The instrument is being switched on; nothing
downstream has settled either. Adopt instead the free polarity rule B10 already
names — **retrigger-is-not-cleared** — and put the watchdog on the DAC's own
rail so the two come up together. Zero parts.

### B3. A breath-mute FET on the watchdog (W13, D3 #11)

**Proposed:** `Q-BREATH-MUTE` so the watchdog can reach the sixth jack.

**Decline — and note that W13's severity collapses once S3 is fixed.** W13
reasons about breath as if it were a DAC channel that can latch. It is not: the
breath path is **analog end to end from the player's mouth**. It cannot be stuck
at a level the player is not producing. The two ways it *could* misbehave are:

- unplugged or powered off → **that is S3**, the missing bias return, which is
  on my keep list and parks the jack at 0 V as ADR 0005 always claimed;
- `CLR` removes the ambient zero → the jack acquires the un-nulled pedestal,
  4–9 % of span. A standing offset, not a drone, on a channel the player is
  holding in their hands.

A FET across the main expression output is a part that can fail closed and mute
the instrument.

**Consequence of declining:** after a watchdog event the breath jack sits up to
~0.9 V high until firmware recovers. The pitch and mod channels — the ones that
*can* drone — are already parked by `CLR`.

### B4. A hardware `LDAC` line (B4 #2)

**Proposed:** synchronise the offset channel and the four mod codes with `LDAC`.

**Decline the conductor.** The umbilical is 8 of 8 and adding a ninth means
changing the connector, which is the largest mechanical decision in the project.

**Consequence of declining:** nothing, because the DAC8568's write-and-update
command form plus S4's refresh-every-pass discipline gives the same guarantee in
firmware. Write the offset first in the pass. Worst case is one 250 µs pass where
offset and signal disagree — a click, once, after an event that only happens when
something else has already gone wrong.

### B5. Per-strip fusing of the LED feeds (B10 #22)

**Proposed:** a 500 mA fuse on each WS2815 strip feed.

**Decline.** Two more parts inside the bonded body, both of which can nuisance-
trip, protecting a load whose documented dominant failure mode is *open*, on a
rail already behind the module's limiter, on a subsystem the design describes as
decoration.

**Consequence of declining:** a shorted strip pulls on the umbilical feed until
the module-side limiter acts. Which is the limiter's job, and is why the design
put it at the module end where it can be resized.

### B6. A readback-capable DAC (D4 #6)

**Proposed:** choose an octal DAC with readback so the module can be verified.

**Decline.** The DAC grade analysis — A/C reset to zero scale, the grade letter
setting the reference gain — is called by ADR 0006 "the whole decision." Swapping
the part to recover readback reopens that, and readback still cannot reach the
instrument because MISO was deleted and the umbilical is full.

**Consequence of declining:** the module stays open-loop, permanently. The
proportionate 90 % is the LINK LED off the watchdog state (3 parts, module side)
plus the written diagnostic signatures — which B10 is right to call worth more
than most of the parts it proposes.

### B7. Current-sense and per-section power provisions on the carrier (D2 #14, #15)

**Proposed:** make every rail current-measurable and every section independently
powerable, so a fault can be bisected.

**Decline the shunts and the section switches.** This is production DFT on a
board that will be assembled once, by the person who designed it, with a bench.

**Consequence of declining:** to measure a rail you lift a lead or clamp a
current probe on the umbilical — which ROADMAP E6 already schedules with a
current probe, on switch-on *and* hot-plug. The proportionate residue is two
**0 Ω links** in series with the two largest rails: zero cost, zero new failure
modes, and a place to break the circuit for a meter. Fit those, decline the rest.

### B8. The B10 fix block as a block

B10 offers "roughly 60 passive parts and 10 actives" as one set. Taken as a set
this roughly doubles the passive count on two hand-soldered boards and makes both
harder to debug — which matters, because the debugging is done by the same person
under the same deadline.

**Decline the block; take it item by item.** Inside it, five items are on my keep
list (pull-ups, moving the '125 to the LM317 rail, clamps inboard of the 1 kΩ,
`R-OUT-PROT` to 1206, LINK LED). The others should be individually justified or
dropped. In particular decline: pull-ups on the 14 spare bits (tie them at the
package), the per-strip fuses (B5 above), and the second TVS array at the module
end (A1's reasoning: the module is serviceable).

---

## C. True, and inaudible / invisible / immaterial

### C1. The remaining ground-path pitch terms (B7 F1, B7 F4)

**Finding:** the rack's shared bus ground contributes ~4.8 cents of
breath-correlated pitch error; the module's internal ground 5.7–7.2 cents.

**Adopt the free half, decline the rest.** The module's internal term is fixed by
a layout discipline that costs nothing: a star return and a Kelvin sense from the
pitch stage to the pitch jack's sleeve. Do that at layout.

**Decline the rack-bus term.** Fixing it needs a dedicated return conductor the
umbilical does not have, or moving 300–430 mA of instrument return off the shared
bus ground — which is the connector decision again.

**Consequence of declining:** roughly 5 cents of pitch movement correlated with
playing intensity, at the extremes of the LED and load swing. Once W3 (22 cents)
and W4 (20 cents) are fixed — items 6 on the keep list — this residual sits
inside what the trimmer (2.4 cents) and the driven VCO (3.5 cents) do on their
own over an ordinary temperature swing. It is an informed accept, and the number
should be written into ADR 0004 so it is not rediscovered.

### C2. The 10 µF per satellite shift-register board (C2 F17)

**Finding:** 100 nF alone resonates with ~350 nH of loom at 851 kHz, inside the
key-chain's SPI band.

**Decline — as a duplicate of item 1.** The computed rail disturbance from a QH
edge is **1.65 µV**. The resonance concern is about coupling into key inputs, and
once every key input carries a 10 nF to ground behind a 10 kΩ pull-up (keep-list
item 1), an 851 kHz disturbance is attenuated at the input by roughly 54 dB. The
fix and the finding address the same failure; buying both is paying twice.

**Consequence of declining:** four fewer capacitors inside the body. If E4's
error counter shows chain errors, the counter is the diagnostic the design
already built for exactly this, and the body is still open at that point.

### C3. `R-OUT-PROT` tolerance and tempco (C2 F5, second half)

The finding computes **0.083 cents over 10 °C** for ordinary 1 % thick film with
±100 ppm/°C, and correctly concludes "keep the value, keep 1 %." Worth naming as
the model of a finding that quantified itself out of existence — and as the
standard the rest of the register should have been held to.

(The package change 0805 → 1206 is free and should be taken; 141 mW in a 125 mW
part during a sustained short is a real derating and the footprint costs nothing.)

### C4. The body-capacitance rationale for the plate bond (B7 F10)

The ADR's stated reason computes to **41 nanovolts** against a 153 µV LSB —
wrong by six decades. **Adopt the one-paragraph rewrite** (the real reason is
ESD return) and the routing note (bond short, to the nearest cluster board, not a
400 mm flying lead to the carrier). **Decline the ESD-gun test programme** at
±8 kV contact discharge with counted trials at two bond lengths.

**Consequence of declining:** you take the routing note on physics rather than on
measurement. The routing note is free and the measurement changes nothing about
what you would do.

### C5. `±10 V is not reachable` (B4 #9)

The mod range is bounded to about ±9.8 V by the DAC's inability to reach its own
rails, not by the op-amp headroom the ADR checked.

**Decline any change.** ADR 0006 says it in its own words: *"nobody's ear cares
whether a modulation CV is 2 % off."* Write the real number in the ADR; change no
circuit.

**Consequence of declining:** a mod channel labelled ±10 V spans ±9.8 V.

### C6. The reasoning-defect findings (B4 #11, B4 #12, B9 #12, parts of B7 F10)

"Step size is bounded by slew rate" is the wrong mechanism for a correct
conclusion. "The DAC's full-scale output is its supply" is imprecise — full scale
is 2 × the internal 2.5 V reference and merely coincides with a 5 V rail.

**These are prose, and they are right.** Decline them **as tracked changes**:
they are one editing pass, not three work items, and each is a single sentence.
Naming them as findings in a register of a hundred changes is how a
half-hour of editing becomes three review cycles.

**Consequence of declining (as changes):** nothing, provided they land in the
single editing pass described in D2 below.

---

## D. Process and documentation findings that generate work without reducing risk

### D1. A2's 38 staleness items and A3's convention items, individually tracked

A2 finds 38 pieces of documentation drift. A3 adds the status-vocabulary
violation on the `BENCH` row, `BENCH` not being a bill-of-materials item at all,
the phantom `U-IMU` line, `R-MOSI-SER`'s category field, and ten rows carrying
`candidate` for parts an Accepted ADR names outright.

**Decline all of these as individually tracked changes.** A2's own pattern
section says most of the 38 come from **three** reversals — the sensor and board
moving to the tail, breath going single-ended, and the mod rate going 2 → 4 kHz —
plus the ADR 0013 zone table. That is four edits with a grep, not thirty-eight
decisions.

**Consequence of declining:** the register's count drops by roughly forty and
nothing gets worse, *provided* one editing pass happens: for each of the three
reversals, grep every document for the superseded claim and fix all of them at
once. The failure mode the register is guarding against is a stale sentence
getting built — and the specific ones that could get built (the INA134 in ADR
0004's parts list, the single-leg pulldown in ADR 0005, the "74HC165" in seven
places, the zone table) belong in the *keep* column and are worth naming
individually. The other ~34 are not.

### D2. D2 #27 and #28 — "no milestone owns the testability provisions"

**Decline.** This is a finding about the shape of a project-tracking artefact.
Adding a testability owner to each milestone, and adding "prove the testability
provisions" to M8's checklist, produces a checklist that is longer without
producing a test that is better.

**Consequence of declining:** the service header (keep-list item 2) has to land
in M4's CAD by someone remembering. Write it in ROADMAP M4's row as a *thing*
("service connector at the tail") rather than as a *process*.

### D3. The D4 detector suite, as nineteen items

**Decline twelve of nineteen as scheduled work:** #8 (sensor degrades over
months), #9 (restrictor clogs), #11 (stale gyro bias), #12 (channel saturates),
#15 (invisible brownout resets), #16 (config acknowledged not persisted), #17
(note-gate chatter), #18 (watchdog margin), #7 (frozen display board), #10's
absolute thresholds and alarm colours, #14 as a lifetime instrument, #19 (already
accepted by its own author).

These are a condition-monitoring product for a fleet. The user is one person who
is standing next to the instrument, has a full bench, and will have F6's live
telemetry on a phone showing breath, IMU angles and commanded CV — which the
ROADMAP already pulls forward as a test instrument.

**Adopt five:** #1 (commissioning fingerprint — the enabler), #2 (per-load
calibration, = W2), #3 (auto-zero gating, = W11), #4 (intermittent key), #13
(press a key, light its matrix pixel — the only wiring-error check that works
with the body open, and free).

**Consequence of declining:** slow degradations go unattributed for longer. Each
of the twelve is a few lines of firmware that can be added *at any time in the
instrument's life*, because they are firmware — which is exactly why they should
not compete for attention against things that bond shut at M8. That ordering is
the whole point.

### D4. "Walk the BOM against the ADRs, line by line, with a checklist" (B10)

**Adopt this one, and decline everything it duplicates.** B10 is right that this
is an afternoon and that it will find more than the review did. It also
*subsumes* most of A3's 38 findings and M4's "34 further line items." Running the
pass and separately tracking the 38 findings it would find is doing the work
twice.

---

## E. Duplicates that would be triple-counted

The register presents these as independent convergence ("five agents found it").
Convergence is evidence that the finding is *true*. It is not evidence that there
are five changes to make. Counted as changes:

| One change | Appears as |
|---|---|
| `C-AA-ADC` 220 nF → 47 nF | W1, B1 #1, B6 #8, B8 #2, C1 F9, C2 F1 — **six** |
| Two 1 MΩ bias-return resistors | S3, B2 #1, B7 F3, B8 #1, B9 #2, C2 F3, D1 #1, D3 #4 — **eight** |
| Make the ambient zero subtract | S2, B1 #4, B2 #2, B9 #1, C1 F8, D3 #1 — **six** |
| Umbilical SPI ≥ 2 MHz in ADR 0004 + E11 | W5, A1 #4, B4 #5, B8 #5, C5 F3 — **five** |
| Delete / resize `F-POLY` | S7, B5 #2, B6 #2, B6 #3, C1 F19, C2 F6, C3 #16 — **seven** |
| Replace `U-LOADSW` | S1, B5 #1, B6 #1, C1 F1, D1 #6 — **five** |
| `R-OPAMP-IN` qty 5 → 7 | B9 #9, C2 F21, A3 F21 — **three** |
| Shield bonded at both ends (one sentence) | B2 #10, B7 F8, D1 #15, D3 #15 — **four** |
| Split the umbilical TVS by voltage | S6, C1 F2, C2 F18, D1 #9, B6 #11 — **five** |
| LM317 tolerance | S5, C1 F3, C2 F4, B5 #5 — **four** |

**Fifty-three register entries; ten changes.** Any plan built by counting
findings rather than counting changes will be about five times larger than the
work actually is — and will, more damagingly, spend its attention proportional to
how many agents happened to be pointed at the same subsystem.

---

## F. One downgrade worth stating separately

### S5 — the LM317 tolerance stack

The arithmetic is right: 4.964–5.622 V against a 4.95–5.50 V window, and no
nominal value fits. The proposed fixes are a 0.1 % divider, an LP2951, or a
second REF5050 buffered by half an OPA2197.

**Downgrade it from a showstopper to a bench task.** This is a *one-off*. The
worst case is a statistical statement about a population of one. The author has
a full bench, a TO-92 regulator with two through-hole resistors, and a voltmeter.
Build it, measure it, and select R2 — which is exactly what you would do anyway.

**Decline the LP2951 and the second REF5050.** Adopt the free part of the fix:
**shrink R2** so the I_ADJ term stops contributing, and buy a handful of 0.1 %
parts for the divider (pennies, and they arrive in the same order).

**Consequence:** the module's DAC rail is set by measurement on the bench rather
than guaranteed by tolerance analysis. For one unit, that is strictly better
information. If the selected value lands outside the window, you find out at E7
with a meter, on a board with four screws in it.

---

# Part 3 — Where the review got it backwards

Places where it declined, worked around, or under-weighted something it should
have adopted.

### 1. 6HP is the constraint, and nobody questioned it

Three MAJOR electromechanical findings and one showstopper-adjacent one exist
*only* because the module is 6HP:

- **C3 #3 / W9:** "brace it to the PCB" is not buildable as one board — clearing
  the etherCON body needs a ~26 mm notch in a ≤28 mm board, which severs it. The
  recommendation is **a two-board module**.
- **C3 #4:** two knobs across 30.18 mm forces **D ≤ 13 mm**, which excludes
  essentially every knob a Eurorack builder owns (Rogan 1PS 15.8, Davies 1900H
  14.3, Alpha KM-16 16 mm).
- **C3 #9:** the tail and panel are over-subscribed in depth.
- **W9 / C3 #2:** the flange-versus-panel margin is 2.09 mm, not the 3.19 mm the
  ADR computed from the bore.

**8HP is 40.34 mm.** It costs **2 HP in a rack the README explicitly describes as
generous**, and:

- two pots on 20 mm centres allow a **20 mm knob** — the constraint disappears
  entirely rather than being met with a specified 12 mm part;
- the 26 mm etherCON flange leaves 7.2 mm of panel each side instead of 2.1 mm,
  and the screw positions stop being the thing the design hangs on;
- a 26 mm notch in a ~38 mm board leaves 12 mm of web, which makes the
  single-board module plausible again and **deletes the two-board redesign**;
- the panel is laser-cut from a DXF, so a wider panel costs the same money;
- a bigger board is *easier* to hand-assemble and hand-debug, which is the
  dominant build constraint in this project.

Combine it with C3 #4's own free recommendation — **move the umbilical connector
to the bottom of the panel**, so the cable hangs away from the controls instead
of draping across both knobs and all six jacks — and the vertical overrun closes
too.

Twenty-three agents optimised inside a constraint that costs 2 HP to relax. That
is the single best trade in the register and it is not in it.

### 2. S1's replacement is more protection than the job needs

The proposal on the table is **LT1641-2CS8 + N-FET + sense resistor**, latch-off,
with an ILIM network — a hot-swap controller, five-plus parts, a latched state,
and a new failure mode (latched off, instrument dead, no indication). And S7
shows the current-limit approach **may prevent boot**: constant-current charging
1–2.7 mF of strip bulk at 500 mA takes 22–65 ms, during which the buck never
reaches its 8 V UVLO.

**The actual requirements are two:** ramp the inrush so the toggle and the rack
rail are not slammed, and stop a crushed cable burning. Both are met by a
**P-FET with an RC gate ramp plus a 1.5–2 A fuse**: three parts, no latch, no
ILIM resistor to get wrong, no auto-retry oscillation (the failure ADR 0014
analyses), no possibility of failing to start the load, and it is on the
serviceable side of the system.

The review responded to a protection part being wrong by specifying a more
capable protection part. The proportionate response to "the protection part does
not survive the rail" is to ask whether the protection needs to be that clever.

### 3. W2's free half is buried under its own correction

The register's W2 entry leads with "the reasoning does not survive" and ends with
the resolution. The resolution — **store an affine `(gain, offset)` per load
preset** — is free firmware that removes a flat 29–59 cents of detuning, which is
the largest audible error in the register that costs nothing to fix. It should
have been a headline finding, not the last paragraph of a correction. It is item
7 on my keep list.

### 4. `J-USB` marked `not-needed` (C3 #10)

C3 calls this "the part most likely to end the project" and the register does not
carry it forward. It is right. The tail USB-C is the *only* opening in the body,
C5 F1 makes it the recovery path, and a BOM row that says `not-needed` is how a
part stops being thought about. The status is wrong even though the conclusion
("the dev boards carry these") is right — the *slot* and its alignment are the
deliverable, not the receptacle.

### 5. The MCP3202's spare channel has three claimants and no owner

D2 #22, D4 #6/#14/#15 and C1 F10 each propose a different use for the one spare
precision analog input: a 5.000 V reference monitor, an umbilical +12 V sense, a
temperature channel. The review never resolves it, and D2 #17 correctly notes the
same pattern on the two spare GPIO — *"the decision is currently being made by
whoever gets there first."*

**Resolve it now, before the carrier:** a two-resistor divider from **umbilical
+12 V**. It is the only claimant that detects a failure nothing else can see
(cable intermittency, brownout, the module's load switch having tripped), it is
two passives, and it is entombed if it is not done before E13. The reference
monitor is checkable on the bench; the temperature is free from the IMU.

### 6. W6's conclusion is more alarming than its arithmetic

W6 re-sums the note-onset path at **4.1–4.7 ms against a 5 ms target** and
concludes ADR 0003's "roughly 10× margin" is about 1.1×. The re-sum is right and
the "10×" claim should go.

But **1.3 ms of that is keep-list item 4 — a single capacitor value.** Fix W1 and
the path is ~3.1–3.4 ms, against a physical gesture (a hard tongue attack) that
rises in 5–15 ms. **Decline any further latency work.** Correct the budget
document, take the 47 nF, and stop; the remaining two largest terms are the tube
and the transducer, both physical, both already deliberate trades.

### 7. Two accepts the review got exactly right, said so it is clear I checked

- **D1 #19 — the umbilical plugged into a real Ethernet port.** A passive PoE
  injector would put ±48 V into the SPI pins and kill both boards. The review
  declines the circuit and takes the labelling. Correct: series protection rated
  for 48 V on four signal lines costs far more than the failure for a one-off,
  and the failure requires a specific piece of equipment in a specific room.
- **D4 #19 — the WS2815 backup data line hides accumulating dead LEDs.** It is
  silent *on purpose*, and the purpose is good. Boot sweep, no alarm. Correct.

These two are the shape the rest of the register should have had.

---

## Summary

| | Count |
|---|---|
| Register entries | ~250 |
| Distinct changes after collapsing duplicates | ~90 |
| Changes I would make | **10 + 6 near-misses** |
| Changes I would decline with stated consequence | ~35 named here, standing in for ~60 register entries |
| Changes that are one editing pass, not changes | ~45 (A2, A3 conventions, prose corrections) |
| Things the review got backwards | 6 |

The register is worth having. Its three showstoppers are real, its dynamic pitch
finding (W4) is the best work in it, and the key-switch pull-up gap is the kind of
hole that ruins an instrument quietly for years. But it counts findings, not
changes, and it prices every fix as though the instrument were a product with
customers, a warranty and a second unit. It has none of those. It has one player,
who has built one of these before, who owns a full bench, and who will be standing
beside it.

**The things worth money here are the things that bond shut.** Everything else
can wait until it actually misbehaves — which, for a one-off, is a legitimate
design strategy and not an oversight.
