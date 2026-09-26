# N5 — The deliberate holes

**Slice:** every `external_endpoints` entry and every single-endpoint net across
all 22 `netlist.yaml` files.
**Measured against:** `d1f0cb7` (`HEAD` is `5c39a4e`, which adds only this wave's
own README `[test] git diff --stat d1f0cb7 HEAD` → one file, `docs/review/**`, so
the corpus is `d1f0cb7`). `tools/` frozen, not modified.
**Cold:** nothing under `docs/review/` was read.

## Method

The checker prints counts, not the list, so I enumerated the holes directly with
PyYAML rather than by grepping:

```
[test] python3 <script> over hardware/**/netlist.yaml, for each file printing
       external_endpoints and every net with len(endpoints) < 2
```

**Result: 39 `external_endpoints` entries across 12 netlists, and 39
single-endpoint nets. The two sets are identical** — every net with fewer than
two endpoints is declared, and every declared entry names a net in the same
file that has exactly one endpoint. There is no undeclared single-endpoint net
anywhere, and no stale entry naming a net that has since gained a second
endpoint. `module/breath-response-shaper` carries an explicit
`external_endpoints: []`; the other nine netlists have none.

Baseline for every `[test]` below:

```
[test] python3 tools/check-netlist.py
netlist: 22 circuit(s), 197 components, 254 nets, 55 master net(s) | 0 problem(s)
  | 0 drawing page(s) without a netlist | 0 master endpoint(s) awaiting one
per-board bundles not resolved to single nets: KEY_BITS, MARKER_BITS
instances: 102 row(s) placed exactly to BOM qty, 4 counted by section, 7 short:
  C-BUCK-IN 1/2, C-DECOUPLE 1/19, C-DECOUPLE-CARRIER 5/8, HDR-DEV 1/6,
  J-CHAIN 1/8, R-OPAMP-IN 6/7, U-BREATH 1/2
EXIT=0
```

39 of 254 nets — **15 %** of the netlisted design — is an endpoint that stops at
a reason rather than at a pin.

## The inventory, classified

| # | Circuit | Entry | Class | Verdict |
|---|---|---|---|---|
| 1 | `carrier/breath-adc` | `ADC_CH1` | decided NC | sound |
| 2–5 | `carrier/display-and-service-uart` | `SVC_TXD_LOOM`, `SVC_RXD_LOOM`, `DISP_CONSOLE_TXD`, `DISP_CONSOLE_RXD` | **open** | sound, exemplary |
| 6–7 | `carrier/display-and-service-uart` | `SPARE1`, `SPARE2` | decided spare | sound (ADR 0009) |
| 8 | `carrier/display-and-service-uart` | `J_DISP_NC` | decided NC | sound |
| 9–10 | `carrier/led-strip-drive` | `SPARE_GATE_B_OUT`, `SPARE_GATE_D_OUT` | decided NC | sound |
| 11 | `carrier/carrier` | `TVS_SPARE` | decided NC | sound (checked hard, see below) |
| 12 | `carrier/power-entry-instrument` | `AGND_INST` | model | **N5-6 — reason false** |
| 13 | `carrier/power-entry-instrument` | `PLATE_BOND` | physical | sound |
| 14–15 | `cluster/key-marker-and-bits` | `MARKER_HIGH`, `MARKER_LOW` | model | **N5-3, N5-4, N5-5** |
| 16–18 | `cluster/key-marker-and-bits` | `FREE_BIT_1..3` | model | **N5-4** |
| 19 | `cluster/key-register` | `QH_BAR` | decided NC | sound |
| 20–27 | `cluster/key-register` | `KEY_IN_A..H` | model | **N5-3** |
| 28–29 | `interfaces/key-chain-loom` | `CHAIN_SPARE_1`, `CHAIN_SPARE_2` | decided spare | sound (ADR 0009) |
| 30–31 | `module/breath-output-stage` | `RAIL_POS`, `RAIL_NEG` | **false hole** | **N5-1** |
| 32–33 | `module/dac8568` | `DAC_CH6_UNUSED`, `DAC_CH8_UNUSED` | decided NC | sound |
| 34 | `module/digital-and-supervision` | `SPARE_GATE_OUT` | decided NC | sound |
| 35 | `module/digital-and-supervision` | `CS_PULLUP_TOP` | **open** | sound, exemplary |
| 36–37 | `module/pitch-stage` | `TRIM_OFFSET_BOTTOM`, `TRIM_GAIN_STRAP` | **open** | sound (**N5-10** on the second) |
| 38 | `module/umbilical-load-switch` | `ON_DIVIDER` | **open** | sound |
| 39 | `module/umbilical-load-switch` | `PWRGD` | decided NC | sound, but **N5-7** |

**8 of the 39 are genuinely undecided questions. 14 are decided no-connects or
ADR 0009 spares. 14 are consequences of a modelling choice, not of an open
design question. 1 is physical. 2 are not holes at all.**

That ratio matters for how the count reads: "39 unasserted endpoints" sounds
like 39 unfinished decisions and it is eight.

---

# Findings

