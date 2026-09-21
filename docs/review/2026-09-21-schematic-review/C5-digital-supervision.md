# C5 — Digital path and supervision

**Cold review, 2026-09-21.** Subject: `hardware/module/digital-and-supervision.md`,
line by line; then the relevant parts of `docs/decisions/0004-cv-interface-module.md`,
`firmware/README.md`, and BOM rows 34, 35, 43, 49, 50, 54, 69, 70, 71, 82, 83, 99,
100, 101.

Not read, by instruction: `docs/review/`, `docs/research/`. Any claim this page
makes about prior art (Expert Sleepers, "no surveyed module") is therefore
**unverified here** and is treated as an assertion, not as evidence.

Vendor datasheet domains were proxy-blocked. Where a conclusion depends on a
datasheet number I name the **part and the parameter** and gate the conclusion
rather than inventing a figure. `[from memory]` means exactly that: it may be
wrong and it is not a substitute for the datasheet.

Evidence markers: `[repo]` `[calc]` `[datasheet]` `[from memory]` `[gated]`.

---

## Severity table

| # | Severity | Finding |
|---|---|---|
| D1 | **Critical** | The presence threshold sits *inside the breath signal's legitimate range*. Inhaling, a warm cavity, or a low-spec sensor drops the detect, disables the buffer and fires the watchdog mid-phrase |
| D2 | **Critical** | `OE` gating and the watchdog are **in series, not independent**. The watchdog's only input is the buffered `CS`, which `OE` gates. Every presence dropout starves the watchdog by construction |
| D3 | **Critical** | `R-PRESENCE`'s specified values cannot produce the specified threshold. 100k/10k gives **0.45–0.47 V** from any rail in the module — more than twice the entire signal. Built as specified, the module never enables |
| D4 | **High** | LM311 input bias current across the 1 MΩ bias resistor puts the *unplugged* node at **+0.10 to +0.25 V**, at or above the +100 mV threshold. Detect reads "present" with nothing attached — the exact failure the redesign exists to fix |
| D5 | **High** | The watchdog cannot see the failure it was built for. It retriggers on `CS` edges; firmware's mandated refresh-everything loop emits `CS` edges forever with stale data |
| D6 | **High** | The DAC8568 clear-code register reportedly includes an *ignore-`CLR`* option. One corrupted frame silently and permanently disables the watchdog, undetectably. Firmware's sticky-register list also omits the power-down register |
| D7 | **High** | Disabling `OE` mid-frame asserts an asynchronous `SYNC` rising edge at the DAC. Yes, the two mechanisms fight, and the unplug case drones for 99 ms first |
| D8 | **High** | `LDAC` appears **nowhere in the repository**. A floating CMOS input on the one part the module exists for |
| D9 | **High** | Cable-side `CS` idles to **+5 V into a 3V3 pin on an unpowered MCU**: ~430 µA continuously through the ESP32's clamp in the design's *normal* resting state, and the node sits at ~0.7 V, so "CS idle high" is not achieved |
| D10 | **High** | The page's own schematic drawing is the **superseded** circuit. The ASCII art shows in-amp output, −200 mV, from −12 V — the arrangement the prose below it declares broken |
| D11 | **Low** *(resolved mid-review)* | `OE` pull-up rail: BOM row 101 was rewritten during this review and now agrees with the pages on bus +5 V. What survives is that this page's stated *justification* is a non-sequitur and its rail table is internally inconsistent |
| D12 | **Medium** | The retrigger open question is posed against the wrong number — 16 µs and ~2376 retriggers, not 250 µs and ~400 — and against the wrong parameters |
| D13 | **Medium** | `Rext` = 1 MΩ gives a 5.21 µA timing current against the HC family's ±1 µA input leakage: ±19 % before the capacitor is considered. Timeout spread ~71–141 ms. "74HC123 or equivalent" is not timing-portable |
| D14 | **Medium** | `SCLK` — the fastest edge in the system — has **no series resistor**; `MOSI`'s 220 Ω is over-damped. ADR 0004's "7.9 MHz corner" is the figure for 100 Ω, not 220 Ω |
| D15 | **Medium** | The buffer is **enabled** for ~100–400 ms of the instrument's boot before firmware writes. Protection rests entirely on `CS`, which is the pull with the rail problem in D9 |
| D16 | **Medium** | The LM317 window ADR 0004 computes (4.88–5.54 V) runs past the DAC8568's 5.5 V maximum, and the bench procedure pushes *upward* with no stated ceiling |
| D17 | **Medium** | Unused gates and halves are not tied off: the spare 74AHCT125 gate's input, the second half of the 74HC123, and the '123's own `CLR` pin |
| D18 | **Medium** | An unpowered 74AHCT125 back-drives the DAC-side `CS` pull-up through its output body diode, dragging `SYNC` to ~0.7 V — a valid LOW at the DAC. "Kills the buffer and nothing else" is false |
| D19 | **Medium** | `MOSI`/`CS` share a twisted pair with **no return conductor**; all three SPI returns use the `SCLK` pair's `DIG_GND` |
| D20 | **Low-Med** | What happens on `CLR` *release* is nowhere documented, and it decides whether a boot-looping instrument gives silence or a ~3 Hz stutter of the stuck note |
| D21 | **Low** | Panel LED: sized with the wrong rail, 3.66 mA not 3.8 mA, 3.35 mA at bus −5 %, colour unspecified, cathode return not drawn — and it now flickers with breath |
| D22 | ~~Low~~ **Fixed mid-review** | Ref-des `R-CLR-PU` named a pull-**down**; BOM row 71 is now `R-CLR-PD` |
| D23 | **Low** *(mostly fixed mid-review)* | BOM row 43's decoupling count was 19 and is now 22; it still counts a DAC8568 `DVDD` pin that the TSSOP-16 pinout has no room for |
| D24 | **Low** | ADR 0004's "+5 V ~10 mA (level shifter only)" is stale and ignores AHCT ΔICC at a 3.3 V input |
| D25 | **Low** | "1 MΩ hysteresis, the value Expert Sleepers ships" is not a transferable claim; hysteresis depends on the impedance of the node it feeds, which here is 45 mV |
| D26 | **Medium** | A sustained +12 V fault on `BREATH` — a case ADR 0003 calls *designed-safe* — puts ~11.9 V on the comparator's input, likely outside the LM311's input common-mode range |

---

## D1 — The presence threshold sits inside the signal **Critical**

The proposed replacement is a real improvement on what it replaces, and it is
still not sound, for a reason neither the page nor `R-PRESENCE` raises.

### Node voltages, every state

Topology from `breath-receive-stage.md` `[repo]`: instrument buffer → 1 kΩ
series (`R1`) → `BREATH` conductor → 10 kΩ module-side series (`R3` in the
current drawing) → node **A**, the in-amp's `IN−`, with a 1 MΩ bias return
(`R5`) from A to module `AGND`. The `AGND` conductor takes the mirror path
(`R1b` 1 kΩ, `R2` 10 kΩ) to node **B**, the `IN+`, with its own 1 MΩ (`R4`).
The proposal taps node A `[repo: digital-and-supervision.md, "sense … through
the existing 10 kΩ protection resistors"]`, and ADR 0004 now adopts it in the
same words `[repo]`.

*(The reference designators on the two legs were swapped in
`breath-receive-stage.md` while this review was being written, and `R1b` was
added. I have described the resistors by function so the argument survives the
relabelling; only the leg matters, and the series total on each leg is 11 kΩ
either way.)*

| State | Node A | Node B | Detect should say | Detect says |
|---|---|---|---|---|
| Cable unplugged | 0 V + I_B·1 MΩ = **+0.10…+0.25 V** `[calc, D4]` | same | absent | **present** (D4) |
| **Sustained +12 V fault on `BREATH`** | 12 × 1 M/(1 M + 11 k) = **11.87 V** `[calc]` | ≈0 V | — | present, possibly inverted (D26) |
| Cable in, instrument off (panel toggle) | ≈0 V; instrument op-amp output clamped to its dead rails through 1 k + 10 k against 1 M `[from memory: unpowered op-amp output clamps within ~0.6 V of its rails]` | ≈0 V | absent | absent ✓ |
| Instrument alive, at rest | 0.200 × 1 M/(1 M + 11 k) = **197.8 mV** `[calc]` | ≈0 V | present | present ✓ |
| Instrument alive, rest, sensor at bottom of spec (0.152 V) | 0.152 × 0.98912 = **150.3 mV** `[calc]`; spec range 0.152–0.378 V `[repo: breath-receive-stage.md]` | ≈0 V | present | **marginal** |
| Playing, hard blow | ~4.5 V at the sensor → node A ≈ 4.45 V `[calc from repo's 2.5–2.8 kPa figure]` | ≈0 V | present | present ✓ |
| **Player inhales / negative differential pressure** | sensor clips toward **0 V** | ≈0 V | present | **ABSENT** |
| **Warm cavity, reference port restricted** | BOM row 55: "gains ~5.2 kPa when warm and the output clips at zero" `[repo]` | ≈0 V | present | **ABSENT** |
| `BREATH` conductor open (cable intermittency) | 0 V, held by R4 | ≈0 V | — | absent |

### Why that is critical and not merely untidy

The threshold is +100 mV `[repo]`. The signal's *legitimate* resting value is
+200 mV, and the signal's legitimate range **extends below the threshold**,
because the MPXV4006**DP** is a differential part whose output clips at zero for
negative differential pressure `[repo: BOM row 5, row 55]`. So:

- **Suck on the mouthpiece and the instrument disappears.** `OE` goes high, the
  DAC-side SPI lines go to their idle pulls, no more `CS` edges reach the '123,
  and **99 ms later `CLR` fires**: pitch subsonic, all four mods to 0 V, mid-note.
