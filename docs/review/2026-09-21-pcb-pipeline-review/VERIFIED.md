# VERIFIED — what was checked by hand, and where an agent was wrong

Findings are claims. This file records which ones were re-checked independently
of the agent that filed them, and what the re-check found.

---

## P2 — no headless netlist import exists

**Claim:** there is no way, in any KiCad version or interface, to import a
netlist into a board headless. `NETLIST`, `NETLIST_READER`, `PCB_NETLIST` and
`BOARD_NETLIST_UPDATER` are absent from the SWIG bindings; `kicad-cli pcb` has
no import verb; the IPC API needs a running KiCad.

**Re-checked independently, 2026-09-21. CONFIRMED.**

```
$ curl .../kicad/-/raw/9.0.9/pcbnew/python/swig/pcbnew.i   → 153 lines, no match for NETLIST
$ curl .../kicad/-/raw/9.0.9/pcbnew/python/swig/board.i    → 202 lines, no match for NETLIST
$ grep -oE 'CLI::PCB_[A-Z_]+' kicad/kicad_cli.cpp @ 9.0.9
    PCB_DRC_COMMAND  PCB_RENDER_COMMAND
    PCB_EXPORT_{DRILL,DXF,GENCAD,GERBER,GERBERS,IPC*,ODB,PDF,POS,SVG}_COMMAND
```

No import verb, no update verb. **This is a real hole in the pipeline as
written**, and it invalidates the unstated assumption in stage 3 that a
generated netlist lands in a board by itself.

**Also confirmed:** `skidl==2.3.0` hard-depends on `kinet2pcb>=1.1.4`
(`Requires-Dist: kinet2pcb>=1.1.4` in the sdist's `PKG-INFO` *and*
`setup.py`), which is the proposed route around the hole. Not yet tested
end to end — only the dependency is established.

**Noted while verifying, outside P2's slice:** `kicad-cli pcb export` offers
**`odb`** and **`ipc2581`** alongside gerbers. Neither appears in the plan.
Flagged for P7.

---

## Still to verify

Everything else. The wave is in flight; this file gets one section per report
as each is re-checked.

---

## P1 — not one `kicad-cli` line in the plan would parse

**Claim:** `input` is a *positional* argument with no default, so every command
in the plan — all six — fails with "Too few arguments" before doing anything.

**Re-checked, 2026-09-21. CONFIRMED.** `kicad/cli/command.cpp:124-133` @ 9.0:

```cpp
m_argParser.add_argument( ARG_INPUT )
        .help( UTF8STDSTR( _( "Input file" ) ) )
        .metavar( "INPUT_FILE" );
```

No `--` prefix, no `.default_value()`. Positional and required.

Not re-checked but carried: `--units mm` on `export drill` is really
`--excellon-units`; `--severity-error` *narrows* the report and drops every
warning from `--exit-code-violations`, which is a silent wrong-green; the
OpenGL paragraph is false for KiCad 9 because `pcb render` is a CPU raytracer;
and "library tables need a GUI first" is refuted — `kicad-cli` creates them
itself under `KFCTL_CLI`.

## P10 — the copper arithmetic was wrong and the conclusion inverted

**Claim:** "0.5 mm of 1 oz copper is roughly a 1 A trace at a 10 °C rise …
that is no margin" is wrong; IPC-2221 gives **1.447 A**.

**Re-checked by doing the arithmetic, 2026-09-21. CONFIRMED.**
IPC-2221 external, `I = k·ΔT^0.44·A^0.725`, k = 0.048, 1 oz = 1.378 mil:

| width | area | current at 10 °C |
|---|---|---|
| 0.25 mm | 13.56 mil² | **0.875 A** |
| 0.30 mm | 16.28 mil² | 0.999 A |
| 0.50 mm | 27.13 mil² | **1.447 A** |

Against a limit of `47 mV / 50 mΩ` = **0.940 A**, 0.5 mm has ~54 % margin. The
plan said the opposite.

**And the same table refutes the plan a second way, which P10 did not say:**
the plan's `Default` signal class at **0.25 mm is 0.875 A**, *below* the
0.940 A limit. So the advice "derive the power width, don't default it" was
right — but for the opposite reason. The power class is fine and it is the
*default* class that would be marginal if it ever carried fault current.

**Also confirmed by P10 and accepted without re-check:** "1.0 A" is stale —
`power-entry.md` opens with "the limit is 0.940 A, not 1.0 A". The plan copied
a superseded figure from ADR 0005, twice.

## P5 — SKiDL survives, three of the plan's claims about it do not

Not independently re-checked; P5 ran real circuits in a clean venv with no
KiCad, which is stronger evidence than re-reading source. Accepted as filed.

The architecture holds: SKiDL works with **no KiCad installed**, parses
**KiCad 9** symbol libraries, and ad-hoc parts need no library at all.

Three plan claims refuted: "fail the build on any ERC error" **does not
happen** — SKiDL exits 0 with errors and writes the netlist anyway;
`generate_schematic()` **does** exist, so "you lose `--schematic-parity`" is
out of date (though its output is non-deterministic and cannot be the parity
artifact); and `check-bom-parity.py` "diffs by refdes" is **impossible** —
`bom.csv` is role-keyed, and 61 rows are 149 physical parts.
