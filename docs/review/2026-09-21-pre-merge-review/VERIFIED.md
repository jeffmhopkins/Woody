# Verified by hand — pre-merge wave

A finding is a claim. This file records what was checked against the corpus
and where an agent was right or wrong. Checked as reports land; the wave is
still running.

## A3 — mod channels

| Claim | Check | Verdict |
|---|---|---|
| **M5** — "DAC channel 7" is never mapped to the DAC8568's address field, leaving it ambiguous by one channel (DAC-G `0110` vs DAC-H `0111`) on the node that sets the intercept of four jacks | `grep -rn "DAC-G\|DAC-H\|A3..A0\|0110\|0111"` across `hardware/`, `docs/decisions/`, `firmware/`, `config/` | **Confirmed. Zero hits.** The corpus names a channel by an ordinal that the datasheet does not use, with no `MISO` to catch a wrong write |

Not yet checked: M1 (the drawing's column positions), M2 (the buffer-load
model and the missing sink case), M3 (the `CLR` grade attribution), M4, M6,
M7, M8, S1–S3.

## A8 — grounding

| Claim | Check | Verdict |
|---|---|---|
| **Incidental** — `ROADMAP.md:53` carries a live `8HP`, and none of `panel-width`'s five forbidden patterns matches the spelling `at 8HP rather than` | Read the line; compared against the five patterns | **Confirmed.** The line reads "good practice **at 8HP** rather than the structural necessity it was at 6HP", describing a panel width that was superseded by 10HP. The five patterns are `panel is 40.34 mm`, `The panel is 8HP`, `inside 8HP`, `at 8HP this`, `Comfortable at 8HP` — **`at 8HP rather than` matches none**, and the checker reports PASS. **The fifth recorded escape of this exact class**, and it is in the file a builder follows at E12 |
| **F4-3** — all three line citations in `dig-gnd-topology`'s `candidates` are stale | Opened each cited line | **Confirmed, all three.** `0004:627` is mid-sentence about cents of error; the claim it cites is at **:637**. `digital-and-supervision.md:53` is a row of an ASCII drawing about `OE`; the claim is at **:60**. A line number is a path with different syntax, and nothing checks these |

Not yet checked: F1 (the jack sleeve and panel as an unassigned second
ground — needs a real part), F4-1/4-2 (ADR 0004 vs `power-entry.md`, and
`ROADMAP.md` as an undeclared fourth document), F5/F2, F6, F6-1/6-3, F9,
F-AGND-2, F3-1.

### Note on F4-3's significance

The `dig-gnd-topology` entry's own `note` field says *"power-entry.md states
that ADR 0004 was corrected on this point. IT WAS NOT — line 627 still says
the opposite."* That note is right about the substance and wrong about the
line, which is the failure mode one level up: **the record of the defect has
itself gone stale.**

## A1 — breath chain

| Claim | Check | Verdict |
|---|---|---|
| `U-DIFFRX`'s BOM row carries a live `-9.6V`, a **forbidden** value of `inamp-full-scale`, escaping because the list spells it with a space | Read the row; compared to the four patterns | **Confirmed, and worse than reported.** The row says *"Output is 0V at rest to **-9.6V** at full"*. The forbidden patterns are `-9.6 V`, `−9.6 V`, `-10.05 V`, `−10.05 V` — all four carry a space before the `V`. **The corpus spells it without one.** The register's own note says −9.6 V "is derived from nothing and matches no configuration", and it is live on the in-amp's own row while `check-staleness.py` reports PASS |

**This is the sixth recorded escape of this class, and the second found
today.** The mechanism is identical every time and is written down in two
places in this repository: a forbidden pattern is a case-sensitive literal,
and the corpus spells its numbers more ways than the person writing the list
imagines. Today the spelling was one absent space.

## B5 — firmware contract