- **A restricted reference port escalates from "breath reads zero" to "the whole
  module is dead."** BOM row 55 already warns that coating the reference port
  makes a live sensor look dead. Coupling `OE` to that signal turns a
  one-channel fault into a total loss of CV output, with no readback to explain
  it.
- **The margin at the bottom of the sensor's own spec is gone.** The pedestal
  is "a **spec band, not a number**: 0.152–0.378 V" — `breath-receive-stage.md`
  now says so in those words and has widened the `REF` trimmer's range to cover
  it `[repo]`. Worst legal rest at the module node = 0.152 × 0.98912 =
  **150.3 mV** `[calc]`. Subtract 45 mV of hysteresis (D25 `[calc]`) and the
  LM311's input offset voltage — **name the parameter: LM311 V_OS, typ/max**
  `[gated]`, commonly quoted around 3 mV typ / 7.5 mV max `[from memory]` — and
  the gross margin above the 100 mV threshold is roughly **5 mV**. That is not a
  margin, it is a coin toss on a production part at the edge of its spec.

### Does it chatter?

**Not from noise; yes from signal.**

- At rest, the comparator sees the same node the in-amp sees, behind the 531 Hz
  differential pole `[repo: breath-receive-stage.md]`. 45 mV of hysteresis
  against a few mV of sensor output noise `[from memory: MPXV4006 output noise
  is single-digit mV RMS; gated]` is roughly 10:1. No noise chatter.
- Through the **power-up ramp** it crosses once, slowly: the LT1641's ~50 ms
  ramp `[repo: power-entry.md]` feeds the buck's UVLO, then REF5050, then the
  sensor. Each of those has its own startup, so the crossing is not guaranteed
  monotonic, but any non-monotonicity is bounded and 45 mV of hysteresis handles
  it. **This is not the chatter risk.**
- The chatter risk is **dwell**: a player breathing lightly, or a sensor sitting
  at 150 mV, parks the signal in the neighbourhood of the threshold, and every
  crossing is an `OE` transition, which is a `SYNC` edge at the DAC (D7). The
  design has no way to know this is happening.

### Recommendation (see also D2)

**Stop using a signal as an enable.** The health indication is fine — a
breath-derived comparator *is* a good LED driver, and ADR 0004's "one comparator
reports six things" argument is correct for an *indicator*. It is wrong for a
*gate*, because the health of the analog front end is not a proxy for "the far
end can drive the SPI lines."

The concrete rewiring is in **"The one change that fixes most of this"** below,
and it reuses every part already on the BOM.

---

## D2 — The two mechanisms are in series, not independent **Critical**

The page states them as separate: three circuits deciding "what the module does
when the instrument is absent, asleep, or hung" `[repo]`. The prompt asks
whether they can fight. They do worse than fight — **one is the other's power
switch.**

```
presence ──► OE ──► 74AHCT125 ──► buffered CS ──► 74HC123 trigger ──► CLR
```

The watchdog's **only** input is the buffered, DAC-side `CS` `[repo:
"Retriggered from the buffered, DAC-side CS — never the cable side"]`, and that
node exists only while `OE` is asserted. Therefore:

1. **Every presence dropout is also a watchdog timeout.** D1's inhale case, a
   nicked `BREATH` conductor in a cable the ADR itself calls a consumable and
   tells you to expect intermittency from `[repo: ADR 0004 "treat cable failure
   as routine"]`, a sensor drifting low — all of them assert `CLR` 99 ms later.
2. **The presence detect's reliability is now the watchdog's reliability.** The
   page's claim that the supervision is on a separate rail so "a rack +5 V
   glitch must not be able to clear the outputs mid-phrase" `[repo]` is
   undermined by its own topology under D11: if `OE`'s pull-up is on bus +5 V
   (as this page says), a bus +5 V dropout unpowers the buffer, the DAC-side
   `CS` goes static (D18), and **`CLR` fires anyway**. The rail separation buys
   less than claimed.
3. **There is no path by which "instrument absent" clears the DAC promptly.**
   Unplug the cable mid-note and the DAC holds its last value for the full
   99 ms — the exact "loud, indefinite" failure ADR 0004 opens with, just
   time-limited. ADR 0004's E10 test pulls the umbilical mid-note and watches
   *the breath jack* `[repo]`; nobody is told to watch PITCH, which is where the
   99 ms of drone and the D7 glitch live.

**E10 amendment:** scope PITCH and one MOD during the unplug, not just BREATH.

**Independent corroboration, added to the repo during this review.**
`breath-receive-stage.md`'s new `R1` section reaches the same conclusion from
the other end: "if `R1` opens, the presence detect de-asserts and takes the
**whole SPI link** with it, so pitch and the mods die with breath" `[repo]`.
That page found it as a consequence of one resistor's power rating; this one
finds it as a consequence of the topology. Two routes to the same coupling is
the signal that the coupling, not either resistor, is the defect.

---

## D3 — `R-PRESENCE`'s values cannot make the threshold **Critical**

BOM row 100: `100k / 10k / 1M 1%`, "Threshold ~+100 mV, POSITIVE" `[repo]`.

The 1 MΩ is the hysteresis feedback (row 100 says so), leaving 100k/10k as the
threshold divider. From every rail available in the module `[calc]`:

| Source | 5.0 × 10/110 | 5.21 × 10/110 | −12 × 10/110 |
|---|---|---|---|
| Threshold produced | **454.5 mV** | **473.6 mV** | **−1090.9 mV** |

The intended threshold is **+100 mV**. To get it from 5.21 V you need a ratio of
(5.21 − 0.1)/0.1 = **51.1 : 1** `[calc]` — e.g. 511k/10k, not 100k/10k.

Consequences as drawn:

- **Built as specified, the threshold is 454–474 mV against a signal whose
  resting value is 198 mV.** The comparator never trips, `OE` is never asserted,
  the buffer is never enabled, the LED never lights and the module produces no
  CV at all. This is a build-stopping defect, not a tuning item.
- The *superseded* arrangement fails the same test: 100k/10k from −12 V is
  −1.09 V, not the −200 mV the drawing labels `[calc]`. **Both the old and the
  new threshold are unachievable with the resistors specified**, which suggests
  the three values were never derived at all.
- Row 100 says "Final values at E10." Deferring a value is reasonable; carrying
  three values that are wrong by 4.5× and 5.5× is not, because they will be
  ordered and stuffed.

**Fix:** delete the values from row 100 and replace with the *derivation* plus a
placeholder, or state the divider explicitly. If the tap moves per the
recommendation below, the divider becomes ~2.6 V from 5.21 V (10k/10k) and the
problem disappears.

---

## D4 — LM311 bias current defeats the unplugged state **High**

The tap is at node A, whose source impedance depends on whether the cable is
connected:

| | Thevenin at node A | I_B · R |
|---|---|---|
| Cable connected | 1 MΩ ∥ 11 kΩ = **10.88 kΩ** `[calc]` | 100 nA → **1.1 mV** `[calc]` |
| **Cable unplugged** | **1 MΩ** (R4 alone) | 100 nA → **100 mV**; 250 nA → **250 mV** `[calc]` |

**Name the parameter:** LM311 **I_B (input bias current), typical and maximum,
and its sign** `[gated]`. Figures commonly quoted are 100 nA typ / 250 nA max,
with a bipolar input stage whose base current flows *out of* the input pin
`[from memory — this is exactly the kind of number that must come off the
datasheet]`.

If that magnitude and sign are right, then **unplugged, node A sits at +100 to
+250 mV against a +100 mV threshold** — the detect reads "instrument present"
with nothing plugged in. That is the identical failure mode as the deleted
+12 V divider, arrived at by a different route, and neither the page nor row 100
mentions it. Even if the sign is the other way, the 1 MΩ source impedance means
the *unplugged* node is not 0 V, and "unplugged that node is at 0 V (pulled by
R4/R5)" `[repo: digital-and-supervision.md, R-PRESENCE row]` is false by
100–250 mV.

### The same tap damages the breath channel

Node A is the in-amp's input. The comparator's bias current flowing in R4 is an
input offset to the INA828, multiplied by G = 2.185 `[repo]`:

- 100 nA × 1 MΩ = 100 mV at the input → **218 mV at the in-amp output** `[calc]`.
- That is DC, so `TRIM-BREATH-ZERO` nulls it at commissioning. It does not null
  its **drift**. A bipolar I_B typically changes by roughly 2× over a 0–70 °C
  span `[from memory; gated on the LM311 I_B-vs-temperature curve]`, which is
  ~100 mV of drift at the input → **~218 mV at the in-amp output** → ~2.2 % of a
  10 V span.
- `breath-receive-stage.md` budgets "on the order of 20 mV in 10 V over a full
  warm-up" `[repo]`. **The comparator tap is an order of magnitude worse than
  the entire drift budget of the channel it taps.**

**Fix if the tap stays:** do not tap node A. Either tap ahead of R2 (source
impedance 1 kΩ from the instrument's buffer → I_B error 0.1 mV `[calc]`, but
then the unplugged node is held only through R2+R4 = 1.01 MΩ and D4 returns), or
buffer the tap with the one spare OPA2197 half `[repo: BOM row 13, "Twelve
halves, eleven used… One spare"]`, or use a CMOS/JFET-input comparator whose
I_B is picoamps. **Best: move the tap out of the analog path entirely** —
see below.

---

## D5 — The watchdog cannot see the failure it exists for **High**

ADR 0004's premise: "If the real-time board hangs mid-note, the DAC holds its
last written value and **the rack drones forever**" `[repo]`.

The watchdog retriggers on **edges of `CS`** `[repo]`. It has no view of frame
content, frame count, or whether the numbers are changing. And
`firmware/README.md` mandates, as a rule and not an optimisation:

> "**Refresh everything, every pass. Never write-on-change.**" `[repo]`

So the firmware is *designed* to emit six identical frames every 250 µs forever,
whether or not anything upstream is alive. The failure modes this leaves open:

- **A hang above the output loop.** The DAC service task keeps running (pinned
  to its own core, per `firmware/README.md` `[repo]`) while the key-scan, breath
  or fingering path is wedged. `CS` edges continue; the watchdog sees a
  perfectly healthy instrument; the rack drones forever. This is the headline
  failure, and it is invisible.
- **A DMA-driven or timer-driven SPI transfer whose buffer is stale.** On the
  ESP32-S3 an SPI transaction queue or a continuous DMA descriptor keeps
  clocking without CPU involvement `[from memory]`. The watchdog cannot tell it
  from a healthy loop.
- **A partial hang where one of the six channels stops being recomputed.** No
  mechanism anywhere notices.

**What the watchdog actually detects** is narrower than advertised: *SPI has
stopped*, or *the link is broken*. It does not detect *SPI is stuck*, which is
the stated requirement.

### Fix

A watchdog that cannot be retriggered by a hung system needs an input a hung
system cannot produce. Options, cheapest first:

1. **A heartbeat frame with a pattern only a healthy pass can emit** — e.g.
   alternate the target of one dummy frame between two unpopulated channels
   (6 and 8 are spare `[repo: BOM row 12]`) on alternating passes, and retrigger
   the monostable from a decode of that alternation. Costs a flip-flop and a
   gate; the unused half of the '123 (D17) is not the right part for it, but a
   74HC74 is a dollar.
2. **Retrigger from a toggling line, not a chip-select.** With all eight
   conductors allocated `[repo: ADR 0004 "Revised conductor budget", eight of
   eight]` there is no spare wire, so this means multiplexing a heartbeat onto
   `CS` (a deliberately-shaped extra pulse between frames) and detecting it.
   Feasible, fiddly.
3. **Accept the narrower scope and say so.** If the real requirement is only
   "the link is dead", write that in ADR 0004 and delete the "hangs mid-note"
   justification, because the mechanism does not cover it. **This is the honest
   minimum and it should be done regardless of which option is chosen.**

---

## D6 — The watchdog is software-defeasible, undetectably **High**

Two register-level issues, both gated on **SBAS430 (DAC8568)** and both
load-bearing.

**(a) Clear-code register.** The DAC8568 clear-code register reportedly selects
what `CLR` does, with four options: clear to zero scale, to midscale, to full
scale, and **ignore the `CLR` pin** `[from memory — gate on SBAS430, "Clear Code
Register"]`. BOM row 12 already knows the register exists and firmware/README
already knows it is sticky `[repo]`. What neither says:

> **If a single corrupted frame writes the "ignore `CLR`" code, the hardware
> watchdog is permanently and silently disabled.** With `MISO` deleted, nothing
> can ever discover this.

This page's own argument makes the corrupted frame credible: "a DAC8568 frame
carries the software reset, the clear-code register and the internal-reference
enable — so a mis-framed word is a **sticky** failure" `[repo]`. It draws the
conclusion for pitch values and stops one step short of the conclusion for the
watchdog itself.

**Fix:** firmware must rewrite the clear-code register on the same periodic
schedule as the reference-enable register, and the *interval* matters —
`firmware/README.md` says "a word every few thousand passes" `[repo]`, i.e. up
to ~1 s at 4 kHz `[calc: 4000 × 250 µs = 1.0 s]`. One second of a disabled
watchdog is acceptable; one second of the *wrong clear code* (clear to full
scale) is +10 V on pitch. Tighten to every few hundred passes and put the
clear-code write immediately before any long operation.

**(b) The power-down register is missing from the sticky list.** The DAC8568
command set includes a power-down/power-up command with per-channel modes
(1 kΩ / 100 kΩ / Hi-Z to ground) `[from memory — gate on SBAS430]`.
`firmware/README.md` enumerates the sticky registers as "the internal-reference
enable, and the clear-code register itself" `[repo]` and omits power-down.
A mis-framed word that powers a channel down is **not** repaired by the
refresh-everything rule, because that rule refreshes *data* registers. Add the
power-down register to the refresh list.

---

## D7 — Yes, they fight; mid-frame `OE` is the mechanism **High**

**What happens if the buffer is disabled mid-frame.** `OE` rises
asynchronously; all four outputs go Hi-Z within the AHCT's t_PHZ. At the DAC:

- `SYNC` was **low** (frame in progress). The DAC-side 10 kΩ pull-up now takes
  it **high**. The DAC sees a `SYNC` rising edge partway through a 32-bit word.
- `SCLK` and `DIN` collapse to their DAC-side pull-downs — **low**. If `SCLK`
  was high at that instant, the collapse to low is a falling clock edge; if it
  was low, nothing. Whether the DAC's shift counter advances depends on which
  edge it uses `[gated: SBAS430 — SCLK active edge and the behaviour when `SYNC`
  rises before 32 clocks]`.
- The benign outcome, if the part aborts a short frame, is a discarded word.
  The malign outcome, if the part latches on the 32nd clock regardless, is a
  **garbage command word** — and this page has already argued that a garbage
  word is sticky.

So: **the `OE` gate can manufacture exactly the mis-framing the six pull
resistors exist to prevent**, once per enable/disable event, and D1 makes those
events reachable from normal playing.

**Re-enabling** is safer: the DAC8568 resets its shift counter on the `SYNC`
falling edge `[from memory; gated]`, so framing self-heals on the next frame.
The damage is confined to the one word straddling the transition.

**The other direction — `CLR` asserted while frames are arriving** — does not
occur: `CLR` only falls 99 ms after the last `CS` edge, which by definition is
not mid-frame, and it is *released* by the first `CS` edge of the next frame,
i.e. before that frame's data is shifted. That half of the interaction is clean,
and it is the half the page worried about.

**The interaction it did not consider is the unplug:** presence drops → `OE`
high → possible garbage word (above) → **99 ms of held CV on pitch and four
mods** → `CLR`. Loud, and squarely the failure ADR 0004 declares unacceptable.

---

## D8 — `LDAC` is unmentioned anywhere in the repository **High**

```
$ grep -rn "LDAC" --include=*.md --include=*.csv .   # excluding review/research
(no matches)
```
`[repo]`

The DAC8568 in TSSOP-16 has, by pin count, `VOUT A–H` (8) + `VREFIN/VREFOUT` +
`AVDD` + `GND` + `LDAC` + `CLR` + `SYNC` + `SCLK` + `DIN` = **16 pins exactly**
`[calc from the pin list; gated on SBAS430 for the pinout]`. There is no room
for a separate `DVDD`, which incidentally confirms that `0.7 × AVDD` is the
right threshold to design to (and see D23).

Consequences of leaving `LDAC` unspecified:

- Floating, it is a CMOS input on a precision part in a precision box — the
  precise thing this page spends a whole section condemning for `SCLK`, `MOSI`
  and `CS`.
- Tied **high** with the LDAC register at its default, writes to the DAC
  registers may never reach the outputs at all, depending on which command
  firmware uses `[gated: SBAS430, LDAC register default and the interaction
  between "write and update" commands and the LDAC pin]`.
- The **LDAC register** is another sticky, write-once register a corrupted frame
  can reach — a third entry for firmware's refresh list alongside D6.

**Fix:** tie `LDAC` low (transparent update) on the schematic and add the row to
the BOM, or state explicitly that it is driven and from what. It cannot stay
undrawn on the page that is the schematic of record for the digital path.

---

## D9 — The cable-side `CS` pull-up is on the wrong rail **High**

BOM row 49: "Cable side: **CS to +5V**, SCLK and MOSI to ground" `[repo]`, and
the page's diagram agrees `[repo]`.

The far end of that conductor is an **ESP32-S3 GPIO on a 3.3 V rail**. In the
state ADR 0004 calls normal — "module alive, DAC alive… the state the instrument
spends most of its life in" `[repo]` — the panel toggle is off, so the instrument
is completely unpowered with the cable still plugged in. Then:

- Current flows from bus +5 V through the 10 kΩ, down the cable, into the
  ESP32's input clamp diode and onto the instrument's dead 3V3 rail:
  **(5.0 − 0.7) / 10 kΩ = 430 µA, continuously** `[calc]`.
- The node therefore sits at roughly one diode drop, **~0.7 V, not +5 V.** So
  the documented purpose of the pull — "CS up… so the buffer's inputs do not
  float" `[repo]` — is achieved only in the sense that the node is a valid AHCT
  **LOW** (V_IL = 0.8 V `[from memory: SN74AHCT125, V_IL max 0.8 V over
  V_CC 4.5–5.5 V; gated]`), by **100 mV**, on a clamp voltage with a −2 mV/K
  tempco `[from memory]`. It is not the high the design says it is.
- 430 µA into a dead 3V3 net is **phantom power**: the rail floats up until
  leakage balances, and the ESP32 sits partially biased. This is precisely the
  hazard BOM row 46 calls out for the ADC divider — "5V-before-3V3 sequencing
  otherwise pushes ~2.5 mA into the ADC ESD clamp on every power-up" `[repo]`.
  **The same mistake is present here and unflagged.**

**Fix (cheap, one resistor):** make the cable-side `CS` idle a 3.3 V-class level
— 10 kΩ to +5 V with 20 kΩ to `DIG_GND` gives an open-circuit **3.33 V** with a
6.7 kΩ Thevenin `[calc]`, still a solid AHCT high (V_IH 2.0 V) and harmless to
an unpowered 3V3 pin. Or pull to +5 V through 100 kΩ (44 µA `[calc]`) and accept
the slower node. Or derive a 3.3 V reference — the module has none, which is why
the divider is the pragmatic answer.

