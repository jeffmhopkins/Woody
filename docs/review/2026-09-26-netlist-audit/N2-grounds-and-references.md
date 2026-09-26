# N2 — grounds and references

**Slice:** every reference net and every return path, across all 22
`netlist.yaml` files and `hardware/nets.yaml`.
**Measured against:** `d1f0cb7`. Working tree is at `5c39a4e`, whose only change
is `docs/review/2026-09-26-netlist-audit/README.md`
`[test] git show --stat 5c39a4e → 1 file changed, docs/review/.../README.md`,
so the corpus under audit is `d1f0cb7` unmodified. `tools/` untouched; nothing
outside this file was written.
**Cold:** nothing under `docs/review/` was read.

**Baseline** `[test]`:

```
$ python3 tools/check-netlist.py --strict
netlist: 22 circuit(s), 197 components, 254 nets, 55 master net(s) | 0 problem(s)
    | 0 drawing page(s) still without a netlist | 0 master endpoint(s) awaiting one
per-board bundles not resolved to single nets: KEY_BITS, MARKER_BITS
instances: 102 row(s) placed exactly to BOM qty, 4 counted by section, 7 short: …
```

## What I checked

**The reference nets, found by enumeration rather than from a list.** Grepping
every ground-like token in the corpus `[test] grep -rohE '…GND…' hardware/
docs/decisions docs/reference config firmware README.md ROADMAP.md | sort |
uniq -c` gives, in order of frequency: `GND` 158, `AGND` 109, `PWR_GND` 89,
`DIG_GND` 48, `AGND_MOD` 44, `AGND_INST` 25, `AGND_SENSE` 20, `GND_CHAIN` 15,
`GNDBOND` 13, plus `V_AGND`, `RT_GND`, `GND_SVC`, `GND_SUPPLY`, `DISP_GND`,
`VIRTUAL_GND` (all of which are connector pin names or a local node, not nets).
`hardware/nets.yaml` carries exactly five `kind: reference` entries
`[repo hardware/nets.yaml]`:

| net | origin | `reference:` circuits | ref ports declared |
|---|---|---|---|
| `GND_CHAIN` | `interfaces/key-chain-loom` | 3 cluster circuits | 4 |
| `AGND_INST` | `carrier/power-entry-instrument` | 3 | 4 |
| `DIG_GND` | `module/power-entry` | 2 | 3 |
| `PWR_GND` | `module/power-entry` | 6 | 7 |
| `AGND_MOD` | `module/power-entry` | 6 (+1 `proposed:`) | 8 |

and one net that is deliberately *not* a reference: `AGND_SENSE`, "A SIGNAL,
NOT A GROUND … DO NOT MERGE IT WITH AGND_MOD"
`[repo hardware/nets.yaml:292-296]`.

I walked all 26 `dir: ref` ports, every net they name, and every pin on those
nets, against the owning page's `## Interfaces` row, the page's prose, the
page's drawing, and ADR 0004's ground-plan section
`[repo docs/decisions/0004-cv-interface-module.md:630-668]`.

---

## N2-1 — `AGND_MOD` is the return path for all six CV jack sleeves, on a net two of its own pages call "Not a return path"

**Severity: high.**

**Claim.** Three netlists put all six `J-CV` sleeves on `AGND_MOD`, which bonds
the module analog star to the rack's ground network through every patch cable,
at up to six points — against ADR 0004's rule that the analog return joins the
star "and nowhere else", and against two pages' own `## Interfaces` rows.

**Evidence.**

- `[repo hardware/module/pitch-stage/netlist.yaml:166-171]` `AGND_MOD` =
  `C-AA-PITCH.2`, `C-FILT-PITCH.2`, `R-BIAS-DAC.2`, **`J-CV-PITCH.SLEEVE`**.
- `[repo hardware/module/breath-output-stage/netlist.yaml:148-154]` `AGND_MOD` =
  `R-GAIN-FLOOR.2`, `POT-OFFSET.CCW`, `U-BREATH-SUM.IN+`, `C-OUT-BREATH.2`,
  **`J-CV-BREATH.SLEEVE`**.
- `[repo hardware/module/mod-channels/netlist.yaml:418-432]` `AGND_MOD` carries
  **`J-CV-MOD1.SLEEVE`** … **`J-CV-MOD4.SLEEVE`** plus five `R-BIAS-DAC` and
  four `C-FILT-MOD`.
- `[repo hardware/module/pitch-stage/pitch-stage.md]` `## Interfaces`:
  "`AGND_MOD` | ref | … | The module analog star, drawn `AGND`. `C-AA-PITCH`
  and `C-FILT-PITCH` shunt to it. **Not a return path** — see the figure".
- `[repo hardware/module/mod-channels/mod-channels.md]` `## Interfaces`:
  "… `C-FILT-MOD` shunts to it. **Not a return path** — see the figure".
- `[repo docs/decisions/0004-cv-interface-module.md:655]` "**The analog return
  is its own region**, joining at the star and nowhere else. The DAC's `AVDD`
  return and the in-amp's `REF` tie belong in it." Line 637 enumerates what that
  region carries: "Op-amps, DAC `AVDD`, the pitch stage's reference". Jack
  sleeves are not in that list.
- `[repo docs/decisions/0004-cv-interface-module.md:661-663]` already costs the
  rack ground at "~4.8 cents: the module shares a 16-pin ribbon return with
  every other module in the case" — and a patch cable's sleeve *is* that
  return, arriving at the analog star instead of at `J-PWR-EURO.GND`.
- No page anywhere in the corpus states where a `J-CV` sleeve returns
  `[test] grep -rni "sleeve" hardware/ docs/decisions docs/reference config` →
  only `pitch-stage.md:274` (a plug shorting tip to sleeve on insertion) and
  the `J-CV` BOM row's pinout note. `panel.md` says of each jack "A panel
  cutout. The net is that circuit's"
  `[repo hardware/module/panel/panel.md]`. So these three netlists are the
  first and only assertion of it, and all three chose the star.

**What would have to be true for this to be wrong.** Either (a) the corpus
somewhere says jack sleeves belong on the analog star and I missed it — I
grepped for `sleeve`, `SLEEVE`, `jack ground` and read all six jack rows and
`panel.md`; or (b) `AGND_MOD` and `PWR_GND` are intended to be one node at the
star with no functional distinction, in which case the sleeves' choice does not
matter — but that is contradicted by ADR 0004:651-659 and by
`power-entry.md`'s Grounding section; or (c) "Not a return path" in those two
`## Interfaces` rows means only "not a *supply* return path", in which case the
rows should say so, because a jack sleeve is the one return every reader will
think of.

