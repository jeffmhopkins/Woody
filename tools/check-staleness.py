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

# THE CHECKER'S OWN BLIND SPOT, found 2026-09-21 and reproduced before fixing.
#
# os.walk() on a directory that does not exist yields nothing, silently. So
# CORPUS_DIRS naming a path that has been renamed or moved did not fail - it
# scanned fewer files and reported PASS. Measured: `mv docs/decisions docs/adr`
# took the corpus from 33 files to 18 and still printed
# "PASS no live stale values", exit 0, and the commit hook rendered green.
#
# That is this project's named failure mode committed by the one tool that
# exists to prevent it, during precisely the operation that triggers it - a
# restructure. A check that cannot assert its own inputs exist cannot assert
# anything about them.
#
# The floor is a tripwire, not a specification. Splitting files moves the count
# UP, so any real drop below it means the corpus definition and the tree have
# disagreed. Raise it when the tree grows; never lower it to make a run pass.
MIN_CORPUS_FILES = 30

# The two files this tool READS rather than scans. Moving either one raised a
# FileNotFoundError traceback and exit 0 - and the commit hook greps stdout for
# four anchored words, none of which a traceback contains, so it rendered
# "staleness: " with nothing after it. A crash must not read as silence.
TOOL_INPUTS = ["config/figures.yaml", "hardware/bom.csv"]

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


def check_corpus_shape(files):
    """Assert the corpus is where the corpus definition says it is.

    Every other check in this file is a statement about the files it was
    handed. None of them can tell that it was handed the wrong set.
    """
    problems = []
    for d in CORPUS_DIRS:
        p = os.path.join(ROOT, d)
        if not os.path.isdir(p):
            problems.append(f"CORPUS_DIRS names {d!r}, which is not a directory. "
                            f"Moved? Then move it here too, in the same commit")
        elif not any(os.path.relpath(f, ROOT).startswith(d + os.sep) for f in files):
            problems.append(f"CORPUS_DIRS names {d!r} and it contributed NO files")
    for f in CORPUS_FILES:
        if not os.path.exists(os.path.join(ROOT, f)):
            problems.append(f"CORPUS_FILES names {f!r}, which does not exist")
    for f in TOOL_INPUTS:
        if not os.path.exists(os.path.join(ROOT, f)):
            problems.append(f"this tool reads {f!r}, which does not exist. "
                            f"Update TOOL_INPUTS and every path that names it")
    if len(files) < MIN_CORPUS_FILES:
        problems.append(f"corpus is {len(files)} files, below the floor of "
                        f"{MIN_CORPUS_FILES}. Something moved out from under "
                        f"this tool; it is not scanning what you think it is")
    return problems


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


# Tokens that match the refdes SHAPE but are not refdes. Built by running the
# check and reading all 36 hits, not by imagining what might match - packages,
# part numbers, toolchains and hyphenated prose all look like `XX-NNN`.
# This list is why the check can be switched on at all: see check_refdes.
NOT_REFDES = re.compile(
    r"^(SOIC|SOT|TO|DO|SOD|SMA|SMB|QFN|TSSOP|MSOP|TQFP|DIP|SIP|MS8E?|PG|HP)-"
    r"|^(ESP|USB|RJ|CAT|IDC|LED|RTV|PWM|SPI|UART|GPIO|ADC|DAC|IMU|MIDI|WS|XL|MF|MI|HI)-"
    r"|^(KS|MX|RV|PJ|NE|SS|BAV|SP|LT|MPXV|REF|OPA|INA|LM|SN|MCP|ERA|SMAJ|PESD|USBLC)-?[0-9]"
    r"|^(PULL|PUSH|N|P)-(UP|DOWN|FET|CHANNEL)"
    r"|^R-78E"
    # CI-SN is the tail of the MCP3202-CI/SN order code; U-BOLT is prose
    # about a strap point, not a part reference.
    r"|^(CI-SN|U-BOLT)$"
    # SHA-256 is prose about banking a document, not a part.
    r"|^SHA-")


def check_refdes(files, bom_refs):
    """Reference designators drawn in a schematic with no BOM row.

    THIS WAS DEAD CODE until 2026-09-21 - defined here in full and never
    called from main(). Two cold agents found that independently, and the
    reason it was never switched on is measurable: run raw it yields 36 hits
    of which roughly 14 are not reference designators at all. An inferred
    dependency edge has a noise floor, and a check that cries wolf gets
    ignored or deleted.

    So it runs ADVISORY, never fatal, and filtered through NOT_REFDES. It is
    the one check here that reports a DEPENDENCY rather than a value, which
    is the half of this project's failure mode a grep cannot otherwise see.
    """
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
        if tok in bom_refs or NOT_REFDES.search(tok):
            continue
        base = tok.split("/")[0]
        if base in bom_refs or any(tok.startswith(b + "-") for b in bom_refs):
            continue
        # An abbreviation of a real row - C-GATE for C-GATE-LOADSW. Drawn
        # short, BOMmed long. Worth knowing about but not a missing part.
        if any(b.startswith(tok + "-") for b in bom_refs):
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


