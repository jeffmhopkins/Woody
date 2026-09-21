# B1 — Eurorack mechanical and electrical conformance (cold standards review)

**Date:** 2026-09-21
**Reviewer scope:** mechanical and electrical conformance of the 8HP CV interface
module against *published* Eurorack standards and the actual conventions of
published modules. Not against the project's own reasoning.

**Sources read in the repo:** `hardware/module/*.md` (all six), `hardware/bom.csv`,
`docs/decisions/0004-cv-interface-module.md`, `docs/decisions/0005-power-architecture.md`.
Incidental greps touched `README.md`, `ROADMAP.md`, `firmware/README.md`,
`docs/reference/latency-budget.md`, `docs/decisions/0003`, `0006`.
**`docs/review/**` and `docs/research/**` were not opened.** This review is cold by
construction.

## Network conditions — what could and could not be verified

The sandbox egress proxy blocked almost every relevant host. Verified by
`curl` probe and by tool error:

| Host | Result |
|---|---|
| `doepfer.de`, `www.doepfer.de` | **blocked** (`EGRESS_BLOCKED`, and connect 000). The primary standards source was unreachable throughout. |
| `en.wikipedia.org` | **blocked** (`EGRESS_BLOCKED`) |
| `sdiy.info` | **blocked** (`EGRESS_BLOCKED`) |
| `www.exploding-shed.com` | **blocked** (`EGRESS_BLOCKED`) |
| `modulargrid.net`, `www.modulargrid.net` | blocked (connect 000) |
| `modwiggler.com`, `www.modwiggler.com` | blocked (connect 000) |
| `mutable-instruments.net`, `pichenettes.github.io` | blocked (connect 000) |
| `www.thonk.co.uk` (Thonkiconn datasheet PDF) | blocked (connect 000) |
| `www.neutrik.com`, `neutrik.com`, `www.penn-elcom.com` | blocked (connect 000) |
| `befaco.org`, `musicthing.co.uk`, `www.nonlinearcircuits.com` | blocked (connect 000) |
| `intellijel.com`, `4ms.info`, `learningmodular.com`, `synthcube.com` | blocked (connect 000) |
| `media.digikey.com`, `www.mosaic-industries.com` | blocked (connect 000) |
| `division-6.com`, `northcoastsynthesis.com`, `noiseengineering.us` | blocked (connect 000) |
| `github.com` / `raw.githubusercontent.com` | **reachable** |
| GitHub MCP API | scoped to `jeffmhopkins/woody` only — could not read third-party repos |
| Web search | **worked** (returns search-engine summaries of blocked pages) |

So: first-party open-hardware documentation was obtained only where it lives on
raw.githubusercontent.com. The single richest source obtained is Mutable
Instruments' own documentation repository, which is Émilie Gillet's first-party
text. Everything else is either a search-engine summary of a page I could not
open, or marked `[from memory]`.

**Claims marked `[from memory]` in this report are weak.** Where a conclusion
depends on one, I say what measurement or datasheet page would settle it.

---

# Findings by design element

## 1. Panel width — 8HP = 40.34 mm

**Rank: Note (confirmed correct).** HARD standard, and the module conforms.

The published formula is `width = (n × 5.08) − 0.3 mm, +0 / −0.2`, attributed to
Graham Hinton and reproduced as the Doepfer mechanical specification
`[web] https://www.modwiggler.com/forum/viewtopic.php?t=134066` (via search
summary; modwiggler itself is blocked) and
`[web] https://sdiy.info/wiki/Eurorack` (blocked, search summary only).

`[calc]` 8 × 5.08 = 40.64; 40.64 − 0.3 = **40.34 mm**, tolerance +0/−0.2, i.e.
40.14–40.34 mm.

`[repo] docs/decisions/0004-cv-interface-module.md:603` states
"`(8 × 5.08) − 0.3` = **40.34 mm**, +0/−0.2" and `[repo] hardware/bom.csv` PANEL
row states `40.34 × 128.5mm`. **Both the formula and the tolerance direction are
exactly right**, including the detail that the tolerance is one-sided. This is
better than most DIY projects get it. Independently confirmed, no action.

Panel height 128.5 mm is likewise correct
`[web] https://www.modwiggler.com/forum/viewtopic.php?t=155376` (search summary):
3U raw = 3 × 44.45 = 133.35 mm `[calc]`, panel sized down to 128.5 mm to clear
the rail flanges.

---

## 2. Panel mounting holes and slots — NOT SPECIFIED ANYWHERE

**Rank: Medium.** HARD standard (the module will not mount) but trivially fixed
before the DXF is cut.

Published values: mounting holes sit **3 mm in from the top and bottom panel
edges, giving 122.5 mm between hole centres, at Ø3.2 mm**
`[web] https://www.modwiggler.com/forum/viewtopic.php?t=155376` and
`[web] https://synthracks.com/blog/eurorack-rails-diy-guide` (both via search
summary; hosts blocked). `[calc]` 128.5 − 2×3 = 122.5. ✓ internally consistent.

Published panels use **elongated/oval slots rather than round holes**, because
5.08 mm HP pitch does not align with the M3 sliding-nut positions in a rail slot
and a round hole leaves no lateral adjustment `[from memory — weak; I could not
open a published panel DXF or a Doepfer drawing to confirm the slot dimensions]`.

`[repo]` The repo specifies **none of this**. `hardware/bom.csv` PANEL row says
only "2mm aluminium, 8HP x 3U (40.34 x 128.5mm) … Laser or waterjet from DXF".
There is no hole count, no hole position, no hole diameter, no slot geometry
anywhere in `hardware/module/*.md`, `bom.csv`, ADR 0004 or ADR 0005. At 8HP the
convention is **two fixings, diagonally opposite** (top-left, bottom-right)
`[from memory — weak]`.

**Action:** put Ø3.2 mm (or 3.2 × 5.5 mm slots) at 3 mm from top and bottom edges
into the DXF spec, and decide 2 vs 4 fixings. This matters more than usual here
because the panel is carrying a latching connector that gets tugged (§4).

---

## 3. Panel height budget — "107 mm of ~110 mm usable" is unsupported and I do not believe it

**Rank: High.** HARD constraint. This is my principal mechanical finding.

### The available window

`[web]` The usable vertical window for **panel-mounted hardware** is ~110 mm, not
128.5 mm: "the PCB behind the front panel is typically about 18.5 mm shorter than
the panel height, resulting in approximately 110 mm for a 3U PCB"
`[web] https://www.modwiggler.com/forum/viewtopic.php?t=155376` (search summary).
`[calc]` 128.5 − 18.5 = 110.0. The rails sit *behind* the panel at top and
bottom, so any component body that protrudes behind the panel must land inside
that window or it fouls a rail. The project uses 110 mm and that is the right
number.

