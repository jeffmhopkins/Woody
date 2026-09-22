# G11 — Do the decision records still describe the thing that exists?

**Slice:** G11, ADR audit. **Cold:** I read nothing under `docs/review/`.
**Revision:** the brief names `a4b80b1`. `git log` puts HEAD at `25cc740`,
two commits later. `git diff --stat a4b80b1..HEAD` `[test]` shows the only
change is `docs/review/2026-09-22-goal-verification/README.md` (+81), so
`docs/decisions/**`, `hardware/**` and `config/**` are byte-identical at both
revisions and every `[repo]` citation below holds at `a4b80b1`. Working tree
clean.

**Scope covered:** all fourteen ADRs read end to end, against `hardware/**`,
`config/figures.yaml`, `config/key-layout.yaml`, `docs/reference/**`,
`ROADMAP.md`, `README.md`, `hardware/bom.csv`, `datasheets/MANIFEST.csv`.

Findings are filed against the ADR and the specific claim. Provenance is on
every one.

---

## A. Decisions that no longer describe the design

### G11-1 — ADR 0005 still specifies a ramp no capacitor can deliver (confirmed)

`[repo] docs/decisions/0005-power-architecture.md:263` — the decision line is
still **"1.0 A, latch-off, with a programmed 50–100 ms ramp."** The warning
block immediately under it (`:265–279`) records that the LT1641's `GATE`
pull-up is −5/−10/−20 µA, a 4:1 window that cannot be held inside a 2:1 time
window, and ends **"Not decided here; raised against this ADR by the wave that
read the datasheet."**

`[repo] config/figures.yaml:499–506` — `loadswitch-gate-cap` is
`"82 nF, ramp 49-197 ms (98 ms typ)"`, **settled**, with a `note` saying ADR
0005's spec "IS NOT ACHIEVABLE with this part".
`[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:256–270`
derives the same envelope.

So a **settled** register figure and the owning schematic both contradict a
live line in an **Accepted** ADR, and the ADR records the conflict without
resolving it. The two named exits (widen to 50–200 ms, or program the ramp
externally) are both still open. This is the defect the brief predicted; it is
still live at `a4b80b1`.

### G11-2 — ADR 0005's Decision paragraph specifies the 3.3 V buck its own next section calls wrong

`[repo] 0005:43–44`: *"The rack already provides ±12V… The instrument takes
+12V up the cable and **derives 3.3V locally with a small buck converter**."*

`[repo] 0005:69–72`, twenty-five lines later: *"### The rail that matters is
5 V, not 3.3 V — An earlier revision of this ADR specified a 12 V to 3.3 V
buck. **That is wrong**…"*, and `[repo] 0005:203` *"**3.3 V does not need its
own converter.**"* The power tree at `0005:184–201` shows two 12 V→5 V bucks
and no 3.3 V converter.

The refutation exists; it never reached the Decision paragraph, which is the
one a reader stops at.

### G11-3 — ADR 0005 gives two different clamp-legal worst cases

`[repo] 0005:161` load table: `| **Clamp-legal worst** | 928 mA | 119 mA |
**579 mA** | 6.5 W |`.
`[repo] 0005:296`: *"it is set from below, by the clamp-legal worst case of
**~630 mA** plus ramp current"*.

`[calc]` the table's own convention (`0005:170–173`: convert at 11.4 V, buck
90 % efficient) gives `928 mA × 5 V ÷ 0.9 ÷ 11.4 V = 452 mA` + `119 mA` =
**571 mA**, which is the 579 in the table to within rounding and is not 630.
The 1.0 A limit is argued from the 630.

### G11-4 — ADR 0001 still places the MCU with the display

`[repo] 0001:89–93`: *"The display is the only thing that cannot run far…
**So the MCU lives with the display** and everything else runs long and
slow."*

`[repo] 0013:144–148` puts the display board at the Top and the real-time MCU
at the Bottom (tail), 360 mm apart (`0013:174–183`). ADR 0001's own
supersession note (`0001:68–75`) covers the *topology diagram* and the "bare
module vs dev board" half of the Decision sentence, and explicitly does not
reach this paragraph. `0001:78` in the replacement diagram correctly puts the
MCU at TAIL — so the ADR contradicts itself eleven lines apart.

### G11-5 — ADR 0001's Consequences instruct the build ADR 0013 rejected

`[repo] 0001:361–363`: *"Buy a **plain** S3 dev board plus a **separate**
display module, so the bench setup matches the final architecture **rather
than an integrated-screen board that would have to be unlearned later**."*
ADR 0008 selects the LilyGO T-Display-S3 AMOLED — an integrated screen-and-MCU
board — as the display board (`[repo] 0008:3, 157`), and ADR 0013:73–76 says
that category is reopened and *"A C6 is perfectly good in this role"*.

`[repo] 0001:364–365`: *"**Custom carrier design needed eventually**: USB-C,
ESD protection, boot/reset, 3.3V regulation. Espressif publishes reference
designs for this."* `[repo] 0013:228–232`: *"**Do not design a custom ESP32-S3
carrier.** That means taking on the module footprint, USB-C, ESD, boot and
reset circuitry…"*. `[repo] ROADMAP.md:54` (E13) says **"Passive carrier… No
MCU, no USB, no RF"**.

`[repo] 0001:359–360`: *"Dev boards remain the bring-up platform… they are the
reference the custom boards get checked against."* Under 0013 the dev boards
**are** the final boards (`0013:234–235`, `0007:147–150`).

Three consequences of an Accepted ADR, none marked, all reversed.

### G11-6 — ADR 0009 states the superseded key-input network and attributes it to ADR 0001

`[repo] 0009:519–522`: *"**Fit the key input networks.** …— **10 kΩ, 100 Ω and
10 nF** per switch position on the cluster boards (**ADR 0001**)."*

`[repo] 0001:215`: *"**Per switch position: 2.2 kΩ to 3V3, 100 Ω in series,
47 nF to ground**"*. `[repo] hardware/bom.csv:35` `R-KEY-PU,…,2k2 1%`.
`[repo] config/figures.yaml:196` derives `key-scan-current` from
`2.2 kohm + 100 ohm`; `:244` derives `key-press-time` from `47nF`.

This is a live stale value **and** a citation that resolves to the opposite
content. It is invisible to the checker: `figures.yaml:197` forbids
`"10 kOhm pull-ups"`, and `:495` forbids `"10 nF timer"` — neither spelling
matches `10 kΩ, 100 Ω and 10 nF`. `[test] PreToolUse hook output, every Bash
call this session: "staleness check: PASS no live stale values"`.

