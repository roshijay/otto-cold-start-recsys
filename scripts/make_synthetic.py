"""Generate a tiny synthetic OTTO-like JSONL for CI smoke tests."""
import argparse, json, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", type=int, default=2000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    n_items, popular = 500, list(range(20))
    base_ts = 1659304800  # seconds; parse_events.py auto-detects ms vs s
    with open(args.out, "w") as f:
        for s in range(args.sessions):
            n_events = rng.randint(1, 12)
            ts = base_ts + s * 30
            events = []
            for _ in range(n_events):
                aid = rng.choice(popular) if rng.random() < 0.6 else rng.randint(0, n_items - 1)
                r = rng.random()
                etype = "orders" if r > 0.97 else ("carts" if r > 0.90 else "clicks")
                ts += rng.randint(5, 600)
                events.append({"aid": aid, "ts": ts * 1000, "type": etype})
            f.write(json.dumps({"session": s, "events": events}) + "\n")
    print(f"Wrote {args.sessions} synthetic sessions to {args.out}")

if __name__ == "__main__":
    main()
