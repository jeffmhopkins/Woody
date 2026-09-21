# R5 — How published designs carry power, digital and analog off-board over a cable

**Date:** 2026-09-21
**Scope:** prior art for Woody's 2 m Cat5/etherCON umbilical — Eurorack expanders,
RJ45 interconnects in synth gear, mixed analog/digital bundles, SPI over cable,
wrong-cable faults, wind-controller tethers, and cable mechanics.
**This is not a validation exercise.** Where Woody has reinvented something, or
differs from practice, or has missed a failure mode practice exists to prevent,
that is said plainly. Where Woody is right to differ, that is also said.

## Evidence markers — read these before trusting anything below

The egress proxy blocked **every non-GitHub host** I attempted this session.
Confirmed blocked by the proxy (403 on CONNECT or no route): `doepfer.de`,
`intellijel.com`, `modwiggler.com`, `electro-music.com`, `neutrik.com`,
`ti.com`, `analog.com`, `nxp.com`, `expert-sleepers.co.uk`, `hackaday.com`,
`northcoastsynthesis.com`, `ibiblio.org`, `manuals.plus`, `yamahamusicians.com`,
`en.wikipedia.org`. `github.com` over git-HTTPS works; the GitHub API and
`raw.githubusercontent.com` for arbitrary repos do not.

So the markers are:

| Marker | Means |
|---|---|
| `[schematic]` | I opened and parsed the netlist/schematic file this session. File named. |
| `[source]` | I opened the source file or vendor manual file this session. File named. |
| `[search-summary]` | **A search engine's summary of a page I could not open.** The underlying page is blocked. Treat every number here as unconfirmed hearsay until someone opens the page. |
| `[calc]` | My arithmetic this session, from stated inputs. |
| `[repo]` | From Woody's own repository, with the file named. |
| `[from memory]` | Unverified. Used sparingly and flagged. |

**There is no `[datasheet]` marker in this document**, because every datasheet
host was blocked. Any claim that would need one is marked `[from memory]` or
left open.

---

## Findings vs Woody

| # | What published designs do | What Woody does | Verdict |
|---|---|---|---|
| 1 | **The predecessor had no umbilical.** OWP (2021) is a self-contained Teensy instrument with USB-MIDI out; its only Eurorack hardware is a *separate* LED module with its own CV jacks `[source]` | 8-conductor tether carrying power, analog and SPI | **The umbilical is a brand-new subsystem with zero heritage in this author's own work.** Nothing from 2021 de-risks it |
| 2 | Eurorack expanders use **unkeyed 0.1" IDC ribbon**, orientation documented by a red stripe and *photographs*; Expert Sleepers' off-board pedalboard breakout uses bare 2×12 + 2×5 IDC with no protection parts at all `[schematic]` `[source]` | etherCON, latching, keyed by the plug, with TVS, series R and a shunt Schottky | **Woody is far ahead of Eurorack expander practice.** This is the clearest place Woody is right to differ |
| 3 | Mutable **deleted** its one expander (Shelves) by absorbing it into a wider module `[source]`; Mutable **forbids hot-plug** of the Stages chain in the manual `[source]` | Hot-plug is routine and expected; handled with an LT1641-1 current-limited load switch | **Woody is better than Mutable here**, and is solving a problem Mutable chose to legislate away |
| 4 | RJ45-in-Eurorack exists and is **passive, signal-only**: Doepfer A-180-9, Intellijel Octalink, ADDAC213, DIY RJ45 bridge. The DIY one carries **8 signals and no ground at all** — the shield is the return `[schematic]` | 8 conductors, 4 disciplined signal/return pairs, 3 of them grounds | **Woody's pin discipline is better than all of them.** But none of them carry power, which is where Woody's real risk is |
| 5 | Real A-180-9 users report **nontrivial crosstalk on Cat5e at ~3 m** *"whether sending as twisted pairs of signal/gnd or master ground + signals on other conductors"*, plus **severe drop and crosstalk from high ground resistance** in the bundled cables; Doepfer recommends Cat7/8 and putting audio/CV at one end and digital at the other `[search-summary]` | 2 m, STP preferred, analog at pins 1–2, fastest edge at pins 7–8, power between | **Woody's pin map is the documented mitigation, arrived at independently.** The cable-quality lesson is not yet in the BOM as a *test*, only as a preference |
| 6 | Industry answer to analog over Cat5 is **fully differential, one balanced channel per pair, optional transformer + ground lift** (Radial Catapult) `[search-summary]` | Single-ended BREATH against a dedicated non-current-carrying `AGND`, into an in-amp | **Woody differs, and is right to.** See §3 — but the technique has a name Woody never uses, and naming it would have saved argument |
| 7 | A dedicated sense return for a single-ended analog signal is **standard automotive practice** ("sensor ground", returns only to the ECU, never to chassis, never shared with power return) `[search-summary]` | `AGND` carries no power current; module senses BREATH against it | **Woody is not reinventing anything.** It reinvented the *derivation* at length in ADR 0003 without knowing the technique already has a name and an industry |
| 8 | SPI over Cat5 at 0.5–2 MHz is a **known, asked-about configuration**, and the published answer involves **Schmitt-trigger buffers at both ends** `[search-summary]`; 33 Ω-class series termination to bring driver + R up to the cable's Z₀ `[search-summary]` | 220 Ω on MOSI only; 74AHCT125 (plain buffer); 74AHCT14 held as an E11 contingency | **The value is wrong and Woody already knows** (V4 §F1). My independent calc agrees: **first far-end step 1.89 V against a 2.0 V V_IH** `[calc]`. The Schmitt part should be baseline, not contingency |
| 9 | Mutable's inter-module digital link is **asynchronous UART at 921.6 kbaud** over 3 pins — no clock line, no chip select `[source]` | Synchronous SPI: clock, data and a framing line, all exposed to the cable | **Woody differs and the reason is defensible** (a dumb module needs a DAC-native protocol), but it puts three failure surfaces in the cable where practice puts one |
| 10 | The commercially available tethered Eurorack breath controller (Red Module MINI BC → RSD-01-BC) uses **a stereo 3.5 mm cable**: three conductors `[search-summary]` | Eight conductors, two grounds carrying current, 360 mA | **Woody's umbilical problem is self-inflicted.** The prior art avoids it by keeping the handpiece nearly passive. That is a design choice Woody made, not a constraint |
| 11 | **Akai EWI 3000 (1987) is the direct architectural ancestor**: 10-pin tether carrying GND, +5 V Vref, −12 V, +12 V and **six single-ended analog CVs** (Key, Octave, Vib, Breath, Glide, Bend), pins 5–10 **diode-clamped to 0 and Vref** `[search-summary]` | One analog channel, clamped, with a sense return | **Woody is a more careful version of a 1987 design.** The clamp-every-analog-pin idiom is the one thing the EWI does that Woody only does on BREATH |
| 12 | Every *modern* wind controller — Akai EWI4000s/5000/Solo, NuEVI, NuRAD, MiniWI — is **self-contained, USB/DIN MIDI out, no tether** `[source]` `[search-summary]` | Tethered | **Woody revives an architecture the field abandoned ~1995.** Defensible (the target is a modular rack, not a synth), but it means the modern literature has nothing to offer |
| 13 | The PoE answer to a wrong/crossover cable on an RJ45 power feed is a **diode bridge at the powered device**, explicitly so it is polarity-insensitive when crossover cables are used `[search-summary]` | One shunt SS34 + let the LT1641-1 latch off | **Practice makes the fault a non-event; Woody makes it a safe failure.** A bridge is strictly better and costs ~0.6 V of a ~5 V margin. Worth pricing |
| 14 | Stranded patch cable for anything that flexes is **universal, uncontested practice** `[search-summary]` | `CABLE-UMB` specifies stranded, shielded, consumable, keep spares | **Correct and already decided.** But "stranded" is the floor, not the ceiling — see §7 |

