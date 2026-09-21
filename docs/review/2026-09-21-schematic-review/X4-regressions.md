# X4 — Regression sweep over today's changes

**Scope:** commits `541ce12`…`b9beb48`, all dated 2026-09-21. Hunting for things
that were **true when written and became false later the same day**, not fresh
design flaws.

**Method:** read every commit message in the range and diffed the files each one
touched against the files it did *not* touch. The productive question turned out
to be not "what changed" but "which commit changed a number, and which documents
quoting that number were not in that commit's file list".

**Evidence marking.** Every row is `[repo]` (file and line, read today),
`[git]` (a commit I read, sha given), or `[from memory]`. I have used
`[from memory]` only where I reason about circuit behaviour rather than repeat
something the repo says. Where a claim is my *inference* from two repo facts I
say so explicitly rather than laundering it as `[repo]`.

**Headline.** The two known regressions are fixed. Nine more are not. The
pattern is mechanical and identifiable: **six commits today edited a schematic
page or the BOM without touching the ADR that owns the decision.**
`fd3e183` and `3d8b7e1` never touched `ROADMAP.md`, `ADR 0003` or `ADR 0004`;
`b9beb48` never touched `ADR 0004`; `0f2eeb6` never touched `ADR 0006`'s grade
paragraph. Everything in Tier 1 below falls out of exactly those four gaps.

---

## Tier 1 — a build, a purchase or a firmware write would act on these

