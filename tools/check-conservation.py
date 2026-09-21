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

print(f"source {src}@{rev}: {len(was)} words")
print(f"destinations: {len(now)} words across {len(dests)} file(s)")
seams=[l for l in lost if l[1]<N]   # a seam loses at most N-1 shingles
real=[l for l in lost if l[1]>=N]
print(f"seams (new text inserted between preserved passages): {len(seams)}")
print(f"REAL GAPS (source text with no home): {len(real)}")
for pos,gap,text in real:
    print(f"  gap {gap} words @ {pos}: {text[:220]}")
