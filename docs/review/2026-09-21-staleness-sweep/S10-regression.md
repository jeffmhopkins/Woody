# S10 — Regression audit of the 2026-09-21 fix batch

**Question:** for each fix applied today, did it land in every corpus document
that carried the old value or the old claim?

**Corpus audited:** `hardware/**`, `docs/decisions/**`, `config/**`,
`docs/reference/**`, `ROADMAP.md`, `README.md`, `firmware/README.md`.
Review, log and research directories were read for context and are not
reported on.

**Commits in scope:** `3040d43`, `b1142b4`, `efebba9`, `745af8c`.

**Result: 4 of 16 landed everywhere. 10 are partial. 2 introduced new
contradictions.** The recurring shape is unchanged: the fix lands in the page
being edited, and the *other* copy of the same number survives — three times
today in the very file the commit edited, and twice in text that names the file
it failed to update.

---

## Ranked findings

### 1. Umbilical pin map (change 5) — **PARTIAL**, and the survivor is a schematic net list

`carrier.md` §4 was corrected. `carrier.md` **§1**, the page's own top-level tail
drawing, still carries the superseded map:

```
hardware/controller/carrier.md:49-50
   │ J-UMB   1 BREATH   2 AGND   3 +12V   6 PWR_GND   4 MOSI   5 CS      │
   │         7 SCLK     8 DIG_GND                                        │
```

That is `MOSI`+`CS` on pair (4,5) with no return between them — the exact
failure the change exists to remove — drawn 480 lines above the corrected
version in the same file.

`docs/decisions/0004-cv-interface-module.md:84-85`, the "Revised conductor
budget" block, is also still the old pairing, in the same ADR whose pin table
below it was revised:

```
SCLK      / DIG_GND     SPI to the DAC, ~1 MHz
MOSI      / CS
```

Same ADR, `:44`: *"With real Cat5/6 each signal sits against a ground in its own
twisted pair."* The new §"Pin assignment" text at `:787` flags this sentence as
false — *"This ADR also asserted twice that … Its own table never did"* — but
leaves it standing, and under the new map it is still false (SCLK and MOSI share
a pair).

**Consequence:** a builder wiring from `carrier.md` §1 or from ADR 0004's budget
block builds the map the review computed a 1.9:1 margin for, on the one signal
whose corruption is sticky.

---

### 2. Response-shaper stage (change 14) — **INTRODUCED A NEW INCONSISTENCY** (op-amp capacity, insertion point, decoupling count)

The stage is drawn in `breath-output-stage.md` §4 and has four new BOM rows.
Nothing else in the corpus knows about it.

**(a) The op-amp package count is now claimed three different ways.**

- `hardware/bom.csv:83` adds `U-RESP,module,OPA2197IDR,…,1,open` — a **seventh**
  OPA2197 package, described as *"Response shaper: 1/2 shapes at /2 inverting,
  1/2 restores x2 inverting"*, i.e. the shaper *is* this package.
- `hardware/module/breath-output-stage.md:265` says the opposite: the shaper
  costs *"**Both remaining OPA2197 halves**"* of the existing six, and `:287-290`
  says the seventh package is what the *other* (A5 `POT-OFFSET`) finding needs.
- `hardware/bom.csv:13` (`U-OPA-PITCH`) still reads *"Six packages, twelve
  halves, TEN used… **TWO SPARE**"* — unchanged.
- `hardware/module/breath-output-stage.md:130-132`, two sections above §4 on the
  same page: *"Ten of twelve halves used across the module, two spare."*
- `docs/decisions/0006-cv-channel-allocation.md:552` still spends *"the last
  spare op-amp half in `U-OPA-PITCH`"* on the `VREFOUT` follower.

**(b) Two decoupling capacitors are missing from the BOM.**
`hardware/bom.csv:42` `C-DECOUPLE` is qty **19** and enumerates
*"6 x OPA2197 on +/-12V = 12, INA828 = 2, LM311 on +/-12V = 2, DAC8568 … "*.
With `U-RESP` fitted that is 7 packages = 14 caps, so the row should be 21.
(The enumeration also still itemises the deleted LM311 — see finding 10.)

**(c) The module rail drawing still lists six op-amps.**
`hardware/module/power-entry.md:16`: `│   OPA2197 ×6, INA828`.

