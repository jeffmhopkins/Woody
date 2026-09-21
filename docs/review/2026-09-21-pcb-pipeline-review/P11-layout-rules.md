# P11 — The layout rules: what is right, and what is missing

**Slice:** the layout rules in `docs/reference/pcb-pipeline.md` (proposed, nothing
built). **Method:** cold — no prior review directory read. **Date:** 2026-09-21.

Provenance on every claim: `[repo file:line]`, `[calc]` with the arithmetic shown,
`[github, verified]` with the path in a cloned upstream tree, `[from memory]`.

## Model validation, before anything else

Two of the findings below turn on capacitive common-mode-to-differential
conversion, so the model is first checked against the corpus's own published
numbers. For a mismatch `ΔC` between the two common-mode capacitors against
`R = 11 kΩ` per leg, the CM→DM ratio is `2π·f·R·ΔC`:

| `ΔC` | At 500 Hz | `breath-receive-stage.md` says |
|---|---|---|
| 150 pF (±5 % C0G, worst case 10 % of 1.5 nF) | **−45.7 dB** `[calc]` | "~46 dB" `[repo breath-receive-stage.md:227]` |
| 30 pF (±1 % C0G) | **−59.7 dB** `[calc]` | "±1 % is needed to clear 60" `[repo breath-receive-stage.md:228]` |

The model reproduces both, so it is used below. Note in passing what it also
says: **±1 % C0G lands at 59.7 dB, which misses the 60 dB budget by 0.3 dB on
its own, before any other term** `[calc]`. There is no margin left for layout to
spend. That is the premise for finding M3.

Copper constants used throughout: 1 oz = 34.8 µm, `ρ_Cu` 1.72e-8 Ω·m →
**0.494 mΩ/square** `[calc]`. Microstrip, 0.25 mm trace over 1.6 mm FR4
(`εr` 4.3): `Z0` = 140.8 Ω, `εeff` = 2.837, **C = 0.0399 pF/mm** `[calc]`.

---

# 1. Verdict on each rule the plan states

| Rule | Verdict |
|---|---|
| Decoupling within ~2 mm | **Right number, wrong quantity.** It constrains distance where the physics is loop area, and it is silent on which of four returns each cap lands in |
| `Default` 0.25 mm signal | **Correct and conservative.** A shipping comparable uses 0.15 mm |
| `Power` derived from IPC-2221 | **The instruction is right; the sentence justifying it is arithmetically false** |
| `Analog` 0.25 mm hand-routed | **Correct width. The net list is the wrong half of the board** — see W1 |
| Hand-route `AGND` star | Right, but `AGND` is one of two different nets sharing that name — see W2 |
| `BREATH`/`AGND` "matched and parallel" | **Right instruction, wrong reason, and the plan's own keepout rule breaks it** — see M3 / W4 |
| `PWR_GND` / `DIG_GND` separate, one tie | Right, and incomplete: there are **four** returns, not three — see W2 |
| Pitch feedback loop area | Right, and the least of the pitch worries |
| 1 A load-switch path + FET thermal pad | Path right. "Thermal pad" is not a thermal problem on this board — see W5 |
| Thermal reliefs on THT pads | **Correct, and verified free**: 4 spokes at 0.508 mm cost 0.12 mΩ `[calc]`. But it silently decides the SMD case too — see M6 |
| No copper under connector bore / panel cutouts | **Aimed at a hazard this board does not have, and misses the one it does** — see W6 |

## 1.1 "Decoupling within ~2 mm of the pin it serves"

**2 mm is a fine number and it is not what decides the result.** Build the loop
a 2 mm rule permits: 2 mm out, 2 mm of return, two vias, one 0805. At ~1 nH/mm
of narrow trace over a 1.6 mm-distant reference, ~1.2 nH per via and ~1 nH of
0805 ESL `[from memory]`, that is ≈7.4 nH, which resonates with 100 nF at
**5.85 MHz** `[calc]`. Above that the decoupler is an inductor.

5.85 MHz is adequate for six OPA2197s and for the DAC's `AVDD`. It is not
obviously adequate for the 74AHCT125, whose output edges have a knee near
100–250 MHz (`t_r` 2–5 ns `[from memory]`, `f_knee` = 0.5/`t_r` `[calc]`).

The defect is that **the same 2 mm passes a cap whose ground via is 6 mm away
in the wrong direction, and fails a cap 2.5 mm away with its via touching its
own pad.** The rule measures the one term that does not dominate.

**And it is silent on the thing that matters more here.** `C-DECOUPLE` is
nineteen parts and the BOM enumerates them: "6 × OPA2197 on ±12V = 12, INA828 =
2, DAC8568 AVDD+DVDD = 2, 74AHCT125, LT1641 VCC, LM317 in"
`[repo hardware/bom.csv:43]`. Those nineteen return to at least **three
different grounds** — the module analog return, `PWR_GND` (the LT1641's `VCC`
decoupler sits on the 1 A node), and whatever the 74AHCT125's ground pin is tied
to. A board that returned the LT1641's decoupler into the analog region would
pass "within 2 mm" and would put load-switch switching current directly under
the pitch reference, which is the mechanism ADR 0004 costs at **5.7–7.2 cents**
`[repo docs/decisions/0004-cv-interface-module.md:617-619]`.

## 1.2 "`Default` 0.25 mm" — correct, and more conservative than a shipping board

Winterbloom Sol's rev1 mainboard is the closest published comparable: a
**2-layer** precision-DAC Eurorack CV board on ±12 V `[github, verified:
wntrblm/Sol `hardware/rev1/mainboard/mainboard.kicad_pcb:23-25` — the layer
stack is `F.Cu` and `B.Cu` only]`. It carries **one** net class, "Default", at
`trace_width 0.15`, `clearance 0.15`, `via_dia 0.8 / via_drill 0.4`
`[github, verified: same file:200-206]` — and it puts `+12V`, `-12V`, `+5V`,
`2V5REF` and all four CV outputs *in that class* `[same file:207-214]`.

So 0.25 mm for signal is right with margin, and Woody's three-class plan is
already better structured than a board that shipped. `pitch-stage.md` cites Sol
by name as prior art `[repo hardware/module/pitch-stage.md:78]`, so this is a
fair comparison rather than an arbitrary one.

## 1.3 "Derive the power width" — right instruction, false premise

The plan says: *"0.5 mm of 1 oz copper is roughly a 1 A trace at a 10 °C rise,
and the load switch's path is specified at 1.0 A. That is no margin."*
`[repo docs/reference/pcb-pipeline.md:143-145]`

