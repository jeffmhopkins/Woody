# S3 — The carrier: what it has to contain, and what the module assumes about it

**Subject:** `hardware/controller/`, which was empty when this review started.
The module has five drawn pages; the instrument end has none. This document is
the gap list that had to exist before `carrier.md` could be drafted, and
`hardware/controller/carrier.md` is the draft that came out of it.

**Method.** Read `0001`, `0003`, `0005`, `0007`, `0008`, `0009`, `0013`, `0014`,
`0004`'s umbilical sections, `config/key-layout.yaml`, `firmware/README.md`, the
five pages in `hardware/module/`, the `controller` rows of `hardware/bom.csv`,
`R10-keyscan-and-adc.md` and `D2-missing-testability.md`. Two dev-board facts
were checked against open board-definition files on GitHub rather than against
vendor pages, which the proxy still blocks.

## Evidence marking, and a warning about it

Every claim below is marked `[repo]` (with the file), `[calc]` (arithmetic
shown), `[board-def]` (an open-source board definition file, named and fetched
in this session), or `[from memory]` (a datasheet number I could not open —
treat as hearsay and check before committing copper).

This project has twice found its own honesty markers calibrated backwards, so
one explicit statement about direction: **`[from memory]` here means I could not
verify it and you should not build on it.** Where a `[from memory]` number is
load-bearing for a finding, the finding says so and says what changes if the
number is wrong. Where I believe something but cannot support it, I have written
"I think" rather than marking it.

## What could not be verified, and therefore is not asserted

- **No vendor datasheet was opened.** `waveshare.com` returns `403` through the
  proxy; `ti.com`, `nxp.com`, `analog.com`, `neutrik.com` were reported blocked
  by the prior-art wave and I did not retry them. Every MCP3202, WS2815,
  MPXV4006DP and R-78E5.0 number below is `[from memory]` or `[repo]`.
- **The Waveshare ESP32-S3-Matrix's physical dimensions are not known to me.**
  Not the outline, not the header row spacing, not which face carries the LEDs.
  Three findings below depend on those numbers and are written as "this needs
  measuring at E1", not as "this fails".
- **Whether `EN` and `IO0` appear on the ESP32-S3-Matrix's headers** is
  inferred, not observed. The inference is strong and the consequence is the
  worst on this page, so it is finding C0-1 and it is a measurement, not a
  conclusion.

---

# Part 1 — The headline

## The carrier described in ADR 0013 is not the carrier the rest of the repo needs

ADR 0013's "Build approach: dev boards as modules on a passive carrier" says the
carrier holds "**headers the dev boards plug into**" and "**two** R-78E5.0
regulator modules — **one per dev board**" `[repo] 0013`. `hardware/bom.csv`
follows it: `HDR-DEV` qty 6, "2 strips for the ESP32-S3-Matrix, 2 for the
T-Display-S3 AMOLED, 2 spare" `[repo] bom.csv`.

**The display board is not on this board and cannot be.** ADR 0013's own zone
table puts it in the Top zone; ADR 0008 says it "must mount lengthwise", needs
"60 mm of body length" and gets its own 60 mm display band at the top of the
instrument; ADR 0013's run table gives the distance from the tail as **360 mm**
`[repo] 0008, 0013`.

So the carrier has **one** dev-board socket pair, not two, and the second
regulator — if it stays on the carrier — feeds a board 360 mm away. Three things
follow and none of them are written down anywhere:

- `HDR-DEV` is over-counted and the carrier's dev-board keepout is one board's,
  not two.
- ADR 0013's justification for the second regulator is that the display board's
  "WiFi bursts are absorbed locally rather than reaching the analog section"
  `[repo] 0013`. A regulator at the tail with its bulk capacitance 360 mm away
  does not do that. Either the R-78E5.0 moves to the display board and +12 V
  goes up the loom, or `C-BULK-DISP` (already in the BOM as `open`) is what
  actually does the job and the regulator's location is arbitrary. **That is a
  live decision that changes the carrier, and nothing in the repo takes it.**
- The display loom is not "four broken-out pins — a UART pair and power"
  `[repo] 0013`. See C0-4.

**Everything downstream in this review assumes: one dev board on the carrier,
the ESP32-S3-Matrix.** If that is wrong, stop and fix ADR 0013 first, because
the board outline depends on it.

---

# Part 2 — Findings, ranked by retrofittability

The ranking is the one ADR 0001 uses: what can be fixed on the bench, what needs
a board spin before M8, and what is gone the moment the body is bonded.

**Class 0** — unretrofittable. Wrong at E13 or M8 means wrong forever.
**Class 1** — a carrier spin. The roadmap says the carrier "*will* spin at least
once" `[repo] ROADMAP.md`, so this is expensive, not fatal.
**Class 2** — documents, BOM and firmware. Free to fix, but each one is a live
trap for whoever lays the board out.

---

## Class 0 — gone when the body bonds

### C0-1. The recovery path may not be wireable. This is the worst finding here.

ADR 0009 specifies "a screwed service cover on the tail underside … over a
ten-pin header on the carrier: `EN`, `IO0`, `U0TXD`, `U0RXD`, `GND` for each
board", and calls it "the only opening in the instrument that exists for a
failure" `[repo] 0009`. `firmware/README.md` repeats the requirement and adds
"Exercise it at M8, before the body closes" `[repo]`. `HDR-SERVICE` is in the
BOM as `candidate`, marked `UNRETROFITTABLE` `[repo] bom.csv`.

