"""The main board's unlocked copper taken up and routed again by the centreline router's
four-layer stage (tools/pcb_route2.py, issue #46) - the plan's gate for it. It READS
main-board.kicad_pcb and WRITES main-board.route2.kicad_pcb beside it: a trial, not the
source, and not a re-layout - no part moves.

    python3 hardware/boards/main-board/route2_trial.py [--fence x0,y0,x1,y1]

What stays: every part; every LOCKED track and via - the plane fanout, the breath pair and
its guards, connect_first and the hand routes (#45); the zones. What is taken up: every
unlocked track and via (inside --fence only, with one). Then: any plane pad without its
via is fanned out (layout.yaml fanout:), every other net routed - its class's layers,
via size and costs, route_first first - never on a plane layer it does not name, never
across a split in its reference plane but at a tie's window; the zones filled and every
fragment of a plane fanned out again into its body. The numbers against the source are
printed; `pcb.py check` is run on the trial in place, by hand (see the issue).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pcbnew       # noqa: E402
import yaml         # noqa: E402
import pcb_route2   # noqa: E402

SRC = os.path.join(HERE, "main-board.kicad_pcb")
OUT = os.path.join(HERE, "main-board.route2.kicad_pcb")


def measure(path):
    b = pcbnew.LoadBoard(path)
    unl = [t for t in b.GetTracks() if not t.IsLocked()]
    tr = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    errs, unc = pcb_route2.drc(path)
    return {"length_mm": round(sum(pcbnew.ToMM(t.GetLength()) for t in tr), 1),
            "vias": sum(1 for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)),
            "unlocked_items": len(unl), "drc_errors": len(errs), "unconnected": unc}


def main():
    fence = None
    if "--fence" in sys.argv:
        fence = tuple(float(v) for v in sys.argv[sys.argv.index("--fence") + 1].split(","))
    lay = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))
    board = pcbnew.LoadBoard(SRC)
    m = pcb_route2.model_from_board(board, lay, fence=fence)
    nets = set(m.nets())
    if fence:
        from shapely.geometry import box
        fb = box(*fence)
        nets = {e.net for e in m.index.e.values() if e.kind in ("track", "via") and not e.locked and e.geom.within(fb)}
    took = pcb_route2.take_up(m, nets)
    print(f"route2: took up {took} unlocked track(s) and via(s) of {len(nets)} net(s)" + (f" inside {fence}" if fence else "")
          + f"; kept {m.kept_for_locked} unlocked item(s) a locked route depends on")
    r = pcb_route2.Router(m, flow=0.3, budget=3_000_000, fence=fence)
    route_nets = [n for n in m.nets() if n in nets and n not in m.planes.plane_nets]
    failed = r.route(route_nets, first=lay.get("route_first") or [], connect_first=lay.get("connect_first") or [])
    for line in r.log:
        print("route2: " + line)
    print(f"route2: {r.summary()}; failed {failed or 'none'}")
    pcb_route2.write(board, m, r.runs)
    # the old router's own finishing pass (tools/pcb_route.tidy), as post_route runs it: empty
    # and doubled tracks, dangling ends, acute joins squared, collinear joints merged, the
    # chamfer - never on locked copper. Where new copper meets the hand routes it is what
    # squares the joins between them
    import pcb_route
    pcbnew.SaveBoard(OUT, board)
    board = pcbnew.LoadBoard(OUT)
    pcb_route.tidy(board, lay)
    pcbnew.SaveBoard(OUT, board)
    code = (f"import sys, json, yaml; sys.path.insert(0, {os.path.join(ROOT, 'tools')!r}); import pcb_route2; "
            f"print('ORPH ' + json.dumps(pcb_route2.fix_plane_orphans({OUT!r}, yaml.safe_load(open({os.path.join(HERE, 'layout.yaml')!r})))))")
    t = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    orph = [json.loads(l[5:]) for l in t.stdout.splitlines() if l.startswith("ORPH ")]
    if not orph:
        raise SystemExit(f"route2: the plane orphan pass failed:\n{t.stderr[-2000:]}")
    print(f"route2: plane fragments fanned out again: {orph[0][0]}; still apart: {orph[0][1] or 'none'}")
    print(f"route2: wrote {os.path.relpath(OUT, ROOT)}")
    print(f"route2: source {measure(SRC)}")
    print(f"route2: trial  {measure(OUT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
