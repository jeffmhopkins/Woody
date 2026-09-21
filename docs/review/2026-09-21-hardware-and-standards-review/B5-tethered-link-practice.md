# B5 — The tethered link against published practice

**Cold comparative review, 2026-09-21.** Reviewer read only the in-scope repo files
(`docs/decisions/0004-cv-interface-module.md`, `docs/decisions/0003-breath-sensing-path.md`,
`hardware/module/digital-and-supervision.md`, `hardware/controller/carrier.md` §1/§2/§4,
`hardware/bom.csv` rows `CABLE-UMB` and `J-UMBILICAL`) plus outside sources.
No prior review or research document was opened.

Findings are indexed **by signal or by cable**, not by document. Every claim is marked
`[repo]` / `[web] <url>` / `[calc]` / `[from memory]`.

---

## 0. Network failures — URLs that would not load

The agent proxy blocked direct fetches to almost every primary source. Search-engine
retrieval worked; page fetch did not. **These URLs failed and their content below comes
from search-result extracts rather than the page itself:**

`www.expert-sleepers.co.uk`, `expertsleepers.com`, `www.patchmanmusic.com`, `maffez.com`,
`mitxela.com`, `en.wikipedia.org`, `doepfer.de` / `www.doepfer.de`, `tsp.esta.org`,
`pathway.acuitybrands.com`, `www.aviom.com`, `www.neutrik.com`, `www.ti.com`,
`www.analog.com`, `www.microchip.com`, `modulargrid.net`, `modwiggler.com` /
`muffwigglers.com`, `electro-music.com`, `intellijel.com`, `electronics.stackexchange.com`.

**Consequence for this report:** ESTA E1.27-2, TI SLYT441, the Neutrik etherCON datasheet
and the Expert Sleepers manuals are cited from indexed extracts, not from the documents.
The numbers quoted from them should be re-checked against the PDFs before anything is cut.
Where that matters I say so at the finding.

---

## 1. Summary table

| # | Rank | Indexed under | One line |
|---|---|---|---|
| **S-1** | **Showstopper** | **the connector** | The one hazard every published RJ45-for-non-Ethernet standard exists to address — wrong *port*, not wrong *lead* — is the one hazard ADR 0004's connector section never considers. |
| **H-1** | High | `SCLK`, `MOSI`, `CS` | 220 Ω series on a 100 Ω line is 2.5× over-terminated. The first incident wave lands **below** the receiving buffer's V_IH. |
| **H-2** | High | the cable (shield) | A shielded etherCON at both ends puts the cable screen in parallel with `PWR_GND` and routes part of ~400 mA onto the module's *panel*, breaking ADR 0004's own star-ground rule. Nothing in scope says where the shield bonds. |
| **H-3** | High | `SCLK`, `MOSI`, `CS` | 2 m of raw single-ended SPI is outside every published statement of SPI's reach. Nobody ships it. What the field ships instead is specific and cheap. |
| **H-4** | High | the whole cable (hot-plug) | RJ45 has no staggered pins. Published power-and-signal connectors mate ground-first / power-last; Eurorack's own convention is "power down the case first". |
| **M-1** | Medium | `+12V` / `PWR_GND` (3, 6) | The BOM specifies "stranded patch lead" with no AWG. Stranded patch cord is commonly 26 or 28 AWG, not the 24 AWG every derivation in the repo assumes — 2.5× the resistance. |
| **M-2** | Medium | the pin map | The T568B assignment is better-reasoned than most published pinouts, with one real defect: pair (3,6) is the *split* pair, so the power loop physically encloses `MOSI`/`CS` in the untwisted region. |
| **M-3** | Medium | `BREATH` / `AGND` (1, 2) | Sending analog 2 m is entirely normal — the field does it *and* digitises at source, and both camps have direct wind-instrument precedent. This design's receiver is better than either. |
| **L-1** | Low | the cable | Cat5e is the right family. The `CABLE-UMB` row is not a specification — it cannot be ordered unambiguously. |
| **L-2** | Low | the cable | The ~200 pF figure is 1.8× conservative (Cat5e is 56 pF/m), and the lumped-RC model it feeds is the wrong model. |
| **N-1** | Note | the topology | Eurorack has no precedent for this umbilical at all. When a signal leaves the rack, the field changes physical layer entirely. |

---

## 2. THE CONNECTOR — etherCON / RJ45 carrying 12 V and logic

### S-1 — Showstopper. The wrong-port case is unaddressed, and it is the case the standards exist for.

ADR 0004 §*Cable specification* handles **wrong lead** carefully and well: it tabulates
rollover and 10/100 crossover swaps, shows that a rollover puts reverse polarity into the
instrument, and adds `D-REVSHUNT` (SS34) so the module's LT1641-1 latches off `[repo] 0004`,
`[repo] carrier.md §1`. That reasoning is sound and better than most hobby practice.

It never considers **wrong port** — the module's etherCON receiving a patch lead from a live
switch, or the Woody lead being plugged into one. On an 8HP panel in a rack next to other
gear, with a standard Cat5e patch lead, this is the likelier of the two mistakes.

**What published practice does about exactly this:**

- **ANSI E1.27-2 (DMX512 over Cat5)** assigns pin 1 = data common, 2/3 = primary data pair,
  6/7 = optional secondary, **8 = data common, and leaves pins 4 and 5 unconnected on
  purpose** — "the avoidance of pins 4 and 5 helps to prevent equipment damage, if the
  cabling is accidentally plugged into a single-line public switched telephone network phone
  jack", and "connection of DMX equipment to non-DMX equipment such as Ethernet switches or
  telephone equipment may result in serious equipment damage and/or personal injury, as pins
  4 and 5 may carry voltages of up to 48 VDC or greater"
  `[web] https://pathway.acuitybrands.com/-/media/abl/pathway/files/resources/reference-guides/pathway-dmx-wiring-guide.pdf?forceBehavior=open`
  (fetch blocked; extract via search).
