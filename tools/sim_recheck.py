#!/usr/bin/env python3
"""Every results.yaml re-checked against its own numbers (no ngspice).

    python3 tools/sim_recheck.py          # every sim dir; exit 1 on a problem

`tools/sim.py check` proves a results.yaml's INPUTS have not moved (it hashes them)
and reads each assertion's recorded `pass:`. Neither covers the results body, so
two hand edits went straight through it and through the commit gate (issue #9,
G5, verified by mutation): a measure's `nom` set to -999, and an assert's `expr`
replaced with `True`. This asks what check does not:

- the recorded sims, measures and assert list are exactly sims.yaml's (expanded
  over its `sweep:`s);
- every assert in sims.yaml, evaluated again on the recorded min / nominal / max
  in the same environment `sim.py run` gives it, agrees with the recorded `pass:`.

And one thing `run` itself never asked (G6): a `post:` measure pinned to a
constant of its own definition measures nothing. `trough(v, cross(v, v_on + 1),
t_end)` can never read above v_on + 1, so an assert that it stays above
v_on + 0.5 passes by construction (power-entry-instrument's `v_buck_dip`, since
replaced). Each call's arguments are taken in the domain the call reads them in -
a `cross`/`backswing` LEVEL is in the measure's units, a window edge is in the
x-axis's (time, frequency) - and a measure is compared only with the constants of
its own domain: a value with the levels, an `argpeak`/`cross` result with the
window edges. A measure whose recorded min or max sits on one (to 1e-4) is a
PROBLEM when an assert reads it, and a NOTE otherwise (a frequency peak at its
window's edge says the window missed the peak; nobody may be relying on it).

It is a separate tool, not part of `sim.py check`, ON PURPOSE: sim.py hashes
itself into every results.yaml, so any edit to it marks all of them stale until
every sim is re-run. This file is not a sim input, and changing it changes no
result.
"""
import ast
import functools
import math
import os
import re
import sys
from collections import Counter

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402

ROOT = sim.ROOT
# config/figures.yaml is parsed afresh on every call (45 times in one pass, two thirds
# of this tool's run time); it cannot change during one run, so read it once
sim.figures = functools.lru_cache(maxsize=None)(sim.figures)

# where each POST function reads its numeric arguments: "x" is the x axis (a
# time or frequency window), "v" the waveform's own units; index 0 is the wave
ARG_DOMAIN = {
    "peak": {1: "x", 2: "x"}, "trough": {1: "x", 2: "x"}, "argpeak": {1: "x", 2: "x"},
    "cross": {1: "v", 2: "x"}, "backswing": {1: "v", 3: "x", 4: "x"},
    "at": {1: "x"}, "overshoot": {1: "x", 2: "x"}, "rebound": {1: "x", 2: "x"},
    "settling": {1: "x", 2: "x"},
}
RETURNS_X = {"argpeak", "cross"}


def _const(node, p):
    """The value of a sub-expression that reads no waveform, or None."""
    if any(isinstance(x, ast.Name) and x.id == "w" for x in ast.walk(node)):
        return None
    try:
        v = eval(compile(ast.Expression(node), "<post>", "eval"), {"__builtins__": {}},
                 {"p": p, "math": math, "abs": abs})
    except Exception:       # noqa: BLE001 - not a number, so not a constant
        return None
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v != 0 else None


def pinned_constants(expr, p):
    """The constants a post: measure could be pinned to, in the measure's own domain."""
    try:
        tree = ast.parse(expr, mode="eval").body
    except SyntaxError:
        return []
    top = tree.func.id if isinstance(tree, ast.Call) and isinstance(tree.func, ast.Name) else None
    want = "x" if top in RETURNS_X else "v"
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ARG_DOMAIN:
            for i, arg in enumerate(node.args):
                if ARG_DOMAIN[node.func.id].get(i) == want:
                    c = _const(arg, p)
                    if c is not None:
                        out.append(c)
    return sorted(set(out))


