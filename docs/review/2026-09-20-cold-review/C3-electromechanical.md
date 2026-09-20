# C3 — Electromechanical review

**Scope:** every electromechanical part in `hardware/bom.csv` — connectors, switches, jacks,
potentiometers, cable, LED strip, panel and mounting hardware. Plus the hardware that should
be in the BOM and is not.

**Sandbox note on sourcing.** `neutrik.com`, `thonk.co.uk`, `mouser.com`, `farnell.com`,
`rs-online.com`, `sdiy.info`, `exploding-shed.com`, `docs.waveshare.com` and most vendor
domains are blocked by this environment's egress proxy, so primary datasheet PDFs could not
be opened. Where a figure below came out of a search-engine abstract of a vendor page I say
so and call it **verified (secondary)**; where it is my own recall I say **from memory** and
do not dress it up. Two dimensions that the design genuinely turns on could not be obtained
at all and are marked **UNOBTAINED** — they are listed first in §14 as the things to fetch
before any panel or CAD work.

---

## Verdict table

| Ref | Specified part | Verdict | One-line reason |
|---|---|---|---|
| `J-UMBILICAL` | Neutrik etherCON D-series chassis, variant TBD, ×2 | **CHANGE** | "Solder-tag variant" does not exist; the real choice is feedthrough / PCB-mount / IDC, and PCB-mount forces the module PCB to 24 mm behind the panel |
| `CABLE-UMB` | "Cat5e STP patch lead, stranded, ~2 m", ×2 | **CHANGE** | No AWG, no jacket, no OD; OD must be 5–8 mm to fit the etherCON carrier's gland, which rules out slim 28 AWG leads |
| — | etherCON cable carriers | **MISSING** | 4 × NE8MC-class needed (2 per cable); without them the latch and strain relief that justified etherCON do not exist |
| `SW1-n` | Gateron KS-33 Red linear, 18 | **KEEP** | 12.2 mm / 1.70 mm / 3.00 mm all confirmed against vendor listings; right switch for the duty |
| `CAP1-n` | Tai-Hao MT165-MX 16.5 mm, 18 (4 × 5-packs) | **KEEP** | Explicitly listed as Gateron Low Profile 2.0/3.0 compatible; 20 caps covers 18 keys |
| `PLATE-TOP` | Aluminium key plate, thickness open | **UNVERIFIED** | Clip-engagement thickness still unknown; extend the M1 coupon to a thickness ladder, not just a kerf ladder |
| `J-CV` | PJ398SM (Thonkiconn), ×6 | **KEEP** | 9.0 × 10.45 mm body fits two columns in 6HP with room; de-facto standard |
| `POT-BREATH` | Alpha 9 mm vertical PCB, B50k, ×2 | **KEEP** | Body fits; the *knob* is the constraint, not the pot |
| — | Knobs for `POT-BREATH` | **MISSING** | Two knobs side by side in 30.18 mm caps knob diameter at ~13 mm — must be specified, not discovered |
| `SW-POWER` | SPST sub-miniature toggle, 6 mm bushing | **CHANGE** | Now a dry-circuit signal switch with no wetting current; specify gold contacts or provide ~1 mA |
| — | Panel power LED + series resistor | **MISSING** | ADR 0004's panel layout has an LED; the BOM has no LED and no resistor |
| `J-PWR-EURO` | 16-pin shrouded keyed IDC header | **KEEP** | Correct — the module *requires* +5 V, which the 10-pin bus omits |
| — | 16-way ribbon, 16-pin **both ends** | **MISSING** | Most cases ship 16→10 cables, which do not carry +5 V. Module dead on arrival |
| `LED-SIDE` | WS2815 60/m, 2 × 420 mm | **KEEP** | 10 mm strip fits the side channel with margin; 25 LEDs/side lands on a cut mark |
| `U-LVLSHIFT` | 74AHCT125 as WS2815 data shifter | **CHANGE (probable)** | WS2815 datasheet V_IH = 0.7 × VDD = **8.4 V** at 12 V. 5 V AHCT does not meet it on paper |
| `F-POLY` | PPTC 1206, 500 mA hold | **CHANGE** | Derates to ~0.3–0.35 A at the cavity's 50–60 °C against a 275–430 mA load — nuisance trip |
| `MECH-GNDBOND` | Ring terminal + M3 hardware | **CHANGE** | Plain ring terminal on aluminium oxide is not a bond; needs a serrated washer, stainless, and a measured resistance |
| `J-USB` | "not-needed — dev boards carry these" | **CHANGE** | In a body that cannot be reopened, every flashing cycle loads a dev-board SMT receptacle with no mechanical backup |
| `PANEL` | 2 mm aluminium, **30.0** × 128.5 mm | **CHANGE** | ADR 0004 uses 30.18 mm. One of the two is wrong; 30.18 is the (n × 5.08) − 0.3 figure |
| — | Tail end cap / umbilical backing plate | **MISSING** | The laminated stack in ADR 0009 has no end caps at all, and the etherCON has nothing to mount to |
| — | U-bolt, backing plate, strap hardware, neck strap | **MISSING** | ADR 0009 calls this "the highest-stress point in the entire build" and there is no line item |
| — | Module mounting screws, washers, PCB standoffs | **MISSING** | Including the standoffs that implement "brace the etherCON to the PCB" |
| — | Internal loom cable, anchors, service loops | **MISSING** | ADR 0009 mandates a ground return per key-chain signal and two spare conductors; no cable is specified |
| — | LED strip mechanical retention | **MISSING** | 3M tape in a 45–55 °C sealed cavity, mounted vertically, for the life of the instrument |
| — | Breath tube retention at the sensor barb | **MISSING** | 400 mm of silicone tube in a constantly-moving body, on a push-fit port that must never leak |
| — | Jack nuts / nylon washers, pot nuts | **MISSING** | Minor, but PJ398SM is sold both with and without nuts |
| — | Umbilical cable clip to the neck strap | **MISSING** | The single cheapest thing that extends the life of the most-abused item in the system |
| `TRIM-PITCH` | Multiturn cermet trimmers, ×2 | **KEEP** | Correct class of part; no mechanical concern |

---

## Findings

### 1. The etherCON "solder-tag variant" in ADR 0004's open question does not exist — MAJOR

**ADR 0004 closes with:** *"Feedthrough (NE8FDP-class) … A solder-tag or PCB-mount variant
avoids that and costs a fiddlier assembly. Decide with the datasheets in hand at E12 and M7."*

There is no solder-tag etherCON chassis connector. The chassis range, as far as vendor
listings show, is:

| Variant | Termination | Flange | Notes |
|---|---|---|---|
| **NE8FDP / NE8FDP-B** | Feedthrough (RJ45 socket on the rear) | D | Max panel thickness **4 mm**; screws included. *Verified (secondary)* |
| **NE8FDV / NE8FDV-B** | Vertical PCB mount | D | **PCB sits 24 mm behind the panel.** *Verified (secondary)* |
| **NE8FDV-YK / NE8FDV-YK-B** | **IDC, tool-free** | D | Penn Elcom lists as "D Series IDC". *Verified (secondary)* |
| **NE8FDY-C6 / -C6-B** | **IDC, gas-tight, tool-free**, CAT6 | D | *Verified (secondary)* |
| **NE8FDX-P6 / -B** | Feedthrough, **shielded**, CAT6A | D | *Verified (secondary)* |
| **NE8FBH / NE8FBV (+ -C5, -C6, -LED)** | Horizontal / vertical PCB mount | **B ("space saving")** | Max panel thickness **3 mm**; vertical variant also at 24 mm. *Verified (secondary)* |

