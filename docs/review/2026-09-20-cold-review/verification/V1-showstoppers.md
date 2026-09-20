# V1 — Falsification pass on showstoppers S1–S7

Method: each item re-derived from the ADRs, the BOM and (where reachable) vendor
data, without reading the register's summary as an authority. The underlying
agent documents (`B5`, `B6`, `B1` …) were consulted *after* deriving, to see
where the register's one-paragraph summary diverges from what the agent actually
wrote. In three cases it diverges materially.

**Egress note.** `ti.com`, `onsemi.com`, `st.com`, `mouser.com`, `octopart`,
`digikey` PDF hosts and every CDN I tried are blocked by the proxy (403 on
CONNECT). `WebSearch` works and returns vendor-page text. So: part facts below
are from search summaries of vendor/distributor pages, not from PDFs I opened.
Each one is labelled with what it rests on.

Summary of verdicts:

| | Register's claim | Verdict |
|---|---|---|
| S1 | TPS2553 is a 2.5–6.5 V part on +12 V | **SURVIVES** (fully) |
| S2 | Ambient-zero injection has the wrong polarity | **SURVIVES BUT DOWNGRADED** |
| S3 | In-amp has no common-mode bias return | **SURVIVES** (fully) |
| S4 | Shared `CLR` zeroes the mod offset | **SURVIVES** (fully) |
| S5 | LM317 cannot meet its own specification | **SURVIVES BUT DOWNGRADED** |
| S6 | `U-TVS-UMB` is a 5 V array across +12 V | **OVERSTATED** (core part error survives; the destruction mechanism does not) |
| S7 | Both current limits below worst case | **SURVIVES IN PART** — polyfuse half survives, limiter half is downgraded, one sub-claim is **FALSE** |

---

## S1 — TPS2553 on the +12 V rail. **SURVIVES.**

### Independent re-derivation

ADR 0005 puts the load switch "on the umbilical +12 V feed", and ADR 0004's
power tree draws it explicitly downstream of the bus +12 V protection diode:
`bus +12V ──[1N5817]──[ferrite]──[bulk]──[TPS2553]── umbilical +12V`. So the
part's `IN` pin sees bus +12 V less ~0.35 V of Schottky ≈ **11.6 V**, and its
`OUT` pin the same. There is no reading of either ADR under which it sees less:
ADR 0005 separately and at length rejects sending 5 V up the umbilical, so the
node it switches is 12 V by decision, not by accident.

Part data (search summaries of TI's own TPS2553 / TPS2553D product pages, plus a
TI E2E thread): operating input range **2.5 V to 6.5 V**; **absolute maximum
V_IN 7 V**. Two independent search routes returned the same range, and the "USB
power switch" framing on the product page is corroborating — this is a 5 V USB
port part.

11.6 V against a 7 V absolute maximum is **+66 % over abs-max**, not a marginal
derating question. It fails on first application of power.

### What I attacked

- **Is there a topology where it sees ≤6.5 V?** No. I looked for a reading where
  the switch sits on the module's 5 V logic rail or on a 5 V umbilical. ADR 0005
  devotes a whole section ("Why 12 V goes up the umbilical, not 5 V") to
  excluding the second, and the switch's stated jobs — inrush into the
  instrument's bulk, umbilical short foldback — are only meaningful on the 12 V
  conductor.
