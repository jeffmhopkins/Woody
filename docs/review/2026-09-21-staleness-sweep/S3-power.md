# S3 — Power: rails, currents, and power parts

**Sweep date:** 2026-09-21
**Domain:** every rail, every current figure, every power-related part.
**Corpus audited:** `hardware/**`, `docs/decisions/**`, `config/**`,
`docs/reference/**`, `ROADMAP.md`, `README.md`, `firmware/README.md`.
`docs/review/**`, `docs/log/**` and `docs/research/**` were read for context
only and are **not** reported as stale.

**No file was edited.** This report is the only thing written.

Indexed by **disputed fact**, not by document. Line numbers are as of this
sweep.

---

## Summary table

| # | Disputed fact | Rank |
|---|---|---|
| P1 | The load-switch current limit: **0.940 A or 1.0 A** | **Showstopper** |
| P2 | Whether the instrument starts at all: 240 mA of foldback against a 360 mA start load | **Showstopper** |
| P3 | The instrument's umbilical current: **eight** live figures | **Showstopper** |
| P4 | Clamp-legal worst case: **579 mA or ~630 mA**, inside one ADR | High |
| P5 | Start duration: **62 ms / 75 ms / 17 ms** | High |
| P6 | The split-diode justification: **20 cents or 0.00018 cents** | High |
| P7 | The LM317 DAC rail: **5.25 V or 5.21 V** | High |
| P8 | What the panel LED indicates after a latch | High |
| P9 | FET ramp dissipation and energy: **4 W / 0.158 J or 6 W / 0.45 J** | High |
| P10 | Module entry bulk capacitance: **188 µF or 241 µF** | High |
| P11 | One 5 V regulator or two | High |
| P12 | `R-ILIM`: a fixed 50 mΩ, or a value selected at E6 | Medium |
| P13 | `C-DECOUPLE` qty 19 against an enumeration that sums to 21 | Medium |
| P14 | `C-BULK-RAIL`'s sizing rationale still counts the deleted LM311 | Medium |
| P15 | `C-TIMER-LOADSW` error factor: "12× to 300×" against 37× to 925× | Medium |
| P16 | `DIG_GND`: own path to the star, or not | Medium |
| P17 | Instrument bulk: **2.2 mF** against a BOM that gives 1.14–2.2 mF | Medium |
| P18 | Thermal budget: 8 W (ADR 0014) against 6.5 W (ADR 0005) | Medium |
| P19 | The 75 mV → 114 dB → 0.15 µV chain does not evaluate | Low |
| P20 | "the entire pitch error budget at 0.42 cents" | Low |
| P21 | Schottky forward drop: 400 mV or 0.305–0.380 V | Low |
| P22 | `+12 V`/`PWR_GND` pair "and the presence signal" | Low |
| P23 | The `power-entry.md` drawing routes the umbilical branch into `PWR_GND` | Low |
| P24 | "That is 1.5x on the *unfolded* limit" reads backwards | Low |

---

# SHOWSTOPPERS

## P1 — The load-switch current limit is stated as both 0.940 A and 1.0 A

This is the single most-propagated stale fact in the sweep: **four live
assertions of 1.0 A against one of 0.940 A.** `R-ILIM` is an ordering
decision and the sense threshold that produces 1.0 A is the one that was
explicitly corrected today.

**Rebuilt side — `hardware/module/power-entry.md` L110-113:**

> **1. The limit is 0.940 A, not 1.0 A.** The LT1641's sense threshold is
> **47 mV**, not 50 `[web, two reviewers]`. `R-ILIM` at 50 mΩ gives
> `47 mV / 50 mΩ = 0.940 A` `[calc]`.

and L131, L147, L151, L158 all carry 0.940 A / 940 mA forward.

**Stale side — `docs/decisions/0005-power-architecture.md` L260-262:**

> ### Set the limit at 1.0 A, and delete the polyfuse
>
> **1.0 A, latch-off, with a programmed 50–100 ms ramp.**

**`docs/decisions/0005-power-architecture.md` L273-274:**

> from below, by the clamp-legal worst case of ~630 mA plus ramp current, and
> from above by the connector. **1.0 A sits between them**

**`docs/decisions/0005-power-architecture.md` L217-218** (a cross-reference
that reproduces the stale heading verbatim):

> instrument's own faults cannot bypass it. See "Set the limit at 1.0 A, and
> delete the polyfuse" below for why keeping both was worse than keeping one.

**`hardware/bom.csv` L63, `R-ILIM` notes:**

> "THE resistor that is the limit. 1.0A target."

**`hardware/bom.csv` L18, `U-LOADSW` notes:**

> "Set the limit at 1.0A with a programmed 50-100ms ramp."

**Why this is worse than a 6 % discrepancy.** 1.0 A is not an independent
target — it is `50 mV / 50 mΩ`. It *is* the arithmetic of the 50 mV threshold
that was corrected to 47 mV today. Every remaining "1.0 A" is the deleted
number wearing a different unit. Nothing in the corpus records a decision to
round 0.940 A up to 1.0 A; ADR 0005 instead derives 1.0 A from a bracket
(`~630 mA` from below, the etherCON from above) that P4 shows is itself stale.

Consequence: `47 mV / 1.0 A = 47 mΩ`, not 50 mΩ. Whichever way this resolves,
`R-ILIM` changes value or the limit changes number. Both cannot stand.

---

## P2 — `power-entry.md` asserts a 360 mA start load and then integrates the start with no load at all

This is an internal contradiction inside the section rebuilt today, and it
undoes that section's conclusion.

**`hardware/module/power-entry.md` L115-121:**

> foldback acts during **the entire start ramp**. It regulates
> the sense drop to about **12 mV at V_out = 0**, i.e. **240 mA** `[calc]` —
> *below* the programmed charging current. **Every start therefore begins in
> current limit.**

**`hardware/module/power-entry.md` L124-131** — the correction the section was
written to make:

> **3. The start table had a charging row and no load row.** The instrument
> draws ~360 mA while it is starting; the table only counted the current
> going into the capacitors.
>
> ```
> 100 ms ramp:  charging 2.2 mF x 120 V/s = 264 mA
>               plus instrument load        360 mA
>                                         = 624 mA   against a 940 mA limit
> ```

**`hardware/module/power-entry.md` L144-153** — and then the load row is
dropped again:

> Integrating the foldback law from V_out = 0 to 12 V, with
> `k = 240 mA / 940 mA = 0.255`:
>
> ```
> t = C.V / (I.(1-k)) . ln(1/k)
>   = 2.2 mF x 12 V / (0.940 A x 0.745) x ln(3.92)
>   = 51.5 ms                bare
>   ~ 62 ms                  with the strip quiescent and both bucks loading
> ```

`t = C·V / (I·(1−k)) · ln(1/k)` is the closed form of
`∫ C dV / I_limit(V)` with **`I_load = 0`**. It is the zero-load solution.
I reproduce 51.5 ms exactly from the stated inputs (0.0264 / 0.7003 × 1.366),
which confirms no load term is present.