| Claim | Check | Verdict |
|---|---|---|
| `firmware/README.md` contradicts itself about where the display runs, inside the list it calls "not negotiable" | Read both bullets | **Confirmed.** Bullet 2: "Display renders on the other core, on its own SPI host." Bullet 5, three lines later: "WiFi and the display are on the other MCU." Both are in the same non-negotiable list |

Not yet checked: the twelve absent obligations, the SPI-host exhaustion
claim, the IMU I2C arithmetic, and the four further staleness escapes B5
reports.

## Cross-cutting, from four reports that could not see each other

Three agents independently report the same structural cause: **BOM rows were
assigned by matching reference-designator strings, so parts the drawings
label differently fell into `unplaced.csv`** — `U-DIFFRX`, `R-GAIN-INAMP`,
`C-FILT-BREATH` and others are *drawn* and filed as undrawn. A1 adds the
consequence that matters: **every staleness escape it found is in a file the
chain's own pages do not reach.** The misfiling did not create the stale
values, but it put them where no reader of the breath chain would look.

That assignment rule is mine, from this session.

## B4 — ADRs vs drawn reality

| Claim | Check | Verdict |
|---|---|---|
| **B4-01** — ADR 0004 withdraws the frame watchdog at `:484` and then reasons from it as live at `:523` | Read both lines; tested whether `:516-524` sit inside the withdrawal blockquote | **Confirmed, and the structure is the point.** `:484` opens `> **Withdrawn 2026-09-21.**`. Lines 516–524 are **plain prose, not quoted** — outside the withdrawal — and `:523` reads "the MCU dies, SPI stops, `CLR` fires, and breath keeps working." With no watchdog, `CLR` does not fire. **This is the exact class `CLAUDE.md` §5 names as the one no grep can find**, and it is the same watchdog, in a different document, still live |
| **B4-14** — `key-pullup-qty`'s forbidden pattern `"Twenty-one sets"` matches a **true** sentence, and is masked only by an accident of line wrapping | Read the pattern and `0001:217` | **Confirmed.** The line reads "…rather than 265 mm of loom. Twenty-one sets across the". The statement is correct — 21 networks and 24 pull-ups are different quantities — and the only reason the hook is silent is that `rather than` happens to share the line and counts as refutation wording. **Reflow that paragraph and the checker starts failing on a correct statement**, whose cheapest "fix" is to make it wrong |

## A2 — pitch chain

| Claim | Check | Verdict |
|---|---|---|
| **P2** — there is no decoupling capacitor on `VREFOUT` anywhere in the BOM, on the node where 1 mV is 1.2 cents | `grep -i vrefout hardware/bom.csv` | **Confirmed on the corpus side.** The only rows naming `VREFOUT` are the op-amp, the offset trimmer and a series resistor. No capacitor. **The datasheet half I could not verify myself** — `pypdf` fails in this container with a `_cffi_backend` error, so I could not re-read the cited pages. A2's datasheet citations for P1 and P2 stand as its claims, not as my verification |

Not yet checked: P1 (the 3-stated `VREFOUT` at power-on, which refutes three
separate statements about what the pitch jack does), P3 (the LT5400 outside
the clamp), P4, P6–P14.

### A note on the tooling, for whoever picks this up

`pypdf` is broken in this container. `docs/reference/repo-maintenance.md` §3
records `python3 -c "import pypdf"` as the working extraction route "used for
every extraction in this session" — **that is no longer true here**, and any
agent told to verify a datasheet claim will hit it. `pdftotext` was already
recorded as not installed in every session. Whoever re-verifies B3's slice
needs a working reader first.

## B1 / A4 — the seventh spelling of the refuted sensor transfer function

Two agents that could not see each other filed this independently.

| Claim | Check | Verdict |
|---|---|---|
| `docs/decisions/0005-power-architecture.md:74` carries the **refuted** `0.2–4.7 V` sensor output as live fact, in a spelling no `forbidden` pattern matches | Extracted the literal from the line; compared byte for byte against all 27 patterns on `sensor-full-scale` | **Confirmed.** The line holds `0.2–4.7 V` — U+2013, **no spaces**. The register has `0.2-4.7 V` (ASCII hyphen), `0.2 – 4.7 V` (en dash *with* spaces) and `0.2–4.80 V` (tight en dash, but the 4.80 value). The tight-en-dash `4.7` form is the one nobody wrote. Zero hits; checker PASS |

