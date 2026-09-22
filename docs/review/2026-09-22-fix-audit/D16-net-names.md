# D16 — the net renames, and whether the tables and the drawings can still be reconciled

**Slice:** the 2026-09-22 qualification of colliding net names in the 23
`## Interfaces` tables, and the two-sources-of-truth arrangement it left behind.
**Method:** cold. `docs/review/2026-09-22-fix-audit/README.md` read; nothing else
under `docs/review/**`. Git log and `git diff` used. Every claim carries
provenance.

**Verdict in one line:** the qualification of the *names* is sound and the
collision census is real, but **the mitigation the whole decision rests on —
"each row names the drawing's own spelling" — is present on 6 of 29 qualified
rows, one of those 6 is false, one is partial, and `carrier.md` §2 uses the bare
token `AGND` for two different nets inside one picture, which no per-row mapping
can repair.** Three collisions of the same shape were never spotted at all.

---

## Summary of findings

| # | Finding | Severity |
|---|---|---|
| D16-1 | The per-row drawing mapping is missing on 23 of 29 qualified rows | **High** — this is the mitigation the decision rests on |
| D16-2 | `pitch-stage.md`'s mapping is **false**: `AGND` appears nowhere in that page's drawing | **High** |
| D16-3 | `carrier.md` §2 spells two different nets `AGND` inside one drawing; the ADC row's named spelling `AGND-local` is split across two lines at exactly that node | **High** — this is the short |
| D16-4 | `breath-output-stage.md`'s mapping is right for 1 of the 3 nodes it names; the other two are drawn bare `AGND` | **High** |
| D16-5 | `carrier.md` §4 labels the umbilical SPI clock `SCK`, which is another circuit's net name (`J-CHAIN` pin 2, the key chain clock) | **High** — unlisted collision |
| D16-6 | `SER` and `QH` are self-declared multi-net names that were never qualified | Medium |
| D16-7 | Bare `+12V` and bare `5 V` each denote two or three different physical nets across the tables | Medium |
| D16-8 | `AGND_INST` is cited as a net by three pages and declared as a row by none | Medium |
| D16-9 | `breath-output-stage.md`'s `DAC AVDD` row still describes a drawing label that was fixed the same day | Medium — the repo's named failure, inside the rename work |
| D16-10 | The `dac-rail` value is still restated in two derived drawings; the fix landed on one of three | Medium |
| D16-11 | Six rows attribute the DAC-side `R-SPI-PULL` to the cable-side net, which is the merged reading the rename exists to remove | Medium |
| D16-12 | `spi-link.md:46` uses the retired bare `CS` for a third net (`SYNC`) | Low |
| D16-13 | Suffix convention mixes a board axis and a device axis; `SCLK` is the only collision where the bare name was kept | Low |
| D16-14 | `hardware/bom.csv`, ADR 0004, ADR 0003, `ROADMAP.md` and `umbilical-pinmap` are all still in the bare namespace | Low-Medium, judgement call |
| D16-15 | `OE_INST`/`OE_MOD` cannot short — both are ground ties. `pcb-pipeline.md`'s "two different physical nets" is loose for that row | Low |
| D16-16 | Nothing mechanical checks any of this | **High**, as a cause |

---

## 1. Is the scheme complete?

### 1.1 What is in the tables

I enumerated every row of every `## Interfaces` table: **164 rows across 23
circuit pages** `[test]`:

```
$ python3 - <<'EOF'   # extract Node cells from every '## Interfaces' table
  ... (walk hardware/**/*.md, take the first '## Interfaces', read | rows)
EOF
164 rows
```

**29 of those 164 rows carry a name from the five renamed families**
(`AGND_*`, `BREATH_*`, `OE_*`, `CS_*`, `SCLK`/`SCLK_DAC`). Counts by name
`[test]`:

```
AGND_MOD 8   AGND_SENSE 2   AGND_INST 2
BREATH_SENSE 2   BREATH_OUT 2 (+1 "BREATH_OUT jack")
CS_MOD 2   CS_ADC 1
OE_MOD 3   OE_INST 1
SCLK 2   SCLK_DAC 3
```

**No row in any Interfaces table still carries a bare `AGND`, `BREATH` or `OE`
as a Node name.** That part of the sweep is complete `[repo]`, verified by
regenerating the Node-cell list and reading all 164.

### 1.2 Three collisions of the same shape that nobody has spotted

**D16-5 — `SCK` names two different clocks, and the drawing is the one that
does it.** `hardware/carrier/carrier.md:215` labels the umbilical SPI clock:

```
  IO35 SCK  ──[R-SPI-SER 100R]───┬──── J-UMB pin 4   ┐ pair (4,5)
```