**Put the page's own two numbers together:** at `V_out = 0` foldback allows
**240 mA**; the page says the instrument draws **~360 mA** during the start.
240 − 360 = **−120 mA** of charging current. The output never leaves zero, the
part sits in current limit indefinitely, the 150 ms timer expires, and the
LT1641-1 latches — **which is exactly the failure the rebuild exists to fix.**

The "~ 62 ms with the strip quiescent and both bucks loading" line acknowledges
a load exists but shows no arithmetic; 62 ≈ 51.5 × 1.2 and nothing states the
1.2.

Neither model is defensible as written. Either the load during the ramp is far
below 360 mA (plausible — the buck is a constant-*power* load that draws almost
nothing at low `V_in`, and ADR 0014's blank-at-boot rule means the strips are
dark), in which case the 624 mA start table is wrong; or it is 360 mA, in which
case the circuit does not start and no timer value rescues it. **The page must
pick one and show the working.** Until it does, "the load switch now starts" is
not established.

---

## P3 — The instrument's umbilical current is stated eight different ways

Every one of these is live corpus text. Sorted ascending.

| mA | Where | Exact text |
|---|---|---|
| **~275** | `docs/decisions/0004-cv-interface-module.md` L248 | "~320 mA (45 module incl. the DAC regulator, **~275 instrument**)" |
| **290** | `docs/decisions/0004-cv-interface-module.md` L253-256 | "harmless at 50 mA and is not at **290 mA**" / "\| Series R \| Drop at **290 mA** \|" |
| **~320** | `docs/decisions/0004-cv-interface-module.md` L248 | "\| +12 V \| **~320 mA** (45 module incl. the DAC regulator, ~275 instrument) \|" *(module total, not instrument)* |
| **~350** | `docs/decisions/0003-breath-sensing-path.md` L387, `hardware/module/breath-receive-stage.md` L224, `hardware/bom.csv` L59 | "a **~350 mA** power return — about 0.2 ppm" |
| **359** | `docs/decisions/0005-power-architecture.md` L95, L158 | "\| **12 V** \| **359 mA** \| 122 mV cable + 400 mV Schottky + 60 mV \|" and "\| Typical play \| 226 mA \| 248 mA \| **359 mA** \|" |
| **~360** | `hardware/module/power-entry.md` L7, L125, L198, L252; `docs/decisions/0004-cv-interface-module.md` L549, L555 | "no published Eurorack design passes **360 mA** of someone else's load" / "\| `PWR_GND`, from the etherCON \| **~360 mA** of instrument current \|" |
| **392** | `hardware/module/power-entry.md` L65 | "HF isolation (`r_d` is 69 mΩ at **392 mA**)" |
| **~400** | `docs/decisions/0004-cv-interface-module.md` L622 | "Against an instrument drawing **~400 mA** that is 80 % of rating" |
| **410–430** | `docs/decisions/0004-cv-interface-module.md` L248 | "a review put it nearer **410–430 mA**. Measure at E6 before sizing the load switch" |
| **612** | `hardware/module/power-entry.md` L52 | "0.305 V at 245 mA → 0.380 V at **612 mA**" *(the shared-diode total, the old topology)* |

**Which agree, and which do not:**

- **359 and ~360 agree.** ADR 0005's load table is the only derived figure in
  the list, and `power-entry.md`, ADR 0004 §Grounding and ADR 0004's pitch-bend
  mechanism all round it to 360 mA. ADR 0005 L158 is the source of truth.
  I verified it: `226 mA × 5 V / (0.90 × 11.4 V) + 248 mA = 358.1 mA`. **Keep.**
- **~350 is a third rounding of the same number** and is harmless where it is
  used (a 0.2 ppm ratio in ADR 0003 / `breath-receive-stage.md` / `bom.csv`
  `R-BIAS-INAMP`), but it is a fourth spelling of one quantity.
- **~275, 290 and ~320 are pre-correction.** ADR 0005 L149-151 says so in
  terms: *"ADR 0005 originally said 250 mA and ADR 0004 **~275 mA**; five
  independent rebuilds during review came back between 390 and 650 mA."*
  **ADR 0004 was never updated.** Its rail table, its series-resistor rejection
  table and its "~50 mA of idle LED drivers" provenance paragraph all still run
  on the superseded figure while ADR 0005 states the figure is superseded.
- **290 mA is load-bearing and wrong.** ADR 0004's rejection of the series
  resistor is computed at 290 mA: "2.2 Ω | 0.64 V". At the corrected 360 mA
  that is 0.79 V; at 410–430 mA, 0.90–0.95 V. The conclusion survives, the
  arithmetic does not.
- **~400 mA is load-bearing and wrong in the unsafe direction.** ADR 0004 L622
  rules out M12 X-coded because 400 mA is "80 % of rating" against 0.5 A. At
  ADR 0005's 359 mA it is 72 %; at the review's 410–430 mA it is 82–86 %.
  The conclusion survives; the number cited does not match any current table.
- **410–430 mA is an unresolved review estimate left inline** in ADR 0004's own
  rail table, presented as a competing value rather than reconciled against
  ADR 0005's 359 mA. ADR 0004 L266-268 then says *"a review's independent
  estimate lands 100 mA above it"* — 100 mA above 320 is 420, so this figure is
  anchored to the stale 320, not to 359.
- **392 mA appears once**, in `power-entry.md`'s own new text, with no source.
  It is not a row of any table. See *Facts asserted but never derived*.
- **612 mA is correctly historical** — it is the shared-diode total under the
  deleted topology and is quoted as such.

**Rank: Showstopper.** This number sizes `R-ILIM`, the ≥1 A ferrite rating,
the etherCON contact margin, the cable drop that sets the arriving 11.4 V, and
the `PWR_GND` IR drop that ADR 0004 converts into 5.7–7.2 cents of pitch bend.
ADR 0004 carries five of the eight spellings and is the document that needs the
sweep.

---

# HIGH

## P4 — The clamp-legal worst case is 579 mA and ~630 mA in the same ADR

**`docs/decisions/0005-power-architecture.md` L160** (the load table):

> | **Clamp-legal worst** | 928 mA | 119 mA | **579 mA** | 6.5 W |

**`docs/decisions/0005-power-architecture.md` L164-165** (the paragraph
immediately under it, reusing 579):

> light costs 531 mA on the umbilical if it is spent on the strips and 579 mA if
> spent on the matrix — a **9 %** difference.

**`docs/decisions/0005-power-architecture.md` L272-274** (112 lines later):

> So the limit is not bracketed from above by that state any more — it is set
> from below, by the clamp-legal worst case of **~630 mA** plus ramp current, and
> from above by the connector.

