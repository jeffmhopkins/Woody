# MECH — datasheet wave R7, Priority-3 mechanical set

Researcher: MECH. Date 2026-09-21. No repo file outside `datasheets/` was touched.

Provenance tags: `[datasheet <doc> p.N]`, `[schematic <doc> ref]`, `[calc]`, `[web <url>]`,
`[repo <file>:<line>]`.

Documents banked (11 new files):

| file | sha256 (short) | pages |
|---|---|---|
| `mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf` | `ae1e4157` | 1 |
| `connectors/NE8FDP-DATASHEET.pdf` | `7c13fee4` | 3 |
| `connectors/NE8FDV-DATASHEET.pdf` | `b994e0e0` | 3 |
| `connectors/NEUTRIK-PG-DATA-CONNECTOR.pdf` | `bc9c1280` | 36 |
| `connectors/NE8MC.pdf` | `b2415641` | 1 |
| `connectors/NE8MC-DATASHEET.pdf` | `2664a28f` | 2 |
| `connectors/NE8MX.pdf` | `eb3e0c73` | 1 |
| `connectors/NE8MX6.pdf` | `ac0e7673` | 1 |
| `connectors/TE-IDC-SOCKET-CATALOG-82012.pdf` | `2d6eb5b3` | 104 |
| `other-semi/MPXV4006-AN1646.pdf` | `a68763f0` | 7 |
| `discrete-and-power/1N4148W.pdf` | `a39b522c` | 6 |
| `discrete-and-power/1N4148W-DIOTEC.pdf` | `5f5e1a5c` | 3 |

Nothing is BLOCKED. Every assigned document was obtained.

---

## 1. Waveshare ESP32-S3-Matrix schematic — THE 5 V QUESTION IS SETTLED

`https://files.waveshare.com/wiki/ESP32-S3-Matrix/ESP32-S3-Matrix-Sch.pdf`
→ HTTP 200, `application/pdf`, 177 828 bytes, `%PDF-1.3`.
Altium Designer, 1 sheet A4, created 2024-03-25.
Banked as `datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf`.
Verified: the sheet's title block reads `ESP32-S3-Matrix` / `Waveshare`; the text layer
contains 64 instances of `WS2812B-0807`.

The PDF has a real text layer, but the schematic symbols are laid out so that plain
`pdftotext` scrambles the net/pin association. Every claim below was read off a
**rendered** crop of the sheet at 300–450 dpi as well as the text layer.

### 1.1 The LED rail — **5 V, via a Schottky from VBUS. CONFIRMED.**

> `[schematic ESP32-S3-Matrix-Sch, U6/U7/U8 detail]` Each WS2812B-0807 is drawn with
> pin 1 `VDD` tied to the net label **`VCC_5V`**, pin 3 `VSS` tied to `GND`, pin 4 `DIN`
> from the previous device's pin 2 `DOUT`. This is repeated identically for all 64
> devices `U1 … U64`.

There is **no** connection from any LED to `3V3`, and no regulator, load switch, P-FET
or diode between `VCC_5V` and the LED array — the LEDs sit directly on `VCC_5V`.

`VCC_5V` itself is **not** raw VBUS:

> `[schematic … USB block]` USB-C receptacle `J1`, pins `A9/B4` and `A4/B9` = `VBUS`.
> `VBUS` → **`D1`, `B5819WS`**, anode pin 1 on the `VBUS` side, cathode pin 2 on the
> left, and the cathode net is labelled **`VCC_5V`**. `C1 2.2 µF` sits on the **`VBUS`**
> side of `D1` (pre-diode). `R1` and `R2`, both `5.1 K`, are the CC1/CC2 pulldowns on
> `B5` and `A5`.

So the rail feeding 64 LEDs is **VBUS minus one Schottky drop**, not 5.00 V. The forward
drop of the `B5819WS` at the array's current is a number the repo does not yet hold —
`B5819WS` is not in `datasheets/`. Flagging it rather than guessing.

**Verdict vs the repo:** `datasheets/MANIFEST.csv:53` records the schematic as BLOCKED
and says "The 5V-vs-3V3 rail for the 64 LEDs is therefore inferred from the vendor
function-block drawing, not read off a schematic." That inference is now **CONFIRMED**
off the schematic, and the BLOCKED row can be retired. `MANIFEST.csv:36`'s "3V3 is
marked OUT, i.e. the board is fed from 5V" is **CONFIRMED**.

### 1.2 The LED part number — **WS2812B-0807. REFUTED against the repo.**

> `[schematic … U1–U64]` Every one of the 64 LED symbols carries the value string
> **`WS2812B-0807`**. Count verified by extracting the text-layer bounding boxes: 64
> occurrences, spanning x 243–732 pt, y 101–323 pt on the A4 sheet — i.e. the whole
> matrix block.

The repo says **WS2812C** in three live corpus places:

- `[repo docs/decisions/0007-imu-selection.md:176]` "**The matrix is 64 WS2812C parts on
  GPIO14**, chained, driven over SPI2 in Zephyr's configuration."
- `[repo ROADMAP.md:184]` "64 unlit **WS2812C** drivers are an estimated ~50 mA…"
- `[repo docs/decisions/0014-lighting.md:358]` "**WS2812C-2020 draws 5 mA per channel**,
  so 15 mA per LED at full white and 960 mA for all 64."

