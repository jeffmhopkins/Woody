# N8 — the author's own assertions

**Slice:** N8, cold. **Claim type:** the assertions made in the commit messages
of the 2026-09-22/23 netlist conversion, verified independently of those
messages.

**Measured against** `d1f0cb7`. The working tree is at `5c39a4e`, which adds
only `docs/review/2026-09-26-netlist-audit/README.md`
`[test] git diff --stat d1f0cb7..HEAD → 1 file changed, docs/review/… only`, so
every corpus statement below is true of `d1f0cb7`.
`tools/` treated as frozen: every experiment ran in `/tmp/n8-clone`
(`git clone /home/user/Woody`), never in the shared tree.

**Cold:** I read nothing under `docs/review/`. Two `git grep` runs in §F and
§N8-10 incidentally printed matching lines from `docs/review/` paths; I have
not used any of that text as evidence and no claim below rests on it. I read
git history throughout, which the brief allows.

**Baseline, reproduced before anything else**
`[test] cd /tmp/n8-clone && python3 tools/check-netlist.py --strict`

```
netlist: 22 circuit(s), 197 components, 254 nets, 55 master net(s) | 0 problem(s)
         | 0 drawing page(s) still without a netlist | 0 master endpoint(s) awaiting one
instances: 102 row(s) placed exactly to BOM qty, 4 counted by section, 7 short:
  C-BUCK-IN 1/2, C-DECOUPLE 1/19, C-DECOUPLE-CARRIER 5/8, HDR-DEV 1/6,
  J-CHAIN 1/8, R-OPAMP-IN 6/7, U-BREATH 1/2
```

`[test] python3 tools/merge-bom.py --check → checked 155 rows from 26 fragments | 0 problems`
`[test] python3 tools/audit-notes.py --regrown → 0 row(s) still narrating rather than specifying`

Every headline number in the closing commit `5f051c0` reproduces exactly.

---

## Verdict in one paragraph

**The asserted defects are real.** I reconstructed the before state of every
one I could reach and found no fabricated finding — the aggregate rows, the
missing BOM rows, the bundled master nets, the two-nets-that-were-one-node, the
three boundary disagreements and the pull-up with no rail were all genuinely
there, and the fixes mostly reached the citing pages *in the same commit*. The
self-correction in `a4eaa23` is exactly right, to the digit. **Every injection
I reproduced fired, and fired for the reason claimed** (§C).

What does not hold up is the *coverage* the wave then claimed for itself.
Fifteen findings follow. The three that matter are: the tool checks only
bracketed labels and says nothing about the values it skips, so the three BOM
rows `8d66e2d` created because "a netlist cannot be written without noticing"
have drawn values that nothing compares (**N8-1**); an eighth aggregate row of
exactly the shape the wave says it forced apart seven times survives at
`C-BULK-RAIL`, on the page whose drawing defect started the exercise, because
the value test is a substring match (**N8-2**); and the global instance count is
structurally blind to any row placed **zero** times — 42 of 155 rows, twelve of
them named on schematic pages and absent from `unplaced.csv` (**N8-3**).

---

## A. Assertions checked and found correct

