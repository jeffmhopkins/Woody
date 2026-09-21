# LED — Waveshare ESP32-S3-Matrix power-path parts (R7)

Researcher: LED. Date: 2026-09-21. Repo: /home/user/Woody.
Assignment: (1) WS2812B-0807, (2) B5819WS, (3) ME6217C33M5G.

Files banked this run:

| file | sha256 (short) | pp |
|---|---|---|
| `datasheets/discrete-and-power/B5819WS.pdf` | `437ac962…` | 6 |
| `datasheets/other-semi/ME6217C33M5G.pdf` | `fb290308…` | 13 |
| `datasheets/other-semi/XL-0807RGBC-WS2812B.pdf` | `bdc437c4…` | 18 |
| `datasheets/other-semi/XL-0807RGBC-WS2812B-REV2024.pdf` | `008695e4…` | 16 |

Every file verified: starts with `%PDF-`, >10 kB, part number present in
`pdftotext -layout` output. No repo file outside `datasheets/` was touched.

---

## 1. WS2812B-0807 — **BLOCKED for the exact part. Worldsemi does not publish it.**

### Repo's current belief

`[repo docs/decisions/0014-lighting.md:381-382]`

> "WS2812C-2020 draws **5 mA per channel**, so 15 mA per LED at full white and
> 960 mA for all 64 — **this is the wrong part's figure; see the note above.**"

`[repo docs/decisions/0014-lighting.md:161]` "at full field it asks for 960 mA on
its own" — the load-bearing use.
`[repo ROADMAP.md:184]` "64 unlit WS2812C drivers are an estimated ~50 mA".
The ADR already carries the lead's 2026-09-21 warning block
`[repo docs/decisions/0014-lighting.md:357-378]` saying the figure is unsourced.

### Verdict on the fetch: **BLOCKED (part-specific document does not exist publicly)**

This is not "I could not reach the server". I reached Worldsemi and established a
**negative from the vendor's own machine-readable catalogue**:

- `[web https://www.world-semi.com/datasheet-availability.js?v=20260901a]` is the
  index the site's own "Download Datasheet" buttons read. It enumerates **68 EN
  keys** covering every published Worldsemi part. The WS2812 family keys are:
  `ws2812a, ws2812b-v6, ws2812b-v7, ws2812b-mini-v6, ws2812b-mini-v7,
  ws2812b-1313-v6, ws2812b-2020-v6, ws2812b-2020-v7, ws2812b-2427-v6/-v7,
  ws2812b-4020-v6/-v7, ws2812c-v6, ws2812c-1313-v6, ws2812c-2020-v6,
  ws2812c-2427-v6, ws2812c-4020-v6, ws2812c-mini-v6, ws2812d-*, ws2812e-*`.
  **There is no `0807` key of any kind, in EN or CN.**
- The URL scheme it exposes is `https://www.world-semi.com/downloads/datasheets/en/<key>-<ver>.pdf`.
  Control: `…/en/ws2812b-2020-v6-1.0.pdf` → **HTTP 200, 1 264 070 bytes, `%PDF-`**.
  Guesses `…/en/ws2812b-0807.pdf` and `…/en/ws2812b-0807-v1.0.pdf` → **HTTP 404**.
- Product pages exist at `/products/<model>.html`; `/products/ws2812b-0909.html`
  → 200 (so an ultra-small package page *can* exist), but
  `/products/ws2812b-0807.html` and `/products/ws2812b-b0807.html` → **404**.

Other routes tried and their exact outcomes:

| route | result |
|---|---|
| `git clone https://github.com/FastLED/datasheets` | cloned OK; `find -iname '*0807*'` → **0 hits**. `worldsemi/addressable-led/` holds only WS2801, WS2811, WS2812, WS2812B, WS2813, WS2815, WS2816 |
| web.archive.org CDX, `url=world-semi.com matchType=domain filter=original:.*0807.*` | HTTP 200, **0 rows**; later calls returned the IA "Temporarily Offline" 503 page, so Wayback is **down this session** |
| LCSC search API `wmsc.lcsc.com/wmsc/search/global-search` | `{"code":404,"msg":"The static resource is unavailable…"}` for all three keywords |
| `datasheet.lcsc.com` / `www.lcsc.com/datasheet/*.pdf` | HTTP 200 but `text/html`, 9 381 B bot page — not a PDF |
| `files.waveshare.com`, `waveshare.com/wiki/ESP32-S3-Matrix` | wiki links only the ESP32-S3 datasheet/TRM and `ESP32-S3-Matrix-Sch.pdf`. **No LED datasheet anywhere on the vendor page** |
| WebSearch, several phrasings | returns generic 5050 WS2812B datasheets and 0807 *strip* listings; no Worldsemi 0807 document |

