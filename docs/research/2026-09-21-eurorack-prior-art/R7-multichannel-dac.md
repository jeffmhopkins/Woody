# R7 — Multi-channel DAC practice in synthesiser designs

**Topic:** what open synth and Eurorack designs actually do with multi-channel CV
DACs, and where Woody agrees, differs, or has not yet met the failure mode that
produced the practice.

## Evidence rules used here

Every claim carries one of:

- `[source: <file>]` — code I opened this session, in a repository I cloned.
- `[schematic: <file>]` — a schematic or netlist I opened and parsed this session.
- `[websearch]` — a search-engine summary of a document I could **not** open.
- `[inference]` — my reasoning from the above, not a quoted fact.
- `[from memory]` — unverified recollection. Treat as a prompt to check.
- `[docs: <file>]` — Woody's own repository.

**What I could not reach.** The egress proxy blocks `ti.com`, `analog.com`,
`e2e.ti.com`, `mouser.com`, `digikey.com`, `octopart.com`, `bdtic.com`,
`alldatasheet.com`, `doepfer.de`, `modwiggler.com`, `web.archive.org` and
`en.wikipedia.org` (verified by `curl` and by `WebFetch` returning
`EGRESS_BLOCKED`). **I therefore did not open a single DAC datasheet.** Every
datasheet-level statement below is marked `[websearch]` and should be checked
against the real SBAS430 before anything is ordered. GitHub is reachable by
`git clone` and `raw.githubusercontent.com`.

Repositories opened this session: `pichenettes/eurorack` (Yarns, Marbles,
Stages, Tides 2), Mutable Instruments hardware schematics (Eagle `.sch`, twelve
modules), `mxmxmx/O_C` (hardware PDF + firmware), `westlicht/performer` and
`westlicht/performer-hardware`, `pichenettes/cvpal`, `Befaco/midithing`,
`Befaco/VCMC`, `wntrblm/Castor_and_Pollux`.

I found **no** open hardware or firmware for Expert Sleepers or ADDAC CV modules
this session; GitHub code search for `org:expertsleepers` returned nothing. I am
not asserting they are closed, only that I could not open anything.

---

## Findings vs Woody

| # | Finding from real designs | Woody | Verdict |
|---|---|---|---|
| 1 | DAC8568 grade selects **reference gain** as well as reset state: A/B = gain 1 (2.5 V FS), C/D = gain 2 (5 V FS) `[websearch]`, corroborated by Per\|Former shifting data one bit for an A part `[source]` | BOM says "DAC8568C (**or A grade**)"; ADR 0006 presents the grade as a reset-state choice only | **Wrong, and load-bearing.** An A part halves full scale and breaks pitch span, mod span and the 2.5 V offset channel. C only |
| 2 | The quad siblings expose reset state and reference enable as **pins** (`RSTSEL`, `ENABLE`); the octal parts do not `[schematic: O_C]`, `[source: stages]` | Woody treats both as its own discoveries | Right conclusion; the hazards are a known consequence of going octal, not exotic |
| 3 | Boot sequence in the one other DAC8568 design: software **reset** → clear-code → internal-ref enable → power-up-all `[source: performer Dac.cpp]` | Enable reference only; rely on POR for the rest | **Add the software reset.** Woody's normal state is "module powered, instrument rebooting" — POR never happens there |
| 4 | Nobody in the corpus uses `CLR`. Per\|Former ties `/CLR` high **and** writes the clear-code register to `ClearIgnore` `[schematic + source]` | `CLR` is the watchdog action | Novel. Defensible for Woody's topology, but unexercised — see the ESP32 flash-stall hazard below |
| 5 | Hardware `LDAC` is tied inactive everywhere: O_C `[schematic]`, Befaco MIDI Thing `[source]`, Per\|Former `[schematic]` | No hardware `LDAC`; reviewer's proposal declined | **Matches practice exactly.** Keep |
| 6 | Synchronous update, where wanted, is done in software: write input registers, then `update-all` on the last channel `[source: performer]`; or one atomic multi-channel bus write `[source: Castor & Pollux]` | Not mentioned | Free for Woody, because all six channels are written every pass anyway. Record it as the escape hatch |
| 7 | Internal reference is normal for the DAC; external precision references (LM4040) appear for the **output-stage offset** `[schematic: 8 MI modules, O_C, Per\|Former]` | Internal reference for the DAC; offset from a DAC channel | Reference choice matches practice. Offset-from-DAC is unique to Woody |
| 8 | Everyone else's bipolar offset is an LM4040 shunt reference `[schematic]` | DAC channel 7 | **Right to differ** — it is the only route that gives 0 V at the jacks on both POR *and* `CLR`. The LM4040 route pins four jacks at −10.05 V on `CLR` |
| 9 | 12-bit is normal for shipping CV, including 1 V/oct: Befaco MIDI Thing (MCP4728), CVpal (MCP492x), Castor & Pollux (MCP4728) `[source]`. Mutable Stages uses an **octal 14-bit** DAC8168 `[schematic]` | 16-bit octal | Fine, but 16 bits is not what makes Woody accurate; Woody's own error table already says so |
| 10 | Per\|Former has a 16-bit part and deliberately uses **15-bit codes** (top bit repurposed as a flag) `[source: Calibration.h]` | Full 16-bit, 0.25–4.75 V window | Confirms the marginal bit is not precious |
| 11 | Multi-point per-octave correction is universal: Yarns **11**, O_C **11 per channel** + autotune, Per\|Former **11 per volt per channel**, CVpal **9**, Befaco MIDI Thing **21 (two per octave)** `[source]` | Planned, "roughly one per octave", cites Yarns as twelve | Practice confirmed. The Yarns number is **eleven** (`kNumOctaves = 11`) |
| 12 | O_C ships an **autotune** that measures a real VCO and fills the table automatically `[source: OC_DAC.cpp]` | Manual two-point + multi-point by hand at E9 | Prior art exists for the exact measurement Woody plans to do by hand |
| 13 | "Refresh everything" has prior art (Per\|Former every tick; Marbles/Tides 2/Stages every sample frame by DMA) — **and so does the opposite**: Yarns is explicitly write-on-change with dirty flags `[source]` | Refresh everything, never write-on-change | Rule is right; **the stated reason is not the operative one** — Yarns has no readback either |
| 14 | Per\|Former runs the DAC8568 at **3.3 V**, no LDO for it, no level shifter, and takes gain ≈4.17 in the op-amp `[schematic]` | LM317 at 5.21 V + 74AHCT125 + bench-selected divider, gain 2 | Both defensible. But the grade and the supply are **the same decision**, and ADR 0004's table treats them as independent |
| 15 | MCP4728 powers up to its **EEPROM** contents; Befaco zeroes all four channels immediately after reset `[source: firmware.ino]` | n/a | Third reset behaviour. Evidence that "what does it do at reset" is a question practitioners routinely ask |
| 16 | No real synth project in this survey uses AD5668, AD5676 or MAX5136 | Considered AD5676 in ADR 0006 | TI's DAC85xx/DAC81xx family dominates; see §1 for why |

