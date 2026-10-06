# Hand-routing a board on Windows

How to open a Woody board in KiCad on a Windows PC, route part of it by hand
with KiCad's interactive (push-and-shove) router, and hand it back so the
repository's checks, renders and fab files are regenerated. Written for the
main board's tail corner (#40), but it works for any board under
`hardware/boards/`.

## 1. Install KiCad 9 (not 10)

- Download the **KiCad 9.0.x** Windows installer from
  <https://www.kicad.org/download/windows/>. Use the newest 9.0 release, and
  at least the version `tools/toolchain.yaml` names as `kicad_min`.
- **Do not use KiCad 10** (or a 10.x nightly). It silently upgrades the
  `.kicad_pcb` file format on save, and the repository's tools and checks run
  KiCad 9, so a board saved by 10 will not load here.
- Run the installer with the defaults. Tick the **3D models** component if
  you want the 3D viewer (Alt+3) to show real parts; routing does not need it.

## 2. Get the repository

1. Install **Git for Windows** from <https://git-scm.com/download/win>, or
   use GitHub Desktop.
2. Clone and check out the working branch:

   ```
   git clone https://github.com/jeffmhopkins/woody.git
   cd woody
   git checkout claude/car-instrument-cad-design-xvqwv2
   git pull
   ```

3. Make your own branch for the hand-routing, so it never collides with the
   agents' work:

   ```
   git checkout -b hand-route-main-board
   ```

## 3. Open the right file

Open the **project**, not the bare board file:

```
hardware\boards\main-board\main-board.kicad_pro
```

Double-click it, or use KiCad → File → Open Project. Then open the **PCB
Editor** from the project window.

- The project's own footprint library (`woody`) is found through the
  project's `fp-lib-table`, which points at `hardware/lib/woody.pretty`.
  Opening the `.kicad_pro` is what makes that work. If KiCad warns about a
  missing library, the project was not opened from the repository folder.
- **Ignore** these: `board-netlist.yaml`, `fab/`, `layout.yaml`, and every
  `*.png`. They are generated or read by the tools, and you never edit them
  by hand.

## 4. Find the corner

- The tail end is the **right-hand end** of the board in the editor. The
  crowded corner is around **J1** (J-MCU, the microcontroller connector),
  with **U6** (the level shifter), **J7** (J-MIDI), **U12**, **R48–R51**,
  **FB3/FB4** (the MIDI out), and **U13 / Q2** (the 5 V ideal-diode OR).
- To jump to a part: **Ctrl+F**, type the reference (e.g. `J1`), Enter.
- To see one layer at a time: in the Appearance panel on the right, click
  the layer name, and use **Ctrl+Shift+H** (high-contrast mode) to dim the
  others.
- `docs/review/2026-10-04-main-board-routing/REPORT.md` and issue #40
  describe what is wrong with the current routing there.

## 5. Unlock what you want to re-route

Most of the board's copper is **locked** on purpose, so the scripts never
disturb it, and a locked track cannot be dragged.

- Select the tracks and vias you want to redo (drag a box, or click one and
  press **U** to grow the selection along the net).
- Right-click → **Locking → Unlock**.
- Only unlock what you intend to change. Leave the **breath pair**
  (`SENSOR_BUFFERED_OUT` and its `AGND_INST` leg, with the ground guard tracks
  and stitching vias beside it) locked and untouched.

## 6. Route with push-and-shove

Set the router first: **Route → Interactive Router Settings**, mode
**Shove**, and tick *Optimize pad connections*.

| Key | Does |
|---|---|
| **X** | Route a single track from the pad or track under the cursor |
| **D** | Drag a track segment at 45°, pushing others aside (push-and-shove) |
| **G** | Drag a track at a free angle |
| **V** (while routing) | Drop a via and continue on the other outer layer |
| **PgUp / PgDn** (while routing) | Change layer |
| **/** | Flip the corner direction (posture) of the track being routed |
| **Backspace** | Undo the last segment while routing |
| **Esc** | Finish or cancel the current track |
| **Delete** | Delete the selected copper |
| **B** | Refill all copper zones (the planes) |

Track widths and clearances come from the board's **net classes**, so you
do not need to set them. Power nets are wider automatically.

House rules, from `docs/reference/tooling.md` *The routing policy*:

- Short, direct runs at 45°. Fixed layer directions only where a crowded
  corner needs them.
- Route families together: power first, then lines heading the same way as
  a bundle, then the rest.
- Vias only where a crossing needs one. **Power nets never take a small
  via**: use the via size their net class gives.
- Layer 2 (In1.Cu) is the solid ground plane: route nothing on it. Layer 3
  (In2.Cu) carries the +12 V plane and the analog-ground strip under the
  breath pair; do not route across the strip.

## 7. Check before you hand it back

1. Press **B** to refill the zones.
2. **Inspect → Design Rules Checker → Run DRC**, with *Test for parity
   between PCB and schematic* ticked. Aim for **0 errors and 0 unconnected
   items**; warnings about library footprints are expected.
3. **File → Save** (Ctrl+S). Do not use "Update PCB from Schematic"; the
   schematic is unchanged.

## 8. Hand it back

```
git add hardware/boards/main-board/main-board.kicad_pcb
git commit -m "#40: tail corner hand-routed in KiCad"
git push -u origin hand-route-main-board
```

Then tell Claude the branch name. Claude runs the repository's own checks
(`tools/kicad.py check --board main-board`, which also proves the board
still agrees with the body CAD), regenerates the renders and `fab/`, and
merges. Those tools need the Linux toolchain (`tools/setup-env.sh`), which
is why they run on Claude's side rather than on Windows.

**Commit only `main-board.kicad_pcb`.** KiCad may also touch
`main-board.kicad_pro` (window and view settings); leave that uncommitted
(`git checkout -- hardware/boards/main-board/main-board.kicad_pro`). The
`.kicad_prl` file and `*-backups/` folders it creates are already ignored.
