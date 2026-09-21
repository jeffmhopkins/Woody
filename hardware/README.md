# hardware/ — how this directory is organised

One circuit per directory. The directory is the unit: the drawing, the parts,
the declared dependencies and the history of what the circuit *used to be* all
sit together, so a change and its record are never in different places.

```
<board>/<circuit>/<circuit>.md     the schematic: ASCII drawing, derivations,
                                   and an ## Interfaces table of every net
                                   that crosses the circuit's boundary
                  bom.csv          this circuit's parts. A FRAGMENT
                  circuit.yaml     declared dependencies. SEEDED, NOT VERIFIED
                  notes.md         past tense only. No live value belongs here
                  sim/             an ngspice deck and its contract. No results
```

| Directory | |
|---|---|
| [`carrier/`](carrier/carrier.md) | The instrument's real-time board — 5 circuits |
| [`cluster/`](cluster/cluster-boards.md) | Four identical key boards — 3 circuits |
| [`module/`](module/module.md) | The 10HP Eurorack module — 12 circuits |
| [`interfaces/`](interfaces/README.md) | The 3 circuits that cross a board boundary |

## The `## Interfaces` table

Every circuit page carries one: every net that crosses that circuit's
boundary, one row each. A PCB netlist is transcribed from these, so a row is
a wiring instruction and two pages disagreeing about a net is a short.

| Column | |
|---|---|
| **Node** | The net's name, **qualified** where the same bare name means different things on different boards. `AGND_SENSE`, `AGND_INST` and `AGND_MOD` are three nets; `AGND` alone is a merge waiting to happen. Each row names the drawing's own spelling so a reader can match the two. |
| **Dir** | This circuit's side of the net: `in`, `out`, `in/out`, `ref` (a return or a reference) or `—` (no connection here — the row is context). |
| **Peer** | A bare `board/circuit` id when the other end is a circuit in this tree, a reference designator or part name when it is not, `—` when there is nothing on the other end. |
| **Figure** | A citation into `config/figures.yaml`. The table names nodes; it **does not restate values.** |

**Exactly one page sources a net.** The page holding the part that drives it
says `out` and "Sourced here"; every other page says `in` and names it. Two
pages both claiming to source one net is the defect this column exists to
make visible — it happened to the DAC's `SCLK`/`DIN`/`SYNC`, in two
byte-identical rows.

The two board-crossing tables (`interfaces/breath-sense-link`,
`interfaces/spi-link`) carry an extra **End** column naming which side of the
cable a node sits on, because for those the board is not implied by the page.

*(This definition sat inline in all 23 circuit pages until 2026-09-21 —
twenty-three copies of one paragraph, in a repository whose first rule is
state it once and cite it. It is here, and they cite it.)*

## Two rules that will bite you

**`bom.csv` here is GENERATED.** `tools/merge-bom.py` rebuilds it from the
per-circuit fragments, so **a direct edit survives until the next run of that
tool and then disappears without a word.** Edit the fragment. A row lives with
the circuit **whose page derives its value** — not where it is mentioned, not
where it is mounted. `merge-bom.py --check` proves the master still matches
and the commit hook runs it, so this one fails loudly rather than silently.

**Numbers shared between documents are not written here.** They live in
`config/figures.yaml`, stated once by their owner and **cited by name**
everywhere else. This whole repository is organised around one recorded
failure — a value changes and the documents derived from it do not follow —
and citation is the only form that cannot go stale. `CLAUDE.md` has the rule
and the three-step procedure for changing a tracked figure.

## What is deliberately not here

`hardware/unplaced.csv` holds the BOM rows **no schematic page derives**.
That is a count, not a dumping ground: a part nobody has drawn.

It was 50 rows and is now 34. Sixteen of them were drawn all along — the
DAC, the in-amp, the LM317 and its divider, the entry diodes, the four
beads, the bulk capacitors, both load-switch capacitors, the module's level
shifter and the LT5400 — and were sitting in the undrawn pile because
assignment matched on **reference designator** while those parts are drawn
under a local label (`R1`, `C_cm`, `FB2`, `R_G`) or a part number
(`INA828`, `LM317LZ`, `DAC8568`). A count of undrawn parts that includes
every principal IC on a board is not a count of anything.

What remains is genuinely unplaced, and most of it is mechanical — the oak,
the acrylic, the adhesives, the fasteners — plus the parts whose circuit has
no page yet.

Drawings that span more than one circuit were **left whole** rather than
redrawn, and the circuits cite them. `carrier.md`'s §2 figure carries three
circuits in one connected picture; dividing it would mean redrawing it, and a
redraw is not a move.