- **ANSI E1.11 / ESTA** goes further and restricts the connector itself: RJ45 for DMX "shall
  be limited to connections that are part of a fixed installation and not normally accessible
  except to qualified, authorized users", permitted externally "only on patch and data
  distribution products and only when permanently installed in controlled access areas"
  `[web] https://tsp.esta.org/tsp/documents/docs/ANSI-ESTA_E1-11_2008R2018.pdf` (fetch
  blocked; extract via search). A hand-held instrument tether is the opposite of that.
- **IEEE 802.3af/at PoE** never energises a pair until a detection/classification handshake
  finds a valid 25 kΩ signature, and delivers its DC **common-mode through transformer centre
  taps** so that *no DC ever appears across a winding*
  `[web] https://www.coilcraft.com/en-us/edu/series/magnetics-for-power-over-ethernet/`,
  `[web] https://tutoduino.fr/en/poe-en/`.
- **Aviom A-Net** is the closest commercial analogue — 24 VDC at 0.5 A plus the audio payload
  on one shielded Cat-5e — and it handles the hazard by documentation: "while the Cat-5e
  cables and connectors used on Aviom products look like typical computer Ethernet network
  connections, users should not connect computers, routers, or other home network equipment
  to A-Net devices"
  `[web] https://www.aviom.com/library/Application-Notes/62_A-Net-v.-Ethernet---Networking-Designed-for-Audio.pdf`
  (fetch blocked; extract via search).
- **Passive PoE** is the cautionary case: with no handshake, "the power is just there … and
  can damage things not expecting power to be there", and "never ever plug a passive POE fed
  network cable into a non-passive POE accepting device"
  `[web] https://community.ui.com/questions/Will-Passive-PoE-fry-equipment/d3d85ff6-d9ea-4e80-b8c2-d65611c54a81`,
  `[web] https://blog.intermit.tech/2016/03/review-gigabit-passive-poe-injectors-and-switches.html/`.

**What this design does, against those:**

| Property | 802.3af/at | E1.27-2 DMX | Aviom A-Net | **Woody** |
|---|---|---|---|---|
| DC on the pairs | common-mode via centre taps | none | yes (24 V) | **yes, 12 V, differential pin-to-pin on (3,6)** |
| Applied before handshake | no | n/a | yes | **yes** |
| Pins 4/5 | power (Alt B) | **deliberately empty** | — | **`MOSI` / `CS`, live CMOS logic** |
| Connector accessible to a user | yes, but protected | forbidden outside controlled areas | yes | **yes** |

Two concrete failure paths, both `[calc]`:

1. **Woody lead into an Ethernet switch.** +12 V (pin 3) and `PWR_GND` (pin 6) are the two
   legs of the 3-6 pair, so 12 V lands **differentially across the switch port's 1:1
   isolation-transformer winding**. Winding DCR is of order 0.5–2 Ω `[from memory]` → 6–24 A
   until the LT1641-1 folds back. The module survives (the load switch is the fuse, exactly as
   ADR 0004 intends `[repo] 0004`); the switch port very likely does not. Note this is the
   *inverse* of PoE: PoE's whole transformer discipline exists so that DC never crosses a
   winding, and this design's pin map guarantees it does.
2. **Passive-PoE / telephone-class voltage into the module.** 48 V on pins 4/5 arrives at
   `U-TVS-SPI` (SP0504BAHT-class, 5 V) through the instrument's 220 Ω series resistors
   `[repo] carrier.md §4`. `[calc]` (48 − 5)/220 = 195 mA, **0.98 W dissipated in a SOT-23-6
   TVS array**. It is not a 1 W part `[from memory]` — the array and the 74AHCT125 inputs both
   go. Two pins the standards leave empty are the two pins this design puts logic on.

**What to do.** None of this needs a new connector.
- Move `MOSI`/`CS` off pins 4/5 and leave that pair unconnected, accepting one fewer pair.
  There is spare capacity: `MISO` is already deleted `[repo] 0004`, and `SCLK`/`DIG_GND` +
  one more pair covers three logic lines if `CS` shares the `DIG_GND` pair's ground return.
  This is the single highest-value change available and it costs nothing but a table edit,
  before layout.
- If the pin map is held, add series protection sized for 48 V DC sustained on pins 4/5, not
  for ESD, and say so in the `U-TVS-SPI` row.
- Put the warning where a user will meet it: silkscreen on the 8HP panel. Aviom, Clear-Com
  and ETC all do exactly this and nothing more, because nothing more is available on an RJ45.

*Honest counterweight:* this is ranked Showstopper on **standards conformance and
consequence**, not on probability. Probability is a judgement about the owner's rack. But
the fix is a pin-map edit before layout, and after layout it is a respin — which is why it
is ranked where it is.

### Is there precedent for 12 V on an RJ45 outside PoE? Yes, and it is respectable.

- **Aviom A-Net**: 24 VDC, 0.5 A to personal mixers over the same Cat-5e that carries the
  audio, with shielded cable specified to stay inside CISPR 22 / FCC Part 15 Class B
  `[web] https://www.aviom.com/AviomProducts/Features/Getting-Started.php`,
  `[web] https://www.aviom.com/library/User-Guides/107_MT-X-Expansion-Box-User-Guide.pdf`.
- **Clear-Com HelixNet** carries "four channels of digital quality audio, plus program and
  power for beltpacks, over a single, shielded twisted-pair cable (microphone cable, Cat5 or
  Cat6)"; its analog ancestor put 28–30 V DC on one conductor, duplex audio plus call
  signalling on the other, and used the shield as common
  `[web] https://clearcom.com/DownloadCenter/manuals/HelixNetv4.0/HelixNet_Partyline_User_Guide_399G229A.pdf`,
  `[web] https://www.ampco-flashlight.com/wp-content/uploads/2019/02/clear-com-partyline.pdf`.

