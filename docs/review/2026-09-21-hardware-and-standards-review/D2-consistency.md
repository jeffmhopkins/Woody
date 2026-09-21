# D2 — Cross-document consistency audit

**Date:** 2026-09-21. **Method:** cold. The reviewer read the whole design
corpus — `hardware/module/*.md` (6), `hardware/controller/*.md` (2),
`hardware/bom.csv` (119 rows), `docs/decisions/*.md` (14 + README),
`config/key-layout.yaml`, `docs/reference/latency-budget.md`,
`docs/reference/ks33-geometry.md`, `ROADMAP.md`, `README.md`,
`firmware/README.md` — and read **no** prior review or research document.

**Indexed by the fact in dispute, not by the document.** Every entry names
every file that states the fact and what each one says.

**Ranking**

| Rank | Meaning |
|---|---|
| **Showstopper** | Two documents specify incompatible hardware. Building from one gives a board the other does not describe |
| **High** | The same physical quantity carries different values |
| **Medium** | Wording implies a decision that has been superseded |
| **Low** | Stale phrasing, no functional effect |

**Headline:** 13 showstoppers, 40 high, 34 medium, 10 low. The deletion of the
**frame watchdog** and the **presence comparator** has landed in the ADRs, the
BOM's prose and three schematic sections — and **not** in the two drawings that
a board would actually be built from. `hardware/module/digital-and-supervision.md`
declares both parts deleted in its prose while its own schematic, its own rail
table and its own open-items list continue to build them.

---

## Summary table