`[repo] hardware/carrier/carrier.md:215`. But `SCK` is already a **Node cell in
two Interfaces tables**, where it means the *key chain* clock from a different
SPI host: `hardware/interfaces/key-chain-loom/key-chain-loom.md:29`
(`` `SCK` (`J-CHAIN` pin 2) | carrier → clusters | out | `HDR-DEV` IO38 ``) and
`hardware/cluster/key-register/key-register.md` (`` `SCK` | in |
`interfaces/key-chain-loom` ``) `[repo]`. `carrier.md`'s own key-chain drawing
confirms the second sense: `IO38  SPI3 SCK ──[R-CHAIN-SER 100R]─────► 2 SCK`
`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:68`.

So a transcriber reading `SCK` off `carrier.md` §4 and looking it up in the
tables lands on the key-chain net and merges **SPI2's clock with SPI3's clock**
— two driven clock outputs on different GPIOs shorted together. This is the
same failure the `SCLK`/`SCLK_DAC` split was made to prevent, on the same
signal, one drawing away, and it is on nobody's list: `docs/reference/pcb-pipeline.md`'s
collision table has five rows and `SCK` is not one of them `[repo]
docs/reference/pcb-pipeline.md:67–73`.

Worse, `carrier.md` spells **the same conductor two ways in one file**: the
block diagram at line 50 says `4 SCLK`, §4 at line 215 says `IO35 SCK` `[repo]`.
`spi-link.md:38`'s `SCLK` row names `HDR-DEV IO35` as its driving end, which is
the only thing that lets a careful reader resolve it — and that is an IO number,
not a drawing spelling.