**The ESP32-S3-Matrix's headers appear not to carry `EN` or `IO0`.**
CircuitPython's board definition enumerates both header columns completely
`[board-def]
adafruit/circuitpython:ports/espressif/boards/waveshare_esp32_s3_matrix/pins.c`:

```
left  column (top→bottom): 5V, GND, 3V3, IO7, IO6, IO5, IO4, IO3, IO2, IO1
right column (bottom→top): IO33 … IO40, IO43, IO44
```

Twenty pins. No `EN`, no `IO0`, no `RST`. Zephyr's devicetree for the same board
puts the BOOT button on `gpio0 0` — i.e. GPIO0 is a button on the board, not a
pin on the header `[board-def]
zephyrproject-rtos/zephyr:boards/waveshare/esp32s3_matrix/esp32s3_matrix_esp32s3_procpu.dts`.

Two caveats, stated plainly. `pins.c` lists MCU GPIOs, so a non-GPIO `EN` pad
could exist and not appear there. And these files describe the board revision
their authors had. **So this is a measurement for E1, not a verdict.** But the
enumeration is a *complete* description of both columns including the three
power pins, which is what makes the inference strong.

**If it holds, the carrier cannot route `EN` and `IO0` and ADR 0009's recovery
path does not exist.** The options, none of which is currently decided:

| | Cost |
|---|---|
| Flying leads from the dev board's BOOT/RESET button pads to `HDR-SERVICE` | Soldering to a board the BOM deliberately socketed (`HDR-DEV`: "SOCKETS not solder-down — a dead dev board in a bonded body is otherwise terminal") — the two provisions fight |
| Rely on USB-Serial-JTAG only, keeping `firmware/README.md`'s "USB MIDI is opt-in" rule as the *sole* defence | Works until one image claims OTG and does not give it back. That is the exact failure ADR 0009 bought the header against |
| Rely on OTA rollback only | Covers a bad image; does not cover a corrupted app partition or a bad NVS |
| Expose the dev board's own BOOT/RESET buttons through the tail underside | A second opening in the body, and the board must be positioned against it |

The display board's half of the header is a different problem: its pins exist
(28-pin breakout, 18 GPIO plus 3V3/GND/VBUS `[repo] 0008`), but they are
**360 mm away** — see C0-4.

**Do this at E1**, which already happens before the carrier is laid out
`[repo] ROADMAP.md E1`: put a meter on every header pin of both boards, and
write the result into ADR 0007's pin-assignment section. It costs five minutes
and it is the difference between a recoverable instrument and a sealed one.

### C0-2. The ~22 mm matrix cutout and the dev-board headers want the same board width

ADR 0009 and ADR 0014 both require "a matching cutout in the carrier PCB",
"roughly 22 mm square", "because the board's LED face points at the carrier and
the light has to pass through it" `[repo] 0009, 0014`.

**Arithmetic, on assumptions that are stated because I do not have the board.**
`[calc]` from `[from memory]` inputs:

```
8x8 matrix, 2.6 mm pitch (ADR 0014's own figure, [repo]) → 20.8 mm of emitters
Header: 10 pins at 2.54 mm = 22.86 mm of pins
      → minimum board length in the header direction ≈ 25.4 mm
      → the two header rows sit on opposite edges of a board that must be
        ≥ ~22 mm across to hold a 20.8 mm matrix between them
Row-to-row spacing therefore ≈ 22–25 mm, call it 23.5 mm
Usable slot between the rows on the carrier:
      23.5 − 2 × (0.8 mm pad radius + 0.5 mm clearance) = 20.9 mm
```

**So the largest hole that fits between the header rows is about 21 mm, against
a 22 mm requirement, with no margin and on a guessed row spacing.** And a 2-layer
carrier with a 21 mm hole between its two header rows has two ~1 mm strips of
copper carrying twenty pins, joined only around the ends of the slot. Every
signal from the dev board has to route around those ends. That is not a
comfortable board; it may not be a routable one.

**There is a fallback and it is better than the baseline.** ADR 0009 and ADR
0014 both name it: "the board moves to the carrier's underside" `[repo]`. If the
dev board hangs below the carrier with its LED face pointing *away* from the
carrier and straight at the oak window, **there is no cutout at all** — no hole,
no routing detour, no mechanical weak point, and the diffuser gets closer to the
LEDs, which ADR 0014 wants anyway ("thin, and close to the LEDs").

Whether that works depends on one fact nobody has: **which face of the dev board
carries the matrix relative to the header rows.** ADR 0009 says "Confirm on
arrival" `[repo]`. That confirmation is now a gate on the board outline, not a
detail.

**Recommendation:** treat underside mounting as the default and the cutout as
the fallback, not the other way round. Draw the cutout in the CAD anyway so the
oak window position is fixed either way.

### C0-3. "~23 conductors" is the wrong number, everywhere, by about 2×

Five documents carry the figure. ADR 0001's comparison table: "Conductors down
the body: **~23** (18 switches + grounds + spares)". `WIRE-LOOM`: "~23 conductors
in total plus the LED and UART runs". ROADMAP's checklist: "Do 23 conductors fit
the side channel?" `[repo] 0001, bom.csv, ROADMAP.md`.

**The count, built from the repo's own rules** `[calc]`:

| | Conductors | Source |
|---|---|---|
| Fitted switches | 18 | `key-layout.yaml` `counts.total` |
| Reserved spare-switch positions | **3** | `key-layout.yaml` `spare_bits_switches`, "cutouts required at M3 even if fitted later" — the wire has to be there before the body bonds |
| Grounds, one per four signals, per ribbon | **6** | ADR 0001 item 1, applied to 6/5/4/3-signal ribbons + the spares |
| Two spare conductors per loom × 4 looms | **8** | ADR 0009, "Run two spare conductors in every internal loom" |
| **Key looms subtotal** | **35** | |
| WS2815 strips: 12 V, GND, DI per strip | 6 | ADR 0014 |
| …plus `BI` per strip, if needed | +2 | see C0-7 |
| Display loom | 9–11 | see C0-4 |
| Aluminium plate bond to `PWR_GND` | 1 | `MECH-GNDBOND` |
| **Total terminating on the carrier, excluding the umbilical** | **~53** | |
| Umbilical | 8 | ADR 0004 |

**The good news, since the prompt asked whether this can be terminated on the
board: yes, comfortably.** `[calc]` As four IDC boxed headers matching the
ribbons ADR 0001 already specifies — 2×6, 2×5, 2×4, 2×4 — the key looms occupy
roughly 4 × 100 mm² including keepout, against a ~4500 mm² board. Termination
area is not the constraint; single-row 2.54 mm headers would be (53 × 2.54 =
135 mm of board edge, which a 100 × 45 mm outline does not have to spare), and
ribbon-with-alternating-grounds is what ADR 0001 specifies anyway.

**The bad news is where they go, not where they land.** `[calc]` The instrument
is 57 mm wide with 4 mm acrylic sides `[repo] 0009` → **49 mm internal**.
`PCB-CARRIER` is "~100 × 45 mm" `[repo] bom.csv`. That leaves **2 mm each side**
for two side channels that ADR 0009 and ADR 0014 jointly require to carry two
WS2815 strips (~10 mm wide each `[from memory]`), four ribbons, and the 400 mm
breath tube `[repo] 0003`. Two millimetres is not a channel.

The carrier is 100 mm long against a 40 mm tail allocation in ADR 0009's length
budget, so it extends ~40 mm up into the right-hand key run, where the centreline
is switch bodies and the sides are the only free volume. **A 45 mm-wide carrier
and open side channels are mutually exclusive over that length.**

This is the M4 item the ROADMAP already flags, with a corrected number and a
second dimension. It is on this page because the *board outline* is the variable,
and the board outline is being drawn now.

### C0-4. The display loom is 9–11 conductors, not 4

ADR 0013: the display board "needs **four broken-out pins** — UART pair and
power — instead of ten" `[repo] 0013`. That is true of the *board's* pin
requirement and false of the *loom's* conductor requirement, and the difference
is ADR 0009's service header.

`[calc]` from `[repo] 0013, 0009, firmware/README.md`:

```
+5 V (or +12 V, see the headline)          1
GND                                         1
UART1 TX, UART1 RX                          2
EN, IO0, U0TXD, U0RXD  (service header)     4
GND for the service half                    1   (or shared, → 0)
two spare conductors (ADR 0009)             2
                                          ----
                                          10–11 over 360 mm
```

Ten conductors over 360 mm, sharing a side channel with an 800 kHz WS2815 data
line and its 12 V power — carrying, among other things, **two asynchronous
reset-class signals (`EN`, `IO0`) that are level-sensitive and have no
filtering**. A glitch on `EN` resets the display board mid-performance; a glitch
on `IO0` at the wrong moment puts it into download mode on the next reset.

Neither is currently specified to have a pull-up, a series resistor or a filter
at the carrier end. **They need all three**, and the right place for them is the
carrier, which is why this is on this page. A 10 kΩ pull-up and a 100 Ω/10 nF
network per line is the same part set as `R-KEY-PU`/`R-KEY-SER`/`C-KEY` and
costs six passives.

*(`EN` with 10 nF on it will slow the reset edge; 10 kΩ × 10 nF = 100 µs, which
is fine for a reset line and is what an RC reset circuit looks like anyway.
`IO0` is sampled only at reset, so filtering it is free.)*

### C0-5. What `AGND` does at the instrument end has never been drawn

ADR 0003 spends pages on `AGND` at the module and one sentence on it here:

> "The star point is the analog ground pour on the **bottom cluster board**, at
> the sensor and reference, immediately adjacent to the umbilical connector."
> `[repo] 0003`

There is no bottom cluster board — ADR 0001 says the clusters are "switches, and
nothing else" `[repo] 0001`. `hardware/module/breath-receive-stage.md` labels the
same node "INSTRUMENT (bottom cluster board)" `[repo]`. Both mean the carrier.

The real question the naming hides: **does the analog section's supply return go
home on `AGND` or on `PWR_GND`?** ADR 0004's rule is "`AGND` carries no power
current" `[repo] 0004`; ADR 0003's star-point sentence says the sensor's and the
reference's ground pour *is* `AGND`, which would put their return current on it.

`[calc]`, using ADR 0003's own cable figure (0.168 Ω for 2 m of 24 AWG, which
its 8.4 µV / 50 µA row implies):

```
Analog section from +12 V:  REF5050 ~1 mA + OPA2197 2 × ~1 mA + sensor 10 mA
                          = ~13 mA
If that returns on AGND:   13 mA × 0.168 Ω = 2.2 mV of offset on the sense pair
At the in-amp's G = 2.185: 4.8 mV at the breath jack = 0.048 % of 10 V
```

**So either choice is electrically survivable**, because the 13 mA is
DC-constant (the sensor's supply current does not modulate with pressure
`[from memory]`) and `TRIM-BREATH-ZERO` nulls a constant offset at commissioning
`[repo] breath-receive-stage.md`. The right answer is still `PWR_GND`, because
it costs nothing and it keeps the rule true rather than approximately true.

