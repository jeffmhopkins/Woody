# A6 — the key chain, finger to firmware

**Agent:** A6, cold (no prior review directory read).
**Slice:** KS-33 → RC network → 74HC165 → loom → carrier → firmware note decision.
**Date:** 2026-09-21. **Findings are node-indexed. Nothing was fixed.**

Provenance on every claim: `[repo] path:line`, `[calc]` with the arithmetic,
`[datasheet]` with document and page, `[from memory]`.

> **`tools/check-staleness.py` PASSES on this corpus** — *"PASS no live stale
> values | corpus 121 files | 5 unresolved (tracked)"* `[repo]`. **Every stale
> value in section A is live behind that PASS.** Seven of them are the
> documented failure: a forbidden pattern that matches one spelling of a value
> and misses another by a character or two.

---

## Summary

| | |
|---|---|
| Re-derived and **correct** | both crossing times, both conservative bounds, the threshold interpolation, the four-vendor table, the 8-bit marker allocation, the eight-position pinout, all four copies of the ADC-reference arithmetic, the `R-SER-TERM` divider, the `F-CHAIN` withdrawal argument |
| **Verified independently** | the `left_thumb` marker flip: reproduced exactly (D3) |
| **Stale, live, checker-blind** | 7 findings (A1–A7) |
| **Semantic, un-greppable** | 6 findings (B1–B6) |
| **Not reproducible** | 1 (D4) |

The two that would cost the most: **B1** (the debounce window is 20× shorter
than the switch's own published bounce, and two documents still say that bounce
is unpublished) and **A1** (`bom.csv` — the most-cited file here — tells the
reader the release is 93 µs and the press 5.7 µs, against a live 119.9 / 5.92).

---

# A. Stale values that are live, with the checker passing

## A1 — `R-KEY-SER`, `C-KEY`: `bom.csv` carries three superseded crossing times

**Node:** key input node (switch → `R-KEY-SER` → 74HC165 parallel input).

`[repo] hardware/cluster/key-switch-network/bom.csv:4` (`R-KEY-SER`):

> "press is ~1us (100R x 10nF) so it stays instant, release is ~93us (10k x
> 10nF) which is a free hardware debounce"

`[repo] hardware/cluster/key-switch-network/bom.csv:5` (`C-KEY`):

> "Press crosses HC165's VIL (0.99V at 3.3V) in ~5.7us … 44x margin against the
> 250us scan period. Release crosses VIH (2.31V) at ~125us."

Live values: `key-press-time` **5.92 µs**, `key-release-time` **119.9 µs**,
margin **42×** `[repo] config/figures.yaml`. Neither 10 kΩ nor 10 nF is fitted:
`R-KEY-PU` is 2k2 and `C-KEY` is 47 nF `[repo] same file, rows 3 and 5`.

Three things make this worse than an ordinary stale row:

1. **The `C-KEY` row quotes the *corrected* thresholds beside the *superseded*
   crossing times.** 0.99 V and 2.31 V are today's numbers; 5.7 µs and 125 µs
   are not derivable from them with the fitted parts. `[calc]` with
   V_IL = 0.99 V, τ = (2200∥100)×47 nF = 4.4957 µs, start 3.3 V, asymptote
   3.3×100/2300 = 0.1435 V: t = −4.4957·ln(0.8465/3.1565) = **5.92 µs**. The row
   is internally inconsistent, not merely old.
2. **"44x margin"** is consistent with 5.7 (250/5.7 = 43.9 `[calc]`) and
   inconsistent with the owner page's 42×. A derived number moved with the wrong
   parent.
3. **Both rows survive in the generated master.** `tools/merge-bom.py --check`
   reports *"checked 138 rows from 24 fragments | 0 problems"* `[repo]`, and the
   same text is at `hardware/bom.csv:35` and `:36`.

**Why the checker missed it.** `key-release-time.forbidden` contains
`"release ~93 us"`; the corpus spells it `~93us`. `key-press-time.forbidden`
contains ``"`V_IL` at **5.7"``; the corpus spells it `in ~5.7us`.
`key-release-time.forbidden` contains ``"`V_IH` at **125"``; the corpus spells
it `at ~125us`. Three misses, each by a space or a markup fragment — the
`sensor-full-scale` failure CLAUDE.md §2 describes, three more times.

## A2 — the owner page restates its own figure as the superseded value

**Node:** key input node.

`[repo] hardware/cluster/key-switch-network/key-switch-network.md:109`:

> "The **125 µs** release filter is half a scan period and costs nothing
> musically"

This is the *owner* of `key-release-time` `[repo] config/figures.yaml`, and 61
lines above it the same page states **119.9 µs** correctly, twice. `[calc]`
119.9/250 = 0.48 — the "half a scan period" reading is what the 125 was written
to support.

`key-release-time.false_positive_note` says a bare 125 µs *legitimately* means
the mean sampling period and the 8 kHz loop period `[repo] figures.yaml:159`.
That note is correct, and it is also the reason a reviewer scanning for 125
would wave this one through.

## A3 — the marker is still "six bits" on the carrier page

**Node:** marker straps.

`[repo] hardware/carrier/carrier.md:378-383`:

> "**Two items left this page with the registers.** The **marker pattern**
> (which six bits, to what levels) … They are now on
> `hardware/cluster/cluster-boards.md`, which proposes an answer to both."

`marker-bits` = **8 bits**, decided 2026-09-21 `[repo] config/figures.yaml`,
and stated as 8 in ADR 0001, `key-layout.yaml`, `key-marker-and-bits.md`,
`cluster-boards.md` and `key-chain-loom.md`. Three defects in one sentence:

- **six**, against a `forbidden` list carrying four other spellings of six
  (`"Four to six of the"`, `"4-6 are claimed"`, `"six bits carry the marker"`,
  `"**6 marker"`). This is a fifth.
- **"proposes"** — it is decided, and `cluster-boards.md:200-202` says so
  itself: *"The marker pattern is no longer among them"*.
- **the pointer is dead**: `cluster-boards.md` has no §4 any more
  `[repo] grep of its headings: 1, 41, 72, 104, 115, 146, 177, 200`. §4 is
  `hardware/cluster/key-marker-and-bits/key-marker-and-bits.md`.

## A4 — "15 passives" is 5 free bits × 3, and there are 3 free bits

**Node:** free bits 22, 23, 31.

`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:189-192`:

> "Giving the 3 free bits the full network too is now **15 passives** … under
> the tail topology it also needed **five more wires** down the body."

`[calc]` 3 bits × 3 passives = **9**; and since all three already carry an
`R-KEY-PU` (`key-pullup-qty` = 24 = 21 + 3 `[repo] figures.yaml`), the true
increment is **6** — `R-KEY-SER` and `C-KEY` each. 15 = 5 × 3 and "five more
wires" = 5 × 1: both are the superseded `free-bits` value of 5.

`free-bits.forbidden` carries `"five genuinely free"`, `"The 5 genuinely
free"`, `"5 free bits"`, `"Eight to ten remain"` — four spellings of the *value*
and none of its *products*. The sentence costing the decision is the one that
survived.

## A5 — "63 network passives" is 21 × 3, and `R-KEY-PU` went to 24

**Node:** `R-KEY-PU` / `R-KEY-SER` / `C-KEY`.

`[calc]` from the live BOM: `R-KEY-PU` 24 + `R-KEY-SER` 21 + `C-KEY` 21 =
**66**, or 70 with the four `C-DECOUPLE-165`. Six live corpus statements say 63:

| | |
|---|---|
| `hardware/cluster/cluster-boards.md:195` | "63 **network** passives" — unambiguous, and unambiguously 66 |
| `hardware/carrier/carrier.md:283` | "4 ICs and 63 passives moved to `PCB-CLUSTER`" |
| `docs/decisions/0001-…:138` | "+41 %: 4 ICs and 63 passives" (comparison table) |
| `docs/decisions/0001-…:162` | "added 4 ICs and 63 passives" |
| `docs/decisions/0013-two-mcu-split.md:241` | "keeps 4 ICs and 63 passives off a carrier" |

63 = 21 × 3, the pull-up count before the three free bits were budgeted. The
21→24 change landed in the `qty` column and in the prose explaining it
`[repo] bom.csv R-KEY-PU notes: "TWENTY-FOUR: one per switch position … PLUS
one each for the 3 genuinely free bits"` — and in no derived total anywhere.

`cluster-boards.md`'s per-board table is itself **correct** (`R-KEY-PU` 6/6/6/6
= 24, `R-KEY-SER` and `C-KEY` 5/4/6/6 = 21 `[calc]`); the total two lines below
it is not. The defect is inside one screen of the correct numbers.

## A6 — "one 8–11 way loom" against a decided 12

**Node:** `J-CHAIN` / the loom.

`[repo] hardware/carrier/carrier.md:350` and `:364`: "one **8–11 way** loom",
"one **8–11 way** key loom". `chain-conductors` = **12**
`[repo] config/figures.yaml`, and the table at `carrier.md:314-321` — in the
same section, 30 lines above — sums 4 + 5 + 1 + 2 = 12 `[calc]` and labels the
row "**Key loom, all four clusters, chained — `J-CHAIN` is 2×6** | **12**".

## A7 — "6-way or 10-way" is posed as open on a page that draws the 2×6

**Node:** `J-CHAIN`.

`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:138-140`:

> "**Six conductors is the signal count, not the conductor count.** Whether this
> connector is 6-way or 10-way is a decision this page cannot take alone — see
> *Still open*."

Decided: 2×6, 12-way, alternating ground, ADR 0001 fix 1, 2026-09-21 `[repo]
0001:249-256`. The same page draws the 12-way pinout at lines 88-113 and again
at 216-219, and its `J-CHAIN` BOM row records the decision. 10-way is not a live
candidate at all — the spares took it to 12. The sentence reads as a live open
question 50 lines below its own answer.

*(`chain-conductors.forbidden` carries `"six conductors per hop"`, `"SIX
conductors per hop"`, `"6 conductors per hop"`, `"Six conductors leave"`,
`"six conductors leave"` — five spellings, and this one is
`"Six conductors is the signal count"`.)*

---

# B. Semantic — what a grep cannot reach

## B1 — the debounce is 20× shorter than the switch's own published bounce

**Node:** key input node → firmware note decision. **This is the finding I
would act on first.**

**The bounce figure exists and is banked.** Gateron's vendor drawing
KS-33H10B050NN-Y24 Version 2 gives **bounce time 5 ms max at 16 in/sec**
`[datasheet GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf, quoted at
hardware/bom.csv PLATE-TOP row and ROADMAP.md:120]`.

**The only debounce window in an ADR is 250 µs.** `[repo] 0001:315-320`:

> "**Require two consecutive agreeing samples before a note-on.** At the 4 kHz
> loop rate that is **250 µs** of added latency … Note-*off* stays filtered as
> before."

`[calc]` 5 ms / 250 µs = **20×**. Nothing in the corpus compares the two.

