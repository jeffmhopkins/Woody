# N4 — pin identity

**Slice:** N4, pin identity. Every component in all 22 `netlist.yaml` files whose
part has a banked datasheet, checked pin by pin against that document: does the
pin exist, is it the datasheet's own name, does it mean what the netlist assumes,
is an active-low pin at the right level, is anything tied where the datasheet
forbids, and is any pin the device *has* simply absent.

**Revision measured:** `d1f0cb7`. Working tree is at `5c39a4e`; `git diff --stat
d1f0cb7..HEAD -- . ':!docs/review'` is **empty**, so the corpus I read is
byte-identical to `d1f0cb7` `[test]`. `tools/` not modified.

**Cold:** nothing under `docs/review/` was read.

**Extraction method.** `pymupdf` text layer, plus — where the pinout is a
graphic — word-coordinate clustering (same y = same wire) and, once, a 12×
render read as an image. Where neither worked I say so rather than filling the
gap from memory.

---

## The one-line answer to the two commissioned questions

1. **The DAC's channel→letter map is right in the only sense available, and
   nothing settles it — but the map is not where the risk is.** The datasheet
   never numbers a channel at all; its only numeric handle is the 4-bit
   *address*, which is **0-based** (`0000` = DAC Channel A). A 1..8 numbering
   therefore cannot be the datasheet's numbering, which makes the ordinal map
   the only consistent reading — and leaves the *address* map, which decides
   whether firmware rotates every output by one pin, stated nowhere. **N4-5.**

2. **The quad buffer's gate assignment is free and harmless — but the letters
   it is written in do not exist on the device, and the two `74AHCT125`
   netlists use them incompatibly.** The bigger finding beside it: all four
   `OE` pins are tied to GND on both parts, which is the *opposite* of what
   SCLS264O recommends, and neither note says so. **N4-6.**

And the finding neither question asked for, which is larger than both: **the
same "which section?" defect the author flagged on the quad buffer is
unflagged, and live, on eleven OPA2197 halves and on the LT5400.** **N4-2**,
**N4-4.**

## Why the checker is silent on all of this

`tools/check-netlist.py` builds `declared_pins` from the netlist's own `pins:`
list (`tools/check-netlist.py:406`) and then only proves each member is used
exactly once (`:425-433`). There is no device model anywhere in `tools/`, so a
pin the silicon does not have passes, and a pin the silicon has that the
netlist omits is invisible. Baseline `[test]`:

```
$ python3 tools/check-netlist.py --strict
netlist: 22 circuit(s), 197 components, 254 nets, 55 master net(s) | 0 problem(s) | ...
instances: 102 row(s) placed exactly to BOM qty, 4 counted by section, 7 short: ...
EXIT=0
```

Zero problems, on a corpus containing every item below.

---

# Findings

## N4-1 — `U-MCU-RT.IO43`, `U-MCU-RT.IO44` (and `.P3V3`, `.P5V`): pins the board does not have under those names

**Severity: medium.** Four of the eighteen pins declared on `U-MCU-RT` name
nothing in the banked schematic.

`hardware/carrier/netlist.yaml:64` declares
`pins: [IO1, IO2, IO5, IO6, IO7, IO33..IO40, IO43, IO44, P3V3, P5V, GND]`
`[repo hardware/carrier/netlist.yaml]`.

The banked `datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf` has
exactly one 20-way header, `P1`. Read by coordinate (pad number at x≈801, net
label at x≈763, matched by y) `[datasheet WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf p.1]`:

| P1 | net | P1 | net |
|---|---|---|---|
| 1 | `VCC_5V` | 11 | `RX` |
| 2 | `GND` | 12 | `TX` |
| 3 | `3V3` | 13 | `IO40` |
| 4 | `IO7` | 14 | `IO39` |
| 5 | `IO6` | 15 | `IO38` |
| 6 | `IO5` | 16 | `IO37` |
| 7 | `IO4` | 17 | `IO36` |
| 8 | `IO3` | 18 | `IO35` |
| 9 | `IO2` | 19 | `IO34` |
| 10 | `IO1` | 20 | `IO33` |

- `grep -oE "\bIO[0-9]+\b"` over the whole banked schematic returns
  `IO0 IO1 IO2 IO3 IO4 IO5 IO6 IO7 IO8 IO9 IO10 IO11 IO12 IO13 IO14 IO15 IO16
  IO17 IO18 IO21 IO33 IO34 IO35 IO36 IO37 IO38 IO39 IO40 IO41 IO42 IO45 IO47
  IO48` — **no `IO43`, no `IO44`** `[test]`.
- The chip-side pins are named `U0TXD` and `U0RXD` (U66, `ESP32-S3FH4R2`), and
  they carry nets `TX` and `RX` respectively — same y, x 461/476/481/499
  `[datasheet WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf p.1]`.
- `grep -c "P3V3\|P5V"` over the schematic returns **0** `[test]`. The board's
  names are `3V3` and `VCC_5V`.

The irony is that `carrier/netlist.yaml`'s own **port** names are `U0TXD` and
`U0RXD` — the datasheet's names — and only the `pins:` list reaches for the
invented ones. The nets are `U0TXD: [port, U-MCU-RT.IO43]` and
`U0RXD: [port, U-MCU-RT.IO44]` `[repo hardware/carrier/netlist.yaml:181-188]`.

**That `IO43` = `U0TXD` and `IO44` = `U0RXD` on an ESP32-S3 is `[from memory]`
and I could not prove it from any banked document** — the schematic gives chip
*package* pin numbers (49, 50), not GPIO numbers. So the netlist's pin names are
simultaneously unprovable here and inconsistent with the one document the repo
banks for this board.

