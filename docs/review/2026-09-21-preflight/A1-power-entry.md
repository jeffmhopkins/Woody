# A1 — `hardware/module/power-entry.md`, cold review against the banked datasheets

**Reviewer slice:** the module's whole power tree — reverse protection, ferrites,
bulk, the LT1641 load switch and its FET, the LM317 DAC rail, the exported
umbilical feed.

**Method.** Cold: no prior review directory was opened. The design corpus was read
freely. Every number below that carries a `[datasheet …]` marker was read out of a
PDF in `datasheets/` during this review, not taken from the corpus. Where the
document is vector CAD with no text layer (the Laird bead drawing, the 1N5817
forward-characteristics figure, LT1641 Figure 5) it was rendered and read by hand or
digitised pixel-by-pixel; the digitisation method is stated at the point of use.

**Provenance markers:** `[datasheet <file> p.N]` · `[repo <file>:<line>]` · `[calc]`
with the arithmetic shown · `[from memory]` · `[no document]` where the corpus
asserts something no banked file supports.

---

## 0. Headline

Seven things worth the owner's time, in order of how much they cost if ignored.

1. **`PWRGD` is connected to nothing, and the `FB` divider was sized entirely from
   a `PWRGD` requirement.** §4.2. The one node with "a hard requirement" has no
   consumer anywhere in the corpus.
2. **The hot-plug margin is 1.48×, not 2.01×.** §4.4. The corpus computes the start
   on *typical* silicon and the fault timer on *worst-case* silicon and divides them.
   On consistent worst-case corners the start is 64.4 ms against a 95.6 ms timer.
3. **The FET's SOA requirement is a ~600 ms pulse at 12 V, not "10 and 100 ms".**
   §4.5. The page tabulates the 587 ms max fault time and then does not use it.
4. **`ΔVGATE` is only guaranteed for `VCC` ≥ 10.8 V, and worst-case `VCC` here is
   11.085 V.** §3-N1. 0.285 V of margin on a spec that appears nowhere in the
   corpus, and it forces a logic-level FET specified at `V_GS` = 4.5 V.
5. **The `PWRGD` worst-case margin is 0.06–0.12 V, not 0.4 V.** §4.2. The stated
   11.36 V omits `D2`'s forward drop and `FB2`'s DCR — the two components
   immediately upstream.
6. **`r_d` is 330 mΩ at 392 mA, not 69 mΩ — and no part on this page carries
   392 mA.** §3 and §2.4. `D1`/`D2` split the current at the first node.
7. **The drawing says `4 × 47 µF` and `bom.csv` says `100 µF / 47 µF / 47 µF` for
   four capacitors.** §5.1. Two documents, one part, and the BOM does not say which
   of the two +12 V branches gets the 100 µF.

Everything the page says about the **foldback mechanism, the unconnected `FB` pin,
the `-1` latch and the `I_GATE` 4:1 window is confirmed verbatim.** That work holds.

---

## 1. Current budget, built from the datasheets

### 1.1 The structural point that reorganises the whole budget

The corpus books a single "module total on +12 V". **No component on this page
carries it.** `D1` and `D2` split the +12 V at the very first node, so downstream of
the split there are two independent current paths and the total exists only on three
things: the IDC's +12 V contacts, the trace between them and the two anodes, and the
rack's own +12 V conductor.

```
J-PWR-EURO +12V  ──┬── D1 ── FB1 ── C1 ── +12V analog      32 mA typ   <- NEVER 392
                   └── D2 ── FB2 ── C2 ── LT1641/R-ILIM/FET/umbilical  361 mA typ
```

This matters because the corpus applies 392 mA to `FB2` `[repo hardware/bom.csv,
FB-IN row: "falling to ~245-275 ohm at the 392 mA module total"]` and to `D2`'s
dynamic resistance `[repo hardware/module/power-entry.md:89]`. Both parts are on the
`D2` branch and carry the umbilical current alone.

### 1.2 Per-rail budget

All device currents below are read out of the banked PDFs. "hot" is the max over the
device's full specified temperature range where one is published.

#### Branch 1 — `+12V_ANA` (through `D1` / `FB1` / `C1`)

| Load | typ | max 25 °C | max hot | source |
|---|---|---|---|---|
| OPA2197 × **7 packages = 14 amplifiers**, `I_Q` | 14.00 | 18.20 | 21.00 mA | `[datasheet OPA2197.pdf p.8: I_Q 1 / 1.3 mA per amplifier; 1.5 mA over −40…+125 °C]` |
| INA828 × 1, `I_Q` | 0.600 | 0.650 | 0.850 mA | `[datasheet INA828IDR.pdf p.6]` |
| LM317L **input** = its output + `I_ADJ` | 9.63 | 10.43 | 10.43 mA | sum of the three rows below |
| ├ DAC8568 `AVDD`, normal mode, internal ref **on** | 1.25 | 2.00 | 2.00 mA | `[datasheet DAC8568CIPW.pdf p.5]` |
| ├ `R-REG-SET` divider, 1.25 V / 150 Ω | 8.33 | 8.33 | 8.33 mA | `[calc]` 1.25/150 = 8.333 mA |
| └ LM317L `I_ADJ` | 0.050 | 0.100 | 0.100 mA | `[datasheet LM317LZ.pdf p.5: 50 µA typ / 100 µA max]` |
| `LED-PANEL` via `R-LED-PANEL` 2.2 kΩ | 4.41 | 4.41 | 4.41 mA | `[calc]` (11.70 − 2.0)/2200 = 4.41 mA (3.86 mA for a 3.2 V green LED) |
| Signal-network and output currents | ~3.5 | ~7 | ~7 mA | **`[no document]`** — see note |
| **Branch 1 total** | **≈ 32.1** | **≈ 40.7** | **≈ 43.7 mA** | |

> **The "signal-network and output currents" row has no source anywhere in the
> corpus.** Six CV outputs into Eurorack inputs through `R-OUT-PROT` 1 kΩ, the mod
> channels' "~1.3 mA total into 4 × 10k" `[repo hardware/module/mod-channels.md:22]`,
> `POT-GAIN` 50 kΩ, `R-BREATH-SUM`, `TRIM-*` and `R-BIAS-DAC` 6 × 100 kΩ are each
> stated in their own page and **never summed**. ~3.5 mA is my estimate `[calc,
> estimate]`. It is the only soft number in this table and it is small.

**Against the corpus:** ADR 0004 books **45 mA** `[repo docs/decisions/0004-cv-interface-module.md:267]`,
`bom.csv`'s `FB-IN` row books **~45 mA**, `figures.yaml`'s `umbilical-current`
`false_positive_note` implies **33 mA** (392 − 359), and `bom.csv`'s `C-BULK-RAIL`
row books **about 22 mA**. Four values for one quantity. 45 mA is a fair over-book of
my 40.7 mA worst case and I recommend keeping it as the design figure; **22 mA is
wrong** — it predates the seventh op-amp and still names the deleted comparator.

**`U-RESP` is a seventh OPA2197 and the page does not know it.** The drawing's
annotation is `OPA2197 ×6, INA828` `[repo hardware/module/power-entry.md:16]`, and
`bom.csv` carries `U-OPA-PITCH` qty 6 **plus** `U-RESP` qty 1, both OPA2197. That is
7 packages, 14 amplifiers, and 2.0 mA of `I_Q` the page does not count. It also means
`C-DECOUPLE` is short by two — see §7.

#### Branch 3 — `-12V_ANA` (through `D3` / `FB3` / `C3`)

| Load | typ | max hot | source |
|---|---|---|---|
| OPA2197 × 14 amplifiers, `I_Q` | 14.00 | 21.00 mA | same current as Branch 1 — see note |
| INA828 × 1 | 0.600 | 0.850 mA | `[datasheet INA828IDR.pdf p.6]` |
| `R-OFFNEG` 95.3 kΩ from −12 V | 0.126 | 0.126 mA | `[calc]` 12/95300 |
| Output sink currents | ~0.8 | ~2 mA | `[no document]` |
| **Branch 3 total** | **≈ 15.5** | **≈ 24.0 mA** | |

> **A dual-supply op-amp's quiescent current is one current, not two.** It enters at
> `V+` and leaves at `V−`, so the *same* 14 mA appears on both rails. The two branches
> therefore differ only by their single-ended loads: the LM317 branch (9.6 mA) and the
> panel LED (4.4 mA) on +12 V, against `R-OFFNEG` (0.13 mA) on −12 V.

**Against the corpus:** ADR 0004 books **~40 mA** on −12 V, `bom.csv`'s `C-BULK-RAIL`
row books **10 mA**, and its `FB-IN` row books **10–20 mA**. Three values. **40 mA is
over-booked by 2.6×; 10 mA is under-booked by 1.5×.** My 15.5 mA typ / 24 mA hot is
the datasheet answer.

#### Branch 2 — `+12V_SW` → `UMBILICAL_+12V` (through `D2` / `FB2` / `C2` / `R-ILIM` / FET)

| Load | quiescent | typical play | +WiFi | clamp-legal worst | clamp fails |
|---|---|---|---|---|---|
| Instrument, down the umbilical | 212 | **359** | 414 | 579 | ~1522 mA |
| LT1641 `I_CC` (tapped at `VCC`, **not** through `R-ILIM`) | 2.0 typ | 2.0 | 2.0 | 5.5 max | 5.5 mA |
| `R-FB-HI` + `R-FB-LO` divider, 12 V / 40.81 kΩ | 0.29 | 0.29 | 0.29 | 0.29 | 0.29 mA |
| **`D2` / `FB2` carry** | **214** | **361.6** | **416.6** | **585** | limited |
| **`R-ILIM` / FET / umbilical carry** | **212** | **359.3** | **414.3** | **579.3** | limited |

`[repo docs/decisions/0005-power-architecture.md:155-161]` for the instrument column;
`[repo config/figures.yaml, umbilical-current]` for the 359 mA;
`[datasheet LT1641.pdf p.2: I_CC 2 mA typ / 5.5 mA max, ON = 3 V]`.

`I_CC` does **not** pass through `R-ILIM`: `VCC` (pin 8) taps the upstream side of the
sense resistor and `GND` (pin 4) returns to `PWR_GND`, so the chip's own current is
outside the sensed loop `[datasheet LT1641.pdf p.8 Figure 5, read from the rendered
drawing]`. That is worth stating because it means the 0.94 A limit is a clean limit
on the exported current, with no chip-current error term.

The `clamp fails` column never reaches the load: the LT1641 limits at
**0.78 / 0.94 / 1.10 A** `[datasheet LT1641.pdf p.2: V_SENSETRIP 39/47/55 mV at
V_FB = 1 V]` ÷ 50 mΩ `[calc]`, then latches.

#### Branch 4 — bus `+5V` (through `FB4` / `C4`)

| Load | typ | max | source |
|---|---|---|---|
| 74AHCT125 static `I_CC` | 0.002 | **0.020 mA** | `[datasheet SN74AHCT125.pdf p.4: I_CC 2 µA typ / 20 µA max at V_CC = 5.5 V]` |
| `ΔI_CC`, 3 umbilical inputs at a 3.3 V logic high | 4.05 | **4.50 mA** | `[datasheet SN74AHCT125.pdf p.4: 1.35 mA typ / 1.5 mA max per input at 3.4 V]` |
| Dynamic, 3 outputs × ~15 pF × 5 V × 2 MHz | 0.45 | 0.45 mA | `[calc]` I = C·V·f |
| Internal switching, 3 gates at 2 MHz | ~1 | ~1.5 mA | `[calc, estimate]` |
| `R-SPI-PULL` cable side, 3 × 10 kΩ — **rail unspecified** | 0 | 1.5 mA | `[no document]` — §6 |
| **4th (spare) gate, input floating** | ? | **?** | **unresolved — see below** |
| **Branch 4 total** | **≈ 5.5** | **≈ 8.0 mA** | |

