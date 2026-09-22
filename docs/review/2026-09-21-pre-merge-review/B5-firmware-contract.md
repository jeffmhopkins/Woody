# B5 — What the hardware requires of firmware, and whether firmware knows

Cold pre-merge review, 2026-09-21. Agent B5.

**Method.** Read `firmware/README.md` in full, then enumerated every firmware
obligation asserted anywhere in `hardware/**`, `docs/decisions/**`,
`docs/reference/latency-budget.md`, `config/**` and `ROADMAP.md`, and checked
each against the firmware contract. No `docs/review/**` directory was opened.
Provenance is marked on every claim: `[repo] path:line`, `[calc]`,
`[from memory]`.

**Scope note.** No firmware exists. `firmware/README.md` (170 lines) is the
entire contract. So the question is not "is the code wrong" but "will the
author of the first commit be told". Every finding below is filed against the
thing the obligation acts on — a DAC register, a bus, a chain bit, a loop pass —
rather than against a file, because most of them are one requirement asserted on
one schematic page and nowhere a firmware author would look.

**Headline count.** 12 hardware-asserted firmware obligations are absent from
the contract. 5 statements in the contract or the budget are contradicted by
other corpus documents or are not buildable as written. 4 staleness escapes sit
on figures firmware must consume; the checker passes all four
`[repo] tools/check-staleness.py → "PASS no live stale values | corpus 121 files,
23 circuits | 5 unresolved (tracked)"`.

---

## Part 1 — Obligations the contract does not carry

Ordered by what it costs to discover them late.

### B5-01 — node `SPI2`/`U-ADC` · MCP3202 clock ceiling. The corpus says outright that this is written nowhere.

`spi-link.md` closes the MCP3202 clock question and then states the consequence
itself:

> ESP-IDF sets `clock_speed_hz` per *device* on a shared host, so this is a
> firmware line and not a part change. **It is written nowhere.**
> `[repo] hardware/interfaces/spi-link/spi-link.md:109-111`

It is still written nowhere. `firmware/README.md` contains no SPI clock at all —
not 2 MHz for the DAC, not 0.9 MHz for the ADC, not 1 MHz for the key chain.
The hardware facts behind them are settled and banked: `fCLK` max **1.8 MHz at
5 V / 0.9 MHz at 2.7 V, no 3.3 V row** `[repo] spi-link.md:91-94`; 2 MHz on the
umbilical `[repo] docs/decisions/0004-cv-interface-module.md:61`; 1 MHz on the
key chain `[repo] docs/reference/latency-budget.md:96`.

**Why it bites.** DAC and ADC share SPI2 `[repo] spi-link.md:113-118`. The
natural ESP-IDF mistake is one `clock_speed_hz` for the host. At the DAC's
2 MHz the MCP3202 is **2.2× over its guaranteed maximum** `[calc] 2.0/0.9`, and
the failure is quiet: a SAR that misses its last bits returns plausible counts,
which lands as breath noise and gets blamed on the analog front end.

There is also a **floor** nobody has carried forward: §6.2's 1.2 ms sample-cap
hold gives an effective `fCLK` ≥ ~10 kHz, which "forecloses 'slow the ADC down'
as a way to buy loop time" `[repo] spi-link.md:104-108`. That is a constraint on
a decision a firmware author under budget pressure will actually reach for.

### B5-02 — loop pass · the loop does not close with ESP-IDF driver defaults, and the fix is a firmware line

`loop-budget` is `196-241 us of 250 us`, and its derivation field is explicit:

> Bus time 148-155 us PLUS ESP-IDF per-transaction overhead (24 us interrupt /
> 9 us polling) which no document counted. **291 us with driver defaults - does
> not close.** Polling transactions on an acquired bus are not an optimisation,
> they are what makes 4 kHz reachable.
> `[repo] config/figures.yaml:433-435`

`latency-budget.md:151-160` repeats it. `firmware/README.md` says "**4 kHz
loop** for sensor read and DAC update, pinned to one core" and nothing else. The
single most load-bearing implementation constraint in the project — use
`spi_device_polling_transmit` on a bus held with `spi_device_acquire_bus`, not
the default interrupt transactions — is recorded only in a YAML derivation field
and a blockquote in the latency budget.

At driver defaults the architecture fails at its first integration test, and it
fails as jitter rather than as an error.

### B5-03 — node `VREFOUT` · the reference-enable ordering rule lives on a schematic page

The requirement is asserted once, in the pitch stage's component discussion:

> it carries a firmware requirement: **the reference-enable must be firmware's
> first DAC write**, before any channel data, and it is in the sticky-register
> set that gets periodically refreshed (`firmware/README.md`).
> `[repo] hardware/module/pitch-stage/pitch-stage.md:143-146`

`firmware/README.md` names the internal-reference enable **only** as a sticky
register to refresh — "the internal-reference enable, and the clear-code
register itself" — and never states the ordering. The forward reference on
`pitch-stage.md` points at a document that does not contain the rule it points
at.

**The consequence is stated on three other pages and is not small.** With the
reference disabled, `V_ref` and the DAC term are both zero, so the pitch jack
sits at **0 V — a VCO's base note** — not subsonic
`[repo] pitch-stage.md:134-137`. ADR 0006's power-on table asserts "below −2 V";
`pitch-stage.md` records that these "are different states, 2.5 V apart"
`[repo] pitch-stage.md:137-138`. ADR 0006 separately warns this is "a known
DAC8568 bring-up surprise — a board that looks dead at E7 with every channel
reading 0 V" `[repo] docs/decisions/0006-cv-channel-allocation.md:224-228`. And
`breath-receive-stage.md:43` marks `VREFOUT` "disabled until firmware enables
it" in its interface table.