def check_links(files):
    """Markdown links in the corpus must resolve to a file that exists.

    Added 2026-09-21 during the restructure, after three links broke in a way
    nothing could see. They were written as bare filenames -
    `](breath-receive-stage.md)` - which resolved while the pages were
    siblings in one directory and stopped resolving the moment each page got
    its own. A bare filename is not a path token, so the path rewriter had
    nothing to match on and reported a clean run.

    This is the general form of that: do not check that known-old spellings
    are gone, check that what is written now RESOLVES. The first only knows
    about breakage you predicted.
    """
    pat = re.compile(r"\]\(([^)#\s]+\.md)[^)]*\)")
    problems = []
    for path in files:
        rel = os.path.relpath(path, ROOT)
        if not rel.endswith(".md"):
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except Exception:
            continue
        for m in pat.finditer(text):
            tgt = m.group(1)
            if tgt.startswith(("http://", "https://")):
                continue
            dest = os.path.normpath(os.path.join(os.path.dirname(path), tgt))
            if not os.path.exists(dest):
                line = text[:m.start()].count("\n") + 1
                problems.append(f"{rel}:{line} links to {tgt!r}, which does "
                                f"not resolve")
    return problems


def check_checks():
    """Every check in this file must actually be called.

    check_refdes() was defined here, fully written, and never called from
    main() - for the whole life of the tool. Two cold agents found it
    independently in one afternoon, and a third caught check_corpus_shape()
    in the same unwired state while it was being added. A check nobody wired
    up reads exactly like a check that passes.

    So the tool asserts its own wiring, and the assertion is four lines.
    """
    import inspect
    src = inspect.getsource(main)
    return [f"{n}() is defined and never called from main() - a check that "
            f"does not run reads exactly like one that passes"
            for n, f in sorted(globals().items())
            if n.startswith("check_") and n not in ("check_checks",)
            and callable(f) and (n + "(") not in src]


def main():
    files = corpus_files()

    # Before anything else. A shape problem makes every result below it a
    # statement about the wrong set of files, so it is reported first and it
    # is fatal on its own.
    shape_problems = check_corpus_shape(files)
    wiring_problems = check_checks()

    # If an input this tool READS is gone, the checks below raise rather than
    # report, and a traceback is invisible to the commit hook. Fail loudly in
    # the one format the hook can see, and stop.
    if any(os.sep.join(f.split("/")) in p or f in p
           for f in TOOL_INPUTS for p in shape_problems):
        for p in shape_problems:
            print("  " + p)
        print(f"FAIL {len(shape_problems)} shape | corpus {len(files)} files "
              f"| checks did not run")
        return 1

    live, refuted, spec = check_figures(files)
    bom_problems, bom_refs, ncols, nrows = check_bom()
    drawn_not_bommed = check_refdes(files, bom_refs)
    link_problems = check_links(files)

    emit([f"corpus: {len(files)} files | bom.csv: {nrows} rows x {ncols} cols | "
          f"figures tracked: {len(spec['figures'])}", ""], detail_only=True)

    fail = False

    if link_problems:
        fail = True
        emit([f"BROKEN LINKS ({len(link_problems)})"]
             + ["  " + p for p in link_problems] + [""], detail_only=True)

    if wiring_problems:
        fail = True
        emit([f"UNWIRED CHECKS ({len(wiring_problems)})"]
             + ["  " + p for p in wiring_problems] + [""], detail_only=True)

    if drawn_not_bommed:
        body = [f"drawn in a schematic, no BOM row ({len(drawn_not_bommed)}) "
                f"- ADVISORY, not a failure",
                "  A dependency, not a value. Each is either a part nobody "
                "ordered or a name nobody cleaned up.", ""]
        for tok, where in drawn_not_bommed:
            body.append(f"  {tok:24s} {', '.join(where)}")
        body.append("")
        emit(body, detail_only=True)

    if shape_problems:
        fail = True
        emit([f"CORPUS SHAPE ({len(shape_problems)})",
              "  The corpus is not where CORPUS_DIRS says it is, so every "
              "result below describes the wrong set of files.", ""]
             + ["  " + p for p in shape_problems] + [""], detail_only=True)

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

    # The one line that always prints. It carries the corpus FILE COUNT, and
    # that is deliberate: "PASS" alone was true while half the corpus was
    # unscanned, so the count is what a reader checks, not the verdict.
    n_unres = len(unresolved)
    if fail:
        print(f"FAIL {len(shape_problems)} shape + {len(link_problems)} links "
              f"+ {len(live)} stale + {len(bom_problems)} bom "
              f"| corpus {len(files)} files | {n_unres} unresolved (tracked) "
              f"| detail: .staleness/report.txt or --detail")
    else:
        print(f"PASS no live stale values | corpus {len(files)} files | "
              f"{n_unres} unresolved (tracked)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
