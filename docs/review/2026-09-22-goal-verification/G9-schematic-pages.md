# G9 — the schematic pages, read as engineering documents

**Slice:** G9. **Date:** 2026-09-22. **Cold:** nothing under `docs/review/` was
opened. I listed no review directory and read no review file, including the
wave README that briefed me (the brief arrived as a message).

**Revision measured against:** `a4b80b1`, pinned. See *Provenance and the
freeze* at the bottom — the working tree moved under this slice and every
`[repo]` claim below was re-verified against a pinned clone at `a4b80b1`
(`/tmp/claude-0/g9pin`), which `diff -rq` shows byte-identical to
`hardware/**` and `config/figures.yaml` in the working tree at the time of
writing.

**Scope:** all 23 circuit pages, the 3 board pages (`carrier.md`,
`cluster-boards.md`, `module.md`), `hardware/README.md`,
`hardware/interfaces/README.md`, all 23 `circuit.yaml`, all 13 `notes.md`,
`hardware/bom.csv`, `hardware/unplaced.csv` and `config/figures.yaml`.

**Method:** every inline derivation recomputed in Python; every ASCII drawing
scanned for column drift by extracting the character positions of
`│├┤┬┴┼┌┐└┘` per line and looking for a rail that jogs; every `## Interfaces`
table's `Peer` column parsed and matched against its `circuit.yaml`
`circuit:` edges in both directions; every refdes in a page matched against
`hardware/bom.csv` and every BOM row matched back to the page that derives it.

**Headline:** the BOM was trimmed this session and the pages were not, and it
shows. **Sixteen of the findings below are page-versus-BOM or page-versus-page
disagreements about a component value, a reference designator or a
quantity** — four of which would produce a wrong board rather than a confusing
document. One derivation is wrong by 2×, one by ~2000×, and one live
electrical claim (`POT-OFFSET` centre) is wrong by 0.53 V and is contradicted
on another page that is right.

**What is in good shape, stated so the next wave does not re-check it:** all
23 `## Interfaces` tables match their `circuit.yaml` `circuit:` edges exactly,
in both directions, with no unresolved id and no missing back-edge `[test]`
(script in *Method*, run against the pinned clone). `merge-bom.py --check`
passes: `bom.csv: checked 140 rows from 26 fragments | 0 problems` `[test]
python3 tools/merge-bom.py --check`. The `mod-channels.md` topology argument
that `CLAUDE.md` §5 names as the worst recorded premise-drift has been
repaired properly — `mod-channels.md:160-168` renames the trigger to the DAC's
own power-on reset and `LK-CLR`, and the same repair is carried in
`mod-channels/notes.md:101-106` and `breath-receive-stage/notes.md:68-75`.

---

## A. Findings that would produce a wrong board

### G9-1 — `R-FB` is 40 kΩ in the drawing and 40.2 kΩ in the parts list, and every derived number follows the drawing

**Node:** `R-FB` / `R-BREATH-SUM`, `hardware/module/breath-output-stage/breath-output-stage.md:82` vs `:149`.

The drawing says `[R-FB 40k]` `[repo] breath-output-stage.md:82`. The Values
table says **40.2 kΩ 1 %** `[repo] :149`. `hardware/bom.csv` says
`R-BREATH-SUM,...,10k / 40.2k 1%,...,qty 2` `[repo] hardware/unplaced.csv:31`.

The offset table at `:122-126` is computed with **40 kΩ**, not 40.2 kΩ
`[calc]`:

```
V_out(offset) = −R_FB · ( V_wiper/R_OFF  −  12/R_OFFNEG )
   wiper 0 V     : 40.0k × 12/95.3k = +5.037 V   page says +5.04   ✓ at 40k
                   40.2k × 12/95.3k = +5.062 V   would be +5.06    ✗
   wiper 5.21 V  : −40.0k × (5.21/21.0k − 12/95.3k) = −4.887 V  page says −4.89 ✓ at 40k
                   −40.2k × (same)                  = −4.911 V  would be −4.91 ✗
```

The same 40 kΩ is used again at `:138` (`40k/95.3k × 50 mV = 21 mV`) `[calc]`
40/95.3 × 50 = 20.99 mV. **40 kΩ is not an E96 1 % value**, so the drawing and
three derived numbers are all against a part that cannot be ordered. Either
the drawing is stale or the Values table and the BOM are.

### G9-2 — `POT-OFFSET` does not sit at zero at centre; it sits at +0.60 V, and the page that says otherwise dismisses the reason

**Node:** `POT-OFFSET` wiper / `R-OFF`, `breath-output-stage.md:122-134` against `panel.md:74-76`.

`breath-output-stage.md:125` gives **Centre | 2.605 V | +0.07 V** and `:132-134`
says *"This wiper does **not** need buffering. Its source impedance varies from
0 at either end to `R/4` at centre, so the endpoints are exact and the middle
is slightly non-linear in rotation. For an offset knob that is feel, not
error."*

The `R/4` is not a rotation non-linearity, it is a **series impedance in the
offset leg**, and the page's own offset table omits it `[calc]`:

```
POT-OFFSET 10 kΩ, top at dac-rail (5.21 V), bottom at AGND.
At centre: V_oc = 2.605 V, R_s = p(1−p)·10k = 2.5 kΩ.
  I(R-OFF)    = 2.605 / (21.0k + 2.5k) = 110.85 µA     (page uses 2.605/21.0k = 124.05 µA)
  I(R-OFFNEG) = −12 / 95.3k            = −125.92 µA
  net = −15.07 µA  →  V_jack = 40k × 15.07 µA = +0.603 V
True zero crossing:  1.2592p² + 3.9508p − 2.6443 = 0  →  p = 0.567
                     i.e. 6.7 % of travel past centre; on a 270° pot, 18.1°
```

That reproduces **`panel.md:75-76`'s "+0.605 V" and "~20° past centre"** to
three digits `[calc]`, and `breath-response-shaper.md:269-270` repeats the
same "~20° off its true zero". So two live pages say the detent is wrong and
one live page says it is right, and the one that says it is right is the one
that owns the circuit. `POT-OFFSET`'s BOM row still reads *"bipolar, zero at
centre"* `[repo] hardware/bom.csv`, and `breath-output-stage.md:178-180`
proposes a centre-detent part on the strength of it.

**0.53 V on a ±5 V offset control, at the one position the panel is being
detented for.** Pick one: buffer the wiper (one op-amp half, which
`panel.md:76` says 10HP made room for), or re-derive the offset table with
`R_s` in it and withdraw "zero at centre".

### G9-3 — the entry bulk is `4 × 47 µF` on the drawing and explicitly *not* on the BOM row

**Node:** `C1`–`C4` / `C-BULK-RAIL`, `hardware/module/power-entry/power-entry.md:42,49,75,77,190`.