**REFUTED.** The fitted part is the WS2812B in the 0807 package. This matters beyond
nomenclature: ADR 0014's entire matrix current table is derived from the WS2812C-2020
datasheet's 5 mA/channel, and `datasheets/other-semi/WS2812C.pdf` is banked as the
authority for it. The repo also banks `other-semi/WS2812B.pdf` (5050) and
`other-semi/WS2812B-2020.pdf` — **neither is the 0807 package**, and
`[repo datasheets/MANIFEST.csv:41]` itself notes that the 5050 WS2812B datasheet
"states >=400 Hz and **no current spec**" while the 2020 part states 12 mA/channel,
36 mA total. So the three candidate datasheets in the bank give **no current spec**,
**5 mA/ch** and **12 mA/ch** respectively, and the part actually fitted (0807) matches
none of them. The 960 mA full-white figure and the ~50 mA idle figure both rest on the
wrong part number. **A WS2812B-0807 datasheet is a new gap and should get a BLOCKED
row of its own.**

### 1.3 Data line: **GPIO14, through a MOSFET level shifter, no series resistor.**

> `[schematic … Q1 detail]` `IO14` → `Q1`, **`DMG1012T-7`** (N-channel MOSFET). Gate
> (pin 1) to `3V3`. Source (pin 2) is the `IO14` node, pulled up by **`R4` 2.2 K to
> `3V3`**. Drain (pin 3) is the net **`LED_DIN`**, pulled up by **`R3` 4.7 K to
> `VCC_5V`**. `C5 1 µF` decouples `VCC_5V` at this block. `LED_DIN` runs to `U8` pin 4
> (`DIN`); the chain then runs `U8 → U7 → U6 → …`, ending at net `DOUT`.

This is the textbook bidirectional open-drain translator. Three things follow that the
repo does not currently say:

1. **There is no series resistor on the data line at all** (no 33 Ω / 100 Ω / 470 Ω).
   The only impedance in the path is the 4.7 K pull-up.
2. The high side is **pull-up driven**, so the rising edge is an RC through 4.7 K into
   the `LED_DIN` net capacitance plus the first LED's input. This is the vendor's
   choice, but it is a marginal topology for an 800 kHz WS2812 waveform and it is worth
   recording before anyone adds cable length to the `DOUT` extension pad.
3. `GPIO14` is **CONFIRMED** — matches `[repo datasheets/MANIFEST.csv:33]`
   ("NEOPIXEL = GPIO14") and `[repo docs/decisions/0007-imu-selection.md:176]`.

### 1.4 USB 5 V path and the 3V3 regulator — **ME6217C33M5G CONFIRMED.**

> `[schematic … U49]` `VCC_5V` → `U49` pin 1 `VIN`; pin 2 `GND`; pin 3 `EN` tied to
> `VIN`; pin 5 `VOUT` = net `3V3`; pin 4 `BP` marked no-connect (red X).
> Value string **`ME6217C33M5G`**. Input decoupling **`C3 0.1 µF` + `C4 10 µF`** on
> `VCC_5V`. Output **`C2 10 µF`** on `3V3`.

`[repo datasheets/MANIFEST.csv:35]` says "ME6217C33M5G LDO (3.3V, 800mA max)" from the
function-block PNG. The **part number is CONFIRMED**; the **800 mA rating is
NOT-IN-DOCUMENT** — the schematic states no current rating, and no ME6217 datasheet is
banked. The 800 mA is still an unsourced number.

Also on the USB side: `R7` and `R9`, both **22 R**, in series with `USB_N`/`USB_P` to the
ESP32-S3's `U_N`/`U_P`. The MCU is **`ESP32-S3FH4R2`** (`U66`), crystal `Y1` 40 MHz,
antenna `J2` "贴片天线 CA-C03" (chip antenna), IMU `U67` **`QMI8658C`** on `IMU_SDA`/
`IMU_SCL` with `IMU_INT1`/`IMU_INT2` — all consistent with
`[repo datasheets/MANIFEST.csv:33]`.

### 1.5 Decoupling on the LED rail — **there is none in the array.**

Capacitor designators on the whole sheet are `C1 … C18`. Their text-layer positions were
extracted and compared against the LED array's extent (x 243–732 pt, y 101–323 pt):
**no capacitor falls inside the array.** `[calc]`

The entire capacitance on `VCC_5V` is:

| ref | value | where |
|---|---|---|
| `C5` | 1 µF | at the `Q1` level-shifter block |
| `C3` | 0.1 µF | `U49` input |
| `C4` | 10 µF | `U49` input |
| **total** | **11.1 µF** | all clustered on the back of the board |

`C1 2.2 µF` is on `VBUS`, i.e. on the **other** side of `D1`, and does not decouple the
LED rail. `C2 10 µF` is on `3V3`.

So: 64 addressable LEDs, no per-device 100 nF, and 11.1 µF of lumped bulk sitting behind
the only path into the array. Not a defect in the repo (nothing claimed otherwise), but
it is the fact that governs how much rail sag the matrix causes when a bright frame is
pushed, and it is worth having on the record before ADR 0014's brightness cap is
re-argued.

---

## 2. Neutrik etherCON

`neutrik.com` was fully reachable. Product pages fetched HTTP 200; download links were
scraped from the page HTML rather than guessed, as instructed.

### 2.1 THE PANEL-THICKNESS LIMIT — **4 mm max, CONFIRMED, two primary sources**

I read the already-banked `datasheets/connectors/NE8FDP.pdf` first, as instructed.
`pdftotext -layout` returns **1 byte** — the drawing is fully outlined vector with no
text layer, which is exactly what `[repo datasheets/MANIFEST.csv:5]` already records
("PDF text is outlined vector - no text layer"). That row's statement "**Drawing does
NOT state the 4 mm panel-thickness limit**" is **CONFIRMED** — there is no text to state
it, and the rendered drawing carries no such note.

The number is in Neutrik's **datasheet**, not the drawing. Two independent Neutrik
documents, both now banked:

