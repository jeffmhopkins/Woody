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
# Raised 30 -> 100 on 2026-09-21: the restructure took the corpus from 33
# files to 118, and a floor of 30 would have let two thirds of it vanish
# before tripping. A floor that no plausible accident reaches is decoration.
MIN_CORPUS_FILES = 100

# The two files this tool READS rather than scans. Moving either one raised a
# FileNotFoundError traceback and exit 0 - and the commit hook greps stdout for
# four anchored words, none of which a traceback contains, so it rendered
# "staleness: " with nothing after it. A crash must not read as silence.
TOOL_INPUTS = ["config/figures.yaml", "hardware/bom.csv"]

# A forbidden value on a line that also refutes it is fine - that is how a
# correction is supposed to read. Only unqualified survivals are failures.
#
# JUDGED IN A WINDOW AROUND THE MATCH, not over the whole line. In bom.csv a
# "line" is an entire row, so any refutation word anywhere in a 2000-word
# notes cell excused every forbidden string in it - 28 of 59 exemptions were
# landing inside a BOM row, and two were outright escapes: a rule stated in a
# row's opening sentence and refuted 400 words later, and a live "five
# connectors" excused by an unrelated "rather than starred".
#
# A correction reads NEXT TO the thing it corrects. This window is what makes
# that the rule rather than the hope.
REFUTATION_WINDOW = 300

# THE VOCABULARY IS WHAT ACTUALLY LEAKED, not the distance. Measured on the
# live corpus: of 59 exemptions, 23 rode on a bare "was" and 4 on "old" -
# words that appear constantly in ordinary technical prose that is not a
# correction at all. Two named escapes prove the point, and NEITHER is fixed
# by any window:
#
#   FB-IN     states a ">=1 A" rule the datasheet refutes, and is excused by
#             a "was" 201 characters away, about something else.
#   WIRE-LOOM states a live "five connectors" against a tracked 8, and is
#             excused by "rather than starred" 24 characters away - an
#             unrelated clause, closer to the claim than any tightening
#             could exclude.
#
# So the exemption now requires a word that MEANS a correction was made, not
# merely a past tense. Dropped: was, were, prior, earlier, old, former,
# instead of, rather than, wrong, incorrect. A sentence that genuinely
# corrects something can always say "no longer", "superseded" or carry the
# dated marker this repository already uses.
REFUTATION = re.compile(
    r"\b(previously|stale|supersed\w+|withdrawn|refut\w+|no longer|used to|"
    r"corrected|deleted|obsolete|historical|retired|deprecated|"
    r"until \d{4}|this (row|line|page|ADR|file) (said|carried|read)|"
    r"carried a superseded)\b"
    # "An earlier revision ..." is this corpus's dominant house style for an
    # ADR refutation - 60 such openers, 41 of them with no other marker in
    # range. The bare word `earlier` was dropped (correctly: 380
    # non-correction uses), so the BIGRAM is restored instead.
    r"|an earlier (revision|version|draft)"
    r"|this (field|row|line|page|ADR|file) (said|carried|read|used to)",
    re.I)

# WITHDRAWN 2026-09-22: a bare ISO date, a bare "->", a bare "\u2192" and a
# case-sensitive bare NOT were all added here as correction markers, and all
# four are ORDINARY PROSE.
#
# Demonstrated by injection, byte-identical but for one token:
#     "Bench session 2026-08-14 covered the jack layout"   -> PASS
#     "Bench session covered the jack layout"              -> FAIL
#
# The exempt region went from 33.9 % to 48.4 % of corpus characters. ONE
# slice measured that pair, not three: this comment said "three cold slices
# measured that independently" and there is no third measurement in the
# twenty reports - D5 states the pair, D3 measured only the new side. A
# number travelling further than its evidence, inside the fix for that exact
# failure mode, caught by the re-verification slice (E1) that read it.
#
# And the pair conflates two changes, which matters to anyone repeating the
# work: new vocabulary at the whole-line geometry is 29.3 %, old vocabulary
# at the +-300 window is 63.2 %. THE WINDOW IS WHAT WIDENED THE SURFACE;
# the vocabulary narrowed it at either geometry. So withdrawing markers moves
# this number far less than the pair suggests, and a repeat run that sees it
# barely move has NOT refuted the diagnosis.
#
# All 68 forbidden-pattern matches in the corpus were exempted and the live
# list was EMPTY, which means the stale-value half of this checker was
# reporting nothing at all.
#
# WIRE-LOOM is the case that settles it: the commit that added these markers
# NAMES that row as one of the two escapes it was closing. It dropped the
# "rather than" the row used to ride on, and the row then rode on the date
# the same commit added, 222 characters away. Its sibling FB-IN is genuinely
# closed - because that one was fixed by editing the TEXT rather than the
# regex.
#
# A correction says it is a correction. It does not merely carry a date.


def corpus_files():
    out = []
    for f in CORPUS_FILES:
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            out.append(p)
    for d in CORPUS_DIRS:
        # followlinks=True: a circuit reachable only through a symlinked
        # directory was invisible to the scan AND left the corpus count
        # unmoved, so the MIN_CORPUS_FILES tripwire could not help either.
        for dirpath, _, names in os.walk(os.path.join(ROOT, d),
                                         followlinks=True):
            rel = os.path.relpath(dirpath, ROOT)
            if any(rel.startswith(x) for x in EXCLUDE):
                continue
            for n in names:
                if n.endswith((".md", ".csv", ".yaml", ".yml")):
                    out.append(os.path.join(dirpath, n))
    return sorted(set(out))


