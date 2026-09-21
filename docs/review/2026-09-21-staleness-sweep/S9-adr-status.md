# S9 — ADR status, superseded notes, and the navigational layer

**Scope.** Do the 14 ADRs still say what the project does, and do the
navigational documents (`README.md`, `ROADMAP.md`, `firmware/README.md`,
`docs/decisions/README.md`, `docs/reference/**`) describe the project that
exists? Schematic pages under `hardware/**` are treated as ground truth, per the
rule the breath page established and `pitch-stage.md`, `mod-channels.md` and
`power-entry.md` all restate.

**Method.** Every ADR read in full. Every double-quoted phrase in the corpus
(226 of them) extracted mechanically and searched, normalised, across the whole
repository; misquotes and phrases that exist nowhere are reported in §4. Every
`` `REFDES` `` token in the corpus checked against `hardware/bom.csv`.

**Nothing was edited.** This file is the only thing written.

---

## Summary of rankings

| Rank | Count | |
|---|---|---|
| **Showstopper** | 3 | S-1 `REF` grounded, S-2 the star point board, S-3 the `DIG_GND` star rule |
| **High** | 11 | |
| **Medium** | 14 | |
| **Low** | 9 | |

---

# 1. ADR status accuracy

## H-1 — The index says 0007 and 0008 are "board open". Both name a selected board.

`docs/decisions/README.md:47-48`

> | [0007](0007-imu-selection.md) | IMU selection | Accepted (board open) |
> | [0008](0008-display-selection.md) | Display selection | Accepted (board open) |

`docs/decisions/0007-imu-selection.md:3`

> **Status:** Accepted. Board selected: Waveshare ESP32-S3-Matrix.

`docs/decisions/0008-display-selection.md:3`

> **Status:** Accepted. Board selected: LilyGO T-Display-S3 AMOLED (base, not Plus).

ADR 0008 closes the question explicitly at `:228-230`: *"**Open** — Nothing
blocking. Confirm the board outline on arrival"*. ADR 0007 `:236-238` settles
the one remaining gate (*"the carrier layout is not blocked on it"*). Both
boards are in `bom.csv` (`U-MCU-RT`, `U-DISP`) and both are named in ROADMAP E1.
**Rank: High** — the index is the first thing a reader consults, and it reports
two settled component choices as open.

## H-2 — The index says 0011 is "Open". ADR 0011 is Accepted, and the licences are in the repo.

`docs/decisions/README.md:51`

> | [0011](0011-licensing.md) | Licensing | Open |

`docs/decisions/0011-licensing.md:3`

> **Status:** Accepted

The decision is fully specified (`0011:15-24`, a four-row table), the three
licence texts exist in `LICENSES/`, and `README.md:83-91` describes the outcome
as settled. The index's own definition of `Open` — *"Options identified,
decision not made. Usually blocking something"* (`README.md:23`) — does not
describe this ADR. **Rank: High.**

## M-1 — ADR 0001's index row is right; its own note is subtly narrower.

`docs/decisions/README.md:41` reads *"Accepted (partitioning revised by 0013)"*,
and `0001:3-6` agrees. No defect. Recorded because it is the one index row that
does match, and it is the model the other three should follow. **Rank: Low
(informational).**

## M-2 — No ADR is marked `Superseded`, yet the index defines the value and the format section promises it.

`docs/decisions/README.md:32-35`

> When a decision is reversed, do not edit the old ADR. Mark it `Superseded` and
> write a new one that says what changed. ADR 0005 is an example: the battery
> architecture was real work that got deleted by a better idea, and the record of
> why it was deleted is worth keeping.

ADR 0005's status is `Accepted` (`0005:3`); the battery material lives inside it
under a `## Superseded approach: onboard battery` heading (`0005:10`), not as a
superseded ADR. The stated convention has never been used and the example given
does not work the way the text says. **Rank: Medium** — the process rule and the
practice disagree, which is what lets reversed decisions sit unmarked (§2).

---

# 2. Superseded-note accuracy, and reversed decisions with no note at all

## VERIFIED FIXED — ADR 0001's "no satellite boards" note

`docs/decisions/0001-mcu-and-board-partitioning.md:68-75` now reads correctly:

> **The second half stands.** It was reversed for a while — an intermediate
> version of this ADR moved all four shift registers to the carrier and said
> there were "no satellite boards" — and *"One register per cluster"* below
> reversed it back. The cluster boards are the satellite boards.

Mechanically checked: the phrase `no satellite boards` appears in the repository
**only** at `0001:72`, inside the note that disowns it. The note is accurate.

## H-3 — Curve shaping on the analog breath output is declared "genuinely lost" in two ADRs. A panel control now does it.

`docs/decisions/0003-breath-sensing-path.md:555-557`

> **Curve shaping on the breath output.** Genuinely lost — `breath_gamma` cannot
> apply to a signal firmware never touches.

`docs/decisions/0006-cv-channel-allocation.md:277-278`

> Firmware still shapes the response curve upstream of the DAC. The knobs fit the
> *range* to the patch; the firmware shapes the *feel*.

`hardware/module/breath-output-stage.md` §4 and its component table:

> **CCW (wiper toward `V_shaped`)** → extra *feedback* current at high breath
> → gain falls with pressure → **compressive, "logarithmic"**.
> …
> | Panel | **A third pot and a third knob** |

`hardware/bom.csv:80`

> POT-RESP,module,"50k linear,…Breath response: log (CCW) - linear (centre) - exponential (CW)"

A reversed decision with **no superseded note anywhere**. ADR 0003 and ADR 0006
both still state that response shaping cannot reach the breath jack; the module
now contains a dedicated analog shaper in that exact path. ADR 0006's sentence
is also wrong twice over — breath never passes through the DAC, so "upstream of
the DAC" does not describe the breath channel at all. **Rank: High.**

## H-4 — ADR 0010 still books "four to six" marker bits. Eight were decided on 2026-09-21.

`docs/decisions/0010-key-layout-as-data.md:172-174`

> - **Four to six of the spare chain bits belong to the marker pattern**
>   (ADR 0001) and are not available for switches. Eight to ten remain, which is
>   more than three.

`docs/decisions/0001-mcu-and-board-partitioning.md:320-321`

> **Use 8 of the 14 spare chain bits as a fixed marker pattern. DECIDED,
> 2026-09-21** — this line read "4–6" until then.

`hardware/controller/cluster-boards.md:288-291`

> ### The marker pattern: 8 bits, not 6 — DECIDED 2026-09-21
> `key-layout.yaml` booked 6 marker bits and 5 genuinely free ones. **It now says
> 8 and 3**

Six remain, not "eight to ten" — three reserved spare-switch bits and three
free. A reversed decision with no note in the ADR that carries the stale number.
**Rank: High** (it is the document that owns the spare-bit budget).

## H-5 — ADR 0001 contradicts itself on the free-bit count, in the same document as the decision that changed it.

`docs/decisions/0001-mcu-and-board-partitioning.md:289-292` (fix 6)

> **Tie `CLK INH` low at all four devices, and pull every unused parallel
> input.** … The five genuinely free spare bits are floating CMOS inputs — the
> exact fault `R-KEY-PU` exists to fix.