| # | Assertion (commit) | Verdict | Evidence |
|---|---|---|---|
| A1 | `R-BREATH-SUM` `10k / 40.2k 1%` qty 2 and `R-BREATH-OFF` `21.0k / 95.3k 1%` qty 2 were one `part` field each, split into four rows (`82f1464`) | **real** | `[git 82f1464^:hardware/bom.csv]` shows exactly those two rows; `[repo hardware/bom.csv]` now has `R-BREATH-IN 10k`, `R-BREATH-FB 40.2k`, `R-BREATH-OFF 21.0k`, `R-BREATH-OFFNEG 95.3k`, qty 1 each. Quantity conserved 2+2 → 4×1. |
| A2 | The label regex `[A-Z][A-Z0-9][A-Z0-9-]*` matched "2 labels of 10" on the pilot page (`82f1464`) | **real, exactly** | `[test]` both regexes run over `drawing_lines()` of `breath-output-stage.md`: old → 2 (`[POT-GAIN 50k]`, `[POT-OFFSET 10k]`), current → 10. The stated numbers and the stated two survivors are both right. |
| A3 | `C-FILT-BREATH` `15nF … + 1.5nF … (cm x2)` qty 3 → `C-DIFF-BREATH` 1 + `C-CM-BREATH` 2 (`b594f24`) | **real** | `[repo hardware/bom.csv]` both rows present, qty 1 and 2; the ±1 % now sits on `C-CM-BREATH` only. |
| A4 | `R-REG-SET` `150R / 475R 0.1%` qty 2 and `C-REG-ADJ` `10uF / 1uF` qty 2 split (`3aa4cd0`) | **real** | `[git 3aa4cd0^:hardware/bom.csv]` shows both aggregates; `[repo]` now `R-REG-SET-HI/-LO`, `C-REG-ADJ`, `C-REG-OUT`, qty 1 each. |
| A5 | `3aa4cd0` claimed "0 problems, 0 awaiting" and there were 3 and 68; `a4eaa23`'s corrected numbers are 3 circuits / 42 components / 41 nets / 34 master nets / 0 problems / 11 pending / 68 awaiting | **both exactly right** | `[test]` clone at `3aa4cd0`: 3 problems (`DIG_GND`, `PWR_GND`, `AGND_MOD` each "names module/power-entry as out, but that circuit declares dir 'ref'"), 68 awaiting. Clone at `a4eaa23`: `3 circuit(s), 42 components, 41 nets, 34 master net(s) | 0 problem(s) | 11 … | 68 …`. The confession and the correction both reproduce to the digit. |
| A6 | `R-MODGAIN` `10k / 30k 1%` qty 8 was an aggregate; every citation moved in the same commit (`8646e75`) | **real, and complete** | `[git 8646e75^]` `git grep R-MODGAIN` over the §6 corpus gives 7 sites (ADR 0006 ×2, `bom.csv`, `breath-output-stage.md`, `breath-output-stage/circuit.yaml`, `mod-channels/bom.csv`, `mod-channels/circuit.yaml`, `mod-channels.md`). `[git 8646e75]` all 7 carry `-IN`/`-FB`; no bare `R-MODGAIN` survives outside `ROADMAP.md`'s narration. |
| A7 | `R-ADCDIV` `10k / 15k 1%` was an aggregate whose two refdes `carrier.md` §2 had drawn all along with no BOM row (`f209624`) | **real** | `[git f209624^:hardware/carrier/carrier.md:120]` `[R-ADCDIV-U 10k]──┬──[R-ADCDIV-L 15k]`; `git grep R-ADCDIV-U` at that revision hits that line only — no BOM row. `[repo]` both rows exist; `breath-adc.md`'s four sites, `carrier.md`'s two and the `circuit.yaml` edge all moved in the same commit. (The `figures.yaml` edit is **N8-10**.) |
| A8 | `LK-CLR` was named as a live feature by four files and had no BOM row (`0e50417`) | **real** | `[git 0e50417^]` `git grep LK-CLR` over the corpus: `firmware/README.md:67`, `dac8568.md:21` and `:44` (drawing), `link-supervision.md:27`, `mod-channels.md:162` — and no `bom.csv` row. `[repo hardware/bom.csv:83]` the row now exists. |
| A9 | `R1 20k`, `R2 10k` and the `2 × 10 k` divider were in the drawing and the cost table of `breath-response-shaper.md` and in no BOM row (`8d66e2d`) | **real** | `[git 8d66e2d^:hardware/module/breath-response-shaper/bom.csv]` holds only `POT-RESP`, `R-RESP`, `D-RESP`, `U-RESP`. `[repo]` `R-RESP-IN 20k`, `R-RESP-FB 10k`, `R-RESP-DIV 10k ×2` added. (The drawing half of this fix is **N8-1**.) |
| A10 | `SPI_DAC` was one master net carrying `SCLK_DAC`/`DIN`/`SYNC`; `DAC_CH2_5` was one net carrying four channels; `MOD_JACKS` one net for four jacks (`0e50417`, `8646e75`) | **real, and cleanly retired** | `[repo hardware/nets.yaml]` three nets at 459/467/474, four at 512–533. `git grep` over the corpus finds the three retired names only in `nets.yaml` narration and `ROADMAP.md`. No page still cites a bundle. |
| A11 | The carrier's "+12 V strip feed" and "+12 V analog" are the same node as the umbilical's; two invented master nets removed (`cfaa6a7`) | **real, and the table followed** | `[repo hardware/carrier/power-entry-instrument/power-entry-instrument.md:22-24]` the two rows now read "**The same net as the row above**" and "**Also the same net**". The fix reached the reader-facing table in the same commit. |
| A12 | `key-register.md`'s only bracketed label was split over three lines, so the page never appeared in the pending list (`cfaa6a7`) | **real** | `[git cfaa6a7 -- key-register.md]` the diff replaces `[C-DECOUPLE-165` / `100 nF, AT the` / `package]` with a one-line label. `[test]` clone at `cfaa6a7^`: pending list is 5 pages and `key-register.md` is not among them. (The stated count is **N8-14**.) |
| A13 | The cable-side `CS` pull-up has no rail on the module board, and the `R-SPI-PULL` cell contradicted itself in a `.csv` (`7721c75`) | **real, and the sharpest finding of the wave** | `[git 7721c75^:hardware/interfaces/spi-link/bom.csv]` the cell opens *"Cable side: CS to +5V"* and 40 words later says *"CABLE-SIDE CS PULLS TO 3V3, NOT +5V"* — a refutation in place inside a `.csv`. `[repo hardware/nets.yaml]` the only 3V3 nets are `V3V3_CHAIN` (carrier→clusters) and `DEV_3V3` ("the only 3V3 on the instrument"). `[repo hardware/interfaces/spi-link/netlist.yaml:24-33]` `J-UMBILICAL` has 8 pins and none is 3V3. The rail genuinely does not exist there. (The quote in the fix is **N8-8**.) |
| A14 | `ON` was declared as crossing into `module/panel` while `panel.md` claims only the hole (`c3e61fd`) | **real** | `[git c3e61fd^:umbilical-load-switch.md:19]` `| ON | in | module/panel |`; `[git c3e61fd^:panel.md]` has no `ON` row. `[repo umbilical-load-switch.md:24]` now `| ON | — | … **Not a crossing.**`, and `SW-POWER` is this circuit's own fragment row `[repo hardware/module/umbilical-load-switch/bom.csv:2]`. |
| A15 | `foreign:` was an unconditional skip (`c3e61fd`) | **real, verbatim** | `[git c3e61fd^:tools/check-netlist.py:405-407]` the loop body opens `if ref in foreign: continue` before any comparison. |
| A16 | `module/link-supervision` is not a receiver of `UMBILICAL_POS12` because every row on its page reads "Not fitted" (`5f051c0`) | **real** | `[repo hardware/module/link-supervision/link-supervision.md:27-31]` all five Interfaces rows open `**Not fitted.**`. |
| A17 | The `PWR_GND` pour does not include `carrier/breath-adc` and `carrier/breath-excitation-reference` (`4e8933e`) | **real** | `[git 4e8933e^:power-entry-instrument.md:25]` lists all four peers; `[repo :25]` lists three and says why. The reasoning is right: both pages return on `AGND_INST`. (What the fix left behind is **N8-4**.) |
| A18 | `CLR` has no driver and `R-CLR-PU` holds it; `OE_MOD` is retired (`a02b628`) | **real** | `[repo hardware/nets.yaml CLR]` `undriven: true` + `pull:`, receivers `[module/dac8568]`; `[repo digital-and-supervision.md:72]` "NOT HERE ANY MORE: the 74HC123 frame watchdog and the LM311 presence [comparator]". |
| A19 | `[1k R-OPAMP-IN]` → `[R-OPAMP-IN 1k]` is "same width, so no column moves" (`76e79b1`) | **real** | `[test] git show 76e79b1 -- pitch-stage.md \| cat -A` — the two lines are byte-identical apart from the swap; both labels are 15 characters. |

---

## B. Findings

### N8-1 — `R-RESP-IN` / `R-RESP-FB` / `R-RESP-DIV` and `R_G`: an unbracketed value in a drawing is checked by nothing, and nothing says so

**Severity: high** (it is the exact defect class the whole exercise exists to close).

**Claim.** `CLAUDE.md` and `hardware/README.md` state that the checker proves
"**every `[REFDES value]` label in a drawing against the netlist that owns the
part**", and `76e79b1` states the principle that "A LABEL THE PARSER CANNOT READ
IS NOW REPORTED … because silence reads like agreement" — but a drawing that
states a value **without brackets** is not parsed, not reported and not
compared, and the three rows `8d66e2d` created are drawn exactly that way.

**Evidence.**
`[repo hardware/module/breath-response-shaper/breath-response-shaper.md:59,62]`
the drawing reads `R1 20k` and `R2 10k` as bare text inside the fenced block;
the divider legs are drawn `[10k]` with no refdes.
`[repo hardware/module/breath-response-shaper/netlist.yaml:31-38]` declares
`drawn_as: R1` and `drawn_as: R2` — aliases for labels that do not exist in
bracket form, so they are never exercised.
`[test]` in `/tmp/n8-clone`, `sed` line 59 `R1 20k`→`R1 99k` and line 62
`R2 10k`→`R2 77k`, then `python3 tools/check-netlist.py --strict`:

```
netlist: 22 circuit(s), 197 components, 254 nets, 55 master net(s) | 0 problem(s) | …
EXIT=0
```

`[test]` a scan of every drawing line on every netlisted page for
`<known refdes or drawn_as> <value>` outside brackets finds five such sites,
all currently unchecked: `breath-response-shaper.md:59` `R1 20k`, `:62`
`R2 10k`, `:70` `POT-RESP 50k`, `breath-receive-stage.md:92` `R_G 42.2k`,
`display-and-service-uart.md:74` `HDR-SERVICE 2×3`.
I checked all five against `hardware/bom.csv` by hand: all five currently
agree, so **the hole is latent, not a live misbuild** — `R_G 42.2k` matches
`R-GAIN-INAMP 42.2k 0.1%`, `POT-RESP 50k` matches its row, `R1`/`R2` match the
rows the same wave created.
`[repo breath-response-shaper.md:136]` the cost table still spends "R1 20 k,
R2 10 k, divider 2 × 10 k" and does not name the three new refdes, so the
reader of the page has no route from the drawing to the rows.

**What would have to be true for this to be wrong.** That `CLAUDE.md`'s
sentence is read as scoping the guarantee to bracketed labels only *and* that a
reader is expected to know an unbracketed value is outside the guarantee. Both
documents state the coverage claim with no such qualification, and `76e79b1`
went out of its way to add a check for the weaker case (a bracket the parser
cannot read), which is evidence the author intended no such escape.

**Smallest fix.** Bracket them: `[R-RESP-IN 20k]`, `[R-RESP-FB 10k]`,
`[R-RESP-DIV 10k]` ×2, `[R_G 42.2k]`, `[POT-RESP 50k]` — all are same-width or
wider-only-to-the-right of the current text on those lines, and the drawn_as
aliases already exist for `R1`/`R2`. Then have the checker print, once per run,
the count of drawing lines that contain a known refdes and a digit outside any
bracket, so the residue is a number rather than a silence.

---

### N8-2 — `C-BULK-RAIL`: the eighth aggregate row, on the page the exercise started from, survived because the value test is a substring match

**Severity: high** (it is an unorderable line item, and it is the row behind the
original "stuffing list under-fits +12 V by half" defect).

**Claim.** `ROADMAP.md:267-269` and six commit messages state that an aggregate
row — "one `part` field holding two values, so no instance could state a value
that matched it" — is a defect the netlist rollout forced apart seven times.
`C-BULK-RAIL` is the eighth instance of exactly that shape, is still aggregate
at `d1f0cb7`, and passes `check-netlist.py` clean.

**Evidence.**
`[repo hardware/bom.csv:69]`
`C-BULK-RAIL,module,"100uF (+12V) / 47uF (-12V, +5V) 25V electrolytic",…,4,candidate`
— two values in one `part` field at qty 4. Ordering it requires 1 × 100 µF and
3 × 47 µF; the row as written is not a line item.
`[repo hardware/module/power-entry/netlist.yaml:81-101]` the four instances
state `value: "100uF"` (C1) and `value: "47uF"` (C2, C3, C4).
`[repo tools/check-netlist.py:375]` the row check is
`if "value" in c and norm(c["value"]) not in norm(bom[row_ref]["part"])` — a
**substring** test, so `100uf` and `47uf` are both inside
`100uf(+12v)/47uf(-12v,+5v)25velectrolytic` and both pass. The stated criterion
("no instance could state a value that matched it") is therefore not what
selected the seven; what selected them is whether the checker complained.
**And the row's live justification rests on a deleted part.** The same cell
reads *"The +12V branch carries the LM317's divider, the DAC and the
comparator, about 22mA against -12V's 10mA - so at 47uF each it collapses 2.2x
faster"* `[repo hardware/bom.csv:69]`, while
`[repo hardware/module/digital-and-supervision/digital-and-supervision.md:72]`
records the LM311 presence comparator as deleted. `[calc]` the 2.2× is
22 mA / 10 mA, so one of the two terms of the ratio that chooses 100 µF over
47 µF is a load list containing a part that is not fitted. `5a6cf6c`'s own
message flagged this ("Also noted for whoever owns that row … Not fixed here")
and it is still live four days later.

**What would have to be true for this to be wrong.** That a *through-hole
electrolytic bought as one reel of two capacitances* is a real line item, or
that the comparator's share of the 22 mA is zero. The second is testable and I
could not test it — no document gives the LM311's supply current — which is
itself the point: the number cannot be reproduced.

**Smallest fix.** Split it the way the other seven went:
`C-BULK-P12` 100 µF qty 1 and `C-BULK-RAIL` 47 µF qty 3, in
`hardware/module/power-entry/bom.csv`, re-run `merge-bom.py`, update the four
`of:`/`value:` pairs in that netlist and the `[C1 100uF]`…`[C4 47uF]` labels.
Recompute the +12 V load without the comparator and state the new ratio, or
mark the 2.2× `TBD` with the measurement that decides it.

---

### N8-3 — the global instance count cannot see a row placed zero times, and `J-CV` "from unplaced to 6/6" records a transition nothing measured

**Severity: medium-high.**

**Claim.** `8646e75` introduces the global instance count as "the thing a
per-circuit file structurally cannot check", and `ef8c42f` states the principle
"NAMED, NOT COUNTED … a number is one they have to trust". The check iterates
only over rows some netlist mentions, so a BOM row placed **zero** times is
absent from both the exact count and the short list — 42 of 155 rows, and the
printed line does not say so.

**Evidence.**
`[repo tools/check-netlist.py:221]` `for row, n in sorted(used.items())` —
`used` is a `Counter` built only from components found in netlists, so a row
nobody netlists never enters the loop.
`[test]` reproducing `used` in the clone against `hardware/bom.csv`:
155 rows, **113** placed at least once, **42** placed zero times. Of those 42,
30 are declared in `hardware/unplaced.csv`; the remaining **12** are in neither
the netlists nor `unplaced.csv`: `C-BULK-DISP`, `LK-SER`, `MECH-COAT`, `PANEL`,
`PCB-CARRIER`, `PCB-CLUSTER`, `PLATE-THUMB`, `PLATE-TOP`, `R-SER-TERM`,
`R-TRIM-RANGE`, `SW-THUMB`, `WIRE-LOOM`.
Eight of the twelve are mechanical and legitimately carry no net. **Four are
electrical and are each named on a schematic page**
`[test] grep -rl` → `C-BULK-DISP` on `power-entry-instrument.md`,
`R-TRIM-RANGE` on `pitch-stage.md`, `LK-SER` and `R-SER-TERM` on
`key-chain-loom.md`. `CLAUDE.md` says `unplaced.csv` "holds the rows no
schematic page names", so these four are in a third category with no home and
no count.
**And the closing commit's own example is in that blind spot.** `5f051c0` says
"`J-CV` goes from unplaced to 6/6".
`[test] git show 5f051c0^:hardware/unplaced.csv | grep -c J-CV → 0` — it was not
in `unplaced.csv`. `[test]` clone at `5f051c0^`,
`python3 tools/check-netlist.py` → `instances: 97 … 8 short: C-BUCK-IN 1/2,
C-DECOUPLE 1/19, C-DECOUPLE-CARRIER 5/8, HDR-DEV 1/6, J-CHAIN 1/8,
R-KEY-PU 21/24, R-OPAMP-IN 6/7, U-BREATH 1/2` — `J-CV` is not there either. It
was placed 0/6 and invisible, which is neither state the sentence names.

