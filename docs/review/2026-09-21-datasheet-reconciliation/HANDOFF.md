# Handoff to the PCB-pipeline session

**From wave R7 (datasheet reconciliation), 2026-09-21.** You were writing
`docs/reference/pcb-pipeline.md` on `main` while this ran. We touched the same
three files — `hardware/bom.csv`, `config/figures.yaml`, `datasheets/MANIFEST.csv`
— and R7 moved several things your **Precursors** list depends on. This is what
changed under you, ordered by how much it costs you if you miss it.

---

## 1. One correction I owe you, and it went the wrong way first

Your `U-TVS-SPI` note recorded the ESD7104 as checked-and-rejected, and added an
observation flagged honestly as *"an inference from a DIFFERENT part [that] must
be confirmed against the SP0504BAHT itself"* — that a sustained-fault rating may
be outside what this class of array specifies at all.

**I got the SP0504BAHT, and I first wrote up your inference as confirmed. It is
refuted.** The two documents are mirror images:

| | steady-state `P_D` | pulse rating |
|---|---|---|
| onsemi ESD7104 | none stated | 8/20 µs, IEC 61000-4-2 |
| **Littelfuse SP0504BAHT** | **0.225 W** (Abs Max p.2; `PD@70°C .225W` p.7) | **none at all** |

So a sustained rating is *not* outside what this part specifies — it is 0.225 W,
a published hard ceiling, and the prior review's 0.98 W is refuted by a real
sourced number **4.4× lower** rather than by an absence. Your prescription
survives unchanged: a series resistor or a resettable element, not a bigger
array. What is genuinely missing is the *pulse* side, which is what an ESD array
would normally be specified by.

Your rejection records are **intact and untouched** — ESD7104 in `U-TVS-SPI` and
in `.manifest-R4.csv`, Littelfuse USBR in `.manifest-R4.csv` for `F-CHAIN`. I
did not edit `.manifest-R4.csv` at all. Neither part has been re-proposed.

---

## 2. Your Precursor 1 moved — six packages and two new refdes

**`bom.csv` is 135 rows now, was 133.** `tools/check-bom-parity.py` will need
both new ones when you write it.

| refdes | what changed | why it matters to you |
|---|---|---|
| **`R-PRECISION`** (LT5400) | package → **MS8E with a 1.88 × 1.68 mm exposed pad** | Was "MSOP-8, no pad". **The footprint must be `MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm`, not plain `MSOP-8`.** See §3 — this one also lands on your pour. |
| **`U-TVS-SPI`** (SP0504BAHT) | package → **SOT-23-5** | Was SOT-23-6. **Pin count changes, so the netlist changes**, not just the footprint. The 4-channel part is the -5; `SP0505BAHTG` is the genuine -6 with a 5th channel if you'd rather keep the footprint. |
| `C-TIMER-LOADSW` | **10 µF**, package 0805 C0G → **THT radial or 1210** | Was TBD. The old 0805 C0G was wrong by three orders of magnitude. Needs a **low-leakage** part — leakage is a meaningful fraction of the LT1641's 3 µA pull-down. |
| `C-GATE-LOADSW` | **82 nF**, 0805 or 1206 | Was TBD, and the part did not exist in the BOM at all. |
| `R-FB-HI` / `R-FB-LO` | **35.7 kΩ / 5.11 kΩ**, 0805 | Were TBD. |
| **`R-GATE-SER`, `R-GATE-COMP`** | **NEW ROWS** — 10 Ω and 1 kΩ, 0805 | Straight off ADI's Figure 5. `R-GATE-COMP` is **in series with `C-GATE`**, not parallel. New nets on the load switch. |
| `PLATE-TOP`, `PLATE-THUMB` | **1.20 mm** aluminium | Your Precursor 4, "mechanical inputs settled". Both 1.5 and 2 mm are **outside Gateron's window**. |
| `FB-IN` | Laird `MI1206K601R-10`, 1206 | Part now chosen; see §4. |

