"""The left key board re-placed and re-routed by the new tools (issue #46): the cluster
packer (tools/pcb_pack.py) seats every passive, the centreline router (tools/pcb_route2.py)
routes every net. It READS key-board-lh.kicad_pcb and WRITES key-board-lh.revb.kicad_pcb
beside it - a trial, not the source. The silkscreen still says rev A (ADR 0020
Amendment 9: rev A is not yet ordered); "revb" names the file, not a revision.

    python3 hardware/boards/key-board-lh/revb_trial.py [--place-only] [--liquid] [--fillet MM]

What stays where the source has it: the parts the body CAD places (the five switches,
J-CHAIN J1, the four mounts - pcb-geometry.echo), the outline, the mounts' keep-outs and
the two ground zones. Everything else is placed COLD by the packer (place(), below) and
the copper is stripped; then every net is routed, connect_first and route_first first,
ground last as a net, stitched, and every piece of the pours tied to the net after a
fill. Its numbers against the source's are printed; whether
it replaces the source is decided on them, by a person.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pcbnew       # noqa: E402
import yaml         # noqa: E402
import pcb_pack     # noqa: E402
import pcb_route2   # noqa: E402

SRC = os.path.join(HERE, "key-board-lh.kicad_pcb")
OUT = os.path.join(HERE, "key-board-lh.revb.kicad_pcb")
BODY = ["SW1", "SW2", "SW3", "SW4", "SW5", "J1", "H1", "H2", "H3", "H4"]


def key_roles(board):
    """Each switch's network in role order - series R (its SWITCH_LEG), pull-up R (its KEY
    and the 3V3 rail), C (its KEY and ground) - read off the nets, not off the references."""
    nets = {fp.GetReference(): {p.GetNetname() for p in fp.Pads()} for fp in board.GetFootprints()}
    roles = {}
    for sw in [r for r in BODY if r.startswith("SW")]:
        leg = next(n for n in nets[sw] if n.endswith("SWITCH_LEG"))
        series = next(r for r, ns in nets.items() if r != sw and leg in ns)
        key = next(n for n in nets[series] if n != leg)
        pull = next(r for r, ns in nets.items() if r.startswith("R") and key in ns and r != series)
        cap = next(r for r, ns in nets.items() if r.startswith("C") and key in ns)
        roles[sw] = [series, pull, cap]
    return roles


def strip(board):
    """Every track and via goes; the zones stay (their outlines and settings are the source's),
    emptied for a refill."""
    gone = list(board.GetTracks())
    for t in gone:
        board.Delete(t)
    for z in board.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    return len(gone)


def place(board, lay, log):
    """A COLD placement: only what the body CAD places stays (BODY). Every other part - the
    register too - starts unplaced (it keeps no seat clear and ends no airwire) and is
    seated by the packer, in the order each cluster's anchor exists:
      1. U1, the register, round J1 (its chain lines' end), any of four turns;
      2. U1's two decouplers and the free input's pull-up round U1;
      3. C7, the chain's reservoir, round J1;
      4. one key network - series R, pull-up R, C - searched once and stamped at all five
         switches (the source's own rule: every key's network the same way round its
         switch), either of two turns."""
    bd = pcb_pack.board_of(board, rails=[lay["ground_net"]] + list(lay.get("power_nets") or []))
    bd.unplaced = {r for r in bd.parts if r not in BODY}
    pk = pcb_pack.Packer(bd, BODY, log)
    roles = key_roles(board)
    turns = (0, 90, 180, 270)
    reps = [pk.pack("J1", ["U1"], rotations=turns), pk.pack("U1", ["C6", "C8", "R11"], rotations=turns),
            pk.pack("J1", ["C7"], rotations=turns), pk.pattern(list(roles), roles, rotations=(0, 90))]
    for r in reps:
        if r["result"] != "packed":
            raise SystemExit(f"revb: the packer refused - {r['result']}")
    if bd.unplaced:
        raise SystemExit(f"revb: still unplaced after packing: {sorted(bd.unplaced)}")
    pk.apply(board)
    return reps


def route(board, lay, liquid=False, fillet=0.0):
    m = pcb_route2.model_from_board(board, lay)
    # the search's node budget: the bench's default is sized for small boards; this one has
    # ~1.6 million states (cells x 8 headings x 2 layers), and a rail's tree can need more
    r = pcb_route2.Router(m, flow=0.3, budget=4_000_000)
    failed = r.route(first=lay.get("route_first") or [], ground=lay["ground_net"],
                     connect_first=lay.get("connect_first") or [])
    for n in list(failed):
        if r.rescue(n):
            failed.pop(n)
    liq = r.liquid(fillet) if liquid else None
    pcb_route2.write(board, m, r.runs)
    return r, failed, liq


def measure(path):
    b = pcbnew.LoadBoard(path)
    tr = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    errs, unc = pcb_route2.drc(path)
    return {"length_mm": round(sum(pcbnew.ToMM(t.GetLength()) for t in tr), 1),
            "vias": sum(1 for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)),
            "segments": len(tr), "drc_errors": len(errs), "unconnected": unc}


def main():
    liquid = "--liquid" in sys.argv
    fillet = float(sys.argv[sys.argv.index("--fillet") + 1]) if "--fillet" in sys.argv else 0.0
    lay = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))
    lay = dict(lay, via_cost=lay.get("via_cost", 2.4))
    board = pcbnew.LoadBoard(SRC)
    log = []
    n = strip(board)
    reps = place(board, lay, log)
    print(f"revb: {n} track(s) and via(s) stripped; cold-packed: U1 {reps[0]['seats']}; its cluster {reps[1]['seats']}; "
          f"C7 {reps[2]['seats']}; key network {reps[3]['arrangement']}")
    for line in log:
        print("revb: " + line)
    if "--place-only" in sys.argv:
        pcbnew.SaveBoard(OUT, board)
        errs, _ = pcb_route2.drc(OUT, fill=False)
        place_errs = [e[:3] for e in errs if e[0] in ("courtyards_overlap", "items_not_allowed")]
        print(f"revb: placed only - wrote {os.path.relpath(OUT, ROOT)}; KiCad placement findings: {place_errs or 'none'}")
        return 1 if place_errs else 0
    r, failed, liq = route(board, lay, liquid, fillet)
    for line in r.log:
        print("revb: " + line)
    if liq:
        print(f"revb: liquid {liq}")
    print(f"revb: router {r.summary()}; failed {failed or 'none'}")
    pcbnew.SaveBoard(OUT, board)
    # the pours: every piece tied to its net (fits cannot see a pour), in a fresh process
    import json
    import subprocess
    code = (f"import sys, json, yaml; sys.path.insert(0, {os.path.join(ROOT, 'tools')!r}); import pcb_route2; "
            f"print('TIE ' + json.dumps(pcb_route2.tie_pour_islands({OUT!r}, yaml.safe_load(open({os.path.join(HERE, 'layout.yaml')!r})), "
            f"{lay['ground_net']!r})))")
    t = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    tie = [json.loads(l[4:]) for l in t.stdout.splitlines() if l.startswith("TIE ")]
    if not tie:
        raise SystemExit(f"revb: the pour pass failed:\n{t.stderr[-2000:]}")
    print(f"revb: pour islands tied with {tie[0][0]} via(s); untied: {tie[0][1] or 'none'}")
    print(f"revb: wrote {os.path.relpath(OUT, ROOT)}")
    print(f"revb: source {measure(SRC)}")
    print(f"revb: trial  {measure(OUT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
