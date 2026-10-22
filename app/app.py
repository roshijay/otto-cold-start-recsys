"""OTTO cold-start recsys -- Streamlit demo.

A technical demo for stakeholders: it walks through the analysis behind a ship
decision the way a design review would. Thin UI over precomputed artifacts (built
by src/recsys/export_assets.py) -- nothing trains here, the app only loads small
files and renders them.
"""
from pathlib import Path
import json

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ASSETS = Path(__file__).parent / "assets"  # robust to any working directory
REPO_URL = "https://github.com/roshijay/otto-cold-start-recsys"

st.set_page_config(page_title="OTTO cold-start recsys", layout="wide")
st.title("OTTO cold-start recommender")
st.caption(
    "Demo on a 200,000-session sample of the OTTO public e-commerce data. "
    f"[GitHub repo]({REPO_URL})"
)


@st.cache_data
def load_assets():
    funnel = pd.read_csv(ASSETS / "funnel.csv").iloc[0]
    sess = pd.read_parquet(ASSETS / "session_summary_sample.parquet")
    stats = pd.read_parquet(ASSETS / "item_stats_top.parquet")
    vecs = pd.read_parquet(ASSETS / "item_vectors.parquet")
    vcols = [c for c in vecs.columns if c != "aid"]
    M = vecs[vcols].to_numpy(dtype=np.float32)
    M /= np.linalg.norm(M, axis=1, keepdims=True)  # unit rows: dot product = cosine
    bakeoff = pd.read_csv(ASSETS / "bakeoff.csv")
    ope = json.loads((ASSETS / "ope_summary.json").read_text())
    playground = json.loads((ASSETS / "playground.json").read_text())
    return funnel, sess, stats, vecs, M, bakeoff, ope, playground


funnel, sess, stats, vecs, VEC_M, bakeoff, ope, playground = load_assets()
ids = vecs["aid"].to_numpy()

tab1, tab2, tab3, tab4 = st.tabs([
    "Product analytics", "Recommender playground",
    "Similar items", "Experiment readout",
])

