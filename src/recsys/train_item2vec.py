"""Train item2vec: skip-gram Word2Vec over train sessions.

Each session = a "sentence", each aid = a "word" (stored as string, since
gensim keys are strings). Items appearing in similar session contexts get
similar vectors -- behavioral similarity with zero product metadata.
Saves to data/sample/item2vec.model (gitignored: large, reproducible).
"""
import time
from gensim.models import Word2Vec
from evaluate import load_sessions, time_split

print("loading sessions...")
sessions = load_sessions()
train, _ = time_split(sessions)
sentences = [[str(a) for a in aids] for _, aids, _, _ in train]
print(f"training on {len(sentences):,} sessions...")

t0 = time.time()
model = Word2Vec(
    sentences,
    vector_size=64,   # small: trains in minutes, cheap to store; bigger dims
                      # only help with far more data per item (most items are rare)
    window=5,         # items within 5 positions shape each other; wider would
                      # blur distinct shopping intents in these long sessions
    min_count=5,      # items seen <5 times get no vector: their embeddings
                      # would be noise, and this keeps vocab/RAM manageable
    sg=1,             # skip-gram over CBOW: learns better vectors for RARE items,
                      # and the long tail is most of this catalog
    workers=4,
    epochs=5,
    seed=42,          # reproducibility
)
dt = time.time() - t0
print(f"trained in {dt:.0f}s | vocab: {len(model.wv):,} items")
model.save("data/sample/item2vec.model")
print("saved to data/sample/item2vec.model")