| # | Fact in dispute | Files that disagree | What each says | Rank |
|---|---|---|---|---|
| **S1** | Does the module contain a 74HC123 frame watchdog? | `digital-and-supervision.md` (§circuit, §rails, §still-open) / `digital-and-supervision.md` (§"There is no frame watchdog") / `power-entry.md` / `bom.csv` R-CLR-PU / `bom.csv` PCB-MODULE / `bom.csv` C-DECOUPLE / `firmware/README.md` / ADR 0004 | Drawn `74HC123 / 5.21V rail / 1M × 220nF / ≈ 99 ms` · "**Deleted.**" · "the comparator and the watchdog stay on the LM317's 5.21 V" · "THE WATCHDOG IS DELETED (U-WATCHDOG, R-WDT, C-WDT all gone)" · board contains "watchdog" · "Was 22 with the 74HC123; the watchdog is deleted" · "When the module watchdog asserts `CLR`" · "Withdrawn 2026-09-21" | **Showstopper** |
| **S2** | Does the module contain an LM311 presence comparator? | `digital-and-supervision.md` (§circuit, §rails, §still-open) / `digital-and-supervision.md` (§"There is no presence detect either") / `power-entry.md` (rail list + LED section) / `bom.csv` C-DECOUPLE / `bom.csv` U-LVL-MOD, LED-PANEL / ADR 0004 / `breath-receive-stage.md` | Drawn `LM311 / ±12 V / EMIT→GND / 1M hyst` · "Deleted with the watchdog" · "OPA2197 ×6, INA828, LM311" and "**The LM311 itself runs on ±12 V**" · qty counts "LM311 on +/-12V = 2" · "that comparator is DELETED" · "**Both versions are deleted.**" · "if `R1` opens, the presence detect de-asserts" | **Showstopper** |
| **S3** | Is the DAC8568 `CLR` pin pulled up or down? | `digital-and-supervision.md` / `bom.csv` R-CLR-PU | `[R-CLR-PD 10k]` to `AGND` — a **pull-down on an active-low pin** · "Pull-up holding the DAC8568 CLR inactive" | **Showstopper** |
| **S4** | `C-FB-PITCH` value and which two nodes it spans | ADR 0006 / `pitch-stage.md` drawing / `pitch-stage.md` values table / `pitch-stage.md` split-loop table / `bom.csv` C-FB-PITCH | "**1 nF across the feedback resistor**" · `[C-FB-PITCH 1nF]` · "**2.2 nF C0G**… NOT 'across R2'" · "`C-FB-PITCH` 1 nF from the **op-amp output**" · "2.2nF … NOT 'across the feedback resistor'" | **Showstopper** |
| **S5** | Is `C-FILT-PITCH` fitted? | ADR 0006 / `pitch-stage.md` / `bom.csv` C-FILT-PITCH | "`C-FILT-PITCH` is deleted" · "**Restored** at the jack", 10 nF · row present, qty 1, "RESTORED" | **Showstopper** |
| **S6** | Is there a twin 1 kΩ in the instrument-side `AGND` leg (`R1b`)? | `breath-receive-stage.md` / `bom.csv` R-SER-BREATH-INST / `carrier.md` §2 drawing / `carrier.md` component table | "`R1b` … **Its twin in the `AGND` leg**", unretrofittable · qty **2**, "TWO, not one" · `AGND` runs straight to `J-UMB pin 2` with no resistor · one row, `1 kΩ`, no twin, no qty | **Showstopper** |
| **S7** | Is `R-ISO-REF` in the reference buffer loop? | `bom.csv` R-ISO-REF / `breath-receive-stage.md` / `carrier.md` §2 drawing / ADR 0003 power tree | row present, "INSIDE THE LOOP, with feedback taken at the SENSOR's VS pin" · "`R-ISO-REF` goes inside the loop … Instrument-side, so unretrofittable" · `[½ OPA2197 buffer]──┬── SKT-BREATH pin VS` — no resistor, no local feedback · `[REF5050 5.000V]──[OPA2197 ½ buffer]──┬── MPXV4006DP VS` | **Showstopper** |
| **S8** | Refdes and count of the instrument-side SPI series resistors | `bom.csv` R-SPI-SER / `carrier.md` §4 / `carrier.md` component table | one row `R-SPI-SER`, qty **3** · `R-SCLK-SER` / `R-MOSI-SER` / `R-CS-SER`, "only `R-MOSI-SER` reached the BOM, qty 1" · two of the three marked "proposed" | **Showstopper** |
| **S9** | Which rail the module's `CS` idle pull goes to | ADR 0004 / `bom.csv` R-SPI-PULL / `digital-and-supervision.md` | "**CS pulled to +5 V**" · "CABLE-SIDE CS PULLS TO 3V3, NOT +5V … DAC-SIDE CS PULLS TO AVDD" · `CS↑` with no rail named, on both sides | **Showstopper** |
| **S10** | The module panel LED's rail, resistor value and refdes | `power-entry.md` / `bom.csv` R-LED-PANEL / `bom.csv` LED-PANEL | `bus +5V ──[R-OE-PU 10k]` and `[R-LED 820R]` onto the LM311 collector · **`R-LED-PANEL` 2k2**, "~4mA from the module's **+12V analog rail**. Was 820R from bus +5V" · "A PLAIN POWER LED off the module's own rail" | **Showstopper** |
| **S11** | Mod-channel gain network: LT5400 1:4, or 10 k/30 k discretes? | ADR 0006 / `mod-channels.md` / `bom.csv` R-MODGAIN / `bom.csv` R-PRECISION | "**Gain of 4 is a 1:4 ratio**, which the LT5400 family offers directly — no external resistor" · `R2 30 kΩ 1 %`, `k = 3` · "10k / 30k 1% metal film", qty 8 · LT5400 "RATIO IS 1:1 … Two of four sections used" | **Showstopper** |
| **S12** | Is `LDAC` in the design? | `digital-and-supervision.md` / `bom.csv` R-LDAC | "**`LDAC` is not in this design anywhere** … **Tie it.**" — listed as *Still open*, not drawn · row present, qty 1, "Tied, not driven" | **Showstopper** |
| **S13** | Is the breath receive input held at 0 V by a pulldown? | ADR 0005 / ADR 0006 / ADR 0003 / `breath-receive-stage.md` / `bom.csv` R-BIAS-INAMP | "**Pull down the module's breath receive input** … One resistor" · "The receiver's differential pulldown holds it there" · "**The pulldown is deleted** and replaced by a common-mode bias return" · "The 100 kΩ differential pulldown \| **Deleted.**" · "REPLACES R-PD-BREATH" | **Showstopper** |
| **H1** | Instrument current drawn through the umbilical | ADR 0004 ×3 / ADR 0005 ×2 / ADR 0003 / `power-entry.md` / `bom.csv` R-KEY-PU | "~320 mA (45 module …, ~275 instrument) … a review put it nearer 410–430 mA"; "Drop at 290 mA"; "**~360 mA**"; "~400 mA that is 80 % of rating" · "359 mA"; "~630 mA" vs its own table's 579 mA · "~350 mA power return" · "360 mA of someone else's load" · "against a 360mA budget" | **High** |
| **H2** | The LM317 DAC rail voltage | ADR 0004 ×2 / ADR 0006 ×2 / ROADMAP E6 / `bom.csv` U-REG-DAC / everything else | "5.25 V" · "off the LM317's own 5.25 V", "its own 5.25 V regulator" · "local 5.25V DAC regulator" · "Adjustable LDO set to **5.25V**" · **5.21 V** in `power-entry.md`, `digital-and-supervision.md`, `pitch-stage.md`, `breath-receive-stage.md`, `breath-output-stage.md`, ADR 0003, ADR 0005, and `bom.csv` R-REG-SET's own arithmetic | **High** |
| **H3** | In-amp output at rest and at full sensor scale | `breath-receive-stage.md` drawing / same page's derivation / `breath-output-stage.md` / `bom.csv` U-DIFFRX / `digital-and-supervision.md` | "= 0 V at rest, **−9.6 V** at full" · "jack span **9.94 V**" · "Rest 0.00 V … Sensor full scale **−10.05 V**" · "Output is **-0.44V at rest** to **-10V** at full" · "(0 V absent, **−0.44 V alive**)" | **High** |
| **H4** | MPXV4006DP output span | ADR 0003 ×3 / ADR 0005 ×2 / `carrier.md` ×2 / `bom.csv` U-BREATH / `breath-receive-stage.md` / `breath-output-stage.md` | "~0.2–**4.80** V", "0.2–4.80 V", "0.2–4.80 V" · "outputting **0.2–4.7 V**", "reaches 4.7 V" · "Vout **0.2 – 4.7 V**", "full scale = **4.7 V** × 0.6" · "0.2-**4.7**V" · "0.2 → **4.8** V" · "**4.800** V" | **High** |
| **H5** | Marker bits / free bits split | ADR 0001 / `key-layout.yaml` fields / `key-layout.yaml` comment / `cluster-boards.md` / `carrier.md` §3 / ADR 0010 | "**6 marker → 8 marker, 5 free → 3 free**" · `spare_bits_marker: 8`, `spare_bits_free: 3` · "The **5** genuinely free bits are FLOATING CMOS INPUTS" · "**It now says 8 and 3**" · "**6** \| Marker pattern" and "**5** \| Genuinely free" and "Which **six** bits carry the marker … is still undecided" · "**Four to six** of the spare chain bits belong to the marker pattern … **Eight to ten remain**" | **High** |
| **H6** | Conductors leaving each cluster board / per hop | ADR 0001 diagram / ADR 0001 table / ADR 0001 prose ×2 / `key-layout.yaml` / `bom.csv` WIRE-LOOM / `bom.csv` PCB-CLUSTER / `cluster-boards.md` / `carrier.md` / ROADMAP | "**12 conductors per hop** (2x6 IDC)" · "**12 per hop** — **6 signals-and-supply, 5 grounds, 2 spare**" (= 13) · "loom width (**6 conductors per hop** …)" and "**six conductors** leave each cluster" · "**Six conductors** leave each board - VCC, GND, CLK, SH/LD, SER-in, QH-out" · "**TWELVE** conductors per hop" · "only **six** conductors leave each board" · "**six** signals leave the board instead of twenty-one" · "**12**" in the loom table · "**Six conductors per hop** rather than the 32–44" | **High** |
| **H7** | Number of `J-CHAIN` connectors | ADR 0001 / `bom.csv` J-CHAIN / `bom.csv` WIRE-LOOM / `carrier.md` / `cluster-boards.md` | "**Eight connectors** have to match, across five boards" · qty **8**, "EIGHT of them, not five" · "so **five connectors** must match: one on the carrier and one per cluster board" · "**EIGHT connectors, not five.**" · "7 chain connectors — **plus one more … eight in all**" | **High** |
| **H8** | Time to read the 32-bit key chain | `latency-budget.md` key path / `latency-budget.md` rule 1 / ADR 0001 / `carrier.md` | "74HC165 chain read \| **< 10 µs** via SPI DMA" · "key chain **16 µs**" · "Full chain reads in **~32 µs** at 1 MHz" · "SPI3 keys 32 bits @ 1.0 MHz = **32.0 µs**" | **High** |
| **H9** | SAR ADC conversion time | `latency-budget.md` / ADR 0003 | "**~24 µs** … **This row said 50–200 µs**, which is a generic SAR allowance" · "SAR ADC conversion \| **~50–200 µs**" — unchanged | **High** |
| **H10** | GPIO broken out on the ESP32-S3-Matrix | ADR 0007 / ADR 0009 / `carrier.md` / `bom.csv` HDR-SERVICE / `bom.csv` U-MCU-RT / ADR 0001 | "**17 GPIO**… **Seventeen, not sixteen**" · "three power and **seventeen** GPIO" · "3 power and **17** GPIO" · "3 power + **17** GPIO" · "**16 GPIO** broken out (1-7, **34**-40, 43, 44)" — omits GPIO33 · "Two extra pins against **sixteen** of headroom" | **High** |
| **H11** | Broken-out pins the real-time role needs | ADR 0007 / ADR 0013 table / ADR 0013 prose ×2 / ADR 0014 / `bom.csv` U-MCU-RT | "**Used \| 14 of 17**" · "**Total on the chip \| 18 of ~30 \| 14 broken out**" · "**Fourteen** chip pins of headroom" (30 − 18 = 12) and "not expected at **13 pins** and one job" · "roughly 17 broken out and **12 needed**" · "vs **14** needed" | **High** |
| **H12** | Is GPIO33 spare or driving the chain's `SER`? | ADR 0007 / `carrier.md` §3 / `cluster-boards.md` / `bom.csv` R-SER-TERM | "GPIO 3, 4 and **33 stay free**", "spare: 3, 4, 33" · "**IO33** SER out ──[R-CHAIN-SER 100R]────► 6 SER" · "If firmware *does* drive **`IO33`**" · "if firmware instead DRIVES it from the carrier's **IO33**" | **High** |
| **H13** | Number of LEDs on the side strips | ADR 0014 (decision) / ADR 0014 (table) / `bom.csv` LED-SIDE / `carrier.md` §5 | "**60/m.**" — decided · "60/m (**50 LEDs**)" / "30/m (25 LEDs)" · "WS2815 … **60/m**, 1m reel … two 420mm side runs" · "sends it to **25 addressable LEDs** on a 12 V rail" | **High** |
| **H14** | Key input network values | ADR 0001 / `cluster-boards.md` / `carrier.md` / `bom.csv` R-KEY-PU/C-KEY / **ADR 0009** | "**2.2 kΩ** to 3V3, 100 Ω in series, **47 nF**" · "R-KEY-PU 2k2 … C-KEY 47 nF" · "2.2 kΩ/100 Ω/47 nF" · 2k2 / 47nF · "**10 kΩ, 100 Ω and 10 nF** per switch position on the cluster boards (ADR 0001)" | **High** |
| **H15** | Key-network press/release time constants | ADR 0001 / `cluster-boards.md` / `bom.csv` C-KEY / **`bom.csv` R-KEY-SER** | "Press … **5.7 µs**", "Release … **125 µs**" · same · "Press crosses … in **~5.7us** … Release crosses VIH at **~125us**" · "press is **~1us (100R x 10nF)** … release is **~93us (10k x 10nF)**" | **High** |
| **H16** | Load-switch start time, dissipation and energy | `power-entry.md` / `bom.csv` C-TIMER-LOADSW / ADR 0005 / `bom.csv` U-LOADSW | "1.0 A into 2.2 mF to 12 V is **26 ms**… **Timer ≈ 50 ms**… survive **12 W for 50 ms — 0.6 J**" · "outlast a current-limited start into … 2.2mF (**26ms**) … **12W x t**" · "**in about 75 ms** of constant-current start … a fault timer longer than it" · "A 1.0A ramp at ~6V mean for **75ms** is **~6W and 0.45J**" | **High** |
| **H17** | Clamp-legal worst case on the umbilical | ADR 0005 table / ADR 0005 prose | "Clamp-legal worst … **579 mA**" · "set from below, by the clamp-legal worst case of **~630 mA**" | **High** |
| **H18** | Pitch static error budget, per term | `pitch-stage.md` table A / `pitch-stage.md` table B (same section) / ADR 0006 / `bom.csv` R-PRECISION | DAC ref **0.42 cents**, LT5400 **0.027**, TRIM-GAIN **0.068** · DAC ref **~0.5 cents**, LT5400 **~0.1 cents** · DAC ref **0.54 cents**, matched network **0.11 cents**, discretes **5.40** · "0.42 … against **0.027** for the LT5400 and **0.38** for two 0.1%/10ppm discretes" | **High** |
| **H19** | Mod offset channel: voltage and write policy | ADR 0006 table row / ADR 0006 update-rate table / `mod-channels.md` / `firmware/README.md` / `latency-budget.md` | "Shared **3.3333 V** offset for mod 1–4" · "Mod offset \| **written once at boot** \| The shared **2.5 V** reference point" · "**3.3333 V** from DAC ch7" · "**3.3333 V** … written once at boot … *(The value changed …)*" then "refresh all six populated channels every pass" · "the loop refreshes the mod offset every pass rather than writing it once" | **High** |
| **H20** | Current the mod reference buffer drives | `mod-channels.md` drawing / `mod-channels.md` §"One buffer, four loads" | "(**~1.3 mA** total into 4 × 10k)" · "At **2.5 V** into 2.5 kΩ that is **1 mA**" | **High** |
| **H21** | Pitch jack voltage at rack power-on | ADR 0006 / `pitch-stage.md` / ADR 0004 | "Pitch \| Bottom of its range, **below −2 V** \| Subsonic" · "**Power-on is 0.000 V, not 'subsonic'** … ADR 0006's power-on table asserts 'below −2 V' for both; they are different states, 2.5 V apart" · "clears to zero scale, which parks pitch **subsonic**" | **High** |
| **H22** | Which DAC grades are acceptable | ADR 0006 / `bom.csv` U-DAC / ADR 0004 | "**Not 'A or C'** … Only C satisfies both requirements" · "**GRADE LOCKED TO C**" · "an **A/C grade** part clears to zero scale" | **High** |
| **H23** | Channels refreshed down the umbilical | ADR 0003 / ADR 0004 / `latency-budget.md` / `bom.csv` U-DAC | "**Breath analog, 7 channels at 4 kHz** \| **0.90 Mbit/s**" and "the loop refreshes **seven**" · "**Breath analog, 6 channels at 4 kHz** \| **0.77 Mbit/s**" and "Seven channels were populated until the breath ambient-zero was deleted" · "Six 32-bit words at 2 MHz" · "Populate **6** of 8" | **High** |
| **H24** | Umbilical SPI clock | ADR 0004 §"What goes over the cable" / ADR 0004 §"Revised conductor budget" / everywhere else | "SCLK, MOSI, CS      SPI to the DAC, **~2 MHz**" · "SCLK / DIG_GND     SPI to the DAC, **~1 MHz**" · 2 MHz in ADR 0003, ADR 0006, `latency-budget.md`, `carrier.md`, ROADMAP E11 | **High** |
| **H25** | Series resistor value on the umbilical SPI lines | ADR 0004 §decision / ADR 0004 §deadline / `carrier.md` / `bom.csv` R-SPI-SER | "**220 Ω** in series on MOSI at the driving end" · "transmission-line analysis puts the right value nearer **68 Ω**" · "**220 Ω** … corrected text puts the transmission-line-right value nearer **68 Ω**" · part is "**220R**", note says "transmission-line analysis says **~68R**" | **High** |
| **H26** | Instrument mass | ADR 0009 §Mass (first) / ADR 0009 §Mass (second) | "**2.25 in** \| **~778 g (1.72 lb)**" · "**Total** \| **~825 (1.8 lb)**" — for the same 2.25 in build | **High** |
| **H27** | OPA2197 output swing on ±12 V | ADR 0004 / `bom.csv` U-OPA-PITCH / ADR 0005 / ADR 0006 / `pitch-stage.md`, `mod-channels.md` / `breath-output-stage.md` | "on ±12 V it reaches roughly **11.9 V**" · "RRIO on +/-12V reaches **~11.9V**" · "swings to roughly **+11.5V**" · "an OPA2197 reaches **~±11.45 V**" · "less two Schottky drops reaches **~±11.45 V**" · "stops at about **±11.5 V**" | **High** |
| **H28** | Module decoupling cap count | `bom.csv` C-DECOUPLE qty / its own arithmetic | qty **21** · "6 x OPA2197 … = 12, INA828 = 2, **LM311 on +/-12V = 2**, DAC8568 … = 2, 74AHCT125, LT1641 VCC, LM317 in" — counts a part the same file says is deleted; without it the sum is **19** | **High** |
| **H29** | `R-OUT-PROT` power rating | `bom.csv` R-OUT-PROT / `breath-output-stage.md` / `mod-channels.md` / `pitch-stage.md` | "1k 1%, **>=500mW**" · "1 kΩ, 1206 **≥500 mW** \| Shared spec with the other five outputs" · `[R-OUT-PROT 1k, 1206]` · "1 kΩ 1 %, **1206 ≥250 mW**" | **High** |
| **H30** | Output-loop duty at 4 kHz | `latency-budget.md` / `carrier.md` | "ADC 24 µs + key chain 16 µs + six DAC channels … = **136 µs** … **54 % duty**" · "SPI2 total = **122.7 µs** of 250 µs → **49 %**. SPI3 keys … **32.0 µs, concurrent → 13 %**" | **High** |
| **H31** | Buck switching frequency used in the alias argument | ADR 0003 / `bom.csv` C-AA-ADC / `carrier.md` | "A buck running at **500 kHz** … at **496.1 kHz** to 100 Hz … **58 dB at 500 kHz**" · "the R-78E5.0 switches at **330kHz not 496kHz**. **55dB at 330kHz**" · "the R-78E5.0's **~330 kHz** switching rate = **55 dB**" | **High** |
| **H32** | Where the breath channel is band-limited | ADR 0003 / `carrier.md` / `bom.csv` R-SER-BREATH-INST / `breath-receive-stage.md` | "**Band-limit at both ends**, around 500 Hz" · "**There is no band-limit capacitor at the instrument end** … **Do not add a cap at `R-SER-BREATH-INST`**" · "Series protection on the breath buffer output" — no cap · "**ahead of the in-amp**" only | **High** |
| **H33** | Location of the analog ground star point | ADR 0003 ×2 / `carrier.md` §2 | "the analog ground pour on the **bottom cluster board**, at the sensor and reference" and "Everything analog … sits on **that one board**" · "**a board that does not exist**; it means this one" | **High** |
| **H34** | Breath path total latency | ADR 0003 table / ADR 0003 prose ×2 / `latency-budget.md` table / `latency-budget.md` prose | "**Total \| < 1.5 ms**" · "**~3.1 ms**" and "from ~1.5 ms to **~2.6 ms**" · "**~2.83 ms** + restrictor" (analog) and "**~2.9–3.1 ms**" (digital) · "**2.80 ms** against a 5 ms target" | **High** |
| **H35** | `HDR-DEV` quantity | `bom.csv` HDR-DEV / `carrier.md` | qty **6** — "2 strips for the ESP32-S3-Matrix, 2 for the T-Display-S3 AMOLED, 2 spare" · "**Qty is one board's worth, not two** — the display board is 360 mm away" | **High** |
| **H36** | Spare LT5400 sections and what they can build | `pitch-stage.md` §values / `pitch-stage.md` §still-open (twice) / `mod-channels.md` / `bom.csv` R-PRECISION | "the other two are spare" · "The claim that two spare sections can build the mod channels' 1:3 is **arithmetically impossible**" *and*, six lines later, "**The two spare LT5400 resistors** … Worth a look when the mod channels are laid out" · "a 1:3 ratio that **three sections of an LT5400 give directly against the fourth**" · "Two of four sections used" | **High** |
| **H37** | Spare gates on the 74AHCT125 | `bom.csv` U-LVLSHIFT / `bom.csv` R-LED-SER / `carrier.md` §5 / ADR 0004 | "**Two spare gates.**" · qty **4**, "**FOUR not two** … the level shifter's two spare gates are exactly what it needs" (→ zero spare) · "**all four gates are used, none spare**, against the BOM's 'Two spare gates'" · "with a spare gate left over" | **High** |
| **H38** | Number of key switches to buy / fit | `bom.csv` SW1-n / ADR 0010 / `key-layout.yaml` / `cluster-boards.md` | qty **21** ("18 keys + 3 spares") · "**18 switches**, decided" · `total: 18` · per-board table sums to **18**; "18 fitted switches in **21 networked positions**" — the 3 extra switches are allocated to no board | **High** |
| **H39** | Mod-channel output span | `mod-channels.md` §adopted / `mod-channels.md` §range / `mod-channels.md` tolerance table / ADR 0006 | "lands on **exactly ±10.000 V**" · "**±10.05 V** uses the DAC's *full* 0–5 V span" — present tense, describing the deleted four-resistor version · "Span \| **19.703–20.303 V**" · "**−10…+10V**" | **High** |
| **H40** | `C-OUT-BREATH` corner | `breath-output-stage.md` / `breath-receive-stage.md` / ADR 0006 / `bom.csv` C-OUT-BREATH / `latency-budget.md` | "**~482 Hz**" · "~**480** Hz reconstruction at the jack" · "~**480 Hz**" · "**~480Hz** with R-OUT-PROT" · "Output RC at the jack, **480 Hz**" | **Low→High**, see §H40 |
| **M1–M34** | see [Medium](#medium) | | | **Medium** |
| **L1–L10** | see [Low](#low) | | | **Low** |

---

## Showstoppers

### S1 — The frame watchdog is deleted in prose and built in the drawing

`hardware/module/digital-and-supervision.md` is the page a module would be
stuffed from. Its schematic block draws the part:

> ```
> │        ┌──────────────┐    buffered CS       │ │
> │        │  74HC123     │◄───(DAC side)        │ │
> │        │  5.21V rail  │                      │ │
> │        │  1M × 220nF  │──────Q───────────────┘ │
> │        │  ≈ 99 ms     │                        │
> │        └──────────────┘                        │
> ```

Its rail table allocates a supply to it:

> | **LM311, 74HC123** | **LM317 5.21 V / ±12 V** | Supervision must not die with the rail it supervises |

and

> | DAC AVDD | **LM317 5.21 V** | Same rail as the watchdog, so `CLR` levels are unambiguous |

Its *Still open* list asks for work on it:

> - **A power-on reset RC on the '123's own `CLR`**, so the power-up safe state is
>   guaranteed rather than probable.
> - **The retrigger question was posed against the wrong numbers.** Six frames
>   per pass means **~2400 retriggers per timeout at ~16 µs intervals** …
>   The real gates are the '123's discharge `R_on` …

Eighty lines above all of that, the same file says:

> ## There is no frame watchdog
>
> **Deleted.** A 74HC123 monostable used to assert the DAC's `CLR` when SPI
> traffic stopped. The part, its timing pair and its decoupling are gone; `CLR`
> is pulled **inactive**, with a solder pad beside it so it can be asserted by
> hand.

`hardware/bom.csv` agrees the part is gone and has **no row** for it:

> `R-CLR-PU` — "THE WATCHDOG IS DELETED (U-WATCHDOG, R-WDT, C-WDT all gone), so CLR has no driver and is tied INACTIVE - pulled high."

> `C-DECOUPLE` — "Was 22 with the 74HC123; the watchdog is deleted"

But the BOM's own board description still contains it:

> `PCB-MODULE` — "DAC, scaling, jacks, power entry, load switch, **watchdog**"

`hardware/module/power-entry.md` still powers it:

> The **comparator and the watchdog stay on the LM317's 5.21 V** so that a bus
> rail failure cannot take the supervision with it.

`firmware/README.md` still reasons from it as a live mechanism:

> When the module watchdog asserts `CLR`, every DAC channel including channel 7
> goes to zero scale.

ADR 0004 is correct — the mechanism is struck through under a "**Withdrawn
2026-09-21**" banner — but its unstruck sub-section "The watchdog's scope is the
DAC channels, and breath is outside it" is cited as live by two other files
(`breath-receive-stage.md` §"What the jack does when the watchdog fires",
ROADMAP E10). A part with no BOM row, drawn on the schematic, with a rail
allocated and open design questions attached, is buildable by accident.

### S2 — The presence comparator is deleted in prose and built in two drawings

Same file, same shape. The schematic draws it:

> ```
> │   in-amp output ──┐                            │
> │   (0 V absent,    │   ┌──────────┐             │
> │    −0.44 V alive) └───┤ LM311    │             │
> │                       │ ±12 V    │             │
> │   threshold −200 mV ──┤ EMIT→GND ├──collector──┤
> │   (from −12 V)        │ 1M hyst  │             │
> ```

and the same file says:

> ## There is no presence detect either
>
> Deleted with the watchdog, and for converging reasons.

> **`OE` is tied enabled**, which is what every surveyed Eurorack module does.

Yet its *Still open* list keeps four items that only exist if the comparator
does:

> - **The presence tap point**, above. It needs the one-line change described and
>   a corrected `R-PRESENCE` row.
> - **The threshold may sit inside the breath signal's own range.** …
> - **The clean answer may be to demote this comparator to LED and health duty**

`R-PRESENCE` has **no row in `bom.csv`**, and neither does the LM311.

`hardware/module/power-entry.md` places it on a rail and gives it its own
paragraph:

> ```
>   +12V ├───┬──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V
>        │   │                                  │   OPA2197 ×6, INA828, LM311
> ```

> **The LM311 itself runs on ±12 V**, not on 5.21 V — it has to resolve a signal
> near 0 V, and a comparator on a single positive supply cannot, which is
> precisely and only why the LM393 was rejected.

`bom.csv` buys decoupling for it (see **H28**):

> `C-DECOUPLE` — "6 x OPA2197 on +/-12V = 12, INA828 = 2, **LM311 on +/-12V = 2**, DAC8568 AVDD+DVDD = 2, …"

against `bom.csv` `LED-PANEL`:

> "It used to be driven by a presence comparator that watched the breath line -
> **that comparator is DELETED**"

and `bom.csv` `U-LVL-MOD`:

> "**OE IS TIED ENABLED.** The presence-gated OE is deleted along with its comparator"

and ADR 0004 §"There is no presence detect, and the buffer runs unconditionally":

> **Both versions are deleted.**

`breath-receive-stage.md` also still argues from it as a live circuit:

> Two consequences nobody had written down: if `R1` opens, **the presence detect
> de-asserts and takes the whole SPI link with it**, so pitch and the mods die
> with breath

That consequence cannot happen — `OE` is tied enabled — so a stated failure
mode of an instrument-side, unretrofittable resistor is fictional.

### S3 — `CLR` is pulled the wrong way in the schematic

`hardware/module/digital-and-supervision.md`:

> ```
> │                   │   CLR ◄───────────────┼─┐ │
> │                   └───────────────────────┘ │ │
> │                                   │          │ │
> │                          [R-CLR-PD 10k]      │ │
> │                                   │          │ │
> │                              AGND ┘          │ │
> ```

`hardware/bom.csv`:

> `R-CLR-PU`,module,10k 1%,,"**Pull-up** holding the DAC8568 CLR inactive, with a bring-up pad"

`CLR` on a DAC8568 is active low. The drawing's `R-CLR-PD` to `AGND` asserts
clear permanently; the BOM's `R-CLR-PU` holds it inactive. The two documents
give the part opposite refdes *and* opposite polarity, and the drawing's version
produces six dead outputs.

### S4 — `C-FB-PITCH` is specified three ways, one of which the corpus calls dangerous

`docs/decisions/0006-cv-channel-allocation.md`:

> **Adopted.** Pitch now closes its DC loop at the jack, with `C-FB-PITCH` (**1 nF
> across the feedback resistor**) taking the loop back to the op-amp output above
> ~16 kHz

`hardware/module/pitch-stage.md` — the drawing:

> ```
>                               ├──[C-FB-PITCH 1nF]──────────┤   ← AC feedback
> ```

— the split-loop table:

> | `C-FB-PITCH` **1 nF** from the **op-amp output** | above ~16 kHz | …

— and the values table, twenty lines later:

> | **C-FB-PITCH** | **2.2 nF C0G** | **From the op-amp OUTPUT to the (−) input — NOT "across R2".** …

with the page's own boxed warning:

> > **Not "across the feedback resistor".** With the tap at the jack, `R2` spans
> > *jack → (−)*, so a capacitor across `R2` connects the same two nodes and
> > leaves `R-OUT-PROT` inside the loop at every frequency — which is the
> > capacitive-load-in-the-loop case, at **18° of phase margin with 2 m of cable
> > and under 10° with four destinations.**
> >
> > … Three other places said "across the feedback resistor" and were wrong, and
> > prose is what a layout gets built from.

`hardware/bom.csv` sides with the values table:

> `C-FB-PITCH`,module,**2.2nF** C0G/NP0,,"Compensation cap, op-amp OUTPUT to the inverting input" … "Three documents said 'across R2' and were wrong."

ADR 0006 is one of the three documents that "said 'across R2' and were wrong",
and it has not been corrected. Two numbers (1 nF, 2.2 nF) and two nets, inside
the one page that says this net "decides whether the stage is stable".

### S5 — `C-FILT-PITCH` is deleted and restored

ADR 0006:

> `C-FILT-PITCH` is deleted: a capacitor to ground at the jack would now sit
> inside the DC loop at exactly the handover.

and its filter table lists only `C-AA-PITCH` for pitch:

> | Pitch | `R-OPAMP-IN` 1 kΩ, **ahead of the stage** | 10 nF C0G | 15.9 kHz |

and:

> **Pitch is now the exception** — its feedback is tapped at the jack, so that
> node is the feedback node and **carries no capacitor at all**.

`hardware/module/pitch-stage.md`:

> | **C-FILT-PITCH** | **10 nF C0G** | Restored at the jack. The low-impedance shunt at the connector, which nothing else provides |

> - **`C-FILT-PITCH`**, 10 nF back at the jack. **The reason given for deleting
>   it does not survive** …

`hardware/bom.csv` has the row:

> `C-FILT-PITCH`,module,10nF C0G/NP0,,Reconstruction and RF shunt at the pitch jack,…,1,candidate … "**RESTORED.**"

ADR 0006 also still carries, in the same section, a table row describing the
deleted part in the present tense:

> | Cap to ground **at the jack**, after the series R | What this design **currently specifies** | Safe, but see below |

### S6 — `R1b` exists on the module page and the BOM, and not on the board that carries it

`hardware/module/breath-receive-stage.md`:

> | **R1b** | 1 kΩ 1 %, 1206 | **Its twin in the `AGND` leg.** Free, and it is what keeps CMRR from collapsing |

> **`R1b` fixes it for nothing.** … One resistor, instrument-side, and therefore
> **unretrofittable**.

`hardware/bom.csv`:

> `R-SER-BREATH-INST`,**controller**,1k 1%, 1206 >=250mW,…,**2** … "**TWO, not one**, and 1206 not 0805 - both changed with the schematic and this row did not follow. R1 in the BREATH leg, **R1b its twin in the AGND leg** … Both are instrument-side and **UNRETROFITTABLE**"

`hardware/controller/carrier.md` §2 — the schematic for that board — draws one:

> ```
>                      ├──[½ OPA2197 buffer]──┬──[R-SER-BREATH-INST 1k]── J-UMB pin 1
>                      │   (V+ = +12V)        │                            BREATH
> …
>   J-UMB pin 2 AGND ──┴── analog star point ──[single tie]── PWR_GND
> ```

and its component table lists one, singular, with no quantity:

> | `R-SER-BREATH-INST` | 1 kΩ | Output protection. **No series cap here** | `[repo]` |

The whole 60 dB CMRR budget rests on this part (`breath-receive-stage.md`:
"That is the **entire** 60 dB budget, spent by one unmatched resistor"), and the
page that would be laid out does not have it.

### S7 — `R-ISO-REF` is in the BOM and in neither schematic

`hardware/bom.csv`:

> `R-ISO-REF`,controller,10R 1%,,Isolation resistor inside the REF5050 buffer's feedback loop,…,1 … "**INSIDE THE LOOP**, with feedback taken at the **SENSOR's VS pin** … Without it the follower drives 100nF + 10uF directly: a 21kHz pole inside a loop crossing at MHz."

`hardware/module/breath-receive-stage.md` §"The instrument-side reference buffer
is not stable as connected":

> **`R-ISO-REF` goes inside the loop**, with feedback taken at the sensor's `VS`
> pin … **Instrument-side, so unretrofittable.**

`hardware/controller/carrier.md` §2 draws the unstable arrangement:

> ```
>   +12V ──[REF5050]── 5.000 V ──┬──[½ OPA2197 buffer]──┬── SKT-BREATH pin VS
>              │                 │                      │
>         [C-REF-OUT 10 µF]  [100 nF]                   │   U-BREATH MPXV4006DP
> ```

and ADR 0003's power tree does the same:

> ```
> umbilical +12V ──[REF5050 5.000V]──[OPA2197 ½ buffer]──┬── MPXV4006DP VS
> ```

Neither shows the resistor nor the feedback tap at `VS`. `carrier.md`'s
component table has no `R-ISO-REF` row at all, and `C-REF-OUT`'s entry there
still asks the question the stability analysis answered:

> | `C-REF-OUT` | 10 µF ×2 | **Qty 2 for one part — say whether that is parallel or in+out** | `[repo]`, ambiguous |

### S8 — Three refdes in the schematic, one different refdes in the BOM

`hardware/controller/carrier.md` §4:

> ```
>   IO35 SCK  ──[R-SCLK-SER 220R]──┬──── J-UMB pin 7   ** R PROPOSED **
>   IO36 MOSI ──[R-MOSI-SER 220R]──┼──── J-UMB pin 4
>   IO34 CS   ──[R-CS-SER  220R]───┼──── J-UMB pin 5   ** R PROPOSED **
> ```

> **`R-SCLK-SER` and `R-CS-SER` are new.** … only `R-MOSI-SER` reached the BOM,
> **qty 1** `[repo] bom.csv`.

`hardware/bom.csv` has none of those three refdes. It has:

> `R-SPI-SER`,controller,220R 1%,,Series termination on SCLK, MOSI and CS at the driving end,…,**3** … "**THREE, not one.** SCLK had NONE and it is the fastest edge on the cable"

So: the schematic references three parts that do not exist in the BOM; the BOM
contains one part that appears in no schematic; and the schematic's statement of
what the BOM contains is wrong. The carrier page's component table compounds it
by marking two of them "proposed".

### S9 — The `CS` idle pull goes to three different rails

ADR 0004:

> - **CS pulled to +5 V; SCLK and MOSI pulled to ground**, at the module end.

`hardware/bom.csv` `R-SPI-PULL`:

> **CABLE-SIDE CS PULLS TO 3V3, NOT +5V**: pulled to 5V it drives 430uA
> continuously through the unpowered ESP32's input clamp in the design's NORMAL
> resting state, and the node sits at ~0.7V so 'CS idle high' is not even
> achieved. **DAC-SIDE CS PULLS TO AVDD (the LM317's 5.21V), not bus +5V**

`hardware/module/digital-and-supervision.md` draws both sets and names no rail
for either:

> ```
>             │      [R-SPI-PULL ×3]        ┌────┴─────────┐
>             │       SCLK↓ MOSI↓ CS↑       │  74AHCT125   │
> …
>             │                           [R-SPI-PULL ×3]     │
>             │                            SCLK↓ MOSI↓ CS↑    │
> ```

> Polarity is the same on both sides: `CS` up, `SCLK` and `MOSI` down.

Three candidate rails (3V3 via the cable, bus +5 V, LM317 5.21 V), and the
schematic silent. The BOM's own note says the ADR's choice fails in the
design's normal resting state.

### S10 — The module panel LED is two different circuits

`hardware/module/power-entry.md` §"The panel LED sits on the buffer's rail":

> Both loads now pull up to the **74AHCT125's own bus +5 V**:
>
> ```
>   bus +5V ──┬──[R-OE-PU 10k]────────┬── OE ×4 (active low)
>             │                       │
>             └──[R-LED 820R]──▷|─────┘
>                             LED      │
>                                      └── LM311 collector (emitter at GND)
> ```
>
> `(5.21 − 2.0) / 4 mA ≈ 800 Ω → 820 Ω`, and on the 5 V rail it is ~3.8 mA.

`hardware/bom.csv`:

> `R-LED-PANEL`,module,**2k2** 1%,,Series resistor for LED-PANEL,…,1 … "~4mA from the module's **+12V analog rail**. **Was 820R from bus +5V** when it shared a node with the level shifter's OE pins; **that node is gone with the comparator**"

Two different rails, two different resistor values, two different refdes
(`R-LED` vs `R-LED-PANEL`), and `R-OE-PU` has no BOM row at all. The same
`power-entry.md` section is the one that says "**Drawing this found a bug**"
about the LED's pull-up rail — the fix it describes is itself now superseded.

### S11 — Mod channels: LT5400 1:4 ratio vs 10 k/30 k discretes

ADR 0006:

> - **Gain of 4 is a 1:4 ratio**, which the LT5400 family offers directly — no
>   external resistor, so no absolute tempco leaks into the gain.

`hardware/module/mod-channels.md` opens by naming the contradiction and then
building the other thing:

> ADR 0006 specifies `Vout = 4 × (Vdac − 2.5 V)` and contradicts itself about how
> to build it — the topology section offers an LT5400 1:4 ratio, the calibration
> section says ordinary 1 % discretes. The discretes won (ADR 0006, `R-MODGAIN`)

> | **R2** | **30 kΩ 1 %** | Feedback. `k = 3`, gain `1 + k` = **exactly 4** |

`hardware/bom.csv`:

> `R-MODGAIN`,module,**10k / 30k 1% metal film**,…,8 — "EIGHT, not sixteen"
>
> `R-PRECISION`,module,LT5400 **1:1** quad … "**Two of four sections used.**"

ADR 0006 is the ADR of record and still specifies a part configuration nothing
else in the corpus builds.

### S12 — `LDAC` is "not in this design anywhere" and has a BOM row

`hardware/module/digital-and-supervision.md` §Still open:

> - **`LDAC` is not in this design anywhere**, which leaves a CMOS input floating
>   on the DAC and means six channels cannot update atomically. **Tie it.**

`hardware/bom.csv`:

> `R-LDAC`,module,10k 1%,,Ties the DAC8568 LDAC pin to its inactive level,…,1 … "LDAC appeared NOWHERE in the design … **Tied, not driven**: a hardware LDAC was considered and declined"

The part is bought and the decision recorded; the module's digital schematic
still lists it as an unresolved gap and does not draw the net.

### S13 — The breath pulldown is deleted and still specified in two ADRs

ADR 0003:

> **The pulldown is deleted and replaced by a common-mode bias return.**

`hardware/module/breath-receive-stage.md`:

> | The 100 kΩ differential pulldown | **Deleted.** R4/R5 do its job without its 1–17 % attenuation |

`hardware/bom.csv`:

> `R-BIAS-INAMP`,module,1M 1% … "**REPLACES R-PD-BREATH.**"

ADR 0005 still prescribes it as a part to fit:

> **Pull down the module's breath receive input**, so that an instrument which is
> switched off — or unplugged — presents 0 V rather than a floating buffer output.
> **One resistor**, and it means powering down the instrument silences the patch

ADR 0006 still relies on it for a power-on guarantee:

> | **Breath** | 0 V | **The receiver's differential pulldown holds it there** (ADR 0003) |

The replacement (`R4`/`R5`, 1 MΩ to module analog ground) is a *bias return*,
not a pulldown to 0 V at the jack — ADR 0006's power-on table asserts a
behaviour the deleted part provided.

---

## High

### H1 — Instrument umbilical current: seven different numbers

- ADR 0004: "| +12 V | **~320 mA** (45 module incl. the DAC regulator, **~275 instrument**) — **estimated, and a review put it nearer 410–430 mA**."
- ADR 0004, same section: "| 2.2 Ω | 0.64 V |" under "Drop at **290 mA**".
- ADR 0004 §Grounding: "| `PWR_GND`, from the etherCON | **~360 mA** of instrument current |".
- ADR 0004 §etherCON: "Against an instrument drawing **~400 mA** that is 80 % of rating, on a figure that has already moved twice."
- ADR 0005 load table: "| Typical play | 226 mA | 248 mA | **359 mA** | 4.1 W |" and "| **Clamp-legal worst** | 928 mA | 119 mA | **579 mA** |".
- ADR 0005 prose: "it is set from below, by the clamp-legal worst case of **~630 mA** plus ramp current".
- ADR 0003: "They divert tens of nanoamps against a **~350 mA** power return".
- `power-entry.md`: "no published Eurorack design passes **360 mA** of someone else's load through its entry diode" and "at **360 mA** typical: 18 mV drop, 6 mW".
- `bom.csv` `R-KEY-PU`: "1.5mA per PRESSED key against a **360mA** budget".

`power-entry.md` sizes `R-ILIM` and the FET against 360 mA; ADR 0005 sizes the
1.0 A limit against 630 mA; ADR 0004 says the number is "the least trustworthy
number in this document" and then uses four values of it.

### H2 — The LM317 DAC rail is 5.25 V in five places and 5.21 V in ten

5.25 V: ADR 0004 "A local **5.25 V** regulator off the protected +12 V rail" and
its power tree "`[LM317LZ 5.25V]`"; ADR 0006 "`VREFOUT` is a 2.5 V reference
inside the part, off the LM317's own **5.25 V**" and "The DAC runs from its own
**5.25 V** regulator"; ROADMAP E6 "local **5.25V** DAC regulator"; `bom.csv`
`U-REG-DAC` description "Adjustable LDO set to **5.25V** for the DAC AVDD".

5.21 V: ADR 0004 "an LM317LZ set to **~5.21 V**" and "3.65 V at AVDD = **5.21 V**";
ADR 0005 "its own LM317LZ set to **~5.21 V**"; ADR 0003 ×2; `power-entry.md` ×3;
`digital-and-supervision.md` ×3; `pitch-stage.md`; `breath-receive-stage.md`;
`breath-output-stage.md` ×3; `bom.csv` `R-SPI-PULL`, `R-OPAMP-IN`,
`TRIM-BREATH-ZERO`, `R-BREATH-OFF`.

`bom.csv` `R-REG-SET` settles it arithmetically against the specified divider:

> "Vout = 1.25*(1+475/150) = **5.21V**."

so the part's own row and the divider's row disagree with each other.

### H3 — The in-amp's rest and full-scale outputs

`hardware/module/breath-receive-stage.md` drawing:

> ```
>                                         │  Vout = −2.185·(V_BREATH − V_AGND) + V_REF
>                                         │       = 0 V at rest, **−9.6 V at full**
> ```

Same page, prose:

> The in-amp then rests at 0 V and reaches **−9.6 V** at full sensor range

Same page, derivation table:

> | **R_G = 42.2 kΩ → G = 2.1848, effective 2.1611** | **jack span 9.94 V** |

`hardware/module/breath-output-stage.md`:

> | Sensor full scale (6 kPa) | 4.800 V | **−10.05 V** |

`hardware/bom.csv` `U-DIFFRX`:

> "Output is **-0.44V at rest** to **-10V** at full"

`hardware/module/digital-and-supervision.md` drawing:

> `in-amp output ──┐  (0 V absent, **−0.44 V alive**)`

Four full-scale values (−9.6, −9.94, −10.0, −10.05) and two rest values (0 V,
−0.44 V). The −0.44 V rest is the *un-nulled* pedestal × gain, i.e. the state
before `TRIM-BREATH-ZERO` was adopted — so the BOM row and the supervision
drawing describe a superseded circuit.

### H4 — Sensor output span: 4.7 V or 4.8 V

4.80 V: ADR 0003 "~0.2–**4.80** V out"; ADR 0003 comparison table "| Output span
| 0.2–**4.80** V | 0.2–**4.80** V |"; ADR 0003 "full scale, 0.2–**4.80** V, for
the CV output"; `breath-receive-stage.md` "| Sensor span, 0.2 → **4.8** V | 4.6 V |";
`breath-output-stage.md` "| Sensor full scale (6 kPa) | **4.800** V |".

4.7 V: ADR 0005 "a 5 V part outputting **0.2–4.7 V** (ADR 0003)"; ADR 0003 itself
"The sensor reaches **4.7 V** while the ADC runs on 3.3 V"; `carrier.md` drawing
"MPXV4006DP Vout  **0.2 – 4.7 V**"; `carrier.md` derivation "full scale = **4.7 V**
× 0.6 = 2.82 V … **3502 counts**"; `bom.csv` `U-BREATH` "766mV/kPa, **0.2-4.7V**".

The ADC divider's full-scale count and headroom check in `carrier.md` are
computed from 4.7 V; at 4.80 V they give 2.88 V and 3576 counts, and the
"85 % of range" figure moves. ADR 0003 states both values within itself.

### H5 — Marker bits: 8/3, 6/5, or "four to six"/"eight to ten"

Current decision (ADR 0001, `key-layout.yaml` fields, `cluster-boards.md`):

> ADR 0001: "**Use 8 of the 14 spare chain bits as a fixed marker pattern. DECIDED, 2026-09-21** — this line read '4–6' until then." … "So the allocation is **6 marker → 8 marker, 5 free → 3 free**"

> `key-layout.yaml`: `spare_bits_marker: 8      # DECIDED 2026-09-21, ADR 0001 - was 6` / `spare_bits_free: 3`

> `cluster-boards.md`: "### The marker pattern: 8 bits, not 6 — DECIDED 2026-09-21"

Not applied in `hardware/controller/carrier.md` §3:

> | **6** | Marker pattern | **Cluster boards** — hard-wired at the register input. Unretrofittable |
> | **5** | Genuinely free | **Cluster boards** — must be pulled |

> **Which six bits carry the marker and to what pattern is still undecided**

> **Two items left this page with the registers.** The **marker pattern**
> (**which six bits**, to what levels) …

Not applied in ADR 0010:

> - **Four to six of the spare chain bits belong to the marker pattern**
>   (ADR 0001) and are not available for switches. **Eight to ten remain**, which
>   is more than three.

(The true remainder is 6: three reserved switch bits plus three free.)

And `key-layout.yaml` contradicts its own fields two lines above them:

> #   **The 5 genuinely free bits** are FLOATING CMOS INPUTS and must be pulled -
> #   the exact fault R-KEY-PU exists to fix (ADR 0001).
> …
> spare_bits_free: **3**        # was 5; two went to the marker.

### H6 — Six conductors per hop, or twelve, or thirteen

Twelve: ADR 0001 topology diagram "**ONE chained run, 12 conductors per hop
(2x6 IDC)**"; `bom.csv` `WIRE-LOOM` "**TWELVE conductors per hop**"; `bom.csv`
`J-CHAIN` 2×6 pinout; `cluster-boards.md` §3; `carrier.md` loom table "| **Key
loom, all four clusters, chained — `J-CHAIN` is 2×6** | **12** |".

Six: `config/key-layout.yaml`:

> # **Six conductors leave each board** - VCC, GND, CLK, SH/LD, SER-in, QH-out - with
> # a ground return per signal, chained cluster to cluster rather than starred.

ADR 0001 §"On the something else":

> It wins on hand-joint count …, on loom width (**6 conductors per hop** against
> 40–56 mm of ribbon …)

ADR 0001 Consequences:

> every switch-to-chip connection is a trace on the board the switch is already
> soldered to, and **six conductors leave each cluster**.

`bom.csv` `PCB-CLUSTER`:

> "every switch-to-chip connection becomes a TRACE and **only six conductors
> leave each board**"

`cluster-boards.md` §intro:

> "**six signals leave the board** instead of twenty-one"

ROADMAP:

> | **Does the chained key loom fit the side channel?** | M4 | **Six conductors
> per hop** rather than the 32–44 the tail-mounted alternative needed |

Thirteen: ADR 0001's own comparison table:

> | Conductors down the body | **12 per hop** — **6 signals-and-supply, 5 grounds, 2 spare** | 32–44 |

6 + 5 + 2 = 13, not 12. The signal-and-supply count is 5 (`SCK`, `SH/LD`, `SER`,
`QH`, `3V3`).

This one matters physically: the M4 side-channel fit check in the ROADMAP is
written against six conductors and the ribbon is twelve.

### H7 — Five chain connectors or eight

`bom.csv` `WIRE-LOOM`:

> "chained through each cluster board in turn rather than starred, so **five
> connectors must match**: one on the carrier and one per cluster board"

`bom.csv` `J-CHAIN` (qty 8):

> "**EIGHT of them, not five**: the chain is four hops and SER/QH are
> point-to-point rather than bus, so every cluster board but the last carries an
> IN and an OUT. Carrier 1, right_thumb 2, right_hand 2, left_thumb 2, left_hand 1"

ADR 0001: "**Eight connectors have to match, across five boards**".
`carrier.md`: "**EIGHT connectors, not five.**"
`cluster-boards.md`: "7 chain connectors — **plus one more `J-CHAIN` on the
carrier, eight in all**".

Two rows of the same file give different counts for the same connector.

### H8 — Key-chain read time: <10 µs, 16 µs, or 32 µs

`docs/reference/latency-budget.md` key path:

> | 74HC165 chain read | **< 10 µs** via SPI DMA |

`docs/reference/latency-budget.md` rule 1:

> one pass costs ADC 24 µs + **key chain 16 µs** + six DAC channels at 2 MHz 96 µs
> = **136 µs**

ADR 0001:

> Full chain reads in **~32 µs** at 1 MHz, about **13 %** of a 250 µs loop period.

`carrier.md`:

> `SPI3  keys   32 bits      @ 1.0 MHz =  32.0 µs, concurrent → 13 %`

32 bits at the decided 1 MHz is 32 µs. The 16 µs in the loop-duty rule is the
2 MHz figure; the rule's total (136 µs) is therefore 16 µs light, and the
8 kHz-does-not-close argument is built on it.

### H9 — ADC conversion time

`latency-budget.md`:

> | SAR ADC conversion | **~24 µs** | 18 clocks at the MCP3202's ~0.9 MHz ceiling
> on 3.3 V. **This row said 50–200 µs**, which is a generic SAR allowance and not
> this part |

ADR 0003's latency table still says:

> | SAR ADC conversion | **~50–200 µs** |

`latency-budget.md` states explicitly why this matters:

> At 200 µs a pass costs **312 µs against a 250 µs period and the loop does not
> close**

The correction landed in one document and not in the ADR that owns the sensing
path.

### H10 — 16 or 17 GPIO broken out on the ESP32-S3-Matrix

ADR 0007:

> Broken out: **GPIO 1–7** on one side, **GPIO 33–40, 43, 44** on the other.
> **Seventeen, not sixteen** — an earlier revision of this list omitted GPIO33 and
> **the error propagated into ADR 0013 and the roadmap**.

`bom.csv` `U-MCU-RT` still carries the error:

> "**16 GPIO broken out (1-7, 34-40, 43, 44)** vs 14 needed"

ADR 0001 also still carries it:

> Two extra pins against **sixteen** of headroom

`bom.csv` `HDR-SERVICE` has the corrected figure ("3 power + **17** GPIO"), as
do ADR 0009 and `carrier.md`. The BOM contradicts itself in two rows.

### H11 — How many pins the real-time role needs

- ADR 0007: "| **Used** | **14 of 17** | spare: 3, 4, 33 |"
- ADR 0013 table: "| **Total on the chip** | **18** of ~30 | **14 broken out** |"
- ADR 0013 prose immediately after: "**Fourteen chip pins of headroom**, against two before." — 30 − 18 = **12**.
- ADR 0013 §Considered and rejected: "not expected at **13 pins** and one job."
- ADR 0014: "Two data lines cost one extra GPIO, against roughly 17 broken out and **12 needed** on the real-time board (ADR 0007)."
- `bom.csv` `U-MCU-RT`: "vs **14** needed".

### H12 — GPIO33: spare or the chain's serial-out driver

ADR 0007:

> **GPIO 3, 4 and 33 stay free.** GPIO 3 and 4 are ADC1 channels

> | **Used** | **14 of 17** | **spare: 3, 4, 33** |

`carrier.md` §3 assigns it:

> ```
>    IO33  SER out  ──[R-CHAIN-SER 100R]─────►  6  SER     (into the far device)
> ```

`cluster-boards.md`:

> If firmware *does* drive **`IO33`**, the carrier's output wins through its
> 100 Ω series resistor against a 10 kΩ pull

`bom.csv` `R-SER-TERM`:

> "If firmware instead DRIVES it from the carrier's **IO33**"

ADR 0007 is the ADR of record for the pin assignment and shows the pin free.
Actual spares are therefore 2, not 3.

### H13 — 25 or 50 LEDs per pair of strips

ADR 0014: "So: **one run per side**, roughly 420 mm each, **0.84 m total**"; the
density table gives "| 30/m (**25 LEDs**) |" and "| 60/m (**50 LEDs**) |"; and:

> ### Density: 60/m
> … **60/m.**

`bom.csv` `LED-SIDE` is 60/m. `carrier.md` §5 costs the boot hazard against the
other row:

> The buffer squares up whatever it sees into clean 5 V edges and sends it to
> **25 addressable LEDs** on a 12 V rail.

### H14 — Key network values in ADR 0009

ADR 0009 §"Things that are free now and impossible later":

> **Fit the key input networks.** A 74x165's parallel inputs have no internal
> pull-up, so without them every key input floats in a channel shared with 12 V
> LED power and 800 kHz data — **10 kΩ, 100 Ω and 10 nF** per switch position on
> the cluster boards (ADR 0001).

ADR 0001, which it cites:

> **Per switch position: 2.2 kΩ to 3V3, 100 Ω in series, 47 nF to ground**

`bom.csv`: `R-KEY-PU` **2k2**, `C-KEY` **47nF**. `cluster-boards.md`: same.
This also re-asserts "**12 V** LED power" as the coupling aggressor, which
ADR 0001 refutes ("**There is no 12 V edge.** … The fast aggressor is the **data
line, at 5 V**").

### H15 — `R-KEY-SER`'s own timings are the pre-correction pair

`bom.csv` `R-KEY-SER`:

> "With C-KEY: press is **~1us (100R x 10nF)** so it stays instant, release is
> **~93us (10k x 10nF)** which is a free hardware debounce."

`bom.csv` `C-KEY`, the adjacent row:

> "Press crosses HC165's VIL (0.99V at 3.3V) in **~5.7us** … Release crosses VIH
> (2.31V) at **~125us**. The '~1.4us / 176x' pair this row used to carry was the
> 10nF part against LVC thresholds; both changed."

ADR 0001 records the same correction and adds:

> Earlier versions of this line read "~1 µs" and "~93 µs". Those were the
> 10 kΩ/10 nF pair against LVC thresholds and **both parts of that changed**.

The exact pair ADR 0001 names as stale is still in the BOM, one row above the
row that corrects it.

### H16 — Load-switch start time, power and energy

`power-entry.md`:

> The timer must be longer than a *current-limited* start (1.0 A into 2.2 mF to
> 12 V is **26 ms**) …
> - **Timer ≈ 50 ms**, comfortably past 26 ms.
> - **The FET must survive 12 W for 50 ms — 0.6 J — as a single pulse.**

> **This is why the package changed.** An earlier BOM revision said SOT-23, and
> at **0.6 J** that is hundreds of degrees of junction rise.

ADR 0005:

> **It boots — in about 75 ms of constant-current start**, which is long enough
> to trip a USB-class fault timer. The prescription is the same either way: a
> programmed ramp and **a fault timer longer than it**.

`bom.csv` `U-LOADSW`:

> "A 1.0A ramp at ~6V mean for **75ms** is **~6W and 0.45J**"

`bom.csv` `C-TIMER-LOADSW`:

> "Sets the **~50ms** fault timeout, which must outlast a current-limited start
> into the instrument's 2.2mF (**26ms**) and bounds the FET's single-pulse SOA
> energy at **12W x t**"

ADR 0005 requires the fault timer to exceed 75 ms; `power-entry.md` and the
timer capacitor's own row set it to ~50 ms. On ADR 0005's number the instrument
does not boot. The FET is also sized against two different pulses (12 W/0.6 J vs
6 W/0.45 J).

### H17 — Clamp-legal worst case: 579 mA or ~630 mA

ADR 0005 load table: "| **Clamp-legal worst** | 928 mA | 119 mA | **579 mA** | 6.5 W |"

ADR 0005, fourteen lines later: "it is set from below, by the clamp-legal worst
case of **~630 mA** plus ramp current"

`carrier.md` uses the table's 5 V column ("Clamp-legal worst on the 5 V rail,
total **928 mA**"), so the 5 V figure is consistent; only the umbilical figure
disagrees with itself.

### H18 — The pitch error budget, four ways

`hardware/module/pitch-stage.md` §"What limits accuracy, in order" contains two
tables, back to back, for the same terms:

> | **DAC internal reference** | **0.42 cents** | **The largest term, and untrimmable** |
> | LT5400 ratio tracking | **0.027 cents** | |
> | `TRIM-GAIN` tempco | **0.068 cents** | 200 Ω cermet |

then, after four paragraphs of prose, without a header:

> | LT5400 ratio tracking | **~0.1 cents** | The reason it is not two discrete 0.1 % parts, which would be **~1.2 cents** |
> | DAC internal reference | **~0.5 cents** | A gain term, per above |
> | OPA2197 offset drift | <0.1 cents | |
> | DAC INL, ±4 LSB typical | ~0.4 cents | |

ADR 0006:

> | DAC internal reference, 5 ppm/°C | 0.45 mV | **0.54** |
> | **Discrete resistors, 25 ppm/°C each, drifting oppositely** | **4.50 mV** | **5.40** |
> | Matched network, 1 ppm/°C tracking | 0.09 mV | **0.11** |

`bom.csv` `R-PRECISION`:

> "the DAC's internal reference drifts **0.42 cents** over 10degC … against
> **0.027** for the LT5400 and **0.38** for two 0.1%/10ppm discretes"

Discretes are 5.40, ~1.2 and 0.38 cents in three documents; the DAC reference is
0.42, ~0.5 and 0.54. `pitch-stage.md` also says of the second table's first row
that the ranking "**is resolved, and both published numbers were wrong**" —
while the wrong numbers are still on the page below.

### H19 — The mod offset channel: 2.5 V or 3.3333 V, once or every pass

ADR 0006's channel table row:

> | *(internal)* | DAC ch 7 | — | — | Shared **3.3333 V** offset for mod 1–4 |

ADR 0006's update-rate table:

> | Mod offset | **written once at boot** | The shared **2.5 V** reference point |

`firmware/README.md` says why both halves of that row are wrong:

> The mod channels are `Vout = 4·Vdac − 3·V_ref`, with `V_ref` the shared
> **3.3333 V** from DAC channel 7 — **written once at boot** (ADR 0006).
> *(The value changed with the two-resistor redraw in `mod-channels.md`; writing
> the old 2.5 V into channel 7 against the current 10 k/30 k network gives a
> **−7.5…+12.5 V window — wrong span, and it clips positive**.)*

> **Refresh everything, every pass. Never write-on-change.**

`latency-budget.md`: "the loop refreshes the mod offset every pass rather than
writing it once". ADR 0006's own row is the only surviving statement of the rule
that `firmware/README.md` exists to overturn, and it carries the value that
"clips positive".

### H20 — The mod reference buffer's load current

`mod-channels.md` drawing:

> ```
>    DAC ch7 ──[1k]──┬── ½ OPA2197 ──┬── V_ref = 3.3333 V
>    (shared)        │   follower    │   to all four channels
>                    └───────────────┘   (**~1.3 mA** total into 4 × 10k)
> ```

`mod-channels.md` §"One buffer, four loads", same page:

> At **2.5 V** into 2.5 kΩ that is **1 mA**, comfortable for the part.

3.3333 V into 2.5 kΩ is 1.33 mA. The prose was not swept with the redraw.

### H21 — Pitch at power-on

ADR 0006:

> | **Pitch** | Bottom of its range, **below −2 V** | Subsonic. A VCO there is inaudible |

`pitch-stage.md`:

> **Power-on is 0.000 V, not "subsonic".** `V_ref` is the DAC's internal
> reference, which is **disabled until firmware writes an enable** — so *both*
> terms are zero and the jack sits at **0 V, a VCO's base note**, until that
> write. After it, `CLR` parks at −2.500 V. **ADR 0006's power-on table asserts
> "below −2 V" for both; they are different states, 2.5 V apart.**

ADR 0004 repeats the superseded claim:

> an A/C grade part clears to zero scale, which **parks pitch subsonic**

ADR 0006 itself, twenty lines below its own table, half-concedes it:

> It also means the outputs sit at 0 V from rack power-on until firmware enables
> the reference, which happens to reinforce the table above.

— which it does not; it contradicts the pitch row.

### H22 — A/C grade vs C-locked

ADR 0006: "**Not 'A or C', which this line used to say.** … **Only C satisfies
both requirements.** `bom.csv` is locked to `DAC8568CIPW`".

`bom.csv` `U-DAC`: "**GRADE LOCKED TO C.** … This row previously read
'DAC8568C (or A grade)'".

ADR 0004, unchanged: "an **A/C grade** part clears to zero scale".

`mod-channels.md` notes the safety consequence: "a B/D part would put **+2.5 V
on all four jacks**"; an A part, per ADR 0006, halves everything and leaves
channel 7 unable to reach its reference.

### H23 — Six or seven channels on the umbilical

ADR 0003:

> | **Breath analog, 7 channels at 4 kHz** | **0.90 Mbit/s** | **2 MHz** |
>
> *(The 0.6 MHz this table used to give came from a 2 kHz mod rate and five
> channels; ADR 0006 moved to 4 kHz and **the loop refreshes seven**.)*

ADR 0004:

> | **Breath analog, 6 channels at 4 kHz** | **0.77 Mbit/s** | **≥1.5 MHz → specify 2 MHz** |
>
> (**Seven channels were populated until the breath ambient-zero was deleted** —
> ADR 0003 — which is slack)

`latency-budget.md`: "SPI to DAC over umbilical | ~96 µs | **Six** 32-bit words at 2 MHz".
`bom.csv` `U-DAC`: "**Populate 6 of 8**: pitch, 4 mods, mod offset; channels 6 and 8 spare".

ADR 0003's table and its own footnote are the last place the deleted seventh
channel is still counted.

### H24 — ADR 0004 gives the umbilical SPI clock twice, differently

> ```
> SCLK, MOSI, CS      SPI to the DAC, **~2 MHz**
> ```

versus, forty lines later in the "Revised conductor budget":

> ```
> SCLK      / DIG_GND     SPI to the DAC, **~1 MHz**
> ```

The whole of ADR 0004's bandwidth section, `latency-budget.md`, `carrier.md` and
ROADMAP E11 use 2 MHz. The 1 MHz figure is the rate of the *key chain*, on the
other board.

### H25 — Series resistor value: 220 Ω or 68 Ω

ADR 0004 §decision: "**220 Ω in series on MOSI at the driving end.**"

ADR 0004 §"This number has a deadline", same file:

> `R-MOSI-SER` at 220 Ω with ~200 pF of cable is a **3.6 MHz** corner — 7.9 MHz is
> the 100 Ω case this same sentence offers as the fix, which is the wrong way
> round … **transmission-line analysis puts the right value nearer 68 Ω**

`carrier.md`: "**ADR 0004's corrected text puts the transmission-line-right value
nearer 68 Ω** (11.7 MHz corner …); take all three down together if E11 wants the
headroom."

`bom.csv` `R-SPI-SER`: part is **220R**; note says "**transmission-line analysis
says ~68R** for a clean first step. Decide at E11 on the real cable."

The corpus has an orderable value nothing defends and a defended value nothing
orders.

### H26 — ADR 0009 has two `### Mass` sections with different totals

First:

> | Width | Mass |
> |---|---|
> | 2.00 in | ~735 g (1.62 lb) |
> | **2.25 in** | **~778 g (1.72 lb)** |
> | 2.50 in | ~825 g (1.82 lb) |

Second, seven lines later, for the decided 2.25 in build:

> | **Total** | **~825 (1.8 lb)** |

825 g is the first table's **2.50 in** row. One of the two is 47 g out, and
both sections claim to describe the chosen envelope.

### H27 — OPA2197 output swing

- ADR 0004: "It is rated to ±18 V, so on ±12 V it reaches roughly **11.9 V**"
- `bom.csv` `U-OPA-PITCH`: "RRIO on +/-12V reaches **~11.9V**"
- ADR 0005: "A rail-to-rail op-amp on a +12V rail swings to roughly **+11.5V**"
- ADR 0006: "±12 V rails less ~0.35 V of Schottky leaves ±11.65 V, and an OPA2197 reaches **~±11.45 V** — 1.45 V of margin"
- `pitch-stage.md` and `mod-channels.md`: "An OPA2197 on ±12 V less two Schottky drops reaches **~±11.45 V**"
- `breath-output-stage.md`: "the OPA2197 stops at about **±11.5 V**"

`breath-output-stage.md`'s clipping rule ("their sum has to fit in ±11.5 V") and
`mod-channels.md`'s margin claim ("±10.05 V has 1.4 V of margin") are computed
from different numbers.

### H28 — `C-DECOUPLE` quantity counts a deleted part

`bom.csv`, qty **21**:

> "One per supply pin, close to the pin. 6 x OPA2197 on +/-12V = 12, INA828 = 2,
> **LM311 on +/-12V = 2**, DAC8568 AVDD+DVDD = 2, 74AHCT125, LT1641 VCC, LM317 in.
> **Was 22 with the 74HC123; the watchdog is deleted**"

The row removed the watchdog's cap and kept the comparator's two. Without the
LM311 the enumeration sums to **19**.

### H29 — `R-OUT-PROT` power rating

`bom.csv`: "1k 1%, **>=500mW**", with a derivation ("Pitch shorted now rails the
op-amp across this resistor: 142mW … 192mW steady state … specify >=500mW").

`breath-output-stage.md`: "| **R-OUT-PROT** | 1 kΩ, **1206 ≥500 mW** | Shared
spec with the other five outputs |".

`pitch-stage.md`: "| **R-OUT-PROT** | 1 kΩ 1 %, **1206 ≥250 mW** | Short
protection, **inside the DC feedback loop** |".

The page that introduced the jack-side tap — which is what created the 192 mW
worst case — is the one that still specifies 250 mW.

### H30 — Loop duty at 4 kHz

`latency-budget.md`:

> Serialised, one pass costs ADC 24 µs + key chain 16 µs + six DAC channels at
> 2 MHz 96 µs = **136 µs** … At 4 kHz it is 136 µs of 250 µs — **54 % duty**

`carrier.md`:

> ```
> SPI2  DAC    6 × 32 bits @ 2.0 MHz =  96.0 µs
> SPI2  ADC    24 clocks    @ 0.9 MHz =  26.7 µs
> SPI2  total                         = 122.7 µs of 250 µs → **49 %**
> SPI3  keys   32 bits      @ 1.0 MHz =  32.0 µs, concurrent → 13 %
> ```

Different ADC time (24 vs 26.7 µs), different key-chain time (16 vs 32 µs),
different model (serialised vs concurrent). The serialised total with the
corrected key figure is 154.7 µs, 62 % — which is the number the 8 kHz argument
should be made against.

### H31 — The buck's switching frequency in the aliasing argument

ADR 0003:

> A buck running at **500 kHz** sampled at 4 kHz folds to DC; at 498 kHz it folds
> to **2 kHz**, and at **496.1 kHz** to **100 Hz — directly into the breath band**
> … 47 nF gives a ~564 Hz corner and **58 dB at 500 kHz**.

`bom.csv` `C-AA-ADC`:

> "the '~600Hz, 58dB at 496kHz' note was wrong twice over - wrong corner, and
> **the R-78E5.0 switches at 330kHz not 496kHz**. **55dB at 330kHz**."

`carrier.md`:

> attenuation at the R-78E5.0's **~330 kHz** switching rate = 20·log10(330k/564) = **55 dB**

The part's actual switching frequency was corrected in the BOM and the carrier
page; the ADR that argues the aliasing case still uses 496–500 kHz, and its
worked example ("496.1 kHz folds to 100 Hz") is the reason the part is fitted.

### H32 — Where the breath channel is band-limited

ADR 0003: "**Band-limit at both ends, around 500 Hz.**"

`carrier.md` §2:

> **2. There is no band-limit capacitor at the instrument end of `BREATH`.**
> ADR 0003 says "band-limit at both ends, around 500 Hz" `[repo] 0003`;
> `breath-receive-stage.md` puts the whole 500 Hz filter at the receive end …
> **Drawn that way here. Do not add a cap at `R-SER-BREATH-INST`.**

`breath-receive-stage.md`: filter is "**ahead of the in-amp**", module side only.
`bom.csv` `C-FILT-BREATH`: "**AHEAD of the amp**". No instrument-side cap row.

ADR 0003 is unchanged and would have a builder fit a part the carrier page
forbids.

### H33 — The analog star point is on a board that does not exist

ADR 0003:

> > **The star point is the analog ground pour on the bottom cluster board, at the
> > sensor and reference, immediately adjacent to the umbilical connector.**
>
> Everything analog in the instrument — the sensor, the REF5050, both halves of
> the OPA2197, the ADC divider — sits on **that one board** …

`carrier.md` §2:

> ADR 0003 names the star point as "the analog ground pour on the bottom cluster
> board" `[repo] 0003` — **a board that does not exist; it means this one.**

`bom.csv` `PCB-CLUSTER` confirms the cluster boards carry only "switches, one
74HC165, its decoupling, and the per-key network". The section ADR 0003 wrote
specifically to give a rule a real object points at a board with no analog on it.

### H34 — Breath latency totals

ADR 0003's own table: "| **Total** | **< 1.5 ms** |" — computed before the tube,
the restrictor and the filter poles.

ADR 0003 prose: "The digitised path comes to **~3.1 ms** against a 5 ms target".

ADR 0003 §"The cost": "Breath path goes from ~1.5 ms to **~2.6 ms**".

`latency-budget.md`: "| **Total** | **~2.83 ms** + restrictor |" (analog) and
"| **Total** | **~2.9–3.1 ms** + restrictor |" (digital), and in prose:
"**2.80 ms** against a 5 ms target".

ADR 0003's table is the one a reader meets first and it is 1.3 ms optimistic; it
also still books the ADC at 50–200 µs (**H9**) and omits the tube, which the
same ADR later adds at 1.17 ms.

### H35 — `HDR-DEV` quantity

`bom.csv`, qty **6**:

> "Cut to length: 2 strips for the ESP32-S3-Matrix, 2 for the T-Display-S3
> AMOLED, 2 spare."

`carrier.md`:

> | `HDR-DEV` | 2 × 10-way machined socket | **Qty is one board's worth, not two** — the display board is 360 mm away |

> This page therefore draws **one** dev-board socket pair

ADR 0013 is the source of the two-board reading:

> The carrier holds only: **Headers the dev boards plug into**

### H36 — The spare LT5400 sections

`pitch-stage.md` §"It is a non-inverting amplifier": "Two of the LT5400's four
resistors do the job; **the other two are spare.**"

`pitch-stage.md` §Still open, first bullet:

> The claim that two spare sections can build the mod channels' 1:3 is
> **arithmetically impossible** — three sections against the fourth is all four.

`pitch-stage.md` §Still open, last bullet — six lines later:

> - **The two spare LT5400 resistors.** Available, matched, and currently doing
>   nothing. **Worth a look when the mod channels are laid out.**

`mod-channels.md` still makes the refuted claim as a reason for the topology:

> Eight resistors instead of sixteen, one matching requirement instead of two per
> channel, and **a 1:3 ratio that three sections of an LT5400 give directly
> against the fourth.**

### H37 — Spare gates on the 74AHCT125

`bom.csv` `U-LVLSHIFT`: "SOIC-14. 5V rail TTL thresholds … **Two spare gates.**
VERIFY WS2815 threshold"

`bom.csv` `R-LED-SER`, qty **4**: "**FOUR not two**: the WS2815's BACKUP data line
is cited as a reason for the part choice in ADR 0014 and again in ADR 0005, and
was connected to nothing - **the level shifter's two spare gates are exactly what
it needs**"

`carrier.md` §5:

> If so, **all four gates are used, none spare**, against the BOM's "Two spare
> gates" `[repo] bom.csv`, and the LED loom is 8 conductors rather than 6.

ADR 0004: "**74AHCT125** for the shifter … with a spare gate left over."

The BOM buys four series resistors for four gates and still advertises two
spares; `carrier.md`'s loom conductor table books "6–8" on the strength of the
unresolved question the BOM has already resolved.

### H38 — 18 switches or 21

`bom.csv` `SW1-n`, qty **21**: "18 keys + 3 spares (octave up/down, hold/preset)
- cutouts required in the DXF at M3 even if fitted later"

ADR 0010: "**18 switches**, decided". `key-layout.yaml`: `total: 18`.

`cluster-boards.md` component table allocates: `LH` 5, `LT` 4, `RH` 6, `RT` 3 =
**18**, with "**18 fitted switches in 21 networked positions**". No board is
allocated the three spare switches, so the BOM's 21 cannot be placed from the
schematic. `CAP1-n` is also 21 against 18 fitted.

### H39 — Mod channel span: ±10.000 V or ±10.05 V

`mod-channels.md` §adopted:

> it lands on **exactly ±10.000 V** where the four-resistor version needed a
> 40.2 kΩ fudge to reach ±10.05 and still did not hit the number

`mod-channels.md` §"On the range", present tense, describing the current design:

> **On the range:** **±10.05 V** uses the DAC's *full* 0–5 V span. ADR 0006's
> 0.25–4.75 V window is a **pitch-channel reserve** … Stated because the two
> numbers look contradictory side by side and are not.

`mod-channels.md` tolerance table: "| Span | **19.703–20.303 V** |" — centred on
20.003 V, i.e. ±10.0015.

ADR 0006: "| **Mod 1–4** | DAC ch 2–5 | **−10…+10V** |".

The paragraph that exists to say two numbers are not contradictory is itself the
stale one — its ±10.05 V belongs to the deleted four-resistor stage.

### H40 — `C-OUT-BREATH` corner: 480 Hz or 482 Hz

`breath-output-stage.md`: "| **C-OUT-BREATH** | 330 nF film | **~482 Hz**, jack
side |". `breath-receive-stage.md`: "| **Output RC** | 1 kΩ + 330 nF film |
**~480 Hz** reconstruction at the jack |". ADR 0006: "| Breath | 1 kΩ | 330 nF
film | **~480 Hz** |" and "it is already a **482 Hz** channel by the time it
reaches the module". `bom.csv` `C-OUT-BREATH`: "**~480Hz**".
`latency-budget.md`: "| Output RC at the jack, **480 Hz** | **332 µs** |" —
332 µs is the group delay of a 479 Hz pole; 482 Hz gives 330 µs, the value the
row above it uses for the identical RC. Raised to High only because the
latency table sums two poles it gives two different frequencies for.

---

## Medium

**M1 · ROADMAP E10 says `REF` is grounded, then says to trim it.** One table
cell contains both the superseded and the current decision:

> Analog breath stage: **in-amp receiver with `REF` grounded**, gain/offset knobs.
> **Set `TRIM-BREATH-ZERO` first**, until the in-amp output reads 0 V

`breath-receive-stage.md` §"Why `REF` is trimmed rather than grounded":
"**Grounding it makes the panel knobs interact** … turn GAIN to 2.4×, and the
jack idles around **+0.6 V — into a VCA**."

**M2 · `firmware/README.md` states the superseded version:**

> since the in-amp's `REF` pin is **grounded** rather than driven by a firmware
> zero (ADR 0003), no DAC register touches the breath jack at all

**M3 · `breath-receive-stage.md` contradicts its own section heading**, 170
lines below it:

> `CLR` reaches the DAC channels; breath touches none of them, and **now that
> `REF` is grounded** it touches the breath stage in no way at all

**M4 · ADR 0004 keeps the presence-gating prescription immediately above the
section that deletes it.** Four bullets and a paragraph survive:

> - **Gate the 74AHCT125's output enable from a real presence detect**, so
>   "instrument absent" is a state the hardware knows about
>
> **It needs a bench override.** … A jumper or a solder link that forces `OE` low
> is two pads. **Without it the gating locks out every module milestone**

then:

> ### There is no presence detect, and the buffer runs unconditionally
> **Both versions are deleted.**

**M5 · ADR 0004's cable block still lists MISO and the presence signal**, which
its own conductor budget deletes:

> ```
> MISO                unused today — module ID and presence detect
> ```
> ```
> +12V      / PWR_GND     power, and the presence signal
> ```

against, in the same file: "**MISO goes**, and with it the planned module-ID
line."

**M6 · `digital-and-supervision.md`'s *Still open* list is four items about
deleted parts** — the `R-PRESENCE` row, the '123's power-on-reset RC, the
retrigger arithmetic ("~2400 retriggers per timeout"), and "demote this
comparator to LED and health duty". See **S1**, **S2**.

**M7 · ADR 0010's spare-bit accounting.** "**Four to six** of the spare chain
bits belong to the marker pattern (ADR 0001) … **Eight to ten remain**, which is
more than three." Eight are claimed; six remain (3 reserved + 3 free).

**M8 · `key-layout.yaml`'s comment contradicts its own field**, two lines apart:
"The **5** genuinely free bits are FLOATING CMOS INPUTS" vs `spare_bits_free: 3`.

**M9 · `bom.csv` `MECH-PTFE` still uses the refuted Helmholtz model and an
orifice:**

> "One part, two jobs: **sizes the resonance** above the 500Hz corner and blocks
> liquid. **Size the orifice at E2.**"

ADR 0003: "**the model this ADR used was invalid** … A Helmholtz model requires
the neck volume to be small against the cavity, and here it is the other way
round … It is **independent of trap volume.** **No restrictor *size* moves it.**
… which is why it is specified as **porous PTFE rather than as an orifice**."
ADR 0003's own §Condensation also still calls it "*the same part as the
**Helmholtz restrictor** above*".

**M10 · The ~22 mm carrier cutout is required by three documents and proposed
for deletion by the carrier page.** ADR 0009: "**A matching cutout in the carrier
PCB**"; ADR 0014: "**The carrier needs a ~22 mm cutout** … Free on a 2-layer
board, impossible to add later"; `bom.csv` `PCB-CARRIER`: "**Must carry the ~22mm
cutout** … Impossible to add later". `carrier.md` §7: "**Proposed: mount the
ESP32-S3-Matrix on the carrier's *underside* … and delete the cutout.**"

**M11 · `docs/decisions/README.md`'s index disagrees with three ADR headers.**
Index: "| 0007 | IMU selection | Accepted (**board open**) |", "| 0008 | Display
selection | Accepted (**board open**) |", "| 0011 | Licensing | **Open** |".
ADR 0007: "**Status:** Accepted. **Board selected: Waveshare ESP32-S3-Matrix.**"
ADR 0008: "**Status:** Accepted. **Board selected: LilyGO T-Display-S3 AMOLED**".
ADR 0011: "**Status:** Accepted."

**M12 · `README.md` has two licence sections and they disagree.**

> ## Licence
> Three share-alike licences, one per kind of work — **GPL-3.0-only** … Derivatives stay open on the same terms.

and, as the final section of the same file:

> ## Licensing
> **Not yet decided** — see [ADR 0011](docs/decisions/0011-licensing.md).

**M13 · `firmware/README.md` still describes the single-MCU core split:**

> - **Display renders on the other core, on its own SPI host.** A display refresh
>   must never block the output loop.

four bullets above "**WiFi and the display are on the other MCU.**"

**M14 · ADR 0013's carrier list still asks for two sockets and puts both
regulators on the carrier**, which `carrier.md` contests:

> - **Headers the dev boards plug into**
> - **Two** R-78E5.0 regulator modules — one per dev board … and the umbilical connector

`carrier.md`: "**The display board is 360 mm away** … It reaches this board
through a loom, not a socket. This page therefore draws **one** dev-board socket
pair and leaves the second regulator's location open."

**M15 · ADR 0006's own channel table calls the mod channels "Trimmed"**:

> | **Mod 1–4** | DAC ch 2–5 | **−10…+10V** | none | **Trimmed** |

against, in the same ADR: "**Mod channels stay trimmer-free.**" and
`mod-channels.md`, which fits none.

**M16 · `carrier.md` says the anti-alias RC is unbooked; it is booked.**

> `latency-budget.md` and ADR 0003 book "SAR ADC conversion ~50–200 µs" and **no
> RC term at all** `[repo]` … Found by `R10-keyscan-and-adc.md` §B-2 and **still
> unapplied**.

`latency-budget.md` now carries both: "| **Anti-alias filter, 564 Hz** |
**282 µs** | `C-AA-ADC` against the divider's 6 kΩ. **Omitted entirely before**".
Only ADR 0003 is still stale (see **H9**).

**M17 · `carrier.md` §4 mis-states the BOM.** "only `R-MOSI-SER` reached the BOM,
**qty 1**" — the BOM row is `R-SPI-SER`, qty 3 (see **S8**).

**M18 · `carrier.md` §5 marks `R-LED-SER` as proposed.** "**`R-LED-SER` is
proposed** on the same grounds as §4 … **100–330 Ω** at the buffer." The BOM has
it: `R-LED-SER`, **330R**, qty **4**, status candidate.

**M19 · `carrier.md`'s component table marks `C-ADC-BULK`, `R-LED-PD`,
`R-CHAIN-SER`, `U-TVS-CHAIN`, `F-CHAIN`, `TP-*`/`LK-*` as "proposed — no BOM
entry yet".** That is accurate for those six; listed here because the same table
also marks `R-SCLK-SER` and `R-CS-SER` proposed when the BOM covers them, so a
reader cannot use the "proposed" marking as a reliable signal.

**M20 · ADR 0004 specifies linear-taper pots; the breath gain pot's taper is
open.** ADR 0004: "Alpha 9 mm vertical pots (**linear taper** — predictable for
CV scaling)". `bom.csv` `POT-GAIN`: "50k, **taper TBD at E10**".
`breath-output-stage.md`: "| **POT-GAIN** | 50 kΩ, **taper from the bench** |"
and "**`POT-GAIN`'s taper.** Linear gives a knob that does most of its work in
the last quarter turn."

**M21 · ADR 0009 still says "three or four" left-thumb keys.** "…and **three or
four** mechanical keys on the underside for the left thumb". ADR 0010 and
`key-layout.yaml` fix it at **4**.

**M22 · `bom.csv` `SW1-n` still says the cutout must be measured.** "Binary.
**Plate cutout must be measured.** Soldered." — followed, in the same note, by
"**Datasheet and STEP model published by Gateron - use them, do not caliper the
housing**". ADR 0002: "An earlier revision of this ADR said the cutout dimension
*'must be measured, not taken from a datasheet'*. **That was wrong.**"

**M23 · `bom.csv` `KNOB-BREATH` names a refdes that does not exist.** "Knob for
the **POT-BREATH** shaft type". The pots are `POT-GAIN` and `POT-OFFSET`.

**M24 · `bom.csv` `PCB-MODULE` description lists "watchdog"** (see **S1**).

**M25 · `bom.csv` `U-ADC` still quotes the superseded loop-rate range.**
"50ksps at 3V3 vs **4-8kHz** needed". `latency-budget.md`: "**The 8 kHz end of
the old '4–8 kHz' range does not close.** … 4 kHz is the number."

**M26 · `mod-channels.md` records the inverting-amp alternative twice, with
different verdicts.** Lines 79–87: "*(A third option surfaced in the same
research …)*" ending "Taking the reference from a DAC channel keeps the inverting
topology and the safe clear together." Lines 194–224, a full section: "**it is
strictly better than what is drawn above. Not adopted unilaterally**". A reader
of the first passage would not know the page later recommends it.

**M27 · `mod-channels.md` misquotes ADR 0006.** "ADR 0006 says these channels
need to be **\"linear and repeatable, not calibrated\"**". ADR 0006 says
"Channels 2–6 need only to be **linear and repeatable**" and "They need to be
linear and repeatable, **not musically accurate**". The phrase quoted does not
appear.

**M28 · ADR 0006's filter section still describes the jack cap as current.**
"| Cap to ground **at the jack**, after the series R | **What this design
currently specifies** | Safe, but see below |" — in the section that deletes it
(see **S5**).

**M29 · ADR 0006 §"Why dedicating pitch and breath" still gives breath a 2 kHz
corner.** "- **Breath wants a gentler filter**, ~2 kHz." The same ADR concludes,
600 lines later: "This ADR's earlier '~2 kHz for breath' is superseded by that
page" (480 Hz). The earlier text was not edited.

**M30 · ROADMAP E10 reasons from the watchdog.** "**Pull the umbilical mid-note
with the mouthpiece at rest** and confirm the breath jack parks quietly: **the
watchdog has no authority over it by design**, and this is the check that the
design is right about why (ADR 0004)." With the watchdog deleted, the test still
matters but its stated rationale is gone; `digital-and-supervision.md` records
the new consequence — "**pull the umbilical mid-note and the rack holds that note
until you flip the module's toggle**" — which ROADMAP E10 does not test for.

**M31 · `breath-receive-stage.md` §"What the jack does when the watchdog fires —
settled"** cites ADR 0004's watchdog section as live reasoning; that section sits
under ADR 0004's "**Withdrawn 2026-09-21**" banner.

**M32 · `digital-and-supervision.md`'s rails table row "LM311, 74HC123"**
allocates a supply to two deleted parts and is the justification for a design
rule ("Supervision must not die with the rail it supervises") that no longer has
a subject.

**M33 · ADR 0003's own power tree omits `R-ISO-REF`** (see **S7**) while ADR 0003
is the ADR the BOM row cites (`adr` column: 0003).

**M34 · `bom.csv` `R-KEY-PU` and `cluster-boards.md` disagree on whether the
2.2 kΩ decision is live.** BOM: "**Kept anyway** as cheap insurance … 1.5mA per
PRESSED key against a 360mA budget **is nothing**". `cluster-boards.md`:
"**Keeping it is not free any more**, because 25.8 mA of play-rate load lands on
the rail that is also the MCP3202's voltage reference — worth 3.2 LSB". The BOM
measures the cost against the wrong budget (the 360 mA umbilical rail, not the
dev board's 3V3 LDO / ADC reference).

---

## Low

**L1 · `latency-budget.md` totals.** Table "**~2.83 ms** + restrictor"; prose
four paragraphs later "**2.80 ms** against a 5 ms target".

**L2 · `bom.csv` `R-KEY-PU` says 1.5 mA per key**; ADR 0001, `carrier.md` and
`cluster-boards.md` all compute **1.43 mA** (3.3 V / 2.3 kΩ).

**L3 · `ks33-geometry.md` header vs body.** "an open-source **52-key** split
keyboard" against "| `lefttop.stl` | **23** cutouts |" + "| `righttop.stl` |
**24** cutouts |" = 47, and "**47 cutouts** across a working build".

**L4 · ADR 0001 uses the LVC threshold in the corrected coupling argument.**
"landing at 1.94 V against a **0.8 V** threshold" — and, twelve lines later,
"nowhere near `V_IL` on either family (**0.8 V for LVC, 0.99 V for the 74HC165
actually fitted**)". `bom.csv` `C-KEY` repeats only the LVC number: "does not
cross a **0.8 V** threshold".

**L5 · ROADMAP Track F lists F9 before F8.** "| F9 | **Matrix surface** | … |"
then "| F8 | Persistence | … |"; the phase view reads "**F4–F9**".

**L6 · ADR 0009 has two identically-titled `### Mass` headings** (see **H26**) —
a structural duplicate independent of the numeric disagreement.

**L7 · `carrier.md` still argues with the repo's "~23" loom figure it then
withdraws.** "`[calc]`, built from the repo's own rules — **not** the '~23' that
ADR 0001, `WIRE-LOOM` and the ROADMAP all carry" … "**this page withdraws the
objection**. ~28–30 against ~23".

**L8 · `bom.csv` `D-USBOR` part and note.** Part: "**1N5817 or SS14**"; note:
"**One diode per source** into the shared 5V node". `carrier.md` draws one per
*regulator output* and says so: "| `D-USBOR` ×2 | **SS14** | **One per regulator
output, not 'one per source' — the OR node is a dev-board pin** | `[repo]` **note
is wrong** |".

**L9 · `carrier.md` §2 reference-buffer drawing omits `C-REF-OUT`'s second
part's role**, leaving "| `C-REF-OUT` | 10 µF ×2 | **Qty 2 for one part — say
whether that is parallel or in+out** |" open while `bom.csv` `C-REF-OUT` states
"Per the REF50xx datasheet's recommended output capacitance, **with a 100nF from
C-DECOUPLE-CARRIER alongside**" — i.e. the BOM implies parallel and the carrier
page still calls it ambiguous.

**L10 · ADR 0004's panel description and the pot count.** "two breath knobs,
then six jacks in two columns" is consistent with `POT-GAIN` + `POT-OFFSET` and
`KNOB-BREATH` qty 2; listed only because ADR 0004 elsewhere calls the module's
controls "two breath knobs" while `breath-output-stage.md` proposes a third
open question (a centre-detent variant) that would change the part.

---

## What to fix first

1. **`hardware/module/digital-and-supervision.md` must be redrawn.** Its
   schematic, its rail table and its open-items list build two parts its own
   prose, the BOM and ADR 0004 delete (**S1**, **S2**), and its `CLR` pull is
   backwards (**S3**). It is the only description of the module's digital
   section, and it is not buildable as drawn.
2. **`hardware/module/power-entry.md` §"The panel LED"** describes a circuit
   whose central node ("the presence comparator's open collector") no longer
   exists, with a resistor value and a rail the BOM has already changed
   (**S10**), and its rail list feeds a deleted comparator (**S2**).
3. **`hardware/controller/carrier.md` §2 is missing two instrument-side,
   unretrofittable parts** that the BOM buys and the module page requires:
   `R1b` (**S6**) and `R-ISO-REF` (**S7**). Both are named "unretrofittable" by
   the documents that specify them.
4. **ADR 0006 still specifies the pitch compensation capacitor across the
   feedback resistor** (**S4**) — the arrangement the rest of the corpus says
   gives 18° of phase margin — and still deletes `C-FILT-PITCH` (**S5**), which
   the BOM buys.
5. **The marker-bit decision (8/3) has not reached `carrier.md` or ADR 0010**
   (**H5**), and `key-layout.yaml` contradicts its own field. These bits are
   hard-wired copper on boards that bond shut.
6. **The loom is six conductors in five documents and twelve in five others**
   (**H6**). The ROADMAP's M4 side-channel fit check — a gate before the plate
   DXF — is written against the wrong number.
