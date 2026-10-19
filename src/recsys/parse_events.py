"""Flatten sampled JSONL sessions -> one row per event -> events.parquet"""
import json
import pandas as pd

src = "data/sample/train_sample.jsonl"
dst = "data/sample/events.parquet"

rows = []
with open(src) as f:
    for line in f:
        sess = json.loads(line)
        sid = sess["session"]
        for order, e in enumerate(sess["events"]):
            rows.append({
                "session_id": sid,
                "aid": e["aid"],
                "ts": e["ts"],
                "event_type": e["type"],
                "event_order": order,
            })

df = pd.DataFrame(rows)

# Normalize ts to a real timestamp column (auto-detect ms vs s)
if df["ts"].max() > 1e12:
    df["event_ts"] = pd.to_datetime(df["ts"], unit="ms")
else:
    df["event_ts"] = pd.to_datetime(df["ts"], unit="s")

print(df["event_type"].value_counts())
print("Sessions:", df["session_id"].nunique(), "| Events:", len(df))
print("Time range:", df["event_ts"].min(), "->", df["event_ts"].max())

df.to_parquet(dst, index=False)
print("Wrote", dst)
