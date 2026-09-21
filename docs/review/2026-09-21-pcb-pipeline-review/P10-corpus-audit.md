# P10 — Does the PCB pipeline plan agree with this repo's design corpus?

**Slice:** every claim `docs/reference/pcb-pipeline.md` makes *about this
project*, checked against `hardware/**`, `docs/decisions/**`,
`docs/reference/**`, `config/**`, `firmware/**`, `README.md`, `ROADMAP.md`,
`CLAUDE.md`. Toolchain claims (KiCad/SKiDL/Freerouting behaviour) are out of
slice except where they assert something about this repo.

**Cold.** No prior review directory was read.

**Version reviewed:** 335 lines, `md5 eccf2314fb17c892201bac174923bca8`,
at commit `233f0b9` *"Add SPICE verification…"*. The file grew from 294 to 335
lines *during* this review (the SPICE stage, §2, landed mid-audit). Line numbers
below are against the 335-line version.

**Headline.** The plan's tooling reasoning is sound and mostly in slice-adjacent
territory. Its *statements about this project* have drifted in the exact way
`CLAUDE.md` names: **five numbers restated from elsewhere, two of them already
corrected in the owning document, one of them arithmetically wrong, and one of
them a figure the register marks `disputed`.** The grounding section follows a
revision of ADR 0004 that `power-entry.md` explicitly declines. The hand-route
list is missing the nets the corpus spends the most words on.

---

## 1. Verdict table

