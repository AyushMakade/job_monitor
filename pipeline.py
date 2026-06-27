#!/usr/bin/env python3
"""Unified daily job monitor.

Window logic:
  * FIRST run (no state.json) -> cutoff is None -> sources return EVERYTHING they
    can (seeds the baseline; a fuller page pull is used just this once).
  * EVERY run after -> cutoff = now - LOOKBACK_HOURS (default 48h). The wide
    window plus de-duplication means a delayed/skipped run never leaves a gap and
    re-runs never double-count.

Source contract: fetch(cutoff, now) where cutoff=None means "first run, take all".
"""
from datetime import datetime, timedelta, timezone
import config, store, tagging
from sources import REGISTRY

def main():
    now = datetime.now(timezone.utc)
    last_run = store.load_state()
    if last_run is None:
        cutoff = None
        print(f"Run {now:%Y-%m-%d %H:%M UTC} | FIRST RUN — taking everything available (baseline)")
    else:
        cutoff = now - timedelta(hours=config.LOOKBACK_HOURS)
        print(f"Run {now:%Y-%m-%d %H:%M UTC} | window: last {config.LOOKBACK_HOURS}h "
              f"(since {cutoff:%Y-%m-%d %H:%M UTC})")

    raw = []
    for name in config.ENABLED_SOURCES:
        fn = REGISTRY.get(name)
        if not fn:
            print(f"  ! source '{name}' enabled but not registered — skipping")
            continue
        got = fn(cutoff, now)
        raw += got

    tagged = [tagging.tag(r) for r in raw]
    deduped = store.dedupe_within_run(tagged)

    history = store.load_history_keys()
    fresh = [r for r in deduped if r["dedup_key"] not in history]

    store.append(fresh)
    store.write_digest(fresh, now)
    store.save_state(now)
    print(f"  {len(fresh)} new role(s) added "
          f"({len(deduped) - len(fresh)} already in CSV). Digest + CSV updated.")

if __name__ == "__main__":
    main()