**Conclusion: the fitted part's per-channel current remains unsourced from its own
datasheet, and I did not substitute the WS2812C's number.** Per the brief, that is
the reportable outcome. `matrix-led-current` should stay **blocked**.

### What I did get, and it is strong evidence — but it is NOT the 0807's own datasheet

The schematic string was verified by me independently:
`[repo datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf, pdftotext]`
the literal token is **`WS2812B-0807`** (no "B0807" form appears), alongside
`B5819WS` (p. with D1), `ME6217C33M5G` and `DMG1012T-7`.

**(a) A real 0807-package, WS2812B-protocol LED datasheet — XINGLIGHT
XL-0807RGBC-WS2812B, LCSC C3646929.** This is the part a reseller ships when you
buy an "0807 WS2812B" LED `[web https://makerselectronics.com/product/ws2812-smd-addressable-rgb-led-0807/]`.
Manufacturer is **XINGLIGHT, not Worldsemi**. Two revisions exist and they disagree
with each other, which matters:

*Rev A — LCSC upload `2207041845`, 18 pp, banked as `XL-0807RGBC-WS2812B.pdf`*

> "OUT RGB 输出电流 / **OUT RGB output current** … Lout … Typ **12** … mA …
> Test conditions **VDD=5V, VDS=1V**"  `[datasheet XL-0807RGBC-WS2812B (2207041845) p.5]`
>
> "静态电流 / **Static current** … IDD … Typ **0.35** … mA … **VDD=5V, IOUT "OFF"**"  `[p.5]`
>
> "芯片电源电压 / Chip power supply voltage … VDD … Min **3.5** … Max **5.5** … V"  `[p.5]`
>
> "6.采用优化预置 **12mA/通道**恒流模式 / Optimized preset **12mA / channel** constant
> current mode is adopted"  `[p.2]`
>
> "7.内置低压强化模块，VDD 在 **4.5-5.5V** 以上 100%正常工作."  `[p.2]`
>
> Absolute max: "供电电压 Supply Voltage VDD **3.5-5.5V**"; "输出端口耐压 Output port
> withstand voltage VOUT **10** V"; Topr **-40 ~ +85 ℃**; ESD 3000 V HBM  `[p.4]`
>
> Package: "外观尺寸（L/W/H）: **2.0*1.8*0.8mm**"  `[p.1]` — so "0807" is imperial
> 0.08"×0.07", **not** 0.8 mm × 0.7 mm.
>
> Switching: Fpwm typ **4.5 kHz** (Iout=5 mA)  `[p.6]`. Bit timing: Tin0h ≥0.3 µs,
> Tin1h ≥0.9 µs, T0L ≥0.9 µs, T1L ≥0.3 µs, cycle ≥**1.2 µs** (≈**800 kbps**),
> reset **>200 µs**, GRB order, high bit first  `[p.8]`.

*Rev B — LCSC upload `2409291103`, 16 pp, banked as `XL-0807RGBC-WS2812B-REV2024.pdf`*

> "三通道恒流驱动器**默认输出 19mA** … 可设置电流 **1.75mA~19mA**，共 **16 个电流增益等级**；
> PWM 信号刷新率高达 **4KHz**"  `[datasheet XL-0807RGBC-WS2812B (2409291103) p.1]`
>
> "DOUT R/G/B/W 端口驱动电流 / Port drive current … IOUT … Min **1.75** … Max **19** … mA …
> VDS = 2V, current gain setting 0000 ~ 1111"  `[p.5]`
>
> "静态电流 Static power consumption … IDO … Typ **2.5** … mA … **VDD=4.5V, IOUT "OFF"**"  `[p.5]`