def check_readable(files):
    """A corpus file that cannot be READ must not silently leave the scan.

    check_figures wraps its open() in try/except and continues, and
    corpus_files() counts NAMES rather than successful reads - so one
    non-UTF-8 byte dropped a file out of the staleness scan while the corpus
    count, the number this tool nominates as the one to trust, still included
    it. Reported green, scanning less.
    """
    problems = []
    for path in files:
        try:
            open(path, encoding="utf-8").read()
        except Exception as e:
            problems.append(f"{os.path.relpath(path, ROOT)} cannot be read as "
                            f"UTF-8 ({type(e).__name__}) - it is being SKIPPED "
                            f"by every check while still counted in the corpus")
    return problems


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
                    # Narrow to a window around the match itself. The joined
                    # stream is what was searched, so the window is taken
                    # there and the line context is kept only for reporting.
                    lo = max(0, at - REFUTATION_WINDOW)
                    hi = min(len(text), at + len(bad) + REFUTATION_WINDOW)
                    near = text[lo:hi]
                    rec = (fig["id"], fig.get("value"), bad, rel, first,
                           ctx.strip()[:100])
                    (refuted if REFUTATION.search(near)
                     else live).append(rec)
    return live, refuted, spec


def check_patterns(spec):
    """A forbidden pattern that CANNOT match is indistinguishable from one
    that matches nothing.

    Two shapes, both real. A pattern containing a literal newline can never
    match the line-JOINED stream check_figures searches - `spi-series-r`
    carries "220 Ohm with\n~200 pF", which is exactly what CLAUDE.md
    2's "add one pattern per spelling you find" produces when the spelling
    you find is hard-wrapped. And a settled figure with an EMPTY forbidden
    list contributes nothing at all: four entries were in that state, and
    emptying every list in the register produced a PASS line byte-identical
    to a healthy run.

    Neither is reported anywhere today, so the report cannot distinguish
    "checked and clean" from "not checked".
    """
    problems, thin = [], []
    for fig in spec["figures"]:
        pats = fig.get("forbidden") or []
        for bad in pats:
            if "\n" in bad:
                problems.append(f"[{fig['id']}] pattern {bad!r} contains a "
                                f"newline and can never match the joined "
                                f"stream - split it at the wrap")
            # A PATTERN THAT CARRIES ITS OWN REFUTATION MARKER CAN NEVER FIRE
            # ANYWHERE, because the exemption window always contains the
            # match. Three slices found this independently; three patterns
            # were in that state, one of them belonging to the figure
            # CLAUDE.md names as the worst recorded case.
            if REFUTATION.search(bad):
                problems.append(f"[{fig['id']}] pattern {bad!r} contains a "
                                f"refutation marker, so it exempts itself and "
                                f"can never fire - reword it")
        if not pats and fig.get("status") == "settled":
            thin.append(f"[{fig['id']}] is settled with an EMPTY forbidden "
                        f"list - it contributes nothing to any run")
    return problems, thin


def check_bom_generated():
    """hardware/bom.csv is GENERATED. Assert it still matches its fragments.

    The trap this closes has already sprung once in this repo, on
    MANIFEST.csv: a direct edit to a generated file survives until the next
    run of its tool and then disappears without a word. bom.csv is the
    most-cited file here - 37 backtick references - so it is the worst
    possible place to repeat it.

    A banner comment was considered and rejected: csv.DictReader takes row 0
    as the header, and two tools already read this file.
    """
    import subprocess
    try:
        r = subprocess.run([sys.executable,
                            os.path.join(ROOT, "tools/merge-bom.py"), "--check"],
                           capture_output=True, text=True, cwd=ROOT, timeout=60)
        m = subprocess.run([sys.executable,
                            os.path.join(ROOT, "tools/merge-manifests.py"),
                            "--check"],
                           capture_output=True, text=True, cwd=ROOT, timeout=60)
    except Exception as e:
        return [f"could not run a generated-file check: {e}"]
    # BOTH RESULTS, ALWAYS. This returned on the manifest result before it
    # ever examined merge-bom's, so a manifest problem MASKED a hand-edited
    # hardware/bom.csv completely - on the most-cited file in the repository,
    # in the check written to guard it. The stdout-plus-stderr fix below was
    # applied to one branch and not to this one, six lines apart, in the same
    # function, in the same commit.
    out = []
    for tool, res in (("merge-manifests.py", m), ("merge-bom.py", r)):
        if res.returncode == 0:
            continue
        # Keep every line the tool chose to print. The old filter kept only
        # "PROBLEM:" and "does not match", which discarded every
        # "REFUSING TO WRITE:" message merge-manifests has and replaced a
        # precise, purpose-written refusal with "it probably crashed".
        msgs = [l.rstrip() for l in (res.stdout + "\n" + res.stderr).splitlines()
                if l.strip() and not l.strip().startswith("PASS")]
        out += msgs or [f"{tool} --check exited {res.returncode} and said "
                        f"nothing parseable - it probably crashed. Run it "
                        f"directly"]
    if out:
        return out
    return []
    # HARVEST STDERR TOO, AND NEVER RETURN AN EMPTY LIST ON A NON-ZERO EXIT.
    #
    # This read stdout only. merge-bom.py opens fragments as UTF-8, so one
    # Latin-1 micro-sign or ohm from a spreadsheet export makes it traceback
    # to STDERR with empty stdout - and an empty list is indistinguishable
    # from "no problems". Verified: with a hand-edit live in bom.csv AND one
    # \xb5 byte in a fragment, this printed PASS, exit 0.
    #
    # That is the FOURTH instance of the fail-open class in this repository,
    # and it was inside the check written to close the third. A non-zero exit
    # means something is wrong; if it produced no parseable output, say that
    # rather than nothing.
    msgs = [l.strip() for l in (r.stdout + "\n" + r.stderr).splitlines()
            if l.strip() and "problems" not in l]
    return msgs or [f"merge-bom.py --check exited {r.returncode} and said "
                    f"nothing parseable - it probably crashed. Run it directly"]


