# C4 — Sourcing risk review

**Scope:** every line item in `hardware/bom.csv` (58 rows, 4 of them `not-needed`),
assessed for lifecycle, single-source exposure, availability, spares policy,
substitution safety and counterfeit exposure. Plus a practical read on the total
order.

**Design context taken as given:** one-off, no volume, no cost-down, built once,
played for years, **body bonded shut and never reopened** (ADR 0009). Cost only
matters where it buys insurance. Schedule matters where a part could vanish
before the build finishes.

---

## Verification status — read this first

| | |
|---|---|
| **Verified online this session** | MPXV4006DP lifecycle; DAC8568 grade/reset behaviour and orderable P/Ns; TPS2553 input voltage range; SP3012-06UTG lifecycle; LM317LZ lifecycle; R-78E5.0-1.0 availability; OPA2197IDR status; INA821/INA828 status; 74HC123 Nexperia-vs-TI status; WS2815 logic thresholds; LT5400 variant ratios (partial); PJ398SM interchangeability; Gateron KS-33 2.0/3.0 line status; MT165-MX vendors; LilyGO and Waveshare board availability; Neutrik anti-counterfeit measures; MPX-family counterfeiting |
| **Fetch blocked by this sandbox's egress proxy** | `ti.com`, `analog.com`, `digikey.com`, `mouser.com`, `littelfuse.com`, `alldatasheet.com`, `datasheet.octopart.com`. Also `gateron.com` / `gateron.co` (already recorded in `docs/reference/ks33-geometry.md`). **Every claim below that depends on those domains is marked and is second-hand — from search-result summaries, third-party distributor pages, or memory.** None of it is a substitute for pulling the vendor page yourself before ordering. |
| **From memory, not verified** | Anything tagged `[MEM]`. Prices, MOQ behaviour, porous-PTFE supply, keyboard-community counterfeit patterns, Eurorack DIY vendor stock. |
| **From the repository** | Anything tagged `[REPO]`. |

Severity scale: **S1** blocks the build or is unrecoverable once bonded · **S2**
costs a re-order or a board spin · **S3** costs money or annoyance only.

---

## 1. Risk table

| # | Part (`ref`) | Risk type | Sev | Action |
|---|---|---|---|---|
| 1 | `U-LOADSW` TPS2553DBV | **Wrong voltage class** — 2.5–6.5 V part specified on a +12 V feed. Also possibly NRND | **S1** | Respec to a 12 V-capable eFuse (TPS25926/TPS25924/TPS2592A class) **before** the module PCB is laid out. Package and pinout both change |
| 2 | `U-TVS-UMB` SP3012-06UTG | **Obsolete** (mfr discontinued); BOM package is also wrong (UDFN-14, not SOT-23-6) | **S1** | Respec. Pick an in-production 8-line array in a leaded package that satisfies ADR 0013's no-QFN policy |
| 3 | `U-DAC` DAC8568 | **Grade availability** — design requires A or C grade (zero-scale reset). C-grade reel showed out-of-stock/backorder; A-grade visible mainly at brokers | **S1** | Lock the full orderable P/N now, buy from a broad-line distributor, buy a spare in the same order. **Never** accept B or D as a substitute |
| 4 | `U-BREATH` MPXV4006DP | **Entombed wear part, single-source, architecture depends on it**. Lifecycle is fine (Active) | **S1** | Buy 3–4. Recognise spares only help **pre-bond** — see finding 12 |
| 5 | `U-MCU-RT` ESP32-S3-Matrix | **Entombed consumer dev board**, silent revisions (PSRAM quad/octal, matrix face orientation) | **S1** | Buy 2 in one order, same batch. Confirm quad PSRAM at E1 before the carrier is laid out |
| 6 | `U-DISP` T-Display-S3 AMOLED | **Entombed consumer dev board** with a known wear-out mode (AMOLED burn-in); base/Plus and board revisions exist | **S1** | Buy 2 in one order. Confirm it is the **base**, no touch, and note which header variant |
| 7 | `R-PRECISION` LT5400-class | **Part number not yet decided** (`qty TBD`). LT5400 suffix sets the ratio; the pitch ratio question is still live | **S2** | Close the ratio decision, then order the exact suffix + grade. Stock is uneven across suffixes |
| 8 | `J-UMBILICAL` etherCON | **Variant undecided** (feedthrough vs solder-tag) and one end is entombed. Counterfeit Neutrik is documented | **S2** | Decide at E12/M7 as planned; buy 3 (2 build + 1 spare) from an authorised dealer, check the hologram |
| 9 | `LED-SIDE` WS2815 | **Marginal supply channel**; "12 V addressable" is routinely WS2811-based, not WS2815; batch/bin variation | **S2** | Buy ≥2 m from one reputable vendor in one order. Verify per-LED addressing and the backup data line on arrival |
| 10 | `SW1-n` Gateron KS-33 Red 2.0 | **Line being superseded** — KS-33 Low Profile **3.0** now exists. Bought from Amazon (marginal channel for Gateron) | **S2** | Buy 6–10 spares of the **2.0** now, plus the 4 lighter-spring thumb switches if M1 calls for them. Verify the 18 on hand against the published spec |
| 11 | `U-WATCHDOG` 74HC123 | Nexperia variant **discontinued**; TI CD74HC123M active | **S3** | Specify `CD74HC123M` explicitly, not "74HC123" |
| 12 | `U-ADC` MCP3202-CI/SN | Availability wobble (backorder seen at one distributor) | **S3** | Check stock at two broad-line distributors; buy 2. `-CI/P` and `-CI/ST` are the same die in other packages |
| 13 | `U-KEYS` 74LVC165A | **Package risk**: TI's stocked option is TSSOP (0.65 mm); BOM says SOIC-16 | **S2** | Confirm a SOIC-16 (D) orderable exists in stock, or fall back to Nexperia `74HC165D` (SOIC-16, and already blessed as a drop-in by ADR 0001) |
| 14 | `U-LVLSHIFT` / `U-LVL-MOD` 74AHCT125 | Fine on lifecycle. **Substitution trap**: HC/LVC/LV variants silently fail | **S2** | Specify `SN74AHCT125D` or `74AHCT125D`. Buy 4 |
| 15 | `MECH-PTFE` porous PTFE plug | **Genuine MOQ / marginal-supplier line**, entombed, sets the Helmholtz response | **S2** | Identify a source early (PTFE syringe-filter hack is the cheap path `[MEM]`). Do not leave to build day |
| 16 | `CABLE-UMB` Cat5e STP stranded | Easy to get wrong (solid core, Cat6 23AWG solid) | **S3** | Buy 3 × 2 m stranded shielded patch leads. Declared a consumable already |
| 17 | `POT-BREATH` Alpha 9 mm B50k | Footprint/bushing varies between "9 mm vertical" parts; panel is cut once | **S2** | Buy the pots **before** the panel DXF is finalised, and measure |
| 18 | `SW-POWER` sub-mini toggle | 6 mm vs 6.35 mm bushing; one-off panel | **S2** | Same — part in hand before the panel is cut |
| 19 | `D-JACK-CLAMP` BAV99 | Substitution trap (BAT54S) already documented in BOM | **S3** | Keep the note on the schematic symbol, not just the BOM |
| 20 | `U-REF-BREATH` REF5050AIDR | Grade suffix matters (`A` = ±0.05 %); entombed | **S3** | Order the `A` grade explicitly; buy 2 |
| 21 | `U-DIFFRX` INA821 **or** INA828 | Two parts on one line with **different gain equations** | **S2** | Pick one, fix `R_G` to it. Same footprint hides the difference |
| 22 | `U-BUCK` R-78E5.0-**1.0** | 1 A rating already at 1.36 A worst case; `-0.5` variant exists and is fatal | **S2** | Order the `-1.0`. Buy 2. Check the digits on arrival |
| 23 | `PLATE-TOP`, `BODY-OAK`, `SIDE-ACRYLIC`, `PANEL`, `MECH-WINDOW` | **Unquotable** — no thickness, no material spec, no vendor | **S2** | These are the schedule risk, not the semiconductors. See finding 16 |
| 24 | `C-BULK-DISP`, `TUBE`, `MECH-COAT` | `status: open`, no part number | **S3** | Close before the consolidated order |
| 25 | All TI/ADI precision analog | **Counterfeit channel risk** — re-marked grades are undetectable at the bench | **S2** | Broad-line distributors only. No eBay, no AliExpress, no brokers for `U-DAC`, `R-PRECISION`, `U-REF-BREATH`, `U-OPA-*`, `U-DIFFRX` |