def recheck(simdir, got):
    rel = os.path.relpath(simdir, ROOT)
    spec = sim.load(simdir)
    problems, notes = [], []
    parts, doc = sim.netlist_parts(spec)
    figs = {k: sim.figure_value(str(v["value"])) for k, v in sim.figures().items()
            if re.match(r"\s*-?\d", str(v["value"]))}
    p_nom = sim.derive(spec, sim.corners(spec, parts)[0][1])
    n = Counter(c.get("of", r.split(":", 1)[-1]) for r, c in doc["components"].items())
    recorded = got.get("sims") or {}
    wanted = sim.expand(spec["sims"])
    for name in sorted(set(recorded) - {s["name"] for s in wanted}):
        problems.append(f"{rel}: results.yaml records sim {name!r}, which sims.yaml does not define")
    for s in wanted:
        r = recorded.get(s["name"])
        if r is None:
            problems.append(f"{rel}: {s['name']} is in sims.yaml and not in results.yaml - python3 tools/sim.py run {rel}")
            continue
        ms = r.get("measures") or {}
        if sorted(ms) != sorted(s["measures"]):
            problems.append(f"{rel}: {s['name']} records measures {sorted(ms)}, sims.yaml asks for {sorted(s['measures'])}")
            continue
        want_a = [a["expr"] for a in s.get("asserts") or []]
        got_a = [a.get("expr") for a in r.get("asserts") or []]
        if want_a != got_a:
            problems.append(f"{rel}: {s['name']}: the recorded asserts are not sims.yaml's - results.yaml was "
                            f"edited, or sims.yaml changed without a run")
            continue
        env = {"nom": {m: v["nominal"] for m, v in ms.items()}, "min": {m: v["min"] for m, v in ms.items()},
               "max": {m: v["max"] for m, v in ms.items()}, "fig": figs, "n": n, "p": p_nom,
               "abs": abs, "math": math}
        for a, ra in zip(s.get("asserts") or [], r.get("asserts") or []):
            try:
                ok = bool(eval(a["expr"], {"__builtins__": {}}, env))
            except Exception as e:  # noqa: BLE001 - failing to evaluate is the finding
                problems.append(f"{rel}: {s['name']}: cannot evaluate {a['expr']!r} on the recorded numbers ({e})")
                continue
            if ok != bool(ra.get("pass")):
                problems.append(f"{rel}: {s['name']}: results.yaml says {a['expr']!r} "
                                f"{'passed' if ra.get('pass') else 'failed'}, but its own recorded numbers "
                                f"{'pass' if ok else 'fail'} it - the file was edited; re-run it")
        for m, expr in (s.get("post") or {}).items():
            got_m = ms.get(m) or {}
            hit = [c for c in pinned_constants(expr, p_nom) for k in ("min", "max")
                   if isinstance(got_m.get(k), (int, float)) and abs(got_m[k] - c) <= 1e-4 * abs(c)]
            if not hit:
                continue
            used = [a["expr"] for a in s.get("asserts") or []
                    if re.search(rf"\[['\"]{re.escape(m)}['\"]\]", a["expr"])]
            msg = (f"{rel}: {s['name']}: {m} = {got_m.get('min')}..{got_m.get('max')} sits on {hit[0]:g}, "
                   f"a constant of its own definition ({expr}), and can read nothing past it")
            if used:
                problems.append(msg + f" - asserted by {used[0]!r}, which therefore passes by construction")
            else:
                notes.append(msg + " (no assert reads it)")
    return problems, notes


def main():
    problems, notes = [], []
    dirs = sim.sim_dirs()
    for d in dirs:
        path = os.path.join(d, "results.yaml")
        if not os.path.exists(path):
            continue                    # sim.py check reports a sim never run
        try:
            pr, nt = recheck(d, yaml.safe_load(open(path)) or {})
        except SystemExit as e:
            pr, nt = [str(e)], []
        problems += pr
        notes += nt
    for p in problems:
        print("  " + p)
    for nt in notes:
        print("  note: " + nt)
    print(f"sim recheck: {'FAIL' if problems else 'PASS'} - {len(dirs)} sim dir(s), "
          f"{len(problems)} problem(s), {len(notes)} note(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
