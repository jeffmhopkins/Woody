# Left-hand key board — `key-board-lh`

The left hand's five keys (LH1–LH5) and their register. The board is screwed to
the underside of the key plate (ADR 0020), and one IDC ribbon runs from it to
the main board (ADR 0017, amended). **This board is the project's worked
example.** Every other board is laid out, checked and ordered the way this one
is.

What each circuit does, and why, is on its page:
- [`key-register`](../../cluster/key-register/key-register.md)
- [`key-switch-network`](../../cluster/key-switch-network/key-switch-network.md)
- [`key-marker-and-bits`](../../cluster/key-marker-and-bits/key-marker-and-bits.md)
- [`cluster-boards.md`](../../cluster/cluster-boards.md)
- the ribbon: [`key-chain-loom.md`](../../interfaces/key-chain-loom/key-chain-loom.md)

This page covers the board as a made thing.

## Files — what is source, what is generated

| File | What it is |
|---|---|
| `key-board-lh.kicad_sch` (+ the three circuit sheets it places) | **Source.** Every connection, and each part's identity: `Row`, `Pins`, `Manufacturer`, `MPN`, `LCSC`, `Assembly` (ADR 0019) |
| `key-board-lh.kicad_pcb` | **Source**, once laid out: edit it in KiCad 9 |
| `layout.yaml` | How the first layout was made: part positions, routing rules, the board house's limits (`fab:`), the silkscreen title |
| `board-netlist.yaml` | Exported from the sheets (`tools/kicad.py export`) |
| `*.sch.png`, `*.pcb-*.png` | Renders, recorded in `hardware/SHEETS.csv` |
| `fab/` | **Generated** by `tools/pcb.py render`, and recorded in the ledger against the board *and* the sheets. Never edit it by hand |

`fab/` holds:
- Gerbers: both coppers, pastes, silkscreens and masks, plus the edge.
- `key-board-lh-job.gbrjob`, which carries thickness and finish.
- `key-board-lh.drl`.
- `key-board-lh-pos.csv`, KiCad's own placement export.
- For JLCPCB:
  - `key-board-lh-bom-jlc.csv` — the machine-placed parts, with LCSC numbers.
  - `key-board-lh-cpl-jlc.csv` — their placement.
  - `key-board-lh-hand-assembly.csv` — the parts fitted by hand.

Rebuild and check:

```
python3 tools/kicad.py export hardware/boards/key-board-lh   # sheets -> board-netlist.yaml, ERC
python3 tools/pcb.py check hardware/boards/key-board-lh      # DRC + schematic parity + the body CAD's positions
python3 tools/pcb.py render hardware/boards/key-board-lh     # renders and fab/
python3 tools/kicad.py check                                 # everything above is current
```

`tools/pcb.py layout … --force` rebuilds the board from scratch, from
`layout.yaml` and the body CAD. It overwrites any hand edits, so run it only
while `layout.yaml` is still the record of the layout. `docs/reference/tooling.md`
§4 covers the tools.

## Ordering it — JLCPCB

The board house is JLCPCB. Its limits are banked in `datasheets/fab/`, and they
are in `layout.yaml` `fab:`, so KiCad's DRC checks this board against them.

**The bare board**

| Setting | Value | Why |
|---|---|---|
| Layers | 2 | |
| Thickness | 1.2 mm | `config/body.yaml` `boards.key_board_t` (ADR 0020); a standard JLC thickness |
| Material | FR-4 | |
| Surface finish | HASL lead-free | At 1.2 mm, JLC's Economic assembly offers HASL only. It is also in the board's stackup and the Gerber job file |
| Solder mask | Green | Economic assembly at 1.2 mm offers green or black |
| Copper | 1 oz | |
| Outline | `Edge.Cuts` | The body CAD's key board (`mechanical/export/key-board-lh.dxf`): rounded corners, four M2 holes |

Upload `fab/` zipped: every `.gbr` file, the `.drl` and the `.gbrjob`.

**Assembly — Economic PCBA, bottom side only**

- **Every machine-placed part is on the bottom** (the side facing the main board).
- **Upload** `fab/key-board-lh-bom-jlc.csv` as the BOM and `fab/key-board-lh-cpl-jlc.csv` as the CPL.
  - The designators are this project's references, such as `R-KEY-SER-LH1`.
