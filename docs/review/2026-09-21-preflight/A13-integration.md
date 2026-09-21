# A13 — Integration: the things that are nobody's page

**Agent:** A13, cold. **Date:** 2026-09-21.
**Slice:** what happens *between* the schematic pages, and at moments no single
page describes — power-on and power-down across all six outputs at once, the
breath chain end to end, cable pull and re-plug, coupling between the two MCUs
and the analog path, and every cross-page dependency where two documents state
the same quantity.

**Cold:** `docs/review/**` was not read. Sources are the design corpus
(`hardware/**`, `docs/decisions/**`, `docs/reference/**`, `config/**`,
`firmware/**`, `README.md`, `ROADMAP.md`) and the 75 banked documents in
`datasheets/`.

**Provenance marks.** `[datasheet <doc> p.N]` — read out of a banked PDF this
session. `[repo file:line]` — read out of the corpus. `[calc]` — arithmetic
shown. `[from memory]` — not verified, treat as a lead. Unmarked claims are a
defect; there should be none.

**Already tracked, not rediscovered:** `dig-gnd-topology`, `cref-out-node`,
`riso-ref-topology`, `breath-working-point`, `pitch-cents-budget`,
`panel-height-budget`, `matrix-led-current`, `ref5050-grade`
`[repo config/figures.yaml]`. Where a finding below *touches* one of those it
says so.

**Method note on the datasheets.** Three of the strongest findings here came
from reading a banked PDF that the corpus cites but whose *neighbouring rows*
nobody read: the MPXV4006DP's Offset row (§2.1), the Waveshare board's power
net (§4.1), and the DAC8568's LDAC/command matrix (§1.5, §1.6). The pattern is
that a page fetched a datasheet to settle one question and stopped.

---

## 0. Findings, ordered by what they cost

| # | Finding | Severity | Nodes / refdes |
|---|---|---|---|
| **1.1** | Bus +5 V powers the buffer that drives the DAC's inputs; AVDD comes from the LM317. No sequencing control, no series resistance, and TI forbids it in words | **High** | `U-LVL-MOD` out, `U-DAC` pins 2/15/16, `AVDD` |
| **1.2** | Rack power-**down** exists nowhere in the corpus but one BOM note, and the schematic that owns the capacitors contradicts that note's fix. All six jacks are dragged toward −12 V for ~17 ms every time the rack is switched off | **High** | `C-BULK-RAIL` C1/C3, all six jacks |
| **1.4** | Pitch sits at **0 V — a VCO's base note** — for the whole 200–600 ms boot window and then steps to −2.500 V. ADR 0006's table says "below −2 V, subsonic" and its own next paragraph contradicts it | **High** | `PITCH` jack, `VREFOUT` |
| **1.5** | `LDAC` tied high + `LDAC` register default `0` ⇒ the plain "write to input register" command **never updates an output**. Written nowhere | **High** | `R-LDAC`, `U-DAC` |
| **2.1** | `sensor-full-scale` — a tracked, settled, *owned* figure — is wrong against the banked datasheet. The pedestal is **0.265 V typ**, not 0.200 V | **High** | `U-BREATH`, `config/figures.yaml` |
| **2.3** | `POT-OFFSET`'s "zero at centre" is **+0.60 V**, not the +0.07 V its own page tabulates. The page states both numbers, 250 lines apart | **High** | `POT-OFFSET`, `R-OFF`, `BREATH` jack |
| **2.4** | The response shaper's restore stage is the chain's **first clip point and it is ahead of the gain knob**. No knob avoids it | **High** | `U-RESP` b-half, `BREATH` jack |
| **3.1** | The in-amp rests at `+V_REF` when the cable opens, so the breath jack **steps by 0.22–1.73 V**. ADR 0006 has this right; ADR 0005, `ROADMAP.md` E10 and `breath-receive-stage.md` do not | **High** | `R-BIAS-INAMP`, `BREATH` jack |
| **3.2** | RJ45 has no make-first/break-last contact. A pin-8-first withdrawal opens **both grounds while +12 V is still mated** | **High** | `J-UMBILICAL` pins 3/6/8, `U-LVL-MOD` in |
| **4.1** | The dev board's header 5 V pin is `VCC_5V`, **downstream** of the `B5819WS` — so ADR 0014's newly adopted binding constraint does not apply in the instrument's own configuration | **High** | `HDR-DEV` 5 V, `U-MCU-RT` |
| **4.2** | The 3V3 LDO's input is `VCC_5V`, the same node as the 64 matrix LEDs, and its output is the MCP3202's `VREF`. Breath → matrix → `VREF` → breath is a closed loop | **High** | `VCC_5V`, `U-ADC` `VDD` |
| **1.6** | "No write order avoids it" is refuted by the part: command `0010` is a software `LDAC` that updates all eight channels at once | Medium | `U-DAC` |
| **1.3** | The module's own ±12 V current split is stated three ways, and `C-BULK-RAIL`'s value depends on which is true | Medium | `C-BULK-RAIL`, `D-REVPOL` |
| **2.2** | `carrier.md` derives the ADC divider from **4.7 V** while its own drawing two inches above says 4.80 V. The checker cannot see it | Medium | `R-ADCDIV` |
| **2.6** | The analog breath drift figure ("~20 mV in 10 V", unverified) is bounded by the banked datasheet **26× higher**, and the datasheet's validity window is 2–4× narrower than the corpus's own interior temperature rise | Medium | `U-BREATH`, `TRIM-BREATH-ZERO` |
| **2.8** | `±11.45 V` of op-amp headroom is a **nominal-rail** figure. At Eurorack −5 % the analog rail is 11.25 V. Three pages size margin against the nominal | Medium | `U-OPA-PITCH`, all six jacks |
| **3.3** | Contact bounce on insertion: the hot-plug analysis assumes the far capacitor starts at 0 V | Medium | `U-LOADSW`, FET |
| **3.4** | Re-plug: the DAC never reset, so it holds the pre-unplug codes; breath comes back ~100 ms before pitch and the mods do | Medium | `U-DAC`, `BREATH` jack |
| **3.5** | The cable-side `CS` pull-up is specified, in two documents, to **a rail the module does not have** | Medium | `R-SPI-PULL` |
| **4.5** | With the instrument off and the cable connected — the corpus's *normal resting state* — `CS` at the buffer input sits at ~0.7 V, below `V_IL`, so the DAC's `SYNC` is held **asserted** continuously | Medium | `R-SPI-PULL`, `U-DAC` `SYNC` |
| **4.3** | `ME6217` load regulation is **50 mV max** over 1–300 mA; `carrier.md`'s `[from memory]` figure understates the max case, and the ESP32-S3's own activity swing is a bigger aggressor than the key pull-ups and is not costed | Medium | `U-ADC` `VDD`/`VREF` |
| **4.6** | No SPI→`BREATH` pair-to-pair crosstalk figure exists anywhere | Medium | `J-UMBILICAL` pairs (1,2) vs (4,5) |
| **5.x** | Eleven cross-page quantity disagreements, tabulated in §5 | Mixed | — |

---

## 1. Power-on and reset, across all six outputs at once

The corpus has **no transient analysis of any kind**, and the five scattered
power-on claims do not compose. Here is the sequence, with a state for each of
the six jacks at each step.

### 1.0 The sequence

| # | Event | Timing | PITCH | MOD 1–4 | BREATH |
|---|---|---|---|---|---|
| 0 | Rack off | — | 0 V | 0 V | 0 V |
| 1 | Rack switched on. Bus +12/−12/+5 rise in the PSU's own order | ms | undefined during the ramp — `R-BIAS-DAC` 100 k holds each DAC output node at 0 V and `R-BIAS-INAMP` holds the in-amp's inputs `[repo hardware/bom.csv R-BIAS-DAC, R-BIAS-INAMP]` | as pitch | undefined |
| 2 | LM317 brings `AVDD` to 5.21 V; DAC's power-on reset fires | ms | **0.000 V** | **0 V** | — |
| 3 | Analog ±12 V settle; `TRIM-BREATH-ZERO`'s divider (off `AVDD`) settles | ms | 0.000 V | 0 V | **OFFSET knob less 0.2–1.7 V** (§3.1) |
| 4 | Panel toggle on → `LT1641` `ON` above 1.313 V and `VCC` above UVLO `[datasheet LT1641.pdf p.2, via repo hardware/module/power-entry.md]` | — | unchanged | unchanged | unchanged |
| 5 | Load switch ramps the umbilical: **49–197 ms**, 98 ms typ `[repo config/figures.yaml loadswitch-gate-cap]` | 49–197 ms | unchanged | unchanged | unchanged |
| 6 | Instrument's buck starts above 8 V in `[repo datasheets/discrete-and-power/R-78E5.0-1.0.pdf via bom.csv U-BUCK]`; ESP32-S3 boot ROM + bootloader window, GPIOs Hi-Z, "order 100–300 ms" `[repo hardware/controller/carrier.md §5, marked [from memory] there]` | +100–300 ms | unchanged | unchanged | **steps up by 0.2–1.7 V** the moment the REF5050 and the sensor are alive — *before* any DAC write |
| 7 | Firmware's **first** DAC write: enable internal reference `[repo hardware/module/pitch-stage.md]` | ~1 word | **steps 0 V → −2.500 V** | stays 0 V (ch 7 still zero) | unchanged |
| 8 | Firmware writes the five signal channels and ch 7 | 100–200 µs `[repo hardware/module/digital-and-supervision.md:250]` | to the note | **transient −10.00 V or +11.45 V** depending on order (§1.6) | unchanged |
| 9 | Steady state | | note | modulation | breath |

Total from panel toggle to first valid CV: **~150 ms best case, ~500 ms worst**
`[calc: 49 + 100 = 149; 197 + 300 = 497]`. Nothing in the corpus states this
number, and `ROADMAP.md`'s E-track has no step that observes it.

### 1.1 [High] The DAC's digital inputs are driven from a rail its own supply does not track

**Node:** `U-LVL-MOD` outputs → `U-DAC` pins 2 (`SYNC`), 15 (`DIN`), 16 (`SCLK`).

`U-LVL-MOD`, a 74AHCT125, runs from the **rack bus +5 V** — through `FB4` and
`C4` only, with no diode `[repo hardware/module/power-entry.md:49-50, and
bom.csv U-LVL-MOD: "Runs from bus +5V; the DAC runs from U-REG-DAC"]`. The
DAC's `AVDD` comes from the `LM317LZ` behind `D1`, `FB1` and `C1`
`[repo hardware/module/power-entry.md:15-20]`. **These are different rails with
different startup paths and nothing sequences them.**

Three facts from banked documents:

- `[datasheet DAC8568CIPW.pdf p.2]` Absolute maximum: *"Digital input voltage to
  GND −0.3 to **+AVDD + 0.3 V**"*.
- `[datasheet DAC8568CIPW.pdf, Power-On Reset section]` TI states the rule in
  words: *"**No device pin should be brought high before power is applied to
  the device.**"*
