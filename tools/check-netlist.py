#!/usr/bin/env python3
"""Prove each circuit's netlist against the BOM and against its own drawing.

WHY THIS EXISTS. An ASCII drawing is a picture. No tool in this repository
could read one, so nothing checked that a value in a drawing matched the BOM
row for the same refdes - and a 2026-09-22 review found four that did not:

    R-FB        drawn 40k     BOM 40.2k   (and 40k is not an E96 value)
    C1          drawn 47uF    BOM 100uF   (on the +12 V rail, so half)
    R-LED-SER   drawn 220R    BOM 330R
    N-FET       drawn nameless, BOM Q-LOADSW

Every one of those is a one-line diff against a netlist, and none of them was
reachable before. The netlist is AUTHORITATIVE; the drawing is a
representation of it (hardware/README.md says so, and ROADMAP tracks the
rollout).

WHAT IT CHECKS, per circuit that has a netlist.yaml:

    bom        every refdes exists in hardware/bom.csv, and its `value`
               matches that row
    nets       every net has at least two endpoints, unless it is declared
               in external_endpoints
    pins       every declared pin is used exactly once; no net references a
               pin a component does not declare
    drawing    every `[REFDES value]` label in the page's ASCII drawing names
               a component in the netlist AND agrees with it
    ports      every port is used by a net, and every net port is declared

A circuit with no netlist.yaml is REPORTED, NOT FAILED, while the rollout is
in progress - the count of pages still without one is printed on every run so
it cannot quietly stall. `--strict` turns that into a failure once the
rollout is done.

Usage:  python3 tools/check-netlist.py [--strict] [<circuit-dir> ...]
Exit:   0 clean, 1 problems
"""
import csv, os, re, sys, glob

try:
    import yaml
except ImportError:
    sys.exit("check-netlist.py needs PyYAML")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOX = set("│┬┴├┤┼└┘┌┐─►")
# `[R-FB 40.2k]` / `[FB1]` / `[D1 1N5817]` - a bracketed label in a drawing.
#
# THE SECOND CHARACTER MAY BE A HYPHEN, and the first version of this regex
# said `[A-Z][A-Z0-9][A-Z0-9-]*`, which requires it not to be. THIS REPO'S
# REFDES CONVENTION IS X-NAME: R-FB, D-JACK-CLAMP, C-OUT-BREATH, U-LOADSW. So
# the pattern matched POT-GAIN and POT-OFFSET and essentially nothing else -
# 2 labels out of 10 on the pilot page - and the checker reported 0 problems
# on a drawing with a deliberately injected R-FB 40k in it. A fail-open in the
# tool written to close fail-opens, caught by testing it against the defect it
# exists for rather than by reading it.
LABEL = re.compile(r"\[([A-Z][A-Z0-9-]*[A-Z0-9])\s*([^\]]*)\]")


def bom_rows():
    p = os.path.join(ROOT, "hardware/bom.csv")
    with open(p, newline="", encoding="utf-8") as fh:
        return {r["ref"]: r for r in csv.DictReader(fh)}


def drawing_labels(page_path):
    """Every [REFDES value] sitting inside an ASCII drawing on that page.

    A FENCED BLOCK CONTAINING BOX CHARACTERS IS A DRAWING, and every line in
    it counts. Judging line by line on a box-character threshold missed the
    parts drawn on their own - `[D-JACK-CLAMP BAV99]` has two box characters
    and `[R-OUT-PROT 1k, 1206]` has none, because they hang off a rail rather
    than sitting in it. Those are exactly the rows a stuffing list gets wrong.
    """
    out = []
    try:
        lines = open(page_path, encoding="utf-8").read().split("\n")
    except OSError:
        return out
    # First pass: which fenced blocks are drawings?
    fence, start, blocks = False, 0, []
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            if fence:
                blocks.append((start, n))
            fence, start = not fence, n
    drawing = set()
    for a, b in blocks:
        body = lines[a:b - 1]
        if sum(sum(ch in BOX for ch in L) for L in body) >= 3:
            drawing.update(range(a + 1, b))
    for n, line in enumerate(lines, 1):
        if n not in drawing and sum(ch in BOX for ch in line) < 3:
            continue
        for ref, val in LABEL.findall(line):
            out.append((n, ref, val.strip()))
    return out


def norm(v):
    """Compare values the way a human does: case and spacing are noise."""
    return re.sub(r"\s+", "", (v or "").lower()).rstrip(",")


VALTOK = re.compile(r"\d+(?:\.\d+)?\s*[a-zA-Z%\u03a9\u00b5]*")


def value_tokens(v):
    """The magnitudes in a value string, normalised.

    A DRAWING LABEL MAY SAY LESS THAN THE BOM, NEVER SOMETHING DIFFERENT.
    `[R-OUT-PROT 1k 500mW]` is a fair abbreviation of `1k 1%, >=500mW` - a
    drawing cannot carry the full part string without pushing every column to
    its right. But `[R-FB 40k]` against `40.2k 1%` is a contradiction, and it
    is the one that reached a review: 40k is not an E96 value, so a layout
    taken off that drawing orders a part nobody sells.

    So the test is SUBSET, not equality and not substring: every magnitude the
    drawing states must appear in the netlist's value.
    """
    return {norm(m) for m in VALTOK.findall(v or "") if any(c.isdigit() for c in m)}