**Source A — the per-product datasheet, verbatim:**

> `[datasheet NE8FDP p.2 — "Mechanical" table]`
> ```
> Insertion force        ≤ 20 N
> Withdrawal force       ≤ 20 N
> Lifetime               > 1000 mating cycles
> Panel thickness        max. 4 mm 0.16'
> Wiresize
> Wiring                 Feedthrough
> Locking device         Latch lock
> Chassis shape          D
> ```
> (Document footer: "NE8FDP All rights reserved / 21.09.2026 2/ 3" — this is a
> server-generated datasheet, so the date is the fetch date.)

The **NE8FDV** datasheet carries the identical line, and puts it in the product
description as well:

> `[datasheet NE8FDV p.1]` "Vertical PCB panel mount RJ45 receptacle, D-shape metal
> flange with latch lock, **max. panel thickness 4 mm**, mounting screws not included"
>
> `[datasheet NE8FDV p.2]` "Panel thickness — **max. 4 mm 0.16'**"

**Source B — the Neutrik Product Guide, which resolves the variant question:**

> `[datasheet "04 Neutrik PG EN - Section Data Connector - 202110-V22" p.13, "Technical
> Data" table]` Columns are `NE8MX-TOP | NE8MX* (Cable Con.) | NE8FA/B* (A+B Series) |
> NE8FD*-TOP (D Shape) | NE8FD* (D Series)`.
> ```
> Panel thickness   max. 3 mm / 0.12"   -   -   4 mm / 0.16"   4 mm / 0.16"
> ```
> i.e. the base/left-hand value is 3 mm, the two cable-connector columns are "-" (no
> panel), and **both D-shape columns override to 4 mm / 0.16"**.

**Verdict: CONFIRMED.** The "4 mm max panel thickness" asserted at
`[repo docs/decisions/0004-cv-interface-module.md:776]` and
`[repo docs/decisions/0013-two-mcu-split.md:202]` is Neutrik's own published figure for
the D-series etherCON receptacles, and it now has a primary source.

**Partial correction to the repo's hedge.** `[repo hardware/bom.csv:19]` (`J-UMBILICAL`)
says "the one secondary source found gives 3mm for the NE8FDY-C6 variant and '1-3mm' on
Neutrik's general D-series page, **so the number is VARIANT-DEPENDENT and the blanket 4mm
is over-general**." The Product Guide shows the opposite reading: 3 mm is the *generic*
base value for the range and **4 mm is the D-series exception**. Likewise
`[repo hardware/bom.csv:88]` (`MECH-BACKPLATE`) says "The D-series panel-thickness limit
is somewhere in 1-4mm depending on variant and is NOT stated on the drawing the repo
holds". The second clause is right; the first is now wrong for `NE8FDP` and `NE8FDV`,
which are the two variants the module would actually use. Both are 4 mm flat.

*Not checked:* whether the CAT6 `NE8FDY-C6` variant is also 4 mm. Its datasheet was not
fetched. If the variant decision at E12/M7 lands on a `-C6` part the number must be
re-read — but note `[datasheet NE8FDP p.1]` "Attention! Does not intermate with CAT6
cable connector NE8MC6-MO and NKE6S* cables", so that variant is a different decision
anyway.

The conclusion the number supports — cannot mount through 6 mm oak — survives under
every reading, as the repo already says.

### 2.2 The cable-side carrier — **NE8MC is DISCONTINUED. Loud flag.**

> `[datasheet NE8MC p.1, verbatim, first two lines of the document]`
> ```
> NE8MC
> *** DISCONTINUED ***
> Direct replacement / successor: NE8MX
> ```

`[repo hardware/bom.csv:19]` names the chassis side ("Neutrik etherCON D-series chassis
(variant TBD)") and does not name a cable-side part, so nothing in the corpus is
literally refuted — but any BOM that reaches for the obvious `NE8MC` will be reaching
for a dead part. **NE8MX is the part to specify.**

Dimensions, from the vendor drawings (all three banked):

| part | doc | shell Ø | length, with boot | length, no boot | boot Ø |
|---|---|---|---|---|---|
| `NE8MC` | `ST-NE8MC`, Aend-Index **C**, drawn 31.01.01 / changed 20.03.07, A3 2:1 | **Ø19 [0.748]** | **68 [2.677]** (type 1) | **52.6 [2.071]** (type 2) | — |
| `NE8MX` | Drawing ID 20001842, Article 30010008, created 19.07.2018 / approved 14.10.2022, A3 2:1 | **Ø20,1 [0.79]** | **66,4 [2.614]** (type 1) | **50 [1.969]** (type 2) | **Ø18,9 [0.74]** |
| `NE8MX6` | Drawing ID 20004268, Article 30012292, created 09.02.2015 / approved 18.06.2025, A4 2:1 | **Ø20,3 [0.799]** | **75,5 ±1 [2.972 ±0.039]** | — | **Ø19,05 [0.75]** |

`NE8MC.pdf` has **no text layer** (Pro/ENGINEER → Ghostscript 7.0 outlines, same as
`NE8FDP.pdf`); the part number and every dimension above were verified by **rendering**
the A3 sheet at 200 dpi and reading the title block (`EtherCon / NE8MC / ST-NE8MC /
NEUTRIK AG FL-9494 SCHAAN`). `NE8MX.pdf` and `NE8MX6.pdf` do have text layers and each
contains its own part number twice.

Cable OD ranges, which decide the umbilical cable choice:

> `[datasheet NE8MC p.2]` "Cable O.D. **max. 8 mm 0.315'**"
> `[datasheet NE8MX p.2]` "Cable O.D. **4.5 mm - 8 mm**"
> `[datasheet NE8MX6 p.2]` "Cable O.D. **7.0 - 9.5 mm**" … "Protection class IP 65 (in
> combination with NE8FDX-*6-W)" … "Temperature range -40 °C to +70 °C"

