# S2 — What is specified in prose but drawn nowhere, and what is needed but specified nowhere

**Date:** 2026-09-21
**Scope:** all fourteen ADRs, `ROADMAP.md`, `firmware/README.md`,
`config/key-layout.yaml`, `docs/reference/`, `hardware/bom.csv`, and the five
drawn pages in `hardware/module/`.
**Deliberately not read:** `docs/review/` and `docs/research/`. Everything below
was derived from the primary documents only, so anything an earlier pass already
found will appear here as a rediscovery rather than as a citation.

**Method, both directions:**

1. **Prose → circuit.** Every ADR sentence that implies a part, a net or a
   connection, checked against the BOM and against the five drawn pages.
2. **Function → circuit.** The instrument walked as a system — power in,
   sensing, scanning, processing, display, lighting, output, protection, test,
   assembly, service — asking what a working one needs that nobody has written
   down anywhere.

`hardware/controller/` is empty, so for the instrument side the *only* record of
intent is ADR prose and BOM rows. That asymmetry is why most of what follows
lands on the carrier.

**Evidence marking:** `[repo]` claims quote the sentence that implies the missing
thing. `[from memory]` claims rest on general engineering knowledge and are
weaker — they are labelled as such and none of them is in the top five.

---

## Ranked table

**Section A — unretrofittable.** Cannot be added once the body is bonded, or
once an irreversible process step has been taken. Ranked first regardless of
size, per the brief.

| # | Gap | Cost to add now | Cost to discover later |
|---|---|---|---|
| **A1** | **The display-board harness does not exist.** ADR 0013 budgets "four broken-out pins"; ADR 0009 and `firmware/README.md` independently require `EN`, `IO0`, `U0TXD`, `U0RXD`, `GND` to reach it as well. Real count is 9–11 conductors over 360 mm, and no loom carries them | Four lines in the BOM, ten crimps at M7 | The display board is the one with no external connector. A missing `IO0` or `EN` = an instrument that plays but can never be configured again, for the life of the object |
| **A2** | **No service aperture for the breath sensor or the condensation trap**, although two ADRs promise both are serviceable and a second sensor is bought as a spare | One more through-cut in the laminated layer that already holds the matrix window and the service cover; one CAD afternoon at M4 | The stated most-likely-to-fail part, and its trap, are sealed inside a bonded body. The spare sensor is unusable and the "clearable without disassembly" requirement is silently void |
| **A3** | **The WS2815 backup-data input is connected to nothing.** The backup line is cited as a *reason for the part choice* in two ADRs; the level shifter is specified with "two spare gates", which is exactly the two gates the backup lines need | Two gates already bought, two traces, zero new parts | The redundancy that justified choosing WS2815 over WS2812B does not exist. One dead LED dark-ends a 420 mm run behind bonded acrylic |
| **A4** | **No test points, probe pads or ground posts on either PCB.** Six ROADMAP items and two ADRs call for a scope, a logic analyser or a current probe on nets that exist only as traces | A dozen 1 mm pads and two ground loops; free on boards being laid out anyway | Every in-body measurement the plan books — E4's hour-long key-chain error run, M8's scoped pitch-while-LEDs-sweep — has nowhere to attach. Fly-wire probing a conformal-coated carrier inside a part-assembled instrument, or skip the measurement |
| **A5** | **Neither board has a mounting or retention scheme.** The carrier must hold four independent registrations (etherCON cutout, USB-C slot, 22 mm matrix window, 12 × 40 mm service cover) and nothing says how it is located or fixed | Four mounting holes in the DXF and on the PCB, plus standoffs in the BOM | The board is positioned by whatever it rests on. The USB-C slot, the service cover and the matrix window all miss, in a stack that is then bonded |
| **A6** | **Conformal coating has no mask list beyond the two sensor ports** — not the service header, not the dev-board sockets, not the breath-sensor socket | One sentence in the BOM note and on the assembly sheet | Coating is irreversible. Sealing the service header destroys the one recovery path ADR 0009 calls "the only thing standing between a bad flash and a finished instrument that will not boot" |
| **A7** | **`SCLK` and `CS` get no source termination while `MOSI` does**, on the same 2 m cable, with `SCLK` named in ADR 0004 as the fastest edge in the system. Both also branch to on-carrier loads | Two 0805 resistors and two footprints | If E11 says the link needs them, the carrier respins — affordable before bonding, terminal after. If E11 passes marginally, intermittent mis-framed DAC words in the finished instrument |
| **A8** | **The umbilical shield has no defined termination at either end**, and the instrument-end backing plate is "aluminium or ply — TBD", so one end may be non-conductive. Bonding it at both ends also creates a second `PWR_GND` return in parallel with the one ADR 0004's star rule requires to be alone | A decision and one solder tag | Either a useless shield or a parallel power return through the chassis — the exact mechanism ADR 0004 measures as 5.7–7.2 cents of breath-correlated pitch bend |
| **A9** | **No series resistors on the two LED data lines**, on 800 kHz edges running 420 mm in the same side channels as the key looms | Two resistors, two footprints | ADR 0014's own words: strips that work on the bench and glitch in the build — behind bonded acrylic |
| **A10** | **The loom's spare conductors are already spent.** ADR 0009 requires two spares per loom; ADR 0010 requires three future switches whose plate cutouts are mandatory. They are the same conductors, and nobody has reconciled them | Widen two ribbons by two ways each | The plate has holes for switches that can never be wired |

**Section B — retrofittable, but expensive to discover late.** Ranked by the
cost of finding out.