**What would have to be wrong.** That "unplaced" in `5f051c0` means "not placed
in a netlist" rather than "in `unplaced.csv`" — a reading the sentence permits,
but which still leaves the 0-times class unreported by design. The 12
unaccounted rows do not depend on that reading.

**Smallest fix.** One line in `check_global`: iterate over `bom` rather than
`used`, and print a third bucket — `N row(s) placed nowhere and not in
unplaced.csv`, named. Then either netlist `C-BULK-DISP`, `LK-SER`,
`R-SER-TERM`, `R-TRIM-RANGE` or move them to `unplaced.csv` with what decides
them.

---

### N8-4 — `AGND_INST`: the `PWR_GND` fix removed two peers and left the boundary declared from one side only

**Severity: medium.**

**Claim.** `4e8933e` correctly removed `carrier/breath-adc` and
`carrier/breath-excitation-reference` from `power-entry-instrument.md`'s
`PWR_GND` row because both return on `AGND_INST` — and then added no
`AGND_INST` row, so the page `hardware/nets.yaml` names as that net's **origin**
now carries no Interfaces row for it, while both peers still name the page. That
is the same "two halves of one boundary disagreeing" shape the commit was
fixing.

**Evidence.**
`[repo hardware/nets.yaml AGND_INST]` `origin: carrier/power-entry-instrument`,
`reference: [carrier/breath-adc, carrier/breath-excitation-reference,
interfaces/breath-sense-link]`.
`[repo hardware/carrier/power-entry-instrument/power-entry-instrument.md]`
`grep -n AGND` returns two hits: line 25 (the `PWR_GND` row, which only says
the two pages are *no longer* listed) and line 70 (`MECH-GNDBOND` … never to
`AGND`). **There is no `AGND_INST` row and no row naming `breath-adc` or
`breath-excitation-reference` at all.**
`[repo hardware/carrier/breath-adc/breath-adc.md:29]` still reads
`| AGND_INST | ref | carrier/power-entry-instrument | … |`.
`hardware/README.md:53-56` requires "every net that crosses that circuit's
boundary, one row each … two pages disagreeing about a net is a short."
**The dependency edges did not follow either.** `[test]` a header-aware parse of
every `## Interfaces` Peer column against every `circuit.yaml`'s `circuit:`
edges gives exactly one edge-without-a-peer in the corpus:
`carrier/power-entry-instrument` still declares `- circuit:carrier/breath-adc`
`[repo hardware/carrier/power-entry-instrument/circuit.yaml:29]` although its
Peer column no longer names it, and `breath-adc/circuit.yaml:22` still declares
the reciprocal. `check-staleness.py` reports `0 deps`, so nothing sees it.

**What would have to be wrong.** That `AGND_INST` does not cross
`power-entry-instrument`'s boundary. It cannot be that: the master names the
circuit as its origin and three other circuits as references, and the page's own
`PWR_GND` note says `AGND_INST` "reaches this pour on the **single tie**".

**Smallest fix.** Add one row to that table —
`| AGND_INST | ref | carrier/breath-adc, carrier/breath-excitation-reference, interfaces/breath-sense-link | dig-gnd-topology | Originates here; the single tie to the pour is this circuit's |` —
which also restores the `circuit:` edges the README's rule requires.

---

### N8-5 — `carrier/carrier`: a circuit id with no `circuit.yaml`, named as a Peer, where the README's own mechanical rule cannot be applied

**Severity: medium.**

**Claim.** `f209624` put the carrier board's netlist at `hardware/carrier/`
"not in a circuit directory, because `carrier.md` is the BOARD page", and gave
it the circuit id `carrier/carrier`. That id is now used in `hardware/nets.yaml`
and named in three Interfaces Peer columns — but the directory has no
`circuit.yaml`, so `hardware/README.md`'s mechanical `circuit:`-edge rule
(which the same wave edited) cannot be satisfied at either end, and a reader
applying it gets a wrong answer with no way to tell.

**Evidence.**
`[test]` 23 directories under `hardware/` carry a `circuit.yaml`; the 22
`netlist.yaml` files declare 22 circuit ids, and exactly one — `carrier/carrier`
— is backed by no `circuit.yaml` directory. `[repo]` `ls hardware/carrier/*.yaml`
→ `netlist.yaml` only.
`[repo hardware/README.md:110-114]`: "ONE `circuit:` edge per distinct
`board/circuit` id in the **Peer** column of this circuit's `## Interfaces`
table, AND every such edge is declared from **both** ends. A peer that is not a
circuit in this tree … creates no edge."
`[test]` the same header-aware parse finds `carrier/carrier` in the Peer column
of three pages — `power-entry-instrument.md` (added by this wave, `[test] git
log -S 'carrier/carrier' --oneline -- power-entry-instrument.md → d1f0cb7`),
`breath-sense-link.md` and `spi-link.md` — and **no `circuit.yaml` anywhere
declares an edge to it.**

**What would have to be wrong.** That `carrier/carrier` is "not a circuit in
this tree", in which case the Peer column should name it by reference designator
and the README should say so. But `nets.yaml` names it as driver or receiver of
nets and `check-netlist.py` treats it as a circuit, so the corpus uses it both
ways at once.

**Smallest fix.** One sentence in `hardware/README.md`'s `circuit.yaml` section:
`carrier/carrier` is a board page that carries nets and has a `netlist.yaml`
but no `circuit.yaml`, so it creates no `circuit:` edge — or give it a
`circuit.yaml` and let the rule stand as written.

---

### N8-6 — `HDR-DEV`: the netlist note written to explain `1/6` contradicts the row it is checked against and both statements on its own page

**Severity: medium.**