Run IPC-2221's external-conductor law, `I = 0.048·ΔT^0.44·A^0.725` (A in mil²):

```
1.0 A at ΔT = 10 °C  →  A = 16.30 mil²  →  w = 16.30/1.37 = 0.302 mm
0.5 mm (19.69 mil)   →  A = 26.97 mil²  →  I = 1.441 A at ΔT = 10 °C
0.5 mm at 1.0 A      →  ΔT = 4.36 °C
```
`[calc]`

**0.5 mm is a 1.44 A trace, not a 1.0 A trace, and at 1.0 A it rises 4.4 °C.**
That is 44 % of current margin, not "no margin". The instruction — compute it,
put the arithmetic in the script — is exactly right and should stay. The
sentence arguing for it is wrong by 44 %, and this project's named failure mode
is a number that stops matching its derivation.

Two further problems with the `Power` class as listed
`[repo docs/reference/pcb-pipeline.md:139-141]`:

- It lumps `+12V`, `-12V`, `+5V`, `AVDD` and `PWR_GND` into one width. But
  `AVDD` carries ~13 mA `[repo hardware/bom.csv:38]`, `-12V` ~10 mA
  `[repo hardware/bom.csv:77]`, and only the umbilical `+12V`/`PWR_GND` branch
  carries 0.94 A. Sizing all five for 1 A is harmless but it hides which net
  the derivation is actually about.
- **`DIG_GND` is in no class at all** and falls to `Default` 0.25 mm — on a
  board whose own power page says "a 2 MHz SPI return wants the pour directly
  under its trace" `[repo hardware/module/power-entry.md:347-348]`.

## 1.4 Thermal reliefs on through-hole pads — correct, and checked

The plan's reasoning (hand-soldered, a solid THT connection to a pour sinks the
iron) is right. The obvious objection is that the 16-pin IDC's power and ground
pins carry the 392 mA module total and the 0.94 A umbilical return, so a relief
might constrict them. It does not: four spokes at Sol's geometry (0.508 mm
bridge, 0.508 mm gap `[github, verified: mainboard.kicad_pcb:3951-3952]`) is one
square each, four in parallel = 0.25 sq = **0.12 mΩ** `[calc]`. At 1 A that is
0.12 mV and 0.12 mW. **No conflict. The rule stands unmodified.**

---

# 2. The missing rules, ranked by what omitting them costs this board

## M1 — Hand-route and lock `VREFOUT`, `V_ref`, the trimmer wipers and `AVDD`. Do not autoroute them.

**This is the largest single gap and it is a gap of selection, not of technique.**

The plan hand-routes and locks: `AGND`, the `BREATH`/`AGND` pair,
`PWR_GND`/`DIG_GND`, the pitch feedback loop, the 1 A path
`[repo docs/reference/pcb-pipeline.md:156-164]`. Everything else goes to
Freerouting. Sort the board's analog nets by how much a millivolt on them costs:

| Node | 1 mV costs | Source |
|---|---|---|
| **`V_ref`** (pitch intercept, 2.500 V) | **1.2 cents** | `[repo hardware/module/pitch-stage.md:116]` |
| **`VREFOUT`** (DAC internal ref, exported) | a gain term; 1 mV on 2.5 V is 400 ppm ≈ **1–3.4 cents** | `[calc from repo pitch-stage.md:117]` |
| `INA828 REF` | 1 mV at the breath jack = 0.01 % of span | `[repo breath-receive-stage.md:57]` |
| `AVDD` | ~0.0000037 cents, via LM317 line reg and OPA2197 PSRR | `[calc: 0.00044 cents per 120 mV, repo config/figures.yaml `diode-split-rationale`]` |
| **Pitch / mod / breath jack outputs** | nothing — each has 1 kΩ of series isolation and a shunt cap at the jack | `[repo pitch-stage.md:133-136]` |

`V_ref` and `VREFOUT` are **not in any hand-routed class**. The pitch outputs —
the most robust nets on the board — **are**.

The consequence, stated in the corpus's own units: `config/figures.yaml` records
the total pitch error budget as **disputed among 0.42, 0.85, 1.35 and ~1.2
cents** `[repo config/figures.yaml:172-179]`. **One millivolt of routing-induced
error on `V_ref` is 1.2 cents — it equals or exceeds every candidate for the
whole budget** `[calc]`, and that net is currently handed to an autorouter with
a 1800-second timeout and 100 passes.

`V_ref` is worse than a bare net, too: it is the output of a follower whose
input is `TRIM-OFFSET`, a 10 kΩ cermet `[repo hardware/bom.csv:111]` with a
~2.5 kΩ source impedance at mid-wiper, and the trimmer must be placed where a
screwdriver reaches (M7) rather than where the op-amp is. That is the longest
sensitive trace on the board, and it is unnamed in the plan.

**Rule to add:** a fourth net class, `Reference`, hand-routed and locked,
containing `VREFOUT`, the `TRIM-OFFSET` wiper and its range network, `V_ref`,
the mod channels' shared 3.3333 V `[repo hardware/module/mod-channels.md:101]`,
the `TRIM-BREATH-ZERO` wiper and the `INA828 REF` net. Routed short, on one
layer, over unbroken analog-return copper, never parallel to `SCLK`/`MOSI`/`CS`.

## M2 — Name the fourth ground, and stop `AGND` meaning two different nets

**The plan's stage 5 is headed "three grounds, two zones, one star" and
enumerates `PWR_GND`, `DIG_GND` and `AGND`** `[repo docs/reference/pcb-pipeline.md:178-190]`.
ADR 0004's table has **four** returns
`[repo docs/decisions/0004-cv-interface-module.md:606-612]`:

| Return | Carries | In the plan? |
|---|---|---|
| `PWR_GND` | ~360 mA | zone |
| `DIG_GND` | SPI switching current | zone |
| **Module analog return** | op-amps, DAC `AVDD`, the pitch reference | **absent** |
| `AGND` (from the etherCON) | **nothing — it is an in-amp input** | keepout + "star" |

The plan has substituted a net that is *not a ground* for the one that *is*, and
the one it dropped is the one carrying ADR 0004's largest live pitch term
(5.7–7.2 cents `[repo 0004:617-619]`).

**The name collision is worse than the omission**, because it is invisible:

- `breath-receive-stage.md` writes the cable conductor as `AGND (pin 2)`
  `[repo:28]` and the module's analog ground as `AGND(module)` `[repo:39, 43, 47]`
  — two nets, distinguished only by a parenthesis.
