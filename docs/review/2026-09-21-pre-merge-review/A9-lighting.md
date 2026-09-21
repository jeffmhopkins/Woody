# A9 — Lighting, and every route by which it reaches an analog output

**Wave:** 2026-09-21 pre-merge review
**Slice:** the LED strips, the 8×8 matrix, their power and data paths, and every
coupling route from LED switching to an analog output.
**Cold:** nothing under `docs/review/**` was read, including this directory's own
`README`. No prior wave's findings informed anything below.
**Status of everything here:** claims, not corrections. Nothing was fixed.

## Provenance key

`[repo] path:line` — read in this repository.
`[datasheet] doc, where` — read out of a **banked** document in `datasheets/`,
by extracting the PDF's own text or its net labels with coordinates. Every
`[datasheet]` claim below was extracted in this session, not recalled.
`[calc]` — arithmetic shown.
`[from memory]` — general knowledge, flagged as the weakest class.

---

## What was verified by hand against banked documents

Before the findings, because several findings depend on these and because three
corpus claims **passed**.

| # | Claim in the corpus | Verdict |
|---|---|---|
| V1 | WS2815 `V_IH = 0.7 VDD` in a table whose header declares `VDD = 4.5…5.5 V` | **CONFIRMED** |
| V2 | WS2815 pin 6 is `BIN`, pin 5 is `GND` | **CONFIRMED** |
| V3 | WS2815 bypass latch is sticky until power-off | **CONFIRMED, verbatim** |
| V4 | WS2815 PWM/refresh rate ~2 kHz | **CONFIRMED** |
| V5 | The Waveshare board carries 64 × `WS2812B-0807` | **CONFIRMED, independently** |
| V6 | `B5819WS` thermal arithmetic (435 mA / 283 mA) | **ARITHMETIC CONFIRMED** |
| V7 | "All 64 LEDs draw through one `B5819WS`" **in this instrument** | **REFUTED — see A9-01** |
| V8 | The `ME6217C33M5G` is a second limit on matrix LED current | **REFUTED — see A9-02** |

**V1** `[datasheet] datasheets/led/WS2815.pdf` (Worldsemi V1.1, p.3): the
section head reads *"Electrical Characteristics ( TA=-20~+70°C, **VDD=4.5~5.5V**,
VSS=0V )"* and the row reads *"High-level Input | V_IH | 0.7VDD | … | V |
D_IN , SET"*. `[calc]` 0.7 × 4.5 = 3.15 V, 0.7 × 5.5 = 3.85 V. The corpus's
reading is right and the 74AHCT125 on 5 V clears it.

