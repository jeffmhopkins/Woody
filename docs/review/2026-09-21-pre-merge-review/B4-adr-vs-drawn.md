# B4 — Do the fourteen ADRs still describe the thing that is drawn?

**Agent B4, cold pre-merge review, 2026-09-21.** Nothing under `docs/review/**`
was read. Every claim carries provenance: `[repo] path:line`, `[calc]`,
`[from memory]`.

**Report only. Nothing in the corpus was edited.**

---

## Method

1. Built the ADR→circuit map two ways: the `adr:NNNN` edges declared in the 23
   `circuit.yaml` files, and the `adr` column of `hardware/bom.csv`
   `[repo] hardware/**/circuit.yaml`, `[repo] hardware/bom.csv`.
2. Read all fourteen ADRs, and the schematic page of every circuit each one
   governs.
3. For each disagreement, asked three questions: which side is right, does
   either say so, and does anything downstream still reason from the wrong one.
4. Checked every row of `docs/decisions/README.md` against its target file.
5. Ran no tools that mutate. The commit hook's checker reported `PASS` on every
   Bash call in this session; two findings below are things it cannot see and
   one is a thing it is actively being prevented from seeing.

### The ADR→circuit map, as declared

| ADR | Circuits declaring it | Delegation clause? |
|---|---|---|
| 0001 | `cluster/key-register`, `cluster/key-switch-network`, `interfaces/key-chain-loom`, `interfaces/spi-link` | **no** |
| 0002 | `interfaces/key-chain-loom` | **no** |
| 0003 | `carrier/breath-adc`, `interfaces/breath-sense-link`, `interfaces/spi-link`, `module/breath-output-stage`, `module/breath-receive-stage`, `module/power-entry` | **no** (0004 delegates on its behalf, for one paragraph) |
| 0004 | `interfaces/breath-sense-link`, `interfaces/spi-link`, `module/digital-and-supervision`, `module/link-supervision`, `module/panel`, `module/power-entry` | **yes**, one paragraph `[repo] docs/decisions/0004-cv-interface-module.md:231` |
| 0005 | `carrier/power-entry-instrument`, `module/power-entry`, `module/umbilical-load-switch` | **no** |
| 0006 | `module/breath-output-stage`, `module/breath-receive-stage`, `module/mod-channels`, `module/pitch-stage`, `module/power-entry` | **yes** `[repo] docs/decisions/0006-cv-channel-allocation.md:84` |
| 0009 | `carrier/display-and-service-uart`, `interfaces/key-chain-loom` | **no** |
| 0013 | `carrier/display-and-service-uart`, `carrier/power-entry-instrument` | **no** |
| 0014 | `carrier/led-strip-drive`, `module/umbilical-load-switch` | **no** |
| 0007, 0008, 0010, 0011, 0012 | none | n/a |

The convention exists and is stated twice:

> "Topology, values and derivation are in
> `hardware/module/breath-receive-stage/breath-receive-stage.md`, which supersedes this paragraph and
> ADR 0003's prose where they disagree."
> `[repo] docs/decisions/0004-cv-interface-module.md:231`

> "Where those pages disagree with the prose here, they win — that is the rule
> the breath page established and the reason it exists."
> `[repo] docs/decisions/0006-cv-channel-allocation.md:84`

**Two of the nine ADRs that govern a drawn circuit carry it.** Finding B4-07
shows what the other seven cost.

---

## Findings, highest value first

Node-indexed where a node exists. Severity is my judgement of consequence, not
of how wrong the sentence is.

---

### B4-01 — `CLR` — ADR 0004 still asserts the watchdog fires, three sections after withdrawing it. **HIGH.**

**Node:** `CLR` at `U-DAC` / `module/digital-and-supervision`.

This is a second instance of the exact class CLAUDE.md §5 names, in the ADR that
deleted the mechanism.

ADR 0004 withdraws the frame watchdog in a box:

> "**Withdrawn 2026-09-21.** The mechanism below was built and then deleted …
> **pull the umbilical mid-note and the rack holds the note until the module's
> toggle is flipped.** … The paragraphs below are kept because the problem they
> describe is still real." `[repo] docs/decisions/0004-cv-interface-module.md:484-492`

Thirty lines below that box, still inside it by position but written as live
analysis under its own `####` heading, the ADR says:

> "on a sagging cable the buck drops out at 8 V while the REF5050 and OPA2197
> hold regulation to ~7.2 V, so the MCU dies, SPI stops, **`CLR` fires**, and
> breath keeps working. Breath *still working* when everything else has parked
> is the designed behaviour, not a gap in it."
> `[repo] docs/decisions/0004-cv-interface-module.md:520-524`

**Nothing asserts `CLR` when SPI stops.** The drawn corpus is unanimous:

- "With no watchdog there is no `CLR` to fire mid-note"
  `[repo] hardware/module/digital-and-supervision/digital-and-supervision.md:82`
- "What asserts `CLR`, now that the watchdog is gone. Two things … the DAC's own
  **power-on reset** … and the **`LK-CLR` solder pad**"
  `[repo] hardware/module/mod-channels/mod-channels.md:157-161`
- "**pitch and the four mod jacks hold their last value indefinitely** — that is
  the accepted cost of deleting the frame watchdog" `[repo] ROADMAP.md:51`

So on a sagging cable the outputs do **not** park. Pitch and the four mod jacks
hold their last written value — which is precisely the "stuck CV is worse than a
dead one" failure the *same section* opens by declaring unacceptable
`[repo] docs/decisions/0004-cv-interface-module.md:478-482`. The paragraph that
was kept "because the problem it describes is still real" now contains a
sentence asserting the problem is solved, by a part that does not exist.

**Why it matters more than a stale sentence.** It is the only place in the
corpus that reasons about the *sagging-cable* brownout, as distinct from the
unplug case the ROADMAP covers. If `CLR` does not fire there, a brownout
mid-note leaves five jacks droning while breath continues to track the room —
and no page says so.

**Recommendation.** The withdrawal box's scope is ambiguous because a `####`
heading and three paragraphs of live prose sit under it without strikethrough.
Either strike the two paragraphs that assert `CLR` fires, or move the box's
closing line below them. The substantive question — what the design's answer to
a sagging-cable brownout now is — belongs in
`digital-and-supervision.md`'s *Still open*, where the same class of question
already lives.