---

## 1. Eurorack expanders: what they actually carry, and what goes wrong

**The idiom is bare 0.1" IDC ribbon, and the published designs do almost nothing
about mis-insertion.**

- **Expert Sleepers, disting NT Pedalboard Breakout** — an off-board unit
  explicitly meant to sit on a pedalboard, i.e. on the floor, metres from the
  rack, being stepped on. `connections.kicad_sch` shows the link is a
  **`Conn_02x12_Odd_Even` plus a `Conn_02x05_Odd_Even`** — plain 24-way and
  10-way IDC ribbon — carrying `+12V`, `GND`, and twelve analog `INPUTn` /
  `OUTn` nets to `PJ612A-A` jacks. The entire component count on that sheet is
  **six resistors: four 0 Ω, one 2 kΩ, one 10 kΩ** `[schematic:
  prior/es/NT-pedalboard-breakout/connections.kicad_sch]`. There is no TVS, no
  series protection on the signals, no reverse protection on the +12 V that
  leaves the rack. A commercial manufacturer ships a powered off-board breakout
  with less protection than Woody puts on one conductor.
- **Mutable Instruments, Shelves expander** — the manual's entire guidance is:
  *"The expander is provided with two cables. Check that they are connected like
  on these pictures (observe the orientation of the red stripe)"*, followed by
  four photographs `[source: midocs/docs/modules/shelves/manual.md]`. **Unkeyed,
  reversible, and documented by photograph.** The eventual fix was not a better
  connector: hardware revision v6 **absorbed the expander into an 18 HP module
  and the cable stopped existing** `[source: midocs/docs/modules/shelves/index.md]`.
- **Mutable Instruments, Stages chain** — a 3-pin cable daisy-chaining up to six
  modules, with the manual instruction *"Make sure your Eurorack system is
  powered off whenever you connect or disconnect units from the chain."*
  `[source: midocs/docs/modules/stages/manual.md]`. **The published answer to
  hot-plug on an inter-module link is to forbid it in the manual.**
- The same manuals show the *power* idiom is identical and equally unkeyed:
  every Mutable manual says only *"the red stripe of the ribbon cable (−12 V
  side) must be oriented on the same side as the 'Red stripe' marking"*
  `[source: midocs/docs/modules/{stages,veils_2020,ripples_2020,elements,frames,peaks,warps,edges}/manual.md]`.
  Doepfer reportedly **recommends against keyed headers on bus boards** because
  incorrectly-keyed boards and cables are common enough that keying can make
  correct connection impossible `[search-summary]`.