| # | Gap | Cost to add now | Cost to discover later |
|---|---|---|---|
| **B1** | **The module cannot be brought up standalone, because the buffer's `OE` is gated on instrument presence and there is no override.** ADR 0004's explicit claim that it can, and the ROADMAP's whole E6→E12 strategy, are both defeated by a circuit that is already drawn | A two-pin jumper, or a pad pair on the `OE` node | E7 is reached with a module, a dev board and a meter, and *nothing comes out of the DAC*. Debugging a correct circuit. Would be item #1 overall if it were not fixable with four screws |
| **B2** | **The 99 ms frame watchdog defeats every static bench measurement**, and E7's acceptance criterion is written as one ("commanded codes produce expected voltages on the meter") | One sentence in the ROADMAP, or a `CLR`-defeat pad | Same as B1, at the same milestone, from the other direction — codes are commanded and the outputs sit at zero |
| **B3** | **No bench +12 V entry on the carrier.** ADR 0005 says USB-OR "means the instrument runs on the bench without a rack attached", but the breath sensor, its reference, its buffer and the LEDs are all on +12 V and USB supplies none of it | A two-pin header, or an RJ45 breakout fixture in `tools/` | E14 re-runs E1–E11 on the carrier and needs a module in a powered rack to do any of it. The bench affordance the diode was bought for does not cover the analog front end |
| **B4** | **`C-BULK-DISP` is `TBD`/`open` while ADR 0013 makes it load-bearing**, and nobody has said which end of the 360 mm run buck B sits at, or checked the R-78E5.0's maximum output capacitance | Two decisions, one part number | A remote 5 V rail with an oversized remote cap either refuses to start or oscillates, 360 mm from its regulator, inside a bonded body |
| **B5** | **No thermal path from anything to the aluminium plate.** The README says every watt leaves through it; ADR 0014's entire lighting clamp is sized from an assumed 3 K/W with no mechanism drawn, and 6 mm of oak sits between the cavity and the plate | A thermal pad and a bracket, decided at M4 | M8's soak measures the real figure. If it is materially worse than 3 K/W, the clamp number is wrong and the only remaining lever is dimmer lighting |
| **B6** | **The etherCON variant is deferred to E12/M7, but the tail-face DXF (M4) and the carrier outline (E13) are fixed before it.** The two variants differ in what the instrument end needs behind the panel | Decide at M4 instead of M7 | The same ordering violation the ROADMAP has already caught twice, on the most crowded face in the instrument |
| **B7** | **`L-BUCK-IN` has no damping leg and no BOM row for one**, and the page that flags it treats it as a module part while the BOM places it on the (undrawn) carrier | An R-C leg and a category fix | Flagged as open in `power-entry.md`, so this is a tracking gap rather than a blind spot — but it lands on the board nobody has drawn |
| **B8** | **Five shift-register inputs are left floating.** `R-KEY-PU` is quantity 21 — switch positions only — while `key-layout.yaml` says the five free bits "must be pulled" | Five resistors | Five CMOS inputs floating on a board that also carries the 800 kHz LED shifter. The exact fault the other 21 resistors exist to prevent |
| **B9** | **`C-STRIP-BULK` has nothing to mount to.** Two through-hole radial electrolytics are specified "at each WS2815 feed point", which is a flexible strip in a 20 mm cavity | Two 10 × 15 mm feed PCBs, or a defined potted joint | Two unsupported capacitors on solder joints to a flex strip, bonded in. The joint that fails is the one ADR 0014 calls not optional |

---

## Section A — detail

### A1 — The display-board harness does not exist

**What it is.** Nine to eleven conductors have to run 360 mm from the carrier at
the tail to the display board at the top, and no document defines that run.

**What implies it.** Three separate documents each specify part of it and none
of them adds up:

- ADR 0013 budgets the link: *"It needs **four broken-out pins** — UART pair and
  power — instead of ten."* `[repo: docs/decisions/0013-two-mcu-split.md]`
- ADR 0009 requires four more, plus a ground: *"**And a screwed service cover on
  the tail underside**, beside the matrix window, over a ten-pin header on the
  carrier: `EN`, `IO0`, `U0TXD`, `U0RXD`, `GND` for each board."*
  `[repo: docs/decisions/0009-enclosure-construction.md]` The header is on the
  carrier. The second board is 360 mm away. Those five signals have to get
  there.
- `firmware/README.md` makes it load-bearing: *"**The display board is the worse
  case.** It has no external connector of its own and it is the only path from
  the phone to the real-time board's NVS, so bricking it leaves a working
  instrument that can never be reconfigured. It gets the same two OTA partitions
  and the same header pins."* `[repo: firmware/README.md]`
- The only loom row in the BOM disposes of the whole run in four words:
  *"~23 conductors in total plus the LED and UART runs."*
  `[repo: hardware/bom.csv, WIRE-LOOM]` — "the UART runs", singular pair. `EN`,
  `IO0`, `U0TXD`, `U0RXD` and the 5 V feed are not in that sentence, and the
  four enumerated ribbons are all cluster ribbons.
- And the distance is stated: *"| Display board | **360 mm** |"*
  `[repo: docs/decisions/0013-two-mcu-split.md]`

**What is actually needed, counted out:** UART1 TX, UART1 RX, 5 V, GND,
`EN`, `IO0`, `U0TXD`, `U0RXD`, a second GND for the service group, and — by
ADR 0009's own rule — two spares. Nine signals, eleven ways.

**Three second-order things nobody has specified either.**

- **The 5 V conductor is a power conductor, not a signal.** ADR 0005's load
  table puts the display side at up to 336 mA on the 5 V rail in the
  "typical + live config over WiFi" row `[repo:
  docs/decisions/0005-power-architecture.md]`. Over 360 mm of ribbon-gauge wire
  and back, that is a real IR drop into a board whose local rail is meant to
  absorb WiFi transients.