---

### B4-02 — Analog star point — ADR 0003 defines it on a board that does not exist, and the drawn page says so where the ADR cannot see it. **HIGH.**

**Node:** analog star point / `AGND` at `J-UMB` pin 2.

ADR 0003 has a section whose entire purpose is closing this gap:

> "Several rules in this ADR refer to bonding `AGND` to 'the instrument's analog
> ground star point'. A review pointed out that **no such point was defined
> anywhere**, so the rules referenced an object that did not exist. It exists
> now …
> > **The star point is the analog ground pour on the bottom cluster board, at
> > the sensor and reference, immediately adjacent to the umbilical
> > connector.**"
> `[repo] docs/decisions/0003-breath-sensing-path.md:684-694`

**There is no bottom cluster board.** ADR 0001 settled the cluster boards as
"switches, ONE 74HC165 each, its decoupling, and that cluster's key networks"
`[repo] docs/decisions/0001-mcu-and-board-partitioning.md:84-85`; nothing analog
is on them, and `hardware/cluster/cluster-boards.md` contains no occurrence of
`analog`, `AGND`, `sensor` or `REF5050` `[repo]`. The sensor, the REF5050, both
OPA2197 halves and the ADC divider are all on the **carrier**
`[repo] hardware/carrier/carrier.md:99-136`, where the star is actually drawn:

```
  J-UMB pin 2 AGND ──[R-SER-BREATH-INST 1k]──┴── analog star point
                                               │
                                               └──[single tie]── PWR_GND
```
`[repo] hardware/carrier/carrier.md:134-137`

The schematic side has already found this and filed it — under a heading that
states the ADR is silent:

> "### Two things this drawing settles that no ADR does
> **1. The analog star point is on this board, and `AGND` is sense-only.**
> ADR 0003 names the star point as 'the analog ground pour on the bottom cluster
> board' `[repo] 0003` — **a board that does not exist**; it means this one."
> `[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:86-91`

**So both sides are wrong about each other.** The ADR thinks it defined the star
point; the schematic thinks no ADR did. Neither statement is true and neither
document can see the other, because ADR 0003 carries no delegation clause
(B4-07).

This is not cosmetic. `dig-gnd-topology` is one of five tracked-unresolved
figures `[repo] config/figures.yaml`, and `breath-sense-link.md` proposes the
open half (supply return on `PWR_GND`, `AGND` sense-only) as **Proposed**, not
decided `[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:94-110`.
The ground plan is being decided in a schematic page's proposal while the
governing ADR points at a phantom board.

---

### B4-03 — ADR 0001's Consequences still prescribe the three things ADR 0013 forbids. **HIGH.**

**Node:** carrier / `PCB-CARRIER`, `HDR-DEV`.

ADR 0001's status line and one in-body box cover the partitioning reversal
`[repo] docs/decisions/0001-mcu-and-board-partitioning.md:3-6, 68-77`. **The
Consequences section was never revisited**, and three of its five bullets are
now inverted:

| ADR 0001 Consequences | What was actually decided |
|---|---|
| "Dev boards remain the bring-up platform and are not wasted — they are **the reference the custom boards get checked against**" `:359` | There are no custom boards. The dev boards *are* the final build: "the carrier is **passive**, the dev boards plug into it and stay there, so the onboard IMU *is* the final IMU" `[repo] docs/decisions/0007-imu-selection.md:147-150` |
| "Buy a **plain** S3 dev board plus a **separate** display module … rather than an integrated-screen board that would have to be unlearned later" `:361-363` | Both selected boards are integrated: an 8×8 LED matrix board `[repo] docs/decisions/0007-imu-selection.md:142-145` and an integrated AMOLED board `[repo] docs/decisions/0008-display-selection.md:157`. ADR 0007 states the plain board is **not purchasable**: "**No ESP32-S3 board exists with a 6-axis IMU and nothing else.** Every one carries an LCD, an AMOLED, or an LED array" `[repo] docs/decisions/0007-imu-selection.md:157-159`. And ADR 0014 turns the unwanted matrix into a deliverable — "the instrument's only two-dimensional display" `[repo] docs/decisions/0014-lighting.md:13` |
| "**Custom carrier design needed eventually: USB-C, ESD protection, boot/reset, 3.3V regulation.** Espressif publishes reference designs for this." `:364-365` | "**Do not design a custom ESP32-S3 carrier.** That means taking on the module footprint, USB-C, ESD, boot and reset circuitry, power sequencing, antenna keepout and RF layout rules" `[repo] docs/decisions/0013-two-mcu-split.md:229-232`. The list is the same list, item for item, with the verdict reversed |

**This is a reader-facing hazard, not a tidiness one.** ADR 0001 is the
most-cited ADR in `hardware/**` — 26 citations, more than any other
`[repo] grep -roh "ADR 0001" hardware --include=*.md | wc -l`. Its Consequences
section is where someone starting the build looks, and it tells them to buy the
wrong part and design a board the project has decided not to design.

The ADR 0013 revision box at `:68` covers only the sentence it sits under. It
does not reach 290 lines down.

---

### B4-04 — Bonded body: ADR 0009 deleted the premise; seven ADRs still argue from it. **HIGH.**

**Node:** enclosure / `MECH-*`.

ADR 0009 supersedes it explicitly:

> "## The body comes apart
> **This supersedes the page's earlier assumption that the stack is bonded
> shut.** The section below the U-bolt already said it in one line — 'a body
> that is bonded shut is a body that is never opened again' — and then the
> construction went on bonding it. **It does not any more.**"
> `[repo] docs/decisions/0009-enclosure-construction.md:553-558`

and restates the consequence: the items in "Things that are free now and
impossible later" are "no longer *impossible* later — they are merely
expensive" `[repo] docs/decisions/0009-enclosure-construction.md:490-496`.

ADR 0002 was updated to match: "this paragraph said 'a bonded laminated body'
and meant a rebuild. Accepted either way"
`[repo] docs/decisions/0002-key-switches-and-mounting.md:92-93`.

**Nothing else was.** Twelve live occurrences across six ADRs, unmarked:

| Location | The argument it carries |
|---|---|
| `0001:160` | "in a strap-worn instrument **that is bonded shut**" — a scoring line in the per-cluster-vs-tail decision table |
| `0001:191` | "inside a body **that cannot be reopened**" — the premise of the whole key-line signal-integrity section |
| `0001:244` | "they **cannot be retrofitted** into a bonded body" |
| `0003:248` | "the most likely part to fail, in a body **that cannot be reopened**" — an argument for sensor placement |
| `0003:752` | "to a **sealed** body" |
| `0005:238` | "a **bonded body that cannot be reopened** to change the decision" — one of the reasons `SW-PWR-INST` is deleted |
| `0005:323` | "50 mW less inside the **sealed** body" |
| `0007:199` | "In a body **that cannot be opened**, two pins is a cheap price for keeping a console" — the UART0/UART1 decision |
| `0008:201` | "inside a **sealed** body" |
| `0013:294` | "Its own USB is inside a **bonded body** and reaches nothing" — the display-flashing decision |
| `0014:53` | "inside a **bonded stack that cannot be reopened**, is a liability for no benefit" — **the deciding factor** for two data lines over one chained pair |
| `0014:82-83` | "In a **bonded laminated body that cannot be opened casually (ADR 0002)**" — an argument for WS2815 over WS2812B |

**`0014:82-83` is the worst of them**, because it cites ADR 0002 as its
authority for a claim ADR 0002 has since reversed in terms. A reader who follows
that citation finds the opposite of what the sentence says.

**None of these conclusions is necessarily wrong** — ADR 0009 says the cost is
"real … but it is not the cliff this page was written against". The defect is
that eleven arguments are stated as absolutes (`cannot`, `never`, `impossible`)
when the decision behind them was downgraded to "expensive", and one of them is
a *deciding* factor (`0014:53`). The class is the one CLAUDE.md §5 names: the
grep for "bonded" finds all twelve and cannot tell you that the premise moved.

---

### B4-05 — ADR 0004's 10HP decision rests on a circuit the corpus marks *Proposed*. **HIGH.**

**Node:** `POT-RESP`, `module/breath-response-shaper`; figure `panel-width`.

ADR 0004 derives the panel width like this:

> "Then `POT-RESP` was added (see
> `hardware/module/breath-response-shaper/breath-response-shaper.md`), making
> three controls.
> **10HP is 50.50 mm**, and the win is not the width itself — **it is that three
> pots fit in one row instead of two**, which deletes a whole 20+ mm row from a
> budget that was already over."
> `[repo] docs/decisions/0004-cv-interface-module.md:744-748`

`panel-width` is `settled`, owner ADR 0004, and 10HP is in the project's
one-line description in `CLAUDE.md` `[repo] config/figures.yaml`,
`[repo] CLAUDE.md:4`.

The circuit that supplies the third pot is not accepted:

> "**Proposed 2026-09-21.** Requested after the review wave, and independently
> asked for by it"
> `[repo] hardware/module/breath-response-shaper/breath-response-shaper.md:9`

and its own Interfaces table records that even its insertion point is open:

> "`V_shaped` | out | `module/breath-output-stage` | — | Drawn feeding the gain
> attenuator. ***Where it inserts* is argued below and is open**"
> `[repo] hardware/module/breath-response-shaper/breath-response-shaper.md:26`

**Does the 10HP decision survive without it?** Partly, and that is the point —
nobody has checked. The height overrun is real before the third control
(`~115 mm against ~110 mm`, `[repo] hardware/module/panel/panel.md:19-21`), but
the *stated* win is specifically the row deletion, which needs three pots. And
ADR 0004 records that two 20 mm knobs do not fit in 8HP while 16 mm is the
ceiling `[repo] docs/decisions/0004-cv-interface-module.md:740-742` — so two pots
*do* fit in 8HP at 16 mm. Drop `POT-RESP` and the reasoning as written collapses;
whether the conclusion does is unexamined.

**Recommendation:** either accept `POT-RESP` (which needs an ADR — see B4-09) or
re-derive `panel-width` from the height budget alone. A `settled` figure should
not depend on a `Proposed` part.

---

### B4-06 — ADR 0005 is `Accepted` while containing an undecided specification, and the register has settled it without it. **MEDIUM-HIGH.**

**Node:** `C-GATE`, `U-LOADSW` (`module/umbilical-load-switch`).

ADR 0005's load-switch section specifies "**1.0 A, latch-off, with a programmed
50–100 ms ramp**" `[repo] docs/decisions/0005-power-architecture.md:262`, then
immediately says the spec cannot be met and declines to fix it:

> "**This ADR has to choose.** Either widen the specification to **50–200 ms** …
> or program the ramp with something other than the part's internal pull-up.
> **Not decided here; raised against this ADR by the wave that read the
> datasheet.**"
> `[repo] docs/decisions/0005-power-architecture.md:272-278`

The schematic page states the same fork and leaves it with the ADR:

> "**⚠ ADR 0005's '50–100 ms ramp' is not achievable with this part** … Either
> ADR 0005 widens its ramp specification to 50–200 ms, or the ramp must be
> programmed by something other than the internal pull-up."
> `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:261-266`

Meanwhile `config/figures.yaml` records it as closed:

```
  - id: loadswitch-gate-cap
    value: "82 nF, ramp 49-197 ms (98 ms typ)"
    status: settled
```
`[repo] config/figures.yaml`

**Three problems, in order:**

1. **Status.** `Accepted` means "Decided. Build to this"
   `[repo] docs/decisions/README.md:22`. ADR 0005 contains a named, open,
   two-option choice. Nothing in the status line or the index row says so, and
   the choice is not in the ADR's Consequences or any Open section — the ADR has
   neither.
2. **The register settled what the ADR did not.** `loadswitch-gate-cap` is
   `settled` at a value the governing ADR's own specification excludes. Per
   `repo-maintenance.md` §5, a disputed entry must carry `decided_by`; this one
   is not disputed, so nothing will re-check it. The 49–197 ms envelope is
   *correct* — it is derived against the banked datasheet
   `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:253-259`
   — but it contradicts a live ADR requirement, and the register is where the
   contradiction is invisible.
