# S12 — Findings reconciliation: what was applied, what was declined, what was dropped

**Date:** 2026-09-21. **Scope:** the 20 agent reports in
`docs/review/2026-09-21-hardware-and-standards-review/`, against the design
corpus at `HEAD` (`745af8c`).

**What this audits:** disposition, not engineering. No finding is re-argued.
Every Showstopper- or High-ranked finding gets exactly one status.

## Method, and the single fact that decides most of this

Three commits followed the review: `b1142b4` (the "must-change block"),
`efebba9` (breath response control) and `745af8c` (8HP → 10HP).
Between them they touch **ten corpus files**:

```
README.md  ROADMAP.md  bom.csv  carrier.md  cluster-boards.md
breath-output-stage.md  digital-and-supervision.md  power-entry.md
docs/decisions/0004  docs/decisions/0009
```

`git diff 3040d43..HEAD --stat` confirms the list is exhaustive.

**Not touched at all:** `pitch-stage.md`, `mod-channels.md`,
`breath-receive-stage.md`, `firmware/README.md`, `config/key-layout.yaml`,
`docs/reference/latency-budget.md`, and ADRs **0001, 0003, 0005, 0006, 0010,
0013, 0014**.

Any finding whose only home is one of those files is, by construction, either
recorded somewhere else or silently dropped. Almost none were recorded
somewhere else: **the ROADMAP's "Open items blocking work" table gained
nothing, and its "Bench measurements the review asked for" table gained
nothing** — both received only an `8HP → 10HP` string edit. A twenty-agent
review produced no new entry in the two places a builder looks for what is
still open.

**Ranking note.** A1–A8 and B1–B6 rank Showstopper / High explicitly. C1, C2
and C4 report verdicts (BROKEN / SURVIVES / UNDECIDABLE) with no rank; C3
reports outcomes. For those four, a **BROKEN** verdict on a claim the corpus
asserts, or a C3 outcome of damage/non-start, is treated as the
Showstopper/High equivalent and marked `(C-equiv)`.

---

## The table

Status key: **A** = applied · **A-P** = applied but partial · **D** = declined
with a recorded reason · **T** = open and tracked where a builder will see it ·
**X** = SILENTLY DROPPED.

