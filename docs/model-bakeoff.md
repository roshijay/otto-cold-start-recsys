# Model bake-off — session recommenders

## Protocol (`src/recsys/evaluate.py`)
- **Time-based split:** 160,000 train / 40,000 test sessions, split at 2022-08-01 05:55:17.
  Train ends 15ms before test starts -- no overlap, no leakage.
- **Task:** for each test session, input = all events except the last; target = the last event's aid.
- **Metrics:** Recall@20 ("was the true next item in our top 20?") and MRR@20 (same, rewarding
  higher ranks), reported per target event type (clicks / carts / orders) plus a business-weighted blend.
- **Contract:** every model implements `recommend(session_aids, k)` returning aids not already in the
  session, so all three compete on identical terms.

## Results

| model | clicks n | clicks R@20 | clicks MRR@20 | carts R@20 | carts MRR@20 | orders R@20 | weighted R@20 | weighted MRR@20 |
|---|---|---|---|---|---|---|---|---|
| popularity | 36,753 | 0.0044 | 0.0008 | 0.0007 | 0.0001 | 0.0000 | 0.0021 | 0.0004 |
| co-visitation | 36,753 | 0.0647 | 0.0219 | 0.0235 | 0.0101 | 0.0006 | 0.0328 | 0.0113 |
| item2vec | 36,753 | 0.0257 | 0.0079 | 0.0104 | 0.0040 | 0.0006 | 0.0133 | 0.0041 |

(Carts n=1,532; orders n=1,715. Orders R@20 of 0.0006 = exactly 1 hit in 1,715.)

## Interpretation
- **Co-visitation wins everywhere** -- ~2.5x item2vec and ~15x popularity on weighted recall@20.
  Session context beats no context (popularity) and beats compressed context (embeddings).
- **Popularity is near-zero, as Phase 3 predicted.** The extreme long tail (top item = 0.15% of orders)
  means the global top-20 almost never contains any given session's next item. The Q4 hypothesis survived.
- **Why item2vec lost -- the leading hypothesis:** skip-gram assumes items close in the sequence share
  intent, like words in a sentence. But Q5 showed OTTO sessions are days-long visitor histories, so
  consecutive events can be days apart and unrelated -- that dilutes the window the embeddings learn from.
  Co-visitation counts session-level co-occurrence regardless of distance, so it is immune to this.
  Contributing factors: hyperparameters (dim=64, window=5, epochs=5) were starting guesses, never tuned;
  and averaging 3 query vectors collapses distinct intents into one centroid, while co-visitation keeps
  each query item's evidence separate.
- **Orders are unpredictable for all three models** (~1/1715 each; popularity 0/1715). Predicting the exact
  next purchase out of 283k candidates is beyond next-item retrieval at this granularity -- a real system
  would reframe the task (predict *whether* they order, or rank within a candidate set) rather than tune harder.

## Weight choices (business reasoning, not math)
- Event-type weights 1/5/20 (click/cart/order) encode business value: an order is worth ~20 clicks.
  Same judgment as the popularity baseline weights -- documented, not tuned on the test set.
- The weighted blend exists because a model could win on clicks while being useless for revenue;
  the blend keeps the scoreboard honest about what the business cares about.

## What I would try next (with another week)
1. Tune item2vec: dim, window, epochs, and skip-gram vs CBOW -- the current settings were never searched.
2. Recency-weighted query vector: Q5 says sessions span days, so weight recent aids over ancient ones
   instead of a flat last-3 average.
3. Restrict embedding training contexts to same-day event pairs, matching the intent-window reality.
4. Hybrid: co-visitation candidates re-ranked by embedding similarity -- combine the winner's recall
   with the embeddings' generalization to unseen pairs.
5. Reframe the orders task (propensity to order / candidate-set ranking) instead of exact next-order retrieval.

## Reproducibility
- `python src/recsys/train_item2vec.py` -- trains embeddings (54s, vocab 282,719 @ min_count=5)
- `python src/recsys/run_bakeoff.py` -- rebuilds co-visitation, scores all three (~4 min)
- Model file `data/sample/item2vec.model` is gitignored (reproducible, ~100MB); everything else is in git.
