#!/usr/bin/env python3
"""Merge datasheets/.manifest-R*.csv fragments into datasheets/MANIFEST.csv.

The six researchers wrote to separate fragments to avoid a write race. This is
idempotent: it rebuilds MANIFEST.csv from the fragments every time, so rerunning
it after a fragment changes is the whole update procedure.
"""
import csv, glob, io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HDR = ["part", "manufacturer", "file", "sha256", "source_url", "fetched", "status", "notes"]

rows, seen, problems = [], set(), []
for frag in sorted(glob.glob(os.path.join(ROOT, "datasheets", ".manifest-R*.csv"))):
    name = os.path.basename(frag)
    with open(frag, newline="", encoding="utf-8") as fh:
        rdr = list(csv.reader(fh))
    if not rdr:
        problems.append(f"{name}: empty"); continue
    if [c.strip() for c in rdr[0]] != HDR:
        problems.append(f"{name}: header is {rdr[0]}, expected {HDR}"); continue
    for i, r in enumerate(rdr[1:], 2):
        if not any(r):
            continue
        if len(r) != len(HDR):
            problems.append(f"{name}:{i} has {len(r)} columns, expected {len(HDR)}"); continue
        # Fragments disagree on what `file` is relative to: some wrote
        # "datasheets/connectors/x.pdf" (repo root), others "connectors/x.pdf".
        # The manifest's own convention is relative to datasheets/, so
        # normalise here rather than teaching the verifier both spellings.
        r[2] = r[2].strip()
        if r[2].startswith("datasheets/"):
            r[2] = r[2][len("datasheets/"):]
        key = (r[0], r[2])
        if key in seen:
            problems.append(f"{name}:{i} duplicate part+file {key}"); continue
        seen.add(key)
        rows.append(r)

rows.sort(key=lambda r: (r[2] or "zzz", r[0]))
out = io.StringIO()
w = csv.writer(out, lineterminator="\n")
w.writerow(HDR); w.writerows(rows)
open(os.path.join(ROOT, "datasheets/MANIFEST.csv"), "w", encoding="utf-8").write(out.getvalue())

# A BLOCKED row is an honest gap when it is written and a LIE once someone
# banks the part. The fragments are per-researcher and append-only by
# convention - an earlier researcher's fragment is their record and is not
# edited - so the same part legitimately appears twice, once BLOCKED with no
# file and once OK with one. That is fine in the fragments and misleading in
# the generated MANIFEST, where a reader greps for BLOCKED to find the gaps.
# Report it rather than rewriting it: the row stays, the reader is told.
banked = {r[0].strip().lower() for r in rows if r[2] and r[6].upper().startswith("OK")}
superseded = [r for r in rows
              if not r[2] and r[6].upper() in ("BLOCKED", "NOT-FETCHED")
              and r[0].strip().lower() in banked]

# Exact part-string match is not enough, and under-reporting is the dangerous
# direction: a later researcher banks the same part under a more specific name
# ("Ferrite bead 600R@100MHz 1206 (FB-IN, chosen part)" vs the blocked
# "Ferrite bead >=1A 600R@100MHz"), the strings differ, and the blocked row
# goes on reading as a live gap. That happened three times between R7 and R8
# and nearly cost a wave of agents re-fetching documents already on disk.
#
# Two further rules, in order of trust:
#   DECLARED - an OK row quotes the blocked row's exact part string in its
#              notes. Zero false positives, and it is the one a researcher can
#              deliberately opt into: quote the row you are closing.
#   LIKELY   - shared distinctive tokens. A heuristic, reported as "check",
#              never as fact, because the tempting near-misses here are
#              WS2812B-0807 against WS2812B-2020 and the WS2815 strip against
#              the WS2815 IC - different dies and different products, and
#              silently conflating them is the exact defect this repo exists
#              to prevent.
def _tokens(part):
    out, cur = set(), []
    for ch in part.lower():
        if ch.isalnum():
            cur.append(ch)
        elif cur:
            out.add("".join(cur)); cur = []
    if cur:
        out.add("".join(cur))
    # Structural words describe the KIND of document, not which part it is for.
    GENERIC = {"drawing", "vendor", "datasheet", "sheet", "series", "route",
               "second", "source", "alternative", "chosen", "part", "spec",
               "specification", "manual", "note", "application", "mating",
               "half", "and", "the", "for", "with", "curve"}
    return {t for t in out if len(t) >= 3 and t not in GENERIC}