ADR 0004 and ADR 0005 both book **~10 mA**. That is a safe over-book and I recommend
keeping it. But two things behind it are undocumented:

- **The 74AHCT125 has four buffers, three are used, and nothing in the corpus ties
  the fourth input.** `[repo hardware/module/digital-and-supervision.md:31: "OE x4 →
  GND — tied ENABLED"]` enables all four. A floating CMOS input sits in the linear
  region and draws crowbar current indefinitely; this is the exact failure the six
  `R-SPI-PULL` resistors exist to prevent on the other three. **Tie gate 4's input to
  GND.** It is one net in the netlist and it is the only unbounded term in this rail's
  budget.
- **`ΔI_CC` is the dominant term, not `I_CC`.** The 3.3 V arriving from the instrument
  is a TTL-level high, not a CMOS-level high, so each input holds the AHCT input stage
  partly on. 4.5 mA max across three inputs is 225× the static current. Nothing in the
  corpus mentions it. It does not break anything — it is the reason 10 mA is the right
  over-book rather than 1 mA.

### 1.3 Totals at the rack connector, and the clamp limits

| | quiescent | **typical** | +WiFi | clamp-legal worst | clamp failure |
|---|---|---|---|---|---|
| `J-PWR-EURO` **+12 V** | 246 | **393** | 449 | **626** | ≤ 986 then latch |
| `J-PWR-EURO` **−12 V** | 15.5 | 15.5 | 15.5 | 24.0 | 24.0 mA |
| `J-PWR-EURO` **+5 V** | 5.5 | 5.5 | 5.5 | 8.0 | 8.0 mA |
| `J-PWR-EURO` **GND** (net return) | 236 | **383** | 439 | 610 | ≤ 970 mA |
| **3V3** | — | — | — | — | **not a module rail** |

`[calc]` +12 V typical = 32.1 (Branch 1) + 361.6 (Branch 2) = 393.7 mA.
Ground return = I(+12) + I(+5) − I(−12) = 393.7 + 5.5 − 15.5 = 383.7 mA.
Clamp failure +12 V = 40.7 + 940 + 5.5 = 986 mA, held there by the LT1641 for one
fault-timer period and then latched off.

**Verdict on the three figures the owner asked about:**

| Claim | Where | Verdict |
|---|---|---|
| `~404 mA typical` | `[repo docs/decisions/0004-cv-interface-module.md:267]` | **Close but over-booked.** 45 + 359 = 404. My datasheet build is 393.7. The 45 mA module figure is a fair over-book of 40.7 mA worst case; the arithmetic omits the LT1641's `I_CC` and the `FB` divider, which happen to cancel most of it. **Keep 404 as the design figure, fix its derivation.** |
| `359 mA instrument` | `[repo config/figures.yaml, umbilical-current]` | **Correct as the quantity it names** — the current down the umbilical in typical play. Not checkable from a datasheet (it is an instrument-side build), but it is the only derived figure and its derivation reproduces: 226 × 5 / (0.9 × 11.4) + 248 = 358.1 mA `[calc]`. The 90 % buck efficiency is **conservative**: `[datasheet R-78E5.0-1.0.pdf p.2: 93 % at min V_in (8 V), 85 % at max V_in (28 V)]`, so ~91–92 % at 11.4 V. |
| `392 mA module` | `[repo config/figures.yaml, diode-split-rationale]` and `[repo hardware/bom.csv, FB-IN]` | **Wrong twice.** (a) The number is 393.7, not 392 — 392 uses a 33 mA module branch that matches none of the four module figures in the corpus and omits the LT1641's own current. (b) **More seriously, it is attributed to `D2` and `FB2`, which are on the split branch and carry 361.6 mA.** No component on this page carries a "module total". |

**Nothing is double-counted.** One thing is **not counted at all**: the LT1641's own
`I_CC` (2–5.5 mA) and the `FB` divider (0.29 mA) appear in no budget in the corpus.
They are small; the point is that they sit on the branch whose current everyone
believes they already know.

**Against the connector.** `[datasheet 3M-303-SERIES-BOXED-HEADER.pdf p.1: "Current
Rating: 1 A"]` per contact. The Doepfer 16-pin bus puts +12 V on **two** contacts and
GND on **six** `[repo hardware/module/power-entry.md:101 assumes six grounds]`, so
393 mA typical is 197 mA per +12 V contact — 5× inside the rating. **Even the
single-contact case is safe**: if one +12 V pin is unseated, 986 mA (the LT1641's
ceiling) is still inside 1 A, and the limiter acts before the contact does. That is a
positive result worth recording: *the load switch's current limit is below the
connector's rating, so the connector is never the fuse.*

---

## 2. Impedance at every boundary

### 2.1 Source impedance of each rail, as seen by its load

| Boundary | DC | mid-band | HF | source |
|---|---|---|---|---|
| Rack +12 V at the IDC | ~50–200 mΩ + ~1 µH of flying bus | — | — | **`[from memory]` — no banked document. Flagged.** |
| `D2` dynamic resistance `r_d` at 359 mA | **0.353 Ω** | — | shunted by diffusion capacitance | `[calc]` from the banked curve, §2.4 |
| `D1` `r_d` at 45 mA | **~2.1 Ω** (extrapolated; see §2.4) | — | — | `[calc]`, off the bottom of the published curve |
| `FB2` DCR | **0.080 Ω max** | — | — | `[datasheet MI1206K601R-10-ferrite-bead.pdf, rev E, ELECTRICAL CHARACTERISTICS table]` |
| `FB2` \|Z\| at 100 MHz, under real bias | — | — | **460 / 316 / 145 Ω** | §2.3 |
| `C2` 100 µF electrolytic | 0 | ESR-limited above ~3 kHz | ESR ~0.3–1 Ω | **`[from memory]` — no capacitor datasheet is banked** |
| `R-ILIM` | **50 mΩ** | | | `[repo]` — and it has **no BOM value**, status `open` |
| FET `R_DS(on)` | **TBD, assumed 50 mΩ** | | | `[repo hardware/module/power-entry.md:269 "an assumption, since the FET is still TBD"]` |
| 2 m Cat5 umbilical, round trip | **0.34 Ω** | ~2 µH | 100 Ω line | `[repo docs/decisions/0005-power-architecture.md:93]` |
| LM317L output, DC | **0.27 Ω typ / 0.53 Ω max** | rises above ~1 kHz | `C-REG-OUT` takes over | `[calc]` from `[datasheet LM317LZ.pdf p.5]`, §2.2 |
| `C-REG-OUT` 1 µF | — | 40 Ω at 4 kHz | 0.16 Ω at 1 MHz | `[calc]` 1/(2πfC) |
| `FB` divider, seen at the `FB` pin | **4.49 kΩ** (35.7k ∥ 5.11k) | | | `[calc]` |
| `GATE` node → FET gate | **10 Ω** (`R-GATE-SER`) | | | `[datasheet LT1641.pdf p.8 Fig. 5: R5 = 10 Ω 5 %]` |
| `GATE` node → ground | **1 kΩ + 82 nF** (`R-GATE-COMP` + `C-GATE`) | | | `[datasheet LT1641.pdf p.8 Fig. 5: R6 = 1 k 5 % in series with C1]` |

### 2.2 The LM317's output impedance against the DAC's transient demand

**SLCS144E publishes no output-impedance curve.** `[datasheet LM317LZ.pdf — checked
all 33 pages; §8.3.1 says only "NPN Darlington output topology provides naturally low
output impedance and an output capacitor is optional"]`. So the number has to be
derived from load regulation, and it can be:

```
Output voltage regulation, V_O >= 5 V, I_O = 2.5 mA to 100 mA:
    5 mV/V typ at 25 degC, 10 mV/V max over temperature   [datasheet LM317LZ.pdf p.5]
    -> 5.21 V x 0.005 = 26.1 mV  (typ)   over a 97.5 mA load step
       5.21 V x 0.010 = 52.1 mV  (max)
    Z_out(DC) = 26.1 mV / 97.5 mA = 0.268 ohm typ
              = 52.1 mV / 97.5 mA = 0.534 ohm max          [calc]
```

**The DAC's transient demand:**

```
Full-scale write to the pitch channel drives C-AA-PITCH 10 nF through R-OPAMP-IN 1k.
Charge drawn from AVDD:  Q = C x dV = 10 nF x 5.0 V = 50 nC          [calc]
Supplied by C-REG-OUT (1 uF) + C-DECOUPLE (100 nF) = 1.1 uF:
    droop = 50 nC / 1.1 uF = 45 mV                                   [calc]
Plus the DAC's own supply-current excursion during SPI edges:
    IDD rises from ~1.25 mA to ~3.2 mA in the input transition region
    [datasheet DAC8568CIPW.pdf p.15, "POWER-SUPPLY CURRENT vs LOGIC INPUT VOLTAGE"]
    ~2 mA for ~250 ns = 0.5 nC -> 0.5 mV. Negligible.
```

**Conclusion.** The LM317L's loop cannot supply a 45 mV, microsecond-scale event — its
`Z_out` is only 0.27 Ω at DC and rises with frequency as the loop gain rolls off. What
supplies it is `C-REG-OUT`, and 1 µF is **adequate**: 45 mV of droop against the
~250 mV of margin the 5.00–5.50 V `AVDD` window allows. **But nothing in the corpus
has computed it**, and the number is 45 mV rather than the "noise" it is treated as.
If `C-AA-PITCH` ever grows, or if more than one channel is written full-scale in the
same SPI frame, this scales linearly and `C-REG-OUT` must scale with it. *Record the
45 mV.*

### 2.3 `FB-IN` is not 600 Ω where it matters — confirmed, and it is worse than stated

The corpus's claim is in `[repo config/figures.yaml, ferrite-bias-impedance]` and in
`bom.csv`'s `FB-IN` row. **I digitised the drawing independently** rather than
re-reading the corpus's numbers: the PDF was rendered at 20× zoom, the axes calibrated
from the tick-label positions (0 Ω and 700 Ω on the linear y-axis; decade labels 1, 10,
100, 1000 MHz on the log x-axis), and the five curves separated by their exact RGB
values along the column at 100 MHz.

| DC bias | corpus | **this review, independent digitisation** | verdict |
|---|---|---|---|
| 0 A | ~614 Ω | **614 Ω** (608–620) | CONFIRMED |
| 250 mA | ~431 Ω | **437 Ω** (430–444) | CONFIRMED |
| 500 mA | ~157 Ω | **160 Ω** (157–164) | CONFIRMED |
| 1000 mA | ~72 Ω | **75 Ω** (73–77) | CONFIRMED |
| 1500 mA | ~51 Ω | **54 Ω** (52–56) | CONFIRMED |

`[datasheet MI1206K601R-10-ferrite-bead.pdf, "Z vs FREQUENCY IMPEDANCE UNDER DC BIAS",
rev E 08/05/13, digitised]`. The nameplate table on the same sheet reads **Z@100 MHz
600 nominal / 450 min / 750 max, DCR 0.080 Ω max, rated 1500 mA, 3.20 × 1.60 ×
1.10 mm, −40 to +125 °C including self-heating** — every one of `bom.csv`'s stated
specs CONFIRMED.

