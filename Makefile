.PHONY: all sample dbt recsys ope similarity assets clean

all: sample dbt recsys ope similarity assets
	@echo "Pipeline complete."

sample:
	.venv/bin/python src/recsys/make_sample.py
	.venv/bin/python src/recsys/parse_events.py
	.venv/bin/python src/recsys/load_duckdb.py

dbt:
	cd dbt && ../.venv/bin/dbt build

recsys:
	.venv/bin/python src/recsys/train_item2vec.py
	.venv/bin/python src/recsys/run_bakeoff.py

ope:
	.venv/bin/python src/recsys/ope.py

similarity:
	.venv/bin/python src/recsys/check_similarity.py

assets:
	.venv/bin/python src/recsys/export_assets.py

clean:
	rm -rf data/sample/train_sample.jsonl data/sample/events.parquet data/warehouse.duckdb
