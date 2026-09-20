# D2 — Missing testability, diagnosis and bring-up provisions

Review of `/home/user/Woody` at Phase 0, against `README.md`, `ROADMAP.md`, all
fourteen ADRs, `docs/reference/`, `hardware/bom.csv`, `config/key-layout.yaml`
and the prior analog review.

**No schematic or PCB exists yet.** `hardware/controller/` and
`hardware/module/` are empty. Every provision below is therefore still free.
Most of them stop being free at E12 (module fab), E13 (carrier fab), M4 (stack
CAD) or M6 (body cut), and all of them stop being available at M8 when the body
is bonded.

## The shape of the problem, in one paragraph

After bonding there are exactly **two** electrical openings into the instrument:
the etherCON, carrying eight conductors that are **all committed** (ADR 0004's
revised budget is 8 of 8, the spare was consumed and MISO was deleted), and a
**USB-C slot at the tail serving one of the two microcontrollers**. Everything
else — the breath sensor and its precision reference, the ADC, the buffer, both
SPI buses, the inter-MCU UART, the shift-register chain, the 5 V buck, the LED
feeds, the second MCU in its entirety — is behind a glue line. The project's
documents contain roughly thirty instructions of the form "measure this",
"confirm this with a logic analyser", "verify at E14 on the carrier", and
"re-run this at M8", and not one line anywhere specifying the physical means to
do so. The prior review found the absence of a *self-test*; what is missing
underneath that is the **hardware the self-test would use**, and the access a
human with a scope would need on the day the instrument stops working.

Severity key: **Critical** = the design cannot be debugged or recovered without
it; **High** = a documented milestone or a known failure mode becomes
unobservable; **Medium** = diagnosis becomes guesswork or requires destructive
work; **Low** = convenience with real value.

---

# A — Access through a sealed body

## 1. **There is no external diagnostic connector, and the UART0 console terminates on a header that is inside the bonded body.**

- **Severity:** Critical
- **Where:** Carrier PCB (E13) and the tail or underside face of the body (M4/M6).
- **What goes wrong:** ADR 0007 spends two GPIO (43/44) on a UART0 console
  specifically so a console survives — *"In a body that cannot be opened, two
  pins is a cheap price for keeping a console"* — and then routes it to "a
  carrier test header", which is sealed inside that same body. The pins are paid
  for and the benefit is thrown away at the last step. After bonding, panic
  output, boot logs, the chain error counter, the breath zero, the NVS CRC state
  and every `printf` a future debugging session would want are unreachable.
  Telemetry over WiFi (F6) is not a substitute: it is on the *other* MCU, across
  a link that is itself one of the things you will need to debug, and it
  requires the radio, the web stack and the UART protocol all to be working.
- **Provision:** One external **diagnostic connector** at the tail or on the
  underside near the matrix window, behind a small oak or acrylic plug. Ten
  ways, 1.25 mm JST or 2×5 1.27 mm header:

  | Pin | Net |
  |---|---|
  | 1 | GND |
  | 2 | RT_UART0_TX (GPIO43) |
  | 3 | RT_UART0_RX (GPIO44) |
  | 4 | RT_EN (reset) |
  | 5 | RT_BOOT (GPIO0) |
  | 6 | DISP_UART0_TX |
  | 7 | DISP_UART0_RX |
  | 8 | DISP_EN |
  | 9 | DISP_BOOT |
  | 10 | +5 V (rail sense / fixture power, fused or series-R) |

  This one part solves console, recovery and re-flashing for **both** boards
  (findings 2 and 3) for the life of the instrument.
- **Cost:** One connector, a 4-way addition to the top loom, a ~12 × 6 mm hole
  and a plug. Under £2 and one CAD feature.
- **Retrofit:** **One-shot.** Impossible after bonding at any price.

## 2. **The display board has no external access of any kind — no USB, no console, no reset, no boot button — and how it gets flashed is still an open question in ADR 0013.**

- **Severity:** Critical
- **Where:** Display board mounting, top loom, carrier (E13), body (M6).
- **What goes wrong:** ADR 0013 leaves open *"whether the display board is
  flashed over its own USB or via the real-time board"*, and ADR 0009 provides a
  USB-C slot for the **real-time** board only. The display board holds the web
  app assets (F5), the WiFi stack, the panel driver and half the UART protocol —
  the half most likely to need changing after the instrument is finished. If
  that decision is left to M7, the default outcome is a sealed board that can
  only be updated over WiFi, by the very firmware that would be being replaced.
  One bad OTA, one corrupt partition, one protocol-version mismatch that stops
  the link coming up, and the top third of the instrument is dead permanently.