_freq = {}
for r in rows:
    for t in _tokens(r[0]):
        _freq[t] = _freq.get(t, 0) + 1

DISTINCTIVE = 6      # a token in more than this many rows names a category
_ok = [r for r in rows if r[2] and r[6].upper().startswith("OK")]
_exact = {id(r) for r in superseded}
declared, likely = [], []
for r in rows:
    if r[2] or r[6].upper() not in ("BLOCKED", "NOT-FETCHED") or id(r) in _exact:
        continue
    part = r[0].strip()
    # "SUPERSEDES" must be present too: plenty of rows legitimately MENTION a
    # part without closing its gap. The Waveshare schematic names WS2812B-0807
    # on every one of its 64 symbols and is emphatically not its datasheet.
    hit = next((o for o in _ok
                if part and part in o[7] and "SUPERSEDES" in o[7].upper()), None)
    if hit is not None:
        declared.append((r, hit)); continue
    rt = {t for t in _tokens(part) if _freq.get(t, 99) <= DISTINCTIVE}
    best, shared = None, set()
    for o in _ok:
        common = rt & _tokens(o[0])
        if len(common) > len(shared):
            best, shared = o, common
    # Two distinctive tokens, or one token so rare it occurs only in this pair.
    if best is not None and (len(shared) >= 2 or any(_freq.get(t) == 2 for t in shared)):
        likely.append((r, best, sorted(shared)))

def norm(s):
    # Historical-row detection used exact lowercase equality and under-reported
    # by three: "MPXV4006 AN1646" never matches "MPXV4006DP", and a row whose
    # part carries a parenthetical or a suffix never matches its own bank.
    return "".join(c for c in s.lower() if c.isalnum())


banked = {norm(r[0]) for r in rows if r[6].upper().startswith("OK") and r[2]}
historical = []
for r in rows:
    if r[6].upper().startswith("OK") or not r[0]:
        continue
    n = norm(r[0])
    if any(n == b or n in b or b in n for b in banked):
        historical.append(r[0])

ok = sum(1 for r in rows if r[6].upper().startswith("OK"))
blocked = sum(1 for r in rows if r[6].upper() == "BLOCKED")
print(f"MANIFEST.csv: {len(rows)} rows from {len(glob.glob(os.path.join(ROOT,'datasheets','.manifest-R*.csv')))} fragments "
      f"| {ok} ok, {blocked} blocked, {len(rows)-ok-blocked} other")
if superseded:
    print(f"  NOTE: {len(superseded)} BLOCKED/NOT-FETCHED row(s) name a part that is now banked "
          f"elsewhere in this manifest. They are kept as the record of the gap, not as a live gap:")
    for r in superseded:
        print(f"        - {r[0]}")
if declared:
    print(f"  SUPERSEDED (declared): {len(declared)} row(s) whose part string a banked row quotes:")
    for r, o in declared:
        print(f"        - {r[0]}  ->  {o[2]}")
if likely:
    print(f"  CHECK: {len(likely)} BLOCKED/NOT-FETCHED row(s) LOOK superseded by a banked row under a "
          f"different name. This is a heuristic - confirm the die and the product before believing it:")
    for r, o, shared in likely:
        print(f"        - {r[0]}")
        print(f"            possibly covered by: {o[0]}  ->  {o[2]}")
        print(f"            shared: {', '.join(shared)}")
for p in problems:
    print("  PROBLEM:", p)
sys.exit(1 if problems else 0)
