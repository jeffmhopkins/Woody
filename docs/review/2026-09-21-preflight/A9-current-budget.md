# A9 — Whole-system current and power budget

**Wave:** 2026-09-21 preflight. **Slice:** the total, across both boards, per
rail, and whether it is legal in a Eurorack case.
**Method:** cold. No `docs/review/**` was read. The budget below is built from
the banked datasheets first and compared with the corpus afterwards, per the
brief.

**Provenance marks.** `[datasheet <file> p.N]` = read out of a file in
`datasheets/`. `[repo <file>:<line>]` = the corpus. `[calc]` = arithmetic,
shown. `[web <url>]` = fetched this session, **not banked**. `[from memory]` =
unverified, treat as a placeholder. Unmarked claims are defects; there should be
none.

**One thing the brief got backwards, stated up front.** The brief says the LED
strips "run on raw +12 V upstream of the buck, so they are not behind the load
switch's limit." They are upstream of the **buck** — correct — but they hang off
`J-UMB` pin 3, which is the LT1641's output `[repo hardware/controller/carrier.md:§1]`.
**The strips are fully behind the 0.94 A limiter.** That matters, because under
the banked WS2815 datasheet a latched full-white strip pair alone demands 2.25 A
and trips it; see §6.

---

## 1. THE RECONCILED BUDGET

All currents in mA. Instrument-side 5 V figures are at the buck **output**
(5.00 V). `I_umb` is solved iteratively, because the 5 V branch is a
constant-power load and the arriving voltage depends on the current it draws
`[calc]`. `V_arr` is at `J-UMB` pin 3 with the rack at −5 % and typical
contact resistance (§4 gives the worst case).