- **Check every part's orientation in JLC's placement preview before you pay.**
  - The CPL carries KiCad's own rotation.
  - JLC applies its tape-orientation corrections itself (`datasheets/fab/JLCPCB-KICAD-BOM-CPL-GUIDE.pdf`). We do not guess them.
  - The 74HC165's pin 1 is marked on the silkscreen, and that is the one to look at.
- **Which parts are in the order:**
  - The parts carry JLC Basic numbers, except the 74HC165: Nexperia 74HC165D, C5613, a "Preferred" Extended part with no loading fee on Economic.
  - **Not in the order:** the five switches, `J-CHAIN` (none in stock at JLC — see its BOM row), the test pads and the M2 holes.
- **The sheets are the source of every part number.** To change a part, set its `LCSC`/`MPN` fields in the circuit sheet and re-render. The BOM row (`hardware/cluster/bom.csv` etc.) says what the part must be; the sheet says which one is bought.

## Assembling the rest by hand

1. **J-CHAIN** (Samtec SHF-106-01-L-D-RA).
   - It goes on the bottom side, mouth toward the tail, and is soldered from the top (switch) side.
   - Its tails stand out of the top face and face the key plate's window (`mechanical/export/plate-top.dxf`), so they need no trimming.
   - Pin 1 is the dot on the silkscreen.
2. **The switches go into the plate first.**
   - Clip the five KS-33s into the key plate's cutouts.
   - Lower the board onto their pins and the plate's four M2 standoffs.
   - Fit the four M2 screws (`MECH-KB-SCREW`) from the bottom.
   - **Then** solder the switch pins, from the bottom. Soldering with the board screwed to the plate is what holds the board at the depth the pins were designed for (`switch.pcb_below_seat`).
3. **The ribbon** (`CBL-CHAIN`, ordered `-RN2`, notch reversed on the key-board end).
   - Plug it in with the lid laid face down beside the body, off its far edge, before the lid is screwed down. That is the length it was made for (`mechanical/drc.echo` "key-chain ribbon length (derived)").

## Bring-up

Before the first key board goes into an instrument, check it on the bench. The five test pads are on the bottom, labelled 3V3, GND, SCK, SH/LD and QH.

1. **No shorts.** Measure TP-3V3 to TP-GND with no power: it must not read as a short.
2. **The cable's pinout, with a meter, on the first cable.**
   - With both ends free, main-board-end conductor 10 must reach the key-board socket's position 3 (3V3), and conductor 2 its position 11 (SCK).
   - That is the `-RN2` map, key pin = 13 − main pin (`key-chain-loom.md`).
   - A cable without `-RN2` puts 3V3 on a ground pin.
3. **Power.** Feed 3.3 V between TP-3V3 and TP-GND (current-limited to ~20 mA).
   - With no key pressed, the only draw is the 74HC165's quiescent current and leakage.
   - Each pressed key adds its pull-up's current, about 1.4 mA [calc: 3.3 V across R-KEY-PU's 2k2 and R-KEY-SER's 100R].
4. **The chain.** Drive SH/LD low then high, then clock SCK, and watch QH.
   - It shifts out this board's eight bits: H..D are LH1..LH5, then the marker and free bits, per `key-marker-and-bits/allocation.yaml`.
   - Each key reads low while pressed.
   - Firmware normally does this; with a logic analyser on the test pads it is visible without one.

## Open, and what decides each

| Open | Decided by |
|---|---|
| The FFSD socket's stand-out from the header's mouth: `boards.chain_plug_proud`, which sets the ribbon's fold (the print does not dimension it) | M4, the first mated pair |
| The M2 standoff's stocked length and the plate alloy it clinches into (ADR 0020) | the plate vendor, M4 |
| J-CHAIN's source (0 at JLC): buy from Samtec or a distributor, or validate a stocked alternative against its print | the first order |
| Part orientation in JLC's placement preview (above) | the first order |
| No 3D model of J-CHAIN in the renders (Samtec's is behind a login; `datasheets/.manifest-R12.csv` records the attempt) | nothing blocks on it |
| The main board's end of the ribbon | the main board's layout |