Four pages depend on the write. None of them is `firmware/README.md`.

### B5-03b — same node · "first write" is the wrong shape of rule for this hardware, and nothing states the right one

The module is powered through its own panel toggle `SW-POWER` into the load
switch's UVLO `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:16`,
with a gate ramp of **49–197 ms (98 ms typ)** `[repo] config/figures.yaml:347`.
The module can therefore be switched on minutes after the instrument booted, and
the DAC does a fresh power-on reset when it is — reference disabled again.

"First DAC write" does nothing for that case. The only thing that recovers it is
the periodic sticky-register refresh, and `firmware/README.md` bounds that
refresh only as "**a word every few thousand passes**". At 4 kHz that is roughly
0.5–1 s `[calc] 3000/4000 = 0.75 s`, during which pitch sits at 0 V on every
module power-up — audible, and exactly the symptom ADR 0006 predicts will be
misread as dead hardware.

No document in the corpus states a bound for that refresh period. It should be
one, and it should be derived from "the longest a wrong output may stand", not
from budget slack.

### B5-04 — chain bits 6,7,14,15,20,21,29,30 · the marker protocol

ADR 0001 and the marker page both state the firmware side of the framing check:

> Firmware checks the marker on every read; a frame that fails it **holds the
> previous frame** rather than acting on garbage, and increments a **visible
> error counter**.
> `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:325-328`

> A marker is a framing check: firmware reads it every scan, and a frame that
> fails it holds the previous frame and increments a visible error counter.
> `[repo] hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:53-55`

`firmware/README.md` does not mention the marker, the hold-previous-frame rule,
or the counter. The word "marker" does not appear in it.

Three further facts firmware needs and is not told:

- **The pattern itself** — `1 0 · 0 1 · 0 1 · 0 1` in bit order, with the
  per-device levels `[repo] key-marker-and-bits.md:99-107`. The page closes
  with "**firmware has to be told the pattern**"
  `[repo] key-marker-and-bits.md:120-121`, and the levels are still marked
  "Proposed".
- **The counter undercounts about 4×** — "a single-bit flip is caught **8 times
  in 32**, and the 24 bits that carry the music are never among them"
  `[repo] key-marker-and-bits.md:109-113`. Any alarm threshold set on that
  counter has to be set knowing it sees a quarter of the corruption.
- **Alarm display is mandatory** — "the key-chain marker error count to be
  visible", and alarm states "cannot be configured off"
  `[repo] docs/decisions/0014-lighting.md:343-352`, echoed at
  `[repo] ROADMAP.md:146` (F9).

This is the cleanest instance of the failure mode this slice was set up to find:
a protocol firmware must implement, asserted only inside a schematic directory
about copper straps.

### B5-05 — key press path · the two-sample rule contradicts the contract, and two other documents take the contract's side

ADR 0001, in a section headed "Two firmware rules the chain depends on":

> **Require two consecutive agreeing samples before a note-on.** At the 4 kHz
> loop rate that is 250 µs of added latency — inadible \[sic: "inaudible"\], and
> a twentieth of the 5 ms budget. […] This keeps the asymmetric debounce's fast
> attack while removing its single-sample credulity.
> `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:314-321`

Against that:

- `firmware/README.md`: "**Asymmetric key debounce** — fire immediately on
  press, filter only the release."
- `[repo] docs/reference/latency-budget.md:97`: "| Debounce (press) | 0 — fire
  immediately |"
- `[repo] hardware/cluster/key-switch-network/key-switch-network.md:107-108`:
  "**Press is instant on the scan's timescale and release is filtered**".

ADR 0001 reconciles the two in its own prose; no other document knows the
reconciliation exists. A firmware author reading the contract implements
single-sample note-on, and the latency budget's key path confirms them with a
literal zero. The 250 µs the rule costs is not in the key path table either, so
the budget is wrong by one loop period on the one path the project calls most
latency-sensitive.

`firmware/README.md` also correctly requires the release window to come from
**measured** KS-33 bounce at M1 — that part is stated and is not a defect.

### B5-06 — strips `J-LED-L`/`J-LED-R` and the 8×8 matrix · four firmware rules, none of them in the contract

`firmware/README.md`'s lighting section carries exactly three numbers — zero,
deadband, span — and correctly sources the deadband from E2's measured standard
deviation. It carries none of ADR 0014's actual firmware rules:

1. **The thermal clamp.** "A single instrument-wide lighting budget of ~3 W,
   summed across both strips and the matrix, **enforced in firmware before any
   write**. When the commanded total exceeds it, **scale everything down
   proportionally** rather than refusing the write."
   `[repo] docs/decisions/0014-lighting.md:171-175`
2. **Blank first at boot.** "**Blank both strips *and the matrix* as the first
   act at boot**, before anything else initialises."
   `[repo] 0014-lighting.md:214-218`, restated `[repo] 0014-lighting.md:448`.
   The carrier page depends on this rule existing and then explains why it
   cannot cover the window that matters: GPIO1/GPIO2 are high-Z for the
   bootloader window, so `R-LED-PD` was added as the hardware half of the same
   defence `[repo] hardware/carrier/led-strip-drive/led-strip-drive.md:46-56`.
3. **Constant-current animation.** "**Animate by moving light, not by changing
   how much of it there is.** Render a dot, a bar or a field whose *total
   current* is held constant, and move or recolour it. Fades, pulses and
   whole-field brightness sweeps modulate the supply that pitch is referenced
   to." — with "Where a fade is genuinely wanted […] take it while no note is
   sounding." `[repo] 0014-lighting.md:520-531`. This one is priced: four
   independent coupling routes from LED current to the pitch jack, "adding to
   more than every static term in ADR 0006's precision budget put together, and
   unlike those terms **they move while you play**"
   `[repo] 0014-lighting.md:513-517`.