# The 11 columns, spelled once. merge-bom.py owns the same list; if they
# disagree the generated-file check fails, which is the point.
BOM_HDR = ["ref", "category", "part", "manufacturer", "description",
           "package", "qty", "status", "source", "adr", "notes"]


def check_bom():
    path = os.path.join(ROOT, "hardware/bom.csv")
    rows = list(csv.reader(open(path, newline="", encoding="utf-8")))
    hdr, n, problems = rows[0], len(rows[0]), []
    # Assert the HEADER, not just that every row agrees with row 0. The column
    # count was derived from row 0, so a truncated header made every data row
    # "wrong" - or, with a matching truncation, made the whole file agree with
    # itself at the wrong width.
    if len(hdr) != len(BOM_HDR) or [c.strip() for c in hdr] != BOM_HDR:
        problems.append(f"bom.csv:1 header is {hdr}, expected {BOM_HDR}")
    seen = {}
    for idx, r in enumerate(rows[1:], 2):
        if len(r) != n:
            problems.append(f"bom.csv:{idx} has {len(r)} columns, expected {n}")
        if r and r[0] in seen:
            problems.append(f"bom.csv:{idx} duplicate refdes {r[0]} (also line {seen[r[0]]})")
        elif r:
            seen[r[0]] = idx
    return problems, set(seen), n, len(rows) - 1, {
        r[0]: r for r in rows[1:] if r}


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
    # CO-MENTION is the banner every circuit.yaml carries explaining how its
    # edges were seeded. It is prose about the graph, not a part, and it put
    # a 23-file entry at the top of this advisory.
    r"|^CO-MENTION$"
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
        # The one reader here that had no try/except. One Latin-1 byte
        # anywhere in hardware/** crashed the whole tool from inside the check
        # documented as "ADVISORY, never fatal", and check_readable's
        # purpose-written message never got printed.
        try:
            text = open(path, encoding="utf-8").read()
        except Exception:
            continue
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


def load_circuits():
    """Every circuit.yaml in the tree, keyed by its declared id."""
    out = {}
    # followlinks=True HERE TOO. The fix went into corpus_files() and not
    # into this walk, so a circuit reachable only through a symlink joined
    # the corpus while the circuit count stayed put - and "a circuit
    # reachable only through a symlinked directory" is the stated reason the
    # change was made.
    for dirpath, _, names in os.walk(os.path.join(ROOT, "hardware"),
                                     followlinks=True):
        if "circuit.yaml" not in names:
            continue
        rel = os.path.relpath(os.path.join(dirpath, "circuit.yaml"), ROOT)
        try:
            data = yaml.safe_load(open(os.path.join(ROOT, rel), encoding="utf-8"))
        except Exception as e:
            out[rel] = {"_broken": str(e), "_path": rel}
            continue
        data = data or {}
        data["_path"] = rel
        key = data.get("id", rel)
        # A DUPLICATE id used to EVICT a whole circuit from the map, silently:
        # the second file overwrote the first and every check below then
        # described a tree with one fewer circuit in it. A real dead-refdes
        # finding was replaced by a cosmetic id/directory finding that way.
        if key in out:
            data["_dup_of"] = out[key].get("_path", "?")
        out[key] = data
    return out


def check_circuits(circuits, spec, bom_refs):
    """Declared dependency edges must resolve. D3's design, zero-false-positive half.

    D3's central measurement is why this checks DECLARED edges only: an
    INFERRED dependency edge has an unusable noise floor - run raw,
    check_refdes yields 36 hits of which ~14 are not reference designators at
    all - and a check that cries wolf gets ignored or deleted. That is exactly
    what happened to check_refdes, which sat unwired for the tool's whole life.

    So nothing here guesses. Every edge was written down by someone, and the
    only question asked is whether the thing it names still exists.
    """
    problems = []
    fig_ids = {f["id"] for f in spec["figures"]}
    provided = set()
    for c in circuits.values():
        for p in c.get("provides") or []:
            provided.add(p)

    for cid, c in sorted(circuits.items()):
        path = c.get("_path", cid)
        if "_broken" in c:
            problems.append(f"{path}: will not parse - {c['_broken'][:80]}")
            continue
        if "_dup_of" in c:
            problems.append(f"{path}: declares id {cid!r}, which "
                            f"{c['_dup_of']} already declares - one of them "
                            f"is invisible to every check here")
        # id must match the directory it sits in, or `owner:` and
        # `depends_on:` point at a name the tree does not have.
        want = os.path.dirname(path).replace("hardware/", "", 1)
        if c.get("id") != want:
            problems.append(f"{path}: id is {c.get('id')!r}, directory says "
                            f"{want!r}")
        for dep in c.get("depends_on") or []:
            if ":" not in str(dep):
                problems.append(f"{path}: depends_on {dep!r} has no type "
                                f"prefix (adr:/circuit:/fig:/refdes:/node:)")
                continue
            kind, name = str(dep).split(":", 1)
            if kind == "fig" and name not in fig_ids:
                problems.append(f"{path}: depends_on fig:{name} - no such "
                                f"figure in config/figures.yaml")
            elif kind == "circuit" and name not in circuits:
                problems.append(f"{path}: depends_on circuit:{name} - no "
                                f"circuit declares that id")
            elif kind == "refdes" and name not in bom_refs:
                problems.append(f"{path}: depends_on refdes:{name} - no BOM "
                                f"row. Deleted with the part it belonged to?")
            elif kind == "adr":
                hits = glob_adr(name)
                if not hits:
                    problems.append(f"{path}: depends_on adr:{name} - no such ADR")
            elif kind == "node" and name not in provided:
                problems.append(f"{path}: depends_on node:{name} - no circuit "
                                f"provides it")
            elif kind not in ("adr", "circuit", "fig", "refdes", "node"):
                # NO ELSE ON THE PREFIX CHAIN meant six typo'd prefixes -
                # "refdes " with a space, "Refdes", "refdess", "part", "nodes",
                # "figs" - were all silently accepted as valid edges.
                problems.append(f"{path}: depends_on {dep!r} has an unknown "
                                f"type prefix {kind!r} - expected one of "
                                f"adr:/circuit:/fig:/refdes:/node:")
    return problems