**D16-6 — `SER` and `QH` are declared multi-net and left unqualified.**
`key-chain-loom.md:35` says of `QH`, in its own Node row: *"**Point to point,
and a different net on each side of every board.**"* `[repo]`. Its prose is
blunter still: *"`QH` and `SER` are not a bus, and that is what forces two
connectors"* `[repo] key-chain-loom.md:248`, and *"each board's QH feeds the
PREVIOUS board's SER"* `[repo] key-chain-loom.md:89`. So `QH` is five distinct
nets and `SER` is at least two (the `J-CHAIN` pin-6 pass-through conductor, and
each 74HC165's pin-10 serial input, which `LK-SER` selects between — `[repo]
key-chain-loom.md:234–240`, `cluster/key-register/key-register.md:39`). Both
Node cells are bare. `key-register.md`'s `SER` row says "point to point, not a
bus" while `key-chain-loom.md:32`'s `SER` row says "the one pass-through" — the
two tables describe different topologies under one name, and the reconciliation
is in prose 50 lines below one of them.

This is exactly the criterion the scheme was built on ("a name that denotes two
different physical nets"), the page states the collision itself, and the
qualification was not applied. A netlist that merges `SER` ties all four
registers' serial inputs to the carrier and the shift chain stops being a chain.

**D16-7 — bare `+12V` and bare `5 V`.** Node cells `[test]`, from the same
enumeration:

- `` `+12V` `` on the carrier (`breath-excitation-reference.md:26`, "REF5050
  `VIN`"), `` `+12V` strip feed `` and `` `+12V` analog `` on
  `power-entry-instrument.md:21–22`, and `` `+12V`, GND at `J-LED-L/-R` `` on
  `led-strip-drive.md:27` — all downstream of the umbilical.
- `` `+12V`, `-12V`, `+5V`, `GND` on `J-PWR-EURO` `` and `` `+12V` ahead of
  `D1`/`D2` `` on the module (`power-entry.md:26,31`,
  `umbilical-load-switch.md:18`) — the Eurorack bus rail.

The carrier's `+12V` and the module's `+12V` are separated by `U-LOADSW`'s FET
and 2 m of Cat5 `[repo] umbilical-load-switch.md:20`. They are two physical
nets with one name. `UMBILICAL +12V` and `MODULE ANALOG +12V` exist and are
correctly qualified; the bare rows are the leak. `docs/reference/pcb-pipeline.md:88`
names this hazard itself — *"`Net("+12V")` **constructs**. Two modules naming
the same rail give `+12V` and `+12V1`"* — without noticing that the tables
already carry the collision it warns about.

`5 V` is the same shape on the carrier: `power-entry-instrument.md:23–24`
declares **two** 5 V nets, `5 V, buck A` and `5 V, buck B`, and the two
receiving pages name neither — `led-strip-drive.md:24` says `5 V` and
`display-and-service-uart.md:31` says `5 V (or `+12V`) on `J-DISP`` `[repo]`.
The disambiguation is in the Note cell, not the Node cell, which is the exact
arrangement `breath-sense-link.md:38–40` argues is insufficient for `AGND`.

**Also: two names for one net**, a milder version of the same defect —
`` `VDD`/`VREF` 3V3 `` (`breath-adc.md:23`) vs `` `3V3` `` (key-chain-loom,
key-register, key-switch-network), which `key-chain-loom.md:36` confirms is one
net by listing `carrier/breath-adc` as a peer; and `MISO` (`spi-link.md:44`) vs
`DOUT` (`breath-adc.md:24`), where spi-link's row does say they are one node
`[repo]`. `` `±12 V` `` (`breath-sense-link.md:62`) vs `MODULE ANALOG +12V`,
`MODULE ANALOG −12V` (five module pages) is a third `[repo]`.

**D16-8 — `AGND_INST` has no owning row.** Three pages name it: `breath-adc.md:29`
and `breath-excitation-reference.md:30` both declare `` `AGND_INST` | ref |
`carrier/power-entry-instrument` ``, and `breath-sense-link.md:41` asserts it is
"the instrument's star" `[repo]`. `power-entry-instrument.md`'s own table has
**no `AGND_INST` row** — the name appears only inside the `PWR_GND` pour row's
Note (`"…`AGND_INST` reaches it on a single tie"`) `[repo]
power-entry-instrument.md:25`. `hardware/README.md:36` states the rule this
breaks: *"**Exactly one page sources a net.** The page holding the part that
drives it says `out` … every other page says `in` and names it."* The net whose
existence is the entire basis of the "three, not two" claim is declared from the
receiving end only. `breath-sense-link.md`, which holds both ends of the breath
chain, also has no `AGND_INST` row — only `AGND_SENSE` and `AGND_MOD` `[repo]
breath-sense-link.md:51–63`.

---

## 2. Is the scheme consistent?

**D16-13 — the suffixes run on two different axes, and one collision kept its
bare name.**

| Pair | Axis |
|---|---|
| `AGND_INST` / `AGND_MOD` | board |
| `OE_INST` / `OE_MOD` | board |
| `AGND_SENSE`, `BREATH_SENSE` | role (the umbilical conductor) |
| `BREATH_OUT` | role (the jack) |
| `CS_MOD` / `CS_ADC` | **board vs device, in one pair** |
| `SCLK` / `SCLK_DAC` | **nothing vs device** |

Two consequences worth recording.

`CS_MOD` is the odd one. Every other `_MOD` name (`AGND_MOD`, `OE_MOD`) is a
module-**local** net. `CS_MOD` is not local to anything: it is driven from
`HDR-DEV` IO34 on the carrier and crosses the umbilical `[repo]
spi-link.md:40`. `pcb-pipeline.md:73` makes the point against itself —
*"**both of its nets are on the carrier**, so it does not even need the
umbilical to collide"* — and then names the far board in the qualifier.
`CS_DAC`/`CS_ADC` would have matched `SCLK_DAC` and been true. Not a defect that
shorts anything; it is the kind of inconsistency that makes the next person
guess.

`SCLK` is the only collision where the bare name was **kept** for one of the two
nets. Every other family retired the bare form. That makes bare `SCLK`
load-bearing and ambiguous in a way the others are not: when a reader meets
`SCLK` they cannot tell whether it is the deliberately-kept qualified name or a
label that has not been swept yet. In `digital-and-supervision.md` the
distinction is carried correctly in both table and drawing `[repo]
digital-and-supervision.md:26, :57`; in `carrier.md` it is spelled `SCK` at the
driving end (D16-5). One name doing double duty is the thing the scheme exists
to stop.

**Names the register does not know.** `config/figures.yaml`'s `umbilical-pinmap`
value is still written entirely in the bare namespace `[repo]`:

```
value: 1,2 BREATH/AGND | 3,6 +12V/PWR_GND | 4,5 SCLK/MOSI | 7,8 CS/DIG_GND
```

Twelve Interfaces rows cite `umbilical-pinmap` from a Node cell that says
`BREATH_SENSE`, `AGND_SENSE`, `CS_MOD` or `SCLK` `[test]`, and following the
citation returns the bare name. **I do not think this is a defect to fix in the
value** — the pin map names conductors on a connector and the qualified names
name nets, and rewriting the register value would move a settled figure to say
something it was not derived to say. It should be an added `note:` on the entry
saying which qualified name each conductor is, which costs nothing and is where
a reader looks. As it stands the register is a fourth naming authority (drawing,
table, register, BOM) and nothing says how they relate.

No `circuit.yaml` names a net `[test]: grep -rn 'net' hardware --include=circuit.yaml`
returns only header prose — so the renames could not break the dependency graph,
and did not.

---

## 3. Can a transcriber reconcile table and drawing?

This is the question the decision stands or falls on, and it is where the fix is
weakest.

`hardware/README.md:32` states the guarantee: *"Each row names the drawing's own
spelling so a reader can match the two."* `docs/reference/pcb-pipeline.md:65`
repeats it: *"each table row names the drawing's spelling beside the qualified
one."* `breath-sense-link.md:44` repeats it a third time: *"The drawings still
spell all of these `AGND`, `AGND-local`, `AGND(module)` and `BREATH`; **each row
says which**."*

### D16-1 — the guarantee holds on 6 of 29 rows

I checked every row whose Node cell carries a qualified name for a drawing
spelling in its Note `[test]`:

| Page | Node | Drawing spelling named |
|---|---|---|
| `carrier/breath-adc` | `AGND_INST` | `` `AGND-local` in `carrier.md` §2 `` ✔ (but see D16-3) |
| `carrier/breath-excitation-reference` | `AGND_INST` | `` `AGND-local` in `carrier.md` §2 `` ✔ |
| `module/breath-receive-stage` | `AGND_SENSE` | `` `AGND (pin 2)` `` ✔ (near-miss, below) |
| `module/breath-receive-stage` | `AGND_MOD` | `` `AGND(module)` `` ✔ |
| `module/mod-channels` | `AGND_MOD` | `` `AGND` `` ✔ |
| `module/breath-output-stage` | `AGND_MOD` | `` `AGND(module)` `` **partial — D16-4** |
| `module/pitch-stage` | `AGND_MOD` | `` `AGND` `` **FALSE — D16-2** |
| `carrier/breath-adc` | `CS_ADC` (IO39) | — |
| `carrier/led-strip-drive` | `OE_INST` ×4 | — |
| `interfaces/breath-sense-link` | `BREATH_SENSE` | — |
| `interfaces/breath-sense-link` | `AGND_SENSE` | — |
| `interfaces/breath-sense-link` | `AGND_MOD` | — |
| `interfaces/spi-link` | `SCLK` | — |
| `interfaces/spi-link` | `CS_MOD` | — |
| `interfaces/spi-link` | `SCLK_DAC`,`DIN`,`SYNC` | — |
| `interfaces/spi-link` | `OE_MOD` ×4 | — |
| `module/breath-output-stage` | `BREATH_OUT` | — |
| `module/breath-receive-stage` | `BREATH_SENSE` | — |
| `module/breath-response-shaper` | `AGND_MOD` | — |
| `module/dac8568` | `SCLK_DAC`,`DIN`,`SYNC` | — |
| `module/dac8568` | `AGND_MOD` | — |
| `module/digital-and-supervision` | `SCLK` | — |
| `module/digital-and-supervision` | `CS_MOD` | — |
| `module/digital-and-supervision` | `SCLK_DAC`,`DIN`,`SYNC` | — |
| `module/digital-and-supervision` | `OE_MOD` ×4 | — |
| `module/link-supervision` | `OE_MOD` ×4 | — |
| `module/panel` | `BREATH_OUT` jack | — |
| `module/power-entry` | `AGND_MOD` | — |
| `carrier/breath-adc` | SPI2 `SCLK`,`MOSI`,`DOUT` | — |

**Seven rows name a spelling. Twenty-two do not.** Of the seven, one is false,
one is partial, and one is a literal near-miss. **Three are cleanly correct.**

The sharpest instance: `breath-sense-link.md:44` promises "each row says which"
and **all three of its own qualified rows say nothing** `[repo]
breath-sense-link.md:51, :52, :62`. The page that introduces the scheme does not
follow it.

`AGND_MOD` — the most-used qualified name, on 8 pages — carries a mapping on 4,
and two of those four are wrong or partial.

### D16-2 — `pitch-stage.md`'s mapping is false

`hardware/module/pitch-stage/pitch-stage.md:26`:

> `` | `AGND_MOD` | ref | `module/power-entry` | `dig-gnd-topology` | The module analog star, **drawn `AGND`**. `C-AA-PITCH` and `C-FILT-PITCH` shunt to it. … | ``

`[test]`:

```
$ grep -n 'AGND' hardware/module/pitch-stage/pitch-stage.md
26:| `AGND_MOD` | ref | … drawn `AGND`. …
201:- **`C-AA-PITCH`**, 10 nF from the `R-OPAMP-IN` node to `AGND` — 15.9 kHz
```

The drawing at lines 30–55 contains no `AGND`, and neither `C-AA-PITCH` nor
`C-FILT-PITCH` appears in it at all `[repo]`. A transcriber told to find `AGND`
in this page's drawing finds nothing, and the two capacitors the row says return
to it are not drawn anywhere. The row is a claim about a picture that does not
contain what it claims.

### D16-4 — `breath-output-stage.md`'s mapping is right for one node of three

`hardware/module/breath-output-stage/breath-output-stage.md:25` says
`AGND_MOD` is *"drawn `AGND(module)`. `R-GAIN-FLOOR`, the summer's (+) input and
`C-OUT-BREATH` all return here."* The drawing `[test]`:

```
$ grep -n 'AGND' hardware/module/breath-output-stage/breath-output-stage.md
25:| `AGND_MOD` | … drawn `AGND(module)`. R-GAIN-FLOOR, the summer's (+) input and C-OUT-BREATH …
67:                     AGND(module)                  [R-IN 10k]      ← R-GAIN-FLOOR
81:                                          AGND   │                 ← the summer's (+) input
88:                                                 ├──[C-OUT-BREATH 330nF film]── AGND
```

`AGND(module)` labels `R-GAIN-FLOOR` only. The other two nodes the row
enumerates — the summer's (+) input and `C-OUT-BREATH` — are labelled **bare
`AGND`**, the token that on `carrier.md` line 134 means `AGND_SENSE`. A netlist
taken from this picture ties the breath output stage's summing reference and its
output filter return to the umbilical sense conductor. **That is the short the
scheme exists to prevent, on the page whose row claims to prevent it.**

### D16-3 — `carrier.md` §2 uses `AGND` for two different nets, in one picture

`[test]`, all `AGND` in `hardware/carrier/carrier.md`:

```
 50:   │ J-UMB   1 BREATH   2 AGND   3 +12V   6 PWR_GND   4 SCLK   5 MOSI   │   → AGND_SENSE
 99:    AGND-local   AGND-local  │                        [100 nF]           → AGND_INST
101:                             │  paths:            AGND-local             → AGND_INST
122:      │                  [C-AA-ADC 47 nF C0G]              AGND          → AGND_INST
123:      │                                                    -local
134:  J-UMB pin 2 AGND ──[R-SER-BREATH-INST 1k]──┴── analog star point       → AGND_SENSE
```

Two problems, both fatal to the per-row mitigation.

**First, the bare token `AGND` appears at line 122 meaning `AGND_INST` and at
lines 50 and 134 meaning `AGND_SENSE`, in the same file, in connected pictures.**
A per-row mapping cannot disambiguate a picture that is ambiguous internally.

**Second, `breath-adc.md:29`'s mapping points at the one node where the spelling
it names does not exist as a matchable string.** That row is specifically about
"`R-ADCDIV`'s lower leg and `C-AA-ADC`" and says they are "drawn `AGND-local`".
At that node the label is broken across the drawing's gutter: `AGND` on line 122,
`-local` on line 123. `grep 'AGND-local'` returns lines 99 and 101 only `[test]`.
This is `CLAUDE.md`'s own recorded trap — *"A pattern containing a hard wrap can
never fire … A refutation split across an ASCII drawing's gutter does not count"*
— occurring inside the drawing rather than inside a `forbidden` pattern. A
transcriber reading line 122 sees `AGND`, matches it against line 134's `AGND`,
and merges the ADC divider's return with the in-amp's `IN+` leg **across `R1b`**.

**Third, `AGND_INST`'s other drawn form is not a label at all.** Line 134's
right-hand end reads `analog star point` — prose, not a net name. So the
instrument star is drawn three ways (`AGND-local`, `AGND`/`-local`, `analog star
point`) and the rows name one of the three.

**Literal near-miss.** `breath-receive-stage.md:44` says *"The drawing labels it
`AGND (pin 2)`"*; the drawing at line 62 reads `AGND   (pin 2)` — three spaces
`[test] cat -A`. Harmless to a human, and worth noting only because this
repository's recorded failures are all one or two characters wide.

### Pages with no drawing of their own

Eleven of the 23 circuit pages have no ASCII drawing `[test]` — including
`breath-sense-link`, `spi-link`, `breath-adc`, `breath-excitation-reference`,
`panel`, `link-supervision`, `panel-led`, `key-chain-loom`,
`power-entry-instrument`, `display-and-service-uart`, `key-marker-and-bits`. For
those, "the drawing's spelling" is meaningless unless the row also names *which*
drawing. **Only the two `AGND_INST` rows do** (`"in `carrier.md` §2"`). Every
other qualified row on a drawing-less page — all four on `spi-link`, all three
on `breath-sense-link` — leaves the reader to guess which of `carrier.md` §2,
`carrier.md` §4 or the peer page's drawing they should be matching against.

---

## 4. Is `AGND` three nets? Is `R1b` fitted?

**Yes to both, verified from the circuit and not from the claim.**

The instrument end `[repo] hardware/carrier/carrier.md:134`:

```
  J-UMB pin 2 AGND ──[R-SER-BREATH-INST 1k]──┴── analog star point
                       R1b  ** WAS MISSING **
```

The module end draws the same series element independently `[repo]
hardware/module/breath-receive-stage/breath-receive-stage.md:62`:

```
   analog star ──[R1b 1k]──────────────────────── AGND   (pin 2) ──┐
```

So the conductor at `J-UMB` pin 2 is separated from the instrument's analog star
by a 1 kΩ series resistor, and from the module's analog star by `R2` (10 kΩ) and
the 1 MΩ bias pair `[repo] breath-receive-stage.md:70–82`. **Three nodes, two
series elements between them, three nets.** The claim is correct and the two
drawings agree about it from opposite ends.

`R1b` is specified: `hardware/bom.csv` carries `R-SER-BREATH-INST` at **qty 2**
`[test] csv read of hardware/bom.csv:43`, with the note *"TWO, not one … R1 in
the `BREATH` leg, R1b its twin in the `AGND` leg"*. `** WAS MISSING **` in the
drawing marks that it was missing *from the picture*, not from the design —
`breath-sense-link.md`'s "Two parts this drawing was missing" section is
explicit about that `[repo]`.

**One hazard nobody has recorded.** `R-SER-BREATH-INST`'s status is `candidate`
`[test]`, and its justification carries only 1.7 dB of CMRR margin
(`breath-sense-link.md`: *"the link CMRR falls from **70.2 dB to 60.2 dB**
`[calc, A2]` against an independently derived requirement of 58.5 dB"`). **If
`R1b` is ever dropped, `AGND_SENSE` and `AGND_INST` become one net and the
scheme goes from three names to two** — and nothing in the corpus records that
the net count depends on a candidate-status part. The count "three" is asserted
in prose in three places (`hardware/README.md:32`,
`breath-sense-link.md:41`, `pcb-pipeline.md:69`) and is not a tracked figure, so
no tool would catch the divergence. A one-line note on the
`R-SER-BREATH-INST` BOM row — *"deleting this part merges `AGND_SENSE` into
`AGND_INST`"* — would close it for free.