4. **Alarms preempt and cannot be configured off.**
   `[repo] 0014-lighting.md:341-352`.

Rule 3 is the expensive omission. It is a rule about *how to write an animation
loop*, it has no hardware backstop, and a firmware author who has never read
ADR 0014 will write a breath-driven brightness fade on day one because that is
the obvious thing to write.

### B5-07 — real-time core · IRAM placement, and the config round-trip that stalls the loop

> **An ESP32-S3 NVS commit or OTA write disables the instruction cache** and can
> stall non-IRAM code on both cores. With no watchdog there is no `CLR` to fire
> mid-note, so the consequence is now a *stalled refresh* rather than a reset:
> the jacks hold their last value for the duration of the stall […] Still worth
> measuring, and **the DAC service routine still belongs in IRAM**.
> `[repo] hardware/module/digital-and-supervision/digital-and-supervision.md:78-84`

`firmware/README.md` does not mention IRAM, the instruction cache, or NVS
commits stalling the loop. It does, two sections later, mandate the thing that
triggers the stall:

> The phone edits, the display board forwards, **the real-time board validates,
> applies, persists** and echoes back.

Persisting is an NVS commit, on the real-time board, at the player's convenience
— i.e. potentially while a note is sounding. The contract requires the write and
is silent about its cost; the cost is recorded on a module schematic page under
"Still open". These two statements need to meet, and the place they must meet is
`firmware/README.md`.

### B5-08 — node `DAC ch1` · pitch must jump the round-robin, which is a seventh word the budget does not book

> | Pitch | **4 kHz**, plus **immediate update on note change** | Static between
> notes; what matters is latency at the transition, not rate |
>
> Pitch is the subtle one: it needs no *rate*, but it must not wait for its turn
> in a round-robin. **Push it the instant the note resolves.**
> `[repo] docs/decisions/0006-cv-channel-allocation.md:245,252-253`

Absent from `firmware/README.md`. It also interacts with B5-02: the budget books
**six** 32-bit DAC words per pass `[repo] latency-budget.md:62`, and an
out-of-turn pitch push is a seventh, costing 16 µs at 2 MHz
`[calc] 32 bits / 2 MHz = 16 µs` plus one more transaction overhead (9 µs
polling) — ~25 µs into a pass already at 196–241 µs of 250. On note-change
passes the budget is at or past its ceiling. Nobody has written that down.

### B5-09 — calibration and persistence · the contract's NVS list does not include calibration at all

`firmware/README.md` §"Data, not code" lists exactly two things in NVS: the
fingering table and the routing matrix. Calibration is not among them, and the
word "calibration" does not appear in the contract. What the corpus requires:

- **A per-load affine `(gain, offset)` pair, not a scale factor.** "Correcting
  only the slope […] leaves the offset short by `(1 − k_new/k_trim) × 2.5 V`.
  Trimmed against 100 kΩ and then played into 50 kΩ, that is **+29 cents sharp
  on every note**; into 33 kΩ, **+59 cents**. A one-number correction therefore
  converts a progressive tracking error into a *constant* transposition, which
  is worse to play than the error it replaced."
  `[repo] 0006-cv-channel-allocation.md:530-540`, restated at
  `[repo] 0006:577-582` — "**Two numbers, not one**".
- **A multi-point NVS table** on top of it, for DAC INL. "the multi-point NVS
  table handles the rest" `[repo] 0006:786`; "**Firmware handles what trimmers
  cannot:** DAC integral nonlinearity" `[repo] 0006:474`;
  "firmware's multi-point correction, not a trimmer's job"
  `[repo] hardware/module/pitch-stage/notes.md:64`.
- **Anchor points inside the musically used range**, not at −2 V / +7 V.
  `[repo] 0006:781-786`.
- **Named presets per patch** — "one VCO", "two multed" — with a display line
  `[repo] 0006:577-582`.
- **±600 cents of offset authority** is what the 0.25–4.75 V DAC window exists
  to reserve `[repo] 0006:543`, `[repo] pitch-stage.md:139-142`,
  `[repo] mod-channels.md:145-148`. Firmware must not spend that window on
  anything else, and is not told so.

`ROADMAP.md:147` (F8) says "Config and calibration in NVS; presets" — one line,
in a milestone table, which is the only place in the corpus where calibration
and NVS appear in the same sentence outside ADR 0006's argument.

### B5-10 — breath digital copy · the auto-zero is referenced by the contract but never specified anywhere the contract points

`firmware/README.md` mentions the auto-zero exactly once, in passing, as a
consumer of the deadband figure: "the auto-zero's 'quiet' gate needs the same
figure". It never says there is an auto-zero, what gates it, or what it must
report. Its "Zero — the power-on ADC capture" describes only the **seed**.

The specification is in ADR 0006 and is unusually complete:

- Seed from an ADC capture at power-on, then "**decay it toward the current
  reading whenever breath has been sub-threshold for about 2 seconds**"
  `[repo] 0006:288-292`.
- **Sub-threshold is not sufficient** — it "eats a sustained pianissimo, and it
  re-zeros during the catch-breath of a circular-breathing passage"
  `[repo] 0006:296-299`.
- **Gate on "sub-threshold *and* quiet"**, where quiet means "the signal's
  standard deviation is below about 2× what it measured at commissioning — the
  same stillness-gated estimator ADR 0007 already uses for IMU bias"
  `[repo] 0006:307-312`.
