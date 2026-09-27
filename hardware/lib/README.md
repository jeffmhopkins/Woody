# hardware/lib — this project's own KiCad footprints

Parts KiCad's stock library does not have. Board projects reach it through
their `fp-lib-table` as the library `woody`.

| Footprint | From | Changed |
|---|---|---|
| `woody.pretty/SW_Gateron_KS33_1u` | `datasheets/mechanical/GATERON-KS-33-SW_KS33_1u.kicad_mod` — marbastlib (ebastler), banked with its URL and hash in `datasheets/MANIFEST.csv`. **Community-drawn, not Gateron's**; its pin positions are checked against Gateron's drawing (`GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`) in `docs/reference/ks33-geometry.md` | renamed to match its file; `exclude_from_bom` removed (the switch is bought — `SW1-n`); still excluded from pick-and-place files (hand-soldered) |
