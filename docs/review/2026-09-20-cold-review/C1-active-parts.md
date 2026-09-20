# C1 — Active parts review

Every active semiconductor in `hardware/bom.csv`, checked against what the
design actually asks of it. Read alongside ADRs 0001, 0003, 0004, 0005, 0006,
0007, 0013 and 0014.

**Scope note.** This pass is about *part selection*. Where a topology or passive
value is implicated in whether a chosen part can do its job, it is called out,
but the review does not re-open decisions that the ADRs have settled on other
grounds.

**Two findings are hard blockers.** `U-LOADSW` (TPS2553) and `U-TVS-UMB`
(SP3012) are both 5 V-class parts sitting on a +12 V rail. Both are outside
their absolute maximum ratings as drawn. Everything else is refinement.

---

## Verdict table

| Ref | Chosen part | Verdict | One-line reason |
|---|---|---|---|
| **U-LOADSW** | TPS2553DBV | **CHANGE** | 2.5–6.5 V part on a +12 V rail — ~2× over absolute max. Datasheet-verified |
| **U-TVS-UMB** | SP3012-06UTG | **CHANGE** | V_RWM = 5.0 V; cannot sit across the umbilical +12 V pair. Datasheet-verified |
| **U-REG-DAC** | LM317LZ + 240R/768R | **CHANGE** | Full tolerance stack reaches 5.62 V against the DAC's 5.5 V recommended max. Fix is the divider, not the part |
| **U-KEYS** | 74LVC165A ×4 | **CHANGE** | Part number does not resolve to a mainstream in-production device; use SN74LV165AD |
| **U-DIFFRX** | "INA821 or INA828" | **CHANGE** | Two part numbers in one BOM line. Pick INA828IDR — G = 2.131 lands on an exact E96 R_G |
| **D-REVPOL** | 1N5817 ×2 | **CHANGE** | 20 V / 1 A. Free upgrade to 1N5819 (40 V) and 1N5822 (3 A) on the +12 V leg |
| **F-POLY** | PPTC 1206 500 mA hold | **CHANGE** | Hold current derates below the instrument's own peak draw at the documented interior temperature |
| **U-WATCHDOG** | 74HC123 | **CONSIDER** | Function right, part mediocre. CD74HC4538M is the precision equivalent. Rail, timing cap and a bring-up defeat are all unspecified |
| **U-LVL-MOD** | 74AHCT125 on bus +5 V | **CONSIDER** | Move it to the DAC's 5.25 V rail: fixes a sequencing clamp event and ~10 mV of V_IH headroom, deletes the bus-rail dependency |
| **U-DISP** | LilyGO T-Display-S3 AMOLED | **CONSIDER** | SY6970 PMU is documented unstable on 5 V with no battery, in a deliberately battery-free design |
| **R-PRECISION** | LT5400-class (passive) | **CONSIDER** | Buys 0.11 cents of drift into a channel whose trimmer already costs 2.4 cents. 20× over-specified |
| **U-DAC** | DAC8568C | **KEEP** | Right part, right grade. Specify `DAC8568ICPW` — the D grade differs by one character and has the opposite reset |
| **U-OPA-PITCH** | OPA2197 ×5 | **KEEP** | Correct and comfortably over-specified; the one-part-number rule is worth more than the saving. Quantity is short by one |
| **U-BUF** | OPA2197IDR | **KEEP** | +12 V rail choice is the right fix for the fault-vs-CMRR conflict. Watch capacitive loading on the sensor supply |
| **U-REF-BREATH** | REF5050AIDR | **KEEP** | Over-specified on initial accuracy, correct on the thing that matters (line rejection). Full P/N already given |
| **U-ADC** | MCP3202-CI/SN | **KEEP** | 12 bits and ~65 ksps at 3.3 V are ample. Two free improvements available; see F9/F10 |
| **U-BREATH** | MPXV4006DP | **KEEP** | Correct part, correct rationale. BOM package column is wrong — it is 8-SOP SMT, not THT |
| **U-IMU** | QMI8658C (onboard) | **KEEP** | Right sensor class, and the only policy-legal way to get one. Decouple its read rate from the 4 kHz loop |
| **U-MCU-RT** | Waveshare ESP32-S3-Matrix | **KEEP** | Meets every stated gate. The header `5V`/VBUS collision needs a real diode, not a bench check |
| **U-LVLSHIFT** | 74AHCT125 | **KEEP** | WS2815 V_IH confirmed at 3.5 V — the open verification item in ADR 0014 closes in the part's favour |
| **U-BUCK** | R-78E5.0-1.0 | **KEEP** | Lowest-risk regulator in the design. Damp the input LC; OKI-78SR-5/1.5 is the drop-in if headroom is wanted |
| **D-JACK-CLAMP** | BAV99 ×6 | **KEEP** | Correct part, correct configuration, correct reasoning about Schottky leakage |
| **LED-SIDE** | WS2815 60/m | **KEEP** | Backup data line earns its place in a sealed body. Add a pull-down on each D_IN |
| **U-ESD-USB / SW-BOOT / J-USB** | marked not-needed | **KEEP** | Correct — the dev boards carry them |

Missing active parts identified: a diode-OR for the USB/buck 5 V collision (F14),
an OE-gating network for the module level shifter (F17), and a module-end TVS
(F2). Passive gaps in the breath path are noted in F20.

---

# Findings

Severity: **Critical** (part cannot work as drawn) / **High** (out of spec or a
repeatable stress event) / **Medium** (real error with margin) / **Low**
(tidy-up). Confidence and verification status are stated per finding.

---

## F1 — U-LOADSW: the TPS2553 is a 6.5 V part on a 12 V rail

**Severity: Critical. Confidence: High. Datasheet-verified.**

The TPS2553 is a USB-class power-distribution switch with an **input voltage
range of 2.5 V to 6.5 V**. ADR 0004's own power tree puts it here:

```
bus +12V ──[1N5817]──┬──[ferrite]──[bulk]──[TPS2553]── umbilical +12V
```

That is 12 V applied to a part whose absolute maximum V_IN is 7 V. It will not
survive first power-on. The current-limit setting is irrelevant.

I suspect this is a naming slip rather than a design error — ADR 0005 says
"**TPS2553-class** current-limited load switch", meaning the *function*, and the
BOM then hardened the class name into a part number. The function is right and
the reasoning in ADR 0005 (inrush ramp into the instrument's bulk, foldback on an
umbilical fault, toggle drives an enable rather than the current) is all correct
and should be kept exactly as written. Only the part changes.

### What to use instead

The policy constraint makes this harder than it looks. Every modern one-chip
12 V eFuse I could find is in a leadless package:

| Candidate | Range | Package | Verdict |
|---|---|---|---|
| TPS2592AA / TPS2592AL | 4.5–18 V | VSON-10 (3×3) | Function is perfect; **violates the QFN/leadless policy** |
| TPS27S100A/B | up to 40 V | HTSSOP-14 PowerPAD | Thermal pad — needs paste and a hotplate. **Violates policy** |
| MIC2039, MIC2545A | 5.5 V max | SOT-23-6 / SOIC-8 | Wrong voltage class |
| LM5060 | 5.5–65 V | VSSOP-10, 0.5 mm | Leaded but finer than the TSSOP-16 already accepted |
| **LT1641-1 / LT1641-2** | **9–80 V** | **SO-8** | **Recommended** |

**Recommendation: `LT1641-1CS8` (auto-retry) or `LT1641-2CS8` (latch-off), SO-8,
plus an N-channel MOSFET and a sense resistor.** It is the only candidate that is
both correctly rated and squarely inside the package policy, and it does
everything ADR 0005 asks for and more:

- Inrush is set by a single capacitor on the GATE pin: `I_inrush = C_L × 10 µA / C1`.
  For the instrument's bulk (call it 1000 µF, dominated by the two WS2815 feed
  capacitors) and a 200 mA inrush target, `C1 = 1000 µF × 10 µA / 200 mA = 50 nF`.
- Analog **foldback** current limit, which is precisely what ADR 0005 wants on a
  crushed cable — the current limit reduces as the output voltage collapses, so a
  dead short does not sit at full limit current.
- A programmable timer turns the FET fully off if the fault persists, rather than
  cooking the pass device.
- Remote enable, which is what the panel toggle drives.

Sense resistor for a 500 mA trip: LT1641's current-limit sense threshold is
nominally 50 mV, so `R_SENSE = 50 mV / 0.5 A = 100 mΩ`, 1 % , ≥0.5 W. Pass FET:
any logic-level-gate 30–60 V N-channel in SOT-223 or DPAK with R_DS(on) ≤ 50 mΩ
— e.g. `IRLR024N` or `SUD50N06-09L` in DPAK, both through-hole-adjacent and easy
to hand-solder.