- **Log the accumulated correction**, "visible on the display and in the web
  app" — because otherwise the auto-zero silently absorbs "a partially blocked
  PTFE restrictor, a cavity that has started sealing, or a shifted sensor
  offset" `[repo] 0006:300-306, 314-318`. ADR 0004 leans on this same log as
  the only detector for a stuck sensor `[repo] 0004:527-531`.

`ROADMAP.md:140` (F2) carries a compressed correct version — "seeded at
power-on, then gated on sub-threshold AND quiet" — which is more than the
firmware contract says.

**Commissioning dependency, unstated:** the quiet gate needs a commissioning-time
standard deviation stored in NVS. Nothing says who captures it, when, or what
firmware does if it is absent — which is the same class of hole as the
uncalibrated case in B5-12a.

### B5-11 — mod and breath defaults

> **Default every mod and breath range to 0–8 V.** The mod channels *can* do
> ±10 V, but that is headroom, not a default […] **Bipolar is opt-in per
> channel**, set explicitly from the display, so nothing sends a negative
> voltage into a patch that was not asked to receive one.
> `[repo] 0006-cv-channel-allocation.md:773-778`

Absent from `firmware/README.md`, whose routing-matrix bullet lists "source,
scale, offset, curve and slew" and no defaults. This is a safety default with a
named rationale, in a section literally headed "Firmware defaults and bring-up
rules" — a section `firmware/README.md` does not cite.

### B5-12 — the three silent failures: one named, two absent, and none specified

`ROADMAP.md:209-221` states "All three fixes are firmware and all three are
free." Checked one at a time against the contract:

**B5-12a — blank or corrupt NVS → default calibration.** Fix: "CRC the
calibration blob; a hard **UNCALIBRATED** state on the display the player cannot
miss." `[repo] ROADMAP.md:217`. Not in `firmware/README.md` — no CRC, no
checksum, no UNCALIBRATED state, and per B5-09 no calibration blob in its NVS
list at all. ADR 0014 independently requires the same state to be unmissable on
the matrix `[repo] 0014:346`. **Not specified.** Also unspecified anywhere: what
the instrument *does* when uncalibrated — refuse to play, play on defaults, or
something else. That is a behavioural decision with no owner.

**B5-12b — stuck-closed switch.** Fix: "Flag any key closed at boot, or held
beyond N seconds, as suspect and report it." `[repo] ROADMAP.md:218`. Not in
`firmware/README.md`. `N` is unbound everywhere in the corpus. A held key is
also a legitimate playing state, so `N` is a real design decision, not a
placeholder — and the marker straps explicitly cannot catch this class: "the
straps go direct to the rails, so they share no component with the 21 key
networks they are read as vouching for"
`[repo] key-marker-and-bits.md:113-115`. **Named, not specified.**

**B5-12c — stale breath zero.** Fix: "Continuous auto-zero (ADR 0006), plus
showing the current zero on the display." `[repo] ROADMAP.md:219`. See B5-10:
the contract's only breath zero is "the power-on ADC capture", which is the
failure, not the fix. The display requirement appears nowhere in
`firmware/README.md` (its display section says "The display shows status only"
and does not enumerate the status). **Not specified, and the contract's one
sentence on the subject states the superseded behaviour.**

Score: 0 of 3 specified in the firmware contract; 1 of 3 (F2) partially
specified in the ROADMAP's own milestone table.

---

## Part 2 — Told to do what the hardware cannot do, or what another document denies

### B5-13 — the contract contradicts itself about where the display runs, inside the list it calls non-negotiable

`firmware/README.md`, "Architecture constraints […] not negotiable without
revisiting those", bullets 2 and 5:

> - **Display renders on the other core, on its own SPI host.** A display
>   refresh must never block the output loop.
> - **WiFi and the display are on the other MCU.** They cannot preempt the
>   output loop.

Both cannot be true. ADR 0013 moved the display to a separate chip joined by
UART1 `[repo] docs/decisions/0013-two-mcu-split.md:30,51`, and
`display-and-service-uart.md:57` fixes that link as "IO5 → display RX, IO6 ←
display TX — UART1, 921600 baud". There is no display SPI host on the real-time
board and no display rendering on either of its cores.

Worse, bullet 2 is **not buildable**. Both usable SPI hosts on the real-time
board are claimed: SPI2 carries DAC8568 + MCP3202 on GPIO35/36/37 with CS on 34
and 39, SPI3 carries the key chain alone on GPIO38/40
`[repo] docs/decisions/0007-imu-selection.md:186-190`,
`[repo] spi-link.md:113-118`. "Its own SPI host" does not exist.

The same stale framing is live in two more corpus documents:

- `[repo] docs/reference/latency-budget.md:184-190` — rule 3 "Separate SPI host,
  separate core", immediately followed by rule 4 "The WiFi stack and display are
  on a different MCU entirely (ADR 0013)". Two adjacent numbered rules, one
  refuting the other.
- `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:44-47` — "The whole
  timing architecture here is a core split: sensor, key scan and DAC output own
  one core; display, WiFi and web server own the other." This is the origin, and
  it is the ADR `firmware/README.md` cites as the source of the constraint.

This is the single most consequential defect in this slice. The firmware
contract's opening architecture list tells its reader to reserve a core and a
bus for a peripheral that is on another chip, and the reader has no way to know
which bullet wins. **What the other core actually runs is unstated everywhere** —
USB MIDI, the UART1 link, LED rendering, NVS commits and the web-config
validation all have to live somewhere, and no document assigns them.

### B5-14 — display board recovery: the contract states an outcome whose mechanism the hardware forecloses

`firmware/README.md`:

> **The display board is flashed over its UART, by the real-time board.** That
> closes ADR 0013's open question and **removes the one case where a board with
> no external connector of its own needed hardware recovery.** It gets the same
> two OTA partitions.