def glob_adr(num):
    import glob as _g
    return _g.glob(os.path.join(ROOT, "docs/decisions", f"{num}-*.md"))


def check_verified_against(circuits):
    """A cited datasheet SHA must still match the manifest.

    Catches a re-bank: someone replaces a PDF with a newer revision, the
    manifest's hash moves, and every figure read off the old revision is now
    resting on a document nobody has read.
    """
    manifest = os.path.join(ROOT, "datasheets/MANIFEST.csv")
    if not os.path.exists(manifest):
        return []
    have = {}
    for r in csv.DictReader(open(manifest, newline="", encoding="utf-8")):
        if r.get("sha256"):
            have.setdefault(r["sha256"].strip(), set()).add(
                (r.get("part", "") or "").strip())
    problems = []
    for cid, c in sorted(circuits.items()):
        for v in c.get("verified_against") or []:
            sha = str(v.get("sha256", "")).strip()
            part = v.get("part", "?")
            if sha == "BLOCKED":
                # An honest gap, and it must say what decides it - the same
                # rule CLAUDE.md applies to a TBD.
                if not v.get("blocked_on"):
                    problems.append(f"{c['_path']}: verified_against {part} is "
                                    f"BLOCKED with no blocked_on: saying what "
                                    f"decides it")
                continue
            if sha and sha not in have:
                problems.append(f"{c['_path']}: verified_against {part} cites "
                                f"sha256 {sha[:12]}... which is in no manifest "
                                f"row - was the document re-banked?")
            elif sha and part != "?" and part.strip() not in have[sha]:
                # THE SHA WAS ALL THAT WAS COMPARED, so a hash copied from a
                # DIFFERENT part's manifest row passed. The row holds the part
                # name; it was read and never used.
                problems.append(f"{c['_path']}: verified_against {part!r} "
                                f"cites a sha256 that belongs to "
                                f"{sorted(have[sha])} - the hash is real but "
                                f"it is a different document")
    return problems


def check_sections(files):
    """A cross-file `page.md §N` reference must find a §N heading in that page.

    Added 2026-09-21. A section number is a path with different syntax: it
    names a POSITION inside another document, and moving positions is exactly
    what a restructure does. The corpus carries about twenty of these and the
    Phase B splits invalidated several - ADR 0004 pointed at a §4 that had
    moved to another file entirely.

    Same principle as check_links and check_owners: do not hunt for spellings
    already known to be wrong, assert that what is written now RESOLVES.
    """
    ref = re.compile(r"`?([a-z0-9][a-z0-9-]*\.md)`?\)?[^.\n]{0,24}?§\s?(\d+)")
    head = re.compile(r"^#{1,6}\s.*?§\s?(\d+)", re.M)

    # KEYED BY BASENAME, this pooled all 15 notes.md and all 10 README.md
    # into one namespace, so `notes.md 5` resolved against ANY notes.md in
    # the tree - a hole the restructure created by giving every circuit a
    # notes.md. Key by relative path, and resolve a bare filename only when
    # exactly one file in the corpus carries it.
    declares, by_base = {}, {}
    for path in files:
        base = os.path.basename(path)
        if not base.endswith(".md"):
            continue
        rel = os.path.relpath(path, ROOT)
        try:
            declares[rel] = set(
                head.findall(open(path, encoding="utf-8").read()))
        except Exception:
            continue
        by_base.setdefault(base, []).append(rel)

    problems = []
    for path in files:
        rel = os.path.relpath(path, ROOT)
        if not rel.endswith(".md"):
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except Exception:
            continue
        for m in ref.finditer(text):
            target, num = m.group(1), m.group(2)
            if target == os.path.basename(path):
                continue                  # self-reference
            # Prefer a sibling of the citing page, then a unique basename.
            sib = os.path.relpath(
                os.path.normpath(os.path.join(os.path.dirname(path), target)),
                ROOT)
            if sib in declares:
                tgt_rel = sib
            elif len(by_base.get(target, [])) == 1:
                tgt_rel = by_base[target][0]
            elif len(by_base.get(target, [])) > 1:
                line = text[:m.start()].count("\n") + 1
                problems.append(
                    f"{rel}:{line} points at {target} §{num}, but "
                    f"{len(by_base[target])} files in the corpus are called "
                    f"{target} - the reference is ambiguous")
                continue
            else:
                continue                  # not a corpus page; check_links owns it
            if num not in declares[tgt_rel]:
                line = text[:m.start()].count("\n") + 1
                problems.append(f"{rel}:{line} points at {tgt_rel} §{num}, "
                                f"which that page no longer declares")
    return problems


