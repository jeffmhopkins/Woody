# R5 — Fix audit, `383116e..eebcdfb`

**Slice:** R5, the fix audit (wave README, "Slices").
**Revision measured:** `eebcdfb` (HEAD `36341bf` differs from it only by the
wave README `[run: git diff --stat eebcdfb HEAD]`). `tools/` not modified; the
tools were run as they stand at `eebcdfb`.
**Cold:** nothing under `docs/review/` read except this wave's README.

**Commits audited** `[run: git log --oneline 383116e..eebcdfb]`, every text diff
read with `git show` (renders, Gerbers and `.kicad_pcb` bodies skimmed by stat;
`docs/review/` skipped):

| Commit | Subject |
|---|---|
| `cd264c1` | Register becomes the SN74HCS165; key-board standoff gets its washer |
| `22f82ec` | WIP: corpus follows the SN74HCS165 and the standoff washer |
| `1040a65` | Corpus follows the SN74HCS165 and the standoff washer; the owner's fallback |
| `eebcdfb` | LH key board: every key's network identical round its switch; no acid traps; silk both sides |

## Gates, as run

| Command | Result |
|---|---|
| `python3 tools/check-staleness.py` | `PASS no live stale values \| corpus 172 files, 23 circuits, 40 figures / 274 patterns \| 6 unresolved (tracked) \| 221 restated-not-cited (advisory)`, exit 0 `[run]` |
| `python3 tools/check-netlist.py --strict` | `22 circuit(s), 193 components, 246 nets, 64 master net(s) \| 0 problem(s)`, exit 0 `[run]` |
| `python3 tools/merge-bom.py --check` | `checked 158 rows from 26 fragments \| 0 problems`, exit 0 `[run]` |
| `python3 tools/kicad.py check` | `PASS - 3 source sheet(s), 2 board(s), 39 render(s) match their sources`, exit 0 `[run]` (runs `pcb.py check`, `tools/kicad.py:528-532`) |

All four pass. Every finding below is therefore something the gates cannot see.

## Findings

### R5-1 [medium] `config/body.yaml`'s hardware comment still says the standoff's length is not a parameter and the part is "a candidate, not a choice"

