# N3 — Supply nets, the `rails:` key, and decoupling

**Slice:** N3, cold. Claim type: supply nets, `rails:`, decoupling.
**Measured against:** `d1f0cb7`. `HEAD` at the time of this report is `5c39a4e`;
`git diff --stat d1f0cb7 HEAD` is one file, this wave's `README.md`, which I did
not read, so the corpus I measured is `d1f0cb7` exactly `[test]`.
**`tools/` pinned:** not modified. Every `[test]` below is that revision's tool.
**Cold:** nothing under `docs/review/` was read. Experiments ran in
`git clone /home/user/Woody /tmp/n3-clone`, since deleted; the shared tree was
never modified.

**Baseline** `[test] python3 tools/check-netlist.py --strict`:

```
netlist: 22 circuit(s), 197 components, 254 nets, 55 master net(s) | 0 problem(s)
instances: 102 row(s) placed exactly to BOM qty, 4 counted by section, 7 short:
  C-BUCK-IN 1/2, C-DECOUPLE 1/19, C-DECOUPLE-CARRIER 5/8, HDR-DEV 1/6,
  J-CHAIN 1/8, R-OPAMP-IN 6/7, U-BREATH 1/2
```

Three of those seven shorts are mine and are in N3-3 / N3-4 / N3-7.

---

## Summary

One critical finding: **the LM317 divider that makes `DAC_AVDD` is wired
backwards in the authoritative netlist and in both of its BOM rows**, giving
1.65 V where `config/figures.yaml` `dac-rail` says 5.21 V (N3-1). It is below
the DAC8568's absolute minimum AVDD, so as netlisted the module does not work.
Nothing in the repository catches it: `check-netlist.py`, `check-staleness.py`
and `merge-bom.py --check` all pass on the wrong assignment **and** on the
right one `[test]`.

Thirteen findings. `rails:` itself is sound where it is used, and one whole
class of thing I was sent to look for is genuinely clean: every `rails:`
declaration in the corpus is on an OPA2197 half, every one of them is supported
by its page, and the one on a not-fitted part is handled correctly through
`nets.yaml`'s `proposed:` mechanism. The single-supply assertion on the carrier
is correct and electrically sound. What `rails:` costs is *omission* — 9 of the
10 placed OPA2197 halves declare it and the tenth does not (N3-2), and because
the shorthand does not net supply pins, 15 of the 27 decoupling capacitors the
BOM buys have **no pin in the corpus to attach to** (N3-4).

| id | sev | against | one line |
|---|---|---|---|
| N3-1 | **critical** | `module/power-entry` `REG_ADJ`/`DAC_AVDD` | LM317 divider inverted: 1.65 V, not `dac-rail`'s 5.21 V |
| N3-2 | high | `U-REF-BUF` (breath-receive-stage) | the only OPA2197 half in the corpus with no `rails:` — no supply at all |
| N3-3 | high | `C-DECOUPLE` | qty 19 counts a DAC8568 `DVDD` pin that does not exist; 18 |
| N3-4 | medium | `C-DECOUPLE`, `C-DECOUPLE-CARRIER` | `rails:` makes per-pin decoupling unplaceable: 15 of 27 caps have no pin |
| N3-5 | medium | `MODULE_ANALOG_POS12` @ breath-output-stage | port omitted; `D-JACK-CLAMP.K` dumped into an invented `RAIL_POS` |
| N3-6 | medium | `ON` net, umbilical-load-switch | unquoted `ON:` — YAML parses the net *name* as boolean `True` |
| N3-7 | medium | `C-BUCK-IN` | netlist settled the one-LC topology; row and page still say ×2 |
| N3-8 | medium | `PWR_EXPORT` (`FB2`, `C2`) | the bead whose whole selection is the umbilical current is netted to a dead end |
| N3-9 | low-med | `C-ADC-BULK` | a row whose own note says PROPOSED, NOT DECIDED is asserted unconditionally |
| N3-10 | low-med | `U-DAC.VREFIN/VREFOUT` | no load capacitor anywhere; SBAS430E recommends >=150 nF |
| N3-11 | low | `MODULE_ANALOG_POS12` | `R-OFFNEG`'s stated reason for −12 V is false on both halves |
| N3-12 | low | `C-BULK-RAIL` / `MODULE_ANALOG_POS12` | the 2.2x decay argument counts a deleted comparator and omits the op-amps |
| N3-13 | method | `rails:` | demonstrated fail-open: a wrong rail set, and a missing one, both pass |

---

## N3-1 — **CRITICAL.** `module/power-entry`, nets `REG_ADJ` and `DAC_AVDD`: the LM317 divider is inverted, and the rail is 1.65 V rather than `dac-rail`'s 5.21 V

**Claim.** `hardware/module/power-entry/netlist.yaml` puts the 475 Ω resistor
between `U-REG-DAC.OUT` and `ADJ` and the 150 Ω from `ADJ` to ground, which is
the reciprocal of the ratio `config/figures.yaml` derives `dac-rail` from; as
netlisted `DAC_AVDD` is 1.65 V, below the DAC8568's 2.7 V minimum AVDD and far
below the 5.0 V floor the figure marks HARD.

**Evidence.**

The netlist `[repo hardware/module/power-entry/netlist.yaml]`:

```yaml
  R-REG-SET-HI: {value: "475R 0.1%"}
  R-REG-SET-LO: {value: "150R 0.1%"}
  REG_ADJ:  [U-REG-DAC.ADJ, R-REG-SET-HI.2, R-REG-SET-LO.1, C-REG-ADJ.1]
  DAC_AVDD: [U-REG-DAC.OUT, R-REG-SET-HI.1, C-REG-OUT.1, port: DAC_AVDD]
  AGND_MOD: [... R-REG-SET-LO.2 ...]
```

So R(OUT→ADJ) = 475 Ω and R(ADJ→GND) = 150 Ω. Both BOM rows say the same in
their own `description` fields `[repo hardware/module/power-entry/bom.csv]`:
`R-REG-SET-HI,...,475R 0.1% metal film,,"LM317 divider, ADJ to OUT"` and
`R-REG-SET-LO,...,150R 0.1% metal film,,"LM317 divider, ADJ to GND"`.