| # | Quoted claim (plan line) | Corpus | Verdict |
|---|---|---|---|
| 1 | "module PCB and its panel (E12), then carrier and the four cluster boards (E13)" (333–334) | `ROADMAP.md:E12`, `ROADMAP.md:E13`; `hardware/bom.csv:114` `PCB-CLUSTER` qty 4 `[repo]` | **CONFIRMED** |
| 2 | "ROADMAP puts them in that order because the carrier will spin at least once" (334–335) | `ROADMAP.md` gives that reason for **M5-after-E13** and **body-close-after-E13**, not for E12-before-E13; the E-track states no reason for its own numbering `[repo]` | **UNSUPPORTED** (reason invented; the ordering itself is right) |
| 3 | "one module per schematic page … imports the six" (95–101) | `hardware/module/` holds exactly six pages `[repo]`. (Note the corpus miscounts itself: `digital-and-supervision.md:3` says "Fifth and last module page", `breath-output-stage.md:3` says "Sixth module page". Six is right.) | **CONFIRMED** |
| 4 | "0.5 mm of 1 oz copper is roughly a 1 A trace at a 10 °C rise" (183–184) | IPC-2221 external, 1 oz = 1.378 mil, `I = 0.048·ΔT^0.44·A^0.725`: A = 19.685 × 1.378 = **27.13 mil²**, 10^0.44 = 2.7542, 27.13^0.725 = 10.946 → **I = 1.447 A** `[calc]`. 0.5 mm is a **1.45 A** trace, not a 1 A trace. A 1.0 A external trace is **0.30 mm**; 0.940 A is **0.276 mm** `[calc]` | **REFUTED** — understates by 45 % |
| 5 | "the load switch's path is specified at 1.0 A" (184–185) | `docs/decisions/0005-power-architecture.md:260` does say 1.0 A. `hardware/module/power-entry.md` — the owning schematic page — opens its load-switch rebuild with **"1. The limit is 0.940 A, not 1.0 A."** (47 mV / 50 mΩ) `[repo]` | **REFUTED** — restates a value the owning page corrects by name |
| 6 | "That is no margin." (185) | 0.5 mm external = 1.447 A against a 0.940 A limit = **54 % margin** `[calc]`. Even the plan's own `Default` class at 0.25 mm is a 0.875 A trace `[calc]` | **REFUTED** — and the conclusion is inverted |
| 7 | "`Power` \| `+12V`, `-12V`, `+5V`, `AVDD`, `PWR_GND`" (180) | `power-entry.md` drawing has **six** distinct supply nets: bus `+12V`, **`MODULE ANALOG +12V`**, **`UMBILICAL +12V`**, `MODULE ANALOG −12V`, bus `+5V`, `AVDD 5.21V` `[repo]`. `UMBILICAL +12V` — the only net that ever carries 0.94 A, and the one the width derivation is *for* — is absent from the class | **REFUTED / incomplete** |
| 8 | "60 dB of CMRR was already spent on one unmatched resistor" (199–200) | `breath-receive-stage.md` ("Symmetry"): the 60.2 dB loss is from `R1` having no twin — and **`R1b` fixes it**, is in `bom.csv`, and is **instrument-side** (`R1`/`R1b` are on the cluster board, not the module being laid out) `[repo]` | **REFUTED as stated** — past tense implies a standing loss; it is fixed, and it is not a module-board layout term |
| 9 | "three grounds, two zones, one star" (218) | ADR 0004 tabulates **four** returns arriving at this board: `PWR_GND`, `DIG_GND`, **the module analog return**, `AGND` — and says "**The analog return is its own region**, joining at the star and nowhere else. The DAC's `AVDD` return and the in-amp's `REF` tie belong in it." `[repo, docs/decisions/0004-cv-interface-module.md:605–630]` | **REFUTED** — the fourth return, which the corpus says needs its own region, has no zone, no keepout and no mention |
| 10 | "`PWR_GND` / `DIG_GND` — separate copper, one tie at the inlet" (201) and "as separate zones … a single deliberate tie at the power inlet" (227–229) | ADR 0004 says "`DIG_GND` likewise — its own path to the star." **`power-entry.md` ("Grounding") says the opposite:** "**`DIG_GND` is *not* given its own path to the star**, which an earlier revision of ADR 0004 asked for: a 2 MHz SPI return wants the pour directly under its trace, and routing it to a distant star point is the classic split-plane mistake." `[repo]` | **REFUTED by the owning page.** The corpus contradicts itself here; the plan picked the superseded side and flags no dispute |
| 11 | "`AGND` — a sense-only star, never a return" (197) | ADR 0004:630: "**`AGND` is not in this list** [of returns]. It terminates at the in-amp's IN+ and at the two 1 MΩ bias resistors, and that is all it does." It is a **two-terminal input net**, not a star `[repo]` | **PARTLY CONFIRMED** (never a return: yes) / **REFUTED** (it is not a star) |
| 12 | "`AGND` tied exactly once" (248) | ADR 0004:630 — IN+, `R2`/`R3`, **and both** 1 MΩ bias resistors; `breath-receive-stage.md` also returns two `C_cm` caps to `AGND(module)`. And `pitch-stage.md`, `mod-channels.md` and `breath-output-stage.md` all return jack caps and a floor resistor to a net they spell **`AGND`** `[repo]` | **REFUTED** — unsatisfiable as written; see §4.1 (net-name collision) |
| 13 | "This board is hand-soldered" (232) / "This board is hand-assembled" (266) | `bom.csv:70` says it of **`PCB-CARRIER`** ("2 layers, hand-assembled"); ADR 0013:250 says it of the carrier ("It can be assembled by hand"). **Nothing in the corpus says it of `PCB-MODULE`** (`bom.csv:71`) `[repo]` | **UNSUPPORTED** — true-by-inference (ADR 0013's package policy is repo-wide), never stated for the board the plan is about |
| 14 | "**Thermal reliefs on every through-hole pad**" (232) | ADR 0004:613–623 and `power-entry.md`'s ground table make milliohms load-bearing: 17 mΩ → 6.2 mV → **7.4 cents**, i.e. **0.43 cents per mΩ at 360 mA** `[calc from repo]`. A 4-spoke relief on the IDC star pin or the etherCON `PWR_GND` pin adds a few mΩ **exactly where the star rule exists to remove them** | **REFUTED as a blanket rule** — "every" contradicts ADR 0004 |
| 15 | "the largest *live* term in the pitch error budget at 5.7–7.2 cents" (222–223) | ADR 0004:332 and :617 give 5.7–7.2 cents. But `power-entry.md`'s own table lists **larger** live ground terms: ribbon 7.4 cents (24 on a flying bus), busboard 8–18 cents, shield ~7 cents `[repo]`. And `config/figures.yaml` marks `pitch-cents-budget` **`disputed`**: "two contradictory tables and no stated total" | **REFUTED** — not the largest, and ranked inside a budget the register says does not exist |
| 16 | "every decoupling cap within ~2 mm of the pin it serves" (250) | The only placement rule in the corpus is `bom.csv:43` `C-DECOUPLE`: "One per supply pin, **close to the pin**." No distance anywhere `[repo]` | **UNSUPPORTED** — 2 mm is invented (and is ~one 0805 body length, `bom.csv:43` package "0805 (2.0 x 1.25mm)") |
| 17 | "`hardware/bom.csv`, 11 columns" (280) | `CLAUDE.md`; `csv` header is 11 wide, 132 data rows `[repo, calc]` | **CONFIRMED** (but see §2 — restated, unregistered) |
| 18 | "update … **the column check in `tools/check-staleness.py`** in the same commit" (294–296) | `tools/check-staleness.py:84` — `hdr, n, problems = rows[0], len(rows[0]), []`. The column count is **derived from the header row**. `grep -n "11" tools/check-staleness.py` returns nothing `[repo]` | **REFUTED** — there is no column check to update |
| 19 | "`tools/check-staleness.py` scans `hardware/`, `docs/decisions/`, `docs/reference/`, `config/`, `firmware/`, `README.md`, `ROADMAP.md`" (300–302) | `tools/check-staleness.py:30–31` exactly `[repo]` | **CONFIRMED** |
| 20 | "the repo root keeps generated files out of the design corpus with no checker change" (302–303) | True of the checker `[repo]`. But **`README.md:98`**: "`hardware/` BOM, schematics, **PCB**, split by board" — and `mechanical/` is "CAD source, **2D cut exports**, drawings" `[repo]` | **CONFIRMED for the checker / REFUTED against `README.md`** — see §4.2 |
| 21 | "**Nothing generated under `hardware/`.** That directory is reviewed prose." (315) | `README.md:98` allocates PCB to `hardware/`; `hardware/bom.csv` is not prose; `hardware/controller/.gitkeep`, `hardware/module/.gitkeep`, `hardware/datasheets/.gitkeep` are placeholders for artifacts `[repo]` | **REFUTED** |
| 22 | "`MANIFEST.csv` records which are vendor-issued and which are community-authored" (296–298) | `datasheets/MANIFEST.csv:6` `NE8FDV.kicad_mod` notes "NOT A VENDOR DRAWING – …" `[repo]`. It is the free-text `notes` column, not a field | **CONFIRMED** (weakly — no queryable column) |
| 23 | "Prefer the footprints already banked in `datasheets/`" (296) | Banked `.kicad_mod`/`.dxf`: etherCON `NE8FDV`, `PJ398SM`, three Gateron KS-33, LilyGO outline, a 3HP panel `.kicad_pcb` `[repo]`. Of these only **two** (etherCON, PJ398SM) are module-board parts; `DAC8568CIPW`, `INA828IDR`, `LT1641-1CS8`, `LM317LZ`, `LT5400`, the DPAK FET have none | **CONFIRMED but thin** |
| 24 | "`tools/check-bom-parity.py` diffs the first two **by refdes**" (287) | `hardware/bom.csv` is **part-keyed, not refdes-keyed**: `SW1-n`, `CAP1-n`, `R-KEY-PU` (qty 24), `C-DECOUPLE` (qty 19), and `U-LOADSW` is **one row for three physical parts** ("LT1641-1CS8 + DPAK/SO-8 N-FET + sense R") `[repo]` | **REFUTED** — a refdes-keyed diff against a KiCad netlist cannot run without a mapping layer the plan does not mention |
| 25 | "this is the one place in the pipeline where it would otherwise happen silently" (288–290) | `tools/check-staleness.py:96` `check_refdes()` already flags "reference designators drawn in a schematic with no BOM row" `[repo]` | **REFUTED** — a one-way schematic→BOM parity check exists today |
| 26 | "`pitch-cents-budget` is **disputed** in `config/figures.yaml` — two contradictory tables and no stated total" (155) | `config/figures.yaml`, `pitch-cents-budget`, verbatim `[repo]` | **CONFIRMED** — and correctly *cited*, which makes line 222–223 the inconsistency |
| 27 | "The page claims the feedback network is 'a lead at every load tried'. This is the highest-risk item on that page by its own admission" (151) | `hardware/module/pitch-stage.md`: "The feedback network is a **lead** at every passive load tried"; "This is the highest-risk item on the page." `[repo]` | **CONFIRMED** |
| 28 | "The claim is 2.6° of phase margin and oscillation near 458 kHz without it" (152) | `hardware/controller/carrier.md:232–233` verbatim `[repo]` | **CONFIRMED** (note: carrier circuit, not module — E13, not E12) |
| 29 | "`R_o ≈ 75.8 Ω` is back-solved from a stated pole, not read, and SBOS737 is `BLOCKED`" (153) | `carrier.md:229–230`, `:252`, `:267` `[repo]` | **CONFIRMED** |
| 30 | "a ÷10 scaling would have put the knee above a hard blow" (156) | `breath-output-stage.md:227–235` `[repo]` | **CONFIRMED** |
| 31 | "`C-FB-PITCH` took **two independent reviewers** to establish that a cap in the feedback of a non-inverting stage is a 6.02 dB shelf" (138–140) | `pitch-stage.md` gives the 6.02 dB shelf and credits it to "an earlier version of this page" being wrong. The "two independent loop analyses" in that page are about **`C-FILT-PITCH` at the jack**, a different question `[repo]` | **UNSUPPORTED** (attribution; 6.02 dB itself is CONFIRMED) |
| 32 | "`LT1641` has no model anywhere — a researcher searched GitHub and GitLab" (162–164) | Corpus records only `datasheets/MANIFEST.csv` LT1641 `status=BLOCKED` and `power-entry.md`'s provenance warning `[repo]`. The search claim lives outside the design corpus | **UNSUPPORTED from the corpus** (may be true in a review dir; not citable as corpus) |
| 33 | "no copper under the **connector bore**" (252) | `bom.csv:71`: the D24.0 mm bore is in the **panel**; the board has an **etherCON notch** and a "4.5 mm web" `[repo]` | **PARTLY REFUTED** — wrong feature named for the board |
| 34 | "the FET's **thermal pad**" (205) | `power-entry.md`: "**DPAK or SO-8**, chosen against the single-pulse SOA curve"; `bom.csv:18` "SO-8 + DPAK or SO-8 FET", status `candidate` `[repo]` | **UNSUPPORTED** — assumes a package the corpus leaves open (an SO-8 FET has a drain paddle, not a DPAK tab) |

---

## 2. Tracked figures the plan restates instead of citing

`CLAUDE.md` rule 1: a figure in `config/figures.yaml` is stated **once**, in its
owner, and **cited by name** everywhere else.

### 2.1 Register entries restated (rules violation)

| Figure `id` | Register value / status | Where the plan restates it | Note |
|---|---|---|---|
| `pitch-compensation` | "2.2 nF, **op-amp OUTPUT to the (−) input**" — owner `hardware/module/pitch-stage.md` | **line 200–202**: "compensation cap from the op-amp *output*, protection resistor inside the DC loop" | Restates the substance of the value with no citation of owner or register. |
| `pitch-cents-budget` | **`disputed`** — "two contradictory tables and no stated total" | **line 222–223**: "the largest *live* term in the pitch error budget at **5.7–7.2 cents**" | Asserts a *ranking inside* a budget the register says does not exist. The same document cites this figure correctly at line 155 — so it both obeys and breaks the rule, 67 lines apart. |

That is the whole list against the register as it stands. **The register is the
problem, not the plan's discipline** — see 2.2.

### 2.2 Owned figures the plan restates that **are not in the register and should be**

Every one of these is a number owned by one document, copied into a second, and
invisible to `tools/check-staleness.py` (`PASS no live stale values` today — the
plan trips nothing, because none of these has a `forbidden` list).

| Number restated | Owner | Plan line | Status |
|---|---|---|---|
| **1.0 A** load-switch limit | `ADR 0005:260–262` **vs** `power-entry.md` "the limit is **0.940 A**, not 1.0 A" | 184–185, 205 | Already two-valued in the corpus; the plan copied the stale one, twice. |
| **5.7–7.2 cents** module ground term | `ADR 0004:332`, `:617`; `power-entry.md` | 222–223 | Copied, not cited; and mis-ranked. |
| **60 dB** in-amp CMRR budget | `breath-receive-stage.md` ("Symmetry") | 199–200 | Copied, misapplied to the wrong board. |
| **11 columns**, `hardware/bom.csv` | `CLAUDE.md` | 280 | **The plan proposes changing it to 12 in the same document that restates 11.** `CLAUDE.md` is *not* in `CORPUS_DIRS`/`CORPUS_FILES` (`check-staleness.py:30–31`), so neither copy is checkable. This is the project's named failure mode, freshly manufactured. |
| **four** cluster boards | `bom.csv:114` qty 4 | 333–334 | Benign, but a count, copied. |

**Recommendation in the plan's own idiom:** before this document is acted on,
add `loadswitch-current-limit`, `module-ground-cents` and `inamp-cmrr-budget` to
`config/figures.yaml`, with `1.0 A` in the first one's `forbidden` list. The
checker then finds `pcb-pipeline.md:184` and `:205` on the next commit.

### 2.3 Numbers the plan invents with no corpus source at all

| Plan value | Line | Source |
|---|---|---|
| `Default`/`Analog` track width **0.25 mm** | 179, 181 | none |
| decoupling **within ~2 mm** of the pin | 250 | none — corpus says only "close to the pin" (`bom.csv:43`) |
| "0.5 mm ≈ 1 A at 10 °C" | 183–184 | wrong by 45 % (§1 #4) |
| **five** iterations before stopping | 254 | none (fine as a policy, flagged for completeness) |

---

## 3. Critical nets missing from the hand-route list (§4, lines 195–205)

The plan locks five things. The corpus argues at length for these, and none is
on the list.

**3.1 `SENSE` / `R-ILIM` Kelvin pair** — `power-entry.md`: sense threshold
**47 mV** across a **50 mΩ** shunt. `[calc]` 1 mΩ of trace inside the sense loop
is a **2 %** shift in the current limit; 5 mΩ is 10 %. The plan lists "the 1 A
load-switch path" — the *power* path — and not the two-wire Kelvin connection to
pins 7/8 that decides what that limit actually is. This is the single clearest
omission.

**3.2 `FB` (LT1641 pin 2) and the `R-FB-HI`/`R-FB-LO` divider** —
`power-entry.md` §"5. `FB` was not connected, and that is what stops it
starting". High-impedance, doubles as the `PWRGD` comparator input at 1.233 V,
and the corpus calls it the mechanism behind "the instrument never starts".

**3.3 `GATE` / `C-GATE-LOADSW`** — `power-entry.md`: `I_GATE` **10 µA typical,
no min/max established**; `C-GATE = 10 µA / 120 V/s = 83 nF`. A 10 µA node sitting
above the +12 V rail: any leakage path across it changes the programmed ramp,
which is the only thing keeping the FET inside its SOA.

**3.4 `ON` pin and the panel-toggle run** — `power-entry.md` §"Still not
designed: the `ON` pin": falling threshold **1.233 V**, **80 mV** hysteresis,
**−1 µA** input current, "no divider, no logic level, no supply, no pull-down,
no debounce". An 80 mV-hysteresis, 1 µA node on a flying lead to a panel toggle,
routed past the DAC and the LED, with four passives that do not yet exist.

**3.5 `CS`** — `digital-and-supervision.md`: "**Why `CS` is the one that must not
glitch.** It frames the word… ADR 0004 deleted `MISO`, so firmware can never
read back what the DAC actually received… the only failure in the digital path
that does not self-heal." The cable-side fix was a pin-map change (`CS` paired
with `DIG_GND`, margin 1.9:1 → 6200:1). **The board-side equivalent — `CS` not
run parallel to `SCLK`/`MOSI`, `DIG_GND` continuous beneath it — is not in the
plan**, and `CS` falls into the plan's `Default` class where Freerouting places
it wherever it likes.

**3.6 `CLR` and `LDAC`** — `digital-and-supervision.md`: both are 10 kΩ pull-ups
to `AVDD` on active-low pins, with an `LK-CLR` solder pad to GND beside `CLR`.
The same page records that drawing `CLR` the wrong way "was the single cheapest
way in the whole design to end up with a module that does nothing at all" — six
dead CV outputs, uncorrectable by SPI. A 10 kΩ high-Z net that kills the board
belongs on a locked list.

**3.7 `VREFOUT` → buffered `V_ref` (2.500 V) and `TRIM-OFFSET`** —
`pitch-stage.md`: **1 mV of offset error = 1.2 cents at every note**. 1 mV of
coupling onto this node is worth more than most of the static error table. Not
mentioned.

**3.8 DAC ch7 → buffered `V_ref` 3.3333 V, fanning to four channels** —
`mod-channels.md`: one node, four loads, and `CLR` safety depends on it going to
zero. Not mentioned.

**3.9 The LT5400 1:1 pair (`R1`/`R2`)** — `pitch-stage.md`: ratio tracking
0.027 cents is the entire reason for an $8 part, kept explicitly so a future
external reference has something to sit on. The plan has no rule about matched
networks, thermal symmetry or copper balance around them; an autorouter will
treat the four sections as four ordinary resistors.

**3.10 etherCON shell / shield bond** — `power-entry.md`'s ground table:
"**The cable shield, if the etherCON shell bonds to the 10HP panel — ~7 cents**",
and "the shield policy is sixteen words in the whole repo". This is a
board-and-panel copper decision of the same magnitude as the star rule, and the
plan does not mention shields at all.

**3.11 The six jack sleeve returns** — ADR 0004 assigns every return to a
region; `pitch-stage.md`, `mod-channels.md` and `breath-output-stage.md` return
`C-FILT-PITCH` 10 nF, `C-FILT-MOD` 82 nF ×4 and `C-OUT-BREATH` 330 nF to a net
the drawings call `AGND`. The plan's scheme gives `AGND` **no zone and a
keepout**, which leaves eleven jack-side capacitor returns with nowhere to go.

**3.12 The module analog return region** — §1 #9. ADR 0004 names it as one of
four returns and says it is "its own region, joining at the star and nowhere
else. The DAC's `AVDD` return and the in-amp's `REF` tie belong in it." It has
no zone, no priority and no keepout in the plan.

---

## 4. Other things the plan asserts that the corpus does not support

### 4.1 `AGND` and `BREATH` each name two different nets — and the plan's
verification assumes they name one

This is fatal to "circuit as code" and to three of the seven `verify.py`
assertions, and the plan does not see it.

- **`AGND`** is (a) umbilical conductor pin 2, a **sense-only in-amp input**
  (ADR 0004:99, :611, :630), and (b) the symbol the module drawings use for the
  **local analog return**: `breath-receive-stage.md` returns `C_cm ×2`, `R4`,
  `R5` to "`AGND(module)`"; `pitch-stage.md` returns `C-AA-PITCH` and
  `C-FILT-PITCH` to "`AGND`"; `mod-channels.md` returns `C-FILT-MOD` to
  "`AGND`"; `breath-output-stage.md` returns `R-GAIN-FLOOR`, the summer's (+)
  and `C-OUT-BREATH` to "`AGND`" `[repo]`.
- **`BREATH`** is (a) umbilical conductor pin 1, the in-amp **input**
  (ADR 0004:99), and (b) the **output jack** net
  (`breath-receive-stage.md` and `breath-output-stage.md` both end at
  "BREATH jack") `[repo]`.

A SKiDL transcription that takes net names from the pages produces a netlist in
which **the breath in-amp input is shorted to the breath output jack** and in
which the analog return is tied to the sense conductor at eleven places. The
plan's assertions "no two nets merged; `AGND`, `PWR_GND`, `DIG_GND` still
distinct" and "`AGND` tied exactly once" would both **pass** on that netlist,
because the merge happened upstream, in the transcription.

**Precursor the plan is missing: a net-naming reconciliation across the six
pages before any transcription.** This is the highest-value item in this audit.

### 4.2 `pcb/` and `fab/` at the repo root contradict `README.md`

The plan is right that `check-staleness.py` would ignore them
(`check-staleness.py:30–31`). But `README.md:98` — which *is* in
`CORPUS_FILES` — says `hardware/` holds "BOM, schematics, **PCB**, split by
board", and `mechanical/` holds "**2D cut exports**". `hardware/module/.gitkeep`
and `hardware/controller/.gitkeep` are placeholders for exactly that `[repo]`.
Adopting `pcb/` + `fab/` is a change to the repository layout and must update
`README.md` in the same commit, which the plan does not say. As written,
"Nothing generated under `hardware/`" is a statement the corpus refutes rather
than a statement of the convention.

Related: the plan's E12 deliverable is "module PCB **and its panel**", but the
panel is a **DXF** cut by the same vendor and order as the key plate
(`bom.csv:21`), belongs in `mechanical/export/` per `README.md:100`, and the
pipeline produces nothing for it. `kicad-cli pcb export step` is offered "for
mechanical fit against the panel" — against a panel no stage generates.

### 4.3 Pour-after-autoroute cannot verify the star rule

The plan routes (§5), then pours (§6), then asserts "no two nets merged" (§7).
On a **2-layer** board (`bom.csv:71`) with the whole signal set autorouted
across both layers, a `PWR_GND` zone fragmented by autorouted tracks is still
**one net** — it passes every assertion in §7 — while its return current takes
whatever path is left. ADR 0004's mechanism is *IR drop along shared copper*,
not connectivity: "If `PWR_GND` shares copper with the analog return for even a
centimetre, 360 mA develops an IR drop across that shared length"
`[repo, ADR 0004:613]`. **Nothing in §7 measures that.** At
**0.43 cents per mΩ at 360 mA** `[calc]`, the assertion set cannot distinguish a
good board from a 20-cent one. The corpus's own quantities suggest the missing
check is a copper-path resistance extraction, or at minimum zone-fill-before-route.

### 4.4 The precursor list is right in kind and incomplete in fact

Against the corpus as it stands today:

- **Precursor 1** ("Every BOM row `selected`"): of **61 module rows, 2 are
  `selected`** — 45 `candidate`, 13 `open`, 1 `not-needed` `[calc from
  hardware/bom.csv]`. Repo-wide: 6 of 132.
- **Precursor 1** also needs a flag the plan omits: `bom.csv` already records a
  **known-wrong footprint** — `C-TIMER-LOADSW` is specified 0805 C0G while
  `power-entry.md` computes 9.4 µF, "wrong for 9.4 uF by three orders of
  magnitude", and it is **blocked on `164112fc.pdf`** (`MANIFEST.csv`, status
  BLOCKED). The plan's own sentence — "a placement built around a wrong
  footprint is the one expensive thing to redo" — has a live instance in the
  corpus and does not name it.
