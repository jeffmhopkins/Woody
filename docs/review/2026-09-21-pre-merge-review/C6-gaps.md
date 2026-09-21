# C6 — The gaps: what the design needs that no document owns

**Slice:** the facts the design depends on that no file states, no figure
tracks, and no milestone decides.
**Method:** cold. No file under `docs/review/**` was opened, this wave's or any
other's. Every claim carries provenance: `[repo] path:line`, `[calc]` with the
arithmetic, `[datasheet]` with document and page, `[from memory]`.
**Findings are node-indexed** — against a net, a refdes, a named quantity or a
milestone ID, not a file and line.
**Report only.** Nothing outside this file was changed.

A note on what this slice can and cannot claim. Every finding below is a claim
that *no document owns a thing*. That is a negative, proved by search, so each
one names the searches that came back empty and says what would falsify it. A
gap is refuted by one file, and several below would be.

---

## Part 1 — The worst gaps, with the consequence in one line

**G1. The umbilical's conductor gauge is nowhere specified, and every power and
analog-return number in the project assumes 24 AWG.**
`CABLE-UMB` buys a *stranded* Cat5e patch lead; stranded patch cord is commonly
26 or 28 AWG, which is 1.6× to 2.6× the assumed loop resistance — and the
breath pair's error budget is one of the things sized against it.

**G2. `breath-working-point` is `disputed`, its `decided_by` names M1, and M1
cannot decide it.**
M1 is switch characterisation — cutout, bounce, hysteresis, spring weight. It
has no player, no mouthpiece and no manometer. Meanwhile 2.8 kPa is being used
as settled in three corpus derivations.

**G3. `matrix-led-current` is `blocked` on a bench measurement at E1, and E1
measures the wrong current.**
E1 measures *idle / unlit*. The blocked figure is *full white, 64 LEDs*, and it
is what ADR 0014's non-configurable brightness clamp is sized from.

**G4. There is no fingering system — no document, no data file, no milestone
that authors one.**
E5 is "first playable" and says the fingering table is "exercised". Nothing in
the repository says what any fingering *is*.

**G5. No single document owns the ESP32-S3 GPIO assignment.**
It is spread across five schematic pages, it is the contract firmware must match
exactly, and it is unretrofittable once the body closes on a socketed dev board.

**G6. The thermal environment has no owner, and the corpus works to three
mutually inconsistent assumptions about it.**
"10–20 K above ambient" (eight places, untracked), "65 °C ambient" at the buck,
"60 °C interior" at the matrix Schottky. No maximum interior temperature is
stated anywhere, and it is the input to the lighting clamp, three deratings and
the breath zero.