Eight of those rows moved to `status: selected`. None has a `footprint` yet —
when you add your 12th column, these are the rows with no prior art to copy.

---

## 3. The exposed pad is a pour question, and it is yours

Your §6 is *"three grounds, two zones, one star"*. The LT5400's exposed pad
arrives straight into the middle of it, and nothing in the corpus says where it
goes, because the BOM did not know it had one.

`[5400fa p.6, "Where to Connect the Exposed Pad"]`: it is **not DC-connected to
any resistor**, *"do not tie the exposed pad to noisy signals or noisy grounds"*,
and *"connecting the exposed pad to a quiet AC ground is recommended"*. p.2's
"EXPOSED PAD (PIN 9) IS FLOATING" means floating *internally* — not a
contradiction, and not permission to leave it unconnected.

**The number that makes it a real decision: pad-to-resistor coupling is 5.5 pF,
against only 1.4 pF resistor-to-resistor.** The pad is therefore the dominant
stray on the 1 V/oct network. Your pour plan gives `AGND` no zone at all plus a
keepout, so "quiet AC ground" has to mean something specific here. **Decide it
with the layout, not after it.**

**And note it is the same shape of question as your own `dig-gnd-topology`**,
which arrived in `config/figures.yaml` while R7 was running: *where does this
net return to, and does the answer survive two layers?* Both are "which ground
does this attach to", both are unanswerable until the 2-layer vs 4-layer
decision is made, and both are invisible to `check-staleness.py` because they
are semantic. **They should probably be decided in one sitting** — a pad told to
find "a quiet AC ground" on a board that has not settled where its grounds meet
is a decision deferred twice, not once.

---

## 4. Things that change your §2 (simulate before copper)

- **OPA2197 `Zo` is specified at 375 Ω, not the 75.8 Ω the corpus back-solved**
  `[SBOS737C p.8, two occurrences]`. Every pole derived from 75.8 moves ~5× the
  *wrong* way: 21 kHz → 4.24 kHz against 100 nF, 200 Hz → 42 Hz against 10.1 µF.
  If your SPICE stage simulates the reference buffer, **this is the number to
  check it against**, and the banked TI macromodel models `Zo` explicitly.
- **TI publishes the worked answer for that exact circuit** — SBOS737C §8.2.3
  p.30, Figure 56, *"Precision Reference Buffer"* driving 10 µF: `R_ISO` 37.4 Ω,
  `R_F` 1 MΩ at `VOUT`, `R_Fx` 10 kΩ + `C_F` 39 nF at the op-amp output, 89° PM.
  `R-ISO-REF` is currently 10 Ω. A good first target for stage 2.
- **But it is blocked on a question no simulation settles:** three files
  disagree about **which side of the buffer `C-REF-OUT` sits on**. `carrier.md`
  draws the 10 µF on the REF5050 output (= the buffer's *input*); `bom.csv` and
  `breath-receive-stage.md` both say the buffer *drives* it. No grep finds that,
  and it changes the whole compensation. **Settle the node before you simulate
  the network.**
- **`FB-IN` is not 600 Ω where it matters.** Read off Laird's bias curve at
  100 MHz: FB1/FB3/FB4 sit on the flat part and get 580–614 Ω, but **FB2 carries
  the umbilical at 359 mA and gets ~280–310 Ω** — half its nameplate. The
  ">= 1 A" rule in that row does not do what it says: a bead's rating is
  **thermal, not magnetic**, and a 3 A part in the same package reads *worse* at
  500 mA. If any EMC simulation assumes 600 Ω on FB2, it is wrong by 2×.

---

## 5. Your Precursor 3 — two tracked figures are not out of `disputed`

R7 added five entries to `config/figures.yaml`. Three are `settled`
(`loadswitch-timer`, `loadswitch-gate-cap`, `loadswitch-fb-divider`,
plus `plate-thickness` and `opa2197-output-impedance`). **Two are not:**

- **`ref5050-grade` — `disputed`, and it is a potential part change.**
  `REF5050**A**IDR` is the *Standard* grade: **±0.1 %, 8 ppm/°C**, not the
  ±0.05 % / 3 ppm/°C the corpus asserted in three places `[SBOS410O Table 4-2
  p.3]`. `REF5050IDR` is the High grade, same package, same pinout, one letter.
  If that letter changes, `U-REF-BREATH` changes — **so this blocks your
  Precursor 1 for that row**, not just Precursor 3.
- **`matrix-led-current` — `blocked`, and unblocking it needs a current probe.**
  Not a PCB question, but it sits under ADR 0014's brightness cap.

Also raised and **not decided**, all of which touch a board you will lay out:
ADR 0005's ramp spec (`I_GATE` is 5–20 µA, so a 50–100 ms window is
unachievable); how a 1.20 mm plate gets stiffened; and the `C-REF-OUT` node.

