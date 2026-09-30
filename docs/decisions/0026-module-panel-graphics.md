# 0026 — The module panel's graphic language

**Status:** Accepted, 2026-09-30. The owner asked for the panel's graphics to
follow "the darker Pittsburgh Modular SV-1b / Lifeforms design language", and
for a Blender render of the result. The research behind this record was a
survey of Eurorack labelling conventions made the same day (reference photos
studied, none traced); its findings that decide something are cited below.
The owner settled the three choices it left open the same day, and revised
the artwork after the first rendered preview (point 7).

Every number this record decides is a leaf of `config/module.yaml` under
`art:`, with its status and source. Every zone is derived in
`mechanical/cad/module.scad` and checked by a rule in
`mechanical/module/drc.echo` (the `art:` and `art zone:` rules), named here
and not restated. The artwork's own placement rules are checked by
`tools/panel-art.py`, whose report is `mechanical/module/art/panel-art-check.txt`.

## Context

ADR 0024 placed every part on the panel and left **legend zones** beside
them, but nothing said what goes in them, how it looks, or how it is made.
The owner's reference is Pittsburgh Modular's black Lifeforms panels (the
SV-1b, the Primary Oscillator b). Reduced to rules, that language is: a black
frame with **mid-grey islands**, one per function, and **light-grey header
bars**, three tones and no accent colour; **all lowercase**, one grotesque,
two sizes; **inputs outlined, outputs plain**; **no knob scales** except a
bare − and + on an attenuverter; a small title top-centre and a maker line on
the frame. The survey found the field split between marking outputs
(Intellijel, Mutable, Befaco) and marking inputs (Pittsburgh, Make Noise's
arrows); either way, one class is boxed.

## Decision

1. **Three tones on black anodise, as named spot inks.** `SLATE` for the
   islands and `BAR` for the header pill, the six jack pills and the maker
   line, both over a white `UNDERBASE`; `WHITE` for every other word. Pill
   words are **knocked out** of `BAR`, so the anodise is the dark text and no
   dark ink is needed.
   Nothing else is coloured: the green LED is the only colour on the face.
   The preview colours and the contrast floor are `art.ink.*` and
   `art.min.contrast`; the report gives each pair's ratio.
2. **Inter, lowercase.** Inter 4.1 (SIL OFL 1.1) — a Helvetica-class
   neo-grotesque with a tall x-height, banked in `datasheets/fonts/`
   (fragment R33) — in Medium and SemiBold, at the sizes `art.size.*`, and
   set as outlines in every deliverable. `art.lowercase` lowercases whatever
   the text leaves say.
3. **Three islands, by function.** A: the three breath knobs, under a
   full-width `breath` header on the frame. B: the six jacks, **with no
   header** (point 4 says why). C: the LED, the toggle and the umbilical. The gutter between A
   and B runs between the first row's nuts and the pot legend bands; the one
   between B and C between the last row's nuts and the toggle's row. Rules
   `art: gutter …` and `art: gutter A|B between the first row's nuts and the
   pot legends`.
4. **Every jack's word is knocked out of a light-grey pill** — `pitch`,
   `breath`, `mod 1` … `mod 4` — filling its legend zone from the jack's side
   to just inside the island's edge, all six one size (the owner's revision,
   point 7). Every jack on this module is an output, and a solid box is the
   output mark in the convention Intellijel states and Mutable and Befaco
   follow, so the pills themselves say *output*: island B needs no header,
   and a `cv out` or `outputs` bar over it would say it twice. This departs
   from Pittsburgh, which boxes inputs; the module has none, so no box on the
   panel can be read as one. ADR 0004's write-on strip for the MOD jacks is
   dropped with the pads.
5. **Scales: only OFFSET's ends.** Offset is bipolar with its zero at the
   centre, so it gets a bare − and + at the R0904N's end stops (`art.mark.*`;
   the angle is half the banked datasheet's total rotation). Gain gets none.
   Curve gets none yet: its ends are named now, but no word fits there
   (`art.resp_marks`, open, below).
6. **Made from the CAD, checked, and registered.** `module.scad` derives
   every graphics zone from the layout and echoes every zone's position, every
   keep-out and every part's place to `mechanical/module/export/panel-art.echo`.
   `tools/panel-art.py` sets the words in the zones and fails on any breach of
   its rules (ink inside its zone, `art.min.print_cut` from every cut, off
   every nut, washer, knob budget and plug grip, `art.min.text`,
   `art.min.stroke` measured off the banked font, contrast, header padding,
   every word but the name and the maker line on an island). Its outputs — the SVG master, the
   spot-colour PDF, a proof, the report and the render textures — are
   `scripts:` outputs of `tools/cad.py`, fingerprinted against every file they
   read, so a moved zone marks the artwork stale.
7. **The owner's words, 2026-09-30**: the third knob is **`curve`**
   ("Replace response with curve"); the toggle is marked with the **words**
   `off` and `on`, not IEC 60417's O and I. **After the first preview render**
   the owner revised the artwork: the name `woody` moves to the top, between
   the two top panel screws (zone `name`, derived between their washers'
   reach); the title band under it carries the maker line **`space coast
   synthesizers`**, subdued — smaller (`art.size.maker`), Medium, in `BAR`'s
   grey — replacing the `WOODY / 2026` placeholder; the pill that read
   `cv out` becomes the `pitch` label; `breath` and `mod 1`–`mod 4` get the
   same pill; the write-on pads, the numerals and the `mod` label go; and
   the LED's `rack` label goes, because the LED is not rack power — it is lit
   while the toggle is on **and** the load switch delivers
   (`hardware/module/panel-led`), so it belongs to the power row it sits in.
   Every word is an `art.text.*` leaf, `settled`.
8. **Production: UV print on the black-anodised 2 mm aluminium ADR 0024
   already specifies**, CNC-cut from `export/panel.dxf` by the same vendor,
   with "use white ink" and "underprint white" set (Front Panel Express,
   Schaeffer). The PDF carries one optional-content layer per ink, each a
   named Separation colour with a CMYK alternate, overprint on, and the cut
   and a preview of the anodise on non-printing layers. **One proof panel
   before a run**, after a 1:1 paper print of `panel-art.pdf` over a cut
   template with the knobs, the plugs and the NE8MX fitted — ADR 0024's fit
   test.

## Consequences

- A printed FR-4 panel is **not** the prototype route: one silk colour cannot
  make both SLATE and BAR, and 1.6 mm is not the 2 mm the NE8FAV's and the
  toggle's `panel_max` were checked against.
- The ink pulls back `art.min.print_cut` from every hole, so a hole's edge
  shows a thin ring of bare anodise: that is the registration allowance, not a
  flaw.
- `jack.nut_d` is still `tbd`; the A|B and B|C gutters are derived from it,
  so a nut measured in hand moves the islands, and the rule above says
  whether the gutter still fits.
- The Blender renders (`tools/render-module.py`) read the same textures and
  the same echo, so they cannot show artwork the report did not check.

## Open, with what decides each

- **Curve's end marks** (`art.resp_marks`): the shaper page now names the
  ends (counter-clockwise logarithmic, clockwise exponential, the centre
  detent linear), but a word at the end stop does not fit outside the knob
  budget; the owner chooses words beside `curve` or glyphs.
- **The ink colours** (`art.ink.*`, nominal): the proof panel, photographed
  against a grey card.
- **The jack nut's diameter** (`jack.nut_d`, tbd), which places two gutters:
  a Thonkiconn nut measured or its drawing banked.
