# Datasheets and mechanical drawings

**Actual PDFs, not links.** Four review waves were degraded by every vendor
site being blocked at the egress proxy — dozens of findings are marked
`[from memory]` and several load-bearing numbers (the LT1641's `I_TIMER`, the
DAC8568 grade mapping, the OPA2197's output impedance, the KS-33's clip
dimension) have never been read off a real document. This directory is the fix.

## Rules

- **The PDF lives here.** A link is not a datasheet; the link rots and the
  proxy blocks it on the day you need it.
- **`MANIFEST.csv` has one row per part**, with the SHA-256 of the file, where
  it came from, and when. A file with no manifest row is untrusted.
- **A part that could not be fetched gets a row too**, with `status=BLOCKED`,
  the exact URL and the exact error. An honest gap is useful; a fabricated
  file is not.
- **Verify before committing**: `python3 tools/verify-datasheets.py`. It
  checks that every row's file exists, that a `.pdf` really begins with `%PDF`
  and is larger than 10 kB, that every SHA-256 matches, that a row with no
  file says why, and that nothing sits on disk without a row. Vendor sites
  commonly serve an HTML error page with a `.pdf` filename, which is the
  failure the magic-number check exists for.
- **Non-PDF artefacts are banked too** — dimensioned DXFs, STEP solids, KiCad
  footprints, vendor images — because they carry dimensions the design is
  built from. The KS-33's Z stack and the etherCON's screw pattern both came
  from these rather than from a datasheet.
- **Each researcher writes to `.manifest-R<N>.csv`**, and
  `python3 tools/merge-manifests.py` rebuilds `MANIFEST.csv` from the
  fragments. It is idempotent — edit a fragment, re-run, re-verify. Do not
  hand-edit `MANIFEST.csv`; it is generated.

## How to fetch anything at all from here

Six researchers converged on the same levers independently, so they are worth
writing down. **Every vendor and distributor host is blocked at the egress
proxy** — ti.com, analog.com, nxp.com, neutrik.com, gateron.com, waveshare,
mouser, digikey, alldatasheet, **and web.archive.org**. What works:

| Lever | Note |
|---|---|
| `git clone https://github.com/<owner>/<repo>` | Works for **any public repo**. Clone, then `find -iname '*.pdf'`. This is the main unlock. |
| `raw.githubusercontent.com/...` | Direct fetch of a known path, including binaries. |
| `media.githubusercontent.com/media/...` | **Git-LFS objects.** `raw` returns only a ~130-byte pointer; swapping the host returns the real bytes. |
| The GitHub MCP `search_code` tool | The only working search. `api.github.com/search/code` is scoped to this repo. |
| GitLab's unauthenticated REST API | `/projects?search=` and `/repository/tree?recursive=true` give real listings. Blob search needs a token. |

**GitHub indexes no binaries.** `extension:pdf` and `path:**/*.pdf` always
return zero. The productive search is for *text* files that reference a PDF
beside them — READMEs, BOMs, manifests — and for Git-LFS pointer files, which
are text and therefore path-indexed.

## What is still missing, and why it matters

Seventeen rows are `BLOCKED` or `NOT-FETCHED`. Three of them block real
decisions:

- **LT1641-1** (`164112fc.pdf`) — `C-TIMER`, `C-GATE` and the new `R-FB-HI` /
  `R-FB-LO` divider all rest on search-index text rather than a document.
- **SP0504BAHT** — the TVS array's power rating has never had a source.
- **A ferrite bead with an impedance-vs-DC-bias curve.** A researcher
  deliberately declined to bank a Würth part that has no bias curve at all,
  on the grounds that a datasheet which cannot answer the question is worse
  than the gap. That judgement is right and worth preserving.

The rest are second sources, substitutes and mechanical drawings whose absence
is recorded in the relevant BOM row.

## Provenance and licence

These are third-party copyrighted documents, redistributed here for a
one-off personal build so that the design can be verified offline. They are
not covered by this repository's own licence (ADR 0011). Each manifest row
records its source.