ADR 0013 says the same `[repo] 0013-two-mcu-split.md:292-295`. But the display
board's `EN` and `IO0` are deliberately not wired:

> **`HDR-SERVICE` is therefore 2×3, six pins, not 2×5** — a UART pair and a
> ground for each board, and nothing else. […] **No EN, no IO0, and so no RC
> networks for them.**
> `[repo] hardware/carrier/display-and-service-uart/display-and-service-uart.md:44-64`

Without `IO0` low at reset there is no route into the S3's ROM serial bootloader
`[from memory]`, so the real-time board cannot run an esptool-style flash. The
only available mechanism is an **application-level OTA responder inside the
display image**, reachable over UART1. That works precisely when the display
image is healthy, and fails precisely when it is not — which is the case the
sentence claims to remove. Its own USB "is inside a bonded body and reaches
nothing" `[repo] 0013:294`.

The claim is an overclaim, and it is load-bearing for a body that bonds shut.
What the contract should carry instead: the display image's UART OTA responder
must be reachable independently of the application's own state — from the
bootloader, from the rollback slot, or from a minimal responder that starts
before the rest of the image — and rollback (`CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE`,
which the contract already requires for the real-time board) must be enabled on
the display board too. None of that is written.

### B5-15 — the 8×8 matrix has no assigned drive method, and its one documented method collides with SPI2

The matrix is "64 `WS2812B-0807` parts on GPIO14, chained, **driven over SPI2 in
Zephyr's configuration**" `[repo] docs/decisions/0007-imu-selection.md:176`. In
Woody, SPI2 is the DAC + ADC bus at 4 kHz (B5-13), so that method is unavailable.

ADR 0014 assigns the two **strips** explicitly — "The ESP32-S3 drives both on
separate RMT channels without effort"
`[repo] docs/decisions/0014-lighting.md:54-57` — and says nothing about the
matrix. So the corpus assigns a drive method to 2 of the 3 LED outputs.

This matters to the loop, not just to tidiness: a 64-pixel WS2812 frame is
**1.92 ms** of 800 kHz data `[calc] 64 × 24 bits / 800 kHz`, or 7.7 loop periods.
On RMT/DMA it is background; bit-banged or on a blocking driver it destroys the
4 kHz loop outright. The contract says nothing, and an author with both SPI hosts
already claimed will reach for the obvious thing.

### B5-16 — the IMU is in the contract's job list, in no budget, and has no stated rate

`firmware/README.md`: "`realtime/` — ESP32-S3. Keys, breath, **IMU**, DAC loop,
USB MIDI."

`docs/reference/latency-budget.md` does not contain the string "IMU". The
`loop-budget` derivation counts DAC, ADC, key chain and driver overhead only
`[repo] config/figures.yaml:433-435`. The IMU is on **I2C**, not SPI —
"| I2C: IMU | 2 | **no** — onboard, GPIO11/12 |"
`[repo] docs/decisions/0013-two-mcu-split.md:51`, confirmed by CircuitPython's
pin names at `[repo] docs/decisions/0007-imu-selection.md:172-174`.

`[calc]` A 12-byte accel+gyro burst on I2C is ~13 bytes × 9 bits = 117 bit-times;
at 400 kHz that is **293 µs**, longer than the entire 250 µs loop period; at
100 kHz, 1.17 ms. The IMU therefore **cannot** be read synchronously in the
4 kHz loop, and no document says so or says what rate it should be read at.
ROADMAP E3's acceptance is "Tilt and roll angles read reliably **at rate**"
`[repo] ROADMAP.md:43` — with "at rate" undefined.

ADR 0007's own requirements bound it from below: the complementary filter, the
stillness-gated bias estimator, and specifically "End the pre-press sampling
window **~50 ms before the press**" `[repo] 0007:122-124` — which needs enough
history at a known cadence to have a valid estimate 50 ms back. That is a
sampling-rate requirement nobody has turned into a number.

### B5-17 — ADR 0006's update-rate table still lists a DAC channel that was deleted

> | Breath zero offset | continuous, slow | See the auto-zero rule below |
> `[repo] docs/decisions/0006-cv-channel-allocation.md:247`

This row sits in a table headed "Channels do not share an update rate", between
"Mod 1–4" and "Mod offset (ch 7)" — i.e. among DAC channel rows. The breath
ambient-zero channel is deleted: "**Channel 6 was freed deliberately**"
`[repo] 0006:25`; "The breath ambient-zero channel that briefly made it seven is
deleted (ADR 0003)" `[repo] latency-budget.md:180-181`; "Nothing claims the
freed channel; leaving it unclaimed is the point" `[repo] 0006:31`.

The adjacent row was corrected on 2026-09-21 and carries its own refutation
note; this one was not. A firmware author reading the channel-rate table as a
channel-rate table writes a seventh DAC channel — which is the exact class of
bug `firmware/README.md`'s statelessness section exists to prevent, arriving
from the opposite direction. No grep finds it: every token in the row is
individually true of the digital zero.

### B5-18 — ADR 0003 still books the ADC conversion at the value the latency budget says decides whether 4 kHz is buildable

`[repo] docs/decisions/0003-breath-sensing-path.md:22`:

> | SAR ADC conversion | ~50–200 µs |

`latency-budget.md` refutes this at length and books 24 µs, with a boxed warning:
"**This page gave two different figures for the same ADC read, and the gap
decides whether 4 kHz is buildable.** […] At 200 µs a pass costs **312 µs against
a 250 µs period and the loop does not close**"
`[repo] latency-budget.md:164-171`. The `loop-budget` forbidden list carries the
pattern `"SAR ADC conversion ~50"` `[repo] config/figures.yaml:436`.

