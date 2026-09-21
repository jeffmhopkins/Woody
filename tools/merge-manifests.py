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

ok = sum(1 for r in rows if r[6].upper().startswith("OK"))
blocked = sum(1 for r in rows if r[6].upper() == "BLOCKED")
print(f"MANIFEST.csv: {len(rows)} rows from {len(glob.glob(os.path.join(ROOT,'datasheets','.manifest-R*.csv')))} fragments "
      f"| {ok} ok, {blocked} blocked, {len(rows)-ok-blocked} other")
if superseded:
    print(f"  NOTE: {len(superseded)} BLOCKED/NOT-FETCHED row(s) name a part that is now banked "
          f"elsewhere in this manifest. They are kept as the record of the gap, not as a live gap:")
    for r in superseded:
        print(f"        - {r[0]}")
for p in problems:
    print("  PROBLEM:", p)
sys.exit(1 if problems else 0)
