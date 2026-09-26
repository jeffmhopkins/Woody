# Verified by hand, by id

`CLAUDE.md`: *findings are claims.* Several in this repository's history have
been wrong, and one was wrongly marked disputed — which is worse, because a
wrong finding gets caught by the next reviewer while a finding filed as handled
does not. Nothing below is repeated onward until it appears here with its
verification.

**Recorded as each slice lands, not at the end.** The previous wave produced
377 findings and closed none of them by id, and `CLAUDE.md` records that as the
measured reason ten consecutive rounds were judged partial: verification
answered findings by restating them in prose, so "every one hand-verified" was
true of *reports* and false of *findings*.

## N6 — the master's directions, both ends

Slice reports 22 findings over 55 master nets and 151 endpoint assertions, with
nothing left unresolved. Four verified so far; the rest are unverified and must
not be acted on or repeated until they are.

| id | verdict | verification |
|---|---|---|
| N6 structural claim | **CONFIRMED, with one correction to its wording** | "Nothing in the repo compares the master to an `## Interfaces` table" is right in substance. `grep -rln Interfaces tools/` returns `tools/check-conservation.py`, so the claim as phrased overstates: that file *mentions* the table in a comment at line 118 and never reads one — it is a word-shingle conservation checker for a page split, taking `<rev> <source> <dest>...`. No tool reads a Dir or Peer cell as data. `[test]` |
| N6-1 | **CONFIRMED** | `hardware/carrier/circuit.yaml` does not exist; `grep -c "^\| Node \| Dir" hardware/carrier/carrier.md` = 0; `grep -rn "carrier/carrier" --include=circuit.yaml hardware/` exits 1. The id was invented by `hardware/carrier/netlist.yaml` and is the master's most-connected endpoint. `[test]` |
| N6-2 | **CONFIRMED** | `spi-link.md:38-40` carry Dir `out` on `SCLK`, `MOSI`, `CS_MOD` against `driver: carrier/carrier` in the master and `dir: in` in that circuit's own netlist. `[repo hardware/interfaces/spi-link/spi-link.md:38-40]` |
| N6-4 | **CONFIRMED, and sharper than reported** | `power-entry.md:29` lists `interfaces/spi-link` as a `DAC AVDD` receiver and states **"Not `module/digital-and-supervision`"** in bold, while the master now names that circuit a receiver because `R-PULL-SYNC.2` returns to the rail. The page's negation argues about the 74AHCT125's *supply* (bus +5 V), which is a different question from where a pull-up on its output returns — so the bold denial does not refute the new receiver, and one of the two still has to move. `[repo hardware/module/power-entry/power-entry.md:29]` |

**Not yet verified, not to be repeated:** N6-3, N6-5 through N6-22.

## Slices still running

N1, N2, N3, N4, N5, N7, N8.
