# C4 — Break the shared reference

**Falsification pass on one decision:** that 25.8 mA of key pull-up current on the
ESP32-S3-Matrix's 3V3 LDO moves the MCP3202's reference by 0.077 % / 3.2 LSB, and
that this is "almost certainly inaudible" `[repo] carrier.md §2, §3; cluster-boards.md §2`.

Written cold: `docs/review/**` and `docs/research/**` were not read. Nothing was
edited except this file.

Evidence marks: `[repo] <file>`, `[calc]` with arithmetic inline, `[web] <url>`,
`[from memory]`. Blocked hosts are named where they blocked.

---

## Verdict in one paragraph

**BROKEN.** Not because the arithmetic is wrong — the 0.3 %/100 mA load-regulation
figure is a good guess and survives (§1) — but because it is the DC answer to a
question that is not about DC, and because it is the *smallest* of at least six
current steps on that node. The ESP32-S3's own Wi-Fi TX burst is a 150–350 mA step
on the same rail: **6× to 14× the key current**, at packet rate, with a millisecond
envelope that lands squarely in the breath band. The key term is not the dominant
term; it is roughly the fifth-largest. And the structural hole underneath all of it
is this: **`C-AA-ADC` filters the numerator of the conversion. The reference is the
denominator. Nothing in the design filters the denominator.** The signal path has a
564 Hz bandwidth `[repo] carrier.md §2`; the reference path has none at all.