`CLAUDE.md` names `sensor-full-scale` as the worst recorded case of this
class and says the corpus spelled one number **seven** ways. This is the
eighth, in the same figure, found after three review waves and a restructure.

## A10 / B1 — two more single-character escapes

| Claim | Check | Verdict |
|---|---|---|
| `ROADMAP.md:203` says **"Six conductors per hop"**; `chain-conductors` is **12** | Read the line; compared against all five patterns | **Confirmed.** The list holds `six conductors per hop`, `SIX conductors per hop`, `6 conductors per hop` — and, in Title case, `Six conductors leave`. So Title case *was* considered, for the other spelling. The miss is one letter. The row is the one that asks "does the chained key loom fit the side channel?" and gates it "before the plate DXF is cut" |
| `hardware/bom.csv:62` and `hardware/module/panel-led/bom.csv:2` carry the **retired** four-row panel budget | Read both rows; compared against `panel-height-budget`'s nine patterns | **Confirmed, four values, four misses, each by one removed space.** The rows spell `~115mm against ~110mm usable`, `107mm of ~110mm`, `= 97mm, 13mm spare`; every pattern spells `NN mm`. And this is the generated master plus its fragment, so the same stale text is in the repository twice |

## A7 / A4 — the DAC threshold is read off the wrong datasheet row

| Claim | Check | Verdict |
|---|---|---|
| `0004:209` justifies the level shifter with "the DAC's **0.7 × AVDD** input threshold — **3.65 V** at AVDD = 5.21 V"; SBAS430E splits that parameter and the module is in the other half | Re-read the banked `datasheets/analog/DAC8568CIPW.pdf` p.4 directly | **Confirmed.** p.4 gives `VINH` as **two rows**: `2.7V≤AVDD<4.5V → 0.7×AVDD` and `4.5V≤AVDD≤5.5V → 0.625×AVDD`. The LM317 rail is 5.21 V, so the binding figure is **0.625 × 5.21 = 3.26 V**, not 3.65 V. p.53's own revision history records TI splitting it into two rows. **The conclusion survives** — 3.3 V CMOS still cannot drive it — but the number that carries the argument is wrong by 0.39 V, on the ADR that owns the link |

## B2 — the DAC order code does not exist

| Claim | Check | Verdict |
|---|---|---|
| `U-DAC`'s part number `DAC8568CIPW` is not an orderable device | Searched the banked datasheet's own Package Option Addendum | **Confirmed. Zero occurrences of `DAC8568CIPW` in the whole document.** p.54–57 enumerate `DAC8568IAPW / IBPW / **ICPW** / IDPW` and their `R` reel variants. The `I` and the grade letter are transposed; the C grade orders as **`DAC8568ICPW`**, which appears nowhere in this corpus |

This one propagated further than a value normally does: it is in
`hardware/bom.csv`, in `0006:176` and `:179`, in `datasheets/MANIFEST.csv`,
and **in the banked file's own name** — so the datasheet is filed under a part
number that does not exist. The manifest row beside it says the grade table
was "verified verbatim", which it was. Nobody checked the line above it.

## A9 — the strips' per-LED current, and a refutation that stopped 284 lines short