Note the NE8MX has a **lower** bound of 4.5 mm that the discontinued NE8MC did not — a
thin Cat5 patch cable that worked in an NE8MC may not strain-relieve in an NE8MX.

Other D-series receptacle specs now sourced, previously unsourced or absent:

> `[datasheet NE8FDP p.2]` Rated current per contact **1,5 A**; rated voltage **≤ 57 V**;
> contact resistance **< 50 mΩ**; dielectric strength **1 kVdc**; insulation resistance
> **> 0.5 GΩ**; lifetime **> 1000 mating cycles**; insertion/withdrawal force **≤ 20 N**;
> PoE type 4 class 8 (100 W) acc. IEEE 802.3bt; temperature range **-30 °C to +80 °C**;
> shell zinc diecast ZnAl4Cu1, nickel plated; contacts bronze CuSn8, 0.2 µm Au over Ni.

The **1.5 A per contact** figure is directly relevant to the umbilical's ~360 mA return
`[repo hardware/module/power-entry.md:344]` and to any decision to parallel conductors.

---

## 3. 2.54 mm IDC ribbon socket — the MATED stack height

**Document obtained:** TE Connectivity (Tyco Electronics) **"Ribbon Cable Interconnect
Solutions", Catalog 82012, Revised 10-09**, 104 pp, via
`https://www.farnell.com/datasheets/1498232.pdf` (HTTP 200, `application/pdf`,
3 101 419 bytes). The Farnell filename is anonymous — per the brief's mirror caution I
checked the content: `pdfinfo` Title is "Ribbon Connector | Tyco Electronics", and the
socket/header pages carry TE part numbers and the catalog number. It is genuine and it is
a TE document, **not** a 3M one as the search hit implied. Banked as
`connectors/TE-IDC-SOCKET-CATALOG-82012.pdf`.

This is the mating half the repo's BLOCKED row `[repo datasheets/MANIFEST.csv]` /
`.manifest-R5.csv:16` says does not exist in any indexed repo. **That row can be
retired.**

### 3.1 Socket body height — read off the drawing

> `[datasheet Catalog 82012 p.52, "Female Socket Connectors, .100 x .100 [2.54 x 2.54]
> Centers, 622 and 636 Series", SOCKET CONNECTOR elevation]`
> ```
> 14.10 (.555)   BEFORE CRIMPING, WITHOUT STRAIN RELIEF
> 10.5  (.413)   AFTER CRIMPING, WITHOUT STRAIN RELIEF
> 12.10 (.476)   MAX
> 14.35 (.565)   \  AFTER CRIMPING, WITH STRAIN RELIEF
> 16.8  (.661)   /
> 6.10  (.240)   MAX   (body width, end view)
> 3.81 (.150) / 1.27 (.050) / 2.54 ±.10   (polarising slot, contact pitch)
> ```
> The dimensions are outlined artwork, not text; read from a 450 dpi render of p.52.
> Note: "THIS SLOT IS OMITTED ON SIZES 14 & SMALLER" — **a 2×6 has no centre polarising
> slot in this series.**

Corroborated by the second socket family in the same catalog:

> `[datasheet Catalog 82012 p.54, "609 Series", Dual Slot IDC Design]`
> `12.37 (.487) BEFORE CRIMPING` / `10.54 (.415) AFTER CRIMPING`

Two independent TE socket families agree on **≈10.5 mm crimped body height**. Take
**10.5 mm nominal, 12.10 mm max**, and **+3.85 mm** if the optional strain-relief clip is
fitted (14.35 nominal / 16.8 max).

Plan dimensions for the 2×6 we need:

> `[datasheet Catalog 82012 p.53, 622 Series table, 12-position row]`
> `A = .777 [19.74]`, `B = .500 [12.70]`, `C = .150 [3.81]`, TE P/N **`2-1658527-0`**
> (T&B ref `622-1230LF`). A 12-position socket **with** strain relief is **not listed**
> in the 622 table (the 12-pos strain-relief cells are "—"), and the 636 Series table has
> **no 12-position row at all**.

That last point is the direct analogue of the repo's finding that 3M's 303 header table
has no 12-pin entry `[repo datasheets/MANIFEST.csv]` — **the 2×6 is a poorly-populated
size on both halves.** Wurth has the 2×6 header; TE has the 2×6 socket only in the bare
622 flavour, without the strain-relief option.

### 3.2 THE MATED STACK HEIGHT — the arithmetic, explicitly

The insertion depth is what converts a body height into a stack height, and **no drawing
in the catalog dimensions a mated assembly.** So the arithmetic is built from three
dimensions and one assumption, and I am naming all four.

Dimensions it rests on:

| symbol | value | source |
|---|---|---|
| `H_hdr` shroud top above PCB | **9.10 ±0.15 mm** (Wurth WR-BHD) | `[repo datasheets/MANIFEST.csv]`, `connectors/WR-BHD-61201621621.pdf` |
| " | **9.3 ±0.25 mm** (3M 303) | `[repo datasheets/MANIFEST.csv]`, `connectors/3M-303-SERIES-BOXED-HEADER.pdf` |
| " | **9.86 mm** = .388 in (TE low-profile) | `[datasheet Catalog 82012 p.76]`, side elevation, board face to shroud top, including the .041 [1.04] standoff |
| `D_cav` shroud cavity depth | **6.50 ±0.15 mm** (Wurth), **6.50 mm** = .256 in (3M) | `[repo datasheets/MANIFEST.csv]` |
| `H_skt` socket height, crimped | **10.5 mm** nom / **12.10 mm** max | `[datasheet Catalog 82012 p.52]` |