**Claim.** `f209624` added a note to `hardware/carrier/netlist.yaml` explaining
the shortfall the instance count prints. The explanation is a fourth,
incompatible account of what `qty 6` buys.

**Evidence.** Four live statements:

| where | what it says |
|---|---|
| `[repo hardware/bom.csv HDR-DEV]` desc | "Sockets for **both** dev boards on the carrier", qty **6** |
| same row, notes | "Cut to length: **2 strips for the ESP32-S3-Matrix, 2 for the T-Display-S3 AMOLED, 2 spare**" |
| `[repo hardware/carrier/carrier.md:29]` | "`HDR-DEV` in the BOM budgets header strips for **both**" — then argues the display board "reaches this board through a loom, not a socket" |
| `[repo hardware/carrier/carrier.md:293]` | "`2 × 10-way machined socket` … **Qty is one board's worth, not two** — the display board is 360 mm away" |
| `[repo hardware/carrier/netlist.yaml:69]` (**new, 2026-09-23**) | "**Six strips for one dev board**, which is why the instance count reads HDR-DEV 1/6: one mating part, six pieces bought" |

`[calc]` if the socket is `2 × 10-way` (carrier.md:293) and one board's worth is
needed (carrier.md:293), the quantity is 2 strips, not 6; the BOM row's own
breakdown reaches 6 only by buying for **both** boards. "Six strips for one dev
board" reconciles with neither. The instance line has printed `HDR-DEV 1/6` on
every run since 2026-09-23 and no commit message mentions it.
Two further disagreements on the same row, unchecked because neither is a
drawing label: the part is `2.54mm female header strip - machined or dual-wipe`
in `bom.csv` and `2 × 10-way machined socket` on `carrier.md:293`.

**What would have to be wrong.** That the ESP32-S3-Matrix needs six header
strips. Nothing in the corpus says it does, and `carrier.md:293`'s own Value
column says `2 × 10-way`.

**Smallest fix.** Decide the quantity once on `carrier.md` (one board's worth =
2, plus spares if wanted), fix the `bom.csv` row's notes to match, and replace
the netlist note with a citation to that decision instead of an arithmetic of
its own.

---

### N8-7 — `hardware/README.md`: the paragraph a reader hits first says nothing checks a drawing, directly above the paragraph saying a tool does

**Severity: medium.** This is the shape this repository has a commit subject
named after (`b4b2f47`, "the correction was added BESIDE the false statement,
not instead of it") and both halves were written by this wave.

**Claim.** The block quote the conversion added to `hardware/README.md` states,
in the present tense, that no tool can read a drawing and nothing checks a
drawn value against its BOM row — and then states two paragraphs later that
`tools/check-netlist.py` does exactly that.

**Evidence.** `[repo hardware/README.md:27-38]`, verbatim and contiguous:

> **An ASCII drawing is a picture.** No tool in this repository can read one,
> so nothing checks that a value in a drawing matches the BOM row for the same
> refdes …
>
> **`tools/check-netlist.py` checks the drawing against the netlist**, and the
> netlist against `bom.csv` and against `nets.yaml`.

`[test] git diff 3e88bf2^ d1f0cb7 -- hardware/README.md` — the entire block quote
is an addition of this wave, so the false sentence is not a survivor from before
the tool existed; it was authored alongside its own refutation.
The same block's third paragraph — "Where a drawing and a row disagree and **no
netlist covers them**, `bom.csv` wins" — describes an empty set at `d1f0cb7`
(0 pending pages), and the heading "Where a `netlist.yaml` exists, that is"
implies a partial rollout that `5f051c0` closed.
Two paragraphs later, `[repo hardware/README.md:62-64]`: "this table is for the
pages that have no netlist yet" — also an empty set; and of the three
shorthands it lists, only `C-TIMER` and `C-GATE` have a `drawn_as:` anywhere
`[test] grep -rn 'drawn_as: *\(C-TIMER\|C-GATE\|J-UMB\)'` → two hits, no
`J-UMB`.

**What would have to be wrong.** That "No tool in this repository can read one"
is meant historically. It is written in the present tense with no date, in the
first sentence a reader of `hardware/` meets, and the 2026-09-22 clause after
it is dated while this one is not.

**Smallest fix.** Change the first paragraph to the past tense and date it —
"Until 2026-09-22 no tool here could read one, and nothing checked …" — and
drop the "where a netlist exists" / "no netlist covers them" / "pages that have
no netlist yet" hedges, which now describe nothing.

---

### N8-8 — `R-SPI-PULL`: the fix's own explanation quotes the row in the wording the same commit deleted

**Severity: medium.** A recorded shape, in an authoritative file.

**Claim.** `7721c75` removed the self-refutation from the `R-SPI-PULL` notes
cell (correctly, per `CLAUDE.md` 2b) and, in the same commit, wrote a
`netlist.yaml` comment that quotes the deleted wording as the row's current
text.

**Evidence.**
`[git 7721c75:hardware/module/digital-and-supervision/netlist.yaml:150]`
`# R-SPI-PULL's own row says "CABLE-SIDE CS PULLS TO 3V3, NOT +5V", with the`
`[git 7721c75:hardware/interfaces/spi-link/bom.csv]` the row as committed in the
same commit reads `CABLE-SIDE CS PULLS TO 3V3: pulled to 5V it drives 430uA …`
— the `, NOT +5V` is gone.
`[repo]` both are unchanged at `d1f0cb7`: the quotation marks still claim text
that no longer exists in the file being quoted.
A second, softer instance: `[repo digital-and-supervision.md]`'s "Still open"
bullet says "`R-SPI-PULL`'s row says it pulls to **3V3, not +5 V**" — a
paraphrase rather than a quotation, and the row does still argue against 5 V in
its next clause, so I do not file that one.

**What would have to be wrong.** That the netlist comment is quoting the
pre-`7721c75` row deliberately as history. It is written in the present tense
("says") and in a file `CLAUDE.md` declares authoritative.

**Smallest fix.** Drop the four words: `# R-SPI-PULL's own row says the
cable-side CS pull goes to 3V3, with the reason: …`.

---

### N8-9 — "runs from the commit gate": there is no gate that blocks, and one netlist problem is reported as five

**Severity: medium-low.**

**Claim.** `ROADMAP.md:229-231` — "`tools/check-netlist.py --strict` runs from
the commit gate, so a new drawing page with no netlist is now a **failure**
rather than an entry on a list" — and `CLAUDE.md`'s hardware conventions —
"`tools/check-netlist.py --strict` runs from the commit gate and proves all of
it" — assert an enforcement the same `CLAUDE.md` documents as absent.

**Evidence.**
`[repo .claude/settings.json]` the only hook is one `PreToolUse` entry whose
command runs `check-staleness.py` and emits `systemMessage` and
`hookSpecificOutput.additionalContext` via `jq -n`. There is no
`permissionDecision` anywhere in the file, and no other hook.
`CLAUDE.md` §2 states this itself: *"it emits only `additionalContext`, never a
`permissionDecision`, so **a FAIL never blocks a commit**"*. So the two "commit
gate" sentences written by this wave assert exactly what §2 was written to
refute.
The plumbing below the gate does work:
`[repo tools/check-staleness.py:440-443]` runs `check-netlist.py --strict`, and
`[test]` injecting `[R-FB 40k]` in the clone makes `check-staleness.py` exit 1
and print `FAIL … 5 generated …`; `[test]` adding a new drawing page with no
netlist makes `check-netlist.py --strict` exit 1.
**A second, smaller defect in the same path:** that run had *one* netlist
problem and the gate reported **5**. `[repo tools/check-staleness.py:461-462]`
collects every non-`PASS` line of the tool's output, so
`check-netlist.py`'s four informational lines (`netlist:`, `not a circuit:`,
`per-board bundles…`, `instances:`) are counted as problems. A reader cannot
tell from the `FAIL` line how many netlist defects exist, in a repository whose
named failure is a count that has moved.

