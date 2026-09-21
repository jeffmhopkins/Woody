# TI — datasheet wave R7 findings report

Agent: **TI**.  Date: 2026-09-21.  Two documents assigned, **both fetched, verified
and banked**. No repo file was edited except dropping the two PDFs into
`datasheets/texas-instruments/`.

| part | file | sha256 | status |
|---|---|---|---|
| OPA2197 (OPA197/OPA2197/OPA4197) | `datasheets/texas-instruments/OPA2197.pdf` | `27653a7d5e965cbb2d23f7998919ebd774efd5cd3e126b8f0881469ae91166fd` | OK |
| REF5050 (REF50xx family) | `datasheets/texas-instruments/REF5050.pdf` | `d2da9488194dba11732c85c498b563c12e0bb6b3e2d21631022dde9bff51a13d` | OK |

Fetch notes `[web]`:
- `https://www.ti.com/lit/ds/symlink/opa2197.pdf` → **HTTP 200**, `application/pdf`,
  2 174 683 B, 56 pages. `%PDF` magic OK, `pdftotext -layout` contains "OPA2197" 107×.
- `https://www.ti.com/lit/ds/symlink/ref5050.pdf` → **HTTP 404** (TI 404 HTML page,
  3 298 B). So does `.../symlink/ref5045.pdf` and `https://www.ti.com/lit/gpn/ref5050`.
  **The symlink name for this part no longer exists** — TI renamed the product folder
  to `REF50`/`REF50E` (see rev N/O revision history). The working URL is the
  document-number form: `https://www.ti.com/lit/ds/sbos410/sbos410.pdf` → **HTTP 200**,
  `application/pdf`, 5 082 549 B, 52 pages, "REF5050" 43× in extracted text.
  **The manifest's recorded source URL for this part is dead and should be replaced.**

Curve digitisation method `[calc]`: pages rendered with `pdftoppm -r 200/350 -png`,
axis gridlines located by dark-pixel row/column scan, trace located by colour mask,
log/linear mapping from the detected gridlines. Calibration is **independently
validated** — see §1a, where the digitised plateau lands on TI's own tabulated value.

---

# 1. OPA2197 — SBOS737C

## 1d. Document identity  `[datasheet SBOS737 p.1]`

> `OPA197, OPA2197, OPA4197`
> `SBOS737C – JANUARY 2016 – REVISED MARCH 2018`
> `OPAx197 36-V, Precision, Rail-to-Rail Input/Output, Low Offset Voltage, Operational Amplifiers`

- Document number **SBOS737**, revision **C**. Original January 2016, last revised
  **March 2018**. 56 pages. PDF metadata: `Keywords: , SBOS737,SBOS737C`,
  `Title: ... datasheet (Rev. C)`.
- **Rev C is still the latest** — this is what `ti.com/lit/ds/symlink/opa2197.pdf`
  serves today (2026-09-21).
- `OPA2197IDR` in the orderable addendum `[datasheet SBOS737C p.49]`:
  `Active / Production / SOIC (D) | 8 / 2500 | LARGE T&R / NIPDAU / Level-2-260C-1 YEAR / –40 to 125 / marking "2197"`.
  **The BOM's part number is real, current and correctly formed.**

## 1a. Open-loop output impedance Ro — **REPO REFUTED**

**Repo belief** `[repo] hardware/controller/carrier.md:228-231`:
> "Back-solving the OPA2197's output impedance from this page's own stated 21 kHz
> pole gives **Ro ≈ 75.8 Ω**."
and `[repo] carrier.md:267-269`: "`Ro = 75.8 Ω` is back-solved, not read."

### The datasheet does NOT give Ro only as a curve. There is a specified number.

`[datasheet SBOS737C p.8, §6.7 Electrical Characteristics, OUTPUT section]` — verbatim:

```
ZO   Open-loop output      f = 1 MHz, IO = 0 A, See Figure 26          375        Ω
     impedance
```

and identically `[datasheet SBOS737C p.10, §6.8]`:

```
ZO   Open-loop output      f = 1 MHz, IO = 0 A, see Figure 26          375        Ω
     impedance
```

**TI specifies ZO = 375 Ω typical.** The repo's 75.8 Ω is **4.95× too small**
against TI's own specified figure. The repo has been carrying a number that is
one fifth of the datasheet value, in a stability calculation, through four review
waves.

### Figure 26, digitised

`[datasheet SBOS737C p.16]` — "Figure 26. Open-Loop Output Impedance vs Frequency",
conditions banner: `TA = 25°C, VS = ±18 V, VCM = VS/2, RLOAD = 10 kΩ connected to
VS/2, and CL = 100 pF (unless otherwise noted)`. Single trace, log–log, x = 0.1 Hz
to 10 MHz, y = 10 Ω to 10 kΩ.

| frequency | Ro (digitised) |
|---|---|
| 0.1 Hz | **≈ 3.26 kΩ** |
| 1 Hz | ≈ 2.30 kΩ |
| 3 Hz | ≈ 1.08 kΩ |
| 10 Hz | ≈ 482 Ω |
| 30 Hz | ≈ 386 Ω |
| **100 Hz – 300 kHz (the plateau)** | **≈ 371 – 379 Ω** |
| 1 MHz | ≈ 301 Ω |
| 2 MHz | ≈ 221 Ω |
| 5 MHz | ≈ 114 Ω |
| 10 MHz | ≈ 73 Ω |

**Calibration check `[calc]`:** the digitised plateau reads 371–379 Ω against TI's
tabulated `ZO = 375 Ω`. The extraction is good to ≈ ±2 %. This is a genuine
independent validation, not a fit.

**Shape, stated plainly:** Ro is **not** flat. It *rises* below ~30 Hz to about
3.3 kΩ at 0.1 Hz (normal for a CMOS RRO stage at DC), sits on a **≈ 375 Ω plateau
from 100 Hz to about 300 kHz**, then falls above ~300 kHz to ≈ 73 Ω at 10 MHz.

**Minor internal discrepancy, reported honestly:** TI's table says `375 Ω` **at
f = 1 MHz**, but the plotted curve at exactly 1 MHz reads ≈ 300 Ω — the knee is
already past. Either TI is quoting the plateau value and labelling it "1 MHz", or
the plotted unit rolls off slightly earlier than the specified one. **Do not
resolve this by picking the convenient one.** Everywhere from DC to 1 MHz,
Ro ≥ 300 Ω.

### What this does to the repo's stability arithmetic — **the problem gets WORSE**

