# R9 — Fail-safe and supervision on CV outputs: what published designs actually do

**Date:** 2026-09-21
**Scope:** ADR 0004 §"The module's normal 'off' state has the SPI bus floating",
§"Presence detect is a comparator on the breath line", §"A stuck CV is worse than a
dead one", §"The watchdog's scope is the DAC channels"; BOM rows `U-WATCHDOG`,
`R-WDT`, `C-WDT`, `R-CLR-PU`, `U-PRESENCE`, `R-PRESENCE`, `R-OE-PU`, `U-LVL-MOD`,
`R-SPI-PULL`.

## Evidence markers, and what this session could and could not reach

| Marker | Means |
|---|---|
| `[schematic]` | A schematic or netlist file **opened in this session**. The file is named every time. |
| `[source]` | A firmware source file **opened in this session**. Named every time. |
| `[docs]` | A repository README or Woody's own documents, opened this session. |
| `[datasheet]` | **Nothing in this report carries this marker.** See below. |
| `[memory]` | Asserted from prior knowledge, **not verified this session**. Treat as a hypothesis to check. |
| `[snippet]` | A search-engine summary of a page that could not be opened. Second-hand. Weakest class here. |

**Network reality, stated plainly.** Of the sources the brief named, only GitHub was
reachable. `doepfer.de`, `modwiggler.com`, `ti.com`, `e2e.ti.com`, `analog.com`,
`nxp.com`, `intellijel.com`, `expert-sleepers.co.uk`, `neutrik.com`, `mouser.com`
and `en.wikipedia.org` were all refused at the egress proxy (`connect_rejected`,
403 to CONNECT) for both `curl` and WebFetch. **So there are no datasheet citations
in this document and no ModWiggler thread citations.** Every load-bearing claim below
is either a schematic/netlist I opened on GitHub, or is marked `[memory]`/`[snippet]`
and flagged as needing checking. Where the brief asked for Doepfer PDFs and TI/Maxim
app notes, the honest answer is: blocked, not found, not guessed.