def anchored_in(tok, text):
    """Is `tok` present in `text` as a value rather than as debris?

    Nothing before it that would make it part of a longer number or of a part
    number - this is what stops "4.86" being satisfied by "14.863 mm", "197"
    by "OPA2197" and "5050" by "REF5050". A trailing unit letter IS allowed,
    because "100R", "47uF" and "5.21V" are how the BOM spells values.
    """
    return re.search(r"(?<![0-9A-Za-z.])" + re.escape(tok) + r"(?![0-9])",
                     text) is not None


REFDES_IN_VALUE = re.compile(r"\b([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\b")


def check_datasheets():
    """Run verify-datasheets.py, which was wired to nothing.

    CLAUDE.md 3 says it "must pass before committing anything under
    datasheets/". It was in no automated path at all, so that was a human
    rule with no mechanism - and a byte-tampered banked PDF, or a deleted
    one, both gave this checker a clean PASS while verify-datasheets caught
    each of them on its own.
    """
    import subprocess
    tool = os.path.join(ROOT, "tools/verify-datasheets.py")
    if not os.path.exists(tool):
        return [f"tools/verify-datasheets.py is missing - CLAUDE.md 3 "
                f"requires it to pass before anything under datasheets/ is "
                f"committed"]
    try:
        r = subprocess.run([sys.executable, tool], capture_output=True,
                           text=True, cwd=ROOT, timeout=120)
    except Exception as e:
        return [f"could not run verify-datasheets.py: {e}"]
    if r.returncode == 0:
        return []
    # msgs[:40] TRUNCATED PAST THE REAL PROBLEMS. verify-datasheets.py prints
    # its "not a failure" BOM-coverage advisory BEFORE the list of actual
    # defects, so at 37+ uncovered parts a genuine SHA mismatch fell off the
    # end - reproduced with a flipped byte in a banked PDF. Put the lines
    # that name a real defect first, and keep the cap generous.
    lines = [l.rstrip() for l in (r.stdout + "\n" + r.stderr).splitlines()
             if l.strip() and not l.strip().startswith(("OK", "PASS"))]
    hot = [l for l in lines if any(k in l for k in
           ("sha256", "MISMATCH", "does not resolve", "not on disk",
            "REFUSING", "Traceback", "Error", "problems"))]
    rest = [l for l in lines if l not in hot]
    msgs = hot + rest
    return msgs[:120] or [f"verify-datasheets.py exited {r.returncode} and "
                          f"said nothing parseable. Run it directly"]


def check_bom_figures(spec, bom_rows):
    """A figure that names a part must agree with that part's BOM row.

    THE HOLE THIS CLOSES IS THE WHOLE PROJECT, and a cold newcomer slice found
    it by following the documented procedure rather than by reading code.

    Change a resistor the way CLAUDE.md and repo-maintenance.md tell you to -
    edit the fragment, re-run merge-bom.py, run this checker - and you get
    "0 problems" and "PASS no live stale values" while config/figures.yaml and
    the owner page both still state the old value. Reproduced: R-SPI-SER from
    100R to 220R, green, with 220 ohm being the value that figure's derivation
    exists to REJECT.

    It escaped because nothing related a BOM row to the figure governing it.
    check_owners compares the register against the owner page, and after that
    edit those two still agreed with each other perfectly - both still said
    100. The BOM is the third party to that agreement and no check read it as
    one.
    """
    problems = []
    for fig in spec["figures"]:
        if fig.get("status") != "settled":
            continue
        value = str(fig.get("value", ""))
        nums = [t for t in re.findall(r"\d+\.?\d*", value) if len(t) >= 2]
        if not nums:
            continue
        primary = max(nums, key=len)
        for ref in REFDES_IN_VALUE.findall(value):
            row = bom_rows.get(ref)
            if row is None:
                continue
            # THE `part` FIELD, NOT THE WHOLE ROW. Searching the row passed
            # the very edit this check exists to catch: R-SPI-SER's notes
            # cell contains the sentence "THREE. 100R, not 220R", so after
            # the part field was changed to 220R the string "100" was still
            # there, in prose, and the check was satisfied by the argument
            # for the value rather than by the value.
            part = row[BOM_HDR.index("part")] if len(row) > 2 else ""
            if not anchored_in(primary, part):
                problems.append(
                    f"[{fig['id']}] says {value!r}, but the BOM part field "
                    f"for {ref} is {part!r} and states no {primary} - the "
                    f"register and the part it names disagree")
    return problems


NUM_UNIT = re.compile(
    r"(?<![0-9A-Za-z.])(\d+(?:\.\d+)?)\s?"
    r"(mV|kV|V|mA|uA|µA|A|kohm|Mohm|ohm|Ω|kΩ|MΩ|mW|kW|W|"
    r"°C|K|mm|cm|um|µm|ns|us|µs|ms|s|kHz|MHz|Hz|pF|nF|uF|µF|"
    r"dB|HP|AWG|ppm|%)(?![0-9A-Za-z])")


