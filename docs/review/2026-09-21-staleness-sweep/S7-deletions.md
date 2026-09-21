# S7 — Deletions: what is gone, and what still depends on it

**Date:** 2026-09-21
**Slice:** every part, net, signal and feature that has been deleted, declined or
superseded — audited for residue in the design corpus.

**Corpus audited:** `hardware/**`, `docs/decisions/**`, `config/**`,
`docs/reference/**`, `ROADMAP.md`, `README.md`, `firmware/README.md`.
`docs/review/**`, `docs/log/**` and `docs/research/**` were read for context and
are **not** reported against — they are historical records and are allowed to
describe deleted parts.

## Three states, used throughout

- **Merely mentioned** — prose history ("the watchdog was deleted because…").
  Correct, valuable, **not reported**.
- **Still drawn** — a schematic, pin map, table or drawing shows the part as if
  it exists.
- **Still depended on** — an argument, a justification, a quantity, a test
  criterion or a firmware rule elsewhere requires the deleted thing to exist.
  **This is the class that builds wrong boards.**

## Verdict table

| # | Deleted thing | Verdict | Rank |
|---|---|---|---|
| 1 | Frame watchdog (74HC123) | **STILL DEPENDED ON** | **Showstopper** |
| 2 | Presence comparator (LM311) | **STILL DEPENDED ON** | **Showstopper** |
| 3 | Gated `OE` | **STILL DEPENDED ON** (ADR 0004 only) | High |
| 4 | `R-PD-BREATH` differential pulldown | **STILL DEPENDED ON** | **Showstopper** |
| 5 | `R-TERM-CHAIN` series termination | **CLEAN** | — |
| 6 | `MISO` on the umbilical | **STILL DRAWN** (ADR 0004 pin list) | Medium |
| 7 | Panel octave switch | **CLEAN** | — |
| 8 | `SW-PWR-INST` | **CLEAN** as a part; its *reason* is refuted | Medium |
| 9 | Instrument-end polyfuse | **CLEAN** | — |
| 10 | `EN` / `IO0` availability | **CLEAN** | — |
| 11 | `R-SCLK-SER` / `R-MOSI-SER` / `R-CS-SER` | **STILL DEPENDED ON** (ADR 0004) | High |
| 12 | Four-resistor mod gain network | **STILL DEPENDED ON** | **Showstopper** |

Plus **six refuted arguments** still doing load-bearing work — see the sweep at
the end. Two of them (the 20-cent diode bend, the feedback-cap pole) are the
stated justification for a part count and a part deletion respectively.

---

# 1. The frame watchdog (74HC123) — **STILL DEPENDED ON — Showstopper**

**Gone from every drawing.** `hardware/module/digital-and-supervision.md` was
redrawn today and is explicit:

> `digital-and-supervision.md:51` —
> "`NOT HERE ANY MORE: the 74HC123 frame watchdog and the LM311 presence`
> `comparator. Both deleted; see "What this redraw changed".`"

> `digital-and-supervision.md:153-158` — "## There is no frame watchdog …
> **Deleted.** A 74HC123 monostable used to assert the DAC's `CLR` when SPI
> traffic stopped. The part, its timing pair and its decoupling are gone"

**No BOM row survives.** `U-WATCHDOG`, `R-WDT` and `C-WDT` are absent from
`hardware/bom.csv` entirely, and `R-CLR-PU` records the deletion correctly.

### 1a. `bom.csv` still lists it in `PCB-MODULE`'s scope — *merely stale text*

`hardware/bom.csv:70`, `PCB-MODULE` description field:

> "`DAC, scaling, jacks, power entry, load switch, watchdog`"

The same row's notes field already flags it:
"`'watchdog' in this row's description is stale - that part is DELETED`".
Self-annotated, so it misleads nobody. **Low.** Delete the word.

### 1b. `firmware/README.md` still names it as the cause of the rule — **depended on**

`firmware/README.md:53-57`:

> "When the module
> watchdog asserts `CLR`, every DAC channel including channel 7 goes to zero
> scale. Firmware then rewrites the five signal channels … Every mod jack pins at
> `4 × Vdac` ≈ +11.45 V and stays there."

