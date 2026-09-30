# K1 — The circuit of the left-hand key board

**Slice:** K1, cold. **Revision:** `d46a3b0` (working tree). `tools/` frozen, and only run here.
**Fact domain:** `U-KEYS-LH` (74HC165 at 3.3 V), the five key networks
(`C-KEY-LH1..5`, `R-KEY-SER-LH1..5`, `R-KEY-PU-LH1..5`), the marker and free
bits, `C-DECOUPLE-165-LH`, the five `TP-*-LH` pads and the chain signals, checked
against the KiCad sheets, the exported netlists, the design pages,
`config/figures.yaml`, the BOM rows and the banked datasheets.

## Summary

The wiring is right. Every pin of `U-KEYS-LH` matches the banked pinout, the
marker straps and the free bit match `allocation.yaml`, the five test pads are
on the nets their names give, `CLK INH` is tied low, `QH'` is left open, and the
decoupling cap is 2.5 mm from `VCC`. The 3.3 V thresholds and all four crossing
times recompute exactly. Nothing in the netlist is wrong.

The defects are in what the pages **claim the key network does**:

- The RC edges break the 74HC165's recommended input rise and fall time by a
  factor of about 16 on press and about 280 on release, and no page mentions it
  (K1-1).
- The network is called a "free hardware debounce", but its 120 µs window is 42×
  shorter than the switch's own banked 5 ms bounce (K1-2).
- The release time is restated as "125 µs" in two live places that the checker
  cannot see (K1-3).

There are also several smaller claims that the data refutes (K1-4 to K1-10), a
bring-up gap (K1-11), and two missing provisions a real board would want
(K1-12, K1-13).

Datasheet text was extracted with `pdftotext -layout` from the banked PDFs.
Page numbers are the PDF's own "n / 20" (Nexperia) or printed page (onsemi).

---

## Findings

### K1-1 [medium] Every key input breaks the 74HC165's maximum input rise/fall time, by ~16× on press and ~280× on release, and no page says so

**Node:** `/KEY_LH1`…`/KEY_LH5` → `U-KEYS-LH` pins 6,5,4,3,14 (`H G F E D`). Figures `key-release-time`, `key-press-time`.

**What the datasheets say:**
- onsemi recommended operating conditions: `tr, tf` ≤ **600 ns at VCC = 3.0 V** (1000 ns at 2.0 V, 500 ns at 4.5 V) `[datasheets/logic/74HC165-onsemi.pdf, p.3]`. The AC table gives 800 ns at 3.0 V `[same, p.5]`.
- Nexperia: `Δt/ΔV` ≤ 625 ns/V at 2.0 V and ≤ 139 ns/V at 4.5 V `[datasheets/logic/74HC165-nexperia.pdf, p.6, Table 5]`. Nexperia is the fitted part (`MPN 74HC165D,653`, `[repo hardware/cluster/key-register/key-register.kicad_sch]`).
- TI: `Δt/Δv` ≤ 1000 / 500 / 400 ns at 2 / 4.5 / 6 V, with the footnote: *"If this device is used in the threshold region … there is a potential to go into the wrong state"* `[datasheets/logic/74HC165-ti-scls116e.pdf, recommended operating conditions]`.
- None of the three parts has a Schmitt-trigger input.

**What the network does** `[calc]`:
- **Release:** τ = 103.4 µs. The 10–90 % time is τ·ln 9 = 227 µs. The slope at `V_IH` is (3.3 − 2.31) / 103.4 µs = 9.57 mV/µs, which is **104 000 ns/V**. Interpolating Nexperia to 3.3 V gives a limit of 625 − (1.3/2.5)(625 − 139) = **372 ns/V**, so the release edge is **~280× over**.
- **Press:** τ = 4.496 µs. The slope at `V_IL` is (0.99 − 0.1435) / 4.496 µs, which is **5 311 ns/V** (~14× over). The 10–90 % time is 9.9 µs against 600 ns (~16× over).
- **Time spent between `V_IL` and `V_IH`** (the undefined band):
  - On release, the node reaches 0.99 V at 103.4·ln(3.1565/2.31) = 32.3 µs and reaches 2.31 V at 119.9 µs, so it spends **87.6 µs** in the band. At a 250 µs scan, 87.6/250 = **35 % of releases** will have one sample taken inside that band.
  - On press, it spends 5.92 − 1.69 = **4.2 µs** in the band.

