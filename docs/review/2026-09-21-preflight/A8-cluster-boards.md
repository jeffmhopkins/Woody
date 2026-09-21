# A8 — Key cluster boards, cold review

**Date:** 2026-09-21. **Slice:** `hardware/controller/cluster-boards.md`,
`docs/decisions/0001-mcu-and-board-partitioning.md`,
`docs/decisions/0010-key-layout-as-data.md`, `config/key-layout.yaml`.

**Cold:** no file under `docs/review/**` was opened. Everything below is from the
design corpus and from the 75 banked documents under `datasheets/`.

**Provenance marks:** `[datasheet <doc> p.N]` a banked document read this
session; `[repo file]`; `[calc]` with the arithmetic shown; `[from memory]`.
Anything unmarked is a defect in this report.

**Documents actually opened this session** (all by text extraction with
PyMuPDF, page numbers are PDF page indices):

| file | what it is |
|---|---|
| `datasheets/other-semi/74HC165-onsemi.pdf` | onsemi MC74HC165A/D Rev. 13, April 2025, 16 pp |
| `datasheets/other-semi/74HC165.pdf` | TI SN54/74HC165 SCLS116E, rev. Sep 2003, 22 pp |
| `datasheets/other-semi/74HC165-nexperia.pdf` | Nexperia 74HC165/74HCT165 Rev. 8, 9 May 2025, 20 pp |
| `datasheets/other-semi/74HC165-toshiba.pdf` | Toshiba TC74HC165P/F, 1986 databook excerpt (OCR) |
| `datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` | KS-33H10B050NN-Y24 Version 2, drafted 2023-01-03, 6 pp |
| `datasheets/other-semi/WS2815.pdf` | WS2815 V1.1, 8 pp |
| `datasheets/discrete-and-power/MF-PSMF010X-polyfuse.pdf` | Bourns MF-PSMF series, Rev. O 05/17, 5 pp |
| `datasheets/connectors/WR-BHD-61201621621.pdf` | Würth WR-BHD male box header |
| `datasheets/connectors/3M-303-SERIES-BOXED-HEADER.pdf` | 3M TS-0818-D, 303 series |

---

## §0 Findings, node-indexed

Severity: **B** blocks a board or a plate; **C** correctness; **S** staleness;
**N** noted, no action forced.

| # | Node / ref | Severity | Finding |
|---|---|---|---|
| 1 | `key-release-time`, `key-press-time` | N | **Both values and both derivations verified exactly.** 119.894 µs and 5.9167 µs. `threshold_note` is correct. All four vendors agree digit for digit at every shared rail. §1. |
| 2 | `key-release-time` / `key-press-time` | N | **New and stronger than the register claims:** both crossing times are *exactly ratiometric in VCC* and are the same number at any rail. The 3.3 V in the derivation is decorative. §1.4. |
| 3 | `U-KEYS` AC | C | onsemi publishes a **complete 3.0 V column for AC and timing too**, not only VIH/VIL. Every `[from memory]` timing claim on the page (`tens of nanoseconds`, `~0.5 ns skew`, `slow edges`) is now a datasheet number. §4. |
| 4 | `U-KEYS` t_PD min | C | **No vendor specifies a minimum propagation delay.** The chain's hold margin rests on an unspecified parameter. It is not at risk, but it must be recorded as an assumption, not a derived margin. §4.3. |
| 5 | `C-KEY` pole | C | The **1.54 kHz / 54 dB pole is the released-state figure only.** Pressed, the node is 2k2∥100 Ω and the pole is **35.4 kHz → 27.1 dB** at 800 kHz. Conclusion survives; the stated number is the optimistic state. §2.3. |
| 6 | `F-CHAIN` | B | **Fit it — as MF-PSMF010X in 0805.** The BOM's own objection computes the drop at the fuse's *hold rating*, not the *load*. The real drop is **26–226 mV**, and finding 2 makes the design immune to it. §3.3. |
| 7 | `F-CHAIN` | C | The row's stated threat is *"beside 12 V LED power"*. **A series PTC on the 3V3 feed cannot protect against a 12 V-onto-3V3 fault at all** — it protects only 3V3-to-GND. §3.4. |
| 8 | `F-CHAIN` | S | `bom.csv` says package `1206`. The datasheet body is **2.00–2.30 × 1.20–1.50 mm = 0805**, and the series designator literally means 0805. The row's own note already says so and the package field was not changed. |
| 9 | `PCB-CLUSTER` / `PLATE-TOP` | B | **`cluster-boards.md` §5 still calls plate thickness open and reasons from 1.5–2 mm.** It is settled at **1.20 mm**, `status: settled`, owner `ks33-geometry.md`. `config/key-layout.yaml` still carries `plate_thickness: null` with a comment about clips. §6.1. |
| 10 | `PCB-CLUSTER` standoff | B | **There IS a standoff and it is ~2.0 mm.** "Hard against the plate underside" was computed against a 1.5–2 mm plate. At 1.20 mm the gap is **2.00–2.40 mm**. §6.2. |
| 11 | `SW1-n` | B | **The vendor drawing publishes contact bounce: 5 ms max.** Both `ks33-geometry.md` ("not available anywhere, needs a scope, M1") and the debounce argument on this page predate it. The RC network absorbs it; **firmware's two-sample rule does not.** §2.5. |
| 12 | `SW1-n` | C | Vendor **minimum** ratings exist: **2 VDC min, 10 µA min**. This closes the wetting-current half of the 2k2-vs-10k trade with a number: both values pass. §2.4. |
| 13 | `R-KEY-PU` 2k2 vs 10k | C | The page prices the 10 k option at *"a 100 µs τ"*. **10 k × 47 nF gives τ = 470 µs and a 561 µs release** — 5.6× the stated cost and 2.2 scan periods. The real comparison is 2k2/47nF against **10k/10nF**, which gives the *same* 119 µs release at ¼ the current. §2.6. |
| 14 | ADR 0001 Consequences | S | **"six conductors leave each cluster"** is a live stale assertion. The settled figure is 12. The string is in `figures.yaml`'s `forbidden` list and the checker missed it **because the phrase wraps across a line break.** §8.1. |
| 15 | `tools/check-staleness.py` | B | The checker matches `bad in line`, line by line. **Any forbidden phrase that wraps is invisible to it.** Three wrapped hits exist today; one (#14) is live. §8.1. |
| 16 | marker pattern | N | **Verified exhaustively and independently.** The current pattern passes **0** of the 23 wrong permutations; the pre-flip repeating-nibble pattern passes exactly one, `RT → RH → LH → LT`; the −5 shift hole is real in the old pattern and gone in the new. §5.1. |
| 17 | marker pattern | S | The page says a mid-shift reload *"passes at 11 of 31 reload points."* **11 is the pre-flip number. The current pattern is 12 of 31.** The flip that killed the permutation hole made the reload hole one worse, and the adjacent number did not follow. §5.2. |
| 18 | free bits 22, 23, 31 | C | **Answer to open item 6: take the marker to 11, all three strapped LOW.** It cuts reload holes 12 → 8, keeps 0 permutation holes, and *removes* three resistors. Two of the eight possible level assignments are actively worse. §5.3. |
| 19 | `LK-SER` / `R-SER-TERM` | C | §1 says a chain reorder moves the §4 bit groups. **It also moves `LK-SER` position B, `R-SER-TERM`, and the 1-vs-2 `J-CHAIN` variant from `LH` to `LT`.** Not stated anywhere. §7.3. |
| 20 | ADR 0010 | C | Broken sentence in the design corpus: *"What is more than three."* — a truncated edit in the spare-bits paragraph. §8.3. |
| 21 | `carrier.md` §3 | S | *"Six conductors is the signal count… whether this connector is 6-way or 10-way is a decision this page cannot take alone"* and *"`F-CHAIN`… Proposed, not in the BOM."* Both decided; both still open on the page. |
| 22 | `carrier.md` §3 | S | *"the `H`…`A`-to-switch mapping inside each device is still open."* §4 of `cluster-boards.md` decides it. |
| 23 | `R-KEY-SER`, `C-KEY` rows | S | `bom.csv` `R-KEY-SER` describes the **superseded 10k/10nF** network in full (`~1us`, `~93us`). `C-KEY` carries `~5.7us`, `44x` and `~125us` against settled 5.92 / 42× / 119.9. Neither matches a `forbidden` string. §8.2. |
| 24 | `R-CHAIN-SER` | N | **100 Ω verified correct, and ADR 0001's deletion argument for `R-TERM-CHAIN` does not apply to it** — the resistor's own edge slowing is what makes the line lumped. §4.5. |
| 25 | `U-KEYS` part source | C | **Nexperia's 74HC165 inputs are overvoltage tolerant to 15 V; onsemi's and TI's are not.** In a body where 12 V LED power runs beside these conductors that is a survival property the corpus does not have. §4.6. |
| 26 | `U-KEYS` SH/LD | C | The page says the load happens *"on the falling edge of `SH/LD`"*. It is **level-sensitive while `SH/LD` is LOW and captured on the rising edge**. The numbers firmware needs — `t_w` 27/32 ns, `t_su` 30/40 ns, `t_rec` 30/40 ns — are written nowhere. §4.4. |

---

## §1 Key network timing — deliverable 1

### 1.1 The four vendors, at every rail each publishes

Read off the DC tables this session:

| Source | 2.0 V | 3.0 V | 4.5 V | 6.0 V |
|---|---|---|---|---|
| TI SCLS116E `[datasheet 74HC165.pdf p.4]` | 1.5 / 0.5 | *absent* | 3.15 / 1.35 | 4.2 / 1.8 |
| Nexperia Rev. 8, Table 6 `[datasheet 74HC165-nexperia.pdf p.6]` | 1.5 / 0.5 | *absent* | 3.15 / 1.35 | 4.2 / 1.8 |
| Toshiba TC74HC165 `[datasheet 74HC165-toshiba.pdf]` | 1.5 / 0.5 | *absent* | 3.15 / 1.35 | 4.2 / 1.8 |
| **onsemi MC74HC165A Rev. 13** `[datasheet 74HC165-onsemi.pdf p.4]` | 1.5 / 0.5 | **2.1 / 0.9** | 3.15 / 1.35 | 4.2 / 1.8 |

**The page's table is correct in every cell.** All four agree digit for digit at
every shared rail, at all three temperature bands. onsemi's 3.0 V row is
2.1 V / 0.9 V, which is exactly 0.70 / 0.30 × VCC, at −55…25 °C, ≤85 °C and
≤125 °C alike.

The Toshiba entry is an OCR of a 1986 scan and its VIL column does not extract
cleanly; its VIH MIN column reads 1.5 / 3.15 / 4.2 and there is no 3.0 V row.
Treat it as corroboration of the *shape*, not as a fourth independent digit.

**JESD8C is confirmed.** `[datasheet 74HC165-nexperia.pdf p.1]`, §2 Features:
*"Complies with JEDEC standards: JESD8C (2.7 V to 3.6 V), JESD7A (2.0 V to
6.0 V)."* JESD8C's CMOS input levels are 0.7 / 0.3 × VDD `[from memory]` — that
one link in the argument is still memory, not a banked document, and the page
should say so.