The regulator's transfer `[datasheet datasheets/discrete-and-power/LM317LZ.pdf
SLCS144E section 8.4.1]`: *"The device OUTPUT pin will source current necessary
to make OUTPUT pin 1.25 V greater than ADJUST terminal"* — and the front-page
typical application shows the 470 Ω between Output and Adjustment with the
second resistor from Adjustment to ground. So
`V_O = 1.25 x (1 + R_ADJ→GND / R_OUT→ADJ) + I_ADJ x R_ADJ→GND`.

`[calc]` as netlisted: `1.25 x (1 + 150/475) = 1.645 V`, plus
`I_ADJ x 150 = 8-15 mV` at 50-100 µA → **1.65-1.66 V**.

Three independent internal sources say the assignment must be the other way
round:

1. `[repo config/figures.yaml]` `dac-rail`,
   `derivation: "1.25 x (1 + 475/150) = 5.208 V"` — the numerator, i.e.
   `R_ADJ→GND`, is **475**.
2. `[repo docs/decisions/0004-cv-interface-module.md:196]` *"**Shrink R2** —
   150 Ω / 475 Ω instead of 240 Ω / 768 Ω — which halves the `I_ADJ`
   contribution to 24-48 mV."* 240 Ω is the classic `R1` (OUT→ADJ), so the pair
   is written R1/R2 and R2 = 475. `[calc]` the stated 24-48 mV is
   `50-100 µA x 475 Ω = 23.8-47.5 mV`; against 150 Ω it would be 7.5-15 mV, and
   the sentence would not be true.
3. `[repo hardware/bom.csv]` `U-REG-DAC`: *"~13mA load including the divider."*
   `[calc]` divider current is `1.25 / R_OUT→ADJ`: 8.33 mA at 150 Ω, 2.63 mA at
   475 Ω. Only the 150 Ω reading reaches ~13 mA — and the same row's warning
   that *"A BLEEDER SIZED FOR TI'S 2.5mA UNDER-LOADS A 3.5mA PART"* is about a
   margin that the 475 Ω reading destroys.

The drawing is the only place that has it right: `[repo
hardware/module/power-entry/power-entry.md:50]` reads `150R/475R`, in the same
R1/R2 order as ADR 0004.

Consequences at 1.65 V: the DAC8568 is outside its 2.7-5.5 V supply range
entirely `[datasheet datasheets/analog/DAC8568CIPW.pdf SBAS430E, PIN
DESCRIPTIONS: "3 AV_DD Power-supply input, 2.7V to 5.5V"]`, so grade C's
5.0-5.5 V window is not even the binding constraint. `DAC_AVDD` also feeds
`POT-OFFSET.CW` (the breath offset's positive leg, specified ±5 V),
`TRIM-BREATH-ZERO.CW` (the breath zero, needing 0-1.0 V) and `R-PULL-SYNC`
`[repo]` — four consumers on one wrong rail.

**Why no check sees it** `[test]`. `check-netlist.py` compares the netlist's
`value` against the BOM row's `part` field, so a *consistently wrong* pair
passes. Swapping only the netlist fails loudly — `R-REG-SET-HI value '150R
0.1%' does not appear in its BOM part field '475R 0.1% metal film'`, 2 problems
— and swapping the fragment as well and re-running `merge-bom.py` returns to
**0 problems**. `check-staleness.py` returns `PASS` on both. `merge-bom.py
--check` returns `0 problems` on both. The divider resistors also carry no
`[REFDES value]` label in the drawing (the page writes the bare text
`150R/475R`), so the drawing check cannot reach them either.

**This is the repository's named failure with a date on it.** Both rows say
*"SPLIT OUT 2026-09-22 FROM AN AGGREGATE ROW THAT COULD NOT BE NETLISTED - two
different values in one part field at qty 2"* `[repo]`. The aggregate row held
both values and no positions; the split invented the positions, put the values
on the wrong ones, and the netlist then transcribed the split faithfully. The
figure's own derivation was three lines away in a file nobody re-read.

**What would have to be true for this to be wrong.** Either (a) `R-REG-SET-HI`
and `R-REG-SET-LO` do not mean the ADJ→OUT and ADJ→GND legs their own
`description` fields name — but the netlist wires them exactly as those fields
describe, so the netlist would still be wrong; or (b) `dac-rail`'s derivation
`1 + 475/150` is itself inverted and the intended rail is 1.65 V — which ADR
0004's 24-48 mV arithmetic, the `~13mA` load figure, the 5.00 V HARD floor and
the DAC's 2.7 V minimum each independently refute; or (c) the LM317's output is
1.25 V **below** ADJ, which SLCS144E 8.4.1 says it is not.

**Smallest fix.** In `hardware/module/power-entry/bom.csv` swap the two `part`
values — `R-REG-SET-HI` → `150R 0.1% metal film`, `R-REG-SET-LO` → `475R 0.1%
metal film` — leaving both `description` fields and `R-REG-SET-LO`'s "E7
SELECTS THIS ONE" note where they are, since those are already right. Then
change the two `value:` fields in `hardware/module/power-entry/netlist.yaml` to
match, and re-run `tools/merge-bom.py`. All three must be in one commit: the
netlist/BOM value comparison locks them together, so a partial fix fails the
gate `[test]`. Nothing else moves — the page's `150R/475R` and the figure's
derivation are already correct.

---

## N3-2 — HIGH. `U-REF-BUF` (`module/breath-receive-stage`) declares no `rails:` and no supply pins: per the authoritative file, this op-amp has no supply

**Claim.** Ten OPA2197 halves are placed across the module netlists; nine
declare `rails: [MODULE_ANALOG_POS12, MODULE_ANALOG_NEG12]` and `U-REF-BUF`
declares neither rails nor supply pins, so the file that is authoritative for
connectivity gives it no supply at all.

**Evidence** `[repo hardware/module/breath-receive-stage/netlist.yaml]`:

```yaml
  U-REF-BUF:
    part: OPA2197
    section: A
    of: U-OPA-PITCH
    pins: [IN+, IN-, OUT]
    note: "Buffers the trimmer wiper into the in-amp REF pin..."
```

