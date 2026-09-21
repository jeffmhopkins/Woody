# Preflight wave — what landed, and what has not

**Written 2026-09-21, at the end of the session that ran the wave.** All
thirteen agents reported. **Four slices have been worked into the corpus; nine
have not.** This file exists so the next session can tell the difference
without re-reading 800 kB of reports.

> **A report is a claim, not a fact.** `CLAUDE.md` is explicit about this, and
> this wave produced three more examples of why. Nothing below is "done"
> because an agent said it — it is done because it was checked against a
> document and committed. `VERIFIED.md` records the checks.

## Landed

| Slice | What landed | Commit |
|---|---|---|
| **A12** — datasheet coverage | Two structural blind spots in my own tooling. `verify-datasheets.py` could not see a BOM part with **no manifest row at all**; `merge-manifests.py` under-reported historical rows. Both fixed. | `b43e823` |
| **A3 / A2** — breath receive, pitch | **`sensor-full-scale` refuted** — the transfer function's offset coefficient is `0.053`, not `0.04`, so the pedestal is 0.265 V and full scale 4.864 V. **The first time a `SETTLED` figure was refuted by a banked document.** | `6a00ab3` |
| **A10** — impedance | Two corrections to things I wrote myself: the `F-CHAIN` drop (I used the fuse's hold current, not the circuit's draw) and the `riso-ref-topology` framing. | `6a00ab3` |
| **A4** — carrier | **Both decisions.** `cref-out-node` settled (C-REF-OUT is on the REF5050's own pins) and `riso-ref-topology` settled (TI Figure 56 dual feedback; `R-ISO-REF` 10 Ω → 37.4 Ω plus three new parts). Decisive citations re-read from the PDFs first. | `ddfa72c` |
| **A4-10 + A13-4** | The pedestal correction **propagated** — eleven derived statements, and twelve new `forbidden` patterns. Both agents found it independently, hours apart. | `367aaa1` |
| **A11** — net names | Landed before the wave closed. | `29f6aa5` |

Also landed from outside the wave: the `R-LDAC` pull-up defect (`a9f9c47`) and
wave R8's panel-height and toggle work (`af6be85`).

## Not landed — the nine slices still to triage

Each report is complete and on disk. **None of these has been checked against
its sources by hand**, which is the step that turns a finding into a change.

| Slice | Report | Headline the next session should start from |
|---|---|---|
| **A1** | `A1-power-entry.md` | `PWRGD` is connected to nothing; hot-plug margin is 1.49× not 2.01× (the page computes start and timer on different silicon corners); `r_d` is 332 mΩ not 69 mΩ — **and that one is a `figures.yaml` `value`, so it propagates** |
| **A5** | `A5-mod-channels.md` | Ten findings, untriaged |
| **A6** | `A6-breath-output.md` | The shaper delivers 1.289× where its own table claims 1.494×; the "mathematically linear" null is 14° off centre. **Recommends deleting `U-RESP`** — a whole SOIC-8 — by recasting as one non-inverting half |
| **A7** | `A7-digital-supervision.md` | Untriaged |
| **A8** | `A8-cluster-boards.md` | Gateron publishes **5 ms max** contact bounce; `ks33-geometry.md` still calls it unobtainable, and ADR 0001's debounce is 250 µs — 1/20 of that window |
| **A9** | `A9-current-budget.md` | Untriaged |
| **A13** | `A13-integration.md` | Ten High findings. Bus +5 V powers the buffer driving the DAC's inputs while `AVDD` comes from the LM317, **no sequencing**, abs-max `AVDD+0.3 V`. Pitch sits at 0 V — a VCO's base note — for 150–500 ms at every boot. RJ45 has no make-first/break-last contact |

## The cluster I would take first

**A1, A6 and A13 converge on the same rail**, which is why I would work them as
one change rather than three:

- **A1:** the LM317 rail's worst-case low corner is **4.992 V — under the
  DAC8568's 5.00 V hard floor** (`dac-rail` has a `floor:` field for exactly
  this). A1 proposes retargeting at the window centre.
- **A13:** the same rail has no sequencing against the bus +5 V that powers the
  level shifter driving the DAC's inputs — **and A13 notes the rail change
  three reviewers already want fixes it for free.**
- **A6:** deleting `U-RESP` removes two decoupling caps and an op-amp from the
  same supply, and frees the half A5's buffer needs.

Three findings, one fix, and the reason to do them together is that each one's
proposed remedy changes the other two's arithmetic.

## Decisions that are the owner's, not a reviewer's

Both have been open across two waves and **both gate work that is otherwise
ready**:

1. **Two layers or four.** Gates `dig-gnd-topology` and the LT5400's exposed
   pad. On two layers the corpus's own requirements are mutually exclusive —
   see the `dig-gnd-topology` entry, which states the contradiction.
2. **The net-naming convention.** Three competing schemes now exist:
   `AGND_MODULE` (first cold review), `AGND_SENSE`/`AGND_MOD` (A11),
   `UMB_BREATH_N`/`M_ARET` (A11's later proposal). **A11's case is strongest
   because it keeps the `AGND` token out of both names** — and `AGND` being
   mistaken for a ground is the single most repeated defect in this corpus.

## Two gaps in `datasheets/`

`U-ESD-USB` (USBLC6-2SC6) and `D-TVS-BREATH` (PESD12VS1UB) have **no manifest
row at all**. `verify-datasheets.py` names them on every run. Either bank the
document or add a `BLOCKED` row with the URLs tried — an honest gap is useful,
an invisible one is not.
