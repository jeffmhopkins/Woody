# Verified by hand, by id

`CLAUDE.md`: *findings are claims.* Several in this repository's history have
been wrong, and one was wrongly marked disputed — which is worse, because a
wrong finding gets caught by the next reviewer while a finding filed as handled
does not. Nothing below is repeated onward until it appears here with its
verification.

**Recorded as each slice lands, not at the end.** The previous wave produced
377 findings and closed none of them by id, and `CLAUDE.md` records that as the
measured reason ten consecutive rounds were judged partial: verification
answered findings by restating them in prose, so "every one hand-verified" was
true of *reports* and false of *findings*.

## N6 — the master's directions, both ends

Slice reports 22 findings over 55 master nets and 151 endpoint assertions, with
nothing left unresolved. Four verified so far; the rest are unverified and must
not be acted on or repeated until they are.

| id | verdict | verification |
|---|---|---|
| N6 structural claim | **CONFIRMED, with one correction to its wording** | "Nothing in the repo compares the master to an `## Interfaces` table" is right in substance. `grep -rln Interfaces tools/` returns `tools/check-conservation.py`, so the claim as phrased overstates: that file *mentions* the table in a comment at line 118 and never reads one — it is a word-shingle conservation checker for a page split, taking `<rev> <source> <dest>...`. No tool reads a Dir or Peer cell as data. `[test]` |
| N6-1 | **CONFIRMED** | `hardware/carrier/circuit.yaml` does not exist; `grep -c "^\| Node \| Dir" hardware/carrier/carrier.md` = 0; `grep -rn "carrier/carrier" --include=circuit.yaml hardware/` exits 1. The id was invented by `hardware/carrier/netlist.yaml` and is the master's most-connected endpoint. `[test]` |
| N6-2 | **CONFIRMED** | `spi-link.md:38-40` carry Dir `out` on `SCLK`, `MOSI`, `CS_MOD` against `driver: carrier/carrier` in the master and `dir: in` in that circuit's own netlist. `[repo hardware/interfaces/spi-link/spi-link.md:38-40]` |
| N6-4 | **CONFIRMED, and sharper than reported** | `power-entry.md:29` lists `interfaces/spi-link` as a `DAC AVDD` receiver and states **"Not `module/digital-and-supervision`"** in bold, while the master now names that circuit a receiver because `R-PULL-SYNC.2` returns to the rail. The page's negation argues about the 74AHCT125's *supply* (bus +5 V), which is a different question from where a pull-up on its output returns — so the bold denial does not refute the new receiver, and one of the two still has to move. `[repo hardware/module/power-entry/power-entry.md:29]` |

**Not yet verified, not to be repeated:** N6-3, N6-5 through N6-22.

## N1 — feedback and loop topology

Slice reports 9 findings over all 14 feedback-bearing devices, and states
explicitly which circuits contain no feedback network rather than leaving the
gap silent. Two verified so far.

| id | verdict | verification |
|---|---|---|
| **N1-1** | **CONFIRMED — the LM317's divider legs are swapped and the DAC rail is 1.65 V** | `hardware/module/power-entry/netlist.yaml`: `DAC_AVDD` (the OUT node) carries `R-REG-SET-HI.1` = **475 Ω**, and `AGND_MOD` carries `R-REG-SET-LO.2` = **150 Ω**, so OUT→ADJ is 475 and ADJ→GND is 150. `[calc] 1.25 x (1 + 150/475) + 50 uA x 150 = 1.652 V`. `config/figures.yaml:349` states the settled derivation as `1.25 x (1 + 475/150) = 5.208 V`, which requires the opposite assignment — 475 on ADJ→GND. The figure is `status: settled`, owns the quantity, and carries `floor: 5.00 V, HARD` because the DAC8568's C grade is specified only for AVDD 5.0–5.5 V. **And the BOM says what the netlist says:** `R-REG-SET-HI` (475R) is described *"LM317 divider, ADJ to OUT"* and `R-REG-SET-LO` (150R) *"ADJ to GND"*. So the netlist transcribed the BOM faithfully and the BOM contradicts the figure register. `[test]` `[calc]` `[repo config/figures.yaml:349]` `[repo hardware/bom.csv]` |
| N1-2 | **CONFIRMED by reading, not yet by injection** | `breath-output-stage`'s `RAIL_POS`/`RAIL_NEG` are single-endpoint nets in `external_endpoints` whose stated reason is that the clamp rails terminate outside the circuit — while `MODULE_ANALOG_NEG12` is a declared port of that same circuit, already carrying `R-BREATH-OFFNEG.1`. Every other circuit with the same BAV99 nets it to the rail ports. `[repo hardware/module/breath-output-stage/netlist.yaml]` |

