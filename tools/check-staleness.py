#!/usr/bin/env python3
"""
Mechanical staleness check for the Woody design corpus.

Three review waves found the same defect ~90 times: a value changes and the
numbers derived from it elsewhere do not follow. This catches the numeric half
mechanically, so it does not depend on anyone remembering.

It cannot catch the semantic half - prose that still DEPENDS on a deleted part,
or an argument that survives its own refutation. That needs a reader. Run the
staleness-sweep agents at gates for those.

Usage:  python3 tools/check-staleness.py [--verbose]
Exit:   0 clean, 1 defects found
"""
import csv, os, re, sys, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERBOSE = "--verbose" in sys.argv
# Terse by default: this runs from a PreToolUse hook on every commit, and a
# 60-line dump on every invocation is a real cost. Detail goes to a file.
DETAIL = "--detail" in sys.argv or VERBOSE
os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".staleness"), exist_ok=True)
REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      ".staleness/report.txt")

# The design corpus must be self-consistent. Review/log/research are dated
# historical records and are deliberately excluded - a 2026-09-21 review saying
# "8HP" is CORRECT as a record of what was true when it was written.
CORPUS_DIRS = ["hardware", "docs/decisions", "docs/reference", "config", "firmware"]
CORPUS_FILES = ["README.md", "ROADMAP.md"]
EXCLUDE = ("docs/review", "docs/log", "docs/research")

# A forbidden value on a line that also refutes it is fine - that is how a
# correction is supposed to read. Only unqualified survivals are failures.
REFUTATION = re.compile(
    r"\b(was|were|previously|prior|stale|supersed\w+|withdrawn|refuted?|refutes|"
    r"no longer|used to|earlier|old|former\w*|instead of|rather than|wrong|"
    r"incorrect|corrected|deleted|obsolete|historical|until \d{4}|"
    r"this (row|line|page|ADR|file) (said|carried|read)|carried a superseded)\b",
    re.I)


def corpus_files():
    out = []
    for f in CORPUS_FILES:
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            out.append(p)
    for d in CORPUS_DIRS:
        for dirpath, _, names in os.walk(os.path.join(ROOT, d)):
            rel = os.path.relpath(dirpath, ROOT)
            if any(rel.startswith(x) for x in EXCLUDE):
                continue
            for n in names:
                if n.endswith((".md", ".csv", ".yaml", ".yml")):
                    out.append(os.path.join(dirpath, n))
    return sorted(set(out))


def check_figures(files):
    spec = yaml.safe_load(open(os.path.join(ROOT, "config/figures.yaml")))
    live, refuted = [], []
    for fig in spec["figures"]:
        for bad in fig.get("forbidden") or []:
            for path in files:
                rel = os.path.relpath(path, ROOT)
                if rel == "config/figures.yaml":
                    continue
                try:
                    lines = open(path, encoding="utf-8").read().splitlines()
                except Exception:
                    continue
                # Match against a line-JOINED stream, not line by line. The
                # corpus is hard-wrapped at ~78 columns, so a forbidden phrase
                # that straddles a line break was invisible - and one was:
                # "six conductors leave" wrapped across 0001:369-370 while
                # sitting in its own forbidden list, and the checker passed.
                #
                # Lines are joined with ONE space and their internal spacing is
                # left alone, because several forbidden patterns are code-block
                # spellings containing runs of spaces ("SCLK      / MOSI").
                buf, lineof = [], []
                for i, line in enumerate(lines, 1):
                    s = line.strip()
                    if buf:
                        buf.append(" ")
                        lineof.append(i)
                    for ch in s:
                        buf.append(ch)
                        lineof.append(i)
                text = "".join(buf)

                start = 0
                while True:
                    at = text.find(bad, start)
                    if at < 0:
                        break
                    start = at + 1
                    first = lineof[at]
                    last = lineof[min(at + len(bad) - 1, len(lineof) - 1)]
                    # Judge refutation on every line the match touches, so a
                    # correction written above or below a wrapped phrase counts.
                    ctx = " ".join(lines[first - 1:last])
                    rec = (fig["id"], fig.get("value"), bad, rel, first,
                           ctx.strip()[:100])
                    (refuted if REFUTATION.search(ctx) else live).append(rec)
    return live, refuted, spec


