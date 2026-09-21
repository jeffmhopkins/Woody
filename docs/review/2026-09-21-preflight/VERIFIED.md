# VERIFIED — preflight wave

## A11 — `+12V` is three nets, and that is worse than `AGND`

**Re-checked, 2026-09-21. CONFIRMED** at `hardware/module/power-entry.md:13-24`.
One `+12V` label at the IDC branches through `D1` to the module analog rail and
through `D2` to the umbilical export rail. A transcription taking the label
literally **merges all three and shorts out `D1`, `D2`, `FB1`, `FB2`, `C1`,
`C2` and the entire LT1641 load switch** — i.e. exactly the split whose whole
stated purpose is keeping instrument current out of the analog rail, and which
`D-REVPOL` is qty 3 to achieve.

## A11's own self-check — it was right to ask, and the answer is no

A11 closed by flagging that if an earlier wave had already named the module
analog return, it had invented a second name and made things worse. **It had —
there are now three proposals, A11's included:**

| Source | Sense conductor | Module analog return |
|---|---|---|
| First cold review, `D3` | — | `AGND_MODULE` |
| Pipeline wave, `P11` | `AGND_SENSE` | `AGND` or `AGND_MOD` |
| **A11** | `UMB_BREATH_N` | `M_ARET` |

**Not adopting any of them unilaterally.** A11's argument for avoiding the
`AGND` token in *either* name is the strongest one on the table — after the
rename, `grep -rn AGND` finds only sites still needing work, which the other
two schemes do not give you. But this is a convention decision, it is cheap for
the owner to settle, and settling it three different ways is how the problem
started.

## ADR 0004 carried two contradictory umbilical pin maps — FIXED

A11 reported it; **confirmed and repaired in the same pass.**
`docs/decisions/0004-cv-interface-module.md:97-98` paired
`SCLK / DIG_GND` and `MOSI / CS`, against its own corrected table 730 lines
later at `:828-831` and against `config/figures.yaml: umbilical-pinmap`, both
of which say `SCLK / MOSI` and `CS / DIG_GND`.

**Why the checker missed it:** `umbilical-pinmap`'s `forbidden` list matched the
**table-cell** spelling (`| MOSI / CS |`) and not the **code-block** spelling
(`MOSI      / CS`, runs of spaces). Both spellings are now listed.

**This is the fourth time a forbidden pattern has missed a different formatting
of the same value** — and I had edited that exact block earlier today without
noticing the pairing was wrong.
