"""Collect reach/engagement metrics for every published post into insights.json (read-only)."""
import json, os, sys, urllib.parse, urllib.request, datetime
TOKEN = os.environ["IG_ACCESS_TOKEN"].strip(); USER = os.environ["IG_USER_ID"].strip()
API = "https://graph.instagram.com/v21.0" if TOKEN.startswith("IG") else "https://graph.facebook.com/v21.0"
def get(path, **p):
    p["access_token"] = TOKEN
    try:
        with urllib.request.urlopen(f"{API}/{path}?{urllib.parse.urlencode(p)}", timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e: return {"error": e.read().decode()[:300]}
out = {"at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="minutes"),
       "account": get(USER, fields="followers_count,media_count"), "posts": []}
for p in json.load(open("published.json")):
    mid = p["media_id"]; reel = "/reel/" in p["permalink"]
    m = "reach,views,likes,comments,shares,saved,total_interactions" + (",ig_reels_avg_watch_time,ig_reels_video_view_total_time" if reel else "")
    ins = get(f"{mid}/insights", metric=m)
    if "error" in ins and reel:
        ins = get(f"{mid}/insights", metric="reach,views,likes,comments,shares,saved,total_interactions")
    row = {"id": p["id"]}
    row.update({k: v for k, v in get(mid, fields="like_count,comments_count").items() if k != "id"})
    for d in ins.get("data", []): row[d["name"]] = d["values"][0]["value"] if d.get("values") else d.get("total_value", {}).get("value")
    if "error" in ins: row["insights"] = "no permission"
    out["posts"].append(row)
json.dump(out, open("insights.json", "w"), ensure_ascii=False, indent=1); print(json.dumps(out, ensure_ascii=False, indent=1))
