# D4 — Missing failure detection and diagnostics

**Scope.** Failures Woody can suffer that produce a *plausible but wrong* result
rather than an obvious fault. Ranked by **how long the failure would go unnoticed
× how much damage it does in that time**, which is why an enabler that blinds
every other detector outranks any single fault.

**What this review assumes as already decided**, and does not re-argue:

- CRC on the calibration blob and a hard `UNCALIBRATED` state (ROADMAP).
- Stuck-closed-switch flagging at boot / held beyond N seconds (ROADMAP).
- Continuous auto-zero, and showing the zero on the display (ROADMAP, ADR 0006).
- The 74x165 marker pattern and its error counter (ADR 0001).
- `CLR` at the module when frames stop, i.e. the stuck-CV watchdog (ADR 0004).
- Alarm states preempt the 8×8 matrix and cannot be configured off (ADR 0014).

Those five are the right instincts. Every finding below is either a failure they
do not cover, or a place where the decided fix detects the fault but nothing
carries the news to a human.

---

## The four annunciation surfaces, and what each is actually good for

Named once here so individual findings can just point at one.

| Surface | Owner | Property that decides its job | Use it for |
|---|---|---|---|
| **8×8 matrix** | Real-time board | The **only** surface on the authoritative MCU. Survives the display board, the UART, WiFi and the umbilical | Hard alarms. Full-field red X = faulted; amber border = degraded/suspect; a two-digit glyph = which key or channel |
| **AMOLED** | Display board | Text, read at a steep angle while playing, but **downstream of a link that can silently freeze** | A persistent health strip of four tokens — `CAL` `ZERO` `KEY` `LINK` — grey/amber/red, plus a boot banner |
| **LED strips** | Real-time board | One-dimensional, ambient, peripheral vision | Exactly one message: a slow amber pulse at the tail = "look at a real display". No detail |
| **Web app** | Display board, phone | Unlimited area, history, arrives only when asked for | Counters, trends against commissioning, per-key table, self-test runner. The diagnostic home |

**Rule that falls out of the first row:** no alarm may live only on the AMOLED.
Every hard fault appears on the matrix as well, because the matrix is the only
surface whose failure mode is "dark" rather than "plausible".

---

## 1. Nothing records what a healthy Woody looks like, so no gradual failure has anything to be compared against

**Severity: Critical (enabler).**

**The failure.** Every detector below of the form "it got worse" needs a number
for "before". This project has a full bench, a pre-bond gate (M8) that already
gathers most of these numbers, and no mechanism anywhere that stores them. Once
the body is bonded, the as-built state can never be re-measured.

**What the player perceives.** Nothing, directly. What they perceive is
findings 6, 8, 9 and 10 below, none of which can be detected without this.

**Why it is silent.** It is an absence, not an event. Everything works on day
one, and the baseline is only missed years later when something has already
drifted and there is no way to prove it.

**Detection.** Not a detector — a prerequisite. At M8, and again at the first
power-on after bonding, write a signed **commissioning fingerprint** to a
dedicated NVS namespace, CRC'd and separately versioned from config so a config
wipe cannot take it:

| Baseline | Source | Used by |
|---|---|---|
| Breath at-rest ADC noise, σ over 1 s, sub-threshold | existing MCP3202 | 8 |
| Breath zero code, cold, and after a 30 min soak | existing MCP3202 | 3, 6 |
| Zero-injection DAC ch 6 code at cold zero | firmware | 5 |
| Breath attack 10–90 % rise time, P10 over 200 notes | existing MCP3202 | 9 |
| Per-key bounce duration, press and release, all 18 | existing key scan | 4 |
| Per-key actuation count (starts at whatever M8 leaves) | existing key scan | 4 |
| Interior temperature curve, 20 min from cold | IMU die temp (16) | 3, 16 |
| Gyro bias magnitude and accel magnitude at rest | existing IMU | 11 |
| Pitch cal: two anchors, INL table, the load it was taken against | firmware | 2 |
| Layout file hash and firmware bit-map hash | build | 13 |
| DAC saturation code measured at E7 | bench | 12 |
| Umbilical +12 V and local 5 V, idle and full lighting | rail monitor (7) | 7, 15 |

Then: **the web app's diagnostics page shows every live value beside its
commissioning value and the percentage drift**, and that single page is what
turns eleven of the findings below from "needs a bench" into "needs a glance".

**Annunciation.** Web app, one page, "Health vs. as-built". Matrix shows an amber
border if any tracked metric is outside its per-metric band.

**Hardware or firmware.** Firmware only, but it must be written before M8 or the
measurements happen and evaporate.

**ADD.** This is the highest-value missing firmware in the project after the
self-test that S11 already asked for, and it is the same build of work.

---

## 2. The pitch calibration is present, CRC-valid, and wrong — because it was taken against a different patch than the one plugged in

**Severity: Critical.**

**The failure.** ADR 0006 keeps the 1 kΩ output resistor and pays for it with a
firmware per-load scale factor: "one VCO" vs "two multed" is a 0.98 % gain
difference, **58 cents at five octaves up**. Nothing in the instrument knows
which load is actually connected, and nothing prompts the player to say. The
same shape covers a trimmer that has crept, an INL table silently truncated by a
partial NVS write, and a calibration taken months ago against a VCO that has
since been re-multed.

**What the player perceives.** The instrument is in tune in the middle of its
range and progressively sharp or flat at the extremes. Which is *also* what a
poorly-tracking VCO does, what a cold rack does, and what a wind player's own
pitch perception does under pressure. So it is heard as "the top octave is a bit
wild", and attributed to the oscillator, the room, or the player.

**Why it is silent.** `UNCALIBRATED` covers "no calibration". This is the case
where a calibration exists, passes CRC, loads cleanly, and is simply not the one
for this patch. Every indicator in the design reads green.

