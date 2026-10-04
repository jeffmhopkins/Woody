# Breath sense link — consolidation record

**Past tense only, and no live value.** Every live value is in
[`breath-sense-link.md`](breath-sense-link.md), in the pages it was assembled from, or in
`config/figures.yaml`. If a number appeared here it would be in the wrong file.

This directory did not exist before 2026-09-21. Until then the circuit was
described twice — once in `hardware/carrier/carrier.md` §2 and once in
`hardware/module/breath-receive-stage/breath-receive-stage.md` —
and each half derived statements from parts that were drawn only in the other.
The consolidation moved text and did nothing else: no value was edited, no
contradiction between the two halves was reconciled and no open question was
closed.

## 2026-09-26 — the sensor was never a through-hole part

Until 2026-09-26 the corpus described `U-BREATH` as "case 1351-01, dual side
ports, THT leads", and bought a machined SIP socket strip for it,
`SKT-BREATH`, in `hardware/carrier/bom.csv` and `hardware/carrier/netlist.yaml`,
so that ADR 0003's spare could be fitted. The banked datasheet's ordering
table ticked case 1351 as surface mount all along, and its outline is a
gull-wing SOP, which a SIP socket cannot hold. `mechanical/DESIGN.md` noticed it
while modelling the sensor and left it to the BOM. `SKT-BREATH` was deleted, the
sensor was soldered down, and the replaceability argument moved to the
iron-rework procedure on `breath-sense-link.md`. `carrier.md` had also carried
"which port is P1" as open; the same datasheet's Table 3 had answered it.

## 2026-10-04 — one fixed ~459 Hz pole became a switched filter (#32)

Until 2026-10-04 the receive filter was one fixed pole: `C-DIFF-BREATH` 15 nF
across the pair and `C-CM-BREATH` 1.5 nF on each leg, 2 × 11 kΩ against
15.75 nF, about 459 Hz; and `C-OUT-BREATH` 330 nF film behind `R-OUT-PROT`
gave a second pole near 480 Hz at the jack. The CMRR requirement's band was DC
to 500 Hz, and the matched 1.5 nF pair held its worst corner at 62.8 dB there.

The owner raised the band-limit to 1.5 kHz ("Let's go ahead and just put the
filter to 1.5 khz") and then made it a panel toggle, 500 Hz / 1.5 kHz / wide.
Two things made the old common-mode capacitors impossible to keep:

- **1.5 kHz failed the requirement.** With the 1.5 nF pair the 1.5 kHz mode's
  worst corner fell to about 53.6 dB at its top `[calc, an ideal difference
  amplifier against the same corners, 2026-10-04]`: the pair's mismatch converts
  common mode in proportion to frequency, and three times the frequency is
  three times the conversion.
- **WIDE could not exist.** The corner is 2 × 11 kΩ against `C_diff + C_cm/2`,
  so with 1.5 nF on each leg it could not pass 9.6 kHz even with no `C_diff` at
  all, and `C_diff` could not then dominate `C_cm`.

So `C_cm` came down by more than an order of magnitude and the fixed `C_diff`
with it, two switched capacitors were added beside the fixed one, and the
jack's capacitor moved above the widest mode. The values are
`breath-sense-link.md`'s *Component values*, not this page's.
