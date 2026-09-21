# B2 — BOM integrity: can this bill of materials be ordered and built?

**Agent:** B2, cold pre-merge review, 2026-09-21.
**Slice:** `hardware/bom.csv` (138 rows, generated from 24 fragments) against the
pages that draw the parts.
**Cold rule observed:** nothing under `docs/review/**` was read. Where a grep
returned a hit count in a review directory it is reported as a count only, and
no content from those files informs any finding below.
**Provenance:** every claim is marked `[repo] path:line`, `[calc]`,
`[datasheet]` (document + page/field, read off a banked PDF in this session),
or `[from memory]`. Unmarked claims would be defects; there are none.

**REPORT ONLY — nothing was changed.** `merge-bom.py --check` and
`check-staleness.py` were run read-only and both pass.

---

## Verdict

**No.** Three classes of defect block ordering, and one blocks netlisting.

1. **One principal IC cannot be ordered by the part number given.**
   `U-DAC` is `DAC8568CIPW`, which is not a TI order code.
2. **Two rows carry a footprint that does not match the part.** `D-USBOR` and
   `C-FILT-MOD`; a third (`U-TVS-CHAIN`) carries a pin count that a banked
   datasheet refutes for the only part the corpus proposes for it.
3. **Six quantities contradict the drawing that owns them**, and two BOM rows
   contradict each other on the same count.
4. **~22 of the 50 `unplaced.csv` rows are drawn**, not undrawn — including
   every principal active device on the module board. `module.md` admits three
   of them; the real count is seven times that.

Separately, the BOM carries **no sourcing information at all**: the `source`
column is populated on **2 of 138 rows** and `manufacturer` on **34 of 138**
`[calc, csv column census of hardware/bom.csv]`. There is no distributor part
number, no MOQ and no price anywhere. As an ordering document this is a parts
list, not a BOM.

Verified sound and worth recording: `merge-bom.py --check` reports *"138 rows
from 24 fragments | 0 problems"*; the file is 11 columns and **pure CRLF** —
139 CRLF terminators, **0 bare LF** `[calc, byte census]`; no duplicate `ref`;
the `adr` column is populated on all 138 rows and every ADR named (0001–0009,
0013, 0014) exists in `docs/decisions/` `[repo]`.

---

# A. Findings, indexed by refdes

Severity: **P1** blocks an order or a netlist · **P2** wrong value or quantity
that will be built wrong · **P3** hygiene, ownership, provenance.

---

## A1 · `U-DAC` — **P1** — the order code does not exist

`bom.csv` row `U-DAC` names **`DAC8568CIPW`**
`[repo] hardware/unplaced.csv:6, hardware/bom.csv:94`.

The banked datasheet's Package Option Addendum enumerates the whole orderable
range and it contains **no such code**
`[datasheet datasheets/analog/DAC8568CIPW.pdf, Package Option Addendum]`:

```
DAC8568IAPW  DAC8568IAPWR
DAC8568IBPW  DAC8568IBPWR
DAC8568ICPW  DAC8568ICPWR      ← the C grade, tube / tape-and-reel
DAC8568IDPW  DAC8568IDPWR
```

The form is `DAC8568I<grade>PW`. The row transposes the `I` and the grade
letter. `DAC8568CIPW` returns **zero matches** in the document text
`[calc, string search over the extracted PDF text: index −1]`;
`DAC8568ICPW` is present with `ACTIVE TSSOP PW 16 90 … DA8568C`.

**Why this one matters more than a typo.** The row's own note says
*"GRADE LOCKED TO C. The grade letter selects REFERENCE GAIN as well as reset
state — A/B are gain 1 (2.500V full scale), C/D are gain 2 (5.000V). An
A-grade part would halve everything"* `[repo] hardware/bom.csv:94`. And
ADR 0006 says *"**Specify the full orderable part number in the BOM**, not
'DAC8568'. The grade …"* `[repo] docs/decisions/0006-cv-channel-allocation.md:222`.
The instruction landed everywhere; the string is wrong everywhere.

**It has propagated to four places in the design corpus** and one generated
file `[repo, grep]`:

| Where | Line |
|---|---|
| `hardware/unplaced.csv` (the row itself) | `:6` |
| `hardware/bom.csv` (generated) | `:94` |
| `docs/decisions/0006-cv-channel-allocation.md` *"locked to `DAC8568CIPW`"* | `:176` |
| `docs/decisions/0006-…` *"`datasheets/analog/DAC8568CIPW.pdf`"* | `:179` |
| `datasheets/MANIFEST.csv` `part` column, and the banked file's own name | `:2` |

**The correct string `DAC8568ICPW` appears nowhere in the design corpus**
`[calc, grep over hardware/**, docs/decisions/**, docs/reference/**, config/**,
firmware/**, README.md, ROADMAP.md: zero hits]`. It does occur in
`docs/research/` and in three prior review directories — counts only; those
files were not opened, per the cold rule.

**Note for whoever fixes it:** `MANIFEST.csv` is generated (CLAUDE.md §4) and
the banked PDF's *filename* carries the bad string too, so the fix is not a
one-line edit. Route it through `docs/reference/repo-maintenance.md` §3.

---

## A2 · `D-USBOR` — **P1** — one row, two parts, one footprint that fits one of them

```
D-USBOR | part: "1N5817 or SS14" | package: "DO-41 THROUGH-HOLE" | qty 2
```
`[repo] hardware/carrier/power-entry-instrument/bom.csv, hardware/bom.csv:7`

`SS14` is **SMA (DO-214AC)** — read off the banked part:
*"MECHANICAL DATA Case: SMA (DO-214AC)"*
`[datasheet datasheets/discrete-and-power/SS14.pdf p.1, Vishay doc 88746]`.
`1N5817` is DO-41 axial. The two alternatives share no land pattern. The row
as written cannot be turned into a footprint without choosing first, and
nothing in the row says what decides it.

---

## A3 · `D-REVSHUNT` — **P2** — the BOM is right and `MANIFEST.csv` is wrong

This is the reverse of the usual direction, so it is worth stating precisely.

- `bom.csv` says `SS34`, package **`DO-214AB (SMC)`**, and its note records the
  correction: *"This row said DO-214AC, which is the SS14's package.
  [datasheet SS34.pdf p.1] states 'MECHANICAL DATA / Case: SMC (DO-214AB)'"*
  `[repo] hardware/bom.csv:10`.
- **The BOM row is correct.** Verified directly against the banked PDF:
  *"MECHANICAL DATA Case: SMC (DO-214AB)"*, and again in the summary block
  *"Package SMC (DO-214AB) Circuit configuration Single SMC (DO-214AB)"*
  `[datasheet datasheets/discrete-and-power/SS34.pdf p.1, Vishay doc 88751 rev 23-Apr-2020]`.
- **`datasheets/MANIFEST.csv`'s own row for that same file says
  `"SMA (DO-214AC), 3.0A"`** `[repo] datasheets/MANIFEST.csv, row SS34`.

So the package fix landed in `bom.csv` and **not** in the manifest row a
reader would use to check it — and the manifest now asserts the exact wrong
package the BOM was corrected away from. Anyone verifying `D-REVSHUNT` against
the manifest will "confirm" the old error.

`D-TVS-PWR` `SMAJ15A` at `DO-214AC` is **correct** — *"compact chip package
DO-214AC (SMA)"* `[datasheet datasheets/discrete-and-power/SMAJ15A.pdf p.1]`.

---

## A4 · `U-TVS-CHAIN` — **P1/P2** — the pin-count correction landed on one row of two

`datasheets/MANIFEST.csv`'s `SP0504BAHT` row records the finding in full:
*"Ordering Information p.1 states SP0504BAHTG is 4 channels in SOT23-5, and
SP0505BAHTG is 5 channels in SOT23-6 … So bom.csv U-TVS-SPI 'SOT-23-6', **carrier.md:825**,
**carrier.md:812 and bom.csv U-TVS-CHAIN '4-ch array, SOT-23-6' are ALL WRONG on
pin count**"* `[repo] datasheets/MANIFEST.csv, row SP0504BAHT`.