**Detection.**
- **Bind the calibration to its load by construction.** The stored blob carries
  `load_preset` (name), `taken_at`, `anchor_notes`, `n_inl_points`, and the
  firmware scale factor in force when it was taken. Refuse to treat a fit as
  valid unless all five are present — a defaulted field is a fault, not a zero.
- **Assert the point count.** A two-point fit where a 12-point table is expected
  is a truncated write. Threshold: `n_inl_points` < the value in the
  commissioning fingerprint → degraded, not faulted.
- **Trend the trimmers.** Every time calibration is re-run, store the delta
  against the previous run. A fixed hardware chain should need the same
  correction each time. Threshold: a change of more than **±6 cents equivalent**
  (≈ 5 mV at the jack, ≈ 40 DAC LSB) between consecutive calibrations with no
  hardware change is trimmer or op-amp drift, not a better calibration — and it
  is the only warning the module's two cermet trimmers will ever give.
- **Age it.** Elapsed playing hours since `taken_at` > 200 h → prompt.

**Annunciation.** AMOLED health strip: `CAL` reads the *preset name*, not "OK" —
`CAL 1VCO` permanently on screen, amber if the preset has not been re-confirmed
this session, red on a degraded blob. Matrix: amber border while amber, red X on
red. Web app: calibration history with the per-run delta plotted, which is the
only place trimmer creep becomes visible.

**Hardware or firmware.** Firmware only.

**ADD.** The ROADMAP already calls E9 "the milestone that decides whether this is
an instrument or a thing that is always slightly out of tune". This is the
failure that lets E9 pass and the instrument be out of tune anyway, for years.

---

## 3. The continuous auto-zero conceals exactly the breath faults it was added to absorb

**Severity: Critical.**

**The failure.** ADR 0006 decays the breath zero toward the current reading
whenever breath has been sub-threshold for ~2 s. That is correct for thermal
drift. It is also an *active concealment mechanism*: a partially blocked
reference port, a cavity that has been sealed more than assumed, a slow leak in
the tube, a sensor whose offset has shifted permanently, and a player resting
with light mouthpiece pressure all present as slow zero movement — and all get
absorbed silently. Worse, the 2 s rule can fire during genuinely quiet playing:
sustained pianissimo below threshold for two seconds and the zero adopts the
player's live blowing pressure, after which they must blow harder to reach
threshold at all.

**What the player perceives.** "I have to push harder than I used to." "Quiet
passages cut out." "The instrument loses its top end after twenty minutes." All
three are read as breath support, embouchure, or fatigue — which for a wind
player is the most natural self-diagnosis there is, and the hardest to disprove.

**Why it is silent.** The correction is the symptom. The whole point of the
mechanism is that drift does not reach the output, so nothing downstream can
ever reveal that it occurred.

**Detection.** Three cheap bounds on a mechanism that currently has none. Using
the MCP3202 at 12 bits and V_REF = V_DD = 3.3 V, behind the 0.6× divider from a
766 mV/kPa sensor: **≈ 560 counts/kPa**, zero nominally at **≈ 149 counts**,
full scale at **≈ 3501 counts**, 1 count ≈ 1.8 Pa.

- **Absolute bound.** The live zero must stay within the physically credible band
  around the datasheet zero. Threshold: |zero − 149| > **330 counts (±0.6 kPa,
  10 % of full scale)** is not thermal offset — it is a blocked reference port, a
  sealed cavity, or a failing sensor. Fault, not warning.
- **Rate bound.** After 30 minutes from cold, the interior is near equilibrium.
  Threshold: sustained zero movement > **0.05 kPa/min (≈ 28 counts/min)** past
  that point is a leak or a blockage, not warm-up.
- **Stillness gate on the decay itself.** Do not decay on "sub-threshold" alone —
  require **sub-threshold AND quiet**: short-window σ below 2× the commissioning
  at-rest noise. Actual blowing carries turbulence that resting air does not, so
  this single extra condition removes the pianissimo failure entirely, and it is
  the same trick ADR 0007 already uses for the gyro bias estimate.
- **Session budget.** Total zero excursion since boot, displayed, and alarmed
  above ±0.6 kPa.

**Annunciation.** AMOLED health strip: `ZERO` shows the live offset in kPa with
one decimal and its sign — a number that moves is a number the player learns the
normal range of. Amber outside ±0.3 kPa, red outside ±0.6 kPa. Matrix: red X on
red, because a zero that far out means the instrument is measuring something
other than breath. Web app: zero-vs-time trace for the session with the decay
events marked, which is also the trace M8's thermal soak wants.

**Hardware or firmware.** Firmware only (the rate/blockage discrimination is much
stronger with the die temperature from finding 16, which is also firmware only).

**ADD.** The ROADMAP entry "show the current zero on the display" is necessary
and nowhere near sufficient — a displayed number with no band is a number nobody
reads.

---

## 4. A key with an intermittent contact returns a wrong *note*, not a missing one, and is indistinguishable from a fingering slip

**Severity: Critical.**

**The failure.** ROADMAP and ADR 0001 handle the *stuck-closed* case. The harder
case is a switch, solder joint or loom conductor that is marginal: it opens for a
few milliseconds mid-note, closes 20 ms late on a fast passage, or chatters on
slow release inside the KS-33's actuation/reset hysteresis gap. Fingerings here
are **combinational**, so a single bad bit does not remove a note — it returns a
*different* note, or a note that arrives late, once every few hundred actuations.

**What the player perceives.** They played a wrong note. Occasionally. In fast
passages, on one particular transition. Every musician's prior for this is
"I fluffed it", and it is reinforced every time the passage comes out right on
the next attempt. In a bonded body, there is no way to falsify it by ear.

**Why it is silent.** It is statistically indistinguishable from the player's own
error rate, and it degrades over years, so there is never a day when it starts.

**Detection.** All of it is free from the scan that already runs at 4 kHz, and
none of it exists in the design:

- **Per-key chatter counter.** Any closure or opening shorter than the M1-measured
  bounce window + 50 % margin, or any transition that reverses within 30 ms
  during an active note. Threshold: **more than 1 such event per 200 actuations
  of that key over a session** — with the player's own note count as the
  denominator, so the statistic is comparable across keys and sessions.
- **Per-key bounce duration, tracked.** Median press-bounce per key vs. the
  commissioning fingerprint. Threshold: median grown > **2×** commissioning, or
  P95 > the debounce window itself, is a worn or contaminated contact.
- **Per-key actuation count and last-seen.** A key that has not closed in
  **three sessions** while its neighbours have is either broken open or a
  fingering nobody uses — both worth knowing, and the web app can say which.
- **Cross-check against the 74x165 marker pattern (finding 14).** A chatter
  burst that coincides with marker failures is a loom problem; one confined to a
  single bit with clean markers is a switch.

**Annunciation.** Matrix: amber border, plus a two-digit glyph of the suspect key
index on demand (hold the two control switches). AMOLED health strip: `KEY RH4`.
Web app: an 18-row table — actuations, chatter events, median bounce vs.
commissioning, last chatter timestamp. That table is the artefact that turns
"some fingerings feel wrong" into a name and a number, which is the entire point.

**Hardware or firmware.** Firmware only.

**ADD.** Highest-value firmware-only detector in the instrument, and the one with
the strongest attribution-to-the-player failure mode of any finding here.

---

## 5. The breath zero correction is applied open-loop to a signal path the instrument cannot see, so the display and the jack can disagree without limit

**Severity: High.**

**The failure.** The instrument's own breath reading is a **divided copy taken at
the buffer output, inside the instrument** (ADR 0003). The zero correction is
applied *at the module*, into the in-amp's `REF` pin from DAC channel 6
(ADR 0006). These are two different places. Firmware nulls the digital copy in
software and commands a code it *believes* nulls the analog copy — and nothing
measures the result. If the assumed in-amp gain is off, if DAC ch 6 drifts or was
never enabled, if the `REF` pin is loaded, or if the sign is wrong, the jack sits
at a standing DC offset while the display reads a perfect zero.

Everything downstream of the instrument's ADC tap is unobserved: 2 m of cable,
the in-amp, the gain and offset knobs, the output filter and the jack. The
knobs are a specific instance — an Alpha 9 mm pot that has gone scratchy with age
produces breath dropouts the instrument cannot see and has no vocabulary for.

**What the player perceives.** A VCA that never quite closes, a quiet drone under
rests, or a breath range that has "moved" — all read as rack behaviour or a patch
quirk, because the instrument's own display insists breath is zero.

**Why it is silent.** Two representations of the same quantity, one of which is
authoritative for the display and the other for the sound, with no path between
them. The display is not lying about what it measures; it is measuring the wrong
side of the correction.

**Detection.**
- **Bound the injected code.** The commanded ch 6 code is a firmware-visible
  proxy for the sensor's offset, and physics bounds it. Threshold: departure
  from the commissioning value by more than **±0.3 kPa equivalent** is a fault in
  the injection path, not ambient drift. This is free and catches the gross case.
- **Assert the enable.** Re-write the DAC's internal-reference enable and ch 6
  code on a schedule (see finding 12), so a lost write self-heals in milliseconds.
- **The real fix is at the module, and it is one part.** See finding 7.

**Annunciation.** AMOLED `ZERO` token goes amber when the injected code is
out of band, with the number shown; matrix amber border. Web app shows the
digital zero and the commanded injection code side by side, which makes the
divergence legible at a glance during M8 and during any later meter check.

**Hardware or firmware.** Firmware for the bound; hardware (finding 7) for
actual observation.

**ADD.** Also worth one line in ADR 0003: state explicitly that the in-amp
precedes the gain knob. If it does not, R12's original complaint returns —
the null is scaled by a pot firmware cannot read, and 0.2 V × ΔG is a 435 mV
stuck offset.

---

## 6. Nothing in the system ever learns whether the module did what it was told

**Severity: High.**

**The failure.** ADR 0004 deleted MISO from the umbilical on the argument that
"+12 V on the umbilical is itself evidence the module is connected" — and then
nothing senses +12 V. The link is unidirectional by construction. The DAC is
written and never read. The watchdog monostable can assert `CLR` and park every
channel, and the instrument continues playing into silence with a display showing
live note names and breath levels.

**What the player perceives.** Depends on the conductor. A marginal SPI line: an
occasional wrong-pitch note or a mod channel that jumps, read as a patch quirk. A
`CLR` assertion mid-phrase: "the rack glitched". A degrading `AGND` contact:
breath CV that wanders with the light show — "the sound wobbles a bit". All of
them land on the rack, which is the other half of a system the player also does
not fully trust.

**Why it is silent.** There is no return path, so no amount of firmware can close
the loop. This is the structural blind spot the rest of the design's care is
built on top of.

**Detection, in increasing order of cost.**