**Why it is medium rather than high:**
- These are parallel data inputs, not clocks. The register only captures them when `SH/LD` returns high, so TI's double-clocking warning does not apply directly.
- An indeterminate sample during the crossing looks exactly like contact bounce, and firmware already has to filter bounce (K1-2).
- The unstated costs are:
  - extra `ICC` while an input dwells mid-rail `[from memory: CMOS input shoot-through; not tabulated in the banked sheets]`;
  - supply noise on the shared rail during that dwell turning into several transitions.

**Where it is missing:**
- `key-switch-network.md` §2 quotes the TI threshold warning ("another reason not to shave this margin") but never checks its own edge against the rise-time limit.
- Grep for `rise time|transition|Schmitt|ns/V` across `hardware/cluster`, `key-chain-loom`, ADR 0001 and `figures.yaml` finds no such check `[run: grep -rn -i -E 'rise.?time|transition (rate|time)|Schmitt|ns/V' …]`.

**Fix:** state the violation on `key-switch-network.md`, with the argument above: data input, sampled on `SH/LD`'s rising edge, a 35 % chance of one undefined sample, absorbed by the release filter. Measure `ICC` with a key held half-pressed at bring-up. If that argument is not accepted, the alternative is a Schmitt buffer (74HC14/74LVC14) per key, which is 5 more parts per board.

### K1-2 [medium] The page and BOM call the RC a "free hardware debounce", but the switch's banked bounce is 5 ms, 42× longer than the RC's 120 µs window

**Node:** `C-KEY`/`R-KEY-SER` rows, figure `key-release-time` (its `conservative_bound`), figure `ks33-contact-bounce`.

**Evidence:**
- Gateron's own sheet says *"Bounce Time: 5msec Max. (at 16 in/sec. actuation speed)"* `[datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf, sheet 6 item 5]`. The register tracks this as `ks33-contact-bounce` = "5 ms max at 16 in/sec actuation" `[repo config/figures.yaml]`.
- The RC's release filter is `key-release-time` = 119.9 µs `[repo config/figures.yaml]`. Then 5000 / 119.9 = **41.7×** `[calc]`.
- During press bounce, any contact gap longer than ~120 µs reads as a release. On release, every bounce re-closure pulls the node low again in 5.9 µs (press τ). So the RC removes **neither** bounce direction at the 5 ms scale.

**Claims that say otherwise:**
- `R-KEY-SER` BOM row: *"release crosses V_IH at key-release-time, which is a free hardware debounce"* `[repo hardware/cluster/key-switch-network/bom.csv, also hardware/bom.csv:37]`.
- `C-KEY` row: *"The filter is cheap insurance and a BOUNCE filter"* `[repo same file]`.
- `key-switch-network.md` §2: *"The 47 nF is a bounce filter"* and *"Press is instant … release is filtered, which is the asymmetric-debounce shape ADR 0001 wants"*.
- `figures.yaml` `key-release-time.conservative_bound`: *"the release is absorbed by the asymmetric debounce either way"*.

**The corpus already knows this, in another file.** `docs/reference/latency-budget.md` says *"rejecting bounce is entirely the release filter's job, and the release window has to outlast the bounce burst rather than the 125 µs the key network's RC contributes"* `[repo docs/reference/latency-budget.md:125-135]`. The same point appears in `firmware/README.md:23`.

This is the recorded shape "a fix that did not reach the pages citing it". The correction landed in the latency budget; the owner page of the figure and the BOM rows still describe the RC as the debounce.