Four locations were named. **Two were fixed and two were not**
`[repo, grep for SOT-23-5|SOT-23-6 over hardware/**, config/**, docs/decisions/**]`:

| Location | Now | Status |
|---|---|---|
| `hardware/interfaces/spi-link/bom.csv` `U-TVS-SPI` | `SOT-23-5 (0.95mm pitch)` | **fixed** |
| `hardware/carrier/carrier.md:292` `U-TVS-SPI` | `SP0504BAHT, **SOT-23-5**` | **fixed** |
| `hardware/interfaces/key-chain-loom/bom.csv:4` `U-TVS-CHAIN` | `SOT-23-6` | **not fixed** |
| `hardware/carrier/carrier.md:285` `U-TVS-CHAIN` | `4-ch array, SOT-23-6` | **not fixed** |

The fix landed on the row being edited and not on the row that copies it — the
project's named failure mode, in the commit that was about it.

**One caveat, stated so this is not over-claimed.** `U-TVS-CHAIN`'s `part`
field is the generic *"4-channel TVS array"*, not `SP0504BAHT`. Four-channel
arrays do exist in SOT-23-6 `[from memory]`, so `SOT-23-6` is not wrong *in the
abstract*. But the row's own justification is *"`U-TVS-SPI` does exactly this
job for the umbilical's three"* `[repo] hardware/interfaces/key-chain-loom/bom.csv:4`,
and `carrier.md:285` says the same — so the part the corpus has in mind is the
SOT-23-5 one. Either name a different part or take the correction. A row that
pins a **package** while leaving the **part** open is backwards regardless.

---

## A5 · `WIRE-LOOM` vs `J-CHAIN` — **P2** — bom.csv contradicts itself on a connector count

Two rows of the same file give two different answers to one question.

- `J-CHAIN`, qty **8**: *"EIGHT of them, not five: the chain is four hops and
  SER/QH are point-to-point … Carrier 1, right_thumb 2, right_hand 2,
  left_thumb 2, left_hand 1"* `[repo] hardware/bom.csv:47`.
- `WIRE-LOOM`: *"chained through each cluster board in turn rather than
  starred, so **five connectors must match**: one on the carrier and one per
  cluster board"* `[repo] hardware/bom.csv:29,
  hardware/carrier/bom.csv:6`.

`config/figures.yaml` tracks this as `chain-connectors`, value **`"8"`**, owner
`hardware/interfaces/key-chain-loom/key-chain-loom.md`, and lists
**`"five connectors must match"` as a forbidden pattern**
`[repo] config/figures.yaml, figure chain-connectors`.
`carrier.md` states it plainly: *"EIGHT connectors, not five"*
`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:85` (moved from
`carrier.md` §3).

**The forbidden pattern is present, live and unrefuted, and the checker passes.**
See §C for the mechanism — the `WIRE-LOOM` cell contains the words *"rather than
starred"*, and `rather than` is in the checker's refutation regex
`[repo] tools/check-staleness.py:63-67`, so the whole row is excused by a clause
that has nothing to do with the connector count.

`PCB-CLUSTER`'s note gets it right — *"~8 connectors across 4 ribbon
assemblies"* `[repo] hardware/bom.csv:40` — so the corpus holds 5 and 8 for one
quantity, in one generated file, three rows apart.

---

## A6 · `HDR-DEV` — **P2** — qty describes the superseded two-socket topology

```
HDR-DEV | qty 6 | open | "Cut to length: 2 strips for the ESP32-S3-Matrix,
                          2 for the T-Display-S3 AMOLED, 2 spare"
```
`[repo] hardware/carrier/bom.csv, hardware/bom.csv:28`

`carrier.md` deletes the display board's sockets explicitly, twice:

> *"**The display board is 360 mm away at the top of the instrument** … It
> reaches this board through a loom, not a socket. This page therefore draws
> **one** dev-board socket pair"* `[repo] hardware/carrier/carrier.md:29-38`

> `| HDR-DEV | 2 × 10-way machined socket | **Qty is one board's worth, not
> two** — the display board is 360 mm away |`
> `[repo] hardware/carrier/carrier.md:282`

`[calc]` 6 = 2 (matrix) + 2 (display) + 2 (spare). With the display board's
pair deleted the row should be 2 + spares, i.e. 4 at the same spare policy.
The row still budgets sockets for a board that plugs into `J-DISP`.

---

## A7 · `C-BULK-RAIL` — **P2** — the value the row argues for is not the value drawn, and its argument rests on a deleted part

```
C-BULK-RAIL | qty 4 | "100uF (+12V) / 47uF (-12V, +5V) 25V electrolytic"
```
`[repo] hardware/unplaced.csv:33, hardware/bom.csv:122`

The row's whole case: *"**NOT 47uF on every rail.** The +12V branch carries the
LM317's divider, the DAC and **the comparator**, about 22mA against −12V's 10mA
— so at 47uF each it collapses 2.2x faster … **100uF on +12V balances the
decay**"* `[repo] hardware/bom.csv:122`.

The page that owns the circuit draws **47 µF on all four rails**:

```
+12V ├──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V
     └──[D2 1N5817]──[FB2]──[C2 47µF]──┬── PWR_GND (star)
-12V ├───[D3 1N5817]──[FB3]──[C3 47µF]──── MODULE ANALOG −12V
 +5V ├───[FB4]──[C4 47µF]──────────────── 74AHCT125 only