- **Provision:** Decide **now**, and prefer the proxy: wire the display board's
  UART0 pair, `EN` and `IO0` down the body to the diagnostic connector in
  finding 1 (four conductors, which is why the loom needs four spares and not
  ADR 0009's two). `esptool` over those four wires flashes an ESP32 of any
  variety from a dead stop, needs no working firmware, and is the same procedure
  in ten years. Optionally *also* gate `EN`/`IO0` from two real-time GPIO so the
  real-time board can re-flash its neighbour over USB with no extra cable — but
  see finding 17 on the contention for those two pins.
- **Cost:** Four conductors in a loom that is being built anyway.
- **Retrofit:** **One-shot.**

## 3. **Nothing provides external access to the real-time board's BOOT and EN buttons, and the tail USB-C cannot be both the MIDI port and the recovery path.**

- **Severity:** Critical
- **Where:** Tail face (M6), carrier (E13).
- **What goes wrong:** The ESP32-S3's internal USB PHY serves *either* USB-OTG
  (which is what class-compliant USB MIDI, milestone E5, requires) *or* the ROM
  USB-Serial-JTAG. When the application owns the PHY and enumerates as a MIDI
  device, there is **no reliable host-side way to force the chip into download
  mode** — the flasher's auto-reset handshake has nothing to talk to. The
  universal fallback is holding BOOT while pulsing EN, and both buttons are on
  the dev board, behind oak. The failure mode is the classic one: a firmware
  image that hangs before USB initialises, or an interrupted flash, bricks an
  instrument that cannot be opened. ADR 0009's tail slot is sized for the
  *connector*, not for the buttons beside it.
- **Provision:** Bring `EN` and `IO0` of the real-time board to the diagnostic
  connector (finding 1), **and** either align the tail slot so the dev board's
  own buttons are reachable with a pin, or fit two small externally accessible
  push buttons. Belt and braces is justified here — this is the one failure that
  ends the project. Add a firmware rule: **never burn the eFuse that disables
  the download ROM**, and keep a factory-image partition.
- **Cost:** Two conductors, or two 5 mm holes.
- **Retrofit:** **One-shot.**

## 4. **There is no pneumatic access to the breath path after bonding — no way to apply a known pressure, and no way to re-verify or re-calibrate the sensor for the rest of the instrument's life.**

- **Severity:** High
- **Where:** Breath tube, trap and mouthpiece region (M4/M6/M7).
- **What goes wrong:** ADR 0009 requires the trap be *"clearable without
  disassembly"*, which is a cleaning requirement, not a measurement one. Every
  breath measurement the project specifies — transducer response, tube delay and
  ringing, Helmholtz restrictor sizing, the cold-start warm-up sweep, the
  blocked-reference-chamber check, the breath-zero-versus-temperature soak — is
  performed by putting a known pressure in at one end and watching the other.
  After M8, none of them can be repeated. And they *will* need repeating: ADR
  0003 calls the sensor the most likely part to fail, calls the PTFE plug a
  clog-prone restrictor, and states the reference port must never be blocked —
  three failures whose signature is "breath response has gone wrong", all
  distinguishable only by applying a known pressure and reading the response.
- **Provision:** A **tee with a plugged luer or barb stub** in the tube between
  the mouthpiece and the trap, brought out through the body beside the
  mouthpiece and capped. A hand pump and a £15 reference manometer then give a
  full-span breath calibration, on the bench or years later, without opening
  anything. It also makes ADR 0003's "confirm which port is P1 with a syringe"
  a check you can repeat on the finished instrument rather than only at E2.
- **Cost:** A tee, a cap, one hole. Under £5.
- **Retrofit:** **One-shot.** The tube and trap are laminated in.

## 5. **The only externally verifiable electrical reference to the aluminium plate is accidental, and the plate bond is a known silent-failure path.**

- **Severity:** Medium
- **Where:** Plate stack, U-bolt, tail (M5/M7).
- **What goes wrong:** ADR 0009 makes bonding the plate to `PWR_GND` one of its
  four "free now, impossible later" items, because an unbonded plate fires
  spurious notes when touched. The bond is a ring terminal on an M3 screw inside
  the cavity. A crimp that is loose, or that relaxes over a few years of thermal
  cycling, produces exactly the symptom the bond exists to prevent — and by then
  there is no way to check it.
- **Provision:** Make the bond **measurable from outside**: ensure at least one
  externally accessible conductive feature (the U-bolt is the natural one, since
  ADR 0009 already through-bolts it into the plate stack) is deliberately
  continuous with the plate, and that `PWR_GND` is reachable at the etherCON
  shell or at pin 6. Then "plate bond intact" is a two-probe continuity check on
  the finished instrument. Record the as-built resistance at M8 so a later
  measurement has something to be compared against.
- **Cost:** Nothing — it is a decision to make a path deliberate and to write
  down the number.
- **Retrofit:** The *measurement path* is one-shot; the *number* must be
  recorded at M8.

## 6. **The umbilical carries no return conductor, so the instrument can never observe anything about the module, and the module can never report anything to the instrument.**

- **Severity:** High
- **Where:** ADR 0004 pin map, decided at E11/E12.
- **What goes wrong:** MISO was deleted on the argument that *"+12 V on the
  umbilical is itself evidence the module is connected"*, and the prior review
  already noted that nothing senses it. The consequences are wider than presence
  detect. There is **no path by which the instrument can verify any part of its
  own CV output**: the DAC8568 is write-only with no SDO, the analog chain is
  two metres away, and no conductor comes back. Power-on self-test therefore
  cannot cover pitch, the four mod channels, the ambient-zero injection, the
  breath receiver, the watchdog, or whether the cable's SPI pairs are intact.
  The instrument will happily display a note it is not actually outputting.
- **Provision:** Three options, decide deliberately at E11 rather than by
  default: (a) accept, and move the entire burden to module-side indicators —
  findings 18 to 20, which is the cheap and probably correct answer; (b) trade
  `DIG_GND` (pin 8) for `MISO`, letting SPI returns share `PWR_GND`, and measure
  the cost at E11 — the link is 0.6 MHz, so this is likely free; (c) keep 8/8
  and accept that the module is diagnosed by eye. Whichever is chosen, **write
  the reasoning down**, because the documents currently imply a presence-detect
  capability that does not exist.
- **Cost:** Option (b) costs one E11 measurement. Option (a) costs the parts in
  findings 18 to 20.
- **Retrofit:** The instrument end is **one-shot**; the cable and module are not.

---

# B — Test points, stage boundaries and isolation

## 7. **No test points are specified anywhere in the project, on either board.**

- **Severity:** Critical
- **Where:** Carrier (E13) and module (E12) layout.
- **What goes wrong:** Every milestone in Track E is written as a measurement
  and none names a node. E7 says "commanded codes produce expected voltages" —
  measured where? The DAC is a TSSOP-16 whose output pins sit under a scaling
  stage; the jack is behind a 1 kΩ series resistor and a clamp pair. E8 says
  "trimmed to target, linear across the span" — at the op-amp output, or at the
  jack into a load? Those differ by exactly the divider error ADR 0006 spends a
  page on. Without named, probeable nodes, bring-up degrades into probing IC
  legs with a needle, which on a 0.65 mm TSSOP is how boards get destroyed
  during their first power-on.
- **Provision:** A **test point schedule** as a deliverable, with 1.0–1.5 mm
  pads (and a ground pad within 5 mm of each, so a scope spring ground can be
  used — measuring tens of millivolts of rail ripple with a 15 cm ground lead
  measures the lead):

  **Carrier:** umbilical +12 V after the polyfuse; buck 5 V out; real-time 3V3;
  REF5050 out; OPA2197 reference-buffer out; sensor `VS` at the sensor pin;
  sensor `Vout`; breath buffer out; ADC input node (after the divider, at the
  220 nF); `AGND` star point; `PWR_GND`; `BREATH` at the connector; each 74x165
  `Q_H`, `CLK`, `SH/LD` at the first and last device in the chain; both LED data
  lines at the level-shifter output; UART1 TX and RX.

  **Module:** bus +12 V, −12 V, +5 V at the header; each rail after its diode
  and after its ferrite; LM317 5.25 V out; DAC `AVDD` and `VREF`; **each of the
  seven used DAC output pins**; each op-amp output before its 1 kΩ series
  resistor; each jack tip; in-amp `+IN`, `−IN`, `REF` and `OUT`; both breath pot
  wipers; the watchdog's retrigger input and its `CLR` output; the load switch's
  `FAULT` and `ILIM` nodes; the level shifter's `OE`.
- **Cost:** Pad area and a silkscreen label each. Effectively zero on boards
  that are not area-constrained.
- **Retrofit:** **One-shot on the carrier** (sealed); a board spin on the module.

## 8. **There is no logic-analyser landing on any bus, on boards where four separate buses must be proven "logic-analyser clean".**

- **Severity:** High
- **Where:** Carrier (E13), module (E12).
- **What goes wrong:** E4b requires a *"logic-analyser clean"* inter-MCU UART;
  E11 requires SPI verified on the real cable at length; E14 requires **E1–E11
  re-run on the carrier**; the latency budget's characterisation table calls for
  an LA on the ADC round trip, the umbilical and the UART. On a passive carrier
  the dev boards plug into sockets, so the signals of interest are *underneath a
  seated module* — the one place an LA clip cannot go. E14 is the milestone that
  is silently unachievable here: it asks for every earlier measurement to be
  repeated on a board that exposes less than the dev boards did.
- **Provision:** Two 2×5 0.1 in headers on the carrier with **alternating
  grounds**, one per bus group:
  - LA-A: SPI2 SCK, MOSI, MISO, CS_DAC, CS_ADC (+ 5 grounds)
  - LA-B: SPI3 SCK, MISO, latch, LED_D1, LED_D2 (+ 5 grounds)
  - plus UART1 TX/RX on the diagnostic connector (finding 1), which makes the
    inter-MCU link sniffable **after bonding as well**.

  On the module, the same on the connector side of the level shifter: SCLK,
  MOSI, CS as received from the cable, plus their grounds — that is precisely
  the node E11 exists to look at, and ADR 0004's open question about whether a
  74AHCT14 Schmitt receiver is needed cannot be answered without it.
- **Cost:** Two headers, pennies. Unpopulated pads are enough.
- **Retrofit:** **One-shot on the carrier.**

## 9. **There is no way to inject a known signal at any stage boundary, so a fault can only be localised by removing parts.**

- **Severity:** High
- **Where:** Carrier and module layout.
- **What goes wrong:** The breath chain is sensor → buffer → {divider → ADC,
  umbilical → in-amp → gain pot → offset → output filter → jack}. That is seven
  stages between a puff of air and a voltage, spread across two boards and two
  metres of cable, and the only stimulus available is a human exhaling. When the
  breath output is wrong, nothing distinguishes a clogged restrictor from a
  swollen die coat from a drifted reference from a broken cable pair from a
  mis-set knob. The same is true on the CV side: E8's "linear across the span"
  failing tells you nothing about whether the DAC or the scaling stage is at
  fault.
- **Provision:** **Break-and-inject links** — a 0805 pad pair with a 0 Ω, or a
  2-pin header with a shunt — at each stage boundary, with a test pad on each
  side:
  - carrier: buffer output → umbilical driver; buffer output → ADC divider;
    REF5050 → buffer input (lets a bench 5.000 V be substituted)
  - module: DAC out → each op-amp input (drive the scaling stage from a
    precision source and characterise it independently of the DAC); op-amp out →
    1 kΩ series resistor; in-amp OUT → gain pot; ambient-zero DAC → in-amp `REF`
    (grounding `REF` characterises the in-amp alone)
  - module: pads across the `BREATH`/`AGND` receive pair so a bench source can
    drive a known differential voltage with **no instrument connected** — this
    is what makes E10's breath stage and the two panel knobs trimmable
    standalone.
- **Cost:** Ten to fifteen 0 Ω links and their pads.
- **Retrofit:** Module, board spin. **Carrier, one-shot.**

## 10. **The frame watchdog will fight every bring-up fixture that writes the DAC and stops, and there is no way to disable it.**

- **Severity:** High
- **Where:** Module, `U-WATCHDOG` (74HC123), E7 onward.
- **What goes wrong:** ADR 0004 asserts `CLR` when no valid frame has arrived
  for N ms. E7's method is "command a code, read the meter" — a fixture that
  writes once and stops. The watchdog then clears the DAC to zero scale, the
  meter reads 0 V, and the first hour of E7 is spent debugging a DAC that is
  working perfectly. The same trap catches E8's trimming (adjust a trimmer,
  watch the output — which has been cleared), E9's calibration points and E10's
  channel trimming. This is a designed-in feature that makes four milestones
  hostile.
