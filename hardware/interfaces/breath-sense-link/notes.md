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