What that leaves is actually the stronger evidence anyway — **production schematics**,
not forum opinion. Nine shipping Expert Sleepers modules, two open 16-bit CV modules
built on the DAC8565/DAC8568 (Woody's own part family), and the whole Mutable
Instruments firmware tree.

---

## Findings vs Woody

| # | What published designs do | Woody | Verdict |
|---|---|---|---|
| 1 | **No surveyed Eurorack module has a hardware watchdog on its CV outputs.** Performer ties DAC8568 `CLR` permanently inactive `[schematic]`; O_C drives DAC8565 `RST` from an MCU GPIO `[schematic]`. The universal answer is the **processor's own watchdog** — MI enables the STM32 IWDG in Tides2, Stages, Marbles, Plaits and the AVR WDT in Grids and Branches `[source]`. | Module-end retriggerable monostable on `CLR`. | **Woody is right to differ.** Everyone else's answer requires the processor to be on the same board. Woody's is 2 m away behind a write-only link, so IWDG cannot park the outputs — only reboot a processor that is not driving them any more. Woody's mechanism is the *only* one available to it. |
| 2 | **Power-on transient is a full-scale positive CV on every channel, for as long as the firmware takes to boot.** Both surveyed DAC modules use **inverting** output stages, so DAC zero-scale (the power-on-reset state) is *maximum positive output*: Performer's own schematic note says input `[0 V, 3.3 V]` → output `[5.17 V, −5.25 V]`, so 0 V in = **+5.17 V out on all eight jacks** `[schematic]`; O_C's inverting stage (24k9 in, 100k feedback, `V_bias` = 1.25 V) gives **≈ +6.3 V out on all four** `[schematic]`. Neither fits any mute, soft-start or relay. | Non-inverting, `Vout = 2·Vdac − 2.500` for pitch (0 → **−2.500 V**, subsonic) and mod offset supplied by **DAC channel 7 itself**, so a `CLR` zeroes signal *and* offset together → **0 V** `[docs: hardware/module/pitch-stage.md, mod-channels.md]`. | **Woody is materially better and should say so.** The ch-7-as-offset trick is the non-obvious part: it is what makes "zero scale" and "safe" the same state. In the two published designs they are opposites. |
| 3 | **Series resistance between DAC and op-amp input is 24 kΩ–25 kΩ in both surveyed designs** — not as protection, but because an *inverting* stage's gain resistor sits there for free (Performer R44/R25/… = 24 k `[schematic]`; O_C = 24k9 `[schematic]`). Both derive their low rail from +12 V (Performer: LM1117-3.3 off +12 V; O_C: LM1117-5 → ADP150-3.3 off +12 V) so the digital rail can never precede the analog one `[schematic]`. | 1 kΩ on every op-amp input the DAC drives `[docs]`, DAC AVDD from an LM317 off the module's own +12 V. | **Adequate but the thinnest margin in the survey.** 1 kΩ from a 5 V rail is 5 mA into an input clamp diode; the usual absolute-max clamp current for a precision op-amp is around 10 mA `[memory — datasheet blocked]`. 2× margin vs 24×–37× in the published designs. Woody's rail ordering is as safe as theirs (AVDD is derived from +12 V and cannot lead it). **The real sequencing exposure is elsewhere — see §3 below.** |
| 4 | **Presence detect is done by protocol, at boot only, with no dedicated pin.** MI Stages discovers its neighbours by exchanging FourCC magic words (`'disc'`, `'over'`) over a serial link during a fixed 2 s window, then stops; a module that is plugged in later is never seen `[source: stages/chain_state.cc]`. No resistor ID, no pull-up, no ident pin in anything surveyed. | A comparator watching the breath receiver's resting DC level — continuous, not boot-only, and reports six things at once. | **Woody's idea is sound and rarer than it looks.** "Detect presence by observing a signal you already have" is the right move when you have no return path. Continuous beats Stages' boot-only. **But the implementation has a hard flaw — see §4.** |
| 5 | **Nobody pulls their SPI lines, because nobody's SPI bus ever floats.** Performer's `DAC_SCK` / `DAC_MOSI` / `DAC_SYNC` nets contain exactly two nodes each — MCU pin and DAC pin `[schematic: sequencer.net]`. Same in O_C `[schematic]`. | 3 × 10 kΩ pulls at the module end `[BOM: R-SPI-PULL]`. | **Correct in principle, and Woody's situation genuinely is different.** But the pulls appear to be on the wrong side of the buffer, or at least on only one side — **see §5.** This is the finding most likely to bite. |
| 6 | **The 74x123 is production hardware, not a cursed part.** Expert Sleepers **Persephone** ships a `74*123` triggered from an LM311, timing `10 kΩ + 1 nF C0G 1 %`, running from a **local L78L05 off +12 V**, with the '123's own `CLR` pins tied hard to +5 V `[schematic: persephone_B_v1.sch]`. Expert Sleepers **Aloysius** ships a `CD4098B` dual retriggerable monostable, timing `4.7 kΩ + 680 nF`, `RES` tied to +12 V `[schematic: aloysius_B_v1.sch]`. | 74HC123 with **1 MΩ + 220 nF X7R** → ~99 ms `[BOM: R-WDT, C-WDT]`. | **Part choice vindicated; the RC is at both extremes of the survey.** 100× the resistance and 220× the capacitance of the shipping example. The specific worry is retrigger discharge — **see §6.** |
| 7 | **Nobody mutes an output.** Zero mute relays, zero soft-start circuits and zero output muting FETs across nine ES production modules, Performer, O_C and the MI tree (grep for `relay`, `mute`, `soft.?start`, `inrush` returns nothing `[schematic + docs]`). CMOS analog switches appear only as **function** switches — ES Otterley's CD4066B waveform selectors, which are followed by 10 kΩ and run off a **resistively divided ±9 V** (3 k / 18 k / 3 k across ±12 V, ~1 mA) `[schematic: otterley_B_v1_2.sch]`; ES Aloysius's DG211 switches shape resistors around a `TLV9354` summing node `[schematic]`. | Declined a series FET on the breath output `[docs: ADR 0004]`. | **Woody's refusal matches practice exactly.** The industry pattern is unambiguous: analog switches go where a feedback network or a following resistor divides their `R_on` away, never in series with a DC-accurate output. |
| 8 | **Output jack series resistors: 470 Ω** on every output across nine ES modules; **220 Ω** in O_C; **220 Ω inside the feedback loop** in Performer (op-amp OUT → 220 Ω → jack node, and the 100 k feedback + 18 pF are taken from the *jack* side) `[schematic: sequencer.net net `CV1`]`. Input jacks: **4.7 kΩ** universally in ES modules `[schematic]`. | 1 kΩ on every CV output `[docs: ADR 0004]`. | **Highest in the survey, and it has a pitch consequence — see §8.** |

---

## Detail

### 1. Does any Eurorack module watchdog its CV outputs? No. And the reason matters.

I could not find one. What I found instead is three distinct postures:

**Posture A — the DAC's clear pin is wired inactive and forgotten.** Westlicht
Performer uses the **DAC8568C**, the same family as Woody's part. Its netlist puts
`U8` pin 9 (`CLR`) and pin 3 (`AVDD`) on the *same net*, `+3.3VA`, and pin 1 (`LDAC`)
on `GND` `[schematic: performer-hardware/sequencer.net]`. So `CLR` is tied
permanently deasserted, `LDAC` permanently asserted, and no GPIO reaches either.
If the STM32 hangs, all eight outputs hold their last value indefinitely and nothing
in the module notices. The schematic contains no watchdog, no supervisor, no reset IC.

**Posture B — the reset pin is wired to the processor, which is exactly the processor
that can hang.** Ornament & Crime rev2e brings DAC8565 pin 13 (`RST`) to a Teensy
GPIO as net `RST_DAC` `[schematic: O_C/hardware/o_c_rev2e_schematic.pdf]`. This is
strictly worse than useless as a hang defence: the one agent that can assert it is
the one that has stopped running. It is there for initialisation, not supervision.

**Posture C — watchdog the processor, not the outputs.** This is Mutable Instruments'
answer and it is consistent across the range. `IWDG_WriteAccessCmd` /
`IWDG_SetPrescaler` / `IWDG_Enable` appear in `tides2/drivers/system.cc`,
`stages/drivers/system.cc`, `marbles/drivers/system.cc` and `plaits/plaits.cc`, with
`IWDG_ReloadCounter()` called from the main loop of each; `grids` and `branches` do
the same with `avrlib/watchdog_timer.h` and `ResetWatchdog()` `[source]`. A hang
therefore reboots the MCU in tens of milliseconds and the firmware re-establishes the
outputs.

**Is a stuck CV a known complaint?** I could not verify this — ModWiggler is blocked.
A search index returned summaries describing users whose digital modules "freeze …
with no output and stop responding to input (both manual and CV), with only a total
power cycle fixing it" `[snippet — modwiggler.com t=226160, page not opened]`. That is
suggestive and no more. **Do not cite it as established.**

**What this means for Woody.** Posture C is the whole industry's answer and it is
unavailable to Woody by construction. An IWDG in the instrument's real-time board
reboots a processor that is no longer driving anything; it cannot park a DAC 2 m away
on the other side of a link with no MISO. ADR 0004's reasoning — "at the module end
where it is independent of the thing that hung" — is not over-engineering. It is the
only remaining option, and the absence of prior art here is an artefact of nobody else
having Woody's topology, not evidence that the problem is imaginary.

One thing the survey *does* argue against: ADR 0004 says "nothing in the design
notices" as if that were unusual. It is not unusual. It is the norm. The section is
right about the fix and slightly overstated about the novelty of the problem.

### 2. Power-on and power-off transients: the accepted state of the art is a full-scale spike

This is the most surprising finding in the survey and it is worth stating bluntly.

Westlicht Performer's own schematic annotation reads:

> `Inverting opamp configuration, Input range [0V,3.3V], Output range [5.17V,-5.25V]`
> `[schematic: performer-hardware/dac.sch, Text Notes at 1800 4300]`

The DAC8568C's power-on-reset state is zero scale `[memory — TI grades A/C clear to
zero scale, B/D to midscale; datasheet blocked]`. Zero scale is 0 V. Through an
inverting stage, 0 V in is **+5.17 V out**. So from the instant the rack's ±12 V
comes up until the STM32 finishes booting and writes its first frame, **all eight CV
outputs of a Performer sit at +5.17 V**.

O_C is the same shape. Its output stage is inverting with `V_bias` from a 47 k/47 k
divider off the 2.5 V reference and a 100 k/24k9 ratio `[schematic]`, giving
`Vout ≈ 1.25 × (1 + 100/24.9) − 4.016 × Vdac ≈ 6.27 − 4.016·Vdac`. At DAC zero scale:
**+6.27 V on all four outputs**, until the Teensy runs.

Neither design fits anything to prevent this. There is no mute FET, no relay, no
soft-start, no output clamp. Across the whole surveyed set — nine Expert Sleepers
production modules, Performer, O_C — a grep for `relay|mute|soft.?start|inrush`
returns **nothing** `[schematic + docs]`.

Power-off is not defended either. Nothing observed sequences the outputs down; the
rails simply collapse and the op-amps follow them.

**So the accepted standard is: a full-scale positive step on every CV output for the
boot time of the processor, and an undefined collapse at power-off.** A click is
accepted, a thump is accepted, and — measurably, in two of the most-copied open CV
designs there are — a several-volt full-scale spike lasting hundreds of milliseconds
is accepted too.

**Where Woody lands.** Woody's pitch stage is `Vout = 2·Vdac − 2.500`
`[docs: hardware/module/pitch-stage.md]` and its mod stage takes its 2.500 V offset
from **DAC channel 7**, so a clear zeroes the offset along with the signal and all
four mod jacks land at exactly 0 V `[docs: hardware/module/mod-channels.md]`. Pitch
lands at −2.500 V — subsonic, which is the intended safe state.

That is genuinely better than the prior art, and the reason is a specific design
choice (non-inverting scaling + offset-from-a-DAC-channel) rather than luck. ADR 0004
should be more confident about this than it currently is, and the mod-channels page
is right that the ch-7 offset is "the whole reason `CLR` works".

**The one gap:** Woody's safe state only exists *if the monostable's Q output is low
at power-up*. See §6.

### 3. Supply sequencing between 5 V digital and ±12 V analog

**What published designs do.** Both DAC modules derive their low rail from +12 V, so
it physically cannot lead the analog rails: Performer runs two LM1117-3.3 and a +5 V
regulator all off +12 V `[schematic: power.sch]`; O_C runs LM1117-5 → 10 µH → ADP150-3.3,
all off VCC (+12 V) `[schematic]`. And both get 24 k–25 kΩ of series resistance between
DAC output and op-amp input for free, because their output stages are inverting.

So the published answer to "is a series resistor on the op-amp input standard?" is:
**nobody thinks about it, because the inverting topology hands them 25 kΩ.** Woody
chose a non-inverting topology for good reasons (pitch-stage.md derives them) and
therefore has to buy that resistance deliberately. That is not over-cautious — it is
paying for something the other designs got as a side effect.

**Is 1 kΩ enough?** 5.21 V through 1 kΩ into an unpowered op-amp input is ~5 mA.
The conventional absolute-max input clamp current for precision op-amps is around
10 mA `[memory — OPA2197 datasheet blocked]`. So 1 kΩ is sufficient with roughly 2×
margin, against 24×–37× in the published designs. For a one-off instrument this is
fine, but it is the thinnest margin in the survey and it is worth knowing that.

**The sequencing hazard Woody actually has is not that one.** It is the
**74AHCT125 on the rack's +5 V bus driving a DAC whose AVDD comes from a local LM317
off +12 V**. These are two independent rails with no defined order. Eurorack PSUs
commonly derive +5 V from +12 V `[memory]`, which would make the order safe, but not
all do, and the module cannot know which is fitted. If bus +5 V leads the LM317's
output, the AHCT125 can drive ~5 V into DAC digital inputs sitting on an AVDD near 0 V.

**Woody is accidentally protected here, and the protection is worth making deliberate.**
`R-OE-PU` pulls the `OE` pins **high** (buffer disabled) whenever the LM393 is not
actively pulling them low `[BOM: R-OE-PU]`. During any window where ±12 V is absent,
the breath receiver is dead, the comparator cannot report "present", and the buffer's
outputs are Hi-Z. So the level shifter cannot inject into an unpowered DAC. That is a
real second-order benefit of the OE gating that ADR 0004 does not claim, and it should
be claimed, because it is a reason not to "simplify" the gating away later.

None of this is standard practice in the survey, because none of the surveyed modules
has a level shifter on a different rail from its DAC. Woody's arrangement is unusual;
its defence happens to already be in place.

### 4. Presence detect — and the one place Woody's version is broken

**Prior art.** MI Stages is the only real expander-presence mechanism I found in an
open design. It has no presence pin. Each module transmits a discovery packet
containing a magic word to its left and right neighbours every 50 ms between t=500 ms
and t=1500 ms, and concludes a neighbour exists when a packet arrives with the
*opposite* magic word (`'disc'` from the left, `'over'` from the right); `index_` and
`size_` are built up from the counters carried in those packets, with an `ouroboros_`
flag for the ring case `[source: stages/chain_state.cc:84–118]`. Discovery is a
one-shot: `discovering_neighbors_ = counter_ < 8000` at a 4 kHz block rate, i.e. it
ends 2 s after boot and never runs again. **Hot-plug is not detected.**

Nothing else in the survey detects anything. Expander connections in Expert Sleepers
modules are plain `TSW-112-02-S-S` inter-board headers with signals and rails and no
ident line `[schematic, all ES modules]`.

So: **the answer to "is it a dedicated pin, a pull-up, a resistor ID?" is "none of
those — it is a protocol handshake, and only at boot."** Woody's approach — infer
presence from the DC level of a signal that is already there — is legitimate, is
continuous rather than boot-only, and is the right instinct for a link with no return
path. ADR 0004's argument that one threshold reports cable, far-end +12 V, REF5050,
sensor, buffer and both analog conductors is correct and is a genuinely elegant piece
of design.

**But the part cannot do the job as specified.** From
`hardware/module/breath-receive-stage.md` `[docs]`, the INA828 output is
`−2.185 × (V_BREATH − V_AGND)`: **−0.44 V at rest and −10 V at full breath**. The
comparator must therefore sit on a node that swings to −10 V and must resolve a
threshold at about −200 mV. The BOM specifies an **LM393** with "open collector to
bus +5 V" `[BOM: U-PRESENCE, R-OE-PU]`.

Three things follow, and they contradict each other:

1. An LM393 powered from +5 V and GND has an input common-mode range that does not
   extend below its own V− pin, and inputs driven more than a few hundred millivolts
   below V− forward-bias substrate diodes `[memory — TI/onsemi LM393 datasheet
   blocked]`. It cannot see −437 mV, let alone −10 V.
2. If instead the LM393 is powered from +5 V and −12 V so that it *can* see those
   levels, then **its open-collector output pulls down to its own V− pin, which is now
   −12 V.** The LM393 has no separate emitter terminal. Driving the 74AHCT125's `OE`
   pins to −12 V destroys them.
3. Generating a −200 mV threshold at all requires a negative reference. `R-PRESENCE`
   is specified as "100k / 10k / 1M" `[BOM]` with no rail named. A divider from +5 V
   and ground cannot produce a negative voltage.

**The prior art has the fix, in the same family of modules, twice.** Expert Sleepers
uses the **LM311** for exactly this: a comparator that spans the analog rails but
drives a ground-referenced logic node.

- Persephone: `IC3[LM311PWR].VCC+` on **+12 V**, `VCC−` on **−12 V**, and
  `EMIT_OUT` tied to **GND**, with `COL_OUT` pulled up by `R5 = 1 kΩ` to a local
  **+5 V**, and `R24 = 1 MΩ` from `COL_OUT` back to `IN+` for hysteresis
  `[schematic: persephone_B_v1.sch]`.
- Aloysius: `IC7`/`IC8` LM311 on ±12 V, both `EMIT_OUT` pins to GND, `COL_OUT`
  pulled up by 10 kΩ, feeding CMOS logic `[schematic: aloysius_B_v1.sch]`.

The LM311's separate collector *and* emitter pins are the entire reason it is chosen
over an LM393 in synth circuits: the comparator core runs on ±12 V and sees the full
analog swing, while the output transistor is referenced wherever you like — here,
ground — so it drives 5 V logic cleanly. That is precisely Woody's requirement.

Note also that Persephone's hysteresis resistor is **1 MΩ from output to `IN+`**,
which is exactly the value and topology `R-PRESENCE` already specifies. Woody's
network is right; the comparator underneath it is not.

### 5. Floating CMOS inputs — Woody pulls the wrong side of the buffer

**Prior art.** There is none worth the name, because no surveyed module has a bus that
idles. In Performer the nets `DAC_SCK`, `DAC_MOSI` and `DAC_SYNC` each contain exactly
two nodes: an STM32 pin and a DAC pin, with no third component of any kind
`[schematic: sequencer.net]`. O_C is identical `[schematic]`. The lines are always
driven because the driver is 20 mm away and always powered.

Woody's situation is genuinely different and ADR 0004's reasoning — "module alive,
DAC alive, SCLK / MOSI / CS floating … is the state the instrument spends most of its
life in" — is correct and is not something the prior art has an opinion about.

**But the mechanism as specified has a hole.** Woody's signal chain is:

```
cable ──> [74AHCT125 inputs] ──> buffer ──> [DAC8568 SCLK/DIN/SYNC]
              ^                    ^
        R-SPI-PULL (×3)      OE gated off when instrument absent
