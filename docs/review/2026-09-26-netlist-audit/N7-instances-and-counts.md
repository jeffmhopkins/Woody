# N7 — instances and counts

**Slice claim type:** how many of each part, and which circuit places it.
**Measured against `d1f0cb7`.** `tools/` treated as frozen; every `[test]`
below was run against a throwaway `git clone` of this repository checked out at
`d1f0cb7` and deleted afterwards. The shared tree was not modified.

**Cold:** nothing under `docs/review/` was read, including this wave's own
directory.

`git diff --stat d1f0cb7 HEAD` is one file, `docs/review/2026-09-26-netlist-audit/README.md`
`[test]`, so the corpus at `HEAD` and at `d1f0cb7` are byte-identical and every
`[repo]` citation below holds at the named revision.

---

## Baseline

```
$ python3 tools/check-netlist.py
netlist: 22 circuit(s), 197 components, 254 nets, 55 master net(s) | 0 problem(s)
  | 0 drawing page(s) still without a netlist | 0 master endpoint(s) awaiting one
per-board bundles not resolved to single nets: KEY_BITS, MARKER_BITS
instances: 102 row(s) placed exactly to BOM qty, 4 counted by section, 7 short:
  C-BUCK-IN 1/2, C-DECOUPLE 1/19, C-DECOUPLE-CARRIER 5/8, HDR-DEV 1/6,
  J-CHAIN 1/8, R-OPAMP-IN 6/7, U-BREATH 1/2
```
`[test]` — identical at `d1f0cb7` and at `HEAD`.

**The row census closes exactly.** `hardware/bom.csv` has 155 rows;
`hardware/unplaced.csv` has 30; 113 distinct rows are placed by at least one
netlist; 12 are in neither set. `[calc] 113 + 30 + 12 = 155` `[test]`. And
`102 + 7 + 4 = 113` — the checker's three buckets account for every placed row.
No row is in both `unplaced.csv` and a netlist `[test]` — **item 5's second half
is clean.**

---

## 1. The seven short rows, one at a time

Five are explained somewhere in the corpus. **Two are not, and the checker's own
source claims otherwise** (N7-10).

| row | placed/qty | verdict |
|---|---|---|
| `R-OPAMP-IN` | 6/7 | genuine open question — **confirmed** |
| `C-BUCK-IN` | 1/2 | real, documented contradiction between two rows |
| `U-BREATH` | 1/2 | modelling limit (a bought spare) — acceptable, badly sited (N7-11) |
| `J-CHAIN` | 1/8 | modelling limit — acceptable, stated in the netlist |
| `HDR-DEV` | 1/6 | modelling limit that **hides a disputed quantity** (N7-3) |
| `C-DECOUPLE-CARRIER` | 5/8 | **real gap, undocumented** (N7-2) |
| `C-DECOUPLE` | 1/19 | **real gap, undocumented, largest** (N7-1) |

### `R-OPAMP-IN` 6/7 — the open question is real. Verified.

The row is qty 7 and allocates as "Pitch, mod 1-4, the mod offset buffer, the
VREFOUT follower" `[repo hardware/bom.csv R-OPAMP-IN notes]`.
`mod-channels.md:213` says the same: "`R-OPAMP-IN` qty 7 covers pitch, the four
mods, this buffer and the `VREFOUT` follower" `[repo]`.

Placed: `module/pitch-stage:R-OPAMP-IN`, `module/mod-channels:R-OPAMP-IN-1..4`,
`module/mod-channels:R-OPAMP-IN-REF` = 6 `[test]`. `[calc] 7 − 6 = 1`, and the
one missing is the `VREFOUT` follower's.

The follower itself **is** placed — it is `U-PITCH-REFBUF`, "Unity follower on
the trimmed reference", `section: A` of `U-OPA-PITCH`
`[repo hardware/module/pitch-stage/netlist.yaml:28-34]` — and its input net
`TRIM_WIPER` runs `TRIM-OFFSET.W → U-PITCH-REFBUF.IN+` with no resistor between
them `[repo same file, nets:]`. `pitch-stage.md`'s "Still open" states exactly
this, names the decision ("whether that (+) input needs clamp-current
protection when the DAC pin reaches it through a 10 kΩ trimmer"), and states
both outcomes: "If it does, the part belongs here and the drawing gains a
label; if it does not, the row is qty 6" `[repo pitch-stage.md:335-343]`.

**This is a genuine open question, correctly filed, with what decides it named.
No finding.**

### `C-BUCK-IN` 1/2 — a documented contradiction, not a transcription gap

`C-BUCK-IN` is qty 2, "One per buck" `[repo hardware/bom.csv]`, and there are
two bucks (`U-BUCK-A`, `U-BUCK-B`, both `of: U-BUCK`, qty 2, exact) `[test]`.
`L-BUCK-IN` is qty 1. The netlist says so in the place a reader will hit it:
"QTY 1 HERE AND THE BOM BUYS 1, against C-BUCK-IN's qty 2 — the two rows
describe different topologies and the page says so"
`[repo hardware/carrier/power-entry-instrument/netlist.yaml:57]`, and
`power-entry-instrument.md:131` and `:149` carry it as an open item: "One LC and
one bulk cap, or two LCs and a missing inductor" `[repo]`.

**Explained. The shortfall is the honest shadow of an undecided topology. No
new finding.**

### `J-CHAIN` 1/8 — modelling limit, acceptable, and stated

`chain-connectors` is a tracked figure: `value: "8"`, `status: settled`,
derivation "carrier 1, RT 2, RH 2, LT 2, LH 1"
`[repo config/figures.yaml:291-297]`. `[calc] 1+2+2+2+1 = 8` ✓ — **qty 8 is
right.**

The netlist header states the limit and predicts the exact string the checker
prints: "this netlist places the carrier's J-CHAIN … and check-netlist prints
J-CHAIN 1/8 rather than claiming the chain is drawn"
`[repo hardware/interfaces/key-chain-loom/netlist.yaml:11-13]`. The reason is
real: the seven board-side positions are asymmetric (2/2/2/1), so
`cluster/key-register`'s `replicated: 4` structurally cannot express them, and
modelling them needs the hop map, which is prose.

**Acceptable, and it hides nothing — the missing seven are named and counted in
the figure's own derivation.**

---

## 2. `replicated:` — both numbers are right, and both are genuinely checked

Two netlists use it: `cluster/key-switch-network` `replicated: 21` and
`cluster/key-register` `replicated: 4` `[test]`.

**21 is right.** `key-marker-and-bits.md`'s allocation table gives the fitted
and reserved switch positions per device: `right_thumb` RT1–3 + sw+ sw− sw? = 6,
`right_hand` RH1–6 = 6, `left_thumb` LT1–4 = 4, `left_hand` LH1–5 = 5
`[repo hardware/cluster/key-marker-and-bits/key-marker-and-bits.md §4]`.
`[calc] 6+6+4+5 = 21`, and the page states the consequence: "**Every position
above gets the full `R-KEY-PU`/`R-KEY-SER`/`C-KEY` network**, including the
three unfitted spares — 21 sets" `[repo]`.

**4 is right.** Four devices in the same table (`right_thumb`, `right_hand`,
`left_thumb`, `left_hand`), and `PCB-CLUSTER` is qty 4 `[repo hardware/bom.csv]`.

**Multiplying out gives the right answer for every row in both circuits,
including the shared one.**

| row | arithmetic | qty |
|---|---|---|
| `C-KEY` | 21 × 1 | 21 ✓ |
| `R-KEY-SER` | 21 × 1 | 21 ✓ |
| `SW1-n` | 21 × 1 | 21 ✓ |
| `R-KEY-PU` | 21 × 1 (switch network) **+ 3 × 1** (`key-marker-and-bits`) = 24 | 24 ✓ |
| `U-KEYS` | 4 × 1 | 4 ✓ |
| `C-DECOUPLE-165` | 4 × 1 | 4 ✓ |

`[calc]` and `[test]`. The shared row is `R-KEY-PU`, and the +3 is the three
free bits, which the page derives independently: 32 bits − 21 switch positions
− 8 marker bits = 3, "`left_thumb` `B` and `A` (22, 23) and `left_hand` `A`
(31)", each "gets an `R-KEY-PU` and nothing else" `[repo key-marker-and-bits.md]`.
`[calc] 32 − 21 − 8 = 3`; `21 + 3 = 24` ✓. Both netlists name this in their
headers rather than leaving the reader to derive it
`[repo hardware/cluster/key-switch-network/netlist.yaml:4-7]`.

**And the factor is checked end to end, in both directions** `[test]`:

```
replicated: 21 -> 22 :  C-KEY 22/21, R-KEY-PU 25/24, R-KEY-SER 22/21, SW1-n 22/21
                        all four reported as over-use problems
replicated: 21 -> 20 :  C-KEY 20/21, R-KEY-PU 23/24, R-KEY-SER 20/21, SW1-n 20/21
                        all four appear in the short list
```

The 22 case is the important one: `R-KEY-PU` reads 25/24, i.e. the cross-circuit
sum tracked the replication factor correctly. **`replicated:` is the one part of
this model that is fully checked and fully right.** No finding.

---

## 3. `section:` — the counts are right; the exemption is not

Four rows are counted by section `[test]`:

| row | instances | packages needed | qty | verdict |
|---|---|---|---|---|
| `R-PRECISION` | `pitch-stage:R1[A]`, `R2[B]` | LT5400 is a **quad**, 2 of 4 elements used → 1 | 1 | ✓ |
| `U-BUF` | `breath-excitation-reference:U-REFBUF[A]`, `U-BREATHBUF[B]` | dual, both halves → 1 | 1 | ✓ |
| `U-RESP` | `breath-response-shaper:U-RESP-A[half]` | 1 half of a dual → 1 | 1 | ✓ (but see N7-4/N7-5) |
| `U-OPA-PITCH` | 10 halves across 4 circuits | see below | 6 | ✓ **only under one of two readings** |

`R-PRECISION` checks out by hand: the row is an "LT5400 1:1 quad (four equal
10k)" and its notes say "Two of four sections used"
`[repo hardware/bom.csv R-PRECISION]`; `pitch-stage.md:344` books the other two
as "The two spare LT5400 resistors" `[repo]`. `[calc] ceil(2/4) = 1` package ✓.

