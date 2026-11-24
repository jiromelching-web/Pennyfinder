#!/usr/bin/env python3
"""PennyFinder refresh: builds docs/data/deals.json for the 6 Home Depot stores in
Fresno, Clovis, Madera and Selma, CA.

Sources (all public pages, fetched politely: 5 requests per run, 2 s apart):
  1. Spotted (spottedflips.com) city clearance pages -> per-store clearance price,
     was price, % off, units in stock, and when Spotted last checked that store.
  2. Penny Recon public JSON (pennyrecon.com/data/items.json, linked in its footer)
     -> national penny ($0.01) candidates with SKU / Internet # / UPC and CA report counts.
homedepot.com itself is NOT queried: its Akamai bot protection returns 403 to
cloud/datacenter IPs, and we do not try to get around that.
PennyCentral is NOT scraped (its terms prohibit scraping); the app links to it.

Usage:  python3 scripts/refresh.py [--out docs/data/deals.json]
Needs:  Python 3.9+ and beautifulsoup4  (pip install beautifulsoup4)
"""
import argparse, json, re, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

UA = "Mozilla/5.0 (compatible; PennyFinder personal refresh; +single user, a few runs/day)"
STORES = [
    {"id": "663",  "name": "Fresno",       "address": "3272 W Shaw Ave, Fresno, CA 93711",          "phone": "(559) 277-9600", "city": "Fresno"},
    {"id": "1014", "name": "N Fresno",     "address": "7150 N Abbey St, Fresno, CA 93720",          "phone": "(559) 431-9860", "city": "Fresno"},
    {"id": "1086", "name": "South Fresno", "address": "4864 E Kings Canyon Rd, Fresno, CA 93727",   "phone": "(559) 455-9124", "city": "Fresno"},
    {"id": "664",  "name": "Clovis",       "address": "845 W Shaw Ave, Clovis, CA 93612",           "phone": "(559) 294-9600", "city": "Clovis"},
    {"id": "1088", "name": "Madera",       "address": "2155 N Schnoor St, Madera, CA 93637",        "phone": "", "city": "Madera"},
    {"id": "8529", "name": "Selma",        "address": "3175 Highland Ave, Selma, CA 93662",         "phone": "(559) 891-0506", "city": "Selma"},
]
STORE_IDS = {s["id"] for s in STORES}
CITY_PAGES = {c: f"https://www.spottedflips.com/clearance/home-depot/ca/{c}" for c in ["fresno", "clovis", "madera", "selma"]}
PENNYRECON_JSON = "https://www.pennyrecon.com/data/items.json"
TZ_SRC = {"EST": ZoneInfo("America/New_York"), "EDT": ZoneInfo("America/New_York"),
          "PST": ZoneInfo("America/Los_Angeles"), "PDT": ZoneInfo("America/Los_Angeles"),
          "CST": ZoneInfo("America/Chicago"), "CDT": ZoneInfo("America/Chicago")}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def money(t):
    m = re.search(r"\$([\d,]+(?:\.\d+)?)", t or "")
    return float(m.group(1).replace(",", "")) if m else None


def parse_checked(txt, now):
    # e.g. "Nov 23, 8:43 PM EST" (no year on the page)
    m = re.search(r"([A-Z][a-z]{2} \d{1,2}), (\d{1,2}:\d{2} [AP]M) ([A-Z]{3})", txt or "")
    if not m:
        return None
    tz = TZ_SRC.get(m.group(3), ZoneInfo("America/New_York"))
    for yr in (now.year, now.year - 1):
        try:
            dt = datetime.strptime(f"{m.group(1)} {yr} {m.group(2)}", "%b %d %Y %I:%M %p").replace(tzinfo=tz)
        except ValueError:
            continue
        if dt <= now + timedelta(days=2):
            return dt.astimezone(timezone.utc).isoformat()
    return None


