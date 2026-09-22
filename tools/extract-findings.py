#!/usr/bin/env python3
"""Build a wave's finding ledger FROM ITS REPORTS. Generated, never typed.

A cold slice measured this wave and found the thing that explains ten
consecutive rounds being judged "partial":

    198 numbered findings across the reports.
    0 of them referenced by id in VERIFIED.md.
    0 in STATUS.md.

Verification addressed findings by restating them in prose, so a claim could
be answered twice or not at all and nobody could tell which. "Every one
hand-verified" was true of REPORTS and false of FINDINGS - about a quarter
were actually checked. And the next round had no list to be complete against,
which is the mechanical reason every round is found partial. It is not a
failure of diligence; there was no denominator.

THIS FILE IS GENERATED, and that is the whole point. A hand-maintained ledger
is a restated count, and CLAUDE.md rule 1 exists because restated counts go
stale - the wave-count sentence in CLAUDE.md has now been wrong three times,
including once inside the paragraph explaining why. So the ledger is derived
from the reports on every run, and the reports stay the single source.

Usage:  python3 tools/extract-findings.py <wave-dir> [--check]
"""
import csv, os, re, sys

ID = re.compile(r"\b([A-Z]\d{1,2}[-.]\d{1,2})\b")
SEV = re.compile(r"\b(high|critical|blocking|medium|low|advisory)\b", re.I)

# A finding is INTRODUCED where its id leads a line or a bold run, and merely
# CITED anywhere else. Both matter and they are different numbers: the first
# is what a round has to answer, the second is how much the slices reached
# across each other.
INTRO = re.compile(r"^\s*(?:[-*>|]\s*)*\**\[?([A-Z]\d{1,2}[-.]\d{1,2})\b")


def harvest(path):
    """Every finding id in one report, with where it is introduced."""
    out = {}
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except Exception:
        return out
    slice_id = os.path.basename(path).split("-")[0]
    for n, line in enumerate(lines, 1):
        intro = INTRO.match(line)
        for fid in {m.replace(".", "-") for m in ID.findall(line)}:
            rec = out.setdefault(fid, {"id": fid, "slice": slice_id,
                                       "line": "", "severity": "",
                                       "headline": ""})
            if intro and intro.group(1).replace(".", "-") == fid and not rec["line"]:
                rec["line"] = n
                text = re.sub(r"[*`>#\[\]|]", " ", line).strip()
                rec["headline"] = re.sub(r"\s+", " ", text)[:220]
                sev = SEV.search(line)
                rec["severity"] = sev.group(1).lower() if sev else ""
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    wave = sys.argv[1].rstrip("/")
    home, cited = {}, {}
    for f in sorted(os.listdir(wave)):
        if not f.endswith(".md") or f in ("README.md", "VERIFIED.md",
                                          "STATUS.md", "FINDINGS.md"):
            continue
        for fid, rec in harvest(os.path.join(wave, f)).items():
            cited.setdefault(fid, set()).add(rec["slice"])
            if rec["line"] and fid not in home:
                home[fid] = rec
    # An id cited but never introduced is a cross-reference to a sibling's
    # finding, or a typo. Both are worth seeing, so they get a row.
    for fid, slices in cited.items():
        if fid not in home:
            home[fid] = {"id": fid, "slice": "|".join(sorted(slices)),
                         "line": "", "severity": "",
                         "headline": "CITED ONLY - introduced in no report"}
    rows = [home[k] for k in sorted(home)]

    # Has this finding been answered anywhere in the wave's own verification?
    # BY ID. Prose restatement is what let a quarter look like a whole.
    verified = ""
    for name in ("VERIFIED.md", "STATUS.md"):
        p = os.path.join(wave, name)
        if os.path.exists(p):
            verified += open(p, encoding="utf-8").read()
    for r in rows:
        r["verdict"] = "recorded" if r["id"] in verified else "NOT ADDRESSED"

    out = os.path.join(wave, "FINDINGS.csv")
    hdr = ["id", "slice", "line", "severity", "verdict", "headline"]
    text_rows = [[r[k] for k in hdr] for r in rows]

    if "--check" in sys.argv:
        import io
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\r\n")
        w.writerow(hdr)
        w.writerows(text_rows)
        cur = open(out, encoding="utf-8", newline="").read() if os.path.exists(out) else None
        if cur != buf.getvalue():
            print(f"  {out} does not match its reports. It is GENERATED - "
                  f"re-run this tool, do not edit it")
            print(f"FINDINGS: checked {len(rows)} | 1 problems")
            return 1
    else:
        with open(out, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, lineterminator="\r\n")
            w.writerow(hdr)
            w.writerows(text_rows)

    n_open = sum(1 for r in rows if r["verdict"] == "NOT ADDRESSED")
    print(f"FINDINGS: {len(rows)} findings from "
          f"{len({r['slice'] for r in rows})} slices | "
          f"{len(rows) - n_open} addressed by id | {n_open} NOT ADDRESSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