**What this means for Woody.** ADR 0004 says *"Reversed ribbon cable is the
classic Eurorack failure and the keying alone is not worth trusting"* and fits
Schottkys behind the 16-pin header `[repo: ADR 0004]`. That is correct and is
**above** the practice documented above, not merely equal to it. The expander
literature offers Woody no technique it does not already have. What it offers is
a warning: the two designers with the strongest reputations in this space
responded to off-board links by **deleting one** and **prohibiting hot-plug on
the other**. Woody is doing neither, so the load switch and the CLR watchdog are
carrying weight that Mutable simply refused to carry.

**One thing Woody has that practice does not, and should keep:** the presence
comparator on the breath line gating all four `OE` pins (ADR 0004). Nothing in
the expander literature I opened has any notion of "is the far end there". The
Stages chain has a 2-second neighbour-discovery phase and a FourCC key
(`'disc'` / `'over'`) to validate a discovery packet, but no hardware presence
detect and **no CRC on the running packets** — a 24-byte `Packet` is accepted on
arrival `[source: eurorack/stages/chain_state.{h,cc}]`.

---

## 2. RJ45 / etherCON in synth interconnect: who, and what happened

**It is an established Eurorack idiom, and in every case I could examine it is
passive and signal-only.**

- **DIY RJ45 Eurorack Bridge** (`rahji/rj45eurorackbridge`, GPL, 2020). I parsed
  the EAGLE netlist. All **eight** RJ45 pins go to the **tips** of eight
  `PJ301M-12` jacks. The jack sleeves tie to a local `GND` net that also lands on
  the RJ45 shell mounting holes `MH1/MH2` — and `GND` **does not appear on any
  of the eight pins** `[schematic:
  rj45bridge/eagle/RJ45_EURORACK_BRIDGE_castellated.sch]`. So the signal return
  is the **cable shield**, which is why the README insists on *shielded* cable.
  The README also names the commercial equivalents: *"a module like Intellijel's
  Octalink, the Doepfer A-180-9, or the ADDAC213 Eurorack Bridge"*, and warns
  *"Don't connect the other end of the ethernet cable to anything other than
  another one of these devices"* `[source: rj45bridge/README.md]`.
- **Doepfer A-180-9 / Intellijel Octalink** are the commercial versions, mutually
  compatible, 8 patch points over one RJ45 `[search-summary]`.

**What went wrong, from users.** This is the most useful material in the whole
topic and I could only get it second-hand:

- *"nontrivial crosstalk on standard cat5e at around 3 meters of length **whether
  sending as twisted pairs of signal/gnd or master ground + signals on other
  conductors**"* `[search-summary]`. Both of Woody's candidate topologies, named,
  at 1.5× Woody's length, reported as a problem.
- *"an 8 foot Cat6 connection was noisy, but running an **extra ground wire**
  attached via spade lugs under the screws of the A-180-9 cleaned it right up"*
  `[search-summary]`. **The fix was more ground, not better cable** — which is
  the common-impedance mechanism ADR 0003 derives, appearing in the wild.
- The bundled cables *"produced severe voltage drop and crosstalk, believed to be
  due to **high resistance on the ground**"* `[search-summary]`.
- Doepfer reportedly recommends **Cat7 or Cat8**, and **audio/CV in the upper
  section, digital in the lower** `[search-summary]`.

**All four of these are unopened pages.** If any one claim in this document
deserves to be verified by a human with an unblocked browser, it is this cluster,
because it is the only field data that exists on Woody's exact cable at Woody's
exact length.

**What it says about Woody.** The last bullet is Woody's pin map, from a vendor,
arrived at independently. Woody's version is stronger: not just "analog at one
end, digital at the other" but *every fast signal paired with its own return*.
The crosstalk reports also do not clearly separate "crosstalk" from "shared-ground
offset" — the extra-ground-wire fix suggests the latter dominated, which is
precisely the failure `AGND` exists to prevent.

**Nobody in this group carries power.** That is the gap. Woody's RJ45 risk is not
the risk any of these products took.

---

## 3. Mixing analog and switching digital in one bundle; is a sense return real?

**Yes. It is standard practice in an industry Woody never cites.**

Automotive ECU wiring: sensors connect **only** to the ECU's dedicated sensor-ground
pins; sensor ground *"must return directly to the ECU sensor ground pins and
should never connect to the chassis or engine block"*; *"the ECU measures the
difference between the sensor signal wire and the sensor ground return, and if
sensor ground shifts due to shared current paths or resistance, the ECU
interprets that offset as a change in sensor value"*; sensors *"must never share
high-current return paths"* `[search-summary]`. That is ADR 0003's argument,
verbatim, for a ratiometric 5 V analog sensor on a long harness next to
high-current loads — the same sensor class Woody uses.