**Fix:** reword the `R-KEY-SER` and `C-KEY` rows and §2 so the RC is a glitch filter (sub-120 µs), and debounce is firmware's release window sized against `ks33-contact-bounce`. Cite that figure; do not restate it.

### K1-3 [medium] `key-release-time` is restated as "125 µs" on its own owner page and on `latency-budget.md`; the value is 119.9 µs, and the checker passes both

**Node:** figure `key-release-time` (value "119.9 us").

**Evidence:**
- `hardware/cluster/key-switch-network/key-switch-network.md:119` says *"The 125 µs release filter is half a scan period"*.
- `docs/reference/latency-budget.md:133` says *"than the 125 µs the key network's RC contributes"*.
- `[repo config/figures.yaml]`, `key-release-time.note`: *"Starting from 0 V instead of the divider voltage gives 124.5 us, which is the error the 125 us figure came from."*
- The forbidden list holds `"at ~125us"` and `"~125us"`. Neither matches "The 125 µs release filter" or "the 125 µs the key network's RC" (different spelling and word order).
- The hook reported `staleness check: PASS no live stale values` on this revision `[run: PreToolUse hook output, python3 tools/check-staleness.py]`.
- `[calc]` 103.4 × ln(3.1565/0.99) = 119.9 µs, and 103.4 × ln(3.3/0.99) = 124.5 µs. So "125" is the retired from-0 V number.

**Fix:** cite `key-release-time` in both sentences. Add forbidden patterns in each file's spelling: `"125 µs release filter"`, `"125 µs the key network"`. The `false_positive_note` already protects the legitimate "mean 125 µs" sampling-period uses at `latency-budget.md:59,97`.

### K1-4 [low] `key-marker-and-bits.md` "Still open" says "the 3 reserved spare-switch positions"; there are 2

**Node:** `config/key-layout.yaml` `spare_bits_switches`; `allocation.yaml` `right_thumb` `sw+ sw-`.

**Evidence:**
- `key-marker-and-bits.md:139` says *"Where the 3 reserved spare-switch positions go. Proposed on right_thumb … an M2 decision"*.
- `config/key-layout.yaml:160` says `spare_bits_switches: 2`.
- `allocation.yaml` has only `sw+`, `sw-`.
- The same page's §4 says *"There was a third, hold/preset, until 2026-09-26"*.
- The item also still reads "Proposed" and "an M2 decision", while `allocation.yaml` and the board sheets already wire the two spares on `right_thumb`.

This is the recorded shape "a stated count that has moved under the sentence stating it". `docs/decisions/0010-key-layout-as-data.md:220` ("three reserved") is worth a K6/K8 look.

**Fix:** cite `spare_bits_switches` instead of the count, and restate what is actually open (fitting, not placement).

### K1-5 [low] "A mid-shift `SH/LD` reload passes at 11 of 31 reload points" has no derivation and does not reproduce against `allocation.yaml`

**Node:** figure `marker-bits`; `allocation.yaml`.

**Evidence:** `key-marker-and-bits.md:105` gives no provenance tag and no arithmetic. Grep finds no derivation elsewhere `[run: grep -rn -i 'reload|11 of 31' hardware/cluster docs/decisions/0001* hardware/interfaces firmware]`.

**My recomputation** `[calc, python over allocation.yaml]`:
- The model: a reload after *k* clocks makes received bit *i* ≥ *k* equal to frame bit *i − k*.
- The marker passes when all 8 marker positions (6:1, 7:0, 14:0, 15:1, 20:0, 21:1, 29:0, 30:1) hold their levels.
- Results by assumption about the key bits:

| Key bits | Reload points that pass |
|---|---|
| All released (pulled high), free and spare bits high | **3** (k = 22, 30, 31) |
| All pressed | **2** (k = 26, 31) |
| Any value, free and spare bits high | **16** |
| Any value, one clock off either way | 16 or 13 |
| Guaranteed for every key state | **1** (k = 31) |

None of these gives 11. The figure may predate the 2026-09-26 allocation change, or it may use a model the page does not state.