---

## 6. Network intel, since you documented the policy too

You found pypi in the proxy's `noProxy` list. R7 found the rest of it had moved:
**ti.com, neutrik.com, murata.com, gateron.com, files.waveshare.com,
farnell.com, docs.rs-online.com, world-semi.com, onsemi.cn, tai-hao.com and
`web.archive.org` all answer normally.** Nine of seventeen inherited gaps closed
by asking again.

**Two consequences for you specifically:**

1. **`web.archive.org` reaches hosts that are still dead.** `analog.com` fails
   today exactly as it did in four previous waves — origin-side, not policy —
   and its 2019 capture of `164112fc.pdf` fetched in one try. Use the CDX API:
   `cdx/search/cdx?url=<host>/<path>&output=text`, then
   `web/<timestamp>id_/<url>` for raw bytes. Pass any `filter=` through
   `curl -G --data-urlencode` or brackets in the regex break the URL.
2. **Your `.manifest-R4.csv` rows still record `farnell.com` as "HTTP 000
   connect_rejected".** That is no longer true — `www.farnell.com/datasheets/47249.pdf`,
   *the exact URL already in that BLOCKED row*, returned 200 on the first try
   and is now the SP0504BAHT. I left R4 untouched because it is your record,
   but **the other BLOCKED rows carrying farnell URLs are worth re-probing.**

And a trap that caught three researchers this wave: **a 200 and a `.pdf`
filename prove nothing.** An RS-online URL recorded as the LT1641's mirror is a
real PDF *of the LT4256*. A Farnell URL found searching for a 74HC165 contains
no occurrence of "165". A Diodes Inc URL found searching for a 1N4148W is the
**MMST3906 transistor**. Grep the extracted text for the part number, always.

Separately: **several key documents have no text layer at all.** Gateron's
drawing, both Laird bead drawings, the Neutrik outlines and the TE socket page
are vector CAD — `pdftotext` returns a byte or two and the dimensions exist only
in the picture. The plate thickness, the bead bias curve and the IDC stack
height were all read by rendering at 150 dpi and looking. If your pipeline ever
pulls a dimension out of `datasheets/` programmatically, it will silently get
nothing from these.

---

## 7. Two housekeeping notes

- **`tools/merge-manifests.py` gained a reporting block.** It now names the
  BLOCKED/NOT-FETCHED rows whose part is banked elsewhere — ten of them today.
  It changes no data and edits no fragment; the fragments stay as their authors
  wrote them, because a BLOCKED row is the honest record of a gap when it was
  written. The generated MANIFEST is where a reader greps for gaps, so it says
  which ten are history.
- **One pre-existing duplicate, not mine and not yours:** WS2815 is banked twice
  under two paths (`mechanical/WS2815-worldsemi-datasheet.pdf` and
  `other-semi/WS2815.pdf`), same SHA-256, from R3 and R6. Harmless, but
  `check-bom-parity` or any manifest-driven tooling should expect it.

`check-staleness`, `verify-datasheets` and `merge-manifests` all pass on
`1dc0b5c`. 75 artefacts verified, 0 problems.