### The claimed content

`[repo] docs/decisions/0004-cv-interface-module.md:584-585` — "Connector, power
switch and LED … two breath knobs, then six jacks in two columns … Roughly
**107 mm of ~110 mm usable height** — full but workable."
Repeated at `[repo] :500` — "a panel already at 107 mm of ~110 mm usable".

**There is no breakdown of the 107 mm anywhere in the repository.** I grepped the
whole repo (excluding `docs/review/**` and `docs/research/**`) for `107`, `110`,
`128.5`, `13 mm`, "jack pitch", "panel layout", "knob" — the only hits are the two
assertions above and the BOM PANEL/PCB rows. The number is asserted, never
derived.

### Bottom-up reconstruction

`[calc]` Using the project's own component list and conventional Eurorack
envelopes (`[from memory]` for the envelopes themselves — each is flagged):

| Element | Vertical envelope | Basis |
|---|---|---|
| Neutrik etherCON D flange | **31 mm** + 1 mm clearance each side = **33** | flange height ~31 mm `[from memory — weak; the caller's brief gives ~26 × 31 mm, consistent]` |
| gap | 3 | judgement |
| Toggle + LED **sharing one row** | 12 | 6 mm bushing needs ~10 mm plus lever clearance `[from memory]` |
| gap | 3 | judgement |
| Two Alpha 9 mm pots **side by side** | 18 | 16 mm knob + 2 mm `[from memory]` |
| gap | 4 | judgement |
| Six jacks, 3 rows × 2 columns at 13 mm pitch | **42** | 8 mm above first centre + 2 × 13 + 8 mm below last, to clear plug bodies |
| **Total** | **115 mm** | |

**115 mm against 110 mm available.** And that layout already takes every
favourable option: toggle and LED share a row, the two pots are side by side
rather than stacked, jack pitch is at the tight end, and the MOD 1–4 write-on
strip is assumed to fit in the gutter between the two jack columns rather than
taking its own band.

Stack the two pots vertically instead and it becomes `[calc]` 115 + 18 = **133 mm**,
which is more than the whole panel.

**I cannot reproduce 107 mm from the stated contents.** The gap between my 115 mm
and the project's 107 mm is 8 mm, which is roughly the sum of the inter-element
clearances — i.e. the 107 mm figure looks like a sum of component heights with no
clearance allowance at all.

### What settles it

This is the one thing in the module that is cheap to falsify and expensive to get
wrong (the panel is laser-cut once, in the same order as the key plate per
`[repo] ADR 0004:224`). ADR 0004 already says "Print the panel at 1:1 on paper and
check it is actually usable before cutting" `[repo] :587`. **That check is now
load-bearing, not a nicety.** Do it with:

- the real Neutrik D-series drawing (flange height and screw-centre spacing),
- real knobs on real Alpha 9 mm pots,
- a real 3.5 mm plug inserted in adjacent jacks at the chosen pitch.

If it does not fit, the honest options are 10HP, or moving the etherCON off the
panel face (see §5).

---

## 4. Panel width vs. two knobs — the "16–20 mm knob" claim is wrong at the top of its range

**Rank: Low.** CONVENTION, easily fixed at BOM time.

`[repo] docs/decisions/0004-cv-interface-module.md:646` — 8HP "allows a normal
16–20 mm knob instead of the ~13 mm the 15 mm pot centres forced."

`[calc]` Two knobs side by side on a 40.34 mm panel:
- 16 mm knobs: centres ≥16 mm apart → e.g. 12.17 and 28.17 mm; knob edge sits
  **4.17 mm** from each panel edge. Workable, tight.
- 20 mm knobs: centres ≥20 mm apart → 10.17 and 30.17 mm; knob edge sits
  **0.17 mm** from each panel edge. **Does not fit**, and would overhang the
  neighbouring module.

So 20 mm knobs are only available if the two pots are stacked vertically — which
costs another 18 mm of the height budget that §3 says is already over. State
**16 mm maximum, side by side** in the BOM (`KNOB-BREATH` row currently says only
"Match the shaft of the POT-BREATH variant ordered").

---

## 5. etherCON on the panel — the panel cutout arithmetic is right; the notch consequence is under-stated

**Rank: Medium.**

`[repo] ADR 0004:606-609` and `[repo] bom.csv` J-UMBILICAL: "23.8mm cutout in a
40.34mm 8HP panel = 8.27mm each side."
`[calc]` (40.34 − 23.8) / 2 = **8.27 mm**. ✓ arithmetic correct.

The Neutrik D-series panel cutout is commonly drawn as **Ø24.0 mm** with a flat
`[from memory — weak; neutrik.com and penn-elcom.com were both blocked, so I could
not open the drawing]`. `[calc]` If it is 24.0 rather than 23.8, the remaining
aluminium is (40.34 − 24.0)/2 = **8.17 mm** — the conclusion is unchanged either
way, so the 8HP decision is robust to that uncertainty. Good.

**Confirmed and correctly captured:** the D-series is rated for **max 4 mm panel
thickness** `[web] https://www.neutrik.com/en/product/ne8fdp` (via search summary;
host blocked). A 2 mm aluminium panel is inside that. `[repo] ADR 0004:657` and
`[repo] bom.csv` J-UMBILICAL both state this and correctly conclude the
*instrument* end cannot mount through 6 mm oak. Independently confirmed.

**What is under-stated: the PCB notch.**
`[repo] bom.csv` PCB-MODULE: "~35 x 110mm, 1.6mm". `[repo] ADR 0004:637` says
clearing the connector body needs a "~26 mm notch".
`[calc]` 35 − 26 = 9 mm of web, i.e. **4.5 mm of 1.6 mm FR4 on each side**,
spanning the ~31 mm height of the notch.

Two consequences the repo does not draw out:

1. **All routing between the top and bottom halves of the module crosses two
   4.5 mm webs**, on a **2-layer** board (`[repo] bom.csv` PCB-MODULE). That
   includes ±12 V, the 5.21 V rail, three SPI lines, and — critically —
   `PWR_GND`, which `[repo] ADR 0004:565` requires to run "from the etherCON to
   the star point **on its own copper**, touching nothing else on the way", while
   carrying 360 mA–1.0 A. The etherCON is at the top of the panel; the power
   header and star point are not. That current has to cross a 4.5 mm web without
   sharing copper with the analog return, on two layers, next to a 16-bit DAC.
   Current density is not the problem (`[calc]` 1 A on 1 oz outer copper wants
   ~0.5 mm for a 10 °C rise `[from memory]`, which fits easily in 4.5 mm) —
   **routing congestion is.**
2. **Structural.** 4.5 mm of FR4 each side is the load path between the two
   halves of the board, in a module whose whole premise is that a cable is tugged
   at the panel every time the instrument moves. `[repo] ADR 0004:652` says
   "Brace the connector to the PCB anyway … At 8HP this is good practice rather
   than a structural necessity." With a 26 mm notch through a 35 mm board, I
   would call it a necessity, not good practice.

