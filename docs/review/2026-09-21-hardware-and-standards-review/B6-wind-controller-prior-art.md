# B6 — Wind controller prior art: breath sensing and musical behaviour

**Reviewer stance:** cold comparative. I did not read `docs/review/**` or
`docs/research/**`. Everything here is derived from the in-scope repo files plus
published sources found this session. Where I agree with work that may already
exist elsewhere in the repo, that agreement is independent.

**Scope read:** `docs/decisions/0003-breath-sensing-path.md`,
`hardware/controller/carrier.md` §2, `hardware/module/breath-receive-stage.md`,
`hardware/module/breath-output-stage.md`, `hardware/bom.csv`,
`docs/decisions/0006-cv-channel-allocation.md`,
`docs/decisions/0010-key-layout-as-data.md`, `config/key-layout.yaml`.
Also read for context: `docs/reference/latency-budget.md`,
`docs/decisions/0014-lighting.md` §LED/breath loop, `firmware/README.md`,
`ROADMAP.md`.

**Findings are indexed by design element.** Rank: Showstopper / High / Medium /
Low / Note.

---

## 0. The published corpus I was able to reach

Network was heavily restricted. Reachable: `raw.githubusercontent.com`, the
GitHub code-search API, and the search index (which returned extracted text for
pages I could not fetch directly).

**Primary sources actually read:**

| Source | What it gave |
|---|---|
| `[web] https://github.com/berglundinst/NuEVI` (files read via `raw.githubusercontent.com/berglundinst/NuEVI/master/NuEVI/settings.h` and GitHub code search) | The most complete open-source wind controller. Sensor MP3V5004GP (0–3.92 kPa), 12-bit ADC, `BREATH_THR_FACTORY 1400`, `BREATH_MAX_FACTORY 4000`, `BREATHCURVE_FACTORY 4` of 13 curves, `BREATH_CC_FACTORY 2`, `DEGLITCH_FACTORY 20 // 0 - OFF, 5 to 70 ms`, `VEL_SMP_DL_FACTORY 20 // 0 to 30`, `filterFreq = 30.0` Hz one-pole on breath |
| `[web] https://raw.githubusercontent.com/Trasselfrisyr/MiniWI/master/MiniWI/MiniWI.ino` | Minimal wind controller. MPX5010GP (0–10 kPa), `ON_Thr 40`, `breath_max 300`, `ON_Delay 20` ms ("wait for tounging peak"), three-state NOTE_OFF / RISE_WAIT / NOTE_ON machine, `CC_INTERVAL 15` ms, breath on CC#2, exponential smoothing `0.8/0.2` |
| `[web] https://github.com/Trasselfrisyr/MiniWI` (sibling sketches `T.WI`, `TeensieWI`, `MiniVI-cap`, `MiniWI-lite`, …) | Same state machine and the same `ON_Delay 20` in every variant — this is the field's standard note-on rule, not one author's quirk |
| `[web] https://github.com/habuenav/Breath` | A library whose *only* job is blow detection for EWI projects, on MPS20N0040D + HX710B |
| `[web] https://support.akaipro.com/en/support/solutions/articles/69000849456-akai-pro-ewi-5000-calibrating-the-ewi-5000` | EWI5000 exposes **three** breath parameters: sensitivity (zero/threshold), dynamic range (span), **rate of change** |
| `[web] https://www.manualslib.com/manual/1595204/Akai-Ewi5000.html?page=14` (text via search index; the page itself is proxy-blocked) | EWI5000 "Note Delay (note keys)": *"preset to accommodate rapid changes in fingerings, but you may occasionally produce unexpected sounds"*; user-settable 00–99 |
| `[web] https://www.addacsystem.com/en/news/introducing-addac310-pressure-to-cv` and `[web] https://sonicstate.com/news/2024/07/26/pressure-to-cv-eurorack-module` | ADDAC310 Pressure-to-CV: closest published analogue to this project's module. **Dead-ended air path by design** ("doesn't provide any way for incoming air to escape"), per channel **Response (exponential↔linear↔logarithmic)**, **Time (attack/decay)**, **Offset**, **Gain**, plus a **Gate output with its own threshold** and a Hold |
| `[web] https://modulargrid.net/e/pulplogic-bc-breath-control` | Pulp Logic BC — the model ADR 0003 names. Operates on **blow *and* draw** (pressure and vacuum) |
| `[web] https://www.soundonsound.com/reviews/yamaha-wx5` | WX5: 16 keys including 2 assignable high keys and **4 octave keys under the left thumb**; four fingering modes; right-thumb sprung pitch-bend rocker |
| `[web] https://www.sweetwater.com/store/detail/EWI5000--akai-professional-ewi-5000-electronic-wind-instrument-midi-controller` | EWI5000: **13 note touch sensors**, 8 octave rollers (6 mobile + 2 fixed), 2 pitch-bend plates, 2 ground plates |
| `[web] https://aodyo.com/sylphyo-user-guide-2/` | Sylphyo: internal sounds "not more than a few milliseconds"; over MIDI **5–20 ms** gesture-to-sound |
| `[web] https://dynasample.com/downloads/Aerophone_setup_for_use_with_the_XPression.pdf` | Roland Aerophone AE-10: breath CC begins **6–15 ms** after note-on, ~10 ms jitter |
| `[web] https://www.manualslib.com/manual/207345/Akai-Ewi-USB.html?page=5` (text via search index) | EWI USB: **"moisture release valve at the very bottom"**; removable, washable mouthpiece |
| `[web] https://www.printables.com/model/647683-yamaha-wx7-wx11-wx5-air-inlet-elbow-spare-part` (text via search index; page proxy-blocked) | The WX7/WX11/WX5 **air inlet elbow** exists as a replaceable spare part, and its job is *"to prevent moisture from reaching the breath sensor, as condensation from exhaled air can contaminate the sensor"* |
| `[web] https://pubmed.ncbi.nlm.nih.gov/19796415/` / `[web] https://pmc.ncbi.nlm.nih.gov/articles/PMC4001942/` | Maximal expiratory mouth pressure, healthy adults: male 192 ± 42 cmH₂O, female 111 ± 25 cmH₂O |
| `[web] https://www.researchgate.net/publication/233620195_Blowing_Pressures_in_Bassoon_Clarinet_Oboe_and_Saxophone` and `[web] https://euphonics.org/11-3-reed-instruments/` | Acoustic single reeds: **2–3 kPa soft, 4–4.5 kPa loud**; clarinet low register 2.5–3.9 kPa |
| `[web] https://components101.com/news/mpxv5004dp-pressure-sensor` | MPXV5004: 0–3.92 kPa ≈ **400 mm H₂O**, 1.0 V/kPa — the de-facto wind-controller range |
| `[web] https://octopart.com/mpx5010gp-nxp+semiconductors-70301692` | MPX5010GP: 0–10 kPa, 450 mV/kPa, 0.2–4.7 V |
| `[web] https://midi.org/community/midi-specifications/cc2-vs-cc11` | CC2 is the MIDI Breath Controller by definition; CC34 is its LSB |

