#!/usr/bin/env python3
"""Content conservation for a Phase B split.

Every run of words in the SOURCE page at <rev> must survive somewhere in the
destination files. This is the check a restructure actually needs: its
characteristic loss is a paragraph that quietly does not make it, and no
value-based or path-based check can see that.

WORD STREAM, not lines. Moving a blockquote out of a blockquote legitimately
strips "> " prefixes and rewraps every line in it, so line-level matching
reports the whole block as lost. Comparing shingles of the word stream
survives rewrapping and still catches a dropped sentence.

Usage: conserve.py <rev> <source-path> <dest-path> [<dest-path> ...]
"""
import subprocess, sys, re

N = 8   # shingle length in words; long enough that prose collisions are rare


def words(text):
    text = re.sub(r"[`*~_#|>]", " ", text)      # markdown furniture
    text = re.sub(r"\s+", " ", text)
    return text.split()


rev, src, dests = sys.argv[1], sys.argv[2], sys.argv[3:]
was = words(subprocess.run(["git", "show", f"{rev}:{src}"], capture_output=True,
                           text=True, check=True).stdout)
now = []
for d in dests:
    now += words(open(d, encoding="utf-8").read())

have = set()
for i in range(len(now) - N + 1):
    have.add(" ".join(now[i:i + N]))

lost, i = [], 0
while i <= len(was) - N:
    sh = " ".join(was[i:i + N])
    if sh not in have:
        j = i
        while j <= len(was) - N and " ".join(was[j:j + N]) not in have:
            j += 1
        # j - i is the real gap. A seam - where new text was inserted between
        # two preserved passages - shows as a gap of ~1: every word survives,
        # only their adjacency does not. A dropped sentence shows as a gap of
        # its own length.
        lost.append((i, j - i, " ".join(was[i:min(j + N, len(was))])))
        i = j + 1
    else:
        i += 1

# BOTH ENDS HIDE BELOW N. In the interior a 1-word deletion breaks N
# shingles and is reported; at either END only k shingles exist to break, so
# deleting the last - or the FIRST - 1/3/5/7 words scores seams:1 REAL
# GAPS:0.
#
# The tail half of this was written first, and the symmetric sentence about
# the head was never written. A cold reviewer found it by deleting the first
# six words of a page - its entire H1 heading and status label - and getting
# rc=0, where the same six words off the end gave rc=1.
#
# That asymmetry mattered more than the hole it left, because DELETING WORDS
# OFF THE FRONT OF A PASSAGE IS WHAT A SPLIT DOES: an agent moves a section
# to a new page and rewrites its heading. The one check built to prove the
# splits conserved content was blind to the likeliest way a split loses it.
#
# So compare the first N and the final N words explicitly, rather than
# pretending the shingle walk covers either end.
tail_lost = ""
if len(was) >= N and " ".join(was[-N:]) not in have:
    tail_lost = " ".join(was[-N:])
head_lost = ""
if len(was) >= N and " ".join(was[:N]) not in have:
    head_lost = " ".join(was[:N])

# A PASSAGE STATED TWICE CAN BE HALVED FOR FREE, because `have` is a set: one
# surviving copy satisfies every lookup for both. The same reviewer deleted a
# 26-word grounding warning from one of the two sections carrying it and got
# REAL GAPS: 0. Compare MULTIPLICITY, not just presence.
from collections import Counter
src_counts = Counter(" ".join(was[i:i + N]) for i in range(len(was) - N + 1))
dst_counts = Counter(" ".join(now[i:i + N]) for i in range(len(now) - N + 1))
halved = [(sh, c, dst_counts.get(sh, 0)) for sh, c in src_counts.items()
          if c > 1 and dst_counts.get(sh, 0) < c]

print(f"source {src}@{rev}: {len(was)} words")
print(f"destinations: {len(now)} words across {len(dests)} file(s)")
seams=[l for l in lost if l[1]<N]   # a seam loses at most N-1 shingles
real=[l for l in lost if l[1]>=N]
print(f"seams (new text inserted between preserved passages): {len(seams)}")
print(f"REAL GAPS (source text with no home): {len(real)}")
for pos,gap,text in real:
    print(f"  gap {gap} words @ {pos}: {text[:220]}")
if head_lost:
    print(f"  HEAD: the source's first {N} words are not in any destination: "
          f"{head_lost[:200]}")
if tail_lost:
    print(f"  TAIL: the source's last {N} words are not in any destination: "
          f"{tail_lost[:200]}")
if halved:
    print(f"  REPEATED PASSAGES THINNED ({len(halved)}): the source states "
          f"these more times than the destinations do")
    for sh, c, d in halved[:10]:
        print(f"      {c}x -> {d}x: {sh[:160]}")

# Exit non-zero on a real gap. This printed its findings and exited 0 for its
# whole life, so any caller that trusted the exit code - a hook, a CI step, a
# `&&` chain - read a real gap as success. Same class as the three fail-open
# holes this restructure already found; it is only luck that every invocation
# so far was read by a human.
sys.exit(1 if (real or tail_lost or head_lost or halved) else 0)