3. **Same shape on the current limit.** The section heading is still "Set the
   limit at 1.0 A" `[repo] docs/decisions/0005-power-architecture.md:260`; the
   drawn value is **0.940 A typical, 0.78–1.10 A guaranteed**
   `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:30-35`.
   ADR 0005 does record the 39/47/55 mV spread in a box at `:280-284`, so this
   half is refuted in place — but the heading a reader scans is not.

**Lowest-cost fix:** widen ADR 0005 to 50–200 ms, which its own box says "costs
nothing the analysis below depends on".

---

### B4-07 — Seven of the nine ADRs that govern a drawn circuit carry no delegation clause, and the cost is measurable. **MEDIUM-HIGH.**

Only 0004 and 0006 delegate (map above). The seven that do not are 0001, 0002,
0003, 0005, 0009, 0013 and 0014.

**Every one of them is currently being corrected by a schematic page that has no
standing to do it**, and in each case the correction is invisible from the ADR:

| Schematic page | Correction filed against | ADR acknowledges? |
|---|---|---|
| `breath-sense-link.md:88-91` | ADR 0003's star point ("a board that does not exist") | no |
| `breath-sense-link.md:112-117` | ADR 0003's "band-limit at both ends, around 500 Hz" — the whole filter is at the receive end, and `bom.csv` notes the ADR superseded | no |
| `umbilical-load-switch.md:261-266` | ADR 0005's ramp spec | **yes** — the one case, and only because the ADR raised it itself |
| `power-entry-instrument.md:96-100` | "**ADR 0005's load table has one 5 V column and the two-regulator decision needs it split per buck. That split is not written anywhere and it is what sizes both parts.**" | no |
| `power-entry-instrument.md:136-140` | ADR 0013 contradicting itself on where buck B lives (below) | no |
| `led-strip-drive.md:46-55` | ADR 0014's blank-at-boot rule "cannot run in the window it matters" (B4-08) | no |
| `key-chain-loom.md:138-140` | "**Six conductors is the signal count, not the conductor count**" | partly — ADR 0001 now says 12, but see B4-11 |
| `carrier.md:284` | ADR 0001's deletion of `R-TERM-CHAIN` vs a proposed `R-CHAIN-SER` doing "a different job" | no |
| `panel.md:33-35` | ADR 0004's "16–20 mm knobs" claim — "**withdrawn** rather than quietly left standing" | no |

The delegation clause is what makes this traffic legitimate rather than a second
source of truth. Adding one sentence to each of the seven is the single
highest-leverage change available in this slice, and it is the mechanism the
corpus already invented.

---

### B4-08 — ADR 0014's third defence against latched strips cannot run, and the hardware fix is unadopted. **MEDIUM-HIGH.**

**Node:** `R-LED-PD`, IO1/IO2 at `U-LVLSHIFT` (`carrier/led-strip-drive`).

ADR 0014 lists three things that break the thermal-runaway loop; the third is:

> "**Blank both strips *and the matrix* as the first act at boot**, before
> anything else initialises."
> `[repo] docs/decisions/0014-lighting.md:214-218`

The drawn page shows the window where that rule does not exist:

> "**`R-LED-PD` is new and it is the fix for a real hole.** ADR 0014's defence
> against latched strips is 'blank both strips and the matrix as the first act at
> boot' — **a firmware rule that cannot run in the window it matters.** On reset
> GPIO1 and GPIO2 are high-impedance inputs for the bootloader window (order
> 100–300 ms `[from memory]`), `OE` is tied low so the buffer is enabled, and an
> AHCT input floating near its threshold does not sit still. … that is random
> pixel data — the exact state the thermal clamp exists to prevent, at the moment
> no firmware is running to clamp it. **Two 0805s, and they cannot be added
> later.**"
> `[repo] hardware/carrier/led-strip-drive/led-strip-drive.md:46-55`

Two consequences:

1. **ADR 0014 is unamended.** Its defence-in-depth argument still reads as three
   layers when the third has a 100–300 ms hole in it, on every reset, which is
   exactly the condition the runaway scenario at `:191-202` produces.
2. **The fix is not in the BOM.** `R-LED-PD` appears in the checker's "drawn in a
   schematic, no BOM row" list `[repo] .staleness/report.txt`, and the page marks
   it `** PROPOSED **`. The page says it is unretrofittable. The module side has
   the identical protection already specified — `R-SPI-PULL` ×6
   `[repo] hardware/carrier/led-strip-drive/led-strip-drive.md:57-59` — so the
   asymmetry is an oversight, not a decision.

---

### B4-09 — Decisions visible in the schematics that no ADR records. **MEDIUM.**

Beyond the layer count and ground topology the corpus already knows about, four
circuits name no ADR anywhere — not in `circuit.yaml`, not in prose, not in
`[repo] NNNN` form `[repo] hardware/module/dac8568/dac8568.md`,
`[repo] hardware/module/panel-led/panel-led.md`,
`[repo] hardware/module/breath-response-shaper/breath-response-shaper.md`,
`[repo] hardware/carrier/breath-excitation-reference/breath-excitation-reference.md`.

Of these, two are citation hygiene and two are genuinely ungoverned:

**Ungoverned:**

1. **Analog breath response shaping (`POT-RESP`).** A third panel control, two
   op-amp halves, a panel row and the 10HP width (B4-05). No ADR mentions it —
   `POT-RESP` appears exactly once in `docs/decisions/`, in ADR 0004's panel
   arithmetic `[repo] grep -rn "POT-RESP" docs/decisions/`. ADR 0003 owns breath
   response and does not know it exists. This is a feature decision, not a
   component value.
2. **The REF5050 buffer's dual-feedback compensation.** `R-ISO-REF`,
   `R-FB-REF`, `R-FBX-REF`, `C-FB-REF` — four parts, all marked "**instrument-side
   and unretrofittable**"
   `[repo] hardware/carrier/breath-excitation-reference/breath-excitation-reference.md:98`
   — replacing a topology that had 1.5° of phase margin. Tracked as
   `riso-ref-topology` in the register but recorded in no decision.

**Citation hygiene, worth fixing because the lock is invisible otherwise:**

3. **`module/dac8568`** draws the part whose **grade letter is the whole
   decision** — "`bom.csv` is locked to `DAC8568CIPW`"
   `[repo] docs/decisions/0006-cv-channel-allocation.md:174-175` — and never
   cites ADR 0006. Its one gesture at it is oblique: "The figure's `floor` is a
   C-grade condition, not a preference"
   `[repo] hardware/module/dac8568/dac8568.md:17`. A reader on that page cannot
   reach the reasoning that makes A, B and D wrong.