### 1.2 The derivations in `config/figures.yaml`, recomputed

`[calc]`, at VCC = 3.3 V, `R-KEY-PU` 2.2 kΩ, `R-KEY-SER` 100 Ω, `C-KEY` 47 nF:

```
V_IH = 0.70 x 3.3                          = 2.310 V
V_IL = 0.30 x 3.3                          = 0.990 V
pressed node  = 3.3 x 100/(2200+100)       = 0.143478 V
tau_release   = 2200 x 47n                 = 103.400 us
tau_press     = (2200||100) x 47n
              = 95.6522 x 47n              =   4.4957 us
release = -103.400 x ln((3.3-2.310)/(3.3-0.143478)) = 119.894 us
press   =   -4.4957 x ln((0.990-0.143478)/(3.3-0.143478)) = 5.9167 us
margin inside a 250 us scan = 250/5.9167   = 42.3x
```

**Both register values are correct as stated.** `119.9 us` and `5.92 us`.
`derivation:` on both entries is correct string for string, including the
`0.1435 V` pressed-node figure and the parallel-combination τ.

The TI-only pessimistic bound also checks out `[calc]`: at 0.75/0.25 × VCC,
release = 138.75 µs and press = 6.891 µs, giving 36.3× margin. Both
`conservative_bound:` fields are right.

### 1.3 The bracketing argument is sound, and one sentence overstates it

The page says interpolation between the 3.0 V and 4.5 V rows *"assum[es] no
ratio at all"* and that landing on 0.70/0.30 *"is what makes the bracketing
argument safe rather than lucky."*

`[calc]` Both bracketing rows lie exactly on the line `V = 0.70 × VCC` through
the origin. Linear interpolation between two points on one line through the
origin **must** land on that line — for any intermediate rail, not just 3.3 V.
So the agreement is a tautology, not an independent confirmation. The argument
is still correct and still safe; it is just that the *evidence* is the two
published rows themselves, not the interpolation between them. Recommend the
sentence be softened rather than removed.

### 1.4 The figure that matters more than either bound

`[calc]` Both crossing times are **exactly ratiometric in VCC**. Writing
`k = R_SER/(R_PU+R_SER) = 0.0434783`:

```
release: 0.70 = 1 - (1-k) e^(-t/tau)   ->  t = tau x ln((1-k)/0.30)   = tau x 1.159582
press:   0.30 = k + (1-k) e^(-t/tau)   ->  t = tau x ln((1-k)/(0.30-k)) = tau x 1.316418
```

VCC cancels. Evaluated numerically at 3.300, 3.075, 3.000 and 2.500 V, the
release is 119.894 µs and the press 5.9167 µs at every one of them, to the last
digit printed.

**Three consequences, none of which is anywhere in the corpus:**

- Any drop on the loom's 3V3 — `F-CHAIN`, connector resistance, the LDO under
  load — costs the key network **nothing**. That is the single most useful fact
  about this topology and it is what settles `F-CHAIN` in §3.
- The `0.1435 V` and `3.3 V` in the register's `derivation:` field are
  presentational. The figure would survive a rail change with no edit.
- It holds **only because `R-KEY-PU` returns to the same rail the register runs
  from.** If the pull-ups were ever taken to a separate or filtered 3V3, the
  cancellation breaks. Worth one line in the schematic notes, because it is the
  sort of thing a layout "improvement" removes silently.

### 1.5 The TI ground-bounce warning is quoted out of its scope

The page repeats TI's warning about *"double-clocking from induced ground
bounce"* as a general reason not to shave margin.

`[datasheet 74HC165.pdf p.4, footnote ‡]`, verbatim: *"If this device is used
in the threshold region (from VILmax = 0.5 V to VIHmin = 1.5 V), there is a
potential to go into the wrong state from induced grounding, causing double
clocking. Operating with the inputs at tt = 1000 ns and VCC = 2 V does not
damage the device; however, functionally, the CLK inputs are not ensured while
in the shift, count, or toggle operating modes."*

0.5 V and 1.5 V are the **2 V** rows. The warning is about 2 V operation with
1000 ns input transitions on **CLK**, not about key inputs at 3.3 V. The
underlying principle generalises; the citation does not. Mark it as a general
CMOS caution rather than as this datasheet's statement about this circuit.

---

## §2 Impedance and the network — deliverable 2

### 2.1 Pressed-node divider voltage

`[calc]` 3.3 × 100/2300 = **0.143478 V**, against `V_IL` = 0.990 V — a 0.847 V
margin, 6.9×. Correct as drawn and correctly *not* 0 V.

Released, the node sits at VCC minus the leakage drop: `[datasheet
74HC165-onsemi.pdf p.4]` `Iin` max ±0.1 µA at ≤25 °C and **±1.0 µA at ≤85 °C**
(specified at VCC = 6.0 V). `[calc]` 1 µA × 2.2 kΩ = **2.2 mV**, so the released
node is 3.298 V against `V_IH` 2.310 V. Leakage is irrelevant at 2k2 and still
irrelevant at 10 k (10.0 mV). **Input leakage does not decide the 2k2-vs-10k
question**, and nothing in the corpus should claim it does.

### 2.2 Time constants

Verified in §1.2. The **parallel** combination for the press, 4.4957 µs, is
correct and the `4.7 µs` correction recorded in `key-press-time`'s
`threshold_note` stands: with the switch closed the pull-up is still connected,
so the node sees 2k2∥100 Ω.

### 2.3 The pole — correct number, incomplete statement

`[calc]` Released: `f = 1/(2π × 2200 × 47n)` = **1539.2 Hz**; at 800 kHz,
`20·log10(800e3/1539.2)` = **54.3 dB**. Both figures as printed.

**But that is the released state only.** Pressed, the node resistance is
2k2∥100 = 95.65 Ω and `[calc]` `f = 35.40 kHz`, giving **27.1 dB** at 800 kHz —
27 dB less rejection, in the state where a false *release* would be the fault.

The conclusion survives with room to spare. ADR 0001's corrected aggressor is
1.36 V of swing on an unfiltered wire `[repo] 0001`; at 27.1 dB that is 61 mV
on a node sitting at 0.143 V, which must reach 2.310 V to read released. But
the page should state which state its 54 dB belongs to, because a reader
checking the worse case will not find it.

**800 kHz is itself the conservative choice**, and worth saying so.
`[datasheet WS2815.pdf p.1]`: *"Data transmitting at speeds of up to
800Kbps"*, and the PWM refresh is 2 kHz — so 800 kHz is the **bit rate**, not
the edge rate. The real aggressor spectrum runs to the edge knee, tens of MHz,
where the same pole gives `[calc]` 80.9 dB at a 17 MHz knee. Using the bit rate
understates the rejection by ~27 dB. Leave it; just do not let a later reviewer
"correct" it upward.

### 2.4 Contact resistance, and the vendor minimums nobody had

`[datasheet GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf p.6]`, sheet 6 Specification
block, verbatim:

```
1. Rating: 12VAC/DC Max. 2VDC Min. 10mA AC/DC Max, 10uA DC Min.
2. Contact Resistance: 200mOhm Max.
3. Insulation Resistance: 100MOhm Min (DC100V).
5. Bounce Time: 5msec Max. (at 16 in/sec. actuation speed).
```

and `[datasheet … p.1]` §4.2, contact resistance 200 mΩ max measured
contact-to-contact at 1 mA / 5 VDC. Contact material is **Au alloy**
`[datasheet … p.6, ITEM 6]`.

`[calc]` With the maximum 200 mΩ contact in series, the pressed node moves from
0.143478 V to 0.143750 V — **0.27 mV** — and the press crossing from 5.9167 µs
to 5.9291 µs, **+0.2 %**. **Contact resistance changes nothing.**

**What is new is the minimum.** The switch is specified down to 2 VDC and
10 µA. The open-circuit voltage across the contacts is 3.3 V and the closed
current is 1.435 mA `[calc]` — inside the window at both ends, and 143× the
minimum current. At 10 kΩ the closed current would be 327 µA, still 33× the
minimum. **So contact wetting does not decide 2k2 vs 10k either**, and now
there is a vendor number to say so with instead of folklore.

### 2.5 Bounce: the number exists now, and it changes a firmware rule