### Current cost in the normal "module on, instrument off" state

Asked explicitly, so here is the whole accounting `[calc]`:

| Pull | Current in that state |
|---|---|
| Cable-side `CS` 10 k ↑ +5 V | **430 µA** (into the dead instrument — the only one that costs anything) |
| Cable-side `SCLK` 10 k ↓ | ~0 (node already at 0 V, nothing driving) |
| Cable-side `MOSI` 10 k ↓ | ~0 |
| DAC-side ×3 | ~0 — `OE` is high, outputs Hi-Z, load is DAC input leakage (±1 µA `[from memory]`) |
| `R-OE-PU` 10 k | 0 — comparator off, node at +5 V |
| LED + 820 Ω | 0 — LED off |
| **Total** | **≈ 0.43 mA, all of it the back-drive in D9** |

With the instrument **present** the same accounting gives 3 × 500 µA of
pull-fighting on the DAC side `[calc: 5.0 V / 10 kΩ]` plus 500 µA through
`R-OE-PU` plus 3.66 mA through the LED (D21) — about **5.7 mA** on a bus +5 V
rail that ADR 0004 still budgets at "~10 mA (level shifter only)" (D24).

### Do the pulls fight the drivers?

Yes, trivially, and the numbers are worth having:

- DAC side, buffer driving high: 500 µA per line into the 10 kΩ pull-down
  `[calc]`. Against the AHCT125's rated drive (±8 mA `[from memory: SN74AHCT125
  I_OH/I_OL = ±8 mA at V_CC 4.5 V; gated]`) this costs a V_OH droop of roughly
  500 µA × ~70 Ω ≈ **35 mV** `[calc, using an output impedance inferred from the
  V_OH-at-8 mA spec]`. Irrelevant.
- Cable side, ESP32 driving: 330 µA per pull-down, 170 µA back into `CS` when it
  drives high `[calc]`. Irrelevant.
- **The values are right for the DAC side and wrong for the cable side**, for the
  rail reason above and for the boot reason in D15.

---

## D10 — The drawing is the superseded circuit **High**

Lines 52–57 of the page `[repo]`:

```
   in-amp output ──┐
   (0 V absent,    │   ┌──────────┐
    −0.44 V alive) └───┤ LM311    │
                       │ ±12 V    │
   threshold −200 mV ──┤ EMIT→GND ├──collector──
   (from −12 V)        │ 1M hyst  │
```

Thirty lines later the same page says that arrangement "**stops working**" and
must be replaced `[repo]`. The ASCII diagram is the artefact that gets read at
layout time; the prose is the artefact that gets skimmed. **This will be built
as drawn.**

Same section, two more drafting defects:

- The LED branch `└─[820R]─▷|── panel LED` terminates in a label, not a node.
  The LED's **cathode connection is not drawn anywhere on this page.** From
  `power-entry.md` it returns to the comparator's collector node `[repo]`, but
  this page is the schematic of record for that node.
- The `CLR` pull-down is labelled `R-CLR-PD 10k` on the drawing and is
  `R-CLR-PU` in the BOM (D22).

**Fix:** redraw before anything else on this page is acted on. A schematic page
whose drawing and prose disagree about the circuit is worse than no page.

---

## D11 — The `OE` rail argument **Low — resolved mid-review**

**Resolved while this review was being written.** BOM row 101 previously said
"FROM THE LM317'S 5.21V, NOT BUS +5V" and shouted about it; it has been
rewritten to agree with `digital-and-supervision.md` and `power-entry.md` on
bus +5 V, and it now retracts the earlier note explicitly and correctly: the
5.21 V rule "was right for the COMPARATOR and the WATCHDOG… It is wrong for
this pull-up, which shares a node with the buffer's `OE` inputs" `[repo: row
101, current]`. **That is the right answer and the right reason.** I recorded
the contradiction before the fix landed; it is no longer live.

Two smaller things survive it and are still worth fixing on the page:

- **The page's stated justification is a non-sequitur.** Its rail table gives
  the reason as "Same node as the buffer's inputs — pulling them to a *higher*
  rail would push the AHCT125's input clamps" `[repo]`. `OE` is **not** the same
  node as the buffer's inputs; the inputs come from the cable and are driven
  from 3.3 V logic. The correct reason is the one BOM row 101 now gives — `OE`
  is an *input pin of a 5 V part* and must not be pulled above that part's own
  V_CC. As written on the page, a future reader who notices the node is not in
  fact shared could "correct" the rail back toward +12 V, which is the bug
  `power-entry.md` says drawing the circuit found.
- **The rail table is internally inconsistent.** The row above says
  "**Supervision must not die with the rail it supervises**" `[repo]`. `OE`
  gating *is* supervision, and it is on the bus rail. The resolution is fine —
  a dead buffer is Hi-Z anyway — but the table asserts a principle it then
  breaks one row later without saying so, and D2 point 3 shows the principle is
  weaker in practice than the table claims.

**Had it gone the other way** — 5.21 V into a bus-+5 V input — the overdrive
would have been 0.46 V at bus −5 %, or **0.79 V** with the LM317 at the high
extreme D16 derives `[calc]`, against a gated parameter (*SN74AHCT125 V_I
absolute maximum, and whether it is referenced to V_CC*). Recorded because the
same question returns if anyone moves the buffer to the 5.21 V rail.

## D12 — The retrigger question is posed against the wrong numbers **Medium**

The page's open item: "Whether the '123 empties 220 nF in a 250 µs retrigger
window. It is retriggered **~400 times per timeout period**" `[repo]`. BOM row
54: "Bench-check that it empties 220 nF in a 250 µs retrigger window" `[repo]`.

Both numbers are wrong, and one of them is wrong in the unsafe direction.

**The retrigger count.** The loop writes **six** DAC words per pass
`[repo: firmware/README.md, "books six DAC words per pass"]`, each with its own
`CS` assertion. Per timeout `[calc]`:

```
passes per timeout  = 99 ms / 250 µs          = 396
CS assertions       = 396 × 6                 = 2376
average interval    = 99 ms / 2376            = 41.7 µs
interval inside a burst = 32 bits / 2 MHz     = 16.0 µs
```

So the real question is whether the '123 copes with a retrigger every **16 µs**,
not every 250 µs — **15× tighter than the question as posed**, and ~2376
retriggers, not ~400.

**The wrong quantity.** "Empties 220 nF" is not what has to happen. Between
retriggers the timing capacitor charges by only `[calc]`:

```
dV/dt at t=0 = V_CC / (R·C) = 5.21 V / 0.220 s = 23.68 V/s
in 16 µs:  0.379 mV   (83 pC into 220 nF)
in 250 µs: 5.92 mV    (1.30 nC)
```

The discharge transistor does not have to empty the capacitor; it has to remove
**83 pC**. The question is therefore not "can it sink 220 nF" but
**"how long is the internal discharge path held on, and at what R_on"** — two
parameters, both on the datasheet.

**Why it still matters.** Modelling steady state as `V* = α^6 (V* + 5.92 mV)`
where α = exp(−t_dis/(R_on·C)) is the fraction surviving each retrigger `[calc]`:

| R_on | discharge window | V* (capacitor's resting level) |
|---|---|---|
| 100 Ω | 16 µs (= `CS` low) | **0.08 mV** — fine |
| 100 Ω | 1 µs | 18.9 mV — fine |
| 100 Ω | 100 ns | 214 mV — fine |
| 1 kΩ | 16 µs | 10.8 mV — fine |
| 1 kΩ | 100 ns | **2.17 V** — against a threshold around 3.3 V, marginal |
| 10 kΩ | 100 ns | **21.7 V** — never holds off; **the watchdog fires during normal traffic** |

So the concern is real, but it is decided entirely by whether the '123 holds its
discharge transistor on **for the duration of the trigger pulse** (safe: `CS` is
low for 16 µs) or **for a short fixed internal window** (potentially fatal).

**Name the parameters, gate the conclusion:** *74HC123 — internal C_ext
discharge-transistor on-resistance, and whether the discharge is held for the
trigger pulse width or for a fixed internal interval; plus any specified
minimum retrigger period.* `[gated]`

**Better fix than bench-checking it:** this whole circuit is a supervisor built
from a monostable. A dedicated watchdog IC (MAX6369-class, pin-selectable
timeout; TPS382x-class, fixed) takes a `WDI` edge, has a defined power-on reset,
a push-pull or open-drain output, and no R_ext/C_ext at all `[from memory —
confirm the specific part's timeout options]`. It replaces the '123, `R-WDT`,
`C-WDT`, the power-on-reset RC that is still open, and D13's tolerance problem,
with one part. For a population of one this is cheaper in bench time than
characterising a monostable's discharge transistor.

---

## D13 — 1 MΩ / 220 nF is at the edge of the part's specification **Medium**

`t = 0.45 · R · C = 0.45 × 1 MΩ × 220 nF = 99.0 ms` `[calc]` — the arithmetic
is right `[repo]`. What sits behind it is not comfortable:

**Timing current vs leakage.** At 5.21 V the charging current at t = 0 is
`5.21 V / 1 MΩ = 5.21 µA` `[calc]`. The HC family's specified input leakage is
±1 µA `[from memory: I_I max ±1 µA for 74HC; gated]`. If the R_ext/C_ext pin's
leakage is anywhere near that, it is **±19 % of the timing current on its own**
`[calc]`.

**Combined spread** with X7R's ±15 % temperature coefficient `[from memory]`:

```
short:  99 ms × 0.85 / 1.19  =  70.7 ms
long:   99 ms × 1.15 / 0.81  = 140.6 ms
```
`[calc]`

The page says "±30 % on a 99 ms timeout changes nothing" `[repo]`. The spread is
wider than ±30 %, and more importantly **the comparison is against the wrong
thing**: the page's own last open item is an ESP32 flash-cache stall of unknown
duration `[repo]`. A 70.7 ms floor against an unmeasured stall is not a margin,
it is an unquantified risk. Measure the stall (the page says so) *and then* size
the timeout against the measurement, with the 70.7 ms figure as the number to
clear.

**R_ext range.** `[gated: 74HC123 — minimum and maximum permitted R_ext.]` For
several parts in this family the specified maximum is 1 MΩ `[from memory]`,
which puts this design *at* the limit with no margin, and some family members
specify less. Combined with the 5.21 µA timing current this is the wrong corner
of the part's operating space to be sitting in.

**"74HC123 or equivalent"** `[repo: BOM row 54]` — the 0.45 coefficient is
**not portable**. The 74HC123, 74HCT123, CD74HC123, 74HC221 and CD4538B do not
share one timing formula, and some include an additive term at small C_ext
`[from memory]`. A second-source substitution can move the timeout by ~2×. Pin
the exact part number in the BOM, or the row is not a specification.

---

## D14 — 2 MHz over 2 m of Cat5, and the series resistor is on the wrong line **Medium**

### Will it work?

Yes, marginally, and the margin is smaller than ADR 0004 claims.

**Is it a transmission line?** Cat5 propagation is ~5 ns/m `[from memory: NVP
≈ 0.65–0.70c]`, so 2 m is ~10 ns one-way, **20 ns round trip**. An ESP32-S3
GPIO edge is a few ns `[from memory]`. t_r < 2·t_pd, so **yes** — this must be
treated as a transmission line, not a lumped RC.

**ADR 0004's arithmetic is wrong.** It says "`R-MOSI-SER` at 220 Ω with ~200 pF
of cable is a ~7.9 MHz corner, so 2 MHz has margin" `[repo]`. `[calc]`:

| R | C | 1/(2πRC) |
|---|---|---|
| 220 Ω | 200 pF | **3.62 MHz** |
| 220 Ω | 104 pF (2 m at ~52 pF/m `[from memory]`) | 6.96 MHz |
| **100 Ω** | **200 pF** | **7.96 MHz** |

**7.9 MHz is the figure for 100 Ω, not 220 Ω.** The number in the ADR belongs to
the resistor value the ADR says it might fall back to, not to the one specified.
On its own model the real corner is 3.62 MHz and the 10–90 % rise time is
2.2·RC = **97 ns** `[calc]` — 39 % of a 250 ns half-period. It closes, with
about 1.8× of margin, not the ~4× the stated number implies.

**Transmission-line treatment, `MOSI`.** Source ≈ 220 Ω + ~30 Ω driver = 250 Ω
into Z₀ ≈ 100 Ω, far end open (10 kΩ ∥ CMOS). Γ_source = +0.43 `[calc]`. The far
end staircases `[calc]`:

```
t = 10 ns  1.886 V     t = 70 ns  3.189 V
t = 30 ns  2.694 V     t = 90 ns  3.252 V
t = 50 ns  3.040 V     t = 110 ns 3.280 V
```

It crosses the AHCT's V_IH of 2.0 V on the **second** bounce, at ~30 ns. Fine at
2 MHz, monotonic, no double-clocking. Over-damped but safe.

**`SCLK` has no series resistor at all.** `R-MOSI-SER` is qty 1, `MOSI` only
`[repo: BOM row 50]`. Source ≈ 30 Ω into 100 Ω, Γ_source = **−0.54** `[calc]`:

```
t = 10 ns  5.077 V   ← overshoot
t = 30 ns  2.343 V
t = 50 ns  3.815 V
t = 70 ns  3.023 V   … converging on 3.3 V
```

and on the falling edge, by symmetry, the first excursion is to **−1.78 V**
`[calc]`, clamped by the AHCT's input diode, followed by a rebound to **+0.95 V**
`[calc]`.

Three problems, all on the clock:

1. **5.08 V into an AHCT input on a rail that may be 4.75 V.** Whether that is
   inside absolute maximum is the same gated parameter as D11 — *SN74AHCT125
   V_I absolute maximum, and whether it is referenced to V_CC.*
2. **Clamp current on every falling edge**: roughly (1.78 − 0.5)/100 Ω ≈ 13 mA
   `[calc, order of magnitude]`, at 2 million edges per second during a burst,
   through the cable and back through `DIG_GND`.
3. **The +0.95 V rebound sits in the AHCT's indeterminate band** (V_IL 0.8 V,
   V_IH 2.0 V `[from memory; gated]`) for ~10 ns. A plain buffer driven into its
   indeterminate band can emit a runt or a slow output edge. **This is exactly
   what the "74AHCT14 if edge cleanup is needed" note is hedging against**
   `[repo: ADR 0004]`, and the arithmetic says the line that needs it is
   `SCLK`, which nobody has protected.

