# Woody — contradiction audit (A1)

Scope read: `README.md`, `ROADMAP.md`, all fourteen ADRs plus `docs/decisions/README.md`,
`docs/reference/latency-budget.md`, `docs/reference/ks33-geometry.md`, `hardware/bom.csv`,
`config/key-layout.yaml`, `firmware/README.md`, `LICENSE`. `docs/review/` and `docs/log/`
were read for context only and are not cited as contradictions; neither are the many
places where an ADR quotes its own superseded text to explain a reversal.

Findings are ordered by severity. Every one is a pair of statements each written as
*current* design.

---

## 1. The real-time board is in two different places

**Severity: SHOWSTOPPER**

> `docs/decisions/0013-two-mcu-split.md`, "Physical placement: three zones":
> "| **Middle** | Real-time MCU |" … "| **Bottom** | IMU, umbilical connector, power
> entry and 3.3 V regulation, protection |" … "### Mid-body placement halves the
> worst-case run … Longest run drops from 14 inches to 8."
> Its distance table costs the mid-body option "IMU 175 mm" and "Umbilical 205 mm".

> `docs/decisions/0014-lighting.md`, "The 8×8 matrix":
> "The real-time board sits at the very bottom tip of the instrument — where ADR 0007
> wants it for maximum acceleration sensitivity — with its LED face directed out through
> a window in the oak underside."

> `docs/decisions/0007-imu-selection.md`, "Two things to carry forward":
> "This also settles the board's position rather than leaving it to convenience:
> **the very bottom tip**."

> `docs/decisions/0008-display-selection.md`, "This does not undo the two-MCU split":
> "the display belongs at the top, the real-time board mid-body (ADR 0013)."

**Why they cannot both be true.** The IMU is *on* the real-time board — ADR 0007 selects
the Waveshare ESP32-S3-Matrix specifically because "the onboard IMU *is* the final IMU"
(carrier is passive), and the BOM row `U-IMU` says "QMI8658C (onboard U-MCU-RT)". A board
cannot be mid-body while its soldered-down IMU is in the bottom zone 175 mm away. The
same board carries the 8×8 matrix that ADR 0009 and ADR 0014 require to shine through a
tail window "below the right-hand key run", and the USB-C edge that ADR 0009 requires at
the tail face. Mid-body placement puts the matrix under the inter-hand gap and the U-bolt.

**Which is correct.** *Bottom tip.* It is forced by three independent constraints written
after ADR 0013's zone table — onboard IMU (0007), tail matrix window + carrier cutout +
USB-C slot (0009, 0014), and the analog star point "on the bottom cluster board … at the
sensor and reference, immediately adjacent to the umbilical connector" (0003). ADR 0013's
mid-body analysis predates the board selection that made IMU position and board position
the same variable.

**Impact if unresolved.** The tail window, the ~22 mm carrier cutout, the USB-C slot and
all loom lengths are cut into a stack that is bonded shut. Getting this wrong is the
"one unrecoverable mistake" the ROADMAP names.

**Confidence: high.**

---

## 2. The breath sensor is at the top on a short tube, and at the bottom on a 400 mm tube

**Severity: SHOWSTOPPER**

> `docs/decisions/0013-two-mcu-split.md`, "Physical placement: three zones":
> "| **Top** | Display board (AMOLED + WiFi), **breath sensor + ADC on a short tube**,
> upper key cluster |"

> `docs/decisions/0009-enclosure-construction.md`, "Breath tube access":
> "The only stack requirement is **access to clear it without disassembly** … just a
> serviceable path to the sensor end of a **short tube near the top**."

> `docs/decisions/0003-breath-sensing-path.md`, "Sensor placement: at the bottom, with
> the real-time board": "**Decided after review. This reverses an earlier placement whose
> justification turned out to be false.**" … "| **400 mm (chosen)** | **1.17 ms** |
> **214 Hz** |"

> `ROADMAP.md`, E2: "Sensor + ADC at the bottom with the real-time board (ADR 0003)".
> `hardware/bom.csv`, `TUBE`: "~400mm - the sensor sits at the BOTTOM with the real-time
> board (ADR 0003), **not at the top**".
> `docs/reference/latency-budget.md`: "| Tube propagation | **~1.17 ms** | 400 mm."