**5 ms max, at 16 in/s actuation.** `docs/reference/ks33-geometry.md` says
*"Contact bounce duration and the actuation/reset hysteresis gap… Gateron
publishes travel and force but neither of these… Milestone M1."* The banked
drawing publishes the first, and sheet 6's force–travel diagram marks the
**operating point** and **reset point**, which is the second. Both halves of
that paragraph are refuted by a document already in the repo.

`[calc]` What the RC network does with a 5 ms bounce train:

- On **closure**, the node falls through `V_IL` in 5.92 µs — the press asserts
  on the first contact.
- During a **bounce gap**, the node climbs with τ = 103.4 µs and does not reach
  `V_IH` until **119.9 µs**. So **any bounce gap shorter than 119.9 µs is
  invisible at the register input.**
- On **release**, the same 119.9 µs filter means the register only reads HIGH
  119.9 µs after the *last* bounce closure. The release side is genuinely
  debounced by construction for a train of any length.

So the asymmetric-debounce shape ADR 0001 wants is confirmed by the numbers,
and the hardware handles bounce gaps up to 119.9 µs.

**The firmware rule is the one that does not survive.** ADR 0001 specifies
*"two consecutive agreeing samples before a note-on… At the 4 kHz loop rate
that is 250 µs of added latency."* `[calc]` 250 µs is **1/20 of the worst-case
5 ms bounce window**. If any gap in the train exceeds 119.9 µs, the sequence is
note-on, then a false released reading, within the bounce window — and the
asymmetric debounce's whole point is that note-on is not filtered.

**Proposed, and it is a one-line firmware change:** after a confirmed state
change on a key, **lock that key's state for ≥ 5 ms — 20 loop periods at
4 kHz** — before accepting the opposite edge. 5 ms is the vendor's own
guaranteed maximum, so it is a specification rather than a guess. The cost is
5 ms of extra note-off latency in the worst case, against a 5 ms total budget
that ADR 0001 says note-off is filtered inside anyway, and no musician retriggers
a key at 200 Hz. This belongs in ADR 0001's *Two firmware rules the chain
depends on*, which currently has the number wrong by 20×.

### 2.6 `R-KEY-PU` 2k2 vs 10k — the page prices the alternative wrong

The page and `bom.csv` both frame this as 2k2 against 10 k *"at the price of a
100 µs τ in a humid cavity."*

`[calc]` **10 kΩ with the fitted 47 nF gives τ = 470 µs and a release crossing
of 561.2 µs** — not 100 µs. That is 2.2 scan periods, and it turns "release is
filtered and costs nothing musically" into a real note-off delay. The 100 µs in
that sentence is the **2k2** τ (103.4 µs), carried across into the wrong branch
of the comparison.

**The comparison that is actually available** `[calc]`:

| | 2k2 + 47 nF (fitted) | 10 k + 47 nF (as the page prices it) | 10 k + 10 nF |
|---|---|---|---|
| per closed key | 1.435 mA | 0.327 mA | 0.327 mA |
| 18 closed | **25.83 mA** | 5.88 mA | 5.88 mA |
| τ release | 103.4 µs | 470 µs | 100.0 µs |
| release crossing | **119.9 µs** | **561.2 µs** | **119.4 µs** |
| press crossing | 5.92 µs | 5.71 µs | **1.30 µs** |

**10 k + 10 nF gives the same release filter to within 0.5 µs, a quarter of the
current, and a 4.5× faster press.** It is also exactly the pair the design
started from and abandoned. The only thing 2k2/47nF buys over it is lower node
impedance in a humid cavity — and ADR 0001 has already refuted the coupling
argument that impedance was defending against, and §2.1 above shows leakage
does not reach it either.

**Not reopened here** — the page explicitly records it as a live trade and this
is a review, not a decision. But the trade cannot be judged on the numbers the
page states, because one of them is wrong by 5.6×, and the third column is
missing entirely. **Recommend the page carry all three columns.**

---

## §3 Current draw, the rail, and `F-CHAIN` — deliverable 3

### 3.1 The key networks

`[calc]` `3.3 / (2200 + 100)` = **1.4348 mA** per closed key. 18 closed =
**25.83 mA**. Both figures correct.

**The worst case is 21, not 18.** All 21 networked positions can be closed once
the three reserved spare switches are fitted — the networks are budgeted for
them and `bom.csv` buys them `[repo] bom.csv R-KEY-SER qty 21`. `[calc]`
21 × 1.4348 = **30.13 mA**. The three genuinely free bits carry a pull-up and
nothing else, so they contribute 0. **Design the rail to 30.1 mA, quote 25.8 mA
as the play-rate figure.**

### 3.2 The registers' own supply current, at the real clock rate

`[datasheet 74HC165-onsemi.pdf p.4]`: `ICC` max per package, `Vin = VCC or
GND`, `Iout = 0`, at VCC = 6.0 V: **4 µA** (−55…25 °C), **40 µA** (≤85 °C),
160 µA (≤125 °C). `CPD` = **40 pF** typ (Nexperia gives 35 pF `[datasheet
74HC165-nexperia.pdf p.9]`).

`[calc]` Dynamic, from the datasheet's own `PD = CPD·VCC²·f + ICC·VCC`:

```
per device, during the 1 MHz burst : 40p x 3.3 x 1e6      = 132 uA
averaged over 32 clocks / 250 us   : 40p x 3.3 x 128e3    =  16.9 uA
four devices, average              =  67.6 uA
four devices, peak during the burst = 528 uA
quiescent, four devices, <=85 C     = 160 uA
```

**Budget: 30.1 mA + 0.16 mA + 0.53 mA ≈ 30.8 mA worst case, ~26.0 mA at play
rate.** The page's "plus 4 × 74HC165 quiescent, negligible" is correct — the
registers are 2.5 % of the load even counting the switching term.

### 3.3 What the 3V3 rail can deliver down 265 mm of loom

`[calc]`, 28 AWG stranded ribbon at 0.214 Ω/m `[from memory]`, and IDC contact
resistance **20 mΩ max** `[datasheet WR-BHD-61201621621.pdf, Electrical
Properties]` — the Würth sheet is the only one of the two header datasheets
that publishes a contact resistance; 3M's gives only a 1 A current rating
`[datasheet 3M-303-SERIES-BOXED-HEADER.pdf]`:

```
3V3 conductor, carrier to the far board:
  wire   0.265 m x 0.214 ohm/m                = 0.0567 ohm
  8 IDC contact interfaces x 20 mohm          = 0.160  ohm
  total                                       = 0.217  ohm
  drop at 30.1 mA, all load lumped at the end = 6.5 mV
ground return, five conductors in parallel    = 0.043 ohm -> 1.3 mV
```

**The loom is not the constraint — it costs 8 mV round trip.** Both headers are
rated far above this current (Würth 3 A, 3M 1 A). Whether the *source* can
deliver 30 mA is a carrier question and `carrier.md` §2 already owns it (the
dev board's LDO is also the MCP3202's reference, costed at 3.2 LSB).

### 3.4 `F-CHAIN` — recommendation: **fit it**, as `MF-PSMF010X` in **0805**

`[datasheet MF-PSMF010X-polyfuse.pdf p.1]`, Electrical Characteristics:
Vmax 15 V, Imax 40 A, **Ihold 0.10 A**, **Itrip 0.30 A**, **R 1.0–7.5 Ω at
23 °C**, max time to trip 0.5 s at 1.5 A. Body 2.00–2.30 × 1.20–1.50 mm
`[datasheet … p.2]` — **0805**, as the `PSMF` series designator says
explicitly (*"PSMF = 0805 Surface Mount Component"*, p.3).

**The BOM's objection is arithmetic on the wrong current.** The row computes
*"at up to 100mA is 0.1 TO 0.75V OF DROP"* — that is the drop at the fuse's
**hold rating**, which this circuit never approaches. `[calc]` At the real load:

| | 25.8 mA (play) | 30.1 mA (all 21 closed) |
|---|---|---|
| R = 1.0 Ω | 26 mV | 30 mV |
| R = 7.5 Ω | 194 mV | **226 mV** |

**226 mV worst case, and §1.4 proves it costs nothing.** Key thresholds are
exactly ratiometric in VCC, so the crossing times are unchanged at 3.074 V.
The only level that does not track is `QH` returning to the MCU: `[datasheet
74HC165-onsemi.pdf p.4]` `VOH` ≥ VCC − 0.1 V at |Iout| ≤ 20 µA, so `[calc]`
2.97 V against an ESP32-S3 `V_IH` of 0.75 × 3.3 = 2.475 V `[from memory]` —
**0.50 V of margin, against 0.72 V unfused.** Acceptable.

**The derating is published and it is fine.** `[datasheet … p.1, Thermal
Derating Chart]` MF-PSMF010X `Ihold`: 0.10 A at 23 °C, **0.09 A at 40 °C,
0.08 A at 50 °C, 0.07 A at 60 °C**, 0.05 A at 85 °C. The cavity runs 10–20 K
above ambient `[repo] 0001`, so ~35–45 °C: `Ihold` ≈ 0.085–0.09 A against a
30.8 mA worst-case load — **2.8–3.0×**. Even at 60 °C it is 2.3×.

**Do not go up a size.** MF-PSMF020X halves the resistance (0.65–3.5 Ω) but
trips at **0.50 A**. The fuse has to trip *below* whatever the dev board's LDO
can deliver, or the LDO folds back first and the instrument browns out anyway —
which is the exact failure the fuse exists to prevent. `figures.yaml`'s
`matrix-led-current` entry derates that LDO to **~250–500 mA** `[repo]
figures.yaml`. 0.30 A is inside that; 0.50 A is not. **The 010X is the only
part in the series whose trip point is usable here, and its resistance is
affordable.** That is the whole answer.

**Two things to change in the row, though:**

