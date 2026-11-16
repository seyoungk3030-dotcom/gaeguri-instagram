"""Shared content-priority order for Instagram (ig_plan.py) and YouTube (yt_plan.py).
priority.json defines tiers of series and a repeating slot pattern (e.g. AABAAC = 4 of every 6 slots go to the
best-performing tier). Inside a tier, lower episode numbers go first. When a tier runs out, the next tier fills in.
FEST (date-bound) episodes are not ordered here: callers keep them on their own dates."""
import json

def order(items, series_of, ep_of, key_of=lambda x: ''):
    cfg = json.load(open('priority.json'))
    tier_of = {s: t for t, ss in cfg['tiers'].items() for s in ss}
    names = list(cfg['tiers'])
    pools = {t: [] for t in names + ['_']}
    boost = [b.lower() for b in cfg.get('boost', [])]
    hit = lambda x: any(b in key_of(x).lower() for b in boost)
    for x in sorted(items, key=lambda x: (not hit(x), ep_of(x))):
        pools[tier_of.get(series_of(x), '_')].append(x)
    out, pat, i = [], cfg['pattern'], 0
    while any(pools.values()):
        want = pat[i % len(pat)]; i += 1
        for t in [want] + names + ['_']:
            if pools.get(t):
                out.append(pools[t].pop(0)); break
    return out
