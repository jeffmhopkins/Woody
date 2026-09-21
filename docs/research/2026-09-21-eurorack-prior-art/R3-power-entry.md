# R3 — Eurorack power entry, protection and distribution as actually practised

**Date:** 2026-09-21
**Scope:** prior art for ADR 0004 ("Power entry, and why this module is not a typical
one", "Grounding: one origin, named") and ADR 0005 (whole document); BOM rows
`D-REVPOL`, `FB-IN`, `C-BULK-RAIL`, `U-LOADSW`, `R-ILIM`, `U-REG-DAC`, `R-REG-SET`,
`J-PWR-EURO`, `LED-PANEL`.

## Evidence key, and what it cost to get

Every claim below carries one of four markers. They are used strictly:

- `[schematic]` — I opened the file in this session. The file is named. Where the
  source is a binary EAGLE `.sch` I could only extract part strings, not net
  topology, and that limitation is stated inline.
- `[datasheet]` — a manufacturer parameter. **Every vendor datasheet domain was
  blocked** (ti.com, analog.com, vishay.com, murata.com, product.tdk.com,
  bourns.com, littelfuse.com, digikey, mouser, lcsc all returned `000`/blocked).
  So `[datasheet]` here means *a parameter recovered through web-search summary of
  a datasheet or distributor parametric page*, never a PDF I opened. Treat these
  as needing one confirming look at the real PDF before a part is ordered.
- `[docs]` — vendor or community documentation. **doepfer.de, modwiggler.com,
  mutable-instruments.net, expert-sleepers.co.uk, befaco.org, northcoastsynthesis.com,
  rossum-electro.com, monome.org, aisynthesis.com and web.archive.org are all
  blocked to direct fetch from this session.** Where a `[docs]` claim comes from a
  search-engine summary of a blocked page rather than the page itself, it says so.
  Nothing below is a substituted guess for a blocked source.
- `[from memory]` — general engineering knowledge, unverified in this session.

**Reachable:** github.com and raw.githubusercontent.com (clone + raw fetch), and
the WebSearch tool. That is all. The schematic corpus below is therefore the
strongest evidence in this document, and it is deliberately doing most of the work.

### The corpus I actually opened

| Source | Files | What it is |
|---|---|---|
| Mutable Instruments, `pichenettes/eurorack` | 12 × `*/hardware_design/pcb/*.sch` (binary EAGLE — strings only) | Braids, Frames, Kinks, Links, Marbles, Peaks, Plaits, Stages, Tides2, Veils, Volts, Yarns |
| Winterbloom, `wntrblm/Castor_and_Pollux` | `hardware/mainboard/power.kicad_sch`, `hardware/mainboard/mainboard.pdf`, `hardware/expander/expander.kicad_sch` | Fully annotated commercial module, current ratings written on the schematic |
| Winterbloom, `wntrblm/Micronova` | `hardware/board/board.pdf`, `hardware/bus_board/bus_board.kicad_sch` | A small commercial Eurorack PSU + bus board |
| Expert Sleepers, `expertsleepersltd/hardware` | `power-bus/power_bus_v1-schematic.pdf`, `midi-breakout/dm4_midi_brk_v1-schematic.pdf` | Bus board (gives the authoritative 16-pin pin/net grouping); a breakout fed over a cable |
| `bpcmusic/telex` | `hardware/TELEXo/board/Telex-O Schematic.pdf` | A DAC856x + OPA417x + 74AHCT125 CV expander — architecturally the nearest neighbour to Woody's module in the whole corpus |
| `mzuelch/CATs-Eurosynth` | 63 `.sch`/`.kicad_sch` (CGS, MFOS, YuSynth, Haraldswerk, HAGIWO, Slim/Standard Line) | Census of DIY-canon module power entry |
| `apfaudio/eurorack-pmod` | `hardware/eurorack-pmod-r3.5/power_conn.kicad_sch` | Digital/analog module with split grounds |
| `Bemeier/bmcv` | `pcb/power.kicad_sch` | Polyfuse-only entry |
| `soundslikefrank/miditron` | `hardware/power_ref.kicad_sch` | Schottky + bead + three local regulators |
| `Alloyed/KitsBlips` | `kicad/_templates/eurorack/power.kicad_sch` | Someone's *template* for a Eurorack module — i.e. what a designer considers the default |

---

## Findings vs Woody

| # | Woody's position | What practice does | Verdict |
|---|---|---|---|
| 1 | Series 1N5817 Schottkys on +12 V and −12 V | Dominant idiom. 38 of 63 DIY schematics carry 1N5817/1N5819 in series; Mutable ships 1N5819HW on every module examined; Winterbloom ships two "30 V 500 mA" series diodes `[schematic]` | **Right, and it is genuinely the standard** |
| 1b | Split +12 V into **two** diodes so instrument current does not modulate the analog branch's Vf | No published module does this — because no published module passes 360 mA of someone else's load through its entry diode. The mechanism is real and the fix is 20 cents | **Right to differ.** Not reinvention; there is nothing to reinvent |
| 1c | No fuse anywhere at the module | Series diode *plus* a polyfuse is common where the designer thought about it: Telex-O (2 × 0805L020, 200 mA hold), eurorack-pmod (2 × 200 mA), Mutable Frames and Veils both carry a PTC-1206 `[schematic]` | **Differs, and the reasoning has a hole.** The load switch guards the *umbilical* branch only. The analog branch, the −12 V rail and the bus +5 V pin have no overcurrent protection at all |
| 2 | 16-pin shrouded keyed header; a reversal "kills the buffer and nothing else" | On a **16-pin** connector a 180° reversal shorts bus +12 V, +5 V and CV together through the module's own ground net. That is a rack-level fault, not a module-level one. Doepfer's own warning is "both the module and the power supply may be damaged" `[docs, search summary of blocked doepfer.de]` | **Under-analysed.** Woody's own analysis is for the 10-pin case; it uses a 16-pin header |
| 3 | ≥1 A bead, 1206/1210; "the common 0805 600 R bead is ~300 mA and a saturated bead is a wire" | Conclusion right, stated reason wrong. 0805 600 Ω exists at 600 mA (BLM21AG601SN1D, signal-line) *and* at 2.3 A (BLM21SP601SN1D, power-line) `[datasheet, distributor parametric]`. Winterbloom annotates bead current on the schematic: `600R@100MHz 500mA` on ±12 V, `200mA` on the analog 3.3 V `[schematic]` | **Right conclusion, wrong rule.** Package size does not set rated current; the *series* does. A 1210 signal-line bead can still be a 300 mA part |
| 3b | 47 µF bulk per branch at entry | Corpus is 10 µF (CATs DIY canon), 22 µF (Castor & Pollux, eurorack-pmod, bmcv, miditron) `[schematic]`. 47 µF × 4 is ~2–5× the norm | **Justified by current, but note the side effect:** entry capacitance is what makes hot-plugging a module dangerous, and Woody has more of it than anyone |
| 3c | "A real LC, 10–47 µH, between the umbilical node and the buck input" | Micronova puts a genuine `L1 10 µH 800 mA` + 100 µF LC on its DC input `[schematic]` — so LC is practised. But an undamped LC feeding a *constant-power* switching load is the textbook negative-resistance oscillator | **Incomplete.** No damping network is specified anywhere in ADR 0004/0005 |
| 4 | Bus +5 V is "a requirement, not an option" for the 74AHCT125 | The opposite is the settled practice. Doepfer: +5 V is needed by "a few older modules" only `[docs, search summary]`. Mutable makes 5 V locally with a µA78L05 on Marbles, Plaits, Stages, Tides2; miditron uses LM1117-5.0; the KitsBlips *template* has a 78L05; Telex-O's 10-pin header takes ±12 V and GND only `[schematic]` | **Wrong way round, and it costs more than Woody thinks** — see §4 |
| 5 | LT1641-1 + external FET, latch-off at 1.0 A, 50–100 ms programmed ramp | Nothing in Eurorack does this. A GitHub code search for `eurorack` + `TPS2553 OR LT1641 OR eFuse OR TPS259` returns **only Woody's own repo** `[docs]`. The practised idiom for sourcing power out is *convert the voltage and let the converter's own limit be the limiter* (Expert Sleepers FH-2: 500 mA at 5 V from an on-board regulator) `[docs, search summary of blocked expert-sleepers.co.uk]` | **Right to differ in kind** — Woody passes the rail through unconverted, so it has no free limiter — **but the implementation has a hard error: the SOT-23 FET is far outside SOA** (§5) |
| 5b | Window "roughly 0.9–1.13 A"; `R-ILIM` value from E6's load measurement | The LT1641 sets its limit on a 50 mV sense threshold `[datasheet, search summary]`, whose own tolerance is of order ±10–15% `[from memory]` | **The acceptance window is narrower than the part's accuracy.** Same mistake Woody already diagnosed and fixed on the LM317 divider, repeated one row down the BOM |
| 6 | LM317LZ at ~5.21 V off its own protected +12 V, divider selected by measurement at E7 | Local linear regulation straight off +12 V is exactly what everyone does. Castor & Pollux runs an LD1117-3.3 from +12 V and writes the dissipation (0.8 W) and junction-temperature arithmetic on the schematic `[schematic]`. Telex-O generates its DAC's 5 V locally rather than from the bus `[schematic]` | **Right, and conventional.** Two omissions, both small (§6) |
| 7 | Star ground: `PWR_GND`, `DIG_GND` and analog return on separate copper, joined at the inlet ground pin | The precision-analog designs in the corpus use **one ground net** and split the *supply* instead: Mutable has a single `GND` plus `VCC`/`VDDA`; Castor & Pollux has a single `GND` with `+3.3VA` fed through a bead from `+3.3V` `[schematic]`. Split grounds appear in eurorack-pmod (`GND`/`GNDD`) and as a two-symbol tie point in the KitsBlips template `[schematic]` | **Half right.** Giving `PWR_GND` its own copper is correct. Giving a 2 MHz SPI return its own copper, separate from the plane its signals run over, is the classic split-plane EMC mistake |

---

## 1. Reverse-polarity protection

### It really is the community standard, and the census is not close

`[schematic]` Across the 63 `.sch`/`.kicad_sch` files in `mzuelch/CATs-Eurosynth`
(a curated collection of the DIY canon — CGS, MFOS, YuSynth, Haraldswerk, HAGIWO,
plus the maintainer's own Slim Line and Standard Line boards), I counted by regex:

| Idiom | Files containing it |
|---|---|
| Series Schottky (`1N5817`/`1N5819`) | **38 / 63** |
| Ferrite bead | **0 / 63** |
| Any fuse or PTC | **0 / 63** |
| TVS / clamp | **0 / 63** |
| P-FET reverse protection | **0 / 63** |
| Local regulator (78L05/LM317/1117/MCP17) | 3 / 63 |

(The 25 files without a Schottky are mostly control/panel sub-sheets with no power
entry on them. The point stands: where there is a power entry, there is a series
Schottky and usually nothing else.)

The typical entry, quoted from files I opened `[schematic]`:

- `Slim Line/Buffered Multiple SMD`: `1N5817` + 2 × `1N5819WS`, `10u/16` × 2, `100n` × 4
- `Slim Line/Clock Divider`: `1N5819` + 2 × `1N5819WS`, `10uF/16V` × 2, `100nF` × 4
- `HAGIWO/Sync LFO`: `1N5817`, 2 × `1N5819`, `10u` × 2, `100n` × 5
- `Alloyed/KitsBlips` *template* (`kicad/_templates/eurorack/power.kicad_sch`): a
  10-pin Eurorack header, `D1`/`D2` = `1N5819` in series with +12 V and −12 V, one
  polarised cap per rail, and an `L78L05_TO92` making +5 V from +12 V. When a
  designer writes down their default, that is the default.

Commercial confirmation `[schematic]`:

- **Mutable Instruments** — `1N5819HW` appears in the strings of Braids, Frames,
  Links, Marbles, Peaks, Plaits, Stages, Tides2, Veils and Yarns. (Binary EAGLE:
  I can prove the part is in the design, not where it sits. Given the part and the
  application, series entry is the overwhelming reading.) Several also carry
  `BAT54S` and a "Ceradiode" ESD suppressor, and Frames and Veils additionally
  carry a `PTC-1206` resettable fuse.
- **Winterbloom Castor & Pollux** — `D1`, `D2`, both annotated `30V 500mA`, in
  series with +12 V and −12 V, each followed by a `600R@100MHz 500mA` bead and a
  `22u 16V` bulk cap. Read directly off `hardware/mainboard/mainboard.pdf` page 2.
- **Telex-O** — the power block is literally captioned *"POWER with reverse
  polarity protection"* and contains a `BAS70-04` dual Schottky plus two
  `0805L020` polyfuses, on a 10-pin header carrying only `+12V 9*2`, `GND 3*6`,
  `-12V 1*2`.

### What Doepfer actually says

`[docs — search-engine summary of doepfer.de/a100_man/a100t_e.htm and
doepfer.de/faq/a100_faq.htm; the domain is blocked to direct fetch from this
session, so this is second-hand and should be re-read from the source]`

Doepfer's published guidance is about **mechanics, not circuitry**:

- the coloured wire marks −12 V and must point to the bottom, without exception;
- if the red wire does not point down, do not connect the module: "both the module
  and the power supply may be damaged";
- bus boards from third parties with *polarised* box headers are explicitly not
  allowed, because they can force the A-100 cable in the wrong way round, which
  "will destroy the module and void the warranty";
- the A-100Bus V6 (2019) boxed headers carry a keying gap, and the nose must point
  right.

And on protection diodes: Doepfer added reverse-polarity diodes to new modules
around 1996, having originally left them off on cost grounds, and the change was
driven by customers and other manufacturers rather than by a specification — diodes
being cheaper than warranty support for abuse `[docs, search summary of blocked
modwiggler.com thread]`.

So: **Doepfer recommends a keyed connector and a red stripe. It does not publish a
protection-circuit recommendation.** The series Schottky is a *community* standard,
not a Doepfer one. ADR 0004 says "Eurorack practice for module power entry is well
settled, and converges on..." — that is true of practice, and Woody should not
attribute it to Doepfer.

### The alternatives, and their documented failure modes

`[docs, search summaries — the primary pages (sound-au.com AN013,
northcoastsynthesis.com, rossum-electro.com, modwiggler threads) are all blocked]`
plus `[from memory]` for the mechanisms:

| Scheme | Cost | How it fails |
|---|---|---|
| **Series Schottky** (Woody) | Vf, always, on every milliamp | Does not protect against *offset* insertion (the one-row-shifted cable), where rails land on ground pins. Does not current-limit. Vf drifts with load and temperature — which is precisely why Woody split the +12 V diode |
| **Shunt diode to ground + fuse** | No steady-state drop | The fuse must actually clear before the diode dies. A 1 A Schottky into a 2 A supply with a 1.5 A polyfuse holds a *sustained* short until the PTC warms up; the diode is the sacrificial element and commonly goes first. Also: clamping to ground places a dead short across the rack's supply, browning out every other module in the case |
| **P-FET / ideal diode** | ~20 mV instead of ~350 mV; more parts | Gate protection (a Zener + resistor) is mandatory at 12 V or the Vgs rating is exceeded; the body diode conducts during reverse until the FET turns off; no current limit either. The corpus contains **zero** examples in 63 DIY schematics |
| **Nothing** | free | ICs go first (TL084/LM386 are the commonly named casualties), electrolytics are reverse-biased, and 3.3 V regulators "puff" `[docs, search summary of blocked modwiggler threads]` |

**Where this lands for Woody.** Series Schottky is right. Three diodes rather than
two is right, and the ~80 mV Vf-modulation argument in ADR 0004 is sound and, as far
as this corpus shows, original — no published module has this problem because no
published module has this load.

One correction to ADR 0004's framing: it lists "a small series resistor of 2.2–10 Ω"
as the common alternative to a bead. **In this corpus that idiom does not appear at
all** — 0 of 63 DIY files and none of the commercial designs use a series resistor
on the rails. The paragraph ruling it out on drop grounds is arguing against
something practice already does not do.

---

## 2. What a reversed ribbon actually destroys

### The pinout, from a schematic rather than from memory

`[schematic — expertsleepersltd/hardware/power-bus/power_bus_v1-schematic.pdf]`
The Expert Sleepers bus board wires each 2×8 header as: pins 1,2 = −12 V; pins 3–8 =
GND; pins 9,10 = +12 V; pins 11,12 = +5 V; pins 13,14 = CV bus; pins 15,16 = Gate bus.
The 10-pin subset is the first five columns: −12 V, GND, GND, GND, +12 V.

### The 10-pin case, and the 16-pin case, are different accidents

A 180° in-plane reversal of a 2×N IDC maps pin *p* in column *c*, row *r* to the pin
in column *N+1−c*, other row. That is my derivation from the pinout above, not a
quotation:

**10-pin reversed** — module pin 1,2 (−12 V) ← bus 10,9 (+12 V); module 9,10 (+12 V)
← bus 2,1 (−12 V); module GND pins 3–8 ← bus GND pins 8–5. **Ground survives; the
two rails swap.** With series Schottkys: the +12 V diode blocks (≈12 V reverse,
inside the 1N5817's 20 V VRRM `[datasheet, search summary]`), and the −12 V diode is
*forward*-biased by the −12 V now on that pin, so the module quietly powers its
negative rail and nothing else. This is the case the community means by "the diodes
saved it", and it is the case Woody's protection is designed for.

**16-pin reversed** — module GND pins 3–8 ← bus pins 14,13,12,11,10,9 = CV, CV,
+5 V, +5 V, +12 V, +12 V. **The module's ground plane shorts the rack's +12 V, +5 V
and CV bus together.** The module's own rails sit at −12 V relative to its ground,
and its +5 V input pin sits 12 V *below* its ground. Series Schottkys on ±12 V do
nothing about any of this. This is why Doepfer's warning names the power supply as a
casualty and not just the module `[docs, search summary]`.

Woody uses a 16-pin shrouded keyed header (`J-PWR-EURO`), and it must, because it
needs the bus +5 V pin. ADR 0004's sentence —

> A reversed or row-offset ribbon that puts +12 V onto that pin kills the buffer and
> nothing else, which is why the +5 V entry gets no protection network of its own.

— is wrong in three ways:

1. On a true reversal the +5 V pin does not see +12 V; it sees roughly −12 V with
   respect to the module's own ground. (Either kills a 74AHCT125; the stated
   mechanism is not the real one.)
2. "Nothing else" ignores that the 74AHCT125's inputs and outputs are tied to the
   DAC's SPI pins and to the presence comparator's OE net. With VCC 12 V below the
   input pins, the buffer's input clamp diodes conduct, and the DAC's outputs and
   the pull-up network source that current. `[from memory]` The containment claim
   needs series resistors in the SPI lines to be true, and Woody has one
   (`R-MOSI-SER`, 220 Ω) on exactly one of the four nets.
3. The bus +5 V is *also* the pull-up rail for the LM393 presence comparator
   (ADR 0004). See §4 — that is not a $0.30 exposure.

**What protects against it, in practice:** keying and shrouding, and nothing else.
The whole community answer is mechanical. `[docs, search summary]` "Non-keyed
connectors will inevitably be plugged in backwards, no matter how clearly the
correct orientation is marked"; the advice is shrouded headers at **both** ends of
the cable, and never to trust the red stripe. Woody already specifies a shrouded
keyed header, which is the correct and complete answer to this question — and it is
worth noting that most modules use a **10-pin** header, which (per the mapping above)
is itself a protection measure, because the 10-pin reversal cannot short the rails
together through the module's ground.

---

## 3. Filtering: what is actually fitted

`[schematic]`, all read this session:

| Design | +12 V / −12 V entry after the diode | Bulk | Local decoupling |
|---|---|---|---|
| CATs DIY canon (63 files) | nothing | 10 µF/16 V | 100 nF |
| Castor & Pollux | `FB1`, `FB2` = 600 R@100 MHz, **500 mA** | 22 µF/16 V | 100 nF |
| eurorack-pmod | `L1`, `L2` "FERRITE" + 200 mA polyfuse | 22 µF | 100 nF |
| bmcv | 4 × `470R` FerriteBead + `SMD1206P110TF` polyfuse (1.1 A) | 22 µF, 10 µF, 1 µF | 100 nF, 10 nF |
| miditron | 2 × `Ferrite_Bead` "100 @ 100 MHz" + 2 × `1N5819` | 22 µF, 10 µF, 1 µF | 100 nF |
| Telex-O | 2 × `0805L020` polyfuse + `BAS70-04` | 10 µF | 100 nF |
| Micronova (PSU side) | `F1` 1.5 A polyfuse, `TH1` MOV (optional), `D1` "BARRIER 3A" Schottky, **`L1` 10 µH 800 mA + `C1` 100 µF** | 22 µF, 10 µF, 4.7 µF per rail | — |

So: ferrite beads are common in the SMD/commercial half of the corpus and absent
from the DIY half. RC is absent. LC appears once, on a PSU's DC input.

### The bead current-rating finding is right, but the rule Woody wrote is wrong

`[datasheet — distributor parametric pages via search; murata.com blocked]`

- `BLM21AG601SN1D` — 0805, **600 Ω @ 100 MHz**, rated **600 mA**, DCR 0.21 Ω.
  Murata's `BLM21A` series is the *signal-line* family.
- `BLM21SP601SN1D` — 0805, **600 Ω @ 100 MHz**, rated **2.3 A**. `BLM21S` is a
  power-line family.
- `BLM21PG600SN1D` — 0805, **60 Ω @ 100 MHz** (not 600 — the part-number digits are
  a trap), rated **3–3.5 A**, DCR 20 mΩ.

`[schematic]` Winterbloom's Castor & Pollux annotates its beads with current:
`600R@100MHz 500mA` on ±12 V and `600R@100MHz 200mA` on the analog 3.3 V branch.
A commercial designer writing the rated current next to the impedance is the
strongest possible corroboration that Woody's *concern* is a real one that
practice takes seriously.

But the rule in `FB-IN` — "1206 or 1210", "the common 0805 600 R part is ~300 mA" —
will not reliably produce a ≥1 A bead. Package and impedance do not determine rated
current; the *series* does, and both a 600 mA and a 2.3 A part exist at 0805 600 Ω.
Buying a 1210 signal-line bead gets you a 1210-sized 300 mA part.

**"A saturated bead is a wire" is also the optimistic failure mode.** `[from memory]`
The worse one is that a bead run near rated current loses impedance *and* its DCR
rises with temperature, so the branch's DC drop grows under exactly the load that
caused it. On the umbilical branch at 580 mA through a bead whose DCR is a few
hundred milliohms, that is tens of millivolts of load-dependent drop *in series with
the supply the instrument's buck regulates from* — harmless — but the same bead sits
on the analog branch feeding the pitch chain, where the whole point of splitting the
diode was to keep load-dependent drops out.

### The LC in front of a switching load needs a damping network

`[from memory]` ADR 0004 prescribes "10–47 µH of inductance, not a bead" between the
umbilical node and the buck input. An LC filter feeding a regulated switching
converter is the standard negative-resistance instability: the converter presents
`−V²/P` at its input, and if the filter's output impedance peak at resonance
approaches that magnitude, the loop oscillates. The usual fix is a damping leg — a
series R + C across the filter capacitor, R of order the filter's characteristic
impedance — and it is not optional at 10–47 µH with 47 µF. Add the ~2–3 µH of loop
inductance in 2 m of Cat5 and the 470–1000 µF ADR 0004 puts at the WS2815 feed
points, and the umbilical is itself an underdamped LC feeding a constant-power load.

Nothing in the corpus addresses this, because no Eurorack module has a switching
load two metres away. It belongs on E11's list.

### Bulk capacitance, and the inrush the community organises around

`[docs, search summary]` The universal Eurorack rule is: **never plug a module in
with the rack powered.** The stated reason is inrush into the module's uncharged
bulk capacitance, which both damages the module's own parts and sags the bus enough
to glitch logic in other modules.

Woody's entry bulk is 4 × 47 µF = 188 µF against a corpus norm of 10–22 µF per rail.
That is defensible given the current, but it is worth recording explicitly: at rack
power-on Woody's module presents several times the usual inrush, and on a
Micronova-class supply (rated +12 V 1 A, max ~1.5 A `[schematic]`) that is a
measurable fraction of the budget. It also means the module must never be
hot-installed, which is the normal rule anyway.

---

## 4. The +5 V bus rail

### Nobody trusts it, and the reason is documented

`[docs — search summary of blocked doepfer.de pages]`

- +5 V is required by "a few older A-100 modules" only: A-113 (old version),
  A-190-1, A-191.
- A-100PSU3 supplies +12 V 2000 mA, −12 V 1200 mA, +5 V 2000 mA (up to 4000 mA with
  a fuse change).
- The A-100AD5 low-cost +5 V adapter is good for **100 mA**, and it derives that 5 V
  from the +12 V supply.
- The A-100 miniature supply gives **50 mA** at +5 V.

`[schematic]` Winterbloom's Micronova, a current small commercial supply, rates its
rails +12 V 1 A (max ~1.5 A), −12 V **300 mA**, +5 V **500 mA**, ripple 75 mVpp,
with +5 V coming from a `VX7805-500` fed from the DC input.

`[docs, search summary]` The community position is explicit and circular: users
complain when a module needs +5 V, so manufacturers regulate down from +12 V so the
module works in any case, so cases have less reason to supply +5 V.

### What designers do instead — every single one in the corpus

`[schematic]`

- **Mutable Instruments**: `ua78l05` appears in the strings of Marbles, Plaits,
  Stages and Tides2, with the TI µA78L05 datasheet URL embedded. A 78L05 from +12 V.
- **KitsBlips template**: `L78L05_TO92` from +12 V, annotated "provides up to 100mA
  / can swap with L7085 for 1.5A".
- **miditron**: `LM1117-5.0` for +5 V, `LM1117-3.3` for +3V3, `ADP150` for +3.3VA —
  three local regulators, all from the rack's ±12 V.
- **Castor & Pollux**: `LD1117-3.3` from +12 V, with "Power dissipated: 0.8W",
  "Maximum rated junction temperature: 125 °C", "Junction to ambient thermal
  resistance: 100 °C/W", "Maximum temperature rise without heatsink: 80 °C" written
  on the sheet.
- **Telex-O**: 10-pin header taking `+12V`, `GND`, `-12V` only; its 5 V comes from a
  `REF02AU` and its 3.3 V from an `MCP1703`. **Telex-O runs a DAC8564 and four
  74AHCT1G125 buffers and still does not touch the bus +5 V.**

That last one is the closest analogue in the corpus to Woody's module — DAC856x,
OPA417x output amps, AHCT125 level shifting, precision references — and it makes
every low-voltage rail locally.

### Why this matters more to Woody than the ADR admits

ADR 0004 justifies keeping the level shifter on the bus rail because "the only thing
hanging on the unprotected bus +5 V pin is a $0.30 buffer". But ADR 0004 also
specifies the presence comparator as "an LM393 half, open-collector, **pulled to the
bus +5 V rail**, driving all four `OE` pins" — and the panel LED off the same signal.

So loss of the bus +5 V (a case without the rail, a blown PSU fuse, a reversed
ribbon, a bad crimp on pins 11/12) takes out, together:

- the level shifter, so SPI stops reaching the DAC;
- the OE pull-up, so the OE net's idle state is whatever the open-collector
  comparator and a dead pull-up leave it at. **If OE is active-low and the
  comparator pulls it low for "instrument present", then losing the pull-up leaves
  OE low — buffers enabled — which is the exact state the gating exists to
  prevent.** This needs checking against the intended polarity; if it is the other
  way round it should be written down as the reason.
- the module's only health indicator, so the failure is silent.

`[schematic]` And the third of these is what nobody else in the corpus has to worry
about, because Castor & Pollux, Telex-O, Mutable and miditron all derive every
low-voltage rail from +12 V.

**The fix is one part.** A second 78L05/LM317LZ (or an extra ~10 mA on the existing
LM317 with the AHCT125's own 100 nF and a small series bead, if the switching-current
argument can be met) off the +12 V analog branch deletes the bus +5 V dependency
entirely — and with it the one pin in the design that has no reverse protection, the
one rail whose absence is silent, and the "engineering for a case this instrument is
never in" objection, since the module would then work in *any* case rather than
depending on a property of one.

---

## 5. The unusual part — a module that sources power out

### What the practised idiom actually is

There are three published patterns, and Woody matches none of them:

**(a) Expander ribbon: pass the rails through, protect nothing.** `[schematic]`
Castor & Pollux's expander (`hardware/expander/expander.kicad_sch`) is a 2×5 header
carrying six jack signals and GND — **no power at all**; the expander is passive.
Telex-O's `ii` header is 3-pin (GND/SDA/SCL) and each Telex module takes its own
rack power from its own 10-pin header. Expert Sleepers' `dm4_midi_brk_v1` MIDI
breakout has a header captioned `POWER` wired to `GND` only — the breakout is
passive DIN jacks. Where expanders *are* powered from the host, the ribbon is
unprotected and unfused, and the documented consequence is that plugging an expander
cable in backwards damages both boards `[docs, search summary]`.

**(b) USB host port: convert the voltage, and let the converter be the limiter.**
`[docs — search summary of the blocked Expert Sleepers FH-2 manual]` The FH-2
"will provide the USB specification's theoretical maximum of 500 mA for connected
devices", from its own regulator, which is "about 83 % efficient, which means that
the current draw on the +12 V rail is about half that drawn by the USB device". The
module itself draws 118 mA / 48 mA. `[docs, search summary]` Intellijel's USB Power
1U takes the **bus +5 V** straight through to a USB socket and provides "1 amp or
more", bounded by the bus board's own 5 V capacity — i.e. limited by the PSU, not by
the module.

**(c) Nothing at all.** A GitHub code search this session for `eurorack` together
with `TPS2553 OR LT1641 OR eFuse OR TPS259` returned **three files, all in
`jeffmhopkins/Woody`** `[docs]`. A search for `eurorack` with the common USB
power-switch parts (`AP2141`, `MIC2005`, `TPS2065`, `SY6280`, `NCP380`) returned
**zero** `[docs]`. Hot-swap controllers are not a Eurorack idiom in any form.

### Why Woody is right to differ

Pattern (b) is the one Woody most resembles, and the difference is decisive: **every
published module that sources power out converts the voltage on the way, and gets
current limiting free from the converter.** Woody cannot, because the WS2815 strips
need 12 V at the far end (ADR 0014) — so it passes the rack's +12 V through
unconverted, and there is no regulator in the path to limit anything. A module that
hands raw rail voltage to a 2 m detachable cable, at up to ~580 mA, has no prior art
to copy and genuinely needs an explicit limiter.

The second reason is one the community has already written down from the other side.
`[docs, search summary]` The universal rule "turn the rack off before installing a
module" exists *because* Eurorack has no hot-swap provision: uncharged capacitance
meets a low-impedance supply, inrush is limited only by parasitics, and the bus sags
enough to glitch logic elsewhere. **Woody's umbilical is hot-plugged by design** —
it is a cable the player connects, not a module that gets installed. The community's
answer to inrush is procedural and Woody cannot use it, so a circuit answer is
correct. A programmed ramp is the right shape of answer.

**So the LT1641 is proportionate in kind.** It is not proportionate as specified.

### The error: the SOT-23 FET is outside its SOA

`[docs — Analog Devices' own framing, via search summary of blocked analog.com]`
"A hot-swap controller uses an external MOSFET to shape the power-up ramp (dv/dt),
limit inrush and short-circuit current, and **keep the MOSFET within SOA**", and the
LT1641's programmable **foldback** exists specifically because "the foldback
characteristic tends to keep the MOSFET's power dissipation constant in current
limit, as the sense resistor's voltage limit decreases as the output voltage
decreases."

`bom.csv` specifies `LT1641-1CS8 + N-FET + sense R`, package `SO-8 + SOT-23 FET`.
Work the dissipation, using ADR 0005's own numbers:

- Constant-current start at 1.0 A, "about 75 ms" (ADR 0005's figure).
- During the ramp the FET holds the difference between the ~11.6 V input and the
  rising output. Mean drain–source voltage over a linear ramp ≈ 6 V.
- Mean dissipation ≈ **6 W for ~75 ms**, ≈ 0.45 J, and the *peak* at the start of the
  ramp is ~11.6 W.
- `[from memory]` A SOT-23 FET's single-pulse transient thermal impedance at 75–100 ms
  is of order 50–80 °C/W. 6 W × 60 °C/W ≈ **360 °C of junction rise.**

Even granting a factor of three in either direction, this is not close. The
conclusion is robust: **the pass FET must be a DPAK/SO-8-class device with a
published single-pulse SOA curve, chosen against that curve at 12 V for the full
ramp time** — or the ramp must be shortened and the foldback programmed so the
worst case (ramp into a hard short, 11.6 V across the FET at the full limit) stays
inside it. A short circuit at the etherCON, with the fault timer running, is the
sizing case, not the normal start.

ADR 0005 never mentions SOA or foldback. This is the clearest instance in the whole
document of "practice exists because of a failure mode Woody has not considered" —
except that here the practice is hot-swap engineering generally rather than Eurorack.

### The trip window is narrower than the part

`[datasheet, search summary]` The LT1641 sets its limit with a sense resistor between
`VCC` and `SENSE` against a **50 mV** threshold, and trips after the `TIMER` cap,
charged at 80 µA, reaches 1.233 V.

`[from memory]` The threshold on parts of this class carries a specified tolerance of
order ±10–15 % over temperature. ADR 0005 specifies "a window of roughly 0.9–1.13 A"
— ±11 % about 1.0 A. **The window is the same size as the part's own accuracy**,
before the sense resistor's tolerance and before E6's measurement uncertainty.

This is structurally identical to the LM317 divider problem ADR 0004 already
diagnosed and solved, and the same solution applies: `R-ILIM` is a bench-selected
value, verified by pulling the real trip point with an electronic load, not computed
from 50 mV / I. `bom.csv` says "final value from E6's current-probe measurement" —
E6 measures the *load*; it needs to also measure the *trip*.

### Two free wins from the part Woody has already chosen

- **Undervoltage lockout.** The LT1641 has a programmable UVLO pin. Using it means
  the instrument is not connected to the rail until +12 V is actually up — which
  removes Woody's inrush from the case-wide inrush at rack power-on, for two
  resistors.
- **`VCC` ≥ 9 V.** The part is a 9–80 V device `[datasheet, search summary]` and sits
  downstream of a Schottky: nominal 11.65 V, ~11.05 V with the rack 5 % low. Fine,
  but the margin to the 9 V floor is what determines whether a rack-side sag makes
  the controller reset and re-ramp. Worth one line in the ADR.

### The simpler idiom, for the record

If latch-off and a defined 1.0 A were not required, the honest minimum would be a
P-FET on the umbilical feed with an RC gate ramp for soft start (the toggle already
drives it), plus a polyfuse rated above 12 V — which is what practice would reach
for. That is 4 parts instead of ~8 and no SOA arithmetic, but it gives up: a defined
trip current, a fault timer, latch-off, UVLO, and the ability to distinguish "tripped"
from "off". Given that the umbilical is hot-plugged and its far end is sealed inside
a bonded wooden body, **keeping the hot-swap controller is the right call** — with
the FET fixed.

---

## 6. Local regulation for the DAC's AVDD

Woody is doing the conventional thing, and the corpus agrees `[schematic]`:

- **Castor & Pollux**: `LD1117-3.3` straight from +12 V, with the dissipation and
  thermal arithmetic written on the schematic. Winterbloom did not reach for a
  switcher or a reference; they reached for an LDO from +12 V and then checked the
  temperature rise.
- **Telex-O**: the DAC8564's 5 V comes from a `REF02AU` (a precision reference doing
  supply duty) and its logic from an `MCP1703` — neither from the bus.
- **miditron**: `LM1117-5.0` from +12 V, plus `ADP150` specifically for the *analog*
  3.3 V.
- **Mutable**: `ua78L05` from +12 V on four modules; `LM1117-3.3`, `MCP1703`,
  `REG1117` elsewhere.

The LM317LZ at 5.21 V is entirely in keeping. Three observations:

1. **The divider is also the minimum load, and that works out.** 1.25 V / 150 Ω =
   8.33 mA of divider current, which on its own satisfies an LM317's minimum-load
   requirement `[from memory]`. Worth stating in the ADR, because it is the kind of
   thing that gets "optimised" later by someone raising R1 to save power.
2. **Dissipation is a non-issue and should be said so.** (11.6 − 5.21) × ~13 mA ≈
   **83 mW** in TO-92 — about 15 °C of rise `[from memory]`. Winterbloom writes this
   number down for a part dissipating ten times as much; Woody's ADR does not write
   it down at all, which makes it look unconsidered rather than fine.
3. **Select-on-bench is right and is what one-offs are for.** ADR 0004's argument —
   that "no nominal value fits on paper" is a statement about a population and this
   is a population of one — is correct, and the corpus offers no counter-practice,
   because commercial designers cannot select on the bench and so must buy tolerance
   they do not need.

The one thing to carry across from §5: the same argument applies to `R-ILIM` and has
not been applied there.

---

## 7. Grounding on a mixed analog/digital module

### What published layouts actually do

`[schematic]`

- **Mutable Instruments** — strings extraction across Plaits, Marbles and Stages
  shows a single `GND` net (plus the usual auto-numbered `GNDnn` symbol instances),
  with `VCC` and `VDDA` as separate *supply* nets. No `AGND`/`DGND` split anywhere in
  the three files.
- **Castor & Pollux** — the power sheet uses `power:GND` exclusively. The
  analog/digital separation is done on the rail: `+3.3V` from the LD1117, then
  `FB3 600R@100MHz 200mA` to `+3.3VA`, which is what the MCP600x input amps, the
  MCP4728 and the analog references run from. One ground, two supplies.
- **apfaudio eurorack-pmod** — splits `GND` and `GNDD` as separate nets, with
  ferrites on the rails as well. So split grounds do exist in practice.
- **KitsBlips template** — places a `GND1` and a `GND2` symbol adjacent at one point
  on the sheet, i.e. a deliberate single-point tie between two ground nets. Someone's
  *default* module includes a ground-tie point.

So: practice is split, and the *precision-analog* designs in the corpus are on the
single-pour side, moving the separation onto the supply rail with a bead.

### Where Woody's rule is right and where it is the classic mistake

ADR 0004's mechanism — 360 mA of `PWR_GND` sharing copper with the analog return
develops an IR drop the pitch reference then sits on — is correct, and the
5.7–7.2 cents figure is the same shape of error as the shared-Schottky term. **Giving
`PWR_GND` its own copper from the etherCON to the inlet ground pin is right and is
the thing that would be expensive to fix later.**

`DIG_GND` is a different case, and the rule as written is likely to make it worse
`[from memory]`. The SPI runs at 2 MHz with fast edges; its return current does not
flow "to the star point", it flows in the copper directly beneath the signal trace,
because at those frequencies that is the lowest-inductance path. Forcing `DIG_GND`
onto its own copper that joins the analog return only at the inlet means:

- any SPI trace that crosses the boundary between the digital region and the analog
  region has its return current routed the long way round, creating a loop whose
  area is the whole board;
- the loop radiates, and it couples into exactly the high-impedance analog nodes the
  split was meant to protect;
- the level shifter's switching current — the thing ADR 0004 cites as the reason to
  keep the AHCT125 off the DAC's supply — now returns through a long narrow path
  instead of a plane.

The rule that matches both the corpus and the physics is:

- **one uninterrupted ground pour** under everything, on an 8HP board where the
  pour is the only thing keeping return paths short;
- **`PWR_GND` as its own routed conductor** (a trace or a dedicated copper strip,
  not a slot in the pour) from the etherCON to the inlet ground pin, so its 360 mA
  never shares a conduction path with the analog return — this is the one Woody
  correctly identified;
- **`DIG_GND` tied to the pour at the etherCON**, with the SPI traces routed so they
  never cross a gap, and with the level shifter's decoupling doing the local work;
- **`AGND` exactly as ADR 0004 already has it** — an in-amp input, not a return,
  terminating at IN+ and the two 1 MΩ bias resistors. That part is right and unusual
  and should not be touched.
- the analog/digital separation that Mutable and Winterbloom actually ship is on the
  **supply**: a bead between the digital 5 V/3.3 V and the analog one. Woody already
  has that shape (separate LM317 for the DAC) and can keep leaning on it.

---

## What Woody should change

1. **Fix the load-switch FET.** `SOT-23` in `U-LOADSW` is wrong by a large margin.
   Size the pass FET from a published single-pulse SOA curve at ~11.6 V for the
   full programmed ramp and for the fault-timer duration into a hard short; expect
   a DPAK or SO-8 part. Program the LT1641's **foldback** — it exists for exactly
   this. (§5)
2. **Measure the trip current, do not compute it.** The 0.9–1.13 A window is
   narrower than the 50 mV sense threshold's own tolerance. Add to E6: pull the real
   trip point with an electronic load and select `R-ILIM` from that, the same way
   `R-REG-SET` is selected at E7. Widen or re-derive the stated window. (§5)
3. **Delete the bus +5 V dependency.** One 78L05/LM317LZ off the +12 V analog branch
   removes the only unprotected pin in the design, the only silent rail failure, and
   the OE-net fail-state question below. Every comparable design in the corpus —
   Mutable, Winterbloom, Telex-O, miditron, and the KitsBlips default template —
   makes its low-voltage rails locally. (§4)
4. **Resolve the OE fail-state.** Write down what the OE net does when the LM393's
   pull-up rail is absent, and make "no +5 V" mean *buffers disabled*, not enabled.
   Today the pull-up is on the rail the ADR treats as expendable. (§4)
5. **Rewrite the reversed-ribbon paragraph in ADR 0004.** On a 16-pin header a
   reversal shorts bus +12 V, +5 V and CV through the module's ground net and puts
   the module's rails 12 V below its own ground; it does not "put +12 V on the +5 V
   pin". Keep the shrouded keyed header; keep the conclusion that the exposure is
   small; fix the mechanism and note the coupling from a dying buffer into the DAC's
   SPI pins. (§2)
6. **Restate the bead rule by rated current, not by package.** `FB-IN` should
   specify a *power-line* series part with a datasheet rated current ≥ 1 A (and the
   1206/1210 note demoted to a hint). 0805 600 Ω exists at both 600 mA and 2.3 A;
   1210 does not guarantee anything. Follow Winterbloom and put the rated current on
   the schematic next to the impedance. (§3)
7. **Damp the LC.** If a 10–47 µH inductor goes in front of the instrument's buck,
   specify the damping leg (series R+C across the filter cap) with it, and treat the
   cable + far-end 470–1000 µF as part of the same filter. Put it on E11. (§3)
8. **Correct the attributions in ADR 0004.** The series-Schottky convergence is
   *community* practice, not a Doepfer recommendation — what Doepfer publishes is
   keying, red-stripe-down, and a warning that a reversed cable can take the PSU with
   it. And the "2.2–10 Ω series resistor instead of a bead" variant does not appear
   anywhere in the corpus; the paragraph ruling it out is arguing with a ghost. (§1)
9. **Reconsider the total absence of a fuse — on the branches the load switch does
   not cover.** The analog +12 V branch, the −12 V rail and the +5 V pin have no
   overcurrent protection. Mutable fits a PTC on Frames and Veils, Telex-O fits two,
   eurorack-pmod fits two. ADR 0005's deletion argument is specifically about the
   *instrument-end* polyfuse and does not reach these. (§1)
10. **Write the LM317's numbers down.** 83 mW, ~15 °C rise, 8.3 mA divider current
    satisfying the minimum load. Winterbloom writes these on the schematic; Woody's
    absence of them reads as unconsidered rather than as fine. (§6)
11. **Change the `DIG_GND` layout rule to a single pour** with `PWR_GND` as the one
    dedicated conductor, and keep `AGND` exactly as specified. (§7)

## What Woody should keep

1. **Series Schottkys on ±12 V.** This is the standard, by a wide margin, and the
   census is unambiguous: 38 of 63 DIY schematics, every Mutable module examined,
   Winterbloom, Telex-O. (§1)
2. **Three diodes, not two.** The ~80 mV Vf-modulation mechanism is real, it needs no
   ground path, and it is visible by inspection of the power tree. No published
   module does this because no published module passes a third of an amp of
   someone else's load through its entry diode. This is the best original piece of
   reasoning in ADR 0004. (§1)
3. **The shrouded keyed 16-pin header.** Mechanical prevention is the entire
   community answer to reversal, and Woody's is at the strong end of it. (§2)
4. **A local regulator for the DAC's AVDD, fed from the protected +12 V.** Exactly
   what Telex-O, miditron, Castor & Pollux and Mutable all do, for the same reason.
   (§6)
5. **Selecting `R-REG-SET` on the bench at E7.** Correct for a population of one, and
   the corpus's tolerance-stacked alternatives exist only because commercial
   designers cannot do this. Extend the habit to `R-ILIM`. (§5, §6)
6. **Sending 12 V up the umbilical rather than 5 V.** This is the same trick the
   FH-2 uses in reverse (convert at the far end, so the rack-side current is
   halved), and the drop arithmetic in ADR 0005 is the standard reason. (§5)
7. **A current-limited, ramped load switch on the umbilical feed, with latch-off.**
   Eurorack's answer to inrush is "turn the rack off first", and Woody cannot use it,
   because the umbilical is a cable the player plugs in. No published Eurorack module
   sources unconverted rail voltage out over a detachable cable, so there is no
   simpler idiom to copy — the `-1` (latch) suffix over `-2` (auto-retry) is right,
   and so is refusing to let a fault pull on the rack's rail. (§5)
8. **The panel LED driven from the presence comparator rather than from the rail.**
   With a latching load switch this is the only thing that can report *why* the
   instrument went dark, and it reports the far-end analog chain at the same time.
   Nothing in the corpus has an equivalent. (§4)
9. **`AGND` as an in-amp input and not a return.** Unusual, correct, and the reason
   a 2 m analog run works at all. (§7)
10. **Bulk at the load rather than at the entry, for the WS2815 feeds.** ADR 0004's
    own correction, and it matches where every design in the corpus puts its
    capacitance — next to the thing that swings the current. (§3)

---

## Sources

**Repositories opened in this session** (cloned or raw-fetched from github.com /
raw.githubusercontent.com):
`pichenettes/eurorack` · `wntrblm/Castor_and_Pollux` · `wntrblm/Micronova` ·
`expertsleepersltd/hardware` · `bpcmusic/telex` · `mzuelch/CATs-Eurosynth` ·
`apfaudio/eurorack-pmod` · `Bemeier/bmcv` · `soundslikefrank/miditron` ·
`Alloyed/KitsBlips` · `moPsy-project/eurorack-power-breakout`

**Blocked to direct fetch from this session** (findings attributed to these are
search-engine summaries, flagged as such inline, and should be re-read from source
before anything is ordered or respun): doepfer.de · modwiggler.com ·
mutable-instruments.net · expert-sleepers.co.uk · befaco.org ·
northcoastsynthesis.com · rossum-electro.com · monome.org · aisynthesis.com ·
intellijel.com · web.archive.org · ti.com · analog.com · vishay.com · murata.com ·
product.tdk.com · bourns.com · littelfuse.com · digikey.com · mouser.com · lcsc.com

**Not consulted, and it shows:** Befaco's published schematics (befaco.org blocked;
their GitHub `Befaco/hardware` repo contains only a README), Music Thing Modular,
Nonlinearcircuits and AI Synthesis. Their absence is why the DIY half of the census
leans on `CATs-Eurosynth`. If any of those become reachable, the bead/fuse counts in
§1 and §3 are the numbers worth re-running.