### G11-7 — ADR 0014 still assumes one 5 V regulator shared by both dev boards

`[repo] 0014:181–183`: *"**The instrument's own regulator, which is a 1 A
part.** The matrix hangs on the R-78E5.0-1.0 **alongside both dev boards**…"*
`[repo] 0014:455–457`: *"The matrix **shares the 1 A R-78E5.0 with both dev
boards**, which take roughly 330–400 mA between them, so a full-field matrix
would ask for about 1.36 A from a 1 A part."*

`[repo] 0013:246–247`: *"**Two** R-78E5.0 regulator modules — **one per dev
board**"*. `[repo] 0005:207–212` *"**Two bucks, not one.**"*, with the power
tree at `0005:190–194` putting the matrix on buck A with the real-time board
only and the display board alone on buck B.

ADR 0014's headroom argument — which is the stated justification for the
brightness cap — is computed on a topology two other ADRs deleted.

### G11-8 — ADR 0014 lists a refuted coupling route as one of four live ones

`[repo] 0014:534–539`: *"**Four independent routes** were found by which LED
current reaches the pitch jack — the offset reference divider, **a shared
reverse-polarity diode**, the module's internal ground and the rack's bus
ground — adding to more than every static term in ADR 0006's precision budget
put together."*

`[repo] 0006:641–659` strikes that row through: *"**The 1N5817 row is refuted
and struck through**… lands **five orders of magnitude below the smallest
other term in this table**."* `[repo] 0004:323–346` splits the diodes and
cites `diode-split-rationale` rather than restating it. `[repo]
figures.yaml:621–624` records the settled value as *"fault isolation and HF
isolation"*, not pitch modulation.

So 0014 still sums a term 0006 removed, and the "more than every static term
put together" claim is computed with it in.

### G11-9 — ADR 0013's carrier holds headers and a regulator for a board 360 mm away

`[repo] 0013:234–247`: the carrier holds *"Headers the dev boards plug into"*
and *"**Two** R-78E5.0 regulator modules — **one per dev board** … and the
umbilical connector"*. The same ADR's own zone table (`0013:144–148`) puts the
display board at the Top and the carrier at the tail, and `0013:178` measures
that run at **360 mm**.