- `pitch-stage.md` and `mod-channels.md` write the module analog ground as bare
  **`AGND`**: "10 nF from the `R-OPAMP-IN` node to `AGND`" `[repo pitch-stage.md:202]`,
  `[C-FILT-MOD 82nF]── AGND` `[repo mod-channels.md:43]`.
- ADR 0004 writes the *cable conductor* as bare **`AGND`**: "`AGND`, from the
  etherCON | Nothing." `[repo 0004:611]`.

So bare `AGND` means the module analog return in two schematic pages and the
in-amp input in the ADR and in the power page. A SKiDL transcription that takes
the name at face value **merges them**, which makes the cable's sense return a
ground — "anything that makes it a return path breaks the reason a 2 m analog
run works at all" `[repo 0004:630-632]`.

**And the plan's own guard cannot catch it.** `verify.py` asserts "no two nets
merged; `AGND`, `PWR_GND`, `DIG_GND` still distinct"
`[repo docs/reference/pcb-pipeline.md:206]` — three names, and the merge that
matters is *inside* the one called `AGND`.

**Rules to add:** (a) rename at transcription — `AGND_SENSE` for the etherCON
conductor, `AGND` (or `AGND_MOD`) for the module analog return, and never the
bare word again; (b) the module analog return gets **its own zone**, third,
joining `PWR_GND` at the star and nowhere else; (c) the netlist-equality
assertion enumerates four returns.

## M3 — The `AGND` keepout must cover **both** legs of the breath pair, or it breaks the pair

Two of the plan's rules contradict each other and the contradiction is
quantifiable.

Rule A: "`BREATH` / `AGND` pair, connector to in-amp — matched and parallel"
`[repo pipeline:158-159]`. Rule B: "`AGND` gets no zone at all — a routed star,
plus a keepout so neither ground zone floods across it" `[repo pipeline:186-187]`.

Apply B literally and the `AGND` leg runs over a copper void while the `BREATH`
leg runs over a `PWR_GND` or `DIG_GND` pour. At 0.0399 pF/mm `[calc]`, a 40 mm
run from the etherCON to `R2`/`R3` puts ~1.6 pF under `BREATH` and ~0.2 pF under
`AGND` — **ΔC ≈ 1.4 pF, asymmetric, in exactly the place the two 1.5 nF
common-mode capacitors are matched to ±1 % to control.**

What that costs, in the validated model: 1.4 pF is −86.3 dB `[calc]`. On its own
that is far below the 60 dB budget. **But the budget is already spent**: the
±1 % `C_cm` term alone is 1.036e-3, i.e. −59.7 dB, against a 60 dB target
`[calc, reproducing repo breath-receive-stage.md:228]`. Adding 4.84e-5 takes the
total to 1.071e-3 → **−59.4 dB**. It is 0.3 dB, and every 0.3 dB now comes out
of a budget that starts at zero.

**Rule to add:** the keepout is a *single window enclosing both legs*, from the
etherCON pins to `R2`/`R3`, with identical copper (i.e. none) under each. Then
"matched and parallel" means what it should.

## M4 — Say where the SPI return current goes; the corpus has it going the long way round

This is the one that could make the board measurably worse and it appears in no
document.

`digital-and-supervision.md` puts the 74AHCT125 between the etherCON and the
DAC `[repo:29-51]`. The buffer runs from **bus +5 V**; the DAC runs from the
**LM317's 5.21 V** `[repo hardware/bom.csv:35]`. ADR 0004 assigns the DAC's
return to the **analog** region: "The DAC's `AVDD` return and the in-amp's `REF`
tie belong in it" `[repo 0004:628-629]`. `DIG_GND` — the SPI return from the
cable — runs "its own path to the star" `[repo 0004:627]`.

So the buffer's outputs drive the DAC's `SCLK`/`DIN`/`SYNC`, and the return
current for those edges has to get from the DAC's ground pin back to the
buffer's ground pin. **If the DAC sits in the analog region and the buffer sits
in `DIG_GND`, the only continuous copper between them is the star at the power
inlet** — the far corner of a ~45 × 110 mm board `[repo hardware/bom.csv:71]`.

Order of magnitude: a 30 mm run into ~10 pF of DAC input plus trace gives
`i = C·dV/dt` = 10 pF × 5 V / 3 ns = **16.7 mA** `[calc]`. A return loop of
~150 mm perimeter is ~100 nH `[from memory, ~1 nH/mm]`, so
`V = L·di/dt` ≈ **0.5 V of ground bounce between the DAC's ground and the
buffer's** `[calc, order of magnitude]`. That lands on the ground pin of the
part that sets six CV outputs.

It is also the mechanism the corpus is already frightened of by a different
route: a stray edge on `CS` re-frames a 32-bit word, and a mis-framed word is
**sticky** because `MISO` was deleted and firmware can never read back
`[repo digital-and-supervision.md:97-104]`.

**Rules to add:** (a) the 74AHCT125 is placed adjacent to the DAC, buffer
outputs to DAC inputs under 25 mm; (b) the `DIG_GND` ↔ analog-return relationship
at that pair is an explicit, single, *recorded* decision, not an emergent
property of two pours meeting; (c) the assertion is not "the nets are distinct"
but "for every `SCLK`/`MOSI`/`CS` segment, continuous reference copper of one
named net exists directly beneath it for its whole length".

**And one thing the corpus genuinely does not say:** which net the 74AHCT125's
own ground pin ties to. Its *input* thresholds are referenced to `DIG_GND`
arriving from the cable; its *output* return loop wants to be with the DAC. It
must be one or the other, both have a cost, and no document chooses.

## M5 — There is no bypass capacitor on `VREFOUT`, and the plan's check cannot notice