**What is not survivable is leaving it undrawn.** This is one copper decision on
a board that is made once, and the two ADRs that touch it point in opposite
directions. The draft page takes a position; it needs ADR sign-off.

### C0-6. `SCLK` and `CS` have no series element at the driving end, and the driving end is this board

`D1-missing-protection.md` finding 10: "Series current limiting on `SCLK` and
`CS` at the driving end — **ADD**" `[repo]`. The BOM has `R-MOSI-SER` at 220 Ω,
qty **1**, and nothing on `SCLK` or `CS` `[repo] bom.csv`. The fix was accepted
and did not land.

ADR 0004 calls `SCLK` "the fastest edge in the system" `[repo] 0004` and sends it
down 2 m of ~100 Ω twisted pair into a single 74AHCT125 input with a 10 kΩ pull.
That is an unterminated transmission line driven by a 3.3 V CMOS output with a
few-nanosecond edge. `R10` records that reflection-induced double-clocking is set
by edge rate and is not helped by slowing the clock `[repo] R10 A8`.

`R-MOSI-SER`'s own note gives the sizing rule and the reasoning applies
identically: 220 Ω into ~200 pF is a 7.9 MHz corner, "closer to a real source
match on Cat5's ~100 Ω" at 100 Ω `[repo] bom.csv, 0004`. **Fit the same resistor
on `SCLK` and on `CS`.** Two 0805s. Unretrofittable in the sense that matters:
the board is inside the body and the cable is 2 m long.

*(`CS`'s case is weaker than `SCLK`'s — it moves once per frame — but ADR 0004's
own analysis says a stray `CS` edge re-frames a 32-bit DAC word into the software
reset and clear-code registers, which is a sticky failure `[repo]
digital-and-supervision.md`. That is the expensive edge, not the frequent one.)*

### C0-7. The WS2815's backup data line is celebrated and never wired

ADR 0014 chooses the WS2815 partly for its "**Backup data line.** … a single
failed LED does not kill everything downstream of it. In a bonded laminated body
… that matters more than it would in a serviceable build" `[repo] 0014`.

`[from memory]`, and this is the load-bearing uncertainty: on a WS2815 strip the
backup path works by each pixel's `BI` taking the *previous-but-one* pixel's
output, which leaves the first pixels of the strip with nothing to take. Strips
therefore bring out **four** wires at the head — 12 V, GND, `DI`, `BI` — and both
data pads must be driven from the same source for the redundancy to cover the
head of the run.

If that is right, then per strip the carrier owes **two** level-shifted outputs,
not one:

| | Documented | Needed |
|---|---|---|
| 74AHCT125 gates | 2 used, "Two spare gates" `[repo] bom.csv` | **4 used, none spare** |
| Loom conductors for LEDs | 6 | **8** |

**If it is wrong, nothing changes.** Check it against the WS2815 datasheet or
against the pads on the actual reel — this is a five-minute check on a part that
is already `candidate` in the BOM, and it decides how many gates and how many
wires leave this board.

### C0-8. Nothing holds the LED data lines low while the MCU is in reset

ADR 0014's defence against latched strips is a firmware rule: "**Blank both
strips *and the matrix* as the first act at boot**, before anything else
initialises" `[repo] 0014`. That is correct and it is not sufficient, because it
cannot run during the window it most matters.

The mechanism `[calc]` + `[from memory]`:

- On ESP32-S3 reset, GPIO1 and GPIO2 are inputs, high-impedance, for the whole
  bootloader window — of order 100–300 ms.
- The 74AHCT125's `OE` pins are tied low (there is no GPIO for them, and none is
  wanted), so the buffer is **enabled** the whole time.
- An AHCT input floating near its ~1.5 V threshold does not sit still. It
  oscillates, or it follows whatever couples onto a 3.3 V trace next to a 12 V
  LED supply, and the buffer faithfully squares that up into a clean 5 V edge
  and sends it to 25 addressable LEDs on a 12 V rail.

The WS281x protocol has no framing beyond a reset gap, so random edges are
random pixel data. **A brownout-reset instrument therefore goes to a random
colour field, which is the state ADR 0014's thermal clamp exists to prevent, at
the moment no firmware is running to clamp it.**

**Fix: a 10 kΩ pull-down on each 74AHCT125 input**, on the carrier, at the
buffer. Two 0805s, and they cannot be added later. `R-SPI-PULL` on the module
page is the same idea for the same reason and has six of them `[repo]
digital-and-supervision.md` — the instrument end has none.

### C0-9. The sensor socket, the clearable trap and the 12 × 40 mm service cover do not meet

Three requirements, each reasonable, that have never been drawn together:

- **ADR 0003:** the MPXV4006DP is a wear part, "socketed or otherwise
  replaceable", "buy two" `[repo] 0003`. `SKT-BREATH` is in the BOM.
- **ADR 0003 and ADR 0009:** the dead-volume trap must be "clearable without
  disassembly", "reachable from the tail face" `[repo] 0003, 0009`.
- **ADR 0009:** the only opening on the tail underside is a screwed cover
  "roughly 12 × 40 mm" over the service header `[repo] 0009`.

`SKT-BREATH`'s own note already spots half of it: "The spare is only reachable if
the first part comes out, and the body is bonded" `[repo] bom.csv`. A 12 × 40 mm
slot over a 2×5 header does not let you reach a socketed 1351-01, unplug a
400 mm tube, and clear a trap.

**Either the service cover becomes a real tail-underside hatch** — sized to
reach the sensor, the trap and the header, with the sensor and trap positioned
under it — **or the socket is decoration** and should be deleted in favour of
soldering the part in and relying on the second one for a rebuild.