Total reference-related error at the worst moment, Case B (matrix off the 3V3 rail,
i.e. the project's own assumption): **30 counts RSS to 123 counts linear-worst, or
1.9 % to 7.7 % of the 1594-count playable span** — **9× to 38× the accepted budget**
(§6). Case A (matrix on the 3V3 rail) is not a budget, it is a redesign (§3).

Cheapest fix: **two 0805 resistors (~£0.02) and 27 µs of loop time** — measure the
LDO against the REF5050 the board already carries, on the ADC channel the BOM already
calls spare, and divide it out (§7). It is cheaper than the 10 µF cap whose stated
justification this report disproves.

---

## Index by circuit node / BOM reference

| Node / ref | Finding | § | Verdict |
|---|---|---|---|
| `U-MCU-RT` LDO | Part identified as ME6217C33M5G, 800 mA, SOT-23-5 | §1 | identified `[web]` |
| `U-MCU-RT` LDO | DC load-regulation figure ~0.24 %/100 mA — the project's 0.3 % is sound | §1 | **SURVIVES** |
| `U-MCU-RT` LDO | No transient spec published; transient droop is 1.3×–29× the DC term | §1 | **BROKEN** |
| `U-ADC` MCP3202 | Reference error is *additive and full-scale-weighted*, not a gain term, for anything faster than one conversion | §1.4 | **BROKEN** (new mechanism) |
| `U-MCU-RT` 3V3 | ESP32-S3 Wi-Fi TX = 150–350 mA step, 6–14× the key step, never costed | §2 | **BROKEN** |
| `U-MCU-RT` 3V3 | DFS 240↔80 MHz ≈ the entire key term, on its own | §2 | **BROKEN** |
| `U-MCU-RT` 3V3 | USB-Serial-JTAG SOF = 1 kHz in-band modulation, never costed | §2 | **BROKEN** |
| 8×8 matrix | Which rail it runs from is not recorded anywhere and decides the whole report | §3 | **UNDECIDABLE** — one measurement |
| 8×8 matrix, Case A | 400 Hz WS2812B PWM lands *directly in band*; full field exceeds the 800 mA LDO | §3 | **BROKEN** if Case A |
| 8×8 matrix, Case B | Reaches the reference only via PSRR → <0.1 LSB | §3 | **SURVIVES** if Case B |
| `U-BUCK` R-78E5.0 | 330 kHz ripple folds to exactly 2.000 kHz and wanders with load | §4 | **SURVIVES** on magnitude (0.9–1.8 LSB) |
| `C-STRIP-BULK` / WS2815 | 2 kHz PWM: the fundamental does *not* alias to DC — the **even harmonics** do, worst at 25 %/75 % duty | §5 | mechanism **REAL**, supply-path magnitude negligible |
| `PWR_GND` / `U-ADC` GND | ADR 0014's own 34 mV animation ground offset is a *reference* error if it appears across the ADC's supply return. No layout rule written | §5.3 | **UNDECIDABLE** — needs a written rule |
| `C-ADC-BULK` 10 µF | Does ~0.2 % of the job it is named for at 2 kHz; the LDO is 450–44,000× stiffer | §5.4 | **stated reason DISPROVED**, part still worth fitting |
| `R-KEY-PU` 2k2 | Going back to 10 k removes the one term that was already inaudible | §7.4 | not worth doing |
| `R-CHAIN-SER` / J-CHAIN | 265 mm ribbon inductance on the key step = 1.2 mV, and it is at the far end anyway | §1.5 | **SURVIVES** |
| SPI2 / SPI3 scheduling | Key chain shifts at 1 MHz *concurrent* with the ADC conversion, on the same 3V3. Free to fix | §2.4 | **BROKEN**, zero-cost fix |

---

## §1 The LDO, and why the right number is not load regulation

### 1.1 The part

`waveshare.com`, `docs.waveshare.com`, `files.waveshare.com`, `docs.zephyrproject.org`,
`devices.esphome.io`, `cnx-software.com`, `electronics-lab.com`, `lcsc.com`,
`datasheet.lcsc.com` and `alldatasheet.com` were **all 403 from this sandbox**
(proxy log confirms `connect_rejected` / policy denial). The schematic PDF could not
be opened. What follows is from search-result synthesis, marked as such.

The ESP32-S3-Matrix's 3V3 regulator is an **ME6217C33M5G** (Nanjing Micro One),
SOT-23-5, 800 mA `[web]` via search on
`https://www.waveshare.com/wiki/ESP32-S3-Matrix` and corroborated for the
same-family ESP32-S3-Zero at `https://docs.waveshare.com/ESP32-S3-Zero`.

Published specs obtained `[web]` (`https://www.lcsc.com/product-detail/C427602.html`,
`https://datasheet.lcsc.com/datasheet/pdf/722f7d98b8d249d1938ed34115c5822b.pdf`):

| Parameter | Value | Source |
|---|---|---|
| I_out max | 800 mA | `[web]` |
| Dropout | 180 mV @ 300 mA (3.3 V part); 100 mV @ 300 mA (5.0 V part) | `[web]` |
| Ripple rejection | **65 dB @ 1 kHz — one point, no curve** | `[web]` |
| Line regulation | 0.03–0.05 %/V | `[web]` |
| Load regulation | **not published for the ME6217**; sibling ME6211 gives 8 mV over 1→100 mA | `[web]` |
| Transient response | **not published** | `[web]` |
| Test condition | C_IN = C_L = 10 µF | `[web]` |

### 1.2 The DC figure SURVIVES

`[calc]` from the ME6211's 8 mV / 100 mA:

```
8 mV / 3.3 V = 0.242 % per 100 mA
```

The project assumed **0.3 %/100 mA** `[repo] carrier.md §2`. That is within 25 % of
the sibling part's published figure and on the conservative side. **SURVIVES.** The
number is fine. The problem is what it is a number *for*.

One correction in the project's favour, and one against:

**In its favour** `[calc]` — a reference error is multiplicative, so the error in
counts is δ × *the code you are reading*, not δ × 4096. The project quoted
`0.077 % = 3.2 LSB`, which is 0.00077 × 4096. At the real-play code of 1743
`[repo] carrier.md §2` the DC key term is:

```
0.00077 × 1743 = 1.34 counts = 0.084 % of the 1594-count playable span
```

So the headline 3.2 LSB is **2.4× pessimistic** at the code that matters. The DC key
term is genuinely inaudible — more inaudible than claimed.

**Against it**: that is the only term in the budget, and it is the smallest one.

### 1.3 The figure that actually matters: transient droop

A key press is a step. `[repo] cluster-boards.md §2` gives the edge: the press
time constant is `R-KEY-SER × C-KEY = 100 Ω × 47 nF = 4.7 µs`, so the pull-up
current rises from 0 to 1.43 mA with a 4.7 µs envelope — spectral content out past
**34 kHz**, which is at or above a cheap CMOS LDO's loop bandwidth. Load regulation
describes the rail *after* the loop has settled. Between the edge and settling, the
output capacitor alone supplies the step.

`[calc]`, ΔV ≈ ΔI · t_r / C_tot:

```
ΔI       = 25.8 mA (18 keys)                         [repo] carrier.md §3
C_tot    = dev-board C_L (datasheet test cond. 10 µF [web], Waveshare fit unknown)
           + C-ADC-BULK 10 µF X7R derated ~40 % at 3.3 V bias [from memory] ≈ 6 µF
           bracket: 7 µF (no C-ADC-BULK, small dev-board cap) … 16 µF (both, best case)
t_r      = LDO loop response. NOT PUBLISHED [web]. Bracket 2–20 µs for a
           65 dB@1 kHz CMOS LDO [from memory]

optimistic   0.0258 × 2 µs  / 16 µF =  3.2 mV → δ = 9.8e-4
central      0.0258 × 10 µs / 12 µF = 21.5 mV → δ = 6.5e-3
pessimistic  0.0258 × 20 µs /  7 µF = 73.7 mV → δ = 2.2e-2
```

Against the accepted δ = 7.7e-4, the transient is **1.3× to 29× larger; 8.5× at the
central estimate**. The decision was taken on the DC number and the event is not DC.

**How far, and for how long:** 3–74 mV, for 2–20 µs, once per contact make. But a
mechanical switch does not make once. `KS-33` bounce is 1–5 ms `[from memory]`, which
is **4 to 20 conversions** of the 4 kHz sampler, each seeing a different point on a
ragged 25.8 mA current waveform. And `C-KEY` does not help: it filters the *logic
node*, while the disturbance is the *pull-up current itself*, which is what bounces.

### 1.4 The mechanism the project has no model for: reference error stops being a gain term

This is the most important finding in the report.

The MCP3202 is a SAR. Its 12 bit-trials are **12 separate comparator decisions at 12
separate instants**, each against a different VREF-derived threshold, spread over
`[calc]` 12 clocks at 0.9 MHz `[repo] carrier.md §4` = **13.3 µs** (18 clocks total
= 20.0 µs of conversion).

- If VREF is **constant across the conversion**, the result is `code × (1 − δ)`. Pure
  gain error. Small at small codes. This is the project's model, and the source of
  the defence *"it is the reference moving, so it scales the reading rather than
  offsetting it"* `[repo] carrier.md §3`.
- If VREF **moves during the conversion**, the error is `Σ 2^(11−k) · δ_k`. The MSB
  trial alone carries a weight of **2048 LSB**. The worst case over all trials is
  **4095 LSB**. The error is now **additive and independent of the input code**.

`[calc]` the crossover: any disturbance whose *edge* falls inside the 13.3 µs
bit-trial window is additive. So:

```
disturbance slower than ~1/13.3 µs = 75 kHz   → gain term,     error = δ × code
disturbance with an edge inside the window     → additive term, error up to δ × 4096
```

The key-press transient (4.7 µs edge, 2–20 µs recovery) is **in the additive
regime**. So is the switcher ripple (§4). So is the leading edge of every Wi-Fi burst
(§2).

`[calc]` probability a key edge lands inside a conversion window = 20 µs / 250 µs =
**8 % per contact make** — but with 5–50 bounce edges per press it is a near-certainty
that at least one conversion is hit at every key change.

`[calc]` the additive key-press glitch, central model: δ = 6.5e-3 × 2048 = **13
counts**, worst-case × 4096 = **27 counts**.

**Why this matters more than the size of the number:** the project's defence is that
a gain error is small where the signal is small, i.e. near rest, i.e. near the
**note-on threshold**. That defence is exactly inverted for the additive regime. The
additive terms are at *full strength at the threshold*, and they arrive *at the moment
keys move*, which is the same moment the threshold is being crossed. The failure mode
is not a quiet gain wobble. It is **gate chatter on attacks, correlated with
fingering**, which will be blamed on the switches for a month.

Concrete, and written nowhere: **the note-gate hysteresis must exceed ~100 counts**
(see §6) until the reference is corrected.

### 1.5 Two things that SURVIVE, with proof

**Ribbon inductance on the key step.** `[calc]` for one 3V3 conductor against its
adjacent ground in a 1.27 mm-pitch ribbon, 28 AWG (r ≈ 0.16 mm):

```
L' = (µ0/π)·ln(d/r) = (4πe-7/π)·ln(1.27/0.16) = 4e-7 × 2.07 = 0.83 µH/m
L (265 mm)          = 0.22 µH                                [repo] carrier.md §3
dI/dt (initial)     = 25.8 mA / 4.7 µs = 5.49 kA/s
V = L·dI/dt         = 1.2 mV  → δ = 3.7e-4 → 0.6 counts at play code
```

and it appears at the *far* end of the ribbon, across the pull-ups, not at the
reference node. **SURVIVES.**

**`F-CHAIN`.** A 100 mA PPTC `[repo] carrier.md §3` has 0.5–2 Ω typical `[from
memory]`. `[calc]` 25.8 mA × 1 Ω = 26 mV, again dropped at the *pull-up* end, moving
V_IH from 2.310 V to 2.292 V. Irrelevant to the 74HC165 and irrelevant to the
reference (the LDO senses at its own output pin, upstream of the fuse). **SURVIVES —
but note it buys no isolation for the reference either.**

---

## §2 What else is on that rail: the ESP32-S3 itself

`espressif.com` and `docs.espressif.com` are **403 from this sandbox** (proxy log).
Figures below are `[web]` via search summary of the ESP32-S3 datasheet Tables 6-4 and
6-6 (`https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf`,
not directly openable).

### 2.1 The steps, ranked against the key step

`[web]` + `[calc]`, all on the **same 3V3 node that is the MCP3202's reference**:

| Source on 3V3 | Step | vs the 25.8 mA key step | Repetition |
|---|---|---|---|
| Wi-Fi TX burst on/off | **150–350 mA** (datasheet TX 180–240 mA; peaks to ~500 mA cited) | **6× – 14×** | packet rate; 0.2–1 ms envelopes |
| Wi-Fi RX on/off | ~95–100 mA | **3.7×** | continuous when associated |
| CPU DFS 240 ↔ 80 MHz | ~25–40 mA (modem-sleep spans 13–107 mA by CPU freq) | **1.0× – 1.6×** | scheduler rate |
| **21 key pull-ups** | **25.8 mA** | **1.0×** | play rate |
| USB-Serial-JTAG / USB MIDI | ~10–20 mA, with SOF at 1 kHz | 0.4–0.8× | 1 kHz, continuously |
| QMI8658C IMU (onboard, on 3V3) | ~1.5 mA accel+gyro `[from memory]` | 0.06× | ODR rate |
| MCP3202 + I²C pull-ups | ~1.2 mA | 0.05× | — |

**The key current is not the dominant term. It is the fourth- or fifth-largest step
on its own node.** The project computed the one it owns and declared the node
budgeted.

### 2.2 What the Wi-Fi term is worth in counts

`[calc]`, a 250 mA TX burst:

```
DC model (0.242 %/100 mA):  δ = 6.0e-3  → 1743 × 6.0e-3 = 10.5 counts at play code
                                        → 8× the whole accepted budget, from DC alone
```

Transient: the ideal-cap model gives ΔV = 0.25 A × 10 µs / 12 µF = 208 mV, which is
unphysical (the board would brown out), so the module's own bulk must be supplying
the first microseconds. Observed 3V3 dips on ESP32 boards during TX are commonly
**50–150 mV** `[from memory]`, corroborated qualitatively `[web]`
(`https://esp32.com/viewtopic.php?t=21530`; ESP32 brownout detect at 2.44 V):

```
δ = 50 mV/3.3 V  = 1.5e-2 → gain term at play code: 26 counts
                           → additive (leading edge in-conversion): 31 counts
δ = 150 mV/3.3 V = 4.5e-2 → gain term at play code: 78 counts
                           → additive:                92 counts
```

**Repetition rate is the sting.** Beacons, ACKs and live-config traffic put these
bursts at tens to hundreds of Hz with ~1 ms envelopes. That is **inside the 0–564 Hz
breath band**, it is not attenuated by anything, and it is uncorrelated with playing,
so it reads as breath tremolo that comes and goes with the network.

ADR 0005 already knows about this mechanism and already fixed it — **for the display
board**: *"ADR 0013 asks for a regulator per board so the display board's WiFi bursts
are absorbed locally instead of reaching the analog section"* `[repo] 0005`. The
real-time board's own Wi-Fi bursts land directly on the ADC reference and no document
mentions it. The fix that was thought important enough to buy a second R-78E5.0 was
applied to the distant radio and not to the one sitting on the reference.

### 2.3 ADR 0003 made this exact argument and then dropped it

`[repo] 0003` rejects putting the *sensor* on the shared 5 V rail with a table:

> | 0.4 % (a modest load step) | 21 mV | — "That rail carries AMOLED current steps,
> WiFi TX bursts and key-LED transitions"

and concludes *"What does not calibrate out is dynamic excursion — load steps with
millisecond envelopes."* That is precisely, word for word, the situation the ADC's
reference is now in. ADR 0003 spent a REF5050 (`U-REF-BREATH`) to get the *sensor*
off a rail with Wi-Fi bursts on it, then left the *converter's reference* on a rail
with Wi-Fi bursts on it — and the converter's reference divides the reading just as
the sensor's supply multiplies it.

### 2.4 A free error source: SPI3 shifts while SPI2 converts

`[repo] carrier.md §4` books `SPI3 keys 32 bits @ 1.0 MHz = 32.0 µs, **concurrent**`.

`[calc]` the ESP32's three SPI3 output pads drive ~50 pF of ribbon each:

```
I_avg = C·V·f·n = 50 pF × 3.3 V × 1 MHz × 3 = 495 µA average
```

— negligible as an average, but delivered as **32 current spikes of tens of mA at
1 MHz**, drawn from the ESP32's VDD3P3 pins, i.e. **from the reference node**, with a
32 µs burst that overlaps the MCP3202's 13.3 µs bit-trial window. Per §1.4 that is
the additive regime: each bit trial sees a different point on a 1 MHz current comb.

Magnitude cannot be bounded without measurement. **The fix is free and unwritten:
sequence SPI3 and SPI2 rather than running them concurrently.** The loop has 250 µs
and needs 149 µs `[repo] carrier.md §4`; there is room. Concurrency here buys nothing
and injects a disturbance that is *synchronous with the conversion*, which is the
worst possible phase relationship.

---

## §3 The 8×8 matrix — the question that decides this report

### 3.1 Which rail: UNDECIDABLE, and nothing in the repo records it

The schematic could not be opened (all Waveshare hosts 403). What `[web]` yields:

- The board's LDO is the **ME6217C33M5G, 800 mA** `[web]`.
- The 64 LEDs are **WS2812B** `[web]`, with an internal PWM refresh of **400 Hz**
  `[web]` (`https://www.superlightingled.com/blog/ws2815-vs-ws2812b/`,
  `https://www.advateklighting.com/blog/guides/refresh-and-pwm-rates`).
- The vendor's own warning: *"Do not set the LED brightness too high; excessive
  brightness will cause the temperature to rise rapidly and may damage the board"*
  `[web]` via `https://www.waveshare.com/wiki/ESP32-S3-Matrix`.
- Community practice: WLED users set the automatic brightness limiter to **850 mA or
  less "to keep the board cooler"** `[web]`, same source.

Both the vendor warning ("**damage the board**", not "damage the LEDs") and an 850 mA
community limit sitting a hair above an **800 mA LDO rating** point hard at the LEDs
drawing *through* the regulator. That is a strong prior, not a proof.

**`[repo] 0014` assumes the other case**: its current table is headed `mA @ 5 V` and
`[repo] 0005`'s power tree draws `12V→5V buck A ─┬── real-time board 5V pin / ├── 8×8
matrix (via that board)`. Nothing in the repo says how the matrix gets from the 5 V
pin to the LEDs, and the answer is the difference between a footnote and a redesign.

**Measurement (10 minutes, E1):** power the board from the 5 V pin only, put a meter
in series with nothing and a scope probe on the 3V3 pin, and step the matrix from all
off to an 8-pixel bar at 25 %. If 3V3 moves by more than a millivolt or two, the LEDs
are on 3V3. Confirm with a continuity check from an LED's VDD pad to the 3V3 pin.

### 3.2 Case B — matrix on 5 V: SURVIVES

The step lands on the LDO's **input**, so it reaches the reference only through PSRR.
`[calc]` at the WS2812B's 400 Hz PWM rate, using the 65 dB @ 1 kHz spec `[web]` (PSRR
is higher, not lower, below the spec point):

```
a 100 mV excursion on 5 V × 10^(−65/20) = 100 mV × 5.6e-4 = 56 µV on 3V3
δ = 56 µV / 3.3 V = 1.7e-5  →  0.03 counts at play code
```

Negligible. **SURVIVES.** Note this is the *only* term in the whole report that the
LDO genuinely rejects, and it is the one the project spent `C-ADC-BULK` on.

### 3.3 Case A — matrix on 3V3: BROKEN, four ways

Taking ADR 0014's own current table `[repo] 0014` and reading it as current *through
the LDO*:

**(a) Idle already beats the key term.** 40–64 mA of driver quiescent `[repo] 0014`
is **1.6–2.5× the 25.8 mA** the project spent its analysis on, and it is there
continuously, not as a step.

**(b) 400 Hz PWM lands directly in the breath band and nothing filters it.** 400 Hz
is *below* Nyquist, so it does not alias — it is worse than that, it is a genuine
in-band tone. It passes `C-AA-ADC`'s 564 Hz corner unattenuated, and `C-AA-ADC` is on
the wrong side of the ratio anyway. `[calc]` at a 50 % breath-bar (+160 mA
`[repo] 0014`):

```
δ_pp = 2 × (160/100) × 0.00242 = 7.7e-3
counts_pp at play code = 1743 × 7.7e-3 = 13.4 counts pp
= 1.1 MIDI CC steps of 400 Hz buzz, whose amplitude tracks how hard you are blowing
```

**(c) It closes a feedback loop on the breath reading.** `[repo] 0014`: *"the strips
and the matrix are driven from the MCU's digitised breath"*. So LED current is a
function of the code, and the code is a function of LED current. `[calc]`:

```
k = dI_LED/dcode = 160 mA / 1743 counts = 0.0918 mA/count
dδ/dI            = 0.00242 / 100 mA     = 2.42e-5 /mA
loop gain L      = code × (dδ/dI) × k   = 1743 × 2.42e-5 × 0.0918 = 3.9e-3
```

Stable (L ≪ 1), but it produces a **+0.39 % signal-dependent gain bend at full
breath, growing as code²** — a soft-knee expansion that no zero-trim and no span knob
removes, because it is not a constant. ADR 0014 designed the animation to be
proportional to breath specifically so a full-field bar "behaves"; that same choice
makes the error proportional to breath.

**(d) The one display state that must never fail is the one that kills the rail.**
`[repo] 0014` requires an unmissable full-field error display and full-field white is
**960 mA** — on an **800 mA** part `[web]`, shared with the ESP32-S3 core. That is not
a reference error, it is thermal shutdown (160 °C `[web]`) and a brownout of the MCU
that is trying to report the fault. It also means ADR 0014's 3 W clamp is derived
against the wrong constraint: the clamp is sized against the R-78E5.0's 1 A on the
5 V rail `[repo] 0014, 0005`, and in Case A the binding part is a SOT-23-5 LDO that
appears in **no budget in the repository**.

---

## §4 The upstream path: 330 kHz through the LDO — SURVIVES, but only just

`recom-power.com` was not reachable; R-78E5.0 ripple is `[from memory]` 20–30 mVpp
for the R-78E class. `[repo] bom.csv C-AA-ADC` fixes the switching rate at 330 kHz.

`[calc]`:

```
Input ripple to LDO             ≈ 30 mVpp @ 330 kHz
ME6217 PSRR: 65 dB @ 1 kHz is the ONLY published point [web]. A CMOS LDO's PSRR
falls above loop bandwidth to a 15–25 dB floor in the 100 kHz–1 MHz decade
[from memory]. Take 20 dB (×0.1):
  → 3.0 mVpp on 3V3, i.e. ±1.5 mV
δ_pk = 1.5 mV / 3.3 V = 4.5e-4
```

**Does it alias? Yes, and to the worst possible place** `[calc]`:

```
330 000 Hz mod 4 000 Hz : 330 000 − 82 × 4 000 = 2 000 Hz
```

Exactly **f_s/2**. And a ±1 % shift in the switcher's frequency (±3.3 kHz) sweeps the
alias across the *entire* 0–2 kHz baseband — and the R-78E's frequency is
load-dependent, so the alias frequency moves with LED brightness and Wi-Fi duty.

**Magnitude**, per §1.4 this is deep in the additive regime (3 µs period vs a 13.3 µs
trial window), so it is *not* averaged away by the conversion and it is *not* scaled
by the code:

```
MSB trial alone: 4.5e-4 × 2048 = 0.92 counts
all trials worst case: 4.5e-4 × 4096 = 1.84 counts
```

**SURVIVES** on magnitude: 0.9–1.8 counts is 0.06–0.12 % of the playable span.

But record two things. First, **this single term is by itself as large as the entire
accepted budget** (3.2 LSB nominal, 1.3 LSB corrected). Second, ADR 0003 met exactly
this mechanism on the input side and found it serious enough to buy the highest-value
passive in the breath path:

> *"a buck running at 500 kHz sampled at 4 kHz folds to DC; at 496.1 kHz it folds to
> 100 Hz — directly into the breath band… the alias frequency moves with the
> converter's load-dependent switching frequency, so it is a wandering tone rather
> than a fixed one."* `[repo] 0003`

The same sentence is true of the reference, and the reference got nothing.

---

## §5 The WS2815 strips: 2 kHz against a 4 kHz sampler

### 5.1 What actually happens at exactly Nyquist

The project's premise — *"~2 kHz, which is exactly Nyquist for a 4 kHz sampler"*
`[repo] carrier.md §2` — is right about the frequency and wrong about the consequence.

`[calc]`:

- A **pure 2.000 kHz sinusoid** sampled at 4 kHz does **not** alias to DC. It maps to
  the Nyquist bin: successive samples alternate `±A·cos(φ)`, with amplitude set by the
  sampling phase. It is a sample-to-sample alternation, not a baseband tone.
- At **2000 + ε Hz** it folds to **2000 − ε Hz** and beats against the alternation at
  **2ε**. The WS2815's timebase is an on-chip RC oscillator, so ε = ±200–400 Hz
  (±10–20 %) is normal `[from memory]`. The alias therefore sits at **1.6–2.0 kHz** —
  above `C-AA-ADC`'s 564 Hz corner, and well above the sensor's own 159 Hz. **The
  fundamental is not the problem.**

**The even harmonics are the problem.** PWM is a square wave, and harmonic *n* of a
duty-*D* square has amplitude `(2A/nπ)·|sin(nπD)|` `[calc]`:

```
n = 2  →  4 000 Hz = exactly f_s   →  folds to DC  (or to 2ε: a 0.4–0.8 Hz WANDER)
          amplitude = (A/π)·|sin(2πD)|
          MAXIMUM 0.318·A at D = 0.25 or D = 0.75;  ZERO at D = 0.50
n = 4  →  8 000 Hz = 2 f_s         →  folds to DC as well
```

**So the worst duty cycle is 25 % / 75 % brightness, not full brightness** — and
`[repo] 0014` parks the clamp there: *"on the strips that is a full-length single hue
at ~75 %"*. The design's normal operating point is the alias worst case.

And the premise itself is not solid: `[web]`
(`https://www.superlightingled.com/blog/ws2815-vs-ws2812b/`) reports the WS2815's
internal PWM as ~2 kHz **"however, some datasheets also state 8 kHz"**. At 8 kHz the
**fundamental** folds to DC with amplitude 0.637·A — twice the worst even-harmonic
case. `C-ADC-BULK`'s entire written justification rests on a PWM rate that is in
dispute between datasheets and has not been measured.

### 5.2 Magnitude through the supply path: negligible

The strips are on raw 12 V `[repo] 0005`, two regulators away from the reference.
`[calc]`:

```
umbilical R ≈ 0.34 Ω  (from [repo] 0005: 122 mV cable drop at 359 mA)
500 mA strip swing → 170 mV on the instrument's 12 V
R-78E input-ripple rejection at 2 kHz ≈ 30–40 dB [from memory] → 1.7–5.4 mV on 5 V
× ME6217 PSRR ≥ 60 dB at 2 kHz [web, 65 dB @ 1 kHz] → ≤ 5 µV on 3V3
δ ≤ 1.6e-6 → < 0.01 counts
```

**SURVIVES.** The WS2815 strips do not reach the ADC reference through the supply.

### 5.3 Magnitude through ground: UNDECIDABLE, and it needs a written rule

`[repo] 0014` books its own figure: *"a 34 mV ground offset that moves with the
animation"* in `PWR_GND`.

VREF is `VDD − GND` **at the MCP3202's pins**. The dev board generates and senses 3V3
against *its own* GND pin. If any part of that 34 mV appears in the copper between
the dev board's GND pin (through `HDR-DEV`) and the MCP3202's GND pin, it is a
**reference** error, not a signal error. `[calc]` 34 mV / 3.3 V = 1.0 % → **18 counts
at play code, animation-correlated**.

`[repo] carrier.md §2` writes the star-point rule for the *signal* return (`AGND`
sense-only, local analog pour joining `PWR_GND` at one tie at the umbilical
connector). It says **nothing about the ADC's supply return**, and `[repo] 0014`'s
mitigation is aimed at the breath *channel*, not at the converter's reference.

**Missing layout rule, to be written into carrier.md §2:** *the dev board's GND pin,
the MCP3202's GND pin, `C-ADC-BULK`'s ground terminal and the ADC divider's bottom leg
are one node, and no strip, matrix or `74AHCT125` return current crosses it.* This is
free at layout time and impossible afterwards.

### 5.4 The 10 µF fix: DISPROVED for its stated purpose

`C-ADC-BULK`'s stated job `[repo] carrier.md §2 and component table`: *"the reference
has no anti-alias and the WS2815 PWM is ~2 kHz against a 4 kHz sampler"*, and
*"10 µF plus the existing 100 nF, treating that pin as an analog reference rather than
a logic supply."*

For a disturbance injected as **current** into the 3V3 node, the capacitor sits in
**parallel with the LDO's own closed-loop output impedance**. It only diverts current
where `Z_cap < Z_LDO`. `[calc]` at 2 kHz:

```
C effective: 10 µF X7R 0805 at 3.3 V DC bias ≈ 6 µF [from memory]
Z_cap(2 kHz) = 1/(2π × 2000 × 6e-6) = 13.3 Ω

Z_LDO(2 kHz): pass-device resistance from the published dropout [web],
   180 mV / 300 mA = 0.60 Ω;
   the part is spec'd 65 dB PSRR at 1 kHz [web], so loop gain there is ~60 dB:
   Z_out ≈ 0.60 / 1000 = 0.6 mΩ.   Allow a full decade of margin: ≤ 6–30 mΩ.

Ratio Z_LDO : Z_cap = 1 : 450 … 1 : 22 000
→ the capacitor carries 0.2 % or less of the disturbance current at 2 kHz.
```

**DISPROVED.** At the frequency it was specified for, the LDO is already 450× to
22,000× stiffer than the capacitor. The 10 µF does essentially nothing there.

For disturbances arriving from the LDO's **input** (§4, §5.2), the cap does nothing
either — that path is governed by PSRR, and the cap is already below the LDO's output
impedance.

**Where the 10 µF *does* earn its place** is above the LDO's loop bandwidth — order
10–100 kHz — where `Z_LDO` rises and the cap takes over. That is exactly the
key-step and Wi-Fi-step transient regime of §1.3 and §2.2, where `[calc]` above shows
it **halves the droop** (73.7 mV at 7 µF → 21.5 mV at 12 µF → 12 mV at 16 µF).

**So: fit the part, delete the reason, and write the real one.** The one job it does
is the job the project did not compute.

**One secondary effect to check at layout** `[calc]`: `C-ADC-BULK` sits a few
centimetres from the LDO's output, across `HDR-DEV`. With ~30 nH of loop inductance:

```
f_res = 1/(2π√(30 nH × 6 µF)) = 11.9 kHz
Z0    = √(L/C) = 70.7 mΩ ; with R ≈ 50 mΩ of trace + ESR, Q ≈ 1.4
```

A mildly peaked impedance at ~12 kHz, sitting right in the band where the key-step and
Wi-Fi-step energy lives. Not dangerous, but the 47–100 Ω of fix 2 (§7.2) damps it out
completely, which is one more reason to prefer that arrangement over a bare cap.

---

## §6 Total reference budget at the worst moment

**Scenario:** a chord change (5 keys make, 3 break, 1–5 ms of bounce) + a note attack
(breath crossing the gate threshold) + LEDs at the 3 W clamp (strips single-hue 75 %,
matrix showing a breath bar) + Wi-Fi live-config traffic in progress.

**Case B — matrix on 5 V (the project's own assumption).** Counts at the play code
1743, and at the note-on threshold (≈200 counts), where the additive terms bite:

| Node / ref | Term | δ | @1743 | @threshold | Regime |
|---|---|---|---|---|---|
| `R-KEY-PU` ×21 | DC load reg, 25.8 mA | 7.7e-4 | 1.3 | 0.15 | gain |
| `R-KEY-PU` ×21 | step transient, central | 6.5e-3 | 11 | **13** | additive |
| `U-MCU-RT` 3V3 | Wi-Fi TX, DC part | 6.0e-3 | 10.5 | 1.2 | gain |
| `U-MCU-RT` 3V3 | Wi-Fi TX, transient 50–150 mV | 1.5e-2…4.5e-2 | 26 … 78 | **31 … 92** | additive |
| `U-MCU-RT` 3V3 | DFS 240↔80 MHz | 9e-4 | 1.6 | 0.2 | gain |
| `U-MCU-RT` 3V3 | USB SOF, 1 kHz | ~5e-4 | 0.9 | 1.0 | mixed |
| `U-BUCK` → LDO | 330 kHz ripple, aliased | 4.5e-4 | — | 0.9 … 1.8 | additive |
| `PWR_GND` / `U-ADC` GND | animation ground offset | 0 … 1.0e-2 | 0 … 18 | 0 … 20 | additive |
| SPI3-during-conversion | 1 MHz comb, §2.4 | unbounded | ? | ? | additive |

`[calc]` totals, excluding the unbounded SPI3 term:

```
RSS, optimistic column   √(1.3² + 11² + 10.5² + 26² + 1.6² + 0.9² + 0.9²)
                       = √913 = 30.2 counts = 1.90 % of the 1594-count span
linear sum, optimistic   1.3+11+10.5+26+1.6+0.9+0.9+0   =  52 counts = 3.3 %
linear sum, pessimistic  1.3+11+10.5+78+1.6+0.9+1.8+18  = 123 counts = 7.7 %
```

**Against the accepted 3.2 LSB / 0.2 %: 9× (RSS) to 38× (linear worst).**

Translated `[calc]`:

```
MIDI CC resolution = 1594 counts / 127 steps = 12.6 counts per CC step
  → 30–123 counts = 2.4 to 9.8 MIDI CC steps of excursion,
    bursting at Wi-Fi packet rate and at every chord change
Note gate: 13–92 counts of ADDITIVE error sit at the threshold,
  → gate hysteresis must exceed ~100 counts or the instrument chatters on attacks
```

**Case A — matrix on 3V3.** Add 13 counts pp of 400 Hz buzz whose amplitude tracks
breath (§3.3b), a +0.4 % breath-dependent curve bend (§3.3c), and a full-field state
that exceeds the LDO's rating outright (§3.3d). At that point the budget is not the
question.

### Is "inaudible" still the right word?

**No.** Three independent reasons, any one of which is sufficient:

1. **It is 0.2 % of the wrong thing.** The figure is the DC gain term from the
   smallest of at least six current steps on that node. Correctly computed it is
   1.3 counts, not 3.2 — and correctly *scoped* it is one row of an eight-row table
   whose total is 30–123.
2. **The dominant terms are additive, not multiplicative** (§1.4). The defence *"it
   is the reference moving, so it scales the reading"* holds only for disturbances
   slower than one 13.3 µs conversion. The key transient, the Wi-Fi edge and the
   switcher ripple are all faster. In that regime the error is weighted by 4096 LSB
   regardless of code, which means it is at **full strength at the note-on
   threshold** — the exact place the gain-term argument claims safety.
3. **It is correlated with playing, not random.** Chord changes and breath-driven LED
   animation put the error in lockstep with the performance. Two to ten CC steps of
   *correlated* error is heard as a chirp on attacks and a warble tied to the lights,
   not as a noise floor. The ear finds correlated error at levels far below where it
   finds noise.

The honest word for the current state is not *inaudible*. It is **unmeasured** — and
carrier.md's own instinct was right: *"the symptom of getting it wrong is 'the breath
reading moves when I press keys', which gets blamed on firmware."* The instinct was
right and the number was two orders of magnitude short of justifying the shrug.

---

## §7 The cheapest fix, costed

### 7.1 FIRST CHOICE — measure the reference on the ADC's own spare channel. **~£0.02 + 27 µs/loop.**

Everything needed already exists on the board:

- `U-ADC` MCP3202 **CH1 is explicitly spare** — *"One spare channel"* `[repo] bom.csv`,
  and `[repo] carrier.md §2` draws it as `CH1 = spare`.
- `U-REF-BREATH` **REF5050** is a genuine precision reference already fitted:
  ±0.05 %, 3 ppm/°C, ~5 ppm/V line regulation, buffered by half the OPA2197
  `[repo] 0003`.

**Add:** a `10 k / 10 k 1 %` divider from the buffered 5.000 V to CH1 → 2.500 V.
Same part class as `R-ADCDIV` (0805 1 % metal film), so no new line item type.

`[calc]` settling, to show no cap is needed or wanted on CH1:

```
Thevenin = 10k ∥ 10k = 5 kΩ ; MCP3202 sample cap 20 pF [repo] R10 B-2
τ = 5 kΩ × 20 pF = 100 ns
acquisition = 1.5 clocks at 0.9 MHz = 1.67 µs = 16.7 τ → settling error 5.6e-8
load on the REF5050 buffer = 2.5 V / 10 kΩ = 250 µA, against 10 mA available
```

**Firmware** `[calc]`:

```
code_CH0 = 4096 · Vin / VREF
code_CH1 = 4096 · 2.500 / VREF          (2.500 V is genuinely fixed)
⇒ Vin = 2.500 · code_CH0 / code_CH1      — VREF cancels EXACTLY
scale back to counts:  corrected = code_CH0 × 3103 / code_CH1
   (3103 = 4096 × 2.5/3.3, the nominal CH1 code)
```

**What it cancels:** the DC load-regulation term, the key-chord droop, the Wi-Fi burst
(DC *and* transient), DFS steps, USB SOF, the LED PWM term in either Case A or Case B,
the LDO's temperature drift and its ±1 % initial accuracy — and, if CH1's divider
bottom leg returns to the same local ground as CH0's, the §5.3 ground-offset term as
well. Everything slower than ~50 kHz.

**What it does not cancel:** the 330 kHz switcher alias (§4, 0.9–1.8 counts) and any
intra-conversion noise, because the two conversions are sequential.

`[calc]` **residual and cost:**

```
conversion separation: 20–27 µs → cancels everything below ~40 kHz
CH1 quantisation: 1 LSB in 3103 = 3.2e-4 → 0.56 counts at the play code
→ the 30–123 count worst case collapses to ~1–2 counts
SPI2 budget: 122.7 µs → 149.4 µs of 250 µs = 60 %  [repo] carrier.md §4 — fits
parts: 2 × 0805 1 % metal film ≈ £0.02
```

**This is cheaper than the 10 µF capacitor whose stated justification §5.4 disproves,
and it is better than a separate voltage reference**, because it also removes the LDO
drift, the initial accuracy error and the ground term, none of which a fixed reference
would touch.

### 7.2 SECOND — 47–100 Ω in series into MCP3202 VDD. **£0.01.** Only *with* 7.1.

Put 47–100 Ω between the dev-board 3V3 and the ADC's VDD, in front of the existing
100 nF and the proposed 10 µF. `[calc]`:

```
100 Ω + 6 µF → corner 265 Hz → 18 dB at 2 kHz, 38 dB at 20 kHz
and it finally makes C-ADC-BULK do the job it was named for.
DC cost: MCP3202 I_DD ≈ 550 µA [from memory] × 100 Ω = 55 mV of offset
```

The 55 mV is a pure gain term that both the span knob and fix 7.1 remove. It also
damps the 12 kHz `C-ADC-BULK`/header resonance of §5.4.

**Do not fit this without 7.1.** The MCP3202's own supply current is code-dependent
(the internal DAC switches differently per conversion), so a bare series resistor
converts that into a *signal-dependent* reference error — a new nonlinearity in place
of an old gain error. With 7.1 in place, CH1 sees the same filtered node and the
correction still holds.

### 7.3 THIRD — the structural fix, if 7.1 and 7.2 are refused. **~£0.70.**

`[repo] carrier.md §2 and *Still open*` already names it: *"the fix is a separate rail
for the pull-ups or a real reference for the ADC, and both are board decisions"*.
Costed:

- **`U-ADC` MCP3202-CI/SN → MCP3204-CI/SL.** Same SPI family, same protocol, SOIC-14
  instead of SOIC-8, **a separate VREF pin**, and four channels instead of two.
  ~£0.30 over the MCP3202 `[from memory]` — `microchip.com` was 403 from this sandbox.
- **A 2.5 V reference:** LM4040DIM3-2.5 (SOT-23) or REF3025, ~£0.35 `[from memory]`.
- **Re-ratio `R-ADCDIV`:** 2.500 V / 4.7 V = 0.532, so 10 k / 11 k instead of
  10 k / 15 k. `[calc]` new full scale = 4.7 × 0.532 = 2.50 V = 4096 counts; real play
  2.34 × 0.532 = 1.245 V = 2040 counts; rest 0.2 × 0.532 = 0.106 V = 174 counts;
  playable span **1866 counts**, 17 % *better* resolution than today's 1594.
- One footprint change on a board not yet laid out.

This also frees two more ADC channels, which the *Still open* list would find uses for.

### 7.4 NOT worth doing — `R-KEY-PU` 2.2 k → 10 k

`[repo] cluster-boards.md §2` records this as a live trade (25.8 mA → 5.9 mA,
"3.2 LSB → 0.7 LSB"). `[calc]` at the play code it is 1.3 counts → 0.3 counts: it
removes the one term that was already inaudible, does nothing about Wi-Fi, the LEDs,
the switcher or the ground, and costs a 103 µs release τ in a humid cavity. **The
cluster-boards page is right to leave it alone — but for the wrong reason.** It should
be left alone because it is irrelevant, not because it is a close call.

### 7.5 Free, and not in any document

1. **Sequence SPI3 and SPI2** instead of running the key shift concurrent with the
   conversion (§2.4). Zero cost, removes a disturbance that is synchronous with the
   bit trials.
2. **Write the ADC supply-return layout rule** (§5.3) into carrier.md §2 before
   layout. Free now, impossible later.
3. **Note-gate hysteresis ≥ 100 counts** in firmware until 7.1 lands (§6). Written
   nowhere.
4. **Re-derive ADR 0014's 3 W clamp** against the ME6217's 800 mA, not only the
   R-78E5.0's 1 A, once §3.1 is measured.
5. **`C-ADC-BULK`: keep the part, rewrite the justification.** Its real job is halving
   load-step droop at 10–100 kHz, not filtering 2 kHz.

---

## What would change this report

One measurement, and it is ten minutes at E1: **which rail powers the ESP32-S3-Matrix's
64 LEDs.** If 5 V, this is a §6 Case B problem — still 9×–38× the accepted budget,
still fixed for £0.02. If 3V3, then §3.3 applies, ADR 0014's clamp is derived against
the wrong part, and the reference decision is not a trade that was mis-costed but a
topology that cannot work.

Two more, in order of value: the ME6217's **load-transient response** (step 0→30 mA
with a 5 µs edge, scope the 3V3 pin) — the parameter every number in §1.3 brackets and
the datasheet does not publish; and the **3V3 dip during a Wi-Fi TX burst** on the
assembled board, which is the single largest term in the table and is currently a
`[from memory]` range spanning 3×.