- **Provision:** A **jumper that disables the watchdog** — hold the monostable
  retriggered, or link `CLR` high — clearly labelled, fitted during E7–E10 and
  removed at E12 as a checklist item. Add a **test pad on `CLR`** and an
  indicator LED (finding 19) so its state is never in doubt. Also specify N in
  the ADR; it is currently "size N so a busy loop cannot trip it".
- **Cost:** One jumper.
- **Retrofit:** Module board spin — but cheaper to notice now than at E7.

## 11. **The level shifter's output enable is gated from umbilical +12 V, which contradicts the claim that the module can be brought up standalone.**

- **Severity:** High
- **Where:** Module (E12), affects E7–E10.
- **What goes wrong:** ADR 0004 gates the 74AHCT125's `OE` from umbilical +12 V
  presence, and ADR 0004 also states *"the module can be brought up entirely
  standalone — driven from any dev board with a test pattern and a multimeter"*.
  Those are in tension: a dev board on the bench driving SPI into the module has
  no reason to be feeding +12 V back up a cable, and with `OE` deasserted the
  DAC sees nothing. Worse, the sense node is the *output of the load switch*, so
  what it actually detects is "the panel toggle is on", not "an instrument is
  attached" — the presence detect does not detect presence (see finding 6).
- **Provision:** A three-way link on `OE`: gated / forced-on / forced-off.
  Forced-on is the bench mode and also the fault-isolation mode; forced-off
  parks the DAC inputs safely while probing. Pair with a **bench umbilical
  harness** (finding 16).