4. **`module/panel-led`** is governed by ADR 0004's "The panel LED becomes an
   ordinary power indicator off the module's own rail"
   `[repo] docs/decisions/0004-cv-interface-module.md:440-441` and cites nothing.

**Also unrecorded — the layer count, confirmed and worse than "missing".**
No ADR decides 2 vs 4 layers, yet the 2-layer assumption is load-bearing in
three places: ADR 0001's carrier-area argument
`[repo] docs/decisions/0001-mcu-and-board-partitioning.md:163`, ADR 0014's
matrix-cutout cost `[repo] docs/decisions/0014-lighting.md:466`, and
`PCB-CARRIER`'s BOM row `[repo] hardware/carrier/carrier.md:295`. ADR 0013
asserts it in passing — "nothing needs more than two layers"
`[repo] docs/decisions/0013-two-mcu-split.md:250` — while the register records
it as an **open upstream decision blocking a disputed figure**:

> "decided by: The 2-layer vs 4-layer decision, which is upstream of it. On two
> layers the corpus's own requirements are mutually exclusive … **Four layers
> dissolves the conflict.**" (`dig-gnd-topology`) `[repo] config/figures.yaml`

So an `Accepted` ADR states as settled the thing the register says is open and
is blocking a figure. That is a contradiction in its own right (see B4-13).

---

### B4-10 — `datasheets/` is a top-level directory with no licence row, in breach of ADR 0011's own rule. **MEDIUM.**

**Node:** repository licensing.

ADR 0011's Consequences say:

> "**New top-level directories need a row in the table.** The root `LICENSE`
> file is the one to update"
> `[repo] docs/decisions/0011-licensing.md:77-78`

`datasheets/` is a top-level directory `[repo] ls /home/user/Woody`. It appears
in neither table `[repo] docs/decisions/0011-licensing.md:16-21`,
`[repo] LICENSE:6-12`.

It is also the one directory where the three-licence scheme cannot simply be
extended: it holds **verbatim third-party vendor PDFs** — TI, Gateron,
Worldsemi, Linear — deliberately banked rather than linked
`[repo] datasheets/README.md:1-20`. A reader applying the `docs/` row's
`CC-BY-SA-4.0` to a redistributed TI datasheet would be asserting a licence the
project cannot grant.

This is a decision with no ADR *inside* the ADR that owns the subject, which is
why I am filing it here rather than as a licensing nit. `LICENSES/` and
`.claude/` are also unrowed but are self-evidently not the project's work
product; `datasheets/` is 8 directories of material someone will redistribute.

---

### B4-11 — Cross-ADR and internal contradictions. **MEDIUM to LOW.**

Six, filed together because each is small and none is marked.

**(a) `A/C grade` — ADR 0004 permits a part ADR 0006 forbids.** ADR 0004 says
"an **A/C grade** part clears to zero scale"
`[repo] docs/decisions/0004-cv-interface-module.md:497`. ADR 0006 corrects
exactly that spelling: "**Not 'A or C', which this line used to say.** The grade
letter selects the **reference gain** as well as the reset state … **An A-grade
part halves every output** — pitch becomes −2…+2.25 V, the mods ±5 V, and
channel 7 cannot reach its reference voltage at all. **Only C satisfies both
requirements.**" `[repo] docs/decisions/0006-cv-channel-allocation.md:171-175`.
The reset-state claim in ADR 0004 is *true* (A and C both clear to zero scale,
confirmed against SBAS430E `[repo] docs/decisions/0006-cv-channel-allocation.md:181-184`)
— which is what makes it dangerous, because the sentence is not wrong enough to
trip a reader, and following it to an A-grade part halves the instrument.

**(b) Panel control count — ADR 0006 says two, ADR 0004 says three.** ADR 0006's
headline channel table gives breath "GAIN 0.5–4×, OFFSET ±5 V"
`[repo] docs/decisions/0006-cv-channel-allocation.md:12`; ADR 0004 says
"`POT-RESP` was added … making three controls"
`[repo] docs/decisions/0004-cv-interface-module.md:744-745`; `panel.md` builds
the layout around three `[repo] hardware/module/panel/panel.md:24-35`. ADR 0006's
table is the one most readers will hit first.

**(c) Free GPIO on the real-time board — 12, 14, 17.** ADR 0014 argues option B
"against roughly 17 broken out and **12 needed** on the real-time board
(ADR 0007)" `[repo] docs/decisions/0014-lighting.md:55`. ADR 0007 says
**14 of 17**, spare 3, 4, 33
`[repo] docs/decisions/0007-imu-selection.md:194`; ADR 0013 agrees, "14 of 17
broken out, three spare" `[repo] docs/decisions/0013-two-mcu-split.md:57`.
So ADR 0014's argument spends one of three spare pins while claiming five are
free, and cites ADR 0007 for a number ADR 0007 does not contain. The conclusion
holds; the margin quoted for it is 67 % too generous.

**(d) ADR 0013 vs ADR 0013 — where buck B lives.** The build-approach list puts
both regulators on the carrier: "the carrier holds only … **Two** R-78E5.0
regulator modules — one per dev board"
`[repo] docs/decisions/0013-two-mcu-split.md:245-247`. The reasoning that
justifies two says the opposite: "give each board its own regulator from the
umbilical +12V, **with local bulk capacitance on the display board, so WiFi
bursts are absorbed locally** rather than reaching the analog section"
`[repo] docs/decisions/0013-two-mcu-split.md:131-133`. The display board is
360 mm from the carrier by ADR 0013's own table
`[repo] docs/decisions/0013-two-mcu-split.md:178`. The drawn page has already
filed it and cannot resolve it:

> "**Where buck B lives.** ADR 0013's carrier list puts both regulators here;
> ADR 0013's own reasoning wants the display board's WiFi transients absorbed
> locally, which a regulator 360 mm away does not do. … Pick one before
> `J-DISP`'s conductor list is fixed."
> `[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md:136-140`

Note the deadline in that last sentence — it is a connector conductor count, so
it becomes unretrofittable.

