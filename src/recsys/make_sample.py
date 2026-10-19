"""Take the first N sessions of train.jsonl -> data/sample/train_sample.jsonl.

Reads train.jsonl straight from the download zip (no extraction needed).
Set OTTO_RAW to a plain .jsonl path to read an extracted file instead --
the Step 11 CI workflow uses this for its synthetic fixture.
Set OTTO_SAMPLE_N to change the sample size.
"""
import json, os, zipfile

N = int(os.environ.get("OTTO_SAMPLE_N", "200000"))
src = os.environ.get("OTTO_RAW", "data/raw/otto-recommender-system.zip")
dst = "data/sample/train_sample.jsonl"

def iter_lines(path):
    if path.endswith(".zip"):
        zf = zipfile.ZipFile(path)
        names = [n for n in zf.namelist() if n.endswith("train.jsonl")]
        assert len(names) == 1, f"expected one train.jsonl in zip, found: {names}"
        with zf.open(names[0]) as f:
            for line in f:
                yield line.decode("utf-8")
    else:
        with open(path) as f:
            yield from f

written = 0
with open(dst, "w") as fout:
    for line in iter_lines(src):
        if written >= N:
            break
        json.loads(line)  # validate it's real JSON before keeping it
        fout.write(line)
        written += 1

print(f"Wrote {written:,} sessions to {dst}")