Compare the nine that do: `U-REFBUF`/`U-BREATHBUF` (carrier, one rail),
`U-PITCH-REFBUF`, `U-PITCH-AMP`, `U-BREATH-BUF`, `U-BREATH-SUM`,
`U-MOD-REFBUF`, `U-MOD-1`..`U-MOD-4`, `U-RESP-A` `[repo, grep -rn "rails:"
hardware --include=netlist.yaml]`. `U-REF-BUF` is the single exception.

It is invisible to the tool because `MODULE_ANALOG_POS12` and
`MODULE_ANALOG_NEG12` are *already* ports of this circuit — netted to
`U-DIFFRX.V+`/`V-` and to `D-CLAMP-BREATH`'s legs — so nothing looks
unsatisfied. Demonstrated `[test]`: in the clone, deleting the `rails:` line
from `pitch-stage`'s `U-PITCH-AMP` leaves
`check-netlist.py --strict` at **0 problems**.

The part does need the rails: `U-OPA-PITCH`'s row says *"RRIO on +/-12V reaches
~11.9V"* and lists *"breath REF-zero buffer"* among the ten halves in use
`[repo hardware/bom.csv]`, and `breath-receive-stage.md` states the in-amp REF
pin needs a low-impedance drive `[repo]`.

The second-order cost is that N3-3 and N3-4 cannot be checked from the
netlists: the corpus cannot say how many OPA2197 packages sit on ±12 V, because
one of them says it sits on nothing.

**What would have to be true for this to be wrong.** That `U-REF-BUF` is fed
from somewhere the netlist does state — it is not; its only three pins are
`IN+`, `IN-`, `OUT` — or that omitting `rails:` is a deliberate convention for
a half whose package-mate declares them. It has no package-mate: `section: A`
of this `U-OPA-PITCH` instance is the only half placed in this circuit, and its
`B` half is one of the module's two declared spares.

**Smallest fix.** One line:
`rails: [MODULE_ANALOG_POS12, MODULE_ANALOG_NEG12]` under `U-REF-BUF`. No other
file moves — `nets.yaml` already lists `module/breath-receive-stage` as a
receiver on both nets.

---

## N3-3 — HIGH. `C-DECOUPLE` qty 19: the enumeration counts a DAC8568 `DVDD` pin that does not exist

**Claim.** `C-DECOUPLE`'s own note enumerates the pins its quantity is counted
from, and one of them — the DAC8568's `DVDD` — is not a pin on the part. The
row buys 19 where the module's supply pins number 18.

**Evidence.** The note `[repo hardware/bom.csv]`:

> *"One per supply pin, close to the pin: 6 x OPA2197 on +/-12V = 12, INA828 =
> 2, DAC8568 AVDD+DVDD = 2, 74AHCT125, LT1641 VCC, LM317 in."*

`[calc]` 12 + 2 + 2 + 1 + 1 + 1 = 19, which is the row's qty, so `DVDD` is
load-bearing for the number.

