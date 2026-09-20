# B10 — Fault and abuse review

**Woody**, independent analog design review, failure/abuse scope.
Sources read: `README.md`, `ROADMAP.md`, `docs/decisions/0001`–`0014`,
`docs/reference/ks33-geometry.md`, `docs/reference/latency-budget.md`,
`hardware/bom.csv`, `config/key-layout.yaml`, `firmware/README.md`.
Not read, by instruction: `docs/review/`, `docs/log/`.

No repository file was modified.

## How to read this

Every figure is marked **[repo]** (read out of the documents above, quoted back
at them), **[memory]** (a datasheet or standards figure I am working from
recall and have *not* verified against a datasheet in this session — treat as a
hypothesis to check, not as a number to design from), or **[derived]**
(arithmetic on the other two, shown inline).

Severity is calibrated to *this* project: one-off, hand-assembled, sealed body,
generous rack, full bench. "SHOWSTOPPER" means the design as written either
destroys itself or becomes unrecoverable inside a bonded body. It does not mean
"a product would fail certification".

Section 4 is the proportionality call: what is worth fixing and what is worth
signing off as accepted risk.

---

## 1. Where the design already gets this right

Stated explicitly, because a fault review that only lists gaps misrepresents
the design. These are not padding — each one is a failure mode that this
project has already closed, and several are closed better than the Eurorack
norm.

- **Reverse ribbon.** Shrouded keyed 16-pin header plus series 1N5817 on both
  ±12 V rails. On a 180° reversal both diodes are reverse-biased at ~12 V
  against a 20 V rating **[memory]** and the module is simply dark. This is the
  correct answer and it is the classic Eurorack kill. (The residual is the
  +5 V pin — finding 2 — and the *offset* case, finding 5.)
- **The breath buffer on +12 V.** Putting the instrument's OPA2197 buffer on
  the same rail as the highest voltage the umbilical carries means a sustained
  +12 V fault on `BREATH` is *at* the rail, not above it, so no clamp conducts.
  The op-amp sinks a few mA at ~0.2 V, dissipating ~2 mW **[derived]**. This is
  the single best piece of fault reasoning in the document set: it dissolved a
  conflict rather than trading one side off against the other.
- **Differential 100 kΩ pulldown across `BREATH`–`AGND`.** Instrument off or
  unplugged ⇒ 0 V differential ⇒ breath CV sits at the in-amp's `REF`, not at a
  floating buffer output. Right answer, right topology (differential, not
  single-leg).
- **DAC grade chosen so that every channel's power-on state is simultaneously
  correct.** Taking the mod offset from a DAC channel rather than a fixed 2.5 V
  makes `4 × (0 − 0) = 0 V` on an A/C-grade zero-scale reset, while the same
  reset parks pitch below −2 V. That is an elegant, deliberate, free result and
  it is why rack power-on and brown-out recovery are quiet (finding 17).
- **The load switch is at the module, not the instrument.** So the current
  limit holds regardless of what the instrument's MCU is doing — including
  nothing. ADR 0014's analysis of the polyfuse thermal-runaway loop is correct
  and the conclusion drawn from it is correct.
- **The frame watchdog.** "A stuck CV drones the rack forever and nothing
  notices" is the right thing to have noticed, and a retriggerable monostable
  asserting `CLR` at the *module* end — independent of the thing that hung — is
  the right shape of answer.
- **WS2815 backup data line** in a body that cannot be opened. A single dead
  LED is one dark pixel, not a dead run. Correct part choice for the
  constraint.
- **Key layout and fingering table as data in NVS.** Nobody has written this
  down as a fault mitigation, but it is the *only* recovery available for a
  dead key switch in a bonded body: re-author the fingering table around it.
  See finding 22.
- **Blank-at-boot for strips and matrix**, closing the latched-colour hole a
  brown-out opens.
- **Marker pattern on the key chain**, converting an invisible intermittent
  into a counter.
- **Supply headroom is comfortable.** 12 V − 0.4 V (1N5817 @ 300 mA
  **[memory]**) − ~0.06 V ferrite − ~0.05 V TPS2553 R_on **[memory]** − 0.35 V
  cable (26 AWG @ 0.65 A, finding 15) = **11.1 V** at the instrument
  **[derived]**, against a buck needing >6 V **[repo]** and a REF5050 needing
  ≥7 V **[repo]**. Nothing is tight.
- **M8 as a pre-bond gate with failure injection.** The single most valuable
  structural decision in the roadmap for everything below.

---

## 2. Findings

### 2.1 Rack power entry and the module's rails

---

**1. Both current limits guarding the umbilical are set below the
instrument's own documented worst-case draw, and the one inside the sealed
body is the one that cannot be replaced.**

**Severity: SHOWSTOPPER**

*Failure case:* normal playing with the lighting near its own 3 W clamp.

*What actually happens.* Build the instrument's +12 V draw from the project's
own numbers:

| Term | Figure | Source | At +12 V |
|---|---|---|---|
| Two dev boards | 330–400 mA @ 5 V | **[repo]** ADR 0014 | 400 mA × 5 / (12 × 0.85) = **196 mA** |
| WS2815 quiescent, both runs | ~120 mA @ 12 V | **[repo]** ADR 0005 | **120 mA** |
| Matrix idle drivers | ~50 mA @ 5 V | **[repo]** ADR 0007 (estimate) | **25 mA** |
| Sensor, REF5050, OPA2197 | ~15 mA | **[derived]** | **15 mA** |
| **Idle subtotal** | | | **356 mA** |
| Lighting at the 3 W clamp | 3 W **[repo]** ADR 0014 | 3/12 direct, 3/(12×0.85) via buck | **250–294 mA** |
| **Normal worst case** | | | **606–650 mA** |

(Buck efficiency 85 % **[memory]**; everything else **[repo]**.)

Against that:

- `U-LOADSW` TPS2553: *"Adjustable limit set ~500 mA"* **[repo]**. Typical
  programmed-limit accuracy for this family is ±15–20 % at the low end
  **[memory]**, so a nominal 500 mA can land at ~425 mA. It will current-limit
  during ordinary playing.
- `F-POLY`: *"PPTC 1206 500 mA hold"* **[repo]**, mounted at the umbilical
  entry **inside the bonded body**. A PPTC's hold current derates with ambient;
  at the documented 10–20 K interior rise **[repo]** the effective hold is
  roughly 0.8 × nominal = ~400 mA **[memory]**. It is below the *idle* figure
  with almost no margin and comfortably below the playing figure.

**Which part fails first:** `F-POLY`. It does not blow cleanly — it enters its
gradual current-limiting region, its resistance rises, the rail at the buck
sags, the buck compensates by drawing *more* input current, and the device
heats further. That is exactly the positive-feedback loop ADR 0014 identified
and declared solved by the load switch — but the load switch is 2 m upstream
and does not remove a series thermal element inside the instrument. The
observable symptom is the thing this project has spent the most effort trying
to avoid: intermittent brown-outs blamed on firmware, inside a box that cannot
be opened.