- **Precursor 2** ("no *topological* item left in Still open"): the module page
  set has at least seven, none named `[repo]`:
  `power-entry.md` — the `ON` pin (four missing passives), no fuse on the analog
  rails, damping the input LC; `pitch-stage.md` — "`TRIM-OFFSET` is not
  buildable as described"; `mod-channels.md` — the single-inverting-amp redraw,
  "strictly better… the call belongs to the author"; `digital-and-supervision.md`
  — whether to restore link supervision (four parts), and **dropping bus +5 V,
  which is "a rail change and a connector change"** (16-pin → 10-pin header —
  i.e. a different board footprint); `breath-output-stage.md` — the response
  shaper (`POT-RESP`/`R-RESP`/`D-RESP`/`U-RESP`, all `open`, "PROPOSED
  2026-09-21", and it adds a third pot to the panel).
- **Precursor 3** cites `pitch-cents-budget` at line 155 but **not
  `panel-height-budget`**, which is `disputed` in the register, is owned by
  ADR 0004, and is the figure that decides the module **panel layout and board
  outline** — precursor 4's subject. Its `decided_by` says the arithmetic is now
  doable on paper and that the panel toggle is still BLOCKED in `MANIFEST.csv`.
- **Precursor 4** ("connector orientation") omits the one mechanical
  requirement the corpus states for this board: "**Must brace the etherCON
  mechanically**" (`bom.csv:71`), echoed by `ROADMAP.md` E12 "etherCON braced to
  the PCB".
- **A missing precursor:** `power-entry.md` — "**Confirm the foldback law and
  the `FB` divider against `164112fc.pdf` before the parts order.** If it holds,
  this is a board that would not have powered up." Three of the plan's five
  locked nets are LT1641 nets; all of them rest on `[web, search-index]`
  provenance.

### 4.5 Minor

- Line 181: `Analog` class is "0.25 mm, **routed by hand**", but §4's hand-route
  list names only *pitch feedback* — not `BREATH`, not the four mod outputs.
  Internal to the plan, but it is the corpus's precision set.
- `Default` and `Analog` are both 0.25 mm, so the `Analog` class carries no
  electrical rule at all.
- `hardware/datasheets/` exists as an empty `.gitkeep` placeholder while the
  bank the plan points at is top-level `datasheets/`. Pre-existing, but the plan
  cites the latter while asserting a convention about the former's parent.
- The SPICE table (§2) mixes module circuits with **carrier** circuits
  (`R-ISO-REF`, the OPA2197 `Zo` work are `hardware/controller/carrier.md` —
  E13). Harmless for a board-independent stage, worth labelling.

---

## 5. What survives

For the record, since "falsify" was the instruction and a review that finds only
faults is not calibrated: verdict-table rows **1, 3, 17, 19, 22, 23, 26, 27, 28,
29, 30** are confirmed against the corpus, and the architectural argument in
§"circuit as code, not a parsed drawing" is consistent with `CLAUDE.md`'s
diagnosis (the corpus defect is derived documents not following their source;
generating the netlist rather than re-deriving it is the right shape of fix).
The SPICE stage is the best-sourced section in the document — every project
claim in it checks out — and it correctly *cites* `pitch-cents-budget` rather
than restating it, which is the discipline the rest of the document needs.

---

## Provenance summary

All findings are `[repo]` with file or file:line, or `[calc]` with the
arithmetic shown inline. Two claims are marked UNSUPPORTED rather than REFUTED
because their basis may exist outside the design corpus (verdict rows 32 and 31)
— this reviewer was cold to `docs/review/**` by instruction and did not check
there. Nothing in this report is `[from memory]` or `[web]`.
