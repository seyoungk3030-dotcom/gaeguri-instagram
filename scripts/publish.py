"""Publish scheduled Gaeguri Bhai reels and card-news carousels to Instagram (@gaeguribhai) via the Graph API.

Usage:
  python scripts/publish.py              # post the oldest approved, unpublished entry due by today (KST-6h), one per run
  python scripts/publish.py --id ID      # post one specific entry now
  python scripts/publish.py --check ID   # build the media container only (nothing goes public)
"""
import argparse, datetime, json, os, sys, time, urllib.parse, urllib.request

TOKEN = os.environ["IG_ACCESS_TOKEN"].strip()
USER = os.environ["IG_USER_ID"].strip()
# Instagram-login tokens (IGAA...) use graph.instagram.com; Facebook / system-user tokens use graph.facebook.com.
API = ("https://graph.instagram.com/v21.0" if TOKEN.startswith("IG") else "https://graph.facebook.com/v21.0")
KST = datetime.timezone(datetime.timedelta(hours=9))
REPO = os.environ.get("GITHUB_REPOSITORY", "seyoungk3030-dotcom/gaeguri-instagram")
REF = os.environ.get("MEDIA_REF") or os.environ.get("GITHUB_SHA") or "main"


def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    req = urllib.request.Request(f"{url}?{data.decode()}") if method == "GET" else urllib.request.Request(url, data=data, method="POST")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == 3:
                sys.exit(f"{method} {path} failed: {e.code} {e.read().decode()}")
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            if attempt == 3:
                sys.exit(f"{method} {path} failed: {e}")
        time.sleep(5 * 2 ** attempt)


def media_url(path):
    return f"https://raw.githubusercontent.com/{REPO}/{REF}/{path}"


def wait_ready(cid, limit=900):
    for _ in range(limit // 10):
        st = call("GET", cid, fields="status_code,status")
        if st.get("status_code") == "FINISHED":
            return
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            sys.exit(f"container {cid} failed: {st}")
        time.sleep(10)
    sys.exit(f"container {cid} not ready after {limit}s")


def build(post):
    if post.get("type") == "card":
        kids = []
        for m in post["media"]:
            kids.append(call("POST", f"{USER}/media", image_url=media_url(m), is_carousel_item="true")["id"])
        for k in kids:
            wait_ready(k, 300)
        cid = call("POST", f"{USER}/media", media_type="CAROUSEL", children=",".join(kids), caption=post["caption"])["id"]
        wait_ready(cid, 300)
        return cid
    params = dict(media_type="REELS", video_url=media_url(post["media"][0]), caption=post["caption"], share_to_feed="true")
    if post.get("cover_ms") is not None:
        params["thumb_offset"] = str(post["cover_ms"])
    cid = call("POST", f"{USER}/media", **params)["id"]
    wait_ready(cid)
    return cid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id")
    ap.add_argument("--check")
    ap.add_argument("--type", choices=["reel", "card"], help="only post this type (scheduled runs pass it)")
    a = ap.parse_args()
    sched = json.load(open("schedule.json"))
    published = json.load(open("published.json"))
    done = {p["id"] for p in published}
    by_id = {p["id"]: p for p in sched["posts"]}

    if a.check:
        print(f"container {build(by_id[a.check])} ready; not published")
        return
    if a.id:
        due = [by_id[a.id]]
    else:
        # GitHub often starts scheduled runs hours late (11/15: 21:40 run started 04:04 KST; 11/16: runs started
        # 02:23-08:32 KST). Rules: only post inside the evening window 21:00-03:00 KST (= 17:30-23:30 IST);
        # a run outside it does nothing (so a late run never posts tonight's reel in the morning).
        # Inside the window: post the OLDEST unpublished post dated on/before the posting day
        # (today if >= 21:00, yesterday if after midnight), one per run -> missed days catch up next evening.
        now = datetime.datetime.now(KST)
        if not (now.hour >= 21 or now.hour < 3):
            print(f"outside the 21:00-03:00 KST posting window ({now:%H:%M}); nothing posted")
            return
        day = (now if now.hour >= 21 else now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        due = sorted((p for p in sched["posts"] if p["date"] <= day and p.get("approved")
                      and p["id"] not in done and (not a.type or p.get("type", "reel") == a.type)),
                     key=lambda p: p["date"])[:1]
    for post in due:
        if not post.get("approved"):
            print(f"{post['id']} is not approved; skipped"); continue
        if post["id"] in done:
            print(f"{post['id']} already published"); continue
        cid = build(post)
        mid = call("POST", f"{USER}/media_publish", creation_id=cid)["id"]
        link = call("GET", mid, fields="permalink").get("permalink")
        print(f"published {post['id']} -> {link}")
        published.append({"id": post["id"], "media_id": mid, "permalink": link,
                          "at": datetime.datetime.now(KST).isoformat(timespec="seconds")})
        json.dump(published, open("published.json", "w"), ensure_ascii=False, indent=1)
    if not due:
        print("nothing due (all posts up to today are published)")


if __name__ == "__main__":
    main()
