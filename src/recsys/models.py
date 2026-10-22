"""Baseline recommenders: weighted popularity + co-visitation.

Both implement recommend(session_aids, k) -> aids not in the input session,
so the harness in evaluate.py scores them identically.
"""
import duckdb
from collections import Counter, defaultdict

# Business weights: an order is worth ~20 clicks. Documented judgment, not tuned.
# (Phase 3 Q4: clicks-popularity and orders-popularity disagree, so a
# clicks-only ranking would push items people browse but never buy.)
W_CLICK, W_CART, W_ORDER = 1, 5, 20

_popularity = None


def _load_popularity():
    """Global item ranking by weighted event counts, read from the mart.

    Why from fct_item_stats instead of recomputing? The mart is the tested,
    documented source of truth -- recomputing in Python would duplicate logic
    and could silently drift. Marts feeding models is how production teams work.
    """
    global _popularity
    if _popularity is None:
        con = duckdb.connect("data/warehouse.duckdb", read_only=True)
        rows = con.execute(
            "select aid, n_clicks, n_carts, n_orders from main_marts.fct_item_stats"
        ).fetchall()
        con.close()
        rows.sort(key=lambda r: -(W_CLICK * r[1] + W_CART * r[2] + W_ORDER * r[3]))
        _popularity = [r[0] for r in rows]
    return _popularity


def recommend_popularity(session_aids, k=20):
    """Top-K by global weighted popularity, excluding seen items."""
    seen = set(session_aids)
    # Candidate pool capped at top-2000: scanning the full 650k-item ranking
    # per session would cost 40k x 650k checks in the bake-off. No real session
    # has 1980+ of the very top items already seen, so the cap never changes
    # the output -- it just skips pointless scanning.
    return [a for a in _load_popularity()[:2000] if a not in seen][:k]


_cooccur = None


def build_covisit(train_sessions, max_aids=40):
    """Count how often item pairs co-occur in the same train session.

    Uses the last `max_aids` distinct aids per session: recent context carries
    the current intent, and it caps the pair explosion (a 500-aid session
    would otherwise emit 250k pairs). Pairs are counted unordered --
    direction doesn't matter for "also viewed".
    """
    global _cooccur
    co = defaultdict(Counter)
    for _, aids, _, _ in train_sessions:
        uniq = list(dict.fromkeys(aids))[-max_aids:]
        for a in uniq:
            ca = co[a]
            for b in uniq:
                if b != a:
                    ca[b] += 1
    _cooccur = co
    print(f"co-visitation built: {len(co):,} items with partners")


def recommend_covisit(session_aids, k=20):
    """Rank unseen items by summed co-occurrence with the session's last 3 aids.

    Why the last 3? In a days-long history, ancient clicks are stale context --
    the last few items carry the current intent. (Trying 1 vs 3 vs 5 is a
    natural follow-up experiment; 3 is the documented starting choice.)
    """
    if _cooccur is None:
        raise RuntimeError("call build_covisit(train_sessions) first")
    seen = set(session_aids)
    scores = Counter()
    for a in session_aids[-3:]:
        for b, c in _cooccur.get(a, {}).items():
            if b not in seen:
                scores[b] += c
    return [a for a, _ in scores.most_common(k)]