- **Cost:** A 3-pin header.
- **Retrofit:** Module board spin.

## 12. **The four shift registers are electrically indistinguishable, so a chain fault localises to "the chain" rather than to a segment.**

- **Severity:** High
- **Where:** `config/key-layout.yaml`, carrier and cluster boards (E13, M7).
- **What goes wrong:** ADR 0001's marker pattern is the project's best idea about
  the key chain: 4–6 spare bits carrying a fixed pattern, checked every read,
  with a visible error counter. But the pattern is described as one pattern
  across the chain. A non-zero counter then says only "the looms need work" —
  and the roadmap's most time-critical measurement ("key-chain error counter
  over an hour, LEDs and WiFi active … says the looms need work **while the body
  is still openable**") becomes a yes/no rather than a pointer. There are 14
  spare bits and four physical loom segments.
- **Provision:** Allocate **three marker bits in each of the four registers, and
  make each register's pattern distinct** (e.g. `101`, `010`, `110`, `001`).
  Firmware then reports which device's field failed, which localises the fault
  to one loom segment and one connector. Record the allocation in
  `key-layout.yaml` alongside `spare_bits`. While there: define the idle level of
  every unused input explicitly — a floating 74x165 input is a random bit that
  will be blamed on the loom.
- **Cost:** Wiring already being done, plus a few lines of YAML.
- **Retrofit:** **One-shot.**

## 13. **Every internal loom is planned as soldered wiring, so no segment can be isolated, swapped or measured independently during the one assembly you get.**

- **Severity:** Medium
- **Where:** Carrier and satellite boards (E13, M7, M8).
- **What goes wrong:** M8's gate requires "failure injection" and a full re-run
  of the E11 breath-noise test on the final harness. Both mean disconnecting and
  reconnecting things. With soldered looms, the only failure you can inject is
  unplugging the umbilical, and a suspect segment cannot be substituted for a
  known-good one. It also means a single wiring error found at M8 is a
  desoldering job inside a populated cavity.
- **Provision:** **Land every internal loom on a connector at the carrier**
  (JST-XH or similar, keyed, one per loom: top/display, upper cluster, lower
  cluster, thumb clusters, strip A, strip B, breath sensor). Keying matters more
  than it sounds — four identical cluster looms are four chances to build the
  chain in the wrong order, and ADR 0001 requires a specific ordering for the
  hold-margin argument to hold.
- **Cost:** Seven connectors and the crimping.
- **Retrofit:** **One-shot.**

---

# C — Power, rails and current

## 14. **No rail can be current-measured without cutting something, on a project whose lighting budget, thermal clamp and load-switch limit are all sized from currents it intends to measure.**

- **Severity:** High
- **Where:** Carrier (E13), module (E12).
- **What goes wrong:** E1 requires idle current measured "before the carrier is
  laid out"; ADR 0014 sizes the entire 3 W thermal clamp from that number; E6
  requires inrush measured "with a current probe, on switch-on *and* hot-plug"
  and sets the TPS2553 limit from it; ADR 0004 calls the instrument current
  figure "the least trustworthy number in this document" and says to measure it.
  A current probe cannot clamp a PCB trace, and a DMM cannot be inserted into
  one. On a dev board you measure at the USB lead; on the carrier at E14 there
  is nowhere.
- **Provision:** A **2-pin shunt link in series with every rail branch**, so a
  meter can be inserted or a temporary wire loop fitted for a clamp probe:
  carrier — umbilical +12 V total, +12 V → buck, +12 V → REF5050/OPA2197,
  +12 V → strip A, +12 V → strip B, 5 V → display board, 5 V → real-time board,
  5 V → level shifter, 3V3 → shift-register chain. Module — bus +12 V, bus
  −12 V, bus +5 V, +12 V → umbilical branch, +12 V → analog branch. Optionally
  fit a 0.1 Ω 1 % sense resistor with a Kelvin pad pair on the two that matter
  dynamically (umbilical +12 V, and 5 V → display board) so a scope can watch
  the WiFi transient and the LED step the latency budget asks about.
- **Cost:** Fourteen 2-pin headers and shunts, two sense resistors.
- **Retrofit:** **One-shot on the carrier.** These links double as the
  section-isolation provision in finding 15.

## 15. **No section can be powered independently of the others, so a fault that pulls a rail down cannot be bisected.**