**Choose the `-2` (latch-off) variant.** ADR 0014's brownout-latch analysis says
the failure mode to avoid is a self-heating protection device oscillating in and
out of limit. Auto-retry into a persistent fault reproduces exactly that
behaviour at a different frequency. A latch that requires the panel toggle to be
cycled is the correct human interface for "something is wrong with the cable."

**Set the limit from the E6 measurement, not from the BOM's ~500 mA.** ADR 0004
already says the instrument current figure is the least trustworthy number in the
document, and the verification pass put the ceiling at ~1.25 A. A 500 mA limit
against a 600 mA peak would nuisance-trip. Fit `R_SENSE` last.

---

## F2 — U-TVS-UMB: SP3012 is a 5 V array and two of the conductors it protects are not 5 V signals

**Severity: High. Confidence: High. Datasheet-verified** (Littelfuse SP3012
series, V_RWM = 5.0 V at I_R ≤ 1 µA).

The BOM puts one `SP3012-06UTG` across the umbilical entry — "8 conductors from
outside". Three problems:

1. **The +12 V conductor.** A 5 V standoff diode on a 12 V rail is forward into
   its clamp continuously. This is not a marginal call; it is a short across the
   supply through a part rated for ESD energy, not DC.
2. **The BREATH conductor reaches 4.8 V.** At V_RWM the array is specified at up
   to 1 µA of leakage. Through the 10 kΩ protection resistor the design needs on
   that line (ADR 0003), 1 µA is **10 mV of temperature-dependent error** on the
   channel the project spent the most analysis protecting. Typical leakage is
   nanoamps, so this is a "check it, do not assume it" item rather than a
   certainty — but the standoff voltage is only 200 mV above the signal peak,
   which is too little design margin on a precision line.
3. **Six channels, eight conductors.** Four of the eight are grounds and need no
   channel, so six is arithmetically sufficient — but the allocation is not
   written down anywhere, and the +12 V pin must not be one of them.

### Recommendation: split the protection by what the conductor carries

| Conductor(s) | Part | Why |
|---|---|---|
| SCLK, MOSI, CS (3.3 V logic) | Keep a low-capacitance 5 V array — `SP3012-04UTG` (SOT-23-6, 4 channels) | Right standoff, low C for SPI edges |
| BREATH | **`PESD12VS1UL`** or any 12 V-standoff single-line TVS, SOD-882/SOT-23 | 12 V standoff puts leakage in the picoamp range at 4.8 V |
| +12 V / PWR_GND | **`SMAJ15A`** (15 V standoff, 400 W, DO-214AC) | Correct rating for a power rail; the large package is easy to place |

**And fit the same set at the module end.** The BOM only has a TVS at the
controller. A human plugs and unplugs the cable at both ends, and ADR 0004's
hot-plug discussion (R28/R37) applies symmetrically. The module end is also where
an ESD event reaches the DAC and the precision analog section, which is the more
expensive side to lose.

---

## F3 — U-REG-DAC: the LM317 tolerance stack overruns the DAC's recommended maximum

**Severity: High. Confidence: High. Arithmetic, from standard LM317L
specifications.**

The BOM states: *"Vout = 1.25*(1+768/240) = 5.25V. Worst-case ±4% = 5.04-5.46V,
inside the DAC8568 5.5V max."*

That calculation applies the reference tolerance and stops. It omits the divider
tolerance and the adjust-pin current. The full expression is:

```
Vout = Vref × (1 + R2/R1) + Iadj × R2
```

With `Vref = 1.25 V ±4 %`, `R1 = 240 Ω ±1 %`, `R2 = 768 Ω ±1 %`,
`Iadj ≤ 100 µA`:

| Term | Worst high | Worst low |
|---|---|---|
| R2/R1 | (768 × 1.01)/(240 × 0.99) = **3.2646** | (768 × 0.99)/(240 × 1.01) = **3.1366** |
| Vref × (1 + R2/R1) | 1.30 × 4.2646 = **5.544 V** | 1.20 × 4.1366 = **4.964 V** |
| Iadj × R2 | +0.077 V | +0.000 V |
| **Vout** | **5.62 V** | **4.96 V** |

**5.62 V against a 5.5 V recommended operating maximum** (absolute max 6.0 V, so
this is out-of-spec rather than destructive). And the low end is worse than it
looks in the other direction: at AVDD = 4.96 V the DAC is being asked to output
4.75 V — the top of the window ADR 0006 chose specifically for headroom — with
only 210 mV of it. The review's own R5 finding puts the required headroom at
100–200 mV. The window ADR 0006 designed is real, but this regulator does not
reliably deliver the rail that makes it real.

### Fix 1 (recommended): shrink the divider and tighten it

The Iadj term scales with R2, so halving both resistors halves it. Use
**R1 = 120 Ω, R2 = 383 Ω, both 0.1 % metal film** (both are E96 values):

| | Value |
|---|---|
| Nominal (Iadj typ 50 µA) | 1.25 × 4.1917 + 0.019 = **5.26 V** |
| Worst high | 1.30 × (1 + 3.1917 × 1.002) + 0.038 = **5.495 V** |
| Worst low | 1.20 × (1 + 3.1917 × 0.998) + 0.019 = **5.04 V** |

5.495 V is inside 5.5 V — by 5 mV, which is not margin, it is arithmetic luck —
and 5.04 V gives 290 mV of DAC headroom at the 4.75 V code. Divider current rises
to 1.25/120 = **10.4 mA**, which comfortably exceeds the LM317L's ~3.5 mA minimum
load requirement (the existing 240 Ω already did, at 5.2 mA — that part of the
original choice was correct and is worth saying).

### Fix 2 (better): use a regulator with a ≤1 % reference

The LM317's ±4 % reference consumes the entire tolerance budget on its own. A
**`LP2951ACM`** (SOIC-8, adjustable, 0.5 % reference, 100 mA, low quiescent
current, no minimum-load requirement) with 0.1 % divider resistors lands at
5.25 V ±0.8 % = **5.21–5.29 V**, which makes both edges non-issues permanently.
It is the same effort to fit, it is in a policy-preferred package, and it adds a
shutdown pin and an error flag that could be used later.

### For a one-off, also do this

Fit the regulator, **measure the rail, and select R2 to land at 5.30 V.** The
bench is available and this is a five-minute job that removes the whole argument.
The design should still be correct without it — a board that only works because
someone hand-selected a resistor is not a design — but there is no reason not to.

### One associated note

The 10 µF ADJ bypass gives a 7.7 ms soft-start (`768 Ω × 10 µF`). That is
deliberate and good for the DAC, but it is what creates the sequencing hazard in
F5 below, so the two findings are linked.

---

## F4 — U-DAC: right part, right grade; specify the orderable number and beware one character

**Severity: Low (as a specification gap). Confidence: High. Grade behaviour
verified** (TI DAC7568/DAC8168/DAC8568 documentation: A and C grades reset to
zero scale, B and D to midscale; grades A/B accept external V_REFIN ≤ AVDD, C/D
≤ AVDD/2).

ADR 0006's grade analysis is correct and the reasoning is the best piece of part
selection in the document — taking the mod offset from a DAC channel so that a
zero-scale reset parks *every* output correctly is genuinely elegant.

Since the design uses the **internal** reference, the A-versus-C distinction
(external V_REFIN range) is irrelevant here. The C grade is the mainstream
stocked variant, so:

> **Specify `DAC8568ICPW` (TSSOP-16, tube) or `DAC8568ICPWR` (reel).**

**And note the trap:** `DAC8568I**C**PWR` and `DAC8568I**D**PWR` differ by one
character and have opposite power-on behaviour. The D grade parks pitch at
midscale — a VCO octaves up — from rack power-on until firmware writes. Put the
letter in bold in the BOM and check the reel label on arrival, because this is
exactly the kind of error that presents as "the module is broken" at E7.

### Is the part right on specifications?

| Requirement | DAC8568 | Verdict |
|---|---|---|
| ≥16-bit on pitch | 16-bit, monotonic | ✔ |
| Settling ~10 µs (latency budget) | ~7 µs typ to ±0.003 % FSR | ✔ |
| 8 channels (7 used) | Octal | ✔ |
| 0–5 V span from a ≤5.5 V supply | Internal 2.5 V ref, ×2 gain | ✔ — and this is the reason to prefer it over AD5676R, whose 0–2.5 V span would double the scaling gain and with it every downstream noise and offset term |
| Supply 2.7–5.5 V | ✔ at 5.25 V | see F3 |
| INL | ±4 LSB typ, ±12 LSB max | Adequate — ADR 0006 already budgets 0.66–2.0 cents for it and handles it with the multi-point NVS table |