So the *category* is fine. What separates those from this one is that both are
**closed proprietary ecosystems with matched endpoints**, and neither puts bare CMOS logic on
a pin. **What PoE does that this does not** is, precisely: detect before energising; deliver
DC common-mode so it never crosses a magnetic; bound the current per conductor by standard;
and define the PD's behaviour on insertion and removal.

**Rated-current sanity, in this design's favour** `[calc]`: etherCON is 1.5 A per contact,
<200 mΩ input-to-output, >1000 mating cycles
`[web] https://www.mouser.com/pdfdocs/NeutriketherCONConnectors1.PDF` (fetched via search
extract; Neutrik site blocked). At the reviewed 410–430 mA `[repo] 0004` a single contact
carries 27–29 % of rating. That is comfortable, and materially better than the M12 X-code
alternative ADR 0004 rejected on the same ground `[repo] 0004`. The ADR's own 80 %-of-rating
arithmetic for M12 is correct.

---

## 3. `SCLK` / `DIG_GND` (7, 8) and `MOSI` / `CS` (4, 5) — the SPI link

### H-1 — High. 220 Ω into a 100 Ω line is over-terminated, and the first incident wave misses V_IH.

The repo already knows the arithmetic it quoted was wrong, and already names 68 Ω as the
transmission-line-right value `[repo] 0004`, `[repo] carrier.md §4`. **This review confirms
that independently and can say how much it matters.**

Inputs, all sourced:
- Cat5e Z₀ = 100 Ω ± 15 %, propagation delay 4.80–5.30 ns/m
  `[web] https://ackspace.nl/w/images/b/b1/Cat5_reference_sheet.pdf`,
  `[web] https://www.farnell.com/datasheets/1311844.pdf`.
- `[calc]` 2 m → one-way 9.6–10.6 ns, **round trip 19.2–21.2 ns**.
- Rule of thumb: treat as a transmission line if rise time < 2 × propagation delay
  `[web] https://www.academyofemc.com/transmission-lines`,
  `[web] https://www.polarinstruments.com/support/cits/Critical_length.pdf`.
  An ESP32-S3 GPIO edge is ~2–5 ns `[from memory]`, against a 20 ns threshold. **This link is
  unambiguously a transmission line.** Nothing in scope treats it as one.
- SN74AHCT125: V_IH(min) = **2.0 V** at V_CC 4.5–5.5 V, and "requires fast input transitions
  to operate correctly. The recommended input transition rise or fall rate is **20 ns/V**"
  `[web] https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf` (fetched via search extract),
  `[web] https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT125.pdf`.

`[calc]` Series-termination ladder at the module-end buffer input (far end effectively open —
CMOS plus 10 kΩ pull `[repo] digital-and-supervision.md`), driver output impedance taken as
~35 Ω `[from memory]`, so R_s(total) ≈ 255 Ω:

| t (ns) | far-end voltage, **R_s ≈ 255 Ω (as drawn)** | far-end voltage, **R_s ≈ 103 Ω (68 Ω resistor)** |
|---|---|---|
| 10 | **1.86 V — below V_IH = 2.0 V** | **3.25 V — done** |
| 31 | 2.67 V | 3.30 V |
| 51 | 3.03 V | 3.30 V |
| 71 | 3.18 V | 3.30 V |

**Result:** as drawn, the first incident wave does not clear the buffer's input threshold. The
DAC-side edge resolves only on the second or third round trip, ~30–50 ns after the driver
switched, and the buffer's input **sits inside its forbidden band (0.8–2.0 V) for roughly
20 ns** — against TI's 20 ns/V recommendation, which allows 24 ns across that 1.2 V band.
It is at the limit, with none of the margin the 220 Ω figure was chosen to buy. At 68 Ω the
edge is a single clean step in one transit.

Why this matters more than a timing budget suggests: the failure is not a late edge at 2 MHz
(250 ns half-period is ample). It is that an input dwelling at its threshold on a part with
**no hysteresis** can emit runt or multiple pulses. The repo already states the consequence —
"a stray edge on `CS` re-frames the 32-bit word … a mis-framed word is a **sticky** failure
that the 4 kHz refresh does not clear" `[repo] digital-and-supervision.md`. The over-termination
is the mechanism most likely to produce that stray edge.

**Adopt both things the repo already has on its own shelf:** 68 Ω on all three lines
`[repo] 0004`, and the 74AHCT14 Schmitt buffer that "two independent reviews already
recommended … for edge cleanup on `SCLK`, `MOSI` and `CS` over 2 m of Cat5"
`[repo] digital-and-supervision.md`. They address different halves of the same defect —
68 Ω fixes the edge; the Schmitt makes the receiver indifferent to whatever is left.

### H-3 — High. Nobody ships 2 m of raw single-ended SPI. What they ship instead.

The published position is unanimous and quantified:

- "SPI is a board level protocol … not designed to be a fieldbus. A practical maximum distance
  without transceivers and other specialized techniques is **12–18 inches**"
  `[web] https://forum.allaboutcircuits.com/threads/reading-a-spi-sensor-over-a-long-distance.47494/`.
- TI's own reference design states the baseline as "**the standard SPI range of only
  0.5 metres**", and that SPI over LVDS "extends the communication range to **at least three
  metres**" `[web] https://www.ti.com/lit/ug/tidued8/tidued8.pdf`,
  `[web] https://www.electronicsforu.com/electronics-projects/reference-design-for-transmitting-spi-signals-via-lvds`.
- TI SLYT441, *Extending the SPI bus for long-distance communication*, is the canonical
  application note; its technique is **clock feedback** — the master runs a second SPI port as
  a slave so returning data is delayed equally with the clock — and it uses RS-422 drivers
  with twisted pair, because "twisted-pair cable conductors are closely electrically coupled so
  external noise induced into both conductors appears as common-mode noise, and differential
  receivers are immune to common-mode signals"
  `[web] https://www.ti.com/lit/an/slyt441/slyt441.pdf` (fetch blocked; extract via search).
- RS-422 for comparison: 4000 ft / ~1200 m, up to 10 Mb/s
  `[web] https://www.come-star.com/blog/rs422-distance-maximum-range-speed-limitations/`.
