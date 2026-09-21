# Datasheets and mechanical drawings

**Actual PDFs, not links.** Four review waves were degraded by every vendor
site being blocked at the egress proxy — dozens of findings were marked
`[from memory]` and several load-bearing numbers had never been read off a real
document. This directory is the fix, and as of wave R7 (2026-09-21) it mostly
works: the LT1641's `I_TIMER`, the OPA2197's output impedance and the KS-33's
clip dimension were the three named here as missing, and **all three are now
read off vendor documents banked in this directory**. Two of the three had been
*wrong*, one of them by a factor of five.

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
- **Closing someone else's BLOCKED row: quote it.** When you bank a document
  that fills an earlier gap, put the blocked row's **exact `part` string** in
  your own row's notes together with the word **`SUPERSEDES`**.
  `tools/merge-manifests.py` then reports that row as closed every time it
  runs. This matters because you must not edit their fragment, so the blocked
  row goes on existing — and a reader greps `BLOCKED` to find the gaps. In
  September 2026 three banked documents read as live gaps for exactly this
  reason, and a session nearly spent a wave of agents re-fetching them. The
  tool also guesses at renamed matches and prints them under `CHECK:`, but that
  is a heuristic and it says so: it deliberately will not match `WS2812B-0807`
  to `WS2812B-2020`, because those are different dies.
- **Each researcher writes to `.manifest-R<N>.csv`**, and
  `python3 tools/merge-manifests.py` rebuilds `MANIFEST.csv` from the
  fragments. It is idempotent — edit a fragment, re-run, re-verify. Do not
  hand-edit `MANIFEST.csv`; it is generated.

## How to fetch anything at all from here

**The egress policy is not the same on every session, so measure it before you
plan around it.** Six researchers in waves R1-R6 found every vendor and
distributor host blocked and built an elaborate GitHub-mining method around
that. A seventh wave (R7, 2026-09-21) found ti.com, neutrik.com, murata.com,
gateron.com, files.waveshare.com, farnell.com, docs.rs-online.com,
world-semi.com, onsemi.cn, tai-hao.com and **web.archive.org** all answering
normally. Nine of the seventeen gaps closed by simply asking again.

Spend the first five minutes on a reachability sweep:

```
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
curl -sS -A "$UA" -o /dev/null -w "%{http_code} %{content_type}\n" -L --max-time 40 "<url>"
```

| Lever | Note |
|---|---|
| **`web.archive.org`, via the CDX API** | **The single biggest unlock in R7.** It is how `164112fc.pdf` was recovered after four waves failed: `cdx/search/cdx?url=<host>/<path>&output=text` lists captures, then fetch `web.archive.org/web/<timestamp>id_/<original-url>` for raw bytes. It reaches hosts that are still dead directly — analog.com among them. Use `curl -G --data-urlencode` for any `filter=`, or brackets in the regex break the URL. |
| Mirror hosts | `docs.rs-online.com`, `www.farnell.com/datasheets/<id>.pdf`, `datasheet.lcsc.com`, `www.tme.eu`, `static6.arrow.com`. Farnell in particular served two documents in R7 from URLs an earlier wave had recorded as `HTTP 000`. |
| Regional domains | `www.onsemi.cn` serves what `www.onsemi.com` 403s. `www.tai-hao.com` answers where `taihao.com.tw` does not. Worth trying before declaring a vendor blocked. |
| `git clone https://github.com/<owner>/<repo>` | Works for any public repo. Clone, then `find -iname '*.pdf'`. |
| `raw.githubusercontent.com/...` | Direct fetch of a known path, including binaries. |
| `media.githubusercontent.com/media/...` | **Git-LFS objects.** `raw` returns only a ~130-byte pointer; swapping the host returns the real bytes. |
| The GitHub MCP `search_code` tool | GitHub indexes no binaries: `extension:pdf` always returns zero. Search for *text* files that reference a PDF beside them. |

**A 200 and a `.pdf` filename prove nothing. Three mirrors lied in R7 alone:**

- `docs.rs-online.com/5ab4/0900766b810edab8.pdf`, recorded in an earlier
  BLOCKED row as the LT1641's RS mirror, is a real 195 kB PDF — **of the
  LT4256**, a pin-compatible successor.
- `farnell.com/datasheets/2299370.pdf`, found searching for a 74HC165, is a
  genuine 359 kB PDF containing no occurrence of "165".