- **Nothing conditions the UART.** ADR 0013 disposes of the run as *"the
  **inter-MCU UART**, the least timing-sensitive link in the instrument, running
  at 921600 baud with 2 % bus utilisation"* `[repo:
  docs/decisions/0013-two-mcu-split.md]`. Utilisation is not the issue: the
  *edges* are, and after the LED data lines these are the fastest edges in the
  body, running unshielded through side channels that ADR 0009 shares with 12 V
  pulsed LED current. The alternating-ground rule is written for the key chain
  only — *"**The key chain still needs a ground return per signal**"* `[repo:
  docs/decisions/0009-enclosure-construction.md]` — and no equivalent exists for
  the UART pair. ROADMAP E4b asks for it to be *"logic-analyser clean"* with
  nothing specified to make it so.
- **Idle state.** If the display board is unpowered, held in reset, or its
  harness is unplugged during assembly, its TX pin floats into the real-time
  board's RX. No idle pull is specified anywhere. `[from memory]` — the
  consequence, framing-error storms and a spurious link-down indication, is
  ordinary practice rather than a documented requirement here.

**Cost now:** four BOM lines (ribbon, two connectors, spares), and the decision
of whether the run is one 12-way ribbon or two. Ten crimps at M7.

**Cost later:** the top-ranked item in this review because of what it costs to
get wrong. ADR 0009 and `firmware/README.md` both argue at length that the
display board's recovery path is the single most important thing in a bonded
body, and then neither of them runs the wires. If `IO0` and `EN` are not in the
loom, the header they terminate at is decorative.

---

### A2 — No service aperture for the breath sensor or the trap

**What it is.** Two ADRs promise the breath sensor and its condensation trap are
serviceable in a bonded body, a spare sensor is on the BOM for that reason, and
no opening in the enclosure exists through which either can be reached.

**What implies it.**

- ADR 0003, on the sensor: *"**Treat the sensor as a wear part.** It is socketed
  or otherwise replaceable, and the trap is clearable without disassembly. **Buy
  two** — ordinary spares for a part that gets breathed into for years."*
  `[repo: docs/decisions/0003-breath-sensing-path.md]`
- ADR 0009, on the trap: *"The only stack requirement is **access to clear it
  without disassembly**. Not a drain plumbed through the body — just a
  serviceable path to the sensor end."* and *"'clearable' means reachable from
  the tail face rather than from the mouthpiece end."*
  `[repo: docs/decisions/0009-enclosure-construction.md]`
- The BOM already half-notices: *"The spare is only reachable if the first part
  comes out, and the body is bonded."* `[repo: hardware/bom.csv, SKT-BREATH]`

**What is drawn.** ADR 0009 enumerates the tail's openings exactly: the etherCON
cutout, the USB-C slot, the ~22 mm matrix window, and a *"Roughly 12 × 40 mm,
two M2 screws"* service cover over the ten-pin header. Nothing else. A
`MECH-SERVICECOVER` sized for a 2×5 header is not a hand-and-tweezers aperture,
and the sensor is a case 1351-01 part in a SIP socket with a silicone tube on one
port.

**Cost now.** One more through-cut in the laminated layer that already carries
the window and the cover, sized so the socket and the trap are reachable, and a
second cover plate. Both go into the same M4 CAD pass as the other three
openings, and the ROADMAP already books a 1:1 paper check of that face.

**Cost later.** Both promises are void and neither ADR notices. The consequence
is not a dead instrument — it is a slowly degrading one: ADR 0003 spends two
pages establishing that the gel die coat *"swells when wet, which shows up as
unreliable readings rather than as a dead part"*, and that vapour *"cannot be
eliminated from a closed tube that is breathed into"*. The mitigation it lands
on — *"only spares make it survivable"* — requires an aperture that does not
exist.

---

### A3 — The WS2815 backup data line is connected to nothing

**What it is.** WS2815 carries a second data conductor. Nothing in the design
drives it, and the level-shifter allocation shows it was never counted.

**What implies it.** The backup line is a stated *reason for the part choice*,
twice:

- *"**Backup data line.** WS2815 carries a redundant data path, so a single
  failed LED does not kill everything downstream of it. In a bonded laminated
  body that cannot be opened casually (ADR 0002), that matters more than it
  would in a serviceable build."* `[repo: docs/decisions/0014-lighting.md]`
- And it is used to reject a whole alternative architecture: a 5 V umbilical
  *"would force 5 V strips, **giving up the backup data line that matters in a
  sealed body**"* `[repo: docs/decisions/0005-power-architecture.md]`

**The evidence it is not wired.** Three places, all consistent:

- The shifter is allocated at two gates: *"SOIC-14. 5V rail TTL thresholds so
  3V3 reads high. **Two spare gates.** VERIFY WS2815 threshold"* `[repo:
  hardware/bom.csv, U-LVLSHIFT]`. Four gates, two strips, two used — one data
  line per strip and nothing for the backup pair.
- ADR 0014 confirms the intent: *"One package covers both strips."*
- The pin budget allocates *"WS2815 data, two strips | 2 | 1, 2"* `[repo:
  docs/decisions/0007-imu-selection.md]`, which is correct and sufficient: the
  backup input needs no extra GPIO, only the second buffer gate.

**Why it matters.** `[from memory]` on the mechanism, `[repo]` on the
consequence: on a WS2815 strip the redundant path is carried between LEDs, but
the head of each run has no upstream LED to supply it — the backup input at the
strip's input end has to be driven alongside the primary, or the redundancy
begins one LED late and the first failure still dark-ends the run. Left
floating, it is a high-impedance CMOS input in a channel carrying 12 V pulsed
LED current, which is the same fault class as A8 and as the key inputs ADR 0001
spends a page fixing.

**Cost now:** two traces to gates already bought and already on the board.
Literally zero new parts.

**Cost later:** the redundancy that justified the part choice is absent, in the
one place the ADR says it matters most. Discovered when an LED fails behind
bonded acrylic.

---

### A4 — No test points on either PCB

**What it is.** Neither `PCB-CARRIER` nor `PCB-MODULE` has a single test point,
probe pad or ground post specified, and nothing in the BOM provides one. The
ROADMAP repeatedly assumes access to nets that exist only as traces.

**What implies it.** Walking the E-numbered milestones for what each one has to
touch:

| Milestone | Asked for | Reachable as specified? |
|---|---|---|
| E4b | *"Framed UART between the two boards, status flowing, **logic-analyser clean**"* | Only on a bare carrier with the harness unplugged. After M7, no |
| E6 | *"**Inrush with a current probe, on switch-on *and* hot-plug**"* | Yes — a probe can go round the umbilical. Fine |
| E7 | *"Commanded codes produce expected voltages on the meter, all six channels"* | At the jacks, yes — but see B2 |
| E9 | *"**Pitch stability into worst-case cable capacitance**"*, *"Pitch DC load sweep"* | At the jack, yes |
| E11 | *"**on the T568B pin mapping in ADR 0004**"*, and ADR 0004: *"Confirm at E11 with a logic analyser and a scope on the real cable at length"* | The SPI nets appear only between the etherCON and the level shifter on each board. No pad, no header, nothing to clip a ground to |
| E14 | *"E1–E11 re-run on the carrier, not on dev boards"* | Every carrier-internal net — the sensor's buffered output, the 0.6× divider, the 5.000 V reference, both 5 V rails, the four register outputs — is a trace |
| M8 | *"**pitch scoped while the LEDs sweep**"*, *"thermal soak ... watching ... **the breath zero** at the sensor"* | In a part-assembled instrument. The breath zero is an internal carrier net |

`[repo: ROADMAP.md, docs/decisions/0004-cv-interface-module.md]`

**What else is missing with it.** A ground reference. Both boards define a star
point in prose — *"One origin, at the IDC's ground pin"* `[repo:
hardware/module/power-entry.md]`, and *"**The star point is the analog ground
pour on the bottom cluster board**, at the sensor and reference, immediately
adjacent to the umbilical connector"* `[repo:
docs/decisions/0003-breath-sensing-path.md]` — and neither brings it to anything
a probe can attach to. On the module that matters twice over, because ADR 0004
distinguishes four returns that must not be confused and every measurement of
them needs the right one.

*(Aside: that ADR 0003 sentence names "the bottom cluster board", which no
longer exists in the architecture. The carrier is the only candidate. Staleness
rather than a gap, but the AGND star is defined on a board that was deleted.)*

**Cost now.** A dozen 1 mm pads and two wire loops, on two boards being laid out
from scratch. Free.

**Cost later.** Every measurement in the table above either does not happen or
happens by soldering to a conformal-coated board inside a part-assembled
instrument at M8, which is the one gate that is not allowed to fail.

---

### A5 — Neither board has a mounting or retention scheme

**What it is.** Nothing anywhere says how the carrier or the display board is
held in the body. No mounting holes, no standoffs, no brackets, no screws in the
BOM for either. The mechanical BOM rows that exist are `MECH-UBOLT`,
`MECH-BACKPLATE` (for the connector), `MECH-THUMBREST`, `MECH-SERVICECOVER` and
`MECH-GNDBOND` — none of them holds a PCB.

**What implies it.** The carrier is positionally load-bearing in four
independent ways, all of them stated:

*"Must carry the ~22mm cutout under the 8x8 matrix (ADR 0014), the umbilical
backing-plate mounting, and the service header (ADR 0009)."* `[repo:
hardware/bom.csv, PCB-CARRIER]`

and ADR 0009 adds the fourth: *"**A USB-C slot at the tail face** ... Keep that
edge of the board at the tail."* Plus ADR 0014: *"**The carrier needs a ~22 mm
cutout** under the board, because the LED face points at the carrier and the
light has to pass through it."*

So the carrier's position sets: whether the etherCON flange lines up with its
cutout, whether the dev board's USB-C lines up with its slot, whether the matrix
lines up with a 22 mm window in the oak *and* the 22 mm hole in the carrier
itself, and whether the ten-pin header lands under a 12 × 40 mm cover. Four
registrations against three different laminated layers, with no defined datum.

**The display board is worse in one respect.** ADR 0008 says *"**It must mount
lengthwise.** At 60 mm the board is 3 mm wider than the instrument"* `[repo:
docs/decisions/0008-display-selection.md]` — it is an AMOLED that has to be read
through something, at a defined height in a 20 mm cavity, and nothing positions
it either.

**Cost now.** Four holes in the carrier outline, four in the DXF, a handful of
M2.5 standoffs in the BOM. It belongs in the same M4 CAD pass as everything
else.

**Cost later.** The boards are located by whatever they happen to rest on, and
the stack is then bonded. This is the kind of thing that is obvious in
retrospect and invisible in a repository that has fourteen ADRs and no assembly
drawing.

---

### A6 — Conformal coating has no mask list

**What it is.** The coating rule masks two ports and stops. It does not mask the
recovery path.

**What implies it.** Both halves are in the same ADR, about 140 lines apart, and
neither refers to the other:

- *"**Conformal-coat the boards.** The instrument is breathed into for hours,
  behind eighteen unsealed switch cutouts, in a body whose interior runs 10–20 K
  above ambient."*
- *"**Cut the service cover and populate its header** ... It is the only thing
  standing between a bad flash and a finished instrument that will not boot, and
  both dev boards depend on it."*

`[repo: docs/decisions/0009-enclosure-construction.md]`

And the BOM's coating note masks exactly one thing: *"MASK BOTH SENSOR PORTS
FIRST — a sealed reference chamber gains ~5.2kPa when warm and the output clips
at zero"* `[repo: hardware/bom.csv, MECH-COAT]`.

**What else has to be masked, and why each one is terminal:**

- **`HDR-SERVICE`** — ten pins that are the only route to either board after
  bonding. Coated, they are ten insulated pins.
- **`HDR-DEV`**, the dev-board sockets. The BOM is explicit about why they are
  sockets: *"SOCKETS not solder-down - a dead dev board in a bonded body is
  otherwise terminal"* `[repo: hardware/bom.csv, HDR-DEV]`. A coated socket is a
  solder-down socket.
- **`SKT-BREATH`**, for the same reason as A2.
- The etherCON contacts and the USB-C shell. `[from memory]`

**Cost now.** One sentence in `MECH-COAT`'s note and one line on the assembly
sheet.

**Cost later.** Irreversible by definition. The project has already written down
that the coating can destroy the pressure reference; it has not noticed that the
same can of aerosol can destroy the recovery path, the sensor socket and the
dev-board swap, all of which the design elsewhere treats as non-negotiable.

---

### A7 — `SCLK` and `CS` get no source termination

**What it is.** One of the three SPI lines that cross the umbilical has a series
resistor. The other two, including the clock, have nothing.

**What implies it.** ADR 0004 specifies exactly one: *"**220 Ω in series on MOSI
at the driving end.** Source termination on the one line that runs the full
umbilical carrying data."* `[repo: docs/decisions/0004-cv-interface-module.md]`
`R-MOSI-SER` is quantity 1 in the BOM.

But the conductor budget in the same ADR runs three: *"`SCLK` / `DIG_GND`",
"`MOSI` / `CS`"* — all three cross the cable. And the same ADR names the clock
as the worst of them when arguing the pin map: *"SCLK, the fastest edge in the
system, is at the far end."*

The justification given — *"the one line that runs the full umbilical carrying
data"* — is true only if "carrying data" means payload. A reflection on `CS` is
worse than one on `MOSI`, and the module's own drawn page says why:
*"A stray edge on `CS` re-frames the 32-bit word, and a DAC8568 frame carries
the software reset, the clear-code register and the internal-reference enable —
so a mis-framed word is a **sticky** failure that the 4 kHz refresh does not
clear, unlike a corrupted data bit which self-heals in 250 µs."* `[repo:
hardware/module/digital-and-supervision.md]`

**A second, undrawn complication.** On the carrier, `SCLK` does not merely go
down the cable — it also fans out to the MCP3202, which shares SPI2 (ADR 0013's
pin table). So the clock net is a T junction between a 20 mm on-board stub and a
2 m unterminated transmission line. Nothing draws that branch, because
`hardware/controller/` is empty. `[from memory]` for the branch's significance;
`[repo]` for the topology.

**Cost now.** Two resistors and two footprints, plus the E11 note that says
which to fit.

**Cost later.** ADR 0004 already puts a deadline on this: *"**This number has a
deadline.** E11 validates the real cable at the real rate and it is a gate
before the body bonds — there is no second chance to test 2 m of Cat5 at a speed
the instrument turns out to need."* If E11 says the clock needs damping, the
answer is a carrier respin — affordable then, impossible after bonding.

---

### A8 — The umbilical shield has no termination

**What it is.** A shielded cable is specified, and no document says what the
shield connects to at either end.

**What implies it.** The cable spec: *"**Shielded (STP/FTP) preferred.** Twisted
pairs are what make the analog breath channel survive (ADR 0003) and any Cat5e
has those, but the shield is free at this price and the breath pair is the one
signal with no digital margin to spare."* `[repo:
docs/decisions/0004-cv-interface-module.md]`

And the instrument-end mounting is undecided in a way that decides it:
*"**Mount the connector to an internal backing plate** — aluminium or ply"*
`[repo: docs/decisions/0009-enclosure-construction.md]`, echoed by
`MECH-BACKPLATE`'s BOM row, *"TBD - aluminium or ply"*. Ply does not terminate a
shield.

**Why it is not cosmetic.** ADR 0004's grounding section is unusually explicit
about what must not happen: *"**`PWR_GND` runs from the etherCON to the star
point on its own copper**, touching no other return on the way. It is the
dirtiest net on the board and it is the one that must be kept to itself."* A
shield bonded to conductive chassis at both ends is a second return path in
parallel with `PWR_GND` — through the module's panel, the rack rails, and the
instrument's aluminium plate, which `MECH-GNDBOND` deliberately ties to
`PWR_GND`. The ADR quantifies what shared returns cost here: *"a review measured
this as **5.7–7.2 cents of breath-correlated pitch bend**"*.

The conventional answer `[from memory]` is to bond the shield at the module end
only and leave the instrument end open or capacitively coupled — which is a
decision the etherCON variant choice (A/B6) forecloses if it is made carelessly,
because some chassis variants bond the shell to the panel by construction.

**Cost now.** One decision and one solder tag, taken alongside the variant
choice.

**Cost later.** Either the shield does nothing — in which case ADR 0004 bought
it for a reason that never materialised — or it does something unintended to the
one net the design most needs kept alone.

---

### A9 — No series resistors on the LED data lines

**What it is.** The level shifter's outputs drive two 800 kHz data lines 420 mm
each through the side channels, with nothing in series.

**What implies it.** ADR 0014 is precise about the risk and stops one component
short of addressing it:

*"**What is needed is level shifting on the data line.** ... A **74AHCT125** is
the standard answer ... **This is a classic source of intermittent, maddening LED
behaviour — strips that work on the bench and glitch in the build** — so it is
worth getting right rather than discovering empirically."* `[repo:
docs/decisions/0014-lighting.md]`

The project already knows the technique and applies it to the other fast line it
owns — `R-MOSI-SER`, *"Series termination at the DRIVING end"* `[repo:
hardware/bom.csv]` — but the two lines that share a physical channel with
eighteen key conductors and a 12 V pulsed supply get nothing. `[from memory]`
for the 220–470 Ω convention on addressable-strip data lines; `[repo]` for the
stated risk and for the asymmetric treatment.

**Cost now.** Two resistors, on a board that already has 63 passives for the key
networks.

**Cost later.** Exactly the failure the ADR names, behind bonded acrylic.

---

### A10 — The loom's spare conductors are already spent

**What it is.** Two documents each claim the same spare conductors.

**What implies it.**

- ADR 0009: *"**Run two spare conductors in every internal loom.** The looms are
  hand-built, once, into a stack that cannot be reopened. A spare pair costs a
  few cents and some crimping now; discovering you need one signal more after
  bonding costs the instrument."* `[repo:
  docs/decisions/0009-enclosure-construction.md]`
- ADR 0010: *"**Reserve cutouts for three spare switches in the plate DXF** —
  the expected assignment is octave up, octave down, and a hold/preset input ...
  **Populating them is optional; cutting them is not.**"* `[repo:
  docs/decisions/0010-key-layout-as-data.md]`
- The loom row implements the first and not the second: *"right_hand 6 signals,
  left_hand 5, left_thumb 4, right_thumb 3, each with a ground every ~4 and TWO
  SPARE CONDUCTORS"* `[repo: hardware/bom.csv, WIRE-LOOM]` — signal counts
  exactly match the 18 fitted switches.

So the three future switches have to use the spares, and then there are no
spares. And `R-KEY-PU`/`R-KEY-SER`/`C-KEY` are all quantity 21, which shows the
carrier end *was* built for 21 positions — the loom end was not.

Worse, placement is deliberately deferred: *"**Placement is an M2 question**,
decided with hands on the mule, not now."* If two of the three land in the same
cluster, that cluster's spares are gone and one switch is unwirable.

**Cost now.** Widen two ribbons by two ways each, and state that the spare-switch
conductors are additional to the two spares rather than the same ones.

**Cost later.** ADR 0010 is right that cutting the holes is the irreversible
part — but a hole with no wire behind it is the same outcome as no hole, reached
more expensively.

---

## Section B — detail

### B1 — Standalone module bring-up is blocked by the presence gate

**This would be #1 overall if it were not fixable with four screws.**

**What it is.** The module's SPI buffer is enabled only when the presence
comparator says an instrument is attached. There is no way to force it. So the
module cannot be driven by a dev board, which is the basis of the entire E6→E12
plan.

**What implies it.** The claim, twice:

- *"**The module can be brought up entirely standalone** — driven from any dev
  board with a test pattern and a multimeter — long before the instrument
  exists. This de-risks the whole CV problem on its own schedule."* `[repo:
  docs/decisions/0004-cv-interface-module.md]`
- *"The module track (E6 onward) can run start to finish without the instrument
  existing. Drive it from any dev board with a test pattern and a multimeter."*
  `[repo: ROADMAP.md]`

And the circuit that contradicts it, in a page that is already drawn:

- *"**Gate the 74AHCT125's output enable from a real presence detect**, so
  'instrument absent' is a state the hardware knows about rather than one it
  stumbles into."* `[repo: docs/decisions/0004-cv-interface-module.md]`
- *"| Cable unplugged | R4/R5 pull both inputs to `AGND` → **0 V** |"* and the
  corrected tap: *"Unplugged that node is at 0 V (pulled by R4/R5); alive it is
  at +0.2 V. Threshold +100 mV"*, with *"an LM311 half, open-collector, pulled
  to the bus +5 V rail, driving all four `OE` pins."* `[repo:
  hardware/module/digital-and-supervision.md, docs/decisions/0004-cv-interface-module.md]`

A dev board on a patch lead supplies `SCLK`, `MOSI` and `CS` on pins 4/5/7/8 and
nothing at all on pins 1/2. The comparator therefore reads "absent", `OE` is
de-asserted, the buffer outputs go Hi-Z, and the DAC sees the six pull resistors
on its side of the buffer and nothing else. E7 through E11 all fail, in a way
that looks like a dead DAC.

*(This is a different finding from the tap-point error the page already flags
under "Still open". That one says the detect does not work as drawn. This one
says that even once it works, it locks out the bench.)*

**Cost now.** A two-pin jumper on the `OE` node, or a pair of pads to short. Or
one line in the ROADMAP saying the bench fixture must present +0.2 V across the
breath pair — but a jumper is more honest, because it also covers the case where
the breath front end is the thing under test.

**Cost later.** Reaching E7 with a correct module, a correct fixture and no
output, and debugging a circuit that is working as designed. The module is the
deliverable with four screws in it, so the fix is cheap whenever it is found —
what is expensive is the time and the doubt.

---

### B2 — The frame watchdog defeats static bench measurement

**What it is.** The module clears all DAC channels if `CS` stops toggling for
~99 ms. Several ROADMAP acceptance criteria are written as static measurements.

**What implies it.**

*"`t ≈ 0.45 · R · C` → 1 MΩ × 220 nF ≈ **99 ms**"*, *"**Retriggered from the
buffered, DAC-side `CS`**"* `[repo:
hardware/module/digital-and-supervision.md]`, and *"**Assert `CLR` at the module
when no valid frame has arrived for N milliseconds** ... an A/C grade part clears
to zero scale"* `[repo: docs/decisions/0004-cv-interface-module.md]`.

Against:

- E7: *"**Commanded codes produce expected voltages on the meter**, all six
  channels"* — a command followed by a meter reading is more than 99 ms.
- E8: *"Raw analog gain and offset trimmed to target"* — trimming with a
  screwdriver.
- E9: *"**Multi-point fit** — one point per octave ... 1V/oct verified against a
  real VCO"* — a VCO settling at each point.

`[repo: ROADMAP.md]`

Firmware has the corresponding rule for the instrument — *"**Refresh
everything, every pass. Never write-on-change.**"* `[repo: firmware/README.md]`
— but `firmware/README.md` explicitly excludes bring-up fixtures from its scope:
*"Throwaway test firmware for E-track milestones belongs in `fixtures/`, not in
the instrument firmware."* Nothing tells the fixture author.

**Cost now.** One sentence against E7, or a `CLR`-defeat pad beside the
monostable.

**Cost later.** Same symptom as B1 at the same milestone, from the other
direction, and the two together will read as one confusing fault.

---

### B3 — No bench +12 V entry on the carrier

**What it is.** The instrument's analog front end, its reference and its LEDs
all run from raw umbilical +12 V. USB supplies 5 V. There is no third way in.

**What implies it.** The claim: *"**OR the umbilical power with USB power** — it
costs a diode, and it means the instrument runs on the bench during development
without a rack attached. That is worth a diode."* `[repo:
docs/decisions/0005-power-architecture.md]`

The power tree in the same ADR shows what USB does not reach:

```
umbilical +12V ──┬── WS2815 LED strips          (direct, no conversion)
                 ├── REF5050 5.000V ──[OPA2197 ½]── MPXV4006DP breath sensor
                 ├── OPA2197 V+  (½ reference buffer, ½ breath buffer)
