# C4 — the `## Interfaces` tables

**Agent:** C4, cold pre-merge review, 2026-09-21.
**Slice:** the `## Interfaces` tables — the one piece of new prose the
restructure permitted. Written by eight agents in parallel, never checked
against each other, now load-bearing for the dependency graph and for any
netlist transcription.

**Method.** All 22 tables extracted mechanically and compared row against row.
Every claim below is marked `[repo] path:line`, `[calc]` with the arithmetic
shown, or `[from memory]`. Findings are indexed by **net**, not by file.
**Nothing was fixed.** Per the cold rule I read nothing under `docs/review/**`.

`hardware/module/panel/panel.md` carries no table and says so `[repo]
hardware/module/panel/panel.md:3`. 22 circuits × 1 table; 158 rows total.

---

## Summary of what the audit found

| | |
|---|---|
| Machine-readable peer edges (bare `board/circuit` ids) | **49** `[calc]` |
| Of those, **one-sided** — the named peer has no row back | **27 (55 %)** `[calc]` |
| Rows on `carrier/**` and `cluster/**` pages using a machine-readable peer | **0 of 48** `[calc]` |
| Nets whose two ends disagree on **peer** | 5 nets, 11 rows |
| Nets whose two ends disagree on **direction** | 2 nets |
| Nets whose two ends disagree on **name** | 6 nets |
| Rows that are not a crossing net at all | **26** (every `Dir` = `—` row) + 4 more `[calc]` |
| Distinct `Dir` values in use | **7**: `in` 51, `out` 44, `ref` 24, `—` 26, `in/out` 4, `internal` 2, `panel` 2 `[calc]` |
| Peer notations in use | **4 incompatible forms** + prose |
| Restated quantities in rows that also cite the owning figure | 11 rows |
| Figure ids cited that do not resolve | **0** — all 27 cited ids exist in `config/figures.yaml` `[calc]` |

The last row is the one good result: **not one broken figure citation in 158
rows.** That half of the discipline held completely. Everything else below is
about the half that did not.

---

## The defects, by net

### N1 — `DAC AVDD` / `AVDD` / `LM317 rail` / `buffered +5.21 V`: one net, four names, wrong peer at the source

**Severity: high. This is a netlist defect, not a documentation one.**

`[repo] hardware/module/power-entry/power-entry.md:25`

```
| `DAC AVDD` | out | `module/digital-and-supervision` | `dac-rail` | The LM317 output…
```

The consumer is not `digital-and-supervision`. It is `dac8568`, which the DAC
was split into earlier the same day `[repo]
hardware/module/dac8568/dac8568.md:3-6`:

`[repo] hardware/module/dac8568/dac8568.md:20` — `| `AVDD` | in | `module/power-entry` | `dac-rail` | …`