# ---------------- Tab 1: product analytics ----------------
with tab1:
    st.header("The project in 30 seconds")
    st.write(
        "**The problem.** This store has a huge catalog and no star products -- the "
        "best-selling item is only 0.15% of all orders. So 'show everyone the most "
        "popular items' barely works: the most-clicked items are actually the *least* "
        "likely to end in a purchase. On top of that, a 'session' here isn't one quick "
        "visit -- it's a shopper's history stretched over several days (the median gap "
        "from first click to order is 4.2 days). The task: given what someone browsed, "
        "predict what they'll want next. There are no product descriptions or categories "
        "to help -- only behavior."
    )
    st.write(
        "**What was built.** A pipeline from raw logs to a ship decision: (1) data models "
        "in dbt that turn 10M raw events into clean tables; (2) product analytics answering "
        "8 business questions; (3) three recommendation approaches tested head-to-head on "
        "a time-based split -- trained on older sessions, tested on newer ones, the way it "
        "would meet the real world; (4) a 'similar items' feature built from item "
        "embeddings; (5) an off-policy evaluation -- a way to estimate a new policy's "
        "effect from old logs, without running a live experiment first."
    )
    st.write(
        "**The bottom line.** Co-visitation -- 'recommend what shoppers tend to view "
        "alongside this' -- beat the popularity baseline about 15x on the "
        "business-weighted score. The fancier item2vec model lost to it, because "
        "multi-day sessions break the short-window assumption it was trained on "
        "(diagnosed, not hidden). A simulated pilot study then estimated co-visitation "
        "would lift reward per impression ~11x, with the 95% confidence interval sitting "
        "entirely above zero. **Recommendation: ship it to a real A/B test.**"
    )
    st.caption("A technical demo for stakeholders, not a customer app.")

    st.header("Where does the funnel leak?")
    c2c = funnel["n_with_cart"] / funnel["n_sessions"]
    c2o = funnel["n_with_order"] / funnel["n_with_cart"]
    st.write(
        "Think of it like a pipe: 200,000 shoppers enter at the top, and we watch how "
        "many make it through each next step. The chart shows the pipe narrowing -- "
        f"**{funnel['n_sessions']:,.0f}** sessions become **{funnel['n_with_cart']:,.0f}** "
        f"carts ({c2c:.1%}) and then **{funnel['n_with_order']:,.0f}** orders ({c2o:.1%} "
        "of carts). The biggest leak is the first step: over half of all browsers never "
        "put anything in a cart. Checkout itself is healthy. That first step -- browsing "
        "turning into carting -- is exactly where recommendations operate, so it's where "
        "the money is."
    )
    funnel_df = pd.DataFrame({
        "stage": ["sessions", "reached cart", "ordered"],
        "count": [funnel["n_sessions"], funnel["n_with_cart"], funnel["n_with_order"]],
    })
    st.altair_chart(
        alt.Chart(funnel_df).mark_bar().encode(
            x=alt.X("stage", title=None, sort=["sessions", "reached cart", "ordered"]),
            y=alt.Y("count", title="sessions"),
            tooltip=["stage", alt.Tooltip("count", format=",")],
        ).properties(height=300),
        use_container_width=True,
    )

    st.header("Conversion rises with history length")
    st.write(
        "Do shoppers who browse more also buy more? The chart groups sessions by how many "
        "items were viewed -- 0-5, 5-10, all the way to 320+ -- and shows what share of "
        "each group ended in a purchase. It climbs steadily, from near 0% for the shortest "
        "sessions to over 70% for the longest. One caution: this is correlation, not proof "
        "that browsing *causes* buying -- a motivated shopper both browses more and buys "
        "more. Even so, it means keeping shoppers engaged -- the recommender's whole job "
        "-- lines up with revenue."
    )
    bin_labels = ["0-5", "5-10", "10-20", "20-40", "40-80", "80-160", "160-320", "320+"]
    conv_df = (
        sess.assign(len_bin=pd.cut(
            sess["n_events"], bins=[0, 5, 10, 20, 40, 80, 160, 320, 10**9],
            labels=bin_labels))
        .groupby("len_bin", observed=True)["converted"].mean()
        .reset_index()
        .rename(columns={"len_bin": "history length (events)",
                         "converted": "conversion rate"})
    )
    st.altair_chart(
        alt.Chart(conv_df).mark_bar().encode(
            x=alt.X("history length (events)", title=None, sort=bin_labels),
            y=alt.Y("conversion rate", title="conversion rate",
                    axis=alt.Axis(format="%")),
            tooltip=["history length (events)",
                     alt.Tooltip("conversion rate", format=".1%")],
        ).properties(height=300),
        use_container_width=True,
    )

    st.header("Headline findings")
    st.write(
        "- **No star products.** The top item by orders is just 0.15% of all orders -- the "
        "catalog is one long tail. 'Most popular' found the shopper's true next item in its "
        "top 20 only about 0.4% of the time.\n"
        "- **'Sessions' are really multi-day histories** (median 4.2 days from first click "
        "to order), not single visits -- so recommendations should pay most attention to "
        "recent behavior.\n"
        "- **70% of buyers put more items in their cart after ordering** -- saving for later "
        "is normal. But only ~24% come back on a *later day* and truly buy again; the rest "
        "is the same checkout, because OTTO logs every bought item as its own order event."
    )