**`FB2` at its real currents** (interpolating between bracketing traces; the linear and
log-linear interpolations bound the answer):

| `FB2` operating point | current | \|Z\| at 100 MHz | vs the 600 Ω the BOM row names |
|---|---|---|---|
| Quiescent | 214 mA | **~460 Ω** | 77 % |
| **Typical play** | **361.6 mA** | **282–316 Ω** | **~50 %** |
| Typical + WiFi | 416.6 mA | 240–272 Ω | 43 % |
| **Clamp-legal worst** | **585 mA** | **~142–147 Ω** | **24 %** |
| At the LT1641's limit | 940 mA | ~80 Ω | 13 % |

**The corpus's ~280–310 Ω is CONFIRMED** for typical play. What it does not have is
the bottom of the range: **at the clamp-legal worst case `FB2` gives less than a
quarter of its nameplate.**

**What else this changes — three things:**

1. **The umbilical's HF filter is program-dependent, and it degrades exactly when the
   noise is worst.** The current that biases `FB2` down is dominated by the LED
   brightness, and the LEDs are the loudest aggressor in the instrument. The filter is
   at 460 Ω when nothing is happening and 145 Ω when everything is. That is the wrong
   way round and it is not recorded anywhere.
2. **It changes nothing below ~30 MHz, which is where the real noise is.** Read the
   same sheet's `|Z|, R, X vs FREQUENCY` plot: the part is **~10–15 Ω at 1 MHz** and
   far less at the R-78E5.0's **330 kHz** switching frequency `[datasheet
   R-78E5.0-1.0.pdf p.2: "Internal Operating Frequency, 3.3 & 5 V out: 330 kHz"]`. So
   `FB2` is a wire at the buck fundamental **at every bias, including zero**. The bias
   derating only bites in a band above 30 MHz where the bead was the sole defence. The
   LF job belongs entirely to `C2` and to the rack's source impedance — and `C2`'s ESR
   is `[from memory]`. **That is the real gap, not the bead.**
3. **`FB1`, `FB3` and `FB4` are fine and can be a cheaper part.** At 32 mA, 15.5 mA
   and 5.5 mA they sit on the flat 0 A trace at **~614 Ω**. The `>= 1 A` rule that
   `bom.csv` already refutes bought nothing for them either — a 1206 600 Ω bead of any
   rating gives them the nameplate.

**Recommendation.** Do not chase a bigger bead for `FB2`. **Restate the `FB2`
requirement at its real operating current** — "≥ 280 Ω at 100 MHz at 360 mA of DC
bias, falling to ≥ 140 Ω at 580 mA" — and note in the row that the part's useful band
slides up in frequency rather than disappearing, so the correct compensating move if
E11 finds a problem is a **second-order LC at the module end of the umbilical**, not a
larger bead. `bom.csv`'s existing note already reaches this conclusion; it just stops
one step short of writing the requirement down at the right current.

### 2.4 The diode numbers, re-derived from the banked curve

I rebuilt `D2`'s model from the **guaranteed** points plus the digitised curve, rather
than from a two-point exponential fit, because a Schottky has both an exponential
region and a series-resistance region and a single fit across 1→3 A over-estimates
the ideality factor.

```
Model: Vf = n.Vt . ln(I/Is) + I . Rs
Anchors (all from datasheets/discrete-and-power/1N5817.pdf, DS23001 Rev.8):
  0.240 V at 245 mA   \  digitised off Fig. 2 at 8x render, axes calibrated from
  0.360 V at 612 mA   /  the tick labels; this review's read agrees with the corpus
  0.450 V at 1.0 A    \  GUARANTEED MAXIMA, p.1 table
  0.750 V at 3.0 A    /

Solving the two chords simultaneously:
  0.120 = n.Vt . ln(2.498) + 0.367 . Rs
  0.300 = n.Vt . ln(3.000) + 2.000 . Rs
  -> Rs = 0.100 ohm,  n.Vt = 0.0910 V                                       [calc]

Back-check against BOTH guaranteed points (the model was fitted to neither):
  Vf(1.0 A) = 0.240 + 0.0910.ln(1.0/0.245) + 0.755x0.100 = 0.4435 V  vs 0.450 max
  Vf(3.0 A) = 0.240 + 0.0910.ln(3.0/0.245) + 2.755x0.100 = 0.7440 V  vs 0.750 max
  Both within 1.5 % of the specified maximum. The model is calibrated.      [calc]