## N5-1 — `module/breath-output-stage` · `D-JACK-CLAMP.K` / `D-JACK-CLAMP.A` · **HIGH**

**Claim.** `RAIL_POS` and `RAIL_NEG` are not holes: both rails are already
asserted for this circuit by the page, by the master net list and by the same
netlist file, and two sibling circuits net the identical clamp normally — so the
stated reason is false and the two entries should not exist.

**Evidence.**

The declared reason `[repo hardware/module/breath-output-stage/netlist.yaml]`:

> `# Endpoints deliberately outside this circuit's scope. Without this the`
> `# two-endpoint rule would fire on the clamp rails, which terminate on the`
> `# module's supply rather than inside this circuit.`

Four refutations, in increasing order of how close they sit to the file:

1. **The same file.** `MODULE_ANALOG_NEG12` is a declared port (`dir: in, from:
   module/power-entry`) *and* a net with two endpoints (`port:
   MODULE_ANALOG_NEG12`, `R-BREATH-OFFNEG.1`). `D-JACK-CLAMP.A` is the same node.
   The −12 V supply is not "outside this circuit's scope"; it is two lines above
   the hole. `[repo hardware/module/breath-output-stage/netlist.yaml]`
2. **The page's own `## Interfaces` table** asserts the connection in words:
   *"`MODULE ANALOG +12V`, `MODULE ANALOG −12V` | in | `module/power-entry` | — |
   Op-amp supplies, and `D-JACK-CLAMP` returns to both rails."*
   `[repo hardware/module/breath-output-stage/breath-output-stage.md]`
3. **`hardware/nets.yaml`** lists `module/breath-output-stage` in the `receivers:`
   of both `MODULE_ANALOG_POS12` and `MODULE_ANALOG_NEG12` — the master already
   asserts that both rails reach this circuit. `[repo hardware/nets.yaml]`
4. **Both sibling CV circuits do it the normal way.** `module/mod-channels` nets
   `D-JACK-CLAMP-1..4.K` onto `MODULE_ANALOG_POS12` and `.A` onto
   `MODULE_ANALOG_NEG12`; `module/pitch-stage` does exactly the same for its one
   clamp. One of three CV outputs treats the clamp rails as unassertable.
   `[repo hardware/module/mod-channels/netlist.yaml, hardware/module/pitch-stage/netlist.yaml]`

**Why this is worse than cosmetic.** `D-JACK-CLAMP` is the part that stops a
patched −12 V from reaching the summer's output. A netlist that declares its two
rail endpoints "outside scope" transcribes to a PCB net list with a clamp wired
to nothing at one end, which passes every check here and fails silently on the
bench. The repo's own rule cuts the other way too: `hardware/nets.yaml` says *"an
asserted connection the board does not have is worse than a missing one"* — this
is a **missing** connection that three documents assert.

**What would have to be true for this to be wrong.** That the breath jack's
BAV99 is *not* returned to the module analog rails but to something else — which
would contradict the page's Interfaces row, `nets.yaml`, and the two sibling
circuits at once; or that `MODULE_ANALOG_POS12`/`NEG12` at the breath stage are
different nodes from the ones `pitch-stage` and `mod-channels` name, for which
there is no evidence anywhere.

**Smallest fix, verified.** Declare the `MODULE_ANALOG_POS12` port, put
`D-JACK-CLAMP.K` on it, add `D-JACK-CLAMP.A` to the existing
`MODULE_ANALOG_NEG12` net, delete both entries. Tested in a clone (the shared
tree was not touched):

```
[test] git clone /home/user/Woody /tmp/n5-clone; edit only
       hardware/module/breath-output-stage/netlist.yaml as above; then
       python3 tools/check-netlist.py
netlist: 22 circuit(s), 197 components, 253 nets, 55 master net(s) | 0 problem(s)
EXIT=0
```

Net count 254 → 253 (two false holes removed, one real net added),
`external_endpoints` on that circuit becomes `[]`, zero problems. No other file
changes.

---

## N5-2 — `carrier/display-and-service-uart` · `J-DISP.SUPPLY` · **MEDIUM**

**Claim.** The netlist asserts `INST_5V_B` onto `J-DISP.SUPPLY`, choosing one
branch of a decision three documents call open — and unlike every other open
item on this circuit, nothing on the `J-DISP` side records it.

**Evidence.**

- The netlist asserts it flatly: `INST_5V_B: [port: INST_5V_B, J-DISP.SUPPLY]`,
  and `J-DISP`'s component note lists what the connector carries without
  mentioning that the rail identity is open.
  `[repo hardware/carrier/display-and-service-uart/netlist.yaml]`
- The page's Interfaces table: *"5 V (or `+12V`) on `J-DISP` … **Which of the two
  rails it is depends on where buck B lives, which is open in `carrier.md`**"*
  `[repo hardware/carrier/display-and-service-uart/display-and-service-uart.md]`
- `bom.csv` row `J-DISP`: *"OPEN ON TWO THINGS, AND BOTH ARE DECIDED AT LAYOUT:
  which rail travels on it - 5V or +12V …"* `[repo hardware/bom.csv:30]`
