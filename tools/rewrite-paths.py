#!/usr/bin/env python3
"""
Path rewriter for the 2026-09-21 restructure, and its own proof of correctness.

A restructure is this project's named failure mode with every path in the
repository as the value. So this tool does three things, and the third is the
one that matters:

    --apply    rewrite old->new path tokens across the corpus, from the MAP
    --verify   assert no old-side token survives outside history
    --invert   THE PROOF. For every changed file, apply the INVERSE rewrite and
               require the result byte-identical to that file at the baseline
               revision. If A2 changed anything other than a path token from
               the MAP, this fails and names the file.

--invert is what makes "Phase A changed no content" a decidable proposition
rather than a promise. A numeric-token diff is the weak form: it cannot see a
permutation, a non-numeric fact, or an edit inside a path. Byte identity under
inversion can.

HISTORY IS NEVER REWRITTEN. docs/review/, docs/log/ and docs/research/ point at
the old paths on purpose - a path is a value, and rewriting it makes a review
say what its author did not (CLAUDE.md 6). They resolve through the MAP.

Usage:
    python3 tools/rewrite-paths.py --apply
    python3 tools/rewrite-paths.py --verify
    python3 tools/rewrite-paths.py --invert --baseline <rev>
"""
import csv, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, "docs/reference/path-map-2026-09-21.csv")

# Never rewritten, and never checked for survivors. These are dated records.
#
# docs/review|log|research are history by CLAUDE.md 6. The datasheet manifest
# fragments are the same kind of thing for the same reason: they are
# append-only and per-author, and repo-maintenance.md 1 forbids editing
# another wave's fragment because a row is the honest record of what that
# researcher found WHEN THEY FOUND IT. A note in a 2026-09-21 fragment naming
# hardware/controller/carrier.md is correct as a record of where that page was.
# MANIFEST.csv is GENERATED from those fragments, so rewriting it would be
# destroyed on the next merge anyway - the two must be excluded together or
# the tool reports a survivor it can never clear.
HISTORY = ("docs/review/", "docs/log/", "docs/research/",
           "datasheets/.manifest-R", "datasheets/MANIFEST.csv")

# Rewritten by hand, not from the MAP, because each needs judgement about what
# the path MEANS rather than what it says. Excluded from --invert by name and
# reviewed by hand instead; see D5 5.3.
HAND_EDITED = (
    "tools/check-staleness.py",
    "tools/verify-datasheets.py",
    "tools/merge-manifests.py",
    "tools/rewrite-paths.py",
    "CLAUDE.md",
    "README.md",
    ".claude/settings.json",
    ".gitignore",
    "docs/reference/path-map-2026-09-21.csv",
    "docs/reference/repo-maintenance.md",
    # RELATIVE LINKS ARE RECOMPUTED, NOT SUBSTITUTED, so these two cannot be
    # proven by inversion and are hand-checked instead. Both carried a link
    # written as a bare filename - `](breath-receive-stage.md)` - which
    # resolved while the module pages were siblings and stopped resolving when
    # each got its own directory. The correct new text depends on where the
    # LINKING file now sits, which a search-and-replace cannot know.
    # Named here rather than quietly folded into the map, because the point of
    # the inversion check is that its exclusion list is short and reviewed.
    "hardware/module/mod-channels/mod-channels.md",
    "hardware/module/pitch-stage/pitch-stage.md",
)

TEXT_EXT = (".md", ".csv", ".yaml", ".yml", ".py", ".json", ".txt")