ADR 0003 spells it as a table cell — `| SAR ADC conversion | ~50–200 µs |` — with
pipes and spaces, so the literal match misses by two characters. **The checker
passes** `[repo] tools/check-staleness.py`. This is the exact escape mechanism
`sensor-full-scale`'s `escape_note` records — "a table cell with pipes"
`[repo] config/figures.yaml:80` — recurring on a different figure.

ADR 0003's table is the second-most-likely place a firmware author looks for the
breath path's timing, and it is unrefuted there.

---

## Part 3 — Staleness escapes on figures firmware must consume

All four pass `tools/check-staleness.py`. Filed here rather than to a staleness
slice because each is a number firmware reads.

### B5-19 — `key-release-time` is restated stale on the page that owns it

`[repo] hardware/cluster/key-switch-network/key-switch-network.md:109`:

> `[repo] 0001`. The **125 µs** release filter is half a scan period and costs
> nothing musically; note-off is filtered in firmware anyway.

`key-release-time` is **119.9 us**, owner
`hardware/cluster/key-switch-network/key-switch-network.md`
`[repo] config/figures.yaml:149-153` — this page. Four lines above, its own
table says "crosses `V_IH` at **119.9 µs**"
`[repo] key-switch-network.md:103`. The forbidden list carries
``"`V_IH` at **125"`` `[repo] config/figures.yaml:157`; this spelling is a bare
"125 µs" followed by "release filter" and escapes it. The `false_positive_note`
warns that a bare 125 µs legitimately means the mean sampling period and the
8 kHz period `[repo] config/figures.yaml:158` — and this occurrence is neither.
Third recorded instance of an owner document contradicting its own figure.

Firmware consequence: it is the hardware release-filter figure the firmware
debounce window is sized against, and it is 4 % long on the owner page.

### B5-20 — `marker-bits` is restated stale on `carrier.md`

`[repo] hardware/carrier/carrier.md:378-379`:

> **Two items left this page with the registers.** The **marker pattern**
> (which **six bits**, to what levels) and the **`H`…`A`-to-switch mapping** are
> now `PCB-CLUSTER` decisions

`marker-bits` is **8 bits**, DECIDED 2026-09-21
`[repo] config/figures.yaml:171-177`. Forbidden patterns are
`"Four to six of the"`, `"4-6 are claimed"`, `"six bits carry the marker"`,
`"**6 marker"` — the parenthetical "(which six bits, to what levels)" matches
none. The sentence continues "both still have to be **told to firmware**", so it
is a live instruction about firmware's input carrying the superseded width.

### B5-21 — `config/key-layout.yaml` points firmware at a section that no longer exists

`[repo] config/key-layout.yaml:129-130`:

> #   fails its own marker whichever way it broke. See
> #   hardware/cluster/cluster-boards.md section 4 for the bit assignment.

`cluster-boards.md` has sections headed `§3` and `§5` and no `§4`
`[repo] hardware/cluster/cluster-boards.md:104,115` — §4 moved to
`hardware/cluster/key-marker-and-bits/key-marker-and-bits.md` on 2026-09-21
`[repo] key-marker-and-bits.md:3-5`. This is the only pointer in the corpus from
firmware's own data file to the bit assignment firmware must implement, and it
resolves to nothing.

`config/**` is corpus, not a historical record `[repo] CLAUDE.md:83-85`, so
CLAUDE.md §6's "paths in those records are not to be corrected" does not apply —
this one is live and broken.

### B5-22 — `docs/decisions/0006:331` — "breath locked to channel 2"

> With breath locked to **channel 2** there is no genericity conflict, so the
> knobs sit directly in the analog path
> `[repo] docs/decisions/0006-cv-channel-allocation.md:331`

The same ADR's allocation table reads "| **Mod 1–4** | DAC ch 2–5 |" and puts
breath outside the DAC entirely `[repo] 0006:11-13`. "Channel 2" here must mean
the second *panel jack*, not DAC channel 2 — but the ADR uses "channel" for DAC
channels in the surrounding forty lines, and this is the ADR named "CV channel
allocation". Low severity, high blast radius if read the other way: it names
breath onto Mod 1's DAC channel. Disambiguate to "the breath jack".

---

## Part 4 — The budget's terms against what firmware is told to do per pass

Asked directly, because the task asks for the terms and for what the budget does
not count.

**What `loop-budget` counts** `[repo] config/figures.yaml:429-435`,
`[repo] latency-budget.md:141-160`:

| Term | Time | Bus |
|---|---|---|
| DAC, 6 × 32 bits @ 2 MHz | 96.0 µs | SPI2 |
| ADC, 24 clocks @ 0.9 MHz | 26.7 µs | SPI2 |
| Key chain, 32 bits @ 1 MHz | 32.0 µs | SPI3, concurrent |
| ESP-IDF per-transaction overhead | 9 µs polling / 24 µs interrupt each | — |
| **Total** | **196–241 µs of 250 µs (78–96 %)** | |

**What it does not count**, each of which the corpus separately requires firmware
to do:

1. **The IMU read** — B5-16. Not in the table, on a different bus, arithmetically
   incapable of fitting.
2. **LED frame assembly and the 3 W clamp** — B5-06, B5-15. 114 pixels total
   (2 × 25 WS2815 + 64 matrix) `[repo] led-strip-drive.md:52`, `[repo] 0007:176`.
3. **Anything computational.** Fingering-table lookup, per-channel smoothing,
   breath curve shaping, the four-channel routing matrix (source/scale/offset/
   curve/slew), and the multi-point pitch interpolation are all required
   `[repo] ROADMAP.md:139-143`, `[repo] firmware/README.md` — and the budget is
   bus time plus driver overhead only. The key path table's "Firmware note
   resolution | < 20 µs" `[repo] latency-budget.md:99` is a latency row, not a
   loop-duty row, and is not in the 196–241 µs.