```
`[repo] hardware/module/power-entry/power-entry.md, "The circuit"`

and states it again in prose: *"**Entry bulk is 4 × 47 µF**, which is 2–5× the
surveyed norm of 10–22 µF"* `[repo] hardware/module/power-entry/power-entry.md,
"Still open"`.

**And the load the row sizes against no longer exists.** *"the comparator"* is
the LM311 presence comparator, which `link-supervision.md` records as deleted:
*"A 74HC123 monostable … **Deleted.** … the LM311 presence comparator … Both
deleted"* `[repo] hardware/module/link-supervision/link-supervision.md:1-6, and
"There is no presence detect either"`. `C-DECOUPLE`'s own note already followed
that deletion through — *"was 21. The two caps counted for the LM311 are
removed - that part was DELETED"* `[repo] hardware/bom.csv:56` — and
`C-BULK-RAIL` did not. This is CLAUDE.md §5's class exactly: an argument
surviving its own refutation, invisible to a grep.

Either the drawing is one capacitor value short or the row's differential
sizing is stale. Both cannot be built.

---

## A8 · `C-BUCK-IN` — **P2** — qty 2 against one capacitor drawn, and the stability derivation uses one

```
C-BUCK-IN | qty 2 | "100uF 25V electrolytic" | note: "One per buck"
```
`[repo] hardware/carrier/power-entry-instrument/bom.csv, hardware/bom.csv:8`

The drawing shows **one** `L-BUCK-IN` and **one** `C-BUCK-IN` on a shared node
that both regulators hang off:

```
├──[L-BUCK-IN]──┬──────┼──[R-78E5.0 A]──▷|── dev board 5V
│   10–47 µH    │      │
│        [C-BUCK-IN    │
│         100 µF 25V]  │
│               └──────┼──[R-78E5.0 B]──▷|── J-DISP 5V
```
`[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md, "The circuit"`

`L-BUCK-IN` is correctly qty 1. The input-LC derivation on the same page uses
**one** capacitor: *"L = 22 µH (mid range), **C = 100 µF** … f0 = 3.39 kHz,
Z0 = 0.469 Ω"* `[repo] same file, "Derivations"`.

`[calc]` If the row's "one per buck" is built, C = 200 µF and the derived
numbers move: f0 = 1/(2π√(22 µH × 200 µF)) = **2.40 kHz** (not 3.39) and
Z0 = √(22 µH/200 µF) = **0.332 Ω** (not 0.469). The 220× damping margin
survives, so nothing breaks — but the page's stated figures are wrong for the
BOM's quantity, and the row and the drawing cannot both be right.

---

## A9 · `C-REG-ADJ` — **P2** — qty 2, one drawn

```
C-REG-ADJ | qty 2 | "10uF / 1uF ceramic or tantalum"
          | desc: "LM317 ADJ bypass and output cap"
```
`[repo] hardware/unplaced.csv:23, hardware/bom.csv:112`

The LM317 as drawn has **only the output capacitor**:

```
└──[LM317LZ]──┬── DAC AVDD 5.21V
   150R/475R   │
   0.1%     [C 1µF]
```
`[repo] hardware/module/power-entry/power-entry.md, "The circuit"`

The 10 µF ADJ bypass — the one the row justifies (*"ADJ bypass drops output
noise to ~50uV RMS … TI SLCS144E confirms … ripple rejection goes from 65dB typ
to 66 min / 80 typ WITH a 10uF capacitor from ADJUSTMENT to ground"*
`[repo] hardware/bom.csv:112`) — is in the BOM and **not in the drawing**. The
BOM is right here and the schematic is one part short.

---

## A10 · `U-BREATH` — **P2** — qty 2, one sensor drawn, no spare declared

```
U-BREATH | MPXV4006DP | qty 2 | status: selected
```
`[repo] hardware/interfaces/breath-sense-link/bom.csv, hardware/bom.csv:41`

Exactly one sensor exists anywhere in the corpus:

- one in the carrier drawing `[repo] hardware/carrier/carrier.md:105`
- one socket: `SKT-BREATH` qty **1** `[repo] hardware/bom.csv:29`
- one decoupler: `C-DECOUPLE-CARRIER`'s enumeration allocates *"MPXV4006DP"*
  **once** out of its 8 `[repo] hardware/bom.csv:22`
- `carrier.md`'s component table lists *"`U-BREATH` + `SKT-BREATH` |
  MPXV4006DP"* as one line `[repo] hardware/carrier/carrier.md:288`

The row's note is long and detailed and never mentions a spare
`[repo] hardware/bom.csv:41`. Compare `U-MCU-SPARE`, which is a *separate row*
for spares and says so. Either qty 2 is a spare that should be declared (the
project's own convention) or it is wrong.

Related, lower confidence: **`MECH-PTFE` qty 2** with a note that says
*"Pressure port only - the DP's reference port is unplumbed"* and
*"One part, two jobs"* `[repo] hardware/bom.csv:114` — one port, one plug
drawn (*"P1 ◄── 400 mm tube + PTFE plug + ≤1 mL trap"*
`[repo] hardware/carrier/carrier.md:107-110`), qty 2 unexplained.

---

## A11 · `R-LED-SER` — **P2** — BOM 330 R, drawing 220 R

```
R-LED-SER | "330R 1%" | qty 2
```
`[repo] hardware/carrier/led-strip-drive/bom.csv, hardware/bom.csv:23`

The page that owns it draws **220 R**, twice:

```
└──►│ 74AHCT125 gate A ├──[R-LED-SER 220R]── J-LED-L  DI   ** R PROPOSED **
└──►│ gate C ├──[220R]── J-LED-R DI
```
`[repo] hardware/carrier/led-strip-drive/led-strip-drive.md, "§5 LED data"`

and its component table gives a range: *"`R-LED-SER` ×2–4 | **100–330 Ω**"*
`[repo] same file, "Component table"`. The prose says *"100–330 Ω at the
buffer"*. So the value is unresolved in the range, drawn at 220, and
single-valued at 330 in the BOM. qty 2 is correct and settled — the row's
revert to two is verified against the WS2815 recommended circuit
`[repo] hardware/bom.csv:23`, corroborated on the page at "§5".

---

## A12 · `R-OUT-PROT` — **P2** — the page that drove the power-rating raise still carries the old rating

BOM: `"1k 1%, >=500mW"`, with the derivation in the row:
*"Pitch shorted now rails the op-amp across this resistor: 142mW. Pitch against
a 220R output at −5V in output-to-output patching: 192mW … 250mW would be 1.3x;
specify >=500mW"* `[repo] hardware/module/bom.csv:2, hardware/bom.csv:87`.

| File | Says |
|---|---|
| `hardware/bom.csv` / `hardware/module/bom.csv` | `>=500mW` |
| `hardware/module/breath-output-stage/breath-output-stage.md:151` | `1206 ≥500 mW` ✓ |
| **`hardware/module/pitch-stage/pitch-stage.md:129`** | **`1206 ≥250 mW`** ✗ |

`[repo, grep for "250 mW|250mW|500 mW|500mW" over hardware/**]`

The raise was driven by the **pitch** stage taking jack-side feedback, and the
pitch page is the one that did not follow. (`R-SER-BREATH-INST` at ≥250 mW is a
*different* part and is consistent between `bom.csv:42` and
`breath-sense-link.md:134` — checked, not a defect.)

---

## A13 · `FB-IN` — **P2** — the selection rule a buyer reads is the one the datasheet refutes

The row opens with the live specification:

> *"One per branch: +12V analog, +12V umbilical, −12V, +5V. **Rated >=1A - the
> common 0805 600R part is ~300mA and a saturated bead is a wire.**"*
> `[repo] hardware/bom.csv:113, hardware/unplaced.csv:25`

`config/figures.yaml` lists **that exact sentence** as a forbidden pattern for
`ferrite-bias-impedance`, because it is refuted: *"THE '>=1 A' RULE DOES NOT DO
WHAT THE BOM ROW SAID IT DID. A bead's current rating is THERMAL, not magnetic
… A 3000 mA part in the same package with the same 600 ohm nominal reads ~145
ohm at 500 mA — SLIGHTLY WORSE than the 1500 mA part"*
`[repo] config/figures.yaml, figure ferrite-bias-impedance`.

The refutation **is** in the row — roughly 400 words later, after a `|`
separator `[repo] hardware/bom.csv:113`. The leading sentence, which is what a
reader sizing a second source acts on, still states the wrong rule as the
selection criterion.

This is the pattern `figures.yaml` already documents for a different row:
*"the bom.csv row's own LEADING sentence still said 0.05% with the refutation
appended 200 words later — the fix landed where the editor was, not where the
reader looks"* `[repo] config/figures.yaml, ref5050-grade caught_late_note`.
It has recurred on `FB-IN` and nothing catches it (§C).

`FB-IN` qty **4** is correct — FB1–FB4, one per rail, drawn
`[repo] hardware/module/power-entry/power-entry.md, "The circuit"`.

---

## A14 · `R-KEY-SER` and `C-KEY` — **P2** — notes carry the superseded 10 k / 10 nF network

The key network is `R-KEY-PU` 2.2 kΩ, `R-KEY-SER` 100 Ω, `C-KEY` 47 nF
`[repo] hardware/cluster/key-switch-network/key-switch-network.md, "§2"`, and
the crossing times are tracked: `key-release-time` = **119.9 µs**,
`key-press-time` = **5.92 µs** `[repo] config/figures.yaml`.

| Row | Says | Should be |
|---|---|---|
| `R-KEY-SER` | *"press is ~1us (**100R x 10nF**) … release is **~93us** (**10k x 10nF**)"* | 5.92 µs; 119.9 µs; 100 Ω ∥ 2.2 kΩ × 47 nF |
| `C-KEY` | *"Press crosses HC165's VIL (0.99V at 3.3V) in **~5.7us**"* | **5.92 µs** |
| `C-KEY` | *"Release crosses VIH (2.31V) at **~125us**"* | **119.9 µs** |
| `C-KEY` | *"**44x** margin against the 250us scan period"* | **42×** (page) |

`[repo] hardware/cluster/key-switch-network/bom.csv, hardware/bom.csv:35-36;
page values at hardware/cluster/key-switch-network/key-switch-network.md,
"Derivations" table]`

Every one of these evades its forbidden pattern by a character or two — the
exact escape CLAUDE.md §2 warns about:

| Forbidden in `figures.yaml` | What the BOM actually spells |
|---|---|
| `` `V_IL` at **5.7 `` | `in ~5.7us` |
| `` `V_IH` at **125 `` | `at ~125us` |
| `release ~93 us` | `release is ~93us` |

`[repo] config/figures.yaml, figures key-press-time / key-release-time]`

**And the page agrees with the BOM on one of them**, which is worse than
disagreeing: `key-switch-network.md` says *"The **125 µs** release filter is
half a scan period"* in prose, ninety lines below its own table that says
119.9 µs `[repo] hardware/cluster/key-switch-network/key-switch-network.md,
"Press is instant…"`. A cross-check between the row and the page therefore
finds false agreement. `figures.yaml`'s `false_positive_note` for
`key-release-time` protects a bare `125 us` because it also legitimately means
the mean sampling period — that exemption is what this sentence is hiding
behind. `C-KEY`'s `~103us` tau is correct and verified.

---

## A15 · `U-LOADSW` — **P1** — three orderable parts on one line, at qty 1, one of them undecided

```
U-LOADSW | part: "LT1641-1CS8 + DPAK/SO-8 N-FET + sense R"
         | package: "SO-8 + DPAK or SO-8 FET" | qty 1 | status: candidate
```
`[repo] hardware/module/umbilical-load-switch/bom.csv, hardware/bom.csv:55`

Three problems in one cell:

1. **The FET has no part number and is explicitly undecided.** The page: *"the
   FET is still TBD"*, and the selection criterion is *"chosen against the
   single-pulse SOA curve … The SOA chart must cover 12 V at 10 and 100 ms"*
   `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md,
   "Sizing the FB divider" and "What sizes the FET"`. Its `R_DS(on)` is an
   **assumption** that the `PWRGD` margin depends on — *"the FET drops about
   the same **if** its R_DS(on) is also ~50 mΩ — **an assumption, since the FET
   is still TBD**"*. A TBD part carried inside a `candidate` row is invisible
   to any status filter.
2. **"sense R" duplicates `R-ILIM`**, which has its own row
   `[repo] hardware/bom.csv:57`. The same part is budgeted twice.
3. **The row's own preferred grade is not the `part` field.** *"THE I-GRADE
   EXISTS: LT1641-1IS8 is −40 to +85degC against the CS8's 0 to +70degC, for a
   part in a rack that may sit in a hot van — **prefer it**"*
   `[repo] hardware/bom.csv:55`, repeated on the page *"the **I grade exists**
   and costs nothing to prefer"*. The `part` field still says `LT1641-1CS8`.

**Also in that row, a claim that over-reaches:** *"**EVERY** claim in this row
is now CONFIRMED against the document EXCEPT the VCC UVLO maximum"*
`[repo] hardware/bom.csv:55`. Two earlier claims in the same cell are not
confirmed — *"Set the limit at 1.0A"* (the datasheet gives 0.78 / **0.94** /
1.10 A at 50 mΩ `[repo] config/figures.yaml + hardware/bom.csv:57 R-ILIM`) and
*"with a programmed 50-100ms ramp"* (the page's own verdict: *"**ADR 0005's
'50–100 ms ramp' is not achievable with this part**"*
`[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md`). A
blanket "every claim confirmed" over a cell containing two refuted ones is the
kind of sentence that stops the next reviewer looking.

**Sourcing risk not flagged anywhere** `[from memory + repo]`: the LT1641 is a
legacy Linear Technology part; `analog.com` is unreachable and the datasheet
was recoverable **only** from *"the Internet Archive's 2019-02-02 capture"*
`[repo] datasheets/MANIFEST.csv, row LT1641-1CS8`. The corpus treats that as a
*fetch* problem. A part whose manufacturer serves no current datasheet is also
a *lifecycle* signal, and no row says so. Worth one line in the row before an
order is placed.

---

## A16 · `R-ILIM` — **P3** — the value the whole circuit is designed around is not in the row

```
R-ILIM | part: "Sense resistor, value from E6" | status: open
```
`[repo] hardware/bom.csv:57`

Every number on the load-switch page is computed at **50 mΩ** — the drawing
says `[R-ILIM 50mΩ]`, the limit is `47 mV / 50 mΩ = 0.940 A`, the foldback floor
is `12 mV / 50 mΩ = 240 mA`, and the `PWRGD` margin assumes a 20 mV drop at
0.4 A `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md
and hardware/module/power-entry/power-entry.md]`.

The row names its decider (`E6`) correctly per CLAUDE.md — that part is right.
What it does not do is state the 50 mΩ starting point, so the row and the four
derivations that depend on it are not linked in either direction. Compare
`R-REG-SET`, which handles the identical "selected on the bench" case by giving
the value **and** saying it is a starting point: *"R2 is SELECTED ON THE BENCH
at E7 … and the value here is the starting point"* `[repo] hardware/bom.csv:111`.

---

## A17 · `D-RESP` — **P2** — `part` and `package` name two different devices

```
D-RESP | part: "1N4148 x2, antiparallel" | package: "SOD-123 or SOD-323"
```
`[repo] hardware/module/breath-response-shaper/bom.csv, hardware/bom.csv:75`

`1N4148` is the DO-35 axial glass part; the SOD-123/SOD-323 device is
`1N4148W` `[from memory, and corroborated by the row's own banked-datasheet
note, which is entirely about **1N4148W**]`. The row's note already flags half
of it: *"Diotec's 1N4148W … is **SOD-123F, NOT SOD-123** — flat lead, no
standoff — so this row's 'SOD-123 or SOD-323' has to name the manufacturer"*
`[repo] hardware/bom.csv:75`. It names neither the manufacturer nor the `W`
suffix in the `part` field. Three candidate footprints (SOD-123, SOD-123F,
SOD-323) behind one unsuffixed part number.

---

## A18 · `C-FILT-MOD` — **P3** — an unresolved package with `VERIFY` in the field

```
C-FILT-MOD | "82nF C0G/NP0" | package: "1210 or film - VERIFY" | candidate | qty 4
```
`[repo] hardware/module/mod-channels/bom.csv, hardware/bom.csv:85`

`VERIFY` in the `package` column with `status: candidate` — CLAUDE.md requires
unresolved things to be marked `TBD`/`open` **and to say what decides them**.
This says neither. qty 4 is correct (four mod channels, one each)
`[repo] hardware/module/mod-channels/mod-channels.md, "The circuit — one channel of four"`.

---

# B. `hardware/unplaced.csv` — 50 rows, ~22 of them drawn

`module.md` already concedes part of this:

> *"**`hardware/unplaced.csv` holds this board's principal ICs** — the DAC, the
> in-amp, the LM317 — because BOM assignment matched on reference designator
> and these are drawn by part number. Known, recorded, not yet fixed."*
> `[repo] hardware/module/module.md, "Still open at board level"`

**The admission is a seventh of the problem.** Method: for each of the 50 rows,
grep every `hardware/**/*.md` for the refdes, then for the part number, then
for the value and the local label the drawing actually uses
`[calc, three grep passes over 42 schematic pages]`.

### B1 · Drawn, and it is not close — file these against their circuits

| Ref | Drawn on | Drawn as | Qty check |
|---|---|---|---|
| `U-DAC` | `module/dac8568/dac8568.md`; `digital-and-supervision.md` | `DAC8568C` in the block | 1 ✓ |
| `U-DIFFRX` | `module/breath-receive-stage/breath-receive-stage.md` | `INA828` box | 1 ✓ |
| `U-LVL-MOD` | `module/digital-and-supervision/digital-and-supervision.md` | `74AHCT125` box | 1 ✓ |
| `U-REG-DAC` | `module/power-entry/power-entry.md` | `[LM317LZ]` | 1 ✓ |
| `R-REG-SET` | `module/power-entry/power-entry.md` | `150R/475R 0.1%` | 2 ✓ |
| `C-REG-ADJ` | `module/power-entry/power-entry.md` | `[C 1µF]` | **1 of 2 — see A9** |
| `D-REVPOL` | `module/power-entry/power-entry.md` | `D1 D2 D3 1N5817` | 3 ✓ |
| `FB-IN` | `module/power-entry/power-entry.md` | `FB1 FB2 FB3 FB4` | 4 ✓ |
| `C-BULK-RAIL` | `module/power-entry/power-entry.md` | `C1 C2 C3 C4 47µF` | 4 ✓, **values conflict — A7** |
| `C-TIMER-LOADSW` | `power-entry.md`; `umbilical-load-switch.md` | `[C-TIMER 10µF]`, `C_T` | 1 ✓ |
| `C-GATE-LOADSW` | `power-entry.md`; `umbilical-load-switch.md` | `[C-GATE 82nF]` | 1 ✓ |
| `R-PRECISION` | `module/pitch-stage/pitch-stage.md` | `R1`/`R2` labelled `LT5400 1:1 pair` | 1 ✓ |
| `R-GAIN-INAMP` | `breath-receive-stage.md` | `R_G 42.2k` | 1 ✓ |
| `R-SER-BREATH` | `breath-receive-stage.md` | `R2`, `R3` `10k 0.1%` | 2 ✓ |
| `C-FILT-BREATH` | `breath-receive-stage.md` | `C_diff 15nF` + `C_cm 1.5nF` ×2 | 3 ✓ |
| `D-CLAMP-BREATH` | `breath-receive-stage.md` | *"BAV99 to ±12 V, both legs"* | 2 ✓ |
| `R-BREATH-SUM` | `breath-output-stage.md` | `R-IN 10k`, `R-FB 40k` | 2 ✓ |
| `R-BREATH-OFF` | `breath-output-stage.md` | `R-OFF 21.0k`, `R-OFFNEG 95.3k` | 2 ✓ |
| `J-CV` | `pitch-stage.md`, `mod-channels.md`, `breath-output-stage.md` | `PITCH jack`, `MOD n jack`, `BREATH jack` | 6 ✓ |
| `J-UMBILICAL` | `carrier.md`; `power-entry.md`; `umbilical-load-switch.md`; `panel-led.md` | `J-UMB`, `etherCON` | 2 ✓ |
| `LED-SIDE` | `led-strip-drive.md`; `power-entry-instrument.md` | `WS2815 strips` at `J-LED-L/-R` | 1 reel ✓ |
| `U-IMU` | `interfaces/spi-link/spi-link.md`; `carrier.md` | `QMI8658`; *"onboard: IMU GPIO10-13"* | 1 ✓ |
| `TUBE`, `MECH-PTFE` | `carrier.md:107-110` | *"400 mm tube + PTFE plug + ≤1 mL trap"* | see A10 |

`[repo, all rows verified by opening the named page and locating the label]`

**`D-CLAMP-BREATH` is the sharpest case:** its own note says
*"**Drawn on hardware/module/breath-receive-stage/breath-receive-stage.md** and
had no row"* `[repo] hardware/bom.csv:137` — the row records that it is drawn
and then sits in the file for parts that are not.

**The pattern is uniform and mechanical**, which is the useful part: none of
these 23 is undrawn. Every one is drawn under a **local label** (`R1`, `C_cm`,
`D1`, `FB2`, `R_G`, `PITCH jack`) or a **part number** (`INA828`, `LM317LZ`,
`DAC8568C`, `LT5400`). The assignment matched on refdes string and found
nothing, so an 88-row placed BOM and a 50-row orphan list are an artefact of the
matcher, not of the design. `module.md` names the cause correctly and
under-counts the effect by 7×.

### B2 · Genuinely unplaced — correct as they stand

`CAP1-n`, `U-MCU-SPARE`, `BENCH`, `U-OPA-GEN` (qty 0, `not-needed`), `J-USB`,
`U-ESD-USB`, `SW-BOOT` (all three `not-needed`: *"Dev boards carry these"*),
`PCB-MODULE`, `KNOB-BREATH`, `MECH-UBOLT`, `MECH-BACKPLATE`, `MECH-THUMBREST`,
`MECH-SERVICECOVER`, `MECH-FASTENER`, `ENDCAP-MOUTH`, `ENDCAP-TAIL`, `ADH-WOOD`,
`ADH-RTV`, `BODY-OAK`, `SIDE-ACRYLIC`, `MECH-WINDOW`, `MECH-MOUTH`,
`U-TVS-MODULE`, `CABLE-UMB`, `J-UMBILICAL-CABLE`, `U-DISP`.

Two notes on this list:

- **`U-DISP` is a real gap, not a filing error.** It is unplaced because *"the
  display board has no schematic page in this corpus … What that end needs —
  its regulator, its bulk capacitance, its console pinout — is asserted in
  ADR 0013 and in `bom.csv` and is drawn nowhere"*
  `[repo] hardware/carrier/display-and-service-uart/display-and-service-uart.md`.
  `C-BULK-DISP` (in the *placed* BOM) is that board's bulk capacitor, so the
  BOM carries parts for a board that does not exist as a page.
- **`U-TVS-MODULE` is deliberately open and says so** — *"DELIBERATELY open,
  not forgotten … Fit at E12 if E11 gives any reason to"*
  `[repo] hardware/bom.csv:131`. Correct per CLAUDE.md. But it is **not
  orderable**: `part` = *"Same three groups, module end of the etherCON"*,
  `package` = *"as above"*, `qty` = **1**. `[calc]` The instrument end's "three
  groups" are `U-TVS-SPI` (1) + `D-TVS-BREATH` (2) + `D-TVS-PWR` (1) = **4
  parts**, so qty 1 cannot be right whichever way the phrase is read.

---

# C. Why none of this trips the checker

`check-staleness.py` reports **PASS, 0 live stale values** and a
*"refuted in place (59)"* bucket. Using the checker's own functions
`[calc, importing tools/check-staleness.py and calling check_figures()]`:

```
live: 0    refuted: 59
  18  hardware/bom.csv
  10  hardware/unplaced.csv
   3  hardware/module/breath-receive-stage/bom.csv
   2  hardware/interfaces/spi-link/bom.csv
   2  hardware/module/umbilical-load-switch/bom.csv
   1  hardware/carrier/bom.csv      …and 23 in prose files
```

**28 of the 59 exemptions — just under half — land inside a BOM row.**

The mechanism is structural, not a tuning problem
`[repo] tools/check-staleness.py:60-67, 176-182`:

```python
ctx = " ".join(lines[first - 1:last])
(refuted if REFUTATION.search(ctx) else live).append(rec)
```

The refutation window is **a line**. In a prose page a line is ~80 characters
and "was / previously / no longer / rather than" genuinely sits next to the
value it refutes. **In `bom.csv` a line is an entire row**, and a `notes` cell
routinely runs 500–2000 words. Any one of those words anywhere in the cell
excuses every forbidden string in it.

Verified instances, one benign and two not:

| Row | Forbidden string | Excused by | Verdict |
|---|---|---|---|
| `C-TIMER-LOADSW` | `12x to 300x` | *"10nF **was** wrong by 12x to 300x"* — adjacent | **benign**, reads as a correction |
| `WIRE-LOOM` | `five connectors must match` | *"chained … **rather than** starred"*, a different clause about a different subject | **escape** — A5 |
| `FB-IN` | `Rated >=1A - … a saturated bead is a wire` | a refutation ~400 words later, after a `\|` separator | **escape** — A13 |

**The corpus already contains a written description of this hole**, in a BOM
row: *"Note also that check-staleness.py did NOT flag this row: the line
carries refutation wording for the OLD pedestal, so the exemption scored it
refuted-in-place while the NEW value it installed was stale. A refutation can
carry a wrong replacement and the exemption cannot tell"*
`[repo] hardware/bom.csv:68, TRIM-BREATH-ZERO]`. It was written about that row
and not generalised. `FB-IN` and `WIRE-LOOM` are live instances of the same
hole.

**Two smaller checker observations, recorded not fixed:**

- The advisory *"drawn in a schematic, no BOM row (19)"* includes a spurious
  entry `CO-MENTION`, harvested from all 23 `circuit.yaml` files
  `[repo] .staleness/report.txt]`. It is a parser artefact, and a false entry
  in an advisory list is how the list stops being read.
- **`R-FB`** (breath output stage's ×4 feedback resistor) is **missing** from
  that advisory list although `R-IN`, `R-OFF` and `R-OFFNEG` from the same
  drawing are present `[repo] .staleness/report.txt vs
  hardware/module/breath-output-stage/breath-output-stage.md, "The circuit"`.
  The likely cause is a prefix collision with `R-FB-HI` / `R-FB-LO` /
  `R-FB-REF`; unconfirmed, and worth five minutes because a detector with a
  silent miss is worse than none.

---

# D. Drawn but absent from the BOM entirely

The checker's advisory already lists 19 `[repo] .staleness/report.txt`. Sorted
by what they cost:

### D1 · Real parts, drawn, argued for, with no row

| Name | Drawn on | What the page says |
|---|---|---|
| `R-LED-PD` ×2, 10 kΩ | `led-strip-drive.md` §5 (in the drawing) | *"the fix for a real hole … On reset GPIO1 and GPIO2 are high-impedance … that is random pixel data … **Two 0805s, and they cannot be added later**"* |
| `J-LED-L`, `J-LED-R`, 4-way | `led-strip-drive.md` §5; `power-entry-instrument.md` (12 V and GND pass through them) | *"Proposed — 12 V, GND, `DI`, `BI`"* |
| `J-DISP`, 9-way | `display-and-service-uart.md` §6; `carrier.md` block diagram; `power-entry-instrument.md` (buck B feeds it) | *"9 conductors, 360 mm, up a side channel"* |
| `C-ADC-BULK`, 10 µF X7R | `carrier.md` §2 drawing; `breath-adc.md` component table | *"the ADC's scale factor is the dev board's LDO output, and it has no anti-alias filter of its own … the WS2815 PWM rate at ~2 kHz, which is exactly Nyquist for a 4 kHz sampler"* |
| `LK-CLR`, solder pad | `dac8568.md` drawing **and** its Interfaces table | *"`LK-CLR` asserts it by hand"* — `R-CLR-PU`'s row pays for it (*"A solder pad to ground beside it"*) but it has no row of its own |
| `R-IN`, `R-FB`, `R-OFF`, `R-OFFNEG` | `breath-output-stage.md` | covered by `R-BREATH-SUM` / `R-BREATH-OFF` **under different names** — see D3 |

`[repo, each verified in the named drawing]`

**`J-LED-L/-R` and `J-DISP` are the expensive ones**: three connectors that
three separate pages route power and signal through, with no row, no pin count
in the BOM and no cost. A loom cannot be crimped from this BOM.

### D2 · Named as missing by the page itself — correctly flagged, still absent

- **The `ON`-pin divider**, four passives: *"There is no divider, no logic
  level, no supply, no pull-down, no debounce and no UVLO threshold specified
  anywhere — **four missing passives on the node that decides whether the
  instrument powers up at all**"*
  `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md,
  "Still not designed: the `ON` pin"`. No BOM row, not even a `TBD` one, and
  its decider **is** named on the page (*"the trip point is an ADR 0005
  decision"*) — so a row could be written today.
- **`TP-*` / `LK-*`**: *"Proposed — `D2` asked for test points, shunt links and
  an LA header on this board and none exist in the BOM"*
  `[repo] hardware/carrier/carrier.md:296]`.
- **An RJ45 jack footprint at the instrument end**, *"(~16 × 14 mm, **not in
  the BOM**)"* `[repo] hardware/carrier/carrier.md, "Still open"`.

### D3 · Name collisions — the drawing and the BOM use different refdes for the same part

| Drawn as | BOM row | Where |
|---|---|---|
| `R-IN` 10 k + `R-FB` 40.2 k | `R-BREATH-SUM` "10k / 40.2k 1%" qty 2 | `breath-output-stage.md` |
| `R-OFF` 21.0 k + `R-OFFNEG` 95.3 k | `R-BREATH-OFF` "21.0k / 95.3k 1%" qty 2 | `breath-output-stage.md` |
| `R2`, `R3` | `R-SER-BREATH` | `breath-receive-stage.md` |
| `R4`, `R5` | `R-BIAS-INAMP` | `breath-receive-stage.md` |
| `C_diff`, `C_cm` ×2 | `C-FILT-BREATH` | `breath-receive-stage.md` |
| `R1`, `R2` | `R-PRECISION` (LT5400) | `pitch-stage.md` |
| `R1`, `R2` (again, different circuit) | `R-MODGAIN` | `mod-channels.md` |
| `D1`, `D2`, `D3` | `D-REVPOL` | `power-entry.md` |
| `C1`–`C4` | `C-BULK-RAIL` | `power-entry.md` |
| `FB1`–`FB4` | `FB-IN` | `power-entry.md` |
| `J-UMB` | `J-UMBILICAL` | `carrier.md`, `spi-link.md`, `breath-sense-link.md` |
| `R-SCLK-SER`, `R-MOSI-SER`, `R-CS-SER` | `R-SPI-SER` qty 3 | `spi-link.md` — the page flags it itself: *"Same three parts, two naming schemes, neither side"* `[repo] hardware/interfaces/spi-link/spi-link.md:54-57` |

`R1` and `R2` mean four different resistors on three pages. None of this is
netlistable as it stands.

### D4 · Dead names still in drawings — cleanup, not parts

`R-TERM-CHAIN` (deleted by ADR 0001), `R-OFFINJ` (*"`R-OFFINJ` is deleted"*,
`pitch-stage.md`), `R-PRESENCE`, `R-OE-PU`, `R-CLR-PD` (all belong to the
deleted LM311/74HC123 supervision) `[repo] .staleness/report.txt and the named
pages]`. They inflate the "drawn, no BOM row" advisory to the point where the
five real entries in D1 do not stand out.

---

# E. Fragment ownership — rows filed against the wrong circuit

CLAUDE.md: *"A row lives with the circuit **whose page derives its value**."*
These do not.

| Ref | Filed in | Page that derives it | Confidence |
|---|---|---|---|
| `C-TIMER-LOADSW`, `C-GATE-LOADSW` | `unplaced.csv` | `module/umbilical-load-switch/` — both drawn in its gate network and sized on it | **high** |
| `R-BIAS-INAMP` ×2 | `module/pitch-stage/bom.csv` | `module/breath-receive-stage/` — drawn there as `R4`/`R5`; `pitch-stage.md` only **cites** it as prior art (*"This project already fixed the identical problem on the breath in-amp with `R-BIAS-INAMP`"* `[repo] pitch-stage.md:322`) | **high** |
| `PANEL` | `module/panel-led/bom.csv` | `module/panel/` — which has a page and a `circuit.yaml` and **no `bom.csv`**; `panel.md` is where 10HP × 3U is derived | **high** |
| `C-DECOUPLE-CARRIER` qty 8 | `carrier/led-strip-drive/bom.csv` | board-level (`carrier/bom.csv`) — it is *"one per supply pin: MCP3202, REF5050 IN AND OUT, OPA2197 +12V, 74AHCT125, MPXV4006DP, and both R-78E5 inputs"*, of which the LED circuit owns **one** | **high** |
| `C-DECOUPLE` qty 19 | `module/umbilical-load-switch/bom.csv` | board-level (`module/bom.csv`) — the load switch derives **one** 0.1 µF `VCC` bypass; the other 18 belong to five other circuits | **high** |
| `U-OPA-PITCH` qty 6 | `module/breath-receive-stage/bom.csv` | board-level — its note enumerates ten halves across six circuits | medium |
| `LK-SER` qty 4, `R-SER-TERM` | `interfaces/key-chain-loom/bom.csv` | `cluster/cluster-boards.md` — both rows say *"PROPOSED by hardware/cluster/cluster-boards.md"*, and both are per-cluster-board parts | medium |
| `R-SPI-PULL` qty 6 | `interfaces/spi-link/bom.csv` | `module/digital-and-supervision/` — all six are drawn there, both sides of the module's buffer; `digital-and-supervision/` has **no `bom.csv`** | medium |

`[repo, each verified by opening the fragment and the two candidate pages]`

**Three circuit directories have a page and no fragment**:
`module/digital-and-supervision/`, `module/panel/`, `module/link-supervision/`.
The third is correct and says so: *"**NOT FITTED. Nothing in this directory is
on the board** … neither ever had a `bom.csv` row. There is no circuit to draw
here and no part to buy"* `[repo] hardware/module/link-supervision/link-supervision.md:1-6`.
The first two are not — they draw parts that are filed elsewhere or nowhere.

**Also worth flagging:** `config/figures.yaml` names
`hardware/module/power-entry/power-entry.md` as the `owner` of
`loadswitch-timer`, `loadswitch-gate-cap` and `loadswitch-fb-divider`
`[repo] config/figures.yaml]`. Those three quantities moved to
`umbilical-load-switch/` in the 2026-09-21 split
`[repo] hardware/module/power-entry/power-entry.md:8-11: "Split 2026-09-21.
The load switch moved to umbilical-load-switch/"`. Four `owner` pointers in
`figures.yaml` also point at **`hardware/bom.csv`**, which is generated — the
text they name lives in a fragment, so following the pointer leads to a file
that must not be edited.