**(d) The page's own main schematic contradicts §4's stated insertion point.**
§4 `:297-301` says the stage inserts *"between the in-amp and the gain
attenuator"*. The §1 circuit at `breath-output-stage.md:35` still shows the
in-amp feeding `POT-GAIN` directly:

```
   from the INA828
   0 … −4.7 V ──────[POT-GAIN 50k]────┤ +
```

Nothing in `breath-receive-stage.md` or ADR 0003 mentions a stage after the
in-amp either. The chain, as drawn anywhere outside §4, does not contain the
new stage.

**(e) The same node has two voltages on one page.** §1 `:23-24` gives the in-amp
output as **−4.69 V** at a hard blow and **−10.05 V** at sensor full scale; §4
`:191`, `:231`, `:243-244` uses **−9.94 V** / **4.64 V**. §4's figures match
`breath-receive-stage.md:175` and `bom.csv:58` (9.94 V span); §1's do not.

**(f) The headroom rule was not re-derived.** `:137-138` still says *"offset at
+5 V and gain at 4× puts a hard blow at +23 V"*. With up to 1.49× from the new
shaper at a hard blow (§4's own table) that combination is now ~+34 V, and the
"their sum has to fit in ±11.5 V" rule at `:143-144` is computed without it.

**(g) Commissioning order.** `ROADMAP.md:51` (E10) still reads *"in-amp receiver
with `REF` grounded, **gain/offset knobs**"* and a two-knob order; §3 `:155-157`
already calls the order three steps, and there are now three knobs.

Polarity is the one thing that is *self*-consistent: two inversions restore it,
and §4 flags at `:294-296` that the end-to-end chain has not been re-derived.
That flag is honest, but it is the only place the problem is recorded.

---

### 3. Load switch rebuild (change 3) — **PARTIAL**; the ADR that owns the decision is untouched

`power-entry.md` is fully rebuilt (47 mV, 0.940 A, foldback through the ramp,
~62 ms start, 150 ms timer target) and `C-TIMER-LOADSW` / `C-GATE-LOADSW` are
correct in `bom.csv`. Three documents still carry the superseded physics:

- `docs/decisions/0005-power-architecture.md:260` — section heading **"Set the
  limit at 1.0 A, and delete the polyfuse"**; `:262` *"**1.0 A, latch-off, with a
  programmed 50–100 ms ramp.**"*; `:274` *"**1.0 A sits between them**"*; `:217`
  *"See 'Set the limit at 1.0 A…'"*; `:282-283` *"It boots — in about **75 ms of
  constant-current start**"* against the rebuilt page's ~62 ms
  *current-limited* start. ADR 0005 nowhere records the 47 mV threshold, the
  240 mA foldback floor, or that every start begins in current limit.
- `hardware/bom.csv:63` (`R-ILIM`) — *"THE resistor that is the limit. **1.0A
  target.** The stated 0.9-1.13A window…"*
- `hardware/bom.csv:18` (`U-LOADSW`) — *"A **1.0A ramp** at ~6V mean for 75ms is
  ~6W and 0.45J… **Set the limit at 1.0A** with a programmed 50-100ms ramp."*

`bom.csv` was edited in the same commit; these two rows sit four and forty-five
rows from the ones that were changed.

**Consequence:** E6 sizes `R-ILIM` from a 1.0 A target that the drawing says is
0.940 A, and the ADR's boot analysis still rests on the 75 ms number the rebuild
replaced.

---

### 4. "20 cents of pitch bend" diode justification (change 13) — **PARTIAL**; three survivors, one of them a design-change justification

Corrected only in `power-entry.md:55-61` (*"0.15 µV = **0.00018 cents**"*). The
old figure — five orders of magnitude larger — still justifies parts and
decisions in three places:

- `hardware/bom.csv:36` (`D-REVPOL`, qty 3): *"instrument current then modulates
  its Vf by ~80mV, which is **~20 cents of breath-correlated pitch bend** and
  needs no ground path at all (ADR 0006)"*
- `docs/decisions/0004-cv-interface-module.md:300-302`: *"so it modulates that
  diode's forward voltage by ~80 mV — about **20 cents of breath-correlated
  pitch bend**, needing no ground path at all and visible by inspection of the
  diagram itself."*
- `docs/decisions/0006-cv-channel-allocation.md:562`, inside the error-budget
  table that drives two "free fixes":
  *"| **The module's analog rail and the umbilical feed share one 1N5817**, so
  instrument current modulates its V_f by ~80 mV | **~20 cents** |"*

ADR 0004 and `bom.csv` were both edited by the same commit.

**Consequence:** the largest *stated* dynamic pitch error in ADR 0006's budget is
a number the repo now believes is wrong by ~10^5, and it is the stated reason
`D-REVPOL` is qty 3.

---

### 5. `R-OUT-PROT` rating raised (change 11) — **PARTIAL**, and one schematic is two revisions behind

`hardware/bom.csv:41` now specifies **0.66–1 W** (ERJ-P08 class). The schematics
that name the rating were not updated:

- `hardware/module/pitch-stage.md:133`: *"| **R-OUT-PROT** | 1 kΩ 1 %, **1206
  ≥250 mW** | …"* — the pitch output is precisely the case the BOM says now
  rails the op-amp across this resistor.
- `hardware/module/breath-output-stage.md:127`: *"| **R-OUT-PROT** | 1 kΩ, 1206
  **≥500 mW** | Shared spec with the other five outputs |"*

Three documents, three different ratings, for one part the BOM calls *"the ONLY
part in the module at real risk from any jack fault"*.

---

### 6. Key timings 125 / 5.7 µs → 119.9 / 5.92 µs (change 9) — **PARTIAL**, including inside the edited file

Corrected at `cluster-boards.md:156-157`. Survivors:

- `docs/decisions/0001-mcu-and-board-partitioning.md:225-226`:
  *"| Release, τ = 2.2 kΩ × 47 nF | 103 µs; crosses `V_IH` at **125 µs** |"*
  *"| Press, τ = 100 Ω × 47 nF | 4.7 µs; crosses `V_IL` at **5.7 µs** — 44×
  inside the 250 µs scan |"*
  — immediately followed, at `:233`, by a note congratulating itself for having
  swept these very figures into `bom.csv`.
- `hardware/bom.csv:92` (`C-KEY`): *"Press crosses HC165's VIL (0.99V at 3.3V) in
  **~5.7us** … **44x margin** … Release crosses VIH (2.31V) at **~125us**."*
- `hardware/controller/cluster-boards.md:163` — seven lines below the corrected
  table, in the file the fix landed in: *"The **125 µs** release filter is half a
  scan period and costs nothing musically."*

---

### 7. `R-KEY-PU` 21 → 24 (change 8) — **PARTIAL**

`bom.csv:90` and `cluster-boards.md:430` are 24. `hardware/controller/carrier.md:406`
still reads:

```
   3V3  ───────[F-CHAIN, see below]─────────► 10  3V3     → 21 pull-ups,
```

`cluster-boards.md:354` names the file it did not fix: *"Its component table,
`bom.csv` and **`carrier.md`** all carried 21 pull-ups for exactly the 21 switch
positions… `R-KEY-PU` is now **qty 24**."* Two of the three were updated.

---

### 8. SPI series resistors → `R-SPI-SER`, 220 Ω → 100 Ω (change 6) — **PARTIAL**

`bom.csv:49` and `carrier.md:531-563, 768` are correct. ADR 0004, edited by the
same commit, still argues from the old refdes and the old value:

- `:69`: *"**`R-MOSI-SER` at 220 Ω** with ~200 pF of cable is a **3.6 MHz**
  corner…"*
- `:479`: *"**220 Ω in series on MOSI at the driving end.** Source termination on
  the one line that runs the full umbilical carrying data."*

`hardware/module/digital-and-supervision.md:223`, in its *Still open* list, also
still poses the resolved question: *"**`SCLK` has no series resistor and `MOSI`
does.** That is the wrong way round"*.

---

### 9. Panel 8HP → 10HP (change 15) — **PARTIAL**; both assertions the commit set out to retire survive

The dimensional change landed (README, ROADMAP:183, ADR 0004, ADR 0009,
`power-entry.md:79`, four BOM rows, `KNOB-BREATH` qty 3, ≤14 mm knobs, 97 mm
derivation). What did not land is the thing the commit message says it fixed —
ADR 0004's underived 107 mm figure, *"asserted twice"*. **Both assertions are
still there, unedited, in the file that now also derives 97 mm:**

- `docs/decisions/0004-cv-interface-module.md:500`: *"Plus a toggle on a panel
  already at **107 mm of ~110 mm usable**."*
- `:584-585`: *"…**two breath knobs**, then six jacks in two columns… Roughly
  **107 mm of ~110 mm usable height — full but workable**."*

`:584` is doubly stale: there are three knobs now. So ADR 0004 currently states
107 mm twice and 97 mm once, and describes both a two-knob and a three-knob
panel.

Two `8HP` phrases also survive on the exact lines the commit rewrote:

- `ROADMAP.md:53` (E12): *"10HP panel cut… etherCON braced to the PCB — good
  practice **at 8HP** rather than the structural necessity it was at 6HP."*
  (ADR 0004:693 says *"At 10HP this is good practice"*.)
- `ROADMAP.md:183`: *"…against a 50.50 mm 10HP panel … **Comfortable at 8HP**;
  the tail is now the tight one"*.

Minor: the commit message claims the *"16–20 mm knobs"* claim was withdrawn *"in
both places it appears"*; it appeared once in ADR 0004 (old `:646`) and once in
`KNOB-BREATH`, and both are handled. No survivor.

---

### 10. Watchdog / LM311 removal (change 2) — **PARTIAL**; the drawing is clean, five other documents are not

`digital-and-supervision.md`'s circuit, rail table and `C-DECOUPLE` are correct
(19), and `power-entry.md`'s LM311 rail reference and panel-LED section are
rewritten. The parts live on elsewhere — and in the redrawn file's own lower
half, which the single diff hunk never reached:

- `hardware/module/digital-and-supervision.md:175`, in the watchdog table:
  *"| Module powered, instrument off | `OE` gating | `OE` gating, unchanged |"*
  — directly contradicting `:75-78` of the same file, *"**`OE` gating is gone.**
  … `OE` is **tied low — permanently enabled**"*.
- Same file `:114-121`: the six-pulls argument still rests on *"**with `OE`
  disabled** the buffer's outputs are Hi-Z"*, a state that can no longer occur.
  `bom.csv:48` (`R-SPI-PULL`) carries the same justification.
- Same file, *Still open* `:206-237` — an entire list of open questions about
  deleted parts: *"**A power-on reset RC on the '123's own `CLR`**"*; *"The real
  gates are the **'123's** discharge `R_on`"*; *"**The presence tap point**,
  above. It needs the one-line change described and a corrected `R-PRESENCE`
  row"*; *"A config save that overruns 99 ms would assert `CLR` mid-note"*. The
  §"obvious way to get the link coverage back" at `:190-193` likewise still
  describes the presence comparator in the present tense.
- `hardware/module/mod-channels.md:217`: *"The PER|FORMER avoids this by
  disabling `CLR` entirely; **Woody cannot, because the watchdog is the whole
  answer to a processor two metres away**."* Also `:150`, `:215` (*"On a watchdog
  `CLR`…"*).
- `firmware/README.md:54`: *"When the module **watchdog asserts `CLR`**, every
  DAC channel including channel 7 goes to zero scale."*
- `ROADMAP.md:51` (E10): *"…confirm the breath jack parks quietly: **the
  watchdog has no authority over it** by design"*.
- `hardware/bom.csv:76` (`C-BULK-RAIL`): *"The +12V branch carries the LM317's
  divider, the DAC **and the comparator, about 22mA** against -12V's 10mA"* — the
  100 µF/47 µF split is sized on a current that includes a deleted part.
- `hardware/bom.csv:42` (`C-DECOUPLE`): the itemisation still reads *"… **LM311
  on +/-12V = 2** …"* and still sums to 21 while the quantity field says 19.

Note the drawing at `power-entry.md:15` shows `[C1 47µF]` on +12 V and `:273`
says *"Entry bulk is 4 × 47 µF"*, against `bom.csv:76`'s *"NOT 47uF on every
rail… 100uF on +12V"*. That mismatch predates today (`1752009`) but sits in the
section this batch rewrote.

---

### 11. Marker 6 → 8 bits, free 5 → 3 (change 16) — **PARTIAL**, inside `key-layout.yaml` itself

`spare_bits_marker: 8` / `spare_bits_free: 3` are correct, as are ADR 0001 and
`cluster-boards.md` §4. Nine lines above the corrected fields, in the same file:

```
config/key-layout.yaml:131
#   The 5 genuinely free bits are FLOATING CMOS INPUTS and must be pulled -
```

The file therefore says 3 free bits and 5 free bits on the same screen, and the
stale line is the one that states the pull-up requirement `R-KEY-PU` qty 24 was
sized from.

---

### 12. `R1b` / `R-ISO-REF` and the CMRR claim (change 4) — **PARTIAL** and **INTRODUCED A NEW INCONSISTENCY**

Both parts are now drawn in `carrier.md` §2, with the compensation requirement.
Three problems:

**(a) The "fifty times" claim was not corrected where it lives.** The commit
message says the receive page was corrected. It was not edited at all.
`hardware/module/breath-receive-stage.md:210` still reads:

> *"That is the **entire** 60 dB budget, spent by one unmatched resistor… The
> 0.1 % module-side parts buy 94 dB and this **throws away fifty times that**."*

`carrier.md:223-226` instead adds a note *about* that sentence — so the repo now
contains the wrong claim and a remote correction of it, which is the arrangement
this project keeps rediscovering.

**(b) New contradiction inside the added text.** `carrier.md:219`: *"the link
CMRR falls from **70.2 dB to 60.2 dB**"*, i.e. `R1b` buys 10 dB. Six lines later,
`:224-225`: *"the real floor is **73 dB** … so `R1b` buys about **13 dB**."* Both
lines were added by the same commit.

**(c) The compensation requirement reached no BOM row.** `carrier.md:235-246`
states that `R-ISO-REF` with feedback at `VS` — *"(in-loop, **as drawn**)"* — is
*"**still unstable**"* and needs a feedback zero (`R_F`·`C_F`) or an R–C snubber.
No such part exists: `grep` finds `C_F`/snubber only in that passage, and
`bom.csv:122` (`R-ISO-REF`) and `bom.csv:26` (`U-BUF`) still present the
resistor alone as the fix — *"**FIX IT INSIDE THE LOOP** - isolation resistor in
series with the output, feedback taken at the SENSOR PIN"*. The §2 drawing
depicts the configuration its own text calls unstable.

---

## Landed everywhere

- **1. `CLR` redrawn as a pull-up to AVDD.** `digital-and-supervision.md:42-47`
  matches `bom.csv:67` (`R-CLR-PU`), the bring-up pad is kept, and no other
  corpus document states a pull direction. (The stale `'123`/99 ms `CLR` prose in
  the same file is reported under finding 10, not here.)
- **7. `cluster-boards.md` §2 figure.** The switch leg now goes to GND, the
  caption matches, and the correction is dated in place. No other copy of that
  figure exists in the corpus — ADR 0001:216 describes the network in words only
  and is consistent.
- **10. `left_thumb` marker pair flipped.** `cluster-boards.md:320` reads
  `| left_thumb | D | 20 | **0** | | C | 21 | **1** |`, the pattern string
  `1 0 · 0 1 · 0 1 · 0 1` matches bit order, and ADR 0001 and
  `key-layout.yaml` defer to §4 for levels rather than duplicating them.
- **12. `F-CHAIN`, `U-TVS-CHAIN`, `R-CHAIN-SER` BOM rows.** `bom.csv:94-96`
  exist, quantities (3 / 1 / 1) match `carrier.md:398-410`, and the `proposed`
  status matches `carrier.md:755-757` and `bom.csv` `open`.

---

## Where the pattern concentrated today

Three fixes left a survivor **in the same file that was edited**: the 125 µs
release filter (`cluster-boards.md:163`), the old pin map (`carrier.md:49`), and
the 107 mm panel height (ADR 0004:500, :585). Two left a survivor in text that
**names the file it failed to update** (`cluster-boards.md:354` → `carrier.md`;
`b1142b4`'s own message → `breath-receive-stage.md`). And the largest single
gap is the one with no prior art in this repo at all: the response stage was
added to one page and one BOM block, and the module's op-amp count, decoupling
count, rail drawing, signal chain and headroom arithmetic were all left at six
packages and two knobs.