**Smallest fix.** Move the six `SLEEVE` pins to `PWR_GND` and add a
`PWR_GND: {dir: ref, …}` port to `pitch-stage`, `breath-output-stage` and
`mod-channels` (and `PWR_GND`'s `reference:` list in `nets.yaml`) — or, if the
sleeves are meant to stay on the star, delete "Not a return path" from the two
rows and say in `nets.yaml`'s `AGND_MOD` note that six patch-cable returns land
on it. One of the two, but not the present state, where the authoritative file
and the page say opposite things about the same six pins.

---

## N2-2 — `DIG_GND` has no instrument end: `J-UMB-INST.8` lands on nothing, and the page that names its peer names a circuit with no such port

**Severity: high.**

**Claim.** `DIG_GND` is declared "Digital return, instrument to module" and is
`CS_MOD`'s return partner, but no netlist gives it an endpoint on the
instrument. Its instrument-side connector pin is netted and then stops.

**Evidence.**

- `[repo hardware/nets.yaml:329-335]` `DIG_GND`: `carries: "Digital return,
  instrument to module"`, `origin: module/power-entry`,
  `reference: [interfaces/spi-link, module/digital-and-supervision]`. No
  carrier-side circuit.
- `[repo hardware/interfaces/spi-link/netlist.yaml:89-92]` `DIG_GND` =
  `port` + `J-UMB-MOD.8` + `J-UMB-INST.8`. `J-UMB-INST` is "The instrument's,
  at the tail" (line 46).
- `[repo hardware/interfaces/spi-link/spi-link.md:41]` the `## Interfaces` row
  names the peers: "`DIG_GND` | instrument ↔ module | ref |
  **`carrier/carrier.md`** ↔ `module/power-entry`".
- `[repo hardware/carrier/netlist.yaml:20-45]` `carrier/carrier` declares 19
  ports. `DIG_GND` is not among them. Its only reference port is `PWR_GND`.
- `[repo hardware/carrier/carrier.md:223-231]` §4's drawing shows
  "`J-UMB pin 8 ──┘ DIG_GND`" where the `┘` closes the "pair (7,8)" bracket —
  an annotation, not a connection — and the clamp on the same drawing goes to
  `PWR_GND`, not to pin 8.
- `[repo config/figures.yaml:334-339]` the `umbilical-pinmap` figure's whole
  derivation is "**`CS` must have a ground partner**: it frames the word, MISO
  is deleted so a mis-frame is unreadable and sticky." A partner that is
  open-circuit at the driving end is not a partner.
- Consequence at the clamp: `[repo hardware/carrier/netlist.yaml:201-204]`
  `U-TVS-SPI.GND` is on `PWR_GND`, which the BOM row confirms is deliberate
  ("ALL FOUR CHANNELS SHARE ONE COMMON PIN (pin 2), so a single array cannot
  straddle `PWR_GND` and `DIG_GND`"
  `[repo hardware/interfaces/spi-link/bom.csv:4]`). So the three SPI signals
  are clamped to one reference on the carrier and paired with a different one
  down the cable, and the netlists assert no path between the two.

**What would have to be true for this to be wrong.** That pin 8 is genuinely
intended to be unconnected at the instrument end — in which case `nets.yaml`'s
`carries:` is wrong ("instrument to module"), `spi-link.md`'s Peer column is
wrong (`carrier/carrier.md`), and the `umbilical-pinmap` derivation loses its
reason. Or that `DIG_GND` joining `PWR_GND` on the carrier is so obvious it
needs no statement — but the same corpus thought the module-side version of
that question worth a `DISPUTED` register entry, and on the carrier it would put
the 2 MHz SPI return in parallel with the 359 mA power return
`[repo config/figures.yaml:612-618, umbilical-current]`.

**Smallest fix.** One line in `carrier/netlist.yaml`'s `ports:` and one net
entry deciding what pin 8 lands on at the carrier, plus `carrier/carrier` in
`nets.yaml`'s `DIG_GND` `reference:` list. If it cannot be decided, say so where
the other undecidable endpoints are said — `spi-link/netlist.yaml` has no
"OPEN, AND NOT GUESSED AT" note, and `power-entry/netlist.yaml` shows the form.

---

## N2-3 — `carrier/carrier` is the one netlisted circuit with no `## Interfaces` table and no `circuit.yaml`, and it is the circuit N2-2 needs

**Severity: high (structural; it is why N2-2 is invisible).**

**Claim.** `carrier/carrier` declares a reference port and eighteen others, is
named on 19 master nets, and has neither of the two files that would let a
reader or a tool check those declarations against prose.

**Evidence** `[test]`:

```
$ for f in $(find hardware -name '*.md' | grep -v notes.md | sort); do \
    echo "$(grep -c '^## Interfaces' $f)  $f"; done
0  hardware/carrier/carrier.md          ← every other circuit page: 1
$ for n in $(find hardware -name netlist.yaml); do d=$(dirname $n); \
    [ -f "$d/circuit.yaml" ] || echo "MISSING circuit.yaml: $d"; done
MISSING circuit.yaml: hardware/carrier
$ find hardware -name circuit.yaml | wc -l
23
```

`hardware/README.md:52-56` says "Every circuit page carries one: every net that
crosses that circuit's boundary, one row each. A PCB netlist is transcribed from
these"; `hardware/README.md:103-104` says "Every circuit directory carries a
`circuit.yaml`". `carrier/carrier` has neither, so its `PWR_GND: {dir: ref}`
port is named by no page row and creates no dependency edge, and the count "23
circuits" (the staleness hook's own summary) excludes the circuit id that
`nets.yaml` names as driver on 11 nets and as a `PWR_GND` reference.

**What would have to be true for this to be wrong.** That `carrier/carrier` is
a *board* page and not a circuit — which is what its netlist header argues
(`[repo hardware/carrier/netlist.yaml:4-7]` "carrier.md is the board page
rather than a circuit page"). But `cluster/cluster-boards.md` and
`module/module.md` are board pages too and neither carries a netlist; this one
does, and it is the only board page that declares ports. A file that declares a
boundary has a boundary to tabulate.

**Smallest fix.** Add the `## Interfaces` table (19 rows, one per port) and a
`circuit.yaml`. The `PWR_GND` and `DIG_GND` rows are where N2-2 gets decided.

---

## N2-4 — on the module, all three reference nets originate at `module/power-entry` and none of them reaches `J-PWR-EURO.GND`

**Severity: high.**

**Claim.** `AGND_MOD`, `DIG_GND` and `PWR_GND` all name `module/power-entry` as
origin; in that circuit's netlist they are three disjoint nets, and only
`PWR_GND` contains the rack ground pin. Nothing in any netlist joins the other
two to it, and `power-entry/netlist.yaml` — which documents one *other*
unassertable endpoint at length — says nothing about this one.

**Evidence** `[repo hardware/module/power-entry/netlist.yaml:182-197]`:

```
AGND_MOD: port, C1.2, C3.2, R-REG-SET-LO.2, C-REG-ADJ.2, C-REG-OUT.2
DIG_GND:  port, C4.2
PWR_GND:  port, J-PWR-EURO.GND, C2.2
```

- The page says these meet: "One origin, at the IDC's ground pin … The analog
  return is its own region joining at the star"
  `[repo hardware/module/power-entry/power-entry.md:174-176]`;
  `dac8568.md`'s `## Interfaces` says of `AGND_MOD` "The analog star, **single
  tie**"; ADR 0004:626-629 "The origin is the Eurorack power inlet's ground pin.
  Every milliamp in the module leaves through it".
- So `AGND_MOD`'s tie to the star is **settled** by the corpus, and unlike
  `DIG_GND`'s it is not the `DISPUTED` figure — `dig-gnd-topology`'s `quantity`
  is "Where `DIG_GND` returns to" `[repo config/figures.yaml:541-552]` and all
  three of its candidates are about `DIG_GND`. Nothing makes `AGND_MOD`'s
  single tie unassertable.
- `[calc]` what has no path home as a result: `C1` 100 µF on
  `MODULE_ANALOG_POS12` and `C3` 47 µF on `MODULE_ANALOG_NEG12` are the module's
  entry bulk; their charge and ripple current enters at `J-PWR-EURO.POS12` /
  `.NEG12` and, per the netlist, returns onto `AGND_MOD`, which touches
  `J-PWR-EURO.GND` nowhere. The decoupling loop for both analog rails is open
  in the authoritative model. Likewise the `LM317` divider's
  1.25 V / 150 Ω = 8.3 mA through `R-REG-SET-LO`.
- `C4` (bus +5 V bulk) returns to `DIG_GND`, and the 74AHCT125's supply current
  leaves `U-LVL-MOD.GND` onto `DIG_GND`
  `[repo hardware/module/digital-and-supervision/netlist.yaml:125-136]` — so
  the rack's +5 V return also has no asserted path back to the rack.
- The contrast is the point: `carrier/power-entry-instrument` has exactly this
  situation and documents it —
  `[repo hardware/carrier/power-entry-instrument/netlist.yaml:139-146]` "THE
  SINGLE TIE, and it is copper rather than a part … Declared because this
  circuit is the net's origin and the master has to have a side to check
  against." `module/power-entry/netlist.yaml` has a 28-line note at its foot,
  and every word of it is about the `D2` branch.
- No page states where `C1`, `C3` or `C4` return. The drawing shows only `C2`'s
  bottom on "PWR_GND (star)"
  `[repo hardware/module/power-entry/power-entry.md:53]`. So splitting the four
  entry bulk capacitors' returns across three different reference nets is a
  netlist-only decision on which no page can be checked.

**What would have to be true for this to be wrong.** That `external_endpoints`
and `nets.yaml`'s "a net here asserts a connection; do not add one
speculatively" are meant to cover a *known* copper tie as well as an *unknown*
endpoint. If so, the two files should say it in the same words, and the fact
that one of them does and the other does not is itself the finding.

**Smallest fix.** The same comment `power-entry-instrument/netlist.yaml` already
carries, in `power-entry/netlist.yaml`, naming all three nets and which one
holds `J-PWR-EURO.GND`. Separately, decide `C1`/`C3`/`C4`'s returns on the page
rather than only in the netlist.

---

## N2-5 — `GND_CHAIN` and `PWR_GND` are one node under two names, and no netlist joins them: the whole key chain has no return

**Severity: high.**

**Claim.** `nets.yaml` states in its own note that `GND_CHAIN` is not a separate
node from `PWR_GND`, then declares it a separate net whose origin is
`interfaces/key-chain-loom`. That circuit declares no `PWR_GND` port, and the
reference return its page names — `HDR-DEV`'s ground pins — appears in no net.

**Evidence.**

- `[repo hardware/nets.yaml:44-51]` `GND_CHAIN`, `kind: reference`,
  `origin: interfaces/key-chain-loom`, note: "It is the carrier's `PWR_GND`
  pour arriving on `HDR-DEV`'s ground pins — **a separate name for the five
  conductors in the ribbon, not a separate node**".
- `[repo hardware/interfaces/key-chain-loom/key-chain-loom.md:301-306]` "The
  chain's return here is the five alternating grounds, `GND_CHAIN`, which is
  the carrier's `PWR_GND` pour arriving on `HDR-DEV`'s ground pins."
- `[repo hardware/interfaces/key-chain-loom/key-chain-loom.md:68-76]` the
  drawing's five ground rows all start at `HDR-DEV`:
  `GND ────────► 1 GND`, and the `## Interfaces` row's Peer is "`HDR-DEV` →
  `cluster/key-register`".
- `[repo hardware/interfaces/key-chain-loom/netlist.yaml:30,116-123]`
  `GND_CHAIN: {dir: ref, from: interfaces/key-chain-loom}` — its own origin —
  and the net is `port` + `J-CHAIN.1/3/5/7/9` + `U-TVS-CHAIN.GND`. No
  `HDR-DEV`, no `PWR_GND` port. The asymmetry is exact: the **3V3** side of the
  same socket *is* modelled, as `DEV_3V3: {dir: in, from: carrier/carrier}`
  (line 24), from `U-MCU-RT.P3V3`
  `[repo hardware/carrier/netlist.yaml:197-199]`. The ground side of the same
  socket is renamed and given a local origin.
- `[calc]` what floats as a result: four `74HC165` supply returns and four
  `C-DECOUPLE-165` `[repo hardware/cluster/key-register/netlist.yaml:66-70]`,
  21 `C-KEY` and 21 switch legs
  `[repo hardware/cluster/key-switch-network/netlist.yaml:63-66]`, and the
  pull-up current the carrier page costs at "18 keys closed = 25.8 mA step on
  the ADC's reference" `[repo hardware/carrier/carrier.md:180-186]` — 25.8 mA
  on a net with no asserted path home.
- The one place a `DIG_GND`/`GND_CHAIN` label conflict *was* caught is handled
  well and is not a finding: the drawing labels `U-TVS-CHAIN`'s return
  `DIG_GND`, the netlist nets it to `GND_CHAIN`, and both the netlist note
  (line 64) and the page (lines 301-306) say so explicitly.

**What would have to be true for this to be wrong.** That a net named in
`nets.yaml` as "not a separate node" from another net is understood by every
reader and every downstream tool to be an alias, needing no tie. If that is the
intent, the master should carry an `alias_of:` key — as written, the two
entries are indistinguishable from two nets that must not be joined, which is
what the `AGND_INST`/`AGND_SENSE`/`AGND_MOD` entries beside them are.

**Smallest fix.** Either add `PWR_GND: {dir: ref, from: module/power-entry}` to
`key-chain-loom`'s ports and put `J-CHAIN.1/3/5/7/9` and `U-TVS-CHAIN.GND` on
it, dropping `GND_CHAIN`; or keep `GND_CHAIN` and give it the `HDR-DEV` /
`PWR_GND` endpoint the page names.

---

## N2-6 — `AGND_INST` "carries no power current" is ADR 0004's rule about `AGND_SENSE`, restated against the wrong net

**Severity: medium.**

**Claim.** `nets.yaml` attaches the corpus's strongest grounding rule to
`AGND_INST`, where it is false by ~13 mA. The rule belongs to `AGND_SENSE`, the
umbilical conductor, where it is true and where ADR 0004 and
`breath-sense-link.md` both put it.

**Evidence.**

- `[repo hardware/nets.yaml:273]` `AGND_INST`: "Instrument analog star.
  **Carries no power current — that is the whole point of it**".
- `[repo docs/decisions/0004-cv-interface-module.md:638]` the table of returns:
  "`AGND`, **from the etherCON** | **Nothing.** It is an in-amp input, not a
  ground (ADR 0003)"; and :657-659 "**`AGND` is not in this list.** It
  terminates at the in-amp's IN+ and at the two 1 MΩ bias resistors, and that is
  all it does." ADR 0004's `AGND` is the conductor on the pair — i.e.
  `AGND_SENSE` — not the local pour.
- `[repo hardware/interfaces/breath-sense-link/breath-sense-link.md:101-124]`
  settles the actual question, and gives the number:
  "REF5050 ~1 mA + OPA2197 2 × ~1 mA + MPXV4006DP 10 mA = ~13 mA `[repo] 0003`"
  — the cost of returning the analog supply current *down the umbilical's AGND
  conductor*, which the page rejects ("**`PWR_GND` anyway**"). The local pour is
  a different thing: "The local analog pour joins `PWR_GND` at **one** tie".
- What the netlists put on `AGND_INST` is that whole 13 mA, up to the single
  tie: `U-BREATH.GND`
  `[repo hardware/interfaces/breath-sense-link/netlist.yaml:79-84]`;
  `U-REF-BREATH.GND`, plus `C-REF-OUT-VIN.2` and `C-DEC-REF-VIN.2` — two bypass
  capacitors whose other ends are on `UMBILICAL_POS12`, the 359 mA rail
  `[repo hardware/carrier/breath-excitation-reference/netlist.yaml:134-141,
  93-97]`; `U-ADC.VSS`, `C-ADC-BULK.2`, `C-DEC-ADC.2`
  `[repo hardware/carrier/breath-adc/netlist.yaml:85-91]`.
- The netlists are right and the sentence is wrong. `AGND_SENSE` as netlisted
  carries only the in-amp bias current — `R1b` → `R2` → `R4` 1 MΩ
  `[repo hardware/module/breath-receive-stage/netlist.yaml:121-131,176-179]` —
  which is the rule ADR 0004 states.

**What would have to be true for this to be wrong.** That "power current" is
meant to exclude IC supply return, in which case ~13 mA of DC through the pour
is not "power current". But the sentence's own justification — "that is the
whole point of it" — is ADR 0004:657's justification for the *conductor*, and
the corpus's most-cited grounding fact should not be one net off.

**Smallest fix.** Move the clause: `AGND_SENSE`'s entry already says "A SIGNAL,
NOT A GROUND"; add "carries no power current" there, and give `AGND_INST` the
true statement — the local analog pour, carrying ~13 mA of front-end supply
return to the single tie, per `breath-sense-link.md`'s decision.

---

## N2-7 — `J-LED-L.BI` / `J-LED-R.BI` are tied to the carrier pour; the page, the BOM row and the datasheet reading all put that tie at the strip head

**Severity: medium.**

**Claim.** The netlist makes `BI` a fourth net on the carrier side of each LED
connector. Three places in the corpus say the `BI`-to-`GND` tie is at the first
pixel, 420 mm away, and that the loom therefore carries six conductors, not
eight.

**Evidence.**

- `[repo hardware/carrier/led-strip-drive/netlist.yaml:115-130]` `PWR_GND`
  includes `J-LED-L.BI` and `J-LED-R.BI`.
- `[repo hardware/carrier/led-strip-drive/led-strip-drive.md:26]`
  `## Interfaces`: "`J-LED-L` `BI`, `J-LED-R` `BI` | ref | **the head of each
  strip** | — | A **ground** connection, not a driven one".
- Same page, component table (line 122): "`BI` is a **ground** connection **at
  the head of the strip** … so it is still a 4-way connector but **only three
  nets**, and `BI` can tie to the same GND pin's net **at the strip end**".
- Same page, lines 88-96: the datasheet's recommended circuit "ties **L1's pin 6
  (`BI`) to pin 5 (`GND`)**" — inside the tape — "and the LED loom stays at 6
  conductors rather than 8".
- `[repo hardware/carrier/led-strip-drive/bom.csv:4]` (`R-LED-SER`, and the
  same text in the generated `hardware/bom.csv:25`): "So `BI` is a ground
  connection, not a driven one: two gates, two resistors, and the LED loom
  stays at 6 conductors rather than 8."
- The netlist's own comment quotes the rule correctly — "The datasheet's
  recommended circuit ties the first pixel's `BI` to its `GND` … which is what
  keeps the LED loom at 6 conductors" (lines 110-114) — and then wires `BI` to
  the wrong end of the loom in the net twelve lines below it.

**What would have to be true for this to be wrong.** That `J-LED-L` is a 4-way
connector whose `BI` pin is *not* carried by the loom and is strapped to the
pour on the board as a spare-pin convention. That is a coherent reading of a
4-way connector with three nets — but it is not what the page's `ref` Peer
column says ("the head of each strip"), and it moves an ESD/backup-data
reference 420 mm from where the vendor's circuit puts it.

**Smallest fix.** Remove the two `BI` pins from `PWR_GND` and declare
`LED_BI_L` / `LED_BI_R` in `external_endpoints` with the page's reason — the
same mechanism the file already uses for `SPARE_GATE_B_OUT`.

---

## N2-8 — `led-strip-drive` nets the strip power pins that its own page and its own component note say belong to another circuit

**Severity: medium.**

**Claim.** The page marks the strip's `+12V`/`GND` row `Dir —` — which
`hardware/README.md` defines as "no connection here — the row is context" — and
the netlist connects all four of those pins, putting the 359 mA strip return on
this circuit's `PWR_GND` net.

**Evidence.**

- `[repo hardware/carrier/led-strip-drive/led-strip-drive.md:27]` "`+12V`, GND
  at `J-LED-L/-R` | **—** | `carrier/power-entry-instrument` | Strip power
  passes through this connector but **is that circuit's net**".
- `[repo hardware/README.md:84]` "`—` (no connection here — the row is
  context)".
- `[repo hardware/carrier/led-strip-drive/netlist.yaml:60]` the component note
  repeats it: "Strip power passes through this connector and is
  `carrier/power-entry-instrument`'s net, **not this circuit's**" — and lines
  99-102 and 127-128 then net `J-LED-L.POS12`, `J-LED-R.POS12` on
  `UMBILICAL_POS12` and `J-LED-L.GND`, `J-LED-R.GND` on `PWR_GND`.
- The other circuit reaches the same two feed points from its side:
  `C-STRIP-BULK-L`/`-R` "At the J-LED-L feed point"
  `[repo hardware/carrier/power-entry-instrument/netlist.yaml:42-52]`.

Electrically harmless — one net either way — but it is a boundary the corpus
draws twice and the netlist crosses, and `hardware/README.md:56` says "two pages
disagreeing about a net is a short", which is the standard this is measured
against.

**What would have to be true for this to be wrong.** That a connector's pins
belong to the circuit that owns the connector regardless of whose net they
carry — which is defensible and is probably the right rule. Then the page's
`Dir —` and the component note are both wrong and should be corrected, because
as written a transcriber reading the page would leave two pins unconnected.

**Smallest fix.** Change the page row's `Dir` to `ref`/`in` and delete
"not this circuit's" from the component note, or move the four pins. Either
way, not three files disagreeing.

---

## N2-9 — `umbilical-load-switch.md` says the FET source returns to `PWR_GND` and, two rows up, that it is the exported rail; the netlist chose silently

**Severity: medium.**

**Claim.** The page's `PWR_GND` row lists "the FET source" as returning to
`PWR_GND`, while its `UMBILICAL +12V` row calls the same pin the exported rail.
`Q-LOADSW` is a high-side switch, so only the second can be true. The netlist is
right and records nothing.

**Evidence.**

- `[repo hardware/module/umbilical-load-switch/umbilical-load-switch.md:25]`
  "`UMBILICAL +12V` | out | … | **The FET's source**, down the Cat5 umbilical."
- Same table, line 26: "`PWR_GND` | ref | `module/power-entry` | — |
  `C-TIMER`, `C-GATE`, `R-FB-LO` **and the FET source** return here, to the
  star at the IDC".
- `[repo hardware/module/umbilical-load-switch/netlist.yaml:119-122,133-139]`
  `UMBILICAL_POS12` = `Q-LOADSW.S`, `R-FB-HI.1`, port; `PWR_GND` = port,
  `U-LOADSW.GND`, `C-GATE-LOADSW.2`, `C-TIMER-LOADSW.2`, `R-FB-LO.2`,
  `C-DECOUPLE-LOADSW.2`.
- The page's own §"Four things the old section had wrong", item 2, makes the
  high-side reading explicit: "In a high-side N-FET the drain is *always* at
  12 V" (:47, in item 2 of "Four things the old section had wrong"). So the `PWR_GND` row contradicts a correction three
  paragraphs below it.
- The same row also omits two real returns the netlist carries:
  `U-LOADSW.GND` and `C-DECOUPLE-LOADSW.2` (the datasheet's supply-transient
  capacitor, netlist line 79).

**What would have to be true for this to be wrong.** That "the FET source" in
the `PWR_GND` row means the source of the *gate-drive* return path rather than
the FET's source terminal. No reading of a five-pin list makes that likely, and
the netlist did not read it that way either.

**Smallest fix.** Strike "and the FET source" from the `PWR_GND` row and add
`U-LOADSW`'s `GND` and `C-DECOUPLE-LOADSW`.

---

## N2-10 — the two single-supply `OPA2197` halves return `V-` to the analog star in prose and to nothing in the netlist, and the schema cannot express it

**Severity: medium.**

**Claim.** `U-REFBUF` and `U-BREATHBUF` run single-supply from +12 V with `V-`
on `AGND_INST`. Neither appears on `AGND_INST`, neither declares a `V-` pin, and
`rails:` cannot carry a reference net because the checker turns every `rails:`
entry into a `dir: in` port. Separately, `U-REF-BUF` on
`module/breath-receive-stage` declares no supply at all.

**Evidence** `[test]`, one line per op-amp half in the corpus:

```
carrier/breath-excitation-reference  U-REFBUF        rails=['UMBILICAL_POS12']            supplypins=[]
carrier/breath-excitation-reference  U-BREATHBUF     rails=['UMBILICAL_POS12']            supplypins=[]
module/breath-receive-stage          U-DIFFRX        rails=None            supplypins=['V+','V-']
module/breath-receive-stage          U-REF-BUF       rails=None            supplypins=[]
module/breath-output-stage           U-BREATH-BUF    rails=[POS12, NEG12]  supplypins=[]
… 8 more, all rails=[POS12, NEG12]
```

- `[repo hardware/carrier/breath-excitation-reference/netlist.yaml:62]`
  `U-REFBUF`'s own note: "Single supply from +12 V, **V- on the analog star**.
  Buffers the 5.000 V into the sensor." The `AGND_INST` net six lines below
  (134-141) does not contain it, and neither does `rails:`.
- `[repo tools/check-netlist.py:435-443]` "A component declares `rails:`
  instead, and that counts as this circuit receiving those nets" —
  `ports.setdefault(rail, {"dir": "in", …})`. A `ref` net declared through
  `rails:` would be reported as a role mismatch by the master check
  (`:160-162`), so the only way to state an op-amp's reference rail is an
  explicit pin on the reference net — which is what `U-DIFFRX` does and no
  `OPA2197` half does.
- `U-REF-BUF` is the outlier even among those: 12 of 13 `OPA2197` halves declare
  `rails:`; it is the one that declares nothing, and it is the half that drives
  the in-amp's `REF` pin, where source impedance matters to 5 Ω
  `[repo hardware/module/breath-receive-stage/bom.csv:4]`.
- `[repo hardware/carrier/carrier.md:128]` the drawing states `(V+ = +12V)` for
  the buffer and never states `V-`; grepping the owning page for `V-`,
  `negative` or `single supply` returns nothing
  `[test] grep -n "V−\|V-\|negative\|[Ss]ingle supply"
  hardware/carrier/breath-excitation-reference/breath-excitation-reference.md`
  → no output.

**What would have to be true for this to be wrong.** That implicit rails are
understood to include the reference rail, so declaring `UMBILICAL_POS12` implies
"and the other one, whatever the notes say". That cannot be true of a
single-supply stage, where which node `V-` sits on is the design choice — and
the note exists precisely because it is.

**Smallest fix.** Give the two halves explicit `V-` pins on `AGND_INST`, and
give `U-REF-BUF` a `rails:` line. Longer-term, `rails:` needs to take a
reference net without forcing `dir: in`; that is a `tools/` change and `tools/`
is frozen for this wave.

---

## N2-11 — the `DISPUTED` figure that owns every ground question cites three locations and all three are wrong

**Severity: medium.**

**Claim.** `dig-gnd-topology` is the register entry a reader is sent to from
17 citations across 15 pages and from 10 of the 26 reference ports
`[test] grep -rho "dig-gnd-topology" $(find hardware -name '*.md' | grep -v
notes.md) | wc -l → 17`. All three of its
`candidates:` line citations point somewhere the statement is not, and one
points past the end of its file.

**Evidence** `[repo config/figures.yaml:541-552]` and `[test]`:

| citation | what is actually there |
|---|---|
| `docs/decisions/0004-cv-interface-module.md:627` | ":627 is "The origin is the Eurorack power inlet's ground pin." The "own path to the star" statement is at **:654** `[test] grep -n "own path to the star" → 654`. The entry's `note:` compounds it: "line 627 still says the opposite" — it does not say anything on the subject. |
| `hardware/module/power-entry/power-entry.md:495-498` | the file is **196 lines** `[test] wc -l → 196`. The statement is at :174-179 `[test] grep -n "own path to the star\|One origin, at the IDC" → 174, 177`. |
| `hardware/module/digital-and-supervision/digital-and-supervision.md:53` | :53 is a drawing gutter line (`│  … │  SCLK+MOSI share pair (4,5)`). "analog star, single tie (ADR 0004)" is at **:70** `[test] grep -n "analog star, single tie" → 70`. |

**What would have to be true for this to be wrong.** That the line numbers were
correct at `d1f0cb7`'s ancestor and are understood as historical. But
`config/figures.yaml` is corpus, not `docs/log/` — `CLAUDE.md` §6 lists exactly
which trees are history and `config/**` is on the other list — so its pointers
are live and must resolve. The 2026-09-21 restructure moved all three files
`[repo git log --oneline: 3f31981 "Restructure: one circuit per directory"]`.

**Smallest fix.** Three line numbers, or replace them with the section names
(`ADR 0004 "Ground plan"`, `power-entry.md "## Grounding"`,
`digital-and-supervision.md`'s drawing) so the next move does not break them.

---

## N2-12 — `digital-and-supervision.md`'s drawing picks a side of the disputed figure in prose, where nothing checks it

**Severity: medium-low.**

**Claim.** The drawing asserts one of the three candidates as fact. The netlist
correctly declines to, but nothing in the repository can see the disagreement,
because `check-netlist.py` only reads `[REFDES value]` labels.

**Evidence.**

- `[repo hardware/module/digital-and-supervision/digital-and-supervision.md:70]`
  the `DIG_GND` column of the drawing terminates in
  `└── analog star, single tie (ADR 0004)`.
- `[repo hardware/module/digital-and-supervision/netlist.yaml:125-136]`
  `DIG_GND` contains no `AGND_MOD` endpoint, and `power-entry`'s `DIG_GND` is
  `port` + `C4.2`.
- The page's own `## Interfaces` row says the opposite of its drawing: "Where it
  ties is the disputed figure, **not a fact this page settles**" (:29).
- `[repo tools/check-netlist.py:26-30]` the `drawing` check is "every
  `[REFDES value]` label". A bare-prose assertion inside a drawing is outside
  it, and `hardware/README.md:26-28` says "An ASCII drawing is a picture. No
  tool in this repository can read one".

**What would have to be true for this to be wrong.** That "(ADR 0004)" in the
label makes it a citation of a candidate rather than an assertion. But ADR
0004:654 asks for `DIG_GND`'s **own path** to the star, which is candidate 1,
while the label says **single tie** to the analog star, which is candidate 3 —
the label cites the ADR for the opposite of what the ADR says.

**Smallest fix.** `└── DIG_GND return: dig-gnd-topology (DISPUTED)` in the
drawing.

---

## N2-13 — `nets.yaml` settles which ground the panel LED lands on, in the entry that says it does not settle topology

**Severity: medium-low.**

**Claim.** `panel-led.md` says which ground the indicator returns to *is* the
disputed figure. The netlist picks `AGND_MOD` and flags it, which is honest;
`nets.yaml` picks it and does not, which is not.

**Evidence.**

- `[repo hardware/module/panel-led/panel-led.md]` `## Interfaces`: "LED return |
  ref | `module/power-entry` | `dig-gnd-topology` | **Not drawn anywhere in the
  corpus.** The rail it comes from is the analog one; **which ground it lands on
  is the disputed figure**".
- `[repo hardware/module/panel-led/netlist.yaml:34-40]` flags its own choice:
  "WHICH GROUND IT LANDS ON IS THE DISPUTED FIGURE … `AGND_MOD` is the reading
  that matches the rail; if the figure settles the other way this line moves
  with it." Good practice and the only netlist in the corpus that does it.
- `[repo hardware/nets.yaml:431-447]` `AGND_MOD`'s `reference:` list contains
  `module/panel-led`, with the disclaimer "This file records which circuits
  reference the net; it does **NOT** settle the topology and must not be read as
  settling it." The disclaimer covers where `AGND_MOD` meets `DIG_GND`. It does
  not cover *which of two reference nets a given pin sits on*, which is what
  listing `module/panel-led` decides.
- `[calc]` the current it puts there: `R-LED-PANEL` 2.2 kΩ from +12 V analog
  through a 3 mm LED, `(12 − 2.0) / 2200 = 4.5 mA` DC, continuous whenever the
  rack is on `[repo hardware/module/panel-led/panel-led.md]` — into the net ADR
  0004:655 wants joining the star "and nowhere else".

**What would have to be true for this to be wrong.** That a `reference:` list
is read as "may reference" rather than "does". Every other entry in the file is
read the second way; the forward check in `check-netlist.py:143-163` requires
the named circuit to declare a matching `ref` port, which is an assertion.

**Smallest fix.** One clause on `AGND_MOD`'s `note:` naming `module/panel-led`
as the entry the figure may move, or a `proposed:` for it — the mechanism the
same file already uses for `module/breath-response-shaper`.

---

## N2-14 — every page that enumerates what returns to `AGND_MOD` is missing items the netlist puts there

**Severity: low-medium.**

**Claim.** Four pages list what returns to the module star. In all four the
netlist carries more, and the additions are DC divider legs, not shunts.

**Evidence** (page row, then netlist net):

| circuit | page names | netlist adds |
|---|---|---|
| `module/pitch-stage` | `C-AA-PITCH`, `C-FILT-PITCH` | `R-BIAS-DAC.2` (100 kΩ), `J-CV-PITCH.SLEEVE` |
| `module/mod-channels` | `C-FILT-MOD` | `R-BIAS-DAC-CH7.2` + `R-BIAS-DAC-1..4.2` (5 × 100 kΩ), 4 × `SLEEVE` |
| `module/breath-receive-stage` | `R4`, `R5`, both `C_cm`, "the output RC" | `TRIM-BREATH-ZERO.CCW` |
| `module/breath-output-stage` | `R-GAIN-FLOOR`, summer `(+)`, `C-OUT-BREATH` | `POT-OFFSET.CCW`, `J-CV-BREATH.SLEEVE` |

`[repo hardware/module/pitch-stage/pitch-stage.md]`,
`[repo hardware/module/mod-channels/mod-channels.md]`,
`[repo hardware/module/breath-receive-stage/breath-receive-stage.md]`,
`[repo hardware/module/breath-output-stage/breath-output-stage.md]` against
`netlist.yaml:166-171`, `:418-432`, `:176-182`, `:148-154` respectively.
`[calc]` the trimmer legs are not negligible on a star: `TRIM-BREATH-ZERO`
across `DAC_AVDD` gives `5.21 V / 10 kΩ = 521 µA`, `POT-OFFSET` gives
`5.21 V / 10 kΩ = 521 µA`. `R-BIAS-DAC` at 100 kΩ is ~50 µA each at mid-scale.
The sleeves are N2-1.

**What would have to be true for this to be wrong.** That the `## Interfaces`
`Note` column is illustrative, not exhaustive. `hardware/README.md:52-56` says
"every net that crosses that circuit's boundary, one row each", which governs
the Node column; it does not say the Note must enumerate every pin. So this is
the weakest of the findings, and I file it because the pages *do* enumerate —
four out of four — and a reader checking a netlist against a page will read a
short list as a complete one, which is how N2-1 stayed invisible.

**Smallest fix.** "and the DAC bias returns" / "and the trimmer's lower end" in
each Note, or drop the enumerations.

---

## N2-15 — the figure cited on a reference port is inconsistent across the circuits that share the net, and one of them is the wrong figure

**Severity: low.**

**Claim.** Seven circuits declare a `PWR_GND` ref port and cite three different
things; eight declare `AGND_MOD` and cite two.

**Evidence** `[test]`, tabulating `figure:` on every `dir: ref` port:

```
26 ref ports in all: PWR_GND 7, AGND_MOD 8, GND_CHAIN 4, AGND_INST 4, DIG_GND 3

PWR_GND    dig-gnd-topology ×3 (carrier/carrier, led-strip-drive, display-and-service-uart)
           umbilical-pinmap ×2 (power-entry-instrument, spi-link)
           none             ×2 (module/power-entry, umbilical-load-switch)
AGND_MOD   dig-gnd-topology ×5   none ×3 (power-entry, breath-receive, breath-output)
AGND_INST  none ×3   dig-gnd-topology ×1 (power-entry-instrument)
DIG_GND    umbilical-pinmap ×1 (spi-link)   dig-gnd-topology ×1 (digital-and-supervision)
           none ×1 (power-entry)
GND_CHAIN  chain-conductors ×3   none ×1 (key-switch-network)
```

`nets.yaml`'s own `figure:` keys are: `GND_CHAIN` → `chain-conductors`,
`AGND_INST` → `dig-gnd-topology`, `DIG_GND` → `dig-gnd-topology`, `AGND_MOD` →
`dig-gnd-topology`, `PWR_GND` → **none**. So the three circuits citing
`dig-gnd-topology` on `PWR_GND` cite a figure whose `quantity:` is "Where
`DIG_GND` returns to" `[repo config/figures.yaml:542]` on a net the figure's
candidates never mention, and the master net they cite it from carries no figure
at all. `check-netlist.py` never compares a port's `figure:` with the master's
`[test] grep -n "figure" tools/check-netlist.py` → no comparison.

**What would have to be true for this to be wrong.** That `figure:` on a port
means "a figure relevant to this port" rather than "this net's figure". Then it
is not checkable and not worth carrying; `nets.yaml:26` says "VALUES LIVE IN
`config/figures.yaml`. `figure:` cites; it does not restate", which reads as the
net's figure.

**Smallest fix.** Make each ref port cite its master net's `figure:`, and give
`PWR_GND` one (`umbilical-current` is the figure its own page's row cites
`[repo hardware/module/power-entry/power-entry.md:32]`).

---

## N2-16 — `cluster/key-marker-and-bits` declares a `GND_CHAIN` port that no net of that name exists for, and nothing on the board returns to

**Severity: low.**

**Claim.** The file has no `GND_CHAIN:` net. Its `GND_CHAIN` ref port is
consumed by a net named `MARKER_LOW` whose only member is that port — a second
name for the same node inside one file — and no component in the circuit returns
to it.

**Evidence** `[repo hardware/cluster/key-marker-and-bits/netlist.yaml:21,54-59,
68-73]`:

```
ports:  GND_CHAIN: {dir: ref, from: interfaces/key-chain-loom, figure: chain-conductors}
…
MARKER_LOW:
  - port: GND_CHAIN
…
external_endpoints: [MARKER_HIGH, MARKER_LOW, FREE_BIT_1..3]
```

The three components are pull-ups whose pin 1 is on `V3V3_CHAIN` and pin 2 on
`FREE_BIT_n`. `MARKER_HIGH` is the same shape against `V3V3_CHAIN`, so the
`V3V3_CHAIN` port appears in two nets. `[repo hardware/nets.yaml:97-106]`
declares `MARKER_BITS` a `kind: signal` net driven by this circuit, and
`per_board: true` exempts it from the port check
`[repo tools/check-netlist.py:101-114]` — so the four low straps are, in the
authoritative model, part of the reference net rather than of the signal net
that is supposed to carry them, and nothing says so.

**What would have to be true for this to be wrong.** Nothing much — a strap to
ground *is* the ground net, and the per-board exemption is well argued. This is
a naming artifact rather than a wiring claim. I file it because a `ref` port
that appears under a different net name is the exact shape a reader
cross-checking the page's `3V3`, `GND` row will not find.

**Smallest fix.** Rename the net `GND_CHAIN` and put the comment about the four
low straps on it.

---

## N2-17 — `module/power-entry`'s `## Interfaces` row for `PWR_GND` names two of the six circuits that reference it, and three of them have no dependency edge

**Severity: low.**

**Evidence.** `[repo hardware/module/power-entry/power-entry.md:32]` "`PWR_GND`
| ref | `module/umbilical-load-switch`, `carrier/power-entry-instrument`".
`[repo hardware/nets.yaml:357-368]` `PWR_GND`'s `reference:` adds
`interfaces/spi-link`, `carrier/display-and-service-uart`,
`carrier/led-strip-drive`, `carrier/carrier`, and all four declare
`PWR_GND: {dir: ref, from: module/power-entry}`.
`[test] grep -n "circuit:" hardware/module/power-entry/circuit.yaml` →
`carrier/power-entry-instrument`, `interfaces/spi-link`, and nine module
circuits; no `carrier/carrier`, `carrier/led-strip-drive` or
`carrier/display-and-service-uart`. `hardware/README.md:112-114` requires "ONE
`circuit:` edge per distinct `board/circuit` id in the **Peer** column … AND
every such edge is declared from **both** ends", so the missing page rows are
what the missing edges are downstream of. (`carrier/display-and-service-uart`
also names `carrier/power-entry-instrument` as its `PWR_GND` peer on the page
while its netlist names `module/power-entry`.)

**What would have to be true for this to be wrong.** That a reference net's Peer
column lists only the circuits it *crosses a board boundary to*, not everything
that returns to it. That reading is consistent with the two names present and
would make the row correct — but then `nets.yaml` should not be read as seeded
from these tables, and `led-strip-drive`'s and `carrier/carrier`'s own netlists
should not name `module/power-entry` as their peer.

**Smallest fix.** Four names in the page row; the edges follow.

---

## What I checked and found clean

- **The three `AGND` nets are never merged.** `AGND_SENSE`, `AGND_INST` and
  `AGND_MOD` appear in seven netlists between them and no net contains pins from
  two of them. Every declaration of `AGND_SENSE` is `dir: in` or `dir: out`,
  never `ref` — `breath-sense-link` (`out`), `spi-link` (`in`),
  `breath-receive-stage` (`in`) — which is what "A SIGNAL, NOT A GROUND"
  requires. `R1b` sits between `AGND_INST` and `AGND_SENSE` exactly as
  `breath-sense-link.md` demands
  `[repo hardware/interfaces/breath-sense-link/netlist.yaml:74-84]`, and the
  only DC path from the instrument star to the module star is
  `R1b` 1 kΩ + `R2` 10 kΩ + `R4` 1 MΩ `[calc]` — a bias path, which is the
  design. This is the corpus's most-warned-about merge and it did not happen.
- **`MECH-GNDBOND` lands on `PWR_GND` and nowhere else**
  `[repo hardware/carrier/power-entry-instrument/netlist.yaml:126-135,148-149]`,
  with the plate end in `external_endpoints`. `CLAUDE.md` and
  `nets.yaml:369-371` both require "NEVER to AGND"; no netlist puts it near one.
- **No netlist makes a reference tie the corpus does not place.** I looked for
  the opposite of N2-4: a netlist joining two reference nets somewhere the
  corpus does not. There is none — only `power-entry-instrument` and
  `module/power-entry` hold ports on more than one reference net, and neither
  joins them. The defect is omission, not misplacement.
- **`U-TVS-SPI.GND` → `PWR_GND`** matches `spi-link.md`'s `## Interfaces` row
  and the BOM row's reasoning about the shared common pin. (The consequence is
  N2-2, not this net.)
- **The cluster returns match all three pages.** `U-KEYS.GND`, `CLKINH` and
  `C-DECOUPLE-165` on `GND_CHAIN` (page: "`C-DECOUPLE-165` returns here, at the
  package"); `C-KEY.2` and `SW1-n.2` on `GND_CHAIN` (page: "`C-KEY` and the
  closed switch both return here"). Pin for pin. Only N2-5 applies, and it is
  about where `GND_CHAIN` itself goes.
- **`display-and-service-uart`'s four ground pins** — both `J-DISP` grounds and
  both `HDR-SERVICE` grounds — are on `PWR_GND`, matching "Two grounds on
  purpose — one with the supply, one with the UART pairs".
- **The `key-chain-loom` `DIG_GND` label conflict is handled, not hidden.** The
  drawing's label, the netlist's choice and the page's paragraph all three
  name the conflict and the figure it waits on. This is the model the rest of
  the reference ports should follow, and I found it in one file out of 22.
- **`breath-response-shaper`** declares only the two ports its drawn half needs
  and takes `proposed:` on the other two; `check-netlist.py:181-183` exempts
  `proposed:` from the forward check, so this is correct rather than lucky.

## Coverage, and what I did not do

26 `dir: ref` ports across 22 netlists, five reference nets, and every pin on
every net those ports name — checked against the owning page's `## Interfaces`
row, its prose, its drawing where it has one, ADR 0004's ground plan, and the
`dig-gnd-topology` / `umbilical-pinmap` / `umbilical-current` register entries.

Not done: I did not check `AGND_SENSE`'s signal-domain properties (CMRR, the
differential pole) — that is a signal claim, not a reference one. I did not
audit the non-reference nets, the instance counts, or the `[REFDES value]`
labels. I did not verify `4.5 mA`, `521 µA`, `8.3 mA` or `13 mA` against
datasheets; the first three are `[calc]` from BOM values and the fourth is the
corpus's own figure `[repo breath-sense-link.md:116]`. Two findings (N2-14,
N2-16) are weak by construction and are marked so.