**Why they cannot both be true.** Same component, two ends of a 457 mm body. The tube
length differs by 13× (30 mm vs 400 mm) and the latency budget differs by 1.08 ms —
0.09 ms vs 1.17 ms, which is the *largest single term* in the whole budget. ADR 0003 also
deletes the internal analog run on the strength of the bottom placement, and ADR 0009's
own consequences section relies on that deletion ("It is resolved by the sensor moving to
the bottom"), so ADR 0009 contradicts itself two sections apart.

**Which is correct.** *Bottom, 400 mm tube.* ADR 0003 is the owning ADR, it reverses the
top placement explicitly and gives the falsified reason (74x165 `QH` cannot share MISO),
and the ROADMAP, BOM and latency budget all follow it. The log confirms it as decision #1
of the review resolution. ADR 0013's zone table and ADR 0009's "Breath tube access"
paragraph are unpatched leftovers.

**Confidence: high.**

---

## 3. The breath receiver is both an INA134 difference amp and an INA821/828 in-amp

**Severity: MAJOR**

> `docs/decisions/0004-cv-interface-module.md`, "Module parts, chosen for build ease":
> "**INA134 for the breath difference amp.** On-chip matched resistors give ~90 dB CMRR
> against the 60 dB needed (ADR 0003), with no external matching network to place or
> match."

> `docs/decisions/0003-breath-sensing-path.md`, "So separate the grounds…":
> "**But the receiver is a true instrumentation amplifier (INA821 / INA828), not a
> difference amplifier.** A difference amp's CMRR is set by **source-impedance balance,
> not by the chip** … this design's own protection resistor and pulldown would have left
> roughly **19–34 dB against the 60 dB the scheme needs.**"

> `hardware/bom.csv`, `U-DIFFRX`: "INA821 or INA828 … Buffered GOhm inputs make source
> impedance irrelevant. Absorbs the ~2.13x gain stage. REF pin takes the ambient-zero
> injection".

**Why they cannot both be true.** They are different parts with different topologies and
incompatible downstream consequences. ADR 0004's "~90 dB CMRR" is the datasheet figure for
a balanced source; ADR 0003 shows the actual source impedance (≥3.3 kΩ unmatched
protection resistor) drops the same part to 19–34 dB, i.e. 26–41 dB short of requirement.
The two also disagree on where the ambient zero is injected: ADR 0003 and ADR 0006 both
put DAC channel 6 into "the in-amp's `REF` pin", which the INA134 arrangement does not
provide in the same way, and ADR 0003 credits the in-amp with absorbing the 2.13× gain
stage that ADR 0004 still budgets separately.

**Which is correct.** *INA821/INA828.* ADR 0003 owns the breath path, does the arithmetic,
and the BOM implements it; the review-resolution log records it as decision #3. ADR 0004's
parts list was not updated.

**Confidence: high.**

---

## 4. The umbilical SPI clock is 0.6 MHz, 1 MHz and 2 MHz — and at 0.6 MHz the 4 kHz loop does not close

**Severity: MAJOR**

> `docs/decisions/0004-cv-interface-module.md`, "What goes over the cable":
> "SCLK, MOSI, CS      SPI to the DAC, **~2 MHz**"
> …"Revised conductor budget": "SCLK      / DIG_GND     SPI to the DAC, **~1 MHz**"
> …bandwidth table: "| **Breath analog, 5 channels at 2 kHz** | **0.32 Mbit/s** |
> **~0.6 MHz** |"

> `docs/reference/latency-budget.md`, "Breath digital copy":
> "| SPI to DAC over umbilical | ~50 µs | **2 MHz** |"
> …same file, characterisation table: "**~0.6 MHz** now that breath is analog".

> `ROADMAP.md`, E11: "SPI (**~0.6 MHz**) and the analog breath pair over the real cable".

**Why they cannot both be true.** These are three values for one wire, differing by 3.3×.
Worse, the loop budget is built on the highest of them and fails at the lowest. The
latency budget's rule 1 states: "one pass costs ADC 24 µs + key chain 16 µs + **six DAC
channels 96 µs** = **136 µs**, against … 250 µs" at 4 kHz. Six DAC8568 writes are 6 × 32 =
192 bits; 192 bits in 96 µs is exactly 2 Mbit/s. At the ~1 MHz of the revised conductor
budget the same six writes take 192 µs (total 232 µs of a 250 µs period — 93 % duty), and
at ~0.6 MHz they take **320 µs, which exceeds the entire 250 µs loop period**. The 4 kHz
loop and a 0.6 MHz umbilical cannot both be satisfied.

**Which is correct.** The *link* arithmetic (0.32 Mbit/s → ~0.6 MHz "at 50 % use") is a
throughput estimate, not a clock specification, and it was never reconciled with the
per-pass serialisation budget. The buildable number is the latency budget's **2 MHz**
(also ADR 0001's "comfortable at 2 MHz SPI over twisted pair"); nothing electrical
objects, since ADR 0004 itself says plain single-ended SPI over twisted pair is
unremarkable here. E11 should be specified at the clock the loop needs, not at the
average-throughput figure.

**Confidence: high** that the documents disagree; **medium-high** that 2 MHz is the
intended resolution.

---

## 5. Mod and pitch channels update at 4 kHz, but every bandwidth table still assumes 2 kHz

**Severity: MAJOR**

> `docs/decisions/0006-cv-channel-allocation.md`, "Channels do not share an update rate":
> "| Pitch | **4 kHz**, plus **immediate update on note change** |" … "| Mod 1–4 |
> **4 kHz** | See below — 2 kHz leaves an audible image |" … "**The table used to say
> 2 kHz and it was wrong twice over.**"

> `docs/decisions/0003-breath-sensing-path.md`, "It pays for itself on the digital link",
> and `docs/decisions/0004-cv-interface-module.md`, "Bandwidth is modest again":
> "| **Breath analog, 5 channels at 2 kHz** | **0.32 Mbit/s** | **~0.6 MHz** |"
> ADR 0004 text: "the digital link carries only pitch, four mod channels and the zero
> offset **at 2 kHz**".

**Why they cannot both be true.** The payload is computed from the rate. Five channels ×
32 bits × 2 kHz = 320 kbit/s, which is the 0.32 Mbit/s printed. At the 4 kHz ADR 0006
mandates it is **640 kbit/s**, and the derived clock figure doubles from ~0.6 MHz to
~1.2 MHz. Every "0.32 Mbit/s / ~0.6 MHz" cell in ADR 0003, ADR 0004, and the ROADMAP's
E11 acceptance criterion is therefore half the true requirement. (ADR 0003 also says
"5 channels" while listing six loads — pitch, four mods and the zero offset.)

**Which is correct.** *4 kHz*, per ADR 0006, which owns channel rates, argues it from the
zero-order-hold image (−12.6 dB at 2 kHz vs −19.2 dB at 4 kHz) and from the loop budget
that "already assumes six DAC channels serviced every 250 µs pass". The bandwidth tables
in ADR 0003/0004 were written before that revision and were not recomputed.

**Confidence: high.**

---

## 6. Configuration lives on the instrument's display, and configuration lives on a phone

**Severity: MAJOR**

> `README.md`, "Output": "**Mod 1–4** — assignable; source, scale, offset, curve and slew
> **configured on the instrument's own display**".

> `docs/decisions/0006-cv-channel-allocation.md`: "Per-channel source, scale, offset,
> curve and slew are **set on the instrument's display**." … "with firmware selecting the
> actual range per channel **from the instrument's display**: 0–5 V, 0–8 V, 0–10 V, ±5 V,
> ±2.5 V" … "**Bipolar is opt-in per channel**, set explicitly **from the display**".

> `docs/decisions/0012-configuration-interface.md`, "Decision": "**Configure over WiFi
> from a phone, using a web app served by the instrument.**" … "the display … becomes a
> **status** display".
> `docs/decisions/0008-display-selection.md`: "The display is now a **status** surface …
> It no longer has to host a navigable four-channel routing matrix".
> `ROADMAP.md`, F7: "Status display … **Status only — config lives on the phone**".
> `firmware/README.md`: "Config is a web app served from the display board's flash over
> SoftAP, **not a menu system** … The display shows status only."

**Why they cannot both be true.** A four-channel routing matrix editor either exists on
the panel or it does not. ADR 0012 rejects it explicitly ("Driving all of that through a
small display and a couple of buttons is a bad experience and a large amount of
firmware"), and ADR 0013 goes further — the display board "renders what it is told",
persists nothing, and under the selected LilyGO board the display has *no input device at
all* (ADR 0008: "**The base version, not the Plus.** Touch is redundant with configuration
on a phone"). There is literally no mechanism by which a player sets a curve "from the
display".

**Which is correct.** *Phone/web app.* ADR 0012 is the owning ADR, ADR 0008 and ADR 0013
are both written downstream of it, and the ROADMAP and firmware README follow. README.md
and the four sentences in ADR 0006 are stale.

**Confidence: high.**

---

## 7. The instrument's local rail is 3.3 V and also 5 V

**Severity: MAJOR**

> `docs/decisions/0005-power-architecture.md`, "Decision": "The instrument takes +12V up
> the cable and **derives 3.3V locally with a small buck converter**."

> `docs/decisions/0005-power-architecture.md`, "The rail that matters is 5 V, not 3.3 V":
> "An earlier revision of this ADR specified a 12 V to 3.3 V buck. **That is wrong** …"
> and its power tree: "12V→5V buck ──┬── display board 5V pin / real-time board 5V pin /
> LED data level shifter" plus "**3.3 V does not need its own converter.**"

> `docs/decisions/0014-lighting.md`, "Rail: use a 12 V strip": "The instrument has +12 V
> from the umbilical and **derives 3.3 V locally** (ADR 0005)" — yet the same ADR later
> says "The matrix hangs on the **R-78E5.0-1.0** alongside both dev boards".

> `docs/decisions/0013-two-mcu-split.md`: bottom zone is "power entry and **3.3 V
> regulation**", while the carrier parts list in the same ADR contains "**R-78E5.0
> regulator module**" (a 5 V part).
> `docs/decisions/0004-cv-interface-module.md`: "power (**3.3V derived locally** in the
> instrument, small buck)".
> `README.md`: "**The instrument's own 5 V regulator**, which is a 1 A part".
> `hardware/bom.csv`, `U-BUCK`: "R-78E5.0-1.0 … 12V to 5V switching regulator module".

**Why they cannot both be true.** ADR 0005 proves the 3.3 V version is unbuildable: the
MPXV4006DP swings to 4.7 V and "a buffer running on 3.3 V would clip the top 30 % of the
breath range", and the dev boards want their `5V`/`VBUS` pins driven. The 1 A budget
arithmetic in ADR 0014 and the BOM ("dev boards ~330-400 mA plus a full-field matrix at
960 mA would be 1.36 A") is 5 V arithmetic and is meaningless on a 3.3 V rail.

**Which is correct.** *5 V, R-78E5.0-1.0*, with 3.3 V taken from the dev boards' own
regulators. Four documents were not swept when the rail changed — including ADR 0005's
own Decision paragraph, which its own later section calls wrong.

**Confidence: high.**

---

## 8. The carrier is a custom ESP32-S3 board, and the carrier is passive with dev boards plugged in

**Severity: MAJOR**

> `docs/decisions/0001-mcu-and-board-partitioning.md`, "Decision": "**ESP32-S3**, as a
> bare module on a custom carrier — **not a dev board** — with satellite boards
> distributed along the body." Consequences: "**Custom carrier design needed eventually:
> USB-C, ESD protection, boot/reset, 3.3V regulation.**"

> `docs/decisions/0013-two-mcu-split.md`, "Build approach": "**Do not design a custom
> ESP32-S3 carrier.** That means taking on the module footprint, USB-C, ESD, boot and
> reset circuitry … **Instead: keep both dev boards as modules, on a carrier that has no
> MCU on it at all.**"
> `ROADMAP.md`, E13: "**Passive** carrier: dev boards plug in … No MCU, no USB, no RF on
> it (ADR 0013)."
> `hardware/bom.csv`, `J-USB` / `U-ESD-USB` / `SW-BOOT`: status "not-needed" —
> "Dev boards carry these. **Only required if a custom MCU carrier is ever built**".

**Why they cannot both be true.** ADR 0001's status header only claims that "partitioning
[was] revised by ADR 0013 — display and WiFi moved to a second MCU"; it does not withdraw
the bare-module decision, and its Consequences still direct someone to design the exact
circuitry ADR 0013 forbids. The two also cascade: ADR 0007 depends on the passive carrier
("the onboard IMU *is* the final IMU"), which is false on a bare-module carrier.

**Which is correct.** *Passive carrier with dev boards*, per ADR 0013, the ROADMAP and the
BOM. ADR 0001's Decision/Consequences need the same "superseded by 0013" treatment its
header gives the partitioning.

**Confidence: high.**

---

## 9. Licensing is decided, open, and not yet decided

**Severity: MAJOR** (it is the repository's public licence statement)

> `docs/decisions/0011-licensing.md`: "**Status:** Accepted … **Three share-alike
> licences, one per kind of work.**"
> `LICENSE`: "Woody is released under three licences, one per kind of work."
> `README.md`, "## Licence": "Three share-alike licences … **GPL-3.0-only** for firmware,
> **CERN-OHL-S-2.0** for hardware …"

> `docs/decisions/README.md`, index: "| [0011](0011-licensing.md) | Licensing | **Open** |"
> `README.md`, "## Licensing" (the last section of the file): "**Not yet decided** — see
> [ADR 0011](docs/decisions/0011-licensing.md). The previous project's firmware was
> GPLv3."

**Why they cannot both be true.** A repository either has a licence grant or it does not,
and `README.md` makes both claims 25 lines apart, under near-identical headings. A reader
who scrolls to the bottom is told the work is unlicensed, which legally defaults to "all
rights reserved" — the opposite of the stated intent.

**Which is correct.** *Decided.* ADR 0011 is Accepted, the `LICENSE` file and all three
texts in `LICENSES/` exist and are complete. Delete the stale `## Licensing` section of
the README and set the index row to Accepted.

**Confidence: high.**

---

## 10. Protection currents are already sized at 500 mA against a draw the documents say is unknown and may be 430 mA

**Severity: MAJOR**

> `docs/decisions/0004-cv-interface-module.md`, "It passes the instrument's current":
> "| +12 V | ~320 mA (45 module incl. the DAC regulator, ~275 instrument) — **estimated,
> and a review put it nearer 410–430 mA. Measure at E6 before sizing the load switch** |"
> … "**The instrument figure is the least trustworthy number in this document.** … 
> **Nothing downstream should be sized from it.** **E6 measures the real draw with a
> current probe**, and the load switch's current limit is set from that measurement."

> `hardware/bom.csv`, `U-LOADSW`: "TPS2553DBV … **Adjustable limit set ~500mA**."
> `hardware/bom.csv`, `F-POLY`: "PPTC 1206 **500mA hold**".
> `ROADMAP.md`, E6 bench table: "**Inrush with a current probe** … Sizes the load switch's
> current limit **from measurement rather than from a guess**".

**Why they cannot both be true.** One document says the limit is unset pending E6; the BOM
sets it. And the number chosen cannot satisfy the stated load: against the review's
410–430 mA the current limit sits 16–22 % above nominal draw, and a PPTC's *hold* current
is a room-temperature figure that derates roughly 25–50 % inside a body documented to run
10–20 K above ambient — i.e. a 500 mA hold part is at or below the instrument's own steady
draw. Both devices would then nuisance-trip during ordinary playing, and ADR 0014's
brownout-latch failure chain is exactly the scenario a marginal polyfuse creates.

**Which is correct.** ADR 0004's rule. Leave both values TBD-at-E6 in the BOM, and expect
the sized parts to land nearer 1 A hold / ~800 mA limit rather than 500 mA.

**Confidence: high** on the contradiction; **medium** on the suggested magnitudes
(they depend on the E6 measurement).

---

## 11. The controller "carries no analog signal path" — which two ADRs explicitly call false

**Severity: MINOR**

> `README.md`, "What it is": "The controller is **purely digital and carries no analog
> signal path** and no battery." (its table also lists Controller Domain "Digital")

> `docs/decisions/0004-cv-interface-module.md`, "Decision": "**It does not become purely
> digital, and an earlier version of this line said it did.** That claim was already false
> when written and **it let a review finding through unchallenged.** The instrument still
> carries the pressure sensor, a precision reference, two op-amp stages and the analog
> drive onto the umbilical."
> `docs/decisions/0003-breath-sensing-path.md`: "The claim that let the finding through is
> worth correcting explicitly … the instrument is **not** 'purely digital with no analog
> signal path'. It carries the sensor, a precision reference, two op-amp stages and the
> analog drive. **It is where most of the project's analog risk lives.**"

**Why they cannot both be true.** The BOM places `U-REF-BREATH` (REF5050), `U-BUF`
(OPA2197 dual), `R-ADCDIV` and `C-AA-ADC` in the *controller* category, and the umbilical
carries a `BREATH`/`AGND` analog pair out of it.

**Which is correct.** The ADRs. The README sentence is the exact wording both ADRs were
edited to kill, and it is load-bearing: it is what caused a reviewer to propose a fix that
assumed the instrument had no analog section.

**Confidence: high.**

---

## 12. The key chain is 74LVC165A and 74HC165

**Severity: MINOR**

> `docs/decisions/0001-mcu-and-board-partitioning.md`: "**the part stays 74LVC165A** …
> LVC is kept because it is specified natively at 3.3 V and is already selected — but it
> is kept **with item 4 above**, the series termination."
> `hardware/bom.csv`, `U-KEYS`: "74LVC165A … Kept for its native 3V3 spec, WITH 33-68R
> series termination. **74HC165 is a drop-in on the same footprint if E4 says otherwise**."

> `hardware/bom.csv`, `CAP1-n` (keycap row!) notes: "**74HC preferred over LVC** for ~2x
> input noise margin, not for speed - over an unterminated loom LVC's faster edges are
> worse."
> `ROADMAP.md` E4, `docs/decisions/0005-power-architecture.md` power tree,
> `docs/decisions/0008-display-selection.md`, `config/key-layout.yaml`
> ("One **74HC165** per cluster: 4 devices, 32 bits"), `docs/decisions/0001` Consequences
> ("The **74HC165** chain suits this geometry well"): 74HC165.

**Why they cannot both be true.** Same four devices, two families. They are pin-compatible,
so this is not fatal — but the BOM asserts both preferences in two different rows, and the
"74HC preferred" note is stranded in the *keycap* line where nobody sourcing shift
registers will see it.

**Which is correct.** *74LVC165A with 33–68 Ω series termination*, per ADR 0001's decision
and the `U-KEYS` row. The generic "74HC165" phrasing elsewhere is shorthand that should
read "74x165" (ADR 0001 and ADR 0013 already use that form in their analysis sections);
the `CAP1-n` note is a stale paste and contradicts the part actually specified.

**Confidence: medium-high** (the loose "74HC165" usages may be intended generically; the
`CAP1-n` note is unambiguously contradictory).

---

## 13. ADR 0006 populates six DAC channels and seven DAC channels

**Severity: MINOR**

> `docs/decisions/0006-cv-channel-allocation.md`, "Decision": "Two further DAC channels
> drive offsets rather than jacks … **Seven of eight channels used, one spare.**"
> Two paragraphs later: "Use an **octal** 16-bit DAC (DAC8568 or AD5676) and **populate
> six.**"

> `hardware/bom.csv`, `U-DAC`: "**Populate 7 of 8**: pitch, 4 mods, breath ambient-zero,
> mod offset."

**Why they cannot both be true.** The ADR's own allocation table lists channels 1–7 in use
(pitch, mod 1–4, breath ambient-zero, shared 2.5 V mod offset). "Populate six" is the
pre-offset-channel count and is arithmetically inconsistent with the table above it.

**Which is correct.** *Seven*, per the table and the BOM. (Note that the six-channel figure
also propagates into the latency budget's "six DAC channels 96 µs" loop pass — which is
correct there, since channel 7 is "written once at boot".)

**Confidence: high.**

---

## 14. ADR 0009 gives the instrument two different masses

**Severity: MINOR**

> `docs/decisions/0009-enclosure-construction.md`, first "### Mass": "| **2.25 in** |
> **~778 g (1.72 lb)** |" (with 2.50 in listed at ~825 g)

> `docs/decisions/0009-enclosure-construction.md`, second "### Mass" (immediately below,
> same heading, "Rough estimate at this envelope"): aluminium 157 + oak 131 + oak 174 +
> acrylic 164 + electronics 200 = "| **Total** | **~825 (1.8 lb)** |"

**Why they cannot both be true.** Same envelope, same build, 47 g apart — and the second
table's total is exactly the first table's figure for the *2.50 in* width that was not
chosen. Everything else about the two tables agrees (both assume 200 g of electronics),
so one of them is a width column read off by one.

**Which is correct.** The itemised table (~825 g) is checkable and sums correctly; the
first table's 2.25 in row appears to be the stale one, or the width sensitivity in the
first table is overstated. Either way one heading should go. Consequence is cosmetic —
both land in the stated 1.5–2 lb EWI band.

**Confidence: medium** on which is right; **high** that they conflict.

---

## 15. Two ADR status headers disagree with the index

**Severity: MINOR**

> `docs/decisions/README.md`, index: "| 0007 | IMU selection | Accepted (**board open**) |"
> and "| 0008 | Display selection | Accepted (**board open**) |"

> `docs/decisions/0007-imu-selection.md`: "**Status:** Accepted. **Board selected:
> Waveshare ESP32-S3-Matrix.**" — and its Open section lists only routing defaults.
> `docs/decisions/0008-display-selection.md`: "**Status:** Accepted. **Board selected:
> LilyGO T-Display-S3 AMOLED** (base, not Plus)." — Open section: "**Nothing blocking.**"

**Why they cannot both be true.** The index is the first thing a reader consults for
status. Both boards are in `hardware/bom.csv` with status `selected`, and ROADMAP E1 names
both by part number as the bring-up hardware.

**Which is correct.** *Selected.* Update the two index rows to plain "Accepted".
(The same index also still carries 0011 as Open — see finding 9.)

**Confidence: high.**

---

## 16. `firmware/README.md` contradicts itself twice

**Severity: MINOR**

> "Architecture constraints … they are not negotiable": "**Display renders on the other
> core, on its own SPI host.** A display refresh must never block the output loop."
> Four bullets later, in the same list: "**WiFi and the display are on the other MCU.**
> They cannot preempt the output loop."

> "Data, not code": "Both live in NVS and are **editable from the display and over USB**."
> Two sections later: "## Configuration lives on a phone … **The display shows status
> only.**"

**Why they cannot both be true.** Under ADR 0013 the display is on separate silicon, so
there is no "other core" running it and no display SPI host on the real-time board at all
— ADR 0007's pin map assigns SPI2 to the DAC+ADC and SPI3 to the key chain, with nothing
left for a panel. And a display that "shows status only" on a non-touch board (ADR 0008:
base, not Plus) cannot be the thing config is edited from.

**Which is correct.** The two-MCU statements. The "other core" bullet is inherited from
ADR 0001's pre-0013 core split; "editable from the display" is the same stale claim as
finding 6, as is ADR 0010's "editable — over USB from a host tool (**F7**)", which also
points at the wrong milestone: F7 is "Status display"; the config app is **F5**.

**Confidence: high.**

---

## 17. Smaller cross-reference and numeric mismatches

**Severity: NIT** (grouped; each is a single stale number)

1. **`docs/decisions/0014-lighting.md`**: "Two data lines cost one extra GPIO, against
   roughly **17 broken out and 12 needed** on the real-time board (ADR 0007)" — ADR 0007's
   pin table and the BOM both say **16 broken out, 14 needed, 2 spare**. The cited ADR
   says something different from the citation.
2. **`docs/decisions/0013-two-mcu-split.md`**, "Considered and rejected": "not expected at
   **13 pins** and one job" — its own table two pages up says 18 chip pins / 14 broken out.
3. **6HP panel width**: `hardware/bom.csv` `PANEL` says "6HP x 3U (**30.0** x 128.5mm)";
   the `J-UMBILICAL` row in the same file, ADR 0004 and ROADMAP E12/M4 all say
   **30.18 mm** ("`(6 × 5.08) − 0.3`"). The 0.18 mm matters only because the etherCON
   leaves 3.19 mm of aluminium each side, which is the number the bracing decision turns
   on.
4. **Key-chain read time**: `docs/reference/latency-budget.md` key-path table says
   "74HC165 chain read **< 10 µs** via SPI DMA"; rule 1 of the same file uses "key chain
   **16 µs**"; ADR 0001 says "Full chain reads in **~32 µs at 1 MHz**". Three values for
   32 bits of shifting; they reconcile only at three different clock rates.
5. **`ROADMAP.md`**: "both inform wiring and plumbing that get **sealed inside a bonded
   body at M6**" — but M8, which comes after M6 and M7, is defined as "Assembled but
   **not bonded** … **Nothing closes until this passes**". The bonding point is after M8.
6. **`docs/decisions/0009-enclosure-construction.md`**: "the fix is narrowing toward
   55 mm, **which costs the two-column layout**" — the same ADR's "Nothing on the
   instrument binds the width" section says "**Two-column key clusters. Void:** keys run
   in a single line (ADR 0010)". There is no two-column layout left to cost.
7. **`hardware/bom.csv`**, `SW1-n`: "**Plate cutout must be measured.**" … and, in the
   same cell, "Datasheet and STEP model published by Gateron - **use them, do not caliper
   the housing**". ADR 0002, `docs/reference/ks33-geometry.md` and `config/key-layout.yaml`
   all state the cutout as settled at 14.0 × 14.0 mm.
8. **`docs/decisions/0003-breath-sensing-path.md`**, sensor-placement thermal bullet: "this
   is a gauge sensor with a temperature-dependent offset **whose zero is captured once at
   cold startup**" — contradicted by the same ADR's "Continuous auto-zero absorbs anything
   slow" and by ADR 0006's "**A zero captured once at startup is wrong by the time the
   first piece ends.**"

**Confidence: high** on each mismatch; low consequence individually.

---

## Documents that are internally consistent

- **`config/key-layout.yaml`** — self-consistent and consistent with ADR 0010, ADR 0009
  and ADR 0001: 5 + 6 + 4 + 3 = 18, 15 `note` / 3 `control`, 4 × 8 = 32 bits with 14
  spare, envelope 457 × 57 × 38 mm, cutout 14.0 mm, `plate_thickness: null` correctly
  mirroring the one genuinely open mechanical item. (Only the generic "74HC165" naming
  in finding 12 touches it.)
- **`LICENSE`** — agrees with ADR 0011 line for line, including the `config/` dual grant.
  The conflict in finding 9 is entirely in the README and the ADR index, not here.
- **`docs/reference/ks33-geometry.md`** — self-consistent, correctly scoped as evidence
  rather than specification, and its "the vendor drawing supersedes it" clause is honoured
  by ADR 0002.
- **`docs/decisions/0010-key-layout-as-data.md`** and **`0011-licensing.md`** — no internal
  contradictions found (0010's only defect is the F7/F5 milestone reference in finding 16).
- **`docs/decisions/0012-configuration-interface.md`** — internally consistent; its
  relaxation banner is properly marked as a revision rather than asserted as two facts.

## Cross-cutting observation

Findings 1, 2, 6, 7 and 8 are all the same failure: a decision was reversed in its owning
ADR, the ROADMAP and BOM were swept, and **a sibling ADR's summary table or zone diagram
was not**. The stale statements survive specifically in tables and diagrams rather than in
prose, because the prose was what got edited. A mechanical pass over every table, power
tree and ASCII diagram in `docs/decisions/` — checking each cell against the owning ADR —
would likely close all of them and is worth doing before M4 CAD starts, since four of the
five determine geometry that gets bonded shut.
