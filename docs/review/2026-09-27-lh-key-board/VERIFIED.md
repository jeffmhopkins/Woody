# VERIFIED — how the findings were checked, and where someone was wrong

The finding ledger is `FINDINGS.csv` (generated). `STATUS.md` answers every id
in it. This file says **how** each group was checked, and records every place a
slice, a fixing agent or the orchestrator was wrong, because a wrong finding is
caught by the next reviewer, and a finding wrongly filed as handled is not.

## Method of the fix round

Three fixing agents worked alongside the orchestrator, each on a disjoint set of
files:
- a docs pass (33 ids);
- a research pass (datasheets and part data);
- a checks and reproducibility pass (K7, K3-2, K3-10), in its own worktree, merged at `fd6017e`;
- a final docs pass (33 ids).

**Every agent's report is a claim.** The checks below separate what the
orchestrator re-ran from what only an agent ran.

## Re-run or re-derived by the orchestrator

- **K1-1**, re-derived `[calc]`:
  - release: 104 444 ns/V against the interpolated 372 ns/V limit = 280.6×;
  - press: 5 311 ns/V = 14.3×;
  - 87.6 µs of the release inside the band, 35 % of 250 µs scans.

  The slice's numbers stand. TI's "no input signal transition rate requirements" was read on `SN74HCS165-ti-scls828a.pdf` p.15 `[run: pdftotext]`.
- **K1-14**: Nexperia's Table 2 "Pin description" is on p.4 `[run: pdftotext -f 4]`.
- **K2-1 / K5-1**: the cable directions were read on the FFSD print, sheet 1: the `-RN2` notch and the key on each socket.
  - **The orchestrator had it wrong.** The model's comment and four documents said both cables leave downward.
  - K2 and K5 found this independently: agreement between cold slices.
- **K3-1**: after the re-layout, 0 of 43 vias are on or in an SMD pad `[run: pcbnew HitTest and polygon distance]`.
- **K3-4**: the Samtec SHF print gives the tail (0.41 square) and **no PCB hole**; the 0.70 drill is derived, in `hardware/lib/README.md`.
- **K3-6**: 684 segments became 243, with 0 collinear joints left `[run]`.
  - **4 acute GND junctions remain** (75°, 50°, 32°, 55°) `[run]`, so it is recorded as partly fixed, not fixed.
  - The staircases were a float-rounding bug in `commit()`, not a missing pass; the new post-pass then merged 0 joints, which is what showed that.
- **K3-8**: the decoupler is 2.25 mm centre to centre from U-KEYS pins 15 and 16 `[run]`.
- **K5-5**: MSO4-M2's 3.0 mm minimum from hole centre to edge, its 3.18 mm hole, its 3.16 mm shank and its lengths of 2 or 3 were read by the orchestrator on the banked PEM MPF page 5 `[run: pdftotext -f 5]`. The research agent's figures match. The new rule prints 3.61 mm.
- **K5-6**: neither stocked length lands in the window (0.8 and 1.8 mm against 2.0–2.4) `[calc]`, now printed as a drc NOTE. The finding was right that "buy 2.2" was a point, not a window.
- **K8-1**: the new `drc.echo` "key board to main board gap" prints **17.4**, which is K8's own corrected figure.
  - **Verifying the finding found more than it said.** Against "main board parts room under the key boards", a 2.54 mm IDC stack fits nominally and fails only at its worst case. The ADR's "fits nowhere" was also wrong, and is corrected with a dated note.
- **K8-6**: the FFSD print's `.120` thickness and its `positions × .050 + .165` length were read before `body.yaml` was re-cited to it.
- **Gates**: all were re-run on the final tree (`STATUS.md` header). `kicad.py check` runs `pcb.py check` with the checks agent's stricter checks, so the real board passes them rather than only a scratch copy.

## Only an agent ran, and how it can be trusted

- **K7-*, K3-2, K3-10** (the checks agent):
  - Each new check was confirmed by the agent to fire on a deliberately broken scratch copy. The breakages are listed in `STATUS.md`.
  - The orchestrator did not repeat those breakages. It did run every check on the real board: 35 errors before the re-layout, 0 after.
  - `setup-env.sh`'s download loop passed `bash -n` but was never run end to end, and `STATUS.md` says so.
- **The docs passes**: their gates passed when re-run by the orchestrator. It spot-checked K6-8 (`tooling.md` now lists the four fields), K8-13 (the three edges) and K8-1, and completed K8-1 itself.

## Where a slice or an agent was wrong

- **K4-7 rejected.** The "two different 2s" are the same two: SW1-n's two spares are the two reserved spare-switch positions. Dropping one would read 20 against 21 placed, which `check-netlist.py` reports, so it would not pass silently.
- **K1-5**: the page's "11 of 31 reload points" did not reproduce. By the docs agent's count, 3 pass with all keys released, 2 with all pressed, and 1 for every key state. The claim was removed rather than replaced with another count.
- **K8-1 as filed** (above): the finding's fix, "check whether fits nowhere still holds", was the right instruction. The claim does not hold as stated.
- **The fixing round introduced four clashes and caught them.**
  - The corrections for K5-10 and K5-3 caused them: the board's real end moved the mouth lid screw, and the longer service ribbon reached a gap lid screw. The same round's change to the standoff finder put two main-board standoffs through a thumb plate's edge.
  - `clash.txt` found all four. Each is fixed, and each now has a DRC rule, so it cannot come back silently.
- **An orchestrator error, recorded as a trap.** A script opened `key-chain-loom/bom.csv` for writing before reading its line endings, and truncated it. The file was restored from git before anything was committed. Read, then open for writing.

## Not checked

- The acute-junction wedges' fill (K3-6): whether the pour enters each wedge was not measured.
- Samsung's per-part datasheet for C53134 (K4-3): not fetchable; the catalogue's neighbouring part is banked.