So the decision is not "feedthrough vs solder tag". It is:

- **Instrument end → `NE8FDY-C6` or `NE8FDV-YK` (IDC).** This is the answer ADR 0004 was
  reaching for and did not know existed. Tool-free, gas-tight IDC termination of eight
  conductors, D-shape flange, **no second mating interface in the +12 V path or the analog
  pair**, and no soldered wire bundle behind a connector inside a body that is bonded shut.
  It is strictly better than both options the ADR considered.
- **Module end → `NE8FDV` (vertical PCB mount, D).** This *is* "braced to the PCB" — the
  connector is a PCB part, so the load path runs into the board by construction rather than
  by a bracket someone has to remember. See finding 3 for what it costs.

**Intermate trap, and it is a real one.** Vendor copy states that `NE8FDY-C6` intermates only
with `NE8MC6-MO`, `NKE6S-*` and generic RJ45 plugs, and that `NE8FDX-P6` does **not**
intermate with `NE8MC6-MO`. The two ends of this system must therefore be chosen as a
*family*, not as two independent decisions at two different milestones (E12 and M7, per the
ADR). If the module end lands on `NE8FDX-P6` and the instrument end on `NE8FDY-C6`, one cable
cannot serve both. *Verified (secondary); confirm against Neutrik's own intermate matrix.*

**Confidence:** high on the variant list, high on the intermate warning, medium on which
exact part numbers remain in production.

---

### 2. The "3.19 mm each side" figure measures the bore, not the part — MAJOR (correction, not a reversal)

ADR 0004: *"A 23.8 mm hole in a 30.18 mm panel leaves two strips of aluminium 3.19 mm wide."*

**The arithmetic is right.** (30.18 − 23.8) / 2 = **3.19 mm**. And 30.18 mm is right:
(6 × 5.08) − 0.3 = 30.18, +0/−0.2. *Verified (secondary).*

**The figure is optimistic for three separate reasons.**

1. **The flange is wider than the bore.** The D-series flange is **31 × 26 mm**
   (*verified, secondary*). (30.18 − 26) / 2 = **2.09 mm** of panel visible either side of the
   connector. That is the number you look at, and it is the number that has to survive the
   panel-edge radius.
2. **The screw holes are unaccounted for.** The D-series takes two countersunk M3 fasteners
   (*verified, secondary*). Their positions within the 26 mm flange are **UNOBTAINED** — see
   §14. Whatever they are, they lie inside 26 mm, so the web between a screw hole and the
   panel edge is **≤ 2.09 mm and probably less**. If the connector is ever rotated 90° so the
   screws lie on the horizontal axis, the cutout group will not fit a 6HP panel at all. The
   orientation is therefore *forced*, and that should be written down before the DXF is cut.
3. **Tolerances stack the wrong way.** Panel width is +0/−0.2. The common practical drill is
   24.0 mm, not 23.8 (*verified, secondary — the 23.8 figure is the precise D spec, 15/16″ =
   23.81 mm is what people actually use*). Laser kerf adds ~0.1 mm. Worst case:
   (29.98 − 24.1) / 2 = **2.94 mm** of bore-to-edge material.

**The ADR's conclusion — brace it to the PCB — is correct, and here is the number behind it.**
Out-of-plane second moment of area, 2 mm panel:

- Full width: 30.18 × 2³ / 12 = **20.1 mm⁴**
- Two 3.19 mm strips: 2 × (3.19 × 2³ / 12) = **4.25 mm⁴** → **21 % of the full panel**

At the flange width it is 2 × (2.09 × 2³ / 12) = 2.79 mm⁴, **14 %**. So the connector band is
a seventh as stiff as the panel either side of it, in the one axis the cable loads. Bracing is
not belt-and-braces; it is the load path.

**Severity:** major. **Confidence:** high on the arithmetic, high on the conclusion.

---

### 3. "Brace it to the module PCB" is not buildable as a single-board module — MAJOR

This is the finding I would act on first, because it changes the module's board count and
therefore its schematic partitioning.

- PJ398SM jacks are vertical PCB-mount, so the jack PCB sits **~6–7 mm** behind the panel
  (*from memory; the exact body height above PCB is **UNOBTAINED***).
- The etherCON D chassis body extends roughly **30–40 mm** behind the panel
  (*from memory; **UNOBTAINED***), and the PCB-mount variants explicitly place their PCB at
  **24 mm** (*verified, secondary*).

A single PCB parallel to the panel at ~7 mm therefore passes straight through the middle of
the etherCON body. To clear it you need a notch about **26 mm wide × 31 mm tall**. A 6HP module
board is at most ~28 mm wide and realistically 25–26 mm. **A 26 mm notch severs the board.**

Three ways out:

- **(a) Two boards.** Front board at ~7 mm carries the six jacks, two pots, the toggle and the
  LED. Main board at 24 mm carries `NE8FDV`, the DAC, op-amps, the bus header and everything
  else. Joined by a 2×5 or 2×8 0.1″ header and two M3 standoffs. This is the clean answer and
  it makes "braced to the PCB" true by construction.
- **(b) Connector at the extreme end of the panel**, PCB starting below it, with a folded
  aluminium or 3D-printed bracket tying the connector body to the board. Keeps one board;
  adds a bespoke bracket to a project with no CNC.
- **(c) Feedthrough `NE8FDP` panel-mounted with the board notched *around* the bottom or top
  of the connector** — only works if the connector is at a panel extremity, i.e. (b) again.

Recommend **(a)**, and note that it also resolves the module depth question: 24 mm connector
+ 1.6 mm board + ~8 mm of THT lead/standoff + the 16-pin header and its ribbon bend radius
≈ **55–65 mm total module depth**. Fine for a normal case, **too deep for a skiff**. That
should be stated in the README's design scope alongside "the target rack has a generous
supply".

E12's done-when text — *"etherCON braced to the PCB, not carried by two 3.19 mm strips"* —
should be rewritten to name the mechanism, because as phrased it can be signed off by a
zip tie.

**Severity:** major. **Confidence:** high on the geometric conflict, medium on the exact
depths pending the drawing.

---

### 4. The 6HP panel closes, but only just, and not with the knobs anyone would reach for — MAJOR

ADR 0004: *"Roughly 107 mm of ~110 mm usable height — full but workable."*

Usable height is **108.5 mm**: 128.5 mm panel, with 10 mm of keep-out at top and bottom for
the rails (*verified, secondary*). So "~110" is about right, slightly generous.

Here is the budget with real part sizes:

| From top | Item | Claim (mm) | Running (mm) |
|---|---|---|---|
| 0 | keep-out | 10.0 | 10.0 |
| | etherCON D flange | 31.0 | 41.0 |
| | clearance for the NE8MC latch release (you press it with a fingertip) | 4.0 | 45.0 |
| | toggle + LED row (side by side: 6.1 mm bushing hole + 8 mm bezel = 15 mm wide, fits) | 12.0 | 57.0 |
| | gap | 4.0 | 61.0 |
| | knob row, Ø12 mm knobs + 2 mm | 14.0 | 75.0 |
| | gap | 5.0 | 80.0 |
| | 3 jack rows at 13 mm pitch | 39.0 | 119.0 |
| | bottom keep-out starts at | | **118.5** |

