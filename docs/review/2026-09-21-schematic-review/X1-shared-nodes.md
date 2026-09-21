# X1 — Shared nodes, rails and parts across the five module pages

**Scope.** Not any one page. Every node, rail, part or signal that appears on
more than one page, or that one page creates and another consumes. Indexed by
node. Single-page faults are left to the single-page reviewers except where a
second page depends on them.

**Evidence markers.** `[repo]` = read in this repository, file and line given.
`[calc]` = arithmetic shown in full. `[from memory]` = general engineering
knowledge, unverified here. Vendor domains were proxy-blocked, so no datasheet
figure is asserted; where one is needed the gap is named as a gap.

**Sources read in full:** the five pages in `hardware/module/`, `hardware/bom.csv`,
ADRs 0003/0004/0005/0006/0014, `ROADMAP.md`, `firmware/README.md`, `B7-grounding.md`.

---

## Summary of what the gaps contain

Nine defects live only between pages. In rough order of cost to fix later:

| # | Node | Defect | Severity |
|---|---|---|---|
| 1 | `AGND` | Three pages hang returns on a conductor two ADRs say must carry nothing | **Showstopper** |
| 2 | LM311 rail | `power-entry.md` puts the comparator on 5.21 V; that re-creates the exact fault the LM393 was rejected for | **Showstopper** |
| 3 | DAC ch7 / mod network | `mod-channels.md` is half-converted: its diagram says 30 k/3.3333 V, its tables say 40.2 k/2.500 V. Every other document says 30 k | **Major** |
| 4 | LM311 collector | BOM puts the pull-up on 5.21 V and the LED on bus +5 V — two rails on one node, and both pages say bus +5 V | **Major** |
| 5 | Bus +5 V | Three documents still say "only the buffer" is on it after two more loads were added | **Major** |
| 6 | `VREFOUT` | Pitch's offset trim can only move one direction; nothing computes the total load; breath proposes a share pitch forbids | **Major** |
| 7 | OPA2197 halves | Pages draw 9, BOM enumerates 11, packages buy 12. Three numbers | **Minor (cost)** |
| 8 | Output jacks | Six outputs, five clamps drawn, two input clamps not in the BOM; reconstruction corners differ 33× with no stated rule | **Major** |
| 9 | DVDD | The DAC's digital supply appears in one BOM cell and nowhere else, yet the level-shifter argument depends on it | **Major (gap)** |

Six shared assumptions checked out sound and are recorded in one line each at the end.

---

## Node `AGND`

### Who creates it

The instrument. `AGND` is umbilical pin 2, leaving the analog ground pour on the
bottom cluster board and running 2 m up the Cat5 `[repo: docs/decisions/0003-breath-sensing-path.md:641-646]`.

### What the ADRs say it may do

Unambiguous, and stated twice:

> "`AGND`, from the etherCON | **Nothing.** It is an in-amp input, not a ground
> (ADR 0003)" `[repo: docs/decisions/0004-cv-interface-module.md:496]`

> "**`AGND` is not in this list.** It terminates at the in-amp's IN+ and at the
> two 1 MΩ bias resistors, and that is all it does. Anything that makes it a
> return path breaks the reason a 2 m analog run works at all."
> `[repo: docs/decisions/0004-cv-interface-module.md:515-517]`

`power-entry.md` restates it correctly in prose: "`AGND` is not a ground at all —
it is an in-amp input (ADR 0003)" `[repo: hardware/module/power-entry.md:161]`.

### Who consumes it, page by page

| Page | Use | Legal under ADR 0004? |
|---|---|---|
| `breath-receive-stage.md:27,36` | umbilical `AGND` → R3 10 k → INA828 IN+ | **Yes** — this is the defined termination |
| `breath-receive-stage.md:44-46` | R4, R5 1 MΩ to **`AGND(module)`** | **Yes** — explicitly named in ADR 0004:516 |
| `breath-receive-stage.md:38,42` | 2 × `C_cm` 1.5 nF to **`AGND(module)`** | Yes in substance (CM filter return) |
| `power-entry.md:15-22` | C1 47 µF, C2 47 µF **and the LM317 output cap** return to a node drawn as `AGND` | **No** |
| `mod-channels.md:37` | `C-FILT-MOD` 82 nF × 4 to `AGND` | **No** |
| `digital-and-supervision.md:41-43` | `R-CLR-PD` 10 k to `AGND` | **No** |
| `digital-and-supervision.md:108-113` | proposed presence threshold "against `AGND`" | Conditional — see below |

### The defect

**`breath-receive-stage.md` is the only page that distinguishes `AGND(module)`
from the umbilical `AGND` conductor.** It writes the qualifier five times
`[repo: breath-receive-stage.md:38,42,46]` against the bare `AGND (pin 2)` at
line 27. The other three pages write bare `AGND` and mean, by context, the
module analog return. **No page, ADR or BOM row states whether these are one net
or two.** On a netlist they are one net by name, and the pages will be entered
into a netlist.

If they are one net, three consequences follow, none of them acknowledged:

1. **The module's analog bulk capacitance returns down the sense conductor.**
   `power-entry.md:15-22` draws C1 (47 µF, module analog +12 V) and C2 (47 µF,
   the *umbilical* +12 V branch) both returning to `AGND`. C2's return is the
   inrush path for 2.2 mF of instrument bulk `[repo: power-entry.md:77]` at up
   to 0.53 A `[repo: power-entry.md:83]`. That current is the single thing the
   whole D1/D2 split exists to keep off the analog side
   `[repo: power-entry.md:48-55]`.

2. **The mod channels' filter current lands in the breath differential input.**
   Four `C-FILT-MOD` at 82 nF, driven to ±10 V. At 1 kHz,
   `|Z| = 1/(2π · 1000 · 82e-9) = 1.94 kΩ` `[calc]`; `10 V / 1.94 kΩ = 5.2 mA`
   per channel, `× 4 = 20.6 mA` peak into `AGND` `[calc]`. B7 gives the `AGND`
   conductor as 0.189 Ω `[repo: docs/review/2026-09-20-cold-review/B7-grounding.md:904]`,
   so `20.6 mA × 0.189 Ω = 3.9 mV` `[calc]` appears **differentially** at the
   in-amp, `× 2.185 = 8.5 mV` at its output `[calc]`, against a 9.94 V span —
   0.09 %, i.e. mod-channel content audible on the breath CV. This is the same
   failure mode B7 §F-LED spends pages on, arriving by a new route.

3. **`R-CLR-PD` puts a permanent DC current in it.** 10 kΩ from the '123's
   push-pull `Q` at 5.21 V = `5.21 / 10 000 = 521 µA` `[calc]`, flowing whenever
   the watchdog is *not* firing, which is all of normal operation. 88 µV across
   0.189 Ω `[calc]` — electrically trivial, but it is a standing DC current in
   the one conductor that is specified to carry zero, and it is the precedent
   that makes the other two look acceptable.

If they are **two** nets, then `power-entry.md` has no drawn return for the
analog bulk caps or the LM317 output cap at all, and `mod-channels.md` /
`digital-and-supervision.md` reference an undefined node.

**Either reading is a defect.** Fix: rename the module analog return to
something that is not `AGND` — ADR 0004:494 already calls it "Module analog
return" — and use `AGND` exclusively for the pin-2 conductor. Then redraw
`power-entry.md:15-22`, `mod-channels.md:37` and
`digital-and-supervision.md:41-43` onto it.

### A second, smaller `AGND` defect: the presence threshold

`digital-and-supervision.md:108-113` proposes sensing "the module end of the
`BREATH` conductor directly against `AGND`", threshold +100 mV. Two problems the
page does not raise:

- **It needs a differential comparison.** `AGND` is not at module 0 V by
  definition, so "+100 mV" must be +100 mV *above `AGND`*. Generating that
  requires a threshold source referenced to `AGND` — which puts divider current
  into `AGND`, the thing item 1 above is about. At µA it is harmless, but it
  must be drawn and budgeted, not left implicit.