**(b) Corroboration from a genuine Worldsemi "B"-suffix part already in the bank.**
`[repo datasheets/other-semi/WS2812B-2020.pdf p.4]`, "LED Characteristics" table:
"**Quiescent Current：<0.6mA**  Test Condition DC=5V … **Working Current 12mA**".
So 12 mA/channel is the Worldsemi **WS2812B** family figure; 5 mA/channel is
specific to the **WS2812C**.

**(c) The vendor's own thermal warning**, which the ADR's brightness cap should cite:
> "Please note that the LED brightness should not be set too high, it will cause a
> rapid temperature increase, which can result in damage to the board."
> `[web https://www.waveshare.com/wiki/ESP32-S3-Matrix]` (repeated 5× on that page)
> and "It supports, ESP32-s3-8x8 is based on RGB **WS2812B**." — the vendor names
> the **B**, never the C.

### What this does to the 960 mA — **REFUTED as too low, in every direction**

`[calc]` 3 channels × 64 LEDs = 192 channels.

| per-channel source | mA/ch | mA/LED white | **mA for 64 at full white** |
|---|---|---|---|
| WS2812C-2020 — **the wrong part**, what the ADR uses | 5 | 15 | **960** |
| WS2812B-2020, genuine Worldsemi `[WS2812B-2020.pdf p.4]` | 12 | 36 | **2304** |
| XL-0807RGBC-WS2812B rev A `[p.5]` | 12 | 36 | **2304** |
| XL-0807RGBC-WS2812B rev B, default gain `[p.1, p.5]` | 19 | 57 | **3648** |

Idle (drivers powered, all channels off), `[calc]` × 64:
WS2812B-2020 `<0.6 mA` → **<38.4 mA**; XL rev A `0.35 mA` → **22.4 mA**;
XL rev B `2.5 mA` → **160 mA**. The ROADMAP's "~50 mA" estimate `[repo ROADMAP.md:184]`
sits inside the first two and is **3.2× low** against rev B.

**The ADR's conclusion survives and gets much stronger; its number does not.**
The argument "full field nearly exhausts the 1 A R-78E5.0" becomes "full field is
**2.3–3.6×** the regulator's entire rating" — and, see §2, **2.3–3.6× the rating of
the single Schottky every LED draws through**. I am not proposing a replacement
figure for `matrix-led-current`, because none of the three sources above is the
fitted part. What I am saying is that **960 mA is not a conservative placeholder —
it is optimistic by at least 2.4×**, and any analysis leaning on it is leaning the
wrong way.

**VERDICT: NOT-IN-DOCUMENT for WS2812B-0807 itself (no such document is published).
REFUTED for the 960 mA figure, on converging evidence from three other documents.**

---

## 2. B5819WS Schottky — **CONFIRMED, with one package correction and one hard ceiling**

Banked: `datasheets/discrete-and-power/B5819WS.pdf`, sha256
`437ac96205e4d6aec87ca1e7ea715654cb0d14a378c07ef76c6cc1c074545261`,
source `https://www.mccsemi.com/pdf/products/B5817WS-B5819WS(SOD-323).pdf`
(HTTP 200, 646 044 B, `application/pdf`). Doc "B5817WS THUR B5819WS", **Rev-5.1-03022026**,
6 pp, manufacturer **Micro Commercial Components (MCC)**. "B5819WS" appears 13× in
the extracted text.

### Repo's current belief

`[repo docs/decisions/0014-lighting.md:374-376]`
> "`VCC_5V` is **not 5.00 V**: it is USB `VBUS` through a `B5819WS` Schottky, so the
> LED rail is a diode drop below VBUS."

No numeric V_F, no current rating, no package anywhere in the corpus — `grep` for
`B5819` over `docs/decisions hardware README.md ROADMAP.md config` returns only that
line. So everything below is **new**, not a contradiction.

### Datasheet text, verbatim

