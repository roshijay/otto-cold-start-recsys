# Experiment design: ship co-visitation session recommender vs popularity baseline

## 1. Background & hypothesis
- Built three session-based recommenders on 200k OTTO sessions; offline bake-off (time-based 80/20 split, 40k test sessions): **co-visitation won** — weighted Recall@20 0.0328 vs popularity 0.0021 (~15x). See `docs/model-bakeoff.md`.
- Off-policy evaluation on a simulated 50/50 pilot log (40k sessions, 67 informative impressions): IPS lift **+3.04e-04 per impression**, 95% CI [2.13e-04, 4.03e-04] — entirely above zero; doubly robust agrees; ~11x the popularity policy's expected reward. See `docs/ope-results.md`.
- **Hypothesis:** replacing the popularity baseline with co-visitation in the recommendation slot increases orders per session. OPE says the effect is large and positive; this experiment tests it on live traffic.

## 2. Randomization unit: session
- Sessions are anonymous; there is no stable user id. Randomize at session level.
- Implication: no within-user pre-period data → CUPED-style variance reduction isn't available; stratify by hour-of-day / traffic source instead.

## 3. Treatment vs control
- **Control:** popularity-baseline top-20 in the recommendation slot.
- **Treatment:** co-visitation top-20 in the same slot. Only the ranking logic changes; UI, slot position, and K stay identical (isolate the variable).

## 4. Metrics
- **Primary:** orders per session (baseline 0.254).
- **Secondary:** carts per session, clicks per session, session conversion rate.
- **Guardrails:** p99 recommendation latency, fraction of sessions with zero recommendations (must not regress — a worse fallback hurts everyone).

## 5. Sample size (power analysis)
- Baseline p = 0.254 orders/session (`marts.fct_funnel`: 50,871 / 200,000).
- Minimum detectable effect δ = +10% relative = 0.0254 — the smallest win worth the engineering maintenance cost of a new ranking path. (Size on the MDE, not the OPE point estimate — avoids winner's curse.)
- α = 0.05, power = 0.8:

  n per group = 2 * (z_{1-α/2} + z_{1-β})² * p(1-p) / δ² = **4,602 sessions/group**

- At ~450k sessions/day (12.9M sessions / ~29 days), power is reached in under a day. **Power is not the constraint** — run a fixed **2 weeks minimum** anyway: novelty effects need time to wash out, and a full run covers weekly seasonality.

## 6. Analysis plan
- Two-sample t-test on session-level primary metric; check SRM (sample ratio mismatch) daily as a validity alarm.
- Segment by new vs returning session behavior if identifiable.
- Pre-register the decision rule before launch (see §7).

## 7. Decision rule (pre-registered)
- **SHIP:** primary metric up, p < 0.05, guardrails flat.
- **ITERATE:** flat primary, no guardrail regression → revisit features/weights.
- **KILL:** primary down (p < 0.05) or any guardrail regresses.

## 8. Risks
- **Novelty effect:** treatment may pop early as users notice change; require the effect to persist past week 1 before calling it (hence the 2-week minimum).
- **Interference:** minimal — session-level randomization keeps groups independent.
- **Seasonality:** avoid launching over major sale events; note the dates.