The DAC8568 in TSSOP-16 has one supply pin. `[datasheet
datasheets/analog/DAC8568CIPW.pdf SBAS430E, PIN CONFIGURATIONS / PIN
DESCRIPTIONS]`: pin 3 is `AV_DD`, *"Power-supply input, 2.7V to 5.5V"*; the
block diagram shows `AV_DD` and `GND` and no second supply; the string `DVDD`
appears **zero** times in the whole banked document `[test] grep -a -o "DVDD"`
on the extracted text returns nothing. The netlist agrees and cites the same
table: `U-DAC`'s 16 declared pins are `LDAC, SYNC, AVDD, VOUTA..VOUTH,
VREFIN/VREFOUT, CLR, GND, DIN, SCLK` `[repo
hardware/module/dac8568/netlist.yaml]`.

**Reconciled against the netlists, the module's supply pins are 18** `[repo,
all 22 netlist.yaml]`: `U-DAC.AVDD` 1, `U-LVL-MOD.VCC` 1, `U-LOADSW.VCC` 1,
`U-REG-DAC.IN` 1, `U-DIFFRX.V+`/`V-` 2, and 2 each for the BOM's 6 OPA2197
packages = 12. The enumeration and the netlists therefore agree item for item
**except** on the DAC, where the enumeration is one ahead. The exclusion of
`U-RESP` is correct and correctly flagged in the note; it would add 2, not 1,
if fitted.

**What would have to be true for this to be wrong.** That the intended second
DAC capacitor is not a supply-pin decoupler at all but the 1-10 µF bulk that
SBAS430E *"strongly recommend[s]"* alongside the 0.1 µF `[datasheet, Power
Supply Recommendations]`. If so the quantity survives and the note is still
wrong, because that part is not a `DVDD` decoupler and because the bulk is
already on the net as `C-REG-OUT` (1 µF, `[repo]` net `DAC_AVDD`) — and the
note would need to say which.

**Smallest fix.** The row lives in
`hardware/module/umbilical-load-switch/bom.csv` `[test] grep -rln "^C-DECOUPLE,"
hardware/*/*/bom.csv`. Change `DAC8568 AVDD+DVDD = 2` to `DAC8568 AVDD`, set
`qty` 19 → 18, re-run `tools/merge-bom.py`. Fix it in the same commit as N3-4,
or the count moves twice.

---

## N3-4 — MEDIUM. `rails:` makes per-pin decoupling structurally unplaceable: 15 of the 27 decoupling capacitors bought have no pin in the corpus to attach to

**Claim.** `C-DECOUPLE` is placed 1/19 and `C-DECOUPLE-CARRIER` 5/8 not through
oversight but because `rails:` declares a supply *without netting the pin* — so
a capacitor "at the op-amp's +12 V pin" has no endpoint to name, and the same
capacitor netted to the rail net would be indistinguishable from one at any
other pin on it.

**Evidence.** `[test]` baseline: `C-DECOUPLE 1/19, C-DECOUPLE-CARRIER 5/8`.
The checker's docstring frames under-use as an artefact of an incomplete
rollout — *"circuits without a netlist place nothing"* — but the same run
reports `0 drawing page(s) still without a netlist`, so that explanation has
expired and these two rows are the only decoupling rows still short.

Which are placed, against `C-DECOUPLE-CARRIER`'s own enumeration
(*"MCP3202, REF5050 IN AND OUT, OPA2197 +12V, 74AHCT125, MPXV4006DP, and both
R-78E5 inputs"*) `[repo hardware/bom.csv; all netlist.yaml]`:

| enumerated pin | netlist instance |
|---|---|
| MCP3202 | `C-DEC-ADC` @ `DEV_3V3`/`AGND_INST` — placed |
| REF5050 VIN | `C-DEC-REF-VIN` @ `UMBILICAL_POS12`/`AGND_INST` — placed |
| REF5050 VOUT | `C-DEC-REF-VOUT` @ `REF_5V`/`AGND_INST` — placed |
| MPXV4006DP VS | `C-DEC-SENSOR` @ `VS`/`AGND_INST` — placed |
| 74AHCT125 | `C-DECOUPLE-LED` @ `INST_5V_A`/`PWR_GND` — placed |
| **OPA2197 +12V** | **none** |
| **R-78E5 input A** | **none** |
| **R-78E5 input B** | **none** |

5 of 8, exactly as the tool reports. The set agrees; three are simply not in
any netlist. `C-DECOUPLE`: the only instance anywhere is
`C-DECOUPLE-LOADSW` on `BUS_POS12_RAW` at `U-LOADSW.VCC` `[repo
hardware/module/umbilical-load-switch/netlist.yaml]` — 1 of 18 (N3-3).

**Why it is structural, not clerical.** `U-REFBUF` and `U-BREATHBUF` declare
`rails: [UMBILICAL_POS12]` and net no supply pin `[repo]`. The only node a
100 nF at their V+ could attach to is `UMBILICAL_POS12` itself — where
`C-DEC-REF-VIN` already sits. So the netlist has no way to express "a second
100 nF, at the op-amp's pin rather than the reference's", which is the whole
content of the row's *"One per supply pin, close to the pin"*. The same holds
for all twelve module op-amp instances and for both buck inputs, which the
netlist collapses into one `BUCK_IN` node `[repo
hardware/carrier/power-entry-instrument/netlist.yaml]` — so the
enumeration's "both R-78E5 inputs" names two pins that the authoritative file
has as one node.

One thing this corroborates rather than contradicts: `C-DECOUPLE-CARRIER` gives
the carrier's OPA2197 **one** capacitor where `C-DECOUPLE` gives each module
OPA2197 **two**. That is the single-supply topology showing up in the
purchasing, independently of the `rails:` key — see *Clean* below.

**What would have to be true for this to be wrong.** That "placed" is not meant
to include bypass capacitors at a pin the netlist does not model, i.e. that
`rails:` is understood to carry its decoupling implicitly. Nothing says so, the
`instances` check counts these rows as short rather than exempt, and
`C-DECOUPLE-LOADSW` shows the intent is to place them where a pin exists.

**Smallest fix.** Not a value change; a schema one, and it should be decided
before the KiCad export the netlists are for. Either (a) extend `rails:` to
take the pin names, so `rails: {MODULE_ANALOG_POS12: V+, MODULE_ANALOG_NEG12:
V-}` gives the capacitors an endpoint; or (b) declare `V+`/`V-` in `pins:` on
the ten OPA2197 halves and drop `rails:` on them, which is what `U-DIFFRX`
already does and what makes the INA828's two capacitors placeable. Until one of
those lands, add a line to the two BOM rows saying the instances are unplaceable
by construction, so the `short:` line stops reading as an unfinished
transcription.

---

## N3-5 — MEDIUM. `MODULE_ANALOG_POS12` at `module/breath-output-stage`: the port is omitted and `D-JACK-CLAMP.K` is dumped into an invented `RAIL_POS`

**Claim.** `breath-output-stage` is the only circuit that clamps a CV output to
the module rails without naming those rails: it declares
`MODULE_ANALOG_NEG12` as a port but not `MODULE_ANALOG_POS12`, and sends both
clamp legs to locally invented one-endpoint nets `RAIL_POS`/`RAIL_NEG` listed in
`external_endpoints`. The two other circuits with the identical part net it to
the real rails.

**Evidence** `[repo]`:

```yaml
# breath-output-stage/netlist.yaml
ports: {BREATH_INAMP_OUT, DAC_AVDD, MODULE_ANALOG_NEG12, AGND_MOD}   # no POS12
  RAIL_POS: [D-JACK-CLAMP.K]     # clamp to +12 V
  RAIL_NEG: [D-JACK-CLAMP.A]     # clamp to -12 V
external_endpoints: [RAIL_POS, RAIL_NEG]

# pitch-stage/netlist.yaml and mod-channels/netlist.yaml
  MODULE_ANALOG_POS12: [port: MODULE_ANALOG_POS12, D-JACK-CLAMP.K, ...]
  MODULE_ANALOG_NEG12: [port: MODULE_ANALOG_NEG12, D-JACK-CLAMP.A, ...]
```

Its own page contradicts it: *"`MODULE ANALOG +12V`, `MODULE ANALOG −12V` | in |
`module/power-entry` | — | Op-amp supplies, and `D-JACK-CLAMP` returns to both
rails"* `[repo hardware/module/breath-output-stage/breath-output-stage.md:24]`,
and the drawing labels the clamp `── ±12 V` at line 88. The netlist's own header
says *"Nets that cross this circuit's boundary. These must match the page's ##
Interfaces table"*. `hardware/nets.yaml` also names
`module/breath-output-stage` in `MODULE_ANALOG_POS12`'s `receivers`, so the
master and the page agree and only the circuit's `ports:` block does not.

It passes because `rails:` on the two op-amp halves synthesises the implicit
port, and the `external_endpoints` escape suppresses the two-endpoint rule on
the invented nets. The result is that the one +12 V connection in this circuit
that *is* a real pin — a diode cathode — is the one the checker cannot verify,
while `breath-response-shaper`, which genuinely has nothing but op-amp rails on
those nets, says so explicitly in a comment `[repo
hardware/module/breath-response-shaper/netlist.yaml:25]`. That is the
convention; this is a departure from it.

**What would have to be true for this to be wrong.** That `RAIL_POS`/`RAIL_NEG`
are deliberately unasserted because the clamp's rail termination is an open
question on this circuit and not on the other two. Nothing says so: the page
asserts it flatly, the part is the same `D-JACK-CLAMP` row, and the `#` comments
name the rails.