**Wrong if:** a vendor pinout document not in `datasheets/` silkscreens those
two pads `IO43`/`IO44`. The board photo/silkscreen is not banked, so I cannot
exclude it — but the banked schematic is what the repo has, and it says `TX`/`RX`.

**Smallest fix:** in `hardware/carrier/netlist.yaml:64`, rename the two pins to
`U0TXD`/`U0RXD` (matching the ports already there and the chip pin names) or to
`TX`/`RX` (matching P1's labels), and rename `P3V3`/`P5V` to `3V3`/`VCC_5V`.
Pure rename; the nets already exist.

---

## N4-2 — `U-OPA-PITCH`: `section: A` is claimed by three circuits and `section: B` by two, on a six-package row

**Severity: high.** This is exactly the defect the author flagged on the quad
buffer ("*which signal gets which gate is assigned here and nowhere else*"),
and here it is neither flagged nor resolvable.

`U-OPA-PITCH` is one BOM row, **qty 6**, `OPA2197`, SOIC-8 — "*Six packages,
twelve*…" halves `[repo hardware/bom.csv]`. Eleven netlist components declare
`of: U-OPA-PITCH` `[test]`:

| file | refdes | `section:` |
|---|---|---|
| `module/pitch-stage/netlist.yaml` | `U-PITCH-REFBUF` | **A** |
| `module/pitch-stage/netlist.yaml` | `U-PITCH-AMP` | **B** |
| `module/breath-output-stage/netlist.yaml` | `U-BREATH-BUF` | **A** |
| `module/breath-output-stage/netlist.yaml` | `U-BREATH-SUM` | **B** |
| `module/breath-receive-stage/netlist.yaml` | `U-REF-BUF` | **A** |
| `module/mod-channels/netlist.yaml` | `U-MOD-REFBUF` | `half` |
| `module/mod-channels/netlist.yaml` | `U-MOD-1` … `U-MOD-4` | `half` ×4 |

`A` three times, `B` twice, and no package instance is ever named. `section: A`
of a six-package aggregate row identifies no pin. And `section: half` is not a
section at all — the OPA2197 has exactly two, named `A` and `B`
`[datasheet analog/OPA2197.pdf p.3-4]`:

> `+IN A` 3, `–IN A` 2, `OUT A` 1, `+IN B` 5, `–IN B` 6, `OUT B` 7, `V+` 8, `V–` 4

So the letter is load-bearing: it *is* the pin number. As written, **not one of
the eleven op-amp halves in the module resolves to a pin.**

The checker cannot see it: `section` is read only for BOM instance counting
(`tools/check-netlist.py:218, 392-399`), never for collision, and the pins
`IN+`/`IN-`/`OUT` hang off eleven *different* refdes, so "used exactly once"
is satisfied eleven times over.

`carrier/breath-excitation-reference` is the counter-example that proves the
shape: `U-REFBUF` = `A`, `U-BREATHBUF` = `B`, both `of: U-BUF`, and `U-BUF` is
**qty 1** — so there the letters do resolve.

**Wrong if:** `section:` is defined somewhere as meaning "one half of some
package, which one is a layout decision" rather than "channel A of the
OPA2197". `hardware/README.md` does not define `section:` at all, and the
DAC/quad-buffer netlists treat an unstated assignment as something a netlist
must assert, so I do not think that reading is available.

**Smallest fix:** give the six packages instance refdes
(`U-OPA-PITCH-1` … `-6`) and change each op-amp's `of:` to name one, keeping
`section: A|B`. Twelve halves, eleven used, one spare — and the spare becomes
visible, which it currently is not.

---

## N4-3 — `U-OPA-PITCH` pin 8 (`V+`) and pin 4 (`V–`): supply pins that appear in no net anywhere

**Severity: medium.**

`grep` for `.V+`/`.V-`/`.VCC`/`.VEE` on every OPA2197 component across all 22
netlists returns **nothing** `[test]`. The convention instead is a `rails:` key
naming supply *nets*, which `tools/check-netlist.py:436-443` consumes to mark a
port implicitly received — and the tool's own comment says the trade was
deliberate. Fine as far as it goes. Two things it does not reach:

- **`U-REF-BUF` in `module/breath-receive-stage` has no `rails:` key at all**
  `[repo hardware/module/breath-receive-stage/netlist.yaml:107-112]`. It is the
  only one of the thirteen OPA2197 sections in the corpus with no supply
  declaration in any form `[test]`. It is masked because `U-DIFFRX.V+`/`.V-` in
  the same file already satisfy `MODULE_ANALOG_POS12/NEG12`, so no port looks
  unsatisfied and the checker stays quiet.
- **`U-REFBUF` and `U-BREATHBUF` declare `rails: [UMBILICAL_POS12]` — one rail
  for a two-rail part.** The note beside them says "*Single supply from +12 V,
  **V- on the analog star***"
  `[repo hardware/carrier/breath-excitation-reference/netlist.yaml:61-62]`, so
  the negative-rail connection exists as prose and as no declaration. `V–`
  (pin 4) of that package is netted nowhere and railed nowhere.

**Wrong if:** `rails:` is understood to list only rails that are *ports of this
circuit*, with ground implied. That reading does not save `U-REF-BUF`, which
lists none.

**Smallest fix:** add `rails: [MODULE_ANALOG_POS12, MODULE_ANALOG_NEG12]` to
`U-REF-BUF`, and add the ground net to the two carrier buffers' `rails:` lists.

---

## N4-4 — `R-PRECISION` (LT5400): four pins and the exposed pad are in no net; the sections are named A/B and the device names them R1–R4

**Severity: medium-high.**

`hardware/module/pitch-stage/netlist.yaml:36-49` models the LT5400 as two
two-pin resistors:

```
R1:  {of: R-PRECISION, section: A, value: "10k", pins: [1, 2]}
R2:  {of: R-PRECISION, section: B, value: "10k", pins: [1, 2]}
```

The BOM row is `LT5400 1:1 quad (four equal 10k), MSOP-8 option`, qty 1,
"*Two of four sections used*" `[repo hardware/bom.csv]`. The banked
`datasheets/analog/LT5400.pdf` (5400fa) Pin Configuration, p.2, reads:

> `TOP VIEW` / `MS8E PACKAGE` / `8-LEAD PLASTIC MSOP` / `R1 R2 R3 R4` /
> `1 2 3 4` `8 7 6 5` / `EXPOSED PAD (PIN 9) IS FLOATING`

`[datasheet analog/LT5400.pdf p.2]`

Three separate defects fall out:

1. **The device's sections are named `R1 R2 R3 R4`, not `A` and `B`.** The
   netlist's `section: A|B` names sections this part does not have — and the
   netlist's *refdes* are `R1` and `R2`, which collide with the datasheet's own
   section names while the `section:` field says something else. Which two of
   the four, and therefore which four of the eight pins, is unstated.
2. **Four pins (sections R3 and R4) and the exposed pad are in no net.** The
   package has **nine** numbered terminals; four appear. The DAC netlist states
   the principle this violates, in its own words: "*an unlisted pin and a pin
   listed as going nowhere read the same in a picture and not at all the same
   in a layout review*" `[repo hardware/module/dac8568/netlist.yaml]`.
3. **The exposed pad is a decided-open layout question that exists only in the
   BOM notes and not in the file a tool reads.** The datasheet, p.6:

   > "The exposed pad is not DC connected to any resistor terminal … To avoid
   > interference, do not tie the exposed pad to noisy signals or noisy grounds.
   > **Connecting the exposed pad to a quiet AC ground is recommended** as it
   > acts as an AC shield and reduces the amount of resistor-resistor
   > capacitance."

   `[datasheet analog/LT5400.pdf p.6]` — and Note 2 counts "*the voltage across
   any pin with respect to the exposed pad*" toward the ±80 V rating
   `[datasheet analog/LT5400.pdf p.2]`, so it is an electrical terminal, not
   mechanical.

**Verified OK alongside it:** the *choice* of two sections is sound whichever
two, because the matching spec is `∆R/R` "**Resistor Matching Ratio (Any
Resistor to Any Other Resistor)**" `[datasheet analog/LT5400.pdf p.3]` and is
defined as "*the ratio error of the largest of the four resistors to the
smallest of the four*" `[datasheet analog/LT5400.pdf p.5]`. I checked this
because the Available Options table columns are `R2 = R3 (Ω)` and `R1 = R4 (Ω)`,
which reads like a pairing constraint; it is not one. **The pitch stage's
0.027-cent ratio claim survives.**

