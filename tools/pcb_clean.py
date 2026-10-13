#!/usr/bin/env python3
"""Acid traps cleared from a routed board by taking off the scraps that make them (#47).

    python3 tools/pcb_clean.py <board.kicad_pcb> [--short MM] [--rounds N]

Freerouting's wiring, imported, leaves short scraps where its tracks meet: spurs a few tenths
of a millimetre long off a straight run, a track doubling back on itself. Each meets its own
net at a sharp angle, and pcb.py check fails the board on it (pcb.check_tracks, an acid trap).
On the main board, 2026-10-13, thirty of them remained after pcb_route.tidy, which removed
none: their far ends touch another scrap, so they are not "dangling" to it.

For each acid trap, each track of that net through the trap's point and shorter than `--short`
(default 0.6 mm) is taken off in turn. The removal is KEPT ONLY IF the net's pads stay as joined
as they were (the scorecard's own connectivity, tools/pcb_score._open: pads, tracks, vias and
filled zones, by geometry) and the board's acid traps fall. Rounds until nothing changes. It
never adds copper and never disconnects anything; what it cannot clear it reports.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def clean(path, short=0.6, rounds=6, log=print):
    """Clear what acid traps scrap removal can, on the board at `path`, in place. Returns
    (traps before, traps after, tracks removed)."""
    import pcbnew
    import pcb
    import pcb_score
    b = pcbnew.LoadBoard(path)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname():
                pads.setdefault(p.GetNetname(), []).append(p)
    traps = pcb.check_tracks(b)
    first = len(traps)
    removed = 0
    gone = []
    for _ in range(rounds):
        changed = False
        for t in list(traps):
            m = re.search(r"\[tracks\] (.+?) on (\S+): .* at \(([-\d.]+), ([-\d.]+)\)", t)
            if not m:
                continue
            net, x, y = m.group(1), float(m.group(3)), float(m.group(4))
            at = pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))
            here = [u for u in b.GetTracks() if type(u) is pcbnew.PCB_TRACK and u.GetNetname() == net
                    and (u.HitTest(at) or (u.GetStart() - at).EuclideanNorm() < 2000 or (u.GetEnd() - at).EuclideanNorm() < 2000)]
            here.sort(key=lambda u: u.GetLength())
            base = pcb_score._open(b, None, net, pads.get(net, []))
            n_before = len(pcb.check_tracks(b))
            for u in here:
                if pcbnew.ToMM(u.GetLength()) >= short or u in gone:
                    continue
                # taken off its net, it is out of both checks (they go by net); a Remove and
                # Add on a loaded board breaks KiCad's next walk of it (pcb_freeroute's note)
                code = u.GetNetCode()
                u.SetNetCode(0)
                if pcb_score._open(b, None, net, pads.get(net, [])) <= base and len(pcb.check_tracks(b)) < n_before:
                    gone.append(u)
                    removed += 1
                    changed = True
                    break
                u.SetNetCode(code)
        traps = pcb.check_tracks(b)
        if not changed:
            break
    for u in gone:
        b.Delete(u)
    traps = pcb.check_tracks(b)         # as they stand once the scraps are off, not as tested
    pcbnew.SaveBoard(path, b)
    log(f"pcb_clean: acid traps {first} -> {len(traps)}, {removed} scrap(s) removed")
    for t in traps:
        log("pcb_clean: left - " + t.split("[tracks] ", 1)[-1][:120])
    return first, len(traps), removed


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    short = float(args[args.index("--short") + 1]) if "--short" in args else 0.6
    rounds = int(args[args.index("--rounds") + 1]) if "--rounds" in args else 6
    clean(os.path.abspath(args[0]), short, rounds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