`hardware/bom.csv` has nineteen `C-` rows. Grepping all of them: `C-REF-OUT`
10 µF exists for the instrument's REF5050 "per the REF50xx datasheet's
recommended output capacitance" `[repo hardware/bom.csv:76]`. **There is no
capacitor on the DAC8568's `VREFOUT` pin anywhere in the BOM** `[repo, checked
across all 19 `C-` rows in hardware/bom.csv]`.

That pin is not idle. It is exported: `VREFOUT ──[TRIM-OFFSET 10k]──┬── ½ OPA2197
── V_ref` `[repo hardware/module/pitch-stage.md:14]`, so it drives a 10 kΩ
trimmer — ~250 µA of DC load `[calc]` — and it is the node the entire pitch
tracking argument rests on: "the whole transfer function scales... a reference
drift becomes a pure *gain* error and never an offset error"
`[repo pitch-stage.md:105-107]`.

**The plan's verify step is "every decoupling cap within ~2 mm of the pin it
serves"** `[repo pipeline:210]`. That check validates the caps that exist. It
passes, silently and forever, on a board with no reference bypass at all.

**Rules to add:** (a) the check is inverted — enumerate *supply and reference
pins* from the netlist and assert each has a cap, rather than enumerating caps
and measuring distance; (b) `C-DECOUPLE`'s count of 19 and its named pin mapping
`[repo hardware/bom.csv:43]` is asserted against the netlist, so a deleted part
moves the count (it has already moved twice: 22 → 21 → 19, both times because a
part was deleted and the count did not follow `[repo bom.csv:43]`).

## M6 — Ground stitching, zone islands, and the 2-layer return path

The plan pours two zones and then stops. On two layers with an autorouter, every
track Freerouting lays on `B.Cu` is a slot in the return plane, and
`ZONE_FILLER` will happily produce disconnected islands that are DRC-clean and
electrically dead.

Sol's practice, on a directly comparable 2-layer board: **122 vias, of which 95
are on `GND`** `[github, verified: wntrblm/Sol mainboard.kicad_pcb, counted]` —
78 % of all vias are stitching. Sol also pours `GND` on **both** `F.Cu` and
`B.Cu` `[github, verified: same file:3949, 5484]`, and pours `+5V` and `+12V` as
zones too `[same file:3827, 3877, 3900]`, which the plan does not consider.

Stitch pitch: `f_knee` = 0.5/`t_r` = 100–250 MHz for the 74AHCT125's edges
`[calc, t_r 2–5 ns from memory]`; `v` in FR4 ≈ 1.78e8 m/s `[calc]`; λ/20 =
36–89 mm `[calc]`. **≤25 mm gives margin at the worst reading.**

**Rules to add:**
- Each zone must fill as **one connected polygon**; assert zero orphan islands
  after every `Fill()` (and after every subsequent edit, since the plan already
  correctly says re-fill after any change `[repo pipeline:194-195]`).
- Stitching vias on each ground zone at ≤25 mm pitch, and specifically a row
  flanking the `SCLK`/`MOSI`/`CS` run.
- **Return-path continuity assertion** (this is the one worth writing): for each
  net in `Analog`, `Reference` and the SPI set, walk its track centrelines and
  assert unbroken reference copper of a single named zone directly beneath, on
  the opposite layer, for the whole run. Rasterising the filled zone polygons and
  sampling the centreline is a ~50-line script and it catches the defect that
  actually kills 2-layer analog boards.
- **Zone pad-connection is set explicitly, not defaulted.** Sol uses
  `connect_pads thru_hole_only` on its `GND` and `+12V` zones `[github, verified:
  mainboard.kicad_pcb:3902, 3950, 5485]` — reliefs for PTH only, SMD pads solid.
  KiCad's default is thermal relief for *all* pads, which would put spokes on
  every SOIC ground pad and every decoupler's ground pad, adding ~0.3 nH
  `[calc, from the 0.508 mm spoke geometry]` to the very loop rule 1.1 exists to
  protect. Small, and free to get right, and invisible if left to a default.

## M7 — Bring-up access: five parts are selected on the bench, and one test needs a wire to clamp

The plan treats the board as a thing that gets fabricated. It also gets
*commissioned*, and the corpus specifies that commissioning in detail.

**Two parts have values that are chosen by measurement after the board exists:**

| Part | Package now | When |
|---|---|---|
| `R-REG-SET` | 0805 **or through-hole** | "SELECTED ON THE BENCH at E7" `[repo bom.csv:39]` |
| `R-ILIM` | 0805 or 1206 | `status=open`, "value from E6... selected on the bench like `R-REG-SET`" `[repo bom.csv:64]` |

> **This table said five until the corpus moved under this review.**
> `C-TIMER-LOADSW`, `C-GATE-LOADSW`, `R-FB-HI` and `R-FB-LO` were `TBD` and
> `blocked` when this slice began and are now `selected` with real values —
> 10 µF low-leakage, 82 nF C0G, 35.7 k and 5.11 k `[repo bom.csv:119-122]` —
> against a **now-verified** `164112fc` `[repo power-entry.md:136-138]`. Recorded
> rather than silently corrected, because a reviewer citing the blocked state is
> exactly the staleness this repo exists to catch, and it caught me.

Each will be desoldered and replaced several times, on a hand-assembled board,
possibly with 100 µF electrolytics and an etherCON body nearby.

**Rule:** bench-selected parts get through-hole or oversized hand-solder pads,
on a board edge, with ≥5 mm of clear approach and nothing tall within 10 mm, and
they are never placed under the etherCON's envelope.

**The current probe is a physical requirement, not a note.** ROADMAP books
"**Inrush with a current probe, on switch-on *and* hot-plug**" at E6
`[repo ROADMAP.md:194]`, and the `R-ILIM` row says "E6 measures the TRIP as well
as the load, with a current probe" `[repo bom.csv:64]`. **A current probe cannot
clamp around a trace.** The layout must provide a removable wire link or a
2-pin header in the umbilical +12 V path, or the E6 measurement that sizes the
load switch cannot be made on the board that was built.

**Test points.** `hardware/bom.csv` has **no test-point row**, and the
commissioning procedures name specific nodes: `TRIM-BREATH-ZERO` is set "until
the in-amp output reads 0 V" `[repo ROADMAP.md:51]`, so the INA828 output needs
a probe pad; E7 "measures where the DAC's top codes start compressing against
AVDD" `[repo ROADMAP.md:47]`, so `AVDD` needs one; E6 needs `TIMER`, `GATE` and
`FB` on the load switch, three nets whose behaviour is currently *inferred from
search-index text* `[repo power-entry.md:189-199]`.

**Rule:** named test pads on `AVDD`, `VREFOUT`, `V_ref`, the INA828 output, the
in-amp `REF`, `TIMER`, `FB`, `GATE`, `PWR_GND` and the analog return — ring or
loop pads sized for a scope probe's ground spring, not bare vias.

## M8 — Trimmer and control accessibility is a volume problem, not a placement preference

Three trimmers, all `THROUGH-HOLE` multiturn cermet `[repo bom.csv:110, 111, 113]`,
all adjusted with a screwdriver after the module is assembled. Two of them
(`TRIM-GAIN`, `TRIM-OFFSET`) are iterated: "Repeat twice"
`[repo pitch-stage.md:258]`.

The board sits behind the panel with panel-mounted jacks and pots between them,
so **the panel-facing side of the board is a 7–14 mm slot with a 2 mm aluminium
lid.** Nothing is adjustable there. And the etherCON occupies a large fixed
volume: flange 26 × 31 mm, **34.55 mm behind the panel** `[repo bom.csv:19]`.

**Rules to add:** (a) all three trimmers on the rear-facing side, screws facing
rearward, with ≥15 mm of clear axial approach for a trim driver; (b) **a
component keepout on the board equal to the etherCON's projected envelope**,
because everything there is unreachable and un-reworkable for the life of the
board; (c) `TRIM-GAIN`'s footprint straps the wiper to one end — "a two-terminal
series trimmer fails open to the rail... that is a footprint decision, not a
value" `[repo pitch-stage.md:331-332]`, and it is currently recorded only in a
*Still open* list, which is where footprint decisions go to be forgotten.

## M9 — Derive the panel and the board from one file; two of the banked numbers already disagree

Six `J-CV`, three pots, a toggle, an LED and an etherCON all pass through the
panel and are all soldered to the board. The positional budget is tight: the
PJ398SM bushing is **D6.0 mm with a 6.2–6.5 mm practical hole**
`[repo bom.csv:16]`, so radial slop is **0.10–0.25 mm** `[calc]` — and all six
jacks must land at once.

**Rule:** panel feature centres live in **one** data file (this project already
has the pattern — ADR 0010, key layout as data, and `config/key-layout.yaml`),
and *both* the panel DXF and the board's panel-mount footprint placements are
generated from it. `verify.py` asserts each panel-mount footprint's origin equals
its panel feature centre within **±0.1 mm**. Two sources of truth drifting is
the project's named failure mode, and the plan already applies exactly this
argument to the BOM `[repo pipeline:244-246]` and then does not apply it to the
mechanics.

**The reason to do it now rather than later:** two banked dimensions already
disagree about where the board plane is.

```
PJ398SM:   panel face → 5.5 mm → body front, body 8.3 mm deep
           → board at 13.8 mm from the panel's front face   [repo bom.csv:16]