- The adjacent I²C data is worth citing because it names the mechanism: "capacitance, not
  clock speed, is usually what kills [the] bus", and off-board ribbon adds 25–50 pF per 0.5 m
  `[web] https://hackaday.com/2017/02/08/taking-the-leap-off-board-an-introduction-to-i2c-over-long-wires/`,
  `[web] https://learn.adafruit.com/working-with-i2c-devices/cable-length`.

**So 2 m at 2 MHz is 4× the range TI calls standard and roughly 6× the hobby rule of thumb.**
ADR 0004 says "plain single-ended SPI at a couple of MHz over twisted pair is still
unremarkable" `[repo] 0004`. Measured against published practice, that sentence is wrong:
it is remarkable, and no source found here supports it.

That said — **it is not physically implausible, and the honest reason is worth stating**,
because the ADR's instinct is closer to right than its citation. `[calc]` The round trip is
19–21 ns against a 250 ns half-period at 2 MHz: reflections settle in ~8 % of a bit phase.
The repo's own 220 Ω, wrong though its derivation is, is at least a *source* termination, so
the line is not truly unterminated. What is missing is not speed margin; it is (a) a correct
termination value, (b) a receiver with hysteresis, and (c) any statement anywhere in scope
that the link is a transmission line at all.

**What the field uses instead, in order of how much this project would have to change:**

| Alternative | Cost here | Precedent |
|---|---|---|
| Correct source termination + Schmitt receiver | ~$0.40, already on the repo's shelf | universal |
| Slow the clock | free, but does not close — 0.6 MHz already failed `[repo] 0004` | — |
| RS-422/485 transceiver pair | 2 ICs, 2 pairs; ADR 0004 keeps this as contingency `[repo] 0004` | TI SLYT441 |
| LVDS | 2 ICs; "at least three metres" | TI TIDUED8 |
| A slow async link (UART/MIDI) | re-architecture | **Yamaha WX**: MIDI at 31.25 kbaud, opto-isolated current loop, over the *same* 5-pin mini-DIN that carries ~8.5 V power `[web] https://www.saxontheweb.net/threads/wx-connector-pinout.91326/`, `[web] https://yamahamusicians.com/forum/viewtopic.php?t=9922`, `[web] https://en.wikipedia.org/wiki/Digital_current_loop_interface` |

The last row is the one this project should look hardest at, because it is a *wind controller
to tone module* link, 2 m, power on the same cable, shipping since 1987. MIDI is "a simple
31 kHz serial data stream, optically isolated, with no handshake"
`[web] https://gearspace.com/threads/wiring-midi-to-cat5e.1389018/` — it solves ground offset,
misplug tolerance and hot-plug all at once by being a current loop with no shared reference.
Woody cannot use MIDI directly (six 32-bit DAC words at 4 kHz is 768 kb/s against MIDI's
31.25 kb/s `[calc]`), but the *reason* it survives is the thing this link does not have.

**Failure mode when people get it wrong.** Consistently reported as (a) intermittent bit
errors that track cable routing and length, (b) double-clocking on ringing edges, and (c) for
SPI specifically, loss of frame alignment because `CS` glitched — and (c) is the one this
repo has already identified as *sticky* `[repo] digital-and-supervision.md`. The
digital-and-supervision page's own conclusion — that the six `R-SPI-PULL` resistors and a
tied-enabled `OE` are what every surveyed Eurorack module does — is correct **for modules
whose SPI stays on the board**. It is not evidence about a 2 m link, and the page is right to
say so in its opening paragraph.

### L-2 — Low. Cable capacitance and delay.

`[calc]` Cat5e mutual capacitance is specified at 5.6 nF/100 m = **56 pF/m**
`[web] https://www.farnell.com/datasheets/1311844.pdf`, so 2 m is **112 pF**, not the ~200 pF
the repo uses `[repo] 0004`, `[repo] carrier.md §4`. The repo is conservative by 1.8×, which
is the safe direction — but the lumped-RC corner it feeds is the wrong model for a line whose
round trip exceeds the driver's rise time, so the conservatism does not buy anything real.
Replace the RC corner with the ladder in H-1.

Propagation delay appears nowhere in scope. `[calc]` 9.6–10.6 ns one-way is ~4 % of a half
period at 2 MHz — harmless now, and the number that would decide whether a return path could
ever be added (TI SLYT441's clock-feedback technique exists because that delay stops
mattering only if the clock is delayed with it). One line in E11's acceptance criteria.

---

## 4. `BREATH` / `AGND` (1, 2) — the analog channel

### M-3 — Medium, and mostly favourable. Analog over 2 m is normal; this design's receiver is better than the precedents.

**The field does both, and wind instruments specifically have gone both ways.**

*Analog down the cable, real and shipping:*
- **Yamaha BC1/BC2/BC3 breath controller.** The BC jack is a 3.5 mm TRS with "three pins:
  power, ground, and signal"; the controller returns an **analog voltage**, −0.5 V to −8.5 V
  on the ring against sleeve ground, with the synth supplying −9 V and up to 20 mA
  `[web] https://forum.vintagesynth.com/viewtopic.php?t=54526`,
  `[web] https://www.tecontrol.se/products/usb-midi-breath-controller/breath-controller-facts`.
  This is Woody's exact topology — breath as a DC analog voltage, power on the same cable —
  on every Yamaha synth with a BC input for forty years.
- **Akai EWI1000 / EVI1000 → EWV2000.** "The EWV2000 … interprets the **voltage control**
  information from the instrument"; the controller sends CV over a proprietary multi-conductor
  cable, and the module has no MIDI input at all
  `[web] https://gearspace.com/board/electronic-music-instruments-and-electronic-music-production/696571-akai-ewv2000-compatibility-later-ewi-controllers.html`,
  `[web] https://reverb.com/item/63810951-akai-ewi-1000-and-ewv-2000-1980s`.