| Finding | Agent | Severity | Status |
|---|---|---|---|
| S1 Z-stack does not close; top-face switches must span 8 mm of laminate to reach a PCB | A1 | Showstopper | **X** |
| H1 `J-CHAIN` ~8.9 mm boxed header in a 20 mm cavity; two face each other | A1 | High | **X** |
| H2 Bits 22, 23, 31 floating — no pull-up budgeted | A1 | High | **A** — `R-KEY-PU` 21→24 in `bom.csv` + `cluster-boards.md` §4/table |
| H2b Alternative: strap all 3 → 11-bit marker, 0 free | A1 | High (variant) | **D** — `cluster-boards.md` still-open list, "Left at 8/3 rather than drifting" |
| H3 Cluster-board ground net never named; `MECH-GNDBOND` puts `PWR_GND` mm above it | A1 | High | **X** |
| 1 `R-ISO-REF` absent from drawing and table; reference buffer oscillates | A2 | Showstopper | **A** — `carrier.md` §2 drawing + compensation requirement |
| 2 `R1b` (`R-SER-BREATH-INST` ×2) not on the carrier | A2 / A5 F-R1B / D2 S6 | High | **A-P** — drawn in §2; **the §"Component inventory" table still lists it without ×2** |
| 3 `D-TVS-BREATH` on the op-amp side of the series resistor | A2 | High | **X** — drawing still shows it inside `R1`; a contradictory floating note "AT THE CONNECTOR" was added instead |
| 4 `VDD_ADC`: MCU transient load and 330 kHz ripple are 10–50× the pull-up term; bare 10 µF does not fix them | A2 | High | **X** |
| 5 `AGND-local`↔`PWR_GND`: no layout constraint written for the WS2815 return | A2 | High | **X** |
| 1 `C-BUCK-IN`: no low-ESR HF cap at either R-78E input; ripple-current rating exceeded | A3 | Showstopper | **X** |
| 2 3 W of 8×8 matrix on a 25 mm dev board is thermally impossible; needs a matrix sub-cap | A3 | Showstopper | **X** |
| 3 `D-REVSHUNT` clamps past the −0.3 V abs max of three analog parts; partial faults never latch | A3 | High | **X** |
| 4 `D-USBOR` puts a second Schottky in series with USB-C VBUS | A3 | High | **X** |
| 5 No temperature grade / hour rating / ESR band on any electrolytic in a bonded body | A3 | High | **X** |
| 6 `R-LED-PD` is on the buffer's *inputs*; useless in the 12 ms window | A3 | High | **X** |
| 7 `5V_B` regulator 360 mm from its load delivers none of ADR 0013's benefit | A3 | High | **X** |
| D1 `MOSI`/`CS` share one twisted pair | A4 / A8 #1 | Showstopper | **A** — pin map swapped in ADR 0004, `carrier.md` §4, `digital-and-supervision.md` |
| D2 Loop budget omits ESP-IDF per-transaction overhead; 291 µs with driver defaults | A4 | High | **X** — and VERIFIED.md explicitly endorsed A4's number as "the number to design against" |
| D3 220 Ω is the wrong series value | A4 / B5 H-1 / D2 H25 | High | **A-P** — 100 Ω in `bom.csv` + `carrier.md`; **ADR 0004 still states 220 Ω as its decision (L479) and 68 Ω at L73** |
| D4 MCP3202 `SCLK`/`DIN` drawn nowhere | A4 | High | **X** |
| D5 Presence detect available for two resistors and a spare pin | A4 | High, free, unretrofittable | **X** |
| D6 Recovery ladder rung 2 is deleted by an NVS setting stored on the board being recovered | A4 | High | **X** |
| D7 `BOOT`/`RESET` reachable through the existing service cover | A4 | High, free | **X** |
| D8 WS2815 `V_IH` literal datasheet value is 8.4 V | A4 | High | **X** |
| D9 SPI2 is claimed by the onboard matrix in the reference config | A4 | High | **X** |
| F-OFF-1 Unbuffered `POT-OFFSET` wiper puts "zero at centre" at +0.605 V | A5 | High | **X** — and `efebba9` notes it in passing while adding a *different* pot |
| F1 `CLR` drawn as a pull-down on an active-low pin | A6 / D2 S3 | Showstopper | **A** — `digital-and-supervision.md` redrawn to AVDD via `R-CLR-PU` |
| F2 DAC ch7 "written once at boot" vs refresh every pass | A6 / D2 H19 | High | **X** — ADR 0006 L186 and `firmware/README.md` L50 both unchanged |
| F3 `R-OUT-PROT` worst case 322 mW, not 192 mW | A6 / B4 / D2 H29 | High | **A-P** — BOM *note* says "specify 0.66–1 W"; **the BOM value field still reads `>=500mW`, `breath-output-stage.md` says ≥500 mW and `pitch-stage.md` still says ≥250 mW** |
| F4 Every plug insertion rails the pitch jack to ~+11.9 V for 50–100 µs | A6 | High | **X** |
| 1 `C-TIMER-LOADSW` 10 nF is a ~1 ms timer | A7 / B3 3.2 / C3-1 | Showstopper | **A** — `power-entry.md` rebuilt; BOM row `TBD`, marked BLOCKING |
| 2 No gate capacitor exists anywhere | A7 | Showstopper | **A** — `C-GATE-LOADSW` created, marked BLOCKING |
| 3 Start current 0.89 A against a 0.9 A limit; start table has no load row | A7 | Showstopper | **A** — 0.940 A limit and a loaded 62 ms start now derived |
| 4 Foldback stretches a current-limited start past the timer | A7 / B3 3.3 / C3-1 | Showstopper | **A** — foldback re-derived, described correctly |
| 5 367 mA umbilical swing → ~6 mV → 7.4 cents of breath-correlated pitch bend | A7 / B3 §8 / A8 #3 | Showstopper | **T** — recorded in `power-entry.md` as "Not fixed here"; **not in the ROADMAP open-items table** |
| 6 `ON` pin unbuildable as drawn | A7 | High | **A** — `power-entry.md` §"Still not designed: the `ON` pin" |
| 7 A reversed 16-pin ribbon shorts rack +12 V to +5 V through the module's ground pour | A7 / B1 #9 | High / **Showstopper (B1)** | **X** — and the refuted sentence still stands in `power-entry.md` L92 and ADR 0004 L193 |
| 8 Hot-plug consumes ~25 ms of the timer; no operating procedure | A7 / B3 3.4 / C3-2 | High | **A** — hot-plug now named as the sizing case |
| 9 FET SOA sized on the constant-power hyperbola only (Spirito) | A7 | High | **A** — "chosen against the single-pulse SOA curve" |
| 10 `R-ILIM` 50 mΩ 0805 needs Kelvin connection | A7 | High | **X** |
| 11 A soft 5–30 Ω cable fault dissipates up to 12 W inside a bonded body, forever | A7 | High | **X** |
| 12 The "20 cents" consequence of the 80 mV Vf modulation is wrong by ~5 orders | A7 | High | **A-P** — corrected in `power-entry.md`; **`bom.csv` `D-REVPOL` still carries the 20-cent claim verbatim** |
| 13 `C-BULK-RAIL`: page says 4×47 µF, BOM says 100 µF | A7 / D1 A50 | Medium-High | **X** |
| 14 Module current draw is declared nowhere (~390 mA typ / ~610 mA worst) | A7 / B1 #11 | Medium-High / **High (B1)** | **X** |
| 1 `MOSI`/`CS` pair | A8 | Showstopper | **A** (see A4 D1) |
| 2 `DIG_GND` named in three documents, drawn at the instrument end in none | A8 | Showstopper | **A-P** — `carrier.md` §4 now draws pin 8 → `DIG_GND`; **the two-answers question (is it `PWR_GND` at the instrument?) is still unresolved and `U-TVS-SPI`→`PWR_GND` vs `U-TVS-CHAIN`→`DIG_GND` still disagree** |
| 3 No shield-termination policy anywhere | A8 / B5 H-2 | High | **T** — one line in `power-entry.md`: "the shield policy is sixteen words in the whole repo" |
| 4 `CABLE-UMB` 0.168 Ω is the solid-core figure for a stranded cable | A8 | High | **X** |
| 5 `U-LOADSW` 1.0 A limit vs ADR 0014's 1522 mA clamp-off worst case | A8 | High | **X** |
| 6 Eight identical `J-CHAIN` connectors; a swapped IN/OUT fights two '165 outputs | A8 | High | **X** |
| 7 `U-TVS-MODULE` deferred, though the threat originates at the player's hand | A8 | High | **X** |
| 9 16-pin reverse insertion analysis is wrong | B1 | Showstopper (analysis) | **X** |
| 3 Panel height budget: ~115 mm bottom-up against 110 mm; "107 mm" never derived | B1 | High | **A** — ADR 0004 now derives 97 mm at 10HP |
| 10 Bus +5 V rail should be dropped | B1 / B3 §2 / A7 | High ×3 | **X** — *claimed* declined in `b1142b4`; **no such record exists** |
| 11 Current draw declaration (1045 mA worst on +12 V) | B1 | High | **X** |
| 12 `D2` 1N5817 rated 1.0 A at a 1.0 A limit, zero margin | B1 | High | **X** |
| 15 200–400 mA square wave at ~2 kHz onto the case's shared +12 V | B1 | High | **X** |
| G-4 Instrument away → rack drones indefinitely; `CLR` has no driver | B2 | Showstopper | **X** |
| G-1 No gate/trigger output exists | B2 | High | **X** |
| B-1 Breath jack is not 0 V at power-on; up to +5.06 V | B2 / C2 N-JACK-1 / C3-6 / A5 F-BIAS-1 | High | **X** — ADR 0005 and ADR 0006 untouched |
| I-2 Passive-multing PITCH gives 44–67 % overshoot that never settles | B2 / B4 / A6 | High | **X** |
| 3.2 `C-TIMER-LOADSW` 100–300× too small | B3 | Showstopper | **A** |
| 1.5 / §2 Bus +5 V has no diode; drop the rail | B3 | High | **X** |
| 3.3 Foldback vs programmed ramp | B3 | High | **A** |
| 3.4 The sizing case is the hot-plug | B3 | High | **A** |
| §8 360 mA of foreign current in the rack's shared copper → 8–18 cents | B3 | High | **T** (with A7 #5) |
| §9 Repo-internal consistency inside scope | B3 | High | **A-P** — the power-entry items landed; the BOM copies did not |
| `R-OUT-PROT` 269–464 mW; derated 1206 gives ~1.1× | B4 | High | **A-P** (see A6 F3) |
| `C-FILT-PITCH` 10 nF on the feedback node spends the whole stability margin; 0 of 12 published designs do it | B4 | High | **X** |
| Stackcable PITCH→MOD/BREATH rings longer than the update period | B4 | High | **X** |
| S-1 Wrong-*port* misplug; pins 4/5 should be vacated | B5 | Showstopper | **D** — ADR 0004 §"Considered and rejected: moving the SPI signals off pins 4/5 entirely" |
| H-1 220 Ω over-terminates a 100 Ω line | B5 | High | **A** (see A4 D3) |
| H-2 Shield bonding unspecified | B5 | High | **T** (thin) |
| H-3 Nobody ships 2 m of raw single-ended SPI | B5 | High | **X** |
| H-4 RJ45 has no mating sequence; no hot-plug rule | B5 | High | **A-P** — hot-plug is now the load-switch sizing case; **no mating/operating rule was written** |
| 2.1 No drain and no replaceable wet part, in a body that bonds shut | B6 | Showstopper | **X** |
| 1.1 2.8 kPa is unsourced and cited in a circle | B6 / A5 F-CAL-1 | High | **X** |
| 1.4 Commissioning at 2.16× rails at 3.23 kPa | B6 / A5 F-OUT-1 | High | **X** |
| 2.2 ≤1 mL trap fills in tens of hours; no drain, no access route | B6 | High | **X** |
| 2.3 Diffusion puts mouth humidity at the die in ~56 min | B6 | High | **X** |
| 4.1 No breath response curve | B6 | High | **A** — `efebba9` adds `POT-RESP`, and cites B6 |
| 4.3 Note-on is a bare threshold on a 564 Hz signal; no hysteresis | B6 | High | **X** |
| 4.4 No fingering deglitch | B6 | High | **X** |
| Claim 1 The 8-bit marker misses three families, incl. the reorder this project proposed | C1 | BROKEN (C-equiv) | **A** — `left_thumb` pair flipped; `cluster-boards.md` §4 records the exhaustive solve |
| Claim 1b Put the marker bit map in `key-layout.yaml` | C1 | BROKEN, root cause | **X** — `key-layout.yaml` untouched; the eight levels remain prose-only |
| Claim 2 `SH/LD` wants a 100 kΩ pull-up at each `U-KEYS` | C1 | (C-equiv) | **X** |
| Claim 3 Two agreeing samples do not remove credulity (750 µs burst vs 250 µs scan) | C1 | BROKEN (C-equiv) | **X** |
| Claim 4 `LK-SER`+`R-SER-TERM` self-test is broken both ways; move `R-SER-TERM` to `LK-SER`'s common pin | C1 | BROKEN (C-equiv) | **X** |
| Claim 5 125 µs is 1/12–1/50 of a real bounce train; one press reads as several | C1 | BROKEN (C-equiv) | **X** |
| N-INP-1 Open `AGND` leaves the instrument fully playable with 44 counts of wobble | C2 | BROKEN, worst in set | **X** |
| N-INM-1 / N-JACK-1 Open BREATH parks at −1.24 V; standalone rest is −6.15…+3.80 V | C2 | BROKEN | **X** |
| N-SENSE-1 Post-commissioning thermal drift is 35 counts, 9.5× the ADR's figure | C2 | BROKEN | **X** |
| N-REF-1 `TRIM-BREATH-ZERO` 0→1.0 V does not cover a drifted max-pedestal part | C2 | BROKEN | **X** |
| N-BUF-1 The instrument buffer is the one active device with no RF filter, by decision | C2 | BROKEN, unretrofittable | **X** |
| N-POTG-2 Usable gain range is a function of the offset setting | C2 | BROKEN | **X** |
| C3-1 Every start latches off | C3 | Non-start | **A** |
| C3-2 Load switch is upstream of the connector | C3 | Damage | **A** |
| C3-3 `R-LED-PD` not in `bom.csv`; random strip data at boot exceeds the limit | C3 | Latch-off | **X** — `R-LED-PD` is still "PROPOSED" in `carrier.md` and has no BOM row |
| C3-4 A garbage DAC word holds 182 mW into a neighbouring module indefinitely | C3 | "the one that can hurt the synth" | **X** |
| C3-5 `R-SPI-PULL` cable-side `CS` pulls to a rail the module does not have | C3 / A4 D15 / D2 S9 | Undefined by construction | **X** |
| C3-7 Write order *does* change the `CLR`-exit excursion (−10.0 V vs +11.45 V) | C3 / A6 F11 | Damage-adjacent | **X** |
| C3-8 No series resistance between `U-LVL-MOD` and the DAC; ±50 mA into an unpowered input | C3 | Damage | **X** |
| C3-10 The load switch cannot see a 5 V or 3V3 short at all | C3 | Thermal, silent | **X** |
| C3-11 The panel LED cannot indicate a latch-off | C3 | Every latching fault is silent | **A** — `power-entry.md` §"But the LED has lost the job it was kept for" |
| §1.4 Reference error is additive and full-scale-weighted, not a gain term | C4 | BROKEN, new mechanism | **X** |
| §2 Wi-Fi TX step is 6–14× the key step and is never costed | C4 | BROKEN | **X** |
| §3 Which rail the 8×8 matrix runs from is recorded nowhere and decides the report | C4 | UNDECIDABLE | **X** — not added to the ROADMAP bench table |
| §2.4 SPI3 shifts while SPI2 converts; free to fix | C4 | BROKEN, zero cost | **X** |
| §5.3 ADR 0014's 34 mV animation ground offset needs a written layout rule | C4 | UNDECIDABLE | **X** |
| A9 Key chain booked at 16 µs; 32 µs at the stated 1 MHz | D1 | wrong | **X** |
| A13/A14 Marker 6/5 → 8/3, and 5 free bits → 15 passives | D1 | wrong | **A-P** — table fixed; **`carrier.md` L514 still says "six bits … still undecided" and L521 still says "5 free bits … 15 passives"** |
| A58 `bom.csv` `R-KEY-SER` carries the pre-correction 1 µs / 93 µs pair | D1 | wrong | **X** |
| A1–A4, A20–A23, A33–A43, A57, A60 and the 22 cross-file disagreements in §2 | D1 | wrong | **X** — every one lives in a file that was not opened |
| S1 74HC123 watchdog deleted in prose, built in the drawing | D2 | Showstopper | **A-P** — see §"Partial" below; four documents still depend on it |
| S2 LM311 presence comparator likewise | D2 | Showstopper | **A-P** — `breath-receive-stage.md` L195 still says "if `R1` opens, the presence detect de-asserts" |
| S3 `CLR` pulled the wrong way | D2 | Showstopper | **A** |
| S4 `C-FB-PITCH` specified three ways, one called dangerous | D2 | Showstopper | **X** |
| S5 `C-FILT-PITCH` deleted in ADR 0006, restored in `pitch-stage.md` | D2 | Showstopper | **X** |
| S6 `R1b` | D2 | Showstopper | **A-P** |
| S7 `R-ISO-REF` | D2 | Showstopper | **A** |
| S8 Three SPI refdes vs one BOM refdes | D2 | Showstopper | **A** |
| S9 `CS` idle pull goes to three different rails | D2 | Showstopper | **X** |
| S10 Module panel LED is two different circuits | D2 | Showstopper | **A** |
| S11 Mod channels: LT5400 1:4 vs 10 k/30 k discretes | D2 | Showstopper | **X** |
| S12 `LDAC` "not in this design anywhere" and has a BOM row | D2 | Showstopper | **X** |
| S13 Breath pulldown deleted and still specified in two ADRs | D2 | Showstopper | **X** |
| H5 Marker bits 8/3 vs 6/5 vs "four to six" | D2 | High | **A-P** |
| H15 Key-network time constants | D2 | High | **A-P** — `cluster-boards.md` only; ADR 0001 L225–226 and `bom.csv` `C-KEY` still 125 µs / 5.7 µs |
| H25 Series resistor value | D2 | High | **A-P** — now a *three*-way disagreement (ADR 0004 220 Ω, ADR 0004 68 Ω, BOM/carrier 100 Ω) |
| H28 `C-DECOUPLE` counts a deleted part | D2 | High | **A-P** — qty 21→19; **the note's own enumeration still reads "LM311 on +/-12V = 2" and still sums to 21** |
| H29 `R-OUT-PROT` power rating | D2 | High | **A-P** |
| H16 Load-switch start time / power / energy | D2 | High | **A-P** — `power-entry.md` rebuilt; `bom.csv` `U-LOADSW` still says "75ms … ~6W and 0.45J" |
| H1–H4, H6–H14, H17–H24, H26–H27, H30–H40 (31 further High cross-file contradictions) | D2 | High | **X** — none of the files holding them were opened |