**Not yet verified, not to be repeated:** N1-3 through N1-9.

## N7 — instances, `replicated:`, `section:`, `of:`

Slice reports 15 findings and closes its own item list with arithmetic. Three
verified, two of them fail-opens in the check I described in PR #2 as *"the
count a per-circuit check structurally cannot do"*.

| id | verdict | verification |
|---|---|---|
| **N7-8** | **CONFIRMED BY INJECTION — one `section:` token exempts a whole row from over-use detection** | `tools/check-netlist.py:228` puts `if sections[row]: continue` **before** the `if n > have` test. In a clone at `d1f0cb7`, nine instances of `R-OUT-PROT` against a qty of 6 report `instances: R-OUT-PROT is placed 9 time(s) across all netlists and the BOM buys 6`; adding `section: half` to **one** of the nine makes that line vanish and the summary reads `101 row(s) placed exactly to BOM qty, 5 counted by section` — a board three parts short, reported clean. Latent on 4 rows today. `[test]` |
| **N7-9** | **CONFIRMED — a row placed zero times is invisible** | `used` is a Counter over placed instances, so a row nobody places never appears in either the exact count or the short list. Census by hand: 155 BOM rows = **113 placed + 30 in `unplaced.csv` + 12 placed nowhere and in neither list** — `C-BULK-DISP`, `LK-SER`, `MECH-COAT`, `PANEL`, `PCB-CARRIER`, `PCB-CLUSTER`, `PLATE-THUMB`, `PLATE-TOP`, `R-SER-TERM`, `R-TRIM-RANGE`, `SW-THUMB`, `WIRE-LOOM`. Several are mechanical and belong in no netlist, which is the real gap: there is no third category for them. `[test]` |
| **N7-10(b)** | **CONFIRMED — the tool's own docstring restates a wrong fact** | `tools/check-netlist.py:199` says the seventh `R-OPAMP-IN` is claimed for *"the VREFOUT follower, which no drawing shows and no netlist places"*. The follower **is** placed — `U-PITCH-REFBUF` at `hardware/module/pitch-stage/netlist.yaml:28` — and **is** drawn, `pitch-stage.md:31` shows `½ OPA2197`. The unplaced part is the resistor, not the follower. A restated fact gone wrong inside the tool written to catch restated facts. `[test]` `[repo]` |

**Not yet verified, not to be repeated:** N7-1 through N7-7, N7-10(a), N7-11 through N7-15.

## N5 — the deliberate holes

Slice enumerated what the checker only counts: **39 `external_endpoints`
entries across 12 of the 22 netlists, and exactly 39 single-endpoint nets —
the two sets are identical.** No undeclared single-endpoint net, no stale entry
naming a net that has since gained a second endpoint. It then classified them:
8 genuinely undecided, 14 decided no-connects, 14 consequences of a modelling
choice, 1 physical, 2 not holes at all. 12 findings. Three verified.