| Claim | Check | Verdict |
|---|---|---|
| The strip power figures rest on a per-LED current that no banked document supports | Read `datasheets/led/WS2815.pdf` p.3 directly; recomputed from `0014:132` | **Confirmed.** `0014:132` gives `60/m (50 LEDs) | 1.01 A` — **20.2 mA/LED** `[calc]`. The banked WS2815 datasheet p.3 states **`RGB Channel Constant Current 15 mA`**, i.e. **45 mA/LED** at full white — **2.23× higher**. The same page's `Quiescent Current 2.1 mA` reproduces ADR 0005's 123 mA exactly, so the two numbers in the corpus have different sources and only one of them is the datasheet |
| The corpus already knows this class of error | Read `0014:416` | **Confirmed, and this is the finding.** At `:416` the corpus says of the *matrix* figure: "**this is the wrong part's figure and it is at least 2.4× too low**". That refutation is 284 lines below the strip table at `:153`, which still reads `Both strips full white at 60/m | 12.1 W | ~36 K` with no flag. At 45 mA/LED the same row is **≈27 W and ≈81 K** `[calc]` |

`~36 K` is the number the ~3 W lighting clamp was sized to avoid, so the
strip row is not decorative — it is the load case the clamp exists for.
**The fix landed where the editing was happening and not where the reader
looks**, in the ADR that owns lighting.

## A6 — the path map is itself stale, in 22 of 287 rows

| Claim | Check | Verdict |
|---|---|---|
| `docs/reference/path-map-2026-09-21.csv` calls the `74HC165` datasheets "unmoved" when they moved | Resolved every `datasheets/…` path cited anywhere in the design corpus | **Confirmed, and it is broader than the three rows filed.** Of 88 distinct `datasheets/` paths cited in the corpus, **22 resolve to nothing — and all 22 are in the path map**, every one with `kind=unmoved` and `old == new`. The files were re-filed by function (`datasheets/logic/`, `/led/`, `/analog/`) and the map was not updated. Two rows are wrong about the filename as well, not just the directory: the map names `74HC165-toshiba.pdf` and `74HC165.pdf`; the bank holds `74HC165-toshiba-1986-excerpt.pdf` and `74HC165-ti-scls116e.pdf` |

This is mine, and it is a new shape. `CLAUDE.md` §6 says paths in the
historical records "are not to be corrected — resolve them through
`repo-maintenance.md` §7", and §7 points at this map. **The documented
mechanism for resolving stale paths is itself stale**, and silently: an
`unmoved` row has `old == new`, so `rewrite-paths.py --verify` has nothing to
look for, and `check_links` only reads markdown links, not CSV cells. Every
check passes.

It is also the same failure as the ones above, one level up: not a value that
went stale, but **the table that exists to resolve stale values**.

## A2 — a correction to this file

The note at the end of the A2 section says `pypdf` is broken in this
container. **That is wrong, and it mattered** — it would have told the next
reader that B3's whole slice was unverifiable.

`pypdf` works. What fails is the system `cryptography` package's Rust
binding, which `pypdf` imports eagerly and only needs for *encrypted* PDFs.
Stubbing the module out before the import makes extraction work on every
banked document:

```python
import sys, types
for m in ('cryptography', 'cryptography.hazmat', 'cryptography.exceptions',
          'cryptography.hazmat.primitives',
          'cryptography.hazmat.primitives.ciphers',
          'cryptography.hazmat.primitives.padding',
          'cryptography.hazmat.backends'):
    sys.modules[m] = types.ModuleType(m)
import pypdf
```

Four of the verifications above were done this way. `repo-maintenance.md` §3
needs this rider, and that edit is **held pending the merge decision** rather
than taken now, because the corpus is under a content freeze and making an
exception for my own convenience is how freezes stop meaning anything.

## A5 / A4 / C3 — the umbilical branch: three cold agents, one topology contradiction

The strongest convergence in this wave. Three agents on three different
slices, none able to see the others, filed the same defect from three sides.