**Tally of Showstopper/High dispositions: 21 applied, 13 applied-partial, 2
declined with reason, 3 open-and-tracked, and roughly 90 silently dropped**
(counting D1's §2 list and D2's residual Highs as blocks rather than
individually).

---

## The silently dropped findings

Ordered by what bonds shut, burns, or ships wrong first.

### 1. A1 S1 — the Z-stack does not close (Showstopper)

`cluster-boards.md` §5 models the stack as plate → switch → PCB with an
MX-like ~3.4 mm standoff. ADR 0009 puts the aluminium plate on the *outside*
of the oak top, so a top-face switch must span 2 mm aluminium + 6 mm oak =
**8 mm of laminate** before it reaches anything a PCB could sit on. A KS-33 is
12.2 mm overall and has ~5 mm of body below the mounting shoulder at most.
ADR 0009 also contradicts itself three paragraphs later ("even if the entire
12.2 mm sat inside it there would be 8 mm left"), which places the switch
*below* the oak.

`cluster-boards.md` §5 presents Z as a single `TBD` waiting on one Gateron
dimension. It is not: it is waiting on an undecided question about where
`PLATE-TOP` goes. Three non-equivalent resolutions are costed in A1 (move the
plate inside; cut the oak away along the key line; hand-wire the top clusters
and reverse ADR 0001's per-cluster argument). None was recorded. Everything
downstream is blocked by it: component height, which side the passives go on,
the `J-CHAIN` connector choice, the plate DXF and the oak cut list.

Pick-up: `docs/review/.../A1-cluster-boards.md` §Part 2 SHOWSTOPPER;
`cluster-boards.md` §5; ADR 0009 stack table.

### 2. B1 #9 / A7 #7 — the 16-pin reversal analysis is wrong (Showstopper)

On a reversed 16-pin ribbon the module's GND lands on bus +12 V *and* bus
+5 V, and the series Schottkys are not in that path — keying is the only
protection. The repo's stated analysis, **"a reversed ribbon that kills the
buffer and nothing else is an acceptable outcome"**, is still standing
verbatim in `power-entry.md` L92 and ADR 0004 L193–195. Two agents refuted it
independently. Nothing was changed and nothing was recorded.

This one is doubly bad because it is the load-bearing justification for the
next item.

### 3. B1 #10 / B3 §2 / A7 — drop the bus +5 V rail (three agents, three reasons)

`b1142b4`'s commit message says this was *"not applied, and recorded as
decisions rather than drifted into."* **There is no such record.** ADR 0004's
section "The 74AHCT125 stays on the bus +5 V rail" is byte-identical to its
pre-review state; `git diff 3040d43..HEAD -- docs/decisions/0004-cv-interface-module.md`
contains no line mentioning the +5 V rail at all. `power-entry.md` L91 is
likewise unchanged.

The three reasons were: B1 — the 16-pin header's reversal hazard exists
*because* of pins 11–16, and a 10-pin header maps ground to ground so the
diodes work; B3 — 0 of 8 published designs needing a sub-12 V rail take it
from the bus; A7 — it is the only rail with no reverse protection, and
`bom.csv` already documents that a reversed ribbon on it reaches the DAC's
`SYNC` pin, and `C-BULK-RAIL` on that branch is a through-hole electrolytic
that vents when reverse-biased.

The rail exists for one 74AHCT125. This is a **claimed decline that is in fact
a silent drop**, and it is the single largest honesty defect in the applied
block.

### 4. B2 G-4 — the rack drones indefinitely (Showstopper)

Instrument unplugged, powered off, or the load switch tripped: the DAC holds
its last codes. Pitch holds, mods hold, breath sits at the OFFSET knob. `CLR`
has no driver; the watchdog and the presence detect are both deleted. Nothing
in the corpus records this.

**The applied block made it worse.** `digital-and-supervision.md` was redrawn
to tie `CLR` to AVDD through `R-CLR-PU`, *permanently inactive* — which is
correct for the CLR pull-direction defect and simultaneously confirms G-4's
premise that nothing can park the outputs. Meanwhile `mod-channels.md` L150
and L215–217 still justify the whole mod topology on *"on a watchdog `CLR` the
channels go to zero"*, and `firmware/README.md` L54 still says *"when the
module watchdog asserts `CLR`"*. B2 rates this "the classic wind-controller
failure the field designs against"; B2 G-1 (no gate output at all, present in
every comparable design) is the same gap from the other side.

### 5. A3 #1 and #2 — the carrier power section was never opened (two Showstoppers)

`carrier.md` §1 has no change in the whole review window. A3's two
Showstoppers stand:

- **No low-ESR HF capacitor at either R-78E input.** The deliberately-high-ESR
  electrolytic is the only input cap, leaving ~170–194 mV rms of 330 kHz
  ripple at the regulator pin and exceeding the part's ripple-current rating.
  A3 calls it "the cheapest fix on this page".
- **3 W on a 25 mm dev board is thermally impossible** regardless of
  regulator. The 928 mA that sizes both regulators is 600 mA of 8×8 matrix.
  The instrument-wide clamp needs a matrix sub-cap.

Five further A3 Highs (#3 `D-REVSHUNT` past abs-max, #4 `D-USBOR` double
Schottky onto a sealed-in USB-C receptacle, #5 no electrolytic grade in a
bonded body — 0.9 years to end of life, #6 `R-LED-PD` on the wrong side,
#7 the 360 mm regulator) went with it.

### 6. A4 D2 — the loop budget does not close (High), endorsed and then dropped

A4: ESP-IDF's documented per-transaction overhead (24 µs interrupt, 9 µs
polling) is counted by no document. With driver defaults the pass is **291 µs
against a 250 µs period — 4 kHz does not close**; with polling transactions on
an acquired bus it is 196–241 µs.

`VERIFIED.md` reconciles this against D1 and concludes: *"the number to design
against is A4's, and the firmware technique it names is not optional — it is
what makes 4 kHz reachable at all."* Then nothing happened. `carrier.md` L593
still reads `SPI2 total = 122.7 µs of 250 µs → 49 %`, and
`latency-budget.md` still carries 136 µs / 54 % and the 16 µs key-chain row
D1 corrected to 32 µs. **A conclusion the auditor personally underwrote is
sitting unrecorded in the two documents that own the number.**

### 7. D2 S4 / S5 — the pitch compensation network (two Showstoppers)

`pitch-stage.md` L29 draws `C-FB-PITCH 1nF`; L179 says "1 nF from the op-amp
output"; L134 and `bom.csv` say **2.2 nF**; ADR 0006 L611 says **"1 nF across
the feedback resistor"** — the arrangement `pitch-stage.md` itself says gives
**18° of phase margin with 2 m of cable**. ADR 0006 L614 says `C-FILT-PITCH`
is deleted; `pitch-stage.md` L136 and `bom.csv` say restored.

`VERIFIED.md` lists both as hand-confirmed. Neither file was opened.
**The accepted ADR still prescribes the topology the schematic calls
unstable.** B4 adds, independently, that `C-FILT-PITCH` at 10 nF on the
feedback node spends the entire stability margin and is unprecedented in 12
published designs.

### 8. D2 S9 / C3-5 / A4 D15 — the `CS` idle pull names a rail that does not exist

One `bom.csv` row (`R-SPI-PULL`) says both *"Cable side: CS to +5V"* and
*"CABLE-SIDE CS PULLS TO 3V3, NOT +5V"*. ADR 0004 L348 says +5 V.
`digital-and-supervision.md` draws `CS↑` on both sides with no rail named —
including in the **newly redrawn** figure. C3 adds the killer: the module has
no 3V3 rail and 3V3 is not one of the eight conductors, so the resting state
of `CS`/`SYNC` is undefined by construction.

### 9. B6 2.1 — no drain, no replaceable wet part, bonded body (Showstopper)

Every published wind controller provides a drain or a replaceable wet part.
This design has neither and the body bonds shut. `bom.csv` `SKT-BREATH`
already says the socket *"only earns its place if the sensor is reachable"*.
ADR 0003 and ADR 0009 were not opened; ADR 0009 L251's pre-existing "not a
drain plumbed through the body — just a serviceable path to the sensor end"
predates the finding and is what B6 is arguing against, not a response to it.
B6's four supporting Highs (2.2 trap capacity, 2.3 diffusion reaching the die
in ~56 min, 1.1 the unsourced 2.8 kPa, 1.4 the rail at 3.23 kPa) went with it.