> Product Summary `[datasheet B5817WS-B5819WS Rev-5.1 p.1]`:
> "V_RRM **40 V** … V_F Max @ 1A **600 mV** … I_F(AV) **1A** … I_R Max **40 µA**"
> Mechanical Data `[p.1]`: "**Package: SOD-323**"

> Maximum Ratings (TA=25℃) `[p.2]`, B5819WS column:
> "Peak Repetitive Reverse Voltage V_RRM **40** V … RMS Reverse Voltage V_R(RMS) **28** V …
> Reverse Voltage V_R **40** V … **Average Forward Current I_F(AV) 1 A** …
> Non-Repetitive Peak Surge Current, tp=8.3 ms Half Sine Wave, TJ=25℃, I_FSM **10 A** …
> **Power Dissipation P_D 200 mW** … Operating Junction Temperature Range T_J **-65 to +125 ℃**"

> Thermal characteristics `[p.2]`: "Thermal Resistance from Junction to Ambient **RθJA 500 ℃/W**"
> (Note 2: "Device mounted on an FR4 Printed-Circuit Board (PCB) with the recommended pad layout.")

> Electrical Characteristics `[p.2]`, B5819WS:
> "Reverse Breakdown Voltage V_BR, I_R=1 mA (pulse test), Min **40** V"
> "**Forward Voltage V_F … I_F = 1A … Max 0.60 V … I_F = 3A … Max 0.90 V**"
> "Reverse Current I_R, V_R = 40 V, Typ **7 µA**, Max **40 µA**"
> "Junction Capacitance C_J, V_R=4 V f=1.0 MHz **48 pF**; V_R=10 V **32 pF**"
> "Reverse Recovery Time t_rr, IF=10 mA, IR=10 mA, Irr=0.1×IR, RL=100Ω, Max **50 ns**"

### V_F vs I_F at the currents that matter

The datasheet tabulates V_F only at 1 A and 3 A. Intermediate values come from
**Fig.1 – Typical Instantaneous Forward Characteristics (per diode)**, the
"B5818WS&B5819WS Curve Characteristics" page `[p.4]`, five T_J curves
(125/100/75/25/−55 ℃) on a log-I axis 0.1–1000 mA against a linear 0–0.6 V axis.
I rendered that page at 600 dpi and read the **T_J = 25 ℃** curve off the gridlines.
**Provenance: `[graph-read, datasheet p.4 Fig.1, ±0.03 V]` — weaker than a table row,
and should be marked as such wherever it lands.**

| I_F | V_F, T_J = 25 ℃ | provenance |
|---|---|---|
| 100 mA | **≈0.36 V** | `[graph-read p.4 Fig.1, ±0.03 V]` |
| 500 mA | **≈0.46 V** | `[graph-read p.4 Fig.1, ±0.03 V]` |
| 1 A | **≈0.50 V** typ / **0.60 V max** | graph-read; **max is the table row, `[p.2]`** |

The corpus's habitual "~0.35 V of Schottky" `[repo docs/decisions/0006-cv-channel-allocation.md:136]`
and "400 mV Schottky" `[repo docs/decisions/0005-power-architecture.md:95]` are about
the 1N5817 on the ±12 V rails, not this part, but for scale: this diode is ~0.36 V at
100 mA and ~0.50 V at 1 A, so **VCC_5V ≈ VBUS − 0.36 V at light load and VBUS − 0.50 V
near 1 A.** With VBUS at the wiki's own "4.9 V or more" floor
`[web waveshare.com/wiki/ESP32-S3-Matrix]`, VCC_5V lands at **4.4–4.55 V** —
below the XL-0807's "100 % functional above 4.5–5.5 V" band `[XL rev A p.2]`.

### **The real ceiling is not I_F(AV) = 1 A. It is the 200 mW package.**

`[calc]` P_D = 200 mW at T_A = 25 ℃, and RθJA 500 ℃/W × 200 mW = 100 K = exactly
T_J(125) − T_A(25), so the two agree and derate together.

- At V_F ≈ 0.46 V: I_max = 0.200 W / 0.46 V = **435 mA** at T_A = 25 ℃.
- At V_F ≈ 0.50 V: I_max = 0.200 / 0.50 = **400 mA**.
- Inside the instrument at T_A = 60 ℃: P_allowed = (125−60)/500 = 0.130 W →
  I_max = 0.130 / 0.46 = **283 mA**.

