"""item2vec recommendations: learned item embeddings.

Trained by train_item2vec.py. recommend() averages the last-3 item vectors and
returns the most cosine-similar items -- the same math as the batched path in
run_bakeoff.py, just one session at a time (fine for the demo; the bake-off
batches for speed).
"""
import numpy as np
from gensim.models import Word2Vec

from models import recommend_popularity

_model = None


def load_model(path="data/sample/item2vec.model"):
    global _model
    if _model is None:
        _model = Word2Vec.load(path)
        print(f"item2vec loaded: {len(_model.wv):,} items, dim={_model.wv.vector_size}")
    return _model


def recommend_item2vec(session_aids, k=20):
    """Average the last-3 item vectors -> most cosine-similar unseen items.

    Falls back to popularity when none of the recent aids have vectors
    (items rarer than min_count never got embeddings).
    """
    wv = load_model().wv
    vecs = [wv[str(a)] for a in session_aids[-3:] if str(a) in wv]
    if not vecs:
        return recommend_popularity(session_aids, k)
    avg = np.mean(vecs, axis=0)
    seen = {str(a) for a in session_aids}
    sims = wv.most_similar(positive=[avg], topn=k * 5)
    return [int(a) for a, _ in sims if a not in seen][:k]
