# hardware/lib — this project's own KiCad footprints

Parts KiCad's stock library does not have. Board projects reach it through
their `fp-lib-table` as the library `woody`.

| Footprint | From | Changed |
|---|---|---|
| `woody.pretty/SW_Gateron_KS33_1u` | `datasheets/mechanical/GATERON-KS-33-SW_KS33_1u.kicad_mod` — marbastlib (ebastler), banked with its URL and hash in `datasheets/MANIFEST.csv`. **Community-drawn, not Gateron's**; its pin positions are checked against Gateron's drawing (`GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`) in `docs/reference/ks33-geometry.md` | renamed to match its file; `exclude_from_bom` removed (the switch is bought — `SW1-n`); still excluded from pick-and-place files (hand-soldered) |
| `woody.pretty/IDC-Header_2x06_P1.27mm_Samtec_SHF_Horizontal` | KiCad's `Connector_PinHeader_1.27mm:PinHeader_2x06_P1.27mm_Horizontal` for the pads; the shroud from Samtec's banked catalogue page (`datasheets/connectors/SAMTEC-SHF-1.27MM-SHROUDED-IDC-HEADER.pdf`) | J-CHAIN, the key chain's right-angle IDC header (ADR 0017 amended). Body 13.97 long and 5.33 deep, its back 2.53 in front of the far (odd) pin row, measured at the bend, and its mouth at +x (the full print, `datasheets/connectors/SAMTEC-SHF-1XX-01-X-D-XX-PRINT.pdf`, sheet 2 section C-C); the courtyard takes in the FFSD plug standing out of the mouth (`boards.chain_plug_proud`, tbd). Pads Ø1.05 on the 0.65 drill: KiCad's Ø1.0 leaves a 0.175 ring, under JLC's 0.18 minimum. No 3D model (Samtec's is behind a login) |