**Smallest fix.** Add `MODULE_ANALOG_POS12: {dir: in, from: module/power-entry}`
to `ports:`, replace the two invented nets with the two rail nets carrying
`port:` plus the clamp leg — copying `pitch-stage`'s block verbatim — and delete
the `external_endpoints:` list. One file.

---

## N3-6 — MEDIUM. `module/umbilical-load-switch`: the `ON` net's name parses as the boolean `True`

**Claim.** The net joining `SW-POWER.COM` to `U-LOADSW.ON` — the module's power
switch into the load switch's enable — is written `ON:` unquoted, and YAML 1.1
resolves a bare `ON` to boolean true, so the authoritative file's key for that
net is `True` and not the string `ON`.

**Evidence** `[test]`:

```
$ python3 -c "import yaml; n=yaml.safe_load(open('hardware/module/\
umbilical-load-switch/netlist.yaml'))['nets']; ..."
non-string net key: True bool -> ['SW-POWER.COM', 'U-LOADSW.ON']
is "ON" a key? False
```

It is the only non-string key in all 22 netlists `[test]`, and the author knew
the trap: two of the declarations above it are quoted *for this exact reason* —
`pins: [VCC, SENSE, GATE, FB, TIMER, 'ON', PWRGD, GND]   # quoted: YAML reads a
bare ON as true` and `pins: [COM, 'NO']   # quoted: YAML reads a bare NO as
false` `[repo, lines 25 and 83]`. Line 129 is `  ON:` and is not quoted.

The checker is silent because a net key only reaches the master comparison
through `ports:`, and this net is local; the endpoint strings `'U-LOADSW.ON'`
and `'SW-POWER.COM'` are inside quotes and resolve fine, so the pin checks pass.
Every downstream consumer — a KiCad exporter, a grep for the net, a diff — sees
`true`.

**What would have to be true for this to be wrong.** That the name is not
load-bearing because the netlists are only read by `check-netlist.py`. The
files' own headers say KiCad is generated from them later.

**Smallest fix.** Quote it: `  'ON':`. One character pair, in the file that
already documents why.

---

## N3-7 — MEDIUM. `C-BUCK-IN`: the netlist has settled the one-inductor topology and the row and the page have not followed

**Claim.** `check-netlist.py` reports `C-BUCK-IN 1/2`, and that is not a
rollout artefact: the netlist places both bucks on a single `BUCK_IN` node with
one 100 µF, which is one of the two topologies the page lists as open — and per
`hardware/README.md` the netlist now wins, so the row's qty 2 and the page's
`C-BUCK-IN ×2` are the derived statements that did not move.

**Evidence** `[repo hardware/carrier/power-entry-instrument/netlist.yaml]`:
`BUCK_IN: [L-BUCK-IN.2, C-BUCK-IN.1, U-BUCK-A.IN, U-BUCK-B.IN]`, with
`L-BUCK-IN`'s note *"QTY 1 HERE AND THE BOM BUYS 1, against C-BUCK-IN's qty 2 -
the two rows describe different topologies... This file draws the one-inductor
version because that is what the drawing shows."* The BOM row says
*"Completes the LC... **One per buck**"* and qty 2 `[repo hardware/bom.csv]`;
the page's component table says `C-BUCK-IN ×2` and its *Still open* keeps
*"`L-BUCK-IN` qty 1 against `C-BUCK-IN` qty 2. One LC and one bulk cap, or two
LCs and a missing inductor."* `[repo
hardware/carrier/power-entry-instrument/power-entry-instrument.md:132,149]`

The damping derivation on the same page sides with the netlist, not the row
`[repo ibid:80-82]`: it takes `C = 100 µF` and gets
`f0 = 3.39 kHz, Z0 = 0.469 Ω`. `[calc]` with the row's two 100 µF on one node:
`C = 200 µF → f0 = 1/(2π√(22µ·200µ)) = 2.40 kHz`, `Z0 = √(22µ/200µ) = 0.332 Ω`,
and two electrolytics in parallel roughly halve the ESR to 0.25-0.5 Ω, so
`Q ≈ 0.332/0.375 ≈ 0.9` — still no peaking, but not the numbers the page
prints. The derivation is written for one capacitor.

**What would have to be true for this to be wrong.** That the netlist is the
provisional one and the row is the decision — which `hardware/README.md`'s "the
netlist wins" inverts, and which the page's own `C = 100 µF` contradicts.

**Smallest fix.** The page's own open item is what decides it, so this is a
decision, not a transcription. The cheap half is honest either way: add to
`C-BUCK-IN`'s note that the netlist places one and the row buys two, naming
which is which. If the one-LC reading is adopted, qty 2 → 1, drop *"One per
buck"*, and the damping paragraph needs no edit.

---

## N3-8 — MEDIUM. `PWR_EXPORT` (`module/power-entry`): `FB2` and `C2` are netted to a dead end, and the figure `ferrite-bias-impedance` is derived from a current that branch does not carry

**Claim.** The netlist leaves the `D2`/`FB2`/`C2` branch terminating nowhere and
says so honestly — but it frames the open question as *"what reverse-polarity
protection the instrument actually has"*, and does not say that the reading both
`## Interfaces` tables assert (the export tapped **before** the diodes) makes
`FB2` carry **no current at all**, which is the premise of a settled figure and
of the entire `FB-IN` part selection.

**Evidence** `[repo hardware/module/power-entry/netlist.yaml]`:
`PWR_EXPORT: [FB2.2, C2.1]` — and the export path netted is
`J-PWR-EURO.POS12 → BUS_POS12_RAW → module/umbilical-load-switch →
UMBILICAL_POS12`, i.e. bypassing `D2`/`FB2`/`C2` entirely. The file's closing
note grounds that in two independent statements: *"power-entry.md:31 'The branch
is taken **before** the diodes' and umbilical-load-switch.md:18"*.