- **The hysteresis network taps the in-amp's input node.** BOM specifies "1M
  from output to IN+ for hysteresis" `[repo: hardware/bom.csv:100]`. If the
  LM311's IN+ *is* the `BREATH` node behind R2, then 1 MΩ from a 0/+5 V output
  injects up to `5 / 1e6 = 5 µA` `[calc]` into a node whose source impedance is
  the 10 kΩ protection resistor, giving `5 µA × 10 kΩ = 50 mV` `[calc]` of
  single-leg, single-ended error — `× 2.185 = 109 mV` at the in-amp output
  `[calc]`, about 1 % of full scale, and it steps at every plug event. It is
  also single-ended on one leg, which is the exact CM→DM conversion mechanism
  `breath-receive-stage.md:168-175` rejects a capacitor for.
  **The comparator must tap through its own buffer or a high-value divider, not
  hang on the in-amp's input pin.**

### One dependency claim that is false

`breath-receive-stage.md:164-166` states:

> "**But the rule as written in ADR 0003 forbids the thing that makes the
> receiver work, and must be restated** to mean 'no *power* current', which is
> what it always meant."

ADR 0003 as written already says exactly that: "Give the analog signal its own
return conductor that carries **no power current**"
`[repo: docs/decisions/0003-breath-sensing-path.md:336, emphasis in original]`.
ADR 0004:87 repeats it verbatim, and ADR 0004:516 explicitly names "the two
1 MΩ bias resistors" as a permitted termination. **Nothing needs restating; the
breath page's claim about ADR 0003 is wrong.** Delete the paragraph — it invites
someone to loosen a rule that is already correctly worded, and it is the only
textual cover the three illegal `AGND` returns above currently have.

---

## Node: the LM311's collector — `OE` ×4, panel LED, pull-up

### Consumers

| Consumer | Page | Assumption made |
|---|---|---|
| `OE` ×4 on the 74AHCT125 | `digital-and-supervision.md:28`, `power-entry.md:138` | active low; part is on bus +5 V |
| Panel LED + 820 Ω | `power-entry.md:139-141`, `digital-and-supervision.md:61` | pulled to **bus +5 V** |
| `R-OE-PU` 10 k | `power-entry.md:138`, `digital-and-supervision.md:60` | pulled to **bus +5 V** |
| LM311 open collector, emitter at GND | `digital-and-supervision.md:56` | LM311 on **±12 V** |

### Defect 4 — the BOM puts two different rails on one node

Both schematic pages agree: LED and pull-up both to bus +5 V
`[repo: power-entry.md:136-145; digital-and-supervision.md:60-61]`. The BOM does
not:

- `R-LED-PANEL`: "820R from **BUS +5V**, NOT 2k2 from +12V" `[repo: hardware/bom.csv:83]`
- `R-OE-PU`: "**FROM THE LM317'S 5.21V, NOT BUS +5V** — … the SUPERVISION must
  not [sit on the bus rail], or one rail failure takes the shifter, the OE
  gating and the only health indicator together" `[repo: hardware/bom.csv:101]`

**These are the same node.** The BOM is internally inconsistent on the node the
prompt flags as having changed twice today, and it disagrees with both pages.

**Verdict: the pages are right, `R-OE-PU`'s note is wrong, and its stated reason
is void.** The buffer whose `OE` this gates is itself on bus +5 V
`[repo: docs/decisions/0005-power-architecture.md:122-123]`. If bus +5 V dies,
the buffer is unpowered and its outputs are Hi-Z regardless of `OE` — which is
the safe state — so pulling `OE` to a surviving rail buys nothing. Pulling it to
5.21 V instead *costs* something: with the bus rail at its allowed −5 %
(4.75 V), the `OE` pin sits 0.46 V above its own VCC, and with the bus rail at
0 V it sits 5.21 V above it, back-feeding `5.21 / 10 kΩ = 521 µA` `[calc]`
through an unpowered part's input clamps. That is a smaller version of the
+12 V-on-a-5 V-input bug this node was fixed for once today.

Also note `R-OE-PU`'s `description` column still reads "Pull-up from the **LM393**
open collector" `[repo: hardware/bom.csv:101]` while its notes say LM311. Third
inconsistency on one row.

### Defect 2 (showstopper) — which rail is the LM311 on?

Three statements, two of them agreeing and one of them catastrophic:

- `digital-and-supervision.md:54-55` draws "LM311 / ±12 V"
- `power-entry.md:16` lists "LM311" among the loads on MODULE ANALOG +12 V
- BOM: "run it on **+-12V** so it can see the negative input, tie the emitter to
  GND, pull the collector to +5V" `[repo: hardware/bom.csv:99]`

against

- `power-entry.md:149-151`: "The **comparator** and the watchdog stay on the
  LM317's 5.21 V so that a bus rail failure cannot take the supervision with it."

**An LM311 on 5.21 V / GND cannot see a negative input.** That is precisely and
only why the LM393 was rejected:

> "The INA828 rests at −0.44V, below an LM393's own V− if it runs on +5V/GND"
> `[repo: hardware/bom.csv:99]`

`power-entry.md:149-151` re-creates the rejected fault under a new part number.
It is one sentence, it is on the page a builder reads while choosing rails, and
it is wrong. **Delete "the comparator and" from that sentence.** The watchdog
half of it is correct and is corroborated by `hardware/bom.csv:54`.

(Note that the argument the sentence is making — supervision must outlive a bus
rail glitch — is satisfied anyway: ±12 V is not the bus rail.)

### What the node actually does, checked

With the LM311 released, the node is pulled to +5 V through 10 kΩ. The LED
branch sees `5.0 − 2.0 = 3.0 V` across `820 Ω` only if the node is below 3.0 V,
so at 5 V the LED is dark and `OE` is high → outputs Hi-Z → **instrument absent
= buffer disabled = LED out**. With the LM311 saturated, the node is at ~0.2 V,
LED current `(5.0 − 2.0 − 0.2) / 820 = 3.4 mA` `[calc]` (the page's 3.8 mA
`[repo: power-entry.md:145]` is computed from 5.21 V, the rail it is no longer
on — harmless but stale), `OE` low → enabled → **LED lit**. Total LM311 sink
`3.4 mA + 5.0/10 kΩ = 3.9 mA` `[calc]`, trivial for the part. **Polarity,
fail-safe direction and current budget on this node are correct.** The defects
are in which rail the documents claim, not in the topology.

---

## Rail: bus +5 V

### Defect 5 — "the only thing on it is a $0.30 buffer" is now false in three documents

| Document | Claim | True? |
|---|---|---|
| `power-entry.md:41` | "`+5V ├──[FB4]──[C4 47µF]──── 74AHCT125 **only**`" | No |
| `power-entry.md:58-60` | "the **only** thing on it is a $0.30 buffer, and a reversed ribbon that kills the buffer and nothing else is an acceptable outcome (ADR 0004)" | No |
| ADR 0005:122-123 | "It is used — but **only for the 74AHCT125 level shifter**, around 10 mA" | No |
| ADR 0004:186-192 | "the only thing hanging on the unprotected bus +5 V pin is a $0.30 buffer. A reversed or row-offset ribbon that puts +12 V onto that pin kills the buffer and nothing else, **which is why the +5 V entry gets no protection network of its own**" | No |

`power-entry.md:136-145` and `digital-and-supervision.md:60-61` add two more
loads to the rail — `R-OE-PU` and the LED — and `power-entry.md:41` was not
updated in the same commit. The word "only" appears three lines above the
section that breaks it, on the same page.

**Why this is not cosmetic.** The no-protection decision at ADR 0004:191 is
*derived* from the "nothing else" claim. With the two new loads, a reversed or
row-offset ribbon puts +12 V onto a node that reaches:

- the 74AHCT125's four `OE` pins (dead part, accepted);
- **the LM311's open collector**, through 10 kΩ and through the LED — an
  external rail arriving on a supervision part that is deliberately on a
  different supply;
- the LED at `(12 − 2) / 820 = 12 mA` `[calc]` against a 4 mA design point
  `[repo: power-entry.md:145]` — survivable, visible;
- **and possibly the DAC's `SYNC` pin** — see the unresolved item below.

The ADR's cost/benefit ("kills a $0.30 part") no longer describes the blast
radius. Either re-derive it with the real load list, or fit the series element
ADR 0004 declined.

### Unresolved: what rail do the DAC-side SPI pulls go to?

`digital-and-supervision.md:31-32` draws the second `R-SPI-PULL ×3` between the
buffer and the DAC — "SCLK↓ MOSI↓ **CS↑**". The pull-up's rail is not stated on
any page, and `hardware/bom.csv:49` says only "DAC side: same". The two
candidates are not equivalent:

- **To bus +5 V**: a reversed ribbon reaches the DAC8568's `SYNC` pin through
  10 kΩ. That is a ~$10 part with a `SYNC` glitch that latches the clear-code
  register `[repo: digital-and-supervision.md:83-86]`, not a $0.30 buffer.
- **To 5.21 V**: correct against the DAC's own thresholds, and isolated from the
  bus rail. `521 µA` `[calc]` flows into the buffer's unpowered outputs if the
  bus rail dies, which is fine.

**5.21 V is right. Say so on the page.** It is the difference between a $0.30
failure and a DAC failure, and it is currently undrawn.

### Load

Nobody has added up bus +5 V. `10 mA` for the buffer `[repo: ADR 0005:123]` +
`3.4 mA` LED + `0.5 mA` pull-up = **~14 mA** `[calc]`. Negligible against any
rack. **Sound; no action.**

---

## Rail: the LM317's 5.21 V

### Consumers

| Consumer | Page | Stated |
|---|---|---|
| DAC8568 `AVDD` | `power-entry.md:18`, `digital-and-supervision.md:36` | yes |
| 74HC123 | `digital-and-supervision.md:47`, `hardware/bom.csv:54` | yes |
| DAC8568 `DVDD` | — | **nowhere** — see below |
| DAC-side `CS` pull-up | — | **undrawn** (above) |
| LM311 | `power-entry.md:149` claims it; everything else denies it | **defect 2** |

### Current budget — checks out

`Vout = 1.25 × (1 + 475/150) = 1.25 × 4.1667 = 5.208 V` `[calc]` ✓ matches the
stated 5.21 V `[repo: hardware/bom.csv:39]`.

Divider current `= 1.25 V / 150 Ω = 8.33 mA` `[calc]`. This alone exceeds an
LM317's minimum load requirement `[from memory: 3.5–10 mA]`, so the regulator
cannot fall out of regulation on a light load. **Sound.**

The '123's dynamic draw is the one number nobody computed, and it turns out to
be the answer to an open question. With `R·C = 1 MΩ × 220 nF = 0.22 s` and a
250 µs retrigger interval, the timing cap only charges
`ΔV = 5.21 × (1 − e^(−250e-6 / 0.22)) = 5.21 × 1.136e-3 = 5.9 mV` `[calc]`
between retriggers. Charge dumped per retrigger
`= 220 nF × 5.9 mV = 1.30 nC` `[calc]`; at 4 kHz that is `5.2 µA` `[calc]`.

So total: `8.33 mA` divider + DAC `AVDD` + ~0 for the '123 ≈ **11–13 mA**,
matching the BOM's "~13mA load incl. the divider, ~90mW"
`[repo: hardware/bom.csv:38]`. Dissipation
`(11.7 − 5.21) × 13 mA = 84 mW` `[calc]` in TO-92. **Budget is sound as written
— provided the LM311 does not move onto this rail.** If defect 2 is resolved the
wrong way, add the comparator's supply current and, far worse, lose the negative
input range.

### The '123 open question, answerable on paper

`hardware/bom.csv:54` and `digital-and-supervision.md:154-156` both leave open
"whether the '123 empties 220 nF in a 250 µs retrigger window". From the
arithmetic above the cap is only ever 5.9 mV above ground during steady
retriggering, so there is almost nothing to empty. The worst case is the first
retrigger after a timeout, with the cap near 5.21 V: with an internal discharge
resistance of order 50 Ω `[from memory — the figure is the gap]`,
`τ = 50 Ω × 220 nF = 11 µs` `[calc]`, `5τ = 55 µs < 250 µs` `[calc]`. **The
answer is almost certainly yes, and the only unknown is one number off a
datasheet — not a bench session.** Worth recording so E-phase time is not spent
on it.

### Sequencing

`AVDD` rises with +12 V through the LM317; bus +5 V rises independently from the
rack. Both orders were checked:

- **Bus +5 V first**: the buffer powers up, `OE` is pulled high by `R-OE-PU`
  (bus +5 V, per the pages), outputs Hi-Z, nothing is driven into an unpowered
  DAC. The LM311 is unpowered (±12 V absent) so its collector is open — which
  means high, which means disabled. **Correct by construction.**
- **5.21 V first**: `R-CLR-PD` holds `CLR` low = cleared = zero scale
  `[repo: digital-and-supervision.md:137-141]`, and the '123 shares the rail so
  there is no window where a powered '123 drives a dead DAC. **Correct.**

**Sound. No action.** The one residual is the '123's own power-on `Q` state,
already on both still-open lists `[repo: digital-and-supervision.md:152-153;
hardware/bom.csv:54]`.

### Defect 9 — `DVDD` exists in exactly one cell of the repository

`grep -rn "DVDD"` across the whole repo returns two hits: the C-DECOUPLE note
"DAC8568 AVDD+DVDD = 2" `[repo: hardware/bom.csv:43]` and a cold-review line
`[repo: docs/review/2026-09-20-cold-review/C2-passives.md:764]`. **No schematic
page assigns `DVDD` a rail.**

This is load-bearing, because the entire level-shifter argument is stated
against `AVDD`:

> "Its job is to get 3.3 V logic over the DAC's **0.7 × AVDD** input threshold —
> 3.65 V at AVDD = 5.21 V" `[repo: docs/decisions/0004-cv-interface-module.md:186-187]`

repeated at `digital-and-supervision.md:68`. On a part with a separate digital
supply, the digital input threshold is normally referenced to the *digital*
supply `[from memory — the DAC8568 datasheet is the gap]`. If `DVDD` is tied to
bus +5 V the threshold is `0.7 × 5.0 = 3.50 V` and the margin improves; if it is
tied to `AVDD` the stated 3.65 V holds; either way **the sentence everybody is
relying on names the wrong pin, and the pin it should name is undrawn.**

Fix: put `DVDD` on the 5.21 V rail explicitly (same rail as `AVDD`, which keeps
`CLR` levels unambiguous — the reason already given at
`digital-and-supervision.md:71`), draw it, and re-word the threshold sentence
against `DVDD`. Confirm the threshold reference pin when `ti.com` is reachable.

---

## Node `VREFOUT` and its buffered/trimmed derivative

### Who drives it

The DAC8568's internal reference, grade C, reference gain 2, so
`VREFOUT = 2.500 V` and full scale `= 5.000 V` `[repo: hardware/bom.csv:12]`.
Full scale is independent of `AVDD` `[repo: ROADMAP.md:189; ADR 0005:132-135]`.

### Who loads it

| Load | Page | Value |
|---|---|---|
| `TRIM-OFFSET` 10 kΩ across `VREFOUT` | `pitch-stage.md:14,131`, `hardware/bom.csv:106` | `2.5 / 10 kΩ = 250 µA` `[calc]` |
| `TRIM-BREATH-ZERO` 10 kΩ + divider, range 0…~0.6 V | `breath-receive-stage.md:53-54`, `hardware/bom.csv:108` | ~`60 µA` `[calc, see below]` |
| (rejected) passive divider for the mod reference | `mod-channels.md:84-87` | not adopted ✓ |

For the breath trimmer: producing 0…0.6 V from 2.500 V with a 10 kΩ pot at the
bottom needs a top resistor of `10 kΩ × (2.5 − 0.6)/0.6 = 31.7 kΩ` `[calc]`,
total 41.7 kΩ, `2.5 / 41.7 kΩ = 60 µA` `[calc]`.

**Total DC load ≈ 310 µA** `[calc]`. Whether the DAC8568's `VREFOUT` pin can
source that, and with what load regulation, is **unverified** — `ti.com` was
unreachable. It is the single most consequential unknown on this node, because
the pin sets both the DAC's own full scale *and* pitch's intercept.

### Is one follower enough? — yes, as drawn

The pitch follower drives only `R1` 10 kΩ, the bottom of the feedback divider:
`2.5 / 10 kΩ = 250 µA` `[calc]`. Comfortable. **Sound.**

### Defect 6a — pitch's "Shared with nothing else" is contradicted by breath

`pitch-stage.md:129` asserts of its buffered 2.500 V node:

> "| **V_ref** | 2.500 V, buffered `VREFOUT` | **Shared with nothing else**; one op-amp half |"

`breath-receive-stage.md:233-235` proposes to share it:

> "Its own values, its **offset reference (the buffered `VREFOUT` created for
> pitch is the obvious node)**, and whether the gain pot's wiper needs a buffer
> are E10 work."

