# Similarity search — behavioral "semantic" search

## How it is built (`src/recsys/similar.py`)
- `similar_items(aid, k=10)`: cosine similarity of the item's item2vec vector against the
  full vocab, top-K excluding itself. Exact nearest-neighbor scan (milliseconds per query).
- The vectors encode *session context*: items browsed in similar journeys land near each other.
  "Similar" therefore means **behaviorally similar** -- no product text exists in this dataset,
  so the semantics are learned from journeys, not descriptions.
- Cold-start role: a zero-history session can't use the session recommender, but a user
  picking/typing an item can still get "similar items" -- query-based, not history-based.
- Deployable artifact: `app/assets/item_vectors.parquet` -- top 20,000 items by clicks with
  their 64-dim vectors (19,997 have vectors; 3 were too rare in train, skipped honestly),
  7.7 MB. One row per aid, v0..v63 columns; the demo does numpy cosine on this frame.
  Regenerable via `python src/recsys/similar.py`.

## Sanity checks (`src/recsys/check_similarity.py`) -- behavior, not vibes
Aids are anonymous, so neighbors are verified by behavior:
1. **co-occurrence overlap**: fraction of the top-10 that co-occur with the query aid in train sessions;
2. **order-rate similarity**: do neighbors convert (orders / all events) like the query?

**HEAD aid (29735 -- the most-clicked item from the Phase 3 analysis):**
- neighbors: 329725, 832192, 575616, 618429, 1745380, 881836, 651801, 788882, 937559, 1047297
- co-occurrence overlap: **9/10**
- query order rate 0.0146; neighbor order rates: 8 of 10 in 0.012-0.024, two at 0.0000.
- Verdict: the embedding neighborhood is behaviorally coherent -- same sessions, same
  conversion band.

**RARE aid (aid=4, 10-30 lifetime events):**
- co-occurrence overlap: **0/10**; neighbor order rates mostly 0.0000 (one at 0.0769).
- Verdict: noisy, as expected. Few observations -> noisy vectors. This is the
  *cold-start within cold-start* problem: similarity search degrades exactly where a
  cold-start fallback would be most wanted.

## Honest framing
- Behavioral similarity, not textual: neighbors are "items browsed by similar journeys,"
  which may or may not match human notions of substitutability.
- Quality degrades for rare items -- which is why the exported artifact (and the demo)
  covers head items only.
- `similar_items` returns [] for items with no vector rather than guessing.