- **Severity:** High
- **Where:** Carrier (E13).
- **What goes wrong:** A short or an over-current at first power-on is the
  single most common bring-up event, and the correct response is to bring up one
  section at a time. Here, the module's load switch feeds one umbilical +12 V
  node which feeds everything: two dev boards, two LED strips, the precision
  reference, the analog front end. If the load switch folds back at M7 power-on,
  the only diagnostic available is "something in the instrument is shorted" —
  inside an assembly with seven looms and a hundred solder joints.
- **Provision:** The same shunt links as finding 14, deliberately specified as
  **isolation links** and documented as a bring-up order: umbilical → analog
  front end only → add real-time board → add display board → add strip A → add
  strip B. Check the current at each step against a recorded expected value.
  This also gives E11 and M8 an electrical (rather than physical) way to turn
  the LED strips on and off, which is exactly the variable those two tests
  sweep.
- **Cost:** Shared with finding 14.
- **Retrofit:** **One-shot.**

## 16. **The instrument cannot be powered on a bench without the module, and USB power does not reach the analog front end.**

- **Severity:** Medium
- **Where:** Bench tooling, needed from E2 onward.
- **What goes wrong:** ADR 0005 keeps a diode so "the instrument runs on the
  bench during development without a rack attached" — but USB supplies 5 V, and
  the REF5050, the OPA2197 buffer pair and the WS2815 strips are all on +12 V.
  On USB alone the breath sensor has **no supply at all**: the thing the bench
  session most often exists to debug is the thing that is not powered. The 12 V
  can only arrive through the etherCON.
- **Provision:** Build a **bench umbilical harness** as a named tool in
  `tools/`: an RJ45 breakout to a lab supply (+12 V/PWR_GND), flying leads for
  SCLK/MOSI/CS/DIG_GND to a dev board, and BREATH/AGND to a scope. Cheap,
  off-the-shelf, and it is the single fixture that makes E2, E3, E4, E4b, E10,
  E11 and E14 possible on a bench, and the only way to power a **finished**
  instrument for diagnosis without a rack. Document the pinout next to ADR
  0004's T568B table. Also state plainly in ADR 0005 that USB power runs the
  logic only.
- **Cost:** Under £20, no board change.
- **Retrofit:** Retrofittable, but must exist before E2.

## 17. **The two spare GPIO on the real-time board have at least four claimants, and the decision is currently being made by whoever gets there first.**

- **Severity:** Medium
- **Where:** ADR 0007 pin map, carrier layout (E13).
- **What goes wrong:** GPIO3 and GPIO4 are the only headroom. Candidates already
  visible in the documents and in this review: proxy-flash control of the
  display board (`EN`, `IO0` — two pins), a divided +12 V rail monitor (ADR 0007
  notes both are ADC1 channels), a config-mode input, a heartbeat or fault LED.
  The pin map also collapses to zero spare if E1 finds octal PSRAM. Left
  implicit, these get allocated at layout time by convenience, and the two
  highest-value diagnostic uses lose.
- **Provision:** Rank them explicitly in ADR 0007 **before E13**, and prefer:
  GPIO3 = divided umbilical +12 V sense (rail health, cable degradation, a
  brownout precursor — the etherCON lead is a declared consumable and
  intermittency is its expected failure); GPIO4 = display-board `EN` for proxy
  reset. Push `IO0` onto a spare chain-input bit or onto the external diagnostic
  connector instead. Record the fallback if PSRAM turns out octal.
- **Cost:** A decision plus two resistors.
- **Retrofit:** **One-shot.**

---

# D — Indicators, presence and "what is alive"

## 18. **Nothing on the module says what is alive: one power LED for three rails, a load switch whose FAULT pin is unused, and a watchdog whose state is invisible.**

- **Severity:** High
- **Where:** Module panel and PCB (E12).
- **What goes wrong:** ADR 0004's panel list is "connector, power switch and
  LED". That LED cannot distinguish: rack +12 V present but −12 V missing (a
  row-offset ribbon, the classic Eurorack failure the keyed header is meant to
  prevent and does not always); bus +5 V missing (kills the level shifter and
  therefore all CV, silently); the load switch in foldback because the umbilical
  is crushed or the instrument is shorted; the watchdog holding `CLR` because
  the instrument has hung or been unplugged. All four present identically: the
  patch is silent or stuck, and the power LED is on.
- **Provision:** Five indicators, all single LEDs and a resistor:
  - **+12 V**, **−12 V**, **+5 V** rail presence (three LEDs, on the panel or
    visible on the PCB edge)
  - **FAULT** — drive it from the TPS2553's existing open-drain `FAULT` output.
    This part is already in the BOM and its most useful pin is currently unused.
  - **LINK LOST** — driven from the watchdog's `CLR` assertion, so "no valid
    frame from the instrument" is a light rather than a mystery.
- **Cost:** Five LEDs, five resistors, panel space for two or three of them.
- **Retrofit:** Module board spin; free now.

## 19. **There is no presence or aliveness detect, although the hardware to build one already exists and would test the whole analog chain end to end.**

- **Severity:** Medium
- **Where:** Module (E12).
- **What goes wrong:** ADR 0004 deleted MISO on the argument that +12 V is
  evidence of connection, and the prior review observed that nothing reads it —
  and as finding 11 notes, the node that *is* read is downstream of the panel
  switch, so it is evidence of the switch, not of the instrument.
- **Provision:** Exploit a property the design already has. The MPXV4006DP's
  output floor is **0.2 V at zero pressure**, and the module's receive pair has
  a differential 100 kΩ pulldown, so with no instrument attached `BREATH−AGND`
  is 0 V and with a healthy instrument attached it is ~0.2 V before any breath.
  A single comparator (or a spare op-amp section) with a ~100 mV threshold on
  the in-amp output therefore reports: cable connected, +12 V reaching the far
  end, REF5050 alive, sensor alive and unclipped, buffer alive, both analog
  conductors intact. That is an end-to-end health check of the entire analog
  chain, from one part. Drive an **INSTRUMENT ALIVE** LED with it. (Threshold
  must sit below the minimum commanded ambient-zero offset; the boot value is
  zero, so this is comfortable.)