**Wrong if:** `R-PRECISION`'s two sections are meant to stay unassigned until
layout and `section: A|B` is a placeholder. The row is `status: open`, so that
is possible — but then the placeholder should not use letters the part does not
have, and the exposed pad still has no representation.

**Smallest fix:** rename to `section: R1` / `section: R2` (or whichever two),
and add a third component for the pad — `LT5400-EP` with `pins: [EP]` in a
single-endpoint net named for the open decision, exactly as `dac8568`'s
`DAC_CH6_UNUSED` does. That makes the open question visible to `--strict`
instead of only to a reader of `bom.csv`.

---

## N4-5 — `U-DAC`: the channel→letter map (commissioned claim 1)

**Severity: medium — and not where the author put the warning.**

### The pin names are exactly right

All sixteen pin names in `hardware/module/dac8568/netlist.yaml` are SBAS430E's
own, and the pin-number comment in that file is correct line for line
`[datasheet analog/DAC8568CIPW.pdf p.6, PIN DESCRIPTIONS]`:

> 1 `LDAC` · 2 `SYNC` · 3 `AVDD` · 4 `VOUTA` · 5 `VOUTC` · 6 `VOUTE` ·
> 7 `VOUTG` · 8 `VREFIN/VREFOUT` · 9 `CLR` · 10 `VOUTH` · 11 `VOUTF` ·
> 12 `VOUTD` · 13 `VOUTB` · 14 `GND` · 15 `DIN` · 16 `SCLK`

Sixteen declared, sixteen used exactly once, two named as no-connect by
decision. **This is the best-formed component in the corpus** and the only one
that cites the document its pin names came from.

### "No document in this corpus states that map" — verified

`grep -rniE "VOUT[A-H]|DAC ?[A-H]\b|channel [A-H]\b"` over
`hardware/ docs/decisions/ docs/reference/ config/ firmware/ README.md
ROADMAP.md`, excluding the DAC netlist itself, returns **zero hits** `[test]`.
ADR 0006 allocates purely by number — `DAC ch 1` pitch, `ch 2–5` mod 1–4,
`ch 6` spare, `ch 7` the 3.3333 V reference `[repo docs/decisions/0006-cv-channel-allocation.md]`
— and `firmware/` contains one `README.md` and no code `[test]`. The author's
statement is accurate.

### Is the map right?

**Internally, yes, and it is the only reading available.** ch6→`VOUTF` and
ch8→`VOUTH` are the 6th and 8th letters; the six live nets run `VOUTA`…`VOUTE`,
`VOUTG` with no gap or repeat. And a 1..8 numbering *cannot* be the datasheet's
own numbering, because —

