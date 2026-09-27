#!/usr/bin/env python3
"""Board netlists assembled from the circuit netlists - one file per physical board.

    python3 tools/board.py build hardware/boards/key-board-rh   # write board-netlist.yaml
    python3 tools/board.py check hardware/boards/key-board-rh   # exit 1 if it no longer follows its sources

WHY. The circuit netlists under hardware/ are written ONCE PER CIRCUIT and
replicated: one key-register for four registers, one key-switch-network for
every switch position. A board is several of those, wired to each other and to
its connector, with the per-board choices (which key sits on which register
input) filled in. Writing that out by hand would be a second copy of every
circuit, which is this repository's named failure waiting to happen. So a
board is GENERATED from:

  board.yaml                                  which board, which cluster, its connector,
                                              and what the register's ports are called here
  hardware/cluster/key-register/netlist.yaml  the register and its decoupler
  hardware/cluster/key-switch-network/...     one network per switch position
  hardware/cluster/key-marker-and-bits/...    the free-bit pull-ups, and allocation.yaml:
                                              what every register input carries
  hardware/interfaces/key-chain-loom/...      the board's J-CHAIN, pin by pin, and the
                                              net names the ribbon gives each conductor
  config/key-layout.yaml                      that every key named exists, on this cluster

The output, board-netlist.yaml, is in the same format as a circuit netlist, so
tools/sch.py draws it and proves the drawing against it. It is named so that
tools/check-netlist.py (which checks CIRCUITS against the BOM) does not count
a board's parts a second time.

Reference designators on a board are the circuit's refdes with the instance
appended - R-KEY-PU-RH1 is the pull-up of key RH1 - and every part carries
`of:` naming its BOM row.

`build` also proves allocation.yaml against the table in key-marker-and-bits.md
§4, which is its written form. If they disagree, nothing is written.
"""
import hashlib
import os
import re
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLUSTER = os.path.join(ROOT, "hardware", "cluster")
LOOM = os.path.join(ROOT, "hardware", "interfaces", "key-chain-loom", "netlist.yaml")
ALLOC = os.path.join(CLUSTER, "key-marker-and-bits", "allocation.yaml")
ALLOC_PAGE = os.path.join(CLUSTER, "key-marker-and-bits", "key-marker-and-bits.md")
LAYOUT = os.path.join(ROOT, "config", "key-layout.yaml")
SOURCES = [os.path.join(CLUSTER, "key-register", "netlist.yaml"),
           os.path.join(CLUSTER, "key-switch-network", "netlist.yaml"),
           os.path.join(CLUSTER, "key-marker-and-bits", "netlist.yaml"),
           ALLOC, ALLOC_PAGE, LOOM, LAYOUT]


def y(path):
    return yaml.safe_load(open(path))


def members(netlist, name):
    return [m for m in netlist["nets"].get(name, []) if isinstance(m, str)]


def git_blob(path):
    r = subprocess.run(["git", "hash-object", path], capture_output=True, text=True, cwd=ROOT)
    return r.stdout.strip() or hashlib.sha1(open(path, "rb").read()).hexdigest()


def fingerprint(bdir):
    h = hashlib.sha1()
    for f in [os.path.join(bdir, "board.yaml"), os.path.abspath(__file__)] + SOURCES:
        h.update((os.path.relpath(f, ROOT) + git_blob(f)).encode())
    return h.hexdigest()[:12]


def check_allocation_page(alloc):
    """allocation.yaml must say what key-marker-and-bits.md §4's table says."""
    text = open(ALLOC_PAGE).read()
    sec = text[text.index("### Allocation"):]
    problems = []
    for cluster, row in alloc["registers"].items():
        m = re.search(r"^\| `%s` \| [^|]+\|(.*)\|\s*$" % cluster, sec, re.M)
        if not m:
            problems.append(f"{cluster}: no row in {os.path.relpath(ALLOC_PAGE, ROOT)} §4")
            continue
        cells = [c.strip().strip("*") for c in m.group(1).split("|")]
        for cell, item in zip(cells, row):
            want = {"M0": "M", "M1": "M", "sw+": "sw+", "sw-": "sw−"}.get(item, "free" if item.startswith("FREE") else item)
            if cell != want:
                problems.append(f"{cluster}: allocation.yaml says {item}, the page's table says {cell}")
    return problems