- `diodes.com/assets/Datasheets/ds30079.pdf`, found searching for a 1N4148W,
  is the **MMST3906 transistor**.

So: `head -c 4` must be `%PDF`, size over 10 kB, and the part number must appear
in `pdftotext -layout` output. `tools/verify-datasheets.py` enforces the first
two; **only you can enforce the third.** And when a document is vector CAD —
Gateron's drawing, the Laird bead drawings, the Neutrik outlines — `pdftotext`
returns almost nothing and the numbers are only in the picture. Render it
(`pdftoppm -r 150 -png`) and read it.

## What is still missing, and why it matters

**Rewritten 2026-09-21 after wave R7.** Seventeen rows were `BLOCKED` or
`NOT-FETCHED`; **ten of those parts are now banked**, and
`tools/merge-manifests.py` prints their names every time it runs. The earlier
fragments are left exactly as their researchers wrote them — a BLOCKED row is
the honest record of a gap at the time, and editing it would destroy the one
thing it is for — so the same part legitimately appears twice in `MANIFEST.csv`,
once `BLOCKED` with no file and once `OK` with one. **Trust the row with the
file.**

The three that blocked real decisions are all resolved:

- **LT1641-1** — `164112fc.pdf` is banked. It confirmed eight of nine claims
  verbatim, including that foldback is sensed at the `FB` pin, and refuted the
  `VCC` UVLO maximum. `C-TIMER`, `C-GATE`, `R-FB-HI` and `R-FB-LO` all have
  values now and the parts order is unblocked.
- **SP0504BAHT** — banked, and it settled the power question by **not having
  one**: there is no peak-pulse-power spec in the document at all, so the
  0.98 W figure is unsourceable rather than merely wrong.
- **A ferrite bead with an impedance-vs-DC-bias curve** — found, in Laird's
  `MI1206K601R-10`. The judgement that produced this gap was right and is
  upheld: Murata's *PDF* turns out to carry no bias curve either (that data
  lives only in SimSurfing), so a Murata part can be an alternate but not the
  characterised one.

**What is genuinely still open**, and all of it was opened *by* R7 rather than
inherited:

- **WS2812B-0807 — and this one is not a fetch failure, it is a vendor
  negative.** The Waveshare schematic, once banked, showed the matrix is fitted
  with this part and not the WS2812C the corpus assumed. **Worldsemi does not
  publish a datasheet for it**: their own machine-readable datasheet index
  enumerates 68 keys covering every published part — `ws2812b-v6/-v7`, `-mini`,
  `-1313`, `-2020`, `-2427`, `-4020`, all of `ws2812c/d/e` — and has no `0807`
  key in either language, while the control URL for `ws2812b-2020-v6` returns a
  real 1.26 MB PDF. Two XINGLIGHT `XL-0807RGBC-WS2812B` revisions are banked as
  **surrogates, named as such**, and they disagree with each other (12 vs
  19 mA/channel, 7× on quiescent). Tracked as `matrix-led-current`, status
  `blocked` — and **unblocking it now needs a current probe at E1, not another
  fetch.**
- **`5400fc.pdf`** — the LT5400 is banked at rev **fa**, which answers the
  exposed-pad question fully. Rev fc is still wanted because rev fa predates
  the `-7` option, so `LT5400-7` is *not-in-document* rather than refuted.
- **Tai-Hao MT165** — no drawing exists anywhere. Tai-Hao's own store confirms
  16.5 x 16.5 mm and MX-compatible; height, stem depth and profile are
  unpublished. Two independent routes failed; recorded and moved on.

The rest are second sources and substitutes whose absence is recorded in the
relevant BOM row.

**A note on surrogates.** Three rows in this manifest bank a document for a part
that is *not* the one fitted: the two XINGLIGHT 0807 LEDs and the 1986 Toshiba
`TC74HC165P/F` excerpt. Their notes say so in the first line, and they exist
because a bracketing document is worth more than nothing when the real one does
not exist. **They must never be cited as the fitted part's datasheet**, and the
figure they bracket stays `blocked` or carries its bracket explicitly.

## Provenance and licence

These are third-party copyrighted documents, redistributed here for a
one-off personal build so that the design can be verified offline. They are
not covered by this repository's own licence (ADR 0011). Each manifest row
records its source.
