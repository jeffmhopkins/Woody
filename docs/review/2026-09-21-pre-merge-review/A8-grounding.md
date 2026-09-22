# A8 — grounds and return paths, across all three boards and the cable

**Wave:** 2026-09-21 pre-merge review. **Slice:** returns, bonds, star point,
ground-coupled pitch error. **Cold:** no prior `docs/review/**` was read.

**Findings are node-indexed** — filed against a net or a bond, not a file.
Every claim carries `[repo] path:line`, `[calc]`, `[datasheet]` or
`[from memory]`. Nothing was fixed; this is a report.

**Method.** Read every `hardware/**` page and `circuit.yaml`, the six ADRs that
name a ground (0003, 0004, 0005, 0006, 0009, 0014), `docs/reference/pcb-pipeline.md`,
`docs/reference/latency-budget.md`, `config/figures.yaml`, `hardware/bom.csv`
and `hardware/unplaced.csv`, and the banked Thonkiconn footprint. The
arithmetic in §6 was re-derived from scratch and then compared to the corpus.

**Headline.** The corpus says there are four returns. There are **twelve named
conductors or bonded metal bodies** acting as returns or references, and
**five of them have no owner** — no document says what they attach to.
`AGND` is three different nets under one name, not two. And the one rule the
whole plan rests on — *every milliamp leaves through the power inlet's ground
pin* — is **false by inspection** at the six output jacks, because the corpus
never assigns the jack sleeves and never states that the 2 mm aluminium panel
is a conductor.

---

## 1. The return inventory the corpus does not have

`docs/decisions/0004-cv-interface-module.md:614-621` names four returns
`[repo]`. `docs/reference/pcb-pipeline.md:225-227` repeats the same four as a
post-layout assertion `[repo]`. Here is what the corpus actually contains.