These cannot both stand. The electrical cost is small — an OPA2197 follower's
output impedance at DC is milliohms `[from memory]`, so a few hundred µA of
extra static load moves the node by microvolts — but **the calibration cost is
not small, and it is the thing the prompt asks about:**

> Does trimming it for pitch move anything else?

**If breath's downstream offset takes the *buffered, trimmed* node, then yes.**
`TRIM-OFFSET` sets pitch's intercept `[repo: hardware/bom.csv:106]`, and moving
it would then also move where the breath jack rests. The two commissioning
procedures are written as independent — pitch's at `pitch-stage.md:202-205`,
breath's at `breath-receive-stage.md:199-209` — and neither mentions the other.
Adopting breath's "obvious node" silently couples them.

**Resolution to record now, before E10 makes the choice by default:** breath's
downstream stage must take its offset reference from **raw `VREFOUT` through its
own divider**, or from a DAC channel, never from pitch's trimmed node.

**The other direction is already safe, and this is the good news:**
`TRIM-BREATH-ZERO` taps **raw** `VREFOUT`, ahead of pitch's trim
`[repo: breath-receive-stage.md:53-54]`. So **pitch's trim does not move breath's
zero.** One line, correct as drawn, no action.

### Defect 6b — the load must be constant, and nobody says so

Any load on `VREFOUT` that *changes* shifts the DAC's own full scale, and
therefore shifts pitch tuning — the same shape as today's already-found bug
(a trimmer on one page breaking a circuit on another), running in the opposite
direction.

- `TRIM-OFFSET` is specified "10 kΩ … **across** `VREFOUT`" `[repo: pitch-stage.md:131]`.
  A pot wired end-to-end across a source draws a constant current regardless of
  wiper position; only the wiper current varies, and the wiper feeds a
  high-impedance follower input. **Constant load. Sound.**
- `TRIM-BREATH-ZERO` is specified only as "10k multiturn cermet + divider"
  `[repo: hardware/bom.csv:108]` with no topology. **If it is wired as a
  rheostat, turning it modulates `VREFOUT` and therefore pitch.**

**Write the rule on both pages: every trimmer on `VREFOUT` is a potentiometer
across a fixed divider, never a rheostat.** It costs nothing at draw time and
is unrecoverable at layout time.

### Defect 6c — pitch's offset trim is one-sided, downward only

`pitch-stage.md:14` draws `VREFOUT ──[TRIM-OFFSET 10k]──┬── ½ OPA2197 follower`,
with "+ range resistors", and the BOM gives the intended authority as
"Range ~50mV on a 2.5V reference is ~60 cents of offset" `[repo: hardware/bom.csv:106]`.

**A divider from a 2.500 V source cannot produce more than 2.500 V.** The
required nominal is 2.500 V `[repo: pitch-stage.md:58,128]`. So the achievable
range is `(0, 2.500] V` — the trim can only reduce `V_ref`, which only makes the
intercept less negative, which only moves pitch **sharp**. It cannot go flat.
`[calc: max output of a resistive divider = its source]`

This is the identical error the same page catches on its *other* trimmer:

> "**0 → +5 % of ratio, one-sided** — a series trimmer can only add. … but it is
> not ±5 % and an earlier revision said it was" `[repo: pitch-stage.md:130]`

The page found it once and missed it once, two rows apart in the same table.

**Fix options, both cheap:** give the "follower" a non-inverting gain of ~1.02
with the trimmer in its feedback divider, so 2.500 V sits mid-travel; or feed
the top of the trim divider from the 5.21 V rail rather than from `VREFOUT`
(which forfeits the ratiometric argument at `pitch-stage.md:99-119` and should
therefore be the second choice).

### Defect 6d — the range-setting resistors have no BOM row

`pitch-stage.md:14` says "+ range resistors" in the drawing and nowhere else.
`TRIM-OFFSET` in the BOM is the trimmer alone `[repo: hardware/bom.csv:106]`;
`TRIM-BREATH-ZERO` says "+ divider" with no values `[repo: hardware/bom.csv:108]`.
Two divider networks, four to six resistors, zero part numbers, zero values.
**They are the parts that set both trims' authority**, which is the one thing
defect 6c shows is currently wrong.

### Also on this node: `R-OFFINJ`