```

The BOM half-notices and draws the wrong conclusion: *"Both sources drop ~0.3V,
leaving ~4.7V at the dev boards' 5V pins - fine for their onboard LDOs, **and the
breath sensor is no longer on this rail**"* `[repo: hardware/bom.csv, D-USBOR]` —
the sensor's absence from the 5 V rail is recorded as a reason the diode drop is
harmless, not as the reason the bench affordance no longer covers breath.

**What it costs the plan.** The ROADMAP's headline shortcut is
*"**E1 → E2 → E4 → E5 on a bench, mounted to M2.** Dev board, breath sensor, key
scan, USB MIDI, on a laser-cut test plate"* — and E2 is breath. On dev boards
with a lab supply that is fine. The problem arrives at
E14: *"**E1–E11 re-run on the carrier, not on dev boards.** Everything before
this was proven on a different physical thing."* `[repo: ROADMAP.md]` At that
point the carrier's only +12 V entry is the etherCON, so E14 needs a powered
rack and a working module for every one of its eleven re-runs — including E1,
E2, E3, E4 and E5, none of which have anything to do with the module.

**Cost now.** A two-pin header or a pair of pads on the carrier's +12 V node
downstream of `D-REVSHUNT`, or an RJ45-to-flying-lead breakout in `tools/`.

**Cost later.** E14 becomes rack-dependent for no reason, and a carrier fault
and a module fault become hard to tell apart at the exact milestone whose
purpose is to prove the carrier.

---

### B4 — The display rail's bulk capacitor and the regulator's location

**What it is.** Two unanswered questions about a rail that ADR 0013 makes an
architectural guarantee.

**What implies it.**

- The requirement: *"give each board its own regulator from the umbilical +12V,
  **with local bulk capacitance on the display board**, so WiFi bursts are
  absorbed locally rather than reaching the analog section."* `[repo:
  docs/decisions/0013-two-mcu-split.md]`, repeated in
  `docs/reference/latency-budget.md`.
- The part: `C-BULK-DISP`, part `TBD`, status `open`, note *"Absorbs WiFi TX
  transients so they do not reach the rack rail"* `[repo: hardware/bom.csv]`.
- The regulator's location: *"**Two** R-78E5.0 regulator modules — one per dev
  board"*, in the list of what **the carrier** holds `[repo:
  docs/decisions/0013-two-mcu-split.md]`. So buck B is at the tail and its load
  is 360 mm away.

**Three things nobody has decided.**

- **Whether buck B is really on the carrier.** If it is, "local bulk capacitance
  on the display board" sits at the far end of a 360 mm inductive run from its
  regulator, which is a different circuit from the one the isolation argument
  describes. If it is not, the carrier's parts list is wrong.
- **The value.** `[from memory]`: the R-78E series specifies a maximum output
  capacitance, and a 470–1000 µF bulk of the kind `C-STRIP-BULK` uses would
  exceed it — a switching module that will not start, or starts into current
  limit. This one is weaker than the rest of the review because I am asserting a
  datasheet limit I cannot cite from the repo; it wants checking rather than
  believing.
- **The pin.** ADR 0005's tree says *"12V→5V buck B ──── **display board 5V
  pin**"* while ADR 0008's own board table says the breakout is
  *"28 pins — 18 GPIO plus **3V3 / GND / VBUS**"* `[repo:
  docs/decisions/0005-power-architecture.md,
  docs/decisions/0008-display-selection.md]`. There is no "5V pin" in that list.
  Feeding 5 V into `VBUS` on a board that may carry charging circuitry is a
  question, not a given.

**Cost now.** Two decisions, one part number, and a note on the board's power
entry. All of it before the carrier is laid out.

**Cost later.** A display board that browns out on WiFi TX, or a regulator that
will not start, 360 mm inside a bonded body — and the thing it was bought to
protect is the analog section.

---

### B5 — Nothing conducts heat to the aluminium plate

**What it is.** The entire lighting budget is sized from a thermal resistance
with no mechanism behind it.

**What implies it.**

- README: *"**Heat.** The body is oak and acrylic — insulators — and sealed.
  **Every watt leaves through the aluminium plate**, part of which is under the
  player's hands."* `[repo: README.md]`
- ADR 0014 turns that into the number everything else depends on: *"The existing
  electronics dissipate roughly 5 W for an interior rise of 10–20 K, so call it
  **~3 K per watt**."* — and from it, *"**A single instrument-wide lighting
  budget of ~3 W**"*. `[repo: docs/decisions/0014-lighting.md]`

**What is missing.** No thermal interface anywhere: not between the carrier and
the plate, not for either R-78E5.0, not for the display board, not for the LED
strips. The strips are in the side channels against acrylic; the carrier is at
the tail under oak; the stack puts *"oak top ~6 mm"* between the cavity and the
plate `[repo: docs/decisions/0009-enclosure-construction.md]`. `[from memory]`:
oak is a good insulator, so "every watt leaves through the aluminium plate" is a
statement about where the heat eventually goes, not about a path anything has.

**Partially retrofittable, which is why it is in section B.** The ROADMAP books
the measurement: *"**Interior temperature rise under load** | M8 | The lighting
budget is set from an estimated 3 K/W"* — and M8 is pre-bond, so a pad or a
bracket can still go in. What cannot change at M8 is the stack geometry.

**Cost now.** A thermal pad and a bracket decided at M4, or an explicit
statement that there is no conduction path and 3 K/W is a convection-and-bulk
estimate.

**Cost later.** If M8 measures materially worse than 3 K/W, the 3 W clamp is
wrong and the only lever left is less light — which is the one parameter ADR
0014 spends its length defending.

---

### B6 — The etherCON variant is decided after the parts it constrains are cut

**What it is.** An ordering violation of exactly the class the ROADMAP has
already caught twice.

**What implies it.**

- The deferral: *"**Which etherCON variant at each end.** Feedthrough
  (NE8FDP-class) presents a plain RJ45 on the back, so the instrument end could
  take a short patch lead to a jack on the carrier instead of eight soldered
  wires inside a body that cannot be reopened ... **Decide with the datasheets in
  hand at E12 and M7**, not now."* `[repo:
  docs/decisions/0004-cv-interface-module.md]`
- What is fixed earlier: M4 produces *"Full laminated stack in CAD, every layer
  a 2D part"*, M5 cuts the plate, E13 builds the carrier — all before M7. `[repo:
  ROADMAP.md]`
- And the face is already the tight one: *"**The tail face is crowded.** It
  carries the umbilical connector, the USB-C slot, and — on the underside just
  inboard — the matrix window ... all of it must be drawn together at M4"*
  `[repo: docs/decisions/0013-two-mcu-split.md]`

The two variants differ in what sits behind the panel: a feedthrough needs a
mating RJ45 and its bend radius inside a 40 mm tail section that also holds the
carrier, the breath trap and the service header; a solder-tag variant needs
eight wires and no clearance. Those are different CAD models, and M4 has to pick
one.

**Cost now.** Pull the decision forward to M4 — the datasheets are a download.

**Cost later.** The tail DXF and the carrier outline are cut against an
assumption, on the face ADR 0009 says has *"about 3.5 mm of material above and
below the cutout"*.

---

### B7 — `L-BUCK-IN` has no damping leg, and is filed on the wrong board

**Already flagged as open, so this is a tracking gap rather than a blind spot —
but it lands on the board nobody has drawn.**

*"**Damping the input LC.** `L-BUCK-IN` (10–47 µH) in front of a constant-power
switching load, with 2 m of cable and ~2 mF at the far end, is the textbook
negative-resistance instability and **no damping leg is specified**. Put it on
E11 with the real cable."* `[repo: hardware/module/power-entry.md]`

Two things follow that the page does not say. There is no BOM row for a damping
R-C — the BOM has `L-BUCK-IN` and no companion. And `L-BUCK-IN` is categorised
`controller`, i.e. on the carrier, while the page that owns the problem is a
module page: the inductor is in front of the buck, and the buck is in the
instrument. Whichever board it is on, the damping leg has to be on the same one,
and if that is the carrier then it is unretrofittable after bonding.

**Cost now.** One R-C and a category fix. **Cost later:** a rail that rings at
switch-on, discovered at E11, on the board that cannot be respun after M7.

---

### B8 — Five shift-register inputs are left floating

`R-KEY-PU`, `R-KEY-SER` and `C-KEY` are all quantity 21 — *"21 sets of pull-up,
series resistor and filter capacitor"* `[repo:
docs/decisions/0013-two-mcu-split.md]`, which is 18 fitted switches plus 3
reserved positions. The chain is 32 bits. Of the 14 spare bits, 6 are the marker
pattern (tied hard by definition), 3 are the reserved switch positions
(covered), and:

*"The 5 genuinely free bits are FLOATING CMOS INPUTS and must be pulled — the
exact fault `R-KEY-PU` exists to fix (ADR 0001)."* `[repo:
config/key-layout.yaml]`

ADR 0001 says the same: *"**Tie `CLK INH` low at all four devices, and pull every
unused parallel input.** Both are permanent, both were sitting only in a review
document, and the five 'free' bits are floating CMOS inputs."* The `CLK INH` half
made it into the BOM note for `U-KEYS`; the pull half did not, and the quantity
proves it.

Five resistors. Small, but on a board that cannot be touched after bonding, and
the failure mode is the one the other 63 passives exist to prevent.

---

### B9 — `C-STRIP-BULK` has nothing to mount to

*"**470–1000 µF at each strip feed point.** Bulk capacitance belongs where the
current swings, not at the module end of a 14-inch cable."* `[repo:
docs/decisions/0014-lighting.md]`, and `C-STRIP-BULK` is specified
`THROUGH-HOLE radial`, quantity 2, *"Bulk at each WS2815 feed point"* `[repo:
hardware/bom.csv]`.

A feed point on a WS2815 run is three solder pads on a flexible strip. Two
through-hole radial electrolytics hanging off flex-strip pads in a 20 mm cavity,
inside a bonded body, with nothing retaining them, is an assembly nobody has
drawn — and ADR 0014 calls the capacitor *"the cap that is not optional"*.

**Cost now.** Two 10 × 15 mm feed boards, or a defined strain-relieved and
potted joint, decided at M4 with the channel depth.

**Cost later.** The joint that fails is the one the ADR says is not optional,
behind bonded acrylic.

---

## What I checked and did not find missing

Bounding the review, so the absence of an item below is informative:

- **Module analog.** The five drawn pages are dense and self-critical, and they
  carry their own "Still open" lists — the input-LC damping, the `'123` power-on
  reset, the presence tap point, the analog-rail fuse. I found nothing in them
  that they have not already flagged, except A7 and B1/B2.
- **Umbilical protection.** All three TVS groups exist at both ends, with the
  12 V-standoff reasoning on the breath legs and `D-REVSHUNT` for the rollover
  lead. This is well covered.
- **Key input networks.** 63 passives for 21 positions, the `CLK INH` tie, the
  marker pattern, the alternating-ground rule. Covered, except B8's five pulls.
- **Breath analog path.** Sensor supply, buffer rail, divider impedance, the
  220 nF anti-alias cap, the in-amp topology, the bias returns. Covered
  thoroughly.
- **Recovery.** OTA rollback, USB-MIDI opt-in, the service header, dev-board
  sockets. All present — which is precisely why A1 and A6 matter, since both
  quietly disable it.
- **The 100 nF class of gap.** `C-DECOUPLE-CARRIER` already covers every carrier
  IC supply pin individually. I found no missing decoupling worth a row, and did
  not manufacture one.

---

## One-line summary

Of the ten unretrofittable items, **seven are conductors, apertures, pads or
masking instructions rather than components** — the instrument side is not short
of parts, it is short of the drawing that would show how the parts it already
has are connected, held, reached and probed. That is the predictable shape of a
project where `hardware/module/` has five schematic pages and
`hardware/controller/` has a `.gitkeep`.