Four more things fall out of that choice, all of which constrain the carrier
layout and none of which is written:

- **Which port is P1 is still open** — ADR 0003 says "Confirm which port is P1
  before layout" `[repo]`. Layout is now.
- **Both ports are on the same side** (case 1351-01 `[repo] 0003`), so the tube
  barb and the open reference barb are adjacent. The tube's routing must not
  cover, kink or blow adhesive across the reference port, whose blockage is the
  failure ADR 0003 describes as "reads correctly from cold and fails after ten
  minutes of playing" `[repo]`.
- **A socketed part with a 400 mm tube on it is a lever.** Nothing retains it.
- **`MECH-COAT` must mask both ports** `[repo] bom.csv, 0009` — which is easier
  if the sensor is under a hatch and harder if it is buried.

### C0-10. The umbilical's termination on this board is an open decision

ADR 0004's open list: "**Which etherCON variant at each end.** Feedthrough
(NE8FDP-class) presents a plain RJ45 on the back, so the instrument end could
take a short patch lead to a jack on the carrier instead of eight soldered wires
inside a body that cannot be reopened … **Decide with the datasheets in hand at
E12 and M7**" `[repo] 0004`.

That decision changes this board:

| | On the carrier |
|---|---|
| Feedthrough + patch lead | An RJ45 jack footprint, ~16 × 14 mm plus keepout, which is **not in the BOM**, plus the height of a vertical jack in a ~20 mm cavity |
| Solder-tag or PCB-mount etherCON | Eight wires or eight pads at a defined position relative to the tail face |

And ADR 0013's carrier list says the carrier holds "the umbilical connector"
`[repo] 0013`, while ADR 0009 says the etherCON mounts "to an internal backing
plate — aluminium or ply, tied into the same stack that carries the keys"
`[repo] 0009`. Those are different boards. The second one is right, for the
reason ADR 0009 gives (3.5 mm of oak above and below a 26 × 31 mm flange is not
structure); the carrier gets wires, not a flange.

**E12/M7 is after E13.** The carrier is drawn before the decision is taken. Pull
it forward or draw both footprints.

### C0-11. No test point, shunt link or instrumentation header exists anywhere

`D2-missing-testability.md` asked for them on the carrier specifically — supply
test points, current-measurement shunt links, a logic-analyser header with
alternating grounds, breath-path taps, loom connectors rather than soldered
wires `[repo] D2`. `hardware/bom.csv` contains no row matching `test point`,
`TP-`, `shunt link`, or `0R link` `[verified by grep]`.

E14 is "E1–E11 re-run on the carrier, not on dev boards", and M8 requires a
thermal soak, a failure-injection pass and a service-header recovery `[repo]
ROADMAP.md`. None of those has a documented physical means of measurement.

These are individually trivial and collectively the difference between debugging
the instrument and guessing at it. They are Class 0 because the board is made
once.

---

## Class 1 — a carrier spin

### C1-1. The MCP3202's maximum clock and SPI2's 2 MHz

**This was found by R10 on 2026-09-21 and has not been applied to any ADR or BOM
row** `[repo] R10 B-3`. Restated because it is a carrier fact and the carrier is
being drawn.

`[from memory]`, via R10's search-summary tier: MCP3202 is specified at **100
ksps at V_DD = 5 V and 50 ksps at V_DD = 2.7 V**; a 12-bit conversion takes 18
clocks. `[calc]`:

```
100 ksps × 18 = 1.8 MHz at 5.0 V
 50 ksps × 18 = 0.9 MHz at 2.7 V
3.3 V is not specified → design to 0.9 MHz
```

ADR 0003, ADR 0004, `latency-budget.md` and `power-entry.md` all specify **SPI2
at 2 MHz** `[repo]`, and ADR 0004 says 2 MHz "leaves room for the MCP3202
sharing the host" `[repo] 0004`. **2 MHz over-clocks the converter by more than
2×.**

**This is a firmware line, not a redesign** — ESP-IDF's SPI master sets
`clock_speed_hz` per device on a shared host, so the DAC gets 2 MHz and the ADC
gets 900 kHz on the same bus. It is Class 1 rather than Class 2 only because
"the ADC and the DAC run at different clocks on one host" is a constraint the
board's decoupling, its `SCLK` routing and its test provisions should be drawn
knowing, and because if it turns out to be wrong the answer is a different part.

**The loop budget still closes** `[calc]`, and it is worth recording because ADR
0004's version of this sum omitted the ADC:

```
SPI2  DAC   6 × 32 bits  @ 2.0 MHz = 96.0 µs
SPI2  ADC   24 clocks    @ 0.9 MHz = 26.7 µs
SPI2  total                        = 122.7 µs  of a 250 µs period → 49 %
SPI3  keys  32 bits      @ 1.0 MHz = 32.0 µs   concurrent, different host → 13 %
```

### C1-2. The ADC's reference is its supply, and its supply is unfiltered and unbudgeted

The MCP3202 has no `VREF` pin; `VDD` is the reference `[repo] R10 B4, bom.csv`.
`VDD` here is the dev board's own 3.3 V LDO, reached through a header pin.
So **the digital breath copy's scale factor is 1 / V_LDO** — a rail with no
tolerance stated anywhere in the repo.

Three consequences, in descending order of how much they matter:

**Aliasing on the reference, which is the mechanism ADR 0003 calls a showstopper
on the signal.** R10 found it `[repo] R10 B-3`: for a VDD-referenced SAR, `VREF`
sits in the transfer function identically, and has no anti-alias filter at all.
The repo's own `C-STRIP-BULK` note puts the WS2815 PWM rate at **~2 kHz**
`[repo] bom.csv` — exactly Nyquist for a 4 kHz sampler. **The fix is a
capacitor**: `C-DECOUPLE-CARRIER` gives the MCP3202 one 100 nF and nothing else.
Add bulk — 10 µF — at that pin and treat it as an analog reference, not a logic
supply.

**Gain error from the LDO.** `[from memory]` typical initial accuracy ±1–2 % and
load regulation of order 0.1–0.5 % per 100 mA. Only gain survives, because the
zero is auto-tracked in firmware and the span is set by a panel knob `[repo]
0003, 0006`, so this does not matter. R10 reached the same conclusion
independently.

**Load steps from the key pull-ups, which is a new one.** `[calc]` The 21
pull-ups hang on the same 3.3 V rail: 3.3 V / (10 kΩ + 100 Ω) = **327 µA per
closed key**, so an 18-key chord is a **5.9 mA** step on the ADC's reference. At
an LDO load regulation of 0.3 % per 100 mA that is 0.018 % — **0.7 LSB at 12
bits**. Checked, and it is fine. Recorded because it is the kind of coupling that
gets discovered as "the breath reading moves when I press keys" and blamed on
firmware for a year.

### C1-3. Both SPI hosts are allocated, and the vendor's own configuration drives the matrix from one of them

ADR 0007 records that "the matrix is 64 WS2812C parts on GPIO14, chained, driven
over **SPI2** in Zephyr's configuration" `[repo] 0007`. Confirmed at source: the
board's pinctrl node is `spim2_ws2812_led` with `pinmux = <SPIM2_MOSI_GPIO14>`
`[board-def] zephyr:.../esp32s3_matrix-pinctrl.dtsi`.

SPI2 is the DAC and ADC bus; SPI3 is the key chain `[repo] 0001`. **There is no
third SPI host.** So all three WS281x outputs — the matrix on GPIO14 and the two
strips on GPIO1/2 — have to come from RMT (or the parallel LCD peripheral).

`[from memory]` the ESP32-S3 has four RMT TX channels, so three fits. But it is
a hard architectural constraint that appears in no ADR and in no firmware note,
and the consequence of getting it wrong is a WS2812 driver sharing a bus with the
breath converter and the pitch DAC. R10 flagged the same thing `[repo] R10 B-3`.

**Not a carrier change**, but it belongs in the carrier page because GPIO1 and
GPIO2 are carrier nets and their driver choice is now constrained.

### C1-4. One inductor, two bucks

`L-BUCK-IN` qty **1**, "LC between the umbilical node and the buck input".
`C-BUCK-IN` qty **2**, "One per buck" `[repo] bom.csv`. Those two rows describe
different topologies. Either there is one LC feeding a common 12 V node that both
bucks hang on (then the second 100 µF is local bulk, not part of an LC), or there
are two LCs and the inductor count is wrong.

**The LC is stable either way** `[calc]`, which is worth recording because
`power-entry.md` lists "Damping the input LC" as still open:

```
L = 22 µH (mid of the 10–47 µH range), C = 100 µF
f0 = 1/(2π√LC)   = 3.39 kHz
Z0 = √(L/C)      = 0.469 Ω
ESR of a 100 µF/25 V radial ≈ 0.5–1 Ω [from memory] → Q ≈ 0.5–0.9, no peaking

Negative resistance of the constant-power load at typical play:
  5 V branch 226 mA × 5 V = 1.13 W out, /0.90 = 1.26 W in at 11.4 V
  R_neg = −V²/P = −103 Ω
Middlebrook margin: 103 Ω / 0.47 Ω ≈ 220× (47 dB)
```

And the cable itself is its own damping: 2 m of 24 AWG is 0.34 Ω round trip
against a Z0 of about 0.02 Ω into 2.2 mF `[calc]`, i.e. hugely overdamped.

**So the instrument end of `power-entry.md`'s open item looks closed**, provided
the bulk capacitors are real electrolytics with real ESR and not low-ESR
ceramics. If someone substitutes ceramics for `C-BUCK-IN`, Q goes up and this
paragraph stops being true. Note it on the row.

### C1-5. "Neither is near its rating" is not supported by the table above it

ADR 0005, justifying two bucks: "Split, the real-time side carries the matrix and
the display side carries its own transients, and **neither is near its rating**"
`[repo] 0005`.

`[calc]` from ADR 0005's own load table and ADR 0014's matrix figures:

```
Clamp-legal worst on the 5 V rail, total                     928 mA  [repo] 0005
Of which the display board is roughly                    ~150–250 mA  [estimated]
Buck A therefore carries                                  ~680–780 mA
Buck A is an R-78E5.0-1.0                                    1000 mA
                                                          → 68–78 %
```

Seventy-odd percent of a 1 A switching module, inside a sealed body running
10–20 K above ambient `[repo] 0014`, is not "not near its rating". It is probably
fine — the part derates from around 60 °C `[from memory]` — but the sentence is
doing reassurance that its own numbers do not support.

**The deeper gap: ADR 0005's load table has one 5 V column and the two-regulator
decision needs it split.** Nobody has written how much load lands on buck A and
how much on buck B. That split is what sizes both parts, and it is the only
reason the second regulator exists.

### C1-6. The USB-OR cannot be built the way the BOM describes it