---

# F. Sourcing and status

### F1 · No sourcing data

`source` populated on **2** rows (`SW1-n` → *"Amazon"*, `CAP1-n` → *"Beekeeb"*),
`manufacturer` on **34**, of 138 `[calc, column census]`. No MPN-to-distributor
mapping, no stock, no price, no lead time. Nothing can be quoted from this
file.

### F2 · Status spread

`candidate` 81 · `open` 33 · `selected` 17 · `not-needed` 4 · `purchased` 2 ·
`available` 1 `[calc]`. **98 of 138 rows (71 %) are `candidate` or `open`.**
Whatever else is true, this is not an orderable state, and no row is in a
"released" state at all — there is no such status.

### F3 · `TBD`/`open` rows that do not say what decides them

CLAUDE.md requires a decider. These have none `[repo, each row's `notes` read in
full]`:

`C-BULK-DISP` (part `TBD`, and `package` = *"1206 / electrolytic THT"*, which is
two incompatible packages) · `BODY-OAK` (`TBD`) · `SIDE-ACRYLIC` (`TBD`) ·
`MECH-THUMBREST` (`TBD`) · `MECH-BACKPLATE` (`TBD`) · `U-TVS-CHAIN` ·
`R-CHAIN-SER` · `LK-SER` · `PCB-CLUSTER` · `HDR-DEV` · `CABLE-UMB` ·
`U-RESP` · `POT-RESP`.

