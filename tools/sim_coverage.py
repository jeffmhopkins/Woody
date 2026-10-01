#!/usr/bin/env python3
"""Which circuits are simulated, and is the record of it true?

    python3 tools/sim_coverage.py        # exit 1 and say why if the coverage table is wrong

The register is the table under "Coverage - every circuit and board" in
docs/reference/tooling.md section 5: one row per circuit with parts and per board,
`own` (it has a sim/), `covered` (naming the sim/ directories that cover it, and what)
or `n/a` (and why). This reads it against the tree: a circuit whose netlist.yaml has a
part, or a board, with no row fails; so does an `own` row with no sim/, a `covered` row
naming no existing sim/, an `n/a` row with no reason, a row whose circuit has since grown
its own sim/, and a row for a circuit that does not exist. check-staleness.py runs it.

It is not part of tools/sim.py on purpose: sim.py hashes itself into every results.yaml,
so a change here would make every simulation stale for nothing.
"""
import glob
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COVERAGE_DOC = os.path.join(ROOT, "docs", "reference", "tooling.md")
COVERAGE_HEAD = "### Coverage — every circuit and board"


def coverage_rows():
    """{name: (kind, text)} from the coverage table in docs/reference/tooling.md section 5:
    the record of which circuits and boards have their own sim/, which another sim covers
    (and which), and which have nothing to simulate. The page is the register; this reads it."""
    text = open(COVERAGE_DOC).read()
    if COVERAGE_HEAD not in text:
        return None
    rows = {}
    for line in text.split(COVERAGE_HEAD, 1)[1].splitlines():
        if line.startswith("#"):
            break
        m = re.match(r"\|\s*`([^`]+)`\s*\|\s*(own|covered|n/a)\s*\|(.*)\|\s*$", line)
        if m:
            rows[m.group(1)] = (m.group(2), m.group(3).strip())
    return rows


def coverage_subjects():
    """{name: dir} for every circuit whose exported netlist has a part, and every board."""
    out = {}
    for p in glob.glob(os.path.join(ROOT, "hardware", "**", "netlist.yaml"), recursive=True):
        doc = yaml.safe_load(open(p)) or {}
        if doc.get("components") and doc.get("circuit"):
            out[doc["circuit"]] = os.path.dirname(p)
    for p in glob.glob(os.path.join(ROOT, "hardware", "boards", "*", "board-netlist.yaml")):
        d = os.path.dirname(p)
        out["boards/" + os.path.basename(d)] = d
    return out


def check_coverage():
    """Every circuit with parts, and every board, has a row in the coverage table, and the
    row is true: `own` has a sim/, `covered` names existing sim/ directories, and a circuit
    with its own sim/ is not recorded as covered elsewhere or as having nothing to simulate."""
    rows = coverage_rows()
    rel = lambda p: os.path.relpath(p, ROOT)
    if rows is None:
        return [f"{rel(COVERAGE_DOC)} has no '{COVERAGE_HEAD}' table - the register of what is simulated"]
    problems = []
    subjects = coverage_subjects()
    for name, d in sorted(subjects.items()):
        own = os.path.exists(os.path.join(d, "sim", "sims.yaml"))
        if name not in rows:
            problems.append(f"coverage: {name} has parts and no row in {rel(COVERAGE_DOC)} "
                            f"'{COVERAGE_HEAD}' - give it a sim/, or say what covers it or why nothing need")
            continue
        kind, text = rows[name]
        if kind == "own" and not own:
            problems.append(f"coverage: {name} is recorded 'own' and {rel(d)}/sim/sims.yaml does not exist")
        if kind != "own" and own:
            problems.append(f"coverage: {name} has its own sim/ but is recorded '{kind}' - make the row 'own'")
        if kind == "covered":
            named = re.findall(r"`(hardware/[^`]*?/sim)/?`", text)
            if not named:
                problems.append(f"coverage: {name} is recorded 'covered' and names no `hardware/.../sim/` directory")
            for s in named:
                if not os.path.exists(os.path.join(ROOT, s, "sims.yaml")):
                    problems.append(f"coverage: {name} is recorded covered by {s}/, which has no sims.yaml")
        if kind == "n/a" and not text:
            problems.append(f"coverage: {name} is recorded 'n/a' and does not say why")
    circuit_ids = {os.path.relpath(os.path.dirname(p), os.path.join(ROOT, "hardware"))
                   for p in glob.glob(os.path.join(ROOT, "hardware", "**", "circuit.yaml"), recursive=True)}
    for name in sorted(set(rows) - set(subjects) - circuit_ids):
        problems.append(f"coverage: the table has a row for {name}, which is no circuit or board")
    return problems


def main():
    problems = check_coverage()
    for p in problems:
        print("  " + p)
    n = len(coverage_subjects())
    print(f"sim coverage: {'FAIL' if problems else 'PASS'} - {n} circuits and boards with parts, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