**URLs that failed (all `EGRESS_BLOCKED` by the proxy unless noted):**
`https://www.patchmanmusic.com/WindControllerFAQ.html`,
`https://www.manualslib.com/…` (all pages),
`https://www.manualsdir.com/manuals/459731/akai-ewi5000.html?page=22`,
`https://cdn.inmusicbrands.com/akai/ewi-4000/ewi4000s_refmanual_revd_00.pdf…`,
`https://static.roland.com/assets/media/pdf/AE-30_Parameter_Guide_eng01_W.pdf`,
`https://www.tecontrol.se/files/MIDI%20BBC2%20Users%20manual.pdf`,
`https://www.acoustics.asn.au/journal/2000/2000_28_2_Fletcher.pdf`,
`https://www.nxp.com/docs/en/data-sheet/MP3V5004G.pdf`,
`https://www.nxp.com/docs/en/data-sheet/MPXV5004G.pdf`,
`http://gordophone.blogspot.com/2013/01/breath-sensing-101.html`,
`http://gordophone.blogspot.com/2013/01/breath-and-note-onoff-transitions.html`,
`https://en.wikipedia.org/wiki/Wind_controller`,
`https://www.printables.com/model/647683-…`,
`https://mybreathmymusic.com/wp-content/uploads/2016/05/Yamaha-WX5-Manual-English.pdf`,
`http://www.columbia.edu/~rtc/yamaha_wx5.pdf`,
`https://www.acoustics.asn.au/…`.
`https://web.archive.org/…` — refused by the fetch tool, not the proxy.

**One consequence for the repo:** `breath-receive-stage.md` quotes the WX5
manual — *"Wind Zero may change slightly when Wind Gain is adjusted, so you may
have to repeat"* — and I **could not verify that quotation**; every host
carrying the WX5 manual is blocked. The argument it supports (null the pedestal
ahead of the gain pot) is independently correct on its own arithmetic, so
nothing turns on it, but the citation is currently unverifiable from inside this
environment.

---

## 1. Element: the working pressure range (the "2.8 kPa" figure)

### 1.1 — High — **The 2.8 kPa working point has no source, and the repo
contradicts itself about it by a factor of 1.8×.**

Three documents carry two different numbers and cite each other in a circle:

- `[repo] docs/decisions/0003-breath-sensing-path.md:136` — *"Normal
  wind-controller playing sits around **0–5 kPa**."* No citation.
- `[repo] hardware/module/breath-receive-stage.md:265` — *"real playing tops out
  around **2.8 kPa** against the sensor's 6 kPa range"*, introduced as a
  correction to this page, with no source.
- `[repo] hardware/module/breath-output-stage.md` — *"Real playing only reaches
  about 2.8 kPa against the sensor's 6 kPa range **(ADR 0003)**"* — but ADR 0003
  does not contain the figure 2.8 kPa anywhere `[repo]` (grep: the only "2.8" in
  that file is `2.83 mL` of tube volume).
- `[repo] hardware/controller/carrier.md` §2 — `real play = 2.8 kPa …
  [2.8 kPa from breath-receive-stage.md]`.