---

## 5. Did the renames break anything that cited the old names?

**Nothing broke.** No citation was invalidated, because none of the old names
was a citation target — they are net names in prose, not figure ids or paths.
`tools/check-staleness.py` reports PASS `[test]` and `merge-bom.py --check` is
run by the commit hook.

What did **not** follow the rename:

| Reader | State | My view |
|---|---|---|
| `docs/reference/pcb-pipeline.md` | **Updated and correct.** Collision table at :67–73 lists all five with the right qualifiers; the prose at :63–65 states the drawings-keep-bare-names decision explicitly `[repo]` | Correct. One editing defect, below |
| `config/figures.yaml` `umbilical-pinmap` | Value still bare (`1,2 BREATH/AGND … 7,8 CS/DIG_GND`) `[repo]` | Leave the value; add a `note:` mapping conductor → qualified net |
| `hardware/bom.csv` + fragments | **Entirely bare.** 8 rows name renamed nets `[test]` — `D-TVS-BREATH` ("ESD protection on the `BREATH` and `AGND` legs"), `U-DIFFRX` ("BREATH drives IN−, AGND drives IN+"), `D-CLAMP-BREATH`, `R-SER-BREATH-INST`, `R-BIAS-INAMP` ("AGND's no-current rule"), `MECH-GNDBOND` ("PWR_GND, never AGND"), `U-LVL-MOD` ("OE IS TIED ENABLED"), `R-LED-PANEL` ("the level shifter's OE pins"), `R-SPI-PULL` | Incomplete. `bom.csv` is the most-cited file in the repo and a transcription input |
| `docs/decisions/0004` | 42 bare occurrences `[test]`. Line 45 asserts *"the three grounds are named and distinct — `PWR_GND`, `DIG_GND` and `AGND`"* `[repo] 0004:45` | **This one contradicts the scheme.** The ADR says three grounds; the scheme says `AGND` alone is three nets, so there are five. ADR 0004 is corpus, not history |
| `docs/decisions/0003` | 10 bare occurrences `[test]` | Same class, lower stakes |
| `ROADMAP.md:53` | *"`PWR_GND` and `DIG_GND` each on their own copper, `AGND` not a return at all"* `[repo]` | Bare `AGND` meaning `AGND_SENSE`. Under the new names `AGND_MOD` **is** a return, so the sentence reads false |
| `firmware/README.md` | Names no nets at all `[test]` | Clean. No action |
| `hardware/**/circuit.yaml` | Name no nets `[test]` | Clean |

