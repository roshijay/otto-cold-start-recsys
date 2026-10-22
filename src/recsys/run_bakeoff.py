"""Bake-off: score all three recommenders on the shared test set.

Popularity and co-visitation score per-session (fast). item2vec uses a batched
numpy path: 40k individual most_similar calls would each scan the whole 283k-item
vocab (~an hour total); chunked matrix multiplies do the same cosine math in
about a minute. Same recommendations, different speed.
"""
import json
import time
import numpy as np
from evaluate import load_sessions, time_split, evaluate, score_all, K
from models import recommend_popularity, recommend_covisit, build_covisit
from item2vec_recs import load_model

t0 = time.time()
sessions = load_sessions()
train, test = time_split(sessions)
print(f"train: {len(train):,} | test: {len(test):,}", flush=True)

build_covisit(train)

results = {}
results["popularity"] = evaluate(recommend_popularity, test)
print("popularity done", flush=True)
results["covisit"] = evaluate(recommend_covisit, test)
print("covisit done", flush=True)

# --- batched item2vec: identical cosine math to recommend_item2vec, vectorized ---
wv = load_model().wv
item_ids = wv.index_to_key                      # string aids, vocab order
M = wv.vectors / np.linalg.norm(wv.vectors, axis=1, keepdims=True)  # unit rows
inputs = [aids[:-1] for _, aids, _, _ in test]   # same inputs as the harness


def batch_item2vec(batch_size=250):
    all_recs = []
    n_batches = (len(inputs) + batch_size - 1) // batch_size
    for b in range(n_batches):
        chunk = inputs[b * batch_size:(b + 1) * batch_size]
        Q, missing = [], set()
        for i, aids in enumerate(chunk):
            vecs = [wv[str(a)] for a in aids[-3:] if str(a) in wv]
            if not vecs:                        # no vectors -> popularity fallback
                missing.add(i)
                Q.append(np.zeros(wv.vector_size))
            else:
                q = np.mean(vecs, axis=0)
                nrm = np.linalg.norm(q)
                Q.append(q / nrm if nrm else q)  # unit query: dot = cosine
        sims = np.asarray(Q) @ M.T               # (batch, vocab) cosine sims
        for i, aids in enumerate(chunk):
            if i in missing:
                all_recs.append(recommend_popularity(aids, K))
                continue
            sim = sims[i]
            cand = np.argpartition(-sim, K * 4)[:K * 4]   # top-80, unsorted
            cand = cand[np.argsort(-sim[cand])]           # ...now sorted
            seen = set(aids)
            all_recs.append([int(item_ids[j]) for j in cand
                             if int(item_ids[j]) not in seen][:K])
        print(f"  item2vec batch {b + 1}/{n_batches}", flush=True)
    return all_recs


results["item2vec"] = score_all(test, batch_item2vec())
print(json.dumps(results, indent=1))
print(f"total: {time.time() - t0:.0f}s")