`docs/decisions/0001-mcu-and-board-partitioning.md:337-338`

> So the allocation is **6 marker → 8 marker, 5 free → 3 free**, and the 3 that
> remain still get pulled per fix 6.

Fix 6 says five; the section 45 lines later says three. `cluster-boards.md:348`
and `bom.csv:90` both say three. **Rank: High** — this is a hard-wired,
unretrofittable copper decision and the ADR gives two numbers for it.

## M-3 — ADR 0001's "Twenty-one sets" is stale against `R-KEY-PU` qty 24.

`docs/decisions/0001-mcu-and-board-partitioning.md:215-219`

> **Per switch position: 2.2 kΩ to 3V3, 100 Ω in series, 47 nF to ground** …
> Twenty-one sets across the four boards, so the three reserved spare-switch bits
> are covered too. (`R-KEY-PU`, `R-KEY-SER`, `C-KEY`; values per `bom.csv`.)

`hardware/controller/cluster-boards.md:355-357`

> `R-KEY-PU` is now **qty 24**. Found in review.

`bom.csv` carries `R-KEY-PU` 24, `R-KEY-SER` 21, `C-KEY` 21. The three free bits
get a pull-up and nothing else, so "twenty-one sets" is right for two of the
three parts and wrong for the one that matters. **Rank: Medium.**

## M-4 — ADR 0004's presence-detect section is superseded two headings later and carries no note.

`docs/decisions/0004-cv-interface-module.md:346-359` prescribes the mechanism —

> - **Gate the 74AHCT125's output enable from a real presence detect**, so
>   "instrument absent" is a state the hardware knows about rather than one it
>   stumbles into.
> **It needs a bench override.** … A jumper or a solder link that forces
> `OE` low is two pads.

— and `0004:367-369`, the very next heading, deletes it:

> ### There is no presence detect, and the buffer runs unconditionally
> **Both versions are deleted.**

`hardware/module/digital-and-supervision.md:32` confirms: *"OE x4 → GND | tied
ENABLED"*. The earlier prose is live, unstruck and reads as a requirement. ADR
0004 marks the watchdog deletion with a proper `> **Withdrawn 2026-09-21.**`
block at `:424`; it did not do the same here. **Rank: Medium.**

## M-5 — ADR 0004's power-on table still says "an A/C grade part". ADR 0006 locked C.

`docs/decisions/0004-cv-interface-module.md:436-439`

> The DAC's own `CLR` pin already does exactly what is wanted — an A/C grade part
> clears to zero scale, which parks pitch subsonic and the mod channels at 0 V
> (ADR 0006)

`docs/decisions/0006-cv-channel-allocation.md:146-150`

> **Not "A or C", which this line used to say.** The grade letter selects the
> **reference gain** as well as the reset state … Only C satisfies both
> requirements.

`mod-channels.md:150` calls the grade **locked** and `:169-174` makes it
safety-critical in a second way. The paragraph sits inside ADR 0004's withdrawn
block, which mitigates but does not correct it. **Rank: Medium.**

## L-1 — ADR 0004's withdrawal notes reference a claim the ADR no longer contains.

`docs/decisions/0004-cv-interface-module.md:651-652` and `:684-685` both attack
*"this ADR's claim of '16–20 mm'"* knobs. Mechanically: the string `16–20`
occurs in ADR 0004 **only at those two lines** — i.e. only inside the two
withdrawals. The claim itself has already been removed, so the notes now argue
with nothing. `bom.csv:84` and `breath-output-stage.md:285` repeat the same
withdrawal. **Rank: Low** (harmless, but it is exactly the pattern that makes a
reader hunt for text that is not there).

---

# 3. ADRs that contradict the schematic that implements them

## S-1 (SHOWSTOPPER) — Three documents say the in-amp's `REF` pin is grounded. The schematic says it carries a buffered trimmer, and explains why grounding it breaks the panel knobs.

`hardware/module/breath-receive-stage.md:93-96`

> **`REF` is driven from a buffered trimmer** set once at commissioning.
> +0.437 V nulls a *typical* +0.200 V pedestal — but the pedestal is a **spec
> band, not a number**: 0.152–0.378 V … **Range the trimmer 0 → +1.0 V.**

`hardware/module/breath-receive-stage.md:117-123`

> **Grounding it makes the panel knobs interact, and an earlier revision of this
> page claimed the opposite.** With `REF` at 0 V the sensor's pedestal stays in
> the signal, *upstream of the gain pot*, and gets multiplied by it: trim the jack
> to zero at unity gain, turn GAIN to 2.4×, and the jack idles around **+0.6 V —
> into a VCA**.

Against that:

`ROADMAP.md:51` (E10)

> Analog breath stage: in-amp receiver with `REF` grounded, gain/offset knobs.

`firmware/README.md:69-71`

> **Breath is outside all of this.** It never passes through the DAC, and since
> the in-amp's `REF` pin is grounded rather than driven by a firmware zero
> (ADR 0003), no DAC register touches the breath jack at all.

`hardware/module/breath-receive-stage.md:285-287` (the schematic page's own prose,
contradicting its own circuit)

> `CLR` reaches the DAC channels; breath touches none of them, and now that
> `REF` is grounded it touches the breath stage in no way at all

