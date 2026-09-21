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
