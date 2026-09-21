#!/usr/bin/env python3
"""Verify every PDF in datasheets/ is a real PDF and matches its manifest row."""
import csv, hashlib, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DS = os.path.join(ROOT, "datasheets")
rows = list(csv.DictReader(open(os.path.join(DS, "MANIFEST.csv"), newline="")))
bad, ok, blocked = [], 0, 0
listed = set()
for r in rows:
    if r["status"].strip().upper() == "BLOCKED":
        blocked += 1
        if not r["source_url"].strip():
            bad.append(f"{r['part']}: BLOCKED with no source_url recorded")
        continue
    p = os.path.join(DS, r["file"])
    listed.add(os.path.relpath(p, DS))
    if not os.path.exists(p):
        bad.append(f"{r['part']}: manifest names {r['file']} which does not exist"); continue
    data = open(p, "rb").read()
    if not data.startswith(b"%PDF"):
        bad.append(f"{r['part']}: {r['file']} is not a PDF (probably an HTML error page)"); continue
    if len(data) < 10240:
        bad.append(f"{r['part']}: {r['file']} is {len(data)} bytes - too small to be real"); continue
    h = hashlib.sha256(data).hexdigest()
    if r["sha256"].strip() and r["sha256"].strip() != h:
        bad.append(f"{r['part']}: sha256 mismatch (manifest {r['sha256'][:12]}, file {h[:12]})"); continue
    ok += 1
for dirpath, _, names in os.walk(DS):
    for n in names:
        if n.lower().endswith(".pdf"):
            rel = os.path.relpath(os.path.join(dirpath, n), DS)
            if rel not in listed:
                bad.append(f"{rel}: PDF on disk with no MANIFEST row")
print(f"datasheets: {ok} verified, {blocked} recorded as blocked, {len(bad)} problems")
for b in bad:
    print("  " + b)
sys.exit(1 if bad else 0)
