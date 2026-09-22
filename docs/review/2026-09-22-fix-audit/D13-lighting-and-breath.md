# D13 — the lighting current and the breath sensor's full scale

**Slice:** the two corrections that landed 2026-09-22 — ADR 0014's WS2815
annotation (commit `b32c557`) and the `sensor-full-scale` citation sweep
(commit `df22096`).

**Cold:** nothing under `docs/review/**` read except this wave's `README.md`.
Git log and `git diff` used throughout.

**Verdict in one line:** both datasheet claims are **correct as quotations** and
one supporting sentence in the lighting annotation is **false**; both fixes are
**incomplete**, the lighting one substantially so — the annotation corrects one
cell of a six-cell table and leaves **four** downstream uses of the refuted
figure live, one of which reverses the ADR's central conclusion.

---

## 1. The two datasheet claims, verified

### 1a. WS2815, 15 mA per channel — CONFIRMED, with three caveats the annotation does not carry

`[test]` Integrity first, since a claim off the bank is only as good as the bank:

```
$ sha256sum datasheets/led/WS2815.pdf
72e22d2f740c561db3cd82db1915dad35c546f5e7551b896000445fa4b3ca957
$ python3 tools/verify-datasheets.py
datasheets: 78 verified, 23 recorded as blocked or not-fetched, 0 problems
```

That SHA matches `datasheets/MANIFEST.csv` rows 56 and 57 `[repo]`. The document
is Worldsemi WS2815 V1.1, 8 pages, revision record on p.8 (`V1.0 20170523`,
`V1.1 20171010 "Absolute Maximum Ratings"`) `[datasheet WS2815.pdf p.8]`.

`[datasheet WS2815.pdf p.3]` Read with `pymupdf` per this wave's README. The
figure is in a table headed **`LED Characteristics`** with a single value column
headed **`Ref. Value`**, verbatim and in document order:

```
LED Characteristics
Ref. Value
Quiescent Current                     2.1mA
RGB Channel Constant Current          15mA
RED Brightness (Central Value)        360mcd
GREEN Brightness (Central Value)      1150mcd
BLUE Brightness (Central Value)       220mcd
WHITE Brightness (Central Value)      1710mcd
```

So **ADR 0014:135–136 quotes the document correctly**, including the part it
gets right that matters: the figure is *per channel*, and three channels at full
white is 45 mA per LED. `[calc]` 45 / 20.2 = 2.228 → the stated **2.23×** is
right; 50 × 45 mA = **2.25 A**; 2.25 A × 12 V = **27.0 W**; 27.0 × 3 K/W =
**81 K**. Every number in the annotation's arithmetic checks.

**Caveat 1 — the figure carries no conditions at all, and the two condition
lines on the page do not govern it.** p.3 has two bracketed headers,
`Electrical Characteristics (TA=-20～+70℃, VDD=4.5～5.5V, VSS=0V)` and
`Switching Characteristics (TA=-20～+70℃, VDD=4.5～5.5V, VSS=0V)`
`[datasheet p.3]`. The `LED Characteristics` table is a **third**, separate
block with no header of its own and one `Ref. Value` column — no min/typ/max, no
temperature, no supply, no duty cycle. And the `VDD` in those two headers is the
**logic** rail, not the LED rail: p.2's `PIN Function` gives pin 1 `VCC` as
"IC POWER SUPPLY" and pin 2 `VDD` as "LED POWER SUPPLY, connect to '+12V'",
while p.2's Absolute Maximum Ratings gives `Power supply voltage VDD
+9.5~+13.5 V` `[datasheet p.2]`. The document reuses one symbol for two nets —
which this same ADR already established at :100–107 for `V_IH`, and
`led-strip-drive.md:74–81` documents at length `[repo]`. So **nothing in the
document conditions the 15 mA on voltage, colour or temperature**; it is a
nominal design value, which is why "Ref. Value" is the correct thing to call it.

**Caveat 2 — colour does not change the arithmetic, and the annotation is right
not to correct for it.** One current figure covers all three channels; only
brightness differs (360 / 1150 / 220 mcd) `[datasheet p.3]`. Full white is all
three channels at 255/256 duty, so 45 mA/LED needs no colour correction.

**Caveat 3 — the document cannot bound the thermal consequence it now implies.**
`[datasheet, all 8 pages read]` There is **no thermal resistance, no package
power dissipation rating and no derating curve** anywhere in the WS2815
datasheet. The only thermal number is Absolute Maximum `Operating Temperature
Topt -25～+85 ℃` `[datasheet p.2]`. `[calc]` At 45 mA from a 12 V rail each LED
takes 0.54 W, essentially all of it dissipated in the package's internal current
sinks — and `[calc]` 20 °C ambient + the annotation's own 81 K is **101 °C**,
which is outside the WS2815's own +85 °C operating maximum and outside the
MPXV4006DP's `Operating Temperature TA +10° to +60° °C`
`[datasheet MPXV4006DP.pdf p.4]`. **The pathological state the annotation
computes violates two banked absolute-maximum ratings, and the annotation does
not say so.** See §3.

**One honest tension, marked as weak.** `[from memory]` 20.2 mA/LED × 12 V ×
60/m = 14.5 W/m `[calc]`, which is very close to the 14.4 W/m that WS2815 60/m
*tape* is commonly marketed at, while the IC datasheet implies 32.4 W/m
`[calc]`. So the 2.23× is plausibly the known gap between an IC's
constant-current spec and a tape vendor's W/m rating, and **neither number is a
measurement**. This *supports* the fixer's decision not to rewrite the table
(§2) — but note the asymmetry with `matrix-led-current`, whose 960 mA at least
**stated its source** ("WS2812C-2020 draws 5 mA per channel", 0014:437) and was
caught for that reason. `[repo, git]` `git log -S "1.01 A" -- docs/decisions/0014-lighting.md`
returns one commit, `7a5236c`, the file's creation: **20.2 mA/LED has never had
a stated source in this repository**, which is the worse of the two conditions.

### 1b. The annotation's own corroborating sentence is WRONG

ADR 0014:141–143 `[repo]`:

> Note the same page's *Quiescent Current **2.1 mA*** reproduces ADR 0005's
> 123 mA figure exactly, so the two numbers in this corpus came from
> different sources and only the quiescent one came from the datasheet.

`[calc]` 2.1 mA × 50 LEDs = **105 mA**, not 123 mA. 123 / 50 = 2.46 mA/LED.
105 mA is **15 % below** ADR 0005:158's `123 mA` and 12.5 % below ADR 0005:233's
"roughly 120 mA of strip quiescent draw" `[repo]`. "Exactly" is false.

It is also unfalsifiable as written, and that is the deeper problem:
`config/figures.yaml` `umbilical-current` states "This is the only derived
figure; **eight others are asserted**" `[repo] config/figures.yaml:604`, so the
`123 mA` cell has no written decomposition. Nobody can tell how much of it is
strip quiescent and how much is the +12 V analog branch.

**What would settle it:** write the per-branch decomposition of ADR 0005's
`12 V direct` column. Until that exists, no claim of the form "the datasheet
reproduces the load table" can be checked — and §3 shows the same missing
decomposition blocks the one propagation that matters most.

### 1c. MPXV4006DP full scale — CONFIRMED, and the register is right

`[datasheet analog/MPXV4006DP.pdf p.3–4]`, extracted verbatim:

```
VS                4.75   5.0   5.25   Vdc
Full Scale Span   VFSS    —    4.6    —     V
Offset (Voff)            0.152 0.265 0.378  V
Sensitivity V/P            —    766    —    mV/kPa
Accuracy (10 to 60°C)                ±2.46  %VFSS with auto zero
                                     ±5.0   %VFSS without auto zero