`[repo] hardware/carrier/carrier.md:25–35` has already noticed — *"## One dev
board, not two … The display board is 360 mm away at the top of the instrument
(ADR 0013's own zone table)… This page therefore draws **one** dev-board
socket pair and leaves the second regulator's location open"*. The schematic
page corrected itself; the ADR it cites did not.

### G11-10 — ADR 0003 puts the analog star point on a board that carries no analog

`[repo] 0003:693–699`: *"**The star point is the analog ground pour on the
bottom cluster board, at the sensor and reference**… Everything analog in the
instrument — the sensor, the REF5050, both halves of the OPA2197, the ADC
divider — sits on that one board."*

`[repo] 0001:85–86`: the cluster boards hold *"switches, ONE 74HC165 each, its
decoupling, and that cluster's key networks"* — nothing analog.
`[repo] 0013:242–248` and `[repo] ROADMAP.md:54` put the MCP3202, REF5050 and
OPA2197 on the **carrier**. `[repo] 0003:223` heading is *"Sensor placement: at
the bottom, **with the real-time board**"*, i.e. the carrier.

The definition a rule set refers back to names the wrong board. `[repo]
hardware/interfaces/breath-sense-link/breath-sense-link.md:101` cites *"ADR
0003 names the star point as…"*, so the mis-naming is already being cited.

### G11-11 — ADR 0003 calls the restrictor "the Helmholtz restrictor" after deleting the Helmholtz model

`[repo] 0003:262–278`: *"**The resonance needs handling, and the model this ADR
used was invalid.** An earlier revision called it a **Helmholtz resonator** at
~320 Hz… The lumped assumption is violated backwards. The correct model is a
**distributed pipe**."*

`[repo] 0003:804–807`, 540 lines later: *"**A porous hydrophobic PTFE plug at
the sensor port.** … it is **the same part as the Helmholtz restrictor
above**"*. There is no Helmholtz restrictor above any more.

### G11-12 — ADR 0003 refers to "Option A", which no longer exists in the document

`[repo] 0003:784`: *"Short tubes accumulate less, **which Option A gives for
free**."* The placement section was rewritten to a single decision
(`0003:223–233`, *"Sensor placement: at the bottom"*); there are no lettered
options anywhere in the ADR, and the chosen tube is 400 mm, not short
(`0003:253–256`). A reader cannot resolve the reference.

### G11-13 — ADR 0009 prices a width change against a layout it has already voided

`[repo] 0009:203–204`: *"If any of those fail, the fix is narrowing toward
55 mm, **which costs the two-column layout**."*
`[repo] 0009:148`, fifty-five lines earlier, in the same ADR: *"**Two-column
key clusters.** Void: keys run in a single line (ADR 0010)."*
`[repo] 0010:83–86` and `[repo] config/key-layout.yaml:68` both confirm a
single line.

The stated cost of narrowing is a thing that does not exist, so the M2 decision
this paragraph frames is framed wrongly.

### G11-14 — ADR 0002 still instructs the reader to fetch documents that are banked

`[repo] 0002:128–132`: *"**Download the datasheet and the STEP model before any
CAD starts.** They are at gateron.com/pages/3d and the KS-33 Low Profile 2.0
datasheet page… **Put the STEP in `mechanical/`** so the stack is modelled
against the real solid."*

`[repo] 0002:167–172`, thirty-five lines later: *"**✅ 2026-09-21: THE DRAWING
IS IN HAND**… banked at
`datasheets/mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`."*
`[test] ls datasheets/mechanical/` → `GATERON-KS-33-3D.step`,
`GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf`,
`GATERON-KS-33-SW_KS33_1u.kicad_mod`, `GATERON-KS-33-ergogen-footprint.js`.
`[test] ls mechanical/` → only `cad/`, `drawings/`, `export/`, all `.gitkeep`.

The instruction is live, already done, and points at the wrong directory —
`datasheets/` is the bank (`CLAUDE.md` §3), not `mechanical/`.

### G11-15 — ADR 0012 still recommends the display ADR 0008 rejected

`[repo] 0012:99–101`: *"That materially changes ADR 0008. **A small OLED**,
previously marginal because a four-channel routing matrix needed depth to
navigate, **is now comfortable and arguably preferable**."*

`[repo] 0008:23–26`: *"**AMOLED.** This **supersedes an earlier lean toward a
monochrome OLED**"*, and `0008:3` records the board as selected. ADR 0012
carries no note that 0008 answered it the other way, while 0008 carries a
"Revised by ADR 0012" header — the supersession is recorded in one direction
only (see also G11-26).

### G11-16 — the bonded body survives in six ADRs after ADR 0009 made it serviceable

`[repo] 0009:553–558`: *"## The body comes apart — **This supersedes the page's
earlier assumption that the stack is bonded shut.**"*, closing on six
fasteners (`0009:589–593`). ADR 0002 corrected itself (`0002:90–95`).

Still arguing from a body that cannot be opened `[repo]`:

| ADR | line | text |
|---|---|---|
| 0001 | 160 | "in a strap-worn instrument that is **bonded shut**" |
| 0001 | 191 | "inside a body that **cannot be reopened**" |
| 0001 | 244 | "they **cannot be retrofitted into a bonded body**" |
| 0001 | 337 | "**the body bonds shut**, so it can never become an input" |
| 0003 | 248 | "the most likely part to fail, in a body that **cannot be reopened**" |
| 0004 | 960 | "eight soldered wires inside a body that **cannot be reopened**" |
| 0005 | 239 | "a panel location inside a **bonded body that cannot be reopened**" |
| 0007 | 199 | "In a body that **cannot be opened**, two pins is a cheap price" |
| 0013 | 294 | "Its own USB is inside a **bonded body** and reaches nothing" |
| 0014 | 53 | "inside a **bonded stack that cannot be reopened**" |
| 0014 | 83 | "In a bonded laminated body that **cannot be opened casually**" |
| 0014 | 497 | "flashing and USB MIDI both require it in a body that **cannot be opened**" |

`config/key-layout.yaml:150` carries it too. Most of these are load-bearing —
0001:244 is the reason the five/six wiring fixes are called irreversible,
0013:294 is the whole argument for flashing the display board over UART, and
0007:199 is why UART0 is spent on a console. `ROADMAP.md:78` was corrected;
the ADRs were not. Several of the arguments probably still hold on the
"expensive, not impossible" reading `0009:492–503` offers — but none of them
says so, and a reader cannot tell which survive.

---

## B. Citations that resolve to the wrong content

### G11-17 — ADR 0005 cites the wrong schematic page for the load-switch sizing, twice

`[repo] 0005:272`: *"the **guaranteed envelope is 49–197 ms**
(`hardware/module/power-entry/power-entry.md`)."*
`[repo] 0005:343–344`: *"`C-GATE` at 82 nF and `C-TIMER` at 10 µF, **sized in
`hardware/module/power-entry/power-entry.md`** against the datasheet"*.

`[test] grep -n "ramp|C-GATE|82 nF|LT1641" hardware/module/power-entry/power-entry.md`
returns two hits, both labels inside an ASCII drawing (`:57`, `:64`). No
sizing, no envelope, no derivation.
`[repo] config/figures.yaml:503, 487, 512` name the owner of all three
load-switch figures as
`hardware/module/umbilical-load-switch/umbilical-load-switch.md`, which is
where the derivation is (`:255–282`).

Both citations were correct before the load switch got its own circuit
directory and neither followed it. Refdes drifted too: ADR 0005 writes
`C-GATE` / `C-TIMER`; the register and BOM use `C-GATE-LOADSW` /
`C-TIMER-LOADSW` (`figures.yaml:484, 500`).

### G11-18 — ADR 0009's key-network citation

Covered in G11-6: `0009:521` attributes `10 kΩ / 100 Ω / 10 nF` to ADR 0001,
which specifies `2.2 kΩ / 100 Ω / 47 nF`.

### G11-19 — citations I checked and that **do** resolve (recorded so the next round need not redo them)

`[repo]` all verified against the cited ADR text:

- `hardware/interfaces/key-chain-loom/key-chain-loom.md:58` "ADR 0001 fix 1
  calls this the highest-value item on its list" → `0001:246–247` ✔
- `key-chain-loom.md:102` "fix 2" chained-not-starred → `0001:267` ✔
- `key-chain-loom.md:105` and `cluster-boards.md:77` "fix 3" data toward the
  clock source → `0001:269–274` ✔
- `config/key-layout.yaml:152` and `bom.csv:35` "ADR 0001 fix 6 / fix-6 fault"
  floating CMOS inputs → `0001:292–295` ✔
- `bom.csv:49` / `key-chain-loom/bom.csv:2` "ADR 0001 item 1" a ground between
  every signal → `0001:246–258` ✔
- `bom.csv:30`, `carrier/bom.csv:6` "Two spares per ADR 0009" → `0009:524` ✔
- `bom.csv:48` "banned by the ADR 0013 package policy" → `0013:253–262` ✔
- `0004:347` "`D-REVPOL` qty 3, ADR 0006" → `0006:661, 672` ✔ (note the BOM
  row's own `adr` column says `0005`, `[repo] bom.csv:57`; ADR 0005 does not
  name `D-REVPOL` — low severity, but the row and the prose disagree on which
  ADR owns it)
- `carrier.md:284` "ADR 0001 deleted `R-TERM-CHAIN`" → `0001:182` ✔

The numbered-item citations are therefore **sound**: no insertion has
renumbered anything (but see G11-23 for the count that states how many items
there are).

---

## C. Specs an ADR states that the parts do not support

### G11-20 — ADR 0009 asserts a KS-33 overall height the banked drawing does not dimension

`[repo] 0009:76–79`: *"**The KS-33 is 12.2 mm tall overall**, from Gateron's
published specification — this ADR previously called it unmeasured and
deferred it to M1, **which was wrong on both counts**: the switch is
documented, and **the number was available all along** (ADR 0002)."* The
cavity argument at `0009:81–85` rests on it: *"even if the entire 12.2 mm sat
inside it there would be 8 mm left… The earlier worry… **looks overstated**."*

`[repo] docs/reference/ks33-geometry.md:71–74` — the page that owns KS-33
geometry, written against the banked drawing: *"latch span 14.70, housing
bottom 2.50 ±0.05, pin tips 5.10… **Overall height is NOT-IN-DOCUMENT**:
neither the 12.75 mm measured off the STEP nor the BOM's 12.2 mm is confirmed
**or refuted**."*

So the vendor drawing that closed `plate-thickness` does **not** carry an
overall height, and the reference page says so explicitly. ADR 0009 states the
opposite in bold, calls the earlier caution wrong, and spends the margin.
`[repo] 0002:118–123` presents the same 12.2 mm under *"Known from the
published specification, **pending the drawing itself**"* — which was honest
when written and is now contradicted by the drawing having arrived without it.
`0002:87–90` still says the above/below-plane split is *"on the dimensioned
drawing"* and is a reason to download it; `ks33-geometry.md:91` has the split
(`housing bottom −2.50 mm`) and not the total.

**This is the shape the brief asked for**: a dimension asserted to a datasheet
that does not support it, with a clearance conclusion built on it.

### G11-21 — ADR 0006 keeps a trim-range specification its own adopted value violates

`[repo] 0006:478–481`: *"**Keep the trim range small — 5 to 10 %** — around a
fixed precision resistor."* The cost table at `0006:465–469` starts at 5 %
(22 ppm/°C, 2.4 cents) and has no row below it.

`[repo] 0006:744–746`, in the same ADR: *"**`TRIM-GAIN` shrinks to 200 Ω
(0 → +2 %)**, which drops its tempco contribution to ~2 ppm/°C"*, and
`0006:447`: *"At **200 Ω** it contributes **2 %**"*. `[repo]
hardware/module/pitch-stage/pitch-stage.md` is the owner page and carries the
200 Ω.

The prescription (5–10 %) and the decision (2 %) are 300 lines apart in one
ADR, and the cost table a builder would read cannot price the value actually
chosen.

### G11-22 — ADR 0008's breakout count does not add up, and I could not settle it

`[repo] 0008:166`: `| Breakout | **28 pins** — 18 GPIO plus 3V3 / GND / VBUS |`.
`[calc]` 18 + 3 = 21, not 28. Either there are duplicated power pins (possible)
or the 28 is wrong. `0008:176` and `0008:206` both argue from the **18**, and
`0013:70–71` needs only four, so nothing downstream breaks either way.

**Could not check.** `[test] python3 -c "pymupdf … LILYGO-T-DISPLAY-S3-AMOLED-SCHEMATIC.pdf"`
extracts 8 kB of Altium frame boilerplate and no `IO\d+` tokens at all — the
net labels are vector art. Rendering both sheets at 150 dpi and reading the
header blocks by eye is the way to settle it, and I did not do it. Flagged for
whoever owns the E1 pin-list print (`ROADMAP.md:195`).

### G11-23 — specs I checked against banked documents and found **supported**

Recorded so this is not re-done `[repo] datasheets/MANIFEST.csv`, `[calc]`:

- `0004:209` `0.625 × AVDD = 3.26 V at 5.21 V` → `0.625 × 5.21 = 3.256` ✔,
  and the ADR already records the `V_INH` band split it got wrong before.
- `0005:282` `R-ILIM 50 mΩ` against 39/47/55 mV → `0.78 / 0.94 / 1.10 A` ✔;
  `0005:284` "±17 %" → `(1.10−0.78)/2 ÷ 0.94 = 17 %` ✔.
- `0001:221–230` the whole key-network table reproduces exactly from
  `τ = 103.4 µs` / `4.4956 µs` and the 0.1435 V closed-switch pedestal:
  release `119.9 µs`, press `5.92 µs`, `1.43 mA`, `25.8 mA`, pole `1.54 kHz`,
  `54 dB` ✔. The onsemi source it cites is banked
  (`datasheets/logic/74HC165-onsemi.pdf`, MANIFEST row present).
- `0003:123` `Vout = VS × (0.1533·P + 0.053)` → `0.7665 V/kPa`, `0.265 V` at
  zero, `4.864 V` at 6 kPa ✔ against `sensor-full-scale` and
  `breath-sensor-slope`.
- `0003:163` sealed-cavity `ΔT/T`: `15/293 × 101.3 = 5.19 kPa`, `86 %` of
  6 kPa ✔. `0003:266` `π × 1.5² × 400 = 2.83 mL` ✔. `0003:255–256` pipe modes
  `343/(4×0.4) = 214 Hz`, `343/(2×0.4) = 429 Hz` ✔.
- `0004:687` `(10 × 5.08) − 0.3 = 50.50` ✔ and the whole 6/8/10HP web table ✔.
  `0004:771–779` clear-height and hardware-blocked-width arithmetic ✔ against
  `figures.yaml:405`.
- `0006:534–537` load-divider cents and `0006:372–378` tempco table ✔.
  `0006:775–777` RC corners: `15.92 / 1.941 / 482 Hz` ✔.
- `0009:296–320` etherCON tail-face margins, both orientations ✔.
- `0014:131–138` LED current table and the 2.23× correction ✔.
- All datasheets ADRs cite by path exist and have MANIFEST rows with SHA-256:
  `analog/REF5050.pdf`, `analog/DAC8568CIPW.pdf`, `analog/INA828IDR.pdf`,
  `analog/LT5400.pdf`, `discrete-and-power/LT1641.pdf`, `led/WS2815.pdf`,
  `mechanical/GATERON-KS-33-VENDOR-SPEC-DRAWING.pdf` `[test] ls + grep`.

---

## D. Supersession bookkeeping

### G11-24 — one decision recorded in two ADRs with different content: the umbilical bandwidth table

| | channels | payload | clock | `[repo]` |
|---|---|---|---|---|
| ADR 0003 | **7** at 4 kHz | **0.90 Mbit/s** | 2 MHz | `0003:419–425` |
| ADR 0004 | **6** at 4 kHz | **0.77 Mbit/s** | ≥1.5 → 2 MHz | `0004:58–73` |

`[calc]` both are internally right for their own count at 32-bit frames
(`6×32×4000 = 768 kbit/s`; `7×32×4000 = 896 kbit/s`). They cannot both be the
design.

**ADR 0004 is right and ADR 0003 is stale.** `0004:71–73`: *"(**Seven channels
were populated until the breath ambient-zero was deleted** — ADR 0003 — which
is slack…)"*. `0006:14, 25–31` frees DAC channel 6 and says *"Nothing claims
the freed channel"*; `0006:22` *"**Six of eight channels used**"*;
`0006:265` puts ch 7 *"refreshed every pass, like the other five"* = six;
`0006:272` *"the loop budget, which already assumes **six** DAC channels
serviced every 250 µs pass"*.