def check_restated(files, spec):
    """A number restated across three or more files, with no register entry.

    ADVISORY. This is the condition every staleness defect in this repository
    grows from, and nothing has ever looked for it: the checker can only
    search for values it has already been TOLD are old, so the state that
    precedes a defect - the same number written out in five places instead of
    cited once - is invisible until the number moves and five documents are
    wrong at once.

    CLAUDE.md names sensor-full-scale as the worst recorded case and says the
    corpus spelled it seven ways. It was restated six times before it moved.

    Advisory rather than fatal on purpose. check_refdes sat unwired for this
    tool's whole life because it was switched on with an unusable noise floor,
    and a check that cries wolf gets ignored or deleted. This one reports and
    does not fail, so the number can be driven down deliberately.
    """
    known = set()
    for fig in spec["figures"]:
        blob = str(fig.get("value", "")) + " " + " ".join(
            fig.get("forbidden") or [])
        for n, _u in NUM_UNIT.findall(blob):
            known.add(n)
        for n in re.findall(r"\d+\.?\d*", str(fig.get("value", ""))):
            known.add(n)

    where = {}
    for path in files:
        rel = os.path.relpath(path, ROOT)
        if rel == "config/figures.yaml":
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except Exception:
            continue
        for n, u in set(NUM_UNIT.findall(text)):
            if n in known or float(n) == 0:
                continue
            where.setdefault(f"{n} {u}", set()).add(rel)

    return sorted(((k, sorted(v)) for k, v in where.items() if len(v) >= 3),
                  key=lambda kv: (-len(kv[1]), kv[0]))


def check_owners(spec):
    """Rule 1: the owning document STATES the figure. Assert it actually does.

    Added 2026-09-21. `owner:` had never been read by anything - not by this
    tool, not by any other - for the whole life of the register. Four separate
    Phase B split agents, none of which could see the others, reported the
    same consequence: a split moves a derivation into a sibling directory and
    the register goes on naming the file it left, silently.

    Note what a weaker version of this check would have missed. After Phase A
    rewrote paths, every `owner:` path still RESOLVED - the file existed. What
    had broken was that the file no longer stated the value. So this checks
    the claim rule 1 actually makes, not the spelling of a path.

    Matched on the value's numeric tokens, because values are prose as often
    as numbers ("fault isolation and HF isolation (r_d 69 mohm at 392 mA)").
    A value with no digits at all is unmatchable and is skipped rather than
    guessed at.
    """
    problems, weak = [], []
    for fig in spec["figures"]:
        value = str(fig.get("value", ""))
        if value in ("DISPUTED", "BLOCKED") or fig.get("status") != "settled":
            continue
        owner = fig.get("owner", "")
        path = os.path.join(ROOT, owner)
        if not os.path.exists(path):
            problems.append(f"[{fig['id']}] owner {owner!r} does not exist")
            continue
        # WHAT THIS CHECK CANNOT DO, stated because a green result here is
        # otherwise read as more than it is.
        #
        # A token must be DISTINCTIVE to be evidence. chain-connectors' value
        # is "8": it matches almost any prose, so the check would pass
        # wherever the owner pointed. spi-series-r tokenises to 100 and 3.
        # Three figures were verified by hand in the 2026-09-21 restructure
        # and all three had genuinely moved while this check stayed green.
        #
        # So a weak value is reported as UNVERIFIABLE rather than passed. The
        # check then makes exactly one claim - "the owner states something
        # only this figure would say" - and says so when it cannot.
        # THE LONGEST token, not any token. `any()` over everything >= 3
        # chars still passed spi-series-r on "100" - the very figure this
        # docstring names as the counter-example - because "100" also spells
        # the Cat5 line impedance and "not 100 %". A check whose own
        # docstring names a case it does not catch is worse than no check.
        # TWO THINGS WENT WRONG HERE AND BOTH ARE WORTH NAMING.
        #
        # (1) The tokens came from a DIGITS-ONLY regex, so for a value like
        #     "100 ohm, R-SPI-SER, qty 3" the only token >= 3 characters was
        #     "100" - which is the exact token the previous docstring named as
        #     the reason the version before THAT was wrong. Repointing that
        #     figure's owner at an unrelated ADR gave PASS, exit 0, because
        #     the ADR contains "100 ohm" in a key-switch network.
        #
        # (2) The match was an unanchored substring, so "4.86" was satisfied
        #     by "14.863 mm", "197" by "OPA2197", and "5050" by "REF5050" -
        #     a quarter of the settled register was being verified against a
        #     part number.
        #
        # So: take EVERY distinctive token, numeric and symbolic, and require
        # each to appear ANCHORED - not glued to a neighbouring digit, letter
        # or hyphen. An identifier like R-SPI-SER is far more distinctive than
        # any number in the same value, and it was being discarded.
        try:
            text = open(path, encoding="utf-8").read()
        except Exception:
            continue

        # Take the number tokens the same way they will be LOOKED FOR: a run
        # of digits glued to letters inside the value is part of a part
        # number, not a value. cref-out-node's value begins "REF5050 VOUT",
        # and picking 5050 out of it meant the check was asking whether the
        # owner page mentions a part - which it does, and which proves
        # nothing about the topology the figure actually states.
        nums = [t for t in re.findall(r"(?<![0-9A-Za-z.])(\d+\.?\d*)(?![0-9A-Za-z])",
                                      value) if len(t) >= 3]
        idents = [t for t in re.findall(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b",
                                        value) if len(t) >= 5]
        # TWO DEFECTS HERE, BOTH FOUND BY A COLD AUDIT ON 2026-09-22.
        #
        # (1) `or` IS EXCLUSIVE. For any figure whose value contains a
        #     hyphenated identifier the numbers were never looked at at all -
        #     so spi-series-r was verified against "R-SPI-SER" and its value
        #     100 was NOT CHECKED. That is a REGRESSION: the version before
        #     this one would have caught the very case this one was written
        #     for. The docstring above says "take EVERY distinctive token,
        #     numeric and symbolic", and `or` is not how you take every one.
        #
        # (2) `sorted(..., key=len)` IS NONDETERMINISTIC. Ties break on set
        #     iteration order, i.e. on PYTHONHASHSEED. loop-budget's tested
        #     token came out 196, 241 or 250 at random; end to end, with a
        #     real rule-1 violation live, ten identical runs gave 6 PASS and
        #     4 FAIL. That is worse than a hole: it means no run of this tool
        #     proves anything, because the next run may disagree.
        #
        # So: union, not alternation; and a total order on the sort key.
        toks = (sorted(set(idents), key=lambda t: (-len(t), t))[:2]
                + sorted(set(nums), key=lambda t: (-len(t), t))[:1])

        if not toks:
            weak.append(f"[{fig['id']}] value {value!r} has no token "
                        f"distinctive enough to locate - owner "
                        f"{owner} is UNCHECKED")
            continue

        def anchored(tok):
            return anchored_in(tok, text)

        missing = [t for t in toks if not anchored(t)]
        if missing:
            problems.append(f"[{fig['id']}] owner {owner} does not state its "
                            f"own value {value!r} - looked for "
                            f"{', '.join(repr(m) for m in missing)} and found "
                            f"no unglued occurrence. Did the derivation move?")
    return problems, weak


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
    # INLINE MARKDOWN LINKS TO .md ONLY was most of this check's surface
    # missing: broken links to bom.csv, config/figures.yaml and a .dxf all
    # passed, and so did every reference-style link. A link is a path, and a
    # path either resolves or it does not; the extension is not the point.
    # THE CHARACTER CLASS EXCLUDED `#`, so the regex failed outright on any
    # link carrying an anchor and the split("#") below was unreachable. 23 of
    # 166 inline links were out of coverage - all 23 circuit pages'
    # `](../../README.md#the-interfaces-table)`, i.e. the anchor added in the
    # same batch, pointing at the one heading a restructure is most likely to
    # move. Single-quoted titles were unmatched too.
    pat = re.compile(r"\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")
    refpat = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(\S+)", re.M)
    problems = []
    for path in files:
        rel = os.path.relpath(path, ROOT)
        if not rel.endswith(".md"):
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except Exception:
            continue
        for m in list(pat.finditer(text)) + list(refpat.finditer(text)):
            tgt = m.group(1).split("#")[0]
            if not tgt or tgt.startswith(("http://", "https://", "mailto:",
                                          "#")):
                continue
            dest = os.path.normpath(os.path.join(os.path.dirname(path), tgt))
            if not os.path.exists(dest):
                line = text[:m.start()].count("\n") + 1
                problems.append(f"{rel}:{line} links to {tgt!r}, which does "
                                f"not resolve")
    return problems