**Fix:** give the model and the arithmetic, or drop the number. Firmware is told to rely on it.

### K1-6 [low] The free-bit pull-up's note says each one "costs the same static draw as a key"; it draws about 1 µA

**Node:** `R-KEY-PU-FREE3` (`of: R-KEY-PU`), net `/KEY_FREE3` → `U-KEYS-LH.A`.

**Evidence:**
- The sheet Note says *"each one costs the same static draw as a key"* `[repo hardware/cluster/key-marker-and-bits/key-marker-and-bits.kicad_sch:153; exported to netlist.yaml]`.
- `/KEY_FREE3` has only `R-KEY-PU-FREE3.2` and `U-KEYS-LH.A` on it `[repo hardware/boards/key-board-lh/board-netlist.yaml]`. There is no path to ground.
- So the current is the input leakage, ≤ ±1 µA at 85 °C `[datasheets/logic/74HC165-nexperia.pdf p.6, I_I]`, against 1.43 mA for a closed key.
- `key-scan-current`'s derivation counts only closed keys `[repo config/figures.yaml]`, so the Note contradicts the register.

**Fix:** reword to "costs a part and a placement, not current".

### K1-7 [low] `R-KEY-SER`'s stated role ("bounds injected current") is not what it does; it limits `C-KEY`'s dump into the switch contact, which peaks at 3.3× the KS-33's rating

**Node:** `R-KEY-SER-LH1..5`, `/LHn/SWITCH_LEG`.

**Evidence:**
- The BOM row ends *"Also bounds injected current"* `[repo hardware/cluster/key-switch-network/bom.csv]`.
- `R-KEY-SER` sits between the node and the switch. The register input is on the node directly (`/KEY_LH1`: `C-KEY-LH1.1`, `R-KEY-PU-LH1.2`, `R-KEY-SER-LH1.1`, `U-KEYS-LH.H` `[repo board-netlist.yaml]`), so it bounds nothing that is injected into the register.

**What it actually does** `[calc]`:
- When the switch closes, the 47 nF charged to 3.3 V discharges through R-KEY-SER plus the contact: 3.3 / (100 + 0.2) = **32.9 mA peak**, τ ≈ 4.7 µs, energy ½·47 nF·3.3² = 0.256 µJ.
- Without R-KEY-SER, the peak would be bounded only by the ≤ 200 mΩ contact resistance.
- The KS-33 is rated **10 mA max, 10 µA min, resistive load** `[datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf, sheet 3 item 3 and sheet 6; MANIFEST.csv row]`. The steady 1.43 mA is well inside that. The 32.9 mA transient is 3.3× the rated maximum, for microseconds.

**Fix:** state the real role on §2. Optionally, 330 Ω brings the peak to 10 mA `[calc: 3.3/330]`, with:
- press τ = (2200 ∥ 330) × 47 nF = 287 Ω × 47 nF = 13.5 µs;
- pressed node at 3.3 × 330 / 2530 = 0.43 V;
- press crossing 13.5 × ln(2.87/0.56) = 22.0 µs, still 11× inside the 250 µs scan;
- static current 1.30 mA.

That trade is the owner's to make.

### K1-8 [low] The 10 kΩ trade is priced as "a 100 µs τ", which is the old 10 kΩ/10 nF network; with the fitted 47 nF it is 470 µs

**Node:** `R-KEY-PU` (open trade 2k2 vs 10k), `C-KEY` 47 nF.

**Evidence:** `key-switch-network.md` §2 says *"Going back to 10 kΩ would cut that to 6.2 mA and 0.8 LSB, at the price of a 100 µs τ"*.

`[calc]`:
- 10 kΩ × 47 nF = **470 µs**.
- The pressed node would sit at 3.3 × 100/10100 = 0.0327 V.
- Release crossing: 470 × ln(3.2673/0.99) = **561 µs**, more than two scan periods.
- The 6.2 mA is correct (19 × 3.3/10100 = 6.21 mA).
- 100 µs is 10 kΩ × 10 nF, the superseded network that `figures.yaml` `key-release-time.escape_note` records.