**What would have to be wrong.** That "commit gate" is a name for the
PreToolUse hook rather than a claim about blocking. Even on that reading, "is
now a failure rather than an entry on a list" is the claim at issue, and a
non-blocking advisory line *is* an entry on a list.

**Smallest fix.** Either say "runs before every Bash call and reports; it does
not block — see `CLAUDE.md` §2" in both places, or add a
`permissionDecision: "deny"` branch to the hook for a FAIL. And in
`check-staleness.py`, count only lines the sub-tool emits before its summary,
or have `check-netlist.py` print its problem count on stderr for the gate to
quote.

---

### N8-10 — `sensor-full-scale`: a dated escape record was edited to name two rows that did not exist on that date

**Severity: medium-low.**

**Claim.** `f209624` lists "figures.yaml's own count of rows" among the
citations it moved with the `R-ADCDIV` split. That text is not a count of BOM
rows in the repository — it is the record of what a **2026-09-21** grep found —
and editing it makes the record describe a state that never existed.

**Evidence.**
`[git f209624 -- config/figures.yaml]` the whole diff is one line:
`-      Plus three BOM rows: R-ADCDIV, U-BREATH and D-TVS-BREATH, each`
`+      Plus four BOM rows: R-ADCDIV-U, R-ADCDIV-L, U-BREATH and D-TVS-BREATH, each`
`[repo config/figures.yaml:61-75]` the enclosing block is `escape_note_3`, which
opens "THE EIGHTH AND NINTH SPELLINGS, **2026-09-21**, FOUND BY A PRE-MERGE WAVE"
and closes "it is what found all six".
`R-ADCDIV-U` and `R-ADCDIV-L` were created on 2026-09-23 by this very commit
`[test] git grep R-ADCDIV-U f209624^` → one hit, `carrier.md`'s drawing, no BOM
row — so the 2026-09-21 grep cannot have found them.
The sentence is also false in the present tense: `[test]` none of
`R-ADCDIV-U`, `R-ADCDIV-L`, `U-BREATH`, `D-TVS-BREATH` contains the string
`4.7` at `d1f0cb7`, so no row "spells it without the space before the V" any
more. The text is purely a record, and `CLAUDE.md` §6's principle — a record of
what was true when it was written must not be "corrected" — is what the edit
breaks.

**What would have to be wrong.** That `escape_note_3` is a live inventory
rather than a dated record. Its own first line is a date and a past-tense
finding, and its last clause counts what "it … found".

**Smallest fix.** Restore `R-ADCDIV` and `three`, and if the rename matters to a
future reader add a parenthesis: `R-ADCDIV (split into -U/-L on 2026-09-23)`.

---

### N8-11 — `ROADMAP.md` "Seven fixes to the label parser alone" enumerates eight, and omits the first one

**Severity: low.** A stated count that has moved under the sentence stating it —
one of the four shapes `CLAUDE.md` says to slice for.

**Claim and evidence.** `[repo ROADMAP.md:286-293]`:

> **And the checker kept failing open.** Seven fixes to the label parser alone
> … a refdes may be one character, may carry `_`, may carry `.`; a label
> written value-first or split across two lines is reported rather than
> skipped; `foreign:` was an unconditional skip; `10R`, `10 Ω` and `10 kΩ` are
> one value; `×2` and `#1` are counts, not magnitudes.

`[calc]` the clause enumerates 3 + 2 + 1 + 1 + 1 = **eight** fixes against a
stated seven. Three of the eight (`foreign:`, the unit folds, the count tokens)
are not label-parser fixes at all. And the list omits the **first and largest**
one: the `[A-Z][A-Z0-9][A-Z0-9-]*` regex that required the second character not
to be a hyphen, which `[test]` saw 2 labels of 10 on the pilot page and which
`tools/check-netlist.py:53-66` gives fourteen lines of its own docstring to.
Counting every distinct fix the commit messages assert, I get **eighteen**
across `82f1464`, `76e79b1`, `c3e61fd`, `cfaa6a7`, `8d66e2d` and `4e8933e`.

**What would have to be wrong.** That "the label parser" excludes the regex
that parses the label. It does not.

**Smallest fix.** Delete the number, as this repository does elsewhere: "**The
checker kept failing open**, and every fix came from a correct label reported
wrong or an injected defect not reported at all — the list is in
`tools/check-netlist.py`'s docstring and comments." Then add the
second-character-hyphen case, which is the one worth a reader's time.

---

### N8-12 — the instance line names seven short rows; the reader-facing list explains five, and its stated reason is wrong for one of those

**Severity: low.**

**Claim and evidence.** `ef8c42f` introduced the named short list with "Four of
the five have a written reason and the fifth is a question this rollout
raised." The list is now seven `[test]` — `C-BUCK-IN 1/2`, `C-DECOUPLE 1/19`,
`C-DECOUPLE-CARRIER 5/8`, `HDR-DEV 1/6`, `J-CHAIN 1/8`, `R-OPAMP-IN 6/7`,
`U-BREATH 1/2` — and `ROADMAP.md`'s "Still open" list `[repo ROADMAP.md:309-328]`
covers five of them. `HDR-DEV` (see **N8-6**) and `U-BREATH` are printed on
every run and explained nowhere: `[test] grep -rn U-BREATH` over the corpus
finds no statement of why the row is qty 2.
`ROADMAP.md`'s item 4 also says "**Decoupling is not netted.** Supply pins
arrive through `rails:`, so the per-pin decouplers have no pin to hang on" —
but `C-DECOUPLE-CARRIER` reads **5/8**, so five of them are netted and the
stated reason is false for the majority of that row.

