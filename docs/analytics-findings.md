# Analytics findings — OTTO cold-start recsys

Sample: first 200,000 sessions (session starts 2022-07-31 22:00 → 2022-08-01 06:43).
Key discovery (Q5): "sessions" are long-lived anonymous visitor histories (days–weeks), not single visits.

## Q1 — Funnel: where does the drop-off happen?
SQL: dbt/analyses/q1_funnel.sql
- 200,000 sessions → 94,561 reach cart (47.3%) → 50,871 order (25.4%).
- Click→cart is the biggest leak (53% of browsers never cart); cart→order converts at 54%.
- Interpretation: investment belongs at the browse→cart transition — exactly where recommendations operate. Checkout is already healthy.

## Q2 — Session length vs conversion
SQL: dbt/analyses/q2_session_length.sql
- Conversion rises monotonically with history length: 0% at 2 events → 8% at 10 → 31% at 40 → 56% at 100 → 70%+ past 150.
- Structural zero: 17,063 two-event sessions, exactly 0% conversion.
- Interpretation: associated, not causal — intent drives both depth and purchase likelihood; more events also mean more mechanical chances for an order. Tail buckets (<100 sessions) are noisy; minimum support applies.

## Q3 — Hourly patterns
SQL: dbt/analyses/q3_hourly.sql (+ q3b_session_dates.sql diagnostic)
- Inconclusive beyond the window: the sample covers a single overnight period, so no general time-of-day claim is supported. Within-window conversion runs 22–28%.
- The diagnostic was the real finding: first-200k sampling = first ~9 hours of data.

## Q4 — Item concentration: head vs long tail
SQL: dbt/analyses/q4_item_concentration.sql
- Extreme long tail: top item by orders = 0.15% of all orders; top 20 ≈ 1.3%.
- Clicks-popularity ≠ orders-popularity: most-clicked item (5,579 clicks) converts at 1.6%; a mid-click item converts at 19%.
- Interpretation: no hero items — popularity baseline will be weak; session-based personalization has room to win. Empirically justifies the weighted multi-objective score (orders ≫ clicks).

## Q5 — Click-to-order lag (my question)
SQL: dbt/analyses/q5_click_to_order_lag.sql
- Median 4.2 days first-click → first order (p25: 11h, p75: 12.6d, p90: 20.6d; n=50,871).
- Discovery: sessions are long-lived visitor histories; purchase journeys play out over days.
- Interpretation: the consideration window is long — recommendations should weight recent behavior within long histories, and there's a natural role for re-engagement ("still interested?") surfaces.

## Q6 — Post-order carting (my question)
SQL: dbt/analyses/q6_post_order_carting.sql
- 70.0% of buyers (35,619 of 50,871) cart again after their first order, averaging 6.3 items; 51.9% order again later in their history.
- Interpretation: saving-for-later is mainstream behavior, not an edge case — evidence for a persistent-cart feature. Post-order carts are high-value intent signals for the next purchase.

## State of the business
Out of 200,000 sessions, only 25% end in a purchase — and the biggest leak is at the top: 53% of visitors never add to cart. Demand is an extreme long tail with no hero items, and strikingly, the most-clicked products convert worst (1.6% vs 19% for a mid-click item): popularity seems to breed skepticism rather than trust, the TikTok Shop effect where 1,000+ reviews send shoppers hunting for the honest bad ones instead of buying. Meanwhile "sessions" turned out to be multi-day visitor histories (median 4.2 days from first click to order), and 70% of buyers cart again right after ordering — already saving for next time, manually. So I'd invest at the browse→cart transition with session-based recommendations (popularity-based would backfire, per the data), weight recent behavior within long histories, and build a real save-for-later surface for the second purchase journey that's already happening.