- **Eurorack itself.** Every patch cable is single-ended CV, and ADR 0003's explanation of why
  it works — the patch ground carries only µA of signal current, so it is a pure reference —
  is correct and well argued `[repo] 0003`.

*Digitise at source, equally real:*
- **Yamaha WX7/WX11/WX5** digitise in the instrument and send MIDI plus power on one 5-pin
  mini-DIN `[web] https://www.saxontheweb.net/threads/wx-connector-pinout.91326/`.
- Every wind controller since (EWI USB, Aerophone) is USB/MIDI.
- **Industrial** is the strongest "digitise or current-loop it" camp, and it is worth reading
  the reason: the standard answer is not digitising, it is **4–20 mA**, because "the signal
  current, not voltage, carries the information … cable resistance has little effect on signal
  quality", good to ~1000 m
  `[web] https://control.com/technical-articles/why-is-4-20-ma-current-used-for-industrial-analog-controls/`,
  `[web] https://www.sevensensor.com/how-does-cable-length-affect-sensor-signal-protection-methods`.
  Voltage signalling is where "sensitivity loss [may occur] beyond 50–100 metres"
  `[web] https://industrialmonitordirect.com/blogs/knowledgebase/0-10v-vs-4-20ma-analog-signal-comparison-guide`.
  **2 m is two orders of magnitude inside that.** The distance is not the problem and ADR 0003
  is right to say so.

**What the field does about ground offset over that distance** is exactly what ADR 0003 does:
make the reference not-a-power-return, and receive differentially. Pro-audio-over-Cat5
practice states the same rule from the other end — "if your audio signals are not in balanced
format, they do not transport too well over CAT 5 or 6 cables as they tend to pick up noise
and crosstalk very easily … it is best [to] convert them to balanced before sending"
`[web] https://www.epanorama.net/blog/2021/04/17/xlr-over-cat-567/`; with balanced signals,
pair-to-pair crosstalk is "-90 dB at 20 kHz … around -120 dB" at mid frequencies
`[web] https://forum.soundonsound.com/phpbb/viewtopic.php?t=78117&embed=true`.

**Verification of the repo's own numbers** `[calc]`: 24 AWG copper is 0.0842 Ω/m
`[from memory]` → 0.168 Ω for 2 m, matching ADR 0003 exactly; 350 mA × 0.168 Ω = 58.8 mV,
matching the ADR's 58.9 mV row `[repo] 0003`. The derivation is arithmetically sound.

**Where this design is ahead of its own precedents:** the Yamaha BC and the Akai EWI both
return analog against a ground shared with the controller's supply current. Woody does not —
`AGND` carries no power current and terminates at an INA828's IN+ and two 1 MΩ bias resistors
and nothing else `[repo] 0004`, `[repo] 0003`, `[repo] carrier.md §2`. And the choice of a
true in-amp over a difference amp, on the ground that a difference amp's CMRR is set by source
impedance balance rather than by the chip `[repo] 0003`, is correct, non-obvious and the kind
of thing that is usually got wrong. Nothing to change.

**One thing to check that is not in scope:** the repo notes there is no band-limit cap at the
instrument end, deliberately `[repo] carrier.md §2`. Against AES72 practice — where every
audio pair is balanced and terminated at *both* ends
`[web] https://www.aes.org/standards/blog/2019/7/aes72-2019-published`,
`[web] https://quadtwistedpair.com/uncategorized/aes-72-pinouts/` — that is unusual, and it
makes the `BREATH` conductor a 2 m antenna presenting a 1 kΩ source. The repo's justification
(RF rectification must be stopped at the receiver) is correct as far as it goes; it does not
address emission the other way. E11 should scope the `BREATH` conductor for SPI-rate content,
not only check the received signal.

---

## 5. `+12V` / `PWR_GND` (3, 6) — the power pair

### H-2 — High. Nothing in scope says where the cable shield bonds, and a shielded etherCON bonds it by default.

`CABLE-UMB` says "Shielded preferred" `[repo] bom.csv`; ADR 0004 says "Shielded (STP/FTP)
preferred … the shield is free at this price" `[repo] 0004`. `J-UMBILICAL` is a Neutrik
etherCON D-series chassis connector at both ends `[repo] bom.csv`. **Nowhere in any in-scope
file is the shield's termination specified.** I searched all five documents for it.

That is not a documentation gap, it is an electrical decision made by default. etherCON D
chassis parts are metal-shelled and bond the screen to the panel `[from memory]`. At the module
end the panel is rack ground; at the instrument end ADR 0009's backing plate is tied by
`MECH-GNDBOND` to `PWR_GND` `[repo] carrier.md §1`. So the screen becomes a **second
`PWR_GND` conductor in parallel with pin 6**, carrying a share of ~400 mA set by the ratio of
resistances, and delivering it into the module's **panel** rather than into the star point at
the Eurorack power inlet.

That directly contradicts the rule ADR 0004 spends a section establishing: "`PWR_GND` runs from
the etherCON to the star point on its own copper, touching no other return on the way. It is the
dirtiest net on the board and it is the one that must be kept to itself" `[repo] 0004`. A
chassis-bonded screen is precisely another return, joined somewhere other than the star.

Published practice is explicit and points one way: **ground the screen at one end only**,
conventionally the receiving/controller end, "to prevent ground loop currents"
`[web] https://industrialmonitordirect.com/blogs/knowledgebase/4-20ma-analog-sensor-cable-selection-for-remote-io`.
Aviom, by contrast, *requires* shielded Cat-5e — but for radiated-emissions compliance, on a
link whose endpoints it controls
`[web] https://www.aviom.com/library/User-Guides/107_MT-X-Expansion-Box-User-Guide.pdf`.

**Decide it explicitly, in ADR 0004, before layout:** shield bonded at the module end only
(isolate the instrument-end etherCON shell from the backing plate), or bonded at both and
`PWR_GND` sized and routed knowing the screen is in parallel with it. Either is defensible.
Leaving it to whichever etherCON variant gets ordered at E12/M7 `[repo] bom.csv` is not.