This is the recorded shape "an explanation that restates the wrong value". It also understates the cost side of a live trade by 4.7×.

**Fix:** use the 47 nF numbers, or state that going to 10 kΩ also means changing `C-KEY`.

### K1-9 [low] The pages say the network passives sit "AT the register input, millimetres from the switch"; on the LH board they sit at the switch, up to 44 mm from the register

**Node:** `C-KEY-LH1..5`, `R-KEY-SER-LH1..5`, `R-KEY-PU-LH1..5`.

**Claims:**
- `key-switch-network.md` Interfaces: *"Both passives sit at the register input, millimetres from the switch"*.
- The §2 drawing: *"Both passives are AT the register input … That is automatic"*.
- Sheet Notes on `C-KEY` and `R-KEY-SER` say the same `[repo key-switch-network.kicad_sch:460,478]`.

**The board** `[run: pcbnew over key-board-lh.kicad_pcb]` measures C-KEY pad 1 to its `U-KEYS-LH` pin, C-KEY to switch pin 1, and the routed length of the node:

| Key | C-KEY → register pin | C-KEY → switch pin 1 | Routed node |
|---|---|---|---|
| LH1 | 44.2 mm | 10.7 mm | 50.6 mm |
| LH2 | 34.9 mm | 6.3 mm | 41.3 mm |
| LH3 | 25.3 mm | 6.3 mm | 36.6 mm |
| LH4 | 17.3 mm | 12.5 mm | 33.8 mm |
| LH5 | 7.7 mm | 11.9 mm | 18.2 mm |

`layout.yaml` says this is the intent: *"Each key network is a row of three 0805s beside its own switch"* `[repo hardware/boards/key-board-lh/layout.yaml]`.

The electrical consequence is small: the node is 2.2 kΩ ∥ 47 nF, and the traces lie over a two-sided ground pour. But the worked example contradicts the sentence that describes it.

**Fix:** either move `C-KEY` next to its register pin, or change the pages to "beside its switch; the node trace to the register is ≤ ~50 mm over ground".

### K1-10 [low] `SH/LD` is described as "falling edge loads"; the load is level-sensitive, and the sample is taken at the rising edge

**Node:** `/CHAIN_SHLD` → `U-KEYS-LH.SHLD` (pin 1).

**Evidence:**
- `key-register.md` Interfaces says *"Falling edge loads the parallel inputs"*, and §1 says *"On the falling edge of SH/LD the parallel inputs load"*.
- Nexperia: *"When the parallel load input (PL) is LOW the data from D0 to D7 is loaded into the shift register asynchronously"* `[74HC165-nexperia.pdf p.1]`. The function table shows Q7 following D7 while PL = L `[p.4, Table 3]`.
- ADR 0001 has it right: *"SH/LD is asynchronous and level-sensitive"* `[repo docs/decisions/0001-mcu-and-board-partitioning.md:203]`.
- What firmware captures is the input state when `SH/LD` returns high. That instant is what K1-1's 35 % figure is measured against.

**Fix:** reword both. Optionally cite the minimum `SH/LD` low width at 3.0 V: 27 ns at 25 °C, 36 ns at 125 °C `[74HC165-onsemi.pdf p.5]`.

### K1-11 [low] Bench bring-up leaves `SER` floating, with no test pad; the README's "only draw is quiescent current" does not hold with a floating CMOS input

**Node:** `/CHAIN_SER_LH` (= `J-CHAIN.7` → `U-KEYS-LH.SER` only `[repo board-netlist.yaml]`).

