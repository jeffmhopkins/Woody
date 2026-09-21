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

`hardware/unplaced.csv` holds the BOM rows **no schematic page names**. That
is a count, not a dumping ground: a part nobody has drawn. Two of its clusters
name circuits this corpus has no page for — six identical jack-protection
networks drawn three times, and nineteen decoupling capacitors with no home.

Drawings that span more than one circuit were **left whole** rather than
redrawn, and the circuits cite them. `carrier.md`'s §2 figure carries three
circuits in one connected picture; dividing it would mean redrawing it, and a
redraw is not a move.