- `[datasheet SN74AHCT125.pdf p.3]` The buffer's `V_OH` is **4.4 V min** at
  −50 µA and 3.8 V min at −8 mA, and its outputs carry clamps in both
  directions (`I_OK` ±20 mA) — so it is a genuine 4.4 V source into those pins.

There is **no series resistance** between the buffer's outputs and the DAC's
inputs `[repo hardware/module/digital-and-supervision.md:21-51]` — `R-SPI-SER`
is the *instrument*-end part `[repo hardware/controller/carrier.md §4]`. So if
the rack's +5 V leads the LM317's output by any margin, three pins are driven
to 4.4 V with `AVDD` near zero, and the only current limit is the buffer's own
drive strength (±25 mA continuous `[datasheet SN74AHCT125.pdf p.3]`).

The DAC-side pull resistors do **not** cover this: `bom.csv` puts the DAC-side
`CS` pull-up on `AVDD` and `SCLK`/`MOSI` pull-downs on ground
`[repo hardware/bom.csv R-SPI-PULL]`, which is correct and is a different
mechanism from the buffer actively driving.

Which rail leads is a property of the rack PSU, not of this module, and the
corpus never asks. The opposite order is safe (`AVDD` up, buffer VCC down →
outputs weak, pulls define the pins).

**Two fixes, and one of them is already wanted for other reasons.**
`digital-and-supervision.md:108-116` records that *"three reviewers
independently want [the bus +5 V rail] dropped"* and that deriving the
buffer's rail locally is *"one TO-92 and two capacitors"*. Deriving it from
`AVDD` — or from the same LM317 — makes the sequencing hazard structurally
impossible, because the buffer then cannot be powered before the part it
drives. Failing that, **1 kΩ in series on each of the three lines at the DAC**
bounds the injection to under 5 mA. Either is cheap; neither exists.

### 1.2 [High] Rack power-down is analysed nowhere, and the schematic contradicts the one place it is

**Node:** `C-BULK-RAIL` C1 (+12 V) and C3 (−12 V); all six output jacks.

Grepping the whole design corpus for power-down returns **one** hit, in free
text inside a BOM note `[repo hardware/bom.csv C-BULK-RAIL]`:

> *"at 47 µF each it collapses 2.2× faster and every rack power-down leaves the
> op-amps with V+ near 0 and V− at −6 to −8 V for ~30 ms, pulling all six jacks
> toward the surviving negative rail. 100 µF on +12 V balances the decay."*

I rebuilt it from datasheets rather than trusting it, and it is real.

```
[calc] +12 V analog load
  OPA2197  1.0 mA typ per amplifier x 12 amplifiers   = 12.0 mA
           [datasheet OPA2197.pdf p.8: "IQ ... per amplifier, IO = 0 A, 1 / 1.3 mA"]
  INA828   0.6 mA typ                                 =  0.6 mA
           [datasheet INA828IDR.pdf: "IQ ... VIN = 0 V, 600 / 650 uA"]
  LM317 branch: 1.25 V / 150 R divider 8.33 mA
                + DAC8568 1.25 mA                     =  9.6 mA
           [repo bom.csv R-REG-SET; datasheet DAC8568CIPW.pdf p.1
            "Ultralow Power Operation: 1.25mA at 5V Including Internal Reference"]
  R-LED-PANEL 2.2 k from +12 V, LED ~2 V              =  4.5 mA
                                               total  = 26.7 mA

[calc] -12 V analog load
  OPA2197 x 12 + INA828 + R-OFFNEG (12 V / 95.3 k)    = 12.7 mA

  ratio 2.10 : 1
```

With the **4 × 47 µF the schematic draws** `[repo
hardware/module/power-entry.md:15-50 and :513 "Entry bulk is 4 × 47 µF"]`:

```
[calc] dV/dt(+12) = 26.7 mA / 47 uF = 568 V/s
       dV/dt(-12) = 12.7 mA / 47 uF = 270 V/s
       +12 V falls 11.85 -> 2 V in 9.85 / 568 = 17.3 ms
       in that time -12 V has fallen only 4.7 V, so it is still at -7.2 V
```

That reproduces the BOM note's "−6 to −8 V" independently. **Every six jacks
get dragged toward −7 V for ~17 ms at every rack power-down**, through
op-amps whose positive rail has gone and whose common-mode range is violated.
`D-JACK-CLAMP` cannot help — it clamps to the same collapsing rails.

Two things are wrong beyond the transient itself:

1. **The owning page does not carry the fix.** `power-entry.md` draws and names
   4 × 47 µF; `bom.csv` says "NOT 47 µF on every rail" and specifies 100 µF on
   +12 V. A board built from the schematic has the defect the BOM was edited to
   remove. (With 100 µF: `[calc]` 267 V/s against −12 V's 270 V/s — balanced,
   and the BOM's fix is correct.)
2. **The BOM note's own premise is stale.** It counts *"the LM317's divider,
   the DAC and **the comparator**"* among the +12 V loads. The LM311 presence
   comparator is deleted `[repo hardware/module/digital-and-supervision.md:55,
   133-149]`. The conclusion survives — my recount without the comparator still
   gives 2.10:1 — but it is a live argument resting on a deleted part, which is
   the failure mode `CLAUDE.md` §4 names.

**Recommended:** move the 100 µF into `power-entry.md`'s drawing and add one
line stating the power-down behaviour, because the observable symptom is "the
rack burps downward every time I switch off", which reads as a fault.

### 1.3 [Medium] The module's own rail currents are stated three ways

| Source | +12 V module | −12 V module | Ratio |
|---|---|---|---|
| `[repo docs/decisions/0004-cv-interface-module.md:265-269]` | ~45 mA | ~40 mA | 1.1 |
| `[repo hardware/bom.csv C-BULK-RAIL]` | ~22 mA | ~10 mA | 2.2 |
| `[calc]`, §1.2 above, from banked Iq figures | ~27 mA | ~13 mA | 2.1 |

`C-BULK-RAIL`'s value is decided by that ratio, so the disagreement is not
cosmetic. ADR 0004's 1.1:1 would say the 47 µF/47 µF pair is fine; it is the
outlier and it is the one a reader sizing rails would find first. My figure
and the BOM's agree on the ratio.

A secondary consequence: `D1` carries only ~27 mA, not the 359 mA `D2` carries,
so its `V_f` is around 0.15 V `[datasheet 1N5817.pdf, extrapolating below the
0.24 V-at-245 mA point the repo digitised — marked as an extrapolation]`, not
the "roughly 0.3–0.4 V at this current" ADR 0004 quotes for the umbilical
branch. The analog rail is therefore **higher** than the corpus assumes. See
§2.8, where the error runs the other way.

### 1.4 [High] Pitch plays the VCO's base note for the whole boot window

**Node:** `PITCH` jack, `VREFOUT`.

`pitch-stage.md` gets the mechanism right:

> *"`V_ref` is the DAC's internal reference, which is **disabled until firmware
> writes an enable** — so *both* terms are zero and the jack sits at **0 V, a
> VCO's base note**, until that write. After it, `CLR` parks at −2.500 V. ADR
> 0006's power-on table asserts 'below −2 V' for both; they are different
> states, 2.5 V apart."* `[repo hardware/module/pitch-stage.md]`

Confirmed at the part: `[datasheet DAC8568CIPW.pdf, Power-On Reset section]`
*"The internal reference is powered off / down by default and remains that way
until a valid reference-change command is executed."* And with the reference
off, the `VREFIN/VREFOUT` pin is an **input**, presenting 8 kΩ
`[datasheet DAC8568CIPW.pdf p.4, "Reference input impedance 8 kΩ"]` — so
`TRIM-OFFSET`'s divider sees a low impedance to ground and the pitch reference
node really is 0 V, not floating. The claim holds.

**What has not landed, and what nobody has said:**

- **ADR 0006's table row is still wrong**, and the fix went in at
  `pitch-stage.md` only: *"| **Pitch** | Bottom of its range, below −2 V |
  Subsonic. A VCO there is inaudible |"* `[repo
  docs/decisions/0006-cv-channel-allocation.md:197-199]`.
- **ADR 0006 contradicts itself thirty lines later**: *"It also means the
  outputs sit at 0 V from rack power-on until firmware enables the reference,
  **which happens to reinforce the table above**"* `[repo
  docs/decisions/0006-cv-channel-allocation.md:227-230]`. It does not reinforce
  it; it refutes it. A reader who checks one paragraph against the other cannot
  tell which is current.
- **Nobody states that this is a step on a live jack.** The interval at 0 V is
  the whole of steps 1–6 in §1.0 — **150 to 500 ms** — and 0 V is not subsonic,
  it is the VCO's base note, audible into any patch left connected. Then it
  steps down 2.5 V. The audible event at every rack power-on is *a note, then a
  downward swoop*, and the ADR says "inaudible".

**Recommended:** correct ADR 0006's table row to the two-state form
`pitch-stage.md` already gives, delete the "reinforces" sentence, and add the
duration. If the base note matters musically, the cheap fix is firmware's
first DAC write being the reference enable *and* a pitch code in the same
burst, which shortens the audible window to the boot time rather than removing
it — there is no hardware fix short of a jack relay, which ADR 0006 already
declined for breath on the same grounds.

### 1.5 [High] `LDAC` tied high means the ordinary write command never updates an output

**Node:** `R-LDAC`, `U-DAC`.

`R-LDAC` ties `LDAC` to `AVDD`, inactive, not driven `[repo
hardware/module/digital-and-supervision.md:49-50, bom.csv R-LDAC]`.

`[datasheet DAC8568CIPW.pdf, LDAC Functionality]`: *"The default value for each
bit [of the LDAC register], and therefore for each DAC channel, is zero. …
**if the LDAC register bit is set to '0', the DAC channel is controlled by the
LDAC pin.**"*

And `[datasheet DAC8568CIPW.pdf p.35, Table 11]` the command `C3..C0 = 0000` is
*"Write to input register — DAC Channel n"* — buffer only, no update.

So on a virgin part with `LDAC` strapped high, **a firmware that uses the
plain write command loads six data buffers and leaves all six outputs at zero
scale forever.** Firmware must use `C = 0011` (*"Write to DAC Input Register
Ch n and update DAC register Ch n"*) or `C = 0010` (see §1.6).

This is precisely the shape of bring-up trap the corpus already collects — ADR
0006 records the internal-reference-disabled trap in the same words: *"a board
that looks dead at E7 with every channel reading 0 V is usually this, not a
soldering fault"* `[repo docs/decisions/0006-cv-channel-allocation.md:226-228]`.
The `LDAC` trap sits beside it and is written down nowhere:
`firmware/README.md` does not mention `LDAC` at all, and
`digital-and-supervision.md` asserts the *consequence* ("the six populated
channels update as each word lands") without the command that makes it true.

**Recommended:** one line in `firmware/README.md`'s architecture constraints,
and one line on `digital-and-supervision.md`'s `R-LDAC` bullet.

### 1.6 [Medium] "No write order avoids it" is refuted by the part

`digital-and-supervision.md:250-253` records, as an accepted cost:

> *"a hardware `LDAC` was considered and declined, so the six populated channels
> update as each word lands rather than together. The cost is real and accepted
> — **every exit from `CLR` throws intermediate values at the mod jacks for
> 100–200 µs and no write order avoids it.**"*

`[datasheet DAC8568CIPW.pdf p.36, Table 11]` — the part has a software `LDAC`:

> *"Write to Selected DAC Input Register and Update All DAC Registers …
> `0 X 0 0 1 0 | A3..A0 | Data` — Write to DAC input register Ch n and **update
> all DAC registers (SW LDAC)**"*

So: five words with `C = 0000` (buffer only), then the sixth with `C = 0010`,
and **all six outputs change on the same clock edge**. The intermediate values
are deleted in firmware, for free, with no extra word and no GPIO.

This matters more than 100–200 µs sounds, because §1.0 step 8 shows what the
intermediates *are*. With `Vout = 4·Vdac − 3·V_ref` `[repo
hardware/module/mod-channels.md]`:

```
[calc] ch 7 written before the signal channels:  4 x 0      - 3 x 3.3333 = -10.00 V on all four
       signal channels written before ch 7:      4 x Vdac  - 0          = up to +11.45 V (rails)
