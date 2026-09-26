#!/usr/bin/env python3
"""Prove the `## Interfaces` tables against hardware/nets.yaml and the netlists.

WHY THIS EXISTS. `hardware/nets.yaml`'s own header says it was SEEDED FROM THE
23 `## Interfaces` TABLES. Then 22 netlists were written, a dozen master
entries changed driver or receivers, six were deleted as not being crossings,
two were merged and several split - and nothing ever compared the result back
to the tables. `tools/check-netlist.py` proves the master against the
per-circuit `ports:` blocks, so the netlists and the master were made to agree
with EACH OTHER while the pages they came from were left behind. A 2026-09-26
cold slice walked all 55 nets and 151 endpoint assertions by hand and found 22
defects, and said 14 of them would be caught by a check that read the Dir and
Peer cells. This is that check.

WHAT IT CHECKS

    peers     every Peer cell names a real circuit id, a known non-circuit
              (a connector, a part, a board with no page) or `-`
    symmetry  if page A names circuit B as a Peer with a direction, B's table
              names A back. This is hardware/README.md's rule for a `circuit:`
              edge, applied to the tables the edges come from.
    edges     circuit.yaml's `circuit:` edges and the table's Peer column are
              the same set, in both directions
    dirs      where a Node cell names a master net, the row's Dir agrees with
              that net's role in hardware/nets.yaml

WHAT IT CANNOT CHECK, AND SAYS SO. A Node cell is prose: `DAC ch1`,
`MODULE ANALOG +12V`, three nets in one cell. Rows whose node does not resolve
to a master net are COUNTED AND LISTED, never silently skipped - an unresolved
row is the gap, and hiding it would be this repository's whole failure mode
wearing a tool as a disguise.

Usage:  python3 tools/check-interfaces.py [--verbose]
Exit:   0 clean, 1 problems
"""
import glob, os, re, sys, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERBOSE = "--verbose" in sys.argv

# Peers that are legitimately NOT circuits. hardware/README.md: the Peer column
# holds "a reference designator or part name when it is not" a circuit, and
# HDR-DEV in particular "creates no edge".
NON_CIRCUIT = {
    "HDR-DEV", "HDR-SERVICE", "SW-THUMB", "SW-POWER", "J-UMB", "J-CHAIN",
    "J-DISP", "J-LED-L", "J-LED-R", "U-LOADSW", "the two WS2815 strips",
    "the head of each strip", "REF5050", "MCP3202",
}
DIR_OK = {"in", "out", "in/out", "ref", "—", "-", ""}


def cell(text):
    return re.sub(r"[`*]", "", text).strip()


def tables():
    """(circuit_id, page, [rows]) for every page carrying an Interfaces table."""
    # A PAGE'S CIRCUIT IS THE ONE WHOSE NETLIST NAMES IT, not the one in its
    # own directory. carrier/mcu's netlist sits in a subdirectory and points at
    # ../carrier.md, and keying off the directory silently attributed that page
    # to nothing - which made every one of its circuit: edges look unbacked.
    ids = {}
    for f in glob.glob(os.path.join(ROOT, "hardware/**/circuit.yaml"), recursive=True):
        spec = yaml.safe_load(open(f, encoding="utf-8")) or {}
        ids[os.path.dirname(f)] = spec.get("id")
    # WHEN SEVERAL NETLISTS NAME ONE PAGE, only the page can say whose table it
    # carries. Four circuits point at carrier.md - three of them merely draw on
    # it and have tables of their own - so inferring from `page:` picked
    # whichever the glob reached first. An explicit marker beside the table is
    # the same shape as `<!-- netlist: none -->` and cannot be guessed wrong.
    page_circuit = {}
    for page in glob.glob(os.path.join(ROOT, "hardware/**/*.md"), recursive=True):
        m = re.search(r"<!--\s*interfaces:\s*([a-z0-9/-]+)\s*-->",
                      open(page, encoding="utf-8").read())
        if m:
            page_circuit[os.path.realpath(page)] = m.group(1)
    out = []
    for page in sorted(glob.glob(os.path.join(ROOT, "hardware/**/*.md"), recursive=True)):
        if os.path.basename(page) in ("README.md", "notes.md"):
            continue
        lines = open(page, encoding="utf-8").read().split("\n")
        # COLUMNS BY NAME, NOT BY POSITION, and a first cell that only has to
        # START with Node. Two tables head it `| Node / part |` and two carry an
        # extra `End` column, and the first version of this keyed off the exact
        # strings `| Node | Dir |` and `| Node | End |` - so it did not parse
        # breath-sense-link or breath-receive-stage AT ALL. Every circuit: edge
        # on those two then looked unbacked and nobody looked like naming them
        # back: 9 of the first run's problems were this detector, not the
        # corpus. A checker keyed to one spelling is the defect it is looking
        # for, wearing a tool as a disguise.
        head = None
        for n, l in enumerate(lines):
            if not l.startswith("|"):
                continue
            c = [cell(x).lower() for x in l.strip().strip("|").split("|")]
            if c and c[0].startswith("node") and "dir" in c and "peer" in c:
                head, cols = n, c
                break
        if head is None:
            continue
        di, pi = cols.index("dir"), cols.index("peer")
        end = next((n for n in range(head + 2, len(lines))
                    if not lines[n].startswith("|")), len(lines))
        rows = []
        for n in range(head + 2, end):
            c = [cell(x) for x in lines[n].strip().strip("|").split("|")]
            if len(c) <= max(di, pi):
                continue
            rows.append((n + 1, c[0], c[di], c[pi]))
        cid = page_circuit.get(os.path.realpath(page)) or ids.get(os.path.dirname(page))
        out.append((cid, os.path.relpath(page, ROOT), rows))
    return out, set(v for v in ids.values() if v)