**G7. No document enumerates single-conductor faults in the umbilical, although
the corpus names conductor fracture as the cable's expected wear-out mode.**
Two of the eight cases are silent (`CS` open → the rack drones), one is
damaging (`PWR_GND` open → the instrument's supply return goes down `DIG_GND`).

**G8. The layout file's own generator does not exist and no milestone builds
it.**
ADR 0010's consequence names "a small generator in `tools/`" that turns
`key-layout.yaml` into plate DXF geometry and a firmware mapping. `tools/` holds
six repo-hygiene scripts and nothing else. M2 cuts the first plate.

**G9. The project has four partial open-item lists and no union.**
`figures.yaml` tracks 5 unresolved figures; `bom.csv` carries 33 `open` rows;
sixteen pages carry a `Still open` section; `ROADMAP.md`'s "Open items blocking
work" table has four rows. Nothing cross-checks them, and no tool can.

**G10. The rack — the environment the whole design is specified against — has
no specification.**
The README declares the target rack's supply "generous" and its +5 V rail
"regulated" as *stated properties*, with no number for either, and "11.4 V" is
in live use meaning two different nodes.

---

## Part 2 — Full findings, with provenance

### Section A — Load-bearing numbers that are in no document

#### A1. `CABLE-UMB` / nets `+12V`, `PWR_GND`, `BREATH`, `AGND` — conductor gauge is unspecified

Three independent derivations are built on 24 AWG:

- `[repo] docs/decisions/0005-power-architecture.md:91` — "Over 2 m of 24 AWG,
  round trip ~0.34 Ω", giving the 122 mV cable drop in the load table at line 95.
- `[repo] hardware/bom.csv` `U-BUCK` notes — "~121mV in 4m of Cat5 at 360mA",
  which is what establishes ~3 V of margin against the R-78E5.0's 8 V minimum
  input.
- `[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:100` —
  "0.168 Ω for 2 m of 24 AWG", which sizes the `AGND`-vs-`PWR_GND` return
  decision at 4.8 mV at the breath jack.

The part that has to deliver it: `[repo] hardware/unplaced.csv` `CABLE-UMB` —
"Cat5e STP patch lead, **STRANDED**, ~2m … solid core work-hardens and
fractures under constant flexing". The row constrains construction and
shielding and says nothing about gauge.

`[calc]` at 359 mA (`umbilical-current`), loop = 4 m:

| Conductor | Ω/m | Loop Ω | Drop |
|---|---|---|---|
| 24 AWG solid (assumed) | 0.0842 | 0.337 | **121 mV** |
| 26 AWG stranded | ~0.138 | 0.552 | **198 mV** |
| 28 AWG stranded | ~0.221 | 0.884 | **317 mV** |

`[from memory]` for the 26/28 AWG stranded figures — they are ordinary
wire-table values, not read from a banked document, and the exact number varies
with the strand count.

Consequences that move with it: the arriving +12 V (and with it the R-78E5.0
derating arithmetic and the buck's constant-power margin), `ferrite-bias-impedance`'s
operating current is unaffected but the rail it sits on is not, and — the one
that is not merely a margin — the `AGND` leg's series resistance in the breath
pair, where `breath-sense-link.md`'s 1.7 dB of CMRR margin already rests on two
parts' tolerance.

**Who notices, when:** nobody, until E11 measures breath noise over the real
cable at length, or E6 measures the rail. A 28 AWG lead passes every
paper check in the repository.

**What would settle it:** a gauge requirement on the `CABLE-UMB` row, sourced
either from a specific banked patch-lead datasheet or from a stated worst case,
and re-running the three derivations above against it. Patch leads are cheap
and the resistance is directly measurable with a four-wire meter — this is a
ten-minute bench answer, not a research question.

#### A2. `breath-working-point` — a `disputed` figure is load-bearing in three live derivations

`[repo] config/figures.yaml` `breath-working-point`: `status: disputed`,
candidates "2.8 kPa (cited to ADR 0003, which does not contain it; the two
schematic pages cite each other)", "0–5 kPa", "3–4 kPa".

Live uses of 2.8 kPa as fact:

- `[repo] hardware/carrier/breath-adc/breath-adc.md:37-38` — "real play = 2.8 kPa
  → … → 1795 counts", annotated `[2.8 kPa from breath-receive-stage.md]`, which
  is precisely the circular citation the register describes.
- `[repo] hardware/module/breath-output-stage/breath-output-stage.md:39,42` —
  the hard-blow row of the gain table, **−4.64 V** at the in-amp output.
- `[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:193`.

**Who notices, when:** at E10, when the panel GAIN range is trimmed and the
stage turns out to be scaled for the wrong working point; or never, because
`POT-GAIN` absorbs it and the instrument simply uses a fraction of its range.

**What would settle it:** a manometer and a player — see D1 for why the
milestone the register names cannot do it.

#### A3. `AGND` / ADC reference — the LDO load-regulation figure behind `key-scan-current`'s consequence is `[from memory]`, and its datasheet is banked

`[repo] hardware/carrier/carrier.md:174` — "at an LDO load regulation of ~0.3 %
per 100 mA `[from memory]`: 0.077 % = 3.2 LSB". Repeated at
`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:122-123`.

`key-scan-current` is tracked and its `companion` field names both consequences
as stated elsewhere — but the *input* that converts 25.8 mA into 0.077 % is not
tracked and is explicitly unsourced. The LDO is the ESP32-S3-Matrix's onboard
ME6217C33M5G, and `datasheets/discrete-and-power/ME6217C33M5G.pdf` is banked
`[repo]`.

**Who notices, when:** never. The symptom carrier.md predicts — "the breath
reading moves when I press keys" — gets blamed on firmware, which is the
document's own stated reason for writing it down.

**What would settle it:** read load regulation off the banked ME6217C33M5G
datasheet and mark the provenance. Ten minutes, and the figure is already in the
repository.

#### A4. Rack rail tolerance — "11.4 V" names two different nodes and neither is owned

- `[repo] docs/decisions/0005-power-architecture.md:95` — 359 mA, "122 mV cable
  + 400 mV Schottky + 60 mV", **arriving** at the instrument as "~11.4 V", i.e.
  delivered from a **12.00 V** rack.
- `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:160` —
  "at −5 % is 11.4 V", i.e. the **rack rail itself**.
- `[repo] hardware/bom.csv` `U-BUCK` — "rack at 11.4V, less ~0.28V of Schottky …
  ~121mV in 4m", i.e. the second reading, stacking the losses on top.

Three documents, one numeral, two nodes. The rack's assumed rail tolerance is
not in `figures.yaml` and is not stated in the README's design-scope section,
which declares the rack's properties in words only
`[repo] README.md` ("generous supply", "regulated +5 V rail").

**Who notices, when:** at E6, if the bench supply happens to sag; otherwise it
propagates silently into every margin claim downstream.

**What would settle it:** one tracked figure for the rack +12 V worst case, one
for +5 V, both owned by ADR 0005, and a pass over the three documents above.
This is the exact shape `figures.yaml` exists to fix, on a quantity it does not
carry.

#### A5. Interior temperature — no maximum is stated, and three incompatible assumptions are in use

- "10–20 K above ambient" — `[repo] docs/decisions/0009-enclosure-construction.md:531`,
  `docs/decisions/0006-cv-channel-allocation.md:278`,
  `docs/decisions/0003-breath-sensing-path.md:243`,
  `docs/decisions/0001-mcu-and-board-partitioning.md:212`,
  `docs/decisions/0014-lighting.md:148`,
  `hardware/carrier/power-entry-instrument/power-entry-instrument.md:97`,
  `hardware/cluster/key-switch-network/key-switch-network.md:118`, and
  `docs/decisions/0007-imu-selection.md:211` in paraphrase. Eight places, one
  quantity, untracked — the register's blind spot by construction.
- "65 °C ambient" at the buck — `[repo] hardware/bom.csv` `U-BUCK` derating note.
- "60 °C interior" at the dev board's Schottky — `[repo] config/figures.yaml`
  `matrix-led-current` `supersedes_the_constraint`, and
  `docs/decisions/0014-lighting.md:394`.

`[calc]` these do not agree. ADR 0005's load table gives 4.1 W typical and 6.5 W
clamp-legal `[repo] 0005:157-161`; at ADR 0014's ~3 K/W `[repo] 0014:148` that
is 12–20 K, so a 25 °C room gives a 37–45 °C interior. The 60 °C and 65 °C
figures are a different and much harsher assumption. Neither is wrong; nothing
says which is the requirement.

The 3 K/W itself is declared an estimate — `[repo] 0014:184` "That figure is a
bounding estimate, not a measurement" — and is untracked.

**Who notices, when:** at M8's thermal soak, which is the last gate before the
instrument is called finished. If the answer is bad there, the fix is the
lighting budget, the plate, or the enclosure — all of which are cut by then.

**What would settle it:** a stated maximum interior temperature in ADR 0009 (the
enclosure owns the thermal path), tracked, with the three derating analyses
citing it. The M8 measurement then confirms or refutes one number instead of
three.

#### A6. The 3V3 rail has no current budget, and the one document that lists its loads omits both the largest ones

`[repo] docs/decisions/0005-power-architecture.md` power tree:
"real-time board 3V3 out ──┬── 74HC165 chain / ├── breath ADC / └── I2C
pull-ups", followed by "**3.3 V does not need its own converter.** The loads on
it are the shift register chain (microamps), the ADC (milliamps) and pull-ups,
all comfortably inside the headroom".

Two things missing from that list:

1. **The ESP32-S3 itself**, which is the dominant load on that LDO.
2. **`key-scan-current`**, a *tracked figure* — 25.8 mA at 18 keys closed
   `[repo] config/figures.yaml`. ADR 0005 says "pull-ups" and gives no number,
   while the register carries one.

The LDO's own capability is itself contested: `[repo] config/figures.yaml`
`matrix-led-current` — "the ME6217C33M5G LDO's printed 800 mA is 'guaranteed by
design' and not production-tested, derating to ~250–500 mA on SOT-23-5".

**Who notices, when:** at E1, if idle current is measured at the 3V3 rail rather
than the 5 V input — which is not what E1 asks for; otherwise at E14 on the
carrier with all 18 keys closed, which is not a state anyone tests deliberately.

**What would settle it:** a 3V3 line in ADR 0005's load table, citing
`key-scan-current` rather than restating it, with the MCU's own draw and the
LDO's derated capability beside it.

---

### Section B — Untracked derived quantities (the register's blind spot)

#### B1. `AGND` / ADC — the playable breath span exists in two values and is in no register

`[repo] hardware/carrier/breath-adc/breath-adc.md:40` — "playable span above
rest ≈ **1598** counts of 4096".
`[repo] hardware/carrier/carrier.md:177,373` — "0.2 % of the **~1594**-count
playable span" (twice).
`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:126` — "against a
playable breath span of **~1594** counts".

`[calc]` from breath-adc.md's own derivation: 1795 − 197 = 1598. The 1594 is
off by four counts and is the version that appears three times, including on the
page that owns the argument.

This quantity is derived from `sensor-full-scale` (tracked) *and* from
`breath-working-point` (disputed, A2). It is the denominator of the only stated
acceptability claim about the key-scan reference step. It is in no register
entry, so nothing can see it diverge — and it already has.

**Who notices, when:** never. Four counts is invisible; what matters is that the
mechanism that produced it is unguarded, and `breath-zero-ref`'s `escape_note`
records exactly this shape of failure happening to a different quantity.

**What would settle it:** a `breath-playable-span` register entry owned by
`breath-adc.md`, blocked behind A2 since it cannot be correct while its input is
disputed.

#### B2. `J-UMB` pin 1/2 — the 58.5 dB link CMRR *requirement* has no derivation in the corpus

`[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:77-78` —
"link CMRR falls from 70.2 dB to 60.2 dB `[calc, A2]` against an independently
derived requirement of **58.5 dB**: 1.7 dB of margin". Repeated at
`[repo] hardware/module/breath-receive-stage/sim/README.md:19-20,75`.

The *achieved* figure carries its arithmetic (`:192`). The *requirement* carries
only the word "independently derived" and an agent's initials. What noise
amplitude on the pair, at what frequency, against what allowable error at the
jack? Not in the corpus.

A requirement with 1.7 dB of margin against it is a requirement that decides
whether `R1b` is sufficient, and `R1b` is on the unretrofittable side of the
cable.

**Who notices, when:** at E11 if the breath jack is noisy, at which point the
instrument is assembled. `R1b` is instrument-side and the body is closed.

**What would settle it:** either the derivation, written out where the 58.5 dB
is asserted, or a register entry marking it `disputed` with `decided_by: E11`.
The simulation deck exists and has not been run
`[repo] hardware/interfaces/README.md`.

#### B3. `plate_cutout` 14.00 mm and its tolerance are not tracked, while `plate-thickness` is

`plate-thickness` is a tracked, settled figure owned by `ks33-geometry.md`
`[repo] config/figures.yaml`. The cutout beside it is not:

- `[repo] config/key-layout.yaml` — `plate_cutout: 14.0`
- `[repo] ROADMAP.md` M1 — "**Cutout is 14.0 × 14.0 mm**"
- `[repo] config/figures.yaml` `plate-thickness` `note` — "Cutout confirmed and
  tightened to **14.00 +0.05/−0.02** square"

Three statements, two precisions, one tolerance that exists in only one of them —
and the one that carries the tolerance is a `note` field on a *different*
figure, where no check looks for it.

Same page, same source drawing, same commit-day. `plate-thickness` moved and is
protected; the cutout moved in the same breath and is not.

**Who notices, when:** at M1's test coupon, if whoever cuts it works from
`key-layout.yaml` (14.0, no tolerance) rather than from the register note. At M5
it is aluminium.

**What would settle it:** a `plate-cutout` register entry owned by
`ks33-geometry.md`, with `key-layout.yaml` and ROADMAP citing it.

#### B4. `key-layout.yaml` still carries `plate_thickness: null` against a settled figure

`[repo] config/key-layout.yaml` — "`plate_thickness: null` … OPEN, and it blocks
M4/M5. 2 mm defeats the retention clips entirely; MX standard is 1.5 mm; the
reference KS-33 build uses 1.1 mm. Needs the clip dimension from Gateron's
drawing (ADR 0002)."
`[repo] config/figures.yaml` `plate-thickness` — 1.20 mm, `status: settled`,
read off the banked Gateron drawing, with a note that **all three** of the
candidates listed above are out of the vendor window.
`[repo] hardware/cluster/cluster-boards.md:167` — "Plate thickness is still open
and blocks M4/M5 `[repo] key-layout.yaml`".

This is filed here rather than as staleness because of the *gap* it exposes:
`config/**` is in the corpus and the checker scans it, but a `null` is not a
stale value and no `forbidden` pattern can catch an absence. **The register can
protect a wrong number and cannot protect a missing one.** The same hole covers
every `TBD` in `bom.csv`.

**Who notices, when:** at M4, when CAD needs a thickness and the data file that
generates the plate says `null` while the register says 1.20.

**What would settle it:** a checker rule that a `settled` figure's owner-adjacent
data file may not hold `null` for the same quantity. Cheap, and it is the one
class of register failure that is mechanically detectable and not yet detected.

---

### Section C — Interfaces with no owner

#### C1. The ESP32-S3 GPIO map — the firmware/hardware contract, spread over five pages

Assembled here from the corpus `[repo]`:

| GPIO | Function | Stated in |
|---|---|---|
| IO1, IO2 | WS2815 strip data, into `U-LVLSHIFT` | `carrier/led-strip-drive/led-strip-drive.md:20,30,36` |
| IO5, IO6 | UART1 to the display board | `carrier/display-and-service-uart/display-and-service-uart.md:25,57` |
| IO7 | `SH/LD` chain latch | `interfaces/key-chain-loom/key-chain-loom.md:28,67` |
| IO33 | `SER` chain serial in | `interfaces/key-chain-loom/key-chain-loom.md:29,69` |
| IO34 | `CS` → DAC8568, down the umbilical | `interfaces/spi-link/spi-link.md:37` |
| IO35 | `SCLK` SPI2 | `interfaces/spi-link/spi-link.md:35` |
| IO36 | `MOSI` SPI2 | `interfaces/spi-link/spi-link.md:36` |
| IO37 | `MISO` — MCP3202 `DOUT`, board-local | `interfaces/spi-link/spi-link.md:40` |
| IO38 | SPI3 `SCK`, chain | `interfaces/key-chain-loom/key-chain-loom.md:27,65` |
| IO39 | `CS` → MCP3202 | `carrier/carrier.md` §4 |
| IO40 | `QH` chain return (SPI3 MISO) | `interfaces/key-chain-loom/key-chain-loom.md:30,71` |
| IO43, IO44 | `U0TXD`/`U0RXD` console | `carrier/display-and-service-uart/display-and-service-uart.md:26,68` |
| GPIO10–13 | QMI8658C IMU (onboard) | `interfaces/spi-link/spi-link.md:125` |
| GPIO14 | 8×8 matrix (onboard) | `interfaces/spi-link/spi-link.md:125` |
| GPIO19/20 | USB (onboard) | `carrier/carrier.md` block diagram |

Five schematic pages plus two board-definition facts. `firmware/README.md` has
no pin table `[repo]` — searched, and it lists architecture constraints only.
`config/` has no pin file. `figures.yaml` has no entry.

This is exactly the class the `interfaces/` directory exists for — "their
numbers cannot be derived from one side"
`[repo] hardware/interfaces/README.md` — applied to the board/firmware boundary
instead of a board/board one. Two chip selects (IO34 to the DAC, IO39 to the
ADC) differ by one character and address devices two metres apart.

`[calc]` the block diagram claims 17 GPIO broken out
(`carrier/carrier.md`: IO1–IO7, IO33–IO40, IO43, IO44 = 7 + 8 + 2 = 17) and 15
are assigned above, leaving IO3 and IO4 — two spare, against the "three spare"
in `figures.yaml`'s `matrix-led-current`-adjacent PSRAM note and ROADMAP's E1
row. Minor, and a symptom: nobody is counting in one place.

**Who notices, when:** at F1/E14, by a person reading five pages to write a pin
header. A transposition is a wrong-device SPI transaction, which on a write-only
link is silent.

**What would settle it:** one table. Either `config/pins.yaml` beside
`key-layout.yaml` (which would also make it generatable, per ADR 0010's model),
or a section in `firmware/README.md` that the schematic pages cite.

#### C2. `J-DISP` — the display board's end of the loom is undrawn and has no page

`[repo] hardware/carrier/display-and-service-uart/display-and-service-uart.md:25`
— "UART1. **Far end undrawn**".

The carrier side is specified: 9-way, IO5/IO6 at 921600 baud, console pair, 5 V,
GND `[repo] :57,68,89`. The T-Display-S3 AMOLED side has no page, no
`circuit.yaml`, no BOM fragment, and no entry in `hardware/module.md`-equivalent
board list. Which of its 18 broken-out GPIO `[repo] hardware/unplaced.csv`
`U-DISP` carry UART1, whether its 5 V pin can be back-fed, and where buck B
lands are all unanswered — and the last of those is a *named* open item
`[repo] power-entry-instrument.md` "Still open", while the first two are not
named anywhere.

This is a board with an MCU, a radio, a screen and a flash image, and the
repository draws none of it.

**Who notices, when:** at E4b, which is the inter-MCU link milestone — by which
point the loom conductor list is fixed if `J-DISP` has been ordered.

**What would settle it:** a `hardware/display/` board page, or an explicit
statement in ADR 0008/0013 that the display board is used as a module with no
carrier-side drawing and that its pin selection is deferred to F-track.

#### C3. SPI2 — clock polarity and phase are specified nowhere, for two devices that need different modes

Searched `cpol|cpha|spi mode|falling edge|rising edge` across `hardware/**`,
`docs/decisions/**`, `docs/reference/**`, `firmware/**`, `config/**`,
`README.md`, `ROADMAP.md` `[repo]`. Two hits, both about the 74HC165's `SH/LD`
(`cluster/key-register/key-register.md:18,48`). Nothing about SPI2.

`[datasheet]` DAC8568, SBAS430, pin description for `D_IN`/`SCLK`, read from the
banked `datasheets/analog/DAC8568CIPW.pdf`: "Data are clocked into the 32-bit
input shift register on each **falling edge** of the serial clock input." That
is CPHA = 1 with CPOL = 0, or CPHA = 0 with CPOL = 1.

`[from memory]` the MCP3202 is a mode (0,0) / (1,1) part — data out on the
falling edge, sampled on the rising. If so, the two devices on SPI2 need
*different* modes.

This is recoverable — ESP-IDF sets mode per device on a shared host, the same
way it sets `clock_speed_hz` per device, which the corpus already notes is "a
firmware line and not a part change" and that **"It is written nowhere"**
`[repo] hardware/interfaces/spi-link/spi-link.md`. The clock-rate half of that
sentence is recorded; the mode half is not recorded at all.

**Who notices, when:** at E7, when commanded codes do not produce expected
voltages and the cause looks like a wiring fault. Recoverable in an afternoon —
this is a low-cost gap, listed because it is the same omission as the one the
corpus already flagged, one line away.

**What would settle it:** read the mode off the banked MCP3202 DS21034F (the PDF
is banked but resisted text extraction in this session — render it, as
`panel-toggle-hole` and `plate-thickness` did) and state both devices' modes
beside the clock rates in `spi-link.md`.

#### C4. `MECH-GNDBOND` — the aluminium plate is tied to `PWR_GND` and nothing owns the consequence

`[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md` —
"`MECH-GNDBOND` ties the aluminium plate to `PWR_GND`, never to `AGND`. This
board is the only place that bond can originate." `[repo] ROADMAP.md` M5 —
"bonded to `PWR_GND`".

What is owned: which net, and where it originates. What is not owned anywhere:
the plate is the surface under the player's hands, it is the instrument's
largest conductor, it is galvanically continuous with the rack's ground through
2 m of cable, and it is the design's stated thermal exit path
(`[repo] README.md` "Every watt leaves through the aluminium plate, part of
which is under the player's hands").

No document states what that means for touch temperature, for the plate as an
antenna on a 2 m tether, or for what happens to it if `PWR_GND` opens (see C5).

**Who notices, when:** at M8's two-hour play test, for temperature. Never, for
the rest.

**What would settle it:** a paragraph in ADR 0009, which owns the enclosure and
already owns the thermal argument. This is a documentation gap, not necessarily
a design one — the bond may well be right.

---

### Section D — Decisions nothing decides

Every `blocked`/`disputed` entry in `figures.yaml`, and the BOM's `open` rows,
crossed against `ROADMAP.md`.

#### D1. `breath-working-point` → `decided_by: M1` — M1 cannot decide it

`[repo] config/figures.yaml` `breath-working-point` `decided_by`: "**M1**, with
a player and a manometer. Sets the panel gain range AND the ADC headroom."

`[repo] ROADMAP.md` M1, in full: cutout dimension and test coupon, retention by
hand, bounce and actuation/reset hysteresis on five press/release cases, action
assessed by hand, thumb-key spring weight. It is a *switch* milestone. No
mouthpiece, no tube, no sensor, no manometer — the sensor is not even on the
bench until E2.

E2 is the milestone with the player, the mouthpiece, the tube, the trap and
twenty minutes of real playing `[repo] ROADMAP.md` E2. It is the milestone that
can answer this, and the register does not point at it.

The word "manometer" appears nowhere in `ROADMAP.md` `[repo]` — searched.

**Who notices, when:** M1 completes, the figure stays disputed, and nobody
re-reads the register to find out why. Then E2 runs without knowing it was
supposed to take this measurement, and the question survives to E10.

**What would settle it:** change `decided_by` to E2 and add the manometer
measurement to E2's "Bench measurements" row, where the equipment already is.

#### D2. `matrix-led-current` → "A BENCH MEASUREMENT AT E1" — E1 measures idle, not full white

`[repo] config/figures.yaml` `matrix-led-current`: `status: blocked`, candidates
960 / 2304 / 3648 mA, `decided_by` "A BENCH MEASUREMENT AT E1", `blocked_on`
"Unblocking needs a current probe, not a fetch", and `note` "**THIS NUMBER IS
LOAD-BEARING.** ADR 0014 uses it to argue the matrix alone nearly exhausts the
1 A R-78E5.0, and that argument drives a hard brightness cap that the ADR
deliberately makes non-configurable."

`[repo] ROADMAP.md` E1: "**PSRAM confirmed quad, not octal**, and **idle current
measured**".
`[repo] ROADMAP.md` bench table, first row: "**Real-time board idle current** |
E1 | 64 **unlit** `WS2812B-0807` drivers are an estimated ~50 mA … E1 measures
it".

Both are the *quiescent* figure. The blocked quantity is "ESP32-S3-Matrix LED
current, **full white, 64 LEDs**" — a different measurement with a different
setup, and the candidates span 960 to 3648 mA. Nothing in the roadmap asks for
it.

The clamp it justifies is also the one thing ADR 0014 will not let the user turn
off `[repo] 0014`.

**Who notices, when:** the figure stays `blocked` through E1 and nobody knows
why, because E1's own success criterion was met. It surfaces at M8's thermal
soak, or at E13 when buck A is sized.

**What would settle it:** a second E1 row — full-white current at the 5 V input
with a current probe, which is the same probe, the same board and the same
afternoon.

#### D3. `pitch-cents-budget` → no milestone at all

`[repo] config/figures.yaml`: `status: disputed`, four candidates (0.42 / 0.85 /
1.35 / ~1.2 cents), `decided_by` "pitch-stage.md has two contradictory budget
tables back to back and states no total. One coherent table, then cite it."

That is an editing task, not a measurement, and no milestone owns editing tasks.
E8 ("Pitch channel scaled") and E9 ("the milestone that decides whether this is
an instrument or a thing that is always slightly out of tune"
`[repo] ROADMAP.md`) both need a total error budget to judge a result against,
and neither names this figure.

The register also records that `power-entry.md` scaled a ground-path finding
against one of the four candidates `[repo] config/figures.yaml`, so a second
document is already downstream of the unresolved number.

**Who notices, when:** at E9, when a measured tracking error has nothing to be
compared against.

**What would settle it:** a documentation gate before E8, or an explicit
acceptance of one candidate. Either is cheap; neither is scheduled.

#### D4. `dig-gnd-topology` → `decided_by` a layer-count decision no milestone makes

`[repo] config/figures.yaml` `dig-gnd-topology`: `decided_by` "The 2-layer vs
4-layer decision, which is upstream of it."

Where the layer question lives: `[repo] hardware/module/module.md` "**Two layers
or four** is undecided and gates the grounding scheme";
`[repo] docs/reference/pcb-pipeline.md:245` "**Open: 2 layers or 4** … This is a
cost decision and it gates the routing."

Where it does not live: `ROADMAP.md`. Searched for "layer" `[repo]` — three
hits, all about the laminated mechanical stack or the ordering rules, none about
copper.

Meanwhile the BOM has already committed: `PCB-CARRIER` "**2-layer** PCB",
`PCB-CLUSTER` "**2-layer** PCB", `PCB-MODULE` "**2-layer** PCB"
`[repo] hardware/bom.csv` — all three at `status: open`, all three naming a
layer count as though it were settled.

**Who notices, when:** at E12/E13, when a board is laid out. `dig-gnd-topology`
is unretrofittable on a module that has been fabricated.

**What would settle it:** a milestone or a gate that takes the decision, before
E12. It is upstream of a disputed figure, upstream of the routing pipeline, and
already pre-empted in three BOM rows.

#### D5. `ref5050-grade` → a purchasing decision, and there is no purchasing milestone

`[repo] config/figures.yaml` `ref5050-grade`: `disputed`, `decided_by`
"Changing one letter in the order code, or accepting 2× the initial error and
2.7× the drift … it is a part change, not a documentation fix."

`ROADMAP.md` has no milestone about ordering, procurement or a BOM freeze —
searched for "order", "purchas", "procure" `[repo]`; the only hits are
"ordering rules" about milestone sequencing.

This is structural, not specific to this figure. Things the repo defers to a
purchase with nothing to defer them *to*:
`J-UMBILICAL` "variant TBD", `J-UMBILICAL-CABLE` "variant TBD" (status `open`),
`SW-THUMB` "KS-33 lighter variant — TBD at M1", `POT-GAIN` "taper TBD at E10",
`BODY-OAK` / `SIDE-ACRYLIC` / `ENDCAP-*` "TBD" `[repo] hardware/bom.csv`.
Two rows are deliberately blocked on a datasheet and say so, which CLAUDE.md
correctly calls not-a-defect; these are a different set.

**Who notices, when:** whoever places the first order, who will make a dozen
undocumented selections in one afternoon and will not write any of them down,
because there is no document for it.

**What would settle it:** a procurement gate per track — "BOM frozen for E6", "BOM
frozen for M4" — which is also the natural place to force the `candidate` →
`selected` transition that 81 BOM rows are waiting on.

#### D6. 33 `open` BOM rows, four of which are an entire circuit

`[calc]` from `hardware/bom.csv`: 81 `candidate`, 33 `open`, 17 `selected`,
4 `not-needed`, 2 `purchased`, 1 `available`.

`POT-RESP`, `R-RESP`, `D-RESP`, `U-RESP` are all `open`
`[repo] hardware/bom.csv` — that is the whole of
`hardware/module/breath-response-shaper/`, a circuit with a page, a drawing, a
`circuit.yaml` and a BOM fragment, in which no part is chosen and whose
insertion point is itself open
`[repo] hardware/module/breath-response-shaper/breath-response-shaper.md:26`
("*Where it inserts* is argued below and is open").

`ROADMAP.md`'s "Open items blocking work" table has four rows `[repo]` — plate
stiffening, CAD tool, oak thickness, the inter-MCU frame format. None of the 33.

**Who notices, when:** at E10, which is where `POT-RESP` is commissioned, with
no part chosen and no decision about where it goes in the chain.

#### D7. No milestone builds the `key-layout.yaml` generator, and M2 needs it

`[repo] docs/decisions/0010-key-layout-as-data.md` Consequences — "A small
generator in `tools/` turns the layout file into DXF cutout geometry and a
firmware header or config blob" and "The schema needs to exist before M2, since
the first laser-cut plate should be generated from it rather than drawn by
hand."

`[repo] tools/` holds `check-conservation.py`, `check-staleness.py`,
`merge-bom.py`, `merge-manifests.py`, `rewrite-paths.py`, `verify-datasheets.py`
— six repo-hygiene scripts and a `.gitkeep`. No generator.

`ROADMAP.md` M2 is "Full key count on a laser-cut plate, hand-wired, mounted to
a mock body; playable" `[repo]`. No F-track or tooling milestone produces the
generator; F1 is "Custom fingering table driven from config", which consumes a
different artefact.

The schema *does* exist — `key-layout.yaml` is complete but for the nulls — so
half of ADR 0010's consequence has landed and half has not.

**Who notices, when:** the day someone cuts the M2 plate, and draws it by hand
because the tool does not exist. ADR 0010's entire purpose — that the plate and
the firmware cannot drift apart — is lost silently at that moment, and the file
still looks like a source of truth afterwards.

---

### Section E — Failure modes nobody has written down

#### E1. Single-conductor faults in the umbilical, on a cable whose named wear-out mode is conductor fracture

The corpus names the mechanism: `[repo] hardware/unplaced.csv` `CABLE-UMB` —
"solid core work-hardens and fractures under constant flexing, **which is this
cable's whole life**".

The corpus names one failure case: cable *unplugged*, whole
`[repo] hardware/module/link-supervision/link-supervision.md` failure table, and
`ROADMAP.md` E10 "Pull the umbilical mid-note".

No document enumerates the eight single-conductor cases. Working them from the
pin map `[repo] config/figures.yaml` `umbilical-pinmap` and the pulls
`[repo] hardware/interfaces/spi-link/spi-link.md`:

| Open conductor | Behaviour | Loud or silent |
|---|---|---|
| 3 `+12V` | Instrument dead | **Loud** |
| 6 `PWR_GND` | The instrument's ~359 mA supply return has to find another path. `AGND` is behind 1 kΩ (`R1b`) + 10 kΩ (`R2`) and cannot carry it; `DIG_GND` is a direct tie at the module. **The whole supply return goes down the `CS` pair's ground partner** — a conductor sized for an SPI return — and power current lands on the digital ground reference, which is the one thing ADR 0004's star rule forbids | **Silent, and damaging.** The instrument probably still runs |
| 1 `BREATH` | In-amp `IN−` floats to the 1 MΩ bias pair. The stage does not saturate (that is what `R4`/`R5` are for) but the breath jack reads nonsense | Silent |
| 2 `AGND` | Same, on `IN+` | Silent |
| 7 `CS` | `R-SPI-PULL` holds it **high = deasserted**. The DAC is never framed again and **holds its last value forever** — pitch and four mod jacks frozen mid-note, with no `MISO` to notice | **Silent.** Identical to the deleted-watchdog case the corpus already calls "the everyday case" |
| 4 `SCLK` / 5 `MOSI` | Pulled low. Frames arrive corrupt or never; `CS` still toggles. A mis-framed 32-bit word reaches the software-reset and internal-reference-enable bits — the corpus's own "sticky failure" `[repo] spi-link.md` | **Silent and sticky** |
| 8 `DIG_GND` | SPI loses its return partner; signals reference through `PWR_GND` at the connector. Marginal, intermittent | Silent |

Six of eight are silent. `[calc]` on the pin-6 case only in the qualitative
sense above — the actual current division depends on `dig-gnd-topology`, which
is itself disputed, so the magnitude cannot be computed from the corpus as it
stands. That is part of the finding.

**Who notices, when:** in year two of playing the instrument, as "it sometimes
sticks". The `CS` case is indistinguishable from the accepted frame-watchdog
cost, which means the accepted cost will absorb the diagnosis.

**What would settle it:** the table above, in `link-supervision.md`, which is
already the page that owns "what we gave up and what it costs". Restoring
presence detect (the page's one open question) covers the `CS` and `PWR_GND`
cases and not the breath pair; that changes the cost/benefit of a decision the
page presents as still live.

#### E2. Nothing states what happens if `MECH-GNDBOND` or the plate bond is the only thing carrying return current

Follows from E1's pin-6 row and C4. The aluminium plate is bonded to `PWR_GND`
at the carrier `[repo] power-entry-instrument.md`, and the etherCON is mounted
on the plate stack, not on the PCB `[repo] hardware/carrier/carrier.md` block
diagram — "etherCON (on the plate stack, NOT on this PCB — ADR 0009)". Whether
the connector shell is bonded to the plate, and whether that shell is a return
path, is stated nowhere I can find.

For an STP cable (`CABLE-UMB` says "Shielded preferred") the shield's
termination at each end is also unspecified — searched `shield`, `drain`,
`STP` across the corpus `[repo]`; the only substantive hit is the BOM row
itself.

**Who notices, when:** at E11, as breath-channel noise with no identified source
— which is exactly the test ADR 0003's whole analog-breath decision rests on.

**What would settle it:** a shield-termination statement in
`breath-sense-link.md` (it owns the pair) or in ADR 0004 (it owns the
connector). One sentence either way, and "not terminated" is a legitimate
answer.

#### E3. Condensation and saliva in the tube are handled; the trap's service interval is not

`MECH-PTFE` "blocks liquid", trap volume ≤1 mL, "Size the orifice at E2"
`[repo] hardware/unplaced.csv`. ADR 0003 wants the trap "clearable without
disassembly" and `carrier.md` records that it is not: "ADR 0003 wants a
replaceable wear part and a trap 'clearable without disassembly'; ADR 0009 gives
a 12 × 40 mm cover over a 2×5 header. Those do not meet."
`[repo] hardware/carrier/carrier.md` Still open.

That much is named. What is not named anywhere: how often ≤1 mL fills during
normal play, and therefore whether the unmet requirement matters in a session or
in a year. A woodwind accumulates condensate continuously.

**Who notices, when:** the first time the instrument is played for two hours —
which is M8's play test, after the body is closed.

**What would settle it:** measure accumulation during E2's twenty-minute play
test. The test exists; the observation is one line added to it.

---

### Section F — Documents the project depends on and does not have

| Document | Depended on by | Present? |
|---|---|---|
| **Fingering system** — which fingering sounds which note | E5 (first playable), F1, ADR 0010's note-index model, and the "roughly 2.5–3 octaves" that sizes the calibration window `[repo] 0006:492` | **No.** `key-layout.yaml` says of itself "This file defines the physical layout only" `[repo]`. No milestone authors it |
| **GPIO / pin map** | F1, E14 | **No.** See C1 |
| **Mechanical drawing set** | M4–M7, the laser cutter, the plate DXF | **No.** `mechanical/cad`, `mechanical/drawings`, `mechanical/export` each contain exactly one empty `.gitkeep` `[repo]`. The CAD tool itself is an open item `[repo] ROADMAP.md` |
| **Layout → DXF / firmware generator** | M2, ADR 0010's entire thesis | **No.** See D7 |
| **Commissioning procedure** | E8, E9, E10 | **Partial, and in the wrong place.** The full trim order for the breath chain lives inside one ROADMAP table cell `[repo] ROADMAP.md` E10 — trimmer first, then gain, then panel offset, meter on the jack not the display. That is a procedure, written as a milestone criterion |
| **Calibration data format** | E9 ("stored in NVS with a version and a checksum"), F8, and the "blank or corrupt NVS" silent failure `[repo] ROADMAP.md` | **No.** The requirement is stated three times; the format is stated nowhere |
| **Inter-MCU frame format** | E4b | **No — and correctly tracked.** See G2 below |
| **Test / acceptance plan** | M8 ("Nothing closes until this passes") | **Partial.** M8's cell lists six tests; `latency-budget.md` has a characterisation table; `ROADMAP.md` has a bench-measurement table. Three lists, no union, no pass/fail criteria on most rows |
| **Assembly instructions** | M7, and the fact that the loom is hand-terminated once | **No.** Not searched for exhaustively; no candidate file exists |

The pattern across this table: the project is unusually good at recording
*decisions* and has no home for *procedures*. `docs/decisions/` and
`docs/reference/` are both present; there is no `docs/procedures/`, and
procedures are therefore landing in ROADMAP table cells, where they are one
milestone edit from being lost.

---

## Part 3 — Gaps I looked for and found were actually covered

Recorded so the next reader does not re-derive them.

**Inter-MCU frame format and protocol versioning.** Named as open in three
places and correctly routed: `[repo] docs/decisions/0013-two-mcu-split.md:291`
lists it under Open; `[repo] ROADMAP.md` "Open items blocking work" tracks it to
E4b; `[repo] firmware/README.md` states the requirement ("Put a protocol version
in the frame header from the first commit"). This is what a properly owned gap
looks like in this repository.

**The module's behaviour when the instrument is absent or the DAC is cleared.**
Thoroughly covered, and the `CLR` → +11.45 V trap is documented with its cause
corrected when the watchdog was deleted
`[repo] firmware/README.md` "Why statelessness, specifically". The one case I
expected to be missing — that `CLR` fires on every ordinary rack power-up, not
only on fault — is stated explicitly.

**The 5 V rail split between buck A and buck B.** I expected this to be an
unnamed gap. It is named, precisely, on the page that needs it:
`[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md` —
"ADR 0005's load table has one 5 V column and the two-regulator decision needs
it split per buck. That split is not written anywhere and it is what sizes both
parts." Covered as a *statement*; still has no milestone, which is D5's shape.

**Bus +5 V on the module.** Open, named, and argued from three directions
`[repo] hardware/module/digital-and-supervision/digital-and-supervision.md`
"Still open — the bus +5 V rail". Not a gap.

**The marker pattern and the `H`…`A`-to-switch mapping.** I expected these to
have fallen between the carrier and the cluster boards during the restructure.
They were explicitly handed over: `[repo] hardware/carrier/carrier.md` "Two
items left this page with the registers", with `cluster-boards.md` §4 named as
the destination and `marker-bits` tracked in the register. Handled well.

**`R1b`'s justification.** The missing-rationale gap ("its real job … appears
nowhere in the repo") was found by two reviewers and is now written down on the
page that owns both ends `[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md`.
The *requirement* it is measured against is still unowned — that is B2, a
narrower finding than I started with.

**Which port of the MPXV4006DP is P1; the etherCON variant; the dev board's
matrix face.** All three are layout-blocking, all three are named in
`carrier.md`'s Still open list with what they block `[repo]`. Named gaps, not
invisible ones.

**`hardware/unplaced.csv` as a dumping ground.** CLAUDE.md warns that it should
be "a count of parts nobody has drawn, not a dumping ground". It has drifted —
`C-TIMER-LOADSW` and `C-GATE-LOADSW` sit there while `power-entry.md` derives
their values and owns the corresponding register entries `[repo] config/figures.yaml`
`loadswitch-timer`, `loadswitch-gate-cap`; the same is true of `R-GAIN-INAMP`,
`U-DAC`, `U-DIFFRX` and others. **But this is known and recorded**:
`[repo] hardware/module/module.md` — "`hardware/unplaced.csv` holds this board's
principal ICs — the DAC, the in-amp, the LM317 — because BOM assignment matched
on reference designator and these are drawn by part number. Known, recorded, not
yet fixed." Not a gap; a named debt.

**Whether a `circuit.yaml` edge graph hides missing circuits.** I checked whether
any BOM refdes or `circuit:` edge resolves to nothing. The tooling already
guarantees this: `[repo] hardware/module/power-entry/circuit.yaml` header —
"every edge RESOLVES. A refdes names a BOM row that exists, a fig names a
register entry, a circuit names a declared id", enforced by
`check-staleness.py`. The honest caveat is in the same header — edges were
seeded from co-mention and "correctness of the edge itself is a reader's job and
has not been done" — but that is a *verification* debt, stated, not a gap.

---

## Part 4 — One structural observation

Three of the findings above (B1, B3, A5) are the same shape: **a quantity
derived inside a page, restated in two or three other pages, and never entered
in the register.** `config/figures.yaml`'s own escape notes record this
happening twice before — `breath-zero-ref` ("an untracked quantity derived from
a tracked one has no protection at all") and `key-scan-current` ("the derivation
live in two files in full, with none of its five numbers in this register").

Both were caught by a human reading, after the divergence had already happened.
Nothing detects the *condition* — a number appearing in three corpus files and
in no register entry — although that condition is mechanically detectable from
the files the checker already reads.

That is not a finding about any one number. It is the observation that the
register protects what it knows about, and the only thing that decides what it
knows about is somebody noticing. This slice exists because of that, and so does
the next one.
