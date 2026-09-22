# G6 — Can you actually order and build this?

**Slice:** G6, BOM buildability, cold.
**Revision measured:** `a4b80b1`. `git log` HEAD at the time of writing is
`25cc740`; `git diff --stat a4b80b1..HEAD` is one file, `docs/review/2026-09-22-goal-verification/README.md`,
which I did not open. `[test] git diff --stat a4b80b1..HEAD` → `1 file changed, 81 insertions(+)`.
The corpus is therefore identical at the two revisions and every claim below
holds at `a4b80b1`. `tools/` was **not** pinned and I did not touch it.
**Cold:** I read nothing under `docs/review/`, `docs/log/` or `docs/research/`.
One near-miss: `tools/merge-bom.py`'s docstring quotes "D4 of the 2026-09-21
pre-merge review" verbatim — I read the tool, not the review.

**Method.** Parsed `hardware/bom.csv` (`[test] python3 -c "import csv; …"` →
141 lines, 140 data rows, 11 columns, CRLF), walked every row, and rebuilt the
ref → fragment map from the 26 fragments directly so every finding is filed
against the fragment a fix would go in. `[test] python3 tools/merge-bom.py --check`
→ `bom.csv: checked 140 rows from 26 fragments | 0 problems`, exit 0, so the
master does match its fragments and reading the master for analysis is safe.
Package claims were checked against the banked PDFs with `pymupdf`.

---

## Bottom line

**Four things stop someone placing this order today. Everything else is either
buyable or honestly marked open.**

1. **Four parts the schematics draw have no BOM row at all** — `J-DISP`,
   `J-LED-L`, `J-LED-R`, `C-ADC-BULK` (G6-1). You cannot assemble the carrier
   without them and nothing in the order covers them.
2. **`J-UMBILICAL` is not a part number** (G6-2). "Neutrik etherCON D-series
   chassis (variant TBD)", qty 2, status `candidate` — and the two ends almost
   certainly want different variants.
3. **`R-PRECISION` is marked `selected` and cannot be ordered** (G6-3): the
   LT5400 order code has two letter fields and neither is chosen.
4. **The 82 nF C0G package is contradicted between two rows** (G6-4), one of
   which says in its own notes that the other's package does not exist.

Two more will cost money rather than block: **`U-RESP` double-counts an
OPA2197 package** (G6-5) and **`D-TVS-BREATH` names a SOD-523 part in a
SOD-323 footprint** (G6-6).

`Q-LOADSW` and `R-ILIM` are also unbuyable today, but both are `open` **with
what decides them stated**, which the hardware conventions call correct. They
are listed under "correctly open" rather than as defects.

---

## BLOCKERS

**G6-1. Four parts are drawn, marked "proposed" on their own pages, and have no
BOM row.** These are not refdes-aliasing cases like `R_G` or `C_diff`; there is
no row under any name.

| drawn | where | what the page says it is | row? |
|---|---|---|---|
| `J-DISP` | `[repo] hardware/carrier/display-and-service-uart/display-and-service-uart.md:92` | **9-way**, "Proposed — see §6. Was 11-way before `EN`/`IO0` were withdrawn" | none |
| `J-LED-L`, `J-LED-R` | `[repo] hardware/carrier/led-strip-drive/led-strip-drive.md:115` | **4-way each**, "Proposed — 12 V, GND, `DI`, `BI`" | none |
| `C-ADC-BULK` | `[repo] hardware/carrier/breath-adc/breath-adc.md:103` | **10 µF X7R**, bulk at MCP3202 `VDD`/`VREF`, "proposed" | none |

`[repo] hardware/carrier/carrier.md:59,72,132,232,299,302` draws all four in the
board-level figure. `[test] python3` regex over `hardware/**`, `docs/decisions/**`,
`docs/reference/**`, `config/**`, `firmware/**`, `README.md`, `ROADMAP.md` for
each of the 140 refdes confirms none of these four strings is a BOM ref.
`tools/check-staleness.py` already reports them — `[test] python3 tools/merge-bom.py --check`
fired the `PreToolUse` hook, whose report lists them under *"drawn in a
schematic, no BOM row (17) — ADVISORY, not a failure"*
(`[repo] .staleness/report.txt:62-79`). Thirteen of those seventeen are deleted
names (`R-OFFINJ`, `R-TERM-CHAIN`, `R-PRESENCE`, `R-OE-PU`, `R-CLR-PD`, `LK-CLR`)
or local aliases already covered by a row (`J-UMB`→`J-UMBILICAL`,
`R-CS-SER`/`R-MOSI-SER`/`R-SCLK-SER`→`R-SPI-SER`, `R-IN`/`R-OFF`/`R-OFFNEG`→
`R-BREATH-SUM`/`R-BREATH-OFF`). **These four are not.** Fragment for a fix:
`hardware/carrier/display-and-service-uart/bom.csv`,
`hardware/carrier/led-strip-drive/bom.csv`, `hardware/carrier/breath-adc/bom.csv`.

Two of them also have no loom row to plug into: `WIRE-LOOM`
(`[repo] hardware/carrier/bom.csv:6`) is one row, qty 1, `part` = "Ribbon,
ground per signal — chained cluster to cluster", and its notes describe only
the **key chain**. The display loom (9 conductors, 360 mm,
`[repo] display-and-service-uart.md:56`) and the two LED looms have no
conductor count, no length and no connector anywhere in the BOM.

**G6-2. `J-UMBILICAL` is a product family, not an orderable part, and one row
covers two ends that probably need different variants.**
`[repo] hardware/module/power-entry/bom.csv:3` — `part` = "Neutrik etherCON
D-series chassis (variant TBD)", qty 2, package "panel mount", **status
`candidate`**. Its notes are excellent on geometry (bore D24.0 mm, flange
26 × 31 mm, the two diagonal D3.2 mm holes at ±9.5 × ±12.0, panel thickness
max 4 mm) and end with "Variant decided at E12/M7", so the decider exists —
but the status is `candidate`, not `open`, which is the "looks decided and is
not" case. Three separate places say the choice is live and consequential:

- `[repo] docs/decisions/0004-cv-interface-module.md:958-965` — "**Which
  etherCON variant at each end.** Feedthrough (NE8FDP-class) presents a plain
  RJ45 on the back … The cost is two more contact interfaces in every signal,
  including the +12 V path and the analog pair."
- `[repo] hardware/carrier/carrier.md:390-392` — "**The etherCON variant at the
  instrument end**, which decides whether this board carries an RJ45 jack
  footprint (**~16 × 14 mm, not in the BOM**) or eight wires."
- `[repo] hardware/unplaced.csv:7` (`J-UMBILICAL-CABLE`) — "NE8FDP is a
  FEEDTHROUGH receptacle that mates with any standard RJ45".

So one `qty=2` row may have to become two rows with two part numbers, and one
of the two branches pulls in a board RJ45 jack the BOM does not have. Both
`NE8FDP` and `NE8FDV` datasheets are banked
(`[repo] datasheets/MANIFEST.csv`, rows `connectors/NE8FDP-DATASHEET.pdf`,
`connectors/NE8FDV-DATASHEET.pdf`, `connectors/NE8FDV.kicad_mod`), so this is
decidable from documents already in the repo.

**G6-3. `R-PRECISION` is status `selected` on a part number that is two
letter-fields short of orderable.** `[repo] hardware/module/pitch-stage/bom.csv:10`
— `part` = "LT5400 1:1 quad (four equal 10k), MSOP-8 option", status
**`selected`**. Its own notes give the rule: *"ORDER CODE IS TWO LETTER FIELDS:
LT5400 + `<A|B matching>` + `<C|I|H|MP temp>` + MS8E-1#PBF"*, then state that
the grades differ materially — "Grade A is 0.01% matching, B 0.025%; A degrades
to ±0.0125% over −40/+85 °C while B is flat". Neither letter is chosen anywhere
in the corpus. The `-1` option and the MS8E package *are* pinned and both check
out: `[datasheet] datasheets/analog/LT5400.pdf` — "MS8E" appears 71×, "DFN"
0×, and the MSOP exposed-pad drawing gives `1.68 ± 0.102` × `1.88 ± 0.102`,
matching the row's "1.88 x 1.68mm EXPOSED PAD" exactly. **The package is right
and the part number is incomplete**, which is the harder half to notice.

**G6-4. 82 nF C0G/NP0 has two mutually exclusive packages in two rows, and one
row says the other's package cannot exist.**

- `[repo] hardware/module/umbilical-load-switch/bom.csv:12` — `C-GATE-LOADSW`,
  "82nF C0G/NP0 or film, 50V", package **"0805 or 1206"**, status **`selected`**.
- `[repo] hardware/module/mod-channels/bom.csv:2` — `C-FILT-MOD`, "82nF
  C0G/NP0", package "1210 or film - **VERIFY**", and the notes: *"PACKAGE IS
  PROBABLY WRONG: 82nF in C0G/NP0 almost certainly does not exist in 0805 -
  C0G permittivity puts that value in 1210 or larger. Unverified because every
  distributor site was proxy-blocked."*

Same value, same dielectric, same voltage class. If `C-FILT-MOD`'s reasoning is
right then `C-GATE-LOADSW`'s "0805 or 1206" is unbuyable — and `C-GATE-LOADSW`
is the part that programs the load-switch ramp, so it is not optional. This is
the shape `CLAUDE.md` §"Review waves" calls *a fix that did not reach the pages
citing it*: the finding was written on one row and the row with the same part
was not touched. Note also that `C-FILT-MOD`'s note argues against **0805**
while its own `package` field already says **1210** — the note is stale against
its own field, so a reader can reasonably conclude the question was settled when
it was not.

I could **not** resolve which is right: there is no capacitor datasheet of any
kind in `datasheets/` (`[repo] datasheets/MANIFEST.csv`, 101 rows, none a
ceramic capacitor), and I did not attempt distributor sites.

---

## WRONG PART OR WRONG PACKAGE

**G6-5. `U-RESP` double-counts an OPA2197 package. One physical part, two
rows.** `[repo] hardware/module/breath-response-shaper/bom.csv:5` — `U-RESP`,
part `OPA2197IDR`, package SOIC-8, **qty 1**, status `open`. Its own notes say
the opposite of what its `qty` orders:

> *"**THIS PACKAGE CONSUMES BOTH OF THE MODULE'S REMAINING SPARE OPA2197
> HALVES**, because the shaper needs one and POT-OFFSET's wiper needs the
> other … Fit this and the module has no spare op-amp capacity left."*

Three other places agree it is the spare halves of the existing six packages,
not a seventh package:

- `[repo] hardware/module/breath-receive-stage/bom.csv:2` (`U-OPA-PITCH`, qty 6)
  — *"Six packages, twelve halves, TEN used … **TWO SPARE — and U-RESP claims
  both of them if it is fitted**, so check that row before spending them."*
- `[repo] hardware/module/breath-response-shaper/breath-response-shaper.md:30`
  — "`U-RESP`'s two halves — **the last two on the module**"; and line 128,
  "**Both remaining OPA2197 halves**".
- `[repo] hardware/module/breath-output-stage/breath-output-stage.md:157` —
  "**Ten of twelve halves used across the module**".

`[calc]` I recounted the ten from the pages, not from the note: pitch amp and
VREFOUT follower (`pitch-stage.md:31,42`), mod ch7 V_ref buffer and four mod
channels (`mod-channels.md:39,52`), the `TRIM-BREATH-ZERO` REF buffer
(`breath-receive-stage.md:88`), and the gain buffer and summer
(`breath-output-stage.md:62,78`) = 2+5+1+2 = **10**. 6 packages × 2 = 12 halves,
2 spare. The enumeration in `U-OPA-PITCH`'s notes lists exactly ten items and
they match one-for-one. So `U-RESP` qty 1 buys a **seventh** package for halves
that already exist.

Corroboration from a fourth row: `[repo] hardware/module/umbilical-load-switch/bom.csv:5`
(`C-DECOUPLE`, qty 19) enumerates *"6 x OPA2197 on ±12V = 12, INA828 = 2,
DAC8568 AVDD+DVDD = 2, 74AHCT125, LT1641 VCC, LM317 in"* — `[calc]`
12+2+2+1+1+1 = 19 ✓. It counts **six** OPA2197 packages. If `U-RESP` were a
seventh package the decoupling count would have to be 21. So `C-DECOUPLE`,
`U-OPA-PITCH` and both response-shaper pages all say six; only `U-RESP`'s `qty`
says seven. **Fix in `hardware/module/breath-response-shaper/bom.csv:5`, not in
the master.**