`[repo] carrier.md:229-233` computes a 21 kHz pole from Ro = 75.8 Ω against the
100 nF at the sensor's `VS` pin, and `[repo] bom.csv:27` (`U-BUF`) says "a pole at
21kHz (or 200Hz) INSIDE its own loop".

`[calc]`, using TI's specified `ZO = 375 Ω`:

```
100 nF  :  f_p = 1/(2*pi*375*100e-9)   = 4 244 Hz   ->   4.24 kHz   (repo says 21 kHz)
10.1 uF :  f_p = 1/(2*pi*375*10.1e-6)  =    42.0 Hz               (repo says 200 Hz)
```

Both poles sit **~5× lower** than the repo believes — i.e. **further below
crossover, more phase eaten, less margin**. The repo's conclusion ("`R-ISO-REF` is
needed, and the follower is unstable without compensation") is **strengthened, not
overturned**. But every component value derived from 75.8 Ω must be recomputed.

**One point in the repo's favour, stated so the lead does not over-correct:**
75.8 Ω is very close to the digitised Ro at **10 MHz** (≈ 73 Ω), which is the
unity-gain loop crossover frequency (GBW = 10 MHz). A textbook RISO analysis uses
Ro *at crossover*, so the repo's back-solve is a defensible estimate **of the
high-frequency Ro specifically**. It is nevertheless **not** the number TI
specifies, it is five times the low- and mid-frequency Ro, and any reader who
opens SBOS737C will find `375 Ω` and conclude the repo is wrong. **VERDICT:
REFUTED as written; the page must cite `ZO = 375 Ω typ (SBOS737C §6.7, p.8)` and,
if it wants to use ~73 Ω, say explicitly that it is reading Figure 26 at 10 MHz.**

## 1b. Capacitive-load limit — **THE REPO'S OWN DISPUTE IS WRONG. 1 nF IS AN OPA2197 FIGURE.**

**Repo belief** `[repo] hardware/controller/carrier.md:248-256`, verbatim:
> "⚠ The "1 nF maximum capacitive load" that stood here is **not a verified
> OPA2197 figure.** "Stable with 1-nF Capacitive Loads" is a **verbatim
> feature-list bullet of the INA828** (SBOS792A, first page, now in the repo)
> — a different part, in a different stage, on a different board. The
> OPA2197's own capacitive-load limit is **unverified**."

**This is refuted.** 1 nF appears **three times** in SBOS737C as an OPA2197 figure:

1. `[datasheet SBOS737C p.1, Features]` verbatim:
   > `• High Capacitive Load Drive Capability: 1 nF`
2. `[datasheet SBOS737C p.1, Description]` verbatim:
   > "Unique features such as differential input-voltage range to the supply rail,
   > high output current (±65 mA), **high capacitive load drive of up to 1 nF**, and
   > high slew rate (20 V/µs) make the OPA197 a robust, high-performance operational
   > amplifier for high-voltage, industrial applications."
3. `[datasheet SBOS737C p.22, §7.3.5 Capacitive Load and Stability]` verbatim:
   > "The OPAx197 features a patented output stage capable of driving large
   > capacitive loads, and **in a unity-gain configuration, directly drives up to
   > 1 nF of pure capacitive load.** Increasing the gain enhances the ability of the
   > amplifier to drive greater capacitive loads; see Figure 47 and Figure 48. The
   > particular op amp circuit configuration, layout, gain, and output loading are
   > some of the factors to consider when establishing whether an amplifier will be
   > stable in operation."

The INA828 bullet is real too — I checked the banked copy: `[repo]
datasheets/texas-instruments/INA828IDR.pdf` p.1 line 22, "• Stable with 1-nF
Capacitive Loads". **Both parts carry a 1 nF capacitive-load headline. The numbers
coincide.** The reviewer who traced the repo's figure to the INA828 traced it to a
part that *also* says 1 nF, and concluded from the coincidence that the OPA2197
figure was unverified. It was unverified — but it was also **correct**.

Per CLAUDE.md's own rule ("a wrong finding gets caught by the next reviewer while
a finding filed as handled does not"), **the ⚠ block in `carrier.md:248-269` is now
itself the stale artefact** and should be replaced by a citation, not left standing.

**Note the qualifier, which is the part that actually matters here:** the 1 nF is
"**pure capacitive load**" in "**a unity-gain configuration**". The section is
§7.3.5, **not** a §9.x — the repo's expectation of a "9.x Capacitive Load and
Stability" section is wrong for rev C. §9 in SBOS737C is "Power Supply
Recommendations".

### Figure 47 / Figure 48 — Small-Signal Overshoot vs Capacitive Load

`[datasheet SBOS737C p.23]` (duplicated as Figures 27 and 28 on p.16). Both are
**100-mV output step**, three traces: RISO = 0 Ω / 25 Ω / 50 Ω, x = 20–2000 pF log.
Figure 47 is **G = –1 V/V**; Figure 48 is **G = +1 V/V (unity gain)** — Figure 48 is
the one that governs the repo's reference buffer and breath buffer, both of which
are followers.

**Figure 48, G = +1 V/V (unity gain)** — digitised, ±2 percentage points:

| CL | RISO = 0 Ω | RISO = 25 Ω | RISO = 50 Ω |
|---|---|---|---|
| 50 pF | 12.4 % | — | 12.0 % |
| 100 pF | 15.5 % | — | 14.9 % |
| 200 pF | 20.7 % | 21.4 % | 20.0 % |
| 300 pF | 26.2 % | 25.3 % | 17.0 % |
| **400 pF** | **30.4 %** | 24.0 % | 15.0 % |
| 500 pF | 32.4 % | 21.2 % | 13.0 % |
| 700 pF | 36.2 % | 19.8 % | 11.6 % |
| **1000 pF (= the "1 nF" limit)** | **40.3 %** | 18.4 % | 10.0 % |
| 1300 pF | 43.4 % | 16.4 % | 9.6 % |
| **1600 pF** | **≈ 45 %** | 16.6 % | 9.0 % |
| 1950 pF | 48.2 % | 16.5 % | 9.0 % |

**Answers to the brief's question:** bare (RISO = 0), unity gain — **~30 % overshoot
is reached at ≈ 400 pF, and ~45 % at ≈ 1.6 nF. At TI's headline 1 nF the bare
overshoot is ≈ 40 %.** So "1 nF max capacitive load" is **not** a 30 %-overshoot
threshold; it is a *stable-but-ringing* limit. Anyone reading "drives 1 nF" as
"1 nF is fine" is reading it wrong.

