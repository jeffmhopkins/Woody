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
   pcb.py's `route: freerouting` lays them before the autorouter; then CONNECT_FIRST, the
   named pad-to-pad connections Freerouting could not make, laid on that near-empty board and
   fixed.
3. The Freerouting round trip (tools/pcb_freeroute.py: its pinned release, neck-down off).
   FIRST, alone (FIRST, or --first): the nets that cross the board between two fixed parts,
   routed by Freerouting on a copy where nothing else has a net, then fixed on the board.
4. Freerouting again on its own result (its wiring unfixed, so it rips up and shoves), up to
   ROUNDS rounds or until nothing is left; then the tracks tidied. What is still apart is
   REPORTED by net. --complete adds pcb.py's post_route (the grid router with rip-up), bounded
   by COMPLETE_S - off by default: every one of trial 4's 26 DRC errors was on a net it laid.
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
        "/breath-adc/*", "REF_VIN", "/BREATH_SENSE",
        # and J-MCU's 5 V link J1.3 - J1.17 under its back row, the source board's hand route:
        # left to Freerouting it was the one connection in that strip it did not make (trial 3)
        "INST_5V_A"]

# Routed FIRST, alone on the board, then fixed: the nets that cross it between two fixed parts.
# Left to the end of Freerouting's run they had the whole finished board to cross, and four of
# trial 3's nine leftovers were these (2026-10-13). The SPI bus (J-MCU to the MCP3202) and the
# chain's two long lines from their series resistors at J-MCU
# Off by default since trial 4 (2026-10-13): with these five fixed first, Freerouting left 19
# connections for the rest, against trial 3's 9 without. `--first` still runs it
FIRST = []
FIRST_TRIED = ["/IO35", "/IO36", "/IO37", "/CHAIN_SCK", "/CHAIN_SHLD"]
# Freerouting again on its own result, until nothing is left or ROUNDS are run: its wiring goes
# back unfixed, so the next round rips up and shoves round what it left - Freerouting's own
# push-and-shove finishing the board, where the grid completion laid illegal copper (trial 1's
# crossing, trial 4's 26 DRC errors, every one on a net it routed)
ROUNDS = 3
# Pad-to-pad connections laid BEFORE Freerouting, on the board that holds only the kept copper
# and the fanout (pcb_route.complete, as pcb_route.prepare's connect_first), then fixed. Each is
# one Freerouting's rounds could not make on trial 5's board (2026-10-13: four left, round 4 on)
CONNECT_FIRST = [
    # J-MCU's two neighbouring 5 V pins: the source board joins them by a 0.4 mm link it did not
    # lock, so the copper strip took it; Freerouting never made it again
    ("J1.1", "J1.3"),
    # the USB OR-ing FET's gate to the controller, 5 mm: Freerouting ringed Q2.1 in with
    # BUCK_A_OUT (U13.3 - U13.6) and every round left it
    ("Q2.1", "U13.5"),
    # J-MCU pin 20 to the right-hand chain's last register: its way out of the header's top row
    # was taken by IO34 (F.Cu, y 133) and IO6 (B.Cu) before it was routed
    ("J1.20", "U8.9"),
]
COMPLETE_S = 40 * 60      # the grid completion's bound: past it the board as Freerouting left it


def step(code, timeout=None):
    """`code` in a fresh process (a just-saved board, as pcb.py does it), its output shown.
    With `timeout` (s), None when it runs out."""
    try:
        r = subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {TOOLS!r}); " + code],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    out = "\n".join(l for l in r.stdout.splitlines() if "Debug:" not in l and not l.startswith("route: WARNING"))
    if out:
        print(out)
    if r.returncode:
        sys.exit(f"fr_trial: failed: {code[:80]}\n{r.stderr[-3000:]}")
    return r.stdout