| # | File : line | Says now | Should say | Evidence |
|---|---|---|---|---|
| 1 | `firmware/README.md:49–50` | mod offset is "the shared **2.5 V** from DAC channel 7", transfer function `Vout = 4 × (Vdac − Voffset)` | `V_ref = 3.3333 V`; the stage is the two-resistor non-inverting form `Vout = 4·Vdac − 3·V_ref` | `[repo]` firmware/README.md:49–50; `[repo]` bom.csv:68 "V_ref = 3.3333V"; `[git] fd3e183` |
| 2 | `docs/decisions/0006:143` | "So specify an **A or C grade** part" | **C grade only** — `DAC8568CIPW` | `[repo]` 0006:143; `[repo]` bom.csv:12 "GRADE LOCKED TO C"; `[git] 0f2eeb6` |
| 3 | `hardware/bom.csv:68` | `R-MODGAIN` **qty = 16** | **8** (the note in the same cell says "EIGHT, not sixteen") | `[repo]` bom.csv:68; `[git] fd3e183` changed value and note, left qty |
| 4 | `hardware/bom.csv:43` | `C-DECOUPLE` **qty 19**, derived from "5 x OPA2197 on +/-12V = 10 … LM393" | **21** — 6 × OPA2197 = 12 pins; and the part is **LM311** | `[repo]` bom.csv:43 vs bom.csv:13 (qty 6) and bom.csv:99 (LM311) |
| 5 | `hardware/bom.csv:101` | `R-OE-PU`: "**FROM THE LM317'S 5.21V, NOT BUS +5V**" | **bus +5 V** | `[repo]` bom.csv:101 vs `[repo]` power-entry.md:135–143 and digital-and-supervision.md:60,69; `[git] b9beb48` |
| 6 | `hardware/module/mod-channels.md:93–96` | Values table: `R1,R3 10 kΩ` / **`R2,R4 40.2 kΩ`** / **`V_OFF 2.500 V`** | `R1 10 kΩ`, `R2 30 kΩ`, one pair per channel; `V_OFF 3.3333 V` | `[repo]` mod-channels.md:93–96 vs its own diagram at :14,:31 and bom.csv:68 |
| 7 | `hardware/module/pitch-stage.md:130–135` | Component table carries `TRIM-GAIN 1 kΩ / ±5 %`, `TRIM-OFFSET … wiper through R-OFFINJ`, `R-OFFINJ 470 kΩ`, `C-FILT-PITCH 10 nF` | `TRIM-GAIN 200 Ω, 0→+2 %`; `R-OFFINJ` **deleted**; `C-FILT-PITCH` **deleted**, replaced by `C-FB-PITCH 1 nF` | `[repo]` pitch-stage.md:130–135 vs its own diagram at :29,:35 and :166,:192; bom.csv:105–107 |
| 8 | `docs/decisions/0001:179` | the 21 sets of `R-KEY-PU`/`R-KEY-SER`/`C-KEY` sit "on the **cluster board**" | at the register inputs **on the carrier** — there is no cluster board | `[repo]` 0001:179 vs 0001:116–124 (same ADR, 55 lines earlier), bom.csv:73,90,92; `[git] 7c68404` |
| 9 | `hardware/module/digital-and-supervision.md:52–57` | ASCII schematic draws the presence detect from the **in-amp output**, "0 V absent, −0.44 V alive", "threshold −200 mV (from −12 V)" | BREATH node against `AGND`, 0 V / +0.2 V, **threshold +100 mV, positive**, no negative reference | `[repo]` digital-and-supervision.md:52–57 vs its own prose at :108–113 and bom.csv:99–100 |
| 10 | `docs/decisions/0004:370–383` | `−437 mV` alive; "a fixed threshold — say **−200 mV**"; "**Grounding `REF`** (ADR 0003) turns the detect into a comparison against a rail"; "an **LM393** half … the second half of the package is spare" | +0.2 V alive at the BREATH node; +100 mV; `REF` is **trimmed**, not grounded; **LM311**, a single comparator with no spare half | `[repo]` 0004:370,372,380–381,383 vs bom.csv:99–100, digital-and-supervision.md:108–122; `[git] 0f2eeb6`, `[git] fd3e183`, `[git] b9beb48` |
| 11 | `docs/decisions/0003:370–371` and `0003:574–575` | "`REF` ties to module analog ground"; "the in-amp's `REF` pin ties to module analog ground **and stays there**" | `REF` is driven from a buffered `TRIM-BREATH-ZERO` at **+0.437 V** divided from `VREFOUT` | `[repo]` 0003:370–371,574–575 vs bom.csv:108 and breath-receive-stage.md:53–55,84–85,143; `[git] fd3e183` |
| 12 | `ROADMAP.md:51` (E10) | "Analog breath stage: in-amp receiver with **`REF` grounded**, gain/offset knobs" | `REF` trimmed; and E10 must now include **"set `TRIM-BREATH-ZERO` until the in-amp output reads 0 V"** as a commissioning step | `[repo]` ROADMAP.md:51 vs breath-receive-stage.md:197–209 |
| 13 | `ROADMAP.md:191` (E9) | "Confirms the **plain series RC** is unconditionally stable where an **in-loop version would not have been**" | The design *is* now the in-loop version. This row is a **gate on the highest-risk change in the module**, not a reassurance about the topology that was dropped | `[repo]` ROADMAP.md:191 vs pitch-stage.md:173–175 and 0006:610–612 ("now a gate rather than a reassurance"); `[git] fd3e183` |

### Notes on the Tier 1 rows

**#1 is the one I would fix first.** It is not a stale prose number — it is the
value a firmware author writes into DAC channel 7. `[from memory]` With the
two-resistor network now in the BOM (`R1 = 10 k`, `R2 = 30 k`, `k = 3`), writing
2.5 V gives `Vout = 4·Vdac − 7.5`, i.e. a −7.5…+12.5 V window: wrong span, and
clipping at the positive end. The intended `3.3333 V` gives exactly ±10.000 V.
`firmware/README.md` is also the document `latency-budget.md:62,154` and
`0006`'s statelessness argument both point at for the refresh rule, so it is
read.

**#2 is the one a purchase would act on.** `0f2eeb6` established that the
DAC8568 grade letter selects **reference gain**, not just reset state, and that
an A-grade part halves pitch span, mod span, and cannot reach the offset
channel's value at all `[git] 0f2eeb6`. It locked `bom.csv:12` to C. It did not
touch `0006:143`, which still authorises an A grade. The prior-art report that
produced the finding says in terms *"Amend ADR 0006's grade paragraph the same
way"* `[repo]` docs/research/2026-09-21-eurorack-prior-art/R7-multichannel-dac.md:675
— the instruction was written down and not carried out.