4. **The seventh DAC word on note change** — B5-08, ~25 µs.
5. **The two-sample note-on confirmation** — B5-05, 250 µs of latency absent from
   the key path table.
6. **UART1 status traffic to the display at 921600 baud**
   `[repo] display-and-service-uart.md:57`, and the WebSocket telemetry F6
   requires feeding it `[repo] ROADMAP.md:145`.
7. **USB MIDI**, when enabled `[repo] firmware/README.md`.
8. **NVS commits stalling both cores** — B5-07.

At 78–96 % duty before any of the eight, the honest statement is that the loop
budget is a **bus** budget, not a loop budget, and nothing in the corpus says so.
`latency-budget.md` is candid that 4 kHz "is not comfortable"
`[repo] latency-budget.md:150` and that the measured ADC round trip is "a gate on
the architecture, not a refinement of it" `[repo] latency-budget.md:176-178`.
That candour should extend to the compute terms: **the figure's name promises
more than its derivation delivers**, which is how `loop-budget`'s own
`escape_note` describes the last time this went wrong
`[repo] config/figures.yaml:437-455`.

One stale cross-reference found while checking the terms: `breath-adc.md`'s
warning says "`latency-budget.md` and ADR 0003 book 'SAR ADC conversion
~50–200 µs' and **no RC term at all** `[repo]` […] Found by
`R10-keyscan-and-adc.md` §B-2 and **still unapplied**"
`[repo] hardware/carrier/breath-adc/breath-adc.md:66-71`. It has been applied in
`latency-budget.md` — the 282 µs anti-alias row is there
`[repo] latency-budget.md:58` and the ADC row is 24 µs
`[repo] latency-budget.md:60`. The warning is now half wrong: still true of
ADR 0003 (B5-18), no longer true of the latency budget.

---

## Part 5 — The statelessness rule: verified, and it is the one thing this corpus does right

Checked as asked, because it is the rule most depended on.

**Stated once**, in `firmware/README.md`, as a rule and not a note: "**Refresh
everything, every pass. Never write-on-change.** […] *With no readback, shared
state can only be made safe by being made stateless.* This is the rule, not an
optimisation note".

**Cited by name from five places that depend on it**, none of which restates the
mechanism:

| Where | What it depends on the rule for |
|---|---|
| `[repo] docs/decisions/0004-cv-interface-module.md:64-66` | the 2 MHz umbilical clock — six channels, not five |
| `[repo] docs/decisions/0006-cv-channel-allocation.md:248` | ch 7's "refreshed every pass" row |
| `[repo] hardware/module/mod-channels/mod-channels.md:177-181` | the +11.45 V mirror-image failure being closed |
| `[repo] docs/reference/latency-budget.md:62,178-181` | the six-word booking |
| `[repo] hardware/module/link-supervision/link-supervision.md:61-64` | why the 74HC123 watchdog could not work and was deleted |

That is the `USB MIDI opt-in` pattern CLAUDE.md §1 holds up as the model, applied
to a second fact, and it holds. `firmware/README.md`'s "Why statelessness,
specifically" section is also the one place in the corpus where a rule's *stated
cause* was deliberately re-grounded after the cause was deleted — the watchdog
→ power-on-reset + `LK-CLR` rewrite — with the reason for the rewrite left in
place. That is the right treatment and should be the template.

**Two gaps against it, both minor:**

- The sticky-register set it enumerates is "the internal-reference enable, and
  the clear-code register itself". The DAC8568 frame also carries a **software
  reset** and an **LDAC register** `[repo] spi-link.md:162-166`,
  `[repo] hardware/module/dac8568/notes.md:23-31`. `[calc]` LDAC-register
  corruption is benign here because `R-LDAC` is a 0 Ω strap to GND, so both
  register states behave identically; a spurious software reset is caught by the
  reference-enable refresh within the refresh period. So the enumeration is
  *adequate* — but it is adequate by accident, and the reasoning is not written.
- The refresh period is unbounded — B5-03b.

**Verified not a defect** (checked because they look like ones):

- `firmware/README.md` restating **3.3333 V** rather than citing `mod-reference`
  is a **sanctioned** exception: "which is why `firmware/README.md` states the
  value rather than deriving it" `[repo] mod-channels.md:16`. The price is that
  a future move of `mod-reference` must reach `firmware/README.md`, and the
  figure's `forbidden` list should get a pattern matching firmware's spelling
  when that day comes.
- **Write order within a pass is immaterial.** `LDAC` is strapped to GND, so
  channels update as each word lands `[repo] dac8568/notes.md:23-31`. With
  `V_ref` constant in steady state, ch 7's position in the round-robin has no
  effect; the only transient is the documented, accepted 100–200 µs at `CLR`
  exit, which "no write order avoids" `[repo] dac8568/notes.md:38-41`. Not a
  gap.
- **The mod topology needs no firmware sign flip.** `Vout = 4·Vdac − 3·V_ref` is
  non-inverting in `Vdac` `[calc]`: at `Vdac`=0, −10.000 V; at 5 V, +10.000 V.
  The "firmware sign flip" in `mod-channels/notes.md:35,90` belongs to the
  rejected single-inverting-amp alternative only, and both occurrences sit in
  past-tense shelved text. Not a live obligation.