```

| Quantity | corpus | **this review** | verdict |
|---|---|---|---|
| `V_f` modulation 245 → 612 mA | 120 mV | **120 mV** | **CONFIRMED** |
| `V_f` at 359 mA (typical play) | "~0.3–0.4 V" | **0.286 V** | CONFIRMED, and 0.400 V in ADR 0005's drop table is pessimistic by 114 mV |
| `V_f` modulation across the **real** operating span (212 → 579 mA) | not computed | **128 mV** | NEW |
| **`r_d` at 392 mA** | **69 mΩ** | **`n.Vt/I + Rs` = 0.0910/0.392 + 0.100 = 0.332 Ω** | **REFUTED — 4.8× low** |
| `r_d` at 359 mA (what `D2` actually carries) | — | **0.353 Ω** | NEW |
| `r_d` at 45 mA (`D1`) | — | ~2.1 Ω, **extrapolated** | see below |

**The 69 mΩ is refuted, and the refutation strengthens the conclusion it supports.**
`power-entry.md:89` keeps `D1`/`D2` for "fault isolation and HF isolation (`r_d` is
69 mΩ at 392 mA)". The real figure is **five times larger**, so the isolation argument
is five times stronger than stated. Fix the number; keep the part. This is also the
`value` field of `figures.yaml`'s `diode-split-rationale`, so it is the *owning*
statement and every citation of it inherits the error.

**Two further caveats on the diode section, both new:**

- **`D1` and `D3` operate off the bottom of the published curve.** Fig. 2's y-axis
  bottoms out at **0.1 A**. `D1` carries 32–45 mA and `D3` carries 15–24 mA. Neither
  point is on any published curve, and the exponential model extrapolates nonsensically
  below 100 mA (it returns 0.066 V at 45 mA, which is physically wrong). **There is no
  document for `D1`'s or `D3`'s forward drop.** A 1N5817 at 45 mA is conventionally
  0.15–0.25 V `[from memory]`. Nothing depends on it — but the page should say so
  rather than implying the 0.3–0.4 V figure covers all three.
- **"HF isolation" is the weaker half of the argument.** A forward-biased Schottky at
  360 mA is a ~0.35 Ω resistor in parallel with its diffusion capacitance, so above a
  few MHz it is not isolating much. `[datasheet 1N5817.pdf p.1: C_T 110 pF typ at 4 V
  reverse]` is the *reverse* capacitance and does not apply forward-biased. **The
  fault-isolation half is the one that carries the part.** Say that, and the argument
  stops resting on a number that will not survive a bench measurement.
- **New, and load-bearing for a hot-plug:** `[datasheet 1N5817.pdf p.1, note under the
  ratings table: "Single phase, half wave, 60 Hz, resistive or inductive load. **For
  capacitive load, derate current by 20 %**"]` → `I_O` = **0.8 A** for `D2`, which
  feeds a purely capacitive branch. The 940 mA current limit **exceeds `D2`'s derated
  average rating**, for up to one fault-timer period. As a one-shot inside `I_FSM`
  (25 A for 8.3 ms) it is safe; as a *repeated* hot-plug it is at the edge. Note it in
  the `D-REVPOL` row.

---

## 3. Provenance re-check — every `[from memory]` and `[calc]` on the page

| # | Claim on the page | old marker | **now** |
|---|---|---|---|
| 1 | Pinout `1 ON 2 FB 3 PWRGD 4 GND 5 TIMER 6 GATE 7 SENSE 8 VCC` | `[164112fc p.2]` | **CONFIRMED** `[datasheet LT1641.pdf p.2 TOP VIEW; corroborated by the pin numbers in Fig. 5 p.8]` |
| 2 | Foldback is sensed at `FB`, not at the output | `[p.8]` | **CONFIRMED verbatim** `[datasheet LT1641.pdf p.8]` |
| 3 | Foldback law: 12 mV at `V_FB` = 0, linear to 47 mV at 0.5 V, flat above | `[p.5, p.8, Fig. 7]` | **CONFIRMED verbatim** `[datasheet LT1641.pdf p.5 SENSE pin; Fig. 7 p.9]` |
| 4 | `V_SENSETRIP` 39 / 47 / 55 mV; 8 / 12 / 17 mV at `V_FB` = 0 | `[p.2]` | **CONFIRMED** `[datasheet LT1641.pdf p.2]` |
| 5 | `I_TIMER` 3 µA down / 80 µA up / 77 µA net | `[p.8]` | **CONFIRMED verbatim** `[datasheet LT1641.pdf p.8]`, and independently in the `TIMER` pin description p.5 |
| 6 | `I_TIMERUP` −24 / −80 / −132 µA; `I_TIMERON` 1.5 / 3 / 5 µA | `[p.2]` | **CONFIRMED** `[datasheet LT1641.pdf p.2]` |
| 7 | `I_GATEUP` −5 / −10 / −20 µA | `[p.2]` | **CONFIRMED** `[datasheet LT1641.pdf p.2, full-temperature (dot) row]` |
| 8 | Fault at `TIMER` = 1.233 V, discharged at 3 µA | `[p.5, p.8]` | **CONFIRMED** `[datasheet LT1641.pdf p.5, p.8]` |
| 9 | `-1` restored by interrupting power or pulsing `ON` low | `[p.9, p.5]` | **CONFIRMED verbatim** `[datasheet LT1641.pdf p.9 and p.5 ON-pin description]` |
| 10 | `V_ONL` 1.233 / `V_ONH` 1.313 / 80 mV hysteresis | `[p.2]` | **CONFIRMED** `[datasheet LT1641.pdf p.2]` |
| 11 | `V_LKO` 7.5 / 8.3 / **8.8** V (page had said 9.8) | `[p.2]` | **CONFIRMED, and the refutation is correct** `[datasheet LT1641.pdf p.2]` |
| 12 | `C-TIMER` minimum 1.5 nF | `[p.5]` | **CONFIRMED** `[datasheet LT1641.pdf p.5]` |
| 13 | S8, θ_JA 110 °C/W, `LT1641-1CS8` / `-1IS8`, `#PBF` | `[p.2]` | **CONFIRMED** `[datasheet LT1641.pdf p.2]` |
| 14 | `I_INFB` ≤ 1 µA max | `[p.2]` | **CONFIRMED** `[datasheet LT1641.pdf p.2, V_FB = GND]` |
| 15 | `C(nF) = 62 · t(ms)` | `[p.8]` | **CONFIRMED verbatim** `[datasheet LT1641.pdf p.8]` |
| 16 | ADI's Fig. 9 caption story | `[p.9]` | **CONFIRMED verbatim** `[datasheet LT1641.pdf p.9]` |
| 17 | `R5` 10 Ω prevents HF oscillation in Q1; `R6` 1 k provides loop compensation | `[p.7]` | **CONFIRMED verbatim** `[datasheet LT1641.pdf p.7]` |
| 18 | `R-GATE-COMP` is **in series with** `C-GATE`, not in parallel | `[Fig. 5 p.8]` | **CONFIRMED by rendering Fig. 5 at 6× and reading the topology.** `R6` runs from the chip-`GATE` node horizontally into `C1`, then to ground. **The page's drawing matches ADI exactly.** |
| 19 | 0.1 µF between `VCC` and `GND` | `[p.9]` | **CONFIRMED** `[datasheet LT1641.pdf p.9 "Supply Transient Protection"]` |
| 20 | ADI's 24 V example uses 49.9 k / 3.4 k | `[Fig. 5 p.8]` | **CONFIRMED** `[datasheet LT1641.pdf p.8, R1/R2]` |
| 21 | `V_f` modulation 120 mV, 0.24 V at 245 mA → 0.36 V at 612 mA | `[repo, digitised]` | **CONFIRMED by independent digitisation** `[datasheet 1N5817.pdf p.2 Fig. 2]`, §2.4 |
| 22 | Calibration: 0.454 V at 1.0 A, 0.746 V at 3.0 A vs 0.450 / 0.750 maxima | `[repo]` | **CONFIRMED** `[datasheet 1N5817.pdf p.1]` — my own two-region fit returns 0.4435 / 0.7440 |
| 23 | OPA2197 PSRR 110.5 dB worst case from ±3 µV/V | `[SBOS737C p.8]` | **CONFIRMED** `[datasheet OPA2197.pdf p.8]`. Arithmetic checks: 20·log₁₀(1/3e−6) = 110.46 dB `[calc]` |
| 24 | **LM317 line regulation 0.52 mV/V** | **unmarked** | **CONFIRMED as the 25 °C TYPICAL, and it is not the worst case.** `[datasheet LM317LZ.pdf p.5: input voltage regulation 0.01 %/V typ / 0.02 %/V max at T_J = 25 °C; 0.02 %/V typ / **0.05 %/V max** over I_O = 2.5–100 mA]`. 0.01 %/V × 5.21 V = 0.521 mV/V `[calc]`. **Worst case is 0.05 %/V = 2.605 mV/V — 5× larger.** Using it scales the 0.00044 cents to 0.0022 cents, which still changes nothing. |
| 25 | R-78E5.0 is 8–28 V | `[repo, datasheet]` | **CONFIRMED** `[datasheet R-78E5.0-1.0.pdf p.2 Selection Guide: R-78E3.3-1.0 = 7–28, **R-78E5.0-1.0 = 8–28**]`. Note ADR 0004:287 still says the buck "needs more than **6 V** in" — stale against the banked document. |
| 26 | FET peak fault dissipation ~4 W at V_out ~ 4 V | `[calc]` | **CONFIRMED and sharpened.** In foldback at `V_OUT` = 0 the FET holds `V_DS` = `VCC` ≈ 11.7 V at 240 mA typ / **340 mA at the 17 mV max floor** → **2.8 W typ / 4.0 W max** `[calc]`. The "roughly flat" claim holds: at `V_OUT` = 4 V, `V_DS` ≈ 7.7 V at 940 mA → 7.2 W. **Peak is at `V_OUT` ≈ 4 V and is 7.2 W, not 4 W.** |
| 27 | Ramp energy ½CV² = 0.158 J | `[calc]` | **Arithmetic confirmed** for C = 2.2 mF: ½ × 2.2e−3 × 144 = 0.158 J `[calc]`. But see §6 — **2.2 mF is not derivable from `bom.csv`**, whose range is 1.04–2.1 mF. |
| 28 | `r_d` 69 mΩ at 392 mA | `[repo figures.yaml]` | **REFUTED — 0.332 Ω.** §2.4 |
| 29 | Worst-case delivered output ~11.36 V | `[calc]` | **REFUTED — 11.045 V.** §4.2 |
| 30 | 2.01× hot-plug margin | `[calc]` | **REFUTED — 1.48× on consistent corners.** §4.4 |
| 31 | "A ≥1 A bead is specified because … a saturated bead is a wire" | `[repo]` | **Already refuted in `bom.csv`; CONFIRMED refuted here.** §2.3 |
| 32 | Entry bulk is 4 × 47 µF | `[repo drawing]` | **CONTRADICTED by `bom.csv`**, which says 100 µF / 47 µF / 47 µF for qty 4. §5.1 |

### Three things the datasheet says that the page does not

| **New** | Finding | Consequence |
|---|---|---|
| **N1** | **`ΔVGATE` (external N-channel gate drive, `V_GATE` − `VCC`) is specified MIN 4.5 V for `VCC` = 10.8 V to 20 V, and MIN 10 V only for `VCC` = 20 V to 80 V** `[datasheet LT1641.pdf p.2, full-temperature row; corroborated in the GATE pin description p.5: "guarantees at least 10V of gate drive for supply voltages above 20V and 4.5V gate drive for supply voltages between 10.8V and 20V"]` | **Two consequences.** (a) The FET must be a **logic-level part with `R_DS(on)` specified at `V_GS` = 4.5 V** — this criterion appears nowhere in the corpus, which sizes the FET only on SOA. (b) **Our worst-case `VCC` is 11.085 V**, only **0.285 V above the 10.8 V floor of that spec**. `VCC` is pin 8, tapped *upstream* of `R-ILIM`, so it sees `D2` and `FB2` only: `VCC` = 11.400 (rack −5 %) − 0.286 (`D2` at 359 mA) − 0.029 (`FB2` DCR at 359 mA) = **11.085 V** `[calc]`. At a −7.5 % rack it is **10.83 V**; below about −8 % the datasheet guarantees **no** gate drive at all. (The 11.045 V of §4.2 is the switch *output*, one `R-ILIM` and one FET further down — a different node.) |
| **N2** | **ADI's Figure 5 carries a FOURTH gate-network part that the page's "Three parts the datasheet's own application has and this page did not" does not name: `D1`, a CMPZ5248B (18 V) Zener, cathode to the chip `GATE` node and anode to the FET source** `[datasheet LT1641.pdf p.8 Fig. 5, read from a 6× render]` | It clamps `V_GS` to 18 V, matching `ΔVGATE`'s **18 V maximum** `[p.2]`. **It is only needed if the chosen FET's `V_GS(max)` is below 20 V.** Recommendation in §4.5. |
| **N3** | **`R-GATE-COMP` decouples `C-GATE` from the fault turn-off path, and that is worth two orders of magnitude** | `I_GATEDN` is 35 / 70 / 100 mA at `V_GATE` = 2 V `[datasheet LT1641.pdf p.2]`. **With `C-GATE` tied straight to ground (the old, wrong drawing)** the pull-down must discharge all 82 nF: 82 nF × 12.5 V / 70 mA = **14.6 µs**, 29 µs on min silicon `[calc]`. **With `R-GATE-COMP` in series as ADI draws it**, the `GATE` node carries only the FET's `C_iss` (~1 nF through `R-GATE-SER`): 1 nF × 12.5 V / 70 mA = **0.18 µs** `[calc]`. `C-GATE` then bleeds out through the 1 kΩ at τ = 82 µs, irrelevant. **`R-GATE-COMP` is not only a compensation zero — it makes the fault turn-off 80× faster.** That is an independent confirmation that ADI's topology is right, and it is a stronger argument than the one `bom.csv` gives. |

---

## 4. The live open items, answered

### 4.1 Entry bulk is 4 × 47 µF — should it change? **Give a number.**

**First, the page and the BOM disagree.** The drawing and the `Still open` bullet both
say **4 × 47 µF** `[repo hardware/module/power-entry.md:15,22,48,50,514]`. `bom.csv`
says `C-BULK-RAIL` = **"100uF (+12V) / 47uF (-12V, +5V) 25V electrolytic", qty 4**
`[repo hardware/bom.csv, C-BULK-RAIL]`. Four capacitors, three named values, and **the
BOM never says which of the two +12 V branches gets the 100 µF**. This is the project's
named failure mode, on this page, today.

**Second, the BOM's reasoning is correct but its numbers are stale.** Its argument is a
decay-rate match at rack power-down: the +12 V branch must not collapse faster than
−12 V or the op-amp outputs get pulled toward the surviving negative rail. It cites
"about 22 mA against −12 V's 10 mA" — and that 22 mA **still counts the deleted
comparator**. Recomputed from the datasheets (§1.2):

```
I(+12V analog) / I(-12V analog) = 32.1 / 15.5 = 2.07          [calc]
C1 / C3                         = 100 / 47   = 2.13
Match to within 3 %.                                          [calc]
```

**The argument survives its own refutation, in the good direction.** Deleting the
comparator and adding the seventh op-amp moved both terms and left the ratio where it
was. Keep 100 / 47.

**Third, on "2–5× the surveyed norm".** Quantified, the worry does not land. Total
entry bulk at the recommendation below is 257 µF; a "norm" module at 4 × 22 µF is
88 µF. At rack power-on a typical Eurorack PSU ramps over 10–100 ms `[from memory]`, so
the extra 169 µF costs `169 µF × 12 V / 50 ms = 41 mA` of additional charging current
`[calc]` against a supply rated 1–2 A. That is not a case-wide inrush problem. The
diodes are also clear: charging 100 µF on a 10 ms ramp is `100 µF × 1200 V/s = 120 mA`
`[calc]`, five orders below `I_FSM` = 25 A / 8.3 ms `[datasheet 1N5817.pdf p.1]`.

**Where the "too much bulk" flag *does* land is `C4`**, and for a completely different
reason. `[repo hardware/module/digital-and-supervision.md:109-113]` already says it:
bus +5 V "is the only rail here with no reverse protection — on a branch **whose bulk
capacitor vents when reverse-biased**." A 47 µF electrolytic on a rail whose only load
draws 5.5 mA is buying nothing and holding the one component that fails violently.

#### Recommended values

| Cap | Branch | **Value** | Why |
|---|---|---|---|
| `C1` | +12 V analog | **100 µF 25 V electrolytic** | decay-rate partner to `C3` at the recomputed 2.07:1 current ratio |
| `C2` | +12 V umbilical | **100 µF 25 V electrolytic** | **changed from 47 µF.** `C2` is what supplies the first microseconds of the FET's 940 mA step so the rest of the rack does not see it: `Q = 940 mA × 10 µs = 9.4 µC` → 0.20 V of local dip on 47 µF, **0.094 V on 100 µF** `[calc]`. It is also the `VCC` reservoir the LT1641 sees, and §3-N1 says that rail has only 0.25 V of margin to spare. |
| `C3` | −12 V analog | **47 µF 25 V electrolytic** | unchanged |
| `C4` | bus +5 V | **10 µF 25 V X7R ceramic** | **changed from 47 µF electrolytic.** The load is 5.5 mA. 10 µF ceramic removes the venting failure mode from the one branch with no series diode, and the ESR loss does not matter on a logic rail. |

**Total entry bulk 257 µF**, and the "4 × 47 µF" phrasing disappears from the corpus.

### 4.2 `PWRGD` — the requirement the `FB` divider was sized from does not exist

**`PWRGD` (pin 3) is connected to nothing.** It appears in the drawing not at all, in
`bom.csv` only inside prose, and there is **no pull-up resistor row anywhere in the
corpus** — ADI's reference circuit fits `R7` 24 kΩ for exactly this `[datasheet
LT1641.pdf p.8 Fig. 5]` and `[p.5: "Open Collector Output to GND"]`. A grep of the
whole design corpus returns eleven hits, all of them inside `power-entry.md`'s own
divider-sizing argument, `bom.csv`'s two `R-FB-*` rows, and `figures.yaml`'s
derivation for the same.

And the page's sizing rests on it: *"The divider is chosen at the `PWRGD` end, because
**that is the end with a hard requirement**"* `[repo hardware/module/power-entry.md:263-264]`.

**Two consequences.**

**(a) The stated margin is wrong by 3.5×.** The page computes the worst-case delivered
output as 11.4 − 0.020 (`R-ILIM`) − 0.020 (FET) = 11.36 V. **It omits `D2` and `FB2`,
the two components immediately upstream of the switch.**

```
Worst-case output, rack at -5 %:
  11.400  bus +12 V at -5 %                                        [repo] 0005