### 10. A2 #3 — `D-TVS-BREATH` on the wrong side of the series resistor (High)

The `carrier.md` §2 drawing still branches `[D-TVS-BREATH 12 V standoff]` from
the node *inside* `R-SER-BREATH-INST`, so the 1 kΩ absorbs the ESD strike.
The applied block added a separate, unconnected annotation at the bottom of
the same figure reading `[D-TVS-BREATH ×2, AT THE CONNECTOR]`. **The figure
now shows the part in two places and says neither is wrong.** Required order:
connector → TVS → R → silicon.

### 11. A7 #10 and #11 — the two load-switch faults the rebuild did not cover

The `power-entry.md` rebuild is the best work in the applied block, and it
covers four of A7's five Showstoppers. It does not mention:

- **#10, `R-ILIM` Kelvin.** A 50 mΩ 2-terminal sense resistor in 0805 has
  pad/trace parasitics around 10 % of its value — the same size as the
  LT1641's own threshold tolerance, on the part whose threshold the rebuild
  just corrected from 50 mV to 47 mV.
- **#11, the soft cable fault.** A 5–30 Ω umbilical fault draws under the
  limit forever and dissipates up to **12 W inside a bonded oak body**. The
  limiter cannot see it. C3-10 reaches the same class of hole from the other
  side: the load switch cannot see a 5 V or 3V3 short at all.