ADR 0003's own parenthetical at `:422–425` — *"ADR 0006 moved to 4 kHz and the
loop refreshes **seven**"* — is the fix for the *rate* half landing on the
retired *count*. A textbook "a fix whose own explanation restates the wrong
value".

### G11-25 — supersessions are recorded in one direction only, and no ADR carries `Superseded`

`[repo] docs/decisions/README.md:36–39` sets the rule: *"When a decision is
reversed, do not edit the old ADR. **Mark it `Superseded`** and write a new one
that says what changed."* `README.md:26–30` defines the status.

`[test] grep -n "^\*\*Status:\*\*" docs/decisions/*.md` — every one of the
fourteen reads `Accepted`. Nothing in the directory is `Superseded`, and the
index table (`README.md:53–68`) has no such row either. Instead:

| Superseded in place, inline | supersession note present? | backlink from the superseding ADR? |
|---|---|---|
| 0001 partitioning ← 0013 | yes, `0001:3–6, 68–75` | yes, `0013:5` |
| 0008 pin budget ← 0013 | yes, `0008:63–66, 152–155` | yes, `0013:12–13` |
| 0008 display scope ← 0012 | yes, `0008:7` | **no** — `0012:92–104` never says 0008 is revised by it, and still argues for an OLED (G11-15) |
| 0012 radio-off rule ← 0013 | yes, `0012:52–63` | yes, `0013:128–133` |
| 0005 battery architecture | kept as a titled "Superseded approach" section, `0005:10–36` | n/a |
| 0004 conductor budget ← itself | struck through, `0004:35–48` | n/a |

