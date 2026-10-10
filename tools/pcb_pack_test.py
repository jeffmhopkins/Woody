"""The cluster packer (tools/pcb_pack.py, issue #46) on constructed boards
(tools/pcb_testboards.py). Each cell in its own process; every packed board is also
checked by KiCad's own DRC (courtyards, footprints in rule areas), not only by the
packer's rule list.

    python3 tools/pcb_pack_test.py               # every cell; exit 1 on a failure
    python3 tools/pcb_pack_test.py --plot DIR    # ...and a 2D plot of each routed result

  minikey      the three-key board's heap: register cluster, header cluster, one key T stamped
               at all three switches - every seat legal, the same T at every switch
  density      the same board at spacing 0.4 and 1.5 mm, J1 with a 3 mm escape band: the least
               gap between packed courtyards is at least the spacing, nothing in the band
  moat         J7's series parts and ferrites dropped on the moat and in the island's mouth:
               packed clear of both, airwires no longer crossing the keep-out
  contain      the island ADC's filter, dumped off the island: packed wholly inside it
  refuse       a body-owned part or the anchor named in --parts is refused; a locked part
               named there is released, and the report says so
  nofit        a box too tight for the row: refused with the side and the parts named
  report       the place report: problems before the pack, none after (its exit code)
  route        the packed island board routed by pcb_route2: DRC clean
"""
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CELLS = ["minikey", "density", "moat", "contain", "refuse", "nofit", "report", "route"]
MINIBODY = ["SW1", "SW2", "SW3", "J1", "H1", "H2", "H3", "H4"]
ISLBODY = ["J7", "H11", "H1", "H2", "H3", "H4", "TP1"]


def _setup():
    import pcbnew
    import pcb_pack as P
    import pcb_route2 as R2
    import pcb_testboards as T
    return pcbnew, P, R2, T


def drc_place(R2, path):
    """KiCad's placement findings on a saved board: courtyards overlapping and footprints
    in a rule area that forbids them."""
    errs, _ = R2.drc(path, fill=False)
    return [e for e in errs if e[0] in ("courtyards_overlap", "items_not_allowed", "footprint")]


def cell_minikey(out, plot):
    pcbnew, P, R2, T = _setup()
    b = T.minikey()
    bd = P.board_of(b)
    pk = P.Packer(bd, MINIBODY)
    roles = {f"SW{k}": list(T.MINIKEY["keys"][k]) for k in (1, 2, 3)}
    reps = [pk.pack("U1", ["C6", "R11"]), pk.pack("J1", ["C7"]), pk.pattern(["SW1", "SW2", "SW3"], roles)]
    moved = ["C6", "R11", "C7"] + [r for a in roles for r in roles[a]]
    rules = {r: P.violations(bd, pk.placed[r], pk.placed) for r in moved}
    rules = {r: v for r, v in rules.items() if v}
    # the same T at every switch: each role's offset from its switch identical
    offs = []
    for k in range(3):
        o = set()
        for a in roles:
            sx, sy = pk.placed[a].court.centroid.x, pk.placed[a].court.centroid.y
            px, py = pk.placed[roles[a][k]].centroid
            o.add((round(px - sx, 3), round(py - sy, 3)))
        offs.append(len(o))
    pk.apply(b)
    p = os.path.join(out, "minikey-packed.kicad_pcb")
    pcbnew.SaveBoard(p, b)
    kd = drc_place(R2, p)
    res = {"results": [r["result"] for r in reps], "rule_breaks": rules, "drc_placement": kd[:5], "same_T": offs,
           "arrangement": reps[2].get("arrangement"), "configurations": reps[2].get("configurations")}
    res["pass"] = all(r["result"] == "packed" for r in reps) and not rules and not kd and offs == [1, 1, 1]
    return res