- **Is ADR 0005 aware of the rating?** Confirmed the register's "tell": ADR 0005
  defends the part for two paragraphs purely on **package** grounds ("SOT-23-6 …
  at 0.95 mm pitch it is *coarser* than the TSSOP-16 DAC") and never states an
  input-voltage rating. So the rating was never in scope when the part was
  chosen.
- **Is the datasheet claim reachable?** TI's PDF is blocked. But the 2.5–6.5 V
  figure appears in TI's own product-page copy returned by search, in the TI
  store listing, and in an E2E thread; the abs-max 7 V figure appears in the
  same E2E thread. This is as close to primary as this sandbox allows, and three
  independent pages agreeing on a headline parametric is not the kind of thing
  search summaries get wrong.
- **"Every modern one-chip 12 V eFuse fails the package policy."** I tried to
  break this with a counter-example. Best candidate was **ST STEF01** — 8–48 V,
  fully programmable current limit, programmable start-up time, selectable
  latching or auto-retry thermal shutdown, integrated MOSFET: functionally
  exactly what is wanted. **It is HTSSOP-14 with a thermal pad** (order code
  STEF01FTR), so it fails the policy the same way TPS27S100 does. The register's
  claim held against my best attempt.
- **Is LT1641-2CS8 the only route?** No, and the register overstates by naming
  one part. **LM5069MM (MSOP-10, 9–80 V)** and **LTC4210 (MSOP-8 / SOT-23-6,
  2.7–16.5 V)** are the same architecture (controller + external N-FET + sense
  resistor) in packages the scope explicitly permits ("TSSOP/MSOP acceptable").
  This does not change the finding, only the shopping list.
- **Is the latch-off-vs-auto-retry reasoning sound?** Partly. The stated reason —
  "auto-retry reproduces the oscillating-protection failure ADR 0014 analyses" —
  is a weak analogy: ADR 0014's failure is *thermal positive feedback in a PPTC*,
  which has no counterpart in a fixed-duty retry. The **real** argument for
  latch-off is S7's: with ~1.2 mF of bulk downstream, an auto-retry part that
  aborts a long start hiccups forever and the instrument never boots. Same
  conclusion, different and better reason.

### Verdict and cheapest fix

**SURVIVES, full showstopper status.** This is the one item where the failure is
immediate, physical and unambiguous.

Cheapest correct fix: a hot-swap controller in a permitted package plus an
external N-FET and sense resistor — LT1641-2CS8 (SO-8), **or** LM5069MM
(MSOP-10), **or** LTC4210 (MSOP-8). The register's proposal is one valid member
of that set, not the only one. Whichever is chosen, the **timer capacitor must
be sized for the ~75 ms start into 1.2 mF** (see S7), which is the parameter
that actually decides whether the instrument boots.

**Confidence: very high** on the finding; **high** on the part data, limited only
by not having opened the PDF.

---

## S2 — Ambient-zero injection polarity. **SURVIVES BUT DOWNGRADED.**

### Independent re-derivation

Sensor: MPXV4006DP, `Vout = VS·(0.1533·P + 0.04)`. At `VS` = 5.000 V and
`P` = 0: **V_out = 0.200 V**. Distributor/NXP page data returned by search
independently confirms "output voltage range 0.2 V to 4.7 V, sensitivity
766 mV/kPa" — so the 0.2 V floor is a datasheet property, not an ADR assumption.

Module gain: ADR 0003 has the in-amp "absorb the ~2.13× scaling stage". Check
where 2.13 comes from: 10.00 V / 4.70 V = **2.128**. So the in-amp maps the
sensor's *top* to the jack's top, and carries the 0.2 V floor through with it.

In-amp transfer: `V_out = G·(V_IN+ − V_IN−) + V_REF`.
At rest: `V_out = 2.128 × 0.200 + V_REF = 0.426 + V_REF`.
Nulling requires **`V_REF` = −0.426 V**.

DAC ch 6 is a DAC8568 output: internal 2.5 V reference × gain 2, span
**0 to +5.000 V**, unipolar. It cannot produce −0.426 V. Confirmed.

Direction of drift does not rescue it: the quantity being nulled is
`G × (sensor zero offset)`, which is positive-definite, so the required `V_REF`
is negative for every operating point, not merely at one extreme.

### What I attacked

- **Is the standing error really 4–9 % of full scale?** I get **4.3 %**
  (0.426 V of 10 V) and can reconstruct no route to 9 %. The register's upper
  bound is unexplained; report 4.3 %.
- **Is ADR 0006's power-on table actually falsified?** Yes, but note *why*: the
  table's justification is "the receiver's differential pulldown holds it there",
  which is a statement about the in-amp's **input**. With the instrument
  connected and powered the input is 0.2 V, not 0 V, and the output is 0.426 V
  before any firmware write. The table is right about the unpowered case and
  wrong about the powered one — which is the more common one.
- **Is there a topology that makes it vanish?** Yes, and it is free, which is the
  reason for the downgrade. **Swap the in-amp's input legs and make the existing
  downstream breath stage inverting.** Then `V_inamp = −2.128·V_sensor + V_REF`
  with `V_REF = +0.426 V` from DAC ch 6 (positive, in range), and the downstream
  inverting stage restores polarity: `V_jack = 2.128·V_sensor − 0.426`. Worst
  in-amp excursion is −9.58 V, comfortable on ±12 V. There **is** a downstream
  stage — `U-OPA-PITCH` is 5 × OPA2197 = 10 amplifiers for pitch, four mods and
  "breath scaling", and the gain/offset knobs and the ~2 kHz reconstruction
  filter have to live somewhere. Inverting a stage that already exists costs
  **zero parts**.
  The register's two proposals (inverting downstream stage; difference of two DAC
  channels) are both valid; the first is free, the second costs an op-amp, two
  resistors and the one spare DAC channel.
- **Could the panel offset knob absorb it?** Arithmetically yes (−0.5 V of knob
  authority plus 0 to +5 V of DAC). But the knob is a divider off a ±12 V rail
  with no rejection — this is W3's problem moved onto breath — and it makes the
  panel control a technical trim, which is the split-brain ADR 0006 warns about.
  Not a fix.

### Verdict and cheapest fix

**SURVIVES as a true topology error; DOWNGRADED from showstopper to major.**
Nothing is damaged, nothing is unrecoverable, the error is on the module board
(which is not bonded shut), and the correct fix is a sign flip in a stage that
already exists. The register's own first proposal is the cheapest correct fix.