RAN = set()


def instrument():
    """Wrap every check so that RUNNING it is what gets recorded.

    This assertion used to read the SOURCE TEXT of main() and look for the
    substring "check_links(". That is satisfied by a call that never happens:
    `link_problems = []  # check_links(files)` passes, and so does
    `if False and link_problems:`. Both were demonstrated, each giving PASS
    with a live broken link and UNWIRED CHECKS = 0.

    A check that does not run reads exactly like one that passes - which is
    the whole reason this assertion exists - so the assertion itself must not
    be satisfiable by anything short of the call actually being made.
    """
    for name, fn in list(globals().items()):
        if not (name.startswith("check_") and name != "check_checks"
                and callable(fn)):
            continue

        def make(nm, f):
            def wrapper(*a, **k):
                RAN.add(nm)
                return f(*a, **k)
            wrapper.__doc__ = f.__doc__
            return wrapper
        globals()[name] = make(name, fn)


def check_checks():
    """Every check in this file must actually have been called.

    check_refdes() was defined here, fully written, and never called from
    main() - for the whole life of the tool. Two cold agents found it
    independently in one afternoon, and a third caught check_corpus_shape()
    in the same unwired state while it was being added.

    Called at the END of main(), because it now reports what RAN.
    """
    return [f"{n}() is defined and was never called - a check that does not "
            f"run reads exactly like one that passes"
            for n, f in sorted(globals().items())
            if n.startswith("check_") and n != "check_checks"
            and callable(f) and n not in RAN]