**So the B5819WS in SOD-323 limits the whole ESP32-S3-Matrix board — matrix, ESP32-S3,
IMU, the lot — to roughly 280–435 mA continuous, not 1 A.** The 1 A I_F(AV) headline
is a 25 ℃, infinite-heatsink-free number that the 200 mW dissipation rating overrides
long before you reach it. Against §1's 2.3–3.6 A full-field figure this is **5–13×
over**, and against the ADR's own 960 mA it is still **2.2–3.4× over**.

**VERDICT: CONFIRMED that a B5819WS sits in the LED supply path (schematic + ADR agree).
NEW: I_F(AV) = 1 A, P_D = 200 mW, RθJA = 500 ℃/W, V_F ≈ 0.36/0.46/0.50 V at 0.1/0.5/1 A.**

**CORRECTION to the task brief:** the brief expected **SOD-123**. The datasheet says
**SOD-323** `[p.1, p.2 "Package: SOD-323"]`. The industry suffix convention is
`B5819W` = SOD-123, `B5819WS` = SOD-**323** — the smaller body, hence the 200 mW.
Anything in the repo that assumes SOD-123 is assuming ~2× the dissipation.

**Caveat on manufacturer, stated plainly:** `B5819WS` is a generic type number made by
MCC, Slkor, Jiangsu Changjing, Panjit and others. The schematic gives no manufacturer
and no footprint string — I grepped `sch.txt` for `SOD`, `0402`, `0603` and found
nothing. MCC is *a* legitimate source for this type number and its numbers are typical
of the type, but **which vendor Waveshare actually fitted is unknown.** I did not
reach a second vendor's copy for comparison (alldatasheet.com and the Changjing/TSC
routes were not pursued after the MCC document verified clean — two-route rule).

---

## 3. ME6217C33M5G LDO — **800 mA CONFIRMED as printed, but it is "guaranteed by design" and the SOT-23-5 package cuts it to ~350–500 mA**

Banked: `datasheets/other-semi/ME6217C33M5G.pdf`, sha256
`fb290308c013d99b28fadf015a3830800cedbae65ac977f0b7d7679bead9edd4`,
source `https://www.onwaytech.com/static/upload/file/20231009/1696841020308260.pdf`
(HTTP 200, 456 331 B, `%PDF-`). Microne / Nanjing Micro One **ME6217 series, V05, 13 pp**.
The exact ordering code **`ME6217C33M5G` appears in the ordering table** — that is why
I chose this copy over the LCSC C427602 upload (V02, 10 pp), which is the same series
document at an older revision and **lacks the thermal-resistance table entirely**.
I also hold that V02 copy (`wmsc.lcsc.com/…/1912111437_…_C427602.pdf`, 249 381 B) if a
cross-check is wanted; its 800 mA and dropout rows match verbatim.

### Repo's current belief

`[repo datasheets/MANIFEST.csv:35]` and `[repo datasheets/.manifest-R6.csv:7]`, in the
notes field of the **function-block PNG** row:
> "BACK = USB-C, BOOT, RESET, ESP32-S3, QMI8658C IMU, **ME6217C33M5G LDO (3.3V, 800mA max)**"

That is the whole of it — `grep -rn "ME6217\|800 mA\|800mA"` over
`docs/decisions hardware README.md ROADMAP.md config` returns **nothing**. The 800 mA
was read off a vendor marketing drawing, exactly as the brief said.

### Datasheet text, verbatim

> Features `[datasheet ME6217 V05 p.1]`:
> "**Maximum Output Current: 800 mA** （VIN≥VOUT(T)+1.0V）"
> "Dropout Voltage: **100mV @ IOUT =300mA, VOUT =5.0V**"
> "Operating Voltage Range: **2V～6.5V**" · "Highly Accuracy: ±1％"
> "Low Current Consumption: During Operation: **100uA（TYP.）**; During Shutdown: **0.1uA（TYP.）**"
> "Thermal Shutdown Protection：**160℃**"