**Fix, cheaper than a Schmitt:** **put 68–100 Ω in series with `SCLK` at the
driving end** (source-matching a ~30 Ω driver to a 100 Ω line) and **reduce
`MOSI` to the same value**. ADR 0004 already contemplates 100 Ω "closer to a
real source match on Cat5's ~100 Ω anyway" `[repo]` — it just never extends it to
the clock. `CS` should get one too; it is slow, but it is the line where a stray
edge is sticky.

### Failure mode if it does not work

**A double-clock on `SCLK` shifts the DAC's 32-bit frame by one bit.** The
command and address nibbles shift with it, so the word does not merely carry a
wrong value — it can land in the control space: software reset, clear code
(D6a), reference enable, power-down (D6b), LDAC register (D8). With `MISO`
deleted **nothing can ever detect it**, and by this page's own argument such a
word is sticky where a corrupted data bit self-heals in 250 µs `[repo]`.

The practical signature is: works on the bench with a short lead, fails
occasionally with the real cable, in a way that looks like a firmware bug, on a
system with no readback. That is why E11 is a gate before the body bonds
`[repo: ADR 0004]` — and E11 should be told to look for **frame-shift** symptoms
specifically (unexpected channel changes, reference dropouts), not just eye
diagrams.

---

## D15 — What the DAC sees during the instrument's boot **Medium**

The sequence, from the repo's own numbers:

| t (from panel toggle) | Event |
|---|---|
| 0 | `LT1641-1` begins its programmed ramp `[repo: power-entry.md, ~50 ms]` |
| ~30 ms | umbilical +12 V passes the `R-78E5.0`'s input minimum `[repo: ADR 0004 "a buck that needs more than 6 V in"]` |
| ~35–60 ms | instrument 5 V → REF5050 → MPXV4006DP → OPA2197 buffer → node A reaches +0.2 V |
| **~60 ms** | **presence asserts, `OE` goes low, the buffer is ENABLED** |
| ~100–400 ms | ESP32-S3 ROM bootloader, 2nd-stage bootloader, OTA-rollback check, NVS read, app init `[from memory — measure it at E5]` |
| then | first SPI frame |

**So the buffer is enabled for roughly 100–400 ms during which the instrument's
SPI pins are in their ROM/boot state, and everything they do is level-shifted to
5 V and presented to the DAC.**

What saves it: **`CS` alone.** The module's 10 kΩ holds `CS` high, the DAC
ignores `SCLK` and `DIN` while `SYNC` is high, and no frame can be latched. That
is a real and adequate defence — **but it is the one pull with the rail problem
in D9**, and it is defeated in any state where the far end drives `CS` low.

The residual exposures, all real:

1. **`SCLK`'s DC level is not guaranteed valid.** The ESP32's internal pull-up
   is nominally ~45 kΩ `[from memory; gate on the ESP32-S3 datasheet, R_PU]`.
   Against the module's 10 kΩ pull-down `[calc]`:
   `3.3 × 10/(10 + 45) = 0.60 V` — a valid AHCT low (0.8 V) by 200 mV. But the
   condition for validity is `R_PU ≥ (3.3 − 0.8)/0.8 × 10 kΩ = 31.25 kΩ`
   `[calc]`. **A 30 kΩ internal pull-up puts the buffer's clock input at 0.83 V —
   inside the indeterminate band, with the buffer enabled and the DAC
   listening, for the entire boot.** The module cannot see or control that
   parameter.
2. **Strapping pins and the ROM UART.** `firmware/README.md` records the service
   header pins (`EN`, `IO0`, `U0TXD`, `U0RXD`) `[repo]` but records **no
   constraint on which GPIOs carry the umbilical SPI**. If `CS` lands on a
   strapping pin, or on a pin the ROM drives, the boot exposure becomes a real
   frame.
3. **Peripheral-init ordering.** Configuring the SPI host before driving `CS`
   high glitches `CS` low. `firmware/README.md` says nothing about it.
4. **Download mode.** Holding `IO0` leaves the pins in ROM states indefinitely,
   with the buffer enabled the whole time. This is a bench state, and the
   service header exists precisely to get into it `[repo]`.

**Fixes, all in `firmware/README.md`:** add an architecture constraint that (a)
the three umbilical SPI pins must avoid strapping pins and ROM-driven pins,
(b) `CS` must be driven high as a plain GPIO before the SPI host is configured,
(c) internal pull-ups must be disabled on `SCLK` and `MOSI`, and (d) the first
frame of every pass is a throwaway write to an unpopulated channel (6 or 8
`[repo: BOM row 12]`), which also absorbs the truncated-first-frame case in the
recommendation below. Verify (a)–(c) at E11 with a logic analyser on the DAC
side of the buffer during a cold boot — not on the cable side.

---

## D16 — The LM317 window runs past the DAC's maximum supply **Medium**