The drawing labels all four as `[C1 47µF]`, `[C2 47µF]`, `[C3 47µF]`,
`[C4 47µF]` `[repo] power-entry.md:42,49,75,77`, and *Still open* says
**"Entry bulk is 4 × 47 µF"** `[repo] :190`. The BOM row opens with
**"NOT 47uF on every rail"** and specifies `100uF (+12V) / 47uF (-12V, +5V)`
`[repo] hardware/module/power-entry/bom.csv:9`. A netlist or a stuffing list
taken off this drawing under-fits the +12 V rail by half.

The same *Still open* bullet's argument (*"2–5× the surveyed norm of
10–22 µF"*) is computed from the drawing's 47 µF; at the BOM's values the
total is 294 µF, not 188 µF, and the multiple is larger still.

Related, and worth a separate look by whoever owns the BOM: that row's note
justifies the split on *"the LM317's divider, the DAC **and the comparator**"*
— the LM311 comparator is deleted (`link-supervision.md:1-8`) `[repo]`.

### G9-4 — `R-LED-SER` has three different values in three places

**Node:** `R-LED-SER`, `hardware/carrier/led-strip-drive/led-strip-drive.md:35,41,99,114`.

Drawing: `[R-LED-SER 220R]` and `[220R]` `[repo] :35,:41`. Prose: *"100–330 Ω
at the buffer"* `[repo] :99`. Component table: **100–330 Ω** `[repo] :114`.
BOM: **330R 1%** `[repo] hardware/carrier/led-strip-drive/bom.csv:4`. The
drawing is the only place that commits to a number and it is the one number
none of the other three carries.

### G9-5 — `R-OUT-PROT` is specified at two different power ratings on two pages

**Node:** `R-OUT-PROT`, `pitch-stage.md:132` vs `breath-output-stage.md:153`.

`pitch-stage.md:132`: *"1 kΩ 1 %, **1206 ≥250 mW**"*. `breath-output-stage.md:153`:
*"1 kΩ, 1206 **≥500 mW**. Shared spec with the other five outputs"*. BOM:
`R-OUT-PROT ... 1k 1%, >=500mW ... qty 6` `[repo] hardware/bom.csv`. It is one
part, qty 6, so `pitch-stage.md` is the odd one out. (The ≥250 mW spelling is
correct for a *different* part — `R-SER-BREATH-INST`, BOM `1k 1%, 1206
>=250mW` `[repo]`, matching `breath-sense-link.md`'s `R1` row — which is
probably how it got copied across.)

### G9-6 — four refdes the drawings use do not exist in `bom.csv`, and the parts they name do

**Nodes and where drawn:**

| Drawn as | `bom.csv` row | Where |
|---|---|---|
| `C-TIMER` | `C-TIMER-LOADSW` | `power-entry.md:63`, `umbilical-load-switch.md:21,98,141,241`, `panel-led.md:50` |
| `C-GATE` | `C-GATE-LOADSW` | `power-entry.md:64`, `umbilical-load-switch.md:21,79,206,256,266,300,307` |
| `J-UMB` | `J-UMBILICAL` | `carrier.md:50,116,134,213-216`, `power-entry-instrument.md:19-20,30,52`, `spi-link.md`, `breath-sense-link.md`, `breath-receive-stage.md:56,62`, `breath-adc.md` |
| `N-FET` (unlabelled) | `Q-LOADSW` | `power-entry.md:62` |

`[repo]` for all four, verified against the pinned `hardware/bom.csv` ref list.
`R-GATE-COMP`'s own BOM note says *"in series with **C-GATE-LOADSW**"*
`[repo]`, so the BOM is internally consistent and the pages are not.

`Q-LOADSW` is the sharpest of the four: `umbilical-load-switch.md:319-322` says
*"The pass FET is its own BOM row, `Q-LOADSW`, and the part is not chosen. It
was carried inside `U-LOADSW`'s `part` field ... until 2026-09-22"* — the row
was created this session and the drawing, which `power-entry.md:13` states is
*"unchanged"*, still shows an anonymous `N-FET`.

`hardware/README.md` says the Interfaces tables are what *"a PCB netlist is
transcribed from"* and that *"each row names the drawing's own spelling so a
reader can match the two"* `[repo]`. Four of the drawings' spellings match
nothing.

### G9-7 — the four resistors `breath-output-stage.md` derives are filed in `unplaced.csv` as parts no page derives

**Node:** `R-IN`, `R-FB`, `R-OFF`, `R-OFFNEG` = `R-BREATH-SUM`, `R-BREATH-OFF`.

`hardware/unplaced.csv` rows 31 and 32 are `R-BREATH-SUM` (10k / 40.2k, qty 2)
and `R-BREATH-OFF` (21.0k / 95.3k, qty 2) `[repo]`. `hardware/README.md:107-109`
defines that file as *"the BOM rows **no schematic page derives**… a part
nobody has drawn"* `[repo]`. `breath-output-stage.md:59-91` draws all four and
`:105-140` derives every one of their values.