**#5 is a live three-way disagreement about a net.** `0f2eeb6` moved the
comparator pull-up off the bus rail to the LM317's 5.21 V, with an argument
(supervision must not die with the rail it supervises) `[git] 0f2eeb6`.
`b9beb48` then moved it *back* to bus +5 V, with a different argument (the OE
pins are inputs on a bus-rail part; pulling them to a higher rail pushes the
input clamp) and wrote that into both new schematic pages `[git] b9beb48`
`[repo]` power-entry.md:135–143, digital-and-supervision.md:69. It updated
`R-LED-PANEL` in the BOM and **not** `R-OE-PU`, which still carries the
superseded instruction in shouting capitals. `ADR 0004:383` independently says
bus +5 V. **A reader cannot tell which is current**: the BOM note is the most
emphatic and the most recent-looking, and it is the wrong one.

**#9 and #10 together are the unfixed half of a fix that was announced as
complete.** `b9beb48`'s message says the broken presence detect was *"Fixed by
tapping ahead of the trim"* `[git] b9beb48`. What was actually fixed is the BOM
(`U-PRESENCE`, `R-PRESENCE` — verified in the diff `[git] b9beb48`). The
schematic page created in the same commit still **draws** the broken version,
and `ADR 0004` — the ADR that owns the presence detect and is cited by both —
was not touched at all. So the circuit is described correctly in exactly one of
the three places that describe it.

---

## Tier 2 — contradictions where two documents disagree and neither is marked

These will not be soldered wrong, but a reader cannot tell which document is
current, which is the failure mode `aabd8ca` was written to attack `[git] aabd8ca`.