def cell_density(out, plot):
    pcbnew, P, R2, T = _setup()
    res = {}
    for spacing in (0.4, 1.5):
        b = T.minikey()
        bd = P.board_of(b, rails=["GND", "V3V3"])
        pk = P.Packer(bd, MINIBODY, spacing=spacing, escape={"J1": ("W", 3.0)})
        roles = {f"SW{k}": list(T.MINIKEY["keys"][k]) for k in (1, 2, 3)}
        reps = [pk.pack("U1", ["C6", "R11"]), pk.pack("J1", ["C7"]), pk.pattern(["SW1", "SW2", "SW3"], roles)]
        moved = ["C6", "R11", "C7"] + [r for a in roles for r in roles[a]]
        others = [r for r in pk.placed if r not in moved and pk.placed[r].side == "F"]
        gap = min(pk.placed[a].court.distance(pk.placed[c].court) for a in moved for c in moved + others if a != c)
        band = pk.escape_bands()[0]
        inband = [r for r in moved if pk.placed[r].court.intersection(band).area > 1e-6]
        res[spacing] = {"results": [r["result"] for r in reps], "least_gap": round(gap, 3), "in_escape_band": inband}
    res["pass"] = all(all(x == "packed" for x in res[s_]["results"]) and res[s_]["least_gap"] >= s_ - 0.01
                      and not res[s_]["in_escape_band"] for s_ in (0.4, 1.5))
    return res


def cell_moat(out, plot):
    pcbnew, P, R2, T = _setup()
    b = T.island()
    bd = P.board_of(b, ["AGND"])
    parts = ["R50", "R51", "FB3", "FB4"]
    before = P.score(bd, parts, bd.parts)
    pk = P.Packer(bd, ISLBODY)
    rep = pk.pack("J7", parts)
    after = P.score(bd, parts, pk.placed)
    rules = {r: P.violations(bd, pk.placed[r], pk.placed) for r in parts}
    rules = {r: v for r, v in rules.items() if v}
    pk.apply(b)
    p = os.path.join(out, "island-moat.kicad_pcb")
    pcbnew.SaveBoard(p, b)
    kd = [e for e in drc_place(R2, p) if any(x in " ".join(e[2]) for x in parts)]
    res = {"result": rep["result"], "sides": rep.get("sides"), "seats": rep.get("seats"), "before": before, "after": after,
           "rule_breaks": rules, "drc_placement": kd[:5]}
    # before: airwires across the keep-out or the island; after: none, and nothing breaks a rule
    res["pass"] = rep["result"] == "packed" and before[0] > 0 and after[0] == 0 and not rules and not kd
    return res


def cell_contain(out, plot):
    pcbnew, P, R2, T = _setup()
    b = T.island()
    bd = P.board_of(b, ["AGND"])
    parts = ["R10", "C10", "C11"]
    pk = P.Packer(bd, ISLBODY)
    rep = pk.pack("U2", parts)
    isl = bd.islands["AGND"]
    inside = {r: isl.contains(pk.placed[r].court) for r in parts if "AGND" in pk.placed[r].nets()}
    # R10 has no AGND pad: it may not stand over the island at all
    over = {r: pk.placed[r].court.intersection(isl).area > 1e-6 for r in parts if "AGND" not in pk.placed[r].nets()}
    rules = {r: P.violations(bd, pk.placed[r], pk.placed) for r in parts}
    rules = {r: v for r, v in rules.items() if v}
    pk.apply(b)
    p = os.path.join(out, "island-contain.kicad_pcb")
    pcbnew.SaveBoard(p, b)
    kd = [e for e in drc_place(R2, p) if any(x in " ".join(e[2]) for x in parts)]
    res = {"result": rep["result"], "seats": rep.get("seats"), "inside_island": inside, "foreign_over_island": over,
           "rule_breaks": rules, "drc_placement": kd[:5]}
    res["pass"] = rep["result"] == "packed" and all(inside.values()) and not any(over.values()) and not rules and not kd
    return res


def cell_refuse(out, plot):
    pcbnew, P, R2, T = _setup()
    b = T.island()
    res = {}
    for tag, parts in (("body", ["R50", "H11"]), ("anchor", ["R50", "J7"])):
        bd = P.board_of(b, ["AGND"])
        try:
            P.Packer(bd, ISLBODY).pack("J7", parts)
            res[tag] = "accepted"
        except SystemExit as e:
            res[tag] = str(e)
    bd = P.board_of(b, ["AGND"])
    bd.parts["R50"].locked = True
    pk = P.Packer(bd, ISLBODY)
    rep = pk.pack("J7", ["R50", "R51", "FB3", "FB4"])
    res["lock"] = pk.log
    res["lock_result"] = rep["result"]
    # a locked part is not in the default set
    bd2 = P.board_of(b, ["AGND"])
    bd2.parts["R50"].locked = True
    res["default_set"] = P.Packer(bd2, ISLBODY).movable("J7")
    res["pass"] = "body CAD" in res["body"] and "the anchor does not move" in res["anchor"] and any("place lock released: R50" in l for l in pk.log) \
        and rep["result"] == "packed" and "R50" not in res["default_set"]
    return res


