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
- **Verify before committing**: the file must begin with `%PDF`, be larger
  than 10 kB, and contain the part number in its extracted text. Vendor sites
  commonly serve an HTML error page with a `.pdf` filename.

## Provenance and licence

These are third-party copyrighted documents, redistributed here for a
one-off personal build so that the design can be verified offline. They are
not covered by this repository's own licence (ADR 0011). Each manifest row
records its source.