So `breath-output-stage.md` attributes it to ADR 0003, ADR 0003 says something
else, and `carrier.md` attributes it to `breath-receive-stage.md`, which asserts
it without support. **Both the analog gain range (0.5–4×, "working point near
2.1×") and the ADC divider's headroom budget are sized off this unsourced
number.** Fix the provenance before E10, or the commissioning procedure is
calibrating to a guess.

### 1.2 — Note — **The field's published working points bracket 2.8 kPa, so the
number is plausible — but it is at the bottom of the bracket.**

Reconstructed from published firmware defaults:

| Design | Sensor | Note-on threshold | Full-expression point |
|---|---|---|---|
| NuEVI factory `[web] github.com/berglundinst/NuEVI` `NuEVI/settings.h` | MP3V5004GP, 0–3.92 kPa, 12-bit | `BREATH_THR 1400` → **≈0.7 kPa** `[calc]` | `BREATH_MAX 4000` → **≈3.9 kPa**, i.e. the sensor's own ceiling `[calc]` |
| MiniWI `[web] raw.githubusercontent.com/Trasselfrisyr/MiniWI/master/MiniWI/MiniWI.ino` | MPX5010GP, 0–10 kPa, 10-bit @5 V | `ON_Thr 40` → **≈0.15–0.2 kPa above rest** `[calc]` | `breath_max 300` → **≈2.9–3.0 kPa** `[calc]` |
| MPXV5004 / MP3V5004 family, the de-facto wind-controller part | 0–3.92 kPa = 400 mm H₂O `[web] components101.com/news/mpxv5004dp-pressure-sensor` | — | 3.92 kPa is chosen *as* the top of playing |

`[calc]` NuEVI: MP3V5004G is ratiometric, V_out = V_S×(0.2·P + 0.2); at a 3.3 V
Teensy rail that is 0.66 V offset and 0.66 V/kPa. 1400/4095 × 3.3 V = 1.128 V →
(1.128 − 0.66)/0.66 = **0.71 kPa**. 4000/4095 × 3.3 = 3.224 V → **3.88 kPa**.

`[calc]` MiniWI: MPX5010GP, 0.2 V offset (±0.1 V), 450 mV/kPa, 10-bit on a 5 V
reference = 4.883 mV/count. Rest sits at 20–41 counts. `ON_Thr 40` is therefore
**0–20 counts above rest = 0–0.22 kPa**; `breath_max 300` is 259–280 counts
above rest = 1.26–1.37 V = **2.8–3.0 kPa**.

Acoustic reference for sanity `[web] euphonics.org/11-3-reed-instruments/`:
single reeds run **2–3 kPa soft, 4–4.5 kPa loud**; clarinet low register
2.5–3.9 kPa `[web] researchgate.net/publication/233620195_Blowing_Pressures_in_Bassoon_Clarinet_Oboe_and_Saxophone`.

**Verdict: 2.8 kPa is real but low.** The field clusters at **2.9–3.9 kPa** for
"as loud as it goes". ADR 0003's own "0–5 kPa" is high; 2.8 kPa is at the floor.
The honest design range is **3–4 kPa**, and see 1.4 for why picking the low end
costs you.

### 1.3 — Medium — **±6 kPa is a defensible sensor choice, and the brief's
"±" is wrong: it is a unidirectional 0–6 kPa part.**

`[repo] 0003` states this explicitly — *"This is a unidirectional 0–6 kPa part,
so a reversed connection does not read backwards — it reads zero."* The DP
package is differential in *plumbing*, not in *sign*.

Against the field: 6 kPa sits between the two published families — 3.92 kPa
(MPXV5004/MP3V5004, the wind-controller default) and 10 kPa (MPX5010, MiniWI).
**6 kPa is the better of the two for this instrument specifically**, and the
reason is the closed tube:

- Published controllers bleed. The EWI has *"restricted airflow by design, which
  is why players often need to let air escape from the sides of their mouth"*
  `[web] https://www.saxontheweb.net/threads/ewi-usb-airflow.127244/`. A bleed
  turns effort into flow, which caps the pressure a given embouchure produces.
- This design has **no bleed at all** `[repo] 0003` ("The closed tube is correct,
  and why"). With zero flow, none of the player's effort is spent moving air, so
  the *same* embouchure produces a *higher* pressure than on an EWI. A 3.92 kPa
  part would be the wrong choice here; 6 kPa is right.
- Ceiling check `[calc]`: maximal expiratory mouth pressure in healthy adults is
  192 ± 42 cmH₂O male / 111 ± 25 cmH₂O female
  `[web] https://pmc.ncbi.nlm.nih.gov/articles/PMC4001942/` = **18.8 kPa and
  10.9 kPa**. So 6 kPa is 32–55 % of what a player can physically produce
  against an occlusion, and a dead-ended tube *is* an occlusion. It is not
  unreachable; it is one hard accent away.

**So it is not "wasting most of its range" — but it is not clipping-proof
either, and the design has no defined behaviour when the sensor saturates.**
Above 6 kPa the part pins at ~4.8 V and the jack stops moving; there is no soft
knee, no indication, and (because the CV path is analog) no firmware limiter.
See 1.4.

### 1.4 — High — **The output stage's gain range and the field's own maximum
pressure are incompatible: set the gain the way commissioning tells you to and
a loud player clips into the rail.**

`[repo] hardware/module/breath-receive-stage.md` §Commissioning step 2 says to
set panel GAIN so a hard blow (2.8 kPa) fills the output — *"which puts the
working point near 2.1×"*. `[repo] hardware/module/breath-output-stage.md`
confirms ≈2.13×.

`[calc]` The in-amp delivers −0.766 V/kPa × 2.1611 = **−1.655 V/kPa**. At 2.8 kPa
that is −4.63 V; ×2.157 at the output stage = +10.0 V. Now blow to the field's
own full-expression point:

| Pressure | Jack, at the commissioned 2.16× |
|---|---|
| 2.8 kPa (the repo's assumption) | 10.0 V |
| 3.0 kPa (MiniWI's `breath_max`) | 10.7 V |
| **3.23 kPa** | **11.5 V — the OPA2197 rail** |
| 3.9 kPa (NuEVI's factory `breath_max`) | 13.9 V, demanded; delivered 11.5 V |

**Everything above ≈3.2 kPa is lost**, and `breath-output-stage.md` itself says
what that sounds like: *"the clip is a rail clip with no soft region, so it will
sound like a wall rather than compression."* The commissioning procedure as
written produces an instrument that walls out on any accent above a mezzo-forte
that the published field would call normal.

This is not fatal — it is what the GAIN knob is for — but **the commissioning
text is wrong**. Step 2 should read: *set GAIN so that the loudest note you
actually play reaches the top of the range you want, then verify a deliberate
over-blow does not hit the rail.* And `breath-output-stage.md`'s headroom
section should state the pressure at which the rail is reached for any given
gain, not only the offset-plus-gain combination.

### 1.5 — Note — **Resolution is genuinely a non-issue; ADR 0003 is right.**

`[calc]` from `[repo] carrier.md` §2's own divider: rest 0.2 V → 149 counts;
2.8 kPa → 2.347 V → ×0.6 = 1.408 V → 1748 counts. Playable span **1599 counts of
4096**. Against 7-bit MIDI CC2 that is 12.5 ADC counts per MIDI step — more than
an order of magnitude of margin, and enough to apply a curve in firmware without
banding. NuEVI runs the same 12 bits `[web] github.com/berglundinst/NuEVI` and
nobody complains. Confirmed, independently.

---

## 2. Element: the mouthpiece-to-sensor path (400 mm tube, PTFE plug, ≤1 mL trap)

### 2.1 — Showstopper — **Every published wind controller provides a drain or a
replaceable wet part. This one provides neither, and the body cannot be opened.**

The field's position is unambiguous and is expressed in *hardware*, not in
spares:

- **Akai EWI USB/5000:** a **moisture release valve at the very bottom of the
  instrument** that the player wipes periodically, plus a mouthpiece that
  unscrews and goes in the sink
  `[web] https://www.manualslib.com/manual/207345/Akai-Ewi-USB.html?page=5`.
- **Yamaha WX5/WX7/WX11:** an **air inlet elbow** whose stated function is *"to
  prevent moisture from reaching the breath sensor, as condensation from exhaled
  air can contaminate the sensor"* — and which is common enough as a failure
  that there is a published 3D-printable replacement
  `[web] https://www.printables.com/model/647683-yamaha-wx7-wx11-wx5-air-inlet-elbow-spare-part`.
- **WX11 specifically:** *"if the soft plastic cap behind the mouthpiece is not
  making a proper seal, the circuit board's components can be exposed to
  contamination from the breath"*
  `[web] https://www.manualslib.com/manual/1100438/Yamaha-Wx11.html?page=18`.

This design's answer is *"Treat the sensor as a wear part. It is socketed or
otherwise replaceable, and the trap is clearable without disassembly. **Buy
two**"* `[repo] 0003`. **That is a spares strategy substituting for a plumbing
strategy, and the BOM already knows it does not close:**

> `SKT-BREATH … "ADR 0003 calls the sensor a wear part and buys two. The spare
> is only reachable if the first part comes out, and the body is bonded."`
> `[repo] hardware/bom.csv:77`

and

> `**SKT-BREATH only earns its place if the sensor is reachable.** See *Still
> open*.` `[repo] hardware/controller/carrier.md` §2

**The socket is a mitigation that the enclosure decision cancels.** Either the
sensor is reachable after bonding — in which case say through which face, and
put it in ADR 0009 — or the socket is decoration and the instrument's most
moisture-sensitive part is a single-use item. The field's verdict is that this
part *will* need attention; two shipping instruments built hardware specifically
to give it that attention.

**Worse: geometry puts the water exactly where the sensor is.** The mouthpiece
is at the top, the sensor at the bottom `[repo] 0003` §"Sensor placement", and
the instrument is played roughly vertically. Condensate on the tube walls runs
**downhill to the sensor**. The EWI's drain is at the bottom for the same
reason — it is where water goes. This design puts the transducer there instead.

### 2.2 — High — **The ≤1 mL trap has a computable capacity, no drain, and no
stated access mechanism.**

`[calc]`, with assumptions stated so they can be argued with:

- Tube 3 mm bore × 400 mm = **2.83 mL** `[repo] 0003` + trap 1 mL = 3.83 mL.
- Each note compresses the closed volume by ΔV/V = ΔP/P₀ = 2.8/101.3 = **2.76 %**
  → 0.106 mL of mouth-temperature saturated air drawn in per note.
- Saturated air at 37 °C holds 44 mg/L; at a 20 °C tube wall, 17.3 mg/L. The
  condensable difference is 26.7 mg/L `[from memory]`.
- 0.106 mL × 26.7 mg/L = **0.0028 mg of water per note**. At a dense 4 notes/s,
  that is 41 mg/h ≈ **0.041 mL/h**.

So **~24 hours of continuously dense playing to fill a 1 mL trap** from the
pumping mechanism alone, before counting diffusive transport (below), which is
probably the larger term. Call it *tens of hours of real playing* — i.e. **months,
not years** — and the trap has no drain, so it only ever fills.

`[repo] 0003` says *"Make it clearable without disassembly. Not a drain plumbed
through the body — just access."* **No access mechanism appears anywhere in the
in-scope documents.** `carrier.md` §2 draws the trap as a label on the P1 port
with no route to the outside. This is the same gap as 2.1 and should be closed
by the same decision.

### 2.3 — High — **The 400 mm tube does not keep vapour away from the die; it
delays it by under an hour.**

ADR 0003 is candid that *"vapour cannot be eliminated from a closed tube that is
breathed into"* `[repo] 0003`, but it does not quantify how quickly vapour
arrives, and the length of the tube reads as though it helps.

`[calc]` In a dead-ended tube with no bulk flow, water vapour moves by diffusion.
D(H₂O in air) ≈ 2.4 × 10⁻⁵ m²/s `[from memory]`. Characteristic time over
L = 0.4 m: t ≈ L²/2D = 0.16 / 4.8×10⁻⁵ = **3 300 s ≈ 56 minutes.**

Under an hour of playing, the air at the die is at mouth humidity. The porous
PTFE plug is by construction a *vapour* path (it has to be, or it would not be a
pneumatic restrictor), so it does not change this. NXP's own qualification —
*"NOT compatible with water or water vapors"*, with a gel die coat that swells
when wet `[repo] 0003`, which I could not verify directly because
`https://www.nxp.com/docs/en/data-sheet/MP3V5004G.pdf` and the MPXV4006 sheet are
both proxy-blocked — therefore applies from the first hour of every session, not
eventually.

**This is survivable — the whole published field uses the same sensor family and
the instruments last years — but it is survivable *because* those instruments
let you get at the wet parts.** See 2.1.

### 2.4 — Medium — **The PTFE plug is a consumable being specified as a
permanent part, and its failure mode is the one the design can least see.**

`MECH-PTFE` does two jobs — acoustic damping of the pipe mode, and liquid-water
barrier `[repo] hardware/bom.csv:52`, `[repo] 0003`. Hydrophobic porous PTFE
barriers in respiratory service are consumables: saliva carries mucin and salts
that dry on the membrane and progressively occlude it `[from memory]`.

The consequence is specific and nasty. The plug's pore size sets the acoustic
resistance, which sets the pneumatic time constant, which is **the one term in
the latency budget that is not measured**:

> `| **Pneumatic restrictor** | **? — sized at E2** | … the term most able to
> break it |` `[repo] docs/reference/latency-budget.md`

A slowly clogging plug therefore presents as **an instrument that gets
progressively less responsive over months**, with no step change and nothing to
blame. And ADR 0006's continuous auto-zero is explicitly at risk of eating the
evidence — it already names *"a partially blocked PTFE restrictor"* as one of
three failures it cannot distinguish from thermal drift `[repo] 0006`. The
logged-correction diagnostic ADR 0006 adds is the right instinct, but it catches
*zero* drift, not *bandwidth* loss. **A slowing restrictor moves no zero at all.**

Recommendation: add a bench check that is sensitive to the thing that actually
changes — the E2 tap-and-ring-down test `[repo] 0003` re-run annually, or a
firmware measurement of breath rise time on attacks, trended over sessions. The
instrument has a display and a web app; it can watch its own step response.

### 2.5 — Medium — **The reference port is open to a cavity that is itself
breathed into, so the PTFE plug protects one face of the die and nothing
protects the other.**

`[repo] 0003` plugs P1 with porous hydrophobic PTFE and leaves P2 *"open inside
the instrument, connected to nothing."* The cavity is described elsewhere in the
same repo as *"breathed into for hours behind 18 unsealed switch cutouts,
interior 10-20K above ambient"* `[repo] hardware/bom.csv:53` (`MECH-COAT`).

The gel die coat sits on **both** sides of the diaphragm. If the vapour objection
in 2.3 is real for P1, it is real for P2 — and P2 has no barrier at all, sits in
warm humid air, and cannot be given one without breaking the pressure reference
(ADR 0003's own "do not gasket the switch cutouts" rule). ADR 0003's escape hatch
is already written — *"the reference port gets vented to outside through its own
filtered stub first"* — and I would promote that from contingency to **the
default**, because it costs one stub at layout time and is unretrofittable
afterwards.

### 2.6 — Note — **Tube length: nobody else does this, and the delay is
nevertheless affordable.**

Published controllers put the transducer at or within a few centimetres of the
mouthpiece — the WX's sensor is immediately behind the inlet elbow
`[web] printables.com/model/647683-…`; NuEVI and MiniWI mount the sensor on the
main board with a short hose `[web] github.com/berglundinst/NuEVI`. A 400 mm run
is unique to this design.

It costs 1.17 ms `[repo] docs/reference/latency-budget.md` — see §5, where I
conclude it is comfortably affordable against published latencies. The routing
and thermal arguments for moving the sensor to the bottom `[repo] 0003` are
sound. **The cost is not latency; it is 2.1 and 2.2** — 400 mm of downhill
condensing surface terminating on the transducer.

---

## 3. Element: the reference port and the internal cavity

### 3.1 — Note — **Referencing to the instrument's interior is what the field
does. Confirmed, independently.**

Every published wind controller uses a *gauge* sensor whose reference is the air
inside the body (MP3V5004**GP**, MPX5010**GP**, MPXV5004**GP** — all gauge parts
`[web] github.com/berglundinst/NuEVI`, `[web] github.com/Trasselfrisyr/MiniWI`).
Their bodies vent through the moisture valve, the drain hole and every seam.
Leaving the DP's P2 stub unconnected *inside* the body reproduces exactly that
`[repo] 0003`. This decision is orthodox.

### 3.2 — Note — **The 5.2 kPa sealed-chamber figure is correct, and the
"cavity must leak" dependency is safe by three orders of magnitude.**

`[calc]` Sealed volume, isochoric: ΔP = P₀·ΔT/T₀ = 101.325 × 15 / 293.15 =
**5.18 kPa** — ADR 0003's 5.2 kPa is right, and it is 86 % of a 6 kPa full
scale, as stated.

The interesting question ADR 0003 asserts but does not quantify is whether the
cavity leaks *enough*. It does, overwhelmingly:

`[calc]` Envelope 457 × 57 × 38 mm = 990 mL `[repo] config/key-layout.yaml`;
take ~450 mL free after boards, plate and hardware. A 15 K rise over 15 minutes
must expel ΔV = 450 × 15/293 = **23 mL over 900 s = 25.6 µL/s**. Through a single
0.36 mm-diameter hole in a 2 mm wall, viscous (Hagen–Poiseuille, µ = 1.8×10⁻⁵
Pa·s):

```
Q = π d⁴ ΔP / (128 µ L) = 1.145e-8 · ΔP  [m³/s per Pa]
ΔP = 25.6e-9 / 1.145e-8 = 2.2 Pa
```

**~2 Pa.** Against a note-on threshold that will sit in the hundreds of pascals
(§4), that is 0.08 % of the working span, from *one* pinhole. The design has
eighteen switch cutouts and every glue seam. **The "it leaks fast enough"
assumption is not lucky — it has about three orders of margin**, and ADR 0003
should say so with a number, because the current text reads as an assertion
someone will later be tempted to "fix" with a gasket.

The masking rule for `MECH-COAT` `[repo] hardware/bom.csv:53` remains exactly
right and is the real risk: a *sealed* P2 gets the full 5.2 kPa and the
instrument looks dead. That is well handled.

### 3.3 — Low — **Key presses displace cavity air into the reference port. This
is unconsidered and it is measurable.**

Consequence of "P2 open to the cavity" that I could not find addressed anywhere
in scope. The output is P1 − P2, so anything that raises cavity pressure
*lowers* the breath reading.

`[calc]` A KS-33 stem entering the cavity: ~16–20 mm² cross-section × ~3.2 mm
travel = **51–64 mm³ = 0.051–0.064 mL** per key. Against ~450 mL free volume,
adiabatically (γ = 1.4):

```
ΔP ≈ γ·P₀·ΔV/V = 1.4 × 101 325 × 0.064/450 000 = 20 Pa per key
```

Four keys landing together on a fingering change: **~80 Pa**, i.e. **2.9 % of a
2.8 kPa span — about 290 mV at a 10 V jack**, transient, and *exactly
coincident with note changes*. It appears as a dip in breath CV on every
fingering transition.

Two things bound it downward: the plate cutout is not airtight around the switch
body, so some of the displaced volume vents locally to outside rather than into
the cavity; and the cavity's leak (3.2) drains it with some time constant. Both
are unknown. **This is a Low because it is probably much smaller in practice —
but it is a real, physical, key-correlated breath artefact, it has the same
symptom as the pull-up/reference-depression effect `carrier.md` §2 already
found ("the breath reading moves when I press keys"), and it is free to measure
at E4: scope the breath output while pressing keys with the mouthpiece at
rest.** If both mechanisms are present they add.

### 3.4 — Low — **Nothing defines what happens when the player draws (inhales).**

The tube is dead-ended, so a draw produces a *negative* differential trivially —
maximal inspiratory pressures in adults run to roughly −10 kPa `[web]
https://pmc.ncbi.nlm.nih.gov/articles/PMC4001942/` `[calc]`, and a casual suck
easily makes −2 kPa.

Two gaps:

1. **Expressively, the field treats draw as an axis, not an accident.** The Pulp
   Logic BC — the module ADR 0003 names as its model for panel gain and offset —
   *"operates on both blow and draw (pressure and vacuum)"*
   `[web] https://modulargrid.net/e/pulplogic-bc-breath-control`. This design's
   unidirectional part forecloses that permanently, and the in-amp's polarity and
   the `TRIM-BREATH-ZERO` 0→+1.0 V range `[repo] hardware/bom.csv:102` lock the
   foreclosure into the analog chain as well. That may be the right call — but it
   is an undocumented one.
2. **Mechanically, the reverse-pressure rating is not stated.** ADR 0003 covers a
   reversed *plumbing* connection ("it reads zero") but not a reversed
   *pressure*. The MPXV4006DP datasheet was unreachable
   (`https://www.nxp.com` proxy-blocked) so I cannot say whether −10 kPa on P1 is
   within rating. **Check this before E2**, because a dead-ended tube invites it
   and the instrument cannot be opened to replace the sensor.

---

## 4. Element: the breath response curve, and the note-on rule

### 4.1 — High — **The field universally applies a curve, and the module this
design most resembles puts that curve on the panel. Gain + offset alone is a
real musical limitation.**

Prior art, unanimous:

| Design | Curve provision |
|---|---|
| NuEVI | **13 selectable curves** (`curveM4…curveM1`, linear, `curveP1…curveP4`, `curveS1/S2`, `curveZ1/Z2`), factory default index 4 — i.e. *not* linear `[web] github.com/berglundinst/NuEVI` `NuEVI/settings.h`, `NuEVI/NuEVI.ino` |
| Akai EWI5000 | Breath **sensitivity**, **dynamic range** and **rate of change**, all user-set `[web] support.akaipro.com/en/support/solutions/articles/69000849456-akai-pro-ewi-5000-calibrating-the-ewi-5000` |
| Roland Aerophone AE-30 | Breath curve parameters in the parameter guide (page proxy-blocked, listed at `https://static.roland.com/assets/media/pdf/AE-30_Parameter_Guide_eng01_W.pdf`) |
| **ADDAC310 Pressure to CV** — a Eurorack breath-to-CV module, the closest published analogue to this project's module | Per channel: **Response** (exponential ↔ linear ↔ logarithmic on one knob), **Time** (attack/decay slew), **Offset**, **Gain**, plus a **Gate out with its own threshold** `[web] addacsystem.com/en/news/introducing-addac310-pressure-to-cv`, `[web] sonicstate.com/news/2024/07/26/pressure-to-cv-eurorack-module` |

ADR 0003 concedes the loss and argues the modular idiom covers it — *"sending
raw breath and shaping it with the rack's own tools is the idiom, and the panel
gain and offset knobs (ADR 0006) are exactly the Pulp Logic model"*
`[repo] 0003`. **Two problems with that defence:**

1. The nearest published module in the same category does **not** send raw
   breath. It ships a response knob, a slew, *and* a gate, in the same panel
   space this design gives to two knobs.
2. Shaping in the rack costs a wave-shaper or a function generator plus a patch
   cable per instrument, and the curve you most want — a gentle expansion at the
   bottom so pianissimo has room — is exactly the one that is fiddly to patch
   and trivial in firmware.

**Ranked High rather than Showstopper because the decision is coherent and
reversible in the module, which is not bonded shut.** But two concrete
recommendations:

- **The module has two spare op-amp halves** `[repo] hardware/bom.csv:13`
  ("Ten of twelve halves used … TWO SPARE"). A one-knob exp/log bender between
  the in-amp and the gain stage is two halves and three passives, and it is the
  single highest-value addition available to the breath channel.
- **Failing that, say in ADR 0003 that the breath jack is deliberately raw and
  that a shaper is expected in the rack**, so the omission is a documented
  interface contract rather than an absence.

### 4.2 — Note — **Firmware curve shaping on the digital copy is preserved, and
that is correctly identified.** `[repo] 0003`, `[repo] 0006`. Nothing to add
except that CC2 is the right destination: *"CC2 is by default assigned to Breath
Control"* `[web] https://midi.org/community/midi-specifications/cc2-vs-cc11`, and
both NuEVI (`BREATH_CC_FACTORY 2`) and MiniWI (`midiSend(…, 2, breathLevel)`)
default to it `[web] github.com/berglundinst/NuEVI`,
`[web] github.com/Trasselfrisyr/MiniWI`. If high resolution is ever wanted, CC34
is the defined LSB partner.

### 4.3 — High — **The note-on rule is a bare threshold read through a 564 Hz
filter. Every published design low-passes the gating signal an order of
magnitude harder, and adds a state machine.**

The published note-on rule is not "pressure > threshold". It is a three-state
machine with a deliberate wait:

```
NOTE_OFF → (pressure > ON_Thr) → RISE_WAIT → (ON_Delay elapsed) → NOTE_ON
#define ON_Delay 20   // wait for tounging peak
```
`[web] https://raw.githubusercontent.com/Trasselfrisyr/MiniWI/master/MiniWI/MiniWI.ino`
— and identically in `T.WI`, `TeensieWI`, `MiniVI-cap`, `MiniWI-lite`,
`MiniWI-cap`, `TeensieWI-FSR`, `TeensieWI-mod`
`[web] github.com/Trasselfrisyr/MiniWI`. NuEVI does the same with
`VEL_SMP_DL_FACTORY 20 // 0 to 30` `[web] github.com/berglundinst/NuEVI`
`NuEVI/settings.h`.

And the signal the threshold is compared against is heavily smoothed:

- NuEVI: `float filterFreq = 30.0;` — a **30 Hz** one-pole, applied to the
  breath reading *before* both the CC and the gate
  `[web] github.com/berglundinst/NuEVI` `NuEVI/NuEVI.ino`.
- MiniWI: `breathLevel = oldBreath*0.8 + breathLevel*0.2` at its loop rate,
  plus a 15 ms CC interval.

**This design compares against a signal band-limited at 564 Hz**
`[repo] hardware/controller/carrier.md` §2 (`C-AA-ADC`, f_c = 564 Hz), sampled at
4 kHz. `[calc]` That is **19× wider than NuEVI's gating bandwidth**. Breath is
turbulent; broadband noise in a 500 Hz band around a threshold is precisely the
chatter generator. Nothing in ADR 0003, ADR 0006, `carrier.md` or the firmware
README specifies:

- the threshold value,
- **hysteresis** (a separate, lower note-off threshold),
- a **slower filter for the gating signal specifically**,
- or a **rise-wait** before committing the note.

The one hysteresis mention in the repo is in `[repo] 0014` and is sized against
*LED-induced reference depression*, not against breath noise — a different and
much smaller disturbance.

**Recommendation, all firmware, all free:** run the gate off its own
~20–30 Hz-filtered copy of the breath value (the raw 4 kHz stream stays for the
mod channels and the analog jack, which do not care), add hysteresis, and adopt
the field's rise-wait. `firmware/README.md`'s asymmetric-debounce philosophy
(`instant press, filtered release`) is right for a *contact* and wrong for a
*breath threshold*, which has no mechanical edge to be fast about.

### 4.4 — High — **Fingering deglitch is absent, and it is the one thing a
shipping commercial instrument exposes to the player as a knob.**

`grep -rn -i "deglitch"` over the repo outside the review directories: **no
hits** `[repo]`. Debounce is thoroughly worked (`ROADMAP.md` E4, `firmware/README.md`,
`bom.csv` `R-KEY-SER`/`C-KEY`, ADR 0001 §"two consecutive agreeing samples"),
but that is **contact bounce on a single switch**. The field's problem is
different: on a fingering *change*, the fingers do not land and lift
simultaneously, so the instrument momentarily sees an intermediate fingering and
plays a wrong note.

- **NuEVI:** `#define DEGLITCH_FACTORY 20 // 0 - OFF, 5 to 70 ms in steps of 5`
  `[web] github.com/berglundinst/NuEVI` `NuEVI/settings.h`. Twenty milliseconds,
  by default, deliberately.
- **Akai EWI5000** ships it as a user control, "Note Delay (note keys)": *"The
  EWI5000's note key response is preset to accommodate rapid changes in
  fingerings, but you may occasionally produce unexpected sounds, depending on
  your playing style… You can play notes more smoothly with a larger Note Delay
  value, but it may prevent you from playing quickly."*
  `[web] https://www.manualslib.com/manual/1595204/Akai-Ewi5000.html?page=14`
  (text via search index; page proxy-blocked).

**This design's stated policy is the exact opposite.** `[repo]
docs/reference/latency-budget.md:103` — *"Debounce asymmetrically. Fire on the
leading edge and filter only the release."* `[repo] ADR 0001:194` — *"Asymmetric
debounce fires on the first closed sample."* Applied to a *fingering*, firing on
the first closed sample of a newly-landed key while a key from the old fingering
is still down produces the intermediate note at full velocity, immediately.

**Fifteen note keys spread over eleven top positions and four thumb positions
`[repo] config/key-layout.yaml` makes this worse, not better**, because more
fingers move per transition than on a 3-key-change EWI fingering.

Ranked High because it is the difference between an instrument that plays
cleanly and one that spits wrong notes in fast passages, and because the design
currently has no *place* for the decision — it belongs in ADR 0010 or a new
fingering ADR, alongside the fingering table that already lives in NVS.

### 4.5 — Medium — **There is no velocity strategy for the MIDI path.**

ADR 0003 lists USB MIDI as one of four consumers of the digital copy
`[repo] 0003` and ADR 0010 mentions a CC-driven modulation scheme, but nothing
says how a MIDI **note-on velocity** is derived. The field's answer is uniform
and specific: cross the threshold, **wait ~20 ms for the tonguing peak**, then
sample — `ON_Delay 20` in MiniWI and its seven siblings, `VEL_SMP_DL_FACTORY 20`
(range 0–30) plus `VEL_BIAS_FACTORY 0` (range 0–9) in NuEVI
`[web] github.com/Trasselfrisyr/MiniWI`, `[web] github.com/berglundinst/NuEVI`.

This is worth capturing because it **interacts with 4.3**: the rise-wait that
gives you a correct velocity is the same rise-wait that suppresses threshold
chatter. One mechanism, two benefits.

### 4.6 — Note — **Continuous auto-zero is ahead of the published field, and
the circular-breathing objection was already caught.**

EWI5000 and WX5 both zero by **manual adjustment** (EWI "breath sensitivity" set
just below the trigger point while not blowing
`[web] support.akaipro.com/…/69000849456-akai-pro-ewi-5000-calibrating-the-ewi-5000`;
WX5 "Wind Zero" and "Wind Gain" screws on the back). ADR 0006's
"sub-threshold **and** quiet" gate with a logged running correction
`[repo] 0006` is better than anything published I could find, and the
circular-breathing catch-breath hazard is explicitly handled there. Confirmed
independently; no finding.

---

## 5. Element: latency and the 5 ms budget

### 5.1 — Note — **The 5 ms target is comfortably ambitious against every
published figure. The 400 mm tube is affordable. Confirmed.**

| Instrument | Published latency |
|---|---|
| Aodyo Sylphyo, internal sounds | *"not more than a few milliseconds"* `[web] https://aodyo.com/sylphyo-user-guide-2/` |
| Aodyo Sylphyo, over MIDI | **5–20 ms** gesture-to-sound `[web] https://aodyo.com/sylphyo-user-guide-2/` |
| Roland Aerophone AE-10 | breath CC begins **6–15 ms** after note-on; ~10 ms jitter `[web] https://dynasample.com/downloads/Aerophone_setup_for_use_with_the_XPression.pdf` |
| NuEVI | breath CC update interval **6–15 ms** (≈65–165 Hz), plus 20 ms velocity delay and 20 ms deglitch `[web] github.com/berglundinst/NuEVI` |
| MiniWI | `CC_INTERVAL 15` ms, `ON_Delay 20` ms `[web] github.com/Trasselfrisyr/MiniWI` |
| MIDI wire, any of them | `[calc]` 3 bytes × 10 bits ÷ 31 250 baud = **0.96 ms** per message, before queueing |

This project: **~2.83 ms analog to the jack, ~2.9–3.1 ms for the digital copy**,
plus an unmeasured restrictor `[repo] docs/reference/latency-budget.md`. That is
**2× better than the best published figure and 5–7× better than the typical
one**, and the breath CV is *continuous* rather than updated at 65–165 Hz, which
is a larger qualitative difference than the latency number. The 1.17 ms tube is
41 % of the analog budget and still leaves the whole chain inside the best
published instrument's performance.

**Confirming ADR 0003's conclusion, and strengthening it:** the sensor-at-the-
bottom trade is not close. Even if the restrictor turns out to cost another
1.5 ms, this instrument is still faster than anything you could buy.

### 5.2 — Medium — **The 5 ms budget is a breath-CV budget, not a note-event
budget, and the project has never stated a note-event latency.**

This matters because 4.3, 4.4 and 4.5 each add tens of milliseconds by design,
not by accident. If the field's numbers are adopted — 20 ms rise-wait, 20 ms
fingering deglitch — the **musical** latency from "player decides" to "correct
note sounding at the right loudness" becomes ~23 ms, which is the field norm and
is fine, but it is nowhere in `latency-budget.md`.

The page currently books the key path at *"Debounce (press) | 0 — fire
immediately"* `[repo] docs/reference/latency-budget.md:97`. **Add a second
budget** — note-event latency — so that a future decision to add deglitch is a
budgeted change rather than a silent 20 ms regression against a table that says
zero. The two budgets are genuinely different and conflating them is how the
deglitch decision gets refused for the wrong reason.

---

## 6. Element: key layout — 18 switches in four clusters

### 6.1 — Note — **The count is in the field's range, and the four-key left
thumb is exactly the Yamaha WX5 arrangement.**

| | Finger keys | Thumb / register | Continuous controls | Total switch-like |
|---|---|---|---|---|
| Akai EWI5000 | **13** note touch sensors | 8 octave rollers (6 mobile + 2 fixed) | 2 pitch-bend plates, bite | 21+ `[web] sweetwater.com/store/detail/EWI5000--akai-professional-ewi-5000-electronic-wind-instrument-midi-controller` |
| Yamaha WX5 | ~12 (of 16 keys, incl. 2 assignable high keys) | **4 octave keys, left thumb** | lip/reed sensor, right-thumb sprung pitch rocker | 16 `[web] soundonsound.com/reviews/yamaha-wx5` |
| **Woody** | **11** (LH1–5, RH1–6) | **4** (LT1–4) | none binary; IMU + 3 RT control switches | **18** `[repo] config/key-layout.yaml` |

**11 finger keys is slightly leaner than both** (EWI 13, WX ~12) and well inside
the field. **Four left-thumb octave keys is the WX5 arrangement verbatim** —
ADR 0010's reasoning from saxophone thumb-hook ergonomics
`[repo] docs/decisions/0010-key-layout-as-data.md` lands on the same answer a
shipping Yamaha did, for the same reason. Nothing to change.

15 note keys against EWI's 13 also means the fingering table has *more*
expressive room than the commercial reference, not less — which matters because
ADR 0010 declines the EWI's 8 octave rollers and has to get the register range
out of 4 thumb keys.

### 6.2 — Medium — **Six keys in a strict longitudinal line under one hand has
no precedent. Treat the lateral offset as the expected outcome, not the
fallback.**

ADR 0010 commits to *"Eleven top keys … in one longitudinal line, flute-style.
No second column, no lateral side-key bank"*, then reasons correctly that a
six-key line at relaxed pitch spans 120 mm against an 80–90 mm four-finger span
and concludes the spacing must be non-uniform, with *"whether 6 in a strict line
works for the right hand, or whether the outermost one or two want a small
lateral offset"* left to M2 `[repo] docs/decisions/0010-key-layout-as-data.md`.

**The published field has already answered this**, and the answer is
consistently *lateral offset*:

- Saxophone: the left-hand pinky operates a **spatula table of four keys** on a
  separate axis; the right-hand pinky has two. Both are off the main line.
- Flute: the right-hand Eb pinky key and the B/Bb thumb keys are on separate
  axes; the trill keys are offset. "Flute-style single line" is a simplification
  of the flute.
- EWI: three side/auxiliary keys sit off the main run
  `[web] sweetwater.com/store/detail/EWI5000--…`.
- WX5: two assignable high keys plus trill keys in Sax B mode
  `[web] soundonsound.com/reviews/yamaha-wx5`.

**No published wind controller or acoustic woodwind puts six keys for one hand
on a single straight line.** ADR 0010's own arithmetic predicts why. The finding
is not that the layout is wrong — the ADR explicitly reserves the question for
M2 — but that the *prior* should be inverted: RH5/RH6 offset laterally is what
the field does, and a strict line is the experiment.

This is also cheap to be wrong about in the right direction: `key-layout.yaml`
carries explicit `x`/`y` per key with no pitch parameter
`[repo] config/key-layout.yaml`, so a lateral offset is *already* just different
numbers. ADR 0010 gets full credit for that; the schema anticipated exactly this.

### 6.3 — Note — **Declining lip/bite is defensible, but the field's
justification is that *something* continuous lives at the mouth or the thumb.**

Every published controller gives the player a second continuous axis that can be
operated *while the note sounds and the instrument stays still*: WX5 lip sensor +
right-thumb sprung rocker, EWI bite + two pitch-bend plates, Aerophone bite +
bend. This design declines both — *"No bite or lip sensor. Settled early and
unchanged. There is no embouchure axis and none is wanted"* `[repo] 0003` — and
puts the second axis on the IMU (ADR 0007), with the right thumb carrying three
**binary** control switches `[repo] config/key-layout.yaml`, `[repo] 0010`.

**There is precedent for that: the Sylphyo's expression axes are motion-based**
`[web] https://aodyo.com/product/sylphyo/`. So it is not unprecedented, just
unusual. No change recommended; recorded so the trade is visible — the
instrument's only two continuous axes are breath and whole-body motion, and
whole-body motion is unavailable in any passage where the player is holding the
instrument still.

---

## 7. Things published wind controllers do that this design has not considered
at all

Ranked, and separate from the above so the list is usable as a checklist.

1. **High — Fingering deglitch / note delay.** §4.4. NuEVI `DEGLITCH 20 ms`
   (5–70 ms); EWI5000 exposes it as a player-facing control. Absent from the
   repo, and the repo's stated debounce philosophy points the other way.
2. **High — Hysteresis and a dedicated, heavily-filtered gating signal.** §4.3.
   The field gates on a ~30 Hz copy; this design would gate on a 564 Hz one.
3. **Medium — A rise-wait before committing the note, and velocity sampled after
   it.** §4.5. `ON_Delay 20 ms` in eight published sketches; `VEL_SMP_DL 20`
   with a `VEL_BIAS` in NuEVI.
4. **Medium — A response curve on the CV output.** §4.1. ADDAC310 puts
   exponential↔logarithmic on a panel knob in an 8HP-class breath module; NuEVI
   ships 13 curves and does not default to linear.
5. **Medium — Attack/decay slew on the breath CV.** ADDAC310's "Time" control
   `[web] addacsystem.com/en/news/introducing-addac310-pressure-to-cv`; EWI5000's
   "rate of change"
   `[web] support.akaipro.com/…/69000849456-akai-pro-ewi-5000-calibrating-the-ewi-5000`.
   Not in `breath-output-stage.md`'s two knobs. Cheap in the module's two spare
   op-amp halves, or free in firmware for the digital copy.
6. **Medium — A gate output derived from the breath threshold, as a
   first-class panel feature.** ADDAC310 gives every channel a gate with a
   selectable source (post-slew or pre-slew). Here a gate is *possible* — ADR
   0006 says "a gate can be assigned to one [mod channel] if wanted"
   `[repo] 0006` — but nothing dedicates one, and a breath instrument driving a
   Eurorack VCA needs a gate on essentially every patch. Given `DAC ch 6` is
   explicitly spare `[repo] 0006`, this is nearly free; the cost is a panel jack.
7. **Medium — A *span* calibration for the digital copy.** Every published
   instrument calibrates both ends: WX5 "Wind Zero" *and* "Wind Gain"; EWI5000
   sensitivity *and* dynamic range; NuEVI `breathThrVal` *and* `breathMaxVal`.
   This design defines one zero authority per representation with care
   `[repo] 0003`, `[repo] 0006`, but **defines no span/max authority for the
   digital copy at all** — the analog path gets the panel GAIN knob and the
   digital copy gets nothing. So CC2, the mod channels and the display all run on
   an uncalibrated span. The instrument has a display and a web app; a "blow as
   hard as you ever will" capture is a small feature and it is the field's
   standard.
8. **Low — Draw/vacuum as an expressive axis.** §3.4. Pulp Logic BC does blow and
   draw. Foreclosed here by a unidirectional part; worth writing down as a
   decision.
9. **Low — Hold/freeze on the breath CV.** ADDAC310 has it per channel, gate-
   triggerable. Trivially assignable to an RT control switch here.
10. **Note — Selectable fingering *systems*.** WX5 offers four (three sax, one
    flute) `[web] soundonsound.com/reviews/yamaha-wx5`; EWI5000 offers flute,
    oboe, sax and EVI `[web] sweetwater.com/store/detail/EWI5000--…`. ADR 0010's
    NVS-resident, host-editable fingering table `[repo] 0010` already subsumes
    this — the data model supports multiple tables even though the ADR only ever
    speaks of one. Worth one sentence in ADR 0010 to make it explicit.

---

## 8. Two document-integrity items inside my scope

### 8.1 — Medium — `breath-receive-stage.md` contradicts itself about `REF`.

The page's whole opening argument is that `REF` carries a **buffered trimmer**
(`TRIM-BREATH-ZERO`, 0 → +1.0 V) and that **grounding it would make the panel
knobs interact**. Then, in "What the jack does when the watchdog fires":

> *"breath touches none of them, and **now that `REF` is grounded** it touches
> the breath stage in no way at all"* `[repo] hardware/module/breath-receive-stage.md`

`REF` is not grounded. This is a stale sentence from the revision in which the
DAC channel was deleted, and it directly contradicts `bom.csv`'s
`TRIM-BREATH-ZERO` row `[repo] hardware/bom.csv:102` and the page's own component
table. The *conclusion* (the watchdog does not touch the breath path) survives
either way — but this is exactly the class of two-readings-in-one-document defect
the page was written to eliminate, and the page says so itself in its own
preamble.

### 8.2 — Low — The unverified 0.5 mV/K offset tempco is load-bearing twice.

`[repo] 0003` uses ~0.5 mV/K to conclude the jack drifts ~23 mV in 10 V over
warm-up, which is the argument that retires the DAC-driven ambient zero.
`breath-receive-stage.md` repeats it at ~20 mV and flags it: *"**That figure is
unverified** … nxp.com was unreachable when this was written."* `[repo]`
**nxp.com is still unreachable** (`https://www.nxp.com/docs/en/data-sheet/…`,
proxy-blocked, confirmed this session). Carry the flag into ADR 0003 too, and
close it at the M8 thermal soak, which already puts a thermocouple at the sensor
`[repo] 0003` — measuring the offset tempco there costs nothing and retires a
figure two documents lean on.

---

## 9. Summary table

| # | Design element | Rank | One line |
|---|---|---|---|
| 2.1 | Moisture path / serviceability | **Showstopper** | Every published controller has a drain or a replaceable wet part; this has neither and the body is bonded. The BOM already says the socket "only earns its place if the sensor is reachable" |
| 1.1 | Working pressure range | High | 2.8 kPa is unsourced and cited in a circle; ADR 0003 says 0–5 kPa. Both size real hardware |
| 1.4 | Output stage gain range | High | Commissioning at 2.16× puts the rail at 3.23 kPa, below the field's own full-expression point. Rail clip, no soft region |
| 2.2 | ≤1 mL trap | High | ~0.04 mL/h of condensate, no drain, no stated access route. Tens of hours to fill |
| 2.3 | 400 mm tube vs vapour | High | Diffusion puts mouth humidity at the die in ~56 min. Length does not protect the sensor |
| 4.1 | Breath response curve | High | The nearest published breath-to-CV module has Response, Time, Offset, Gain and a Gate. This has Gain and Offset |
| 4.3 | Note-on rule | High | Bare threshold on a 564 Hz signal; the field gates on ~30 Hz with a state machine. No hysteresis anywhere |
| 4.4 | Fingering deglitch | High | NuEVI defaults to 20 ms; EWI5000 ships it as a knob. Absent here, and the stated debounce philosophy is the opposite |
| 1.3 | Sensor range choice | Medium | 0–6 kPa (not ±) is the right pick for a bleed-free tube, but saturation behaviour is undefined |
| 2.4 | PTFE plug | Medium | A consumable specified as permanent; clogging presents as gradual sluggishness that auto-zero cannot see |
| 2.5 | Reference port humidity | Medium | P1 gets a hydrophobic barrier; P2 sits bare in the breathed-into cavity. Vent it outside through a filtered stub |
| 4.5 | MIDI velocity | Medium | No strategy; the field's 20 ms rise-wait solves this and 4.3 together |
| 5.2 | Latency budget scope | Medium | 5 ms is a breath-CV budget; note-event latency is unbudgeted and about to grow by 20–40 ms |
| 6.2 | Right-hand key line | Medium | Six keys in a strict line under one hand has no precedent in any published layout. Invert the M2 prior |
| 8.1 | `breath-receive-stage.md` | Medium | Says `REF` is grounded in one section and trimmed in three others |
| §7.6–7.7 | Gate output; digital span calibration | Medium | A breath instrument into Eurorack needs a gate; the digital copy has a zero authority but no span authority |
| 3.3 | Reference port vs key presses | Low | ~20 Pa per key into the reference chamber, ~80 Pa on a four-key change — key-correlated breath dip. Measure at E4 |
| 3.4 | Draw / negative pressure | Low | Undefined behaviour, foreclosed expressive axis, unverified reverse-pressure rating |
| 8.2 | 0.5 mV/K tempco | Low | Unverified, load-bearing in two documents, free to measure at M8 |
| 1.2, 1.5, 3.1, 3.2, 4.2, 4.6, 5.1, 6.1, 6.3 | — | Note | Independently **confirmed**: the closed tube, the cavity-leak dependency (by ~3 orders), the 5.2 kPa sealed-chamber figure, gauge-referencing to the interior, 12-bit sufficiency, CC2, the auto-zero scheme, the latency margin, and the 4-key left thumb |

**The single most load-bearing confirmation:** the closed, dead-ended tube —
which ADR 0003 records as having been challenged — is not merely defensible, it
is what a 2024 commercial Eurorack breath module does on purpose. The ADDAC310
*"doesn't provide any way for incoming air to escape, and it's the resulting
pressure buildup that's used to generate the module's CV output"*
`[web] https://sonicstate.com/news/2024/07/26/pressure-to-cv-eurorack-module`.
And the venting-at-the-corners-of-the-mouth technique ADR 0003 relies on is
documented for the EWI as normal practice
`[web] https://www.saxontheweb.net/threads/ewi-usb-airflow.127244/`. That
decision should not be re-raised.

**The single most load-bearing contradiction:** the field's moisture answer is
plumbing and access, not spares. Two shipping instruments built dedicated
hardware for it. This design bought a second sensor and then bonded the body
shut.