`U-BUF` checks out: one dual, section A the reference buffer, section B the
breath buffer, matching the row's own description "Dual RRIO op-amp: breath
buffer + reference buffer" `[repo hardware/bom.csv U-BUF]`. `[calc] ceil(2/2) = 1` ✓.

### `U-OPA-PITCH`: the ten halves map 1:1 onto the row's enumeration

The row says "Six packages, twelve halves, TEN used: pitch, mod 1-4, mod offset
follower, VREFOUT follower, breath REF-zero buffer, breath gain buffer, breath
summer" `[repo hardware/bom.csv U-OPA-PITCH]`. The ten netlisted halves `[test]`
map onto it exactly:

| row's name | netlist instance | circuit |
|---|---|---|
| pitch | `U-PITCH-AMP[B]` | `module/pitch-stage` |
| VREFOUT follower | `U-PITCH-REFBUF[A]` | `module/pitch-stage` |
| mod 1–4 | `U-MOD-1..4[half]` | `module/mod-channels` |
| mod offset follower | `U-MOD-REFBUF[half]` | `module/mod-channels` |
| breath REF-zero buffer | `U-REF-BUF[A]` | `module/breath-receive-stage` |
| breath gain buffer | `U-BREATH-BUF[A]` | `module/breath-output-stage` |
| breath summer | `U-BREATH-SUM[B]` | `module/breath-output-stage` |

`[calc] 2 + 5 + 1 + 2 = 10` ✓. **The half-count is right and the netlists agree
with the row, name for name.** That is worth recording, because three pages once
disagreed about it `[repo tools/check-netlist.py check_one, comment at l.385]`.

**What the count does *not* settle is the package count**, and that is N7-4.

---

## Findings

### N7-1 — `module/umbilical-load-switch / C-DECOUPLE` — 18 of 19 module decoupling capacitors are placed by nothing, and no file says why

**Severity: High.**

**Claim.** `C-DECOUPLE` is qty 19 and exactly one instance exists in all 22
netlists; the other 18 are placed by no circuit and no file in `hardware/`
records that as deliberate.

**Evidence.** The row's own enumeration is arithmetically sound: "6 x OPA2197 on
+/-12V = 12, INA828 = 2, DAC8568 AVDD+DVDD = 2, 74AHCT125, LT1641 VCC, LM317 in"
`[repo hardware/bom.csv C-DECOUPLE]`, `[calc] 12+2+2+1+1+1 = 19` ✓ — **qty 19 is
right.** The single placed instance is `C-DECOUPLE-LOADSW`, the LT1641's, noted
"One of the board-wide C-DECOUPLE row"
`[repo hardware/module/umbilical-load-switch/netlist.yaml:75-79]`.
`grep -rn -i decoupl hardware/module/*/netlist.yaml` returns that instance and
nothing else `[test]` — no other module netlist mentions decoupling at all, and
`grep -rn "1/19" hardware/` finds nothing `[test]`.

By the row's own enumeration the missing 18 are allocable to circuits that
already have netlists: `pitch-stage` 2, `breath-output-stage` 2,
`breath-receive-stage` 2 (OPA2197) + 2 (INA828), `mod-channels` 6,
`dac8568` 2, `digital-and-supervision` 1 (74AHCT125), `power-entry` 1 (LM317 in).
`[calc] 2+2+2+2+6+2+1+1 = 18`, `18 + 1 = 19` ✓.

The sibling rows show the pattern is available and already used:
`C-DECOUPLE-165` is placed 4/4 and `C-DECOUPLE-CARRIER` 5/8, both via `of:`
`[test]`.

**What would make this wrong.** If the module netlists deliberately model only
signal connectivity and treat supply-pin bypassing as a layout rule — but then
`C-DECOUPLE-LOADSW` would not be netlisted either, and `C-DECOUPLE-165` and
`C-DECOUPLE-CARRIER` would not be. Or if a file I did not read says so; I
grepped `hardware/**` for `decoupl` in every netlist and for the printed string
`1/19` `[test]`, and found nothing.

