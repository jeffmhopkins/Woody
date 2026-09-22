# D10 — Can this BOM still be ordered and built?

**Slice:** the BOM as a buildable artefact, after the 2026-09-22 surgery
(two new fragments, 18 rows out of `unplaced.csv`, `R-LED-PD` added, `PANEL`
moved, nine `notes` rewritten, `NO_PARTS` added to `merge-bom.py`).

**Method.** Read the 139 rows of `hardware/bom.csv` and all 25 fragments as an
order, not as a diff. Rebuilt the master independently (own concatenator, own
byte comparison — not `merge-bom.py --check`). Cross-checked quantities against
the ASCII drawings and `## Interfaces` tables. Read the banked PDFs with
`pymupdf` for the three order codes that could be settled from a document.
Provenance on every claim; `[repo]` paths are absolute-from-root with line
numbers.

**Headline.** The mechanics are clean — the master is byte-exact, 11 columns,
CRLF throughout, no duplicate refdes, no fragment outside `ORDER`, and
`NO_PARTS` is truthful. The order codes changed on 2026-09-22 are correct and
land everywhere. What did not survive the audit is the *derived* layer: three
corpus documents still describe a BOM that no longer exists, two rows that were
moved now sit beside pages that contradict them, and a "same reel" ordering
instruction survives the topology change that killed it.

---

## Part 1 — The seven questions in the brief

### 1. Ordering: is every `part` an orderable thing?

`U-DAC` verified against the banked datasheet's own addendum, and it is right.

> `[datasheet] datasheets/analog/DAC8568CIPW.pdf` p.54, PACKAGE OPTION
> ADDENDUM: `DAC8568IAPW / IAPWR / IBPW / IBPWR / ICPW / ICPWR / IDPW /
> IDPWR`, all `TSSOP / PW / 16 pins / ACTIVE`. `DAC8568ICPW` occurs 4 times in
> the document; **`DAC8568CIPW` occurs 0 times** (whole-document text scan,
> 62 pages).

So `U-DAC` = `DAC8568ICPW`, `TSSOP-16 (0.65mm pitch)` `[repo]
hardware/module/dac8568/bom.csv:4` is correct in both fields, and the change
landed completely: no corpus file spells `DAC8568CIPW` as an order code any
more — the six remaining occurrences are the banked file's *name*, the
`.manifest-R2` fragment (a historical record), and ADR 0006's narration of the
correction `[repo] docs/decisions/0006-cv-channel-allocation.md:176-183`.

**One residue.** `datasheets/MANIFEST.csv` now carries **both** rows against
the same file and SHA — line 2 `DAC8568CIPW` (from `.manifest-R2.csv`) and
line 3 `DAC8568ICPW` (from `.manifest-R9.csv`, whose own note says it
"SUPERSEDES" line 2). Both are live rows in the generated manifest, so a
reader looking up datasheet coverage for the DAC finds the un-orderable
spelling first. This is a consequence of the correct §4 decision not to edit
another wave's fragment; the honest fix is a `status` or note on the R2 row's
successor, not a deletion. **Low severity, flagged because the manifest is
what an order is checked against.**

#### 1a. `U-TVS-SPI` names an order code that is not in its own banked datasheet

`[repo] hardware/interfaces/spi-link/bom.csv:4` — `part = SP0504BAHT or
equivalent 4-channel 5V array`, `package = SOT-23-5 (0.95mm pitch)`.

> `[datasheet] datasheets/discrete-and-power/SP0504BAHT.pdf` p.1 Ordering
> Information lists `SP0502BAHTG, SP0503BAHTG, SP0504BAHTG, SP0505BAHTG,
> SP0504BAATG, SP0506BAATG, SP0502BAJTG, SP0504BAJTG, SP0505BAJTG` — **every
> orderable code carries a trailing `G`.** p.6 outline drawing: `SP0504BAHTG -
> SOT23-5`. Whole-document scan: `SP0504BAHTG` 3 occurrences,
> `SP0504BAHT` (not followed by G) **0 occurrences**.

The **package is right** (SOT23-5, 4-channel — verified), so this is a suffix,
not a transposition: the non-`G` part is presumably the pre-RoHS version, and
the banked document is titled "SP050xBA **Lead-Free/Green**". But it is the
same defect class the same batch fixed on `U-DAC`, in a row whose own notes are
entirely about order-code hygiene ("It was un-orderable as written"), and the
`MANIFEST.csv` row and the banked filename both use the non-`G` spelling too.
**Claim:** the orderable code is `SP0504BAHTG`. Settled by the Ordering
Information table above; nothing else needed.

#### 1b. `D-USBOR` offers two alternatives and one footprint, and the footprint admits only one of them

`[repo] hardware/carrier/power-entry-instrument/bom.csv:7` — `part = 1N5817 or
SS14`, `package = DO-41 THROUGH-HOLE`, `status = candidate`, no decider in the
notes.

> `[datasheet] datasheets/discrete-and-power/SS14.pdf` p.1: "Case: **SMA
> (DO-214AC)**", repeated three more times. The 1N5817 is DO-41 axial
> `[repo] hardware/module/power-entry/bom.csv:4` uses it as such.