| Claim | Check | Verdict |
|---|---|---|
| Both Interfaces tables say the umbilical branch is taken **before** the entry diodes; the drawing, the part counts and a **settled** tracked figure all require it **after** `D2` | Read both rows, the `D-REVPOL` and `FB-IN` BOM rows, and `ferrite-bias-impedance`'s derivation | **Confirmed, and one side of it is settled.** `power-entry.md:28` and `umbilical-load-switch.md:15` both say "taken **before** the diodes, which is the point of the split". Against that: `D-REVPOL` is **qty 3**; `FB-IN` is qty 4 and its note enumerates "One per branch: +12V analog, **+12V umbilical**, −12V, +5V"; and `ferrite-bias-impedance` — **status settled** — derives FB2's 280–310 Ω from "**FB2 carries `umbilical-current` (359 mA)**", distinct from the module's own 392 mA. If the tables are right, FB2 carries nothing and a settled figure is wrong |

Why it is the wave's most consequential finding rather than one more stale
sentence:

- **The two halves agree with each other**, because the same sentence was
  copied into both pages during the split. Cross-checking the two ends —
  the thing the `## Interfaces` tables exist for — returns agreement.
- **It is a layout instruction.** Followed at layout it deletes reverse
  protection on the 359 mA branch and leaves `D2`/`FB2` as dead copper.
- A5 computed the consequence the other way: with `D2` + `FB2` in the path,
  the load switch's `FB`-divider worst-case margin falls from the **0.4 V**
  it was chosen to have to **0.05–0.11 V**.
- **Both parts are in `unplaced.csv` as well** — `D-REVPOL` and `FB-IN` are
  in the file that counts "parts nobody has drawn", while being the parts the
  power-entry drawing is mostly made of.

Nothing here says which topology is correct. It needs a decision, not an edit.

## C4 — two netlist shorts in the tables written to prevent netlist shorts

| Claim | Check | Verdict |
|---|---|---|
| **F5** — `module/dac8568`'s `SCLK`/`DIN`/`SYNC` has two declared drivers | Compared the two rows | **Confirmed, and they are byte-identical.** `spi-link.md:42` and `digital-and-supervision.md:27` both read "`SCLK`, `DIN`, `SYNC` … out … `module/dac8568` … Buffer outputs. The DAC-side three of the six `R-SPI-PULL` sit on these". The buffer is physically on `digital-and-supervision` — **`spi-link.md:43` says so itself**, one row later, when explaining why the +5 V open item stayed over there. So `spi-link` claims to source three nets that do not cross its own boundary |
| **N2** — `bus +5V` has two mutually exclusive sources | Read all three tables and the drawing | **Confirmed.** `power-entry.md:27` exports "bus `+5V` **after `FB4`/`C4`**" to `module/digital-and-supervision`, and its drawing at `:74` shows `+5V ├──[FB4]──[C4 47µF]──── 74AHCT125 only`. Both receiving tables — `digital-and-supervision.md:28` and `spi-link.md:43` — say the rail comes straight from the "Eurorack bus header", naming no bead, no capacitor and no peer circuit. A transcription gets **two nets both called bus +5 V**, one filtered and one not, and no DRC can say which is real. The BOM sides with `power-entry`: `FB-IN` is qty 4 and one of the four is the +5 V branch |

The second one is not only a naming problem. Whether that rail has 47 µF on
it is what decides how long the buffer stays powered after `AVDD` collapses —
the sequencing hazard A4 and C3 filed independently.

## B1 / B2 — four tracked figures are owned by the generated file

| Claim | Check | Verdict |
|---|---|---|
| Four `figures.yaml` entries name `hardware/bom.csv` as `owner` | Enumerated every entry's `owner` | **Confirmed: `key-pullup-qty`, `panel-toggle-hole`, `ferrite-bias-impedance`, `ref5050-grade`** |

Rule 1 says the owner **states** the figure and everyone else cites it. These
four point a maintainer at the one file in the repository where a statement
is deleted without a word on the next `merge-bom.py`. It is the trap
`CLAUDE.md` §4 names, aimed by the register itself — and it is **mine**,
created the moment the restructure made that file generated and not
propagated into `config/figures.yaml`.

`check_owners` passes on all four, because `merge-bom.py` copies the
fragments' notes through, so the value really is present in the generated
output. The check proves the text is there. It cannot ask whether the file
it is in is one a human should edit.
