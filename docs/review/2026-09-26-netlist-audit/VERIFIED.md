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

## Slices still running

N2, N3, N4, N8.