```

When the instrument is absent, `OE` is high and **the buffer's outputs are Hi-Z**. At
that moment the pins that are floating are the **DAC8568's** `SCLK`, `DIN` and `SYNC`
— not the buffer's inputs. `R-SPI-PULL` is specified as three resistors "at the
module", and the BOM's stated rationale is "a stray CS edge latches garbage into the
pitch DAC" `[BOM: R-SPI-PULL]` — which is a statement about the *DAC* side. If the
three resistors are on the cable side of the buffer, they protect nothing during the
state they were bought for; if they are on the DAC side, the buffer's own inputs float
and draw the crowbar current ADR 0004 objects to, inside the precision box.

**You need both.** Six resistors, not three. On the DAC side, `SYNC` pulls to the
DAC's own AVDD (5.21 V) rather than to the bus +5 V, so the pull tracks the rail the
DAC's input thresholds are referenced to.

**A second, related gap: what retriggers the monostable?** Nothing in ADR 0004 or the
BOM says which node `U-WATCHDOG` is triggered from. It matters a great deal. If the
'123 is triggered from the **cable side**, a floating or noisy cable input can
self-retrigger the watchdog indefinitely and the outputs never park — the watchdog is
defeated in exactly the state it exists for. **Trigger it from the buffered, DAC-side
`SYNC`**, downstream of the `OE` gate, so that "instrument absent" propagates to
"watchdog expires" by construction. This is a one-line specification that is currently
missing and is free at schematic time.

### 6. Is the 74HC123 reasonable? Yes — but the RC is at the edge of the survey

**The part is not cursed.** Expert Sleepers ships a `74*123` in Persephone and a
`CD4098B` in Aloysius `[schematic]`. Both are retriggerable CMOS monostables. Both
are in production modules from a maker with a reputation for conservative electronics.
The "74HC123 is noise-sensitive" reputation `[memory]` did not stop either design.

**What differs is the timing network, in both directions and by two orders of
magnitude.**

| Design | R | C | Dielectric | Approx. pulse |
|---|---|---|---|---|
| ES Persephone (`74*123`) `[schematic]` | 10 kΩ | 1 nF | **C0G 1 %** | ~4.5 µs |
| ES Aloysius (`CD4098B`) `[schematic]` | 4.7 kΩ | 680 nF | (unspecified) | ~1.6 ms (0.5·R·C) |
| **Woody (`U-WATCHDOG`)** `[BOM]` | **1 MΩ** | **220 nF** | X7R | **~99 ms** |

Two observations, of unequal weight.

**Minor, and Woody is fine.** The X7R choice is sometimes objected to on tolerance
grounds. It does not matter here. A frame watchdog only has to be comfortably longer
than 250 µs and comfortably shorter than a second; ±30 % of 99 ms is still inside both
bounds by more than an order of magnitude. Persephone needs C0G 1 % because its pulse
*is* the measurement; Woody's is not. **Keep the X7R.**

**Major, and unresolved.** A *retriggerable* monostable must fully discharge `Cext`
on every retrigger. Woody retriggers at the frame rate — one every **250 µs** — with
**220 nF** on the timing node, i.e. roughly 400 retriggers per timeout period. Whether
a 74HC123's internal discharge transistor empties 220 nF within the available window,
and what the effective timeout becomes if it does not, is a datasheet-and-bench
question. **I could not answer it: nexperia.com and ti.com were both refused by the
egress proxy this session.** Persephone's 1 nF discharges trivially; Woody's is 220×
larger. This is the single highest-value thing to check before the module is laid out.

Note the tension, so it is not "fixed" in the wrong direction: reducing C makes the
discharge easier but pushes R above 1 MΩ, and 1 MΩ is already at the top of the
typical `Rext` range for the family `[memory]`, where board leakage and coupling into
a high-impedance node start to matter. Woody's 1 MΩ / 220 nF split is already the
right *direction* for a fast retrigger rate. The question is whether it is far enough.

**On the alternatives the brief listed:**

- **Supervisor IC (TPS3823 etc.) — does not meet the requirement.** The TPS3823's
  watchdog timeout is fixed at approximately 1.6 s `[snippet — ti.com product page,
  not opened]`. That is 16× Woody's 99 ms target and cannot be changed. Supervisor
  ICs are built for "has the firmware died" on a human timescale, not for "has a frame
  arrived" on a musical one. **Rejecting them is correct.**
- **The processor's own watchdog — unavailable.** Already covered: it is 2 m away
  behind a write-only link.
- **RC on a comparator (missing-pulse detector) — genuinely viable and Woody already
  owns the parts.** If `U-PRESENCE` becomes an LM311 (per §4), its package is single.
  But if the comparator stays a dual, the spare half plus a diode, a resistor and a
  capacitor is a missing-pulse detector with a timing node whose impedance you choose
  freely, and it deletes a 16-pin package. Offered as an option, not a demand —
  the monostable is the more conventional answer and has production precedent.
- **A retriggerable timer — this is what Woody has.** Keep it.

**One more thing Persephone does that Woody should copy.** Persephone powers its
`74*123` from a **local L78L05 off +12 V**, not the rack's +5 V bus, and ties the
'123's own `CLR` pins hard to that local +5 V `[schematic]`. Woody's watchdog rail is
not specified anywhere in ADR 0004 or the BOM. It should be the LM317's 5.21 V (the
same rail as the DAC it is protecting), not the bus +5 V — otherwise a rack +5 V
glitch can reset the watchdog and clear the outputs mid-phrase, which is a new failure
mode invented by the defence against an old one.

### 7. Muting analog paths — Woody's refusal is exactly right

The survey is unanimous and worth quoting in aggregate: **not one output mute in the
whole set.** No relays, no series FETs, no muting JFETs on any output, in nine Expert
Sleepers production modules, Performer, O_C, or anything in the MI tree.

Analog switches appear, but only where their `R_on` is divided away:

- **ES Otterley**, two `CD4066B` as LFO waveform selectors. Each switch output goes
  through a **10 kΩ** resistor (`R42`–`R58`) before anything else, and the switches
  run from a **resistively divided ±9 V** — `3 kΩ` from +12 V, `18 kΩ` across, `3 kΩ`
  to −12 V, about 1 mA of bias `[schematic: otterley_B_v1_2.sch]`. Nobody spends a
  zener, let alone a regulator, on the rail of a switch in a signal path they do not
  consider precision.
- **ES Aloysius**, a `DG211BDY` switching envelope shape resistors (`R85` 470 k,
  `R36` 100 k, `R70` 15 k) at the inverting node of a `TLV9354`, and one throw tied to
  `AGND` `[schematic: aloysius_B_v1.sch]`. The switch sits at a virtual ground where
  its `R_on` is in series with a 100 k-class resistor and contributes a fraction of a
  percent.

The rule the prior art follows is: **a CMOS switch goes where a feedback loop or a
following resistor divides its `R_on` by 20× or more. It never goes in series with a
DC-accurate output.**

ADR 0004's reasoning for declining a series FET on breath — "would bring its own
`R_on`, leakage and charge injection to defend against a failure that path cannot
have" — is exactly the industry rule, arrived at independently. **Keep the decision
and keep the paragraph.** The E10 test (pull the umbilical mid-note, watch the jack)
is the right way to close it.

### 8. An incidental finding: the 1 kΩ output resistors interact with pitch calibration

Not strictly fail-safe, but it came out of the same survey and it is quantifiable.

| Design | Output series R | Placement |
|---|---|---|
| Westlicht Performer | 220 Ω | **Inside the feedback loop** — `U4.OUT → R43 → CV1`, with the 100 k feedback and 18 pF taken from the `CV1` node (the jack) `[schematic: sequencer.net]` |
| Ornament & Crime | 220 Ω | Outside the loop `[schematic]` |
| Expert Sleepers (9 modules) | **470 Ω** | Outside the loop, on every output jack `[schematic]` |
| **Woody** | **1 kΩ** | Outside the loop `[docs: ADR 0004]` |

Into a 100 kΩ destination `[memory — the usual Eurorack input impedance]`, a 1 kΩ
output resistor is a −0.99 % gain error, which on a 1 V/oct output is
**−17 cents per octave of scale error**. ES's 470 Ω gives −8.1 cents/oct; O_C's 220 Ω
gives −3.8; Performer's in-loop 220 Ω gives zero.

ADR 0006 calibrates pitch once against a real VCO, which absorbs this completely —
**for that VCO**. What it does not absorb is the *spread* between destinations. Across
plausible destination impedances of 50 kΩ to 1 MΩ:

- with 1 kΩ: −34 to −1.7 cents/oct, a **32 cents/oct spread**;
- with 220 Ω: −7.6 to −0.4 cents/oct, a **7 cents/oct spread**.

Performer's trick — take the feedback from the jack side of the series resistor, with
a small feedback capacitor (18 pF) for stability into cable capacitance — removes it
entirely and is free. Woody's OPA2197 is already a precision part with the loop
bandwidth to do this.

This does not need deciding now, but the pitch channel is the one output where it is
worth a line in the schematic notes rather than a surprise at calibration.

---

## What Woody should change

1. **Replace the LM393 with an LM311 (or equivalent separate-emitter comparator),
   powered from ±12 V with the emitter pin to module analog ground.** `U-PRESENCE` as
   specified cannot work: an LM393 on +5 V/GND cannot see a −437 mV input, and on
   +5 V/−12 V its open-collector output pulls to −12 V and kills the 74AHCT125 `OE`
   pins. Expert Sleepers solves precisely this problem with an LM311 on ±12 V, emitter
   to GND, 1 kΩ collector pull-up to a local +5 V, 1 MΩ hysteresis to `IN+`, in both
   Persephone and Aloysius `[schematic]`. Woody's 1 MΩ hysteresis value is already
   right; only the comparator underneath it is wrong. **This is the one finding that
   is a bug rather than a preference.**

2. **State which rail generates the −200 mV threshold.** It has to come from −12 V.
   `R-PRESENCE` is currently "100k / 10k / 1M" with no rail named `[BOM]`, and no
   divider from +5 V and ground can produce a negative voltage.

3. **Pull the SPI lines on both sides of the 74AHCT125 — six resistors, not three.**
   With `OE` disabled the buffer's outputs are Hi-Z, so the DAC8568's `SCLK`/`DIN`/
   `SYNC` are the pins that float in the state `R-SPI-PULL` exists for. Pull the DAC
   side to the DAC's own AVDD / ground, and keep the cable-side pulls for the
   crowbar-current reason ADR 0004 already gives.

4. **Specify that `U-WATCHDOG` is retriggered from the buffered, DAC-side `SYNC`.**
   If it is retriggered from the cable side, a floating or noisy cable can keep the
   monostable alive forever and the watchdog never fires — defeated in exactly the
   state it exists for. Free to fix now; a bodge wire later.

5. **Give the 74HC123 a power-on reset on its own `CLR` pin, and power it from the
   LM317's 5.21 V, not the bus +5 V.** The power-up state of a 74HC123's `Q` is not
   guaranteed unless its own `CLR` is asserted `[memory]`. A 10 kΩ/100 nF to that pin
   guarantees `Q` starts low, which means the DAC's `CLR` is asserted from the instant
   power arrives and Woody's 0 V / −2.5 V safe state is real rather than probable.
   Persephone ties its '123's `CLR` to a **local** regulated +5 V off +12 V
   `[schematic]`; putting Woody's watchdog on the rack bus +5 V would let a rack glitch
   clear the outputs mid-phrase.

6. **Delete `R-CLR-PU`, or re-justify it.** Its stated reason — "active-low CLR must
   not float while the monostable is being retriggered" `[BOM]` — does not hold if a
   74HC123 `Q` drives it: that output is push-pull and never floats. Worse, the pull
   is to **+5 V**, i.e. it *deasserts* `CLR`, which is the unsafe direction. Compare
   `R-OE-PU`, which is correctly fail-safe and says so. If the pull is kept for a
   reason not written down, write it down; otherwise it is a part whose only effect is
   to weaken the power-up state.

7. **Bench-check the 74HC123's retrigger discharge at 250 µs with 220 nF.** This is
   the one open question the survey could not close. Persephone's shipping 74x123 uses
   1 nF; Woody uses 220 nF and retriggers ~400 times per timeout. Add it to E7 or E11:
   drive real frames, pull the cable, scope `CLR` and confirm the timeout is ~99 ms and
   repeatable. **Do not size anything from the 0.45·R·C figure until it is measured** —
   the datasheets were unreachable this session.

8. **Consider taking the pitch output's feedback from the jack side of its 1 kΩ**, as
   Performer does with its 220 Ω `[schematic]`. Free, removes a 17 cents/octave
   destination-dependent scale error, and needs only the small feedback capacitor
   Performer already fits.

## What Woody should keep

1. **The module-end watchdog itself.** No surveyed module has one, but that is because
   every one of them has its processor on the same board and reaches for the MCU's own
   watchdog instead — MI does exactly this in six modules `[source]`. Woody cannot.
   The absence of prior art is an artefact of Woody's topology, not evidence the
   problem is imaginary. ADR 0004's "at the module end where it is independent of the
   thing that hung" is the correct conclusion.

2. **The 74HC123 as the part.** It ships in Expert Sleepers Persephone `[schematic]`
   and its CMOS cousin the CD4098B ships in Aloysius `[schematic]`. The reputation is
   not a reason to change parts. The RC values are a reason to measure.

3. **The X7R timing capacitor.** A ±30 % timeout error on a 99 ms watchdog is
   irrelevant. Persephone needs C0G because its pulse *is* the measurement; Woody's is
   not. Do not "upgrade" this.

4. **Non-inverting output scaling with the mod offset taken from DAC channel 7.** This
   is the best thing in the design and the survey proves it. The two most-copied open
   CV modules both use inverting stages and therefore both park **every output at
   +5 V to +6 V** from power-on until the firmware boots `[schematic: performer dac.sch
   annotation; O_C rev2e]`. Woody's arrangement makes DAC zero-scale and "safe" the
   same state, on both pitch and the mods, by construction. ADR 0004 understates this.

5. **Declining the series FET on breath.** The rule the prior art follows without
   exception is that CMOS switches go where a feedback network or a following resistor
   divides `R_on` away — ES Otterley follows its CD4066B with 10 kΩ and runs it off a
   resistively divided rail; ES Aloysius puts its DG211 at a virtual ground `[schematic]`.
   Nobody puts a switch in series with a DC-accurate output. ADR 0004 reached the
   industry rule from first principles. Keep the paragraph and keep E10.

6. **Presence detect by watching a signal that already exists.** The only real
   expander-presence mechanism found in open hardware is MI Stages' magic-word
   handshake, which needs a bidirectional link and only runs for the first 2 s after
   boot `[source: stages/chain_state.cc]`. Woody has no return path and gets a
   continuous answer. The *idea* is better than the prior art even though the *part*
   is wrong (see change 1).

7. **The `OE` gating's fail-safe direction.** `R-OE-PU` pulling `OE` high — buffer
   disabled — when the comparator is dead or unpowered is correct, and it does a second
   job ADR 0004 does not claim: it prevents the bus-+5 V-powered level shifter from
   driving an LM317-powered DAC that has not come up yet. Claim it explicitly, so
   nobody removes the gating later as redundant.

8. **Accepting that a stuck breath *sensor* is out of scope.** Nothing in the survey
   defends against a stuck sensor either, and the analysis in ADR 0004 — an analog path
   has no register to hold — is correct.

---

## Sources opened in this session

| Source | What it is |
|---|---|
| `westlicht/performer-hardware` — `dac.sch`, `power.sch`, `jacks.sch`, `sequencer.net`, `sequencer-cache.lib` | Westlicht Performer: DAC8568C, 8 CV outputs, ±12 V. Cloned and parsed. |
| `mxmxmx/O_C` — `hardware/o_c_rev2e_schematic.pdf` | Ornament & Crime rev2e: DAC8565, 4 CV outputs. |
| `expertsleepersltd/hardware` — `analogue/{persephone,aloysius,otterley,ivo,cicely,beatrix,amelia,lorelei,pandora}/*.sch` | Nine Expert Sleepers production modules, Eagle 9 XML, parsed to netlists. |
| `pichenettes/eurorack` — `stages/chain_state.{h,cc}`, `{tides2,stages,marbles}/drivers/system.cc`, `plaits/plaits.cc`, `{grids,branches}/*.cc`, `{marbles,yarns}/drivers/dac.cc`, `*/hardware_design/pcb/*.sch` | Mutable Instruments firmware tree; hardware files are pre-6 Eagle binary and were only mineable for part numbers (DAC8564 in Marbles/Yarns/Tides2). |
| `Befaco/hardware`, `Befaco/VCMC`, `expertsleepersltd/NTX-8CV`, `vk2gpu/eurorack-modules`, `supersynthesis/eurorack` | Checked; contributed nothing beyond the negative result in §7 (no mutes, no relays, no soft-start anywhere). |

**Blocked this session** (egress policy, `connect_rejected` / 403 to CONNECT, for both
`curl` and WebFetch): `doepfer.de`, `modwiggler.com`, `ti.com`, `e2e.ti.com`,
`analog.com`, `nxp.com`, `intellijel.com`, `expert-sleepers.co.uk`, `neutrik.com`,
`mouser.com`, `en.wikipedia.org`, `hackaday.com`, `northcoastsynthesis.com`,
`blacknoisemodular.com`. No Doepfer schematic, no ModWiggler thread and **no datasheet
of any kind** was read. Every `[memory]` and `[snippet]` claim above is a hypothesis,
not a result.