**(e) ADR 0012 recommends the display ADR 0008 rejected.** "That materially
changes ADR 0008. **A small OLED**, previously marginal because a four-channel
routing matrix needed depth to navigate, **is now comfortable and arguably
preferable.**" `[repo] docs/decisions/0012-configuration-interface.md:99-101`.
ADR 0008 selected AMOLED and states "This supersedes an earlier lean toward a
monochrome OLED" `[repo] docs/decisions/0008-display-selection.md:25`, then
selected a specific board `[repo] docs/decisions/0008-display-selection.md:3`.
ADR 0012's paragraph is unmarked and points at a reversed decision.

**(f) ADR 0001's conductor breakdown does not add to its own total.** The table
row reads "**12 per hop** — 6 signals-and-supply, 5 grounds, 2 spare"
`[repo] docs/decisions/0001-mcu-and-board-partitioning.md:135`. 6 + 5 + 2 = 13
`[calc]`. The correct breakdown is 4 signals + `3V3` + 5 grounds + 2 spare = 12,
which is what the ADR's own diagram
`[repo] docs/decisions/0001-mcu-and-board-partitioning.md:250-252` and the loom
page both give: "`GND SCK GND SH/LD GND SER GND QH GND 3V3 spare spare`"
`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:209`. `12` is the
tracked value (`chain-conductors`, owner ADR 0001), so the register is right and
one line of its owner is not.

---

### B4-12 — Arguments that survived their own refutation, smaller than B4-01/03/04. **MEDIUM to LOW.**

**(a) ADR 0006 credits firmware with shaping a signal firmware cannot reach.**

> "Firmware still shapes the response curve **upstream of the DAC**. The knobs
> fit the *range* to the patch; the firmware shapes the *feel*."
> `[repo] docs/decisions/0006-cv-channel-allocation.md:339-340`

The sentence sits under "## Breath knobs are analog, in the signal path", and
ADR 0006's own decision table says "**Breath never enters the digital path on
its way out**" `[repo] docs/decisions/0006-cv-channel-allocation.md:18`. There
is no DAC in the breath path, so nothing can be upstream of it, and the
knobs/firmware division of labour the sentence describes does not exist for the
CV. The schematic side states the consequence flatly: "**This module has two
knobs and no shaping at all**"
`[repo] hardware/module/breath-response-shaper/breath-response-shaper.md:14`.
*Caveat, because it changes the fix rather than the finding:* firmware does
shape the **digital copy** (MIDI/USB), which ADR 0006 elsewhere treats as a
separate representation with separate authority `[repo] :285-287`. The sentence
is defensible if it means the copy and wrong if it means the jack, and its
placement says the jack. Rewriting it to name which representation it governs
costs one clause and removes the reason `POT-RESP` had to be discovered by a
review rather than derived.

**(b) ADR 0012's config-mode entry points at a pool that was consumed.**

> "The radio is off by default and during performance. It is enabled explicitly,
> by entering config mode — **one of the spare shift-register inputs (ADR 0010)**
> or a gesture."
> `[repo] docs/decisions/0012-configuration-interface.md:80-82`

The 14 spare bits have since been allocated in full: **8 marker, 3 reserved
spare switches, 3 free** `[repo] config/key-layout.yaml:138-141`. The three
reserved ones are named — octave up, octave down, hold/preset
`[repo] config/key-layout.yaml:131` — and none is config mode. The three "free"
bits explicitly **cannot become inputs**: "A free bit has no plate cutout and no
switch. The body bonds shut. You cannot add a switch to one without cutting the
plate, and the plate is generated at M3 and fitted before bonding"
`[repo] hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:56-61`.

ADR 0012's Open section does still list "Whether config mode is entered by a
physical input or a key gesture" `[repo] docs/decisions/0012-configuration-interface.md:130`,
so the ADR is honest overall — but the decision paragraph offers a mechanism
that no longer has anywhere to land, and it attributes the pool to ADR 0010,
which does not allocate it (ADR 0001 and `key-layout.yaml` do).

*Note in passing:* the argument quoted above from `key-marker-and-bits.md` is
itself resting on "the body bonds shut" (B4-04). Here it survives, because the
binding constraint it actually names is the **plate**, generated at M3 and
fitted before assembly — not the bonding. Worth rewording for the same reason
the others are.

**(c) ADR 0013's headroom claim.** "Worth revisiting only if the S3 turns out to
struggle with loop determinism, which is not expected at **13 pins** and one
job." `[repo] docs/decisions/0013-two-mcu-split.md:286-287`. The table 230 lines
above totals **18 on the chip, 14 broken out**
`[repo] docs/decisions/0013-two-mcu-split.md:53`, and the ADR records that "An
earlier version of this table showed 14 pins and one shared host, and was wrong"
`[repo] :66`. So the corpus now carries three numbers for one quantity and 13 is
none of them.

**(d) ADR 0001's SPI3 headroom.** "Two extra pins against **sixteen of
headroom**" `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:117`.
Against the selected board it is **three spare of seventeen**
`[repo] docs/decisions/0007-imu-selection.md:194`. The pins are still available;
the margin quoted is off by 5×.

---

### B4-13 — Status accuracy and the hand-maintained index. **MEDIUM.**

All fourteen ADRs read `Accepted` `[repo] grep "^\*\*Status:\*\*" docs/decisions/0*.md`.
All fourteen index rows read `Accepted` `[repo] docs/decisions/README.md:37-52`.
The three rows the index's own warning names — 0007, 0008, 0011 — now match
their targets, so that warning is a historical note that has been acted on
`[repo] docs/decisions/README.md:29-35`.

**Row-by-row, three still disagree with their target:**

1. **0008.** The row reads "Accepted. Board selected: LilyGO T-Display-S3
   AMOLED" `[repo] docs/decisions/README.md:44`. The file says "**(base, not
   Plus)**" `[repo] docs/decisions/0008-display-selection.md:3` — and the
   distinction is load-bearing, since the Plus is the touch variant and "Touch
   is redundant with configuration on a phone, and it costs pins and complexity"
   `[repo] docs/decisions/0008-display-selection.md:198-199`. The row is the
   short form someone orders from.