**the DAC8568 datasheet never numbers a channel.**
`grep -niE "channel ?[0-8]|DAC ?[0-8][^.0-9]|ch[0-8]"` over the full 62-page
extraction returns **zero hits** `[test]`. Channels are named `A`…`H`
throughout. The *only* numeric handle the part offers is the four address bits
`A3..A0`, and those are **0-based** `[datasheet analog/DAC8568CIPW.pdf p.35,
Table 11]`:

> `0 X 0 0 0 0 0 0 0 0  Data  X X X X  Write to input register - DAC Channel A`
> `0 X 0 0 0 0 0 0 0 1  Data  X X X X  Write to input register - DAC Channel B`
> `0 X 0 0 0 0 0 0 1 0  Data  X X X X  Write to input register - DAC Channel C`

So `address = 0` is channel A. Under the netlist's map, firmware must write
`address = N − 1` for "channel N". **Nothing in the corpus says that.** A
firmware author who writes `address = N` rotates every output by one pin:
pitch (ch1) leaves on `VOUTB`, which this netlist wires to mod 1's jack; the
3.3333 V shared reference (ch7) leaves on `VOUTH`, which this netlist declares
`DAC_CH8_UNUSED`. With the mod reference stuck at 0 V and the mod channels at
`Vout = 4·Vdac − 3·Vref`, all four jacks sit at `4·Vdac` — which
`firmware/README.md` already identifies as the failure shape for a missing ch7
refresh `[repo firmware/README.md:60-64]`. Same symptom, different cause, and
the corpus has a name for it and no defence against it.

**So: the finding is not that the letter map is wrong. It is that the netlist
asserted the half of the join that nothing can act on, and left unasserted the
half that firmware will act on.** The comment says "*Contradict it in ADR 0006
if it is wrong and this file follows*" — but ADR 0006 as written cannot
contradict it, because it has no vocabulary for letters or addresses.

**Wrong if:** some banked document or corpus file joins number to letter and my
grep missed the spelling. I searched `VOUT[A-H]`, `DAC [A-H]`, `channel [A-H]`
case-insensitively across the whole §6 corpus; a join written as, say, "the
first output" in prose would escape it.

**Smallest fix:** one table in ADR 0006, beside the allocation table it already
has:

| ADR channel | DAC8568 output | pin | address `A3..A0` |
|---|---|---|---|
| ch 1 | `VOUTA` | 4 | `0000` |
| … | … | … | … |
| ch 7 | `VOUTG` | 7 | `0110` |
| ch 8 | `VOUTH` | 10 | `0111` |

The address column is the one that has to be there. The netlist then cites it
and deletes its own `[derived, not cited]` marker — and the map stops being an
assertion made in the one file firmware never reads.

---

## N4-6 — `U-LVL-MOD` / `U-LVLSHIFT` (74AHCT125): gate assignment, gate *letters*, and `OE` (commissioned claim 2)

**Severity: low for the assignment, medium for the `OE` tie.**

### Pin names: exact

All fourteen match `[datasheet logic/SN74AHCT125.pdf p.1]`:

> `1OE 1A 1Y 2OE 2A 2Y GND` (1–7) · `VCC 4OE 4A 4Y 3OE 3A 3Y` (14–8)

Both netlists declare all fourteen, each used exactly once. The function table
confirms the active-low sense: `OE = L, A = H → Y = H`; `OE = H → Z`
`[datasheet logic/SN74AHCT125.pdf p.2]`. All four `OE` tied to GND therefore
means **enabled**, which is what both notes claim. Correct.

### The assignment is free — but it is written in letters the part does not have

The datasheet numbers the gates `1`–`4` and uses **no letters anywhere**.
The two netlists then introduce letters, and not compatibly:

- `carrier/led-strip-drive`: nets named `GATE_A_OUT` (`1Y`), `GATE_C_OUT`
  (`3Y`), `SPARE_GATE_B_OUT` (`2Y`), `SPARE_GATE_D_OUT` (`4Y`), and a note
  "*Gates B and D are spare*" — so A=1, B=2, C=3, D=4
  `[repo hardware/carrier/led-strip-drive/netlist.yaml]`.
- `module/digital-and-supervision`: numbers only — "*Gate 4 is the spare the
  BOM row mentions*" — with `1A`=SCLK, `2A`=MOSI, `3A`=CS_MOD, `4A` tied to GND
  `[repo hardware/module/digital-and-supervision/netlist.yaml]`.

The assignment itself is unfalsifiable and harmless: the four gates are
electrically identical, so any permutation works. The **naming** is the defect —
one file's "gate D" is the other file's "gate 4", the device calls it neither,
and the corpus has already been bitten once by a number/letter join with no
joining statement (N4-5, same wave, same shape).

### The `OE` tie contradicts the datasheet's stated recommendation, and neither note says so

`[datasheet logic/SN74AHCT125.pdf p.1, description/ordering information]`:

> "To ensure the high-impedance state during power up or power down, **OE
> should be tied to V<sub>CC</sub> through a pullup resistor**; the minimum
> value of the resistor is determined by the current-sinking capability of the
> driver."

Both netlists tie all four `OE` **to GND**, permanently
`[repo hardware/carrier/led-strip-drive/netlist.yaml`, net `PWR_GND`;
`hardware/module/digital-and-supervision/netlist.yaml`, net `DIG_GND]`. In
`led-strip-drive` this is not incidental: the note on `R-LED-PD-1` says the
pull-downs "*cannot be added later*" because "*GPIO1 is high-impedance for the
bootloader window, **OE is tied low**, and an AHCT input floating near its
threshold becomes clean 5 V edges into 25 LEDs*". That is precisely the
power-up condition the datasheet's recommendation exists to prevent, solved on
the input side instead of the enable side. It may well be the right trade —
`OE` on the module side has no comparator left to drive it — but the datasheet
recommends against it and **neither note records that it is a departure.** A
later reviewer reading only the netlist has no way to know the recommendation
exists.