`grep -rn "R-BREATH-SUM\|R-BREATH-OFF" hardware/*/*/*.md` returns nothing
`[test]` — the page uses local labels (`R-IN`, `R-FB`, `R-OFF`, `R-OFFNEG`)
and nothing connects them. This is exactly the failure `hardware/README.md:96-104`
says was fixed for sixteen parts on 2026-09-21 (*"assignment matched on
reference designator while those parts are drawn under a local label"*), and
`module.md:38-45` reports it as closed. Four rows were missed.

### G9-8 — `R-BIAS-INAMP`'s BOM row lives with the circuit whose dependency on it was *proved false*

**Node:** `R-BIAS-INAMP` (`R4`/`R5`, 1 MΩ ×2).

`hardware/module/pitch-stage/bom.csv` holds `R-BIAS-INAMP` `[test] grep -l
"R-BIAS-INAMP" hardware/*/*/bom.csv`. Its BOM description is *"Common-mode
bias return, one per in-amp input"* `[repo]` — the breath in-amp's `R4`/`R5`,
drawn in `breath-receive-stage.md:79` and derived in
`breath-sense-link.md`'s component table and CMRR argument.

`hardware/README.md:73-77` lists `pitch-stage → R-BIAS-INAMP` as one of three
edges *"verified false by a cold reviewer"* — *"the page names it as an
explicit **contrast**"*. The `refdes:` edge was kept (README says so), but the
**BOM row itself** was filed on the strength of that same false co-mention,
and `hardware/README.md:87-90` requires a row to live *"with the circuit whose
page derives its value"*. It should be under `interfaces/breath-sense-link/`
or `module/breath-receive-stage/`.

### G9-9 — the `BREATH` jack clamp is two different parts on two pages, and one of them has no quantity for it

**Node:** clamp at `BREATH_OUT`.

`breath-receive-stage.md:110` draws `[D-CLAMP-BREATH BAV99]── ±12 V`
immediately above `BREATH jack` `[repo]`. `breath-output-stage.md:84` draws
`[D-JACK-CLAMP BAV99]── ±12 V` at the same node `[repo]`.

`D-CLAMP-BREATH` is **qty 2**, described as *"Clamp diodes on the BREATH and
AGND legs at the in-amp input"* `[repo] hardware/bom.csv` — both are consumed
by `breath-receive-stage.md:67`. `D-JACK-CLAMP` is qty 6, one per CV output
`[repo]`, which is the right part for the jack. So the third
`D-CLAMP-BREATH` on `breath-receive-stage.md:110` is a part that is drawn,
named and not budgeted, sitting on a net another page already clamps.

### G9-10 — the `±1 %` tolerance the CMRR budget depends on is not in the BOM

**Node:** `C_cm` ×2 / `C-FILT-BREATH`.

`breath-sense-link.md` (*"`R1` is a 1206, and it has a twin"*): *"**And `C_cm`
needs a tolerance, which nothing specifies.** At ±5 % the common-mode
capacitor mismatch alone gives ~46 dB; ±1 % is needed to clear 60. Specify
**±1 % C0G** on the two 1.5 nF parts."* `[repo]`.

`C-FILT-BREATH`'s BOM row is `15nF C0G (diff) + 1.5nF C0G (cm x2)`, qty 3,
with no tolerance `[repo] hardware/bom.csv`. The page states the requirement
and the BOM still does not carry it, so the part ordered clears 46 dB against
a 60 dB budget.

### G9-11 — `U-RESP` is a seventh OPA2197 package; every page says there are six

**Node:** `U-RESP` vs `U-OPA-PITCH`.

BOM: `U-OPA-PITCH` qty **6** OPA2197 SOIC-8, *and separately* `U-RESP` qty 1
OPA2197IDR SOIC-8 `[repo] hardware/bom.csv`.

`breath-output-stage.md:156-158`: *"**Ten of twelve halves used across the
module, two spare**"* — twelve halves is six packages `[calc] 6×2=12`.
`breath-response-shaper.md:313`: the shaper costs *"**Both remaining OPA2197
halves**"* — i.e. it fits in the existing six. `breath-receive-stage.md:172`:
*"`U-OPA-PITCH` goes to six packages"*. `power-entry.md:43` labels the analog
rail *"OPA2197 ×6, INA828"*.

I recounted the halves `[calc]`: receive `REF` buffer 1, output-stage gain
buffer + summer 2, pitch `V_ref` follower + main 2, mod ch7 follower 1 + four
channels 4 = **10 of 12**, ✓ matching `breath-output-stage.md`. The shaper
takes the last two. So `U-RESP` is either a seventh package nobody's page
accounts for, or the shaper's two halves double-booked.

### G9-41 — the LM317's `ADJ` bypass is not drawn, and it is half of a qty-2 part the rail-noise reasoning depends on

**Node:** `C-REG-ADJ`, `hardware/module/power-entry/power-entry.md:45-47`.

The drawing shows the LM317 with its `150R/475R` divider and a single
`[C 1µF]` on the output `[repo] power-entry.md:47`. `grep -n "ADJ"
power-entry.md` returns one hit, and it is the words *"line regulation"* at
`:105` `[test]` — **the `ADJ` pin's bypass capacitor is nowhere on the page.**

`C-REG-ADJ` is **qty 2**, *"LM317 ADJ bypass **and** output cap"*,
`10uF / 1uF ceramic or tantalum` `[repo] hardware/module/power-entry/bom.csv:7`,
and that row's note is explicit about what the missing half buys:
*"ADJ bypass drops output noise to ~50uV RMS … ripple rejection goes from 65dB
typ to 66 min / 80 typ **WITH a 10uF capacitor from ADJUSTMENT to ground**"*
`[repo]`.

So the 10 µF is the ADJ bypass and the 1 µF is the output cap; the drawing
carries the 1 µF and not the 10 µF. The page's own rail-noise argument at
`:101-112` (the 120 mV → AVDD chain, G9-24) rests on the LM317 attenuating
what arrives at it, which is the pin that is not drawn. A board stuffed from
this drawing gets 65 dB where the argument assumes 80.

### G9-12 — `R-BIAS-DAC` qty 6, and only one of the six is drawn

**Node:** `R-BIAS-DAC`.

BOM: qty 6, *"DC bias path to ground at every DAC output pin"* `[repo]`.
`pitch-stage.md:322-326` derives and places one (*"at the **DAC pin**, not
after `R-OPAMP-IN`"*). `mod-channels.md` never names it and its drawing
(`:38-65`) shows none on `DAC ch2` or `DAC ch7` `[repo]`. Five of the six sit
on nets `mod-channels` owns and that page does not know they exist — the
mirror of G9-7.

---

## B. Drawings that have drifted out of alignment

All positions below are 0-based character columns of box-drawing glyphs,
extracted per line by script `[test]` and re-verified against the pinned clone.

### G9-13 — `power-entry.md`: the LT1641 box has three different right edges and the branch into it lands three columns off

**Node:** `U-LOADSW` box and the `PWR_GND` branch, `power-entry.md:49-65`.

```
line 49  ...──[C2 47µF]──┬────  PWR_GND (star)     ┬ at col 45
line 50                  │                          │ at col 46     ← already off by 1
line 51   ┌─────────────┴──────────────┐            ┴ at col 42     ← off by 3–4
line 54   ┌────┴────┐                         box right edge col 46
line 55   │ VCC SENSE│                         box right edge col 47
line 56-58                                     box right edge col 47
line 59   │ TIMER GATE├──┬──[R-GATE-SER 10Ω]  box right edge col 48
line 61   └──┬────┬──┘                         box right edge col 47
```

The `┴` on line 51 is the branch point for the whole load-switch block and it
does not line up with the `│` above it. `│ VCC SENSE│` at line 55 has no gap
before its right wall — the classic *label inserted without re-padding* — and
`│ TIMER GATE├` at line 59 pushes it one further. This is the only drawing for
**three** circuits (`power-entry`, `umbilical-load-switch`, `panel-led`), all
three of which say it is *"one drawing"* and *"unchanged"*.

Also `[C-TIMER 10µF]│` at line 63 puts a `│` at col 52 where the rail it
belongs to is at col 51 on lines 59-61 `[test]`, and the `┼` at col 51 on line
65 therefore has nothing above it.

### G9-14 — `breath-receive-stage.md`: the clamp line connects to nothing, and the INA828 box is one cell narrow at the top

**Node:** `D-CLAMP-BREATH` and the INA828, `breath-receive-stage.md:53-113`.

- **Line 67** — `[D-CLAMP-BREATH] BAV99 to ±12 V, both legs  ◄──────────┼─┤` —
  its `┼` and `┤` are at cols **85 and 87** `[test]`. The two conductors it is
  clamping are at cols 68 and 70 on every line above and below it. The clamp
  is drawn 17 columns away from the pair it clamps.
- **Line 62** (`analog star ──[R1b 1k]── AGND (pin 2) ──┐ │`) has its glyphs
  at cols **67, 69** against **68, 70** on lines 63-66 `[test]` — off by one,
  and `R1b` is the part that was added to this drawing.
- **Line 57** has a `│` at col **72** against col 70 on lines 56, 58-61 — off
  by two, on the `↓ to IN−, via R3` annotation line.
- **Line 81** has col **64** against col 63 on lines 75-80 and 82.
- **INA828 box:** top border `┌──▼───────▼──┐` runs col 33→**47** (line 83);
  the sides and the bottom `└──────┬───────┘` run col 33→**48** (lines 84-90)
  `[test]`. The box's lid is one cell narrower than its body.

### G9-15 — `pitch-stage.md`: the `C-FB-PITCH` rail is off by two, and the reason is the value change this page documents

**Node:** `C-FB-PITCH`, `pitch-stage.md:46`.

The right-hand feedback rail sits at col **59** on lines 45, 47, 49, 51, 52;
on line 46 it is at col **61** `[test]`. Line 46 is
`├──[C-FB-PITCH 2.2nF]──────────┤`. `1nF` → `2.2nF` is exactly two characters
wider, and `pitch-stage.md:178` records that value change ("This row said
**1 nF / ~16 kHz** until 2026-09-21; the value went to 2.2 nF … and this row
did not follow"). The drawing did not follow either.

### G9-16 — `breath-output-stage.md`: a stray box bottom, and the output rail jogs one column

**Node:** gain buffer, `breath-output-stage.md:59-91`.

Line 64 closes the follower box at cols 38→53; **line 65 carries a second
`└────────────────┘` at cols 38→55** — eighteen wide against the box's sixteen,
below the box it is supposed to belong to, connecting nothing `[test]`. And
the signal rail runs at col **56** on lines 62-65 and col **57** on lines
66-75 `[test]`.

### G9-17 — `POT-OFFSET`'s lower track end is not drawn

**Node:** `POT-OFFSET`, `breath-output-stage.md:69-72`.

The drawing shows `DAC AVDD ──[POT-OFFSET 10k]` and a wiper, and nothing on
the pot's other end `[repo]`. The offset table at `:122-126` requires the
bottom at 0 V (`Full CCW | 0 V`), and the source-impedance term in G9-2
depends on it. A three-terminal part with one terminal undrawn, on the page
that owns it.

---

## C. Values that changed and did not propagate

### G9-18 — `carrier.md` still says the marker is **six** bits, and the checker's forbidden patterns miss it by one word

**Node:** `marker-bits`, `hardware/carrier/carrier.md:378-383`.

> *"**Two items left this page with the registers.** The **marker pattern**
> (which six bits, to what levels) … are now `PCB-CLUSTER` decisions"* `[repo]
> carrier.md:378-380`.

`marker-bits` is **8 bits**, settled, *"Decided 2026-09-21"* `[repo]
config/figures.yaml`. `key-marker-and-bits.md:50` heads its section *"The
marker pattern: 8 bits, not 6 — DECIDED 2026-09-21"* and
`key-chain-loom.md` says *"Which eight bits carry the marker, and their
levels, was decided 2026-09-21"* `[repo]`. `cluster-boards.md:219-221` says
*"**The marker pattern is no longer among them** — 8 bits, two per device,
decided 2026-09-21"*. `carrier.md` alone still presents it as open *and* as
six.

`marker-bits`'s `forbidden` list carries `"six bits carry the marker"` and
`"**6 marker"` `[repo] config/figures.yaml:260`. `carrier.md`'s spelling is
`(which six bits, to what levels)` — it clears both patterns by a word.
**`check-staleness.py` reports PASS on this** `[test]` — this is the CLAUDE.md
§2 trap ("write the pattern in the spelling of the file it must match")
occurring live, on the figure whose own history is the example.

### G9-19 — "63 network passives" in four live places; the count is 66

**Node:** `R-KEY-PU`/`R-KEY-SER`/`C-KEY` totals.

`cluster-boards.md:211-213`: *"4 ICs, 4 decoupling caps, 18 fitted switches in
21 networked positions, **63 network passives**, 7 chain connectors"* `[repo]`.
The same page's component table three rows above gives `R-KEY-PU` as
**6/6/6/6 = 24**, flagged in bold as *"**24, not 21.**"* `[repo] :203`.

```
[calc]  R-KEY-PU 24 + R-KEY-SER 21 + C-KEY 21 = 66
        (63 = 21 × 3, the count before key-pullup-qty went 21 → 24)
```

BOM quantities confirm 24/21/21 `[repo] hardware/bom.csv`. The stale 63 is
live in four places `[test] grep -rn "63 passives\|63 network" hardware/`:

- `hardware/cluster/cluster-boards.md:211`
- `hardware/carrier/carrier.md:283` (*"4 ICs and 63 passives moved to
  `PCB-CLUSTER`"*)
- `hardware/carrier/bom.csv:4` — `PCB-CARRIER` notes, *"the registers and
  their 63 passives"*
- `hardware/cluster/bom.csv:4` — `PCB-CLUSTER` notes, *"it keeps 63 passives
  off the carrier"*

The last two are `.csv`, where CLAUDE.md §2b allows no refutation window at
all. (Both are also in the generated `hardware/bom.csv`, rows for
`PCB-CARRIER` and `PCB-CLUSTER`.) `R-LED-SER`'s BOM note carries a fifth
instance — *"TWO PARTS ON THE AGGRESSOR, against 63 on the victims"* `[repo]
hardware/carrier/led-strip-drive/bom.csv:4`.

### G9-20 — `hardware/README.md` says `unplaced.csv` is 34 rows; it is 32

**Node:** `hardware/README.md:112`, `hardware/unplaced.csv`.

*"It was 50 rows and is now 34. Sixteen of them were drawn all along"* `[repo]
hardware/README.md:112` (pinned read: `git show a4b80b1:hardware/README.md`).

```
[test]  git show a4b80b1:hardware/unplaced.csv | python3 -c \
          "import sys,csv; print(len(list(csv.DictReader(sys.stdin))))"
        → 32
```

Rule 1 applies to this file too. Two of the 32 are `R-BREATH-SUM` and
`R-BREATH-OFF`, which per G9-7 should not be there at all — so the count is
wrong *and* the contents are.

### G9-21 — `hardware/README.md` says two tables carry the `End` column; three do

**Node:** `hardware/README.md`, *The `## Interfaces` table*.

*"The **two** board-crossing tables (`interfaces/breath-sense-link`,
`interfaces/spi-link`) carry an extra **End** column"* `[repo]`.
`interfaces/key-chain-loom/key-chain-loom.md`'s table header is
`| Node | End | Dir | Peer | Figure | Note |` `[test]` — parsed header, same
script as the edge check. The brief I was given also says three. The README
names two.

### G9-22 — the playable ADC span is 1598 counts on the page that derives it and 1594 on the two that cite it

**Node:** `R-ADCDIV` / `C-AA-ADC` derivation.

`breath-adc.md:43`: *"playable span above rest ≈ **1598** counts of 4096"*
`[repo]`, and I reproduce it `[calc]`: rest `0.265 × 0.6 / 3.3 × 4096 = 197.4`;
play `(0.265 + 0.7665 × 2.8) × 0.6 / 3.3 × 4096 = 1794.9`; difference 1597.5.

`carrier.md:177` and `carrier.md:373` and `key-chain-loom.md:129` all say
*"~**1594**-count playable span"* `[repo]` `[test] grep -rn "1594\|1598"
hardware/`. Three restatements, two values, no citation — the figure is not in
the register at all.

(Minor, same node: `breath-adc.md:38` says `4.86 × 0.6 = 2.92 V … 3622 counts`;
`[calc]` 2.916/3.3 × 4096 = 3619.4, and 3622 back-solves to 4.8634 V. Within
rounding of `sensor-full-scale`'s exact 4.864 V — noted, not filed.)

### G9-23 — `pitch-stage.md`'s shelf corner is still computed at 1 nF

**Node:** `C-FB-PITCH`, `pitch-stage.md:185-191`.

```
G(s) = 1 + (R2/R1)/(1 + sR2C) = (2 + sRC)/(1 + sRC)
Pole at 15.9 kHz, zero one octave above at 31.8 kHz
```

`[calc]` with `R2 = 10 kΩ`: 15.9 kHz ⇒ `C = 1/(2π·10k·15 900) = 1.00 nF`.
`C-FB-PITCH` is **2.2 nF** — in the Values table at `:133`, in the split-loop
table at `:178`, at `:211`, and in `hardware/bom.csv` (`2.2nF C0G/NP0`)
`[repo]`. At 2.2 nF the pole is `1/(2π·10k·2.2n) = **7.23 kHz**` and the zero
**14.5 kHz** `[calc]`.

The structural claims (one octave apart, max 6.02 dB) are correct at any
value; the two frequencies are not, and they are the same 1 nF arithmetic that
`:178` records as having been caught and fixed one row earlier. This is the
recorded shape *"a fix that did not reach the pages citing it"*, on the same
page, fourteen lines down.

### G9-24 — the diode-modulation pitch result does not follow from the chain that is written above it

**Node:** `D1`/`D2` (`D-REVPOL`), `power-entry.md:101-112`, and
`diode-split-rationale` in `config/figures.yaml`.

Stated chain: *"120 mV → LM317 line regulation (0.52 mV/V) → **62 µV on AVDD**
→ OPA2197 PSRR (110.5 dB worst case, ±3 µV/V max) → **0.00044 cents**"*
`[repo] power-entry.md:105-107`; the same chain is in the figure register's
`derivation` `[repo] config/figures.yaml`.

```
[calc]  as written:   62 µV × 3 µV/V = 1.86e-10 V
                      1 cent = 1/1200 V = 833.3 µV
                      → 2.2e-7 cents, not 0.00044

        what gives 0.00044:  120 mV × 3 µV/V = 0.36 µV
                             0.36 µV / 833.3 µV = 4.3e-4 cents  ✓
```

The published answer is right for *"apply PSRR to the 120 mV directly"* and
skips the LM317 attenuation that the sentence spends two clauses on. The two
readings differ by ~2000×. The **conclusion is unaffected** — both are
negligible — but the arithmetic as written is not reproducible, and it is
carried verbatim into `config/figures.yaml`, where it is the derivation of a
`settled` figure.

Same paragraph, smaller: *"It implies ~21 % pitch sensitivity to the +12 V
rail"* `[repo] :103`. `[calc]` 20 cents = 16.67 mV; 16.67/120 = 13.9 %;
16.67/**80** = 20.8 %. The 21 % is computed against the superseded 80 mV that
the blockquote directly above has just replaced with 120 mV.

### G9-25 — `power-entry.md` states the disputed pitch budget as a settled total, and gets the total wrong too

**Node:** `pitch-cents-budget`, `power-entry.md:133-134`.

*"`pitch-stage.md` puts the **entire pitch error budget at 0.42 cents**"*
`[repo]`. Two problems:

1. `pitch-cents-budget` is `status: disputed`, and the register's own
   `decided_by` says *"pitch-stage.md has two contradictory budget tables back
   to back and **states no total**"* `[repo] config/figures.yaml`.
2. `pitch-stage.md:284-288`'s table gives 0.42 cents as the **DAC internal
   reference term only** — *"The largest term"* — alongside 0.027 and 0.068
   `[repo]`. It is not the total.

`power-entry/circuit.yaml` declares no `fig:pitch-cents-budget` edge `[repo]`,
so the graph does not record the dependency either. The argument the number is
used for (*"the carefully engineered part of the pitch path is one to two
orders of magnitude below…"*) holds against 0.42, 0.52 or 0.54, so nothing
downstream breaks — but a `disputed` figure is being cited as settled from a
page that does not own it.

### G9-26 — `pitch-stage.md` carries 0.54 cents and 0.42 cents for the same term, 165 lines apart

**Node:** DAC internal reference, `pitch-stage.md:120-121` vs `:284-286`.

`:120-121`: *"the ADR's 'the DAC's internal reference is sufficient, at **0.54
cents** over 10 °C' survives: that figure is a gain term."* `:286`: **DAC
internal reference | 0.42 cents | The largest term** `[repo]`. Neither
mentions the other. `pitch-stage/notes.md:53-54` records that a superseded
table said `~0.5` and that the live figure is 0.42 — so the shelf knows about
`~0.5` and not about the `0.54` still live on the page. This looks like the
second of the *"two contradictory budget tables"* the register is pointing at,
and it did not move to `notes.md` with the first.

### G9-27 — one page says one spare op-amp half remains, two say two

**Node:** `U-OPA-PITCH` halves.

`breath-receive-stage.md:172`: *"It costs the last spare OPA2197 half, and
`U-OPA-PITCH` goes to six packages **so there is still one**."*
`breath-output-stage.md:157-158`: *"Ten of twelve halves used across the
module, **two spare**."* `breath-response-shaper.md:198-199` (quoting the
review that requested it): *"the module has **two spare OPA2197 halves**"*,
and `:313` spends *"Both remaining OPA2197 halves"*. `[calc]` my own count is
ten used, two spare (G9-11), so `breath-receive-stage.md` is the stale one —
it was written before `breath-output-stage.md` settled at two halves, and its
own `Still open` at `:252-255` records that settlement without going back to
fix the sentence.

### G9-28 — `R-FB` is *"the same E96 part as `R-MODGAIN`"*, and it has not been since the mod redraw

**Node:** `R-FB` / `R-MODGAIN`, `breath-output-stage.md:149`.

`R-MODGAIN` is **10 kΩ / 30 kΩ**, qty 8 `[repo] hardware/bom.csv`, after
`mod-channels.md` moved to the two-resistor `k = 3` form. The 40.2 kΩ belonged
to the **four-resistor** version, which `mod-channels/notes.md:50-54` records
as superseded (*"used 40.2 kΩ against 10 kΩ"*) and `mod-channels.md:100`
strikes through (*"±10.05 V (40.2 kΩ fudge)"*) `[repo]`. The sharing
justification is dead; the value may still be right on its own merits.

### G9-29 — the release filter is 119.9 µs, quoted as 125 µs on the page that owns the figure

**Node:** `key-release-time`, `key-switch-network.md:112`.

*"The **125 µs** release filter is half a scan period and costs nothing
musically"* `[repo]`. `key-release-time` is **119.9 µs**, owned by this page,
and the table eight lines above states it correctly `[repo] :105`. `[calc]`
125 is 250/2; 119.9 is not. Half a scan period is 125 µs, the filter is not.

### G9-30 — `panel.md` restates both tracked figures after saying it does not

**Node:** `panel-width`, `panel-height-budget`, `panel.md:4-8, 54, 57-58, 68`.

The page's own opening: *"this page cites them and **does not restate them**"*
`[repo] :6-7`. It then writes *"10HP is **50.50 mm**"* `:54`, *"**110 mm** of
content against **115.5 mm** of clear panel"* `:57-58`, and *"Three pots
across **50.50 mm**"* `:68`. Both figures are owned by
`docs/decisions/0004-cv-interface-module.md` `[repo] config/figures.yaml`.
(The `panel-toggle-hole` restatement at `:62` is legitimate — this page owns
that one.) The values are all currently correct; rule 1 is about what happens
when they are not.

### G9-31 — peak fault dissipation in the pass FET is ~7.5 W, not ~4 W

**Node:** `Q-LOADSW`, `umbilical-load-switch.md:324-327`.

*"With foldback working, peak fault dissipation is **~4 W at V_out ~ 4 V**,
not the 12 W the old page assumed"* `[repo]`.

```
[calc]  I_limit(V_out) = 0.240 + 0.17531·V_out  up to V_out = 3.99 V, flat at 0.940 A above
        P_FET(V_out)   = (12 − V_out) · I_limit(V_out)
          V_out = 0      : 12.00 × 0.240 = 2.88 W
          V_out = 2      : 10.00 × 0.591 = 5.91 W
          V_out = 3      :  9.00 × 0.766 = 6.89 W
          V_out = 3.99   :  8.01 × 0.940 = 7.53 W   ← maximum
          V_out = 6      :  6.00 × 0.940 = 5.64 W
```

(The slope 0.17531 A/V and the 3.99 V knee are the page's own, `:203` and
`:219`, and I reproduce both `[calc]`.) The peak *is* at V_out ≈ 4 V, as
stated — the number beside it is off by 1.9×. The paragraph immediately below
then does its thermal check at **12 W** (*"a DPAK is 0.6 C/W at 50 ms, so 12 W
is a 7 C rise"* `:331`), so the page uses two different figures two sentences
apart. The conclusion (*"the killer is Spirito / linear-mode derating"*, SOA
not thermal) survives either way, but 4 W is the number someone would take to
an SOA chart.

### G9-32 — the `47 kΩ`-scale leakage comparison is 10×, not 30×

**Node:** `R-FB-HI`/`R-FB-LO`, `umbilical-load-switch.md:186-189`.

*"Divider current is 294 µA at 12 V — 294× the 1 µA max `FB` input current …
The `47 kΩ`-scale alternative would have been **30×** the leakage for 3 mW"*
`[repo]`.

```
[calc]  present: 35.7k + 5.11k = 40.81k → 12/40.81k = 294.0 µA  ✓ (page's own figure)
        a 10× scaling (357k/51.1k = 408.1k) → 29.4 µA
        leakage fraction 1/29.4 vs 1/294  →  10× worse, and 3.53 − 0.35 = 3.18 mW saved
```

3 mW ✓, 30× ✗ (10×). Everything else in that section reproduces exactly: 3.99 V,
10.49 V, 9.85 V, 1.503 V, 294 µA, 0.34 %, 3.5 mW, 17.1 + 30.4 = 47.5 ms, 9.37 µF,
587/160/95.6 ms, 2.01× and 1.89×, 61/122/244 V/s, 197/98/49 ms, 134/268/537 mA,
0.16 V at 1.3 ms, 10 mV and 17 mV, 1.69 V at 10.1 ms, 130 mV, 10.5 % `[calc]`.
This is the best-derived page in the corpus and the one error in it is cosmetic.

### G9-33 — `carrier.md`'s status block says no datasheet was reachable; four of its own questions have since been closed from banked datasheets

**Node:** `hardware/carrier/carrier.md:6-9`.

*"Not checked against a single datasheet — `waveshare.com`, `ti.com`,
`nxp.com` and `analog.com` were all blocked from this sandbox. **Read it as a
proposal with its uncertainties marked, not as a design.**"* `[repo]`.

Since then, and on this page's own circuits: the MCP3202 clock limit closed
against `datasheets/analog/MCP3202-CI-SN.pdf` (`carrier.md:393-395` says so
itself, struck through) `[repo]`; the WS2815 threshold and `BI` closed against
`datasheets/led/WS2815.pdf` (`led-strip-drive.md:64-96`); the OPA2197 `Zo` and
the REF5050 `C_L` closed against banked SBOS737C/SBOS410O
(`breath-excitation-reference/notes.md:23-51`); the R-78E5.0 8 V minimum is
cited from `datasheets/discrete-and-power/R-78E5.0-1.0.pdf`
(`umbilical-load-switch.md:170`). The blanket disclaimer now understates the
page, which matters because it is the disclaimer a reader uses to decide how
hard to look.

### G9-42 — `breath-adc.md` derives its clamp current from the retired 4.7 V sensor full scale, ten lines under a correct citation of the replacement

**Node:** `R-ADCDIV` upper leg, `hardware/carrier/breath-adc/breath-adc.md:50-53`.

```
worst case, 3V3 at 0 and the clamp holding the pin at ~0.7 V:
  (4.7 − 0.7) / 10 kΩ = 400 µA   against a family-typical ±2 mA  [from memory]
```

The node driving that divider is the **buffered sensor output**, whose ceiling
is `sensor-full-scale` = **4.86 V** `[repo] config/figures.yaml`. The same page
cites it correctly ten lines above — `[0.265 and 4.86 from sensor-full-scale]`
`[repo] :42`.

```
[calc]  (4.86 − 0.7) / 10 kΩ = 416 µA,  not 400 µA
```

**4.7 V is the retired value of this exact figure**, not a coincidence:
`sensor-full-scale`'s `forbidden` list carries `"4.7 V × 0.6"`,
`"full scale = 4.7 V"`, `"reaches 4.7 V"`, `"0.2–4.7 V"` and eight more
spellings of it `[repo] config/figures.yaml:60`. This one survives as a bare
`(4.7 − 0.7)`, which matches none of them.

The figure's `escape_note` names *"the ~4.7 V the 5 V rail arrives at after a
diode"* as a legitimate decoy `[repo] :81`, and the sentence above the block
does say *"the 5 V rail comes up before the dev board's 3V3"* — but there is
no diode between anything and this node, and the 5 V buck rail does not feed
it: the buffer runs from +12 V and the sensor from the REF5050's 5.000 V
(`carrier.md` §2) `[repo]`. So the decoy reading does not apply and 4.86 V is
the number that belongs here.

4 % on a figure with 5× of margin — the conclusion (*"the upper leg is
≥10 kΩ"*) is untouched. It is filed because it is a derivation running on a
superseded input, directly beneath a correct citation of its replacement, and
because the checker cannot see it.

### G9-43 — `digital-and-supervision.md` opens by justifying itself on supervision that is deleted on its own board

**Node:** `hardware/module/digital-and-supervision/digital-and-supervision.md:5-13`.

> *"The SPI link from the umbilical to the DAC, and **the three circuits that
> decide what the module does when the instrument is absent, asleep, or
> hung**. None of this carries signal; all of it decides whether the signal is
> trustworthy.*
>
> *No surveyed Eurorack module has any of it. … Everyone else's processor is
> on the same board as their DAC and can use its own internal watchdog.
> Woody's is two metres away behind a write-only link, **so the module has to
> supervise itself**."* `[repo]`

There are no three such circuits and the module does not supervise itself.
The 74HC123 frame watchdog and the LM311 presence comparator are both deleted
and `OE_MOD` is tied enabled — stated on this page's own drawing at `:67-68`
(*"NOT HERE ANY MORE"*), in its own Interfaces row for `OE_MOD` at `:32`, and
at length in `link-supervision.md:1-8` (*"**NOT FITTED. Nothing in this
directory is on the board.**"*) `[repo]`. What is left of "supervision" on
this page is six pull resistors and four enables tied to `GND`.

The page's title and its first two paragraphs are the surviving frame of the
circuit that was removed. This is the `CLAUDE.md` §5 shape — *"an argument
survives its own refutation"* — and it is in the topmost prose of the page,
which is what a reader uses to decide whether the section is load-bearing.
`mod-channels.md:160-168` shows how the same premise was repaired properly
three pages away.

### G9-34 — `HDR-DEV` qty 6 against the page's own correction

**Node:** `HDR-DEV`, `carrier.md:282`.

The component table row reads *"**Qty is one board's worth, not two** — the
display board is 360 mm away"* `[repo] carrier.md:282`, and `:34-35` says the
page *"draws **one** dev-board socket pair"*. BOM: `HDR-DEV` qty **6**,
description *"Sockets for **both** dev boards on the carrier"* `[repo]`. The
page states the correction; the BOM has not taken it.

### G9-35 — `SW1-n` and `CAP1-n` are qty 21 against 18 fitted switches

**Node:** `SW1-n`, `CAP1-n`.

BOM: `SW1-n` qty 21, status **purchased**; `CAP1-n` qty 21 keycaps, purchased
`[repo]`. `cluster-boards.md:202,211` fits 5+4+6+3 = **18** and describes the
other three as *"reserved spare switches … network fitted, **pad unloaded**"*
`[repo]` `[calc]`. Defensible if the three spares were bought against a later
retrofit — but nothing says so, and `key-marker-and-bits.md:43-44` says the
spares need *"plate cutouts at M3 even if the switches are fitted later"*,
which reads as *not* fitted. Flagging as a question, not a defect.

---

## D. `notes.md` — live material on the history shelf

Every `notes.md` opens with the same rule: *"**Past tense only.** … If a
number here is still true, it is in the wrong file."* `[repo]`. Eleven of the
thirteen hold to it cleanly. Two do not.

### G9-36 — `mod-channels/notes.md` holds an undecided recommendation that says the drawn circuit is worse

**Node:** `hardware/module/mod-channels/notes.md:108-112`.

> *"Taking the reference from a **DAC channel** instead keeps the inverting
> topology *and* the safe clear… That is the version worth considering, and it
> is **strictly better than what is drawn above**. Not adopted unilaterally: it
> is a redraw of a settled page and **the call belongs to the author**."*

That is a live, open design decision — present tense, unresolved, and adverse
to the live drawing. The note's own preamble concedes it: *"It was not
adopted, and **that paragraph's call was open when this moved**; the page
points here rather than carrying it"* `[repo] :70-71`. `mod-channels.md`'s
`Still open` list (`:214-221`) does not carry it. An open item that exists only
on the history shelf is an open item nobody will work.

### G9-37 — `pitch-stage/notes.md` holds live LT5400 facts that contradict the live page

**Node:** `TRIM-GAIN`, `R-PRECISION`, `hardware/module/pitch-stage/notes.md:98-101`.

> *"**Absolute tolerance is ±7.5 % (A) / ±15 % (B)** — nobody had written that
> down, and it means `TRIM-GAIN`'s "0 → +2 %" is nominal-only; the real
> authority is **1.86–2.16 %** on an A part."*

`pitch-stage.md:129` states `TRIM-GAIN` as *"0 → +2 % of ratio"* with no
caveat, and `:327-330` reopens *"Whether 200 Ω is the right `TRIM-GAIN`. It is
0 → +2 % and one-sided"* — the live page's number, in the live page's open
question, against a correction that lives only in `notes.md`. The absolute
tolerance and the 1.86–2.16 % authority are current facts about a current
part. Same file, same paragraph: *"the 0.027 cents line in the budget above is
conservatively sourced"* is a live endorsement of a live table row.

### G9-38 — two stated counts in `notes.md` that the lists under them have outgrown

- `hardware/module/link-supervision/notes.md:18` — heading *"### **Three**
  bullets retired here, 2026-09-21"* over a table with **four** rows
  `[repo] :24-28`.
- `hardware/carrier/breath-excitation-reference/notes.md:26` — *"**Two**
  earlier notes on this page are superseded"* followed by items numbered
  **1, 2 and 3** `[repo] :30-51`.

Both are the recorded shape *"a stated count that has moved under the sentence
stating it"*.

---

## E. Structural and formatting defects

### G9-39 — four Markdown breaks in live pages

- `hardware/interfaces/key-chain-loom/key-chain-loom.md` — *"The mapping
  inside each device is still open, and\nit is now a cluster-board decision`**`
  — as is the `H`…`A`-to-switch mapping"*: an unmatched closing `**` with no
  opener, and a sentence that reads as if it were spliced `[repo]`.
- `hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:102-107` — a
  blockquote whose line 104 (`pull-ups for exactly the 21`) has lost its `>`
  prefix, breaking the quote in two `[repo]`.
- `hardware/module/dac8568/notes.md:38-44` — a strikethrough opened with `~~`
  and never closed, so the whole superseded bullet renders as live text
  `[repo]`.
- `hardware/module/mod-channels/mod-channels.md:168` — the blockquote ends
  with *"Channel 7 goes to 0 V with the rest, so:"*, which is the lead-in to
  the code block **outside** the quote at `:170-172`. The sentence introducing
  the live equation is trapped in the historical aside `[repo]`.

Also `hardware/carrier/carrier.md:356-399` — *"Ordered by what blocks what.
The first four block layout"* introduces a bullet list that is interrupted
after three bullets by two blockquotes and then resumes, so the list renders as
two lists and the *"first four"* spans the break `[repo]`.

### G9-40 — `carrier.md` is named as a `Peer` and is not a circuit

**Node:** `Peer` column vocabulary.

`hardware/README.md` defines `Peer` as *"a bare `board/circuit` id when the
other end is a circuit in this tree, a reference designator or part name when
it is not"* `[repo]`. `breath-sense-link.md` names
`` `carrier/carrier.md` §2 `` in four rows and `spi-link.md` names
`` `carrier/carrier.md` `` in one `[repo]`. `carrier/` is a **board** page
with no `circuit.yaml`, so it is neither a circuit id nor a refdes, and the
`§2` suffix is not in the grammar either. It creates no edge (confirmed:
all 23 `circuit.yaml` files match their tables exactly `[test]`), so nothing
is broken — but the transcription rule the column exists for does not cover
these rows. Either the board pages get an entry in the vocabulary, or the rows
point at the circuit directories instead.

Smaller, same file: `hardware/README.md`'s column table defines **four**
columns (Node, Dir, Peer, Figure); all 23 tables carry a fifth, **Note**, and
two carry `Node / part` rather than `Node` `[test]` (parsed headers). The
definition has not kept up with the tables.

---

## What I could not check

- **`key-marker-and-bits.md:93` — *"A mid-shift `SH/LD` reload passes at 11 of
  31 reload points."*** I could not reproduce 11 under either model I tried
  `[calc]`: treating a marker position as "caught" only when the bit that
  lands on it is another marker of the opposite level gives **23** passing
  reload points; treating the whole frame as deterministic with no keys
  pressed (free bits pulled high, unpressed keys high) gives **3**. The page
  does not state which key states it quantifies over. The sibling claims in
  the same paragraph — *"caught 8 times in 32"* and *"undercounts about 4×"* —
  do reproduce `[calc] 32/8 = 4`. Not filed as a defect; filed as unverifiable
  as written.
- **`notes.md`'s 23-permutation marker result** (`key-marker-and-bits/notes.md:28-36`)
  — an exhaustive symbolic result I did not re-run.
- **Anything resting on a datasheet I did not open**: the 1N5817 `r_d` =
  69 mΩ at 392 mA and the 120 mV modulation (`power-entry.md:87-88`), the
  Laird bias-impedance curve readings, the INA828 and OPA2197 electrical
  tables, the WS2815 recommended-application figure, the LT1641 numbers (I
  checked the *arithmetic* built on them, not the *readings*), and the
  MPXV4006DP `V_off` band. G9-24 is an arithmetic finding about a chain, not a
  challenge to any datasheet number in it.
- **`[sim]` claims** — the 1.5° / 85.9° / 76° phase margins on
  `breath-excitation-reference.md`, and the two loop analyses cited at
  `pitch-stage.md:204-210`. The decks are `sim/README.md` contracts with no
  results, by design; nothing has been run.
- **`R-RESP`'s gain-ratio column** (`breath-response-shaper.md:286-292`) — I
  reproduced `i_D` and every gain ratio to three digits `[calc]` from a 0.6 V
  ideal knee, which is the page's own model; I did not model a real 1N4148.
- **Whether `carrier.md:23`'s pointer into `docs/review/`resolves** — I did not
  open or list any review path, cold-review rule.

---

## Provenance and the freeze

The working tree moved under this slice while I was reading. I observed the
`PreToolUse` staleness hook report, across read-only calls of mine:
`PASS` → `FAIL (1 links)` → `PASS` → `FAIL (1 stale)` → `FAIL (2 stale)` →
`PASS`. At the `FAIL (1 links)` moment `git status --short` showed
`M README.md` and `M tools/check-staleness.py`, and the diffs were an injected
broken link (`README.md:148 → g10-does-not-exist.md`) and a one-line patch
`link_problems = []  # G10 experiment: silence a noisy check` in
`tools/check-staleness.py:1116`. At the `FAIL (1 stale)` moment
`hardware/module/power-entry/power-entry.md` was modified; `.staleness/report.txt`
named `power-entry.md:195 found '~275 instrument'`, which is **not** in the
committed file at that line `[test] git show a4b80b1:hardware/module/power-entry/power-entry.md
| sed -n '190,200p'`. The coordinator has since confirmed this was an
injection-testing slice.

**Everything in this report rests on pinned content.** After the coordinator's
notice I cloned to `/tmp/claude-0/g9pin`, checked out `a4b80b1`, and ran
`diff -rq` over `hardware/` and `config/figures.yaml` against the working
tree: **no differences**. `hardware/module/pitch-stage/circuit.yaml`, which
the coordinator flagged specifically, was re-read with
`git show a4b80b1:` and matches what I analysed. `git status --short` at the
time of writing shows only sibling slices' untracked/modified files under
`docs/review/2026-09-22-goal-verification/` — no tracked corpus file is
modified.

The two `[test]` tool runs I quote — `merge-bom.py --check` (0 problems) and
the staleness `PASS` used in G9-18 — were both taken at moments when
`git status --short` showed no tracked corpus modification. I did **not** use
`tools/check-staleness.py` as evidence for anything except G9-18, where the
claim is that it reports PASS on a live stale value; if the tool was still
patched at that moment the patch was to `check_links`, which is a different
check, so the claim stands either way. The G9-18 defect is in any case
demonstrable by reading `config/figures.yaml:260` against `carrier.md:379`
without running anything.

---

## Summary by severity

**Would produce a wrong board or a wrong part order:** G9-1 (`R-FB` 40k/40.2k),
G9-2 (`POT-OFFSET` centre +0.60 V), G9-3 (entry bulk 47 µF vs 100 µF),
G9-4 (`R-LED-SER` three values), G9-5 (`R-OUT-PROT` 250/500 mW),
G9-10 (`C_cm` tolerance absent), G9-11 (seventh OPA2197).

**Would break a netlist transcription:** G9-6 (four refdes that do not exist),
G9-9 (two clamp parts on one jack), G9-13 and G9-14 (drawings whose rails do
not connect), G9-17 (`POT-OFFSET` end undrawn).

**Live stale values:** G9-18 (six/eight marker bits — and the checker passes),
G9-19 (63 vs 66, four places, two of them `.csv`), G9-20 (34 vs 32),
G9-21 (two vs three End columns), G9-22 (1594 vs 1598), G9-23 (15.9 kHz at
1 nF), G9-26 (0.54 vs 0.42), G9-27 (one vs two spare halves), G9-29 (125 vs
119.9 µs).

**Arguments whose premise has moved:** G9-8 (`R-BIAS-INAMP` filed on a
refuted edge), G9-25 (a `disputed` figure quoted as a settled total),
G9-28 (*"same part as `R-MODGAIN`"*), G9-33 (*"no datasheet was reachable"*),
G9-36 (a live, adverse proposal on the history shelf), G9-37 (a live
correction only in `notes.md`).

**Arithmetic:** G9-24 (~2000×, conclusion unaffected), G9-31 (1.9×, and the
page uses two figures two sentences apart), G9-32 (10× vs 30×).
