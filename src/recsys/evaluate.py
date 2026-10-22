"""Offline evaluation harness for session recommenders.

Protocol:
- TIME-BASED SPLIT: sessions sorted by session_start; first 80% train, last 20% test.
- TASK: input = all events except the last; target = the last event's aid.
- METRICS: Recall@20 / MRR@20 per target event type + business-weighted blend.
- CONTRACT: recommend(session_aids, k) -> aids not in the input session.
"""
import duckdb

K = 20
# Business weights for the blended score: an order is worth ~20 clicks.
# Same judgment as the popularity baseline weights -- documented, not tuned.
TYPE_WEIGHTS = {"clicks": 1.0, "carts": 5.0, "orders": 20.0}


def load_sessions():
    """One row per session: aids + event types in event order, plus session_start.

    Why the list() aggregates? Pulling 10.3M raw rows into Python would eat
    gigabytes of RAM. Aggregating in DuckDB first gives 200k tidy rows --
    the database does the heavy lifting, Python gets a clean structure.
    """
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    rows = con.execute(
        """
        select
            e.session_id,
            list(e.aid order by e.event_order) as aids,
            list(e.event_type order by e.event_order) as types,
            s.session_start
        from main_staging.stg_events e
        join main_marts.fct_session_summary s using (session_id)
        group by e.session_id, s.session_start
        """
    ).fetchall()
    con.close()
    return rows


def time_split(sessions, train_frac=0.8):
    """Sort by session_start; first 80% train, last 20% test."""
    ordered = sorted(sessions, key=lambda r: r[3])
    n_train = int(len(ordered) * train_frac)
    return ordered[:n_train], ordered[n_train:]


def score_all(test_sessions, all_recs, k=K):
    """Score precomputed recommendation lists against held-out last events."""
    hits = {"clicks": 0, "carts": 0, "orders": 0}
    mrr = {"clicks": 0.0, "carts": 0.0, "orders": 0.0}
    n = {"clicks": 0, "carts": 0, "orders": 0}
    for (sid, aids, types, start), recs in zip(test_sessions, all_recs):
        target, ttype = aids[-1], types[-1]
        n[ttype] += 1
        if target in recs[:k]:
            hits[ttype] += 1
            mrr[ttype] += 1.0 / (recs.index(target) + 1)
    out = {}
    for t in ("clicks", "carts", "orders"):
        out[t] = {
            "n": n[t],
            "recall@20": hits[t] / n[t] if n[t] else 0.0,
            "mrr@20": mrr[t] / n[t] if n[t] else 0.0,
        }
    wsum = sum(TYPE_WEIGHTS[t] * n[t] for t in n)
    out["weighted"] = {
        "recall@20": sum(TYPE_WEIGHTS[t] * hits[t] for t in n) / wsum,
        "mrr@20": sum(TYPE_WEIGHTS[t] * mrr[t] for t in n) / wsum,
    }
    return out


def evaluate(recommend_fn, test_sessions, k=K):
    """Convenience wrapper: score a per-session recommend() function."""
    recs = [recommend_fn(aids[:-1], k) for _, aids, _, _ in test_sessions]
    return score_all(test_sessions, recs, k)