---

## 6. Module depth behind the panel

**Rank: Medium (convention), Note (hard fit).**

Published case depths `[web] https://modwiggler.com/forum/viewtopic.php?t=154441`,
`[web] https://modwiggler.com/forum/viewtopic.php?t=115249`,
`[web] https://www.perfectcircuit.com/signal/buying-guide-eurorack-cases` (all via
search summary; hosts blocked):

- "skiff friendly" ≈ **25–40 mm** module depth
- Doepfer skiffs: **max module depth 55 mm**, 60 mm inside depth
- original Doepfer racks ≈ **140 mm**; portable Doepfer ≈ **100 mm**
- typical aluminium performance boats ≈ **70 mm** inside

`[repo] ADR 0004:636` says the etherCON "body extends 30–40 mm behind the panel
while the jacks put the PCB about 7 mm behind it". Taking the worst of that,
overall module depth ≈ **40 mm** plus a little for the 16-pin shrouded header
(~9 mm tall `[from memory]`) and the radial 100 µF entry electrolytic (~11 mm
`[from memory]`) sitting on a PCB 7 mm back: `[calc]` 7 + 1.6 + 11 = ~20 mm, so
the etherCON dominates.

**Verdict on hard fit: ~40 mm fits every mainstream case and is inside Doepfer's
55 mm skiff limit. It is marginal for the shallowest skiffs.** Declare it. No
published module declares depth as a matter of course, but ModularGrid records it
and buyers filter on it.

**The convention problem is on the front, not the back.** The etherCON is on the
*panel face*, so a latching metal-shelled Cat5e plug protrudes **forwards** out of
an 8HP module, into the same space patch cables occupy, with a stiff patch lead
and a bend radius. An etherCON cable plug is ~60 mm long `[from memory — weak]`.
Consequences no repo document addresses:

- It will fight the lids of lidded cases (Intellijel, Doepfer portable, most
  performance boats).
- It occupies the front airspace of the neighbouring modules.
- It is the one connector on the panel that a user cannot simply unplug to close
  the lid without powering the instrument down.

This is a genuine "will surprise a Eurorack user" item. It is a *convention*
issue, not a standards violation — nothing forbids it — but it is the kind of
thing that gets a module returned.

---

## 7. Jacks — PJ398SM / Thonkiconn

**Rank: Low / Note.** Conforming choice; three details unspecified.

**Confirmed conforming.** PJ398SM (a.k.a. Thonkiconn, QingPu WQP-PJ398SM) is the
de facto Eurorack 3.5 mm jack
`[web] https://raw.githubusercontent.com/clacktronics/AudioJacks/main/DATA.md`
(first-party-ish: a maintained Eurorack KiCad library's own reference notes — "AKA
Thonkiconn, very commonly used eurorack jack sold by many suppliers like Thonk").
`[repo] bom.csv` J-CV row: "PJ398SM (Thonkiconn) … De facto eurorack standard.
Standard panel hole". Correct.

**Panel hole: 6 mm.** `[web] https://www.midiphy.com/en/shop-details/179/61/pj398sm-jack-x10-modular-eurorack-diy-3-5mm-jack-pj398sm`
(via search summary; host reachable only through search) — "3.5mm mono connector
with switching function for PCB mounting that needs a 6mm hole in the panel."
`[repo]` The repo never states 6 mm, or any panel hole diameter for any component.
The DXF needs jack Ø6.0, pot bushing (Alpha 9 mm vertical = M7, Ø7.0 `[from
memory — weak]`), toggle Ø6.0 for a 6 mm bushing, LED Ø3.0, and the etherCON
D-cutout. **None of the five is written down.**

**Nut torque: no published figure found.** The Thonk datasheet PDF
(`https://www.thonk.co.uk/wp-content/uploads/2014/02/Thonkiconn_Jack_Datasheet.pdf`)
was unreachable — `www.thonk.co.uk` refused connection through the proxy. Four
searches surfaced no manufacturer torque spec from QingPu either. Community
practice is finger-tight plus a small nudge, because the moulded body cracks when
over-torqued `[from memory — weak]`. **Do not put a torque figure in the build
documentation that you have not read off a datasheet.**

**Jacks as mechanical support — conforming, and this module is well served.**
The convention is that the panel nuts on jacks and pots hold the PCB to the panel,
with no separate standoffs: "the most important part is that the parts are all the
same height off the PCB, and Alpha pots and the PJ398SMs are as such"
`[web] https://www.modwiggler.com/forum/viewtopic.php?t=227586` (search summary).
`[repo]` This module has six jacks + two pots + a toggle + the etherCON's own two
screws — more panel fixings than most 8HP modules. Fine. The one caution is §5:
the etherCON's screws and the jacks' nuts are on opposite sides of a 26 mm notch,
so panel-to-PCB spacing has to be consistent across that notch or the jacks will
be strained.

**Switched contact / normalling — not addressed.** PJ398SM is the *switched*
variant: three pins, the third being a normalling contact that is closed to the
tip when no plug is inserted
`[web] https://www.midiphy.com/...pj398sm-jack-x10-...` (search summary). All six
of this module's jacks are **outputs** (`[repo]` pitch, breath, MOD 1–4), so there
is nothing to normal, and leaving the switch pin unconnected is the correct and
conventional treatment. **But no repo document says so.** The six schematic
drawings in `hardware/module/*.md` all end at "MOD n jack" / "BREATH jack" /
"PITCH jack" with a single wire and no pin assignment. A builder stuffing the
board has no statement of which of the three pins is tip, which is sleeve, and
that the third is deliberately floating. Add one line. (If the switch pins are
left floating *and routed*, they are 6 antennas next to a 16-bit DAC; tie them to
nothing, or to AGND at a single point, deliberately.)

**Note:** if the normalling contact is genuinely unused, PJ301M-12 is the same
footprint and is what half the corpus uses
`[web] https://raw.githubusercontent.com/clacktronics/AudioJacks/main/DATA.md`.
No reason to change; recorded so the choice is a choice.

---

## 8. Power header — 16-pin shrouded keyed IDC

**Rank: conforming choice. But see §9 — the reverse-insertion analysis in the repo is wrong.**

**The pinout.** Two independent sources agree, and they agree with each other on
non-overlapping halves:

- `[web] https://cdn-learn.adafruit.com/downloads/pdf/usb-to-eurorack-power-supply.pdf`
  (search summary; `cdn-learn.adafruit.com` not directly fetched): "+12V to IDC
  pins **9 and 10**, −12V to IDC pins **1 and 2**, GND to pins **3, 4, 5, 6, 7 and 8**."
- `[web] https://github.com/Takazudo/claude-resources` →
  `skills/kicad-sch-tweak/references/kicad-sch-format.md`, "Eurorack IDC Pinout
  Reference" table (surfaced by GitHub code search; I could not open the file —
  the GitHub MCP is scoped to `jeffmhopkins/woody` only): "| 13 | CV | 14 | CV |
  | 15 | GATE | 16 | GATE |".