**Smallest fix.** Either add the 18 instances (`of: C-DECOUPLE`, on the supply
nets each circuit already declares), or add one line to
`hardware/module/umbilical-load-switch/netlist.yaml`'s header saying the other
18 are a layout rule and naming the string `C-DECOUPLE 1/19` so the shortfall
reads as intended rather than unfinished — the shape
`key-chain-loom/netlist.yaml:11-13` already uses.

---

### N7-2 — `carrier/* / C-DECOUPLE-CARRIER` — 3 of 8 are missing from circuits that already place the IC they bypass

**Severity: Medium-High.** Smaller than N7-1 and more clearly a gap, because the
three missing instances are individually named by the row and belong to circuits
that already place the part being decoupled.

**Claim.** The shortfall `C-DECOUPLE-CARRIER 5/8` is a real transcription gap,
not a modelling limit, and nothing anywhere explains it.

**Evidence.** The row's settled enumeration is "MCP3202, REF5050 IN AND OUT,
OPA2197 +12V, 74AHCT125, MPXV4006DP, and both R-78E5 inputs"
`[repo hardware/bom.csv C-DECOUPLE-CARRIER]`. `[calc] 1+2+1+1+1+2 = 8` ✓ —
**qty 8 is right**, and the row records the 7→8 change and the datasheet
authority for it (SBOS410O §9.4.1.1).

Placed `[test]`: `breath-adc:C-DEC-ADC` (MCP3202),
`breath-excitation-reference:C-DEC-REF-VIN` and `C-DEC-REF-VOUT` (REF5050 in and
out), `breath-excitation-reference:C-DEC-SENSOR` (MPXV4006DP VS),
`led-strip-drive:C-DECOUPLE-LED` (74AHCT125) = 5. `[calc] 8 − 5 = 3` missing:
the **OPA2197 +12 V** one and **both R-78E5 input** ones.

Both homes already exist and already place the IC:
`carrier/breath-excitation-reference` places `U-BUF` (the OPA2197) and three
other instances of this very row `[test]`; `carrier/power-entry-instrument`
places `U-BUCK-A` and `U-BUCK-B`, the two R-78E5 `[test]`. Neither declares a
`C-DECOUPLE-CARRIER`.

`grep -rn "5/8\|C-DECOUPLE-CARRIER" hardware/ --include=*.md --include=*.yaml`
returns only the four `of:` sites, one `circuit.yaml` edge and one drawing label
— no explanation `[test]`.

**What would make this wrong.** If the OPA2197's bypass on the carrier is
actually the row `C-DECOUPLE` (module) rather than this one — but that row's
enumeration is explicitly module-side ("6 x OPA2197 on +/-12V" is the module's
six), and this row's own text names "OPA2197 +12V" among its eight.

**Smallest fix.** Three instances: one `of: C-DECOUPLE-CARRIER` on `U-BUF`'s
+12 V node in `hardware/carrier/breath-excitation-reference/netlist.yaml`, two on
`U-BUCK-A.IN`/`U-BUCK-B.IN` in
`hardware/carrier/power-entry-instrument/netlist.yaml`. That takes the row to
8/8 and removes it from the short list.

---

### N7-3 — `carrier / HDR-DEV` — qty 6 is described three incompatible ways, and `carrier.md` refutes its own fragment

**Severity: High.** This is the named failure of this repository, inside the
instance count: the page's reasoning moved and the row it derives did not
follow, and the netlist note written to explain the shortfall restates the
quantity wrongly.

**Claim.** `HDR-DEV` qty 6 is not supported by the page that owns it, and the
three places that explain it give three different arithmetics.

**Evidence.**

1. **The fragment** (`hardware/carrier/bom.csv`, so the row's owner is
   `carrier/`): description "Sockets for **both** dev boards on the carrier",
   notes "Cut to length: 2 strips for the ESP32-S3-Matrix, 2 for the
   T-Display-S3 AMOLED, 2 spare" `[repo]`. `[calc] 2+2+2 = 6`.
2. **`carrier.md:293`**, the owning page's own value table:
   "`HDR-DEV` | 2 × 10-way machined socket | **Qty is one board's worth, not
   two** — the display board is 360 mm away" `[repo]`.
3. **`carrier/netlist.yaml:69`**: "**Six strips for one dev board**, which is
   why the instance count reads HDR-DEV 1/6: one mating part, six pieces
   bought" `[repo]`.