1. **`package` is `1206` and the part is 0805.** The row's own note says so and
   the field was not updated. Two millimetres of board, unretrofittable, on a
   part the row itself calls unretrofittable.
2. **Restate the threat.** The row's justification is *"runs 265 mm through the
   body beside 12 V LED power; a short on it browns out the dev board LDO."* A
   series PTC on the 3V3 feed **cannot protect against 12 V landing on the 3V3
   net** — current then flows *into* the net from the LED rail, backfeeding the
   LDO, with the fuse on the wrong side. It protects only a 3V3-to-GND short,
   which is the less damaging of the two named faults. For the 12 V fault the
   corpus needs a **clamp at the cluster-board end** — a ~3.6 V SMD TVS on the
   3V3 conductor at the first cluster board, or an extra channel on
   `U-TVS-CHAIN`, which today covers the four signals and not the supply.
   `[datasheet 74HC165-onsemi.pdf p.3]` Maximum Ratings: `VIN` −0.5 to
   **VCC + 0.5 V**, `IIK` ±20 mA. 12 V on a 3.3 V part is destructive, not
   marginal.

---

## §4 Chain signal integrity — deliverable 4

### 4.1 The onsemi 3.0 V column settles far more than the threshold

This is the most useful finding in the slice. `[datasheet 74HC165-onsemi.pdf
p.4–5]` publishes a full **3.0 V column through the AC and timing tables**,
which no other vendor does. Every one of these is nearer 3.3 V than the 2.0 V
or 4.5 V figures the corpus would otherwise have to bracket with:

| Parameter | 3.0 V, ≤25 °C | 3.0 V, ≤85 °C | 3.0 V, ≤125 °C |
|---|---|---|---|
| `f_max`, 50 % duty | **18 MHz** | 17 MHz | 15 MHz |
| `t_PLH/t_PHL` CLK → `QH` | **52 ns** | 63 ns | 65 ns |
| `t_PLH/t_PHL` SH/LD → `QH` | 58 ns | 70 ns | 72 ns |
| `t_PLH/t_PHL` input `H` → `QH` | 52 ns | 63 ns | 65 ns |
| `t_TLH/t_THL` output transition | **27 ns** | 32 ns | 36 ns |
| `t_su` data → SH/LD | **30 ns** | 40 ns | 55 ns |
| `t_su` `SA` (serial in) → CLK | **30 ns** | 40 ns | 55 ns |
| `t_su` SH/LD → CLK | 30 ns | 40 ns | 55 ns |
| `t_h` CLK → `SA`, SH/LD → data | **5 ns** | 5 ns | 5 ns |
| `t_rec` CLK → CLK INH | 30 ns | 40 ns | 55 ns |
| `t_w` min pulse, CLK and SH/LD | **27 ns** | 32 ns | 36 ns |
| `C_in` | 10 pF max | | |

All are *maxima* except `t_h`, `t_w`, `t_rec` and `f_max`, which are minima.
Nexperia's Table 8 `[datasheet 74HC165-nexperia.pdf p.9]` independently gives
`t_h` = **5 ns min at every rail and every temperature band**, matching onsemi.

**Vendor inconsistency worth recording:** onsemi's Recommended Operating
Conditions `[… p.3]` gives input `tr, tf` max **600 ns** at VCC = 3.0 V, while
the Timing Requirements table `[… p.5]` gives **800 ns** at 3.0 V for the same
parameter. Use 600 ns. Nothing here comes close to either.

### 4.2 HC and not LVC — confirmed by a number, not an assertion

The whole per-cluster topology rests on *"HC's slow edges make 265 mm an
ordinary lumped load instead of a transmission line"* `[repo] 0001,
cluster-boards.md §1`. That has been an assertion in every document. It is now
measurable:

`[calc]` Electrical length of the loom, 265 mm of ribbon at ~0.6 c:

```
t_flight       = 0.265 / 1.8e8 = 1.47 ns
round trip     = 2.94 ns
```

`[calc]` Capacitive load, using `C_in` = 10 pF max, ~50 pF/m for 1.27 mm-pitch
ribbon against adjacent grounds `[from memory]`, ~1 pF per IDC contact
`[from memory]`:

| net | loads | total C | edge with 50 Ω source | with `R-CHAIN-SER` (150 Ω) |
|---|---|---|---|---|
| `SCK`, `SH/LD` | 4 devices + loom + 8 connectors | **~62 pF** | 6.8 ns | **20.5 ns** |
| `SER` | 1 device + full loom | ~32 pF | 3.5 ns | 10.6 ns |
| `QH`, one hop | 1 device + one ribbon | ~16 pF | 1.8 ns | 5.3 ns |

**The margin is 7× to 20× over the 2.94 ns round trip, and the HC output's own
transition time is 27 ns** `[datasheet 74HC165-onsemi.pdf p.4]` — 9× the round
trip, into the standard 50 pF test load, which is close to the real 62 pF.
**Lumped, by any rule of thumb, on every net.** HC is confirmed.

An LVC part at ~2–3 ns edges `[from memory]` would land at or below the round
trip and the loom would be a transmission line. The corpus's reasoning is
right; it now has the arithmetic.

**One number in ADR 0001 to fix:** *"the drive is ample into ~26 pF of loom at
1 MHz."* 26 pF is the loom and connectors alone; the four `C_in` at 10 pF each
are the larger half. **The real `SCK` load is ~62 pF.** It is still ample —
`[calc]` slewing 3.3 V in 100 ns into 62 pF needs 2.05 mA against the
datasheet's 2.4 mA spec at 3.0 V `[datasheet 74HC165-onsemi.pdf p.4]` — but the
stated figure is 2.4× low and the conclusion should not rest on it silently.

### 4.3 Setup and hold across four devices

**Setup, per hop.** Device N+1's `QH` must reach device N's `SA` before N's next
clock. `[calc]`, worst case over temperature:

```
T_clk >= t_PD(max) + t_su + skew
      =  63 ns     + 40 ns + 1.5 ns   = 104.5 ns  ->  9.57 MHz ceiling
at <=25 C: 52 + 30 + 1.5 = 83.5 ns    -> 11.98 MHz
```

**At 1 MHz the setup margin is 895 ns of a 1000 ns period — the chain could run
to 9.6 MHz on this budget.** `f_max` for the device itself is 17–18 MHz at
3.0 V, so the *device* is not the ceiling and neither is the timing: the hop
setup is, at 9.6 MHz.

**Hold, per hop — and this is where the design rests on an unspecified
parameter.** Both devices see the same `SCK` edge. Data flows toward the clock
source, so the *driving* device (further from the carrier) is clocked **later**
than the *receiving* one, and the skew adds to hold margin:

```
hold margin = t_PD(min) + skew - t_h
            = t_PD(min) + 1.5 ns - 5 ns