`[calc]` Those two are consistent and leave exactly one gap, which must be +5 V:

| Pin | Net | Pin | Net |
|---|---|---|---|
| 1 | **−12 V** (red stripe) | 2 | −12 V |
| 3 | GND | 4 | GND |
| 5 | GND | 6 | GND |
| 7 | GND | 8 | GND |
| 9 | **+12 V** | 10 | +12 V |
| 11 | **+5 V** | 12 | +5 V |
| 13 | CV bus | 14 | CV bus |
| 15 | Gate bus | 16 | Gate bus |

**This table is reconstructed, not read off Doepfer.** `doepfer.de` was blocked.
Verify against `https://doepfer.de/a100_man/a100t_e.htm` before committing copper.

**Red stripe = −12 V.** "At the bus board side the colored wire has to show to the
bottom which is labeled '−12V'"
`[web] https://doepfer.de/a100_man/a100t_e.htm` (via search summary of the blocked
page) — and confirmed first-party in every Mutable manual, e.g.
`[web] https://raw.githubusercontent.com/pichenettes/mutable-instruments-documentation/master/docs/modules/plaits/manual.md`:
"The red stripe of the ribbon cable (−12V side) must be oriented on the same side
as the '**Red stripe**' marking on the module and on your power distribution board."

**`[repo]` The module has no red-stripe marking specified.** `bom.csv`
J-PWR-EURO says "Shrouded and keyed — reversed ribbon is the classic eurorack
failure." Shrouding is the right answer, but **every published module silkscreens
the stripe marking anyway** — Mutable states it in the manual of every single
module I fetched (Plaits, Rings, Beads, Marbles). Add "Red stripe ▼" to the
silkscreen and to the build documentation. This costs nothing and is a universal
convention.

**`[repo]` The CV and Gate bus lines (pins 13–16) are never mentioned anywhere.**
Not in `hardware/module/power-entry.md`, not in ADR 0004, not in ADR 0005, not in
the BOM. Using a 16-pin header means the module's connector lands on the bus CV
and Gate lines. The correct treatment — **leave them unconnected** — is almost
certainly what is intended, but it must be *stated*, because the failure mode if
a layout tool auto-connects them to the ground pour is that this module shorts the
case's CV and Gate buses for every other module in the rack. One line in
`power-entry.md`.

**10-pin vs 16-pin is itself a convention point.** Every Mutable module I fetched
uses a **2×5 (10-pin)** connector — Plaits, Rings, Beads and Marbles all say
"requires a −12V/+12V power supply (**2x5 pin connector**)"
`[web] https://raw.githubusercontent.com/pichenettes/mutable-instruments-documentation/master/docs/modules/{plaits,rings,beads,marbles}/manual.md`.
16-pin on the module is legitimate and is what you must use if you want +5 V — but
see §10, because the +5 V requirement is the thing forcing it, and it is
load-bearing for almost nothing.

---

## 9. Reverse insertion — **the series Schottkys do not protect a 16-pin module, and the repo's analysis of this is wrong**

**Rank: Showstopper (for the stated analysis) / High (for the design consequence).**
This will damage the user's case PSU, not the module.

`[repo] docs/decisions/0004-cv-interface-module.md:193-195`:

> "the only thing hanging on the unprotected bus +5 V pin is a $0.30 buffer. A
> reversed or row-offset ribbon that puts +12 V onto that pin kills the buffer and
> nothing else, which is why the +5 V entry gets no protection network of its own."

Repeated at `[repo] hardware/module/power-entry.md`: "a reversed ribbon that kills
the buffer and nothing else is an acceptable outcome (ADR 0004)."

**That is only true for a 10-pin connector.** Work the 16-pin case.

A 180° reversal maps module pin *n* to bus pin *17 − n*. `[calc]` Using the
pinout in §8:

| Module pin(s) | Module net | Now connected to bus pin(s) | Bus net |
|---|---|---|---|
| 1, 2 | −12 V | 16, 15 | Gate |
| 3, 4 | GND | 14, 13 | **CV** |
| 5, 6 | GND | 12, 11 | **+5 V** |
| 7, 8 | GND | 10, 9 | **+12 V** |
| 9, 10 | +12 V | 8, 7 | GND |
| 11, 12 | +5 V | 6, 5 | GND |
| 13, 14 | CV | 4, 3 | GND |
| 15, 16 | Gate | 2, 1 | −12 V |

**The module's ground net lands on bus +12 V, bus +5 V and bus CV simultaneously.**
That is a dead short from the case's +12 V rail to its +5 V rail through this
module's ground plane, with the module's entire ground pour floating at +12 V.
The series Schottkys D1, D2 and D3 are on the *rails*; **none of them is in the
ground path**, so they do nothing. Outcome: the case PSU current-limits, blows a
fuse, or cooks — and the module's electrolytics see reverse bias.

Contrast the 10-pin case `[calc]`: pins 1,2 = −12 V, 3–8 = GND, 9,10 = +12 V;
reversal maps 1↔10, so −12 V ↔ +12 V and **GND maps to GND**. The rails swap, the
Schottkys block, nothing happens. *This* is the case the "series diode makes you
reverse-proof" folklore describes, and it is the case Mutable is describing when
they say "with 2/, nothing happens, it's like an open circuit"
`[web] https://raw.githubusercontent.com/pichenettes/mutable-instruments-documentation/master/docs/tech_notes/hardware_miscellania.md`.

**So:** on a 16-pin module, *only the shroud and key* prevent a case-damaging
event. The diodes are not a second line of defence for this failure — they are a
second line of defence for a different failure. `[repo] ADR 0004:217-218` — "a
16-pin shrouded keyed IDC power header with Schottky diodes behind it. Reversed
ribbon cable is the classic Eurorack failure and **the keying alone is not worth
trusting**" — has it backwards. The keying is the *only* thing protecting against
reversal here; the diodes protect against a rail-swap that a keyed 16-pin
connector cannot produce anyway.

**Concrete consequences to act on:**

1. The shroud and key on `J-PWR-EURO` are now **safety-critical**, not
   belt-and-braces. Specify the part properly (shrouded, keyed, and the key on the
   correct side relative to pin 1).
2. The "+5 V entry gets no protection because a reversed ribbon only kills the
   buffer" argument **must be withdrawn**. It is wrong about what a reversed
   16-pin ribbon does. Whether the +5 V pin then wants a diode is a separate and
   much smaller question (§10 argues the pin should not exist at all).