579 mA is derivable from the table (`928 × 5 / (0.9 × 11.4) + 119 = 571 mA`,
within the table's own ~1.5 % rounding). **~630 mA is derivable from nothing in
the corpus.** It is 8.8 % above the table row it names.

This matters because ~630 mA is one of the two brackets ADR 0005 uses to
justify the 1.0 A limit in P1. With 579 mA the "1.0 A sits between them"
argument is built on a number that the same document contradicts two screens
earlier.

---

## P5 — The start takes 62 ms, 75 ms, or 17 ms

**`hardware/module/power-entry.md` L152-153, L169:**

> ```
>   = 51.5 ms                bare
>   ~ 62 ms                  with the strip quiescent and both bucks loading
> ```
> **Target: a 150 ms timer** (2.4x the 62 ms loaded start)

**`docs/decisions/0005-power-architecture.md` L281-284:**

> because available current exceeds demand at every point on the way up so the
> node rises monotonically and **the buck starts at ~17 ms**. **It boots — in
> about 75 ms of constant-current start**, which is long enough to trip a
> USB-class fault timer.

**`docs/decisions/0005-power-architecture.md` L318-319:**

> Programmable ramp rate and a programmable fault timer come with the part, which
> is what **the 75 ms start above needs**.

**`hardware/bom.csv` L18, `U-LOADSW`:**

> "A 1.0A **ramp at ~6V mean for 75ms**"

The 75 ms figure is the constant-current start at **500 mA** — ADR 0005 L279
frames the whole passage as the rebuttal to a 500 mA limit. It is not a
property of the built circuit. It is nonetheless quoted twice more in ADR 0005
and once in the BOM as *the* start time, and the BOM's FET SOA sizing is built
on it.

ADR 0005 L281-282's premise — *"available current exceeds demand at every point
on the way up so the node rises monotonically"* — is exactly what
`power-entry.md` L115-121 now denies: foldback holds the limit at 240 mA at
`V_out = 0`. The two documents assert opposite facts about the same node.

`2.4 × 62 = 149 ms`, so the 150 ms timer target is internally sound *given* 62 ms.

---

## P6 — The split diodes: "20 cents" survives in three corpus documents

**Corrected side — `hardware/module/power-entry.md` L55-62:**

> **The "20 cents of breath-correlated pitch bend" that followed is not.**
> It implies ~21 % pitch sensitivity to the +12 V rail. [...] the real path is
> 75 mV → LM317 line regulation (0.52 mV/V) → 39 µV on AVDD → OPA2197 PSRR
> (114 dB) → **0.15 µV = 0.00018 cents** `[calc, A7]`. The 20-cent figure is a
> survival from the rail-divider topology ADR 0006 already deleted.

**Stale — `hardware/bom.csv` L36, `D-REVPOL`:**

> "THREE not two: the module's analog +12V and the umbilical feed must NOT share
> a diode - instrument current then modulates its Vf by ~80mV, which is **~20
> cents of breath-correlated pitch bend** and needs no ground path at all
> (ADR 0006)"

**Stale — `docs/decisions/0004-cv-interface-module.md` L298-302:**

> the instrument's current flows through the same diode as the module's analog
> rail, so it modulates that diode's forward voltage by ~80 mV — about **20
> cents of breath-correlated pitch bend**, needing no ground path at all and
> visible by inspection of the diagram itself.

**Stale — `docs/decisions/0006-cv-channel-allocation.md` L562** (a row of the
dynamic-error table):

> | **The module's analog rail and the umbilical feed share one 1N5817**, so
> instrument current modulates its V_f by ~80 mV | **~20 cents** |

The factor between the two claims is **110,000**. ADR 0006's table then draws a
conclusion from the stale row (L566): *"Every one of these is larger than every
term in this ADR's precision budget"* — which is false for this row by five
orders of magnitude, and which is the sentence that justifies the third diode.

`power-entry.md` L63-66 already anticipates this: *"Left as it was, the next
reviewer who checks the arithmetic deletes the part."* Three documents are
still left as it was.

Also stale in the same breath: **`bom.csv` L36 and ADR 0004 L300-301 both
repeat "needs no ground path at all"**, which `power-entry.md` L69-88 now
identifies as the sentence that hid the real 7.4–18 cent ground-path effect.

---

## P7 — The LM317 DAC rail is 5.25 V in six places and 5.21 V in nine

`bom.csv` contradicts itself **across two adjacent rows**.

**`hardware/bom.csv` L37, `U-REG-DAC`, description field:**

> "Adjustable LDO set to **5.25V** for the DAC AVDD"

**`hardware/bom.csv` L38, `R-REG-SET`, the very next row:**

> "Vout = 1.25*(1+475/150) = **5.21V**."

`1.25 × (1 + 475/150) = 5.2083 V`. **5.21 V is derived and 5.25 V is not.**
5.25 V is a survival from the deleted 240 Ω / 768 Ω divider
(`1.25 × (1 + 768/240) = 5.25 V` exactly), which `R-REG-SET`'s own note says
was replaced.

**Remaining 5.25 V assertions:**

| File | Line | Text |
|---|---|---|
| `hardware/bom.csv` | 37 | "Adjustable LDO set to **5.25V** for the DAC AVDD" |
| `docs/decisions/0004-cv-interface-module.md` | 132 | "**A local 5.25 V regulator** off the protected +12 V rail" |
| `docs/decisions/0004-cv-interface-module.md` | 282 | "`└──[LM317LZ 5.25V]── DAC AVDD`" (power-tree diagram) |
| `docs/decisions/0006-cv-channel-allocation.md` | 542 | "`VREFOUT` is a 2.5 V reference inside the part, off the LM317's own **5.25 V**" |
| `docs/decisions/0006-cv-channel-allocation.md` | 688 | "The DAC runs from its own **5.25 V** regulator" |
| `ROADMAP.md` | 47 | "local **5.25V** DAC regulator and bus +5V logic rail up" |

**5.21 V assertions (correct):** `power-entry.md` L18;
ADR 0005 L125; ADR 0004 L159 and L190; ADR 0003 L371 and L578;
`bom.csv` L38, L109, L128; `digital-and-supervision.md` L40, L43;
`breath-receive-stage.md` L55; `breath-output-stage.md` L43, L100, L103;
`pitch-stage.md` L89.

ADR 0004 is self-contradictory the same way `bom.csv` is: L159 says 5.21 V,
L282's diagram says 5.25 V, thirty lines apart.

**Load-bearing:** ADR 0004 L190 computes the AHCT logic-high margin against
"the DAC's 0.7 × AVDD input threshold — **3.65 V at AVDD = 5.21 V**". At
5.25 V that threshold is 3.675 V. Small, but it is the number the level-shifter
decision rests on, and two rails cannot both be the rail.

---

## P8 — Two documents still say the panel LED reports a latch; the power page says it cannot

**Corrected side — `hardware/module/power-entry.md` L232-241:**

> `bom.csv` justifies it: *"with LT1641-1 latching off on a fault, this still
> says why the instrument went dark."* **On +12 V analog it cannot.** That
> rail is live whenever the rack is, so the LED is lit in every one of the
> latching faults above — hot-plug, LED-boot overcurrent, a current-limited
> start, a soft short. The one indication the design has for "the load switch
> has latched" indicates nothing.

**Stale — `hardware/bom.csv` L78, `LED-PANEL`** (the exact sentence quoted
above, still in place):

> "With LT1641-1 latching off on a fault, this still says why the instrument
> went dark"

**Stale — `hardware/bom.csv` L103, `D-REVSHUNT`:**

> "Cathode to the +12V pin: reversed, it conducts hard, the module's LT1641-1
> sees a short and LATCHES OFF, and **the panel LED says so**. The load switch
> becomes the fuse"

**Stale — `docs/decisions/0004-cv-interface-module.md` L738-740:**

> Reversed, it conducts hard, the module's LT1641-1 sees a short, **latches
> off**, and **the panel LED goes out**. The load switch becomes the fuse,
> which is what it was for.

The LED is on the module's +12 V **analog** rail (`bom.csv` L79, `R-LED-PANEL`
"~4mA from the module's +12V analog rail"), upstream of `D2`/the load switch
entirely. A latched load switch does not touch it. `D-REVSHUNT`'s entire
diagnostic story — "the reversed lead is diagnosable because the LED goes out"
— is false as the circuit now stands, in both the BOM and ADR 0004.