def check_one(d, bom, problems):
    rel = os.path.relpath(d, ROOT)
    spec = yaml.safe_load(open(os.path.join(d, "netlist.yaml"), encoding="utf-8"))
    comps = spec.get("components") or {}
    nets = spec.get("nets") or {}
    ports = spec.get("ports") or {}
    external = set(spec.get("external_endpoints") or [])

    # --- refdes and value against the BOM
    for ref, c in comps.items():
        row_ref = c.get("of", ref)        # a section names its package
        if row_ref not in bom:
            problems.append(f"{rel}: {ref} is in no bom.csv row "
                            f"(looked for {row_ref!r})")
            continue
        if "value" in c and norm(c["value"]) not in norm(bom[row_ref]["part"]):
            problems.append(f"{rel}: {ref} value {c['value']!r} does not appear "
                            f"in its BOM part field {bom[row_ref]['part']!r}")

    # --- nets: endpoints, and pins that exist
    declared_pins = {(r, str(p)) for r, c in comps.items()
                     for p in (c.get("pins") or [])}
    used = []
    for net, eps in nets.items():
        if net not in external and len(eps) < 2:
            problems.append(f"{rel}: net {net!r} has {len(eps)} endpoint(s); "
                            f"a net needs two or must be in external_endpoints")
        for ep in eps:
            if isinstance(ep, dict):
                pn = ep.get("port")
                if pn and pn not in ports:
                    problems.append(f"{rel}: net {net!r} uses undeclared port {pn!r}")
                continue
            if "." not in ep:
                problems.append(f"{rel}: net {net!r} endpoint {ep!r} is not REF.PIN")
                continue
            ref, pin = ep.rsplit(".", 1)
            if ref not in comps:
                problems.append(f"{rel}: net {net!r} references unknown component {ref!r}")
            elif (ref, pin) not in declared_pins:
                problems.append(f"{rel}: {ref} has no pin {pin!r} "
                                f"(declares {comps[ref].get('pins')})")
            used.append((ref, pin))

    for rp in sorted(declared_pins - set(used)):
        problems.append(f"{rel}: {rp[0]}.{rp[1]} is declared and connected to nothing")
    for rp in sorted({u for u in used if used.count(u) > 1}):
        problems.append(f"{rel}: {rp[0]}.{rp[1]} appears in more than one net")

    for pn in ports:
        if not any(isinstance(e, dict) and e.get("port") == pn
                   for eps in nets.values() for e in eps):
            problems.append(f"{rel}: port {pn!r} is declared and used by no net")

    # --- THE ONE THAT CATCHES THE RECORDED DEFECTS: drawing vs netlist
    #
    # `drawn_as` is how a drawing's local label is reconciled with the BOM
    # refdes. A drawing says [R-FB 40.2k] because the full name would push
    # every column to its right, and widening a label inside a drawing is
    # itself a recorded defect on five pages. Declaring the alias HERE - in
    # the authoritative file - is better than the prose table it replaces,
    # because the checker can enforce it.
    alias = {c["drawn_as"]: ref for ref, c in comps.items() if c.get("drawn_as")}
    page = os.path.join(d, spec.get("page") or "")
    for lineno, ref, val in drawing_labels(page):
        ref = alias.get(ref, ref)
        if ref not in comps:
            if ref in bom or any(c.get("of") == ref for c in comps.values()):
                continue                  # a package or a shorthand, not a net node
            problems.append(f"{rel}: drawing line {lineno} labels {ref!r}, "
                            f"which is not in this netlist")
            continue
        want = comps[ref].get("value")
        if want and val:
            extra = value_tokens(val) - value_tokens(want)
            if extra:
                problems.append(f"{rel}: drawing line {lineno} shows {ref} as {val!r}, "
                                f"which the netlist's {want!r} does not support "
                                f"({', '.join(sorted(extra))})")
    return len(comps), len(nets)


def main():
    strict = "--strict" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    dirs = sorted({os.path.dirname(p) for p in
                   glob.glob(os.path.join(ROOT, "hardware/**/netlist.yaml"),
                             recursive=True)})
    if args:
        dirs = [d for d in dirs if any(a.rstrip("/") in d for a in args)]

    # Pages that carry a drawing and have no netlist yet - the rollout's
    # denominator, printed every run so it cannot stall unnoticed.
    pending = []
    for page in glob.glob(os.path.join(ROOT, "hardware/**/*.md"), recursive=True):
        if os.path.basename(page) in ("README.md", "notes.md"):
            continue
        if not drawing_labels(page):
            continue
        if not os.path.exists(os.path.join(os.path.dirname(page), "netlist.yaml")):
            pending.append(os.path.relpath(page, ROOT))

    bom = bom_rows()
    problems, comps, nets = [], 0, 0
    for d in dirs:
        c, n = check_one(d, bom, problems)
        comps += c
        nets += n

    for p in problems:
        print("  " + p)
    print(f"netlist: {len(dirs)} circuit(s), {comps} components, {nets} nets | "
          f"{len(problems)} problem(s) | {len(pending)} drawing page(s) still "
          f"without a netlist")
    if pending and not args:
        for p in sorted(pending):
            print(f"    pending: {p}")
    return 1 if problems or (strict and pending) else 0


if __name__ == "__main__":
    sys.exit(main())