**Evidence:**
- `R-SER-TERM`, the chain-end pull-up, is on the **main board** by decision `[repo hardware/interfaces/key-chain-loom/key-chain-loom.md, "The chain-end serial input"]`.
- The README's bench procedure powers the board from TP-3V3/TP-GND with the ribbon off (step 3), then clocks SCK and watches QH (step 4) `[repo hardware/boards/key-board-lh/README.md, Bring-up]`.
- So `SER` floats: there is no pad for it, and nothing on the board holds it.
- That breaks the datasheet rule: *"Unused inputs must always be tied to an appropriate logic voltage level"* `[74HC165-onsemi.pdf p.3 note 3]`; *"All unused inputs … must be held at VCC or GND"* `[74HC165-ti-scls116e.pdf, note 3]`.
- Any clock past the 8th shifts in undefined bits. The step-3 current reading can include shoot-through from the floating input `[from memory]`.

**Fix:** in the README, tell the bench user to jumper `J-CHAIN` pin 7 to pin 3 (3V3) and clock exactly 8, or add a sixth pad `TP-SER-LH` (bare copper, costs nothing, and `TP-CHAIN` qty moves 10 → 12).

### K1-12 [advisory] The key board has no ESD protection, and the main-board TVS does not cover this board's `QH`

**Node:** `J-CHAIN` (key board), `/HOP_LH_LT`, `U-TVS-CHAIN` (main board).

**Evidence:**
- `U-TVS-CHAIN` (SP0504BAHTG) sits *"on SCK, SH/LD and the chain-end SER … at the left_hand J-CHAIN; its fourth channel is spare"* `[repo key-chain-loom.md, main-board end drawing]`.
- `QH` coming back from the LH board (`/HOP_LH_LT`) is not on it.
- On the key board, `J-CHAIN` pins 5/7/9/11 go straight to `U-KEYS-LH`. Its only protection is the part's own HBM > 2000 V (JS-001 class 2) and CDM > 1000 V `[74HC165-nexperia.pdf p.1]`.
- The ribbon is unplugged at every service (`key-chain-loom.md`: "the sockets are plugged every time the lid goes back on"), which is when a handled header is exposed.

**Suggestion (for K2/owner):** put `QH` on the spare TVS channel at the main board. For the key board, accepting the part's own ESD rating is defensible, but it should be stated.

### K1-13 [advisory] No footprint for the damping bulk capacitor that the chain page already expects the key board may need

**Node:** `V3V3_CHAIN_LH`, `C-DECOUPLE-165-LH`, `FB-CHAIN`.

**Evidence:**
- The `FB-CHAIN` row says: *"the bead and the key board's C-DECOUPLE-165 (100nF) form an LC near 0.5MHz … scope the key board's VCC while shifting and add a damping bulk cap on the key board if it rings"* `[repo hardware/interfaces/key-chain-loom/bom.csv]`.
- `[calc]` f = 1/(2π√(1 µH·100 nF)) = 503 kHz and Z₀ = √(L/C) = 3.16 Ω. That is half the 1 MHz chain clock (`docs/reference/latency-budget.md:98`).
- The only other capacitance on the rail sits behind 2.2 kΩ (the `C-KEY`s), so it adds no damping.
- The LH board's 3V3 net holds only `C-DECOUPLE-165-LH` and the pull-ups `[repo board-netlist.yaml]`.
- The board is being ordered now as the worked example. Adding the cap after E14 would mean a respin.

**Suggestion:** add a DNP 0805/1206 footprint (e.g. 10 µF, whose ESR provides the damping) on `V3V3_CHAIN_LH` near `J-CHAIN` pin 3.

### K1-14 [advisory] Provenance defects on the threshold and pinout citations

