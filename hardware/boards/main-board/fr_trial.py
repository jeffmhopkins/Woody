#!/usr/bin/env python3
"""The main board routed by Freerouting from a placement, scored (#47; ADR 0029 as amended
2026-10-13: Freerouting routes, this repository's development goes to placement).

    python3 hardware/boards/main-board/fr_trial.py <placed.kicad_pcb> --out DIR [--keep GLOB,...]

A trial, like cold_trial.py: it writes into --out, never the board itself.

1. COPPER: the placement's copper is stripped but for the nets --keep names - by default the
   analog block's hand routes (the breath pair, its guards and the analog island's copper,
   #33), kept locked so Freerouting routes round them. Everything else is Freerouting's:
   the owner, 2026-10-13, "only some components need be locked".
2. The moat's keep-out and the plane fanout (pcb_route.moat_keepout, pcb_route.fanout), as
   pcb.py's `route: freerouting` lays them before the autorouter.
3. The Freerouting round trip (tools/pcb_freeroute.py: its pinned release, neck-down off).
4. Zones filled and pcb.post_route: tidied, KiCad's missing connections tried once more,
   the silkscreen.
5. The scorecard (tools/pcb_score.py) and KiCad's DRC; the board, a render and the score in
   --out.

What it leaves - an open net, a long detour - is a placement question: move the parts in its
way (pcb_pack) and run it again.
"""
import fnmatch
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

# the analog block's hand routes, kept (#33): its island, the breath pair and its guards
KEEP = ["AGND_INST", "/SENSOR_BUFFERED_OUT", "/SENSOR_RAW", "VS", "/breath-excitation-reference/*",
        "/breath-adc/*", "REF_VIN", "/BREATH_SENSE"]


def step(code):
    """`code` in a fresh process (a just-saved board, as pcb.py does it), its output shown."""
    r = subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {TOOLS!r}); " + code],
                       capture_output=True, text=True)
    out = "\n".join(l for l in r.stdout.splitlines() if "Debug:" not in l and not l.startswith("route: WARNING"))
    if out:
        print(out)
    if r.returncode:
        sys.exit(f"fr_trial: failed: {code[:80]}\n{r.stderr[-3000:]}")
    return r.stdout


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    out = os.path.abspath(args[args.index("--out") + 1]) if "--out" in args else sys.exit("fr_trial: --out DIR")
    keep = args[args.index("--keep") + 1].split(",") if "--keep" in args else KEEP
    src = os.path.abspath(args[0])
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "main-board.fr.kicad_pcb")
    import pcbnew
    import yaml
    import pcb
    import pcb_route
    lay = yaml.safe_load(open(os.path.join(HERE, "layout.yaml")))
    b = pcbnew.LoadBoard(src)
    kept = gone = 0
    for t in list(b.GetTracks()):
        if any(fnmatch.fnmatchcase(t.GetNetname(), g) for g in keep):
            t.SetLocked(True)
            kept += 1
        else:
            b.Delete(t)
            gone += 1
    print(f"fr_trial: {kept} track(s) and via(s) kept ({', '.join(keep)}), {gone} stripped")
    pcb_route.moat_keepout(b, lay)
    rep = pcb_route.fanout(b, lay, pcb_route.Obstacles(b, lay))
    print(f"fr_trial: fanout: {len(rep)} line(s) of report" + (f"; {rep[:3]}" if rep else ""))
    pcbnew.SaveBoard(path, b)
    # the board's own project, its net classes from layout.yaml (as pcb.py layout writes them)
    pro = os.path.splitext(path)[0] + ".kicad_pro"
    shutil.copy(os.path.join(HERE, "main-board.kicad_pro"), pro)
    j = json.load(open(pro))
    if lay.get("net_classes"):
        pcb.set_net_classes(j, lay)
        json.dump(j, open(pro, "w"), indent=2)
    edge = float(lay["rules"]["edge_clearance"])
    step(f"import pcb_freeroute; pcb_freeroute.route({path!r}, {edge!r}, {lay.get('directions')!r})")
    step(f"import pcb_route; pcb_route.fill_zones({path!r})")
    step(f"import pcb; pcb.post_route({path!r}, {HERE!r})")
    step(f"import pcb_route; pcb_route.fill_zones({path!r})")
    md = os.path.join(out, "score.md")
    step(f"import pcb_score; rows = pcb_score.score({path!r}, everything=True); t = pcb_score.totals(rows); "
         f"open({md!r}, 'w').write(pcb_score.markdown(rows, 'main-board.fr')); print('fr_trial: score', t); "
         f"print('fr_trial: open', [r['net'] for r in rows if r['open']])")
    step(f"import pcb_route2 as R; e, u = R.drc({path!r}); import collections; "
         f"print('fr_trial: KiCad DRC', len(e), 'error(s)', dict(collections.Counter(x[0] for x in e)), u, 'unconnected')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