This is the *worked example that justifies the statelessness rule* — the single
most load-bearing firmware constraint in the repo
(`firmware/README.md:38-42`, "Refresh everything, every pass. Never
write-on-change."). Its only named trigger no longer exists.

**What breaks:** nothing electrically — but the rule now has no written cause.
The surviving triggers for a `CLR` are the DAC's own power-on reset, a hot-plug,
and the hand-asserted `LK-CLR` pad that `bom.csv:67` says E7–E10 want
("`A solder pad to ground beside it lets CLR be asserted BY HAND`"). **None of
those appear anywhere in `firmware/README.md`.** A future reader who checks the
premise, finds the watchdog deleted, and relaxes the rule reintroduces the
+11.45 V pin. Re-anchor the paragraph on power-on reset and the bring-up pad.
**High.**

### 1c. `mod-channels.md` builds its topology on it — **depended on, and this is the dangerous one**

`hardware/module/mod-channels.md:148-152`:

> "## The offset is a DAC channel, and that is the whole reason `CLR` works
> …
> On a watchdog `CLR`, the C-grade DAC8568 … clears **every** channel to zero
> scale (ADR 0006). Channel 7 goes to 0 V with the rest"

`mod-channels.md:215-218`:

> "On a watchdog `CLR` the channels go to zero and the divider does
> not, so `Vout = 5 × 2.0 = +10 V` — a hard rail on four jacks. The PER|FORMER
> avoids this by disabling `CLR` entirely; Woody cannot, **because the watchdog is
> the whole answer to a processor two metres away.**"

The last clause is a **refuted premise carrying a live conclusion.** "Woody
cannot disable `CLR`" is the sentence that rules out the single-inverting-amp
topology that four of four surveyed designs use — and it is justified by a part
that was deleted this morning.

**What breaks:** the *conclusion* survives (the DAC's power-on reset still
clears to zero scale, and `LK-CLR` still exists, so a `VREFOUT`-divider offset
would still slam four jacks to a rail). But the *stated reason* is gone, so the
page's own "strictly better" alternative at
`mod-channels.md:222-226` is now blocked by an argument the author can no longer
verify. Restate as: "`CLR` is asserted at every power-on by the DAC itself and
by the bring-up pad, so a non-clearing offset reference is unsafe regardless of
supervision." **Showstopper** — this is the exact shape the brief warned about:
a whole topology resting on a deleted part.

### 1d. `digital-and-supervision.md`'s own "Still open" list asks for work on the deleted part — **depended on**

`digital-and-supervision.md:210-217`:

> "- **A power-on reset RC on the '123's own `CLR`**, so the power-up safe state is
>   guaranteed rather than probable.
> - **The retrigger question was posed against the wrong numbers.** Six frames
>   per pass means **~2400 retriggers per timeout at ~16 µs intervals**, not ~400
>   at 250 µs … The real gates are the '123's discharge
>   `R_on` and whether discharge follows the trigger pulse."

Two open design actions, on a part the same page deletes 55 lines above. An
engineer working the open list will size an RC and a retrigger regime for a
footprint that is not on the board. **High.** Either move these to the
"if the watchdog is ever restored" file or delete them.

### 1e. `ROADMAP.md` E10's pass criterion is stale — **depended on**

`ROADMAP.md:51`:

> "**Pull the umbilical mid-note with the mouthpiece at rest** and confirm the
> breath jack parks quietly: the watchdog has no authority over it by design,
> and this is the check that the design is right about why (ADR 0004)."

The test is still worth running. Its stated rationale is not — and worse, the
same physical test now has a *second*, unmentioned outcome that
`digital-and-supervision.md:169-173` spells out:

> "| Cable unplugged mid-note | caught | **not caught — the DAC holds and the rack drones** |"

So at E10 the tester pulls the umbilical, sees breath park quietly, ticks the
box — **and pitch plus four mod jacks hold their last value indefinitely, which
the milestone does not tell them to look at or accept.** **Showstopper for the
milestone text.** E10 must now say: breath parks; pitch and mods hold; that is
the accepted cost of deleting the watchdog.

### 1f. `breath-receive-stage.md` and ADR 0004 cross-reference a withdrawn section — **depended on**

`hardware/module/breath-receive-stage.md:283-291`:

> "## What the jack does when the watchdog fires — settled
> **Nothing, and that is correct.** … Reasoning in full in
> ADR 0004, "The watchdog's scope is the DAC channels"."

That ADR 0004 section (`docs/decisions/0004-cv-interface-module.md:445`,
"#### The watchdog's scope is the DAC channels, and breath is outside it") sits
**inside** the block ADR 0004 marks withdrawn at line 419:

> "> **Withdrawn 2026-09-21.** The mechanism below was built and then deleted …
> The paragraphs below are kept because the problem they describe is still real."

A live schematic page cites a withdrawn section as its authority. The physics is
unchanged — breath never passes through the DAC — so nothing is electrically
wrong. **Medium.** Retitle the breath section "What the jack does on a `CLR`"
and cite the surviving argument, not the withdrawn mechanism.

---

# 2. The presence comparator (LM311) — **STILL DEPENDED ON — Showstopper**

**Gone from every drawing** (`digital-and-supervision.md:51`, quoted above), and
ADR 0004 deletes both versions explicitly at
`docs/decisions/0004-cv-interface-module.md:367-381` ("**Both versions are
deleted.** … **`OE` is tied enabled.**"). **No BOM row** — `R-PRESENCE` and
`U-PRESENCE` appear nowhere in `hardware/bom.csv`.

### 2a. ADR 0004's conductor budget still allocates a conductor to it — **still drawn**

`docs/decisions/0004-cv-interface-module.md:83`:

> "`+12V      / PWR_GND     power, and the presence signal`"

This is the **Revised conductor budget** — the current, authoritative 8-of-8
mapping, the one E11 and E12 build to. It annotates the power pair as carrying
"the presence signal". There is no presence signal. **High** — this is a
conductor counted for a deleted feature, in the table that defines the cable.

### 2b. `breath-receive-stage.md` builds a fault-propagation claim on it — **depended on**

`hardware/module/breath-receive-stage.md:195-198`:

> "Two consequences nobody had written down: if `R1` opens, the presence detect
> de-asserts and takes the **whole SPI link** with it, so pitch and the mods die
> with breath; and during the fault the jack clips high and *holds* while the
> detect still says "present"."

Both consequences are **false as of today**. With the comparator deleted and
`OE` tied enabled, `R1` opening kills breath and nothing else — SPI, pitch and
the mods are untouched. This passage sits in the section that argues `R1` must
be a 1206 and needs a twin (`R1b`), so a reader assessing the severity of an
`R1` failure is reading an inflated blast radius from a part that does not
exist.

**What breaks:** the `R1`/`R1b` argument itself survives on the other grounds
given (139 mW in an 0805; 60 dB of CMRR spent on one unmatched resistor). But
the *real* post-deletion consequence — an open `R1` is now completely silent,
because nothing at the module end watches the far end of the cable any more — is
**not written anywhere**, and ADR 0004:404-410 identifies exactly this as the
accepted loss. **Showstopper for the paragraph**; rewrite it to say that an open
`R1` is undetectable rather than catastrophic.

### 2c. `digital-and-supervision.md` proposes restoring watchdog coverage *from* the deleted comparator — **depended on**

`digital-and-supervision.md:188-193`:

> "### The obvious way to get the link coverage back, for no new parts
>
> `CLR` can be driven from the **presence comparator** instead of from a
> monostable. **It already reports** cable connected, far-end power, reference alive,
> sensor alive and both analog conductors intact"

Present tense — "It already reports" — for a part deleted on the same page. The
proposal is headed "**for no new parts**", and it needs at minimum an LM311, its
two decoupling caps, `R-PRESENCE` and a 74AHCT14. **High.** The proposal may
well be right, but it must be costed as a restoration, not as free.

### 2d. The "Still open" list asks for a BOM row for the deleted part — **depended on**

`digital-and-supervision.md:208-209`:

> "- **The presence tap point**, above. It needs the one-line change described and
>   a corrected `R-PRESENCE` row."

`R-PRESENCE` is in no BOM and never was. This asks someone to *correct* a row
that does not exist, for a part that is deleted. **High.**

Same list, `digital-and-supervision.md:228-233`:

> "- **The threshold may sit inside the breath signal's own range.** … **The clean
>   answer may be to demote this comparator to LED and health duty and gate `OE`
>   from the link itself**"

An open item about tuning the threshold of a deleted comparator, whose
threshold problem was one of the three reasons it was deleted
(`ADR 0004:373-379`). **Medium** — circular and confusing, but harmless.

### 2e. `C-DECOUPLE`'s quantity breakdown still counts its two caps — **quantity counted for it**

`hardware/bom.csv:42`, `C-DECOUPLE`, qty **19**, notes:

> "`One per supply pin, close to the pin. 6 x OPA2197 on +/-12V = 12, INA828 = 2,`
> **`LM311 on +/-12V = 2`**`, DAC8568 AVDD+DVDD = 2, 74AHCT125, LT1641 VCC, LM317 in.`
> `Was 22 with the 74HC123; the watchdog is deleted | 2026-09-21: was 21. The two`
> `caps counted for the LM311 are removed - that part was DELETED and its`
> `footprint is no longer drawn`"

**The enumeration and the quantity now disagree.** Summed as written:
12 + 2 + **2** + 2 + 1 + 1 + 1 = **21**, against a stated qty of **19**. The
trailing note removes the LM311's two caps but the itemised list that a board
stuffer would check against still contains them. **High** — this is the exact
failure the row's own history records twice (22 → 21 → 19), left half-applied.
Strike "`LM311 on +/-12V = 2`" from the enumeration.

### 2f. `U-DIFFRX` still carries the pre-trimmer rest value the comparator needed — **depended on**

`hardware/bom.csv:27`, `U-DIFFRX`:

> "`Output is -0.44V at rest to -10V at full`"

Against the drawn circuit, `hardware/module/breath-receive-stage.md:58`:

> "`Vout = −2.185·(V_BREATH − V_AGND) + V_REF`
> `      = 0 V at rest, −9.6 V at full`"

and the commissioning step, `breath-receive-stage.md:272-273`:

> "1. **`TRIM-BREATH-ZERO`**, internal, until the in-amp output reads 0 V. Once,
>    at build."

and `ROADMAP.md:51`: "**Set `TRIM-BREATH-ZERO` first**, until the in-amp output
reads 0 V".

−0.44 V at rest is the **un-nulled** output — the standing pedestal that existed
before `REF` carried a trimmer, and precisely the offset a comparator watching
the breath line needed in order to have anything to trip on. The trimmer's whole
job is to make it 0 V. Both endpoints are stale (−0.44 → 0 V, −10 → −9.6 V).

**What breaks:** anyone bringing up the in-amp at E10 with `bom.csv` in hand
will trim to −0.44 V and then find the downstream inverting stage resting
~1.8 V off zero at the working gain of 2.1×. **Showstopper for E10 commissioning.**

---

# 3. The gated `OE` — **STILL DEPENDED ON (ADR 0004 only) — High**

**Clean in both schematics**, and unusually well documented:

- `digital-and-supervision.md:32` draws "`OE x4 → GND`  tied ENABLED".
- `digital-and-supervision.md:75-80` retires `R-OE-PU` and the 820 Ω by name:
  "**3. `OE` gating is gone.** … `R-OE-PU` and the 820 Ω had no BOM rows;
  `R-LED-PANEL` is 2.2 kΩ from +12 V analog and is drawn on the power page".
- `hardware/module/power-entry.md:222-228` carries the matching retraction:
  "**This whole section described a circuit that no longer exists.** … The
  comparator is deleted, `OE` is tied low and permanently enabled, and neither
  `R-OE-PU` nor `R-LED` ever had a BOM row."
- `bom.csv:34` `U-LVL-MOD`: "`OE IS TIED ENABLED`".
- `bom.csv:79` `R-LED-PANEL` 2k2: "`Was 820R from bus +5V when it shared a node
  with the level shifter's OE pins; that node is gone with the comparator`".

`R-OE-PU` and an 820 Ω `R-LED` appear in **no** BOM row. The panel LED's rail is
settled: **+12 V analog through 2.2 kΩ**, ~4 mA.

### 3a. ADR 0004 still prescribes the gating, unmarked — **depended on**

`docs/decisions/0004-cv-interface-module.md:347-352`:

> "**So pull them, and gate the buffer:**
>
> - **CS pulled to +5 V; SCLK and MOSI pulled to ground**, at the module end.
> - **Gate the 74AHCT125's output enable from a real presence detect**, so
>   "instrument absent" is a state the hardware knows about rather than one it
>   stumbles into."

This is a bare imperative in an **Accepted** ADR, with no supersession marker.
The section that retracts it begins 15 lines later at line 367 — but unlike the
watchdog block, which gets an explicit "**Withdrawn 2026-09-21**" callout and
strikethrough at line 419, this one gets nothing. The first prescription a
reader hits is the deleted one. **High.** Mark it the way the watchdog block is
marked.

Note also that the first bullet is itself stale against `bom.csv:48`
(`R-SPI-PULL`), which specifies **six** pulls and requires the cable-side `CS`
to pull to **3V3, not +5 V** — "`pulled to 5V it drives 430uA continuously
through the unpowered ESP32's input clamp`". ADR 0004 still says +5 V.

### 3b. The gating is ADR 0004's stated reason for moving the power switch — see item 8

---

# 4. `R-PD-BREATH`, the differential pulldown — **STILL DEPENDED ON — Showstopper**

**Deleted** and replaced:

- `docs/decisions/0003-breath-sensing-path.md:376-383`: "**The pulldown is
  deleted and replaced by a common-mode bias return.** … **A purely differential
  element gives the in-amp's inputs no DC path to ground at all.** Unplugged,
  input bias current ramps both inputs until the amplifier saturates, so the
  breath jack goes to a rail rather than to **the 0 V ADR 0005 promises**."
- `hardware/module/breath-receive-stage.md:253`: "| The 100 kΩ differential
  pulldown | **Deleted.** R4/R5 do its job without its 1–17 % attenuation |"
- `hardware/bom.csv:59`, `R-BIAS-INAMP`: "`REPLACES R-PD-BREATH.`"

`R-PD-BREATH` has no BOM row. **But ADR 0003 flagged the collision in its own
text and neither of the two ADRs it names was updated.**

### 4a. ADR 0005 still prescribes it — **depended on**

`docs/decisions/0005-power-architecture.md:330-333`:

> "**Pull down the module's breath receive input**, so that an instrument which is
> switched off — or unplugged — presents 0 V rather than a floating buffer output.
> One resistor, and it means powering down the instrument silences the patch
> instead of leaving a stuck level (ADR 0003)."

A live, unmarked, one-resistor instruction in an **Accepted** ADR, citing
ADR 0003 — which deleted it and says so. **Showstopper:** a reader fitting this
resistor reintroduces the 1–17 % signal attenuation the deletion removed,
*and* the single-element differential shunt that ADR 0003 shows gives the in-amp
inputs no DC return.

### 4b. ADR 0006's power-on table is load-bearing on it — **depended on**

`docs/decisions/0006-cv-channel-allocation.md:158`:

> "| **Breath** | 0 V | The receiver's differential pulldown holds it there (ADR 0003) |"

This is the **rack power-on state table** — the table that justifies the C-grade
DAC lock and the whole "best available state on every channel at once"
conclusion. Its breath row is wrong twice over:

1. The named mechanism is deleted.
2. **The replacement does not produce 0 V at the jack.** Two 1 MΩ bias
   resistors hold the in-amp's *inputs* at module analog ground; the in-amp then
   rests at `V_REF` (+0.437 V from `TRIM-BREATH-ZERO`, nulling the sensor
   pedestal that is absent when the instrument is off), and the downstream
   inverting gain-and-offset stage puts the jack wherever the panel OFFSET knob
   was left — which `breath-receive-stage.md:273-275` specifies as a **±5 V,
   zero-at-centre** control, and ADR 0004:459 describes as "the jack falls to
   wherever the panel offset knob left it and stays there."

**What breaks:** the power-on safety claim for one of six outputs. ADR 0006's
table asserts a defined 0 V on the breath jack at rack power-on; the built
circuit asserts an *arbitrary* voltage up to ±5 V, set by a knob, with the
instrument absent. **Showstopper.** Either correct the row to "panel OFFSET
position, ±5 V" and accept it, or decide whether a defined power-on state is
actually required on that jack.

---

# 5. `R-TERM-CHAIN`, the series termination — **CLEAN**

Deleted by ADR 0001 and properly fenced everywhere:

- `docs/decisions/0001-mcu-and-board-partitioning.md:182-186`: "**So
  `R-TERM-CHAIN` is not restored.** It was wrong as written anyway — series
  termination is a point-to-point technique and those lines drop on four boards"
- `hardware/controller/carrier.md:755`: "ADR 0001 deleted `R-TERM-CHAIN` because
  series termination is wrong for a line that drops on four boards; **this is
  edge-rate damping at the source, which is a different job and survives that
  argument**"
- `hardware/bom.csv:94`, `R-CHAIN-SER`: "`a DIFFERENT job from the R-TERM-CHAIN
  that ADR 0001 deleted - that was series TERMINATION`"

No BOM row, no drawing, no quantity. The successor part (`R-CHAIN-SER`, 100 Ω
×3) is distinguished by name and by argument in all three places.

**Checked and cleared:** `R-SER-TERM` (`bom.csv:112`) is *not* a resurrection —
it is a 10 kΩ **pull-up** on the chain-end board's serial input, a different
part doing a different job (`cluster-boards.md:237-255`).

---

# 6. `MISO` on the umbilical — **STILL DRAWN — Medium**

**Deleted by ADR 0004** and correctly relied upon as absent in five places:

- `firmware/README.md:38-42`: "The umbilical is write-only — `MISO` was deleted
  from the cable (ADR 0004) — so nothing downstream can ever be read back."
- `firmware/README.md:59`: "With no `MISO` this is undetectable"
- `digital-and-supervision.md:95-97`: "ADR 0004 deleted `MISO`, so **firmware
  can never read back what the DAC actually received.**"
- `mod-channels.md:161`: "indefinitely, with no `MISO` to notice it."
- `ADR 0004:772`: "This ADR deleted `MISO`, so firmware can never read back what
  the DAC received."

**No document assumes the DAC can be read back.** Every surviving use is of the
form "because there is no `MISO`, therefore…" — which is the correct dependency
direction. The three other `MISO` hits are a different, on-board signal:
`carrier.md:537` "`IO37 MISO ── MCP3202 DOUT only (never leaves the board)`",
`carrier.md:404` (SPI3 to the 74x165 chain), ADR 0008:79 and ADR 0013:44.

### 6a. ADR 0004's own "What goes over the cable" block still lists it — **still drawn**

`docs/decisions/0004-cv-interface-module.md:35-40`:

> "```
> +12V, GND, GND      power (3.3V derived locally in the instrument, small buck)
> SCLK, MOSI, CS      SPI to the DAC, ~2 MHz
> MISO                unused today — module ID and presence detect
> spare               reserved
> ```"

Presented under "### What goes over the cable" with no supersession marker; the
replacement arrives 45 lines later as "### Revised conductor budget"
(line 81-88) and at line 94 "MISO goes, and with it the planned module-ID line."
The block also predates the T568B pin map at line 745-750 and shows a
conductor count that no longer matches (it lists two GNDs and a spare; the
settled budget has `DIG_GND`, `PWR_GND`, `AGND` and no spare).

Nothing structural depends on it and the correction is three sections below,
so: **Medium.** Strike it through or fold it into the revised budget.

---

# 7. The panel octave switch — **CLEAN**

Considered and declined at `docs/decisions/0004-cv-interface-module.md:488-512`
("A three-position toggle for +1 / 0 / −1 octave was proposed and is **not
built**"), and — importantly — the *reserve language that argued for it* has
been corrected at `docs/decisions/0006-cv-channel-allocation.md:425-434`:

> "> **What the reserve is, because it is easy to misread.** The 0.25–4.75 V
> > window … is **calibration headroom** … It is **not** a limit on
> > transposition. … This was briefly misread as "firmware cannot transpose by a
> > full octave", which is wrong, and **it nearly bought an analog octave switch
> > the module does not need.**"

**Nothing assumes it.** Specifically checked:

- **Panel layout** (`ADR 0004:583-585`) — "Connector, power switch and LED …
  two breath knobs, then six jacks in two columns". No toggle. The panel's
  "third control" that drove 8HP → 10HP is the breath-response pot
  (`POT-RESP`, `bom.csv:80`), not an octave switch.
- **Panel height budget** — "Roughly 107 mm of ~110 mm usable height" with the
  switch absent; adding one back would not fit, which is consistent.
- **`V_ref` switching network** — no 1.500/3.500 V taps, no extra op-amp half,
  no 0.1 % step resistors anywhere in `pitch-stage.md` or `bom.csv`.
- Every other "octave" hit is either key-based octave control (ADR 0010's three
  reserved chain bits, `cluster-boards.md:277`, `carrier.md:509`,
  `bom.csv:2`) or a unit of pitch error. Different feature, correctly alive.

---

# 8. `SW-PWR-INST`, the instrument-end power switch — **CLEAN as a part; its reason is refuted — Medium**

Deleted at `docs/decisions/0005-power-architecture.md:240`:

> "**So `SW-PWR-INST` is deleted.** Nothing on the instrument switches anything."

Clean everywhere:

- `hardware/bom.csv:17`, `SW-POWER`: "`The only power switch in the system;
  SW-PWR-INST is deleted (ADR 0005)`" — and the row is the *module* toggle.
- `hardware/controller/carrier.md:116`: "**There is no fuse and no power switch
  on this board** (ADR 0005)."
- No `SW-PWR-INST` BOM row, no instrument-side switch in any drawing, no panel
  cutout for one in ADR 0009.

### 8a. ADR 0004 justifies the relocation with the deleted `OE` gating — **refuted argument**

`docs/decisions/0004-cv-interface-module.md:361-365`:

> "That OE gating is the reason the power switch had to move to the module
> (ADR 0005). With a switch at the instrument end, "+12 V present on the
> umbilical" would no longer mean "instrument alive", and the gating would fail in
> exactly the state it exists for. **The relocation was load-switch-shaped but this
> is what made it necessary.**"

The `OE` gating is deleted (item 3). So the sentence that claims to identify
what "made it necessary" now points at nothing.

**Nothing breaks**, because ADR 0005 supplies two independent and sufficient
reasons that stand on their own (`0005:224-238`): the Recom R-78E5.0 "**has no
enable pin**" — "The switch as specified has nothing to switch" — and the
WS2815 strips run on raw +12 V *upstream* of the buck, so killing the buck
leaves "an instrument still lit, still drawing current, with its logic dead."
**Medium** — delete the ADR 0004 paragraph so the decision is not seen resting
on a deleted feature.

---

# 9. The instrument-end polyfuse — **CLEAN**

Deleted at `docs/decisions/0005-power-architecture.md:287-300` with four
reasons, and correctly reflected:

- `docs/decisions/0005-power-architecture.md:212-218`: "**There is no fuse at
  the umbilical entry.** An earlier revision of this ADR put a polyfuse here …
  That job is done — better, faster and without the thermal hysteresis — by the
  module's load switch"
- `docs/decisions/0013-two-mcu-split.md:246-247`: "**No polyfuse:** the current
  limit lives at the module end (ADR 0005)"
- `hardware/controller/carrier.md:116`: "There is no fuse and no power switch on
  this board (ADR 0005)."
- `docs/decisions/0014-lighting.md:202-203` records the history correctly: "The
  polyfuse is deleted (ADR 0005)."

No BOM row for an umbilical-entry polyfuse. **Checked and cleared:** `F-CHAIN`
(`bom.csv:96`) is a *different* proposed part — a 100 mA polyfuse on the **3V3
cluster-chain conductor**, not the umbilical entry. `power-entry.md:270-272`
draws the boundary explicitly: "ADR 0005's deletion argument was about the
*instrument-end* polyfuse and does not reach these."

---

# 10. `EN` and `IO0` availability — **CLEAN**

Established as **not** on the ESP32-S3-Matrix headers, and every downstream
count was updated:

- `hardware/bom.csv:97`, `HDR-SERVICE`: "`SIX pins, not ten. EN and IO0 are NOT
  available`"
- `hardware/controller/carrier.md:665-706`: "**This section's open question has
  been answered, against it.** … **`HDR-SERVICE` is therefore 2×3, six pins, not
  2×5** … **Two conductors and three passives per line come out of the loom with
  it** … `No EN, no IO0, and so no RC networks for them.` … **The proposed RC
  networks are withdrawn along with the lines they protected.**"
- `docs/decisions/0009-enclosure-construction.md:303-317`: "over a **six-pin**
  header … **Not `EN` and `IO0`, which are not available.**"
- `firmware/README.md:91-94`: "**There is no hardware boot-force**: `EN` and
  `IO0` are not broken out on the ESP32-S3-Matrix"

**Conductors are counted correctly.** `carrier.md:783` — "| **`J-DISP`** |
**9-way** | **Proposed … Was 11-way before `EN`/`IO0` were withdrawn** |" — and
the loom tally at `carrier.md:803` reads "| Display loom (§6) — `EN`/`IO0`
withdrawn | 9 |". The itemised 9 at `carrier.md:692-700` sums correctly. No RC
networks for `EN`/`IO0` survive in any BOM row. Nothing plans to wire them.

This is the model the other eleven deletions should be measured against.

---

# 11. `R-SCLK-SER` / `R-MOSI-SER` / `R-CS-SER` — **STILL DEPENDED ON (ADR 0004) — High**

Replaced today by `R-SPI-SER` ×3 at 100 Ω. Clean in the schematic and the BOM:

- `hardware/controller/carrier.md:531-546`: "**All three are `R-SPI-SER`, and the
  value is 100 Ω.** The refdes matters: this page previously drew
  `R-SCLK-SER`, `R-MOSI-SER` and `R-CS-SER`, **none of which exist in
  `bom.csv`**, while the BOM carries `R-SPI-SER` at qty 3 used by no schematic."
- `hardware/bom.csv:49`: "`THREE. 100R, not 220R - revised 2026-09-21 … carrier.md
  used to draw these as R-SCLK-SER / R-MOSI-SER / R-CS-SER, which were in no BOM`"

### 11a. ADR 0004 still prescribes the old part, the old count and the old value — **depended on**

`docs/decisions/0004-cv-interface-module.md:479-481`:

> "**220 Ω in series on MOSI at the driving end.** Source termination on the one
> line that runs the full umbilical carrying data. It also makes SYNC-signal
> regeneration at the module unnecessary, which was the alternative under
> consideration."

and `docs/decisions/0004-cv-interface-module.md:69-72`:

> "`R-MOSI-SER` at 220 Ω with
> ~200 pF of cable is a **3.6 MHz** corner — 7.9 MHz is the 100 Ω case this same
> sentence offers as the fix, which is the wrong way round."

**Three errors in one prescription**, all settled against it elsewhere today:

1. **One resistor, not three.** `bom.csv` and `carrier.md` both specify three.
   Worse: `digital-and-supervision.md:234-238` lists as open "**`SCLK` has no
   series resistor and `MOSI` does.** That is the wrong way round: `SCLK` is
   the fastest edge on the cable" — an open item that ADR 0004's text is the
   source of.
2. **220 Ω, not 100 Ω.** `carrier.md:552-556` computes 220 Ω as "**1.83–1.86 V**
   … **below threshold, dwelling ~20 ns per edge in the forbidden band**"
   against the 74AHCT125's 2.0 V `V_IH`.
3. **The RC-corner model is refuted.** `carrier.md:548-551`: "Two m of Cat5 is a
   **100 Ω transmission line**: the round trip is ~20 ns against 2–5 ns edges,
   so this is a reflection problem, not an RC corner. Three reviewers agreed."
   ADR 0004:69's "3.6 MHz corner" is that dead model, still deriving a number.

**What breaks:** the ADR is the document that E11 validates against
(`ROADMAP.md:52`, "SPI **at 2 MHz** … **on the T568B pin mapping in ADR 0004**").
A board built to ADR 0004's prose fits one 220 Ω resistor on `MOSI`, leaves the
fastest edge on the cable unterminated, and dwells in the forbidden band on
every `SCLK` edge. **High.**

---

# 12. The four-resistor mod gain network — **STILL DEPENDED ON — Showstopper**

Replaced today by the two-resistor `k = 3` form:

- `hardware/module/mod-channels.md:52-66`: "**`k = 3`, with the shared offset
  channel writing 3.3333 V instead of 2.500 V.** … **Adopted, and it is drawn
  above.** Eight resistors instead of sixteen"
- `hardware/bom.csv:66`, `R-MODGAIN`, qty **8**: "`EIGHT, not sixteen: R1=10k,
  R2=30k per channel, k=3 … V_ref = 3.3333V from the offset channel.`"

### 12a. ADR 0006 still describes the old network as the design — **depended on**

`docs/decisions/0006-cv-channel-allocation.md:102-106`:

> "```
> Vout = 4 × (Vdac − 2.5 V)
>
>   Vdac 0.00 V  →  −10 V
>   Vdac 2.50 V  →    0 V
>   Vdac 5.00 V  →  +10 V
> ```"

and `docs/decisions/0006-cv-channel-allocation.md:130-142`:

> "With a fixed 2.5 V offset, `Vout = 4 × (Vdac − 2.5)` parks the mod outputs at
> **−10 V** on a zero-scale reset …
> **Taking the offset from a DAC channel dissolves it.** On a zero-scale reset
> *both* terms are zero:
> ```
> Vout = 4 × (Vdac − Voffset) = 4 × (0 − 0) = 0 V
> ```"

The ADR does carry a partial correction at lines 86-99, but it stops short:

> "> **The mod channels can take the same
> > form** at `k = 3` with the offset channel writing 3.3333 V; **whether they do is
> > open** (`mod-channels.md`)."

**It is not open any more.** `mod-channels.md:62` — "**Adopted, and it is drawn
above.**" — and `bom.csv` is locked to 10 k/30 k ×8. ADR 0006 leaves a settled
question open and then, 40 lines later, specifies the superseded transfer
function three times in prose the firmware reads.

**What breaks — concretely.** `firmware/README.md:49-53` already names the
hazard:

> "The mod channels are `Vout = 4·Vdac − 3·V_ref`, with `V_ref` the shared
> **3.3333 V** from DAC channel 7 — **written once at boot** (ADR 0006). *(The
> value changed with the two-resistor redraw in `mod-channels.md`; writing the
> old 2.5 V into channel 7 against the current 10 k/30 k network gives a
> **−7.5…+12.5 V window — wrong span, and it clips positive**.)*"

ADR 0006 is cited as the source for that boot write, and ADR 0006 still says
2.5 V. **Firmware written from ADR 0006 clips four mod outputs positive.**
**Showstopper.**

### 12b. ADR 0006's grade-lock argument uses the superseded network — **depended on**

`docs/decisions/0006-cv-channel-allocation.md:136-142` argues the C-grade lock
from `4 × (Vdac − Voffset) = 4 × (0 − 0) = 0 V` — the four-resistor difference
form, which is safe for *any uniform* reset state. `mod-channels.md:168-174`
records that this is no longer true:

> "**The two-resistor form also made the DAC grade safety-critical**, which the
> four-resistor form did not. `4X − 4X` is zero for *any* uniform reset state;
> `4X − 3X` is `X`. With the locked C grade that is 0 V and correct — but a B/D
> part would put **+2.5 V on all four jacks** where the old topology gave 0 V
> regardless."

The *conclusion* (lock the C grade) survives, because ADR 0006 has a second,
independent reason — reference gain (`0006:118-123`, "Only C satisfies both
requirements"). But the ADR's stated mod-channel safety margin is now
**topology-dependent rather than topology-free**, and the ADR does not say so.
**High.**

---

# Refuted arguments still doing work

Six arguments the corpus has explicitly refuted, checked for surviving use.

## A. "~20 cents of breath-correlated pitch bend" from diode `V_f` modulation — **STILL DOING WORK — High**

**Refuted** at `hardware/module/power-entry.md:54-62`:

> "**The "20 cents of breath-correlated pitch bend" that followed is not [sound].**
> It implies ~21 % pitch sensitivity to the +12 V rail. Pitch full scale is
> set by the DAC's *internal* reference, and AVDD comes from the LM317, so
> the real path is 75 mV → LM317 line regulation (0.52 mV/V) → 39 µV on AVDD
> → OPA2197 PSRR (114 dB) → **0.15 µV = 0.00018 cents** `[calc, A7]`. The
> 20-cent figure is a survival from the rail-divider topology ADR 0006
> already deleted. Two reviewers reached this independently."

**Still asserted in three corpus places, and in two of them it is the sole
justification for a part count:**

1. `hardware/bom.csv:36`, `D-REVPOL`, qty **3** —
   "`THREE not two: the module's analog +12V and the umbilical feed must NOT
   share a diode - instrument current then modulates its Vf by ~80mV, which is
   ~20 cents of breath-correlated pitch bend and needs no ground path at all
   (ADR 0006)`"
2. `docs/decisions/0004-cv-interface-module.md:299-302` — "so it modulates that
   diode's forward voltage by ~80 mV — about **20 cents of breath-correlated
   pitch bend**, needing no ground path at all … (`D-REVPOL` qty 3, ADR 0006.)"
3. `docs/decisions/0006-cv-channel-allocation.md:562` — "| **The module's analog
   rail and the umbilical feed share one 1N5817**, so instrument current
   modulates its V_f by ~80 mV | **~20 cents** |" — inside a four-row table whose
   closing line reads "Every one of these is larger than every term in this
   ADR's precision budget", and which then prescribes "**Separate the
   Schottkys.** … `D-REVPOL` goes to three".

The 80 mV figure is sound and independently confirmed (`power-entry.md:49-53`,
A7's 75 mV). The **20 cents** is 110,000× too large. The part survives on the
reasons `power-entry.md:63-66` gives — "fault isolation between the exported
rail and the analog rail, and HF isolation" — but until those reasons are copied
into `bom.csv` and ADR 0006, `power-entry.md:66-67` predicts the outcome
exactly: "Left as it was, the next reviewer who checks the arithmetic deletes
the part."

Worse: ADR 0006's table now ranks a 0.00018-cent term above real terms in the
same table (5.7–7.2 cents of module ground, ~4.8 cents of bus ground), which
**inverts the priority order for the grounding work that is still open**
(`power-entry.md:68-90`).

## B. "A cap across a non-inverting stage's feedback resistor makes a pole" — **STILL DOING WORK — High**

**Refuted** in two BOM rows and on the schematic page:

- `hardware/module/pitch-stage.md:181-193`: "**`C-FB-PITCH` is not a filter, and
  an earlier version of this page said it was.** … `G(s) = 1 + (R2/R1)/(1 + sR2C)
  = (2 + sRC)/(1 + sRC)` … **Maximum attenuation 6.02 dB, at any frequency, for
  any capacitor value.** It is a shelf, not a pole"
- `hardware/bom.csv:114`, `C-AA-PITCH`: "`THE ACTUAL PITCH FILTER … It is a
  shelf, not a pole.`"
- `hardware/bom.csv:108`, `C-FB-PITCH`: "`NOT 'across the feedback resistor' …
  Three documents said 'across R2' and were wrong.`"

**Still asserted in ADR 0006**, where it is the stated reason for deleting a
part, `docs/decisions/0006-cv-channel-allocation.md:611-615`:

> "**Adopted.** Pitch now closes its DC loop at the jack, with `C-FB-PITCH` (1 nF
> across the feedback resistor) taking the loop back to the op-amp output above
> ~16 kHz — **which is also the reconstruction pole, so it is one part doing both
> jobs.** `C-FILT-PITCH` is deleted: a capacitor to ground at the jack would now sit
> inside the DC loop at exactly the handover."

Three defects in five lines:

1. **"across the feedback resistor"** — the topology the BOM and the schematic
   both flag as the dangerous one. `bom.csv:108`: "with the tap at the jack, R2
   spans jack-to-(-), so a cap across R2 connects the same two nodes and leaves
   R-OUT-PROT inside the loop at every frequency: **18 degrees of phase margin
   with 2m of cable, under 10 with four destinations**."
2. **"which is also the reconstruction pole"** — the refuted claim itself. It
   cannot be a pole; it is a 6.02 dB shelf.
3. **"`C-FILT-PITCH` is deleted"** — **the deletion has been reversed and ADR 0006
   was not updated.** `hardware/bom.csv:119`: "`RESTORED. It was deleted on the
   reasoning that a cap on the feedback node sits inside the DC loop at the
   handover; two independent loop analyses then put 10nF there and found phase
   margin UNCHANGED`". `pitch-stage.md:136` lists it as "**Restored at the
   jack**", and `pitch-stage.md:205-211` gives the analysis.

**What breaks:** ADR 0006 tells a builder to omit `C-FILT-PITCH` (leaving the
connector with no low-impedance shunt at all — `pitch-stage.md:197-199` costs
this at 30 dB at 1 MHz) and to wire `C-FB-PITCH` across `R2` (18° of phase
margin). `pitch-stage.md:224-226` names the risk in general terms — "Three other
places said "across the feedback resistor" and were wrong, and **prose is what a
layout gets built from**" — but the ADR is still one of them. **High.**

*Adjacent, same part:* `pitch-stage.md`'s own drawing at line 29 shows
`[C-FB-PITCH 1nF]` and its split-loop table at line 179 says "1 nF", while the
values table at line 134, the revision note at line 212 and `bom.csv:108` all
say **2.2 nF**. One page, two values. **Medium.**

## C. The 12 V LED edge — **CLEAN**

Refuted at `docs/decisions/0001-mcu-and-board-partitioning.md:144-147`: "**There
is no 12 V edge.** The WS2815 rail is held up by 470–1000 µF and its LED current
is PWM'd at ~2 kHz (ADR 0014). The fast aggressor is the **data line, at 5 V**."
Every surviving mention is a refutation: `cluster-boards.md:166-175`,
`carrier.md:483-491`, `bom.csv:92` (`C-KEY`: "`NOTE the coupling argument that
originally justified this part was wrong (see ADR 0001)`"), `ADR 0001:206`.
**No document still uses a 12 V edge to size anything.**

## D. ~15 pF of coupling — **CLEAN**

Same three refutation sites. No surviving quantitative use.

## E. 180 pC of injected charge — **CLEAN**

Refuted at `carrier.md:483-491`: "The first draft carried ADR 0001's
`180 pC / 10 nF = 18 mV`, and a companion figure of **+4.5 V on the loom node**
from `180 pC / 40 pF`. **Both are dead**, for two independent reasons, and
**neither should be reintroduced**". The 4.5 V figure appears nowhere else.

## F. `Q/C` as a coupling model — **CLEAN**

Refuted at `ADR 0001:148-152` ("**`Q/C` is the wrong model.** Coupling is a
*divider*: `ΔV = V_agg · C_c/(C_c + C_v)`"), and re-stated as refuted at
`cluster-boards.md:169-171` and `carrier.md:489`. The parts it once justified
(`R-KEY-PU`, `R-KEY-SER`, `C-KEY`) are all retained on **restated** grounds — a
floating CMOS input has no defined state — and each BOM row says so. This is the
correct pattern: the part survived, the argument was replaced, and both are
written down.

---

# Adjacent findings (outside the twelve, found while sweeping)

- **`ROADMAP.md:51` prescribes a design option that was declined.** E10 reads
  "Analog breath stage: in-amp receiver with **`REF` grounded**, gain/offset
  knobs" and then, in the same cell, "**Set `TRIM-BREATH-ZERO` first**". These
  are the two mutually exclusive options.
  `breath-receive-stage.md:113-119` declines the first by name: "### Why `REF`
  is trimmed rather than grounded — **Grounding it makes the panel knobs
  interact** … turn GAIN to 2.4×, and the jack idles around **+0.6 V**." With
  `REF` grounded there is nothing for `TRIM-BREATH-ZERO` to drive. **High** —
  a commissioning instruction that cannot be followed as written.

- **`digital-and-supervision.md:219-223` says `LDAC` "is not in this design
  anywhere"**, while `hardware/bom.csv:120` carries an `R-LDAC` row. Not a
  deletion, but the same class of drawing-vs-BOM divergence; worth one line of
  reconciliation.

---

# Recommended order of work

**Showstoppers, in the order they cost the most:**

1. **ADR 0006:102-146** — correct the mod transfer function to `4·Vdac − 3·V_ref`
   with `V_ref = 3.3333 V`, and close the "whether they do is open" question
   (item 12a). Firmware built from this clips four outputs.
2. **`bom.csv:27` `U-DIFFRX`** — "−0.44 V at rest to −10 V" → "0 V at rest to
   −9.6 V" (item 2f). E10 miscommissions on this.
3. **ADR 0005:330** — delete the "Pull down the module's breath receive input"
   prescription (item 4a). It reintroduces a deleted part.
4. **ADR 0006:158** — the power-on table's breath row (item 4b). The design has
   no defined power-on state on that jack and does not say so.
5. **`mod-channels.md:217-218`** — re-anchor "Woody cannot disable `CLR`" on the
   DAC's power-on reset and `LK-CLR`, not on the watchdog (item 1c).
6. **`ROADMAP.md:51` E10** — add the pitch-and-mods-drone outcome to the pass
   criteria, and fix `REF` grounded vs trimmed (items 1e, adjacent).

**High, and cheap:**

7. `ADR 0004:479` and `:69` — 220 Ω on `MOSI` → 100 Ω `R-SPI-SER` ×3 (item 11a).
8. `ADR 0004:83` — strike "and the presence signal" from the conductor budget
   (item 2a).
9. `ADR 0004:347-352` — mark the `OE`-gating prescription superseded the way the
   watchdog block is marked (item 3a).
10. `bom.csv:42` `C-DECOUPLE` — strike "LM311 on +/-12V = 2" so the enumeration
    sums to 19 (item 2e).
11. `breath-receive-stage.md:195-198` — an open `R1` is now silent, not
    catastrophic (item 2b).
12. `digital-and-supervision.md:208-217` — retire the three "Still open" bullets
    that design a deleted part (items 1d, 2c, 2d).
13. `ADR 0006:611-615` — "across the feedback resistor", "reconstruction pole"
    and "`C-FILT-PITCH` is deleted" are all three wrong (sweep item B).
14. `bom.csv:36` `D-REVPOL` and `ADR 0006:562` — replace the 20-cent figure with
    the reasons that hold (sweep item A).

**Low:** `bom.csv:70` `PCB-MODULE` description; `ADR 0004:35-40` MISO pin block;
`ADR 0004:361` power-switch rationale; `pitch-stage.md` 1 nF vs 2.2 nF.
