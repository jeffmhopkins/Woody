# Restructure design wave — method

**Opened 2026-09-21.** Six cold agents, run in parallel, each asked to *propose*
rather than to review. This wave produces a target structure and a standard;
it changes no corpus file.

## Why a wave rather than just doing it

The restructure moves every path in the repository: 33 `owner:` paths in
`config/figures.yaml`, 52 Markdown links, ~194 backtick path references, the
`CORPUS_DIRS` list inside `tools/check-staleness.py`, and every path in
`datasheets/MANIFEST.csv`. The project's one recorded failure mode is a value
changing and its derived statements not following. **A restructure is that
failure mode with every path in the repository as the value.**

## Constraints handed to every agent, decided before the wave opened

1. **Content freeze.** Move and split only. No technical change, no renumbered
   value, no resolved finding. A restructure diff that changes no numbers is
   mechanically checkable; one that also fixes things is not.
2. **Fragments generate the master.** Per-circuit `bom.csv` is the source;
   `hardware/bom.csv` becomes generated, on the pattern `.manifest-R*.csv` →
   `merge-manifests.py` → `MANIFEST.csv` already established here.
3. **Circuit blocks are the primary axis**, with thin board pages above them.
   `breath` crosses two boards and the umbilical; slicing by board splits that
   chain, which is the shape that produces the defect this repo is organised
   against.

## Cold rules, unchanged from prior waves

- Agents may not read `docs/review/**` — including this file's siblings.
  Agreement between agents who cannot see each other is evidence; agreement
  with a document they just read is not.
- **Provenance on every claim** — `[repo]` with the path and line, `[calc]`
  with the arithmetic shown, `[web]` with the URL, `[from memory]`. An unmarked
  claim is a defect in the report.
- Sliced by design question, not by file.

## Slices

| ID | Question |
|---|---|
| **D1** | Circuit inventory — what the distinct blocks are, and which line ranges of which files each one is made of |
| **D2** | The circuit directory standard — what files, what each owns, and where a decision lives |
| **D3** | The revision and staleness paradigm, and the checker that enforces it |
| **D4** | BOM fragment format and generator; `datasheets/` de-duplication |
| **D5** | Migration mechanics — every reference that breaks on a move, and what must deliberately not be fixed |
| **D6** | The ADR boundary — what, if anything, moves out of the fourteen ADRs |

`VERIFIED.md` records what was checked by hand afterwards and where an agent
was wrong. A report is a claim, not a fact.