---

## 1. Which DACs, and why

What I actually found, by part:

| Project | DAC | Bits | Ch | Evidence |
|---|---|---|---|---|
| Mutable **Yarns** (MIDI→CV) | DAC8564 | 16 | 4 | `[schematic: mi/yarns/.../yarns_v03.sch]` |
| Mutable **Marbles** | DAC8564 | 16 | 4 | `[schematic: marbles_v70.sch]` |
| Mutable **Tides 2** | DAC8564 | 16 | 4 | `[schematic: tides2_v40.sch]` |
| Mutable **Stages** | **DAC8168** | **14** | 8 | `[schematic: stages_v70.sch]`, `[source: stages/drivers/dac.cc]` |
| Mutable **Braids** | DAC8551 | 16 | 1 | `[schematic: braids_v50.sch]` |
| Mutable **Peaks** | DAC8552 | 16 | 2 | `[schematic: peaks_v30.sch]` |
| Mutable **CVpal** (USB→CV) | MCP482x/492x class | 12 | 2 | `[source: cvpal/dac.h]` — command words `0x1000`/`0x9000` are the MCP49xx channel-select/gain/shutdown format `[inference]` |
| **Ornament & Crime** | DAC8565 | 16 | 4 | `[schematic: o_c_rev2e_schematic.pdf]` |
| **PER\|FORMER** (westlicht) | **DAC8568C** | 16 | 8 | `[schematic: performer-hardware/dac.sch + sequencer.net]` |
| **Befaco MIDI Thing** | MCP4728 | 12 | 4 | `[source: firmware/firmware.ino]` |
| **Winterbloom Castor & Pollux** | MCP4728 | 12 | 4 | `[source: firmware/src/drivers/gem_mcp4728.h]` |
| Mutable Plaits / Veils / Frames / Links / Kinks | no external DAC | — | — | `[schematic]` |

Three things drive the choice, and none of them is resolution:

**Channel count per package, at one command set.** The TI DAC7568 / DAC8168 /
DAC8568 are 12/14/16-bit octal parts that share a pinout and command set, and
DAC8164 / DAC8564 / DAC8565 are the 14/16-bit quad equivalents. The Marbles and
Tides 2 Eagle libraries carry **both** `DAC8564` and `DAC8164ICPW` part strings
`[schematic]`, which is what a pin-compatible resolution alternate looks like in
a BOM `[inference]`. Woody inherits this for free: if a DAC8568C is
unobtainable, a DAC8168 drops into the same footprint at 14 bits and the same
32-bit frames — the only firmware change is where the data sits in the word
(Stages left-justifies 16-bit values into a 14-bit part and lets the low bits
fall off the end: `*p++ = channel_selection_bits_[j] | (word >> 12); *p++ = word << 4;`
`[source: stages/drivers/dac.cc]`).

**A 2.5 V, 2 ppm/°C reference on the die** `[websearch]`. Every MI board still
carries an LM4040 — but for the *output stage*, not the DAC. This is why nobody
reaches for a separate REF5025 next to the converter, and Woody's "the internal
reference is sufficient" is the normal answer, not a shortcut.

**Package and price.** All of the above are TSSOP/SOP in the 16-pin class. The
12-bit parts win where the design is a MIDI interface rather than a precision
instrument: the MCP4728 is I²C, quad, has its own EEPROM, and is about a dollar.

**AD5668 / AD5676 / MAX5136 do not appear** in any real synth project I could
find. AD5676 is the interesting near-miss for Woody, because it has **SDO
readback** — you can read a channel's DAC register back over SPI `[websearch]`.
That is the one architectural answer to Woody's §7 problem, and Woody's own
ADR 0006 lists AD5676 as the alternative octal it considered `[docs: ADR 0006]`.
It would not have helped: Woody deleted the return conductor from the cable
(ADR 0004), so readback was foreclosed at the umbilical, not at the converter.
That is a defensible trade — the freed conductor became half of the differential
breath pair — but it should be recorded as *"we gave up readback to buy the
analog breath channel"*, not as *"the part cannot do it"*.

---

## 2. Reset state

**Woody is right that the grade matters, and wrong about what the grade means.**

`[websearch]` of the TI datasheet returns two facts, from two separate searches:

- A and C grades power on to **zero scale**; B and D to **midscale** (B/D carry
  the midscale value in OTP).
- **A/B have a reference gain of 1; C/D have a gain of 2.** The external-VREFIN
  limits differ with it (A/B: ≤ AVDD; C/D: ≤ AVDD/2).

