# Verification pass — eight agents told to falsify, not extend

The register in the parent directory was written from 23 agent reports. These
eight agents were pointed at **the register and the reports**, with instructions
to break them.

**They did.** The findings are mostly right. The synthesis was not. Read this
directory before acting on the register.

## What the verification changed

| | |
|---|---|
| **Showstoppers** | 7 claimed → **4 survive fully** (S1, S3, S4, S7-partial), 2 downgraded (S2, S5), 1 overstated (S6) |
| **"Blow harder, pitch bends"** | 4 routes → **1 mechanism + 1 contingent**; ~52 cents implied → **5–15, most likely 6–8** |
| **Register entries** | 53 entries → **10 actual changes**. Any plan built by counting findings is ~5× too large |
| **Proposals** | ~190 distinct; **31 collide in 24 pairs or clusters**; 8 shared budgets over-subscribed |

## The three structural defects in the register

**1. `[verified]` did two jobs.** Found independently by V1, V3 and V6. It meant
both "I redid unambiguous arithmetic" (true verification) and "I redid the
arithmetic *given the agent's assumed topology*" (not verification at all).
Every finding that survived unconditionally is one where the repository pins the
reading; every finding that downgraded is one where it does not.

**2. The honesty markers were calibrated backwards** (V3). Every `[from memory]`
claim that could be checked was right. **Every claim found actually wrong was
tagged `[verified]`** — the 8 V buck UVLO, the LT1641 suffixes, the LM317
minimum load, the LT5400 1:4 ratio. The hedges went on *recollection* rather
than on *retrieval confidence*: a search summary and a datasheet reading were
marked identically. Three of five falsifications needed no network at all.

**3. Duplicate findings were collapsed; duplicate figures never were** (V3).
Two documents disagreed on 7 V vs 8 V inside the document set. The LT1641 labels
contradicted the next sentence. A typ column was read as a max.

## The errors that would have reached hardware

- **`LT1641-2` is the auto-retry part. `LT1641-1` latches off.** The register's
  S1 remedy orders the variant whose behaviour the same paragraph argues against.
  The only error in the register that would have been soldered on.
- **Three of four pitch-offset proposals take the reference from `VREFOUT`,
  which is disabled at reset** — pitch then parks at 0 V, an audible note,
  breaking ADR 0006's power-on table.
- **Two documents propose a second SP3012 array at the module end, on +12 V** —
  reproducing showstopper S6 at the other end of the cable.
- **Five documents rewrite the same four positions in the breath input network
  and no two produce the same circuit**, yielding six different in-amp gains
  (2.13 / 2.143 / 2.20 / 2.229 / 2.384 / 2.39), each arithmetically correct for
  a different combination.
- **The LT5400 de-specification is backwards.** ADR 0006 is correct that
  *tracking*, not absolute tempco, is what matters. Two independent 10 ppm parts
  give √2 × 10 = 14.1 ppm/°C of ratio drift ≈ 1.5 cents against the LT5400's
  0.11 — it would become the dominant term in the budget.

## The register's own self-contradictions

- **Line 217 says ~22 cents of pitch FM. Line 502 says "nothing the instrument
  does reaches pitch above 0.03 cents."** A factor of 700, in one document. The
  findings section and the confirmations section were written as separate
  exercises and never read against each other.
- **Six of eight items in "what the review confirmed as right" are defective**
  (V8) — the most dangerous section, because nobody re-reads a confirmation. The
  thermal entry takes B6's confirming sentence and drops its finding (rise is
  20–29 K, not the 9 K quoted). The stability entry promotes B9's *conditional*
  to unconditional: on the wrong side of that capacitor, every output stage
  oscillates.
- **The one "resolved" agent-versus-agent conflict is reversed.** C3 had already
  stated the internal-regulation fact and declined to rely on it; the register
  used C3's own caveat to refute C3.
- **`README.md:28` still says the controller "is purely digital and carries no
  analog signal path"** — the exact sentence ADR 0004 blames for letting a past
  review finding through, corrected in the ADR today and left standing in the
  more prominent document. It is absent from the register's list of its author's
  own errors, which instead confesses a duplicate heading, a misplaced BOM note
  and a power figure. V8's verdict: **"penitent about cosmetics, protective
  about architecture."**

## Things filed below showstopper that should stop the build

- **Key-switch pull-ups.** A 74x165 input with an open switch and no pull-up has
  no defined level. The scanner does not function as specified. Gates **M3**.
- **B9 f6** — the reference follower drives the sensor's *supply* pin, which by
  the BOM's own rule takes 100 nF. An oscillator on a ratiometric supply, 400 mm
  inside a bonded body. One 10 Ω resistor, free now, impossible later.
- **`C-STRIP-BULK` has no temperature grade** — ~1.3 years of life at a 50 °C
  interior, in two permanently entombed capacitors.
- **The frame watchdog can be masked.** DAC and ADC share SPI2, so retriggering
  on SCLK means a hang that stops DAC updates while breath sampling continues
  feeds the watchdog forever. The register made S4 a showstopper for a *side
  effect* of the watchdog firing and omitted the finding that it may never fire.

## Unblocked by the verification

- **Gateron KS-33: cutout 14.00 ±0.03 mm, clip engagement 1.20 ±0.05 mm.** Both
  2 mm and the 1.5 mm MX standard exceed the clip window. Closes the open item
  gating M4, M5, five BOM lines and a cutting order — obtained from a vendor
  drawing transcription and Gateron's own STEP link, both on GitHub, a route
  none of the 23 agents tried.
- **ESP32-S3-Matrix PSRAM is quad, confirmed from the header pin list** — closes
  an E1 bench item without a bench.
- **Load budget settled**: 392 mA typical, 555–589 mA clamp-legal worst. ADR
  0005's 250 mA is "a good estimate of a different instrument" — one with no
  matrix, no WS2815 quiescent and no lighting clamp.
- **The instrument does boot through a 500 mA limit** (~75 ms). The register's
  "never reaches UVLO" was false; the real constraint is the fault timer.

## The method that found the conflicts

V4's, and it is the durable lesson: **index proposals by the node or resource
they touch, not by the document that raised them** — which is exactly the axis a
per-subsystem agent assignment cuts across. Eight shared budgets are
over-subscribed, and *in every case each claimant's own document describes its
claim as free*: ten op-amp halves against 14–15 claimed, one spare ADC channel
against four claimants, eight umbilical conductors against eleven, 108.5 mm of
panel against 118.5 mm already needed.

One hard conflict created by a fix: **W5 raises the umbilical clock to 2 MHz
because the loop does not close below it, and the MCP3202 on the same bus tops
out near 1.1 MHz at 3.3 V.** Solvable per-transaction in firmware, and nobody
wrote it down.