### M-1 — Medium. "Stranded patch lead" and "24 AWG" are not the same cable, and every derivation assumes the latter.

`CABLE-UMB` specifies "Cat5e STP patch lead, **STRANDED**, ~2 m" with no conductor gauge
`[repo] bom.csv`. The stranded-not-solid reasoning is correct and well made `[repo] 0004`.
But stranded patch cord is commonly 26 AWG, and the "slim" patch cords sold precisely for
flexibility are 28 AWG — a whole product category with its own standards work
`[web] https://www.flukenetworks.com/blog/cabling-chronicles/skinny-28-awg-patch-cords`,
`[web] https://www.quabbin.com/tech-briefs/design-factors-implementing-commercial-poe-28-awg-and-26-awg-stranded-patch-cable`.
TIA-568.2-D treats 28 AWG as a derated case, limiting it to ~15 m of channel to keep DC loop
resistance inside 25 Ω `[web] https://www.fs.com/blog/the-slimmer-the-better-4-faqs-for-using-slim-patch-cables-8875.html`.

`[calc]`, at the reviewed 410 mA `[repo] 0004`:

| Conductor | Ω/m | 2 m, out + back | Drop on the +12 V loop |
|---|---|---|---|
| 24 AWG (what every repo derivation assumes) | 0.0842 | 0.337 Ω | **0.138 V** |
| 26 AWG (typical stranded patch) | 0.1339 | 0.536 Ω | **0.220 V** |
| 28 AWG ("slim", the flexible one) | 0.2129 | 0.852 Ω | **0.349 V** |

The power drop stays harmless in all three cases against a buck needing >6 V in `[repo] 0004`.
The place it actually shows is the sense pair: `carrier.md §2` costs the `AGND`-carries-supply-
current error at 13 mA × 0.168 Ω × 2.185 = **4.8 mV** `[repo] carrier.md §2`. At 28 AWG the same
calculation gives **12.1 mV** `[calc]` — still nulled by `TRIM-BREATH-ZERO`, still DC-constant,
but 2.5× the number in the document, and the document's conclusion ("survivable either way")
is now resting on a gauge nobody specified.

**Add the gauge to `CABLE-UMB`.** 24 AWG stranded shielded patch is a real, buyable, common
product. Specifying it makes four derivations across two documents true instead of
approximately true, and costs nothing.

### M-2 — Medium. The pin map is well reasoned; its one real defect is the split pair.

The reasoning in ADR 0004 is better than most published pinouts: it identifies that pairs
untwist for ~13 mm inside an RJ45 plug and that pin adjacency there is where crosstalk actually
happens `[repo] 0004`. That is correct, and it is the right level of detail.

Physical order in the plug, `[repo] 0004`:
`1 BREATH · 2 AGND · 3 +12V · 4 MOSI · 5 CS · 6 PWR_GND · 7 SCLK · 8 DIG_GND`

**What holds up.** `BREATH` at pin 1 is adjacent only to its own sense return; `SCLK`, the
fastest edge, is at the far end, three pin positions and a DC conductor away. The claim that
the analog pair never neighbours a sharp edge is true as stated. Compared with AES72/QTP —
which exists only to keep four balanced channels apart and does not mix signal classes at all
`[web] https://quadtwistedpair.com/uncategorized/aes-72-pinouts/` — this is a reasonable
adaptation of the same instinct to a cable that must mix classes.

**What does not.** T568B pair (3,6) is the **split pair**: its two legs are the only pair in
the standard separated by other conductors. So across the ~13 mm untwisted region at each
plug, the +12 V go and return **physically enclose pins 4 and 5**, forming a loop with
`MOSI`/`CS` inside it. That is the opposite of a guard. The current in that loop is not DC:
the repo's own figure for the WS2815 strips is a **200–400 mA square wave at ~2 kHz**
`[repo] 0004`. Two consequences, neither fatal:

- `MOSI`/`CS` sit in a 2 kHz magnetic field for ~26 mm of the run. Logic does not care about
  2 kHz. Fine.
- The +12 V loop is also the worst-coupled loop in the cable *as a radiator*, and the repo has
  already noted the AHCT125 must be driven with fast edges. If shielding turns out to be needed
  for emissions (as it is for Aviom
  `[web] https://www.aviom.com/library/User-Guides/107_MT-X-Expansion-Box-User-Guide.pdf`),
  this is the geometry that will have caused it.

**If the pin map is revised anyway for S-1**, the better arrangement puts the power pair on
(1,2) or (7,8) — a *compact* pair — and keeps pins 4/5 empty, in that order of preference.
This is one edit that would close two findings at once.

---

## 6. THE WHOLE CABLE — hot-plug

### H-4 — High. RJ45 has no mating sequence, and every published power-and-signal connector does.

Published hot-plug practice is specific: "hot swap connectors have staggered pin lengths …
ground pins (which are longer) connecting first", and the three-stage form is "first mate
ground, last mate enable" — ground, then data, then power
`[web] https://www.connectpositronic.com/en/hot-swap-connectors/`,
`[web] https://en.wikipedia.org/wiki/Hot_swapping`. SATA's 15-pin power connector is the
textbook implementation: longest ground pins first, pre-charge pins through current-limiting
resistors second, everything else last, explicitly "to limit inrush current and prevent arcing
during insertion" `[web] https://ask.adaptec.com/app/answers/detail/a_id/17175/~/principles-for-using-hot-swap-with-sas/sata-systems`.
Typical stagger is 0.5 mm → 25–250 ms between first and last contact
`[web] https://www.connectpositronic.com/en/hot-swap-connectors/`.

**8P8C has none of this.** All eight contacts are on one plane, and during insertion each jack
spring wipes across the plug's blades — "the wire contacts of the plug wipe against the free
ends of the contact wires" — so the mating order is set by mechanical tolerance, not by design
`[web] https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9093807`. Live
disconnection of a powered RJ45 is documented as producing arcing that damages the contact
plating `[web] https://www.link-pp.com/knowledge/8p8c-modular-rj45-connectors-guide.html`.

