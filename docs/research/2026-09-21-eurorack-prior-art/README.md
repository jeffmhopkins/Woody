# Eurorack prior-art research — 2026-09-21

Ten researchers, one per subsystem, asked the same question: **what do published
designs already do here, and where is Woody reinventing or diverging?**

Each was told to read the repo first so it compared against what is decided
rather than against a generic module; to mark provenance strictly (`[schematic]`
means a file opened in that session and nameable); and explicitly *not* to
validate Woody — the valuable finding is practice that exists because of a
failure mode this design has not considered. Each was also told to say plainly
where Woody is right to differ, since this is a one-off for one known rack and
"everyone does X" is not an argument by itself.

**Wave in progress.** Files land here as agents finish; this register is written
once they are all in.

| | Topic | In |
|---|---|---|
| R1 | 1 V/oct output stages | |
| R2 | Bipolar CV from a unipolar DAC | |
| R3 | Eurorack power entry and protection | |
| R4 | What goes between an op-amp and a jack | |
| R5 | Off-board links: expanders, RJ45, SPI over a cable | ✓ |
| R6 | Breath control as actually built | ✓ |
| R7 | Multichannel DAC practice | |
| R8 | 1 V/oct calibration, from real code | |
| R9 | Fail-safe and supervision on CV outputs | |
| R10 | Key scanning over a long loom, and SAR ADC front ends | |

## A note on what the proxy allowed

Both agents so far report the same thing: **GitHub clone works and almost
nothing else does.** doepfer.de, ti.com, analog.com, nxp.com, neutrik.com,
modwiggler, electro-music, hackaday and Wikipedia were all blocked. So there is
very little `[datasheet]` evidence in this wave and a good deal of
`[search-summary]` — search-engine summaries of pages nobody could open.

That tier is explicitly flagged in each document and should be treated as
hearsay until someone with an unblocked browser checks it. It is not nothing —
it pointed at real things — but it is not a datasheet.

What the agents *could* do was clone and read source: five wind-controller
firmwares, several Eurorack module repos, and the author's own 2021
`Open-Woodwind-Project`. The strongest findings in this wave all came from
reading code and netlists, not from the web.
