"""Re-date UNPUBLISHED Instagram reels in schedule.json by content priority (prio.py / priority.json).
- Published posts and anything dated today or earlier never move (today's slot stays as is).
- FEST (date-bound) episodes keep their date; every other unpublished reel fills the remaining daily slots
  from tomorrow on, one per day, in priority order. Card posts are left alone.
Idempotent; run after shipping new episodes or after a weekly review. Usage: python3 ig_plan.py [--dry]"""
import json, sys, datetime as dt
from prio import order
S = 'schedule.json'; sch = json.load(open(S)); posts = sch['posts']
done = {p['id'] for p in json.load(open('published.json'))}
bank = json.load(open('yt_bank.json'))
series = lambda p: bank.get(str(p.get('ep')), ['', ''])[1]
tomorrow = (dt.datetime.now(dt.timezone(dt.timedelta(hours=9))) + dt.timedelta(days=1)).date()
movable = [p for p in posts if p['id'] not in done and p.get('type', 'reel') == 'reel'
           and dt.date.fromisoformat(p['date']) >= tomorrow]
fixed = {p['date'] for p in posts if p.get('type', 'reel') == 'reel' and p not in movable}
fest = [p for p in movable if series(p) == 'FEST']
fixed |= {p['date'] for p in fest}
rest = order([p for p in movable if series(p) != 'FEST'], series, lambda p: p['ep'], lambda p: p['id'])
d = tomorrow
for p in rest:
    while d.isoformat() in fixed: d += dt.timedelta(days=1)
    p['date'] = d.isoformat(); d += dt.timedelta(days=1)
    p.pop('note', None)
posts.sort(key=lambda p: (p['date'], 0 if p.get('type') == 'card' else 1))
for p in [p for p in posts if p in movable][:21]: print(p['date'], p['ep'], series(p), p['id'])
if '--dry' not in sys.argv: json.dump(sch, open(S, 'w'), ensure_ascii=False, indent=1)
