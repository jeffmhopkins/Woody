# N6 — the master's directions, checked from both ends

**Slice:** N6, cold. **Claim type:** for every net in `hardware/nets.yaml`, does
the circuit named as `driver`/`origin` say it sources it, does each `receivers:`
circuit say it receives it, does each `reference:` circuit name it, and does each
named circuit's `netlist.yaml` declare a port with the matching `dir` — then the
other direction, a master net no page names and a page-named net the master lacks.

**Measured against `d1f0cb7`.** Working tree is at `5c39a4e`, whose only diff
against `d1f0cb7` is `docs/review/2026-09-26-netlist-audit/README.md`
(`[test] git diff --stat d1f0cb7 HEAD` → `1 file changed, 80 insertions(+)`), a
file this slice did not read. `tools/` unread-and-unmodified except for
`tools/check-netlist.py`, read only. Nothing outside this file was written.

## What was checked, and the baseline

- **55 master nets** carrying **151 endpoint assertions** (`(net, circuit, role)`
  triples across `driver`, `origin`, `receivers`, `reference`, `proposed`)
  `[calc]` over `hardware/nets.yaml`.
- **145 declared ports** across **22 `netlist.yaml` files** `[calc]`.
- **23 `## Interfaces` tables, 164 data rows** `[calc]` — which is *exactly* the
  "164 rows" the master's own header claims it was seeded from
  `[repo hardware/nets.yaml:12-14]`. That count is **not** stale; I checked it
  because it is the shape this repository fails in, and it holds.
