#!/usr/bin/env python3
"""
Rebuild hardware/bom.csv from the per-circuit fragments.

Same relationship as .manifest-R*.csv -> MANIFEST.csv: the fragments are the
source, the root file is GENERATED, and a direct edit to the generated file
survives until the next run of this tool and then disappears without a word.
That trap is documented in repo-maintenance.md 3 because it has already
happened once with the manifest. bom.csv is the most-cited file in the
repository - 37 backtick references - so it is the worst possible place to
repeat it. Hence --check, wired into check-staleness.py.

THE ASSIGNMENT RULE, from D4:

    A row lives in the fragment for the circuit WHOSE PAGE DERIVES ITS VALUE.
    Not where it is mentioned, not where it is mounted - where the number
    comes from.

"Where it is mounted" fails on PLATE-TOP, a mechanical part whose dimensions
cluster-boards.md derives. "Where it is mentioned" fails on R-BIAS-INAMP,
named once in the whole corpus - on the PITCH page, as a contrast.

ORDERING is a hand-written list, not a glob and not a sort. Adding a circuit
is then a visible one-line diff in this file rather than a silent re-sort of
138 rows, and a fragment on disk but missing from ORDER is an error rather
than a silent omission.

Usage:  python3 tools/merge-bom.py [--check]
        --check  regenerate into memory and byte-compare; do not write
Exit:   0 clean, 1 problems
"""
import csv, glob, io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "hardware/bom.csv")
HDR = ["ref", "category", "part", "manufacturer", "description", "package",
       "qty", "status", "source", "adr", "notes"]

# The emission order. Hand-written on purpose - see the module docstring.
# Shared fragments last, so a reader scanning the generated file meets the
# circuits in board order before the cross-cutting rows.
# Circuits that own no BOM rows, and why. A circuit is in here because
# someone decided it owns nothing - never because a file happened to be
# missing. See the refusal in load().
NO_PARTS = {
    "hardware/module/link-supervision/bom.csv":
        "the watchdog and presence detect are NOT FITTED - the page exists "
        "to record what was deleted and what restoring it would cost",
}

ORDER = [
    "hardware/carrier/power-entry-instrument/bom.csv",
    "hardware/carrier/breath-excitation-reference/bom.csv",
    "hardware/carrier/breath-adc/bom.csv",
    "hardware/carrier/led-strip-drive/bom.csv",
    "hardware/carrier/display-and-service-uart/bom.csv",
    "hardware/carrier/bom.csv",
    "hardware/cluster/key-register/bom.csv",
    "hardware/cluster/key-switch-network/bom.csv",
    "hardware/cluster/key-marker-and-bits/bom.csv",
    "hardware/cluster/bom.csv",
    "hardware/interfaces/breath-sense-link/bom.csv",
    "hardware/interfaces/spi-link/bom.csv",
    "hardware/interfaces/key-chain-loom/bom.csv",
    "hardware/module/power-entry/bom.csv",
    "hardware/module/umbilical-load-switch/bom.csv",
    "hardware/module/panel-led/bom.csv",
    "hardware/module/dac8568/bom.csv",
    "hardware/module/digital-and-supervision/bom.csv",
    "hardware/module/link-supervision/bom.csv",
    "hardware/module/breath-receive-stage/bom.csv",
    "hardware/module/breath-output-stage/bom.csv",
    "hardware/module/breath-response-shaper/bom.csv",
    "hardware/module/pitch-stage/bom.csv",
    "hardware/module/mod-channels/bom.csv",
    "hardware/module/panel/bom.csv",
    "hardware/module/bom.csv",
    "hardware/unplaced.csv",
]


def load():
    """Read every fragment in ORDER. Returns (rows, problems)."""
    rows, seen, problems = [], {}, []

    on_disk = set(os.path.relpath(p, ROOT) for p in
                  glob.glob(os.path.join(ROOT, "hardware", "**", "bom.csv"),
                            recursive=True))
    on_disk.discard("hardware/bom.csv")
    if os.path.exists(os.path.join(ROOT, "hardware/unplaced.csv")):
        on_disk.add("hardware/unplaced.csv")

    # A fragment on disk that ORDER does not name would be silently dropped
    # from the master - the exact failure mode this tool exists to prevent.
    for extra in sorted(on_disk - set(ORDER)):
        problems.append(f"{extra} exists but is not in ORDER in "
                        f"tools/merge-bom.py - it would be silently dropped")

    for rel in ORDER:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            # A FRAGMENT NAMED IN ORDER BUT ABSENT USED TO BE SKIPPED IN
            # SILENCE, and the master was then regenerated a few rows
            # shorter with everything green - merge-manifests.py refuses the
            # analogous case and this did not. "Not every circuit owns parts"
            # is a real situation, so it has to be SAID rather than inferred
            # from a missing file.
            if rel in NO_PARTS:
                continue
            problems.append(f"{rel} is in ORDER but is not on disk. If that "
                            f"circuit genuinely owns no parts, say so in "
                            f"NO_PARTS in tools/merge-bom.py; otherwise the "
                            f"master is about to lose its rows silently")
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            rdr = list(csv.reader(fh))
        if not rdr:
            problems.append(f"{rel}: empty")
            continue
        if [c.strip() for c in rdr[0]] != HDR:
            problems.append(f"{rel}: header is {rdr[0]}, expected {HDR}")
            continue
        for i, r in enumerate(rdr[1:], 2):
            if not any(r):
                continue
            if len(r) != len(HDR):
                problems.append(f"{rel}:{i} has {len(r)} columns, "
                                f"expected {len(HDR)}")
                continue
            # A row belongs to exactly one circuit. This is the old
            # duplicate-refdes check moved one level up, and it now catches a
            # stronger error: not "the same refdes twice in one file" but
            # "two circuits both claim it", with both locations named.
            if r[0] in seen:
                problems.append(f"{rel}:{i} refdes {r[0]!r} is already owned "
                                f"by {seen[r[0]]} - a row belongs to exactly "
                                f"one circuit")
                continue
            seen[r[0]] = f"{rel}:{i}"
            rows.append(r)
    return rows, problems


def render(rows):
    """CRLF, always. repo-maintenance.md 4: setting lineterminator to \\n
    rewrites every line in the file and buries a three-row change in a
    130-row diff."""
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\r\n")
    w.writerow(HDR)
    w.writerows(rows)
    return out.getvalue()


def main():
    rows, problems = load()
    text = render(rows)
    check = "--check" in sys.argv

    if check:
        try:
            current = open(MASTER, encoding="utf-8", newline="").read()
        except Exception as e:
            problems.append(f"cannot read {MASTER}: {e}")
            current = None
        if current is not None and current != text:
            a, b = current.split("\r\n"), text.split("\r\n")
            n = next((i for i in range(max(len(a), len(b)))
                      if (a[i:i+1] or [None]) != (b[i:i+1] or [None])), 0)
            problems.append(
                f"hardware/bom.csv does not match its fragments, first "
                f"difference at line {n+1}. It is GENERATED - edit the "
                f"fragment, not the master, then re-run this tool")
    else:
        with open(MASTER, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)

    for p in problems:
        print("  " + p)
    verb = "checked" if check else "wrote"
    print(f"bom.csv: {verb} {len(rows)} rows from "
          f"{sum(1 for r in ORDER if os.path.exists(os.path.join(ROOT, r)))} "
          f"fragments | {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