ADR 0004: "the worst-case spread is about 0.66 V" about a 5.21 V nominal
`[repo]`, i.e. **4.88 V to 5.54 V** `[calc]`. ADR 0004 also states the DAC8568
is "a 2.7–5.5 V part" `[repo]`.

**5.54 V > 5.5 V.** The documented tolerance window's upper end is outside the
DAC's specified supply range. The ADR's answer — select R2 on the bench at E7 —
is the right answer, but the procedure as written pushes **upward**: "raise the
top codes and find where they start compressing against AVDD" `[repo]`, and BOM
row 39 says "buy a handful of neighbouring E96 values" `[repo]`. Nothing in
either document states a **ceiling**.

**Fix:** write the ceiling into row 39 and into ADR 0004's E7 step. The AVDD
selected on the bench must satisfy `V_out(max over line, load and temperature)
≤ 5.5 V`, which means the *measured* value has to sit meaningfully below 5.5 V —
the LM317's line regulation against a +12 V rail that moves with the rack, and
its load and temperature regulation, all have to fit underneath. 5.2–5.3 V
measured is a sensible target; 5.45 V is not.

### The level arithmetic at every corner

Asked explicitly. `[calc]` throughout; thresholds `[from memory, gated]`.

**Stage 1 — 3.3 V logic into the AHCT125 (TTL thresholds, V_IH 2.0 V,
V_IL 0.8 V for V_CC 4.5–5.5 V).**

| Corner | Value | Margin |
|---|---|---|
| ESP32 V_OH min (0.8 × 3.3) | 2.64 V | +0.64 V over V_IH |
| …after the `MOSI` divider 10 k/(10 k + 220 Ω) | 2.58 V | +0.58 V |
| Boot, `SCLK` with a 45 kΩ internal pull-up | 0.60 V | −0.20 V under V_IL ✓ |
| Boot, `SCLK` with a 30 kΩ internal pull-up | 0.83 V | **+0.03 V — invalid** (D15) |
| Instrument off, `CS` at the clamp | ~0.7 V | −0.10 V under V_IL, marginal (D9) |

The AHCT's TTL thresholds are independent of V_CC over 4.5–5.5 V, so the bus
rail at −5 % does not move this stage at all. **This is the part of the design
that is right, and it is why AHCT was the correct family choice.**

**Stage 2 — AHCT125 output into the DAC8568 (CMOS thresholds, 0.7 × AVDD /
0.3 × AVDD `[repo: ADR 0004; gated on SBAS430]`).**

| AVDD | V_IH = 0.7·AVDD | Bus +5 V | AHCT V_OH at 500 µA | Margin |
|---|---|---|---|---|
| 5.21 V nominal | 3.647 V | 5.00 V | ~4.965 V | **+1.32 V** |
| 5.21 V | 3.647 V | **4.75 V (−5 %)** | ~4.715 V | **+1.07 V** |
| **5.54 V (high extreme)** | **3.878 V** | **4.75 V (−5 %)** | ~4.715 V | **+0.84 V** |
| 4.88 V (low extreme) | 3.416 V | 5.25 V (+5 %) | ~5.213 V | +1.80 V |

`V_OH` taken as `V_CC − I·R_out` with `R_out ≈ 70 Ω` inferred from the AHCT's
V_OH-at-8 mA specification `[calc; gated]`. **Every corner closes with ≥0.84 V.**
ADR 0004's claim of "a volt of margin" at the sagging rail is right to within
the value of the DAC-side pull-downs `[repo]`.

The low side: `V_IL = 0.3 × 5.21 = 1.563 V` against an AHCT V_OL of ~35 mV
`[calc]`. Enormous.

**The one corner that does not close** is the overvoltage direction: bus at
+5 % with AVDD at its low extreme gives 5.213 V into a pin whose absolute
maximum is `AVDD + 0.3 = 5.18 V` `[calc; gated on SBAS430 for the +0.3 V figure]`
— **over by 33 mV**. No clamp conducts at 33 mV of forward bias, so this is a
paper violation rather than a physical hazard, but it is a violation the project
has not noticed, and it gets worse if the rack's +5 V is worse than ±5 % (ADR
0004 itself calls it "the least-regulated rail in Eurorack" `[repo]`).

**Stage 3 — AHCT125 output into the 74HC123 trigger (CMOS thresholds at the
'123's own 5.21 V rail).** This is the only HC (not HCT) threshold in the chain
and it is the one cross-rail interface nobody has checked `[calc]`:

```
'123 V_IH = 0.7 × 5.54 V (worst high AVDD) = 3.878 V
AHCT V_OH at bus −5 %                       = 4.715 V   → margin +0.84 V ✓
'123 V_IL = 0.3 × 4.88 V                    = 1.464 V
AHCT V_OL                                   = 0.035 V   → margin 1.43 V ✓
```

It closes. Say so in the page, because it is not obvious and the next reader
will have to redo it.

---

## D17 — Unused gates and halves are not tied off **Medium**

Three omissions, all of the same class the page spends a section condemning:

1. **The 74AHCT125's fourth gate.** BOM row 35: "Covers SCLK MOSI CS with a
   **spare gate**" `[repo]`. Nothing says what its input connects to. A floating
   CMOS input is the crowbar-current problem this page exists to fix, and it is
   on the same die as the three lines being protected. **Tie the spare input to
   `DIG_GND`.** (Its `OE` may stay on the common node; an unconnected buffer
   output is harmless.)
2. **The 74HC123's second half.** The '123 is a **dual** monostable `[from
   memory; gated]`. The page and BOM row 54 treat it as a single. Its A, B and
   `CLR` inputs must be tied per the datasheet or it will free-run or crowbar —
   inside the precision analog box, on the supervision rail.
3. **The '123's own `CLR` pin.** The page lists "a power-on reset RC on the
   '123's own `CLR`" as still open `[repo]`. Open is the wrong status: the pin
   must be tied **high** to run at all. The open item is the RC; the tie is not
   optional and is not drawn.

On the POR priority, a mild **de-escalation** in the page's favour: the '123 and
the DAC are on the same 5.21 V rail, and the DAC's own power-on reset clears it
to zero scale regardless `[repo: BOM row 12, "C also clears to ZERO scale"]`. If
the '123 emits a spurious 99 ms pulse at power-up — a known behaviour of this
part family `[from memory; gated]` — the consequence is that `CLR` is released
for 99 ms while the DAC is already at zero scale and nothing is writing.
**Harmless.** The POR RC is good practice and belongs on the drawing, but it is
not the risk the page's placement in the open list implies, and item 2 above is
more urgent than item 3.

---

## D18 — "Kills the buffer and nothing else" is false **Medium**

ADR 0004 accepts a reversed or row-offset ribbon putting +12 V on the bus +5 V
pin: "kills the buffer and nothing else, which is why the +5 V entry gets no
protection network of its own" `[repo]`, echoed in `power-entry.md` `[repo]`.

Trace what an unpowered 74AHCT125 does to the DAC-side nodes:

- The DAC-side `CS` pull-up (to whichever rail — the page does not say, see
  below) sources current into the buffer's dead output. A CMOS output's PMOS
  body diode conducts into a V_CC of 0 V, so the node is dragged to roughly one
  diode drop: **~0.7 V**, with `(5.21 − 0.7)/10 kΩ = 451 µA` flowing `[calc]`.
- 0.7 V is a valid **LOW** at the DAC (`V_IL = 0.3 × AVDD = 1.56 V` `[calc]`).
  **`SYNC` is therefore held asserted indefinitely**, with the interface armed
  and the shift counter waiting.
- The '123's trigger sees a static low → no edges → timeout → **`CLR` asserted**.

The outcome is *safe* (the DAC parks), but the mechanism is not the one
documented, and the claim as written is wrong in two respects: a dead buffer
also parks the DAC, and it holds `SYNC` low through a back-drive path nobody has
drawn. Worth correcting because the claim is load-bearing — it is the stated
reason the +5 V entry gets no protection.

**Also unstated anywhere:** **which rail the three DAC-side pulls go to.** The
page's diagram just says `[R-SPI-PULL ×3]` `[repo]`. It matters: on bus +5 V they
die with the buffer (the case above); on the LM317's 5.21 V they hold `SYNC` at
a clean high when the buffer is merely Hi-Z, which is what you want. **They
should be on 5.21 V, the DAC's own rail**, and the page should say so.

---

## D19 — The pin map gives two SPI signals no return **Medium**

ADR 0004's map `[repo]`:

| Pins | Pair | Signal |
|---|---|---|
| 1, 2 | ✓ | BREATH / AGND |
| 3, 6 | ✓ | +12V / PWR_GND |
| 4, 5 | ✓ | **MOSI / CS** |
| 7, 8 | ✓ | SCLK / DIG_GND |

The map is optimised for the analog pair, and the reasoning about the power pair
acting as a guard is sound `[repo]`. But:

- **`MOSI` and `CS` share a twisted pair with no return conductor in it.** A
  twisted pair maximises coupling between its two conductors — that is its
  purpose. Here that means `MOSI`'s eight transitions per frame are maximally
  coupled onto `CS`, which is the one line where this page argues a stray edge
  is a **sticky** failure `[repo]`. During normal traffic `CS` is driven from a
  ~30 Ω source and the risk is small; during the boot window (D15) and the
  instrument-off state (D9) it is held only by 10 kΩ and is much more exposed.