What depends on the other reading: `[repo config/figures.yaml]`
`ferrite-bias-impedance`, `value: "~580-614 ohm on FB1/FB3/FB4; ~280-310 ohm on
FB2"`, owner `power-entry.md`; the page's table row *"`FB2` | `umbilical-current`
| **~280-310 Ω**"* and *"`FB2` is the one that matters"* `[repo
power-entry.md]`; `FB-IN`'s row, whose whole single-criterion part choice is
*"**FB2 CARRIES THE UMBILICAL AT figures.yaml umbilical-current AND GETS ROUGHLY
HALF THAT**"* with `IR drop at 0.080 ohm max is 28.7 mV at the umbilical
current` `[repo hardware/bom.csv]`; and the netlist's own `FB2` note repeating
it. If the tables are right and the netlist follows them, every one of those is
about a bead in series with nothing.

This is the `rails:`-adjacent version of the same hazard: a supply branch that
no tool can find fault with because both of its ends are declared, one of them
as deliberately absent.

**What would have to be true for this to be wrong.** That `D2`/`FB2`/`C2` sit in
series with the load-switch *output*, which is the drawing's apparent reading and
would put the umbilical current through `FB2`. Then the figure and `FB-IN` are
right and `BUS_POS12_RAW`'s *"taken before the diodes"* — stated identically on
two pages and followed by the netlist — is wrong, along with the netlist's
`BUS_POS12_RAW` net itself.

**Smallest fix.** Not a wiring change until the page decides. Add one sentence
to the netlist's closing note and to `ferrite-bias-impedance`: that the `FB2`
bias figure and `FB-IN`'s selection assume the second reading, so resolving the
branch the way both Interfaces tables describe retires them. Naming the
dependency costs a line and stops the figure looking settled.

---

## N3-9 — LOW-MEDIUM. `C-ADC-BULK` is asserted unconditionally in `carrier/breath-adc`'s netlist although its own row says PROPOSED, NOT DECIDED

**Claim.** The netlist nets `C-ADC-BULK` into `DEV_3V3`/`AGND_INST` as an
ordinary connection, while the row it names says the part may not exist. The
corpus has a mechanism for this at net level (`proposed:` in `nets.yaml`) and
none at component level, so the marker is simply lost.

**Evidence** `[repo hardware/carrier/breath-adc/netlist.yaml]`:
`DEV_3V3: [port: DEV_3V3, U-ADC.VDD, C-ADC-BULK.1, C-DEC-ADC.1]`, with the
matching leg on `AGND_INST`. The row `[repo hardware/bom.csv]`: status `open`,
*"*** PROPOSED, NOT DECIDED *** - the page says so and this row says so...
DECIDED AT E9, on the bench, by scoping VREF with the LEDs sweeping - that is
the only measurement that settles whether this part is needed at all"*. The
drawing marks it `** PROPOSED **` `[repo hardware/carrier/carrier.md:144]`.

Contrast: `module/breath-response-shaper` is entirely `open`, and
`hardware/nets.yaml` keeps it out of `receivers` and in `proposed:` on all four
of its nets, with *"`proposed:` means DRAWN BUT NOT ADOPTED... this file does
NOT claim the board has the connection"*. And `D-USBOR-A` shows the
netlists' convention for an undecided *value*: *"NO `value:` ON PURPOSE. The row
is open"* `[repo hardware/carrier/power-entry-instrument/netlist.yaml]`. There
is a convention for an open value and one for an open net; there is none for an
open part, so the strongest statement in the corpus about this capacitor is
absent from the file that outranks the others.

**What would have to be true for this to be wrong.** That netting a proposed
part is understood as "where it goes if fitted" and needs no marker. Then
`nets.yaml`'s `proposed:` and `D-USBOR`'s missing `value:` are both redundant.

**Smallest fix.** One key on the component — `proposed: true`, or reuse the
`open:` spelling the BOM `status` column uses — plus a line in the netlist's
header comment. It changes no connectivity and the checker ignores unknown keys
`[test]`, so it lands alone.

---

## N3-10 — LOW-MEDIUM. `U-DAC.VREFIN/VREFOUT` has no load capacitor in any netlist and no BOM row

**Claim.** The DAC's internal reference drives `VREFOUT` into `pitch-stage` with
nothing on it; the banked datasheet recommends >=150 nF there, and
`module/dac8568`'s netlist contains no capacitor of any kind.

**Evidence** `[repo hardware/module/dac8568/netlist.yaml]`: the four components
are `U-DAC`, `R-CLR-PU`, `R-LDAC`, `LK-CLR`; `VREFOUT:
[U-DAC.VREFIN/VREFOUT, port: VREFOUT]`. `[datasheet
datasheets/analog/DAC8568CIPW.pdf SBAS430E, Internal Reference]`: *"for improved
noise performance, an external load capacitor of 150nF or larger connected to
the V_REFH/V_REFOUT output is recommended"*, and separately *"a 1 µF to 10 µF
capacitor and 0.1 µF bypass capacitor are strongly recommended"* with *"A supply
bypass capacitor at the AV_DD input is also recommended"*. `[repo]` `grep -in
VREF hardware/bom.csv` returns no reference-bypass row, and `dac8568.md`
contains no occurrence of `decoupl`, `bypass` or `capacit` `[test]`.

Of the three, the 1-10 µF is arguably satisfied — `C-REG-OUT` (1 µF) is on the
`DAC_AVDD` net `[repo hardware/module/power-entry/netlist.yaml]`, on the same
board — and the 0.1 µF is `C-DECOUPLE`'s unplaced share (N3-4). The VREFOUT
capacitor is absent from the netlists, the BOM and the page alike.

**What would have to be true for this to be wrong.** That the reference is
buffered before anything loads it and the recommendation is therefore optional —
`VREFOUT` does feed a follower, `U-PITCH-REFBUF` via `TRIM-OFFSET` `[repo
hardware/module/pitch-stage/netlist.yaml]`, and the datasheet says
"recommended", not required. It is still a datasheet recommendation that no
document has declined on the record, which is the shape §3 of `CLAUDE.md` exists
for.

**Smallest fix.** A row in `hardware/module/dac8568/bom.csv`, `C-REF-DAC`
150 nF-1 µF, netted `VREFOUT`/`AGND_MOD`; or one sentence on `dac8568.md`
declining it with the reason, as `C-REF-OUT`'s row declines the REF5050's
TRIM/NR capacitor.

---

## N3-11 — LOW. `MODULE_ANALOG_POS12`: the reason `R-OFFNEG` is taken from −12 V is false in both halves

**Claim.** `breath-output-stage.md` justifies the negative offset leg with *"the
−12 V rail carries no LED current, because the strips run from +12 V"*. The
strips do not run from `MODULE_ANALOG_POS12`, and the one LED that does is on it.

**Evidence** `[repo hardware/module/breath-output-stage/breath-output-stage.md:
158-159]` for the sentence. The strips: `J-LED-L.POS12` and `J-LED-R.POS12` net
to `UMBILICAL_POS12` `[repo hardware/carrier/led-strip-drive/netlist.yaml]`,
whose driver is `module/umbilical-load-switch` fed from `BUS_POS12_RAW` — taken
ahead of `D1`/`D2` `[repo hardware/nets.yaml; hardware/module/power-entry/
netlist.yaml]`. `MODULE_ANALOG_POS12` is *"downstream of D1 and FB1"*
`[repo hardware/nets.yaml]`. Two separate branches; `FB-IN`'s own row
distinguishes them, `FB1` at *"~45mA"* against `FB2` at the umbilical current
`[repo hardware/bom.csv]`. So no strip current is in `MODULE_ANALOG_POS12`.

The LED that is: `MODULE_ANALOG_POS12: [port, R-LED-PANEL.1]` →
`LED-PANEL.A` → `AGND_MOD` `[repo hardware/module/panel-led/netlist.yaml]`, and
`power-entry.md`'s Interfaces row for the rail says so in as many words:
*"`R-LED-PANEL` hangs on it too"* `[repo]`. `[calc]` `(12 − 2)/2200 = 4.5 mA`.

The conclusion survives — 4.5 mA of DC through a 2.2 kΩ is not a modulation, and
the page's own `21 mV, 0.21 % of span` sensitivity number is unaffected — but the
stated reason is wrong in both directions, and it is the kind of reason a later
reviewer uses to move a part.

**What would have to be true for this to be wrong.** That "+12 V" in that
sentence means `UMBILICAL_POS12` rather than the rail `R-OFFNEG`'s alternative
would have been. Then the first half is right by accident and the second half —
that −12 V is the rail without LED current — is still false in the only
comparison the sentence is making.

**Smallest fix.** Delete the clause after the comma, or replace it with the
reason that holds: `MODULE_ANALOG_NEG12` carries only op-amp quiescent current,
while `MODULE_ANALOG_POS12` additionally carries the LM317's whole load and
`LED-PANEL`.

---

## N3-12 — LOW. `C-BULK-RAIL`'s +12/−12 asymmetry argument counts a deleted comparator and omits the op-amps

**Claim.** The row's reason for 100 µF on +12 V and 47 µF elsewhere rests on a
22 mA vs 10 mA load ratio whose +12 V term includes *"the comparator"* — a part
`nets.yaml` records as deleted — and excludes the six OPA2197 packages and
`LED-PANEL` that `MODULE_ANALOG_POS12` actually carries. Recomputed, the stated
2.2× becomes about 1.5×.

**Evidence.** The row `[repo hardware/bom.csv]`: *"The +12V branch carries the
LM317's divider, the DAC and the comparator, about 22mA against -12V's 10mA - so
at 47uF each it collapses 2.2x faster."* The comparator: *"module/link-supervision
was a receiver here and is not one: its page says 'Not fitted' against every row,
including the presence detect"* `[repo hardware/nets.yaml]`, and `panel-led.md`
*"that comparator is not fitted"* `[repo]`.

What the enumeration leaves out, per the netlists: ten OPA2197 halves in six
packages draw from **both** rails at `IQ 1mA/amp` `[repo hardware/bom.csv
U-OPA-PITCH]`, and `LED-PANEL` draws 4.5 mA from +12 V only (N3-11).
`[calc]` +12 V: 22 + ~10 (op-amps) + 4.5 (LED) ≈ 36 mA, and −12 V: 10 + ~10 ≈
20 mA — ratio **1.8×**, or ~1.5× if the deleted comparator's share is removed
from the 22 mA first. The conclusion (put the larger capacitor on +12 V) is
unchanged; the factor and one of its three named loads are not.

**What would have to be true for this to be wrong.** That the 22/10 mA figures
already include the op-amp quiescent under "the DAC" and the sentence is only
naming the three largest terms. Then −12 V's 10 mA has no plausible source at
all, since the INA828 and the op-amps are the only things on it.

**Smallest fix.** Replace *"and the comparator"* with *"and the op-amps'
quiescent on both rails plus `LED-PANEL` on this one"* and drop the `2.2x`, which
is the restated number that goes stale next. The 100 µF stands.

---

## N3-13 — METHOD. The `rails:` fail-open, demonstrated

`rails:` is checked in one direction and not the other, and N3-2 is what the
unchecked direction costs. Three experiments in `/tmp/n3-clone`, `tools/`
untouched:

**A. A rail the circuit already receives is accepted however wrong it is.**
Adding `rails: [DAC_AVDD, AGND_MOD]` to `U-REF-BUF` — declaring a ±12 V RRIO
op-amp to run single-supply from the 5.21 V DAC rail and a ground — gives
`0 problem(s)` `[test]`. Both nets are already ports of that circuit, so the
master's bidirectional check is satisfied and nothing compares the rail against
the part or the page.

**B. A rail the board does not have IS caught.** Adding `rails: [BUS_5V]` to
`LED-PANEL` gives `module/panel-led: declares a port on 'BUS_5V' and
hardware/nets.yaml does not name it on that net`, 1 problem `[test]`. So the
orientation's "a rail a netlist gives a part which does not exist on that board"
is covered — as long as `nets.yaml` is right, which is where that check
bottoms out.

**C. Omitting `rails:` entirely is silent.** Deleting the line from
`pitch-stage`'s `U-PITCH-AMP` gives `0 problem(s)` `[test]`.

So the shorthand is falsifiable against the *board* and not against the *part*,
and it is not falsifiable at all by absence. A cheap check with no judgement in
it: **any component with a `part:` or `value:` naming an op-amp, an in-amp, a
regulator or a logic family, and neither a `rails:` key nor a declared supply
pin, is reported.** On this corpus it would print exactly one line, N3-2.

---

## Clean, and what was checked

- **Single supply vs split supply on the carrier — correct, page-supported, and
  electrically sound.** `U-REFBUF` and `U-BREATHBUF` declare
  `rails: [UMBILICAL_POS12]` with *"Single supply from +12 V, V- on the analog
  star"* `[repo]`, and four independent statements agree: `carrier.md`'s drawing
  labels both halves `(V+ = +12V)`, its component table says *"both on +12 V"*,
  `power-entry-instrument.md`'s Interfaces row says *"the V+ of both OPA2197
  halves"*, and `U-BUF`'s BOM row says *"it RUNS ON +12V, NOT 5V"* with the
  consequence spelled out `[repo]`. `C-DECOUPLE-CARRIER`'s enumeration
  corroborates it from the purchasing side: *one* capacitor for "OPA2197 +12V"
  where `C-DECOUPLE` gives each module package two.
  Output range `[calc]` from `[datasheet datasheets/analog/OPA2197.pdf SBOS737C
  EC table, OUTPUT]`, swing from either rail `5 mV typ / 25 mV max` at no load,
  `95 / 125` at `R_LOAD = 10 k`, `430 / 500` at `2 k`: with `V- = 0` the breath
  buffer must reach the sensor's worst-case pedestal of **0.152 V** (the
  datasheet's own `Voff` minimum, quoted in `TRIM-BREATH-ZERO`'s row). Its DC
  load is the ADC divider, `10k + 15k = 25 kΩ`, in parallel with `1k + 10k + 1M`
  down the umbilical — lighter than the 10 kΩ row — so the floor is at most
  125 mV and the margin is **≥27 mV**. Tight but real, and the 4.86 V top is
  7 V clear of +12 V. Input common mode `(V−) − 0.1` to `(V+) + 0.1` covers it.
  I checked this against the claim that the assertion might not be supported;
  it is, from four directions, and I found no defect. Recorded because the 27 mV
  is thinner than anything in the corpus states, and a substitution for a
  non-RRIO part would break it silently.
- **Rails on a not-fitted part — handled correctly.** `U-RESP-A` declares both
  module rails while every `breath-response-shaper` BOM row is `open` and the
  page says *"Proposed 2026-09-21"*. `hardware/nets.yaml` keeps the circuit out
  of `receivers` and in `proposed:` on `MODULE_ANALOG_POS12`,
  `MODULE_ANALOG_NEG12`, `AGND_MOD` and `BREATH_INAMP_OUT`, and the netlist's
  `ports:` block explains in a comment why the rails are not ports there. This
  is the one place the corpus gets the proposed/asserted distinction right, and
  it is the model N3-9 should copy.
- **`module/panel-led`** — page, netlist and `nets.yaml` agree that the
  indicator is on `MODULE_ANALOG_POS12` with the return on `AGND_MOD`, and the
  netlist flags the ground as the disputed figure rather than asserting it.
  Clean.
- **Decoupling that is placed and correct** `[repo, all netlist.yaml]`:
  `C-DECOUPLE-LOADSW` on `BUS_POS12_RAW` at `U-LOADSW.VCC`; `C-DECOUPLE-LED`
  on `INST_5V_A` at `U-LVLSHIFT.VCC`; `C-DEC-ADC` and `C-ADC-BULK` on
  `DEV_3V3` at `U-ADC.VDD`; `C-DEC-REF-VIN`/`C-DEC-REF-VOUT` on the REF5050's
  two sides with `C-REF-OUT-VIN`/`C-REF-OUT-VOUT` beside them; `C-DEC-SENSOR`
  on `VS`, which is the 100 nF the reference buffer's compensation is designed
  against `[repo R-ISO-REF note]`; `C-DECOUPLE-165` across `V3V3_CHAIN`/
  `GND_CHAIN` at `U-KEYS.VCC`/`GND`, `replicated: 4` against qty 4 — exact.
- **`C-REF-OUT`'s placement, the one the page says must not move.** Both 10 µF
  are on the REF5050's VIN and VOUT and neither is on the buffer's output,
  which `[repo config/figures.yaml cref-out-node]` settles and `[repo
  hardware/bom.csv C-REF-OUT]` explains (10 µF there would be 10 000× the
  OPA2197's 1 nF limit). The netlist matches the figure.
- **Both regulators' input/output sides.** LM317: input on
  `MODULE_ANALOG_POS12` after `FB1`/`C1`, output `DAC_AVDD` with `C-REG-OUT`
  1 µF, and `C-REG-ADJ` 10 µF on the ADJ pin — which the drawing does not show
  and the netlist does, with a note saying so. That is the netlist earning its
  keep: the rail's ripple-rejection claim depends on that part and the picture
  omitted it. (The divider between them is N3-1.) Bucks: `C-BUCK-IN` on the
  **input** side, which is the side the damping derivation needs, with the ESR
  requirement carried in the component note *"ELECTROLYTIC, AND THE ESR IS THE
  POINT"* `[repo]` — the one page whose calculation depends on a real ESR states
  it in three places (page, component table, netlist) and the netlist is one of
  them. No output capacitor on either buck, correctly: *"No minimum load on the
  5V part"*, `Max capacitive load 220uF` `[repo U-BUCK]`.
- **`interfaces/breath-sense-link`** — sensor excitation from the `VS` port,
  return on `AGND_INST`. **`interfaces/key-chain-loom`** — `DEV_3V3` through
  `F-CHAIN` to `V3V3_CHAIN`. **`carrier/carrier`** — dev-board `P5V`/`P3V3`/
  `GND` netted, no local decoupling, consistent with
  `C-DECOUPLE-CARRIER`'s enumeration excluding the MCU. All clean.
- **The known pull-up-with-no-rail** (`CS_PULLUP_TOP`, `R-PULL-CS`) is already
  documented in the netlist and the page's *Still open*; I re-read it and found
  nothing to add.
- **Not checked, and not mine:** `U-BREATH 1/2`, `HDR-DEV 1/6`, `J-CHAIN 1/8`,
  `R-OPAMP-IN 6/7` (the VREFOUT follower), `KEY_BITS`/`MARKER_BITS`
  per-board resolution, the two duplicate `OPA2197IDR` rows in
  `datasheets/MANIFEST.csv` (one `OK`, one `BLOCKED`), and the `±11.5 V` swing
  on `breath-output-stage.md` against `~11.9V` on `U-OPA-PITCH` — a restated
  figure with no register entry, which belongs to whichever slice owns
  `figures.yaml` coverage.