- **Node:** `hardware.kb_standoff_l`, `MECH-KB-STANDOFF`.
- **Shape:** 1 (a fix that did not reach the text beside it) and 4 (a statement its own new entries refute).
- **Introduced / missed by:** `cd264c1` (added `kb_standoff_l`, status `nominal`, and made the row `selected`); `1040a65` edited the same file and missed it.
- **Evidence:** `[repo config/body.yaml:729-736]` "The standoff's length is not a parameter: it is the plate-to-board gap the switch pins set (switch.pcb_below_seat less the plate), in drc.echo … it is a candidate, not a choice - see MECH-KB-STANDOFF and ADR 0020." Directly below it, `kb_standoff_l: value: 3, status: nominal, source: "MSO4-M2-3, the owner's choice 2026-09-27"` `[repo config/body.yaml:~755]`. `MECH-KB-STANDOFF` status is `selected` `[repo hardware/unplaced.csv:25]`. The comment is unchanged from `383116e` `[run: git show 383116e:config/body.yaml | grep -n "candidate, not a choice"` → line 731]. The derivation now runs the other way: the hardware sets `switch.pcb_below_seat` (ADR 0020 point 2's amendment). `decided_by: "M4, with the standoff chosen"` on `kb_standoff_od`, `kb_standoff_edge` and `kb_standoff_inset` `[repo config/body.yaml:741, 751, 792]` reads the same way. The remaining open question is whether the part clinches, not which part it is.
- **Fix:** rewrite the comment. The standoff is MSO4-M2-3 (`kb_standoff_l`). With the washer (`kb_washer_t`) it sets `switch.pcb_below_seat`, and PEM and the plate vendor confirm that it clinches. Change the three `decided_by` entries to "M4: PEM and the plate vendor confirm MSO4-M2-3 clinches". Then run `tools/cad.py build`, because `params.scad` carries the sources.

### R5-2 [medium] ADR 0020 cites a DRC rule that `cd264c1` deleted, in the present tense

- **Node:** `mechanical/drc.echo` rule "key-board standoff stocked lengths against the window".
- **Shape:** 1 (a renamed or deleted rule, not followed to the page citing it).
- **Introduced / missed by:** `cd264c1` removed the rule `[repo git show cd264c1 -- mechanical/drc.echo: the "-" line "key-board standoff stocked lengths against the window"]` and replaced it with "key-board standoff and washer set the board depth" and "key-board depth at the hardware's tolerance limits".
- **Evidence:** `[repo docs/decisions/0020-key-boards-screw-to-the-plate.md:143-153]` "neither length lands in the window the switch pins allow: `drc.echo` "key-board standoff stocked lengths against the window" prints both and the shim that would close the gap … So the first question for the plate vendor and PEM is whether MSO4-M2-3 with a shim, or the fallback above, holds the board." `[run: grep -c "stocked lengths" mechanical/drc.echo]` → 0. `[run: rules.py]` checks every quoted rule name near "drc.echo" in the corpus against `drc.echo`. This is the only dangling one this range created. The next bullet (the owner's choice) supersedes the shim, but it never says so. A reader who follows this bullet finds no such line and no shim.
- **Fix:** mark the bullet superseded in place: "*(Superseded the same day by the washer, below; the rule it cites was replaced by "key-board standoff and washer set the board depth".)*" Keep the rule name on the same line as the correction.

### R5-3 [low] `switch.pcb_below_seat` moved 3.4 → 3.3, and three pages still derive about 0.5 mm of pin from it

- **Node:** `boards.key_board_t` source; ADR 0020 point 6; the tooling history bullet.
- **Shape:** 1.
- **Introduced / missed by:** `cd264c1` fixed `docs/reference/ks33-geometry.md:110-116` (now "a little higher than the middle, so they show a little more pin") and missed the pages that restate the same arithmetic.
- **Evidence:** `[calc]` pin below a 1.2 mm key board = 5.10 − `switch.pcb_below_seat` − 1.2 = 5.10 − 3.3 − 1.2 = **0.6 mm** (it was 0.5 at 3.4). Still stated as ~0.5 against `switch.pcb_below_seat` by name:
  - `[repo config/body.yaml:448]` `key_board_t` source: "the board top is switch.pcb_below_seat below it, so … 1.2 mm ~0.5 mm". The same text is in `mechanical/cad/generated/params.scad:106`.
  - `[repo docs/decisions/0020-key-boards-screw-to-the-plate.md:98-100]` "the board's top is `switch.pcb_below_seat` below it. … on 1.2 mm about 0.5 mm".
  - `[repo docs/reference/tooling.md:391-392]` "The key boards are now 1.2 mm, which leaves about 0.5 mm".
- The 1.6 mm / 0.1 mm statements are still right for the thumb switches at `switch.thumb_pcb_below_seat` = 3.4 `[calc: 5.10 − 3.4 − 1.6 = 0.1]`.
- **Fix:** do not restate the number. Say "at the window's middle, ~0.5 mm; the key boards sit a little higher (`switch.pcb_below_seat`) and show a little more", citing `ks33-geometry.md`, as that page now does.

### R5-4 [low] `switch.pcb_below_seat_window`'s source still says "pcb_below_seat is its middle"

- **Node:** `switch.pcb_below_seat_window`.
- **Shape:** 1.
- **Introduced / missed by:** `cd264c1`.
- **Evidence:** `[repo config/body.yaml:270]` "…some pin to solder; pcb_below_seat is its middle", which is also in `params.scad:73`. The window is [3.2, 3.6], so its middle is 3.4 `[calc]`. `switch.pcb_below_seat` is 3.3 `[repo config/body.yaml:241]`. The parameter that now sits at the middle is `switch.thumb_pcb_below_seat` `[repo config/body.yaml:235-238]`.
- **Fix:** change it to "switch.thumb_pcb_below_seat is its middle; the key boards' switch.pcb_below_seat is set by their hardware, inside it".

### R5-5 [low] ADR 0020 point 4 still says the standoff's end face is what covers the top keep-out

- **Node:** the standoff keep-out on `F.Cu` (every `H-*` hole footprint on `key-board-lh`).
- **Shape:** 1.
- **Introduced / missed by:** `cd264c1`. The echoed diameter became `max(hardware_kb_standoff_od, hardware_kb_washer_od)` = 4.5 `[repo mechanical/cad/woody_body.scad:699-701; mechanical/export/pcb-geometry.echo:7-10]`. `tooling.md:387-389` was updated in `1040a65`, and ADR 0020 was not.
- **Evidence:**
  - `[repo docs/decisions/0020-key-boards-screw-to-the-plate.md:66-71]` "On top it is covered by the standoff's end face … `tools/pcb.py` places the keep-out from the CAD's standoff diameter and screw head". The washer (OD 4.5) is what bears on the top copper now.
  - Same shape, advisory: `[repo mechanical/cad/woody_body.scad:1096]` "no parts under a screw head: the PCB keeps the same circle clear". The CAD parts envelope excludes a 3.8 circle (`max(screw_head_d 3.8, standoff_od 3.16)`), while the PCB keep-out is now 4.5 + 2 × clearance `[repo tools/pcb.py:682]`. So the circles are no longer the same. The CAD is the more permissive of the two, so a part envelope could pass CAD and fail PCB.
  - The comment at `tools/pcb.py:677` ("The standoff's end face presses on the top copper") is in frozen `tools/` and is recorded here only.
- **Fix:** in ADR 0020 point 4, write "On top it is covered by the washer (`MECH-KB-WASHER`, `hardware.kb_washer_od`)…". Make the scad envelope use the same `max(...)` as the echo, or reword its comment.

### R5-6 [low] `latency-budget.md` says the key press is "two orders of magnitude inside the scan period": it is 25×

- **Node:** `key-press-time`.
- **Shape:** 4 (a conclusion its own corrected number refutes).
- **Introduced / missed by:** `cd264c1` moved `key-press-time` 5.92 → 9.87 µs. `22f82ec` edited the very next row of the same table (`latency-budget.md:98`) and left this one.
- **Evidence:** `[repo docs/reference/latency-budget.md:96]` "Two orders of magnitude inside the scan period". `[calc]` 250 / 9.87 = 25.3×, which is 1.4 orders. The owner says "25× inside the 250 µs scan" `[repo hardware/cluster/key-switch-network/key-switch-network.md:96]`, and so does `figures.yaml` `key-press-time.note`. The sentence was already an overstatement at 42× (1.6 orders), and the move made it worse. ADR 0001's "far inside the 250 µs scan" `[repo docs/decisions/0001-mcu-and-board-partitioning.md:241]` is fine.
- **Fix:** "Far inside the scan period (the figure's `note`)". Do not restate 25×.

### R5-7 [low] The `R-KEY-SER` row still names the plain-HC thresholds `V_IL` / `V_IH`

- **Node:** `R-KEY-SER` (`hardware/cluster/key-switch-network/bom.csv:4`, master `hardware/bom.csv:37`).
- **Shape:** 1.
- **Introduced / missed by:** `22f82ec` rewrote the sibling `C-KEY` row to "the register's lower threshold (VT-, at its minimum) … upper threshold (VT+, at its maximum)" and left `R-KEY-SER`. `1040a65`'s BOM list ("C-KEY, TP-CHAIN, PCB-CLUSTER, R-CHAIN-SER, U-KEYS") does not include it.
- **Evidence:** `[repo hardware/cluster/key-switch-network/bom.csv:4]` "press crosses V_IL at key-press-time so it stays instant, and release crosses V_IH at key-release-time". Both figures are now defined against the SN74HCS165's VT− min and VT+ max `[repo config/figures.yaml:218-223, 238-243]`. The SN74HCS165 table has no `V_IH`/`V_IL` rows, only VT+, VT− and ΔVT `[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.6, §6.5]`. There is no wrong number here, but the row points a reader at thresholds the fitted part does not have.
- **Fix:** use the `C-KEY` wording ("the register's lower/upper threshold, VT−/VT+, at key-press-time / key-release-time"), edit the fragment, and run `merge-bom.py`.

### R5-8 [low] The new forbidden patterns miss the CSV spellings of the retired thresholds, against the escape note written in the same commit

- **Node:** `config/figures.yaml` `key-release-time.forbidden`, `key-press-time.forbidden`.
- **Shape:** 2 (the fix's own explanation states the rule the fix breaks).
- **Introduced by:** `cd264c1`. Its new `escape_note` ends "Patterns for a retired value go in both spellings." `[repo config/figures.yaml:226-231]`.
- **Evidence** `[run: scratchpad/R5/pat.py]` (each pattern `git grep -F` at `383116e`, at `cd264c1^` and at `eebcdfb`, over the §6 corpus):
  - The crossing-time patterns are sound. `at **119.9`, `→ 119.9 µs`, `at **5.92` and `42× inside the 250` each fired at `383116e` on ADR 0001 and on `key-switch-network.md`. At `eebcdfb` they fire only in `figures.yaml` (the list itself) and in `key-switch-network/notes.md`, which the checker counts as refuted in place. `119.9us`, `5.92us` and `42x inside the 250` are CSV spellings that matched nothing at either revision (pre-emptive, harmless).
  - The threshold patterns `V_IH = 2.31 V` and `V_IL = 0.99 V` matched **only `config/figures.yaml` itself** at `383116e`, never a derived page.
  - The CSV spellings that were actually live at `383116e`, in `C-KEY` (fragment and master), are "`VIL (0.99V at 3.3V)`", "`VIH (2.31V)`" and "`above the HC165's VIL`" `[run: git grep -F "VIH (2.31V)" 383116e` → `hardware/bom.csv`, `hardware/cluster/key-switch-network/bom.csv`]. No pattern covers any of them.
  - Tested: `VIH (2.31V)`, `VIL (0.99V` and `HC165's VIL` each fire on both CSVs at `383116e` and on **nothing** at `eebcdfb` `[run]`, so adding them costs no false positive.
- The four patterns removed because they matched the new value (`at **138.7`, `crosses \`V_IH\` at **138.7`, `0.75 x VCC = 2.475`, `0.75 × VCC = 2.475`) were right to go: the owner now says "passes VT+ max at **138.7 µs**" `[repo key-switch-network.md:95]`, and `figures.yaml` says "0.75 x VCC".
- **Fix:** add `"VIH (2.31V)"`, `"VIL (0.99V"` and `"HC165's VIL"` to the two entries.

### R5-9 [low] `pcb.py check`'s new acid-trap test is missing from both lists of what `check` fails on

- **Node:** `tools/pcb.py` `check_tracks` (the "two tracks meet at < 90°" error).
- **Shape:** 3 (the list moved under the sentence enumerating it).
- **Introduced by:** `eebcdfb`. The commit message says "a new pcb.py check fails on any"; `check_tracks` is at `[repo tools/pcb.py:909-928]` and is called from `cmd_check` `[repo tools/pcb.py:~1023, "bad += check_tracks(board)"]`.
- **Evidence:** `[repo docs/reference/tooling.md:263-277]` "**`check` fails on**, every line an error:" lists DRC and parity, the design settings, silk and the body CAD, but no track-angle test. `[repo hardware/boards/key-board-lh/README.md:77-86]` "`pcb.py check` fails on any of these:" has the same omission. `eebcdfb` edited both files and updated neither list. `[run: grep -n -i "acute\|acid" docs/reference/tooling.md]` → nothing.
- **Fix:** add a bullet to both lists: "two tracks of one net meeting on one layer at under 90° (an acid trap; KiCad's DRC has no such test)".

### R5-10 [advisory] The README says `networks:`, `parts:` and `silk:` are the layout-only keys: `route_first:` is one too, and nothing checks the owner's rule afterwards

- **Node:** `hardware/boards/key-board-lh/layout.yaml` `route_first:` and `networks: pattern`.
- **Shape:** 3.
- **Introduced by:** `eebcdfb`.
- **Evidence:** `[repo hardware/boards/key-board-lh/README.md:35]` "`networks:`, `parts:` and `silk:` are read only by `pcb.py layout`". `route_first` is read by `tools/pcb_route.py:516-518`, which runs at layout only. So the owner's rule ("every key's network identical round its switch") is a layout-time property: once the `.kicad_pcb` is hand-edited (it is the source after layout, `README.md:34`), no check holds it `[repo tools/pcb.py:231, the only reader of networks]`. This belongs to R6's domain and is noted here for the ledger.
- **Fix:** add `route_first:` to the sentence. Either state that the network pattern is not re-checked after a hand edit, or add a check.

### R5-11 [advisory] Two superseded ADRs still state the 74HC165 as settled

- **Node:** `U-KEYS`.
- **Shape:** 1.
- **Missed by:** `22f82ec` / `1040a65`, whose sweep amended ADRs 0001, 0005, 0009 and 0010.
- **Evidence:** `[repo docs/decisions/0013-two-mcu-split.md:263]` "It is settled the other way: **one 74HC165 per cluster**". `[repo docs/decisions/0008-display-selection.md:109]` "The 74HC165 chain reads all 18 switches". Both ADRs carry **Status: Superseded** by ADR 0015 (line 3), so neither is a live instruction. ADR 0001's amendment covers only its own text ("The wording "74HC165" that remains above records the reasoning at the time", `0001:408`).
- **Fix:** none required. Optionally, write "74x165", as ADR 0005 now does.

### R5-12 [advisory] The owner's new standoff fallback did not reach `MECH-KB-SCREW`

- **Node:** `MECH-KB-SCREW` (`hardware/unplaced.csv:27`, `hardware/bom.csv:152`).
- **Shape:** 1.
- **Introduced by:** `1040a65`, which added the fallback to ADR 0020 (`:174-181`) and to `MECH-KB-STANDOFF`.
- **Evidence:** The fallback runs a screw up through the board, the washer, a spacer and a clearance hole in the plate into a nut on the plate's top face `[repo docs/decisions/0020-key-boards-screw-to-the-plate.md:174-181]`. That needs roughly 1.2 + 0.3 + 1.8 + 1.2 + a nut `[calc; the spacer is 2.1 − 0.3 per the ADR's "spacer plus washer replaces the standoff's reach"; M2 nut height ~1.6 from memory]`, about 6 mm. The row fixes "M2 x 4" and says a longer screw "stands above the plate's top face into the oak", which is exactly what the fallback designs for (the pocket in the oak). No nut row exists. It is correct for the chosen part and silent on the fallback.
- **Fix:** add one clause to `MECH-KB-SCREW`: "with ADR 0020's fallback, longer — through the plate into a nut in the oak's pocket; sized when the fallback is taken".

### R5-13 [advisory] The retired derivation in `key-switch-network/notes.md` is announced as "verbatim" but carries inserted markers

- **Node:** `key-release-time`, `key-press-time` (history).
- **Shape:** 2 (the fix's own framing is not true of the text it frames).
- **Introduced by:** `cd264c1`.
- **Evidence:** `[repo hardware/cluster/key-switch-network/notes.md:43]` "What the page said until then, verbatim:". Lines 79, 109, 138 and 139 contain "(retired, 74HC165)", which is not in the source text `[run: git show cd264c1^:hardware/cluster/key-switch-network/key-switch-network.md]`. The markers are what let `check-staleness.py` exempt table rows under rule 2b's same-line requirement. They are useful, but they make "verbatim" false. Relatedly, `[repo hardware/cluster/key-register/notes.md:23-24]` "thresholds against onsemi's published 3.0 V row — see §Derivations": §Derivations now derives the SN74HCS165's thresholds, and the onsemi table is in `key-switch-network/notes.md`.
- **Fix:** write "verbatim, with each retired figure marked (retired, 74HC165)". Point `key-register/notes.md`'s "see §Derivations" at `key-switch-network/notes.md`.

### R5-14 [advisory] ADR 0001's history quote says `C-KEY` "now carries these figures"

- **Node:** `C-KEY`, `key-release-time`, `key-press-time`.
- **Shape:** 1.
- **Missed by:** `cd264c1`, which replaced the table's figures with citations.
- **Evidence:** `[repo docs/decisions/0001-mcu-and-board-partitioning.md:245-251]` "`bom.csv` row `C-KEY` carried the stale the superseded "~1.4 us / 176x" pair until this edit and now carries these figures". The table above it now carries only figure names (`0001:240-241`). `C-KEY` deliberately does not restate the figures ("The thresholds are those figures' threshold_note, not restated here", `hardware/cluster/key-switch-network/bom.csv:5`). The sentence is also garbled ("the stale the superseded").
- **Fix:** "…until this edit, and now cites `key-release-time` / `key-press-time`."

### R5-15 [advisory] The test pads' stated order and the register's pins disagree for SER/QH

- **Node:** `TP-SER-LH`, `TP-QH-LH`, `U-KEYS-LH` pins 9 and 10.
- **Shape:** 2.
- **Introduced by:** `eebcdfb`.
- **Evidence:** `[repo hardware/boards/key-board-lh/layout.yaml:79-82]` "in the order of the register's own pins above them - SER and QH by pins 10 and 9 … so no chain net crosses another's pad". `[run: pcbnew.LoadBoard, pad positions, PCB mm]`: U-KEYS-LH pin 9 (`/HOP_LH_LT`, QH) is at x 146.06 and pin 10 (`/CHAIN_SER_LH`) at x 147.32, but TP-SER-LH is at x 143.0, left of TP-QH-LH at x 146.5. Along x, the SER/QH pads are therefore in the reverse order of their pins. The rest runs left to right: GND pin 8 at 146.06 → pad 150.0; SCK pin 2 at 153.68 → pad 153.5; SH/LD pin 1 at 154.94 → pad 157.0; 3V3 pin 16 at 154.94 → pad 160.5. `pcb.py check` passes, so nothing is shorted or unrouted. The claim is about ordering, and whether the crossing matters is R3's call.
- **Fix:** R3 to judge. Either swap TP-SER/TP-QH or reword the comment and the README's "in the register's pin order" (`README.md:251`).

### R5-16 [advisory] The dated `unplaced.csv` count table in `pcb-pipeline.md` moved again

- **Node:** `hardware/unplaced.csv`.
- **Shape:** 3.
- **Moved by:** `cd264c1` (added `MECH-KB-WASHER`, qty 8).
- **Evidence:** `[repo docs/reference/pcb-pipeline.md:149-155]` says "Re-measured against the current tree, 2026-09-21: … `unplaced.csv` … **34** rows, **75** units". `[run: csv count]` gives 32 rows / 78 units at `383116e` and 33 / 86 at `eebcdfb`. The table is dated and was already off before this range, so this is not a regression of it. It is recorded because the washer moved it and a reader may take it as current.
- **Fix:** replace the table with "`wc -l hardware/unplaced.csv` is the count", as `hardware/README.md:183` already does.

## Checked and found consistent

- **The part switch, part name.** `[run: grep -rn 74HC165 over the §6 corpus, excluding "HCS"]` Every remaining hit is one of the following:
  - history in `notes.md` files;
  - ADR 0001 text covered by its amendment (`0001:408`);
  - the explicit "not a plain 74HC165" warnings (`README.md:165`, `key-register.md:73,80`, `key-switch-network.md:88`);
  - the KiCad library symbol id `74xx:74HC165` and its cached `Value` (`key-register.kicad_sch:19,28`). The instance `Value` is `74HCS165`, the MPN `SN74HCS165DR` and the LCSC `C2864745` (`:394, 402-403`);
  - the path map, and R5-11.

  The old LCSC `C5613` and MPN `SN74HC165` appear nowhere live `[run]`. `U-KEYS` (fragment and master), `board-netlist.yaml` (both boards), the `fab/…bom-jlc.csv`, `nets.yaml`, `spi-link.md`, the `key-chain-loom.md` drawing, `cluster-boards.md`, `key-layout.yaml`, `allocation.yaml`, ROADMAP E4 and ADRs 0005 and 0010 all follow.
- **Timing figures.**
  - `[calc]` release: 103.40 × ln(3.1565/0.825) = 138.7 µs. Press: 4.4957 × ln(3.1565/0.3515) = 9.87 µs. 10 kΩ trade: 470 × ln(3.267/0.825) = 646.9 µs ≈ 647. Interpolations 2.358 V → 125.0 µs and 0.612 V → 8.58 µs. The "about 4.5 µs" 0 V-start error: 103.4 × ln(3.3/0.825) − 138.7 = 4.6.
  - Thresholds: TI VT+ max 1.5/3.15/4.2 and VT− min 0.3/0.9/1.2 at 2/4.5/6 V; ΔVT min 0.2/0.4/0.6; VT− max ≤ 0.5 × VCC in every row (1.0/2 = 0.50, 2.2/4.5 = 0.49, 3.0/6 = 0.50) `[datasheets/logic/SN74HCS165-ti-scls828a.pdf p.6]`, so ADR 0001's and `C-KEY`'s "1.94 V clears 1.65 V by about 0.3 V" holds.
  - Nexperia 74HCS165 at 3.0–3.6 V: VT+ max 0.7 VCC, VT− min 0.2 VCC, both inside the bound `[datasheets/logic/74HCS165-nexperia.pdf p.6]`.
  - CLK→QH 18 ns max at 4.5 V and 45 at 2 V `[same TI, p.7]`, matching `spi-link.md`. tt 5/8 ns at 4.5 V `[p.8]`, stated the same way in ADR 0001, `key-register.md`, `key-chain-loom.md` and `U-KEYS`.
  - "just over half a scan": 138.7/250 = 0.55 `[calc]`, in ADR 0001, `key-switch-network.md` and `figures.yaml role_note`. No "under half a scan" survives `[run: grep]`.
- **Every citation of `key-release-time` / `key-press-time`** in the corpus `[run: grep]` cites by name. Only the owner restates them (`key-switch-network.md:95-96`). Apart from R5-6 and R5-7, all wording is correct.
- **The standoff and depth.**
  - `[calc]` 3 + 0.3 = 3.3 = `switch.pcb_below_seat`. Limits 3 − 0.08 + 0.25 = 3.17 and 3 + 0.05 + 0.35 = 3.40, against [3.2, 3.6], which matches `drc.echo` "key-board depth at the hardware's tolerance limits" and ADR 0020's "a few hundredths". Standoff below the plate 3 − 1.2 = 1.8, plus the washer 0.3 = 2.1 = "key-board standoff length (derived)".
  - M2 × 4 against the THROUGH limit 1.2 + 2.1 + 1.2 = 4.5, leaving 2.5 engaged `[calc]`.
  - The drc.echo shifts follow from the board rising 0.1: parts room 14.1 → 14.2, gap 17.4 → 17.5, pin tails 1.25 → 1.15, fold 2.725 → 2.775, ribbon 104.27 → 104.37.
  - None of the retired values (14.1, 17.4, 1.25, 2.725, 104.27, 2.2 standoff, "0.2 to 0.6" shim) is restated anywhere in the corpus `[run: grep]`.
  - The FFSD code stays 4.48, consistent with `chain_order_in` = ceil((104.37 + 2t + 3.175)/25.4 × 100)/100 `[repo mechanical/cad/woody_body.scad:929]`.
  - "tbd parameters in play" stays 92: one removed (`kb_standoff_stock_l`) and one added (`thumb_pcb_below_seat`) `[repo drc.echo:2 diff]`.
  - `clash.txt`: 132 → 140 solids (+8 washers), still 100 allowed, no count restated elsewhere `[run: grep]`.
  - ADR 0017's "not at its worst case" (13.1 fits and 14.6 does not, against 14.2) still holds.
  - `switch.thumb_pcb_below_seat` is used for the thumb board in `woody_body.scad:788` and is cited correctly in `cluster-boards.md:121`, `DESIGN.md:46` and ADR 0020.
- **The fallback.** ADR 0020's old self-clinching-nut fallback (`:139-141`) is refuted in place by "This replaces the self-clinching-nut fallback above" (`:181`). `MECH-KB-STANDOFF` carries the new one. The README's *Open* row and `cluster-boards.md` Still-open both say "ADR 0020's fallback".
- **Test pads.** "six" and the six names agree in the `TP-CHAIN` row (fragment and master), the README (`:113, :203, :233, :251`) and `layout.yaml`. No live "five".
- **Drill files.** The README (`:45`), `tooling.md` (`:284`) and `SHEETS.csv` name `key-board-lh-PTH.drl` / `-NPTH.drl`, which match `fab/` `[run: ls]`. The tools present match the README's description: PTH 0.3/0.7/1.3, NPTH 2.2/5.25. `fab/` holds 16 files, as the README's list describes `[run: ls]`.
- **Network pattern and silk.** `tooling.md:243, 247`, the README (`:103-108, :220-243`) and `layout.yaml` describe the same `pattern`/`except`/`add_top_silk`/`top_at`. No old per-key wording ("above its switch", "one entry per key") survives `[run: grep]`.
- **ESD.** No live "over 2000 V" / 74HC165 HBM remains. `cluster-boards.md:243` and `key-chain-loom.md:365` cite ±4000 V HBM / ±1500 V CDM from TI p.4.
- **Retired figure fields.** No page still cites the removed `conservative_bound` `[run: grep]`.