- **All three SPI return currents have to come back through the single
  `DIG_GND` conductor in the `SCLK` pair.** `MOSI`'s and `CS`'s return therefore
  flows in the clock's own reference conductor — textbook common-impedance
  coupling, directly onto the fastest edge in the system. A real number needs the
  pair's loop inductance and the actual edge currents `[gated — this is an E11
  measurement, not a calculation]`, but the topology is wrong on its face and
  ADR 0004's confidence ("Nothing with a sharp edge is ever adjacent to the
  analog pair" `[repo]`) addresses a different question than the one that bites.
- The practical consequence lines up with D14: `SCLK`'s ringing and its clamp
  currents return through the same conductor that references `SCLK`.

**Fix options, in order of cost:** (a) nothing, and let E11 measure it — legitimate,
since all eight conductors are allocated and there is no free wire; (b) swap so
that the pairs are `CS`/`DIG_GND` and `SCLK`/`MOSI`, which is worse (two fast
signals in one pair); (c) accept that `MOSI` and `CS` are a pair and **slow
`MOSI`'s edges deliberately** — which the existing 220 Ω already does, and is
the one thing the over-damped value is genuinely good for. Say (c) out loud in
ADR 0004 as the actual justification for 220 Ω, since the stated one (D14) is
arithmetically wrong.

---

## D20 — What happens when `CLR` is *released* is undocumented **Low-Medium**

`CLR` is released by the **first `CS` edge** after a timeout. Nothing in the
repository says what the DAC does at that moment, and there are two possible
behaviours with very different outcomes `[gated: SBAS430 — does `CLR` load the
clear code into the DAC registers (latched), or force the outputs only while the
pin is low?]`:

- **Register-clearing (latched):** on release the outputs stay at zero scale
  until firmware writes. Silence. Correct.
- **Level-forcing:** on release the outputs revert to the pre-`CLR` register
  contents — **the stuck values the watchdog just cleared**.

The second case matters because the interesting failure is not a clean
disconnection but a **marginal** one: an instrument brown-out-looping on a sagging
cable emits a burst of `CS` edges every few hundred milliseconds. With
level-forcing behaviour, that gives `CLR` released → stuck note back → 99 ms →
`CLR` → released → stuck note back: **a ~3 Hz stutter of the drone**, which is
arguably worse than the drone. With latched behaviour you get silence.

This is one datasheet line and it decides the character of the design's main
failure mode. Put it in the page.

---

## D21 — The panel LED **Low**

`power-entry.md` and BOM row 83: `(5.21 − 2.0) / 4 mA ≈ 800 Ω → 820 Ω`, "on the
5 V rail it is ~3.8 mA" `[repo]`.

- **The sizing uses the wrong rail.** Both documents place the LED on bus +5 V;
  the arithmetic uses 5.21 V.
- **The current is wrong:** `(5.0 − 2.0)/820 = 3.66 mA`, not 3.8 mA `[calc]`. At
  bus −5 %: `(4.75 − 2.0)/820 = 3.35 mA` `[calc]`.
- **The LED's colour is unspecified** — BOM row 82 says only "3 mm LED —
  diffused" `[repo]`. V_f 2.0 V is a red assumption. A green or blue diffused
  3 mm part is V_f ≈ 3.0–3.2 V `[from memory]`, giving `(5.0 − 3.2)/820 =
  2.20 mA` `[calc]` — dim, and at bus −5 % dimmer still. Specify the colour, or
  specify the resistor against the worst V_f.
- **The cathode connection is not drawn on this page** (D10).
- **The LED now flickers with breath.** Per D1 the comparator drops out for
  negative differential pressure, so the module's only health indicator blinks
  when the player inhales. BOM row 82 says this LED "is also the only thing that
  says why the instrument went dark" `[repo]` — an indicator that flickers during
  normal playing cannot do that job.
- Minor but worth noting: the LED's ~3.7 mA returns through the LM311's emitter
  to the ground star. It is DC and constant, so it does not modulate anything —
  but it is bus-+5 V current returning through the analog ground region, and the
  grounding section of ADR 0004 is strict about exactly this kind of thing
  `[repo]`. Route the emitter to the star deliberately, not to whatever pour is
  nearest.

---

## D26 — A designed-safe +12 V fault may invert the comparator **Medium**

*(Found late, after `breath-receive-stage.md` was revised mid-review; numbered last rather than renumbering everything above it.)*

ADR 0003 and `breath-receive-stage.md` treat a **sustained +12 V fault on the
`BREATH` conductor as a designed-safe case** — the instrument-side buffer runs
from +12 V precisely so the fault sits at the rail rather than above it `[repo]`.
The crossover-lead case in ADR 0004 makes it reachable from a consumable patch
lead `[repo]`.

Under that fault the comparator's input node goes to `[calc]`:

```
12 V × 1 MΩ / (1 MΩ + 11 kΩ) = 11.87 V
```

The LM311 runs on ±12 V `[repo: BOM row 99]`. **11.87 V is 0.13 V below its own
V+.** *Name the parameter: LM311 input common-mode range referenced to V+ —
commonly quoted as extending only to about V+ − 1.5 V* `[from memory; gated]`.
If that is right, the fault drives the comparator well outside its
common-mode range, where the possible behaviours are an indeterminate output,
**output phase inversion**, or input-stage damage `[gated: LM311 input voltage
absolute maximum and CMR]`.

Consequences, all of which chain through D2 and D7:

- If the output holds "present", the module keeps running with a breath jack
  clipped hard high — which `breath-receive-stage.md` already identifies as a
  hazard of this fault `[repo]`.
- If the output goes indeterminate or inverts, `OE` chatters, and every `OE`
  transition is an asynchronous `SYNC` edge at the DAC (D7) with the
  garbage-frame consequences of D6.

Neither the module-end protection (`R2`/`R3` and the BAV99 to ±12 V) nor the
existing analysis covers the *comparator*, because the comparator was added to
that node after the protection was reasoned about. **Fix:** clamp the
comparator's input separately (a 100 kΩ series resistor into the LM311 costs
nothing and drops the fault to a harmless current), or — better — take the
comparator off that node entirely, per the recommendation below.

---

## D22–D25 — Bookkeeping **Low**

**D22 — fixed mid-review.** The BOM designator was `R-CLR-PU` on a row whose own
text said, in capitals, "**PULL-DOWN, not pull-up**", while the page's drawing
called it `R-CLR-PD`. Row 71 is now `R-CLR-PD` `[repo, current]`. Nothing left to
do; recorded so the fix is not undone.

**D23 — mostly fixed mid-review.** Row 43 was qty 19 and enumerated "5 × OPA2197…
**LM393**"; it is now qty 22 with "6 × OPA2197 on +/−12 V = 12, INA828 = 2,
LM311 on +/−12 V = 2" `[repo, current]`, which matches my count of the op-amp
packages and the comparator's two supply pins.

**One term survives:** the row still reads "DAC8568 AVDD+DVDD = 2". By pin count
the TSSOP-16 DAC8568 has no room for a separate `DVDD` (D8), so the correct
total is **21**, not 22. Gate on SBAS430's pinout before changing it — and if
`DVDD` really is absent, that also confirms the `0.7 × AVDD` threshold the whole
level-shifter argument rests on.

**D24.** ADR 0004's rail table still reads "+5 V | ~10 mA (level shifter only)"
`[repo]`. The bus +5 V rail now also carries `R-OE-PU` (0.5 mA) and the panel
LED (3.66 mA) when the instrument is present — about **4.2 mA** `[calc]` — and
"level shifter only" is contradicted by `power-entry.md`'s own diagram on the
same subject. Separately, the figure ignores **ΔICC**: HCT-family inputs held at
a TTL high rather than at the rail draw a static supply current adder. *Name the
parameter: SN74AHCT125 ΔICC per input, at V_I = 3.3 V with V_CC = 5 V* `[gated]`.
With three inputs permanently at 3.3 V this could be a meaningful fraction of a
10 mA budget. Re-derive the row.

**D25.** "Expert Sleepers ships this circuit, **at this hysteresis value**, in two
modules" `[repo]`. A 1 MΩ feedback resistor is not a hysteresis value — the
hysteresis is set by the ratio of that resistor to the impedance of the node it
feeds. With the specified 100k/10k divider `[calc]`:

```
node impedance      = 100k ∥ 10k = 9.09 kΩ
hysteresis band     = 5.0 V × 9.09k / (1 MΩ + 9.09k) = 45.0 mV
```

45 mV is a reasonable number here — but it is a *consequence* of the divider,
which D3 shows is wrong, so the quoted 1 MΩ does not transfer from whatever
circuit it came from. Also: the page opens with "**No surveyed Eurorack module
has any of it**" `[repo]` and then cites Expert Sleepers shipping two pieces of
it. Both claims may be defensible under different readings of "it", but as
written they sit badly together, and I cannot check either from here.

---

## The one change that fixes most of this

D1, D2, D3, D4, D7 and half of D11 are all consequences of a single decision:
**the digital buffer's enable is derived from an analog signal.** Undo that and
they go together.

### Proposal: `OE` from the watchdog, LED from the watchdog, comparator reused as the level shifter

```
cable-side CS ──┬──► 74AHCT125 input (as today)
                │
                └──► 74HC123 trigger        (moved: cable side, not DAC side)

74HC123  Q  ──► DAC CLR                      (as today)
74HC123  Q  ──► LM311 IN−, against ~2.6 V from a 10k/10k divider on 5.21 V
LM311 collector ──┬──► OE ×4   (bus +5 V pull-up, as today)
                  └──► panel LED (as today)