I could not open the datasheet to confirm, but there is strong independent
corroboration in silicon-facing code. PER|FORMER supports both parts on the
same board and carries a per-unit hardware config to say which is fitted:

```c
enum class Type { DAC8568C, DAC8568A };
...
case Type::DAC8568C: _dataShift = 0; break;
case Type::DAC8568A: _dataShift = 1; break;
...
data <<= _dataShift;
```
`[source: performer/src/platform/stm32/drivers/Dac.cpp, Dac.h]`, with
`HardwareConfig::dacType()` stored in flash `[source: src/apps/hwconfig/HardwareConfig.h]`
and a changelog entry "Added a `hwconfig` to support DAC8568A (in addition to
the default DAC8568C)" `[source: CHANGELOG.md]`.

The calibration model stores codes in `0..0x7fff` `[source: model/Calibration.h]`.
So the C part is driven with **half** the code range and the A part with the
**full** range, for the same output voltage. That is a factor of two in volts
per code — i.e. a factor of two in full scale — and it is exactly what a
gain-2 versus gain-1 reference produces `[inference]`.

**Consequence for Woody, which is the single most important finding in this
document.** `hardware/bom.csv` row `U-DAC` says
`DAC8568C (or A grade) - full orderable P/N required`, and its note explains the
grade as a reset-state choice: *"A/C grade resets to ZERO scale - B/D reset to
midscale"* `[docs: hardware/bom.csv]`. ADR 0006 says the same `[docs]`. Both are
half the story. Woody needs **gain 2 and zero-scale reset at once**, and only the
**C** grade has both. If an A-grade part is fitted:

- full scale is 2.500 V, not 5.000 V;
- pitch `2·Vdac − 2.5` over the 0.25–4.75 V window becomes a range of roughly
  −2.0 V to **+2.25 V** instead of −2 … +7 V — four and a half octaves gone,
  and no trimmer reaches it;
- the mods become ±5 V, not ±10 V;
- **DAC channel 7 cannot produce 2.500 V at all** except at its top code, so the
  mod channels' zero sits at the one place the part is least linear.

The BOM's own instruction — "specify the full orderable part number, the grade
letter is the whole decision" — is right, and the parenthesis "(or A grade)"
contradicts it. `DAC8568ICPW` / `DAC8568ICPWR` is the part.

**Does anyone else write about this?** Yes, in the way engineers usually do —
by making it a pin so it is not a purchasing decision. The DAC8565 in Ornament
& Crime has `RSTSEL` (pin 14) and `ENABLE` (pin 15) brought out, and the O_C
schematic ties **`LDAC`, `ENABLE`, `RSTSEL` and `GND` together to ground**
(traced from the vector wires: pin-16 and pin-15 stubs at x≈238 join the
vertical run down to the ground symbol that pin 14 and pin 6 also reach)
`[schematic: O_C/hardware/o_c_rev2e_schematic.pdf]`. `RSTSEL` low = power up at
zero scale `[websearch]`. So O_C gets Woody's property with a track to ground.

The octal parts have no spare pins for this, which is *why* TI moved it into the
grade and the reference enable into a register. **Woody's two "traps" are the
price of the octal package, not oversights peculiar to the DAC8568.** That is
worth saying in ADR 0006, because it reframes them from "gotchas we found" to
"the known cost of the part class we chose, and here is how we pay it".

Other reset behaviours found in the wild: the MCP4728 powers up to whatever is
in its on-chip EEPROM, which is why Befaco writes zeros to all four channels
immediately after reset with the comment *"Reset DAC values to 0 after reset"*
`[source: midithing/firmware/firmware.ino]`. People do get bitten, and the fix
is always the same: write a known state at boot rather than trusting POR.

**Which Per|Former does, and Woody does not.** Its init is:

```c
reset();                        // command 7, RESET_POWER_ON
setClearCode(ClearIgnore);
setInternalRef(true);
writeDac(POWER_DOWN_UP_DAC, 0, 0, 0xff);
```
`[source: performer/src/platform/stm32/drivers/Dac.cpp]`

Woody's firmware plan enables the reference and nothing else. A software reset
costs one 32-bit word and matters more for Woody than for Per|Former, because
**Woody's module stays powered while the instrument is switched off** (ADR 0004:
*"the ordinary powered-down state is: module alive, DAC alive"*) `[docs]`. Every
instrument reboot is a case where the DAC has *not* seen a POR and may be holding
anything — including a `CLR`-cleared state, a garbage word latched by a stray
`CS` edge, or the clear-code register set by a corrupted boot word. POR
reasoning does not cover that path at all.

---

## 3. `CLR` and `LDAC`

### `LDAC`: Woody's decision matches every design I opened

- Per|Former: `/LDAC` (pin 1) → `GND` `[schematic: sequencer.net]`.
- Ornament & Crime: `LDAC` (pin 16) → `GND` `[schematic]`.
- Befaco MIDI Thing: *"LDAC pin must be grounded for normal operation."*
  `[source: midithing/firmware/firmware.ino:170]`.
- `LDAC` appears **nowhere** in the O_C firmware `[source: grep of O_C/software]`.

Declining the reviewer's hardware `LDAC` is the majority practice, not a
shortcut. Keep it.

### Synchronous update: real, and obtained without the pin

Two designs in the corpus do care about updating channels together, and both
get it from the protocol rather than a pin:

```c
void Dac::write() {
    for (int channel = 0; channel < Channels; ++channel) {
        writeDac(channel == 7 ? WRITE_INPUT_REGISTER_UPDATE_ALL
                              : WRITE_INPUT_REGISTER, channel, _values[channel], 0);
    }
}
```
`[source: performer/src/platform/stm32/drivers/Dac.cpp]` — seven input-register
writes, then one write-and-update-all. That is an `LDAC` pulse made of one
command bit.