Whether the ADRs should have been swept is a judgement call. I would not rewrite
their bodies — they are reasoning written at a time — but ADR 0004 line 45's
"three grounds" is a **live statement of fact in the corpus that the rename made
wrong**, and it should carry a one-line correction the way the rest of that ADR's
superseded passages do.

**D16-12 — one retired name survives inside a rewritten table.**
`hardware/interfaces/spi-link/spi-link.md:46`:

> `` | `DAC AVDD` | module | in | … | What the DAC-side **`CS`** pull returns to, **not** bus `+5V` … | ``

Bare `CS` was retired in favour of `CS_MOD`/`CS_ADC`. Here it means **neither**:
the DAC-side pull sits on `SYNC` `[repo] digital-and-supervision.md:57`, so the
retired name denotes a third net. Low severity — the sentence is true about the
rail — but it is the retired token alive in the file that retired it.

**Editing defect in `pcb-pipeline.md`.** The `SCLK` paragraph at :75–80 argues
about the buffer (*"Merging them shorts a buffer across itself"*) and then says
*"A transcription taking names off the drawings shorts the breath in-amp input
to the breath output jack"* `[repo] docs/reference/pcb-pipeline.md:78–79` —
which is the **`BREATH`** consequence, in the `SCLK` paragraph. Reads as a
mis-paste.