3. **Row-offset insertion is a live hazard here specifically because the header is
   16-pin.** A 10-pin socket will physically sit inside a 16-pin shroud in more
   than one position `[from memory — weak, but this is the well-known reason DIY
   guides tell you to align to the stripe]`. A 10-pin header does not have this
   degree of freedom. Since §10 argues the +5 V rail is not needed, going to a
   **10-pin header removes both this hazard and the reversal hazard above.**

---

## 10. The +5 V rail — this module requires a case rail it does not need, and the stated reason is backwards

**Rank: High.** CONVENTION, with a hard-compatibility consequence.

`[repo] docs/decisions/0005-power-architecture.md`: "the bus +5 V rail is free and
convenient. It is used — but **only for the 74AHCT125 level shifter**, around
10 mA." And: "The target rack supplies +5 V, so the level shifter's rail is a
**requirement, not an option**. No jumper, no unpopulated fallback footprint."

### What published modules do

The dominant practice is to **not touch the bus +5 V at all**, and to derive
low-voltage rails locally from +12 V. First-party evidence:

- **All four Mutable modules I fetched draw nothing from +5 V** and use a 10-pin
  connector, which has no +5 V pin: Plaits 50 mA/+12 V, 5 mA/−12 V; Rings
  120/5; Beads 100/10; Marbles 80/20
  `[web] https://raw.githubusercontent.com/pichenettes/mutable-instruments-documentation/master/docs/modules/{plaits,rings,beads,marbles}/manual.md`.
  These are digital modules with MCUs. Émilie Gillet's own hardware note says the
  digital section "run[s] at 3.3V, usually generated through a linear or
  switched-mode regulator **embedded in the module**"
  `[web] https://raw.githubusercontent.com/pichenettes/mutable-instruments-documentation/master/docs/tech_notes/hardware_miscellania.md`.
- Mutable sold a whole product, **Volts**, whose only job is to make +5 V from the
  case for people whose cases do not have it — using an OKI-78SR-5 switcher
  `[web] https://www.thonk.co.uk/shop/mutable-instruments-volts-5v-source/` (search
  summary). The existence of that product is the evidence that +5 V is not
  dependable.
- "+5V rail is used on a select number of modules requiring some extra power"
  `[web] https://www.modwiggler.com/forum/viewtopic.php?t=24935` (search summary).

### What +5 V is actually worth in a real case

- Tiptop **uZeus**, one of the most widespread PSUs: **+12 V 2000 mA, −12 V 500 mA,
  +5 V 170 mA** `[web] https://synthracks.com/shop/tiptop-audio-uzeus-with-universal-adaptor`
  (search summary).
- Intellijel **TPS80W**: +12 V 3 A, −12 V 3 A, **+5 V 1.5 A**
  `[web] https://intellijel.com/downloads/manuals/tps-power-supply-eurorack_manual_2019.09.16.pdf`
  (search summary; host blocked).
- Doepfer **PSU3**: +12 V 2000 mA, −12 V 1200 mA, **+5 V 4000 mA**
  `[web] https://doepfer.de/a100_man/a100t_e.htm` (search summary; host blocked).

So 10 mA of +5 V is trivially available *when the rail exists*. The problem is
that plenty of cases and bus boards do not present it, and plenty of users own
only 10-pin cables.

### The stated reason does not survive checking

`[repo] ADR 0005`: the buffer stays on bus +5 V because "Its job is to clear the
DAC's 0.7 × AVDD threshold; the bus rail is a stated requirement".

`[calc]` The DAC's AVDD is the LM317's **5.21 V** (`[repo] bom.csv` U-REG-DAC,
`R-REG-SET`: Vout = 1.25 × (1 + 475/150) = 5.21 V ✓ arithmetic checks).
V_IH = 0.7 × 5.21 = **3.65 V**.

- Buffer on **bus +5 V at −5 % = 4.75 V** → AHCT output ≈ 4.6 V. Margin
  4.6 − 3.65 = **0.95 V**.
- Buffer on the **local 5.21 V** → output ≈ 5.1 V. Margin **1.45 V**, and it
  **tracks AVDD exactly**, so the margin is immune to rail movement by
  construction rather than by tolerance stack.

**The local rail gives a strictly better threshold match than the bus rail.** The
justification for using bus +5 V is the opposite of what the numbers say. The real
argument for the bus rail — keeping the buffer's switching current off the DAC's
supply — is a decoupling problem (a bead and a 100 nF, both already in the BOM),
not a rail-selection problem. Three SPI lines at 2 MHz into short traces is
`[calc]` roughly 3 × 30 pF × 2 MHz × 5 V ≈ **0.9 mA** of average switching current
`[from memory for the 30 pF]` — not a threat to an LM317LZ with 100 mA of headroom.

### Recommendation

**Delete the bus +5 V dependency.** Run the 74AHCT125 from the LM317's 5.21 V.
That:

- removes the only thing on the unprotected +5 V pin, so §9's "reversed ribbon
  kills the buffer" argument becomes moot rather than wrong;
- lets the header become **10-pin**, which removes the 16-pin reversal hazard
  (§9) and the row-offset hazard;
- makes the module work in every Eurorack case rather than in cases with a +5 V
  rail;
- matches what every Mutable module does.

The counter-argument in `[repo] ADR 0005` ("A module that also worked in cases
without a +5 V rail would be engineering for a case this instrument is never in")
is a defensible scope call for a one-off. It is still a departure from the
strongest convention in the corpus, it is bought with the weaker of the two
threshold margins, and it costs the module its reverse-insertion safety. Record
the trade honestly or take the free win.

---

## 11. Current draw declaration — the number to publish, and it is very large for 8HP

**Rank: High.** CONVENTION, with a real risk of browning out small cases.

### How published modules declare it

Per-rail milliamps, in the manual, first-party. Mutable's exact phrasing:
"The module draws **50mA** from the **+12V** rail, and **5mA** from the **−12V**
rail."
`[web] https://raw.githubusercontent.com/pichenettes/mutable-instruments-documentation/master/docs/modules/plaits/manual.md`.
ModularGrid records +12/−12/+5 mA per module and sums a rack
`[web] https://www.modwiggler.com/forum/viewtopic.php?t=133347` (search summary).

**For a module that powers something external there is an established form**, and
it is exactly this module's situation. Expert Sleepers FH-2 — also **8HP**, also a
USB host that feeds external gear — declares: "**118mA on the +12V rail, 48mA on
the −12V rail plus the power requirement of any attached USB device**"
`[web] https://rubadub.co.uk/products/expert-sleepers-fh-2-factotum` (search
summary). Copy that structure.

### This module's numbers

`[repo]` inputs: module analog +12 V ≈ 45 mA, −12 V ≈ 40 mA, bus +5 V ≈ 10 mA
(ADR 0004:246-250). Umbilical load from ADR 0005's load table: quiescent 212 mA,
typical play **359 mA**, typical + WiFi 414 mA, clamp-legal worst **579 mA**,
clamp-failed ~1522 mA. Load switch trips at **1.0 A** (`[repo] bom.csv` R-ILIM,
U-LOADSW).

`[calc]` Declared totals:

| Condition | +12 V | −12 V | +5 V |
|---|---|---|---|
| Quiescent (instrument booted, LEDs blanked) | 45 + 212 = **257 mA** | 40 mA | 10 mA |
| **Typical play** | 45 + 359 = **404 mA** | 40 mA | 10 mA |
| Typical + WiFi config | 45 + 414 = **459 mA** | 40 mA | 10 mA |
| Clamp-legal worst | 45 + 579 = **624 mA** | 40 mA | 10 mA |
| **Bounded worst — load switch at limit** | 45 + 1000 = **1045 mA** | 40 mA | 10 mA |

**The number to publish is the bounded worst, 1045 mA on +12 V**, because that is
what the case must survive, and it is the one figure the design actually
guarantees. `[repo] ADR 0004:248` currently declares "~320 mA (45 module … ~275
instrument)", which is **stale** — ADR 0005's later load table puts typical play at
359 mA, not 275 mA. Two ADRs disagree. Fix.

