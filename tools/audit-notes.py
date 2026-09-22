#!/usr/bin/env python3
"""Tell a BOM notes cell's LIVE content from its accumulated history.

WHY THIS EXISTS. 88 % of hardware/bom.csv was `notes` prose - 118,198 of
134,555 characters - and hardware/**/notes.md, the shelf this repo's own
conventions designate for "what the circuit used to be", held 709 lines. The
history was not on the shelf; it was smeared through the field a builder reads
to order parts, in 48 dated `| YYYY-MM-DD:` supersession segments.

That is what made the staleness checker weak. A retired value sitting on the
same line as a live one is why the refutation exemption had to exist at all,
and the exemption is what hid eight live stale values through a twenty-agent
review. Take the history out of the data files and the exemption is not
needed.

THE CUT LINE, and it is the only rule here:

    KEEP what tells a builder WHAT TO DO.
    CUT what tells them WHAT SOMEONE USED TO THINK.

"CONTACT MATERIAL G, GOLD, NEVER W - silver goes intermittent at 1 uA" stays.
"This row said DO-214AC, which is the SS14's package" goes; git has it, and
git cannot go stale.

This tool does NOT trim. It classifies, so that a trim can be CHECKED rather
than trusted: run it before, trim by hand, run it after, and every sentence it
called LIVE must still be somewhere - this row, the circuit's page, or its
notes.md - or be a drop you can name.

Usage:
    python3 tools/audit-notes.py                 # summary, all rows
    python3 tools/audit-notes.py <REF> [<REF>]   # classified, one row each
    python3 tools/audit-notes.py --regrown       # rows that look like logs again
"""
import csv, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOM = os.path.join(ROOT, "hardware/bom.csv")

# A sentence that tells a builder what to do. Order matters only for reporting.
LIVE = [
    (r"\bNEVER\b|\bDO NOT\b|\bMUST\b|\bmust\b", "imperative"),
    (r"\bspecify\b|\bprefer\b|\bchoose\b|\bpick\b|\border\b", "instruction"),
    (r"\bTBD\b|\bopen\b|\bOPEN\b|\bBLOCKING\b|\bunsourced\b|NOT CHOSEN", "unresolved"),
    (r"decided by|DECIDED BY|decides it|before the order|before layout", "decider"),
    (r"\bmin/max\b|\bworst case\b|\btolerance\b|\bderate", "limit"),
]
# A sentence that records what the row used to say. These are what git holds.
HIST = [
    (r"\|\s*\d{4}-\d{2}-\d{2}", "dated supersession segment"),
    (r"\bused to\b|\bthis row said\b|\bthis row carried\b|\bwas wrong\b", "self-narration"),
    (r"\bREPLACES\b|\bsuperseded\b|\bSUPERSEDED\b|\bretired\b|\bRETIRED\b", "supersession"),
    (r"\bREFUTED\b|\brefuted\b|\bwas never\b|\bno longer\b", "refutation"),
    (r"\breviewers? (disagree|found|caught)\b|\bthe review\b|\bcold review\b", "review narration"),
    (r"\bUNBLOCKED\b|\bRESOLVES\b|\bnow CONFIRMED\b|\bwas BLOCKED\b", "status change"),
]


def segments(notes):
    """Split a cell the way its authors wrote it: dated segments, then prose."""
    parts = []
    for seg in re.split(r"\s*\|\s*(?=\*{0,3}\s*\d{4}-\d{2}-\d{2})", notes):
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z*(])", seg):
            s = s.strip()
            if s:
                parts.append(s)
    return parts


def classify(s):
    live = [n for p, n in LIVE if re.search(p, s)]
    hist = [n for p, n in HIST if re.search(p, s)]
    # History wins ties: a sentence that narrates a change and also shouts an
    # imperative is usually narrating the imperative someone USED to follow.
    # Reported as BOTH so a human decides, never silently dropped.
    if live and hist:
        return "BOTH", live + hist
    if hist:
        return "HIST", hist
    if live:
        return "LIVE", live
    return "PLAIN", []


def rows():
    with open(BOM, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    regrown = "--regrown" in sys.argv
    rs = rows()

    if args:
        for r in rs:
            if r["ref"] not in args:
                continue
            print(f"\n=== {r['ref']}  ({len(r['notes'])} chars)")
            for s in segments(r["notes"]):
                kind, why = classify(s)
                mark = {"LIVE": "  KEEP ", "HIST": "  cut  ",
                        "BOTH": "  ???  ", "PLAIN": "  ...  "}[kind]
                print(f"{mark}{s[:150]}")
                if why:
                    print(f"         ^ {kind}: {', '.join(sorted(set(why)))}")
        return 0

    tot = {"LIVE": 0, "HIST": 0, "BOTH": 0, "PLAIN": 0}
    per = []
    for r in rs:
        c = {"LIVE": 0, "HIST": 0, "BOTH": 0, "PLAIN": 0}
        for s in segments(r["notes"]):
            k, _ = classify(s)
            c[k] += 1
            tot[k] += 1
        per.append((len(r["notes"]), c["HIST"] + c["BOTH"], r["ref"], c))

    if regrown:
        # THE TRIGGER IS HISTORY SEGMENTS, NOT LENGTH, and the first version of
        # this got that wrong: `>= 3 or len > 1200` flagged twelve rows that
        # had just been trimmed correctly, because a dense SPEC is long too.
        # U-DAC is 1,891 characters of AVDD floors, grade-dependent tempco and
        # an order code that does not exist, with zero history in it. A
        # threshold that fires on correct rows is the trap CLAUDE.md names, in
        # the tool written to enforce the rule. Length is reported as context;
        # it decides nothing.
        bad = [p for p in per if p[1] >= 2]
        bad.sort(key=lambda p: (-p[1], -p[0]))
        for n, h, ref, c in bad:
            print(f"  {ref:22} {h:>2} history/ambiguous segment(s)   ({n:,} chars)")
        print(f"\n{len(bad)} row(s) still narrating rather than specifying")
        return 1 if bad else 0

    chars = sum(len(r["notes"]) for r in rs)
    print(f"hardware/bom.csv: {len(rs)} rows, {chars:,} chars of notes")
    print(f"  segments: {tot['LIVE']} LIVE, {tot['HIST']} history, "
          f"{tot['BOTH']} ambiguous (a human decides), {tot['PLAIN']} neutral")
    per.sort(reverse=True)
    print("\n  heaviest rows:")
    for n, h, ref, c in per[:12]:
        print(f"    {ref:22} {n:>6,} chars  {c['LIVE']:>2} keep  "
              f"{c['HIST']:>2} cut  {c['BOTH']:>2} ???")
    return 0


if __name__ == "__main__":
    sys.exit(main())