- 0.286   D2 forward drop at 359 mA        [datasheet 1N5817.pdf, model of §2.4]
- 0.029   FB2 DCR, 0.080 ohm max x 359 mA  [datasheet MI1206K601R-10, rev E]
- 0.020   R-ILIM, 50 mohm x 0.4 A
- 0.020   FET at R_DS(on) = 50 mohm (assumed; the FET is TBD)
= 11.045 V                                                              [calc]

Against the stated worst-case PWRGD release of 10.93 V:  margin 0.115 V
At R_DS(on) = 200 mohm:  10.987 V  ->                    margin 0.057 V
The page claims 0.4 V and 0.37 V respectively.
```

**(b) Because the divider was sized from a wrong number, it should move.** Retarget the
nominal `PWRGD` point from 10.5 V to **10.05 V**, restoring the margin the page
intended:

```
k = V_FBH / V_OUT = 1.313 / 10.05 = 0.13065  ->  R-FB-HI / R-FB-LO = 6.654
E96:  R-FB-HI = 34.0 kohm 1 %,  R-FB-LO = 5.11 kohm 1 %   (ratio 6.654)   [calc]
```

| | `V_OUT` at which it happens |
|---|---|
| `V_FB` = 0.5 V — full 47 mV limit available | **3.83 V** (was 3.99 V — marginally earlier, marginally better for the start) |
| `PWRGD` releases, `V_FB` = 1.313 V rising | **10.05 V** (9.83–10.47 V worst case over 1 % resistors and the 1.280–1.345 V `V_FBH` window `[datasheet LT1641.pdf p.2]`) |
| `PWRGD` re-asserts, `V_FB` = 1.233 V falling | **9.44 V** |
| `V_FB` at the settled 12.0 V output | **1.568 V** (abs max on `FB` is 60 V `[p.2]`) |
| **Worst-case margin below the worst-case delivered output** | **0.575 V** at 50 mΩ, **0.52 V** at 200 mΩ |

Divider current at 12 V = 12 / 39.11 kΩ = **307 µA**, i.e. 307× the 1 µA max `FB`
input current `[datasheet LT1641.pdf p.2]`, so leakage is ≤ 0.33 % of the ratio and
3.7 mW is not worth trimming. The page's reasoning on this point is sound and
unchanged.

**Recommendation to the owner, in order:**

1. **Connect `PWRGD`.** It is free, it is already a pin, and it is the correct driver
   for the panel LED — see §4.6. Then the "hard requirement" becomes real.
2. Move `R-FB-HI` to **34.0 kΩ**, keep `R-FB-LO` at **5.11 kΩ**.
3. Fix the 11.36 V arithmetic in the page and in `figures.yaml`'s
   `loadswitch-fb-divider` derivation, which repeats it verbatim.

*(`figures.yaml`'s `loadswitch-fb-divider` currently has `value: "35.7 kohm / 5.11
kohm"` and `forbidden: ["R-FB-HI,module,TBD", …]`. Changing it is the three-step
process in `CLAUDE.md` §2, and `35.7` will need to go into `forbidden`.)*

### 4.3 Damping the input LC — is it stable?

**`carrier.md`'s conclusion is right and its margin is not the binding one.** Its
calculation `[repo hardware/controller/carrier.md:124-139]` rests on
`ESR of a 100 µF / 25 V radial ≈ 0.5–1 Ω [from memory]`, which is the one input the
whole result depends on, and it picks L = 22 µH ("mid range") from a 10–47 µH BOM range
`[repo hardware/bom.csv, L-BUCK-IN]`.

**Redo it at the corners, and it stops depending on the ESR at all.**

```
Middlebrook: the filter's peak output impedance must sit well below |R_neg|.

Worst L, worst C:  L = 47 uH (top of the BOM range), C = 100 uF
  Z0 = sqrt(L/C) = sqrt(47e-6/100e-6)      = 0.685 ohm                   [calc]
  Series R with ZERO ESR (a ceramic substitution) = inductor DCR alone, ~0.1 ohm
  Q  = Z0 / R = 6.85    ->  Z_peak = Q.Z0  = 4.69 ohm                    [calc]

Worst load: BOTH bucks hang off C-BUCK-IN, so the constant-power load is the
whole 5 V rail, not just buck A:
  928 mA x 5 V / 0.90 = 5.16 W at 11.4 V
  R_neg = -V^2/P = -11.4^2 / 5.16 = -25.2 ohm                            [calc]

Margin at the worst corner:  25.2 / 4.69 = 5.4x  = 14.6 dB               [calc]
```

14.6 dB clears Middlebrook's 6 dB rule of thumb but is a long way from the **220× /
47 dB** `carrier.md` reports — because that figure used the mid-range inductor, the
typical-play load, buck A alone, and a `[from memory]` ESR, all four on the favourable
side simultaneously.

**Recommendation: pin `L-BUCK-IN` to 10 µH and the open item closes without a damping
leg.**

```
At L = 10 uH:  Z0 = 0.316 ohm, Q(zero ESR) = 3.16, Z_peak = 1.00 ohm
  Margin = 25.2 / 1.00 = 25x = 28 dB, at the worst load AND with no ESR at all [calc]
Still filters: f0 = 1/(2.pi.sqrt(LC)) = 5.03 kHz, 66x below the buck's 330 kHz
  [datasheet R-78E5.0-1.0.pdf p.2], giving ~32 dB of ESR-limited attenuation [calc]
```

**Pinning the value to 10 µH makes the answer independent of the `[from memory]` ESR,
independent of which capacitor is fitted, and independent of the load split between the
two bucks.** That is worth more than 47 dB of margin that rests on an unsourced
number. Keep the electrolytic anyway — it costs nothing and it is what `carrier.md`
already specifies — but the result no longer needs it.

**One caveat the corpus does not have:** `[datasheet R-78E5.0-1.0.pdf p.2: max.
Capacitive Load 220 µF]`. `C-BUCK-IN` at 100 µF is on the *input* so it is not covered
by that limit, but the **output** side (dev-board decoupling plus whatever the matrix
board carries) is, and nothing in the corpus checks it. Out of my slice; flagged.

**Verdict: stable, at every corner, with no damping leg — provided `L-BUCK-IN` is
pinned. Put the 10 µH in `bom.csv` and delete the range.**

### 4.4 No fuse on the analog rails

**The corpus leaves this open honestly, and the banked polyfuse datasheet closes it.**

ADR 0005's deletion argument is about the *instrument-end* polyfuse and rests on two
facts: the hold current derated **below typical play**, and the part sat downstream of
the module's limiter. `[repo docs/decisions/0005-power-architecture.md:307-317]`. The
page correctly says that argument does not reach the analog rails. Here is why it
genuinely does not:

```
MF-PSMF series, Ihold at 23 degC / at 60 degC, and Vmax:
  [datasheet MF-PSMF010X-polyfuse.pdf p.2 Electrical Characteristics
   and p.4 Thermal Derating Chart]

  MF-PSMF010X     Vmax 15 V   Ihold 0.10 A (0.07 A at 60 degC)  Itrip 0.30 A  R 1.0-7.5 ohm
  MF-PSMF010/24X  Vmax 24 V   Ihold 0.10 A (0.07 A at 60 degC)  Itrip 0.30 A  R 1.0-7.5 ohm
  MF-PSMF020X     Vmax  9 V   Ihold 0.20 A
  MF-PSMF035X     Vmax  6 V   Ihold 0.35 A     <- and everything above it is Vmax 6 V
```

That last line **confirms ADR 0005's "the obvious part number is a 6 V-rated part on a
12 V rail"** — for the *umbilical* current, which needs `I_hold` ≥ 0.6 A, every
candidate in the series is a 6 V part. **But the analog branches draw 41 mA and
24 mA**, and at that current the 15 V and 24 V parts are available.

| | +12 V analog | −12 V analog |
|---|---|---|
| Worst-case draw (§1.2) | 43.7 mA | 24.0 mA |
| `I_hold` at 60 °C, MF-PSMF010/24X | 70 mA | 70 mA |
| **Margin below hold** | **1.6×** | **2.9×** |
| Series R after reflow, 1.0–7.5 Ω | **0.04–0.33 V** of drop | **0.02–0.18 V** |

**The thermal-runaway objection does not apply here, and that is the whole point.** A
PTC creeps into current limiting when the normal current sits *near or above* `I_hold`
— which is exactly what killed the instrument-end part. At 44 mA against a 70 mA
derated hold, the part never leaves its low-resistance state in normal operation.

**What it buys:** a shorted decoupling cap, a solder bridge, a reversed `C1`, or an
op-amp latch-up currently presents a **dead short from the rack's +12 V rail**, which
browns out every other module in the case. A PTC makes the module isolate itself — the
same job the load switch does for the umbilical, on the branch that has no limiter. It
also protects `D1`, whose average rating is **0.8 A for a capacitive load** (§2.4).

**Recommendation: fit `MF-PSMF010/24X` on the +12 V-analog and −12 V branches,
immediately after `D1` and `D3` and ahead of `FB1`/`FB3`.** Two new BOM rows.
`V_max` 24 V, `I_max` 80 A.

- **Not on bus +5 V.** The load is 5.5 mA; the smallest part's 1–7.5 Ω does more harm
  than a PTC does good on a logic rail, and that rail's real hazard is the reversed
  ribbon, which a PTC does not address. (`C4` → ceramic does, §4.1.)
- **Not on the umbilical branch.** ADR 0005 is right: the LT1641 is faster, has no
  thermal hysteresis, and sits at the source end. Nothing changes there.
- **Headroom check:** 0.33 V of worst-case drop on +12 V analog against the LM317's
  5.9 V worst-case `V_I − V_O` and its 2.5 V minimum `[datasheet LM317LZ.pdf p.4
  Recommended Operating Conditions]` — 3.1 V of margin left. Fine.
- **Impedance check:** `R1max` 7.5 Ω is in series ahead of `C1`, so the rail's source
  impedance below `1/(2π·7.5·100 µF)` = **212 Hz** `[calc]` is 7.5 Ω. A 1 mA
  output-current change moves the rail 7.5 mV; through the OPA2197's 110.5 dB
  worst-case PSRR that is 24 nV at the input `[calc]`. Not a concern.

### 4.5 ADR 0005's ramp spec is unachievable — widen, or change the approach?

**Recommendation: widen ADR 0005 to a 50–200 ms ramp. Do not change the approach.**

The reasons, and then the two things that *do* have to change.

1. **Nothing downstream depends on the ramp time.** The fault timer is sized against
   the hot-plug, not the ramp `[repo hardware/module/power-entry.md:333-334]`. ADR 0005's
   own "75 ms start" is a *current-limited* start, not a ramped one. The FET is sized
   on SOA. The spec is load-bearing on nothing.