The assumption: **the socket bottoms out on the shroud cavity floor**, so insertion
depth = `D_cav`. This is how these connectors are designed to seat and it is the only
self-consistent reading of TE's own geometry — the header's cavity inner width is
`.240 [6.10]` `[datasheet Catalog 82012 p.76, end view]` and the socket body width is
`.240 [6.10] MAX` `[datasheet Catalog 82012 p.52, end view]`, i.e. the body is dimensioned
to slide the full depth of the cavity. But it is an assumption, and no document states it.

```
[calc]  H_mated = H_hdr + H_skt - D_cav

  Wurth header, socket nominal :  9.10 + 10.50 - 6.50 = 13.10 mm
  3M    header, socket nominal :  9.30 + 10.50 - 6.50 = 13.30 mm
  TE    header, socket nominal :  9.86 + 10.50 - 6.50 = 13.86 mm

  Wurth header, socket MAX     :  9.10 + 12.10 - 6.50 = 14.70 mm
  3M    header, socket MAX     :  9.30 + 12.10 - 6.50 = 14.90 mm

  Wurth header, WITH strain relief, nominal : 9.10 + 14.35 - 6.50 = 16.95 mm
  Wurth header, WITH strain relief, MAX     : 9.10 + 16.80 - 6.50 = 19.40 mm
```

**The bound that does not rest on the assumption.** Insertion depth cannot exceed the
cavity depth, so `H_mated ≥ 13.10 mm` (Wurth) is a **hard lower bound**. The hard upper
bound is `H_hdr + H_skt = 9.10 + 10.50 = 19.60 mm` (zero insertion), which is physically
impossible since the contacts must engage. The design number is therefore:

> **Mated stack height ≈ 13.1 mm above the board (Wurth) / 13.3 mm (3M), bounded below
> at 13.1 mm and, on any credible engagement, not above ~14.7 mm.**

**Against the 20 mm cavity** `[repo hardware/bom.csv:94]`: 20 − 13.1 = **6.9 mm** of
headroom for the ribbon's bend radius, worst case 20 − 14.9 = **5.1 mm**. `[calc]`
That is not tight for a bare socket — a 12-way 1.27 mm ribbon folds in well under 5 mm.

**It is tight, and probably fails, if the strain-relief clip is fitted**: 16.95 mm
nominal leaves 3.05 mm, and 19.40 mm max leaves 0.6 mm. `[calc]` Since the 622 Series
table does not offer a strain-relieved 12-position part anyway, the recommendation falls
out on its own: **specify the bare socket and strain-relieve the ribbon on the board, not
on the connector.**

**Cable-exit height.** The catalog does not dimension the ribbon's exit height or bend
separately. The strain-relief clip's +3.85 mm over the bare socket
`[calc: 14.35 − 10.50 = 3.85]` is the closest thing to a bend allowance the document
gives, and it is a clip dimension, not a cable one. **NOT-IN-DOCUMENT** for the
cable-exit height as such.

**Verdict vs the repo:** `[repo hardware/bom.csv:94]` "the number that actually decides
'tight' is the MATED stack height, which is STILL BLOCKED: no ribbon-socket datasheet
exists in any indexed repo" — the datasheet now exists and is banked. The mated height is
no longer blocked; it is **≈13.1 mm derived, with the seating assumption named**. The
header-side numbers the repo already holds (9.10 Wurth / 9.3 3M) are **CONFIRMED** by a
third vendor at 9.86 mm (TE), which is 0.6–0.8 mm taller — so *if the carrier ends up
using a TE header the stack grows by ~0.8 mm*.

---

## 4. MPXV4006 / AN1646

`https://raw.githubusercontent.com/spmp/water_controller/master/datasheets/AN1646_MPX-app-note.pdf`
→ HTTP 200, 234 885 bytes, `%PDF`. `pdfinfo` Title: "AN1646, Noise Considerations for
Integrated Pressure Sensors", Author Freescale Semiconductor. 7 pp. Rev 2, 05/2005.
Banked as `other-semi/MPXV4006-AN1646.pdf`.

### 4.1 OUTPUT FILTERING — recommended RC values and topology

> `[datasheet AN1646 p.2]` "When filtering with hardware, **a low-pass RC filter with a
> cutoff frequency of 650 Hz is recommended. A 750 ohm resistor and a 0.33 µF capacitor
> have been determined to give the best results** (see Figure 2) since the 750 ohm series
> impedance is low enough for most A/D converters."

Topology, from Figure 2: sensor pin 1 (Vout) → **750 Ω series** → A/D node, with
**0.33 µF to ground** at the A/D node. Supply decoupling on pin 3 (+5.0 V): **1.0 µF in
parallel with 0.01 µF**.

`[calc]` `f_c = 1/(2π·750·0.33 µF) = 1/(2π·2.475e-4) = 643 Hz` — agrees with the stated
650 Hz.

> `[datasheet AN1646 p.2]` "Some A/D's will not work well with the source impedance of a
> single pole RC filter. … In applications where the A/D converter is sensitive to high
> source impedance, **a buffer should be used.** The integrated pressure sensor has a
> rail-to-rail output swing, which dictates that a **rail-to-rail operational amplifier**
> should be used to avoid saturating the buffer. A MC33502 rail-to-rail input and output
> op amp works well for this purpose (see Figure 3)."

And on averaging:

> `[datasheet AN1646 p.2]` "A rolling average of eight to 64 samples will clean up most of
> the noise. A **10 sample average reduces the noise to about 2.5 mV peak to peak** and a
> **64 sample average reduces the noise to about 1 mV peak to peak**. … the S/N ratio
> improves as the square root of the number of samples … **a rolling average of four
> samples combined with the RC filter in Figure 2 results in a noise output on the order
> of 1 mV peak-to-peak.**"

Supply guidance, relevant to the module's rail choice:

> `[datasheet AN1646 p.5]` "The integrated pressure sensor is designed, characterized and
> trimmed to be powered with a **5.0 V ±5 %** power supply which can supply the **maximum
> 10 mA** current requirement of the sensor. Powering the integrated sensor at another
> voltage than specified is not recommended because the offset, TCO and TCS trim will be
> invalidated… A **0.33 µF to 1.0 µF ceramic capacitor in parallel with a 0.01 µF**
> ceramic capacitor works well… it is preferable to use a **linear regulator such as an
> MC78L05 rather than a relatively more noisy switching power supply**… the power to the
> sensor **and the A/D voltage reference should be tied to the same supply**" (sensor
> output is ratiometric, so supply variation cancels).

### 4.2 MOUNTING — **NOT-IN-DOCUMENT in AN1646**

AN1646 contains **no mounting section and no mounting-stress caution**. Its seven pages
are: introduction, noise filtering, four scope figures, power supply, layout optimization
(5 rules), analog layout, digital layout, conclusion, references. I read all seven. The
brief expected a mounting caution here; it is not there. **NOT-IN-DOCUMENT.**

The mounting-stress caution is in the **datasheet**, as Note 5 — cross-check below.

### 4.3 Cross-check: MPXV4006DP datasheet Note 5, verbatim

Read off the already-banked `datasheets/other-semi/MPXV4006DP.pdf` (22 pp; `pdftotext`
emits "Couldn't find trailer dictionary" warnings but extracts cleanly).

> `[datasheet MPXV4006DP p.3, Note 5]` "**Auto Zero at Factory Installation:** Due to the
> sensitivity of the MPXV4006, **external mechanical stresses and mounting position can
> affect the zero pressure output reading.** To obtain the 2.46 % FSS accuracy, the device
> output must be 'autozeroed'' after installation. Autozeroing is defined as storing the
> zero pressure output reading and subtracting this from the device's output during normal
> operations. **The specified accuracy assumes a maximum temperature change of ±5 °C
> between autozero and measurement.**"

Two consequences the repo should carry:

1. The 2.46 % FSS accuracy is **conditional on an autozero after installation** — the
   datasheet's own transfer-function graphs distinguish "± 5.0 % VFSS" (no autozero) from
   "± 2.46 % VFSS" (autozeroed) `[datasheet MPXV4006DP p.5, Figs 4 and 5]`.
2. The ±5 °C clause means the autozero has to be **re-taken as the instrument warms**, or
   the accuracy claim lapses. In a sealed body with a documented 10–20 K interior rise
   `[repo docs/decisions/0007-imu-selection.md:207ff]` that is not a formality.

And the datasheet's own filtering figure, which points at AN1646:

> `[datasheet MPXV4006DP p.5, Figure 3 caption]` "**Recommended Power Supply Decoupling
> and Output Filtering Recommendations** (For additional output filtering, please refer to
> **Application Note AN1646**.)" — the figure shows **1.0 µF** and **0.01 µF** supply
> decoupling and **470 pF** on the output.
>
> `[datasheet MPXV4006DP p.5, body text]` "Figure 3 shows the recommended decoupling
> circuit for interfacing the output of the integrated sensor to the A/D input of a
> microprocessor or microcontroller. Proper decoupling of the power supply is
> recommended. … Typical, minimum and maximum output curves are shown for operation over a
> temperature range of 10 °C to 60 °C **using the decoupling circuit shown in Figure 3**."

**Note the discrepancy, and it is not cosmetic:** the datasheet's Figure 3 output filter
is a bare **470 pF** with no series resistor; AN1646's is **750 Ω + 0.33 µF**. The
datasheet's specified accuracy curves are stated to be measured with the *Figure 3*
circuit. A design using the AN1646 filter gets much better noise but is no longer the
configuration the accuracy curves were taken in. Both are vendor-recommended; they are
different circuits for different purposes. **CONFIRMED that AN1646 gives 750 Ω / 0.33 µF;
CONFIRMED that the datasheet gives 470 pF; the two are not the same recommendation.**

---

## 5. 1N4148W (SOD-123) for `D-RESP`

`https://www.vishay.com/docs/85748/1n4148w.pdf` → **HTTP 404** (confirms the brief).
Also 404: `/docs/85748/1n4148.pdf`, `/docs/81857/1n4148w.pdf`, `/docs/85751/1n4148w.pdf`,
`/doc?85748`. `www.nexperia.com/product/1N4148W` → HTTP 200 but a **bot "Challenge
Validation" page**, 1 849 bytes, no datasheet link. `www.diodes.com/assets/Datasheets/
ds30079.pdf` → HTTP 200, real PDF, but it is the **MMST3906 PNP transistor** — another
instance of the mirror-mislabelling trap the brief warns about; deleted, not banked.

**Two genuine datasheets obtained:**

**A. Vishay 1N4148W, Document Number 86356, Rev. 1.0, 16-Nov-2023, 6 pp**
`https://www.vishay.com/docs/86356/1n4148w.pdf` → HTTP 200, 122 766 bytes. Text layer
contains `1N4148W` ×10 and `SOD-123` ×5. Banked as `discrete-and-power/1N4148W.pdf`.
*(The correct Vishay doc id is **86356**, not 85748. The repo's BLOCKED row
`[repo datasheets/MANIFEST.csv:49]` already listed 86356 among the URLs tried, so the
failure was network, not the id.)*

