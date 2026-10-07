# MIDI out — decision history

**Past tense only.** Every live value lives in [`midi-out.md`](midi-out.md),
`config/body.yaml` `midi`, `mechanical/drc.echo` or `hardware/bom.csv`. If a
number here is still true, it is in the wrong file.

## The jack through the oak bottom (2026-10-04 to 2026-10-07)

Issue #37 put `J-MIDI-OUT` through the **oak bottom**, at the tail, in the
lane beside the etherCON that the USB-C extension's receptacle had stood in
(owner, 2026-10-04: *"I think you need it on the bottom face, and then just do
a connector to the main board instead of actually mounting it to PCB"*). That
lane existed because the etherCON sat off-centre (`ethercon.offset_y`, a
placeholder). A counterbore from the bottom's inside face took the jack's
collar and left the oak its nut could clamp, and its nut stood under the
bottom face. `J-MIDI` was a **top-entry** JST PH (B3B-PH-SM4-TB) in the main
board's far tail corner, and the lead rose off the jack's tabs, crossed the
lane and dropped into it.

It was superseded on 2026-10-07 (issue #45; ADR 0021, *Amendment,
2026-10-07*). The owner asked for the jack on the face the etherCON is on, the
etherCON centred, and a side-entry header facing the tail. Centring the
etherCON alone also broke the oak-bottom design: the lane went to the
flange-to-side width the tail face has today, narrower than that counterbore,
and the model's rule *"MIDI jack in the oak bottom"* failed with the
counterbore overlapping both the flange's footprint and the side's groove.

The same pass corrected two readings of the jack's drawing that the oak-bottom
design carried: it took the 10.0 hex for a **collar, across its corners**, and
the body for the collar's diameter. The drawing's hex is the **nut**, 10.0
across its flats; the collar behind the thread is round and the body is
narrower (`config/body.yaml` `midi.jack_nut_af`, `jack_collar`, `jack_body`).