2. **0008, again.** The file records two supersessions the row does not:
   "**Revised by ADR 0012**" in its Context
   `[repo] docs/decisions/0008-display-selection.md:7` and "Superseded in effect
   by [ADR 0013] … The display board now needs four pins, not ten"
   `[repo] docs/decisions/0008-display-selection.md:63-66`. Compare 0001, whose
   row *does* carry "(partitioning revised by 0013)". The index is inconsistent
   with itself about whether revision belongs in the row.
3. **0005.** `Accepted` with no qualifier, against an ADR containing "**Not
   decided here**" for the ramp specification (B4-06). Under the index's own
   definitions — `Accepted` = "Decided. Build to this", `Open` = "Options
   identified, decision not made"
   `[repo] docs/decisions/README.md:21-23` — one section of 0005 is `Open` and
   there is no vocabulary for that.

**The structural point the index already makes about itself is the right one.**
"Each row restates a fact its own target owns, which is rule 1 in `CLAUDE.md`
broken in the project's own index. **It should be generated from the
`**Status:**` line of each ADR.**" `[repo] docs/decisions/README.md:32-34`. Five
minutes of `tools/` would delete this finding class permanently, and the repo
already has the pattern — `merge-bom.py --check` and `merge-manifests.py`
`[repo] docs/reference/repo-maintenance.md:§3-4`. Findings 1 and 2 above would
not exist with a generated table; finding 3 needs a fourth status value, or an
Open section in 0005.

**Section-level supersession — audited, and it is in good shape.** Every
superseded block I found is marked, most with a date and a reason:
`0001:68` (partitioning), `0001:236` (C-KEY figures), `0001:284` (series
termination, struck), `0001:379` (marker allocation), `0002:92` (bonded body),
`0002:154` (plate thickness, with a ✅ and the drawing), `0004:42` (conductor
budget), `0004:390` (SPI pulls and OE gating, struck), `0004:484` (watchdog),
`0004:744` (panel width), `0005:60` (sensor off the 5 V rail), `0005:104`
(umbilical voltage argument demoted to historical), `0005:264` (ramp),
`0005:357` (`R-PD-BREATH`, struck), `0006:122` (LT5400 ratio), `0006:164`
(grade lock), `0006:171` (A-or-C), `0006:218` (breath power-on row),
`0008:63` (pin budget), `0008:137` (C6 gate, struck), `0009:366`, `0009:493`,
`0009:555` (bonded body), `0010:131` (arc versus line), `0013:150`
(placement table), `0013:238` (shift registers, struck), `0013:292` (flashing
route) `[repo]`.

**The failure is not in the marking. It is that marking a block does not reach
the places that reason from it** — B4-01 (0004 withdrew the watchdog, then
asserted it fires), B4-03 (0001's box did not reach its Consequences 290 lines
down), B4-04 (0009 marked it; six other ADRs never heard), B4-11(a)
(0006 corrected "A or C"; 0004 still says it). All four are cases of a correct
supersession mark and an uncorrected downstream reader — which is exactly
CLAUDE.md's opening paragraph, restated at the level of arguments instead of
values.

---

### B4-14 — A `forbidden` pattern in `config/figures.yaml` forbids a true statement, and an accidental keyword is the only thing keeping the build green. **MEDIUM.** *(Register defect, found while checking B4-11(f). Reported because it is a live trap.)*

`key-pullup-qty` lists:

```
    forbidden: ["21 pull-ups", "Twenty-one sets"]
```
`[repo] config/figures.yaml:208`

ADR 0001 contains the literal string:

> "Twenty-one sets across the four boards, so the three reserved spare-switch
> bits are covered too."
> `[repo] docs/decisions/0001-mcu-and-board-partitioning.md:217`

**Two things are wrong, and they cancel out today.**

1. **The sentence is correct and should not be forbidden.** "Sets" means the
   full `R-KEY-PU` / `R-KEY-SER` / `C-KEY` network, and there are 21 of those —
   `R-KEY-SER` qty 21, `C-KEY` qty 21 `[repo] hardware/bom.csv:35-36`. The
   drawn page says the same thing in the same words: "Every position above gets
   the full `R-KEY-PU`/`R-KEY-SER`/`C-KEY` network … — **21 sets**, which is what
   `bom.csv` budgets"
   `[repo] hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:43-45`.
   The figure's value of 24 is the `R-KEY-PU` count alone, correctly derived as
   "21 switch positions + 3 free bits" `[repo] config/figures.yaml`. Different
   quantities; the forbidden pattern conflates them.
2. **The checker is not catching it anyway, for an unrelated reason.** The
   `REFUTATION` regex includes `rather than`
   `[repo] tools/check-staleness.py:64-66`, and refutation is judged on every
   line the match touches `[repo] tools/check-staleness.py:177-182`. Line 217
   happens to read "…**rather than** 265 mm of loom. Twenty-one sets across
   the…". The hit is filed as "refuted in place" and never surfaces. `PASS` on
   every run this session `[repo] PreToolUse hook output`.

**Why this is worth a finding rather than a shrug.** Reflow that paragraph —
delete "rather than 265 mm of loom", or let the sentence wrap differently — and
the commit hook starts failing on a true statement in an ADR, with a message
saying the value is stale. The next person's cheapest move is to "fix" ADR 0001
to say 24 sets, which would be wrong: there are 21 networks and 24 pull-ups.
`repo-maintenance.md` §5 names `false_positive_note` as "the one that earns its
keep — it tells the next person why a legitimate occurrence of a forbidden
string is allowed, so they do not 'fix' it"
`[repo] docs/reference/repo-maintenance.md`. This entry has none.

**Recommendation:** drop `"Twenty-one sets"` from the forbidden list (it was
never a spelling of 24), keep `"21 pull-ups"`, and add a `false_positive_note`
recording that 21 sets and 24 pull-ups are both correct and different.

---

## What I checked and found clean

Recorded because a cold reviewer's negative results are worth as much as the
positive ones, and because "not mentioned" reads as "not checked".

- **ADR 0006 ↔ `module/mod-channels`, `module/pitch-stage`.** The two-resistor
  non-inverting topology, `k = 3`, `V_ref` = 3.3333 V from channel 7, and the
  `4·Vdac − 3·V_ref` = ±10 V span all agree between ADR and page, and the ADR's
  superseded four-resistor/LT5400 form is struck in place at both ends
  `[repo] docs/decisions/0006-cv-channel-allocation.md:80-95, 122-123`,
  `[repo] hardware/module/mod-channels/mod-channels.md:7-16`. `[calc]`:
  4 × 5.000 − 3 × 3.3333 = +10.00 V; 4 × 0 − 3 × 3.3333 = −10.00 V. This is the
  best-maintained ADR/schematic pair in the corpus and it is the one with a
  delegation clause.
