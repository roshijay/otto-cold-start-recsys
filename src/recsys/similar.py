"""Item-embedding similarity search -- "behavioral" semantic search.

Each item2vec vector positions an item so that items appearing in similar
session contexts land near each other. Cosine similarity between vectors is
therefore BEHAVIORAL similarity: no product text is involved; the "semantics"
are learned from browsing journeys (Phase 4).

This is also the cold-start fallback from the spec: a session with zero history
can't use the session recommender, but a user picking/typing an item can still
get "similar items" -- query-based, not history-based.
"""
import numpy as np

from item2vec_recs import load_model


def similar_items(aid, k=10):
    """Top-K most cosine-similar aids to `aid`, excluding itself.

    Exact nearest-neighbor scan over the vocab (a few ms -- fine for interactive
    use; the demo will do numpy cosine on the exported parquet instead).
    Returns [] for items with no vector (rarer than min_count): honest empty,
    not a guess.
    """
    wv = load_model().wv
    key = str(aid)
    if key not in wv:
        return []
    sims = wv.most_similar(key, topn=k + 1)  # [0] is the query itself (sim 1.0)
    return [int(a) for a, _ in sims if a != key][:k]


def export_item_vectors(top_n=20000, path="app/assets/item_vectors.parquet"):
    """Export top-N items by clicks with their vectors: small, deployable artifact.

    Why top 20k by clicks? The demo's similarity search is a head-item feature;
    rare items' vectors are noisy anyway (see check_similarity.py). 20k x 64
    float32 ~= 5MB -- loads instantly on a 1GB free host. One row per aid with
    v0..v63 columns: the demo does numpy cosine directly on this frame.
    Regenerable: re-run this after retraining and the demo updates.
    """
    import os
    import duckdb
    import pandas as pd

    wv = load_model().wv
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    aids = [r[0] for r in con.execute(
        f"select aid from main_marts.fct_item_stats order by n_clicks desc limit {top_n}"
    ).fetchall()]
    con.close()
    have = [a for a in aids if str(a) in wv]
    print(f"top-{top_n} by clicks: {len(have):,} have vectors "
          f"({top_n - len(have):,} too rare, skipped)")
    mat = np.array([wv[str(a)] for a in have], dtype=np.float32)
    df = pd.DataFrame(mat, columns=[f"v{i}" for i in range(mat.shape[1])])
    df.insert(0, "aid", have)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"exported {len(df):,} items x {mat.shape[1]} dims -> {path} "
          f"({os.path.getsize(path) / 1e6:.1f} MB)")


if __name__ == "__main__":
    export_item_vectors()