| State | +12 V direct (strips + analog) | Buck A (RT board + matrix + '125) | Buck B (display board) | 5 V total | **I_umb** | V_arr | Instrument heat |
|---|---|---|---|---|---|---|---|
| **Q** quiescent — booted, radio off, all LEDs blanked | 120 | 135 | 124 | **259** | **250** | 11.00 V | 2.75 W |
| **P** typical play, ~1.5 W of light | 244 | 160 | 124 | **285** | **390** | 10.86 V | 4.24 W |
| **W** play + live config over WiFi (RX) | 244 | 160 | 214 | **374** | **437** | 10.81 V | 4.72 W |
| **W+** WiFi TX burst, instantaneous | 244 | 160 | 414 | **574** | **542** | 10.71 V | 5.81 W |
| **C1** clamp-legal worst — all 3 W to the matrix | 120 | **750** | 214 | **964** | **623** | 10.64 V | 6.62 W |
| **C2** clamp-legal worst — all 3 W to the strips | 370 | 160 | 214 | **374** | **564** | 10.69 V | 6.03 W |
| **F** clamp fails, everything latched full white | 2370 | 2426 | 204 | **2630** | **4295 demanded** | — | — |

Rack-facing totals, which is what a Eurorack case sees:

| Rail | Q | P | W | **C1 (design maximum)** | F |
|---|---|---|---|---|---|
| **+12 V** (umbilical **+** the module's own) | 283 / 295 | 423 / **435** | 470 / 482 | 656 / **668** | limiter trips at 940 |
| **−12 V** | — | **13 typ / 19 max** (`[calc]`, §2) | | | |
| **bus +5 V** | — | **~2 typ / 5.3 max** (`[calc]`, §2) | | | |

*(Each +12 V cell is "typical-silicon module / max-silicon module". §3 explains
why that single distinction resolves the corpus's two disagreeing headline
figures.)*

**The single number to quote for the module:** **+12 V, 435 mA typical play,
668 mA clamp-legal worst.** State F is a *demand*, not a draw — it is above the
limiter and the instrument latches off.

### Line items, from the documents

**Instrument, raw +12 V (upstream of both bucks, downstream of the LT1641):**

| Item | Figure | Source |
|---|---|---|
| WS2815 ×50, quiescent | 50 × 2.1 mA = **105 mA** | *"Quiescent Current 2.1mA"* `[datasheet other-semi/WS2815.pdf p.3]`, 60/m × 0.84 m `[repo docs/decisions/0014-lighting.md]` |
| WS2815 ×50, per channel at full drive | 50 × 15 mA = **750 mA** | *"RGB Channel Constant Current 15mA"* `[datasheet other-semi/WS2815.pdf p.3]` |
| WS2815 ×50, full white | 105 + 3 × 750 = **2355 mA** | `[calc]` — **disputed, see §6** |
| REF5050AIDR | 1.0 mA max, **1.2 mA** to +125 °C | `[datasheet texas-instruments/REF5050.pdf p.8, table 6.5 "REF50xxI and REF50xxAI"]` — note p.9's 340 µA is the **E** variant, a different part |
| OPA2197 (`U-BUF`, both halves) | 1.3 mA/amp max, **1.5 mA/amp** over temp → 3.0 mA | `[datasheet texas-instruments/OPA2197.pdf p.8]` |
| MPXV4006DP, sourced by the buffer off +12 V | **10 mA** max | *"Supply Current I S — — 10 mAdc"* `[datasheet other-semi/MPXV4006DP.pdf p.3]` |
| Breath buffer output + ADC divider | ~0.3 mA | `[calc]` 4.8 V into (1 k + ~21 k ∥ 25 k) |
| Two R-78E5.0 at no load | 2 × 1.5 mA | *"Quiescent Current 1.5mA"* `[datasheet discrete-and-power/R-78E5.0-1.0.pdf p.1]` |
| **Analog subtotal** | **14.5 mA** | `[calc]` 1.2 + 3.0 + 10 + 0.3 |

**Instrument, buck A (5.00 V):**

| Item | Figure | Source |
|---|---|---|
| ESP32-S3, 240 MHz, dual core 32-bit, peripheral clocks **on** | **81.3 mA** (Typ2) | Table 5-9 `[web https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf, v2.2, p.68]` — fetched via a GitHub-LFS mirror, sha256 `2d5a7cb7fd559d8d972bd88db32669c0196d23f22d7afaafb0f63d099b589a3f`. **Not banked** |
| … flash access adder | **+10 mA** | same, Table 5-9 note 3 |
| Key pull-ups, 18 closed | 3.3/(2200+100) = 1.435 mA × 18 = **25.8 mA** | `[calc]`; `R-KEY-PU` = 2k2 `[repo hardware/bom.csv]`, matches `[repo hardware/controller/carrier.md:§3]`. All 21 switch positions closed = **30.0 mA** |
| MCP3202 | **0.55 mA** max | *"Operating Current I DD — 375 550 µA"* `[datasheet other-semi/MCP3202-CI-SN.pdf p.3]` (spec'd at V_DD = 5.0 V; there is no 3.3 V row) |
| 74HC165 ×4 | 4 × 160 µA = **0.64 mA** max | *"ICC … 6 V 8 160 80 µA"* `[datasheet other-semi/74HC165.pdf p.5]` |
| QMI8658C IMU | ~1.5 mA | `[from memory]` — **no datasheet banked** |
| I²C pull-ups | ~0.7 mA | `[calc]` 2 × 3.3 V/4k7 at 50 % low |
| 74AHCT125 | 20 µA + ΔI_CC 1.5 mA/input at 3.4 V × 2 × ~50 % duty = **1.5 mA** | `[datasheet texas-instruments/SN74AHCT125.pdf p.4]` |
| 8×8 matrix, idle (drivers powered, all dark) | 64 × 0.6 mA = **38.4 mA** max | *"Quiescent Current：<0.6mA"* `[datasheet other-semi/WS2812B-2020.pdf p.4]` |
| 8×8 matrix, full white | 64 × 3 × 12 mA = **2304 mA** | *"Working Current 12mA"* `[datasheet other-semi/WS2812B-2020.pdf p.4]` — **surrogate part, blocked; see §6** |

**Instrument, buck B (5.00 V):** ESP32-S3 81.3 mA idle / 91 mA Wi-Fi RX /
**291 mA Wi-Fi TX** at 100 % duty (802.11g 54 Mbps @19 dBm; 802.11b is 340 mA)
`[web esp32-s3 datasheet v2.2 Table 5-7 p.66]`; AMOLED panel via the `BV6802`
boost, 40 mA typical / 120 mA bright `[from memory]` — **no panel datasheet
banked**, and this is the second-largest unsourced item after the matrix;
two 2 kΩ indicator LEDs + `TP4065` ≈ 3 mA `[datasheet mechanical/LILYGO-T-DISPLAY-S3-AMOLED-SCHEMATIC.pdf p.1, R10/R17/U5]`.

**Module, its own +12 V** (`[calc]`, per-item sources in §2): 12 OPA2197
amplifiers 12.0 typ / 18.0 max; INA828 0.60/0.85; LM317 branch 10.7/11.0; panel
LED 4.55; mod reference load 1.3; CV outputs 0.6; LT1641 `I_CC` 2.0/5.5; `FB`
divider 0.29; SPI pulls 0.5 → **32.5 mA typical, 42.2 mA on worst-case
silicon**, plus 60 mA if all six CV outputs are shorted to ground at once.

---

## 2. Per-rail detail, and the two rails nobody costed

### −12 V — **13 mA typical, 19 mA worst case**, not ~40 mA

`[calc]` An op-amp's quiescent current enters at V+ and leaves at V−, so the
negative rail carries the same 1.0/1.3/1.5 mA per amplifier
`[datasheet OPA2197.pdf p.8]`: 12 amplifiers = 12.0/15.6/18.0 mA. Add the
INA828 at 600 µA typ / 650 µA max / 850 µA to +125 °C
`[datasheet texas-instruments/INA828IDR.pdf p.6]`. Sink currents into patched
inputs are microamps. **Total 12.6 mA typical, 18.9 mA on worst-case silicon.**

`[repo docs/decisions/0004-cv-interface-module.md:269]` books **~40 mA**. That is
conservative rather than wrong — nothing is sized from it — but it is 2×, it is
undocumented, and `−12 V` is not in `config/figures.yaml`.

### Bus +5 V — **~2 mA typical, 5.3 mA worst case**

`[calc]` The only load is `U-LVL-MOD`, one 74AHCT125 `[repo hardware/module/digital-and-supervision.md]`.
Static `I_CC` is **20 µA max** `[datasheet SN74AHCT125.pdf p.4]`. The real term is
`ΔI_CC` = **1.5 mA max per input held at 3.4 V** (same page): `SCLK` and `MOSI`
idle low and `CS` idles at 5 V, so the term only bites while a 3.3 V driver is
holding a line high — roughly 31 % of a 250 µs frame `[repo docs/reference/latency-budget.md]`
→ 3 × 1.5 × 0.31 ≈ 1.4 mA. Add ~0.5 mA through `R-SPI-PULL`'s `CS` pull-up while
`CS` is asserted.

`[repo docs/decisions/0004-cv-interface-module.md:270]` books **~10 mA**. With
`ΔI_CC` counted that is a defensible bound rather than the 10× overestimate it
looks like from `I_CC` alone. **Keep it, and record why** — the next reviewer
who checks it against `I_CC` = 20 µA will delete it.

### The derived 5 V — **the split ADR 0005 never wrote**

`[repo hardware/controller/carrier.md:§1]` states the gap exactly: *"ADR 0005's
load table has one 5 V column and the two-regulator decision needs it split per
buck. That split is not written anywhere and it is what sizes both parts."*
Here it is:

| | Buck A (RT board + matrix + `U-LVLSHIFT`) | Buck B (display board) |
|---|---|---|
| Quiescent | 135 mA (13.5 %) | 124 mA (12.4 %) |
| Typical play | 160 mA (16.0 %) | 124 mA (12.4 %) |
| Play + WiFi RX | 160 mA | 214 mA (21.4 %) |
| Play + WiFi **TX burst** | 160 mA | **414 mA (41.4 %)** |
| **Clamp-legal worst (3 W to the matrix)** | **750 mA (75.0 %)** | 214 mA |

`[repo docs/decisions/0005-power-architecture.md:208-212]` says of the two-buck
split that *"neither is near its rating."* **Buck A is at 75 % of a 1 A part in
the state the clamp explicitly permits.** `carrier.md`'s independently-derived
68–78 % is confirmed. ADR 0005's sentence should go.

### The instrument's 3V3 — no converter, and the load is fine

`[repo docs/decisions/0005-power-architecture.md]`'s claim that 3.3 V needs no
converter holds `[calc]`: the real-time board's `ME6217C33M5G` carries
81.3 + 10 (ESP32-S3) + 25.8 (pull-ups) + 0.55 + 0.64 + 1.5 + 0.7 = **120 mA**
against a printed 800 mA `[datasheet other-semi/ME6217C33M5G.pdf p.4]`.
Two caveats, both from that datasheet: the 800 mA requires
`VIN ≥ VOUT(T) + 1.0 V` = 4.3 V (we have ~4.78 V, §5), and it is
*guaranteed by design*, not production tested — `[repo config/figures.yaml matrix-led-current]`
already records this.

### The module's 5.21 V — minimum load is met, by the divider alone

`[calc]` `R-REG-SET` 150 Ω/475 Ω draws 1.25/150 = **8.33 mA** through the
divider, on top of the DAC8568's 2.0 mA max (*"Normal mode, internal reference
switched on, AVDD = 3.6 V to 5.5 V: 1.25 typ / 2.0 max mA"*
`[datasheet texas-instruments/DAC8568CIPW.pdf p.5]`) and ~0.3 mA of output
current into `R-BIAS-DAC`. **Total ≈ 10.7 mA.**

The LM317L's *"Minimum output current to maintain regulation: 1.5 typ / 2.5 max
mA"* `[datasheet texas-instruments/LM317LZ.pdf p.5]` is therefore met **by the
divider on its own**, with 3.3× margin even against the 3.5 mA that
`[repo hardware/bom.csv U-REG-DAC]` warns other manufacturers' LM317L parts
specify. This closes the hazard that row raises. `I_ADJ` is 50 µA typ / 100 µA
max (same page), which is why `R-REG-SET`'s note about halving the `I_ADJ` term
is right.

---

## 3. THE THREE CORPUS FIGURES, RECONCILED

### `~404 mA typical (45 mA module + 359 mA instrument)` and `392 mA module total`

These are **the same quantity stated twice with different silicon assumptions,
and neither document says which.**

- `[repo docs/decisions/0004-cv-interface-module.md:267]`: *"+12 V | **~404 mA
  typical** (45 mA module incl. the DAC regulator + **359 mA** instrument)"*.
- `[repo hardware/module/power-entry.md:89]`, `[repo config/figures.yaml diode-split-rationale]`
  and `[repo hardware/bom.csv FB-IN]`: *"the 392 mA module total"*.

`[calc]` 404 − 359 = **45**. 392 − 359 = **33**. Both differences are the
module's own +12 V draw, and my independent build from the datasheets gives
**32.5 mA on typical silicon and 42.2 mA on maxima** — so 392 is the typical
build and 404 is the worst-case build. Neither is wrong; they are simply not the
same number, and three files cite 392 while one cites 404, all of them calling it
"the module total on +12 V".

**This is precisely the failure `CLAUDE.md` exists to stop, and it is invisible
to `tools/check-staleness.py`** because neither value is a tracked figure. Only
`umbilical-current` (359 mA) is registered, and its `false_positive_note` goes
out of its way to protect 392 mA as *"a DIFFERENT quantity"* — which it is, from
359, but not from 404.

> **Recommendation.** Add `module-plus12-total` to `config/figures.yaml`, owner
> `docs/decisions/0004-cv-interface-module.md`, value **`435 mA`** (typical play,
> worst-case silicon), with the clamp-legal worst as a second registered figure
> at **`668 mA`**. Put `392 mA` and `404 mA` in its `forbidden` list — with a
> `false_positive_note`, because `392 mA` also legitimately appears in
> `ferrite-bias-impedance`'s derivation, where what it actually means is "the
> current FB2 carries".

### `928 mA clamp-legal worst case`

**Essentially correct, and it is the only one of the three that is.** `[calc]`
My datasheet build of the same state is **964 mA** — 3.9 % apart. Decomposed,
the corpus figure is 600 mA (3 W ÷ 5.00 V of matrix) + 328 mA of dev boards;
mine is 628 mA (3 W ÷ **4.78 V**, the real LED-rail voltage after `D-USBOR`,
§5) + 336 mA of dev boards.

**But it is counted at the wrong node and in the wrong column.** It is a
*5 V rail total*, not a system total, and it is not what the module or the rack
sees — the same state is **623 mA on the umbilical and 668 mA on the rack's
+12 V**. `[repo hardware/controller/carrier.md:146]` already cites it as
"Clamp-legal worst on the 5 V rail, total", which is the correct reading;
`[repo hardware/bom.csv U-BUCK]`'s *"1A each clears the 928mA clamp-legal worst
case that 1A shared does not"* is also correct. Nothing here needs changing
except that 928 should be registered as a figure too, since three files reason
from it.

### The two figures that do move

| Corpus | Datasheet build | Verdict |
|---|---|---|
| Quiescent 5 V rail **180 mA** `[repo 0005:157]` | **259 mA** | **44 % low** |
| Typical play 5 V rail **226 mA** `[repo 0005:158]` | **285 mA** | **26 % low** |
| Typical play 12 V direct **248 mA** `[repo 0005:158]` | **244 mA** | ✅ agrees |
| Quiescent 12 V direct **123 mA** `[repo 0005:157]` | **120 mA** | ✅ agrees |
| Umbilical typical **359 mA** (`umbilical-current`) | **390 mA** | **8 % low** |
| Clamp-legal 12 V direct **119 mA** `[repo 0005:160]` | **120 mA** | ✅ agrees |
| Body heat 2.4 / 4.1 / 6.5 W `[repo 0005]` | 2.75 / 4.24 / 6.62 W | ✅ agrees within 15 % |

**The single cause of every low row is the ESP32-S3.** The only MCU current in
the corpus is *"ESP32-S3 40–80 mA"*, and it is in the **superseded battery
section** of `[repo docs/decisions/0005-power-architecture.md]` — a paragraph
the ADR itself marks as historical. The datasheet's own table for the mode this
design actually runs (240 MHz, both cores, peripheral clocks enabled) is
**81.3 mA**, and flash access adds 10 mA
`[web esp32-s3 datasheet v2.2 Table 5-9 p.68]`. Two boards, so the error is
~80 mA on the 5 V rail before anything else is counted.

**And the corpus already contradicts itself about this, in one sentence.**
`[repo docs/decisions/0014-lighting.md]`: *"The matrix shares the 1 A R-78E5.0
with both dev boards, which take roughly **330–400 mA** between them."* ADR
0005's typical-play 5 V row is **226 mA including the matrix's 38–64 mA of
idle**, i.e. 162–188 mA for both boards. Those two accepted decisions disagree by
a factor of two about the same quantity, and the datasheets side with ADR 0014.

> **Recommendation.** ADR 0005's load table is the owning document for five
> numbers that three other files derive from, and three of its rows are low.
> Rebuild the table from the line items in §1 and register the +12 V column.
> E6 supersedes all of it, per the ADR's own note — but E6 is a milestone away
> and `R-ILIM`, `C-TIMER`, `C-GATE` and the `FB` divider are all sized against
> these numbers *now*.

---

## 4. THE UMBILICAL AS A VOLTAGE-DROP PROBLEM

### The chain, at the clamp-legal worst case

Rack at −5 % = 11.40 V. Every element between the bus pin and the buck's input
pin, in order `[repo hardware/module/power-entry.md]`, `[repo hardware/controller/carrier.md:§1]`:

| Element | Value | Drop at **623 mA** |
|---|---|---|
| `D2` 1N5817 | V_f(0.623 A) = **0.363 V** | −363 mV |
| `FB2` ferrite, DCR | 0.080 Ω max `[datasheet discrete-and-power/MI1206K601R-10-ferrite-bead.pdf]` | −50 mV |
| `R-ILIM` | 50 mΩ | −31 mV |
| N-FET `R_DS(on)` | 50 mΩ **assumed — the FET is TBD** | −31 mV |
| module trace + IDC | ~20 mΩ `[from memory]` | −12 mV |
| 4 × mated etherCON contacts | **< 50 mΩ each** `[datasheet connectors/NE8FDP-DATASHEET.pdf p.2]` | −125 mV |
| 4 m of Cat5 conductor, 24 AWG stranded at 45 °C | 0.395 Ω `[calc]` | −246 mV |
| **at `J-UMB` pin 3** | | **10.54 V** |
| `L-BUCK-IN` DCR | ~150 mΩ — **not specified in `bom.csv`** | −93 mV |
| **AT THE BUCK INPUT** | | **10.45 V** |
| against the R-78E5.0-1.0's **8 V** minimum | | **margin 2.45 V** |

**The V_f figure is read off the banked curve at the real current, as the brief
asks.** `[calc]` A three-parameter fit `V_f = 0.2990 + 0.06893·ln(I) + 0.1550·I`
passes exactly through all three points the repo has digitised or quoted —
0.240 V at 245 mA and 0.360 V at 612 mA from Fig. 2 of
`[datasheet discrete-and-power/1N5817.pdf]`, and the guaranteed 0.450 V max at
1.0 A on p.1. It gives **0.298 V at 400 mA, 0.363 V at 623 mA, 0.440 V at
940 mA** — all well above the 0.30 V nominal the brief warns against, and
above the *"~0.3–0.4 V"* of `[repo hardware/bom.csv D-REVPOL]`.

### Sensitivity — the margin never closes, but it is half what the corpus claims

| Case | At the buck input | Margin over 8 V |
|---|---|---|
| Typical play, 390 mA, benign assumptions | 10.86 V | 2.86 V |
| Clamp-legal worst, documented maxima (above) | 10.45 V | 2.45 V |
| …with a 200 mΩ FET, feedthrough etherCON at both ends, 0.30 Ω inductor | 10.14 V | 2.14 V |
| …with a **26 AWG** patch lead at 45 °C | 10.18 V | 2.18 V |
| Held at the 0.94 A current limit | 10.07 V | 2.07 V |

**Verdict: the 8 V minimum is not binding, under any assumption I can justify.**
`[repo hardware/bom.csv U-BUCK]`'s conclusion stands. Its *number* does not: it
says *"worst case at the buck input is ~10.96 V … so ~3 V of margin"*. The real
worst case is **10.14–10.45 V and 2.1–2.5 V**, because that row's chain omits
three elements that are in its own drawings — **`FB2`'s 80 mΩ, the etherCON
contact resistance, and `L-BUCK-IN`'s DCR** — and uses a nominal 0.28 V for a
Schottky that drops 0.36 V at the current in question.

Three sub-findings worth filing separately:

1. **`CABLE-UMB` does not specify a gauge.** `[repo hardware/bom.csv CABLE-UMB]`
   says *"Cat5e STP patch lead, STRANDED, ~2 m"*. ADR 0005 assumes 24 AWG
   `[repo docs/decisions/0005-power-architecture.md:91]`. Most stranded Cat5e
   patch cords are 26 AWG `[from memory]`, which is **0.629 Ω round trip at
   45 °C against the assumed 0.34 Ω** `[calc]` — nearly double. It still clears
   8 V, but it is 150 mV of unbudgeted drop and it is a consumable the user
   replaces. **Put the gauge in the BOM row.**
2. **etherCON contact resistance is specified and is large.** *"Contact
   resistance < 50 mΩ"* `[datasheet connectors/NE8FDP-DATASHEET.pdf p.2]`. Four
   mated contacts in the loop is 0.200 Ω worst case — **comparable to the whole
   cable**. If the D-series **feedthrough** variant is used at both ends (it is
   an RJ45 on both faces, as `[repo hardware/bom.csv J-UMBILICAL-CABLE]` notes),
   it is eight contacts and 0.400 Ω. The variant choice is currently "TBD at
   E12/M7" and is being treated as mechanical; **it is an electrical decision
   worth ~250 mV.**
3. **`L-BUCK-IN` has no DCR specification.** `[repo hardware/bom.csv L-BUCK-IN]`
   is *"10–47 µH power inductor, ≥1 A"*. Parts in that range span 0.05–0.4 Ω
   `[from memory]`, i.e. 30–250 mV at the clamp-legal current, and it sits
   directly in front of the pin whose 8 V minimum the whole analysis is about.
   Specify **DCR ≤ 0.15 Ω** in the row.

### `PWRGD` — **the margin the page computes is not there**

`[repo hardware/module/power-entry.md, "Sizing the FB divider"]` places the
nominal `PWRGD` release at 10.49 V with a 10.05–10.93 V worst-case window, and
justifies it: *"Eurorack +12 V at −5 % is 11.4 V; R-ILIM at 50 mΩ drops exactly
20 mV at 0.4 A, and the FET drops about the same … so the worst-case output is
~11.36 V … ~0.4 V worst-case margin."*

**That derivation omits `D2` and `FB2`, which its own schematic puts upstream of
the LT1641's `VCC` and `SENSE`.** `[calc]` The real switch output is:

```
  0.400 A  11.40 − 0.298 − 0.032 − 0.020 − 0.020 = 11.03 V   (not 11.36 V)
  0.623 A  11.40 − 0.363 − 0.050 − 0.031 − 0.031 = 10.93 V
  0.940 A  11.40 − 0.440 − 0.075 − 0.047 − 0.047 = 10.79 V
```

Against the page's own worst-case `PWRGD` release of **10.93 V**, the margin at
the clamp-legal worst case is **0.00 V**, and at the current limit it is
**−0.14 V** — `PWRGD` would re-assert while the part is regulating normally.

**Nothing breaks today**, because `PWRGD` is drawn connected to nothing and the
presence comparator that used to use it is deleted
`[repo hardware/module/digital-and-supervision.md]`. It matters because (a) the
page's proposed cheapest-fix — *"drive it from the LT1641's TIMER node, or from
the gate"* — invites someone to use `PWRGD` instead, and (b) the **same divider**
sets the foldback knee, so the ratio is not free to move. `[calc]` The knee is
fine (V_FB = 0.5 V at V_OUT = 3.99 V, and nothing in the start sequence cares),
so the fix is to re-place `PWRGD` lower: a nominal 9.5 V point gives
`R-FB-HI/R-FB-LO` = 6.23, and moves the foldback knee to 3.62 V — harmless.
**Raised, not decided; it is the `FB`-divider owner's call.**

---

## 5. EURORACK LEGALITY

### What the rails can supply

`[repo README.md:69-72]` removes rack *capacity* from scope: *"The target rack
has a generous supply and a regulated +5 V rail … Rack current budget is
therefore not a design constraint here."* I accept that and do not re-derive it.
**What it does not remove is the connector and the bus board**, which are
physical limits no supply size fixes, and the README says so itself.

`[from memory]` For calibration only, not as a constraint: Eurorack supplies
in common use run 1.2–4 A on +12 V, and 1.5 A per rail is the small end.
**668 mA is 17–56 % of one rail.** That is a large module but not an absurd one.

### The connector and the ribbon — both legal, with margin

| Element | Rating | Our worst case | Margin |
|---|---|---|---|
| 16-pin boxed header, 3M 303 series | **1 A per contact** `[datasheet connectors/3M-303-SERIES-BOXED-HEADER.pdf p.1]` | 668 mA over **two** +12 V contacts = 334 mA each | **3.0×** |
| 16-pin boxed header, Würth WR-BHD | **3 A max**, contact resistance 20 mΩ max `[datasheet connectors/WR-BHD-61201621621.pdf p.2]` | 334 mA each | 9× |
| etherCON contact | **1.5 A per contact** `[datasheet connectors/NE8FDP-DATASHEET.pdf p.2]` | 623 mA normal, 940 mA at the limit, on **one** conductor each way | 1.6× at the limiter |
| Ribbon conductor, 28 AWG | ~1 A `[from memory]` | 334 mA | 3× |

**The etherCON is the tightest, and the load switch is correctly placed under
it.** `[calc]` The LT1641's limit spread is 0.78–1.10 A
(`V_SENSETRIP` 39/47/55 mV ÷ 50 mΩ, `[datasheet discrete-and-power/LT1641.pdf p.2]`),
so the **worst-case trip current is 1.10 A = 73 % of the 1.5 A contact rating**.
That is the right answer and it is worth writing down as the reason the limit is
1.0 A-class rather than 1.5 A — ADR 0005 reaches it from above ("bracketed by
the connector") without doing the arithmetic against the spread.

`[repo hardware/bom.csv J-PWR-EURO]` does not name which header. **If it is the
3M part, it is a 1 A contact carrying 334 mA at the clamp-legal worst and ~500 mA
if the limiter is regulating.** Still legal, but the Würth part is banked, is
3 A, and costs the same — **name it.**

### Bus-board fuses

`[from memory]` Doepfer-style passive bus boards have no per-slot protection;
Intellijel, 4ms and Befaco boards commonly fit per-rail or per-slot resettable
fuses in the 1–1.5 A class. **No bus-board document is banked and the corpus
names none.** If the target case fits 1 A per-slot protection, our clamp-legal
668 mA sits at 67 % of it — legal, but the **inrush** below is what would trip
it, and a polyfuse of that class would nuisance-trip on a case power-on.
**This is the one Eurorack question I cannot close from documents. It needs one
line in the README's design-scope paragraph saying what the target case's bus
board is.**

### Inrush at hot-plug

**Two different events, and the corpus only analyses the second.**

1. **Plugging the module's ribbon into a live case.** `[calc]` The module's entry
   bulk charges through `D1`/`D2` with no limiting at all — that path has no
   load switch in it. The stored energy is small (½CV² = 14 mJ at 194 µF) but
   the peak current is set only by ESR and the bus-board impedance, so it is tens
   of amps for tens of microseconds. That is the ordinary Eurorack hot-plug arc
   and everyone has it; `[repo hardware/module/power-entry.md, "Still open"]`
   flags it as *"case-wide inrush at rack power-on"*.
   **But the capacitance is stated two different ways.** That page says *"Entry
   bulk is 4 × 47 µF"*; `[repo hardware/bom.csv C-BULK-RAIL]` says
   *"100uF (+12V) / 47uF (−12V, +5V) 25V"*, qty 4. **The +12 V node is either
   47 µF or 100 µF depending on which file you read**, and inrush is the one
   thing that depends on it. Node-indexed to `C1`/`C-BULK-RAIL`.
2. **Live-inserting the umbilical.** Handled, and handled well
   `[repo hardware/module/power-entry.md]`: 47.5 ms entirely in current limit at
   ≤0.94 A into 2.2 mF, against a worst-case fault timer of 95.6 ms — 2.01×.
   I re-derived the 47.5 ms and agree. **One gap:** RJ45 contacts have no mating
   sequence. If `PWR_GND` (pin 6) makes last, the inrush return finds `DIG_GND`
   (pin 8) or `AGND` (pin 2) instead — up to 0.94 A through the SPI return or
   through an in-amp input. Contact skew on an RJ45 is sub-millimetre so this is
   microseconds, but `AGND` terminates on the INA828's `IN+` and two 1 MΩ
   resistors `[repo docs/decisions/0004-cv-interface-module.md]`, which is not a
   current path. **Worth one sentence and possibly a clamp; nobody owns it.**

### Is the module a good citizen?

**Yes, with two asterisks.** It draws 435 mA typical on +12 V — about 4–10× a
normal module but inside every connector rating; it current-limits its own
largest load at the source; it latches rather than retrying; and it keeps its own
switching load off the bus behind `D2` + `FB2` + 147 µF. The asterisks: its entry
bulk is 2–5× the surveyed norm and adds to case-wide inrush, and **`FB2` is not
doing the filtering job it is specified for** — at 623 mA the Laird part reads
~125 Ω, not 600 Ω `[calc, interpolating the bias curve at 500 mA → 157 Ω and
1000 mA → 72 Ω, datasheet discrete-and-power/MI1206K601R-10-ferrite-bead.pdf]`.
`[repo config/figures.yaml ferrite-bias-impedance]` already records this at 359
and 392 mA (~280–310 Ω and ~245–275 Ω); **the clamp-legal worst case is a further
2× down and that figure's note should carry it**, because keeping the
instrument's buck hash out of the rack is the job it was bought for.

---

## 6. THE MATRIX, THE STRIPS, AND WHAT IS STILL UNKNOWN

### Two corrections to `matrix-led-current`'s "supersedes the constraint"

`[repo config/figures.yaml matrix-led-current]` records, and ADR 0014 repeats:
*"THE 1 A R-78E5.0 IS NOT WHAT STOPS THE MATRIX FIRST. All 64 LEDs draw through
one B5819WS Schottky in SOD-323 … ~283 mA at a 60 °C interior. Behind it the
ME6217C33M5G LDO's printed 800 mA…"*

**Both halves of that topology claim are wrong, and the banked schematic says
so.** `[datasheet mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf p.1]`:

1. **The header's `5V` pin is on `VCC_5V`, downstream of `D1`.** The net that
   contains `D1` pin 2 (cathode), `U49` `ME6217` pin 1 (`VIN`) and pin 3 (`EN`),
   `C3`/`C4`/`C5`, `R3`, and all 64 LED `VDD` pins **also contains `P1` pin 1**.
   Cross-checked by pin arithmetic: `P1` pins 4–10 are IO7…IO1, 11/12 are RX/TX,
   13–20 are IO40…IO33, leaving pins 1/2/3 = 5V/GND/3V3 — exactly the vendor
   pinout, whose manifest note records *"Left row top-to-bottom 5V, GND, 3V3(OUT)
   … the board is fed from 5V"* `[datasheet MANIFEST.csv, WAVESHARE …-pinout.png]`.
   **So when the carrier feeds the `5V` pin, `D1` is reverse-biased and carries
   nothing.** The B5819WS limit applies **only on the bench over USB**.
2. **The `ME6217` never carries LED current at all, in any configuration.** Its
   `VIN` is on `VCC_5V` — the *same node* as the LED array, in parallel with it,
   not in series behind it. The manifest's own extraction says this
   (*"pin 1 VIN from VCC_5V"*); `figures.yaml`'s summary of it inverted the
   topology.

**Consequence.** The binding part for the matrix is back to being the
**R-78E5.0** — plus one thing nobody has named: **the `5V` header pin, its
0.1-inch contact and the board's `VCC_5V` trace now carry the full LED current**
(628 mA at the clamp-legal worst). A 2.54 mm header contact handles that easily;
the trace width is unknown and Waveshare never intended that pin as a 600 mA
feed.

**And a live bench hazard this creates.** `[calc]` A clamp-legal 3 W full field
is 628 mA. Over USB that is 628 mA × ~0.46 V = **289 mW in the B5819WS against
200 mW at 25 °C and 130 mW at a 60 °C interior** — so **E1, measured over USB at
a state the instrument runs continuously, will cook the diode.** It is also over
a 500 mA USB budget. **Power the board from the `5V` pin for E1, not from USB**,
and if both are connected `D1` conducts from `VBUS` and USB back-feeds the
array anyway.

ADR 0014's *conclusion* — a hard, non-configurable brightness cap — survives all
of this untouched, on the thermal argument it already prefers.

### What being `blocked` actually costs the budget: much less than it looks

**The clamp is denominated in watts, and watts is what the budget needs.**
`[repo docs/decisions/0014-lighting.md]`: *"A single instrument-wide lighting
budget of ~3 W, summed across both strips and the matrix, enforced in firmware
before any write."* Three watts is three watts whatever the per-channel current
turns out to be. `[calc]` So:

- **Every clamp-legal row in §1's table is insensitive to `matrix-led-current`.**
  3 W ÷ 4.78 V = 628 mA on the 5 V rail, or 3 W ÷ 12 V = 250 mA on raw +12 V,
  regardless of whether a channel is 5, 12 or 19 mA.
- **What the blocked figure does change is (a) how bright a clamp-legal field
  looks and (b) the fault case.** ADR 0014 claims 3 W is *"a full field at around
  60 % of one channel"*; at 12 mA/channel it is **30 %**, at 19 mA it is 19 %.
  And the fault case moves from 960 mA to 2304–3648 mA.
- **Both of those move in the safe direction.** A brighter-per-milliamp part
  makes the clamp *more* generous visually than assumed; a hungrier one makes
  the fault trip the limiter *harder*. Neither can make a clamp-legal state
  illegal.

> **The budget's confidence is therefore bounded by the clamp being enforced,
> not by the datasheet being found.** Stated as a bound: **provided the firmware
> clamp runs, `matrix-led-current` can be anywhere in 960–3648 mA without moving
> any number in §1's table by more than 0 mA.** With the clamp not running, the
> 5 V rail demand spans 964 mA (5 mA/ch) to 3652 mA (19 mA/ch) and buck A is over
> its rating in every one of them. **That is the honest statement of what E1
> buys: not the budget, but the size of the hole the clamp is plugging.**

### A second figure that should be blocked and is not: the WS2815 strips

`[repo docs/decisions/0014-lighting.md]`'s strip table (30/m 0.50 A, 60/m 1.01 A
at full white) implies **20.2 mA per LED**, which `[calc]` is 6.73 mA per
channel. **The banked datasheet says 15 mA per channel**
`[datasheet other-semi/WS2815.pdf p.3]` — 2.23× more, giving 45 mA/LED and
**2250 mA for 50 LEDs**. There is no source in the corpus for 20.2 mA.

I am **not** proposing 45 mA/LED as settled, and the reason is a consistency
check the datasheet fails `[calc]`: the WS2815's drivers are linear sinks from
12 V, so 15 mA/channel at a ~2–3.2 V LED forward voltage puts **0.41 W inside a
5050 package** at full white — implausible for that package, and inconsistent
with the strip-level 18 W/m that assembled 60/m WS2815 tape is commonly sold
against `[from memory]`, which implies ~25 mA/LED. The three candidates are
therefore **20.2 mA (corpus, unsourced), ~25 mA (strip-level, [from memory]),
45 mA (component datasheet, banked)**.

> **Recommendation.** Add `strip-led-current` to `config/figures.yaml` with
> `status: blocked`, `candidates` as above, `decided_by: "a current probe at E6,
> not another document"`, and `blocked_on: datasheets/MANIFEST.csv — WS2815 LED
> strip` — which is **already a BLOCKED row** reading *"STRIP GEOMETRY NOT
> ESTABLISHED … no strip drawing, DXF or spec sheet for 30/m or 60/m WS2815
> exists"* `[datasheet MANIFEST.csv]`. The matrix got this treatment and the
> strips did not, and they are the same defect: a component datasheet that does
> not settle what an assembled tape draws.

**What *is* settled for the strips, and is worth citing rather than re-deriving:
quiescent is 2.1 mA per LED, so 50 LEDs idle at 105 mA on raw +12 V**
`[datasheet other-semi/WS2815.pdf p.3]`. That confirms
`[repo docs/decisions/0005-power-architecture.md]`'s *"roughly 120 mA of strip
quiescent draw"* and its 119/123 mA table rows, which are the best-sourced
numbers in the load table.

### Other holes in the bank, named

- **No Espressif document is banked.** The two largest digital loads in the
  budget have no datasheet in `datasheets/`. I fetched v2.2 this session
  `[web …/esp32-s3_datasheet_en.pdf]` via a GitHub-LFS mirror (`espressif.com`
  is still 403 at the egress proxy, `media.githubusercontent.com` is not).
  **It should be banked**, with the mirror URL recorded honestly as the source.
- **No AMOLED panel datasheet**, so buck B's largest variable load is `[from
  memory]`. The `BV6802` boost and its `ELVDD`/`ELVSS` rails are visible on the
  banked LilyGO schematic; the panel behind `P8` is not documented anywhere.
- **No QMI8658C datasheet**, ~1.5 mA `[from memory]`.
- **`L-BUCK-IN` and `C-BULK-DISP` have no part numbers**, and the first one is
  in the umbilical drop chain (§4).

---

## 7. THERMAL

**Where the watts go, at the clamp-legal worst case (6.62 W in the instrument,
~0.55 W in the module):**

| Dissipator | Power | Note |
|---|---|---|
| WS2815 strips + matrix (the clamp) | **3.00 W** | by definition — the clamp is a power budget `[repo 0014]` |
| WS2815 quiescent, 50 ICs | **1.26 W** | 105 mA × 12 V `[calc]`, and it is on whenever the rack is |
| Both ESP32-S3 boards + AMOLED | ~1.8 W | `[calc]` 374 mA × 5 V less the LDO splits |
| Buck A at 750 mA out (3.75 W) at ~90 % | **0.42 W** | `[calc]`; buck B at 214 mA ≈ 0.12 W |
| `ME6217` LDO, RT board | **0.18 W** | (4.78 − 3.3) × 120 mA `[calc]`; SOT-23-5 at ~210 °C/W `[repo figures.yaml]` → **+37 K junction over the interior** |
| `D-USBOR` ×2 | ~0.15 W | `[calc]` 0.3 V × (0.75 + 0.21) A worst case |
| **Module:** `D2` 1N5817 | **0.23 W** | 0.363 V × 0.623 A `[calc]`. At the 0.94 A limit, 0.41 W against the 0.45 W-at-1.0 A envelope `[repo bom.csv D-REVPOL]` — transient only, ≤95.6 ms |
| **Module:** `LM317LZ` | **0.070 W** | (11.8 − 5.21) V × 10.7 mA `[calc]`; TO-92 R_θJA up to 149.4 °C/W `[datasheet texas-instruments/LM317LZ.pdf p.4]` → **+10 K**. Confirms `[repo bom.csv U-REG-DAC]`'s "~90 mW" |
| **Module:** `R-FB-HI/LO` divider | 3.5 mW | `[repo hardware/module/power-entry.md]` |

At `[repo docs/decisions/0014-lighting.md]`'s bounding **~3 K/W**, 6.62 W is a
**~20 K interior rise**, consistent with the ADR's own 10–20 K at ~5 W. The
instrument's `+37 K` `ME6217` junction then sits at roughly
25 + 20 + 37 = **82 °C** in a 25 °C room — fine against a 150 °C T_J max
`[datasheet other-semi/ME6217C33M5G.pdf p.4]`, and worth stating because it is
the hottest small package in the body and nobody has costed it.

### The buck modules against the real derating curve

`[datasheet discrete-and-power/R-78E5.0-1.0.pdf p.3, derating graph]`, as read in
`[repo hardware/bom.csv U-BUCK]`: **100 % of rated load to +60 °C ambient, then
linear to 60 % at +85 °C**, natural convection, hard cutoff. `[calc]` The slope
is −1.6 %/K, so **74.8 % is permitted up to 75.8 °C** — and "ambient" for a
module inside the body means interior temperature, i.e. room + ~20 K. A 30 °C
room gives a 50 °C interior and **26 K of headroom**. Compliant, and
`bom.csv`'s "~14 points of margin at 65 °C" is confirmed.

Two efficiency notes `[datasheet R-78E5.0-1.0.pdf p.1, selection guide]`:
**93 % at min V_in (8 V) and 85 % at max V_in (28 V)** for the 5.0 V part. That
**confirms** `[repo docs/decisions/0005-power-architecture.md]`'s correction
that *"85 % is the 28 V-input figure"* and that ~90 % is right at 12 V — linear
interpolation gives 91.4 % at 12 V `[calc]`. **The unread part is the
efficiency-vs-load curve on p.2**, which is vector art with no extractable
values; at buck A's typical-play 16 % load the efficiency is materially below
93 % `[from memory]`, which makes the typical-play umbilical figure slightly
optimistic and the clamp-legal one (75 % load) accurate.

### The FET during the ramp — **the page's peak is 1.9× low**

`[repo hardware/module/power-entry.md, "What sizes the FET"]`: *"peak fault
dissipation is ~4 W at V_out ~ 4 V."*

`[calc]` Using the page's own foldback law (`I = 0.240 + 0.1754·V_OUT`, flat at
0.940 A above V_OUT = 3.99 V):

```
  V_OUT = 0      I = 240 mA   P = 12.00 × 0.240 = 2.88 W
  V_OUT = 2 V    I = 591 mA   P = 10.00 × 0.591 = 5.91 W
  V_OUT = 3.99 V I = 940 mA   P =  8.01 × 0.940 = 7.53 W   ← peak
  V_OUT = 8 V    I = 940 mA   P =  4.00 × 0.940 = 3.76 W
```

dP/dV is positive throughout the foldback region (the unconstrained maximum sits
at V_OUT = 5.32 V, beyond the 3.99 V knee), so the peak is **at the knee and is
7.53 W**, not 4 W. Energy over the 47.5 ms hot-plug is **~0.21 J** `[calc]`,
against the page's 0.158 J — which is ½CV², the energy into the capacitor, and
does not include the instrument's own 360 mA load during the start.

**Thermally this is still nothing** (a DPAK at 0.6 °C/W for 50 ms is a 4.5 K
rise), and the page is right that the real criterion is Spirito / linear-mode
SOA. **But the SOA condition it hands the buyer is wrong by a factor of two.**
The correct requirement is: **single-pulse SOA covering 0.94 A at V_DS = 8.0 V
for 30 ms, and 0.59 A at V_DS = 10 V for 17 ms** — not "12 W at 12 V for 10 and
100 ms". The corrected numbers are *easier* to meet at the high-V_DS end and
*longer* in time, and both matter to the part choice. `U-LOADSW`'s FET is still
TBD, so this can be fixed before it costs anything.

---

## 8. Findings, node-indexed

| # | Node / ref | Finding | Severity |
|---|---|---|---|
| A9-1 | `J-PWR-EURO` / ADR 0004 : ADR 0005 | `404 mA` and `392 mA` are the same quantity on typical vs worst-case silicon; four files cite them interchangeably; neither is a tracked figure | **High** — it is the number a rack integrator reads |
| A9-2 | ADR 0005 load table, 5 V column | Quiescent (180 mA) and typical (226 mA) are 26–44 % low; the cause is an ESP32-S3 figure taken from the ADR's own superseded battery section | **High** |
| A9-3 | ADR 0005 : ADR 0014 | ADR 0014 says the two dev boards take 330–400 mA; ADR 0005's typical row leaves them 162–188 mA. Datasheets side with 0014 | **High** — two accepted ADRs, factor of two |
| A9-4 | `P1-1` / `D1` B5819WS / `U49` | The `5V` header pin is on `VCC_5V`, so `D1` is bypassed when fed from the carrier, and the `ME6217` is in parallel with the LED array, not behind it. `figures.yaml`'s "supersedes the constraint" note inverts both | **High** — a finding filed as handled |
| A9-5 | `R-FB-HI`/`R-FB-LO` | The `PWRGD` margin derivation omits `D2` and `FB2`; real margin is 0.00 V at clamp-legal and −0.14 V at the limit | **Medium** — `PWRGD` is unconnected today |
| A9-6 | `U-LOADSW` FET | Peak ramp dissipation is 7.53 W at V_DS = 8 V, not ~4 W; the SOA condition given to the buyer is wrong | **Medium** — FET still TBD |
| A9-7 | `LED-SIDE` | WS2815 full-white current has no source; datasheet says 15 mA/ch (2.25 A for 50), corpus implies 6.73 mA/ch (1.01 A). Needs a `blocked` figure like the matrix | **Medium** |
| A9-8 | `CABLE-UMB`, `J-UMBILICAL`, `L-BUCK-IN` | Gauge unspecified, etherCON contact resistance (<50 mΩ each, documented) uncounted, inductor DCR unspecified — together 0.2–0.5 V of unbudgeted drop; `bom.csv`'s "~10.96 V, ~3 V of margin" is really 10.14–10.45 V and 2.1–2.5 V | **Medium** — conclusion survives |
| A9-9 | `C1` / `C-BULK-RAIL` | `power-entry.md` says 4 × 47 µF; `bom.csv` says 100 µF on +12 V. Inrush depends on it | **Low** |
| A9-10 | `FB2` | At the clamp-legal 623 mA the bead reads ~125 Ω, not the ~280–310 Ω `figures.yaml` records at 359 mA. Extend that note to the real worst case | **Low** |
| A9-11 | `J-UMB` pins 6/8/2 | RJ45 has no mating sequence; if `PWR_GND` makes last the inrush returns through `DIG_GND` or `AGND`. Unowned | **Low** |
| A9-12 | `J-PWR-EURO` | The header is not named; the banked 3M part is **1 A/contact**, the banked Würth part is 3 A | **Low** |
| A9-13 | `MANIFEST.csv` | No Espressif, AMOLED-panel or QMI8658C document is banked; the ESP32-S3 datasheet **is** reachable this session via a GitHub-LFS mirror | **Low** |
| A9-14 | E1 procedure | Measuring the matrix over USB at a clamp-legal 3 W runs 289 mW through a 200 mW/130 mW diode. Measure from the `5V` pin | **Low**, but it breaks hardware |
| A9-15 | ADR 0005 §"Two bucks, not one" | *"neither is near its rating"* — buck A is at 75 % in the state the clamp permits | **Low** — `carrier.md` already says so |

### What I checked and found **right**

Recorded deliberately, per `CLAUDE.md`'s note that a finding filed as handled is
worse than a wrong one:

- **928 mA** clamp-legal on the 5 V rail: datasheet build 964 mA. ✅
- **119/123/248 mA** on 12 V direct: datasheet build 120/120/244 mA. ✅
- **2.4/4.1/6.5 W** body heat: 2.75/4.24/6.62 W. ✅
- **"85 % is the 28 V figure, ~90 % at 12 V"**: confirmed verbatim by the
  selection guide (93 % at 8 V, 85 % at 28 V). ✅
- **8 V, not 7 V**, for the R-78E5.0-1.0 minimum input: confirmed, and not
  binding — 2.07 V of margin even held at the current limit. ✅
- **The LM317's minimum load is met** by `R-REG-SET`'s 8.33 mA alone, with
  margin against every candidate manufacturer's figure. ✅
- **The 47.5 ms hot-plug start and the 2.01× timer margin**: re-derived, agree. ✅
- **1.5 A etherCON contact vs a 0.78–1.10 A limiter**: 73 % worst case. ✅