- **Wrong Toshiba path.** `key-switch-network.md`'s vendor table cites Toshiba as `74HC165-toshiba.pdf`. The banked file is `datasheets/logic/74HC165-toshiba-1986-excerpt.pdf` `[repo datasheets/MANIFEST.csv]`. The values quoted (1.5/0.5, 3.15/1.35) do match that file `[run: pdftotext on it]`.
- **JESD8C levels not on the cited page.** The page says *"JESD8C (2.7–3.6 V), whose levels are 0.7/0.3 × VDD [74HC165-nexperia.pdf p.1]"*. p.1 only claims compliance and gives no levels. `[from memory]` JESD8-C's LVCMOS input levels are V_IH 2.0 V / V_IL 0.8 V, not 0.7/0.3 × VDD. This is unverified because JESD8C is not banked. Either way the design threshold (2.31/0.99 from onsemi's 3.0 V row) is the conservative one, so no conclusion moves. The "second strike" argument should be removed or banked.
- **`Pins_source` cites a different vendor than the pin names.** `U-KEYS` `Pins_source` cites TI SCLS116E p.1, while the `Pins` field uses Nexperia's names (`PL`, `CP`, `CE`, `Q7`, `DS`, `D0..D7`). The fitted part is Nexperia, whose Table 2 is on p.4 (as `cluster-boards.md` cites). Both pinouts agree (see CORRECT), so this is only a citation tidy-up.
- **One `[from memory]` claim is bankable.** `key-register.md` §1 marks *"H (D7) appears at QH immediately"* `[from memory]`. It is in the banked sheet: Nexperia p.4, Table 3 (parallel load: Q7 = D7) and p.8 (`tpd` D7 → Q7).
- **Wrong family's threshold.** The `C-KEY` BOM row argues coupling *"does not cross a 0.8V threshold"*. 0.8 V is the LVC figure. The fitted HC165's `V_IL` at 3.3 V is 0.99 V (`key-press-time` threshold_note). The conclusion holds either way (the node lands at 1.94 V, ADR 0001).

---

## Checked and found CORRECT

**Pin map**

- `U-KEYS` `Pins` field against the library symbol pins and against both banked pinouts, pin for pin: SH/LD=1, CLK=2, E..H=3..6, QH'=7, GND=8, QH=9, SER=10, A..D=11..14, CLK INH=15, VCC=16 `[repo key-register.kicad_sch:398, lib pins; datasheets/logic/74HC165-ti-scls116e.pdf p.1 D package; 74HC165-nexperia.pdf p.4 Table 2]`.
- `CLK INH` is tied to `GND_CHAIN`. `QH'` is left open, as an external endpoint; the onsemi note says unused outputs are left open `[repo board-netlist.yaml; 74HC165-onsemi.pdf p.3 note 3]`.

**Bit order and allocation**

- Bit order H → A, as argued in `key-register.md`, against the Nexperia function table (DS → Q0, D7 → Q7) `[74HC165-nexperia.pdf p.4]`.
- `allocation.yaml` `left_hand` = `[LH1, LH2, LH3, LH4, LH5, M0, M1, FREE3]` against `board-netlist.yaml`: H..D = `/KEY_LH1..5`, C = `GND_CHAIN` (M0), B = `V3V3_CHAIN_LH` (M1), A = `/KEY_FREE3`. This matches the page table (bits 29 = 0, 30 = 1, 31 free) and the bit numbering 24–31, with `left_hand` at the SER end of the chain `[repo config/key-layout.yaml:133-137]`.
- Marker pattern in bit order: `1 0 · 0 1 · 0 1 · 0 1` `[calc from allocation.yaml]`.
- "8 times in 32": 8 marker bits of 32 `[calc]`.

**Thresholds** `[74HC165-onsemi.pdf p.4, DC table]`

- onsemi's 3.0 V row is 2.1 / 0.9.
- Interpolated in absolute volts to 3.3 V, that gives 2.31 / 0.99 = 0.70 / 0.30 `[calc]`.
- TI, Nexperia and the Toshiba excerpt agree with onsemi at 2.0 V and 4.5 V; TI and Nexperia also agree at 6.0 V `[pdftotext of all four]`.

**Timing figures** `[calc]`

- `key-release-time` 119.9 µs = 103.4 × ln(3.1565/0.99).
- `key-press-time` 5.92 µs = 4.496 × ln(3.1565/0.8465).
- The conservative bounds, 138.7 µs and 6.89 µs.
- The pressed-node divider, 0.1435 V.
- The pole: 1/(2π·103.4 µs) = 1.54 kHz, and 20·log(800k/1.54k) = 54 dB.
- 250/5.92 = 42×.