**It overruns by 0.5 mm at a 13 mm jack pitch**, and closes with ~5 mm to spare at an 11 mm
pitch — which one builder reports as their tightest practical vertical spacing
(*verified, secondary; 13 mm horizontal / 11 mm vertical quoted as a minimum requiring a test
panel*). So the panel is buildable and the ADR's "full but workable" is fair, but there is no
slack at all and the instruction *"print the panel at 1:1 on paper and check it"* is load-bearing
rather than a nicety.

**The knobs are the part that actually does not fit.**

- Alpha 9 mm RD901F: body ~9.7 mm, bushing **M7 × 0.75**, **panel hole 7.5 mm**, bushing
  length 5 mm, shaft 6.35 mm × 15 mm overall from the body. *Verified (secondary).*
- Two pots side by side on a 30.18 mm panel sit at best on **15 mm centres**, leaving
  30.18/2 − 7.5 = **7.59 mm** from each pot centre to the panel edge.
- A knob of diameter *D* needs *D*/2 ≤ 7.59 → **D ≤ 15.2 mm to not overhang the panel**, and
  D ≤ 15 mm to not touch its neighbour — i.e. the two knobs would be *touching* at 15 mm.
- For a usable 2 mm gap between knobs and 1 mm of panel showing at each edge:
  **D ≤ 13 mm**, and **12 mm is the sensible number**.

That excludes essentially every knob a Eurorack builder owns: Rogan 1PS ≈ 15.8 mm,
Davies 1900H ≈ 14.3 mm, Alpha KM-16 ≈ 16 mm (*all from memory*). What works is a small
knurled aluminium or Sifam-style 11–12 mm knob.

**Also: specify the shaft.** Alpha 9 mm pots ship both as **6.35 mm round metal shaft** and as
**18-tooth knurled plastic** (*both verified, secondary, from different vendor listings*). The
knob must match, and the BOM line says neither.

**Recommendation.** Either (i) specify a 12 mm knob and an 18T or D-shaft explicitly, or
(ii) move the umbilical connector to the **bottom** of the panel, which frees the top for the
knobs *and* makes the cable hang away from the controls instead of draping over them — the
NE8MC carrier is a ~60 mm cylinder projecting straight out of the panel, and at the top of the
panel the cable falls across both knobs and all six jacks. (ii) is free and is the better
answer ergonomically; it costs nothing but a note in the panel DXF.

**Severity:** major (the knobs), moderate (the height). **Confidence:** high.

---

### 5. The jacks and the horizontal budget — KEEP, with the numbers

Measured out of a published KiCad footprint for the WQP-PJ398SM
(`nickajeglin/Eurorack-pcbs`, fetched and read directly — **verified, primary**):

- Body footprint in the panel plane: **9.0 mm wide × 10.45 mm long** (Y from 2.03 to 12.48).
- Courtyard: 10.0 × 14.83 mm.
- Bushing keepout Ø3.6 mm radius region centred 6.48 mm along the body.
- Panel hole **6 mm**, thread **M6 × 0.5**; 6.5 mm is the commonly drilled figure to absorb
  nut and panel tolerance (*verified, secondary*).

Two columns at 15 mm centres: outer body edge at 7.5 + 4.5 = 12.0 mm from centreline, against
15.09 mm of half-panel → **3.09 mm of panel outboard of each jack body**. M6 nut across
corners ≈ 9.2 mm (A/F 8 mm) → nut edge at 12.1 mm, **2.99 mm to the panel edge**. Comfortable.

Three rows need ≥ 10.45 mm pitch for the bodies alone; 12–13 mm is right, 11 mm is the floor.

**Ratings.** These are 3.5 mm mono switched jacks with beryllium-copper springs; contact
current and contact resistance are not published by QingPu in anything I could reach
(**UNOBTAINED**). It does not matter here — the CV outputs run through 1 kΩ series resistors
at ≤10 V, so contact current is ≤10 mA and contact resistance of a few tens of milliohms is
four orders below the series resistor. The only electrical risk is *intermittent* contact
during patching, which the `D-JACK-CLAMP` BAV99s already cover.

**Mating cycles** are the real duty question and are also unpublished. A one-off instrument's
jacks see hundreds to low thousands of insertions over their life; PJ398SM is the part the
whole Eurorack ecosystem runs on at that duty. **KEEP.**

Missing: **nuts** (sold both ways) and **nylon washers** to protect a brushed or anodised
panel. Add a line.

---

### 6. The umbilical cable is specified in prose and not in parameters — MAJOR

`CABLE-UMB`: *"Cat5e STP patch lead, STRANDED, ~2m"*, qty 2, status open.

Stranded is correct and the reasoning is correct. But three parameters are missing and each
one can be got wrong by buying "a Cat5e patch lead":

**(a) Conductor gauge.** Patch leads are sold in 24, 26 and 28 AWG stranded
(*verified, secondary*). ADR 0005's drop table assumes 24 AWG at 0.337 Ω round trip for 2 m,
which checks out: 24 AWG at 0.0842 Ω/m × 4 m = **0.337 Ω**, × 250 mA = **84 mV**. Correct
arithmetic.

At the *corrected* current budget the table should be re-run:

| AWG | Ω/m | 4 m loop | Drop at 430 mA | Arrives as |
|---|---|---|---|---|
| 24 | 0.084 | 0.337 Ω | 145 mV | 11.86 V |
| 26 | 0.134 | 0.536 Ω | 230 mV | 11.77 V |
| 28 | 0.212 | 0.850 Ω | 365 mV | 11.64 V |

*(conductor resistances from memory; stranded adds ~5–20 % over solid.)*
**None of these matters electrically** — the buck needs >6 V in. So gauge is not an electrical
constraint, which is worth saying plainly because ADR 0005 implies it is. Gauge matters for
(b) and (c).

**(b) Outer diameter, which is a hard constraint.** The etherCON cable carrier ships with
cable protection elements for **5 mm or 8 mm** cable diameter (*verified, secondary — NE8MC*).
A slim 28 AWG patch lead is typically 3.5–4.2 mm OD and **will not be gripped by either
element**, which deletes the strain relief that is the entire reason etherCON was chosen over
bare 8P8C. **Specify OD 5.0–8.0 mm**, which in practice means a normal-jacket 24 or 26 AWG
lead, not a data-centre slim lead.

**(c) The plug has to fit inside the carrier.** The carrier "accepts the most common RJ45
plugs" (*verified, secondary*) but moulded strain-relief boots generally do not fit. Either
buy plugs without boots and crimp, or buy a ready-made etherCON assembly.

**Recommendation.** Replace the line with something orderable:

> **CABLE-UMB** — Tour-grade stranded **F/UTP Cat5e**, **26 AWG**, TPE or PUR jacket,
> **OD 5.5–6.5 mm**, 2 m, terminated with bootless RJ45 plugs, made up with etherCON cable
> carriers at both ends. Reference product: TMB ProPlex CAT5e 26 AWG SF/UTP
> (*verified as an existing tour-grade product, secondary; its exact OD is **UNOBTAINED***),
> Van Damme or Klotz equivalents. Qty 2 cables, 4 carriers. **Consumable.**

**(d) The shield has nowhere to go.** The review's R38 asked for the shield bonded at both
ends and tied to the aluminium key plate. `NE8FDP` is a *feedthrough* — the shield path
depends on whether the plug's shield reaches a shielded jack, and the plain CAT5e feedthrough
is unshielded. If shield continuity is actually wanted, the part is **`NE8FDX-P6`** (shielded
CAT6A feedthrough) — and note its intermate restriction from finding 1. If it is not wanted,
say so in ADR 0004 and stop specifying STP. Right now the BOM asks for a shield the connector
cannot terminate.