**B. Diotec 1N4148W | 1N4448W, version 2026-06-12, 3 pp**
`https://www.diotec.com/tl_files/diotec/files/pdf/datasheets/1n4148w.pdf` → HTTP 200,
263 740 bytes. Banked as `discrete-and-power/1N4148W-DIOTEC.pdf`.

### 5.1 **PACKAGE WARNING — Diotec's 1N4148W is SOD-123F, not SOD-123**

> `[datasheet Diotec 1N4148W p.1]` package block reads "**SOD-123F**", and the
> alternative-outline table lists "SOD-323F = 1N4148WS", "DO-35 = 1N4148",
> "MiniMELF = LL4148".
>
> `[datasheet Vishay 86356 p.1]` "MECHANICAL DATA — **Case: SOD-123**", and p.4 is headed
> "PACKAGE DIMENSIONS in millimeters (inches): **SOD-123**".

`[repo hardware/bom.csv:83]` (`D-RESP`) specifies package "**SOD-123 or SOD-323**". The
Vishay part matches. **A Diotec-branded 1N4148W does not** — it is the flat-lead
SOD-123F, a different footprint. The order code alone is not enough; the manufacturer has
to be pinned. Flagging this because it is exactly the kind of thing a BOM line loses.

### 5.2 Package outline — SOD-123 (Vishay), read off the drawing

> `[datasheet Vishay 86356 p.4]`, outlined artwork, read from a 400 dpi render:
> ```
> overall height           1.175 ± 0.175 mm      (1.000 – 1.350)
> standoff                 0.20 mm
> lead thickness           0.12 ± 0.03 mm
> coplanarity              0.1 max.
> foot length              0.35 ± 0.1 mm ; 0.5 ref.
> lead form draft          0° to 8°
> body length              2.7  ± 0.15 mm
> overall length           3.7  ± 0.15 mm
> body width               1.55 ± 0.15 mm
> lead width               0.55 ± 0.1 mm
> cathode bar marked on the body
> footprint recommendation: 0.85 × 0.85 pads, 2.5 overall span, 0.85 gap
> Package drawing Rev. 01, 18 Jan 2022, document no. S8-V-3910.01-003 (4)
> ```

For contrast, `[datasheet Diotec 1N4148W p.2, "Dimensions - Maße [mm]"]` gives the
**SOD-123F**: body `2,7 ±0,1`, overall `3,8 +0,2/−0,4`, height `1,1 +0,1/−0,3`, body width
`1,6 ±0,1`, lead width `0,6 ±0,1`, lead thickness `0,12`. Similar footprint, **flat leads,
not gull-wing** — the 0.20 mm standoff of the SOD-123 is absent.

### 5.3 Electrical and thermal — and where the two vendors disagree

| parameter | Vishay 1N4148W (SOD-123) | Diotec 1N4148W (SOD-123F) |
|---|---|---|
| `V_R` / `V_RRM` | 75 V / 100 V `[p.1]` | 75 V / 100 V `[p.1]` |
| `I_F(AV)` | **250 mA** (f ≥ 50 Hz, half wave, resistive, infinite heatsink) `[p.1]` | **150 mA** DC `[p.1]` |
| `I_F` continuous | 300 mA (infinite heatsink) `[p.1]` | `I_FRM` 300 mA repetitive peak `[p.1]` |
| `I_FSM` | 500 mA (`t_p` < 1 s); **2 A** (`t_p` = 1 µs) `[p.1]` | 0.5 A (≤1 s); 1 A (≤1 ms); 4 A (≤1 µs) `[p.1]` |
| **`P_tot`** | **280 mW** on FR-4 with recommended footprint; **380 mW** infinite heatsink `[p.1]` | **400 mW** on PCB with 3 mm² Cu pad per terminal `[p.1]` |
| **`R_thJA`** | **440 K/W** (JEDEC 51-3, FR-4, recommended footprint) `[p.2]` | **312 K/W** (3 mm² pad) `[p.2]` |
| `R_thJL` | **330 K/W** (infinite heat sink) `[p.2]` | not given |
| `T_j` max | 150 °C `[p.2]` | 150 °C `[p.1]` |
| `T_op` | −55 to +150 °C `[p.2]` | −55 to +150 °C `[p.1]` |
| **`V_F`** | ≤ **1 V** @ 10 mA; ≤ **1.2 V** @ 100 mA `[p.2]` | < 0.715 V @ 1 mA; < **0.855 V** @ 10 mA; < 1 V @ 50 mA; < 1.25 V @ 150 mA `[p.2]` |
| `I_R` | 25 nA @ 20 V; 1 µA @ 75 V; 100 µA @ 100 V; 50 µA @ 20 V, 150 °C `[p.2]` | < 25 nA @ 20 V; < 1 µA @ 75 V; < 30 µA @ 20 V 150 °C; < 50 µA @ 75 V 150 °C `[p.2]` |
| **`C_D`** | **1.5 pF max** @ `V_F` = `V_R` = 0 V `[p.2]` | **typ. 2 pF** @ `V_R` = 0 V, 1 MHz `[p.2]` |
| **`t_rr`** | **4 ns** (`I_F` = 10 mA, `i_R` = 1 mA, `V_R` = 6 V, `R_L` = 100 Ω) `[p.2]` | **< 4 ns** (`I_F` = 10 mA → `I_R` = 10 mA down to 1 mA) `[p.2]` |
| `V_fr` turn-on | 2.5 V (50 mA pulses, `t_p` = 0.1 µs, rise < 30 ns) `[p.2]` | not given |
| weight | 10.6 mg `[p.1]` | ≈ 0.01 g `[p.1]` |
| MSL / solder | MSL 1, peak 260 °C `[p.1]` | MSL 1, 260 °C/10 s `[p.1]` |