**Currents and quantities**

- `key-scan-current`: 3.3/2300 = 1.435 mA; × 19 = 27.3 mA. 19 = RT4 + RH6 + LT4 + LH5 `[repo key-layout.yaml]`.
- The README's "about 1.4 mA" per pressed key.
- The README's ~20 mA bench limit covers all 5 LH keys pressed at once (7.2 mA).
- `key-pullup-qty` 24 = 21 + 3.
- Per-board counts in `cluster-boards.md` (LH: 1 U, 1 C-DEC, 5 SW, 6 R-KEY-PU, 5 R-KEY-SER, 5 C-KEY), against `board-netlist.yaml`.

**Chain timing and signal integrity**

- Chain clock 1 MHz against `fmax` ≥ 15 MHz at 3.0 V over −55..125 °C `[74HC165-onsemi.pdf p.4]`: 15× margin.
- CLK→QH `tpd` ≤ 65 ns at 3.0 V `[74HC165-onsemi.pdf p.4]`, against the 1000 ns period. The hop's setup needs ≤ 65 + 55 ns `[calc]`.
- `QH` V_OH ≥ 2.20 V at 3.0 V / 2.4 mA, 125 °C, above the next device's V_IH `[74HC165-onsemi.pdf p.4]`.
- The "lumped load" claim: the 86.27 mm ribbon `[repo mechanical/drc.echo]` plus ≤ 51 mm of board is ≈ 0.14 m ≈ 0.8 ns one-way `[calc, from memory ~5.5 ns/m]`, well under `tt`/6 for HC's ≥ 6 ns edges `[74HC165-nexperia.pdf p.8]`.
- Supply: HC at 3.3 V is inside VCC 2.0–6.0 V `[74HC165-nexperia.pdf p.6]`.

**Decoupling**

- `C-DECOUPLE-165-LH` is 100 nF X7R 0805 (YAGEO CC0805KRX7R9BB104) on `V3V3_CHAIN_LH` / `GND_CHAIN` `[repo board-netlist.yaml, key-register.kicad_sch]`.
- On the PCB, pad 1 is **2.5 mm** from `U-KEYS-LH` pin 16. Both are on B.Cu, and GND pours exist on F.Cu and B.Cu `[run: pcbnew]`. "At the package" holds.

**Test pads and connector**

- `TP-3V3-LH` → `V3V3_CHAIN_LH`, `TP-GND-LH` → `GND_CHAIN`, `TP-SCK-LH` → `/CHAIN_SCK`, `TP-SHLD-LH` → `/CHAIN_SHLD`, `TP-QH-LH` → `/HOP_LH_LT` (= `U-KEYS-LH.QH`). This holds in both `board-netlist.yaml` and the `.kicad_pcb` pad nets `[run: pcbnew]`. Five pads, matching the `TP-CHAIN` row (qty 10 = 5 × 2).
- `J-CHAIN` key-board pins against `key-register.md` Interfaces and the `key-chain-loom.md` key-board-end drawing: SCK 11, SH/LD 9, SER 7, QH 5, 3V3 3, GND 4/6/8/10/12, pins 1/2 spare and unconnected.

**Pull-ups and inputs**

- Every parallel input is driven: 5 networks, 2 straps, 1 pull-up. No floating input while the ribbon is connected. `SER` is held by the main board's `R-SER-TERM` 10 kΩ `[repo key-chain-loom.md]`.
- Pull-up leakage drop: 1 µA × 2.2 kΩ = 2.2 mV `[calc; I_I 74HC165-nexperia.pdf p.6]`.
- KS-33 minimum wetting current: 10 µA ≤ 1.43 mA `[GATERON spec]`.

**Tool runs**

- `python3 tools/check-netlist.py --strict`: *0 problem(s)* `[run]`. It reports its bundle and instance notes, none on this board's nets.