---

## 2. Findings

### 2.1 Lifecycle

**1. `U-LOADSW` TPS2553DBV is the wrong voltage class, and this is the single most important finding in the review.**
TI describes the TPS2553 as a *"0.075–1.7 A adjustable current limit, **2.5–6.5 V**, 85 mΩ USB power switch"* — it is a 5 V USB rail part. `[VERIFIED — TI product description via search summary and several distributor descriptions; ti.com itself is blocked from this sandbox so I could not read the absolute-maximum table directly]`
ADR 0004 and ADR 0005 put it on the **umbilical +12 V feed**, downstream of the reverse-polarity diode. That is roughly double its operating maximum and almost certainly over its absolute maximum. The part cannot do the job it is specified for, so this is not a substitution question — the line item has to be replaced before the module schematic is real.

One search summary also reported the TPS2553 as **NRND** at TI. `[UNVERIFIED — single secondary source, contradicted by other distributor pages showing DBVT as active; ti.com blocked]` Treat NRND as unconfirmed; treat the voltage range as confirmed. Either way the replacement path is the same.

**Replacement path:** a 12 V-class eFuse with adjustable current limit and inrush slew control. TI's TPS25926/TPS25925 family is explicitly positioned for 12 V systems, TPS25924 adds reverse-current blocking, TPS1663 is a 60 V part with far more headroom than needed. `[VERIFIED — TI product descriptions via search]` TPS2592A also exists but TI's own page says new designs should consider an alternate, so skip it. `[VERIFIED]`
**Consequences to price in:** different package (most of these are 8–10-pin, not SOT-23-6), different `ILIM` resistor equation, a different `EN` polarity possibly, and ADR 0005's package-policy argument ("SOT-23-6 is coarser than the TSSOP already accepted") has to be re-run against whatever is chosen. This blocks **E6** and the **E12** module PCB.

**2. `U-TVS-UMB` SP3012-06UTG is obsolete, and the package in the BOM is wrong.**
Multiple distributors report the lifecycle as **Obsolete / no longer manufactured** `[VERIFIED — DigiKey/Octopart/Chip1Stop summaries via search; littelfuse.com blocked]`. Separately, the DigiKey description gives the package as **14-UDFN (3.5 × 1.35 mm)**, not the `SOT-23-6 (0.95 mm pitch)` the BOM records `[VERIFIED — same source]`. A UDFN is a leadless package, which ADR 0013's package policy explicitly rules out ("QFN, BGA, leadless — **Avoid**").
So this line is wrong twice: dead part, forbidden package. Because the BOM's stated intent is "multi-line array beats discretes for placement" across 8 umbilical conductors, the replacement wants to be an in-production multi-channel array in a **leaded** package. Candidate families to evaluate: Littelfuse SP3003/SP3051 series, Semtech RClamp series, ST's ESDA-series arrays, ON Semi ESD arrays — several of these ship in SOIC-8/SO-8 or TSSOP `[MEM — needs verification, all the vendor sites I would check are blocked]`. Note this part sits on the **carrier**, i.e. **inside the bonded body**, so it is worth the ten minutes to choose a leaded part rather than a 0.4 mm-pitch one that might lift a pad.

**3. `U-WATCHDOG` "74HC123 or equivalent" — Nexperia's 74HC123 is discontinued, TI's CD74HC123M is active.**
Nexperia's own product page marks the 74HC123/74HCT123 type numbers as discontinued; TI's CD74HC123M is listed ACTIVE; one Nexperia distributor listing showed deliveries starting April 2026. `[VERIFIED — Nexperia page and Newark/Farnell listings via search]`
Low severity — it is a module-side part, replaceable in minutes — but "74HC123 or equivalent" in a BOM is how you end up ordering the discontinued one. **Write `CD74HC123M` in the BOM.**

**4. Everything else with a part number is Active.** Verified this session:

| Part | Status | Source quality |
|---|---|---|
| `MPXV4006DP` | **Active / Production**, NXP support stated through at least 2028 | `[VERIFIED — NXP part page summary, DigiKey, Mouser via search]` |
| `DAC8568` (family) | **Active**, TSSOP-16 PW, A/B/C/D grades orderable | `[VERIFIED — TI packaging addendum referenced, DigiKey listings; ti.com blocked so I could not read the addendum itself]` |
| `OPA2197IDR` | **Active production**, SOIC-8 | `[VERIFIED — TI product page summary, DigiKey, LCSC]` |
| `INA821` / `INA828` | **Active**, SOIC-8 | `[VERIFIED — TI product pages via search]` |
| `REF5050AIDR` | Active `[MEM]` — not separately verified this session | `[MEM]` |
| `LM317LZ` | **Active** at TI *and* onsemi *and* ST; TO-92 | `[VERIFIED — Octopart, allaboutcircuits, RS]` |
| `R-78E5.0-1.0` | **Active**, in stock, ships same day at DigiKey | `[VERIFIED]` |
| `SN74AHCT125` / `74AHCT125D` | Active at TI, Nexperia and Diodes | `[VERIFIED — multiple distributor listings]` |
| `MCP3202-CI/SN` | Active; see finding 9 on stock | `[VERIFIED — microchipdirect, Avnet, Future listings exist]` |
| `LT5400` family | Active | `[VERIFIED — ADI product page, Mouser/DigiKey series pages; analog.com blocked so the variant table is second-hand]` |
| `PJ398SM` | Active, current production, multiple resellers | `[VERIFIED]` |
| `Neutrik NE8FDP` family | Active; `NE8FDX-P6` is a newer Cat6A D-series sibling, **not** a discontinuation notice for NE8FDP | `[VERIFIED — neutrik.com product pages exist for NE8FDP, -B, -SE, -R, -R-B]` |
| `Gateron KS-33 Low Profile 2.0` | Available, but a **3.0** now exists alongside it | `[VERIFIED — gateron.com product pages listed in search results; pages themselves blocked]` |
| `Tai-Hao MT165-MX` | Available from Beekeeb, Tai-Hao's own shop, and small resellers | `[VERIFIED]` |
| `LilyGO T-Display-S3 AMOLED` (base) | Available; wiki updated Aug 2026 | `[VERIFIED]` |
| `Waveshare ESP32-S3-Matrix` | Available, multiple channels, ~€10.50 at one EU reseller | `[VERIFIED]` |