### Sanity check against a real op-amp count

`[calc]` +12 V module analog, bottom-up from `[repo] bom.csv`: 6 × OPA2197 dual =
12 channels × ~1 mA `[from memory for OPA2197 Iq]` ≈ 12 mA; INA828 ≈ 1 mA; LM311
≈ 5 mA; DAC8568 ≈ 3 mA; LM317 divider 1.25 V / 150 Ω = **8.3 mA**; panel LED
4 mA. Total ≈ **33 mA**, plus output load currents. The declared 45 mA is a
sensible conservative figure. ✓ Independently plausible.

### Is that reasonable for an 8HP module?

No. It is extreme, and it should be declared loudly.

`[calc]` Against published modules:

| Module | HP | +12 V | This module (typical 404 mA) |
|---|---|---|---|
| Mutable Plaits | 12 | 50 mA | **8.1×** |
| Mutable Marbles | 18 | 80 mA | 5.1× |
| Mutable Beads | 16 | 100 mA | 4.0× |
| Mutable Rings | 14 | 120 mA | 3.4× |
| Expert Sleepers FH-2 | **8** | 118 mA | 3.4× |
| Metasonix MVIP (cited as a power hog) | — | 140 mA | 2.9× |
| Soundmachines LP1 (cited as a power hog) | — | >200 mA | ~2× |

(Power-hog citations: `[web] https://modwiggler.com/forum/viewtopic.php?t=52083`,
search summary.)

`[calc]` Against real supplies, using the **bounded worst 1045 mA**:

| PSU | +12 V capacity | Typical 404 mA | Bounded worst 1045 mA |
|---|---|---|---|
| Doepfer A-100 standard / PSU2 | 1200 mA | 34 % | **87 %** |
| Tiptop uZeus | 2000 mA | 20 % | **52 %** |
| Doepfer PSU3 | 2000 mA | 20 % | 52 % |
| Intellijel TPS80W | 3000 mA | 13 % | 35 % |

(Capacities: `[web] https://doepfer.de/a100_man/a100t_e.htm`,
`[web] https://synthracks.com/shop/tiptop-audio-uzeus-with-universal-adaptor`,
`[web] https://intellijel.com/downloads/manuals/tps-power-supply-eurorack_manual_2019.09.16.pdf`
— all via search summary, hosts blocked.)

**On the classic Doepfer 1200 mA supply this one 8HP module can legitimately take
87 % of the entire +12 V budget.** That is not a violation of anything — but a
user who puts it in an LC9 with a PSU2 and a couple of digital modules will brown
out the case, and it will look like the module is faulty. It belongs in the
manual in bold.

### Per-connector limits — real numbers

The bus connector, not the PSU, is the other limit, and it is fine here:

- 2.54 mm IDC contacts are commonly rated **1 A per contact** (3M and equivalents)
  `[web] http://www.mosaic-industries.com/embedded-systems/electronic-instrument-design-new-product-development/cables/ribbon-cable-current-rating`
  and `[web] https://media.digikey.com/pdf/Data%20Sheets/Wurth%20Electronics%20PDFs/Box%20Header_IDC%20Conn%20WR-BHD.pdf`
  (both via search summary; hosts blocked).
- `[calc]` +12 V has **2 contacts** → ~2 A capacity. At the bounded worst 1045 mA
  that is **523 mA per contact, 52 % of rating**. Acceptable.
- `[calc]` The ground return has **6 contacts** → ~6 A. The 1045 mA return is
  17 % of rating. Fine.
- 28 AWG ribbon is the standard 2.54 mm IDC cable `[web]` same sources; single-
  conductor free-air rating ~1.4 A `[from memory — weak]`, derated in a bundle.
  Two conductors carrying 523 mA each is inside that.

**So the connector survives — but only because the LT1641 bounds the fault at
1.0 A.** Without the load switch, an umbilical short would pull the +12 V pin pair
to whatever the case PSU can deliver, and Mutable explicitly warns that "some PSUs
are now so beefy that they'd happily dump 2A"
`[web] https://raw.githubusercontent.com/pichenettes/mutable-instruments-documentation/master/docs/tech_notes/hardware_miscellania.md`.
**The load switch is the single best decision in this module's power entry and the
one that makes the whole umbilical idea defensible in someone else's rack.** Say so.

---

## 12. D2 (1N5817) is sized exactly at the load-switch trip current — zero margin

**Rank: High.** Component rating, hard.

`[repo] hardware/module/power-entry.md` and `[repo] bom.csv` D-REVPOL: three
1N5817 in DO-41, one of which (**D2**) carries the entire umbilical branch.
`[repo] bom.csv` R-ILIM / U-LOADSW: limit **1.0 A**, timer 50 ms, LT1641-**1**
latches off.

`[calc]` The 1N5817 is rated **1.0 A average forward current, 20 V**
`[from memory — this rating is very well established, but I could not open a
datasheet: `www.diodes.com`, `assets.nexperia.com` and `www.onsemi.com` were all
403'd by the proxy]`. That average rating is quoted at a specified lead
temperature (typically T_L = 75–90 °C), with no derating headroom at 1.0 A.

The load switch's job is to hold **1.0 A** through a fault for the full 50 ms
timer. D2 carries that same 1.0 A, in series, for the same 50 ms, with `[calc]`
V_f ≈ 0.45 V at 1 A `[from memory]` → **~0.45 W in a DO-41 with no heatsinking**.
And in normal clamp-legal worst case it sits at 624 mA continuously.