- **Cost:** One comparator, one LED, three resistors.
- **Retrofit:** Module board spin.

## 20. **The instrument has no "I am alive" indicator that survives a firmware fault, and its two displays are the two things most likely to be broken when you need one.**

- **Severity:** Medium
- **Where:** Carrier and matrix window (E13, M6).
- **What goes wrong:** Both status surfaces are software — the AMOLED is on the
  MCU whose link may be the fault, and the 8×8 matrix is on the MCU that may be
  resetting. ADR 0014 already documents the latch-on-brownout case: strips and
  matrix hold their last colours with no firmware running, which is
  indistinguishable from working. At M7, when the instrument is assembled and
  does nothing, the first question is "is the real-time board running at all?"
- **Provision:** A **hardware heartbeat**: one small LED on the carrier driven
  from a real-time GPIO by the 4 kHz loop itself (toggled in the loop, not in a
  timer callback, so it goes dark if the loop stalls), positioned to be visible
  through the matrix window or through a 2 mm light pipe in the tail. If no GPIO
  can be spared (finding 17), take it from a spare 74x165 bit's LED driver or
  the 74AHCT125's spare gate. Firmware side, define the blink code: solid = boot,
  fast = self-test fail, 1 Hz = running, dark = stalled.
- **Cost:** An LED, a resistor, a 2 mm hole.
- **Retrofit:** **One-shot.**

---

# E — Self-test, calibration and the things firmware must be given hardware for

## 21. **There is no power-on self-test specified, and most of what it would check has no hardware hook.**

- **Severity:** High
- **Where:** Firmware, but the hooks are hardware and land at E13.
- **What goes wrong:** The prior review called a diagnostic mode *"the
  highest-value missing firmware in the project"*; the roadmap responded by
  writing the word "self-test" into M8 with no definition and no milestone.
  Meanwhile the three silent failures the roadmap itself enumerates —
  uncalibrated NVS, stuck-closed switch, stale breath zero — are exactly what a
  POST catches. The risk is that the self-test gets written at M8, discovers it
  needs a hardware hook, and the body is ready to bond.
- **Provision:** Specify the POST **now**, as an ADR, and derive the hardware
  from it. What is achievable with the provisions in this document:

  | Check | Hook | Cost |
  |---|---|---|
  | Precision reference alive and in tolerance | **MCP3202 spare channel** on a divided REF5050 output (finding 22) | 2 resistors |
  | Umbilical rail in tolerance | divided +12 V into GPIO3 (finding 17) | 2 resistors |
  | Cavity temperature | **QMI8658C die-temperature register** (finding 23) | free |
  | Sensor plausible | ADC reading within a window around the 0.2 V floor — below it means a blocked reference port or a dead part, above means a stuck tube | free |
  | Chain integrity, localised | per-register marker bits (finding 12) | free |
  | Stuck key | any key closed at boot | free |
  | IMU alive | `WHO_AM_I` + the part's built-in self-test | free |
  | Link alive, versions match | UART protocol version field | free |
  | Calibration valid | CRC over the NVS blob | free |
  | LED strips | drive a known pattern, watch the 5 V rail current step (finding 14) | free |
  | **CV output chain** | **nothing — no return path (finding 6)** | — |

  Report results on the matrix as a preempting alarm (ADR 0014 already reserves
  this), on the AMOLED, and on the UART0 console.
- **Cost:** A handful of resistors, plus the firmware.
- **Retrofit:** The firmware is retrofittable; **the hooks are not.**

## 22. **The MCP3202's spare channel is unassigned, and it is the instrument's only spare precision analog input.**

- **Severity:** High
- **Where:** Carrier (E13).
- **What goes wrong:** `hardware/bom.csv` notes "one spare channel" and nothing
  claims it. The ratiometric failure ADR 0003 describes — the sensor's supply
  *is* its scale factor — is invisible by construction, because the breath path
  is analog to the jack and there is no division to cancel in. A REF5050 that
  drifts, or its buffer that fails, produces a breath response that is simply
  wrong, forever, with no symptom other than "it does not feel like it used to".
  This is the highest-consequence unmonitored node in the instrument and there is
  a free converter input sitting next to it.
- **Provision:** Wire **MCP3202 CH1 to a divided copy of the buffered 5.000 V
  reference** (same ≥10 kΩ upper-leg rule and 220 nF as the breath branch, for
  the same ESD-clamp and sample-cap reasons). Firmware checks it at boot and
  continuously, reports drift, and raises an alarm on deviation. It also gives
  the ADC a known DC reference against which the breath channel's own gain can
  be sanity-checked.
- **Cost:** Two resistors and a cap.
- **Retrofit:** **One-shot.**

## 23. **Thermal behaviour is central to three ADRs and there is no temperature sensor inside the instrument.**