Castor & Pollux does the same on I²C: `gem_mcp_4728_write_channels()` pushes all
four channels in one transaction `[source: firmware/src/drivers/gem_mcp4728.h,
main.c:589]`.

*(A wrinkle I cannot resolve without the datasheet: Per|Former's `/LDAC` is tied
**low**, which I believe makes writes transparent and would make its update-all
batching a no-op `[from memory]`. Either it is decorative or the LDAC register
overrides the pin. Worth ten minutes with SBAS430 before Woody copies the
pattern — but the pattern itself is sound.)*

**What goes wrong without it, for Woody specifically.** At 2 MHz a 32-bit frame
is 16 µs, so mod 1 and mod 4 are written ~48 µs apart, and pitch (pushed
immediately on note change) can land anywhere in the pass. Against the mod
channels' 1.94 kHz reconstruction filter (τ ≈ 82 µs), 48 µs
of skew is a fraction of one filter time constant and about 0.7° of phase at
40 Hz `[inference from docs: ADR 0006, mod-channels.md]`. That is inaudible for
modulation. It would *not* be inaudible if two mod channels ever carried a
stereo pair or an X/Y vector — and ADR 0006 makes the mods generic on purpose,
so that assignment is legal.

**Recommendation: no hardware `LDAC`, but write the escape hatch down.** Woody
already writes all six channels every pass, so switching the first five to
`write input register` and the last to `write input register and update all`
costs nothing, changes no hardware, and removes the skew entirely. Record it in
`firmware/README.md` as the answer if a patch ever needs it, and the `LDAC`
question is closed permanently rather than re-litigated.

### `CLR`: Woody is alone, and that is mostly fine

No design in this corpus uses `CLR`. Per|Former goes further and **actively
disables it**: `/CLR` (pin 9) is tied to `+3.3VA` `[schematic: sequencer.net]`
*and* the clear-code register is written to `ClearIgnore`
`[source: Dac.cpp, enum ClearCode { ClearZeroScale, ClearMidScale, ClearFullScale, ClearIgnore }]`.
Somebody read the same datasheet and concluded the clear path was a liability
worth belt-and-braces suppression.

That is not an argument against Woody. Per|Former's MCU and DAC share a board, a
reset and a power rail; if the MCU hangs, the module is visibly dead and the
user is standing in front of it. Woody's DAC is two metres away on its own
supply, in a rack, driving a VCO, while the thing that computes its outputs is
in the player's hands. ADR 0004's *"a stuck CV is worse than a dead one"* is a
real problem that these designs do not have `[docs]`. **Woody is right to
differ.** But it is an unexercised path, so:

**Hazard A — the clear-code register is the whole watchdog, and it cannot be
verified.** `CLR` drives the outputs to whatever that register selects, and the
options include **full scale** `[source: performer Dac.cpp enum]`. If a single
corrupted boot word lands there, the watchdog stops being a safety mechanism and
becomes a weapon: mods at `4.02 × (5.0 − 0) ≈ +20 V` clipping to +11.45 V on
four jacks, or pitch parked at the top of its range. Woody's
`firmware/README.md` already lists the clear-code register among the write-once
registers to refresh `[docs]` — good — but note that the refresh happens *after*
the fact, and during a hang nothing refreshes. The register must be right
*before* the hang. Mitigations: write it explicitly at boot (never rely on its
default), re-write it every N passes as planned, and **add an E7 bench step that
asserts `CLR` by hand and measures all six jacks**. Nothing in the test plan
currently exercises the one circuit whose entire job is to fire when everything
else has stopped.

**Hazard B — the ESP32 will stall longer than you think.** ADR 0004 says *"size
N so a busy loop cannot trip it but a hang is caught in well under a second"*,
and the design settled on ~99 ms `[docs]`. The threat is not a busy loop; it is
flash. NVS commits and OTA writes on an ESP32-S3 disable the instruction cache,
and code not in IRAM stops executing on **both** cores for the duration of an
erase. Woody writes NVS from the display board's config round-trip and does OTA
with rollback `[docs: firmware/README.md]`. A configuration save mid-performance
that stalls the DAC loop past 99 ms asserts `CLR`: pitch drops subsonic, four
mod jacks go to 0 V, and the note dies. That is a *worse* user-visible failure
than the drone the watchdog exists to prevent, and it happens on a normal
action. **Measure the worst-case loop stall across an NVS commit and an OTA
write at M-something before fixing the monostable's RC**, and consider putting
the DAC service ISR in IRAM so it survives cache-disabled windows. This is the
concrete thing Woody has not considered.

**Hazard C — `R-CLR-PU` may be doing nothing.** The BOM's stated reason is
*"Active-low CLR must not float while the monostable is being retriggered"*
`[docs: hardware/bom.csv]`. A 74HC123's `Q`/`Q̄` outputs are push-pull CMOS and
never float, including during retrigger `[from memory — I could not open the
74HC123 datasheet]`. If the monostable drives `CLR` directly, the pull-up is
decorative and the justification in the BOM is wrong; if the intent is that
`CLR` must be held inactive before the monostable's own supply is valid, then
the driver needs to be open-drain (or the pull-up needs to be on a gate's
input), and that is a schematic-capture decision. Either resolve it or delete
the part — a resistor with a wrong reason in the BOM is how the next reviewer
loses an afternoon.

**Hazard D — the indefinitely-asserted case.** The module's *normal* state is
"powered, instrument off" `[docs: ADR 0004]`. In that state no SPI arrives and
`CLR` is asserted continuously, possibly for weeks. That should be harmless (it
is a static logic input) but it is worth one line in ADR 0004 saying so
deliberately, and worth confirming that the 74HC123 powers up with its output in
the asserting state rather than glitching through the non-asserting one.

---

## 4. Internal vs external reference, and unverifiable write-once registers