**What that produces at the note level.** The hardware network is asymmetric in
the right direction but far too fast to cover it. `[calc]` an *open* interval
must exceed 119.9 µs before the node crosses `V_IH`, and a *close* is seen after
5.92 µs. So inside a 5 ms bounce burst, every open longer than ~120 µs
propagates, and each one is followed by a re-close seen 20× faster. On a
keyboard that is a retrigger. **Here fingerings are combinational** — ROADMAP
states it plainly: *"lifting a finger is how you start the next note"*
`[repo] ROADMAP.md:127`. So each chatter transition resolves to a **different
note**, not a repeat of the same one: a release that bounces walks the
fingering table through intermediate states for up to 5 ms. A player hears a
grace-note spray on legato, which is indistinguishable from a playing mistake —
the same diagnosis trap the marker pattern exists to close.

And ADR 0001 has already written down why it is unfiltered: *"Asymmetric
debounce fires on the first closed sample … so one corrupted 32-bit word becomes
one spurious note-on at full velocity, with no filtering. A conventional
symmetric 20 ms window would silently absorb it."* `[repo] 0001:194-197`. That
paragraph is about a corrupted *read*; the same sentence describes a bounced
*contact*, and the corpus never makes the second connection.

**Two documents still say the figure is unpublished.**

- `[repo] docs/decisions/0002-key-switches-and-mounting.md:217-218`: *"Contact
  bounce and the actuation/reset hysteresis gap, **which Gateron does not
  publish**."*
- `[repo] docs/reference/ks33-geometry.md:163-166`: *"**Not available anywhere,
  still needs a scope.** Contact bounce duration and the actuation/reset
  hysteresis gap. Gateron publishes travel and force but neither of these."*

ROADMAP already records the refutation — *"**Partly refuted 2026-09-21, now
that the vendor drawing is banked**: Gateron *does* publish a bounce figure —
**5 ms max at 16 in/sec**"* `[repo] ROADMAP.md:118-121]` — and it did not
propagate to either. The hysteresis gap genuinely **is** still unpublished, so
both sentences are half right, which is why they read as fine.

- `[repo] docs/reference/latency-budget.md:118` is a third: *"The 2021 firmware
  used a flat 20 ms debounce. **If these switches settle in 2 ms**, setting the
  window from data buys back 18 ms."* The vendor says 5 ms max. The measurement
  is still worth taking — 5 ms is a max at one actuation speed, and release
  bounce is not specified at all — but the row is written as though nothing were
  known.

**Related, same file.** `ks33-geometry.md` contradicts itself across 40 lines:
the header says Gateron's sources *"are unreachable from this project's
sandbox (the egress proxy rejects `gateron.com` and `gateron.co`)"*
`[repo] :7-9`, while the superseded block at `:44-46` says *"`gateron.com`
answers 200 from this sandbox for the first time"*. Its closing section still
says *"Drop the STEP into `mechanical/` when obtained"* `[repo] :175` — the STEP
is banked at `datasheets/mechanical/GATERON-KS-33-3D.step` `[repo]`. And its
**Published specification** table omits the operating force (50 ±15 gf), the
bounce time and the tightened cutout tolerance that the same repo's BOM row
already carries from that drawing.

## B2 — the key path has no total, and omits the two largest terms

**Node:** key path, end to end.

`[repo] docs/reference/latency-budget.md:93-101`. It is the only table on the
page with **no Total row**; both breath tables have one. As written it books
32 + 20 + 60 + 10 = **122 µs** `[calc]`. Two terms are missing:

- **the sampling period, 0–250 µs.** The breath digital table books it
  explicitly and explains why — *"It is not a conversion time — it is
  quantisation in *time*"* `[repo] :86-88]`. The key chain is read once per pass
  and pays exactly the same quantisation. Not booked.
- **ADR 0001's two-agreeing-samples gate, +250 µs.** Not booked — and worse,
  the table books the opposite: **"Debounce (press) | 0 — fire immediately"**
  `[repo] :97`. `firmware/README.md:25` agrees with the table
  (*"fire immediately on press"*); ADR 0001 requires a second sample. **Three
  documents, two answers, on the attack path the whole asymmetric-debounce
  argument exists to protect.**

`[calc]` worst case with both terms and the RC release:
119.9 + 250 + 32 + 250 + 20 + 60 + 10 = **741.9 µs**, six times the table.

**Does the key path close? (slice question 6.)**

- **Inside the loop:** yes, and comfortably. The chain read is 32 µs of a
  148–155 µs bus time inside `loop-budget`'s 196–241 µs of 250 µs
  `[repo] figures.yaml]`; `[calc]` 32 bits at 1 MHz = 32 µs, 32/250 = 12.8 %,
  matching ADR 0001's "about 13 %" `[repo] 0001:373]`.
- **Against the 5 ms target:** yes **as specified** — 0.74 ms worst case, ~6.7×
  margin — **but only because the release window is unbooked.** The release is
  entered as the single word *"filtered"*. Size it from the only published
  bounce number and the release path alone is 5 ms + ~0.5 ms, which **exceeds
  the page's own 5 ms gesture-to-output target**, on the path ROADMAP identifies
  as the critical one. ROADMAP knows this — *"A 10 ms release window delays that
  new note by 10 ms, landing squarely in the territory the attack-latency work
  exists to protect"* `[repo] ROADMAP.md:129-131]` — and `latency-budget.md`,
  the page whose whole job is this, does not carry the term.

**The budget's own stated purpose is to catch exactly this**: *"it is the thing
most likely to be violated accidentally by a change that looks harmless"*
`[repo] :4-6]`. An unbooked term is not even a change.

## B3 — "scan faster if bounce demands it" is backwards

**Node:** SPI3 / chain scan rate.

`[repo] 0001:317-319`:

> "(The chain now has its own SPI host, so it *could* be scanned faster than the
> output loop if the measurement at M1 says bounce demands it.)"