- **ADR 0006 ↔ `module/breath-output-stage`.** "GAIN 0.5–4×, OFFSET ±5 V"
  matches the drawn attenuator: 0.125…1.000 × a fixed ×4
  `[repo] hardware/module/breath-output-stage/breath-output-stage.md:103-106`.
  `[calc]`: 7.15/(7.15+50) = 0.1251; × 4 = 0.500.
- **ADR 0014 ↔ `carrier/led-strip-drive`, option B.** Two independent data lines,
  drawn as IO1 and IO2 through separate 74AHCT125 gates
  `[repo] hardware/carrier/led-strip-drive/led-strip-drive.md:30-39`, and
  assigned as GPIO 1, 2 in ADR 0007's pin table
  `[repo] docs/decisions/0007-imu-selection.md:191`. Three documents, one answer.
- **ADR 0005 ↔ `carrier/power-entry-instrument`.** "There is no fuse and no power
  switch on this board (ADR 0005)"
  `[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md:59-60`;
  `SW-PWR-INST` appears in no BOM row, placed or unplaced
  `[repo] hardware/bom.csv`, `[repo] hardware/unplaced.csv`. A deletion that
  landed everywhere, which is rare enough to name.
- **Every refdes in every ADR resolves to a BOM row**, except `SW-PWR-INST`
  (correctly deleted, above) `[repo] cross-check of ``…`` tokens in
  `docs/decisions/*.md` against `hardware/bom.csv` + `hardware/unplaced.csv``.
  No ADR depends on a part that vanished from the BOM — the failures in this
  report are all about *arguments*, not parts, which is consistent with what the
  register and `merge-bom.py` already mechanise.
- **Every BOM row carries an `adr` value.** No orphans in either file
  `[repo] Counter over the ``adr`` column: 138 rows, 0 blank`.
- **ADR 0007's board verification** (QMI8658C 6-axis, native USB not a bridge,
  17 GPIO not 16) is method-marked and traceable
  `[repo] docs/decisions/0007-imu-selection.md:161-183`. The "Seventeen, not
  sixteen" correction did propagate to ADR 0013 `[repo] :57`. It did not reach
  ADR 0014 — B4-11(c).
- **ADR 0009 ↔ the tail.** Matrix window, carrier cutout, USB-C slot and
  etherCON all appear on both sides with the same constraints
  `[repo] docs/decisions/0009-enclosure-construction.md:259-290`,
  `[repo] docs/decisions/0013-two-mcu-split.md:199-203`.
- **ADR 0010 ↔ `config/key-layout.yaml`.** 18 switches, 4 clusters, 32 bits,
  roles and cluster assignment all agree, including the three `role: control`
  right-thumb keys ADR 0007 depends on
  `[repo] config/key-layout.yaml:67-95, 119-122`.
- **ADR 0004's umbilical pin map** matches `carrier.md`'s connector drawing
  conductor for conductor `[repo] hardware/carrier/carrier.md:50`, against
  `umbilical-pinmap` `[repo] config/figures.yaml`.

---

## Summary

| # | Finding | Class | Severity |
|---|---|---|---|
| B4-01 | ADR 0004 asserts `CLR` fires on SPI loss; the watchdog is deleted | survived refutation | High |
| B4-02 | ADR 0003 defines the analog star point on a board that does not exist | ADR vs drawn | High |
| B4-03 | ADR 0001's Consequences prescribe three things ADR 0013 forbids | survived refutation / cross-ADR | High |
| B4-04 | Twelve bonded-body arguments in six ADRs; ADR 0009 deleted the premise | survived refutation | High |
| B4-05 | ADR 0004's 10HP width rests on a `Proposed` circuit | ADR vs drawn | High |
| B4-06 | ADR 0005 is `Accepted` with an undecided ramp spec the register settled anyway | status / register | Med-High |
| B4-07 | 7 of 9 governing ADRs carry no delegation clause; 9 live corrections filed against them | convention | Med-High |
| B4-08 | ADR 0014's blank-at-boot defence cannot run; `R-LED-PD` unadopted | survived refutation | Med-High |
| B4-09 | `POT-RESP`, the REF5050 compensation, and the layer count have no ADR | no ADR | Medium |
| B4-10 | `datasheets/` has no licence row, breaching ADR 0011's own rule | no ADR | Medium |
| B4-11 | Six cross-ADR / internal contradictions (a–f) | cross-ADR | Med-Low |
| B4-12 | Four smaller surviving refutations (a–d) | survived refutation | Med-Low |
| B4-13 | Two 0008 index rows disagree with target; no status value fits 0005 | status / index | Medium |
| B4-14 | A `forbidden` pattern forbids a true sentence; `rather than` is hiding it | register | Medium |

**The pattern across the high-severity findings.** Every one is a *correctly
marked* supersession whose downstream readers were not updated — ADR 0004
withdrew the watchdog and then reasoned from it, ADR 0001's revision box did not
reach its own Consequences, ADR 0009 deleted the bonded body and six ADRs never
heard. The corpus is already good at marking the block where the change happens.
It has no mechanism at all for the second half, which is the same sentence as
CLAUDE.md's opening — "Fixes land where the editing is happening; they do not
land where the *reader* looks" — with arguments in place of values.

**The two cheapest structural fixes, both of which the repo has already invented
elsewhere:**

1. **Generate `docs/decisions/README.md`'s table from the `**Status:**` lines.**
   The index says this about itself `[repo] docs/decisions/README.md:34`; it
   deletes B4-13 items 1 and 2 permanently, and the tooling pattern exists in
   `merge-bom.py --check`.
2. **Add the delegation clause to the seven ADRs that lack one** (B4-07). It is
   one sentence each, it is the corpus's own invention, and it converts nine
   unsanctioned corrections into legitimate ones. It would not have prevented
   B4-01 through B4-04 — those need a reader — but it is what makes the reader's
   findings land somewhere with standing.