def check_bom():
    path = os.path.join(ROOT, "hardware/bom.csv")
    rows = list(csv.reader(open(path, newline="", encoding="utf-8")))
    hdr, n, problems = rows[0], len(rows[0]), []
    seen = {}
    for idx, r in enumerate(rows[1:], 2):
        if len(r) != n:
            problems.append(f"bom.csv:{idx} has {len(r)} columns, expected {n}")
        if r and r[0] in seen:
            problems.append(f"bom.csv:{idx} duplicate refdes {r[0]} (also line {seen[r[0]]})")
        elif r:
            seen[r[0]] = idx
    return problems, set(seen), n, len(rows) - 1


def check_refdes(files, bom_refs):
    """Reference designators drawn in a schematic with no BOM row."""
    pat = re.compile(r"\b([A-Z]{1,4}[0-9]?-[A-Z0-9-]{2,})\b")
    drawn, missing = {}, []
    for path in files:
        rel = os.path.relpath(path, ROOT)
        if not rel.startswith("hardware/") or rel.endswith(".csv"):
            continue
        text = open(path, encoding="utf-8").read()
        for m in pat.finditer(text):
            tok = m.group(1)
            drawn.setdefault(tok, set()).add(rel)
    for tok, where in sorted(drawn.items()):
        if tok in bom_refs:
            continue
        base = tok.split("/")[0]
        if base in bom_refs or any(tok.startswith(b + "-") for b in bom_refs):
            continue
        missing.append((tok, sorted(where)))
    return missing


def emit(lines, detail_only=False):
    """Collect for the report file; print only if detail was asked for."""
    REPORT_LINES.extend(lines)
    if DETAIL or not detail_only:
        for l in lines:
            print(l)


REPORT_LINES = []


def main():
    files = corpus_files()
    live, refuted, spec = check_figures(files)
    bom_problems, bom_refs, ncols, nrows = check_bom()

    emit([f"corpus: {len(files)} files | bom.csv: {nrows} rows x {ncols} cols | "
          f"figures tracked: {len(spec['figures'])}", ""], detail_only=True)

    fail = False

    if live:
        fail = True
        body = [f"STALE VALUES STILL LIVE ({len(live)})",
                "  A value this quantity no longer has, on a line that does not refute it.", ""]
        cur = None
        for fid, val, bad, rel, ln, txt in sorted(live):
            if fid != cur:
                body.append(f"  [{fid}] is now: {val}")
                cur = fid
            body.append(f"      {rel}:{ln}  found {bad!r}")
            if VERBOSE:
                body.append(f"          {txt}")
        body.append("")
        emit(body, detail_only=True)

    if bom_problems:
        fail = True
        emit([f"BOM INTEGRITY ({len(bom_problems)})"] + ["  " + p for p in bom_problems] + [""],
             detail_only=True)

    unresolved = [f for f in spec["figures"] if f["status"] in ("disputed", "blocked")]
    if unresolved:
        body = [f"UNRESOLVED, tracked deliberately ({len(unresolved)}) - not failures"]
        for f in unresolved:
            body.append(f"  [{f['status']:8s}] {f['id']}: {f['quantity']}")
            body.append(f"             decided by: {f.get('decided_by','-')}")
        body.append("")
        emit(body, detail_only=True)

    if refuted:
        body = [f"old values present but refuted in place ({len(refuted)}) - OK, this is how a correction reads"]
        if VERBOSE:
            body += [f"  {rel}:{ln}  [{fid}] {bad!r}" for fid, val, bad, rel, ln, txt in sorted(refuted)]
        body.append("")
        emit(body, detail_only=True)

    try:
        with open(REPORT, "w") as fh:
            fh.write("\n".join(REPORT_LINES) + "\n")
    except Exception:
        pass

    # The one line that always prints.
    n_unres = len(unresolved)
    if fail:
        print(f"FAIL {len(live)} stale + {len(bom_problems)} bom | {n_unres} unresolved (tracked) "
              f"| detail: .staleness/report.txt or --detail")
    else:
        print(f"PASS no live stale values | {n_unres} unresolved (tracked)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