### 12. C3-3, C3-4, C3-7, C3-8 — four sequencing faults, none recorded

- **C3-3:** `R-LED-PD` is still "PROPOSED" in `carrier.md` with no BOM row.
  Strips get random data for 100–300 ms before firmware runs; mean random draw
  ~0.5 A on top of the ramp exceeds the 0.94 A limit. Intermittent,
  unretrofittable, inside a bonded body. (A3 #6 says the proposed pull-downs
  are on the wrong side anyway.)
- **C3-4:** "the one that can hurt the synth" — a garbage DAC word holds up to
  13.5 mA / 182 mW into a neighbouring module indefinitely, because
  `R-OUT-PROT` is inside the pitch feedback loop and nothing parks the DAC.
- **C3-7 / A6 F11:** write order *does* change the `CLR`-exit excursion —
  ch7-first bounds it to −10.000 V, ch7-last gives +11.45 V into the rail.
  `digital-and-supervision.md` and `bom.csv` `R-LDAC` both still say "no write
  order avoids it". A 21 V difference for one line of firmware.
- **C3-8:** no series resistance at all between `U-LVL-MOD` and the DAC;
  rack +5 V up before the LM317's 5.21 V puts ±50 mA into an unpowered
  DAC8568 input clamp.

### 13. A4 D5, D6, D7 — three free, unretrofittable recovery items