So the actual practice is in-place editing with inline notes, which is the
opposite of the stated rule, and the one case where the backlink is missing
(0012 → 0008) is the one that left a live wrong recommendation. Either the
README's format rule or the practice should move; right now the README
describes a process this directory does not use.

### G11-26 — the index table's known defect is still there

`[repo] README.md:44–51` warns about itself: *"This table is hand-maintained,
and on 2026-09-21 three of its fourteen rows disagreed with the ADR they point
at… **It should be generated from the `**Status:**` line of each ADR.** Until
it is, check the file before trusting the row."*

Rows and files agree today `[test] diff of the fourteen Status lines against
the table` — 0007 and 0008 now carry their board selections in both places.
But `README.md:55` states 0001 as *"Accepted (partitioning revised by 0013)"*
while 0008's and 0012's rows read a bare "Accepted" despite carrying
supersession notes of the same weight. The generator the README asks for is
still not written; this is a restated count/status of exactly the kind
`CLAUDE.md` rule 1 forbids, in the ADR directory's own index.

### G11-27 — no gaps, no stubs

`[test] ls docs/decisions/` — 0001…0014 consecutive, no gaps, no duplicates.
All fourteen have Context (or a titled equivalent), Decision, and Consequences
or a Consequences-shaped section. The shortest, 0011, is complete. None is a
stub. **`breath-working-point` is the one decision that is recorded nowhere** —
see G11-33.

---

## E. Values restated instead of cited

Every tracked figure I found restated inside an ADR, with whether it currently
agrees with `config/figures.yaml`. The checker counts 211 "restated-not-cited
(advisory)" corpus-wide `[test] hook output`; these are the ADR share.

**Restated and currently agreeing** (a latent defect, not a live one):

| figure | register value | ADR restatement `[repo]` |
|---|---|---|
| `plate-thickness` | 1.20 mm | 0002:138, 167, 176, 237, 240; 0009:64 |
| `dac-rail` | 5.21 V | 0003:375; 0004:178, 310; 0005:126; 0006:621 |
| `umbilical-current` | 359 mA | 0004:276, 284 (header), 627 ("~360 mA"); 0005:96, 159 (owner) |
| `panel-width` | 50.50 mm (10HP) | 0004:687, 756; 0009:323 |
| `panel-height-budget` | 110 / 115.5 mm | 0004:667, 790 (owner), 577 ("5.5 mm of slack") |
| `loadswitch-gate-cap` | 82 nF | 0005:272, 343 |
| `loadswitch-timer` | 10 uF | 0005:343 |
| `mod-reference` | 3.3333 V | 0006:15, 21, 92, 105, 117, 124, 265 |
| `sensor-full-scale` | 4.86 V | 0003:101 (with the citation beside it — the good form) |
| `breath-sensor-slope` | 0.7665 V/kPa | 0003:117 ("766 mV/kPa"), 123 |
| `key-scan-current` | 1.43 mA / 25.8 mA | 0001:230, 239 (owner is the schematic page) |
| `key-release-time` / `key-press-time` | 119.9 / 5.92 µs | 0001:227–228 |
| `marker-bits` / `free-bits` | 8 / 3 | 0001:323, 330, 340–341, 374; 0010:174–177 |
| `chain-connectors` | 8 | 0001:254 ("Eight connectors have to match") |
| `ks33-contact-bounce` | 5 ms max | 0002:218 — **cited by name, not restated. The correct form.** |

**Restated and currently disagreeing** — these are the live ones:

- **G11-28** `chain-conductors` = **12** `[repo] figures.yaml:269–272`, owner
  **ADR 0001**. `[repo] 0001:135` breaks it down as *"**12 per hop** — 6
  signals-and-supply, 5 grounds, 2 spare"*. `[calc] 6 + 5 + 2 = 13`. The
  correct breakdown is in the same ADR at `:252–253`
  (`GND SCK GND SH/LD GND SER GND QH GND 3V3 spare spare` = 4 signals + 3V3 +
  5 grounds + 2 spares = 12) and in `config/key-layout.yaml:108–109` (*"4
  signals…, 5 alternating grounds, 3V3, and 2 spares"*). The owner document's
  own comparison table does not sum to the figure it owns.

- **G11-29** `panel-height-budget`, **in the ADR that owns it**. `[repo]
  0004:841–845`: *"**The 97 mm above** is built from `[from memory]` component
  envelopes… **The layout is credible and it is not verified.**"* The derived
  content height directly above is **110 mm** (`0004:790`). 97 mm is one of the
  four retired candidates `[repo] figures.yaml:426` (*"It had four candidates —
  107, 97, 112, 124 — and the answer is none of them"*).
  `figures.yaml:407` forbids `"97 mm against ~110 mm"`, `"97 mm against ~110"`
  and `"= 97mm"` — **and this spelling, `The 97 mm above`, matches none of
  them.** `figures.yaml:415–419` records that the last four escapes of this
  same figure were each "by one removed space". This is the fifth, in the owner
  document, and the checker reports PASS.

- **G11-30** the key-input network in ADR 0009 — G11-6 above.

- **G11-31** `panel-height-budget` / `panel-width` consequence text.
  `[repo] 0004:596–597`: *"That discipline is what kept the panel **inside 10HP
  rather than 10 or 12**."* At 8HP the sentence parsed; after
  `8HP → 10HP` (`0004:688`) it says the panel was kept inside 10 rather than
  10. `hardware/module/panel/panel.md:54–59` has the corrected version.

- **G11-32** `pitch-cents-budget` is `disputed` with owner
  `pitch-stage.md` `[repo] figures.yaml:474–480`, and ADR 0006 — which contains
  the precision budget (`0006:372–378`, `:465–476`) — never mentions that the
  total is disputed or states one. A builder reading only the ADR would take
  `0.11 cents` / `5.4 cents` / `2.4 cents` as a settled budget.

- **G11-33** `breath-working-point` is `disputed` with owner
  **`docs/decisions/0003-breath-sensing-path.md`** `[repo]
  figures.yaml:465–472`, and the register's own candidate list says
  *"2.8 kPa (**cited to ADR 0003, which does not contain it**; the two
  schematic pages cite each other)"*. `[test] grep -n "kPa" 0003` → the ADR
  says only *"Normal wind-controller playing sits around 0–5 kPa"* (`:140`).
  So the register names an ADR as owner of a disputed figure the ADR does not
  discuss, does not carry the dispute, and does not carry the `decided_by`
  (*"M1, with a player and a manometer. Sets the panel gain range AND the ADC
  headroom."*). Nothing in `ROADMAP.md`'s M1 row names it either. **A disputed
  figure with an owner that is silent about it will not get decided.**

---

## F. Numbered items

### G11-34 — ADR 0001 says "Five further fixes" and then numbers six

`[repo] 0001:243–295`: *"**Five further fixes**, in descending order of value.
**The first four are wiring** and cost nothing but planning"*, followed by
items **1 through 6**. Item 4 is struck through and deleted (`:283–289`), so
the live count is five and the numbering runs to six — and "the first four are
wiring" includes the deleted one.

This matters because the corpus cites these by number and by two different
names: `key-chain-loom.md:58` "ADR 0001 **fix 1**", `:102` "fix 2", `:105`
"fix 3", `cluster-boards.md:77` "fix 3", `key-layout.yaml:152` "fix 6",
`bom.csv:35` "fix-6 fault", `bom.csv:30` and `key-chain-loom/bom.csv:2`
"ADR 0001 **item 1**". **All of them resolve correctly** — no renumbering has
happened. But the sentence stating how many there are has moved under the list,
which is one of the four recorded shapes in `CLAUDE.md`, and the next editor
who "fixes" the count by deleting item 4's number breaks seven citations at
once. The struck-through item must keep its number.

---

## G. Arithmetic and internal-consistency defects

- **G11-35** `[repo] 0013:60` *"**Fourteen chip pins of headroom**, against two
  before."* The table two lines up (`0013:42–53`) totals **18 of ~30**.
  `[calc] 30 − 18 = 12`. 14 is what `30 − 16` gives, and 16 is the pre-
  correction total: `0013:62–66` records that *"An earlier version of this
  table showed 14 pins and one shared host, and was wrong"* and adds the two
  SPI3 pins. The correction landed in the table and not in the sentence
  underneath it.

- **G11-36** `[repo] 0013:287` *"Worth revisiting only if the S3 turns out to
  struggle with loop determinism, which is not expected **at 13 pins and one
  job**."* The same ADR says 18 on the chip and 14 broken out. 13 matches
  neither.

- **G11-37** `[repo] 0001:116–117` *"Two extra pins against **sixteen of
  headroom**."* Three ADRs now give three different headroom figures for the
  same chip: 16 (0001), 14 (0013:60), 12 (`[calc]` from 0013's own table).
  `0008:87–90` gives *"roughly 30 usable with quad PSRAM"* against its own
  21-pin budget, i.e. ~9.

- **G11-38** `[repo] 0001:94–96` *"Bandwidth down the body is trivial: **six
  16-bit channels at 4kHz is ~576 kbit/s**."* `[calc] 6 × 16 × 4000 = 384
  kbit/s`. 576 kbit/s is 24 bits per channel. The authoritative figure is
  `0004:62` — six channels at 32-bit frames = 0.77 Mbit/s (see G11-24). Three
  numbers for one quantity across three ADRs.

- **G11-39** `[repo] 0004:282–287`:

  ```
  …which is harmless at 50 mA and is not at 290 mA:

  | Series R | Drop at 359 mA |
  |---|---|
  | 2.2 Ω     | 0.64 V |
  | 10 Ω      | 2.90 V |
  ```

  `[calc] 2.2 Ω × 359 mA = 0.790 V`, not 0.64. `10 Ω × 359 mA = 3.59 V`, not
  2.90. Both cells are `× 290 mA` exactly (`0.64/2.2 = 291 mA`;
  `2.90/10 = 290 mA`), and the prose above them still says 290 mA. The header
  was updated to `umbilical-current` and the cells under it were not — the
  fix reached the label and not the numbers.

- **G11-40** `[repo] 0009:163–189` — **two consecutive sections both headed
  `### Mass`**, giving different totals for the same instrument: the first
  (`:165–169`) puts 2.25 in at **~778 g** and 2.50 in at ~825 g; the second
  (`:179–186`) totals **~825 g** for the chosen envelope. The second table's
  first row is `| Aluminium top plate, **2 mm** | 157 |` — the plate thickness
  retired by `plate-thickness` = 1.20 mm, which `0009:64` states correctly
  sixty lines earlier. `[calc]` at 1.20 mm that row is ~94 g and the total is
  ~762 g. So: a duplicate heading, two contradictory answers, and the survivor
  is computed on a superseded figure.

- **G11-41** `[repo] 0014:55–56` *"Two data lines cost one extra GPIO, against
  roughly **17 broken out and 12 needed** on the real-time board (ADR 0007)."*
  `[repo] 0007:194` `| **Used** | **14 of 17** | spare: 3, 4, 33 |`, and
  `0013:53` *"**14 broken out**"*. 12 was the pre-UART0-console count
  (`0007:228–232` describes exactly that scenario as the one that was ruled
  out).

- **G11-42** `[repo] 0014:141–143` *"Note the same page's *Quiescent Current
  **2.1 mA*** reproduces ADR 0005's **123 mA** figure **exactly**."*
  `[calc]` the strips are `0.84 m at 60/m` = 50 LEDs (`0014:29, 132`);
  `50 × 2.1 mA = 105 mA`, not 123. `0005:158` gives 123 mA as the whole 12 V
  direct quiescent and `0005:234` calls the strip share *"roughly 120 mA"*. The
  agreement claimed as "exactly" is ~15 % out, and it is used to argue that the
  quiescent figure came from the datasheet while the working one did not.

- **G11-43** `[repo] 0003:258` *"Breath path goes from ~1.5 ms to **~2.6 ms**
  against a 5 ms target."* `[calc] 1.5 + 1.17 = 2.67` — correct against the
  1.5 ms table at `0003:19–27`, which the **same ADR** retires at `:34–39`:
  *"The digitised path comes to **~3.1 ms** against a 5 ms target… The old
  figure came from a table that left out the filter poles this design
  specifies, the sampling period, and the pneumatic restrictor."*
  `[repo] docs/reference/latency-budget.md:65` confirms
  `| **Total** | **~2.9–3.1 ms + restrictor** |`. The tube-cost section
  computes its headroom from the base the ADR already refuted 220 lines up.

- **G11-44** `[repo] 0006:141–142` *"Resolution goes from 153 µV/LSB on a 10 V
  span to **305 µV/LSB** on 20 V. That is **0.003 %** of full scale."*
  `[calc] 305 µV ÷ 20 V = 0.0015 %` (= 1/65536). 0.003 % is that figure taken
  against the 10 V span it just stopped using. Harmless to the conclusion,
  wrong as stated.

- **G11-45** `[repo] 0006:742–743` *"The −11.9 and −23.5 cents/octave figures
  **below** become historical."* Those figures are **above**, at `0006:534–535`.
  A reader following the pointer finds nothing.

- **G11-46** `[repo] 0010:174–177` ends a bullet mid-sentence:

  ```
  more than three. This line said "eight to ten" while the marker was four to six; both halves were
  corrected 2026-09-21. What is more than three.
  ```

  *"What is more than three."* is a truncated fragment. The arithmetic around
  it is right (`14 spare = 8 marker + 3 reserved switch + 3 free`, agreeing
  with `key-layout.yaml:145–153` and `figures.yaml:254–266`), but the sentence
  that states it does not finish.

- **G11-47** `[repo] 0001:340–341` *"So the allocation went from a superseded 6
  marker to 8 marker, 5 free → 3 free**, and the 3 that remain…"* — a stray
  closing `**` with no opener; the bold runs from an earlier fragment. Cosmetic,
  but it is in the sentence that records the marker-bit allocation change.

- **G11-48** (outside the ADRs, found while checking one) `[repo]
  config/figures.yaml:408` and `:423` — the `panel-height-budget` entry has
  **two `false_positive_note` keys**. In every standard YAML loader the second
  silently wins, so the note at `:408–413` (the one explaining why `0004:736`
  and `panel.md:20` legitimately narrate the retired numbers) is discarded at
  parse time. Worth a look from whoever owns `tools/check-staleness.py`.

### G11-49 — ADR 0005 offers two "equally valid" alternatives that would invalidate five BOM rows and three settled figures

Flagged to me by the coordinator as independently reported; **verified here against pinned blobs, not taken on report.**

`[repo, pinned] git show a4b80b1:docs/decisions/0005-power-architecture.md:336–339`:

> **LT1641-1CS8 (SO-8, 9–80 V) driving an external N-FET, with a sense resistor.**
> Note the suffix: **`-1` latches off and `-2` auto-retries**… **LM5069MM
> (MSOP-10) and LTC4210 (MSOP-8) are equally valid.**

That sentence was true when the choice was a package-policy survey. It is not
true now, because the entire load-switch design has since been dimensioned from
**LT1641-only** datasheet constants, all of them confirmed verbatim against one
banked document (`datasheets/discrete-and-power/LT1641.pdf`, MANIFEST row
`LT1641-1CS8` with SHA-256 `00aa5309…`):

| Design value | LT1641-only constant it comes from | `[repo, pinned]` |
|---|---|---|
| `C-GATE-LOADSW` **82 nF** | `I_GATE` = −5 / −10 / −20 µA, p.2 | `figures.yaml:504` |
| `C-TIMER-LOADSW` **10 µF** | TIMER 3 µA down / 80 µA up = 77 µA net into a **1.233 V** threshold, p.8 | `figures.yaml:488` |
| `R-FB-HI / R-FB-LO` **35.7 k / 5.11 k** | `V_FB` = 0.5 V for full sense threshold **and** `V_FBH` = 1.313 V for PWRGD release, *set by the same divider* | `figures.yaml:513` |
| `R-ILIM` **50 mΩ** | sense threshold **39 / 47 / 55 mV**, p.2 | `0005:282` |
| foldback floor **240 mA** | 47 mV at `V_FB` ≥ 0.5 V falling linearly to **12 mV** at `V_FB` = 0, p.5 / Fig. 7 p.9 | `figures.yaml:514, 516` |
| the `-1` vs `-2` argument | an ADI suffix convention | `0005:337–338` |

And five BOM rows name the part in their own text `[repo, pinned]
git show a4b80b1:hardware/bom.csv`:

- `U-LOADSW,module,**LT1641-1CS8**`
- `R-FB-HI … "Upper leg of **the LT1641 FB divider**, umbilical +12V to FB"`
- `R-FB-LO … "Lower leg of **the LT1641 FB divider**"`
- `R-GATE-SER … "Series gate resistor between **LT1641 GATE** and the N-FET gate"`
- `C-GATE-LOADSW`, `C-TIMER-LOADSW` — both `selected`, both sized above

Neither alternative carries that pin set: the LTC4210 has no `FB` foldback pin
and no `PWRGD` in this form, so `R-FB-HI/R-FB-LO` have nothing to divide and
the 0.381 ratio `figures.yaml:513` calls *"fixed by the part, not by the
divider"* does not exist; the LM5069's thresholds and timer currents are
different numbers entirely. **Swapping to either "equally valid" part
invalidates 82 nF, 10 µF, 35.7 k/5.11 k, 50 mΩ and the latch-vs-retry
reasoning at once** — and would silently re-open G11-1, since the ramp
arithmetic is `I_GATE`-specific.

`[test] grep -rn "LM5069\|LTC4210"` across `docs/decisions`, `hardware`,
`config`, `docs/reference`, `README.md`, `ROADMAP.md` (tree clean, verified
`== a4b80b1` for all those paths) → **exactly one hit, this sentence.** Neither
part is banked; `datasheets/MANIFEST.csv` has no row for either. So this is a
claim of equivalence with no document behind it, in the ADR that owns the
decision, pointing at parts nothing else in the corpus has ever costed.

**This is the same shape as G11-1 and belongs with it.** Both are ADR 0005
sentences that were written before the LT1641 datasheet was banked and that the
banked datasheet has since made false. Fixing G11-1 without fixing this one
leaves the next reader free to "solve" the ramp problem by reaching for
LM5069MM — which the ADR currently tells them is equally valid, and which would
discard every number on the page.

---

## Provenance addendum — the working tree moved during this wave

After my first pass I was told that another slice had been editing corpus files
**and `tools/check-staleness.py`** in place, uncommitted, while the read-only
slices worked, and that the staleness hook was seen flipping
PASS → FAIL → PASS → FAIL. I re-verified rather than assuming my exposure was
nil. What I did:

**1. Tree state, stated rather than assumed.** `[test] git status --short` at
the time of the re-check: clean apart from five untracked slice reports under
`docs/review/2026-09-22-goal-verification/` (mine among them). `[test] git diff
--stat a4b80b1 -- docs/ config/ hardware/ README.md ROADMAP.md firmware/
tools/` → the only entry is this wave's `README.md` (+81). So `tools/` is at
`a4b80b1` too, and **every corpus path I cite is byte-identical at `a4b80b1`,
`25cc740` and the working tree.**

**2. Every load-bearing quote re-checked against the pinned blob.** `[test]`
28 fixed-string greps of `git show a4b80b1:<file>`, one per finding that quotes
text. **All 28 present.** Three appeared absent on the first run — G11-13,
G11-36, G11-38 — and all three were **my own hard-wrap error**, the trap
`CLAUDE.md` §2 documents: the quoted phrase spans a line break in the source,
so a fixed-string match against the raw file cannot fire. Re-running against a
line-joined stream (`tr '\n' ' '`) found all three, and I confirmed the raw
context by line number (`0009:203–204`, `0013:286–287`, `0001:94–95`). Worth
recording that the trap catches a *reviewer* verifying a finding just as
readily as an author writing a pattern.

**3. The two checker-dependent findings were made checker-independent.**
G11-6 and G11-29 originally cited the PreToolUse hook's *"PASS no live stale
values"* — which is precisely the output that was observed flipping, so it was
worthless as evidence. I replaced it with a direct comparison that runs no
tool: parse the `forbidden` lists out of `git show a4b80b1:config/figures.yaml`
and string-match them against the line-joined pinned ADR text. `[test]`

| figure | offending text present at `a4b80b1`? | patterns | any that fire |
|---|---|---|---|
| `panel-height-budget` vs `0004` ("The 97 mm above") | yes | 12 | **none** |
| `key-scan-current` vs `0009` ("10 kΩ, 100 Ω and 10 nF per switch position") | yes | 3 | **none** |
| `key-press-time` vs `0009` (same text) | yes | 12 | **none** |

Both findings now rest on pinned text and the pinned pattern lists alone. They
would stand even if `check-staleness.py` were deleted.

**4. What this does and does not settle.** It settles that the *text* I
reviewed is the frozen text. It does **not** settle whether some intermediate
read of mine hit a modified file and I formed a wrong impression I then failed
to quote — findings that rest on *absence* are the exposed ones. The two I
would treat as weakest on that basis, and how I re-grounded them:

- **G11-16** (twelve "bonded body" survivals) — re-derived from pinned blobs;
  every one of the twelve line references reproduces.
- **G11-27** ("no gaps, no stubs") and **G11-25** (no ADR carries
  `Superseded`) — `[test] grep -n "^\*\*Status:\*\*" docs/decisions/*.md`
  returns fourteen files, 0001–0014 consecutive, **all `Accepted`**, run on a
  tree verified clean at that moment.

**Findings resting on pinned reads:** G11-1 through G11-16, G11-20, G11-24,
G11-25, G11-27, G11-29, G11-33 through G11-47, and G11-49 — i.e. every finding
that quotes ADR text. **Not re-pinned**, because they are arithmetic over
figures already pinned above and re-checking them adds nothing: G11-17 through
G11-19, G11-21 through G11-23, G11-26, G11-28, G11-30 through G11-32, G11-48.

---

## What I could not check

- **The LilyGO breakout pin count** (G11-22). `pdftotext` is unavailable as the
  brief says; `pymupdf` extracts only Altium title-block boilerplate from
  `LILYGO-T-DISPLAY-S3-AMOLED-SCHEMATIC.pdf` — the net labels are vector.
  Settling it needs `page.get_pixmap(dpi=150)` and an eye on the header blocks.
- **OPA2197 output swing under the real load.** ADR 0003 already flags this
  itself (`0003:533–549`: *"the swing figure that applies here is not obviously
  any of the three tabulated rows… **Re-argue it against the load, or drop the
  claim**"*). I confirmed the flag is present and did not re-derive it; it is an
  open item the ADR owns honestly, not a hidden defect.
- **`ref5050-grade` (disputed), `dig-gnd-topology` (disputed),
  `matrix-led-current` (blocked).** All three are correctly marked in the
  register and correctly narrated in ADR 0003:483–498 / 0014:379–428. I did not
  try to decide them.
- **Page-level re-reads of MPXV4006DP, INA828, DAC8568, OPA2197 and the Gateron
  drawing.** I verified the arithmetic of every figure derived from them and
  confirmed each cited file is banked with a MANIFEST SHA-256, but I read
  datasheet pages directly only for the KS-33 height question (G11-20, via
  `ks33-geometry.md`'s own reading) and the LilyGO attempt. Another slice
  re-reading the banked PDFs against the ADR prose would be worth having; the
  three figures `CLAUDE.md` §3 records as having moved that way all came from
  exactly this kind of check.
- **Whether the G11-16 "bonded body" arguments still hold on the
  "expensive, not impossible" reading.** That is a judgement per argument, not
  a check. I report that none of the twelve says which it is.

---

## Summary

49 numbered findings. The ones I would fix first, in order:

1. **G11-1 with G11-49** — ADR 0005's load-switch section. G11-1 is the only
   finding where an **Accepted** ADR, a **settled** register figure and a drawn
   schematic all disagree and the ADR knows it. G11-49 is the sentence three
   lines below it that would let someone "fix" G11-1 by changing the part and
   discarding every number on the page. They are one edit, not two.
2. **G11-29** and **G11-6** — two live stale values sitting inside ADRs while
   `check-staleness.py` reports PASS, both missed by the spelling of the
   pattern rather than by its absence. G11-29 is in the document that *owns*
   the figure.
3. **G11-24** — one decision, two ADRs, two different numbers, with ADR 0003
   holding the retired count inside the sentence that exists to correct it.
4. **G11-20** — a dimension asserted to a vendor drawing that does not carry
   it, with a clearance conclusion spent against it.
5. **G11-5**, **G11-7**, **G11-9**, **G11-16** — decisions ADR 0013 and ADR
   0009 reversed that the other ADRs still instruct a builder to follow.

The pattern across almost all of them is the one `CLAUDE.md` names: the
correction landed where the editing was happening — the table, the label, the
schematic page — and not where the reader looks: the Decision paragraph, the
Consequences list, the sentence under the table.