`digital-and-supervision`'s table has **no `AVDD` row at all** `[repo]
hardware/module/digital-and-supervision/digital-and-supervision.md:22-28`. So
the source names a circuit that does not receive it, and the actual receiver's
row has no reciprocal.

Two further consumers of the same LM317 rail name `module/power-entry` as peer
and appear nowhere in `power-entry`'s row:

- `[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:28` —
  `| LM317 rail | in | `module/power-entry` | `dac-rail` |`
- `[repo] hardware/module/breath-output-stage/breath-output-stage.md:22` —
  `| buffered +5.21 V | in | `module/power-entry` | `dac-rail` |`

Four names for one node — `DAC AVDD`, `AVDD`, `LM317 rail`, `buffered
+5.21 V` — across four tables, all four citing `dac-rail`. A transcription that
keys on the Node cell produces four nets. `[calc]` The drawing that owns it
labels it a fifth way: `DAC AVDD 5.21V` `[repo]
hardware/module/power-entry/power-entry.md:44`.

### N2 — `bus +5V`: the two ends name mutually exclusive sources

**Severity: high.**

`[repo] hardware/module/power-entry/power-entry.md:26`

```
| bus `+5V` after `FB4`/`C4` | out | `module/digital-and-supervision` | — | The level shifter only…
```

and the drawing confirms it: `+5V ├───[FB4]──[C4 47µF]──── 74AHCT125 only`
`[repo] hardware/module/power-entry/power-entry.md:83`.

Against that, both other tables that carry the net say it comes straight off
the rack:

- `[repo] hardware/module/digital-and-supervision/digital-and-supervision.md:27`
  — `| bus +5 V | in | Eurorack bus header | — | Supplies the 74AHCT125 and nothing else. Open`
- `[repo] hardware/interfaces/spi-link/spi-link.md:36` — the identical row.

These cannot both be the netlist. Either the 74AHCT125 hangs on `power-entry`'s
`FB4`/`C4` node or it hangs on the bus header; the tables assert both, on the
one rail the corpus already flags as having no reverse protection `[repo]
hardware/module/digital-and-supervision/digital-and-supervision.md:100-110`.
A netlist built from the tables gets two nets and no DRC will say which.

### N3 — `VREFOUT`, `DAC ch1`, `DAC ch2`–`ch5`, `DAC ch7`, `CLR`: five rows still point at the pre-split page

**Severity: high. Already propagated into the dependency graph.**

`dac8568` names its consumers correctly `[repo]
hardware/module/dac8568/dac8568.md:22-24`:

```
| `VREFOUT` | out | `module/pitch-stage` |
| `DAC ch1` | out | `module/pitch-stage` |
| `DAC ch7` | out | `module/mod-channels` |
```

The consumers all name `module/digital-and-supervision` instead:

- `[repo] hardware/module/pitch-stage/pitch-stage.md:19` — `| `VREFOUT` | in | `module/digital-and-supervision` |`
- `[repo] hardware/module/pitch-stage/pitch-stage.md:20` — `| `DAC ch1` | in | `module/digital-and-supervision` |`
- `[repo] hardware/module/mod-channels/mod-channels.md:26` — `| `DAC ch7` | in | `module/digital-and-supervision` |`
- `[repo] hardware/module/mod-channels/mod-channels.md:27` — `| `DAC ch2`–`ch5` | in | `module/digital-and-supervision` |`
- `[repo] hardware/module/mod-channels/mod-channels.md:28` — `| `CLR` | in | `module/digital-and-supervision` |`

`digital-and-supervision`'s table carries **no `VREFOUT`, no `DAC ch*` and no
`CLR` row** `[repo]
hardware/module/digital-and-supervision/digital-and-supervision.md:22-28`. All
five edges dangle.

**This has already been consumed.** `circuit.yaml` for both pages declares
`circuit:module/digital-and-supervision` and **no** `circuit:module/dac8568`
`[repo] hardware/module/pitch-stage/circuit.yaml:66`, `[repo]
hardware/module/mod-channels/circuit.yaml:60`, while `dac8568` declares edges
to both `[repo] hardware/module/dac8568/circuit.yaml:56-57`. The graph's own
header states the seeding source: *"circuit: edges were seeded from the
Interfaces tables' Peer column"* `[repo]
hardware/module/dac8568/circuit.yaml:13-14`. The table error is the graph
error.

### N4 — `DAC ch2`–`ch5`: consumed by a table, driven by none

**Severity: medium.** `mod-channels` receives four signal channels `[repo]
hardware/module/mod-channels/mod-channels.md:27`, and the drawing shows them
`[repo] hardware/module/mod-channels/mod-channels.md:42,45` (`DAC ch2`, and
`ch3, ch4, ch5`). `dac8568`'s table lists only `ch1` and `ch7` as outputs
`[repo] hardware/module/dac8568/dac8568.md:23-24`. Four crossing nets have no
row at the source. This is audit question 2 in its purest form: a net that
leaves a circuit and appears in no Interfaces row of that circuit.

### N5 — `CLR`: correct at one pair, wrong at three other rows

`[repo] hardware/module/link-supervision/link-supervision.md:25` (`out` →
`module/dac8568`) and `[repo] hardware/module/dac8568/dac8568.md:21` (`in` ←
`module/link-supervision`) **agree** — same name, opposite directions,
reciprocal peers. That pair is correct.

Three other rows send `CLR` to `digital-and-supervision`, which has no `CLR`
row:

- `[repo] hardware/module/mod-channels/mod-channels.md:28`
- `[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:27`
- `[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:32`

The last two are rows whose own Note says **"Reaches no part of this circuit"**
— i.e. a row asserting an edge to a circuit, in order to say there is no edge.
A mechanical reader gets the edge and not the negation. See F3.

### N6 — `OE` ×4: `out` at one end, `ref` at the other, and a name collision across boards

**Severity: medium (direction), high (collision).**

- `[repo] hardware/module/link-supervision/link-supervision.md:26` — `| `OE` ×4 | **out** | `module/digital-and-supervision` |`
- `[repo] hardware/module/digital-and-supervision/digital-and-supervision.md:28` — `| `OE` ×4 | **ref** | `module/link-supervision` |`
- `[repo] hardware/interfaces/spi-link/spi-link.md:37` — `| `OE` ×4 | **ref** | `module/link-supervision` |`

`ref` is not the opposite of `out`. Both notes say the pin is tied to `GND` and
the driver is not fitted, so `ref` is arguably the truthful one and
`link-supervision`'s `out` is a claim about a circuit that does not exist — but
as written the pair is inconsistent whichever reading you take.

**The collision:** `OE` ×4 also names a different physical net on the *carrier*
— the other 74AHCT125 — with no qualifier: `[repo]
hardware/carrier/led-strip-drive/led-strip-drive.md:23` `| `OE` ×4 | — | tied
LOW |`. Three tables, two boards, two parts, one net name. This is the same
failure class `docs/reference/pcb-pipeline.md` records for `AGND` and `BREATH`
`[repo] docs/reference/pcb-pipeline.md:58-63` and **nobody has flagged it**.
It happens to be benign only because both ends tie to ground.

### N7 — `SCLK` / `MOSI` / `CS` across the umbilical: the reciprocal names a board, not a circuit

`[repo] hardware/interfaces/spi-link/spi-link.md:30-32` gives the carrier side
as `HDR-DEV IO35/IO36/IO34 → `74AHCT125``. The module side `[repo]
hardware/module/digital-and-supervision/digital-and-supervision.md:22-24` gives
the peer as **`carrier` via the umbilical**.

`carrier` is a board directory. It is not a circuit id, not a file, and not the
interface circuit that now owns the crossing. The edge
`digital-and-supervision → interfaces/spi-link` therefore does not exist in the
graph in either direction, for the three nets the umbilical is mainly for. Same
for `DIG_GND` `[repo]
hardware/module/digital-and-supervision/digital-and-supervision.md:25` and for
`breath pair` `[repo]
hardware/module/link-supervision/link-supervision.md:27`.

### N8 — `SCLK` vs `SCK`, and two nets called `CS` on the carrier

The drawing `spi-link`'s row transcribes says **`SCK`**, not `SCLK`: `[repo]
hardware/carrier/carrier.md:213` — `IO35 SCK ──[R-SPI-SER 100R]─── J-UMB pin 4`.
The table says `SCLK` `[repo] hardware/interfaces/spi-link/spi-link.md:30`.
`SCK` is also the *chain* clock name, at `J-CHAIN` pin 2, IO38 `[repo]
hardware/interfaces/key-chain-loom/key-chain-loom.md:23` and `[repo]
hardware/cluster/key-register/key-register.md:13`. A transcription off the
drawings merges the umbilical SPI clock with the key-scan clock.

Likewise the same drawing carries **two nets named `CS`** — `IO34 CS` to
`J-UMB` pin 7 and `IO39 CS` to the MCP3202 `[repo]
hardware/carrier/carrier.md:215,219`. The tables disambiguate them only by a
parenthetical: `` `CS` (IO39) `` `[repo]
hardware/carrier/breath-adc/breath-adc.md:25` versus `` `CS` (`J-UMB` pin 7) ``
`[repo] hardware/interfaces/spi-link/spi-link.md:32` — but
`digital-and-supervision` then drops the qualifier entirely and writes plain
`CS` `[repo]
hardware/module/digital-and-supervision/digital-and-supervision.md:24`. **Add
`CS` to the collision list in `pcb-pipeline.md` §1.**

### N9 — `MISO` / `DOUT`: same conductor, two names, one-sided

`[repo] hardware/interfaces/spi-link/spi-link.md:34` — `| `MISO` | — |
`carrier/breath-adc` | … IO37 is the MCP3202's `DOUT` |`. `breath-adc` calls it
`DOUT` `[repo] hardware/carrier/breath-adc/breath-adc.md:24` and names no peer
but `HDR-DEV`. The drawing writes both: `IO37 MISO ── MCP3202 DOUT only`
`[repo] hardware/carrier/carrier.md:219`.

### N10 — `UMBILICAL +12V` / `J-UMB` pin 3, and `PWR_GND` / `J-UMB` pin 6: the power umbilical has no interface page and no matching names

`[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:15` —
`| `UMBILICAL +12V` | out | **the instrument, down the Cat5 umbilical** |`

`[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md:12` —
`| `J-UMB` pin 3 `+12V` | in | **the module, down the umbilical** |`

Different net name at each end, prose peer at each end. Mechanically
unlinkable. Same for `PWR_GND` `[repo]
hardware/module/power-entry/power-entry.md:29` vs `` `J-UMB` pin 6 `PWR_GND` ``
`[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md:13`.

**Structural note.** Three board-crossing blocks got an interface directory
`[repo] hardware/interfaces/README.md:3-12`, and the power pair (`J-UMB` pins
3 and 6) is not one of them — so the highest-current crossing in the project
is the one with no page holding both ends and no reconciled net name. That may
be deliberate, but it is the reason N10 exists.

### N11 — `MODULE ANALOG ±12V`: the source's consumer list is short by one circuit

`[repo] hardware/module/power-entry/power-entry.md:23-24` lists four analog
pages: `pitch-stage`, `breath-receive-stage`, `breath-output-stage`,
`mod-channels`. `breath-response-shaper` draws `±12 V` from the same place
`[repo] hardware/module/breath-response-shaper/breath-response-shaper.md:22` —
`| ±12 V | in | `module/power-entry` | … `U-RESP`'s two halves — the last two
on the module |` — and is not in the list. The shaper is *proposed*, which
excuses the omission only if the list says so; it does not.

Consumers also rename it: the source says `MODULE ANALOG +12V` / `−12V`,
consumers say `±12 V`, `±12 V`, `±12 V`, and `breath-output-stage` carries
**both** a `−12 V` row and a `±12 V` row for the same supply pair `[repo]
hardware/module/breath-output-stage/breath-output-stage.md:23-24`.

Separately, `power-entry` has a distinct row `` `+12 V analog` `` for
`panel-led` `[repo] hardware/module/power-entry/power-entry.md:28`, and
`panel-led` reciprocates with the same name `[repo]
hardware/module/panel-led/panel-led.md:13`. Whether `+12 V analog` is the same
node as `MODULE ANALOG +12V` is not stated in either row, and `panel-led`'s own
Note says only *"The rail it comes from is the analog one"*. **Two rows in one
table, possibly for one net.**

### N12 — `in-amp output` and `V_shaped`: the shaper's two edges are both one-sided

`in-amp output` reciprocates cleanly between `breath-receive-stage` (`out`) and
`breath-output-stage` (`in`) `[repo]
hardware/module/breath-receive-stage/breath-receive-stage.md:26`, `[repo]
hardware/module/breath-output-stage/breath-output-stage.md:21` — **correct
pair**. But `breath-response-shaper` also takes it `[repo]
hardware/module/breath-response-shaper/breath-response-shaper.md:20` and
`breath-receive-stage` does not list the shaper. And `V_shaped` leaves the
shaper toward `breath-output-stage` `[repo]
hardware/module/breath-response-shaper/breath-response-shaper.md:21` while
`breath-output-stage` has no `V_shaped` row — it mentions the shaper only in a
Note `[repo] hardware/module/breath-output-stage/breath-output-stage.md:21`.
A proposed insertion is exactly the case where both ends must say so.

### N13 — `panel LED` and `+12 V, umbilical side`: `link-supervision`'s two remaining edges

`[repo] hardware/module/link-supervision/link-supervision.md:29` — `| panel LED
| out | `module/panel-led` |`. `panel-led`'s table has no row naming
`link-supervision` `[repo] hardware/module/panel-led/panel-led.md:13-16`.

`[repo] hardware/module/link-supervision/link-supervision.md:28` — `| +12 V,
umbilical side | in | `module/power-entry` | … downstream of the module's own
load switch |`. By its own Note the node is downstream of the load switch, so
the peer is `module/umbilical-load-switch`, not `module/power-entry`, and
neither of those tables names `link-supervision`.

### N14 — `SER` and `QH` on the chain: the two ends cite different figures and tell different stories

`[repo] hardware/cluster/key-register/key-register.md:15` — `| `SER` | in | **the
next board's `QH`, or the carrier through `LK-SER`** | `chain-connectors` |`

`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:25` — `| `SER`
(`J-CHAIN` pin 6) | out | `HDR-DEV` IO33 → **the far device, through `LK-SER`**
| `chain-conductors` | The one pass-through: it rides every hop to the
chain-end board's serial input |`

One says the register's `SER` comes from its neighbour's `QH`; the other says
pin 6 is a carrier-driven pass-through to the chain-end board. Both may be
describing different halves of the same arrangement, but as two rows about one
pin they contradict, and they cite **different figures for the same net**
(`chain-connectors` vs `chain-conductors`). `QH` does the same: `[repo]
hardware/cluster/key-register/key-register.md:16` cites `chain-connectors`,
`[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:26` cites
`chain-conductors`, `marker-bits`, `free-bits`.

`3V3` is a third instance: `key-register` cites **no figure** `[repo]
hardware/cluster/key-register/key-register.md:18` while `key-switch-network`
`[repo] hardware/cluster/key-switch-network/key-switch-network.md:13` and
`key-chain-loom` `[repo]
hardware/interfaces/key-chain-loom/key-chain-loom.md:28` both cite
`key-pullup-qty` for the same rail.

### N15 — `VS` excitation: correct directions, incompatible peer notation

`[repo]
hardware/carrier/breath-excitation-reference/breath-excitation-reference.md:17`
— `| `VS` | out | `U-BREATH`'s excitation pin, drawn in [`carrier.md`](../carrier.md) §2 |`

`[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:25` — `| `VS`
excitation | instrument | in | `carrier/breath-excitation-reference` |`

Directions are opposite and correct. But one end names a refdes and a board
page section, the other names a circuit id — so the edge exists in one
direction only, mechanically. Same shape for `buffered sensor output` `[repo]
hardware/carrier/breath-adc/breath-adc.md:22` vs `[repo]
hardware/interfaces/breath-sense-link/breath-sense-link.md:26`.

---

## F1 — Question 6: the `AGND` and `BREATH` collisions are **not** fixed. They are reproduced.

`docs/reference/pcb-pipeline.md` §1 is explicit `[repo]
docs/reference/pcb-pipeline.md:58-63`:

> `AGND` means the umbilical sense conductor *and* the module analog return.
> `BREATH` means the in-amp input *and* the output jack. … A transcription
> taking names off the drawings shorts the breath in-amp input to the breath
> output jack.

**`breath-sense-link.md` handles this correctly and completely.** Its preamble
names both collisions, explains the `End` column as the remedy, and both rows
carry an explicit "**Not** the module's …" `[repo]
hardware/interfaces/breath-sense-link/breath-sense-link.md:20-22,27-28`. That
is the model.

**`breath-receive-stage.md` handles it partly** — it carries both `AGND` rows
and qualifies the second as `AGND (module)` `[repo]
hardware/module/breath-receive-stage/breath-receive-stage.md:23,29` — but its
`BREATH` row `[repo]
hardware/module/breath-receive-stage/breath-receive-stage.md:22` carries **no
warning that the module's output jack is also called `BREATH`**.

**Every other table propagates the ambiguity.** Tallies `[calc]`:

| | Tables |
|---|---|
| `AGND` written bare, meaning the **module analog star** | `dac8568`, `mod-channels`, `pitch-stage`, `breath-response-shaper`, `power-entry` — **5** |
| `AGND` qualified `AGND (module)` | `breath-output-stage`, `breath-receive-stage`, `breath-sense-link` — 3 |
| `AGND` meaning the **umbilical sense leg** | `breath-receive-stage`, `breath-sense-link` — 2 |
| A **third** name, `AGND-local`, for the *carrier* analog star | `breath-adc`, `breath-excitation-reference` — 2 |
| `BREATH` written bare, meaning the **output jack** | `breath-output-stage` `[repo] hardware/module/breath-output-stage/breath-output-stage.md:26` |
| `BREATH` written bare, meaning the **umbilical conductor** | `breath-receive-stage` |

So the corpus now has **three** spellings of the analog return (`AGND`, `AGND
(module)`, `AGND-local`) and the collision survives in the five tables a
transcription would read first. The `End` column — the mechanism the
`interfaces/README.md` says exists for exactly this `[repo]
hardware/interfaces/README.md:30-32` — exists on 3 of 22 tables and not on any
module page.

`carrier.md` itself is clean on this: it writes `AGND-local` for the star and
`J-UMB pin 2 AGND` for the leg `[repo] hardware/carrier/carrier.md:99,134`. The
tables did not inherit that discipline.

**Add `OE` (N6) and `CS` (N8) to `pcb-pipeline.md` §1's collision list.** Both
are net-name collisions between two boards, neither is recorded there.

---

## F2 — Question 5: four incompatible peer notations, and what it costs

`[calc]`, from parsing all 158 Peer cells:

| Form | Example | Used by |
|---|---|---|
| **A. Bare circuit id** `` `board/circuit` `` | `` `module/power-entry` `` | all 11 module pages, all 3 interfaces pages |
| **B. Markdown link, label = circuit name** | ``[`power-entry-instrument`](../power-entry-instrument/power-entry-instrument.md)`` | all 5 carrier pages |
| **C. Markdown link, label = relative path** | ``[`../key-register/key-register.md`](../key-register/key-register.md)`` | all 3 cluster pages |
| **D. File + section** | `` `carrier/carrier.md` §2 ``, `` `carrier/carrier.md` component table `` | breath-sense-link, spi-link, key-chain-loom |
| **E. Prose / refdes / nothing** | "the dev board's LDO", "panel jack", "chain bus", "the two WS2815 strips", "tied LOW", "unconnected", `PANEL`, `—` | everywhere |

**What it costs, measured.** Of 158 rows, **49 peer edges are machine-readable**
(form A). Of the 48 rows on `carrier/**` and `cluster/**` pages, **zero** are
`[calc]`. The consequence is already recorded inside the repository, by whoever
built the graph:

> *circuit: edges were seeded from the Interfaces tables' Peer column, and the
> agents that wrote those tables did not agree on notation. … So `carrier/**`
> and `cluster/**` declare **ZERO** circuit: edges while `module/power-entry`
> declares seven. That is a property of the tables, not of the hardware.*
> `[repo] hardware/module/dac8568/circuit.yaml:13-20`

That note diagnoses the notation split. **It does not record the second half,
which is that 27 of the 49 edges that *are* machine-readable are one-sided**
`[calc]` — and many of those (N1, N3, N5, N13) are not notation at all. They
are the wrong peer.

**The 11 edges that do reciprocate**, for the record `[calc]`:
`dac8568↔digital-and-supervision`, `dac8568↔link-supervision`,
`digital-and-supervision↔link-supervision`,
`power-entry↔umbilical-load-switch`, `power-entry↔pitch-stage`,
`power-entry↔mod-channels`, `power-entry↔breath-output-stage`,
`power-entry↔breath-receive-stage`, `power-entry↔panel-led`,
`panel-led↔umbilical-load-switch`, `breath-receive-stage↔breath-output-stage`.

Two further peers can **never** reciprocate, by design: `module/panel` carries
no table `[repo] hardware/module/panel/panel.md:3` yet is named as a peer twice
`[repo] hardware/module/breath-output-stage/breath-output-stage.md:27`, `[repo]
hardware/module/breath-response-shaper/breath-response-shaper.md:24`; and
`carrier/carrier.md`, `cluster/cluster-boards.md` and `config/key-layout.yaml`
are named as peers but are not circuits. That is not wrong — but it means a
graph reader must special-case them, and no row marks them as a different kind
of thing.

**Related gap.** Three `breath-sense-link` rows peer to
`` `carrier/carrier.md` component table `` `[repo]
hardware/interfaces/breath-sense-link/breath-sense-link.md:23,24,29` because
`U-BREATH`, `R1`/`R1b` and `D-TVS-BREATH` belong to **no carrier circuit
directory**. The instrument-side breath front end is the one block in the
corpus that the restructure left without a circuit of its own. Worth a decision
before the netlist stage, not a correction now.

---

## F3 — Question 3 and 7: `Dir` has seven values, three of which are not directions, and 30 rows are not crossing nets

Every table's preamble says the same thing `[repo, all 22 files]`:

> Every net that crosses this circuit's boundary.

**26 rows have `Dir` = `—`** `[calc]`, and most of them are not crossing nets:

- **Not connected at all.** `` | `EN`, `IO0` | — | **not wired** | `` `[repo]
  hardware/carrier/display-and-service-uart/display-and-service-uart.md:27`;
  `| CH1 | — | unconnected |` `[repo]
  hardware/carrier/breath-adc/breath-adc.md:27`; `| two spare conductors | — |
  — |` `[repo]
  hardware/carrier/display-and-service-uart/display-and-service-uart.md:26`;
  `| spare ×2 (pins 11, 12) | — | — |` `[repo]
  hardware/interfaces/key-chain-loom/key-chain-loom.md:29`.
- **Internal, by the row's own admission.** `` | REF5050 `VOUT` | **internal** |
  — | `` and `| op-amp output | **internal** | — |` `[repo]
  hardware/carrier/breath-excitation-reference/breath-excitation-reference.md:15-16`.
  `internal` is used on exactly one page, and contradicts the preamble two
  lines above it. Also `` | `LDAC` | ref | — | `R-LDAC`, a 0 Ω strap to `GND` ``
  `[repo] hardware/module/dac8568/dac8568.md:22`, `` | `FB1`–`FB4` | — | — | ``
  `[repo] hardware/module/power-entry/power-entry.md:31`, and `` | `OE` ×4 | —
  | tied LOW | `` `[repo]
  hardware/carrier/led-strip-drive/led-strip-drive.md:23`.
- **Parts, not nets.** `breath-sense-link` has **4 of 13** rows that are
  component lists — `` `R1`, `R1b` ``, `` `U-BREATH` ``, `` `D-TVS-BREATH` ×2 ``,
  `` `R2`, `R3`, `C_diff`, `C_cm` ×2, `R4`, `R5` `` `[repo]
  hardware/interfaces/breath-sense-link/breath-sense-link.md:23,24,29,30`.
  `key-chain-loom` has 4 of 11 `[repo]
  hardware/interfaces/key-chain-loom/key-chain-loom.md:30-33`, including
  `| the 32 bits |` — a concept. `spi-link` has `` `U-TVS-SPI` `` and `SPI2
  host` `[repo] hardware/interfaces/spi-link/spi-link.md:33,35`.
  `breath-receive-stage` has 2 `[repo]
  hardware/module/breath-receive-stage/breath-receive-stage.md:24-25`. The two
  6-column tables' header even says `Node / part`, which is honest — but it
  means the table is two data types in one relation, and a netlist
  transcription must know which rows to skip and has no column telling it.
- **Mechanical.** `| panel cutout | — | `PANEL` | `panel-height-budget` |`
  `[repo] hardware/module/panel-led/panel-led.md:15`. A refdes as a peer, a
  panel aperture as a node.
- **An entire table of nets that do not exist.** All five
  `link-supervision` rows are marked "**Not fitted.**" `[repo]
  hardware/module/link-supervision/link-supervision.md:25-29`. Its preamble is
  honest about it — *"Every net that would cross this circuit's boundary **if it
  were fitted**"* `[repo]
  hardware/module/link-supervision/link-supervision.md:18-19` — but the
  qualification is in prose, not in any column, so the graph seeded from the
  Peer column got 5 edges to an unfitted circuit and `dac8568`,
  `digital-and-supervision` and `spi-link` all carry reciprocal rows to it
  `[repo] hardware/module/dac8568/circuit.yaml:57`.

**`Dir` = `panel`** on two rows `[repo]
hardware/module/breath-output-stage/breath-output-stage.md:27`, `[repo]
hardware/module/breath-response-shaper/breath-response-shaper.md:24`. That is a
peer kind, not a direction. Meanwhile the three panel *jacks* use `out` with
peer "panel jack" `[repo]
hardware/module/breath-output-stage/breath-output-stage.md:26`, `[repo]
hardware/module/mod-channels/mod-channels.md:29`, `[repo]
hardware/module/pitch-stage/pitch-stage.md:21` — so within `module/**` the
panel is reached two different ways, with two different peer forms, in tables
written by the same convention.

**`Dir` = `in/out`** on 4 rows, all carrier `[calc]` — and 3 of the 4 are also
**multi-net rows**: `` | SPI2 `SCLK`, `MOSI`, `DOUT` | in/out | `` `[repo]
hardware/carrier/breath-adc/breath-adc.md:24` packs three nets with three
different directions into one row. `` | IO5, IO6 | `` and `` | `U0TXD` (IO43),
`U0RXD` (IO44) | `` do the same `[repo]
hardware/carrier/display-and-service-uart/display-and-service-uart.md:22-23`.
Question 7 asks whether direction is meaningful for a shared net: here it is
not even resolvable, because the row is not one net.

**`Dir` = `out` used with two different reference frames, inside one table.**
In `breath-sense-link`, `` `BREATH` (`J-UMB` pin 1) | instrument → module | out ``
`[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:27` means
*along the cable, away from the instrument* — `BREATH` is the link's own
conductor and crosses nothing. Six rows later, `| in-amp output | module | out
| `module/breath-output-stage` |` `[repo]
hardware/interfaces/breath-sense-link/breath-sense-link.md:31` means *out of
this circuit*. Same column, same table, two meanings. `key-chain-loom` is the
same: `SCK` is `out` and `QH` is `in`, both relative to the **carrier**, not to
the loom `[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:23,26` —
while `| bus +5 V | module | in |` in `spi-link` is relative to the circuit
`[repo] hardware/interfaces/spi-link/spi-link.md:36`. For a cable, "in" and
"out" of the cable are not defined, and the three interface tables each
resolved that differently.

One further one-sided-by-construction row: `| the serial bit stream | out | the
carrier, through the chain |` `[repo]
hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:15`.
`key-marker-and-bits` has no connection to the chain — its straps land on
`key-register`'s parallel inputs, as its own first two rows say. The bit stream
leaves `key-register`'s `QH`, not this circuit. **Question 3: a row for
something the circuit does not connect to.**

---

## F4 — Question 4: the quantity rule, and where it is broken

All 22 preambles say `[repo, all 22 files]`:

> Quantities appear **only** as a citation into `config/figures.yaml` — this
> table names nodes, it does not restate values.

**All 27 distinct figure ids cited across the 158 rows resolve against
`config/figures.yaml`** `[calc]` — zero broken citations. Against that, the
restatements:

**Q1 — the clear violation.** `[repo]
hardware/module/breath-output-stage/breath-output-stage.md:22`:

```
| buffered +5.21 V | in | `module/power-entry` | `dac-rail` | …
```

`dac-rail`'s value is `5.21 V`, owner `hardware/module/power-entry/power-entry.md`
`[repo] config/figures.yaml`. The row **cites the figure and restates its value
in the same row**, in the Node cell — i.e. the value has become part of a net
name. If `dac-rail` moves, this is a stale net identifier, and CLAUDE.md §2's
grep-for-the-old-value step has to find `+5.21 V` spelled with a leading plus
inside a table cell between pipes — the exact spelling class that cost eleven
live statements the last time `[repo] CLAUDE.md:33-39`.

**Q2 — `chain-connectors` restated.** `[repo]
hardware/interfaces/key-chain-loom/key-chain-loom.md:26`: *"That is what makes
the chain **eight** connectors rather than five"*. `chain-connectors` = `8`,
owned by this very file `[repo] config/figures.yaml`. Owner may state it — but
it is stated in a row that cites three *other* figures, while the row that
cites `chain-connectors` is a different one `[repo]
hardware/interfaces/key-chain-loom/key-chain-loom.md:31`.

**Q3 — `umbilical-pinmap` restated eight times.** The figure's value **is** the
pin map: `1,2 BREATH/AGND | 3,6 +12V/PWR_GND | 4,5 SCLK/MOSI | 7,8 CS/DIG_GND`
`[repo] config/figures.yaml`. Eight rows cite it *and* write the pin number
into the Node cell:

| Row | File |
|---|---|
| `` `BREATH` (`J-UMB` pin 1) ``, `` `AGND` (`J-UMB` pin 2) `` | `[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:27-28` |
| `` `J-UMB` pin 3 `+12V` ``, `` `J-UMB` pin 6 `PWR_GND` `` | `[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md:12-13` |
| `` `SCLK` (`J-UMB` pin 4) ``, `` `MOSI` (pin 5) ``, `` `CS` (pin 7) ``, `` `DIG_GND` (pin 8) `` | `[repo] hardware/interfaces/spi-link/spi-link.md:30-32` |

**I verified all eight against the figure and all eight are currently correct**
`[calc]`. That is the point: this is the shape the recorded failure takes
*before* it fails. The pin number is arguably node identity rather than a
quantity — but if so, the tables should say so, because as written eight rows
duplicate a tracked figure's entire content.

**Q4 — `chain-conductors` restated as a layout.** `chain-conductors` = `12`.
`key-chain-loom` writes out all twelve positions — `pin 2`, `pin 4`, `pin 6`,
`pin 8`, `GND ×5 (pins 1, 3, 5, 7, 9)`, `pin 10`, `spare ×2 (pins 11, 12)` —
and adds *"free in a **2×6**"* `[repo]
hardware/interfaces/key-chain-loom/key-chain-loom.md:23-29`. `2×6 = 12`
`[calc]`. `key-register` and `key-switch-network` each restate *"five
alternating grounds"* and *"pin 10"* `[repo]
hardware/cluster/key-register/key-register.md:18-19`, `[repo]
hardware/cluster/key-switch-network/key-switch-network.md:13,16`.

**Q5 — a component value in a Node/Note cell, no figure at all.** `` `R1` and
the `2 × 10 k` divider that makes `V_in/2` `` and *"The `2 × 10 k` divider's
bottom leg"* `[repo]
hardware/module/breath-response-shaper/breath-response-shaper.md:20,23`. `10 k`
is not in `config/figures.yaml`, so this is not a citation failure — it is the
preamble's own "does not restate values" broken outright, twice in one table.

**Q6 — arithmetic restatements of tracked figures.** `marker-bits` = `8 bits`;
`key-marker-and-bits` writes *"two per device, one high and one low"* across 4
devices `[repo]
hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:13` — `4 × 2 = 8`
`[calc]`. `key-chain-loom` writes *"the 32 bits"* and *"the whole 32-bit
word"* `[repo] hardware/interfaces/key-chain-loom/key-chain-loom.md:24,33`;
32 is not itself tracked but is the sum of `marker-bits`, `free-bits` and the
switch allocation.

**Q7 — smaller, in Note cells.** *"16-pin shrouded keyed IDC"* `[repo]
hardware/module/power-entry/power-entry.md:22`; *"three of `HDR-SERVICE`'s six
pins"*, `GND ×2` `[repo]
hardware/carrier/display-and-service-uart/display-and-service-uart.md:24-25`;
*"four `VCC` pins and four decouplers"* `[repo]
hardware/interfaces/key-chain-loom/key-chain-loom.md:28`.

**Not counted as violations**, for the record: rail names (`+12V`, `−12 V`,
`3V3`, `5 V`, `±12 V`) and GPIO numbers (`IO34`–`IO40`, `IO1`, `IO2`, `IO5`,
`IO6`, `IO43`, `IO44`). These are net identity, not derived quantities, and no
figure owns them. But **note that no figure owns the ESP32 pin assignment
either**, so the ~15 GPIO numbers scattered across five tables are an untracked
shared fact with no single owner — a register entry waiting to be needed.

---

## F5 — Duplicated rows: `spi-link` and `digital-and-supervision` both claim to drive the DAC

**Severity: high, and distinct from N1–N3.**

Three rows are **byte-identical** between two tables `[calc]`:

| Row | |
|---|---|
| `` `SCLK`, `DIN`, `SYNC` | out | `module/dac8568` | — | Buffer outputs. The DAC-side three of the six `R-SPI-PULL` sit on these `` | `[repo] hardware/interfaces/spi-link/spi-link.md:35` and `[repo] hardware/module/digital-and-supervision/digital-and-supervision.md:26` |
| `bus +5 V \| in \| Eurorack bus header` | both files |
| `` `OE` ×4 \| ref \| `module/link-supervision` `` | both files |

The 74AHCT125 is on `digital-and-supervision` — its drawing has the part and
the six pulls `[repo]
hardware/module/digital-and-supervision/digital-and-supervision.md:52-58`, and
`spi-link.md`'s own status line says *"The SPI receive side that feeds this
part — the 74AHCT125 and the six pulls — is still on that page"* `[repo]
hardware/module/dac8568/dac8568.md:5-6`. So `spi-link` lists three nets that do
not cross **its** boundary; they are entirely inside `digital-and-supervision`.

Consequence: **`module/dac8568`'s `SCLK`/`DIN`/`SYNC` input has two declared
drivers.** A netlist assembled from the Peer column gets two sources on one
net. This is question 1's "`out` in one table and `out` in another" — not for
the same edge, but for the same *destination*, which is the same short.

---

## What is right, and should not be touched

Recording these so the next reviewer does not re-open them, and because the
cold-wave rule is that a finding filed as handled is worse than a wrong one
`[repo] CLAUDE.md:113-118`:

1. **All 27 figure ids cited across 158 rows resolve.** Zero broken citations
   `[calc]`. Whatever else the eight agents disagreed on, none of them invented
   a figure.
2. **`breath-sense-link.md`'s treatment of the `AGND`/`BREATH` collision is
   correct and complete** — preamble, `End` column, and an explicit "**Not**
   the module's …" on both rows `[repo]
   hardware/interfaces/breath-sense-link/breath-sense-link.md:20-22,27-28`. It
   is the only table in the corpus that discharges `pcb-pipeline.md` §1. It
   should be the template, not an exception.
3. **`CLR` between `link-supervision` and `dac8568`** is a correct pair: same
   name, opposite directions, reciprocal peers `[repo]
   hardware/module/link-supervision/link-supervision.md:25`, `[repo]
   hardware/module/dac8568/dac8568.md:21`.
4. **`+12V` ahead of `D1`/`D2`** between `power-entry` and
   `umbilical-load-switch` is the cleanest pair in the corpus — identical node
   string, `out`/`in`, reciprocal peers, and it matches the drawing `[repo]
   hardware/module/power-entry/power-entry.md:27`, `[repo]
   hardware/module/umbilical-load-switch/umbilical-load-switch.md:13`, `[repo]
   hardware/module/power-entry/power-entry.md:57-77`.
5. **`link-supervision`'s preamble is honest** about listing nets that would
   exist if fitted `[repo]
   hardware/module/link-supervision/link-supervision.md:18-19`. The defect is
   that the honesty is in prose the graph cannot read, not that it is absent.
6. **`panel.md` correctly has no table** and says why `[repo]
   hardware/module/panel/panel.md:3`.
7. **`carrier.md` itself does not have the `AGND` collision** — it writes
   `AGND-local` for the star `[repo] hardware/carrier/carrier.md:99,122`.

---

## Two notes for whoever fixes this

**Do not fix these one table at a time.** Every defect above is one net seen
from two sides, and 27 of the 49 machine-readable edges are one-sided. Fixing
the side you are looking at produces the failure CLAUDE.md opens with `[repo]
CLAUDE.md:8-12`. The unit of repair is the net, and the check is: *does the row
at the other end now say the same net name, the opposite direction, and this
circuit's id?*

**The tables' value is entirely in being mechanical, and four of the five
columns currently are not.** `Node` mixes nets with parts with concepts;
`Dir` has seven values, three of which are not directions, and two reference
frames; `Peer` has four notations plus prose; `Figure` is the only column that
holds — and it holds *perfectly*. That is not a coincidence. `Figure` is the
column with an external register that something resolves against `[repo]
CLAUDE.md:30-31`. The other four have nothing to resolve against, and they have
drifted in exactly the way the unresolved columns of this repository always
drift.