```

Four jacks slamming to −10 V or to the positive rail, at every boot and every
`CLR` exit. The corpus knows the magnitudes — `firmware/README.md` and
`mod-channels.md` both derive them for the *stuck* case — but files the
transient version as unavoidable.

**Recommended:** adopt the `0010` form, close the open `LDAC`-becomes-a-GPIO
item in `digital-and-supervision.md`, and delete the "no write order avoids
it" sentence.

### 1.7 [Low] "Exactly 0 V" on the mod jacks is exact to about ±28 mV

`[datasheet DAC8568CIPW.pdf p.3]` Zero-code error is **1 mV typ / 4 mV max**.
`[calc]` Worst case, with independent errors of opposite sign on a signal
channel and on ch 7: `4 × (+4 mV) − 3 × (−4 mV) = +28 mV` at a mod jack. Also
`[datasheet DAC8568CIPW.pdf p.3]` *"Power-on glitch impulse … `AVDD` = 5.5 V,
10 mV"* — through pitch's gain of 2 that is 20 mV at the jack, which
`[calc]` is **24 cents**.

Neither is a problem. They are worth a parenthesis because ADR 0006 and
`mod-channels.md` both use the word "exactly", and `pitch-stage.md`'s error
budget is denominated in hundredths of a cent.

---

## 2. The breath chain, end to end

Stages, in order, with the reference for each:
sensor → instrument buffer → `R1` 1 k → 2 m Cat5 → `R2`/`R3` 10 k + 1 M bias
pair → INA828 → *(proposed)* response shaper → `POT-GAIN` attenuator + buffer →
×4 inverting summer with the offset legs → `R-OUT-PROT` 1 k + 330 nF → jack.

### 2.1 [High] The sensor's pedestal is 0.265 V, not 0.200 V — and `sensor-full-scale` is a tracked figure

**Node:** `U-BREATH`; `config/figures.yaml` entry `sensor-full-scale`.

`config/figures.yaml` owns it:

```
  - id: sensor-full-scale
    value: "4.80 V"
    status: settled
    derivation: "0.2 V + 0.766 V/kPa x 6 kPa = 4.796 V"
    forbidden: ["4.7 V output", "0.2-4.7 V", "0.2 – 4.7 V"]