**The DAC's own reference: Woody matches practice.** Every module in the corpus
runs its converter on the internal 2.5 V. The LM4040s that appear on almost
every Mutable board — `LM4040B10` on Marbles, Tides 2, Frames, Braids, Peaks,
Plaits, Veils; `LM4040B25` on Frames, Braids, Peaks, Stages, Veils
`[schematic: 12 MI schematics]` — are for the analog output and input stages,
not for the DAC. Per|Former's is an `LM4040CIM3-10.0` `[schematic: power.sch]`,
used for the output-stage offset (see §8). O_C's LM4040 likewise serves the
output stage, while the DAC8565's own `VREF_OUT` becomes the board's `VREF_2v5`
net `[schematic: o_c_rev2e]`.

**The disabled-by-default trap is real and family-specific.** The DAC8568's
internal reference is disabled at power-up `[websearch]`; the DAC8565's is
enabled by default `[websearch]`. Mutable's own codebase demonstrates the split
perfectly:

- Yarns, Marbles and Tides 2 (DAC8564, quad) **never send a reference-enable
  word** — `grep` for `0x090a`/`0x0900` across the whole of `pichenettes/eurorack`
  matches only Stages `[source]`.
- Stages (DAC8168, octal) sends `0x090A0000` as its very first DMA frame, and
  the word is repeated across every slot of that frame:

```c
if (first_frame_) {
  for (size_t i = 0; i < block_size_; ++i)
    for (size_t j = 0; j < kNumChannels; ++j) {
      *p++ = 0x090a; *p++ = 0x0000; *p++ = 0x0000; *p++ = 0x0000;
    }
  first_frame_ = false;
}
```
`[source: stages/drivers/dac.cc]`

So: **exactly the projects using the octal part carry the enable write.** This
is the cleanest possible confirmation that Woody has identified a real hazard and
that the hazard belongs to the package, not to Woody.

**What people do about registers they cannot verify.** Three patterns, all
present:

1. **Send it from every independent code path that can own the DAC.** Stages
   sends `0x090a` in the application driver *and* again in the firmware-update
   driver `[source: stages/drivers/firmware_update_dac.cc:98]`. Two programs,
   two enables, no assumption that the other one ran.
2. **Send it as part of a fixed known-state sequence after a software reset**,
   so the register's prior contents are irrelevant: Per|Former's
   reset → clear-code → ref-enable → power-up-all `[source]`.
3. **Repeat it.** Stages repeats the word across an entire DMA frame rather than
   sending it once `[source]`. Nobody in the corpus re-sends it *periodically*.

Woody's plan — enable at boot, then refresh the reference-enable and clear-code
registers every few thousand passes `[docs: firmware/README.md]` — is strictly
more conservative than any of these and costs one word per few thousand passes.
**Keep it.** It is the right call precisely because Woody's DAC has a second
master (the watchdog) and outlives the MCU's resets.