**Consistent and correct:** `bom.csv` L79 (`R-LED-PANEL` 2k2, +12 V analog,
"Was 820R from bus +5V"), `digital-and-supervision.md` L75-79 and L145
("The panel LED becomes an ordinary power indicator"), `power-entry.md`
L220-248. `R-LED` 820 Ω and `R-OE-PU` appear in **no** BOM row anywhere —
verified by grep; both are correctly gone.

---

## P9 — FET ramp dissipation and energy: 4 W / 0.158 J against 6 W / 0.45 J

**`hardware/module/power-entry.md` L190-193:**

> With foldback working, peak fault dissipation is **~4 W at V_out ~ 4 V**,
> not the 12 W the old page assumed — the feature holds dissipation roughly
> flat instead of letting it peak. Ramp energy is `1/2 CV^2` = **0.158 J**
> regardless of ramp time

**`hardware/bom.csv` L18, `U-LOADSW`:**

> "A 1.0A ramp at ~6V mean for 75ms is **~6W and 0.45J**; SOT-23 transient
> thermal impedance at that pulse width gives hundreds of degrees of junction
> rise. Choose a DPAK or SO-8 part against its SINGLE-PULSE SOA CURVE, and
> program the LT1641's FOLDBACK, **which exists to hold FET dissipation roughly
> constant in current limit**."

`1.0 A × 6 V × 75 ms = 0.45 J` — internally consistent, but every input is a
stale one (P1's 1.0 A, P5's 75 ms). `½ × 2.2 mF × 144 V² = 0.158 J` ✓.
**2.8× apart**, and it is the number the DPAK/SO-8 SOA selection is made
against.