`D-USBOR`, qty 2: "ORs USB VBUS with the umbilical-derived 5 V rail for bench
use. **One diode per source into the shared 5V node.** Both sources drop ~0.3 V,
leaving ~4.7 V at the dev boards' 5V pins" `[repo] bom.csv`.

The problem is that the "shared 5 V node" **is a dev-board pin**. USB VBUS
arrives inside the dev board, at its own USB-C receptacle; the carrier has no
access to it except through that same `5V` header pin. You cannot put a diode
between a node and itself.

The topology that does work is one diode per **regulator output**:

```
R-78E5.0 A ──▷|── dev board "5V" pin ◄── (VBUS, inside the board)
R-78E5.0 B ──▷|── display board "5V" pin
```

That is still two diodes, so the BOM quantity survives; the note does not, and
neither does the voltage arithmetic. `[calc]` A 5.00 V regulator behind a
Schottky presents ~4.7 V while VBUS presents ~5.0 V, so **whenever USB is
plugged in, the USB port supplies the whole board** — including the 8×8 matrix,
which ADR 0014 puts at up to 960 mA at full field `[repo] 0014`. A laptop port
will not enjoy that.

**Two things to check at E1, both meter work:** whether the `5V` header pin is
connected to VBUS at all (the board has a battery charger `[board-def]
zephyr:.../doc/index.rst`, which may mean a power-path IC rather than a plain
tie), and what the drop is if there is one. **And decide whether bench USB power
is allowed to run the matrix**, because at 4.7 V vs 5.0 V it is not a fallback,
it is the primary source.

### C1-7 through C1-9, briefly

- **C1-7. No series resistor on the 74AHCT125's outputs.** Each drives ~420 mm
  of wire to a strip. The module's equivalent has `R-MOSI-SER`; the instrument's
  has nothing. 100–330 Ω per output, at the buffer. Two more 0805s, and they are
  the same class of part as C0-6.
- **C1-8. `C-REF-OUT` is qty 2 for one REF5050**, described as "output
  capacitor" `[repo] bom.csv`. Either two in parallel or one in and one out — say
  which. The REF5050's stability depends on the output capacitance being in the
  range its datasheet specifies, which nobody has been able to open.
- **C1-9. The 100 × 45 mm outline has no slack.** `[calc]` A rough area budget:
  4 × SOIC-16 ≈ 400 mm²; 63 key passives at 0805 with hand-assembly spacing and
  routing ≈ 1000–1300 mm²; four small ICs ≈ 250 mm²; two R-78E5.0 SIP-3 ≈
  200 mm²; bulk electrolytics and the inductor ≈ 300 mm²; loom and service
  connectors ≈ 500–900 mm²; protection and decoupling ≈ 150 mm². That is
  **2800–3500 mm² against 4500 mm², minus a ~26 × 26 mm dev-board keepout
  (676 mm²)** — so roughly 3824 mm² usable and 2800–3500 mm² claimed, before any
  allowance for routing channels around a hole in the middle of a 2-layer board.
  It fits. It does not fit comfortably, and C0-3 says the 45 mm width is the
  wrong dimension to be spending.

---

## Class 2 — documents, BOM and firmware

Each of these is free to fix and each is a trap for whoever lays out the board.

| | Says | Should say |
|---|---|---|
| `bom.csv` `U-MCU-RT` | "16 GPIO broken out (1-7, 34-40, 43, 44)" | **17** — ADR 0007 corrected this and the BOM row did not follow; GPIO33 is missing from the list `[repo] 0007`, confirmed `[board-def]` |
| ADR 0014 | "roughly 17 broken out and **12** needed on the real-time board (ADR 0007)" | 14 needed. ADR 0007's table says 14 `[repo]` |
| ADR 0014 | "The matrix shares the **1 A R-78E5.0** with both dev boards … about 1.36 A from a 1 A part" | There are two regulators (ADR 0013, ADR 0005). The conclusion survives — buck A alone is ~1.12 A at full field `[calc]` — the arithmetic does not |
| ADR 0003 | "put a **220 nF** cap at the ADC input pin … ~600 Hz corner and 58 dB at 500 kHz" | 47 nF, 564 Hz, 55 dB at 330 kHz. The BOM row `C-AA-ADC` already says so and explains why; the ADR body still argues from the superseded value `[repo]` |
| ADR 0003, `breath-receive-stage.md` | "the **bottom cluster board**" | the carrier. There is no cluster board `[repo] 0001` |
| ADR 0009 | key networks "on the **cluster boards** (ADR 0001)" | on the carrier (ADR 0001, ADR 0013). The sentence is in the "free now and impossible later" list, which is the worst place for a stale location |
| ADR 0001 | "the **five** 'free' spare bits are floating CMOS inputs" in one place, "14 spare bits" in another | Both are true and they are different sets. `key-layout.yaml` has the clean version: 14 spare = 6 marker + 3 spare-switch + 5 free `[repo]` |
| `firmware/README.md` | "Display renders on the other core, on its own SPI host" | The display is on the other **MCU** (ADR 0013). Both of this MCU's SPI hosts are spoken for — see C1-3 |
| ADR 0003 | "**Band-limit at both ends**, around 500 Hz" | Superseded by `breath-receive-stage.md`, which puts the whole filter at the receive end ahead of the in-amp. `R-SER-BREATH-INST`'s note already says so `[repo]`. **This matters to the carrier**: it means there is no capacitor on the instrument-side breath output, which is a part someone will otherwise add |
| `latency-budget.md`, ADR 0003 | ADC path is "~50–200 µs", no RC term | `C-AA-ADC` into the divider's 6 kΩ is **τ = 282 µs**, which exceeds the 250 µs loop period `[calc]`, and the note-on threshold is read through it. R10 found this `[repo] R10 B-2`. ~5.6 % of the 5 ms budget; it belongs in the table that chose 4 kHz over 8 kHz |