The part of S2 that deserves to stay prominent is the last clause — **the
continuous auto-zero cannot correct in the direction it needs to** — because
that is the interaction with W11 and W12 rather than a standing DC offset.

**Confidence: very high** on the mechanism and arithmetic; **high** on the
downgrade.

---

## S3 — No common-mode bias return at the in-amp. **SURVIVES.**

### Independent re-derivation

ADR 0003: "Put the pulldown **differentially across BREATH–AGND**, not on one
leg." The BOM agrees: `R-PD-BREATH, 100k, DIFFERENTIAL across BREATH-AGND not one
leg`. The module-end series elements are protection resistors ("protection
resistors can be 10 kΩ and unmatched"), which are in series, not to ground. The
in-amp `REF` pin is driven by a buffer — that sets the output reference, it is
not an input bias path. `U-TVS-UMB` is a *controller*-side BOM row, and S6 itself
notes the module end has no protection fitted. So there is **no DC path from
either in-amp input to module ground** anywhere in the committed topology.

Consequence is textbook, and TI publishes an application note on exactly this
failure (SBOA503, *Importance of Input Bias Current Return Paths in
Instrumentation Amplifiers*): with no return path the inputs charge until the
common-mode range is exceeded and the input stage saturates.

Rate, unplugged: INA821 input bias current is **0.5 nA maximum** (TI product
page, via search). With the cable removed the only capacitance at the node is
package plus PCB, call it 10–20 pF:

    dV/dt = 0.5 nA / 15 pF ≈ 33 V/s

so the common-mode node crosses the input range in **a few hundred
milliseconds**. The register's "tens of volts per second … saturates in well
under a second" is right, and my derivation is *less* forgiving than theirs
because they appear to have used cable capacitance, which is not present in the
state that matters.

Output consequence: once the input stage saturates, the in-amp output slams,
the downstream breath stage follows, and the breath jack sits near a rail
(±11.4 V through the 1 kΩ). ADR 0005 states the opposite ("an instrument which
is switched off — or unplugged — presents 0 V"), and ADR 0006's power-on table
repeats it. `CLR` cannot reach breath (W13), so nothing corrects it.

### What I attacked

- **Does the return path exist through the power ground when plugged in?** Yes —
  and this is the important scoping. With the instrument connected and powered
  (or connected and switched off at the module), `AGND` reaches instrument ground
  and thence `PWR_GND` back to the module, so the common mode is defined and the
  in-amp works. **The failure is specific to "cable unplugged".** That is a
  narrower failure envelope than the register's phrasing implies — but ADR 0005
  names precisely that state and claims 0 V for it, so the finding lands.
- **Is the register's fix compatible with the CMRR argument that created the
  rule?** Yes. Two matched 1 MΩ from each input to module analog ground are
  *symmetric*, so they do not reproduce the single-leg 19 dB failure ADR 0003
  rejects. Estimating the CMRR they cost: with 10 kΩ series protection and ±1 %
  on the 1 MΩ pair, the common-mode-to-differential conversion is
  ≈ 1 % × 10 k/1 M = 1×10⁻⁴, i.e. **~80 dB**, against the 60 dB the link needs.
  Holds with 20 dB spare.
- **Does it break the AGND no-current rule (R35)?** No. Worst case 11 V/1 MΩ =
  11 µA transiently; in normal operation the instrument-to-module ground offset
  is tens of millivolts, so ~60 nA, against a 350–440 mA power return. Six orders
  of magnitude. The register is right that R35 survives in substance.
- **Is ADR 0003's rule actually the thing that blocks the fix?** Only if read as
  exclusive. "Put the pulldown differentially … not on one leg" forbids a
  single-leg shunt; it does not literally forbid *adding* a symmetric pair. The
  register's "R35 as written forbids the thing that makes the receiver work"
  conflates ADR 0003's pulldown rule with review-finding R35's AGND-bonding rule.
  Cosmetic, but the restatement should be of ADR 0003's rule, not R35's.

### Verdict and cheapest fix

**SURVIVES.** True mechanism, correct consequence, correct fix, and the
consequence is the exact inverse of what two ADRs assert. Failure envelope is
narrower than stated (unplugged only, not "switched off"), which is worth
correcting in the text but does not change the action.

Cheapest fix is the register's: **2 × 1 MΩ, one from each in-amp input to module
analog ground**, series resistance symmetrised. Two 0805 resistors. The
register's fix is the right one.

**Confidence: very high.**

---

## S4 — Shared `CLR` zeroes the mod offset. **SURVIVES.**

### Independent re-derivation

The chain of facts, each checked separately:

1. ADR 0006 sources the mod offset from **DAC channel 7**, and the whole
   power-on-safety argument is `Vout = 4 × (Vdac − Voffset) = 4 × (0 − 0) = 0 V`.
2. ADR 0006's update-rate table: **"Mod offset | written once at boot"**. So
   firmware writes 5 channels per pass (pitch + 4 mods), not 6 or 7.
3. `U-WATCHDOG` (74HC123 retriggerable monostable) "asserts DAC `CLR` when SPI
   traffic stops". Retriggerable means it **deasserts** when traffic resumes.
4. DAC8568 `CLR` behaviour (TI datasheet text via search, corroborated by a TI
   E2E thread): on activation of `CLR`, the clear code is **loaded to all input
   and DAC registers**, and the device exits clear mode on the 24th falling edge
   of the next write. So the cleared value **persists per channel until that
   channel is written**.
5. A/C grade is specified, so the clear code is **zero scale**.

Therefore after a watchdog event and recovery: ch 7 = 0 V, and
`Vout = 4 × (Vdac − 0) = 4 × Vdac`. Firmware commanding 0 V writes
`Vdac` = 2.5 V and gets **+10 V**. Commanding +5 V writes 3.75 V and gets 15 V
demanded, **clipping at ≈ +11.45 V** (OPA2197 on ±11.65 V rails per ADR 0006).

Trigger frequency: the module's own *normal* off state is "panel toggle off,
module alive, SPI silent" (ADR 0004 calls this "the state the instrument spends
most of its life in"). That silence asserts `CLR`. Every power-on of the
instrument is therefore a `CLR`-then-recover cycle. **Routine is right.**

Detectability: MISO is deleted (ADR 0004, "MISO goes"). No readback. Correct.

### What I attacked

- **Does `CLR` clear the input registers or only force the outputs?** This was
  the load-bearing step and it holds: TI's description is "loaded to all input
  and DAC registers", i.e. register contents are destroyed, not masked. If it
  had been output-forcing only, the finding would evaporate. It is not.
- **Is the "free fix" actually free?** Yes — better than the register says. I
  checked `docs/reference/latency-budget.md` directly: "each pass costs ADC 24 µs
  + key chain 16 µs + **six DAC channels 96 µs** = 136 µs, against 250 µs at
  4 kHz". Six words at 2 MHz × 32 bits = 96 µs ✓. Even if the sixth booked word
  is the breath zero rather than the mod offset, a seventh costs 16 µs, taking
  the pass to 152 µs of 250 µs — 61 % duty. Free.
- **Is "all four mod jacks pin at the positive rail" right?** Slightly
  overstated. They pin at the rail only for `Vdac` > ~2.86 V; below that they
  jump to `4 × Vdac`, which is still a large wrong positive CV. Substance
  unchanged: the "stuck CV" ADR 0004 calls unacceptable, on four channels.
- **"The same rule applies to the reference-enable and clear-code registers."**
  Not by this mechanism. `CLR` does not touch the clear-code register or the
  internal-reference-enable setting; only a power cycle or software reset does,
  and the module's own 5.25 V rail is not interrupted by a watchdog event. The
  advice ("shared state without readback must be made stateless") is sound
  policy, but it is not a second instance of this bug.
- **Could a different clear code fix it?** No — the clear code is chip-wide, so
  midscale would park pitch an octave up, which is the conflict ADR 0006
  resolved in the first place.

### Verdict and cheapest fix

**SURVIVES.** Every step checks, including the one that could have killed it.
This is the best-constructed of the seven — and it is the one only one agent
found.

Cheapest fix is the register's: **write channel 7 every pass**. One line, already
in the latency budget.

**Confidence: high.** The one residual is that I read the DAC8568 `CLR`
description through a search summary rather than the PDF; if `CLR` turned out to
be output-forcing rather than register-clearing on this specific part, the
finding would fall. Worth five minutes with the PDF when one is reachable.

---

## S5 — LM317 cannot meet its own specification. **SURVIVES BUT DOWNGRADED.**

### Independent re-derivation

`Vout = Vref·(1 + R2/R1) + I_ADJ·R2`, with R1 = 240 Ω, R2 = 768 Ω, both 1 %.
LM317L: `Vref` 1.20–1.30 V over the full operating range, `I_ADJ` ≤ 100 µA
(TI/onsemi text via search; I could not open either PDF — both domains blocked).

Worst high: `Vref` 1.30, R2 +1 % = 775.68, R1 −1 % = 237.6 → ratio 3.2646

    1.30 × 4.2646 = 5.544 V ; + 100 µA × 775.68 = 0.0776 V → **5.622 V**

Worst low: `Vref` 1.20, R2 −1 % = 760.32, R1 +1 % = 242.4 → ratio 3.1366

    1.20 × 4.1366 = **4.964 V**  (I_ADJ ignored; it can only add)

I reproduce the register's two numbers **exactly** by an independent route.
Spread 0.658 V. Nominal with I_ADJ typ: 1.25 × 4.2 + 50 µA × 768 = **5.288 V**,
not the 5.25 V the BOM states.

ADR 0004's own claim is therefore false on its own terms: it says "5.25 V nominal
keeps worst-case tolerance (±4 % on the LM317 reference) inside the DAC's 5.5 V
recommended maximum". ±4 % on the reference alone gives 5.04–5.46 V, which does
sit inside 5.5 V — so the ADR's arithmetic is right for the terms it kept and
wrong because it dropped the divider (±2 % on the ratio) and `I_ADJ` (+38 to
+78 mV). Those two omitted terms are worth 160 mV and they are exactly what flips
pass to fail. The register characterises this correctly.

DAC8568 AVDD: recommended **2.7–5.5 V** (TI product text via search). So 5.622 V
is 122 mV above *recommended operating conditions*, and — subject to my not
having opened the PDF — below the 6 V absolute maximum.

### What I attacked, and where the finding gives

**The "no nominal value fits" conclusion depends on a floor the reviewer
inserted.** The register states the window as 4.95 V to 5.50 V and concludes a
0.66 V spread cannot fit a 0.55 V window. Check the ratio form, which is the
right way to ask whether *some* nominal fits:

- part spread ratio = 5.622/4.964 = **1.1326**
- required window ratio at 4.95–5.50 = **1.1111** → does not fit ✓ (register right)
- **ADR 0004's own stated floor** is different: "staying above the **4.75 V** top
  of the used output window (ADR 0006)". Add headroom for the DAC's output buffer
  and call the floor 4.85 V. Window ratio 5.50/4.85 = **1.1340** → **it fits**,
  at a nominal of ≈ 5.13 V (5.13 × 1.0709 = 5.494 ✓; 5.13 × 0.9455 = 4.850 ✓).

So the categorical claim is sensitive to a number that is not the design's. It
fits by 0.001 in ratio, which is not a design — but "no nominal value fits" is
not what the arithmetic shows against the design's own floor.

Two further things that cut the same way:

- **The low side is not really in play.** 4.964 V is the figure with `I_ADJ`
  taken as zero. `I_ADJ` has no specified minimum but is ~50 µA typical, worth
  +38 mV, putting the realistic low at **~5.00 V**. The finding is entirely a
  ceiling problem.
- **Realistic, not stacked, worst case.** RSS of 4 % (reference) with 1 % and 1 %
  gives 4.24 %, i.e. 5.47 V including `I_ADJ` typ — right at the line rather than
  over it. The 5.622 V figure requires the reference at its full-temperature
  extreme *and* both resistors at opposite 1 % limits *and* `I_ADJ` at its
  maximum, simultaneously, in a one-off that will be measured on a bench.

And the consequence: **122 mV above recommended operating conditions on a part
whose absolute maximum is 6 V.** That is "outside characterised conditions",
not "destroyed", not "cannot work". Compare S1, where the part is 66 % over
abs-max.

One thing I checked that *doesn't* rescue the LM317: I expected to find that the
LM317's whole rationale was wrong, because DAC8568 full scale with the internal
reference is 2 × 2.5 V = 5.000 V **independent of AVDD** — so "the DAC's
full-scale output *is* its supply" is a sloppy sentence. Reading ADR 0004 in full,
the argument it actually makes is the *headroom* argument ("TI does not specify
the headroom needed to actually reach it … at a bus rail sagging to 4.75 V the
DAC saturates around 4.55–4.65 V"), which is correct. The local regulator is
justified; only its sentence is loose.

### Verdict and cheapest fix

**SURVIVES BUT DOWNGRADED — from showstopper to major.** The arithmetic is exact
and ADR 0004's tolerance claim is genuinely falsified. But the categorical
"no nominal value fits" rests on a 4.95 V floor that is the reviewer's, not the
design's, and the consequence is a recommended-maximum excursion in a fully
stacked corner rather than a functional or destructive failure.

Cheapest correct fix: **the third of the register's three options — delete the
LM317 and run AVDD from a second REF5050 buffered by half an OPA2197.** Both part
numbers are already in the BOM, ±0.05 % initial accuracy removes the entire
tolerance stack, and there is no divider and no `I_ADJ` term. Two caveats worth
writing down: it gives AVDD = 5.000 V, which is *at* the mod channels' 5.000 V
full-scale demand, so the top few millivolts of the +10 V mod excursion compress
(≈ 0.1 % of a 20 V span, irrelevant); and pitch is unaffected because ADR 0006
only uses 0.25–4.75 V.

The register's **first** option — "0.1 % divider with a smaller R2" — is the weak
one and should not be taken first: the dominant error is the ±4 % **reference**,
which no divider tolerance touches. It reduces the spread to about 5.04–5.50 V,
which fits, but with zero margin at the ceiling.

**Confidence: high** on the arithmetic (reproduced independently);
**medium-high** on the downgrade, limited by not having read the DAC8568
absolute-maximum row or the LM317L characteristics table directly.

---

## S6 — `U-TVS-UMB` 5 V array across +12 V. **OVERSTATED.**

### Independent re-derivation

Part data (Littelfuse product page and Newark/DigiKey listings via search —
Littelfuse's own PDF host is blocked):

- **SP3012-06UTG: 6 channels**, 0.5 pF, **5 V working voltage**, V_C(max) 8.4 V,
  rail-to-rail steering diodes plus a zener.
- Package: **uDFN-14**, not the SOT-23-6 the BOM states.
- Lifecycle: **obsolete / no longer manufactured** (distributor lifecycle field).

All three of the register's part claims check out. The BOM's package field is
wrong, and uDFN-14 at that body size is leadless fine-pitch — QFN-class for hand
assembly, which the scope excludes.

### What I attacked, and what breaks

**The destruction mechanism does not follow.** The register asserts "It conducts
continuously on the +12 V conductor and destroys itself on first power-up, inside
the bonded body." That requires the array to be wired across +12 V. Count the
conductors from ADR 0004's revised map:

    +12V / PWR_GND     SCLK / DIG_GND     MOSI / CS     BREATH / AGND

Eight conductors, of which **six are not the power pair**: SCLK, DIG_GND, MOSI,
CS, BREATH, AGND. A **6-channel** array referenced to PWR_GND covers those six
exactly, leaving +12 V and PWR_GND uncovered. That is both the natural
implementation and the only one that fits the channel count.

The register's evidence for the destructive reading is the BOM note "Multi-line
array beats discretes for placement. **8 conductors from outside**." Read in
context that sentence is a *rationale for choosing an array over discretes*
("there are eight conductors coming in, so use an array"), not an instruction to
clamp all eight with this one part. And there is **no schematic in the
repository** — `hardware/module/` and `hardware/controller/` are empty — so no
placement has been committed either way. The finding is an inference about an
implementation that does not yet exist, and the arithmetic of the part's own
channel count argues against that inference.

What *does* survive as a real electrical objection, and by a route the register
does not take: **BREATH is the wrong line for a 5 V array regardless of the power
pair.** Two reasons, both independent of the +12 V question:

- BREATH's normal top-of-range is **4.7 V** against a 5.0 V V_RWM, with 1.5 µA
  max leakage. That is a working margin of 300 mV on a channel that is the
  project's DC-accurate output.
- ADR 0003's whole buffer-on-+12 V decision exists so that a **sustained +12 V
  fault on BREATH** is harmless ("a +12 V conductor against a +12 V rail is at
  the rail, not above it. The clamp never conducts"). Fitting a 5 V clamp on
  BREATH re-creates exactly the destructive path ADR 0003 designed out — and W8
  shows a rollover or crossover patch lead puts +12 V on that pin. So the
  register's prescription ("a 12 V-standoff part on BREATH") is right, for this
  reason rather than the one given.

Also surviving, and independent of everything above: **the module end has no
protection at all**, which the register flags and which the BOM confirms (the
only TVS row is `category: controller`).

### Verdict and cheapest fix

**OVERSTATED.** The part-selection finding survives completely — wrong package
field, obsolete, wrong channel count for the job, wrong voltage class for BREATH,
and a package the assembly policy excludes. The **showstopper framing does not**:
"destroys itself on first power-up inside the bonded body" requires a wiring
choice nobody has made, that the part's own channel count argues against, and
that no schematic commits to. Reclassify as **major — a BOM row that must be
re-specified before any board is laid out**, not as a device that will be
destroyed.

Cheapest correct fix is close to the register's: **split by voltage class** — a
4-channel 5 V array (SOT-23-6 or SOT-363, in-production) on SCLK/MOSI/CS/DIG_GND,
a 12 V-standoff part on BREATH/AGND, and an SMAJ15A-class device on the power
pair — **and fit the same set at the module end**, which is currently unprotected.

**Confidence: high** on the part data (three distributor/vendor routes agree);
**high** on the overstatement, because the conductor count is decisive and the
schematic does not exist.

---

## S7 — Both current limits below worst case. **SURVIVES IN PART.** One sub-claim **FALSE**.

This one has four separable claims. They do not have the same verdict, and the
register's paragraph flattens a disagreement that exists between B5 and B6.

### (a) The load figures. **SURVIVES.**

Rebuilt independently from ADR 0014's clamp:

| Item | mA @ 12 V | Derivation |
|---|---|---|
| WS2815 driver quiescent | 105 | 0.84 m at 60/m = 50 LEDs × 2.1 mA |
| Lit LEDs within the 3 W clamp | 145 | 3 W/12 V = 250 mA total lighting, less quiescent |
| Buck input for 400 mA of 5 V load | 183 | 400 mA × 5 V = 2.0 W ÷ 0.91 ÷ 11 V |
| Sensor + REF5050 + OPA2197 | ~13 | ADR 0003 |
| **Total, clamp-legal steady** | **≈ 446** | |

I reached ≈ 485 mA on my first pass by charging the whole 3 W clamp to *emitted*
light rather than to light-plus-driver-idle; B5 makes the same observation and
quotes 545 mA on that reading. Either way the answer is **440–550 mA**, against
ADR 0005's 250 mA and ADR 0004's ~275 mA. The stale figures are stale by ~1.7×,
and the register's 390–650 mA envelope brackets it. **Holds.**

### (b) The polyfuse. **SURVIVES — this is the strongest part of S7.**

`F-POLY` is a 1206 PPTC, **500 mA hold, at 23 °C**. Four independent objections,
all of which I confirm:

1. **Derating.** PPTC hold derates ~×0.7 at 50 °C. ADR 0014's own thermal model
   puts the interior 10–20 K above ambient, so the part sits at 45–50 °C in
   normal play: effective hold **350–375 mA** against a 440–550 mA legal load.
   It sits permanently above hold.
2. **It cannot trip.** Trip current ≈ 2 × hold. The module-side limiter caps the
   line at 500 mA. A device that needs ~720 mA to trip, behind a 500 mA ceiling,
   **can never trip** — it has no protective function at all.
3. **It is the largest resistance in the path.** 1206 500 mA parts run
   R ≈ 0.25–0.9 Ω; at 440 mA that is **0.11–0.40 V** and **0.05–0.17 W**
   dissipated inside a sealed insulating box. More than the 1N5817 (0.3–0.4 V at
   290 mA per ADR 0004, less at this current) and more than the cable.
4. **The runaway loop is not broken.** Above hold, R rises → instrument rail
   sags → the buck is a constant-power load and draws *more* → more heating.
   ADR 0014 asserts the load switch "replaces" this device; ADR 0005 keeps it and
   calls the two "complementary rather than redundant". Both cannot be true. The
   register is right that ADR 0014 named the problem and did not delete it.

   *Correction to the register, from its own source documents:* B5 says "the load
   switch **does** break the polyfuse's *thermal* runaway term", B6 says it does
   not. Both are partly right and the register picked one. Precisely: the limiter
   bounds the current at 500 mA, so the escalation cannot run away to arbitrary
   current — but 500 mA is *above* the polyfuse's derated hold, so the PPTC still
   climbs its R–T curve until the rail collapses, and the brownout → MCU reset →
   latched-LED sequence still happens. The loop is **bounded, not broken**.

**Delete the polyfuse.** Multiple agents say so and they are right: at this
current, behind this limiter, in this thermal environment, it is a resistor with
a marketing name.

### (c) The limiter setting. **DOWNGRADED.**

The register says the 500 mA limiter is "set below a state the firmware thermal
clamp explicitly permits". The 500 mA figure comes from the **BOM note**
("Adjustable limit set ~500mA"). But **ADR 0004 already supersedes it**:

> "**The instrument figure is the least trustworthy number in this document** …
> Nothing downstream should be sized from it. **E6 measures the real draw with a
> current probe, and the load switch's current limit is set from that
> measurement.**"

So the design does not commit to 500 mA; it commits to measuring and then
choosing. The live finding is narrower and should be stated as such: **the BOM's
placeholder is stale and must not be carried into layout as the `ILIM` resistor
value** — which connects to M4, where the `ILIM` resistor (the thing that *is*
the limit) has no BOM row at all. B5 and B6 both propose **1.0–1.2 A**, i.e.
~2× the measured legal load; that is the right shape, and it is well separated
from the ~1.2 A a latched-full-white strip pair would demand, so it still
distinguishes fault from folly.

### (d) "The limiter may prevent boot." **The stated mechanism is FALSE.**

The register: "Constant-current charging ~1–2.7 mF of strip bulk at 500 mA takes
22–65 ms, **during which the buck never reaches its 8 V UVLO**."

The arithmetic is right — `t = CV/I` = 1.2 mF × 12 V / 0.5 A = 29 ms, and the
1–2.7 mF range brackets 2 × 470–1000 µF plus the buck input and `C-BULK-DISP`.
The **conclusion does not follow.** Walk the start with the limiter holding
500 mA and the loads switching on as the node rises:

| Node | Load present | Current left for the caps | dV/dt | Segment |
|---|---|---|---|---|
| 0 → 7 V | nothing (buck in UVLO, strips dark) | 500 mA | 417 V/s | 17 ms |
| 7 → 9 V | buck 2.2 W/7 V = 314 mA | 186 mA | 155 V/s | 13 ms |
| 9 → 12 V | + strip quiescent 105 mA | 81 mA | 67 V/s | 44 ms |

Available current **exceeds** the load at every point on the way up (349 mA at
9 V, 446 mA at 12 V, both under 500 mA), so the node rises **monotonically** and
the buck **does** reach and pass its UVLO, at about 17 ms. It starts — in ~75 ms
instead of a few. Even at B5's degraded-accuracy 425 mA the inequality still
holds at every segment.

B5's stronger form of the claim — "the operating point runs away downward until
the buck's UVLO drops it out … motorboating at a few tens of hertz" — is also
false for the same reason: a constant-power load only runs away when the
available current is *less* than what it demands at the prevailing voltage, and
here it never is.

What is actually true, and is a real design constraint: a **~75 ms start in
constant-current regulation** will trip the fault timer or thermal cycle of any
integrated switch sized for USB-class inrush, and dissipates roughly 0.25 J in
the pass element. That is why the pass element has to be a hot-swap controller
with an external FET and a **timer capacitor sized for ≥ 100 ms**, and why
latch-off-vs-auto-retry matters (an auto-retry part that aborts at 30 ms hiccups
forever). Same fix, correct reason. The register's reason — a deadlock in which
the buck never starts — does not happen.

### Verdict and cheapest fix

**SURVIVES IN PART.** (a) holds, (b) holds completely and is the important half,
(c) is real but narrower than stated because ADR 0004 already defers the number
to measurement, (d)'s mechanism is **false** though its prescription is right.

Cheapest correct fix, in order:
1. **Delete `F-POLY`.** It cannot trip behind the limiter, it sits above its
   derated hold in normal play, and it is the largest resistance in the 12 V
   path. Free, and it removes a part.
2. **Give `ILIM` a BOM row** and set it from the E6 measurement at ~2× legal
   draw (≈ 1.0 A on the rebuilt table), not from the BOM's stale ~500 mA.
3. **Size the hot-swap timer for a ≥ 100 ms start** into ~1.2 mF, and prefer
   latch-off over auto-retry for that reason.
4. **Reconcile ADR 0014 and ADR 0005** on whether the polyfuse exists. They
   currently contradict each other, and ADR 0014's runaway analysis is only
   correct once it does not.

**Confidence: high** on (a) and (b); **high** on the (d) falsification, which is
a straightforward monotonicity argument on the design's own numbers;
**medium-high** on (c), which is a question of which document governs.

---

## Cross-cutting observations

1. **The register is harsher and flatter than its own source documents.** S7 is
   the clearest case: B5 and B6 disagree with each other about whether the load
   switch breaks the thermal runaway, B5 explicitly concedes half of it, and
   ADR 0004 pre-empts the limiter-sizing complaint outright. None of that
   survives into the one-paragraph summary. Anyone acting on the register alone
   would over-correct.

2. **[verified] is doing less work than it looks.** S5 is marked [verified] and
   the arithmetic *is* exactly right — I reproduced both endpoints independently
   — but the load-bearing step is the **4.95 V floor**, which is not derived
   anywhere and is not the design's own number (ADR 0004 says 4.75 V). Verifying
   the arithmetic of a finding is not the same as verifying its premise.
   Conversely S6 is marked [agent] and its *part* claims all check out against
   three distributor routes; what fails there is the inference, not the data.

3. **Two of the seven are strictly about documents, not circuits.** S6 and the
   (c) half of S7 are BOM rows contradicted by ADR prose, in a project with no
   schematic yet. They are real and must be fixed, but calling them showstoppers
   alongside S1 flattens a distinction that matters for what to do first.

4. **Ranking by "what actually stops the build":**
   S1 (part is destroyed) > S4 (routine trigger, undetectable, four channels
   wrong) > S3 (designed state produces the inverse of the documented behaviour)
   > S7b (a protective device that cannot protect and costs 0.4 V) > S2 (function
   cannot work; free fix) > S5 (recommended-max excursion in a stacked corner)
   > S6 (BOM row must be re-specified).

5. **Cheap fixes that the register already has right:** S2 (invert the existing
   downstream stage — zero parts), S3 (2 × 1 MΩ), S4 (one firmware line, already
   in the latency budget), S7b (delete a part). Four of the seven cost nothing or
   less than nothing. Only S1 is a genuine design decision.

6. **What I could not reach.** No vendor PDF is openable from this sandbox —
   `ti.com`, `onsemi.com`, `st.com`, `mouser.com`, `digikey`, `octopart`,
   `alldatasheet` and every CDN returned 403 at the proxy. Everything above rests
   on vendor and distributor **page text** returned through search, which for
   headline parametrics (voltage range, package, channel count, lifecycle) is
   reliable and was cross-checked across two or three routes each. The three
   figures that would most repay opening a real PDF are: **DAC8568 absolute
   maximum AVDD** (decides whether S5 is "out of spec" or "destructive"),
   **DAC8568 `CLR` register semantics** (decides S4 outright), and the
   **LM317L characteristics table** (confirms the ±4 % reference envelope and the
   100 µA `I_ADJ` cap that S5's ceiling depends on).