**On the AD5676R alternative:** its ±2 LSB max INL is genuinely better and would
shrink the firmware correction table's job. But it costs the ×2 gain option, and
ADR 0004's arithmetic on that is decisive — a 3.3 V/2.5 V span needs 3.6× of
scaling instead of 1.8×, doubling every op-amp error term on the pitch channel.
**DAC8568 is the right call and the ADR's reasoning holds.**

**Two bring-up items the BOM should carry as notes, not just the ADR:**

- The internal reference is **disabled by default**. ADR 0006 says this; put it in
  the BOM note too, because the BOM is what gets read at assembly.
- Decouple `V_REFIN/V_REFOUT` with 100 nF–1 µF. Not currently in the BOM's
  `C-DECOUPLE` line.

---

## F5 — U-LVL-MOD: move the 74AHCT125 to the DAC's own 5.25 V rail

**Severity: High (for the sequencing event). Confidence: High. Arithmetic plus
standard AHCT/CMOS input specifications.**

ADR 0004 deliberately leaves the module's level shifter on the rack's bus +5 V,
reasoning that this keeps its switching current off the DAC supply and leaves
only a cheap buffer exposed to an unprotected rail. Both arguments are weaker
than they look, and the arrangement creates two real problems.

### Problem 1: a clamp event on every power-on

At rack power-on, the bus +5 V rises with the rack supply. The DAC's AVDD rises
behind the reverse-polarity Schottky *and* behind the LM317's **7.7 ms ADJ
soft-start** (F3). For several milliseconds, the 74AHCT125's outputs are at
~5 V driving DAC inputs whose supply is still near zero. Current is limited only
by the buffer's output impedance (~30 Ω), so well over 100 mA flows into the
DAC's input protection diode. The usual family limit is ±20 mA. **This happens
every single time the rack is switched on.**

### Problem 2: V_IH headroom of about 10 mV

Eurorack's +5 V is ±5 %, so the bus can sit at 5.25 V. A CMOS buffer driving a
CMOS input with no DC load puts its output essentially at its own rail. The DAC's
input absolute maximum is AVDD + 0.3 V. With the *current* 240R/768R divider,
worst-case AVDD is 4.96 V, so the limit is 5.26 V against a possible 5.25 V drive.

| | Margin |
|---|---|
| Current divider (240R/768R, 1 %) | **10 mV** |
| With F3's divider (120R/383R, 0.1 %) | 90 mV |

Neither is a design margin.

### Recommendation

**Power `U-LVL-MOD` from the LM317's 5.25 V rail, not the bus +5 V.** Then:

- Both sides of every DAC digital input are on the same rail. The clamp question
  and the V_IH question both disappear by construction, not by arithmetic.
- V_IH at the DAC is 0.7 × 5.25 = 3.675 V; the AHCT drives 5.25 V. 1.57 V of
  margin, permanently.
- The AHCT's TTL input threshold is 2.0 V regardless of its V_CC across
  4.5–5.5 V, so the 3.3 V side is unaffected.
- The module stops depending on the rack's +5 V rail at all. That does not change
  ADR 0005's decision that +5 V is a stated property of the target rack — it just
  means the design no longer leans on it.

**Cost:** roughly 3 mA more on the LM317L (1 mA static plus dynamic). Dynamic
current is genuinely small: three lines at 2 MHz into ~10 pF of DAC input
capacitance is `3 × 10 pF × 5.25 V × 2 MHz ≈ 315 µA` average, with nanosecond
spikes that the 100 nF local decoupling handles entirely. ADR 0004's concern
about "switching current on the DAC's supply" is real in principle and about
three orders of magnitude below significance here. LM317L dissipation goes from
~88 mW to ~100 mW in TO-92 — an 18 K rise, fine.

**Regardless of which rail is chosen, fit 470 Ω–1 kΩ in series in each of SCLK,
MOSI and CS between the buffer and the DAC.** At 1 kΩ into ~10 pF the RC is
10 ns, invisible against a 500 ns bit period at 2 MHz, and it bounds any residual
clamp current to ~5 mA. This is the same class of fix as `R-OPAMP-IN`, which the
design already applies for exactly this reason on the analog side.

---

## F6 — U-KEYS: "74LVC165A" does not resolve to a mainstream part

**Severity: Medium. Confidence: Medium-High.** Searched; the only hits for
`74LVC165A` are broker listings and datasheet-aggregator noise (one of which
describes it as a 16-bit buffer/line driver, which it is not). Nexperia's current
catalogue for this function is **74LV165A** (datasheet Rev. 5, April 2024 — very
much alive); TI's is **SN74HC165** and **SN74LV165A**. I could not find an LVC
165 from any first-tier manufacturer.

This matters because four of these go on four satellite boards inside a body that
cannot be reopened. A brokered part is not an acceptable supply for that.

### Recommendation: `SN74LV165AD` (SOIC-16)

This is not a compromise — it is the part ADR 0001's own reasoning describes:

- **Natively specified at 3.3 V** (V_CC 2–5.5 V), which is the stated reason LVC
  was chosen. The BOM's justification *"kept for its native 3V3 spec"* applies to
  LV exactly as well. (It does not distinguish LV from HC either: plain 74HC is
  specified 2–6 V, so 3.3 V is native for HC too. Only **HCT** requires 5 V. The
  BOM note is wrong on this point.)
- **Output drive around ±6 mA** rather than LVC's ±24 mA, so the last QH→MISO hop
  over 14 inches of unterminated loom rings less — which is the direction ADR
  0001's corrected rationale explicitly wants to move in.
- In production, first-tier, stocked, SOIC-16, same footprint.

**`CD74HC165M` remains the drop-in fallback** if E4 shows anything unexpected,
exactly as the BOM says. One clarification worth recording: at 3.3 V, 74HC's
clock-to-Q is slow (tens of nanoseconds), and in a daisy chain that *helps* —
the cascaded QH→SER path is a hold-time problem, not a cumulative-delay problem,
and slower clock-to-Q buys hold margin. ADR 0001's item 3 (order the chain so data
flows toward the clock source) is attacking the same thing from the other side.
Both are correct.

### Confirm at layout

- `CLK INH` tied low at every device.
- All 14 spare parallel inputs tied high or low — which the marker-pattern scheme
  in ADR 0001 does for free. That is a genuinely good piece of design: it kills
  the floating-input problem and produces a framing check from the same wires.
- 100 nF per device is already in the BOM as `C-DECOUPLE-165` ×4. ✔

---

## F7 — U-DIFFRX: pick one part number, and the reasons point to the INA828

**Severity: Medium (specification gap). Confidence: High. Key specifications
verified.**

The BOM line reads "INA821 or INA828". That is a decision, not a part.

| | INA821 | INA828 |
|---|---|---|
| Offset | 35 µV | 50 µV |
| Offset drift | 0.4 µV/°C | 0.5 µV/°C |
| Noise | 7 nV/√Hz | 7 nV/√Hz |
| Gain equation | G = 1 + 49.4 k/R_G | G = 1 + 50 k/R_G |
| Character | High bandwidth | Low power |

Both are enormously over-specified for this job, which is the honest headline.
Against the design's actual requirements:

| Requirement | Needed | Delivered | Margin |
|---|---|---|---|
| CMRR at G ≈ 2, DC–500 Hz | 60 dB (ADR 0003) | ≥94 dB min | **34 dB** |
| Offset drift over a 15 K session | — (auto-zero corrects it anyway) | 0.5 µV/°C × 15 K × 2.13 = **16 µV** at the output | irrelevant |
| Noise in a 500 Hz channel | below sensor noise | 7 nV/√Hz × √500 = **157 nV** RTI | irrelevant |
| Output swing to +10 V on ±12 V | 10 V | rail-to-rail, ~11.8 V | ✔ |

**Pick the INA828 (`INA828IDR`), on one concrete and one general ground.**

*Concrete:* the design's gain is ~2.13×. With the INA828's 50 kΩ internal
resistor, `R_G = 50 k/1.13 = 44.25 kΩ`, and **44.2 kΩ is an exact E96 value**
giving G = 2.1312. The INA821 wants 43.72 kΩ; the nearest E96 is 43.2 kΩ, giving
G = 2.1435 — a 0.6 % error. Neither matters (the panel gain knob is downstream),
but landing on an exact standard value for free is worth taking.

*General:* the INA828's lower bandwidth and lower quiescent current are the right
direction for a channel deliberately band-limited to 500 Hz. The INA821's extra
bandwidth is something this design would have to filter away.