def load_map():
    """old -> new, for rows that actually moved."""
    pairs = {}
    with open(MAP, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            old, new = r["old"].strip(), r["new"].strip()
            if not old or not new or old == new:
                continue
            if r["kind"].strip() in ("unmoved", "unmoved-history"):
                continue
            pairs[old] = new
    # Longest first. "hardware/module/power-entry.md" must be tried before any
    # shorter prefix of it, or a rewrite lands inside an already-rewritten
    # token and produces a path that resolves to nothing.
    return dict(sorted(pairs.items(), key=lambda kv: -len(kv[0])))


def tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout.split("\n")
    return [f for f in out if f and f.endswith(TEXT_EXT)]


def rewritable(rel):
    return not rel.startswith(HISTORY) and rel not in HAND_EDITED


def rewrite(text, pairs):
    for old, new in pairs.items():
        text = text.replace(old, new)
    return text


def unrewrite(text, pairs):
    """The inverse. Applied shortest-first, the mirror of rewrite's order."""
    for old, new in reversed(list(pairs.items())):
        text = text.replace(new, old)
    return text


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8", newline="") as fh:
        return fh.read()


def write(rel, text):
    with open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def cmd_apply(pairs):
    changed = 0
    for rel in tracked_files():
        if not rewritable(rel):
            continue
        before = read(rel)
        after = rewrite(before, pairs)
        if after != before:
            write(rel, after)
            changed += 1
            print(f"  rewrote {rel}")
    print(f"apply: {changed} file(s) rewritten from {len(pairs)} mapped moves")
    return 0


def cmd_verify(pairs):
    """No old-side token may survive outside history and the hand-edited set."""
    survivors = []
    for rel in tracked_files():
        if not rewritable(rel):
            continue
        text = read(rel)
        for old in pairs:
            at = text.find(old)
            if at >= 0:
                line = text[:at].count("\n") + 1
                survivors.append(f"{rel}:{line} still says {old!r}")
    for s in survivors:
        print("  " + s)
    print(f"verify: {len(survivors)} surviving old-side token(s)")
    return 1 if survivors else 0


def invert_targets(pairs):
    """Every file A2 could have touched, paired with its baseline path.

    NOT just the moved ones. A2 rewrote seven files that did not move at all
    (config/figures.yaml, hardware/bom.csv, five ADRs), and an inversion check
    that skipped them would have proved nothing about the files where most of
    the rewriting actually happened. Found by running the check and noticing
    it reported a suspiciously small number.
    """
    targets = dict(pairs)                       # moved: baseline old -> new
    for rel in tracked_files():                 # unmoved: same path both ends
        if rewritable(rel) and rel not in targets.values():
            targets[rel] = rel
    return targets


def cmd_invert(pairs, baseline):
    """THE PROOF. invert(HEAD:new) must equal baseline:old, byte for byte."""
    bad, checked, skipped = [], 0, 0
    for old, new in invert_targets(pairs).items():
        try:
            was = subprocess.run(["git", "show", f"{baseline}:{old}"], cwd=ROOT,
                                 capture_output=True, check=True).stdout
        except subprocess.CalledProcessError:
            bad.append(f"{old}: not present at baseline {baseline}")
            continue
        p = os.path.join(ROOT, new)
        if not os.path.exists(p):
            bad.append(f"{new}: mapped destination does not exist")
            continue
        with open(p, "rb") as fh:
            now = fh.read()
        if new in HAND_EDITED or new.startswith(HISTORY):
            skipped += 1
            continue
        try:
            restored = unrewrite(now.decode("utf-8"), pairs).encode("utf-8")
        except UnicodeDecodeError:
            restored = now
        checked += 1
        if restored != was:
            # Name the first differing line rather than dumping the file.
            a, b = was.decode("utf-8", "replace").split("\n"), \
                   restored.decode("utf-8", "replace").split("\n")
            n = next((i for i in range(max(len(a), len(b)))
                      if (a[i:i + 1] or [None]) != (b[i:i + 1] or [None])), 0)
            bad.append(f"{new}: inverse differs from {baseline}:{old} at line "
                       f"{n + 1}\n      was: {(a[n:n+1] or [''])[0][:110]!r}\n"
                       f"      now: {(b[n:n+1] or [''])[0][:110]!r}")

    for b in bad:
        print("  " + b)
    print(f"invert: {checked} file(s) byte-identical under inversion, "
          f"{skipped} hand-edited/skipped, {len(bad)} MISMATCH")
    return 1 if bad else 0


def main():
    if not os.path.exists(MAP):
        sys.exit(f"no MAP at {os.path.relpath(MAP, ROOT)} - Phase A writes it "
                 f"before anything moves")
    pairs = load_map()
    if "--apply" in sys.argv:
        return cmd_apply(pairs)
    if "--verify" in sys.argv:
        return cmd_verify(pairs)
    if "--invert" in sys.argv:
        i = sys.argv.index("--baseline") + 1 if "--baseline" in sys.argv else 0
        if not i:
            sys.exit("--invert needs --baseline <rev>")
        return cmd_invert(pairs, sys.argv[i])
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
