# The 32 bits — decision history

**Past tense only.** Every live value lives in `key-marker-and-bits.md`,
`config/key-layout.yaml` or `hardware/bom.csv`. If a number here is still true,
it is in the wrong file.

This is the circuit's superseded shelf, on the convention
[`../../module/pitch-stage/notes.md`](../../module/pitch-stage/notes.md) sets.
Nothing is deleted from it: a deleted superseded value stops warning the next
person, and the refutation wording is what lets `tools/check-staleness.py` tell
a quoted old value from a live one.

---

## `left_thumb`'s marker pair was flipped, 2026-09-21

*Moved verbatim from the marker section of `cluster-boards.md`, 2026-09-21.
"this very page" was that page: the reorder it names is the chain-order item
still open in [`../cluster-boards.md`](../cluster-boards.md). The pattern it
left behind is the live one, in
[`key-marker-and-bits.md`](key-marker-and-bits.md).*

> **`left_thumb`'s pair was flipped on 2026-09-21, and the reason is worth
> keeping.** The original pattern was `1 0 · 0 1 · 1 0 · 0 1` — a **repeating
> nibble**, and the page's own test ("not a repeating *byte*") did not catch
> that. A falsification agent solved the marker exhaustively, as a symbolic
> constraint problem over all eight positions against every key state, and
> found that of the **23 wrong chain permutations exactly one passes
> undetected: `RT → RH → LH → LT`** — which is the reorder *this very page*
> proposes to save a body crossing. It passes whenever `LH5` is released, and
> the result is that the left-hand keys drive the octave keys, `LH5` reads
> permanently released, and the only symptom is the error counter ticking —
> so the diagnosis points at the wrong thing.
>
> Two proposals, made hours apart, each sound alone and jointly blind.
> Flipping this one pair kills all 23 permutations and a −5 shift hole while
> keeping all 24 hard faults caught. **Two straps.**