def cell_nofit(out, plot):
    pcbnew, P, R2, T = _setup()
    b = T.island()
    bd = P.board_of(b, ["AGND"])
    # a row held to the north of H11, within 1 mm: that is the island's arm, so there is none
    rep = P.Packer(bd, ISLBODY).pack("H11", ["R50", "R51", "FB3", "FB4"], side=["N"], grow=1.0)
    res = {"result": rep["result"]}
    res["pass"] = rep["result"].startswith("no legal row on side N") and "nearest row" in rep["result"] \
        and "0 seats" not in rep["result"]
    return res


def cell_report(out, plot):
    pcbnew, P, R2, T = _setup()
    b = T.island()
    p0 = os.path.join(out, "island-before.kicad_pcb")
    pcbnew.SaveBoard(p0, b)
    bd = P.board_of(b, ["AGND"])
    pk = P.Packer(bd, ISLBODY)
    pk.pack("J7", ["R50", "R51", "FB3", "FB4"])
    pk.pack("U2", ["R10", "C10", "C11"])
    pk.apply(b)
    p1 = os.path.join(out, "island-after.kicad_pcb")
    pcbnew.SaveBoard(p1, b)
    codes = []
    texts = []
    for p in (p0, p1):
        r = subprocess.run([sys.executable, os.path.join(HERE, "pcb_pack.py"), "report", p, "--anchors", "J7,U2", "--island", "AGND",
                            "--body", ",".join(ISLBODY)], capture_output=True, text=True)
        codes.append(r.returncode)
        texts.append(r.stdout.strip())
    res = {"exit_codes": codes, "before": texts[0], "after": texts[1]}
    res["pass"] = codes == [1, 0]
    return res


def cell_route(out, plot):
    pcbnew, P, R2, T = _setup()
    b = T.island()
    bd = P.board_of(b, ["AGND"])
    pk = P.Packer(bd, ISLBODY)
    a = pk.pack("J7", ["R50", "R51", "FB3", "FB4"])
    c = pk.pack("U2", ["R10", "C10", "C11"])
    pk.apply(b)
    lay = {"rules": {"track": 0.25, "track_min": 0.2, "clearance": 0.2, "via": 0.7, "via_drill": 0.3, "edge_clearance": 0.3},
           "fab": {"hole_to_hole": 0.25, "hole_clearance": 0.25}}
    m = R2.model_from_board(b, lay)
    r = R2.Router(m, flow=0.3)
    failed = r.route()
    R2.write(b, m, r.runs)
    p = os.path.join(out, "island-routed.kicad_pcb")
    pcbnew.SaveBoard(p, b)
    errs, unc = R2.drc(p)
    if plot:
        import pcb_plot
        pcb_plot.plot(p, os.path.join(plot, "pack-island-routed.png"), nets=["*"], title="pack + route2: island board")
    res = {"packed": [a["result"], c["result"]], "failed": failed, "drc_errors": len(errs), "unconnected": unc,
           "drc": [e[:2] for e in errs[:5]], **r.summary()}
    res["pass"] = a["result"] == c["result"] == "packed" and not failed and not errs and unc == 0
    return res


def main():
    args = sys.argv[1:]
    plot = None
    if "--plot" in args:
        i = args.index("--plot")
        plot = os.path.abspath(args[i + 1])
        os.makedirs(plot, exist_ok=True)
        del args[i:i + 2]
    if args and args[0] == "--cell":
        t0 = time.monotonic()
        res = globals()["cell_" + args[1]](args[2], plot)
        res["seconds"] = round(time.monotonic() - t0, 1)
        print("RESULT " + json.dumps(res, default=str))
        return 0
    out = tempfile.mkdtemp(prefix="pack-bench-")
    ok = True
    for c in args or CELLS:
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "--cell", c, out] + (["--plot", plot] if plot else []),
                           capture_output=True, text=True)
        line = [l for l in p.stdout.splitlines() if l.startswith("RESULT ")]
        if p.returncode or not line:
            print(f"{c:8s} FAIL (crashed)\n{p.stderr[-1500:]}")
            ok = False
            continue
        res = json.loads(line[-1][7:])
        passed = res.pop("pass")
        ok &= passed
        print(f"{c:8s} {'PASS' if passed else 'FAIL'}  {json.dumps(res, default=str)}")
    print(f"boards in {out}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
