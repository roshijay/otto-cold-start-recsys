# Data dictionary - OTTO cold-start recsys 
## raw.events 
One row per event. Source: first 200,000 sessions of OTTO train.jsonl, streamed from the download zip (never extracted). 
| column | type | meaning |
|---|---|---|
| session_id | BIGINT | anonymous session id — NOT a person |
| aid | BIGINT | anonymous article/product id — no names, no categories, no prices |
| ts | BIGINT | raw timestamp, MILLISECONDS (verified: 13-digit values) |
| event_type | VARCHAR | clicks / carts / orders |
| event_order | BIGINT | position of the event within its session (0 = first) |
| event_ts | TIMESTAMP | ts converted to a real timestamp |

## Quirks
- Event imbalance: ~9.3M clicks / 752K carts / 213K orders (~44:1 clicks:orders).
  Clicks are abundant and weak; orders are rare and strong.
- No product metadata exists — all modeling must be behavioral (IDs only).
- Time window: 2022-07-31 → 2022-08-28 (~4 weeks, contiguous).
- Sample is the FIRST 200k sessions: deterministic, roughly time-ordered.

## Lineage
`data/raw/otto-recommender-system.zip` → `make_sample.py` →
`data/sample/train_sample.jsonl` → `parse_events.py` →
`data/sample/events.parquet` → `load_duckdb.py` → `raw.events`