| # | Where | The disagreement | Evidence |
|---|---|---|---|
| 14 | `digital-and-supervision.md:115–116` and `:150–151` | **An honesty marker pointing backwards.** The page says *"The BOM's `R-PRESENCE` note still describes the old −200 mV arrangement **and is wrong**"*, and lists "a corrected `R-PRESENCE` row" under *Still open*. The BOM row was corrected **in the same commit that wrote those sentences**. The stale document is the one making the accusation. | `[repo]` digital-and-supervision.md:115–116,150–151 vs `[git] b9beb48` diff of bom.csv:100 |
| 15 | `breath-receive-stage.md:68` and `:222–224` | Section heading still reads "**`REF` ties to ground**", and the watchdog section says "**now that `REF` is grounded** it touches the breath stage in no way at all" — on a page whose next section is titled "Why `REF` is trimmed rather than grounded" | `[repo]` breath-receive-stage.md:68,96,222–224; `[git] fd3e183` rewrote the page around both sentences |
| 16 | `ROADMAP.md:212` | "Stale breath zero" is listed as **made loud by** "Continuous auto-zero (ADR 0006), plus showing the current zero on the display". Firmware's auto-zero now corrects **only the digital copy** and E10 explicitly says a flat bar on the screen is no longer evidence about the jack — so the named fix no longer addresses the named failure | `[repo]` ROADMAP.md:212 vs ROADMAP.md:135 (F2, correctly updated), breath-receive-stage.md:216–218, 0003:567–571; `[git] 0b1cfc6` |
| 17 | `ROADMAP.md:190` | E9 "Pitch DC load sweep … **Quantifies the 1 kΩ divider error** against the real patch, and tells you how much a re-mult actually shifts tuning" — the divider error is gone for any load | `[repo]` ROADMAP.md:190 vs 0006:601–602 "The load-divider error is gone, for any load"; `[git] fd3e183` |
| 18 | `ROADMAP.md:49` (E8) and `0006:417` | "The 5 %-over kludge is deleted — **trimmers go both ways**". `TRIM-GAIN` is a *series* trimmer and `pitch-stage.md:130` says in terms that it is "**0 → +5 % of ratio, one-sided** — a series trimmer can only add … it is not ±5 % and an earlier revision said it was" | `[repo]` ROADMAP.md:49, 0006:417, pitch-stage.md:130 |
| 19 | `0006:380` and `0006:391` | The trimmer tempco table offers 5 / 10 / 20 % rows and the text concludes "**Keep the trim range small — 5 to 10 %**". `TRIM-GAIN` is now 200 Ω = **2 %**, stated 11 lines *earlier* in the same ADR (`0006:360–365`). The ADR contradicts itself within one section. | `[repo]` 0006:360–365 vs 0006:380,391; bom.csv:105 |
| 20 | `pitch-stage.md:215` | Cites the ADR's 2.4 cents against the page's 0.4 cents as "**not reconciled**" — both figures are for a 5 % trimmer that no longer exists. The unreconciled disagreement is now between two dead numbers. | `[repo]` pitch-stage.md:215 vs 0006:380; bom.csv:105 |
| 21 | `0006:427–500` | The entire section "**The pitch output keeps its 1 kΩ series resistor**" still argues that the divider stays and calibration absorbs it, and that jack-side feedback "**costs more than it returns** … real stability work, on a board without one". `0006:589–612` reverses all of it. Neither section carries a pointer to the other, and `0006:602` says the −11.9/−23.5 figures are "**below**" when they are 165 lines **above**. | `[repo]` 0006:442,473,602 vs 0006:593–612 |
| 22 | `0006:150` | Power-on table: "**Breath \| 0 V \| The receiver's differential pulldown holds it there**". The differential pulldown was **deleted** (`breath-receive-stage.md:192`), and see #26 below for why breath is *not* at 0 V at power-on. | `[repo]` 0006:150 vs breath-receive-stage.md:139,192 |
| 23 | `hardware/bom.csv:4` | `U-MCU-RT`: "**16 GPIO broken out** (1-7, 34-40, 43, 44) vs 14 needed", and "confirm quad at E1" framed as a gate | **17**, and PSRAM is no longer a gate | `[repo]` bom.csv:4 vs 0013:57 ("14 of 17 broken out, three spare") and ROADMAP.md:188 ("No longer a gate … 17 broken out"); `[git] dfc3c67` |
| 24 | `hardware/bom.csv:42` | `R-OUT-PROT` note: "On pitch it is **a load divider the gain trim and firmware absorb** (ADR 0006)" | On pitch it is now inside the DC feedback loop and divides nothing | `[repo]` bom.csv:42 vs pitch-stage.md:144–164; `[git] fd3e183` |
| 25 | `hardware/bom.csv:71` vs `digital-and-supervision.md:41,137` | Same part, two reference designators: BOM calls it **`R-CLR-PU`** (while the description field says "Pull-**DOWN**"), the schematic calls it **`R-CLR-PD`** | `[repo]` bom.csv:71, digital-and-supervision.md:41,137 |

---

## Tier 3 — consequence of today's changes that no document has recorded

### 26. Breath's zero now depends on the DAC, and three documents still say it cannot

This is the one I would escalate. It is not a stale sentence; it is a
dependency that today's changes created and that nothing in the repo has noticed.

The facts, all `[repo]`:

- `TRIM-BREATH-ZERO` derives the in-amp's `REF` voltage from **`VREFOUT`** —
  "Range 0 to ~+0.6V from VREFOUT; +0.437V nulls the pedestal exactly"
  (bom.csv:108), drawn the same way at breath-receive-stage.md:53–54.
- `VREFOUT` is the **DAC8568's internal reference**, and it is "**DISABLED by
  default, enable at boot**" (bom.csv:12), restated at 0006:155–159: "the
  outputs sit at 0 V from rack power-on **until firmware enables the
  reference**".

The claims that rest on breath being outside the digital path, all `[repo]`:

- `firmware/README.md:66–68` — "**no DAC register touches the breath jack at
  all**".
