# hardware/lib — this project's own KiCad footprints

Parts KiCad's stock library does not have. Board projects reach it through
their `fp-lib-table` as the library `woody`.

| Footprint | From | Changed |
|---|---|---|
| `woody.pretty/SW_Gateron_KS33_1u` | `datasheets/mechanical/GATERON-KS-33-SW_KS33_1u.kicad_mod` — marbastlib (ebastler), banked with its URL and hash in `datasheets/MANIFEST.csv`. **Community-drawn, not Gateron's**; its pin positions are checked against Gateron's drawing (`GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`) in `docs/reference/ks33-geometry.md` | renamed to match its file; `exclude_from_bom` removed (the switch is bought — `SW1-n`); still excluded from pick-and-place files (hand-soldered) |
| `woody.pretty/IDC-Header_2x06_P1.27mm_Samtec_SHF_Horizontal` | KiCad's `Connector_PinHeader_1.27mm:PinHeader_2x06_P1.27mm_Horizontal` for the pads; the shroud from Samtec's banked catalogue page (`datasheets/connectors/SAMTEC-SHF-1.27MM-SHROUDED-IDC-HEADER.pdf`) | J-CHAIN, the key chain's right-angle IDC header (ADR 0017 amended). Body 13.97 long and 5.33 deep with its mouth at +x; the courtyard takes in the FFSD plug standing out of the mouth. The right-angle view's depth and height are not legible on the catalogue page, so they are `config/body.yaml` `boards.chain_hdr_*`, `tbd` until the full print. No 3D model |