### The design gets three in-amp details right, and they are worth confirming

1. **The REF pin is driven from a buffered DAC channel, not a divider.** Any
   source impedance at REF unbalances the internal difference amplifier and
   degrades CMRR directly. This is the single most commonly made in-amp mistake
   and the design avoids it explicitly. ✔
2. **Buffered gigaohm inputs make the protection resistors free.** With ~0.5 nA
   of input bias current, 10 kΩ in the BREATH leg contributes 5 µV of offset and
   nothing to CMRR. The verification pass's observation — that buffering does not
   defeat the sense return but perfects it — is correct. ✔
3. **The common-mode range is fine, and worth checking rather than assuming.**
   Worst case is V_diff = 4.8 V with V_cm = 2.4 V at G = 2.13, which puts the
   internal first-stage outputs at 2.4 ± 5.11 V = −2.71 V to +7.51 V, against
   ±12 V rails with ~1.2 V of headroom each. No diamond-plot violation, with
   3 V to spare. ✔

### One thing to add

**Put 10 kΩ in series on the AGND leg as well as the BREATH leg.** The BOM lists
neither (see F20), but when they are added, symmetry costs one resistor and buys
protection for the −IN input against a fault on the sense-return conductor. With
a buffered-input in-amp there is no CMRR penalty either way, so there is no
reason not to.

---

## F8 — U-DIFFRX / U-DAC interface: a unipolar DAC channel cannot null a positive sensor offset

**Severity: High. Confidence: High. Arithmetic.**

This is the one finding here that is about topology rather than part choice, but
it is a direct consequence of which parts were chosen, and it is cheap now and
expensive after fabrication.

The breath receiver output is:

```
V_out = G × (BREATH − AGND) + V_REF
```

At zero breath the sensor sits at 0.200 V (`Vout = VS × (0.1533·P + 0.04)` at
VS = 5.000 V, P = 0). So with G = 2.13:

```
V_out(zero breath) = 2.13 × 0.200 + V_REF = 0.426 V + V_REF
```

To make the breath CV read 0 V at zero breath, **V_REF must be −0.426 V**.

`U-DAC` channel 6 is a DAC8568 output. Its range is **0 to +5 V**. It cannot go
negative. As drawn, the ambient-zero mechanism can only push the breath output
*further positive* — it can add offset, never remove it.