**Eurorack's own answer to the same question is blunter: don't.** The community convention is
"always turn off your case before you plug in (or even move) a module"
`[web] https://noiseengineering.us/blogs/loquelic-literitas-the-blog/how-to-plug-in-a-module/`,
`[web] https://www.perfectcircuit.com/signal/eurorack-modular-power-basics`. 802.3af's answer
is to not energise until after detection.

**What this design has, and what it does not** `[repo] 0004`, `[repo] digital-and-supervision.md`:

| Hot-plug protection | Here |
|---|---|
| Inrush limiting into the instrument's bulk C | **Yes — LT1641-1 + FET. Good, and better than most.** |
| Short-circuit foldback on a half-inserted connector | **Yes — explicitly reasoned for** `[repo] 0004` |
| A panel switch so the normal case is not a hot-plug | **Yes — the module's toggle, the system's only switch** |
| Defined mating order (ground first, power last) | **No. Not available on RJ45.** |
| Defined behaviour on *removal* | **No — acknowledged: "pull the umbilical mid-note and the rack holds that note until you flip the module's toggle"** `[repo] digital-and-supervision.md` |
| `LDAC` tied | **No — acknowledged open; "every exit from `CLR` — hot-plug, watchdog recovery, reboot … throws intermediate values at the mod jacks for 100–200 µs"** `[repo] digital-and-supervision.md` |

The first three are genuinely above the field average and the ADR deserves credit for them.
The last three are the gap, and only one of them is a hardware problem: **`LDAC` should be
tied.** It is a CMOS input left floating on the DAC, the repo already knows it, and it is the
cheapest correction on this list.

On the removal case: I will not re-argue the deleted watchdog, which the repo has reasoned
through at length and reached a defensible conclusion on. But the *field* reading of it is
worth one sentence — a link that can be unplugged live and leaves the downstream device
holding its last value is the one behaviour DMX, MIDI and PoE all design against
(DMX receivers hold-last-look *by explicit standard choice* and everyone complains about it;
MIDI's All-Notes-Off exists for this; PoE's PD powers down). The repo's own proposed fix —
drive `CLR` from the presence comparator through a 74AHCT14 inverter, one part, three jobs
`[repo] digital-and-supervision.md` — is the right shape, and it becomes cheaper still if the
Schmitt inverter is bought anyway for H-1.

---

## 7. THE CABLE — is Cat5 the right choice?

### L-1 — Low. Right family, under-specified row.

**Cat5e is a defensible choice and has good company.** AES72/QTP runs four channels of balanced
analog or eight of AES3 over Cat5/5e/6 `[web] https://quadtwistedpair.com/`; DMX512 runs over it
under ANSI E1.27-2; Aviom and Clear-Com HelixNet run audio *and* DC power over it; the
pro-audio norm for that is "Cat6 FTP or STP … usually with robust EtherCon connectors"
`[web] https://forum.soundonsound.com/phpbb/viewtopic.php?t=78117&embed=true`. Four twisted
pairs at 100 Ω, a 1.5 A/contact connector and a $5 replacement cost is a genuinely good match
to "power + one analog + three logic".

**The etherCON decision is the strongest part of the connector section.** The reasoning —
that the instrument moves constantly while being played, that the flex is at the connector, and
that patch lead is not flex-rated so the right answer is to treat the cable as a consumable and
keep spares `[repo] 0004` — is better thought through than most commercial products manage,
and it is the correct trade for a one-off instrument. The HR10A comparison is honest about what
it gives up.

**But `CABLE-UMB` as written cannot be ordered unambiguously** `[repo] bom.csv`. It is missing:

- **conductor gauge** (M-1 above — and it changes four derivations),
- **whether the shield is mandatory and where it bonds** (H-2 above),
- **straight-through, explicitly** — ADR 0004 identifies this as "a hazard rather than a
  preference" and shows that rollover leads are "visually identical to the right ones"
  `[repo] 0004`, and then the BOM row does not say it,
- **flex rating or bend radius.** For a cable whose "entire life" is flexing, the field answer
  is a tour-grade flexible Cat5e (TMB Dataplex-class SF/UTP and equivalents
  `[web] https://tmb.com/docs/dataplex-cables/Dataplex-CAT5e-A4-web.pdf`), not a data-centre
  patch lead. It costs more and lasts; "consumable" is still the right policy, but the
  consumable should be specified.

**What a comparable instrument maker would use.** Akai and Yamaha both used **proprietary
multi-conductor cables with proprietary connectors** — and it is worth naming why, because it
is the whole of S-1: a proprietary connector *cannot be plugged into the wrong thing*. The
cost is exactly the one ADR 0004 identified and priced: "whether the instrument is out of
action for an afternoon with a crimp tool or for the time it takes to open a drawer"
`[repo] 0004`. Akai EWI owners today pay for that choice — the original cables are
"EXTREMELY HARD TO FIND … everything is PROPRIETARY"
`[web] https://gearspace.com/board/electronic-music-instruments-and-electronic-music-production/696571-akai-ewv2000-compatibility-later-ewi-controllers.html`.
**The repo made the opposite trade with its eyes open, and for a one-off instrument that is
the right call.** It just has to pay the cost of the trade, which is protecting against the
misplug it deliberately made possible.

### N-1 — Note. Eurorack has no precedent for this umbilical, and the way it avoids needing one is instructive.

Every expander convention in the format is **short IDC ribbon, inside the case, between modules
screwed to the same rails**: 10-pin or 16-pin, keyed and shrouded, a few inches long. Expert
Sleepers' ESX-8GT connects to its host "using a 10-way ribbon cable supplied with the ESX-8GT"
`[web] https://www.expert-sleepers.co.uk/esx8gtusermanual.html` (fetch blocked; extract via
search). Intellijel's manuals carry the standard warning that "if the pins are misaligned in
any direction or the ribbon is backwards you can cause damage to your module, power supply, or
other modules", and note that some expansion ports are shrouded specifically "to ensure they
can be connected in only one direction"
`[web] https://intellijel.com/downloads/manuals/atlantix_manual_2024.09.12.pdf`.