**G6-6. `D-TVS-BREATH` names a SOD-523 part and specifies a SOD-323 footprint.**
`[repo] hardware/interfaces/breath-sense-link/bom.csv:4` — part "PESD12VS1UB or
equivalent 12V-standoff ESD diode", package **SOD-323**, qty 2.
`[web] https://www.nexperia.com/product/PESD12VS1UB` — the product page's own
title is "PESD12VS1UB (**ESD protection diode in SOD523 package**)"; the
datasheet is published as `PESD12VS1UB.pdf`, "ESD protection diode in SOD523
package", and Farnell lists it as "DIODE, TVS, SOD-523"
(`[web] https://uk.farnell.com/nexperia/pesd12vs1ub/diode-tvs-sod-523/dp/8737371`).
SOD-523 is ~1.6 × 0.8 mm against SOD-323's ~1.7 × 1.25 mm — a different land
pattern, not a tolerance.

This is exactly the failure `D-REVSHUNT` records having already had once
(`[repo] hardware/carrier/power-entry-instrument/bom.csv:10`: *"This row said
DO-214AC, which is the SS14's package"*), on the same kind of part.

**I could not check this against a banked document, and that is why it
survived:** `[repo] datasheets/MANIFEST.csv` carries `PESD12VS1UB` /
Nexperia with **`status=BLOCKED`** and no file. It is the only genuinely
undecided-package part in the design with no banked datasheet. The "or
equivalent" escape means a SOD-323 part exists in the family
(`PESD12VS1BA`-class), so the honest fix is to pin one of the two, not to
assume the footprint is wrong.

**G6-7. `U-TVS-CHAIN` asks for a 4-channel array in SOT-23-6, and the row three
positions away proves that combination is the 5-channel part.**
`[repo] hardware/interfaces/key-chain-loom/bom.csv:4` — part "4-channel TVS
array", manufacturer blank, package **SOT-23-6**, qty 1, status `open`.
`[repo] hardware/interfaces/spi-link/bom.csv:4` (`U-TVS-SPI`) states, from the
banked document: *"ORDER CODE IS SP0504BAHTG AND IT IS SOT-23-5, NOT SOT-23-6
[SP0504BAHT.pdf p.1 ordering table, package outlines pp.6-7]; SP0505BAHTG is
the SOT-23-6 part and brings a fifth channel."* I re-read the banked PDF and it
holds: `[datasheet] datasheets/discrete-and-power/SP0504BAHT.pdf` p.1 ordering
table gives `SP0504BAHTG` → package `SOT23-5`, CH `4`; `SP0505BAHTG` →
`SOT23-6`, CH `5`. The chain needs four signals (`SCK`, `SH/LD`, `SER`, `QH`),
so the channel count is right and **the package is the leftover from before that
correction landed**.

`U-TVS-CHAIN` is also one of only two `open` rows in the whole BOM that **do
not say what decides them** (see G6-15). Its notes end "U-TVS-SPI does exactly
this job for the umbilical's three" — which is a justification, not a decider.

**G6-8. `U-REF-BREATH` orders the grade the corpus believes is wrong.**
`[repo] hardware/carrier/breath-excitation-reference/bom.csv:2` — part
`REF5050AIDR`, status `candidate`. Its own notes: *"**THE GRADE IS A LIVE,
TRACKED DISPUTE** … the A suffix is the WORSE grade [Table 4-2 p.3: REF50xxI =
'High', REF50xxAI = 'Standard'] … and the fix is one letter in the order code
for the same package and pinout."* The register agrees and is blunter —
`[repo] .staleness/report.txt` "UNRESOLVED, tracked deliberately", entry
`ref5050-grade`: *"Since the whole reason for a separate reference is
scale-factor stability, **REF5050IDR is almost certainly the right answer** —
but it is a part change, not a documentation fix."*

The tracking is honest, but the practical consequence is that **the BOM as it
stands orders the wrong letter**, on a part that sets the breath channel's
ratiometric scale factor, and the mistake costs a reorder rather than a rework
only if it is caught before the basket.

**G6-9. `U-LOADSW` orders the commercial temperature grade and its own notes say
that is probably wrong.** `[repo] hardware/module/umbilical-load-switch/bom.csv:3`
— `LT1641-1CS8`, SO-8, status `candidate`. Notes: *"OPEN, AND DECIDED BY
TEMPERATURE RATHER THAN BY THIS DOCUMENT: the grade. This row orders the CS8
(0 to +70 °C); the IS8 is −40 to +85 °C and is the better part for a rack that
may sit in a hot van. **That is a part change, not a documentation fix — decide
it before the order.**"* The package is correct:
`[datasheet] datasheets/discrete-and-power/LT1641.pdf` — "S8" 7×, "SO-8" 1×,
no MS8 or DD variant in the banked revision. Same shape as G6-8: a `candidate`
row whose notes contain a live order-time decision.

**G6-10. `U-REG-DAC` names a part number that does not exist from the
manufacturer whose datasheet is banked for it.**
`[repo] hardware/module/power-entry/bom.csv:5` — part `LM317LZ`, manufacturer
**"multiple"**, package TO-92. `[datasheet] datasheets/discrete-and-power/LM317LZ.pdf`
is **TI's** SLCS144 and its Package Option Addendum enumerates
`LM317LCD`/`LCDR` (SOIC D), `LM317LCLP`/`LCLPR` (**TO-92**, package drawing
`LP`), `LM317LCPK` (SOT-89), `LM317LCPW` (TSSOP) and the `I` temperature
equivalents. `[test] python3 … collections.Counter(re.findall(r'LM317L[A-Z0-9]*'))`
→ **no `LM317LZ` anywhere in the document**. The row already says so
(*"The classic Z suffix is an ST/ON TO-92 marking rather than a TI orderable"*)
and goes further: *"**THE MANUFACTURER FIELD SAYS 'multiple' AND THAT IS
DANGEROUS HERE** … TI's SLCS144E gives minimum output current … 1.5 typ / 2.5
MAX mA … while ST's and ON's LM317L are different documents with different
minimum-load numbers, commonly 3.5 mA."*

TO-92 is the right package for an ST or ON `LM317LZ`, so this is orderable —
but the banked datasheet is for a part number nobody can buy, and the
`manufacturer` field is the thing the row itself flags as hazardous. It is the
one row where "which datasheet applies" is unanswerable from the BOM.

**G6-11. `U-OPA-PITCH`'s `part` field is not an order code, and it is the row
that two other rows cite as authoritative.**
`[repo] hardware/module/breath-receive-stage/bom.csv:2` — `part` = **`OPA2197`**
(no suffix), manufacturer TI, package SOIC-8. Its notes claim ownership: *"THIS
ROW IS WHERE THE OPA2197'S DEVICE FACTS LIVE — U-BUF and U-RESP cite it rather
than repeat it."* Both citing rows spell the orderable code:
`[repo] hardware/carrier/breath-excitation-reference/bom.csv:3` (`U-BUF`) and
`hardware/module/breath-response-shaper/bom.csv:5` (`U-RESP`) both say
`OPA2197IDR`. The manufacturer field differs too — "TI" on two rows, "Texas
Instruments" on the third. Same part, three spellings, and the canonical row
holds the one you cannot order. `[repo] datasheets/MANIFEST.csv` banks it as
`OPA2197IDR` → `analog/OPA2197.pdf`, so the order code is known.

**G6-12. Four rows carry a logic family where every other IC row carries an
order code.** `U-KEYS` = "74HC165", mfr "multiple"
(`[repo] hardware/cluster/key-register/bom.csv:2`); `U-LVLSHIFT` = "74AHCT125",
mfr "multiple" (`[repo] hardware/carrier/led-strip-drive/bom.csv:2`);
`U-LVL-MOD` = "74AHCT125", mfr **blank**
(`[repo] hardware/module/digital-and-supervision/bom.csv:2`). Against
`MCP3202-CI/SN`, `REF5050AIDR`, `OPA2197IDR`, `INA828IDR`, `DAC8568ICPW`,
`LT1641-1CS8` elsewhere, this is a real inconsistency — "74HC165" does not
distinguish `SN74HC165DR` from `CD74HC165M` from `74HC165D,653`, and the four
banked 74HC165 datasheets are from four different vendors (TI SCLS116E,
Nexperia, onsemi, Toshiba — `[repo] datasheets/MANIFEST.csv`). It is orderable
by picking one, so it is not a blocker; but `U-LVL-MOD`'s notes derive its
whole threshold analysis from **SCLS264O**, which is TI's `SN74AHCT125` — so
the part is effectively pinned in prose and left open in the field.

**G6-13. `C-BULK-DISP` has no value, two incompatible packages, and no decider.**
`[repo] hardware/carrier/power-entry-instrument/bom.csv:3` — `part` = **`TBD`**,
package "**1206 / electrolytic THT**", qty 1, status `open`, notes in full:
"Absorbs WiFi TX transients so they do not reach the rack rail". 1206 is an SMD
ceramic footprint; electrolytic THT is a radial can. They are not two options
for one land pattern the way `D-USBOR`'s are — and `D-USBOR` at least *says so*
(*"THE TWO PARTS ARE A CHOICE, NOT ALTERNATIVES: THEY ARE DIFFERENT FOOTPRINTS
… decide before layout"*). This row states no capacitance, no voltage, and
nothing that decides it, against the hardware convention *"Mark unresolved
things `TBD`/`open` **with what decides them**"*.

**G6-14. `L-BUCK-IN` is `candidate` with a 4.7× value range and an undecided
mounting style.** `[repo] hardware/carrier/power-entry-instrument/bom.csv:5` —
"10-47uH power inductor, >=1A", package "**SMD shielded or THT**", status
`candidate`. Notes: "A real inductor, not a bead. This is the part the bead was
wrongly credited for." Nothing decides the value or the footprint. Compare
`C-STRIP-BULK` ("470-1000uF electrolytic, 16V") where any value in the range
works electrically; a 10 µH and a 47 µH in an LC with `C-BUCK-IN` are different
corner frequencies, and SMD-vs-THT is a layout commitment. `candidate` reads
as decided here and is not.

**G6-15. Two `open` rows state no decider.** `C-BULK-DISP` (G6-13) and
`U-TVS-CHAIN` (G6-7). I checked all 36 `open` rows; the other 34 name one —
`Q-LOADSW` ("the single-pulse SOA curve decides it … must cover 12 V at both
10 ms and 100 ms"), `R-ILIM` (E6 with a current probe), `R-TRIM-RANGE` ("values
with the stages at E10"), `SW-THUMB` (M1), `CABLE-UMB` ("buy the lead, read the
jacket print, or measure end-to-end DC resistance at E6"), `F-CHAIN`,
`R-LED-PD` (E1), `MECH-PTFE` (E2), and so on. That is a good record and worth
saying: **the open rows in this BOM are, with two exceptions, correctly open.**

**G6-16. `FB-IN`'s package field admits a size the named part is not made in,
and the row's own requirement is left unresolved.**
`[repo] hardware/module/power-entry/bom.csv:8` — part "Laird MI1206K601R-10
(600R @ 100MHz, 1206, 1.5A)", package "**1206 or 1210**".
`[datasheet] datasheets/discrete-and-power/MI1206K601R-10-ferrite-bead.pdf` —
"1206" appears once, "1210" zero times; the row's own notes give the body as
3.20 × 1.60 × 1.10 mm, which is 1206. More important for an order: the notes
end *"**EITHER restate FB2's requirement at its real operating current OR make
FB2 a physically larger part**"* — an unresolved branch on a `candidate` row
with a single part number and `qty 4`. If FB2 becomes a larger part, this row
splits into two.

---

## QUANTITIES AND PAGE-vs-BOM CONFLICTS

**G6-17. `C-BULK-RAIL` says 100 µF on +12 V; the schematic draws 47 µF on all
four rails; and neither assigns a value to the fourth cap.**
`[repo] hardware/module/power-entry/bom.csv:9` — part "100uF (+12V) / 47uF
(−12V, +5V) 25V electrolytic", **qty 4**, with notes that make the split
load-bearing: *"NOT 47uF on every rail. The +12V branch carries the LM317's
divider, the DAC and the comparator, about 22 mA against −12 V's 10 mA — so at
47 µF each it collapses 2.2× faster and every rack power-down leaves the
op-amps with V+ near 0 and V− at −6 to −8 V for ~30 ms, pulling all six jacks
toward the surviving negative rail."*

The drawing disagrees. `[repo] hardware/module/power-entry/power-entry.md:42-77`:

```
  +12V ├───┬──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V
       │   └──[D2 1N5817]──[FB2]──[C2 47µF]──┬──────── PWR_GND (star)
  -12V ├───[D3 1N5817]──[FB3]──[C3 47µF]────────── MODULE ANALOG −12V
   +5V ├───[FB4]──[C4 47µF]──────────────────────── 74AHCT125 only
```

All four at 47 µF, including `C1` on the rail the row says must be 100 µF. A
builder transcribing the netlist from the drawing fits the part the row exists
to prevent. `[calc]` Separately, the row names **three** branches (+12 V, −12 V,
+5 V) for **four** capacitors: `C2` sits on the umbilical +12 V branch after
`D2`/`FB2` and no value in the row covers it. Neither value is in
`config/figures.yaml` (`[test] grep -n "47 µF\|100 µF\|47uF\|100uF" config/figures.yaml`
→ no match), so no check can reach this — `CLAUDE.md` §1's case for citing
rather than restating, on a value restated in two places and already divergent.

**G6-18. `C-REG-ADJ` buys two capacitors; the schematic draws one, and it is not
the one the argument depends on.** `[repo] hardware/module/power-entry/bom.csv:7`
— "10uF / 1uF ceramic or tantalum", qty 2, "LM317 ADJ bypass and output cap".
The drawing (`[repo] power-entry.md:45-47`) shows only:

```
       └──[LM317LZ]──┬── DAC AVDD 5.21V
        150R/475R    │
        0.1%      [C 1µF]
```

No ADJ bypass. `[test] grep -n "ADJ\|adj" hardware/module/power-entry/power-entry.md`
→ **no match at all**. And the missing part is the one that carries the claim:
`U-REG-DAC`'s notes say *"ripple rejection 65 dB typ, rising to 66 min / 80 typ
**WITH a 10 µF cap on ADJUSTMENT** — which C-REG-ADJ already fits"*, and
`C-REG-ADJ`'s own notes repeat it from the banked SLCS144E. A build from the
drawing gets 65 dB on the DAC's AVDD rail and the BOM will still say 80. The
`R-REG-SET` divider is drawn correctly (150R/475R 0.1% ✓).

**G6-19. `R-LED-SER`: the BOM says 330 Ω × 2; the schematic draws 220 Ω and its
parts table says "100–330 Ω, ×2–4".**
`[repo] hardware/carrier/led-strip-drive/bom.csv:4` — "330R 1%", **qty 2**,
notes *"TWO, NOT FOUR - reverted 2026-09-21"* with a good datasheet-backed
argument (the WS2815's own recommended circuit grounds `BI`). The page it is
derived from did not follow:

- `[repo] hardware/carrier/led-strip-drive/led-strip-drive.md:35` —
  `├──[R-LED-SER 220R]── J-LED-L DI`
- `[repo] …:41` — `├──[220R]── J-LED-R DI`
- `[repo] …:114` — "| **`R-LED-SER`** ×2–4 | **100–330 Ω** | Proposed |"

Both the **value** and the **count** are stale on the page, in the drawing a
netlist is transcribed from. Note `carrier.md:291` did follow the analogous
`R-SPI-SER` correction ("**Was drawn as three refdes that are not in the BOM,
at 220 Ω, derived from an RC model**"), so the same class of fix landed on one
page and not the other.

**G6-20. `R-BREATH-SUM`'s feedback resistor is drawn as 40 kΩ and specified as
40.2 kΩ on the same page.** `[repo] hardware/module/breath-output-stage/breath-output-stage.md:82`
draws `├──[R-FB 40k]── (to −)` and line 138 computes with `40k/95.3k`, while
line 149's parts table and `[repo] hardware/unplaced.csv:32` both say
**40.2 kΩ 1 %**. 40.2 k is E96; 40 k is not a 1 % standard value. One page,
two numbers, on a resistor that sets the fixed ×4.

**G6-21. `SW1-n` + `SW-THUMB` order 25 switches for 21 positions.**
`[repo] hardware/cluster/bom.csv:2` — `SW1-n`, KS-33 Red, **qty 21**, status
`purchased`. `[repo] hardware/cluster/key-switch-network/bom.csv:2` —
`SW-THUMB`, "KS-33 lighter variant — TBD at M1", **qty 4**, status `open`,
notes *"**If taken, SW1-n drops by 4.**"* The arithmetic is honest and stated,
and `SW-THUMB` is correctly `open` with M1 as the decider — but a reader adding
the `qty` column gets 25 for 18 keys + 3 spares. `[calc]` `PCB-CLUSTER`'s notes
give the layout: left hand 5, left thumb 4, right hand 6, right thumb 3 = 18,
plus 3 spares = 21 ✓, and `R-KEY-PU` at 24 = 21 + the 3 genuinely free bits ✓,
`R-KEY-SER` and `C-KEY` at 21 ✓, `CAP1-n` at 21 ✓. Everything else in the key
chain is internally consistent; this is the one line that needs a human at
order time.

**G6-22. `CAP1-n` is `purchased` and its notes say not to order it yet.**
`[repo] hardware/unplaced.csv:2` — status **`purchased`**, source Beekeeb, and
the notes: *"(c) PACK SIZE: this row says 5-packs while Tai-Hao's store lists
18 pcs/set, which would make it two — **CHECK THE PACK SIZE AGAINST THE ACTUAL
SUPPLIER BEFORE ORDERING**"*, plus *"SWITCH COMPATIBILITY IS DISPUTED BETWEEN
VENDORS AND THE TWO ARE NOT RECONCILABLE FROM DOCUMENTS"*. A row cannot be both
already purchased and carry a pre-order check. One of the two is wrong and it
matters, because the compatibility dispute (Tai-Hao says Choc V1; Beekeeb says
Choc v2 / Gateron LP 2.0–3.0 / MX and explicitly not v1) decides whether the
keycaps fit `SW1-n` at all.

---

## CROSS-ROW CLAIMS (brief item 7)

**G6-23. FALSE: `R-BREATH-SUM` claims to share a reel with `R-MODGAIN`, and the
value it names is the one `R-MODGAIN` retired.**
`[repo] hardware/unplaced.csv:32` — *"R-IN 10k, R-FB 40.2k. **Same E96 feedback
part as R-MODGAIN, bought on the same reel**"*. `R-MODGAIN`'s feedback is
**30 kΩ**, not 40.2 kΩ: `[repo] hardware/module/mod-channels/bom.csv:3` —
*"R1=10k, **R2=30k** per channel, k=3"*, corroborated on the page
(`[repo] mod-channels.md:56` draws `└──[R2 30k 1%]`, and line 113's table reads
"**R2** | **30 kΩ 1 %** | Feedback"). Worse, the very row cited names 40.2 k as
the **superseded** value: *"Lands on EXACTLY ±10.000 V, where the old
four-resistor difference amp needed a 40.2 k fudge to reach ±10.05"*, repeated
at `[repo] mod-channels.md:89` and `:100`. The 10 k input resistor *is* shared;
the feedback part is not. The same false claim is restated on the page:
`[repo] hardware/module/breath-output-stage/breath-output-stage.md:149` —
"**R-FB** | 40.2 kΩ 1 % | Fixed ×4. **Same E96 part as `R-MODGAIN`**".

This is `CLAUDE.md`'s named failure in its fourth recorded shape — *a
conclusion that its own corrected number refutes* — and it is an ordering
consequence, not just prose: buy one reel and you are 6 resistors short of one
value and 2 short of another.

**G6-24. FALSE: `R-ILIM` points at a row that is not where it says.**
`[repo] hardware/module/umbilical-load-switch/bom.csv:6` — *"the same mistake
already found and fixed on the LM317 divider, **one row down**"*. The LM317
divider is `R-REG-SET`, in a **different fragment**
(`hardware/module/power-entry/bom.csv:6`) and eight rows earlier in the master
(`hardware/bom.csv:59` vs `R-ILIM` at `:67`). One row down from `R-ILIM` in
both the master and its own fragment is `R-FB-HI`. A positional pointer in a
generated file was never going to survive; the fix is to name the refdes.

**G6-25. TRUE, and worth recording as verified.** I checked every cross-row
claim I found; these all hold.

- `D-USBOR` → *"the evidence is **three rows down**: D-REVSHUNT on this same
  board is DO-214AB"*. ✓ `[repo] hardware/carrier/power-entry-instrument/bom.csv:7`
  → `:10`, three rows, and the same three-row offset survives in the master
  (`hardware/bom.csv:7` → `:10`). The only positional pointer in the BOM that
  is currently right — and it is right by luck, since the fragment and the
  master happen to agree.
- `D-JACK-CLAMP` → *"The two BREATH INPUT clamps are a separate row,
  D-CLAMP-BREATH, so **the module carries eight BAV99 in total**"*. ✓
  `[calc]` 6 + 2 = 8, and `D-CLAMP-BREATH` reciprocates: *"Distinct from
  D-TVS-BREATH, which is the ESD part at the connector."* Mutual.
- `U-OPA-PITCH` → the ten-halves enumeration. ✓ Re-derived from the pages
  independently, see G6-5.
- `U-BUF` and `U-RESP` → *"DEVICE FACTS ARE ON U-OPA-PITCH"*. ✓ Mutual —
  `U-OPA-PITCH` says *"U-BUF and U-RESP cite it rather than repeat it"*. (The
  part number itself is the exception: G6-11.)
- `R-ISO-REF` → *"37.4R is Zo/10 against the specified 375 ohm (**see
  U-OPA-PITCH**)"*. ✓ `U-OPA-PITCH` carries the 375 Ω with its citation.
- `U-TVS-SPI` → *"**ALL FOUR CHANNELS SHARE ONE COMMON PIN (pin 2)**, so a
  single array cannot straddle PWR_GND and DIG_GND — which is why U-TVS-SPI and
  U-TVS-CHAIN stay two packages."* ✓ Consistent with two separate qty-1 rows.
- `POT-OFFSET` ↔ `U-RESP`: *"its true zero sits ~20 degrees past centre at
  +0.605 V while the wiper is unbuffered — **see U-RESP, which buffers it**"*,
  and `U-RESP` says *"POT-OFFSET's wiper needs the other [half]"*. ✓ Mutual,
  same voltage on both sides.
- `POT-OFFSET` and `POT-RESP` → *"RV09 order-code traps are on POT-GAIN and are
  not repeated here"*, and `POT-GAIN` claims *"THIS ROW OWNS THE RV09
  ORDER-CODE TRAPS for all three pots"*. ✓ Mutual three ways. (But see G6-26.)
- `C-FILT-MOD` → *"FOUR not five: breath does not pass through the DAC and has
  its own 330 nF (C-OUT-BREATH, ~480 Hz)"*. ✓ `C-OUT-BREATH` is 330 nF,
  ~480 Hz. `[calc]` 6 output jacks = 4 mod (`C-FILT-MOD`) + 1 breath
  (`C-OUT-BREATH`) + 1 pitch (`C-FILT-PITCH`) ✓.
- `U-TVS-MODULE` → *"Same three groups, module end of the etherCON"*. ✓ Three
  groups cross the umbilical and each has an instrument-end row: power
  (`D-TVS-PWR`), breath pair (`D-TVS-BREATH`), SPI (`U-TVS-SPI`). The key chain
  does not cross it, so it is correctly excluded.
- `C-DECOUPLE`'s 19-cap enumeration ✓ and `C-DECOUPLE-CARRIER`'s 8-cap
  enumeration ✓ (`[calc]` MCP3202 1 + REF5050 IN and OUT 2 + OPA2197 1 +
  74AHCT125 1 + MPXV4006DP 1 + both R-78E5 inputs 2 = 8).
- `J-CHAIN` → *"They sit carrier 1, right_thumb 2, right_hand 2, left_thumb 2,
  left_hand 1"*. `[calc]` = 8 ✓ = `qty`, and the row correctly cites the
  `chain-connectors` figure instead of restating it.
- `R-LDAC`, `R-CLR-PU`, `U-LVL-MOD` all correctly narrate the deleted watchdog
  and comparator, and `C-DECOUPLE`'s count was reduced for both. ✓

**G6-26. No pot order code exists anywhere, on three rows that agree they are
the same part.** `POT-GAIN` (`[repo] hardware/module/breath-output-stage/bom.csv:3`)
lists *"FOUR THINGS THE ORDER CODE HAS TO CARRY"* — bushing suffix (none / E1 /
E1N), centre detent (0C, and it halves the life), the A/B **angle** letter
(*"THE A/B LETTER IN RV09A / RV09B IS THE ROTATIONAL ANGLE … NOT THE TAPER"*),
and the separate taper code — then says *"taper TBD at E10"* and *"THE PART MAY
NOT BE ALPHA: Thonk ships the Song Huei R0904N"*. None of the four is chosen on
any of the three rows. The three also disagree on fields that should match if
they are the same part:

| row | manufacturer | package |
|---|---|---|
| `POT-GAIN` | Alpha | `THROUGH-HOLE 9mm vertical` |
| `POT-OFFSET` | Alpha | `THROUGH-HOLE 9mm vertical` |
| `POT-RESP` | *(blank)* | `PCB mount` |

`POT-RESP` (`[repo] hardware/module/breath-response-shaper/bom.csv:2`) says
"Same part as POT-GAIN" in its notes while leaving the manufacturer blank and
spelling the package differently. Both RV09 and R0904N datasheets are banked
(`[repo] datasheets/connectors/RV09AF-40.pdf`, `R0904N.pdf`), so this is
decidable now. Not a blocker — the panel cannot be drilled without it either
way, and E10 is a legitimate decider for taper — but three rows for one part
with three different field values is how the next divergence starts.

---

## `hardware/unplaced.csv` (brief item 6)

**G6-27. `R-BREATH-SUM` and `R-BREATH-OFF` are derived by a schematic page and
should not be in `unplaced.csv`.** `hardware/README.md` defines the file as
*"the BOM rows **no schematic page derives**"*. Both rows are derived, with
values, by `hardware/module/breath-output-stage/breath-output-stage.md`:

- `[repo] …:67,82,149` — `[R-IN 10k]`, `[R-FB 40k]`, and the table "**R-IN** |
  10 kΩ 1 % | Summer input", "**R-FB** | 40.2 kΩ 1 %" → `R-BREATH-SUM`
  (`[repo] hardware/unplaced.csv:32`, "R-IN 10k, R-FB 40.2k").
- `[repo] …:72,74,151,152` — `[R-OFF 21.0k]`, `[R-OFFNEG 95.3k]` and both table
  rows → `R-BREATH-OFF` (`[repo] hardware/unplaced.csv:33`, "R-OFF 21.0k …
  R-OFFNEG 95.3k").

This is precisely the pattern `hardware/README.md:112-120` records as already
fixed for sixteen rows — *"they were sitting in the undrawn pile because
assignment matched on **reference designator** while those parts are drawn under
a local label (`R1`, `C_cm`, `FB2`, `R_G`)"*. Two more were missed, under the
local labels `R-IN`/`R-FB`/`R-OFF`/`R-OFFNEG`. They belong in
`hardware/module/breath-output-stage/bom.csv`.

**G6-28. `hardware/README.md:112` states a count that has moved under it.**
"It was 50 rows and is now **34**." `[test] python3 -c "import csv; print(len(list(csv.reader(open('hardware/unplaced.csv',newline='',encoding='utf-8'))))-1)"`
→ **32**. (33 physical lines, 1 header.) `[calc]` 50 − 16 = 34 is arithmetically
consistent with the sentence's own story, so the sentence was true when written
and two further rows left afterwards — `D-CLAMP-BREATH`'s notes record one of
them (*"2026-09-21: moved out of unplaced.csv"*). A restated count that no check
can reach, in the paragraph that describes the fix. `CLAUDE.md` names this shape
exactly: *"a stated count that has moved under the sentence stating it"*.

**G6-29. The rest of `unplaced.csv` is honest.** I checked all 32. The
mechanical rows (`BODY-OAK`, `SIDE-ACRYLIC`, `ADH-WOOD`, `ADH-RTV`, the four
`MECH-*` and two `ENDCAP-*`), the consumables (`CABLE-UMB`, `TUBE`,
`MECH-PTFE`, `MECH-MOUTH`), the dev boards and their spare (`U-MCU-RT`'s IMU,
`U-DISP`, `U-MCU-SPARE`), the not-needed trio (`J-USB`, `U-ESD-USB`,
`SW-BOOT`), `BENCH`, `PCB-MODULE`, `PANEL`-adjacent `KNOB-BREATH`,
`U-TVS-MODULE`, `J-UMBILICAL-CABLE` and the `U-OPA-GEN` tombstone are all
genuinely underived by any page. `LED-SIDE` is named only as "the WS2815
strips" on `led-strip-drive.md`, which describes the driver, not the strip —
correctly unplaced.

**G6-30. Nothing in the placed fragments belongs in `unplaced.csv`.** The six
rows whose refdes appears on no `hardware/**.md` page — `J-UMBILICAL` (drawn as
`J-UMB`), `C-REG-ADJ`, `R-GAIN-INAMP` (drawn `R_G 42.2k`), `C-FILT-BREATH`
(drawn `C_diff 15nF` + two `C_cm 1.5nF`), `PANEL`, `J-CV` — are all either
local-label cases or deliberate board-level filings. `J-CV`'s row states the
reason explicitly (*"FILED AT BOARD LEVEL … three circuits drive these six jacks
and panel.md owns only the cutouts: no single circuit page derives the
connector"*), which is consistent with `hardware/module/bom.csv` existing as a
board tier in `tools/merge-bom.py`'s `ORDER`. `C-REG-ADJ` is the one where the
page genuinely omits the part (G6-18) — that is a missing drawing, not a
misfiled row.

---

## Packages verified CORRECT against banked documents

Given this repository's history of shipping through-hole parts in SMD packages,
the clean results are as load-bearing as the defects. All from
`[datasheet]` reads of the banked PDFs via `pymupdf`:

| row | part | BOM package | document |
|---|---|---|---|
| `D-REVSHUNT` | SS34 | DO-214AB (SMC) | `SS34.pdf` — "SMC" 4×, "SMA" **0×** ✓ |
| `D-USBOR` (SMD option) | SS14 | DO-214AC (SMA) | `SS14.pdf` — "SMA" 4×, "SMC" **0×** ✓ |
| `D-TVS-PWR` | SMAJ15A | DO-214AC | `SMAJ15A.pdf` — "SMA" 129×, "SMB"/"SMC" 0× ✓ |
| `D-REVPOL`, `D-USBOR` (THT) | 1N5817 | DO-41 | `1N5817.pdf` — "DO-41" 8×, no SMD case ✓ |
| `U-LOADSW` | LT1641-1CS8 | SO-8 | `LT1641.pdf` — "S8" 7×, "SO-8" 1× ✓ |
| `D-CLAMP-BREATH`, `D-JACK-CLAMP` | BAV99 | SOT-23 | `BAV99.pdf` ✓ |
| `U-TVS-SPI` | SP0504BAHTG | SOT-23-5 | `SP0504BAHT.pdf` p.1 ordering table: `SP0504BAHTG` → SOT23-5, 4 ch ✓ |
| `U-DAC` | DAC8568**I**CPW | TSSOP-16 | `DAC8568CIPW.pdf` — `DAC8568ICPW` 4×, `DAC8568CIPW` **0×**. The row's transposition warning is correct ✓ |
| `R-PRECISION` | LT5400 MS8E, EP 1.88 × 1.68 | MSOP-8 MS8E | `LT5400.pdf` — `1.68 ± 0.102` × `1.88 ± 0.102` exposed pad, "DFN" 0× ✓ |
| `U-BREATH` | MPXV4006**DP** | case 1351-01 | `MPXV4006DP.pdf` ordering table: `MPXV4006DP` → 1351, `MPXV4006GP` → 1369. The row's GP/DP port-convention warning is correct ✓ |
| `FB-IN` | MI1206K601R-10 | 1206 | `MI1206K601R-10-ferrite-bead.pdf` ✓ (but see G6-16 on "or 1210") |

`SW-POWER` deserves its own line: **`NKK M2011SD4G01` decomposes correctly,
field by field**, against `[datasheet] datasheets/connectors/NKK-SERIES-M-TOGGLE.pdf`.
The ordering example on p.7 is `M2013SS1W01` = model + toggle + bushing +
contact + terminals, so `M2011` + `S` + `D4` + `G` + `01`. p.3 "POLES &
CIRCUITS": `M2011` is the only SP row with `ON / NONE / OFF`, i.e. a true SPST,
matching the row's *"M2011 is a true SPST"*. p.3 bushing table: `D4` = "6mm
.350" (8.9mm) Threaded with **D Flat**" — the row's "D4 (D-FLAT) OVER S4
(KEYWAY)" is right, `S4` being the keyed 6 mm. p.7 gives the D-flat cutout as
`(6.5) Dia .256` with `(5.8) .228` across the flat, exactly the row's "6.5mm
panel hole with a 5.8mm D-flat", `M6 P0.75` thread, and "Maximum Panel Thickness
with Standard Hardware: .102" (**2.6mm**)" — the row's "max panel thickness with
the standard hardware is 2.6mm". p.7 contacts: `G` = "Gold; Rated 0.4VA max @
28V AC/DC max", which is the row's gold-not-silver argument. p.13/15: toggle `S`
= .413" (10.5 mm) bat, 2.8 mm dia, 25° throw = the row's "toggle 10.5 x 2.8mm
dia, 25 deg throw". `01` = solder lug. **Every field checks out.** This is the
best-specified row in the BOM and is worth using as the template for the others.

---

## What I could NOT check

- **Stock and price at any distributor.** I made no distributor requests. Every
  "orderable" judgement above is "a complete, unambiguous part number exists",
  not "it is in stock". `C-FILT-MOD`'s note records that distributor sites were
  proxy-blocked for an earlier attempt.
- **82 nF C0G availability in 0805 / 1206 / 1210** (G6-4). There is no
  capacitor datasheet of any kind in `datasheets/` — 101 MANIFEST rows, none a
  passive capacitor — so nothing in the bank can settle it.
- **`D-TVS-BREATH` from a banked document** (G6-6). `PESD12VS1UB` is
  `status=BLOCKED` with no file. I resolved it `[web]` only, from Nexperia's
  own product page and datasheet title plus a Farnell listing. If web evidence
  is not acceptable as provenance for a package change, this reverts to
  "unverified, and the package is unverifiable from the repository".
- **`CAP1-n` fit** (G6-22). Height, stem depth and profile are unpublished;
  both MANIFEST rows for the keycap are `BLOCKED`. Nothing bounds the Z stack
  above `PLATE-TOP`, exactly as the row says.
- **Whether 21 switch positions is the right number.** `config/key-layout.yaml`
  owns `marker-bits`, `free-bits` and the layout; checking the BOM against it is
  another slice's. I verified only that the BOM rows are self-consistent at 21.
- **`Q-LOADSW`'s SOA screening.** There is no candidate part to check a curve
  against.
- **Anything under `docs/review/`, `docs/log/` or `docs/research/`** — cold, by
  the brief.

## One observation outside my slice

`tools/check-staleness.py` returned `PASS` on my first Bash call of the session
and `FAIL … 1 links` on the second, with no intervening write from me. The
failure is `[repo] .staleness/report.txt:14` — "README.md:148 links to
'g10-does-not-exist.md', which does not resolve", and `[repo] README.md:148`
does read `See [the missing page](g10-does-not-exist.md).` I did not
investigate further; it is not a BOM matter and the slice name in the filename
suggests it belongs to someone else. I note only the **non-determinism**, since
`CLAUDE.md` records a previous wave where two slices running one command twenty
minutes apart got opposite verdicts.