# ---------------- Tab 2: recommender playground ----------------
with tab2:
    st.header("Three models, one session, the true next item")
    st.write(
        "Three ways to recommend, tested on 40,000 sessions the models had never seen. "
        "For each session we hid the last thing the shopper did, asked every model for "
        "its top 20 guesses, and checked whether the real item was in the list."
    )
    st.write(
        "**The three approaches.** *Popularity* recommends the most-clicked items overall "
        "-- the same list for everyone, no personalization. *Co-visitation* looks at each "
        "item you viewed and recommends the items that most often show up in the same "
        "sessions as it -- 'shoppers who viewed this also viewed...'. *item2vec* turns "
        "every item into a list of 64 numbers learned from browsing patterns; items "
        "browsed in similar journeys get similar numbers, so it recommends the "
        "numerically closest ones."
    )
    st.write(
        "**Reading the scores.** *Recall@20* = how often the shopper's actual next item "
        "appeared anywhere in the model's top-20 list. 0.065 means about 6.5% of the time. "
        "*MRR@20* is similar, but ranking higher counts more: hitting #1 scores 1.0, #20 "
        "scores 0.05, missing the top 20 scores 0 -- it's the average of those. *Weighted* "
        "blends the three event types by business value: a click counts 1, a cart 5, an "
        "order 20, because an order is worth far more than a click."
    )
    pretty = bakeoff.rename(columns={
        "clicks_r20": "Clicks R@20", "clicks_mrr20": "Clicks MRR@20",
        "carts_r20": "Carts R@20", "carts_mrr20": "Carts MRR@20",
        "orders_r20": "Orders R@20",
        "weighted_r20": "Weighted R@20", "weighted_mrr20": "Weighted MRR@20",
    }).set_index("model")
    st.dataframe(pretty)

    st.subheader("Try a session")
    st.write("Pick a real test session and compare what each model guessed against what "
             "the shopper actually did next (marked '← actual pick').")
    labels = {p["session_id"]:
              f"session {p['session_id']} · {p['n_events']} events · next: {p['target_type']}"
              for p in playground}
    sid = st.selectbox("Session", options=list(labels.keys()), format_func=labels.get)
    p = next(x for x in playground if x["session_id"] == sid)
    st.write("Recent history (item ids):", ", ".join(map(str, p["input_aids"])))
    cols = st.columns(3)
    for col, (name, key) in zip(cols, [("Popularity", "popularity"),
                                       ("Co-visitation", "covisitation"),
                                       ("item2vec", "item2vec")]):
        with col:
            st.subheader(name)
            for i, aid in enumerate(p[key], 1):
                mark = " ← actual pick" if aid == p["target_aid"] else ""
                st.write(f"{i}. {aid}{mark}")

# ---------------- Tab 3: similar items ----------------
with tab3:
    st.header("Behaviorally similar items")
    st.write(
        "Pick an item to see its closest neighbors. 'Close' means the items' "
        "64-number profiles point in nearly the same direction -- the *cosine similarity* "
        "score runs from 0 (unrelated) to 1.0 (identical), and the table shows it for each "
        "neighbor. Those profiles were learned from browsing journeys, not product text -- "
        "this data has no titles or categories -- so neighbors are items that *shoppers* "
        "treat as related. This is the cold-start fallback: even with zero history on a "
        "shopper, a single picked item is enough to recommend from."
    )
    head20 = stats.sort_values("n_clicks", ascending=False).head(20)
    item_labels = {int(r["aid"]): f"#{i+1} most-clicked · aid {int(r['aid'])} "
                                  f"({int(r['n_clicks']):,} clicks)"
                   for i, r in head20.iterrows()}
    aid = st.selectbox("Item", options=list(item_labels.keys()),
                       format_func=item_labels.get)
    st.caption("The 20 most-clicked items -- every choice has neighbors to show.")
    k = st.slider("Neighbors", 5, 20, 10)
    if aid in ids:
        sims = VEC_M @ VEC_M[ids == aid][0]
        top = [t for t in np.argsort(-sims) if ids[t] != aid][:k]
        rows = []
        for t in top:
            a = int(ids[t])
            srow = stats[stats["aid"] == a]
            c, ca, o = (srow.iloc[0][["n_clicks", "n_carts", "n_orders"]].tolist()
                        if len(srow) else (None, None, None))
            rows.append({"aid": a, "cosine": round(float(sims[t]), 3),
                         "clicks": c, "carts": ca, "orders": o})
        st.dataframe(pd.DataFrame(rows))
    else:
        st.warning("Item not in the head-item index (top 20k by clicks).")