- `0004:418–419` — "Breath does not pass through the DAC at all … an analog path
  **has no register to hold**".
- `latency-budget.md:139–143` — rule 1, breath "never digitised at all".

`[from memory, inference]` The signal path is still analog, so the narrow claim
survives. The *zero* does not: at rack power-on, and after any boot in which
firmware fails to issue the internal-reference enable, `VREFOUT = 0`, the trim
delivers 0 V, and the in-amp rests at −0.437 V instead of 0 V rather than at the
nulled zero. Through the downstream inverting stage at the specified 0.6–2.5×
(breath-receive-stage.md:206) that is roughly +0.26 to +1.1 V standing at the
BREATH jack — into a VCA — until firmware runs.

Two further consequences nobody has written down:

- `firmware/README.md:56–58` already names "**the internal-reference enable**"
  as a register with the write-once bug latent in it. It now has a second
  victim it does not know about, on the one output the statelessness rule was
  said not to cover.
- `f2b6cf9` ("A bad flash should not end the instrument") `[git]` assumed a
  dead MCU leaves breath working. It still does for a *hang* after boot; it
  does not for a firmware that never completes boot.
- The new presence comparator senses the BREATH node **ahead of** the trim
  (bom.csv:100), so it is unaffected — that part of `b9beb48` is robust.

I am not asserting this is a defect requiring a redesign — a divider off the
REF5050, which is already in the instrument and always on, would remove it, and
so would simply recording the dependency. I am asserting that **three documents
currently deny a dependency that the BOM creates**, and that is a regression.

### 27. `docs/reference/latency-budget.md` — verdict: still correct, two gaps

Asked directly, so answered directly. I checked every number in it against the
state after `b9beb48`:

- "six DAC channels … **96 µs**" (`:62`, `:146`, `:154`) — **correct**.
  `cc830d5` had briefly set it to seven `[git]`; `0b1cfc6` set it back to six
  and added the "channel that briefly made it seven is deleted" note `[git]`.
  Matches bom.csv:12 ("Populate 6 of 8") and 0006:22 ("Six of eight channels
  used").
- Pitch reconstruction pole "**15.9 kHz** … ~10 µs" (`:64`, `:101`) —
  **survives the redraw**. `[from memory]` `C-FILT-PITCH` (10 nF × 1 kΩ) was
  replaced by `C-FB-PITCH` (1 nF × 10 kΩ); both are 15.9 kHz, so the latency
  term is unchanged. `[repo]` bom.csv:107 says the same.
- Mod 1.94 kHz / 82 µs, breath 531 Hz / 480 Hz, 2 MHz umbilical, 1.6× margin —
  all still match their sources.

Two gaps rather than errors:

| | Where | Gap |
|---|---|---|
| 27a | `latency-budget.md:98` | "Debounce (release) \| **filtered**" carries no number, but the release path now has a **~93 µs hardware filter** (`R-KEY-PU` 10 kΩ × `C-KEY` 10 nF) added earlier the same day. `ROADMAP.md:120–124` argues release latency is *not* free on a woodwind, so this belongs in the budget. `[repo]` bom.csv:91, 0001:179–180, ROADMAP.md:120–124 |
| 27b | `latency-budget.md:100` vs `:62,:63` | Key path books "DAC update + settle **~60 µs**"; the breath table books the same operation as 96 µs SPI burst + 10 µs settling. Two figures for one thing, in one document. |

### 28. Smaller consistency items, unlikely to bite

- `bom.csv:13` `U-OPA-PITCH`: "Twelve halves, **eleven used**" then lists **ten**
  (pitch, mod 1-4, mod offset buffer, breath gain, breath offset, VREFOUT
  follower, breath REF-zero buffer). The eleventh is presumably the gain-pot
  wiper buffer, which `breath-receive-stage.md:234` records as an **open E10
  question**. So the spare count is either 1 or 2 depending on a decision not
  yet made. `[repo]`
- `bom.csv:15` `R-PRECISION` and `mod-channels.md:57` both say the LT5400's two
  spare sections are "available for the mod channels, which want 1:3 (**three
  sections against the fourth**)" — three-against-the-fourth needs all four
  sections, and two are consumed by pitch. `pitch-stage.md:233` says the spares
  are "currently doing nothing", which is the accurate version. `[repo]`
