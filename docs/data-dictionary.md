# Data dictionary - OTTO cold-start recsys 
## raw.events 
One row per event. Source: first 200,000 sessions of OTTO train.jsonl, streamed from the download zip (never extracted). 
| column | type | meaning |
|---|---|---|
| session_id | BIGINT | anonymous visitor id — NOT a person, and NOT a single visit: each session is the visitor's full event history, spanning days to weeks (discovered Q5: median 4.2 days click-to-order lag) |
| aid | BIGINT | anonymous article/product id — no names, no categories, no prices |
| ts | BIGINT | raw timestamp, MILLISECONDS (verified: 13-digit values) |
| event_type | VARCHAR | clicks / carts / orders |
| event_order | BIGINT | position of the event within its session (0 = first) |
| event_ts | TIMESTAMP | ts converted to a real timestamp |

## Quirks
- Event imbalance: ~9.3M clicks / 752K carts / 213K orders (~44:1 clicks:orders).
  Clicks are abundant and weak; orders are rare and strong.
- No product metadata exists — all modeling must be behavioral (IDs only).
- Time window: 2022-07-31 22:00 → 2022-08-01 06:43 (~9 hours, overnight).
- Sample is the FIRST 200k sessions: deterministic and time-ordered, but covers only the first night of data — NOT representative of all traffic hours. Hourly analyses are inconclusive beyond this window. Documented limitation; a systematic every-Nth-session sample is future work.
- Quirk: a few events carry timestamps as late as 2022-08-28, well past the last session start — possible outlier events; session_start (min event_ts) is the reliable ordering key.

## Lineage
`data/raw/otto-recommender-system.zip` → `make_sample.py` →
`data/sample/train_sample.jsonl` → `parse_events.py` →
`data/sample/events.parquet` → `load_duckdb.py` → `raw.events`
