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

ok = sum(1 for r in rows if r[6].upper().startswith("OK"))
blocked = sum(1 for r in rows if r[6].upper() == "BLOCKED")
print(f"MANIFEST.csv: {len(rows)} rows from {len(glob.glob(os.path.join(ROOT,'datasheets','.manifest-R*.csv')))} fragments "
      f"| {ok} ok, {blocked} blocked, {len(rows)-ok-blocked} other")
for p in problems:
    print("  PROBLEM:", p)
sys.exit(1 if problems else 0)