**So the reverse-protection diode is rated at exactly the current the protection
circuit is designed to sustain.** There is no margin anywhere in that chain.

**Action:** use a 2–3 A Schottky on the umbilical branch — 1N5822 (3 A, DO-41,
same footprint) or SS34/SS54 in SMA. Pennies. `[repo] bom.csv` D-USBOR already
lists "1N5817 **or SS14**", so the part family is familiar to the project. Keep
1N5817 for D1 (module analog, 45 mA) and D3 (−12 V, 40 mA), where it is
comfortable.

---

## 13. Reverse-polarity topology — independently confirmed, and the repo's prior-art claim about Mutable is wrong

**Rank: Note (design confirmed) / Low (citation wrong).**

This is the part of the module where the cold check most strongly *supports* the
project.

Mutable Instruments' own hardware note
`[web] https://raw.githubusercontent.com/pichenettes/mutable-instruments-documentation/master/docs/tech_notes/hardware_miscellania.md`
describes both schemes and says why they **abandoned** the polyfuse:

> "Two approaches can be found in the schematics: 1. Series polyfuse + shunt
> diode … 2. Series diode, preferably Schottky (low voltage drop) … **So why did I
> stop using 1?** — With 1/, the small resistance of the polyfuse causes a voltage
> drop that **varies with the current consumption of the module**. The result is
> that the +12V supply for the op-amps **slightly follows the current consumption
> of the digital section**. Not good."

**That is precisely and independently the argument `[repo] hardware/module/power-entry.md`
makes for splitting D1 and D2** — "the instrument's current then flows through the
same diode as the module's analog rail and modulates its forward voltage by
~80 mV … ~20 cents of breath-correlated pitch bend." Same physics, same
conclusion, arrived at by a first-party Eurorack designer for the same reason.
`[repo] power-entry.md` says "There is no prior art for this split because there
is no prior art for the situation." **There is prior art for the physics**, and it
is the single most-cited open-hardware source in the format. The split is
correct; cite it.

**But the repo's other prior-art claim is wrong.** `[repo] hardware/module/power-entry.md`,
"Still open": "Mutable, Telex and others **fit PTCs on their entry rails**."
Mutable **stopped** fitting them — same source: "Note that I continue using the
polyfuse + shunt diode **only** for circuits which uses the V2164 — since this IC
absolutely needs to be protected against a missing V−". This module has no V2164.
So the strongest name in that sentence is evidence *against* adding PTCs to the
analog entry rails, not for it. Whether to add them is still a live question, but
the citation supporting it does not hold.

Also from the same source, relevant to `[repo] pitch-stage.md`'s reference
handling: "The 'wrong' way is to just use one of the supply rails and a voltage
divider … The 'correct' way is to use voltage reference ICs." `[repo] ADR 0006`
moved the pitch offset off a rail divider for exactly this reason. Confirmed.

---

## 14. Entry bulk capacitance — over the norm, and the two repo numbers disagree

**Rank: Low.**

Published norm: `[repo] ADR 0004:237` itself says "typically 10–100 µF per rail",
which matches what I could see of the corpus.

`[repo]` **The repo contradicts itself on the actual value:**
- `hardware/module/power-entry.md` draws `C1..C4 = 47 µF` each → **188 µF total**,
  and says "Entry bulk is 4 × 47 µF, which is 2–5× the surveyed norm of 10–22 µF."
- `hardware/bom.csv` C-BULK-RAIL says "**100uF (+12V)** / 47uF (−12V, +5V)" →
  `[calc]` 100 + 47 + 47 + 47 = **241 µF total**, with an explicit and good reason
  (unbalanced rail decay pulling the jacks toward −12 V at power-down).

The BOM is the later and better-reasoned version; `power-entry.md`'s diagram and
its "Still open" note are stale. Reconcile.

Either way the case-wide inrush point stands and the repo already makes it
(`power-entry.md`: "it adds to everything else in the case"). At 241 µF this
module contributes roughly 10–20× a Mutable module's entry bulk `[from memory for
the 10–22 µF comparator]`. In a large case at switch-on this is a real
contribution to PSU inrush. Not a showstopper; worth a line in the manual, and
worth checking the case PSU does not go into hiccup.

---

## 15. Injecting an audio-band switching load into the case's shared +12 V rail

**Rank: High.** CONVENTION — nothing forbids it; it will annoy the user's whole rack.

This is the behaviour most likely to surprise a Eurorack user, and it is the one
that reaches *other people's* modules.

`[repo] docs/decisions/0004-cv-interface-module.md:313-318` states the mechanism
plainly:

> "*A ferrite bead is a wire at the frequencies that actually matter here.* The
> WS2815 strips modulate their current at the PWM rate, around 2 kHz. A bead is a
> few hundred milliohms at 2 kHz and 47 µF does not hold a rail against a
> 200–400 mA square wave. The outcome is probably survivable …"

and `[repo] :320` adds that "fixing it locally and 'not exporting it to the rack'
cannot work by branching, because both branches are common upstream".

`[repo] docs/reference/latency-budget.md:122` gates it: "outgoing noise from the
local buck lands on every other module in the rack. Gates E6." **Credit where due
— the project has identified this and has a measurement gate on it.** What it does
not have is any specified mitigation. The only series elements between the
instrument's switching load and the case's +12 V pin are a ferrite the project
itself says is a wire at 2 kHz, and a Schottky.

**No module in the surveyed corpus does this.** Mutable's modules draw 50–120 mA of
essentially DC; the largest declared load I found, Endorphin.es Shuttle Control at
1000 mA/+12 V, is itself a *power supply* module and is expected to be treated as
one `[web] https://modulargrid.net/e/endorphin-es-shuttle-control-golden` (search
summary). A module that modulates 200–400 mA at ~2 kHz on the shared rail, in time
with the instrument's lighting, will be audible as a buzz in other modules'
outputs that changes when the lights change — and the user will blame whichever
module they can hear it in.

**Actions:**
1. E6 must measure at the **bus connector**, not just at the module — scope the
   +12 V pin with the instrument running and the strips at a realistic duty.
2. `L-BUCK-IN` already exists (`[repo] bom.csv`, 10–47 µH, and the repo correctly
   notes it needs damping). The equivalent filter is needed on the **module's**
   umbilical branch too, facing the rack, not only at the instrument end.
   `[repo] power-entry.md` "Still open" flags the damping question but frames it
   as an instrument-side stability problem, not as a rack-emissions problem.
3. `[repo] ADR 0004:326` says the bulk should go "at the LED feed point, where the
   current actually swings". Correct, and it is the highest-leverage fix — but it
   reduces what reaches the module, it does not filter what leaves it.

---

## 16. Assorted repo inconsistencies found while checking the above