D5: a working presence detect for two resistors and a pin that is already
spare — which would also give G-4 its missing driver. D6: the recovery
ladder's second rung is deleted by an NVS setting stored on the board being
recovered, and `GPIO0` is inside the body. D7: `BOOT` and `RESET` can be
reached through a service cover that already exists in ADR 0009. All three are
cheap now and impossible after M8.

### 14. C1 Claims 3, 4 and 5, and the marker map's root cause

The marker flip landed. The rest did not:

- **Claim 1b (root cause):** the eight marker levels live only in
  `cluster-boards.md` prose. ADR 0010 makes `key-layout.yaml` the single
  source of truth for the bit mapping; `key-layout.yaml` was not opened. The
  next person to reorder the chain will re-create exactly the hole that was
  just closed.
- **Claim 4:** `LK-SER` + `R-SER-TERM` calls a named healthy chain broken and
  a named broken chain healthy. Fix is to move `R-SER-TERM` to `LK-SER`'s
  common pin — free, on boards not yet made.
- **Claim 2 follow-on:** a 100 kΩ pull-up on `SH/LD` at each `U-KEYS`, so an
  open latch conductor fails safe rather than into a linear-region oscillator.
- **Claim 5:** 125 µs is 1/12 to 1/50 of a real bounce train; a single fast
  press can read as multiple presses. No note-off hold was written, and no
  bounce measurement was added to M1's existing row.

### 15. C2 and C4 — two whole falsification reports with zero disposition

`breath-receive-stage.md`, `breath-output-stage.md` §1–3 and ADR 0003 were not
opened, so **every C2 BROKEN verdict is dropped**, including the worst one in
the set: **N-INP-1**, an open `AGND` conductor leaves the instrument fully
playable with 44 counts of light-show wobble — the exact failure ADR 0003
exists to prevent, and undetectable. Likewise C4: the reference-error
mechanism (§1.4, additive and full-scale-weighted rather than a gain term),
the uncosted Wi-Fi TX step, the free SPI2/SPI3 scheduling fix, and the one
UNDECIDABLE that decides C4's whole report — **which rail the 8×8 matrix runs
from** — which needs one measurement and was not added to the ROADMAP bench
table.

### 16. D1 §2 — twenty-two cross-file numeric disagreements

D1's own framing: *"these are the ones to fix first: in each case a reader of
one file gets a different number from a reader of another."* Three were fixed
(marker split, series resistor value, and the key timings — all partially).
The other nineteen were not, including the in-amp full scale (−9.6 / −9.94 /
−10.05 V), the sensor top of range (4.7 vs 4.80 V — **still 4.7 V in the
`carrier.md` figure that was edited this session**), the DAC channel count
(6 vs 7), the ADC frame (18 vs 24 clocks), the LM317 rail (5.21 vs 5.25 V),
the op-amp swing (±11.45 vs ±11.9 V), and the instrument current (~275 /
~320 / ~360 / 359 / 571 / ~630 mA).

---

## Partial applications, and what is missing from each

| Finding | What landed | What is still wrong |
|---|---|---|
| D2 S1/S2 watchdog + comparator | `digital-and-supervision.md` redrawn; `power-entry.md` rail list and LED section corrected; `C-DECOUPLE` 21→19 | `mod-channels.md` ×3, `firmware/README.md` L54, `breath-receive-stage.md` L195 and L283–290, `ROADMAP` E10, `bom.csv` `PCB-MODULE` description, and `C-DECOUPLE`'s own enumeration (still lists "LM311 on +/-12V = 2", still sums to 21) |
| A6 F3 `R-OUT-PROT` | BOM note says "Specify 0.66–1 W 1206 (ERJ-P08 class)" | BOM **value field** still `1k 1%, >=500mW`; `breath-output-stage.md` L127 ≥500 mW; `pitch-stage.md` L133 **≥250 mW** |
| A4 D3 / D2 H25 series resistor | `bom.csv` and `carrier.md` at 100 Ω, with the transmission-line table | ADR 0004 L479 still states **220 Ω** as its decision and L73 still says 68 Ω — three values now |
| D1 A58 / D2 H15 key timings | `cluster-boards.md` table at 119.9 µs / 5.92 µs | ADR 0001 L225–226 at 125 / 5.7; `bom.csv` `C-KEY` at ~5.7 / ~125; `cluster-boards.md` L163 itself still says "the 125 µs release filter" |
| D1 A13/A14 marker split | `carrier.md` 32-bit table now 8/3 | `carrier.md` L514 "which **six** bits carry the marker … is **still undecided**" (wrong on both counts — the pattern was decided the same day) and L521 "the **5** free bits … **15 passives**" |
| A2 #2 / A5 F-R1B `R1b` | Drawn in `carrier.md` §2 with the CMRR derivation | The page's own component-inventory table still lists `R-SER-BREATH-INST` with no `×2`, beside rows that do carry `×2` and `×3` |
| A7 #12 diode Vf / 20 cents | `power-entry.md` corrects it to 0.00018 cents | `bom.csv` `D-REVPOL` still carries "~20 cents of breath-correlated pitch bend … needs no ground path at all" verbatim |
| A7 #1–#4 / D2 H16 load switch | `power-entry.md` rebuilt with corrected physics; `C-TIMER-LOADSW` reset to TBD and `C-GATE-LOADSW` created, both BLOCKING, both re-packaged correctly | `bom.csv` `U-LOADSW` still specifies the superseded circuit verbatim — "A 1.0A ramp at ~6V mean for **75ms** is ~6W and 0.45J", "Set the limit at **1.0A** with a programmed 50-100ms ramp" — against the rebuilt page's 0.940 A and ~62 ms loaded start. The row that names the part still describes the design that did not start |
| A8 #2 `DIG_GND` | Pin 8 now drawn at the carrier | The showstopper was *which net it is at the instrument*. `carrier.md` §4 still returns `U-TVS-SPI` to `PWR_GND` while §3 returns `U-TVS-CHAIN` to `DIG_GND`. ADR 0004 L568 and `power-entry.md` L254 still disagree with each other |
| B5 H-4 hot-plug | Hot-plug named as the load-switch sizing case | No mating rule, no operating procedure, nothing on RJ45's 750-cycle durability against a bonded-in chassis jack (A8 #8) |