def build(bdir):
    bdef = y(os.path.join(bdir, "board.yaml"))
    reg = y(SOURCES[0])
    net_sw = y(SOURCES[1])
    marker = y(SOURCES[2])
    alloc = y(ALLOC)
    loom = y(LOOM)
    layout = y(LAYOUT)
    problems = check_allocation_page(alloc)

    cluster, sfx = bdef["cluster"], bdef["suffix"]
    rn = bdef["register_nets"]
    rail, gnd = rn["V3V3_CHAIN"], rn["GND_CHAIN"]
    keys = {k["id"]: k for k in layout["keys"]}

    comps, nets = {}, {}

    def add(net, pin):
        nets.setdefault(net, []).append(pin)

    def part(ref, src_ref, src, of=None):
        c = src["components"][src_ref]
        comps[ref] = {"of": of or c.get("of", src_ref), "value": str(c.get("value", "")),
                      "pins": list(c["pins"])}

    # -- the register: its ports become the ribbon's net names on this board
    u = f"U-KEYS-{sfx}"
    part(u, "U-KEYS", reg)
    part(f"C-DECOUPLE-165-{sfx}", "C-DECOUPLE-165", reg)
    rename = {"U-KEYS": u, "C-DECOUPLE-165": f"C-DECOUPLE-165-{sfx}"}
    for name, plist in reg["nets"].items():
        if name.startswith("KEY_IN_"):
            continue
        target = rn.get(name, f"{name}_{sfx}")
        for m in plist:
            if isinstance(m, str):
                ref, pin = m.rsplit(".", 1)
                add(target, f"{rename[ref]}.{pin}")
    ext = [f"QH_BAR_{sfx}"]

    # -- what each parallel input carries
    row = alloc["registers"][cluster]
    for inp, item in zip(alloc["order"], row):
        pin = f"{u}.{inp}"
        if item in ("M0", "M1"):
            add(gnd if item == "M0" else rail, pin)
        elif item.startswith("FREE"):
            r = f"R-KEY-PU-{item}"
            part(r, r, marker, of="R-KEY-PU")
            add(rail, f"{r}.1")
            add(f"KEY_{item}", f"{r}.2")
            add(f"KEY_{item}", pin)
        else:
            if item in ("sw+", "sw-"):
                problems.append(f"{cluster}: {item} is a spare-switch position; this tool does not draw DNP switches yet")
                continue
            k = keys.get(item)
            if not k or k.get("cluster") != cluster:
                problems.append(f"{item}: not a {cluster} key in config/key-layout.yaml")
                continue
            node = f"KEY_{item}"
            names = {"R-KEY-PU": f"R-KEY-PU-{item}", "R-KEY-SER": f"R-KEY-SER-{item}",
                     "C-KEY": f"C-KEY-{item}", "SW1-n": f"SW-{item}"}
            for src_ref, ref in names.items():
                part(ref, src_ref, net_sw)
            local = {"V3V3_CHAIN": rail, "GND_CHAIN": gnd, "KEY_NODE": node, "SWITCH_LEG": f"SW_{item}"}
            for name, plist in net_sw["nets"].items():
                for m in plist:
                    if isinstance(m, str):
                        ref, p = m.rsplit(".", 1)
                        add(local[name], f"{names[ref]}.{p}")
            add(node, pin)

    # -- the connector: its pins and their nets, as the ribbon's netlist has them
    jref = bdef["connector"]
    jnew = bdef.get("connector_as", "J-CHAIN")
    comps[jnew] = {"of": loom["components"][jref].get("of", jref), "value": str(loom["components"][jref]["value"]),
                   "pins": list(loom["components"][jref]["pins"])}
    used = set(rn.values())
    for name, plist in loom["nets"].items():
        for m in members(loom, name):
            ref, p = m.rsplit(".", 1)
            if ref != jref:
                continue
            if name in used:
                add(name, f"{jnew}.{p}")
            elif name.startswith("CHAIN_SPARE"):
                add(name, f"{jnew}.{p}")
                ext.append(name)
            else:
                problems.append(f"{jref}.{p} is on the ribbon's net {name}, which board.yaml does not map")
    for want in used:
        if not any(x.startswith(jnew + ".") for x in nets.get(want, [])):
            problems.append(f"board net {want} reaches no {jref} pin - is register_nets right?")

    if problems:
        return None, problems
    fp = fingerprint(bdir)
    out = {
        "board": bdef["name"], "title": bdef["title"], "pcb": bdef.get("pcb"),
        "fingerprint": fp,
        "components": dict(sorted(comps.items())),
        "nets": {k: v for k, v in sorted(nets.items())},
        "external_endpoints": sorted(ext),
    }
    head = (f"# GENERATED by tools/board.py - do not edit. Fingerprint {fp}.\n"
            f"# Board {bdef['name']}: {bdef['title']}. Sources: board.yaml beside this file,\n"
            + "".join(f"#   {os.path.relpath(s, ROOT)}\n" for s in SOURCES) +
            "# Regenerate: python3 tools/board.py build " + os.path.relpath(bdir, ROOT) + "\n")
    return head + yaml.safe_dump(out, sort_keys=False, width=100), []


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("build", "check"):
        print(__doc__)
        return 2
    bdir = os.path.join(ROOT, sys.argv[2].rstrip("/"))
    text, problems = build(bdir)
    rel = os.path.relpath(bdir, ROOT)
    if problems:
        print(f"board: {rel}: FAIL")
        for p in problems:
            print("  " + p)
        return 1
    path = os.path.join(bdir, "board-netlist.yaml")
    if sys.argv[1] == "check":
        if not os.path.exists(path) or open(path).read() != text:
            print(f"board: {rel}/board-netlist.yaml is STALE - run: python3 tools/board.py build {rel}")
            return 1
        print(f"board: PASS {rel}/board-netlist.yaml follows its sources")
        return 0
    open(path, "w").write(text)
    d = yaml.safe_load(text)
    print(f"board: wrote {rel}/board-netlist.yaml - {len(d['components'])} parts, {len(d['nets'])} nets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