**Severity:** major. **Confidence:** high on (b) and (d), high on the drop arithmetic.

---

### 7. The umbilical's actual duty cycle, and the one cheap thing missing — MODERATE

This is the most-abused item in the system, so taking it seriously:

- **Mating cycles.** Neutrik quotes **>1000 mating cycles** for the etherCON chassis, with
  contacts in bronze CuSn8 and **0.2 µm gold over nickel** (*verified, secondary*). For
  context, generic enterprise RJ45 is specified at 750–1000 cycles, and 0.2 µm = 7.9 µin is
  *thin* against the 50 µin quoted for robust connectors (*verified, secondary*). For an
  instrument plugged in a few times a week — say 200 cycles/year — that is a decade. **Not a
  constraint.** What wears first is the cable's plug, which is a consumable anyway. Good.
- **Contact current.** ~1.5 A per contact (*the figure ADR 0004 and the review both use;
  I could not re-verify it, so treat as secondary*). +12 V rides one conductor and its return
  another, at 275–430 mA → **19–29 % of rating**. Ample.
- **Hot-plug.** The review's R37 (30 A inrush) is doubly dead: the resolution log already
  killed the arcing claim, and the `TPS2553` sits **upstream of the connector** on the module
  side, so the instrument's bulk capacitance charges through the load switch's ~500 mA limit
  whatever the mating order does. Worth writing into ADR 0004 as the answer to R37, because
  right now the log rebuts only the arc and not the inrush.
- **Mating order (R28) is still live, at reduced severity.** etherCON has no sequenced
  contacts. If +12 V makes before `PWR_GND`, the return hunts for a path and `AGND` — a
  sense-only line into the in-amp's reference — is one. Bounded at the load switch's 500 mA
  for a millisecond or two. Two mitigations, both nearly free: make "switch off before
  plugging" the documented rule (it is already the only switch in the system, one reach away),
  and put **back-to-back diodes or a 10 Ω link between AGND and PWR_GND at the instrument
  end** so a mis-sequenced mate cannot drive the full return through the sense conductor.
- **Flex.** This is the failure mode that actually arrives. Cat5e's minimum bend radius is
  ~4 × OD for patch use (*from memory*) — **~25 mm at 6 mm OD**. The cable leaves the tail
  and immediately falls under its own weight (2 m of Cat5e ≈ 70 g), so the bend right at the
  carrier's boot is the fatigue point, cycled every time the instrument moves.

**The missing part is a cable clip.** Anchor the umbilical to the **neck strap** ~150 mm above
the connector, so the swinging mass of cable below is decoupled from the connector and the
bend at the boot is held above its minimum radius. A nylon P-clip or a hook-and-loop strap
tie, one part, pennies, and it roughly doubles the life of the consumable. Add it to the BOM
and to M7's "strain-relieved" done-when, which currently has no mechanism behind it.

**Severity:** moderate. **Confidence:** high.

---

### 8. The instrument tail face: the arithmetic closes and the stack does not — MAJOR

ADR 0009's two claims both check out:

- *"roughly 26 × 31 mm on a face that measures 57 × 38 mm"* — flange **31 × 26 mm**
  *verified (secondary)*.
- *"about 3.5 mm of material above and below the cutout"* — (38 − 31) / 2 = **3.50 mm** ✓
  (this is flange-referenced, which is the right reference).
- *"roughly 31 mm beside the flange"* for the USB-C — 57 − 26 = **31 mm** ✓.

**But run the bore against the layer stack and it comes apart.** ADR 0009's stack is
aluminium 2 / oak top 6 / cavity / oak bottom 8 / thumb plate 2 (inboard). A Ø23.8 mm bore
centred in the 38 mm face leaves (38 − 23.8)/2 = **7.10 mm** above and below the *hole*:

- **Above:** 2 mm aluminium + 6 mm oak = 8 mm of material exists. The bore eats 5.10 mm of
  the oak, leaving **0.90 mm of oak** under the plate.
- **Below:** the outer face is 8 mm of oak. The bore eats 7.10 mm of it, leaving **0.90 mm of
  oak**.

Under a millimetre of oak, top and bottom, at the end of an instrument that hangs on a strap
and has a cable tugging sideways on it. ADR 0009 is right that "oak is not what should be
carrying it" — this is *how* right.

**And there is no part for the connector to mount to.** ADR 0009 describes the stack as
aluminium plate, oak top, acrylic sides, oak bottom, thumb plate. **The ends are open.** There
is no tail end cap in the ADR and none in the BOM. The etherCON needs a flat face 26 × 31 mm
with two tapped or clearance M3 holes and it needs that face to be structural — which means:

> **MISSING: `CAP-TAIL`** — 2–3 mm aluminium tail end cap, full 57 × 38 mm section, carrying
> the etherCON cutout and the USB-C opening, tied by screws into the aluminium key plate and
> the thumb plate so the load path runs into the plate stack rather than into oak end grain.

Two hard constraints on that cap:

1. **Thickness.** The etherCON D is rated for **max panel thickness 4 mm**
   (*verified, secondary*; the B-series is 3 mm). A 2–3 mm cap is fine. **Mounting the
   connector directly through 6 mm of oak is not possible** — the part physically will not
   accept it. That is a hard stop nobody has written down.
2. **The screws.** Wherever the D-series M3 holes fall, they are within 26 mm and within
   13 mm of the bore centre vertically, so they land in the ~0.9 mm oak zone identified above.
   They must go into the metal cap, not through it into oak.

**Severity:** major. **Confidence:** high on the arithmetic, high on the missing part, high
on the 4 mm panel-thickness limit.

---

### 9. The tail is also over-subscribed in depth — MODERATE

ADR 0009's length table allows **40 mm** for *"Tail: connector + strain relief (short)"*.

Into those 40 mm must go: the etherCON body (**~30–40 mm behind the panel**, *UNOBTAINED*),
the real-time board (which must reach the tail face for its USB-C *and* sit at the very tip
for acceleration sensitivity *and* shine its 8×8 matrix through the underside window), the
carrier PCB under it with its own 22 mm cutout, and the internal wiring.

The etherCON alone takes **26 of 57 mm of width and 31 of 38 mm of height for 30–40 mm of
length** — i.e. most of the tail's cross-section for most of its allocated length. The
real-time board and its carrier have to live beside it in the remaining ~28 mm of width.

Expect the tail to want **55–65 mm**, not 40. The table's slack is 31 mm, so it survives, but
it survives by consuming most of it — and the display band already halved that slack once.
Re-run the table with a real tail figure before M4, and note the interaction: if the etherCON
moves to a **B-series PCB-mount** part (finding 12) its behind-panel depth and cutout both
shrink.

**Severity:** moderate. **Confidence:** medium — the depth figure is unobtained and the
conclusion moves with it.

---

### 10. USB-C is marked "not-needed" and it is the part most likely to end the project — MAJOR

`J-USB`, `U-ESD-USB`, `SW-BOOT` are all *"not-needed — dev boards carry these"*, per ADR 0013.
For the ESD array and the buttons, fine. For the **connector**, no.

The instrument's only USB port is a surface-mount receptacle on a Waveshare dev board, itself
plugged into a carrier, inside a body **that is bonded shut**. Every flashing cycle and every
USB-MIDI session (E5 is a whole milestone built on it) puts an insertion force of 10–20 N
through that receptacle's solder joints (*force from memory*). USB-C receptacles are rated
around 10,000 cycles as a part — but that rating assumes the receptacle is mounted in a
chassis that takes the load, not cantilevered on a dev board on pin headers.