```

**Why each piece:**

- **Retrigger from the cable side.** The page forbids this: "from the cable side
  a floating input can retrigger it forever and defeat it in precisely the state
  it exists for" `[repo]`. That objection was written against a design without
  cable-side pulls. **The same page adds `R-SPI-PULL` ×3 on the cable side**
  `[repo]`, so the node is no longer floating — it is held at a defined idle in
  every absent state (5 V unplugged; ~0.7 V plugged-but-off, D9). Static levels
  produce no edges and the watchdog still times out. **The second fix on this
  page removes the rationale for the first, and nobody noticed.**
- **This is also forced.** Driving `OE` from `Q` while retriggering from the
  buffered `CS` is a **deadlock**: at power-up Q is low → `OE` disabled → no
  buffered `CS` → no retrigger → `OE` never enables. The trigger must come from
  upstream of the gate.
- **`OE` can only change at a frame boundary.** It de-asserts 99 ms after the
  last edge — by definition not mid-frame — and asserts *on* a `CS` falling edge,
  which is a frame start. **D7 disappears entirely.**
- **The one new timing constraint:** the buffer must enable between the `CS`
  falling edge and the first `SCLK` edge. That budget is the ESP32's CS-to-SCLK
  setup (~250 ns at 2 MHz for a half-clock setup `[from memory]`) against the
  '123's trigger-to-Q delay plus the AHCT's t_PZL (tens of ns `[gated]`). It
  closes with room, and the **throwaway first frame** from D15 removes the risk
  entirely: the only frame that can ever be truncated is one written to an
  unpopulated channel.
- **The LM311 earns its keep as a level shifter.** It stays on ±12 V with its
  emitter at ground and its collector on the bus +5 V pull-up, exactly as today
  — so D11 stops mattering, because the only cross-rail interface becomes a
  comparator *input*, which does not care what rail it is referenced to. The
  1 MΩ hysteresis now works against a 10k/10k node (5 kΩ) giving ~26 mV
  `[calc]`, against a logic-level input. `R-PRESENCE` becomes two equal
  resistors and D3 evaporates.
- **The LED means something better.** Today it means "the breath front end is
  alive". Under this proposal it means "**frames are arriving**", which is the
  only thing the module actually needs to know and the thing a player most needs
  told. It stops flickering with breath.
- **The in-amp input node is left alone**, so D4's drift problem and the
  comparator's loading of the breath channel both go away.

**What is lost, honestly:** the breath comparator's role as a six-in-one health
report — cable connected, +12 V reaching the far end, REF5050 alive, sensor
alive, buffer alive, both analog conductors intact `[repo]`. That report was
genuinely valuable and this proposal deletes it. Three responses: (i) most of
those conditions are *implied* by frames arriving, since the instrument only
boots if +12 V reaches it; (ii) the ones that are not — sensor and in-amp health
— are exactly what E10's jack test covers `[repo]`; (iii) if the report is
wanted, keep the breath comparator as a **second, indicator-only** LM311 half —
but note the package is a single `[repo: row 99, SOIC-8]`, so it is another part.
**A health indicator that cannot disable anything is a good idea. The same
signal as an enable is not.**

**Cost:** two nets, two resistor values, zero new parts, and it does not touch
the rails, the buffer, the DAC or the timing components. D5 and D6 are *not*
fixed by it and need the separate work described in those sections.

---

## What I checked and found sound

Listed because a review that only lists defects is not a review.

- **`t = 0.45 · R · C` = 99.0 ms for 1 MΩ × 220 nF** `[calc]`. The arithmetic is
  exact. (The coefficient's portability is D13; the value is right.)
- **Six frames at 2 MHz = 96 µs = 38.4 % of a 250 µs pass** `[calc]` — ADR
  0004's figure `[repo]` is correct, and the loop closes at 2 MHz where it
  demonstrably would not have at 0.6 MHz.
- **The choice of AHCT over AHC or LVC is right, and for the right reason.** TTL
  input thresholds (2.0 V / 0.8 V) are specified independently of V_CC across
  4.5–5.5 V `[from memory; gated]`, so the 3.3 V input stage is unaffected by the
  rack's ±5 % — the one stage where the bad rail could have hurt, and it does
  not. Every 3.3 V-into-AHCT corner in D16's first table closes.
- **`0.7 × AVDD` closes at every rail corner with ≥0.84 V** `[calc, D16]`, including
  bus +5 V at −5 % with AVDD at its documented high extreme. The core claim of
  ADR 0004's level-shifter section survives arithmetic.
- **Putting the '123 and the LM311 on the LM317's rail rather than bus +5 V is
  correct**, for the reason given: a rack +5 V transient must not be able to
  assert `CLR` `[repo]`. (It is only partly achieved — D2 point 3 — but the
  intent and the rail choice are right.)
- **Retriggering from the buffered rather than the raw `CS` was the right
  instinct for the design as it stood**, even though the pulls have since made
  the cable side safe and the gating has since made the buffered side a
  liability. The reasoning was sound at the time it was written.
- **The `CLR` pull-down polarity is right and the correction to it is right.**
  Low = cleared = zero scale = safe, and the stated justification for the earlier
  pull-up (a floating push-pull output) genuinely does not hold `[repo]`.
- **Six pulls rather than three is right**, and the argument for it — with `OE`
  disabled the buffer's outputs are Hi-Z, so the pins that actually float are the
  DAC's `[repo]` — is correct and is the kind of thing that is easy to miss.
- **The DAC-side pull values (10 kΩ) are right.** 500 µA of driver fight `[calc]`
  against an 8 mA driver, ~35 mV of V_OH droop, no meaningful AC loading. It is
  the *cable-side* values and rails that are wrong (D9), not these.
- **There is no power-sequencing race at rack power-on.** Bus +5 V and ±12 V
  come up together; the LM317 settles in milliseconds; the instrument cannot
  assert presence until the LT1641's ~50 ms ramp has run and the far-end buck has
  started `[repo]`. So AVDD is always in regulation before `OE` can ever assert,
  and the "buffer drives 5 V into a DAC whose AVDD is still ramping" hazard does
  not exist. The design gets this right by accident of the load switch, but it
  gets it right.
- **The fail-safe direction of `R-OE-PU` is right**: comparator dead or
  unpowered → `OE` pulled high → `OE` is active-low → buffer disabled → failure
  defaults to "instrument absent" `[repo: row 101]`. Correct, and correct in the
  useful direction.
- **The 74HC123 trigger levels from an AHCT output on a different rail close**
  at every corner `[calc, D16 stage 3]` — the only HC-threshold interface in the
  chain, and it is fine.
- **The statelessness rule in `firmware/README.md` is the right response to a
  write-only link**, and the channel-7 analysis that produced it (`CLR` zeroes
  the shared offset, firmware rewrites only the five it thinks of as signals,
  every mod jack pins at +11.45 V `[repo]`) is a genuinely good piece of
  reasoning that I could not fault. Its register list is incomplete (D6) but its
  principle is correct and its arithmetic checks.
- **`MOSI` at 2 MHz over 2 m works**, monotonically, crossing V_IH on the second
  bounce at ~30 ns of a 250 ns half-period `[calc, D14]` — over-damped and slow,
  but safe. The problem is `SCLK`, which was never considered.
- **The repository corrects itself faster than it is reviewed.** Three of my
  findings (D11, D22, most of D23) were fixed by other edits *while this review
  was being written*, each with the right reasoning attached. I have left them
  in, marked, rather than deleting them: a finding that was live when the
  review started and is fixed by the time it lands is evidence the process is
  working, and silently dropping it loses that.
- **The page's honesty about its own defects is real.** It flags that the
  presence detect it inherited stopped working, flags the retrigger question,
  flags the missing POR and flags the NVS-stall risk `[repo]`. Three of those
  four are correctly identified; the fourth is posed against the wrong numbers
  (D12). That is a better hit rate than most pages get, and the finding that the
  `REF` trimmer broke the detect is exactly the kind of cross-page consequence
  this review process exists to catch.

---

## Datasheet questions this review could not close

Every one of these is load-bearing for a conclusion above. The proxy blocked all
vendor domains; none of these figures should be taken from this document.

| Part | Parameter | Decides |
|---|---|---|
| **LM311** | I_B typ/max **and sign**; V_OS max | D4 (whether unplugged reads present), D1 (threshold margin) |
| **LM311** | Input common-mode range referenced to V+; input voltage absolute maximum; phase-inversion behaviour outside CMR | D26 (whether a designed-safe +12 V fault inverts `OE`) |
| **74HC123** | C_ext discharge transistor R_on; whether discharge is held for the trigger pulse or a fixed window; minimum retrigger period | D12 (whether the watchdog false-fires during normal traffic) |
| **74HC123** | R_ext min/max; R_ext/C_ext pin leakage; dual-package unused-half tie-off; power-up output behaviour | D13, D17 |
| **74HC123 (exact PN)** | The timing coefficient K in t = K·R·C | D13 (a substitution can move the timeout 2×) |
| **DAC8568 (SBAS430)** | Clear-code register options — is there an *ignore-`CLR`* code? | **D6a — whether one bad frame can silently disable the watchdog** |
| **DAC8568** | Power-down register: modes, default, and whether a data write clears it | D6b |
| **DAC8568** | Behaviour when `SYNC` rises before 32 clocks; `SYNC`-falling shift-counter reset | D7 |
| **DAC8568** | Does `CLR` latch the clear code into the DAC registers, or force outputs while low? | **D20 — silence or a 3 Hz stutter** |
| **DAC8568** | TSSOP-16 pinout: confirm `LDAC` exists and `DVDD` does not; `LDAC` register default | D8, D23 |
| **DAC8568** | Digital input absolute maximum relative to AVDD | D16 |
| **SN74AHCT125** | V_I absolute maximum and whether it is referenced to V_CC | D11, D14 |
| **SN74AHCT125** | ΔICC per input at V_I = 3.3 V, V_CC = 5 V | D24 |
| **ESP32-S3** | Internal pull-up resistance range (not just typ); GPIO state through ROM boot | **D15 — whether `SCLK` is a valid low during boot** |
| **MPXV4006DP** | Output floor for negative differential pressure; output behaviour through supply ramp | D1 |