### And one defect introduced by the fix itself

ADR 0004's **"Revised conductor budget"** block (L81–86) still reads:

```
SCLK      / DIG_GND     SPI to the DAC, ~1 MHz
MOSI      / CS
```

The pin-map fix landed in the **Pin assignment** table ~670 lines later. The
same ADR now states the old pairing and the new pairing, and the "~1 MHz"
there is D2 H24's unfixed 1-vs-2 MHz contradiction. This is precisely the
failure mode D2 was commissioned to catch, committed in the act of applying
D2's findings.

---

## Findings that conflict with each other

Acting on one of each pair undoes the other. Two were named in `VERIFIED.md`;
three were not.

### 1. Pins 4/5 — B5 S-1 vs A4 D1 / A8 #1 (named, and decided)

B5 wants `MOSI`/`CS` off pins 4/5 because published RJ45-for-other-purposes
standards leave them empty; A4 and A8 put `SCLK`/`MOSI` exactly there. Eight
conductors, eight signals, so 4/5 cannot be vacated without deleting one.
**Resolved:** ADR 0004 records the decision and the reason. This is the model
for how the rest should have been handled.

### 2. The series resistor — B5 H-1 vs A4 D3 (named, and decided)

Both reject 220 Ω. B5 argues toward 68 Ω on match; A4 wins on a number B5 did
not check — 68 Ω draws 48 mA against a 40 mA pad spec. **Resolved at 100 Ω**
in `bom.csv` and `carrier.md` — but see the partial-application table: ADR
0004 still carries both of the losing values, so a reader who starts from the
decision record gets the wrong answer.

### 3. `C-FILT-PITCH` vs `C-FB-PITCH` — B4 vs ADR 0006 vs `pitch-stage.md` (not named)

B4 (High) says `C-FILT-PITCH` at 10 nF on the feedback node spends the whole
stability margin — ratio 2.24 against a needed 2.00 — and that the fix is
either **raise `C-FB-PITCH` to 3.3 nF or drop `C-FILT-PITCH` to 4.7 nF**.
ADR 0006 says `C-FILT-PITCH` is **deleted** and `C-FB-PITCH` is **1 nF across
the feedback resistor**. `pitch-stage.md` says restored at 10 nF and 2.2 nF
output-to-(−). D1 A5/A7 says the stated 12.2 kHz corner reproduces from none of
them. **Four documents, three topologies, and a stability claim that depends on
which you read.** Raising `C-FB-PITCH` per B4 makes ADR 0006's 1 nF *more*
wrong; adopting ADR 0006's "across the feedback resistor" makes B4's ratio
analysis inapplicable and, by `pitch-stage.md`'s own number, leaves 18° of
phase margin. Nobody noticed these three were the same argument.

### 4. `R-KEY-PU` value — A1 H2 / `cluster-boards.md` vs C4 §7.4 vs A2 #4 (not named)

`cluster-boards.md` L463 and `carrier.md` L346 carry an open trade on
`R-KEY-PU` 2.2 kΩ vs 10 kΩ, on the grounds that 2.2 kΩ loads the ADC's
reference at 25.8 mA rather than 5.9 mA. **C4 §7.4 says explicitly: going back
to 10 k is "not worth doing" — it removes the one term that was already
inaudible.** **A2 #4 says the same thing from the other side:** the pull-up
term is the *smallest and most benign* error on `VDD_ADC`, and the MCU's own
transient load and the buck's 330 kHz ripple are 10–50× larger. Meanwhile the
applied block just raised the quantity 21→24, making the load worse by ~14 %
for the three free bits — which A1 H2's *preferred* resolution (strap them,
zero parts, zero current) would have avoided entirely, and which was declined
in favour of resistors. **Three agents say the rail load is the wrong thing to
optimise; the one change made optimises it in the wrong direction.** Nobody
connected them.

### 5. Where breath is band-limited — ADR 0003 vs `carrier.md` vs A2 #8 vs A5 F-CM-1/C2 N-FILT-1 (not named)

D2 H32 records that ADR 0003 says "band-limit at both ends, around 500 Hz"
while `carrier.md` says "**do not** add a cap at `R-SER-BREATH-INST`". On top
of that: A5 F-CM-1 recomputes the module's differential corner as **459 Hz**,
not 482; A2 #8 says the instrument's 564 Hz anti-alias gives 16.6 dB where it
matters, not the 55 dB the page quotes; C2 N-FILT-1 breaks the RF-rectification
mechanism the 482 Hz pole is justified by; A8 lists "482 Hz filter at the
module ahead of the in-amp" as one of three choices that **must be protected in
any rework**. Four agents are adjusting the same filter for four different
reasons and one of them says do not touch it. There is no owner and no single
number.

### 6. Bus +5 V vs the level-shifter threshold — B3 §5.3 vs ADR 0004 (latent)

B3 §5.3 says there is no reason to put the 74AHCT125 on the bus rail; ADR 0004
says the AHCT threshold argument is *better* on the local 5.21 V rail — which
is B3's own conclusion. The two agree, and the corpus still asserts the
opposite justification. This only looks like a conflict because the ADR's
stated reason ("the only thing on the unprotected pin is a $0.30 buffer") is
the sentence B1 #9 refuted. Fix #2 and this one resolves itself.

---

## Audit of the claims made in the user's name

### `VERIFIED.md`'s "Confirmed" contradictions — are they real, and are they fixed?

All seven were real; I re-checked each against the repo. Disposition:

| Claim | Real? | Fixed? |
|---|---|---|
| `CLR` pull-down vs `R-CLR-PU` | Yes | **Yes** |
| `R1b` absent from `carrier.md` | Yes | **Mostly** — drawing yes, component table no |
| `R-ISO-REF` absent from `carrier.md` §2 | Yes | **Yes**, and the compensation gap was caught too |
| `C-FB-PITCH` 1 nF vs 2.2 nF | Yes — still true at L29/L179 vs L134/BOM | **No** |
| ADR 0006 "1 nF across the feedback resistor" | Yes — L611–612, unchanged | **No** |
| LM311 / 74HC123 still drawn; `C-DECOUPLE` should be 19 | Yes | **Partly** — qty fixed, enumeration not; four other documents still depend on the deleted parts |
| Marker 6/5 in `carrier.md` | Yes | **Partly** — table fixed, two adjacent prose claims left stale |

So `VERIFIED.md` is accurate as a finding of fact. Its weakness is what
happened next: **four of the seven it hand-verified are unfixed or
half-fixed**, and the two it flagged as this session's own regressions
(`carrier.md` marker staleness) were only half-corrected, in the same file,
in the commit that cited them.

The "reference designators that do not resolve" list is fully closed:
`R-SCLK-SER`/`R-MOSI-SER`/`R-CS-SER` collapsed into `R-SPI-SER`, and
`F-CHAIN`, `U-TVS-CHAIN`, `R-CHAIN-SER` all have rows. `R-LED` and `R-OE-PU`
are now explicitly retired in prose. This is the cleanest piece of the block.

The "errors introduced in this session" list: the 3V3-vs-GND switch figure is
fixed and labelled; the three unbudgeted pull-ups are fixed; the marker
staleness is half-fixed.

### `VERIFIED.md`'s two "agent claims NOT confirmed as stated"

**B2's brief — the assessment is correct.** I confirmed against
`pitch-stage.md` L49–51: the jack range is −2 → +7 V with a −2.500 V
intercept, not ±5 V about +2.500 V. B2 judged against the repo rather than the
brief and said so in its §1. Correctly recorded, and worth having recorded.

**A6 F2 — the assessment is wrong, or at least over-stated.** `VERIFIED.md`
says A6 "attributed a channel-7 refresh contradiction to ADR 0006 versus
`firmware/README.md`" and that the contradiction actually "sits *inside*
`firmware/README.md`… Right defect, wrong parties."

But ADR 0006 L186 does say, in its update-rate table, *"Mod offset | written
once at boot"*. A6 cites it precisely — its own §4 table names "ADR 0006
update-rate table" as the source. **A6's attribution of one half of the
contradiction is correct.** What A6 got wrong is only the other half: it said
`firmware/README.md` says "refresh every pass", when in fact that file says
*both* (L50 "written once at boot (ADR 0006)"; its statelessness rule
"refresh all six populated channels every pass"). D1 A23 and D2 H19
independently list ADR 0006 as a party to the same contradiction, and D2 H19
adds `mod-channels.md` and `latency-budget.md`.

So the correct statement is: **a five-way contradiction, of which A6 named two
parties and mislabelled one of them.** `VERIFIED.md` downgraded a correct
citation to "wrong parties", and the net effect was that nothing got fixed.
ADR 0006 L186 and `firmware/README.md` L50 both still read "written once at
boot" today, and A6's point stands: the once-at-boot reading is the latent
failure that pins four jacks at +11.45 V after any `CLR`.

### Today's commit messages — which claims are overstated

**`b1142b4`, items 1–5: accurate.** The five must-change fixes are real, they
are where the message says they are, and the reasoning is recorded in the
files. The `power-entry.md` load-switch rebuild in particular is better than
its description — it refuses to pick a capacitor value *because* three
reviewers disagreed, which is the right call and is recorded as such.

**Overstated claims:**

1. **"Not applied, and recorded as decisions rather than drifted into:
   dropping the bus +5V rail…"** — **false**. No record exists anywhere. The
   ADR section it would live in is unchanged, and the sentence three agents
   refuted (`"kills the buffer and nothing else"`) still stands in two files.
   The other two items in that sentence (the free bits, the pitch bend) *are*
   properly recorded; this one is not.
2. **"the key timings become 119.9 us and 5.92 us"** — applied in
   `cluster-boards.md` only. ADR 0001 L225–226 and `bom.csv` `C-KEY` still
   carry 125 µs / 5.7 µs, and `cluster-boards.md`'s own L163 still refers to
   "the 125 µs release filter" eight lines below the corrected table.
3. **"R-OUT-PROT's rating is raised"** — the *note* was raised. The BOM's
   value field still reads `>=500mW`, which is the figure both agents said was
   marginal, and `pitch-stage.md` still reads ≥250 mW, which is the figure D1
   flagged before this review wave. Nothing that a purchaser or a layout
   reader would act on changed.
4. **"the SPI series resistors are one refdes … and the value goes 220R to
   100R"** — true of `bom.csv` and `carrier.md`. ADR 0004, which is where the
   value is *decided*, still says 220 Ω in its decision line and 68 Ω in its
   deadline section.
5. **"the marker's left-thumb pair is flipped"** — true, and well recorded.
   But C1's stated root cause (the bit map lives in prose, not in
   `key-layout.yaml`, contrary to ADR 0010) was not addressed, so the hole is
   closed and the mechanism that opened it is not.

**`745af8c` (10HP):** accurate, and it is the correct response to B1 #3. One
gap: it withdraws ADR 0004's "16–20 mm knobs" claim but does not touch B1 #11
(current declaration) or B1 #12 (D2 sized at the trip current), which were
ranked equally High in the same report.

**`efebba9` (breath response):** accurate about B6 4.1, and honest about its
own open items. It notes A5 F-OFF-1 (the `POT-OFFSET` detent lands ~20° off
zero) in passing as a contrast — **and leaves F-OFF-1 itself unfixed**, while
consuming *both* remaining spare OPA2197 halves, which is the resource A5's
recommended fix for F-OFF-1 needed. The commit says so; the corpus does not
record that the fix is now foreclosed without adding a package.

---

## The one-line verdict

The applied block is good work on the findings it chose, honestly reasoned and
well cited. Its defect is selection, not execution: **it fixed the five things
`VERIFIED.md` had already hand-checked, and then stopped**, while ten of the
twenty reports produced no corpus change of any kind and the ROADMAP — the
only place a builder looks for what is still open — gained nothing from a
twenty-agent review. The most dangerous single item is not any individual
dropped finding; it is that the commit message reports a decline that never
happened, which means the record of *what was considered* is now itself
unreliable.