**What would have to be wrong.** That `HDR-DEV` and `U-BREATH` need no reason
because a spare is obvious. `HDR-DEV`'s quantity is contested in three
documents (**N8-6**), so it is not obvious; `U-BREATH` is a $12 sensor at qty 2
with no sentence anywhere.

**Smallest fix.** Two lines in `ROADMAP.md`'s Still-open list, or two sentences
in the two BOM rows, and rewrite item 4 as "the per-pin decouplers that hang on
a pin no netlist declares (`C-DECOUPLE 1/19`, `C-DECOUPLE-CARRIER 5/8`)".

---

### N8-13 — `R-BREATH-OFF` and `C-REG-ADJ`: history pasted back into the BOM notes column, four rows at a time, with the retired aggregate's name reused for a live child

**Severity: low-medium.** `CLAUDE.md` 2b closes with "exemptions inside
`.csv`/`.yaml` went 60 → 0. **Do not put them back.**"

**Claim and evidence.** `[test]` a sentence-level scan of `hardware/bom.csv`
finds six segments over 80 characters appearing in more than one row — 2,273
redundant characters — and five of the six are pure history:

| × | rows | segment |
|---|---|---|
| 4 | `R-BREATH-IN`, `R-BREATH-FB`, `R-BREATH-OFF`, `R-BREATH-OFFNEG` | "R-BREATH-SUM carried '10k / 40.2k 1%' at qty 2 and **R-BREATH-OFF carried '21.0k / 95.3k 1%' at qty 2**…" |
| 4 | same four | "Both also sat in unplaced.csv as parts no page derives…" |
| 4 | same four | "Value and connectivity are now in netlist.yaml, which is authoritative; this row follows it" |
| 4 | `R-REG-SET-HI`, `R-REG-SET-LO`, `C-REG-ADJ`, `C-REG-OUT` | "SPLIT OUT 2026-09-22 FROM AN AGGREGATE ROW THAT COULD NOT BE NETLISTED…" |
| 2 | `C-DIFF-BREATH`, `C-CM-BREATH` | "C-FILT-BREATH carried '15nF C0G (diff) + 1.5nF C0G +/-1% (cm x2)' at qty 3…" |

**And the split reused each aggregate's name for one of its own children**, so
two rows now say something false about themselves:
`[git 82f1464^:hardware/bom.csv]` the aggregate was `R-BREATH-OFF`, `21.0k / 95.3k 1%`,
qty 2; `[repo hardware/bom.csv]` `R-BREATH-OFF` is now `21.0k 1%`, qty 1 — and
its own notes cell reads "R-BREATH-OFF carried '21.0k / 95.3k 1%' at qty 2".
Identically, `[git 3aa4cd0^]` `C-REG-ADJ` was `10uF / 1uF` qty 2 and
`[repo]` `C-REG-ADJ` is `10uF` qty 1. A retired value and a live one sharing a
line in `hardware/bom.csv` is the situation `CLAUDE.md` 2b exists to
eliminate; nothing catches it because the values are in no `forbidden` list.
Context: `[test] audit-notes.py` reports the notes column at **91,736** chars
against the **82,129** measured at `a4b80b1` (the commit that wrote the cut
line into the rules) — +9,607, of which the netlist conversion itself added
3,381. `--regrown` reports 0, so the tool does not see this class.

**What would have to be wrong.** That "R-BREATH-SUM carried …" tells a builder
what to do. It tells them what someone used to think, which is the cut line's
own example of what goes to git.

**Smallest fix.** One sentence per row, stating only the live fact and where the
history is: `R-BREATH-OFF | 21.0k 1% | … | Offset leg. Value and connectivity
are netlist.yaml's; see notes.md for the aggregate it replaced.` Move the
narrative to `hardware/module/breath-output-stage/notes.md` and
`hardware/module/power-entry/notes.md`. If the name reuse is kept, say in the
row that the old `R-BREATH-OFF` was a different line item.

---

### N8-14 — "the pending list just grew from five to eight": the checker printed seven in that commit

**Severity: low.**

**Claim and evidence.** `cfaa6a7`: "a drawing page is one WITH A DRAWING ON IT
rather than one with a parseable label on it - which is why the pending list
just grew from five to eight. That is the honest denominator; it was wrong
before."
`[test]` clone at `cfaa6a7^`: `5 drawing page(s) still without a netlist`.
`[test]` clone at `cfaa6a7`: `7 drawing page(s) still without a netlist` —
`carrier.md`, `display-and-service-uart.md`, `led-strip-drive.md`,
`cluster-boards.md`, `key-register.md`, `key-switch-network.md`,
`key-chain-loom.md`.
"Eight" is reachable only by counting `power-entry-instrument.md`, which the
same commit converted, so the number the commit reports is not the number the
tool printed in that commit. The underlying claim — the old denominator was
wrong and the new detector sees three more pages — is correct.

**What would have to be wrong.** That "grew to eight" describes the set before
the commit's own conversion. That reading is available, and it is not the one a
reader of "the pending list" takes, since the pending list is a thing the tool
prints.

**Smallest fix.** Nothing in the corpus; the sentence is in a commit message.
Recorded so the next round does not re-derive 8 from it.

---

### N8-15 — `R-ILIM`, `LK-SER`, `R-SER-TERM`: three bracketed labels whose values are silently never compared

**Severity: low.** Same root as **N8-1** — a different mechanism, and it
contradicts the same coverage claim.

**Claim and evidence.** `[repo tools/check-netlist.py:632-641]` the
cross-netlist index skips any component with no `value:`
(line 636, `if not c.get("value"): continue`), so a label whose owner deliberately
declares no value falls through to `if ref in foreign: continue`
(line 521) and is not compared. `[repo tools/check-netlist.py:523-530]` a label
naming a BOM row that no netlist places is likewise skipped.
`[test]` a scan of every bracketed label with a non-empty value against the
resolution the tool actually performs finds three that are never compared:
`power-entry.md:56` `[R-ILIM 50mΩ]` (owner declares no `value:`, by design),
`key-chain-loom.md:272` `[LK-SER position B]` and `:274` `[R-SER-TERM 10k]`
(BOM rows placed in no netlist — see **N8-3**).
`[test]` injections in the clone: `[R-ILIM 9GΩ]` → `0 problem(s)`, exit 0;
`[R-SER-TERM 99k]` → `0 problem(s)`, exit 0.
All three are currently *consistent* with the corpus (`R-SER-TERM` is `10k 0805`
in `bom.csv`; `R-ILIM`'s 50 mΩ matches the page's own prose at
`umbilical-load-switch.md:41`), so again the hole is latent.