2. **Programming the ramp with anything other than the internal pull-up costs more
   than it buys.** The alternative is an external current source into the `GATE` node —
   which means a JFET or a current mirror referenced above `VCC`, on a node that already
   has only 4.5 V of guaranteed headroom above `VCC` (§3-N1) and is the node ADI's own
   compensation network sits on. That is three new parts and a new stability question to
   fix a specification nothing reads.
3. **Both ends of the widened envelope are safe** — the page already establishes this,
   and my recheck below confirms it with a correction.

#### The correction: the fast corner takes 18 % of the timer, not 10.5 %

`power-entry.md:376-382` computes the fast corner's excursion using the **typical**
foldback floor (12 mV) against the **worst-case** timer current (129 µA). Those are
opposite corners of the same die. On consistent min-sense silicon:

```
Min-silicon foldback line:  160 mA at V_FB = 0  ->  780 mA at V_FB = 0.5 V
  [datasheet LT1641.pdf p.2: 8 mV and 39 mV minima, / 50 mohm]
  slope m = (780 - 160) mA / 3.83 V = 161.9 mA/V      (at the retargeted divider)
Fast-corner charging demand: 2.2 mF x 244 V/s = 537 mA
Escapes current limit at:    537 = 160 + 161.9.V  ->  V_OUT = 2.33 V
Time in current limit:  t = (C/m).ln(I2/I1)
                          = (2.2e-3 / 0.1619) . ln(537/160) = 16.5 ms       [calc]
TIMER rise on worst-case silicon: 129 uA x 16.5 ms / 10 uF = 213 mV
                                  = 17.3 % of 1.233 V                       [calc]
```

**213 mV / 17.3 %, not 130 mV / 10.5 %.** Still nowhere near a latch, and the
conclusion — "worth knowing, and nowhere near a latch" — survives. The number does not.

#### The correction that matters more: the hot-plug margin is 1.48×, not 2.01×

Same defect, same page, larger consequence. The start is computed on *typical* silicon
(12 mV floor, 47 mV top) and the fault timer on *worst-case* silicon (132 µA pull-up),
and the ratio of the two is reported as the design margin.

```
Hot-plug, on CONSISTENT min-sense silicon (8 mV floor, 39 mV top):

phase 1  0 -> 3.83 V through the foldback ramp
         t = (C/m).ln(I2/I1) = (2.2e-3 / 0.1619) . ln(780/160)
           = 0.013589 x 1.5841 = 21.5 ms                                    [calc]
phase 2  3.83 -> 12 V at 780 mA less the 360 mA instrument load = 420 mA
         t = 2.2 mF x 8.17 V / 0.420 A = 42.8 ms                            [calc]
                                                        total = 64.3 ms

Worst-case fault timer, 10 uF at the 129 uA net max ramp:
         t = 1.233 V x 10 uF / 129 uA = 95.6 ms                             [calc]
                                                       MARGIN = 1.49x
```

The page reports **2.01×** and uses it to justify 10 µF over 9.4 µF. **The true
worst-case margin is 1.49×**, and at 9.4 µF it would be 1.40×.

**Do not fix this by growing `C-TIMER`.** A bigger timer makes the *other* end worse —
see §4.5's FET note below. Fix it by shrinking the load capacitance:

> **Recommendation (crosses into `carrier.md`'s slice, raised here because this page is
> where it binds):** pin **`C-STRIP-BULK` to 470 µF, not "470–1000 µF"**. Total load
> capacitance falls from 2.1 mF to **1.04 mF**, the worst-case hot-plug start halves to
> **~32 ms**, and the margin becomes **3.0×** `[calc]`. `C-STRIP-BULK`'s own job — bulk
> at the WS2815 feed points — is met at 470 µF. This is a one-word BOM change with a
> 2× effect on the number the whole load switch is sized against.

#### The FET SOA requirement is a ~600 ms pulse, not 10 and 100 ms

`power-entry.md:432` says *"The SOA chart must cover 12 V at 10 and 100 ms."* The page
itself tabulates the fault timer's **minimum** current three lines earlier:

| `TIMER` pull-up | net ramp | fault time at 10 µF |
|---|---|---|
| −24 µA (min) | 21 µA | **587 ms** |

`[datasheet LT1641.pdf p.2: I_TIMERUP −24 / −80 / −132 µA; I_TIMERON 1.5 / 3 / 5 µA]`.
On slow-timer silicon a hard short is held in foldback for **587 ms**, at
`V_DS` = `VCC` ≈ 11.7 V and 240–340 mA (the 12 mV typ / 17 mV max floor), i.e.
**2.8–4.0 W for 0.59 s** `[calc]`. At 0.59 s a DPAK is essentially at its DC thermal
operating point, and — as the page rightly says — **the killer is Spirito / linear-mode
derating at high `V_DS`, which is a DC-SOA question, not a transient one.**

**Restate the FET criterion as three lines:**

1. **SOA must cover `V_DS` = 12 V at 340 mA for 1 s** (read the DC line if 1 s is not
   plotted). Not 10 ms, not 100 ms.
2. **`R_DS(on)` specified at `V_GS` = 4.5 V** — that is the LT1641's guaranteed gate
   drive at our `VCC` (§3-N1).
3. **`V_GS(max)` ≥ 20 V**, so ADI's 18 V Zener (§3-N2) is not needed. If a part with
   `V_GS(max)` = ±12 or ±16 V is otherwise attractive, fit ADI's `D1` as drawn: an 18 V
   Zener, cathode to the chip `GATE` node, anode to the FET source.

Peak dissipation is **7.2 W at `V_OUT` ≈ 4 V** (940 mA × 7.7 V), not the 4 W the page
states `[calc]` — foldback holds it *flatter* than no foldback, not flat.

### 4.6 `R-GATE-SER` and `R-GATE-COMP` — verify against the datasheet; does the drawing match?

**Both CONFIRMED, and the drawing matches ADI exactly.** I rendered Figure 5 at 6× and
read the topology directly rather than inferring it from the caption text.

```
What ADI's Figure 5 actually draws  [datasheet LT1641.pdf p.8, rendered and read]:

  V_IN --[Rs 0.025R]--+--(Q1 IRF530 drain..source)--+-- V_OUT
        |             |                              |
     pin 8 VCC     pin 7 SENSE                    [D1 CMPZ5248B]   <-- NOT in our drawing
                                |                    | anode up to V_OUT
                          [R5 10R 5%]                | cathode down to the GATE node
                                |                    |
  pin 6 GATE ---------------o---+--------------------+
                            |
                      [R6 1k 5%]--[C1 10nF]--GND    <-- R6 IN SERIES WITH C1. Confirmed.
```

| Claim | Verdict |
|---|---|
| `R-GATE-SER` = ADI's `R5`, 10 Ω 5 %, between the chip `GATE` pin and the FET gate | **CONFIRMED** `[datasheet LT1641.pdf p.8 Fig. 5; p.7: "R5 prevents high frequency oscillations in Q1"]` |
| `R-GATE-COMP` = ADI's `R6`, 1 kΩ 5 %, **in series with** `C-GATE`, not in parallel with anything | **CONFIRMED** `[datasheet LT1641.pdf p.8 Fig. 5, read from the render; p.7: "Resistor R6 provides current control loop compensation"]` |
| The RC tap is on the **chip** side of `R-GATE-SER` | **CONFIRMED** — `R5`'s bottom node is the pin-6 node and `R6`/`C1` hang off it, exactly as `power-entry.md:399-407` draws it |
| `C-GATE`'s ramp calculation is unaffected by the 1 kΩ | **CONFIRMED** `[calc]` 10 µA × 1 kΩ = 10 mV against a 12 V ramp |
| ADI's values are 10 Ω and 1 kΩ, and ours are 10 Ω and 1 kΩ | **CONFIRMED** |
| **The page's "three parts" list is missing a fourth** | **`D1`, the CMPZ5248B 18 V Zener from `GATE` to the FET source.** See §3-N2. |

**Two additions to the `R-GATE-COMP` row's justification, both new:** it makes the
fault turn-off 80× faster (§3-N3), and `C-GATE` at 82 nF is 8.2× ADI's `C1`, which
scales the compensation network's pole by the same factor — ADI's 1 kΩ/10 nF corner is
at 15.9 kHz and ours is at **1.94 kHz** `[calc]`. ADI publishes no guidance on
co-scaling `R6` with `C1`. **Keeping 1 kΩ is the conservative choice** (more phase lead
at the loop crossover, not less), but it is a deviation from the reference circuit and
should be recorded as one rather than presented as "read straight off the manufacturer's
reference circuit". The value is right; the provenance claim is one notch too strong.

### 4.7 Bonus — the `ON` pin, designed

The page says *"Still not designed … pick the trip point, then the divider is
arithmetic."* Here is the trip point and the arithmetic, because the datasheet now
supplies the constraint that picks it.

**The trip point picks itself: 10.0 V.** Not an ADR judgement after all —
§3-N1 shows the LT1641's gate-drive specification has a hard floor at `VCC` = 10.8 V,
and the internal `V_LKO` UVLO tops out at 8.8 V `[datasheet LT1641.pdf p.2]`. An `ON`
trip at 10.0 V sits **above** the internal UVLO (so the divider governs, which is the
point of having one) and **below** the 11.085 V worst-case operating `VCC` by 1.0 V
(so it does not nuisance-trip). It is also 1.84 V above the 8.16 V the umbilical must
deliver for the R-78E5.0's 8 V input minimum `[datasheet R-78E5.0-1.0.pdf p.2]`.

```
V_ON = V_ONH = 1.313 V at VCC = 10.0 V  ->  k = 0.1313  ->  R_top/R_bot = 6.616
E96:  R-ON-HI = 34.0 kohm 1 %,  R-ON-LO = 5.11 kohm 1 %  (ratio 6.654)      [calc]

  Rising trip  (V_ONH 1.313):  1.313 x 7.654 = 10.05 V
  Falling trip (V_ONL 1.233):  1.233 x 7.654 =  9.44 V   -> 0.61 V of hysteresis
  Worst case over 1 % parts and the 1.280-1.345 V V_ONH window:
      1.280 x 7.522 = 9.63 V  ...  1.345 x 7.788 = 10.47 V                  [calc]
  Both above V_LKO max (8.8 V) and both below worst-case VCC (11.085 V).   [calc]
  Divider current at 11.69 V: 0.299 mA = 299x the 1 uA max ON input current [p.2]
```

**These are the same two E96 values as the retargeted `FB` divider (§4.2), and that is
not a coincidence** — both dividers reference the same 1.313 V threshold against the
same ~10 V decision point, one on the input side and one on the output side. One part
number each, qty 2.

**Wiring.** `SW-POWER` is the **bottom leg**, in parallel with `R-ON-LO`: closing the
toggle pulls `ON` to `PWR_GND` and turns the instrument off. That way a broken panel
harness leaves the instrument **on** (benign, and the LED still reports) rather than
dead, and the toggle carries 0.3 mA so its rating genuinely stops mattering.

**Debounce.** Add **`C-ON` = 1 µF X7R** from `ON` to `PWR_GND`. τ = (34.0k ∥ 5.11k) ×
1 µF = **4.44 ms** `[calc]`, which swamps toggle bounce and filters rack transients off
a pin that pulls `GATE` low in 6 µs `[datasheet LT1641.pdf p.3: t_PHLON 6 µs]`. Without
it, a bouncing toggle dumps the gate repeatedly and the start stutters.