| id | verdict | verification |
|---|---|---|
| **N5-1** | **CONFIRMED — and it is the same defect N1-2 found independently** | Two cold slices that could not see each other filed `breath-output-stage`'s `RAIL_POS`/`RAIL_NEG` as false holes. Under this wave's own method that agreement is evidence. The stated reason — the clamp rails "terminate on the module's supply rather than inside this circuit" — is refuted by `MODULE_ANALOG_NEG12` being a declared port *and* a two-endpoint net in the same file, by the page's Interfaces row "`D-JACK-CLAMP` returns to both rails", by `nets.yaml` listing the circuit in both rails' `receivers:`, and by every other circuit netting the identical BAV99 normally. `[repo]` |
| **N5-3** | **CONFIRMED — "four different rows" is wrong, and it is my sentence in three files** | Parsed the allocation table: `right_thumb` and `right_hand` are **identical** as a switch/marker/free map (`sw ×6, M, M`) and share marker positions `(B, A)`. Three distinct rows, not four. The claim appears in `key-register/netlist.yaml`, `key-marker-and-bits/netlist.yaml` and `nets.yaml`'s `KEY_BITS` **and** `MARKER_BITS` notes. The conclusion survives — three rows is still not one, so a shared netlist cannot name the inputs — but **a stated count moved under the sentence stating it**, which is one of the four shapes `CLAUDE.md` says to slice for. The slice's replacement fact checks out: the marker **level** map *is* distinct on all four — `RT B=1/A=0`, `RH B=0/A=1`, `LT D=0/C=1`, `LH C=0/B=1`. `[test]` `[repo key-marker-and-bits.md:80-84]` |
| **N5-5** | **CONFIRMED — a `port:` in two nets is never counted, and I relied on that** | `tools/check-netlist.py:406-416`: `declared_pins` and `used` are built only from `REF.PIN` string endpoints; the `isinstance(ep, dict)` branch checks the port is declared and then `continue`s without recording it. So any two nets in one file can share a port silently. I used that deliberately as a bundle-boundary convention — and `key-marker-and-bits`'s `MARKER_HIGH` is that convention's accident: its only endpoint is `port: V3V3_CHAIN`, which another net in the same file already carries. Two names for one node, same for `MARKER_LOW`/`GND_CHAIN`. The tool cannot tell the convention from the accident. `[repo tools/check-netlist.py:406]` |

**Not yet verified, not to be repeated:** N5-2, N5-4, N5-6 through N5-12.

**Holes the slice attacked and could not break** — recorded because a hole that
survives an attack is a result: `CS_PULLUP_TOP` (the "rail does not exist on
this board" claim is true, both halves of the contradiction are real, and it
names what decides it — offered as the model the other 38 should match), the
four console-pair nets, `ON_DIVIDER`, `TRIM_OFFSET_BOTTOM`, `TVS_SPARE`, and
`DAC_CH6/CH8_UNUSED`, whose `[derived, not cited]` disclosure the slice calls
the right way to write a derived assertion.

## N3 — rails, supplies, decoupling

13 findings. Four verified. Its N3-1 is N1-1 found independently — **the second
cold slice to reach the LM317 divider**, with two corroborating sources the
first did not have.

