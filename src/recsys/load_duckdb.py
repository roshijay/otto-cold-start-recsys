"""Load events.parquet into DuckDB raw.events (idempotent rebuild)."""
import duckdb

con = duckdb.connect("data/warehouse.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS raw")
con.execute("CREATE OR REPLACE TABLE raw.events AS SELECT * FROM 'data/sample/events.parquet'")

n = con.execute("SELECT COUNT(*) FROM raw.events").fetchone()[0]
print("raw.events rows:", f"{n:,}")
print(con.execute("DESCRIBE raw.events").fetchall())
con.close()
