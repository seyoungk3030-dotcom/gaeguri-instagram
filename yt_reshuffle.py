"""Re-order ALL not-yet-published YouTube Shorts (scheduled AND pending) by content priority (prio.py / priority.json).
SY asked on 2026-11-18: "예약 순서를 못바꾸면 미리 해놓는 이유가 없잖아? 잘 나온 컨텐츠 위주로 순서 다 바꿔줘" — so already-scheduled
videos may now be moved too. Slots within the next ~36 h are locked (too close to publish to touch safely).
- FEST episodes keep their bank date at 22:00.
- Every other entry gets the next free slot in priority order (22:00 KST daily + 01:00 KST during the 11/16..29 test).
- A `scheduled` entry whose slot changes gets `resched: true` and `resched_from: [old_date, old_time]` (its ORIGINAL Studio slot);
  the YouTube run then changes that video's schedule in YouTube Studio (YT_SCHEDULING.md step 0c) and clears the flag.
- `pending` entries just get new dates (they are uploaded later at their slot as usual).
Idempotent. Usage: python3 yt_reshuffle.py [--dry]"""
import json, sys, datetime as dt
Q = 'yt_queue.json'; q = json.load(open(Q)); bank = json.load(open('yt_bank.json'))
TEST = (dt.date(2026, 11, 16), dt.date(2026, 11, 29))
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).replace(tzinfo=None)
LOCK = now + dt.timedelta(hours=36)
def when(d, t): return dt.datetime.fromisoformat(f'{d}T{t}')
THREE = dt.date(2026, 11, 20)  # SY 2026-11-19: "하루에 3개씩" -> 01:00, 16:30, 22:00 KST every day from 11/20
def slots():
    d = dt.date(2026, 11, 16)
    while True:
        if d >= THREE or TEST[0] <= d - dt.timedelta(days=1) <= TEST[1]: yield (d.isoformat(), '01:00')
        if d >= THREE: yield (d.isoformat(), '16:30')
        yield (d.isoformat(), '22:00')
        d += dt.timedelta(days=1)
for x in q:
    x.setdefault('time', '22:00')
    x['series'] = bank.get(str(x['ep']), ['', x.get('series') or ''])[1] or x.get('series') or ''
live = [x for x in q if x['status'] in ('scheduled', 'pending')]
locked = [x for x in live if when(x['date'], x['time']) <= LOCK]
movable = [x for x in live if x not in locked]
taken = {(x['date'], x['time']) for x in locked}
fest = [x for x in movable if x['series'] == 'FEST']
for x in fest:
    bd = bank.get(str(x['ep']), [x['date']])[0]
    if when(bd, '22:00') > LOCK: x['_new'] = (bd, '22:00'); taken.add(x['_new'])
    else: x['_new'] = (x['date'], x['time'])
# Pattern phase is anchored to the ABSOLUTE slot index (fixed 2026-11-23): before, the pattern restarted at the first movable
# slot, so every time the 36 h lock passed one more slot the whole queue shifted by one and ~100 scheduled videos had to be
# re-moved in Studio each run. Now a slot's tier depends only on the slot, so runs are idempotent between priority changes.
PHASE = 6  # chosen 2026-11-23 as the offset needing the fewest Studio moves from the then-current schedule
cfg = json.load(open('priority.json')); tier_of = {s: t for t, ss in cfg['tiers'].items() for s in ss}; names = list(cfg['tiers'])
boost = [b.lower() for b in cfg.get('boost', [])]; fresh = cfg.get('fresh_from', 0); pat = cfg['pattern']
pools = {t: [] for t in names + ['_']}
rest = [x for x in movable if x['series'] != 'FEST']
for x in sorted(rest, key=lambda x: (not any(b in x.get('media', '').lower() for b in boost), x['ep'] < fresh, x['ep'])):
    pools[tier_of.get(x['series'], '_')].append(x)
left = len(rest)
for i, s in enumerate(slots()):
    if not left: break
    if s in taken or when(*s) <= LOCK: continue
    for t in [pat[(i + PHASE) % len(pat)]] + names + ['_']:
        if pools[t]:
            x = pools[t].pop(0); x['_new'] = s; taken.add(s); left -= 1; break
moves = 0
for x in movable:
    new = x.pop('_new'); old = (x['date'], x['time'])
    if x['status'] == 'scheduled':
        orig = tuple(x.get('resched_from') or old)
        if new == orig: x.pop('resched', None); x.pop('resched_from', None)
        else: x['resched'] = True; x['resched_from'] = list(orig); moves += 1
    x['date'], x['time'] = new
q.sort(key=lambda x: (x['date'], x['time']))
if '--dry' not in sys.argv: json.dump(q, open(Q, 'w'), ensure_ascii=False, indent=1)
print('locked', len(locked), 'movable', len(movable), 'scheduled videos to move in Studio', moves)
for x in [y for y in q if y in movable][:24]:
    print(x['date'], x['time'], x['ep'], x['series'], x['status'], 'MOVE from ' + ' '.join(x['resched_from']) if x.get('resched') else '')