> Selection guide `[p.2]`: "**ME6217C33M5G** … VOUT =**3.3V**； **with CE**；Package：**SOT23-5**"
> Pin assignment `[p.3]`, SOT23-5: 1 = VIN, 2 = VSS, 3 = CE, 4 = NC, 5 = VOUT.

> Absolute Maximum Ratings `[p.4]`:
> "Input Voltage VIN **6.5** V … Output Voltage VOUT Vss-0.3 ~ VIN +0.3 …
> **Output Current IOUT 800 mA** … Operating Ambient Temperature Range TOPR **-40 ~ +85 ℃** …
> Storage −55 ~ +150 ℃ … **Maximum junction temperature TJ −40~+150 ℃**"
> "Thermal resistance (Junction to air) … SOT89-3 **100** … SOT89-5 **100** …
> **SOT23-5 … θJA … 210 … ℃/W**"
> "Power Dissipation … SOT89-3 1.25 … SOT89-5 1.25 … **SOT23-5 … PD … 0.6 … W**"

> Electrical Characteristics, ME6217A33/ME6217C33, VIN = VOUT(T)+1.0 V, CIN=CL=10 µF, Ta=25 ℃ `[p.4]`:
> "Maximum Output Current … IOUTMAX **(Note 4)** … VIN≥ VOUT (T) +1.0V … Typ **800** … mA"
> "Load Regulation ΔVOUT, 1mA≤IOUT≤300mA, Typ **10**, Max **50** mV"
> "**Dropout Voltage VDIF (Note 3) … IOUT =300mA … Typ 100 … Max 180 … mV**"
> "Current consumption during operation ISS, no load, Typ **100**, Max **130** µA"
> "Shutdown current ISD, CE pin = OFF, no load, Typ **0.1**, Max **1.0** µA"
> "CE "High" Voltage VCEH … Min **1.5** V"  ·  "CE "Low" Voltage VCEL … Max **0.3** V"
> "Ripple Rejection Rate |RR| … IOUT=100mA, f=1kHz … Typ **65** dB"
> "**Short-circuit current Ishort, VOUT = 0 V, Typ 350 mA**"
> "Thermal Shutdown Protection Tsd, IOUT=1mA, VIN=VOUT+1V, **160 ℃**"

> **Note 4 `[p.6]`, verbatim and load-bearing:**
> "**IOUTMAX：Due to restrictions on the package power dissipation, this value may not
> be satisfied. Attention should be paid to the power dissipation of the package when
> the output current is large. This specification is guaranteed by design.**"

### Verdict, split three ways

**(a) "800 mA rating" — CONFIRMED as the printed number.** It is in Features `[p.1]`,
Absolute Maximum Ratings `[p.4]` and the electrical table `[p.4]`. The repo's PNG-derived
"800mA max" is not wrong about what the vendor prints.

**(b) …but it is NOT a tested guarantee — REFUTED as a usable ceiling.** Note 4 `[p.6]`
says in the vendor's own words that the number "may not be satisfied" and is
"guaranteed by design", i.e. not production-tested, and it is conditioned on
VIN ≥ VOUT+1.0 V. Treating 800 mA as available current on this board is wrong.

**(c) The SOT-23-5 package sets the real limit.** `[calc]`, from p.4:
θJA = 210 ℃/W, TJ(max) = 150 ℃, PD = 0.6 W. Cross-check: (150−25)/210 = 0.595 W ≈ 0.6 W,
so the two rows are consistent and derate together. On this board VIN is **VCC_5V**,
i.e. VBUS − V_F(B5819WS), so VIN ≈ 4.4–4.6 V, and VOUT = 3.3 V:

| VIN | V drop | P at I | I at P_D = 0.6 W, T_A = 25 ℃ | I at T_A = 60 ℃ (P = (150−60)/210 = 0.43 W) |
|---|---|---|---|---|
| 5.0 V | 1.70 V | 1.70 × I | **353 mA** | **252 mA** |
| 4.5 V | 1.20 V | 1.20 × I | **500 mA** | **357 mA** |