So the two alternatives are a through-hole part and an SMD part, and the single
`package` field names only the first. **This is the exact defect the same batch
fixed three rows below, in the same file**: `D-REVSHUNT` `[repo]
.../power-entry-instrument/bom.csv:10` had its package corrected from DO-214AC
to DO-214AB by reading `SS34.pdf`, and its note says so verbatim ("This row
said DO-214AC, which is the SS14's package"). `SS14.pdf` was banked in the same
wave. The fix landed on the row being edited and not on the row two lines away
that shares the fact. **Medium severity — it is a footprint on a board, and
the row has no decider.**

#### 1c. `D-RESP` names a through-hole part in an SMD package

`[repo] hardware/module/breath-response-shaper/bom.csv:4` — `part = 1N4148 x2,
antiparallel`, `package = SOD-123 or SOD-323`.

The plain **1N4148 is DO-35 axial**. The SMD parts are `1N4148W` (SOD-123) and
`1N4148WS` (SOD-323). The row's own notes are about two banked **1N4148W**
datasheets and even observe that "this row's 'SOD-123 or SOD-323' has to name
the manufacturer" because Diotec's part is SOD-123**F** — but the `part` field
was never changed from `1N4148`. `[repo]` the notes name
`datasheets/discrete-and-power/1N4148W.pdf` and `1N4148W-DIOTEC.pdf`.
**Medium severity: as written the part and the package cannot both be ordered.**

#### 1d. `U-LOADSW` is three parts in one row, and one of them has no part number

`[repo] hardware/module/umbilical-load-switch/bom.csv:3` — `part = LT1641-1CS8
+ DPAK/SO-8 N-FET + sense R`, `package = SO-8 + DPAK or SO-8 FET`, `qty = 1`,
`status = candidate`.

Three problems in one field: (a) "DPAK/SO-8 N-FET" is a description, not an
orderable part, and the notes make the FET choice load-bearing ("Choose a DPAK
or SO-8 part against its SINGLE-PULSE SOA CURVE") with no decider named;
(b) "+ sense R" duplicates `R-ILIM`, which is its own row one line below with
its own quantity — the sense resistor is counted twice; (c) the notes close
with "LM5069MM or LTC4210 equally valid", two more alternatives with no
decider. `qty = 1` for a composite of three parts also means the line-item
count is wrong for a quote. **High severity for an order: this is the part the
module's whole start-up behaviour rests on and it cannot be put in a basket.**

#### 1e. `FB-IN`'s package field contradicts the chosen part

`[repo] hardware/module/power-entry/bom.csv:8` — `part = Laird MI1206K601R-10
(600R @ 100MHz, **1206**, 1.5A)`, `package = **1206 or 1210**`. The part number
is a 1206 part and the part string says 1206; the manifest's named second
source (`HI1206N601R-10`) is also 1206 `[repo] datasheets/MANIFEST.csv:41`.
The "or 1210" is left over from before the part was chosen. **Low severity,
one-word fix.**

#### 1f. Generic part strings where the corpus's own rule says to be specific

ADR 0006 states the rule `[repo] docs/decisions/0006-cv-channel-allocation.md:239`:

> **Specify the full orderable part number in the BOM**, not "DAC8568". The
> grade letter is the whole decision and it is invisible in the generic name.

The rule is obeyed for `U-DAC` and broken for the parts beside it:

| Row | `part` | `mfr` | Comparable row that *is* specific |
|---|---|---|---|
| `U-OPA-PITCH` ×6 `[repo] hardware/module/breath-receive-stage/bom.csv:2` | `OPA2197` | TI | `U-BUF`, `U-RESP` both say `OPA2197IDR` |
| `U-LVL-MOD` ×1 `[repo] hardware/module/digital-and-supervision/bom.csv:2` | `74AHCT125` | *(empty)* | `U-LVLSHIFT` says `74AHCT125`, `mfr = multiple` |
| `U-KEYS` ×4 `[repo] hardware/cluster/key-register/bom.csv:2` | `74HC165` | multiple | — |

The `U-LVL-MOD` / `U-LVLSHIFT` pair is worth one line on its own: the same part
in two rows, and the **new** fragment's row is the one with an empty `mfr`.

**`U-KEYS` is not cosmetic, and this is the sharpest ordering finding in the
slice.** The vendor choice for the 74HC165 is load-bearing on a *settled
tracked figure*. `[repo] config/figures.yaml:216-230`, `key-release-time`:

> `threshold_note`: "onsemi's MC74HC165A/D Rev. 13 p.4 **PUBLISHES A 3.0 V
> ROW**, V_IH 2.1 V / V_IL 0.9 V … TI's SCLS116E has **NO 3.3 V row**"
> `conservative_bound`: "**If a TI SN74HC165 is the part fitted**, its own
> datasheet guarantees nothing at 3.3 V and the pessimistic bound is
> V_IH = 2.475 V, giving **138.7 us**" — against the settled **119.9 us**.

So the register knows the answer depends on which vendor is bought, and the BOM
row that decides it says `74HC165 / multiple / candidate` and carries no note
about vendor at all. The register absorbs it ("the release is absorbed by the
asymmetric debounce either way"), so **this is a provenance defect, not a
design defect** — but it is the one row where a purchasing decision can move a
`settled` figure by 19 µs, and nothing in the BOM says so.

#### 1g. Ranges and descriptions in `part`, no decider

`L-BUCK-IN` = `10-47uH power inductor, >=1A`, `status = candidate` `[repo]
hardware/carrier/power-entry-instrument/bom.csv:5`; `C-STRIP-BULK` =
`470-1000uF electrolytic, 16V`, `candidate` `[repo] …:4`. A 4.7× inductance
range and a 2.1× capacitance range are not orderable, and neither row is
`open`, so neither is required to name a decider (see §3). Compare
`R-TRIM-RANGE`, which is the same kind of unknown and is correctly `open` with
"Values with the stages at E10".

### 2. Quantities: re-counted against the drawings

Every multi-quantity row was re-derived. **All of them are arithmetically
right**, and several were right for reasons only visible on a *different* row:

| Row | qty | Check | Verdict |
|---|---|---|---|
| `C-DECOUPLE` | 19 | 6×OPA2197 on ±12 V = 12, INA828 = 2, DAC AVDD+DVDD = 2, 74AHCT125, LT1641 VCC, LM317 in `[calc] 12+2+2+1+1+1 = 19` | ✅ (but see 4c) |
| `C-DECOUPLE-CARRIER` | 8 | MCP3202, REF5050 VIN, REF5050 VOUT, OPA2197, 74AHCT125, MPXV4006DP VS, 2× R-78E5 in `[calc] = 8` | ✅ |
| `U-OPA-PITCH` | 6 | 12 halves, 10 used (pitch, mod 1-4, mod-offset follower, VREFOUT follower, breath REF-zero, breath gain, breath summer) `[calc] 1+4+1+1+1+1+1 = 10` | ✅ (but see 4c) |
| `R-OPAMP-IN` | 7 | pitch + mod 1-4 + mod-offset buffer + VREFOUT follower `[calc] = 7` | ✅ |
| `R-BIAS-DAC` | 6 | one per populated DAC channel; `U-DAC` notes "Populate 6 of 8" | ✅ |
| `J-CV`, `R-OUT-PROT`, `D-JACK-CLAMP` | 6 each | `panel.md` Interfaces names PITCH + BREATH_OUT + MOD 1-4 = 6 cutouts `[repo] hardware/module/panel/panel.md:30-35` | ✅ |
| `R-SPI-PULL` | 6 | drawing shows `[R-SPI-PULL x3]` twice `[repo] hardware/module/digital-and-supervision/digital-and-supervision.md` | ✅ |
| `R-SPI-SER` | 3 | SCLK, MOSI, CS | ✅ |
| `D-REVPOL` | 3 | D1, D2 (+12 V split), D3 (−12 V); bus +5 V deliberately gets none `[repo] hardware/module/power-entry/power-entry.md:42,49,75,142` | ✅ |
| `FB-IN`, `C-BULK-RAIL` | 4 each | FB1-FB4 / C1-C4 in the drawing | ✅ qty; ❌ value, see 4b |
| `R-MODGAIN` | 8 | 4 channels × (R1 10k + R2 30k); `[calc]` k = 3, gain 1+k = 4, intercept 3 × 3.3333 = 10.000 V → ±10.000 V exactly | ✅ |
| `C-FILT-MOD` | 4 | mods only; breath has its own `C-OUT-BREATH` | ✅ |
| `R-KEY-PU` / `R-KEY-SER` / `C-KEY` | 24 / 21 / 21 | 21 switch positions + 3 free bits pulled but not filtered; matches `key-pullup-qty` = 24 `[repo] config/figures.yaml:299-311` | ✅ |
| `U-KEYS`, `C-DECOUPLE-165` | 4 each | one per cluster board | ✅ |
| `J-CHAIN` | 8 | matches `chain-connectors` = 8 `[repo] config/figures.yaml:291` | ✅ |
| `KNOB-BREATH` | 3 | POT-GAIN + POT-OFFSET + POT-RESP; `panel.md:68` derives ≤14 mm for three-across | ✅ |
| `U-BREATH` | 2 | **one** sensor is drawn `[repo] hardware/carrier/carrier.md:105,288` and `SKT-BREATH` is qty 1 | ✅ — rationale is on the *neighbouring* row: "ADR 0003 calls the sensor a wear part and buys two" `[repo] hardware/carrier/bom.csv` `SKT-BREATH` notes. **Not a defect.** Recorded because it reads as a defect until you find the sentence, and it is on a row an orderer of `U-BREATH` has no reason to open. |

**What the restructure did break is not the arithmetic — it is the level.**
Four board-level quantities now live in circuit fragments, so a per-circuit
BOM generated from a fragment attributes the whole board's count to one
circuit:

- `C-DECOUPLE` **19** in `hardware/module/umbilical-load-switch/bom.csv:4`.
  The load switch needs **one** (LT1641 VCC). The page names the row exactly
  once, as an aside `[repo] .../umbilical-load-switch.md:310`, and the page
  that actually derived the current count is a different one — `[repo]
  hardware/module/digital-and-supervision/notes.md:28`: "**`C-DECOUPLE` drops
  from 21 to 19.**"
- `C-DECOUPLE-CARRIER` **8** in `hardware/carrier/led-strip-drive/bom.csv:3`.
  The LED driver needs **one** (the 74AHCT125). The other seven are the ADC,
  the reference ×2, the buffer, the sensor and the two bucks.
- `U-OPA-PITCH` **6** in `hardware/module/breath-receive-stage/bom.csv:2`.
  That circuit uses **one half** (the in-amp's REF buffer); the six-package
  count is derived by `breath-output-stage.md:155-157` ("Ten of twelve halves
  used across the module").
- `R-BIAS-INAMP` **2** in `hardware/module/pitch-stage/bom.csv:2` — see 6b,
  this one the tool's own docstring already calls out by name.

These four belong in the board-level shared fragments (`hardware/module/bom.csv`,
`hardware/carrier/bom.csv`), which is what `ORDER`'s own comment says they are
for ("Shared fragments last … the cross-cutting rows").

### 3. Status hygiene: 34 `open` rows, 13 name what decides them

`CLAUDE.md`: "Mark unresolved things `TBD`/`open` **with what decides them**."

**Counts** `[calc]` over `hardware/bom.csv`: 139 rows — `candidate` 81,
`open` **34**, `selected` 17, `not-needed` 4, `purchased` 2, `available` 1.
Twelve rows carry `TBD` in `part`.

Of the 34 `open` rows:

- **13 name a milestone or test that decides them** — `SW-THUMB` (M1),
  `R-ILIM` (E6), `R-TRIM-RANGE` (E10), `MECH-PTFE` (E2), `MECH-WINDOW` (M6),
  `CABLE-UMB` (E6), `MECH-MOUTH` (E2), `MECH-UBOLT` (M8), `MECH-FASTENER`
  (M4 CAD), `MECH-SERVICECOVER` (M4 CAD), `U-TVS-MODULE` (E12 if E11 gives a
  reason), `J-UMBILICAL-CABLE` (obtain a vendor drawing), **`R-LED-PD` (E1)**.
- **4 name a decider with no milestone** — `R-RESP` ("a bench pass with a
  player"), `R-SER-TERM` ("a FIRMWARE choice rather than a board choice"),
  `F-CHAIN` ("RE-OPEN THIS DECISION: either a much lower-resistance part, or
  accept the unfused conductor, or move the protection to the source end"),
  `ENDCAP-MOUTH` ("IF IT LOOKS WRONG ON THE BENCH").
- **17 name nothing** — `C-BULK-DISP`, `MECH-COAT`, `PCB-CARRIER`, `HDR-DEV`,
  `WIRE-LOOM`, `PCB-CLUSTER`, `R-CHAIN-SER`, `U-TVS-CHAIN`, `LK-SER`,
  `POT-RESP`, `D-RESP`, `U-RESP`, `TUBE`, `PCB-MODULE`, `MECH-BACKPLATE`,
  `MECH-THUMBREST`, `ENDCAP-TAIL`.

**`R-LED-PD` does answer the question it was added under.** `[repo]
hardware/carrier/led-strip-drive/bom.csv:5`: "**WHAT DECIDES IT: E1, where the
strips first run** — if the boot window shows no spurious pixels without it, it
is not needed. Two parts, one per strip." Qty 2 ✅ (one per strip, matching
`R-LED-SER` qty 2 and the two-data-line topology). Package `0805`, part
`10k 1%`, `adr = 0014`. **This row is correct and complete and is the best-formed
row added in the batch.** The five rows added alongside it in the same wave —
`R-CHAIN-SER`, `U-TVS-CHAIN`, `F-CHAIN`, `LK-SER`, `R-SER-TERM`, all "PROPOSED
by carrier.md / cluster-boards.md and never given a row until 2026-09-21" —
were not held to the same standard: four of the five name no decider.

**Three status-vs-content contradictions**, which are the other half of the
rule:

- **`U-REF-BREATH` is `candidate` while its own part number is a tracked
  `disputed` figure.** `[repo] config/figures.yaml:716-728` `ref5050-grade`:
  `status: disputed`, candidates `REF5050AIDR` vs `REF5050IDR`,
  `decided_by: "Changing one letter in the order code, or accepting 2x the
  initial error and 2.7x the drift"`. The BOM row `[repo]
  hardware/carrier/breath-excitation-reference/bom.csv:2` says
  `REF5050AIDR / candidate`. This is the **one row in the BOM whose order code
  is an open question**, and it is not `open`. (Its leading sentence *was*
  fixed — it now reads "±0.1%, 8ppm/degC AS SPECIFIED", closing the
  `caught_late_note` complaint at `figures.yaml:726`. That half landed.)
- **`C-TIMER-LOADSW` and `C-GATE-LOADSW` are `selected`** with no part number,
  and packages that are still two alternatives (`THROUGH-HOLE radial or 1210
  ceramic`; `0805 or 1206`). `C-TIMER-LOADSW`'s own notes make low leakage
  decisive ("specify a low-leakage part or the timer never resets") — a
  requirement no part has been chosen against. `selected` should mean a part
  is picked.
- **`R-REG-SET` is `candidate` while `R-ILIM` is `open` for the same reason.**
  Both are bench selections: `R-ILIM` = "Sense resistor, **value from E6**"
  (`open`), `R-REG-SET` = "R2 is **SELECTED ON THE BENCH at E7** … the value
  here is the starting point" (`candidate`). One class, two statuses.
- **`BODY-OAK` and `SIDE-ACRYLIC` are `candidate` with `part = TBD`** and no
  decider (`[repo] hardware/unplaced.csv:8,9`, notes "Bottom panel thickness
  sets thumb key inset depth" / "Edge-lit"). `candidate` with a `TBD` part is
  a contradiction in the two fields.
- **`C-FILT-MOD` is `candidate` with `package = 1210 or film - VERIFY`** — an
  explicit unresolved verify inside a row that is not `open`.

### 4. Internal contradictions

#### 4a. The "same reel" ordering instruction died with the mod-channel topology and is still being given, in two files

`[repo] hardware/unplaced.csv:32`, `R-BREATH-SUM` notes, verbatim:

> "R-IN 10k, R-FB 40.2k. **Same E96 feedback part as R-MODGAIN, bought on the
> same reel**"

`[repo] hardware/module/breath-output-stage/breath-output-stage.md:149`:

> | **R-FB** | 40.2 kΩ 1 % | Fixed ×4. **Same E96 part as `R-MODGAIN`** |

And `R-MODGAIN` `[repo] hardware/module/mod-channels/bom.csv:3`:

> `part = 10k / 30k 1% metal film`, qty 8 — "EIGHT, not sixteen: R1=10k,
> R2=30k per channel … Lands on EXACTLY ±10.000V, where the **old
> four-resistor difference amp needed a 40.2k fudge** to reach ±10.05. …
> **Buy from one reel.**"

`R-MODGAIN` no longer contains a 40.2 kΩ value at all — the row that retired it
says so in the same sentence that calls it a "fudge". So **two corpus files
tell you to buy `R-FB` off a reel that is not being bought**, and one of them
is the generated master (`hardware/bom.csv`, the `R-BREATH-SUM` row). The
values themselves are fine — 10k + 40.2k is what the ×4 summer needs `[calc]
1 + 40.2/10 = 5.02`… note in passing that `breath-output-stage.md:105` states
the gain as `R-FB/R-IN = 4`, which is 40/10, not 40.2/10 — a 0.5 % rounding
the page does not flag. **The ordering claim is the defect; the topology change
landed on `mod-channels` and not on the two places that read it.**

#### 4b. `C-BULK-RAIL` was moved into `power-entry`'s fragment, and `power-entry.md` contradicts it twice

The row `[repo] hardware/module/power-entry/bom.csv:9`:

> `part = 100uF (+12V) / 47uF (-12V, +5V) 25V electrolytic`, qty 4 —
> "**NOT 47uF on every rail.** The +12V branch carries the LM317's divider,
> the DAC and the comparator, about 22mA against -12V's 10mA — so at 47uF each
> it collapses 2.2x faster … **100uF on +12V balances the decay.**"

The page it now lives with, in its own drawing `[repo]
hardware/module/power-entry/power-entry.md:42,49,75,77`:

```
  +12V ├───┬──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V
       │   └──[D2 1N5817]──[FB2]──[C2 47µF]──┬──────── PWR_GND (star)
  -12V ├───[D3 1N5817]──[FB3]──[C3 47µF]────────── MODULE ANALOG −12V
   +5V ├───[FB4]──[C4 47µF]──────────────────────── 74AHCT125 only
```

and in prose at `power-entry.md:190`: "**Entry bulk is 4 × 47 µF**, which is
2–5× the surveyed norm of 10–22 µF."

C1 and C2 are the two +12 V branches, so the BOM says 100 µF where the page
says 47 µF, **twice in the drawing and once in prose**. `[repo]` git: the
`100uF (+12V)` string predates this batch (`7a5236c`), and `0e68f25` moved the
row into this fragment without reconciling it. The relocation is what makes it
visible: the assignment rule put the row beside the page that derives its
value, and the page disagrees with it. **High severity — one of the two is a
wrong capacitor on an entry rail, and the row's argument is the more
recently-reasoned of the two.**

**And the row's justification cites a deleted part.** "The +12V branch carries
the LM317's divider, the DAC and **the comparator**" — the LM311 presence
comparator is deleted `[repo]
hardware/module/link-supervision/link-supervision.md`, "There is no presence
detect either", and `C-DECOUPLE`'s own notes record removing its two decoupling
caps for exactly that reason. This is the §5 class `CLAUDE.md` says no grep
finds: the 22 mA figure that decides 100 µF over 47 µF includes a load that
does not exist.

#### 4c. Three rows disagree about whether the response shaper is fitted

- `U-OPA-PITCH` `[repo] hardware/module/breath-receive-stage/bom.csv:2`:
  "Six packages, twelve halves, TEN used … **TWO SPARE**."
- `U-RESP` `[repo] hardware/module/breath-response-shaper/bom.csv:5`, `status
  = open`: "This stage **consumes BOTH remaining spare OPA2197 halves**, so
  the separate A5 finding — `POT-OFFSET`'s wiper is unbuffered … — **needs
  this additional package**."
- `C-DECOUPLE` = 19, whose enumeration counts "6 x OPA2197" and silently omits
  `U-RESP`'s two supply pins `[calc] 19 → 21 if the shaper is fitted`.

Taken together: if the shaper is fitted there are **no** spare halves and the
decoupling count is short by two; if it is not, `U-OPA-PITCH`'s "TWO SPARE"
stands. Neither row says which case it is describing. **And the settled panel
figure has already picked a side**: `panel-height-budget` `[repo]
config/figures.yaml:400-405` derives its content height from "**three pots
across** at 14 mm knobs 22", `panel.md:31` calls `POT-RESP` "the one that made
three-across a single row instead of two", and `KNOB-BREATH` is qty **3**. So a
`settled` tracked figure and a purchased-quantity row both assume the shaper,
while the op-amp count and the decoupling count assume it is not — with all
four of the shaper's own rows (`POT-RESP`, `R-RESP`, `D-RESP`, `U-RESP`) marked
`open` and none of them naming a decider. **Medium-high: this is the one place
where the BOM's arithmetic and a settled figure rest on opposite answers to the
same open question.**

#### 4d. `C-FILT-MOD` and `C-GATE-LOADSW` cannot both be true

Same value, same dielectric, contradictory packages:

| Row | part | package | status |
|---|---|---|---|
| `C-FILT-MOD` `[repo] hardware/module/mod-channels/bom.csv:2` | `82nF C0G/NP0` | `1210 or film - VERIFY` | candidate |
| `C-GATE-LOADSW` `[repo] hardware/module/umbilical-load-switch/bom.csv:11` | `82nF C0G/NP0 or film, 50V` | `0805 or 1206` | **selected** |

`C-FILT-MOD` says: "**82nF in C0G/NP0 almost certainly does not exist in
0805** — C0G permittivity puts that value in 1210 or larger." If that is right
it is equally right for `C-GATE-LOADSW`, which is marked `selected` in
`0805 or 1206` and whose notes dwell on the value ("SET TO 82nF (E24; 83nF is
not orderable)") without ever touching the package. A film 82 nF will not fit
0805 either. **One of these two package fields is wrong; the `selected` one is
the one to doubt.**

#### 4e. `U-TVS-CHAIN` and `U-TVS-SPI` are the same job in two packages

`U-TVS-SPI` = `SP0504BAHT…`, **SOT-23-5**, verified 4-channel (1a above).
`U-TVS-CHAIN` `[repo] hardware/interfaces/key-chain-loom/bom.csv:4` = "4-channel
TVS array", **SOT-23-6**, no part number, `open`, and its note says
"`U-TVS-SPI` **does exactly this job** for the umbilical's three". In the family
the corpus already chose, 4-channel is SOT23-5 and SOT23-6 is the 5-channel
`SP0505BAHTG` `[datasheet] SP0504BAHT.pdf` p.7. So the row asks for a channel
count and a package the chosen family does not pair. **Low-medium; it is
`open`, but it points at the wrong footprint.**

#### 4f. `KNOB-BREATH` tells you to match a part that does not exist

`[repo] hardware/unplaced.csv:20`: "Match the shaft of the **POT-BREATH**
variant ordered — D-shaft and knurled are not interchangeable." There is no
`POT-BREATH` row; the pots are `POT-GAIN`, `POT-OFFSET`, `POT-RESP`. A dangling
refdes inside the sentence that tells you what to order. **Low, one word.**

#### 4g. `C-KEY` / `R-KEY-SER` — the rewrite is correct and complete ✅

Checked as asked: **no number was left behind.**

- `R-KEY-SER` `[repo] hardware/cluster/key-switch-network/bom.csv:4` now cites
  by name: "press crosses V_IL at **key-press-time** … release crosses V_IH at
  **key-release-time**". Its only numerals are inside the refutation clause
  ("SUPERSEDED: this field carried ~1us and ~93us, both computed on the
  10k/10nF network that is no longer fitted"), which the register's own rule
  allows.
- `C-KEY` `[repo] …/bom.csv:5` cites both figures by name and restates only
  numbers that **agree with the register**: tau ~103 µs (register derivation
  "tau = 103.40 us"), V_IL 0.99 V and V_IH 2.31 V (register `threshold_note`,
  the onsemi 3.0 V row), and the 250 µs scan period. `[test]` all four retired
  strings from the two `escape_note`s — `~5.7us`, `44x margin`, `~125us`,
  `~93us` — appear in `hardware/bom.csv` only inside the `SUPERSEDED:`
  clauses; `44x margin` appears zero times. The commit hook agrees: "staleness
  check: PASS no live stale values".

This is the fix in the batch I would hold the others to.

### 5. The generated master — verified independently ✅

`[test]` own script (`ORDER` parsed out of `tools/merge-bom.py`, fragments read
in binary, master rebuilt with `csv.writer(lineterminator="\r\n")`, `bytes ==
bytes`):

```
master bytes: 131725   CRLF: 140   bare LF: 0   bare CR: 0
built  bytes: 131725   identical: True
total rows: 139        duplicate refdes: none
every fragment: 11 columns, header exact, ends with CRLF, zero bare LF
```

140 CRLF = 139 rows + header. Every one of the 25 fragments on disk is named in
`ORDER`; nothing on disk is missing from `ORDER`; the only `ORDER` entry absent
from disk is `hardware/module/link-supervision/bom.csv`, which is in
`NO_PARTS`. `merge-bom.py --check` independently reports "checked 139 rows from
26 fragments | 0 problems", agreeing with the byte comparison.

**One cosmetic mislabel in that summary line:** "26 fragments" counts
`hardware/unplaced.csv`, which the corpus's own vocabulary does not treat as a
per-circuit fragment (`CLAUDE.md`: "`hardware/unplaced.csv` holds the rows no
schematic page names"). The real counts are **25 fragments + unplaced**. It
matters only because it is the number a reader would quote — see 7a, where
three documents quote three different ones.

### 6. The two new fragments

Both are **well-formed** (11 columns, exact header, CRLF, single row each) and
both are in `ORDER` in a sensible place — `digital-and-supervision` between
`dac8568` and `link-supervision`, `panel` last of the twelve module circuits
before the shared `hardware/module/bom.csv`.

#### 6a. `digital-and-supervision` — right row, right home ✅

`U-LVL-MOD` belongs there and the page says so in as many words `[repo]
hardware/module/digital-and-supervision/digital-and-supervision.md`, Interfaces
table: "**Sourced here** — the 74AHCT125 (`U-LVL-MOD`) is this circuit's part."
The drawing's `[R-SPI-PULL x3]` twice matches that row's qty 6. Only defect is
the empty `mfr` field (1f).

#### 6b. `panel` — right row, but it left behind the row the same page derives

`PANEL` is correctly assigned and correctly stated: `2mm aluminium, 10HP x 3U
(50.50 x 128.5mm)` matches `panel-width` = "50.50 mm (10HP)" and its derivation
`(10 × 5.08) − 0.3` `[repo] config/figures.yaml:386-391`, and 128.5 mm matches
the `panel-height-budget` derivation's two banked artefacts. The notes correctly
refuse to restate the budget ("**THE BUDGET IS THE TRACKED FIGURE
panel-height-budget — do not restate it here**") and record why: "every one of
them escaped the forbidden list by a single removed space, because this file
spells NNmm and the register spelled NN mm." That is rule §2's trap, written
down by the row it bit. ✅

**But `KNOB-BREATH` stayed in `unplaced.csv`** `[repo]
hardware/unplaced.csv:20` while `panel.md` is the page that derives it:
`panel.md:68-70` derives the ≤14 mm knob, `KNOB-BREATH`'s own notes restate
that derivation almost verbatim ("three pots across 50.50mm with 3mm gaps needs
<=14mm knobs"), and `breath-output-stage.md:27` explicitly hands it over: "Row
and knob geometry belongs to **the panel page**, not here." The fragment created
today for exactly this circuit has one row and should have two.

#### 6c. Two of the three refdes edges a cold reviewer verified as **false** are the fragments those rows are now filed in

`[repo] hardware/module/pitch-stage/circuit.yaml:20-31` — the same comment block
is in all 23 `circuit.yaml` files:

> "A cold reviewer verified three refdes edges as false by reading:
>   `pitch-stage -> R-BIAS-INAMP`   the page names it as an explicit CONTRAST
>   `breath-adc  -> C-STRIP-BULK`   a citation of a note about the LED strip
>   `breath-receive -> U-OPA-PITCH` a package-count consequence, not a use"

And `tools/merge-bom.py:18-22`, the assignment rule's own worked example:

> "A row lives in the fragment for the circuit **WHOSE PAGE DERIVES ITS VALUE**.
> Not where it is mentioned, not where it is mounted … '**Where it is
> mentioned' fails on R-BIAS-INAMP**, named once in the whole corpus — on the
> PITCH page, as a contrast."

`R-BIAS-INAMP` is filed in `hardware/module/pitch-stage/bom.csv:2`.
`U-OPA-PITCH` is filed in `hardware/module/breath-receive-stage/bom.csv:2`.
**The tool documents both of these placements as the wrong rule, by name, and
makes both of them.** `C-STRIP-BULK` is correctly *not* in `breath-adc`.

Where they belong: `R-BIAS-INAMP`'s value is derived by ADR 0005 `[repo]
docs/decisions/0005-power-architecture.md:371` ("`R-BIAS-INAMP`, two 1 MΩ
resistors from each input to…") and ADR 0003, i.e. the breath receive path, so
`breath-receive-stage` (which holds `U-DIFFRX`). `U-OPA-PITCH`'s count is
derived by `breath-output-stage.md:155-157`, and being a board-wide package
count it belongs in `hardware/module/bom.csv`. Minor correction to the
docstring while it is open: "named once in the whole corpus" is not right —
it is also named at ADR 0005:371 and ADR 0006:222.

#### 6d. The move out of `unplaced.csv` answered "placed" and not "named"

`pcb-pipeline.md:167-169` states the test:

> "**Drawn, named and placed are three different tests**, and only the
> circuit's `bom.csv` fragment answers the third."

`D-CLAMP-BREATH` was fixed properly — the drawing now writes the refdes, and
its row records it ("It was drawn on breath-receive-stage.md TWICE and the
drawing never wrote the refdes … it passed only the first"). **The other 15
rows moved in the same batch were not held to that standard.** `[test]` for
every row, does any `.md` in its own circuit directory contain its refdes:

Named by **no** hardware page at all: `U-DAC`, `U-DIFFRX`, `R-PRECISION`,
`FB-IN`, `C-BULK-RAIL`, `D-REVPOL`, `U-REG-DAC`, `R-REG-SET`, `C-REG-ADJ`,
`J-UMBILICAL`, `C-TIMER-LOADSW`, `C-GATE-LOADSW`, `R-GAIN-INAMP`,
`C-FILT-BREATH`, `J-CV`, `U-KEYS`, `R-OUT-PROT`, `R-OPAMP-IN`, `D-JACK-CLAMP`.

Corpus-wide: **`J-CV` is named in exactly one corpus file — `pcb-pipeline.md`,
the file that says it is unplaced.** `R-PRECISION` is named in **zero** corpus
files outside the BOM. `U-DAC` only in ADR 0006.

`hardware/README.md:73-78` gives the reasoning and it is honest ("those parts
are drawn under a local label (`R1`, `C_cm`, `FB2`, `R_G`) or a part number
(`INA828`, `LM317LZ`, `DAC8568`)"), and `power-entry.md`'s drawing is a good
example of it — `[C-TIMER 10µF]`, `[C-GATE 82nF]`, `[C 1µF]`, `C1`–`C4`,
`FB1`–`FB4`, none of them BOM refdes. **The finding is not that the move was
wrong; it is that the batch established the naming standard on one row and
applied it to one row.** For a netlist transcribed from the pages — the stated
purpose of the `## Interfaces` tables — nothing still joins the picture to 15
of those rows.

### 7. `NO_PARTS` — the declaration is true ✅

`link-supervision` genuinely names no orderable part. `[repo]
hardware/module/link-supervision/link-supervision.md` opens:

> "**NOT FITTED. Nothing in this directory is on the board.** … There is no
> circuit to draw here and **no part to buy**."

Every part it names is named as deleted or as a costed hypothetical: the 74HC123
and LM311 are gone ("neither ever had a `bom.csv` row"), and the restoration
proposal is explicitly priced as *not* free — "restoring **an LM311, its two
decoupling caps, `R-PRESENCE` and a 74AHCT14** — four parts, **none of which has
a BOM row today**." That is the right shape: a costed non-part, not a silent
gap. The `NO_PARTS` reason string matches the page. ✅

Two small notes on the mechanism itself:

- **It is silent when it fires.** `load()` does `if rel in NO_PARTS: continue`
  and prints nothing, so a run gives no visible statement that a circuit was
  skipped — against the docstring's own principle that "'Not every circuit owns
  parts' is a real situation, so it has to be SAID rather than inferred from a
  missing file." It is said in the source and not in the output.
- **`NO_PARTS` keys are not validated against `ORDER`.** A key with a typo, or
  one for a path no longer in `ORDER`, is ignored without comment. Today's
  single entry is correct, so this is latent.
- One refdes escapes the declaration in the other direction: `LK-CLR` is named
  on four corpus pages (`link-supervision.md`, `dac8568.md`,
  `breath-receive-stage/notes.md`, `firmware/README.md`) and has **no BOM
  row**. It is a solder pad, and `R-CLR-PU`'s description already covers it
  ("with a bring-up pad"), so `NO_PARTS` survives — a pad is not orderable.
  Recorded so the next reviewer does not re-raise it.

---

## Part 2 — The two sibling claims

### Claim A: "`360 mA` appears in 6 corpus files against a register that says `359 mA`"

**Occurrence: confirmed. Staleness: not confirmed — and a `forbidden` pattern
would break rule §2.** The claim is also understated: there are *three*
roundings, not two.

`[test] grep` over the corpus (`docs/review/`, `docs/log/`, `docs/research/`
excluded), `[repo]`:

| Spelling | Where |
|---|---|
| `359 mA` (15 hits) | `config/figures.yaml:601` (the register, `settled`), `0005-power-architecture.md:96,159` (the owner), `0004-cv-interface-module.md:276,284`, `pcb-pipeline.md:219,282`, `power-entry/bom.csv:8` (`FB-IN`) |
| `~360 mA` / `360mA` (6 files) | `umbilical-load-switch.md:57,62,222,325`, `power-entry.md:7,170`, `0004-cv-interface-module.md:627,633`, `power-entry-instrument/bom.csv:2` (`U-BUCK`), `key-switch-network/bom.csv:3` (`R-KEY-PU`), and both of those again in the generated `hardware/bom.csv` |
| `~350 mA` / `350mA` | `breath-sense-link.md:223`, `0003-breath-sensing-path.md:391`, `pitch-stage/bom.csv:2` (`R-BIAS-INAMP`) + the master |

**Why it is not staleness.** `[test]` the register's `value` was `"359 mA"` in
**every one of the 20 recorded versions** of `config/figures.yaml` — it has
never moved. So `360 mA` is not a value that failed to follow a change; it is a
rounding. And it is used *consistently in correct arithmetic*: `[calc]`
`umbilical-load-switch.md:222`, `940 − 360 = 580 mA`, then
`2.2 mF × 8.01 V / 580 mA = 30.4 ms`, `17.1 + 30.4 = 47.5 ms` — all three
figures check out, and at 359 mA the answer is 47.4 ms against a conclusion
("the `TIMER` must exceed 47.5 ms") that does not move.

**Therefore a `forbidden` pattern on `360 mA` is exactly the trap `CLAUDE.md`
§2 records**: its cheapest fix would be to rewrite a page whose arithmetic is
right. The useful action is the opposite one — a `rounding_note` or
`false_positive_note` on the `umbilical-current` entry stating that ~360 and
~350 are legitimate roundings of it, so the next cold wave stops re-finding it.
The entry already does this for the adjacent 392 mA and says nothing about the
two roundings of its own value.

**One thing in the claim's neighbourhood is worth the note anyway:** the CSV
spellings. `U-BUCK` spells it `360mA`, `R-KEY-PU` spells it `360mA`, and
`R-BIAS-INAMP` spells it `350mA` — no space before the unit, in the file the
`panel-height-budget` and `key-release-time` `escape_note`s both name as the one
that escapes markdown-spelled patterns. If this figure ever does move, the
grep-first step has to be run against the CSV spelling or it will miss four
hits in `hardware/bom.csv` and its fragments.

### Claim B: "`pcb-pipeline.md` may still name `J-CV ×6` and `D-CLAMP-BREATH ×2` as unplaced"

**Confirmed, and it is worse than the claim** — the whole block is stale, on
six numbers, and it went stale **inside the commit that placed both parts**.

`[repo] docs/reference/pcb-pipeline.md:150-176`, against `[test]` a recount of
the current tree:

| The page says | Actually |
|---|---|
| `hardware/bom.csv`, the generated master — **138 rows, 388 units** | **139 rows, 390 units** |
| "In the **23** per-circuit fragments — **104 rows, 313 units**" | **25** fragments, **107 rows, 323 units** |
| "In `hardware/unplaced.csv` — no page names them — **34 rows, 75 units**" | **32 rows, 67 units** |
| "five are module-board netlist parts …: **`J-CV` ×6**, `U-TVS-MODULE`, **`D-CLAMP-BREATH` ×2**, `R-BREATH-SUM` ×2, `R-BREATH-OFF` ×2. **Thirteen units.**" | **three** rows, **five** units — `U-TVS-MODULE` ×1, `R-BREATH-SUM` ×2, `R-BREATH-OFF` ×2 |
| "`D-CLAMP-BREATH` is the shape of the problem. It **is drawn** … and **its row is still in `unplaced.csv`**" | Placed: `hardware/module/breath-receive-stage/bom.csv:7`, and the drawing now writes the refdes |
| "**The CV jacks are not** [placed], and neither are the four rows beside them" | `J-CV` placed: `hardware/module/bom.csv:5` |

`[test]` git: `J-CV` and `D-CLAMP-BREATH` left `unplaced.csv` in `04b5208`
("The six items the agents could not reach"), whose own message says "The
drawing names it now, and the row is placed" — **and that same commit edited
`docs/reference/pcb-pipeline.md`**, rewriting the net-collision table from four
collisions to five, twenty lines above the block that names the two parts it had
just placed. The fix landed where the editing was; the paragraph a PCB engineer
reads to find out what the netlist will be missing was left describing the
previous tree.

**The same two counts are wrong in two more corpus files, and both were also
open in this batch:**

- `[repo] hardware/README.md:72` — "It was 50 rows and is now **34**.
  **Sixteen** of them were drawn all along". Now 32 and eighteen.
  `hardware/README.md` was edited in `79f5c4a`, in this batch, which added a
  whole new `## The Interfaces table` section and did not touch line 72.
- `[repo] docs/reference/repo-maintenance.md:204` — "`hardware/unplaced.csv`
  holds the **50 rows of 138** that no schematic page names … **six identical
  jack-protection networks** drawn three times, and **nineteen decoupling
  capacitors with no home**". Now 32 of 139, and *both* named clusters are
  placed: the jack protection is `hardware/module/bom.csv` (`J-CV`,
  `R-OUT-PROT`, `D-JACK-CLAMP`, all ×6) and the nineteen decouplers are
  `C-DECOUPLE` in `umbilical-load-switch/bom.csv:4`. This file has not been
  corrected since `d71488e`, and it too was edited in this batch (`79f5c4a`).

So **four documents state the size of this BOM and all four are wrong, in three
different ways** (50 / 34 / 34 / "26 fragments"), in the repository whose first
rule is that shared figures are stated once and cited. The obvious mechanical
answer is that row and unit counts are not shared figures at all — they are
*derivable*, and `merge-bom.py` already prints them. A `--stats` output cited
by name, or the counts moved into `config/figures.yaml` with the tool as their
owner, would close a class that has now gone stale three times in two days.

---

## Part 3 — Verdict

**Can it be ordered?** Not as it stands, but the blockers are few and named.
Hard blockers: `U-LOADSW` (1d, no FET part number, sense resistor counted
twice), `D-RESP` (1c, part and package cannot both be ordered), `D-USBOR` (1b,
footprint admits one of two alternatives). Order-code corrections available
from banked documents today: `SP0504BAHT` → `SP0504BAHTG` (1a). Decisions that
have to be taken before a basket, not during: `U-REF-BREATH`'s grade letter
(the register's `decided_by` is one letter), and the 82 nF C0G package
(`C-GATE-LOADSW` vs `C-FILT-MOD`, 4d).

**Can it be built?** The quantities are sound — every multi-quantity row
re-derived correctly, which is the part of this BOM in the best condition.
Two things would be built wrong from the current corpus: the +12 V entry bulk
capacitors (4b, 47 µF vs 100 µF, page against row), and `R-FB` ordered off a
reel that is not being bought (4a). One open question is answered two
contradictory ways across four rows and a settled figure (4c, the response
shaper).

**Was the batch's own work correct?** Where it was checked against a document,
yes and completely: `U-DAC`'s order code, `D-REVSHUNT`'s package, the
`C-KEY`/`R-KEY-SER` rewrite, the `PANEL` row's refusal to restate the budget,
and `R-LED-PD` as a new `open` row are all correct and all landed everywhere
they are read. The pattern in what failed is uniform and is the project's named
failure: **the batch moved rows and corrected fields, and did not follow the
moves into the documents that describe the result.** Three files describe a BOM
with 138 rows and 34 unplaced; two rows were relocated onto pages that
contradict them; and the naming standard the batch established on
`D-CLAMP-BREATH` was applied to `D-CLAMP-BREATH`.

## Provenance of this report

`[repo]` paths and line numbers are from the working tree at the time of
writing (`hardware/bom.csv` = 139 rows, 131,725 bytes). `[datasheet]` claims
are from files in `datasheets/`, read with `pymupdf` 1.28.2, page numbers as
the PDF paginates. `[calc]` arithmetic is shown inline. `[test]` claims are
from scripts written for this slice — an independent fragment concatenator and
byte comparator, a refdes-vs-page-text scanner, a row/unit recount, and
`git log`/`git show` over `0e68f25~1..HEAD`. No `docs/review/**` file other
than this wave's `README.md` was read.

**What would settle the uncertain findings.** 4b needs a decision, not a
lookup: whichever of 47 µF and 100 µF is right, the other is wrong in the same
repository. 4c needs the response shaper declared fitted or not, after which
three rows and one figure fall out. 1a is settled by the table quoted; 1b and
1c are settled by the banked datasheets quoted. 4d needs one distributor query
that four waves have not been able to make — and until it can be made,
`C-GATE-LOADSW` should not be `selected`.