def main():
    files = corpus_files()

    # Before anything else. A shape problem makes every result below it a
    # statement about the wrong set of files, so it is reported first and it
    # is fatal on its own.
    shape_problems = check_corpus_shape(files) + check_readable(files)

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
    bom_problems, bom_refs, ncols, nrows, bom_rows = check_bom()
    drawn_not_bommed = check_refdes(files, bom_refs)
    link_problems = check_links(files)
    owner_problems, owner_weak = check_owners(spec)
    section_problems = check_sections(files)
    circuits = load_circuits()
    generated_problems = check_bom_generated()
    datasheet_problems = check_datasheets()
    pattern_problems, thin_patterns = check_patterns(spec)
    bomfig_problems = check_bom_figures(spec, bom_rows)
    restated = check_restated(files, spec)
    circuit_problems = (check_circuits(circuits, spec, bom_refs)
                        + check_verified_against(circuits))
    # LAST, because it now reports what actually ran rather than what the
    # source text of this function appears to say.
    wiring_problems = check_checks()

    emit([f"corpus: {len(files)} files | bom.csv: {nrows} rows x {ncols} cols | "
          f"figures tracked: {len(spec['figures'])}", ""], detail_only=True)

    fail = False

    if generated_problems:
        fail = True
        emit([f"GENERATED FILE EDITED BY HAND ({len(generated_problems)})"]
             + ["  " + p for p in generated_problems] + [""], detail_only=True)

    if bomfig_problems:
        fail = True
        emit([f"REGISTER vs BOM ({len(bomfig_problems)})",
              "  A figure and the part it names state different values. "
              "Editing a fragment without the register is how this happens.",
              ""]
             + ["  " + p for p in bomfig_problems] + [""], detail_only=True)

    if pattern_problems:
        fail = True
        emit([f"PATTERNS THAT CANNOT FIRE ({len(pattern_problems)})",
              "  Indistinguishable in every report from a pattern that "
              "matches nothing.", ""]
             + ["  " + p for p in pattern_problems] + [""], detail_only=True)

    if datasheet_problems:
        fail = True
        emit([f"BANKED DATASHEETS ({len(datasheet_problems)})",
              "  verify-datasheets.py, which CLAUDE.md 3 requires to pass.",
              ""]
             + ["  " + p for p in datasheet_problems] + [""], detail_only=True)

    if circuit_problems:
        fail = True
        emit([f"CIRCUIT DEPENDENCIES ({len(circuit_problems)})",
              "  A declared edge naming something that is not there.", ""]
             + ["  " + p for p in circuit_problems] + [""], detail_only=True)

    if section_problems:
        fail = True
        emit([f"BROKEN SECTION REFERENCES ({len(section_problems)})",
              "  A section number names a position inside another document.", ""]
             + ["  " + p for p in section_problems] + [""], detail_only=True)

    if owner_weak:
        emit([f"figure owners this check CANNOT verify ({len(owner_weak)}) "
              f"- not failures, but not confirmations either"]
             + ["  " + w for w in owner_weak] + [""], detail_only=True)

    if owner_problems:
        fail = True
        emit([f"FIGURE OWNERS ({len(owner_problems)})",
              "  Rule 1: the owning document states the figure. These do not.", ""]
             + ["  " + p for p in owner_problems] + [""], detail_only=True)

    if link_problems:
        fail = True
        emit([f"BROKEN LINKS ({len(link_problems)})"]
             + ["  " + p for p in link_problems] + [""], detail_only=True)

    if wiring_problems:
        fail = True
        emit([f"UNWIRED CHECKS ({len(wiring_problems)})"]
             + ["  " + p for p in wiring_problems] + [""], detail_only=True)

    if thin_patterns:
        emit([f"settled figures with NO forbidden patterns "
              f"({len(thin_patterns)}) - ADVISORY. These contribute nothing "
              f"to any run, and a run with no coverage used to print the "
              f"same PASS line as a healthy one."]
             + ["  " + t for t in thin_patterns] + [""], detail_only=True)

    if restated:
        body = [f"RESTATED, NOT CITED ({len(restated)}) - ADVISORY",
                "  A value written out in three or more files with no entry "
                "in the register. This is the state every staleness defect "
                "in this repository grew from: rule 1 says state it once and "
                "cite it, and nothing has ever checked that.", ""]
        for val, wh in restated[:40]:
            body.append(f"  {val:14s} {len(wh)} files: {', '.join(wh[:4])}"
                        + (" ..." if len(wh) > 4 else ""))
        if len(restated) > 40:
            body.append(f"  ... and {len(restated) - 40} more")
        body.append("")
        emit(body, detail_only=True)

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
    # COVERAGE ON EVERY LINE, pass or fail. Emptying every forbidden list in
    # the register produced a PASS line byte-identical to a healthy run, so
    # the verdict alone never said how much had actually been checked. The
    # corpus file count is here for the same reason: "PASS" was once true
    # while half the corpus was unscanned.
    npat = sum(len(f.get("forbidden") or []) for f in spec["figures"])
    cov = (f"{len(files)} files, {len(circuits)} circuits, "
           f"{len(spec['figures'])} figures / {npat} patterns")
    if fail:
        print(f"FAIL {len(shape_problems)} shape + {len(owner_problems)} owners + {len(link_problems)} links "
              f"+ {len(section_problems)} sections + {len(circuit_problems)} deps "
              f"+ {len(generated_problems)} generated + {len(bomfig_problems)} register-vs-bom "
              f"+ {len(datasheet_problems)} datasheets + {len(pattern_problems)} dead-patterns "
              f"+ {len(wiring_problems)} unwired "
              f"+ {len(live)} stale + {len(bom_problems)} bom "
              f"| corpus {cov} | {n_unres} unresolved (tracked) "
              f"| detail: .staleness/report.txt or --detail")
    else:
        print(f"PASS no live stale values | corpus {cov} | "
              f"{n_unres} unresolved (tracked) | "
              f"{len(restated)} restated-not-cited (advisory)")
    return 1 if fail else 0


if __name__ == "__main__":
    instrument()
    sys.exit(main())
