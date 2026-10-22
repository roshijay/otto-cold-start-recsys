"""Sanity checks for the similarity index -- measured by BEHAVIOR, not vibes.

For a head aid and a rare aid, each neighbor is checked by:
1. co-occurrence overlap: fraction of the top-10 that co-occur with the query
   aid in train sessions (from the Phase 4 co-visitation table);
2. order-rate similarity: do neighbors convert (orders / all events) like the query?

Expectation: high overlap + similar order rates for the head aid; noisier for the
rare aid (few observations -> noisy vectors). That degradation is the
"cold-start within cold-start" problem -- documented, not hidden.
"""
import duckdb

import models
from evaluate import load_sessions, time_split
from item2vec_recs import load_model
from models import build_covisit
from similar import similar_items


def order_rate(con, aid):
    c, ca, o = con.execute(
        "select n_clicks, n_carts, n_orders from main_marts.fct_item_stats where aid = ?",
        [aid],
    ).fetchone()
    tot = c + ca + o
    return o / tot if tot else 0.0


def check(con, aid, label):
    sims = similar_items(aid, k=10)
    co = models._cooccur.get(aid, {})
    overlap = sum(1 for s in sims if s in co)
    qr = order_rate(con, aid)
    nrs = [order_rate(con, s) for s in sims]
    print(f"{label}: aid={aid}")
    print(f"  neighbors: {sims}")
    print(f"  co-occurrence overlap: {overlap}/10")
    print(f"  query order rate: {qr:.4f}")
    print(f"  neighbor order rates: {[f'{r:.4f}' for r in nrs]}")


def main():
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    sessions = load_sessions()
    train, _ = time_split(sessions)
    build_covisit(train)

    head_aid = con.execute(
        "select aid from main_marts.fct_item_stats order by n_clicks desc limit 1"
    ).fetchone()[0]

    wv = load_model().wv
    cands = con.execute(
        """select aid from main_marts.fct_item_stats
           where n_clicks + n_carts + n_orders between 10 and 30
           order by aid limit 50"""
    ).fetchall()
    rare_aid = next(a[0] for a in cands if str(a[0]) in wv)

    check(con, head_aid, "HEAD aid (most clicks)")
    check(con, rare_aid, "RARE aid (10-30 events)")
    con.close()


if __name__ == "__main__":
    main()