`pitch-stage.md:132` still carries an `R-OFFINJ` row ("470 kΩ 1 % — **Value and
topology are wrong as drawn**") sixty lines above `pitch-stage.md:192`, which
deletes the part. The BOM has already deleted it `[repo: hardware/bom.csv:106]`.
Stale row; delete it before someone stuffs a 470 k.

### Breath's offset pot needs a reference polarity that does not exist

Following the chain across two pages: the in-amp output runs 0 → −9.94 V
`[repo: breath-receive-stage.md:155]`; the downstream stage is an **inverting**
summer with gain and offset into one virtual ground
`[repo: breath-receive-stage.md:60-63,88-90]`. An inverting summer fed from a
**positive** reference produces a **negative** offset contribution. So with the
only available references being `VREFOUT` (+2.500 V) and the DAC channels
(0…+5 V), **the panel OFFSET knob can only move the jack's rest point down.**
There is no negative reference anywhere on the module. This is E10 work by
`breath-receive-stage.md:233`, but the constraint belongs on the page now,
because it is a statement about which shared node the stage may use.

---

## Node: DAC channel 7 and its follower

### Defect 3 (major) — `mod-channels.md` is half-converted, and it is the only document that is

The `k = 3` conversion — `R2` 30 kΩ, `V_ref` 3.3333 V, gain exactly 4, output
exactly ±10.000 V — is carried by **every other document in the repository**:

| Document | Says |
|---|---|
| `docs/decisions/0006-cv-channel-allocation.md:15` | "DAC ch 7 … Shared **3.3333 V** offset for mod 1–4" |
| `docs/decisions/0006-cv-channel-allocation.md:21,92` | 3.3333 V, `k = 3` |
| `hardware/bom.csv:68` (`R-MODGAIN`) | "R1=10k, **R2=30k** per channel, k=3 so gain = 1+k = **4 exactly** … **V_ref = 3.3333V**. Lands on **EXACTLY ±10.000V**, where the old four-resistor difference amp needed a 40.2k fudge" |
| `hardware/module/pitch-stage.md:83-85` | "`k = 3` with the offset channel writing **3.3333 V**" |
| `docs/research/…/R1-pitch-output-stages.md:137-138` | "`V_ref = 10/3 = 3.3333 V`" |
| `hardware/module/mod-channels.md:14,20,31,54-77` | **3.3333 V, 30 k, ±10.000 V** ✓ |

and is then contradicted by four later sections of that same page:

| Line | Stale text | Should be |
|---|---|---|
| `mod-channels.md:94` | "**R2, R4** \| **40.2 kΩ 1 %** \| … Gain 4.02, so the jack reaches **±10.05 V**" | 30 kΩ, gain 4, ±10.000 V |
| `mod-channels.md:95` | "**V_OFF** \| **2.500 V** from DAC ch7, buffered" | 3.3333 V |
| `mod-channels.md:98-101` | the whole "40.2 kΩ rather than 39 kΩ" paragraph | delete |
| `mod-channels.md:118-120` | tolerance table computed on the 40.2 k network | recompute |
| `mod-channels.md:145-156` | `Vout = 4.02 × (0 − 0)`, `4.02 × (0 − 2.5) = −10.05`, `4.02 × Vdac ≈ +11.45` | ×4 |
| `mod-channels.md:166-167` | "At **2.5 V** into 2.5 kΩ that is **1 mA**" | 3.3333 V, 1.33 mA |

The page's own diagram at line 16 already says "~1.3 mA total into 4 × 10k",
which is correct for 3.3333 V `[calc: 3.3333 / 2.5 kΩ = 1.333 mA]`, while line
167 says 1 mA, correct for 2.500 V `[calc: 2.5 / 2.5 kΩ = 1.00 mA]`. **The page
contradicts itself by exactly the conversion it is announcing.**

This matters cross-page because `pitch-stage.md:83-85` *forward-references*
`mod-channels.md` for the 3.3333 V figure — and lands on a page whose component
table says 2.500 V. The prompt's dependency test ("where a page says see X for
Y, does X actually say Y?") fails here.

### Corrected tolerance for the network that is actually specified

The stale table gives "Zero point ±81 mV, Span 19.70–20.51 V"
`[repo: mod-channels.md:118-120]`. For `R1 = 10 k`, `R2 = 30 k`, both 1 %, with
`V_ref = 3.3333 V` exact (it is a DAC code, not a resistor):

```
Vout = (1 + R2/R1)·Vdac − (R2/R1)·3.3333

corner A   R1 = 9.9k,  R2 = 30.3k  → k = 3.0606, gain 4.0606, intercept 10.2019
           Vdac = 5 → +10.101 V     Vdac = 0 → −10.202 V     span 20.303 V
corner B   R1 = 10.1k, R2 = 29.7k  → k = 2.9406, gain 3.9406, intercept  9.8019
           Vdac = 5 →  +9.901 V     Vdac = 0 →  −9.802 V     span 19.703 V

zero point at Vdac = 2.5:  A → −50.4 mV     B → +49.6 mV
```
`[calc]`

**Span 19.70–20.30 V, zero ±50 mV** — better than the stale ±81 mV / 20.51 V on
both terms. The page's conclusion ("±2 % of gain is the dominant term … anything
pitch-like belongs on channel 1", `mod-channels.md:120-126`) survives unchanged;
only the numbers move. Worst-case +10.20 V still fits the ~±11.45 V headroom
`[repo: mod-channels.md:100]`. **Sound after renumbering.**

### `3.3333 V` is exactly representable — a genuinely clean result

`65535 = 3 × 21845`, so `⅔ × 65535 = 43690` exactly, and
`43690 / 65535 × 5.000 V = 3.333333 V` `[calc]`. The shared offset lands on an
integer code with **zero** quantisation residue, and `3 × 3.333333 = 10.000000`.
The `k = 3` choice is arithmetically exact, not merely convenient. Worth saying
on the page.

The `CLR` safe-state argument also holds exactly and for a subtler reason than
the page gives: on `CLR` both `Vdac` and `V_ref` go to zero scale, and **any
zero-scale offset the DAC has appears in both terms and cancels** —
`4 × (ε − ε) = 0` `[calc]`. `[repo: mod-channels.md:59-61,144-152]` **Sound.**

### Does anything else hang on ch7? — No, and that is correct

Searched: ch7 appears only in `mod-channels.md`, ADR 0006:15,21 and
`hardware/bom.csv:12`. The follower drives four 10 kΩ inputs and nothing else
`[repo: mod-channels.md:164-176]`. Channel allocation is consistent across all
documents: pitch ch1, mods ch2–ch5, offset ch7, **6 of 8 populated, ch6 and ch8
spare** `[repo: hardware/bom.csv:12]`, matching "refresh all six populated
channels" `[repo: mod-channels.md:157-158]`. **Sound.**

One stale echo to note: ADR 0006:278 still says "Channels **2–6** need only to be
linear and repeatable" — the signal mods are now 2–5 and 6 is free
`[repo: ADR 0006:25]`. Harmless but worth one edit.

### Defect: the mod channels use the full 0–5 V span, on the strength of half of ADR 0006's reasoning

`mod-channels.md:131-134`:

> "**On the range:** ±10.05 V uses the DAC's *full* 0–5 V span. ADR 0006's
> 0.25–4.75 V window is a **pitch-channel reserve** — it exists to give firmware
> ±600 cents of offset authority on 1 V/oct — and does not apply here."

ADR 0006 gives the window **two** reasons, not one:

> "Use the DAC's 0.25–4.75 V window rather than its full 0–5 V span. That leaves
> 250 mV of headroom at both rails — **the DAC8568 at AVDD = 5 V cannot reliably
> swing to its own supply** — and the trimmer absorbs the resulting gain change."
> `[repo: docs/decisions/0006-cv-channel-allocation.md:418-421]`

The firmware-reserve reason `[repo: ADR 0006:462-463]` is indeed pitch-specific.
**The output-swing reason is a device limit and applies to every channel.** By
dismissing the window wholesale, `mod-channels.md` puts the four mod channels at
exactly the codes whose behaviour the LM317 rail exists to protect:

> "raise the top codes and find where they start compressing against AVDD. That
> is the floor that actually matters" `[repo: ADR 0004:179-181]`

> "Full scale is 5.000 V from the internal reference at gain 2, *independent* of
> AVDD — what AVDD decides is whether the output buffer can reach it"
> `[repo: ROADMAP.md:189]`

So the mod channels, at code 65535, are the channels that will discover whether
5.21 V was enough — and they are the ones the page says need no margin. **This
is not necessarily wrong** (5.21 V may well be sufficient, which is what E7
measures), but **the page's stated reason for dismissing the window is wrong,
and it removes the only margin the design has against an E7 failure.** Add one
line to `mod-channels.md` acknowledging the second reason and naming E7 as the
gate; if E7 finds compression, it is the mod channels that clip, and the fix is
a window on them too.

---

## Node: the six CV outputs — `R-OUT-PROT`, `D-JACK-CLAMP`, reconstruction caps

Six outputs across three pages: PITCH `[pitch-stage.md]`, MOD 1–4
`[mod-channels.md]`, BREATH `[breath-receive-stage.md]`.

| | PITCH | MOD 1–4 | BREATH |
|---|---|---|---|
| Series R | `R-OUT-PROT 1 kΩ, 1206` `[pitch:33]` | `R-OUT-PROT 1 kΩ, 1206` `[mod:35]` | **"[1k]"**, unnamed, no package `[breath:65]` |
| Clamp | `D-JACK-CLAMP BAV99` to ±12 V, **driver side** `[pitch:31]` | `D-JACK-CLAMP BAV99` to ±12 V, **driver side** `[mod:33]` | **none drawn** |
| Filter cap | **none at the jack** — `C-FB-PITCH` 1 nF in feedback `[pitch:29,166-171]` | `C-FILT-MOD` 82 nF, **jack side** `[mod:37]` | 330 nF, jack side `[breath:65,144]` |
| Corner | 15.9 kHz `[calc: 1/(2π·10k·1n) = 15.92 kHz]` | 1.94 kHz `[calc: 1/(2π·1k·82n) = 1.941 kHz]` | 482 Hz `[calc: 1/(2π·1k·330n) = 482 Hz]` |
| Feedback tap | **at the jack** `[pitch:35,144-165]` | at the op-amp output `[mod:31]` | not drawn |

### Defect 8a — the sixth clamp is bought and not drawn

`D-JACK-CLAMP` is qty **6**, "Clamp diodes on the DRIVER side of R-OUT-PROT",
and its own back-powering arithmetic is computed across "**254 mA across six
jacks**" `[repo: hardware/bom.csv:52]`. Five are drawn — pitch and four mods.
**The breath output has no clamp on its page.** Either `breath-receive-stage.md`
is missing one, or the BOM quantity is wrong and the back-powering figure is
computed over a jack that has no clamp. The first reading is almost certainly
right: the breath jack is as patchable as the others and its op-amp is on the
same ±12 V.

### Defect 8b — two BAV99s exist that the BOM does not buy

`breath-receive-stage.md:32` draws "BAV99 to ±12 V, **both legs**" on the
*receive* pair (`BREATH` / `AGND`), inside the module boundary. `D-JACK-CLAMP`
qty 6 is explicitly output-side only `[repo: hardware/bom.csv:52]`.
`grep BAV99 hardware/bom.csv` returns that one row. ADR 0004:636 references
"BAV99 bound the rest (`hardware/module/breath-receive-stage.md`)", so the part
is real and reasoned — **it has no BOM row.** Module BAV99 count should be
6 outputs + 2 input legs = **8**, or 6 + 1 dual-package if one BAV99 serves both
legs. (The instrument-end ESD parts are separate and correctly rowed:
`D-TVS-BREATH` qty 2 `[repo: hardware/bom.csv:96]`.)

### Defect 8c — the reconstruction convention is stated as one rule and is not one rule

The BOM states a single convention twice, in identical words, for two of the
three outputs:

> "**ON THE JACK SIDE of R-OUT-PROT, never the op-amp side** — inside the loop it
> is a capacitive load and the stage can oscillate."
> `[repo: hardware/bom.csv:64 (C-OUT-BREATH) and :67 (C-FILT-MOD)]`

Pitch is the exception and knows it: the jack-side cap is deleted because the
jack is now the feedback node `[repo: pitch-stage.md:166-171]`. That is sound
engineering and the page argues it well. But the **corners** are then left at
15.9 kHz / 1.94 kHz / 482 Hz with no stated rule, and the BOM itself flags the
mismatch from the other side:

> "1k x 82nF = 1.94kHz. **Real attenuation on the 3.6kHz ZOH image that a 15.9kHz
> corner ignores.**" `[repo: hardware/bom.csv:67]`

Against the 4 kHz DAC update rate `[repo: digital-and-supervision.md:85-86]`:

```
pitch, 15.92 kHz:  20·log10(1/√(1+(4/15.92)²))  = −0.27 dB   [calc]
mod,    1.941 kHz: 20·log10(1/√(1+(4/1.941)²))  = −7.20 dB   [calc]
```

**So the BOM says in plain words that pitch's reconstruction filter does not
reconstruct, and `pitch-stage.md:166-170` says the opposite:**

> "The 15.9 kHz reconstruction pole comes from `C-FB-PITCH` instead, which is the
> **same corner in a better place**"

It is the same corner as the *deleted* part, and that corner was already
ineffective — a fact recorded in the BOM and nowhere on the pitch page. Whether
pitch *needs* image rejection is arguable (a 1 V/oct CV into a VCO integrates
the staircase away; a 4 kHz artefact 68 dB down is inaudible), but **the two
documents currently assert opposite things about the same capacitor, and the
page's justification for the value is the weaker of the two.** Either state the
rule ("pitch needs stability compensation, not image rejection; 1 nF is chosen
for the loop, and the image is left to the VCO") or raise the corner. Do not
leave "same corner in a better place" standing next to the BOM line that calls
that corner ineffective.

Breath's 482 Hz is not a reconstruction pole at all — breath never passes through
the DAC `[repo: hardware/bom.csv:67]` — it is the channel band limit. Calling it
"reconstruction" `[repo: breath-receive-stage.md:144]` is a naming error that
makes the three-way comparison look like an inconsistency when it is not.

### Defect 8d — pitch's own component table and trim procedure contradict pitch's own change, and the ROADMAP inherits it

Three places on `pitch-stage.md` still describe the *pre-change* output:

| Line | Says | But |
|---|---|---|
| 134 | "`R-OUT-PROT` … A load divider the gain trim absorbs (ADR 0006)" | feedback is now at the jack, so the divider error is "identically zero for any load" `[repo: pitch-stage.md:155-156]` |
| 135 | "`C-FILT-PITCH` \| 10 nF C0G \| 15.9 kHz, **jack side**" | deleted at line 166 |
| 207-209 | "**Trim with the real patch connected** … that error is what the gain trim's ±5 % range exists to absorb" | same — there is no longer a load error to absorb |

And this propagates off the page:

- `ROADMAP.md:190` — "**Pitch DC load sweep: open / 100k / 50k / 33k** … Quantifies
  the 1 kΩ divider error against the real patch" — a test for an error the new
  topology removes by construction. Keep the sweep (it now *verifies* zero) but
  rewrite its purpose.
- `ROADMAP.md:191` — "Pitch stability into worst-case cable capacitance \|
  **Confirms the plain series RC is unconditionally stable where an in-loop
  version would not have been**". `pitch-stage.md:173-175` cites this row as
  already covering the new risk:

  > "**E9 already has the check** — 'pitch stability into worst-case cable
  > capacitance' was in the measurement table before this change, and it is now
  > load-bearing rather than reassuring."

  **The row's title is there; its stated rationale is the exact opposite of the
  new circuit.** The design now *is* the in-loop version the row was written to
  say it had avoided. The page's dependency claim is half-true in the way that
  matters least: the words survive, the reason inverts. **Rewrite ROADMAP:191
  before E9, or the test will be run against the wrong hypothesis.** This is the
  highest-risk item on the pitch page by the page's own assessment
  `[repo: pitch-stage.md:175]`, and its verification row currently disagrees with it.

### Defect 8e — `TRIM-GAIN` has three values across two documents

| Source | Value | Implied authority |
|---|---|---|
| `pitch-stage.md:35` (drawing) | **200 R** | `+2 %` of a 10 k ratio `[calc]` |
| `pitch-stage.md:130` (table) | **1 kΩ** | `+10 %` `[calc]` |
| `pitch-stage.md:230` (still open) | "1 kΩ or 500 Ω" | `+10 %` or `+5 %` |
| `pitch-stage.md:130,209` (prose) | "±5 %" / "±5 % range" | `500 Ω`, and one-sided not ± |
| `hardware/bom.csv:105` | "**200R, not 1k**" | `0 → +2 %`, "~2ppm/degC — COMPARABLE to the LT5400" |

The BOM has decided: 200 R, for a stated reason (tempco), enabled by the
feedback-at-jack change `[repo: hardware/bom.csv:105]`. **The pitch page has not
been told.** This is not cosmetic: `pitch-stage.md:215` lists `TRIM-GAIN` tempco
as "**0.4–2.4 cents** … the largest line here" and records the 6× disagreement as
"**not reconciled**" — but the BOM reconciled it by shrinking the part, which
takes the term to "~2 ppm/°C" and off the top of the list. **The page's accuracy
table is ranking a term the BOM already fixed.** Update line 35, line 130, line
215 and the Still Open at line 230 together.

---

## Part: OPA2197 — the half count

Counted by walking every page. Instrument-side halves excluded (they are
`U-BUF`, a separate qty-1 row `[repo: hardware/bom.csv:27]`).

| Page | Half | Ref |
|---|---|---|
| `pitch-stage.md` | `VREFOUT` follower | `:14` |
| `pitch-stage.md` | pitch amplifier | `:25` |
| `mod-channels.md` | DAC ch7 offset buffer | `:14` |
| `mod-channels.md` | mod channel ×4 | `:27` + "(ch3, ch4, ch5 identical)" `:20` |
| `breath-receive-stage.md` | INA828 `REF` buffer | `:53` |
| `breath-receive-stage.md` | downstream inverting **gain + offset**, one block, labelled "**½ OPA2197**" | `:60-63` |
| `digital-and-supervision.md` | — | none |
| `power-entry.md` | — | none |

**Drawn module total: 1 + 1 + 1 + 4 + 1 + 1 = 9 halves** `[calc]`.

The BOM enumerates eleven:

> "Twelve halves, eleven used: pitch, mod 1-4, mod offset buffer, **breath gain,
> breath offset**, VREFOUT follower, breath REF-zero buffer. One spare."
> `[repo: hardware/bom.csv:13]`

`1 + 4 + 1 + 1 + 1 + 1 + 1 = 11` `[calc]` — and **"breath gain" and "breath
offset" are the same half.** The pages say so:

> "an inverting summer does gain and offset with two pots into **one virtual
> ground**" `[repo: breath-receive-stage.md:88-90]`

and the BOM says so itself, two rows earlier:

> "the downstream stage inverts, which is also the topology that does
> gain-then-offset with two pots in **one op-amp half**"
> `[repo: hardware/bom.csv:28]`

**`hardware/bom.csv:13` double-counts one half against `hardware/bom.csv:28`.**

Consequences, all small but all wrong in the same direction:

- **The true count is 9, not 11.** Six packages = 12 halves gives **3 spare**, not
  one `[calc]`.
- `breath-receive-stage.md:125` — "It costs the last spare OPA2197 half, and
  `U-OPA-PITCH` goes to six packages so there is still one" — is wrong twice:
  it was not the last spare, and there are three left, not one.
- The BOM's own history line, "Was 5 packages with zero spare once the breath
  zero trimmer went in" `[repo: hardware/bom.csv:13]`, implies **10**, a third
  number. At the true count of 9, five packages give one spare and the stated
  reason for going to six ("too tight for a part that costs nothing") is already
  satisfied at five.
- `C-DECOUPLE` is budgeted against yet another number — see below.

**Recommendation: keep six packages** (the reasoning is sound, the part is
cheap, and two open items could each consume a half: "whether the gain pot's
wiper needs a buffer" `[repo: breath-receive-stage.md:234]` and the recorded mod
alternative, which would *return* a half `[repo: mod-channels.md:192-193]`). But
**correct the enumeration in `hardware/bom.csv:13`**, because it is the only
place the halves are listed and it is currently one short of describing a
circuit that exists.

### Knock-on: `C-DECOUPLE` qty 19 is computed against 5 op-amps and a part that was replaced

> "One per supply pin … **5 x OPA2197** on +/-12V = 10, INA828 = 2, DAC8568
> AVDD+DVDD = 2, 74AHCT125, 74HC123, LT1641 VCC, LM317 in, **LM393**."
> `[repo: hardware/bom.csv:43]`

Two errors: the op-amp row is six packages, not five `[repo: hardware/bom.csv:13]`,
and the LM393 became an LM311 on ±12 V `[repo: hardware/bom.csv:99]` — two supply
pins, not one. Recount:

```
6 × OPA2197 × 2 pins      12
INA828 (±12 V)             2
DAC8568 AVDD + DVDD        2
74AHCT125                  1
74HC123                    1
LT1641 VCC                 1
LM317 in                   1
LM311 (±12 V)              2
                          ──
                          22        [calc]
```

**22, not 19.** The row's own warning — "Was 10, which is about half the real pin
count" — applies to itself.

---

## Part: `R-OPAMP-IN` — is 7 the right quantity?

The enumeration is given twice, identically:

> "`R-OPAMP-IN` qty 7 covers pitch, the four mods, this buffer and the `VREFOUT`
> follower" `[repo: mod-channels.md:170-171]`

> "SEVEN … Pitch, mod 1-4, the mod offset buffer, the VREFOUT follower."
> `[repo: hardware/bom.csv:51]`

`1 + 4 + 1 + 1 = 7` `[calc]` ✓ internally consistent.

**But the list is drawn from two pages and omits the third.** The stated purpose
is clamp-current protection where a DAC pin on 5.21 V meets an op-amp on ±12 V
that may power up first `[repo: pitch-stage.md:87-90; hardware/bom.csv:51]`.
There are **eight** op-amp inputs driven from a DAC pin:

| # | Input | Has one? | Needed? |
|---|---|---|---|
| 1 | pitch amp (+), from DAC ch1 | yes `[pitch:21]` | yes |
| 2–5 | mod amps (+), from DAC ch2–5 | yes `[mod:23]` | yes |
| 6 | mod offset buffer (+), from DAC ch7 | yes `[mod:14]` | yes |
| 7 | `VREFOUT` follower (+), from `VREFOUT` | yes `[bom:51]` | **redundant** |
| 8 | **breath `REF` buffer (+), from `VREFOUT`** `[breath:53-54]` | **no** | **arguably** |

Two observations that cancel to leave 7 by coincidence rather than by design:

- **#7 is redundant.** `TRIM-OFFSET` is already in series with that input —
  10 kΩ `[repo: hardware/bom.csv:106: "AHEAD of the VREFOUT follower"]` — which
  limits clamp current to `(12 − 2.5) / 10 kΩ = 0.95 mA` `[calc]` by itself. The
  extra 1 kΩ adds 10 % to a value that is already 10× what is needed.
- **#8 is missing.** Same exposure, same node class — but also already protected
  by its own trimmer network, ~41.7 kΩ `[calc, from hardware/bom.csv:108]`.

So the correct statement is not "seven" but **"five where the DAC drives an
op-amp input directly; the three `VREFOUT`-derived inputs are protected by their
trimmer networks"** — and the count is 5, or 7 if you prefer belt and braces on
two of them. Either is defensible; what is not defensible is an enumeration that
includes one trimmer-protected input and silently excludes an identical one on a
page the author of that row had already read. **Symptom of the same gap as the
op-amp half count: `mod-channels.md` and `hardware/bom.csv:51` enumerate the
module from two pages out of three.**

---

## Part: LT5400 — the two spare sections cannot do what the BOM says

`hardware/bom.csv:15`:

> "Two of the four used at 1:1; **the other two are available for the mod
> channels, which want 1:3 (three sections against the fourth).**"

echoed at `pitch-stage.md:233-234` ("The two spare LT5400 resistors. Available,
matched, and currently doing nothing. Worth a look when the mod channels are
laid out") and `mod-channels.md:56-57` ("a 1:3 ratio that three sections of an
LT5400 give directly against the fourth").

**A 1:3 ratio built from a quad uses three sections in series against one — all
four.** Two spare sections give 1:1 or 2:1, never 1:3 `[calc]`. And there are
four mod channels, each wanting its own pair, so even a whole spare quad serves
one channel. The mod channels are specified as ordinary 1 % discretes anyway
(`R-MODGAIN`, `[repo: hardware/bom.csv:68]`, "The discretes won"
`[repo: mod-channels.md:9]`).

**The claim is arithmetically impossible and the need it serves was already
retired.** Delete it from `hardware/bom.csv:15` and downgrade
`pitch-stage.md:233` to what it really is: two matched 10 kΩ resistors available
for anything that wants a matched pair.

---

## Part: 74AHCT125 — the spare gate's input floats

`hardware/bom.csv:35`: "Covers SCLK MOSI CS with **a spare gate**."
`hardware/bom.csv:49`: the six pulls are enumerated as "CS to +5V, SCLK and MOSI
to ground" on each side — **three signals, both sides, six resistors.** The
fourth gate is not in that list.

The stated reason for the cable-side pulls is "so the buffer's inputs do not
float **and crowbar** when the instrument is absent" `[repo: hardware/bom.csv:49]`.
An unconnected AHCT input crowbars for exactly the same reason whether it is
spare or not `[from memory: a CMOS input biased near mid-rail conducts both
output transistors]`. **Tie the spare gate's input to ground at the package.** No
new part, one net, and it is invisible once the board exists.

---

## Cross-page dependency claims — audit

Every "see X for Y" in the five pages, checked against X.

| Claim | Where | Verdict |
|---|---|---|
| "see `mod-channels.md`" for `k=3` / 3.3333 V | `pitch-stage.md:85` | **Half-false.** That page's diagram says 3.3333 V; its component table says 2.500 V and 40.2 kΩ `[repo: mod-channels.md:94-95]` |
| "ADR 0006 specifies `Vout = 4 × (Vdac − 2.5 V)`" | `mod-channels.md:6` | **True** `[repo: ADR 0006:102]` |
| "an A/C-grade DAC8568 clears every channel to zero scale (ADR 0006)" | `mod-channels.md:141` | **True** `[repo: ADR 0006:134]` |
| "ADR 0006 says these channels need to be 'linear and repeatable, not calibrated'" | `mod-channels.md:123` | **True** `[repo: ADR 0006:278,423]`, though the ADR says "channels 2–6" and the allocation is now 2–5 |
| "the statelessness rule in `firmware/README.md` — refresh all six populated channels every pass" | `mod-channels.md:157-158` | **True in substance, not in words.** `firmware/README.md:38` says "**Refresh everything, every pass. Never write-on-change.**" It does not say "six" or name the channels. The quantity comes from `hardware/bom.csv:12`. Fine, but the page quotes a specificity the file does not have |
| "ADR 0006's 0.25–4.75 V window is a pitch-channel reserve … does not apply here" | `mod-channels.md:131-134` | **Half-false** — see the DAC ch7 section. The ADR gives two reasons; one is a device limit that applies everywhere `[repo: ADR 0006:418-421]` |
| "the rule as written in ADR 0003 … must be restated to mean 'no *power* current'" | `breath-receive-stage.md:164-166` | **False.** ADR 0003:336 already says "carries no power current", and ADR 0004:516 already permits the 1 MΩ bias pair |
| "ADR 0004, 'The watchdog's scope is the DAC channels'" | `breath-receive-stage.md:226-227` | **True** `[repo: ADR 0004; digital-and-supervision.md:143-146]` |
| "E9 already has the check — pitch stability into worst-case cable capacitance" | `pitch-stage.md:173-175` | **Title yes, rationale inverted.** `ROADMAP.md:191` says the row confirms the plain series RC "is unconditionally stable **where an in-loop version would not have been**" — and the design is now the in-loop version |
| "Trim with the real patch connected (ADR 0006)" | `pitch-stage.md:207` | **True of ADR 0006, obsolete in this design** — the page's own §"DC feedback is tapped at the jack" removes the error being trimmed out |
| "a reversed ribbon that kills the buffer and nothing else is an acceptable outcome (ADR 0004)" | `power-entry.md:58-60` | **ADR 0004:189-191 does say it** — but the premise ("the only thing on it is a buffer") was invalidated 80 lines later on the same page |
| "the same shape as the polyfuse thermal runaway ADR 0014 describes" | `power-entry.md:121-122` | **True** `[repo: ADR 0014:186-191]` |
| "ADR 0005's deletion argument was about the *instrument-end* polyfuse" | `power-entry.md:173-175` | **True** `[repo: ADR 0005:275]` |
| "`AGND` is not a ground at all — it is an in-amp input (ADR 0003)" | `power-entry.md:161` | **True** — and contradicted by the diagram 140 lines above it |
| "the bus rail is a stated requirement (ADR 0005)" | `digital-and-supervision.md:68` | **True** `[repo: ADR 0005:142-143]` — but the same ADR line 123 says "**only** for the 74AHCT125", which the page breaks at line 60 |
| "`CLR` … An analog path cannot latch at a level the player is not producing (ADR 0004)" | `digital-and-supervision.md:145-146` | **True** |
| "The BOM's `R-PRESENCE` note still describes the old −200 mV arrangement and is wrong" | `digital-and-supervision.md:115-116` | **False — it was already fixed.** `hardware/bom.csv:100` reads "TAP AHEAD OF THE REF TRIM … Threshold ~+100mV, POSITIVE". The page is reporting a defect that the BOM row no longer has. **Delete the sentence and the matching Still Open at line 150-151** |
| "`R-PRESENCE` … the earlier −200 mV arrangement" | `hardware/bom.csv:100` | Correct and current |

### The presence detect's stale copies are still live in two places

The digital page correctly identifies and fixes the trimmer-versus-comparator
collision `[repo: digital-and-supervision.md:103-116]`, but three documents still
carry the pre-fix circuit:

- **Its own drawing.** `digital-and-supervision.md:52-57` still shows "in-amp
  output ── (0 V absent, **−0.44 V alive**)" into the LM311 with "threshold
  **−200 mV** (from −12 V)" — the arrangement the prose forty lines below
  declares broken. The ASCII is what a builder reads.
- **ADR 0004:355-378** still presents the −437 mV / −200 mV table as the design,
  and its "**Fixed is the operative word**" paragraph explicitly rests on `REF`
  being grounded `[repo: ADR 0004:376-378]`.
- **`ROADMAP.md:51` (E10)** still specifies "Analog breath stage: in-amp receiver
  with **`REF` grounded**, gain/offset knobs." E10 is the step that must set
  `TRIM-BREATH-ZERO` `[repo: breath-receive-stage.md:199-209]` and it does not
  mention the trimmer at all.

And `breath-receive-stage.md` itself still says `REF` is grounded in two places
that were missed when the trimmer went in:

- `:68` heading — "**`REF` ties to ground**, and the polarity question dissolved twice"
- `:224` — "now that `REF` is **grounded** it touches the breath stage in no way at all"

against `:53-55,96-131,143` which all say it carries a buffered +0.437 V trimmer.
`hardware/bom.csv:28` (`U-DIFFRX`) also still reads "REF ties **HARD** to module
AGND — no divider" and "Output is **−0.44V at rest** to −10V at full", against
`hardware/bom.csv:108` (`TRIM-BREATH-ZERO`) on the same node.

**This is the single most-copied stale fact in the repository — six locations
across five files, all describing a wire that is not there.** It is also
precisely the fact whose change broke the presence comparator. Sweeping it is
the highest-value editorial action available.

One arithmetic note while in the area: `breath-receive-stage.md:57` says the
in-amp reaches "−9.6 V at full", while its own derivation gives a 9.94 V span
`[repo: :155]` from a 0 V rest. `0 − 9.94 = −9.94 V` `[calc]`, not −9.6.

---

## Assumptions checked and found sound — one line each

1. **`OE` polarity and fail-safe direction.** Active low; comparator released →
   pulled high → buffer disabled → LED out → "instrument absent". Consistent
   across `power-entry.md:138,147-150`, `digital-and-supervision.md:69`,
   `hardware/bom.csv:101`. Correct.
2. **DAC channel allocation.** pitch ch1, mods ch2–5, offset ch7, ch6 and ch8
   spare — consistent across ADR 0006:15,25, `hardware/bom.csv:12`,
   `mod-channels.md:14,20,142`. Six populated, six refreshed. Correct.
3. **`CLR` rail alignment.** The '123 and the DAC share the LM317's 5.21 V, so
   `CLR` levels are unambiguous and neither can drive the other while unpowered
   `[repo: digital-and-supervision.md:70-71]`. Correct, and the reason given is
   the right one.
4. **`R-CLR-PD` direction.** Pull-**down** = cleared = zero scale = safe, and the
   pull-up it replaced is correctly retired `[repo: digital-and-supervision.md:137-141;
   hardware/bom.csv:71]`. Correct (the BOM's `ref` is still spelled `R-CLR-PU`,
   which is a naming nuisance, not a defect).
5. **`R-SPI-PULL` count and polarity.** Six, both sides, `CS` up / `SCLK` and
   `MOSI` down on each — `digital-and-supervision.md:24-32,82` matches
   `hardware/bom.csv:49` exactly, including the reasoning about Hi-Z outputs
   leaving the *DAC's* pins floating. Correct, and it is the best-argued shared
   node on the five pages.
6. **`TRIM-BREATH-ZERO` taps raw `VREFOUT`, ahead of pitch's trim.** So pitch's
   offset trim cannot move breath's zero `[repo: breath-receive-stage.md:53-54
   vs pitch-stage.md:14]`. Correct — and it is the only one of the four
   trim/reference interactions on this node that is right by construction rather
   than by luck.
7. **Watchdog retrigger source.** DAC-side buffered `CS`, never cable-side —
   `digital-and-supervision.md:130-132` matches `hardware/bom.csv:54`. Correct,
   and the failure mode it avoids is stated accurately on both.
8. **D1/D2 split.** Three diodes, branch before them, instrument current kept out
   of the analog rail `[repo: power-entry.md:46-57; hardware/bom.csv:37]`.
   Correct and consistently stated — and it is the design principle that the
   `AGND` return problem (defect 1) quietly violates by another route.

---

## What to fix, in order

1. **Resolve `AGND`.** Rename the module analog return; redraw
   `power-entry.md:15-22`, `mod-channels.md:37`, `digital-and-supervision.md:41-43`.
   Delete `breath-receive-stage.md:164-166`.
2. **Delete "the comparator and" from `power-entry.md:149`.** The LM311 is on
   ±12 V or it cannot do its job.
3. **Finish the `k = 3` conversion in `mod-channels.md`** — lines 94, 95, 98-101,
   118-120, 145-156, 166-167 — and fix `R-MODGAIN`'s qty column (16 → 8).
4. **Fix `hardware/bom.csv:101`** (`R-OE-PU` to bus +5 V, LM311 not LM393) so the
   node has one rail.
5. **Delete "only" from `power-entry.md:41,58-60` and ADR 0005:123**, and
   re-derive ADR 0004:189-191's no-protection decision against the real load list.
6. **State the DAC-side `CS` pull-up rail (5.21 V) and `DVDD`'s rail** on
   `digital-and-supervision.md`.
7. **Sweep the six "`REF` is grounded" copies**, and rewrite `ROADMAP.md:51` to
   include `TRIM-BREATH-ZERO`.
8. **Rewrite `ROADMAP.md:191`'s rationale** before E9 runs against the wrong
   hypothesis; rewrite `ROADMAP.md:190`'s.
9. **Fix the pitch page's stale rows** (134, 135, 207-209, 215, 230) against
   `hardware/bom.csv:105`'s 200 R decision, and fix the one-sided `TRIM-OFFSET`.
10. **Correct the counts**: OPA2197 halves 11 → 9, `C-DECOUPLE` 19 → 22, BAV99
    6 → 8, LT5400 spare-section claim deleted, spare AHCT gate input tied.

---

## What this review could not determine

No vendor domain was reachable. The following are **gaps, not findings**, and no
figure has been invented for any of them:

- **`VREFOUT`'s permitted DC load and its load regulation.** ~310 µA is drawn
  from it by two trimmer networks `[calc]`. Whether that is inside spec, and how
  much it shifts the DAC's full scale, decides whether defect 6b is a rule or a
  redesign.
- **Whether the DAC8568's digital input thresholds reference `AVDD` or `DVDD`.**
  Decides whether ADR 0004:186 is correctly worded (defect 9).
- **The 74HC123's internal `C_ext` discharge resistance.** One number closes the
  "does it empty 220 nF in 250 µs" open item on paper.
- **The LT1641's pin names, foldback topology, and whether `-1` needs an `ON`
  cycle after latch-off** — already correctly flagged at `power-entry.md:113-116`.
- **The LT5400 option suffix** — already flagged at `pitch-stage.md:227-229`.
- **Whether 82 nF exists in C0G below 1210** — already flagged at
  `hardware/bom.csv:67`.