| id | verdict | verification |
|---|---|---|
| **N3-1** | **CONFIRMED, and this is now two independent cold slices plus my own check of three files** | Same defect as N1-1. N3 adds two sources I had not used: ADR 0004's *"150 Ω / 475 Ω instead of 240 Ω / 768 Ω … halves the I_ADJ contribution"* requires R2 = 475 on ADJ→GND, and `U-REG-DAC`'s *"~13 mA load including the divider"* only works at 1.25/150 = 8.3 mA, against 2.6 mA if 475 were the OUT→ADJ leg. It also names the one place that is right — **the drawing**, which reads `150R/475R`. And it establishes the provenance: both rows say *"SPLIT OUT 2026-09-22 FROM AN AGGREGATE ROW THAT COULD NOT BE NETLISTED"*, so the split invented the positions, assigned the values to the wrong ones, and the netlist transcribed it faithfully. `[calc]` `[repo docs/decisions/0004-cv-interface-module.md]` `[repo hardware/bom.csv]` |
| **N3-3** | **CONFIRMED — the decoupling count includes a pin that does not exist** | `C-DECOUPLE`'s enumeration reads *"DAC8568 AVDD+DVDD = 2"*. In the banked SBAS430E, `DVDD` occurs **0** times (`AVDD` occurs 130); the PIN DESCRIPTIONS table lists exactly one supply row, `3 / 2 / AVDD`; and the netlist's own 16-pin list for `U-DAC` has only `AVDD`. Pre-existing corpus prose, and precisely the class the netlists make checkable for the first time — a row's enumeration can now be reconciled against the pins that exist. `[datasheet datasheets/analog/DAC8568CIPW.pdf, PIN DESCRIPTIONS]` `[test]` |
| **N3-6** | **CONFIRMED — a net in my netlist is named the boolean `True`** | `yaml.safe_load` on `hardware/module/umbilical-load-switch/netlist.yaml` returns net keys `[… 'FB', True, 'PWR_GND', …]`. The net written as `ON:` is parsed as a bool under YAML 1.1. The same file quotes the **pins** `'ON'` and `'NO'` two lines earlier *with a comment explaining this exact trap* — and then falls into it on the net name. A KiCad export would emit a net called `True`. `[test]` |
| **N3-13** | **CONFIRMED as a characterisation of `rails:`** | Matches what I know of the code: a rail the circuit already receives is accepted whatever it is, a rail the board lacks is caught, and omitting `rails:` entirely is silent. That third case is N3-2 — `U-REF-BUF` is the only one of ten placed OPA2197 halves with no `rails:` and no supply pins, so per the authoritative file it has no supply. Not separately re-tested; recorded as CONFIRMED-BY-READING. `[repo tools/check-netlist.py]` |

**Not yet verified, not to be repeated:** N3-2 (read, not tested), N3-4, N3-5, N3-7 through N3-12.

**Clean and checked rather than assumed**, which is worth as much as a finding:
the slice attacked the single-supply assertion on the carrier's OPA2197 halves
and found it correct from four directions, then produced a number no document
states — `[calc]` against SBOS737C the breath buffer's worst-case output floor
is ~125 mV against the sensor's 0.152 V minimum pedestal, **≥27 mV of margin**,
real but thinner than anything written, and silently broken by a non-RRIO
substitution.

## N4 — pin identity against the banked datasheets

11 findings. Both commissioned claims answered, and the largest finding is one
neither question asked for. Three verified.

| id | verdict | verification |
|---|---|---|
| **N4 claim 1** | **CONFIRMED, and the warning is on the wrong half** | The letter map is fine: all 16 `U-DAC` pin names are exact against SBAS430E, the ordinal map is the only reading available, and my `[derived, not cited]` disclosure was right that no corpus document states it. But the exposure is the **address**, not the letter. Extracted from the command table: `0 0 0 0` → *"DAC Channel A"*, `0 0 0 1` → B, `0 0 1 0` → C — the address is **0-based** — and the datasheet never numbers a channel at all (`"Channel 1"` and `"DAC Channel 1"`: 0 hits each). So firmware writing `address = N` for "channel N" selects letter N+1 and rotates every output by one pin: pitch (ch1) leaves on `VOUTB`, which this netlist wires to **mod 1's jack**, and the 3.3333 V shared reference (ch7) leaves on `VOUTH`, declared `DAC_CH8_UNUSED` — producing exactly the all-four-mod-jacks-at-`4·Vdac` failure `firmware/README.md` names for a different cause. `[datasheet datasheets/analog/DAC8568CIPW.pdf, command table]` `[test]` |
| **N4-2** | **CONFIRMED — eleven op-amp halves resolve to no pin, and nobody marked it** | Enumerated across all 22 netlists: `U-OPA-PITCH section A` is claimed by **three** circuits (`pitch-stage/U-PITCH-REFBUF`, `breath-output-stage/U-BREATH-BUF`, `breath-receive-stage/U-REF-BUF`), `section B` by **two**, and five more carry `section: half`, which is not a section. No package instance is named anywhere, and on an OPA2197 SOIC-8 the letter **is** the pin set. Invisible to the checker because `section` is only read as a truthiness test to skip BOM counting. `[test]` |
| **N4 claim 2** | **CONFIRMED as harmless, with two real problems beside it** | The gate assignment is unfalsifiable and fine — the gates are identical. Recorded unverified but worth the fixer's attention: `led-strip-drive` names gates with **letters the device does not have** while `digital-and-supervision` uses numbers, the same unjoined naming shape; and all four `OE` are tied to GND on both parts against the datasheet's explicit recommendation to pull `OE` to VCC for guaranteed Hi-Z through power-up, with neither note recording the departure. |