- `power-entry-instrument.md` *Still open*: *"Either it moves to the display board
  and +12 V goes up the loom, or `C-BULK-DISP` does the job … **Pick one before
  `J-DISP`'s conductor list is fixed.**"*
  `[repo hardware/carrier/power-entry-instrument/power-entry-instrument.md]`

The same circuit **does** leave the console pair unasserted for a strictly
smaller ambiguity (which board's console travels — *"it changes nothing else,
because the conductor count is the same either way"*). The supply rail is the
ambiguity that changes the conductor's voltage by 7 V, and it is the one that got
asserted. The only trace of the open question inside the netlist tree is
`U-BUCK-B`'s component note on the *other* circuit: *"WHERE IT LIVES IS OPEN - if
it moves to the display board, +12 V goes up the loom instead"*
`[repo hardware/carrier/power-entry-instrument/netlist.yaml]`.

**Secondary, same sentence.** The Interfaces row's decision pointer is dangling:
it says the item is *"open in `carrier.md`"*, and

```
[test] grep -n -i "buck B" hardware/carrier/carrier.md      → no output
```

The item was moved to `power-entry-instrument.md`'s *Still open* ("*Moved verbatim
from `carrier.md`'s `Still open` list*"). A reader following the netlist's own
authority chain for this assertion lands on a page that no longer carries it.

**What would have to be true for this to be wrong.** That "which rail travels the
loom" is settled at 5 V and the three documents above are stale — in which case
the defect is those three rather than the netlist, and `bom.csv`'s `J-DISP` status
should not be `open`. Either way one of the four is wrong, and nothing prints it.

**Smallest fix.** One sentence in `J-DISP`'s component note: that `SUPPLY` is
netlisted as `INST_5V_B` on the working assumption that buck B stays on the
carrier, and that it becomes `UMBILICAL_POS12` if it does not — plus repointing
the Interfaces row at `power-entry-instrument.md`. (Making it an
`external_endpoints` entry is the *other* consistent answer and is a bigger
change; either is better than silence.)

---

## N5-3 — `cluster/key-register` · `U-KEYS.A..H` and `KEY_BITS`/`MARKER_BITS` · **MEDIUM**

**Claim.** The reason given for these eight holes — repeated in three files — is
that the bit allocation is *"DIFFERENT ON EVERY BOARD"* and that the allocation
table *"has four different rows"*. It has **three** distinct rows: `right_thumb`
and `right_hand` are identical in exactly the respect claimed.

**Evidence.** The allocation table
`[repo hardware/cluster/key-marker-and-bits/key-marker-and-bits.md]`, read as the
class of each input:

| Device | `H` | `G` | `F` | `E` | `D` | `C` | `B` | `A` |
|---|---|---|---|---|---|---|---|---|
| `right_thumb` | sw | sw | sw | sw | sw | sw | **M** | **M** |
| `right_hand` | sw | sw | sw | sw | sw | sw | **M** | **M** |
| `left_thumb` | sw | sw | sw | sw | **M** | **M** | free | free |
| `left_hand` | sw | sw | sw | sw | sw | **M** | **M** | free |

`right_thumb`'s `E`/`D`/`C` are the reserved spare-switch positions `sw+ sw− sw?`,
and the page says *"Every position above gets the full
`R-KEY-PU`/`R-KEY-SER`/`C-KEY` network`", including the three unfitted spares"* —
so for netlisting purposes they are switch positions like any other. Rows 1 and 2
are byte-identical as a switch/marker/free map.

The claim appears three times:

1. `[repo hardware/cluster/key-register/netlist.yaml]` — *"Which of A..H is a
   switch, a marker strap or a free bit is DIFFERENT ON EVERY BOARD -
   key-marker-and-bits.md's allocation table has four different rows"*
2. `[repo hardware/cluster/key-marker-and-bits/netlist.yaml]` — *"Which of a
   device's A..H carries a marker is different on every board - the allocation
   table on this page has four different rows"*
3. `[repo hardware/nets.yaml]`, `KEY_BITS` note — *"which of the eight is a
   switch is different on all four boards - key-marker-and-bits.md's allocation
   table has four different rows"*; and `MARKER_BITS` — *"they sit on different
   inputs on every board"*. Marker **positions** are `(B,A)`, `(B,A)`, `(D,C)`,
   `(C,B)` — the first two are the same inputs.

**The conclusion survives; the reason does not.** Three distinct rows is still
not one, so a `replicated: 4` netlist genuinely cannot name these endpoints. And
one narrower version of the claim *is* true and is the one worth writing: the
marker **level** assignment differs on all four boards — HIGH/LOW lands on
`(B,A)`, `(A,B)`, `(C,D)`, `(B,C)` respectively `[repo` marker levels table,
`key-marker-and-bits.md]`, four distinct ordered pairs. So `MARKER_HIGH`/
`MARKER_LOW` are per-board in the strong sense; `KEY_BITS` is per-board in the
three-of-four sense.

This is the shape `CLAUDE.md` calls out under review-wave slicing — *a fix whose
own explanation restates the wrong value* — except here it is the justification
for a deliberate hole, restated into two more files after the first.

**What would have to be true for this to be wrong.** That a reserved-but-unfitted
switch position is a different endpoint class from a fitted one, which the page
denies in the sentence quoted above; or that I have misread the table.

**Smallest fix.** In all three places: *"the allocation has three distinct rows,
and the marker level assignment differs on all four"*. Nothing else changes.

---

## N5-4 — `cluster/key-marker-and-bits` · `FREE_BIT_1..3`, `MARKER_HIGH`, `MARKER_LOW` · **MEDIUM**

**Claim.** These five holes are framed as an allocation nobody has decided. The
allocation *is* decided, on the page the netlist sits beside; the real obstacle is
a modelling choice in a different file; and the one live decision that could
delete all three free-bit resistors is not cited.

**Evidence.**

- The far ends are named exactly. Free bits: `left_thumb` `B` and `A` (bits 22,
  23) and `left_hand` `A` (bit 31). Markers: the per-device input **and level**
  table. Both on `key-marker-and-bits.md`, three screens above the netlist, under
  a heading that says **DECIDED 2026-09-21** and a closing line *"This is
  hard-wired copper on boards that bond into the instrument. It has to be right
  before the boards are ordered."* `[repo hardware/cluster/key-marker-and-bits/key-marker-and-bits.md]`
- So the obstacle is not that the allocation is unknown. It is that
  `cluster/key-register` declares `replicated: 4` with one shared `U-KEYS`, so
  there is no pin to name a per-board endpoint *on*. That is a property of
  `key-register/netlist.yaml`, and `key-register`'s own header states it correctly
  (*"Resolving it means four board variants"*). `key-marker-and-bits`'s header
  does not; it attributes the hole to the allocation instead.
  `[repo hardware/cluster/key-register/netlist.yaml]`
- **Only three of the three free-bit pull-ups exist in total** — `R-KEY-PU` is
  qty 24 = 21 switch networks + 3 free bits `[repo hardware/bom.csv]` — so they are
  not replicated at all: they are three specific parts on two named boards. "Per
  board" is the wrong axis for them.
- The netlist gives no decision criterion for any of the five, and the live
  decision that governs the free bits is on the page and uncited:
  *"**Whether the last 3 free bits should be marker bits too**, making it 11 …
  strapping them costs *nothing* where pulling them costs three resistors."*
  If that lands, `R-KEY-PU-FREE1..3` cease to exist and `FREE_BIT_1..3` are not
  holes but deletions. That is the strongest available reason for leaving them
  unasserted and it is not the one given.

**What would have to be true for this to be wrong.** That the allocation table and
the marker-level table are proposals rather than the allocation — the levels table
is headed *"Proposed levels:"* under a section headed *"DECIDED 2026-09-21"*, so
the page is genuinely ambiguous about its own status. If "proposed" is the
operative word, then the holes are right and **that** is the reason to write down,
and the page's two headings need reconciling. Either way the reason currently
given is not the true one.

**Smallest fix.** Replace the "per board" framing in
`key-marker-and-bits/netlist.yaml` with the two real reasons: the endpoints are
named on this page but cannot be expressed against a `replicated: 4` register, and
the free bits are open on the page's own 8/3-versus-11 question. Resolve the
DECIDED/Proposed heading clash on the page.

---

## N5-5 — `cluster/key-marker-and-bits` · `MARKER_HIGH` ≡ `V3V3_CHAIN`, `MARKER_LOW` ≡ `GND_CHAIN` · **MEDIUM**

**Claim.** These two nets have no endpoint of their own: each consists of a single
`port:` reference that is *already* an endpoint of another net in the same file.
They are second names for the rails, not nets — the defect
`hardware/README.md` records as *"'nets' that turned out to be one node"* — and
`check-netlist.py` structurally cannot see it.

**Evidence.** `[repo hardware/cluster/key-marker-and-bits/netlist.yaml]`

```
V3V3_CHAIN:   [port: V3V3_CHAIN, R-KEY-PU-FREE1.1, R-KEY-PU-FREE2.1, R-KEY-PU-FREE3.1]
MARKER_HIGH:  [port: V3V3_CHAIN]          # the same port, second net
GND_CHAIN:    [port: GND_CHAIN, ...]
MARKER_LOW:   [port: GND_CHAIN]           # the same port, second net
```

The marker strap *is* copper from the rail to a register input — the file says so
— so electrically `MARKER_HIGH` and `V3V3_CHAIN` are one node and the correct
model is the register input joining `V3V3_CHAIN`. Why no check fires: the
pins-used-exactly-once rule is built only from `REF.PIN` endpoints —
`used.append((ref, pin))` happens inside the `"." in ep` branch — so a `port:`
appearing in two nets is never counted `[repo tools/check-netlist.py]`, and the
baseline run above confirms it passes.

**Consequence.** Two of the 39 holes are an artefact of naming, so the honest
count of unasserted strap endpoints here is 8 (two per board) and the file
expresses them as 2. A reader reconciling "eight strap connections" in the header
against two nets cannot tell which number is the design.

**What would have to be true for this to be wrong.** That `MARKER_HIGH` is
intended as a *label for the eight strap conductors* rather than as a net — which
is defensible as documentation but is not what a file that calls itself
authoritative for connectivity asserts, and is the same argument
`hardware/nets.yaml` rejects for `GND_CHAIN` by recording it as *"a separate name
for the five conductors in the ribbon, not a separate node"* **in a note**, not as
a second net.

**Smallest fix.** Fold the two into a comment on `V3V3_CHAIN`/`GND_CHAIN` naming
the eight strap endpoints as unassertable, and drop the two nets — or keep them
and say in one line that they are aliases, not nodes.

---

## N5-6 — `carrier/power-entry-instrument` · `AGND_INST` · **MEDIUM**

**Claim.** The reason given is false, and the consequence is that the
single-point analog-to-power ground tie — which this circuit exists to originate —
is asserted in no file a tool reads.

**Evidence.** The declared reason
`[repo hardware/carrier/power-entry-instrument/netlist.yaml]`:

> `# THE SINGLE TIE, and it is copper rather than a part. AGND_INST reaches`
> `# PWR_GND at exactly one point on this board … so there is nothing here to`
> `# give the net a second endpoint.`

The second endpoint is the tie itself. `PWR_GND` is a net in the same file with
nine endpoints; what is missing is any object joining the two. And the "copper
rather than a part" argument is refuted twice inside this corpus, once inside this
very file:

- `MECH-GNDBOND` — a **ring terminal** — is modelled here as a two-pin component
  with a BOM row, and its far end (`PLATE_BOND`, a hole in an aluminium plate) is
  the hole next door. `[repo hardware/carrier/power-entry-instrument/netlist.yaml]`
- `LK-CLR` on `module/dac8568` — *"NORMALLY OPEN, and copper rather than a part"* —
  is modelled as a two-pad component with a BOM row and appears in two nets.
  `[repo hardware/module/dac8568/netlist.yaml]`

So pure copper and pure mechanical hardware are both netlistable here when
someone wants the node checked.

**Why it matters.** `breath-adc`'s Interfaces table asserts the tie in prose
(*"the instrument analog star … **tied to `PWR_GND` at one point**"*
`[repo hardware/carrier/breath-adc/breath-adc.md]`), `hardware/nets.yaml` gives
`AGND_INST` `origin: carrier/power-entry-instrument`, and the tracked figure
`dig-gnd-topology` is `status: disputed` with `decided_by` naming the 2-layer/
4-layer decision `[repo config/figures.yaml]`. The one connection on the
instrument board that the disputed figure is about is in no netlist, and no check
can notice its absence because the circuit declaring it exempted itself.

Note also that the port is self-referential: `AGND_INST: {dir: ref, from:
carrier/power-entry-instrument}` — a circuit declaring a net as arriving from
itself. `nets.yaml` uses `origin:` for exactly this and the `from:` field is
unchecked, so it passes.

**What would have to be true for this to be wrong.** That the tie is a layout
instruction rather than a schematic connection — a stitching via placed by the
layout engineer, with nothing to buy. That is a real position, and if it is the
position then the file should say *that* ("the tie is a layout constraint, not a
node; `dig-gnd-topology` owns it") rather than "there is nothing here to connect",
because the two sentences tell a reader to do different things.

**Smallest fix.** Correct the comment to name the tie as the missing endpoint and
point at `dig-gnd-topology`; if the tie is to be checkable, a `LK-` style strap
row is the pattern already in use.

---

## N5-7 — `module/umbilical-load-switch` · `U-LOADSW.PWRGD` · **MEDIUM**

**Claim.** The `PWRGD` hole is honest — nothing reads that pin — but the `FB`
divider on the same part is *sized* from a hard requirement on it. The argument
does not survive its own hole.

**Evidence.**

- The hole: *"PWRGD IS NOT USED. The presence detect that would have read it is
  deleted, and the panel indicator's 'latched' signal is proposed only"*
  `[repo hardware/module/umbilical-load-switch/netlist.yaml]`. Verified: `panel-led.md`
  proposes taking the indication from `TIMER` **or the gate**, not from `PWRGD`
  `[repo hardware/module/panel-led/panel-led.md]`; `link-supervision.md` is headed
  *"NOT FITTED. Nothing in this directory is on the board"*
  `[repo hardware/module/link-supervision/link-supervision.md]`. The pin is read by nothing.
- The divider: *"The divider is chosen at the `PWRGD` end, because that is the
  end with a hard requirement. **`PWRGD` must release below the worst-case
  delivered output.**"* — then `V_FB`/`V_OUT` = 1.313 V / 10.5 V → ratio 7.00 →
  `R-FB-HI` 35.7 kΩ, `R-FB-LO` 5.11 kΩ, with a margin table whose first two rows
  are `PWRGD` release and `PWRGD` re-assert.
  `[repo hardware/module/umbilical-load-switch/umbilical-load-switch.md]`
- `R-FB-HI`'s BOM row carries the same reasoning and the datasheet law it rests
  on: the foldback limit reaches its full value *"when VFB is 0.5V or higher"*
  `[repo hardware/bom.csv:` `R-FB-HI`, quoting `164112fc p.5]`. The behaviour the
  board actually depends on is the 0.5 V threshold. The 1.313 V threshold governs
  only the flag.

So the divider's numbers may well be right, but the stated reason for choosing
them is a requirement on an output that is a declared no-connect. The surviving
constraints are the foldback knee (full limit available at `V_OUT` = 3.99 V) and
the instrument buck's 8 V input minimum — the latter is already in the page, in a
subordinate clause.

**What would have to be true for this to be wrong.** That `PWRGD` is connected
somewhere (it is not — the netlist is authoritative and declares it external), or
that the LT1641's foldback release is tied to 1.313 V rather than 0.5 V (the
datasheet quote in the BOM row says otherwise), or that `PWRGD` is expected to be
used later and the divider is being sized now for that — which is a legitimate
position and is not the one written.

**Smallest fix.** One clause in the sizing section: the divider is sized at the
1.313 V end because it fixes the 0.5 V foldback knee by the part's own ratio, and
`PWRGD` itself is currently unused (`netlist.yaml`). Nothing numerical moves.

---

## N5-8 — `module/panel-led` · `LED-PANEL.K` · **LOW–MEDIUM**

**Claim.** This is the mirror image of the holes above: the netlist **asserts** a
connection its own page calls undecided, and because it is an assertion rather
than a hole, nothing prints it.

**Evidence.** The page's Interfaces table: *"LED return | ref | `module/power-entry`
| `dig-gnd-topology` | **Not drawn anywhere in the corpus.** The rail it comes
from is the analog one; **which ground it lands on is the disputed figure**"*
`[repo hardware/module/panel-led/panel-led.md]`. `dig-gnd-topology` is
`status: disputed` with three live candidates `[repo config/figures.yaml]`.
The netlist asserts `AGND_MOD: [port: AGND_MOD, LED-PANEL.K]`, with the admission
in a comment: *"WHICH GROUND IT LANDS ON IS THE DISPUTED FIGURE … if the figure
settles the other way this line moves with it."*
`[repo hardware/module/panel-led/netlist.yaml]` — and `hardware/nets.yaml` lists
`module/panel-led` under `AGND_MOD`'s `reference:`, so the master asserts it too.

`module/pitch-stage` faced the same situation on two trimmer terminals and chose
`external_endpoints`, with the rule quoted in its header (*"an asserted connection
the board does not have is worse than a missing one"*). Two circuits, one
disputed question each, opposite policies.

This one is defensible — the LED must return somewhere, the analog rail is the
one it comes from, and it is ~4 mA, not a signal. But it is a decision recorded
only in a YAML comment, where `external_endpoints` would have put it in the
checker's output.

**What would have to be true for this to be wrong.** That the disputed part of
`dig-gnd-topology` is only *where the two grounds meet* and not *which ground a
part returns to* — in which case the page's Interfaces row overstates the dispute
and it is the row that needs fixing, not the netlist.

**Smallest fix.** Pick one of the two and make the other match: either add a
`Still open` bullet on `panel-led.md` recording that the netlist has provisionally
picked `AGND_MOD`, or soften the Interfaces row. One line.

---

## N5-9 — `module/dac8568` · `CLR` port provenance · **LOW–MEDIUM**

**Claim.** The `CLR` port declares `from: module/link-supervision` — a circuit
whose page is headed *"NOT FITTED. Nothing in this directory is on the board"*
and which has no netlist. `hardware/nets.yaml` records the same net as
`undriven: true`. The netlist names a driver that does not exist.

**Evidence.** `CLR: {dir: in, from: module/link-supervision}`
`[repo hardware/module/dac8568/netlist.yaml]`; `CLR: … undriven: true, pull:
"R-CLR-PU holds it inactive", receivers: [module/dac8568]` and **no `driver:`**
`[repo hardware/nets.yaml]`; *"NOT FITTED…"*
`[repo hardware/module/link-supervision/link-supervision.md]`. The checker
validates `dir: in` against the master's `receivers:` list — `module/dac8568` is
in it — and never looks at `from:`, so it passes
`[repo tools/check-netlist.py]`.

The page is honest in prose (*"Nothing drives it — the part that did is not
fitted"*), so this is the data file drifting from the page rather than a wrong
design. But `from:` is the field a future KiCad generator would read.

**What would have to be true for this to be wrong.** That `from:` is intended as
"the circuit that *would* drive this" rather than "the circuit that does" — in
which case it is being used in two senses across the 22 files, and the one place
it means something else should say so.

**Smallest fix.** Drop `from:` on that port, or make it
`from: none, was: module/link-supervision (not fitted)`.

---

## N5-10 — `module/pitch-stage` · `TRIM-GAIN.CW` · **LOW**

**Claim.** `TRIM_GAIN_STRAP` is a real hole, but its stated openness — *"which
end, and whether it is a footprint option, is open"* — is half closed by an
assertion in the same file.

**Evidence.** The netlist already asserts the series path as `W`→`CCW`
(`GAIN_TRIM_MID: [R2.2, TRIM-GAIN.W]`, `JACK_TIP: […, TRIM-GAIN.CCW, …]`)
`[repo hardware/module/pitch-stage/netlist.yaml]`. Given that, the page's
requirement — *"Strap the wiper to one end so a dirty track degrades to a known
resistance rather than an open circuit"*
`[repo hardware/module/pitch-stage/pitch-stage.md]` — has one buildable answer:
`[calc]` strapping `W` to `CW` shorts the unused section, so a lifted wiper
degrades to the full `CW`–`CCW` 200 Ω; strapping `W` to `CCW` shorts the *used*
section, making the trimmer 0 Ω at all settings and deleting the trim. So "which
end" is decided by the series-path choice this file has already made, and what
remains open is only whether the strap is a footprint option.

**What would have to be true for this to be wrong.** That the series path is not
settled either — i.e. `W`→`CW` with `CCW` as the strap terminal is still on the
table, in which case the netlist has asserted half of an open item (the same
shape as N5-2, one scale smaller) and should say so; or that the intended strap is
a fixed resistor across `CW`–`CCW` rather than wiper-to-end, which is not what the
page asks for.

**Smallest fix.** Either add "(given the `W`→`CCW` series path asserted above, the
strap is `CW`→`W`; what is open is the footprint)" to the hole, or note that the
series terminal choice is itself provisional.

---

## N5-11 — `module/breath-response-shaper` · `V_SHAPED` · **LOW**

**Claim.** The one boundary net of this circuit that the page names as `out` has
no port, no `hardware/nets.yaml` entry, and no `external_endpoints` entry — so
alone among the open insertion questions, nothing in the toolchain prints it.

**Evidence.** The page's Interfaces table: *"`V_shaped` | out |
`module/breath-output-stage` | — | Drawn feeding the gain attenuator. *Where it
inserts* is argued below and is open"*
`[repo hardware/module/breath-response-shaper/breath-response-shaper.md]`. The
netlist's `V_SHAPED` net has three local endpoints (`U-RESP-A.OUT`,
`R-RESP-FB.2`, `POT-RESP.CCW`) and deliberately stops there — *"WHERE THIS
INSERTS IS OPEN … so this file stops here rather than asserting a path into
module/breath-output-stage"* — which is the right call. But because the net has
three endpoints it is not a declared hole, it is absent from `nets.yaml` (which
carries `BREATH_INAMP_OUT` with `proposed: [module/breath-response-shaper]` but
has no `V_SHAPED` entry at all), and the `external_endpoints: []` on this circuit
says positively that it has no holes. `[repo hardware/nets.yaml,
hardware/module/breath-response-shaper/netlist.yaml]`

This is correctly recorded *in prose*, three times over, and the circuit is
`proposed` anyway — hence LOW. It is listed because my slice's question is "what
prints", and the answer here is nothing.

**What would have to be true for this to be wrong.** That an unfitted circuit's
undecided output is not a hole worth printing until the circuit is adopted, which
is a reasonable line to draw — it just is not the line `nets.yaml`'s `proposed:`
mechanism draws for the same circuit's input.

**Smallest fix.** None required if the position above is deliberate; otherwise one
line on the page's *Open before layout* bullet noting that `V_shaped` is in no
machine-readable file yet.

---

## N5-12 — `J-LED-L` / `J-LED-R` · **LOW, suspicion, adjacent to my slice**

ADR 0009 says *"**Run two spare conductors in every internal loom.**"*
`[repo docs/decisions/0009…:524]`, and it is cited as the authority for
`SPARE1`/`SPARE2` (display loom) and `CHAIN_SPARE_1`/`_2` (chain loom). The LED
loom has none: `J-LED-L` and `J-LED-R` are 4-way with all four pins netted
(`POS12`, `GND`, `DI`, `BI`) `[repo hardware/carrier/led-strip-drive/netlist.yaml,
hardware/bom.csv]`, and no page says why this loom is exempt. Either it is exempt
(the far end is a tape, not a board) and that should be one clause on the
`J-LED-L` row, or it is a missing pair. Marked suspicion: I have not checked
whether ADR 0009's "internal loom" is defined narrowly enough to exclude it.

---

# Holes I tried to break and could not

These are results, not gaps. Each was attacked on the specific claim in its
comment.

**`carrier/carrier` · `TVS_SPARE`** — *"J-UMB pin 8 is DIG_GND, which is a return
rather than something to clamp."* Pin 8 **is** `DIG_GND`
`[repo hardware/interfaces/spi-link/netlist.yaml]`. I then tried the stronger
objection: `AGND_SENSE` (pin 2) is a *signal*, not a ground — `nets.yaml` insists
on it — so is there an unclamped signal conductor beside a spare clamp channel?
**No:** `interfaces/breath-sense-link` places `D-TVS-BREATH-RET` on exactly that
conductor, paired with `D-TVS-BREATH-SIG` on `BREATH_SENSE`
`[repo hardware/interfaces/breath-sense-link/netlist.yaml]`. All four umbilical
signal conductors are clamped; pins 6 and 8 are returns. The spare channel is
genuine and the reason holds.

**`module/digital-and-supervision` · `CS_PULLUP_TOP`** — the "rail does not exist
on this board" claim, and it is **true**.
`[test] grep -rn "3V3\|3\.3 V" hardware/module/` returns only (a) this hole's own
prose, (b) the matching *Still open* bullet, (c) `U-LVL-MOD`'s row describing the
*input* side as 3V3 SPI. The module makes ±12 V, bus +5 V and `DAC AVDD`
`[repo hardware/nets.yaml]`, and `R-SPI-PULL`'s row still places all six on the
module `[repo hardware/bom.csv]` — so the contradiction the hole names is real,
both halves of it. It carries a decision criterion (*"**Decided by:** which end it
sits at — a placement question, and the other five pulls are unaffected either
way"*). **This is the model the other 38 should be measured against.**

**`carrier/display-and-service-uart` · the four console-pair nets** — *"at most
one of those readings can be true of it."* Verified: the Interfaces table does
say both things — the real-time board's pair goes *"to `HDR-SERVICE` **and up
`J-DISP`**"* and the display board's pair arrives at `HDR-SERVICE` — and the loom
carries exactly one service trio of its nine conductors (`1 supply + 1 GND +
2 UART1 + 2 service + 1 GND + 2 spare = 9`) `[calc, repo` the page's conductor
list`]`. Two pairs, one trio. The hole is real and the page's *Still open* carries
*"**Decided by:** which board's console the service header is for when only one
can travel — and it changes nothing else, because the conductor count is the same
either way."*

**`module/umbilical-load-switch` · `ON_DIVIDER`** — *"THE UNDERVOLTAGE-LOCKOUT
DIVIDER IS NOT DESIGNED, and the page says so."* It does, in a section of its own
(*"### Still not designed: the `ON` pin"*), with the datasheet numbers the divider
needs and a decision criterion: *"the trip point is an ADR 0005 decision, not a
datasheet reading: pick it, then the divider is arithmetic."* Correctly recorded.
Minor: the item is **not** in that page's `## Still open` list, which contains
only the input-LC damping bullet — a reader scanning `Still open` misses the
UVLO divider entirely.

**`module/pitch-stage` · `TRIM_OFFSET_BOTTOM`** — *"V_ref nominal IS VREFOUT, a
divider can only go below it."* Confirmed against the page's own derivation: the
stage is gain exactly 2 with the reference at the bottom of the divider and the
intercept −2.500 V from `V_ref` = 2.500 V = `VREFOUT`, and the page's *Still open*
states the same conclusion independently (*"`TRIM-OFFSET` is not buildable as
described"*), with *"E10, with `R-TRIM-RANGE`"* as the criterion and `R-TRIM-RANGE`
existing as a `status: open` BOM row that says what decides it. This is the other
exemplary hole.

**`module/dac8568` · `DAC_CH6_UNUSED` / `DAC_CH8_UNUSED`** — these rest on a map
the file flags itself: *"CHANNEL NUMBER TO DATASHEET LETTER IS ORDINAL HERE …
**NO DOCUMENT IN THIS CORPUS STATES THAT MAP** `[derived, not cited]` … Contradict
it in ADR 0006 if it is wrong and this file follows."* I checked: ADR 0006
allocates by number and says *"two spare"*; nothing joins number to `VOUT` letter
`[test] grep -n "VOUT\|channel 6\|channel 8" docs/decisions/0006*.md` → only the
"two spare" line. The disclosure is accurate, it names what would overturn it, and
it decides which two pins a layout leaves open — so asserting it beats leaving it
implied. **This is the right way to write a derived assertion**, and it is worth
copying to the two places that currently assert without one (N5-2, N5-8).

**`carrier/led-strip-drive` · the two spare gate outputs** — inputs `2A` and `4A`
are on `PWR_GND`, matching the BOM row's *"TIE EVERY UNUSED INPUT TO VCC OR GND"*
and `module/digital-and-supervision`'s identical treatment of its spare gate
`[repo` both netlists`]`. Outputs driving nothing is correct. Sound.

**`carrier/power-entry-instrument` · `PLATE_BOND`**, **`cluster/key-register` ·
`QH_BAR`**, **`carrier/breath-adc` · `ADC_CH1`**, **`SPARE1`/`SPARE2`**,
**`J_DISP_NC`**, **`CHAIN_SPARE_1`/`_2`**, **`SPARE_GATE_OUT`** — all checked
against their pages and ADR 0009; all decided rather than open, all reasons true.

---

# Two things about the mechanism itself

**`external_endpoints` carries two meanings and the count conflates them.** "This
pin is deliberately unconnected" (14 entries) and "we do not yet know what this
connects to" (8 entries) are different facts with different consequences — the
first is finished, the second blocks layout — and they are one list. A second key
(`no_connect:` beside `external_endpoints:`, or a `why:` map) would make the
eight visible; today the only way to separate them is to read 39 comments, which
is what this slice did.

**The `port:`-in-two-nets gap (N5-5) is the one structural blind spot I found.**
`check-netlist.py` enforces pins-used-once rigorously for `REF.PIN` endpoints and
not at all for `port:` endpoints. Any two nets in one file may share a port
silently, which is a short in transcription and an alias in intent, and nothing
distinguishes them.