def parse_city(html, now):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    out, seen_stores = [], {}
    for sec in soup.find_all("section"):
        h = sec.find("h2")
        if not h:
            continue
        m = re.match(r"Home Depot #(\d+)\s+(.*)", h.get_text(" ", strip=True))
        if not m or m.group(1) not in STORE_IDS:
            continue
        sid = m.group(1)
        p = sec.find("p")
        checked = parse_checked(p.get_text(" ", strip=True) if p else "", now)
        rows = sec.select("tbody tr")
        seen_stores[sid] = {"checked_at": checked, "rows": len(rows)}
        for tr in rows:
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue
            a = tds[0].find("a")
            title = tds[0].get_text(" ", strip=True)
            spans = tds[1].find_all("span")
            price = money(spans[0].get_text()) if spans else money(tds[1].get_text())
            was_el = tds[1].find(style=re.compile("line-through"))
            was = money(was_el.get_text()) if was_el else None
            pct_m = re.search(r"(\d+)\s*% off", tds[1].get_text(" ", strip=True))
            pct = int(pct_m.group(1)) if pct_m else (round(100 * (1 - price / was)) if price is not None and was else None)
            qty_m = re.match(r"\s*(\d+)", tds[3].get_text(" ", strip=True))
            out.append({
                "store_id": sid,
                "title": title,
                "price": price,
                "was": was,
                "pct_off": pct,
                "qty": int(qty_m.group(1)) if qty_m else None,
                "penny": price is not None and price <= 0.01,
                "checked_at": checked,
                "source": "Spotted",
                "source_url": urllib.parse.urljoin("https://www.spottedflips.com", a["href"]) if a and a.get("href") else None,
                "hd_search_url": "https://www.homedepot.com/s/" + urllib.parse.quote(title[:80]),
            })
    return out, seen_stores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/data/deals.json")
    args = ap.parse_args()
    now = datetime.now(timezone.utc)
    result = {"generated_at": now.isoformat(), "stores": STORES, "clearance": [], "penny_candidates": [],
              "sources": [], "store_checks": {}}
    for i, (city, url) in enumerate(CITY_PAGES.items()):
        if i:
            time.sleep(2)
        try:
            rows, seen = parse_city(get(url), now)
            result["clearance"] += rows
            result["store_checks"].update(seen)
            result["sources"].append({"name": f"Spotted {city.title()}", "url": url, "ok": True, "rows": len(rows)})
        except Exception as e:  # keep going; report failure in the app
            result["sources"].append({"name": f"Spotted {city.title()}", "url": url, "ok": False, "error": str(e)[:200]})
    time.sleep(2)
    try:
        items = json.loads(get(PENNYRECON_JSON))
        for it in items:
            st = it.get("states") or {}
            result["penny_candidates"].append({
                "sku": it.get("skuFmt") or it.get("sku"), "internet_number": it.get("internetNumber"),
                "upc": it.get("upc"), "model": it.get("modelNumber"), "brand": it.get("brand"),
                "title": it.get("name"), "retail": it.get("retail"), "price": 0.01,
                "last_seen_at": it.get("lastSeenAt"), "first_reported_at": it.get("firstReportedAt"),
                "reports": it.get("reports"), "ca_reports": st.get("CA", 0), "states": len(st),
                "likelihood": it.get("likelihood"), "tier": it.get("tier"),
                "hd_url": it.get("hdUrl"), "source_url": it.get("url"), "image": it.get("imageUrl"),
                "source": "Penny Recon",
            })
        result["sources"].append({"name": "Penny Recon", "url": PENNYRECON_JSON, "ok": True, "rows": len(items)})
    except Exception as e:
        result["sources"].append({"name": "Penny Recon", "url": PENNYRECON_JSON, "ok": False, "error": str(e)[:200]})
    ok = any(s["ok"] for s in result["sources"])
    with open(args.out, "w") as f:
        json.dump(result, f, indent=1)
    print(f"wrote {args.out}: {len(result['clearance'])} store clearance rows, "
          f"{len(result['penny_candidates'])} penny candidates; sources: "
          + ", ".join(f"{s['name']}={'ok' if s['ok'] else 'FAIL'}" for s in result["sources"]))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