**Figure 47, G = –1 V/V** (for completeness), digitised:
200 pF 13.4 % / 500 pF 23.6 % / 1000 pF 33.3 % / 2000 pF ≈ 42.5 % at RISO = 0;
the RISO = 25 Ω trace flattens at ≈ 24 % and RISO = 50 Ω at ≈ 16.7 %.

### Is an isolation resistor recommended? YES, with values.

`[datasheet SBOS737C p.23]` verbatim:

> "For additional drive capability in unity-gain configurations, improve capacitive
> load drive by inserting a small **(10-Ω to 20-Ω) resistor, RISO,** in series with
> the output, as shown in Figure 49. This resistor significantly reduces ringing
> while maintaining dc performance for purely capacitive loads. However, if there
> is a resistive load in parallel with the capacitive load, a voltage divider is
> created, introducing a gain error at the output and slightly reducing the output
> swing. The error introduced is proportional to the ratio RISO / RL, and is
> generally negligible at low output levels. **A high capacitive load drive makes
> the OPA197 well suited for applications such as reference buffers,** MOSFET gate
> drives, and cable-shield drives."

**`Table 3. OPA197 Capacitive Load Drive Solution Using Isolation Resistor`**
`[datasheet SBOS737C p.23]` — measured + calculated, RISO for a target phase margin:

| CL | RISO for 45° PM | RISO for 60° PM | measured overshoot @45° / @60° |
|---|---|---|---|
| 100 pF | 47.0 Ω | 360.0 Ω | 23.2 % / 8.6 % |
| 1000 pF | 24.0 Ω | 100.0 Ω | 22.5 % / 9.0 % |
| 0.01 µF | 20.0 Ω | 51.0 Ω | 22.1 % / 8.7 % |
| 0.1 µF | 6.2 Ω | 15.8 Ω | 23.1 % / 8.6 % |
| 1 µF | 2.0 Ω | 4.7 Ω | 21.0 % / 8.6 % |

Cross-reference: "TI Precision Design **TIDU032**, *Capacitive Load Drive Solution
using an Isolation Resistor*".

### ⚑ TI has a worked **Precision Reference Buffer into 10 µF** — the repo's exact problem

`[datasheet SBOS737C p.30, §8.2.3 Precision Reference Buffer, Figure 56]` verbatim:

> "The OPAx197 features high output current drive capability and low input offset
> voltage, making the device an excellent reference buffer to provide an accurate
> buffered output with ample drive current for transients. For the **10-µF ceramic
> capacitor** shown in Figure 56, **RISO, a 37.4-Ω isolation resistor,** provides
> separation of two feedback paths for optimal stability. **Feedback path number one
> is through RF and is directly at the output, VOUT. Feedback path number two is
> through RFx and CF and is connected at the output of the op amp.** The optimized
> stability components shown for the 10-µF load give a closed-loop signal bandwidth
> at VOUT of 4 kHz, while still providing a loop gain phase margin of 89°. **Any
> other load capacitances require recalculation of the stability components: RF,
> RFx, CF, and RISO.**"

Figure 56 component values: **RF = 1 MΩ, RFx = 10 kΩ, CF = 39 nF, RISO = 37.4 Ω,
CL = 10 µF, VREF = 2.5 V.**

This is the same topology the repo proposes — in-loop isolation resistor, feedback
taken past it, plus a feedback zero — for the same load. Three deltas the lead
should look at:

1. **`R-ISO-REF` is specified as 10 Ω** `[repo] bom.csv:128`. TI's worked value for
   a 10 µF load is **37.4 Ω**, and Table 3's own 60°-PM entry for 0.1 µF is 15.8 Ω.
   10 Ω is TI's *lower bound* for the generic "10–20 Ω" unity-gain advice against a
   *small* CL, not for microfarads.
2. **The repo's own feedback-zero inequality fails with its own numbers.**
   `[repo] carrier.md:239-243` gives `R_F·C_F > R-ISO-REF·C_LOAD`, worked as
   "10 kΩ + 1 nF against 10 Ω + 100 nF = 1 µs". `[calc]` 10 kΩ × 1 nF = 10 µs and
   10 Ω × 100 nF = 1 µs, so it passes — **but only because C_LOAD was taken as
   100 nF.** Two other repo files put `C-REF-OUT`'s **10 µF on that same node**
   (`[repo] bom.csv:27` U-BUF, `[repo] hardware/module/breath-receive-stage.md:341`),
   giving 10 Ω × 10.1 µF = **101 µs > 10 µs — the inequality FAILS.** TI's own
   values satisfy it: 10 kΩ × 39 nF = 390 µs vs 37.4 Ω × 10 µF = 374 µs.
3. **⚑ The repo contradicts itself about where `C-REF-OUT` sits.** `[repo]
   carrier.md:164-166` draws the 10 µF on the **REF5050 output = the buffer's
   INPUT**; `[repo] bom.csv:27` and `[repo] breath-receive-stage.md:341` both say the
   buffer **drives** it. These cannot both be true, and which one is true changes
   the compensation completely. **This is a semantic defect the checker cannot
   catch — flagging it for the lead.**

## 1c. Other figures the repo cites

All `[datasheet SBOS737C p.7–p.10, §6.7/§6.8]` unless noted.

| parameter | datasheet | note |
|---|---|---|
| **GBW** | **10 MHz** (typ), both supply tables | no min/max given |
| **Slew rate SR** | **20 V/µs** typ, `VS = ±18 V, G = 1, 10-V step` | 14 V/µs typ at ±2.25–±4 V, G=1, 1-V step (p.10) |
| **Isc** | **±65 mA** typ, `VS = ±18 V` | same ±65 mA at VS = ±2.25 V (p.10). Abs-max: output short to ground is **Continuous**, one amplifier per package (p.5) |
| **VO swing from rail**, no load | 5 mV typ / **25 mV max** | both rails |
| **VO swing from rail**, RL = 10 kΩ | 95 mV typ / **125 mV max** | both rails |
| **VO swing from rail**, RL = 2 kΩ | 430 mV typ / **500 mV max** | both rails |
| **Supply range** | **±2.25 V to ±18 V / +4.5 V to +36 V** (Recommended Operating Conditions, p.5) | Abs max ±20 V dual / 40 V single. §9 p.30 CAUTION: ">40 V can permanently damage the device" |
| **PSRR** | **±1 µV/V typ, ±3 µV/V max**, TA = –40 to +125 °C (p.7); ±2 µV/V typ at low supply (p.9) | **specified in µV/V, not dB** |
| **IQ per amplifier** | **1 mA typ, 1.3 mA max** @ IO = 0 A; **1.5 mA max** over –40…+125 °C | per amplifier, so a dual is ~2 mA |
| **VOS** | ±25 µV typ / ±100 µV max (VS = ±18 V) | ±10 µV typ / ±100 µV max at VCM = (V+)–1.5 V |
| **dVOS/dT** | ±0.5 µV/°C typ / ±2.5 µV/°C max | ±0.8/±4.5 at VCM = (V+)–1.5 V |
| **AOL** | 134 dB typ / 120 dB min (RL = 2 kΩ); 143 dB typ / 120 dB min (RL = 10 kΩ), VS = ±18 V | |
| **Thermal protection** | output goes **high-Z above 140 °C** junction (§7.3.4 p.22); TJ abs max 150 °C | a real behaviour, not just a rating |
| **Operating TA** | –40 to +125 °C (recommended); –55 to +150 °C (abs max) | |