The review raised this as R12 ("a unipolar 0–5 V DAC channel summed additively
**can only add**, and the sensor's offset needs subtracting. Not addressed
anywhere"). The fix that was adopted moved the injection point to the in-amp REF
pin, which resolves the *authority* question (REF is a genuine low-impedance
summing node) but not the *sign* question.

It also gets worse with temperature, which is the whole reason ADR 0006 made the
zero continuous: a gauge sensor's offset drifts *upward* as often as downward, and
the correction must be bidirectional.

### Fix: use the same trick the mod channels already use

ADR 0006 solved the identical problem for the mod channels with
`Vout = 4 × (Vdac − Voffset)`. Apply it here:

```
V_REF = k × (V_dac6 − V_dac7)
```

where `V_dac7` is the **2.5 V pedestal channel the design already has and already
buffers** for the mod channels. With k = 1 and a unity-gain difference amplifier,
V_REF spans −2.5 V to +2.5 V — comfortably covering the −0.43 V needed with room
for the thermal excursion in both directions.

**Cost: one op-amp channel** (which the F11 quantity recount already argues for)
and four resistors. **No new part number**, no new DAC channel, and it reuses the
pedestal that is written once at boot.

Two alternatives, both worse: reference the breath summing stage to a fixed
negative pedestal (one more trim to drift), or do the subtraction digitally in the
instrument (impossible — the instrument has no DAC, as ADR 0003 establishes).

**Check this against the schematic before layout.** If the intended arrangement
already had a difference stage at REF, this finding collapses to "write it down."
If it did not, the auto-zero cannot work.

---

## F9 — U-ADC: the anti-alias capacitor gives a 120 Hz corner, not 600 Hz

**Severity: Medium-High. Confidence: High. Arithmetic.**

ADR 0003: *"220 nF gives a ~600 Hz corner and 58 dB at 500 kHz."*

The 58 dB figure is right *for a 600 Hz corner* — `20·log10(500000/600) = 58.4 dB`
— so the intent is clear. But the corner is set by the source impedance the cap
actually sees, and that is the divider's Thévenin resistance:

```
R_th = 10 kΩ ∥ 15 kΩ = 6.0 kΩ
f_c  = 1 / (2π × 6.0 kΩ × 220 nF) = 121 Hz
```

**The ADR's number implies a ~1.2 kΩ source.** The divider is 5× stiffer than
that, so the filter is 5× slower than designed.

### Why it matters: 1.3 ms of note-on latency

A single pole's group delay at DC is `1/(2πf_c)` = **1.32 ms**. For a breath
attack (a ramp, not a step) the output lags the input by exactly that time
constant. The note gate fires on this signal.

| | Stated | Actual with 220 nF |
|---|---|---|
| Breath digital path total | ~2.6–2.9 ms | **~3.9–4.2 ms** |
| Against the 5 ms target | comfortable | 80 % consumed |

The latency budget has no row for this filter at all, which is how it stayed
invisible.

### Fix: `C-AA-ADC` = 47 nF, not 220 nF

```
f_c = 1 / (2π × 6.0 kΩ × 47 nF) = 564 Hz
Attenuation at 500 kHz = 20·log10(500000/564) = 59 dB
Group delay = 1/(2π × 564) = 282 µs
```

That is the filter the ADR describes, with the attenuation it claims, at roughly
one loop period of delay instead of five.

**Check the other two jobs the cap does:**

- *Sample-capacitor reservoir.* The MCP3202's sample capacitor is 20 pF
  (datasheet-verified, with ~1 kΩ of switch resistance). Charge sharing with
  47 nF droops the held voltage by `20 p / 47 n = 0.043 %` = 1.7 LSB at 12 bits.
  With τ = 6 kΩ × 47 nF = 282 µs against a 250 µs sample interval the recovery is
  partial, so expect a steady-state gain error around 0.07 % — a fixed scale
  factor that calibrates out, not noise. ✔
- *Source-impedance fix.* Microchip wants ≤1 kΩ of source impedance; the divider
  is 6 kΩ. 47 nF still decouples the converter's charge demand from the divider's
  DC impedance by 2350×, which is what makes the 6 kΩ acceptable. ✔ The
  verification pass was right that this single capacitor is the keystone of the
  R11/R43/R49 cluster — it just needs to be the right value.

**Confirm at the bench** by stepping the input and measuring the settled code
against a slow reference reading.

---

## F10 — U-ADC: the MCP3202 is the right part, with two free improvements and one number to write down

**Severity: Low–Medium. Confidence: High. Key figures datasheet-verified**
(20 pF sample capacitor, ~1 kΩ switch resistance, 100 ksps at 5 V, 50 ksps at
2.7 V).

The part fits the requirement well and is not over-specified:

| Requirement | MCP3202 | Verdict |
|---|---|---|
| SAR, not delta-sigma | SAR, essentially zero group delay | ✔ — and the rule should be restated as a number ("converter group delay under 200 µs", per the review's R40) so it does not wrongly veto a better part later |
| ≥4 kHz sample rate | ~65 ksps at 3.3 V (interpolated) | 16× margin |
| Resolution for thresholds, MIDI CC, mod sources | 12 bit; the sensor's divided span of 2.72 V occupies ~3380 codes ≈ 11.7 effective bits | ✔ — 16 bits would be unusable precision. The 2021 instrument ran 10 bits into 7-bit CC and played fine |
| Spare channel | 1 spare | see below |
| SOIC-8 | ✔ | Policy-preferred |

**12 bits bites in exactly one place**, and the review found it (R42): the bottom
of a gamma curve, where γ = 0.5 magnifies low-end steps ~5×. The fix is free and
costs no hardware — take two taps off one sample stream, raw for the note gate
(which needs speed) and N = 8 decimated (+1.5 bits) for mod, MIDI and display
(which need bits, not speed). Worth carrying into the firmware notes.

### Improvement 1: put the spare channel on the 5.000 V reference

The MCP3202 has no separate V_REF pin — pin 8 is VDD/V_REF. So the digital breath
reading is the ratio of the sensor's REF5050 supply to the **dev board's 3.3 V
LDO**, which is a completely unrelated regulator sharing a die with a WiFi-capable
SoC's bursty digital load.

Both ADC channels share V_REF = VDD. So:

```
breath_code / ref_code   is independent of VDD, exactly
```

**Put a divided copy of the buffered 5.000 V rail on CH1**, using the same 0.6×
ratio so it lands at 3.00 V — inside range, near full scale, good resolution. Two
resistors, no new part number, and it makes the digital breath reading immune to
whatever the ESP32's 3.3 V rail is doing. The BOM already says "one spare
channel"; this is what to spend it on.

(The verification pass reached the same conclusion and correctly rejected the
alternative of running the ADC at 5 V, which would need CLK, DIN *and* CS shifted
up rather than just DOUT down.)

### Improvement 2: write down the clock rate

ADR 0001 specifies a 2 MHz SPI bus. The MCP3202's maximum clock is ~0.9 MHz at
2.7 V and ~1.8 MHz at 5 V, so **at 3.3 V it is roughly 1.1 MHz**. Over-clocking a
SAR does not produce an error flag — it produces subtly wrong codes.

SPI2 carries both the DAC8568 (50 MHz capable) and the MCP3202. ESP-IDF supports
per-device clock configuration on a shared host, so this is a one-line firmware
matter — but it is currently written down nowhere, which is how it becomes a
three-day debugging session in six months.

---

## F11 — U-OPA-PITCH / U-BUF: right part, right reasoning, quantity short by one

**Severity: Low. Confidence: High on the part, Medium on the count (no schematic
to check against).**

The OPA2197 is correct and the single-part-number decision is right. Against the
design's demands:

| Requirement | OPA2197 | Margin |
|---|---|---|
| ±12 V rails | Rated to ±18 V | ✔ |
| ±10 V output at gain 4 | RRIO, ~±11.45 V on ±12 V | 1.45 V |
| 0.2 V output on a single +12 V rail (breath buffer) | within ~30 mV of ground | ✔ |
| Offset drift on pitch | ~0.25 µV/°C typ; over 10 K at gain 2 that is ~5 µV at the output, against 83.3 mV/semitone | **~0.006 cents** |
| Gain of 4 at 2 kHz | 10 MHz GBW → 2.5 MHz closed-loop | 1000× |
| Noise in a 500 Hz channel | 5.5 nV/√Hz → 123 nV | irrelevant |

**It is comfortably over-specified even for pitch**, which the brief asks me to
say. For context: a TL072 would contribute roughly 0.4 cents per 10 K, against a
pitch trimmer that ADR 0006 already accepts at 2.4 cents and a VCO that drifts
~3.5 cents. So the op-amp was never the limiting term in the first place. The
ADR's "not TL072" instinct is right but the margin it buys is 400× larger than
needed.

**Keep it anyway.** One part number across pitch, four mod channels, the breath
stage, the reference buffer and the instrument buffer removes a whole class of
"which chip goes where" errors on a hand-built one-off, and the saving from using
an OPA2196 or a TL07x on the mod channels is a few dollars against a project that
has already decided cost is a minor consideration. This is the right trade and it
is well argued in ADR 0004.

One genuine technical advantage worth recording: **the OPA197's e-trim input
stage uses an internal charge pump rather than a complementary input pair**, so
there is no common-mode crossover distortion region near the positive rail. On a
gain-of-4 mod stage swinging ±10 V that matters; a classic dual-pair RRIO part
would produce a distortion step mid-swing. Confirm against the datasheet's
V_CM specification, but this is the reason to prefer this family over, say, an
MCP6002 or an OPA2340 in this role.

### Quantity

Enumerating the amplifiers the ADRs describe:

| Function | Channels |
|---|---|
| Pitch scaling + output buffer | 2 |
| Mod 1–4 difference amplifiers, gain 4 | 4 |
| Mod 2.5 V pedestal buffer (DAC ch 7) | 1 |
| Breath: post-in-amp gain/offset + output buffer | 2 |
| Ambient-zero conditioning into the in-amp REF (F8) | 1 |
| **Total** | **10** |

Five duals is exactly 10 channels, with **zero spare** — and that count assumes
the breath stage needs only two. **Buy seven.** They are a few dollars each, they
are the same part number as the instrument's, and running one short mid-build on
a one-off is a week.

### One thing to watch on U-BUF

The reference buffer drives the MPXV4006DP's supply pin. **An RRIO CMOS op-amp
driving a large capacitive load is a classic oscillator.** The OPA2197 is
typically stable to a few hundred picofarads without isolation.

The right arrangement, which also happens to be the natural one:

- Put the **bulk capacitance on the REF5050's output** (TI recommends 1–10 µF
  there), where it is driving a reference's output stage designed for it.
- The buffer's non-inverting input is high-impedance and loads nothing.
- Put only **100 nF** at the sensor's V_S pin.

The sensor draws a near-constant ~10 mA, so there is no transient demand
requiring bulk at the load. If the bench shows ringing, add 4.7–10 Ω between the
buffer output and the cap — but note that any series resistance there is a
*direct multiplicative error* on a ratiometric sensor (10 Ω × 10 mA = 100 mV =
2 % of scale), so it must go inside the feedback loop or be calibrated out. Best
avoided by keeping the load capacitance small in the first place.

---

## F12 — U-REF-BREATH: over-specified on the axis that does not matter, correct on the one that does

**Severity: Low (informational). Confidence: Medium-High, from memory** — REF50xx
A grade = ±0.05 % initial, 3 ppm/°C max; non-A = ±0.1 %, 8 ppm/°C. Worth a
datasheet glance but it does not change the verdict.

The BOM already carries the full orderable number, `REF5050AIDR`, which is more
than most lines do. ✔

**It is over-specified, and the ADR says so itself without drawing the
conclusion:** *"Absolute accuracy is not what matters. Breath is zeroed at ambient
and the module's gain knob sets the span."* Initial accuracy of ±0.05 % is
therefore buying nothing at all, and 3 ppm/°C versus 8 ppm/°C buys a span shift
of 0.005 % versus 0.012 % over a 15 K session — both inaudible on a channel whose
own sensor is specified at 2.5 % maximum error.

**`REF5050IDR` (non-A) would be identical in service and cheaper.** I would not
bother changing it — the difference is a few dollars on a one-off and the A grade
is equally available — but it should be recorded as a place where the design is
buying precision it cannot use, because that is the honest accounting.

**What actually matters here is line rejection, and the choice is right for it.**
The failure mode ADR 0003 identifies is *dynamic* rail excursion coupling into a
ratiometric sensor. The REF5050 sits on +12 V, upstream of and completely
isolated from the 5 V buck that carries the AMOLED and WiFi transients. A series
reference on the quiet rail, buffered, is the correct topology, and the 30 dB
error the ADR found in the original arrangement was the single most valuable
catch in the review.

**Two checks:**

- REF50xx input maximum is 18 V. The umbilical is +12 V, so a transient headroom
  check against the TVS clamping voltage in F2 is worth doing — an SMAJ15A clamps
  around 24 V, which is above the REF5050's rating. Consider a series resistor or
  a lower-clamping part on that branch, or accept it as an ESD-only event.
- The reference alone can source ±10 mA against the sensor's 10 mA. The buffer
  removes the question, and it is free because the other half of the package is
  the breath buffer. Good decision, correctly reasoned. ✔

---

## F13 — U-BREATH: right part, wrong package in the BOM, and it cannot be socketed

**Severity: Medium. Confidence: High. Verified** — distributor and datasheet
listings give MPXV4006DP as **8-SOP surface mount, case 1351-01, dual port**,
4.75–5.25 V, 10 mA, 766 mV/kPa, operating range −10 °C to +60 °C.

The part choice is correct and the reasoning is the best sourcing decision in the
project: identical transfer function to the obsolete GP, in production, and it
deletes the hoarding problem. The verification against the ADR's own transfer
function (`5 × (0.1533 × 6 + 0.04) = 4.799 V`) checks out. **Keep it.**

Three corrections:

**1. The BOM package column is wrong.** It reads *"case 1351-01, dual side ports,
THT leads"*. There are no THT leads — it is an 8-lead gull-wing SOP at 1.27 mm
pitch. The review flagged exactly this error for the GP and it was carried over to
the DP unchanged. Hand-solderable ✔, policy-compliant ✔, but the carrier layout
needs SMT pads and a keep-out for the port stubs.

**2. "Socketed or otherwise replaceable" is not achievable as drawn.** ADR 0003
says to treat the sensor as a wear part and socket it. An SMT SOP-8 with tube
stubs cannot be socketed. If the wear-part plan is to survive, the sensor needs
to go on **a small mezzanine PCB with a 0.1" header** into the carrier, so the
whole assembly — sensor, tube stub, trap — lifts out. That is a layout decision
that has to be made now.

**3. The operating temperature range is narrower than the project assumes.**
−10 °C to +60 °C, with the 2.5 % error band specified over +10 °C to +60 °C *with
auto-zero*. The instrument documents a 10–20 K interior rise in a sealed oak
body. At a 25 °C room that is 35–45 °C — inside range, but the margin to 60 °C is
15 K, not the comfortable band the thermal discussion implies. The M8 soak
already puts a thermocouple at the sensor; **record the absolute temperature, not
just the rise.** And note that the datasheet's accuracy figure is *conditional on
auto-zero*, which vindicates ADR 0006's continuous-zero decision on a second,
independent ground.

**Burst pressure** against a 15–20 kPa cough into a sealed mouthpiece remains an
open bench item (the review listed it). The 6 kPa range is the right choice for
playing; the question is only survival of an abuse event.

---

## F14 — U-MCU-RT: the board is right; the `5V` pin needs a diode, not a measurement

**Severity: High. Confidence: Medium-High** (board-specific; the general pattern
is near-universal on Waveshare ESP32 boards).

The ESP32-S3-Matrix meets every gate ADR 0007 and ADR 0013 set: native USB
(verified from Zephyr's devicetree, not a listing — good method), 6-axis IMU
onboard, 16 broken-out GPIO against 14 needed, quad PSRAM. **Keep it.**

The review flagged "is the header `5V` pin raw USB VBUS?" as the **highest
bench-damage risk in the project**, and it is still an open measurement rather
than a design. On most boards in this family the header `5V` pin connects
straight to VBUS with no isolation. That means: buck output and USB host output,
hard-paralleled, every time the instrument is flashed.

**Do not leave this as a measurement.** ADR 0005 already says "OR the umbilical
power with USB power — it costs a diode". Specify the diode:

```
buck 5.0 V ──[Schottky]──┬── real-time board 5V pin
                          └── display board 5V pin
USB VBUS ────────────────┘  (through the board's own connector)
```

- Part: **`PMEG4050EP`** (SOD-128, 0.4 V at 1 A) or **`SS54`** (SMA, ~0.45 V at
  1 A). Either is trivially hand-solderable.
- Keep `U-LVLSHIFT` (the LED data buffer) on the **undiodéd** 5.0 V, so the
  74AHCT125 keeps a full-rail V_CC and the WS2815 data margin is not reduced.
- Cost: ~0.35 V, so the boards see ~4.65 V at their `5V` pins. Their onboard
  3.3 V LDOs need roughly 1.0 V of dropout at a few hundred milliamps, leaving
  ~3.65 V in — adequate, but check the specific LDO fitted. If it is an AMS1117
  at 400 mA the margin is thin and a lower-V_f part matters.

**A side benefit worth noting.** The board's onboard 8×8 matrix is WS2812C-2020,
driven directly from GPIO14 at 3.3 V with no shifter. WS2812-class V_IH is
0.7 × V_DD, so at 5.0 V that is 3.5 V — the matrix is being driven *below* its
specified threshold, which is a known Waveshare-board marginality. Dropping the
board's supply to 4.65 V through the OR diode moves V_IH to 3.26 V and puts the
3.3 V drive **above** threshold. The diode fixes a second problem for free.

---

## F15 — U-DISP: the SY6970 PMU is the one active part on the display board that is a liability

**Severity: Medium. Confidence: Medium** (board-revision dependent).

The T-Display-S3 AMOLED is the right *display* choice — ADR 0008's shape argument
(a 2.2:1 strip on a 57 mm-wide body) is sound and the four-pin requirement after
ADR 0013 means almost anything clears the pin budget.

The problem is a part ADR 0008 lists as harmless: *"It carries little that goes
unused… boards in this category often bundle a PMIC, battery charging and an
onboard IMU. None of that helps here."* The review found that it is not merely
unused — the **SY6970 PMU is documented as unstable on 5 V with no battery
attached**, and this design is deliberately battery-free.

The failure mode is a PMU that cycles or misbehaves on the input rail, on the
board that sits closest to the breath sensor's thermal zone and shares the 5 V
buck with the real-time board.

### What to do

1. **Bring this board up on the buck rail at E1, before anything else depends on
   it.** Not "measure it eventually" — this is a go/no-go on the board.
2. **If it misbehaves, the software fix is first:** configure the SY6970 over I2C
   at boot to disable charging, disable the charge watchdog, and set the input
   current limit to maximum. Several projects using this board do exactly this.
3. **If that does not settle it, the fallback is any S3 board without a PMU.**
   ADR 0008 already names the Waveshare ESP32-S3-Touch-AMOLED-1.8 as the runner-up
   and rejects it on shape, not capability. Since the display board is a terminal
   that needs four pins, the switching cost is a firmware retarget, not a
   redesign.
4. Either way, `C-BULK-DISP` (currently `TBD` / `open` in the BOM) needs a value.
   The latency budget names WiFi transients reaching the analog section through
   shared power as the only remaining WiFi coupling path. **470 µF electrolytic
   plus 10 µF ceramic at the board's 5 V pin** is the right starting point;
   confirm from the measured load-step response.

---

## F16 — U-WATCHDOG: the right idea in a mediocre part, with three unspecified essentials

**Severity: Medium. Confidence: High on the reasoning, Medium on the part
comparison (from memory).**

The frame watchdog is one of the best ideas in the design. *"A stuck CV drones the
rack forever and nothing notices"* is exactly right, the DAC's own CLR pin does
precisely what is wanted, and putting it at the module — independent of the thing
that hung — is the correct placement.

The **74HC123** will work but it is the weaker of the two obvious choices. Its
pulse width is `t_W ≈ 0.45 × R_ext × C_ext` with wide part-to-part, supply and
temperature variation, and it is historically sensitive to layout and trigger-edge
quality.

**Recommend `CD74HC4538M` (SOIC-16, dual precision retriggerable monostable)**
instead. Same package, same pin count, same function, materially better-specified
timing. For a watchdog the absolute accuracy does not matter — but a part whose
timeout wanders by 40 % between "busy loop" and "hung" is the wrong tool for
setting a threshold between those two states.

### Three things that must be specified and currently are not

**1. Which rail.** The DAC's CLR input is AVDD-referenced with
V_IH = 0.7 × AVDD = 3.675 V at 5.25 V. There is no 3.3 V on the module. If F5 is
adopted, **run the monostable from the same LM317 5.25 V rail as the level
shifter** — then CLR's thresholds and clamps are correct by construction, exactly
as for SCLK/MOSI/CS.

**2. The timing components.** For a ~100 ms timeout retriggered by CS edges every
250 µs, use `R = 1 MΩ, C = 220 nF` (HC123) — and **the timing capacitor must be
C0G or film, not X5R/X7R and certainly not electrolytic.** High-K ceramic's
voltage coefficient and electrolytic leakage both shift the timeout by tens of
percent, and leakage in particular turns a fixed timeout into a
temperature-dependent one.

**3. A bring-up defeat.** The DAC8568's CLR is an asynchronous level-sensitive
clear. At power-on the monostable is untriggered, so CLR is asserted and the DAC
is held at zero scale until SPI traffic starts. That is the *desired* behaviour —
and it is also **visually identical to the "internal reference not enabled" trap
that ADR 0006 already warns about**. Two independent causes of "every channel
reads 0 V and the board looks dead" is one too many.

> **Fit a jumper or a solder link that forces CLR high.** At E7, pull it, confirm
> the DAC works, then fit it and confirm the watchdog works. Ten cents,
> five minutes, and it separates two failure modes that otherwise look the same.

**Polarity check:** trigger from **CS**, not SCLK. A CS falling edge retriggers at
the start of every frame, so CLR releases before the first word is latched. A hang
with CS stuck low produces no edges and asserts CLR, which is the case the
watchdog exists for. ✔

---

## F17 — U-LVL-MOD: the OE gating has no parts behind it

**Severity: Low. Confidence: High.**

ADR 0004 requires the module's 74AHCT125 output-enable to be gated from umbilical
+12 V presence, so that "instrument absent" is a state the hardware knows about.
This is correct and it is the reason the power switch had to move to the module.

**No components for it appear in the BOM.** A bare resistive divider from +12 V
to a 5 V logic level would work electrically but produces a slow edge into a
non-Schmitt OE input, which can oscillate through the transition. That is harmless
here (CS is pulled high by `R-SPI-PULL`, so a momentary OE glitch cannot latch
anything), but it should be a decision rather than an accident.

**Simplest correct implementation:** divider from umbilical +12 V (e.g. 100 kΩ /
39 kΩ, giving 3.4 V at 12 V), clamped by a 5.1 V zener, into a spare gate of the
**74AHCT14** that ADR 0004 already earmarks as the fallback if the umbilical needs
edge cleanup. If the AHCT14 is not fitted, a 2N7002 inverter and a pull-up gives
the same clean edge with two parts. Either way, add the line to the BOM.

---

## F18 — U-BUCK: keep it, but damp the input LC

**Severity: Medium. Confidence: Medium-High** (standard input-filter theory;
severity depends on the actual filter values chosen).

The R-78E5.0-1.0 is the right part for this design and ADR 0005's reasoning is
sound: a 3-pin SIP on a 7805 footprint, no inductor, no feedback network, no
layout risk. It is among the lowest-risk parts in the project and it deletes the
whole class of "my buck oscillates" problems. ✔

Input range 7–28 V against ~11.5 V arriving after the Schottky and cable drop ✔.
1 A against 330–400 mA of dev boards plus a clamped matrix ✔, with the module's
load switch bounding the pathological case from upstream ✔.

**If headroom ever looks tight, the drop-in is `OKI-78SR-5/1.5-W36-C`** — same
3-pin SIP footprint, 1.5 A instead of 1.0 A. Worth knowing it exists before the
carrier is laid out, since the footprint is identical and the decision then costs
nothing.

### The finding: `L-BUCK-IN` plus the bulk capacitance forms an undamped LC in front of a switching converter

ADR 0004 correctly replaced the ferrite bead with a real inductor ("this is the
part the bead was wrongly credited for"). But a switching converter presents a
**negative incremental input resistance**, and an undamped LC filter in front of
one is the classic Middlebrook input-filter instability.

With 22 µH and 470 µF:

```
f_0 = 1 / (2π × √(22 µH × 470 µF)) = 1.56 kHz
```

which is squarely in the band the design cares about, and right on top of the
WS2815 PWM rate.

**Fix, two parts:** make the bulk at the buck input an **aluminium electrolytic
with meaningful ESR (0.5–1 Ω), not a ceramic**, or add a damping leg — 100 µF in
series with 1 Ω across the filter capacitor. At 3 W of converter power the
instability is unlikely to be violent, but a 1.5 kHz ringing input filter on the
rail that also feeds the REF5050 and the LED strips is not something to leave to
chance in a body that cannot be reopened.

**Also worth recording:** the R-78E's switching frequency **moves with load**.
ADR 0003 identifies this correctly ("the alias frequency *moves* with the
converter's load-dependent switching frequency, so it is a wandering tone rather
than a fixed one") and it is the reason F9's anti-alias corner has to be right
rather than approximately right.

---

## F19 — Discrete diodes: two free upgrades

**Severity: Low–Medium. Confidence: High. Standard part ratings.**

### D-REVPOL: 1N5817 → 1N5819 / 1N5822

The 1N5817 is 20 V / 1 A. Two problems:

**Reverse voltage.** ADR 0004 justifies the diodes on the grounds that *"reversed
ribbon cable is the classic Eurorack failure and the keying alone is not worth
trusting."* But the failure being defended against is not just a clean reversal —
it is a **row-offset insertion**, which can put +12 V against the −12 V diode and
present it with **24 V reverse**. That exceeds the 1N5817's 20 V rating.

**Forward current.** The +12 V leg carries the instrument's entire draw. The
review's verification pass put that at 300 mA typical, 600 mA peak, ~1.25 A
ceiling. A 1 A diode against a 1.25 A ceiling has no margin.

| Leg | Current | Recommend | Why |
|---|---|---|---|
| +12 V | up to ~1.25 A | **`1N5822`** (40 V, 3 A, DO-41) | 3 A and 40 V; same footprint |
| −12 V | ~40 mA | **`1N5819`** (40 V, 1 A, DO-41) | 40 V; same footprint |

V_f penalty is ~60 mV at these currents (1N5819 is ~0.38 V at 300 mA versus the
1N5817's ~0.32 V), which is irrelevant against ~11.5 V arriving at a buck that
needs 7 V. Same DO-41 package, same handling, pennies.

### D-JACK-CLAMP: BAV99 is correct — confirmed

This is a good decision with correct reasoning and it should be recorded as such.
The Schottky-leakage argument holds:

| Part | Leakage (max, 25 °C) | Error through 1 kΩ | Pitch error |
|---|---|---|---|
| BAT54S | ~2 µA | 2 mV | **2.4 cents**, temperature-dependent |
| **BAV99** | ~100 nA | 100 µV | **0.12 cents** |

The configuration is also right: BAV99's internal series pair with the mid-node
brought out maps exactly onto a rail-to-rail clamp — pin 1 to −12 V, pin 2 to
+12 V, pin 3 to the jack. One SOT-23 per output, six outputs. ✔

If you want it free: **`BAV199`** is the ultra-low-leakage version of the same
part in the same SOT-23 package, at ~5 nA maximum. It is unnecessary — 0.12 cents
is already an order of magnitude below the trimmer's contribution — but it costs
the same and is the strictly better part.

### F-POLY: the polyfuse is undersized and may now be unnecessary

A 500 mA-hold PPTC derates roughly 40–50 % at 60 °C. The instrument documents a
10–20 K interior rise on top of ambient, which puts a 500 mA part's effective hold
current somewhere near **300–400 mA — below the instrument's own peak draw.**
That is a nuisance trip, in a sealed body, mid-performance.

ADR 0014 traces exactly this failure mode ("the polyfuse self-heats and its
resistance rises → the rail sags → the buck draws more input current → …") and
concludes that the module's load switch is what actually breaks the loop.

**Two options, both fine:**

- **Delete it.** The load switch at the module now does the job, faster and
  without thermal hysteresis, and it is on the correct side of the cable.
- **Or size it so it never operates.** A **1.1 A hold** 1206 part (e.g. Littelfuse
  1206L110) sits far enough above the load that it stays out of its self-heating
  region and only acts on a genuine short.

Do not leave it at 500 mA. And note that its series resistance sits **upstream of
the WS2815 strips**, which run on unregulated +12 V — the buck regulates its own
drop away, the LEDs cannot.

---

## F20 — Smaller items

**Severity: Low throughout. Confidence: High.**

**a. `C-DECOUPLE` quantity is short.** The BOM says 10 for the module. Counting
supply pins: five OPA2197 on ±12 V = 10, INA828 on ±12 V = 2, DAC8568 = 1,
74AHCT125 = 1, monostable = 1, plus the DAC's V_REF pin = 1. **That is 16, not
10.** Cheap to get wrong and annoying to discover at assembly.

**b. The breath path's protection and filter passives are not in the BOM at
all.** ADR 0003 specifies a series resistor at the instrument buffer output, 10 kΩ
protection resistors at the in-amp inputs, and ~500 Hz band-limiting at both ends.
None of those appear as BOM lines. `R-PD-BREATH` (the differential pulldown) is
there and is correct; its companions are not.

**c. The 500 Hz filters cost more latency than the budget allows for.** A single
pole at 500 Hz has 318 µs of group delay; two of them (both ends, as ADR 0003
specifies) is **636 µs**, against the latency budget's *"buffer, cable, in-amp,
output filter: < 0.2 ms"*. The breath CV total becomes ~2.8 ms rather than the
stated 2.4 ms. Still far inside the 5 ms target — this is a budget-accuracy note,
not a problem — but it is the same class of omission as F9 and worth correcting in
the same pass.

**d. WS2815 data inputs float at power-up.** Add a 10 kΩ pull-down at each
strip's D_IN. Without it the first pixel's state during the buffer's OE
transition is undefined, which is a small contributor to the "strips that work on
the bench and glitch in the build" class of fault ADR 0014 is trying to avoid.

**e. Series termination on the LED data lines.** `R-TERM-CHAIN` gives the key
chain 33–68 Ω at the driving end. The WS2815 data lines get nothing, and they are
AHCT outputs with ~1–2 ns edges driving ~420 mm of unterminated loom. **Add
33–100 Ω in series at each 74AHCT125 LED output**, same reasoning, same cost.

**f. The IMU read does not fit the 4 kHz loop, and the budget has no row for
it.** A 12-byte burst read over 400 kHz I2C is roughly `(12 + 2) × 9 bits /
400 kHz ≈ 315 µs`, against a **250 µs** loop period. If the Waveshare board wires
only SDA/SCL (which CircuitPython's `IMU_SDA`/`IMU_SCL` naming suggests), SPI is
not available as an escape.

> The fix is free and is a firmware decision: **read the IMU on its own cadence
> at 250–1000 Hz, not every loop pass.** ADR 0007's gesture content is under
> 20 Hz, so 250 Hz is a 12× oversample. Use the DRDY interrupt on INT1 (GPIO10)
> rather than polling. Add a row for it to the latency budget so it is not
> rediscovered.

**g. ADR 0007's "no fusion" claim is factually wrong about the part.** The
QMI8658 has an on-chip Motion Co-Processor with an AttitudeEngine. This does not
change the decision — the design wants raw accel and gyro and should not use it —
but the record should say "fusion not used" rather than "no fusion available."

**h. `LT5400`: the design is buying 20× more precision than the channel can
use.** (Passive, included because the BOM calls it the highest-value precision
part in the design.) ADR 0006's own table:

| Source | Drift over 10 K |
|---|---|
| Matched network, 1 ppm/°C tracking | **0.11 cents** |
| 5–10 % pitch trimmer in the ratio | **2.4–3.7 cents** |
| The VCO being driven | ~3.5 cents |

Once the trimmer is in the gain ratio — and ADR 0006 decided it should be, for
good reasons — the matched network's contribution is 20–30× below the trimmer's
and 30× below the load it drives. **Two 0.1 %, 10 ppm/°C thin-film 0805 resistors
(Vishay TNPW or Susumu RG) give ~14 ppm/°C of ratio drift**, which is *better*
than the trimmer's 22–34 ppm/°C and therefore still not the limiting term.

Dropping the LT5400 removes the design's only MSOP part, removes a ~$10 line item,
removes a part number, and costs ~0.1 cents of drift that is already invisible
beneath the trimmer. ADR 0006 half-reaches this conclusion itself — *"the
precision-network argument was over-engineering relative to the load it feeds"* —
and then keeps the part anyway.

I would drop it. If it is kept, keep it **only on pitch** — the mod channels'
gain-of-4 difference amplifiers should use ordinary 1 % discretes, since ADR 0006
is explicit that nobody's ear cares about a few cents' equivalent there, and four
LT5400-7s would be $40 of matching spent on channels that do not want it.

---

## Confirmations — parts that are right, said plainly

These were checked and need no change. A confirmation is a result.

| Part | What was checked |
|---|---|
| **DAC8568C** | Grade behaviour verified (A/C zero scale, B/D midscale). Octal 16-bit with an internal reference and ×2 gain is the correct choice specifically *because* the ×2 gain halves the downstream scaling gain versus an AD5676R — ADR 0004's arithmetic is right |
| **OPA2197** | Every specification clears by two to three orders of magnitude. The single-part-number discipline is worth more on a hand-built one-off than the money it costs |
| **MPXV4006DP** | Transfer function verified against the ADR's own figures. The DP-not-GP sourcing call is the best decision in the BOM |
| **MCP3202** | 12 bits and ~65 ksps at 3.3 V are correctly sized, not over-specified. The SAR-not-delta-sigma rule is right even though its stated justification is 10× overstated |
| **REF5050A** | Correct topology for a ratiometric sensor, on the correct (quiet) rail, correctly buffered. Full orderable P/N already in the BOM |
| **BAV99** | Right part, right configuration, right reasoning about Schottky leakage |
| **74AHCT125 for WS2815** | **Open verification item closed.** The WS2815's logic runs from an internal 5 V regulator and V_IH is 0.7 × 5 V = **3.5 V** — not 0.7 × 12 V. A 74AHCT125 at 5 V is correct and sufficient, and a direct 3.3 V drive would genuinely have been marginal. The shifter is necessary and adequate |
| **QMI8658C** | The right sensor class, and — given that every competitive 6-axis part is 0.5 mm LGA — the only policy-legal way to have one at all. ADR 0007's conclusion that the dev-board IMU *is* the final IMU is correct |
| **R-78E5.0-1.0** | Lowest-risk regulator available for this job. The 12 V-not-5 V umbilical arithmetic in ADR 0005 is correct and the conclusion follows |
| **ESP32-S3-Matrix** | Meets every gate, and the verification method (Zephyr/CircuitPython board definitions rather than product listings) is the right way to have checked |
| **U-ESD-USB, SW-BOOT, J-USB marked not-needed** | Correct. Rebuilding what the dev boards already carry is work for no gain |

---

## Priority order

| | Finding | Why first |
|---|---|---|
| 1 | **F1** — TPS2553 on 12 V | Will not survive first power-on |
| 2 | **F2** — SP3012 on 12 V | Conducts continuously; also protects a 4.8 V precision line at 5.0 V standoff |
| 3 | **F8** — unipolar DAC cannot null a positive offset | The auto-zero does not work as drawn; free to fix before layout, impossible after |
| 4 | **F5** — level shifter rail | Clamp event on every power-on, ~10 mV of V_IH margin |
| 5 | **F3** — LM317 tolerance | Out of the DAC's recommended range at both ends |
| 6 | **F9** — 220 nF anti-alias cap | 1.3 ms of unaccounted note-on latency |
| 7 | **F6** — 74LVC165A | Sourcing risk on four parts inside a sealed body |
| 8 | **F13** — sensor package / socketing | Layout-blocking; "wear part" plan does not survive an SMT footprint |
| 9 | **F14** — USB/buck 5 V collision | Bench-damage risk, and the diode also fixes the matrix's data margin |
| 10 | **F19** — diode ratings, polyfuse sizing | Free upgrades, same footprints |
| 11 | **F7, F16, F15, F18, F20** | Specification and refinement |

---

## Verification status

Verified against datasheets or manufacturer/distributor data during this review:

- TPS2553 input range 2.5–6.5 V
- SP3012 series V_RWM = 5.0 V at I_R ≤ 1 µA
- MPXV4006DP: 8-SOP SMT, case 1351-01, 4.75–5.25 V, 766 mV/kPa, −10 to +60 °C
- DAC8568 grades: A/C reset to zero scale, B/D to midscale; A/B external V_REFIN
  ≤ AVDD, C/D ≤ AVDD/2
- INA821 vs INA828: 35 µV / 0.4 µV/°C / 49.4 k versus 50 µV / 0.5 µV/°C / 50 k,
  both 7 nV/√Hz
- MCP3202: 20 pF sample capacitor, ~1 kΩ switch resistance, 100 ksps at 5 V /
  50 ksps at 2.7 V
- WS2815 V_IH = 0.7 × 5 V internal rail = 3.5 V
- 74LVC165A: no first-tier manufacturer found; 74LV165A (Nexperia, Rev. 5, 2024)
  and SN74HC165 (TI) are the live parts
- LT1641: SO-8, 9–80 V, analog foldback current limit, capacitor-programmed inrush
- TPS2592Ax 4.5–18 V but VSON-10; TPS27S100 40 V but HTSSOP PowerPAD; MIC2039 and
  MIC2545A both 5.5 V class — all three ruled out on package or voltage

Asserted from memory and worth a datasheet glance, though none changes a verdict:
OPA2197 drift and GBW figures; REF50xx A-grade versus non-A grade specifications;
LM317L reference tolerance (±4 %), I_adj (≤100 µA) and minimum load (~3.5 mA);
1N5817/19/22 ratings; BAV99 and BAV199 leakage; 74AHCT125 V_CC range and TTL
thresholds; CD74HC4538 versus 74HC123 timing behaviour; DAC8568 settling and INL.

Sources consulted: [TI TPS2553](https://www.ti.com/product/TPS2553),
[Littelfuse SP3012 series](https://www.littelfuse.com/products/overvoltage-protection/tvs-diode-arrays/low-ultra-low-capacitance/sp3012),
[NXP MPXV4006](https://www.nxp.com/docs/en/data-sheet/MPXV4006.pdf),
[TI DAC8568](https://www.ti.com/product/DAC8568),
[TI INA821](https://www.ti.com/product/INA821),
[TI INA828](https://www.ti.com/product/INA828),
[Microchip MCP3202](https://www.farnell.com/datasheets/1669376.pdf),
[WS2815 datasheet](https://www.led-stuebchen.de/download/WS2815.pdf),
[Nexperia 74LV165A](https://assets.nexperia.com/documents/data-sheet/74LV165A.pdf),
[ADI LT1641](https://www.analog.com/en/products/lt1641.html),
[TI TPS2592Ax](https://www.ti.com/lit/ds/symlink/tps2592al.pdf),
[TI TPS27S100](https://www.ti.com/product/TPS27S100),
[Microchip MIC2039](https://ww1.microchip.com/downloads/en/DeviceDoc/MIC2039-High-Accuracy-High-Side-Adjustable-Current-Limit-Power-Switch-20005540A.pdf),
[Microchip MIC2545A](https://ww1.microchip.com/downloads/en/DeviceDoc/mic2545a.pdf),
[TI LM5060](https://www.ti.com/product/LM5060).