> **The argument can be made stronger than the corpus makes it, from the same
> page.** `[datasheet]` the pin-function table reads *"1 VCC — IC POWER SUPPLY,
> Suspended or connected with a filter capacitor to GROUND"* and *"2 VDD — LED
> POWER SUPPLY, connect to +12V"*. So the part has an **internally generated IC
> rail on pin 1** that is a separate net from the 12 V LED supply, and
> 4.5–5.5 V is that rail's range. The Electrical Characteristics header has the
> symbol wrong (`VDD` where the part's own pin table says `VCC`), which is also
> why Absolute Maximum Ratings is garbled — it gives *"Logic input high voltage
> V_I : VDD−0.5 ~ VCC+0.5 V"*, a range that runs backwards if `VDD` means
> +12 V. `led-strip-drive.md:70-78` calls this "muddles it further"; it is
> better than that. **Pin 1's existence is what proves there is a low-voltage
> rail for the threshold to be referenced to**, and it closes the question
> without relying on "the conditions line governs". Worth adding, because the
> current argument is one sentence away from being reversible by the next
> reader who notices the abs-max row.

**V2** `[datasheet] WS2815.pdf` p.3 pin table: *"5 GND GND Data & Power
Grounding"*, *"6 BIN BIN Backup Control data signal input"*. The corpus's
"L1's pin 6 (`BI`) to pin 5 (`GND`)" `[repo]
hardware/carrier/led-strip-drive/led-strip-drive.md:80-83` names the right pins.
The recommended-application-circuit **figure itself is a raster with no text
layer** — I confirm that independently (the page's images are all `DCTDecode`),
so the figure could not be re-read here, and the page's own instruction to
"confirm visually against the PDF before the loom is crimped" still stands.

**V3** `[datasheet] WS2815.pdf` p.1: *"…make the BIN in state of receiving
signal until restart after power-off."* Quoted correctly at
`led-strip-drive.md:92-93`.

**V4** `[datasheet] WS2815.pdf` p.1: *"Refresh Frequency updates to 2KHz"* — so
the "~2 kHz PWM rate" that sizes `C-STRIP-BULK` `[repo]
0014-lighting.md:120-123` and that `key-chain-loom.md:155` relies on is a
datasheet figure, not an estimate. Nobody says so; both cite `[repo] 0004`.

**V5** `[datasheet] datasheets/mechanical/WAVESHARE-ESP32-S3-MATRIX-SCHEMATIC.pdf`:
the schematic's own component annotations contain `Comment: WS2812B-0807`
**exactly 64 times**, and the placed net labels give 64 `VDD`/`DIN`/`DOUT`/`VSS`
symbol groups. Third independent confirmation of `0014-lighting.md:358-365`.

---

## Findings

Indexed by node or BOM reference. Severity is my judgement of what it costs if
it ships unchanged.

---

### A9-01 — Node `VCC_5V` / `D-USBOR` / `D1 (B5819WS)` — **MAJOR**

**The corpus's new headline constraint on the matrix is wrong for the way the
instrument actually powers that board.**

`config/figures.yaml:524` (`matrix-led-current.supersedes_the_constraint`) and
`docs/decisions/0014-lighting.md:390-399` both state: *"THE 1 A R-78E5.0 IS NOT
WHAT STOPS THE MATRIX FIRST. All 64 LEDs draw through one `B5819WS` Schottky in
SOD-323"*, and ADR 0014 instructs *"Rewrite the argument against the real
constraint"*.

`[datasheet]` I read the banked schematic's net labels with coordinates. The
power entry is:

```
USB-C ── VBUS ──►|── VCC_5V ──┬── 64 × WS2812B-0807  (every VDD on VCC_5V)
                  D1          └── U49 ME6217C33M5G VIN ──► 3V3
               B5819WS
```

- `D1` `B5819WS`: pin 1 side carries the label `VBUS` (x 99.3, y 395.8), pin 2
  side carries `VCC_5V` (x 50.1, y 393.4). Current flows VBUS → VCC_5V.
- **`VBUS` appears at exactly four places in the whole schematic** — the USB-C
  connector and `D1`'s anode. Nowhere else.
- The 64 LED `VDD` pins and the LDO's `VIN` are all on `VCC_5V`.
- The board's header rows are **not drawn as a component** in this schematic, so
  the "5V" header pin's net is not printed. But since `VBUS` has no other node,
  the 5 V header pin can only be `VCC_5V`.

`[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md:56-60`
draws the instrument's feed as `R-78E5.0 A ──▷|(D-USBOR)── dev board 5V pin`,
and its component table calls `D-USBOR` *"one per regulator output … the OR node
is a dev-board pin"*. **That OR node is `VCC_5V`, downstream of `D1`.** So in
the finished instrument, matrix LED current comes from buck A through
`D-USBOR`, and `D1` is reverse-biased and carries none of it.

Consequences, all of which the corpus currently has backwards:

1. **The R-78E5.0 and `D-USBOR` are the binding path in the instrument**, which
   is what ADR 0014 said *before* the correction. The correction is right about
   the part number and wrong about the topology.
2. **`D1` binds on USB power** — which is E1, E5 (USB MIDI), every flash, and
   every bench session. That is where the 283–435 mA matters, and it is exactly
   where the ADR's firmware clamp is least likely to be running.
3. **With USB plugged in *and* the carrier powering the board, the two sources
   are within tens of millivolts of each other and will share.** `[calc]`
   `D-USBOR` is an SS14 (`[repo] power-entry-instrument.md` component table);
   at 600 mA an SS14 drops ≈0.45 V, giving `VCC_5V` ≈ 4.55 V from a 5.00 V buck.
   `D1` at the same current drops ≈0.5 V from a 5.00 V VBUS, giving ≈4.50 V.
   **A ~50 mV difference across two Schottkys in parallel is not an OR, it is a
   divider** — a meaningful fraction of the matrix current can flow through the
   200 mW diode whenever USB is connected, which is precisely the configuration
   used for flashing and for USB MIDI in a body that cannot be opened.

**Recommend:** re-derive the constraint against `D-USBOR` + R-78E5.0 for the
instrument case and against `D1` for the USB case, and state that the two
sources share rather than OR cleanly. Do not delete the `B5819WS` analysis — it
is correct and load-bearing for E1/E5.

---

### A9-02 — `matrix-led-current` / `U49 ME6217C33M5G` — **MINOR**

`config/figures.yaml:524` and `0014-lighting.md:395-399` continue: *"Behind it,
the `ME6217C33M5G` LDO's printed 800 mA is 'guaranteed by design' … and derates
to ~250–500 mA"*, presented as a second limit on **matrix LED current**.

`[datasheet]` the LDO's `VIN` label is `VCC_5V` (x 45.4, y 260.2) and its `VOUT`
is `3V3`. It sits **in parallel with** the LED array on `VCC_5V`, not in series
with it. Nothing the matrix draws passes through the LDO.

The LDO derating is a real constraint — on the **3V3 rail** that runs the
ESP32-S3 and the QMI8658C — and it is worth keeping for that. It is not a
constraint on the matrix. As written it will be read as one.

---

### A9-03 — Node `LED_DIN` (matrix data) — **MAJOR, and nobody has read this part of the banked schematic**

The corpus says *"One GPIO per strip is the whole interface"*
(`0014-lighting.md:96-99`) and, for the matrix, only that it is *"64
`WS2812B-0807` parts on GPIO14"* (`[repo] docs/decisions/0007-imu-selection.md:176`).

`[datasheet]` the schematic shows the matrix data input is **not driven by
`IO14` directly**. Between them sits a discrete level-translator:

```
        3V3                    VCC_5V
         │                       │
      [R4 2.2K]              [R3 4.7K]
         │                       │
 IO14 ───┴── source   Q1   drain ─┴─── LED_DIN ──► U8 DIN (first of 64)
                 DMG1012T-7 (gate to 3V3)
```

Label coordinates: `VCC_5V`(553.9,173.4) → `R3 4.7K`(563.5,161) →
`LED_DIN`(561.2,152.2) at Q1 pin 3; `3V3`(600.3,173.4) → `R4 2.2K`(605.7,161) →
Q1 pin 2 at `IO14`(612.2,152.2); `Q1 DMG1012T-7`(576.1,145.9). This is the
standard MOSFET bidirectional translator.

Three things follow that no document in the corpus states:

1. **The matrix's reset behaviour is not the strips' reset behaviour.** The
   whole argument for `R-LED-PD` — *"On reset GPIO1 and GPIO2 are
   high-impedance … an AHCT input floating near its threshold does not sit
   still … that is random pixel data"* `[repo] led-strip-drive.md:45-56` — does
   **not** transfer to the matrix, because `R4` (2.2 kΩ to 3V3) and `R3`
   (4.7 kΩ to `VCC_5V`) hold `LED_DIN` **high** when `IO14` floats. A static
   high is neither a WS281x bit nor a reset (reset is a low > 280 µs
   `[datasheet] WS2815.pdf` p.1, same protocol family). The matrix will not
   clock random data during the bootloader window.
2. **So `0014-lighting.md:404-408`'s "the matrix is physically *on* the MCU that
   resets, so it latches too, and it is the more visible of the two" is right
   about latching a previous frame and wrong by implication about the hazard
   class** — the strips can be *given* garbage through a floating input; the
   matrix cannot, absent `R-LED-PD`. The blank-at-boot rule is still correct for
   both; the justification differs.
3. **There is no hardware fix available for the matrix in any case**, and the
   corpus should say so where it says the opposite is cheap: `IO14` is **not
   broken out** (`[repo] 0007-imu-selection.md:181` — broken out is GPIO 1–7,
   33–40, 43, 44), so no pull-down can be added at the carrier. The vendor's
   `R4` is the only thing there is.

**Recommend:** record the `Q1`/`R3`/`R4` stage on the carrier page or ADR 0014.
It is in a banked document, it changes a stated failure mode, and it is the kind
of thing the next reviewer will otherwise re-derive from "one GPIO is the whole
interface", which is true of the strips and false of the matrix.

---

### A9-04 — `LED-SIDE` — the strips' full-white current has no document, and the banked datasheet disagrees with it by ~2.2× — **MAJOR**

`[repo] docs/decisions/0014-lighting.md:130-132`:

| Density | Full white | Single hue, full | Single hue, 40% |
|---|---|---|---|
| 30/m (25 LEDs) | 0.50 A | 0.17 A | 0.07 A |
| 60/m (50 LEDs) | 1.01 A | 0.34 A | 0.13 A |

No provenance mark on the table, and no derivation anywhere in the corpus.
`[calc]` it implies **20.2 mA per LED at 12 V for full white** (1.01 A / 50).

`[datasheet] WS2815.pdf` p.3, "LED Characteristics": *"Quiescent Current 2.1 mA
… RGB Channel Constant Current 15 mA"*. `[calc]` full white = three channels
sinking 15 mA each from the 12 V rail = **45 mA/LED**, plus 2.1 mA quiescent.
50 LEDs → **≈2.35 A, ≈28 W**, against the ADR's 1.01 A / 12.1 W. **Ratio 2.3×.**

Two things make this hard to dismiss:

- **The corpus already uses the other number from the same table and gets it
  right.** `[repo] docs/decisions/0005-power-architecture.md:157` gives 123 mA of
  12 V-direct draw at quiescent with LEDs blanked; `[calc]` 50 × 2.1 mA =
  105 mA plus the analog rail. The *quiescent* figure is datasheet-consistent
  and the *full-scale* figure is not, which is the signature of two different
  sources.
- **The strip itself has a `BLOCKED` MANIFEST row.** `[repo]
  datasheets/MANIFEST.csv:99` — *"WS2815 LED strip … STRIP GEOMETRY NOT
  ESTABLISHED"*. So there is no banked document for the assembled tape that
  could justify a lower per-LED figure (some tapes derate, and `[from memory]`
  vendor listings for 60/m WS2815 commonly quote 18 W/m, which would be
  ~25 mA/LED — still above the corpus's 20.2 and well below the IC's 45).

This is the same failure the matrix section just went through — a per-LED
current taken from somewhere other than the part's own document — on the
**other** light source, and it is currently unflagged.

Everything downstream moves if it is wrong, and moves the *wrong way*:
`[calc]` "Both strips full white at 60/m | 12.1 W | ~36 K"
(`0014-lighting.md:153`) becomes ≈28 W and ≈84 K; ADR 0005's "Clamp fails,
strips latched full white" row (`:161`, 1023 mA on 12 V direct) becomes
≈2.4 A, which changes what the module's load switch has to survive.

**Recommend:** either bank a strip document or mark the table as an estimate
with its source, and add the strips to the E1/E9 current measurement — which is
currently scoped to the matrix only.

---

### A9-05 — `matrix-led-current` — the blocked figure's consumers, one by one — **MAJOR**

The task was to check whether each downstream consumer is honest about resting
on an unmeasured estimate. Result: **the register entry is exemplary, the owner
ADR is not, and one consumer treats the figure as known.**

| Consumer | Honest? |
|---|---|
| `config/figures.yaml:516-526` | **Yes.** `value: BLOCKED`, three candidates with the wrong-part one named, `decided_by` a bench measurement, `blocked_on` a MANIFEST row. This is the model. |
| `hardware/carrier/power-entry-instrument/power-entry-instrument.md:20` | **Yes.** Cites `matrix-led-current` by name in the Interfaces table and restates nothing. Rule 1 followed exactly. |
| `ROADMAP.md:189` | **Yes.** *"the estimate is still an estimate"*, brackets the surrogates, says E1 measures it. |
| `docs/decisions/0007-imu-selection.md:207-213` | **Yes**, for idle — *"an estimated ~50 mA"*, *"Measure the idle draw at E1"*. |
| `docs/decisions/0014-lighting.md:415-428` | **Partly.** The 960 mA table survives under a warning banner that says it is wrong. |
| **`docs/decisions/0014-lighting.md:159-163`** | **NO — see below.** |

**The one that is not honest.** `0014-lighting.md:159-163`, in the *Power
budget* section:

> **The instrument's own regulator, which is a 1 A part.** The matrix hangs on
> the R-78E5.0-1.0 alongside both dev boards, and at full field it asks for
> 960 mA on its own.

No flag, no hedge, stated as fact. The warning banner is at line 358 — **199
lines further down, in a different top-level section**. A reader arriving at the
power budget (which is what the section is for) gets the wrong number with no
warning at all. This is exactly the pattern CLAUDE.md opens with: *"Fixes land
where the editing is happening; they do not land where the reader looks."* The
correction landed in the matrix section because that is where the correcting was
done.

**And the same sentence carries a second, independent staleness.** *"alongside
both dev boards"* and, at `:434-437`, *"It shares the 1 A R-78E5.0 with both dev
boards, which take roughly 330–400 mA between them, so a full-field matrix would
ask for about 1.36 A from a 1 A part."* There is no shared regulator any more:
`[repo] docs/decisions/0005-power-architecture.md:183-195` gives the power tree
as **buck A** = real-time board + matrix + level shifter, **buck B** = display
board, and `:206-211` states *"Two bucks, not one"*; `[repo] hardware/bom.csv:2`
carries `U-BUCK` at **qty 2**, *"ONE PER DEV BOARD"*. The display board's
150–250 mA is not on the matrix's regulator. **The 1.36 A arithmetic sums a load
that no longer exists on that part.**

Both defects are in the sentences that justify the brightness cap, and the cap
is the one thing in this ADR that is deliberately not configurable.

**Recommend:** ADR 0014's power-budget section needs the banner's conclusion
brought *up* to it, and the "both dev boards" load re-split per buck. Note that
`power-entry-instrument.md:86-99` already flags the missing split as an open
item — *"ADR 0005's load table has one 5 V column and the two-regulator decision
needs it split per buck. That split is not written anywhere and it is what sizes
both parts."* This finding is the same hole seen from the lighting side.

---

### A9-06 — The ~3 W clamp does not protect the thing the corpus now says is fragile — **MAJOR**

`[repo] 0014-lighting.md:172-176`: *"A single instrument-wide lighting budget of
~3 W … enforced in firmware before any write."*

`[calc]` If the matrix takes the whole budget: 3 W ÷ 5 V = **600 mA** on
`VCC_5V`. If it takes half: 300 mA.

Against that:
- `D1 B5819WS` (the USB-powered case, A9-01): **283 mA at a 60 °C interior,
  435 mA at 25 °C** `[calc]` verified from `[repo] figures.yaml:524`'s own
  inputs — 0.2 W ÷ 0.46 V = 435 mA; (125 − 60) °C ÷ 500 °C/W = 0.13 W ÷ 0.46 V
  = 283 mA, which also reproduces `P_D` = 200 mW at 25 °C exactly, so the
  arithmetic and the implied `T_j(max)` = 125 °C are self-consistent.
- Waveshare's own wiki warning, quoted at `0014-lighting.md:409-412`, that high
  brightness causes *"a rapid temperature increase, which can result in damage
  to the board"*.

**So the clamp as specified permits about 2× what the dev board's own power path
passes on USB, and the ADR that discovered this did not change the clamp.** It
says *"the brightness cap is right and its justification should change"* — but a
cap sized on a whole-instrument thermal argument has no reason to land below a
per-device limit it was not sized against. It happens not to, by 2×.

**Recommend:** the clamp needs a **per-device sub-limit on the matrix**,
expressed as a current on `VCC_5V`, in addition to the shared thermal budget.
Note that ADR 0014 explicitly rejected per-device caps (`:439-442`, *"a
per-device cap cannot see that both are drawing at once"*) — that reasoning is
sound for the *thermal* budget and does not apply to a component rating. Both
are needed; they are different failures, in the same way the ADR itself argues
the firmware clamp and the load switch are different failures.

---

### A9-07 — The 3 K/W thermal constant is derived from a power figure its own power ADR contradicts — **MAJOR**

`[repo] 0014-lighting.md:146-148`:

> The existing electronics dissipate roughly 5 W for an interior rise of
> 10–20 K, so call it **~3 K per watt**.

`[calc]` (10…20 K) ÷ 5 W = 2–4 K/W → "~3".

But `[repo] docs/decisions/0005-power-architecture.md:157-161` gives the body
heat column as **2.4 W quiescent (booted, radio off, LEDs blanked)**, 4.1 W at
typical play *including* lighting, 6.5 W at clamp-legal worst. The "existing
electronics" with the lights off are **2.4 W, not 5 W**.

`[calc]` On ADR 0005's own number: (10…20 K) ÷ 2.4 W = **4.2–8.3 K/W**. Then:

| Lighting state | ADR 0014's rise | Recomputed at 4.2–8.3 K/W |
|---|---|---|
| Realistic use, ~1.5 W | ~4 K | 6–12 K |
| **The ~3 W clamp** | **~9 K** | **13–25 K** |
| Both strips full white, 12.1 W | ~36 K | 51–100 K |

The clamp is sized to cost "roughly 9 K … inside what the design already
tolerates". On the power ADR's numbers it costs 13–25 K, which is not obviously
inside anything — the interior already runs 10–20 K up, the acrylic bond's
service limit is named as a concern at `:155-158`, and `[repo]
docs/decisions/0003-breath-sensing-path.md:638` prices a 20 K rise at 23 mV out
of 10 V on the breath jack.

Two further weaknesses in the same two lines, both structural:

- **`10–20 K` is an ownerless figure cited in at least eight corpus files** —
  `[repo] 0003:202`, `0003:243`, `0003:638`, `0005:312`, `0006:278`, `0009:531`,
  `0001:212`, `key-switch-network.md:118`, `power-entry-instrument.md:97`,
  `0007:210` — and it is **not in `config/figures.yaml`**. It is exactly the
  shape rule 1 exists for: one quantity, restated ten times, owned by nobody. It
  is also the input to a constant (3 K/W) that sizes the clamp that sizes ADR
  0005's load table that sizes both bucks.
- **The derivation is circular in direction.** 10–20 K is an estimate of the
  rise *including* whatever lighting was assumed when it was written; dividing
  it by an electronics-only power to get K/W and then multiplying by lighting
  power double-counts.

**Recommend:** register `interior-temperature-rise` as a tracked figure with
`status: blocked` on the M8 soak (ROADMAP already schedules it at `:192`), and
restate 3 K/W as what it is — a number with an inconsistent numerator and
denominator. The conclusion "the clamp is thermally generous" may not survive,
and it is better to find that on paper than at M8.

---

### A9-08 — ADR 0014 contradicts its own constant-current rule in two places — **MAJOR (semantic; no grep finds this)**

`[repo] 0014-lighting.md:520-527`, the rule that ADR 0006 leans on:

> **Animate by moving light, not by changing how much of it there is.** Render a
> dot, a bar or a field whose *total current* is held constant, and move or
> recolour it. Fades, pulses and **whole-field brightness sweeps** modulate the
> supply that pitch is referenced to.

Against that, in the same document:

1. **`:325`, the matrix render-mode list**, offers as a configurable option:
   *"Level bar, 2-D dot against a captured zero, centre bloom, **whole-field
   brightness**, glyph"*. Whole-field brightness is named in the rule as the
   thing not to do. Centre bloom modulates lit area, i.e. current. Level bar
   modulates lit area. **Three of the five render modes violate the rule**, and
   the surface is explicitly user-assignable from the display and the web app.
2. **`:420-428`, the matrix current table**, enumerates the expected operating
   states as +5 mA (one dot), +10 mA (eight-pixel bar at 25 %), +160 mA (full
   field at 50 %) — **a 30× range of total current presented as normal use**,
   in a document whose grounding section requires total current to be constant.

The rule is also in tension with the default assignment itself: a breath-driven
level bar is *defined* by the lit area tracking breath. The ADR's proportional
scaling (`:186-188`) makes a growing bar *dimmer*, which could be made to hold
current constant — but nothing says that is what proportional scaling is for,
and the arithmetic is never shown.

This matters more than a wording inconsistency because **ADR 0006 counts the
rule as one of its two free fixes for the pitch jack**
(`[repo] 0006-cv-channel-allocation.md:657-660`) and therefore does not treat
the remaining coupling in hardware.

**Recommend:** decide which it is. Either the rule is absolute — in which case
the render-mode list needs "whole-field brightness" removed or gated to
no-note-sounding, and the current table needs to show constant totals — or it is
advisory while a note sounds, in which case ADR 0006 should not be counting it
as a fix.

---

### A9-09 — The coupling routes, enumerated — and the count in two documents is stale — **MAJOR**

Task item 2. Every route I can identify from LED switching to an analog output,
with what the corpus does about it.

| # | Route | Corpus: quantified / fixed / left |
|---|---|---|
| R1 | Instrument `PWR_GND` shared with the breath sense return | **Fixed in hardware.** `AGND` is a separate umbilical conductor and a separate sense return (ADR 0003); `0014:499-503` prices the alternative at "a 34 mV ground offset that moves with the animation". |
| R2 | Umbilical `+12 V` IR drop from strip current, reaching the instrument's analog rail | **Left, and arguably fine.** `REF5050` + `OPA2197` PSRR sit between it and the sensor. Nowhere quantified against LED current specifically. |
| R3 | Module offset-reference divider on the bare rail | **Quantified (~22 cents p-p) and FIXED in hardware** — divider moved to `VREFOUT`, `[repo] 0006:582-607`. |
| R4 | Shared `1N5817` between the module's analog rail and the umbilical feed | **REFUTED**, `[repo] 0006:613-640`: *"five orders of magnitude below the smallest other term"*. `D-REVPOL` still goes to three, for other reasons. |
| R5 | The module's internal ground/pour | **Quantified (5.7–7.2 cents), NOT fixed**, measured at E6/E9. |
| R6 | The rack's shared bus ground | **Quantified (~4.8 cents), NOT fixed**, measured at E6/E9. |
| R7 | Magnetic/capacitive coupling in the body loom (strip power and 5 V data beside the key chain) | **Partly addressed, not quantified** — a ground return per clocked signal (`key-chain-loom.md:133-141`), `R-LED-SER` damping at the source, and a 54 dB pole at the 800 kHz data rate (`key-switch-network.md:104`). No analog signal is in the body (ADR 0003), so there is no analog victim here. |
| R8 | Umbilical pair-to-pair crosstalk: `+12V`/`PWR_GND` (pins 3,6) beside `BREATH`/`AGND` (pins 1,2) over 2 m | **NOT enumerated anywhere.** See below. |
| R9 | The module's own panel LED on the `+12 V analog` rail | **NOT enumerated anywhere.** See A9-10. |

**On R8.** `[repo] config/figures.yaml:220` (`umbilical-pinmap`) puts the power
pair and the breath pair in the same Cat5. Strip current is the largest and
fastest-switching load in the instrument and it modulates at the 2 kHz PWM rate
`[datasheet]`, in a pair running parallel to the analog pair for 2 m. The corpus
handles this implicitly and well — both are twisted pairs on T568B, the breath
link is differential with a 73 dB common-mode floor set by the 1 MΩ bias pair
`[repo] breath-sense-link.md:83`, and `latency-budget.md:126` schedules *"scope
the breath jack while sweeping display brightness, LED animation and a WiFi
burst"*. But **no document names the route**, and the T568B pairing is what makes
it safe. If anyone ever re-pins the umbilical for another reason, nothing in the
corpus records that pins 3/6 must stay a pair *because of the LEDs*.

**And the count is stale in two places.** `[repo] 0014-lighting.md:513-517`:
*"**Four** independent routes were found … ADR 0006 fixes **the two large ones**
in hardware."* `[repo] ROADMAP.md:200`: *"**Four** routes put LED current onto
pitch and **two are fixed in hardware**."* One of those four (R4) was **refuted
in ADR 0006 itself** — so there are three routes, one hardware fix that matters
(R3), and one hardware change (`D-REVPOL` ×3) retained for reasons that are no
longer about LED coupling. `[calc]` The surviving total is ~22 + 6.5 + 4.8 ≈
**33 cents** before the `VREFOUT` fix and ~11 cents after it, not the "more than
every static term in ADR 0006's precision budget put together" that ADR 0014
claims for four routes. The conclusion (measure it at E6/E9) survives; the
arithmetic behind it does not. This is a textbook CLAUDE.md §5 case: ADR 0006
refuted a row and the two documents that cite the row's *count* did not follow.

**Scale, for context** `[calc]`: 1 V/oct → 1200 cents/V → **1 mV = 1.2 cents**,
so the unfixed ground terms are ~9 mV at the pitch jack and the WS2815 rail term
was ~18 mV p-p.

---

### A9-10 — `LED-PANEL` / `R-LED-PANEL` — the module's own lighting is outside every lighting rule — **MINOR**

`[repo] hardware/module/panel-led/panel-led.md` — one LED, `R-LED-PANEL`
2.2 kΩ from **`+12 V analog`**, `[calc]` ≈4.5 mA, inside the module, on the same
rail that feeds the pitch stage's op-amps, with a return that the page itself
describes as *"**Not drawn anywhere in the corpus.** … which ground it lands on
is the disputed figure"* (`dig-gnd-topology`, `status: disputed`).

Today it is DC and harmless. Three things make it worth filing anyway:

1. **ADR 0014 governs "lighting" and does not know this LED exists.** The
   constant-current rule, the shared budget and the blank-at-boot rule all scope
   the instrument only. There is no statement anywhere that the module's
   indicator must not blink, pulse or PWM — and the page's own proposed rework
   (*"drive it from the LT1641's `TIMER` node, or from the gate, so that lit =
   running and dark = latched"*) makes it a **fault-state-dependent** load on
   the analog rail.
2. `[repo] 0006-cv-channel-allocation.md:816-817` floats *"an LED per jack
   tracking that channel's value … Costs a driver and six LEDs"*. That would put
   **six signal-modulated LEDs on the module's analog ground, centimetres from
   the pitch jack** — the same mechanism ADR 0006 spends a whole section
   removing from the instrument end, reintroduced at the end that has no `AGND`
   protection. Nothing marks it as needing the constant-current treatment.
3. The one route that is quantified and unfixed (R5, the module's internal pour,
   5.7–7.2 cents) is the route this LED's return would use.

**Recommend:** one sentence in ADR 0014 or ADR 0006 scoping the lighting rules
to *all* LEDs including the module's, and a note on the per-jack-LED idea that
it is not free on the pitch channel.

---

### A9-11 — `J-LED-L` / `J-LED-R` — the `BI` decision landed on the schematic page and not on the conductor count — **MAJOR**

Task item 4. The finding `BI` is a ground connection is **correct** (V2 above,
verified against the pin table). What did not follow it:

`[repo] hardware/carrier/carrier.md:322`, the *Loom conductor count* table, still
reads:

| | Conductors |
|---|---|
| WS2815: 12 V, GND, `DI` per strip (+`BI` if needed) | **6–8** |

and totals **"~28–30"** on that range. The question closed at **6** on
2026-09-21 (`[repo] led-strip-drive.md:86-88`: *"the LED loom stays at 6
conductors rather than 8"*; `[repo] led-strip-drive/notes.md:21-23`; `[repo]
hardware/carrier/led-strip-drive/bom.csv` `R-LED-SER` note, *"two gates, two
resistors, and the LED loom stays at 6 conductors rather than 8"*). The carrier
page carries the open question and an obsolete range on the number that feeds
the loom/termination analysis — and that analysis is load-bearing, because the
same section concludes *"a 45 mm-wide carrier and open side channels are still
mutually"* exclusive.

The register cannot catch this: `config/figures.yaml` has no entry for the LED
conductor count, and `matrix-led-current`'s `forbidden` list is `[]`.

**Related, in the same `led-strip-drive.md`:** the Interfaces table at `:23`
gives `J-LED-L BI`, `J-LED-R BI` direction **`out`**, peer *"the head of each
strip"*, while the note in the same row says it is *"a **ground** connection,
not a driven one"*. A ground is not an output. Small, but this table is the
machine-readable-ish surface the `circuit.yaml` edges were seeded from.

---

### A9-12 — `R-LED-SER` — three values in three places — **MAJOR (classic staleness, live)**

One part, one circuit directory, three numbers:

| Where | Value |
|---|---|
| `[repo] led-strip-drive.md:32` (the ASCII drawing) | `[R-LED-SER **220R**]` |
| `[repo] led-strip-drive.md:38` (the ASCII drawing, gate C) | `[**220R**]` |
| `[repo] led-strip-drive.md:111` (component table) | **100–330 Ω** |
| `[repo] hardware/carrier/led-strip-drive/bom.csv` | **330R 1%** |
| `[repo] hardware/bom.csv:23` | **330R 1%** |

The drawing and the BOM disagree by 110 Ω on a part whose job is edge damping,
and the component table gives a range that contains both. `[repo]
hardware/carrier/carrier.md:291` records the identical defect being fixed for
the SPI siblings — *"`R-SPI-SER` ×3 | **100 Ω** | … **Was drawn as three refdes
that are not in the BOM, at 220 Ω, derived from an RC model**"* — so the 220 Ω
in the LED drawing is very likely the same stale SPI-derived number, copied
across when both lived in `carrier.md`, and the LED row moved to 330 Ω without
the drawing following.

`[calc]` It is not electrically critical — 330 Ω against a WS2815's 15 pF input
capacitance `[datasheet] WS2815.pdf` p.3 plus ~40 pF of 420 mm wire `[from
memory]` gives τ ≈ 18 ns, comfortably inside the 220–380 ns `T0H` window
`[datasheet]`. But nothing in the corpus shows that calculation, so "100–330 Ω"
is a range nobody has bounded, and the drawing says a number the BOM does not
carry. Pick one, show the RC, and make the three agree.

---

### A9-13 — `R-LED-PD`, `J-LED-L`, `J-LED-R` — proposed, load-bearing, and in no BOM — **MINOR (already advisory, but under-weighted)**

`[repo] .staleness/report.txt` lists all three under *"drawn in a schematic, no
BOM row (19) — **ADVISORY, not a failure**"*. I confirm: `grep` for `R-LED-PD`
and `J-LED` across every `.csv` in the repo returns **nothing** — not the
fragment, not `hardware/bom.csv`, not `hardware/unplaced.csv`.

The advisory framing undersells two of them:

- **`R-LED-PD` is the fix for a hole the page describes as unfixable later** —
  *"Two 0805s, and they cannot be added later"* `[repo] led-strip-drive.md:56`.
  A part that must exist at fab and exists in no BOM will not be on the order.
- **`J-LED-L/-R` are the LED loom's only interface**, and A9-11 shows the
  conductor count that depends on them is stale in the other direction.

Also worth noting against the "parts nobody has drawn" rule: **`LED-SIDE` — the
strips themselves — is in `hardware/unplaced.csv`** `[repo]
hardware/unplaced.csv`, i.e. filed as a part no schematic page names, while
`hardware/carrier/led-strip-drive/` exists and is entirely about driving it. The
drive circuit is placed and the load is unplaced.

---

### A9-14 — `U-MCU-RT` — the GPIO budget that decides the two-data-line topology is wrong in three documents, three different ways — **MINOR**

ADR 0014's choice of **B** (two independent data lines) over **C** (one GPIO,
mirrored) rests on `[repo] 0014-lighting.md:55-57`: *"Two data lines cost one
extra GPIO, against roughly **17 broken out and 12 needed** on the real-time
board (ADR 0007)."*

`[repo] docs/decisions/0007-imu-selection.md:180-192` is the owner and says:
broken out **17** (GPIO 1–7, 33–40, 43, 44); used **14 of 17**; spare 3, 4, 33;
and *"WS2815 data, two strips | 2 | **1, 2**"* — which matches
`led-strip-drive.md`'s `IO1, IO2` exactly.

Three documents, three counts:

| Document | Broken out | Needed | Spare |
|---|---|---|---|
| `0007-imu-selection.md:180-192` (owner) | 17 | 14 | 3 |
| `ROADMAP.md:195` | 17 | — | 3 |
| **`0014-lighting.md:55`** | 17 | **12** | (implies 5) |
| **`hardware/bom.csv:25` / `hardware/carrier/bom.csv:2`** | **16** *(list omits GPIO33)* | 14 | 2 |

ADR 0014's "12 needed" appears to be the **octal-PSRAM worst case** from a
different paragraph of ADR 0007 (`:229`, *"would take the 17 broken-out pins
down to 12"*) — a ceiling imported as a floor. And `hardware/bom.csv`'s
`U-MCU-RT` note still carries *"16 GPIO broken out (1-7, 34-40, 43, 44)"* — the
GPIO33 omission that ADR 0007 explicitly says *"propagated into ADR 0013 and the
roadmap"* and was corrected. **It did not get corrected in the BOM**, and since
`hardware/bom.csv` is generated, the fix belongs in
`hardware/carrier/bom.csv` and then `tools/merge-bom.py` (CLAUDE.md,
Hardware conventions).

Nothing breaks — with 14 of 17 used there are three spare either way, so option
B is still affordable. But the sentence that decides a topology cites a number
its own source contradicts.

---

### A9-15 — Lighting output has no place in the 250 µs loop budget — **MINOR, but it is a real-time claim nobody has made**

`[repo] docs/reference/latency-budget.md` (figure `loop-budget`, *"196–241 µs of
250 µs"*) accounts for the ADC read (24 µs), the key chain (32 µs) and six DAC
words (96 µs), and notes the pass reaches **291 µs with ESP-IDF driver
defaults** — i.e. it does not close. **No LED transfer appears in it.**

`[calc]` at the WS281x 800 kbps line rate (`[datasheet]` `T0H`+`T0L` ≈ 1.25 µs
per bit):

- one side strip, 25 LEDs × 24 bits × 1.25 µs = **750 µs**
- both strips, driven in parallel on separate RMT channels = **750 µs**
- the matrix, 64 LEDs × 24 bits × 1.25 µs = **1.92 ms**

Each is longer than the entire 250 µs scan period. Asynchronous RMT/DMA makes
that fine — but **nothing in the corpus says that is the plan for the matrix**,
and the one peripheral the corpus names for the matrix is the wrong one:
`[repo] 0007-imu-selection.md:176` says it is *"driven over SPI2 in Zephyr's
configuration"*, while `[repo] hardware/interfaces/spi-link/spi-link.md:118-127`
allocates **SPI2 to the DAC8568 and the MCP3202 at 49 % of the loop** and SPI3
to the key chain. ADR 0014 names RMT for the strips (`:56-57`) and names nothing
for the matrix.

Related: ADR 0014's own anti-chatter fix — *"Drive the LEDs from the post-gate,
slew-limited breath value, not from the raw ADC sample"* (`:490-494`) — puts the
animation source inside the loop, which is where the question arises.

**Recommend:** one line assigning the matrix a peripheral (the S3 has four RMT
TX channels `[from memory]`, so three LED outputs fit) and an LED refresh rate,
and a row in the latency budget saying it is asynchronous and costs only buffer
preparation.

---

### A9-16 — `firmware/README.md` does not carry the three rules the hardware delegates to it — **MAJOR**

Four safety-critical behaviours are specified in ADR 0014 and relied on by ADR
0005, ADR 0006 and the pitch precision budget. The firmware document carries
**none** of them.

| Rule | Where it is stated | In `firmware/README.md`? |
|---|---|---|
| The ~3 W shared lighting clamp, with proportional scale-down | `0014:172-188` | **No** |
| Blank both strips *and* the matrix as the first act at boot | `0014:404-408` | **No** |
| Animate at constant total current (ADR 0006's free fix for pitch) | `0014:520-527`, `0006:657-660` | **No** |
| Drive the LEDs from the post-gate slew-limited value, not the raw sample | `0014:490-494` | **No** |

`[repo] firmware/README.md:113-131` has a section titled *"The lights are
instrument-side, and so is everything about them"* which states Zero, Deadband
and Span — the three *cosmetic* parameters — and stops. `grep -i "clamp\|blank"`
over `firmware/` returns nothing relevant.

This is the highest-leverage gap in the slice. ADR 0014 argues at length that
the firmware clamp *"is a comfort feature against the electrical failure, and a
real one against the thermal failure"* and that nothing but firmware bounds a
sustained bright state that is electrically legal and thermally not. The
document a firmware author reads first does not mention it.

---

### A9-17 — The matrix's 2.6 mm pitch is an unsourced number carrying three decisions — **MINOR**

Task item 6. **The claim is asserted, the decision it gates is tested, and the
number underneath is from memory.**

- The claim: `[repo] 0014-lighting.md:452-455` — *"At **2.6 mm** LED pitch a
  10 mm standoff blends adjacent pixels into mush … prototype against the
  demanding case."* No provenance, no calculation.
- The test **does** exist: `[repo] ROADMAP.md:191`, M6, *"Can an 8×8 at 2.6 mm
  pitch stay pixel-distinct through a window, or only as a blurred bar? Decides
  whether the 2-D IMU assignment is usable"* — which is exactly the question my
  brief asks about, correctly scoped and scheduled. **Good.**
- But `[repo] hardware/carrier/carrier.md:244-256` builds real arithmetic on it
  — *"8×8 at 2.6 mm pitch (ADR 0014's own figure) → 20.8 mm of emitters"*,
  leading to a proposal to **delete the carrier cutout and mount the dev board
  on the underside** — and honestly marks its inputs *"`[from memory]` inputs
  that E1 will replace"*. The owning ADR does not mark it at all, so the
  citation chain reads as firmer at the source than at the derivation.

`[datasheet]` The banked Waveshare document is a **schematic**, which carries no
placement, so 2.6 mm cannot be read from it. Nothing else in `datasheets/`
gives the board's LED pitch or outline.

**And the two pages now disagree on the construction constraint.**
`0014-lighting.md:465-468` states the ~22 mm carrier cutout as a
must-be-in-CAD-from-the-start constraint with the underside mount as the
*fallback*; `carrier.md:242-243` proposes the underside mount as the **default**
and deleting the cutout. Both are live corpus files, one is an accepted ADR.
Whichever wins, the other should say so — and ADR 0009 (`:270-283`) still lists
the matching carrier cutout as one of *"three details that have to be in the CAD
from the start"*.

**Recommend:** mark the 2.6 mm `[from memory]` in ADR 0014, add it to the E1
measurement list (the board will be in hand; a caliper settles it and the whole
cutout-vs-underside argument turns on it), and reconcile ADR 0014 / ADR 0009 /
`carrier.md` on which mounting is the default.

---

### A9-18 — Smaller things, checked and worth one line each

- **`0014:178-181`, "a full field at around 60 % of one channel."** `[calc]`
  3 W ÷ 4.8 W = 62.5 % — that is 60 % of **full white** (all three channels),
  not of one channel. On the corrected 12 mA/ch figure it becomes ~26 %. The
  strips' half of the same sentence checks out: 3 ÷ 12.1 = 25 % ✓ *"a quarter of
  full white"*, and 3 ÷ 4.1 = 73 % ✓ *"a single hue at ~75 %"*.
- **`0014:81-84`, the "backup data line" selling point**, is never qualified by
  what the schematic page later established — the head pixel's `BI` is grounded,
  so pixel 1 has no backup, and the bypass is sticky until power-off
  `[datasheet]`. In a body that opens on six fasteners this is minor; the ADR
  sells it as mattering *"more than it would in a serviceable build"*.
- **The tape's internal `BI` wiring is assumed, not documented.**
  `led-strip-drive.md:82-85` asserts *"From L2 onward each pixel's `BI` comes
  from the *previous* pixel's `DI` node, internal to the tape"*. The banked
  datasheet covers the **IC**; `[repo] datasheets/MANIFEST.csv:99` has the
  assembled strip as `BLOCKED`. The 6-conductor loom decision rests on a
  discrete-LED application figure plus an assumption about a tape nobody has a
  document for. Low risk, worth a sentence.
- **`config/figures.yaml` has two rows for the WS2815** — `[repo]
  datasheets/MANIFEST.csv:55` (`WorldSemi`) and `:56` (`Worldsemi`), same file,
  same SHA-256, different vendor spelling and different note. Generated from
  different `.manifest-R*.csv` fragments, so per CLAUDE.md §4 neither fragment
  should be edited; flagging only so it is not mistaken for two documents.
- **`hardware/carrier/led-strip-drive/circuit.yaml` carries two false
  `depends_on` edges**, of exactly the shape the file's own header warns about:
  `refdes:C-STRIP-BULK` (the page names it **to say it belongs to
  `power-entry-instrument`**) and `refdes:R-SPI-PULL` (named as a **precedent**
  from the module page, not used here). It also omits `refdes:R-LED-PD` and the
  `J-LED-*` connectors, which the page does draw. Reported as verification of
  the header's prediction, not as a new class.
- **`0005:161`, "Clamp fails, strips latched full white"**, reads **1023 mA in
  both the 5 V and the 12 V-direct columns**. `[calc]` they reconcile
  independently (960 + 63 idle; 1005 + 18 analog), so it is probably a
  coincidence rather than a copy — but it is worth one person's eye, and both
  columns move if A9-04 or A9-05 does.

---

## Answers to the six questions, in order

1. **The current estimate.** `config/figures.yaml`, `power-entry-instrument.md`,
   `ROADMAP.md` and ADR 0007 are all honest about resting on an unmeasured
   estimate. **ADR 0014's own power-budget section is not** — it states 960 mA
   as fact 199 lines above the banner that refutes it, and the same sentences
   carry a second staleness (a shared regulator that the two-buck decision
   deleted). See A9-05. The constraint the correction *substitutes* is itself
   wrong for the instrument's actual power path — A9-01, A9-02.
2. **Coupling routes.** Nine identified; the corpus quantifies four, fixes two in
   hardware, leaves three unquantified and two unnamed. The "four routes / two
   fixed" framing in ADR 0014 and the ROADMAP is stale against ADR 0006's own
   refutation. See A9-09, A9-10.
3. **Level shifter.** The threshold argument is **correct and verified against
   the banked datasheet** (V1), and can be made stronger from the pin-function
   table. The *series* resistor on the same net is specified three different ways
   (A9-12), and the matrix's data path has an undocumented transistor stage
   (A9-03).
4. **`BI`.** **Correct** — verified against the pin table (V2). The net-count
   consequence did not reach `carrier.md`'s conductor table, which still carries
   "6–8" and "`+BI` if needed". See A9-11.
5. **Thermal.** The budget's central constant is derived from a power figure its
   own power ADR contradicts by ~2×, in the direction that makes the clamp too
   loose (A9-07); the clamp does not bound the per-device limit the corpus just
   discovered (A9-06); and what measures it — the M8 soak, `ROADMAP.md:192` —
   exists and is correctly scoped. The strips' contribution to all of it rests on
   a per-LED current with no document (A9-04).
6. **Diffusion and pitch.** The claim that decides the 2-D assignment **is
   tested** — M6, `ROADMAP.md:191`, correctly phrased as the deciding question.
   The pitch it is stated against is unsourced and marked `[from memory]` only in
   the file that derives from it, not in the file that owns it; and ADR 0014,
   ADR 0009 and `carrier.md` currently disagree about whether the carrier cutout
   or the underside mount is the default. See A9-17.

## What I could not check

- The WS2815 **recommended application circuit figure** is a raster image with
  no text layer; I confirmed the image encoding but could not re-read the figure.
  The `BI`-to-`GND` claim is supported by the pin table but the figure itself
  remains a single-reader observation. `led-strip-drive.md`'s instruction to
  confirm it visually before crimping should stay.
- The **5 V header pin's net** on the Waveshare board is inferred, not read: the
  schematic does not draw the header rows. The inference is strong (`VBUS`
  appears at four coordinates, all at the USB connector and `D1`), but A9-01
  would be settled outright by a continuity check between the board's `5V` pin
  and `D1`'s cathode at E1 — thirty seconds with a meter.
- No **bench data** exists for anything in this slice. E1 (matrix idle and, I
  recommend, matrix full-field), E6/E9 (pitch while sweeping the LEDs), M6
  (both diffusion prototypes) and M8 (thermal soak) are all still ahead, and all
  four are correctly scheduled.
