"""Assign YouTube publish slots to pending yt_queue.json entries (idempotent; run before every scheduling session).
Rules (user request 2026-11-10):
- Default: one Short per day at 22:00 KST.
- Test window 2026-11-16 .. 2026-11-29: a second Short at 01:00 KST the next morning (= 21:30 IST).
- FEST episodes (festival / date-bound) keep their own bank date at 22:00.
- Already scheduled entries never move. Other pending entries fill the earliest free slots in episode order.
"""
import json, datetime as dt
Q = 'yt_queue.json'; q = json.load(open(Q)); bank = json.load(open('yt_bank.json'))
TEST = (dt.date(2026, 11, 16), dt.date(2026, 11, 29))
today = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))); tomorrow = today.date() + dt.timedelta(days=1)
def slots():
    d = dt.date(2026, 11, 16)
    while True:
        yield (d.isoformat(), '22:00')
        if TEST[0] <= d <= TEST[1]: yield ((d + dt.timedelta(days=1)).isoformat(), '01:00')
        d += dt.timedelta(days=1)
taken = {(x['date'], x.get('time', '22:00')) for x in q if x['status'] == 'scheduled'}
pend = sorted([x for x in q if x['status'] == 'pending'], key=lambda x: x['ep'])
fest = {}
for x in pend:
    bd, series = bank.get(str(x['ep']), [x['date'], ''])
    x['series'] = series
    if series == 'FEST' and (bd, '22:00') not in taken:
        x['date'], x['time'] = bd, '22:00'; fest[(bd, '22:00')] = x['ep']
reserved = set(fest) | taken
gen = slots()
for x in pend:
    if x['series'] == 'FEST' and (x['date'], x.get('time')) in fest: continue
    for s in gen:
        if s in reserved or dt.date.fromisoformat(s[0]) < tomorrow: continue
        x['date'], x['time'] = s; reserved.add(s); break
for x in q: x.setdefault('time', '22:00')
q.sort(key=lambda x: (x['date'], x['time'] != '01:00', x['time']))
json.dump(q, open(Q, 'w'), ensure_ascii=False, indent=1)
for x in [y for y in q if y['status'] == 'pending'][:20]: print(x['ep'], x['date'], x['time'], x['series'])