def main():
    pages, circuit_ids = tables()
    master = (yaml.safe_load(open(os.path.join(ROOT, "hardware/nets.yaml"),
                                  encoding="utf-8")) or {}).get("nets") or {}
    problems, unresolved = [], []

    # role of each circuit on each master net
    role = {}
    for net, spec in master.items():
        for circ in [spec.get("driver")] if spec.get("driver") else []:
            role.setdefault(net, {})[circ] = "out"
        for circ in (spec.get("receivers") or []):
            role.setdefault(net, {})[circ] = "in"
        for circ in [spec.get("origin")] if spec.get("origin") else []:
            role.setdefault(net, {})[circ] = "ref"
        for circ in (spec.get("reference") or []):
            role.setdefault(net, {})[circ] = "ref"
        for circ in (spec.get("proposed") or []):
            role.setdefault(net, {})[circ] = "proposed"

    named = {}          # circuit -> {peer: (page, line)}, direction-bearing rows
    peer_of = {}        # circuit -> {peer}, every row
    for cid, page, rows in pages:
        for line, node, d, peer in rows:
            if d not in DIR_OK:
                problems.append(f"{page}:{line}: Dir {d!r} is not one of "
                                f"in / out / in/out / ref / —")
            # A Peer cell may hold a PATH through the design, not just a list:
            # `HDR-DEV IO35 -> module/digital-and-supervision` names one
            # non-circuit and one circuit. Split on the arrows as well as the
            # commas, and take the last whitespace-separated token of each part,
            # because a cell says which pin it leaves by.
            # EVERY TOKEN, not the last one. A cell reads
            # "carrier/mcu through HDR-DEV" - one circuit and one socket - and
            # taking the last token found the socket and reported the circuit
            # as unnamed, which is the answer the cell was edited to give.
            parts = re.split(r"[,\u2192\u2194]", peer)
            toks = [t for part in parts for t in part.split()]
            for p in toks:
                if not p or p in ("—", "-"):
                    continue
                if p in circuit_ids:
                    # EVERY Peer earns a circuit: edge, whatever the Dir -
                    # hardware/README.md's rule is about the Peer column, and a
                    # `—` row still names a peer. Only SYMMETRY is restricted to
                    # rows that declare a direction, because a context row is
                    # not a claim about a connection.
                    peer_of.setdefault(cid, set()).add(p)
                    if cid and d not in ("—", "-", ""):
                        named.setdefault(cid, {})[p] = (page, line)
                elif p not in NON_CIRCUIT and "/" in p:
                    problems.append(f"{page}:{line}: Peer {p!r} looks like a "
                                    f"circuit id and is not one")
            # Dir against the master, where the node resolves
            key = node.replace(" ", "_").upper()
            hit = next((n for n in master if n == node or n == key), None)
            if hit is None:
                unresolved.append(f"{page}:{line} {node!r}")
                continue
            if not cid:
                continue
            want = role.get(hit, {}).get(cid)
            if want is None:
                if d not in ("—", "-", ""):
                    problems.append(f"{page}:{line}: names {hit} as {d!r}, and "
                                    f"nets.yaml does not name {cid} on that net")
            elif want == "proposed":
                pass
            elif d in ("—", "-", ""):
                problems.append(f"{page}:{line}: names {hit} with Dir '—', "
                                f"meaning no connection - but nets.yaml has "
                                f"{cid} as {want} on it")
            elif d != want and not (d == "in/out" and want in ("in", "out")):
                problems.append(f"{page}:{line}: {hit} Dir is {d!r} and "
                                f"nets.yaml makes {cid} its {want!r}")

    # symmetry, both ways
    # SYMMETRY IS ABOUT BEING NAMED, NOT ABOUT AGREEING ON A DIRECTION. If A
    # says `out` to B and B's row is `-` ("the net is that circuit's"), the
    # relationship is still declared from both ends - that is exactly what a
    # context row is for, and panel.md is built out of them. What is a defect is
    # B not naming A at all.
    for a, peers in named.items():
        for b, (page, line) in peers.items():
            if a not in peer_of.get(b, set()):
                problems.append(f"{page}:{line}: {a} names {b} as a Peer and "
                                f"{b}'s table does not name {a} back")

    # circuit.yaml edges against the Peer column
    for f in glob.glob(os.path.join(ROOT, "hardware/**/circuit.yaml"), recursive=True):
        spec = yaml.safe_load(open(f, encoding="utf-8")) or {}
        cid = spec.get("id")
        edges = {e.split(":", 1)[1] for e in (spec.get("depends_on") or [])
                 if e.startswith("circuit:")}
        peers = set(peer_of.get(cid, set()))
        rel = os.path.relpath(f, ROOT)
        for missing in sorted(peers - edges):
            problems.append(f"{rel}: the table names {missing} as a Peer and "
                            f"there is no circuit:{missing} edge")
        for extra in sorted(edges - peers):
            problems.append(f"{rel}: declares circuit:{extra} and the table's "
                            f"Peer column does not name it")

    for p in problems:
        print("  " + p)
    print(f"interfaces: {len(pages)} table(s), "
          f"{sum(len(r) for _, _, r in pages)} row(s), {len(master)} master net(s) "
          f"| {len(problems)} problem(s) | {len(unresolved)} row(s) whose Node "
          f"does not resolve to a master net")
    if unresolved and VERBOSE:
        for u in unresolved:
            print(f"    unresolved: {u}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