If that receptacle's pads lift, the instrument is unflashable and unrecoverable.

Three options, cheapest first:

- **(a) Bezel the plug, not the board.** Cut the tail-cap opening so the *plug's overmould*
  lands on the aluminium cap before the receptacle bottoms out, and bond the dev board's
  receptacle body to the carrier with epoxy. Costs one CAD feature. Requires knowing the
  plug's overmould dimensions at M4, which means choosing the cable you will use for the life
  of the instrument.
- **(b) Panel-mount USB-C pass-through** on the tail cap with a short internal cable to the
  dev board. A flanged pass-through receptacle (Amphenol U-Type / Adafruit-style panel mount)
  takes the load in the metal cap. Costs ~25 mm of internal length and one part — which
  finding 9 says you do not have.
- **(c) Accept it, and add a second path.** A 6-pin pad header on the carrier brought out to
  the tail for a serial programmer, as an in-case-of-emergency route. Free on a board being
  designed anyway, but it does not rescue USB MIDI.

Recommend **(a)** as the default and **(c)** as free insurance. Either way, change `J-USB`
from "not-needed" to a real line, because the current entry closes a question that is open.

**Severity:** major. **Confidence:** high on the risk, medium on the insertion force.

---

### 11. WS2815 level shifting: the datasheet says the specified part does not work — MAJOR

ADR 0014 and the BOM both flag *"VERIFY WS2815 threshold"*. Here is the verification.

The WS2815 datasheet specifies, for the DIN and SET pins
(*verified, secondary — quoted from the WS2815 datasheet*):

| | |
|---|---|
| V_IH | **0.7 × VDD** |
| V_IL | 0.3 × VDD |
| Hysteresis | 0.35 V |

VDD on a WS2815 is the **12 V** rail. 0.7 × 12 = **8.4 V**. A 74AHCT125 on a 5 V rail drives
about **4.6–4.9 V**. On the datasheet, that is **not a logic high** — it sits in the
undefined band between V_IL (3.6 V) and V_IH (8.4 V).

In practice a great many builds drive WS2815 from 5 V logic and work, because each pixel
regulates 12 V down to an internal 5 V logic rail and the real threshold appears to be
referenced to that. But ADR 0014 already wrote the right rule: *"'most' is not a basis for a
sealed build."*

**So treat 5 V as plan A and lay out plan B on the same board.**

- **Plan A:** 74AHCT125 at 5 V, as specified. Test with the *actual* strip, at the *actual*
  420 mm length, at the *actual* cable capacitance, **before M8 closes the body**.
