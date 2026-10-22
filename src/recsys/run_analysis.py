"""Run a compiled dbt analysis SQL file against DuckDB and print the table."""
import sys, duckdb
path = sys.argv[1]
sql = open(path).read()
con = duckdb.connect("data/warehouse.duckdb")
print(con.execute(sql).fetchdf().to_string())
con.close()
