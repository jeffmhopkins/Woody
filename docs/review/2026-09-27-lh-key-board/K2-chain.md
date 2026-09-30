# K2 — The chain across the ribbon

**Slice:** K2, cold (no `docs/review/**` read except this wave's README).
**Revision measured:** `d46a3b0`. `tools/` not modified; no repository file
changed except this report. Scratch work in the session scratchpad only.

**Fact domain:** every conductor from the main board's `J-CHAIN` to a key
board's `J-CHAIN`: header and socket orientation, the `-RN2` option, which
side each socket's cable leaves from, the resulting pin map, and every place
that states it.

## Summary

**The pin map is right. The reason given for the cable route is wrong.**
From the banked prints, key-board pin = 13 − main-board pin for a `-RN2`
cable, flat and untwisted. Every place that states the pinout agrees with
that and with the others: both KiCad sheets, both exported board netlists,
the LH PCB's pads, the loom netlist, `nets.yaml`, the BOM rows, the loom
page's tables and drawings, `cluster-boards.md`, ADR 0017 and the register
and network pages. The hop allocation is also consistent everywhere.

**What is wrong is the geometry that the corpus claims explains it.** Six
files state that "an FFSD socket's cable leaves on the long side away from its
notch", and conclude that both sockets' cables leave downward. The FFSD
print says otherwise:

- On a standard double-end assembly, the first connector's key is on the
  cable side and the second's is away from it.
- With `-RN2`, both keys are on the cable side.

So with `-RN2` the **main-board socket's cable leaves upward**, off the top of
the plug, toward the key board. The two exits face each other. The route drawn
everywhere (both legs leaving downward, a hairpin whose main leg lies on the
main board) is what a **standard, non-`-RN2` cable** does, with one half-twist.
That cable maps k → k and puts 3V3 on a key-board ground pin. In other words,
the drawings show the wrong cable fitting cleanly. The documented tell ("without
`-RN2` the cable leaves toward the key board") is only true for one of the two
ways such a cable can be plugged.

Findings: 1 high, 2 medium, 3 low, 2 advisory.

---

## The derivation, from the prints

### The header (SHF-106-01-L-D-RA)

- **Sheet 2, Fig 2, upper view:** this view looks into the mouth. Its tails
  protrude past the body toward the top of the image, so the PCB is at the top.
  Row `02` (even pins) is the row next to the PCB. Row `01 03` (odd pins) is
  away from it. The shroud's key gap is in the odd-row wall, in the middle
  (the inner outline drops at x≈330–410 of the crop).
  `[datasheets/connectors/SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf, sheet 2 fig 2]`
- **The lower view is third-angle, looking at the face away from the PCB.**
  It shows the key window and the first-position triangle over column 1.
  Sheet 1 Fig 1 (the vertical version) puts the key gap in the `01 03` wall
  too. `[same print, sheets 1–2]`
- **Section C-C:** the pin nearer the PCB bends first. Its tail is 1.26 behind
  the body and the far row's is 1.27 further. So the even row is nearer the
  body and the odd row is further back. `[same, sheet 2 section C-C]`
  - This agrees with the footprint: odd pads at x=0, even at x=1.27, body
    2.53 → 7.86, mouth at +x `[hardware/lib/woody.pretty/IDC-Header_2x06_P1.27mm_Samtec_SHF_Horizontal.kicad_mod]`.
  - It also agrees with `boards.chain_hdr_pin_back` = 5.33 + 1.26 + 1.27 = 7.86 `[calc]`.
- **Pin 1's end:** seen from the component side with the mouth pointing
  right, pin 1 is at the top of the view and pin numbers increase downward
  `[calc: mouth view, right = forward × up = (−x) × (−z) = −y, pin 1 at image left → +y]`.
  The library footprint does the same: pads step +y in KiCad's
  y-down frame.
- **Main board:** the header stands upright, so its key slot faces **up**.
  **Key board:** the same part hangs upside down with its mouth facing the same
  way, which is a 180° rotation about the insertion axis. Its key slot faces
  **down**, and its pin 1 is at the opposite end across the body. The LH PCB
  matches:
  - pad 1 is at PCB y 111.16, i.e. body y 38.84, and pad 11 is at body y 45.19;
  - the pad centre is at body y 42.015 = `chain_y`;
  - the mouth faces +x (toward the tail) for `left_hand`.

  `[hardware/boards/key-board-lh/key-board-lh.kicad_pcb J-CHAIN on B.Cu; tools/pcb.py to_pcb; mechanical/export/pcb-geometry.echo "chain"]`

### The cable (FFSD-06-D-xx.xx-01-N-RN2)

- **Conductor k is at socket position k.** The contacts in the two rows are
  staggered by half a pitch, so conductors alternate between rows. Note 10
  ties the coloured wire to position 1 of the first connector.
  `[datasheets/connectors/SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf, sheet 1 fig 1 plan view, note 10]`
- **Where the key sits relative to the cable, from the print:**
  - **Sheet 2, Fig 3, "‑RN1 shown" (double end):** both keys are on the
    outer side, away from the cable run. RN1 reverses only the first
    connector, so the **unreversed second connector has its key away from
    the cable.**
  - **Sheet 2, Fig 3, "‑RN2 shown":** both keys are on the inner side,
    toward the cable run. RN2 reverses only the second connector, so the
    **unreversed first connector has its key toward the cable.**
  - **Sheet 1, Fig 1, side view (standard ‑N):** the left socket's lower
    block, the ‑N key, stands on its cable side. The right socket's stands
    on its outer side. That agrees with both of the above.

  Toward-or-away from the cable does not depend on which side a view is taken
  from, so three independent views agree.
  `[FFSD print sheet 1 fig 1; sheet 2 fig 3, all three sub-figures]`
- **This is also forced by the build.** A straight IDC cable is pressed with
  both sockets the same way up, so both keys face the same absolute side. One
  end's cable must therefore leave on the key side and the other's away from
  it `[calc]`.

| Cable | 1st connector | 2nd connector |
|---|---|---|
| standard (‑N) | cable leaves on the key side | cable leaves away from the key |
| ‑RN1 | away | away |
| **‑RN2** | **key side** | **key side** |

### Put together `[calc]`

Frame: x along the body (mouths +x, `left_hand`), y across it, z up. In the
cable's flat frame, X′ points from the 1st connector to the 2nd, Y′ is the
width (conductor 1 at +Y′), and Z′ is the mating face's normal.

- **‑RN2, 1st connector on the main board:**
  - Key up, so X′ → +z, Z′ → +x and Y′ → −y.
  - **The cable leaves upward.**
- **‑RN2, 2nd connector on the key board:**
  - It is reversed, so its key is at −X′. With the key down, X′ → +z and
    Y′ → −y, the same as the main end.
  - Its cable leaves along −X′: **downward**.
  - Y′ is the same at both ends, so the ribbon is flat with bends about y
    only: **no twist**.
  - Conductor k lands at key-board position 13 − k.
- **‑RN2 with the ends swapped** (2nd on the main board, 1st on the key
  board): the exits are the same (main up, key down). The map is also the
  same, because k ↔ 13 − k is its own inverse. **Either end may go to either
  board.**
- **Standard cable, 2nd connector on the main board and 1st on the key board:**
  - Main: key up, cable away from the key, so **down**.
  - Key board: key down, cable on the key side, so **down**. This is the
    drawn route.
  - Y′ → −y at the main end and +y at the key end, so it needs **one
    half-twist**.
  - Map k → k.
- **Standard cable the other way round:** main cable up. The key-board cable
  leaves up into the key board, a 180° crease in the 1.525 mm under the
  board `[calc: top_z 28.4 − (chain_zk 25.35 + 3.05/2)]`. Map k → k.

### The pin table, from the prints

| Conductor k = main-board J-CHAIN pin | Signal | Key-board J-CHAIN pin (13 − k) | Main-board row | Key-board row |
|---|---|---|---|---|
| 1 | GND | 12 | odd (away from main board) | even (against key board) |
| 2 | SCK | 11 | even | odd |
| 3 | GND | 10 | odd | even |
| 4 | SH/LD | 9 | even | odd |
| 5 | GND | 8 | odd | even |
| 6 | SER (key board's in) | 7 | even | odd |
| 7 | GND | 6 | odd | even |
| 8 | QH (key board's out) | 5 | even | odd |
| 9 | GND | 4 | odd | even |
| 10 | 3V3 (via FB-CHAIN) | 3 | even | odd |
| 11 | spare | 2 | odd | even |
| 12 | spare | 1 | even | odd |

Physically, conductor 1 sits at the same body-y end at both headers: main pin 1
at body y ≈ 45.19 and key pin 12 at body y 45.19 `[calc from the PCB pads above]`.

---

## Findings

### K2-1 [high] The rule "an FFSD socket's cable leaves on the side away from its notch" contradicts the banked print. With `-RN2` the main-board socket's cable leaves UPWARD, and the drawn route is the one the wrong (standard) cable takes

**Node:** `CBL-CHAIN`, both ends, and the main-board `J-CHAIN` socket.

**What the corpus says.** Each of these states that both sockets' cables leave
downward, and that `-RN2` is what makes the key-board one do so:

- `hardware/interfaces/key-chain-loom/key-chain-loom.md`, *The ribbon* items 2
  and 3, and *How the ribbon lies closed*: "The main board's header is upright
  … so that socket's cable leaves downward, onto the main board".
- `hardware/interfaces/key-chain-loom/bom.csv` `CBL-CHAIN` notes, and the
  generated `hardware/bom.csv` row: "A socket's cable leaves on the long side
  away from its notch (sheet 1 fig 1) … its cable leaves DOWNWARD … like the
  main board's".
- `docs/decisions/0017-one-main-board.md` amendment, reason 3 and the
  Consequences bullet: "its ribbon leaves downward like the main board's".
- `mechanical/DESIGN.md` items 1–2: "both sockets' cables leave downward".
- `mechanical/cad/woody_body.scad`, comment above `chain_thumb_stub`:
  "exits on the side away from its key … the key board's has its notch
  reversed (-RN2) so it is keyed up too". That is doubly wrong: the key
  board's header is upside down, so its socket is keyed **down** whatever the
  cable option. The option does not change which way the header's slot faces.
- `mechanical/renders/section-ribbon.png` draws the same route.

`[repo, each path]`

**What the print shows.**

- On a standard assembly, the first connector's key is on its cable side and
  the second's is away from it.
- With `-RN2`, both keys are on the cable side.
- The evidence is sheet 2 Fig 3's RN1 and RN2 sub-figures and the side view
  in sheet 1 Fig 1, derived above.

`[datasheets/connectors/SAMTEC-FFSD-XX-X-XX.XX-01-PRINT.pdf, sheet 1 fig 1 side view; sheet 2 fig 3]`

The main-board header's slot faces up `[SHF print sheet 2 fig 2]`, so the
main-board socket's key faces up. Whichever end of an `-RN2` cable is plugged
there, the key is on its cable side, so **the cable leaves from the plug's top
edge, toward the key board.** The key-board socket's cable leaves downward.
The two exits face each other across the gap between the plugs `[calc, above]`.

**Why this is high, not a drawing nit.**

- The route drawn everywhere, with both cables leaving downward, is exactly
  what a **standard FFSD-06-D-…-01-N cable (no `-RN2`)** does. The standard
  cable needs the 2nd connector on the main board and one half-twist, which
  an 86 mm ribbon absorbs without anyone noticing `[calc, above]`.
- That cable maps conductor k to key-board pin k:
  - main pin 10, 3V3 through `FB-CHAIN`, lands on key-board pin 10, which is
    `GND_CHAIN`;
  - main pin 4 (`SH/LD`, IO7 through 100 Ω) and main pin 6 land on
    key-board grounds (pins 4 and 6);
  - on the `right_hand` ribbon, main pin 6 is `left_thumb`'s `QH`, a
    74HC165 output with no series resistor, so that output is shorted too;
  - `SCK` lands on key-board pin 2, which is unconnected.

  `[calc from hardware/interfaces/key-chain-loom/netlist.yaml and the board-netlists]`
- So a builder who matches the pictures will find the right cable looks wrong
  (its main leg rises) and the wrong cable looks right.
- The corpus's stated tell, "Order the cable without -RN2 and … its cable
  leaves toward the key board" (key-chain-loom.md, the `CBL-CHAIN` note and
  the key-board README), holds only for the standard cable's other plugging.

**What limits the damage** is the LDO's current limit, typical only
(key-chain-loom.md). The rail collapses and the Matrix does not start. So the
likely outcome is a dead bench, not a dead board. But the only protection is a
figure that `ME6217C33M5G` p.4 does not guarantee `[repo, key-chain-loom.md's citation]`.

**Fix:**

1. Replace the rule everywhere with the print's: "the first connector's cable
   leaves on its key side and the second's away from it; `-RN2` puts both on
   the key side, `-RN1` both away". Cite sheet 2 fig 3.
2. State the consequence: with `-RN2`, the main-board plug's cable leaves
   upward and the key-board plug's leaves downward, facing each other. The
   map is 13 − k, flat, no twist, and either end may go on either board.
3. Correct the scad comment ("keyed up too").
4. Re-draw the route (K2-2).
5. Say explicitly that a cable whose legs both leave downward is a standard
   cable, and is wrong.

### K2-2 [medium] The closed ribbon's modelled path, and the drc.echo figures derived from it, describe a path the `-RN2` cable does not take

**Nodes:** drc.echo "key-chain ribbon closed: hairpin leg and fold radius"
(34.59, 4.94), "key-chain ribbon hairpin inside the body (left_hand/right_hand)",
and `chain_drops`, `chain_z_low` and `chain_path()` in
`mechanical/cad/woody_body.scad` `[repo mechanical/drc.echo lines 51–53]`.

**What the model draws.** The main-board leg leaves the bottom edge of the main
plug and lies on the main board at z = 12.45, under the plug.
`[run: openscad echo probe including woody_body.scad → cb_top 11, chain_zm 14.05, chain_zk 25.35, chain_z_low 12.45, chain_z_up 22.325, top_z 28.4]`

**Where the `-RN2` cable actually leaves the main plug:** its top edge, at
z = 14.05 + 3.05/2 = 15.575 `[calc]`.

**The space between the plugs** runs from 15.575 up to the key plug's bottom
edge, 25.35 − 1.525 = 23.825. That is a gap of 8.25 mm `[calc]`. The model's
fold diameter is 2 × 4.94 = 9.875 mm `[repo drc.echo]`. A hairpin with both
legs inside that gap gets a fold radius of at most about (8.25 − 0.8)/2 ≈ 3.7 mm
`[calc, ribbon 0.8 from routing.chain_ribbon_t]`, and each leg also has to turn
90° straight out of a socket edge.

**The alternative** is a 180° crease over the main plug's top edge, back down
its face, to reach the modelled path. The model does not include that either.

**History points the same way.** `notes.md` records that an earlier version
had the legs "one at each plug's height". That is closer to what `-RN2`
does, and it was "corrected" away `[repo hardware/interfaces/key-chain-loom/notes.md]`.

(Overlaps K5's domain. Filed here because it follows from K2-1.)

**Fix:** decide the closed route for a main exit from the plug's top: a hairpin
in the gap between the plugs, or a crease at the main plug. Re-derive
`chain_drops`, `chain_leg`, `chain_r` and the hairpin extents from it.
Re-render `section-ribbon`.

### K2-3 [medium] The meter check is scoped to "the first one", but a wrong cable goes in without any mechanical sign, so every cable needs checking before power

**Nodes:** `CBL-CHAIN` note "on the first one, check with a meter that
conductor 10 reaches key-board pin 3" `[repo hardware/interfaces/key-chain-loom/bom.csv]`.
The same wording is in key-chain-loom.md *Still open*. The key-board README's
Bring-up step 2 says "on the first cable" `[repo hardware/boards/key-board-lh/README.md]`.

**Why every cable.** By K2-1, a standard cable fits the drawn route with a
half-twist and puts 3V3 on a ground (main pin 10 → key pin 10). Nothing else
detects it before power. There are two cables per instrument, and a
replacement is bought singly.

**Fix:**

- Make the check per cable, before first power: conductor 10 → the far
  socket's position 3, and conductor 2 → position 11.
- Add that the map is symmetric, so either end may be called the main-board
  end. Readers need not track which end is "first".

**What a wrong cable does, for the page** `[calc]`:

- `DEV_3V3` goes into `GND_CHAIN` through `FB-CHAIN`, limited only by the
  LDO's typical 350 mA.
- IO7 and IO33 drive ground through 100 Ω each: 33 mA while the rail
  lasts. The ESP32-S3's per-pin absolute maximum is about 40 mA
  `[from memory]`.
- On the RH ribbon, `left_thumb`'s `QH` is shorted to ground directly.
- The collapsing rail limits all of these.

### K2-4 [low] The FFSD length field is in inches, while the corpus gives the length in millimetres and says "order that length or the next stock one up"

**Nodes:**

- `CBL-CHAIN` stand-in "FFSD-06-D-xx.xx-01-N-RN2, … xx.xx the length below" `[repo hardware/interfaces/key-chain-loom/bom.csv]`;
- drc.echo "key-chain ribbon length (derived)" 86.27 mm `[repo mechanical/drc.echo]`.

**What the print says.**

- The length field is `XX.XX[XX.X x 25.4]`, i.e. inches, with a 1.00 in
  minimum.
- Note 11 gives a tolerance of ±0.125 in (±3.2 mm) below 12.5 in.
- FFSD is built to length. There are no "stock" lengths.

`[FFSD print sheet 1: length callout, "ASSEMBLY LENGTH", note 11]`

**The risk.** Read literally, "xx.xx = 86.27" orders a 2.19 m cable
`[calc: 86.27 in × 25.4]`.

**Fix:** state the unit and the conversion (86.27 mm = 3.40 in, so the part is
FFSD-06-D-03.40-01-N-RN2 `[calc]`). Say that the −3.2 mm tolerance comes out of
`routing.chain_slack`. Drop "stock".

### K2-5 [low] No check ties the key boards' `J-CHAIN` pin numbers to the loom netlist's `J-CHAIN-KEY-*` pins; they agree today only by hand

**Nodes:**

- `J-CHAIN` in `hardware/boards/key-board-{lh,rh}/key-board-*.kicad_sch`;
- `J-CHAIN-KEY-LH` and `J-CHAIN-KEY-RH` in `hardware/interfaces/key-chain-loom/netlist.yaml`.

**What I compared.** I exported both sheets and read J-CHAIN's pins. The
netlists agree pin for pin with the loom netlist and with each other:

- 11 SCK, 9 SH/LD, 7 SER, 5 QH, 3 3V3;
- 4/6/8/10/12 GND_CHAIN;
- 1 and 2 unconnected.

`[run: kicad-cli sch export netlist --format kicadxml … for both boards; compared with netlist.yaml]`

**What no tool checks.** The two use different refdes. `check-netlist.py`
does not read `board-netlist.yaml`. `kicad.py check_allocation` checks only
the register inputs `[repo tools/check-netlist.py, tools/kicad.py lines 399–445, read]`.
So a key-board sheet renumbered back to k → k would pass every check.

**Fix (after the tools freeze):** make `kicad.py check` compare each board's
`J-CHAIN.<p>` net with the loom netlist's `J-CHAIN-KEY-<board>.<p>` net.

### K2-6 [low] `config/body.yaml` carries two stale statements about the chain parts

**Nodes:** the comment above `boards.chain_hdr_l`, and `routing.chain_slack.source`.

- **The comment** says "both catalogue pages are banked …, their full prints
  are not (403)". Both full prints are banked, and they are cited by the
  entries a few lines below it `[repo config/body.yaml ~lines 336–341, 349–360; datasheets/connectors/]`.
- **`chain_slack`** is "length added … for the twist and the hand". The
  corpus says the ribbon has no twist. By K2-1 only the wrong cable twists
  `[repo config/body.yaml ~line 871]`.

**Fix:**

- Delete "(403)" and say the prints are banked.
- Re-word `chain_slack` as "for the hand and the bends".

### K2-7 [advisory] The header's 2×6 pad grid is symmetric under a 180° turn, so a hand-fitted `J-CHAIN` soldered with its mouth backward is electrically 3V3-on-ground

**Node:** `J-CHAIN` (key board and main board), which is hand-fitted
`[repo hardware/boards/key-board-lh/README.md, "Assembling the rest by hand" 1]`.

**Why the pads allow it.** A 180° turn about the board normal maps the odd row
onto the even row and column c onto column 7 − c. So the physical pin p sits in
pad 13 − p `[calc from the footprint's pad grid]`.

**What that does on the key board.** Conductor 10, 3V3, meets header pin 3,
which is then in pad 10 = `GND_CHAIN`. `SCK` lands in pad 2, which is
unconnected `[calc]`. The same backward fit on the main board combines with
`-RN2` in the same way.

**What guards against it.** The B.SilkS body outline, the pin-1 dot (placed
behind pad 1, away from the mouth, by `tools/pcb.py`), and the README's "mouth
toward the tail" `[repo key-board-lh.kicad_pcb gr_circle at 130.14,111.16; tools/pcb.py lines 321–327]`.
Whether the body would fit backward at all depends on K3's and K5's clearances.
I did not check that.

**Fix:** one line in the README step: "the body sits over the silk outline, the
dot is behind the pins, not under the body; backward is 3V3 on ground".

### K2-8 [advisory] `hardware/nets.yaml` `GND_CHAIN.carries` gives the grounds as "J-CHAIN pins 1/3/5/7/9" without saying which end

**Node:** `GND_CHAIN` `[repo hardware/nets.yaml line 64]`.

These are the main-board numbers. On the key board the grounds are
4/6/8/10/12. The rail entries two stanzas above do qualify their pins
("main-board J-CHAIN pin 10, key-board pin 3").

**Fix:** "… pins 1/3/5/7/9 at the main board (4/6/8/10/12 at the key board)".

---

## Checked and found correct

- **The SHF RA header's orientation** `[SHF print sheet 2 fig 2 and section C-C]`:
  - key slot in the odd-row wall, away from the board;
  - even row nearest the board and the body;
  - pin 1's end as derived above.

  These match the footprint and `boards.chain_hdr_pin_back` (7.86)
  `[calc]`, and the key-chain-loom.md sentence about the main board's slot.
- **"A keyed socket always mates position k to header pin k", so the map is
  set by the cable.** Correct.
- **`-RN2` gives key pin = 13 − main pin, flat and untwisted** `[calc from FFSD sheet 2 fig 3]`.
  Also: `-RN1` gives the same map; its key-board cable leaves up into the key
  board.
- **The key-board sheets** (LH and RH, `J-CHAIN` pins via labels, `Pins`
  1=1…12=12, Note citing 13 − n) and their **exported board netlists** agree
  with the map. The export is current against the sheet
  `[run: kicad-cli export; repo board-netlist.yaml]`.
- **The LH PCB `J-CHAIN`:**
  - on B.Cu, flipped rather than hand-mirrored;
  - pads carry the same nets;
  - mouth +x;
  - pads centred at `chain_y`;
  - pin 1 at the body-y end that makes conductor 1 run straight
    `[repo key-board-lh.kicad_pcb; mechanical/export/pcb-geometry.echo]`.
- **`hardware/interfaces/key-chain-loom/netlist.yaml`:**
  - `CHAIN_SCK` (main 2 / key 11), `CHAIN_SHLD` (4/9), `CHAIN_SER_LH` (6/7),
    `HOP_LH_LT` (key 5 / main 8), `HOP_LT_RH` (6/7), `HOP_RH_RT` (5/8),
    `V3V3_CHAIN_*` (10/3), `GND_CHAIN` (1,3,5,7,9 / 12,10,8,6,4), spares
    (11/2, 12/1) are all consistent with 13 − k.
  - `hardware/nets.yaml`'s hop and rail `carries` agree.
  - `python3 tools/check-netlist.py --strict` reports 0 problems `[run]`.
- **Hop allocation:** chain order MCU ← RT ← RH ← LT ← LH `[repo config/key-layout.yaml chain]`.
  - `HOP_LH_LT` and `CHAIN_SER_LH` are on the LH board.
  - `HOP_LT_RH` and `HOP_RH_RT` are on the RH board.
  - IO33 and `R-SER-TERM` are only on the `left_hand` ribbon's main pin 6.
  - LT's `QH` is on the `right_hand` ribbon's main pin 6.
- **key-chain-loom.md:**
  - the Interfaces table (main-board numbering, stated);
  - the chain drawing (key boxes 7 in / 5 out);
  - the main-board-end and key-board-end drawings;
  - the 1–12 conductor/pin table;
  - the header-row paragraph (key-board signals odd row, grounds even row;
    main board the reverse).
- **The `J-CHAIN` BOM note's two pinouts, the `R-SER-TERM` note (main 6 / key
  7) and the `FB-CHAIN` note (main pin 10)**
  `[repo hardware/interfaces/key-chain-loom/bom.csv; generated hardware/bom.csv rows identical in these fields]`.
- **Other pages:**
  - `cluster-boards.md` (pins 7 and 5, 13 − k);
  - `key-register.md` and `key-switch-network.md` (SER = key pin 7, QH = 5,
    3V3 = 3);
  - ADR 0017's amendment map (13 − n);
  - ADR 0001's pinout string `GND SCK GND SH/LD GND SER GND QH GND 3V3 spare spare`.

  ADR 0001's "Eight connectors … five boards" is a deliberately kept record
  (see the `chain-connectors` entry in `config/figures.yaml`), not a finding.
- **"A ground between every signal" is true in the ribbon as built.**
  - Conductors 2, 4, 6 and 8 each have grounds on both sides.
  - 3V3 (10) has ground 9 on one side and spare 11, floating at both ends,
    on the other. That matches ADR 0001's "3V3 sits against a ground".
  - In the headers, the signals sit side by side along one row, as
    key-chain-loom.md says.
  - `[calc from the pin table; IDC conductor k = position k, FFSD sheet 1 fig 1 staggered contacts]`
- **Keying:**
  - SHF -06 has the key slot (".100 REF, only for -05 thru -25") and FFSD
    -06 accepts -N ("not available in -02 thru -04") `[prints, sheet 1 each]`.
  - `-RA` is correctly ordered without `-LC` ("not available with -RA").
  - The part number FFSD-06-D-xx.xx-01-N-RN2 follows the print's ordering
    syntax (blank plating = standard).
  - With a shrouded, keyed header, a socket cannot be seated skewed,
    offset or rotated.
  - Swapping a `-RN2` cable's ends, or the two key boards' cables, is
    harmless electrically. The markers catch a swap of key boards
    (key-chain-loom.md).
- **Is 3V3 ever on a GND pin?** Yes, under three plausible mistakes:
  - a standard (non-`-RN2`) cable, either way round (K2-1, K2-3);
  - a header soldered with its mouth backward (K2-7);
  - a key-board sheet renumbered to k → k, which no check would catch
    (K2-5).

  It does not happen with a forced or skewed socket, which the shroud
  prevents, or with a `-RN2` cable's ends swapped.