- All 55 nets checked from both ends. **Every one resolved**; nothing was left
  unresolvable. Twenty-four of the fifty-five are named by no `.md` page
  literally (see N6-1's note), and for those I matched the master's canonical
  name to the page's prose spelling by hand.

**The tool is clean and that is the point.** `[test] python3 tools/check-netlist.py`
→ `22 circuit(s), 197 components, 254 nets, 55 master net(s) | 0 problem(s) | 0
drawing page(s) still without a netlist | 0 master endpoint(s) awaiting one`.
Its docstring and `check_master()` prove the master against the **per-circuit
`ports:` blocks only** `[repo tools/check-netlist.py:90-186]`. Nothing in this
repository compares the master to an `## Interfaces` table, and the tables are
what the master says it was seeded from. **Every finding below is in that gap.**

### 33 of the 55 are right on both ends

Clean, both ends agreeing with the master in page Dir, page Peer and netlist
`dir`: `CHAIN_SCK`, `CHAIN_SHLD`, `KEY_BITS`, `MARKER_BITS`, `INST_5V_B`, `VS`,
`DIG_GND`, `BUS_POS12_RAW`, `MODULE_ANALOG_POS12`, `MODULE_ANALOG_NEG12`,
`BUS_5V`, `VREFOUT`, `DAC_CH1`…`DAC_CH5`, `DAC_CH7`, and the carrier-side and
cluster-side halves of the chain and GPIO nets except where named below.

### The deletions and the exemptions, checked

- **The six panel nets were right to delete.** `module/panel`'s table gives
  every one Dir `—` `[repo hardware/module/panel/panel.md:32-36]`, and all six
  `J-CV` instances are placed inside the driving circuits — four in
  `mod-channels/netlist.yaml`, one in `pitch-stage/netlist.yaml`, one
  (`J-CV-BREATH`) in `breath-output-stage/netlist.yaml`
  `[test] grep -rn "of: J-CV" hardware --include=netlist.yaml` → 6 hits. The far
  end really does sit inside one circuit. `SW-POWER` likewise: `panel.md` says
  `—` and `umbilical-load-switch.md:24` says "**Not a crossing**".
- **`per_board:` is used where it is true.** `KEY_BITS` and `MARKER_BITS` only;
  both are eight-wide per-device bundles with a four-way strapping table
  `[repo hardware/nets.yaml:74-99]`, and `key-register/netlist.yaml` is
  `replicated: 4`.
- **`external_driver:` is used where it is true** on `IO6` and `U0RXD` — the
  display board and the service header have no page
  `[repo hardware/carrier/display-and-service-uart/display-and-service-uart.md:28,30]`.
  Its *annotations* are wrong; see N6-20.
- **`undriven:` + `pull:` on `CLR` is true.** `R-CLR-PU` holds it inactive and
  the 74HC123 that drove it is not fitted
  `[repo hardware/module/dac8568/dac8568.md:21]`, `[repo hardware/module/link-supervision/link-supervision.md:27]`.
- **`module/panel` and `module/link-supervision` are named by the master nowhere**
  `[calc]` — and both omissions are right: the panel owns holes, and every row of
  `link-supervision.md` reads "**Not fitted**".
- **`BUS_5V`'s removal of `interfaces/spi-link` is right.** `spi-link.md:47`
  gives it Dir `—`, and no `spi-link` component sits on it.

---

## N6-1 — HIGH — `carrier/carrier`: 20 endpoint assertions, 14 of them driver claims, and no `## Interfaces` table or `circuit.yaml` anywhere

**Net / circuit:** `IO1, IO2, IO5, IO6, IO7, IO33, IO35, IO36, IO37, IO38, IO39,
IO40, U0TXD, U0RXD, DEV_3V3, SCLK, MOSI, CS_MOD, INST_5V_A, PWR_GND` /
`carrier/carrier`.

**Claim.** `carrier/carrier` is the most-connected endpoint in the master — 20 of
the 151 assertions, and `driver` on 14 of them — and it is the one endpoint whose
side of every net exists in no prose artefact at all, so "does the driver's page
say it sources the net" cannot be answered for those 14 from anything but the
netlist.

**Evidence, both ends.**
- Master: `carrier/carrier` appears 20 times, as `driver` on `IO35`, `IO36`,
  `IO39`, `IO38`, `IO7`, `IO33`, `IO1`, `IO2`, `IO5`, `U0TXD`, `DEV_3V3`, `SCLK`,
  `MOSI`, `CS_MOD` (14), as receiver on `IO37`, `IO40`, `IO6`, `U0RXD`,
  `INST_5V_A`, and in `PWR_GND`'s `reference` `[calc]` over `hardware/nets.yaml`.
- `hardware/carrier/carrier.md` has **no `## Interfaces` heading**
  `[test] grep -n "Interfaces" hardware/carrier/carrier.md hardware/module/module.md hardware/cluster/cluster-boards.md` → no output.
- **There is no `hardware/carrier/circuit.yaml`**
  `[test] find hardware -maxdepth 2 -name circuit.yaml` → no output — and **no
  other `circuit.yaml` declares an edge to it**
  `[test] grep -rn "carrier/carrier" --include=circuit.yaml hardware/` → exit 1.
  So the README's "every such edge is declared from **both** ends"
  `[repo hardware/README.md:112-116]` has nothing to be declared from at either end.
- The far ends name it by connector instead: `led-strip-drive.md:23` `HDR-DEV`,
  `display-and-service-uart.md:28-29` `HDR-DEV`, `breath-adc.md:26-28` `HDR-DEV`,
  `key-chain-loom.md:30-35` `HDR-DEV IO38` etc. — which `hardware/README.md:85,116`
  *licenses*, because a dev-board header "is named in the Peer column by its
  reference designator" and "creates no edge". **The master then promotes that
  same connector to a circuit id.** Both files are individually consistent; the
  seam between them is where the direction disappears.
- Consequence for spelling: **24 of the 55 master net names appear in no `.md`
  page** — `V3V3_CHAIN`, `CHAIN_SCK/SHLD/SER/QH`, `KEY_BITS`, `MARKER_BITS`,
  `DEV_3V3`, `INST_5V_A/B`, `SENSOR_RAW`, `SENSOR_BUFFERED_OUT`,
  `UMBILICAL_POS12`, `BUS_POS12_RAW`, `MODULE_ANALOG_POS12/NEG12`, `BUS_5V`,
  `DAC_AVDD`, `DAC_CH1`–`CH5`, `CH7`, `BREATH_INAMP_OUT` `[calc]`.

**What would make this wrong.** If `carrier/carrier` is deliberately *not* one of
the 23 circuits — and it is not; `hardware/README.md:47-50` counts 5 carrier
circuits and `hardware/carrier/netlist.yaml:3-7` says "carrier.md is the board
page rather than a circuit page" — then no Interfaces table is owed. That is
true and does not dispose of the finding: the master still names it as a circuit
endpoint 20 times, and a board page that is a master endpoint is a fourth kind of
thing the README does not define.

**Smallest fix.** One paragraph in `hardware/README.md`'s `## Interfaces` section
saying that `carrier/carrier` is a board-page endpoint whose side is declared in
`hardware/carrier/netlist.yaml` and *not* in any Interfaces table, and that
`HDR-DEV` in a Peer column means it. Anything larger (adding a table, adding a
`circuit.yaml`) is a design decision, not a transcription.

---

## N6-2 — HIGH — `SCLK`/`MOSI`/`CS_MOD`: `spi-link.md` says `out` on three nets the master says it receives

**Net / circuit:** `SCLK`, `MOSI`, `CS_MOD` / `interfaces/spi-link`.

**Claim.** The driver moved to `carrier/carrier` during the conversion and the
page that used to claim it still says `out` — the exact "two pages both claiming
to source one net" defect the Dir column exists to make visible
`[repo hardware/README.md:88-92]`.

**Evidence, both ends.**
- Master: `driver: carrier/carrier`, `receivers: [interfaces/spi-link,
  module/digital-and-supervision]`, with a note that says in as many words
  "**THE DRIVER IS THE DEV BOARD, not the link** … `interfaces/spi-link` is the
  connector and the cable in between - a pass-through, which this schema records
  as a receiver" `[repo hardware/nets.yaml:281-289]`.
- `spi-link.md:38-40`: `| SCLK | instrument → module | **out** | HDR-DEV IO35 →
  module/digital-and-supervision |`, and the same for `MOSI` and `CS_MOD`.
- Its own netlist contradicts its page: `SCLK/MOSI/CS_MOD: {dir: in, from:
  carrier/carrier}` `[repo hardware/interfaces/spi-link/netlist.yaml:26-28]`.
- The parts settle it: all three `R-SPI-SER` instances are placed on the carrier
  (`R-SPI-SER-SCLK/-MOSI/-CS` in `hardware/carrier/netlist.yaml:75-89`), and the
  `spi-link` netlist header says so — "the three series resistors are on the
  carrier (carrier/carrier). Owning a row and placing an instance are different
  things" `[repo hardware/interfaces/spi-link/netlist.yaml:14-19]`.

**What would make this wrong.** If Dir in a two-ended table (`End` column) meant
the net's own direction of travel rather than this circuit's side. Rows 52-53 of
`breath-sense-link.md` use `out` in the this-circuit sense for nets it really
drives, and `hardware/README.md:84` defines Dir as "**This circuit's side** of
the net" with no exemption for `End` tables — so no.

**Smallest fix.** `out` → `in` on `spi-link.md:38-40`. The master and the
netlist are already right.

---

## N6-3 — HIGH — `SENSOR_BUFFERED_OUT`: the driver's page never mentions it, and the two pages that do name the wrong source

**Net / circuit:** `SENSOR_BUFFERED_OUT` / `carrier/breath-excitation-reference`,
`carrier/breath-adc`, `interfaces/breath-sense-link`.

**Claim.** The master's driver is right and no page agrees with it: the driver's
own table has no row, one receiver names the other receiver as its source, and
the other receiver claims `out`.

**Evidence, all three ends.**
- Master: `driver: carrier/breath-excitation-reference`, `receivers:
  [carrier/breath-adc, interfaces/breath-sense-link]`
  `[repo hardware/nets.yaml:258-263]`.
- The master is **correct**: `U-BREATHBUF` (OPA2197 section B, "buffering the
  sensor's output before anything loads it") is a component of
  `breath-excitation-reference`, and its netlist nets `SENSOR_BUFFERED_OUT` to
  `U-BREATHBUF.OUT`
  `[repo hardware/carrier/breath-excitation-reference/netlist.yaml:72-77,157-160]`.
- **The driver's page has no row for it.** All five rows of
  `breath-excitation-reference.md`'s table are `+12V`, `REF5050 VOUT` (`—`),
  `op-amp output` (`—`), `VS` (`out`), `AGND_INST` (`ref`)
  `[repo hardware/carrier/breath-excitation-reference/breath-excitation-reference.md:26-30]`.
  Nothing in the corpus's prose says this circuit sources this net.
- `breath-adc.md:25`: `| buffered sensor output | in | **interfaces/breath-sense-link** |`
  — the wrong peer; its own netlist says
  `{dir: in, from: carrier/breath-excitation-reference}`
  `[repo hardware/carrier/breath-adc/netlist.yaml]`.
- `breath-sense-link.md:57`: `| buffered sensor output | instrument | **out** |
  carrier/breath-adc |` — claims to source it, to a peer it has no connection
  with; its own netlist says `{dir: in, from: carrier/breath-excitation-reference}`
  `[repo hardware/interfaces/breath-sense-link/netlist.yaml:22]`.

**What would make this wrong.** If the buffer were `breath-sense-link`'s part.
It is not: that circuit's components are `U-BREATH`, `R1`, `R1b` and the two
`D-TVS-BREATH`, and its header says "R-SER-BREATH IS NOT HERE … this circuit's
rows are the instrument-side 1k pair and the sensor"
`[repo hardware/interfaces/breath-sense-link/netlist.yaml:6-9,28-62]`.

**Smallest fix.** Add one row to `breath-excitation-reference.md`'s table —
`| buffered sensor output | out | carrier/breath-adc, interfaces/breath-sense-link | sensor-full-scale | Sourced here: the other OPA2197 half |`
— change `breath-adc.md:25`'s Peer to `carrier/breath-excitation-reference`, and
change `breath-sense-link.md:57`'s Dir to `in` with Peer
`carrier/breath-excitation-reference`.

---

## N6-4 — HIGH — `DAC_AVDD`: the receiver moved from `spi-link` to `digital-and-supervision`, and `power-entry.md` now explicitly denies the receiver the master asserts

**Net / circuit:** `DAC_AVDD` / `module/power-entry`, `module/digital-and-supervision`,
`interfaces/spi-link`.

**Claim.** The master is right and the origin page states the opposite in bold.

**Evidence, both ends.**
- Master: `receivers: [module/dac8568, module/breath-output-stage,
  module/breath-receive-stage, module/digital-and-supervision   # the DAC-side
  SYNC pull-up returns here, not to bus +5V]` — `interfaces/spi-link` is **not**
  listed `[repo hardware/nets.yaml:424-432]`.
- The master is **correct**: all six `R-SPI-PULL` are placed on
  `digital-and-supervision`, and `R-PULL-SYNC.2` is on the `DAC_AVDD` net there
  `[repo hardware/module/digital-and-supervision/netlist.yaml:64-82,117-119]`.
  The `spi-link` netlist agrees — "the six pulls are on the module board
  (module/digital-and-supervision)"
  `[repo hardware/interfaces/spi-link/netlist.yaml:14-19]` — and declares no
  `DAC_AVDD` port.
- **`power-entry.md:29` says the opposite, in bold:**
  `| DAC AVDD | out | module/dac8568, module/breath-receive-stage,
  module/breath-output-stage, **interfaces/spi-link** | dac-rail | … **Not
  `module/digital-and-supervision`**, whose 74AHCT125 runs from bus `+5V` |`.
  It names the one circuit the master dropped and denies the one the master
  added. The negation was true of the *buffer's* rail and is false of the
  *pull-up's*, and it is now the only prose statement of this net's receivers.
- **`spi-link.md:46` keeps the row too**, with Dir `in`:
  `| DAC AVDD | module | in | module/power-entry | dac-rail | What the DAC-side
  CS pull returns to, **not** bus +5V |`. It owns the row; it does not place it,
  so the net reaches no part of it and Dir should be `—`.
- `digital-and-supervision.md`'s table has **no `DAC AVDD` row at all** — seven
  rows, none of them this net
  `[repo hardware/module/digital-and-supervision/digital-and-supervision.md:26-32]`.

**What would make this wrong.** If owning a BOM row put the net on the owning
circuit's boundary. `hardware/README.md:147-148` and the `spi-link` netlist
header both say the opposite.

**Smallest fix.** On `power-entry.md:29`, swap `interfaces/spi-link` for
`module/digital-and-supervision` and delete the "**Not
`module/digital-and-supervision`**" clause (git holds the old reasoning). On
`spi-link.md:46`, Dir `in` → `—`. Add a `DAC AVDD` row to
`digital-and-supervision.md`.

---

## N6-5 — MEDIUM-HIGH — `CHAIN_QH` and `IO40` are two master nets for one node, and the netlist says so

**Net / circuit:** `CHAIN_QH`, `IO40` / `interfaces/key-chain-loom`.

**Claim.** A split with nothing in series — the case the master's own
`UMBILICAL_POS12` note says it went back and merged.

**Evidence.** `hardware/interfaces/key-chain-loom/netlist.yaml:141-147`:

    # ONE NET, TWO BOUNDARIES: nothing sits between the connector and the MCU
    # pin but the clamp, so QH arriving from the clusters and IO40 going into
    # the dev board are the same node.
    CHAIN_QH:
      - J-CHAIN.8
      - U-TVS-CHAIN.CH4
      - port: CHAIN_QH
      - port: IO40

One net, two ports, and the master carries both as separate entries with
opposite drivers — `CHAIN_QH` `driver: cluster/key-register`, `IO40`
`driver: interfaces/key-chain-loom` `[repo hardware/nets.yaml:66-71,155-160]`.
Compare the master's own rule, written for exactly this: "The carrier's '+12V
strip feed' and '+12V analog' are not separate nets … They were two more entries
here until the netlist had to name both ends of each and there was only one node
to name" `[repo hardware/nets.yaml:365-369]`.

**And the other four splits at this boundary are legitimate**, which is what
makes this one stand out `[calc]` from
`hardware/interfaces/key-chain-loom/netlist.yaml`:
`IO38`→`CHAIN_SCK` through `R-CHAIN-SER-SCK` (100R), `IO7`→`CHAIN_SHLD` through
`R-CHAIN-SER-SHLD`, `IO33`→`CHAIN_SER` through `R-CHAIN-SER-SER`, and
`DEV_3V3`→`V3V3_CHAIN` through `F-CHAIN` (100 mA polyfuse). Four have a part
between them; the fifth has a clamp to ground and nothing in series.

**What would make this wrong.** If the *master* intends one entry per boundary
crossing rather than one per node — but then `CHAIN_QH`'s and `IO40`'s drivers
could not disagree, and the `UMBILICAL_POS12` note would not exist.

**Smallest fix.** Delete `IO40` and give `CHAIN_QH` `receivers:
[interfaces/key-chain-loom, carrier/carrier]`; drop the `IO40` port from
`carrier/netlist.yaml` and `key-chain-loom/netlist.yaml`, and net `carrier`'s
`U-MCU-RT.IO40` on `CHAIN_QH`. *Or* keep both and say in the entry why, as
`DEV_3V3`/`V3V3_CHAIN` implicitly does by having a fuse.

---

## N6-6 — MEDIUM-HIGH — `interfaces/spi-link`: 8 master assertions, 1 confirmed by its table, 4 with no row at all

**Net / circuit:** `BREATH_SENSE`, `AGND_SENSE`, `UMBILICAL_POS12`, `PWR_GND` /
`interfaces/spi-link`.

**Claim.** The circuit that owns both umbilical connectors has an Interfaces
table for four conductors and a netlist for eight, and the four missing ones are
master endpoints.

**Evidence, both ends.**
- Master names `spi-link` on 8 nets: `SCLK` in, `MOSI` in, `CS_MOD` in,
  `DIG_GND` ref, `BREATH_SENSE` in, `AGND_SENSE` in, `UMBILICAL_POS12` in,
  `PWR_GND` ref `[calc]`.
- Its netlist declares all 8 ports and nets each to a pin of `J-UMB-INST` /
  `J-UMB-MOD`, **its own components**, so all eight genuinely reach parts of this
  circuit `[repo hardware/interfaces/spi-link/netlist.yaml:24-33,36-52,54-118]`.
  The header says it outright: "This circuit is named for the SPI half and it
  carries all eight conductors … They are declared here because the CONNECTOR is
  here" (lines 1-8).
- Its table has 11 rows and **none of them is `BREATH_SENSE`, `AGND_SENSE`,
  `UMBILICAL +12V` or `PWR_GND`** (`PWR_GND` appears only inside the
  `U-TVS-SPI` note) `[repo hardware/interfaces/spi-link/spi-link.md:38-48]`.
  The page's own opening says "**Three** conductors and a return leave the
  carrier" (line 9) — a four-conductor description of an eight-conductor circuit.
- Tallied: of 8 assertions, 1 is confirmed (`DIG_GND` ref), 3 have the wrong Dir
  (N6-2), 4 have no row, and 1 row exists for a net the master does not assert
  (`DAC AVDD`, N6-4).
- The far ends do not name it either: `breath-sense-link.md:52-53` give
  `BREATH_SENSE`/`AGND_SENSE` the Peer `carrier/carrier.md §2 →
  module/breath-receive-stage`, and `umbilical-load-switch.md:25` gives
  `UMBILICAL +12V` the Peers `carrier/power-entry-instrument,
  module/link-supervision`. So for these four nets the master's `spi-link`
  endpoint is asserted by one netlist and no page at either end.

**What would make this wrong.** If a connector pin did not count as the net
reaching the circuit. Then `spi-link`'s ports for all four should go, and the
master should drop it from all four — the finding changes sides but does not go
away.

**Smallest fix.** Four rows on `spi-link.md`, Dir `in`/`in`/`in`/`ref`, Peer
`interfaces/breath-sense-link`, `interfaces/breath-sense-link`,
`module/umbilical-load-switch`, `module/power-entry`, each noting that the
conductor is another circuit's net passing through this circuit's connector —
which is what the netlist header already says.

---

## N6-7 — MEDIUM — `UMBILICAL_POS12`: the merge landed in the netlists and in none of the three pages

**Net / circuit:** `UMBILICAL_POS12` / `carrier/power-entry-instrument`,
`carrier/led-strip-drive`, `carrier/breath-excitation-reference`.

**Claim.** Two carrier nets were merged into the module-sourced one; the three
carrier pages still describe the pre-merge topology, and two of them still claim
to source it.

**Evidence, both ends.**
- Master: `driver: module/umbilical-load-switch`, receivers
  `[carrier/power-entry-instrument, carrier/led-strip-drive,
  carrier/breath-excitation-reference, interfaces/spi-link]`, with the merge
  recorded in the note `[repo hardware/nets.yaml:345-370]`.
- Driver's page agrees: `umbilical-load-switch.md:25` `| UMBILICAL +12V | out |`.
- `power-entry-instrument.md:21-22` still carries **two rows with Dir `out`** —
  `| +12V strip feed | out | carrier/led-strip-drive |` and `| +12V analog | out
  | carrier/breath-excitation-reference |` — each with a note saying "**The same
  net as the row above**". After the merge the row above is
  `UMBILICAL_POS12`, whose driver is the module. So this page claims to source a
  net the master sources elsewhere, twice.
- `breath-excitation-reference.md:26` gives `+12V` Dir `in` with Peer
  `carrier/power-entry-instrument`; its netlist says `{dir: in, from:
  module/umbilical-load-switch}` `[repo .../netlist.yaml:14]`.
- `led-strip-drive.md:27` gives the `J-LED` `+12V` Dir **`—`** with Peer
  `carrier/power-entry-instrument`; its netlist declares
  `UMBILICAL_POS12 {dir: in}` and nets it to `J-LED-L.POS12`, `J-LED-R.POS12`
  `[repo hardware/carrier/led-strip-drive/netlist.yaml:16,124-127]`. Its own
  component note even says "Strip power … is carrier/power-entry-instrument's
  net, not this circuit's" (line 92) while the same file nets it. See N6-9.

**What would make this wrong.** If a `+12V` tap on the same copper could
legitimately be described as sourced by the board that taps it. The master's note
and `merge-bom`'s "a row lives with the circuit whose page derives its value"
both say a net has one source; the merge note says there is only one node.

**Smallest fix.** On `power-entry-instrument.md:21-22`, Dir `out` → `—` (or fold
both rows into the `UMBILICAL +12V` row, which is what the master did). Change
the Peer on `breath-excitation-reference.md:26` and `led-strip-drive.md:27` to
`module/umbilical-load-switch`.

---

## N6-8 — MEDIUM — `nets.yaml`'s own comment says `spi-link` is a receiver on `SCLK_DAC`/`DIN`/`SYNC`; none of the three entries names it

**Net / circuit:** `SCLK_DAC`, `DIN`, `SYNC` / `interfaces/spi-link`.

**Claim.** A stale assertion inside the master, three lines above the entries
that refute it.

**Evidence.** `[repo hardware/nets.yaml:469-475]`:

    # interfaces/spi-link is a receiver on all three because the DAC-side three
    # of the six R-SPI-PULL sit on them and are that circuit's rows.

The three entries that follow declare `driver: module/digital-and-supervision`,
`receivers: [module/dac8568]` and nothing else
`[repo hardware/nets.yaml:477-492]`. `spi-link`'s netlist declares no such port.
And the reason given is itself wrong: all six `R-SPI-PULL` are *placed* on
`digital-and-supervision` `[repo hardware/module/digital-and-supervision/netlist.yaml:64-82]`,
which is why `spi-link.md:45` correctly gives the three Dir `—` ("**Not sourced
here** … these three are a module-board net"). So the comment states a
connection the master does not make, for a reason the netlists contradict.

**What would make this wrong.** Nothing I can see; the comment and the entries
cannot both hold.

**Smallest fix.** Delete the two sentences, or reduce them to the true half: the
DAC-side pull-ups are `spi-link`'s rows and `digital-and-supervision`'s
instances.

---

## N6-9 — MEDIUM — `led-strip-drive.md`'s one `—` row covers two nets that both have declared ports

**Net / circuit:** `UMBILICAL_POS12`, `PWR_GND` / `carrier/led-strip-drive`.

**Claim.** A `—` row — "no connection here, the row is context"
`[repo hardware/README.md:84]` — sits over two nets on which this circuit is a
master endpoint and declares ports.

**Evidence, both ends.** `led-strip-drive.md:27`: `| +12V, GND at J-LED-L/-R | —
| carrier/power-entry-instrument | — | Strip power passes through this connector
but is that circuit's net |`. Against it: master `UMBILICAL_POS12` receivers
include `carrier/led-strip-drive`, master `PWR_GND` reference includes it
`[repo hardware/nets.yaml:349,377-383]`; and its netlist declares
`UMBILICAL_POS12 {dir: in}` and `PWR_GND {dir: ref}`, netting `J-LED-L.POS12`,
`J-LED-R.POS12`, `J-LED-L.GND`, `J-LED-R.GND`, `J-LED-L.BI`, `J-LED-R.BI` — all
components of this circuit
`[repo hardware/carrier/led-strip-drive/netlist.yaml:15-17,124-127,148-163]`.

The master applied the opposite reading elsewhere and said so: `BUS_5V`'s note
is "A '-' row is context, not a connection, and it was seeded here as one"
`[repo hardware/nets.yaml:418-420]`. It removed `spi-link` from `BUS_5V` on that
principle and kept `led-strip-drive` here. **Keeping it is the right call** —
`spi-link` has no part on `BUS_5V`, `led-strip-drive` has four connector pins on
these two — so the defect is in the page's Dir, not the master's list.

**What would make this wrong.** If a connector pin is not a connection — see
N6-6, same question, same answer both times.

**Smallest fix.** Split `led-strip-drive.md:27` into `+12V at J-LED-L/-R` Dir
`in` Peer `module/umbilical-load-switch`, and `GND at J-LED-L/-R` Dir `ref` Peer
`module/power-entry`, keeping the note that neither net is derived here.

---

## N6-10 — MEDIUM — `V3V3_CHAIN` at `key-marker-and-bits` is `ref` on the page and `in` everywhere else

**Net / circuit:** `V3V3_CHAIN` / `cluster/key-marker-and-bits`.

**Evidence, both ends.** Master: `V3V3_CHAIN` `receivers: [cluster/key-register,
cluster/key-switch-network, cluster/key-marker-and-bits]` — role `in`
`[repo hardware/nets.yaml:36-40]`. Netlist: `V3V3_CHAIN: {dir: in, from:
interfaces/key-chain-loom}`
`[repo hardware/cluster/key-marker-and-bits/netlist.yaml]`. Page:
`key-marker-and-bits.md:23` `| `3V3`, `GND` | **ref** | interfaces/key-chain-loom |`
— one row for two nets with one Dir, and `ref` is right for `GND_CHAIN` only.
The two sibling pages get it right: `key-register.md:25` `3V3` `in`,
`key-switch-network.md:20` `3V3` `in`.

The marker straps land "directly on the rails" (same row's note), so 3V3 is a
*source of the asserted bit*, not a return — `in` is correct and `ref` is not.
The checker cannot see it: `check_master` compares only `netlist.yaml`'s `dir`,
and that one says `in` `[repo tools/check-netlist.py:143-161]`.

**What would make this wrong.** If a rail a strap ties to counted as a reference.
`hardware/README.md:84` defines `ref` as "a return or a reference"; the high
strap's rail is neither — it is the logic level being read.

**Smallest fix.** Split the row: `3V3` Dir `in`, `GND` Dir `ref`.

---

## N6-11 — MEDIUM — `AGND_MOD` at `module/panel-led` is asserted by the master, disclaimed by the circuit and absent from the origin's page

**Net / circuit:** `AGND_MOD` / `module/panel-led`, `module/power-entry`.

**Claim.** The one master assertion I can show is *speculative* on the master's
own rule — "A NET HERE ASSERTS A CONNECTION. Do not add one speculatively"
`[repo hardware/nets.yaml:26-27]`.

**Evidence, both ends.**
- Master `AGND_MOD` `reference:` includes `module/panel-led`
  `[repo hardware/nets.yaml:434-448]`.
- `panel-led`'s netlist nets `LED-PANEL.K` to `AGND_MOD` and annotates it
  "**WHICH GROUND IT LANDS ON IS THE DISPUTED FIGURE** … AGND_MOD is **the
  reading that matches the rail**; if the figure settles the other way this line
  moves with it" `[repo hardware/module/panel-led/netlist.yaml:24-31]`.
- Its page is blunter: `panel-led.md:18` `| LED return | ref | module/power-entry
  | dig-gnd-topology | **Not drawn anywhere in the corpus.** … which ground it
  lands on is the disputed figure |`.
- **The origin's page omits it.** `power-entry.md:33`'s `AGND_MOD` row names
  `dac8568, pitch-stage, breath-receive-stage, breath-output-stage,
  breath-response-shaper, mod-channels` — six circuits, not `panel-led` — while
  the same page's `MODULE ANALOG +12V` row (line 27) *does* name `panel-led`.
  So the origin page names the rail and not the return.
- The corpus has a mechanism for exactly this and did not use it here:
  `module/breath-response-shaper`'s comparable uncertainty is carried as
  `proposed:` on four nets `[repo hardware/nets.yaml:400,411,443,555]`.

**What would make this wrong.** If `reference:` meant "returns to the module
analog domain, wherever that lands" rather than "returns to this node". The
`AGND_MOD` entry's own note — "This file records which circuits reference the net;
it does NOT settle the topology" — argues for the weaker reading, in which case
the finding is only the `power-entry.md` omission.

**Smallest fix.** Add `module/panel-led` to `power-entry.md:33`'s peer list. If
the weaker reading is intended, say so in the `AGND_MOD` note — it currently
disclaims the *topology*, not the *membership*.

---

## N6-12 — MEDIUM — `PWR_GND`: the origin page names 2 of the 6 circuits the master does

**Net / circuit:** `PWR_GND` / `module/power-entry`.

**Evidence, both ends.** Master: `origin: module/power-entry`, `reference:
[module/umbilical-load-switch, carrier/power-entry-instrument,
interfaces/spi-link, carrier/display-and-service-uart, carrier/led-strip-drive,
carrier/carrier]` `[repo hardware/nets.yaml:372-395]`. Origin page:
`power-entry.md:32` `| PWR_GND | ref | module/umbilical-load-switch,
carrier/power-entry-instrument | umbilical-current |` — two. The four it omits
each declare the port: `spi-link`, `display-and-service-uart`, `led-strip-drive`
and `carrier/carrier` all carry `PWR_GND: {dir: ref, from: module/power-entry}`
`[calc]` over their netlists. Two of the four are covered by
`power-entry-instrument.md:25`'s "PWR_GND pour" row instead, which names
`display-and-service-uart, led-strip-drive, carrier/carrier` — so the carrier
half is documented on the carrier and the master's single-net model is documented
nowhere.

**What would make this wrong.** If `PWR_GND` were two nets (a module return and a
carrier pour) that the master merged. It is one: the master models it as one net
crossing the umbilical, and `power-entry-instrument.md:20` calls `J-UMB`'s
`PWR_GND` "This board's only supply return, down the umbilical to the module
star".

**Smallest fix.** Extend `power-entry.md:32`'s Peer cell to the six, or add one
clause saying the carrier's four references are enumerated on
`power-entry-instrument.md`.

---

## N6-13 — MEDIUM — `AGND_INST`: the origin's page has no row for it, and one `reference:` circuit has none either

**Net / circuit:** `AGND_INST` / `carrier/power-entry-instrument`,
`interfaces/breath-sense-link`.

**Evidence, both ends.** Master: `origin: carrier/power-entry-instrument`,
`reference: [carrier/breath-adc, carrier/breath-excitation-reference,
interfaces/breath-sense-link]` `[repo hardware/nets.yaml:265-273]`.
`power-entry-instrument.md`'s seven rows contain **no `AGND_INST` row**; the name
appears only inside the `PWR_GND pour` note, arguing why two circuits are *not*
on `PWR_GND` `[repo .../power-entry-instrument.md:17-25]` — the star point's page
never names the star. `breath-sense-link.md` likewise has no `AGND_INST` row;
the name appears twice in prose (lines 43, 53) saying what `AGND_SENSE` is *not*,
while its netlist declares `AGND_INST {dir: ref}` and nets `R1b.1`,
`U-BREATH.GND` and both TVS anodes onto it
`[repo hardware/interfaces/breath-sense-link/netlist.yaml:27,105-110]`. The two
circuits that do carry the row are right: `breath-adc.md:29` and
`breath-excitation-reference.md:30`, both `ref`, both Peer
`carrier/power-entry-instrument`.

**What would make this wrong.** If an `origin` circuit owed no row for the net it
originates. `hardware/README.md:54-56` says the table carries "every net that
crosses that circuit's boundary, one row each", and the master gives this one
four endpoints.

**Smallest fix.** One row on each of the two pages, Dir `ref`.

---

## N6-14 — MEDIUM — `SENSOR_RAW` is named by no `## Interfaces` table at either end

**Net / circuit:** `SENSOR_RAW` / `interfaces/breath-sense-link`,
`carrier/breath-excitation-reference`.

**Evidence, both ends.** Master: `driver: interfaces/breath-sense-link`,
`receivers: [carrier/breath-excitation-reference]`
`[repo hardware/nets.yaml:252-256]`. Both netlists declare it and the connection
is real: `U-BREATH.VOUT` → `U-BREATHBUF.IN+`
`[repo hardware/interfaces/breath-sense-link/netlist.yaml:96-98]`,
`[repo hardware/carrier/breath-excitation-reference/netlist.yaml:153-155]`.
Neither page has a row: `breath-sense-link.md` has `U-BREATH (MPXV4006DP)` with
Dir `—` (line 55), and `breath-excitation-reference.md`'s five rows do not
mention the sensor's output at all. `[test] grep -rn SENSOR_RAW hardware --include=*.md`
→ no hits.

**What would make this wrong.** If the sensor and its buffer were one circuit —
they are not; the sensor is `breath-sense-link`'s row and the buffer is
`breath-excitation-reference`'s, and the master's boundary between them is what
makes this net exist.

**Smallest fix.** One row per page: on `breath-sense-link.md` Dir `out` Peer
`carrier/breath-excitation-reference`; on `breath-excitation-reference.md` Dir
`in` Peer `interfaces/breath-sense-link`. Together with N6-3 this makes the §2
analog chain's three internal nets legible from the tables for the first time.

---

## N6-15 — MEDIUM — `BREATH_INAMP_OUT`: three pages put `interfaces/breath-sense-link` on it, including one claiming `out`

**Net / circuit:** `BREATH_INAMP_OUT` / `interfaces/breath-sense-link`.

**Evidence, three ends.** Master: `driver: module/breath-receive-stage`,
`receivers: [module/breath-output-stage]`, `proposed:
[module/breath-response-shaper]` — `breath-sense-link` is **not** named
`[repo hardware/nets.yaml:551-562]`, and it has no such port and no module-side
component `[repo hardware/interfaces/breath-sense-link/netlist.yaml]`. Against
that:
- `breath-sense-link.md:60` `| in-amp output | module | **out** |
  module/breath-receive-stage → module/breath-output-stage |` — Dir `out` on a
  net whose driver is another circuit, and whose parts are all on another board.
- `breath-receive-stage.md:47` names `interfaces/breath-sense-link` in the Peer
  list of its own `out` row.
- `breath-output-stage.md:22` names it in the Peer list of its `in` row.

The master is right (the INA828 is `breath-receive-stage`'s). Two of the three
pages are cross-references that read as endpoints; the third asserts a source.
This is the same failure as N6-2 and N6-3 in the same table: `breath-sense-link.md`
uses Dir `out` both for nets it drives (rows 52-53, correct) and for nets it
merely narrates (rows 57, 60), and its Peer column holds an `A → B` path rather
than a peer.

**What would make this wrong.** If `breath-sense-link.md` is understood as the
page where the in-amp's full-scale figure is *derived* rather than a circuit
boundary — which its own note says ("The figure is owned at the module end and
derived here"). Deriving a figure is not an endpoint.

**Smallest fix.** `out` → `—` on `breath-sense-link.md:57` and `:60`. That one
character on two rows also closes half of N6-3.

---

## N6-16 — MEDIUM — `key-chain-loom.md`'s four signal rows carry one Dir each across two master nets

**Net / circuit:** `IO38`/`CHAIN_SCK`, `IO7`/`CHAIN_SHLD`, `IO33`/`CHAIN_SER`,
`CHAIN_QH`/`IO40`, `DEV_3V3`/`V3V3_CHAIN` / `interfaces/key-chain-loom`.

**Claim.** The loom's netlist declares 11 ports against 4 signal rows plus a
3V3 row, so the `in` half of each pair is stated nowhere in prose.

**Evidence, both ends.** `key-chain-loom.md:30-35` gives one row per conductor
with a single Dir — `SCK` `out`, `SH/LD` `out`, `SER` `out`, `QH` `in`, `3V3`
`out` — and a Peer cell holding the whole path (`HDR-DEV IO38 →
cluster/key-register`). The netlist declares both halves separately, with the
opposite dir on the carrier side: `IO38/IO7/IO33 {dir: in}`, `DEV_3V3 {dir: in}`,
`IO40 {dir: out}` `[repo hardware/interfaces/key-chain-loom/netlist.yaml:20-30]`,
matching the master `[repo hardware/nets.yaml:137-166]`. So four master
assertions (`IO38` in, `IO7` in, `IO33` in, `DEV_3V3` in) and one (`IO40` out)
have no prose row with a matching Dir.

The `3V3` row compounds it: its Peer list is `HDR-DEV →
cluster/key-switch-network, cluster/key-register, carrier/breath-adc` — which
mixes `DEV_3V3`'s receiver (`carrier/breath-adc`, upstream of `F-CHAIN`) with
`V3V3_CHAIN`'s (downstream), and **omits `cluster/key-marker-and-bits`**, which
the master lists and whose netlist declares the port.

**What would make this wrong.** If a pass-through circuit is meant to carry one
row per conductor rather than one per net. That is defensible for a loom — but
then N6-5's `CHAIN_QH`/`IO40` pair is the master's bug, and either way the two
files disagree about how many nets there are.

**Smallest fix.** Either split the four rows into eight, or add one sentence
above the table saying each row spans the two master nets either side of the
loom's series part and naming them. Add `cluster/key-marker-and-bits` to the
`3V3` row regardless.

---

## N6-17 — LOW (suspicion) — `GND_CHAIN` and `PWR_GND`: the master's own note says they are not separate nodes

**Net / circuit:** `GND_CHAIN` / `interfaces/key-chain-loom`, `PWR_GND` /
`module/power-entry`.

**Claim (suspicion).** Two master nets with two different origins for what the
master says is one node, and — unlike `DEV_3V3`/`V3V3_CHAIN` — with nothing in
series named to justify the split.

**Evidence.** `GND_CHAIN`: `origin: interfaces/key-chain-loom`, note "**It is the
carrier's PWR_GND pour arriving on HDR-DEV's ground pins - a separate name for
the five conductors in the ribbon, not a separate node**"
`[repo hardware/nets.yaml:42-48]`. `PWR_GND`: `origin: module/power-entry`, with
`carrier/carrier` in its `reference` list `[repo hardware/nets.yaml:372-383]`.
The loom netlist nets `GND_CHAIN` to `J-CHAIN.1/3/5/7/9` and `U-TVS-CHAIN.GND`
with no series element `[repo .../key-chain-loom/netlist.yaml:169-176]`. By the
`UMBILICAL_POS12` precedent (`[repo hardware/nets.yaml:365-369]`, quoted in
N6-5) this is one node under two names, with two origins.

**Why I mark it suspicion rather than a defect.** For a reference net, naming the
ribbon's five conductors separately buys something a merge would lose — the
cluster pages' `ref` rows point at the loom, which is where the conductor count
and the alternation argument live. A merge would also make `module/power-entry`
the origin of a cluster-board ground, which reads worse than the split does.

**Smallest fix if it is a defect.** Nothing in the data: add the justification
the note is missing — that the split is deliberate and by *conductor*, the way
`DEV_3V3`/`V3V3_CHAIN`'s is by *fuse*.

---

## N6-18 — LOW (suspicion) — `CHAIN_SER` and `CHAIN_QH` are per-hop nets modelled as single nets, where `KEY_BITS` got `per_board:`

**Net / circuit:** `CHAIN_SER`, `CHAIN_QH` / `cluster/key-register`,
`interfaces/key-chain-loom`.

**Evidence.** Master: `CHAIN_SER` "POINT TO POINT, not a bus", `CHAIN_QH` "Point
to point, like SER", each a single entry with one driver and one receiver
`[repo hardware/nets.yaml:57-71]`. The pages say there is more than one net:
`key-chain-loom.md:33` — "`QH` … **Point to point, and a different net on each
side of every board.**" — and `key-register.md:22` — "`SER` … The next board's
`QH`, or the carrier through `LK-SER`", on a netlist that is `replicated: 4`.
The loom's netlist header agrees and says why it stopped: "SER and QH are POINT
TO POINT and change meaning at every hop … Modelling that means naming which
board's OUT reaches which board's IN, and that hop map is prose on this page and
in no file a tool reads" `[repo .../key-chain-loom/netlist.yaml:4-14]`.

This is the same shape as `KEY_BITS`/`MARKER_BITS`, which got `per_board: true`
and an explicit "EIGHT NETS PER DEVICE, NOT ONE" `[repo hardware/nets.yaml:74-99]`
plus a counted, printed exemption in the tool
`[repo tools/check-netlist.py:107-118]`. `CHAIN_SER`/`CHAIN_QH` got neither, so
`check-netlist.py` proves both ends of a two-ended net that is really a
five-node chain, and prints nothing.

**What would make this wrong.** If `CHAIN_SER`/`CHAIN_QH` name the *carrier-side
hop only* — which the loom netlist's scope ("OF THE CARRIER END") supports. Then
the entries are right and only their notes over-claim.

**Smallest fix.** Say which in the entry: either add `per_board: true` (and
accept the printed gap, as `KEY_BITS` does), or add a `note:` scoping each net to
the carrier's hop and pointing at the hop map.

---

## N6-19 — LOW — `key-marker-and-bits.md` has two rows whose far ends say `—`

**Net / circuit:** the unnamed `switch positions` and `serial bit stream` rows /
`cluster/key-marker-and-bits`.

**Evidence, both ends.** `key-marker-and-bits.md:21` `| switch positions | **in**
| cluster/key-switch-network |`, against `key-switch-network.md:24` `| unfitted
positions | **—** | cluster/key-marker-and-bits |`. And
`key-marker-and-bits.md:22` `| the serial bit stream | **out** |
interfaces/key-chain-loom |`, against `key-chain-loom.md:40` `| the 32 bits |
clusters | **—** | cluster/key-marker-and-bits |`. Both of
`key-marker-and-bits`' notes describe an *allocation* ("take the rest of the
allocation", "rides on the chain order"), not a wire, and the master has no net
for either `[calc]` — correctly: the bits reach the loom only through
`key-register`'s `QH`, and the marker straps share no component with the switch
networks (that page's own row 23 says so).

**What would make this wrong.** If Dir could mark a logical dependency. Every
other `—` row in the corpus, including the two on the far side of these, uses
`—` for exactly this.

**Smallest fix.** Dir `in` → `—` on line 21, `out` → `—` on line 22.

---

## N6-20 — LOW — `from:`/`to:` in the netlists is unchecked, and 11 ports disagree with the master

**Net / circuit:** listed below.

**Claim.** `check-netlist.py` reads only `dir` from a port spec
`[repo tools/check-netlist.py:147,447]`; `from:` and `to:` are prose inside a
data file, and 11 of the 145 ports contradict the master.

**Evidence** `[test]` — a script over `hardware/nets.yaml` and all 22 netlists,
comparing each `in`/`ref` port's `from:` against the master's `driver`/`origin`
and each `out` port's `to:` against its `receivers`:

| circuit | port | netlist says | master says |
|---|---|---|---|
| `carrier/display-and-service-uart` | `IO6` | `from: carrier/carrier` | `external_driver` |
| `carrier/display-and-service-uart` | `U0RXD` | `from: carrier/carrier` | `external_driver` |
| `carrier/carrier` | `IO6` | `from: carrier/display-and-service-uart` | `external_driver` |
| `carrier/carrier` | `U0RXD` | `from: carrier/display-and-service-uart` | `external_driver` |
| `module/dac8568` | `CLR` | `from: module/link-supervision` | undriven; no such circuit in the master |
| `module/digital-and-supervision` | `SCLK`/`MOSI`/`CS_MOD` | `from: interfaces/spi-link` | `driver: carrier/carrier` |
| `module/power-entry` | `AGND_MOD`/`DIG_GND`/`PWR_GND` | no `from:`, uses `to:` on a `ref` port | `origin: module/power-entry` |

The `IO6`/`U0RXD` pair is the sharpest: the two circuits name **each other** as
the source of a net the master says is driven from outside the corpus, so three
files give three answers and no check reads two of them. The three
`digital-and-supervision` rows are the pass-through case (N6-2) and are
informative rather than wrong. `module/power-entry`'s three are an origin
declaring `to:` on a `ref` port, which is at least self-consistent.

**What would make this wrong.** If `from:`/`to:` were documented as "the adjacent
circuit on this net" rather than "the driver". Nothing documents them at all —
`hardware/README.md:19-22` and the `nets.yaml` header describe `ports:` only in
terms of naming a master net and matching a `dir`.

**Smallest fix.** `IO6`/`U0RXD`: `from: "the display board (external)"` /
`from: "the service header (external)"` in both netlists. The rest is a
documentation line saying what `from:`/`to:` means, in `hardware/README.md`.

---

## N6-21 — LOW — `breath-response-shaper`'s netlist says the master carries it on three nets; the master carries it on four

**Net / circuit:** `BREATH_INAMP_OUT`, `MODULE_ANALOG_POS12`,
`MODULE_ANALOG_NEG12`, `AGND_MOD` / `module/breath-response-shaper`.

**Evidence, both ends.** `[repo hardware/module/breath-response-shaper/netlist.yaml:4-6]`
— "hardware/nets.yaml carries it under `proposed:` on **the three nets** it
reads". `[test] grep -n "proposed:" hardware/nets.yaml` → 4 entries, at lines
400 (`MODULE_ANALOG_POS12`), 411 (`MODULE_ANALOG_NEG12`), 443 (`AGND_MOD`) and
555 (`BREATH_INAMP_OUT`). No grouping gives three: the rails plus the star plus
the signal is four, and the signal alone is one. A restated count that has moved
under the sentence stating it.

**Related, same circuit:** the page declares `| V_shaped | out |
module/breath-output-stage |` `[repo .../breath-response-shaper.md:29]`, and
there is no `V_shaped` in the master, no port in either netlist, and no row on
`breath-output-stage.md`. So the proposed circuit's **input** is modelled as
`proposed:` and its **output** is not modelled at all — half a connection. The
netlist explains the asymmetry honestly (the restoring half is undrawn, "writing
it would be inventing it"), so the omission is defensible; the asymmetry is
undocumented in the master.

**What would make this wrong.** If "three nets it reads" excluded the two rails
(which arrive through `U-RESP-A`'s `rails:`, not a port) — that gives two, not
three, and `AGND_MOD` is a port.

**Smallest fix.** "three nets" → "the four nets" (or cite the entries rather than
counting them, per `CLAUDE.md` rule 1). Optionally a `note:` on
`BREATH_INAMP_OUT` saying `V_shaped` is deliberately unmodelled until the
restoring half is drawn.

---

## N6-22 — LOW — `breath-output-stage`'s netlist carries `MODULE_ANALOG_NEG12` twice, once as an `external_endpoint`

**Net / circuit:** `MODULE_ANALOG_NEG12`, `MODULE_ANALOG_POS12` /
`module/breath-output-stage`.

**Evidence.** The file declares a `MODULE_ANALOG_NEG12` port netted to
`R-BREATH-OFFNEG.1`, and *also* a net `RAIL_NEG  # clamp to -12 V` holding
`D-JACK-CLAMP.A`, declared in `external_endpoints`
`[repo hardware/module/breath-output-stage/netlist.yaml:120-122,158-161,166]`.
Those are one node under two names in one file, one of them exempted from the
two-endpoint rule. `RAIL_POS` is the same for `MODULE_ANALOG_POS12`, which this
circuit reaches only implicitly, through `U-BREATH-BUF`/`U-BREATH-SUM`'s
`rails:` — the mechanism at `[repo tools/check-netlist.py:435-443]` that turns a
declared rail into an implicit `in` port. That implicit port is why
`check_master` is satisfied on `MODULE_ANALOG_POS12` for a circuit whose `ports:`
block does not name it, although the page's row does
`[repo .../breath-output-stage.md:24]` and the block's own comment says "These
must match the page's ## Interfaces table".

**What would make this wrong.** If the clamp rails are deliberately left
unresolved because the clamp returns to the rail *outside* this circuit — which
is what `external_endpoints`' comment says. But the `-12 V` rail is already a
declared port in the same file, so the exemption is not needed for that one.

**Smallest fix.** Net `D-JACK-CLAMP.A` onto `MODULE_ANALOG_NEG12` and drop
`RAIL_NEG` from `external_endpoints`; add an explicit `MODULE_ANALOG_POS12` port
and net `D-JACK-CLAMP.K` to it, which removes both exemptions and makes the
`ports:` block match the page as its comment promises.

---

## Per-net verdict, all 55

| net | verdict |
|---|---|
| `V3V3_CHAIN` | N6-10, N6-16 |
| `GND_CHAIN` | N6-17 (suspicion) |
| `CHAIN_SCK`, `CHAIN_SHLD` | both ends agree |
| `CHAIN_SER` | N6-18 (suspicion) |
| `CHAIN_QH` | N6-5, N6-16, N6-18 |
| `KEY_BITS`, `MARKER_BITS` | both ends agree; `per_board:` correct |
| `IO35`, `IO36`, `IO37`, `IO39` | N6-1 (carrier end has no prose row) |
| `IO38`, `IO7`, `IO33` | N6-1, N6-16 |
| `IO40` | N6-1, N6-5, N6-16 |
| `DEV_3V3` | N6-1, N6-16 |
| `IO1`, `IO2`, `IO5`, `U0TXD` | N6-1 |
| `IO6`, `U0RXD` | N6-1, N6-20 |
| `INST_5V_A` | N6-1 (carrier end) |
| `INST_5V_B`, `VS` | both ends agree |
| `SENSOR_RAW` | N6-14 |
| `SENSOR_BUFFERED_OUT` | N6-3 |
| `AGND_INST` | N6-13 |
| `BREATH_SENSE`, `AGND_SENSE` | N6-6 (`spi-link` end) |
| `SCLK`, `MOSI`, `CS_MOD` | N6-2 |
| `DIG_GND` | both ends agree |
| `UMBILICAL_POS12` | N6-7, N6-6, N6-9 |
| `PWR_GND` | N6-12, N6-6, N6-9, N6-1 |
| `BUS_POS12_RAW` | both ends agree |
| `MODULE_ANALOG_POS12` | both ends agree (N6-22 on the port form) |
| `MODULE_ANALOG_NEG12` | both ends agree (N6-22) |
| `BUS_5V` | both ends agree; the `—`-row removal is right |
| `DAC_AVDD` | N6-4 |
| `AGND_MOD` | N6-11 |
| `SCLK_DAC`, `DIN`, `SYNC` | N6-8 |
| `CLR` | N6-20 (peer names a circuit the master lacks); `undriven`+`pull` correct |
| `VREFOUT`, `DAC_CH1`–`DAC_CH5`, `DAC_CH7` | both ends agree |
| `BREATH_INAMP_OUT` | N6-15, N6-21 |

## The pattern, in one line

**The netlists and the master agree with each other and the pages were not
brought along.** Of 151 endpoint assertions, `check-netlist.py` proves 147
against `netlist.yaml` (the four on `KEY_BITS`/`MARKER_BITS` are skipped by
`per_board:` and printed instead) and **0 against an `## Interfaces` table** — and every finding
above except N6-5, N6-8, N6-11, N6-17 and N6-18 is a page that still describes
the pre-conversion topology. Three of them (N6-2, N6-3, N6-15) are pages claiming
`out` on a net they do not source, which is the one defect
`hardware/README.md:88-92` says the Dir column exists to make visible; one
(N6-4) is a page whose bolded negation now contradicts the corpus. A check that
compared the master's `driver`/`receivers`/`reference` against the Dir and Peer
cells — the tables the master says it was seeded from — would have caught
fourteen of these twenty-two, and nothing in `tools/` reads those cells.
