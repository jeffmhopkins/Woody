# V3 — Provenance audit of the 2026-09-20 cold review

Falsification pass over every load-bearing component specification asserted in
`docs/review/2026-09-20-cold-review/`, `hardware/bom.csv` and `docs/decisions/`.
No repository file was modified.

## What is actually reachable from this sandbox

I probed the egress policy rather than assuming it. Reachable: `github.com`,
`api.github.com`, `raw.githubusercontent.com`, `codeload.github.com`,
`gitlab.com`, `bitbucket.org`, and the `WebSearch` tool (which returns
summarised page *content*, not just titles, and repeatedly surfaced verbatim
datasheet table rows).

Blocked for direct fetch: `ti.com`, `analog.com`, `nxp.com`, `st.com`,
`recom-power.com`, `littelfuse.com`, `neutrik.com`, `gateron.com`,
`digikey.com`, `mouser.com`, `datasheet.octopart.com`, `alldatasheet.com`,
`datasheet.lcsc.com`, `datasheet4u.com`, `pdf.datasheet.live`,
`web.archive.org`, `r.jina.ai`. WebFetch returns `EGRESS_BLOCKED` for all of
them, so no vendor PDF was opened in this session either.

**Consequence for grading.** Nothing below is graded CONFIRMED on the strength
of my own memory. CONFIRMED means either (a) a search result reproduced the
datasheet's own wording/table row, ideally from two or more independent hosts,
or (b) I read primary-adjacent source code or vendor-transcribed geometry on
GitHub. Where only one secondary host carried a figure I say so.

The three highest-value routes that the review's agents did not use:

- **GitHub source as a datasheet proxy.** `ostenning/dac8568` (Rust driver)
  encodes the DAC8568's 32-bit shift-register layout and its full command table
  and quotes datasheet §8.2.10 verbatim. CircuitPython's
  `ports/espressif/boards/waveshare_esp32_s3_matrix/pins.c` is the authoritative
  pin list for `U-MCU-RT`.
- **GitHub code search for vendor drawings transcribed by other builders.**
  `salazarr-js/pocket-groovebox` carries a dimensioned transcription of the
  Gateron Low Profile drawing plus the direct link to Gateron's own STEP file —
  which resolves the review's declared blocking item.
- **Asking search for the specific table row** rather than the part number.
  Queries phrased as the row ("absolute maximum ratings IN voltage",
  "Voffset minimum 0.152") returned the values; queries phrased as the part
  returned distributor noise.

---

## Table 1 — Showstopper- and Major-class claims