**So Woody is not inventing a technique; it re-derived one.** The cost of not
knowing the name is visible in the repo: ADR 0003 spends several pages arguing
the mechanism from first principles and then has to add a correction that the
rule *"must now be read as 'no *power* current', which is what it always meant"*
`[repo: ADR 0003]`. The automotive formulation ("sensor ground returns to the
measuring device and carries only sensor return current") says that correctly the
first time. **Recommend: name the technique in ADR 0003** — "sensor ground /
Kelvin sense return" — so the next reader recognises it instead of re-litigating
it.

**Does everyone go fully differential? In pro audio, effectively yes.** Radial's
Catapult family carries four balanced channels over one Cat5, one balanced
channel per pair, with transformer-isolated variants and per-bank ground lifts
`[search-summary]`. Whitlock's position, which is the canonical one, is that
unbalanced interfaces fail because *"the grounded conductor … is not only part of
the signal circuit, but also a path for small power line currents"*, and that
*"common-impedance coupling causes virtually all hum and buzz problems in
unbalanced interfaces"* `[search-summary]`. **Woody's scheme is the exact
structural fix Whitlock describes**: remove the return from the power path, and
sense the difference. ADR 0003 already reaches this and correctly declines full
differential on the grounds that it buys ~6 dB at 500 Hz for the cost of a driver.

**Documented crosstalk figures I could obtain:**

| Figure | Source | Confidence |
|---|---|---|
| Cat5e NEXT ≈ 65.3 dB at 1 MHz | `[repo: analog-design-review.md R36]` — asserted there, not re-verified this session | Medium |
| "Nontrivial" crosstalk on Cat5e at ~3 m for Eurorack CV, both topologies | `[search-summary]` | **Low — page blocked** |
| Radial: crosstalk possible "if there are large differences in signal levels through the same cable"; shielded Cat6 better | `[search-summary]` | Low |
| Cat5e nominal mutual capacitance ~52 pF/m within a pair → ~104 pF over 2 m of MOSI-to-CS coupling | `[from memory]` for the per-metre figure; `[calc]` for the product | **Low on the input** |

**No standard specifies intra-pair crosstalk**, because a pair is *designed* to
couple its two conductors. That is the load-bearing fact for §4.

**The one place ADR 0004's reasoning rests on an unstated assumption.** ADR 0004
says the power pair *"acts as a guard"* between the analog pair and the digital
pairs. Geometrically that is right — in T568B, pin 3 sits between AGND (2) and
MOSI (4), and pin 6 sits between CS (5) and SCLK (7). But a guard conductor works
by being a **low AC impedance**, not by being at 0 V, and the instrument's buck
converter makes the power pair the cable's second-noisiest at ~500 kHz. The guard
claim is therefore **conditional on the umbilical +12 V node being well bypassed
at *both* ends**. Woody has that (module bulk + the LC and bulk at the instrument
buck input), so the conclusion holds — but the ADR should say *why* it holds,
because as written it reads as "DC is quiet", which is the thing that is not
true on this particular cable.

---

## 4. SPI over a metre or more

**It is a thing people do, and the published answer is not just a resistor.**

- A TI E2E thread exists titled, essentially, *SPI configuration for long-distance
  transmission at 0.5 MHz to 2 MHz data rates using Cat5 cable and buffers at
  both ends*, around the **SN74LVC3G17 — a triple Schmitt-trigger buffer**
  `[search-summary]`. Woody's band, Woody's cable, and the published topology is
  **Schmitt buffers at both ends**, not a plain buffer.
- General guidance: series termination value should bring **driver output
  impedance + R up to the cable's Z₀** — ~33 Ω quoted for ribbon to reach
  100–130 Ω total `[search-summary]`; place it within ~5 mm of the driver pin
  `[search-summary]`.
- Beyond ~1 m at higher rates the published fallbacks are differential (LVDS /
  RS-422 / "DualSPI"-style tricks) or isolators `[search-summary]`.

**Independent check of Woody's numbers** `[calc]`, inputs: Z₀ = 100 Ω, 2 m Cat5,
velocity factor ~0.65 → one-way delay **T ≈ 10 ns**; ESP32 GPIO source impedance
~30 Ω; far end effectively open (74AHCT125 input).

| Source R | First far-end step | Time to cross AHCT V_IH = 2.0 V | Settled (>95 %) |
|---|---|---|---|
| **220 Ω + 30 Ω = 250 Ω** (as specified) | 3.3 × 100/350 × 2 = **1.89 V** | **3 T ≈ 30 ns** (first step misses by 114 mV) | ~7 T ≈ 70 ns |
| **68 Ω + 30 Ω = 98 Ω** | 3.3 × 100/198 × 2 = **3.33 V** | **1 T ≈ 10 ns**, one clean step | 1 T |

This reproduces the repo's own finding (V4 §F1: *"the far end sits 110 mV below
the 74AHCT125's 2.0 V V_IH for a full round trip and staircases through the
threshold over ~80 ns"*) from independent arithmetic. **It closes at 2 MHz either
way** — 30 ns against a 250 ns bit period — so this is not a showstopper. It is a
margin the design is spending for no benefit, on the one line whose corruption
costs the most.

**The RC model in ADR 0004 is the wrong model and should be retired.** ADR 0004
justifies 220 Ω with *"~200 pF of cable is a ~7.9 MHz corner, so 2 MHz has
margin"*. With a ~1–2 ns GPIO edge and a 20 ns round trip, the line is a
transmission line for every edge it carries (edge rate ≪ 2× propagation delay).
The lumped-C corner is not the governing constraint and gives a falsely
comfortable answer. ADR 0003 makes the same lumped-C argument for BREATH — and
there it is **correct**, because 160 Hz genuinely is lumped. Same sentence, two
different validities; worth distinguishing in the text so the next reader does
not port the wrong one.

**The hazard practice would flag that Woody's own reviews have already found, but
that has not reached ADR 0004: MOSI and CS share a twisted pair.** Everywhere
else in the map Woody applies the correct rule — one signal, one return, one
pair. Pair (4,5) breaks it. The repo's R36 puts a **3.3 V MOSI edge at ~1 V on
CS for ~20 ns against a 0.8 V V_IL** `[repo: analog-design-review.md R36]`, which
is consistent with ordinary backward-crosstalk theory (coupled amplitude ≈ K_b ×
V, duration ≈ 2 T = 20 ns) `[calc]`.

**Why the asymmetry matters more than the review says.** A corrupted *data* bit
is one wrong DAC code, refreshed 250 µs later by the statelessness rule. A
spurious *CS* edge re-frames the 32-bit word — and the DAC8568's 32-bit frame
carries a command field including **software reset, clear-code register write and
internal-reference enable/disable** `[repo: V3-provenance.md item 8, verified
there against the ostenning/dac8568 crate source]`. A mis-framed word can land on a
control command and produce a **sticky** failure that the 4 kHz refresh does not
clear. So of the two signals in that pair, CS is the one that must not be the
victim, and the current map makes it the victim of the cable's most aggressive
aggressor. ADR 0004's pin-assignment section discusses only *pin adjacency at the
connector* and does not mention intra-pair coupling at all.

The repo's R36 already proposes recovering the CS conductor by regenerating SYNC
at the module. **ADR 0004 currently argues the opposite** — that the 220 Ω on
MOSI *"makes SYNC-signal regeneration at the module unnecessary"* — on grounds
that address edge integrity rather than crosstalk. Those two paragraphs need to
be reconciled in the ADR, not left in two documents.

**What practice does when it has more signals than pairs:** it drops a signal.
Mutable's chain is **asynchronous UART at 115200 × 8 = 921.6 kbaud**, 24-byte
packets, over 3 pins `[source: eurorack/stages/chain_state.cc:58-66,
eurorack/stages/drivers/serial_link.cc]`. That is ~0.92 Mbit/s — **more than
Woody's 0.77 Mbit/s payload** — with **no clock line and no framing line in the
cable at all**. Self-clocked async removes both of Woody's cable-borne failure
surfaces. Woody cannot adopt it directly (the module is deliberately dumb and the
DAC8568 speaks SPI), and that is a defensible trade. But it is the answer
practice reaches for, and it is worth recording in ADR 0004 as *considered and
declined*, with the reason, rather than absent.

---

## 5. Plugging in the wrong cable

**Woody's analysis of the rollover lead is correct and I found no one else who
has documented hitting it in a synth context** — because, per §2, no published
RJ45 synth interconnect carries power. Every one of them is passive; a rollover
lead into an A-180-9 just scrambles which CV arrives where.

**Do people avoid RJ45 for this reason? The ones who use it avoid *power*, not
the connector.** The DIY bridge's README warns only about connecting to network
equipment, not about cable type `[source: rj45bridge/README.md]`. The failure
mode Woody found is genuinely specific to putting a rail on a consumable patch
lead.

**The industry that does put power on RJ45 solved it differently, and better.**
PoE powered devices carry **bridge rectifiers at the input**, and the reason given
is exactly Woody's: *"since the output voltage polarity of a full-wave bridge
rectifier is independent of the input voltage polarity, they are often used in PD
input stages to ensure that the PD is biased properly **when crossover cables are
used**"* `[search-summary]`. A compliant PD also tolerates either mode and either
polarity by design.

| | Woody's SS34 shunt | A PoE-style bridge |
|---|---|---|
| Rollover lead inserted | LT1641-1 sees a short, **latches off**, LED out. Instrument dead until the right lead is found | **Instrument just works** |
| Cost | 1 diode | 4 diodes (or 2 in one package), ~0.6 V extra drop `[calc, assuming ~0.3 V/Schottky]` |
| Margin | — | ~11.5 V at the instrument today against a buck needing >6 V `[repo: ADR 0004]`, so ~0.6 V is affordable |
| Diagnosis | Unambiguous: LED out | **Silent** — the wrong lead keeps working and the fault is never found |

**Neither is obviously right, and the choice is a judgement about a one-off.**
The bridge removes the failure; the shunt makes it loud. For an instrument the
author alone will use, "loud and unambiguous" has real value, and the extra drop
sits on top of an instrument current figure ADR 0004 itself calls *"the least
trustworthy number in this document"*. **Recommend: keep the SS34, record the
bridge as the considered alternative, and state the reason** — because the
current text implies no alternative exists, and one does, and it is the
industry's.

**Two cases ADR 0004's table does not cover.**

- The table lists rollover and 10/100 crossover. **A gigabit crossover** swaps
  (1,2)↔(3,6) *and* (4,5)↔(7,8) — the ADR mentions this in passing to reject a
  pin-map reorder, but does not work through its consequence: `SCLK/DIG_GND`
  arrives on the `MOSI/CS` pins and vice versa. Both are 3.3 V logic into 5 V
  AHCT inputs, so it is probably benign, but "probably" is doing work in a table
  whose other two rows are worked out.
- **A damaged or miswired lead** — one conductor open, or a 4-pair plug crimped
  as 2-pair (common on cheap "Cat5e" leads, which sometimes populate only
  1,2,3,6). Losing 4,5 or 7,8 kills SPI, which the CLR watchdog catches. Losing
  pin 2 (`AGND`) leaves the in-amp's IN+ floating except through its 1 MΩ bias
  resistor — **which is exactly the "cable unplugged" row of ADR 0004's presence
  table**, so the comparator reports it. That is a genuinely good property and it
  is worth stating explicitly in the ADR: the presence detect covers partial
  cable failure, not just absence.

---

## 6. Wind controllers and tethered instruments — the closest prior art

**The Akai EWI 3000 tether is the design Woody is re-deriving.**

Reported 10-pin pinout: `1 GND, 2 Vref (5 V) for analog signals, 3 −12 V,
4 +12 V, 5 Key CV, 6 Octave CV, 7 Vib, 8 Breath, 9 Glide, 10 Bend`, with **pins
5–10 diode-clamped at 0 and Vref** `[search-summary — the source page,
modwiggler.com, is blocked; this is the single most important unverified claim in
this document]`.

Read that against Woody:

| | EWI 3000 (1987) | Woody (2026) |
|---|---|---|
| Power up the cable | ±12 V + a 5 V reference | +12 V only |
| Analog down the cable | **Six** single-ended CVs | One (BREATH) |
| Analog return | **One shared GND**, shared with power | **Dedicated `AGND`, no power current** |
| Digital down the cable | None | SPI: 3 lines |
| Protection on analog inputs | **Diode clamp to 0 and Vref on every one** | BAV99 + 10 k on BREATH `[repo: breath-receive-stage.md]` |
| Instrument current | Sensors and op-amps only — milliamps | **~360 mA** of LEDs, AMOLED, WiFi, two MCUs |

**Three things follow.**

1. **The architecture is proven.** A 1987 product ran six analog CVs plus power
   down one unshielded multicore to a handheld instrument that moved constantly,
   and it worked well enough to define a category. Woody's single analog channel
   is less ambitious than the ancestor.
2. **Woody's shared-ground problem is not inherited — it is created.** The EWI
   got away with one shared ground because its handpiece drew almost nothing.
   Woody draws 360 mA because it chose to put WS2815 strips, an AMOLED and WiFi
   in the instrument. `AGND` is the right fix, but the honest framing is that
   **ADR 0003's several pages of common-impedance analysis are the cost of ADR
   0014's lighting decision**, and that trade is not stated anywhere in the repo.
3. **Clamp every analog pin, not just the one you thought about.** The EWI clamps
   all six. Woody clamps BREATH (BAV99 + 10 k, and `D-TVS-BREATH` at 12 V standoff
   on both BREATH and AGND legs — `[repo: bom.csv]`). That is equivalent
   coverage for Woody's single channel. No gap; noted because it is the one
   idiom the ancestor has that a reader might expect Woody to be missing.

**Yamaha WX7 / WX11.** The controller has **no power source of its own**; the
BT7 pack, WT11 or VL70-m supplies power *and* takes the signal over the WX cable,
and the WX5 was the first to carry batteries and a MIDI OUT on the instrument
`[search-summary]`. Same topology as Woody — power up, signal down, one cable —
and again, a handpiece with a trivial current draw. The WX11 cable is described
as a 5-pin mini-DIN `[search-summary]`. I could not obtain a pinout or determine
whether the payload is analog or serial; **that is an open question, and the
yamahamusicians.com thread that appears to hold the answer is blocked.**

**Everything modern is untethered.**

- **Akai EWI4000s / 5000 / Solo** — self-contained, internal synth, battery,
  audio and MIDI out `[search-summary]`.
- **NuEVI / NuRAD** (Berglund, GPL) — Teensy in the instrument, USB and DIN MIDI
  out. The whole breath front end is an MPX sensor with three passives — `C1
  1 µF, C2 0.01 µF, C3 470 pF` — straight into a Teensy ADC pin `[schematic:
  Trasselfrisyr_NuEVI/hardware/nuevipcbs/NuEVI.sch]`. The "breath controller
  breakout" `mpx.sch` is the same sensor plus the same three caps on a small
  board with **three flying pins** — VS, GND, OUT — inside the instrument
  `[schematic: Trasselfrisyr_NuEVI/hardware/bcbreakout/mpx.sch]`. No reference,
  no buffer, no in-amp, no cable.
- **MiniWI / TeensieWI** family — same pattern `[source:
  Trasselfrisyr_MiniWI/]`.
- **`ggood/BreathController`** — Teensy + Freescale sensor, USB MIDI `[source:
  ggood_BreathController/README.md]`.

**And the author's own predecessor is in this group.** Open-Woodwind-Project
(2021) is a **Teensy 3.2 with two MPR121s, a BNO055 and an MPX2010GS on A0**,
compiled *"with MIDI + SERIAL board options"*, sending USB MIDI `[source:
OWP/src/owp/owp.ino:17-26]`. It has a `CONTROLLER_MODE_MODULAR`, but that mode is
a **MIDI behaviour**, not a cable — it changes note/CC handling and disables
breath CC (`stateMachineControllerModular()`, `breath_enabled = false`) `[source:
OWP/src/owp/owp.ino:191-193, 254-276]`. The project's only Eurorack hardware is
a **separate** LED module: an Arduino Micro reading *"Inputs from the Eurorack
3.5mm jacks, dioded to forward only, scaled to 0-5V"* and PWMing six MOSFETs
`[source: OWP/src/owp_led_controller/owp_led_controller.ino:1-40]`.

**So: Woody's umbilical has no ancestry in this author's own work.** Every
sentence about it in ADR 0004 and 0003 is new reasoning about a new subsystem,
and E11 is the first time any of it will be measured. That is worth stating in
the roadmap, because it changes how much slack E11 needs.

**The commercial tethered Eurorack breath controller exists** — Red Module MINI
BC, bundled with an RSD-01-BC 4 HP power/CV output module, connected by **a
stereo 3.5 mm cable** `[search-summary]`. Three conductors. That is the shape of
this product category when someone builds it to sell: power, breath, ground, and
nothing else in the handpiece.

---

## 7. Strain relief, flex life, and stranded patch cable

**Stranded is correct and uncontested**: *"stranded conductors have longer flex
life"*; *"multiple strands distribute bending stress across many wires instead of
concentrating it on one"*; *"the finer the stranding, the more flexible"*; and
RJ45 terminations are designed around stranded for patch use `[search-summary]`.
Woody's `CABLE-UMB` already says *"STRANDED not solid-core: solid core
work-hardens and fractures under constant flexing"* `[repo: bom.csv]` — correct,
and correctly reasoned.

**But "stranded patch cable" is the floor of flex-rated cable, not the ceiling,
and ADR 0004 already says so without following through.** The ADR rejects HR10A
partly because *"Ethernet patch lead is not flex-rated and **will** eventually
fail"* and concludes *"treat cable failure as routine. Keep spares."* That is the
right decision for a one-off — but it means **Woody has accepted a wear-out
failure and mitigated it with spares**, and the mitigation has two holes:

- **A spare only helps if the failure is recognised as a cable failure.** A
  patch lead that fails by intermittent conductor fracture at the boot does not
  fail cleanly. If `SCLK` goes intermittent, the CLR watchdog fires and the rack
  parks — diagnosable. If **`AGND`** goes intermittent, the presence comparator
  trips (per ADR 0004's own table) — diagnosable. If **`PWR_GND`** or **`+12 V`**
  goes intermittent, the load switch latches — diagnosable. **If `MOSI` or `CS`
  goes intermittent, nothing in the design notices**: the DAC gets refreshed with
  garbage at 4 kHz and the instrument plays wrong notes. That is the one
  conductor-level failure with no detector, and it is on the pair that already
  has the crosstalk problem. A parity or checksum bit in the 32-bit frame is not
  available (the DAC8568 owns the frame), but **a periodic readback is not
  possible either — MISO was deleted**. Worth recording as an accepted risk in
  ADR 0004 rather than being silently absent.
- **The strain relief is at the connector, and the ADR knows where the load
  goes.** ADR 0004 already specifies bracing the etherCON to the PCB so *"it puts
  the load path into the board rather than the panel"*, and notes the instrument
  end needs a backing plate because the D-series is rated to **4 mm maximum panel
  thickness** `[repo: ADR 0004, bom.csv]`. Good. The remaining gap is the
  **cable-side** boot: an etherCON carrier (NE8MX-class) provides a proper
  strain-relieved boot on the *plug*, but only if the lead is assembled into one.
  A plain patch lead pushed into an etherCON D chassis socket gets the chassis
  latch and **none of the plug-side strain relief** — the flex still lands on the
  moulded boot of a consumer patch lead. Since the ADR's whole cable argument is
  "it flexes every time it is played", this is the detail that decides whether
  "consumable" means *annual* or *monthly*. **The `Open` section already defers
  the etherCON variant to E12/M7; the cable-end variant belongs in that same
  decision and is currently not mentioned.**

---

## What Woody should change

1. **Move the Schmitt-trigger receiver from contingency to baseline.** The one
   published configuration matching Woody's exact case — SPI at 0.5–2 MHz over
   Cat5 — uses Schmitt buffers at both ends `[search-summary]`. ADR 0004 holds
   `74AHCT14` as an E11 contingency. Make it the default and let E11 *remove* it
   if the scope is clean, because the failure it prevents (CS re-framing) is the
   one with a sticky consequence. The part count is identical.
2. **Fix the MOSI series value to ~68 Ω, at the driving end only, on all three
   lines** — and put the fault-limiting resistance at the module end where it does
   not fight the termination. V4 §F1 already specifies exactly this; **ADR 0004
   still says 220 Ω** and still justifies it with the lumped-RC corner. The ADR is
   the document people read.
3. **Reconcile ADR 0004 with R36 on the MOSI/CS pair.** The ADR says the 220 Ω
   makes SYNC regeneration unnecessary; R36 says recover the CS conductor by
   regenerating SYNC. One of those has to go. My read is that R36 is right, and
   the asymmetry in §4 above (a corrupted data bit self-heals in 250 µs; a
   mis-framed control word may not) is the argument that settles it.
4. **Add intra-pair MOSI→CS crosstalk to E11's acceptance criteria as a named
   measurement.** E11 currently reads as "SPI at 2 MHz and the breath pair over
   the real cable" `[repo: ROADMAP.md:52]`. Scope `CS` at the module end, at full
   length, while MOSI is toggling, and record the glitch amplitude against
   V_IL = 0.8 V. That is a five-minute measurement that decides items 1 and 3.
5. **Record the PoE bridge rectifier as the considered-and-declined alternative
   to the SS34 shunt**, with the reason (silent tolerance vs. loud, unambiguous
   failure, on a one-off the author diagnoses himself). The current text reads as
   though no alternative exists.
6. **Name the sense-return technique in ADR 0003** — "sensor ground", the
   automotive convention — so the rule stops being re-derived and re-corrected.
7. **State the guard assumption in ADR 0004's pin-map section**: the power pair
   guards because +12 V is a low AC impedance at both ends, which requires the
   instrument-end bulk and LC to actually be there. As written it reads as "DC is
   quiet", which is false for this cable.
8. **Record `MOSI`/`CS` intermittency as the one conductor failure with no
   detector**, since MISO and readback are gone. Accept it explicitly rather than
   leaving it absent.
9. **Fold the cable-end etherCON variant into the E12/M7 connector decision.**
   The chassis latch is not the strain relief that matters for a lead that flexes
   every time the instrument is played.
10. **Add "verify the cable" to the E11 procedure, not just "specify the cable".**
    The A-180-9 field reports blame **ground resistance in the bundled lead**
    `[search-summary]`. Four-wire-measure the DC resistance of the actual lead
    end-to-end before trusting anything measured through it, and do it for the
    spares too. A bad lead will otherwise look like a design fault.

## What Woody should keep

1. **etherCON over bare 8P8C.** The whole published RJ45-in-Eurorack group uses
   bare jacks and none of them are hand-held. The reasoning in ADR 0004 —
   retention tab, no strain relief, the instrument moves while played — is sound
   and is the reason Woody is not in that group.
2. **`AGND` as a non-current-carrying sense return.** Validated twice over: it is
   textbook automotive sensor-ground practice `[search-summary]`, and the
   documented A-180-9 field failure is *the alternative* — shared-ground
   resistance, fixed by a user bolting on an extra ground wire `[search-summary]`.
3. **Declining full differential.** Radial goes differential because it carries
   four wide-band audio channels and cannot control the far end. Woody carries one
   160 Hz channel into an in-amp with gigaohm inputs. The 6 dB is not worth a
   driver, and ADR 0003's reasoning for that is correct.
4. **The pin map.** Analog at one end, fastest edge at the other, power between.
   Doepfer reportedly gives the same advice for the A-180-9 `[search-summary]`;
   Woody derived it independently and applied it more strictly. The only defect is
   the pair that has to hold two signals, and that is an arithmetic constraint
   (five signals, three grounds, four pairs), not a reasoning error.
5. **The current-limited load switch and hot-plug tolerance.** Mutable's published
   answer to this problem is *"make sure your Eurorack system is powered off"*
   `[source: midocs/docs/modules/stages/manual.md]`. Woody engineers it instead.
   On an instrument that gets plugged in and unplugged as part of playing, that is
   the correct and the harder choice.
6. **The presence comparator on the breath line.** Nothing in the expander or
   RJ45 literature I opened has any concept of far-end presence. Woody's version
   reports six things at once for one comparator, and — per §5 — it also covers
   partial cable failure on the analog pair.
7. **The `CLR` watchdog.** Same: no published Eurorack inter-module link I opened
   has a stale-data timeout. Stages accepts a 24-byte packet on arrival with no
   CRC `[source: eurorack/stages/chain_state.cc]`.
8. **"The cable is a consumable."** Stranded patch cable is the right choice and
   accepting wear-out with spares is the right posture for a one-off. Practice
   agrees on the material; ADR 0004's own honesty about the flex rating is the
   part most designs skip.
9. **The 2 m tether carrying analog, power and SPI is genuinely unusual, and
   Woody is entitled to build it.** Nothing in the published Eurorack world does
   all three. The one design that did something close — the EWI 3000 — did
   *more* analog on *less* protection, with one shared ground, and shipped.
   Woody's version is better engineered than its ancestor on every axis I could
   compare. The risk is real, it is concentrated at E11, and it is the right risk
   to be taking.

---

## Open questions I could not close

| Question | Why it is open | How to close it |
|---|---|---|
| The EWI 3000 10-pin pinout | Source page (`modwiggler.com`) blocked by proxy | Open the "Hacking the EWI controller" thread, or an EWI 3000/3020 service manual |
| A-180-9 / Octalink field crosstalk numbers | All ModWiggler pages blocked | Open the A-180-9 threads; this is the only field data on Woody's exact cable |
| Doepfer's own A-180-9 cable and pin-map guidance | `doepfer.de` blocked | Open `doepfer.de/a180_9.htm` |
| Neutrik etherCON current rating per contact (ADR 0004 asserts ~1.5 A) | `neutrik.com` blocked | Open the etherCON datasheet; the ~360 mA figure has ample margin either way, so this is low-priority |
| Yamaha WX7/WX11 cable payload — analog or serial? | `yamahamusicians.com`, `ibiblio.org` blocked | Would sharpen §6 but changes no decision |
| Cat5e intra-pair mutual capacitance per metre | Used `[from memory]` ~52 pF/m | Any Cat5e cable datasheet; only affects the size of the §4 estimate, not its sign |
| Whether anyone has published a *powered* RJ45 synth tether | Found none in an hour of searching; absence of evidence only | — |