### 2.2 Single-source risk

**5. `U-BREATH` MPXV4006DP — single-source, and the architecture is welded to it.**
This is already the best-documented risk in the repo, and ADR 0003 gets it right: the GP is obsolete and the DP has an identical transfer function and is in production. What ADR 0003 *understates* is that single-source here is not just "one manufacturer" — it is **one part, with no functional equivalent at any price**, because the whole analog-breath decision depends on a fast analog transducer. The review's R2 makes the point precisely: every modern replacement is ASIC-plus-internal-DAC (Honeywell ABP at ~1 kHz, ABP2 at ~200 Hz), and a 200 Hz staircase into a VCA is exactly the artefact the analog path exists to prevent. `[REPO]`
**Nearest alternative and what would have to change:** a raw piezoresistive bridge (MPX2010-class or equivalent) plus an instrumentation amp. That is a *better* topology in some respects now — the in-amp's REF pin already does the zero subtraction, and exciting the bridge from the same reference makes the chain ratiometric by construction. But it costs: a second in-amp in the instrument (currently there is none — the instrument end is a buffer only), a gain stage that has to be set and trimmed inside a sealed body, and it reopens ADR 0003's entire protection-resistor/CMRR argument. **Not a build-day substitution. A redesign.**
**So the action is spares, not alternates.**

**6. `U-DAC` DAC8568 — the *grade* is the single-source risk, not the part.**
Confirmed: **A and C grades reset to zero scale; B and D reset to mid-scale.** `[VERIFIED — TI E2E forum and datasheet references via search]` ADR 0006 requires A or C so that `Vout = 4 × (Vdac − Voffset)` parks the mod channels at exactly 0 V and pitch subsonic, and so that the `U-WATCHDOG` `CLR` assertion parks the rack safely. A B or D part **inverts that entire safety argument**: on reset, pitch parks octaves up and the mod outputs go to a known-but-wrong place.
Orderable numbers visible: `DAC8568IAPW(R)`, `DAC8568IBPW(R)`, `DAC8568ICPW(R)`, `DAC8568IDPW(R)`. `[VERIFIED — DigiKey and TI part-detail URLs in search results]` Stock signal is not reassuring: **`DAC8568ICPWR` showed out-of-stock/backorder**, `DAC8568IBPWR` appeared under *DigiKey Marketplace* (third-party sellers, not DigiKey inventory), and `DAC8568IAPWR` appeared with stock at a broker. `[VERIFIED — search summaries; digikey.com blocked so I could not read live stock]`
**Nearest alternative:** ADR 0006 already names **AD5676** (octal 16-bit SPI). Switching to it changes the SPI command format, the reference architecture (AD5676 has no internal reference in all variants — AD5676**R** does), the supply window, the package (TSSOP-16 vs 20-lead), and the reset-state analysis would have to be redone from scratch. **Not a drop-in.**
**Action: pick the exact P/N, verify stock at two distributors, and buy two.** This is the one part where "I will order it when the board is ready" is a real risk.

**7. `R-PRECISION` LT5400 — single-source *and* not yet specified.**
The BOM says `qty TBD`. That is not a sourcing problem yet; it becomes one the moment the module BOM is frozen, because the LT5400 suffix **is** the resistor ratio and the suffixes do not have uniform stock.
What I could verify: the family comes in several ratio options; the `-7` is **1.25 k / 5 k, a 1:4 ratio**, matching 0.025 % on the B grade, 0.2 ppm/°C matching drift. `-1` (2.5 k/10 k) and `-2` (5 k/20 k) are also 1:4; `-8` is 1:9. `[VERIFIED — Newark listing text and ADI marketing pages via search; analog.com datasheet blocked, so the full variant table is NOT confirmed]`
Note what that means for the design: **the mod-channel gain of 4 is directly buildable** from a 1:4 network, which is good news for ADR 0006's `4 × (Vdac − 2.5 V)` topology. The **pitch** stage is the contested one — the review claimed a 9/5 ratio is unbuildable from a matched quad (R4), and the resolution log says "LT5400-7 builds the required gain exactly" `[REPO]`. I cannot check that claim without the datasheet. **Before ordering: pull the ADI datasheet, confirm the exact suffix for *both* stages, and confirm whether one part or two is needed (`qty TBD` may be 2).**
**Nearest alternative:** Vishay's matched thin-film networks (MPM/ACAS series) or Caddock. Different package, different pinout, different ratio sets — a board change, not a build-day swap.

**8. `J-UMBILICAL` etherCON — effectively single-source (Neutrik owns the standard) and the variant is open.**
ADR 0004 leaves feedthrough (NE8FDP-class) vs solder-tag open until E12/M7. That is a reasonable engineering deferral but it is a **sourcing** deferral too: NE8FDP, NE8FDP-B, NE8FDP-SE, NE8FDP-R, NE8FDP-R-B and the Cat6A NE8FDX-P6 are all real, currently-listed parts with different flange geometry, colour and rear interface `[VERIFIED — neutrik.com product pages returned in search]`. Panel cutouts and PCB bracing depend on which one. Do not cut the 6HP panel or the instrument tail backing plate until the actual connector is on the bench.
**Nearest alternative:** the ADR already evaluated M12 X-coded (ruled out on 0.5 A/contact) and Hirose HR10A (ruled out on cable flex-rating). `[REPO]` Both remain valid fallbacks if the panel fit fails; both change the cable strategy completely.

**9. `U-ADC` MCP3202-CI/SN — one manufacturer, but an easy alternative.**
Microchip is the only source. One distributor showed it **on backorder** with a scheduled ship date `[VERIFIED — RS listing text via search]`, which is a caution rather than a crisis. The `-CI/P` (PDIP-8) and `-CI/ST` (TSSOP-8) variants are the same die in different packages and are separately stocked — a legitimate escape hatch, with PDIP being *easier* to hand-assemble, not harder.
**Nearest functional alternative:** MCP3002 (10-bit) loses resolution the design says it does not need anyway; ADS7886/MAX1178-class SAR parts would work but change the SPI framing and the VDD-referenced behaviour that ADR 0003 relies on (VDD-referenced = no separate reference chip). **Prefer the package swap over the part swap.**

**10. `U-KEYS` 74LVC165A — check the package before you check the stock.**
TI's readily-visible orderable for SN74LVC165A is the **TSSOP (PW)** part `[VERIFIED — TI part-detail URL for SN74LVC165APWR in search results]`. The BOM says **SOIC-16**, and ADR 0013's package policy prefers 1.27 mm pitch. I could not confirm a SOIC-16 (`D`) orderable for the **LVC** version is in stock — searches kept returning the *different* part `SN74LV165AD` (LV, not LVC), which is a 2–5.5 V part, and RS showed it as discontinued-from-stock. `[VERIFIED that the search kept returning LV not LVC; the existence/stock of SN74LVC165AD is UNVERIFIED]`
**This matters more than it looks** because ADR 0001 already blesses the fallback: *"74HC165 is a drop-in on the same SOIC-16 footprint if E4 says otherwise."* Nexperia's **74HC165D** is unambiguously a SOIC-16 part with live distributor listings `[VERIFIED — RS listings]`. And ADR 0001 also records that the LVC-over-HC rationale was backwards, and that HC at 3.3 V would have been the lower-risk choice on signal-integrity grounds.
**Recommendation: lay the carrier out for SOIC-16, buy 74HC165D as the primary and 74LVC165A as the alternate, not the other way round.** Same footprint, cheaper, better edges over an unterminated loom, and it removes a package question from a hand-assembled board that goes inside a sealed body.