```

The datasheet is banked and says otherwise, in two independent places on one
page `[datasheet MPXV4006DP.pdf p.3]`:

> *"Offset … `Voff` … **0.152 / 0.265 / 0.378** V"*
> *"Transfer Function (kPa): `Vout = VS × [(0.1533 × P) + 0.053]`"*

```
[calc] transfer function at P = 0:  5.000 x 0.053           = 0.265 V   (= the typ Offset row)
       sensitivity:                 5.000 x 0.1533          = 0.7665 V/kPa  (the repo's 766 mV/kPa, confirmed)
       full scale at 6 kPa:         0.265 + 0.7665 x 6      = 4.864 V
       full-scale span:             4.864 - 0.265           = 4.599 V   (= the datasheet's VFSS 4.6 V, confirmed)
```

So the register's **sensitivity is right and its pedestal is wrong**, and the
error is 65 mV — a third of the value it states. Where 0.200 V came from is
visible in the register's own `forbidden` list: the corpus moved off the
marketing range "0.2–4.7 V" by correcting the **top** end to 4.80 V and
keeping the bottom. The datasheet's own numbers are **0.265–4.864 V**.

This is exactly the case `CLAUDE.md` §3 legislates for: *"A number read off a
banked document beats one from a review."* It is a settled, owned, cited
figure and it is wrong against a document that is in the repo.

**What moves and what does not** — most of the chain is safe, because the
pedestal is nulled at the in-amp's `REF` and only the *span* propagates:

| Consumer | Effect |
|---|---|
| Span, hard blow, in-amp output, jack span | **unchanged** — all derived from Δ, and Δ is set by the sensitivity |
| `TRIM-BREATH-ZERO` nominal, +0.437 V | should be `0.265 × 2.161 = 0.573 V` `[calc]`. Still inside the 0→1.0 V range, which was correctly derived from the 0.152–0.378 V **band** `[repo hardware/module/breath-receive-stage.md]`. No part changes |
| ADC headroom, `R-ADCDIV` | moves — see §2.2 |
| `sensor-full-scale` register entry | **wrong; fix it, and put 4.7 V's relatives in `forbidden` in a form the checker catches** |

### 2.2 [Medium] `carrier.md` derives the ADC divider from a value its own drawing refutes

**Node:** `R-ADCDIV`, `U-ADC` `CH0`.

The drawing says `MPXV4006DP Vout 0.2 – 4.80 V`. Eighty lines below, the
derivation says `[repo hardware/controller/carrier.md §2 Derivations]`:

```
full scale = 4.7 V × 0.6 = 2.82 V  against VREF 3.3 V → 85 % of range, 3502 counts
```

Two errors compound: the 4.7 V is the superseded marketing figure, and even
4.80 V is wrong per §2.1.

```
[calc] correct:  4.864 V x 0.600 = 2.918 V ;  2.918 / 3.3 = 88.4 % ;  3623 counts
       stated:   4.7   V x 0.600 = 2.82  V ;                 85 %  ;  3502 counts
```

Still comfortably inside range, so nothing breaks — but **the checker cannot
see this**, and that is the point worth recording. The `forbidden` list holds
`"4.7 V output"`, `"0.2-4.7 V"` and `"0.2 – 4.7 V"`; the live text is
`4.7 V × 0.6`, which matches none of them. `[repo, verified: `tools/check-staleness.py`
reports PASS on this file.]` The same gap lets `docs/decisions/0005-power-architecture.md:74`
carry *"a 5 V part outputting **0.2–4.7 V**"* — an en dash with no spaces,
one character away from a forbidden string.

**Recommended:** when `sensor-full-scale` is corrected, add bare-number
patterns (`4.7 V ×`, `0.2–4.7`, `4.80 V ×`) to `forbidden`, and re-run.

### 2.3 [High] `POT-OFFSET`'s "zero at centre" is +0.60 V, and the page states both numbers

**Node:** `POT-OFFSET` wiper, `R-OFF` 21.0 k, `R-BREATH-SUM`.

`breath-output-stage.md` tabulates the offset law:

| Pot | Wiper | Offset at the jack |
|---|---|---|
| Full CCW | 0 V | +5.04 V |
| **Centre** | 2.605 V | **+0.07 V** |
| Full CW | 5.21 V | −4.89 V |

Two hundred and fifty lines later, **the same file** quotes the opposite:

> *"`A5` showed `POT-OFFSET`'s wiper is unbuffered, which is why its 'zero at
> centre' actually sits ~20° past centre at **+0.605 V**."*
> `[repo hardware/module/breath-output-stage.md §4]`

And between them, the Values section asserts the design intent: *"**This wiper
does *not* need buffering.** … For an offset knob that is feel, not error."*

I reproduced both numbers, and the second one is correct:

```
[calc] summer, inverting, virtual ground; R-FB 40 k, R-OFF 21.0 k, R-OFFNEG 95.3 k
  Vjack(offset) = -40k x ( Vw / 21.0k - 12 / 95.3k ) = -1.9048 Vw + 5.037

  BUFFERED wiper at centre:   Vw = 2.605 V            -> +0.075 V   (the table)
  UNBUFFERED wiper at centre: pot 10 k across 0..5.21 V, p = 0.5
       Vth = 2.605 V, Rth = 10k x p(1-p) = 2.5 k
       loaded by R-OFF 21 k to a virtual ground:
       Vw = 2.605 x 21/(21+2.5) = 2.3279 V             -> +0.603 V   (§4's figure)
```

The endpoints are exact either way (`Rth = 0` at both ends), so **only the
middle of the travel is wrong** — which is the half of the control the page
made a feature of ("zero at centre", and a centre-detent proposal in *Still
open*).

Consequences that cross pages:

- `breath-receive-stage.md`'s commissioning step 3 promises *"Panel OFFSET for
  where you want the jack to rest — **±5 V, zero at centre**"*. It is not.
- `ROADMAP.md` E10 commissions in that order. A player who centres the knob and
  expects 0 V gets +0.60 V into whatever is patched.
- The law is **non-linear in rotation** throughout, not just at centre —
  `Rth = 10k·p(1−p)` — so the knob's feel is squashed in the middle and exact
  at the ends. That is not recorded.

**The fix is contested inside one file.** §4 says the fix "wants a half, and
this stage takes the last two", and `bom.csv`'s `U-RESP` row says the same:
*"This stage consumes BOTH remaining spare OPA2197 halves, so the separate A5
finding … needs this additional package."* `[repo hardware/bom.csv U-RESP]` So
the seventh package exists in the BOM partly to buffer this wiper — while the
page's Values table still says the wiper does not need buffering, and the
offset table still prints the buffered answer. **Three states of the same
decision, in two files.**

**Recommended:** pick one. If the wiper is buffered, the table is right and the
Values note must change. If it is not, the table must be recomputed with the
loading term and "zero at centre" withdrawn. Either way `U-RESP`'s justification
has to say which halves do what (see §5.2).

### 2.4 [High] The response shaper clips before the gain knob, and no knob avoids it

**Node:** `U-RESP` restore half, between the in-amp and `POT-GAIN`.

The shaper is two inverting halves: `÷2` with the diode branch, then `×2` to
restore scale and polarity `[repo hardware/module/breath-output-stage.md §4,
"What it costs"]`. Its own table gives the gain ratio the diode branch
produces:

| Dynamic | In-amp | Gain ratio |
|---|---|---|
| hard blow | 4.64 V | 1.494 |
| full scale | 9.94 V | **1.586** |

```
[calc] restore-stage output demanded at full scale:  9.94 V x 1.586 = 15.77 V
       OPA2197 on the module analog rails reaches about  11.3-11.5 V
       -> the last row of the stage's own table is not realisable

       clip point:  |Vin| x ratio(Vin) = 11.3 V, ratio ~ 1.5
                    -> Vin ~ 7.5 V at the in-amp
                    -> sensor delta = 7.5 / 2.161 = 3.47 V
                    -> P = 3.47 / 0.7665 = 4.53 kPa
```

**4.5 kPa is 75 % of the sensor's range and about 1.6× a hard blow** (2.8 kPa,
and that figure is itself `breath-working-point` DISPUTED). An overblow, a
cough into the mouthpiece, or a player at the top of the disputed 3–4 kPa band
with the knob toward exponential reaches it.

**Why this is different from the clip the page already documents.**
`breath-output-stage.md` is explicit and correct about the *output* stage:
*"offset at +5 V and gain at 4× puts a hard blow at +23 V … That is the
player's business and it is what the gain knob is for."* The shaper's clip is
**upstream of `POT-GAIN`** — deliberately, because the page wants the knee at a
fixed fraction of full breath — so **turning the gain down does not avoid it**.
It is the first non-defeatable clip point in the chain and the page's headroom
section does not mention it.

**Recommended:** either scale the restore stage at less than ×2 (accepting a
smaller jack span, recoverable at `POT-GAIN`), or bound `R-RESP` so the
maximum ratio × full scale fits the rails. `R-RESP` at 15 k is already flagged
as "a first sizing" wanting a bench pass; this is a hard constraint on that
pass, and it belongs in the §4 *Open before layout* list beside the polarity
item.

### 2.5 [Medium] The chain, arithmetically, in one place — and the three-way hard-blow figure

Nothing in the corpus states the total. Here it is.

```
[calc] stage gains
  sensor                     0.7665 V/kPa                 [datasheet MPXV4006DP.pdf p.3]
  instrument buffer          x 1
  bias-divider loss          x 1M/(1M+11k) = 0.98912       [repo breath-receive-stage.md]
  INA828, RG = 42.2 k        x (1 + 50k/42.2k) = 2.184834
     effective               x 2.16107                    [= config/figures.yaml inamp-full-scale derivation]
  response shaper            x 1.000 to 1.586 (CW) or 0.6-1.0 (CCW), signal-dependent
  POT-GAIN attenuator        x 0.125 to 1.000
  summer                     x 4 (R-FB/R-IN)
  -------------------------------------------------------------------
  total, shaper centred      0.7665 x 2.16107 x (0.5 .. 4) = 0.828 .. 6.63 V per kPa
```

| Input | In-amp out | Jack, GAIN min (0.5×) | Jack, working (2.13×) | Jack, GAIN max (4×) |
|---|---|---|---|---|
| Rest (0 kPa) | 0.00 V | OFFSET | OFFSET | OFFSET |
| Hard blow, 2.8 kPa | −4.64 V | +2.32 V | +9.9 V | +18.6 V → **rails** |
| Sensor FS, 6 kPa | −9.94 V | +4.97 V | +21 V → **rails** | rails |

Reading: the usable region is a diagonal band, and **at any gain above about
2.4× a hard blow clips even with OFFSET at zero** `[calc: 11.3 / 4.64 = 2.44]`.
The page's "their sum has to fit in ±11.5 V" is the right rule; the number that
makes it actionable — the gain above which the knob is self-defeating — is not
stated.

**And the hard-blow figure is given three ways, on two pages**, because two
different in-amp gains are in circulation:

| Value | Where | Which gain it used |
|---|---|---|
| **−4.69 V** | `breath-output-stage.md`, "What it has to do" table | raw 2.1848 `[calc: 2.147 × 2.1848 = 4.691]` |
| **4.64 V** | `breath-output-stage.md` §4, shaper table | effective 2.16107 `[calc: 2.147 × 2.16107 = 4.640]` |
| **"about −4.7 V"** | `breath-receive-stage.md` Commissioning | rounded from either |

The same slip produced `TRIM-BREATH-ZERO`'s nominal: `+0.437 V` is
`0.200 × 2.1848`, where the pedestal it nulls arrives at the in-amp attenuated
by the same 0.98912 the full-scale figure uses `[calc: 0.200 × 2.16107 =
0.432 V]`. `config/figures.yaml`'s `inamp-full-scale` entry uses the effective
gain and is the authority; the 2.1848 uses are the stale side. None of it
matters electrically — the trimmer is set on a bench — but it is the same
value diverging in three places, which is the defect this project is about.

### 2.6 [Medium] The analog path's drift bound is 26× what the page estimates, and the datasheet's window is narrower than the corpus's own temperature rise

`breath-receive-stage.md` closes commissioning with:

> *"Thermal drift afterwards is on the order of **20 mV in 10 V** over a full
> warm-up — a quarter turn if it ever bothers you. **That figure is
> unverified**: it rests on an offset tempco of ~0.5 mV/K that the sensor
> family's datasheet apparently does not break out, and nxp.com was
> unreachable when this was written."*

The datasheet is now banked. It still does not break out TcOffset — the page
was right about that — but it **does** bound the total, and it attaches a
condition nobody has `[datasheet MPXV4006DP.pdf p.3, Table 1 and note 5]`:

> *"Accuracy (10 to 60 °C) … **±2.46 %V_FSS with auto zero** / **±5.0 %V_FSS
> without auto zero**"*
> *"Autozeroing is defined as storing the zero pressure output reading and
> subtracting this from the device's output during normal operations. **The
> specified accuracy assumes a maximum temperature change of ±5 °C between
> autozero and measurement.**"*

```
[calc] +/-2.46 % of VFSS 4.6 V             = +/-113 mV at the sensor
       x 2.16107 (in-amp)                  = +/-244 mV at the in-amp output
       x 2.13 (working downstream gain)    = +/-520 mV at the jack  = 5.2 % of span
  without auto-zero, +/-5.0 % VFSS         = +/-230 mV -> +/-1.06 V at the jack
```

Two things follow, and they split the two representations:

- **The digital copy is fine.** ADR 0006 mandates a continuous auto-zero
  decaying toward the current reading `[repo
  docs/decisions/0006-cv-channel-allocation.md, "Ambient zero is continuous"]`,
  which is precisely the datasheet's own autozero, so the ±2.46 % applies to
  it and the ±5 °C window is met by construction.
- **The analog CV is not.** Its only zero authorities are
  `TRIM-BREATH-ZERO`, set once at build, and the panel OFFSET knob
  `[repo hardware/module/breath-receive-stage.md, the split-authority table]`.
  So the analog path is the **"without auto zero"** column, and ADR 0006's own
  interior-rise figure — *"on the order of 10–20 K over the first 10–20
  minutes"* — is **2 to 4× outside the ±5 °C validity window** of even the
  better number.

I am not claiming ±1 V of real drift: ±2.46 %/±5.0 % is a *total* error budget
(linearity, both hystereses, offset stability, TcSpan, TcOffset) and a maximum,
not a typical. The claim is narrower and holds: **the only sourced bound on
this quantity is 26× the unsourced estimate the page dismisses it with, and
the datasheet voids even that bound over the corpus's own warm-up.** Per
`CLAUDE.md` §3, the banked number wins.

**Recommended:** E2 measures it (`ROADMAP.md` already scopes a warm-up run).
Until then, state the bound rather than the estimate, and note that "a quarter
turn, once" may be "a quarter turn per set".

### 2.7 [Low] Noise is a non-issue, and the corpus never says so

There is no noise budget for the breath chain anywhere. One, so it is not
re-opened:

```
[calc] INA828 at G = 2.1848
  eN(RTI) = sqrt( eNI^2 + (eNO/G)^2 ) = sqrt( 7^2 + (90/2.1848)^2 ) = 41.8 nV/rtHz
      [datasheet INA828IDR.pdf: eNI 7 nV/rtHz, eNO 90 nV/rtHz, and the formula in note (5)]
  output-referred: x 2.1848 = 91 nV/rtHz
  R2+R3 = 20 k differential johnson: 18.2 nV/rtHz RTI -> 40 nV/rtHz out
  total ~ 100 nV/rtHz at the in-amp output

  noise bandwidth set by the 482 Hz jack pole: ENBW = 1.57 x 482 = 757 Hz
  2.75 uV RMS at the in-amp -> x 2.13 -> ~5.9 uV RMS at the jack
  against a 10 V span: 0.6 ppm, ~124 dB
```

The chain is quiet by four orders of magnitude more than it needs to be. The
breath channel's real error budget is **entirely DC**: §2.6's drift, §2.3's
offset-knob error, and — on the digital copy only — §4.3's reference movement.
Worth one line on `breath-receive-stage.md` so the next reviewer does not
spend a day on it.

### 2.8 [Medium] `±11.45 V` is a nominal-rail number and three pages size margin against it

Three pages state the op-amp's reach, and a fourth disagrees:

| Value | Source |
|---|---|
| ~±11.45 V | `[repo hardware/module/mod-channels.md, pitch-stage.md, docs/decisions/0006-cv-channel-allocation.md]` |
| about ±11.5 V | `[repo hardware/module/breath-output-stage.md]` |
| **~11.9 V** | `[repo hardware/bom.csv U-OPA-PITCH: "RRIO on +/-12V reaches ~11.9V"]` |

`[datasheet OPA2197.pdf p.8]` the part's swing from rail is 5/25 mV no-load,
95/125 mV into 10 kΩ, 430/500 mV into 2 kΩ — so the BOM's 11.9 V is the
no-load, nominal-rail, ideal-diode answer and the pages' 11.45 V is about
right at 12.00 V of bus.

**What no page does is apply the rack tolerance it applies elsewhere.**
`power-entry.md` sizes the `LT1641` `FB` divider explicitly against *"Eurorack
+12 V at −5 % is 11.4 V"*. The same −5 % on the analog rail gives:

```
[calc] bus 11.40 V, less D1 (~0.15 V at 27 mA, per 1.3), less FB1 DCR 0.08 R x 27 mA
       -> module analog rail  ~11.25 V
       less 125 mV of swing into 10 k     -> ~11.12 V at the op-amp output
       less the 1 k R-OUT-PROT into a 100 k VCO (~0.11 V) -> ~11.0 V at the jack
```

So the headroom figure everything is sized against is optimistic by **0.45 V**
at the tolerance corner the same repo uses on the next page. It does not break
anything — the mods' ±10.000 V keeps 1.0 V instead of 1.45 V, pitch's +7.5 V
reserve is untouched — but §2.4's clip point moves in, and the "1.45 V of
margin" sentence in ADR 0006 should say which rail it assumed.

---

## 3. Cable pull, mid-note — and re-plug while powered

### 3.1 [High] The breath jack does not park; it steps. Three documents still say it parks

**Node:** `R-BIAS-INAMP` (2 × 1 M), `U-DIFFRX` `REF`, `BREATH` jack.

With the cable open, `R4`/`R5` hold both in-amp inputs at module `AGND`
`[repo hardware/module/breath-receive-stage.md]`, so the differential term is
zero and the in-amp rests at its `REF`:

```
[calc] Vout(in-amp) = -G x (V_BREATH - V_AGND) + V_REF
  cable present, mouthpiece at rest:  -2.161 x 0.265 + V_REF = 0.000 V   (that is what the trimmer sets)
  cable open:                          0 + V_REF             = +0.43 V   (the trimmed null, with no pedestal to null)
  downstream is inverting, total 0.5x .. 4x:
      jack step = -0.43 x (0.5 .. 4) = -0.22 V .. -1.73 V
```

**ADR 0006 has this right**, and says so in the corrected note under its
power-on table: *"the gain-and-offset stage then puts the jack at the **OFFSET
knob's position less 0.2 to 1.7 V**, depending on where GAIN is set"* `[repo
docs/decisions/0006-cv-channel-allocation.md:206-212]`.

**Three other documents do not**, and two of them cite ADR 0006 for the
uncorrected version:

- `[repo docs/decisions/0005-power-architecture.md:368-371]` *"With the
  instrument absent the in-amp rests at its trimmed `V_REF`, and the panel
  gain-and-offset stage puts the jack at the OFFSET knob's position, **anywhere
  in ±5 V**."* — half-corrected: it names `V_REF` and then drops the gain.
- `[repo ROADMAP.md:51, milestone E10]` *"with the instrument absent the breath
  jack then sits wherever the panel OFFSET knob was left, anywhere in ±5 V
  **(ADR 0004, ADR 0006)**"* — cites the document that corrected it.
- `[repo hardware/module/breath-receive-stage.md]` *"**E10 verifies it** by
  pulling the umbilical mid-note with the mouthpiece at rest"*, in a section
  headed *"What the jack does on a `CLR` — settled: **Nothing, and that is
  correct.**"* The `CLR` claim is true and well argued. The *unplug* claim
  sitting beside it is not: an unplug is not a `CLR`, and it does move the jack.
  `ROADMAP.md` E10 repeats it as *"breath parks quietly"*.

This is the named failure mode exactly — the fix landed in ADR 0006, where the
editing was happening, and not in the roadmap step a person will actually
follow at the bench.

**And it is not only the "instrument absent" case.** The same step happens at:
instrument power-down, a load-switch latch-off, a broken `BREATH` or `AGND`
conductor (which `breath-receive-stage.md` correctly notes is now *silent* —
"no part of the system reports it"), and in reverse at every boot (§1.0 step
6). A broken conductor and a pulled cable produce the *same* jack voltage, so
the step is not a diagnostic either.

**Recommended:** one sentence, in `ROADMAP.md` E10 and in
`breath-receive-stage.md`, with the number: *the jack steps down by
`G_downstream × V_REF`, 0.2–1.7 V, and settles there.* That also makes E10 a
real measurement — the step size confirms `TRIM-BREATH-ZERO` is where it should
be.

### 3.2 [High] RJ45 has no make-first/break-last contact, and a pin-8-first withdrawal opens both grounds while +12 V is still mated

**Node:** `J-UMBILICAL` pins 3 (`+12V`), 6 (`PWR_GND`), 8 (`DIG_GND`);
`U-LVL-MOD` inputs; `U-TVS-MODULE`.

The corpus treats an unplug as instantaneous and simultaneous. It is neither.
An 8P8C plug has eight contacts in a row with **no staggered or sequenced
pin**, and it is withdrawn by hand, usually with a rock about the latch. The
two rocking directions give two orders:

```
pin-1 first:  1 BREATH, 2 AGND, 3 +12V, 4 SCLK, 5 MOSI, 6 PWR_GND, 7 CS, 8 DIG_GND
pin-8 first:  8 DIG_GND, 7 CS, 6 PWR_GND, 5 MOSI, 4 SCLK, 3 +12V, 2 AGND, 1 BREATH
```

`[repo docs/decisions/0004-cv-interface-module.md, config/figures.yaml
umbilical-pinmap]` for the assignment.

**The pin-1-first order is benign**: `+12 V` (3) breaks early, the instrument
dies with its grounds still attached, everything else follows.

**The pin-8-first order is not.** `DIG_GND` (8) and `PWR_GND` (6) both open
while `+12 V` (3) is still making — a window of a few milliseconds of hand
movement. In that window the instrument is powered with **no ground return**,
and its local ground floats up toward +12 V. The remaining conductors become
the return path:

| Path | Limited by | Verdict |
|---|---|---|
| `AGND` (2) | `R1b` 1 kΩ at the instrument + `R3` 10 kΩ at the module `[repo hardware/controller/carrier.md §2, breath-receive-stage.md]` | **Safe** — ~1 mA max. ADR 0003's no-power-current rule survives even here |
| `BREATH` (1) | `R1` 1 kΩ 1206, sized for exactly this: *"a sustained +12 V fault on the `BREATH` conductor … designed-safe"*, 139 mW `[repo hardware/module/breath-receive-stage.md]` | **Safe, by accident** — the part was sized for a *different* cause of the same condition, and `D-CLAMP-BREATH` catches the rest |
| `SCLK` (4), `MOSI` (5) | `R-SPI-SER` 100 Ω at the instrument, `R-SPI-PULL` 10 kΩ pull-downs at the module | **Not safe** — see below |

The SPI conductors run into `U-LVL-MOD`'s inputs, and
`[datasheet SN74AHCT125.pdf p.3]`:

> *"Input voltage range, `VI` … **−0.5 V to 7 V**"* — stated **without
> reference to `VCC`**, where the output row is `−0.5 V to VCC + 0.5 V`.
> *"Input clamp current, `IIK` (`VI` < 0) −20 mA"* — **negative only**.

`bom.csv` already reasons from this — *"NO INPUT CLAMP TO VCC — CONFIRMED …
That is what makes back-driving an unpowered module safe"* `[repo
hardware/bom.csv U-LVL-MOD]` — and it is right about the case it considered
(the instrument driving 3.3 V into an unpowered module). It is the **7 V
ceiling** that the ungrounded-instrument case walks into: with the instrument's
local ground floating toward +12 V, its SPI drivers present that offset plus
their own swing to a part whose input abs-max is 7 V, with no clamp to stop it
and only 100 Ω of series resistance. It is a gate-oxide overstress, not a
current one, so the 10 kΩ pull-downs do not protect it.

I am not claiming the instrument's ground reaches a full +12 V — the equilibrium
depends on how fast its 5 V rail collapses and how much its bulk holds — but
the *bound* is +12 V and the *limit* is 7 V, and nothing in the design stands
between them.

**`U-TVS-MODULE` is the part that would, and it is an open BOM row**: *"The
BOM had protection at one end only. **DELIBERATELY open, not forgotten** … Fit
at E12 if E11 gives any reason to."* `[repo hardware/bom.csv U-TVS-MODULE]`

**This is that reason**, and it arrives from ordinary use rather than from ESD.
A clamp to the buffer's own +5 V rail on the three SPI inputs at the module end
closes it for the price of the array already specced for the instrument end.

**Recommended:** (a) fit `U-TVS-MODULE`, or three BAT54-class clamps on
`U-LVL-MOD`'s inputs; (b) add one line to ADR 0004's connector section stating
that the umbilical has no sequenced contact and that break order is arbitrary,
because two other arguments in the corpus (the presence-detect deletion, and
the hot-plug sizing) implicitly assume simultaneity.

### 3.3 [Medium] Insertion bounce: the hot-plug analysis assumes the far capacitor starts at zero

**Node:** `U-LOADSW` FET, `R-ILIM`, `C-BUCK-IN` / `C-STRIP-BULK` (~2.2 mF).

`power-entry.md`'s hot-plug case is careful and, for a *cold* insertion,
correct: 17.1 ms climbing the foldback ramp, 30.4 ms at the flat 940 mA limit,
47.5 ms total against a worst-case 95.6 ms timer — 2.01× `[repo
hardware/module/power-entry.md, "What the start actually takes"]`.

It assumes `V_OUT` starts at 0 V. On a real insertion the contacts **bounce**,
and that gives a different case the page does not cover:

- The `LT1641`'s `VCC` is the module-side +12 V, behind `D2`/`FB2`/`C2`. A
  cable-side break does **not** drop it, so the part never sees the break and
  never re-arms — `V_LKO` is 7.5/8.3/8.8 V `[repo hardware/module/power-entry.md,
  quoting datasheet LT1641.pdf p.2]` and `VCC` stays at 12 V throughout.
- So after the first make, the FET is fully enhanced and `V_FB` is high, i.e.
  **foldback has already released** and the current limit is the flat 940 mA.
- On each re-make, the module side is at ~12 V and the instrument's 2.2 mF is
  at whatever it discharged to during the bounce. That is a capacitor-to-
  capacitor transfer through a fully-on FET (`R_DS(on)` ~50 mΩ assumed `[repo
  hardware/module/power-entry.md, marked as an assumption there]`), limited in
  the first microseconds only by the current-limit **amplifier's response
  time**, not by the programmed limit.

The programmed ramp does not exist for this event, because the gate is already
up. What sizes it is the `LT1641`'s loop bandwidth and the FET's SOA at a
microsecond pulse — and `power-entry.md` correctly insists the FET is chosen
*"against the single-pulse SOA curve"*, but at 10 and 100 ms, not at 1 µs.

**Recommended:** `ROADMAP.md` E6 already scopes *"Inrush with a current probe,
on switch-on **and** hot-plug"*. Add: *with a deliberately bounced insertion*
— wiggle the plug — and scope `R-ILIM`, not just the supply. That is the
measurement that sizes the FET, and it costs nothing extra once the probe is on.

### 3.4 [Medium] Re-plug: the DAC never reset, and the two representations come back 100 ms apart

Nothing at the module resets when the cable goes. `AVDD` is untouched, so no
power-on reset fires; `CLR` is pulled inactive and has no driver `[repo
hardware/module/digital-and-supervision.md]`. Therefore:

- **Across the whole unplug**, the DAC holds the codes written at the instant
  of the pull. `digital-and-supervision.md` has this: *"pull the umbilical
  mid-note and the rack holds that note until you flip the module's toggle …
  That is the everyday case, not an exotic one."*
- **On re-plug**, the module's load switch restarts (47.5 ms, §3.3), the buck
  and the ESP32 boot (100–300 ms), and the first DAC write lands **150–500 ms**
  after the plug clicks. Until then the rack is still holding the *old* note.
  Nobody states the re-plug side.
- **The two breath representations disagree for about a tenth of a second.**
  The analog jack recovers as soon as the REF5050 and the sensor are alive —
  early in the instrument's power-up, before firmware runs — while pitch and
  the four mods stay at their stale pre-unplug codes until step 8. So for
  ~100–300 ms the rack sees *live breath modulating a stale note*, which is a
  more confusing artefact than either the hold or the step on its own.

**Recommended:** E10's umbilical-pull step should re-plug and watch, not just
pull. One line in `ROADMAP.md`.

### 3.5 [Medium] The cable-side `CS` pull-up is specified to a rail the module does not have

**Node:** `R-SPI-PULL`, cable side.

Two documents specify it:

- `[repo hardware/bom.csv R-SPI-PULL]` *"**CABLE-SIDE CS PULLS TO 3V3, NOT
  +5V**: pulled to 5 V it drives 430 µA continuously through the unpowered
  ESP32's input clamp in the design's NORMAL resting state, and the node sits
  at ~0.7 V so 'CS idle high' is not even achieved."*
- `[repo docs/decisions/0004-cv-interface-module.md:390-393]` *"the cable-side
  `CS` pulls to **3V3, not +5 V**"*.

**The module has no 3.3 V rail.** Its rails are, in full: module analog +12 V,
module analog −12 V, bus +5 V (the 74AHCT125 only), and `AVDD` 5.21 V from the
LM317 `[repo hardware/module/power-entry.md, the four-rail drawing]`. A grep
for `3V3`/`3.3 V` across `hardware/module/**` returns nothing. The net has no
source, and the schematic that draws these six resistors
(`digital-and-supervision.md`) does not name a rail for any of them.

**And the stated reason does not survive its own arithmetic.** The current is
set by the ESP32's clamp, which goes to the *instrument's* dead 3V3 rail, so
the node sits at ~0.7 V regardless of what the module pulls to:

```
[calc] pulled to 5 V:   (5.0 - 0.7) / 10 k = 430 uA     (the BOM's own figure)
       pulled to 3.3 V: (3.3 - 0.7) / 10 k = 260 uA
```

The change removes 40 % of a current and **none** of the problem it names —
"CS idle high" is still not achieved, because the clamp, not the pull-up, sets
the node. See §4.5 for what that costs.

**Recommended:** decide it. The options are (a) leave it on +5 V and accept
430 µA and §4.5; (b) put a series Schottky in the `CS` line so the pull-up
cannot reach the ESP32's clamp; (c) move the cable-side pull to the
*instrument* end, where 3V3 exists — at the cost of leaving the buffer's input
undefined when the cable is out, which the DAC-side pull already covers. Any of
them is a decision; "pull to 3V3" is not buildable.

---

## 4. The two MCUs and the analog path

### 4.1 [High] The dev board's 5 V header pin is downstream of the Schottky, so ADR 0014's binding constraint does not bind

**Node:** `HDR-DEV` 5 V pin, `U-MCU-RT` `VCC_5V`, `D-USBOR`.

ADR 0014 was recently rewritten against the banked Waveshare schematic, and the
rewrite adopted a new binding constraint `[repo
docs/decisions/0014-lighting.md:385-405]`:

> *"On the dev board itself, all 64 LEDs draw through a single `B5819WS` in
> SOD-323, whose datasheet gives `I_F(AV)` 1 A but `P_D` = 200 mW and
> `RθJA` = 500 °C/W. At `V_F` ≈ 0.46 V that is **435 mA at 25 °C and 283 mA at
> a 60 °C interior** … **So the brightness cap is right and its justification
> should change.** It is not 'the matrix nearly exhausts the instrument's
> regulator'; it is 'the matrix at full field is several times what the dev
> board's own power path can pass'."*

I read the same schematic positionally rather than as a text dump, and the
topology is:

```
[datasheet WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf p.1, read by text position]

  USB VBUS --|>|-- VCC_5V --+-- 64 x WS2812B-0807  (U1..U64)
             D1             |
          B5819WS           +-- ME6217C33M5G VIN --> 3V3

  header P1 (20-way) power pin: VCC_5V
```

Evidence, all from the same page and all positional:
`B5819WS` at x = 73.9; net label `VCC_5V` at x = 50.1 (left of it) and `VBUS`
at x = 99.3 and 131.9 (right of it) — so the diode is between them, `VBUS` on
the anode side. The `ME6217C33M5G` at x = 95.1: its pin-1 (`VIN`, x ≈ 89.7)
carries net label **`VCC_5V`** at x = 45.4, and its pin-5 (`VOUT`, x ≈ 124)
carries `3V3` at x = 136.3. The header `P1`'s net list contains **`VCC_5V`**
and `GND`; `VBUS` does not appear on it.

**Consequences, and they point in opposite directions:**

1. **The B5819WS constraint is void in this build.** Feeding the carrier's
   5 V into the header pin lands on `VCC_5V`, *downstream* of `D1`. The matrix
   current never crosses that diode unless the board is powered from USB. ADR
   0014's newly adopted justification is correct for a bench board on a USB
   lead and wrong for the instrument — and it **replaced** the constraint that
   does apply. The 1 A `R-78E5.0` is the real limit after all, which is what
   the ADR says two sections earlier and then withdraws.
2. **`D-USBOR` is on the right node.** `bom.csv`'s correction — *"One per
   regulator output, not 'one per source' — the OR node is a dev-board pin"*
   `[repo hardware/bom.csv D-USBOR]` — is confirmed: the board's own `D1` is
   the USB-side OR diode, so only the buck outputs need one. Good.
3. **`C-DECOUPLE-CARRIER`'s count is unaffected**, but the *node* matters for
   §4.2.

This is the same shape as the WS2815 `V_IH` correction the corpus is proud of:
a datasheet read to settle one question, with the adjacent net left unread.

**Recommended:** ADR 0014 keeps the clamp (it is right for thermal reasons
anyway — *"~17.7 W, ~53 K"*) but restores the regulator as the electrical
constraint, and adds one line: *the carrier feeds `VCC_5V`, so the board's own
`B5819WS` carries matrix current only on USB power. E1 measures both.*

### 4.2 [High] Breath → matrix → `VCC_5V` → 3V3 → breath is a closed loop through the ADC's reference

**Node:** `VCC_5V` on the dev board; `U-ADC` `VDD`/`VREF`.

Three facts, each already in the corpus or a banked document, that nobody has
put together:

- **The MCP3202 has no `VREF` pin — `VDD` *is* the reference**, and that `VDD`
  is the dev board's 3V3 LDO `[repo hardware/controller/carrier.md §2, citing
  R10 B4]`.
- **That LDO's input is `VCC_5V`**, the same node as all 64 matrix LEDs, with
  *"no decoupling anywhere inside the array — total `VCC_5V` capacitance is
  11.1 µF"* `[repo docs/decisions/0014-lighting.md:410-414; LDO input net
  confirmed in §4.1 above from the banked schematic]`.
- **The matrix displays breath.** *"The strips and the matrix read the MCU's
  own digitised breath value"* `[repo firmware/README.md]`, with brightness
  mapped from breath through a configurable span `[repo firmware/README.md,
  "Three numbers"]`.

So:

```
breath rises -> ADC reads higher -> firmware brightens the matrix
             -> VCC_5V sags      -> 3V3 (= VREF) sags
             -> reading = Vin/VREF x 4096 rises further
```

**Positive feedback, on the instrument's primary sensor, closed through the
display.** Direction matters: because `VREF` is the *denominator*, a sag makes
the reading larger, which brightens further. It is a gain expansion at the top
of the breath range, not an offset, and it tracks exactly what the player is
doing — the direction that hides it. Loop gain is small (see below) so it is
not an oscillator, but it is a structural loop and it is not written down.

**Magnitude, honestly bounded.** The matrix current is `matrix-led-current`,
which is BLOCKED in `config/figures.yaml` and stays blocked here. What can be
said `[calc]`: a 200 mA matrix swing across the SS14 and the buck's load
regulation puts tens of millivolts on `VCC_5V`; at the ME6217's **65 dB ripple
rejection at 1 kHz** `[datasheet ME6217C33M5G.pdf p.1]` that is sub-millivolt
on `VREF`, i.e. well under an LSB. So the loop is weak — **but it is the
argument `C-ADC-BULK` exists to make, and `C-ADC-BULK` is justified against the
wrong aggressor**:

> *"The repo's own `C-STRIP-BULK` note puts the WS2815 PWM rate at ~2 kHz,
> which is exactly Nyquist for a 4 kHz sampler. 10 µF plus the existing
> 100 nF, treating that pin as an analog reference rather than a logic
> supply."* `[repo hardware/controller/carrier.md §2, C-ADC-BULK]`

The WS2815 strips are on the **+12 V** rail `[repo
docs/decisions/0005-power-architecture.md, power tree]`, two conversions away
from the ADC's reference. The **matrix** is on the same node as the LDO's input,
one component away, driven from the same signal being measured, and has no
decoupling of its own. The proposal is right; its stated reason names the
weaker of the two aggressors and not the one that closes a loop.

**Recommended:** adopt `C-ADC-BULK`, restate the reason, and make E2's
breath-noise measurement a *matrix-on / matrix-off* pair. If the standard
deviation moves, the deadband firmware sizes from it moves too
`[repo firmware/README.md, "Deadband"]`.

### 4.3 [Medium] The ADC reference's load regulation: the datasheet's max is worse, and the biggest aggressor is not costed at all

`carrier.md` costs the key pull-ups against the reference twice, in §2 and §3,
with the same figure:

> *"25.8 mA moves the reference **0.077 %, about 3.2 LSB** … at a load
> regulation of ~0.3 % per 100 mA `[from memory]`"*

The part is banked. `[datasheet ME6217C33M5G.pdf]`:

> *"Load Regulation ΔVOUT, 1 mA ≤ IOUT ≤ 300 mA — **10 typ / 50 max** mV"*
> *"Line Regulation 0.05 % (TYP.)"*, *"High Ripple Rejection: 65 dB @ 1 kHz"*

```
[calc] pro-rating the datasheet window over the 25.8 mA step (299 mA span):
   typ: 10 mV x 25.8/299 = 0.86 mV on 3.3 V = 0.026 %  = 1.1 LSB
   max: 50 mV x 25.8/299 = 4.3  mV on 3.3 V = 0.13  %  = 5.3 LSB
   carrier.md's [from memory] figure:        0.077 %   = 3.2 LSB
```

So the repo's number sits between typ and max — a reasonable guess, and the
**max is 1.7× worse** than what was accepted. Not alarming; worth replacing a
`[from memory]` with a citation, which `CLAUDE.md` §3 asks for.

**The larger omission is on the same rail.** The ESP32-S3 itself runs from this
LDO, and ADR 0005's own load table gives it as **40–80 mA**
`[repo docs/decisions/0005-power-architecture.md:31]`. A 40 mA activity swing
is **1.55× the whole key-pull-up step**, so by the same arithmetic it is
1.7 LSB typ / 8.2 LSB max — and it is correlated with what firmware is doing,
not with anything the player can see. `carrier.md` costs the 25.8 mA of key
pull-ups to two decimal places and does not mention the processor sharing the
rail.

**Recommended:** add the MCU's own draw to the same paragraph, cite the
datasheet's numbers, and note that the whole class of error is removed by
either of the fixes the page already lists ("a separate rail for the pull-ups
or a real reference for the ADC") — which now have a third beneficiary.

### 4.4 [Medium] ADR 0014 still budgets one buck

`[repo docs/decisions/0014-lighting.md:434-437]`: *"It is also **more than the
instrument's 5 V regulator can supply.** The matrix shares the 1 A R-78E5.0
with **both dev boards**, which take roughly 330–400 mA between them, so a
full-field matrix would ask for about 1.36 A from a 1 A part."*

There are two bucks, and the display board is on the other one
`[repo docs/decisions/0005-power-architecture.md, "Two bucks, not one";
hardware/controller/carrier.md §1: "Buck A (real-time board + matrix +
74AHCT125)"]`. The correct load on buck A is the real-time board + matrix +
level shifter — *"~680–780 mA … 68–78 %"* per `carrier.md`'s own arithmetic.

The conclusion (the matrix must be clamped) survives; the number that supports
it is from the superseded one-buck topology. Same class as §4.1: the argument
is right and its premise is stale.

### 4.5 [Medium] In the design's normal resting state, the DAC's `SYNC` is held asserted

**Node:** `R-SPI-PULL` cable side, `U-LVL-MOD` input, `U-DAC` `SYNC`.

`bom.csv` states the condition itself, as an aside `[repo hardware/bom.csv
R-SPI-PULL]`: *"the node sits at ~0.7 V so 'CS idle high' is not even
achieved"*, in *"the design's NORMAL resting state"* — module powered,
instrument off or absent, cable connected.

`[datasheet SN74AHCT125.pdf p.4]` `V_IL` max is **0.8 V** (TTL, not ratioed to
VCC). 0.7 V is below it. `OE` is tied low and permanently enabled `[repo
hardware/module/digital-and-supervision.md, bom.csv U-LVL-MOD]`. Therefore the
buffer drives `SYNC` **low** — asserted — at the DAC, continuously, whenever
the instrument is off with the cable in.

`[datasheet DAC8568CIPW.pdf p.6]`: *"When `SYNC` goes low, it enables the input
shift register, and data are sampled on subsequent falling clock edges."*

So the part sits with its shift register enabled indefinitely, and `SCLK` is
held low only by a 10 kΩ pull-down at the end of two metres of cable. Thirty-two
noise edges — cumulative, over hours — compose a word. `bom.csv`'s own
rationale for buying these six resistors is *"a stray `CS` edge latches garbage
into the pitch DAC"*, and `digital-and-supervision.md` builds the whole
`CS`-pairing argument on `CS` being the pin that must not glitch.

The good news: the DAC-side pull-up **is** on `AVDD` and does hold `SYNC` high
— but only while the buffer's outputs are Hi-Z, and `OE` is tied enabled, so
they never are. The two halves of the six-resistor scheme were designed for
different `OE` policies and only one survived.

**Recommended:** this is the same decision as §3.5. Whatever fixes the pull-up
rail also fixes this; if nothing does, at minimum record that `SYNC` idles
asserted, so the next reviewer does not assume otherwise from the schematic.

### 4.6 [Medium] There is no SPI-to-`BREATH` crosstalk figure anywhere

The corpus computes umbilical crosstalk twice, both times with a **digital**
victim: intra-pair, *"365–907 mV of saturated intra-pair crosstalk against
`CS`'s 678 mV `V_IL` margin"*, and pair-to-pair, *"25–60× smaller"*
`[repo hardware/module/digital-and-supervision.md:86-94,
docs/decisions/0004-cv-interface-module.md:824-876]`. The pin-map swap that
followed is right and I am not reopening it.

**The analog victim is never evaluated.** `BREATH`/`AGND` on pair (1,2) shares
the sheath with `SCLK`/`MOSI` on (4,5) and `CS`/`DIG_GND` on (7,8), at 2 MHz
with 2–5 ns edges `[repo hardware/controller/carrier.md §4]`, for two metres,
and the receiver is an in-amp with 60–73 dB of link CMRR
`[repo hardware/controller/carrier.md §2, "70.2 dB … 60.2 dB … the real floor
is 73 dB"]`.

The design is probably fine, and the reasons are all in the corpus — which is
why the absence of the number is the finding rather than a hazard:

- `C_diff` 15 nF ahead of the in-amp gives a 482 Hz differential pole, so
  `[calc]` `20·log10(2 MHz / 482 Hz)` = **72 dB** of single-pole attenuation at
  the SPI fundamental, before the in-amp.
- The filter is deliberately **ahead** of the in-amp *"because that is the only
  place it can stop RF rectification"* `[repo
  hardware/module/breath-receive-stage.md]` — the one mechanism a downstream
  filter cannot fix.
- `CABLE-UMB` is *"Cat5e **STP** … Shielded preferred"* `[repo hardware/bom.csv
  CABLE-UMB]`, though the shield-bonding policy is *"sixteen words in the whole
  repo"* by `power-entry.md`'s own account.

**Recommended:** E11 measures it — scope the breath jack with SPI running and
the mouthpiece at rest, at both gain extremes. That is a five-minute
measurement that converts three qualitative arguments into a number, and it is
not in `ROADMAP.md`'s measurement table.

### 4.7 [Low–Medium] The `CS` framing risk has a mitigation the part publishes

`digital-and-supervision.md` builds its strongest digital argument on `CS`
re-framing:

> *"A glitch restarts the bit count mid-message, so every bit lands in the
> wrong field … It is the only failure in the digital path that does not
> self-heal on the next update."*

`[datasheet DAC8568CIPW.pdf p.6, SYNC pin description]` gives a specific and
favourable behaviour the page does not record:

> *"**If `SYNC` is taken high before the 31st clock edge, the rising edge of
> `SYNC` acts as an interrupt, and the write sequence is ignored** by the
> DAC7568/DAC8168/DAC8568."*

So a glitch that takes `SYNC` high mid-word and *stays* high until the end of
the burst is **safe** — the word is discarded and the 250 µs refresh rewrites
it. The genuinely dangerous glitch is narrower: one that both rises **and**
falls inside a frame, so that a new 32-bit count starts mid-word and composes
garbage from two halves.

The conclusion — pair `CS` with `DIG_GND`, and never with another aggressor —
is unchanged and correct. What changes is that the corpus's "does not
self-heal" is true of a sub-case rather than of all `CS` glitches, and the
part's own interrupt mechanism is an argument in the design's favour that
nobody has banked.

---

## 5. What one page assumes another provides

### 5.1 Quantities stated in more than one place, and whether they agree

| Quantity | Values found | Verdict |
|---|---|---|
| Sensor pedestal / full scale | 0.2 / 4.80 V `[figures.yaml, ADR 0003]`; 0.2 / 4.7 V `[carrier.md §2, ADR 0005:74]`; **0.265 / 4.864 V** `[datasheet MPXV4006DP.pdf p.3]` | **§2.1 — the register is wrong against a banked document** |
| Hard blow at the in-amp | −4.69 V, 4.64 V `[breath-output-stage.md, two sections]`; "about −4.7 V" `[breath-receive-stage.md]` | **§2.5 — two gains in circulation on one page** |
| OFFSET knob at centre | +0.07 V `[breath-output-stage.md table]`; +0.605 V `[same file, §4]` | **§2.3 — the page states both** |
| Module +12 V / −12 V draw | 45/40 mA `[ADR 0004:265]`; 22/10 mA `[bom.csv C-BULK-RAIL]`; 27/13 mA `[calc, §1.2]` | **§1.3 — three splits, one capacitor value depends on it** |
| Entry bulk | 4 × 47 µF `[power-entry.md drawing and :513]`; 100 µF (+12) / 47 µF (others) `[bom.csv C-BULK-RAIL]` | **§1.2 — the schematic has the defect the BOM was edited to remove** |
| Op-amp output reach | ±11.45 V `[3 files]`; ±11.5 V `[breath-output-stage.md]`; ~11.9 V `[bom.csv]`; ~11.0 V at −5 % rack `[calc, §2.8]` | **§2.8 — a nominal-rail figure used as a worst case** |
| Module op-amp halves | 10 of 12, 2 spare `[breath-output-stage.md, bom.csv U-OPA-PITCH]`; shaper takes "both remaining" `[breath-output-stage.md §4]`; plus `U-RESP` = a 7th package `[bom.csv]` | **§5.2** |
| `C-DECOUPLE` quantity | 19, counting "DAC8568 AVDD+DVDD = 2" `[bom.csv]` | **§5.3 — the part has one supply pin** |
| Cable-side `CS` pull rail | 3V3 `[bom.csv, ADR 0004:391]`; module has no 3V3 `[power-entry.md]` | **§3.5** |
| `R-SPI-PULL` placement | "three at each end" `[ADR 0004:390]`; "BOTH SIDES of the 74AHCT125" — i.e. both at the module `[bom.csv, digital-and-supervision.md]` | Minor; ADR 0004's phrasing reads as one set per *end of the cable*, which is not what is built |
| `R-FB` (breath summer) | 40 k `[breath-output-stage.md drawing]`; 40.2 kΩ `[same file, Values; bom.csv R-BREATH-SUM]` | Minor; the drawing's 40 k is what the offset table was computed with (§2.3) |
| In-amp `REF` | "a buffered trimmer … from the LM317 5.21 V" `[breath-receive-stage.md]`; **"grounded"** `[firmware/README.md]` | **§5.4** |
| Breath jack, instrument absent | "OFFSET less 0.2 to 1.7 V" `[ADR 0006]`; "anywhere in ±5 V" `[ADR 0005:368, ROADMAP.md:51]` | **§3.1** |
| Pitch at power-on | "below −2 V, subsonic" `[ADR 0006 table]`; "0 V, a VCO's base note" `[pitch-stage.md, and ADR 0006's own next paragraph]` | **§1.4** |

### 5.2 [Medium] The module's op-amp half budget is stated three ways

`bom.csv`'s `U-OPA-PITCH` row is the clearest statement: *"Six packages, twelve
halves, TEN used: pitch, mod 1-4, mod offset follower, VREFOUT follower, breath
REF-zero buffer, breath gain buffer, breath summer. TWO SPARE."* I recounted
against the five module schematic pages and it is **exactly right** — ten.

Then:

- `breath-output-stage.md` §4 spends both spares on the response shaper: *"Both
  remaining OPA2197 halves — one shapes at ÷2 inverting, one restores ×2
  inverting."* That makes it twelve of twelve, zero spare.
- The same section then says the `POT-OFFSET` buffering fix *"wants a half, and
  this stage takes the last two"* — i.e. it knows it is over budget.
- `bom.csv` adds **`U-RESP`, `OPA2197IDR`, qty 1** as a separate package, whose
  note says the shaper consumes the two spares *"so the separate A5 finding …
  needs this additional package"*.

So `U-RESP` is a seventh package, and which halves live in which package is
unstated — the shaper's two, or the shaper's two *and* an offset buffer split
across two packages. That matters for layout (the shaper is a signal path; the
offset buffer is a panel-pot buffer) and for §5.3's decoupling count.

**Recommended:** one sentence on `breath-output-stage.md` allocating the
fourteen halves explicitly, the way `bom.csv` allocates the twelve. Also
`breath-receive-stage.md` still says *"It costs the last spare OPA2197 half,
and `U-OPA-PITCH` goes to six packages so there is still one"* — written before
the shaper existed, and now the third count in circulation.

### 5.3 [Medium] `C-DECOUPLE` counts a supply pin the DAC does not have

`[repo hardware/bom.csv C-DECOUPLE]`: *"One per supply pin … 6 × OPA2197 on
±12 V = 12, INA828 = 2, **DAC8568 AVDD+DVDD = 2**, 74AHCT125, LT1641 VCC,
LM317 in"* → 19.

`[datasheet DAC8568CIPW.pdf p.6, Pin Descriptions, TSSOP-16]` the sixteen pins
are `LDAC, SYNC, AVDD, VOUTA, VOUTC, VOUTE, VOUTG, VREFIN/VREFOUT, CLR, VOUTH,
VOUTF, VOUTD, VOUTB, GND, DIN, SCLK`. **There is one supply pin (`AVDD`,
pin 3) and one ground (pin 14). There is no `DVDD`.**

```
[calc] correct count today:            12 + 1 + 1 + 1 + 1 + 1 = 18
       with U-RESP's 7th package:      18 + 2                 = 20
```

The row is off by one in one direction and two in the other, and they nearly
cancel — which is why nobody has noticed. Note the row has already been
corrected twice (22 → 21 → 19) for deleted parts; the phantom `DVDD` survived
both passes.

### 5.4 [Medium] `firmware/README.md` says the in-amp's `REF` is grounded

`[repo firmware/README.md]`:

> *"**Breath is outside all of this.** It never passes through the DAC, and
> since the in-amp's `REF` pin is **grounded** rather than driven by a firmware
> zero (ADR 0003), no DAC register touches the breath jack at all."*

`breath-receive-stage.md` declines grounding it, by name, in a section headed
*"Why `REF` is trimmed rather than grounded"*: *"**Grounding it makes the panel
knobs interact** … trim the jack to zero at unity gain, turn GAIN to 2.4×, and
the jack idles around +0.6 V — into a VCA."*

The page even records that it caught this in its own text — *"And it said 'now
that `REF` is grounded', which is the option this page **declines** forty lines
above, by name"* — and fixed its own copy. `firmware/README.md`'s copy was not
fixed, and `ROADMAP.md` E10 was (it says *"`REF` trimmed, not grounded"*), so
two of three landed.

The paragraph's **conclusion** is unaffected — breath never passes through the
DAC either way — which is exactly why it will survive another wave unless
someone is looking for it.

### 5.5 [Medium] `power-entry.md`'s drawing labels the load switch's supply node `PWR_GND`

**Node:** `D2` / `FB2` / `C2` output.

```
  +12V ├───┬──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V
       │   └──[D2 1N5817]──[FB2]──[C2 47µF]──┬──────── PWR_GND (star)
```

`[repo hardware/module/power-entry.md:15-22]`

The `D2` branch is the **umbilical +12 V feed**, and everything else on the
page says so: *"the instrument's current flowed through the same diode as the
module's analog rail"*; `FB-IN` is *"One per branch: +12 V analog, **+12 V
umbilical**, −12 V, +5 V"* `[repo hardware/bom.csv FB-IN]`; and
`config/figures.yaml`'s `ferrite-bias-impedance` gives *"~580–614 ohm on
FB1/FB3/FB4; **~280–310 ohm on FB2**"* — a lower impedance precisely because
`FB2` carries the 360 mA DC bias, which it could not do in a ground return that
the same drawing routes elsewhere.

Read literally, the drawing ties the `LT1641`'s `VCC`/`SENSE`/`R-ILIM` node to
ground. It is the one page in the corpus whose job is to be built from, and
`CLAUDE.md`'s own principle applies: *"prose is what a layout gets built from"*
— so is a drawing.

**Recommended:** relabel that node `UMBILICAL +12V (pre-switch) → LT1641 VCC`
and put `PWR_GND (star)` on the actual star, which the page's Grounding
section describes correctly in words.

### 5.6 [Medium] The `AVDD` rail's load list omits two panel-facing loads, and one of them is called "buffered" with no buffer

`power-entry.md` draws the LM317 feeding one thing: *"DAC AVDD 5.21 V"*, with a
1 µF cap. `bom.csv` agrees: *"~13 mA load incl. the divider"*.

Two other pages hang loads on that rail:

- `[repo hardware/module/breath-receive-stage.md]` `TRIM-BREATH-ZERO` is *"from
  the LM317 5.21 V"*, through a divider into the `REF` buffer.
- `[repo hardware/module/breath-output-stage.md]` the drawing reads *"buffered
  +5.21 V ──[POT-OFFSET 10k]"*, and the Values table calls it *"±5 V, zero at
  centre"* off that rail.

```
[calc] POT-OFFSET 10 k across 5.21 V           = 0.52 mA, constant
       R-OFF leg, Vw/21.0 k, 0 .. 5.21 V       = 0 .. 0.25 mA, varies with the knob
       TRIM-BREATH-ZERO divider                = unspecified, R-TRIM-RANGE is an open BOM row
```

Neither is large. Two things follow anyway:

1. **The word "buffered" names an op-amp half that does not exist.** §5.2's
   allocation has no half for buffering the 5.21 V rail. Either the drawing
   means "the LM317 rail, which is already low-impedance" — in which case the
   word should go, because it reads as a part — or there is an eleventh half and
   the count is wrong again.
2. **The panel OFFSET knob is a variable load on the DAC's analog supply.** It
   does not move pitch (full scale is set by the internal reference, not `AVDD`
   — ADR 0005 makes that argument at length), but it *does* move
   `TRIM-BREATH-ZERO`'s reference, which is on the same rail, so the breath
   zero and the breath offset are weakly coupled through the regulator. That
   is the exact class of knob interaction the `REF` trimmer was added to
   remove, relocated one more time.

The rail's owning page should list its loads. It currently lists one of three.

### 5.7 [Medium] The back-powering arithmetic does not hold for pitch any more

`[repo hardware/bom.csv D-JACK-CLAMP]`: *"**BACK-POWERING**: clamped at the
JACK, a neighbouring module driving 10 V through its own 220 R output pushes
42 mA per jack into our +12 V rail when this module is off — 254 mA across six
jacks … **Behind the 1 k it is 7.6 mA per jack.**"*

That is correct for breath and the four mods, whose feedback comes from the
op-amp output so `R-OUT-PROT` is genuinely in the way. **Pitch is now
different**: `pitch-stage.md` moved its DC feedback tap to the jack, so `R2`
(10 kΩ) + `TRIM-GAIN` run **from the jack back to the LT5400 and the op-amp's
(−) input**, in parallel with `R-OUT-PROT`.

```
[calc] external +10 V at the PITCH jack, module off:
  through R-OUT-PROT 1 k, clamped on the driver side   -> 7.6 mA     (the BOM's figure)
  through R2 + TRIM-GAIN ~10.2 k, straight to the LT5400 and the op-amp (-) input,
     bypassing R-OUT-PROT and its clamp entirely       -> ~1 mA, unprotected
```

1 mA into an op-amp input clamp is survivable. The part that is not
comfortable is the LT5400: `[repo hardware/bom.csv R-PRECISION, quoting the
banked 5400fa]` *"the LT5400 has **no internal ESD diodes, only ±1 kV HBM**
(p.6), with Figure 1's named remedy being a BAV99"*. The network is now
DC-connected to an external 3.5 mm jack through 10 kΩ, which is the datasheet's
"external connector" case.

`pitch-stage.md` flags the layout half of this — *"check the clamp actually
stands between the jack and every LT5400 pin when this is laid out"* — and that
is the right instruction. What is missing is that **`bom.csv`'s protection
arithmetic was not re-derived when the tap moved**, so the BOM currently claims
a 7.6 mA bound for a node that has an unprotected parallel path.

### 5.8 [Low] Other cross-page items worth a line

- **`latency-budget.md` does not know about the response shaper.** Two more
  op-amp stages in the analog breath path; the delay is negligible `[calc:
  OPA2197 GBW 10 MHz at G=2, well under a microsecond]`, so the budget does not
  move — but the table claims to be the whole path and the stage exists.
- **`carrier.md`'s 282 µs anti-alias τ is still unapplied**, by its own
  admission: *"`latency-budget.md` and ADR 0003 book 'SAR ADC conversion
  ~50–200 µs' and no RC term at all … Found by `R10` §B-2 and still
  unapplied."* `latency-budget.md` **has** since added the 282 µs row. The
  carrier's note is now the stale copy of a fix that landed.
- **`C-DECOUPLE-CARRIER` qty 7** covers *"MCP3202, REF5050 in, OPA2197 +12V,
  74AHCT125, MPXV4006DP, and both R-78E5 inputs"* = 7 `[repo hardware/bom.csv]`.
  The OPA2197 on the carrier runs from **+12 V only** (single supply,
  `[repo hardware/controller/carrier.md §1: "OPA2197 V+"]`), so one cap is
  right — worth noting only because the module counts two per package and the
  two rows look inconsistent side by side. They are not.

---

## 6. What I could not settle

- **Rack PSU rail sequencing** (§1.1). Which of bus +5 V and bus +12 V rises
  first is a property of the target supply. The finding stands either way
  because nothing in the module constrains it, but the *severity* depends on
  the answer. Measurable at E6 in five minutes with two probes.
- **`matrix-led-current`** stays BLOCKED, as `config/figures.yaml` says. §4.2's
  loop gain cannot be bounded tightly without it; E1 measures it.
- **`breath-working-point`** stays DISPUTED. §2.4's clip margin (4.5 kPa
  against a hard blow) is 1.6× on the 2.8 kPa figure and only 1.1–1.5× on the
  3–4 kPa candidates, so the shaper's headroom is more or less comfortable
  depending on which is true. That makes M1's manometer measurement a
  prerequisite for sizing `R-RESP`, not just for the gain range.
- **The instrument's ground potential during a pin-8-first withdrawal**
  (§3.2). I bounded it (+12 V) and bounded the part (7 V) but did not model the
  equilibrium; it depends on how fast the buck's 100 µF collapses. The fix —
  fit `U-TVS-MODULE` — does not depend on the model.
- **Whether `POT-OFFSET`'s wiper is buffered** (§2.3). Three states of that
  decision exist across two files and I could not tell which is current from
  the documents. It is an author's call, not a reviewer's.

## 7. If only five things are fixed

1. **§1.1** — move `U-LVL-MOD` off bus +5 V, or put 1 kΩ in each of its three
   output lines. It is a datasheet-forbidden condition on the one part in the
   module that cannot be replaced without desoldering a TSSOP.
2. **§2.1** — correct `sensor-full-scale` to 0.265 / 4.864 V and strengthen its
   `forbidden` patterns so the checker catches the bare-number forms (§2.2).
   It is a tracked figure that is wrong against a banked document.
3. **§1.5 + §1.6** — one paragraph in `firmware/README.md`: use command `0011`
   or `0010`, never `0000`; use `0010` on the sixth word to make the six-channel
   update atomic. Fixes a dead-board trap and deletes an accepted cost.
4. **§2.3** — settle whether `POT-OFFSET`'s wiper is buffered, and make the
   offset table match. "Zero at centre" is a commissioning instruction in two
   documents and it is currently 0.6 V out.
5. **§3.1** — one sentence in `ROADMAP.md` E10 and in `breath-receive-stage.md`
   saying that the breath jack *steps* on an unplug, with the number. The
   bench step as written tells the operator to expect the wrong thing.

---

*A13, cold, 2026-09-21. Every numbered finding carries its provenance inline.
Findings are claims; `CLAUDE.md` asks that they be verified before being
repeated, and that the verification be recorded.*