The debounce rule in the same paragraph is *N = 2 consecutive agreeing samples*.
`[calc]` the rejected-glitch width is (N−1)/f_scan: 250 µs at 4 kHz, **125 µs at
8 kHz**. Scanning faster **shortens** the window, so it rejects *less* bounce,
not more. To cover a longer bounce you need more samples, and that costs latency
whatever the scan rate. As written the parenthetical offers a remedy that moves
the wrong way, on the one lever the ADR names for handling M1's result.

*(A faster scan is still worth having — it decouples key latency from the DAC
loop period, which is the 0–250 µs term B2 says is unbooked. That is a different
benefit from the one stated.)*

## B4 — the loom's 3V3 protection covers the wrong failure mode

**Node:** `J-CHAIN` pin 10 (3V3), `F-CHAIN`, `U-TVS-CHAIN`.

The stated hazard: *"The 3V3 conductor leaves this board, runs 265 mm through a
bonded body **next to 12 V LED power**, and comes back as nothing"*
`[repo] key-chain-loom.md:143-146`. Two parts are proposed:

- `U-TVS-CHAIN`, a **4-channel** array — *"ESD protection on the key chain
  signals"*, qty 1 `[repo] key-chain-loom/bom.csv:4`. Four channels covers
  `SCK`, `SH/LD`, `SER`, `QH`. **Not 3V3.**
- `F-CHAIN`, a 100 mA polyfuse on 3V3 `[repo] same file:5`.

A 12 V short onto pin 10 is a **voltage** fault. A polyfuse limits current and
does not clamp voltage, and 12 V through 24 × 2.2 kΩ is `[calc]` 131 mA — above
`Ihold` 0.10 A but below `Itrip` 0.30 A, so it may sit there indefinitely. It
lands on four 74HC165 VCC pins with an absolute-maximum supply of 7 V
`[from memory: 74HC family abs max VCC]`, on 24 pull-ups, and on the dev board's
LDO output. **Nothing in the corpus clamps the one conductor whose named failure
mode is a short to a higher rail.** A fifth TVS channel, or a 3V3 clamp at the
cluster end, is the obvious answer and is not proposed anywhere.

**Separately, the `F-CHAIN` row's own analysis is sound and I verified it.** It
withdraws the series-resistance objection because *"the 74HC165's thresholds and
the key pull-ups sit on the SAME rail, so the RC crossing time is independent of
VCC"* `[repo] key-chain-loom/bom.csv:5`. `[calc]` confirmed: with node start
V·100/2300, asymptote V, threshold 0.70·V, t = −τ·ln((V−0.7V)/(V−0.0435V)) =
−τ·ln(0.3136) — V cancels. Correct, and worth keeping.

## B5 — keying does not prevent the `QH`-against-`QH` mis-plug

**Node:** `J-CHAIN` pin 8, at every board that carries both IN and OUT.

*"Same 2×6 pinout at all eight positions, boxed and keyed at every one"*
`[repo] key-chain-loom.md:44`; the stated reason is *"a reversed connector puts
3V3 onto the `QH` net"* `[repo] :215`. Keying stops a 180° reversal. It does not
stop plugging a ribbon into a board's **OUT** where **IN** was meant — three of
the five boards carry both, they are the same part with the same key, and the
page itself says pin 8 *"carries a different net on each side of the board"*
`[repo] :244-246`.

Swap them and pin 8 puts **this board's `QH` against the neighbour's `QH`** —
two totem-pole outputs, permanently driven, in contention. That is precisely the
fault ADR 0001 uses to justify giving the chain its own SPI host: *"`QH` on a
74x165 — any family — is a permanently driven totem-pole output with no
output-enable pin … two push-pull drivers would fight continuously"*
`[repo] 0001:107-111`. The corpus reasons carefully about this hazard on the
bus and not at all on the connector that can create it by hand, in a body that
bonds shut. Cheapest answers: different key positions or shroud polarities for
IN and OUT, or a silkscreen convention — both free at layout, neither
retrofittable.

## B6 — the live 2.2 k / 10 k trade is priced with the superseded capacitor

**Node:** `R-KEY-PU`. This is the circuit's only open electrical decision.

`[repo] hardware/cluster/key-switch-network/key-switch-network.md:128-129`:

> "Going back to 10 kΩ would cut that to 5.9 mA and 0.7 LSB, **at the price of a
> 100 µs τ** in a humid cavity."

`[calc]` with the fitted `C-KEY` = 47 nF, 10 kΩ gives **τ = 470 µs**, and the
release crossing becomes 470 × 1.1594 = **545 µs** — more than **two** 250 µs
scan periods, against 119.9 µs today. 100 µs is 10 kΩ × 10 nF, the superseded
pair that A1's BOM rows also still carry.

So the recorded trade understates the cost of the alternative **4.7×**, and it
understates it in the direction that makes the alternative look attractive: the
current τ is 103.4 µs, so "the price" as written is roughly *what is already
being paid*. The same sentence is repeated at `:140-142` in *Still open*. The
5.9 mA and 0.7 LSB halves are both correct `[calc]` 3.3/(10100) × 18 = 5.88 mA;
5.88 × 0.3/100 = 0.0176 % × 4096 = 0.72 LSB.

---

# C. Provenance — which document each threshold comes from

## C1 — the thresholds are sound, and I re-derived every number

**Node:** 74HC165 parallel input, `V_IH` / `V_IL` at 3.3 V.

Checked against the banked manifest rather than the pages:

| Vendor | Banked file | 2.0 V | 3.0 V | 4.5 V | 6.0 V |
|---|---|---|---|---|---|
| TI SCLS116E | `logic/74HC165-ti-scls116e.pdf` | 1.5 / 0.5 | *absent* | 3.15 / 1.35 | 4.2 / 1.8 |
| Nexperia Rev. 8 | `logic/74HC165-nexperia.pdf` | 1.5 / 0.5 | *absent* | 3.15 / 1.35 | 4.2 / 1.8 |
| Toshiba 1986 | `logic/74HC165-toshiba-1986-excerpt.pdf` | 1.5 / 0.5 | *absent* | 3.15 / 1.35 | 4.2 / 1.8 |
| **onsemi MC74HC165A/D Rev. 13** | `logic/74HC165-onsemi.pdf` | 1.5 / 0.5 | **2.1 / 0.9** | 3.15 / 1.35 | 4.2 / 1.8 |

`[datasheet MANIFEST.csv rows 59–62]`, each row stating the page it was read
from: onsemi *"DC ELECTRICAL CHARACTERISTICS p.4 has VCC columns 2.0 / 3.0 / 4.5
/ 6.0 V, and the 3.0 V row reads VIH min = 2.1 V and VIL max = 0.9 V"*; Nexperia
*"Table 6 … p.6 … VCC = 2.0 / 4.5 / 6.0 V ONLY"*.

`[calc]` interpolating in absolute volts between onsemi's 3.0 V and 4.5 V rows:
`V_IH`(3.3) = 2.1 + 0.2×(3.15−2.1) = **2.31 V**; `V_IL`(3.3) = 0.9 + 0.2×
(1.35−0.9) = **0.99 V**. Both land exactly on 0.70/0.30 × 3.3. The bracketing
argument holds and needs no extrapolation through the 2 V point.

`[calc]` crossing times, pressed node = 3.3 × 100/2300 = 0.1435 V:

| | |
|---|---|
| Release, τ = 2200 × 47n = 103.40 µs | −103.40·ln(0.99/3.1565) = **119.88 µs** ✓ |
| Press, τ = (2200∥100) × 47n = 4.4957 µs | −4.4957·ln(0.8465/3.1565) = **5.918 µs** ✓ |
| TI-only bound `V_IH` 2.475 V | 103.40 × 1.3420 = **138.76 µs** ✓ |
| TI-only bound `V_IL` 0.825 V | 4.4957 × 1.5330 = **6.892 µs** ✓ |
| Margin | 250/5.92 = **42.2×**; 250/6.89 = **36.3×** ✓ |
| Pole | 1/(2π×103.40 µs) = **1539 Hz** ✓; 20·log₁₀(800k/1539) = **54.3 dB** ✓ |

**Every figure in the owner page's derivation block reproduces.** The correction
history it records — 0.75/0.25 taken off a row TI does not have, then put back —
is accurate, and the page is honest about which document gave which number.
This is the strongest-documented value in the slice.

Two provenance defects remain on it:

- **`74HC165-toshiba.pdf` does not exist.**
  `[repo] key-switch-network.md:61` cites it; the banked file is
  `74HC165-toshiba-1986-excerpt.pdf` `[repo] ls datasheets/logic/`. And
  `F-CHAIN`'s own note claims its 2026-09-21 path fix made it *"the only
  dangling `datasheets/` path in the whole corpus"* `[repo]
  key-chain-loom/bom.csv:5` — that claim is **false**, and it is false about
  this slice.
- **The weakest of the four vendors carries none of its caveats.** The manifest
  is emphatic: the Toshiba file is an **OCR'd 1986 excerpt** documenting
  **TC74HC165P/F**, *"NOT the modern TC74HC165AP"*, six pages cut from a 675-page
  databook `[datasheet MANIFEST.csv row 62]`. The page presents it as a plain
  fourth vendor. Since four-vendor agreement is the *entire* argument for
  transferring onsemi's 3.0 V row to whatever part is fitted (`U-KEYS`
  manufacturer is "multiple" `[repo] bom.csv`), the caveat is load-bearing.

## C2 — the ADC-reference derivation: four copies, and its weak link is banked

**Node:** `J-CHAIN` pin 10 (3V3) = MCP3202 `VDD`/`VREF`. (Slice question 5.)

`key-scan-current.companion` says the consequences are stated in **two** places
`[repo] figures.yaml:131`. There are **four** live copies:

| | |
|---|---|
| `hardware/carrier/carrier.md:170-181` and `:372-376` | the claimed owner |
| `hardware/interfaces/key-chain-loom/key-chain-loom.md:113-131` | full copy |
| `hardware/cluster/key-switch-network/key-switch-network.md:105,126-129` | full copy |
| `docs/decisions/0001-…:227-241` | full copy — **not named in the companion note at all** |

**All four agree, and all the arithmetic is right.** `[calc]`
3.3/(2200+100) = 1.4348 mA → 1.43 ✓; ×18 = 25.83 → 25.8 ✓; 25.8 mA × 0.3 %/100 mA
= 0.0774 % → 0.077 ✓; 0.077 % × 4096 (MCP3202 is 12-bit) = 3.17 → 3.2 LSB ✓;
3.2/1594 = 0.201 % → 0.2 % ✓; 25.8/5.88 = 4.39 → "4.4×" ✓.

Three findings on it:

1. **`key-chain-loom.md` contradicts itself about who owns it.** Its Interfaces
   table says the argument *"is owned by neither end and stayed in `carrier.md`
   §2"* `[repo] :34`, and 80 lines later the same page carries a complete copy
   `[repo] :113-131`. `figures.yaml`'s own `escape_note` predicted this shape —
   *"carrier.md also claims sole ownership of the argument … while
   key-chain-loom.md carries an equally complete copy"* — and the count has
   since grown to four.
2. **The whole chain rests on `[from memory]`, and the datasheet is in the
   repo.** All four copies say *"at an LDO load regulation of ~0.3 % per 100 mA
   `[from memory]`"*. The part is **identified**: `ME6217C33M5G`, and the
   manifest names it *"The 3V3 LDO on the Waveshare ESP32-S3-Matrix, fed from
   net VCC_5V … so everything on the board's 3V3 rail sits behind it"*, banked
   at `datasheets/discrete-and-power/ME6217C33M5G.pdf`, *"ME6217 series
   datasheet V05, 13 pp; the exact ordering code ME6217C33M5G appears in the
   p.2 selection guide"* `[datasheet MANIFEST.csv row 44]`. CLAUDE.md §3 is
   exactly on point: *"A number read off a banked document beats one from a
   review."* **This is the single highest-value follow-up in the slice**: 0.3 %
   per 100 mA is the multiplier for 3.2 LSB, which is quoted in four files and
   accepted as a live trade on the carrier page. *(I did not read it — no
   `pdftotext` in this environment — so I assert no value, only that the
   document is present and the figure is not taken from it.)*
3. **The 3.2 LSB conclusion is a gain error, and the pages say so correctly** —
   *"it is the *reference* moving, so it scales the reading rather than
   offsetting it"* `[repo] key-chain-loom.md:127-128`. Correct, and the reason
   the symptom is hard to diagnose. Worth keeping in whichever single copy
   survives deduplication.

---

# D. The marker pattern (slice question 3)

## D1 — the allocation adds up. Verified against four documents.

`[calc]` from `key-marker-and-bits.md:47-53`:

| Device | Bits | fitted | reserved | marker | free |
|---|---|---|---|---|---|
| `right_thumb` | 0–7 | 3 | 3 | 2 | 0 |
| `right_hand` | 8–15 | 6 | 0 | 2 | 0 |
| `left_thumb` | 16–23 | 4 | 0 | 2 | 2 |
| `left_hand` | 24–31 | 5 | 0 | 2 | 1 |
| **total** | **32** | **18** | **3** | **8** | **3** |

Agrees with `marker-bits` 8 and `free-bits` 3 `[repo] figures.yaml`; with
`key-layout.yaml`'s `spare_bits: 14`, `spare_bits_marker: 8`,
`spare_bits_switches: 3`, `spare_bits_free: 3` and its per-cluster comments
(5 + 2 + 4 + 3 = 14 spare `[calc]`); with `counts.total: 18`; and with
`cluster-boards.md`'s per-board `R-KEY-PU` 6/6/6/6 = 24 and `R-KEY-SER`/`C-KEY`
5/4/6/6 = 21 `[calc]`.

Bit numbers in the levels table `[repo] :71-77]` all check against `H`=0 … `A`=7
per device: RT `B`=6, `A`=7; RH `B`=14, `A`=15; LT `D`=20, `C`=21; LH `C`=29,
`B`=30. Read ascending, `1 0 · 0 1 · 0 1 · 0 1` ✓ `[calc]`.

## D2 — the free bits are genuinely free

22 and 23 (`left_thumb` `B`, `A`) and 31 (`left_hand` `A`) `[repo] :95-97]` are
not markers, not switch positions, not reserved. Each carries an `R-KEY-PU` and
nothing else, and `key-pullup-qty` = 24 = 21 + 3 accounts for all three
`[repo] figures.yaml, bom.csv R-KEY-PU]`. **Correct, and correctly separated**
from the three *reserved* positions, which are the retrofittable ones because
they get plate cutouts. That distinction is the load-bearing part of the 6→8
argument and it is made cleanly.

## D3 — VERIFIED INDEPENDENTLY: the `left_thumb` flip

`[repo] hardware/cluster/key-marker-and-bits/notes.md:25-35` claims that with the
pre-flip pattern `1 0 · 0 1 · 1 0 · 0 1`, *"of the **23 wrong chain permutations
exactly one passes undetected: `RT → RH → LH → LT`**"*, that *"it passes whenever
`LH5` is released"*, and that flipping one pair *"kills all 23 permutations"*.

I re-solved this from the live tables as a constraint problem over all 24
orderings, modelling each device's markers at its own local inputs, free bits as
pulled high, switch bits as free variables `[calc]`:

| pattern | wrong permutations that can pass undetected |
|---|---|
| pre-flip (`left_thumb` = `D`:1, `C`:0) | **1** — `RT → RH → LH → LT`, requiring `LH` local input `D` = 1 |
| live (`left_thumb` = `D`:0, `C`:1) | **0** of 23 |

`LH` local `D` is bit 28 = **`LH5`** `[repo] :52]`. **Reproduces the claim
exactly, including which key and which direction.** Recorded as verified — the
flip does what notes.md says, and the two straps are earned.

## D4 — NOT REPRODUCIBLE: "passes at 11 of 31 reload points"

`[repo] key-marker-and-bits.md:90`: *"A mid-shift `SH/LD` reload passes at 11 of
31 reload points."*

Modelling a reload after *r* clocks as `received[i] = b[i]` for `i < r` and
`b[i−r]` for `i ≥ r` — which follows from the chain re-loading every device
simultaneously — and checking only the eight marker positions `[calc]`:

| reading | result |
|---|---|
| reload points undetectable for **at least one** key state | **22** of 31 (free bits high) / 23 (free bits variable) |
| for a **given** key state, worst case over all 2²¹ states (exhaustive) | **12** |
| mean over key states | **≈ 4.6** |
| with no keys pressed | **3** (r = 22, 30, 31) |
| with all keys pressed | **2** (r = 24, 31) |

**No model I could construct yields 11.** The nearest is the exhaustive worst
case, 12. Either the figure is off by one, or it rests on an assumption the page
does not state.

This is a **claim to check, not a confirmed error** — I may not have the
author's model. But the page should carry the model either way, because the
readings differ by 7×: "12 of 31, while this particular chord is held" and
"3 of 31 at rest" are different engineering statements, and the bare number
reads as neither.

## D5 — "the 24 bits that carry the music" is the wrong noun

`[repo] :88-90]`. The arithmetic is right: 8 of 32 caught, `[calc]` 32/8 = 4×
undercount. But of those 24 non-marker bits, **18** are fitted switches; 3 are
unfitted reserved positions and 3 are free bits that carry nothing at all. Music
today is 18 bits. The 4× figure stands; the sentence overstates what is exposed.

## D6 — the marker's honest limits are stated, and they are correct

*"the straps go direct to the rails, so they share no component with the 21 key
networks they are read as vouching for"* `[repo] :91-93]`, and ADR 0001's *"It
is a framing check, not an error-detecting code"* `[repo] 0001:339]`. Both true
and both worth keeping — this is the part of the marker argument that survives
scrutiny best.

---

# E. The loom (slice question 4)

## E1 — the pinout agrees at all eight positions. Checked, agrees.

| source | pinout |
|---|---|
| carrier end drawing `[repo] key-chain-loom.md:88-100]` | 1 GND, 2 SCK, 3 GND, 4 SH/LD, 5 GND, 6 SER, 7 GND, 8 QH, 9 GND, 10 3V3, 11–12 spare |
| cluster end `[repo] :216-219]` | identical |
| `J-CHAIN` BOM row `[repo] key-chain-loom/bom.csv:2]` | identical |
| ADR 0001 fix 1 `[repo] 0001:250-252]` | identical |

`[calc]` 4 signals + 5 GND + 3V3 + 2 spare = **12** = `chain-conductors` ✓.
Every signal is flanked by ground; 3V3 at pin 10 sits against pin 9's ground ✓
(a standard 2×N IDC maps ribbon conductor *n* to pin *n*, so ribbon adjacency
follows pin order `[from memory]`).

`[calc]` connectors: LH 1 + LT 2 + RH 2 + RT 2 = 7, + carrier 1 = **8** =
`chain-connectors` ✓, matching `cluster-boards.md:194-196` and the `J-CHAIN` qty
of 8.

The bus/point-to-point split is consistent end to end: `SCK`, `SH/LD`, `3V3` and
the five grounds straight through IN→OUT; `SER` a pass-through on pin 6 to the
chain-end board; `QH` a different net on each side of pin 8, which is what
forces the second connector. `LK-SER` position A/B reconciles with `LH` having
IN only ✓.

## E2 — `R-SER-TERM` divider checks out

`[calc]` 3.3 × 100/(10000+100) = **32.7 mV** — the page's *"within 33 mV of the
rail"* `[repo] :271-273]` ✓.

## E3 — three parts are described as "not in the BOM" and have BOM rows

`[repo] key-chain-loom.md:146`: *"**`F-CHAIN`** … **Proposed, not in the
BOM.**"* It has a row: `hardware/interfaces/key-chain-loom/bom.csv:5`, status
`open`. Same for `U-TVS-CHAIN` (`:4`) and `R-CHAIN-SER` (`:3`), each of whose
notes records *"PROPOSED by carrier.md and never given a row until
2026-09-21"*. The rows landed; the prose that said they had not did not move.

Minor, same node: the carrier-end drawing marks `R-CHAIN-SER` `** R PROPOSED **`
on `SCK` and `SH/LD` and **not** on `SER` `[repo] :92-96]`, though one BOM row
of qty 3 covers all three.

## E4 — the reader of the schematic page never learns the `F-CHAIN` objection

The `F-CHAIN` BOM row carries a full analysis ending *"**RE-OPEN THIS
DECISION**: either a much lower-resistance part, or accept the unfused
conductor, or move the protection to the source end"* — because the banked
Bourns MF-PSMF010X has 1.0–7.5 Ω `[datasheet MF-PSMF010X-polyfuse.pdf, quoted
at key-chain-loom/bom.csv:5]`. `key-chain-loom.md:143-146` presents it as a
plain proposal — *"A 100 mA polyfuse or a 0603 fuse is two millimetres of
board"* — with no hint that the investigated part fails and the decision is
re-opened. It also says **0603** where the row says **0805**.

---

# F. Cross-references in the corpus that no longer resolve

All five are in live corpus files (not `docs/review`, `docs/log` or
`docs/research`), so CLAUDE.md §6's "do not correct historical paths" does not
cover them.

| where | points at | should be |
|---|---|---|
| `config/key-layout.yaml:130` | `cluster-boards.md` **section 4** | `hardware/cluster/key-marker-and-bits/key-marker-and-bits.md` |
| `docs/decisions/0001-…:227` | `cluster-boards.md` for the vendor-threshold argument | `hardware/cluster/key-switch-network/key-switch-network.md` |
| `hardware/carrier/carrier.md:382-383` | `cluster-boards.md`, "which proposes an answer to both" | same, and it is decided not proposed (A3) |
| `key-switch-network.md:61` | `74HC165-toshiba.pdf` | `74HC165-toshiba-1986-excerpt.pdf` (C1) |

**And the map that is supposed to resolve these is itself stale.**
`docs/reference/path-map-2026-09-21.csv` — a corpus file, and the one
CLAUDE.md §6 routes readers to — lists
`datasheets/other-semi/74HC165-{nexperia,onsemi,toshiba}.pdf` as **`unmoved`**
`[repo] :79-81]`, with the note *"datasheets/ moves whole or not at all"*. Those
paths do not exist; the files are under `datasheets/logic/`. `[calc]` 22
`datasheets/` paths in the corpus resolve to nothing, and every one of them is
in the `other-semi/` or `texas-instruments/` shape the map calls unmoved. A
reader chasing a stale datasheet path through the map is told the path is
current and still finds nothing.

---

# G. Circuit-graph edges this slice's pages do not declare

The `circuit.yaml` header warns that the graph is seeded from co-mention and
unverified, so these are a known class. Two are worth raising anyway, because
the header's stated purpose is *"catch[ing] a dependency on a deleted part"*:

- **`cluster/key-register/circuit.yaml` does not declare `refdes:U-KEYS`.** The
  74HC165 is the circuit's entire subject. It declares `C-DECOUPLE-165` and
  `LK-SER` only, and no `refdes:J-CHAIN` although the page names its pins 8 and
  10.
- **`cluster/key-switch-network/circuit.yaml` does not declare
  `fig:key-scan-current`**, although `figures.yaml` names that page as the
  figure's **owner**. `key-chain-loom`'s does not declare it either, although it
  restates the whole derivation (C2).
- `cluster/key-marker-and-bits/circuit.yaml` declares no `adr:0001`, though the
  page cites it five times.

---

# H. Why the checker passed, and the one change that would fix it

`.staleness/report.txt` lists seven figures whose owner it *cannot* verify.
**Five are this slice's**: `marker-bits` "8 bits", `free-bits` "3",
`chain-conductors` "12", `chain-connectors` "8", `key-pullup-qty` "24" — each
*"has no token distinctive enough to locate"* `[repo]`.

That blind spot is not incidental to A4 and A5; it **is** them. A small integer
has no distinctive spelling, so neither the value nor a statement derived from
it can be matched. But the **product** is distinctive:

| figure | moved | the derived product that did not move |
|---|---|---|
| `key-pullup-qty` 21 → 24 | ×3 passives | **63** should be 66 — six live statements (A5) |
| `free-bits` 5 → 3 | ×3 passives, ×1 wire | **15 passives**, **five more wires** (A4) |

**Recommendation: for a small-integer figure, put its derived products in
`forbidden`, not its value.** `63 passives`, `15 passives`, `five more wires`
are greppable where `21` and `5` are not. That converts the checker's weakest
figures into its strongest ones.

Separately, three `forbidden` lists are one spelling short — A1 (`~93us`,
`~5.7us`, `~125us` against patterns written with a space and with markdown), A3
(`(which six bits`), A7 (`Six conductors is the signal count`). By the corpus's
own count that makes these the **fifth through eighth** recorded instances of a
forbidden pattern missing a different formatting of the same value
`[repo] figures.yaml umbilical-pinmap.false_positive_note_2: "Fourth time a
forbidden pattern has missed a different formatting of the same value"]`.

---

# Ranked

| # | Node | Finding | Why it ranks here |
|---|---|---|---|
| 1 | key input → note decision | **B1** debounce 250 µs vs published bounce 5 ms max; two documents still call the figure unpublished | Unretrofittable in firmware terms only, but it decides what the instrument *sounds like* on every legato release |
| 2 | `R-KEY-SER`, `C-KEY` | **A1** `bom.csv` gives 93 µs / 5.7 µs / 44× against 119.9 / 5.92 / 42× | Most-read file; contradicts two documents that are right |
| 3 | 3V3 / MCP3202 `VREF` | **C2** four copies, and the multiplier is `[from memory]` with its datasheet banked | CLAUDE.md §3 exactly; one read settles a figure quoted four times |
| 4 | key path | **B2** no total, sampling period and the 2-sample gate unbooked, press debounce contradicted across three files | The page exists to prevent this |
| 5 | `R-KEY-PU` | **B6** the open 10 kΩ trade priced with the superseded capacitor, 4.7× low | The only live electrical decision here, priced wrong |
| 6 | `J-CHAIN` pin 10 | **B4** nothing clamps the one conductor whose named hazard is a 12 V short | Unretrofittable; a fifth TVS channel is free now |
| 7 | `J-CHAIN` pin 8 | **B5** keying does not stop IN/OUT mis-plug → `QH` against `QH` | Unretrofittable; free at layout |
| 8 | marker straps | **A3** "which six bits", + dead pointer, + "proposes" | Three defects in one sentence, on a decided figure |
| 9 | `R-KEY-PU` etc. | **A5** "63 network passives" ×6 | Straight arithmetic, six files |
| 10 | free bits | **A4** "15 passives", "five more wires" | Miscosts the retrofit option 2.5× |
| 11 | `J-CHAIN` | **A6**, **A7** 8–11 way and "6-way or 10-way" against a decided 12 | Both contradict a drawing on their own page |
| 12 | key input node | **A2** owner page restates 125 µs | Owner contradicting itself |
| 13 | marker | **D4** "11 of 31" not reproducible (my enumeration: 12 worst case, ~4.6 mean, 3 at rest) | Claim to check, not yet a defect |
| 14 | SPI3 | **B3** "scan faster if bounce demands it" is backwards | Wrong remedy for M1's result |
| 15 | various | **E3**, **E4**, **F**, **G**, **D5** | Housekeeping, but F's path map misleads the reader who is doing the right thing |

**Verified and correct, recorded so the next reviewer need not redo it:** the
threshold interpolation and all four crossing times (C1); the 8/3/21/18
allocation across four documents (D1); the `left_thumb` marker flip, reproduced
exactly including `LH5` (D3); the eight-position pinout (E1); the
`R-SER-TERM` divider (E2); all four copies of the ADC-reference arithmetic (C2);
the `F-CHAIN` VCC-independence argument (B4).
