#!/usr/bin/env python3
"""Unified daily job monitor.
Loops enabled sources -> tags -> de-dups (within run + vs history) -> appends
fresh_jobs.csv -> writes digest.md -> saves last-run state.
Run: python pipeline.py    (needs source API keys as env vars)"""
from datetime import datetime, timedelta, timezone
import config, store, tagging
from sources import REGISTRY

def main():
    now = datetime.now(timezone.utc)
    last_run = store.load_state()
    cutoff = last_run if last_run else now - timedelta(hours=config.LOOKBACK_HOURS)
    mode = "since last run" if last_run else f"first run / last {config.LOOKBACK_HOURS}h"
    print(f"Run {now:%Y-%m-%d %H:%M UTC} | cutoff {cutoff:%Y-%m-%d %H:%M UTC} ({mode})")

    raw = []
    for name in config.ENABLED_SOURCES:
        fn = REGISTRY.get(name)
        if not fn:
            print(f"  ! source '{name}' enabled but no module registered — skipping")
            continue
        got = fn(cutoff, now)
        print(f"  {name}: {len(got)} ad(s) in window")
        raw += got

    tagged = [tagging.tag(r) for r in raw]
    deduped = store.dedupe_within_run(tagged)

    history = store.load_history_keys()
    fresh = [r for r in deduped if r["dedup_key"] not in history]

    store.append(fresh)
    store.write_digest(fresh, now)
    store.save_state(now)
    print(f"  {len(fresh)} genuinely-new role(s) added "
          f"({len(deduped) - len(fresh)} already seen). Digest + CSV updated.")

if __name__ == "__main__":
    main()
