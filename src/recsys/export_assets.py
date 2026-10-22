"""Export small, regenerable demo artifacts from DuckDB in one run.

Principle: the Streamlit app is a THIN UI over precomputed artifacts. All heavy
work (dbt, training, evaluation) already ran on the Mac; the app just loads small
files and renders. This separation -- batch compute vs. serving -- is how
production ML systems are structured.

Regenerable > hand-copied: re-run the pipeline, re-run this script, the demo updates.
"""
import json
import os

import duckdb
import pandas as pd

ASSETS = "app/assets"

# Phase 4 bake-off results, as published in docs/model-bakeoff.md
# (regenerate via `python src/recsys/run_bakeoff.py`; embedded here so the exporter
# doesn't re-run a 4-minute eval every time assets refresh).
BAKEOFF = [
    # model, clicks R@20, clicks MRR, carts R@20, carts MRR, orders R@20, weighted R@20, weighted MRR
    ("popularity",   0.0044, 0.0008, 0.0007, 0.0001, 0.0000, 0.0021, 0.0004),
    ("co-visitation", 0.0647, 0.0219, 0.0235, 0.0101, 0.0006, 0.0328, 0.0113),
    ("item2vec",     0.0257, 0.0079, 0.0104, 0.0040, 0.0006, 0.0133, 0.0041),
]


def export_playground():
    """Precompute top-10 recs from all three approaches for 36 sample sessions.

    The app must stay thin, so the playground's recommendations are computed here,
    once, with the full local stack. Deterministic diverse sample: spread across
    session lengths so visitors see short, medium, and long histories.
    """
    from evaluate import load_sessions, time_split, K
    from models import recommend_popularity, recommend_covisit, build_covisit
    from item2vec_recs import recommend_item2vec

    sessions = load_sessions()
    train, test = time_split(sessions)
    test = [s for s in test if len(s[1]) >= 4]
    order = sorted(range(len(test)), key=lambda i: len(test[i][1]))
    n = 36
    chosen = [test[order[int(k * (len(order) - 1) / (n - 1))]] for k in range(n)]

    build_covisit(train)
    out = []
    for sid, aids, types, start in chosen:
        out.append({
            "session_id": int(sid),
            "n_events": len(aids),
            "input_aids": [int(a) for a in aids[:-1][-10:]],  # last 10 shown
            "target_aid": int(aids[-1]),
            "target_type": types[-1],
            "popularity": [int(a) for a in recommend_popularity(aids[:-1], 10)],
            "covisitation": [int(a) for a in recommend_covisit(aids[:-1], 10)],
            "item2vec": [int(a) for a in recommend_item2vec(aids[:-1], 10)],
        })
    path = f"{ASSETS}/playground.json"
    json.dump(out, open(path, "w"))
    print(f"playground.json: {len(out)} sessions")


def main():
    os.makedirs(ASSETS, exist_ok=True)
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)

    funnel = con.execute("select * from main_marts.fct_funnel").df()
    funnel.to_csv(f"{ASSETS}/funnel.csv", index=False)
    print("funnel.csv:", funnel.shape, list(funnel.columns))

    sess = con.execute(
        "select * from main_marts.fct_session_summary order by random() limit 50000"
    ).df()
    sess.to_parquet(f"{ASSETS}/session_summary_sample.parquet", index=False)
    print("session_summary_sample.parquet:", sess.shape, list(sess.columns))

    stats = con.execute(
        """select aid, n_clicks, n_carts, n_orders
           from main_marts.fct_item_stats order by n_clicks desc limit 20000"""
    ).df()
    stats.to_parquet(f"{ASSETS}/item_stats_top.parquet", index=False)
    print("item_stats_top.parquet:", stats.shape)

    from similar import export_item_vectors  # noqa: E402 -- reuse Phase 6 (idempotent)
    export_item_vectors(path=f"{ASSETS}/item_vectors.parquet")

    ope = json.load(open("docs/ope-numbers.json"))["0.5"]  # the pilot attempt
    json.dump({
        "n_test": ope["n"],
        "n_matches": ope["n_matches"],
        "V_pi_pop_ips": ope["V_pi_pop_ips"],
        "V_pi_cand_ips": ope["V_pi_cand_ips"],
        "lift_ips": ope["lift_ips"],
        "lift_ips_ci95": ope["lift_ips_ci95"],
        "lift_dr": ope["lift_dr"],
        "lift_dr_ci95": ope["lift_dr_ci95"],
        "max_weight": ope["max_weight"],
    }, open(f"{ASSETS}/ope_summary.json", "w"), indent=1)
    print("ope_summary.json written")

    pd.DataFrame(BAKEOFF, columns=[
        "model", "clicks_r20", "clicks_mrr20", "carts_r20", "carts_mrr20",
        "orders_r20", "weighted_r20", "weighted_mrr20",
    ]).to_csv(f"{ASSETS}/bakeoff.csv", index=False)
    print("bakeoff.csv written")

    export_playground()

    print("--- asset sizes ---")
    for f in sorted(os.listdir(ASSETS)):
        p = os.path.join(ASSETS, f)
        print(f"  {f}: {os.path.getsize(p) / 1e6:.1f} MB")
    con.close()


if __name__ == "__main__":
    main()