*Proposal.* **Delete `F-POLY`.** ADR 0014 says the load switch *"replaces a
slow, self-heating, thermally-hysteretic protection device"* **[repo]** — the
BOM simply never carried out that deletion. Its stated job ("a short inside the
instrument pulls on the rack's +12 V rail") is the load switch's job, done
faster, without self-heating and without thermal hysteresis, and from a
location you can reach. If a belt-and-braces device inside the body is still
wanted, it must be a **1.5–2 A hold** part, i.e. sized above the clamped
worst case with derating, not above the idle case.
Separately, **set the TPS2553 limit around 1.2–1.5 A** (within its programmable
range — verify **[memory]**) once E6 has measured the real draw. E6 already
exists for this; what is missing is the statement that the limit must clear the
*clamped* worst case, not the idle case, and that the 3 W lighting clamp and
the load-switch limit are two limits on the same current that nobody has
reconciled.

Note the coupling that finding 19 depends on: raising the load-switch limit to
make the instrument work simultaneously raises the energy available to a
shorted LED inside the body. That is an argument for putting a limit *per
branch*, not for keeping a limit that is too low globally.

*Confidence:* **High** on the arithmetic (every input is the project's own
figure). Medium on the PPTC derating factor and the TPS2553 tolerance, which
are **[memory]**.

*Falsifying test:* E6 with a current probe, running the lighting up to the 3 W
clamp with both strips and a full-field matrix, logging umbilical +12 V current
and the voltage at the instrument end for 30 minutes at the M8 soak
temperature. If the total stays under ~400 mA the finding is wrong.

---

**2. The unprotected bus +5 V entry does not fail the way ADR 0004 claims: a
dead 74AHCT125 can put up to 12 V on the DAC's digital inputs.**

**Severity: MAJOR**

*Failure case:* anything that puts an over-voltage on the module's bus +5 V
pin — a reversed ribbon on a bus board whose CV/Gate lines are driven, a
mis-wired bus board, a bench supply during bring-up.

*What actually happens.* ADR 0004 reasons: *"A reversed or row-offset ribbon
that puts +12 V onto that pin kills the buffer and nothing else, which is why
the +5 V entry gets no protection network of its own."* **[repo]**

Two problems.

*(a) The consequence is understated.* A 74AHCT125's absolute maximum V_CC is
7 V **[memory]**. Above that it does not politely die — it operates, hot, with
its output PMOS pulling to whatever V_CC now is. Its three outputs go to the
DAC8568's `SYNC`, `SCLK` and `DIN`, whose absolute maximum is AVDD + 0.3 V =
5.55 V **[memory]** with AVDD = 5.25 V from the LM317 **[repo]**. The series
impedance between them is the buffer's R_on (tens of ohms) and a PCB trace.
12 V through a DAC input clamp into a 5.25 V rail that an LM317 cannot sink:
the rail is dragged toward ~11.4 V and the DAC — the most expensive part on the
board and the one carrying the calibrated pitch channel — dies with the buffer.
"Kills the buffer and nothing else" is wrong.

*(b) The scenario cited cannot occur with the specified connector.* Getting
+12 V onto the +5 V pin of a 16-pin Eurorack header requires a four-position
shift, which a 16-pin cable on a 16-pin header cannot produce. Under a genuine
180° reversal the +5 V pin receives whatever sits in the mirrored middle
pair — the **CV/Gate** lines **[memory, on the Doepfer bus ordering]**. Many
cases leave those floating; a case with a MIDI-to-CV bus driver puts up to
+10 V there, which is over the 7 V maximum and reproduces (a) anyway. So the
ADR reaches a survivable-sounding conclusion from a scenario that does not
happen, while the scenario that does happen is worse than stated.

*Proposal.* **Move the 74AHCT125 to the LM317's 5.25 V rail and delete the
module's dependence on the rack's +5 V bus entirely.** ADR 0004's objection to
this is that it would put the buffer's switching current on the DAC's supply.
Check it: three lines at ~0.6 MHz **[repo]** into ~30 pF each gives
I = C·V·f·n = 30 pF × 5.25 V × 0.6 MHz × 3 = **0.28 mA** average **[derived]**,
against 100 nF of local decoupling. The objection does not survive arithmetic.
What the move buys:

- the module has one low-voltage rail instead of two, and no unprotected pin;
- AHCT at 5.25 V still has TTL thresholds (V_IH = 2.0 V **[memory]**), so 3.3 V
  from the instrument still reads high;
- output high becomes 5.25 V driving a 0.7 × AVDD = 3.68 V threshold **[repo]**
  — better margin than the 4.6 V-from-a-sagging-bus case the ADR computes;
- the "+5 V is a requirement, not an option" constraint in ADR 0005 disappears,
  and with it a whole class of rack-dependency;
- finding 3 disappears;
- the sequencing hazard in finding 16(c) disappears.

LM317L load becomes ~15 mA: dissipation (11.6 − 5.25) × 15 mA = **95 mW**
**[derived]** in a TO-92, ~17 K rise at θ_JA ≈ 180 K/W **[memory]**. Fine. The
240R/768R divider already supplies 1.25/240 = **5.2 mA** **[derived]**, above
the LM317L's minimum-load requirement **[memory]**.

If the bus rail is kept anyway, the minimum is a 5.6 V TVS or 5.1 V zener plus
a small series element at the buffer's V_CC — two parts.

*Confidence:* **High** that the "kills the buffer and nothing else" claim is
wrong. **Medium** on the Doepfer middle-pair ordering, which is **[memory]** —
but the conclusion does not depend on it, because case (a) holds for any
over-voltage source.

*Falsifying test:* on the bench, power a 74AHCT125 from 12 V with its inputs
driven and a DAC8568 (or a 5 V CMOS load with a 5.25 V rail) on its outputs.
Measure the output voltage and the current into the 5.25 V rail during the
first seconds. If the buffer fails open-output rather than high, the finding is
wrong.

---

**3. The `CS` idle pull-up is referenced to the same bus +5 V rail whose loss
it exists to survive.**

**Severity: MINOR** (dissolved by finding 2's proposal)

*Failure case:* a case with no +5 V bus rail wired, or a broken +5 V conductor
in the ribbon.

*What happens.* `R-SPI-PULL` is *"CS to +5 V, SCLK and MOSI to ground"*
**[repo]**. With +5 V absent, the pull-up is a 10 kΩ resistor to 0 V, so `CS`
is pulled *low* — the opposite of the intended idle — and the buffer is
unpowered anyway, so this is a state where the deliberate defence against
floating CMOS is itself defeated. Nothing is damaged (the DAC's `CLR` is held
asserted by the watchdog because there is no traffic — see finding 6), but the
defence does not do what it was designed to do in the one fault it was designed
for.

*Proposal.* Reference the `CS` pull-up to the same rail that powers the buffer.
With finding 2 applied that is the LM317's 5.25 V and this stops being a
separate item.

*Confidence:* **High** (it follows directly from the quoted BOM line).

*Falsifying test:* in the schematic review, confirm which net the `CS` pull-up
returns to. If it is already the regulated rail, the finding is wrong and the
BOM note is just loose.

---

**4. "Gate the 74AHCT125's OE from umbilical +12 V presence" requires an
inversion that nothing in the BOM provides, and the naive version enables the
buffer in exactly the state the gating exists for.**

**Severity: MAJOR** (as a schematic trap; cheap to close)

*Failure case:* instrument off or unplugged — which ADR 0004 correctly calls
the module's *normal* state, not a fault.

*What happens.* A `'125`'s output-enable is **active low** **[memory]**. The
obvious implementation of "gate OE from umbilical +12 V presence" is a divider
from the umbilical +12 V node to the OE pin. With +12 V present, OE is pulled
*high* — outputs **disabled**. With +12 V absent, OE falls to 0 V — outputs
**enabled**. That is exactly backwards, and the failure is silent: the module
works perfectly whenever the instrument is on, and the gating does nothing in
the only state it exists for. The two spare gates in the SOIC-14 are buffers,
not inverters, so the package cannot supply the inversion itself.

There is a second, load-bearing consequence the ADR does not claim but the
design depends on: this same gating is what protects the DAC when bus +5 V is
present and +12 V is not (finding 16(e)). With the polarity wrong, that
protection is also inverted.

*Proposal.* One NPN (or small N-FET) with its base/gate from a divider off the
umbilical +12 V node, collector to OE with a 10 kΩ pull-up to the buffer's
V_CC, emitter to ground: presence ⇒ OE low ⇒ enabled; absence ⇒ OE pulled high
⇒ disabled. Three parts. Add pull resistors on the **DAC side** of the buffer
as well — `SYNC` to AVDD, `SCLK` and `DIN` to ground, 10 kΩ each — because with
OE deasserted the DAC's inputs are currently left floating. The existing
`R-SPI-PULL` trio sits on the buffer's *input* side and does not cover this.
(The watchdog's held `CLR` means a garbage write cannot reach the outputs, so
this is a crowbar-current and robustness issue rather than a loud one — see
finding 6.)

*Confidence:* **High** on the active-low polarity of a `'125` OE. **Medium** on
whether the schematic will actually be drawn naively — this is a warning about
an undrawn schematic, not a defect found in one.

*Falsifying test:* measure the DAC's `SYNC`/`SCLK`/`DIN` pins with a scope and
the umbilical unplugged. Floating or oscillating ⇒ finding stands. Held at
their pull levels ⇒ already handled.

---

**5. A reversed ribbon is handled; a row-offset ribbon is not, and its worst
version is a rail-to-chassis short through the panel hardware rather than an
IC failure.**

**Severity: MINOR** (mostly prevented by the connector choice already made)

*Failure case:* the module's 16-pin cable plugged one position off at the *bus
board* end, on a bus board with an unshrouded header.

*What happens.* At the module the header is shrouded and keyed **[repo]**, so
an offset cannot occur there. At the bus-board end it can. Shifting by one
position in the direction that pushes the module's pin 1–2 off the end maps the
module's **ground pins onto the bus's −12 V rail** **[memory, on the Doepfer
ordering]**. Both series 1N5817s then block correctly and no module IC sees an
over-voltage — but the module's ground net is now being driven to −12 V, and
the module's ground net is also connected to its front panel through six
PJ398SM jack bushings **[memory: the threaded bushing of a Thonkiconn *is* the
sleeve/ground contact]**, and the panel is bolted to the rack rails.

If the rails are bare aluminium and the case chassis is bonded to bus ground —
common — that is a **dead short from the −12 V rail to ground through the
module's panel bolts and jack nuts**. The current is bounded only by the rack
supply, which the README explicitly describes as generous, and *"fault current,
which a larger supply makes worse, not better"* **[repo]** is precisely the
case. The path runs through four 28 AWG ribbon ground conductors (~1 A each
**[memory]**) into the panel hardware; the ribbon or the PSU's protection is
what gives. Nothing on the module can defend against its own ground pin being
driven — series protection on grounds is not done in Eurorack and should not be
started here.

If the rails are anodized (insulating) or nylon-washered, no short exists and
the module is merely dead. **Which of those is true is unknown and is not
written down anywhere in this project.**

*Proposal.* **Accept the electrical risk; close the informational gap.** Draw
the bond diagram once: key plate → `PWR_GND` → umbilical → module ground →
jack bushings → panel → rack rails → chassis → PSU earth, and mark which of
those bonds actually exist in the target case. It costs an afternoon with a
multimeter on a rack that already exists, it settles this finding, findings 13
and 14, and the mains question in finding 24, and it is the kind of thing that
is free now and impossible to reconstruct later.

*Confidence:* **Medium.** The Doepfer pin ordering and the panel-bond topology
are both **[memory]**, and whether the case bonds the rails is unknown. The
*shape* of the conclusion — that the damaging offset case is a rail-to-chassis
short, not an IC over-voltage — is robust to those details.

*Falsifying test:* continuity check, power off: module ground to rack rail, and
rack rail to bus ground. Two beeps ⇒ the path exists. No beep at either ⇒
finding is moot.

---

**6. The frame watchdog's supply rail and its `CLR` polarity are both
unspecified, and the wrong choice of either turns it from a safety device into
a click generator or a no-op.**

**Severity: MINOR**

*Failure case:* (a) bus +5 V lost while +12 V is present; (b) electrical noise
on the monostable's trigger mid-note.

*What happens.*

*(a) Supply.* `U-WATCHDOG` is a 74HC123 **[repo]** with no rail specified. If
it is powered from bus +5 V and the DAC from the LM317's 5.25 V, then losing
bus +5 V leaves the DAC alive and the watchdog dead — its `CLR` output floats,
the DAC is never cleared, and a stuck CV drones exactly as ADR 0004 describes,
in a fault case the watchdog was bought to cover. Power it from the DAC's own
5.25 V so "DAC alive" implies "watchdog alive". Consequence: its trigger input
must come from the *buffered* (5 V logic) side, because 3.3 V from the
umbilical does not meet an HC part's V_IH = 0.7 × 5.25 = **3.68 V**
**[derived]**.

*(b) Polarity.* Wire it so that **being retriggered is the not-cleared state**
and the timeout asserts `CLR`. In that polarity a noise-induced spurious
trigger can only *postpone* `CLR` — harmless. In the opposite polarity a
spurious trigger drops the DAC to zero scale for the monostable's pulse width:
every mod channel to 0 V and pitch to −2.5 V, mid-note. 74HC123s are
well known for being sensitive to trigger and supply noise **[memory]**, and
this one lives in a module carrying a switching load's current.

*(c) Timing.* Frames arrive every 250 µs **[repo]**. N = 5–20 ms gives 20–80×
margin against a busy loop and still catches a hang well inside a second, as
ADR 0004 asks.

*(d) A residual the ADR overstates.* "This also gives umbilical disconnection
the same behaviour as a hang" is true, but the watchdog catches *stopped*
traffic, not *wrong* traffic. It cannot detect an MCU that has hung with a DMA
still cycling, nor a chattering `CS` on an intermittent cable, either of which
retriggers it forever. See finding 18.

*Proposal.* Specify the rail (DAC's 5.25 V), the polarity (retrigger =
not-cleared), the pulse width (5–20 ms) and a pull on `CLR` that holds it
asserted through the microseconds of indeterminate monostable output at
power-up **[memory]**. Also confirm from the DAC8568 datasheet that `CLR` is
*level*-asserted and holds the outputs while low, rather than clearing once on
an edge **[memory — this is the load-bearing assumption of the whole
watchdog]**.

*Confidence:* **High** that these are unspecified. **Medium** on the DAC8568
`CLR` behaviour, which is exactly why it is listed as a thing to verify.

*Falsifying test:* on the E7 bench fixture, hold `CLR` low and attempt a
channel write; then release. If the write took effect while `CLR` was low, the
watchdog does not do what the design assumes.

---

### 2.2 CV outputs and patch abuse

---

**7. On a sustained short it is the 1 kΩ output resistor, not the op-amp, that
sits at its rating — and 0805 is the wrong package.**

**Severity: MINOR**

*Failure case:* a patch cable shorting a CV output to ground, or plugged into a
grounded sleeve.

*What happens.* The OPA2197 sources 11.5/1000 = **11.5 mA** into the short
**[derived]**, far inside its ~65 mA short-circuit limit **[memory]**. The
op-amp is not the stressed part. The entire voltage lands on `R-OUT-PROT`:

| Output state | V across the 1 kΩ | Power |
|---|---|---|
| Pitch at +7 V | 7 V | **49 mW** |
| Mod at ±10 V | 10 V | **100 mW** |
| Breath at +10 V | 10 V | **100 mW** |
| Op-amp railed at 11.5 V (fault) | 11.5 V | **132 mW** |

against an 0805 thick-film rating of **125 mW at 70 °C ambient** **[memory]**.
Normal outputs sit at 80 % of rating; a railed output exceeds it. Inside a 6HP
module the ambient is above 70 °C-derating's reference. The resistor will not
fail instantly — it will drift, and on the pitch channel a 1 % drift in that
resistor is a 1 % change in the divider against the patched load, which is
**~17 cents per octave** on top of whatever the calibration was set to
**[derived from ADR 0006's own divider table]**.

*Output-to-output patching*, which ADR 0004 specifically claims survival of,
is easier: two outputs at +10 V and −10 V give 20 V across 2 kΩ = 10 mA and
100 mW in each resistor **[derived]**. That claim holds.

*Proposal.* **Use 1206 (250 mW **[memory]**) for `R-OUT-PROT`.** Six parts, no
layout cost, and it also buys margin for the ESD case in finding 9 and the
rail-fault case in finding 8. This is the cheapest fix in the document.

*Confidence:* **High** on the arithmetic. **High** on the 0805/1206 power
ratings, which are industry-standard, though still **[memory]**.

*Falsifying test:* short each output to ground for ten minutes at worst-case
commanded value and thermocouple the resistor. Under ~90 °C ⇒ accept 0805.

---

**8. If the BAV99 clamps are literally "at the CV jacks" they sit on the
unprotected side of the 1 kΩ and a hard external source destroys them; moving
them inboard also deletes their leakage contribution to pitch error.**

**Severity: MAJOR**

*Failure case:* a patch cable carrying a ±12 V-class source onto a CV output —
another module's railed output, a bench supply during bring-up, a passive mult
tying an output to a power breakout.

*What happens.* ADR 0006 and the BOM both say *"clamp diodes at the CV jacks"*
**[repo]**. Read literally — clamp on the jack side of `R-OUT-PROT` — the only
impedance between an external source and the BAV99 is the patch cable. A +15 V
bench supply through ~0.5 Ω of cable into a diode clamping at 11.6 + 0.7 =
12.3 V gives (15 − 12.3)/0.5 ≈ **5.4 A** **[derived]** against a BAV99's ~200 mA
continuous forward rating **[memory]**. The diode is destroyed in microseconds
and the op-amp is then exposed. **First part to fail: the BAV99.**

Placed *inboard* — between the op-amp output and the 1 kΩ — the same fault
gives (15 − 12.3)/1000 = **2.7 mA** into the clamp **[derived]**, trivial, and
the op-amp is genuinely protected. The cost moves to the resistor: an external
+12 V against an output sitting at −10 V puts 22 V across 1 kΩ = 22 mA and
**484 mW** **[derived]**, which burns an 0805 and runs a 1206 at ~2× rating.
That is the right trade: an uncontrolled resistor failure (which goes open, and
kills one channel) is preferable to a clamp failure (which goes short, and
exposes the op-amp and the rails).

There is a second, free benefit. ADR 0006 chose BAV99 over BAT54S specifically
because *"2 µA of Schottky leakage through the 1 kΩ output resistor is 2 mV,
which is 2.4 cents of temperature-dependent pitch error"* **[repo]**. With the
clamp inboard of the resistor its leakage flows out of the op-amp's
low-impedance output node instead of through the 1 kΩ, and the error becomes
**exactly zero** for any diode. The argument that constrained the part choice
disappears with the placement choice.

*Proposal.* **Clamp to the rails between the op-amp output and the series
resistor, on all six channels.** This is also, as far as I can tell, the
Eurorack norm **[memory]**. Combined with finding 7's 1206, the topology is
op-amp → BAV99 to ±12 V → 1 kΩ (1206) → jack.

*Confidence:* **High** on the electrical argument. **Medium** on whether the
documents actually mean the jack side — "at the CV jacks" may be loose prose
for "on the output channels". Worth one line in the ADR either way, because
the reader cannot tell.

*Falsifying test:* on the E7/E10 board, force +15 V onto a CV jack through a
1 A-capable source with a current probe in line. Amps ⇒ clamp is outboard.
Milliamps ⇒ already inboard and the finding is moot.

---

**9. One corrupted word on DAC channel 7 moves all four mod outputs by up to
10 V simultaneously — and it is the one channel written once at boot, so
nothing ever corrects it.**

**Severity: MAJOR**

*Failure case:* a single SPI bit error on the umbilical, a glitch during
brown-out, or a `SYNC` edge on a floating input during an unclean start.

*What happens.* Mod channels are `Vout = 4 × (Vdac − Voffset)` with `Voffset`
from DAC channel 7 nominally 2.5 V **[repo]**. That offset is shared by all
four channels, and it is multiplied by the same gain of 4. A corrupted channel
7 word that lands at zero scale takes every mod output to `4 × Vdac`: a channel
resting at 0 V (Vdac = 2.5 V) jumps to **+10 V**, and all four do it at once
**[derived]**. Into a VCA or a filter that is a full-scale slam.

Every other channel is written every 250 µs, so a corrupted word there is
self-corrected within one loop pass. Channel 7 is *"written once at boot"*
**[repo]**, so the error is permanent until the next reset. The design's single
best accidental defence — fixed-rate refresh — is switched off precisely on the
most leveraged word in the system.

*Proposal.* Two changes, both free.

1. **Refresh channel 7 in the round-robin like everything else.** Cost, from
   the project's own loop budget: seven channels at 16 µs instead of six, so
   136 µs → **152 µs of a 250 µs period, 61 % duty** instead of 54 %
   **[derived from the repo's figures]**. It buys back self-correction on the
   only word that is 4×-leveraged across four outputs.
2. **RC the channel-7 output before its buffer**, τ ≈ 100 ms. The signal is a
   DC reference written once; a 100 ms time constant costs nothing functionally
   and converts any glitch from a step into a ramp, which combined with (1)
   means a corrupt word never reaches the output at all. Put the RC *before*
   the buffer so the op-amp still presents a low impedance to the summing
   stages.

*Related, and worth recording as a strength:* the fixed-rate refresh means a
single corrupted SPI word on any of the other channels is a **250 µs glitch,
not a stuck value**. Through the mod channels' 2 kHz reconstruction filter
(τ = 80 µs **[derived]**) a 250 µs excursion reaches 1 − e^(−3.1) ≈ 95 % of
full scale, so it is an audible click rather than a jump. Nobody has written
this property down, and it should be protected explicitly: **do not "optimise"
the output loop to write-on-change.** That optimisation would convert every
cable glitch from a click into a stuck voltage.

*Confidence:* **High**. The topology, the gain of 4 and the write-once
behaviour are all stated in ADR 0006; the arithmetic is one multiplication.

*Falsifying test:* at E10, command channel 7 to zero scale deliberately and
measure all four mod outputs. If they do not move ~10 V, the offset is not
being applied the way the ADR describes.

---

**10. The ambient-zero channel is the loudest single path available in the
system and has no rate limit anywhere.**

**Severity: MINOR**

*Failure case:* a corrupted word or a firmware bug on DAC channel 6.

*What happens.* Channel 6 drives the INA821's `REF` pin **[repo]**. An in-amp's
`REF` adds to its output one-for-one, and that output then passes through the
gain and offset stages to a 0–10 V jack. A full-scale `REF` excursion therefore
appears at the breath jack scaled by the post-in-amp gain — up to the full
0–10 V span. Breath is the channel most likely to be patched to a VCA, so this
is the one fault in the design that produces **instant full volume**. The
500 Hz–2 kHz output filter turns the step into a ~1 ms rise, which is not a
mitigation.

*Proposal.* The same trick as finding 9, and for the same price: **an RC with
τ ≈ 100 ms between DAC channel 6 and its buffer.** The auto-zero is specified
to decay over ~2 s **[repo]**, so a 100 ms time constant is invisible to the
function and bounds the worst glitch to a slow ramp. One resistor, one
capacitor, placed ahead of the existing low-impedance buffer so CMRR at the
`REF` pin is unaffected.

*Confidence:* **Medium-High.** The `REF`-adds-directly property of an in-amp is
certain; the exact post-in-amp gain is not pinned down in the documents, so the
"up to 10 V" is a bound rather than a measurement.

*Falsifying test:* at E10, step channel 6 from zero to full scale and scope the
breath jack. Measure the excursion and the rise time.

---

**11. An open potentiometer wiper puts the breath output at the rail.**

**Severity: MINOR** (low probability, loudest possible consequence)

*Failure case:* dust, wear or a cracked wiper contact on either Alpha 9 mm pot,
both of which sit directly in the breath signal path **[repo]**.

*What happens.* If the wiper drives an op-amp's non-inverting input and goes
open, that input floats, the op-amp's input bias current charges the stray
capacitance, and the output slams to a rail — **+11.5 V on the breath jack**
**[derived]** into whatever is patched. Same for the offset pot, scaled by the
following stage. The symptom is a full-volume blast with no warning, and it is
intermittent (it comes and goes with wiper position and vibration), which is
the worst diagnostic signature available.

*Proposal.* **One resistor per pot** — 100 kΩ from the wiper node to the end of
the track that represents the safe extreme (minimum gain, zero offset). On an
open wiper the node is then defined, and the failure becomes "the knob stops
working" instead of "the patch screams". Two parts, no signal-path penalty at
these impedances against the op-amp's input impedance.

*Confidence:* **High** on the mechanism (this is the textbook pot failure).
**Low-Medium** on the probability for a new 9 mm pot in a studio — genuinely
rare. It is on the list because the consequence is the maximum the system can
produce and the fix is two resistors.

*Falsifying test:* lift the wiper connection with the module powered and a
scope on the breath jack. If the output stays put, the topology already defines
the node.

---

**12. The analog breath path has no readback anywhere, so a dead breath CV is
undetectable from the instrument — and the display will keep showing breath
moving.**

**Severity: MINOR** (accept, with one cheap partial fix)

*Failure case:* `BREATH` shorted to `AGND` in the cable, an open `BREATH`
conductor, or a failed instrument-side buffer.

*What happens.* The in-amp sees zero differential, its output goes to `REF`,
and the breath jack parks at the ambient-zero value. Nothing detects it,
because the analog path never returns to any processor. Meanwhile the MCU's own
digitised copy — taken from the sensor before the umbilical — keeps working
perfectly, so the instrument's display, its USB MIDI, its note gating and its
mod channels all behave normally. The player's experience is "the note triggers
and the pitch is right but nothing gets louder", with every indicator in the
system saying the breath path is fine.

The MISO conductor that could have carried a module-side status bit was
deliberately deleted, on the reasoning that *"+12 V on the umbilical is itself
evidence the module is connected"* **[repo]**. That reasoning is about
*presence*, and it is correct. What was also deleted, and not noticed, is the
ability to verify *anything* the module does — including DAC readback, which
the DAC8568 supports **[memory]**.

*Proposal.* **Accept the lack of readback** — all eight conductors are spoken
for, and adding a ninth means changing the connector, which is not a
proportional trade for a one-off with a bench in the room. Two cheap partial
measures instead:

1. **A LINK LED on the module panel, driven by the watchdog's `CLR` state.**
   One LED, one resistor, one gate. It turns every umbilical fault, every
   instrument hang, and every "is it talking?" question into something visible
   from across the room. The module has no processor and currently reports
   nothing at all; this is the single highest information-per-part item in this
   review. The panel already carries a power LED **[repo]** and there is room.
2. **Write the signature down.** "Breath jack dead while the display shows
   breath moving ⇒ the fault is between the instrument's buffer and the module's
   in-amp; swap the cable first." That is a sentence in the ADR and it is worth
   more than a part.

*Confidence:* **High** on the failure being silent; that follows directly from
the architecture.

*Falsifying test:* short `BREATH` to `AGND` at the module's connector while
playing. If any indicator anywhere changes, the finding is wrong.

---

### 2.3 The umbilical

---

**13. The specified TVS array is a ~5 V part and the umbilical carries +12 V on
one of the eight conductors it is drawn across.**

**Severity: SHOWSTOPPER** (as written; trivial to fix, and it is inside the
sealed body)

*Failure case:* first power-on.

*What happens.* `U-TVS-UMB` is *"SP3012-06UTG or similar array … TVS array on
umbilical entry … 8 conductors from outside"*, quantity 1, SOT-23-6 **[repo]**.
Two problems with that as a line item:

- **Working voltage.** The SP3012 family is a low-voltage ESD array with a
  working voltage around 5 V **[memory]**. Connected to the +12 V conductor it
  conducts continuously. The current is bounded only by the conductor
  (~0.2 Ω) and whatever the module's load switch allows, so at a 1.2 A limit it
  is dissipating on the order of 8–14 W in a SOT-23-6 **[derived]**. It fails —
  usually short — within seconds, at which point the umbilical +12 V is shorted
  to instrument ground inside a bonded body and the instrument is scrap.
- **Channel count.** A SOT-23-6 array has at most four I/O channels (four pins
  plus ground and V_CC) **[memory]**. There are five conductors needing
  protection (`BREATH`, `MOSI`, `CS`, `SCLK`, `+12V`) and three grounds. One
  SOT-23-6 part cannot cover eight conductors regardless of voltage.

**First part to fail: the TVS array itself, on first power-up.** This is the
worst kind of error for this project: it is inside the one enclosure that
cannot be opened, and it is the kind of thing that passes a schematic review
because the line item *sounds* right.

*Proposal.* Split the protection by voltage:

- **Low-voltage lines** (`BREATH`, `MOSI`, `CS`, `SCLK`): a 5 V-class array,
  correctly counted — one 4-channel SOT-23-6 covers the three SPI lines plus
  `BREATH`, which is the exact fit. Note `BREATH` reaches 4.7 V **[repo]**, so
  confirm the array's working voltage is ≥5 V and its leakage at 4.7 V is
  acceptable — the node is driven by a low-impedance buffer so leakage costs
  nothing electrically, but a part whose V_RWM is 5.0 V running at 4.7 V is at
  94 % of rating.
- **The +12 V conductor**: its own unidirectional part — a 15 V-class SMA TVS
  (SMAJ15A-class **[memory]**) to `PWR_GND`, which stands off 12 V and clamps a
  transient.

Four extra pads. Both parts are ~$0.40.

*Confidence:* **Medium-High.** The arithmetic is certain; the SP3012 working
voltage and the SOT-23-6 channel count are **[memory]** and need one datasheet
lookup each. But the *structural* error — one low-voltage array drawn across a
bus that includes a power rail — stands regardless of which exact part is
meant, and the BOM note "8 conductors from outside" makes clear that is what
was intended.

*Falsifying test:* open the SP3012 datasheet and read V_RWM and the channel
count. If V_RWM ≥ 14 V, the finding collapses to just the channel count.

---

**14. There is no transient protection at the *module* end of a 2 m cable, and
an ESD strike onto the aluminium key plate arrives there as a kilovolt-class
wavefront.**

**Severity: MAJOR**

*Failure case:* the player touches the key plate after walking across a carpet.
This is not an exotic scenario — the plate is the largest touchable conductor
in the system and both hands are on it continuously.

*What happens.* `MECH-GNDBOND` bonds the plate to `PWR_GND` **[repo]**, which is
right: the discharge is conducted rather than arcing to a switch pin. But
`PWR_GND` then runs 2 m down a Cat5 cable to the module.

Using the IEC 61000-4-2 contact-discharge model (150 pF, 330 Ω **[memory]**) at
8 kV:

- stored energy ½CV² = 0.5 × 150 pF × (8 kV)² = **4.8 mJ** **[derived]**
- charge = 1.2 µC, initial current ≈ 8000/330 = **24 A**, rise ~1 ns
  **[derived/memory]**
- the cable is not a lumped inductor at that rise time — it is a transmission
  line. With a twisted pair's Z₀ ≈ 100 Ω **[memory]**, the wavefront launched
  into it is 8000 × 100/(330 + 100) = **~1.9 kV**, arriving at the module in
  ~10 ns **[derived]**.

At the module that wavefront meets the 74AHCT125's inputs (via a 220 Ω
resistor, if it is there — see finding 15), the INA821's inputs via 10 kΩ, and
nothing else. There is no clamp. HBM ratings of ~2 kV **[memory]** on those
parts are not a defence against an IEC contact pulse, which has a much faster
rise and higher peak.

**First part to fail: the 74AHCT125 at the module**, because it has the least
series impedance in front of it. Its death then exposes the DAC by the same
mechanism as finding 2.

*Proposal.* **A second TVS array at the module end of the umbilical**,
referenced to module ground, on the same split-by-voltage plan as finding 13.
One SOT-23-6 plus one 15 V part, ~$0.80, and it is the only thing standing
between a 2 m antenna held in a player's hands and the module's precision
analog. Also: **land the plate's ground bond directly at the umbilical
connector's `PWR_GND` pins**, not at a convenient screw elsewhere in the stack,
so the discharge never traverses the instrument's boards on its way out.
ADR 0003 already puts the analog star point adjacent to the connector, so the
geometry is available — it just needs saying.

*Confidence:* **High** that the module end is unprotected (verified in the BOM:
`U-TVS-UMB` is categorised `controller`, quantity 1). **Medium** on the
kilovolt figure, which depends on Z₀ and the IEC model, both **[memory]**.

*Falsifying test:* an ESD gun at 4 kV and 8 kV contact onto the key plate, with
a scope (high-voltage probe, short ground) on the module's `SCLK` input. If the
excursion there is under a few hundred volts, the coupling is weaker than
modelled.

---

**15. Shield termination is unspecified — and with the shield bonded at both
ends it is the umbilical's primary ESD defence, while undefined it is an
antenna.**

**Severity: MAJOR** (for something that costs two solder joints)

*Failure case:* ESD, and RF ingress from the instrument's own WiFi.

*What happens.* The BOM says *"Cat5e STP patch lead … Shielded preferred"* and
ADR 0004 says the shield is *"free at this price"* **[repo]**. Neither says what
it connects to at either end. The three possibilities are not equivalent:

- **Unterminated at both ends:** a 2 m floating conductor around the signal
  pairs. Worse than no shield for ESD, because it capacitively couples the
  transient to everything inside it with no path to ground.
- **Bonded at one end:** conventional audio practice, and wrong here. It solves
  a hum-loop problem this system does not have, because both ends are *already*
  connected by `PWR_GND` — a shield bonded at one end adds nothing for ESD.
- **Bonded at both ends:** the shield becomes a low-impedance parallel path in
  company with `PWR_GND`, it carries the bulk of any ESD current, and the
  wavefront the signal conductors see (finding 14) drops substantially. It also
  slightly reduces the `PWR_GND` IR drop. Because it parallels `PWR_GND` and not
  `AGND`, it does **not** disturb the sense-return property that the whole
  analog breath scheme rests on (ADR 0003).

An etherCON D-series shell is metal and lands on the module's 6HP panel, which
is at module ground through the six jack bushings **[memory]** — so at the
module end the bond happens whether or not anyone decides it should.

*Proposal.* **Specify: shielded cable, shield bonded to the connector shells at
both ends, instrument-end shell bonded to `PWR_GND` at the connector.** Write
down that this is an ESD decision, not a tidiness one, so that a later reader
does not "fix" it into a one-end bond out of audio habit.

*Confidence:* **High** that it is unspecified. **Medium-High** on the
both-ends-is-correct conclusion, which rests on the observation that the two
grounds are already connected — that part is certain.

*Falsifying test:* the ESD test in finding 14, run with the shield bonded and
then floated. Compare the excursion at the module's `SCLK`.

---

**16. The MOSI series resistor is specified on the wrong board, and `CS` and
`SCLK` have none — which matters most for a rail-to-signal short inside the
cable.**

**Severity: MINOR**

*Failure case:* (a) signal integrity at length; (b) a crushed cable or a
solder whisker shorting `+12V` (pin 3) to `MOSI` (pin 4) — **physically
adjacent pins in the specified T568B mapping** **[repo]**.

*What happens.*

*(a)* `R-MOSI-SER` is described as *"Series termination on MOSI at the driving
end"* and categorised **`module`** **[repo]**. The instrument drives `MOSI`.
Source termination at the receiving end is not source termination; it is a
series resistor that does nothing for the reflection it was bought to damp.
ADR 0001 gets the principle exactly right for the key chain (*"source
termination at the driving end"* **[repo]**) and the BOM then places the
umbilical's one series resistor at the other end.

*(b)* The pin map puts the +12 V conductor immediately beside `MOSI`. With a
short between them: at the instrument, 12 V arrives on an ESP32-S3 GPIO whose
only defence is the TVS array (which, per finding 13, is not sized for this
board anyway). At the module, 12 V arrives at the 74AHCT125's input. With a
220 Ω at the module only, that is 12/220 = **55 mA** **[derived]** into an input
clamp rated ±20 mA **[memory]**. With 220 Ω at *both* ends it is 27 mA and the
instrument-side GPIO is also protected.

*Proposal.* **220 Ω on all three SPI lines at the instrument (driving) end** —
which is where ADR 0001's own rule puts them — **and keep 100–220 Ω at the
module end.** Six resistors, 0805, and they cannot be retrofitted inside a
bonded body. At 0.6 MHz **[repo]** into the module's ~10 pF of input
capacitance, 440 Ω total gives an RC of 4.4 ns against a 833 ns bit period —
0.5 % **[derived]**. There is no performance cost whatsoever.

*While in the neighbourhood:* the key chain's inter-board `QH`→`SER` links have
no series termination either. `R-TERM-CHAIN` is 2 parts, *"clock and latch at
the MCU"* **[repo]**, but each 74LVC165's `QH` also drives an unterminated
75–190 mm link **[repo, ADR 0013's run-length table]** to the next board, with
the same fast-edge-into-an-unterminated-line problem the ADR spends a page
correcting. Four more 33 Ω resistors, one per register, and they too are
unavailable after bonding.

*Confidence:* **High** on (a) — it is a direct contradiction between the BOM's
category field and its own description. **Medium** on the severity of (b),
which depends on whether a whisker short is plausible in an etherCON.

*Falsifying test:* E11, logic analyser at the module end at full cable length,
with and without the instrument-side resistors. If the edges are already clean
with none fitted, (a) is cosmetic.

---

**17. Hot-plug is much less dangerous than it looks, because an RJ45 does not
cross-connect during insertion — and the right defence is a written rule, not a
circuit.**

**Severity: MINOR** (largely already handled)

*Failure case:* plugging or unplugging the umbilical at either end with the
module powered and the panel switch on.

*What actually happens.* Working through it properly:

- **No cross-shorting.** In an 8P8C, each jack spring runs in its own channel
  and only ever wipes along its own plug blade. Contacts do not touch their
  neighbours during insertion **[memory]**. So the "arbitrary order" case is
  purely about *mating skew*, not about transient cross-connections — and the
  skew is set by the tilt of the plug, so sub-millisecond.
- **+12 V mating before any ground:** nothing happens. The instrument's ground
  floats up with it; `AGND` cannot carry return current at the module end
  (it lands on the in-amp's inputs through 10 kΩ and the 100 kΩ pulldown, by
  design), so the only meaningful returns are `PWR_GND` and `DIG_GND`. Worst
  transient current through an in-amp input: 12/10 k = **1.2 mA**
  **[derived]** — inside spec.
- **+12 V with only `DIG_GND` mated:** the instrument runs for a millisecond
  with its full current through the SCLK pair's ground. 0.65 A × 0.27 Ω
  (26 AWG, one way) = **175 mV** of ground offset **[derived]**, invisible to a
  TTL link. Non-event.
- **Inrush:** the TPS2553 does not re-ramp on hot-plug, it current-limits.
  Charging the instrument's ~1 mF of bulk (two 470 µF strip caps **[repo]** plus
  the buck input) to 12 V at 500 mA takes t = CV/I = 1 mF × 12 / 0.5 =
  **24 ms** **[derived]**, during which the load switch dissipates up to 6 W
  falling to zero — on the order of 70 mJ total, trivial for the package's
  thermal mass. **The load switch genuinely handles hot-plug**, and ADR 0005's
  E6 note already asks for a current probe on both switch-on and hot-plug.
- **Unplugging:** contacts break, the watchdog times out in 5–20 ms, `CLR`
  parks pitch at ~−2.5 V and the mods at 0 V. Correct and quiet.
- **The genuinely ugly one:** +12 V on an *exposed* RJ45 plug pin when the
  cable is left dangling from the module. Touch it to a grounded rail and the
  TPS2553 limits. **This is exactly what the load switch is for** and it works.

*Proposal.* **Accept, and write the rule down:** the module's panel switch is
the system's only power switch **[repo]**, one reach away in the same rack,
and flipping it turns every hot-plug into a cold-plug. That should be stated as
the operating procedure in ADR 0004 rather than left implicit, because the
whole hot-plug risk surface is voluntary. **One caveat:** whether the
TPS2553DBV variant latches off or auto-retries after a fault **[memory — I do
not reliably recall which of TPS2552/TPS2553 is which]** changes the behaviour
materially. Auto-retry turns a sustained short into a repeating ~1 A pulse
train on the rack's +12 V rail at the retry duty cycle — a disturbance every
other module in the case hears. Latch-off means a single fault requires a
deliberate toggle to clear, which for a one-off is the better behaviour.
**Pin the variant deliberately.**

*Confidence:* **High** on the RJ45 contact geometry and the inrush arithmetic.
**Low** on which TPS2553 variant does what, which is why it is flagged rather
than asserted.

*Falsifying test:* current probe on the umbilical +12 V, hot-plug ten times,
capture the inrush envelope; then short the far end and look for a retry
pulse train on the rack rail.

---

**18. An open `PWR_GND` conductor is invisible: the instrument keeps working
with its power return through `DIG_GND`, and nothing anywhere notices.**

**Severity: MINOR**

*Failure case:* one broken strand path in a flexed patch lead — precisely the
failure the "cable is a consumable" policy anticipates.

*What happens.* Three conductors go to module ground: `PWR_GND`, `DIG_GND`, and
(at the instrument only) `AGND`. Lose `PWR_GND` and the instrument's entire
return — up to 650 mA (finding 1) plus the WS2815s' hundreds-of-milliamp swings
at their ~2 kHz PWM rate **[repo]** — flows through `DIG_GND`, the SCLK pair's
return. DC offset: 0.65 A × 0.27 Ω = **175 mV** **[derived]**, harmless to a TTL
link. The instrument runs normally.

Two consequences:

- **The fault accumulates silently** until the *next* conductor fails, at which
  point the instrument dies with no history of having been degraded.
- `AGND` is unaffected — it still carries no power current — so the breath CV
  stays clean. That is the sense-return decision doing its job in a fault the
  ADR did not consider, which is a point in the design's favour.

The `AGND`-open case is likewise benign: the 100 kΩ differential pulldown holds
the in-amp at zero differential and the breath output goes to its ambient-zero
value.

*Proposal.* **Accept.** The recovery is already correct (replace the cable), the
cable is already declared a consumable, and building continuity monitoring into
a 2 m link for a one-off is exactly the "fix that costs more complexity than the
failure costs" this review is asked to avoid. Record the symptom instead:
**"SPI marker errors that appear only when the LEDs animate" is the signature of
a degraded umbilical ground.**

*Confidence:* **High**.

*Falsifying test:* lift `PWR_GND` at the module connector and play. If the
instrument fails outright, there is a ground-topology assumption I have wrong.

---

**19. The cable drop budget assumes 24 AWG, but the design requires stranded
patch cable, which is 26–28 AWG.**

**Severity: MINOR**

*What happens.* ADR 0005 computes drop over *"2 m of 24 AWG, round trip
~0.34 Ω"* **[repo]**, which checks out (24 AWG = 0.0842 Ω/m **[memory]**, ×4 m =
0.337 Ω). But the BOM mandates *"Cat5e STP patch lead, **STRANDED**"* **[repo]**
for excellent reasons, and stranded patch leads are commonly 26 or 28 AWG, not
24:

| Gauge | Ω/m **[memory]** | 2 m round trip | Drop @ 0.36 A | Drop @ 0.65 A |
|---|---|---|---|---|
| 24 | 0.0842 | 0.337 Ω | 0.12 V | 0.22 V |
| **26** | 0.134 | **0.536 Ω** | 0.19 V | **0.35 V** |
| 28 | 0.213 | 0.852 Ω | 0.31 V | **0.55 V** |

Nothing breaks — 11.1 V at the instrument still clears the buck's >6 V and the
REF5050's ≥7 V by a mile (see section 1). What changes is that every
`PWR_GND` offset figure in ADR 0003's tables is 1.6–2.5× larger than written,
and the load-switch/polyfuse sizing in finding 1 gets a little tighter.

Add ~20 mΩ per contact interface **[memory]**, two interfaces per conductor per
end; a **feedthrough** etherCON at the instrument end (still open in ADR 0004)
adds two more per conductor.

*Proposal.* **Specify the gauge** in the BOM — "26 AWG stranded or heavier" —
and redo the drop line in ADR 0005 at 0.54 Ω. It costs a sentence and it
removes a number that will otherwise be quoted as if measured. This also feeds
the feedthrough-vs-solder-tag decision at E12/M7, which is currently being made
on contact count without a resistance budget attached to it.

*Confidence:* **High** on the arithmetic; **Medium** on "patch leads are
typically 26–28 AWG", which is **[memory]** and varies by manufacturer — though
that is precisely the reason to specify it rather than assume.

*Falsifying test:* four-wire measurement of one conductor's loop resistance on
the actual cable bought. Under 0.4 Ω ⇒ it is 24 AWG and the original figure
stands.

---

### 2.4 Sequencing, brown-out and hang

---

**20. Rails present in every order: the only persistent bad state is "+12 V and
+5 V without −12 V", and it fails musically rather than electrically.**

**Severity: MINOR** (accept)

Worked through exhaustively, module side:

| State | What happens | First part at risk |
|---|---|---|
| **+12 only** | LM317 and DAC up; op-amps have no V−; buffer unpowered (bus +5 absent), so no writes reach the DAC; outputs stay at reset. Pitch sits near 0 V instead of −2.5 V because the stage cannot swing negative | none |
| **−12 only** | No LM317, no DAC. Op-amps with V+ = 0 sit near 0 V or drift toward −11.5 V. Into a VCO that is subsonic; into a VCA that is closed | none |
| **+5 only** | Buffer alive, DAC dead. Buffer would drive 5 V into unpowered DAC inputs — **prevented by the OE gating**, provided its polarity is right (finding 4). Without that inversion, three DAC inputs each take tens of mA into a dead AVDD | DAC8568 |
| **+12 and +5, no −12** | DAC written normally; pitch stage clips at ~0 V for its whole negative half. **The instrument plays, and every note below the reference octave is the same note** | none — but see below |
| **−12 and +5, no +12** | DAC dead, buffer alive, OE disabled by absent umbilical +12 V. Safe | none |
| **Rack brown-out, all rails** | DAC resets to zero scale with its internal reference disabled **[repo]**: all outputs 0 V except pitch at ~−2.5 V. Instrument reboots. Quiet | none |
| **Instrument-only brown-out** | Module never loses power, so the DAC holds its last value until the watchdog times out (5–20 ms) and asserts `CLR`. Then pitch −2.5 V, mods 0 V, breath at its zero. Instrument boots in ~300 ms **[memory]**, blanks LEDs, enables the DAC reference, resumes | none |

**The "+12 and +5 without −12" row is a genuinely silent failure** and belongs
in the ROADMAP's "failures that are silent" table alongside blank NVS, a
stuck-closed switch and a stale breath zero. It presents as "the low register
has gone wrong", which is exactly the kind of thing that gets blamed on the
fingering table for months.

*Proposal.* **Accept the electrical risk** — a rack with a dead −12 V rail is
usually obvious because half the case is dead — but **add the row to the silent
failures table** with its signature written out: *"everything below the
reference octave plays the same pitch ⇒ the module has lost −12 V."* Free.

*Confidence:* **High** on the enumeration. **Medium** on the exact behaviour of
an OPA2197 with V− absent, which depends on where the floating −12 V net
settles.

*Falsifying test:* on the E10 board, pull each rail in turn with a scope on all
six outputs and a current probe on the DAC's AVDD. Compare against the table.

---

**21. The hardware watchdog catches a *stopped* MCU, not a *hung* one that
keeps clocking — and the thing that closes that gap is free and is not written
down.**

**Severity: MINOR**

*Failure case:* the MCU hangs mid-note.

*What happens.* ADR 0004's analysis of the stuck-CV drone is correct and the
monostable is the right answer for the common case: a task crashes, the SPI
traffic stops, `CLR` asserts, pitch parks subsonic. But two hang modes defeat
it:

- **A hung task with a live peripheral.** An ESP32-S3 with an SPI DMA
  descriptor chain still cycling keeps producing `CS` edges after the code that
  computes the values has stopped. The monostable is retriggered forever and
  the last values drone exactly as if there were no watchdog.
- **A chattering `CS` on an intermittent cable** retriggers it the same way,
  while no real frames arrive.

*Proposal.* **Enable the ESP32-S3's task watchdog (TWDT) and interrupt watchdog
(IWDT) on the real-time board.** They reset the chip, which stops the SPI,
which triggers the 74HC123 — i.e. the software watchdog is what makes the
hardware watchdog *sufficient*, and neither is a substitute for the other. This
is free (both are configuration flags in ESP-IDF **[memory]**) and it should be
stated in `firmware/README.md` alongside the other non-negotiable architecture
constraints, because it is the only thing making a documented hardware safety
device actually cover its stated case.

Add one firmware rule for the other direction: **if breath has been
sub-threshold for N seconds while a note is still held, force the note off.**
That catches a hang in the note-state machine without any hardware involvement.

A hardware-only fix — making the monostable retrigger on something only valid
traffic produces — is available but is not worth it: it means decoding a frame
pattern in discrete logic in a module that deliberately has no processor, to
cover a case that two configuration flags already cover.

*Confidence:* **High** on the gap. **Medium** on whether an ESP32-S3 SPI DMA
would in practice keep running through the relevant hang modes; it depends on
the hang.

*Falsifying test:* at E11, deliberately `while(1);` inside the output loop's
task with DMA armed, and watch both the DAC outputs and the `CLR` line. If
`CLR` asserts, the peripheral stopped too and the concern is theoretical.

---

### 2.5 The instrument

---

**22. A shorted WS2815 is the only fault in this design that can put many watts
into one 5 mm package inside a sealed wooden box held against the player's
face.**

**Severity: MAJOR**

*Failure case:* a single WS2815 failing short — die or driver output — on
either side strip.

*What happens.* The strips run directly from raw umbilical +12 V **[repo]**,
with 470–1000 µF of local bulk at each feed point **[repo]** and *no
branch-level current limit anywhere*. The nearest limit is the module's load
switch, 2 m upstream, shared with the whole instrument.

- **Instant:** the local bulk dumps ½CV² = 0.5 × 1 mF × 144 = **72 mJ**
  **[derived]** into the short in microseconds. Peak current is limited by ESR
  and copper — tens of amps. This may clear the fault by vaporising a bond wire
  or a strip trace, which is the good outcome.
- **If it does not clear:** the fault draws steadily at whatever the load
  switch allows. At finding 1's recommended 1.2 A limit, that is 12 V × 1.2 A =
  **14 W** **[derived]** into one 5050-class package, continuously, until the
  TPS2553 reaches thermal shutdown — and if the rest of the instrument is also
  drawing, the limit may never be reached at all and the fault just sits there
  at whatever current it wants below the limit. A few watts into a 2 × 2 mm
  package glued to acrylic, inside oak, is a char mark, then smoke.

This is the fault the README's own framing points at: *"fault current, which a
larger supply makes worse, not better"* **[repo]**. And note the coupling —
**fixing finding 1 by raising the load-switch limit makes this case worse**,
which is the argument for putting a limit per branch rather than only globally.

*Proposal.* **One 500 mA fast-blow fuse (not a PPTC) in each strip's 12 V feed,
inside the body.** Two parts, ~20 cents. Sizing: realistic use is ~130 mA per
the ADR's own table **[repo]**, and even both strips at the full 3 W clamp is
250 mA total, so a 500 mA element per strip has 2–4× headroom and never sits
near its rating — the thermal-runaway objection ADR 0014 raises against the
main-feed polyfuse does not apply to a branch device with that much margin.

Use a **fuse rather than a PPTC** deliberately: in a sealed body you do not get
to benefit from resettability anyway, and a fuse gives a hard, fast, non-
thermally-hysteretic limit with none of the creeping-resistance behaviour that
made the polyfuse wrong in finding 1. The failure becomes "one strip goes
dark", which the instrument can even report, because the LEDs are driven by
firmware that knows what it commanded.

*Confidence:* **High** on the energy arithmetic. **Low-Medium** on probability —
WS281x failures more often go open than short **[memory]**. It is on the list
because it is the only genuinely hazardous consequence available in the whole
design and the fix is two parts.

*Falsifying test:* short one LED's supply pins on a strip offcut at the
intended feed impedance, with a current probe and a thermal camera, and see
whether it self-clears or sustains. Do this at E6/M6, on scrap, not in the
instrument.

---

**23. Key-switch pull-up resistors are absent from the BOM entirely, and at the
conventional 10 kΩ a saliva film reads as a key press.**

**Severity: MAJOR**

*Failure case:* (a) build-time omission; (b) condensation or saliva bridging a
switch pin to the grounded aluminium plate, which sits 1–2 mm away **[repo]**.

*What happens.*

*(a)* The 74LVC165A has no internal pull-ups **[memory]**, and the BOM contains
no pull-up line item — only `C-DECOUPLE-165` and `R-TERM-CHAIN` **[repo,
verified by grep]**. Without them every switch input floats when its key is
open. Floating CMOS inputs on four registers running down a 14-inch loom beside
an 800 kHz LED data line **[repo]** is a spurious-note generator, and it is
exactly the fault the marker-pattern counter exists to *count* rather than
prevent. **The 14 spare chain bits must be tied too**, not left floating, for
the same reason.

*(b)* This project's own moisture case makes the pull-up *value* matter, not
just its presence. The instrument is breathed into for hours behind 18
deliberately unsealed cutouts (the cavity must leak, for the pressure reference
**[repo]**), the aluminium plate is bonded to `PWR_GND` **[repo]**, and switch
pins sit 1–2 mm from it. A 74LVC165's V_IL at 3.3 V is ~0.8 V **[memory]**, so
a press is read when the leakage resistance satisfies
3.3 × R/(10 k + R) < 0.8, i.e. **R < 3.2 kΩ** **[derived]**.

A saliva film bridging 1 mm with a 1 mm × 0.1 mm cross-section, at a
conductivity of ~1 S/m **[memory]**, is R = L/(σA) = 0.001/(1 × 10⁻⁷) =
**10 kΩ** **[derived]**. That is within one order of magnitude of the trip
threshold — well inside the range where a fatter or saltier bridge reads as a
press. **Phantom notes from condensation, in a body that cannot be opened.**

*Proposal.* **2.2 kΩ pull-ups on all 32 chain inputs.** At 2.2 kΩ the threshold
moves to R < 700 Ω **[derived]**, which a condensation film will not reach.
Current cost: 3.3 V/2.2 kΩ = 1.5 mA per *closed* key; a fingering typically
closes ≤8, so ~12 mA **[derived]** — against an instrument drawing 356 mA. Free.
The stiffer pull also roughly quadruples the noise immunity of every chain
input against capacitive coupling from the LED data line, which is the other
thing this loom is fighting. Two problems, one part value.

*Confidence:* **High** on the BOM omission (verified). **High** that LVC has no
internal pull-ups. **Medium** on the saliva conductivity and the film geometry,
which are **[memory]** and order-of-magnitude — but the margin at 10 kΩ is only
one order of magnitude, which is not enough margin to rely on an
order-of-magnitude estimate.

*Falsifying test:* wet a switch's pins and the plate edge with a saliva
simulant on the M2 mule, and watch the key state with the live telemetry
(F6). Trivial, and it is a test that can be run before anything is bonded.

---

**24. A stuck-*open* key is undetectable and unaddressed — and the real
mitigation for a dead switch in a sealed body is already in the design, unnamed.**

**Severity: MINOR**

*Failure case:* a switch that stops making contact — contact contamination,
a cracked solder joint after a drop, a failed spring.

*What happens.* The ROADMAP's silent-failure table covers **stuck-closed** well:
flag any key closed at boot or held beyond N seconds **[repo]**. **Stuck-open
gets nothing**, and it cannot get the same treatment, because "this key is
open" is the normal state of every key most of the time. The symptom is
identical to stuck-closed in kind — fingerings that participate in that key
silently return a different note — and identically unfalsifiable by ear inside
a body that cannot be opened.

*Proposal.* Two things, both free.

1. **A per-key press counter in NVS, shown on a diagnostics page.** 18 counters,
   a few dozen bytes, one display screen. A key with zero presses after an hour
   of playing while its neighbours have hundreds is a dead key, stated as a
   number rather than as a feeling. This is the same move the marker-pattern
   counter makes for the loom, applied to the switches.
2. **Name the recovery that already exists.** The fingering table is data in
   NVS, editable over WiFi from a phone (ADR 0010, ADR 0012) **[repo]**. That
   means a dead key in a bonded body is recoverable by re-authoring the
   fingering system around it — which is the *only* recovery available and is
   nowhere described as one. ADR 0002 accepts a failed switch as "taking the
   instrument apart"; it does not have to be. Write that down in ADR 0002's
   "accepted consequence" section, because it changes the severity of the
   accepted risk.

*Confidence:* **High**.

*Falsifying test:* disconnect one switch on the M2 mule and try to identify
which one by playing, without looking. Then try again with the counter page.

---

**25. A wetted PTFE restrictor is an intermittent dead breath sensor that
recovers on drying — and it will look exactly like a failed sensor.**

**Severity: MINOR**

*Failure case:* condensation reaching the porous hydrophobic PTFE plug at the
sensor port.

*What happens.* `MECH-PTFE` does two jobs — Helmholtz restrictor and liquid
barrier **[repo]** — and that dual role has a failure mode neither job has on
its own. A hydrophobic membrane does not let water *through*, which is the
point; but a continuous water film across its face, which surface tension
readily sustains over small pores, **blocks air flow as well** **[memory — this
is the known "water-blocked vent" failure of hydrophobic vents]**. The system is
dead-ended, so the sensor chamber behind the plug becomes a sealed volume and
pressure changes at the mouthpiece cannot reach the diaphragm at all.

The output goes to zero, indistinguishable from a dead sensor, and **it comes
back the next day** when the film evaporates. Intermittent-dead-then-fine is
the most misleading diagnostic signature in the document, and the design's
current interpretation guide (ADR 0003: output that *falls* under warming means
a blocked reference chamber, output that *drifts* is ordinary thermal offset
**[repo]**) has no third row for it.

*Proposal.* **Accept the mechanism; add it to the interpretation guide and to
the E2 test.** E2 already runs a human through 20 minutes of real playing
**[repo]** — which is the condition that produces the film. Watch for
*response* dying (a step at the mouthpiece producing nothing) as distinct from
the zero drifting or falling. If it happens, the levers are a larger plug face
area, a coarser pore size, or moving the plug so that gravity drains it rather
than pooling on it — all cheap, all decided at E2 while the geometry is still
open. Also ensure the trap's "clearable without disassembly" access reaches the
plug face, not only the trap volume.

*Confidence:* **Medium-High.** The water-blocked-vent mechanism is real and
well known; whether it occurs at this plug's pore size and duty cycle is not
predictable from here, which is exactly why it is a test rather than a fix.

*Falsifying test:* E2 — wet the plug face deliberately with a drop of water,
then step the pressure at the mouthpiece and scope the sensor output. No
response ⇒ confirmed. Normal response ⇒ the pore size is coarse enough.

---

**26. The DP's reference port is open to a 100 % RH box, and the vapour
argument for venting it outside is independent of the thermal argument the
design already tracks.**

**Severity: MINOR**

*Failure case:* long-term humidity exposure of the sensor's reference face.

*What happens.* ADR 0003 is careful and correct about the reference port's
*pressure* behaviour: the cavity must leak, and it does, through 18 switch
cutouts **[repo]**. It even identifies the right test (watch the zero during
M8's thermal soak) and the right escape hatch (vent the reference port through
a filtered stub, which the DP makes possible and M8 is pre-bond) **[repo]**.

What it does not consider is that "open to the cavity" also means **open to
~100 % RH exhaled air, for hours at a time, for years** — the same condition
the ADR treats as serious on the pressure side, where it quotes NXP saying the
family is *"NOT compatible with water or water vapors"* and that *"the gel die
coat swells when wet"* **[repo]**. On the *reference* side of an MPXV-series DP
part the die face is typically not media-protected in the same way as the
pressure port **[memory — I am not certain which face carries the gel on case
1351-01, and this is the load-bearing uncertainty in this finding]**. If that is
right, the design has the media-hardened face pointed at the filtered,
restricted, trapped tube and the unhardened face pointed at the open humid
cavity.

Three of the ADR's own mitigations — the PTFE plug, the trap, the restrictor —
all sit on the pressure port and none of them protect the reference side.

*Proposal.* **Vent the reference port to outside through its own short filtered
stub by default, rather than only if the M8 soak shows the zero walking.** The
ADR already identifies this as the available move and already notes M8 is
pre-bond; the change is to make it the default rather than the contingency,
because the soak tests the *thermal* argument and does not test the vapour one
at all. A short stub with a PTFE disc at the body wall is one more part of a
kind already in the BOM.

Second: `MECH-COAT`'s "mask both ports before coating" rule **[repo]** is
correct and is the single highest-consequence assembly instruction in the
project. It deserves to be a line on a physical build checklist, not only a
sentence in an ADR, because the failure it prevents (output clipped at 0.2 V
after ten minutes of warming, reading correctly from cold) is described in the
ADR itself as more confusing than a dead part.

*Confidence:* **Medium.** The vapour concern is real and is the ADR's own
concern applied consistently; which die face is gel-coated is **[memory]** and
must be checked before acting.

*Falsifying test:* the MPXV4006DP datasheet's media-compatibility section — does
it qualify both ports, or only P1? One paragraph settles it.

---

**27. Mechanical abuse: the failure order when the instrument is hung by its
cable runs cable retention → module panel → rack rails, and the dev boards are
on unretained 0.1 in headers inside a body that cannot be opened.**

**Severity: MINOR**

*Failure case:* the instrument dropped and arrested by the umbilical; or dropped
onto the floor; or simply put down carelessly a thousand times.

*What happens.*

*Hung/dropped on the cable.* Instrument mass ~825 g **[repo]**. A 0.5 m fall
arrested over ~20 mm of cable and connector compliance gives
a = v²/2s = (2 × 9.81 × 0.5)/(2 × 0.02) = **245 m/s² ≈ 25 g**, so
F = 0.825 × 245 = **~200 N ≈ 20 kgf** **[derived]**. That load passes through
the etherCON latch (cable retention in the ~100 N class **[memory]**), then the
module's panel and its PCB brace, then two M3 screws into the rack rails. At
200 N something yields: most likely the cable or the etherCON latch, which is
the *right* failure order given the cable is a declared consumable — but if the
latch holds, a 20 kgf sideways yank on a 6HP panel will bend it or pull the
module out of the rails, taking the ribbon with it.

The design has already done the two things that matter here — brace the etherCON
to the module PCB **[repo]** and mount the instrument-end connector to an
internal backing plate rather than oak **[repo]**. Both are correct and both are
load-bearing.

*Dropped on the floor.* ~825 g from 1 m is ~8 J **[derived]**. The AMOLED panel
is glass; the keycaps take the first hit. Nothing in the design addresses shock,
and for a one-off nothing should. But one specific consequence does deserve
attention: **the two dev boards plug into the passive carrier on 2.54 mm
headers** (ADR 0013's whole build strategy) **[repo]**, and a shock can partially
unseat a header in a body that cannot be reopened. The symptom would be an
intermittent that looks exactly like a marginal loom.

*Proposal.* Two things, both at M7/M8:

1. **Retain the dev boards mechanically** — a screw through a standoff at the
   far corner of each, or a bead of RTV across the header ends. Minutes of work,
   available only before bonding.
2. **Anchor the umbilical to the rack case, not to the module panel.** A cable
   clip or a zip tie on the rail below the module takes the drop load into the
   case instead of into a 30.18 mm panel with a 23.8 mm hole in it **[repo]**.
   This is the cheapest item in the entire review and it protects the most
   awkward-to-repair joint.

Also add to M8's failure-injection list: **plug and unplug the umbilical 50
times and flex it under load at the instrument end**, watching the key-chain
error counter. The instrument-end etherCON and its solder tags are the single
unrepairable single point of failure in a bonded body, and that is the last
moment they can be exercised.

*Confidence:* **High** on the arithmetic. **Medium** on the etherCON retention
figure, which is **[memory]**.

*Falsifying test:* hang the assembled-but-unbonded instrument from its cable at
M8, add a 5 kg static load, and inspect the connector and backing plate.

---

**28. Two residual items, recorded briefly because they are real and cheap to
close.**

**Severity: NIT**

*(a) The USB bench mode has no breath path.* ADR 0005 offers *"OR the umbilical
power with USB power — it costs a diode … the instrument runs on the bench
during development without a rack attached"* **[repo]**. But the breath sensor's
REF5050, its OPA2197 buffer and the WS2815s all run from **+12 V** **[repo]**,
which USB does not provide. So USB-only running gives keys, IMU, display and
USB MIDI — and **no breath at all**. E5 is *"Plays into a DAW … first playable
milestone"* **[repo]** and depends on breath response. The diode is still worth
having; the claim attached to it needs narrowing to "flashing and key/IMU work",
and E5's bench setup needs a 12 V feed. Better to discover that here than at
E5. *Falsifying test:* trace the REF5050's supply net on the carrier schematic.

*(b) Mains safety, in one line.* The player holds a metal plate bonded through
`PWR_GND` to the rack's ground, while blowing into a tube, with the other hand on
the same plate. The isolation between that plate and mains is entirely the rack
PSU's. That is a general property of every Eurorack system and not a defect
here, but it is worth one sentence in ADR 0009 noting that the key plate's
ground bond makes the PSU's isolation a *player* safety question rather than only
an equipment one — i.e. use an earthed or double-insulated brick, not an
unbranded unisolated supply. *Falsifying test:* measure plate-to-earth
resistance and leakage current with the rack powered.

---

**29. The buck's input LC filter has marginal damping against the converter's
negative input resistance.**

**Severity: MINOR**

*Failure case:* the instrument running at full load with a purely ceramic
capacitor at the buck input.

*What happens.* `L-BUCK-IN` is *"10–47 µH … A real inductor, not a bead"*
**[repo]** between the umbilical node and the R-78E5.0's input. That is the
right call for the noise job it was bought for, but an LC filter in front of a
switching regulator is the classic Middlebrook stability case **[memory]**: the
converter presents a **negative** incremental input resistance
Z_in = −V²/P = −(11.5²)/3 W = **−44 Ω** **[derived]**, and the filter's peak
output impedance must sit well below that.

At L = 47 µH and C = 10 µF: f₀ = 1/(2π√LC) = **7.3 kHz**, characteristic
impedance √(L/C) = **2.17 Ω**, and with the inductor's ~0.3 Ω DCR **[memory]**
Q ≈ 7.2, so the peak output impedance is **~15.6 Ω** **[derived]**. The margin
against 44 Ω is 2.8×, where the usual design rule wants 3–10×. That is inside
the region where the input filter and the converter can ring or sustain a
low-frequency oscillation — at 7 kHz, on the same 12 V rail that feeds the LED
strips and the REF5050, and inside a sealed instrument where it is not
investigable.

*Proposal.* **Damp it.** The cheapest version is to make sure the buck's input
capacitance includes an electrolytic with real ESR (~0.2 Ω) in parallel with
the ceramic, rather than ceramic alone — which also happens to be the part the
design already buys in quantity for the strips. A series R–C damper across the
input cap is the textbook alternative. Either is two parts and it is available
only before layout.

*Confidence:* **Medium.** The framing is standard and the arithmetic is
straightforward, but the actual result depends on the R-78E5.0's real input
capacitance and control bandwidth, neither of which is in front of me.

*Falsifying test:* E6 — scope the buck's input node at full load with a
current-step disturbance, and look for ringing near 5–10 kHz. This is already
half-covered by the "rack rail ripple, both directions" measurement in the
latency budget **[repo]**; it just needs the input node added to the list.

---

## 3. Cases covered with nothing to report

Recorded so the coverage is auditable rather than implied.

| Case | Verdict |
|---|---|
| Reversed Eurorack ribbon | Handled. Both Schottkys block; module dark; no damage. Residual is the +5 V pin only (finding 2) |
| CV output shorted to ground | Survives. 11.5 mA; only the resistor's package rating is marginal (finding 7) |
| CV output to CV output | Survives as claimed. 10 mA, 100 mW per resistor |
| Umbilical unplugged at either end, powered | Safe. Watchdog → `CLR` in 5–20 ms; pitch subsonic, mods 0 V; exposed +12 V plug pin is current-limited at the module |
| Conductors shorted to each other | The damaging combination is +12 V→`MOSI` (adjacent pins) — finding 16. `BREATH`→`AGND` is silent but harmless (finding 12). SPI-to-SPI is a wrong-CV glitch, self-corrected in 250 µs (finding 9) |
| Conductors shorted to shield | Same as shorted to `PWR_GND` once the shield is bonded (finding 15). No new mechanism |
| Contacts mating in arbitrary order | Much smaller risk than it appears: no cross-connection in an 8P8C, sub-ms skew, inrush bounded by the load switch (finding 17) |
| One rail without the others, all orders | Enumerated in finding 20. One silent musical failure, no damage |
| Brown-out and recovery state | Genuinely well designed (section 1, finding 20). Blank-at-boot, zero-scale reset, watchdog `CLR`, NVS CRC all pull in the same direction |
| MCU hangs mid-note | Covered for the common mode; gap and free fix in finding 21 |
| Failed/intermittent conductor | Findings 12, 18, 19. All recoverable by replacing a declared consumable |
| ESD onto a jack | The 1 kΩ + clamp topology is right, *if* the clamp is inboard (finding 8). Residual: repeated strikes drift the 1 kΩ, which is a pitch gain error that recalibration removes |
| ESD onto a key | Conducted into the bonded plate rather than into a switch pin. Correct by design; the exposure is downstream (finding 14) |
| ESD onto the plate / connector shell | Finding 14 and finding 15 |
| Stuck-closed key | Already handled well in the ROADMAP |
| Stuck-open key | Finding 24 |
| Condensation / liquid at the sensor | Findings 25, 26; the pressure-side handling is already thorough |
| Condensation / liquid on the boards | Findings 22, 23. Also: specify coated or IP-rated LED strip — 12 V DC on exposed copper in a humidity chamber corrodes anodically over months, and the strips are the only such copper in the body |
| Open LED in the strip | Handled by the WS2815 backup data line. One dark pixel |
| Shorted LED in the strip | Finding 22 |
| Unplugged / dropped / hung by the cable | Finding 27 |

---

## 4. Proportionality — what to fix and what to accept

The test applied: *does the fix cost less complexity than the failure costs,
given a one-off, a sealed body, a generous rack and a full bench?* In this
project one factor dominates everything: **the body is bonded shut**, so a part
inside it is worth defending at maybe ten times the price of the same part in
the module.

### Fix before any board is fabbed — cheap, and unavailable later

| # | Fix | Cost |
|---|---|---|
| 1 | Delete `F-POLY` (or resize to 1.5–2 A); size the TPS2553 limit from E6's measurement above the *clamped* worst case | −1 part |
| 13 | Split umbilical TVS by voltage; the +12 V conductor gets its own 15 V part | +1 part |
| 23 | 2.2 kΩ pull-ups on all 32 chain inputs, spares included | +32 resistors, ~12 mA |
| 2 | Move the 74AHCT125 to the LM317 rail; delete the bus +5 V dependency | 0 parts, removes 3 findings |
| 4 | Invert the OE gating properly; add pulls on the DAC side of the buffer | +3 parts, +3 resistors |
| 8 | Clamps inboard of the 1 kΩ | 0 parts (a net choice) |
| 7 | `R-OUT-PROT` to 1206 | 0 parts |
| 14 | Second TVS array at the module end; plate bond lands at the connector | +2 parts |
| 22 | 500 mA fuse per LED strip feed | +2 parts |
| 16 | 220 Ω on all three SPI lines at the instrument end; 33 Ω on each `QH` | +7 resistors |
| 9 | RC on DAC ch 7 ahead of its buffer; refresh ch 7 every loop pass | +2 parts, +7 % loop duty |
| 10 | RC on DAC ch 6 ahead of its buffer | +2 parts |
| 11 | Wiper-defining resistor on each pot | +2 parts |
| 12 | LINK LED on the module panel from the watchdog state | +3 parts |
| 6 | Watchdog on the DAC's rail, retrigger-is-not-cleared polarity | 0 parts |
| 29 | Electrolytic (or R–C damper) at the buck input | +1 part |

Total: roughly **60 passive parts and 10 actives**, on boards being laid out
anyway, against a set of failures of which two are unrecoverable inside a bonded
body. Every one of them is a better trade than the design's existing precision
budget, which spends far more than this on tuning stability.

### Fix in firmware — free

- **21** TWDT + IWDT enabled; force note-off on sustained sub-threshold breath.
- **24** Per-key press counters and a diagnostics page; and write down that
  re-authoring the fingering table is the recovery for a dead switch.
- **20** Add "no −12 V ⇒ the bottom of the pitch range collapses to one note"
  to the silent-failures table.
- **9** Record "do not optimise the output loop to write-on-change" as an
  architecture constraint in `firmware/README.md`, with the reason.

### Fix in documentation and procedure — free

- **15** Specify shield bonded at both ends, and say it is an ESD decision.
- **17** State that the panel switch is flipped before plugging the umbilical.
- **19** Specify the cable gauge; redo the drop budget at 0.54 Ω.
- **5** Draw the bond diagram once, with a multimeter, against the real rack.
- **26** Put "mask both sensor ports" on a physical build checklist.
- **27** Add connector flex/insertion cycling to M8's failure injection.
- **12, 25, 18** Write the diagnostic signatures down — they are worth more
  than most of the parts above.

### Accept, explicitly

- **A drop onto a hard floor.** One-off, hand-built, played on a strap. Shock
  mounting a 825 g laminated instrument is a redesign; retaining the dev boards
  (finding 27) captures nearly all the available benefit for nothing.
- **No readback on the analog breath path** (finding 12). Adding a ninth
  conductor means changing the connector. The LINK LED and a written signature
  are the proportional 90 %.
- **Corrupted SPI producing a wrong CV.** Adding link-layer integrity means a
  processor in a module deliberately designed not to have one. The fixed-rate
  refresh already bounds it to a 250 µs click, the cable is a consumable, and
  E11 is the test. Protect the refresh; do not build a protocol.
- **A hung MCU that keeps clocking** beyond what TWDT/IWDT cover. Decoding
  frame validity in discrete logic is out of proportion.
- **An open `PWR_GND` conductor** (finding 18). Continuity monitoring on a
  2 m consumable link is not worth building.
- **A row-offset ribbon at the bus board** (finding 5). Nothing on the module
  can defend its own ground pin, and the connector choice already prevents it
  at the end this project controls.
- **A rack running without −12 V** (finding 20). Obvious in practice; document
  the signature and move on.
- **A failed sensor or a failed switch** in a bonded body. Already accepted by
  ADR 0002 and ADR 0003, correctly — the improvement is detection (finding 24)
  and spares, not serviceability.

### The one thing I would change about the process, not the design

Three of the findings above (1, 13, 23) are **BOM line items that contradict an
ADR, or that an ADR asks for and the BOM does not carry**. `F-POLY` survives a
decision that explicitly replaced it; `R-MOSI-SER` is categorised on the board
opposite to the one its own description names; the key pull-ups the whole key
chain depends on exist in no document at all. The ADRs are unusually good — the
reasoning in ADR 0003 and ADR 0006 is better than most commercial design
documentation — and the gap is between the reasoning and the parts list.

Before E13, **walk the BOM against the ADRs once, line by line, with a
checklist**, and reconcile the category field, the quantity and the value of
every protective component against the ADR that asks for it. That is an
afternoon, it happens before the one board that cannot be revised gets fabbed,
and on this evidence it will find more than this review did.

---

## 5. Figures used, and where they came from

**Read out of the repository and quoted back (`[repo]`):** 3 W lighting clamp;
330–400 mA dev boards; ~120 mA strip quiescent; ~50 mA matrix idle; 960 mA
full-field matrix; 275 mA / 320 mA / 410–430 mA instrument estimates; 1 A
R-78E5.0; 500 mA polyfuse hold; ~500 mA TPS2553 setting; 2 m cable; 0.34 Ω at
24 AWG; 6HP = 30.18 mm; etherCON hole 23.8 mm; 825 g mass; 136 µs loop, 16 µs
per DAC channel, 250 µs period; 0.6 MHz SPI; 1 kΩ output resistors; 10 kΩ in-amp
protection; 100 kΩ differential pulldown; 220 Ω MOSI; 33–68 Ω chain termination;
240R/768R → 5.25 V; DAC8568 A/C zero-scale reset and default-disabled internal
reference; 0.7 × AVDD input threshold; T568B pin mapping; 10–20 K interior rise;
~3 K/W; sensor 0.2–4.7 V and 766 mV/kPa.

**From memory, not verified this session (`[memory]`) — each needs one
datasheet lookup before it is acted on:** the Doepfer 16-pin bus pin ordering;
24/26/28 AWG resistance per metre; 0805 = 125 mW and 1206 = 250 mW; OPA197
short-circuit current ~65 mA; 74AHCT abs-max V_CC = 7 V, input clamp ±20 mA,
V_IH = 2.0 V, active-low OE; 74LVC165 has no internal pull-ups and V_IL ≈ 0.8 V
at 3.3 V; 74HC V_IH = 0.7 × V_CC; DAC8568 abs-max AVDD ≈ 6 V and `CLR` level
behaviour; BAV99 forward rating ~200 mA; SP3012 working voltage ~5 V and
SOT-23-6 channel count; TPS2553 latch-off vs auto-retry and its programmable
limit range; PPTC hold derating ~0.8× at 45 °C; 1N5817 20 V reverse, 0.3–0.4 V
at 300 mA; IEC 61000-4-2 contact model at 150 pF/330 Ω; twisted-pair Z₀ ≈ 100 Ω;
Neutrik etherCON cable retention ~100 N; LM317L minimum load ~3.5 mA and TO-92
θ_JA ≈ 180 K/W; saliva conductivity ~1 S/m; PJ398SM bushing is the sleeve
contact; buck efficiency 85 %; ESP32-S3 boot ~300 ms; Middlebrook input-filter
criterion; hydrophobic-vent water blocking; WS281x failing open more often than
short.

**The three `[memory]` figures the conclusions lean on hardest**, and therefore
the three to check first: the **SP3012 working voltage** (finding 13, severity
SHOWSTOPPER), the **DAC8568 `CLR` level-hold behaviour** (finding 6, on which
the entire watchdog rests), and the **`'125` active-low OE polarity** (finding 4).
All three are single-paragraph lookups.