**What would have to be wrong.** That skipping a label is the same as reporting
it. `76e79b1`'s own reasoning says it is not.

**Smallest fix.** Print one line per run: `N drawing label(s) not compared:
<page>:<line> <label> — <why>`. Three lines today, and the reader can see the
residue instead of inferring it.

---

## C. Injections reproduced, in `/tmp/n8-clone` only

The author claims every fail-open was found "by injection, not by reading" and
quotes the injections. I reproduced nine. **All nine fire, and all nine fire for
the reason claimed.** The shared tree was never modified; `git checkout hardware`
after each.

| Claimed (commit) | Reproduced output `[test]` | Verdict |
|---|---|---|
| `[R-FB 40k]` on the pilot page (`82f1464`) | `hardware/module/breath-output-stage: drawing line 86 shows R-BREATH-FB as '40k', which the netlist's '40.2k 1%' does not support (40k)`, exit 1 | **fires, same message shape as quoted** (the quoted line number was 82; the drawing has since moved) |
| the original regex was a fail-open (`82f1464`) | reverting `LABEL` to `[A-Z][A-Z0-9][A-Z0-9-]*`: the page's labels drop 10 → 2, exactly `[POT-GAIN 50k]` and `[POT-OFFSET 10k]` | **exactly as claimed.** Note the injected 40k is *no longer* silent under the old regex — the later `unparsed_brackets` check catches it (127 noisy problems). The layered defence works. |
| a circuit claiming to drive what the master says it receives (`41e944a`) | `nets.yaml: 'BREATH_INAMP_OUT' names module/breath-receive-stage as out, but that circuit declares dir 'in'`; and with `DAC_AVDD` flipped, `… names module/breath-receive-stage as in, but that circuit declares dir 'out'` | **fires, message identical in form to the quote** |
| a port naming a net nobody owns (`41e944a`) | `module/breath-receive-stage: port 'V_NEG12_TYPO' is in no master net (add it to hardware/nets.yaml)` | **fires** |
| a net with no driver (`41e944a`) | `nets.yaml: 'MODULE_ANALOG_NEG12' has no driver` | **fires** |
| the master's reverse check was missing (`8d66e2d`) | the same run adds `module/power-entry: declares a port on 'MODULE_ANALOG_NEG12' and hardware/nets.yaml does not name it on that net` | **fires, and it is a genuinely new direction** |
| over-use of a qty>1 row (`8646e75`) | two extra `of: R-OPAMP-IN` instances → `instances: R-OPAMP-IN is placed 8 time(s) across all netlists and the BOM buys 7` | **fires, verbatim as quoted** |
| `foreign:` resolved across pages (`c3e61fd`) | `[C-TIMER 1µF]` and `[R-GATE-COMP 2k]` on `power-entry.md` → `drawing line 67 shows C-TIMER as '1µF', which module/umbilical-load-switch's netlist value '10uF' does not support (1uf)` and the same for `R-GATE-COMP` | **fires, and names the owning circuit as claimed.** Also confirms the micro-sign fold. |
| a label split across two lines (`cfaa6a7`) | splitting `[C-BUCK-IN 100µF]` → two `drawing line NN has an unclosed bracket, so any label on it is invisible to every check here` problems | **fires** |

**Did any fix introduce a new fail-open?** I looked specifically at the unit
folds, which are the changes that deliberately erase distinctions.

- `norm()` folds `(?<=\d)([kmg])ohm → \1` *after* `.lower()`, so `50mΩ`
  (milliohm) and `50MΩ` (megaohm) both normalise to `50m` `[test]`. That is a
  10⁹ magnitude collapse, against the function's own comment "folding anything
  that changes a MAGNITUDE would not be". **But the `M`/`m` collapse comes from
  `.lower()`, which was in the original `norm()`** `[git 82f1464:tools/check-netlist.py:102]`,
  so the folds extended a pre-existing hole rather than creating one. No live
  label is affected: the only milliohm in a drawing is `[R-ILIM 50mΩ]`, which is
  unchecked for a different reason (**N8-15**).
- `COUNT = [x×#]\s*\d+` with `re.I` strips `x7` out of `X7R` `[test]
  norm('100nF X7R') → '100nfx7ohm'`, but it strips it from both sides of every
  comparison, so nothing is misjudged.
- The drawing detector counts only Unicode box glyphs (`BOX`), so a schematic
  drawn in pure ASCII `| + -` would be invisible to the whole tool and to the
  pending list. `[test]` I scanned every fenced block in `hardware/**/*.md` for
  heavy ASCII art with fewer than three box glyphs: two hits, both false
  positives (a `[calc]` block on `breath-excitation-reference.md:51-62` and a
  block in an excluded `notes.md`). **No live miss**, latent risk only.
- `check_global`'s blindness to zero-placed rows (**N8-3**) is not new either —
  it is how the check was written in `8646e75` — but it is asserted as complete
  coverage, so I file it.

---

## D. What I did not check

- The per-circuit component/net counts quoted in the eleven intermediate commit
  messages (e.g. "35 components, 26 nets" for `mod-channels`). I verified the
  totals at `82f1464`, `3aa4cd0`, `a4eaa23`, `cfaa6a7`, `5f051c0^` and
  `d1f0cb7`, and every one reproduced; I did not walk the remaining commits.
- Pin numbers and pin names against the banked datasheets (`0e50417`'s claim
  that the DAC8568's pin map was read off `SBAS430E`'s PIN DESCRIPTIONS table).
  That is another slice's domain and I have no way to distinguish a correct
  transcription from a plausible one without the PDF.
- Whether the electrical judgements inside the netlists are right — which gate
  gets which signal, whether `BI` to ground is the recommended circuit, whether
  the ordinal channel map is the intended one. I checked only that each was
  *declared* and marked derived where the commit said it was.
- `a02b628`'s measurements of the seeding pass ("164 rows across 23 circuits,
  114 distinct node spellings, 29 nets named by more than one circuit"). The
  tables have moved since; reproducing the figure at that revision would not
  tell a reader anything actionable now.

## E. One thing worth keeping

`a4eaa23` is the best artefact in this branch. `3aa4cd0` claimed "0 problems, 0
master endpoints awaiting" with 3 problems and 68 awaiting on the screen; the
next commit says so in its subject line, names the hook's non-blocking FAIL as
the mechanism, gives the corrected numbers, and explains the modelling error
that caused the three (`NOBODY DRIVES A GROUND`). `[test]` every one of the
corrected numbers reproduces. That is the shape a wave should aim at, and the
findings above are mostly about the places where this one stopped short of it —
coverage claimed rather than measured, and counts restated rather than printed.