**Not yet verified, not to be repeated:** N4-1, N4-3 through N4-11.

**The slice's closing observation, which I think is the most useful sentence
this wave has produced:** four times a netlist had to join a logical name the
corpus uses (channel 7, gate D, section A, R1) to a physical name the silicon
uses (VOUTG, 3Y, +IN A, pins 2 and 7). Twice I noticed and wrote
`[derived, not cited]`, and **those two are the safe ones, because they are
declared.** The two nobody marked are the two that bite. The marker went on the
visible half.

**Two traps recorded for whoever fixes these:** INA828 SBOS792A §8.1 prose
calls `REF` "pin 6" while its own Pin Functions table says REF=5, OUT=6 — the
table is right and the prose is a datasheet typo, so do not "correct" the
netlist from §8.1. And the banked WS2815 PDF has no text layer at all; the
slice rendered p.4 at 12x to confirm that the recommended circuit ties the first
pixel's `BI` to `GND`, which is the claim the "two spare gates" argument rests
on. It is correct.

## N2 — grounds and references

17 findings over all 26 `dir: ref` ports and every pin on every net they name.
Four verified.

| id | verdict | verification |
|---|---|---|
| **N2-1** | **CONFIRMED — all six jack sleeves bond the module analog star to rack ground** | Enumerated: `J-CV-PITCH.SLEEVE`, `J-CV-BREATH.SLEEVE` and `J-CV-MOD1..4.SLEEVE` are all on `AGND_MOD`, across three netlists. `pitch-stage.md` and `mod-channels.md` both say of that net *"Not a return path"*, and ADR 0004 has the analog region joining the star *"and nowhere else"*. The only occurrence of "sleeve" in any page is about a plug shorting tip to sleeve on insertion — **no page states where a sleeve returns**, so these three netlists are the first and only assertion of it, and all three picked the star without flagging the choice. `[test]` `[repo]` |
| **N2-2** | **CONFIRMED — `DIG_GND` has no instrument end, and both halves of my own check stayed silent** | `carrier/carrier` declares 20 ports and `DIG_GND` is not one of them; `spi-link/netlist.yaml` nets `J-UMB-INST.8` and stops; the master's `DIG_GND` lists `origin: module/power-entry` and references only `interfaces/spi-link` and `module/digital-and-supervision`. So `CS_MOD`'s ground partner — the whole derivation of `umbilical-pinmap` — is open-circuit at the driving end, and the SPI clamp on that board goes to `PWR_GND` instead. **This is the gap in the bidirectional check**: a net that is simply *missing* a participant stays invisible, because the forward pass walks only circuits the master names and the reverse pass walks only ports the netlists declare. Neither side can miss what neither side mentions. `[test]` |
| **N2-3** | **CONFIRMED — same as N6-1, found independently** | Third cold slice to arrive at `carrier/carrier` having neither a `## Interfaces` table nor a `circuit.yaml`. N2 adds why it matters here: it is the circuit N2-2 needs, which is what makes N2-2 invisible. |
| **N2-11** | **CONFIRMED in substance, overstated in detail** | Slice says all three `candidates:` citations in `dig-gnd-topology` point at wrong lines, one past the end of a 196-line file. Checked: `power-entry.md:495` against a **197**-line file — past the end, confirmed; `digital-and-supervision.md:53` lands on a blank drawing gutter (`│  │  │`) — wrong line, confirmed; but `0004-cv-interface-module.md:627` lands on *"…so it is the one point entitled to be called ground"*, which is on topic. So **two of three**, not three, and the file is 197 lines not 196. Recorded corrected rather than repeated. `[test]` |