---

## 6. Values inside net names, and inside drawings

**Node cells: clean.** I checked every one of the 164 Node cells for a numeric
quantity `[test]`. The only matches are rail names (`+12V`, `5 V`, `±12 V`,
`bus +5V`, `MODULE ANALOG −12V`) which are net names, not restated figures. The
`buffered +5.21 V` cell is gone — `6645fb7` replaced it with `` `DAC AVDD` ``
citing `dac-rail` `[repo] git show 6645fb7`. **Q6's first half verifies clean.**

The eight rows that restated `umbilical-pinmap` now cite it: twelve rows carry
`` `umbilical-pinmap` `` in the Figure column and none spells out the pin
assignment `[test]`. **Verifies clean.**

**D16-10 — the drawings do not verify clean.** `79f5c4a` fixed one drawing
label `[repo] git show 79f5c4a -- hardware/module/breath-output-stage/...`:

```
-   buffered +5.21 V ──[POT-OFFSET 10k]
-   (LM317 rail)             │ wiper
+   DAC AVDD ──────────[POT-OFFSET 10k]
+   (`dac-rail`)             │ wiper
```

`dac-rail`'s value `5.21 V` still appears in **two other drawings** `[test]`:

```
hardware/module/dac8568/dac8568.md:39            │   AVDD 5.21V          │
hardware/module/dac8568/dac8568.md:42            │           5.21V  │
hardware/module/breath-receive-stage/...:89      │   buffered    from the LM317 5.21 V
hardware/module/power-entry/power-entry.md:45    └──[LM317LZ]──┬── DAC AVDD 5.21V
```

