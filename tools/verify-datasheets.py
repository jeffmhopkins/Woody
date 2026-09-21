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
import csv, hashlib, os, re, sys

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

# A row-vs-file check is blind to the gap that matters most: a BOM part that
# has no manifest row AT ALL. The ESP32-S3, the QMI8658C and the PESD12VS1UB
# were all hiding in exactly that blind spot - named parts, real manufacturers,
# invisible to every tool because nothing was looking for an absence.
def _norm(s):
    return "".join(c for c in (s or "").lower() if c.isalnum())


uncovered = []
bom = os.path.join(ROOT, "hardware/bom.csv")

# A MISSING bom.csv SKIPPED THE COVERAGE CHECK SILENTLY. The `if os.path.exists`
# below was written to tolerate a tree without a BOM, but the effect is that
# moving or renaming bom.csv turns the whole BOM-coverage half of this tool off
# and still prints a clean summary. During a restructure that is precisely the
# wrong default: the one moment coverage most needs checking is the moment the
# path is most likely to be wrong. Say so loudly instead.
if not os.path.exists(bom):
    sys.exit(f"REFUSING TO REPORT: {os.path.relpath(bom, ROOT)} not found, so "
             f"BOM coverage cannot be checked and a clean summary here would "
             f"be a lie about half this tool's job. If the BOM moved, update "
             f"this path.")

if os.path.exists(bom):
    # Match against the WHOLE manifest, not just its part column: a document is
    # often banked under a different name from the BOM's ("KS-33 Red (linear)"
    # vs "Gateron KS-33 low-profile switch"), and its notes name the real MPN.
    hay = _norm(" ".join(" ".join(r.values()) for r in rows))
    # Same text with word boundaries intact, for the refdes test below. _norm
    # deletes the delimiters, so a whole-token match is impossible against hay.
    hay_tok = re.sub(r"[^a-z0-9]+", " ",
                     " ".join(" ".join(r.values()) for r in rows).lower())
    for r in csv.DictReader(open(bom, newline="", encoding="utf-8")):
        part = (r.get("part") or "").strip()
        if not part or part.upper().startswith("TBD") or "(NONE" in part.upper():
            continue
        # A manufacturer part number is the thing a datasheet can exist for.
        # Take the longest alphanumeric-mixed token as the fingerprint; a bare
        # value like "10k 1%" has none, which is correctly not our problem.
        # A value with a unit ("330nF", "500mW", "10k") has digits and letters
        # but is not a part number, and flagging it trains people to ignore the
        # check. Require length, and reject the value-with-unit shape.
        toks = [t for t in re.split(r"[^A-Za-z0-9]+", part)
                if len(t) >= 6 and any(c.isdigit() for c in t)
                and any(c.isalpha() for c in t)
                and not re.fullmatch(r"\d+[a-zA-Z]{1,3}", t)]
        if not toks:
            continue
        if any(_norm(t) in hay for t in toks):
            continue
        # A manifest row that names the REFDES it covers is coverage, even when
        # no part-number token matches. This is the case a part number cannot
        # reach: the document is a vendor catalogue covering a whole family, and
        # the specific MPN is chosen later, out of that catalogue. Banking it
        # under "... (SW-POWER) - NKK Series M" is the right thing to do and the
        # token test punished it. Require the refdes as a whole token so that
        # e.g. "D1" does not match "D10".
        ref = (r.get("ref") or "").strip()
        ref_tok = re.sub(r"[^a-z0-9]+", " ", ref.lower()).strip()
        if ref_tok and re.search(r"(?<![a-z0-9])%s(?![a-z0-9])"
                                 % re.escape(ref_tok), hay_tok):
            continue
        uncovered.append(f"{r.get('ref')}: {part}")

print(f"datasheets: {ok} verified, {noted} recorded as blocked or not-fetched, "
      f"{len(bad)} problems")
if uncovered:
    print(f"  BOM parts with NO manifest row at all ({len(uncovered)}) - "
          f"not a failure, but nothing else will ever mention them:")
    for u in uncovered:
        print("    " + u)
    print("  Clear each by banking the document or adding a BLOCKED row.")
for b in bad:
    print("  " + b)
sys.exit(1 if bad else 0)