**SOIC-8 (D) package / thermal, OPA2197** `[datasheet SBOS737C p.6, §6.5 Thermal
Information: OPA2197]`:

| metric | D (SOIC) 8 pins | DGK (VSSOP) 8 pins |
|---|---|---|
| RθJA | **107.9 °C/W** | 158 °C/W |
| RθJC(top) | 53.9 | 48.6 |
| RθJB | 48.9 | 78.7 |
| ψJT | 6.6 | 3.9 |
| ψJB | 48.3 | 77.3 |
| RθJC(bot) | N/A | N/A |

Body size SOIC (8) **4.90 mm × 3.90 mm** `[datasheet SBOS737C p.1]`.
⚠ Note the **single** OPA197 in SOIC-8 has RθJA = **115.8 °C/W** (p.6, §6.4) — do not
mix the tables; the dual's number is 107.9.

`[datasheet SBOS737C p.7]` footnote (1) on AOL, worth carrying into the module
pages given six packages on ±12 V: *"For OPA2197, OPA4197: When driving high
current loads on multiple channels, make sure the junction temperature does not
exceed 125°C."*

## 1e. Repo claim ledger — OPA2197

| # | repo claim (file:line) | verdict | datasheet |
|---|---|---|---|
| 1 | `carrier.md:228-231` "Ro ≈ 75.8 Ω", back-solved | **REFUTED** | `ZO = 375 Ω typ, f = 1 MHz, IO = 0 A` (p.8 & p.10). 75.8 Ω is ~the **10 MHz** value off Fig 26, not the specified one |
| 2 | `carrier.md:248-256` "the 1 nF max capacitive load is **not** a verified OPA2197 figure; it is an INA828 bullet" | **REFUTED — the dispute is wrong** | p.1 Features "High Capacitive Load Drive Capability: 1 nF"; p.1 Description; §7.3.5 p.22 "directly drives up to 1 nF of pure capacitive load" |
| 3 | `carrier.md:252` "SBOS737 is BLOCKED"; `MANIFEST.csv:61` OPA2197IDR BLOCKED, "HTTP 000" | **REFUTED (stale)** | fetched 2026-09-21, HTTP 200, banked, sha256 above |
| 4 | `carrier.md:261-266` "settle it with TI's OPAx197 SPICE macromodel" | **SUPERSEDED** | the datasheet has the number; CLAUDE.md §3 — the banked document wins |
| 5 | `bom.csv:13` "RRIO on +/-12V reaches ~11.9V"; `0004:220` "on ±12 V it reaches roughly 11.9 V" | **CONFIRMED** | swing from rail RL = 10 kΩ: 95 mV typ → 12 − 0.095 = **11.905 V** (p.8) |
| 6 | `0003:504` "reaches within ~30 mV of ground" | **PARTIAL / optimistic** | that is the **no-load** figure (5 mV typ / 25 mV max). With RL = 10 kΩ it is 95 mV typ / **125 mV max**; with RL = 2 kΩ, **500 mV max** — which would **miss** the 0.2 V floor that line is defending. Conclusion survives only because the breath buffer's load is ≥10 kΩ. **Say which load.** |
| 7 | `mod-channels.md:107`, `pitch-stage.md:153-154`, `0006:137` "an OPA2197 on ±12 V less two Schottky drops reaches ~±11.45 V" | **CONSISTENT** | 12 − 0.095 (RL=10k typ) − 2 Schottky ≈ 11.45 V is the repo's own arithmetic; the op-amp term is right |
| 8 | `breath-output-stage.md:138,144` "the OPA2197 stops at about ±11.5 V" | **CONSISTENT** | same basis as #5/#7, rounded |
| 9 | `carrier.md:291` "OPA2197 2 × ~1 mA"; `0013:242` | **CONFIRMED** | IQ = 1 mA typ **per amplifier**, 1.3 mA max @25 °C, 1.5 mA max over temp (p.8) |
| 10 | `figures.yaml:217` + `power-entry.md:77` + `0006:633-634` "OPA2197 PSRR (114 dB)" | **NOT-IN-DOCUMENT** | PSRR is specified as **±1 µV/V typ / ±3 µV/V max**. `[calc]` 20·log10(1/1e-6) = **120 dB typ**; 20·log10(1/3e-6) = **110.5 dB worst case**. 114 dB appears nowhere. It is between typ and worst case, so the 0.00029-cents conclusion is unaffected — but the figure is unsourced and should be restated as "120 dB typ / 110.5 dB min, from ±1/±3 µV/V, SBOS737C p.7" |
| 11 | `bom.csv:13` "Six packages, twelve halves" | **CONFIRMED** | OPA2197 is a dual (p.4 pin functions: OUT A/OUT B) |
| 12 | `bom.csv:13,27,84` `OPA2197IDR`, SOIC-8 1.27 mm | **CONFIRMED** | orderable addendum p.49: Active, Production, SOIC (D) 8, –40…125 °C |
| 13 | `0006:381` "OPA2197-class, not TL072 — offset drift" | **CONFIRMED** | dVOS/dT ±0.5 µV/°C typ, ±2.5 µV/°C max |
| 14 | `bom.csv:27` "a pole at 21kHz (or 200Hz) INSIDE its own loop … which no general-purpose precision op-amp survives unconditionally" | **DIRECTION CONFIRMED, NUMBERS REFUTED** | with ZO = 375 Ω the poles are **4.24 kHz** and **42 Hz** `[calc]` — five times worse. §7.3.5 caps unity-gain pure-C drive at 1 nF; 100 nF and 10 µF are 100× and 10 000× that |
| 15 | `bom.csv:128` `R-ISO-REF` = 10 Ω | **REFUTED as a value** | TI's worked reference-buffer-into-10 µF uses **RISO = 37.4 Ω** (§8.2.3 p.30); Table 3 gives 15.8 Ω for 60° PM at only 0.1 µF. "10–20 Ω" (p.23) is generic small-CL advice |