RV09-40:   7.0 mm board-to-shaft, + 2 mm panel
           → board at  9.0 mm from the panel's front face   [repo bom.csv:81,130]
                                              difference: 4.8 mm   [calc]
```

I am reading dimension *semantics* off BOM prose and could be misreading which
face each is measured from — so this is flagged as **a thing the pipeline must
resolve with a stack-up before placement**, not as a settled defect. But the
pipeline's Precursor 4 currently says only "Mechanical inputs settled: panel
cutouts, board outline, connector orientation, standoffs"
`[repo pipeline:289-290]`, which is a heading, not a constraint. A board-to-panel
standoff distance is a *derived number with two inputs that disagree*, and this
repo has a register for exactly that shape of problem.

## M10 — Mounting, the panel bond, and the ~7-cent path nobody has closed

`hardware/bom.csv` has **no mounting hardware row for the module PCB**. The only
`MECH-GNDBOND` row bonds the *instrument's* plate `[repo bom.csv:55]`. `PCB-MODULE`
says only "Must brace the etherCON mechanically" `[repo bom.csv:71]`, and ROADMAP
E12 repeats it `[repo ROADMAP.md:53]` — with no hole, no bracket and no fastener.

Worse, **the pots do not help.** The plain RV09-40 "HAS NO BUSHING AT ALL — it
is snap-in" `[repo bom.csv:81]`, so unless an E1/E1N bushing suffix is ordered
the three pots clamp nothing. The board is held by six jack nuts and an
unspecified etherCON brace.

**And the panel bond is already made, by accident.** The PJ398SM is
"PBT / brass-Ni / BeCu-Ag" `[repo bom.csv:16]` — the metal bushing is the sleeve
contact. Six jack bushings therefore bond the aluminium panel to whichever net
the jack sleeves sit on, and the etherCON shell bonds the cable shield to the
same panel. That is precisely the path `power-entry.md` costs at **~7 cents** and
then declines to fix: "The cable shield, if the etherCON shell bonds to the 10HP
panel | **~7 cents**... Not fixed here. It is a grounding and shield-bonding
decision, and the shield policy is sixteen words in the whole repo"
`[repo hardware/module/power-entry.md:97, 106-107]`.

**The layout cannot avoid making this decision.** The only levers are which net
the jack sleeves are on, and whether the etherCON is isolated from the panel —
and the second is a *part* choice (isolating shoulder washers, or a variant)
that has to precede the order, not the layout.

**Rules to add:** (a) ≥2 module mounting holes with the plated/unplated and
net/no-net choice stated, defaulting to **isolated**; (b) the panel/shield bond
is a single named point with a recorded decision, and `verify.py` asserts the
jack sleeve net by name so it cannot change silently.

## M11 — Six ⌀3 mm voids under the jack barrels

Thonk's own dimensioned sheet, banked in this repo, says: **"leave a 3 mm hole or
a void in the PCB under the barrel"** `[repo hardware/bom.csv:16, from
datasheets/connectors/PJ398SM-drawing.jpg]`. That is a board feature, ×6, and the
plan does not mention it. See W6 for why the plan's nearest rule does not cover it.

Also from the same row, for the netlist rather than the layout: **"PIN 2 =
TIP-NORMAL switch contact — NORMALLY CLOSED TO PIN 3 AND OPENING WHEN A PLUG IS
INSERTED... THE SWITCH CONTACT IS FREE NORMALLING and nothing in the design uses
it yet — worth knowing before the layout, not after"** `[repo bom.csv:16]`. Six
unused pads that SKiDL's `ERC()` will flag as unconnected. They need a deliberate
`NC` marking, or the build fails on six warnings and someone learns to ignore ERC.

## M12 — Copper-to-edge clearance, and the notch web

The plan sets "the basics (clearance, min track, via sizes)" in board design
settings `[repo pipeline:147-149]` and never names **copper-to-edge**. This board
has a non-rectangular outline — the etherCON notch, with a web the corpus has
already worried about at 4.5 mm `[repo bom.csv:71]` — a 2 mm aluminium panel
7–14 mm away, and a metal connector shell in the notch.

**Rule:** `copper_edge_clearance` ≥ 0.3 mm, set explicitly in the board settings
so `kicad-cli pcb drc` enforces it, plus a minimum-web assertion on `Edge.Cuts`.

## M13 — Via-in-pad and tenting

Hand assembly, a TSSOP-16 at 0.65 mm pitch `[repo bom.csv:12]`, THT electrolytics
and a DPAK.

**Rules:** no via inside any SMD pad (it wicks solder on a hand-soldered board and
starves the joint); all vias tented/covered by mask, so a dropped lead or a probe
tip cannot short one; **no thermal-via array under the FET's DPAK tab** — see W5
for why there is nothing to conduct away, and the array would wick the tab's
solder on a hand-soldered part.

## M14 — Silkscreen, stated as a rule rather than an intention

Hand assembly and hand probing, so: every refdes readable *after* the part is
fitted (nothing under a body); pin-1 marks on all nine ICs; polarity on four
electrolytics `[repo bom.csv:77]`, three Schottkys, the LED and the TO-92 flat;
≥1.0 mm text height and ≥0.15 mm stroke; and **the three trimmers labelled by
job, not refdes** — `ZERO`, `P-GAIN`, `P-OFF` — because three identical cermets
set by three different procedures in two different milestones is how a
commissioning step goes to the wrong part.

Plus a **board revision string and date in silk**, which is the thing you
actually want at bring-up and which no fiducial replaces.

## M15 — Fiducials: agreed, none

The plan's own reasoning is correct and consistent. Hand-assembled; no
pick-and-place file, no fab BOM, no rotation table `[repo pipeline:224-228]`.
Fiducials serve a placement machine's vision system and nothing else on this
board. **Confirmed: do not add them.** If assembly is ever bought, they are added
with the `pos` export the plan already defers `[repo pipeline:230-233]`, and the
board will be respun by then anyway.

## M16 — Kelvin on `R-ILIM`: do it, and do not rank it highly

Requested in the slice, so it is priced. `R-ILIM` is 50 mΩ and the trip is
`47 mV / 50 mΩ = 0.940 A` `[repo power-entry.md:129-131]`. Copper in the current
path between the two sense taps adds directly. A realistic error — the tap taken
5 mm downstream on a 2 mm-wide 1 oz trace — is 2.5 squares = **1.23 mΩ = +2.5 %**,
moving the trip from 940 mA to 917 mA `[calc]`.

Real, and it should be routed correctly: both taps land on the resistor's own
pads, symmetric, with all 1 A copper entering from the outboard ends. But 2.5 %
is small against a threshold tolerance the BOM already says is the binding term:
"The stated 0.9–1.13 A window is ±11 % and is **NARROWER THAN THE LT1641'S OWN
SENSE-THRESHOLD TOLERANCE**" `[repo bom.csv:64]` — and E6 measures the trip on
the bench regardless. **Free to get right, not worth ranking above M1–M10.**

## M17 — Guard rings around the in-amp inputs: **not justified on this board**

Requested in the slice; the arithmetic says no.

The `IN+`/`IN−` nodes are not high-impedance in normal operation. Each is driven
through 10 kΩ + 1 kΩ from the cable `[repo breath-receive-stage.md:156-159]`,
shunted by 1.5 nF and 15 nF, with 1 MΩ to the analog return. **With the cable
plugged the node impedance is 11 kΩ ‖ 1 MΩ ≈ 10.9 kΩ** `[calc]` — a guard ring
around that is decoration.

The 1 MΩ case only appears with the cable **unplugged**, which is what `R4`/`R5`
exist for `[repo breath-receive-stage.md:159]`. Even then: a poor 1 GΩ surface
contamination path from a ±12 V net gives 12 nA → 12 mV → ×2.185 = **26 mV at
the in-amp output**, 0.26 % of a 10 V span, with no cable attached `[calc]`.
FR4 surface insulation resistance is normally three orders better than 1 GΩ
`[from memory]`.

**What the arithmetic does support instead**, and which is cheaper than a guard
ring: keep ±12 V nets off the `IN+`/`IN−` pins' immediate neighbourhood, and
specify no-clean flux or a clean under the in-amp. Note also that the INA828 has
an integrated RFI filter at −3 dB / 53 MHz and *tabulated* EMIRR, with worst
cases of **48 dB differential at 400 MHz** `[repo bom.csv:28, SBOS792A]` — so RF
rectification is the mechanism to watch, not DC leakage, and it is already
addressed by putting `C_diff`/`C_cm` **ahead** of the in-amp
`[repo breath-receive-stage.md:238-252]`.

The genuinely high-impedance node on this board is `TIMER` on the load switch:
ramped at ~3 µA against a 1.233 V threshold — an equivalent 411 kΩ `[calc]` —
and the corpus already warns "leakage is a meaningful fraction of the 3 µA
pull-down" `[repo power-entry.md:278-280]`. Keep it small, clean and away from
+12 V. Still not a guard ring.

## M18 — The `ON` pin is a comparator input on a flying wire

`power-entry.md`'s *Still not designed* list: "There is no divider, no logic
level, no supply, no pull-down, no debounce and no UVLO threshold specified
anywhere — four missing passives on the node that decides whether the instrument
powers up at all" `[repo power-entry.md:296-301]`. The pin's input current is
−1 µA and its hysteresis is 80 mV `[repo power-entry.md:219]`.

**Layout rule regardless of the values:** the `ON` divider and its filter cap sit
at the LT1641's pin, not at the panel toggle, and the Thevenin impedance is kept
≤10 kΩ so the 1 µA input current is ≤10 mV against 80 mV of hysteresis `[calc]`.
A high-value divider at the far end of a flying wire to a panel switch is a
comparator input on an antenna.

## M18b — The gate network is now a compensated loop, and it appeared after the plan was written

`power-entry.md`'s load switch has gained `R-GATE-SER` 10 Ω in series with the
FET gate and `R-GATE-COMP` 1 kΩ in series with `C-GATE` from `GATE` to
`PWR_GND`, both "read straight off ADI's typical application"
`[repo hardware/bom.csv:123-124]`. That is no longer a capacitor hung on a pin —
it is a compensation network around a charge pump driving a DPAK gate through
the 1 A switching node.

**Rules to add:** `R-GATE-SER`, `R-GATE-COMP` and `C-GATE` sit at the LT1641's
`GATE` pin with the FET gate within ~10 mm, and the `GATE`–`PWR_GND` loop is
kept tight and away from the drain's copper. And `C-TIMER` is now a **10 µF
low-leakage** part `[repo bom.csv:119]` on a node ramped at ~3 µA — equivalent
411 kΩ `[calc]` — so its pads and the `TIMER` trace stay small, clean and clear
of +12 V, per M17.

## M19 — Creepage and clearance on ±12 V: **no rule needed**

Requested in the slice; the answer is negative and worth recording so it is not
re-asked. The largest potential difference on the board is 24 V, between `+12V`
and `-12V`. IPC-2221 Table 6-1, class B1 (external, uncoated, ≤3050 m), 16–30 V:
**0.1 mm** `[from memory — IPC is not reachable from this sandbox, so treat the
number as unverified]`. Any fab's own minimum — Sol uses 0.15 mm `[github,
verified: mainboard.kicad_pcb:201]` — clears it by 1.5× or better.

**Nothing on this board needs a creepage rule that the fab minimum does not
already give.** Setting the board clearance to 0.2 mm and moving on is correct.

---

# 3. Mechanically enforceable, versus what needs a human

## Enforceable in `verify.py` — write these

| Check | Rule | How |
|---|---|---|
| Four returns distinct | M2 | Netlist comparison, four names not three |
| No bare `AGND` in the netlist | M2 | String assertion on net names |
| Supply/reference pin has a cap | M5 | Walk pins from the netlist, not caps |
| `C-DECOUPLE` count = 19, mapped | M5 | Netlist ↔ `bom.csv` |
| Decoupler ground via ≤1 mm from its pad | 1.1 | Pad/via geometry |
| Decoupler returns to the *correct* zone | 1.1 | Pad net + zone net |
| Zone fills as one polygon, zero islands | M6 | `pcbnew` zone/island API after `Fill()` |
| Stitching via pitch ≤25 mm per zone | M6 | Via positions vs zone outline |
| **Return-path continuity under `Analog`/`Reference`/SPI** | M6 | Rasterise filled polygons; sample track centrelines |
| **Max parallel run: SPI vs `Reference`/`Analog`** | M1 | Track segment pairs; assert no parallel run >5 mm within 1 mm centres |
| Keepout window covers both breath legs | M3 | Keepout polygon vs both track paths |
| Panel footprint origin vs panel data, ±0.1 mm | M9 | Placement vs the one panel file |
| Six ⌀3 mm voids at jack barrel centres | M11 | Drill/`Edge.Cuts` vs `J-CV` footprint origins |
| Bench-selected parts are THT, ≥5 mm clear, outside the etherCON envelope | M7 | Refdes list + footprint + keepout polygon |
| Named test pads all present | M7 | Netlist |
| Trimmers on the rear side, ≥15 mm axial clear | M8 | Layer + height keepout |
| Etherco envelope keepout empty | M8 | Courtyard vs polygon |
| Copper-edge clearance ≥0.3 mm; min web | M12 | Native DRC once *set*; assert the setting too |
| No via in an SMD pad; all vias tented | M13 | Via vs pad geometry; mask apertures |
| Zone pad connection set explicitly (not defaulted) | M6 | Read the zone's `connect_pads` |
| Silk not over pads; text ≥1.0 mm / 0.15 mm | M14 | Native DRC + text attribute scan |
| Power width from IPC-2221, with the arithmetic in the script | 1.3 | Already the plan's intent; fix the comment |

Two of these — return-path continuity and max-parallel-run — do not exist in any
tool and are each roughly fifty lines against `pcbnew`. They are the highest-value
scripts in this slice, because they check the two things that actually degrade a
2-layer precision analog board and that DRC is structurally incapable of seeing.

## Needs a human eye — do not pretend otherwise

- **Which net each of the four returns *should* contain** (M2, M4). A script can
  assert a partition; only a person can say it is the right partition. The DAC's
  ground pin is the specific open question.
- **The 74AHCT125 / DAC ground relationship** (M4). Two defensible answers with
  different costs; a check can only enforce whichever was chosen.
- **The panel/shield bond** (M10). It is a policy the repo has sixteen words on.
- **Where `V_ref` runs** (M1). A script can assert it is locked and short; only a
  person decides the route.
- **The board-to-panel stack-up** (M9). Two banked numbers disagree by 4.8 mm;
  resolving that is arithmetic on a drawing, not a board check.
- **`TRIM-GAIN`'s wiper strap** (M8) and the jack tip-normal pins (M11). Footprint
  and intent decisions.
- **Whether the etherCON's eight conductors reach the board as a soldered tail or
  a short internal lead**, and how much the breath pair untwists doing it. ADR
  0004 already prices intra-pair coupling at 365–907 mV against a 678 mV margin
  `[repo digital-and-supervision.md:91-93]`, and that arithmetic was for the
  cable, not for whatever happens in the last 30 mm.

---

# 4. What is actively wrong for this board

## W1 — The `Analog` hand-route class contains the robust nets and omits the fragile ones

`Analog` is "`BREATH`, pitch and mod outputs" `[repo pipeline:141]` and the
hand-route list adds the pitch feedback loop and the `BREATH`/`AGND` pair
`[repo pipeline:156-164]`.

Every one of those outputs has 1 kΩ of series isolation and a shunt capacitor at
the jack — `C-FILT-PITCH` 10 nF, `C-FILT-MOD` 82 nF, `C-OUT-BREATH` 330 nF
`[repo pitch-stage.md:136, mod-channels.md:102, breath-output-stage.md:128]`.
They are the most abuse-tolerant nets on the board.

Meanwhile **`VREFOUT`, `V_ref`, the three trimmer wipers, the mod channels'
shared 3.3333 V and `AVDD` are in no class at all** and go to Freerouting. On
`V_ref`, 1 mV is 1.2 cents `[repo pitch-stage.md:116]` — more than the entire
pitch budget under any of its four disputed candidates
`[repo config/figures.yaml:172-179]`.

**Fix:** add the `Reference` class of M1 and lock it. The output nets can stay
hand-routed; they are cheap. The point is that the list is currently half-empty
at the sensitive end.

## W2 — "Three grounds" is four grounds, and `AGND` names two nets

Detailed at M2. Two specific wrongs in the plan text:

- Stage 5's heading and its premise sentence — "A single `GND` pour ties
  `PWR_GND`, `DIG_GND` and `AGND` together" `[repo pipeline:179-180]` — omit the
  **module analog return**, which is ADR 0004's third row
  `[repo 0004:609]` and the home of the 5.7–7.2 cent term the same paragraph then
  cites `[repo pipeline:181-182]`. The paragraph names the error and then leaves
  out the net the error is in.
- `verify.py`'s "no two nets merged; `AGND`, `PWR_GND`, `DIG_GND` still distinct"
  `[repo pipeline:206]` **cannot catch the merge that matters**, because the two
  nets at risk are both called `AGND`.

## W3 — "`AGND` tied exactly once" is a check for a property `AGND` does not have

`verify.py` asserts "`AGND` tied exactly once" `[repo pipeline:207]`. ADR 0004:
"**`AGND` is not in this list.** It terminates at the in-amp's `IN+` and at the
two 1 MΩ bias resistors, and that is all it does"
`[repo 0004:630-632]`. It is not tied to a ground at all — once or otherwise.

The assertion is either vacuous or, read literally by whoever implements it,
actively harmful: an implementer who takes it at face value will *create* a tie
to satisfy it, which is the exact failure the rule was written to prevent. What
the check should say is: **`AGND_SENSE` connects to exactly three things — the
etherCON pin, `R2`, and `R4` — and to no zone, no via into a pour, and no other
net.**

## W4 — "Matched and parallel" is the right words for the wrong physics, and the plan's own keepout undoes it

Detailed at M3. To be explicit about the wrong reasons, because "matched and
parallel" will otherwise be implemented as differential-pair length matching:

- **It is not a differential pair.** `BREATH` is single-ended, driven from a
  1 kΩ-series-protected buffer output on the instrument, and `AGND` is a sense
  return that carries no current `[repo breath-receive-stage.md:22-28, 221-224]`.
  There is no differential impedance to control.
- **Propagation-delay matching is meaningless.** The channel is band-limited to
  482 Hz by `C_diff` ahead of the in-amp `[repo breath-receive-stage.md:160]`.
  Skew across 45 mm of FR4 is ~0.25 ns `[calc]`.
- **Loop-area/magnetic matching is not load-bearing either**, for the same
  reason: the 482 Hz differential pole sits *ahead* of the amplifier
  `[repo breath-receive-stage.md:248-252]`, so HF magnetic pickup into the loop
  is filtered before it is amplified.
- **The real reason is capacitive symmetry to the analog return**, at
  0.0399 pF/mm `[calc]`, into a 60 dB budget already exhausted by `C_cm`
  tolerance at 59.7 dB `[calc]`.

And the plan's stage-5 keepout — a void under `AGND` and a pour under `BREATH` —
is the single most efficient way to create the asymmetry the rule is supposed to
prevent. **Two of the plan's rules fight.**

## W5 — "The FET's thermal pad", and copper as a heatsink, is the wrong worry

The plan locks "the 1 A load-switch path **and the FET's thermal pad**"
`[repo pipeline:164]`, which reads as a thermal-copper rule. `power-entry.md`
already refuted that on its own page:

> "**And the criterion is not thermal**: a DPAK is 0.6 °C/W at 50 ms, so 12 W is
> a 7 °C rise. **The killer is Spirito / linear-mode derating at V_DS = 12 V**"
> `[repo power-entry.md:289-293]`

At 50–100 ms the transient thermal impedance is a package property; board copper
does not participate. Steady-state dissipation is `I²R_DS(on)` at 360 mA, which
the same page dismisses as irrelevant `[repo power-entry.md:289-290]`. And the
part is a `-1`: it **latches** `[repo power-entry.md:303-305]`, so there is no
repetitive-pulse duty to integrate.

The DPAK tab is the **drain**, which in a high-side N-FET "is *always* at 12 V"
`[repo power-entry.md:136-138]`. So what the pad actually is, on this board, is a
large area of live +12 V copper — a placement and clearance question, not a
thermal one, and M13's "no thermal via array under the tab" follows.

**The same applies to the LM317**, which the slice asked about: `(12 − 0.28 −
5.21) V × 13 mA` = **85 mW** `[calc, from repo bom.csv:38]` in a TO-92 at
~180–200 °C/W `[from memory]` — a 15–17 °C rise. **No copper area required.**

## W6 — "No copper under the connector bore or panel cutouts" targets features the PCB does not have

`verify.py`'s last assertion `[repo pipeline:211]`. Check what it can match:

- **The etherCON's ⌀24.0 mm bore is in the panel, not the board**
  `[repo bom.csv:19]`. The connector's body sits 34.55 mm *behind* the panel
  `[repo bom.csv:19]` and the board carries a **notch** for it
  `[repo bom.csv:71]`. There is no bore through the PCB to keep copper out of.
- **The jack, pot, toggle and LED holes are also panel features**, 7–14 mm in
  front of the board plane.

So the rule as written will either match nothing, or — worse — be implemented by
projecting panel cutouts onto the board and creating keepouts in the wrong place,
sterilising board area on a 45 × 110 mm board that is already tight.

**Meanwhile it misses the one real PCB void the corpus specifies**: Thonk's
"leave a 3 mm hole or a void in the PCB under the barrel" `[repo bom.csv:16]`,
six times over (M11).

**Fix:** replace it with (a) six ⌀3 mm barrel voids asserted against the `J-CV`
footprint origins, (b) a component and copper keepout equal to the etherCON's
projected envelope, and (c) an `Edge.Cuts` minimum-web assertion at the notch.

## W7 — The build stops at "five full iterations" and reports; nothing catches a *passing* board that is wrong

Minor, but it is the plan's own escape hatch: "Five full iterations, then stop
and report rather than thrashing placement" `[repo pipeline:213]`. Every check in
§6 is a pass/fail on geometry. **None of them is a measurement.** A board that
passes all seven can still have `V_ref` routed 90 mm alongside `SCLK` on the same
layer, because no rule names it — which is W1 restated as a process defect, and
it is exactly the class `CLAUDE.md` §4 says the checker cannot catch and a review
wave must.

The honest addition to stage 6 is not another assertion. It is: **the locked-net
route and the pour are reviewed by eye, once, against this list, before gerbers**
— and the review is recorded, in the way this project records everything else.

---

## Summary — the five that would actually cost this board

1. **M1 / W1** — `V_ref` and `VREFOUT` are autorouted. 1 mV = 1.2 cents = the
   whole pitch budget.
2. **M2 / W2 / W3** — four grounds, not three, and `AGND` names two different
   nets across five files. The plan's own no-merge check cannot see the merge.
3. **M4** — the SPI return path is unspecified and, on ADR 0004's ground
   assignment, runs the length of the board. ~0.5 V of bounce on the DAC's own
   ground reference `[calc, order of magnitude]`.
4. **M3 / W4** — the `AGND` keepout breaks the breath pair's capacitive symmetry,
   into a CMRR budget that is already 0.3 dB short on component tolerance alone.
5. **M7 / M9** — two parts are chosen on the bench, one test needs a wire to
   clamp a probe around, there are no test points, and two banked mechanical
   numbers put the board plane 4.8 mm apart.

Everything else is cheap to add and cheap to check. These five decide whether the
pipeline produces a board that meets the error budget the rest of the corpus was
written to defend.