Transfer Function (kPa): Vout = VS*[(0.1533*P) + 0.053]
Operating Temperature    TA    +10° to +60° °C
```

`[calc]` 5 × (0.1533 × 6 + 0.053) = **4.864 V**, and 0.265 + 4.6 = 4.865 V — the
transfer function and the specified `VFSS` agree to a millivolt. `sensor-full-scale`
= `4.86 V` is right and its derivation in `config/figures.yaml:59` is right
`[repo]`. Sensor supply is the REF5050's 5.000 V `[repo] 0003:475–481`, so
`VS = 5 V` is the correct operating point.

---

## 2. Was leaving the table as drawn right? — Half right, and the half that is
missing is the half that does the work

**The argument is sound.** `matrix-led-current` is `blocked` with
`decided_by: "A BENCH MEASUREMENT AT E1, not another document"` `[repo]
config/figures.yaml:701`, and §1a shows the strip figure is in exactly that
position: two undocumented candidates, no measurement. Rewriting 2.25 A into the
table would replace an unsourced number with a differently-unsourced number and
mark it settled. **Not rewriting was the right call.**

**But "annotated" is not what this repo means by it, and the precedent the
annotation cites shows the difference.** The `matrix-led-current` treatment has
**three** parts, and the strip fix has one:

| | matrix (the cited precedent) | strips (this fix) |
|---|---|---|
| Register entry with `status: blocked`, `candidates`, `decided_by`, `blocked_on` | yes, `config/figures.yaml:695–705` | **none — no entry of any kind** |
| A measurement row that produces the number | yes, `ROADMAP.md:189` (E1) | **none** |
| A marker at each use | at 3 of 4 uses | at 1 of 5 uses |

`[repo]` I grepped `config/figures.yaml` for every `id:` (37 figures): there is
no strip-current entry, no per-LED-current entry, and no interior-rise entry.
`[repo]` I grepped `ROADMAP.md` for every lighting row: `:189` measures the
**matrix** idle current at E1; `:192` measures interior rise at M8 "with strips
and matrix **at the clamp**" — which is a 3 W soak and does not produce a
per-LED full-white current. `:106` says "At E11 the LED strips are not installed
— they arrive at M6". **So the sentence "the strip figure needs the same
treatment: measured, not re-derived" (0014:150–151) names a measurement that
does not exist anywhere in the plan.**

**This matters mechanically, not just tidily.** `tools/check-staleness.py`
excuses a forbidden value only when refutation wording sits within
`REFUTATION_WINDOW = 300` characters of the match `[repo] tools/check-staleness.py:72`,
and `docs/reference/repo-maintenance.md:64–67` states the rule the same way. With
no register entry there are no forbidden patterns, so **the checker cannot see
any of these lines at all** — and if the figure were registered properly, three
of the four surviving uses would fail that window. `[calc]` measured from the
end of the annotation block (line 152) over the joined stream:

- to `:174` (`12.1 W | ~36 K`) — **1,012 characters**
- to `:198` (`twice realistic use`, `a quarter of full white`, `~75 %`) — **2,200**
- to `:257` (`0.13 A … unremarkable against a 3 W budget`) — **5,401**

All three are 3× to 18× outside the window the repo's own tooling enforces.

**And the annotate-don't-rewrite route has already failed once in this very
file.** `[repo]` The matrix's 960 mA survives unmarked at **0014:182** — "at
full field it asks for 960 mA on its own" — 197 lines *above* the annotation
that refutes it, in the paragraph that sizes the regulator. `matrix-led-current`
carries `forbidden: []` `[repo] config/figures.yaml:704`, which
`docs/reference/repo-maintenance.md:55–56` names as a known hole: "A figure with
an empty `forbidden` list … protects nothing until it is settled and its old
values are listed." So the precedent the strip fix copied is itself partial, and
the strip fix copied the partial half.

**The sibling slice's claim is CONFIRMED and is wider than stated.** It named
`:175`, `:198` and `:257`. The full list is below (§3). `:174` is also unmarked
even though the annotation names its exact numbers; and `:122` and the entire
30/m row are affected too.

### What I would do

1. **Add a `strip-led-current` entry to `config/figures.yaml`**, `status: blocked`,
   `value: "BLOCKED"`, owner ADR 0014, `candidates:` the two numbers with their
   provenance (20.2 mA/LED — unsourced, arrives with the file, consistent with a
   14.4 W/m tape rating; 45 mA/LED — WS2815 V1.1 p.3 `Ref. Value`),
   `decided_by:` a bench measurement, `blocked_on:` that measurement. **Put the
   old spellings in `forbidden`** — `"1.01 A"`, `"0.34 A"`, `"| 12.1 W |"`,
   `"~36 K"`, `"17.7 W"`, `"~53 K"`, `"0.13 A"`, `"20.2 mA"` — and **grep first**
   per CLAUDE.md §2, because `0.13 A` in particular needs checking against the
   30/m row's `0.07 A` and any unrelated use.
2. **Add the ROADMAP measurement row.** It belongs at M6/M8, not E1, because
   `ROADMAP.md:106` says the strips do not exist before M6. One current probe on
   one strip's +12 V feed at commanded full white settles it in a minute.
3. **Leave the table's numbers**, but mark each cell and each downstream use with
   the same inline form the matrix already uses at 0014:437 — a clause in the
   same sentence, inside 300 characters, on one line (CLAUDE.md §2, third trap).
4. **Put the marker on `unplaced.csv:5` (`LED-SIDE`)** as well. That row is the
   WS2815 tape's only BOM entry, it makes no current claim at all `[repo]`, and
   it is where somebody ordering the part looks.

---

## 3. The 2.23× traced through — every downstream statement, touched or not

`[calc]` The whole strip table is one number times three multipliers: full
white = N × I, single hue full = N × I/3, single hue 40 % = N × I/3 × 0.4.
Substituting 45 mA for 20.2 mA:

| ADR 0014 line | as drawn | at 45 mA/LED | marked? |
|---|---|---|---|
| `:131` 30/m full white | 0.50 A | **1.125 A** | no |
| `:131` 30/m single hue full | 0.17 A | **0.375 A** | no |
| `:131` 30/m single hue 40 % | 0.07 A | **0.15 A** | no |
| `:132` 60/m full white | 1.01 A | **2.25 A** | **yes** — the one cell the annotation restates |
| `:132` 60/m single hue full | 0.34 A | **0.75 A** | no |
| `:132` 60/m single hue 40 % | **0.13 A** | **0.30 A** | no — and this is the cell the rest of the corpus uses |

**Six cells; one corrected.** The uncorrected five are inside the 300-character
window of the annotation, so they are at least adjacent to it. The four below
are not.

### 3a. The clamp — the conclusion does not survive, and this is the finding of the slice

`[repo] 0014:193` "**A single instrument-wide lighting budget of ~3 W**".
`[repo] 0014:173` and `:256–257` define realistic use as the single-hue-40 % cell:
`~1.5 W`, `0.13 A`. `[calc]` 0.13 A × 12 V = 1.56 W, which reproduces `~1.5 W`
exactly, so the identification is certain.

`[calc]` At 45 mA/LED, realistic use is 0.30 A = **3.6 W**.

**3 W is no longer twice realistic use. It is 0.83× realistic use.** The clamp
as specified would engage during ordinary single-hue breath tracking at moderate
brightness and scale it down — the exact behaviour ADR 0014 designed the clamp
*not* to have at realistic settings. Every sentence in `:198–201` inverts:

| 0014:198–201, as written | at 45 mA/LED `[calc]` |
|---|---|
| "3 W is twice realistic use" | 3 W is **0.83×** realistic use (3 / 3.6) |
| "about a sixth of the pathological case" | about **a thirteenth** (3 / 40.5, see 3c) |
| "on the strips it is a quarter of full white" | **11 %** (3 / 27) |
| "or a single hue at ~75 %" | **~33 %** (250 mA / 0.75 A) |
| "it costs roughly 9 K of interior rise" | **unchanged** — 3 W × 3 K/W = 9 K |

The last row is the one piece of good news and it is worth stating plainly: the
clamp's **value in watts** is defensible and its thermal cost is unaffected,
because it is defined in power. What breaks is every claim about *headroom*, and
the claim that the clamp is generous. `[repo] 0014:257` "around **0.13 A**
there, which is unremarkable against a 3 W budget" becomes 0.30 A = 3.6 W, i.e.
**over** the budget.

`[repo]` `firmware/` contains only `README.md` and no clamp constant, so nothing
is implemented against the wrong number yet. The fix is still cheap.

### 3b. The thermal table at `:171–175` — unmarked, and `:175` is not mentioned at all

`[calc]`

| 0014 row | as drawn | at 45 mA/LED |
|---|---|---|
| `:173` Realistic use | ~1.5 W / ~4 K | **3.6 W / ~10.8 K** |
| `:174` Both strips full white | 12.1 W / ~36 K | **27 W / ~81 K** — named by the annotation, 1,012 chars away, cell unmarked |
| `:175` Matrix full white as well | ~17.7 W / **~53 K** | **~40.5 W / ~122 K** — not mentioned by the annotation at all |

`[calc]` `:175`'s `~17.7 W` decomposes as 12.12 W of strips plus 5.64 W of
matrix (960 mA × 0.49 × 12 V), which confirms it is built on both refuted
figures at once. Substituting the strips at 27 W and the matrix at the banked
WS2812B-2020 12 mA/channel (2.304 A × 0.49 × 12 V = 13.5 W `[calc]`, from
`config/figures.yaml:700`) gives **40.5 W and ~122 K**.

`[calc]` 20 °C + 81 K = 101 °C. Against `[datasheet WS2815.pdf p.2]`
`Topt -25～+85 ℃` and `[datasheet MPXV4006DP.pdf p.4]` `TA +10° to +60° °C`,
the `:174` state is now outside two banked absolute maxima, and `:178`'s "an
acrylic bond at its service limit" — asserted at ~36 K, sourced nowhere in the
corpus `[repo]`, the phrase occurs exactly once — is well past whatever limit
was meant. **A linear K/W model is also being used 2.2× outside the point it was
fitted at**, where convection and radiation are not linear; see §4.

### 3c. `:122` — "hundreds of milliamps" is now amps

`[repo] 0014:120–123` justifies `C-STRIP-BULK` (470–1000 µF ×2): "a WS2815 run
modulates its draw by **hundreds of milliamps** at the ~2 kHz PWM rate".
`[calc]` At 45 mA/LED a 25-LED run modulates 0 → 1.125 A, and both runs 0 →
2.25 A. The **conclusion strengthens** (bulk at the load matters more, not less)
but the bulk *value* was chosen against a swing 2.23× smaller and has no written
derivation `[repo]` — `hardware/bom.csv:4` says only "Bulk belongs at the load".
Unmarked. Nothing checks it.

### 3d. ADR 0005's load table — one row moves hard, and one column cannot be checked

`[repo] 0005:157–162`.

**Row that moves:** `:162` "Clamp fails, strips latched full white | 1023 mA |
1023 mA | **~1522 mA** | ~17 W". `[calc]` The 12 V-direct cell is the strip
full-white 1010 mA plus ~13 mA; at 45 mA/LED it becomes ~2263 mA, umbilical
~2764 mA, body heat 2.764 A × 11.4 V ≈ **31.5 W**.

**The conclusion this row carries gets stronger, and its margin roughly
doubles.** `[repo] 0005:288–298`: "a latched full-white failure is **~1.5 A**,
which is *above* the etherCON contact's 1.5 A rating rather than comfortably
below it … a latched-full-white instrument now *trips the limiter* instead of
sitting just under it, which is the behaviour wanted." `[calc]` It is ~2.8 A —
**1.8× the contact rating**, not marginally over it. And `[repo]
config/figures.yaml:334` `umbilical-pinmap` puts +12 V on **one** conductor
(pins 3,6), so `[calc]` 2.76 A on a single 24 AWG conductor over 0.34 Ω round
trip is 0.94 V of drop and 2.6 W in the cable. Direction of the argument:
unchanged. Magnitude: understated ~1.8×. Unmarked.

**Column that cannot be checked — and this is the real gap.** `:159` "Typical
play | 226 mA | **248 mA** | **359 mA**". `[repo] config/figures.yaml:604`
`umbilical-current`'s derivation is `226 mA × 5 V / (0.9 × 11.4 V) + 248 mA =
358.1 mA`, and says the 248 mA is **asserted**. `[calc]` If the strip term in
that 248 mA is the 0.13 A realistic-use figure (123 mA quiescent + 130 mA
realistic ≈ 253 mA, which fits the cell to 2 %), then at 45 mA/LED the cell
becomes ~418 mA and **`umbilical-current` moves from 359 mA to ~528 mA — a
settled, tracked figure, 1.47× out.**

That is a claim, not a verdict, precisely because the decomposition is not
written down. **What would settle it:** write the per-branch breakdown of the
`12 V direct` column. Until then nobody — reviewer or checker — can tell whether
the 2.23× propagates into the most-cited current figure in the repository.

**If it does, these move with it, none of them touched** `[repo]`:

- `0005:96` the drop table: 359 mA → 122 mV cable → "**~11.4 V** arrives, **5 %**".
  `[calc]` At 528 mA the cable drop is 180 mV.
- `0005:97` "~4.1 W in typical play" `[calc]` → ~6.1 W.
- `config/figures.yaml:712` `ferrite-bias-impedance`, value
  "~280-310 ohm on FB2", derived off 359 mA against a published bias curve
  (0 A 614 Ω, 250 mA 431, 500 mA 157, 1000 mA 72). `[calc]` At 528 mA FB2 reads
  **~150 Ω**, a quarter of its 600 Ω nameplate rather than half. The entry's own
  conclusion ("either the FB2 requirement is restated at its real operating
  current, or FB2 becomes a physically larger part") gets sharper.
- `0004:276` "+12 V | **~404 mA typical** (45 mA module + **359 mA** instrument)".
- `0004:284` "Series R | Drop at 359 mA"; `docs/reference/pcb-pipeline.md:219`
  and `:282` ("0.053 cents at 359 mA").
- `0004:636` and `0006:642`: "**5.7–7.2 cents** of breath-correlated pitch bend"
  from "360 mA develops an IR drop across that shared length … the current
  varies with the lighting" `[repo] 0004:632–638`. `[calc]` The
  breath-correlated term *is* the LED term, which is 2.23×, so this becomes
  **~12.7–16.1 cents** against a `pitch-cents-budget` whose four candidates span
  0.42–1.35 cents total `[repo] config/figures.yaml:466`. It was already an
  order of magnitude over budget and is now two. `ROADMAP.md:200` already sends
  it to E6/E9 for measurement, so the *action* survives; the magnitude in the
  ADRs is understated.
- `0005:296` "set from below, by the clamp-legal worst case of ~630 mA plus ramp
  current" — clamp-legal is power-defined, so **unaffected**; but if typical play
  is 528 mA the LT1641's worst-case 0.78 A limit `[repo] hardware/bom.csv:66`
  sits only 1.48× above typical play rather than 2.17×.

### 3e. Checked and NOT affected — stated so nobody re-reports it

- **Buck sizing.** `[repo] 0005:184` "umbilical +12V ──┬── WS2815 LED strips
  (direct, no conversion)". The strips never cross a buck. `[repo]
  power-entry-instrument.md:92–96`'s "Buck A … ~680–780 mA / 1000 mA →
  68–78 %" is built from the clamp-legal 5 V column, which is power-defined and
  contains the **matrix**, not the strips. **Unaffected.** (It is still exposed
  to `matrix-led-current`, which is a different slice.)
- **Clamp-legal rows of the load table** (`0005:161`) and the
  "328 mA versus 928 mA" strips-vs-matrix comparison at `0005:165–168`. Both are
  defined by the 3 W budget in watts. **Unaffected.**
- **ROADMAP E1** (`:189`). It measures the **matrix's** unlit driver current
  (~50 mA estimated, bracketed 22–160 mA) and is a `matrix-led-current`
  question. **Unaffected by the strip figure** — but see §2: E1 is also *not*
  where the strip figure can be measured, because `ROADMAP.md:106` says the
  strips arrive at M6.
- **The clamp's own thermal cost** (`0014:199`, "roughly 9 K"). Power-defined.
  **Unaffected.**
- `0005:32`'s "~60 mA per WS2812 at full white" sits in the withdrawn
  battery-option section and is about a 5 V WS2812. **Legitimate history.**
  (Worth noting for its own sake: 60 mA/LED ÷ 3 = 20 mA/channel, and the strip
  table's 20.2 mA/**LED** is suspiciously close. A per-channel figure used as a
  per-LED figure is a candidate mechanism for the original error. `[from memory]`,
  speculative, offered only as a hypothesis.)
- `0014:266–268` "Loop gain is around 0.004, so the effect is **0.4 %** of gain
  compression". `[calc]` 2.23× → ~0.9 %. Conclusion ("a slight softening …
  nothing more") survives. Worth a marker, not a fix.

---

## 4. The `3 K/W` constant — unsourced, unowned, and load-bearing in both directions

`[repo]` `3 K/W` and its spelling `~3 K per watt` occur in exactly three places
corpus-wide: `0014:169`, `0014:205`, `ROADMAP.md:192`. There is **no entry in
`config/figures.yaml`** — I listed all 37 `id:` values and checked. **Nothing
owns it.** Its only provenance marking is `0014:205`: "That figure is a bounding
estimate, not a measurement", which is honest and is not a source.

**Its derivation is stated once and both inputs are contested.** `[repo]
0014:168–169`: "The existing electronics dissipate roughly **5 W** for an
interior rise of **10–20 K**, so call it ~3 K per watt." `[calc]` 10–20 K / 5 W
= 2–4 K/W; 3 is the midpoint, so the arithmetic is fine.

- **The 5 W** is ADR 0005's `Body heat` column, which is bracketed by
  `4.1 W` typical and `4.7 W` typical-plus-WiFi `[repo] 0005:159–160` — and
  `0005:170` says "**None of this is measured.** E6 measures the real draw …
  and every number above is superseded the moment it does."
- **The 10–20 K** has no owner either. `[test]` The checker's own advisory names
  it: `.staleness/report.txt` line 16, `RESTATED, NOT CITED` — "`20 K`  12
  files". `[repo]` Restated in `0001:212`, `0003:202`, `0003:243`, `0003:639`,
  `0006:295`, `0007:210`, `0009:531`, `0014:169`, `key-switch-network.md:121`,
  `power-entry-instrument.md:100`, `0005:313`.

**And the two are circular.** `0007:210–211` calls it "a **documented** 10–20 K
interior rise" and `0005:313` derates a polyfuse hold current "at the
**documented** interior rise" — as if 10–20 K were an independent measured fact.
It is not: it is the *input* to the 3 K/W estimate, which is then used to predict
interior rise. Two documents cite the output of a model as evidence for the
model's input, and eleven more restate it with no register entry to move them if
it changes. This is the exact shape CLAUDE.md §1 exists to prevent, on a number
that now carries an 81 K prediction.

**And 3 K/W is being extrapolated 2.2× past its fitting point.** It was fitted
at 5 W. `0014:174` now applies it at 27 W. Convective and radiative loss both
rise superlinearly with ΔT, so a linear K/W will **overstate** 81 K — probably
substantially. `[from memory]` That does not rescue the design: even a
pessimistic-to-realistic correction leaves the `:174` state far outside the
sensor's +60 °C limit. But the report should be honest that **81 K is not a
prediction, it is 3 K/W taken literally**, and the annotation presents it
without that qualifier.

**Recommendation:** track it. One entry — `enclosure-thermal-resistance`,
`status: blocked`, `owner: docs/decisions/0014-lighting.md`, `candidates:`
`"~3 K/W from 5 W → 10–20 K, both asserted"`, `decided_by:` the M8 soak that
`ROADMAP.md:192` already schedules, `note:` that the model is linear and is
being read 2.2× outside its fitting point. Then `10–20 K` becomes a citation in
twelve files instead of a restatement in twelve files, which is CLAUDE.md §1
applied to the number with the widest reach in the corpus.

---

## 5. The breath fix — six locations changed, two survivals, and the 140 mV re-derived

### 5a. The six changed locations are all correct

`[repo, git show df22096]`:

| location | change | correct? |
|---|---|---|
| `0003:565` | "reaches 4.7 V" → "reaches `sensor-full-scale`" | yes |
| `0005:74` | "outputting **0.2–4.7 V**" → "whose output reaches `sensor-full-scale`" | yes |
| `0005:77` | "reaches 4.7 V with margin" → "clears `sensor-full-scale` with margin" | yes |
| `R-ADCDIV` | "Sensor reaches 4.7V" → "reaches sensor-full-scale" | yes |
| `U-BREATH` | "(766mV/kPa, 0.2-4.7V)" → "(see breath-sensor-slope and sensor-full-scale)" | yes |
| `D-TVS-BREATH` | "top of range is 4.7V … 300mV of margin" → "`sensor-full-scale` … 140mV of margin, NOT the 300mV this row claimed" | yes, and see 5c |

All six cite rather than restate, which is CLAUDE.md §1 done correctly. Each BOM
row is in two files (fragment + generated `hardware/bom.csv`) and both copies
moved `[test]` — `python3 tools/check-staleness.py` reports PASS and its
`merge-bom --check` leg is clean.

### 5b. Two survivals

**(i) `hardware/carrier/breath-adc/breath-adc.md:52` — the retired value, live,
in an arithmetic chain, fifteen lines below a line that was fixed.** `[repo]`

```
worst case, 3V3 at 0 and the clamp holding the pin at ~0.7 V:
  (4.7 − 0.7) / 10 kΩ = 400 µA   against a family-typical ±2 mA  [from memory]