`power-entry.md` is `dac-rail`'s **owner** `[repo] config/figures.yaml`, so its
label is legitimate. `dac8568.md` and `breath-receive-stage.md` both cite
`dac-rail` in their tables and restate its value in their drawings — the same
defect that was fixed, in the same shape, one directory away. **The drawing-label
fix landed on 1 of 3 derived instances.**

**D16-9 — and the fix went stale inside the commit that made it.** The row that
*pointed at* the defect was not updated when the defect was removed.
`hardware/module/breath-output-stage/breath-output-stage.md:23`, live today:

> `` | `DAC AVDD` | in | `module/power-entry` | `dac-rail` | The top of `POT-OFFSET`, buffered — the positive leg of the offset pair. **The drawing below labels this node as the buffered LM317 rail and restates the figure's value in the label**; the value belongs to `dac-rail` and not to a net name | ``

The drawing below now reads `DAC AVDD` / `` (`dac-rail`) `` `[repo] :69–70`. It
no longer says "buffered LM317 rail" and no longer restates anything. The row
describes a drawing that was fixed 3 minutes later in `79f5c4a` and left the
sentence behind — **`CLAUDE.md`'s named failure, occurring inside the rename
work, in the one row whose whole content is a reconciliation instruction.** A
transcriber following it looks for a label that is not there.

**And on the same page, 100 lines down, the value is restated twice more**
`[repo] breath-output-stage.md:126, :129`:

```
| Full CW | 5.21 V | **−4.89 V** |
… `R-OFF` pushes a variable from the buffered 5.21 V.
```

plus `2.605 V` at :124, which is `5.21 / 2` `[calc]`. The fix landed where the
editing was happening and not where the reader looks — on the page it was
applied to. `pitch-stage.md:88` restates it once more ("the DAC is on 5.21 V").

None of these fails the checker: the value is current, so they register only in
the 233 advisory "restated-not-cited" hits `[test] .staleness-report.txt`.

---

## 7. Judging the decision

### What was right

Qualifying the tables first was the correct first move, for three reasons that
hold up:

1. The tables are the transcription source, so that is where a merge becomes a
   short. Fixing the source before the picture is the right order.
2. It made the collisions **enumerable**. Before the rename there was no list;
   now there is one, in `pcb-pipeline.md`, and I could audit it — which is how
   D16-5, D16-6 and D16-7 were found. A vague worry became a checkable claim.
3. The `SCLK` find is genuinely good work: two nets under one name **on one
   page's own table**, which is a defect no cross-page comparison would surface,
   and it came out of doing the rename rather than out of a review.

### What was wrong

**The mitigation was assumed rather than applied.** Three documents state that
every row names the drawing's spelling. Seven rows of twenty-nine do; one of the
seven is false and one is partial. This is not a near-miss — it is the load-
bearing half of the decision, absent from three-quarters of the rows it was
promised for, and asserted as complete in `hardware/README.md`, in
`pcb-pipeline.md` and in `breath-sense-link.md` itself. A reader who trusts
those three sentences will not check.