**And this pin is the latch reset.** `[datasheet LT1641.pdf p.5: "Pulsing the ON pin
low after a current limit fault will reset the fault latch"]` and `[p.9: "restored
either by interrupting power or by pulsing ON low"]`. So after a latch-off, off-then-on
at the panel restarts the instrument — the page says this in prose and now the circuit
does it.

**Three new BOM rows: `R-ON-HI` 34.0 kΩ 1 %, `R-ON-LO` 5.11 kΩ 1 %, `C-ON` 1 µF 25 V
X7R 0805.** Closes "Still not designed: the `ON` pin".

### 4.8 Bonus — the panel LED, closed without the datasheet read the page waits for

`power-entry.md:484-489` proposes driving the LED from the `TIMER` node or the gate,
and defers it because *"it depends on what the `TIMER` pin does after a latch."*

**It does not need to.** Two answers, both free:

- **Simplest: move `R-LED-PANEL`'s anode from `+12V_ANA` to `UMBILICAL_+12V`** — the
  FET's source. Lit = the switch is passing current. Dark = latched off, or the toggle
  is off. That is exactly the requirement (`bom.csv`: *"this still says why the
  instrument went dark"*), it is one net change, it needs no datasheet reading at all,
  and it adds 4.4 mA to the umbilical branch — 55× below the 240 mA foldback floor, so
  it cannot affect the start.
- **Better, if `PWRGD` gets connected (§4.2): a second LED from `+12V_ANA` through a
  resistor to `PWRGD`.** `PWRGD` is an open collector rated to sink 2 mA at 0.4 V and
  4 mA at 2.5 V `[datasheet LT1641.pdf p.2, V_OL]`, so `R = (11.7 − 2.0 − 2.5)/4 mA =
  1.8 kΩ`; **2.2 kΩ gives 3.3 mA** `[calc]`, within spec. It lights during the ramp and
  during a fault and goes dark when the output is good — a genuine fault indicator
  beside a genuine power indicator.

**Recommend the first**, and note the second in `LED-PANEL`'s row as what `PWRGD` buys
if it is ever connected.

### 4.9 Bonus — the LM317 rail is aimed 40 mV below where it should be

Out of the open-items list, but inside the slice, and it is a one-line fix.

```
Required window:  AVDD 5.00 - 5.50 V   (DAC8568 C grade; the 5.00 V floor is
  figures.yaml's dac-rail `floor`, and 5.5 V is the DAC's own spec maximum
  [datasheet DAC8568CIPW.pdf p.5: AVDD 2.7 to 5.5 V; abs max -0.3 to +6 V p.2])
Centre of that window: 5.25 V.        Present nominal: 5.208 V, 42 mV below centre.

Worst-case stack at 150 R / 475 R, 0.1 %, 25 degC:
  V_ref 1.20 / 1.25 / 1.30 V, I_ADJ 100 uA max     [datasheet LM317LZ.pdf p.5]
  min = 1.20 x (1 + 474.5/150.15)                  = 4.992 V   <- BELOW THE 5.00 FLOOR
  max = 1.30 x (1 + 475.5/149.85) + 100uA x 475    = 5.472 V                [calc]
  Spread 0.480 V against a 0.500 V window: it does not fit, and it fails LOW.
```

**Two findings.** (a) `bom.csv` says the worst case *"spans 0.66 V against a ~0.55 V
window"*; the datasheet-derived spread at 0.1 % and 25 °C is **0.480 V against
0.500 V**. The 0.66 V is not reproducible from SLCS144E — it is reachable only by
adding the 10 mV/V tempco (52 mV) twice. The row's *conclusion* — that E7 must select
on the bench — is right and unaffected. (b) **The failure is asymmetric and it fails
low**, into the hard floor, because the nominal is 42 mV below centre.

**Recommendation: retarget the bench selection at E7 to the centre of the DAC's window
rather than to 5.208 V, and give it a finer step to hit it with.** E96 alone cannot:
one E96 step on `R2` is 2.3 %, which moves the output by `2.3 % × (V_out − 1.25)` =
**92 mV**, regardless of which resistor you step `[calc]`.

```
Fit R2 as 475 R fixed PLUS one selected series resistor from a small E96 kit:
  475 + 0    -> 1.25 x (1 + 475.00/150) = 5.208 V
  475 + 4.75 -> 1.25 x (1 + 479.75/150) = 5.248 V   <- recommended nominal
  475 + 10.0 -> 1.25 x (1 + 485.00/150) = 5.292 V
  475 + 15.0 -> 1.25 x (1 + 490.00/150) = 5.333 V
  475 + 20.0 -> 5.375 V    475 + 24.9 -> 5.416 V                            [calc]
A 40 mV selection step instead of 92 mV, for one extra 0805.
```

After bench selection the LM317's own reference tolerance is *measured out*, and what
remains is drift: 10 mV/V tempco = 52 mV over 0–125 °C, plus line and load regulation
`[datasheet LM317LZ.pdf p.5]`. **Against ±250 mV of window that is comfortable — but
only if the rail is aimed at the centre.**

**Three supporting confirmations while I was in the document:**

- `V_I − V_O` **minimum 2.5 V** `[datasheet LM317LZ.pdf p.4 Recommended Operating
  Conditions]`. Ours is 6.5 V nominal, 5.9 V at a −5 % rack `[calc]`. Clear.
- **Minimum load 2.5 mA MAX** and `I_O` recommended 2.5–100 mA `[p.4, p.5]` — and
  `bom.csv`'s warning that ST/ON parts commonly want 3.5 mA is the right one to keep.
  Our divider alone is 8.33 mA. Clear on every candidate.
- **The ADJ protection diode is not required here.** `[datasheet LM317LZ.pdf p.9
  §9.2.2.4: "When capacitor is used and V_OUT > 6 V, a protection diode from adjust to
  output is recommended"]`. At 5.21 V we are below that threshold. Worth stating
  explicitly in the `C-REG-ADJ` row, because a reader who knows the LM317 folklore will
  otherwise flag its absence.
- **`RθJA` for the TO-92 (TI's "LP") package is 139.5 °C/W** `[datasheet LM317LZ.pdf
  p.4 Thermal Information]`. At `(11.70 − 5.21) × 9.63 mA` = **62.5 mW** the junction
  rise is **8.7 °C** `[calc]`. `bom.csv`'s "~90 mW" is an over-book; either way it is
  nothing. And note the package column confirms `bom.csv`'s existing warning: **TI's
  TO-92 designator is LP, so "LM317LZ" is an ST/ON marking, not a TI orderable.**

---

## 5. What else this page contradicts

### 5.1 The four entry capacitors

Covered in §4.1. Drawing says `4 × 47 µF` in five places; `bom.csv` says
`100 µF / 47 µF / 47 µF` for four parts and does not assign the fourth.

### 5.2 `2.2 mF` is load-bearing and is not derivable from anything

The `2.2 mF` of instrument-side load capacitance sizes the ramp current (268 mA), the
hot-plug time (47.5 ms, or 64.3 ms recomputed), `C-TIMER`, `C-GATE`, the FET's SOA and
the ramp energy (0.158 J). It appears eight times on this page.

**It is not in `figures.yaml`, and `bom.csv` does not produce it:**

```
C-STRIP-BULK  470-1000 uF x2  = 0.94 - 2.00 mF     [repo hardware/bom.csv]
C-BUCK-IN     100 uF          = 0.10 mF            [repo hardware/controller/carrier.md]
C-BULK-DISP   TBD             = ?                  [repo hardware/bom.csv, status open]
                                -----------------
                                1.04 - 2.10 mF, plus an unknown
```

2.2 mF is above the top of the BOM's own range. It is *conservative* in every use on
this page, so nothing is presently unsafe — but it is an unsourced number driving six
derived values, which is precisely the class of defect `figures.yaml` exists for.

> **Recommendation: add `umbilical-load-capacitance` to `config/figures.yaml`**, owned
> by `docs/decisions/0005-power-architecture.md`, with `status: settled` once
> `C-STRIP-BULK` is pinned (§4.5). Value **1.04 mF** at 470 µF × 2 + 100 µF, or
> **2.10 mF** if the 1000 µF option is kept. This is the highest-leverage single action
> on this page.

### 5.3 Smaller contradictions, node-indexed

| Node / ref | Finding | Provenance |
|---|---|---|
| `+12V_ANA` | Page's drawing annotates `OPA2197 ×6`; `bom.csv` has 7 packages (`U-OPA-PITCH` 6 + `U-RESP` 1) | `[repo hardware/bom.csv]` |
| `C-DECOUPLE` | qty 19 = "6 × OPA2197 = 12, INA828 = 2, DAC8568 AVDD+DVDD = 2, 74AHCT125, LT1641 VCC, LM317 in". **Two errors**: `U-RESP` needs 2 more, and **the DAC8568 has no DVDD** — the TSSOP-16 has one supply pin, `AVDD` `[datasheet DAC8568CIPW.pdf p.6 Pin Functions]`. Should be **20**, not 19. | `[repo hardware/bom.csv]` + `[datasheet]` |
| `+12V_SW` | ADR 0004:287 says the buck "needs more than **6 V** in"; the banked datasheet says **8 V** | `[datasheet R-78E5.0-1.0.pdf p.2]` |
| `-12V_ANA` | ADR 0004 says ~40 mA; `C-BULK-RAIL` says 10 mA; `FB-IN` says 10–20 mA. Datasheet build: **15.5 mA typ / 24 mA hot** | §1.2 |
| `+12V_ANA` | ADR 0004 says 45 mA; `FB-IN` says ~45 mA; `figures.yaml` implies 33 mA; `C-BULK-RAIL` says 22 mA. Datasheet build: **32.1 mA typ / 43.7 mA hot** | §1.2 |
| `D-REVPOL` row | ADR 0005's drop table books **400 mV** of Schottky; `U-BUCK`'s note books **~0.28 V**; the curve gives **0.286 V at 359 mA** | §2.4 |
| `UMBILICAL_+12V` | The `0.00044 cents` chain applies the OPA2197's PSRR to a 62 µV change on `AVDD`, but **the OPA2197 runs from ±12 V, not from `AVDD`** — the chain mixes rails. More importantly, the 120 mV of `V_f` modulation it describes exists **only in the deleted single-diode topology**; with `D1`/`D2` split it does not reach the analog rail at all. The conclusion (negligible) is right for two independent reasons and the page states neither clearly. | `[repo hardware/module/power-entry.md:74-85]` |
| `UMBILICAL_+12V` | **Where the `V_f` modulation went instead.** With the split, `D2`'s 128 mV lands on the umbilical, which feeds the instrument's REF5050 → the ratiometric breath sensor. Total series-drop modulation between quiescent and clamp-legal worst: `D2` 128 + `FB2` 29 + `R-ILIM` 18 + FET 18 + cable 125 = **318 mV** (373 mV at a 200 mΩ FET) `[calc]`. Worst-case delivered voltage at the instrument is **10.75 V** against the buck's 8 V minimum. Not a defect — but the effect moved and no page followed it. | `[calc]`, §2.4 |
| `J-UMBILICAL` | `[datasheet LT1641.pdf p.9]` asks by name for "a surge suppressor at the input" against the inductive spike from a short. `U-TVS-MODULE` is deliberately open. With `C-GATE` fitted, the FET's turn-off is 0.18 µs (§3-N3) into ~2 µH of cable → `L·di/dt` ≈ 10 V — **small, so the deferral is justified**, and now for a computed reason rather than an untested one. | `[calc]` |
| `LED-PANEL` | The page's diagnosis is right (`+12V_ANA` is live in every latching fault) and the fix does not need the deferred datasheet read | §4.8 |

---

## 6. Netlist readiness — every net on this page

The page is about to be transcribed into SKiDL, one module per schematic page. **This
page is not ready.** The circuit is correct; the *identifiers* are not.

### 6.1 Canonical net list

| # | **Canonical name** | Members | Notes |
|---|---|---|---|
| 1 | `BUS_+12V` | `J-PWR-EURO` pins 15,16 → `D1` anode, `D2` anode | the only net carrying the 393 mA total |
| 2 | `BUS_-12V` | `J-PWR-EURO` pins 1,2 → `D3` anode | |
| 3 | `BUS_+5V` | `J-PWR-EURO` pins 9,10 → `FB4` | no reverse protection, by decision (ADR 0004) |
| 4 | `PWR_GND` | `J-PWR-EURO` pins 3–8; the star origin | **see 6.2** |
| 5 | `+12V_ANA_RAW` | `D1` cathode → PTC (§4.4) → `FB1` | |
| 6 | `+12V_ANA` | `FB1` → `C1` → 7 × OPA2197 `V+`, INA828 `V+`, LM317 `IN`, `R-LED-PANEL` | |
| 7 | `+12V_SW_RAW` | `D2` cathode → `FB2` | |
| 8 | `+12V_SW` | `FB2` → `C2` → LT1641 `VCC` (pin 8), `R-ILIM` | also the `C-DECOUPLE` for `VCC` |
| 9 | `SW_DRAIN` | `R-ILIM` → LT1641 `SENSE` (pin 7), FET drain | **renamed — see 6.2** |
| 10 | `UMBILICAL_+12V` | FET source → `J-UMBILICAL` pin 3, `R-FB-HI`, `R-LED-PANEL` anode (§4.8) | |
| 11 | `LSW_GATE` | LT1641 `GATE` (pin 6) → `R-GATE-SER`, `R-GATE-COMP` | |
| 12 | `LSW_GATE_FET` | `R-GATE-SER` → FET gate | |
| 13 | `LSW_GATE_COMP` | `R-GATE-COMP` → `C-GATE` | two-pin net; keep it named, SKiDL will not |
| 14 | `LSW_TIMER` | LT1641 `TIMER` (pin 5) → `C-TIMER` | |
| 15 | `LSW_FB` | `R-FB-HI` / `R-FB-LO` junction → LT1641 `FB` (pin 2) | **renamed — see 6.2** |
| 16 | `LSW_ON` | LT1641 `ON` (pin 1) → `R-ON-HI`, `R-ON-LO`, `C-ON`, `SW-POWER` | new, §4.7 |
| 17 | `LSW_PWRGD` | LT1641 `PWRGD` (pin 3) | **currently NC. §4.2** |
| 18 | `-12V_ANA_RAW` | `D3` cathode → PTC (§4.4) → `FB3` | |
| 19 | `-12V_ANA` | `FB3` → `C3` → 7 × OPA2197 `V−`, INA828 `V−`, `R-OFFNEG` | |
| 20 | `+5V_LOGIC` | `FB4` → `C4` → 74AHCT125 `VCC` | |
| 21 | `DAC_AVDD` | LM317 `OUT` → `C-REG-OUT` → DAC `AVDD`, `R-CLR-PU`, `R-LDAC`, `TRIM-BREATH-ZERO` divider | **renamed — see 6.2** |
| 22 | `REG_ADJ` | LM317 `ADJ` → `R-REG-SET` junction → `C-REG-ADJ` | |

### 6.2 Names that are ambiguous, duplicated, or mean something else elsewhere

| Name | Problem | Fix |
|---|---|---|
| **`FB`** | Used as a net (the LT1641 feedback node) **and** as the refdes prefix for all four ferrite beads (`FB1`–`FB4`) **and** in `C-FB-PITCH` (a feedback capacitor on another page). SKiDL will accept all three and no human will notice. | Net → **`LSW_FB`**. Beads → **`FB1`–`FB4`** kept as refdes only, never as a net name. |
| **`AGND`** | **The single most dangerous name in the corpus.** It is *not a ground* — it is the in-amp's inverting input, the far end of a differential pair `[repo docs/decisions/0003-breath-sensing-path.md; repo hardware/module/power-entry.md:498-499]`. Every layout tool, every DRC and every reader will treat a net called `AGND` as a ground and tie it to the pour. | **Rename to `BREATH_RET`** before transcription. This is cheap now and unfixable after a board is made. |
| **`+12V`** | Means three different nodes: the bus pin (`BUS_+12V`), the module analog rail (`+12V_ANA`), and the umbilical output — `carrier.md:85` labels the *umbilical* node `+12V`. Any net literally called `+12V` shorts two rails across two pages. | Use the three qualified names. Ban the bare `+12V`. |
| **`SENSE`** | Collides with the LT1641 pin name and with `carrier.md`'s "sense pair"/"sense reference" language for the breath link. | Net → **`SW_DRAIN`**. The pin stays `SENSE`. |
| **`AVDD`** | Called `DAC AVDD 5.21V` here, `AVDD 5.21V` in `digital-and-supervision.md:40`, "the LM317 rail" in `breath-receive-stage.md:163`, and "5.21V DAC AVDD" in `bom.csv`. Four spellings. Also one letter from `AGND`. | **`DAC_AVDD`**, everywhere. |
| **`PWR_GND` / `DIG_GND` / analog return** | `figures.yaml`'s `dig-gnd-topology` is **DISPUTED** and its `decided_by` says the 2-layer vs 4-layer decision is upstream of it. **A SKiDL netlist must commit**: one net, or three with an explicit tie component. | **Blocking for transcription.** Decide the layer count first, or transcribe with three named nets and an explicit `NETTIE` symbol at the star so the choice is visible in the schematic rather than implied by a pour. |

### 6.3 Parts that cannot be instantiated as the BOM stands

| Gap | Detail |
|---|---|
| **`D1`, `D2`, `D3` have no BOM rows** | `bom.csv` has `D-REVPOL` qty 3. SKiDL needs one refdes per instance. The drawing's `D1`/`D2`/`D3` also collide with ADI's Figure-5 `D1` and with the `D-` prefix used by `D-JACK-CLAMP`, `D-RESP`, `D-TVS-*`. **Assign `D-REVPOL-12A` (analog), `D-REVPOL-12U` (umbilical), `D-REVPOL-N12`.** |
| **`C1`–`C4` have no BOM rows** | `C-BULK-RAIL` qty 4, three values, no assignment. **Assign `C-BULK-12A`, `C-BULK-12U`, `C-BULK-N12`, `C-BULK-5V`** with the §4.1 values. |
| **`FB1`–`FB4` have no BOM rows** | `FB-IN` qty 4. **Assign `FB-IN1`–`FB-IN4`**, and give `FB-IN2` its own requirement line at 360 mA (§2.3). |
| **The N-FET has no refdes and no row** | It lives inside `U-LOADSW`'s `part` field: `"LT1641-1CS8 + DPAK/SO-8 N-FET + sense R"`. **Three parts in one row.** SKiDL cannot instantiate it, and the SOA/`V_GS` criteria of §4.5 have nowhere to live. **Split into `U-LOADSW` (the IC), `Q-LOADSW` (the FET) and `R-ILIM` (already separate).** |
| **`R-ILIM` has no value** | `status: open`, `part: "Sense resistor, value from E6"`. Every calculation in the corpus uses **50 mΩ** and the BOM never says so. **Put 50 mΩ in the row as the pre-bench value**, with the E6 note kept. |
| **`R-SPI-PULL` cable-side `CS` pull-up has no rail** | `[repo hardware/module/digital-and-supervision.md:31]` shows `CS↑` on the cable side, and the module has no 3V3. If it goes to `+5V_LOGIC`, the instrument's ESP32 pin sees 5 V through 10 kΩ when tri-stated (≈170 µA into its clamp, survivable but undeclared). **A power-net decision, undeclared.** |
| **74AHCT125 gate 4's input has no net** | Three of four buffers used, all four enabled. §1.2. **Tie it to `PWR_GND`.** |
| **The ASCII drawing is ambiguous at `C2`** | `[repo hardware/module/power-entry.md:22]` reads `└──[D2 1N5817]──[FB2]──[C2 47µF]──┬──────── PWR_GND (star)`, which parses as *the +12 V branch connects to PWR_GND*. It is the capacitor's bottom plate, but a transcriber cannot tell. **Redraw before transcription.** |

---

## 7. For the owner

**Do these four before the SKiDL transcription:**

1. **Decide `PWR_GND` / `DIG_GND` / analog-return topology.** `figures.yaml` records it
   as DISPUTED and says the 2-layer vs 4-layer decision is upstream. Transcription
   cannot proceed without a commitment, and committing implicitly through a pour is the
   failure this project named. (§6.2)
2. **Rename `AGND`.** It is not a ground and the netlist is where that becomes
   permanent. (§6.2)
3. **Give `D1-3`, `C1-4`, `FB1-4` and the FET individual refdes and rows.** Eleven
   physical parts with no unique designators. (§6.3)
4. **Pin `C-STRIP-BULK` and add `umbilical-load-capacitance` to `figures.yaml`.** Six
   derived numbers on this page rest on a 2.2 mF that the BOM does not produce. (§5.2)

**Decisions only you can make:**

- **Widen ADR 0005's ramp spec to 50–200 ms** (§4.5). My recommendation, with the
  reasoning; it costs nothing downstream.
- **Connect `PWRGD`** (§4.2). If you do not, delete the "hard requirement" language and
  re-derive the divider from something real — because as written the divider's whole
  justification is a node that goes nowhere.
- **`AVDD` retarget** (§4.9). Note a hazard if you take it: **`5.25 V` and `set to
  5.25V` are in `figures.yaml`'s `dac-rail` `forbidden` list**, put there for an
  unrelated old rationale. If the rail is retargeted toward the centre of the DAC's
  window, the checker will fire on the *correct* new value. That entry needs rewriting
  in the same commit, not just the value.

**Three corrections that are not judgement calls** — the arithmetic is wrong and the
right answer is above:

- `r_d` = **332 mΩ** at 392 mA, not 69 mΩ, and no part carries 392 mA (§2.4, §1.1).
  This is a `figures.yaml` `value` field, so it propagates.
- Worst-case delivered output is **11.045 V**, not 11.36 V (§4.2).
- Hot-plug margin is **1.49×**, not 2.01× (§4.5). The 10 µF choice was justified by the
  2.01×; it is still the right capacitor, for a different reason.

**One thing I could not check and one document that is missing:**

- **No capacitor datasheet is banked.** `C1`–`C4`, `C-BUCK-IN` and `C-STRIP-BULK` are
  all specified only as "electrolytic", and **ESR is a load-bearing input** in two
  places: the input-LC damping (§4.3, which I have made ESR-independent) and the
  umbilical rail's HF impedance above 3 kHz (§2.1, which I have not). Adding one
  electrolytic series datasheet to the bank would close the last `[from memory]` in this
  page's impedance story.
- **No document for the rack's source impedance or the flying bus.** Everything about
  "keeping ourselves out of the rack" is reasoned against a number nobody has. It is
  probably unobtainable — Doepfer does not publish it — in which case the honest move is
  a `BLOCKED` row in `MANIFEST.csv` saying so, which is what the manifest is for.