- `mod-channels.md:145,151,156,167` still compute with **4.02** and **2.5 V**
  (`4.02 × (0 − 2.5) = −10.05 V`; "At 2.5 V into 2.5 kΩ that is **1 mA**") where
  the page's own diagram at `:16` says "~1.3 mA total". `[repo]`
- `mod-channels.md:112–120` derives tolerance by "enumerating all **sixteen
  corners of four 1 % resistors**" — there are now two per channel. `[repo]`
- `bom.csv:65` `R-ILIM` is still `open`, "value from E6", where
  `power-entry.md:70–74` derives **50 mΩ** from the LT1641's 50 mV threshold and
  draws it as `[R-ILIM 50mΩ]`. `[repo]`
- `bom.csv:19` `U-LOADSW` sizes the FET from "1.0A ramp at ~6V mean for 75ms …
  0.45J", which `power-entry.md:88` explicitly refutes ("a normal start **never
  enters current limit**") and replaces with a 0.6 J fault-case figure. Same
  conclusion (DPAK/SO-8), different arithmetic, both live. `[repo]`
- `docs/review/2026-09-20-cold-review/README.md` — its "**What has been
  applied**" table declares itself "the live status" `[git] 541ce12`, and was
  written before most of today's work. It still records "`R-MODGAIN` **×16**",
  and lists **W12** under *Still outstanding* with "needs either a readback or
  an accepted two-point calibration" — W12 was closed by deletion an hour later
  `[git] 0b1cfc6`, and W13 was closed as accepted `[git] f8147c9`. `[repo]`
- Pre-existing, not from today: `key-layout.yaml:5`, `ROADMAP.md:44` and
  `latency-budget.md:96` say "**74HC165**" where the part is `74LVC165A`
  (bom.csv:8); `bom.csv:2` `SW1-n` says "Plate cutout **must be measured**" in
  the same cell that says "use [Gateron's] datasheet and STEP model, do not
  caliper", against `key-layout.yaml:25–29`. `[repo]`

---

## What did *not* regress

Recorded because a review that only reports failures is not calibrated.

- **`7c68404` (registers to the carrier) is the cleanest change of the day.**
  It swept `U-KEYS`, `C-DECOUPLE-165`, `PCB-CARRIER`, `WIRE-LOOM`,
  `key-layout.yaml`, `ADR 0001`, `ADR 0013` and `ROADMAP.md:195` together, and
  deleted `R-TERM-CHAIN` and `PCB-CLUSTER` from the BOM rather than leaving
  them. `[repo]` verified: no `PCB-CLUSTER` or `R-TERM-CHAIN` row survives.
  Its one miss is #8 above.
- **The chain accounting is internally consistent**: 32 bits, 18 used, 14 spare
  = 6 marker + 3 switches + 5 free, and `spare_bits_*` add up. `[repo]`
  key-layout.yaml:97,113–132.
- **DAC channel accounting is consistent everywhere it appears**: six populated
  (bom.csv:12, 0006:22, ROADMAP.md:48 "all six channels",
  latency-budget.md:154, R-OPAMP-IN qty 7 = pitch + 4 mods + offset buffer +
  VREFOUT follower). `[repo]`
- **`aabd8ca`'s sweep held.** No `TPS2553` survives as a live recommendation
  (only as "REPLACES TPS2553" / "is *not* a TPS2553"), no `R-OEGATE`, no
  unresolved "INA821 / INA828", and the duplicated 0.6 MHz table is gone from
  `ADR 0003`. `[repo]` verified by grep.
- **The latency budget survived** the pitch redraw, the mod redraw and the
  register move — see #27.
