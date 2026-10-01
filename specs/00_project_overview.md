# Project Spec: Cold-Start Session Recommendation with Causal Off-Policy Evaluation

## Business framing

A large share of e-commerce sessions are anonymous, first-visit sessions with no
persistent user history (this is true of the OTTO dataset by construction — sessions,
not users, are the unit of data). Before shipping a new session-based recommender for
these cold-start sessions, we want to estimate — using only logged historical data,
without running a live A/B test — whether it would out-convert a simple popularity
baseline, and how confident we are in that estimate.

This mirrors a real experimentation-team ticket: "we can't A/B test everything before
we have some offline evidence it's worth the engineering cost and user-experience risk."

## Data source

OTTO Multi-Objective Recommender System dataset (Kaggle), ~12.9M real anonymized
e-commerce sessions. Each session is a sequence of events: `clicks`, `carts` (cart-adds),
`orders`, each tied to a product (`aid`) and timestamp.

- Full dataset: ~13GB uncompressed. We will develop against a local sample
  (e.g. first N sessions or a random session sample) before loading the full set
  into Snowflake.
- License/usage: OTTO released this for their Kaggle competition; check current
  Kaggle terms before any commercial use — this project is portfolio/educational only.

## Non-goals (explicit scope boundaries)

- This is NOT a re-run of the OTTO Kaggle competition leaderboard chase
  (we are not optimizing recall@20 as the end goal, only as one diagnostic metric).
- This is NOT a claim of a true historical logging policy — OTTO logs weren't
  captured as a bandit experiment, so any propensity scores used in the causal
  evaluation are from a policy we simulate ourselves. This limitation is stated
  explicitly in the final write-up, not hidden.
- No paid APIs. Embeddings and the RAG generation step both run locally
  (sentence-transformers for embeddings, Ollama for LLM generation).

## Pipeline phases

1. **Data foundation** — load raw events into Snowflake (`raw` schema), validate schema,
   document meaning of each field.
2. **dbt modeling layer** — `stg_events` (cleaned, typed, deduped) → intermediate
   (sessionized, feature-enriched) → marts (analytics-ready: funnel, conversion,
   category performance).
3. **Product analytics** — funnel/drop-off analysis, session-length distributions,
   category-level conversion, answered as SQL-first questions against the marts layer.
4. **Cold-start recommender** — baseline: popularity/co-visitation matrix.
   Candidate: session-based sequence model. Multi-objective: weight clicks/carts/orders
   differently when scoring candidates (rare-strong-signal vs abundant-weak-signal tradeoff).
5. **Causal / off-policy evaluation** — simulate a logging policy over historical
   sessions, then estimate the candidate recommender's effect using inverse propensity
   scoring (IPS) and a doubly robust estimator, with confidence intervals. State
   estimator assumptions and limitations explicitly.
6. **Semantic search** — local embedding model over product metadata, vector
   similarity search, positioned as the cold-start fallback for a session with
   zero history (query-based, not history-based).
6b. **RAG shopping assistant** (built after Phase 6, on top of the same vector store)
   — retrieval-augmented generation layer: a user's natural-language query retrieves
   candidate products via the Phase 6 vector store, then a local LLM (via Ollama,
   free/no API cost) generates a grounded natural-language response explaining or
   comparing the retrieved products. Kept as a distinct phase, not merged into
   Phase 6, so the recommender + causal evaluation work remains the project's
   centerpiece rather than being overshadowed by the LLM-facing feature.
7. **Deployment** — small API + UI, hosted free (Streamlit Community Cloud or
   Hugging Face Spaces), demonstrating the recommender + search + RAG assistant +
   a summary of the offline evaluation result.
8. **Documentation** — running learning log (this repo's `docs/` folder), exported
   periodically to PDF, capturing decisions, concepts, and interview-prep notes.

## Tooling (all free-tier)

GitHub (public repo), Kaggle (data), Snowflake (30-day trial, suspend-on-idle
warehouse), dbt Core, Python (uv-managed env), sentence-transformers (local
embeddings), Ollama (local LLM for RAG generation), Streamlit or FastAPI + a
free host.

## Acceptance criteria template (fill in per phase before building)

- What does "done" look like for this phase, concretely?
- What data quality tests must pass?
- What's the specific question this phase answers?
- What would make Claude Code's output for this phase wrong, even if it runs?