- **Plan B, concrete:** a 12 V-rail gate driver in place of the AHCT gate — **TI UCC27517DBV**
  (SOT-23-5, VDD to 18 V, TTL-compatible inputs so 3.3 V drives it directly, ~13 ns
  propagation, 4 A drive into the strip's input capacitance). One per strip, or
  **UCC27524** (dual, SOIC-8) for both. *Part characteristics from memory — check the
  datasheet.* Avoid the obvious open-drain MOSFET-plus-pull-up: at 800 kHz the pull-up RC
  against the strip's input capacitance is the exact intermittency this is trying to avoid.
- **Lay both footprints.** The AHCT125's SOIC-14 and a SOT-23-5 driver can share a footprint
  region with two DNP resistors selecting the path. On a board inside a body that cannot be
  reopened, that is the cheapest insurance in the project.

Note this also affects `U-LVL-MOD` — the *same* 74AHCT125 part number is used at the module
for SPI, where 5 V is unambiguously correct. The "one part number across both boards" argument
in ADR 0004 is a nice-to-have, not a reason to accept an out-of-spec drive level.

**Severity:** major. **Confidence:** high that the datasheet says 0.7 × VDD; high that the
empirical picture is more forgiving; high that a sealed build should not rely on the
empirical picture.

---

### 12. WS2815 strip: the part fits, the mounting is missing — MODERATE

- **Width.** WS2815 60/m on a **10 mm** FPC, **2 mm** high for the IP30 version
  (*verified, secondary*). The side channel: 57 mm body, minus a centre column of ~16 mm for
  the 14 mm switch cutouts and bodies, minus 4 mm of acrylic per side →
  (57 − 16)/2 − 4 = **16.5 mm per channel**. A 10 mm strip plus the digital loom fits with
  ~6 mm to spare. **Closes comfortably.**
- **Cut length.** 60/m → 16.67 mm pitch → 420 mm is **25.2 LEDs**; cut at 25 → **416.7 mm**.
  Fine, and it lands on a cut mark. Two 420 mm runs from a 1 m strip ✓ (840 ≤ 1000).
- **Current.** ADR 0014's 12.1 W / 1.01 A for 50 LEDs full white implies **0.242 W per LED**,
  against the commonly quoted 0.3 W per WS2815 at 12 V (*from memory*). Slightly optimistic
  but the right order, and the 3 W thermal clamp swamps the difference.
- **Feed wiring.** WS2815 needs **four** conductors at the head — 12 V, GND, **DI and BI** —
  because the backup data line is only a backup if the first pixel's BI is driven. The BOM
  and ADR 0014 both talk about "one data line per strip", which is two of the four. Two
  strips → 12 V, GND, DI×2, BI×2 = **6 conductors minimum** down the body before ADR 0009's
  two mandatory spares. Worth stating, because the loom is hand-built once.

**What is missing is how the strip stays where it is put.** These ship on 3M adhesive tape.
The cavity runs 10–20 K above ambient by ADR 0014's own estimate, the strips are mounted
**vertically** on a side wall (shear loading on the adhesive, the worst case for tape creep),
and the instrument is shaken continuously for hours. Adhesive tape in that service will creep,
and a strip that peels inside a bonded body is unfixable.

> **MISSING: strip retention.** Either (a) a 3M **VHB** transfer tape with a primer-prepped
> acrylic surface, (b) a shallow retaining channel or lip cut into the spacer layer — free,
> since every layer is a 2D through-cut anyway, or (c) a bead of neutral-cure silicone along
> both edges after positioning. (b) is the one that costs nothing and fails safe.

Also missing: `C-STRIP-BULK` is specified as radial electrolytics *at each strip feed point* —
two 470–1000 µF radial caps loose in the side channel need mounting and their leads need
strain relief, in a body that moves. They belong on a small tag board or the carrier, not
flying on wires.

**Severity:** moderate. **Confidence:** high.

---

### 13. Key switches, caps and the plate — mostly KEEP, with corrected numbers

**The switch checks out.** Vendor listings for the Gateron **KS-33 Low Profile 2.0 Red**
give (*verified, secondary*):

| | BOM says | Vendor listings say |
|---|---|---|
| Height | 12.2 mm | **12.2 mm** ✓ |
| Pre-travel | 1.70 mm | **1.7 mm** ✓ |
| Total travel | 3.00 mm | **3.0 ± 0.2 mm** ✓ |
| Pins | 3-pin, SMD LED | ✓ |
| Materials | POM / PC / nylon | ✓ |
| Operating force | *not stated* | **45 ± 15 gf** |

So `docs/reference/ks33-geometry.md` is right on every published number it carries, which is
worth saying because that file is appropriately anxious about its own provenance. Add the
**45 ± 15 gf** figure — it is the number M1's "lighter spring for the thumb keys" question
turns on, and the KS-33 line's lighter option is the one to identify *before* ordering.

Two caveats:

- **Rated lifetime is UNOBTAINED.** Gateron publishes travel and force; I could not find a
  cycle rating for KS-33 in anything reachable. For a soldered switch in a bonded body this
  is the one spec you would want. Buy **spares now** — the same argument the project already
  accepted for the MPXV4006DP — because low-profile switch lines get discontinued and a
  **KS-33 Low Profile 3.0** already exists (*verified, secondary*), which means 2.0 is the
  older SKU.
- **Keycap clearance, not compatibility.** MT165-MX is listed as compatible with
  "Choc v2, Gateron Low Profile 2.0/3.0, and Cherry MX" (*verified, secondary*) — so the pairing
  is right. But KS-33 is separately documented as having clearance issues with some tall MX
  profiles (*verified, secondary*), which is exactly why the low-profile MT165 is the correct
  choice and a spare box of MX caps is not.

**Keycap retention is a non-issue, with one caveat.** MX cross-stem friction fit holds against
gravity by two orders of magnitude, and the caps are on the *outside* of the body, so a
detached cap is refittable even after bonding. The caveat is the **thumb-key recesses**: a
16.5 mm cap in a tight recess will rub. Size each recess ≥ **18 mm** in the cap's plan
directions, or use one shared recess per cluster.

**ADR 0009 has a keycap-pitch error worth correcting.** It says the MT165 caps
*"allow roughly 18–20 mm before caps collide, against standard 18 mm MX spacing."* Standard
MX **pitch** is 19.05 mm; 18 mm is the **cap** size. 16.5 mm caps collide at a **16.5 mm**
pitch, not 18. The design uses 24 mm, so nothing breaks — but if anyone later treats "18 mm"
as a floor they will leave 1.5 mm on the table per key across eleven keys.

**The left-thumb arc needs its ambiguity resolved.** ADR 0010: *"roughly 57 mm of travel down
the body with perhaps 15–25 mm of lateral deviation"* for four caps.

- If 57 mm is **first-to-last centre**: pitch = 57/3 = **19.0 mm** > 16.5 → **2.5 mm gap**.
  Closes, barely.
- If 57 mm is the **total extent including caps**: centres span 57 − 16.5 = 40.5 mm →
  pitch **13.5 mm** < 16.5 → **caps overlap**. Does not close.

One sentence in ADR 0010 fixes this and it is worth fixing before M2 draws anything.

**Plate thickness stays open, and the coupon should cover it.** ADR 0002 is right that 2 mm
defeats the clips and that the resolution is Gateron's clip dimension. Since that drawing is
unreachable from here too, note that **M1's test coupon can answer it empirically**: cut the
ladder of cutout sizes in **1.1, 1.5 and 2.0 mm** stock rather than in one thickness. That is
the same half-hour at the vendor's minimum order and it removes the dependency on a document
this project has failed to obtain twice.

**Confidence:** high on the switch specs, high on the pitch arithmetic, high on the cap
clearance point.

---

### 14. The thumb-key inset probably does not exist at 8 mm of oak — MODERATE

ADR 0009: *"Oak thickness sets the inset depth."* ADR 0010: *"the rim of that recess is a
tactile locator."* Both require the cap to sit **below** the outer face at rest.

Work it through with the numbers available (the above-plate/below-plate split of the KS-33's
12.2 mm is the number ADR 0009 correctly identifies as missing, so this is an estimate, not
a result):

| Term | mm | Basis |
|---|---|---|
| KS-33 overall height | 12.2 | verified |
| less pin length | ~3.3 | **estimated** |
| body height | ~8.9 | derived |
| portion above the mounting plane | ~5.5 | **estimated** (Choc-class geometry, from memory) |
| MT165 cap above the switch top housing | ~3.5 | **estimated** |
| **cap top above the plate's outer face** | **~9.0** | |
| oak bottom panel | 8.0 | ADR 0009 |
| **cap top relative to the body's outer face** | **+1.0 (proud)** | |

So on these estimates the thumb keys sit **flush to 1 mm proud**, not inset — and at full
3 mm travel they end up 2 mm *recessed*. There is no rim for the thumb to find at rest, which
is the whole mechanism ADR 0010 relies on for keys the player cannot see.

To get a 2.5 mm inset at rest you need about **11.5 mm** of oak on the bottom panel, or an
extra laminated spacer layer — which the construction gives for free, since every layer is a
2D through-cut anyway.

This is exactly the calculation ADR 0009 says cannot be done without the STEP model, and it
is right. What is worth recording is the **direction**: the uncertainty is not symmetric.
8 mm is at the thin end of the plausible range and the failure mode (no tactile rim, and
thumb keys that can be brushed while gripping) is the one ADR 0010 spends a page guarding
against. Plan for a spacer layer in the M4 CAD and delete it if the STEP model says it is
unnecessary.

**Severity:** moderate. **Confidence:** low-medium on the absolute numbers, high on the
direction and on the recommendation to carry a spacer layer through CAD.

---

### 15. The panel power switch is now a dry circuit — MODERATE

`SW-POWER` was demoted (correctly) to driving the `TPS2553`'s enable pin. ADR 0005: *"The
toggle now carries no load current, so its rating stops mattering."*

**Its current rating stops mattering; its contact material starts mattering.** A switch that
never carries more than a few microamps of enable-pin leakage builds an oxide/sulphide film
on its contacts and develops intermittent or high-resistance closure over a few years — the
classic dry-circuit failure. With no wetting current there is nothing to break the film.

Two fixes, take either:

- **Specify gold contacts / low-level switching.** C&K 7101-series with gold contacts, or
  NKK M2012-series, both sub-miniature toggles with 6 mm (M6 × 0.7) bushings, both rated for
  low-level/dry-circuit switching (*part families from memory; check the contact-material
  suffix, which is the whole point*).
- **Or give it wetting current.** Wire the switch to sink ~1 mA through a 10 kΩ from +12 V
  rather than merely to pull a high-impedance enable. One resistor.

Do both; they cost nothing and this is the only control the player has.

**Physical fit:** sub-miniature toggle body ~8 × 13 mm, bushing M6 × 0.7, panel hole 6.1 mm
(*from memory*). Beside an 8 mm LED bezel that is ~15 mm of panel width against 30.18 available.
**Fits.**

**Severity:** moderate. **Confidence:** high on the dry-circuit mechanism, medium on the
specific part families.

---

### 16. The polyfuse will nuisance-trip — MODERATE

`F-POLY`: PPTC 1206, **500 mA hold**, at the umbilical entry.

PPTC hold current is specified at 20–23 °C and derates steeply with ambient. A 0.5 A-hold
1206 part typically holds around **0.35 A at 50 °C and ~0.30 A at 60 °C** (*from memory;
check the vendor's derating table, it is printed on every PPTC datasheet*).

The instrument's cavity is, by ADR 0014's own estimate, **10–20 K above ambient** at baseline
and up to **+9 K more** at the lighting clamp — so 45–55 °C interior in normal use. The
instrument draws **275 mA by ADR 0004's estimate and 410–430 mA by the review's**. Those two
numbers cross. A 500 mA-hold PPTC in a 50 °C cavity at 400 mA is **operating above its derated
hold current**, which is precisely the slow current-limiting runaway ADR 0014 describes at
length — and then guards against with the module's load switch rather than by resizing the
fuse.

Two clean options:

- **Delete it.** The `TPS2553` at the module already does this job faster, at a fixed limit,
  without thermal hysteresis, and is on the right side of the cable. ADR 0005 calls the two
  "complementary rather than redundant", but the complementary part — a fault *inside* the
  instrument — is covered by the same load switch, because there is only one +12 V path.
- **Or resize to 1.1 A hold** (1206 or 1210), which derates to ~0.75 A at 60 °C and sits well
  clear of the load while still catching a dead short. If you keep it, it must be **outside**
  the heat-soaked region or its derating gets worse, which in a sealed oak body means it
  cannot be.

Recommend **delete**, and record why in ADR 0005 so it does not get re-added.

**Severity:** moderate. **Confidence:** high on the mechanism, medium on the exact derating
figures.

---

### 17. The ground bond is a ring terminal on an oxide layer — MODERATE

`MECH-GNDBOND`: *"Ring terminal + M3 hardware"* bonding the aluminium plate to `PWR_GND`.
ADR 0009 is emphatic that this is one of the four things that are free now and impossible
later. Agreed — and the part as specified will not reliably do it.

- **Aluminium oxide is an insulator** and re-forms in seconds on a freshly abraded surface.
  A tinned-copper ring terminal clamped flat onto it makes an unreliable, ageing contact.
- **Galvanic pair.** Copper ring + steel screw + aluminium plate, in a cavity that is breathed
  into for hours at 45–55 °C, is a corrosion cell with moisture as the electrolyte. The bond
  degrades exactly over the timescale where "the instrument fires random notes when touched"
  gets blamed on firmware.

Specify instead:

> **`MECH-GNDBOND`** — M3 **stainless** (A2) pan-head screw, **stainless external-tooth
> serrated (star) lock washer directly against the abraded aluminium**, tinned-copper ring
> terminal, stainless nyloc nut. Abrade the contact patch immediately before assembly and
> apply a thin film of electrical joint compound (Noalox / Penetrox-class). **Measure the bond
> at < 0.1 Ω before the stack is bonded** — it is on the M8 pre-bond gate's list or it is
> never measured at all.

The serrated washer is the load-bearing part: its teeth bite through the oxide and hold a
gas-tight contact under the screw's preload.

**Also give it a second job.** If the umbilical cable is shielded (finding 6d), this is the
point the shield should land, per the review's R38. Run it as one stud with two terminals
rather than discovering later that there is no shield return inside a sealed body.

**Severity:** moderate. **Confidence:** high.

---

### 18. Eurorack power entry: the header is right, the cable is missing — MODERATE

`J-PWR-EURO` (16-pin shrouded keyed IDC) is the correct call, and the reasoning — the module
*requires* +5 V, which the 10-pin bus omits — is right.

**The cable is not in the BOM and the default is wrong.** The overwhelming majority of ribbon
cables shipped with Eurorack cases and modules are **16-pin at the bus end and 10-pin at the
module end**, which carries ±12 V and ground only. Plug one of those into this module and the
74AHCT125 has no rail, the SPI level shifter is dead, and the DAC never sees a valid frame —
a failure that will look like a firmware problem for an afternoon.

> **MISSING: `CBL-PWR`** — 16-way IDC ribbon, **16-pin connectors at both ends**, 150–200 mm,
> with the red stripe on the −12 V row. Qty 2 (one spare).

**Physical fit.** A 2×8 shrouded header body is about **23.1 × 10 mm** (*from memory*). A 6HP
module PCB is at most ~28 mm wide and realistically 25–26 mm, so the header fits with ~1.5 mm
either side — one orientation only, and the ribbon's exit direction and minimum bend radius
(~10 mm) have to be in the layout, not discovered. On the two-board module of finding 3 it
belongs on the rear board.

Add: **module mounting hardware** — 2 × M3 × 6 screws with nylon washers, plus rail nuts if
the case uses them. Not in the BOM, and it is the last thing you want to be missing on the day.

**Severity:** moderate. **Confidence:** high.

---

### 19. The internal loom is mandated by an ADR and absent from the BOM — MODERATE

ADR 0009 requires, in the same paragraph, that:

- the key chain gets **a ground return per signal** ("ribbon with alternating grounds, or
  twisted pairs"), and
- **two spare conductors run in every internal loom**.

Neither has a BOM line, and the loom is hand-built once into a body that cannot be reopened.
At minimum:

> **MISSING: `CBL-LOOM`** — 1.27 mm-pitch stranded ribbon (alternating-ground assignment) or
> twisted-pair hookup wire, 26–28 AWG **stranded**, silicone or PTFE insulation (the cavity
> runs 45–55 °C and PVC goes soft), ~2 m total.
>
> **MISSING: `CBL-CONN`** — board-to-board connectors: JST PH 2.0 or XH 2.5 headers and
> crimp housings, plus the crimp tool. Or, better in a sealed instrument, soldered joints
> with heat-shrink and **anchored service loops**, because a connector that vibrates apart
> inside a bonded body is unrecoverable and a solder joint is not.
>
> **MISSING: `MECH-ANCHOR`** — adhesive cable tie mounts or P-clips, ~10 off, so every loom
> is anchored at both ends and the U-bolt intrusion is routed around rather than rubbed on.

The choice between crimped connectors and soldered joints deserves an explicit line in
ADR 0013 rather than being made with whatever is on the bench at M7. My recommendation for a
bonded one-off: **soldered, heat-shrunk, anchored, with service loops long enough to lift each
board clear during the M8 dry assembly**.

**Severity:** moderate. **Confidence:** high.

---

### 20. Strap hardware: the highest-stress point in the build has no part number — MAJOR

ADR 0009: *"This is the highest-stress point in the entire build. The strap carries the whole
instrument, and it carries it during play."*

The BOM contains no U-bolt, no backing plate, no strap hook and no strap.

Loads: instrument ~825 g static. A wind player raises, lowers and swings the instrument
continuously; design for a **3–5× dynamic factor** → **~40 N**, with shock loads (catching a
drop) an order above that. Trivial for the metalwork, not trivial for the wood.

> **MISSING: `MECH-UBOLT`** — M4 or M5 **stainless** U-bolt, ~25 mm inside width, legs long
> enough to pass the full 38 mm stack plus plate plus nuts, with **nyloc** nuts. At M4 stainless,
> a single leg's tensile capacity is ~2 kN against a 40 N working load — the metalwork is
> never the limit.
>
> **MISSING: `MECH-UBOLT-PLATE`** — 2–3 mm aluminium backing plate inside the cavity, tied
> into the same plate stack that carries the keys, sized to spread the load well beyond the
> two holes. Crushing oak fibres is the actual failure mode and washer area is the actual fix:
> a plain M4 washer at 40 N is ~0.5 MPa on oak, which is fine — a *shock* load through a bare
> washer is not.
>
> **MISSING: `MECH-STRAP`** — neck strap with a snap hook sized to the U-bolt, and confirm
> the hook's gate clears the bolt with the instrument at playing angle.

Three geometric constraints that belong in M4's CAD, all of which follow from parts that are
currently unspecified:

- the U-bolt legs pass through the cavity in the inter-hand gap — they must miss the side
  channels (LED strips and looms) and the breath tube;
- the legs and the backing plate are inside a bonded cavity, so **position is settled at the
  M8 dry-assembly** and never again — which ADR 0009 already establishes and which is the
  correct call;
- the through-holes in the aluminium key plate have to be in the key-plate DXF, cut at M5,
  before anyone knows where the balance point is. That is a genuine ordering conflict: **M5
  cuts the plate, M8 finds the balance point.** Resolve by cutting a *slot* in the key plate
  (the plate is laser-cut, so a slot is free) and a slot in the internal backing plate, with
  the final position fixed by clamping at M8. The slot is in the parts you cannot reach later;
  the fixing is the thing you set at M8.

That last point looks like it contradicts the review finding that killed U-bolt adjustability —
it does not. The review was right that you cannot *adjust* it after bonding. A slot cut now
means you do not have to.

**Severity:** major. **Confidence:** high.

---

### 21. Smaller missing items, gathered

| Item | Why | Severity |
|---|---|---|
| **Panel LED + resistor** | ADR 0004's panel layout has one; BOM has neither. Needs the bezel/holder too, which sets the panel hole | Minor |
| **PJ398SM nuts** | Sold both with and without; also nylon washers to protect a finished panel | Minor |
| **Pot nuts and washers** | M7 × 0.75; the Alpha ships with one, confirm | Minor |
| **PCB standoffs, module** | M3 × 15 or 18 mm to set the 24 mm connector plane on the two-board module (finding 3) | Moderate |
| **Threaded inserts / standoffs, instrument** | The carrier and dev boards have to mount to the plate stack inside a bonded body. No fasteners anywhere in the BOM | Moderate |
| **Breath tube retention** | 400 mm of silicone on a push-fit barb in a body that is shaken for hours. A cable tie or a short heat-shrink collar at each end, plus tube clips along the run. A tube that walks off the port reads as a dead sensor | Moderate |
| **Tail cap and mouthpiece-end cap** | Finding 8. The stack as drawn has open ends | Major |
| **Umbilical cable clip to the strap** | Finding 7 | Moderate |
| **LED strip retention** | Finding 12 | Moderate |
| **Spare switches** | Finding 13 — soldered, in a bonded body, with no published cycle rating and a 3.0 revision already out | Moderate |

---

### 22. Documentation corrections

- **`hardware/bom.csv`, `PANEL`:** "30.0 × 128.5 mm" contradicts ADR 0004's 30.18 mm.
  30.18 is the (n × 5.08) − 0.3 figure and is what the connector clearance was computed
  against; Doepfer's own table quotes 30.0 for 6 HP, so both conventions exist in the wild,
  but the repository must pick one. Using 30.0 changes the bore clearance from 3.19 to
  3.09 mm — immaterial, but it is exactly the kind of 0.18 mm that gets rediscovered at the
  laser cutter.
- **ADR 0009, keycap spacing:** "standard 18 mm MX spacing" — MX pitch is 19.05 mm; 18 mm is
  the cap. Finding 13.
- **ADR 0010, thumb arc:** "roughly 57 mm of travel" is ambiguous between centre-span and
  total extent, and the two answers differ by whether four caps fit. Finding 13.
- **ADR 0004, open question:** "solder-tag variant" — no such part. Finding 1.
- **ADR 0004, panel:** "3.19 mm each side" is bore-referenced; the flange figure is 2.09 mm
  and the screw-hole figure is smaller still. Finding 2.
- **ADR 0009, tail allowance:** 40 mm for "connector + strain relief" is optimistic by
  15–25 mm. Finding 9.
- **ADR 0005, umbilical drop table:** computed at 250 mA; the current budget has since moved
  to 275–430 mA. The conclusion does not change (finding 6a) but the table should say so
  rather than leaving a stale number in a document people quote.
- **ROADMAP E12:** *"etherCON braced to the PCB"* needs a named mechanism, per finding 3.
- **ROADMAP M7:** *"umbilical connector fitted and strain-relieved"* has no part behind
  "strain-relieved". Finding 7.
- **`docs/reference/ks33-geometry.md`:** add the **45 ± 15 gf** operating force for the Red
  linear, which is published and is what M1's spring-weight question turns on.

---

### 23. The two dimensions to fetch before anything is cut — UNOBTAINED

Everything above that is soft is soft because of these two. Both are one PDF away on a
network that can reach `neutrik.com`.

1. **The Neutrik D-series flange and fastening layout.** Specifically the **positions and
   spacing of the two M3 mounting holes** within the 26 × 31 mm flange. This — not the
   Ø23.8 mm bore — decides whether the connector fits a 30.18 mm panel, because the screws set
   the horizontal extent of the cutout group and the web between a screw hole and the panel
   edge. Neutrik publish it as *"speakON Flange and Fastening Layout — D-size standard"*
   and as a DXF on each product page. I could bound it (≤ 26 mm, therefore ≤ 2.09 mm of panel
   outboard) but not pin it.
2. **The etherCON D-series depth behind the panel**, for the chosen variant. It sets the
   module's total depth (finding 3), the instrument's tail length allowance (finding 9), and
   whether the real-time board can share the tail with it at all.

Two more that are nice to have and currently guessed:

3. **Gateron's KS-33 dimensioned drawing / STEP** — for the above-plate/below-plate split
   (finding 14) and the retention-clip dimension (plate thickness, still open since ADR 0002).
   This project has now failed to obtain it twice; **M1's coupon can answer both empirically**
   by cutting the thickness ladder alongside the kerf ladder, which is the same order at the
   same vendor. Do that rather than waiting for the drawing a third time.
4. **PJ398SM body height above PCB**, which together with the Alpha 9 mm pot's 10 mm body
   height decides whether jacks and pots can share one PCB plane. They demonstrably can — the
   entire Eurorack DIY ecosystem does it — so this is a confirm-before-layout, not a risk.

---

## Summary of what I would change today

1. **Split the module into two boards** (jack/pot board at ~7 mm, main board at 24 mm) and
   specify **`NE8FDV`** at the module end. This is the only construction in which "braced to
   the PCB" is true rather than aspirational. (Finding 3)
2. **Specify `NE8FDY-C6` or `NE8FDV-YK` — the IDC D-shape variant — at the instrument end.**
   It answers ADR 0004's open question better than either option that question considered:
   no solder joints and no extra mating interface inside a body that cannot be reopened.
   Check the intermate matrix and pick the carrier from the same family. (Finding 1)
3. **Add the tail end cap.** The stack currently has open ends and the connector has nothing
   rated to mount to — 6 mm of oak exceeds the part's 4 mm panel-thickness limit outright.
   (Finding 8)
4. **Lay out a 12 V gate-driver footprint alongside the 74AHCT125** for the WS2815 data lines.
   The datasheet threshold is 8.4 V; 5 V works by custom, not by specification, and this is a
   sealed build. (Finding 11)
5. **Specify the umbilical cable as parameters** — 26 AWG stranded F/UTP, OD 5.5–6.5 mm,
   bootless plugs — and **add four etherCON carriers**, without which the latch and strain
   relief that justified the whole connector choice do not exist. (Findings 6, 7)
6. **Specify a 12 mm knob**, or move the connector to the bottom of the panel. Two knobs of
   the size anyone would reach for do not fit across 30.18 mm. (Finding 4)
7. **Delete the 500 mA polyfuse** or take it to 1.1 A. At 400 mA in a 50 °C cavity it is
   operating above its derated hold current. (Finding 16)
8. **Give the strap hardware part numbers and slot the plates**, so M5 can cut the key plate
   before M8 finds the balance point. (Finding 20)
9. **Stop calling `J-USB` "not-needed".** (Finding 10)
10. **Fetch the Neutrik D fastening layout.** It is the one number this review could not get
    and the one that decides the connector's fit. (§23)