| # | Claim as stated | Asserted by | What it is used to prove | Route reached | Verdict |
|---|---|---|---|---|---|
| 1 | TPS2553 input range **2.5–6.5 V**, absolute max IN **−0.3 to 7 V** | README S1, B5 §prov+F1, B6, C1 F1, C4 #1 | **S1** — the load switch is destroyed on first power-on; blocks the module PCB; four decisions across ADR 0004/0005/0014 | TI datasheet text via search summary; independently echoed by two datasheet-mirror hosts | **CONFIRMED** — and the abs-max figure (7 V, which no agent obtained) makes it worse, not better: 12 V is 1.7× abs max, not merely outside recommended |
| 2 | LT1641-2CS8 is the **latch-off** variant; SO-8; 9–80 V | README S1; C1 F1 ("Choose the `-2` (latch-off) variant") | The proposed **replacement** for the TPS2553 — the whole S1 remedy | ADI product pages + three distributor listings via search | **CONTRADICTED.** SO-8 and 9–80 V are right. The suffixes are **inverted**: LT1641-**1** latches off, LT1641-**2** auto-retries after a time-out. The recommended part delivers the exact behaviour the review says must be avoided |
| 3 | MPXV4006DP sits at **+0.2 V at zero pressure by design**; transfer function `Vout = VS(0.1533·P + 0.04)`; Voff **0.152 / – / 0.378 V**; VFSS 4.6 V; 766 mV/kPa | README S2, B2 §prov, B8, C1 | **S2** — the ambient-zero injection has the wrong polarity; a DAC channel spanning 0–5 V cannot null a positive offset | NXP/Freescale MPXV4006 datasheet rows via search summary, two hosts | **CONFIRMED**, and the finding is understated: the spec limit is **0.378 V max**, not 0.2 V, so the required negative REF is up to −0.80 V at G≈2.13, not −0.43 V |
| 4 | MPXV4006DP is **8-SOP surface mount**, case 1351-01 — not THT | README "errors of my own", C1 F-list | Breaks ADR 0003's socketed-wear-part plan; `SKT-BREATH` cannot exist | Distributor package descriptors ("SENSOR PRESSURE DUAL SMD 8-SOP") + case-1351-01 confirmation | **CONFIRMED** — BOM package field is wrong |
| 5 | MPXV4006DP lifecycle **Active/Production, NXP, supported ≥2028** | C4 §verified, BOM ADR 0003 | The DP-not-GP decision, called "the best decision in the BOM" | NXP part page + Octopart lifecycle field via search | **CONFIRMED** |
| 6 | DAC8568 **A/C reset to zero scale, B/D to midscale** | README, B4 §prov, C1, C4, A3 | **S4**, the `U-WATCHDOG` `CLR` safe-state argument, the whole grade decision | TI datasheet text ("For grades A and C, the OTP memory contains all zeroes…") via search; corroborated by the TI E2E CLR thread | **CONFIRMED** |
| 7 | The grade letter **also sets the internal reference gain**: gain 1 for A/B, gain 2 for C/D → an A-grade part **halves every span** | README "errors of my own"; B4 §prov `[VERIFIED]` | Kills "(or A grade)" in the BOM; without it, A-grade substitution silently halves pitch and all four mod spans | TI datasheet text: *"grades A and B, external VREFIN(max) ≤ AVDD; grades C and D, VREFIN(max) ≤ AVDD/2"*, plus "full-scale output voltage range of 2.5 V or 5 V" | **CONFIRMED.** This is the single most consequential figure in the review and it holds |
| 8 | DAC8568 internal reference is **2.5 V and disabled by default**; 32-bit frame; clear-code register must be written; software reset exists | B4 §prov, C5 (`[from memory]` for the frame length), BOM | S4's "shared state must be made stateless"; the boot sequence | **Source code**: `ostenning/dac8568` `src/lib.rs` — *"The input shift register of the DAC7568, DAC8168, and DAC8568 is 32 bits wide"*, `get_internal_reference_message` ("switching DAC8568 from its default state using an external reference"), `WriteToClearCodeRegister`, `SoftwareReset` | **CONFIRMED**, including the frame length C5 flagged as memory-only |
| 9 | DAC8568 recommended **AVDD max 5.5 V** | README S5, C1 F3, C2, BOM `R-REG-SET` | **S5** — the ceiling the LM317 stack overruns | TI datasheet ("AVDD = 2.7 V to 5.5 V") via search | **CONFIRMED** |
| 10 | LM317L **V_ref 1.20–1.30 V**, **I_ADJ ≤ 100 µA**, ±1 % divider → worst case **5.622 V** | README S5, B5 §5, C1 F3, C2 | **S5** — no nominal divider value fits the 4.95–5.50 V window | TI/onsemi LM317(L) datasheet rows via search; I re-derived all three numbers (4.964 / 5.250 / 5.622) and they reproduce exactly | **CONFIRMED** — arithmetic and inputs both |
| 11 | `U-TVS-UMB` SP3012-06UTG: **V_RWM 5.0 V**, **uDFN-14** (not SOT-23-6), **discontinued** | README S6 `[agent]`, B6 §finding (marked `[memory, not verified]`), C1 F2 | **S6** — conducts continuously on +12 V, destroys itself inside the bonded body; BOM package field wrong | Littelfuse SP3012 series datasheet + Octopart lifecycle field via search | **CONFIRMED on all three counts.** S6 should be promoted from `[agent]` to verified; B6's own `[memory]` hedge was unnecessary |
| 12 | In-amp gain equations: **INA821 `G = 1 + 49.4 k/R_G`** (two internal 24.7 kΩ), **INA828 `G = 1 + 50 k/R_G`** (two internal 25 kΩ); an in-amp is unity gain with no R_G | **M3**; A3, B9 §591, C1 F, C2, C4 #21 (`[MEM]` for the numerators) | **M3** — the breath receiver has a gain of 1 as specified; the "INA821 or INA828" ambiguity blocks the resistor value | TI datasheet text for both parts via search, each naming the internal resistor pair | **CONFIRMED.** The `[MEM]` flag in C4 can be lifted |
| 13 | INA821/828 **internal difference-amp resistors ≈ 10 kΩ**, REF referred through them | B2 §prov, explicitly **"From memory"**, and B2 Finding 7 scales linearly with it | The REF-drive impedance argument, and the CMRR cost of a resistive REF source | INA821 internal block schematic reproduced in a search result: `10 k · 24.7 k · 10 k · 10 k · 10 k · 24.7 k`; plus explicit statement "the INA821 has internal 10-kΩ resistors at the reference pin" | **CONFIRMED for INA821.** Not established for INA828 — if INA828 is chosen, B2 Finding 7's arithmetic must be re-checked |
| 14 | **R-78E5.0-1.0 switches at 330 kHz**, not 496 kHz | README "errors of my own", B5 §prov, B6 §547 | Deletes the 496 kHz figure from ADR 0003 and the BOM; changes the aliasing argument for `C-AA-ADC` | Recom R-78E-1.0 datasheet row ("330 kHz at Vin = 12 VDC") via search | **CONFIRMED** |
| 15 | **R-78E5.0-1.0 minimum input is 8 V** | B6 §405 marked `[verified — R-78E-1.0 input range is 8–28 V]`; inherited by README **W13** and **S7** ("its 8 V UVLO") | W13's "1.2 V brown-out window where breath stays live"; S7's "the limiter may prevent boot" | Recom datasheet row: **"Input Voltage Range 7 – 28 VDC"** — and B5 §prov and C2 §1107 both say 7 V | **CONTRADICTED.** Two agents said 7 V, one said 8 V, and the register propagated the 8 V. Both findings survive directionally (the true window, 7.0 V down to the REF5050's 5.2 V dropout, is **wider**, not narrower) but every number quoted in W13 is wrong |
| 16 | REF5050 **minimum V_IN 5.2 V**, I_q 1 mA typ / 1.2 mA max | B6 §406, §0.1 `[verified]` | W13's "breath stays alive while everything else parks" | TI REF50xx datasheet rows via search | **CONFIRMED** |
| 17 | OPA2197 drives **up to 1 nF** of capacitive load | B6 §5 `[verified this session]`, B1 §672 `[from memory]` | The reference buffer driving 100 nF of sensor decoupling directly is outside the rating | TI OPA197/OPA2197 datasheet feature line ("high capacitive load drive of up to 1 nF") plus the R_ISO application note text | **CONFIRMED** |
| 18 | WS2815 logic threshold is **V_IH ≈ 3.5 V** referred to an internal 5 V rail, not 0.7 × 12 V = 8.4 V | README "Agent-versus-agent conflicts: **Resolved**"; B6 §9, C1, C4 — **against C3 §11**, which says 8.4 V and marks the 74AHCT125 CHANGE (probable) | Whether `U-LVLSHIFT` works at all; ADR 0014's open item | Worldsemi WS2815 datasheet via three mirrors. The table's test condition reads **VDD = 4.5–5.5 V** while the supply row reads **9.5–13.5 V**; an independent row gives **"logical input voltage VI: 3.7–5.3 V"**. Worldsemi are reported to have acknowledged the 4.5–5.5 V entry as an error "to be fixed" — without stating which way | **SUSPICIOUS (conclusion right, evidence overstated).** The `VI 3.7–5.3 V` row and universal field practice do support the 5 V shifter, so the design decision is safe. But the primary datasheet is self-contradictory on exactly this row, C3's 8.4 V is a defensible reading of the same table, and the register's "a datasheet check agree" wording claims a resolution the source does not deliver. Keep ADR 0014's verification item open until a strip is on the bench |
| 19 | WS2815 quiescent **< 2.1 mA per LED**; PWM refresh ~2 kHz | B5 §prov, B6 §0.1, B7, B8 | The 105 mA strip-quiescent line in every rebuilt load table (**S7**); the 2 kHz modulation spectrum behind **W4** | Worldsemi datasheet via search summary, two hosts | **CONFIRMED** (secondary sources only; no primary PDF reachable) |
| 20 | etherCON D-series **max panel thickness 4 mm**; ADR 0009 mounts it through 6 mm oak | **W9**, C3 §table and §396 "*Verified (secondary)*" | W9 — the connector cannot mount as specified at the instrument end | Neutrik NE8FDP product page text via search | **CONFIRMED** |
| 21 | NE8FDX-P6 **does not mate** with the NE8MC6-MO carrier | W9 "Intermate trap"; C3 | Both ends must be chosen as a family; breaks the E12/M7 split | Neutrik product pages + B&H/retailer compatibility notes | **CONFIRMED** |
| 22 | etherCON panel cutout **23.8 mm**, leaving 3.19 mm of panel each side of a 30.18 mm 6HP panel | BOM `J-UMBILICAL`, A3 §739, A1 §545, C3, README W9 | The "brace it to the PCB" requirement and the E12 done-when text | Split sources: Neutrik's own D-series material is quoted as a **24 mm** cutout; one secondary source says 23.8 mm | **SUSPICIOUS (precision).** 3.19 mm is quoted to three significant figures off a disputed input; at 24.0 mm it is 3.09 mm. The stiffness conclusion is unaffected, but the number should stop being repeated as exact |
| 23 | ESP32-S3-Matrix breaks out **16 GPIO** (1–7, 34–40, 43, 44) | `hardware/bom.csv` `U-MCU-RT`; A3 §249. README already self-corrects to 17 | The GPIO budget (14 needed), and whether anything is spare | **Source code**: CircuitPython `waveshare_esp32_s3_matrix/pins.c` — header pins are GPIO **1–7, 33–40, 43, 44 = 17**; GPIO14 is the onboard matrix; GPIO11/12/10/13 are the IMU and appear **only** as `IMU_*`, never on a header | **CONFIRMED (README right, BOM and A3 wrong).** The same file independently confirms two other claims: the BOM's IMU pinout (SDA 11 / SCL 12 / INT1 10 / INT2 13) is **correct**, and **W10's "the IMU's I2C is never broken out, E3 is unperformable" is correct** |
| 24 | ESP32-S3's USB PHY routes to **either** USB-Serial-JTAG **or** USB-OTG, never both — C5 calls this "the single most load-bearing memory-sourced claim in this review" | C5 §1018 `[from memory]`; **W10** | W10 — "neither board can be forced into bootloader mode once bonded; one bad image ends the instrument" | Espressif ESP-IoT-Solution / ESP-IDF documentation via search: one internal PHY, defaults to USB-Serial-JTAG, switches to OTG when TinyUSB initialises, external PHY required for both | **CONFIRMED** as a mechanism. But W10's conclusion is **overstated**: the PHY reverts to USB-Serial-JTAG in ROM on every reset, so a (narrow, repeatable) recovery window exists at each power cycle. "One bad image ends the instrument" is only true if the app claims OTG faster than the host can enumerate |
| 25 | QMI8658C carries a **die-temperature register** on the bus already in use | README "Diagnostics"; three agents independently | The proposed free thermal closure — the only temperature sensor anywhere in the design | QST QMI8658C datasheet: TEMP_L/TEMP_H at **0x33/0x34**, two's complement | **CONFIRMED** |
| 26 | Gateron KS-33: 12.2 mm tall, 1.70 mm pretravel, 3.00 mm travel, **14.0 × 14.0 mm cutout**, and the plate thickness is the gating unknown (`gateron.com` blocked) | BOM `SW1-n`/`PLATE-TOP`, `docs/reference/ks33-geometry.md`, C3, C4 §154/§320/§332 | `PLATE-TOP` thickness, which C4 says gates **five** mechanical line items and one cutting order | **GitHub**: `salazarr-js/pocket-groovebox/docs/hardware/modules/gateron-ks-33.md`, a transcription of the Gateron Low Profile dimensional drawing cross-checked against vernier measurement, plus a direct link to Gateron's own `.stp` | **CONFIRMED and the open item is resolvable now.** Plate cutout **14.00 ±0.03 mm**; **plate thickness (the dimension the clip engages) 1.20 ±0.05 mm**; overall height ~12.15 mm; travel 1.7 / 3.0 mm. So 2 mm and the 1.5 mm MX standard both exceed the clip window; the repo's 1.1 mm STL-derived figure was close but low. A second, independent repo states the same 1.2 mm |

---

## Table 2 — Supporting specifications

| # | Claim | Asserted by | Depends on it | Verdict |
|---|---|---|---|---|
| 27 | DAC8568 digital **V_IH = 0.625 × AVDD**, not 0.7 × AVDD | B5 §prov, against **ADR 0004** | Whether the 74AHCT125 level shifter to the DAC is needed at all, and its margin | **CONFIRMED** (TI: "When supplied with 5 V, VIH is 0.625 × AVDD (3.125 V) … to allow 3.3 V logic without translators"). ADR 0004 is wrong; B5 is right |
| 28 | LM317L **minimum load 3.5 mA**, satisfied by the 240 Ω leg at 5.2 mA | B5 §7 ("satisfies the minimum-load requirement"), C2 §314, C1 §213 (proposes 120 Ω → 10.4 mA) | Three separate "this part of ADR 0004 is fine" confirmations | **CONTRADICTED.** The datasheet figure is **3.5 mA typical, 12 mA maximum**. Both the existing 5.2 mA and C1's proposed 10.4 mA fail the guaranteed spec. Every "minimum load is satisfied" line in the review used the typ column |
| 29 | 1206 500 mA PPTC **R_initial ≈ 0.3–0.9 Ω**, 0.5 A hold / 1.0 A trip | B5 §prov, explicitly **"From memory"**; feeds **S7**'s "0.11–0.44 V drop, ~0.26 W, largest resistance in the 12 V path" | S7's case for deleting the polyfuse | Hold/trip **CONFIRMED** (1206L050: 0.5 A / 1.0 A). Resistance **partly CONTRADICTED**: Littelfuse gives R_min 0.150 Ω, R1max 0.750 Ω. S7's drop and dissipation are overstated by roughly 1.5–2×: ~0.075–0.375 V and ~0.04–0.19 W. The recommendation survives on the other three grounds (derating, position downstream of the switch, cannot trip cleanly behind a fast limiter) |
| 30 | LT5400 offers a **1:4 ratio directly**, so the mod gain of 4 is buildable from one network | ADR 0006 (quoted in A3 §125); endorsed by C4 §119 as "good news" | **M2** — the mod channels' gain network; the choice between 4 × LT5400 and 16 discretes | **SUSPICIOUS, leaning CONTRADICTED.** Every reachable description of the family gives ratios of **1:1 and 10:1** (quad 10 k, quad 100 k, dual 10 k / dual 100 k). No 1:4 variant surfaced. C4 correctly flagged the variant table as unread; ADR 0006 did not |
| 31 | LT5400 matching drift 0.2 ppm/°C typ, 1 ppm/°C max; guaranteed matching 0.01 % | B3 §prov "web-verified"; C2 §52 | The "LT5400 is 20–30× over-specified, drop it" recommendation | **CONFIRMED** (ADI product material: 0.01 % matching −40 to +85 °C, 0.2 ppm/°C matching drift). The separate "**absolute** TC 8 ppm/°C" figure is **UNVERIFIABLE-FROM-HERE** |
| 32 | BAT54S leakage ~2 µA → 2 mV → 2.4 cents; BAV99 ~100 nA → 0.12 cents | ADR 0006 / BOM `D-JACK-CLAMP`; re-derived by B5, B9, C1, C2 | "BAV99-over-BAT54S re-derives exactly" in the confirmations list | **CONFIRMED** — both leakage figures are the standard datasheet maxima for those parts |
| 33 | 1N5817 V_F ≈ 0.33–0.40 V at 0.5 A (max 0.45 V at 1 A); dynamic resistance ~0.3 Ω | B5 §prov and B3 §prov, both **"From memory"**; the ~80 mV V_F modulation is the **second-largest term in W4**, the most-converged finding in the review | W4 — "blow harder, the pitch bends", ~20 cents | **CONFIRMED for V_F** (0.2–0.45 V range, 0.45 V max at 1 A, DO-41, across four vendor datasheets). The **dynamic resistance** is consistent with that curve but was not read off one — the 80 mV and therefore the 20 cents rest on an inferred slope |
| 34 | MCP3202: 50 ksps at 3.3 V, one spare channel | BOM; C5 §1017 `[from memory]` f_CLK ≈ 1.1 MHz, 55–65 ksps | The 4–8 kHz sampling requirement — nothing marginal | **CONFIRMED enough.** Datasheet is 100 ksps at 5 V / 50 ksps at 2.7 V with f_CLK = 18 × f_SAMPLE; the BOM's "50 ksps at 3V3" is conservative |
| 35 | 74HC123 pulse width `t ≈ 0.45 · R · C`; 1 MΩ × 220 nF ≈ 99 ms | A3 §160–168 | The watchdog's N, which **M4** says is undefined because the R/C pair has no BOM row | **CONFIRMED** as the standard 74HC123 formula; the arithmetic checks (0.45 × 1e6 × 220e-9 = 99 ms) |
| 36 | ESP32-S3FH4R2 carries **quad** PSRAM; octal would consume GPIO33–37 | BOM `U-MCU-RT` ("confirm quad at E1"); C5 §1021 `[from memory, high confidence]` | Whether the 17-GPIO budget is real | **CONFIRMED by construction.** GPIO33–40 are all on the headers in the CircuitPython board file, which is impossible with octal PSRAM; and Espressif's suffix convention makes `R2` = 2 MB quad. The E1 item is answerable without a bench |
| 37 | TPS2592Ax is VSON-10; TPS27S100 is HTSSOP PowerPAD — so every one-chip 12 V eFuse fails the package policy | README S1, C1 F1 table | Why S1 is "a design decision, not a substitution" | **CONFIRMED for TPS2592** (10-VSON 3×3, 4.5–18 V). TPS27S100's package **UNVERIFIABLE-FROM-HERE** |
| 38 | PJ398SM active, interchangeable with PJ301M-12 / WQP518MA | C4 §96, §183 `[VERIFIED]` | Nothing structural | **CONFIRMED** (secondary) |

---

## Falsifications — what this pass changed

Five claims did not survive, and three of the five are load-bearing.

1. **The LT1641 suffix is inverted (Table 1 #2).** `LT1641-1` = latch-off,
   `LT1641-2` = auto-retry. C1 F1 lists them backwards in a table *and* in a
   bolded instruction — "**Choose the `-2` (latch-off) variant**" — and README S1
   propagated `LT1641-2CS8 … latch-off` into the register. Ordering the part as
   written buys auto-retry into a persistent fault, which is the precise
   behaviour C1 argues against two sentences later by reference to ADR 0014's
   oscillating-protection analysis. This is the only error in the audit that
   would be soldered onto a board and then behave wrongly rather than merely
   be miscalculated.

2. **The R-78E5.0-1.0's minimum input is 7 V, not 8 V (Table 1 #15).** Two
   agents (B5, C2) had 7 V; B6 had 8 V and tagged it `[verified]`; the register
   propagated B6's number into **W13** and **S7**. W13's entire brown-out table
   (8.0 V / 7.2 V / "a 1.2 V window") is built on it, and S7's
   "the limiter may prevent boot … the buck never reaches its 8 V UVLO" inherits
   it too. Both findings survive — the real window, 7.0 V down to the REF5050's
   confirmed 5.2 V dropout, is *wider* — but this is a clean instance of the
   review's own Pattern 4, with the further twist that the disagreement was
   already visible inside the document set and nobody reconciled it.

3. **The LM317L minimum-load check used the typical column (Table 2 #28).**
   Three documents certify that the 240 Ω leg's 5.2 mA "satisfies" the LM317L's
   minimum load. The spec is 3.5 mA **typ / 12 mA max**. C1's remedy (120 Ω,
   10.4 mA) also fails the max. Since S5 already recommends deleting the LM317
   in favour of a second REF5050, this is mostly further evidence for a
   conclusion already reached — but it means "the divider satisfies the minimum
   load" must not be carried forward as a confirmed-good in the register's
   "what the review confirmed as right" section.

4. **The LT5400 1:4 ratio is not established (Table 2 #30).** ADR 0006 asserts
   it as fact; C4 endorses it; every reachable description of the family gives
   1:1 and 10:1 only. **M2** turns on whether the mod gain network is one part or
   sixteen discretes.

5. **S7's polyfuse resistance is ~2× high (Table 2 #29).** Real 0.150–0.750 Ω
   against the asserted 0.3–0.9 Ω, and B5 flagged it as memory at the time.

Two findings should be **upgraded**:

- **S6** (`U-TVS-UMB`) is marked `[agent]` in the register and hedged as
  `[memory, not verified]` in B6. All three of its factual legs — V_RWM 5.0 V,
  uDFN-14 package, obsolete lifecycle — are confirmed. It is not a hypothesis.
- **S2**'s magnitude is understated. The sensor's zero-pressure output is
  specified 0.152–0.378 V, not a nominal 0.2 V, so the negative REF authority
  the fix needs is up to ~0.80 V at the jack, not 0.43 V.

And one item the review lists as **blocked** is not: the Gateron KS-33 plate
thickness is **1.20 ±0.05 mm** (Table 1 #26), obtained from a vendor-drawing
transcription plus Gateron's own STEP link, both on GitHub. C4 says this single
dimension holds up five line items, one cutting order and two milestones.

---

## Load-bearing AND unverified, ranked by what reverses if wrong

Ranked by the size of the decision that moves, not by how likely the figure is
to be wrong.

**1. The etherCON D-series body depth behind the panel (30–40 mm).**
C3 marks it *UNOBTAINED* and W9 nonetheless concludes from it that the module
**must become a two-board design** — "clearing it needs a ~26 mm notch in a
≤28 mm board, which severs it". If the real depth is at the low end, or if a
PCB-mount variant is chosen (C3's own table puts `NE8FDV` at 24 mm behind the
panel), the one-board module may survive and E12's done-when text stands. This
is the largest mechanical decision in the review resting on a number nobody
obtained, and it feeds the M3 layout-lock deadline the register itself calls the
real one. *No route from here; neutrik.com is blocked and no third party carries
the depth dimension.*

**2. The LT1641 variant (falsified above, ranked here because it is actionable).**
Not unverified — wrong. Correct the register and C1 to `LT1641-1CS8` before
anyone orders, and re-read the surrounding paragraph, because the reasoning is
right and only the part number contradicts it.

**3. The WS2815 logic threshold (Table 1 #18).**
The register declares this **Resolved** and closes an ADR 0014 open item on the
strength of it. The primary datasheet is genuinely self-contradictory on that
row and the vendor is reported to have acknowledged the row as an error without
saying which direction it is wrong in. If C3's 8.4 V reading is the correct one,
`U-LVLSHIFT` is the wrong part, a 12 V gate driver is required, and a component
that the register lists under "what the review confirmed as right" becomes a
build-stopper. The practical evidence (the `VI 3.7–5.3 V` row; universal use of
AHCT with WS2815) is strong, so I do not expect a reversal — but "resolved" is
not the right word, and the one-line bench test (drive a single pixel from a
3.3 V GPIO and from an AHCT output, at the end of a 420 mm run) is cheap.

**4. `MPXV4006` accuracy ±2.46 % FSS with auto-zero (B2, "the single most
load-bearing number in this review" by its own account).**
I confirmed the figure and the auto-zero condition. What I could **not** confirm
is the un-auto-zeroed ±5.0 % figure or the temperature-coefficient breakdown
behind it. B2's entire error budget, and **W11**'s argument that the continuous
auto-zero conceals the three failures the DP decision depends on seeing, scale
with that split. *Route: the NXP datasheet's accuracy table; blocked.*

**5. The LT5400 variant table, including whether `LT5400-7` builds the pitch
ratio (Table 2 #30).**
Drives **M2** (one part or sixteen discretes for the mod gain network) and the
"9/5 is not constructible" resolution that the register lists as dissolved. C4
flagged it; ADR 0006 asserted it. *Route: analog.com ordering table; blocked.*

**6. The 1N5817 dynamic resistance behind W4's ~80 mV / ~20 cents (Table 2 #33).**
W4 is the review's most-converged finding and this is its second-largest term.
The forward-voltage curve is confirmed; the slope taken off it is not. If the
real slope is half the assumed 0.3 Ω, this mechanism drops below the offset-rail
term and the "four routes that add" framing weakens to "one route plus noise".
Cheap to settle on the bench — it is a two-point DMM measurement.

**7. The 1206 PPTC hold-current derating at the documented interior rise
(~×0.7 at 50 °C).**
Flagged `[from memory]` by B5. **S7** uses it to claim the polyfuse "derates to
~300–400 mA hold", which is one of the four legs of "delete it outright" and
also one of the two devices S7 says are set below the design's own worst case.
The 0.5 A / 1.0 A points are confirmed; the curve is not. *Route: the Littelfuse
1206L datasheet derating graph; blocked.*

**8. TPS2553 NRND status, and DAC8568 A/C-grade stock.**
C4 ranks the DAC8568 grade as the thinnest-stock line in the BOM and recommends
buying ahead of need. Both are commercial facts, both were taken from single
search summaries, and C4 itself says to re-check them "before money moves". I
could not improve on that from here.

**9. OPA2197 PSRR-vs-frequency and open-loop output impedance.**
B5, B8 and B9 all use `[from memory]` values (≈100 dB at 2 kHz; R_o ≈ 100 Ω).
Each author argues their conclusion survives a 20 dB or 2× error, and I agree —
W3's "86 dB off the right node" is an argument about *topology*, not about the
exact PSRR. Low reversal risk, listed for completeness.

**10. INA828's internal difference-amp resistor value (Table 1 #13).**
Confirmed 10 kΩ for the INA821 only. If the "INA821 or INA828" ambiguity that
**M3** blocks on resolves toward the INA828, B2 Finding 7's REF-impedance
arithmetic needs re-running against a value nobody has.

---

## Two process observations

**The review's honesty markers are well calibrated but asymmetric.** Every claim
tagged `[from memory]` that I could check turned out to be either right (INA821's
10 kΩ, the 1N5817 forward drop, the 32-bit DAC frame, the ESP32-S3 PHY mux, the
octal-PSRAM pin conflict) or wrong in a direction that does not reverse the
finding (the PPTC resistance). Every claim I found *actually wrong* was tagged
**`[verified]`**: the 8 V buck minimum, the LT1641 suffixes, the LM317 minimum
load, ADR 0006's 1:4 LT5400 ratio. The hedges were applied to recollection, not
to the confidence of the retrieval — a figure pulled from a search summary and a
figure read off a datasheet were both marked "verified".

**Three of the five falsifications were visible inside the document set.** The
7 V/8 V split, the LT1641 suffix labels contradicting the sentence that follows
them, and the typ-vs-max minimum-load column were all detectable without any
network access at all. The review collapsed duplicate *findings* against each
other; it did not cross-check duplicate *figures*.