```

**`t_PD(min)` is not specified by any of the four vendors.** TI, onsemi and
Nexperia all give typ and max and leave the Min column as `-`
`[datasheet 74HC165-onsemi.pdf p.4; 74HC165-nexperia.pdf p.8; 74HC165.pdf]`.
Conventionally an HC contamination delay is roughly a third of the max, giving
~17 ns at 3.0 V `[from memory]`, which would leave 13.5 ns of margin. In
practice this is never the failure — but **it is an assumption, not a derived
margin, and the corpus currently presents it as the latter.** Record it that
way.

**This also confirms ADR 0001 fix 3 is doing exactly what it claims.** Ordering
the chain toward the clock source puts the skew on the right side of the hold
inequality. The ADR's honesty about magnitude (`~0.5 ns` against tens of ns) is
also confirmed — `[calc]` the real per-hop flight time is ~0.37 ns for a 66 mm
hop, and the whole-loom skew is 1.47 ns, against a 52–63 ns propagation delay.
**It is 2–3 % of the delay, as the ADR says. It is free, and it is not what
decides whether the chain works.**

**Hold at the MCU.** SPI mode 0 samples `MISO` on the rising `SCK` edge; the
HC165 shifts on the same edge and changes `QH` `t_PD` later. The MCU's `MISO`
hold requirement (a few ns `[from memory]`) is covered by the same unspecified
`t_PD(min)`. Same assumption, same conclusion.

### 4.4 Two firmware constraints nobody has written down

The page says *"On the falling edge of `SH/LD` the parallel inputs load."*
`[datasheet 74HC165-onsemi.pdf p.2, Function Table]`: the load is
**asynchronous and level-sensitive** while SH/LD is LOW — the page's own §1
note and ADR 0001's *"`SH/LD` is asynchronous and level-sensitive"* both say so,
and this sentence contradicts them. The data is **captured on the rising edge**,
which is what `t_su` (parallel data → SH/LD) times against.

So the driver has three numbers it must respect, none of which appears in any
document `[datasheet 74HC165-onsemi.pdf p.5, 3.0 V column, ≤85 °C]`:

```
SH/LD LOW pulse width       t_w   >= 32 ns
key data stable before SH/LD rises  t_su >= 40 ns   (always true: 250 us scan)
SH/LD rising to first SCK edge      t_rec >= 40 ns
```

At 240 MHz an ESP32-S3 GPIO write followed by an SPI transaction start clears
40 ns comfortably `[from memory]`, so this is a recorded constraint rather than
a problem — but it is the kind of thing a DMA-chained or RMT-driven
implementation gets wrong, and it costs one line to state.

### 4.5 `R-CHAIN-SER` 100 Ω ×3 — correct, and for the reason the BOM gives

ADR 0001 fix 4 **deleted** 33–68 Ω series termination because *"series
termination is a point-to-point technique and these lines drop on four boards,
where intermediate receivers sit at the incident half-step; at 68 Ω that step
can land at 1.96 V against a 2.0 V threshold."* `R-CHAIN-SER` is 100 Ω on the
same two nets. At first reading that is the deleted part coming back **worse** —
`[calc]` the incident step at a 105 Ω line with a 150 Ω total source would be
105/(105+150) × 3.3 = **1.36 V**.

**It is not, and the BOM row's distinction is the right one** `[repo] bom.csv
R-CHAIN-SER`: *"Edge-rate damping at the source, which is a DIFFERENT job from
the R-TERM-CHAIN that ADR 0001 deleted."*

`[calc]` The incident-step analysis only applies if the net is a transmission
line. With 100 Ω in series the driven edge becomes **20.5 ns** into the 62 pF
lumped load (§4.2), which is **7× the 2.94 ns round trip**. The resistor's own
slowing is what removes the regime in which its half-step would matter. All
four receivers then see one monotonic RC ramp, not a staircase. Verified in the
other direction too: 20.5 ns is 4 % of a 500 ns half-period at 1 MHz and is
nowhere near the 600 ns input `tr/tf` limit `[datasheet 74HC165-onsemi.pdf
p.3]`.

**100 Ω is right on all three nets.** On `SER` — which *is* point-to-point and
therefore the one net where true series termination applies — 100 Ω plus a
~40 Ω pad `[from memory]` slightly overdamps a ~105 Ω ribbon, which is the safe
side: no overshoot, and the receiver settles after one 2.94 ns round trip.

**`QH` correctly has no series resistor, and the page should say why.** It is
driven by the HC165, not the MCU: `[datasheet 74HC165-onsemi.pdf p.4]` `VOL`
0.26 V at 2.4 mA gives an output impedance of `[calc]` ~108 Ω, already matched
to the ribbon. The output is self-damping, and adding 100 Ω would eat `VOH`
margin at the MCU for nothing. `R-CHAIN-SER` qty **3** is correct, not 4.

### 4.6 A part-selection criterion the corpus does not have

`[datasheet 74HC165-nexperia.pdf p.1]`, §1 General description, verbatim:
*"Inputs are overvoltage tolerant to 15 V. This enables the device to be used
in HIGH-to-LOW level shifting applications."*

onsemi and TI have no such property — `[datasheet 74HC165-onsemi.pdf p.3]`
Maximum Ratings gives `VIN` −0.5 to VCC + 0.5 V.

**In a body where 12 V LED power runs beside these conductors, a 15 V-tolerant
input is the difference between a fault that is repairable and one that is
not.** Nexperia's own Table 5 still gives a *recommended* input range of 0 to
VCC `[… p.6]`, and Table 4's `IIK` row is written generically for
`VI > VCC + 0.5 V` `[… p.5]`, so the claim is about **survival**, not about
specified operation with `VI` above the rail. Treat it as such.

**Recommend `U-KEYS` name the Nexperia 74HC165D specifically**, rather than
`manufacturer: multiple`. All four are pin-identical and agree at every shared
rail, so nothing else in the design changes — but only one of them survives the
fault the loom makes possible. Note the tension this creates with §1: the
**threshold** case rests on onsemi's 3.0 V row, which Nexperia does not print.
That is fine — the 3.0 V row is the *family's* JEDEC row, not one vendor's
silicon, and Nexperia's own JESD8C claim covers 2.7–3.6 V. But it should be
stated, because "we cite onsemi and fit Nexperia" will look like a defect to
the next reviewer if the reason is not written down.

---

## §5 The 32 bits — verification of §4 of the page

### 5.1 The marker pattern, solved exhaustively and independently

I rebuilt the constraint problem from scratch, without reading the falsification
agent's work (it is under `docs/review/`, which this review may not open).

Model `[calc]`: bit order within a device is `H G F E D C B A`, so offsets 0–7.
Each device's eight offsets carry keys (free variables, 0 or 1), unfitted
spare-switch positions (pulled high), hard straps, or pulled free bits. A
permutation passes undetected if **some** key state satisfies all eight marker
checks.

```
RT  offs 0-2 keys, 3-5 spare-switch (pulled 1), 6 = 1, 7 = 0
RH  offs 0-5 keys,                              6 = 0, 7 = 1
LT  offs 0-3 keys, 4 = 0, 5 = 1, 6-7 free (pulled 1)
LH  offs 0-4 keys, 5 = 0, 6 = 1, 7   free (pulled 1)
```

Results:

| pattern | undetected wrong permutations of 23 | rotation holes of 31 | mid-shift reload holes of 31 |
|---|---|---|---|
| **current**, `1 0 · 0 1 · 0 1 · 0 1` | **0** | 5 | **12** |
| pre-flip, `1 0 · 0 1 · 1 0 · 0 1` | **1 — `RT → RH → LH → LT`** | 7 (including −5) | 11 |

**The page's central claim is confirmed exactly.** Of the 23 wrong
permutations, the repeating-nibble pattern passes precisely one, and it is
`RT → RH → LH → LT` — the very reorder §1 of the same page proposes. The flip
kills it, and kills the −5 shift hole (rotation 27) with it. Two proposals made
hours apart, each sound alone and jointly blind: that finding stands, verified
by an independent solve.

**It also survives fitting the spares.** I re-ran the permutation search with
the three reserved spare-switch positions treated as free variables rather than
pulled high, in case a later retrofit reopens a hole. Still **0**.

### 5.2 One number did not follow the flip

The page states, under *What the marker still cannot see*: *"A mid-shift
`SH/LD` reload passes at 11 of 31 reload points."*

`[calc]` Modelling a reload at clock `r` as the received word
`W[0:r] + W[0:32−r]` (keys unchanged across the reload):

```
pre-flip pattern  : 11 of 31   at r = 5, 12, 19, 20, 21, 22, 27, 28, 29, 30, 31
current pattern   : 12 of 31   at r = 12, 13, 18, 19, 20, 21, 22, 27, 28, 29, 30, 31
```

**11 is the pre-flip figure. The current pattern is 12.** The flip that closed
the permutation hole opened one more reload hole, and the sentence that prices
the marker's blind spots did not move with it. This is exactly the defect class
`CLAUDE.md` names: the fix landed where the editing was, not where the reader
looks. It is one bit of severity, and it is in the paragraph whose entire job is
to be honest about what the marker misses.

The other two numbers in that paragraph are right `[calc]`: a single-bit flip is
caught 8 times in 32, and 32/8 = 4× undercount.

*Caveat on the model:* the page does not state how it counts reload points, and
a different convention would give a different absolute number. What is not
model-dependent is that **the flip changed this count**, and the page asserts an
unqualified figure.

### 5.3 Open item 6 — **take the marker to 11, all three straps LOW**

The page leaves this *"at 8/3 rather than drifting"*, with the argument
unresolved. It resolves cleanly once it is computed rather than argued.

`[calc]` Strapping `left_thumb` `B` (22) and `A` (23) and `left_hand` `A` (31)
and having firmware check them, over all eight possible level assignments:

| levels `LT.B, LT.A, LH.A` | undetected perms | rotation holes | reload holes |
|---|---|---|---|
| — (today, pulled, unchecked) | 0 | 5 | **12** |
| **`0, 0, 0`** | **0** | **5** | **8** |
| `1, 0, 0` | 0 | 5 | 8 |
| `0, 0, 1` / `1, 0, 1` / `1, 1, 0` | 0 | 5 | 10 |
| `1, 1, 1` | 0 | 5 | 12 |
| `0, 1, 1` | **1** | 4 | 10 |
| `0, 1, 0` | **1** | 5 | 8 |

**Recommendation: strap all three to GND.** Reload holes fall 12 → 8, a third
fewer blind spots on the highest-blast-radius fault in the chain (ADR 0001's own
framing: a `SH/LD` glitch corrupts all 32 bits). Permutation coverage stays
perfect.

**It costs less than nothing.** The three free bits currently each carry an
`R-KEY-PU`; a strap needs no part. `[repo] figures.yaml key-pullup-qty` would
go **24 → 21**, back to one per switch position, and `bom.csv` loses three
placements.

**And it closes the last surviving instance of a refuted argument.** The reason
the free bits get a pull-up rather than a strap is *"a pulled bit can still be
jumpered at bring-up"*. The page's own case for taking the marker from 6 to 8 is
that a free bit has no plate cutout and the body bonds shut, so it can never
become an input. That argument applies to these three unchanged, and the page
says so. The pull-ups are the place where it was not applied.

**Note the two traps.** `0, 1, 1` and `0, 1, 0` — i.e. strapping `LT.A` high —
reopen a permutation hole. The levels are not free choices, and "one high one
low per device for symmetry" would pick a worse pattern than all-low. This is
why the recommendation carries the levels and not just the count.

**Three tracked figures move together if this is taken**, and the three-step
procedure in `CLAUDE.md` applies to each: `marker-bits` 8 → 11, `free-bits`
3 → 0, `key-pullup-qty` 24 → 21. `key-layout.yaml`'s `spare_bits_marker` /
`spare_bits_free` and ADR 0001's *"8 of them carry the marker pattern and 3 stay
free"* follow. **If it is not taken, it should be closed explicitly rather than
left open a fourth time** — this open item has now survived three waves.

### 5.4 The marker straps themselves

`[datasheet 74HC165-onsemi.pdf p.3, Note 3]`, verbatim: *"Unused inputs must
always be tied to an appropriate logic voltage level (e.g., either GND or VCC).
Unused outputs must be left open."*

**Both halves of the page's §1 and §4 are directly vendor-backed:** strapping
marker inputs to the rails with no resistor and no cap is the manufacturer's own
instruction, and `QH_bar` (pin 7) being left open is too. The page's *"16 parts
saved"* argument is correct and does not need to rest on cost alone.

---

## §6 Mechanical, with the numbers that now exist — deliverable 6

### 6.1 Plate thickness is settled and this page does not know

`[repo] config/figures.yaml`: `plate-thickness`, value **1.20 mm**,
`status: settled`, owner `docs/reference/ks33-geometry.md`, derived from sheet 6
of the banked vendor drawing (slot 1.20 ±0.05 mm). `bom.csv` `PLATE-TOP` and
`PLATE-THUMB` both read `1.20mm aluminium`, both `status: selected`.

**`cluster-boards.md` §5, third bullet:** *"Plate thickness is still open and
blocks M4/M5… MX standard is 1.5 mm and the reference KS-33 build used 1.1 mm.
This board does not decide it but it is fitted around the answer."* **Stale.**

**`cluster-boards.md` Still open:** *"Plate-to-PCB standoff, and plate thickness
(§5). Both come from Gateron's drawing; the second blocks M4/M5 already."*
**Stale — both come from a drawing that is banked.**

**`config/key-layout.yaml`, `meta.plate_thickness`:** still `null`, with
*"OPEN, and it blocks M4/M5. 2 mm defeats the retention clips entirely; MX
standard is 1.5 mm; the reference KS-33 build uses 1.1 mm. Needs the clip
dimension from Gateron's drawing (ADR 0002)."* **Stale, and this is the file the
plate DXF is generated from.** It is the single highest-severity item in the
slice: the DXF generator reads `null` and the answer is sitting in
`figures.yaml` four directories away.

None of the three is caught by `tools/check-staleness.py`, because
`plate-thickness`'s `forbidden` list targets the specific phrasings that existed
when it was written and these are different sentences. The entry's own
`false_positive_note` explains why it has to work that way.

### 6.2 The standoff — **~2.0 mm, and it is not zero**

`[repo] docs/reference/ks33-geometry.md`, Z stack measured off
`GATERON-KS-33-3D.step` and confirmed by the vendor drawing: datum z = 0 at the
underside of the 15 × 15 mm collar; through-cutout section **2.50 mm** deep;
pin blades narrow from −3.2 mm to tips at **−5.10 mm**; centre pole ⌀5.05 reaching
**−5.75 mm** per the drawing.

For the blade to fill the hole, the PCB top cannot be *shallower* than −3.20 mm
(above that the pin root is 2.0 × 0.45 mm and will not pass a ⌀1.2 hole). For
the pin to protrude, the PCB bottom must be above −5.10 mm.

`[calc]`, plate underside at −(plate thickness):

| plate | standoff, plate underside to PCB top |
|---|---|
| 2.00 mm (ruled out) | 1.20 – 1.60 mm |
| 1.50 mm (ruled out) | 1.70 – 2.10 mm |
| **1.20 mm (settled)** | **2.00 – 2.40 mm** |

**The page's conclusion — *"there is no standoff… there is no plate-facing
side… put every passive on the far face"* — was computed against 1.5–2 mm and
does not survive 1.20 mm.** There is **2.00 mm** of clearance at the tightest
usable board position, and it can only grow.

`[calc]` Protrusion and pole clearance, PCB top at −3.20 mm:

| PCB | pin protrusion below the board | centre pole below the board |
|---|---|---|
| 1.6 mm (as `PCB-CLUSTER` specifies) | **0.30 mm** | 0.95 mm |
| 1.2 mm | 0.70 mm | 1.35 mm |
| 1.0 mm | 0.90 mm | 1.55 mm |

**Proposed, and it is a board-order decision: specify `PCB-CLUSTER` at 1.2 mm.**
At 1.6 mm the pin protrudes 0.30 mm, which is a visible-fillet joint but leaves
no room for stack-up tolerance or a slightly proud plate; at 1.2 mm it is
0.70 mm, a normal through-hole joint. `bom.csv` currently says `small, 1.6mm`
`[repo]`. The carrier is 1.6 mm and has no such constraint; these four do.

**The `~2 mm` centre-pole protrusion is also wrong.** The page and
`ks33-geometry.md` both say the pole *"protrudes ~2 mm below the PCB"*.
`[calc]` At the correct board position it is **0.95 mm** with a 1.6 mm board and
1.35 mm with a 1.2 mm board. The ⌀5.25 mm clearance hole through the plate
*and* the board is still required — only the depth behind it changes.

### 6.3 What 2.0 mm of standoff forbids on the plate-facing side

With ~2.00 mm nominal, minus assembly tolerance and plate flatness, budget
**≤1.5 mm maximum component height** on the plate-facing face. `[from memory]`
for the package heights:

| | max height | verdict |
|---|---|---|
| 0805 / 0603 chip passives (`R-KEY-PU`, `R-KEY-SER`, `C-KEY`, `C-DECOUPLE-165`, `R-SER-TERM`, `F-CHAIN`) | ~0.60 mm incl. solder | **permitted** |
| `LK-SER` solder-link pads | flat copper | **permitted** |
| SOIC-16 (`U-KEYS`) | 1.75 mm body + solder | **forbidden** |
| `J-CHAIN` 2×6 boxed header | **9.10 ±0.15 mm** `[datasheet WR-BHD-61201621621.pdf]` / 9.3 ±0.25 mm `[datasheet 3M-303-SERIES-BOXED-HEADER.pdf]` | **forbidden, by 4.5×** |

**So the rule changes from "there is no plate-facing side" to a specific and
much more workable one, and this is the deliverable:**

> **All chip passives may sit on the plate-facing face.** `U-KEYS`, `J-CHAIN`
> and anything else over 1.5 mm go on the far face. The plate is grounded
> through `MECH-GNDBOND` `[repo] carrier.md §1, 0009`, so keep a copper
> keep-out and no exposed via annuli or test pads on the plate-facing face, and
> mask the pads: 2.00 mm is clearance, not insulation.

That matters for layout. The page's §5 currently forbids *all* plate-facing
placement, which on a small board carrying six pull-ups, up to six series
resistors and up to six caps around a SOIC-16 and one or two 2×6 headers is a
real area constraint — and it is not necessary.

Retain the ⌀5.25 mm centre-pole clearance hole per switch through both plate and
board, and the 14.00 +0.05/−0.02 mm cutout `[repo] ks33-geometry.md`.

### 6.4 The switch's own environment limits, since the cavity is breathed into

`[datasheet GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf p.1]` §1.2–1.3: operating
temperature **−40 to +80 °C**; operating relative humidity **≤85 % RH at
+40 °C**. Moisture-resistance test is 40 °C / 90–95 % RH for 96 h `[… p.3 §7.3]`.

The corpus describes a cavity *"breathed into for hours at 10–20 K above
ambient"* `[repo] 0001`. **A closed cavity with a human exhaling into it will
exceed 85 % RH**, which is the switch's stated operating limit, not a test
condition. That is a live question for the open *Conformal coating* item — and
`ADR 0009` should own it, because it is about the cavity, not about this board.
Insulation resistance is 100 MΩ min `[… p.1 §4.1]`, so `[calc]` even at that
limit a 2k2 pull-up sees 3.3 × 2200/100e6 = 73 µV of leakage-driven offset.
The switch is not the leakage path; board contamination would be.

---

## §7 Netlist readiness — deliverable 7

### 7.1 Counts reconcile

`[calc]` against `key-layout.yaml` and the §4 allocation:

| board | switches | spare-switch | marker | free | `R-KEY-PU` | `R-KEY-SER` / `C-KEY` | `J-CHAIN` |
|---|---|---|---|---|---|---|---|
| `right_thumb` | 3 | 3 | 2 | 0 | 6 | 6 | 2 |
| `right_hand` | 6 | 0 | 2 | 0 | 6 | 6 | 2 |
| `left_thumb` | 4 | 0 | 2 | 2 | 6 | 4 | 2 |
| `left_hand` | 5 | 0 | 2 | 1 | 6 | 5 | 1 |
| **total** | **18** | **3** | **8** | **3** | **24** | **21** | **7 (+1 carrier = 8)** |

All four rows sum correctly and every total matches its tracked figure:
`marker-bits` 8, `free-bits` 3, `key-pullup-qty` 24, `chain-connectors` 8.
`bom.csv` `R-KEY-SER` and `C-KEY` at qty 21 match. **The component table is
arithmetically clean.**

### 7.2 Proposed canonical net names — one schematic, four variants

Nothing below is in the corpus; the page names bits by key id (`RT1`, `LH5`),
which cannot be a net name on a schematic that is instantiated four times.

| net | connects | note |
|---|---|---|
| `CHAIN_SCK` | J-IN 2 — U-KEYS 2 — J-OUT 2 | straight bus |
| `CHAIN_LOAD` | J-IN 4 — U-KEYS 1 — J-OUT 4 | straight bus (`SH/LD`) |
| `CHAIN_3V3` | J-IN 10 — U-KEYS 16 — J-OUT 10 — all `R-KEY-PU` — `C-DECOUPLE-165` | one name; **must be the same net the pull-ups return to** (§1.4) |
| `GND` | J-IN 1/3/5/7/9 — J-OUT same — U-KEYS 8 — **U-KEYS 15** — `C-KEY` ×n — low marker straps | tie `CLK INH` **directly** to `GND`, do not give it a net of its own, so ERC cannot leave it floating |
| `QH_OUT` | U-KEYS 9 → J-IN 8 | toward the carrier |
| `QH_IN` | J-OUT 8 → `LK-SER` pad A | from the next board; **absent on the chain-end board** |
| `SER_THRU` | J-IN 6 — J-OUT 6 — `LK-SER` pad B | pass-through on every board *and* tapped to pad B; three connections, one net |
| `SER_DEV` | `LK-SER` common → U-KEYS 10 | |
| `KIN_H` … `KIN_A` | U-KEYS 6,5,4,3,14,13,12,11 | **position-named, not key-named** |
| `SW_H` … `SW_A` | `R-KEY-SER` → switch pin 1 | only where a switch or spare-switch position is fitted |
| *(none)* | U-KEYS 7 `QH_bar` | explicit DNC flag; datasheet says leave open `[datasheet 74HC165-onsemi.pdf p.3 Note 3]` |

The variant table then maps `KIN_H`…`KIN_A` per board to a key id, a marker
level, or free — which is exactly the four-row table in §4 of the page, read as
a netlist input rather than as prose.

### 7.3 Ambiguities to resolve before the boards are drawn

1. **`J-CHAIN` needs two refdes, not one.** `bom.csv` carries a single
   `J-CHAIN` row at qty 8; that is a purchase count. Propose `J-CHAIN-IN` and
   `J-CHAIN-OUT`. The checker's refdes pass accepts both, since it allows any
   token starting with a BOM refdes plus `-`.
2. **`SW1-n` collides across four boards.** Propose `SW-LH1…5`, `SW-LT1…4`,
   `SW-RH1…6`, `SW-RT1…3`, plus three named spare-switch positions. As drawn,
   four boards each have an `SW1`.
3. **A chain reorder moves more than the bit groups — this is not stated
   anywhere.** §1 proposes `RT → RH → LH → LT` and says *"`left_thumb` and
   `left_hand` swap their eight-bit groups."* It also swaps, in the same
   instant:
   - `LK-SER` position **B** moves from `LH` to `LT`;
   - `R-SER-TERM` (qty 1, chain-end board only) moves from `LH` to `LT`;
   - the `J-CHAIN` variant flips: `LT` goes 2 → 1 and `LH` goes 1 → 2;
   - the component table's `LH`/`LT` columns swap for `LK-SER` and
     `R-SER-TERM`.

   `[calc]` I re-solved the marker under the reordered chain: it still catches
   **all 23** wrong permutations, so the reorder is safe on that axis — but the
   rotation holes go **5 → 7**. A second small argument against, to sit beside
   the saved body crossing.
4. **The three spare-switch positions are allocated to `right_thumb` in §4 but
   their placement is an M2 decision** — and placement decides *which board*.
   If they land anywhere but the right thumb cluster, §4's table, the
   `R-KEY-SER`/`C-KEY` per-board columns and the plate that gets the cutouts all
   move. Below.
5. **`R-SER-TERM` at 10 kΩ is a fifth resistor value on a board that otherwise
   uses two.** `[calc]` 2k2 would also work: driven low through the carrier's
   100 Ω it gives 3.3 × 100/2300 = 143 mV against `V_IL` 0.990 V, still 6.9× of
   margin, and it saves a BOM line. 10 kΩ is the better engineering choice —
   `[calc]` 32.7 mV driven, 0.327 mA standby instead of 1.43 mA — and the page's
   *"within 33 mV of the rail"* is exactly right. **Keep 10 kΩ; record that the
   value is deliberate, not inherited**, or someone will consolidate it.

---

## §8 The eight open items, answered — deliverable 5

Ordered as the brief asks: what blocks a board first.

### 8.1 Where the three reserved spare-switch positions go — **BLOCKS A BOARD AND A PLATE**

**Confirm `right_thumb`, and say so as a decision rather than a proposal.**

The page's reasoning is right and the corpus supports every step: RT's three
fitted keys are the only `role: control` inputs `[repo] key-layout.yaml`, the
three spares are octave up / octave down / hold-preset, which are control
functions, and RT has exactly three unallocated positions (`E`, `D`, `C` =
bits 3, 4, 5). **No other cluster has three spare positions at all** once the
marker takes two from each: `RH` has none, `LT` has two, `LH` has one. So the
allocation is forced, not chosen — RT is the only board that can carry all three
without splitting them across clusters or displacing a marker bit.

If they *were* split, the §4 table, the `R-KEY-SER`/`C-KEY` per-board columns
and the plate cutouts all move. **That is the argument for deciding it now:
placement on the plate is an M2 ergonomics question, but *which cluster owns the
bits* is not, and it is the half that blocks the board.** Recommend the page
separate the two and close the electrical half.

Consequence to record: all three cutouts land in **`PLATE-THUMB`**, on the
bottom face, with the four left-thumb and three right-thumb cutouts.

### 8.2 The free bits — **answered in §5.3: strap them, marker goes to 11**

### 8.3 `LK-SER` and `R-SER-TERM` — **fit both, as proposed**

Verified `[calc]`: with `LK-SER` in position B and `R-SER-TERM` 10 kΩ to 3V3, a
carrier driving `IO33` low through `R-CHAIN-SER` 100 Ω produces
3.3 × 100/10100 = **32.7 mV**, against `V_IL` 0.990 V. Driving high, no current
flows and the node is at the rail. Undriven — including at reset, when ESP32
GPIOs are inputs `[from memory]` — the 10 kΩ holds `SER` high, which is ADR
0001's tied-off case, and `[calc]` the ±1 µA input leakage droops it by 10 mV.
**All three states are correct and the self-test becomes a firmware choice for
one resistor.** The page's recommendation stands unmodified.

Two things to add to it:

- **`LK-SER` position is the one thing that makes the four boards one
  schematic**, and it therefore has to be a *fitted variant*, not a hand-cut
  trace. Specify it as a 3-pad link with pad A shorted by default in the
  fabrication drawing, or the chain-end board becomes a fifth variant by
  accident.
- **It moves with the chain order** (§7.3 item 3).

### 8.4 The chain order against the faces — **leave open, and here is what changed**

The page proposes `RT → RH → LH → LT` to save one body-thickness crossing, and
correctly makes it conditional on M3 geometry that does not exist.

Three inputs the page does not have:

- **The marker now catches it either way.** `[calc]` §5.1: the current pattern
  has zero permutation holes, so a *mis-wired* `RT → RH → LH → LT` is detected.
  The reorder is no longer a silent-failure risk; it is only a decision.
- **It costs two rotation holes**, 5 → 7 `[calc]` §7.3.
- **It moves `LK-SER`, `R-SER-TERM` and the `J-CHAIN` variant**, which the page
  does not say.

**Recommend: leave `RT → RH → LT → LH` as written until M3, and add the three
consequences above to the open item.** The skew argument is genuinely worth a
few percent of hold margin and nothing more — `[calc]` §4.3 confirms 1.47 ns of
whole-loom skew against a 52–63 ns propagation delay, which is 2–3 %, exactly as
ADR 0001 says.

### 8.5 The 74HC165 pin map and thresholds — **correctly closed, and confirmed**

`[datasheet 74HC165-nexperia.pdf p.4, Table 2]` and the p.3 package drawing,
checked pin by pin against the page's §1 ASCII, with `A…H` mapped to Nexperia's
`D0…D7`:

```
1 PL=SH/LD   2 CP=SCK   3 D4=E   4 D5=F   5 D6=G   6 D7=H
7 Q7bar=QH_bar   8 GND   9 Q7=QH   10 DS=SER
11 D0=A  12 D1=B  13 D2=C  14 D3=D  15 CE=CLK INH  16 VCC
```

**Every pin matches, and the `A…H` ↔ `D0…D7` mapping is correct too**, which
the page asserts implicitly by writing `E (D4)` and so on. `[datasheet
74HC165-onsemi.pdf p.2, Function Table]` confirms the bit order: on
asynchronous parallel load `QH = h`, so **`H` (D7, pin 6) is the first bit
out** and bit 0 is the `H` input of `right_thumb`. All correct.

The one thing to fix in that section is the *"falling edge of `SH/LD`"*
phrasing — §4.4.

### 8.6 `R-KEY-PU` 2k2 vs 10k — **leave open, but restate the cost**

See §2.6. The trade as the page prices it cannot be judged. The missing column
is 10 k + 10 nF, which gives the same 119 µs release at 5.88 mA. §2.1 and §2.4
remove two of the arguments that were quietly propping up 2k2 (leakage and
contact wetting — neither reaches it at either value).

### 8.7 Plate-to-PCB standoff and plate thickness — **both closed; see §6**

Standoff **2.00–2.40 mm**, plate **1.20 mm**. This item should be struck from
*Still open* and its consequences written into §5 — particularly that the
plate-facing face is usable for chip passives after all.

### 8.8 Whether `LT` takes lighter springs — **no electrical content, leave to M1**

`[datasheet GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf p.6]` the fitted Red is
50 ±15 gf operating force, 1.7 ±0.4 mm pre-travel, 3.0 ±0.2 mm total travel.
A lighter variant changes none of §1–§4. Agreed with the page.

One thing it *does* touch: **`SW-THUMB` is a different order code and therefore
potentially a different bounce spec.** If a lighter spring is taken, re-read
the bounce figure before fixing the firmware lockout of §2.5 — a weaker spring
generally bounces longer `[from memory]`.

### 8.9 Conformal coating — **the cavity humidity number now argues for it**

`[datasheet GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf p.1 §1.3]`: operating
humidity **≤85 % RH at +40 °C**. A sealed body exhaled into for hours will
exceed that. That is a switch-environment finding, not a coating finding — and
coating a soldered mechanical switch is still not obviously right, as the page
says. **Recommend: leave the coating decision to ADR 0009, but move the 85 % RH
number into it**, because it reframes the question from "is coating worth it"
to "what keeps the cavity below the switch's stated limit" — which may be a
vent or a desiccant rather than a coating.

---

## §9 Staleness found, and why the checker did not

### 9.1 The checker has a structural blind spot, and it is hiding a live defect

`tools/check-staleness.py` matches `if bad in line`, iterating `splitlines()`
`[repo] tools/check-staleness.py`. **Any forbidden phrase that wraps across a
Markdown line break is invisible to it**, and this corpus hard-wraps prose at
about 78 columns, so a two-to-four word phrase wraps roughly one time in ten.

`[calc]` Re-running the same forbidden list over whitespace-normalised whole
files rather than line by line finds **three** hits the line-based pass misses:

| figure | phrase | file | status |
|---|---|---|---|
| `chain-conductors` | `six conductors leave` | `docs/decisions/0001-…md:369` | **LIVE — no refutation wording** |
| `key-pullup-qty` | `21 pull-ups` | `hardware/controller/cluster-boards.md` | benign — *"carried a superseded count of"* |
| `spi-series-r` | `220 Ω with ~200 pF` | `docs/decisions/0004-…md` | benign — *"is refuted"* |

The live one reads, in ADR 0001's *Consequences*:

> *"…every switch-to-chip connection is a trace on the board the switch is
> already soldered to, and six conductors leave each cluster."*

The settled figure is **12** `[repo] figures.yaml chain-conductors`, owned by
this very ADR. The phrase is in that entry's `forbidden` list *specifically to
catch this*, and it survives only because the line break falls between
`conductors` and `leave`.

**Proposed fix, and it is four lines:** normalise whitespace across the whole
file before matching, and map the match offset back to a line number for the
report. The refutation test then runs against the surrounding sentence rather
than the surrounding line, which is also more correct — a refutation that wraps
is currently missed in the other direction too.

This is a **B**: the register's whole premise is that the checker makes this
class of defect impossible to forget, and there is a category it cannot see.

### 9.2 Three live stale rows in `bom.csv` that no `forbidden` string matches

- **`R-KEY-SER`**, whole note: *"With C-KEY: press is ~1us (100R x 10nF) so it
  stays instant, release is ~93us (10k x 10nF) which is a free hardware
  debounce."* **Describes the superseded 10k/10nF network in full.** Both
  `~93 us` variants are in `key-release-time`'s `forbidden` list; the row's
  phrasing (`release is ~93us`) matches neither, and there is no refutation
  wording anywhere in the row. Settled values are 5.92 µs and 119.9 µs.
- **`C-KEY`**: *"Press crosses HC165's VIL (0.99V at 3.3V) in ~5.7us… 44x
  margin against the 250us scan period. Release crosses VIH (2.31V) at ~125us."*
  Settled: **5.92 µs, 42×, 119.9 µs.** The forbidden strings are
  ``` `V_IL` at **5.7 ``` and ``` `V_IH` at **125 ```, which target the page's
  Markdown formatting, not the BOM's prose.
- **`R-KEY-PU`**: *"1.5mA per PRESSED key"* against the settled 1.43 mA. Minor,
  but it is the same figure the page and `carrier.md` both quote to three
  digits.

All three are the documented failure mode exactly: the fix landed on the page
where the editing was happening, and `bom.csv`'s prose — which is where a
purchaser actually reads — kept the old numbers.

### 9.3 A broken sentence in ADR 0010

`[repo] docs/decisions/0010-key-layout-as-data.md`, *Spare inputs are reserved
in the plate*:

> *"**Eight of the spare chain bits belong to the marker pattern** (decided
> 2026-09-21; this line said "four to six" until then) (ADR 0001) and are not
> available for switches. **Six remain** — three reserved spare-switch positions
> and three genuinely free. This line said "eight to ten" while the marker was
> four to six; both halves were corrected 2026-09-21. **What is more than
> three.**"*

The last sentence is a truncated edit. The arithmetic around it is right
(8 + 3 + 3 = 14, six remain), so this is a documentation defect rather than a
figure defect — but it is in an Accepted ADR in the design corpus.

Also in the same file: the parenthetical *"(decided 2026-09-21; …)"* and
*"(ADR 0001)"* are adjacent and read as a doubled citation.

### 9.4 `carrier.md` §3 carries two decisions as open

Both are in the design corpus and both were settled the same day:

- *"**Six conductors is the signal count, not the conductor count.** Whether
  this connector is 6-way or 10-way is a decision this page cannot take alone."*
  It is a 2×6 on 12 conductors, decided, and `chain-conductors` owns it.
- *"**`F-CHAIN`, or not.** … **Proposed, not in the BOM.**" It has a BOM row.
- *"the `H`…`A`-to-switch mapping inside each device is still open"* — §4 of
  `cluster-boards.md` gives it in full.

---

## §10 What I would change, in one list

Ordered by what blocks what. Nothing below has been applied; this review touched
only this file.

**Blocks a board or a plate:**

1. `config/key-layout.yaml` `meta.plate_thickness`: `null` → `1.20`, and delete
   the clip-dimension comment. **This is the file the DXF comes out of.**
2. `cluster-boards.md` §5 bullet 3 and *Still open*: strike the plate-thickness
   open item; it is settled at 1.20 mm.
3. `cluster-boards.md` §5 bullet 2: **standoff is 2.00–2.40 mm, not zero.**
   Replace *"put every passive on the far face"* with the height rule in §6.3.
   Correct the centre-pole protrusion from ~2 mm to 0.95 mm at 1.6 mm board.
4. `bom.csv` `PCB-CLUSTER` package: `small, 1.6mm` → **1.2 mm**, for pin
   protrusion (§6.2).
5. `bom.csv` `F-CHAIN` package: `1206` → **0805**. Fit the part; replace the
   drop objection with 26–226 mV at the real load; add the 12 V-fault caveat and
   a clamp.
6. Close open item 8.1: the three spare-switch bits are on `right_thumb` by
   arithmetic, not by preference. Cutouts in `PLATE-THUMB`.
7. Fix `tools/check-staleness.py` to match across line wraps (§9.1), then fix
   `docs/decisions/0001-…md:369` — `six conductors` → **12**.

**Correctness, before firmware is written:**

8. ADR 0001's firmware rules: the two-sample rule at 250 µs is 1/20 of the
   switch's **5 ms specified bounce**. Add a ≥5 ms per-key state lockout
   (§2.5).
9. `cluster-boards.md` §4: *"passes at 11 of 31 reload points"* → **12**, or
   state the model (§5.2).
10. `cluster-boards.md` §1: `SH/LD` load is level-sensitive and captured on the
    **rising** edge; add `t_w` 32 ns, `t_su` 40 ns, `t_rec` 40 ns (§4.4).
11. `cluster-boards.md` §2: the 54 dB pole is the released state; pressed it is
    27.1 dB (§2.3). Both conclusions survive.
12. `cluster-boards.md` §2 / `bom.csv` `R-KEY-PU`: the 10 k option costs
    **561 µs**, not 100 µs. Add the 10k/10nF column (§2.6).
13. `bom.csv` `R-KEY-SER`, `C-KEY`, `R-KEY-PU` notes: three live stale rows
    (§9.2).
14. `carrier.md` §3: three decided items still written as open (§9.4).
15. ADR 0010: the truncated sentence (§9.3).
16. ADR 0001: *"~26 pF of loom"* is the loom alone; the `SCK` load is ~62 pF
    (§4.2).
17. `U-KEYS`: name **Nexperia 74HC165D** for the 15 V input tolerance, and
    record why the threshold citation stays with onsemi (§4.6).

**Worth doing, cheap, not blocking:**

18. Marker to 11 bits, free bits 22/23/31 strapped **LOW**; `key-pullup-qty`
    24 → 21 (§5.3). Three tracked figures move together.
19. Add the ratiometric result (§1.4) to `key-release-time` /
    `key-press-time` as a `note:`, with the warning that it holds only while
    `R-KEY-PU` returns to the register's own rail.
20. Record `t_PD(min)` as an unspecified-parameter assumption, not a margin
    (§4.3).
21. Add the canonical net names and the four `J-CHAIN`/`LK-SER` variant
    consequences of a chain reorder (§7).

---

## §11 Where this review could be wrong

Filed deliberately, because a finding recorded as handled does not get caught by
the next reviewer.

- **The reload-hole model (§5.2).** I count a reload at clock `r` as producing
  `W[0:r] + W[0:32−r]`. The page states 11 without stating its model. If its
  convention differs, the absolute numbers differ — but the page's figure was
  computed before the `left_thumb` flip and the flip changes the count under my
  model, which is the finding.
- **Ribbon capacitance and characteristic impedance** are `[from memory]`
  (~50 pF/m, ~105 Ω). No ribbon *cable* datasheet is banked — the manifest has
  the header and the socket, not the cable. Every conclusion in §4.2 has 7–20×
  of margin, so a 2× error in either does not change an answer, but the inputs
  are not documents.
- **ESP32-S3 `V_IH` = 0.75 × VDD and pad output impedance ~40 Ω** are
  `[from memory]`. The `QH` level margin in §3.4 (0.50 V) depends on the first.
- **JESD8C's 0.7/0.3 levels** are `[from memory]`. Nexperia's *claim* of JESD8C
  compliance is banked; the standard's contents are not. The conclusion does not
  depend on it — onsemi's published 3.0 V row carries it alone.
- **28 AWG at 0.214 Ω/m** is `[from memory]`. The loom drop is 6.5 mV; a 3×
  error still leaves it negligible.
- **§6.2's 2.00 mm standoff inherits the −3.20 mm blade shoulder from
  `ks33-geometry.md`'s STEP measurement**, not from the vendor drawing. The
  drawing confirms the collar, the 2.50 mm through-section and the 5.10 mm pin
  tips; the −3.20 mm point where the blade narrows is third-party CAD. If that
  point is wrong, the standoff moves with it. It is the one number in §6 that is
  not vendor-sourced, and it is the one everything else there is built on.
- **§8.1 claims the spare-switch allocation to `right_thumb` is forced.** That
  is true given the 8-bit marker as allocated. If §5.3's 11-bit proposal were
  taken *and* the marker were reallocated, the arithmetic could change. Under
  §5.3 as proposed — which only strips the three already-free bits — it does
  not.