**One correction of framing.** ADR 0006 and the task brief both call the
internal-reference enable *"a write-once register"*. It is not: it is an
ordinary writable register, which is how Per|Former's `setInternalRef(bool
enabled)` can turn it on *or* off at any time `[source]`. It is write-once in
Woody's *firmware plan*, and the plan already fixes that by refreshing it.
Saying "write-once" makes the silicon sound like the constraint and invites the
wrong mitigations.

---

## 5. Resolution in practice

The corpus does not support "16-bit is necessary for 1 V/oct". It supports
"16-bit is what you use when it is free, and 12-bit ships".

- **Befaco MIDI Thing** — a commercial Eurorack MIDI-to-CV module — is a quad
  **12-bit** MCP4728 driving 1 V/oct pitch, with codes clamped to `0..4095`
  `[source: firmware/MultiPointConv.ino, firmware.ino]`.
- **Mutable CVpal** is a dual **12-bit** part, codes clamped `0..4095`
  `[source: cvpal/calibration_table.h]`.
- **Mutable Stages** — six CV outputs, quantised pitch among them — is an
  octal **14-bit** DAC8168 `[schematic: stages_v70.sch]`. When Mutable needed
  eight channels in one package, they took the 14-bit member of the same family.
- **Winterbloom Castor & Pollux** is a quad **12-bit** MCP4728 with a 12-bit
  `value : 12` bitfield `[source: gem_mcp4728.h]`.

And where 16 bits *is* available, it is not fully spent:

- **Per|Former** masks calibration codes to `0x7fff` and reuses the top bit as
  a "user defined" flag: `int item(int i) const { return _items[i] & 0x7fff; }`
  `[source: model/Calibration.h]`. Eleven volts of span over 15 bits is about
  320 µV/LSB ≈ **0.38 cents** `[inference]`.
- **Yarns** defaults to `54586 − 5133·i` codes per octave `[source: voice.cc]`
  — 5133 codes/octave, i.e. 195 µV/LSB ≈ **0.23 cents**, and it never uses more
  than about 51 000 of 65 536 codes `[inference]`.

**What the real limit is.** Woody's own pitch-stage table answers this and the
answer is not the converter `[docs: hardware/module/pitch-stage.md]`: trimmer
tempco ~0.4 cents over 10 °C, LT5400 tracking ~0.1, internal reference ~0.5,
DAC INL ±4 LSB ~0.4 — against an LSB of roughly 0.18 cents at 16 bits over the
0.25–4.75 V window `[inference]`. Every static term is larger than the LSB, and
Woody separately found **dynamic** terms of 20+ cents (LED-correlated rail
modulation, the shared Schottky, ground IR drop) that dwarf all of them. A
well-compensated VCO drifts ~0.35 cents/K on its own `[docs: ADR 0006]`.

So the honest statement is: **16 bits buys nothing measurable over 14 for this
instrument; the octal package is what Woody is actually buying, and 16-bit is
what that package happens to offer at the top of the family.** That is the same
trade Mutable made in the other direction for Stages. Nothing to change — but
ADR 0006 should not imply the resolution is doing work that the resistors, the
trimmer and the power tree are actually doing.

---

## 6. INL correction in firmware

**Yes, everyone does it, and it is the single most standardised thing in this
whole survey.**

| Project | Points | Spacing | Per channel? | Evidence |
|---|---|---|---|---|
| Mutable Yarns | **11** | one per octave | per voice | `[source: yarns/voice.h:37, voice.cc:85-103]` |
| Ornament & Crime | `OCTAVES+1` = 11 | one per octave | **yes, per channel** | `[source: OC_DAC.h:54, 104-122]` |
| PER\|FORMER | **11** | one per volt, −5…+5 V | **yes, per channel** | `[source: model/Calibration.h]` |
| Mutable CVpal | **9** | one per octave | per channel | `[source: cvpal/calibration_table.h:23]` |
| Befaco MIDI Thing | **21** | **two per octave** (6 semitones) | per channel | `[source: firmware/MultiPointConv.ino]` |

All five interpolate linearly between adjacent points. Yarns:

```c
int32_t a = calibrated_dac_code_[octave];
int32_t b = calibrated_dac_code_[octave + 1];
return a + ((b - a) * note / kOctave);
```
`[source: yarns/voice.cc]`

O_C's is identical in shape `[source: OC_DAC.h pitch_to_dac]`, as is
Per|Former's `voltsToValue()` `[source: Calibration.h]`, as is Befaco's
`intervalConvert()` `[source: MultiPointConv.ino]`.

**Does it help?** The strongest evidence that it does is that O_C ships an
**autotune**: `OC_autotune.h` / `OC_autotune_presets.h`, with
`update_auto_channel_calibration_data(channel, octave, pitch_data)` and a
per-channel `use_auto_calibration_` flag that swaps the measured table in for
the factory one `[source: OC_DAC.cpp]`. Somebody built a closed loop that plays
each octave into a real oscillator, measures the pitch that came back, and
rewrites the table — per channel, per unit. You do not build that for an effect
you cannot hear.

Befaco's is a *learning* calibration driven by playing: send the note one
semitone above an interval boundary and the point moves up; one below and it
moves down `[source: MultiPointConv.ino Processnote()]`. Twenty-one points,
tuned by ear, on a 12-bit DAC.

**Three things Woody should take from this.**

1. **Eleven, not twelve.** ADR 0006 says *"Mutable's Yarns uses twelve for
   exactly this reason"* `[docs]`. `const uint16_t kNumOctaves = 11;`
   `[source: yarns/voice.h:37]`. Small, but it is a cited number, and the whole
   corpus lands on 11 (= 10 octaves + the endpoint), not 12.
2. **Befaco uses two points per octave**, which is the only evidence in the
   corpus that one-per-octave is sometimes not enough. Woody's table is in NVS
   and the points are floats; make the count a constant, not a magic number.
3. **O_C's autotune is the tool Woody described building by hand.** ADR 0006's
   E9 plan is *"verify tracking against a real VCO by ear and by frequency
   counter"* `[docs]`. Woody has a frequency counter, a 2 m cable, and an
   instrument with a WebSocket telemetry channel already specified
   `[docs: firmware/README.md]`. An automated sweep that writes the eleven
   points is a morning's work and it is the difference between calibrating once
   and calibrating whenever the patch changes — which matters *more* for Woody
   than for O_C, because ADR 0006 already says the calibration is specific to
   the load it was made against and wants a per-load preset `[docs]`.

---

## 7. The write-only link

**Both patterns exist in shipping code, and the interesting thing is that
Woody's stated reason does not pick between them.**

Refresh-everything:

- **Per|Former**: `CvOutput::update()` sets all 8 channels then calls
  `_dac.write()`, which writes all 8, every engine tick, unconditionally
  `[source: src/apps/sequencer/engine/CvOutput.cpp]`.
- **Marbles / Tides 2 / Stages**: every channel, every sample frame, streamed by
  circular DMA. There is no "changed?" test anywhere in the path
  `[source: marbles/drivers/dac.cc, tides2/drivers/dac.cc, stages/drivers/dac.cc]`.

Write-on-change:

- **Yarns**, explicitly, with dirty flags and a round-robin that writes at most
  one channel per interrupt:

```c
inline void set_channel(uint8_t channel, uint16_t value) {
  if (value_[channel] != value) { value_[channel] = value; update_[channel] = true; }
}
inline void Write() {
  if (update_[active_channel_]) { Write(value_[active_channel_]); update_[active_channel_] = false; }
}
```
`[source: yarns/drivers/dac.h]`

- **Befaco MIDI Thing**: purely event-driven, `SendvaltoDAC()` called from note
  handling `[source: firmware/MIDIClass.ino, firmware.ino:274]`.

Yarns has no readback either. So *"with no readback, shared state can only be
made safe by being made stateless"* `[docs: firmware/README.md]` is not the
discriminator — Yarns is a stateful write-on-change design with no readback and
it is fine.

**What actually discriminates is whether anything other than firmware can change
the DAC's state.** In Yarns, Marbles, Stages, O_C and Befaco, the MCU and the
DAC share a board, a supply and a reset; if one is alive, so is the other, and
the DAC's registers can only hold what firmware last put there. Woody has two
other writers:

- **the watchdog**, which can clear every channel at any moment, including the
  offset channel the mods subtract from `[docs: ADR 0004, mod-channels.md]`;
- **the power topology**, where the module stays alive across instrument reboots
  `[docs: ADR 0004]` — so "we wrote it at boot" is a claim about a boot the DAC
  may not have witnessed.

**The rule is right; restate the reason.** Something like: *"the DAC has a second
master — the watchdog — and outlives our resets, so firmware's model of its
contents is never authoritative. Refresh everything every pass, including the
registers."* That is a reason that survives contact with Yarns, and it explains
why Woody needs the rule where Yarns does not.

Is there a better pattern than refresh-everything? Only two, and neither is
available:

- **Readback.** AD5676 has SDO `[websearch]`. Woody deleted the conductor.
- **A CRC or sequence number the far end can check.** Requires a return path.
  Same conductor.

What *is* available and is not in the plan: **one spare DAC channel as a loopback
witness.** Woody has two unpopulated channels `[docs: ADR 0006]`. Driving one
with a known ramp and bringing it back up the... no — there is no spare
conductor for that either. The honest position is that Woody's link is
unverifiable by construction, refresh-everything is the correct response, and
the residual risk is exactly the class of bug the mod-channels page already
documents `[docs: hardware/module/mod-channels.md]`. That page is the best piece
of writing in the repository on this subject; it should be linked from
`firmware/README.md`, not just cited.

---

## 8. One thing nobody else does: the offset from a DAC channel

Worth its own section because it is Woody's sharpest divergence.

Every bipolar CV output stage in the corpus takes its offset from a dedicated
shunt reference:

| Design | Offset reference | Evidence |
|---|---|---|
| PER\|FORMER, 8 channels | one `LM4040CIM3-10.0`, through 33 k / 22 k into eight inverting stages (24 k in, 100 k feedback, 220 Ω out, 18 pF) | `[schematic: power.sch, dac.sch]` |
| Ornament & Crime, 4 channels | LM4040, four 75 k "OFFSET" injections into OPA2172 stages (24k9 in, 100 k feedback, 220 Ω out, 22 pF) | `[schematic: o_c_rev2e]` |
| Marbles, Tides 2, Frames, Braids, Peaks, Veils, Plaits | `LM4040B10` and/or `LM4040B25` | `[schematic]` |

Woody instead buffers DAC channel 7 to 2.500 V and subtracts it in four
difference amps `[docs: mod-channels.md]`.

**Woody is right to differ, and the reason is one that none of these designs had
to face.** With an LM4040 the offset survives `CLR`, so a watchdog clear would
zero the five signal channels and leave the offset standing:
`4.02 × (0 − 2.5) = −10.05 V` on four jacks, indefinitely, with nothing able to
notice. Woody's mod-channels page states this exactly `[docs]`. Since none of
the other designs assert `CLR` at all, none of them ever had to choose, and the
LM4040 was free of consequences for them. For Woody it is not. The DAC-channel
offset is the only route that gives 0 V at the jacks on both power-on *and*
`CLR`, and it is correctly reasoned.

**Two costs that should be written down anyway.**

- The offset now carries the DAC's INL, noise, drift and settling, multiplied by
  4.02 onto four jacks. A 1 LSB error on channel 7 is 4 LSB-equivalents on every
  mod output. ADR 0006 says channels 2–6 *"need only to be linear and
  repeatable"* `[docs]` — but channel 7 is not a mod channel, it is the **zero**
  of four bipolar outputs, and a 50 mV error there is 200 mV at every jack.
  **Give channel 7 a stored calibration constant**, measured at E9 against the
  same meter that does pitch. One float. It is the one non-pitch channel that
  deserves the precision treatment, and ADR 0006's "concentrate precision on
  channel 1" rule currently reads as if it does not.
- It creates the `+11.45 V` trap. Already known, already closed by the
  statelessness rule, already documented in the right place `[docs]`. Nothing to
  do; just do not let that documentation drift.

Per|Former also corroborates Woody's *"do not split it into four buffers"*
argument `[docs: mod-channels.md]`: it feeds **eight** output stages from one
shared reference node, so a residual offset error appears as a common shift
across the set rather than eight channels disagreeing `[schematic]`.

---

## 9. Supply and level-shifting: the fork Woody took the other way

ADR 0004 argues the DAC should run at 5 V because a 3.3 V DAC forces the scaling
stage to a gain of 3.6× instead of 1.8×, doubling everything the stage amplifies
`[docs]`. The cost paid is an LM317LZ at 5.21 V, a 74AHCT125 level shifter, and
a divider resistor that has to be selected on the bench because no nominal value
fits on paper `[docs: ADR 0004, bom.csv U-REG-DAC]`.

**Per|Former took the other branch of the same fork**: DAC8568C on `+3.3VA` (pin
3), SPI straight from the STM32 at 3.3 V with no shifter, and a gain of
100 k / 24 k ≈ 4.17 in the output stage, giving −5.25 … +5.17 V
`[schematic: dac.sch, sequencer.net]`, `[source: Calibration.h defaultItemValue
comment]`. Its board's only regulators are an `LM1117-3.3` and an `R-78E5.0-1.0`
`[schematic: power.sch]`. No LDO dedicated to the DAC, no shifter, no
bench-selected resistor, and the top-code-compression problem that ADR 0004
worries about does not arise because the part is nowhere near its rails.

Both are defensible and Woody's is argued honestly. Two observations:

- **The grade and the supply are the same decision, and ADR 0004's table treats
  them as independent.** Its rows are "3.3 V → 0–2.5 V (ref × 1) → gain 3.6×"
  and "5 V → 0–5 V (ref × 2) → gain 1.8×" `[docs]`. Reference gain is not a
  configuration; it is the grade letter (§2). The table is really comparing an
  **A-grade part at 3.3 V** against a **C-grade part at 5 V**. It should say so,
  because that makes the BOM's "(or A grade)" visibly wrong instead of merely
  incorrect.
- **The unexplored option is A-grade at 3.3 V**: 16 full bits over 2.5 V,
  zero-scale reset, no level shifter, no LM317, no bench-selected divider — at
  the price of gain 3.6 and a 3.3 V rail the module does not currently generate.
  I am **not** recommending the change; ADR 0004's noise argument is sound and
  the LM317 is already specified. But it belongs in the "alternatives
  considered" list, because right now the ADR reads as if 3.3 V costs a bit of
  resolution, and it does not — it costs gain.

---

## What Woody should change

1. **`hardware/bom.csv`, row `U-DAC`: delete "(or A grade)". Specify
   `DAC8568ICPW`/`ICPWR`, C grade only.** A/B are reference gain 1 (2.500 V full
   scale); C/D are gain 2 (5.000 V) `[websearch]`, corroborated by Per|Former's
   one-bit data shift between the two parts `[source]`. An A-grade part gives
   −2 … +2.25 V of pitch, ±5 V mods, and a channel-7 offset that cannot reach
   2.500 V. Amend ADR 0006's grade paragraph the same way — the grade letter
   chooses *two* things, and the ADR names only one.
2. **Add a software reset and an explicit clear-code write to the boot
   sequence**, in Per|Former's order: reset → clear code (zero scale) → internal
   reference enable → power-up all channels `[source: performer Dac.cpp]`.
   Woody's module stays powered across instrument reboots, so POR reasoning does
   not cover the common case.
3. **Measure the worst-case DAC-loop stall before fixing the watchdog's 99 ms.**
   An ESP32-S3 NVS commit or OTA write disables the instruction cache and stalls
   non-IRAM code on both cores. A config save that overruns 99 ms asserts `CLR`
   mid-note. Consider putting the DAC service in IRAM. This is the failure mode
   the watchdog design has not yet met.
4. **Add an E7 step that asserts `CLR` by hand and measures all six jacks.** The
   one circuit whose job is to fire when everything else has stopped is currently
   untested, and its behaviour depends on a register that cannot be read back.
5. **Resolve or delete `R-CLR-PU`.** A 74HC123's outputs are push-pull and do not
   float, so the stated reason does not hold `[from memory — verify]`. Either the
   monostable drives `CLR` through something open-drain, or the resistor goes.
6. **Give DAC channel 7 a stored calibration constant.** Its error is multiplied
   by 4.02 onto four jacks; "linear and repeatable" is the right standard for the
   mods but not for their zero.
7. **Restate the statelessness justification.** Not "no readback" — Yarns has no
   readback and is write-on-change `[source]` — but "the DAC has a second master
   (the watchdog) and outlives our resets". Link `mod-channels.md` from
   `firmware/README.md`.
8. **Record the software update-all escape hatch** (`write input register` ×5,
   then `write input register and update all` on the last) in
   `firmware/README.md`, so the hardware-`LDAC` question is closed rather than
   re-opened whenever a patch needs two mods in lockstep. Free, since all six
   channels are written every pass.
9. **Fix the Yarns citation: eleven points, not twelve** (`kNumOctaves = 11`)
   `[source: yarns/voice.h:37]`, and note that Befaco MIDI Thing uses twenty-one
   — two per octave — in case one per octave proves coarse `[source]`.
10. **Stop calling the internal-reference enable a "write-once register".** It is
    an ordinary writable register `[source: performer `setInternalRef(bool)`]`.
    The constraint is Woody's own plan, and the plan already fixes it.
11. **Consider O_C's autotune** as the model for E9 rather than a manual
    frequency-counter session `[source: OC_DAC.cpp, OC_autotune.h]`. Woody
    already has the telemetry channel and the load-preset requirement that makes
    repeatable automated calibration worth more here than it is for O_C.
12. **Fix ADR 0004's DAC-supply table** to say that its two rows are two
    different *parts*, and add "A-grade at 3.3 V: 16 bits over 2.5 V, no shifter,
    no LDO, gain 3.6" to alternatives considered.

## What Woody should keep

- **An octal part for six channels.** Mutable did the same for Stages
  `[schematic]`, and it buys a pin-compatible 14-bit fallback (DAC8168) if the
  16-bit part is unobtainable `[inference]`.
- **The internal 2.5 V reference for the DAC.** Universal in the corpus; the
  external LM4040s on those boards serve the output stages, not the converter
  `[schematic: 12 MI modules, O_C, Per|Former]`.
- **No hardware `LDAC`.** Tied inactive in every design I opened — O_C, Befaco
  MIDI Thing, Per|Former `[schematic, source]`. The reviewer's proposal was
  correctly declined.
- **Refresh everything, every pass**, including the configuration registers.
  Direct prior art in Per|Former's `CvOutput::update()` `[source]` and in the
  DMA-streamed Mutable modules `[source]`.
- **The 2.5 V offset from a DAC channel**, against universal practice. It is the
  only arrangement that gives 0 V at the jacks on both power-on and `CLR`; every
  LM4040-based stage in the corpus would pin four outputs at −10.05 V on a clear
  — those designs simply never assert one.
- **One shared offset node for all four mod channels**, not four buffers.
  Per|Former shares one reference node across eight output stages for the same
  reason `[schematic]`.
- **The watchdog itself.** Nobody else does it — Per|Former actively suppresses
  `CLR` in both hardware and firmware `[schematic + source]` — but nobody else
  has the MCU two metres away on a separate supply from the DAC it drives. "A
  stuck CV is worse than a dead one" is a real problem that this corpus does not
  have, and Woody is right to solve it. It just has to be tested and its trigger
  margin measured against the ESP32's real flash-stall behaviour.
- **Multi-point per-octave correction in firmware.** Yarns 11, O_C 11 per
  channel, Per|Former 11 per channel, CVpal 9, Befaco 21 — all with linear
  interpolation `[source]`. This is the most standardised practice in the whole
  survey and Woody already plans it.
- **1 kΩ series resistors on every output.** Universal; Per|Former uses 220 Ω
  `[schematic]` and O_C 220 Ω `[schematic]`, so 1 kΩ is the conservative end of
  a real range, and ADR 0006 has already argued the trade properly.