# ---------------- Tab 4: experiment readout ----------------
with tab4:
    st.header("Should we ship co-visitation?")
    st.write(
        "The offline tests say co-visitation wins -- but that's still just 'what would we "
        "have recommended.' The real question is causal: *if we actually put this in front "
        "of shoppers, would revenue per impression go up?* We can't rerun history, so we "
        "estimate the answer from logged data instead. That technique is called "
        "off-policy evaluation."
    )
    st.write(
        "**How it works, simply.** Imagine replaying 40,000 past sessions while pretending "
        "our new policy chose the recommendations instead of whatever the shopper actually "
        "saw. Whenever the logged item happens to match what the new policy would have "
        "shown, we keep that moment and re-weight it: (how likely the *new* policy was to "
        "show it) divided by (how likely the *old* policy was). Average those weighted "
        "outcomes and you get an estimate of the new policy's value. We computed it two "
        "ways -- IPS, and doubly robust, which also uses a reward model as a backup -- and "
        "they agreed, which is reassuring."
    )
    st.write(
        "**The setup.** We simulated a 50/50 pilot log: half the impressions came from the "
        "popularity policy, half from co-visitation. Because both policies appear in the "
        "log, the comparison is fair -- and the design guarantees every weight stays small "
        "(at most 2.0), so no single lucky moment can dominate the result."
    )
    st.write(
        f"Off-policy evaluation on a simulated 50/50 pilot log ({ope['n_test']:,} test sessions, "
        f"{ope['n_matches']} informative impressions)."
    )
    col_chart, col_nums = st.columns([3, 2])
    with col_chart:
        vdf = pd.DataFrame({
            "policy": ["popularity", "co-visitation"],
            "expected reward": [ope["V_pi_pop_ips"], ope["V_pi_cand_ips"]],
        })
        st.altair_chart(
            alt.Chart(vdf).mark_bar().encode(
                y=alt.Y("policy", title=None, sort=["co-visitation", "popularity"]),
                x=alt.X("expected reward", title="expected reward per impression"),
                tooltip=["policy", alt.Tooltip("expected reward", format=".2e")],
            ).properties(height=220),
            use_container_width=True,
        )
    with col_nums:
        st.metric("Estimated lift (IPS)", f"{ope['lift_ips']:.2e}")
        st.caption(f"95% CI [{ope['lift_ips_ci95'][0]:.2e}, {ope['lift_ips_ci95'][1]:.2e}]")
        st.metric("Estimated lift (doubly robust)", f"{ope['lift_dr']:.2e}")
        st.caption(f"95% CI [{ope['lift_dr_ci95'][0]:.2e}, {ope['lift_dr_ci95'][1]:.2e}]")
    st.write(
        "**Reading the numbers.** 'Lift' is the extra reward per impression versus the "
        "popularity baseline -- about 11x the baseline's value. The 95% confidence "
        "interval is the range we're 95% sure the true lift falls in; since the whole "
        "range sits above zero, the improvement is real, not noise. And because every "
        "weight is capped at 2.0 by design, no single moment dominates the result."
    )
    st.subheader("Assumptions")
    st.write(
        "- The 'how likely was the policy to show this' numbers come from our simulation, "
        "not from OTTO's real systems -- OTTO never ran this as an experiment.\n"
        "- Every item had a nonzero chance of being shown (built into the simulation), so "
        "the math never divides by zero.\n"
        "- Inside the simulation there are no hidden factors skewing things -- but the "
        "simulation is still not real traffic."
    )
    st.subheader("Limitation")
    st.write("This is directional evidence for prioritizing the engineering work, not proof. "
             "The honest next step is a live A/B test -- and this analysis says it's worth "
             "running.")
    st.subheader("Recommendation: SHIP -- promote to a live experiment")