**11. Parts with genuine multi-source comfort** — no action needed: `OPA2197` (TI, but the only part used across the whole analog design, which is a *concentration* risk rather than a supply one — see finding 21), `LM317LZ` (TI + onsemi + ST, all active `[VERIFIED]`), `74AHCT125` (TI + Nexperia + Diodes `[VERIFIED]`), `1N5817` (dozens of makers `[MEM]`), `BAV99` (dozens `[MEM]`), `PJ398SM` (WQP; PJ301M-12 and WQP518MA are functionally identical and interchangeable `[VERIFIED]`), all 0805 passives, the 16-pin shrouded IDC header, the toggle, the trimmers.

### 2.3 Availability, lead time, MOQ, marginal suppliers

**12. `MECH-PTFE` is the only line item with a real MOQ problem, and it is entombed.**
"Porous hydrophobic PTFE plug" has no part number, no vendor and no size. The industrial suppliers of porous PTFE vent media (Porex, W.L. Gore, Donaldson) sell into OEM channels with meaningful minimums and long quote cycles `[MEM — not verified, could not reach vendor sites]`. This part does two load-bearing jobs at once per ADR 0003 (Helmholtz restrictor above the 500 Hz corner, **and** liquid-water barrier), it sits inside the bonded body, and its orifice size is an **E2 bench-sized** parameter, meaning you need several to size it.
**Practical path `[MEM]`:** PTFE syringe filters (0.2–0.45 µm, 13 mm or 25 mm, sold in packs of 50–100 for tens of dollars from lab suppliers) are hydrophobic porous PTFE in a housing you can cut down, and they come in a range of pore sizes — which is exactly the ladder E2 needs. Also: ePTFE vent patches sold for enclosure venting. Either way, **order a range early**, not one size late.

**13. `WS2815` is the marginal-supplier line.**
No authorised distribution exists for addressable strip in the way it does for a TI part. Practical channels are BTF-Lighting (Amazon/AliExpress), ALITOVE, and a handful of Chinese strip houses `[MEM]`. Two documented problems: (a) counterfeit/degraded addressable LEDs are widespread and present as flicker at low brightness and dead-pixel cascades `[VERIFIED — falatic.com and josh.com spotter's guides, VHS Talk thread]`; (b) "12 V addressable" is ambiguous — plenty of 12 V strip is **WS2811-based with one controller per three LEDs**, which silently destroys the per-LED addressing and the 60/m pixel density the diffusion decision at M6 is predicated on.
**Action:** buy ≥2 m from one vendor in one order; on arrival, verify (i) 60 individually addressable pixels per metre, (ii) the backup data line actually works by deliberately killing one LED before installation. That last test is the entire reason WS2815 was chosen over WS2812B and it costs one LED to confirm.