**The R_thJA disagreement is real and is a mounting-condition disagreement, not an error.**
Vishay's 440 K/W is JEDEC 51-3 on its own recommended footprint; Diotec's 312 K/W assumes
3 mm² of copper at each terminal, which is a deliberately generous pad. Whoever sizes
`D-RESP`'s dissipation should quote **Vishay 440 K/W / 280 mW**, because it is the
conservative pair and it is measured on the recommended footprint.

### 5.4 Verdict against the repo

- `[repo datasheets/MANIFEST.csv:49]` — the 1N4148W BLOCKED row. **Retire it.** Two
  genuine datasheets are now banked.
- `[repo datasheets/MANIFEST.csv:14]` — "only the SOD-123 package/thermal data is
  missing." **Now supplied**: package outline, `R_thJA` 440 K/W, `R_thJL` 330 K/W,
  `P_tot` 280/380 mW.
- `[repo hardware/bom.csv:83]` `D-RESP`, "SOD-123 or SOD-323": **CONFIRMED available** —
  Vishay 1N4148W is SOD-123 and Vishay 1N4148WS (doc 86455) is the SOD-323 sibling. But
  see §5.1: not every vendor's "1N4148W" is SOD-123.
- `[repo hardware/bom.csv:83]` "the **0.6 V knee** lands at about a quarter of a hard
  blow": **NOT-IN-DOCUMENT as a specified parameter.** Neither datasheet specifies `V_F`
  at 0.6 V. Vishay specifies only `V_F` ≤ 1 V at 10 mA and ≤ 1.2 V at 100 mA
  `[datasheet Vishay 86356 p.2]`; the 0.6 V figure is readable only off the *typical*
  curve `[datasheet Vishay 86356 p.3, Fig. 1 — Typical Forward Current vs. Forward
  Voltage]`, where ~0.6 V corresponds to roughly 1 mA at 25 °C, and the same figure shows
  the curve shifting left by well over 100 mV at `T_j` = 150 °C. For a shaper whose whole
  behaviour is the knee position, **that temperature shift is the thing to worry about**,
  and the repo does not mention it. This is a soft claim standing on a typical curve, and
  it should be marked as such rather than cited as a datasheet number.
  Diotec's `V_F` < 0.855 V at 10 mA `[datasheet Diotec p.2]` is the tightest *specified*
  bound anywhere in the bank and is still 250 mV above the asserted knee.

---

## Summary table

| # | Question | Verdict |
|---|---|---|
| 1 | 64 LEDs on 5 V or 3V3? | **CONFIRMED 5 V** — `VCC_5V` direct, no regulator/switch/FET |
| 1 | How `VCC_5V` is made | VBUS → Schottky `D1 B5819WS` → `VCC_5V`. Rail is **VBUS − V_f**, not 5.00 V |
| 1 | LED part fitted | **REFUTED** — `WS2812B-0807`, not WS2812C. 3 corpus statements wrong |
| 1 | Data GPIO | **CONFIRMED GPIO14** |
| 1 | Level shifter / series R | **Q1 DMG1012T-7** MOSFET translator, `R4` 2.2 K to 3V3, `R3` 4.7 K to VCC_5V, **no series resistor** |
| 1 | 3V3 regulator | **CONFIRMED `ME6217C33M5G`** (`U49`). Its **800 mA rating is NOT-IN-DOCUMENT** |
| 1 | Bulk/decoupling on LED rail | **None in the array.** 11.1 µF total (`C5` 1 µF, `C3` 0.1 µF, `C4` 10 µF) |
| 2 | D-series panel thickness 4 mm | **CONFIRMED** — NE8FDP datasheet p.2 and NE8FDV p.1/p.2 and Product Guide p.13 |
| 2 | Is it variant-dependent? | Partly **REFUTED** — 3 mm is the range's base, **4 mm is the D-series value** |
| 2 | On the NE8FDP drawing? | **CONFIRMED NOT** on the drawing (no text layer at all) |
| 2 | Cable carrier | **NE8MC DISCONTINUED**, successor NE8MX. Ø20.1 × 66.4 mm with boot |
| 3 | Mated IDC stack height | **≈13.1 mm** (Wurth) / 13.3 (3M) / 13.9 (TE); ≥13.1 hard lower bound; ≤~14.9 with max socket |
| 3 | Fits the 20 mm cavity? | **Yes**, 6.9 mm spare bare — **no** with a strain-relief clip (3.1 mm, or 0.6 mm worst case) |
| 3 | Cable-exit height | **NOT-IN-DOCUMENT** |
| 4 | AN1646 output filtering | **CONFIRMED** — 750 Ω + 0.33 µF, 650 Hz; buffer with a rail-to-rail op amp if the A/D needs it |
| 4 | AN1646 mounting caution | **NOT-IN-DOCUMENT** — AN1646 has no mounting section |
| 4 | MPXV4006DP Note 5 | **CONFIRMED present** — mounting stress + autozero + ±5 °C. Datasheet's own filter is 470 pF, **not** AN1646's RC |
| 5 | 1N4148W SOD-123 data | **OBTAINED** — Vishay doc 86356. `R_thJA` 440 K/W, `P_tot` 280 mW, `C_D` 1.5 pF, `t_rr` 4 ns |
| 5 | Diotec cross-check | **Different package (SOD-123F)** and different thermal basis (312 K/W / 400 mW) |
| 5 | `D-RESP` 0.6 V knee | **NOT-IN-DOCUMENT** as a spec — typical curve only, and it moves with temperature |