| # | Name **as spelled in the corpus** | Originates | Carries | Instrument end | Module end | Meets the others at |
|---|---|---|---|---|---|---|
| **N1** | `PWR_GND` (umbilical pin 6) | module star, `J-PWR-EURO` GND pin `[repo] hardware/module/power-entry/power-entry.md:23` | `umbilical-current` = 359 mA `[repo] config/figures.yaml:458-461` | the carrier's **whole-board pour**, "this board's only supply return" `[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md:17` | own copper to the star, touching nothing `[repo] 0004:634-636` | the star, and nowhere else *(claimed)* |
| **N2** | `DIG_GND` (umbilical pin 8) | — | SPI edge/displacement current, `CS`'s return partner `[repo] 0004:99` | **UNSTATED — see F2** | **DISPUTED — see §4** | unknown |
| **N3** | "module analog return" (ADR 0004's prose) = `AGND` / `AGND(module)` on every module page | module star | 6 × OPA2197 + INA828 supply return, DAC `AVDD` return, LM317 return, `R4`/`R5`, `C_cm`×2, output RC 330 nF, `R-GAIN-FLOOR`, the summer's (+) input, `C-OUT-BREATH`, `C-FILT-MOD`×4, `C-AA-PITCH`, `C-FILT-PITCH`, the shaper's 2×10 k divider, the pitch `V_ref` buffer `[repo]` (nine pages) | n/a | its own region, joining at the star `[repo] 0004:638-639` | the star |
| **N4** | `AGND` (umbilical pin 2) | the carrier's analog star `[repo] hardware/carrier/carrier.md:134` | **nothing** — in-amp `IN+` bias through `R2` into `R5` 1 M and `R-BIAS-INAMP`, tens of nA `[repo] hardware/bom.csv:77` | leaves through `R1b` `[repo] breath-sense-link.md:41` | terminates at `IN+` and the 1 MΩ pair; **does not reach the star** `[repo] 0004:640-642` | **nowhere** |
| **N5** | `AGND-local` / "analog star point" (carrier) | the carrier | `C-REF-OUT`×2 + their 100 nF, the sensor's 100 nF at `VS`, `R-ADCDIV-L`, `C-AA-ADC` — ~13 mA of analog supply current `[repo] breath-sense-link.md:98-104` | **one tie to `PWR_GND` at the umbilical connector** `[repo] carrier.md:134-136`, `breath-sense-link.md:94-96` | n/a | carrier `PWR_GND`, one tie |
| **N6** | chain-bus `GND` ×5 (`J-CHAIN` pins 1,3,5,7,9) | the carrier | `C-DECOUPLE-165`, `C-KEY`, every closed key switch (`key-scan-current`), the marker straps `[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:208-209`, `hardware/cluster/key-register/key-register.md:23` | carrier pour | n/a | never named as `PWR_GND` anywhere — **see F3** |
| **N7** | bare `GND` on module digital pages | — | `OE`×4 `[repo] hardware/module/digital-and-supervision/digital-and-supervision.md:29,53`; `R-LDAC` 0 Ω strap and the `LK-CLR` pad `[repo] hardware/module/dac8568/dac8568.md:40-44` | n/a | **UNSTATED** | unknown — **see F4** |
| **N8** | Eurorack bus ground, six ribbon conductors ≈17 mΩ | the rack PSU | the whole module's net return | n/a | the star's **only** exit | the rack |
| **N9** | aluminium **key plate** | instrument | touch/ESD, body capacitance | `MECH-GNDBOND` → `PWR_GND`, "never `AGND`" `[repo] hardware/bom.csv:6`, `0009:510-517` | n/a | carrier `PWR_GND` |
| **N10** | **10HP aluminium panel** + six `J-CV` sleeves + the module etherCON shell | module | every patch cable's return, and the rack rails | n/a | **UNASSIGNED** | **see F1 — this is the big one** |
| **N11** | `MECH-BACKPLATE` (instrument etherCON mount) | instrument | — | "TBD — **aluminium or ply**", "tied into the same stack that carries the keys" `[repo] hardware/bom.csv:125`, `0009:327-329` | n/a | **material undecided → bond undecided** |
| **N12** | the **cable shield** (STP/FTP "preferred") | — | unknown | unstated | unstated | **see F5** |

**Four in the plan, twelve in the corpus.** N5, N6 and N7 are aliases or
subsets that no document reconciles; N10, N11 and N12 are conductors that
exist physically and appear in no ground plan at all.

---

## 2. `AGND` — every appearance, and where it is treated as a return

`AGND` is a sense conductor carrying no power current in exactly **one** of
its three senses (N4). Here is every appearance in the design corpus,
classified.

### 2a. Correct — sense-only, flagged as such

- `[repo] 0004:45-46, 99, 108, 621, 640-642` — the rule, four times.
- `[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:41` —
  "**A signal leg, not a local ground**… **Not** the module's `AGND`". This
  is the single best line in the corpus on the subject.
- `[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:39` and
  `sim/README.md:55-57` — same, and the sim README explicitly warns that a
  model tying it to the module's `AGND` "has deleted the common-mode term".
- `[repo] hardware/carrier/carrier.md:134` — `J-UMB` pin 2 through `R1b` to the
  carrier analog star.
- `[repo] hardware/bom.csv:6` / `0009:510-517` — `MECH-GNDBOND` to `PWR_GND`,
  **never** `AGND`, with the body-capacitance reason. Correct and well argued.

### 2b. **Bare `AGND` used to mean the module analog return** — the collision, live

Every one of these is the *module* return, spelled with the *umbilical
conductor's* name and no qualifier:

| Node | Where | What returns there |
|---|---|---|
| `AGND` | `hardware/module/pitch-stage/pitch-stage.md:23,198` | `C-AA-PITCH` 10 nF, `C-FILT-PITCH` 10 nF |
| `AGND` | `hardware/module/mod-channels/mod-channels.md:31,59` | `C-FILT-MOD` 82 nF × 4 |
| `AGND` | `hardware/module/breath-response-shaper/breath-response-shaper.md:28` | the 2 × 10 k divider's bottom leg |
| `AGND` | `hardware/module/dac8568/dac8568.md:23` | "The analog star, single tie" |
| `AGND` | `hardware/module/breath-output-stage/breath-output-stage.md:79,86` | the summer's (+) input, `C-OUT-BREATH` 330 nF |
| `AGND` | `hardware/module/digital-and-supervision/notes.md:33` | the (superseded) `R-CLR-PD` |
| `AGND` | `hardware/module/power-entry/power-entry.md:31,156` | the interfaces row, and the rule sentence |

**F-AGND-1 — `breath-output-stage.md` spells the same node two ways inside one
drawing.** `AGND(module)` at line 65, bare `AGND` at lines 79 and 86, for the
same net `[repo]`. A transcription that honours the qualifier at line 65 and
not at line 79 splits one net in two; a transcription that ignores it merges
the module return into umbilical pin 2. Both are silent.

**F-AGND-2 — the module analog return has no net name of its own.** ADR 0004
calls it "the module analog return" in prose `[repo] 0004:620` and never
names it. Every page that has to draw it therefore reaches for `AGND`. The
collision is not a transcription slip; it is **forced by the absence of a
name**. `docs/reference/pcb-pipeline.md:58-62` treats it as a netlist-import
hazard `[repo]`; it is upstream of that — it is a naming gap in the ADR.

**F-AGND-3 — `ROADMAP.md:53` states the rule in the form that is false.**
E12's instruction to the builder reads "`AGND` not a return at all" `[repo]`.
Held against the module pages in 2b, where `AGND` *is* the return for eleven
components, this instruction is unexecutable as written. ROADMAP.md is in the
design corpus (`CLAUDE.md` §6) and is the document the person laying out the
board will follow.

### 2c. `AGND` given a pour, bonded, or treated as a return

- **`docs/reference/pcb-pipeline.md:31`** — "the router ploughing through the
  `AGND` **star**" `[repo]`; **:101** — "This plan gives `AGND` no zone and a
  keepout" `[repo]`. These two sentences are about *different* `AGND`s: a star
  is a property of N3/N5, a keepout of N4. The page does not say which.
- **`hardware/carrier/carrier.md:99,101,122`** — `AGND-local` used as the
  return symbol for `C-REF-OUT`, the sensor's `VS` decoupler and `C-AA-ADC`
  `[repo]`. This is N5 and is correct, but the name is one hyphenated suffix
  away from N4 on the same drawing (`J-UMB pin 2 AGND`, line 134).
- **`docs/decisions/0003-breath-sensing-path.md:686-697`** — see F6. The ADR
  that owns the star-point definition still bonds `AGND` to a board that does
  not exist.
- **`docs/decisions/0014-lighting.md:247`** — "`AGND` rises → the CV reads
  lower" `[repo]`. See F9: this models `AGND` as a ground whose potential
  moves the reading, which is the single-ended model the differential receiver
  exists to refute.

**Nothing in the corpus bonds `AGND` (N4) to a ground or gives it a pour.**
The rule survives in *substance* everywhere it is drawn. What has failed is
the **name**, and `hardware/module/pitch-stage/bom.csv:2` shows the corpus
already knows it: "~60 nA against a 350 mA power return = 0.2 ppm, so AGND's
no-current rule survives" `[repo]` — a defence of the rule written against
N3's resistors, filed under N4's name.

---

## 3. The named collision — verified, both halves still live

`docs/reference/pcb-pipeline.md:58-62` records that `AGND` means two things
and `BREATH` means two things `[repo]`. **Both collisions still exist after
the restructure.** Exactly which document means which:

### `BREATH`

| Sense | Documents |
|---|---|
| **The umbilical conductor**, `J-UMB` pin 1 — the sensor's buffered output | `0004:99,891`; `carrier.md:50,116`; `breath-sense-link.md:40`; `breath-receive-stage.md:37,59`; `config/figures.yaml:220` |
| **The module's output jack**, the far end of the gain/offset stage | `breath-output-stage.md:24` ("`BREATH` \| out \| panel jack") and its drawing's last line; `breath-receive-stage.md:105` ("BREATH jack"); `module.md`; `0004:653` (panel silkscreen) |

Shorting these two gives the in-amp input driven by its own output stage
nine gain stages downstream. `hardware/interfaces/README.md:24-28` states the
collision explicitly `[repo]`, and `breath-sense-link.md:33-37` disambiguates
it in the Interfaces preamble `[repo]`. **The mitigation is a prose note in
two interface pages; the six drawings still carry the bare name.**

### `AGND`

| Sense | Documents |
|---|---|
| **N4** — the umbilical sense conductor, pin 2 | `0004`; `carrier.md:50,134`; `breath-sense-link.md:41`; `breath-receive-stage.md:39,59`; `0003:341-349`; `figures.yaml:220` |
| **N3** — the module analog return | `pitch-stage.md`; `mod-channels.md`; `breath-output-stage.md`; `breath-response-shaper.md`; `dac8568.md`; `power-entry.md:31`; `breath-receive-stage.md:45,70-101` |
| **N5** — the carrier analog return (as `AGND-local`) | `carrier.md:99-122`; `breath-adc/breath-adc.md:26`; `breath-excitation-reference/breath-excitation-reference.md:27` |

**F3-1 — the collision is three-way, not two-way.** `pcb-pipeline.md` and
`interfaces/README.md` both describe it as two-way `[repo]`. N5 is a third
sense, introduced by the 2026-09-21 restructure when `carrier.md` §2 was split
into `breath-adc/` and `breath-excitation-reference/`, and it is not recorded
in either statement of the collision.

**F3-2 — `interfaces/README.md:26-27` claims "**both** collisions are between
the two ends of one of these three blocks"** `[repo]`. That is true of
`BREATH` and true of the N3/N4 half of `AGND`. It is **false of N5**, which
lives entirely on the carrier — so the `End` column that the README offers as
the mitigation cannot separate `AGND-local` from `AGND`, because both are at
the same end.

---

## 4. `dig-gnd-topology` — the dispute is live, and wider than the register says

`config/figures.yaml:387-399` tracks it as `disputed`, with three candidates
`[repo]`. Verified against the live corpus:

| # | Answer | Document, **as it stands now** |
|---|---|---|
| **A** | "**`DIG_GND` likewise** — its own path to the star." | `docs/decisions/0004-cv-interface-module.md:637` `[repo]` |
| **B** | "**`DIG_GND` is *not* given its own path to the star**, which an earlier revision of ADR 0004 asked for: a 2 MHz SPI return wants the pour directly under its trace, and routing it to a distant star point is the classic split-plane mistake." | `hardware/module/power-entry/power-entry.md:153-156` `[repo]` |
| **C** | "└── analog star, single tie (ADR 0004)" — the `DIG_GND` rail in the drawing terminates there. | `hardware/module/digital-and-supervision/digital-and-supervision.md:60` `[repo]` |

**F4-1 — the dispute is LIVE and has not been silently settled.** ADR 0004:637
still says A. `power-entry.md:154-155` still says ADR 0004 "asked for" A in an
"earlier revision" — implying it was corrected. **It was not.** The register's
own note says this `[repo] config/figures.yaml:398-399`; I confirmed it by
reading line 637, which is unchanged. This is the project's named failure mode
in its purest form: the correction landed on the schematic page where the
editing was happening, and the ADR the reader opens still says the opposite.

**F4-2 — there is a FOURTH document, and the register does not list it.**
`ROADMAP.md:53` (E12): "**Ground laid out to the star rule in ADR 0004** — one
origin at the power inlet, `PWR_GND` and `DIG_GND` **each on their own
copper**" `[repo]`. That is answer **A**, restated in the imperative, in the
document that tells the builder what to do at layout. The register lists three
candidates from three documents; there are **four documents and A has two
votes**. `ROADMAP.md` is in the design corpus (`CLAUDE.md` §6).

**F4-3 — the three line citations in the register are all stale.**
`[repo] config/figures.yaml:393-395` cites:
- `docs/decisions/0004-cv-interface-module.md:**627**` — line 627 is
  "varies with it — which is why a review measured this as **5.7–7.2 cents of**".
  The claim is at **:637**, ten lines later `[repo]`.
- `hardware/module/power-entry/power-entry.md:**495-498**` — **the file is 173
  lines long** `[calc: wc -l = 173]`. The claim is at **:153-156**. The
  citation survived the 2026-09-21 split that moved the load switch and the
  panel LED out of that page.
- `hardware/module/digital-and-supervision/digital-and-supervision.md:**53**` —
  line 53 is "`│ OE x4 → GND │  tied ENABLED`". The claim is at **:60** `[repo]`.

A `disputed` register entry whose whole value is *"here are the three places
that disagree"* points at three wrong places. One of them points into empty
space. `tools/check-staleness.py` cannot see this — it greps values, and a
line number is not a value.

**F4-4 — C is not a third answer; it is B's consequence, and it is the worst
case.** Answer C ties `DIG_GND` to the **analog** star. Answer B says the
2 MHz return should stay under its own trace. Both are satisfied only if the
pour under the SPI trace *is* the analog region — which puts the SPI return
current in the same copper as the pitch stage's `V_ref`. Nobody has costed
that (see F10-e). If the corpus adopts B and C together without saying so, it
has adopted the one option ADR 0004:623-627 spends a page arguing against.

**F4-5 — the instrument end of `DIG_GND` is unstated, and nobody notices.**
Every statement of the dispute is about the module end
(`power-entry.md:31`, `digital-and-supervision.md:26`,
`spi-link.md` `DIG_GND` row `[repo]`). At the instrument end,
`power-entry-instrument.md:17` says `PWR_GND` is "**this board's only supply
return**" `[repo]` — so `DIG_GND` must bond to the `PWR_GND` pour somewhere on
the carrier, and **no document says where**. That bond closes a loop: the SPI
return then has two parallel paths home (pin 8, and pin 6 via the carrier
pour), and the loop area is the whole umbilical. `spi-link.md`'s row says
"Where it ties is the disputed figure, **not a fact either end settles**"
`[repo]` — which is accurate and is also the problem.

**F4-6 — `U-TVS-SPI` clamps to the wrong return.**
`hardware/interfaces/spi-link/spi-link.md` and `carrier.md:218,292`: the 4-channel
array on `SCLK`/`MOSI`/`CS` goes **to `PWR_GND`** at the connector `[repo]`.
The signals' stated return partner is `DIG_GND` (pin 8). An ESD or clamp event
therefore dumps into pin 6 while the signal's return conductor is pin 8 — the
clamp current takes a different conductor home from the signal it is
protecting. This is only harmless if `DIG_GND` and `PWR_GND` are the same node
at the connector, which is answer B/C's instrument-end mirror and is exactly
what F4-5 says is unwritten.

**F4-7 — thirteen circuits declare a dependency on a figure whose value is the
string "DISPUTED".** `fig:dig-gnd-topology` appears in the `depends_on` of
`module/{power-entry, digital-and-supervision, dac8568, pitch-stage,
mod-channels, breath-receive-stage, breath-output-stage, breath-response-shaper,
panel-led}`, `carrier/{power-entry-instrument, display-and-service-uart}` and
`interfaces/{spi-link, breath-sense-link}` `[repo]` (13 `circuit.yaml` files).
`hardware/module/module.md:37-40` names it as gated on the 2-vs-4-layer
decision `[repo]`, as does `pcb-pipeline.md:92-96` `[repo]`. The gating is
correctly recorded; the point here is the blast radius — **more than half the
circuits in the project are downstream of one unanswered question.**

---

## 5. The star point — five things that do not reach it the claimed way

The claim: "**The origin is the Eurorack power inlet's ground pin.** Every
milliamp in the module leaves through it, so it is the one point entitled to
be called ground" `[repo] 0004:609-611`.

### F1 — **The six `J-CV` jack sleeves and the aluminium panel. Unassigned, and a second return to the rack.**

*Node: `J-CV` pin 1 (SLEEVE) ×6 → `PANEL` → rack rails → rack chassis → bus ground.*

- `J-CV` is `PJ398SM` (Thonkiconn) ×6. Its pinout is nailed down in the BOM:
  "PIN 3 = TIP, PIN 2 = TIP-NORMAL…, **PIN 1 = SLEEVE**" `[repo] hardware/bom.csv:97`.
- **No document in the design corpus says what pin 1 connects to.** I grepped
  every `hardware/**` page, every ADR and every reference doc. Six output
  stages name their jack as an output node (`PITCH`, `MOD 1`–`4`, `BREATH`)
  and none names its return `[repo] pitch-stage.md:21, mod-channels.md:29,
  breath-output-stage.md:24`.
- The bushing is **D6.0 mm with 4.5 mm of thread** `[repo] hardware/bom.csv:97`
  and mounts through `PANEL`, which is "**2 mm aluminium**, 10HP × 3U"
  `[repo] hardware/bom.csv:62`, also `pcb-pipeline.md:242`. On this part the
  threaded bushing is the sleeve contact `[from memory]` — corroborated
  negatively by the banked footprint, which has exactly **three** pads,
  `T`, `TN`, `S`, and **no separate shell or bushing terminal**
  `[repo] datasheets/connectors/PJ398SM.kicad_mod:41-43`. **Confirm on a real
  part before layout** — but if it holds, then:
  - all six sleeves are **shorted together by the panel**, regardless of how
    they are routed on the PCB, and
  - the panel bolts to the rack rails, which are the case chassis, which in
    every standard Eurorack case is bonded to the bus-board ground at the PSU
    `[from memory]`.
- **Consequence:** there is a conductive path from the module's jack sleeves to
  the rack ground that **does not pass through `J-PWR-EURO`'s GND pin**.
  ADR 0004:610's "every milliamp leaves through it" is false for every patch
  cable plugged into the module. The module has a second ground connection to
  the rack, in parallel with the ribbon, through a 2 mm aluminium plate whose
  resistance is far lower than the six ribbon conductors' 17 mΩ.
- This is not a small effect on the very term §6 is about: it **parallels** the
  ribbon path and therefore *reduces* the 7.4-cent term — but it does so
  through an uncontrolled, patch-dependent impedance that changes every time a
  cable is plugged in, and it puts jack-sleeve current into the panel and
  thence into the etherCON shell (F5).

**Nothing in the corpus models the panel as a conductor.** `panel/panel.md` is
geometry only and carries no `## Interfaces` table by design `[repo]`.

### F2 — the plate bond reaches the star through **two** paths, not one

*Node: `MECH-GNDBOND` → carrier `PWR_GND` pour → `J-UMB` pin 6 → module star.*

The intended path is stated and correct `[repo] hardware/bom.csv:6`,
`power-entry-instrument.md:62`, `0009:510`. But `MECH-BACKPLATE` — the plate the
instrument's etherCON mounts to — is "**TBD — aluminium or ply**" and is to be
"tied into the same stack that carries the keys"
`[repo] hardware/bom.csv:125`, `0009:327-329`. If it is aluminium, the
instrument's etherCON **shell** is bonded to the key plate, i.e. to `PWR_GND`,
at the connector. Combined with F5 that gives the key plate a second route to
the module. **A mechanical `TBD` decides an electrical bond**, and neither the
BOM row nor ADR 0009 says so.

### F3 — the key loom's five grounds are `PWR_GND` and are never called that

*Node: `J-CHAIN` pins 1, 3, 5, 7, 9.*

Five alternating ground conductors run 265 mm down the body carrying
`C-DECOUPLE-165`, `C-KEY` and every closed key switch's current
`[repo] key-chain-loom.md:208-209`, `key-register.md:23`,
`key-switch-network.md:20`. `key-scan-current` is a tracked figure and
`carrier.md:170-175` costs 18 closed keys at **25.8 mA** `[repo]`. On the
carrier the only return is the `PWR_GND` pour `[repo] power-entry-instrument.md:17,22`,
so these are `PWR_GND` — but **no document says so**, and the bare name `GND`
is used throughout. A netlist built from these pages gets a `GND` net that does
not connect to `PWR_GND`.

**F3a — `key-chain-loom.md:77` proposes `U-TVS-CHAIN` clamping "to `DIG_GND`"**
`[repo]`. **`DIG_GND` does not exist on the carrier or on any cluster board.**
It is an umbilical conductor between the carrier and the module
`[repo] 0004:99`, `figures.yaml:220`. The proposed part would clamp four
instrument-side chain signals to a net that is not present on that board. This
is a wrong net name in a proposed BOM row, and it is the kind of error
`pcb-pipeline.md:58` says the netlist stage cannot catch.

### F4 — bare `GND` on the module's digital pages

*Nodes: `74AHCT125` `OE`×4; `R-LDAC` 0 Ω strap; the `LK-CLR` solder pad.*

`digital-and-supervision.md:29,53` ties `OE`×4 to "`GND`"; `dac8568.md:40-44`
straps `LDAC` and the `CLR` link pad to "`GND`" `[repo]`. The module has a star
(`J-PWR-EURO` GND), an analog return (N3) and a disputed `DIG_GND`. **These
three pins are assigned to none of them.** For `LDAC` and `CLR` the choice
matters: both are DC straps on a part whose `AGND` row says "the analog star,
single tie" `[repo] dac8568.md:23`, so a strap to a *different* ground puts a
DC offset between a DAC control pin and the DAC's own reference.

### F5 — the cable shield: sixteen words, and the condition that makes it real

*Node: `CABLE-UMB` shield ↔ etherCON shells ↔ `PANEL` / `MECH-BACKPLATE`.*

The entire shield policy is `0004:850-852`: "**Shielded (STP/FTP) preferred.**
… the shield is free at this price and the breath pair is the one signal with
no digital margin to spare" `[repo]`, echoed in `hardware/bom.csv:116`
("Shielded preferred"). **Neither end's bond is specified.**
`power-entry.md:127` costs it: "The cable shield, **if** the etherCON shell
bonds to the 10HP panel | **~7 cents**" `[repo]` — and
`power-entry.md:136-137` says so itself: "It is a grounding and shield-bonding
decision, and **the shield policy is sixteen words in the whole repo**."

**The condition is already satisfied by two other decisions.** The module
etherCON is a metal-shell D-series chassis connector mounted through the 2 mm
aluminium panel `[repo] hardware/bom.csv:98`; at the instrument end,
`MECH-BACKPLATE` may be aluminium (F2). So unless someone deliberately
isolates it, the shield is **bonded at both ends**, and it becomes a second
conductor in parallel with `PWR_GND` carrying a share of 359 mA, joining the
instrument's key plate to the module's panel to the rack rails. That is a
ground loop enclosing the whole 2 m tether, and it is the one path that makes
`PWR_GND`'s "own copper, touching no other return" `[repo] 0004:634` untrue at
the cable rather than on the board.

### Where the star claim does hold

For completeness, these were checked and are consistent:
`umbilical-load-switch.md:18` — `C-TIMER`, `C-GATE`, `R-FB-LO` and the FET
source all return "to the star at the IDC" `[repo]`; `power-entry.md`'s drawing
takes `PWR_GND` from `D2`/`FB2`/`C2` straight to the star line `[repo]`;
`carrier.md:134-136`'s single tie between N5 and `PWR_GND` at the connector
`[repo]`; `display-and-service-uart.md:29` puts `J-DISP`'s two grounds on the
`PWR_GND` pour `[repo]`.

### F6 — ADR 0003 still defines the analog star on a board that does not exist

*Node: N5, the carrier analog star.*

`0003:692-694` `[repo]`: "**The star point is the analog ground pour on the
bottom cluster board**, at the sensor and reference, immediately adjacent to the
umbilical connector."

`breath-sense-link.md:88-90` `[repo]` answers it: "ADR 0003 names the star point
as 'the analog ground pour on the bottom cluster board' — **a board that does
not exist**; it means this one."

**The ADR was never corrected.** ADR 0003 is the document that defines the star
point (its heading is "The analog ground star point, defined"), and it is the
one a reader opens. Worse, the refuted location is still **drawn**:
`breath-receive-stage.md:51` labels the instrument side of the link
"`INSTRUMENT (bottom cluster board)`" with "`analog star ──[R1b 1k]`" beneath
it `[repo]`. Same shape as F4-1 — the fix landed on the interface page, not on
the owner or the drawing.

---

## 6. Ground-coupled error onto pitch — re-derived, and the corpus has two
## incompatible sets of numbers

### The scale factor, checked

1 V/oct ⇒ 1 cent = 1/1200 V = **833.3 µV**, so **1 mV = 1.200 cents** `[calc]`.
For the pitch stage `Vout = (1+k)·Vdac − k·V_ref` at `k = 1`, so
`∂Vout/∂V_ref = −1` and a millivolt on the reference is a millivolt at the jack
`[repo] pitch-stage.md:21,53-56`. This confirms
`pcb-pipeline.md:185` — "**1 mV on `V_ref` is 1.2 cents**" `[repo]`.

### The two sets

**Set A** — three documents, one partition:

| Term | Cents | Where |
|---|---|---|
| the module's internal ground | **5.7–7.2** | `0004:341`, `0004:627`, `0006:625`, `ROADMAP.md:200` `[repo]` |
| the rack's shared bus ground | **~4.8** | `0004:341`, `0004:644-645`, `0006:626`, `ROADMAP.md:200` `[repo]` |

**Set B** — one document, a different partition:

| Term | Cents | Where |
|---|---|---|
| the power ribbon's six ground conductors, ≈17 mΩ, 6.2 mV | **7.4** (24 on a flying bus) | `power-entry.md:125` `[repo]` |
| ~20–40 mΩ of busboard to a neighbouring module, 7–15 mV | **8–18** | `power-entry.md:126` `[repo]` |
| the cable shield, if the etherCON shell bonds to the panel | **~7** | `power-entry.md:127` `[repo]` |

### Re-derivation

| Check | `[calc]` |
|---|---|
| Set B row 1, internal consistency | 6.2 mV × 1.2 = **7.44 cents** ✓ |
| but 6.2 mV ÷ 17 mΩ = **364.7 mA** | matches **neither** tracked figure: `umbilical-current` = 359 mA (`figures.yaml:458`) nor the 392 mA module total (`figures.yaml:465`) |
| at 359 mA | 359 mA × 17 mΩ = 6.103 mV → **7.32 cents** |
| at 392 mA | 392 mA × 17 mΩ = 6.664 mV → **8.00 cents** |
| Set B row 2 | 7 mV → 8.4 c; 15 mV → 18.0 c ✓; implies **18.6–41.8 mΩ** at 359 mA |
| Set A rack-bus term, back-solved | 4.8 c → 4.0 mV → **11.1 mΩ** at 359 mA |
| Set A internal-ground term, back-solved | 5.7–7.2 c → 4.75–6.0 mV → **13.2–16.7 mΩ** of shared copper at 359 mA — plausible for ~1 cm of narrow trace (1 oz, 0.25 mm wide ≈ 20 mΩ/cm) but **stated nowhere** |
| Set B row 3, shield | ~7 c → 5.83 mV; **no derivation given, no current, no impedance** |

### Findings

**F6-1 — the rack-bus term is stated twice, 1.7–3.8× apart, both as live
fact.** ~4.8 cents in ADR 0004, ADR 0006 and ROADMAP; 8–18 cents in
`power-entry.md`. The entire difference is an **unstated busboard resistance**:
≈11 mΩ vs 20–40 mΩ `[calc]`. Neither number is in `config/figures.yaml`, so
`tools/check-staleness.py` is structurally incapable of noticing, and no
document cites the other.

**F6-2 — Set B's ribbon term (7.4 cents) exists in exactly one document and is
absent from every summary.** ADR 0004's four-return table `[repo] 0004:616-621`
and its grounding rules `[repo] 0004:633-646` do not mention the ribbon at all;
ADR 0004 attributes 5.7–7.2 cents to *on-board* shared copper. So the corpus
has an **on-board** term (Set A) and an **off-board ribbon** term (Set B) that
are different physical mechanisms, and both are labelled "the module's ground".

**F6-3 — the measurement plan covers only Set A.** `ROADMAP.md:200` (E6/E9):
"this measures the two ground terms that are left — **the module's own pour
(5.7–7.2 cents) and the rack's shared bus return (~4.8)**" `[repo]`. The two
*largest* terms in the corpus — 8–18 cents for the busboard and ~7 cents for
the shield — are not in the test. A gate that measures the two smallest of four
terms will pass and mean nothing.

**F6-4 — 6.2 mV restates a tracked figure's dependent instead of citing it.**
`CLAUDE.md` §1. `power-entry.md:125`'s 6.2 mV implies 365 mA; the register says
359 mA. Using the tracked figure gives 7.32 cents, not 7.4 `[calc]`. Small, and
it is the exact mechanism the project exists to prevent.

### What else couples in that nothing counts

**F6-5 — the breath output stage pushes ~7 mA of breath-correlated AC into the
module analog return.** *Node: `C-OUT-BREATH` 330 nF → N3.* The output RC is
1 kΩ + 330 nF to `AGND` `[repo] breath-output-stage.md:86`,
`breath-receive-stage.md:101`. At the 480 Hz corner with 10 V at the jack:
|Z| = √(1k² + (1/(2π·480·330n))²) ≈ 1.42 kΩ → **7.05 mA peak**, returning into
N3 `[calc]`. Add `C-FILT-MOD` 82 nF × 4 and `C-FILT-PITCH` / `C-AA-PITCH`
10 nF each. **This is the only current inside the module's analog region that
tracks breath**, which is the precise property ADR 0004:626-628 says makes an
error term untrimmable and audible `[repo]`. It is costed nowhere. Against
10 mΩ of shared analog copper it is 70 µV = **0.085 cents** `[calc]` — small,
but it is in the same region as `V_ref` and it is the mechanism, not the
magnitude, that the corpus says to watch.

**F6-6 — the jack-side feedback tap does not correct the sleeve path.**
`pitch-stage.md:21` — "**DC feedback is tapped here, not at the op-amp
output** — so whatever is patched in sits inside the loop" `[repo]` — and
`:257-260` concludes "the load no longer matters… gain 2.020000 for every load
from open circuit to 2 kΩ" `[repo]`. That is true of the **tip** side only. The
receiving module measures `V_tip − V_its_own_ground`, and the sleeve path from
our jack to its ground is outside our loop entirely. The whole 4.8-to-18-cent
rack-bus term lives in that path and the jack-side tap cannot touch it. No
document states this limit, and `pitch-stage.md:300-302` explicitly defers to
"the ground plan" without noting that its own headline fix does not reach there.

**F6-7 — `DIG_GND` carries a 2 MHz return current and has no cents figure.**
If answer B or C holds (§4), the SPI return shares copper with N3, which
carries `V_ref`. `power-entry.md:154-156` argues the routing case `[repo]`;
nobody has converted it to millivolts. Given that 1 mV = 1.2 cents, this is
cheap to bound and has not been bounded.

**F6-8 — the star pad's thermal relief, 0.053 cents, is in one non-ADR
document.** `pcb-pipeline.md:197-199`: "**Star pad solid, everything else
thermal.** A default 4-spoke relief on the star pad costs **0.053 cents** at
359 mA — a quarter of the tightest pitch-budget candidate, from one
DRC-passing pad" `[repo]`. Correctly derived and correctly cited against
`umbilical-current`. It appears in no ADR and in no ROADMAP row, i.e. it is not
where the person laying out the board will look.

**F6-9 — the panel LED's return is undrawn.**
*Node: `LED-PANEL` cathode → ?* `panel-led.md:15`: "LED return | ref |
`module/power-entry` | `dig-gnd-topology` | **Not drawn anywhere in the
corpus.** The rail it comes from is the analog one" `[repo]`. `R-LED-PANEL` is
2k2 from +12 V analog `[repo] hardware/bom.csv:64`, so
(12 − 2)/2200 = **4.5 mA** `[calc]` of DC leaves the analog rail and returns to
an unspecified node. Constant, therefore trimmable, therefore low risk — but it
is the only non-signal current in the analog region and the page itself flags
it as undrawn.

**F6-10 — the `LT5400` exposed pad still has no ground.** *Node: `U-MATCH-PITCH`
EP.* 1.88 × 1.68 mm, floating, **5.5 pF** to the resistors against 1.4 pF
resistor-to-resistor, i.e. the dominant stray on the 1 V/oct network; ADI says
tie it to "a quiet AC ground" `[repo] pitch-stage.md:306-313`,
`pcb-pipeline.md:97-106`. `pcb-pipeline.md:106-107` notes the circularity exactly:
"A pad told to find 'a quiet AC ground' on a board that has not settled where
its grounds meet is a decision deferred twice, not once" `[repo]`. Recorded
here because it is a grounding decision, correctly filed elsewhere, and still
open.

---

## 7. One finding outside the ground plan, raised because it is grounding-adjacent

**F9 — ADR 0014 models the breath channel single-ended, and the number it gets
is ~1750× too large.**

`0014:243-247` `[repo]`: "Through the CV path it is negative feedback. More
breath → brighter LEDs → **`AGND` rises → the CV reads lower.** Loop gain is
around 0.004, so the effect is **0.4 % of gain compression**."

That mechanism requires `AGND`'s potential to move the reading. It cannot: the
module senses `V_BREATH − V_AGND` differentially
(`Vout = −2.185·(V_BREATH − V_AGND) + V_REF`
`[repo] breath-receive-stage.md:88`), and both legs are referenced to the same
carrier analog star, so an LED-induced shift is **common-mode** and is rejected.
`0014:498-501` says so itself, two hundred lines later: "**Without `AGND`**, the
light show would appear on the breath CV — a **34 mV** ground offset" `[repo]`
— the correct conditional.

`[calc]`, using the corpus's own link CMRR of 70.2 dB with `R1b` fitted
`[repo] breath-sense-link.md:77`:
34 mV × 10^(−70.2/20) = **10.5 µV** referred to the in-amp input, against a
4.6 V sensor span = **2.3 × 10⁻⁴ %**, not 0.4 %. **Ratio ≈ 1750×.**

The direction matters more than the magnitude: `0014:247`'s 0.4 % is a
**gain-compression** claim about the top of the breath range, offered as a
characterised behaviour. If it is really 2.3 × 10⁻⁴ %, the paragraph describes
an effect that does not exist, and the two "free fixes" it prescribes
(`0014:254-262`) are sized against a step that is 1750× smaller than assumed.

**This is a claim, not a verdict.** It should be checked by whoever owns
ADR 0014 — specifically whether there is a mechanism I have not seen (the ADC
path at `0014:249-253` is genuinely single-ended and genuinely does have this
loop; it is the **CV** path's arithmetic that does not survive).

---

## 8. Incidental, outside this slice

- **`ROADMAP.md:53` still says 8HP.** "etherCON braced to the PCB — good
  practice **at 8HP** rather than the structural necessity it was at 6HP"
  `[repo]`, against ADR 0004:830's "**At 10HP** this is good practice rather
  than a structural necessity" `[repo]`. `panel-width`'s `forbidden` list has
  four 8HP spellings — `"The panel is 8HP"`, `"inside 8HP"`, `"at 8HP this"`,
  `"Comfortable at 8HP"` `[repo] config/figures.yaml:276` — and **none of them
  matches `"at 8HP rather than"`**. Fifth recorded escape of the same class:
  the pattern list was written from the spellings in front of the author. The
  checker reports PASS.

---

## 9. What I would do first, if anyone is choosing

Ordered by cost-if-wrong, not by effort:

1. **F1 (jack sleeves / panel).** Confirm the Thonkiconn bushing–sleeve
   connection on a real part, then write down what the panel is. It falsifies
   the star rule's headline sentence and it is free before layout.
2. **F4-1 + F4-2.** Correct ADR 0004:637 or mark it superseded, and add
   `ROADMAP.md:53` to the register's candidate list. Then fix the three stale
   line citations in `config/figures.yaml:393-395` — the entry currently sends
   its reader to a line that does not exist.
3. **F-AGND-2.** Give the module analog return a name. The three-way collision
   is forced by its absence and no amount of `End`-column discipline closes it.
4. **F5 + F2.** Decide the shield bond and `MECH-BACKPLATE`'s material together.
   They are one decision wearing two hats, and one of them is currently a
   mechanical `TBD` deciding an electrical bond.
5. **F6-1 + F6-3.** Pick one partition of the ground-coupled pitch terms, put
   it in `config/figures.yaml`, and re-scope E6/E9 against it. Four terms,
   two documents, no register entry, and the test covers the two smallest.