- **Severity:** Medium
- **Where:** Firmware + the real-time board (free).
- **What goes wrong:** The 3 K/W figure underpinning ADR 0014's entire clamp is
  "a bounding estimate, not a measurement". M8 validates it with a thermocouple —
  once, pre-bond, with a wire that has to come out of the body. After bonding,
  the instrument's thermal model can never be checked again, the breath zero's
  correlation with temperature (ADR 0003's cavity-leak dependency) can never be
  confirmed in use, and the cold-start warm-up signature that distinguishes a
  blocked reference chamber from ordinary drift cannot be re-measured.
- **Provision:** Log the **QMI8658C's die temperature** as permanent telemetry.
  The IMU sits at the bottom of the instrument, in the same zone as the breath
  sensor and the real-time board, which makes it a good proxy for exactly the
  node that matters. It costs one register read, no pin and no part. Validate it
  against the M8 thermocouple so the offset is known, and record the offset.
  Then plot breath zero against it for the life of the instrument.
- **Cost:** Free.
- **Retrofit:** Firmware-retrofittable, but the M8 cross-calibration is one-shot.

## 24. **Pitch calibration is load-specific and expensive to produce, and nothing protects it from being destroyed by a firmware update.**

- **Severity:** High
- **Where:** Firmware, NVS partitioning, `tools/`.
- **What goes wrong:** E9 is described as the milestone that decides whether
  this is an instrument, and ADR 0006 adds that the calibration is specific to
  the patch it was made against, so a per-load scale factor is carried too. That
  data is produced with a VCO, a frequency counter and an afternoon. It lives in
  NVS on a board inside a sealed body. A full-erase reflash, a partition table
  change, or an OTA that moves the NVS offset wipes it — and per the roadmap's
  own silent-failure table, the instrument then plays, sounds like an
  instrument, and is out of tune with no indication.
- **Provision:** (a) CRC the blob and enter a hard **UNCALIBRATED** state — this
  is already decided, keep it; (b) a host tool in `tools/` that **dumps and
  restores** calibration over USB, run before every flash; (c) a dedicated NVS
  partition that a normal flash does not touch; (d) a **printed record** of
  measured points, trimmer positions and the load they were taken against, kept
  in the repo — the finished instrument's calibration should be reproducible
  from a document, not only from a flash chip.
- **Cost:** A small host tool and a habit.
- **Retrofit:** Yes — but only if it exists before the first calibration.

## 25. **Recalibration requires a UI path that does not depend on the phone, the WiFi stack or the display board.**

- **Severity:** Medium
- **Where:** Firmware, plus one spare chain bit.
- **What goes wrong:** Config lives on a phone over SoftAP (ADR 0012), served
  from the display board's flash. Recalibration is a thing that must be possible
  in ten years, after a phone OS has stopped trusting a captive portal, after
  the display board has failed, or with the radio off. E9's own procedure —
  step the DAC to a code, read a meter, adjust — needs a way in that is not the
  web app.
- **Provision:** A **calibration and diagnostic mode over UART0 console**,
  reachable through the diagnostic connector in finding 1: set raw DAC code,
  read raw ADC, dump chain word, dump cal table, run POST, report error
  counters. It is text over a serial port, it needs no phone, and it is the
  natural home for the fixture firmware `firmware/README.md` already puts in
  `fixtures/`. Add a **config-mode entry input** on one of the 14 spare chain
  bits (ADR 0012 already contemplates this) so mode entry does not require a
  gesture the firmware must be working to interpret.
- **Cost:** Firmware, one spare chain bit.
- **Retrofit:** Firmware yes; the connector it needs is one-shot.

---

# F — Ordering, geometry and process

## 26. **Two ADRs place the real-time board in different zones, and the flashing and recovery path depends on which is right.**

- **Severity:** High
- **Where:** ADR 0013 vs ADR 0007/0014, resolved by M4.
- **What goes wrong:** ADR 0013's zone table puts the real-time MCU in the
  **middle** of the body ("mid-body placement halves the worst-case run", with a
  table of run lengths from a mid-body position). ADR 0007 and ADR 0014 put the
  same board at the **very bottom tip**, because that is where the IMU wants to
  be and where the 8×8 matrix must sit to face the tail window. ADR 0009's USB-C
  slot at the tail requires *"that edge of the board at the tail face"*. Only one
  of these can be true. If the mid-body placement wins, the USB-C slot does not
  reach the connector, and finding 3's recovery path evaporates along with E5.
- **Provision:** Resolve in ADR 0013 before M4, and state the consequence for
  the tail face explicitly: the real-time board's USB-C edge, the matrix window
  and the diagnostic connector are one geometric constraint group, and the
  etherCON flange (26 × 31 mm on a 57 × 38 mm face) is already competing with
  them. The 1:1 paper check the roadmap schedules for this face should include
  **all four** openings, not two.
- **Cost:** A decision and a sheet of paper.
- **Retrofit:** **One-shot** — it is the body.

## 27. **No milestone owns the testability provisions, so they will be discovered at E13 and E12 rather than specified into them.**

- **Severity:** Medium
- **Where:** `ROADMAP.md`.
- **What goes wrong:** E13 is one line: "passive carrier: dev boards plug in,
  carrier holds shift registers, ADC, buffer, level shifter, regulator,
  connector." Everything in this document is a carrier requirement and none of
  it appears. E14 then asks for E1–E11 to be re-run on that carrier without
  having required it to expose anything. The provisions are free only while the
  layout is being drawn.
- **Provision:** Add the test point schedule, the LA headers, the isolation and
  injection links, the rail shunt links, the diagnostic connector and the
  heartbeat LED to E13's done-when, and the module equivalents to E12's. Add a
  line to E14: **"every test point, link and diagnostic path is exercised at
  least once"** — a test point that has never been used is a test point that may
  not be connected, and E14 is the last milestone where that is discoverable
  cheaply.
- **Cost:** Editing two table rows.
- **Retrofit:** Yes, now.

## 28. **M8 is the last moment any of this can be proven, and its checklist does not include proving it.**

- **Severity:** High
- **Where:** `ROADMAP.md`, M8.
- **What goes wrong:** M8 is correctly identified as the project's most
  important milestone, and it lists the breath-noise re-run, the thermal soak,
  the play test, failure injection and self-test. What it does not list is the
  **commissioning of the diagnostic apparatus itself**. Everything in this
  document is worthless if it is fitted and never used before the glue.
- **Provision:** Add to M8, as explicit pass criteria:
  - flash **both** MCUs through the external diagnostic connector, with the body
    assembled, using nothing but that connector
  - force the real-time board into download mode using only external access
  - apply a known pressure through the pneumatic port and record the full
    response curve; store it as the as-built reference
  - read the reference monitor, the rail monitor and the IMU temperature; record
    the values and the thermocouple offset
  - verify the plate bond from the U-bolt to the module end, and record the
    resistance
  - provoke each per-register marker error deliberately and confirm the counter
    localises it
  - pull each loom connector in turn and confirm the failure is reported rather
    than silent
  - record idle and full-brightness current at every rail shunt link
  - photograph the interior, and commit the photographs, the harness map, the
    test point map and the as-built values to the repository

  Then bond.
- **Cost:** A day.
- **Retrofit:** **One-shot, by definition.**

---

# Milestone reachability table

"Reachable" is assessed for the milestone as scheduled, and separately for
whether the same measurement can ever be repeated on the finished instrument.

| Milestone | What you would put where | Reachable as scheduled? | Repeatable after M8? | Finding |
|---|---|---|---|---|
| **E1** Board bring-up | USB power meter on the dev board lead; `esp_psram` / eFuse read for quad vs octal | Yes — dev board on a bench | Idle current: **no** rail shunt exists | 14 |
| **E2** Breath sensing | Syringe/pump + reference manometer at the mouthpiece; scope on sensor `Vout`; thermocouple at the sensor; scope on the ADC node | Yes on a breadboard | **No** — no pneumatic port, no sensor-output pad | 4, 7 |
| **E3** IMU | Logic analyser on the IMU I2C | **No.** I2C is on GPIO11/12, onboard and **not broken out**; INT1/INT2 likewise. Software `WHO_AM_I`, built-in self-test and telemetry are the only observation available, ever | No | 21 |
| **E4** Key scan | LA on SPI3 SCK/MISO/latch; scope on `Q_H` at the far end of the chain; error counter over an hour | Only on a breadboard; **no LA landing on the carrier** | Counter only, and it does not localise | 8, 12 |
| **E4b** Inter-MCU UART | LA on the UART1 pair under load | **No landing specified** | **No** unless UART1 reaches the diagnostic connector | 1, 8 |
| **E5** USB MIDI | Host DAW; USB-C at the tail | Yes | Yes — but see the MIDI-vs-recovery PHY conflict | 3 |
| **E6** Module power | Scope on bus ±12 V and +5 V with a short ground; current probe on the umbilical feed at switch-on and hot-plug; scope on LM317 output | Partly — **a current probe cannot clamp a trace**, and rail ripple needs local ground pads | Module is serviceable, so yes | 7, 14 |
| **E7** DAC raw | DMM on each DAC output pin; LA on SPI at the DAC; watchdog disabled | **No** — no output pads, and **the watchdog will clear the DAC between writes** | Module serviceable | 7, 10 |
| **E8** Pitch scaled | DMM at the op-amp output *and* at the jack; screwdriver on two trimmers with the module powered; known code injected at the stage input | Trimmer access with the panel fitted is unspecified; no injection link | Module serviceable | 7, 9 |
| **E9** Pitch calibration | Frequency counter on a real VCO, under the real load; commanded-vs-measured side by side; DC load sweep open/100k/50k/33k | Yes, with a fixture — but needs a non-phone way to step codes | Needs a recalibration path that does not depend on WiFi | 24, 25 |
| **E10** Remaining channels, breath stage | Known differential source into `BREATH`/`AGND` with no instrument; scope at in-amp `OUT`, both pot wipers, the jack; `REF` grounded to isolate the in-amp | **No** — no receive-pair injection pads, no `REF` link, `OE` gating blocks standalone operation | Module serviceable | 9, 11 |
| **E11** Umbilical at length | LA on SCLK/MOSI/CS at the module end of the real cable; scope on the breath jack while sweeping display, LEDs and WiFi; **two-channel end-to-end: sensor output and CV jack** | Module end yes with pads; **the sensor-output channel is inside the instrument** | **No.** The end-to-end latency measurement the budget calls "the one that validates the entire table" can never be repeated | 7, 8 |
| **E12** Module PCB + panel | Paper fit check; stiffness by hand | Yes | n/a | 26 |
| **E13** Carrier | Continuity and power-on bisection before any dev board is seated | **No isolation links, no test points, no LA headers specified** | n/a | 7, 8, 14, 15, 27 |
| **E14** Carrier re-validation | Everything from E1–E11, on a board where the buses sit **under seated dev boards** | **This is the milestone that cannot be performed as written** | n/a | 8, 27 |
| **M2/M3** Layout mule | Live per-key telemetry while playing | Yes, F6 pulled forward | n/a | — |
| **M5** Plate | Continuity plate → `PWR_GND`, recorded | Yes | Only via an externally continuous feature | 5 |
| **M7** Integration | Section-by-section power-up with current at each step; per-loom disconnect | **No shunt links, no loom connectors** | n/a | 13, 14, 15 |
| **M8** Pre-bond gate | Everything, for the last time: breath noise on the final harness, thermal soak at the sensor and the clamp, two-hour play, failure injection, self-test | Yes **if and only if** findings 1–4, 12–15 and 21–23 were built in | **This is the boundary.** After it, only the etherCON, the tail USB-C and the diagnostic connector exist | 28 |

---

# The short list

If only five things are taken from this document, take these. All five are
under £30 combined and all five are unobtainable after M8.

1. **The external diagnostic connector** (finding 1) — console, recovery and
   re-flashing for both MCUs, forever.
2. **BOOT/EN access and a decided flashing path for the display board**
   (findings 2, 3) — the difference between an instrument and a brick.
3. **The pneumatic tee** (finding 4) — the only way to ever ask the breath path
   a question again.
4. **The MCP3202's spare channel on the 5.000 V reference** (finding 22) — two
   resistors that make the instrument's highest-consequence invisible failure
   visible.
5. **Rail shunt links and per-register marker bits** (findings 12, 14, 15) —
   turn "something is wrong in the instrument" into "this branch, this segment".

And one that costs nothing at all: **resolve where the real-time board actually
sits** (finding 26), because three other decisions are downstream of it.