- **Breath is genuinely outside all of it.** Consistent across
  `[repo] firmware/README.md`, `[repo] 0003:610-623`, `[repo] 0006:25-31`,
  `[repo] breath-receive-stage.md:213-220`, `[repo] 0004:505-520`. No DAC
  register touches the breath jack; firmware's zero is a subtraction on its own
  ADC copy. Five documents, one story.

---

## Summary table

| # | Node / subject | Obligation | Where it is stated | In `firmware/README.md`? |
|---|---|---|---|---|
| B5-01 | `SPI2` / `U-ADC` | per-device `clock_speed_hz`, ADC ≤ 0.9 MHz, ≥ ~10 kHz floor | `spi-link.md:104-111` ("written nowhere") | **no** |
| B5-02 | loop pass | polling transactions on an acquired bus, or 4 kHz does not close | `figures.yaml:433-435`, `latency-budget.md:151-160` | **no** |
| B5-03 | `VREFOUT` | reference-enable must be the first DAC write | `pitch-stage.md:143-146` only | **no** (register named, ordering not) |
| B5-03b | `VREFOUT` | bound the sticky-register refresh period | nowhere | **no** |
| B5-04 | chain marker bits | check every scan, hold previous frame, visible counter, pattern, 4× undercount | `0001:325-328`, `key-marker-and-bits.md:53,109-121` | **no** |
| B5-05 | key press | two agreeing samples before note-on | `0001:314-321` | **contradicted** |
| B5-06 | strips + matrix | 3 W clamp before any write; blank first at boot; constant-current animation; alarms preempt | `0014:171-175,214-218,341-352,520-531` | **no** |
| B5-07 | real-time core | DAC service routine in IRAM; NVS commit stalls both cores | `digital-and-supervision.md:78-84` | **no** (and the contract mandates the NVS write) |
| B5-08 | `DAC ch1` | immediate out-of-turn pitch update on note change | `0006:245,252-253` | **no** |
| B5-09 | calibration | affine (gain, offset) pair; multi-point NVS table; anchors in range; presets | `0006:530-582,781-786` | **no** — calibration absent from NVS list |
| B5-10 | breath digital copy | auto-zero: seed, sub-threshold AND quiet, ~2 s, log the correction | `0006:288-318` | **referenced, never specified** |
| B5-11 | mod / breath | default 0–8 V, bipolar opt-in per channel | `0006:773-778` | **no** |
| B5-12a | NVS | CRC + hard UNCALIBRATED state | `ROADMAP.md:217`, `0014:346` | **no** |
| B5-12b | key bits | flag key closed at boot or held > N | `ROADMAP.md:218` | **no**, `N` unbound |
| B5-12c | breath zero | continuous auto-zero + show current zero | `ROADMAP.md:219` | **no**, contract states the superseded behaviour |
| B5-13 | cores / SPI hosts | display is on another MCU; both SPI hosts claimed | `0013:30,51`, `0007:186-190` | **self-contradictory, and bullet 2 is unbuildable** |
| B5-14 | display board | UART flash claim vs no `EN`/`IO0` | `display-and-service-uart.md:44-64` | **overclaim** |
| B5-15 | 8×8 matrix | no drive method assigned; ADR 0007's collides with SPI2 | `0007:190` vs `0014:55-57` | **no** |
| B5-16 | IMU | rate unstated; I2C burst > loop period | `0013:51`, `0007:122-124`, `ROADMAP.md:43` | **listed as a job, budgeted nowhere** |
| B5-17 | `DAC ch6` | update-rate table lists a deleted channel | `0006:247` | — (corpus defect) |
| B5-18 | ADC read | `~50–200 µs` live in ADR 0003; checker escapes on the pipe spelling | `0003:22` | — (corpus defect) |
| B5-19 | `key-release-time` | `125 µs` restated on the owner page; 119.9 us | `key-switch-network.md:109` | — (checker escape) |
| B5-20 | `marker-bits` | "which six bits" on `carrier.md`; 8 bits | `carrier.md:379` | — (checker escape) |
| B5-21 | key-layout | points at `cluster-boards.md §4`, which no longer exists | `config/key-layout.yaml:130` | — (broken live pointer) |
| B5-22 | `0006:331` | "breath locked to channel 2" vs "Mod 1–4 = DAC ch 2–5" | `0006:331` | — (ambiguity) |

---

## What I would do about it, in order

Not fixes — this report does not fix anything — but the ordering is part of the
finding, because these are not equally urgent.

1. **B5-13 first, and alone.** The contract's architecture list is the first
   thing the firmware author reads and it disagrees with itself. Until it is
   resolved, every other correction lands in a document the reader has already
   learned not to trust. Resolving it also forces the unanswered question of
   what the real-time board's second core runs.
2. **B5-02, B5-01, B5-03 — the three that make the first integration fail.**
   All three are one line of contract each.
3. **B5-04, B5-05, B5-12b as one item.** They are the key path's whole
   correctness story and they are currently split across an ADR, a copper page
   and a ROADMAP table.
4. **B5-09 + B5-12a + B5-10 as one item.** Calibration, its checksum, its
   failure state and the auto-zero are one persistence design, and the contract
   currently contains none of it.
5. **B5-06 as one item**, because ADR 0014's four rules only make sense together.
6. The staleness escapes (B5-18 through B5-21) are cheap and mechanical; B5-18
   and B5-19 want new `forbidden` patterns per CLAUDE.md §2, grepped for their
   actual spellings rather than written from the owner page — which is what both
   escapes were caused by.

The structural observation, offered once: `firmware/README.md` is cited **by**
seven hardware pages and ADRs as the authority for rules it does not contain
(B5-03, B5-04 via ADR 0001, B5-06, B5-08, B5-10). The corpus has been treating
it as the firmware contract for some time; it has not been maintained as one.
Every finding in Part 1 is that gap.