**Verified OK — the module note's electrical claims both check out**
`[datasheet logic/SN74AHCT125.pdf p.3]`:

- "*Inputs are TTL thresholds, V_IH 2.0 V min, not ratioed to VCC*" → recommended
  operating conditions, `V_IH` min **2 V**, `V_IL` max **0.8 V**, flat across
  `VCC` 4.5–5.5 V. ✔
- "*there is NO INPUT CLAMP TO VCC, which is what makes back-driving an
  unpowered module safe*" → absolute maximum ratings give `Input voltage range,
  V_I  −0.5 V to 7 V` — **independent of VCC** — while `Output voltage range,
  V_O` is `−0.5 V to VCC + 0.5 V`; and clamp current is specified as `Input
  clamp current, I_IK (V_I < 0)` only, versus `Output clamp current, I_OK
  (V_O < 0 **or V_O > VCC**)`. The asymmetry is the evidence, and it is
  conclusive. ✔

**Wrong if:** a later revision of SCLS264O drops the pull-up recommendation.
The banked copy is Rev O, July 2003, and carries it.

**Smallest fix:** drop the letters from `led-strip-drive`'s net names
(`GATE_1_OUT`, `SPARE_GATE_2_OUT`, …) so both files speak the device's own
numbering; and add one clause to each `U-LVL*` note: "*OE to GND, not to VCC
through a pull-up as SCLS264O p.1 recommends — the pull-downs on the A inputs
cover the power-up window instead.*"

---

## N4-7 — `U-REF-BREATH` (REF5050AIDR): three pins declared of eight, two of them `DNC`

**Severity: low-medium.**

`hardware/carrier/breath-excitation-reference/netlist.yaml` declares
`pins: [VIN, VOUT, GND]`. The REF50xxAI in 8-pin SOIC has
`[datasheet analog/REF5050.pdf p.4, Table 5-1]`:

| pin | name | note |
|---|---|---|
| 1, 8 | `DNC` | "**Do not connect**" |
| 2 | `VIN` | declared ✔ |
| 3 | `TEMP` | "Temperature monitoring pin. Provides a temperature-dependent output voltage" — undeclared |
| 4 | `GND` | declared ✔ |
| 5 | `TRIM/NR` | "Output adjustment or noise reduction pin" — undeclared |
| 6 | `VOUT` | declared ✔ |
| 7 | `NC` | "No internal connection" — undeclared |

Nothing here is electrically wrong: `TEMP` is an output and may be left open,
`TRIM/NR` is optional, `NC` is nothing. The defect is that **"do not connect"
is an instruction to a layout, and it is nowhere in the file a layout is
transcribed from.** Pins 1 and 8 are the two most likely to get swept into a
ground pour by someone who has only the netlist.

By the DAC netlist's own standard this is the gap it names. Of the components
with a banked datasheet, `U-REF-BREATH` is the one that declares the smallest
fraction of its package — `U-DAC` 16/16, `U-LVL*` 14/14, `U-KEYS` 16/16,
`U-LOADSW` 8/8, `U-ADC` 8/8, `U-DIFFRX` 8/8 `[test]`.

**Wrong if:** netlists here are understood to carry only connected pins, and
`dac8568`'s no-connect nets are an exception rather than the rule. `dac8568`
argues the opposite in prose, and nothing in `hardware/README.md` states a rule
either way — so this is a convention that exists in one file and should be
stated once.

**Smallest fix:** declare all eight and give pins 1, 3, 5, 7, 8 a
single-endpoint net each (or one `REF_UNUSED_PINS` net if the tool tolerates
it), with `DNC` in the note.

---

## N4-8 — `U-TVS-SPI` / `U-TVS-CHAIN` (SP0504BAHTG): right pin count, invented names, and the common pin cannot be read from the banked document

**Severity: low.**

Both declare `pins: [CH1, CH2, CH3, CH4, GND]`
`[repo hardware/carrier/netlist.yaml`, `hardware/interfaces/key-chain-loom/netlist.yaml]`.

The banked ordering table gives `SP0504BAHTG · CH 4 · SOT23-5`
`[datasheet discrete-and-power/SP0504BAHT.pdf p.1]`, so **five pins, four
channels plus a common — the count is right.** ✔

But the `Pinout` block on the same page is a graphic. The only text in it is
pin numbers (`1 2 3` one side, `4 5` the other, read by coordinate), and the
diode symbols that say which pin is the common carry no text. **Which numbered
pin is ground is not readable from the banked document.** The names `CH1`–`CH4`
and `GND` are the netlist's own; the datasheet supplies no pin names at all.

Also: `carrier` calls the part "`SP0504BAHT` or equivalent"; the datasheet's
order code is `SP0504BAHTG` (the `G` is Lead-Free/Green), and
`key-chain-loom` spells it with the `G`. `MANIFEST.csv` uses `SP0504BAHT`.

**Wrong if:** a footprint file for the part is banked somewhere I did not find.
`find datasheets -type f` shows no `.kicad_mod` for it `[test]`.

**Smallest fix:** none required for correctness — but note in `U-TVS-SPI`'s
`note:` that the pin-number map is not in the banked document, so it is taken
from the footprint at layout time and must be checked then. That is the kind of
thing this repo normally writes down.

---

## N4-9 — `J-CV-PITCH`, `J-CV-BREATH`, `J-CV-MOD1`–`4` (PJ398SM): the third pad, named once out of six

**Severity: low.** All six declare `pins: [TIP, SLEEVE]`. The banked footprint
`datasheets/connectors/PJ398SM.kicad_mod` has **three** pads `[repo]`:

```
(pad T  thru_hole roundrect (at 0 -4.92) ...)
(pad S  thru_hole oval      (at 0  6.48) ...)
(pad TN thru_hole roundrect (at 0  3.38) ...)
```

`TN` is the tip-normalling switch contact. It is accounted for — the `J-CV` BOM
row says "*PIN 2 = TIP-NORMAL SWITCH CONTACT — NORMALLY CLOSED TO PIN 3 AND
OPENING WHEN A PLUG IS INSERTED … THE SWITCH CONTACT IS FREE NORMALLING and
nothing in the design uses it yet*" `[repo hardware/bom.csv]` — and
`pitch-stage` repeats it: "*Its third pin, the normalling switch contact, is
unused and not netted*" `[repo hardware/module/pitch-stage/netlist.yaml:99]`.

`grep` for that statement across the corpus finds it on **`pitch-stage` only**
`[test]`. `breath-output-stage`'s jack and `mod-channels`' four say nothing.
Electrically harmless (unplugged, `TN` is shorted to `T` anyway), but it is a
pad on the board that five of six netlists neither declare nor disclaim — the
`dac8568` distinction again, between "no-connect by decision" and "absent".

The pad names are also `T`/`S`/`TN`, not `TIP`/`SLEEVE`.

**Wrong if:** the BOM row is taken as covering all six instances, which is a
defensible reading — `J-CV` is one row, qty 6, filed at board level precisely
because three circuits share it.

**Smallest fix:** delete the note from `pitch-stage` and rely on the BOM row
(consistent silence), or add `TN` to all six `pins:` lists with a
single-endpoint net (consistent disclosure). Either is better than one of six.

---

## N4-10 — `U-DIFFRX.RG1` / `.RG2` (INA828): a pin name the device does not have, twice

**Severity: low.**

`hardware/module/breath-receive-stage/netlist.yaml:88-89` declares
`pins: [IN+, IN-, REF, RG1, RG2, OUT, V+, V-]`. The INA828 SOIC-8 pin table
`[datasheet analog/INA828IDR.pdf p.3, Pin Functions]`:

> `RG` **1** and **8** — "Gain setting pin. Place a gain resistor between pin 1
> and pin 8." · `–IN` 2 · `+IN` 3 · `–VS` 4 · `REF` 5 · `OUT` 6 · `+VS` 7

The datasheet gives **both** gain pins the same name, `RG`. `RG1` and `RG2` are
the netlist's invention, and nothing says which is pin 1 and which is pin 8.
Harmless — a gain resistor is symmetric — but it is a pin name that resolves to
two possible pins, in a file that exists to be unambiguous. `IN+`/`IN-` vs the
datasheet's `+IN`/`–IN` and `V+`/`V-` vs `+VS`/`–VS` are the same class,
unambiguous.

**Verified OK in the same component**, both claims in the `U-DIFFRX` note
`[datasheet analog/INA828IDR.pdf p.22, §8.1 Reference Terminal]`:

> "any resistance at the reference terminal (shown as R<sub>REF</sub> …) is in
> series with one of the internal **40-kΩ** resistors … For the best
> performance, keep the source impedance to the REF terminal, R<sub>REF</sub>,
> **below 5 Ω**."

The netlist says "*below 5 ohm per the datasheet … RREF sits in series with an
internal 40k arm*" — both exact ✔ — and `REF` is driven from `U-REF-BUF.OUT`
(a buffer output), never from the trimmer wiper, which is the thing the
datasheet's warning is about `[repo hardware/module/breath-receive-stage/netlist.yaml`,
net `REF_DRIVE]`. ✔

**A trap for whoever fixes this, worth recording:** SBOS792A's §8.1 prose calls
`REF` "**pin 6**" ("*in dual-supply operation, the reference pin (pin 6) is
connected to the low-impedance system ground*") while its own Pin Functions
table on p.3 says `REF` = 5 and `OUT` = 6. **The table is right and the prose
is a datasheet typo.** Do not "correct" the netlist from §8.1. The functional
names in use here are immune to it, which is an argument for functional names
and against the pin-number comment style.

**Smallest fix:** `pins: [..., RG(1), RG(8), ...]` or a note naming which is
which. One line.

---

## N4-11 — `U-DAC.AVDD`: no decoupling capacitor on the net

**Severity: low / informational.** `DAC_AVDD` in
`hardware/module/dac8568/netlist.yaml` contains exactly `port`, `U-DAC.AVDD`
and `R-CLR-PU.1` — no capacitor. Every other supply pin in the corpus has one
at the package (`U-LVLSHIFT.VCC`+`C-DECOUPLE-LED`, `U-KEYS.VCC`+`C-DECOUPLE-165`,
`U-LOADSW.VCC`+`C-DECOUPLE-LOADSW`, `U-ADC.VDD`+`C-DEC-ADC`+`C-ADC-BULK`).

This sits inside a gap the checker already reports rather than being a new one:
`instances: … 7 short: … C-DECOUPLE 1/19 …` `[test]` — eighteen of nineteen
bought decouplers are placed in no netlist. Filing it against the pin so it is
answerable by refdes rather than only as a bulk count.

**Wrong if:** the DAC's decoupler is one of the eighteen and is simply awaiting
placement, which is almost certainly the case.

**Smallest fix:** place one `of: C-DECOUPLE` instance on `DAC_AVDD`.

---

# Parts that check out

Named with the document and page checked, per the brief.

| refdes | part | document | verdict |
|---|---|---|---|
| `U-DAC` | DAC8568ICPW | `analog/DAC8568CIPW.pdf` p.6 | **16/16 pin names exact**, each used once, two spares named as no-connect. `CLR` (pin 9, "Asynchronous clear input", active low) pulled **up** by `R-CLR-PU` = inactive ✔. `LDAC` (pin 1, "Load DACs", active low) strapped **low** = asynchronous update ✔, and `R-LDAC` is correctly described as a strap and not a pull-up. `LK-CLR` normally open ✔. `VREFIN/VREFOUT` out to pitch-stage, internal reference, grade C footnote on p.6 applies to *external* VREFIN only ✔ |
| `U-LVLSHIFT`, `U-LVL-MOD` | SN74AHCT125 | `logic/SN74AHCT125.pdf` p.1–3 | 14/14 names exact; `OE` active-low sense correct at GND; `V_IH` 2 V and the absent VCC input clamp both confirmed (see N4-6 for the two naming/recommendation items) |
| `U-KEYS` | 74HC165 | `logic/74HC165-ti-scls116e.pdf` p.1 | 16/16. TI's names are `SH/LD CLK E F G H QH̄ GND QH SER A B C D CLK INH VCC`; the netlist's `SHLD`/`CLKINH`/`QH_BAR` are those names minus punctuation. **`CLK INH` tied low** matches p.2: "*Clocking is accomplished by a low-to-high transition of CLK while SH/LD is held high and CLK INH is held low*" ✔. `QH̄` left as an unconnected output, explicitly ("*DO NOT GROUND IT*") ✔. Note: the netlist's names are **TI's**, not Nexperia's (`PL CP DS D0–D7 Q7`), and `datasheets/logic/74HC165-nexperia.pdf` is also banked — worth a one-line citation in the file saying which |
| 74HC165 `A`–`H` | — | `[calc]` | All 32 register inputs across 4 boards are pulled up, none floating: 21 `key-switch-network` instances + 3 `R-KEY-PU-FREE*` + 8 marker straps (2/board) = **32 = 4 × 8** ✔ |
| `U-LOADSW` | LT1641-1CS8 | `discrete-and-power/LT1641.pdf` p.2, PIN FUNCTIONS | 8/8: `ON`1 `FB`2 `PWRGD`3 `GND`4 `TIMER`5 `GATE`6 `SENSE`7 `VCC`8. `R-ILIM` between `VCC` and `SENSE` matches "*A sense resistor must be placed in the supply path between VCC and SENSE*" ✔. **`PWRGD` left open is correct**, not a floating input — "*Open Collector Output to GND*" ✔. `V_CC` 9–80 V against a +12 V rail ✔. The undesigned UVLO divider (`SW-POWER.NO` → nothing, so `ON` floats) is a **declared** open, named in the netlist and the page, not a transcription gap |
| `U-ADC` | MCP3202-CI/SN | `analog/MCP3202-CI-SN.pdf` p.1, p.17 | 8/8 pins present. Two names are abbreviated: pin 1 is `CS/SHDN` (netlist `CS`) and **pin 8 is `VDD/VREF`** (netlist `VDD`) — but the dual reference role is correctly captured in the netlist note ("*NO VREF PIN - VDD IS THE REFERENCE*") and on the page ✔. `VSS`, `CH0`, `CH1`, `DIN`, `DOUT`, `CLK` exact. `CH1` spare, declared as a single-endpoint net ✔ |
| `U-BREATH` | MPXV4006DP | `analog/MPXV4006DP.pdf` p.4, p.20 | `Vs`, `Vout`, `GND` are the datasheet's names ✔. "*Pins 1, 5, 6, 7, and 8 are NO CONNECTS for small outline package device*" (p.4) — the netlist leaves all five alone ✔ |
| `SW-POWER` | NKK M2011SD4G01 | `connectors/NKK-SERIES-M-TOGGLE.pdf` | **Two terminals is right**: "*M2011 model does not have terminal 1*", and the Poles & Circuits table gives `M2011 · SP · ON-NONE-OFF · SPST` with connected terminals `2-3 / OPEN / OPEN`. **Terminal 2 is labelled `(COM)`** — so `COM` is the datasheet's own name ✔. `NO` is invented but matches the topology |
| `J-LED-L.BI`, `J-LED-R.BI` | WS2815 | `led/WS2815.pdf` p.4, Recommended application circuit | **The netlist's load-bearing claim is correct.** The app-circuit graphic (rendered at 12× and read) shows L1 pin 6 `BI` joining pin 5 `GND` on a common vertical down to the GND rail, while L1's `DI` node runs down and right to feed **L2's** `BI`. So "*ties the first pixel's BI to its GND; from the second pixel on, BI comes from the previous pixel's DI*" ✔ — and with it the argument that gates 2 and 4 are genuinely spare. The app circuit also spells the pins `DI` and `BI`, matching the netlist, though the Pin Function table on p.2 spells them `DIN` and `BIN` |
| `U-MCU-RT` GPIO set | ESP32-S3-Matrix | `mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf` p.1 | All of `IO1 IO2 IO5 IO6 IO7 IO33–IO40` are P1 pads ✔ (table in N4-1). **No collision with anything the board uses itself**: by y-coordinate matching, `IMU_SDA`=`IO11`, `IMU_SCL`=`IO12`, `IMU_INT1`=`IO10`, `IMU_INT2`=`IO13`, `LED_DIN`=`IO14` — and none of `IO10`–`IO14` is claimed by the corpus ✔. The module is `ESP32-S3FH4R2` (in-package quad flash+PSRAM), so `IO33`–`IO37` are free rather than consumed by octal PSRAM ✔. **`HDR-SERVICE`'s claim that "EN and IO0 are NOT available" is confirmed** — P1 carries neither ✔. `IO39`/`IO40` are the chip's `MTCK`/`MTDO` (JTAG); usable as GPIO, and no corpus page mentions it, which is fine but worth knowing |
| `D-JACK-CLAMP*`, `D-CLAMP-IN±` | BAV99 | `discrete-and-power/BAV99.pdf` | Topology ✔ and orientation ✔: the datasheet states "*Small Signal Switching Diode, **Dual in Series***" / "*Connected in series*", and the netlists put the signal on `.C` with `.K` to the positive rail and `.A` to the negative — the only correct use of a series pair as a two-rail clamp. **But** `A`/`K`/`C` are not the datasheet's names — it numbers 1/2/3 and shows the internal construction only as a graphic, so **which numbered pin is the common cannot be read from the banked document's text layer**. Same class as N4-8; flagging, not filing |
| `R-PRECISION` matching | LT5400-1 | `analog/LT5400.pdf` p.3, p.5 | Any-resistor-to-any-resistor; the two-of-four choice is sound (detail under N4-4) |
| `U-REG-DAC` | LM317LZ | `discrete-and-power/LM317LZ.pdf` p.3 | Names are `ADJUSTMENT`/`INPUT`/`OUTPUT`; netlist's `ADJ`/`IN`/`OUT` are unambiguous abbreviations ✔. The TO-92 (`LP`) pin *numbers* are not given in that table (checkmarks only), so the physical order is not provable from the banked copy |
| `U-BUCK-A`, `U-BUCK-B` | R-78E5.0-1.0 | `discrete-and-power/R-78E5.0-1.0.pdf` p.1 | `IN`/`GND`/`OUT` ✔; "*Pin-out compatible with LM78XX linears*", SIP3 |
| `SW1-n` | Gateron KS-33 | `mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` | **Not verifiable.** The banked file is the product *specification*, not the pin drawing — §2.2 and §5.1 both say "*Refer to individual product drawing*", which is not banked. §4.1 tests "*between each pair of terminals*", implying ≥2, and the rating is `10mA 12VDC`. The netlist's claim that the third pin is a locating post rather than a net is plausible and unproven here. Not filed as a finding — an honest gap, and the part is `status` -bearing elsewhere |
| `J-DISP`, `HDR-SERVICE`, `J-CHAIN`, `J-UMB-*`, `J-PWR-EURO` | generic headers / etherCON | — | Pin names are the loom's own, not a device's. Out of scope for pin identity; nothing to check against |

---

# Summary

| id | refdes | severity | one line |
|---|---|---|---|
| N4-1 | `U-MCU-RT.IO43/.IO44/.P3V3/.P5V` | medium | Four declared pins name nothing in the banked board schematic; the pads are `TX`, `RX`, `3V3`, `VCC_5V` |
| N4-2 | `U-OPA-PITCH` sections | **high** | `section: A` claimed by three circuits, `B` by two, `half` by six, on a qty-6 aggregate row — no op-amp half resolves to a pin |
| N4-3 | `U-OPA-PITCH.8`, `.4` | medium | No OPA2197 supply pin is in any net; `U-REF-BUF` has no `rails:` either, and the carrier buffers declare one rail of two |
| N4-4 | `R-PRECISION` (LT5400) | medium-high | Four pins and the exposed pad (datasheet's PIN 9) are in no net; sections named `A`/`B` where the device names them `R1`–`R4` |
| N4-5 | `U-DAC` channel map | medium | Letter map is the only consistent reading and is fine; the **address** map (0-based, `0000` = DAC A) is what firmware will act on and is stated nowhere |
| N4-6 | `U-LVL-MOD`/`U-LVLSHIFT` `OE`, gate letters | medium | All four `OE` tied to GND against the datasheet's explicit pull-up-to-VCC recommendation, undisclosed; and gate *letters* that the device does not have, used incompatibly across two files |
| N4-7 | `U-REF-BREATH` | low-medium | 3 pins of 8 declared; pins 1 and 8 are "do not connect" and that instruction is in no file a layout reads |
| N4-8 | `U-TVS-SPI`, `U-TVS-CHAIN` | low | Count right (SOT23-5, 4 ch); names invented; which pin is the common is not readable from the banked document |
| N4-9 | `J-CV-*` | low | Third footprint pad `TN` disclaimed on one jack of six |
| N4-10 | `U-DIFFRX.RG1/.RG2` | low | The device calls both pins `RG`; the netlist's two names resolve to two possible pins. Plus: SBOS792A §8.1 mis-numbers `REF` as pin 6 — do not "correct" from it |
| N4-11 | `U-DAC.AVDD` | low | No decoupler on the net; inside the checker's already-reported `C-DECOUPLE 1/19` shortfall |

**The pattern underneath N4-2, N4-4, N4-5 and N4-6 is one pattern.** Four times,
a netlist had to join a *logical* name the corpus uses (channel 7, gate D,
section A, R1) to a *physical* name the silicon uses (`VOUTG`, `3Y`, `+IN A`,
pins 2 and 7). Twice the author noticed and wrote `[derived, not cited]` — and
those two are the two that are actually safe, because they are declared. The
two that are not declared are the two that bite: a `section:` letter against a
six-package row identifies nothing, and a channel *address* nobody wrote down
rotates every CV output by one pin. **The marker went on the visible half.**