**So the 3V3 rail's real ceiling is ~350–500 mA at room temperature and ~250–360 mA
inside a warm instrument — not 800 mA.** Anything sizing the 3V3 rail against 800 mA
is over-budgeted by roughly 2×. Note the one small mercy: the diode drop *helps* here,
since a lower VIN means less dissipation in the LDO.

**(d) Dropout at the rated current — NOT-IN-DOCUMENT.** The only dropout spec is
**V_DIF at I_OUT = 300 mA: 100 mV typ, 180 mV max** `[p.4]`, for the C33 part. The
front-page headline "100mV@ IOUT=300mA, VOUT=5.0V" `[p.1]` is the C50's version of the
same 300 mA point. **There is no dropout figure at 800 mA, or at any current above
300 mA, anywhere in the 13 pages.** Any claim about dropout at 800 mA would be
extrapolation and should not be made.

**(e) Thermal resistance — CONFIRMED and new: θJA(SOT23-5) = 210 ℃/W, P_D = 0.6 W `[p.4]`.**
This row does **not exist** in the V02/10-pp copy that LCSC serves for C427602, whose
Absolute Maximum Ratings give only "Power Dissipation SOT-89-5 P_D 1000 mW" — a
*different package*. Had the V02 copy been banked, the obvious mis-read would be to
apply 1000 mW to a SOT-23-5 part and over-budget the rail by 67 %.

---

## Cross-cutting: the three parts are in series, and the weakest is the diode

`[calc]` Every milliamp the 64 LEDs draw passes through **D1 (B5819WS, 200 mW,
≈435 mA practical)**; the 3V3 subsystem then passes through **U? (ME6217C33M5G,
0.6 W, ≈500 mA practical)** behind that same diode.

| limit | value | source |
|---|---|---|
| ADR 0014's assumed full-field matrix draw | 960 mA | `[repo 0014-lighting.md:161,381]` — **wrong part** |
| Full-field at 12 mA/ch (WS2812B family) | **2304 mA** | `[calc]` from `[WS2812B-2020.pdf p.4]`, `[XL rev A p.5]` |
| Full-field at 19 mA/ch (XL rev B default) | **3648 mA** | `[calc]` from `[XL rev B p.1, p.5]` |
| B5819WS practical ceiling, T_A 25 ℃ | **≈435 mA** | `[calc]` from `[B5819WS p.2, p.4]` |
| B5819WS practical ceiling, T_A 60 ℃ | **≈283 mA** | `[calc]` |
| ME6217C33M5G practical ceiling (VIN 4.5 V, T_A 25 ℃) | **≈500 mA** | `[calc]` from `[ME6217 V05 p.4]` |

**The board cannot pass its own full-field current, by a factor of 5 to 13.** ADR 0014
reaches the right conclusion — a hard brightness cap — through a number that is
optimistic by 2.4× and a constraint (the 1 A R-78E5.0) that is not even the binding
one. The binding constraint is a 200 mW SOD-323 diode on the dev board itself, and it
is why the vendor's own wiki says, five times, not to turn the brightness up.

I have not edited ADR 0014 or `config/figures.yaml`; `matrix-led-current` should
remain **blocked** until someone measures the board or Worldsemi publishes an 0807
document, and the two new ceilings above deserve tracked entries of their own.

## Honest gaps

1. **No WS2812B-0807 datasheet exists publicly** (vendor catalogue negative, §1). The
   XINGLIGHT documents are a *different manufacturer's* 0807 part; they are banked under
   their own name, `XL-0807RGBC-WS2812B*.pdf`, and must never be cited as the fitted part.
2. **Which XINGLIGHT revision (12 mA vs 19 mA) matches the board is unknown**, and they
   also disagree on quiescent current by 7× (0.35 mA vs 2.5 mA). Measuring at E1 settles
   both at once and is now worth more than any further document hunt.
3. **B5819WS manufacturer is unconfirmed.** MCC's numbers are typical of the type; the
   schematic names no vendor and no footprint.
4. **V_F at 100 mA and 500 mA is graph-read**, not tabulated — `±0.03 V`, mark it weak.
5. **web.archive.org is down this session** (IA "Temporarily Offline" 503), so the
   Wayback route named in the brief was unavailable after the first CDX call.