**And the mitigation cannot work where it is most needed.** `carrier.md` §2
spells two different nets `AGND` inside one connected picture (D16-3). No
per-row footnote fixes an internally ambiguous drawing, because the transcriber's
direction of travel is picture → name, not name → picture. You read the schematic
and write down what the wire is called. The Interfaces tables are the netlist
source in principle; the drawing is what a person's eye actually follows.

**The precedent was already set and then not followed.** `79f5c4a` **did** redraw
a drawing — `digital-and-supervision.md`'s buffer-output labels, `SCLK↓ MOSI↓
CS↑` → `SCLK_DAC↓ DIN↓ SYNC↑` plus a two-line annotation `[repo] git show
79f5c4a`. The commit message's own reason: *"the one place a transcriber reading
only the picture would short a buffer across itself."* That reason is equally
true of `carrier.md` line 122 vs line 134 and of `breath-output-stage.md` lines
81 and 88. So the "leave the drawings alone" policy is not a policy — it is one
exception granted and three identical cases left.

### What I would do

**Relabel the drawings. Do not redraw them.**

The recorded objection to touching drawings is *"a redrawn schematic is not a
moved one"* `[repo] breath-sense-link.md:23, carrier.md:131`. That objection is
about **dividing** a drawing across pages during the restructure — it protects
the picture's topology and its provenance. Substituting one token for another on
one line is neither a division nor a redraw: the topology is untouched and the
diff is legible. The objection does not reach this case, and `79f5c4a` already
treated it as not reaching this case.

**Cost, measured** `[test]` — bare colliding tokens inside fenced drawings
across `hardware/**` excluding `notes.md`:

```
AGND 16   BREATH 15   CS 9   SCK 7   SCLK 4   OE 2
53 tokens on 43 lines in 9 files
```

Of the 15 `BREATH` hits, most are inside refdes (`D-TVS-BREATH`,
`C-OUT-BREATH`, `D-CLAMP-BREATH`) and must **not** be touched; the genuine net
labels number roughly 25–30. Six sit at end of line and widen freely; the rest
have box-drawing to the right and need the same count of spaces removed on that
line `[test]`. `SCLK` in `digital-and-supervision.md` and the seven chain-clock
`SCK`s are already correct and stay; `carrier.md:215`'s `IO35 SCK` becomes
`SCLK` (D16-5).

That is an afternoon, on nine files, in a repository that spent a day rewriting
23 tables. It is cheaper than the twenty-two footnotes it replaces, and unlike
the footnotes it is **verifiable in one grep**: after the pass, no bare `AGND`,
`BREATH`, `CS` or `SCK` may appear inside a fence in `hardware/**`, with a named
exception list. The two-sources-of-truth problem disappears rather than being
documented.

**D16-16 — and whatever is decided, add the check.** There is no net-name
checker; `tools/` holds staleness, conservation, two merges, a path rewriter and
a datasheet verifier `[test] ls tools`. Nothing guards this scheme. Two checks,
both short:

1. For every Interfaces row whose Node contains `_MOD|_INST|_SENSE|_ADC|_DAC`,
   require a backticked drawing spelling in the Note, and require that string to
   occur inside a fenced block in the file the Note names (defaulting to the same
   file). **This catches D16-1, D16-2, D16-3's split label and D16-4 today.**
2. Assert no bare token from the retired set appears inside a fence, against an
   explicit allow-list. **This is the check that makes the relabel stick.**

Without one of these, the arrangement is maintained by prose discipline alone,
in the repository whose first sentence is that prose discipline does not hold.
Nine waves of evidence say it will drift again, and the evidence in this report
is that it already has — inside the commit that created it.

---

## What would settle the uncertain claims

- **D16-5 (`SCK`)**: confirm from the ESP32-S3 pin allocation that IO35 (SPI2
  clock) and IO38 (SPI3 clock) are genuinely separate nets. `carrier.md`'s block
  diagram shows `SPI3+latch` and `SPI2+2×CS` on different header groups `[repo]
  carrier.md:69`, which I read as confirming it, but I did not find a pin table
  that states it outright.
- **D16-7 (`5 V` buck A / buck B)**: `power-entry-instrument.md` lists buck B's
  location as open `[repo] :24`. If buck B ends up on the display board, the two
  `5 V` nets are on different boards and the collision is worse, not better.
- **D16-15**: I claim `OE_INST` and `OE_MOD` are the *same* net — both are ties
  to their board's ground, and the two boards' grounds are joined by `PWR_GND` on
  umbilical pin 6 `[repo] power-entry.md:32, power-entry-instrument.md:20`. If
  that is right, `pcb-pipeline.md:71`'s framing of `OE` as "two different physical
  nets" is loose, the qualification is a readability improvement rather than a
  short prevented, and it is the one of the five that could safely have been left
  alone. A ground-topology reviewer should confirm before anyone acts on it.