---

# 2. REF5050 — SBOS410O

## 2c. Document identity  `[datasheet SBOS410 p.1]`

> `REF50, REF50E`
> `SBOS410O – JUNE 2007 – REVISED OCTOBER 2025`
> `REF50xx Low-Noise, Very Low Drift, Wide VIN Precision Voltage Reference`

- Document number **SBOS410**, revision **O**. Original June 2007, last revised
  **October 2025**. 52 pages. PDF metadata `Keywords: SBOS410O`.
- **The family/product folder was renamed** — the running head is now `REF50, REF50E`
  (was `REF50XX`; see §11 Revision History, "Changes from Revision M (December 2024)
  to Revision N (March 2025): Update datasheet header folder link from REF50XX to
  REF50 and REF50E"). **This is why `ti.com/lit/ds/symlink/ref5050.pdf` now 404s.**
- Rev O is new: `§11` lists "**Added Table 4-2**" (the grade comparison table) and
  "Updated pin information from: REF50xxA to: REF50xxAI" as rev-O changes. **A repo
  belief formed against rev M or earlier may predate that table.**
- `REF5050AIDR` in the orderable addendum `[datasheet SBOS410O p.36]`:
  `Active / Production / SOIC (D) | 8 / 2500 | LARGE T&R / NIPDAU / Level-2-260C-1 YEAR / –40 to 125 / marking "REF 5050 A"`. `REF5050IDR` also Active.

## 2b. ⚑⚑ Grade — **THE BOM'S PART NUMBER AND ITS STATED SPEC DO NOT MATCH**

**Repo belief** `[repo] hardware/bom.csv:26` (`U-REF-BREATH`), verbatim:
> `U-REF-BREATH,controller,REF5050AIDR,TI,5.000V precision series reference …
> "+-0.05%, 3ppm/degC, ~5ppm/V line reg. The MPXV4006DP is ratiometric so its
> supply IS its scale factor."`

and `[repo] docs/decisions/0003-breath-sensing-path.md:472`:
> "**REF5050**, SOIC-8, 7–18 V in, 5.000 V out at ±0.05 % and 3 ppm/°C, with line
> regulation around 5 ppm/V"

**`Table 4-2. Device Performance Comparison`** `[datasheet SBOS410O p.3]` — verbatim:

| Device | Grade | Temperature Coefficient | Initial Accuracy | Noise | VIN Max | Quiescent Current Max |
|---|---|---|---|---|---|---|
| REF50xxEI | Enhanced | 2.5 ppm/ºC | ±0.025 % | 0.5 µVPP/V | 42 V | 480 µA |
| REF50xx**I** | **High** | 3 ppm/ºC | **±0.05 %** | 3 µVPP/V | 18 V | 1.2 mA |
| REF50xx**AI** | **Standard** | **8 ppm/ºC** | **±0.1 %** | 3 µVPP/V | 18 V | 1.2 mA |

and `[datasheet SBOS410O p.1, §3 Description]` verbatim:
> "REF50 family is available in enhanced grade (REF50xx**EI**), high grade
> (REF50xx**I**), and standard grade (REF50xx**AI**)."

**The "A" suffix is the WORSE grade, not the better one.** Two independent places
in rev O agree (p.1 Description and Table 4-2).

**`REF5050AIDR` — the part the BOM orders — is ±0.1 % and 8 ppm/°C max.**
The `±0.05 % / 3 ppm/°C` the BOM and ADR 0003 both claim belongs to
**`REF5050IDR`** (no `A`).

Confirmed against the electrical table, `[datasheet SBOS410O p.7, §6.5 Electrical
Characteristics REF50xxI and REF50xxAI]` — verbatim rows:

```
 Initial    High Grade       All voltage options (1)      -0.05          0.05    %
 Accuracy   Standard Grade   All voltage options (1)       -0.1           0.1    %

 OUTPUT VOLTAGE TEMPERATURE DRIFT
            High grade                                             2.5      3
 dVOUT/dT                    TA = -40C to 125C                                   ppm/C
            Standard grade                                           3      8
```

(the unit cell renders as `pm/℃` in the PDF text layer — a layout artefact; the
column is ppm/°C.)

So even the `3 ppm/°C` in the BOM is, for an `AI` part, only the **typical** —
the **max is 8 ppm/°C**, 2.7× worse.

**This matters because the repo says it matters.** `[repo] bom.csv:26` — "The
MPXV4006DP is ratiometric so its supply IS its scale factor"; `[repo] bom.csv:27`
— "2% of a ratiometric scale factor **against a reference specified to 0.05%**".
That last clause is false for the part on the BOM. `[calc]` over –40…+125 °C the
`AI` grade's drift alone is 8 ppm/°C × 165 °C = **1320 ppm = 0.132 %**, on top of
±0.1 % initial; the `I` grade would be 3 × 165 = 495 ppm = 0.0495 % on top of
±0.05 %. **Roughly 2.7× the total scale-factor error the repo has budgeted.**

**Two ways out, both for the lead, not me:** change the BOM part to `REF5050IDR`,
or change the stated specs to ±0.1 % / 8 ppm/°C and re-run the breath scale-factor
budget. **Do not "fix" it by editing only one of the two files that state it** —
`bom.csv:26` and `0003-breath-sensing-path.md:472` both carry the number, which is
exactly the failure mode CLAUDE.md opens with.

### Remaining 2b figures — all `[datasheet SBOS410O p.7–8, §6.5]`, `REF50xxI/AI`

Test conditions banner: `At TA = 25°C, ILOAD = 0, CL = 1μF and VIN = (VOUT + 0.2V)
to 18V, unless otherwise noted`.

| parameter | value |
|---|---|
| VOUT, REF5050 | **5 V** |
| Initial accuracy, Standard (`AI`) | **±0.1 % max** |
| Initial accuracy, High (`I`) | ±0.05 % max |
| dVOUT/dT, Standard (`AI`) | **3 ppm/°C typ, 8 ppm/°C max**, –40…125 °C |
| dVOUT/dT, High (`I`) | 2.5 ppm/°C typ, 3 ppm/°C max |
| **Noise 0.1–10 Hz** (`enpp`) | **3 µVPP/V** → `[calc]` ×5 V = **15 µVPP** at 5.000 V |
| Noise 10 Hz–1 kHz (`en`) | 0.9 µVrms/V → `[calc]` 4.5 µVrms |
| **Line regulation** | **1 ppm/V typ, 3 ppm/V max** @25 °C; **5 ppm/V max** over –40…125 °C. Condition: VIN = (VOUT+0.2 V) to 18 V |
| **Load regulation** | **20 ppm/mA typ, 30 ppm/mA max**, –10 mA < IOUT < 10 mA at VIN = VOUT + 0.75 V; **50 ppm/mA max** over temperature |
| Short-circuit current | 25 mA typ (VOUT = 0) |
| Thermal hysteresis, SOIC-8, Standard grade | 90 ppm cycle 1, 50 ppm cycle 2 (High grade: 70 / 50) |
| **Long-term stability**, SOIC-8 | **22 ppm** 0–1000 h; **18 ppm** 1000–2000 h (VSSOP-8: 50 / 25) |
| Turn-on settling | 200 µs to 0.1 % with CL = 1 µF |
| **Quiescent current** | **0.8 mA typ, 1 mA max** @25 °C; **1.2 mA max** over –40…125 °C |
| TEMP pin | 575 mV out, 2.64 mV/°C |
| Specified / operating temperature | –40…125 °C / –55…125 °C |

**Dropout / minimum headroom** — this is a two-part answer:
- `[datasheet SBOS410O p.5, §6.3 Recommended Operating Conditions]`: `VIN` MIN =
  **VOUT + 0.2 V**, MAX = **18 V** (for `I`/`AI`; the `EI` goes to 42 V). NR pin 0–6 V.
  IOUT **–10 to +10 mA**. Footnote: "Except for the REF5020, where VIN (minimum) = 2.7 V."
- `[datasheet SBOS410O p.26-27, §8.4.2 Supply Voltage]` verbatim: "The REF50xx
  family of voltage references features extremely low dropout voltage. With the
  exception of the REF5020 … operate the family of references with a supply of
  **200mV more than the output voltage in an unloaded condition.** For loaded
  conditions, Figure 6-6 shows a typical dropout voltage versus load plot."
- **`Figure 6-6. Dropout Voltage vs Load Current`** `[datasheet SBOS410O p.11]`,
  digitised: **sourcing 10 mA → ≈ 0.47 V at –40 °C, ≈ 0.56 V at +25 °C, ≈ 0.73 V at
  +125 °C.** Sinking (negative IOUT) and at zero load it is flat at ≈ 25 mV.
  `[calc]` For the Woody carrier, which sources ~10 mA into the sensor, worst-case
  VIN ≥ 5.0 + 0.73 = **5.73 V**. There is 12 V. No issue — but the number to cite is
  0.73 V at 10 mA/125 °C, **not** 200 mV, which is the *unloaded* figure.

Abs max `[p.5]`: VIN –0.3…**18 V** (`I`/`AI`), VOUT –0.3…5.5 V, TJ 150 °C.
Thermal `[p.6, §6.4]`, SOIC-8 `I`/`AI`: **RθJA 115 °C/W**, RθJC(top) 63.4, RθJB 57.1,
ψJT 15.4, ψJB 56.2. (VSSOP-8: RθJA 160.9.)

## 2a. ⚑ The output-capacitor recommendation — `C-REF-OUT` qty 2

The sections are numbered as the brief expected: **§8.4.1 Basic Connections** and
**§9.4.1.1 REF50xxI, REF50xxAI Layout Guidelines**.

### §8.4.1 Basic Connections — `[datasheet SBOS410O p.26]`, verbatim

> "Figure 8-6 shows the typical connections for the REF50xx. **TI recommends a
> supply bypass capacitor ranging from 1μF to 10μF. Confirm that a output capacitor
> (CL) is connected from VOUT to GND. For output stability, verify that the
> equivalent series resistance (ESR) value of CL less than or equal to 1.5Ω. To
> minimize noise, the recommended ESR of CL is from 1Ω and 1.5Ω.**"

Figure 8-6 annotations, verbatim:
> `CBYPASS 1µF to 10µF` (on VIN)
> `CL = 1µF to 50µF for REF50xxI, REF50xxAI`
> `CL = 1µF to 100µF for REF50xxEI`

### §9.4.1.1 REF50xxI, REF50xxAI Layout Guidelines — `[datasheet SBOS410O p.29-30]`, verbatim

> "• Place the power-supply bypass capacitor as closely as possible to the supply
> and ground pins. **The recommended value of this bypass capacitor is from 1μF to
> 10μF.** If necessary, add decoupling capacitance to compensate for noisy or
> high-impedance power supplies.
> • **Place a 1μF noise filtering capacitor between the NR pin and ground.**
> • **Verify that the output decouples with a 1μF to 50μF capacitor. A resistor in
> series with the output capacitor is optional. For better noise performance, the
> recommended ESR on the output capacitor is from 1Ω to 1.5Ω.**
> • **Add a high-frequency, 1μF capacitor in parallel between the output and ground**
> to filter noise and help with switching loads as data converters."

### §9.3 Power Supply Recommendations — `[datasheet SBOS410O p.29]`, verbatim

> "TI recommends a supply bypass capacitor ranging from **1μF to 50μF for REF50xxI
> and REF50xxAI.** TI recommends a supply bypass capacitor ranging from 1μF to 100μF
> for REF50xxEI."

(⚠ §9.3 says the VIN bypass may be **1–50 µF** while §8.4.1 and §9.4.1.1 both say
**1–10 µF**. TI's own document is inconsistent. 10 µF satisfies all three.)

### §9.2.1.1 / §9.2.1.2 — the ESR warning, and it cuts against a bare ceramic

`[datasheet SBOS410O p.28]` verbatim:
> "When using the REF50xx in the design, **select a proper output capacitor that
> does not create gain peaking, thereby increasing total system noise.** At the same
> time, select a capacitor that provides the required filtering performance for the
> system. Add input bypass capacitor and noise reduction capacitors for peak
> performances."

`[datasheet SBOS410O p.28-29]` verbatim:
> "The REF5040 is used to drive the REF pin of the ADS8326. Proper selection of
> voltage reference output capacitor is very important for this design. **Very low
> equivalent series resistance (ESR) creates gain-peaking, which degrades SNR of the
> total system. If the ESR of the capacitor is not enough, then an additional
> resistor must be added in series with the output capacitor.** A capacitance of 1μF
> can connect to the NR pin to reduce band-gap noise of the REF50xx."

TI's own Figure 9-1 draws an explicit **`ESR`** resistor in series with the 47 µF at
the reference output, and Table 9-1 measures **86.7 dB SNR** (10 µF out, 0 µF on NR)
vs **92.8 dB** (10 µF + 47 µF out, 1 µF on NR) — a **6.1 dB** improvement.

### ⚑ For the `EI` grade only, there is a hard tabulated CAPACITIVE LOAD spec

`[datasheet SBOS410O p.9, §6.6 Electrical Characteristics REF50xxEI]` — verbatim:
```
 CAPACITIVE LOAD
        Stable input capacitor  range   -40C <= TA <= 125C     0.1                     µF
 CIN
        Stable output capacitor range   -40C <= TA <= 125C       1            100      µF
 CL
```
**There is no equivalent table for the `I`/`AI` grades** — for those the limits come
only from §8.4.1 / §9.4.1.1 prose (1–50 µF out, ESR ≤ 1.5 Ω). And §9.4.1.2 for the
`EI` says "**low ESR (maximum 1Ω)**" — the opposite sense from the `AI`'s 1–1.5 Ω
recommendation. **Do not carry an `EI` number onto an `AI` part.**

### The answer to the repo's open question

`[repo] hardware/controller/carrier.md:940` and `:819`:
> "**`C-REF-OUT` qty 2** for one REF5050 — parallel, or input and output?"

**TI requires a capacitor on BOTH pins, so "one input + one output" is the reading
that matches the datasheet** — but qty 2 is still short of TI's recommended layout,
and one of the two is the wrong dielectric choice without a series resistor:

1. **VOUT — REQUIRED.** "**Confirm that a output capacitor (CL) is connected from
   VOUT to GND**" (§8.4.1). Range **1–50 µF** for `AI`. The BOM's 10 µF is in range.
2. **VIN — RECOMMENDED**, 1–10 µF (§8.4.1, §9.4.1.1) or 1–50 µF (§9.3). The BOM's
   10 µF is in range, at the top of the tighter range. Note `[repo] bom.csv:75`
   already books a 100 nF `C-DECOUPLE-CARRIER` for "REF5050 in", so the 10 µF at VIN
   is bulk *in addition to*, not instead of, the HF cap. Consistent with TI.
3. **⚑ MISSING: the 1 µF on TRIM/NR.** "Place a **1μF noise filtering capacitor
   between the NR pin and ground**" (§9.4.1.1). `[datasheet SBOS410O p.26, §8.3.6]`:
   "A capacitance of 1μF creates a low-pass filter with the corner frequency from
   10Hz to 20Hz. **A low-pass filter decreases the overall noise measured on the
   VOUT pin by half.** … Using this capacitor increases start-up time." **No NR
   capacitor appears anywhere in `bom.csv`.** On a rail whose noise is the breath
   scale factor, this is a free halving of reference noise that the BOM is not
   taking.
4. **⚑ MISSING: the second, high-frequency 1 µF at the output.** "Add a
   high-frequency, 1μF capacitor **in parallel** between the output and ground to
   filter noise and **help with switching loads as data converters**" (§9.4.1.1).
5. **⚑⚑ ESR: `C-REF-OUT` as specified is a stability/noise risk.** `[repo]
   bom.csv:76` specifies `10uF X7R … 1206`. `[calc]` a 1206 X7R MLCC has ESR of
   roughly 2–20 mΩ at the relevant frequencies — **two to three orders of magnitude
   below TI's recommended 1–1.5 Ω**. TI: "Very low equivalent series resistance
   (ESR) creates gain-peaking … **If the ESR of the capacitor is not enough, then an
   additional resistor must be added in series with the output capacitor**"
   (§9.2.1.2), and "For better noise performance, the recommended ESR on the output
   capacitor is from 1Ω to 1.5Ω" (§9.4.1.1). **The BOM needs a ~1–1.5 Ω resistor in
   series with the output `C-REF-OUT`, and it has none.** (The 1.5 Ω is an upper
   bound *for stability*; 1–1.5 Ω is the recommended band *for noise*. A resistor
   here costs nothing in DC accuracy because it is in series with the *capacitor*,
   not with the load — unlike `R-ISO-REF`.)

### ⚑ Repo-internal contradiction about where `C-REF-OUT` sits (repeat of §1b item 3)

- `[repo] carrier.md:164-166` draws `C-REF-OUT 10 µF` on the **REF5050 output**,
  i.e. the buffer's **input** — which is what TI's `CL` means.
- `[repo] bom.csv:27` (`U-BUF`): "as an unbuffered follower this drives the sensor's
  100nF decoupler **plus C-REF-OUT's 10uF**" — buffer **output**.
- `[repo] breath-receive-stage.md:341`: "into the sensor's `VS` pin — which carries a
  100 nF decoupler **and `C-REF-OUT`'s 10 µF**" — buffer **output**.

If the 10 µF is on the REF5050's output (TI's `CL`), the OPA2197 buffer never sees
it and the buffer's load is 100 nF alone — which changes §1b's compensation
completely. **The checker cannot see this. It needs a human decision.**

## 2d. Repo claim ledger — REF5050

| # | repo claim (file:line) | verdict | datasheet |
|---|---|---|---|
| 1 | `bom.csv:26` `REF5050AIDR` **"+-0.05%, 3ppm/degC"** | **REFUTED** | `REF50xxAI` = **Standard** grade = **±0.1 %, 8 ppm/°C max** (Table 4-2 p.3; §6.5 p.7; §3 Description p.1). ±0.05 %/3 ppm/°C is `REF5050IDR` |
| 2 | `0003:472` "5.000 V out at **±0.05 %** and **3 ppm/°C**" | **REFUTED** | same. Duplicated claim — fix **both** files |
| 3 | `bom.csv:27` "a reference specified to **0.05%**" | **REFUTED** | ±0.1 % for the ordered part |
| 4 | `bom.csv:26` / `0003:473` "~5 ppm/V line reg" / "line regulation around 5 ppm/V" | **CONFIRMED (as the over-temperature max)** | 1 ppm/V typ, 3 ppm/V max @25 °C, **5 ppm/V max over –40…125 °C** (§6.5 p.7). Worth saying which |
| 5 | `0003:473-474` "a full volt of movement on +12 V shifts the sensor supply by ~25 µV" | **CONFIRMED** | `[calc]` 5 ppm/V × 5.000 V × 1 V = **25 µV** |
| 6 | `0003:472` "**7–18 V in**" | **NOT-IN-DOCUMENT (conservative)** | MAX 18 V ✓. MIN is **VOUT + 0.2 V = 5.2 V** unloaded (§6.3 p.5), rising to ≈ **5.73 V** at 10 mA/125 °C off Figure 6-6. 7 V appears nowhere; it is safe but unsourced |
| 7 | `0003:475-477` "The reference alone can source 10 mA against the sensor's ~10 mA, which is inside its rating and has no margin" | **CONFIRMED** | IOUT recommended **–10 to +10 mA** (§6.3 p.5); §9.4.3: "specified to deliver current loads of ±10mA over the specified input voltage range". Isc 25 mA typ is not a rating to design to |
| 8 | `carrier.md:291` "REF5050 ~1 mA" | **CONFIRMED** | IQ 0.8 mA typ, **1 mA max @25 °C**, 1.2 mA max over temp (§6.5 p.8) |
| 9 | `bom.csv:76` `C-REF-OUT` **qty 2**, "Per the REF50xx datasheet's recommended output capacitance" | **PARTIALLY CONFIRMED** | a VOUT cap is **required** and a VIN bypass **recommended**, so 2 is defensible as in+out. But TI's `I`/`AI` layout list wants **four** caps (VIN 1–10 µF, VOUT 1–50 µF, a parallel HF 1 µF at VOUT, 1 µF on NR) and the BOM has two |
| 10 | `bom.csv:76` `10uF X7R 1206`, no series resistor | **REFUTED / DEFECT** | ESR of CL must be **≤1.5 Ω for stability** and is recommended **1–1.5 Ω for noise**; a 1206 X7R is ~2–20 mΩ. TI: "If the ESR of the capacitor is not enough, then an additional resistor **must** be added in series with the output capacitor" (§9.2.1.2 p.28-29) |
| 11 | BOM has **no TRIM/NR capacitor** | **DEFECT (omission)** | §9.4.1.1 "Place a 1μF noise filtering capacitor between the NR pin and ground"; §8.3.6 "decreases the overall noise measured on the VOUT pin **by half**" |
| 12 | `carrier.md:819,940` "qty 2 for one part — parallel, or in+out?" | **ANSWERED: in + out** | §8.4.1 Figure 8-6 puts `CBYPASS` on VIN and `CL` on VOUT; both are called for |
| 13 | `MANIFEST.csv:62` REF5050AIDR **BLOCKED**, "Datasheet is SBOS410 (rev O, Oct 2025)" | **REFUTED (stale) / rev CORRECT** | fetched 2026-09-21 via `ti.com/lit/ds/sbos410/sbos410.pdf`, HTTP 200. The recorded rev **O, October 2025 is right** — that earlier agent got the revision right from metadata alone. The `symlink/ref5050.pdf` URL it recorded is genuinely dead (404, not a proxy failure) |
| 14 | `0004:513` "the REF5050 and OPA2197 hold regulation to ~7.2 V" | **CONSISTENT** | REF5050 needs ≥ 5.73 V worst case; OPA2197 needs ≥ 4.5 V single supply. 7.2 V clears both |
| 15 | `0003:123` "ratiometric behaviour, so nothing downstream changes: the REF5050 supply …" | **NOT ASSESSED** | architectural, not a datasheet claim |

---

# 3. Summary for the lead — what must change

**Loudest first.**

1. **`REF5050AIDR` is the ±0.1 % / 8 ppm/°C Standard grade.** `bom.csv:26`,
   `0003:472` and `bom.csv:27` all state ±0.05 % / 3 ppm/°C. Either the part number
   changes to `REF5050IDR` or the breath scale-factor budget absorbs ~2.7× more
   error. **Three files carry the number.**
2. **OPA2197 `ZO = 375 Ω typ` (SBOS737C §6.7 p.8), not 75.8 Ω.** The repo's poles
   move from 21 kHz → **4.24 kHz** and 200 Hz → **42 Hz**. The instability is real
   and worse; `R-ISO-REF = 10 Ω` is under TI's own worked **37.4 Ω** for a 10 µF
   reference-buffer load (§8.2.3 p.30, Figure 56, with RF 1 MΩ / RFx 10 kΩ / CF 39 nF,
   89° PM, 4 kHz BW). TI says explicitly: "Any other load capacitances require
   recalculation".
3. **The ⚠ block at `carrier.md:248-269` is wrong and should come down.** 1 nF **is**
   an OPA2197 figure — p.1 Features, p.1 Description, and §7.3.5 p.22 ("directly
   drives up to 1 nF of pure capacitive load", unity gain). Per CLAUDE.md's rule on
   verifying findings, a disputed-but-correct figure is the dangerous kind.
4. **`C-REF-OUT` needs a series ESR resistor (~1–1.5 Ω) on the output one**, and the
   BOM is missing the **1 µF on TRIM/NR** and the **parallel HF 1 µF at VOUT**.
5. **`C-REF-OUT`'s node is contradictory across three files** — buffer input in
   `carrier.md:164-166`, buffer output in `bom.csv:27` and
   `breath-receive-stage.md:341`. Semantic; no grep finds it.
6. **`PSRR 114 dB` is unsourced** (`figures.yaml:217`, `power-entry.md:77`,
   `0006:634`). SBOS737C gives ±1 µV/V typ / ±3 µV/V max = **120 dB typ / 110.5 dB
   worst case**. Conclusion unaffected; provenance is not.
7. **Two MANIFEST rows flip from BLOCKED to OK**, and the REF5050 source URL must
   change — `ti.com/lit/ds/symlink/ref5050.pdf` is a **real 404**, not a proxy
   failure. Use `https://www.ti.com/lit/ds/sbos410/sbos410.pdf`.
8. **Lower-priority wording:** `0003:504` "within ~30 mV of ground" is the *no-load*
   number; with a 10 kΩ load the max is 125 mV. `0003:472` "7–18 V in" is safe but
   not a datasheet figure (5.2 V unloaded / ~5.73 V at 10 mA, 125 °C).

# 4. What I did NOT verify

- I did not open TI's OPAx197 SPICE macromodel. Per CLAUDE.md §3, the banked
  datasheet wins; the macromodel is now redundant for `ZO`.
- I did not check SBOS410 revisions **before O** to see whether the `A` suffix once
  meant the *high* grade. Rev O's Table 4-2 is **new in rev O** (§11), so an older
  repo belief could have a different origin. **I am reporting only what rev O says
  and am not speculating about earlier revs.** If the lead wants that resolved, it
  needs rev M or N fetched.
- Figure digitisation is ±2 % on Figure 26 (validated against TI's own 375 Ω) and
  ±2 percentage points on Figures 47/48 and 6-6. Tabulated values are exact.
- Nothing in `docs/review/`, `docs/log/` or `docs/research/` was read or assessed —
  historical record, excluded by CLAUDE.md.