**Nothing in the format routes an expander bus out of the case.** When a signal has to leave
the rack, the field changes physical layer entirely:

- **Expert Sleepers ES-3** — ADAT lightpipe over TOSLINK. Optical, galvanically isolated,
  eight channels of CV: "a single optical cable is all that is needed to bring direct CV
  control from your DAW right into the heart of a modular system"
  `[web] https://www.expert-sleepers.co.uk/es3.html` (fetch blocked; extract via search).
- **Expert Sleepers ES-8 / Silent Way** — DC-coupled *audio* over ordinary jacks, so the
  physical layer is one the world already has drivers, cables and connectors for.
- **Tiptop Audio ART** — an encoded digital protocol deliberately shaped to survive "standard
  Eurorack patch cables … fully compatible with passive multiples and stackable patch cables"
  `[web] https://www.perfectcircuit.com/signal/tiptop-art-modules-explained`.
- **BeepBoop Telecom RJ45 / Plum Audio RackPlumber** — the only Eurorack products found that
  use RJ45 between cases, and both carry **patch signals only, no power**
  `[web] https://www.elevatorsound.com/product/beepboop-electronics-rj45-telecom-eurorack-multi-core-cable-module-pair/`,
  `[web] https://www.plum-audio.com/product-page/rackplumber-rj45`.

The pattern is consistent: **raw logic stays in the case; anything that leaves is either
isolated, encoded, or ridden on an existing standard.** `digital-and-supervision.md` opens by
saying "no surveyed Eurorack module has any of it … that is not evidence the problem is
imaginary — it is a consequence of topology" `[repo]`. That is exactly right, and this review
confirms it from outside: the topology has no peer in the format, so the format's conventions
give no cover. The comparisons that *do* apply are Aviom, Clear-Com, DMX-over-Cat5 and the
Yamaha WX — and those are the four this design should be measured against, not against other
Eurorack modules.

---

## 8. The two answers asked for

### The single biggest thing this design does that published practice would not

**It puts a live, user-accessible, industry-standard RJ45 carrying 12 V DC and bare CMOS logic
on a panel, with logic on the two pins every published RJ45-for-non-Ethernet standard
deliberately leaves empty, and with no detection step before power is applied.**

Every body that has faced this problem has answered it, and all three answers are absent here:
ESTA/ANSI restricts the connector to controlled-access fixed installations and leaves pins 4
and 5 unconnected so a misplug into 48 V cannot destroy anything
`[web] https://pathway.acuitybrands.com/-/media/abl/pathway/files/resources/reference-guides/pathway-dmx-wiring-guide.pdf?forceBehavior=open`;
IEEE 802.3af negotiates before energising and delivers DC common-mode so it never crosses a
magnetic `[web] https://www.coilcraft.com/en-us/edu/series/magnetics-for-power-over-ethernet/`;
Aviom and Akai use proprietary protocols or proprietary connectors so the endpoints are always
matched
`[web] https://www.aviom.com/library/Application-Notes/62_A-Net-v.-Ethernet---Networking-Designed-for-Audio.pdf`.

The irony the ADR should feel is its own: it fits two Schottkys on the *rack* connector because
"reversed ribbon cable is the classic Eurorack failure and the keying alone is not worth
trusting" `[repo] 0004` — for a connection made once in the module's life — and then hands the
most-handled interface in the system a connector that mates with every network port in the
building. The correction is a pin-map edit, before layout, and it is cheap.

### The single thing it does better than published practice

**`AGND` — a dedicated sense return that carries no power current, received by a true
instrumentation amplifier.**

The two direct precedents for analog breath down a cable both get this wrong: the Yamaha BC
returns its voltage against a sleeve that is also the supply ground
`[web] https://forum.vintagesynth.com/viewtopic.php?t=54526`, and the Akai EWI cable shares
returns across a proprietary multiway. Eurorack patch cables get away with it only because the
power return is elsewhere — which ADR 0003 identifies precisely, and then *generalises
correctly* instead of copying `[repo] 0003`. The quantification is right (`[calc]` 350 mA ×
0.168 Ω = 58.8 mV of breath-correlated offset avoided, matching the ADR's own table), and the
receiver choice is the non-obvious half: an in-amp rather than a difference amp, because a
difference amp's CMRR is set by *source impedance balance* rather than by the chip, which would
have left ~19–34 dB against the 60 dB the scheme needs `[repo] 0003`.

That is textbook instrumentation practice — the same rule industrial 4–20 mA and AES72 balanced
audio both encode — applied in a place where the entire musical-instrument field, past and
present, does the lazy thing instead. It is the best-reasoned page in the scope and nothing in
published practice argues against it.

---

## 9. Recommended order of action

1. **Before layout — move `MOSI`/`CS` off pins 4 and 5** and leave that pair unconnected, or
   accept and document the 48 V hazard on those pins with protection sized for it. (S-1)
2. **Before layout — decide and write down where the cable shield bonds.** (H-2)
3. **Now — `R-SCLK-SER` / `R-MOSI-SER` / `R-CS-SER` to 68 Ω, and buy the 74AHCT14.** Both are
   already on the repo's own shelf; this review is the outside confirmation. (H-1, H-3)
4. **Now — tie `LDAC`.** Already an open item; it is the cheapest hot-plug fix available. (H-4)
5. **Now — add conductor gauge, mandatory shield and "straight-through" to `CABLE-UMB`.** (M-1, L-1)
6. **At E11 — treat the link as a transmission line.** Scope the far end of `SCLK` and `CS` for
   threshold dwell and runt pulses, not just for eye opening; measure propagation delay; scope
   `BREATH` for SPI-rate content. The acceptance criteria as written do not ask for any of this.