(2) and (3) both say "one board", and contradict each other on how many strips
that is — 2 versus 6. (1) says two boards. And `carrier.md`'s §"One dev board,
not two" settles the physical question against (1): "`HDR-DEV` in the BOM
budgets header strips for both. **The display board is 360 mm away at the top of
the instrument** … It reaches this board through a loom, not a socket"
`[repo carrier.md:25-32]`, corroborated by
`display-and-service-uart.md:6` ("the nine-conductor loom to the display board
360 mm up the body") and `:11` ("*the display board has no schematic page in
this corpus*") `[repo]`.

So by the page's own reasoning the T-Display's 2 strips are not on this board:
`[calc] 6 − 2 = 4` (2 fitted + 2 spare), and qty should be 4.

The netlist's own explanation is the part that matters most, because it is the
text a reader hits when checking the shortfall: "Six strips for one dev board"
is true of no reading in the corpus — (1) gives 2 per board, (2) gives 2.

**What would make this wrong.** If the display board carries its own pair of
`HDR-DEV` strips at its remote location and the row is a system-wide budget
rather than a carrier budget. That would still refute `carrier.md:293` ("one
board's worth") and the description's "on the carrier", and the display board
has no page to place them on — so it moves the defect rather than removing it.

**Smallest fix.** Decide whether qty is 4 or 6, correct the losing statements in
the same commit, and replace `carrier/netlist.yaml:69`'s "Six strips for one dev
board" with the arithmetic that survives. If 6 is kept as a system budget, the
2 display strips belong in `hardware/unplaced.csv`'s territory — a part no
schematic page derives — not folded into a placed row.

---

### N7-4 — `module/breath-response-shaper / U-RESP` and `module/breath-receive-stage / U-OPA-PITCH` — the module's OPA2197 package count is asserted two ways, and `section:` records nothing that could settle it

**Severity: High.** This is the recorded disagreement the corpus has about how
many halves are spoken for, and it is still live at `d1f0cb7`.

**Claim.** The corpus asserts both that `U-RESP` is a **seventh** OPA2197
package and that `U-RESP` **consumes two of `U-OPA-PITCH`'s twelve halves**.
Those cannot both be true; one of them means an OPA2197 is over-bought and the
other means three rows' notes are wrong. No netlist can decide it, because
`section:` never says which halves share a package.

**Evidence.**

- `U-OPA-PITCH`: qty **6**, "Six packages, twelve halves, TEN used … **TWO
  SPARE** — and U-RESP claims both of them if it is fitted, so check that row
  before spending them" `[repo hardware/bom.csv U-OPA-PITCH]`.
- `U-RESP`: a **separate row**, qty **1**, part `OPA2197IDR`, "*** THIS PACKAGE
  CONSUMES BOTH OF THE MODULE'S REMAINING SPARE OPA2197 HALVES ***"
  `[repo hardware/bom.csv U-RESP]`.
- `C-DECOUPLE`: "*** THIS ENUMERATION EXCLUDES U-RESP, which is a **SEVENTH
  OPA2197 package** ***" `[repo hardware/bom.csv C-DECOUPLE]`.
- `POT-OFFSET`: "DO NOT order one unless U-RESP is fitted to buffer this wiper —
  see that row, which spends both of the module's remaining spare op-amp halves"
  `[repo hardware/bom.csv POT-OFFSET]`.
- `breath-response-shaper.md:30`: "`U-RESP`'s two halves — **the last two on the
  module**" `[repo]`.

A BOM is a purchase list, so qty 6 + qty 1 = **7 packages bought**
`[calc]`. Then `C-DECOUPLE` is right and the other four statements are wrong:
`U-RESP` brings its own two halves and `U-OPA-PITCH`'s two spares are untouched,
so the module still has two spare halves after the shaper is fitted, and "no
spare op-amp capacity left" `[repo U-RESP notes]` is false.

The reason nothing can adjudicate it is the pairing, and **the pairing is
nowhere recorded.** Two pairings are consistent with the netlists, and they give
different answers:

| pairing | packages for the 10 halves | `U-OPA-PITCH` qty 6 means | is `U-RESP` a 7th? |
|---|---|---|---|
| halves pair **within a circuit** (`pitch` 2→1, `breath-output` 2→1, `breath-receive` 1→1, `mod-channels` 5→3) | `[calc] 1+1+1+3 = 6` | 6 needed, **0 whole spare package**, 2 spare halves in two different packages | **yes** — the shaper's pair cannot use two halves in two distant packages, so a 7th is genuinely needed, and `U-RESP` qty 1 is right |
| `breath-receive`'s half pairs with a `mod-channels` half (6 halves → 3 packages) | `[calc] 1+1+3 = 5` | 5 needed, **1 whole spare package** = the 2 spare halves | **no** — that spare package *is* `U-RESP`'s, so qty 6 + qty 1 buys 7 to populate 6 and **one OPA2197 is over-bought** |

`U-OPA-PITCH`'s own wording ("TWO SPARE — and U-RESP claims both of them")
asserts the second pairing; `C-DECOUPLE`'s wording asserts the first. The
`section:` values cannot break the tie: `pitch-stage`, `breath-output-stage` and
`breath-receive-stage` use `A`/`B`, while all five `mod-channels` halves and
`U-RESP-A` use the bare token `half` `[test]`, which names no package. There is
no `package:` field and no netlist-level pairing anywhere `[test]`.

**What would make this wrong.** If `section: half` is understood by convention
to mean "pair them in declaration order", so `mod-channels`' five are
`U-MOD-REFBUF`+`U-MOD-1`, `U-MOD-2`+`U-MOD-3`, `U-MOD-4`+spare. That fixes
`mod-channels` at 3 packages and selects the *first* pairing — making
`C-DECOUPLE` right and `U-OPA-PITCH`, `U-RESP`, `POT-OFFSET` and
`breath-response-shaper.md:30` wrong about the spares. Nothing in the corpus
states that convention `[test]`, so it cannot be relied on; either way one of
the two groups of statements is wrong.

**Smallest fix.** Two parts. (a) Replace the bare `half` tokens with `A`/`B` and
a package discriminator so the pairing is data — e.g. `section: A` /
`section: B` with `package: U-OPA-PITCH-3`. (b) Say once, on `U-OPA-PITCH`,
whether `U-RESP` is a seventh package or the sixth one's second use, and delete
the losing sentence from the other three rows and from
`breath-response-shaper.md:30`. Until (a) exists, no tool can check (b) — which
is the point of the finding.

---

### N7-5 — `module/breath-response-shaper / U-RESP` — the second half has two incompatible jobs, and the netlist places neither

**Severity: Medium.** Independent of N7-4: this is about what the two halves
*do*, not how many packages exist.

**Claim.** `U-RESP`'s second half is claimed for two different circuits, and one
of the two claims silently deletes the restoring stage the row's own description
names.

**Evidence.** Reading A — the row's **description** column: "Response shaper:
1/2 shapes at /2 inverting, **1/2 restores x2 inverting**"
`[repo hardware/bom.csv U-RESP]`, corroborated by the page's cost table: "**Both
remaining OPA2197 halves** — one shapes at ÷2 inverting, one restores ×2
inverting to put scale and polarity back"
`[repo hardware/module/breath-response-shaper/breath-response-shaper.md:135]`
and by the netlist header, which quotes it verbatim
`[repo .../netlist.yaml:8-13]`.

Reading B — the row's **notes** column: "because the shaper needs one and
**POT-OFFSET's wiper needs the other** — unbuffered, its zero sits ~20 degrees
past centre at +0.605V" `[repo hardware/bom.csv U-RESP]`, corroborated by
`POT-OFFSET`'s notes `[repo]`.

The two readings are in **the same CSV row, one field apart.** Under A the
POT-OFFSET wiper stays unbuffered; under B the ×2 restoring stage does not
exist. If both are wanted that is 3 halves = 2 packages, and qty 1 is short:
`[calc] ceil(3/2) = 2 ≠ 1`.

The netlist places one half, `U-RESP-A`, "The shaping half, inverting at /2. The
restoring half is the page's other one and is not drawn"
`[repo .../netlist.yaml:U-RESP-A]`, and declines to invent the second: "writing
it would be inventing it" `[repo .../netlist.yaml header]`. The page carries it
as an open item, "**The restoring half is costed and not drawn**"
`[repo breath-response-shaper.md:141]`. **The netlist and the page are the
honest documents here; the BOM row is the defect.** And `POT-OFFSET`'s wiper is
in fact unbuffered in the netlist — `POT-OFFSET.W` reaches
`U-BREATH-SUM.IN-` through a resistor with no follower
`[repo hardware/module/breath-output-stage/netlist.yaml, nets]`.

**What would make this wrong.** If the ×2 restoring stage and the POT-OFFSET
buffer are the same op-amp doing both jobs — an inverting ×2 stage whose input
is the pot wiper. Nothing says that; the wiper and `V_shaped` are different
nodes in different circuits `[repo both netlists]`, and `V_SHAPED`'s comment
says "WHERE THIS INSERTS IS OPEN".

**Smallest fix.** Pick one in `U-RESP`'s notes and make the description agree,
or state that three halves are wanted and move the row to qty 2. One field of
one row.

---

### N7-6 — `module/power-entry / C-BULK-RAIL` — the value string enumerates three rails for four placed capacitors, and the one it omits is a +12 V branch at 47 µF

**Severity: Medium.**

**Claim.** `C-BULK-RAIL` is qty 4, placed 4/4, and its `part` field
`100uF (+12V) / 47uF (-12V, +5V)` accounts for only three of them; the fourth,
`C2`, sits on a second +12 V branch and is 47 µF, which the row's own rule would
make 100 µF.

**Evidence.** Four instances `C1..C4`, all `of: C-BULK-RAIL`, declared 100uF,
47uF, 47uF, 47uF `[test]`. The nets `[repo hardware/module/power-entry/netlist.yaml]`:

```
BUS_POS12_RAW : J-PWR-EURO.POS12, D1.A, D2.A     <- D1 and D2 are BOTH on +12 V
POS12_D1 -> FB1 -> MODULE_ANALOG_POS12 : C1 (100uF)
POS12_D2 -> FB2 -> PWR_EXPORT          : C2 ( 47uF)   <- +12 V, and not enumerated
NEG12_FB -> FB3 -> MODULE_ANALOG_NEG12 : C3 ( 47uF)
BUS_5V_IN -> FB4 -> BUS_5V             : C4 ( 47uF)
```

So the placed set is {+12 V analog, +12 V export, −12 V, +5 V} and the row names
{+12 V, −12 V, +5 V}. `[calc] 4 instances, 3 rails named.`

The row's notes argue 100 µF specifically for "**The** +12V branch" carrying
"the LM317's divider, the DAC and the comparator … about 22mA against -12V's
10mA" `[repo hardware/bom.csv C-BULK-RAIL]` — singular, and that is
`MODULE_ANALOG_POS12`/`C1`, matching `U-REG-DAC.IN` on that net `[repo]`. The
allocation the netlist makes is therefore defensible; **the `part` string is
what is wrong**, and `C1`'s own note inherits it: "100uF on +12 V, NOT 47uF —
the other three are 47uF and this one is not" `[repo .../netlist.yaml:86]` is
only true if the export branch does not count as +12 V.

This also means the row is vacuously value-checked into agreement: the checker
tests `norm(c["value"]) not in norm(bom[row]["part"])`
`[repo tools/check-netlist.py:376]`, and both `100uF` and `47uF` appear in the
string, so **any** of the four caps could be either value and pass.

**What would make this wrong.** If `PWR_EXPORT` is not a +12 V rail — but
`D2.A` is on `BUS_POS12_RAW` with `D1.A` `[repo]`, so it is.

**Smallest fix.** Rewrite the `part` field to enumerate four branches, e.g.
`100uF (+12V analog) / 47uF (+12V export, -12V, +5V)`, and adjust `C1`'s note to
say "the +12 V **analog** branch".

---

### N7-7 — `module/pitch-stage / R-BIAS-INAMP` — the row lives in a fragment whose page only mentions it as a contrast, and places none of it

**Severity: Medium.** The netlists make this provable for the first time.

**Claim.** `R-BIAS-INAMP` violates "a row lives with the circuit **whose page
derives its value**" `[repo CLAUDE.md]`: it sits in
`hardware/module/pitch-stage/bom.csv`, `module/pitch-stage` places zero
instances, and `module/breath-receive-stage` places both.

**Evidence.** Fragment ownership: `hardware/module/pitch-stage/bom.csv` `[test]`.
Placement: `module/breath-receive-stage:R4` and `:R5`, both `of: R-BIAS-INAMP`,
2/2 exact; `module/pitch-stage` places none `[test]`.

The value is derived on the placing page: the drawing shows `[R4 1M]` and
`[R5 1M]` `[repo hardware/module/breath-receive-stage/breath-receive-stage.md:85]`
and the argument that fixes 1 MΩ is there — "times the 1M/(1M+11k) bias divider"
`[repo :100]`, with the correction history at `:129`.

`pitch-stage.md`'s **only** mention is a precedent in a "Still open" bullet:
"This project already fixed the identical problem on the breath in-amp with
`R-BIAS-INAMP`. `R-BIAS-DAC` now does it here" `[repo pitch-stage.md:326]` — the
part that does the job on that page is `R-BIAS-DAC`, a different row.
`hardware/README.md` already records this edge as verified-false: "`pitch-stage`
→ `R-BIAS-INAMP` | the page names it as an explicit **contrast**" `[repo]`.

**What would make this wrong.** If `pitch-stage.md` derived the 1 MΩ and
`breath-receive-stage.md` merely restated it. It does not: `grep -n R-BIAS-INAMP
hardware/module/pitch-stage/*.md` returns the single line above `[test]`.

**Smallest fix.** Move the row from `hardware/module/pitch-stage/bom.csv` to
`hardware/module/breath-receive-stage/bom.csv` and re-run
`tools/merge-bom.py`. The master row is byte-identical either way, so
`merge-bom.py --check` stays green and no other file changes.

---

### N7-8 — `tools/check-netlist.py` `check_global` — one `section:` token anywhere on a row exempts that row from over-use **and** shortfall detection, globally

**Severity: Medium.** A latent fail-open on four rows today, including the two
most-disputed rows in the corpus (N7-4). Reported as a model limit, not a code
change: `tools/` is frozen.

**Claim.** `check_global` skips a row entirely if *any* instance of it carries
`section:`, so the 4 rows "counted by section" are unchecked in both directions,
and a single stray `section:` would silence a real over-use.

**Evidence.** `[repo tools/check-netlist.py check_global]`:

```python
if sections[row]:
    continue          # a package supplying sections is counted in prose
if n > have:
    problems.append(... is placed ... and the BOM buys ...)
```

The `continue` precedes the over-use test, so the exemption covers over-use, not
just half-counting. Proven `[test]`, on a clone at `d1f0cb7`:

- **Positive control.** Three extra `of: R-OUT-PROT` instances (qty 6 → placed
  9, no sections) →
  `instances: R-OUT-PROT is placed 9 time(s) across all netlists and the BOM buys 6`.
- **Add `section: half` to exactly one of those nine** → the problem disappears;
  the line becomes `101 row(s) placed exactly …, 5 counted by section, 7 short`.
  Nine instances against a qty of 6, silent.
- **Over-place a sectioned row.** Four extra `of: U-OPA-PITCH, section: half`
  instances in `mod-channels` → 14 halves against 6 packages (12 halves). The
  `instances:` line is **byte-identical to the baseline**; the only 12 problems
  reported are unconnected-pin errors from my stub components, zero instance
  problems.

The same guard exists per-circuit `[repo check_one, `if sections: continue`]`,
computed as `c.get("of") == row and c.get("section")` — so a sectioned instance
declared *without* `of:` would not be counted as a section there, and the
per-circuit over-use test would fire while the global one stayed silent. No such
instance exists today (all 15 sectioned instances carry `of:` `[test]`), so that
half is latent.

**Is the limit acceptable?** For `R-PRECISION` and `U-BUF` yes — both are
single-package rows whose element counts I verified by hand above. For
`U-OPA-PITCH` and `U-RESP` **no**: those are exactly the rows the corpus
contradicts itself about (N7-4, N7-5), and the exemption is why the
contradiction has survived. The docstring's phrase "counted in prose" is
accurate and is the problem: the prose does not agree with itself.

**What would make this wrong.** If a sectioned row's package count were checked
somewhere else. Nothing checks it: `grep -n "section" tools/check-netlist.py`
shows the token only in the two `continue` guards and the `sections` counters
`[test]`.

**Smallest fix,** for whenever `tools/` unfreezes: keep the exemption but make it
narrow — compute `ceil(sections[row] / elements_per_package)` from a declared
per-package element count and compare that to `qty`, and let a row with
*mixed* sectioned and unsectioned instances fall through to the ordinary
over-use test instead of being exempted whole. The prerequisite is N7-4(a):
until `section:` records pairing, there is nothing to compute from.

---

### N7-9 — `check_global` — a row placed **zero** times is invisible, and twelve rows are in that state

**Severity: Medium.**

**Claim.** The instance check iterates only over rows some netlist places, so a
row that drops to zero instances produces no output at all — and twelve
`bom.csv` rows are currently placed by nothing while also not being in
`unplaced.csv`.

**Evidence.** `for row, n in sorted(used.items())` where `used` is a `Counter`
built from placed instances `[repo tools/check-netlist.py check_global]`; a row
absent from `used` is never examined. Proven `[test]`: on a clone I repointed
`HDR-SERVICE`'s instance to another row, taking `HDR-SERVICE` (qty 1) from 1/1
to placed-zero. The `instances:` line came back **byte-identical** —
`102 row(s) placed exactly to BOM qty, 4 counted by section, 7 short` — with no
mention of `HDR-SERVICE`. A part vanishing from every schematic is the one
instance error this checker cannot see.

The twelve rows `[test]`:

| row | qty | owning fragment | why it is not placed |
|---|---|---|---|
| `PCB-CARRIER` | 1 | `carrier` | not a netlistable component |
| `PCB-CLUSTER` | 4 | `cluster` | ditto |
| `PCB-MODULE` | — | *(in `unplaced.csv`)* | — |
| `PANEL` | 1 | `module/panel` | `module/panel` has a page and **no netlist** (its page carries no drawing, so the rollout counter does not flag it) |
| `PLATE-TOP` | 1 | `cluster` | mechanical |
| `PLATE-THUMB` | 1 | `cluster/key-marker-and-bits` | mechanical |
| `MECH-COAT` | 1 | `carrier` | mechanical |
| `WIRE-LOOM` | 1 | `carrier` | mechanical |
| `C-BULK-DISP` | 1 | `carrier/power-entry-instrument` | display board has no page; open item at `power-entry-instrument.md:145-148` `[repo]` |
| `SW-THUMB` | 4 | `cluster/key-switch-network` | an **alternative** to 4 of `SW1-n` (N7-14) |
| `LK-SER` | 4 | `interfaces/key-chain-loom` | stated: "LK-SER and R-SER-TERM are not placed" `[repo .../netlist.yaml:12]` |
| `R-SER-TERM` | 1 | `interfaces/key-chain-loom` | same line |
| `R-TRIM-RANGE` | 4 | `module/pitch-stage` | open: "Its span needs R-TRIM-RANGE, which is undecided" `[repo pitch-stage/netlist.yaml:26]` |

Most are legitimately in neither set: `unplaced.csv` holds "the BOM rows **no
schematic page derives**" `[repo hardware/README.md]`, and a page *does* derive
`PCB-CARRIER`, `PLATE-TOP`, `MECH-COAT`. **There is no third category** for
"derived by a page, but not a component a netlist can place" — so the count of
parts nobody has drawn is silently 12 short of the number a reader would want,
and the checker's 113-row census reads as complete when it covers 113 of 155.

**What would make this wrong.** If a netlist places one of the twelve under a
different name via `of:` — ruled out, `of:` targets were enumerated exhaustively
and all 113 resolve `[test]` — or if `module/panel` is expected to gain a
netlist, which would move `PANEL` only.

**Smallest fix.** Add a line to `hardware/README.md`'s "What is deliberately not
here" naming the third category and the count-by-arithmetic
(`155 − 30 − 113 = 12`), so a reader knows the census closes. Marking the
mechanical rows with a `netlistable: no` column would make it checkable, but
that is a schema change, not the smallest fix.

---

### N7-10 — `tools/check-netlist.py` — two of the seven shortfalls have no written reason, against a source comment that says every one does; and the docstring misstates which thing is unplaced

**Severity: Medium.** Two separate errors in the same file, both about my slice's
claim type. `tools/` is frozen, so the corpus-side fix is N7-1 and N7-2.

**Claim (a).** The comment above the printed instance line asserts "**every one
of them so far has a reason written down somewhere**" `[repo
tools/check-netlist.py main, comment above the `instances:` print]`. Five do.
`C-DECOUPLE 1/19` and `C-DECOUPLE-CARRIER 5/8` do not — greps for the printed
strings and for `decoupl` across every netlist return no explanation
`[test]`, and N7-1/N7-2 give the detail. So the sentence that tells a reader the
short list is benign is false for 2 of 7 `[calc] 5/7 documented`.

**Claim (b).** `check_global`'s docstring says of `R-OPAMP-IN`: "The seventh is
claimed by a sentence on mod-channels.md for the VREFOUT follower, **which no
drawing shows and no netlist places**" `[repo]`. On its natural reading the
relative clause attaches to *the VREFOUT follower* — and the VREFOUT follower is
placed, as `U-PITCH-REFBUF`, `section: A` of `U-OPA-PITCH`
`[repo hardware/module/pitch-stage/netlist.yaml:28-34]`, and it **is** drawn:
`pitch-stage.md:31-32` shows `VREFOUT ──[TRIM-OFFSET 10k]──┬── ½ OPA2197 ──┬──
V_ref` labelled "follower" `[repo]`. What is unplaced and undrawn is the
*resistor*. `pitch-stage.md:335-343` states it correctly `[repo]`; the docstring
is the one place a reader is told the follower does not exist.

**What would make this wrong.** For (a), a reason in a file I did not grep — I
searched all 22 netlists and all of `hardware/**` `*.md`/`*.yaml` `[test]`, and
deliberately did not search `docs/review/` (cold), but a review directory is not
where a builder looks and `CLAUDE.md` §6 says those are not the corpus. For (b),
reading "which" as attaching to "The seventh" — grammatically available, and the
sentence is then true; the finding is that the nearer antecedent makes it false,
which is a one-word fix.

**Smallest fix.** (a) is fixed by N7-1 and N7-2 writing the two reasons down; the
comment then becomes true again. (b) is one word: "…for the VREFOUT follower, a
resistor which no drawing shows and no netlist places."

---

### N7-11 — `interfaces/breath-sense-link / U-BREATH` — the reason qty is 2 is written only on a different row

**Severity: Low.** The shortfall is a correct modelling limit; the siting of its
explanation is the defect.

**Claim.** `U-BREATH 1/2` is right — one sensor is on the board and the second is
a purchased spare — but `U-BREATH`'s own row never says so, and the only
statement of it is in `SKT-BREATH`'s notes.

**Evidence.** `SKT-BREATH`: "ADR 0003 calls the sensor a wear part and **buys
two**. The spare is only reachable if the first part comes out"
`[repo hardware/bom.csv SKT-BREATH]`. `U-BREATH`'s notes are among the longest
in the file and contain no count `[repo hardware/bom.csv U-BREATH]`; grepping
`U-BREATH`/`MPXV4006` across `hardware/`, `docs/decisions/`, `docs/reference/`
and `config/` for a quantity statement returns only `SKT-BREATH`'s line `[test]`.
One instance is placed, in `interfaces/breath-sense-link` `[test]`, which is
correct: the spare is in a drawer.

Note the corpus is inconsistient about where bought spares live: `U-MCU-SPARE`
is a separate row in `unplaced.csv` `[repo]`, `HDR-DEV` folds "2 spare" into a
placed row (N7-3), and `U-BREATH` folds one spare into a placed row with the
reason on a neighbour. All three read as shortfalls to the checker.

**What would make this wrong.** If the second MPXV4006DP is fitted somewhere —
there is one `SKT-BREATH` (qty 1, placed 1/1) and one sensor node `[test]`, so
it is not.

**Smallest fix.** One clause in `U-BREATH`'s notes: "QTY 2 — one fitted, one
spare; see `SKT-BREATH`." Better still, split the spare into `unplaced.csv` the
way `U-MCU-SPARE` is, which removes the row from the short list.

---

### N7-12 — `carrier/power-entry-instrument / D-USBOR` — the two instances declare no `value:`, so the BOM-value check passes them vacuously

**Severity: Low.**

**Claim.** `D-USBOR-A` and `D-USBOR-B` are the only `of:` instances in the corpus
with no `value:` field, and the checker's value test is conditional on the field
being present — so the one row whose part is explicitly undecided is the one row
with no value cross-check.

**Evidence.** All 113 `of:` instances were enumerated and their declared
`value`/`part` compared against the BOM `part` field; every one matches, and
`D-USBOR-A`/`-B` are the only two with no value at all `[test]`:
`{'of': 'D-USBOR', 'pins': ['A','K'], 'note': 'ONE PER REGULATOR OUTPUT…'}`.
The guard is `if "value" in c and norm(c["value"]) not in norm(bom[row_ref]["part"])`
`[repo tools/check-netlist.py:376]`. The row's part is
`1N5817 (DO-41) or SS14 (SMA) - OPEN` `[repo hardware/bom.csv D-USBOR]` — two
candidate parts in two packages, undecided. That the check fires when a value
*is* present I confirmed incidentally `[test]`: repointing a `2x3` header at
`MECH-COAT` produced
`HDR-SERVICE value '2x3' does not appear in its BOM part field 'Acrylic conformal coating'`.

**What would make this wrong.** If omitting `value:` is the deliberate way to say
"the part is not chosen yet". That would be a defensible convention — but it is
stated nowhere `[test]`, and the two other `open`-status rows with undecided
parts, `R-PRECISION` and `U-RESP`, *do* declare values (`10k`, `OPA2197`).

**Smallest fix.** Give both instances `value: "1N5817"` or `"SS14"` once the
package is chosen; until then, a `note:` on `D-USBOR-B` pointing at the open
choice, since `D-USBOR-B` currently has no note either.

---

### N7-13 — `C-DECOUPLE` and `C-DECOUPLE-CARRIER` — both board-wide rows live with a circuit that places a small minority of them

**Severity: Low.** Suspicion, stated as suspicion: I can prove the placement
asymmetry and that the placing page does not derive the value, but "whose page
derives its value" admits judgement for a row that is nobody's circuit in
particular.

**Evidence.** `C-DECOUPLE` (qty 19) lives in
`hardware/module/umbilical-load-switch/bom.csv` `[test]` and that circuit places
1 of 19. `umbilical-load-switch.md`'s only mention is a *use*: "`[p.9, Supply
Transient Protection]`, which `C-DECOUPLE` already provides"
`[repo :315]` — the value 100 nF and the 19-part enumeration are board-wide and
attributed to ADR 0004 in the row itself `[repo]`.

`C-DECOUPLE-CARRIER` (qty 8) lives in
`hardware/carrier/led-strip-drive/bom.csv` `[test]` and that circuit places 1 of
8; three of the five placed are in `carrier/breath-excitation-reference`
`[test]`. The row's settled allocation is argued from the REF5050 datasheet and
cites `figures.yaml cref-out-node`, ending "the VS one is the 100 nF **the
reference buffer's compensation is designed against**" `[repo hardware/bom.csv]`
— which is `breath-excitation-reference`'s argument, and that page owns
`riso-ref-topology` `[repo .../breath-excitation-reference.md:29]`.

**What would make this wrong.** If a board-wide row is understood to live with
whichever circuit happens to place one, or with the first circuit converted.
Either reading is possible; `CLAUDE.md`'s rule does not cover a row no single
page derives.

**Smallest fix.** Move `C-DECOUPLE-CARRIER` to
`hardware/carrier/breath-excitation-reference/bom.csv`, which is where its
allocation argument lives; leave `C-DECOUPLE` alone until N7-1 decides where its
18 siblings go, and then put the row with whichever circuit places the most.
Either move is fragment-only, so `merge-bom.py --check` stays green.

---

### N7-14 — `cluster/key-switch-network / SW-THUMB` — 25 switches are budgeted for 21 positions, and the model cannot express the either/or

**Severity: Low, latent.** Correctly documented today; noted because it is the
one place where the instance count would go *wrong* rather than short if a
decision landed.

**Evidence.** `SW1-n` qty 21, placed 21/21 exact `[test]`. `SW-THUMB` qty 4,
placed 0, "Optional lighter-spring switches for the four left-thumb keys …
**If taken, SW1-n drops by 4**" `[repo hardware/bom.csv SW-THUMB]`.
`[calc] 21 + 4 = 25` switches bought for 21 positions — correct as an either/or,
wrong as a sum. If M1 takes the option, `SW1-n` must go to 17 while
`key-switch-network`'s `replicated: 21` stays 21, and `SW1-n` would then read
21/17 as an over-use that is not one. Nothing in the netlist model expresses
"one of these two rows per position".

**What would make this wrong.** If `SW-THUMB` is additive — four extra switches
somewhere. The row says the opposite in its own words.

**Smallest fix.** A `note:` on `SW1-n` in
`hardware/cluster/key-switch-network/netlist.yaml` saying the instance count is
21 only while `SW-THUMB` is unfitted, and naming what happens if it is. That
costs one line and makes the future over-use legible instead of surprising.

---

### N7-15 — `R1` / `R2` — the same instance name denotes three different BOM rows, and the cross-page resolver nulls it

**Severity: Low.**

**Claim.** `R1` and `R2` are each used as an instance name or `drawn_as` alias in
three circuits for three different BOM rows, so the checker's cross-page index
marks them ambiguous and drops them — meaning a `[R1 …]` or `[R2 …]` label on a
page that does not own the part resolves against nothing.

**Evidence** `[test]`:

| name | circuit | row |
|---|---|---|
| `R1` | `interfaces/breath-sense-link` | `R-SER-BREATH-INST` |
| `R1` | `module/pitch-stage` | `R-PRECISION` |
| `R1` (`drawn_as`) | `module/breath-response-shaper` | `R-RESP-IN` |
| `R2` | `module/pitch-stage` | `R-PRECISION` |
| `R2` | `module/breath-receive-stage` | `R-SER-BREATH` |
| `R2` (`drawn_as`) | `module/breath-response-shaper` | `R-RESP-FB` |

`main` builds `elsewhere` over both `ref` and `drawn_as`, and on a second row for
the same name sets `elsewhere[name] = None`, then filters the Nones out
`[repo tools/check-netlist.py main]`. Local resolution still wins inside the
owning circuit, so **nothing is broken today** — but `module/breath-receive-stage`
declares `R1` and `R1b` `foreign:` from `interfaces/breath-sense-link`
`[test]`, which is exactly the case that depends on cross-page resolution, and
it survives only because `foreign:` resolves by row rather than by name
`[repo check_one, "A foreign part resolves BY ROW"]`.

Separately and to close item 4: `R1`/`R1b` are **not** one part placed twice.
They are the signal-leg and AGND-leg halves of `R-SER-BREATH-INST` (qty 2),
"THE TWIN IN THE AGND LEG, and it was missing until 2026-09-21"
`[repo hardware/interfaces/breath-sense-link/netlist.yaml]` — 2/2, exact, and
correct. The same holds for `R4`/`R5` (`R-BIAS-INAMP`), `R2`/`R3`
(`R-SER-BREATH`), `C-CM-IN+`/`C-CM-IN-`, `D-CLAMP-IN+`/`D-CLAMP-IN-`,
`D-TVS-BREATH-SIG`/`-RET`, `U-REFBUF`/`U-BREATHBUF`, `U-REF-BUF`, `D-USBOR-A`/`-B`,
`U-BUCK-A`/`-B`, `C-STRIP-BULK-L`/`-R`, `R-LED-SER-L`/`-R`, `J-UMB-MOD`/`-INST`.
**No part is placed twice under different names** `[test]`.

**What would make this wrong.** Nothing observable today — this is a hazard, not
a defect. It becomes one the first time a page draws a `[R1 …]` or `[R2 …]` it
does not own without a `foreign:` entry.

**Smallest fix.** None needed now. If touched, renaming `pitch-stage`'s `R1`/`R2`
to `R-PRECISION-A`/`-B` removes both collisions; note that
`pitch-stage.md`'s drawing uses the short form for column width, so the rename
needs `drawn_as: R1` / `drawn_as: R2` kept.

---

## Item 4, closed: `of:` is right everywhere

All 113 `of:` targets resolve to a `hardware/bom.csv` row, and every instance's
declared `value`/`part` appears in that row's `part` field — checked
independently of the tool by enumerating all 22 netlists and comparing against
the master `[test]`. The two exceptions to the value check are `D-USBOR-A`/`-B`,
which declare no value (N7-12).

**No part is placed in a circuit that neither owns the row nor draws it with no
reason given.** Every cross-fragment placement is either a board-level aggregate
row (`D-JACK-CLAMP`, `J-CV`, `R-OUT-PROT`, `R-OPAMP-IN`, `SW1-n`, `U-MCU-RT`,
`SKT-BREATH`, `HDR-DEV` — all in a `hardware/<board>/bom.csv`, correct by
construction) or is explained on the spot:

| placement | owner | reason given |
|---|---|---|
| `breath-receive-stage` places `R-SER-BREATH` | `interfaces/breath-sense-link` | "R-SER-BREATH IS NOT HERE. The 10k 0.1% pair is the MODULE-side series protection and module/breath-receive-stage places it" `[repo breath-sense-link/netlist.yaml:6-8]` |
| `carrier/carrier` places `R-SPI-SER`, `U-TVS-SPI` | `interfaces/spi-link` | `carrier/netlist.yaml` header; the carrier is the driving end |
| `digital-and-supervision` places `R-SPI-PULL` | `interfaces/spi-link` | the pulls are at the module, per the row `[repo]` |
| `interfaces/spi-link` places both `J-UMBILICAL` | `module/power-entry` | one connector per cable end; `spi-link` is the only circuit that sees both |
| `mod-channels` places 5 of `R-BIAS-DAC` | `module/pitch-stage` | "One of qty 6, one per populated DAC channel" `[repo pitch-stage/netlist.yaml]` |
| `key-marker-and-bits` places 3 of `R-KEY-PU` | `cluster/key-switch-network` | stated in both netlist headers; §2 above |
| `breath-excitation-reference`, `breath-adc` place `C-DECOUPLE-CARRIER` | `carrier/led-strip-drive` | **no reason given** — N7-13 |
| `breath-receive-stage` places both `R-BIAS-INAMP` | `module/pitch-stage` | **no reason given, and the owner places none** — N7-7 |

`foreign:` is a top-level key, not a member of `components:`, so the 22 foreign
declarations across 4 netlists are **correctly excluded from the instance sum**
`[repo check_global reads only spec["components"]]` `[test]` — no double
counting, and each one names its `owner` and `row`, both of which resolve
`[test]`.

---

## Summary of what is right, with the arithmetic

- `[calc]` `113 + 30 + 12 = 155` — the row census closes; `102 + 7 + 4 = 113`.
- `[calc]` `replicated: 21`: `6+6+4+5 = 21` key positions; `R-KEY-PU 21+3 = 24`;
  `32 − 21 − 8 = 3` free bits. `[test]` perturbation to 20 and 22 is caught in
  both directions on all four rows.
- `[calc]` `replicated: 4`: four devices, `U-KEYS 4/4`, `C-DECOUPLE-165 4/4`.
- `[calc]` `U-OPA-PITCH`: 10 netlisted halves, name for name against the row's
  own enumeration of ten.
- `[calc]` `R-PRECISION` `ceil(2/4) = 1`; `U-BUF` `ceil(2/2) = 1`.
- `[calc]` `J-CHAIN` `1+2+2+2+1 = 8`, matching `config/figures.yaml`
  `chain-connectors`.
- `[calc]` `C-DECOUPLE` `12+2+2+1+1+1 = 19`; `C-DECOUPLE-CARRIER` `1+2+1+1+1+2 = 8`.
  Both quantities are right; it is the placement that is short.
- `R-OPAMP-IN 6/7` is a real open question with its decision named.
- Nothing in `unplaced.csv` is placed by a netlist; no part is placed twice under
  different names; all 113 `of:` targets resolve and all declared values match.

## Fifteen findings, by where the fix lands

| | fix in | findings |
|---|---|---|
| netlists (add instances) | 3 | N7-1, N7-2 |
| `bom.csv` fragments (one field or row each) | 7 | N7-3, N7-4(b), N7-5, N7-6, N7-7, N7-11, N7-13 |
| netlist schema (`section:` pairing) | 1 | N7-4(a) — prerequisite for N7-8 |
| `tools/` (frozen; recorded only) | 3 | N7-8, N7-9, N7-10 |
| notes only, latent | 2 | N7-14, N7-15 |

**The pattern across them:** the instance arithmetic itself is almost entirely
correct — 102 rows exact, both `replicated:` factors right and provably checked,
every `of:` resolving. What is wrong is everywhere the model *stops*: the four
section-exempt rows, the twelve zero-placed rows, and the two undocumented
shortfalls. Three of the four highest-severity findings (N7-3, N7-4, N7-5) sit
inside rows the checker prints a number for and then declines to check, which is
also where the corpus contradicts itself — the exemption and the disagreement are
the same fact seen twice.