**Not yet verified, not to be repeated:** N2-4 through N2-10, N2-12 through N2-17. The slice marks N2-14 and N2-16 weak by construction.

**Clean, and the most reassuring result in the wave:** the corpus's
most-warned-about merge **did not happen**. `AGND_SENSE`, `AGND_INST` and
`AGND_MOD` are never merged; `AGND_SENSE` is `in`/`out` in all three netlists
and never `ref`; `R1b` sits between the star and the conductor exactly as
required; `MECH-GNDBOND` is on `PWR_GND` and nowhere near AGND. The slice's
summary of the whole claim type: **no netlist makes a reference tie the corpus
does not place — the defect is omission, not misplacement.**

## N8 — the author's own claims

16 findings. **Its verdict on the substance is that the asserted defects are
real**: 19 before-states reconstructed with no fabricated finding, citations
following in the same commit where checked (`R-MODGAIN` all 7 sites,
`R-ADCDIV` all 8), and all nine reproduced injections firing for the reason
claimed. What fails is the **coverage** the conversion claimed for itself.
Three verified.

| id | verdict | verification |
|---|---|---|
| **N8-2** | **CONFIRMED — there is an eighth aggregate row, and my stated criterion for finding the seven was false** | `C-BULK-RAIL` is `'100uF (+12V) / 47uF (-12V, +5V) 25V electrolytic'` at qty 4 — on the very page whose `4 × 47 µF` drawing defect started this exercise. It survives because the value test at `check-netlist.py:375` is a **substring** match: `norm('100uF')` and `norm('47uF')` are *both* inside that part field, so an instance may claim either and pass. So "no instance could state a value that matched it" is **not** what selected the seven rows I split — the checker's silence was. A two-value aggregate row is unfalsifiable by construction under a substring test. `[test]` `[repo hardware/bom.csv]` |
| **N8-1** | **CONFIRMED by reading the comparison** | The drawing check only reaches `[REFDES value]` brackets. `breath-response-shaper.md` draws `R1 20k` and `R2 10k` as **bare text**, so the three BOM rows commit `8d66e2d` created *because* "a netlist cannot be written without noticing" have drawn values that nothing compares — and the netlist's `drawn_as: R1`/`R2` aliases point at labels that exist in no bracket. Meanwhile `CLAUDE.md` and `hardware/README.md` both claim "every `[REFDES value]` label in a drawing" is checked, unqualified. Five such bare-text sites corpus-wide, all currently correct, so latent. `[repo]` |
| **N8-14** | **CONFIRMED** | Commit `cfaa6a7`'s body says the pending list "just grew from five to eight". The denominator change did take it to 8, and then the same commit converted one page, so the checker's own output at that commit prints **7**. A stated count that moved under the sentence stating it, in a commit whose subject line is about an honest denominator. `[test]` |

**Not yet verified, not to be repeated:** N8-3 through N8-13, N8-15.

**N8 checked specifically for new fail-opens introduced by my fixes and found
none** — `norm()` collapsing `50mΩ`/`50MΩ` comes from the `.lower()` that was
always there, `COUNT`'s `re.I` strips `x7` out of `X7R` symmetrically on both
sides so nothing is misjudged, and the box-glyph drawing detector would miss a
pure-ASCII schematic but no live page is affected. Latent risk, recorded.

**And it names the best artefact in the branch**: `a4eaa23`, the commit that
corrected the previous one for claiming 0 problems when the checker said 3.
It reproduces to the digit.

## All eight slices are in. Wave closed for reporting; fixes not started.