**14. Dev boards are consumer products and will be entombed.**
Both are currently available `[VERIFIED]`. ADR 0013 already states the cost honestly: *"a discontinued dev board would mean a redesign."* `[REPO]` The under-stated part is **silent revision**: LilyGO ships base/Plus/V1.0 variants with different button positions and touch options, and Waveshare boards get quiet BOM changes. ADR 0007 makes two things load-bearing on the exact board: **quad, not octal, PSRAM** (octal eats GPIO33–37 and collapses the pin budget to exactly-enough), and **which face carries the 8×8 matrix relative to the header rows** (ADR 0014 — wrong orientation means mounting on the carrier's underside or a 14-signal flying harness).
**Action: buy two of each, in one order, so the spare is from the same batch as the installed unit.** A spare bought two years later is a different board.

**15. Nothing has a semiconductor lead time worth planning around.** The long poles are process, not parts: laser/waterjet turnaround (days), PCB fab (about a week per spin, and the carrier *will* spin at least once per the ROADMAP), and the M8 pre-bond gate. `[REPO + MEM]`

**16. The real schedule risk is the nine lines with no part number.**
`PLATE-TOP` (thickness open — 1.5 vs 2 mm, pending Gateron's clip dimension), `BODY-OAK` (thickness open — sets thumb inset), `SIDE-ACRYLIC`, `MECH-WINDOW`, `C-BULK-DISP`, `TUBE`, `MECH-COAT`, `MECH-PTFE`, `CABLE-UMB`, plus `R-PRECISION` at `qty TBD`. None of these can be quoted, let alone ordered. Four of them (`PLATE-TOP`, `BODY-OAK`, `SIDE-ACRYLIC`, `MECH-WINDOW`) go in the **same laser/waterjet order as `PANEL`**, which ADR 0004 and ADR 0009 both insist on — so *one unresolved thickness holds up five line items and two milestones.*
And note the Gateron clip dimension is the gating input, and `gateron.com`/`gateron.co` are **unreachable from this sandbox** — the repo's own `ks33-geometry.md` records the same block. Whoever places the order needs to pull that drawing from an unblocked network.

**17. Suppliers you cannot consolidate.** Beekeeb (Hong Kong, keycaps), the Eurorack DIY shops (Thonk UK / Oddvolt SE / Synthrotek US for `J-CV`, `POT-BREATH`, `J-PWR-EURO`), the strip vendor, the board vendors, the cutting vendor, and the wood. That is the irreducible spread — see §4.

### 2.4 Substitution safety — what silently breaks

This is the section that matters most for a one-off, because these are the swaps a builder makes at 11pm with a part in a drawer.

**18. Silently catastrophic — never substitute:**

| Specified | Tempting swap | What silently breaks |
|---|---|---|
| **DAC8568 A or C grade** | DAC8568 B or D | Reset state inverts. Mod channels no longer park at 0 V; pitch parks octaves up instead of subsonic; the `U-WATCHDOG` `CLR` safe-state argument is void. Looks fine on the bench until a reset happens mid-set. `[VERIFIED behaviour]` |
| **MPXV4006DP** | MPXV4006**GP** | Different case (1369-01, single port) — will not fit the 1351-01 footprint. Also obsolete. `[REPO + VERIFIED lifecycle]` |
| **MPXV4006DP** | MPXV**7002**DP | Same-looking dual-port package, but **bidirectional ±2 kPa**, half-scale at zero. Every calibration constant in firmware is wrong and the instrument reads 2.5 V at rest. `[MEM — from the part family, not verified this session]` |
| **MPXV4006DP** | MPXV**5004**DP | 0–3.92 kPa, different sensitivity. Breath clips at ~65 % of intended range. `[MEM]` |
| **74AHCT125** | 74HC125 / 74LVC125 / 74LV125 on the 5 V rail | **AHCT/HCT is the whole point.** HC on 5 V has CMOS thresholds (V_IH ≈ 3.5 V), so a 3.3 V GPIO is marginal-to-invalid. LVC on 5 V is worse. Symptom: LED strips that work on the bench and glitch in the build — exactly what ADR 0014 warns about. `[VERIFIED thresholds via the WS2815 work below]` |
| **BAV99 (silicon)** | BAT54S (Schottky) | 2 µA leakage × 1 kΩ = 2 mV = **2.4 cents of temperature-dependent pitch error**, reintroducing exactly what the LT5400 and the trimmers were bought to remove. Already in the BOM notes — make sure it is on the **schematic symbol** too. `[REPO]` |
| **R-78E5.0-1.0** | R-78E5.0-**0.5** | Half the current rating, against a load already computed at 1.36 A worst case. The digit is easy to misread on the label. `[REPO + VERIFIED part exists]` |
| **Ferrite bead ≥1 A, 1206/1210** | the common 0805 600 Ω part | Rated ~300 mA; both +12 V branches exceed that. A saturated bead is a wire — the filtering silently disappears. `[REPO]` |
| **L-BUCK-IN, a real 10–47 µH inductor** | another ferrite bead | ADR 0004 is explicit: *"This is the part the bead was wrongly credited for."* Also size on **saturation** current, not just RMS. `[REPO]` |
| **Cat5e STRANDED patch** | any Cat5e/Cat6 off the shelf | Most cheap cable is solid core; Cat6 patch is often 23 AWG solid. Work-hardens and fractures at the connector. A broken AGND strand is a ~54 mV intermittent breath offset that will be blamed on firmware forever. `[REPO]` |
| **Tai-Hao MT165-MX** | Tai-Hao MT165 / THCS-MX | Choc v2 stem, not MX. Will not fit KS-33. Beekeeb stocks both on adjacent pages. `[VERIFIED — both product pages exist]` |
| **Gateron KS-33 Low Profile 2.0** | KS-33 3.0, KS-33 Silent 2.0, or KS-27 | KS-27 is 11.75 mm vs KS-33's 12.2 mm `[VERIFIED]`; 3.0 is a separate generation with its own spec; Silent changes the travel/feel. All three break a stack modelled against the 2.0 STEP. |

**19. Safe substitutions — explicitly fine:**

- **74HC165D for 74LVC165A.** Same SOIC-16 footprint, blessed by ADR 0001, and arguably *better* over an unterminated 14-inch loom. `[REPO]` Caveat: **74HCT165 is not fine** — TTL thresholds on a 3.3 V supply are a different animal.
- **PJ301M-12 or WQP518MA for PJ398SM.** Functionally identical and interchangeable; PJ398SM just has stronger reinforced bushings. `[VERIFIED]`
- **MCP3202-CI/P (PDIP) or -CI/ST (TSSOP) for -CI/SN (SOIC).** Same die. PDIP is easier to hand-assemble and easier to socket. `[VERIFIED — all three orderables exist]`
- **1N5819 for 1N5817.** Higher reverse voltage, same forward drop class, same DO-41. `[MEM]`
- **CD74HC123M for "74HC123".** Pick TI's, since Nexperia's is discontinued. `[VERIFIED]`
- **LilyGO T-Display-S3 AMOLED → any C6 or S3 board with a screen and a radio.** ADR 0013 reduced the display board's requirement to four broken-out pins, so this one genuinely *is* substitutable — the only real constraints are AMOLED (not IPS) and the 60 mm lengthwise fit. `[REPO]` Worth knowing: this is the **only** entombed dev board with a clean escape route.

**20. Substitutions that are "safe" but change a number you must then change elsewhere:**

- **INA821 ↔ INA828.** Same SOIC-8, same pinout, **different gain equation** — INA821 is `G = 1 + 49.4 k/R_G`, INA828 is `G = 1 + 50 k/R_G` `[MEM — the 1-to-10,000 vs 1-to-1000 gain-range difference was VERIFIED this session; the exact numerator values are from memory]`. For the ~2.13× stage the difference is small but it is not zero, and it is invisible at assembly. **Pick one part, print its R_G on the schematic, and do not carry "or" in the BOM.**
- **REF5050AIDR vs REF5050IDR.** `A` grade is the ±0.05 % / low-drift one. The non-A grade still works — breath is zeroed and the module's gain knob sets span, so initial accuracy calibrates out — but ADR 0003's 3 ppm/°C drift argument does not survive the swap, and the sensor is ratiometric to this exact rail. `[MEM]`
- **LM317LZ divider values.** The 240 R / 768 R divider draws ~5.2 mA, which is what satisfies the LM317L's minimum-load requirement — the DAC alone does not. If anyone "optimises" that divider to higher values to save power, the regulator loses regulation. `[MEM — the minimum-load mechanism is standard LM317 behaviour; the exact LM317L minimum-load number was not verified]` Worth a schematic note.
- **`C-STRIP-BULK` 470–1000 µF / 16 V.** 16 V on a 12 V rail is thin derating for a part that will sit inside a body running 10–20 K above ambient for years. **Use 25 V**, low-ESR, and check the diameter fits the side channel.
- **Alpha 9 mm B50k → any "9 mm vertical pot".** Taper must be **B (linear)**; ADR 0006 depends on it. And 9 mm vertical pots vary in pin pitch, bushing length and nut size between makers — on a one-off panel with one cutting job, that is a panel you cut twice. Same for `SW-POWER`'s 6 mm bushing. **Have both parts physically in hand before the panel DXF is final.**
- **Conformal coating.** ADR 0009 specifies **acrylic**. Substituting silicone or urethane changes reworkability (acrylic is the reworkable one) and, more importantly, changes how it wicks — and the one thing that must not happen is coating sealing the MPXV4006DP's reference port `[REPO]`.

### 2.5 Counterfeits

**21. The concentrated-risk list, in order.**

- **`U-DAC` DAC8568, `R-PRECISION` LT5400, `U-REF-BREATH` REF5050, `U-OPA-PITCH`/`U-BUF` OPA2197, `U-DIFFRX` INA821.** Precision analog from TI and ADI is heavily re-marked. The specific danger here is **grade re-marking**: a B-grade DAC8568 relabelled C, or a C-grade LT5400 relabelled A, is functionally invisible on a meter and shows up as a wrong reset state or a tuning drift you will chase for months. This BOM is unusually exposed because **one op-amp part number is used six times** (`U-OPA-PITCH` ×5 + `U-BUF` ×1) — a single bad tube contaminates the entire analog design at once. **Broad-line authorised distributors only: DigiKey, Mouser, Farnell/Newark, Arrow, RS, or the manufacturer store. No eBay, no AliExpress, no LCSC for these six lines, no independent brokers even when the "Active/Obsolete Chips" broker pages look official** — several such pages showed up in my searches for exactly these parts.
- **`U-BREATH` MPXV4006DP.** Counterfeit NXP MPX-family sensors are documented and common: implausibly cheap units with inkjet rather than laser marking, grossly inaccurate output or immediate failure on power-up. `[VERIFIED — AliExpress's own buyer-guidance articles describe the authentication problem; general counterfeit-component literature corroborates]` A fake here is the worst possible outcome given the part is entombed. **Authorised distributor only, and keep the packaging.**
- **`J-UMBILICAL` Neutrik etherCON.** Neutrik runs an active anti-counterfeit programme — a hologram of the Neutrik name and logo plus an authenticity seal on individual and carton packaging `[VERIFIED — TV Tech, connectortips, connectorsupplier]`. Counterfeit Neutrik is a long-standing problem in pro audio. Buy from an authorised pro-audio dealer or a broad-line distributor, check the hologram, and note that the **instrument-end connector is entombed and mechanically loaded** — this is not the place for a bargain.
- **`LED-SIDE` WS2815.** Covered in finding 13. Counterfeit/reject addressable LEDs are endemic and are relabelled routinely `[VERIFIED]`.
- **`SW1-n` Gateron KS-33.** The BOM records the source as **Amazon** `[REPO]`, which is a marginal channel for Gateron specifically — mixed and counterfeit switch batches are a known keyboard-community problem `[MEM — I could not verify a KS-33-specific counterfeit report, and gateron.com is blocked]`. Since they are already bought and 18 of them will be soldered into a sealed body, the sensible response is not paranoia but **measurement**: M1 already scopes bounce and hysteresis and assesses action by hand. Add "check actuation force and height against the published 12.2 mm / 1.70 mm / 3.00 mm spec" to that list, and buy the **spares** from Gateron direct or a keyboard specialist rather than the same marketplace listing.
- **`D-REVPOL` 1N5817.** Common commodity Schottky, commonly faked with slower silicon dies `[MEM]`. Low consequence here (the module is serviceable) but it costs nothing to buy from a distributor.
- **Dev boards.** "LilyGO" and "Waveshare" boards on marketplace channels are sometimes clones with different flash/PSRAM configurations or a different IMU. Given that ADR 0007 makes **quad PSRAM** and **QMI8658C** load-bearing, buy from the vendor store or their official marketplace storefront. `[REPO + MEM]`
- **Not applicable but worth noting:** `U-ESD-USB` USBLC6-2SC6 is one of the most-counterfeited small parts in hobby electronics `[MEM]` — it is `not-needed` in this BOM (dev boards carry it), so the risk is zero unless ADR 0013's custom-carrier path is ever revived.

### 2.6 Spares policy against a sealed body

**22. The governing distinction is *entombed* vs *serviceable*, and the BOM splits almost perfectly along the controller/module line.**

**Entombed (inside the bonded lamination, unreachable forever):** all 18 switches, the aluminium key plate, the carrier PCB and everything on it (`U-KEYS` ×4, `U-ADC`, `U-REF-BREATH`, `U-BUF`, `U-LVLSHIFT`, `U-BUCK`, `F-POLY`, `U-TVS-UMB`, `L-BUCK-IN`, all controller passives), `U-BREATH` and its tube/trap/PTFE plug, both dev boards, both WS2815 runs and their bulk caps, the instrument-end etherCON, the internal looms, the U-bolt and backing plate, `MECH-GNDBOND`.

**Serviceable (unscrew the module from the rack, open it on the bench):** everything with `category: module` — `U-DAC`, `U-OPA-PITCH`, `R-PRECISION`, `J-CV`, `POT-BREATH`, `SW-POWER`, `U-LOADSW`, `J-PWR-EURO`, `D-REVPOL`, `U-REG-DAC`, `U-WATCHDOG`, `U-LVL-MOD`, `U-DIFFRX`, all module passives. Plus `CABLE-UMB` and the keycaps, which are outside the body entirely.

**23. The uncomfortable truth about the breath sensor spares.**
ADR 0003 says *"Treat the sensor as a wear part. It is socketed or otherwise replaceable... Buy two."* ADR 0009 says the body is bonded shut. **Both cannot be true after M8.** The sensor is the most-likely-to-fail part in the design (gel die coat swells with moisture; NXP qualifies the family on dry air and states it is not compatible with water or water vapour `[REPO]`), and it is entombed.
So: **the spares are pre-bond insurance only.** They cover the E2 syringe/port-orientation test, a masked-port assembly mistake, a coating accident, a soldering kill, and a unit that reads wrong during the M8 two-hour play test. They do **not** cover a failure in year three — nothing does, short of making the sensor sub-assembly external to the lamination (which the review's S3 proposed and the project declined in favour of the bottom placement). **That trade should be stated explicitly somewhere in ADR 0003, because "buy two" reads like it solves the in-service problem and it does not.**
This does not change the recommendation to buy spares. It changes what they are for.

---

## 3. Recommended buy-spares list

Quantities are **total to order**, including the build units. Rationale is the whole point of the column.

### Tier 1 — buy now, non-negotiable

| Part | Build qty | **Order qty** | Why this quantity |
|---|---|---|---|
| `U-BREATH` MPXV4006DP | 1 | **4** | Entombed, moisture wear part, no functional equivalent at any price, architecture depends on it. Four covers: the build unit, the E2 port-orientation and restrictor-sizing work (which risks one), a coating/masking accident, and the M8 re-test. ~$15–20 each `[MEM]` — trivial against the instrument |
| `SW1-n` Gateron KS-33 Red 2.0 | 18 | **26–28** (+4 lighter-spring thumb switches if M1 says so) | Cheapest insurance in the BOM. M1 destructive characterisation, the M2 hand-wired mule and the final build are three separate populations; desoldering during layout iteration kills switches; and **the 2.0 is being superseded by a 3.0**, so a later re-order may be a different switch. Buy from Gateron direct, not the original marketplace listing |
| `U-MCU-RT` Waveshare ESP32-S3-Matrix | 1 | **2** | Entombed. ~€10–15. Second unit from the **same batch** guarantees the same PSRAM config and matrix orientation the carrier was designed around. ADR 0013 concedes a discontinued dev board means a redesign |
| `U-DISP` LilyGO T-Display-S3 AMOLED (base) | 1 | **2** | Entombed **and** has an acknowledged wear-out mode (AMOLED burn-in). The priciest spare at ~$35–45 `[MEM]` and the most justified one. Base, not Plus; note which header variant |
| `LED-SIDE` WS2815 60/m | 0.84 m | **2 m minimum** | The M6 diffusion prototype consumes strip that is then not available for the build; cutting to 420 mm twice from 1 m leaves no margin for a bad cut or a dead first pixel; re-ordering later gets a different bin. Also buy it early enough to run the backup-data-line test before committing |
| `J-UMBILICAL` etherCON chassis | 2 | **3** | One end is entombed and mechanically loaded (the cable tugs sideways every time the instrument moves). Authorised dealer, hologram checked |
| `U-DAC` DAC8568 (**A or C grade, full P/N**) | 1 | **2** | Not a failure spare — a **lifecycle** spare. The grade is the design and its stock is the thinnest in the BOM. TSSOP-16 hand-soldering also has a nonzero kill rate |
| `U-BUCK` R-78E5.0-1.0 | 1 | **2** | Entombed single point of failure for the instrument's entire 5 V rail, running at ~0.4 A against a 1 A rating with a documented 1.36 A pathological case. ~$6 |
| `CABLE-UMB` Cat5e stranded STP 2 m | 2 | **3** | Declared a consumable by ADR 0004. The policy is "replace at first intermittency", which requires a spare in the drawer, not an order |

### Tier 2 — buy spares because they are cheap and entombed

| Part | Build qty | **Order qty** | Why |
|---|---|---|---|
| `U-KEYS` 74HC165D / 74LVC165A | 4 | **6** | Pennies. Entombed. SOIC rework on a hand-built board kills parts |
| `U-ADC` MCP3202 | 1 | **2** | Entombed, showed a backorder signal at one distributor |
| `U-REF-BREATH` REF5050A**IDR** | 1 | **2** | Entombed, grade-specific, and the breath scale factor literally *is* this part |
| `U-BUF` + `U-OPA-PITCH` OPA2197IDR | 6 | **9** | One of these six is entombed. Buying three extra also protects against a single contaminated tube (see counterfeit note) and gives the module board rework margin |
| `U-LVLSHIFT` + `U-LVL-MOD` 74AHCT125 | 2 | **4** | One is entombed, and this is the part most likely to be substituted wrongly under time pressure — having the right one in the drawer is the defence |
| `R-PRECISION` LT5400 (correct suffix) | 1–2 | **build qty + 1** | MSOP-8 at 0.65 mm on a hand-assembled board. Also suffix-specific stock |
| `U-WATCHDOG` CD74HC123M | 1 | **2** | Trivial cost; Nexperia's version is discontinued so the supply base is thinner than it looks |
| `CAP1-n` MT165-MX | 18 | **20 (4 packs)** — already the plan | Small single vendor, colour/batch matching. 4 packs gives 2 spares for free |
| `MECH-PTFE` porous PTFE | 1 | **a size ladder, 3–5 sizes** | The orifice size is an E2 *result*, not an input. Ordering one size is ordering the wrong size |

### Tier 3 — explicitly do NOT buy spares

- **All 0805 passives** (`R-*`, `C-*`, `FB-IN`, `R-TERM-CHAIN`, `C-DECOUPLE`, …). They are sold in packs of 10/100 and the spare is already in the bag.
- **`J-CV` PJ398SM** — sold in 10-packs; 6 used, 4 spare automatically.
- **`SW-POWER`, `J-PWR-EURO`, `D-REVPOL`, `U-REG-DAC`, `TRIM-PITCH`, `POT-BREATH`, `D-JACK-CLAMP`, `F-POLY`** — all module-side or trivially replaceable, in a box that unscrews from a rack in five minutes. A spare here is clutter. (Buy the minimum pack, which usually gives spares anyway.)
- **`PANEL`, `PLATE-TOP`, `BODY-OAK`, `SIDE-ACRYLIC`** — a "spare" flat part is just a re-order. What you *should* do instead is put the **test coupon** (the ±0.1 mm cutout ladder from ADR 0002) and a **spare 6HP panel blank** in the *same* cutting job, because the marginal cost of extra parts in one job is near zero and a second job is a second setup fee and a second week.
- **`U-LOADSW`, `U-TVS-UMB`** — do not buy anything yet. These two line items are wrong (findings 1 and 2). Buying spares of a part you are about to replace is the most expensive form of thoroughness.

---

## 4. The total order, practically

### 4.1 Supplier grouping

Eleven to fourteen distinct suppliers, realistically consolidated to **nine orders**:

| # | Supplier | Lines | Notes |
|---|---|---|---|
| 1 | **Broad-line distributor A** (DigiKey or Mouser) | `U-DAC`, `U-OPA-PITCH`, `U-BUF`, `U-DIFFRX`, `U-REF-BREATH`, `U-ADC`, `U-KEYS`, `U-LVLSHIFT`, `U-LVL-MOD`, `U-WATCHDOG`, `U-REG-DAC`, `U-BUCK`, `U-BREATH`, `R-PRECISION`, `D-REVPOL`, `D-JACK-CLAMP`, `F-POLY`, `L-BUCK-IN`, `FB-IN`, `TRIM-PITCH`, all 0805 passives, electrolytics | The bulk of the BOM by line count. **Authorised channel is mandatory here** for counterfeit reasons |
| 2 | **Broad-line distributor B** | Whatever A is out of — most likely the DAC8568 grade and the LT5400 suffix | Plan on two broad-line orders, not one. The two parts most likely to force this are also the two most important |
| 3 | **Eurorack DIY shop** (Thonk UK / Oddvolt / Synthrotek) | `J-CV` ×10-pack, `POT-BREATH`, `J-PWR-EURO`, knobs, ribbon cable | Could be folded into #1 for some lines, but Alpha 9 mm pots and Thonkiconns are easier here |
| 4 | **Pro-audio dealer or broad-line** | `J-UMBILICAL` Neutrik ×3 | Authorised only |
| 5 | **Waveshare** (or their official storefront) | `U-MCU-RT` ×2 | |
| 6 | **LilyGO** (or their official storefront) | `U-DISP` ×2 | |
| 7 | **Gateron direct / keyboard specialist** | KS-33 spares, and the lighter thumb springs if M1 calls for them | Not the original Amazon listing |
| 8 | **Beekeeb** *(already ordered)* | `CAP1-n` | |
| 9 | **LED strip vendor** | `LED-SIDE` ≥2 m | Marginal channel by necessity |
| 10 | **Cutting vendor** (SendCutSend / Ponoko / OSH Cut) | `PANEL`, `PLATE-TOP`, `SIDE-ACRYLIC`, `MECH-WINDOW`, test coupons, spare panel blank | **One job, one setup.** Blocked on the plate-thickness decision |
| 11 | **PCB fab** (JLCPCB / PCBWay / OSH Park) | Carrier PCB, module PCB, key-cluster satellite boards | Not BOM lines but the same money and the same calendar |
| 12 | **McMaster-Carr / hardware** | U-bolt, M3 + ring terminal (`MECH-GNDBOND`), silicone tube (`TUBE`), adhesive, `MECH-COAT` | |
| 13 | **Lab supplier** | `MECH-PTFE` size ladder | |
| 14 | **Timber merchant** | `BODY-OAK` | Local |

### 4.2 Rough total cost

**All figures `[MEM]`, ±50 %, and they exclude tooling (the bench is already available per ADR 0006) and the already-purchased switches and keycaps.**

| Group | Rough |
|---|---|
| Semiconductors + passives, incl. all Tier 1/2 spares | $200–280 |
| Dev boards ×2 each | $95–125 |
| Neutrik etherCON ×3 | $45–75 |
| Eurorack hardware (jacks, pots, header, knobs) | $25–40 |
| WS2815 2 m + bulk caps | $20–35 |
| Cat5e stranded STP ×3 | $15–25 |
| Gateron spares + thumb-weight switches | $20–35 |
| Laser/waterjet: panel, key plate, acrylic, coupons, spare blank | $120–220 |
| PCB fab, 2–3 designs, small qty, incl. one expected carrier respin | $80–160 |
| Oak, adhesive, conformal coating, U-bolt, M3, tube, PTFE | $90–150 |
| Shipping across ~9–11 orders | $60–120 |
| **Total** | **≈ $770–1,265** |

Call it **$900–1,000 as a planning number**, with **roughly $120–160 of that being deliberate spares** — about 15 %, which for a sealed one-off that is meant to last years is cheap, and I would not cut it.

The cost is dominated by **process** (cutting + PCB ≈ $200–380) and **dev boards** (≈ $100), not by the precision analog everyone worries about. The DAC8568, the LT5400 and the six OPA2197s together are maybe $50.

### 4.3 What holds the build up

**Nothing in the semiconductor BOM has a lead time that matters.** The hold-ups are all decisions and processes:

1. **`U-LOADSW` must be respecified before the module PCB.** It is on the critical path for E6 and E12, and it changes the schematic, the footprint and possibly the package-policy argument. **Do this first.** *(S1)*
2. **`U-TVS-UMB` must be respecified before the carrier PCB (E13).** It is on the carrier, therefore inside the bonded body, therefore unfixable later. *(S1)*
3. **The plate-thickness decision gates five mechanical line items and one cutting order**, and it needs Gateron's clip dimension — from a network that can reach `gateron.com`. Until that lands, `PLATE-TOP`, `BODY-OAK`, `SIDE-ACRYLIC`, `MECH-WINDOW` and `PANEL` cannot be quoted. *(S2)*
4. **`R-PRECISION`'s suffix gates the module BOM freeze.** Resolve the pitch ratio question against the actual ADI datasheet. *(S2)*
5. **The DAC8568 grade should be bought now, ahead of need**, because it is the one line where stock is visibly thin and where no substitution is acceptable. *(S1)*
6. **The ROADMAP's own ordering rules are the real schedule constraint**, and they are already correct: M5 (aluminium) after E13 (carrier), and the body does not close until the carrier is revision-final and burned in through M8. A carrier respin is *expected*, so budget the week and the fab fee for it rather than being surprised.

Nothing else should stop you ordering. If you want a single action from this review: **fix the load switch, fix the TVS, lock the DAC grade, and buy the four sensors and the two of each dev board today.** Everything else can wait for the decisions it depends on.

---

## 5. Things I could not check, and what you should check instead

- `ti.com`, `analog.com`, `digikey.com`, `mouser.com`, `littelfuse.com` are all blocked from this sandbox. **Every lifecycle claim above that came from a search summary rather than a primary vendor page should be re-checked on an unblocked network before money moves** — specifically: the TPS2553 NRND claim, the SP3012-06UTG obsolescence, the DAC8568 A/C grade stock, the LT5400 variant table, and the existence of a stocked `SN74LVC165AD` in SOIC-16.
- `gateron.com` / `gateron.co` are blocked (as `docs/reference/ks33-geometry.md` already records). The KS-33 2.0 clip dimension, the dimensioned drawing and the STEP model all still need pulling.
- I did not check live stock quantities for anything — only lifecycle and the existence of orderable part numbers.
- I did not verify prices. Every figure in §4.2 is from memory and should be treated as an order-of-magnitude planning number, not a quote.

**Sources**

- [MPXV4006DP — NXP part page](https://www.nxp.com/part/MPXV4006DP) · [Mouser](https://www.mouser.com/ProductDetail/NXP-Semiconductors/MPXV4006DP?qs=N2XN0KY4UWU/MaGWz5cTWg%3D%3D) · [DigiKey](https://www.digikey.com/en/products/detail/nxp-usa-inc/MPXV4006DP/1168423) · [datasheet](https://www.nxp.com/docs/en/data-sheet/MPXV4006.pdf)
- [DAC8568 — TI product page](https://www.ti.com/product/DAC8568) · [packaging addendum](https://www.ti.com/ods/sysadd/oa/symlink/dac8568_oa.pdf) · [DAC8568ICPWR at DigiKey](https://www.digikey.com/en/products/detail/texas-instruments/DAC8568ICPWR/296-50521-1-ND/9685660) · [CLR / reset-grade thread on TI E2E](https://e2e.ti.com/support/data-converters-group/data-converters/f/data-converters-forum/304374/dac8568-clr-pin-software-reset)
- [TPS2553 — TI product page](https://www.ti.com/product/TPS2553) · [datasheet mirror](https://datasheet.octopart.com/TPS2553DBVR-Texas-Instruments-datasheet-11745275.pdf) · [TPS25926/TPS25925](https://www.ti.com/product/TPS25925) · [TPS1663](https://www.ti.com/product/TPS1663)
- [SP3012-06UTG — Littelfuse](https://www.littelfuse.com/products/overvoltage-protection/tvs-diode-arrays/low-ultra-low-capacitance/sp3012/sp3012-06utg) · [DigiKey](https://www.digikey.com/en/products/detail/littelfuse-inc/SP3012-06UTG/3911066) · [Octopart](https://octopart.com/part/littelfuse/SP3012-06UTG)
- [LT5400 — Analog Devices](https://www.analog.com/en/products/lt5400.html) · [datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/5400fc.pdf) · [LT5400BCMS8E-7 at Newark](https://www.newark.com/analog-devices/lt5400bcms8e-7-pbf/res-net-volt-divider-1-25k-5k/dp/50AK5836)
- [OPA2197IDR — TI](https://www.ti.com/product/OPA2197/part-details/OPA2197IDR) · [INA821](https://www.ti.com/product/INA821) · [INA828](https://www.ti.com/product/INA828)
- [LM317LZ/NOPB — Octopart](https://octopart.com/lm317lz/nopb-texas+instruments-24813653) · [onsemi LM317L datasheet](https://www.onsemi.com/pdf/datasheet/lm317l-d.pdf)
- [R-78E5.0-1.0 — DigiKey](https://www.digikey.com/en/products/detail/recom-power/R-78E5-0-1-0/4930585)
- [MCP3202 — Microchip](https://www.microchip.com/en-us/product/mcp3202) · [MCP3202-CI/SN at RS](https://us.rs-online.com/product/microchip-technology-inc-/mcp3202-ci-sn/70046143/)
- [SN74LVC165A — TI](https://www.ti.com/product/SN74LVC165A) · [Nexperia 74HC165D at RS](https://uk.rs-online.com/web/p/counter-ics/1038181) · [SN74HC165 — TI](https://www.ti.com/product/SN74HC165)
- [74HC123/74HCT123 — Nexperia](https://www.nexperia.com/products/analog-logic-ics/logic/specialty-logic/multivibrators/series/74HC123-74HCT123.html) · [CD74HC123M — TI](https://www.ti.com/product/CD74HC123/part-details/CD74HC123M)
- [SN74AHCT125 — TI](https://www.ti.com/product/SN74AHCT125) · [74AHCT125D — Nexperia](https://www.nexperia.com/product/74AHCT125D)
- [WS2815 datasheet](https://www.superlightingled.com/PDF/WS2815-12v-addressable-led-chip-specification-.pdf) · [Advatek WS2815 protocol notes](https://www.advateklighting.com/pixel-protocols/ws2815) · [A spotter's guide to WS2812B LEDs](https://www.falatic.com/index.php/179/a-spotters-guide-to-ws2812b-leds-distinguishing-good-from-garbage) · [A quick test for crappy WS2812B neopixels](https://wp.josh.com/2016/10/29/a-quick-test-for-crappy-ws2812b-neopixels/)
- [Neutrik NE8FDP](https://www.neutrik.com/en/product/ne8fdp) · [NE8FDX-P6](https://www.neutrik.com/en/product/ne8fdx-p6) · [Neutrik takes anti-counterfeit measures](https://www.tvtechnology.com/news/neutrik-takes-anticounterfeit-measures) · [Four tips to avoid counterfeit connectors](https://www.connectortips.com/four-tips-avoid-counterfeit-connectors/)
- [Thonkiconn — Thonk](https://www.thonk.co.uk/shop/thonkiconn/)
- [Gateron KS-33 Low Profile 2.0](https://www.gateron.com/products/gateron-ks-33-low-profile-20-switch-set) · [KS-33 Low Profile 3.0](https://www.gateron.com/products/gateron-ks-33-low-profile-30-mechanical-switch) · [KS-27 vs KS-33](https://www.gateron.co/blogs/news/gateron-low-profile-switches-ks-27-vs-ks-33)
- [MT165-MX — beekeeb](https://shop.beekeeb.com/products/mt165-black-blank-keycap) · [Tai-Hao MT165 range](https://shop.tai-hao.com/categories/mt165-low-profile-keycaps)
- [T-Display-S3-AMOLED — LilyGO wiki](https://wiki.lilygo.cc/products/t-display-series/t-display-s3-amoled/) · [ESP32-S3-Matrix — Waveshare](https://www.waveshare.com/esp32-s3-matrix.htm)
- [Counterfeit electronic component — Wikipedia](https://en.wikipedia.org/wiki/Counterfeit_electronic_component) · [MPX4250 buyer guidance](https://www.aliexpress.com/s/wiki-ssr/article/mpx4250-datasheet)