---

# Part 3 — Two things that were checked and are fine

Recorded because a review that only lists problems gives no information about
the things it did not list.

### The pin budget closes, with three footnotes

ADR 0007's assignment is achievable on the real board. 17 broken out
`[board-def]`, 14 assigned `[repo] 0007`, spare GPIO 3, 4, 33. Nothing the
carrier needs claims a pin that is not in the table: `CLK INH` is tied low,
`OE` on the 74AHCT125 is tied low, the marker bits are hard-wired, the IMU is
on GPIO10–13 and the matrix on GPIO14, none of which are broken out.

Three footnotes:

1. **SPI2 cannot use IO_MUX.** On the S3 the FSPI IO_MUX pins are GPIO9–14
   `[from memory]`, and the board spends 10, 11, 12, 13 on the IMU and 14 on the
   matrix `[board-def] pins.c`. SPI2 on GPIO35/36/37 therefore routes through the
   GPIO matrix, which caps it around 40 MHz rather than 80 `[from memory]`.
   **Irrelevant at 2 MHz** — recorded so nobody rediscovers it as a problem.
2. **GPIO3 is a strapping pin** (JTAG source select) `[from memory]`. It is one
   of the three "spares" ADR 0007 offers as a future analog input. Usable, but
   not a clean spare, and the ADR should say so.
3. **The spare count is three, and C0-1 may want two of them.** If `EN`/`IO0`
   cannot be wired, one of the recovery options is a GPIO-driven reset scheme —
   which is not equivalent and probably not worth it, but it is the only thing
   the spares could buy.

### The key input network does what ADR 0001 claims, by a different mechanism than it describes

ADR 0001's decisive arithmetic is "180 pC / 10 nF = 18 mV" `[repo] 0001`. The
network as the BOM describes it puts the 100 Ω **between the loom and the
capacitor** — which is what makes the press time constant 100 Ω × 10 nF and the
release time constant 10 kΩ × 10 nF, both of which ADR 0001 also claims. So the
injected charge lands on the *loom* side of the series resistor, not directly in
`C-KEY`, and it is worth checking that the conclusion survives.

It does `[calc]`:

```
Loom conductor ≈ 40 pF at 3.3 V; 180 pC injected → +4.5 V spike at the loom node
Redistribution into C-KEY through R-KEY-SER:
   τ = R × (C1·C2)/(C1+C2) = 100 Ω × (40 pF ∥ 10 nF) = 100 Ω × 39.8 pF = 4.0 ns
Final common voltage = 180 pC / 10.04 nF = 17.9 mV
```

So the loom node spikes for about twenty nanoseconds and the register input never
moves more than 18 mV. The mechanism is **charge sharing in nanoseconds**, not RC
filtering in microseconds — which matters, because it means the 10 nF has to be
at the register input *and the 100 Ω has to be short*, i.e. both at the connector
end of the carrier, not distributed. That is a layout rule nobody has written and
it is in the draft page.

Two derivations that support the other numbers in ADR 0001 `[calc]`:

```
Release: 3.3 V through 10 kΩ into 10 nF, τ = 100 µs
         to V_IH = 2.0 V:  t = −100 µs × ln(1 − 2.0/3.3) = 93.2 µs   ✓ "~93 µs"
Press:   10 nF through 100 Ω, τ = 1 µs
         to V_IL = 0.8 V:  t = −1 µs × ln(0.8/3.3) = 1.4 µs          ✓ "~1 µs"
```

---

# Part 4 — What the draft page does with all this

`hardware/controller/carrier.md` is a **first draft**, written to the same shape
as the module pages: block diagram, component table, derivations, still-open.

Where this review found a decision that has not been taken, the draft **takes a
position and labels it a proposal**, rather than either inventing a value or
leaving a hole. Specifically it proposes: `PWR_GND` for the analog supply return
with `AGND` as sense-only (C0-5); underside dev-board mounting as the default
with the cutout as fallback (C0-2); series resistors on `SCLK` and `CS` (C0-6);
pull-downs on the level shifter inputs (C0-8); and a filtered, pulled `EN`/`IO0`
pair for the display loom (C0-4).

Where this review could not establish a number, the draft says so in the row
rather than filling it in. There are more `TBD`s in that page than is
comfortable. That is the correct state for a page written on a day when no
datasheet could be opened.

## What has to happen before this page can be finished

In order, and the first two are cheap:

1. **E1, with a meter on both dev boards.** Every header pin identified; `EN`
   and `IO0` present or absent; `5V` pin to VBUS continuity and drop; which face
   carries the matrix; the board outline and header row spacing measured; idle
   current measured as the ROADMAP already requires. This closes C0-1, C0-2,
   C1-6 and part of C1-5.
2. **One session with the datasheets, from an unblocked browser.** MCP3202 clock
   versus supply; WS2815 data threshold and whether `BI` needs driving; REF5050
   output capacitance; MPXV4006DP port identification and supply current. This
   closes C1-1, C0-7, C1-8 and confirms C0-9.
3. **ADR 0013's carrier section rewritten** for one dev board, with the second
   regulator's location decided.
4. **A plan-view section at the tail** — carrier outline, LED strips, four
   ribbons, the breath tube and the U-bolt against a 49 mm internal width. This
   is the M4 item, and C0-3 says it has to come before the board outline is
   fixed, not after.