**Rank: Low each**, but they are the kind that reach the board.

| Element | Conflict |
|---|---|
| Panel LED drive | `[repo] hardware/module/power-entry.md` and `digital-and-supervision.md` both show **820 Ω to bus +5 V**, sharing a node with the 74AHCT125 `OE` pins and the LM311 collector. `[repo] bom.csv` R-LED-PANEL says **"2k2 … ~4mA from the module's +12V analog rail. Was 820R from bus +5V when it shared a node with the level shifter's OE pins; that node is gone with the comparator."** The BOM is later and the comparator is deleted — the two schematic pages are stale and still draw the deleted comparator. |
| Presence comparator / LM311 | `[repo] digital-and-supervision.md` still draws the LM311 and the 74HC123 in its main circuit diagram, then says in prose that both are deleted. `[repo] bom.csv` C-DECOUPLE (qty 21) still counts "LM311 on ±12V = 2". Someone stuffing the board from the drawing will fit deleted parts. |
| +12 V draw | `[repo] ADR 0004:248` says ~320 mA total; `[repo] ADR 0005`'s load table implies 404 mA typical. See §11. |
| Entry bulk | 188 µF (`power-entry.md`) vs 241 µF (`bom.csv`). See §14. |
| Level shifter rail | `[repo] bom.csv` R-SPI-PULL says the **DAC-side CS pulls to AVDD (5.21 V), not bus +5 V**, with an explicit reverse-ribbon rationale. `[repo] digital-and-supervision.md` draws the DAC-side pulls without stating the rail. Given §10, resolving this by moving the whole buffer to 5.21 V makes the question disappear. |

None of these is a standards question; all of them will produce a wrong board if
the schematic pages are used as the build document, which is what they look like.

---

# Summary table

| # | Design element | Rank | Kind | One line |
|---|---|---|---|---|
| 9 | 16-pin header, reverse insertion | **Showstopper** (analysis) / High (consequence) | HARD | On a 16-pin reversal the module's GND lands on bus +12 V and +5 V; the series Schottkys are not in that path. The repo's "kills the buffer and nothing else" is wrong. |
| 3 | Panel height budget | **High** | HARD | 107 mm is asserted, never derived; bottom-up I get ~115 mm against 110 mm available. 1:1 paper check is now load-bearing. |
| 10 | Bus +5 V requirement | **High** | CONVENTION + compat | Needed by one $0.30 buffer, whose threshold margin is *better* on the local 5.21 V rail. Costs case compatibility and forces the 16-pin header. |
| 11 | Current draw declaration | **High** | CONVENTION | Bounded worst **1045 mA on +12 V** — 87 % of a Doepfer 1200 mA supply, 3.4× the 8HP FH-2. Declare it FH-2-style. |
| 12 | D2 = 1N5817 at a 1.0 A limit | **High** | HARD | Diode rated 1.0 A, protection circuit designed to hold 1.0 A. Zero margin. Use 1N5822/SS34. |
| 15 | Audio-band load on the shared rail | **High** | CONVENTION | 200–400 mA square wave at ~2 kHz onto the case +12 V, no specified attenuation. Unique in the corpus. |
| 2 | Panel mounting holes/slots | Medium | HARD | Not specified anywhere. 3 mm from edges, 122.5 mm centres, Ø3.2 mm / oval slot. |
| 5 | etherCON PCB notch | Medium | HARD | 26 mm notch in a 35 mm board = 4.5 mm webs, on 2 layers, carrying the isolated 360 mA–1 A `PWR_GND`. |
| 6 | Depth / front-protruding etherCON | Medium | CONVENTION | ~40 mm depth is fine; a latching Cat5e plug out the front will fight case lids. |
| 8 | Red stripe marking, CV/Gate pins | Medium | CONVENTION | No stripe marking specified; pins 13–16 never mentioned. Both are one-line fixes. |
| 4 | 20 mm knobs at 8HP | Low | HARD | Two 20 mm knobs do not fit side by side in 40.34 mm. 16 mm max. |
| 7 | Jack panel holes, switch pin, torque | Low | CONVENTION | 6 mm hole not written down; switch-pin treatment not stated; no published torque figure exists (datasheet unreachable). |
| 13 | Mutable PTC citation | Low | — | Mutable stopped using polyfuses except for V2164 circuits. The D1/D2 split is independently confirmed by the same source. |
| 14 | Entry bulk | Low | CONVENTION | 188 vs 241 µF between two repo documents; either is 2–10× the norm. |
| 16 | Stale schematic pages | Low | — | Deleted LM311/74HC123 still drawn; LED resistor/rail disagrees with BOM. |
| 1 | 8HP = 40.34 mm +0/−0.2 | Note | HARD | Confirmed exactly right, tolerance direction included. |

---

# What the module gets right, confirmed independently

Worth stating, because a cold review that only lists faults is misleading:

- **The HP formula and its one-sided tolerance** (§1) — exactly right, and most
  projects get the tolerance wrong.
- **The D1/D2 split** (§13) — the physics is confirmed first-party by Mutable
  Instruments, who abandoned polyfuses for the same reason.
- **The load switch** (§11) — bounding the umbilical fault at 1.0 A is what makes
  it safe to put this module in someone else's case at all. No conventional module
  needs this; this one does, and it has it.
- **etherCON max 4 mm panel thickness** (§5) — correctly caught, and correctly
  propagated to the instrument-end backing-plate decision.
- **1 kΩ series resistors on every output** — the universal Eurorack convention,
  and `[repo] bom.csv` R-OUT-PROT's ≥500 mW rating argument (citing Mutable's own
  ≥200 mW output resistor spec) is better than the convention.
- **Shrouded keyed power header** — and after §9, it is doing more work than the
  project realised.

---

# Verification debts created by the blocked network

These must be closed against primary sources by someone with an unrestricted
browser, before the panel DXF is cut or the board is laid out:

1. **`https://doepfer.de/a100_man/a100t_e.htm`** — the 16-pin pinout table in §8
   is reconstructed from two secondary sources, not read off Doepfer.
2. **Neutrik NE8FDP / etherCON D-series drawing** — flange height, exact cutout
   diameter, screw-centre spacing, and depth behind panel. §3's height budget and
   §6's depth figure both rest on `[from memory]` values.
3. **Thonkiconn / QingPu WQP-PJ398SM datasheet** — panel hole (6 mm is confirmed
   by a vendor page, not a datasheet), nut torque (no figure found anywhere),
   panel-to-PCB standoff height.
4. **1N5817 datasheet** — confirm the 1.0 A average rating and its stated lead
   temperature, then size D2 properly (§12).
5. **Alpha 9 mm vertical pot drawing** — bushing thread and panel hole diameter,
   for the DXF.
6. **Eurorack panel mounting slot geometry** from a published panel DXF (§2).