The BOM row also still describes foldback as a **fault-mode** feature ("in
current limit"), which is the description `power-entry.md` L115-122 corrects:
foldback now acts during *the entire start ramp*, and the start is
*always* in current limit. The BOM's framing is the old, backwards one.

Note `power-entry.md` L194-196 then does its thermal check at 12 W
("a DPAK is 0.6 C/W at 50 ms, so 12 W is a 7 C rise"), four lines after saying
peak dissipation is ~4 W. Defensible as a bounding check, but it should say so.

---

## P10 — Module entry bulk capacitance: 188 µF or 241 µF

**`hardware/module/power-entry.md` L15-41** (the schematic) draws **four
identical 47 µF caps**:

> ```
>   +12V ├───┬──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V
>        │   └──[D2 1N5817]──[FB2]──[C2 47µF]──┬──────── PWR_GND (star)
>   -12V ├───[D3 1N5817]──[FB3]──[C3 47µF]────────── MODULE ANALOG −12V
>    +5V ├───[FB4]──[C4 47µF]──────────────────────── 74AHCT125 only
> ```

and **L273** states the total:

> - **Entry bulk is 4 × 47 µF**, which is 2–5× the surveyed norm of 10–22 µF.

4 × 47 = **188 µF**.

**`hardware/bom.csv` L76, `C-BULK-RAIL`, qty 4:**

> `"100uF (+12V) / 47uF (-12V, +5V) 25V electrolytic"` — "**NOT 47uF on every
> rail.** [...] at 47uF each it collapses 2.2x faster and every rack power-down
> leaves the op-amps with V+ near 0 and V- at -6 to -8V for ~30ms, pulling all
> six jacks toward the surviving negative rail. **100uF on +12V balances the
> decay.**"

100 + 47 + 47 + 47 = **241 µF**.

**And the BOM is ambiguous about which 241 µF.** It names three rails
(`+12V`, `-12V`, `+5V`) for four parts. There are *two* +12 V branches — analog
and umbilical. If both get 100 µF the total is **294 µF**. Three readings, no
tie-breaker.

The disagreement is not cosmetic: the BOM's asymmetric split exists to stop a
rack power-down pulling all six CV jacks to the negative rail for ~30 ms. The
schematic drawn today silently reverts it to symmetric 47 µF, i.e. reinstates
the failure the BOM row was written to prevent. `power-entry.md` L273 then
uses the reverted figure as its "2–5× the surveyed norm" open item.

---

## P11 — ADR 0014 sizes the instrument around one shared 5 V regulator; everything else says two

**Two-regulator side — `docs/decisions/0005-power-architecture.md` L206-211:**

> **Two bucks, not one.** ADR 0013 asks for a regulator per board so the display
> board's WiFi bursts are absorbed locally [...] and the load table above gives
> the second reason: 928 mA of clamp-legal worst case does not fit behind one
> 1 A part.

`docs/decisions/0013-two-mcu-split.md` L245: *"**Two** R-78E5.0 regulator
modules — one per dev board"*. `hardware/bom.csv` L10 `U-BUCK` **qty 2**.
`hardware/controller/carrier.md` L99-104 draws `R-78E5.0 A` and `R-78E5.0 B`.

**Stale — `docs/decisions/0014-lighting.md` L152-155:**

> **The instrument's own regulator, which is a 1 A part.** The matrix hangs on
> the R-78E5.0-1.0 **alongside both dev boards**, and at full field it asks for
> 960 mA on its own.

**Stale — `docs/decisions/0014-lighting.md` L367-368:**

> shares the 1 A R-78E5.0 **with both dev boards**, which take roughly
> 330–400 mA between them, so a full-field matrix would ask for about
> **1.36 A from a 1 A part**.

The 1.36 A figure is one of the three pillars of the ~3 W lighting clamp. Under
the two-buck split the display board is on buck B, so buck A carries the matrix
plus the real-time board only — a different and smaller number, which ADR 0014
never computes. The clamp may well survive (the thermal argument is the binding
one by ADR 0014's own account), but its electrical pillar is computed against a
topology deleted in ADR 0005 and ADR 0013.

**Also singular, minor:** `README.md` L79 — *"**The instrument's own 5 V
regulator**, which is a 1 A part at the end of a 2 m cable"*. Same stale
framing, but it is scope text rather than a derivation.

**Already flagged in-corpus:** `carrier.md` L150-156 notes that ADR 0005's load
table has one 5 V column and the two-regulator decision needs it split per
buck — *"That split is not written anywhere and it is what sizes both parts."*
That gap is real and it is what makes P11 unresolvable from the documents.

---

# MEDIUM

## P12 — `R-ILIM` is a fixed 50 mΩ in the schematic and an open bench value in the BOM

**`hardware/module/power-entry.md` L29 and L112-113:**

> `│  [R-ILIM 50mΩ]        │`
>
> `R-ILIM` at 50 mΩ gives `47 mV / 50 mΩ = 0.940 A` `[calc]`.

**`hardware/bom.csv` L63**, part field `"Sense resistor, value from E6"`,
status `open`:

> "So E6 measures the TRIP as well as the load, with a current probe, and the
> value is **selected on the bench** like `R-REG-SET`"

These are two different design methods. If 50 mΩ is fixed, 0.940 A is the
consequence and E6 only verifies it. If the value is selected at E6 to hit a
target, the target is the spec and 0.940 A is not a fact about the design.
`power-entry.md` presents 0.940 A as settled arithmetic; the BOM presents the
limit as undetermined. The BOM's own target in that row is still 1.0 A (P1).

## P13 — `C-DECOUPLE` is qty 19 against an enumeration that sums to 21

**`hardware/bom.csv` L42**, qty field **19**:

> "One per supply pin, close to the pin. 6 x OPA2197 on +/-12V = 12, INA828 = 2,
> **LM311 on +/-12V = 2**, DAC8568 AVDD+DVDD = 2, 74AHCT125, LT1641 VCC,
> LM317 in. Was 22 with the 74HC123; the watchdog is deleted | 2026-09-21: was
> 21. The two caps counted for the LM311 are removed - that part was DELETED and
> its footprint is no longer drawn"

The enumeration still contains `LM311 on +/-12V = 2`:
12 + 2 + **2** + 2 + 1 + 1 + 1 = **21**, against a stated qty of **19**. The
note says the LM311's two are removed and then leaves them in the list that is
supposed to justify the quantity. A board stuffer working from the enumeration
fits 21; the quantity column buys 19.

The qty **19 is correct** and agrees with
`hardware/module/digital-and-supervision.md` L63-64 — *"**`C-DECOUPLE` drops
from 21 to 19.**"* Only the enumeration is stale.

## P14 — `C-BULK-RAIL`'s sizing rationale still counts the deleted LM311

**`hardware/bom.csv` L76:**

> "The +12V branch carries the LM317's divider, the DAC and **the comparator**,
> about **22mA** against -12V's 10mA - so at 47uF each it collapses 2.2x faster"

The comparator is the LM311, deleted (`digital-and-supervision.md` L51, L60-64;
`bom.csv` L34, L42). The 22 mA figure that produces the 2.2× decay ratio — and
therefore the 100 µF-on-+12 V decision at the heart of P10 — still includes a
part that is not in the design. Nothing in the corpus recomputes it without the
LM311.

Note also that this rationale is silent on the **panel LED's 4 mA**, which moved
*onto* the +12 V analog rail today (`bom.csv` L79). The 22 mA figure is stale in
both directions.

## P15 — "`10nF` was wrong by 12× to 300×" does not follow from the stated equation

**`hardware/module/power-entry.md` L177-179:**

> The specified **10 nF is wrong under every reading** — **12x to 300x** too
> small, giving a 0.16–4 ms timer

**`hardware/bom.csv` L115, `C-TIMER-LOADSW`** (same claim):

> "10nF was wrong by **12x to 300x** and gave a **0.16-4ms** fault timer"

From the page's own equation `C = I_TIMER × t / 1.233 V` and its own table
(365 nF at 3 µA, 9.25 µF at 76 µA — both of which I reproduce exactly):

- 365 nF / 10 nF = **36.5×**
- 9.25 µF / 10 nF = **925×**

The timer durations are right (10 nF × 1.233 / 3 µA = **4.11 ms**;
10 nF × 1.233 / 76 µA = **0.162 ms**, hence "0.16–4 ms" ✓), and the *ratios*
follow from them: 150 / 4.11 = 36.5, 150 / 0.162 = 925. The third reviewer's
2–100 µA bracket gives 24×–1217×, also not 12–300.

**"12× to 300×" is derivable from no combination of the numbers on the page**,
and it understates the error by 3× at the bottom and by 3× at the top. Both
documents carry it identically, so a reader cross-checking them finds
agreement.

## P16 — `DIG_GND`: its own path to the star, or deliberately not

**`hardware/module/power-entry.md` L253-257:**

> **`DIG_GND` is *not* given its own path to the star**, which **an earlier
> revision of ADR 0004** asked for: a 2 MHz SPI return wants the pour directly
> under its trace, and routing it to a distant star point is the classic
> split-plane mistake.

**`docs/decisions/0004-cv-interface-module.md` L568** — the current revision:

> - **`DIG_GND` likewise** — its own path to the star.

`power-entry.md` attributes the requirement to a revision of ADR 0004 that has
been superseded. It has not been. ADR 0004 still asks for exactly the thing
`power-entry.md` says it no longer asks for, and `power-entry.md` L260-261 then
sends the reader to ADR 0004 for "full reasoning".

This is a layout constraint that is free before fab and a respin afterwards
(ADR 0004 L535-537 says so itself). It cannot be left with two answers.

## P17 — "2.2 mF" instrument bulk is the top of a range the BOM gives as 1.14–2.2 mF

`hardware/module/power-entry.md` uses **2.2 mF** five times — L129, L141, L151,
L158, and implicitly in the 0.158 J ramp energy — as a settled quantity. Every
load-switch number on the page scales with it.

The BOM does not contain 2.2 mF. It contains:

- `hardware/bom.csv` L73 `C-BUCK-IN`: "100uF 25V electrolytic", **qty 2** → 200 µF
- `hardware/bom.csv` L46 `C-STRIP-BULK`: "**470-1000uF** electrolytic, 16V", **qty 2** → 940–2000 µF
- `hardware/bom.csv` L31 `C-BULK-DISP`: "TBD", qty 1, status `open` → unknown

Sum: **1.14 mF to 2.2 mF, plus an open row.** 2.2 mF is the worst case, which
is the right choice for a current-limit calculation — but nothing says so, and
`carrier.md` L884 separately flags `L-BUCK-IN` qty 1 against `C-BUCK-IN` qty 2
as "two rows describing different topologies", so even the 200 µF term is not
settled.

At the bottom of the range (1.14 mF) the bare start integral gives 26.7 ms, not
51.5 ms — which is, to within rounding, **the 26 ms the rebuilt page explicitly
rejects** at L155: *"The timer must exceed that, not the 26 ms the old page
compared against."* The old page may simply have used the other end of the same
range.

## P18 — ADR 0014's thermal budget is 8 W; ADR 0005's clamp-legal worst is 6.5 W

**`docs/decisions/0014-lighting.md` L139-141:**

> The existing electronics dissipate roughly **5 W** for an interior rise of
> 10–20 K, so call it **~3 K per watt**.

plus the **3 W** lighting clamp (L156-160) = **8 W**, which ADR 0014 L160 costs
at *"roughly 9 K of interior rise"*.

**`docs/decisions/0005-power-architecture.md` L157-160** (Body heat column):

> | Quiescent | ... | **2.4 W** |
> | Typical play | ... | **4.1 W** |
> | Typical + live config over WiFi | ... | **4.7 W** |
> | **Clamp-legal worst** | ... | **6.5 W** |

ADR 0005's clamp-legal worst — the state where the full 3 W lighting budget is
being spent — is **6.5 W**, not 8 W. I verified 6.5 W from the table
(579 mA × 11.4 V = 6.6 W). ADR 0014's "5 W of existing electronics" is really
the 4.1–4.7 W rows, which *already include* ~1.5 W of realistic lighting, so
adding 3 W on top double-counts. The 3 K/W figure is explicitly a bounding
estimate validated at M8, so nothing breaks — but the two documents give
different answers for the same state and neither references the other.

---

# LOW

## P19 — The 75 mV → 114 dB → 0.15 µV chain does not evaluate

**`hardware/module/power-entry.md` L57-60:**

> the real path is 75 mV → LM317 line regulation (0.52 mV/V) → 39 µV on AVDD
> → OPA2197 PSRR (114 dB) → **0.15 µV = 0.00018 cents** `[calc, A7]`.

- `75 mV × 0.52 mV/V = 39 µV` ✓
- `0.15 µV × 1200 cents/V = 0.00018 cents` ✓
- `39 µV / 10^(114/20) = 39 µV / 501187 = **78 pV**`, not 0.15 µV.

0.15 µV corresponds to **48 dB**, not 114 dB. The chain is off by a factor of
~2000 in the *conservative* direction, so the conclusion ("negligible") is not
merely safe but stronger than stated. Fix the arithmetic or drop the middle
term; as written the calculation does not reproduce and invites exactly the
re-derivation that P6 warns about.

## P20 — "pitch-stage.md puts the entire pitch error budget at 0.42 cents"

**`hardware/module/power-entry.md` L85:**

> `pitch-stage.md` puts the entire pitch error budget at 0.42 cents.

**`hardware/module/pitch-stage.md` L285-289** gives 0.42 cents as *one line of
a table*:

> | **DAC internal reference** | **0.42 cents** | **The largest term, and untrimmable** |
> | LT5400 ratio tracking | 0.027 cents | |
> | `TRIM-GAIN` tempco | **0.068 cents** | ... |

and **L300-304** gives a second, larger budget: LT5400 ~0.1, DAC reference
~0.5, OPA2197 offset <0.1, DAC INL ~0.4 cents. "The entire budget" is nearer
1 cent than 0.42. The rhetorical point in `power-entry.md`'s grounding callout
survives either way; the citation does not.

**Related — `hardware/module/pitch-stage.md` L306-308:**

> Nothing here approaches the **20-odd cents** of the dynamic, LED-correlated
> terms that ADR 0006 fixes **in the power tree** and the ground plan.

"In the power tree" is the split-diode fix, now 0.00018 cents (P6). The
LED-correlated 22 cents p-p term is unaffected and still valid, so this sentence
is half-true; it should name the ground plan and the offset-reference divider
only.

## P21 — Schottky forward drop: 400 mV or 0.305–0.380 V

**`docs/decisions/0005-power-architecture.md` L95:**

> | **12 V** | 359 mA | 122 mV cable + **400 mV Schottky** + 60 mV | **~11.4 V** | **5%** |

**`hardware/module/power-entry.md` L52:**

> 0.305 V at 245 mA → 0.380 V at 612 mA

**`hardware/bom.csv` L36, `D-REVPOL`:** "~0.3-0.4V drop".
**`docs/decisions/0004-cv-interface-module.md` L261:** "A 1N5817 drops roughly
0.3–0.4 V at this current".

At the table's own 359 mA the interpolated drop is ~0.33 V, not 0.400 V.
`12 − 0.122 − 0.330 − 0.060 = 11.49 V`, and the "5 %" error becomes 4.3 %.
The 11.4 V figure is used as the conversion voltage throughout ADR 0005's load
table and in `carrier.md` L134, so it is worth nailing down — but it is
conservative as written.

## P22 — The `+12 V` / `PWR_GND` pair is still said to carry "the presence signal"

**`docs/decisions/0004-cv-interface-module.md` L82-86:**

> ```
> +12V      / PWR_GND     power, and the presence signal
> SCLK      / DIG_GND     SPI to the DAC, ~1 MHz
> MOSI      / CS
> ```

Three things stale in five lines: the presence detect is deleted
(`digital-and-supervision.md` L129-147; `bom.csv` L34); SPI is 2 MHz, not
~1 MHz (`ROADMAP.md` L52, `latency-budget.md` L125, ADR 0004's own L71); and
the pairing contradicts the same ADR's revised map 670 lines later at L754-757
(`SCLK`/`MOSI` on (4,5), `CS`/`DIG_GND` on (7,8)). Only the first is in my
domain, and the power pair itself (3,6) is consistent everywhere.

## P23 — The drawing routes the umbilical +12 V branch into `PWR_GND`

**`hardware/module/power-entry.md` L22:**

> `       │   └──[D2 1N5817]──[FB2]──[C2 47µF]──┬──────── PWR_GND (star)`

As drawn, the umbilical's protected +12 V branch terminates at the ground star.
The load-switch block below it is connected only by the box-drawing `┬`/`│`
run, which also carries the `PWR_GND` label. Read literally this is a short.
It is obviously an ASCII-art artefact, but the +12 V umbilical branch is the
node the whole page is about and its feed into `R-ILIM` should be explicit.

## P24 — "That is 1.5x on the *unfolded* limit" reads backwards

**`hardware/module/power-entry.md` L131-134:**

> ```
>                                         = 624 mA   against a 940 mA limit
> ```
>
> That is **1.5x** on the *unfolded* limit

`940 / 624 = 1.51` — the *limit* is 1.5× the demand, i.e. 1.5× of margin.
`624 / 940 = 0.66`. In a section whose thesis is that the start is over-limit,
"1.5x on the limit" reads as an exceedance. One word ("1.5× of margin against")
fixes it.

---

# Facts asserted but never derived

Ranked by how much rests on them.

| # | Assertion | Where | What is missing |
|---|---|---|---|
| U1 | **Foldback regulates the sense drop to "about 12 mV at `V_out` = 0", i.e. 240 mA** | `power-entry.md` L118-120 | Tagged `[calc]` but there is no input to calculate from. No datasheet cite, no `[web]` mark, no foldback ratio quoted. **`k = 0.255` — and therefore the 51.5 ms start, the 62 ms figure, the 150 ms timer and the whole "every start begins in current limit" thesis — rests entirely on this bare number.** The page's own box says `analog.com` was unreachable through three review waves. |
| U2 | **The instrument draws ~360 mA while it is starting** | `power-entry.md` L124-125 | No derivation. ADR 0005's load table has no start-up row; its nearest state is *Quiescent — booted, radio off, **LEDs blanked*** at 212 mA, and ADR 0014's blank-at-boot rule (L205-209) means the strips *are* blanked during boot. 360 mA is the *typical play* row applied to a state that is not typical play. This is the input to P2. |
| U3 | **`R-ILIM` = 50 mΩ** | `power-entry.md` L29, L113 | The BOM has no value (`"value from E6"`, status `open`). 50 mΩ appears only here, and only because `47 mV / 50 mΩ` lands on a round-looking 0.940 A. See P12. |
| U4 | **`I_GATE` ≈ 10 µA** | `power-entry.md` L140, L180; `bom.csv` L116 | Used twice — for the 10 kV/s bare-`C_iss` ramp that yields the alarming "22 A", and for the ~83 nF `C-GATE` candidate. Same unreachable datasheet as `I_TIMER`, but unlike `I_TIMER` it is *not* bracketed or flagged; it is used as if known. |
| U5 | **FET `C_iss` ≈ 1 nF** | `power-entry.md` L139 | No FET part number exists anywhere in the corpus — `bom.csv` L18 says only "DPAK/SO-8 N-FET". `C_iss` for DPAK N-FETs spans ~300 pF to ~3 nF, i.e. the 10 kV/s is a 3× band, not a number. |
| U6 | **Peak fault dissipation ~4 W at `V_out` ~ 4 V** | `power-entry.md` L190-191 | No working. It is the number the DPAK/SO-8 SOA selection is made against, and it disagrees with the BOM's 6 W (P9). |
| U7 | **Spirito / linear-mode derating "can put a trench part at 2–3 W" at `V_DS` = 12 V** | `power-entry.md` L199-201 | No part, no curve, no `[web]` mark. Stated as the criterion that actually sizes the FET. |
| U8 | **Instrument bulk = 2.2 mF** | `power-entry.md` ×5 | Top of a 1.14–2.2 mF BOM range with an open row on top. See P17. |
| U9 | **~630 mA clamp-legal worst** | ADR 0005 L273 | Not in the load table, not derivable from it (571–579 mA), contradicted by the same ADR. See P4. |
| U10 | **45 mA of module current** | ADR 0004 L248 | Never itemised. The module's own loads are all in `bom.csv` (6× OPA2197, INA828, DAC8568, LM317 at ~13 mA, LT1641, panel LED at ~4 mA) and are summed nowhere. The figure also predates the panel LED moving onto this rail. |
| U11 | **392 mA** | `power-entry.md` L65 | Appears once, to compute `r_d` = 69 mΩ. Not a row of any table and not equal to any other current in the corpus. |
| U12 | **LM317 line regulation 0.52 mV/V; OPA2197 PSRR 114 dB** | `power-entry.md` L58-59 | Both `[calc, A7]` with no datasheet reachable, and the chain they form does not evaluate (P19). |
| U13 | **The 47 mV sense threshold itself** | `power-entry.md` L111-112 | `[web, two reviewers]`, explicitly unverified — the page's own gate box says to read it off the datasheet before ordering. Correctly flagged, listed here because **P1's entire case rests on it** and the corpus has not yet acted on it. |
| U14 | **Display board draw "~150–250 mA ESTIMATED"** | `carrier.md` L147 | Flagged as estimated by the page itself; noted because it is the only per-buck split anywhere and `carrier.md` L150-156 says the split "is not written anywhere and it is what sizes both parts". |
| U15 | **ADR 0014's ×0.49 umbilical conversion factor** | ADR 0014 L351 | ADR 0005 L173-174 says it "survives by coincidence: two ~6 % errors in opposite directions". I confirm `5 / (0.90 × 11.4) = 0.487`, so it is now correct by construction, not by coincidence — but ADR 0014 never states its derivation and ADR 0005's parenthetical is itself now stale. |

---

# Facts I verified consistent

These were chased across every corpus document and **agree**. Recorded so the
next sweep does not re-audit them.

1. **The bus +5 V rail still exists, and every document agrees.** Seven
   independent statements, no dissent:
   `power-entry.md` L41 (`+5V ├───[FB4]──[C4 47µF]──── 74AHCT125 only`) and L91;
   ADR 0004 L134, L189, L250, L292;
   ADR 0005 L120-123 and L142-145 (*"the level shifter's rail is a
   **requirement, not an option**. No jumper, no unpopulated fallback
   footprint"*);
   `bom.csv` L35 `J-PWR-EURO` (*"Carries the +5V rail the module REQUIRES"*)
   and L34 `U-LVL-MOD` (*"Runs from bus +5V"*);
   `digital-and-supervision.md` L31; `ROADMAP.md` L47 (*"bus +5V logic rail
   up"*); `README.md` L69.
   The three reviewers' objection is recorded **as an open item, correctly
   scoped**, at `digital-and-supervision.md` L104-113: *"**Not changed here,
   because it is a rail change and a connector change, not a drawing
   correction.**"* That is the right shape and no document acts as if the rail
   were dropped. The 16-pin header is likewise consistent everywhere
   (`power-entry.md` L13, ADR 0004 L144/L217/L576, `bom.csv` L35); the 10-pin
   alternative appears only inside the open item.
2. **The instrument-end polyfuse is deleted, consistently.** ADR 0005 L213-218
   and L287-299; ADR 0013 L247; ADR 0014 L200-203 (*"**"Replaces" now means
   it** — this ADR added the load switch and left the polyfuse in the BOM
   [...] The polyfuse is deleted (ADR 0005)"*); `carrier.md` L116; no polyfuse
   row in `bom.csv`. `F-CHAIN` (`bom.csv` L96, `carrier.md` L478/L757) is a
   100 mA fuse on the *3V3 chain conductor* — a different part, not a survival.
3. **`SW-PWR-INST` is deleted and the module toggle is the only switch.**
   ADR 0005 L221-246; ADR 0004 L520-527; `carrier.md` L116; `bom.csv` L17
   `SW-POWER` (*"Signal-level only now. The only power switch in the system;
   SW-PWR-INST is deleted (ADR 0005)"*). No contradiction anywhere.
4. **`R-LED` 820 Ω and `R-OE-PU` are gone.** Neither has a BOM row; both are
   referenced only in the past tense, in `power-entry.md` L220-228,
   `digital-and-supervision.md` L75-79 and `bom.csv` L79. Confirmed by grep
   across the whole corpus.
5. **`OE` is tied low / permanently enabled**, in all three places that mention
   it: `bom.csv` L34, `digital-and-supervision.md` L34 and L75-79,
   `power-entry.md` L225. No survival of the presence-gated version.
6. **`C-DECOUPLE` qty 19 is correct** and matches
   `digital-and-supervision.md` L63-64 exactly. Only the enumeration text is
   stale (P13).
7. **The LT1641-**1** suffix (latch-off, not auto-retry)** is consistent:
   ADR 0005 L313-316; `power-entry.md` L207-213; `bom.csv` L18;
   `carrier.md` L113; ADR 0004 L525, L739; `D-REVSHUNT` L103.
8. **TPS2553 is dead everywhere.** It survives only as a rejected candidate in
   ADR 0005 L305-309 and `bom.csv` L18 ("REPLACES TPS2553"). No document
   specifies it.
9. **ADR 0005's load table is internally self-consistent** to within its own
   rounding, on both stated conventions (convert at 11.4 V, buck at 90 %).
   I reproduce every row: quiescent 210.7 vs 212; typical play 358.1 vs 359;
   WiFi 411.7 vs 414; clamp-legal worst 571 vs 579 (the loosest, 1.4 %);
   clamp-failed 1521.5 vs 1522. The "9 % difference" (579 vs 531) and the
   "factor of three" (928 vs 328) both check out.
10. **`carrier.md` §1 introduces no new current figures.** Its two numbers —
    226 mA typical-play 5 V draw (L134) and 928 mA clamp-legal worst on 5 V
    (L146) — are both cited `[repo] 0005` and both match ADR 0005 L157-160
    exactly. `carrier.md` is the *cleanest* power document in the corpus.
11. **The three-diode split itself (`D-REVPOL` qty 3)** is consistent:
    `bom.csv` L36 qty 3; `power-entry.md` L15-39 draws D1/D2/D3;
    ADR 0004 L280-292; ADR 0006 L569-572. Only the *justification* is stale
    (P6), never the part count.
12. **Ferrite beads ≥1 A, four of them, one per branch.** `bom.csv` L40
    `FB-IN` qty 4 ("+12V analog, +12V umbilical, -12V, +5V");
    `power-entry.md` L41 and L93-99; ADR 0004 L330-333; ADR 0006 L702. The
    "a saturated bead is a wire" reasoning and the ~300 mA / 0805 warning match
    word for word across all four.
13. **`L-BUCK-IN` is a real inductor, not a bead**, everywhere: `bom.csv` L47;
    ADR 0004 L328-330; `carrier.md` L99, L111-114. The damping open item is
    correctly split — `power-entry.md` L265-268 leaves it open for the module
    end, `carrier.md` L123-140 closes it for the instrument end and says so.
14. **`C-BUCK-IN` must be electrolytic, not ceramic.** `bom.csv` L73;
    `carrier.md` L139-142 and L775. Consistent, and the reason is given on both
    sides.
15. **The DAC's full scale is set by the internal reference, not AVDD.**
    ADR 0005 L129-141; `ROADMAP.md` L189; ADR 0006 L542-548; `power-entry.md`
    L56-57. ADR 0004 L148-153 still carries the *old* claim ("The DAC's
    full-scale output is its supply") but ADR 0005 L129-134 explicitly quotes
    and corrects it, so it is flagged rather than stale. **The rail voltage it
    is set to is still disputed — see P7.**
16. **The panel LED's new circuit** — 2.2 kΩ from +12 V analog, ~4 mA — is
    consistent in `bom.csv` L78-79, `power-entry.md` L220-231 and
    `digital-and-supervision.md` L78-79. `(12 − 2.0) / 2200 = 4.5 mA` ✓.
    Only the *purpose* is disputed (P8).
17. **Both new BOM rows exist and cross-reference correctly.**
    `C-TIMER-LOADSW` (`bom.csv` L115) and `C-GATE-LOADSW` (L116) are both
    present, both `open`, both `"TBD - see power-entry.md"`, both carry the
    design equation and both candidate values, and both say to read the
    datasheet before ordering. `power-entry.md` L161-186 matches. The
    `C-GATE` row correctly records that the part did not previously exist.
    The package fields agree that 0805 C0G is wrong. *(Though note: neither row
    is buildable as a 1206 either if `I_TIMER` turns out to be 76 µA —
    9.25 µF is a through-hole or tantalum part.)*
18. **The etherCON contact rating (~1.5 A) and the latched-full-white
    consequence** agree: ADR 0004 L614 (`| Current per contact | ~1.5 A |`)
    against ADR 0005 L268-270 and the 1522 mA table row.
19. **`AGND` carries no power current** — asserted identically in
    `power-entry.md` L257-258, ADR 0004 L552 and L571-574, ADR 0003 L387,
    `carrier.md` L263-266, `bom.csv` L59. No dissent anywhere.
20. **Cable drop arithmetic.** ADR 0005 L93-96: 2 m of 24 AWG, round trip
    ~0.34 Ω ✓ (0.0842 Ω/m × 4 m = 0.337 Ω); 359 mA × 0.34 Ω = 122 mV ✓;
    862 mA × 0.34 Ω = 293 mV ✓; 862 mA = 4.1 W / 4.76 V ✓.
21. **The 3 W lighting clamp's own internal arithmetic.** ADR 0014: 15 mA/LED ×
    64 = 960 mA ✓; ×0.49 → 470 mA ✓; realistic use 0.13 A at 12 V ≈ 1.5 W ✓
    against the thermal table's "~1.5 W". Only its *regulator* pillar is stale
    (P11) and its *total* disagrees with ADR 0005 (P18).

---

# What to fix first

1. **P1** — settle the limit. It is one number (0.940 A or 1.0 A), it decides
   `R-ILIM`'s value, and it is the one item on this list that is an *order*.
2. **P2** — the rebuilt section does not yet show that the circuit starts.
   Reconcile the 240 mA foldback floor against the start load, or state the
   start load correctly and re-integrate.
3. **P3** — pick 359 mA and sweep ADR 0004. Five of the eight spellings are in
   that one document and two of them (290 mA, ~400 mA) carry conclusions.
4. **P6, P7, P8** — three find-and-replace sweeps across known line numbers,
   no new engineering required.
5. **U1, U4, U13** — one datasheet read closes the foldback ratio, `I_GATE`,
   `I_TIMER` and the sense threshold together, and with them P1, P2, P5, P9,
   P15 and the two BLOCKING BOM rows.

**Adjacent, outside this domain, noted in passing:** `carrier.md` L612-613
draws `R-LED-SER` at **220R** while `bom.csv` L113 specifies **330R 1%**
(qty 4); and `digital-and-supervision.md`'s *Still open* list (L206-237) still
asks for "a corrected `R-PRESENCE` row" and "a power-on reset RC on the '123's
own `CLR`" for two parts that are deleted. Both belong to another sweep's fact
domain.
