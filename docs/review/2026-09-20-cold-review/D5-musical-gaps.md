# D5 — Musical gaps

*What this instrument needs, as something to play, that the design does not yet
have. Read as a player and an instrument designer, not as a circuit reviewer.*

Scope respected throughout: one tethered rack instrument, one player, bonded
body, CV only, USB MIDI is a fixture. Nothing below argues for a product,
a battery, a speaker or a stage.

---

## The short version

The **electrical** design of this instrument is unusually player-aware. The
**musical** design is almost entirely absent, and it is absent in a specific
way: every document describes a *channel* and none describes a *note*. There is
no written answer anywhere to "how does a note start", "how does a note end",
"what happens between two fingerings", "what is the pitch of a fingering", or
"what does the player touch with their mouth". Those are the instrument.

Almost all of it is firmware and decisions. Two items are hardware and both are
cheap **if taken before M3 locks the layout** — which is much earlier than the
bond at M6/M8, because a switch that does not exist in the plate DXF never
exists at all.

| # | Finding | Kind | Gate | Verdict |
|---|---|---|---|---|
| 1 | Articulation and the note engine are undefined | Firmware + decision | F1/F2 | **ADD** |
| 2 | The mouthpiece is not designed, specified or in the BOM | Hardware + decision | **M3/M4** | **ADD** |
| 3 | Circular breathing has no dropout tolerance, and auto-zero can fight it | Firmware + decision | F2, E2 | **ADD** |
| 4 | The fingering table has no pitch model — decide it before MIDI defines it | Decision | F1 | **ADD** |
| 5 | Spare shift bits are not spare switches; octave/hold/preset keys are pre-plate | Hardware + decision | **M3** | **ADD** |
| 6 | Track F has no pitch-expression milestone — no glide, bend range, vibrato, transpose | Firmware | F-track | **ADD** |
| 7 | Nothing names a gate, and nothing retriggers on a slurred note change | Firmware + labelling | F4 | **ADD** |
| 8 | No tuning ritual: no reference pitch, no defined idle pitch, no note/cents readout | Firmware | F7 | **ADD** |
| 9 | Register changes mid-slur are an unexamined layout requirement | Decision at M2 | **M3** | **ADD** |
| 10 | Shaped breath is not a routable source, only raw breath is | Firmware | F4 | **CONSIDER** |
| 11 | Preset recall has no mechanism from the instrument itself | Firmware (+ #5) | F8 | **CONSIDER** |
| 12 | No embouchure axis — the one woodwind control with no analogue here | Hardware | **M7** | **CONSIDER** (wires only) |
| 13 | Side strips have no assigned job, and the one the player needs is headroom | Firmware | F9 | **CONSIDER** |
| 14 | Continuous key expression / half-holing | Hardware | — | **DECLINE** |

---

## 1. Articulation is undefined. Nothing in the repository says how a note starts, ends, or survives a fingering change.

**ADD.** Firmware and decisions. No hardware. This is the single largest musical
gap in the project and it is entirely free.

Search the ADRs and the roadmap for the note engine and you find three
fragments: "breath threshold and note gating" (F2), "fire immediately on press,
filter only the release" (latency budget), and R52's correction that the release
filter belongs on the *note decision* rather than on each key. That last one is
excellent and is the only place anyone has thought about phrasing. What is
missing is everything around it:

- **Tonguing.** On a closed, dead-ended tube the tongue does not interrupt a
  flow — there is no flow in the sensor branch by design (ADR 0003). What the
  sensor sees from a tongue stroke is a small, fast pressure perturbation from
  oral-cavity volume and embouchure change, not the clean flow interruption an
  EWI's bleed hole produces. The closed tube is the right call for this player
  (it is what makes the circular breathing work, and it was called by the player
  not by analysis) — but it means **the articulation detector has to be built
  for a shallow, fast dip, not for a return to zero.** That is a firmware design
  problem nobody has stated yet. Concretely: a fast-tracking envelope follower
  and a slow one, with a re-articulation fired on a *relative* dip (e.g. 15–25 %
  below the slow follower within ~20 ms) rather than on an absolute threshold
  crossing. Make the depth and window player-adjustable and visible in the F6
  telemetry, because they will be tuned by playing, not by calculation.
- **Transient fingerings.** Fingerings here are combinational across 15 keys and
  fingers do not move simultaneously. Every legato interval passes through one
  or more intermediate key sets that are either a *different valid note* or not
  in the table at all. Without a rule, a C-to-G slur emits a spurious note in
  between — at 1 V/oct into a VCO that is plainly audible. Rules needed, all
  cheap: hold the last valid note through an unmapped set; require the set to be
  stable for a short settling window before committing a *new* note; and never
  let an unmapped set produce silence or a default.
- **Note-off.** Unstated. Does the note end when breath crosses down through
  threshold, and does the pitch CV move? See #8 — it must not.

**Player gains:** the difference between an instrument that phrases and one that
stutters between notes. This is what "plays like an instrument" actually means.

**Cost:** a day or two of firmware inside F1/F2, plus the willingness to make it
all adjustable and tune it by ear over weeks. Zero hardware.

**Pre-bond?** No — but it should be designed before E5, because USB MIDI into a
DAW is the only place it can be tuned before the analog hardware exists, and
that is exactly the job E5 was created for.

---

## 2. The mouthpiece does not exist anywhere in the design.

**ADD.** Hardware and a decision. **Must be settled before M4 CAD and M3 layout
lock**, because the inlet geometry, its angle and its mounting are cut into the
laminated stack.

The BOM has a tube, a trap, a PTFE plug and two sensors. It has **no
mouthpiece**. ADR 0009 allocates "mouthpiece / breath inlet (short) — 40 mm" of
length and says nothing else. E2's acceptance criterion says "a human plays it
for 20 minutes through a real mouthpiece" — a part that has never been chosen.

This is the only part of the instrument the player's *mouth* touches, and it
sets four things no other decision can reach:

- **Embouchure and the vent path.** Air leaves around the corners of the mouth
  (ADR 0003) — that is the mechanism the closed tube depends on and the
  mechanism circular breathing depends on. Its geometry is a property of the
  mouthpiece, not of the tube.
- **Presentation angle and hang.** The instrument hangs from a U-bolt in the
  inter-hand gap and is 457 mm long. Where the mouthpiece points, and how far it
  stands proud of the body, decides whether the player's neck is straight or
  craned for the entire session. This interacts directly with the U-bolt
  position that ADR 0009 has already fixed, and neither document mentions the
  other.
- **Hygiene, in a body that is bonded shut.** A removable, washable mouthpiece is
  the only cleanable interface this instrument will ever have. It is also the
  natural place to make the tube's first section replaceable.
- **Tryability.** Bite tip, tip opening, length, material and angle are all
  matters of taste that are cheap to iterate at M2 with a mock body and
  impossible to iterate afterwards.

**Recommendation:** make it a removable part on a standard interface — a sax or
clarinet mouthpiece body, or a printed/turned stub sized to accept a silicone
bite tip — retained by a fitting bonded into the top oak, with the silicone tube
terminating at it. Add BOM lines for the mouthpiece, its retainer and a spare
bite tip. Try three variants at M2, on the strap, standing and sitting, before
M3.

**Player gains:** comfort over a two-hour session, a reliable vent for circular
breathing, and a part that can be replaced when it wears or gets unpleasant.

**Cost:** an afternoon of decisions, a small fitting in CAD, a few tens of
pounds of parts. Very small next to being wrong about it permanently.

---

## 3. Circular breathing is named once and supported nowhere.

**ADD.** Firmware, plus one free change to an existing test.

The closed tube is the right architecture for a circular breather and ADR 0003
says so. But nothing downstream of the sensor knows the technique exists, and
two decided behaviours are actively hostile to it:

- **Note-off on a dropout.** The catch-breath is a brief dip while the cheeks
  hand over to the lungs. Depending on the player and the tempo it can go deep,
  and if the note gate is a bare threshold with hysteresis, the phrase ends in
  the middle. Fix: a **breath-dropout hold window** — once a note is sounding,
  sub-threshold breath does not release it for an adjustable 50–200 ms, and the
  breath CV can optionally be told to hold or decay slowly rather than follow
  the dip. Two parameters, one comparator, enormous musical value for this
  specific player.
- **Auto-zero chasing the dip.** ADR 0006 decays the ambient zero toward the
  current reading "whenever breath has been sub-threshold for about 2 seconds".
  2 s is probably long enough to be safe, but the interlock should be stated
  properly: **auto-zero only when no note has been active recently**, not merely
  when the instantaneous reading is low. Otherwise a slow passage of long
  catch-breaths walks the floor under the player. One extra condition.

Two things in the design happen to *help* and are worth knowing: the ≤1 mL trap
plus the PTFE restrictor give the pneumatic path a gentle first-order lag that
smooths the handover, and the panel offset knob lets the player lift the floor so
the dip does not reach zero at the VCA.

**Free change:** E2's acceptance test already says "a human plays it for 20
minutes through a real mouthpiece". Add: *including circular breathing*, with
the acceptance criterion "no note drop and no visible zero walk at the
handover". The restrictor is sized at E2 and its size changes how the dip reads,
so it should be sized against the technique that will actually be used.

**Pre-bond?** The E2 test is; the firmware is not.

---

## 4. The fingering table has no pitch model, and USB MIDI is about to choose one for you.

**ADD.** A decision, taken now, at zero cost. Expensive to reverse once the NVS
schema and the web editor exist.

ADR 0010 says the fingering table lives in NVS as data. It never says what an
entry *contains*. The default gravity here is strong and wrong: E5 is USB MIDI,
the natural entry is a MIDI note number, and the moment that is written the
instrument is locked to 12-EDT forever — on a machine whose output is a
continuous voltage and whose whole point is that it is not a MIDI device.

Decide instead that a fingering entry carries:

- **A pitch as a scale-degree index into a separate tuning table**, or as cents
  from a reference — not a MIDI note number. Twelve-tone equal temperament then
  becomes one tuning table among several, and just intonation, meantone,
  19-EDO and stretched tunings cost nothing.
- **A per-entry cents offset.** This is what makes *alternate fingerings* real:
  two fingerings for the same nominal pitch that differ by a few cents, the way
  they do on an acoustic instrument, chosen for the passage.
- **An optional per-entry "colour" value**, routed like any other mod source. On
  a real woodwind alternate fingerings differ in timbre, not only in pitch.
  Here, one number per fingering going to a mod channel gives the same effect
  for free, and it is the cheapest genuinely woodwind-like feature available.
- **A flag for what the entry does when unmapped/transitional** — see #1.

**Player gains:** microtonality, temperaments, alternate fingerings with real
intonation and timbre differences, and a fingering system that can be *tuned*
rather than only remapped.

**Cost:** a schema decision and a slightly larger struct. Perhaps two extra
columns in the web editor at F5.

**Pre-bond?** No, but pre-**F1**, and explicitly before E5 gets to define the
data model by accident.

---

## 5. "14 spare chain bits" are not spare switches. Every physical input has to exist before M3.

**ADD.** Hardware, and a decision that expires at layout lock.

`config/key-layout.yaml` lists 14 spare shift-register bits and names exactly
the right candidates: "octave up/down, a mode or menu button, a hold/sustain
switch". The electrical spares are genuinely free. The *switches* are not: they
need plate cutouts, keycaps, positions in the DXF, and a body that was designed
around them. After M3 they are unbuildable, and after M6 the body is bonded.

Also note the BOM: **18 switches purchased for 18 keys** — zero spares — and 20
caps for 18 keys. If extra inputs are wanted, they are an order, not a
rummage.

The musical case for at least two extra inputs is strong:

- **Octave/transpose up-down**, independent of the fingering. Changing key for a
  tune without relearning fingerings is a basic requirement and the left thumb's
  four register keys are a *fingering* mechanism, not a transposition one.
- **Hold / sustain.** Freezes the current note so the player can breathe, change
  posture, or set up. On a CV instrument with an external envelope this is
  genuinely useful, and it is the single best practice aid for circular
  breathing.
- **Preset / mode**, so the phone is not required mid-session (#11).

**Recommendation:** at M2, mock up two to three extra switches and see whether
they earn their place. Whatever survives goes into the layout file with real
x/y by M3. Order six spare KS-33 and a pack of caps now — the parts cost
nothing and the option expires.

**Pre-bond?** **Yes, and earlier than bond — before M3.**

---

## 6. Track F has no pitch-expression milestone at all.

**ADD.** Firmware. A missing milestone, not a missing idea.

F1 is fingering, F2 breath, F3 output, F4 routing, F5 web, F6 telemetry, F7
display, F8 persistence, F9 matrix. Nothing owns **pitch as an expressive
channel**. ADR 0006 mentions portamento once, in passing, to say it "belongs in
firmware" — and then no milestone ever claims it. The result is that the most
characteristic gestures of wind playing have no home in the plan:

- **Portamento / glide**, with a time constant, and — the part that matters —
  **legato-only glide**: glide when breath sustains through a fingering change,
  jump when the note is re-articulated. That one conditional is the difference
  between expressive and gimmicky.
- **Bend range expressed in semitones**, not in volts or in raw IMU degrees, so
  a gesture means the same thing at every register. Optionally quantised to the
  current scale so a bend lands on a scale degree.
- **Vibrato.** Worth being honest: on this instrument vibrato comes from the
  diaphragm (breath amplitude) or from IMU roll. There is no lip vibrato and
  there will not be (#12). A firmware LFO gated by a thumb switch and depth-
  controlled by tilt is the cheap third option and is worth having — but the
  breath-amplitude route is the idiomatic one and it already works, provided the
  breath path is not over-smoothed (see F3's per-channel smoothing: do not put a
  long slew on breath by default or you will smooth away the player's vibrato).
- **Master tune and transpose**, stored per preset.

**Cost:** a milestone, call it F2b, and perhaps a week of firmware spread over
the playing-in period. No hardware, no analog consequences — ADR 0006 already
established that the pitch reconstruction filter is fast enough that glide is
not staircased, and R24/R25 already argued the rate question out.

---

## 7. Nothing in the design is a gate, and nothing retriggers a slurred note.

**ADD.** Firmware, plus a labelling decision on the panel.

ADR 0006 says, correctly, that a gate can be assigned to a mod channel and the
design should not be *limited* to one. That is the right architecture and the
wrong stopping point, because the sources list never actually includes the two
signals a rack needs:

- **A breath gate** — high while a note is sounding, with hysteresis sized from
  the measured LED-induced ADC step (ADR 0014 already asks for this
  measurement), and with the dropout hold from #3 applied to it.
- **A retrigger pulse on note change** — a few milliseconds, fired when the note
  changes *while the gate stays high*. Without it, every slurred note in a phrase
  shares one envelope, which means every phrase after the first note is shapeless
  unless the player re-articulates. With it, the player chooses: tongue for a new
  envelope, slur for a continuous one, and the rack hears the difference.

Both are pure firmware on an existing channel. The only real decision is
defaults: **mod 1 = gate, mod 2 = retrigger** is a sensible shipping state, with
mods 3–4 free for IMU/colour, and the write-on strip on the panel reflecting it.

**Player gains:** articulation reaches the rack. Right now only amplitude does.

---

## 8. There is no way to tune, and no stated behaviour for pitch between notes.

**ADD.** Firmware, small, high value per unit of effort. Setup workflow.

ADR 0006 does a great deal of work to make pitch *accurate* — real VCO, real
load, multi-point NVS table, per-load scale presets. All of that is about the
bench. Nothing is about the ninety seconds between opening the case and playing:

- **A tuning mode** that parks pitch at a known note (A, or the current preset's
  reference) and holds it, with no breath needed, so the VCO can be trimmed to
  the instrument. Every session on a CV instrument starts this way. It is about
  twenty lines and it removes a recurring annoyance forever.
- **Defined idle pitch behaviour.** Unstated today. It must **hold the last
  note** between notes — if pitch falls to a rest value, every envelope release
  tail glissandos, which is the classic beginner's bug in a CV wind controller.
  Write it down.
- **Note name, octave and cents on the display**, plus which scale preset and
  which per-load pitch scale factor ("one VCO" / "two multed") is in force. The
  per-load preset is a lovely idea from ADR 0006 that will silently mistune the
  instrument if the player cannot see which one is selected.

The rest of "case to playing" is already handled well and unusually thoughtfully
— UNCALIBRATED as an unmissable state, stuck-key flagging, alarm states that
cannot be configured away, blank-at-boot, the DAC watchdog that parks a droning
CV. Add a one-line **ready** state to that set so the player can tell the
difference between "self-check passed" and "nothing has run yet".

---

## 9. How the player changes register mid-slur is an unasked layout question.

**ADD.** A decision at M2, gated by M3. No new hardware if taken in time.

The left thumb gets four keys on an arc, marked `note` on the assumption they
are register keys, with "confirm at M2" against them. The unexamined part is not
how many keys there are — it is **how fast the thumb can get between them
without disturbing the grip**. A register change on a woodwind happens *inside*
a slur, at speed, while the thumb is also sandwiching the body.

Two concrete requirements to carry into M2, both of which change the geometry:

- **Bridged positions must be rollable.** The 2021 firmware used bridged
  positions across a four-octave span. Bridging means pressing two adjacent
  keys at once, which on an arc means rolling the tip across a shared edge — so
  adjacent-key spacing and whether they share a recess (ADR 0010 raises exactly
  this and leaves it open) is a *musical* question, not a comfort one.
  Individual recesses locate better; a shared recess bridges better. That
  tension should be resolved by playing a scale across the break, not by feel at
  rest.
- **Test it with the strap on, standing, on a passage that crosses registers**,
  not by pressing keys at a bench. This is one line added to M2's exit criteria.

Also worth deciding at M2: whether four register keys is actually the right
answer, or whether three plus bridging (the 2021 arrangement) leaves the fourth
position free for hold or transpose (#5).

---

## 10. The shaped breath the firmware computes never leaves the instrument.

**CONSIDER.** Firmware, small. Worth doing once there is something to listen to.

ADR 0003 is honest that curve shaping is "genuinely lost" on the analog breath
output, and argues that shaping belongs to the rack. In a modular context that
is defensible — but it assumes the rack owns a transfer-function module, and it
means the `breath_gamma` that the 2021 instrument used to *feel* like an
instrument now only affects MIDI, the display and mod channels.

The cheap recovery: make **shaped breath** an explicitly named mod source,
distinct from raw breath — the same sample stream with the player's gamma,
threshold floor and slew applied. Patch the analog jack when you want the
cleanest, fastest, unstepped signal; patch the shaped mod channel when you want
the feel. Costs one of four mod channels and a line in the source list.

**Honest caveat:** a mod channel is a 4 kHz zero-order hold into a ~2 kHz filter,
which is precisely the staircase-into-a-VCA artefact the analog path exists to
avoid. It may be perfectly fine and it may zipper. Decide it with E10 on the
bench and a VCA, not from here. That is why this is CONSIDER and not ADD.

Related and free: R42 already specifies two taps off one sample stream — raw for
the gate, decimated for mod/MIDI/display. That is exactly what this needs, and
its stated reason (12 bits biting at the bottom of a gamma curve) is a musical
reason, so make sure it survives into F2.

---

## 11. Presets exist in the roadmap but there is no way to change one without a phone.

**CONSIDER.** Firmware, plus possibly one switch from #5.

F8 says "Config and calibration in NVS; presets". Nothing says how a preset is
selected. Configuration lives on a phone by a good decision (ADR 0012), and
live editing while playing is expected to work — but joining a SoftAP to switch
from one patch's routing to the next patch's routing is not a thing anyone will
do between tunes.

Minimum viable: **four presets, selected from the instrument**, showing their
name on the AMOLED. The mechanism can be a held control-switch combination on
the right thumb, or one of the extra inputs from #5. A preset should carry the
routing matrix, breath curve and threshold, bend range, tuning table and the
per-load pitch scale factor — i.e. everything that changes when the patch
changes.

If #5 is declined, this becomes a key-combination, which ADR 0010's own
commentary rightly calls worse than a dedicated input. That coupling is the
reason to decide #5 deliberately rather than by default.

---

## 12. There is no embouchure axis. That is the one thing a real woodwind has that has no analogue here.

**CONSIDER** — the two spare conductors and a footprint, not the sensor.
Hardware, pre-bond.

Taking the question seriously: against an acoustic woodwind this design gives up
three things.

- **Continuous key position (half-holing, shading).** Accepted and correctly
  closed out in ADR 0002 — the switches are bought, they are binary, and
  expression moves to breath and the IMU. See #14.
- **Alternate fingerings for colour and intonation.** *Recoverable in firmware
  for free* — that is finding #4, and it is the best value in this document.
- **Embouchure — lip pressure and bite.** Genuinely absent, and the only axis
  here with no software substitute. On an EWI or a WX this is a bite sensor,
  and it is how those instruments get lip vibrato, fine bend and a timbral hand
  that is independent of both breath and fingers. Here the equivalent gesture
  requires the right thumb to leave its rest and the whole instrument to move,
  which is a different and much larger gesture.

**Proportionality is against building it.** A force sensor in a mouthpiece that
does not yet exist (#2), wired the length of a body whose whole analog topology
was rearranged specifically to delete long internal runs (ADR 0003), for a
player whose previous instrument had no such axis and who already has two IMU
axes plus acceleration — that is a month of work for a gesture that may never be
used. **DECLINE the sensor.**

**But the option is worth about an hour to preserve**, because the body bonds
shut: run **two spare conductors from the mouthpiece region to the bottom
board** in the existing side channel, leave a pad pair and the MCP3202's
**already-spare second ADC channel** unassigned, and note it. GPIO 3 and 4 are
also free on the real-time board and both are ADC1 channels (ADR 0007). If, a
year in, the instrument wants a bite axis, it is a mouthpiece part and a firmware
source rather than an unbuildable idea. **This is the pre-bond half, and it is
the only part of this finding worth doing now.**

---

## 13. The side strips have no job, and the job they should take is not decoration.

**CONSIDER.** Firmware. Genuinely small.

ADR 0014 leaves "what the side strips actually do" open and suggests they take
the matrix's treatment — generic and assignable. Agreed, with one addition from
the playing position: the strips are the only display the player sees
**peripherally, without looking at anything**. The matrix at the tail needs a
downward glance; the AMOLED at the top needs a steeper one.

So the strips' default assignment should be the thing you must not have to look
for: **headroom and state** — where breath sits against its usable top (so the
player knows when they are about to run out of range, which is how a wind
controller's dynamics get squashed without anyone noticing), plus an unmissable
colour for config-mode-active and for alarm. Breath level as a bar is the
obvious default and is fine; breath *against its ceiling* is more useful and
costs the same.

---

## 14. Continuous key expression.

**DECLINE.** Correctly closed already.

Hall-effect switches would give analog travel with the same caps and would open
half-holing, per-key pressure and continuous key expression — a genuinely
different instrument. ADR 0002 rules it out on the grounds that the switches are
bought and the decision is settled, and that is the right call for a one-off. It
is worth recording that the *consequence* is real, though: with binary keys,
breath and the IMU carry the entire expressive load, which is precisely why
findings #1, #3, #6 and #7 are worth as much as they are. The expressive budget
is thinner here than on an acoustic instrument, so the few axes that exist have
to be developed rather than merely wired.

---

## Where the design already serves the player well

This should be said plainly, because it is most of the project and it is better
than the gaps above imply.

- **Breath gets the best channel in the instrument.** Analog end to end, never
  digitised on the way out, its own precision reference because the part is
  ratiometric, its own sense return so the light show cannot amplitude-modulate
  it, and panel gain and offset knobs in the analog path with zero latency. For
  an instrument whose primary expression is breath, that is the right place to
  have spent the effort, and the gain-then-offset ordering is the correct one.
- **The closed tube is right for this player**, and the ADR's insistence on
  recording *why* it was kept against a confident review finding is exactly the
  behaviour that keeps a one-off instrument coherent.
- **Continuous auto-zero** is the fix for the failure that would otherwise be
  blamed on the player's diaphragm for years.
- **Asymmetric debounce, and R52's correction that the release filter belongs on
  the note decision rather than on the key** — that is a genuinely
  woodwind-specific insight and most controller firmware gets it wrong.
- **Pitch calibration done properly**: multi-point rather than two-point, anchors
  inside the used range, verified against a real VCO under the real load, with a
  named per-load scale preset. This is the difference between an instrument and
  a thing that is slightly out of tune, and the roadmap says so in those words.
- **Capture-on-press IMU gating with a deadband** is the right mechanism for an
  instrument that hangs from a strap and has no fixed zero, and the stillness-
  gated bias estimator is a better answer than either of the alternatives it was
  argued against.
- **The matrix as a two-dimensional gesture display in the player's downward
  glance**, with the deadband drawn on the grid — that is a real instrument-
  design idea, not a use for spare LEDs.
- **Alarm states that cannot be configured away**, UNCALIBRATED as an unmissable
  state, stuck-key flagging, and a watchdog that parks a droning CV: the three
  silent failures that would otherwise be blamed on the player are all made
  loud.
- **Layout and fingering as data, with M2/M3 ergonomic iteration in cheap
  material first**, and live telemetry pulled forward so layout work is observed
  rather than inferred. That is the right shape for an instrument whose
  fingering system has to be discovered by playing it.
- **Mechanical switches replacing capacitive pads** near a wet mouth and wet
  hands — definite actuation is worth more musically than any amount of
  sensitivity.

---

## What must be decided before the body closes

Everything else in this document is firmware or data and can be changed for
years. These cannot:

| Item | Real deadline | Why |
|---|---|---|
| Mouthpiece: part, angle, retention, removability (#2) | **M3 / M4** | Inlet geometry is laminated into the stack; hang angle interacts with the fixed U-bolt |
| Extra switches — octave, hold, preset (#5) | **M3** | Cutouts live in the plate DXF; switches are not in the BOM as spares |
| Register-key arc, spacing and recess sharing (#9) | **M3** | Same plate; bridging is a geometry property |
| Two spare conductors to the mouthpiece region (#12) | **M7 / M8** | Last chance to leave an expression axis possible |
| Circular breathing in the E2 acceptance test (#3) | **E2** | Sizes the PTFE restrictor, which is sealed in |

Everything above is small. The largest single item is the mouthpiece, and it is
small only because it has not been started.