**Rank: Showstopper.** `TRIM-BREATH-ZERO` exists in `bom.csv:109` ("10k
multiturn cermet + divider from the LM317 5.21V rail"), ADR 0003:371 and :574
both describe it as a commissioning trimmer, and ROADMAP E10 itself says *"Set
`TRIM-BREATH-ZERO` first, until the in-amp output reads 0 V"* — **four words
after** telling the builder `REF` is grounded. The two instructions in the same
ROADMAP cell are mutually exclusive. The conclusion `firmware/README.md` draws
from the false premise (that no DAC register touches breath) happens to be true
for a different reason, which is what makes this survive unnoticed.

Note the attribution is also false: `firmware/README.md` credits "(ADR 0003)",
and ADR 0003 says the opposite.

## H-6 — ADR 0006 says `C-FB-PITCH` is 1 nF "across the feedback resistor" and `C-FILT-PITCH` is deleted. The schematic says 2.2 nF, **not** across the feedback resistor, and `C-FILT-PITCH` is restored.

`docs/decisions/0006-cv-channel-allocation.md:611-615`

> **Adopted.** Pitch now closes its DC loop at the jack, with `C-FB-PITCH` (1 nF
> across the feedback resistor) taking the loop back to the op-amp output above
> ~16 kHz — which is also the reconstruction pole, so it is one part doing both
> jobs. `C-FILT-PITCH` is deleted: a capacitor to ground at the jack would now sit
> inside the DC loop at exactly the handover.

`hardware/module/pitch-stage.md:216-225`

> ### ⚠ `C-FB-PITCH` goes from the op-amp OUTPUT to the (−) input
> **Not "across the feedback resistor".** With the tap at the jack, `R2` spans
> *jack → (−)*, so a capacitor across `R2` connects the same two nodes and
> leaves `R-OUT-PROT` inside the loop at every frequency — which is the
> capacitive-load-in-the-loop case, at **18° of phase margin with 2 m of cable
> and under 10° with four destinations.**
> The drawing above is right. Three other places said "across the feedback
> resistor" and were wrong, and prose is what a layout gets built from.

`hardware/module/pitch-stage.md:136` and `:205-214`

> | **C-FILT-PITCH** | **10 nF C0G** | Restored at the jack. …
> **`C-FB-PITCH` goes to 2.2 nF**, which with the jack cap restored is
> maximally flat

`bom.csv:108` agrees with the schematic (2.2 nF, *"FROM THE OP-AMP OUTPUT TO THE
(-) INPUT. NOT 'across the feedback resistor'"*), and `bom.csv:119` carries
`C-FILT-PITCH` 10 nF qty 1.

**Rank: High.** ADR 0006 is one of the "three other places" the schematic names,
and it is the one that reads as the decision of record. It is wrong on the
value, on the topology, and on whether a part exists. ADR 0006 compounds it at
`:639-644`:

> **Pitch is now the exception** — its feedback is tapped at the jack, so that
> node is the feedback node and carries no capacitor at all.

## H-7 — ADR 0006 still specifies an LT5400 1:4 ratio for the mod channels. They are built from 1 % discretes.

`docs/decisions/0006-cv-channel-allocation.md:111-113`

> - **Gain of 4 is a 1:4 ratio**, which the LT5400 family offers directly — no
>   external resistor, so no absolute tempco leaks into the gain.

`hardware/module/mod-channels.md:6-9`

> ADR 0006 specifies `Vout = 4 × (Vdac − 2.5 V)` and
> contradicts itself about how to build it — the topology section offers an
> LT5400 1:4 ratio, the calibration section says ordinary 1 % discretes. The
> discretes won (ADR 0006, `R-MODGAIN`), and this page is what they build.

`hardware/module/mod-channels.md:93-94`

> | **R1** | 10 kΩ 1 % | To the shared reference |
> | **R2** | **30 kΩ 1 %** | Feedback. `k = 3`, gain `1 + k` = **exactly 4** |

`bom.csv:66` — `R-MODGAIN,module,10k / 30k 1% metal film,…,8`. `bom.csv:15` —
`R-PRECISION,module,"LT5400 **1:1** quad (four equal 10k)",…,1`, *"Two of four
sections used."*

**Rank: High.** The gain is not 4 either, in the ADR's own arithmetic: the
two-resistor form is `1 + k` with `k = 3`, which is a **1:3** ratio, not 1:4.
`pitch-stage.md:314-315` closes the door on the LT5400 route independently:
*"The claim that two spare sections can build the mod channels' 1:3 is
**arithmetically impossible** — three sections against the fourth is all four."*

## H-8 — ADR 0006 gives the shared mod offset as 2.5 V in three places and 3.3333 V in three others. The schematic and firmware say 3.3333 V.

Still-2.5 V in ADR 0006:

- `:116` — *"**The 2.5 V reference point comes from a buffered DAC channel**"*
- `:130` — *"With a fixed 2.5 V offset, `Vout = 4 × (Vdac − 2.5)`"*
- `:186` — *"| Mod offset | written once at boot | The shared 2.5 V reference point |"*
- `:102-107` — the worked block `Vout = 4 × (Vdac − 2.5 V)`

Already-3.3333 V in the same ADR: `:15` (the decision table), `:21-22`, `:83-85`
(via the pitch-stage note), and the whole two-resistor discussion.

`hardware/module/mod-channels.md:95`

> | **V_ref** | **3.3333 V** from DAC ch7, buffered | Shared by all four.
> Intercept is `k · V_ref` = 10.000 V |

`firmware/README.md:49-53`

> The mod channels are `Vout = 4·Vdac − 3·V_ref`, with `V_ref` the shared
> **3.3333 V** from DAC channel 7 … *(The value changed with the two-resistor
> redraw in `mod-channels.md`; writing the old 2.5 V into channel 7 against the
> current 10 k/30 k network gives a −7.5…+12.5 V window — wrong span, and it
> clips positive.)*

**Rank: High.** `firmware/README.md` states the exact consequence of a builder
following ADR 0006's stale number, and ADR 0006's own decision table is the
place a firmware author would look first. The `:186` row is the most dangerous
one: it is the row that tells firmware what to write.

## H-9 — ADR 0005 sets the load-switch limit at "1.0 A" and a "50–100 ms ramp". The schematic says 0.940 A, a 100 ms ramp and a 150 ms timer, and that every start begins in current limit.

`docs/decisions/0005-power-architecture.md:260-262`

> ### Set the limit at 1.0 A, and delete the polyfuse
> **1.0 A, latch-off, with a programmed 50–100 ms ramp.**

`docs/decisions/0005-power-architecture.md:279-285`

> **It boots — in about 75 ms of constant-current start** … The prescription is
> the same either way: a programmed ramp and a fault timer longer than it.

`hardware/module/power-entry.md:111-113`

> **1. The limit is 0.940 A, not 1.0 A.** The LT1641's sense threshold is
> **47 mV**, not 50 `[web, two reviewers]`. `R-ILIM` at 50 mΩ gives
> `47 mV / 50 mΩ = 0.940 A` `[calc]`.

`hardware/module/power-entry.md:115-122`

> **2. Foldback was described backwards, and it fights the start.** … It regulates
> the sense drop to about **12 mV at V_out = 0**, i.e. **240 mA** `[calc]` —
> *below* the programmed charging current. **Every start therefore begins in
> current limit.**

`hardware/module/power-entry.md:137-143`

> **4. There was no gate capacitor anywhere.** Not in the drawing, not in
> `bom.csv`. The FET sizing, the boot analysis and ADR 0005's 50–100 ms
> specification all rest on a "programmed ramp" that **did not exist**.

`hardware/module/power-entry.md:145-156`

> `= 51.5 ms` bare / `~ 62 ms` with the strip quiescent and both bucks loading …
> **The timer must exceed that, not the 26 ms the old page compared against.**

`hardware/module/power-entry.md:169-170`

> **Target: a 150 ms timer** (2.4x the 62 ms loaded start) **and a 100 ms
> ramp** (120 V/s, 264 mA of charging).

**Rank: High.** ADR 0005 is the ADR the BOM cites for this part (`bom.csv`
`U-LOADSW`, `R-ILIM`, `C-TIMER-LOADSW`, `C-GATE-LOADSW` all `adr=0005`). Three
of ADR 0005's four load-lines are stale: the limit, the start time, and the
claim that the node "rises monotonically" so a normal start never enters current
limit. Only the `-1` latch-off suffix survives intact.

Sub-finding, same section: ADR 0005 sets the limit *"from below, by the
clamp-legal worst case of ~630 mA plus ramp current"* (`:273-274`) while its own
load table two pages earlier gives clamp-legal worst as **579 mA** on the
umbilical (`:160`). Internal, **Rank: Low**.

## H-10 — ADR 0003 bills the umbilical as carrying seven channels. ADR 0004, the latency budget and `firmware/README.md` all say six.

`docs/decisions/0003-breath-sensing-path.md:413-421`

> | **Breath analog, 7 channels at 4 kHz** | **0.90 Mbit/s** | **2 MHz** |
> *(The 0.6 MHz this table used to give came from a 2 kHz mod rate and five
> channels; ADR 0006 moved to 4 kHz and the loop refreshes seven.)*

`docs/decisions/0004-cv-interface-module.md:54` and `:63-65`

> | **Breath analog, 6 channels at 4 kHz** | **0.77 Mbit/s** | **≥1.5 MHz → specify 2 MHz** |
> (Seven channels were populated until the breath ambient-zero was deleted —
> ADR 0003 — which is slack, not a reason to drop the clock)

`docs/reference/latency-budget.md:169-173`

> Six channels means *all* the populated ones … The breath ambient-zero channel
> that briefly made it seven is deleted (ADR 0003).

`hardware/module/mod-channels.md:166-167` and `firmware/README.md:64-65` both
book six. `docs/decisions/0006:22-23` — *"**Six of eight channels used, two
spare.**"*

**Rank: High.** ADR 0003 is the document that deleted the seventh channel, and
it is the only document still counting it. Both other documents cite ADR 0003 as
the authority for six — a citation that points at a document saying seven.

## M-6 — ADR 0003's "band-limit at both ends" is implemented at one end only.

`docs/decisions/0003-breath-sensing-path.md:405-409`

> **Band-limit at both ends, around 500 Hz.** The sensor only has ~159 Hz of real
> bandwidth, so a narrow channel costs nothing and rejects almost everything that
> could couple in

`docs/decisions/0003-breath-sensing-path.md:342-343`

> the instrument end needs **only a buffer** — an op-amp follower, band-limited,
> with a series resistor for protection.

`hardware/module/breath-receive-stage.md:154-164` — the instrument side carries
`R1` 1 kΩ and `R1b` 1 kΩ and **no capacitor**. Every pole on the breath path is
module-side: `C_diff` 15 nF at 482 Hz *"ahead of the in-amp"*, `C_cm` ×2, and the
output RC. The only instrument-side filter is `C-AA-ADC` 47 nF, which is on the
**ADC branch** (`0003:533`), not on the umbilical drive.

`hardware/controller/carrier.md:282-284` quotes ADR 0003's rule verbatim —
*"band-limit at both ends, around 500 Hz"* — which the mechanical check confirms
is a faithful quote, of a rule the drawn circuit does not implement.
**Rank: Medium** — the rule is either stale or an unbuilt requirement, and
nothing says which.

## M-7 — "Differential over the umbilical" is stated in two corpus documents; ADR 0003 explicitly declines differential drive.

`docs/decisions/0006-cv-channel-allocation.md:12`

> | **Breath** | **analog, differential over the umbilical** | 0–10V, …

`docs/reference/latency-budget.md:139-141`

> **Breath output never digitised at all** — it goes down the umbilical as a
> differential analog signal (ADR 0003)

`docs/decisions/0003-breath-sensing-path.md:341-343, 395-397`

> it means the instrument end needs **only a buffer** — an op-amp follower …
> **No differential line driver.**
> Full differential signalling was considered and is not needed: it buys about
> 6 dB against induced noise … at the cost of a driver in the instrument.

`breath-receive-stage.md:22-28` draws a single-ended buffer into `BREATH` with
`AGND` as a sense return. It is *differentially received*, not differentially
driven. `latency-budget.md` cites ADR 0003 for the opposite of what ADR 0003
says. **Rank: Medium.**

## M-8 — ADR 0006 still says breath wants a ~2 kHz filter, and elsewhere says that claim is superseded.

`docs/decisions/0006-cv-channel-allocation.md:50-51`

> - **Breath wants a gentler filter**, ~2 kHz. It is an inherently slow signal and
>   the steps should be smoothed in hardware.

`docs/decisions/0006-cv-channel-allocation.md:656-659`

> it is already a 482 Hz channel by the time it reaches the module
> (`hardware/module/breath-receive-stage.md`). This
> ADR's earlier "~2 kHz for breath" is superseded by that page.

The superseding note is 600 lines below the text it supersedes, which is still
live and unmarked. ADR 0006's own output table at `:654` gives breath as
`330 nF film / ~480 Hz`, matching `breath-receive-stage.md:164`. **Rank:
Medium** — a correct note pointing at text nobody edited.

## M-9 — ADR 0006's power-on table says pitch parks "below −2 V". The schematic says 0.000 V.

`docs/decisions/0006-cv-channel-allocation.md:154-156`

> | **Pitch** | Bottom of its range, below −2 V | Subsonic. A VCO there is inaudible |

`hardware/module/pitch-stage.md:138-142`

> **Power-on is 0.000 V, not "subsonic".** `V_ref` is the DAC's internal
> reference, which is **disabled until firmware writes an enable** — so *both*
> terms are zero and the jack sits at **0 V, a VCO's base note**, until that
> write. After it, `CLR` parks at −2.500 V. ADR 0006's power-on table asserts
> "below −2 V" for both; they are different states, 2.5 V apart.

Mechanically verified: `below −2 V` is a faithful quote of `0006:156`.
**Rank: Medium** — ADR 0006 itself notes the reference-disabled trap at
`:163-168` and never carried it into its own table.

## M-10 — ADR 0006 says "a two-point fit" in three live places and "multi-point" in one.

`docs/decisions/0006:283-284`

> a per-unit calibration table in NVS, and a two-point fit verified against a real
> VCO

`docs/decisions/0006:676-680`

> **Put the two pitch calibration anchor points inside the musically used range**
> … A two-point fit is only as good as its anchors

`docs/decisions/0006:724`

> take the two-point fit with the meter, then verify tracking against a real VCO

against `docs/decisions/0006:413-417`

> Use a **multi-point** table, roughly one point per octave — Mutable's Yarns
> uses **eleven** (`kNumOctaves = 11`) … An earlier revision of this line said
> twelve.

`ROADMAP.md:50` (E9) asserts multi-point *"is … what ADR 0006 asks for; this row
said 'two-point' and contradicted it."* The ROADMAP fixed its own row and the
ADR it cites is still 3-to-1 the other way. **Rank: Medium** — the ROADMAP's
citation is only 25 % true.

## M-11 — The DAC regulator is 5.21 V in the schematics and 5.25 V in four corpus documents.

5.21 V (settled; `bom.csv` divider 150 Ω / 475 Ω gives 1.25 × (1 + 475/150) =
**5.208 V**):
`power-entry.md:18`, `pitch-stage.md:89`, `breath-receive-stage.md:55`,
`breath-output-stage.md` (offset rail), `digital-and-supervision.md:40`,
`0005:125`, `0003:371,578`, `0004:159`.

5.25 V (stale): `0004:132`, `0004:282` (its own power-tree diagram),
`0006:542`, `0006:688`, `ROADMAP.md:47` (E6), `bom.csv:37` (`U-REG-DAC`
description).

ADR 0004 gives both numbers, 123 lines apart, one of them inside the diagram the
ADR points at. **Rank: Medium.**

## M-12 — ADR 0001's key-network timing numbers disagree with the cluster-board schematic.

`docs/decisions/0001-mcu-and-board-partitioning.md:223-228`

> | Release, τ = 2.2 kΩ × 47 nF | 103 µs; crosses `V_IH` at **125 µs** |
> | Press, τ = 100 Ω × 47 nF | 4.7 µs; crosses `V_IL` at **5.7 µs** — 44× inside the 250 µs scan |

`hardware/controller/cluster-boards.md:155-157`

> | Release, τ = 2.2 kΩ × 47 nF | 103 µs; crosses `V_IH` at **119.9 µs** |
> | Press, τ = 100 Ω × 47 nF | 4.7 µs; crosses `V_IL` at **5.92 µs** — 42× inside the 250 µs scan |

Same τ, same thresholds, different crossings. Neither document flags the other.
(`cluster-boards.md:164` then calls it *"the 125 µs release filter"*, using ADR
0001's number against its own table.) **Rank: Medium** — the numbers are close
enough that nothing breaks, which is why it will survive indefinitely.

## L-2 — ADR 0004 gives the SPI clock as "~1 MHz" in its own conductor budget.

`docs/decisions/0004-cv-interface-module.md:84`

> SCLK      / DIG_GND     SPI to the DAC, ~1 MHz

Against `0004:37` (*"SPI to the DAC, ~2 MHz"*), `0004:54` (*"specify 2 MHz"*),
`carrier.md:573` and ROADMAP E11. Two code blocks in the same ADR, 47 lines
apart. **Rank: Low.**

## L-3 — ADR 0004's panel-height figure is asserted twice and debunked in the same ADR.

`0004:500` — *"a panel already at 107 mm of ~110 mm usable"*;
`0004:585` — *"Roughly 107 mm of ~110 mm usable height — full but workable."*
`0004:648-650` — *"this ADR's own '107 mm of ~110 mm usable' figure is asserted
twice and derived nowhere"*, and `0004:661-667` derives **97 mm**. The two
assertions are still there. **Rank: Low.**

## L-4 — ADR 0004's design-principles line reads "inside 10HP rather than 10 or 12".

`docs/decisions/0004-cv-interface-module.md:518-519`

> That discipline is what kept the panel inside 10HP rather than 10 or 12.

An 8→10 search-and-replace artefact; the sentence now excludes the width it
claims. **Rank: Low.**

---

# 4. Broken and hollow cross-references

*Every double-quoted phrase in the corpus was extracted and searched across the
whole repository, normalised for smart quotes, dashes, Markdown emphasis and
whitespace. Findings below are the ones where a phrase is attributed to a source
that does not contain it, or where a named object does not exist.*

## S-2 (SHOWSTOPPER) — ADR 0003 defines the analog star point on a board that does not exist.

`docs/decisions/0003-breath-sensing-path.md:641-650`

> ## The analog ground star point, defined
> Several rules in this ADR refer to bonding `AGND` to "the instrument's analog
> ground star point". A review pointed out that **no such point was defined
> anywhere**, so the rules referenced an object that did not exist.
> It exists now …
> > **The star point is the analog ground pour on the bottom cluster board, at the
> > sensor and reference, immediately adjacent to the umbilical connector.**

`hardware/controller/cluster-boards.md:11` and `:425-436` enumerate the four
cluster boards: `left_hand`, `right_hand`, `left_thumb`, `right_thumb`. Each
carries one `74HC165`, its decoupling and its key networks — *"Four boards, **one
circuit**"*. **There is no "bottom cluster board", and no cluster board carries
any analog part.**

`hardware/controller/carrier.md:257-259`

> **1. The analog star point is on this board, and `AGND` is sense-only.**
> ADR 0003 names the star point as "the analog ground pour on the bottom cluster
> board" `[repo] 0003` — a board that does not exist; it means this one.

`ROADMAP.md:54` (E13) confirms where the analog actually is: *"carrier holds
ADC, reference, buffer, level shifter, regulators, connectors"*.

**Rank: Showstopper.** The fix to a "rules referencing an object that did not
exist" finding replaced it with an object that also does not exist. It is
propagated: `hardware/module/breath-receive-stage.md:20` draws the sensor,
buffer and ADC under the label

> INSTRUMENT (bottom cluster board)

so the two pages that a builder would use to lay out the analog section
disagree about which PCB it is on.

## S-3 (SHOWSTOPPER) — ADR 0004 and ROADMAP E12 require `DIG_GND` its own path to the star. The schematic says that is the classic split-plane mistake and does not do it.

`docs/decisions/0004-cv-interface-module.md:565-573`

> - **`PWR_GND` runs from the etherCON to the star point on its own copper** …
> - **`DIG_GND` likewise** — its own path to the star.

`ROADMAP.md:53` (E12)

> **Ground laid out to the star rule in ADR 0004** — one origin at the power
> inlet, `PWR_GND` and `DIG_GND` each on their own copper, `AGND` not a return at
> all. Free now, a bodge wire or a respin afterwards

`hardware/module/power-entry.md:252-258`

> One origin, at the IDC's ground pin. `PWR_GND` — the ~360 mA umbilical return
> — runs to it on its own copper and touches nothing else on the way. The analog
> return is its own region joining at the star. **`DIG_GND` is *not* given its
> own path to the star**, which an earlier revision of ADR 0004 asked for: a
> 2 MHz SPI return wants the pour directly under its trace, and routing it to a
> distant star point is the classic split-plane mistake.

**Rank: Showstopper.** The schematic calls ADR 0004's rule "an earlier revision"
— but ADR 0004 has not been revised, and the ROADMAP row is the one a builder
follows at layout. The ROADMAP row is explicit that this is *"free now, a bodge
wire or a respin afterwards"*, i.e. it is an irreversible layout instruction that
points at the superseded rule. Two of the three clauses in the ROADMAP row are
correct (`PWR_GND` own copper, `AGND` not a return); the third is the one the
schematic reversed.

## H-11 — `mod-channels.md` quotes ADR 0006 saying something ADR 0006 does not say.

`hardware/module/mod-channels.md:132-135`

> ADR 0006 says these channels need to be "linear
> and repeatable, not calibrated", and they still are — but "repeatable" is doing
> more work than the old number implied

**Mechanical result:** the string `linear and repeatable, not calibrated`
appears nowhere in `docs/decisions/0006-cv-channel-allocation.md`. It appears in
the repository only in `mod-channels.md` itself and in three review documents
quoting it back. What ADR 0006 actually says:

`0006:286-287`

> Channels 2–6 need only to be linear and repeatable. Nobody's ear cares whether a
> modulation CV is 2% off.

`0006:441-443`

> **Mod channels stay trimmer-free.** They need to be linear and repeatable, not
> musically accurate

"not calibrated" and "not musically accurate" are not the same claim — pitch is
the calibrated channel *and* the musically accurate one, so the substitution
happens to preserve the conclusion while changing the stated reason. **Rank:
High**, because `mod-channels.md` is building an argument about tolerance on top
of the quote.

Secondary: ADR 0006's "Channels 2–6" numbering is itself stale — under the
current allocation the mod channels are DAC ch 2–5, ch 6 is spare and ch 7 is the
offset (`0006:11-15`). "Channels 2–6" belongs to the pre-deletion numbering.

## H-12 — `bom.csv`'s `KNOB-BREATH` row matches a shaft to a refdes that does not exist.

`hardware/bom.csv:84`

> KNOB-BREATH,module,Knob to match the pot shaft - 14mm MAX diameter,,"Knobs for
> the breath gain, offset and response pots",n/a,3,candidate,,0004,"Match the
> shaft of the **POT-BREATH** variant ordered - D-shaft and knurled are not
> interchangeable | 2026-09-21: THREE, not two - POT-RESP added. …"

**Mechanical result:** `POT-BREATH` is not a `ref` in `hardware/bom.csv`. The
grep across the corpus returns it only inside this one note (every other hit is
in `docs/review/2026-09-20-cold-review/`, i.e. pre-split history). The three
actual pots are `POT-GAIN` (`bom.csv:124`, 50 k), `POT-OFFSET` (`:125`, 10 k
linear) and `POT-RESP` (`:80`, 50 k linear) — and they are **not the same shaft
family by default**: two 50 k and one 10 k from potentially different orders.
The instruction "match the shaft of the POT-BREATH variant ordered" cannot be
followed. **Rank: High** — it is a purchasing instruction for a panel that is
cut once, and the row was updated to qty 3 on 2026-09-21 without the refdes
being touched.

## H-13 — ADR 0004 specifies `R-MOSI-SER` at 220 Ω. The refdes does not exist, the count is wrong, and the value was revised to 100 Ω.

`docs/decisions/0004-cv-interface-module.md:69-74`

> `R-MOSI-SER` at 220 Ω with ~200 pF of cable is a **3.6 MHz** corner — 7.9 MHz
> is the 100 Ω case this same sentence offers as the fix, which is the wrong way
> round. 2 MHz still has margin, but less than claimed, and transmission-line
> analysis puts the right value nearer 68 Ω

`docs/decisions/0004-cv-interface-module.md:479-482`

> **220 Ω in series on MOSI at the driving end.** Source termination on the one
> line that runs the full umbilical carrying data.

`hardware/bom.csv:49`

> R-SPI-SER,controller,100R 1%,,"Series termination on SCLK, MOSI and CS at the
> driving end",…,3,… "THREE. 100R, not 220R - revised 2026-09-21. … At 220R the
> far end's first step is 1.83-1.86V against the 74AHCT125's 2.0V VIH, dwelling
> ~20ns per edge in the forbidden band on a part with no hysteresis. 100R gives a
> clean 2.75V single step … 68R is electrically ideal but draws 48mA against a
> 40mA pad spec. carrier.md used to draw these as R-SCLK-SER / R-MOSI-SER /
> R-CS-SER, **which were in no BOM**"

`hardware/controller/carrier.md:541-545`

> **All three are `R-SPI-SER`, and the value is 100 Ω.** The refdes matters:
> this page previously drew `R-SCLK-SER`, `R-MOSI-SER` and `R-CS-SER`, **none
> of which exist in `bom.csv`**

**Rank: High.** ADR 0004 is now the last document carrying the dead refdes and
the withdrawn value, and it offers 68 Ω as "the right value" — a figure the BOM
rejects on pad current. `digital-and-supervision.md:223-226` independently says
*"`SCLK` has no series resistor and `MOSI` does. That is the wrong way round"*,
which is a direct hit on ADR 0004's one-resistor-on-MOSI specification.

## M-13 — ROADMAP E10 requires "Four mod channels trimmed". The mod channels have no trimmers.

`ROADMAP.md:51` (E10)

> … Four mod channels trimmed |

`docs/decisions/0006-cv-channel-allocation.md:441-443`

> - **Mod channels stay trimmer-free.** They need to be linear and repeatable, not
>   musically accurate; firmware scaling is sufficient there

`hardware/module/mod-channels.md:228-230`

> - **Per-channel scale and offset are firmware, not hardware.** ADR 0006 puts
>   source, scale, offset, curve and slew on the instrument's display. This stage
>   is a fixed ±10 V window and stays that way.

`bom.csv` carries exactly three trimmers — `TRIM-GAIN` (1), `TRIM-OFFSET` (1),
`TRIM-BREATH-ZERO` (1) — all on pitch and breath. **Rank: Medium** — an
acceptance criterion for a milestone that cannot be met by turning anything.

## M-14 — ROADMAP E8's "trimmers go both ways" is contradicted by the pitch schematic.

`ROADMAP.md:49` (E8)

> Raw analog gain and offset trimmed to target, linear across the span. The
> 5%-over kludge is deleted — trimmers go both ways (ADR 0006)

The citation is faithful (`0006:424-425`: *"The 'design the gain 5 % high'
kludge is deleted. … A trimmer goes both ways."*). The circuit is not:

`hardware/module/pitch-stage.md:130`

> | **TRIM-GAIN** | **200 Ω** … 0 → +2 % of ratio, **one-sided and now pointing
> the wrong way**: the justification was that the load divider only ever
> *reduces* gain, and the jack-side tap deleted the divider. Nominal is dead on
> 2.000 and the trimmer has no downward authority.

`hardware/module/pitch-stage.md:316-320`

> - **`TRIM-OFFSET` is not buildable as described.** `V_ref` nominal *is*
>   `VREFOUT`, and a divider can only go below it, so the nominal sits at an end
>   stop with no downward authority.

**Rank: Medium** as a correctness issue; see §5 (O-1) for the ordering
consequence, which is worse.

## M-15 — ROADMAP E10's rationale cites a watchdog that has been deleted.

`ROADMAP.md:51` (E10)

> **Pull the umbilical mid-note with the mouthpiece at rest** and confirm the
> breath jack parks quietly: the watchdog has no authority over it by design, and
> this is the check that the design is right about why (ADR 0004).

`hardware/module/digital-and-supervision.md:153-158`

> ## There is no frame watchdog
> **Deleted.** A 74HC123 monostable used to assert the DAC's `CLR` when SPI
> traffic stopped. The part, its timing pair and its decoupling are gone

`docs/decisions/0004-cv-interface-module.md:424-432` marks the withdrawal but
keeps the section `#### The watchdog's scope is the DAC channels, and breath is
outside it` (`:445`) live, which is what the ROADMAP cites. The *test* is still
worth running; the *reason given for it* describes a mechanism that no longer
exists, and `digital-and-supervision.md:172` records the real current behaviour:
*"Cable unplugged mid-note … **not caught — the DAC holds and the rack
drones**"*. **Rank: Medium.**

## M-16 — `breath-receive-stage.md`'s watchdog section contradicts its own circuit.

`hardware/module/breath-receive-stage.md:283-290`

> **Nothing, and that is correct.** `CLR` reaches the DAC channels; breath touches
> none of them, and now that `REF` is grounded it touches the breath stage in no
> way at all

Same page, `:93` — *"`REF` is driven from a buffered trimmer"*; same page, `:115`
— *"### Why `REF` is trimmed rather than grounded"*. Listed separately from S-1
because this is the schematic itself, i.e. the document the corpus defers to.
**Rank: Medium.**

## M-17 — ADR 0012 leaves open a question `firmware/README.md` has settled.

`docs/decisions/0012-configuration-interface.md:130-132`

> - Whether the web app's state is the authority, or the instrument's NVS is, when
>   they disagree after an interrupted session.

`firmware/README.md:146-149`

> **Single source of truth:** every config edit round-trips. The phone edits, the
> display board forwards, the real-time board validates, applies, persists and
> echoes back. The display board never writes authoritative state — two
> authorities that can disagree is the failure mode worth designing out.

`docs/decisions/0013-two-mcu-split.md:31` states it as a decision in a table
(*"State | **Authoritative** | None"*). An Open item that three other documents
have closed. **Rank: Medium.**

## L-5 — ADR 0009's Context still describes "three or four" underside keys for the left thumb.

`docs/decisions/0009-enclosure-construction.md:10-13`

> aluminium key plate on top, and three or
> four mechanical keys on the underside for the left thumb

`hardware/controller/cluster-boards.md:37-42` puts **seven** switches on the
underside — `left_thumb` 4 and `right_thumb` 3, both on `PLATE-THUMB`, *"inside
face of the oak bottom"*. `config/key-layout.yaml` agrees (LT1–4 `face: bottom`,
RT1–3 `face: bottom`). ADR 0009 itself knows this at `:401-402` (*"The right
thumb rests on the instrument and its three control switches"*). ADR 0010:45
settles the count: *"**18 switches**, decided"*. **Rank: Low** (Context prose,
not a specification).

## L-6 — Refdes drawn on schematic pages with no BOM row.

Mechanical scan of `` `REFDES` `` tokens against `bom.csv`:

| Refdes | Cited in | Status |
|---|---|---|
| `C-ADC-BULK`, `R-LED-PD` | `carrier.md` | marked **proposed** on the page — acceptable |
| `J-UMB`, `J-DISP` | `carrier.md` | connectors with no BOM row at all |
| `R-IN`, `R-OFF`, `R-OFFNEG` | `breath-output-stage.md` | BOM groups them as `R-BREATH-SUM` / `R-BREATH-OFF`; names do not match |
| `C-TIMER`, `C-GATE` | `power-entry.md` | BOM calls them `C-TIMER-LOADSW` / `C-GATE-LOADSW` |
| `R-PRESENCE` | `digital-and-supervision.md` | part deleted; the page's own *Still open* list asks for "a corrected `R-PRESENCE` row" for a circuit it deleted |
| `R-OE-PU`, `R-LED` | `power-entry.md`, `digital-and-supervision.md` | both pages state these never had BOM rows — correctly disowned |
| `R-MOSI-SER`, `R-TERM-CHAIN`, `R-OFFINJ`, `SW-PWR-INST` | ADRs 0001/0004/0005 | three are explicitly disowned as deleted; `R-MOSI-SER` is not — see H-13 |

**Rank: Low** individually, except `R-MOSI-SER` (H-13). Listed for completeness
because the scan was mechanical.

## L-7 — `digital-and-supervision.md`'s *Still open* list is about deleted parts.

`:210-217` asks for *"A power-on reset RC on the '123's own `CLR`"* and
re-litigates the '123's retrigger arithmetic, on a page whose §"There is no
frame watchdog" deletes the '123. `:227-233` does the same for the deleted
presence comparator's threshold. **Rank: Low** — a stale open-items list, but it
is the list a builder would work from.

---

# 5. `README.md` and `ROADMAP.md` against reality

## H-14 — `README.md` has two licence sections and the second says the decision has not been made.

`README.md:83-91`

> ## Licence
> Three share-alike licences, one per kind of work — **GPL-3.0-only** for
> firmware, **CERN-OHL-S-2.0** for hardware and mechanical design,
> **CC-BY-SA-4.0** for documentation. Derivatives stay open on the same terms.
> See [`LICENSE`](LICENSE) for the mapping and the reasoning, and
> [ADR 0011](docs/decisions/0011-licensing.md) for why it is three rather than
> one.

`README.md:114-118`

> ## Licensing
> Not yet decided — see
> [ADR 0011](docs/decisions/0011-licensing.md). The previous project's firmware
> was GPLv3.

Both sections cite the same ADR, which is Accepted (H-2) and whose three licence
texts are committed in `LICENSES/`. The second section is the last thing in the
file, so it is what a reader scrolling to the bottom sees. **Rank: High** — a
public repository stating in its README that its licence is undecided, under a
heading two characters different from the one that states it correctly.

## S-1 (restated) — ROADMAP E10 tells the builder to ground `REF`.

Covered in full above. It belongs in this section too: E10 is a build
instruction, the only place a commissioning sequence is written down, and it
contains two mutually exclusive instructions in one cell.

## H-15 — `README.md` describes two breath knobs; there are three controls.

`README.md:47`

> - **Breath** — dedicated, 0–10V, with panel knobs for gain and offset

`README.md:24`

> | Contains | … | DAC, analog scaling, jacks, knobs |

`hardware/module/breath-output-stage.md` §"What it costs, and the decision it
forces"

> | Panel | **A third pot and a third knob** |

`docs/decisions/0004-cv-interface-module.md:664`

> | **Three pots across** — gain, offset, response | 22 mm |

`ROADMAP.md` mentions `POT-RESP`, the response control, or a third knob
**nowhere** — mechanically checked across the whole file. E12 says *"10HP panel
cut"* without saying what changed, and F2 (*"Breath response | Curve shaping"*)
still describes response shaping as purely firmware.

Same defect in the ADR that owns the channel table, `0006:12`:

> | **Breath** | … | GAIN 0.5–4×, OFFSET ±5 V | Trimmed |

and in `0004:584` (*"two breath knobs"*). **Rank: High** — this is today's
change and it has reached exactly one schematic page, one ADR section and one
BOM row.

## M-18 — ROADMAP E12 still reasons about the etherCON brace "at 8HP".

`ROADMAP.md:53` (E12)

> etherCON braced to the PCB — good practice at 8HP rather than the structural
> necessity it was at 6HP.

`docs/decisions/0004-cv-interface-module.md:691-693`

> **Brace the connector to the PCB anyway.** … At 10HP this is good practice
> rather than a structural necessity.

The same cell correctly says *"10HP panel cut"* two clauses earlier, so the row
was half-updated. **Rank: Medium.**

## M-19 — ROADMAP's paper-fit measurement says "Comfortable at 8HP".

`ROADMAP.md:183`

> **1:1 paper fit check, both faces** | M4 | The etherCON flange against a
> 50.50 mm 10HP panel *and* against the 57 × 38 mm instrument tail beside the
> USB-C slot. Comfortable at 8HP; the tail is now the tight one (ADR 0004, ADR 0009)

The panel dimension was updated to 10HP/50.50 mm and the verdict clause was not.
At 10HP ADR 0004 gives *"13.35 mm of aluminium each side"* (`:669`), not the
8.27 mm of the 8HP row (`:612`). **Rank: Medium.**

## M-20 — ROADMAP M1's key counts do not match the layout.

`ROADMAP.md:71` (M1)

> **action assessed by hand** — fingertip vs thumb-tip, and whether the four
> thumb keys want a lighter spring than the eleven finger keys

`hardware/controller/cluster-boards.md:429`

> | `SW1-n` | Gateron KS-33 Red | LH **5** | LT **4** | RH **6** | RT **3** |

Eleven finger keys is right (LH 5 + RH 6). Thumb keys are **seven**, not four —
`left_thumb` 4 and `right_thumb` 3. The spring question is genuinely scoped to
`LT` only (`bom.csv` `SW-THUMB`, *"lighter springs are an open option for `LT`"*),
so the intent survives, but the row reads as a total and the totals are 18
switches / 15 note keys / 3 control keys (`0010:45-57`, `firmware/README.md:127`).
**Rank: Medium.**

## M-21 — ROADMAP E6's regulator voltage is the stale one.

`ROADMAP.md:47` — *"local 5.25V DAC regulator"*. See M-11. **Rank: Medium** (it
is a bring-up acceptance criterion, so it will be measured against).

## L-8 — Track F milestone IDs are out of order.

`ROADMAP.md:141-142` lists `F9 | Matrix surface` before `F8 | Persistence`. The
phase view at `:155` says Phase 5 contains *"F4–F9"*, which is consistent, but
the table reads as an error. **Rank: Low.**

## L-9 — ROADMAP E7's "all six channels" is ambiguous against the allocation.

`ROADMAP.md:48` — *"Commanded codes produce expected voltages on the meter, all
six channels"*. Six DAC channels are populated (`0006:22`), but only five reach a
jack — channel 7 drives the shared mod offset and channel 6 is spare. A meter at
a jack can verify five. **Rank: Low.**

---

## The ordering question: is there a *new* violation?

`ROADMAP.md:90-108` carries three ordering rules a review found violated
(M5 after E13; the body does not close before the carrier is revision-final; M8
exists because E11 tests a topology that does not survive). All three still hold:
M5 is in Phase 4 (`:154`), E13 and M7 are both Phase 4, M8 is pre-bond and is
cited as such by ADR 0003 (`:181-183`) and ADR 0009.

### O-1 (NEW ORDERING VIOLATION) — E8 and E9 depend on a pitch trim network whose design is deferred to E10.

`ROADMAP.md:49-50` — **E8 (Phase 2)**: *"Raw analog gain and offset **trimmed to
target**, linear across the span. … trimmers go both ways"*. **E9 (Phase 2)**:
*"Pitch calibration — Multi-point fit … 1V/oct verified against a real VCO"*.
`ROADMAP.md:152` puts both in Phase 2.

`hardware/module/pitch-stage.md:316-320`

> - **`TRIM-OFFSET` is not buildable as described.** `V_ref` nominal *is*
>   `VREFOUT`, and a divider can only go below it, so the nominal sits at an end
>   stop with no downward authority. The trim network has to put 2.500 V at
>   mid-travel — which means dividing `VREFOUT` and gaining it back, or injecting
>   a small bipolar correction. **E10, with `R-TRIM-RANGE`.**

`hardware/module/pitch-stage.md:326-329`

> - **Whether 200 Ω is the right `TRIM-GAIN`.** It is 0 → +2 % and one-sided,
>   and with the load divider gone it has no downward authority at all. Whether
>   it should be bipolar … or deleted in favour of firmware is an **E9** question.

**E8 is the milestone that trims pitch offset to target. The offset trimmer's
network is not designed until E10, two milestones and one phase later.** E9 —
which the ROADMAP calls *"the milestone that decides whether this is an
instrument or a thing that is always slightly out of tune"* (`:57-58`) — sits in
between, and is asked to resolve the gain trimmer's range while depending on it.
`R-TRIM-RANGE` has a BOM row (`bom.csv:118`, qty 4, *"Range-setting resistors for
the two module trimmers"*) with no values, so the part exists and the network
does not.

This is the same shape as the three rules already listed: a decision gated on
something that happens later. **Rank: High.** It is cheap to fix on paper —
either move the `R-TRIM-RANGE` design to E8, or split E8 into "gain trimmed" and
"offset trimmed" with the latter after E10 — and expensive to discover at the
bench with a board already stuffed.

### O-2 (secondary) — E6 must bring up a load switch whose two timing capacitors and whose `ON`-pin network are undesigned.

`ROADMAP.md:47` (E6) — *"load switch limits and ramps the umbilical feed"*.

`hardware/module/power-entry.md:179-188`

> The specified **10 nF is wrong under every reading** — 12x to 300x too small,
> giving a 0.16–4 ms timer — but the replacement value cannot be taken from a
> review. … **Read `I_TIMER`, `I_GATE` and the sense threshold off the LT1641
> datasheet and set both capacitors before ordering.** The 0805 C0G package in
> `bom.csv` is wrong for any value in the table above.

`hardware/module/power-entry.md:203-209`

> ### Still not designed: the `ON` pin
> … There is no divider, no logic level, no supply, no pull-down, no
> debounce and no UVLO threshold specified anywhere — **four missing passives on
> the node that decides whether the instrument powers up at all.**

Not strictly an ordering inversion — the work can be done before E6 — but E6 is
the first milestone that energises the instrument, and nothing in the ROADMAP
records that three of the load switch's networks are open. **Rank: Medium.**

---

## Appendix — mechanical quoted-phrase verification

226 double-quoted phrases of ≥10 normalised characters were extracted from the
corpus and searched across every `.md`, `.csv`, `.yaml` and `.txt` file in the
repository, after normalising smart quotes, en/em dashes, the minus sign, `×`,
non-breaking spaces, Markdown emphasis characters and whitespace runs.

Phrases attributed to another document and **not found there**: one —
`linear and repeatable, not calibrated` (H-11).

Phrases attributed to the citing document's own earlier revision and not found
anywhere: 18. All 18 were checked individually and all are legitimate — a
document quoting text it has since removed (e.g. ADR 0001's *"no satellite
boards"*, ADR 0006's *"uniform fast filter"* and *"firmware has no offset
authority"*, `pitch-stage.md`'s *"moves offset without touching gain"*,
`power-entry.md`'s *"no ground path at all"*). The one borderline case is ADR
0004's *"16–20 mm"* (L-1), where the withdrawal outlived the claim.

Phrases attributed to another document and **found there verbatim**: all the
rest, including every cross-document quote that carried a finding —
`the precision feature of the entire build` (ks33-geometry → ADR 0002),
`bit 0 is the first bit clocked out` (cluster-boards → ADR 0001),
`costs a few percent of hold margin` (cluster-boards → ADR 0001),
`real stability work, on a board without one` (pitch-stage → ADR 0006),
`below −2 V` (pitch-stage → ADR 0006),
`band-limit at both ends, around 500 Hz` (carrier → ADR 0003),
`across the feedback resistor` (pitch-stage → ADR 0006),
`the DAC8568's full-scale output is its supply` (ADR 0005 → ADR 0004),
`programmed ramp` (power-entry → ADR 0005),
`with LT1641-1 latching off on a fault` (power-entry → bom.csv),
`that reason is gone now the register is back on the cluster board`
(cluster-boards → bom.csv),
`the loom is broken` / `one bit is stuck` (cluster-boards → carrier),
`better drive over a 14 in chain` (ADR 0001 → bom.csv).

The quotes are, with one exception, honest. The staleness is in the unquoted
prose.
