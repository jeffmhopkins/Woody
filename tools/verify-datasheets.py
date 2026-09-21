#!/usr/bin/env python3
"""Verify every banked datasheet artefact matches its MANIFEST row, and that
nothing on disk is unaccounted for.

The rules this enforces, which are the ones datasheets/README.md states:
  - a row that claims a file must name a file that exists
  - a .pdf must actually start with %PDF and be big enough to be real
    (an HTML error page saved as .pdf is the failure this catches)
  - every file's SHA-256 must match the row that banked it
  - a row with no file must say why: BLOCKED or NOT-FETCHED, with a source_url
  - no artefact may sit on disk without a row

It deliberately checks non-PDF artefacts too - drawings, footprints, STEP
models - because those carry dimensions the design is built from.
"""
import csv, hashlib, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DS = os.path.join(ROOT, "datasheets")
# Everything a researcher may legitimately bank. A file on disk with any other
# extension is reported, not ignored.
ARTEFACT = (".pdf", ".dxf", ".step", ".stp", ".kicad_mod", ".kicad_pcb",
            ".jpg", ".jpeg", ".png", ".c", ".py", ".js", ".lib", ".asy")
NO_FILE_OK = {"BLOCKED", "NOT-FETCHED"}

rows = list(csv.DictReader(open(os.path.join(DS, "MANIFEST.csv"), newline="", encoding="utf-8")))
bad, ok, noted, listed = [], 0, 0, set()

for r in rows:
    part = (r.get("part") or "?").strip()
    status = (r.get("status") or "").strip().upper()
    fname = (r.get("file") or "").strip()

    if not fname:
        if status not in NO_FILE_OK:
            bad.append(f"{part}: status {status or '(empty)'} but no file - "
                       f"only {'/'.join(sorted(NO_FILE_OK))} may have no file")
        elif not (r.get("source_url") or "").strip():
            bad.append(f"{part}: {status} with no source_url recorded")
        else:
            noted += 1
        continue

    p = os.path.join(DS, fname)
    listed.add(os.path.relpath(p, DS))
    if not os.path.exists(p):
        bad.append(f"{part}: manifest names {fname} which does not exist")
        continue
    data = open(p, "rb").read()
    if fname.lower().endswith(".pdf"):
        if not data.startswith(b"%PDF"):
            bad.append(f"{part}: {fname} is not a PDF (probably an HTML error page)")
            continue
        if len(data) < 10240:
            bad.append(f"{part}: {fname} is {len(data)} bytes - too small to be real")
            continue
    elif len(data) < 256:
        bad.append(f"{part}: {fname} is {len(data)} bytes - too small to be real")
        continue
    claimed = (r.get("sha256") or "").strip()
    h = hashlib.sha256(data).hexdigest()
    if not claimed:
        bad.append(f"{part}: {fname} banked with no sha256")
        continue
    if claimed != h:
        bad.append(f"{part}: sha256 mismatch on {fname} "
                   f"(manifest {claimed[:12]}, file {h[:12]})")
        continue
    ok += 1

for dirpath, _, names in os.walk(DS):
    for n in names:
        if n.startswith("."):
            continue
        rel = os.path.relpath(os.path.join(dirpath, n), DS)
        if rel in ("MANIFEST.csv", "README.md") or rel in listed:
            continue
        if n.lower().endswith(ARTEFACT):
            bad.append(f"{rel}: artefact on disk with no MANIFEST row")
        else:
            bad.append(f"{rel}: unrecognised file in datasheets/")

print(f"datasheets: {ok} verified, {noted} recorded as blocked or not-fetched, "
      f"{len(bad)} problems")
for b in bad:
    print("  " + b)
sys.exit(1 if bad else 0)