```

`[calc]` With `sensor-full-scale`: (4.86 − 0.7) / 10 kΩ = **416 µA**. The
numeric consequence is trivial (4 %, against a ±2 mA limit); the defect is not.
**Line 37 of the same file was corrected** — it reads
`full scale = 4.86 V × 0.6 = 2.92 V` and carries the citation
`[0.265 and 4.86 from sensor-full-scale]` `[repo] breath-adc.md:37,44`.
`config/figures.yaml:60` holds the pattern **`"4.7 V × 0.6"`**, which is
line 37's *previous* spelling — so the pattern was written from the very line
that got fixed, and the line fifteen lines further down, in the same code fence
family, was not looked at. This is `escape_note_2`'s mechanism verbatim: "A
forbidden list written from the document in front of you cannot catch the
document in front of you."

It escapes all 37 patterns: none matches `(4.7 − 0.7)`. `[test]` The checker
reports PASS. The minus sign is **U+2212**, not ASCII — `cat -A` gives
`(4.7 M-bM-^HM-^R 0.7)` — so a pattern written with a hyphen would miss it
again. **Suggested pattern, in the spelling of the file it must match:**
`"(4.7 − 0.7) / 10 k"`.

**(ii) `hardware/bom.csv:42` and `hardware/interfaces/breath-sense-link/bom.csv:2`
(`U-BREATH`) — "Full scale CONFIRMED as 0.2 to 4.8V on the cover page."**
**The sibling slice's claim is CONFIRMED**, at exactly the line it named.

This is the *other half* of the same row. `df22096` fixed the row's
`(766mV/kPa, 0.2-4.7V)` clause and left this clause, ~700 characters later in
the same cell, untouched `[repo, git]`.

It is not merely stale, it is an **assertion against the register**.
`config/figures.yaml:119` `[repo]`: the cover-page line "0 to 6 kPa, 0.2 to
4.8 V Output" … "**CONTRADICTS the transfer function printed inside the same
document. Table/transfer function wins over the marketing blurb.**" The
`false_positive_note` at `:99` permits *quoting* the cover page — "the ADR 0003
GP-vs-DP comparison row does exactly that, **labelled 'cover page, both parts',
and carries refutation wording**" — and `0003:102` and `0003:118` do it properly
`[repo]`. The `U-BREATH` row instead writes **`CONFIRMED`**, which asserts the
refuted value as settled fact, in the most-cited file in the repository, with no
refutation wording anywhere near it.

**It escapes every pattern, and on the spelling the sibling named.** The
register holds `"0.2-4.80 V"`, `"0.2 – 4.80 V"`, `"0.2–4.80 V"`,
`"0.2 → 4.8 V"`, `"0.2 to 4.8 V out"`, `"| 4.800 V |"`. The row spells it
**`0.2 to 4.8V`** — two significant digits and **no space before the V**. This
is CLAUDE.md §2's first trap, in the same CSV, on the same figure, in the same
commit that wrote the trap down: `escape_note_3` records "three BOM rows …
**each spelling it without the space before the V**" and fixed the `4.7`
spelling in all three while the `4.8` spelling in one of them survived.

**Suggested pattern:** `"CONFIRMED as 0.2 to 4.8V"` — words plus number, so it
cannot fire on `0003:102`/`:118`, which quote the cover page legitimately.
`[test]` I verified nothing else in the corpus carries a bare `4.8V`: the only
other `4.80` hits are `0005:103` (an LM317 rail, a different quantity, exactly
as `false_positive_note` warns) and the two labelled ADR 0003 quotations.

**(iii) Nothing else survives.** `[test]` I grepped the corpus (`hardware/**`,
`docs/decisions/**`, `docs/reference/**`, `config/**`, `firmware/**`,
`README.md`, `ROADMAP.md`) for every spelling of the retired value — `4.7 V`,
`4.7V`, `4.8 V`, `4.8V`, `4.80`, `0.200 V`, `0.2 V at rest`, `+ 0.04`,
`300 mV`, `300mV` — and every other hit is legitimate:

- `breath-receive-stage.md:133`, `:201`, `breath-output-stage.md:45`, `:61`:
  **−4.7 V** at the in-amp — a different quantity and negative, the decoy
  `escape_note_3` documents.
- `0005:97`, `:100`: **~4.7 V** as what a 5 V umbilical would arrive at — the
  second documented decoy.
- `D-USBOR` (`hardware/bom.csv:7`): the 5 V rail after a Schottky.
- `0.25–4.75 V` (pitch/mod DAC window), `4.75–5.25 V` (the MPXV4006DP's own
  supply spec — `config/figures.yaml:351` already carries the
  `false_positive_note` for it), `4.7 µs`, `4.7 kΩ`, and the KS33 geometry
  coordinate `(−4.4, 4.7)`.

**Per CLAUDE.md §2's counterpart rule — most hits will be legitimate — that is
16 legitimate hits against 2 defects.** Do not add a bare `4.7` or `4.8` pattern.

### 5c. The 140 mV, re-derived independently

`[calc]` A 5 V TVS array's `V_RWM` taken as 5.00 V, minus `sensor-full-scale`:

```
5.000 V − 4.864 V = 0.136 V  →  140 mV   (stated)
5.000 V − 4.700 V = 0.300 V  →  300 mV   (retired, and what the row said)
```

**The 140 mV is arithmetically right and the direction is right.** Two things it
does not say, the second material:

**(i) "a 5V array's `V_RWM`" is ambiguous, and this repo has documented both
conventions.** `[repo] hardware/bom.csv:48` (`U-TVS-SPI`) quotes onsemi
**ESD7104: `V_RWM 5.0V`, `V_BR 5.5V`** — which gives exactly 140 mV. But
`[repo] datasheets/MANIFEST.csv:50` records the banked SP0504BAHT as
"**reverse standoff voltage 5.5 V min at I=10uA**" — which would give
`[calc]` 640 mV, 4.6× more. The row does not say which convention it means, and
the two 5 V arrays this repository has actually documented disagree.

**(ii) The 140 mV is typical-against-nominal, and the sensor's own specified
accuracy is larger than it.** `[datasheet MPXV4006DP.pdf p.3–4]` `Voff` is
specified **0.152 / 0.265 / 0.378 V** min/typ/max, and accuracy is
**±2.46 %VFSS with auto zero**, **±5.0 %VFSS without**. `[calc]` 2.46 % × 4.6 V
= **±113 mV**; 5.0 % × 4.6 V = **±230 mV**. So:

```
top of range, typical            4.864 V   → 136 mV of margin
top of range, +2.46 % FSS        4.977 V   →  23 mV of margin
top of range, +5.0 % FSS         5.094 V   → NEGATIVE — above a 5.00 V V_RWM
```

**The worst case the datasheet specifies puts the sensor's output above a 5 V
array's standoff outright.** (Supply tolerance does not add much here: the
sensor runs from a REF5050 5.000 V `[repo] 0003:475–481`, so the ±5 % of
`VS 4.75/5.0/5.25` is not in play — that is a genuine strength of the reference
decision and is worth saying.) The row's conclusion — **use a 12 V part** — is
therefore *more* firmly right than the row argues, and the "140 mV" it now
quotes is a best case presented without that word. **I would add "(typical;
±113 mV of specified FSS accuracy sits on top of it, which takes the worst case
negative)"** — one clause, on one line, in the row.

### 5d. One edit-in-place defect in the same row

`[repo]` The post-fix sentence reads:

> BREATH's normal top of range is sensor-full-scale against a 5V array's V_RWM
> - 140mV of margin, NOT the 300mV this row claimed while it was using a
> retired 4.7V on the project's DC-accurate output, with 1.5uA of leakage into
> a 1k output resistor.

The refutation clause was spliced into the middle of the original sentence, so
"**on the project's DC-accurate output**" — which modified *the margin* — now
modifies "a retired 4.7V". Cosmetic, but this wave exists to catch exactly what
in-place edits do to the sentence around them. The retained `4.7V` string is
correctly excused by the adjacent "retired", per
`docs/reference/repo-maintenance.md:64–67`.

---

## 6. `D-TVS-BREATH` — three numeric claims, one BLOCKED manifest row, zero markers where a reader looks

`[repo] hardware/bom.csv:44` and `hardware/interfaces/breath-sense-link/bom.csv:4`,
identical text, `status` = **`candidate`**. The three claims about the absent
PESD12VS1UB document:

| claim | in the row? | marked unsourced in the row? |
|---|---|---|
| **12 V standoff** (`V_RWM` of the PESD12VS1UB) | "12V STANDOFF, NOT 5V"; "PESD12VS1UB or equivalent 12V-standoff" | **no** |
| **140 mV of margin** against a 5 V array's `V_RWM` | "140mV of margin" | **no** — and see 5c(i): the premise `V_RWM = 5.00 V` is itself unsourced and contradicted by one of the two 5 V arrays this repo has banked |
| **1.5 µA of leakage** into the 1 kΩ output resistor | "with 1.5uA of leakage into a 1k output resistor" | **no** |

`[repo] datasheets/MANIFEST.csv:96` — the BLOCKED row added by the same commit —
says precisely this, and says it well:

> D-TVS-BREATH. NOT FETCHED and previously not recorded at all, which is the
> state CLAUDE.md 3 exists to prevent: **the BOM row makes three numeric claims
> about this part** — a 5V array's V_RWM, the margin against it, and 1.5uA of
> leakage — **and none of them has a document behind it.** … BLOCKING on the
> datasheet. The 12V-standoff CONCLUSION rests on ADR 0003's +12V-buffer
> argument and needs no datasheet; the three numbers do.

**So the gap is recorded honestly and completely — in the manifest. It is not
recorded in the BOM row, which is where the reader is.** That is this project's
named failure mode in its purest form: the fix landed where the editing was
happening, not where the reader looks.

Three specific things are missing, against rules the repo already states:

1. **CLAUDE.md, Hardware conventions:** "Mark unresolved things `TBD`/`open`
   **with what decides them**. Two BOM rows are deliberately blocked on a
   datasheet and say so; that is correct, not a defect." `[repo]` I checked
   every row of `hardware/bom.csv`: **`D-TVS-BREATH` is not one of the rows
   that says so.** Its `status` is `candidate` and the word BLOCKED does not
   appear in it. There are now three rows blocked on a datasheet and two of them
   say so.
2. **CLAUDE.md §3:** "Mark provenance on every figure so the weak ones are
   visible." All three numbers are unmarked. The row's own style elsewhere shows
   it knows how — `U-BREATH` two rows up writes "*** TcOffset IS UNSOURCED IN
   BOTH DIRECTIONS: ***" `[repo]`, and `U-TVS-SPI` writes "the 0.98W
   sustained-fault figure this row's protection budget assumes **has never had a
   source**" `[repo] hardware/bom.csv:48`. Both are the right pattern. This row
   does not use it.
3. **The stakes are in the manifest and not in the row:** qty 2, drawn, on the
   DC-accurate analog output, **unretrofittable after bonding**. A reader of the
   BOM row learns none of that.

`[calc]` For completeness, the one consequence nobody has written down: 1.5 µA
through the 1 kΩ `R-SER-BREATH-INST` `[repo] breath-sense-link.md:146` is
**1.5 mV** of DC error on a channel whose pitch sibling budgets in
hundredths of a cent. That is the number the leakage claim exists to bound, and
it is not stated in either place.

**What I would do:** add to the row, verbatim in its own style —
`*** THREE NUMBERS HERE HAVE NO DATASHEET: *** the 12V standoff, the 140mV
margin (and the 5.00V V_RWM it is computed against - the banked SP0504BAHT
specifies 5.5V min, the ESD7104 5.0V) and the 1.5uA leakage (= 1.5mV into
R-SER-BREATH-INST). BLOCKED in datasheets/MANIFEST.csv - PESD12VS1UB. The
12V-standoff CONCLUSION needs no datasheet (ADR 0003's +12V-buffer argument);
these three numbers do. Qty 2, drawn, unretrofittable after bonding.` — and set
`status` to `open`. Edit the **fragment**, then re-run `tools/merge-bom.py`
(CLAUDE.md, Hardware conventions; 11 columns, CRLF).

---

## Findings, node-indexed

| # | node / ref | finding | severity | provenance |
|---|---|---|---|---|
| D13-1 | ADR 0014 clamp, `:193`–`:201`, `:257` | At 45 mA/LED, "realistic use" is 3.6 W and the ~3 W clamp is **below** it, not twice it. Four headroom claims invert. Untouched. | **high** | `[calc]`, `[datasheet WS2815 p.3]` |
| D13-2 | `strip-led-current` (no such figure) | The refuted figure got a prose annotation but **no register entry, no `forbidden` patterns and no ROADMAP measurement row** — so the checker cannot see it and the annotation's own "needs measuring" prescription names a measurement that does not exist. | **high** | `[repo]`, `[test]` |
| D13-3 | `hardware/bom.csv:42` / `breath-sense-link/bom.csv:2` (`U-BREATH`) | "Full scale **CONFIRMED** as 0.2 to 4.8V" — the retired value asserted as settled, in the most-cited file, escaping all 37 patterns on the no-space spelling. Sibling slice's claim confirmed. | **high** | `[repo]`, `[test]` |
| D13-4 | ADR 0014 `:174`, `:175` | Thermal table unmarked; `:175` (~17.7 W / ~53 K) is not mentioned by the annotation and becomes ~40.5 W / ~122 K. `:174`'s state exceeds the WS2815's own +85 °C `Topt` and the sensor's +60 °C. | **high** | `[calc]`, `[datasheet WS2815 p.2, MPXV4006DP p.4]` |
| D13-5 | `umbilical-current` (359 mA) | Probably 1.47× low (~528 mA) if the strip realistic-use term propagates — and **cannot be checked**, because the `12 V direct` column is asserted with no written decomposition. Eight downstream statements ride on it, incl. `ferrite-bias-impedance` and the 5.7–7.2 cents pitch term. | **high** (unresolved) | `[calc]`, `[repo]` |
| D13-6 | `3 K/W`, `10–20 K` | Neither is tracked or owned; restated in 12 files; the pair is **circular** (two ADRs cite the model's output as evidence for its input); and 3 K/W is read 2.2× past its fitting point. | **medium-high** | `[repo]`, `[test]` `.staleness/report.txt:16` |
| D13-7 | `breath-adc.md:52` | Retired 4.7 V live in an arithmetic chain, 15 lines below a line the same commit fixed; the register's `"4.7 V × 0.6"` pattern was written from that fixed line. U+2212 minus. | **medium** | `[repo]`, `[test]` |
| D13-8 | `D-TVS-BREATH` | Three unsourced numbers, `status: candidate`, no marker in the row. The gap is recorded fully — in the manifest, not where the reader is. Two of three blocked-on-datasheet rows say so; this is the third. | **medium** | `[repo]` |
| D13-9 | ADR 0014 `:141`–`:143` | "2.1 mA reproduces ADR 0005's 123 mA figure **exactly**" is false: 2.1 × 50 = **105 mA**, 15 % out. The annotation's own corroborating sentence. | **medium** | `[calc]`, `[datasheet WS2815 p.3]` |
| D13-10 | ADR 0014 `:131`–`:132` | Five of six table cells uncorrected, incl. the whole 30/m row and the 0.13 A cell the rest of the corpus reads. | **medium** | `[calc]` |
| D13-11 | ADR 0005 `:162`, `:288`–`:298` | Latched-full-white is ~2.8 A, not ~1.5 A — 1.8× the etherCON contact rating on a single conductor, not marginally over. Conclusion strengthens; magnitude understated. | **medium** | `[calc]`, `[repo] figures.yaml:334` |
| D13-12 | ADR 0014 `:122`, `C-STRIP-BULK` | "hundreds of milliamps" of PWM swing is up to 2.25 A. Conclusion strengthens; the 470–1000 µF has no written derivation. | **low-medium** | `[calc]`, `[repo]` |
| D13-13 | `D-TVS-BREATH` prose | The refutation clause was spliced mid-sentence; "on the project's DC-accurate output" now modifies the wrong noun. | **low** | `[repo]` |
| D13-14 | `unplaced.csv:5` (`LED-SIDE`) | The WS2815 tape's only BOM row carries no current figure and no marker — where somebody ordering the part looks. | **low** | `[repo]` |
| D13-15 | ADR 0014 `:182`, `matrix-led-current` | The precedent this fix copied is itself partial: 960 mA survives unmarked 197 lines above its own refutation, and the register entry has `forbidden: []`. Corroborates D13-2's mechanism. | **low** (other slice's node) | `[repo]` |

## What would settle the uncertain ones

- **D13-5** — write the per-branch decomposition of ADR 0005's `12 V direct`
  column. One table. It settles D13-5 and D13-9 together, and it is the single
  highest-value edit named in this report.
- **D13-1 / D13-2 / D13-4 / D13-10** — one current probe on one strip's +12 V
  feed at commanded full white, at M6. Also the honest resolution of the tape-vs-IC
  tension in §1a.
- **D13-6** — the M8 soak `ROADMAP.md:192` already schedules, with the interior
  rise recorded as a measurement rather than restated as an assumption.
- **D13-3 / D13-7 / D13-8** — repo-internal; no measurement needed.

`[repo]` Report only. Nothing in the corpus was modified. `[test]`
`python3 tools/check-staleness.py` → PASS; `python3 tools/verify-datasheets.py`
→ 0 problems. Both were passing before this slice and still are, which is the
point: **every finding above is invisible to both.**