- **Sense +12 V at the instrument.** ADR 0007 leaves **GPIO 3 and 4 free and
  notes both are ADC1 channels**, and the MCP3202 has **a spare channel**. A
  divider from the umbilical +12 V into either gives presence detect, brownout
  detect, sag-under-lighting, and — sampled at loop rate — intermittency detect:
  a cable that dips when the instrument moves is a cable to replace, which is
  precisely the judgement ADR 0004 asks the player to make ("replace at the first
  sign of intermittency") and gives them no instrument for. Thresholds: < 10.5 V
  = warn, < 9 V = fault, any excursion > 300 mV correlated with movement =
  cable suspect. **Two resistors and a wire, and it cannot be added after
  bonding.**
- **Give the module a health LED.** `U-WATCHDOG` already exists to assert `CLR`
  when frames stop. Wiring its output to a panel LED costs an LED and a resistor
  and produces the one annunciation the instrument structurally cannot make about
  itself: *the module is not hearing you*. ADR 0006 considered per-jack LEDs and
  declined them as not worth designing in; a single **health** LED is a different
  proposition and is worth it.
- **Reconsider a readback-capable octal DAC.** ADR 0006 already lists AD5676
  alongside DAC8568. If a part in that class can be read back over the existing
  SPI lines, MISO earns its conductor and every downstream check in this document
  becomes closed-loop. Decide at E7, before the module PCB — after that it is
  a respin.
- **Structural rule to adopt.** *Put things you cannot observe in the module, not
  in the instrument.* The 6HP module is four screws away forever; the instrument
  is bonded shut. Every diagnostic that has to be done with a meter should be
  reachable at the module end.

**Annunciation.** Module panel LED: green = frames arriving, amber = watchdog
armed, red = `CLR` asserted. Instrument: matrix red X on umbilical fault; AMOLED
`LINK` token showing rail volts.

**Hardware.** All four items. Time-critical: the rail sense before bonding, the
LED and the DAC choice before the module PCB.

**ADD** the rail sense and the module health LED. **ACCEPT** the absence of full
readback if the DAC choice does not permit it — but record it as accepted rather
than leaving it as an oversight, because three other findings depend on it.

---

## 7. The annunciation path itself fails silently: a frozen display board looks exactly like a working one

**Severity: High.**

**The failure.** The display board persists nothing and the real-time board does
not depend on it, which is the right architecture and creates this failure. If
the UART dies, the display board hangs, or the frame layout drifts between two
images, the AMOLED keeps showing its last render — or renders a
plausible-but-wrong decode of a frame whose field layout changed. Add AMOLED
burn-in over years (ADR 0008 acknowledges it), and a ghosted `CAL OK` can persist
on the panel after the state beneath it has changed.

**What the player perceives.** A display that looks right. Which is worse than a
dark one, because they then *trust* it — and the first thing they trust it for is
finding 2's calibration preset or finding 3's zero.

**Why it is silent.** A static status screen and a frozen status screen are
pixel-identical. A protocol version field catches "these images disagree
entirely" and not "field seven moved".

**Detection.**
- **Freshness, enforced at the renderer.** Every status frame carries a
  monotonic counter. No valid frame for **250 ms** → the display board blanks to
  a `LINK DOWN` screen rather than holding pixels. Holding the last frame is
  never the correct behaviour on a status-only panel.
- **Layout hash, not just a version number.** The frame header carries a
  protocol version *and* a hash of the frame-layout descriptor. Mismatch → render
  a hard `VERSION MISMATCH` screen, never best-effort fields. This is free on day
  one of the protocol (ADR 0013 and the firmware README already ask for a version
  field; make it two fields) and expensive to retrofit.
- **Reverse heartbeat.** The display board acks; the real-time board alarms on
  **no ack for 3 s** — which is the only way the *authoritative* side learns its
  display is gone.
- **Burn-in discipline as a detection rule, not just a rendering one.** An alarm
  token must never be a static glyph in a fixed position. Shift the health strip
  with the rest of the layout, and mirror every hard alarm to the matrix.

**Annunciation.** Matrix, necessarily — it is the surface that survives.
Real-time board raises an amber border on display-link loss. Display board shows
`LINK DOWN` / `VERSION MISMATCH` full screen. Strips: amber pulse.

**Hardware or firmware.** Firmware only, but the frame-header decision must be
made at E4b with the first commit of the protocol.

**ADD.**

---

## 8. The breath sensor degrades into unreliability rather than dying, over months

**Severity: High.**

**The failure.** NXP qualifies the MPXV4006 family on dry air and states it is
not compatible with water vapour; ADR 0003 records that the **gel die coat swells
when wet, showing up as unreliable readings rather than a dead part**, and
concludes "treat the sensor as a wear part, buy two". Nothing tells the player
when to use the spare — in a body that is bonded shut, where that decision is
expensive either way.

**What the player perceives.** Breath response that has become slightly noisy,
slightly sticky, slightly nonlinear at the bottom — a note that does not quite
start cleanly at pianissimo. Over months. Attributed to reed technique,
mouthpiece, the day, the room.

**Why it is silent.** It is a slow change in a quantity the player has no
external reference for, in the one part of the instrument whose "correct"
behaviour is defined by the player's own body.

**Detection.** Two measurements, both from the existing ADC, both meaningless
without finding 1's baseline:

- **At-rest noise floor.** σ of the breath ADC over a 1 s sub-threshold window,
  rolling median across the session. Threshold: **> 3× the commissioning σ** =
  suspect; **> 6×** = fault. Gel degradation raises the noise floor before it
  moves the mean.
- **Return-to-zero hysteresis.** After every note, compare the settled
  post-note reading against the pre-note zero. A healthy closed dead-ended system
  returns within a few counts. Threshold: median post-note offset
  **> 0.05 kPa (≈ 28 counts)** across 50 consecutive notes indicates a swollen
  gel, accumulated liquid in the trap, or a restrictor problem — and the trap is
  the one of the three that is clearable without disassembly, so the message
  should say "clear the trap, then re-check".

**Annunciation.** AMOLED `ZERO` token doubles as the breath-health token, amber
on suspect. Web app: noise-floor and return-to-zero trends over the instrument's
lifetime, which is the graph that says "order the spare now" months before the
instrument becomes unplayable.

**Hardware or firmware.** Firmware only.

**ADD.**

---

## 9. The PTFE restrictor clogs, and the instrument becomes gradually less responsive

**Severity: High.**

**The failure.** The porous PTFE plug does two jobs (ADR 0003): it sets the
Helmholtz behaviour of a 400 mm tube and it blocks liquid water. Both jobs make
it a filter in a path that is breathed into for hours. As it loads with moisture
and debris, the pneumatic time constant rises and the breath path slows.

**What the player perceives.** The instrument "feels less responsive than it used
to" — attacks arrive late, tonguing is mushy. A wind player compensates
automatically by anticipating, and then experiences the compensation as their own
changing technique. This is the purest example in the design of a fault that
becomes part of the player's habit.

**Why it is silent.** Latency has no absolute reference. The tube delay is
already the largest single term in the budget (1.17 ms of a ~2.4 ms path), and
nothing measures the term that is supposed to be fixed.

**Detection.** Measure the instrument's own attack rise time, continuously, for
free: for every note onset, record the **10–90 % rise time of the breath ADC**,
and keep a rolling P10 (the fastest tenth of attacks, which approximates the
player's hardest tongue and is far more stable than the mean). Threshold: rolling
P10 **> 2× the commissioning P10** is a pneumatic change, not a technique change.
A cross-check that costs nothing: a clog raises rise time *without* changing the
noise floor, where a degraded sensor (finding 8) raises both.

**Annunciation.** Web app: rise-time P10 trend against commissioning, with the
M8 baseline drawn. AMOLED health strip only once it crosses 2×. This is
deliberately a low-urgency annunciation — it is a maintenance signal, not an
alarm — but it must exist somewhere, because otherwise it is invisible forever.

**Hardware or firmware.** Firmware only. The mechanical half — that the plug
should be reachable, like the trap — belongs in ADR 0009's access requirement and
is worth confirming covers the plug and not only the trap.

**ADD.**

---

## 10. The instrument is played for years and never reports how hot it got, in a design whose whole thermal story is an estimate

**Severity: High.**

**The failure.** The thermal model behind the lighting clamp is "roughly 3 K per
watt", explicitly a bounding estimate (ADR 0014). The breath sensor's offset is
temperature-dependent. The acrylic bond has a service limit. The 5 V regulator is
a 1 A part. And there is **no temperature sensor anywhere in the BOM** — the only
thermal measurement in the project is a thermocouple at M8, on the bench, once,
before the body closes.

**What the player perceives.** Nothing, until the compound symptoms: the zero
walking (finding 3), an instrument warm under the hands, and years later an
acrylic bond that has crept. Each gets its own local explanation.

**Why it is silent.** Temperature is the hidden variable that half the other
failures are functions of, and it is unmeasured, so those failures cannot be
attributed and look like independent mysteries.

**Detection.** The QMI8658C on the real-time board exposes a **die-temperature
register** (confirm at E1/E3). It sits at the very bottom tip of the instrument,
centimetres from the breath sensor, on the board that already owns the lighting
budget. It is a free interior thermometer that nothing reads. With it:

- **Absolute bounds.** Warn above **45 °C**, fault and force the lighting budget
  to a floor above **55 °C**.
- **Validate the model in service.** Log ΔT against summed commanded lighting
  power. If the measured K/W exceeds the 3 K/W the clamp was sized from, the
  clamp is too generous and should be reduced — and that is a thing firmware can
  do on its own.
- **Discriminate finding 3.** Thermal offset tracks temperature monotonically and
  reverses on cooling; a blockage does not. With the die temperature, "zero
  drift" and "reference port sealed" stop being the same observation.
- **Watch the clamp.** Alarm if the proportional scale-down engages continuously
  for more than a few seconds — that means something is persistently asking for
  more than 3 W, which is a config or firmware bug rather than a bright moment.

**Annunciation.** Web app: temperature and lighting-power traces per session.
Matrix: amber border above 45 °C. Above 55 °C the matrix is itself part of the
load and should dim as it alarms — a dim red border, not a bright one.

**Hardware or firmware.** Firmware only if the IMU's temperature channel is
usable. A dedicated sensor is hardware and must go in before bonding; check the
IMU register first, because it is free.

**ADD.**

---

## 11. The gyro bias estimate goes stale and gestures stop being repeatable

**Severity: Medium-High.**

**The failure.** ADR 0007's stillness-gated estimator is right, and it has an
explicit fallback: "if the instrument has not been still recently enough, hold
the last good bias rather than adopting a fresh bad one." An instrument played
standing, on a strap, may **never** be demonstrably still. The held bias ages,
and during a 3 s gated bend the integration accumulates error from a bias that is
no longer current. The same section notes gyro *noise* over a gesture is 0.026° —
bias is the entire story, and nothing reports on it.

**What the player perceives.** Bends that do not land where they landed last
time. The same gesture producing a different amount of modulation on different
days. Read as technique — gesture control is the one part of a wind instrument
where players already expect inconsistency from themselves.

**Why it is silent.** The gesture still works. Only its *repeatability*
degrades, and repeatability is exactly what a player attributes to themselves.

**Detection.**
- **Age and magnitude of the held bias.** Threshold: last accepted update older
  than **10 minutes** of playing, or magnitude beyond the commissioning value by
  more than **1 °/s**, marks every IMU-derived source as unreferenced.
- **Measure the accumulated error directly, per gesture.** At gate release,
  compare the gyro-integrated tilt against the accelerometer-derived tilt (valid
  again once motion stops). The disagreement *is* the gesture's error. Threshold:
  median disagreement **> 3° over a 3 s gesture** = the estimator is not keeping
  up. This is the field version of ADR 0007's own
  "gate-press-while-moving" bench test at E3, and it is free.
- **Liveness.** |accel| must sit at 1 g ± 0.15 g at rest, and something must
  change while keys are being pressed. A frozen I2C read that returns a plausible
  constant is otherwise undetectable.

**Annunciation.** The matrix is already the right surface — ADR 0014 draws the
2-D dot against the captured zero *with the deadband on the grid*. Draw the
deadband and the centre mark **amber when the bias is unreferenced**, so the
player sees the estimator's confidence in the same glance as the gesture. AMOLED:
`IMU UNREF`. Web app: bias magnitude and per-gesture disagreement over time.

**Hardware or firmware.** Firmware only.

**ADD.**

---

## 12. A channel saturates rather than stops, and the top of the modulation range quietly flattens

**Severity: Medium-High.**

**The failure.** The mod stage is `Vout = 4 × (Vdac − Voffset)` and ADR 0006 uses
only the DAC's **0.25–4.75 V window**, with real saturation somewhere above that
and dependent on AVDD — which the ROADMAP already schedules as a measurement at
E7 ("record the actual saturation code at the actual rail"). Once measured, that
number is never used again. A mod channel configured with a scale and offset that
push codes past the window clips; so does pitch at the top of a bend near +7 V.

**What the player perceives.** The modulation "runs out" at the top — a filter
sweep that stops opening, a bend that stops bending. Attributed to the
destination module, which is where the sweep visibly stops.

**Why it is silent.** Clipping is smooth, monotonic and bounded. Most of the
range works, and nothing in the signal announces where the linear region ended.

**Detection.** Pure firmware, and the threshold is a measured number that already
exists: count, per channel per second, samples whose **commanded code lands
outside the E7-measured linear window**. Threshold: **> 1 % of samples clipped
over any 5 s window** = that channel is mis-scaled. Report the fraction, not just
a flag, because a channel that clips on 30 % of samples and one that clips on
1.5 % are different conversations.

Two adjacent firmware rules worth stating while this is being written:

- **Keep writing every channel every loop pass.** The latency budget already
  assumes six DAC channels serviced every 250 µs. Do not "optimise" pitch to
  write-on-change: a corrupted word on a write-on-change channel persists for the
  whole note, where on a refreshed channel it lasts 250 µs. The refresh is the
  cheapest error-correction in the system and it is currently accidental.
- **Re-assert the DAC's internal-reference enable and the ch 7 offset
  periodically**, for the same reason (ADR 0006 notes the reference is disabled
  by default; a lost or corrupted enable is a silent state change at the module
  the instrument cannot see).

**Annunciation.** Web app: a per-channel headroom meter, red band at the top,
with the clipped-sample percentage. Matrix: amber border plus the channel number
as a glyph. AMOLED: nothing — this is not a performance-time alarm, it is a
configuration fault, and putting it on the playing surface would train the player
to ignore amber.

**Hardware or firmware.** Firmware only.

**ADD.**

---

## 13. The firmware's bit map and the plate that was actually built can disagree, and every fingering is then subtly wrong

**Severity: Medium-High.**

**The failure.** `config/key-layout.yaml` generates both the plate DXF and the
74x165 bit mapping (ADR 0010). If a firmware image is ever built from a different
revision of that file than the plate that was cut — or if one key's bit is
swapped with one of the 14 spares — the instrument plays, every key does
something, and a subset of fingerings return the wrong note. ADR 0010 also warns
that a `control` key entering the fingering table produces phantom notes and a
`note` key treated as control silently drops fingerings, and proposes no check.

**What the player perceives.** "Some fingerings feel wrong" — the identical
signature to finding 4, but permanent rather than intermittent, which makes it
*more* likely to be accepted as the instrument's character. On a custom fingering
system with no external reference, a wrong fingering table is indistinguishable
from a fingering table you have not learned yet.

**Why it is silent.** There is no external authority on what the fingerings
should be. The instrument is self-consistent and wrong.

**Detection.**
- **Hash the layout.** Embed the hash of `key-layout.yaml` in both firmware
  images at build time; store the as-built hash in NVS at commissioning; compare
  at boot. Mismatch = hard fault, not a warning.
- **Validate the table on every load.** The fingering table must reference only
  `role: note` ids, must cover all 15, and must reference no `control` id.
  Reject the whole table rather than applying a partial one, and say which rule
  failed.
- **Make the physical-to-logical map checkable by a human in 30 seconds.** A
  self-test mode where pressing any key lights the corresponding matrix pixel and
  names the key on the AMOLED. This is a few lines on top of the self-test S11
  already asks for, and it is the only test that catches a *wiring* error as
  opposed to a *data* error.

**Annunciation.** Matrix: red X on hash mismatch, because an instrument that
cannot prove it knows its own keyboard should be loud about it. AMOLED boot
banner: `LAYOUT a1b2c3 ≠ BUILD d4e5f6`. Web app: full key-map table with roles.

**Hardware or firmware.** Firmware only, plus one line in the `tools/` generator.

**ADD.**

---

## 14. The key-chain error counter exists as a bench measurement and not as a lifetime instrument

**Severity: Medium-High.**

**The failure.** ADR 0001's marker pattern is good work — 4–6 of the 14 spare
chain bits as a fixed pattern, a failing frame holds the previous frame, and the
error count "converts an invisible intermittent fault into a number on the
display". The ROADMAP then schedules it as a single measurement: "key-chain error
counter over an hour, at E4". Two gaps follow. First, the counter has to live for
the instrument's life, not for that hour — the loom ages, the body is bonded, and
E4 runs on dev boards on a bench. Second, **holding the previous frame is itself
silent**: a chain failing 5 % of frames does not produce wrong notes, it produces
notes that are up to a few milliseconds late, which reads as sluggishness.

**What the player perceives.** At a low rate, nothing. At a moderate rate, an
instrument that feels slightly behind the beat — the same perception as finding 9,
and the same self-attribution.

**Why it is silent.** The mitigation is the concealment: holding the last good
frame is exactly the behaviour that stops a corrupt read becoming a wrong note,
and therefore stops it becoming visible.

**Detection.** The counter already exists; give it thresholds and a home.
- **Any marker failure during normal play is abnormal.** Threshold: **> 0 per
  hour** = note it in the web app; **> 10 per minute** = amber; **sustained > 1 %
  of frames** = fault, because at that rate held frames are audible as latency.
- **Also count held frames and consecutive holds.** A single hold is a
  non-event; three consecutive holds is 750 µs of stale key state.
- **Persist the counter across boots** in NVS and expose lifetime totals, so a
  loom that is slowly degrading is visible as a trend rather than as a
  per-session number nobody remembers.
- **Correlate with the rail monitor (finding 6) and the LED animation.** Marker
  failures that cluster with lighting transitions are a grounding problem;
  failures that cluster with movement are a loom.

**Annunciation.** AMOLED health strip: nothing at zero, `CHAIN n` in amber above
threshold. Matrix: amber border. Web app: errors-per-hour trend for the life of
the instrument, which is the number ADR 0001 says "says whether the looms are
good" — and looms cannot be reworked after bonding, so the trend is the only
thing that will ever tell you.

**Hardware or firmware.** Firmware only (the hardware — the marker bits — is
already decided and must be wired before bonding).

**ADD** the thresholds, persistence and annunciation. **ACCEPT** the marker
pattern itself as already decided.

---

## 15. Brownout resets are invisible between notes, and the instrument quietly comes back with a different state

**Severity: Medium.**

**The failure.** ADR 0014 traced the polyfuse/brownout/latched-LED loop and fixed
the electrical half with the module's load switch. What remains is the
*informational* half: a real-time board that browns out and resets comes back in
around a second, blanks the LEDs (correctly), re-reads NVS, and **restarts the
breath auto-zero from a cold state in a warm instrument**. Everything is
consistent afterwards and nothing records that it happened.

**What the player perceives.** A brief dropout mid-piece, blamed on the patch or
a cable — followed by a breath response that is subtly off for the rest of the
session, because the zero was recaptured against a warm body and a mouthpiece
that may not have been at rest.

**Why it is silent.** Recovery is fast and complete. The instrument's post-reset
state is self-consistent; only the history is missing.

**Detection.** Free, on the ESP32: read the reset reason at boot
(`ESP_RST_BROWNOUT`, `ESP_RST_PANIC`, `ESP_RST_WDT`, `ESP_RST_POWERON`) and keep
a persistent counter and a small ring buffer of the last 16 reset reasons with
timestamps in NVS. Threshold: **any** brownout or panic reset is reportable; more
than one per session is a fault. With the rail monitor from finding 6, log the
last N milliseconds of rail voltage preceding the reset.

Second half: on a warm restart, **do not treat the recaptured zero as
commissioning-grade** — carry a "zero recaptured after unexpected reset" flag
until the next clean power cycle, and show it.

**Annunciation.** AMOLED boot banner, held for 5 s: `RESET: BROWNOUT (2nd today)`.
Matrix: amber border for the first 10 s after an unexpected reset. Web app:
reset log.

**Hardware or firmware.** Firmware only.

**ADD.** Cheapest detector in this document.

---

## 16. A config change is acknowledged, applied, and not persisted

**Severity: Medium.**

**The failure.** ADR 0013's round-trip rule is right: "the phone edits, the
display board forwards, the real-time board validates, applies, persists and
echoes back the new state." The echo is of the *applied* value. If the NVS write
fails — flash wear, a full partition, a write interrupted by finding 15's
brownout — the value is live in RAM, echoed as correct, and gone at the next
power cycle. ADR 0012 also leaves open "whether the web app's state is the
authority, or the instrument's NVS is, when they disagree after an interrupted
session", which is the same failure from the other end.

**What the player perceives.** "My routing keeps reverting." "I'm sure I set
that." Blamed on themselves for not saving, or on the web app.

**Why it is silent.** Every surface shows success at the moment of the edit. The
divergence only exists across a power cycle, by which time the cause is gone.

**Detection.**
- **Echo the read-back, not the applied value.** After persisting, read the field
  back out of NVS and echo *that*. One extra read per edit, and it turns a silent
  class of failure into an immediate one.
- **Expose NVS health.** Write-error count, free space, and the number of entries
  per namespace, in the web app. A partition filling up is a slow failure with a
  known end.
- **Make pending state visible in the web app.** Every control renders as pending
  until echoed; any field where echo ≠ requested turns amber and shows both
  values. That also resolves ADR 0012's open question in the right direction —
  the instrument is the authority, and the app's job is to show where it and the
  app disagree rather than to paper over it.

**Annunciation.** Web app, entirely — this is a configuration-time failure and
the player is looking at the phone when it happens. AMOLED `CFG FAIL` only if a
persist fails outright.

**Hardware or firmware.** Firmware only.

**ADD.**

---

## 17. Note-gate chatter reads as unreliable tonguing

**Severity: Medium.**

**The failure.** ADR 0014 traced the positive-feedback path — LEDs lighting
depresses the shared-ground reference, which shifts the breath reading in the
direction that keeps them lit — and prescribed two free fixes: size the
hysteresis from the measured LED-induced step at E4, and drive the LEDs from the
post-gate slew-limited value rather than the raw ADC sample. Both are correct and
both are firmware conventions that a later change can quietly undo. There is no
detector for the condition itself.

**What the player perceives.** Notes that stutter or fail to start at quiet
dynamics, right at threshold. Attributed to tonguing, to breath support, to the
reed — never to the light strip, which is doing something visually plausible at
the same moment.

**Why it is silent.** It only happens in a narrow band of breath pressure, at
quiet dynamics, which is where a player already expects to be the weak link.

**Detection.** Firmware, free: count gate transitions whose dwell is
**< 20 ms**. Threshold: **more than 3 per minute** of playing = chatter alarm.
Additionally, log the breath value at every gate transition — a histogram that
clusters tightly at the threshold is chatter; one spread across the range is
playing. As a regression guard, the boot self-test can drive a known lighting
square wave with breath sub-threshold and check the ADC for a correlated step:
threshold **> 0.5 % of full scale (≈ 17 counts)** means the coupling is back and
the hysteresis needs re-sizing.

**Annunciation.** Web app: chatter count and the transition histogram. AMOLED
health strip: nothing during play — an alarm here would land during the exact
passage the player is struggling with, which is the wrong moment to tell someone
it might not be their fault. Report it after, on the phone.

**Hardware or firmware.** Firmware only.

**ADD.**

---

## 18. The module's frame watchdog can fire, or nearly fire, and nothing on either side knows

**Severity: Medium.**

**The failure.** ADR 0004's monostable asserts `CLR` when no valid frame has
arrived for N ms, and asks that N be sized "so a busy loop cannot trip it but a
hang is caught in well under a second". N is currently unspecified, and the
margin against it is unmeasured. Set too tight, a legitimate long loop pass parks
every channel mid-phrase; set too loose, a hang drones for most of a second.

**What the player perceives.** Either a momentary total dropout of every CV at
once — read as a rack glitch — or a drone that outlasts the gesture.

**Why it is silent.** The instrument cannot see `CLR` (finding 6), and the module
has no memory. The event leaves no trace on either side.

**Detection.** The instrument can measure its own side of it exactly: track the
**maximum inter-frame interval per minute** on the DAC SPI path. Threshold: any
gap **> 0.5 × N** = the margin is inadequate and should be reported; a gap
**> N** means `CLR` fired. This also sizes N from data instead of a guess, which
is what ADR 0004 asks for and provides no mechanism for. Pair it with the module
health LED from finding 6, which is the other half.

**Annunciation.** Web app: max inter-frame gap per session against N, plotted.
AMOLED `LINK` token amber if the margin was ever breached. Module panel LED
amber/red at the module end.

**Hardware or firmware.** Firmware for the margin measurement; hardware (the LED)
for the module's own report.

**ADD.**

---

## 19. The WS2815 backup data line hides accumulating dead LEDs until the run fails abruptly

**Severity: Low.**

**The failure.** WS2815 was chosen partly for its redundant data path, so "a
single failed LED does not kill everything downstream of it" (ADR 0014) — which
in a bonded body is exactly right. The consequence is that individual LED
failures are invisible by design, accumulating until two adjacent parts fail and
half a run goes dark at once.

**What the player perceives.** Nothing, for years. Then a strip that is suddenly
half dead, which is loud and which cannot be fixed anyway.

**Why it is silent.** It is silent *on purpose*, and the purpose is good.

**Detection.** There is no electrical return from the strip, so no firmware or
cheap hardware detection exists. The only available check is a human looking at a
known boot pattern.

**Annunciation.** Fold into the boot self-test: a brief per-strip sweep at low
brightness on every power-on, which the player will learn the look of and notice
changing. No alarm state.

**Hardware or firmware.** Neither.

**ACCEPT.** Recorded here so it is an accepted consequence of a good decision
rather than an oversight, and because the decorative strips are the one subsystem
where a silent failure costs nothing musically.

---

## What has to be decided before it becomes impossible

The body bonds at M8 and the module PCB is fabbed at E12. Everything in the left
column has to exist before those dates.

| Item | Finding | Gate | Cost if missed |
|---|---|---|---|
| Umbilical +12 V sense into GPIO3/4 or the MCP3202's spare channel | 6, 14, 15 | before M7 | No presence detect, no brownout evidence, no cable-intermittency detection, ever |
| Module health LED off `U-WATCHDOG` | 6, 18 | module PCB, E12 | The one annunciation the instrument cannot make about itself |
| Readback-capable octal DAC, if one fits the package policy | 6, 12 | E7 / module PCB | Every module-side check stays open-loop, permanently |
| IMU die-temperature register confirmed usable | 10, 3 | E1 / E3 | A dedicated sensor becomes a pre-bond hardware add instead of free |
| Marker bits wired in the chain | 14 | before M7 | Already decided; just do not lose it |
| Frame header carries version **and** layout hash | 7 | E4b, first commit | Retrofitting a header across two images is the thing the header exists to prevent |
| Commissioning fingerprint written | 1 | M8 | Eleven detectors below lose their reference and cannot get it back |
| Pressing any key lights its matrix pixel (self-test) | 13, 4 | before M7 | The only wiring-error check that works with the body open |

## Summary

| # | Failure | Severity | HW / FW | Verdict |
|---|---|---|---|---|
| 1 | No commissioning baseline | Critical | FW | ADD |
| 2 | Calibration valid but wrong for the patched load | Critical | FW | ADD |
| 3 | Auto-zero conceals the faults it absorbs | Critical | FW | ADD |
| 4 | Intermittent key → wrong note, blamed as a slip | Critical | FW | ADD |
| 5 | Zero correction open-loop; display and jack diverge | High | FW + HW | ADD |
| 6 | No return path; module never reports | High | HW | ADD (partly ACCEPT) |
| 7 | The annunciation path fails silently | High | FW | ADD |
| 8 | Breath sensor degrades rather than dies | High | FW | ADD |
| 9 | Restrictor clogs; response slows over months | High | FW | ADD |
| 10 | Interior temperature unmeasured | High | FW | ADD |
| 11 | Stale gyro bias; gestures not repeatable | Med-High | FW | ADD |
| 12 | Channel saturates rather than stops | Med-High | FW | ADD |
| 13 | Bit map vs. as-built plate mismatch | Med-High | FW | ADD |
| 14 | Chain error counter is a bench test, not an instrument | Med-High | FW | ADD |
| 15 | Brownout resets invisible between notes | Med | FW | ADD |
| 16 | Config acknowledged but not persisted | Med | FW | ADD |
| 17 | Note-gate chatter reads as bad tonguing | Med | FW | ADD |
| 18 | Module watchdog margin unknown | Med | FW + HW | ADD |
| 19 | Backup data line hides dead LEDs | Low | — | ACCEPT |

**Seventeen of nineteen are firmware.** Three small hardware items — a divider
into an existing spare ADC channel, one LED on the module panel, and a DAC part
choice — carry the entire hardware cost, and two of the three must be decided
before the body closes.