Correctly formed, for contrast: `SW-THUMB` (*"ADR 0002 leaves the spring weight
to M1"*), `R-ILIM` (*"value from E6"*), `R-TRIM-RANGE` (*"Values with the stages
at E10"*), `MECH-PTFE` (*"Size the orifice at E2"*), `MECH-FASTENER`
(*"an M4 CAD output"*), `U-TVS-MODULE` (*"Fit at E12"*),
`J-UMBILICAL-CABLE` (*"Decide the variant off a real drawing … BLOCKED in
datasheets/MANIFEST.csv"*).

**`WIRE-LOOM` has the opposite problem:** `status: open`, and its note begins
*"**DECIDED 2026-09-21**"* `[repo] hardware/bom.csv:29`. The status contradicts
the cell.

### F4 · Datasheet coverage — one part is neither banked nor BLOCKED

`D-TVS-BREATH` = `PESD12VS1UB`. **`PESD12VS1UB` returns zero matches in
`datasheets/MANIFEST.csv`** `[calc, grep -c = 0]`, and there is no `BLOCKED`
row for it. CLAUDE.md §3: *"A part that could not be fetched gets a row too,
with `status=BLOCKED` and the exact URLs — an honest gap is useful."*

This matters because the row's entire selection argument is a datasheet claim
stated without one: *"12V STANDOFF, NOT 5V. BREATH's normal top of range is
4.7V against a 5V array's V_RWM - 300mV of margin … with **1.5uA of leakage**
into a 1k output resistor"* `[repo] hardware/bom.csv:43]`. The 1.5 µA and the
12 V standoff are both unsourced, and the SOD-323 package is unverified.

(`U-ESD-USB` = `USBLC6-2SC6` is also absent from the manifest, but its status is
`not-needed`, so that is correct.)

### F5 · Single-source / lifecycle risks the corpus does not flag

Flagged by the corpus, correctly — no action: the two dev boards (ADR 0013 names
discontinuation as a redesign risk; `U-MCU-SPARE` mitigates it), the etherCON
variant, the `MT165-MX` keycap (`BLOCKED`), `SW-POWER`'s bushing.

**Not flagged** `[from memory, marked as inference]`:

- **`U-LOADSW` / LT1641** — see A15. Manufacturer serves no current datasheet;
  the only copy is a 2019 Internet Archive capture.
- **`U-TVS-SPI` / SP0504BAHT** — the only obtainable document is *"a databook
  chapter extract, **NOT a standalone part datasheet**, and CARRIES NO DOCUMENT
  NUMBER AND NO REVISION DATE anywhere in it"*, with
  `littelfuse.com`, `mouser` and `alldatasheet` all failing
  `[repo] datasheets/MANIFEST.csv, rows SP0504BAHT]`. The corpus treats this as
  a *fetch* problem and records two replacement candidates already rejected on
  package grounds (`SP3012-06UTG` obsolete/uDFN-14; onsemi `ESD7104` UDFN10
  only). A part with no revisioned datasheet and two dead alternatives is a
  sourcing risk, and the row says `candidate` with no lifecycle note.
  Minor: the orderable code is **`SP0504BAHTG`** (the `G` suffix) per the
  manifest's own reading of the ordering page; the BOM says `SP0504BAHT`.
- **`R-PRECISION` / LT5400** and **`U-DAC` / DAC8568** are sole-source by
  construction (ADI and TI respectively) with no second source named. Fine as a
  decision; worth being explicit before an order.

### F6 · Duplicate part strings across rows

Not defects, but an order built row-by-row will over-buy and under-consolidate
`[calc, part-string grouping over 138 rows]`:

- **OPA2197 in three rows, two spellings, three package strings**:
  `U-BUF` `OPA2197IDR` / `SOIC-8 (1.27mm pitch)` qty 1 ·
  `U-OPA-PITCH` **`OPA2197`** (no `IDR` — not an order code; the suffix is the
  package and packing) / `SOIC-8 (1.27mm pitch)` qty 6 ·
  `U-RESP` `OPA2197IDR` / **`SOIC-8`** qty 1. Total 8 packages.
- `74AHCT125` in two rows (`U-LVLSHIFT`, `U-LVL-MOD`), 2 total.
- `100nF X7R` in three rows (`C-DECOUPLE-CARRIER` 8, `C-DECOUPLE-165` 4,
  `C-DECOUPLE` 19 — the last spelled `100nF X7R 50V`), 31 total.
- `BAV99` in two rows (`D-JACK-CLAMP` 6, `D-CLAMP-BREATH` 2), 8 total.
- `100R 1%` in four rows, 28 total. `10k 1%` in three rows, 8 total.

**A dependency worth recording:** `C-DECOUPLE` qty 19 is enumerated as
*"**6 x OPA2197** on +/-12V = 12, INA828 = 2, DAC8568 AVDD+DVDD = 2,
74AHCT125, LT1641 VCC, LM317 in"* `[calc: 12+2+2+1+1+1 = 19 ✓]`
`[repo] hardware/bom.csv:56`. `U-RESP` is a **seventh** OPA2197 package
(`open`, qty 1) `[repo] hardware/bom.csv:76`, so if the response shaper is
adopted, `C-DECOUPLE` must become **21**. Nothing links the two rows.

---

# G. Quantities verified correct

Recorded so the next reviewer does not redo them, and because CLAUDE.md asks for
verifications to be written down.

| Ref | Qty | Verified against |
|---|---|---|
| `J-CHAIN` | 8 | `key-chain-loom.md` *"carrier 1, RT 2, RH 2, LT 2, LH 1"*; `figures.yaml chain-connectors` = 8 `[calc: 1+2+2+2+1 = 8]` |
| `R-KEY-PU` | 24 | *"21 switch positions + 3 free bits (22, 23, 31)"*; `key-marker-and-bits.md` allocation table `[calc: 21+3]` |
| `R-KEY-SER`, `C-KEY`, `SW1-n`, `CAP1-n` | 21 | *"21 of these"* networks; 18 fitted + 3 reserved spare-switch positions |
| `U-KEYS`, `C-DECOUPLE-165`, `PCB-CLUSTER` | 4 | one per cluster board; 4 × 8 bits = 32 = 21 + 8 marker + 3 free `[calc]` |
| marker straps | **0 parts** | *"strap straight to the rails — no resistor, no capacitor … 16 parts saved"* — correctly absent from the BOM |
| `R-CHAIN-SER` | 3 | `SCK`, `SH/LD`, `SER` in the `J-CHAIN` drawing |
| `R-SPI-SER` | 3 | `carrier.md` §4 drawing; `figures.yaml spi-series-r` |
| `R-SPI-PULL` | 6 | `digital-and-supervision.md` drawing, 3 cable-side + 3 DAC-side |
| `R-MODGAIN` | 8 | 4 channels × (`R1` 10 k + `R2` 30 k) `[calc]` |
| `C-FILT-MOD` | 4 | one per mod channel |
| `J-CV`, `R-OUT-PROT`, `D-JACK-CLAMP` | 6 | pitch + 4 mods + breath `[calc]` |
| `R-OPAMP-IN` | 7 | *"Pitch, mod 1-4, the mod offset buffer, the VREFOUT follower"* `[calc: 1+4+1+1]` |
| `R-BIAS-DAC` | 6 | six DAC-driven nodes; DAC8568 populated 6 of 8 |
| `U-OPA-PITCH` | 6 | *"twelve halves, TEN used … TWO SPARE"*, cross-checked against `breath-output-stage.md`'s *"Two op-amp halves … Ten of twelve halves used"* |
| `C-DECOUPLE-CARRIER` | 8 | enumeration `[calc: 1+2+1+1+1+2 = 8]` |
| `C-DECOUPLE` | 19 | enumeration `[calc: 12+2+2+1+1+1 = 19]`, with the `U-RESP` caveat in F6 |
| `C-REF-OUT` | 2 | `carrier.md` §2 draws `C-REF-OUT#1` and `#2` |
| `U-BUCK`, `C-STRIP-BULK`, `D-USBOR` | 2 | `power-entry-instrument.md` drawing |
| `L-BUCK-IN`, `D-REVSHUNT`, `D-TVS-PWR`, `MECH-GNDBOND` | 1 | same drawing |
| `D-REVPOL` 3, `FB-IN` 4 | | `power-entry.md` drawing |
| `R-SER-BREATH-INST`, `D-TVS-BREATH` | 2 | `carrier.md` §2 (`R1` and `R1b`) |
| `KNOB-BREATH` | 3 | three panel pots (`POT-GAIN`, `POT-OFFSET`, `POT-RESP`) — correct **if** `POT-RESP` (status `open`) lands |
| `LED-SIDE` | 1 | *"Qty is a REEL, not a length. 0.84 m used of 1 m"* |

**`adr` column spot-check — four suspicions raised and all four dismissed**
`[repo, each checked against the ADR named]`:

- `U-MCU-RT` → 0007. ADR 0007's status line reads *"Accepted. **Board selected:
  Waveshare ESP32-S3-Matrix.**"* — correct, despite the ADR being titled *IMU
  selection*.
- `R-LDAC`, `R-CLR-PU` → 0004. ADR 0004 discusses `CLR` at length
  (`:494`–`:523`) — defensible.
- `SW-POWER` → 0004. ADR 0004:235 specifies *"a rated SPST toggle for power"* —
  correct.
- `POT-GAIN`, `POT-OFFSET` → 0003. ADR 0003 owns the panel-knob zeroing
  argument (`:90`, `:618`) — defensible.

One residual inconsistency, low severity: within a single circuit the `adr`
column splits. `breath-output-stage/` files `POT-GAIN`/`POT-OFFSET`/
`R-GAIN-FLOOR` under **0003** and `C-OUT-BREATH` under **0006**;
`led-strip-drive/` files `C-DECOUPLE-CARRIER` under **0013** and its two
siblings under **0014**. Both are defensible per-row and neither is
defensible as a pattern.

---

# H. Suggested order of work

Nothing here was changed. If it is picked up, this ordering minimises rework:

1. **A1 `U-DAC` order code.** Touches `bom.csv`, ADR 0006 ×2, `MANIFEST.csv`
   and a banked filename. Route through `repo-maintenance.md` §3 (§4: the
   manifest is generated).
2. **A2, A3, A4, A17 — packages.** One pass with the banked PDFs open. A3 is a
   `MANIFEST.csv` fix, not a `bom.csv` one.
3. **B1 — re-file the ~23 drawn rows out of `unplaced.csv`.** Doing this before
   the quantity fixes means A7/A8/A9 land in the fragment that owns them. It
   also shrinks `unplaced.csv` to the ~26 rows it is supposed to describe, so
   the count means something again.
4. **A5, A6, A7, A8, A9, A10, A11, A12, A14 — quantities and values.** Each is
   one row or one drawing.
5. **C — the checker's line-scoped refutation window.** Until it is narrowed
   (a sentence, or the text *between `|` separators* in a BOM cell), every
   forbidden pattern inside a `notes` field is unprotected, and that is where
   the most-cited numbers in the repo live. Fixing the escapes in A13/A14/A5
   without fixing this just resets the clock.
6. **D1, D2 — write rows for the five real missing parts** (`R-LED-PD`,
   `J-LED-L/-R`, `J-DISP`, `C-ADC-BULK`, `LK-CLR`) and the `ON`-pin divider.
   Then **D4**: delete the six dead refdes from the drawings so the advisory
   list is readable.
7. **F4** — a `BLOCKED` row for `PESD12VS1UB`, with URLs.
8. **F1** — if this BOM is ever to be ordered from, the `source` column has to
   be filled. 2 of 138 is not a start.

---

## Method and limits

Read: all 42 pages under `hardware/**` (~5000 lines), all 24 BOM fragments,
`hardware/bom.csv`, `hardware/unplaced.csv`, `config/figures.yaml`,
`datasheets/MANIFEST.csv`, `docs/decisions/0006` and targeted sections of
0003/0004/0005/0007. Ran `merge-bom.py --check` and `check-staleness.py`
read-only, and called the latter's `check_figures()` directly to enumerate the
refuted bucket. Extracted and read text from four banked PDFs
(`SS34`, `SS14`, `SMAJ15A`, `DAC8568CIPW`) — `pdftotext` and `pdftoppm` are not
installed in this sandbox, so extraction was done by inflating the PDF content
streams and reading the text-show operators; that recovers body text reliably
and **cannot** read vector drawings or raster figures.

**Not checked, and someone should:**

- Package correctness for parts whose PDFs are image-only or vector-CAD:
  `PJ398SM` (drawing is a `.jpg`), `NKK-SERIES-M-TOGGLE`, the ferrite drawings,
  the Neutrik DXF, the KS-33 footprints. The manifest says these were read by
  rendering at 150–700 dpi; I could not render.
- `INA828IDR`, `REF5050AIDR`, `MCP3202-CI/SN`, `OPA2197IDR`, `LM317LZ`,
  `74HC165`, `SN74AHCT125` order codes and packages were checked for **form**
  `[from memory]`, not against their banked PDFs. Only `DAC8568` was verified
  against its ordering table. Given that the one verified code was wrong, the
  others deserve the same treatment.
- Whether `hardware/module/panel/` and `hardware/module/digital-and-supervision/`
  should get `bom.csv` fragments is an ownership judgement I have flagged but
  not made.
- Actual availability, price and lead time on any part — no distributor was
  reachable and none was tried.
