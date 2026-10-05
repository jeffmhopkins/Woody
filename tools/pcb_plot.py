"""A board's routing in 2D, a chosen set of nets in colour and everything else grey:
how a routing trial is inspected (.claude/skills/pcb-routing/SKILL.md). Read-only - it
loads a .kicad_pcb and writes a PNG, nothing else.

    python3 tools/pcb_plot.py <board dir or .kicad_pcb> -o out.png --nets IO2,/midi-out/*
    python3 tools/pcb_plot.py <board> -o out.png --family buses     # layout.yaml families:
    python3 tools/pcb_plot.py <board> -o out.png --family rest --window 200,0,300,60 --labels J1,U6

--nets takes names (with or without the leading /) and fnmatch globs; --family takes
a family's name from the board's layout.yaml `families:` (or `route_first`, or
`rest`), resolved exactly as pcb_route routes it. --layout points at another
layout.yaml (a trial's, beside a scratch copy of the board). --window is
x0,y0,x1,y1 in the board's own mm (KiCad's frame: y grows downward), which is also the
frame of a family's `region:`. Front copper solid, back dashed, an inner layer dotted;
a via a dot; each net's length and via count in the legend.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PALETTE = ["#e6194b", "#1f77ff", "#2ca02c", "#ff7f0e", "#9467bd", "#17becf", "#8c564b", "#e377c2",
           "#bcbd22", "#7f7f7f", "#00429d", "#93003a"]


def resolve(board, layout, nets=None, family=None):
    """The net names on `board` to colour: `nets` patterns, and/or a family's."""
    import pcb_route
    allnets = sorted(str(n) for n in board.GetNetsByName().keys() if str(n))
    out = []
    if nets:
        out += [n for n in allnets if pcb_route.family_match(n, nets, {"net_classes": (layout or {}).get("net_classes")})]
    if family:
        if layout is None:
            sys.exit("pcb_plot: --family needs the board's layout.yaml (--layout)")
        plan = pcb_route.family_plan(layout, allnets)
        hit = [n for s_, ns in plan if s_["name"] == family for n in ns]
        if not any(s_["name"] == family for s_, _ in plan):
            sys.exit(f"pcb_plot: no family {family!r}; the board's are {', '.join(s_['name'] for s_, _ in plan)}")
        out += sorted(hit)
    return list(dict.fromkeys(out))


def plot(pcb, out, nets=None, family=None, layout=None, window=None, labels=None, title=None):
    import pcbnew
    import yaml
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle
    if os.path.isdir(pcb):
        pcb = os.path.join(pcb, os.path.basename(os.path.normpath(pcb)) + ".kicad_pcb")
    if layout is None and os.path.exists(os.path.join(os.path.dirname(pcb), "layout.yaml")):
        layout = os.path.join(os.path.dirname(pcb), "layout.yaml")
    lay = yaml.safe_load(open(layout)) if isinstance(layout, str) else layout
    b = pcbnew.LoadBoard(pcb)
    chosen = resolve(b, lay, nets, family)
    col = {n: PALETTE[k % len(PALETTE)] for k, n in enumerate(chosen)}
    mm = lambda v: v / 1e6
    fig, ax = plt.subplots(figsize=(14, 9), dpi=110)
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            s, e = d.GetStart(), d.GetEnd()
            ax.plot([mm(s.x), mm(e.x)], [mm(s.y), mm(e.y)], color="k", lw=1)
    bb = b.GetBoardEdgesBoundingBox()
    ax.add_patch(Rectangle((mm(bb.GetX()), mm(bb.GetY())), mm(bb.GetWidth()), mm(bb.GetHeight()), fill=False, ec="k", lw=0.6))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            c = col.get(p.GetNetname())
            bx = p.GetBoundingBox()
            ax.add_patch(Rectangle((mm(bx.GetX()), mm(bx.GetY())), mm(bx.GetWidth()), mm(bx.GetHeight()),
                                   fc=c or "#eeeeee", ec="none", alpha=0.55 if c else 1.0, zorder=1 if c else 0))
    stats = {n: [0.0, 0] for n in chosen}
    style = {pcbnew.F_Cu: "-", pcbnew.B_Cu: (0, (2, 1))}
    for t in b.GetTracks():
        n = t.GetNetname()
        c = col.get(n)
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            if c:
                ax.add_patch(Circle((mm(p.x), mm(p.y)), 0.45, color=c, zorder=5))
                stats[n][1] += 1
            else:
                ax.add_patch(Circle((mm(p.x), mm(p.y)), 0.25, color="#cccccc", zorder=1))
            continue
        s, e = t.GetStart(), t.GetEnd()
        if c:
            ax.plot([mm(s.x), mm(e.x)], [mm(s.y), mm(e.y)], color=c, lw=2.4, ls=style.get(t.GetLayer(), ":"),
                    zorder=4, solid_capstyle="round")
            stats[n][0] += mm(t.GetLength())
        else:
            ax.plot([mm(s.x), mm(e.x)], [mm(s.y), mm(e.y)], color="#d8d8d8", lw=0.6, zorder=0)
    for fp in b.GetFootprints():
        if labels and fp.GetReference() in labels:
            p = fp.GetPosition()
            ax.text(mm(p.x), mm(p.y), fp.GetReference(), fontsize=9, weight="bold", ha="center", va="center", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.15", fc="#fff8c0", ec="#888", lw=0.5))
    for n in chosen:
        ax.plot([], [], color=col[n], lw=2.4, label=f"{n}  {stats[n][0]:.0f} mm, {stats[n][1]} via(s)")
    if chosen:
        ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8, frameon=False)
    ax.set_aspect("equal")
    if window:
        x0, y0, x1, y1 = window
        ax.set_xlim(min(x0, x1), max(x0, x1))
        ax.set_ylim(min(y0, y1), max(y0, y1))
    ax.invert_yaxis()
    ax.set_xlabel("board mm (KiCad frame)")
    tot = sum(v[0] for v in stats.values()), sum(v[1] for v in stats.values())
    ax.set_title((title or os.path.basename(pcb)) + (f" - family {family}" if family else "") +
                 f"\n{len(chosen)} net(s): {tot[0]:.0f} mm, {tot[1]} via(s)   solid = front, dashed = back, dotted = inner",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("board", help="a board directory or a .kicad_pcb")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--nets", help="comma-separated names or globs")
    ap.add_argument("--family", help="a family name from layout.yaml families: (or route_first, rest)")
    ap.add_argument("--layout", help="the layout.yaml (default: beside the board)")
    ap.add_argument("--window", help="x0,y0,x1,y1 in board mm")
    ap.add_argument("--labels", help="comma-separated references to label")
    ap.add_argument("--title")
    a = ap.parse_args()
    if not a.nets and not a.family:
        ap.error("name --nets or --family")
    stats = plot(a.board, a.out, nets=a.nets.split(",") if a.nets else None, family=a.family, layout=a.layout,
                 window=[float(v) for v in a.window.split(",")] if a.window else None,
                 labels=a.labels.split(",") if a.labels else None, title=a.title)
    for n, (L, v) in stats.items():
        print(f"{n}: {L:.1f} mm, {v} via(s)")
    print(f"pcb_plot: wrote {a.out}")


if __name__ == "__main__":
    main()