def first_pass(path, first, edge, directions):
    """The nets `first` names, routed by Freerouting ALONE on the board at `path` (every other
    pad unnetted on a copy, so it has nothing else to connect but stands as an obstacle), then
    copied onto the board fixed. The rest of the board is routed round them."""
    a = path.replace(".kicad_pcb", ".first.kicad_pcb")
    shutil.copy(path, a)
    shutil.copy(os.path.splitext(path)[0] + ".kicad_pro", os.path.splitext(a)[0] + ".kicad_pro")
    step("import pcbnew, fnmatch; "
         f"b = pcbnew.LoadBoard({a!r}); first = {first!r}; "
         "[p.SetNetCode(0) for f in b.GetFootprints() for p in f.Pads() "
         " if p.GetNetname() and not any(fnmatch.fnmatchcase(p.GetNetname(), g) for g in first)]; "
         f"pcbnew.SaveBoard({a!r}, b)")
    step(f"import pcb_freeroute; pcb_freeroute.route({a!r}, {edge!r}, {directions!r})")
    out = step("import pcbnew, fnmatch; "
               f"src = pcbnew.LoadBoard({a!r}); dst = pcbnew.LoadBoard({path!r}); first = {first!r}; n = 0\n"
               "for t in src.GetTracks():\n"
               "    if any(fnmatch.fnmatchcase(t.GetNetname(), g) for g in first):\n"
               "        c = t.Duplicate(); c.SetNet(dst.FindNet(t.GetNetname())); c.SetLocked(True); dst.Add(c); n += 1\n"
               f"pcbnew.SaveBoard({path!r}, dst); print('fr_trial: first pass', n, 'track(s) and via(s) fixed for', first)")
    return out


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
    # the named connections, laid before anything else and fixed
    import pcb_route as PR
    done = 0
    for a_, c_ in CONNECT_FIRST:
        pa = b.FindFootprintByReference(a_.split(".")[0]).FindPadByNumber(a_.split(".")[1])
        pc = b.FindFootprintByReference(c_.split(".")[0]).FindPadByNumber(c_.split(".")[1])
        before = {t.m_Uuid.AsString() for t in b.GetTracks()}
        at = [(pcbnew.ToMM(q.GetPosition().x), pcbnew.ToMM(q.GetPosition().y)) for q in (pa, pc)]
        left = PR.complete(b, lay, [(pa.GetNetname(), at[0], at[1])])
        for t in b.GetTracks():
            if t.m_Uuid.AsString() not in before:
                t.SetLocked(True)
        done += 0 if left else 1
        print(f"fr_trial: connect first {a_} - {c_} ({pa.GetNetname()}): {'FAILED' if left else 'laid, fixed'}")
    pcbnew.SaveBoard(path, b)
    # the board's own project, its net classes from layout.yaml (as pcb.py layout writes them)
    pro = os.path.splitext(path)[0] + ".kicad_pro"
    shutil.copy(os.path.join(HERE, "main-board.kicad_pro"), pro)
    j = json.load(open(pro))
    if lay.get("net_classes"):
        pcb.set_net_classes(j, lay)
        json.dump(j, open(pro, "w"), indent=2)
    edge = float(lay["rules"]["edge_clearance"])
    first = args[args.index("--first") + 1].split(",") if "--first" in args else FIRST
    if first and first != [""]:
        first_pass(path, first, edge, lay.get("directions"))
    rounds = int(args[args.index("--rounds") + 1]) if "--rounds" in args else ROUNDS
    for k in range(1, rounds + 1):
        step(f"import pcb_freeroute; pcb_freeroute.route({path!r}, {edge!r}, {lay.get('directions')!r})")
        step(f"import pcb_route; pcb_route.fill_zones({path!r})")
        left = step(f"import pcb; print('LEFT', len(pcb.unconnected_of({path!r})))")
        n = int(left.split("LEFT", 1)[1].split()[0]) if left and "LEFT" in left else -1
        print(f"fr_trial: Freerouting round {k}: {n} connection(s) left")
        if n == 0:
            break
    if "--complete" in args:
        # the whole of pcb.py's post_route: what Freerouting left, routed by the grid router with
        # rip-up, tidied, the silkscreen. BOUNDED: unbounded, 13 connections ran past two hours
        # (2026-10-13); past COMPLETE_S the board goes back to Freerouting's, and what is left
        # is reported
        back = path + ".before-complete"
        shutil.copy(path, back)
        if step(f"import pcb; pcb.post_route({path!r}, {HERE!r})", timeout=COMPLETE_S) is None:
            shutil.copy(back, path)
            print(f"fr_trial: the completion ran past {COMPLETE_S} s - the board as Freerouting left it")
            step("import pcbnew, yaml, pcb_route; "
                 f"lay = yaml.safe_load(open({os.path.join(HERE, 'layout.yaml')!r})); b = pcbnew.LoadBoard({path!r}); "
                 f"pcb_route.tidy(b, lay); pcbnew.SaveBoard({path!r}, b)")
    else:
        # tidied (plane orphans their via, doubled and dangling tracks off) - and KEPT ONLY IF it
        # leaves no more connections apart than it found: on trials 5 and 7 (2026-10-13) the tidy
        # took apart one and two connections Freerouting had made
        count = lambda: int(step(f"import pcb; print('LEFT', len(pcb.unconnected_of({path!r})))")
                            .split("LEFT", 1)[1].split()[0])
        n0 = count()
        back = path + ".before-tidy"
        shutil.copy(path, back)
        step("import pcbnew, yaml, pcb_route; "
             f"lay = yaml.safe_load(open({os.path.join(HERE, 'layout.yaml')!r})); b = pcbnew.LoadBoard({path!r}); "
             "o = pcb_route.plane_orphans(b, lay); "
             "o and pcb_route.fanout(b, lay, pcb_route.Obstacles(b, lay), only=o); "
             f"pcb_route.tidy(b, lay); pcbnew.SaveBoard({path!r}, b)")
        step(f"import pcb_route; pcb_route.fill_zones({path!r})")
        n1 = count()
        if n1 > n0:
            shutil.copy(back, path)
            print(f"fr_trial: the tidy left {n1} connection(s) apart where Freerouting left {n0} - not kept")
        else:
            print(f"fr_trial: tidied ({n0} -> {n1} apart)")
    step(f"import pcb_route; pcb_route.fill_zones({path!r})")
    md = os.path.join(out, "score.md")
    step(f"import pcb_score; rows = pcb_score.score({path!r}, everything=True); t = pcb_score.totals(rows); "
         f"open({md!r}, 'w').write(pcb_score.markdown(rows, 'main-board.fr')); print('fr_trial: score', t); "
         f"print('fr_trial: open', [r['net'] for r in rows if r['open']])")
    step(f"import pcb_route2 as R; e, u = R.drc({path!r}); import collections; "
         f"print('fr_trial: KiCad DRC', len(e), 'error(s)', dict(collections.Counter(x[0] for x in e)), u, 'unconnected')")
    # what is still apart, by net: the placement loop's input
    step(f"import pcb; m = pcb.unconnected_of({path!r}); import collections; "
         "c = collections.Counter(x[0] for x in m); print('fr_trial: unrouted by net', dict(c.most_common()))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
